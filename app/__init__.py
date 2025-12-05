# backend/app/__init__.py
from flask import Flask, jsonify
from flask_cors import CORS

from .config import config_map
from .extensions import init_extensions
from .api import register_blueprints
from .utils.datetime_provider import BJJSONProvider
from .exceptions.exceptions import CustomAPIException  # 你的自定义异常:contentReference[oaicite:0]{index=0}


def handle_custom_api_exception(e: CustomAPIException):
    """
    全局处理 CustomAPIException，统一返回格式
    """
    return jsonify({
        "code": getattr(e, "code", 1),
        "message": getattr(e, "message", str(e)),
        "data": None,
    }), getattr(e, "status_code", 400)


def create_app(config_name: str = "dev") -> Flask:
    app = Flask(__name__)

    # CORS 设置（保持你原来的配置）
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:5173"}},
        supports_credentials=True,
    )

    # 加载配置
    cfg_cls = config_map.get(config_name, config_map["dev"])
    app.config.from_object(cfg_cls)

    # ⭐ 替换默认 JSON Provider —— datetime 自动转北京时间字符串
    app.json = BJJSONProvider(app)

    # 初始化扩展 & 注册蓝图
    init_extensions(app)
    register_blueprints(app)

    # ⭐ 在工厂函数里注册全局异常处理
    app.register_error_handler(CustomAPIException, handle_custom_api_exception)

    return app
