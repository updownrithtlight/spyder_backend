# backend/app/models/file.py
from datetime import datetime
from sqlalchemy import text

from ..extensions import db


class FileObject(db.Model):
    __tablename__ = "t_file_object"

    id = db.Column(db.Integer, primary_key=True)
    object_key = db.Column(db.String(255), unique=True, nullable=False)
    original_name = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(128), nullable=True)
    size = db.Column(db.BigInteger, nullable=True)

    uploader_id = db.Column(db.Integer, db.ForeignKey("t_user.id"), nullable=True)
    uploader = db.relationship("User", backref="files")

    folder_id = db.Column(db.Integer, db.ForeignKey("t_folder.id"), nullable=True)
    folder = db.relationship("Folder", backref="files")

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "object_key": self.object_key,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size": self.size,
            "uploader_id": self.uploader_id,
            "folder_id": self.folder_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
