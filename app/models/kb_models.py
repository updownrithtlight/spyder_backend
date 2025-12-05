
# app/models/kb_models.py
from ..extensions import db

class KbFolder(db.Model):
    __tablename__ = "t_kb_folder"

    id = db.Column(db.BigInteger, primary_key=True)
    parent_id = db.Column(db.BigInteger, db.ForeignKey("t_kb_folder.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    parent = db.relationship("KbFolder", remote_side=[id], backref="children")


class KbFile(db.Model):
    __tablename__ = "t_kb_file"

    id = db.Column(db.BigInteger, primary_key=True)
    folder_id = db.Column(db.BigInteger, db.ForeignKey("t_kb_folder.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    document_id = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    version = db.Column(db.Integer, nullable=False, default=1)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    created_by = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    folder = db.relationship("KbFolder", backref="files")
    tags = db.relationship("KbTag", secondary="t_kb_file_tag", backref="files")


class KbTag(db.Model):
    __tablename__ = "t_kb_tag"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, server_default=db.func.now())


class KbFileTag(db.Model):
    __tablename__ = "t_kb_file_tag"

    file_id = db.Column(
        db.BigInteger,
        db.ForeignKey("t_kb_file.id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_id = db.Column(
        db.BigInteger,
        db.ForeignKey("t_kb_tag.id", ondelete="CASCADE"),
        primary_key=True
    )
