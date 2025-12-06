# backend/app/models/__init__.py
from ..extensions import db

from .user import User
from .document import Document
from .kb_models import KbFolder,KbFile,KbTag,KbFileTag
from .menu import Menu


__all__ = [
    "db",
    "User",
    "Document",
    "KbFolder",
    "KbFile",
    "KbTag",
    "KbFileTag",
]
