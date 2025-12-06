# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
redis_client: Redis | None = None
jwt = JWTManager()   # ⭐ 新增


def init_extensions(app):
    global redis_client

    # 初始化数据库
    db.init_app(app)

    # 初始化 JWT
    jwt.init_app(app)   # ⭐ 新增，必须有！

    # 初始化 Redis
    redis_client = Redis(
        host=app.config.get("REDIS_HOST"),
        port=app.config.get("REDIS_PORT"),
        db=app.config.get("REDIS_DB"),
        decode_responses=True,
    )
