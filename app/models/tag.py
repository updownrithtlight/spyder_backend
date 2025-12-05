# backend/app/models/tag.py
from datetime import datetime
from sqlalchemy import text

from ..extensions import db


# 中间表：文件 <-> 标签 多对多
file_tag_table = db.Table(
    "t_file_tag",
    db.Column("file_id", db.Integer, db.ForeignKey("t_file_object.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("t_tag.id"), primary_key=True),
)


class Tag(db.Model):
    __tablename__ = "t_tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    color = db.Column(db.String(16), nullable=True)  # 例如 #FF0000

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # 反向关系：Tag.files
    files = db.relationship(
        "FileObject",
        secondary=file_tag_table,
        backref="tags",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
