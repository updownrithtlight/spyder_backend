# backend/app/config.py
import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    # Access Token：短有效期（比如 30 分钟）
    JWT_ACCESS_SECRET = os.environ.get("JWT_ACCESS_SECRET", "dev-access-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)  # Access Token 的过期时间
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Refresh Token 的过期时间
    # Refresh Token：长有效期（比如 7 天）
    JWT_REFRESH_SECRET = os.environ.get("JWT_REFRESH_SECRET", "dev-refresh-secret")

    # ========== MySQL（SQLAlchemy） ==========
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://appuser:appuser123@192.168.31.145:3306/appdb?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ========== Redis ==========
    REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.31.145")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_DB = int(os.environ.get("REDIS_DB", 0))

    # ========== MinIO ==========
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "192.168.31.145:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "admin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "StrongPass123!")
    MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "files")

    BACKEND_PUBLIC= os.environ.get("BACKEND_PUBLIC", "http://192.168.31.138:5000")

    # MinIO 对外访问前缀（给前端 / OnlyOffice 用）
    MINIO_PUBLIC_BASE = os.environ.get(
        "MINIO_PUBLIC_BASE",
        "http://192.168.31.145:9000"   # 先本地直连，以后可以换成 Nginx 反代 http://your-domain/minio
    )

    # ========== OnlyOffice Document Server ==========
    ONLYOFFICE_BASE_URL  = os.environ.get(
        "ONLYOFFICE_DOC_SERVER",
        "http://192.168.31.145:8080"        # Docker 环境下会改成 http://onlyoffice
    )
    ONLYOFFICE_JWT_SECRET = os.environ.get(
        "ONLYOFFICE_JWT_SECRET",
        "MyJWTSecretKey123"
    )
    ONLYOFFICE_FILE_DIR = os.environ.get("ONLYOFFICE_FILE_DIR","D:\dev")
    ONLYOFFICE_VERIFY_INBOX=False
    DOCUMENT_SERVER_COMMAND_URL =os.environ.get("DOCUMENT_SERVER_COMMAND_URL", "http://192.168.31.145:8080/coauthoring/CommandService.ashx")
class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


config_map = {
    "dev": DevConfig,
    "prod": ProdConfig,
}
