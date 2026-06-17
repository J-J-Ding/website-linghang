from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from electric_knowledge.utils_pub import pub_get_employ_name

from electric_knowledge.data_model import db,  BOARD_VALID_MODEL_TABLE
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BoardValidModelData(BaseModel):
    id: Optional[str] = None
    board_model_classification: Optional[str] = Field(None, alias="boardBusinessType")
    board_model: Optional[str] = Field(None, alias="boardBusiness")
    board_model_description: Optional[str] = Field(None, alias="boardBusinessDescribe")
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
            return None
        return str(value)

class BoardValidModelData(BaseModel):
    id: Optional[str] = None
    board_model_classification: Optional[str] = Field(None, alias="boardBusinessType")
    valid_combination_board_model: Optional[str] = Field(None, alias="boardBusiness")
    valid_combination_board_model_description: Optional[str] = Field(None, alias="boardBusinessDescribe")
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
            return None
        return str(value)


def contains_all(list1, list2):
    return set(list2).issubset(list1)


# 业务模型-单板分类&单板模型
def queryBoardBusinessGroupTree():    # 构建基础查询
    """
    查询全部单板有效模型取值记录（树形结构）
    ---
    tags:
      - 单板有效模型
    description: 查询全部单板有效模型取值记录（树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
            {
                "label": "客户侧C卡",
                "value": "客户侧C卡",
                "children": [
                    {
                        "label": "C_O/C_FG",
                        "value": 1
                    },
                    {
                        "label": "C_OSU/C_FG",
                        "value": 2
                    }
                ]
            },
            {
                "label": "客户侧E卡",
                "value": "客户侧E卡",
                "children": [
                    {
                        "label": "E_EoO/E_EoFG",
                        "value": 3
                    },
                    {
                        "label": "E_EoS/E_EoFG/E_EoO",
                        "value": 4
                    }
                ]
            },
        ]}
    """
    query = db.session.query(BOARD_VALID_MODEL_TABLE.board_model_classification, BOARD_VALID_MODEL_TABLE.valid_combination_board_model, BOARD_VALID_MODEL_TABLE.id).filter(BOARD_VALID_MODEL_TABLE.effective_flag=='Y').group_by(BOARD_VALID_MODEL_TABLE.board_model_classification, BOARD_VALID_MODEL_TABLE.valid_combination_board_model, BOARD_VALID_MODEL_TABLE.id).order_by(BOARD_VALID_MODEL_TABLE.board_model_classification, BOARD_VALID_MODEL_TABLE.id)
    # 动态添加过滤条件
    
    # 执行查询
    baseBoardValidModelDatas = query.all()
    result = []
    item = dict()
    
    for baseBoardValidModelData in baseBoardValidModelDatas:
        children_item = dict()
        if baseBoardValidModelData[0] not in list(item.values()):
            if item:
                result.append(copy.deepcopy(item))
            item['label'] = baseBoardValidModelData[0]
            item['value'] = baseBoardValidModelData[0]
            item['children'] = []
        children_item['label'] = baseBoardValidModelData[1]
        children_item['value'] = baseBoardValidModelData[2]
        item['children'].append(children_item)

    result.append(item)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def queryBoardBusinessGroupByParams():    # 构建基础查询
    """
    查询指定的单板有效模型取值记录
    ---
    tags:
      - 单板有效模型
    description: 查询指定的单板有效模型取值记录
    parameters:
      - name: board_model_classification
        in: query
        description: 单板分类
        required: false
        type: string
      - name: valid_combination_board_model
        in: query
        description: 单板有效模型
        required: false
        type: string
      - name: current_status
        in: query
        description: 当前状态
        required: false
        type: string
      - name: operator_person
        in: query
        description: 操作人
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
            "code": 200,
            "message": "获取成功",
            "status": "success",
            "data": [
                {
                "id": 1,
                "boardBusinessType": "客户侧C卡",
                "boardBusiness": "C_O/C_FG",
                "boardBusinessDescribe": "客户侧C卡C_O/C_FG的单板业务模型描述",
                "status": "正常",
                "create_time": "2025-07-07T20:59:47",
                "update_time": "2025-07-11T18:56:24",
                "operator_person": "张进朋10305454",
                "effective_flag": "Y",
            }
            ]
      }
    """
    conditions = [BOARD_VALID_MODEL_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseBoardValidModelData = BoardValidModelData(**query_params)
    if baseBoardValidModelData.board_model_classification:
        conditions.append(BOARD_VALID_MODEL_TABLE.board_model_classification.in_(baseBoardValidModelData.board_model_classification.split(',')))
    if baseBoardValidModelData.valid_combination_board_model:
        conditions.append(or_(BOARD_VALID_MODEL_TABLE.valid_combination_board_model.in_(baseBoardValidModelData.valid_combination_board_model.split(',')), BOARD_VALID_MODEL_TABLE.id.in_([id for id in baseBoardValidModelData.valid_combination_board_model.split(',')]))) # id为整数，整数In字符串数字列表中   
    if baseBoardValidModelData.current_status:
        conditions.append(BOARD_VALID_MODEL_TABLE.current_status.in_(baseBoardValidModelData.current_status.split(',')))
    if baseBoardValidModelData.operator_person:
        conditions.append(BOARD_VALID_MODEL_TABLE.operator_person == baseBoardValidModelData.operator_person)

    try:
        baseBoardValidModelDatas = db.session.query(BOARD_VALID_MODEL_TABLE) \
        .filter(and_(*conditions)).order_by(BOARD_VALID_MODEL_TABLE.board_model_classification, BOARD_VALID_MODEL_TABLE.valid_combination_board_model).all() 
        results = [
            BoardValidModelData.model_validate(item).model_dump(by_alias=True)
            for item in baseBoardValidModelDatas
        ]

        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": {}})


def querySrcBoardBusinessGroupBoardBusinessTypeList():    # 构建基础查询
    conditions = [BOARD_VALID_MODEL_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BOARD_VALID_MODEL_TABLE.board_model_classification).filter(and_(*conditions)).group_by(BOARD_VALID_MODEL_TABLE.board_model_classification)
    # 动态添加过滤条件
    # 执行查询
    baseBoardValidModelDatas = query.all()
    result = []
    for baseBoardValidModelData in baseBoardValidModelDatas:
        result.append(baseBoardValidModelData[0])

    return list(set(result))

def queryBoardBusinessGroupBoardBusinessTypeList():    # 构建基础查询
    """
    查询单板模型分类列表
    ---
    tags:
      - 单板有效模型
    description: 查询单板模型分类列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    results = querySrcBoardBusinessGroupBoardBusinessTypeList()

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})


def queryBoardBusinessGroupBoardBusinessList():    # 构建基础查询
    """
    查询单板有效模型列表
    ---
    tags:
      - 单板有效模型
    description: 查询单板有效模型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BOARD_VALID_MODEL_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BOARD_VALID_MODEL_TABLE.valid_combination_board_model).filter(and_(*conditions)).group_by(BOARD_VALID_MODEL_TABLE.valid_combination_board_model)
    # 动态添加过滤条件
    # 执行查询
    baseBoardValidModelDatas = query.all()
    result = []
    for baseBoardValidModelData in baseBoardValidModelDatas:
        result.append(baseBoardValidModelData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryBoardBusinessGroupStatusList():    # 构建基础查询
    """
    查询单板有效模型全部状态列表
    ---
    tags:
      - 单板有效模型
    description: 查询单板有效模型全部状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BOARD_VALID_MODEL_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BOARD_VALID_MODEL_TABLE.current_status).filter(and_(*conditions)).group_by(BOARD_VALID_MODEL_TABLE.current_status)
    # 动态添加过滤条件
    # 执行查询
    baseBoardValidModelDatas = query.all()
    result = []
    for baseBoardValidModelData in baseBoardValidModelDatas:
        result.append(baseBoardValidModelData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def syncUpdateCoreelementFactorRelation(update_type:str, new_operator_person:str):
    from electric_knowledge.front_business_coreelement_factor_relation_data_service import updateSrcSourceCoreElementFactorRelationData
    if update_type in ["单板模型", "all"]:
        params_dict = {"elementType": "单板", "element": "单板业务要素", "factorType": "单板业务模型因子"}
        updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)
    if update_type in ["单板分类", "all"]:
        params_dict = {"elementType": "单板", "element": "单板产品形态要素", "factorType": "板卡类型因子"}
        updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)

def addBoardBusinessGroupData():
    """
    新增指定的单板有效模型取值
    ---
    tags:
      - 单板有效模型
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            board_model_classification:
              type: string
              description: 单板分类
            valid_combination_board_model:
              type: string
              description: 单板有效模型
            valid_combination_board_model_description:
              type: string
              description: 单板有效模型描述
          example:   # 示例值
            board_model_classification: "客户侧C卡"
            valid_combination_board_model: "C_V/C_O"
            valid_combination_board_model_description: ""
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    baseBoardValidModelData = BoardValidModelData(**body_params)
    board_model_classification = baseBoardValidModelData.board_model_classification
    valid_combination_board_model = baseBoardValidModelData.valid_combination_board_model
    valid_combination_board_model_list = valid_combination_board_model.split('|')
    valid_combination_board_model_num = len(valid_combination_board_model_list)
    valid_combination_board_model_description = baseBoardValidModelData.valid_combination_board_model_description
    conditions = [func.find_in_set(sub, func.replace(BOARD_VALID_MODEL_TABLE.valid_combination_board_model, '|', ',')) > 0 for sub in valid_combination_board_model_list]
    conditions.extend([BOARD_VALID_MODEL_TABLE.board_model_classification == board_model_classification, 
                       (func.length(BOARD_VALID_MODEL_TABLE.valid_combination_board_model) - func.length(func.replace(BOARD_VALID_MODEL_TABLE.valid_combination_board_model, '|', '')) + 1) == valid_combination_board_model_num])

    # 检查新增的数据在数据表中是否已存在
    db_valid_board_model_values = db.session.query(BOARD_VALID_MODEL_TABLE.board_model_classification, BOARD_VALID_MODEL_TABLE.valid_combination_board_model).filter(and_(*conditions)).all()
    tmp_add_valid_board_model_list = valid_combination_board_model.split('|')
    db_valid_board_model_list = []
    for db_valid_board_model_value in db_valid_board_model_values:
        db_valid_board_model_list.extend(db_valid_board_model_value[1].split('|'))
    if contains_all(db_valid_board_model_list, tmp_add_valid_board_model_list):
        return {"code": 201, "status": "success", "message": "新增的单板模型分类-单板有效模型取值已存在!", "data": []}
    elif len(db_valid_board_model_list) > 0:
        db_valid_board_model_list.extend(tmp_add_valid_board_model_list)
        new_db_valid_board_model_values = '|'.join(str(x) for x in set(db_valid_board_model_list))
        update_sql = update(BOARD_VALID_MODEL_TABLE).where(and_(BOARD_VALID_MODEL_TABLE.board_model_classification == board_model_classification
                                                                       )).values(valid_combination_board_model=new_db_valid_board_model_values,  valid_combination_board_model_description=valid_combination_board_model_description,
                                                                                 current_status=check_update,   update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        db.session.execute(update_sql)
        db.session.commit()
        db.session.refresh(db.session.query(BOARD_VALID_MODEL_TABLE).first())
        syncUpdateCoreelementFactorRelation('单板模型', new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增的单板模型分类已存在，新增的单板有效模型取值会和已存在的单板有效模型取值合并，本次为修改操作!", "data": []})
    else:
        insert_sql = insert(BOARD_VALID_MODEL_TABLE).values(board_model_classification=board_model_classification, valid_combination_board_model=valid_combination_board_model, 
                                                      valid_combination_board_model_description=valid_combination_board_model_description, current_status=check_add, 
                                                      create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)

        # 创建新用户
        db.session.commit()
        db.session.refresh(db.session.query(BOARD_VALID_MODEL_TABLE).first())
        syncUpdateCoreelementFactorRelation('all', new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})

def updateBoardBusinessGroupData():
    """
    更新指定的单板有效模型取值
    ---
    tags:
      - 单板有效模型
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [id]
          properties:
            id:
              type: string
              description: 每一行数据的id唯一标识
            board_model_classification:
              type: string
              description: 单板分类
            valid_combination_board_model:
              type: string
              description: 单板有效模型
            valid_combination_board_model_description:
              type: string
              description: 单板有效模型描述
          example:   # 示例值
            id: "2"
            board_model_classification: "客户侧C卡"
            valid_combination_board_model: "C_O/C_FG"
            valid_combination_board_model_description: ""
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    baseBoardValidModelData = BoardValidModelData(**body_params)
    # 提取参数
    id = baseBoardValidModelData.id
    board_model_classification = baseBoardValidModelData.board_model_classification
    valid_combination_board_model = baseBoardValidModelData.valid_combination_board_model
    valid_combination_board_model_description = baseBoardValidModelData.valid_combination_board_model_description
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    update_sql = update(BOARD_VALID_MODEL_TABLE).where(and_(BOARD_VALID_MODEL_TABLE.id == int(id), BOARD_VALID_MODEL_TABLE.effective_flag == 'Y')
                                                                       ).values(board_model_classification=board_model_classification,  valid_combination_board_model = valid_combination_board_model,
                                  valid_combination_board_model_description=valid_combination_board_model_description, current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)  
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BOARD_VALID_MODEL_TABLE).first())
    syncUpdateCoreelementFactorRelation('all', new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def deleteBoardBusinessGroupData():
    """
    删除指定的单板有效模型取值
    ---
    tags:
      - 单板有效模型
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          properties:
            id:
              type: string
              description: 每一行数据的id唯一标识
          example:   # 示例值
            id: "2"
    responses:
      200:
        description: 成功删除数据
    """
    # employ_no = bytes.fromhex(src_employ_no).decode("utf-8")
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json(force=True)
    baseBoardValidModelData = BoardValidModelData(**body_params)
    # 提取参数
    id = baseBoardValidModelData.id
    
    # 检查新增的数据在数据表中是否已存在
    # delete_sql = update(BOARD_VALID_MODEL_TABLE).where(BOARD_VALID_MODEL_TABLE.id.in_([int(id) for id in id.split(',')])).values(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),operator_person=new_operator_person,effective_flag='N')
    # db.session.execute(delete_sql) 
    delete_count = db.session.query(BOARD_VALID_MODEL_TABLE).where(BOARD_VALID_MODEL_TABLE.id.in_([int(id) for id in id.split(',')])).delete()
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BOARD_VALID_MODEL_TABLE).first())
    syncUpdateCoreelementFactorRelation('all', new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def importExcelBoardGroupModelData():
    """
    Excel文件上传接口
    ---
    tags:
      - 单板有效模型
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
        df.iloc[:, 1] = df.iloc[:, 1].ffill()
        df = df.fillna(value='')
        df['单板分类'] = df['单板分类'].astype(str) 
        
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['board_model_classification'] = row["单板分类"] if "单板分类" in row else '' 
            table_dict['valid_combination_board_model'] = '|'.join(single_business_type.strip() for single_business_type in row["单板模型"].split('、'))
            table_dict['valid_combination_board_model_description'] = row["单板模型组合描述"] if "单板模型组合描述" in row else ''

            valid_combination_board_model_list = table_dict['valid_combination_board_model'].split('|')
            conditions = [func.find_in_set(sub, func.replace(BOARD_VALID_MODEL_TABLE.valid_combination_board_model, '|', ',')) > 0 for sub in valid_combination_board_model_list]
            conditions.extend([BOARD_VALID_MODEL_TABLE.board_model_classification == table_dict['board_model_classification'], 
                       (func.length(BOARD_VALID_MODEL_TABLE.valid_combination_board_model) - func.length(func.replace(BOARD_VALID_MODEL_TABLE.valid_combination_board_model, '|', '')) + 1) == len(valid_combination_board_model_list)])
            db_board_model_values = db.session.query(BOARD_VALID_MODEL_TABLE).filter(and_(*conditions)).all()
            if len(db_board_model_values) > 0 and row["单板分类"] and row["单板模型"]:
                update_sql = update(BOARD_VALID_MODEL_TABLE).where(and_(*conditions)).values(
                                                                                valid_combination_board_model_description=table_dict['valid_combination_board_model_description'], 
                                                                                current_status=check_update,
                                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                                operator_person=new_operator_person)
                db.session.execute(update_sql) 
            else:
                insert_sql = insert(BOARD_VALID_MODEL_TABLE).values(board_model_classification=table_dict['board_model_classification'], 
                                                              valid_combination_board_model=table_dict['valid_combination_board_model'], 
                                                              valid_combination_board_model_description=table_dict['valid_combination_board_model_description'], 
                                                              current_status=check_add,
                                                              create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             operator_person=new_operator_person, 
                                                             effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BOARD_VALID_MODEL_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
    

