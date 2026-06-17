import os
import uuid
import re
import mimetypes
from datetime import datetime, timedelta
from flask import Flask, request, send_file, jsonify, abort
from werkzeug.utils import secure_filename

from electric_knowledge.data_model import db, PRODUCT_IMAGE_TABLE

# /otn_ai/project/gzj/uploads
env = os.environ
IMAGE_ENV_PATH = '/otn_ai/' + env.get("IMAGE_ENV","") + '/gzj/uploads' if env.get("IMAGE_ENV","") else './uploads'

# 工具函数
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']

def generate_image_id():
    return f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

def get_image_path(image_id, extension=None):
    if extension:
        return os.path.join(IMAGE_ENV_PATH, f"{image_id}.{extension}")
    return os.path.join(IMAGE_ENV_PATH, image_id)

# API 端点
def upload_image():
    """
    产品知识图片上传接口
    ---
    tags:
      - 产品知识图片
    description: 接收POST请求，通过Header传递工号，通过form-data上传Excel文件
    consumes:  # 关键：指定请求内容类型
      - multipart/form-data
    parameters:
      - name: file  # form-data参数名
        in: formData     # 指定为表单数据
        description: 上传的图片文件(图片格式)
        required: true
        type: file       # 文件类型
        x-mimetype: image/*    
    responses:
      200:
        description: 文件上传成功，数据已写入数据库
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "成功导入文件"
      400:
        description: 请求参数错误
        schema:
          type: object
          properties:
            error:
              type: string
              example: "无效的文件格式"
      401:
        description: 身份验证失败
        schema:
          type: object
          properties:
            error:
              type: string
              example: "无效的工号"
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一ID
        image_id = generate_image_id()
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # 保存文件
        file_path = os.path.join(IMAGE_ENV_PATH, f"{image_id}.{extension}")
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # 创建数据库记录
        image = PRODUCT_IMAGE_TABLE(
            id=image_id,
            filename=filename,
            extension=extension,
            mime_type=mime_type,
            size=file_size,
            upload_time=datetime.utcnow(),
            is_deleted=0,
            delete_time=datetime.utcnow() + timedelta(days=30)
            # 可添加过期时间: delete_time=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(image)
        db.session.commit()
        
        return jsonify({"code":200, "data": image.to_dict()})
    
    return jsonify({"code":400 ,"error": "File type not allowed"})

def get_image(image_id):
    """
    查询指定的产品知识图片
    ---
    tags:
      - 产品知识图片
    description: 查询指定的产品知识图片
    parameters:
      - name: image_id
        in: path
        description: 图片id
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": []}
    """
    # query_params = request.args.to_dict()
    # image_id = query_params.get('image_id', "")

    # 验证ID格式
    if not re.match(r'^\d{14}_[a-f0-9]{8}$', image_id):
        abort(400, description="Invalid image ID format")
    
    # 从数据库查询
    image = PRODUCT_IMAGE_TABLE.query.filter_by(id=image_id, is_deleted=False).first()
    if not image:
        abort(404, description="PRODUCT_IMAGE_TABLE not found")
    
    # 构建文件路径
    file_path = os.path.join(IMAGE_ENV_PATH, f"{image_id}.{image.extension}")
    
    # 验证文件是否存在
    if not os.path.exists(file_path):
        # 文件丢失，更新数据库
        # image.is_deleted = True
        db.session.commit()
        abort(500, description="images file missing at servers file system")
    
    # 返回图片
    response = send_file(
        file_path,
        mimetype=image.mime_type,
        conditional=True
    )
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    response.headers['X-PRODUCT_IMAGE_TABLE-ID'] = image.id
    response.headers['X-PRODUCT_IMAGE_TABLE-Filename'] = image.filename
    
    return response
