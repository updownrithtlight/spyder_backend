# backend/app/models/user.py
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


class User(db.Model):
    __tablename__ = "t_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # 你指定的几个字段：
    user_fullname = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")

    # 等价于：
    # `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "user_fullname": self.user_fullname,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
