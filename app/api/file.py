# # backend/app/api/file.py
# from flask import Blueprint, request, jsonify, current_app
# from ..extensions import db
# from ..models import FileObject, User, Folder, Document
# from ..services.minio_signer import sign_put_object, build_public_url, delete_object
# from ..services.onlyoffice_client import build_onlyoffice_config
#
# bp = Blueprint("file", __name__)
#
#
# @bp.route("/sign-upload", methods=["POST"])
# def sign_upload():
#     """
#     获取 MinIO 直传的预签名 URL
#     body:
#     {
#       "filename": "xxx.docx",
#       "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#       "folder": "docs"
#     }
#     """
#     data = request.get_json() or {}
#     filename = data.get("filename")
#     content_type = data.get("contentType", "application/octet-stream")
#     folder = data.get("folder")
#
#     if not filename:
#         return jsonify({"error": "filename required"}), 400
#
#     signed = sign_put_object(filename, content_type, folder)
#     return jsonify(signed)
#
#
# @bp.route("/", methods=["POST"])
# def create_file_record():
#     """
#     在前端上传 MinIO 成功后调用，记录文件信息：
#     {
#       "object_key": "...",
#       "original_name": "xxx.docx",
#       "mime_type": "application/...",
#       "size": 12345,
#       "uploader_id": 1,       # 可选
#       "folder_id": 10,        # 可选
#       "tag_ids": [1, 2, 3]    # 可选（如果你以后做 tag api）
#     }
#     """
#     from ..models import Tag  # 避免循环引用
#
#     data = request.get_json() or {}
#     object_key = data.get("object_key")
#     if not object_key:
#         return jsonify({"error": "object_key required"}), 400
#
#     existing = FileObject.query.filter_by(object_key=object_key).first()
#     if existing:
#         return jsonify(existing.to_dict()), 200
#
#     file = FileObject(
#         object_key=object_key,
#         original_name=data.get("original_name"),
#         mime_type=data.get("mime_type"),
#         size=data.get("size"),
#     )
#
#     uploader_id = data.get("uploader_id")
#     if uploader_id:
#         user = User.query.get(uploader_id)
#         if user:
#             file.uploader = user
#
#     folder_id = data.get("folder_id")
#     if folder_id:
#         folder = Folder.query.get(folder_id)
#         if folder:
#             file.folder = folder
#
#     tag_ids = data.get("tag_ids") or []
#     if tag_ids:
#         tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
#         file.tags = tags
#
#     db.session.add(file)
#     db.session.commit()
#
#     return jsonify(file.to_dict()), 201
#
#
# @bp.route("/", methods=["GET"])
# def list_files():
#     """
#     支持简单过滤：?folder_id= &uploader_id=
#     """
#     folder_id = request.args.get("folder_id", type=int)
#     uploader_id = request.args.get("uploader_id", type=int)
#
#     q = FileObject.query
#     if folder_id:
#         q = q.filter_by(folder_id=folder_id)
#     if uploader_id:
#         q = q.filter_by(uploader_id=uploader_id)
#
#     files = q.order_by(FileObject.id.desc()).all()
#     return jsonify([f.to_dict() for f in files])
#
#
# @bp.route("/<int:file_id>", methods=["GET"])
# def get_file(file_id: int):
#     file = FileObject.query.get_or_404(file_id)
#     data = file.to_dict()
#     data["public_url"] = build_public_url(file.object_key)
#     return jsonify(data)
#
#
# @bp.route("/<int:file_id>", methods=["DELETE"])
# def delete_file(file_id: int):
#     """
#     删除文件记录 + MinIO 对象
#     """
#     file = FileObject.query.get_or_404(file_id)
#     object_key = file.object_key
#
#     # 先删除 MinIO 文件（失败了可以按需处理）
#     try:
#         delete_object(object_key)
#     except Exception as e:
#         current_app.logger.error(f"Delete MinIO object failed: {e}")
#
#     db.session.delete(file)
#     db.session.commit()
#     return jsonify({"message": "file deleted"})
#
#
# @bp.route("/onlyoffice-config", methods=["GET"])
# def onlyoffice_config():
#     """
#     前端传 ?file_id=xxx 或 ?object_key=xxx，两种方式都支持
#     返回 OnlyOffice 编辑器配置
#     """
#     file_id = request.args.get("file_id", type=int)
#     object_key = request.args.get("object_key")
#
#     file = None
#     if file_id:
#         file = FileObject.query.get_or_404(file_id)
#         object_key = file.object_key
#     elif object_key:
#         file = FileObject.query.filter_by(object_key=object_key).first()
#     else:
#         return jsonify({"error": "file_id or object_key required"}), 400
#
#     if not file:
#         return jsonify({"error": "file not found"}), 404
#
#     document_url = build_public_url(object_key)
#     callback_url = request.url_root.rstrip("/") + "/api/files/onlyoffice-callback"
#
#     # 根据后缀判断文件类型
#     file_type = "docx"
#     if file.original_name and "." in file.original_name:
#         ext = file.original_name.rsplit(".", 1)[1].lower()
#         mapping = {
#             "docx": "docx",
#             "doc": "doc",
#             "xlsx": "xlsx",
#             "xls": "xls",
#             "pptx": "pptx",
#             "ppt": "ppt",
#             "txt": "txt",
#         }
#         file_type = mapping.get(ext, "docx")
#
#     title = file.original_name or object_key.split("/")[-1]
#
#     data = build_onlyoffice_config(
#         document_url=document_url,
#         callback_url=callback_url,
#         file_type=file_type,
#         title=title,
#     )
#
#     # 自动创建 DocumentRecord（如果不存在）
#     doc = DocumentRecord.query.filter_by(object_key=object_key).first()
#     if not doc:
#         doc = DocumentRecord(file=file, object_key=object_key, status=0)
#         db.session.add(doc)
#         db.session.commit()
#
#     data["document_id"] = doc.id
#
#     return jsonify(data)
#
#
# @bp.route("/onlyoffice-callback", methods=["POST"])
# def onlyoffice_callback():
#     """
#     OnlyOffice 回调，更新 DocumentRecord.status
#     payload 大致包括：
#     {
#       "key": "<document key>",
#       "status": 2,
#       ...
#     }
#     """
#     payload = request.get_json() or {}
#     current_app.logger.info(f"OnlyOffice callback: {payload}")
#
#     key = payload.get("key")  # 文档 key，通常你可以用 object_key 或自定义
#     status = payload.get("status")
#
#     if key:
#         doc = DocumentRecord.query.filter_by(object_key=key).first()
#         if doc:
#             if isinstance(status, int):
#                 doc.status = status
#             db.session.commit()
#
#     return jsonify({"error": 0})
