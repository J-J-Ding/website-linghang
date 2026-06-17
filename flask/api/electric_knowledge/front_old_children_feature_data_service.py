from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import pandas as pd
from io import BytesIO

from electric_knowledge.data_model import db, OLD_CHILDREN_FEATURE_TABLE
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'


# 定义查询参数模型
class OldChildrenFeatureData(BaseModel):
    id: Optional[str] = None
    old_children_feature_name: Optional[str] = Field(None, alias="oldSubFeature")
    children_feature_name: Optional[str] = Field(None, alias="subFeature")
    current_status: Optional[str] = Field(None, alias="status")
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    operator_person: Optional[str] = None
    effective_flag: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,    # 允许ORM转换
        populate_by_name=True,   # 关键：按字段名填充数据
        arbitrary_types_allowed=True
    )

    @field_validator('id', mode='before')
    @classmethod
    def convert_id_to_string(cls, value) -> str:
        """将id转换为字符串类型"""
        if value is None:
            return ''
        return str(value)


# 业务方案要素因子
def querySrcOldChildrenFeatureDataByParams(query_params:dict):    # 构建基础查询
    conditions = [OLD_CHILDREN_FEATURE_TABLE.effective_flag == 'Y']
    oldChildrenFeatureData = OldChildrenFeatureData(**query_params)
    if oldChildrenFeatureData.old_children_feature_name:
        conditions.append(OLD_CHILDREN_FEATURE_TABLE.old_children_feature_name.in_(oldChildrenFeatureData.old_children_feature_name.split(',')))
    if oldChildrenFeatureData.children_feature_name:
        conditions.append(OLD_CHILDREN_FEATURE_TABLE.children_feature_name.in_(oldChildrenFeatureData.children_feature_name.split(',')))
    if oldChildrenFeatureData.current_status:
        conditions.append(OLD_CHILDREN_FEATURE_TABLE.current_status.in_(oldChildrenFeatureData.current_status.split(',')))
    try:
        baseOldChildrenFeatureData = db.session.query(OLD_CHILDREN_FEATURE_TABLE).filter(and_(*conditions)).all() 
        results = [OldChildrenFeatureData.model_validate(item).model_dump(by_alias=True) for item in baseOldChildrenFeatureData]
                 
        return results
    except Exception as e:
        return []

# 业务方案要素因子
def queryOldChildrenFeatureDataByParams():    # 构建基础查询
    """
    查询指定的旧子特性-新子特性取值
    ---
    tags:
      - 特性-子特性
    description: 查询指定的特性-子特性取值
    parameters:
      - name: oldSubFeature
        in: query
        description: 旧的子特性
        required: false
        type: string
      - name: subFeature
        in: query
        description: 新的子特性
        required: false
        type: string
      - name: status
        in: query
        description: 当前状态
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [{
      "status": "正常",
      "effective_flag": "Y",
      "update_time": "Thu, 10 Jul 2025 22:12:08 GMT"
    }]}
    """
    try:    
        query_params = request.args.to_dict()
        results = querySrcOldChildrenFeatureDataByParams(query_params)
                 
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": []})


def importExcelOldChildrenFeatureData():
    """
    Excel文件上传接口
    ---
    tags:
      - 特性-子特性
    description: 接收POST请求，通过Header传递工号，通过form-data上传Excel文件
    consumes:  # 关键：指定请求内容类型
      - multipart/form-data
    parameters:
      - name: X-Emp-No
        in: header
        description: 员工工号，用于身份验证
        required: true
        type: string
        example: "10329743"
      - name: file  # form-data参数名
        in: formData     # 指定为表单数据
        description: 上传的Excel文件(xlsx格式)
        required: true
        type: file       # 文件类型
        x-mimetype: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet  # 可选MIME类型限制    
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
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)

    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
        
    file = request.files['file']
    # 检查文件类型

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
    
    try:
     
        df = pd.read_excel(file, engine="openpyxl")
        df["旧标准子特性"] = df["旧标准子特性"].ffill()
        df = df.fillna(value='')
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['old_children_feature_name'] = row["旧标准子特性"] if "旧标准子特性" in row else '' 
            table_dict['children_feature_name'] = row["新标准子特性"] if "新标准子特性" in row else '' 
            db_factor_values = db.session.query(OLD_CHILDREN_FEATURE_TABLE).filter(and_(OLD_CHILDREN_FEATURE_TABLE.old_children_feature_name == table_dict['old_children_feature_name'],
                                                                                      OLD_CHILDREN_FEATURE_TABLE.children_feature_name == table_dict["children_feature_name"]
                                                                       )).all()
            if len(db_factor_values) < 1 :
                insert_sql = insert(OLD_CHILDREN_FEATURE_TABLE).values(old_children_feature_name=table_dict['old_children_feature_name'], 
                                                                                children_feature_name=table_dict["children_feature_name"],  current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
        db.session.commit()

        db.session.refresh(db.session.query(OLD_CHILDREN_FEATURE_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        raise e
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")