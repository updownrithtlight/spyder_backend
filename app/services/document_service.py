# app/services/document_service.py
from datetime import datetime, timedelta
import re
import uuid

from flask import request, current_app
from ..extensions import db

# 这里直接用刚刚建好的模型和枚举
from app.models.document import Document, DocumentStatus, FileType

from app.utils.minio_storage import (
    generate_presigned_upload_url,
    generate_presigned_download_url,
    delete_object,
)
from app.models.result import ResponseTemplate
from app.exceptions.exceptions import CustomAPIException


def _build_object_key(req_json: dict) -> str:
    """
    对应 Java 的 buildObjectKey：fileType/businessId/[parentId]/yyyy/MM/dd/uuid_filename
    """
    file_type = (req_json.get("fileType") or "default").strip()
    business_id = (req_json.get("businessId") or "noBiz").strip()
    parent_id = req_json.get("parentId")

    filename = (req_json.get("filename") or "unnamed").strip()
    safe_filename = re.sub(r'[\\/:*?"<>|]', "_", filename)

    date_path = datetime.now().strftime("%Y/%m/%d")
    uid = str(uuid.uuid4())

    parts = [file_type, business_id]
    if parent_id is not None:
        parts.append(str(parent_id))

    # fileType/businessId[/parentId]/yyyy/MM/dd/uuid_filename
    base = "/".join(parts)
    object_key = f"{base}/{date_path}/{uid}_{safe_filename}"
    return object_key

def prepare_upload():
    """
    POST /api/file/upload/prepare
    Request JSON (对应 PrepareUploadRequest):
    {
      "fileType": "xxx",
      "filename": "xxx.pdf",
      "contentType": "application/pdf",
      "size": 12345               # 字节
    }

    Response:
    {
      "code": 0,
      "data": {
        "documentId": 1,
        "uploadUrl": "https://...."
      }
    }
    """
    data = request.get_json(silent=True) or {}
    if not data.get("filename"):
        raise CustomAPIException("filename 不能为空", 400)

    default_bucket = current_app.config["MINIO_BUCKET"]

    object_key = _build_object_key(data)

    # 先插 DB，状态=UPLOADING
    doc = Document()
    doc.file_type = data.get("fileType")
    doc.bucket = default_bucket
    doc.object_key = object_key
    doc.file_name = data.get("filename")
    doc.content_type = data.get("contentType")
    doc.size = data.get("size")
    doc.status = DocumentStatus.UPLOADING

    db.session.add(doc)
    db.session.commit()

    # 生成预签名上传 URL（比如 15 分钟）
    upload_url = generate_presigned_upload_url(
        bucket=default_bucket,
        object_key=object_key,
        ttl=timedelta(minutes=15),
        request=request,
    )

    return ResponseTemplate.success(
        data={
            "documentId": doc.id,
            "uploadUrl": upload_url,
        }
    )

def confirm_upload():
    """
    POST /api/file/upload/confirm
    Request JSON (对应 ConfirmUploadRequest):
    { "documentId": 1 }

    简单版：只改状态为 COMPLETED
    """
    data = request.get_json(silent=True) or {}
    doc_id = data.get("documentId")
    if not doc_id:
        raise CustomAPIException("documentId 不能为空", 400)

    doc = Document.query.get(doc_id)
    if not doc:
        raise CustomAPIException(f"Document not found: {doc_id}", 404)

    # TODO: 权限校验

    if doc.status != DocumentStatus.UPLOADING:
        # 可以选择直接 return success，不抛错；这里按 Java 逻辑抛异常
        raise CustomAPIException("Document status is not UPLOADING, cannot confirm.", 400)

    doc.status = DocumentStatus.COMPLETED
    db.session.commit()

    return ResponseTemplate.success(message="确认上传成功")

def generate_download_url(document_id: int):
    """
    GET /api/file/<int:document_id>/download-url
    """
    doc = Document.query.get(document_id)
    if not doc:
        raise CustomAPIException(f"Document not found: {document_id}", 404)

    # TODO: 权限校验

    if doc.status != DocumentStatus.COMPLETED:
        raise CustomAPIException("Document is not ready for download", 400)

    url = generate_presigned_download_url(
        bucket=doc.bucket,
        object_key=doc.object_key,
        ttl=timedelta(minutes=15),
        download_filename=doc.file_name,
        request=request,
    )

    return ResponseTemplate.success(
        data={"downloadUrl": url}
    )

def delete_document(document_id: int):
    """
    DELETE /api/file/<int:document_id>
    """
    doc = Document.query.get(document_id)
    if not doc:
        raise CustomAPIException(f"Document not found: {document_id}", 404)

    # TODO: 权限校验

    # 先删 MinIO 对象（按 Java 逻辑）
    try:
        delete_object(bucket=doc.bucket, object_key=doc.object_key)
    except Exception:
        # 这里你可以记 log，然后继续软删除
        pass

    # 软删：改状态
    doc.status = DocumentStatus.DELETED
    db.session.commit()

    return ResponseTemplate.success(message="删除成功")

def prepare_update_upload():
    """
    POST /api/file/update/prepare
    Request JSON (对应 UpdatePrepareRequest):
    {
      "documentId": 1,
      "filename": "new.pdf",
      "contentType": "application/pdf",
      "size": 1234
    }

    返回新的 uploadUrl（覆盖原文件）
    """
    data = request.get_json(silent=True) or {}
    doc_id = data.get("documentId")
    if not doc_id:
        raise CustomAPIException("documentId 不能为空", 400)

    doc = Document.query.get(doc_id)
    if not doc:
        raise CustomAPIException(f"Document not found: {doc_id}", 404)

    # TODO: 权限校验

    # 重新生成 objectKey（复用 Java 逻辑：沿用原 fileType / businessId）
    filename = (data.get("filename") or "unnamed").strip()
    safe_filename = re.sub(r'[\\/:*?"<>|]', "_", filename)
    date_path = datetime.now().strftime("%Y/%m/%d")
    uid = str(uuid.uuid4())

    file_type = doc.file_type or "default"
    business_id = doc.business_id or "noBiz"

    new_object_key = f"{file_type}/{business_id}/{date_path}/{uid}_{safe_filename}"

    # 记录旧 objectKey（如果以后想 confirm 时顺便删老文件，可以加字段）
    old_object_key = doc.object_key

    # 更新 Document
    doc.object_key = new_object_key
    doc.file_name = filename
    doc.content_type = data.get("contentType")
    doc.size = data.get("size")
    doc.status = DocumentStatus.UPLOADING
    db.session.commit()

    upload_url = generate_presigned_upload_url(
        bucket=doc.bucket,
        object_key=new_object_key,
        ttl=timedelta(minutes=15),
        request=request,
    )

    # TODO: 如果你想在 confirm_upload 时删除 old_object_key，可以这里把它写入 doc.extra 字段之类

    return ResponseTemplate.success(
        data={"uploadUrl": upload_url}
    )
