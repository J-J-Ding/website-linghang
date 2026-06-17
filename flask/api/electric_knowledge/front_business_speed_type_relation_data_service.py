from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import re
import pandas as pd
from electric_knowledge.utils_pub import pub_get_employ_name

from electric_knowledge.data_model import db,  BUSINESS_MODEL_RATE_TABLE
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BaseBusinessSpeedTypeData(BaseModel):
    id: Optional[str] = None
    network_element_business_model_rate: Optional[str] = Field(None, alias="businessSpeed")
    business_type_list: Optional[str] = Field(None, alias="businessType")
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

# 定义响应参数模型
class BaseBusinessSpeedTypeOutputData(BaseModel):
    code: int = Field(description='响应码', default=0)
    message: str = Field(description='提示信息', default='获取成功')
    status: str = Field(description='提示信息', default='Success')
    data: List[Optional[BaseBusinessSpeedTypeData]]

def contains_all(list1, list2):
    return set(list2).issubset(list1)

# 业务模型-光口业务速率&业务类型
def queryBusinessSpeedTypeTree():    # 构建基础查询
    """
    查询全部光口业务速率&业务类型取值记录（树形结构）
    ---
    tags:
      - 光口业务速率&业务类型
    description: 查询全部光口业务速率&业务类型取值记录（树形结构）
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
    query = db.session.query(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate, BUSINESS_MODEL_RATE_TABLE.business_type_list, BUSINESS_MODEL_RATE_TABLE.id).filter(BUSINESS_MODEL_RATE_TABLE.effective_flag=='Y').group_by(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate, BUSINESS_MODEL_RATE_TABLE.business_type_list, BUSINESS_MODEL_RATE_TABLE.id).order_by(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate, BUSINESS_MODEL_RATE_TABLE.id)
    # 动态添加过滤条件
    
    # 执行查询
    baseBusinessSpeedTypeTreeDatas = query.all()
    result = []
    item = dict()
    
    for baseBusinessSpeedTypeTreeData in baseBusinessSpeedTypeTreeDatas:
        children_item = dict()
        if baseBusinessSpeedTypeTreeData[0] not in list(item.values()):
            if item:
                result.append(copy.deepcopy(item))
            item['label'] = baseBusinessSpeedTypeTreeData[0]
            item['value'] = baseBusinessSpeedTypeTreeData[0]
            item['children'] = []
        children_item['label'] = baseBusinessSpeedTypeTreeData[1]
        children_item['value'] = baseBusinessSpeedTypeTreeData[2]
        item['children'].append(children_item)

    result.append(item)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def querySrcBusinessSpeedTypeByParams(query_params:dict={}, markdown_flag:bool=False):    # 构建基础查询
    conditions = [BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    baseBusinessSpeedTypeData = BaseBusinessSpeedTypeData(**query_params)
    if baseBusinessSpeedTypeData.network_element_business_model_rate:
        conditions.append(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate.in_(baseBusinessSpeedTypeData.network_element_business_model_rate.split(',')))
    if baseBusinessSpeedTypeData.business_type_list:
        conditions.append(BUSINESS_MODEL_RATE_TABLE.business_type_list == baseBusinessSpeedTypeData.business_type_list)
    if baseBusinessSpeedTypeData.current_status:
        conditions.append(BUSINESS_MODEL_RATE_TABLE.current_status.in_(baseBusinessSpeedTypeData.current_status.split(',')))
    if baseBusinessSpeedTypeData.operator_person:
        conditions.append(BUSINESS_MODEL_RATE_TABLE.operator_person == baseBusinessSpeedTypeData.operator_person)
    try:
        baseBusinessSpeedTypeDatas = db.session.query(BUSINESS_MODEL_RATE_TABLE).filter(and_(*conditions)).all() 
        results = [
            BaseBusinessSpeedTypeData.model_validate(item).model_dump(by_alias=True)
            for item in baseBusinessSpeedTypeDatas
        ]
        # 对光口业务速率按数值进行排序
        def extract_speed_value(speed_str):
            """
            从光口业务速率字符串中提取数值
            支持格式: "100G", "10G", "2.5G及以下", "200G" 等
            提取G前面的数值部分
            """
            if not speed_str:
                return 0
            speed_str = str(speed_str)
            # 找到第一个'G'的位置
            g_index = speed_str.find('G')
            if g_index == -1:
                return 0  # 如果没有G，返回0
                
            # 提取G前面的部分
            before_g = speed_str[:g_index].strip()
            
            # 使用正则表达式提取数字部分（包括小数）
            match = re.search(r'(\d+\.?\d*)', before_g)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return 0
            return 0
        
        # 按提取的数值对结果进行排序
        results.sort(key=lambda x: extract_speed_value(x.get('businessSpeed', '')))
        
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        print(f"查询错误: {e}")  # 添加错误日志
        return ([], 400)


def queryBusinessSpeedTypeByParams():    # 构建基础查询
    """
    查询指定的光口业务速率&业务类型取值记录
    ---
    tags:
      - 光口业务速率&业务类型
    description: 查询指定的光口业务速率&业务类型取值记录
    parameters:
      - name: network_element_business_model_rate
        in: query
        description: 光口业务速率
        required: false
        type: string
      - name: business_type_list
        in: query
        description: 业务类型
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
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [{
                "id": 1,
                "businessSpeed": "2.5G及以下",
                "businessType": "E1,T1,FE,GE,STM1,STM4,STM16,OTU0,OTU1",
                "status": "正常",
                "create_time": "2025-07-07T20:59:47",
                "update_time": "2025-07-11T18:56:24",
                "operator_person": "张进朋10305454",
                "effective_flag": "Y",
            }]}
    """
    query_params = request.args.to_dict()
    results, code = querySrcBusinessSpeedTypeByParams(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})
    

def queryBusinessSpeedTypeStatusList():    # 构建基础查询
    """
    查询光口业务速率&业务类型状态列表
    ---
    tags:
      - 光口业务速率&业务类型
    description: 查询光口业务速率&业务类型状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_RATE_TABLE.current_status).filter(and_(*conditions)).group_by(BUSINESS_MODEL_RATE_TABLE.current_status)
    # 动态添加过滤条件
    # 执行查询
    basebaseBusinessSpeedTypeDatas = query.all()
    result = []
    for basebaseBusinessSpeedTypeData in basebaseBusinessSpeedTypeDatas:
        result.append(basebaseBusinessSpeedTypeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryBusinessSpeedTypeBusinessSpeedList():    # 构建基础查询
    """
    查询光口业务速率列表
    ---
    tags:
      - 光口业务速率&业务类型
    description: 查询光口业务速率列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate).filter(and_(*conditions)).group_by(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate)
    # 动态添加过滤条件
    # 执行查询
    basebaseBusinessSpeedTypeDatas = query.all()
    result = []
    for basebaseBusinessSpeedTypeData in basebaseBusinessSpeedTypeDatas:
        result.append(basebaseBusinessSpeedTypeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryBusinessSpeedTypeBusinessTypeList():    # 构建基础查询
    """
    查询光口业务速率对应的业务类型列表
    ---
    tags:
      - 光口业务速率&业务类型
    description: 查询光口业务速率对应的业务类型列表
    parameters:
      - name: network_element_business_model_rate
        in: query
        description: 光口业务速率
        required: true
        type: string
        example: "10G"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseBusinessSpeedTypeData = BaseBusinessSpeedTypeData(**query_params)
    if baseBusinessSpeedTypeData.network_element_business_model_rate:
        conditions.append(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == baseBusinessSpeedTypeData.network_element_business_model_rate)
    # 构建查询
    query = db.session.query(BUSINESS_MODEL_RATE_TABLE.business_type_list).filter(and_(*conditions)).group_by(BUSINESS_MODEL_RATE_TABLE.business_type_list)
    # 动态添加过滤条件
    # 执行查询
    basebaseBusinessSpeedTypeDatas = query.all()
    result = []
    for basebaseBusinessSpeedTypeData in basebaseBusinessSpeedTypeDatas:
        result.extend(basebaseBusinessSpeedTypeData[0].split(","))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def syncUpdateCoreelementFactorRelation(update_type:str, new_operator_person:str):
    from electric_knowledge.front_business_coreelement_factor_relation_data_service import updateSrcSourceCoreElementFactorRelationData
    if update_type in ["业务速率", "all"]:
        params_dict = {"elementType": "业务", "element": "业务要素", "factorType": "客户侧光层业务因子,线路侧光层业务因子"}
        updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)
    if update_type in ["业务类型", "all"]:
        params_dict = {"elementType": "单板", "element": "单板业务要素", "factorType": "客户侧电层业务因子,线路侧电层业务因子"}
        updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)

