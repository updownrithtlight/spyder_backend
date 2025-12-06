# app/utils/minio_storage.py
from typing import Optional, Dict

from minio import Minio
from datetime import timedelta
from typing import Union, Optional
from flask import current_app, Request
from minio.error import S3Error



def get_minio_client() -> Minio:
    """
    获取 MinIO 客户端，使用配置：
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE
    """
    return Minio(
        current_app.config["MINIO_ENDPOINT"],
        access_key=current_app.config["MINIO_ACCESS_KEY"],
        secret_key=current_app.config["MINIO_SECRET_KEY"],
        secure=current_app.config.get("MINIO_SECURE", False),
    )


def _ensure_bucket_exists(client: Minio, bucket: str) -> None:
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except Exception as e:
        raise RuntimeError(f"Failed to ensure bucket exists: {bucket}") from e


def _build_dynamic_public_base(request: Optional[Request]) -> str:
    """
    模仿 Java 版的 buildDynamicPublicBase：
    - 优先使用 X-Forwarded-Proto / Host
    - scheme + host + 固定前缀（如 /minio）
    """
    cfg_public_base = current_app.config.get("MINIO_PUBLIC_BASE", "").rstrip("/")
    if request is None:
        # 没有 request，就退回配置
        return cfg_public_base

    # 1. scheme
    scheme = request.headers.get("X-Forwarded-Proto") or request.scheme  # http/https

    # 2. host（带端口）
    host = request.headers.get("Host")
    if not host:
        server_name = request.host.split(":")[0]
        port = request.environ.get("SERVER_PORT")
        if port and port not in ("80", "443"):
            host = f"{server_name}:{port}"
        else:
            host = server_name

    # 举例修正：如果是 chengziback.xyz 且是 http，强制 https（和 Java 同逻辑）
    if scheme == "http" and "chengziback.xyz" in host:
        scheme = "https"

    base = f"{scheme}://{host}"
    # 和 Java 中写死 /minio 一样，你也可以改成配置：MINIO_PUBLIC_PREFIX
    return base.rstrip("/") + current_app.config.get("MINIO_PUBLIC_PREFIX", "/minio")


def _rewrite_to_public_url(raw_url: str, dynamic_public_base: str) -> str:
    """
    把内部 endpoint 重写成对外的 base：
    """
    if not raw_url:
        return raw_url

    internal_endpoint = current_app.config.get("MINIO_INTERNAL_ENDPOINT", "").rstrip("/")
    if not internal_endpoint or not dynamic_public_base:
        # 没配，直接用原始 URL
        return raw_url

    import re
    internal_base = re.sub(r"/+$", "", internal_endpoint)
    public_base_fixed = dynamic_public_base.rstrip("/")

    # 只替换前缀
    return raw_url.replace(internal_base, public_base_fixed, 1)


def generate_presigned_upload_url(
    bucket: str,
    object_key: str,
    ttl: Union[int, timedelta, None],
    request: Optional[Request],
) -> str:
    """
    生成上传预签名 URL，对应 Java 的 generatePresignedUploadUrl。
    ttl:
      - timedelta: 直接使用
      - int: 视为秒数
      - None: 使用配置 MINIO_PRESIGNED_EXPIRE_SECONDS（秒），默认 900
    """
    client = get_minio_client()
    _ensure_bucket_exists(client, bucket)

    # 统一得到一个 timedelta 对象
    if isinstance(ttl, timedelta):
        expire_td = ttl
    elif isinstance(ttl, int):
        # 传进来就是秒
        expire_td = timedelta(seconds=ttl)
    else:
        # 没传就用配置
        seconds = int(current_app.config.get("MINIO_PRESIGNED_EXPIRE_SECONDS", 900))
        expire_td = timedelta(seconds=seconds)

    try:
        raw_url = client.presigned_put_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expire_td,  # ⭐ 这里必须是 timedelta
        )
    except S3Error as e:
        raise RuntimeError("Failed to generate presigned upload URL") from e

    dynamic_public_base = _build_dynamic_public_base(request)
    return _rewrite_to_public_url(raw_url, dynamic_public_base)

def generate_presigned_download_url(
    bucket: str,
    object_key: str,
    ttl: Union[int, timedelta, None],
    download_filename: Optional[str],
    request: Optional[Request],
) -> str:
    """
    生成下载预签名 URL，对应 Java 的 generatePresignedDownloadUrl。
    """
    client = get_minio_client()

    if isinstance(ttl, timedelta):
        expire_td = ttl
    elif isinstance(ttl, int):
        expire_td = timedelta(seconds=ttl)
    else:
        seconds = int(current_app.config.get("MINIO_PRESIGNED_EXPIRE_SECONDS", 900))
        expire_td = timedelta(seconds=seconds)

    extra_params: Dict[str, str] = {}
    if download_filename:
        disposition = f'attachment; filename="{download_filename}"'
        extra_params["response-content-disposition"] = disposition

    try:
        raw_url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expire_td,
            response_headers=extra_params or None,
        )
    except S3Error as e:
        raise RuntimeError("Failed to generate presigned download URL") from e

    dynamic_public_base = _build_dynamic_public_base(request)
    return _rewrite_to_public_url(raw_url, dynamic_public_base)



def delete_object(bucket: str, object_key: str) -> None:
    """
    删除对象，对应 Java 的 deleteObject。
    """
    client = get_minio_client()
    try:
        client.remove_object(bucket_name=bucket, object_name=object_key)
    except S3Error as e:
        raise RuntimeError("Failed to delete object from MinIO") from e

# app/utils/minio_storage.py
# (保留你原有的 import 和函数，在文件末尾添加以下内容)

# ... (上面的代码保持不变: get_minio_client, generate_presigned_url 等) ...

def get_object_stream(bucket: str, object_key: str):
    """
    【新增】直接获取 MinIO 文件流（用于 Flask 代理下载）
    返回: MinIO 的 response 对象 (类似 file-like object)
    """
    client = get_minio_client()
    try:
        # get_object 返回的是 urllib3.response.HTTPResponse
        # 它可以被 Flask 的 send_file 直接使用
        return client.get_object(bucket_name=bucket, object_name=object_key)
    except S3Error as e:
        raise RuntimeError(f"Failed to get object stream: {object_key}") from e

def upload_stream(bucket: str, object_key: str, data, length: int, content_type: str = "application/octet-stream"):
    """
    【新增】直接上传流数据到 MinIO（用于回调保存）
    data: bytes 或 file-like object
    """
    client = get_minio_client()
    _ensure_bucket_exists(client, bucket)
    try:
        client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=data,
            length=length,
            content_type=content_type
        )
    except S3Error as e:
        raise RuntimeError(f"Failed to upload stream: {object_key}") from e