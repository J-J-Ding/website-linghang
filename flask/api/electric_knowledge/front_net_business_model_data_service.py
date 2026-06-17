from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd

from electric_knowledge.data_model import db,  BUSINESS_MODEL_TABLE, BUSINESS_MODEL_RATE_TABLE, BOARD_MODEL_TABLE
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BaseNetBusinessData(BaseModel):
    id: Optional[str] = None
    network_element_business_solution: Optional[str] = Field(None, alias="netBusinessScheme")
    network_element_business_model: Optional[str] = Field(None, alias="netBusinessModel")
    input_business_type_list: Optional[str] = Field(None, alias="inputBusinessType")
    crossconnect_type: Optional[str] = Field(None, alias="crossType")
    output_business_type_list: Optional[str] = Field(None, alias="outputBusinessType")
    input_board_model_list: Optional[str] = Field(None, alias="inputBoardBusinessModel")
    output_board_model_list: Optional[str] = Field(None, alias="outputBoardBusinessModel")
    typical_board_examples: Optional[str] = Field(None, alias="typicalBoardCase")
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


# 业务模型-网元业务模型
def queryNetBusinessTree():    # 构建基础查询
    """
    查询全部网元业务模型取值记录（树形结构）
    ---
    tags:
      - 网元业务模型
    description: 查询全部网元业务模型取值记录（树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
      {
                "label": "2.5G及以下",
                "value": "2.5G及以下",
                "children": [
                    {
                        "label": "E1",
                        "value": 1
                    },
                    {
                        "label": "T1",
                        "value": 2
                    }
                ]
            },
            {
                "label": "10G",
                "value": "10G",
                "children": [
                    {
                        "label": "10GE",
                        "value": 3
                    },
                    {
                        "label": "STM64",
                        "value": 4
                    }
                ]
            }
    ]}
    """
    query = db.session.query(BUSINESS_MODEL_TABLE.network_element_business_solution, BUSINESS_MODEL_TABLE.network_element_business_model, BUSINESS_MODEL_TABLE.id).filter(BUSINESS_MODEL_TABLE.effective_flag=='Y').group_by(BUSINESS_MODEL_TABLE.network_element_business_solution, BUSINESS_MODEL_TABLE.network_element_business_model, BUSINESS_MODEL_TABLE.id).order_by(BUSINESS_MODEL_TABLE.network_element_business_solution, BUSINESS_MODEL_TABLE.id)
    # 动态添加过滤条件
    
    # 执行查询
    baseNetBusinessTreeDatas = query.all()
    result = []
    item = dict()
    
    for baseNetBusinessTreeData in baseNetBusinessTreeDatas:
        children_item = dict()
        if baseNetBusinessTreeData[0] not in list(item.values()):
            if item:
                result.append(copy.deepcopy(item))
            item['label'] = baseNetBusinessTreeData[0]
            item['value'] = baseNetBusinessTreeData[0]
            item['children'] = []
        children_item['label'] = baseNetBusinessTreeData[1]
        children_item['value'] = baseNetBusinessTreeData[2]
        item['children'].append(children_item)

    result.append(item)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def querySrcNetBusinessByParams(query_params:dict={}, markdown_flag:bool=False):    # 构建基础查询
    conditions = [BUSINESS_MODEL_TABLE.effective_flag == 'Y']
    baseNetBusinessData = BaseNetBusinessData(**query_params)
    if baseNetBusinessData.network_element_business_solution:
        conditions.append(BUSINESS_MODEL_TABLE.network_element_business_solution.in_(baseNetBusinessData.network_element_business_solution.split(',')))
    if baseNetBusinessData.network_element_business_model:
        conditions.append(or_(BUSINESS_MODEL_TABLE.network_element_business_model.in_(baseNetBusinessData.network_element_business_model.split(',')), BUSINESS_MODEL_TABLE.id.in_([id for id in baseNetBusinessData.network_element_business_model.split(',')]))) # id为整数，整数In字符串数字列表中
    if baseNetBusinessData.current_status:
        conditions.append(BUSINESS_MODEL_TABLE.current_status.in_(baseNetBusinessData.current_status.split(',')))
    if baseNetBusinessData.operator_person:
        conditions.append(BUSINESS_MODEL_TABLE.operator_person == baseNetBusinessData.operator_person)
    try:
        query = db.session.query(BUSINESS_MODEL_TABLE) \
        .filter(and_(*conditions)).order_by(case(
        (or_(
            BUSINESS_MODEL_TABLE.input_business_type_list.is_(None),
            BUSINESS_MODEL_TABLE.input_business_type_list == ''
        ), 1),
        else_=0                        
    ).asc(),
    BUSINESS_MODEL_TABLE.network_element_business_solution, 
    BUSINESS_MODEL_TABLE.input_business_type_list.asc())
        BaseNetBusinessDatas = query.all()
        results = [
            BaseNetBusinessData.model_validate(item).model_dump(by_alias=True)
            for item in BaseNetBusinessDatas
        ]
        if markdown_flag:
            # columns = [col['name'] for col in query.column_descriptions]
            return results

        return (results, 200)
    except Exception as e:
        return ([], 400)
    
