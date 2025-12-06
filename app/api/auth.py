# backend/app/api/auth.py
from flask import Blueprint, request, make_response, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies,
    jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies
)

from app.extensions import db  # 你在 extensions.py 里定义的 db、jwt
from app.models.user import User
from app.models.result import ResponseTemplate
from app.exceptions.exceptions import CustomAPIException

bp = Blueprint("auth", __name__)


# ========== 用户注册（可选） ==========

@bp.route("/register", methods=["POST"])
def register():
    """
    注册用户（如果不需要可删掉）：
    body: { "username": "...", "password": "...", "user_fullname": "..." }
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    user_fullname = (data.get("user_fullname") or "").strip()

    if not username or not password:
        raise CustomAPIException("用户名和密码不能为空", 400)

    if User.query.filter_by(username=username).first():
        raise CustomAPIException("用户名已存在", 400)

    # 假设 User 有 set_password / check_password 方法
    user = User(username=username, user_fullname=user_fullname or username)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise CustomAPIException(f"数据库错误: {e}", 500)

    return ResponseTemplate.success(message="注册成功")


# ========== 登录 ==========

@bp.route("/login", methods=["POST"])
def login():

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return ResponseTemplate.error("username and password required", code=400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return ResponseTemplate.error("Invalid username or password", code=401)

    if getattr(user, "status", "active") != "active":
        return ResponseTemplate.error("账号被禁用，请联系管理员", code=403)
    # identity 建议只放 id，其余信息放到 claims 里
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username},
        expires_delta=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES"),
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"username": user.username},
        expires_delta=current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES"),
    )

    resp = make_response(
        ResponseTemplate.success(
            message="Login successful",
            data={
                "access_token": access_token,  # 方便前端调试用，不一定要存
                "user": user.to_dict(),
            },
        )
    )
    # 写入 HttpOnly Cookie
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200


# ========== 刷新 Access Token（用 refresh cookie） ==========

@bp.route("/refresh-token", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    """
    刷新 Access Token：
    - 自动从 refresh_token_cookie 读 refresh token
    - 校验成功后发新的 access token，并写回 cookie
    """
    ident = get_jwt_identity()  # 字符串 id
    claims = get_jwt()          # 里有 username 等

    new_access = create_access_token(
        identity=ident,
        additional_claims={"username": claims.get("username")},
        expires_delta=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES"),
    )

    resp = make_response(
        ResponseTemplate.success(message="Access token refreshed")
    )
    set_access_cookies(resp, new_access)
    return resp, 200


# ========== 获取当前用户信息 ==========

@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    获取当前登录用户信息：
    - 优先从 cookie 检测 JWT（flask-jwt-extended 默认行为）
    """
    identity = get_jwt_identity()  # 字符串 id
    user = User.query.get(int(identity)) if identity else None
    if not user:
        raise CustomAPIException("用户不存在", 404)

    return ResponseTemplate.success(
        data=user.to_dict(),
        message="User details retrieved successfully",
    )


# ========== 修改密码（示例） ==========

@bp.route("/update-password", methods=["POST"])
@jwt_required()
def update_password():
    """
    修改密码：
    body:
    {
      "currentPassword": "...",
      "newPassword": "..."
    }
    """
    data = request.get_json() or {}
    current_password = data.get("currentPassword") or ""
    new_password = data.get("newPassword") or ""

    if not current_password or not new_password:
        raise CustomAPIException("当前密码和新密码不能为空", 400)

    identity = get_jwt_identity()
    user = User.query.get(int(identity)) if identity else None
    if not user:
        raise CustomAPIException("用户不存在", 404)

    if not user.check_password(current_password):
        raise CustomAPIException("当前密码错误", 401)

    try:
        user.set_password(new_password)
        db.session.add(user)
        db.session.commit()
        return ResponseTemplate.success(message="Password updated successfully")
    except Exception as e:
        db.session.rollback()
        raise CustomAPIException(f"Failed to update password: {e}", 500)


# ========== 退出登录 ==========

@bp.route("/logout", methods=["POST"])
def logout():
    """
    退出登录：
    - 清空 access / refresh cookie
    - 前端自己丢弃本地保存的 access_token（如果有）
    """
    resp = make_response(ResponseTemplate.success(message="Logged out"))
    unset_jwt_cookies(resp)
    return resp, 200
