# backend/app/api/menu.py
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Menu

bp = Blueprint("menu", __name__)


# 工具：构建树形结构
def build_menu_tree(items: list[Menu]) -> list[dict]:
    """
    把扁平的 Menu 列表转成树形结构：
    [
      { id, name, path, children: [...] },
      ...
    ]
    """
    # 先按 id 建个字典
    item_dict: dict[int, dict] = {}
    roots: list[dict] = []

    for m in items:
        item_dict[m.id] = m.to_dict(include_children=False)
        item_dict[m.id]["children"] = []

    # 建树
    for m in items:
        node = item_dict[m.id]
        if m.parent_id and m.parent_id in item_dict:
            item_dict[m.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


@bp.route("/tree", methods=["GET"])
def get_menu_tree():
    """
    获取树形菜单，用于前端侧边栏/顶部导航。
    前端直接拿这个 JSON 构建菜单即可。
    """
    # 这里暂时不分页，全部取出
    menus = Menu.query.order_by(Menu.id.asc()).all()
    tree = build_menu_tree(menus)
    return jsonify(tree)


@bp.route("/", methods=["GET"])
def list_menus():
    """
    扁平列表，后台菜单管理页面用。
    """
    menus = Menu.query.order_by(Menu.id.asc()).all()
    return jsonify([m.to_dict(include_children=False) for m in menus])


@bp.route("/", methods=["POST"])
def create_menu():
    """
    创建菜单：
    {
      "name": "Dashboard",
      "path": "/dashboard",
      "component": "pages/Dashboard",
      "icon": "DashboardOutlined",
      "parent_id": 1,          # 可选
      "created_by": "admin"
    }
    """
    data = request.get_json() or {}

    name = data.get("name")
    path = data.get("path")
    component = data.get("component")

    if not name or not path or not component:
        return jsonify({"error": "name, path, component required"}), 400

    menu = Menu(
        name=name,
        path=path,
        component=component,
        icon=data.get("icon"),
        parent_id=data.get("parent_id"),
        created_by=data.get("created_by"),
        updated_by=data.get("created_by"),
    )

    db.session.add(menu)
    db.session.commit()

    return jsonify(menu.to_dict(include_children=False)), 201


@bp.route("/<int:menu_id>", methods=["PUT"])
def update_menu(menu_id: int):
    """
    更新菜单：
    body 可包含任意字段：
    {
      "name": "...",
      "path": "...",
      "component": "...",
      "icon": "...",
      "parent_id": 1,
      "updated_by": "admin"
    }
    """
    menu = Menu.query.get_or_404(menu_id)
    data = request.get_json() or {}

    if "name" in data:
        menu.name = data["name"]
    if "path" in data:
        menu.path = data["path"]
    if "component" in data:
        menu.component = data["component"]
    if "icon" in data:
        menu.icon = data["icon"]
    if "parent_id" in data:
        menu.parent_id = data["parent_id"]
    if "updated_by" in data:
        menu.updated_by = data["updated_by"]

    db.session.commit()
    return jsonify(menu.to_dict(include_children=False))


@bp.route("/<int:menu_id>", methods=["DELETE"])
def delete_menu(menu_id: int):
    """
    删除菜单项（会把它从树中移除）
    简单版：直接硬删。你也可以改成 is_deleted 软删。
    """
    menu = Menu.query.get_or_404(menu_id)
    db.session.delete(menu)
    db.session.commit()
    return jsonify({"message": "menu deleted"})