def addBusinessSpeedTypeData():
    """
    新增指定的光口业务速率&业务类型取值
    ---
    tags:
      - 光口业务速率&业务类型
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
            network_element_business_model_rate:
              type: string
              description: 光口业务速率
            business_type_list:
              type: string
              description: 业务类型
          example:   # 示例值
            network_element_business_model_rate: "10G"
            business_type_list: "STM64,10GE,OTU2,OTU2E"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    baseBusinessSpeedTypeData = BaseBusinessSpeedTypeData(**body_params)
    network_element_business_model_rate = baseBusinessSpeedTypeData.network_element_business_model_rate
    business_type_list = baseBusinessSpeedTypeData.business_type_list

    # 检查新增的数据在数据表中是否已存在
    db_business_model_rate_values = db.session.query(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate, BUSINESS_MODEL_RATE_TABLE.business_type_list).filter(and_(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == network_element_business_model_rate
                                                                       )).all()
    tmp_add_business_type_list = business_type_list.split(',')
    db_business_type_list = []
    for db_business_model_rate_value in db_business_model_rate_values:
        db_business_type_list.extend(db_business_model_rate_value[1].split(','))
    
    if contains_all(db_business_type_list, tmp_add_business_type_list):
        return {"code": 201, "status": "success", "message": "新增的光口业务速率-业务类型取值已存在!", "data": []}
    elif len(db_business_type_list) > 0:
        db_business_type_list.extend(tmp_add_business_type_list)
        new_db_business_type_values = ','.join(str(x) for x in set(db_business_type_list))
        update_sql = update(BUSINESS_MODEL_RATE_TABLE).where(and_(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == network_element_business_model_rate
                                                                       )).values(business_type_list=new_db_business_type_values,  current_status=check_update,   update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        db.session.execute(update_sql)
        db.session.commit()
        db.session.refresh(db.session.query(BUSINESS_MODEL_RATE_TABLE).first())
        syncUpdateCoreelementFactorRelation("业务类型", new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增的光口业务速率已存在，新增的业务类型取值会和已存在的业务类型取值合并，本次为修改操作!", "data": []})
    else:
        insert_sql = insert(BUSINESS_MODEL_RATE_TABLE).values(network_element_business_model_rate=network_element_business_model_rate, business_type_list=business_type_list, 
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)

        # 创建新用户
        db.session.commit()
        db.session.refresh(db.session.query(BUSINESS_MODEL_RATE_TABLE).first())
        syncUpdateCoreelementFactorRelation("all", new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})

def updateBusinessSpeedTypeData():
    """
    更新指定的光口业务速率&业务类型取值
    ---
    tags:
      - 光口业务速率&业务类型
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
            network_element_business_model_rate:
              type: string
              description: 光口业务速率
            business_type_list:
              type: string
              description: 业务类型
          example:   # 示例值
            id: "2"
            network_element_business_model_rate: "10G"
            business_type_list: "STM64,10GE,OTU2,OTU2E"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    baseBusinessSpeedTypeData = BaseBusinessSpeedTypeData(**body_params)
    # 提取参数
    id = baseBusinessSpeedTypeData.id
    network_element_business_model_rate = baseBusinessSpeedTypeData.network_element_business_model_rate
    business_type_list = baseBusinessSpeedTypeData.business_type_list
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    update_sql = update(BUSINESS_MODEL_RATE_TABLE).where(and_(BUSINESS_MODEL_RATE_TABLE.id == int(id), BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y')
                                                                       ).values(network_element_business_model_rate=network_element_business_model_rate, business_type_list=business_type_list, 
                                                                                 current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)  
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BUSINESS_MODEL_RATE_TABLE).first())
    syncUpdateCoreelementFactorRelation("all", new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def deleteBusinessSpeedTypeData():
    """
    删除指定的光口业务速率&业务类型取值
    ---
    tags:
      - 光口业务速率&业务类型
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
    baseBusinessSpeedTypeData = BaseBusinessSpeedTypeData(**body_params)
    # 提取参数
    id = baseBusinessSpeedTypeData.id
    
    # 检查新增的数据在数据表中是否已存在
    # delete_sql = update(BUSINESS_MODEL_RATE_TABLE).where(BUSINESS_MODEL_RATE_TABLE.id.in_([int(id) for id in id.split(',')])).values(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),operator_person=new_operator_person,effective_flag='N')
    # db.session.execute(delete_sql) 
    delete_count = db.session.query(BUSINESS_MODEL_RATE_TABLE).where(BUSINESS_MODEL_RATE_TABLE.id.in_([int(id) for id in id.split(',')])).delete()
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BUSINESS_MODEL_RATE_TABLE).first())
    syncUpdateCoreelementFactorRelation("all", new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def importExcelbaseBusinessSpeedTypeData():
    """
    Excel文件上传接口
    ---
    tags:
      - 光口业务速率&业务类型
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
        df['光口业务速率'] = df['光口业务速率'].astype(str) 
        
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['network_element_business_model_rate'] = row["光口业务速率"] if "光口业务速率" in row else '' 
            table_dict['business_type_list'] = ','.join(single_business_type.strip() for single_business_type in row["业务类型"].split('、'))
            db_factor_values = db.session.query(BUSINESS_MODEL_RATE_TABLE).filter(and_(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == row["光口业务速率"]
                                                                       )).all()
            if len(db_factor_values) > 0 and row["光口业务速率"] and row["业务类型"]:
                update_sql = update(BUSINESS_MODEL_RATE_TABLE).where(and_(BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == table_dict['network_element_business_model_rate'])
                                                                       ).values(business_type_list=table_dict['business_type_list'], current_status=check_update,
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
            else:
                insert_sql = insert(BUSINESS_MODEL_RATE_TABLE).values(network_element_business_model_rate=table_dict['network_element_business_model_rate'], business_type_list=table_dict['business_type_list'], 
                                                              current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BUSINESS_MODEL_RATE_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
    

