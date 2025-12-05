# backend/app/services/onlyoffice_client.py
import time
import jwt
from flask import current_app


def generate_onlyoffice_token(payload: dict) -> str:
    """
    用 JWT 给 OnlyOffice 的 config 签名
    """
    secret = current_app.config["ONLYOFFICE_JWT_SECRET"]
    payload = payload.copy()
    payload["iat"] = int(time.time())
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def build_onlyoffice_config(
    document_url: str,
    callback_url: str,
    file_type: str = "docx",
    title: str = "Document",
) -> dict:
    """
    生成 OnlyOffice 前端需要的配置 + token
    """
    doc_server = current_app.config["ONLYOFFICE_DOC_SERVER"].rstrip("/")

    config = {
        "document": {
            "fileType": file_type,
            "title": title,
            "url": document_url,
        },
        "editorConfig": {
            "callbackUrl": callback_url,
        },
    }

    token = generate_onlyoffice_token(config)

    return {
        "config": config,
        "token": token,
        "docServerUrl": doc_server,
    }