def queryNetBusinessByParams():    # 构建基础查询
    """
    查询指定的网元业务模型取值记录
    ---
    tags:
      - 网元业务模型
    description: 查询指定的网元业务模型取值记录
    parameters:
      - name: netBusinessScheme
        in: query
        description: 网元业务分类
        required: false
        type: string
      - name: netBusinessModel
        in: query
        description: 网元业务模型
        required: false
        type: string
      - name: status
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
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
            {
                "id": 1,
                "netBusinessScheme": "EoS业务方案",
                "netBusinessModel": "EoS-V-OTN",
                "inputBusinessType": "10GE,STM64",
                "crossType": "V",
                "outputBusinessType": "OTU2,OTU2E",
                "inputBoardBusinessModel": "E_EoS",
                "outputBoardBusinessModel": "L_V",
                "typicalBoardCase": "EoS业务方案典型单板实例",
                "status": "正常",
                "create_time": "2025-07-07T20:59:47",
                "update_time": "2025-07-11T18:56:24",
                "operator_person": "张进朋10305454",
                "effective_flag": "Y",
            }
        ]}
    """
    query_params = request.args.to_dict()
    results, code = querySrcNetBusinessByParams(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})
    

def queryNetBusinessStatusList():    # 构建基础查询
    """
    查询网元业务模型状态列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务模型状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_TABLE.current_status).filter(and_(*conditions)).group_by(BUSINESS_MODEL_TABLE.current_status)
    # 动态添加过滤条件
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.append(baseBaseNetBusinessData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryNetBusinessNetBusinessSchemeList():    # 构建基础查询
    """
    查询网元业务分类列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务分类列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_TABLE.network_element_business_solution).filter(and_(*conditions)).group_by(BUSINESS_MODEL_TABLE.network_element_business_solution)
    # 动态添加过滤条件
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.append(baseBaseNetBusinessData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryNetBusinessNetBusinessModelList():    # 构建基础查询
    """
    查询网元业务分类对应的网元业务模型列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务分类对应的网元业务模型列表
    parameters:
      - name: netBusinessScheme
        in: query
        description: 网元业务分类
        required: false
        type: string
        example: "10G"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseNetBusinessData = BaseNetBusinessData(**query_params)
    if baseNetBusinessData.network_element_business_solution:
        conditions.append(BUSINESS_MODEL_TABLE.network_element_business_solution == baseNetBusinessData.network_element_business_solution)
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_TABLE.network_element_business_model).filter(and_(*conditions)).group_by(BUSINESS_MODEL_TABLE.network_element_business_model)
    # 动态添加过滤条件
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.append(baseBaseNetBusinessData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryNetBusinessBusinessTypeList():    # 构建基础查询
    """
    查询网元业务分类中的入口&出口业务类型列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务分类中的入口&出口业务类型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    query = db.session.query(BUSINESS_MODEL_RATE_TABLE.business_type_list).filter(and_(*conditions)).group_by(BUSINESS_MODEL_RATE_TABLE.business_type_list)
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.extend(baseBaseNetBusinessData[0].split(","))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryNetBusinessBoardBusinessModelList():    # 构建基础查询
    """
    查询网元业务分类中的入口&出口单板业务模型列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务分类中的入口&出口单板业务模型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BOARD_MODEL_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    # 构建查询
    query = db.session.query(BOARD_MODEL_TABLE.board_model).filter(and_(*conditions)).group_by(BOARD_MODEL_TABLE.board_model)
    # 动态添加过滤条件
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.extend(baseBaseNetBusinessData[0].split(","))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryNetBusinessCrossTypeList():    # 构建基础查询
    """
    查询网元业务分类中的交叉类型列表
    ---
    tags:
      - 网元业务模型
    description: 查询网元业务分类中的交叉类型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_TABLE.effective_flag == 'Y', BUSINESS_MODEL_TABLE.crossconnect_type != '']
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_TABLE.crossconnect_type).filter(and_(*conditions)).group_by(BUSINESS_MODEL_TABLE.crossconnect_type)
    # 动态添加过滤条件
    # 执行查询
    baseBaseNetBusinessDatas = query.all()
    result = []
    for baseBaseNetBusinessData in baseBaseNetBusinessDatas:
        result.extend(baseBaseNetBusinessData[0].split(","))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def syncUpdateCoreelementFactorRelation(new_operator_person:str):
    from electric_knowledge.front_business_coreelement_factor_relation_data_service import updateSrcSourceCoreElementFactorRelationData
    params_dict = {"elementType": "业务", "element": "业务要素", "factorType": "网元业务模型因子"}
    updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)


