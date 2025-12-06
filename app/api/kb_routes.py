# app/routes/kb_routes.py
from flask import Blueprint
from app.services import kb_service

bp = Blueprint("kb", __name__)
# 目录树
@bp.route("/folders/tree", methods=["GET"])
def get_folder_tree():
    return kb_service.get_folder_tree()


# 新建目录
@bp.route("/folders", methods=["POST"])
def create_folder():
    return kb_service.create_folder()

# 指定目录下的文件
@bp.route("/files", methods=["GET"])
def list_files_by_folder():
    return kb_service.list_files_by_folder()

# 搜索文件（文件名 + 标签）
@bp.route("/search", methods=["GET"])
def search_files():
    return kb_service.search_files()

# 标签列表
@bp.route("/tags", methods=["GET"])
def list_tags():
    return kb_service.list_tags()

# 上传文件
@bp.route("/files/upload", methods=["POST"])
def upload_file():
    return kb_service.upload_file()

# 更新文件标签
@bp.route("/files/<int:file_id>/tags", methods=["POST"])
def update_file_tags(file_id):
    return kb_service.update_file_tags(file_id)


@bp.route("/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    return kb_service.delete_file(file_id)


# 下载文件
@bp.route("/files/<int:file_id>/download", methods=["GET"])
def download_file(file_id):
    return kb_service.download_file(file_id)


@bp.route("/folders/<int:folder_id>/rename", methods=["POST"])
def rename_folder(folder_id):
    return kb_service.rename_folder(folder_id)


@bp.route("/folders/<int:folder_id>", methods=["DELETE"])
def delete_folder(folder_id):
    return kb_service.delete_folder(folder_id)


