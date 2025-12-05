
# backend/app/api/auth.py
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, current_app, jsonify, request, make_response

from ..models import User

bp = Blueprint("auth", __name__)


# --------- 工具函数 --------- #

def _now_utc():
    return datetime.now(timezone.utc)


def _create_access_token(user: User) -> str:
    """短期 Access Token：放到响应 JSON，让前端存 sessionStorage"""
    now = _now_utc()
    minutes = current_app.config["JWT_ACCESS_EXPIRES_MINUTES"]
    payload = {
        "sub": user.id,
        "username": user.username,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    secret = current_app.config["JWT_ACCESS_SECRET"]
    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _create_refresh_token(user: User) -> str:
    """长期 Refresh Token：只放在 HttpOnly Cookie 中"""
    now = _now_utc()
    days = current_app.config["JWT_REFRESH_EXPIRES_DAYS"]
    payload = {
        "sub": user.id,
        "username": user.username,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=days),
    }
    secret = current_app.config["JWT_REFRESH_SECRET"]
    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _decode_access_token(token: str):
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_ACCESS_SECRET"],
            algorithms=["HS256"],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.InvalidTokenError:
        return None


def _decode_refresh_token(token: str):
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_REFRESH_SECRET"],
            algorithms=["HS256"],
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.InvalidTokenError:
        return None


def _set_refresh_cookie(resp, refresh_token: str):
    """
    把 refresh_token 写到 HttpOnly Cookie.
    dev 环境先不用 secure=True，线上用 https 时一定要 secure=True
    """
    max_age = current_app.config["JWT_REFRESH_EXPIRES_DAYS"] * 24 * 3600
    resp.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=False,  # 本地开发 http；上线 https 请改 True
        path="/",
    )


def _clear_refresh_cookie(resp):
    resp.set_cookie(
        "refresh_token",
        "",
        expires=0,
        path="/",
    )


# --------- 路由 --------- #

@bp.route("/login", methods=["POST"])
def login():
    """
    登录：
    body:
    {
      "username": "bill",
      "password": "123456"
    }

    返回：
    {
      "access_token": "...",
      "user": {...}
    }
    同时在 Set-Cookie 里下发 refresh_token（HttpOnly）
    """
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid username or password"}), 401

    if user.status != "active":
        return jsonify({"error": "user disabled"}), 403

    access_token = _create_access_token(user)
    refresh_token = _create_refresh_token(user)

    resp = make_response(
        jsonify(
            {
                "access_token": access_token,
                "user": user.to_dict(),
            }
        )
    )
    _set_refresh_cookie(resp, refresh_token)
    return resp


@bp.route("/refresh-token", methods=["POST"])
def refresh_token():
    """
    刷新 Access Token：
    - 从 Cookie 里读 refresh_token
    - 校验成功则生成新的 access_token（可选择是否轮换 refresh_token）
    返回：
    {
      "access_token": "..."
    }
    """
    token = request.cookies.get("refresh_token")
    payload = _decode_refresh_token(token)
    if not payload:
        return jsonify({"error": "invalid or expired refresh token"}), 401

    user = User.query.get(payload.get("sub"))
    if not user:
        return jsonify({"error": "user not found"}), 404

    # 生成新的 access_token
    access_token = _create_access_token(user)

    # 是否轮换 refresh_token，看你需要，这里简单起见不轮换
    resp = make_response(jsonify({"access_token": access_token}))
    # 如果想轮换，可以重新生成并写 cookie:
    # new_refresh = _create_refresh_token(user)
    # _set_refresh_cookie(resp, new_refresh)

    return resp


@bp.route("/me", methods=["GET"])
def me():
    """
    获取当前登录用户：
    Header: Authorization: Bearer <access_token>
    """
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    else:
        token = None

    payload = _decode_access_token(token)
    if not payload:
        return jsonify({"error": "invalid or expired token"}), 401

    user_id = payload.get("sub")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({"user": user.to_dict()})


@bp.route("/logout", methods=["POST"])
def logout():
    """
    退出登录：清空 refresh_token cookie，前端自己删掉 access_token
    """
    resp = make_response(jsonify({"message": "logout ok"}))
    _clear_refresh_cookie(resp)
    return resp
