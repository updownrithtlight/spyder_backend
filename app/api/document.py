# app/api/file.py
from flask import Blueprint, request, jsonify

from ..services import document_service

bp = Blueprint("file", __name__)


@bp.route("/upload/prepare", methods=["POST"])
def prepare_upload():
    """
    获取 MinIO 预签名上传 URL
    Body:
    {
        "businessId": "xxx",
        "fileType": "DRAWING",
        "parentId": 1,
        "filename": "test.pdf",
        "contentType": "application/pdf",
        "size": 12345
    }
    """
    try:
        result = document_service.prepare_upload()
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/upload/confirm", methods=["POST"])
def confirm_upload():
    """
    确认上传完成
    Body:
    {
        "documentId": 12
    }
    """
    try:
        result = document_service.confirm_upload()
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<int:document_id>/download-url", methods=["GET"])
def get_download_url(document_id):
    """
    生成下载 URL（预签名）
    GET /api/files/<document_id>/download-url
    """
    try:
        result = document_service.generate_download_url(document_id)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):
    """
    删除文件（软删除 + MinIO 删除）
    """
    try:
        result = document_service.delete_document(document_id)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/update/prepare", methods=["POST"])
def prepare_update_upload():
    """
    更新文件时，获取新的上传 URL
    Body:
    {
        "documentId": 12,
        "filename": "new.pdf",
        "contentType": "application/pdf",
        "size": 9999
    }
    """
    try:
        result = document_service.prepare_update_upload()
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 400
