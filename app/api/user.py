# backend/app/api/user.py
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import User

bp = Blueprint("user", __name__)


@bp.route("/", methods=["POST"])
def create_user():
    """
    创建用户：
    {
      "username": "bill",
      "email": "xxx@example.com",
      "password": "123456",
      "user_fullname": "Bill Fu"
    }
    """
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    fullname = data.get("user_fullname")

    if not username or not password or not fullname:
        return jsonify({"error": "username, password, user_fullname required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 400

    user = User(
        username=username,
        email=email,
        user_fullname=fullname,
        status="active",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@bp.route("/", methods=["GET"])
def list_users():
    """
    ?status=active/disabled 可选
    """
    status = request.args.get("status")
    query = User.query
    if status:
        query = query.filter_by(status=status)

    users = query.order_by(User.id.desc()).all()
    return jsonify([u.to_dict() for u in users])


@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email")
    fullname = data.get("user_fullname")
    status = data.get("status")
    password = data.get("password")

    if username:
        # 检查重名
        exists = User.query.filter(User.id != user.id, User.username == username).first()
        if exists:
            return jsonify({"error": "username already exists"}), 400
        user.username = username

    if email is not None:
        user.email = email
    if fullname is not None:
        user.user_fullname = fullname
    if status in ("active", "disabled"):
        user.status = status
    if password:
        user.set_password(password)

    db.session.commit()
    return jsonify(user.to_dict())


@bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    """
    简单处理：把 status 改成 disabled
    """
    user = User.query.get_or_404(user_id)
    user.status = "disabled"
    db.session.commit()
    return jsonify({"message": "user disabled"})
