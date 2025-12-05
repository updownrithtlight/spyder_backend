# backend/app/models/__init__.py
from ..extensions import db

from .user import User
from .file import FileObject
from .document import Document
from .kb_models import KbFolder,KbFile,KbTag,KbFileTag
from .folder import Folder
from .tag import Tag, file_tag_table
from .menu import Menu


__all__ = [
    "db",
    "User",
    "FileObject",
    "Document",
    "Folder",
    "Tag",
    "file_tag_table",
    "KbFolder",
    "KbFile",
    "KbTag",
    "KbFileTag",
]
