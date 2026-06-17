from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import pandas as pd
from electric_knowledge.utils_pub import pub_get_employ_name
from io import BytesIO

from electric_knowledge.data_model import db, MODULE_FEATURECHECKPOINT_CONTENT_TABLE, MODULE_FEATURE_CHECKPOINT_RELATION_TABLE
from flask import request, jsonify
import logging


logger = logging.getLogger("Logger")

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class ModuleFeaturecheckpointContentData(BaseModel):
    id: Optional[str] = None
    module_name: Optional[str] = Field(None, alias="moduleName")
    featurecheckpoint_name: Optional[str] = Field(None, alias="featurecheckpointName")
    featurecheckpoint_content: Optional[str] = Field(None, alias="featurecheckpointContent")
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    operator_person: Optional[str] = None

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
            return None
        return str(value)
    
class ModuleFeaturecheckpointRelationData(BaseModel):
    id: Optional[str] = None
    module_name: Optional[str] = Field(None, alias="moduleName")
    feature_name: Optional[str] = Field(None, alias="featureName")
    checkpoint_name: Optional[str] = Field(None, alias="checkpointName")
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    operator_person: Optional[str] = None

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
            return None
        return str(value)

# 特性&检测点-内容取值
def queryModuleFeaturecheckpointContentDataByParams():    # 构建基础查询
    """
    查询指定的特性&检测点-内容取值
    ---
    tags:
      - 业务模块-特性&检测点
    description: 查询指定的特性&检测点-内容取值
    parameters:
      - name: featurecheckpointName
        in: query
        description: 特性&检测点名称
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [{
          "featurecheckpoint_name":"",
      "featurecheckpoint_content": "",
      "create_time": "Mon, 07 Jul 2025 17:21:42 GMT",
      "update_time": "Thu, 10 Jul 2025 22:12:08 GMT",
      "operator_person": "张进朋10305454"
    }]}
    """
    conditions = []
    query_params = request.args.to_dict()
    featurecheckpoint_name = query_params.get("featurecheckpointName", "").replace('-特性分析', '')
    featurecheckpoint_name_list = []
    conditions.append(MODULE_FEATURECHECKPOINT_CONTENT_TABLE.featurecheckpoint_name.like(f"%{featurecheckpoint_name}%"))
    baseModuleFeaturecheckpointContentDatas = db.session.query(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).filter(and_(*conditions)).all()
    if len(baseModuleFeaturecheckpointContentDatas) < 1:
        baseModuleFeaturecheckpointRelationDatas = db.session.query(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE).filter(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.feature_name.like(f"%{featurecheckpoint_name}%")).all()
        results = [
            ModuleFeaturecheckpointRelationData.model_validate(item).model_dump(by_alias=True)
            for item in baseModuleFeaturecheckpointRelationDatas
        ]
        for result in results:
            featurecheckpoint_name_list.append(result["checkpointName"])
        new_conditions = []
        new_conditions.append(MODULE_FEATURECHECKPOINT_CONTENT_TABLE.featurecheckpoint_name.in_(featurecheckpoint_name_list))
        baseModuleFeaturecheckpointContentDatas = db.session.query(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).filter(and_(*new_conditions)).all()
        
    try:
        results = [
            ModuleFeaturecheckpointContentData.model_validate(item).model_dump(by_alias=True)
            for item in baseModuleFeaturecheckpointContentDatas
        ]
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "failed", "message": "获取失败", "data": []})
    
def importExcelModuleFeaturecheckpointContentData():
    """
    Excel文件上传接口
    ---
    tags:
      - 业务模块-特性&检测点
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
        # contents = await file.read()

        # # # 将内容封装为 BytesIO 对象，支持 seek 操作
        # excel_file = BytesIO(contents)
        # 读取 Excel 文件（无需保存到本地）
        excel_file = pd.ExcelFile(file)
        sheet_names = excel_file.sheet_names
        
        # 排除名为"修订记录"的sheet页
        filtered_sheet_names = [name for name in sheet_names if name not in ["修订记录", "特性与检测点的对应关系表"]]
        
        # 创建结果字典
        result_dict = {}
        
        # 遍历剩余的sheet页
        for sheet_name in filtered_sheet_names:
            # 读取sheet页内容
            df = pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
            df = df.fillna(value='')
            
            # 将DataFrame转换为markdown表格字符串
            markdown_table = df.to_markdown(index=False)
            result_dict[sheet_name] = markdown_table

        for sheet_name, sheet_content in result_dict.items():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['module_name'] = '电层单板性能告警'
            table_dict['featurecheckpoint_name'] = sheet_name
            table_dict['featurecheckpoint_content'] = sheet_content
            db_factor_values = db.session.query(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).filter(and_(MODULE_FEATURECHECKPOINT_CONTENT_TABLE.featurecheckpoint_name == table_dict['featurecheckpoint_name'])).all()
            if len(db_factor_values) > 0:
                update_sql = update(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).where(and_(MODULE_FEATURECHECKPOINT_CONTENT_TABLE.module_name == table_dict['module_name'],
                                                                                   MODULE_FEATURECHECKPOINT_CONTENT_TABLE.featurecheckpoint_name == table_dict['featurecheckpoint_name'])
                                                                       ).values(featurecheckpoint_content=table_dict["featurecheckpoint_content"], 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
                
            else:
                
                insert_sql = insert(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).values(module_name=table_dict['module_name'], featurecheckpoint_name=table_dict['featurecheckpoint_name'], 
                                                                               featurecheckpoint_content=table_dict["featurecheckpoint_content"], create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(MODULE_FEATURECHECKPOINT_CONTENT_TABLE).first())
        sheet_name = "特性与检测点的对应关系表"
        if sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
            df = df.fillna(value='')
            
            # 逐行解析数据并插入到MODULE_FEATURE_CHECKPOINT_RELATION_TABLE表中
            for index, row in df.iterrows():
                feature_name = row.get('特性名称', '')  # 获取特性名称列的值
                checkpoint_names = row.get('支持性能告警', '')  # 获取检测点列的值
                checkpoint_name_list = checkpoint_names.split(',')
                for src_checkpoint_name in checkpoint_name_list:
                    # 检查数据是否有效
                    checkpoint_name = src_checkpoint_name.strip()
                    if feature_name and checkpoint_name:
                        # 检查是否已存在相同的记录
                        existing_record = db.session.query(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE).filter(
                            and_(
                                MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.feature_name == feature_name,
                                MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.checkpoint_name == checkpoint_name,
                                MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.module_name == '电层单板性能告警'
                            )
                        ).first()
                        
                        if existing_record:
                            # 如果记录存在，则更新
                            update_sql = update(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE).where(
                                and_(
                                    MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.feature_name == feature_name,
                                    MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.checkpoint_name == checkpoint_name,
                                    MODULE_FEATURE_CHECKPOINT_RELATION_TABLE.module_name == '电层单板性能告警'
                                )
                            ).values(
                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                operator_person=new_operator_person
                            )
                            db.session.execute(update_sql)
                        else:
                            # 如果记录不存在，则插入新记录
                            insert_sql = insert(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE).values(
                                module_name='电层单板性能告警',
                                feature_name=feature_name,
                                checkpoint_name=checkpoint_name,
                                create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                operator_person=new_operator_person
                            )
                            db.session.execute(insert_sql)
            
            # 提交事务
            db.session.commit()
            db.session.refresh(db.session.query(MODULE_FEATURE_CHECKPOINT_RELATION_TABLE).first())
                
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")
  