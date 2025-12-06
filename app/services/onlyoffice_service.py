# app/services/onlyoffice_service.py
import hashlib
import time
import io
import mimetypes
import jwt as pyjwt
import requests
from datetime import datetime

from flask import current_app, request, jsonify, send_file
from flask_jwt_extended import get_jwt_identity

from app.models.result import ResponseTemplate
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.utils import minio_storage  # 引入刚才修改的 minio_storage
from app.extensions import db
from app.exceptions.exceptions import CustomAPIException


# ============== 工具函数 ==============

def _cfg(key, default=None):
    return current_app.config.get(key, default)


def _backend_public() -> str:
    # 确保这里返回的是 OnlyOffice 能访问到的 Flask 地址 (如 http://192.168.31.138:5173)
    return (_cfg("BACKEND_PUBLIC") or "").rstrip("/")


def _verify_callback_jwt() -> bool:
    token = request.headers.get("Authorization") or request.headers.get("AuthorizationJwt")
    if not token:
        return False
    try:
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        pyjwt.decode(token, _cfg("ONLYOFFICE_JWT_SECRET"), algorithms=["HS256"])
        return True
    except Exception:
        return False


def _doc_key(doc: Document) -> str:
    updated_at = getattr(doc, "updated_at", None)
    ts = int(updated_at.timestamp()) if isinstance(updated_at, datetime) else int(time.time())
    size = doc.size or 0
    base = f"{doc.id}:{ts}:{size}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


# 扩展名映射
ALLOWED_EXTS_MAP = {
    ".xlsx": ("cell", "xlsx"), ".xls": ("cell", "xls"), ".csv": ("cell", "csv"),
    ".docx": ("word", "docx"), ".doc": ("word", "doc"),
    ".pptx": ("slide", "pptx"), ".ppt": ("slide", "ppt"),
    ".pdf": ("word", "pdf"), ".txt": ("word", "txt"),
}


# ============== 核心逻辑 ==============

def proxy_download_file(doc_id: int):
    """
    服务：从 MinIO 读取流 -> 转发给 OnlyOffice
    """
    doc = Document.query.get(doc_id)
    if not doc:
        raise Exception("Document not found")

    # 1. 调用 minio_storage 获取 MinIO 原始流
    minio_stream = minio_storage.get_object_stream(doc.bucket, doc.object_key)

    # 2. 自动猜测 MIME
    mime_type = doc.content_type
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(doc.file_name)

    # 3. 使用 Flask send_file 转发流
    # as_attachment=True 配合 download_name 能完美处理中文文件名 (RFC 5987)
    return send_file(
        minio_stream,
        as_attachment=True,
        download_name=doc.file_name,
        mimetype=mime_type or "application/octet-stream",
        max_age=0
    )


def _editor_config(doc: Document, id: str, user_name: str, mode: str = "edit"):
    filename = doc.file_name or "unnamed"
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1]
    else:
        ext = ".docx"
    ext_lower = ext.lower()

    # 获取类型
    if ext_lower in ALLOWED_EXTS_MAP:
        document_type, file_type = ALLOWED_EXTS_MAP[ext_lower]
    else:
        document_type, file_type = "word", "docx"

    # 【关键】：URL 指向 Flask 自己的代理接口
    download_url = f"{_backend_public()}/api/onlyoffice/download/{doc.id}"

    # 回调地址
    callback_url = f"{_backend_public()}/api/onlyoffice/callback/{doc.id}"

    cfg = {
        "documentType": document_type,
        "document": {
            "fileType": file_type,
            "key": _doc_key(doc),
            "title": filename,
            "url": download_url,  # 指向 Flask
            "permissions": {
                "edit": mode == "edit" and document_type in ("cell", "word", "slide"),
                "download": True,
                "print": True,
                "comment": True,
            },
        },
        "editorConfig": {
            "mode": "edit" if mode == "edit" else "view",
            "callbackUrl": callback_url,
            "user": {"id": str(id), "name": user_name or str(id)},
            "lang": "zh-CN",
            "autosave": True,
        },
        "height": "100%", "width": "100%", "type": "desktop",
    }

    # 签名
    secret = _cfg("ONLYOFFICE_JWT_SECRET", "MyJWTSecretKey123")
    alg = _cfg("ONLYOFFICE_JWT_ALG", "HS256")
    token = pyjwt.encode(cfg, secret, algorithm=alg)
    if isinstance(token, (bytes, bytearray)):
        token = token.decode("utf-8")
    cfg["token"] = token

    return cfg


def get_editor_config():
    """ 生成前端配置 """
    file_id = (request.args.get("fileId") or "").strip()
    mode = (request.args.get("mode") or "edit").strip()

    if not file_id:
        raise CustomAPIException("fileId cannot be empty", 400)

    try:
        doc_id = int(file_id)
    except ValueError:
        raise CustomAPIException("Invalid fileId", 400)

    doc = Document.query.get(doc_id)
    if not doc:
        raise CustomAPIException("Document not found", 404)

    identity = get_jwt_identity()
    user = User.query.get(identity)
    if not user:
        raise CustomAPIException("User not found", 401)

    return ResponseTemplate.success(
        data=_editor_config(doc, str(user.id), user.user_fullname, mode),
        message="OK"
    )


def onlyoffice_callback(document_id: int):
    """ 回调保存：OnlyOffice -> Flask -> MinIO """
    try:
        if _cfg("ONLYOFFICE_VERIFY_INBOX", False):
            if not _verify_callback_jwt():
                return jsonify({"error": 1, "message": "invalid token"}), 403

        doc = Document.query.get(document_id)
        if not doc:
            return jsonify({"error": 1, "message": "Document not found"}), 404

        data = request.get_json(force=True) or {}
        status = data.get("status")

        # 2=Ready for saving, 6=MustSave
        if status in (2, 6):
            download_url = data.get("url")
            if download_url:
                current_app.logger.info(f"[OnlyOffice] Downloading updated file from {download_url}")

                # 1. Flask 从 OnlyOffice 下载文件
                # 这里的 download_url 是 OnlyOffice 容器内部生成的，Flask 必须能访问到它
                r = requests.get(download_url, stream=True, timeout=60)
                r.raise_for_status()

                # 2. 读取流数据
                file_data = io.BytesIO(r.content)
                length = file_data.getbuffer().nbytes

                # 3. 通过 minio_storage 直接上传流，覆盖原文件
                minio_storage.upload_stream(
                    bucket=doc.bucket,
                    object_key=doc.object_key,
                    data=file_data,
                    length=length,
                    content_type=doc.content_type or "application/octet-stream"
                )

                # 4. 更新数据库信息
                doc.size = length
                doc.updated_at = datetime.now()
                if doc.status != DocumentStatus.COMPLETED:
                    doc.status = DocumentStatus.COMPLETED

                db.session.commit()
                current_app.logger.info(f"[OnlyOffice] Saved doc {document_id} success.")

        return jsonify({"error": 0}), 200

    except Exception as e:
        current_app.logger.exception("OnlyOffice callback failed")
        return jsonify({"error": 1, "message": str(e)}), 200


# 保持原样的辅助函数
def online_status():
    # ... (逻辑同上一次提供代码，调用 DOCUMENT_SERVER_COMMAND_URL)
    pass


def force_save():
    # ... (逻辑同上一次提供代码)
    pass