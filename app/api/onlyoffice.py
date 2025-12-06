# app/api/onlyoffice.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services import onlyoffice_service
from app.exceptions.exceptions import CustomAPIException

bp = Blueprint("onlyoffice", __name__)

# ... (原有的 /config, /callback, /status 等路由保持不变) ...

@bp.route("/config", methods=["GET"])
@jwt_required()
def get_editor_config():
    try:
        result = onlyoffice_service.get_editor_config()
        return result
    except CustomAPIException as e:
        return jsonify({"message": str(e), "code": getattr(e, "status_code", 400)}), getattr(e, "status_code", 400)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@bp.route("/download/<int:document_id>", methods=["GET"])
def download_proxy(document_id):
    """
    【新增】OnlyOffice 专用的代理下载接口
    地址示例: /api/onlyoffice/download/123
    """
    try:
        # 这里不需要 @jwt_required，因为 OnlyOffice 无法携带前端的 JWT
        # 安全起见，如果需要鉴权，通常是在 URL 里带一个一次性 token，或者依靠内网隔离
        return onlyoffice_service.proxy_download_file(document_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@bp.route("/callback/<int:document_id>", methods=["POST"])
def callback(document_id):
    return onlyoffice_service.onlyoffice_callback(document_id)


@bp.route("/status", methods=["POST"])
def online_status():
    try:
        return onlyoffice_service.online_status()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/force-save", methods=["POST"])
def force_save():
    try:
        return onlyoffice_service.force_save()
    except Exception as e:
        return jsonify({"error": str(e)}), 400