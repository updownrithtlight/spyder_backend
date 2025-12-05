# backend/app/models/menu.py
from datetime import datetime
from sqlalchemy import text

from ..extensions import db


class Menu(db.Model):
    __tablename__ = "t_menu_item"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_by = db.Column(db.String(255), default=None)

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )
    updated_by = db.Column(db.String(255), default=None)

    component = db.Column(db.String(255), nullable=False)   # 前端组件路径，例如 'pages/Dashboard'
    icon = db.Column(db.String(255), default=None)          # 图标名，例如 'DashboardOutlined'
    name = db.Column(db.String(255), nullable=False)        # 菜单显示名称
    path = db.Column(db.String(255), nullable=False)        # 路由 path，例如 '/dashboard'

    parent_id = db.Column(db.Integer, db.ForeignKey("t_menu_item.id"))

    # 自关联，parent_menu.children
    parent_menu = db.relationship(
        "Menu",
        remote_side=[id],
        backref=db.backref("children", lazy="subquery"),
        lazy="joined",
    )

    # 你可以后面加 sort_order、hidden 等字段

    def to_dict(self, include_children: bool = False):
        data = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by,
            "component": self.component,
            "icon": self.icon,
            "name": self.name,
            "path": self.path,
            "parent_id": self.parent_id,
        }

        if include_children:
            data["children"] = [
                child.to_dict(include_children=True) for child in self.children
            ]

        return data
