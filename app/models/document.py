# app/models/document.py
from datetime import datetime
from enum import Enum

from ..extensions import db


class FileType(str, Enum):
    """
    对应 Java 的 com.heng.workflow.enums.FileType 枚举
    这里先给几个示例值，你按自己 Java 枚举改掉即可：
      - DRAWING, CONTRACT, OTHER ...
    """
    DRAWING = "DRAWING"
    CONTRACT = "CONTRACT"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    """
    对应 Java enum DocumentStatus { UPLOADING, COMPLETED, FAILED, DELETED }:contentReference[oaicite:1]{index=1}
    """
    UPLOADING = "UPLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class Document(db.Model):
    __tablename__ = "t_documents"

    # 主键
    id = db.Column(db.BigInteger, primary_key=True)


    # 原始文件名
    file_name = db.Column("file_name", db.String(255), nullable=False)

    # 文件类型（枚举，字符串存储）
    file_type = db.Column(
        "file_type",
        db.Enum(FileType),
        nullable=True,
    )

    # 上传时间

    # MinIO 存储相关
    bucket = db.Column("bucket", db.String(128))
    object_key = db.Column("object_key", db.String(512))

    # 文件属性
    content_type = db.Column("content_type", db.String(255))
    size = db.Column("size", db.BigInteger)

    # 状态：UPLOADING / COMPLETED / FAILED / DELETED
    status = db.Column(
        "status",
        db.Enum(DocumentStatus),
        default=DocumentStatus.UPLOADING,
        nullable=True,
    )

    # ===== 如果你的 BaseEntity 里本来有创建/更新时间，可以在这里补上 =====
    # 没有的话，这两列可选：
    created_at = db.Column(
        "created_at",
        db.DateTime,
        default=datetime.utcnow,
    )
    updated_at = db.Column(
        "updated_at",
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f"<Document id={self.id} name={self.file_name}>"
