# backend/app/services/minio_signer.py
from datetime import timedelta, datetime
from uuid import uuid4
import os

from minio import Minio
from flask import current_app


def _minio_client() -> Minio:
    cfg = current_app.config
    return Minio(
        cfg["MINIO_ENDPOINT"],
        access_key=cfg["MINIO_ACCESS_KEY"],
        secret_key=cfg["MINIO_SECRET_KEY"],
        secure=cfg["MINIO_SECURE"],
    )


def build_object_key(filename: str, folder: str | None = None) -> str:
    ext = os.path.splitext(filename)[1]
    key = f"{uuid4().hex}{ext}"
    if folder:
        return f"{folder.rstrip('/')}/{key}"
    return key


def sign_put_object(
    filename: str,
    content_type: str,
    folder: str | None = None,
    expire_minutes: int = 30,
) -> dict:
    client = _minio_client()
    bucket = current_app.config["MINIO_BUCKET"]

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    object_key = build_object_key(filename, folder)
    expires = timedelta(minutes=expire_minutes)

    upload_url = client.presigned_put_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=expires,
    )

    expire_at = datetime.utcnow() + expires
    return {
        "uploadUrl": upload_url,
        "objectKey": object_key,
        "expireAt": expire_at.isoformat() + "Z",
    }


def build_public_url(object_key: str) -> str:
    base = current_app.config["MINIO_PUBLIC_BASE"].rstrip("/")
    bucket = current_app.config["MINIO_BUCKET"]
    return f"{base}/{bucket}/{object_key}"


def delete_object(object_key: str) -> None:
    """
    删除 MinIO 上的对象（文件 API 删除时调用）
    """
    client = _minio_client()
    bucket = current_app.config["MINIO_BUCKET"]
    client.remove_object(bucket, object_key)
