import os
from flask import request, current_app, send_file
from app.models.kb_models import KbFolder, KbFile, KbTag
from app.models.result import ResponseTemplate
from app.exceptions.exceptions import CustomAPIException
from ..extensions import db

def _build_folder_path(folder: KbFolder) -> str:
    """返回类似 '根目录 / 子目录 / 子子目录' 的路径"""
    parts = []
    cur = folder
    while cur:
        parts.append(cur.name)
        cur = cur.parent
    return " / ".join(reversed(parts))


def get_folder_tree():
    """获取目录树结构"""
    folders = (
        KbFolder.query
        .filter_by(is_deleted=False)
        .order_by(KbFolder.sort_order, KbFolder.id)
        .all()
    )

    node_map = {}
    for f in folders:
        node_map[f.id] = {
            "id": f.id,
            "title": f.name,
            "key": str(f.id),
            "children": []
        }

    roots = []
    for f in folders:
        node = node_map[f.id]
        if f.parent_id and f.parent_id in node_map:
            node_map[f.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return ResponseTemplate.success(
        message="获取目录树成功",
        data=roots
    )


def create_folder():
    """
    新建目录
    JSON body:
      {
        "name": "施工方案",
        "parent_id": 1,        # 可选，根目录传null或不传
        "sort_order": 0        # 可选
      }
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        raise CustomAPIException("请求体必须是 JSON", 400)

    name = (data.get("name") or "").strip()
    if not name:
        raise CustomAPIException("目录名称不能为空", 400)

    parent_id = data.get("parent_id")
    sort_order = data.get("sort_order", 0)

    parent = None
    if parent_id:
        parent = KbFolder.query.filter_by(id=parent_id, is_deleted=False).first()
        if not parent:
            raise CustomAPIException("父目录不存在", 404)

    folder = KbFolder(
        name=name,
        parent_id=parent.id if parent else None,
        sort_order=sort_order or 0,
        is_deleted=False,
    )

    db.session.add(folder)
    db.session.commit()

    # 前端树节点格式
    node = {
        "id": folder.id,
        "title": folder.name,
        "key": str(folder.id),
        "children": []
    }

    return ResponseTemplate.success(
        message="创建目录成功",
        data=node
    )


from sqlalchemy import asc, desc  # 确保有这个导入

def list_files_by_folder():
    """根据目录列出文件"""
    folder_id = request.args.get("folder_id", type=int)
    if not folder_id:
        raise CustomAPIException("缺少 folder_id 参数", 400)

    # ⭐ 新增：排序参数
    sort_field = (request.args.get("sort_field") or "updated_at").strip()
    sort_order = (request.args.get("sort_order") or "desc").strip().lower()

    # 允许的排序字段映射
    sort_map = {
        "name": KbFile.name,
        "updated_at": KbFile.updated_at,
        "file_type": KbFile.file_type,
    }
    order_col = sort_map.get(sort_field, KbFile.updated_at)  # 默认按更新时间

    # 升降序
    if sort_order == "asc":
        order_by_expr = asc(order_col)
    else:
        order_by_expr = desc(order_col)

    files = (
        KbFile.query
        .filter(KbFile.folder_id == folder_id, KbFile.is_deleted == False)
        .order_by(order_by_expr)
        .all()
    )

    data = []
    for f in files:
        data.append({
            "id": f.id,
            "name": f.name,
            "folder_id": f.folder_id,
            "document_id": f.document_id,
            "file_type": f.file_type,
            "description": f.description,
            "version": f.version,
            "updated_at": f.updated_at,
            "tags": [t.name for t in f.tags],
        })

    return ResponseTemplate.success(
        message="获取文件列表成功",
        data=data
    )

from sqlalchemy import asc, desc  # 同样需要这个导入

def search_files():
    """
    文件搜索：支持文件名 + 标签
    GET 参数：
      q:          模糊匹配文件名
      tags:       逗号分隔的标签名列表（满足其一即可）
      sort_field: name / updated_at / file_type （可选）
      sort_order: asc / desc （可选）
    """
    q_str = request.args.get("q", "", type=str).strip()
    tag_str = request.args.get("tags", "", type=str).strip()

    # ⭐ 新增：排序参数
    sort_field = (request.args.get("sort_field") or "updated_at").strip()
    sort_order = (request.args.get("sort_order") or "desc").strip().lower()

    sort_map = {
      "name": KbFile.name,
      "updated_at": KbFile.updated_at,
      "file_type": KbFile.file_type,
    }
    order_col = sort_map.get(sort_field, KbFile.updated_at)

    if sort_order == "asc":
        order_by_expr = asc(order_col)
    else:
        order_by_expr = desc(order_col)

    query = KbFile.query.filter(KbFile.is_deleted == False)

    # 文件名模糊搜索
    if q_str:
        like = f"%{q_str}%"
        query = query.filter(KbFile.name.like(like))

    # 标签过滤：当前简单逻辑是“包含任意一个标签”
    if tag_str:
        tags = [t.strip() for t in tag_str.split(",") if t.strip()]
        if tags:
            query = query.join(KbFile.tags).filter(KbTag.name.in_(tags)).distinct()

    # ⭐ 应用排序
    files = query.order_by(order_by_expr).all()

    data = []
    for f in files:
        folder_path = _build_folder_path(f.folder) if f.folder else ""
        data.append({
            "id": f.id,
            "name": f.name,
            "folder_id": f.folder_id,
            "folder_path": folder_path,
            "document_id": f.document_id,
            "file_type": f.file_type,
            "description": f.description,
            "version": f.version,
            "updated_at": f.updated_at,
            "tags": [t.name for t in f.tags],
        })

    return ResponseTemplate.success(
        message="搜索文件成功",
        data=data
    )


def list_tags():
    """列出所有标签（用于前端下拉多选）"""
    tags = KbTag.query.order_by(KbTag.name).all()
    data = [
        {
            "id": t.id,
            "name": t.name,
            "color": t.color,
        }
        for t in tags
    ]
    return ResponseTemplate.success(
        message="获取标签列表成功",
        data=data
    )




# ……上面的函数保持不变……

def _get_or_create_tags(tag_names):
    """根据标签名列表获取/创建标签对象列表"""
    if not tag_names:
        return []

    clean_names = [t.strip() for t in tag_names if t.strip()]
    if not clean_names:
        return []

    existing_tags = KbTag.query.filter(KbTag.name.in_(clean_names)).all()
    existing_map = {t.name: t for t in existing_tags}

    result = []
    for name in clean_names:
        tag = existing_map.get(name)
        if not tag:
            tag = KbTag(name=name)
            db.session.add(tag)
            existing_map[name] = tag
        result.append(tag)
    return result

def upload_file():
    """
    登记已经上传到 MinIO 的知识库文件（只写元数据，不处理文件流）

    JSON body:
      {
        "folder_id": 1,                         # 必填：所属目录
        "name": "施工方案 v1.pdf",             # 可选，不填则从 document_id / object_key 推断
        "document_id": "kb/1/2025/....pdf",   # 必填：MinIO 对象 key 或完整 URL
        "file_type": "pdf",                    # 可选，不填则根据 name/document_id 后缀推断
        "description": "二沉池施工方案",        # 可选
        "version": 1,                          # 可选，默认 1
        "tags": ["施工方案", "二沉池"]          # 可选，数组
      }
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        raise CustomAPIException("请求体必须是 JSON", 400)

    folder_id = data.get("folder_id")
    if not folder_id:
        raise CustomAPIException("缺少 folder_id", 400)

    folder = KbFolder.query.filter_by(id=folder_id, is_deleted=False).first()
    if not folder:
        raise CustomAPIException("目录不存在", 404)

    document_id = data.get("document_id")
    if not document_id:
        raise CustomAPIException("document_id 不能为空", 400)

    # 显示名：优先用传入的 name，没有就从路径里截取文件名
    name = (data.get("name") or "").strip()
    if not name:
        # 尝试从 document_id 里取最后一段
        name = document_id.split("/")[-1] or document_id

    # 文件类型：优先用传入的 file_type，否则从 name 或 document_id 后缀推断
    file_type = (data.get("file_type") or "").strip()
    if not file_type:
        candidate = name or document_id
        if "." in candidate:
            file_type = candidate.rsplit(".", 1)[-1].lower()

    description = data.get("description")
    version = data.get("version") or 1

    kb_file = KbFile(
        folder_id=folder_id,
        name=name,
        document_id=document_id,   # 这里一般存 MinIO object_key 或外部 URL
        file_type=file_type,
        description=description,
        version=version,
        is_deleted=False,
    )

    # 处理标签
    tags = data.get("tags") or []
    if tags and not isinstance(tags, list):
        raise CustomAPIException("tags 必须是数组", 400)

    if tags:
        tag_objs = _get_or_create_tags(tags)
        kb_file.tags = tag_objs
    else:
        tag_objs = []

    db.session.add(kb_file)
    db.session.commit()

    return ResponseTemplate.success(
        message="文件登记成功",
        data={
            "id": kb_file.id,
            "name": kb_file.name,
            "folder_id": kb_file.folder_id,
            "document_id": kb_file.document_id,
            "file_type": kb_file.file_type,
            "description": kb_file.description,
            "version": kb_file.version,
            "tags": [t.name for t in tag_objs],
            "created_at": kb_file.created_at,
            "updated_at": kb_file.updated_at,
        }
    )




def update_file_tags(file_id: int):
    """
    更新某个文件的标签
    JSON body:
      { "tags": ["标签1", "标签2"] }
    """
    kb_file = KbFile.query.filter_by(id=file_id, is_deleted=False).first()
    if not kb_file:
        raise CustomAPIException("文件不存在", 404)

    try:
        data = request.get_json(force=True) or {}
    except Exception:
        raise CustomAPIException("请求体必须是 JSON", 400)

    tags = data.get("tags") or []
    if not isinstance(tags, list):
        raise CustomAPIException("tags 必须是数组", 400)

    # 根据名字获取或创建标签
    tag_objs = _get_or_create_tags(tags)

    # 替换标签
    kb_file.tags = tag_objs
    db.session.commit()

    return ResponseTemplate.success(
        message="标签更新成功",
        data={
            "id": kb_file.id,
            "tags": [t.name for t in kb_file.tags],
        }
    )



# ... 你上面的函数保持不变 ...

def download_file(file_id: int):
    """
    获取指定文件的下载信息（不再由后端流式返回文件）

    GET /api/kb/files/<file_id>/download

    返回：
      {
        "code": 0,
        "message": "获取文件下载地址成功",
        "data": {
          "id": 1,
          "name": "xxx.pdf",
          "document_id": "kb/1/2025/....pdf",  # 一般是 MinIO object_key 或外部 URL
          "file_type": "pdf",
          "description": "...",
          "tags": ["施工方案", "二沉池"]
        }
      }
    """
    kb_file = KbFile.query.filter_by(id=file_id, is_deleted=False).first()
    if not kb_file:
        raise CustomAPIException("文件不存在", 404)

    if not kb_file.document_id:
        raise CustomAPIException("文件存储路径为空", 404)

    return ResponseTemplate.success(
        message="获取文件下载地址成功",
        data={
            "id": kb_file.id,
            "name": kb_file.name,
            "folder_id": kb_file.folder_id,
            "document_id": kb_file.document_id,   # 前端用这个去请求 MinIO / 文件服务
            "file_type": kb_file.file_type,
            "description": kb_file.description,
            "version": kb_file.version,
            "tags": [t.name for t in kb_file.tags],
            "updated_at": kb_file.updated_at,
        }
    )


def delete_file(file_id: int):
  """
  软删除文件（置 is_deleted = True）
  DELETE /api/kb/files/<file_id>
  """
  kb_file = KbFile.query.filter_by(id=file_id, is_deleted=False).first()
  if not kb_file:
      raise CustomAPIException("文件不存在", 404)

  kb_file.is_deleted = True
  db.session.commit()


  return ResponseTemplate.success(
      message="文件删除成功",
      data={"id": file_id}
  )


def rename_folder(folder_id):
    """
    重命名文件夹
    JSON body:
      {
        "name": "新文件夹名称"
      }
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        raise CustomAPIException("请求体必须是 JSON", 400)

    new_name = (data.get("newName") or "").strip()
    if not new_name:
        raise CustomAPIException("文件夹名称不能为空", 400)

    folder = KbFolder.query.filter_by(id=folder_id, is_deleted=False).first()
    if not folder:
        raise CustomAPIException("文件夹不存在", 404)

    folder.name = new_name
    db.session.commit()

    return ResponseTemplate.success(
        message="文件夹重命名成功",
        data={
            "id": folder.id,
            "name": folder.name,
        }
    )

def delete_folder(folder_id):
    """
    删除文件夹（软删除）
    DELETE /api/kb/folders/<folder_id>
    """
    folder = KbFolder.query.filter_by(id=folder_id, is_deleted=False).first()
    if not folder:
        raise CustomAPIException("文件夹不存在", 404)

    # 软删除该文件夹
    folder.is_deleted = True

    # 删除该文件夹下的所有文件（软删除）
    files = KbFile.query.filter_by(folder_id=folder.id, is_deleted=False).all()
    for file in files:
        file.is_deleted = True

    # 删除该文件夹下的所有子文件夹（递归删除）
    subfolders = KbFolder.query.filter_by(parent_id=folder.id, is_deleted=False).all()
    for subfolder in subfolders:
        delete_folder(subfolder.id)  # Recursive delete

    db.session.commit()

    return ResponseTemplate.success(
        message="文件夹及其所有内容删除成功",
        data={"id": folder.id}
    )

