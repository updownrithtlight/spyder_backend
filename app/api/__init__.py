from . import user, document, menu, auth, kb_routes, onlyoffice,onlyoffice_local_router


def register_blueprints(app):
    app.register_blueprint(user.bp, url_prefix="/api/users")
    app.register_blueprint(document.bp, url_prefix="/api/file")
    app.register_blueprint(menu.bp, url_prefix="/api/menus")   # ⭐ 新增菜单 API
    app.register_blueprint(auth.bp, url_prefix="/api/auth")   # ★ 新增
    app.register_blueprint(kb_routes.bp, url_prefix="/api/kb")   # ★ 新增
    app.register_blueprint(onlyoffice.bp, url_prefix="/api/onlyoffice")
