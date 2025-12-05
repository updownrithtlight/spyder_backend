# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()
redis_client: Redis | None = None


def init_extensions(app):
    global redis_client

    db.init_app(app)

    redis_client = Redis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        db=app.config["REDIS_DB"],
        decode_responses=True,
    )