def addNetBusinessData():
    """
    新增指定的网元业务模型取值
    ---
    tags:
      - 网元业务模型
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
          required: [netBusinessScheme, netBusinessModel]
          properties:
            netBusinessScheme:
              type: string
              description: 网元业务分类
            netBusinessModel:
              type: string
              description: 网元业务模型
            inputBusinessType:
              type: string
              description: 入口业务类型
            crossType:
              type: string
              description: 交叉类型
            outputBusinessType:
              type: string
              description: 出口业务类型
            inputBoardBusinessModel:
              type: string
              description: 入口单板原子模型
            outputBoardBusinessModel:
              type: string
              description: 出口单板原子模型
            typicalBoardCase:
              type: string
              description: 典型单板实例
          example:   # 示例值
            netBusinessScheme: "EoS业务方案"
            netBusinessModel: "EoS-V-OTN"
            inputBusinessType: "FE,GE,10GE"
            crossType: "VC"
            outputBusinessType: "OTU0,OTU1,OTU2"
            inputBoardBusinessModel: "E_EoS"
            outputBoardBusinessModel: "L_V"
            typicalBoardCase: "SGEP-V-H2P"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    baseNetBusinessData = BaseNetBusinessData(**body_params)
    network_element_business_solution = baseNetBusinessData.network_element_business_solution
    network_element_business_model = baseNetBusinessData.network_element_business_model
    input_business_type_list = baseNetBusinessData.input_business_type_list
    crossconnect_type = baseNetBusinessData.crossconnect_type
    output_business_type_list = baseNetBusinessData.output_business_type_list
    input_board_model_list = baseNetBusinessData.input_board_model_list
    output_board_model_list = baseNetBusinessData.output_board_model_list
    typical_board_examples = baseNetBusinessData.typical_board_examples

    # 检查新增的数据在数据表中是否已存在
    db_business_model_values = db.session.query(BUSINESS_MODEL_TABLE.network_element_business_solution, BUSINESS_MODEL_TABLE.network_element_business_model).filter(and_(BUSINESS_MODEL_TABLE.network_element_business_solution == network_element_business_solution,
                                                                       BUSINESS_MODEL_TABLE.network_element_business_model == network_element_business_model)).all()

    if len(db_business_model_values) > 0:
        return {"code": 201, "status": "success", "message": "新增的网元业务分类-业务模型取值已存在!", "data": []}
    else:
        insert_sql = insert(BUSINESS_MODEL_TABLE).values(network_element_business_solution=network_element_business_solution, network_element_business_model=network_element_business_model, 
                                                         input_business_type_list=input_business_type_list, crossconnect_type=crossconnect_type, output_business_type_list=output_business_type_list, 
                                                         input_board_model_list=input_board_model_list, output_board_model_list=output_board_model_list, typical_board_examples=typical_board_examples,
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)

        # 创建新用户
        db.session.commit()
        db.session.refresh(db.session.query(BUSINESS_MODEL_TABLE).first())
        syncUpdateCoreelementFactorRelation(new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})

def updateNetBusinessData():
    """
    更新指定的网元业务模型取值
    ---
    tags:
      - 网元业务模型
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
            netBusinessScheme:
              type: string
              description: 网元业务分类
            netBusinessModel:
              type: string
              description: 网元业务模型
            inputBusinessType:
              type: string
              description: 入口业务类型
            crossType:
              type: string
              description: 交叉类型
            outputBusinessType:
              type: string
              description: 出口业务类型
            inputBoardBusinessModel:
              type: string
              description: 入口单板原子模型
            outputBoardBusinessModel:
              type: string
              description: 出口单板原子模型
            typicalBoardCase:
              type: string
              description: 典型单板实例
          example:   # 示例值
            id: "2"
            netBusinessScheme: "EoS业务方案"
            netBusinessModel: "EoS-V-OTN"
            inputBusinessType: "FE,GE,10GE"
            crossType: "VC"
            outputBusinessType: "OTU0,OTU1,OTU2"
            inputBoardBusinessModel: "E_EoS"
            outputBoardBusinessModel: "L_V"
            typicalBoardCase: "SGEP-V-H2P"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    baseNetBusinessData = BaseNetBusinessData(**body_params)
    # 提取参数
    id = baseNetBusinessData.id
    network_element_business_solution = baseNetBusinessData.network_element_business_solution
    network_element_business_model = baseNetBusinessData.network_element_business_model
    input_business_type_list = baseNetBusinessData.input_business_type_list
    crossconnect_type = baseNetBusinessData.crossconnect_type
    output_business_type_list = baseNetBusinessData.output_business_type_list
    input_board_model_list = baseNetBusinessData.input_board_model_list
    output_board_model_list = baseNetBusinessData.output_board_model_list
    typical_board_examples = baseNetBusinessData.typical_board_examples

    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    update_sql = update(BUSINESS_MODEL_TABLE).where(and_(BUSINESS_MODEL_TABLE.id == int(id), BUSINESS_MODEL_TABLE.effective_flag == 'Y')
                                                                       ).values(network_element_business_solution=network_element_business_solution, network_element_business_model=network_element_business_model, 
                                                                                input_business_type_list=input_business_type_list, crossconnect_type=crossconnect_type, output_business_type_list=output_business_type_list,
                                                                                input_board_model_list=input_board_model_list, output_board_model_list=output_board_model_list, typical_board_examples=typical_board_examples,
                                                                                 current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)  
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BUSINESS_MODEL_TABLE).first())
    syncUpdateCoreelementFactorRelation(new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def deleteNetBusinessData():
    """
    删除指定的网元业务模型取值
    ---
    tags:
      - 网元业务模型
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
          example:   # 示例值
            id: "2"
    responses:
      200:
        description: 成功删除数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json(force=True)
    baseNetBusinessData = BaseNetBusinessData(**body_params)
    # 提取参数
    id = baseNetBusinessData.id
    delete_count = db.session.query(BUSINESS_MODEL_TABLE).where(BUSINESS_MODEL_TABLE.id.in_([int(id) for id in id.split(',')])).delete()
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BUSINESS_MODEL_TABLE).first())
    syncUpdateCoreelementFactorRelation(new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def importExcelbaseNetBusinessData():
    """
    Excel文件上传接口
    ---
    tags:
      - 网元业务模型
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
        df['网元业务分类'] = df['网元业务分类'].astype(str) 
        
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['network_element_business_solution'] = row["网元业务分类"] if "网元业务分类" in row else '' 
            table_dict['network_element_business_model'] = ','.join(single_business_type.strip() for single_business_type in row["网元业务模型"].split('、'))
            table_dict['input_business_type_list'] = ','.join(item.strip() for item in row["入口业务类型"].replace('，', ',').split(','))
            table_dict['crossconnect_type'] = row["交叉类型"] 
            table_dict['output_business_type_list'] = ','.join(item.strip() for item in row["出口业务类型"].replace('，', ',').split(','))
            table_dict['input_board_model_list'] = ','.join(item.strip() for item in row["入口单板原子模型"].replace('，', ',').split(','))
            table_dict['output_board_model_list'] = ','.join(item.strip() for item in row["出口单板原子模型"].replace('，', ',').split(','))
            table_dict['typical_board_examples'] = row["典型单板实例"] 
            db_factor_values = db.session.query(BUSINESS_MODEL_TABLE).filter(and_(BUSINESS_MODEL_TABLE.network_element_business_solution == row["网元业务分类"],
                                                                                  BUSINESS_MODEL_TABLE.network_element_business_model == table_dict['network_element_business_model']
                                                                       )).all()
            if len(db_factor_values) > 0 and row["网元业务分类"] and row["网元业务模型"]:
                update_sql = update(BUSINESS_MODEL_TABLE).where(and_(BUSINESS_MODEL_TABLE.network_element_business_solution == table_dict['network_element_business_solution'],
                                                                     BUSINESS_MODEL_TABLE.network_element_business_model == table_dict['network_element_business_model'])
                                                                       ).values(input_business_type_list=table_dict['input_business_type_list'], 
                                                                                crossconnect_type=table_dict['crossconnect_type'], output_business_type_list=table_dict['output_business_type_list'], 
                                                                                input_board_model_list=table_dict['input_board_model_list'], output_board_model_list=table_dict['output_board_model_list'], 
                                                                                typical_board_examples=table_dict['typical_board_examples'],
                                                                                current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
            else:
                insert_sql = insert(BUSINESS_MODEL_TABLE).values(network_element_business_solution=table_dict['network_element_business_solution'], network_element_business_model=table_dict['network_element_business_model'], 
                                                                 input_business_type_list=table_dict['input_business_type_list'], crossconnect_type=table_dict['crossconnect_type'], 
                                                                 output_business_type_list=table_dict['output_business_type_list'],  input_board_model_list=table_dict['input_board_model_list'], output_board_model_list=table_dict['output_board_model_list'], 
                                                                                typical_board_examples=table_dict['typical_board_examples'],
                                                              current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BUSINESS_MODEL_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}    
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
    

