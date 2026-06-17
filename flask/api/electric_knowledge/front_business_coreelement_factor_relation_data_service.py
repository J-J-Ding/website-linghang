from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from electric_knowledge.utils_pub import pub_get_employ_name
from io import BytesIO

from electric_knowledge.data_model import db, CORE_ELEMENT_FACTOR_RELATION_TABLE, FACTOR_VALUE_SRC_CONFIG_TABLE, FEATURE_RELATION_TABLE, BUSINESS_MODEL_RATE_TABLE, BUSINESS_MODEL_TABLE, BOARD_COMPONENTS_TREE_TABLE, SUBRACK_TREE_TABLE, BOARD_VALID_MODEL_TABLE
from electric_knowledge.front_board_components_tree_data_service import querySrcBoardPartTreeSchemeSliceList
from electric_knowledge.front_subrack_components_tree_data_service import querySrcShelfPartTreeSchemeSliceList
from flask import request, jsonify
import logging


logger = logging.getLogger("Logger")

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class CoreElementFactorRelationData(BaseModel):
    id: Optional[str] = None
    core_element_type: Optional[str] = Field(None, alias="elementType")
    core_element: Optional[str] = Field(None, alias="element")
    factor: Optional[str] = Field(None, alias="factorType")
    factor_details_link: Optional[str] = None
    factor_value_src: Optional[str] = Field(None, alias="factorValueSrc")
    factor_value: Optional[str] = Field(None, alias="factorValue")
    factor_ext_value: Optional[str] = Field(None, alias="factorExtValue")
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

class NewBaseCoreElementFactorRelationData(BaseModel):
    id: Optional[str] = None
    core_element_type: Optional[str] = Field(None, alias="elementType")
    core_element: Optional[str] = Field(None, alias="element")
    factor: Optional[str] = Field(None, alias="factorType")
    factor_details_link: Optional[str] = None
    factor_value_src: Optional[str] = Field(None, alias="factorValueSrc")
    factor_value: Optional[str] = Field(None, alias="factorValue")
    factor_ext_value: Optional[str] = Field(None, alias="factorExtValue")
    current_status: Optional[str] = Field(None, alias="status")
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    operator_person: Optional[str] = None
    effective_flag: Optional[str] = None
    factor_value_src_description: Optional[str] = Field(..., alias="factorValueSrcDescription")

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
    # model_config = ConfigDict(from_attributes=True)

# 定义响应参数模型
class CoreElementFactorRelationOutputData(BaseModel):
    code: int = Field(description='响应码', default=0)
    message: str = Field(description='提示信息', default='获取成功')
    status: str = Field(description='提示信息', default='Success')
    data: List[Optional[NewBaseCoreElementFactorRelationData]]


def contains_all(list1, list2):
    return set(list2).issubset(list1)

def remove_duplicates_by_key(dict_list, key='id'):
    seen = set()
    result = []
    for d in dict_list:
        value = d.get(key)
        if value not in seen:
            seen.add(value)
            result.append(d)
    return result

# 业务方案要素因子
def querySrcCoreElementFactorRelationByParams(query_params:dict):    # 构建基础查询
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    custom_order = case(
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '拓扑要素', 1),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '业务要素', 2),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '高可用要素', 3),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '扩展应用要素', 4),
                else_=5
            )
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
        if coreElementFactorRelationData.core_element_type.strip() == '单板':
            custom_order = case(
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '单板业务要素', 1),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '单板产品形态要素', 2),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '单板器件要素', 3),
                else_=4
            )
         
        elif coreElementFactorRelationData.core_element_type.strip() == '子架':
            custom_order = case(
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '子架关键属性要素', 1),
                (CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == '子架核心部件要素', 2),
                else_=3
            )
    if coreElementFactorRelationData.core_element:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(',')))
    if coreElementFactorRelationData.factor:
        conditions.append(or_(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor.in_(coreElementFactorRelationData.factor.split(',')), CORE_ELEMENT_FACTOR_RELATION_TABLE.id.in_([id for id in coreElementFactorRelationData.factor.split(',')]))) # id为整数，整数In字符串数字列表中
    if coreElementFactorRelationData.factor_details_link:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_details_link == coreElementFactorRelationData.factor_details_link)
    if coreElementFactorRelationData.factor_value_src:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src == coreElementFactorRelationData.factor_value_src)
    if coreElementFactorRelationData.factor_value:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value.like(f"%{coreElementFactorRelationData.factor_value}%")) 
    if coreElementFactorRelationData.current_status:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.current_status.in_(coreElementFactorRelationData.current_status.split(',')))
    try:
        baseCoreElementFactorRelationDatas = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE) \
        .join(FACTOR_VALUE_SRC_CONFIG_TABLE, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src == FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src, isouter=True) \
        .filter(and_(*conditions)).order_by(custom_order, CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor).all() 
        results = [
            NewBaseCoreElementFactorRelationData.model_validate(item).model_dump(by_alias=True)
            for item in baseCoreElementFactorRelationDatas
        ]

        return  results
    except Exception as e:
        return  []

# 业务方案要素因子
def queryCoreElementFactorRelationByParams():    # 构建基础查询
    """
    查询指定的要素-因子-因子取值
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询指定的要素-因子-因子取值
    parameters:
      - name: elementType
        in: query
        description: 要素类型
        required: false
        type: string
      - name: element
        in: query
        description: 要素
        required: false
        type: string
      - name: factorType
        in: query
        description: 因子类型
        required: false
        type: string
      - name: factorValue
        in: query
        description: 因子取值
        required: false
        type: string
      - name: factor_details_link
        in: query
        description: 因子详情链接
        required: false
        type: string
      - name: factorValueSrc
        in: query
        description: 因子取值来源
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
      "element": "扩展应用要素",
      "elementType": "业务方案",
      "create_time": "Mon, 07 Jul 2025 17:21:42 GMT",
      "status": "正常",
      "effective_flag": "Y",
      "factorType": "加密因子",
      "factor_details_link": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aad8970a419c11f0be9b9f19a4254cf4/view",
      "factorValue": "F010220-灰光业务维护管理特性,F010221-灰光业务性能告警特性,F010131-彩光业务光标签应用特性,F010102-灰光业务基础特性,F020101-O业务基础特性,F020103-O业务开销配置管理特性,F010133-彩光业务APO功率查询应用特性",
      "factorValueSrc": "feature_relation_table,feature_name",
      "factorValueSrcDescription": "0301-特性子特性及关联关系：特性",
      "id": 2,
      "operator_person": "张进朋10305454",
      "update_time": "Thu, 10 Jul 2025 22:12:08 GMT"
    }]}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    results = querySrcCoreElementFactorRelationByParams(query_params)
    if results:
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    else:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": []})


def querySrcCoreElementFactorValueDict(query_params:dict):
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    if coreElementFactorRelationData.core_element:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(',')))
    if coreElementFactorRelationData.factor:
        conditions.append(or_(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor.in_(coreElementFactorRelationData.factor.split(',')), CORE_ELEMENT_FACTOR_RELATION_TABLE.id.in_([id for id in coreElementFactorRelationData.factor.split(',')]))) # id为整数，整数In字符串数字列表中
    if coreElementFactorRelationData.factor_details_link:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_details_link == coreElementFactorRelationData.factor_details_link)
    if coreElementFactorRelationData.factor_value_src:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src == coreElementFactorRelationData.factor_value_src)
    if coreElementFactorRelationData.factor_value:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value.like(f"%{coreElementFactorRelationData.factor_value}%")) 
    if coreElementFactorRelationData.current_status:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.current_status.in_(coreElementFactorRelationData.current_status.split(',')))
    final_results = {}
    try:
        baseCoreElementFactorRelationDatas = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type, CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_ext_value) \
        .filter(and_(*conditions)).order_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type, CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value).all() 
        results = [
            CoreElementFactorRelationData.model_validate(item).model_dump(by_alias=True)
            for item in baseCoreElementFactorRelationDatas
        ]
        for result in results:
            factor_values = result['factorValue'].strip()
            factorType = result['factorType'][:-2]
            if factorType in ['单板支持的子架', '业务FRM芯片', '控制逻辑', '开销逻辑', '主控因子', '交叉因子', '背板因子']:
                factor_values = result['factorExtValue'].strip()
            if factor_values:
                final_results[factorType] = factor_values.split(',')
            else:
                final_results[factorType] = []
        return (final_results, 200)
    except Exception as e:
        return (final_results, 400)
    

# 业务方案要素因子
def queryCoreElementFactorValueDict():    # 构建基础查询
    """
    查询指定的要素-因子的取值范围列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询指定的要素-因子的取值范围列表
    parameters:
      - name: elementType
        in: query
        description: 要素类型
        required: false
        type: string
      - name: element
        in: query
        description: 要素
        required: false
        type: string
      - name: factorType
        in: query
        description: 因子类型
        required: false
        type: string
      - name: factorValue
        in: query
        description: 因子取值
        required: false
        type: string
      - name: factor_details_link
        in: query
        description: 因子详情链接
        required: false
        type: string
      - name: factorValueSrc
        in: query
        description: 因子取值来源
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
      "element": "扩展应用要素",
      "elementType": "业务方案",
      "create_time": "Mon, 07 Jul 2025 17:21:42 GMT",
      "status": "正常",
      "effective_flag": "Y",
      "factorType": "加密因子",
      "factor_details_link": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aad8970a419c11f0be9b9f19a4254cf4/view",
      "factorValue": "F010220-灰光业务维护管理特性,F010221-灰光业务性能告警特性,F010131-彩光业务光标签应用特性,F010102-灰光业务基础特性,F020101-O业务基础特性,F020103-O业务开销配置管理特性,F010133-彩光业务APO功率查询应用特性",
      "factorValueSrc": "feature_relation_table,feature_name",
      "factorValueSrcDescription": "0301-特性子特性及关联关系：特性",
      "id": 2,
      "operator_person": "张进朋10305454",
      "update_time": "Thu, 10 Jul 2025 22:12:08 GMT"
    }]}
    """
    query_params = request.args.to_dict()
    final_results, code = querySrcCoreElementFactorValueDict(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": final_results})
    
def queryCoreElementFactorRelationTree():    # 构建基础查询
    """
    查询全部要素-因子-因子取值记录（树形结构）
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询全部要素-因子-因子取值记录（树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
      {
        "children": [
          {
            "label": "网元业务模型因子",
            "value": 3
          },
          {
            "label": "线路侧光层业务因子",
            "value": 4
          }
        ],
        "label": "业务要素",
        "value": "业务要素"
      },
      {
        "children": [
          {
            "label": "加密因子",
            "value": 2
          },
          {
            "label": "LLCF故障双向透传因子",
            "value": 15
          }
        ],
        "label": "扩展应用要素",
        "value": "扩展应用要素"
      },
      {
        "children": [
          {
            "label": "拓扑因子",
            "value": 12
          }
        ],
        "label": "拓扑要素",
        "value": "拓扑要素"
      },
      {
        "children": [
          {
            "label": "O恢复因子",
            "value": 6
          },
          {
            "label": "FG保护因子",
            "value": 7
          }
        
        ],
        "label": "高可用要素",
        "value": "高可用要素"
      }
    ]}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    query = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor, CORE_ELEMENT_FACTOR_RELATION_TABLE.id).filter(and_(*conditions)).group_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor, CORE_ELEMENT_FACTOR_RELATION_TABLE.id).order_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element, CORE_ELEMENT_FACTOR_RELATION_TABLE.id)
    # 动态添加过滤条件
    # 执行查询
    baseCoreElementFactorRelationTreeDatas = query.all()
    result = []
    item = dict()
    
    for baseCoreElementFactorRelationTreeData in baseCoreElementFactorRelationTreeDatas:
        children_item = dict()
        if baseCoreElementFactorRelationTreeData[0] not in list(item.values()):
            if item:
                result.append(copy.deepcopy(item))
            item['label'] = baseCoreElementFactorRelationTreeData[0]
            item['value'] = baseCoreElementFactorRelationTreeData[0]
            item['children'] = []
        children_item['label'] = baseCoreElementFactorRelationTreeData[1]
        children_item['value'] = baseCoreElementFactorRelationTreeData[2]
        item['children'].append(children_item)

    result.append(item)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def queryCoreElementFactorRelationStatusList():    # 构建基础查询
    """
    查询要素-因子-因子取值记录的全部状态列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询要素-因子-因子取值记录的全部状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    query = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.current_status).filter(and_(*conditions)).group_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.current_status)
    # 执行查询
    baseCoreElementFactorRelationStatusDatas = query.all()
    result = []
    for baseCoreElementFactorRelationStatusData in baseCoreElementFactorRelationStatusDatas:
        result.append(baseCoreElementFactorRelationStatusData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryCoreElementFactorRelationCoreElementList():    # 构建基础查询
    """
    查询要素列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询要素列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    query = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element).filter(and_(*conditions)).group_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element)
    # 执行查询
    baseCoreElementFactorRelationCoreElementDatas = query.all()
    result = []
    for baseCoreElementFactorRelationCoreElementData in baseCoreElementFactorRelationCoreElementDatas:
        result.append(baseCoreElementFactorRelationCoreElementData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def queryCoreElementFactorRelationFactorList():    # 构建基础查询
    """
    查询因子列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询因子列表
    parameters:
      - name: element
        in: query
        description: 要素
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    # coreElementFactorRelationData = CoreElementFactorRelationData(**request.json)
    # core_element = request.args.get('core_element')
    query_params = request.args.to_dict()
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    if coreElementFactorRelationData.core_element:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(','))
        )

    # 构建查询
    query = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor).filter(and_(*conditions)).group_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor)
    # 动态添加过滤条件
    # 执行查询
    baseCoreElementFactorRelationFactorDatas = query.all()
    result = []
    for baseCoreElementFactorRelationFactorData in baseCoreElementFactorRelationFactorDatas:
        result.append(baseCoreElementFactorRelationFactorData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryCoreElementFactorRelationFactorValueSrcList():    # 构建基础查询
    """
    查询因子取值来源列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询因子取值来源列表
    parameters:
      - name: element
        in: query
        description: 要素
        required: true
        type: string
      - name: factorType
        in: query
        description: 因子类型
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    if coreElementFactorRelationData.core_element:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(','))
        )
    if coreElementFactorRelationData.factor:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.factor.in_(coreElementFactorRelationData.factor.split(','))
        )
    baseCoreElementFactorRelationFactorValueSrcDatas = db.session.query(FACTOR_VALUE_SRC_CONFIG_TABLE, CORE_ELEMENT_FACTOR_RELATION_TABLE).join(CORE_ELEMENT_FACTOR_RELATION_TABLE).filter(and_(*conditions)).with_entities(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src_description).all()
    if len(baseCoreElementFactorRelationFactorValueSrcDatas) < 1:
        baseCoreElementFactorRelationFactorValueSrcDatas = db.session.query(FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src_description).filter(FACTOR_VALUE_SRC_CONFIG_TABLE.effective_flag=='Y').group_by(FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src_description).all()
    # 动态添加过滤条件
    # 执行查询
    result = []
    for baseCoreElementFactorRelationFactorValueSrcData in baseCoreElementFactorRelationFactorValueSrcDatas:
        result.append({"factorValueSrc":baseCoreElementFactorRelationFactorValueSrcData[0], "factorValueSrcDescription":baseCoreElementFactorRelationFactorValueSrcData[1]})

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": remove_duplicates_by_key(result, "factorValueSrc")})

def querySrcCoreElementFactorRelationFactorValueList(query_params:dict, key_flag:bool=False):    # 构建基础查询
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    coreElementFactorRelationData = CoreElementFactorRelationData(**query_params)
    # 仅当 core_element 存在时，添加该条件
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    if coreElementFactorRelationData.core_element:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(','))
        )
    if coreElementFactorRelationData.factor:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.factor.in_(coreElementFactorRelationData.factor.split(','))
        )
    if coreElementFactorRelationData.factor_value_src:
        conditions.append(
            CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src==coreElementFactorRelationData.factor_value_src
        )
    # 构建查询
    db_factor_value_srcs = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value).filter(and_(*conditions)).group_by(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src, CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value).all()
    if len(db_factor_value_srcs) < 1:
        db_factor_value_srcs = db.session.query(FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src_description).filter(and_(FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src==coreElementFactorRelationData.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.effective_flag=='Y')).group_by(FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src, FACTOR_VALUE_SRC_CONFIG_TABLE.factor_value_src_description).all()
    result = []
    if len(db_factor_value_srcs) < 1:
        return result
    # 动态添加过滤条件
    # 执行查询
    
    for db_factor_value_src in db_factor_value_srcs:
        if not db_factor_value_src[0]:
            continue
        factor_value_src = db_factor_value_src[0].split(',')
        
        effective_flag = "effective_flag"
        if factor_value_src[0].upper() == 'MANUAL_INPUT':
            result.extend((db_factor_value_src[1] if db_factor_value_src[1] else '').split(','))
            continue
        # 获取字段属性
        table_class = globals()[factor_value_src[0].upper()]
        
        column1 = factor_value_src[1]
        column_field = getattr(table_class, column1)
        effective_field = getattr(table_class, effective_flag)

        # 构造查询
        if not key_flag:
            db_factor_real_value_srcs = db.session.query(column_field).filter(effective_field == 'Y').group_by(column_field).all()
        elif column1.lower() == "subrack_name":
            column_field1 = getattr(table_class, "factor_type_cn")
            column_field2 = getattr(table_class, "factor_value")
            concat_expr = func.concat(
                func.coalesce(column_field2, ''), '->',
                func.coalesce(column_field, '')
            )
            db_factor_real_value_srcs = db.session.query(concat_expr.label('combined_value')).filter(and_(effective_field == 'Y', column_field1 == '所属产品')).group_by(concat_expr).all()
            
        for db_factor_real_value_src in db_factor_real_value_srcs:
            if coreElementFactorRelationData.factor == "客户侧光层业务因子":
                if db_factor_real_value_src[0].strip() not in ['800G', '1200G', '1600G']:
                    tmp = db_factor_real_value_src[0].strip().split('G')
                    if len(tmp) > 1:
                        result.append(tmp[0] + "G" + tmp[1] + "灰光")
                    else:
                        result.append(tmp[0] + "G灰光")
            elif coreElementFactorRelationData.factor == "线路侧光层业务因子":
                if db_factor_real_value_src[0].strip() not in ['1200G', '1600G']:
                    tmp = db_factor_real_value_src[0].strip().split('G')
                    if len(tmp) > 1:
                        result.append(tmp[0] + "G" + tmp[1] + "彩光")
                    else:
                        result.append(tmp[0] + "G彩光")
            else:
                result.append(db_factor_real_value_src[0].strip())

    return list(set(result))

def queryCoreElementFactorRelationFactorValueList():    # 构建基础查询
    """
    查询因子取值列表
    ---
    tags:
      - 业务方案要素-因子-因子取值
    description: 查询因子取值列表
    parameters:
      - name: element
        in: query
        description: 要素
        required: false
        type: string
      - name: factorType
        in: query
        description: 因子类型
        required: false
        type: string
      - name: factorValueSrc
        in: query
        description: 因子取值来源
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    query_params = request.args.to_dict()
    result = querySrcCoreElementFactorRelationFactorValueList(query_params)
    if len(result) < 1:
        return jsonify({"code": 201, "status": "success", "message": "要素+因子类型对应的因子取值来源为空或手动输入 且单独传入的因子取值来源未被配置", "data": result})
    # 动态添加过滤条件
    # 执行查询
    
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def addCoreElementFactorRelationData():
    """
    新增指定的要素-因子-因子取值
    ---
    tags:
      - 业务方案要素-因子-因子取值
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
            elementType:
              type: string
              description: 要素类型
            element:
              type: string
              description: 要素
            factorType:
              type: string
              description: 因子
            factorValue:
              type: string
              description: 因子取值
            factor_details_link:
              type: string
              description: 因子详情链接
            factorValueSrc:
              type: string
              description: 因子取值来源
          example:   # 示例值
            elementType: "业务方案"
            element: "扩展应用要素"
            factorType: "中断时间测量"
            factorValue: "O业务中断时间测量"
            factor_details_link: "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aad8970a419c11f0be9b9f19a4254cf4/view"
            factorValueSrc: "feature_relation_table,feature_name"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    employ_token = request.headers.get('X-Auth-Value')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    coreElementFactorRelationData = CoreElementFactorRelationData(**body_params)
    # 提取参数
    core_element_type = coreElementFactorRelationData.core_element_type
    core_element = coreElementFactorRelationData.core_element
    factor = coreElementFactorRelationData.factor
    factor_value = coreElementFactorRelationData.factor_value
    factor_details_link = coreElementFactorRelationData.factor_details_link
    factor_value_src = coreElementFactorRelationData.factor_value_src
    # 检查新增的数据在数据表中是否已存在
    db_factor_values = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value).filter(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == core_element_type,
                                                                                                                                                      CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == core_element,
                                                                                                                                                    CORE_ELEMENT_FACTOR_RELATION_TABLE.factor == factor
                                                                                                                                                    )).all()
    tmp_add_factor_value_list = factor_value.split(',')
    db_factor_value_list = []
    for db_factor_value in db_factor_values:
        db_factor_value_list.extend(db_factor_value[0].split(','))
    
    if contains_all(db_factor_value_list, tmp_add_factor_value_list):
        return {"code": 201, "status": "success", "message": "新增的要素-因子-因子取值已存在!", "data": []}
    elif len(db_factor_value_list) > 0:
        old_db_factor_value_list = copy.deepcopy(db_factor_value_list)
        db_factor_value_list.extend(tmp_add_factor_value_list)
        new_db_factor_values = ','.join(str(x) for x in set(db_factor_value_list))
        update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == core_element_type, CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == core_element,
                                                                       CORE_ELEMENT_FACTOR_RELATION_TABLE.factor == factor)).values(core_element_type=core_element_type, factor_details_link=factor_details_link, 
                                                                                                                                                                   factor_value_src=factor_value_src, factor_value=new_db_factor_values, current_status=check_update,
                                                                                                                                                                  update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        db.session.execute(update_sql)
        db.session.commit()
        db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})
    else:
        insert_sql = insert(CORE_ELEMENT_FACTOR_RELATION_TABLE).values(core_element_type=core_element_type, core_element=core_element, factor=factor, 
                                                                       factor_details_link=factor_details_link, factor_value_src=factor_value_src,
                                                             factor_value=factor_value, current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)

        # 创建新用户
        db.session.commit()
        db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})


def updateSrcSourceCoreElementFactorRelationData(body_params:dict, new_operator_person:str):
    conditions = [CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y']
    coreElementFactorRelationData = CoreElementFactorRelationData(**body_params)
    if coreElementFactorRelationData.core_element_type:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationData.core_element_type)
    if coreElementFactorRelationData.core_element:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element.in_(coreElementFactorRelationData.core_element.split(',')))
    if coreElementFactorRelationData.factor:
        conditions.append(or_(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor.in_(coreElementFactorRelationData.factor.split(',')), CORE_ELEMENT_FACTOR_RELATION_TABLE.id.in_([id for id in coreElementFactorRelationData.factor.split(',')]))) # id为整数，整数In字符串数字列表中
    
    if coreElementFactorRelationData.factor_value_src:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value_src == coreElementFactorRelationData.factor_value_src)
    if coreElementFactorRelationData.factor_value:
        conditions.append(CORE_ELEMENT_FACTOR_RELATION_TABLE.factor_value.like(f"%{coreElementFactorRelationData.factor_value}%")) 
    # 提取参数   
    board_part_datas = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).filter(and_(*conditions)).all()
    results = [
            CoreElementFactorRelationData.model_validate(item).model_dump(by_alias=True)
            for item in board_part_datas
        ]
    values = ''
    for result in results:
        if (result['factorValueSrc'] not in ['manual_input']) and (result['factorType'] not in ['业务FRM芯片因子', '控制逻辑因子', '开销逻辑因子']):
            if result['element'] == '单板器件要素':
                if result['factorType'] != '交换FRM芯片因子':
                    part_dict = {"part":result['factorType'][:-2] + '器件'}
                else:
                    part_dict = {"part": '纯电_交换FRM器件'}
                values = querySrcBoardPartTreeSchemeSliceList(part_dict)
            elif result['element'] == '单板产品形态要素':
                if result['factorType'] == '单板支持的子架因子':
                    shelf_dict = {"elementType":"单板", "factorValueSrc": 'subrack_tree_table,subrack_name'}
                    values = querySrcCoreElementFactorRelationFactorValueList(shelf_dict, key_flag=True)
                elif result['factorType'] == '板卡类型因子':
                    board_dict = {"elementType":"单板", "factorValueSrc": 'board_valid_model_table,board_model_classification'}
                    values = querySrcCoreElementFactorRelationFactorValueList(board_dict)
            elif result['element'] == '单板业务要素':
                if result['factorType'] == '单板业务模型因子':
                    board_dict = {"elementType":"单板", "factorValueSrc": 'board_valid_model_table,valid_combination_board_model'}
                    values = querySrcCoreElementFactorRelationFactorValueList(board_dict)
                elif result['factorType'] == '客户侧电层业务因子':
                    business_model_rate_dict = {"elementType":"单板", "factorValueSrc": 'business_model_rate_table,business_type_list'}
                    values = querySrcCoreElementFactorRelationFactorValueList(business_model_rate_dict)
                elif result['factorType'] == '线路侧电层业务因子':
                    business_model_rate_dict = {"elementType":"单板", "factorValueSrc": 'business_model_rate_table,business_type_list'}
                    values = querySrcCoreElementFactorRelationFactorValueList(business_model_rate_dict)
            elif result['elementType'] == '子架':
                part_dict = {"part": result['elementType'] + result['factorType'][:-2] + '部件'}
                if result['factorType'] not in ['电源因子', '风扇因子']:
                    values = querySrcShelfPartTreeSchemeSliceList(part_dict, key_flag=True)
                else:
                    values = querySrcShelfPartTreeSchemeSliceList(part_dict)
            elif result['elementType'] == '业务':
                if result['factorType'] in ['客户侧光层业务因子', '线路侧光层业务因子']:
                    business_dict = {"elementType":"业务",  "factorType": result['factorType']}
                    values = querySrcCoreElementFactorRelationFactorValueList(business_dict)
                elif result['factorType'] == '网元业务模型因子':
                    business_dict = {"elementType":"业务",  "factorValueSrc": 'business_model_table,network_element_business_model'}
                    values = querySrcCoreElementFactorRelationFactorValueList(business_dict)
                
        elif result['factorType'] in ['业务FRM芯片因子']:
            values = querySrcBoardPartTreeSchemeSliceList({"part":'光电_业务FRM器件,纯电_业务FPGA器件,纯电_业务FRM器件'}, key_flag=True)
        elif result['factorType'] in ['开销逻辑因子']:
            values = querySrcBoardPartTreeSchemeSliceList({"part":'光电_业务FRM_开销FPGA器件,纯电_业务FPGA_开销FPGA器件,纯电_业务FRM_开销FPGA器件'}, key_flag=True)
        elif result['factorType'] in ['控制逻辑因子']:
            values = querySrcBoardPartTreeSchemeSliceList({"part":'光电_业务FRM_控制FPGA器件,纯电_业务FPGA_控制FPGA器件,纯电_业务FRM_控制FPGA器件'}, key_flag=True)
        if values:
            if result['factorType'] in ['业务FRM芯片因子', '开销逻辑因子', '控制逻辑因子', '单板支持的子架因子', '主控因子', '交叉因子', '背板因子']:
                values = [value.strip() for value in values if value.split('->')[1].strip()]
                src_values = list(set([value.split('->')[1] for value in values]))
                update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.id == int(result['id']), CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y')
                                                                          ).values(
                                                                factor_value=','.join(src_values), current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)
                update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.id == int(result['id']), CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y')
                                                                          ).values(
                                                                factor_ext_value=','.join(values), current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            else:
                update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.id == int(result['id']), CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y')
                                                                              ).values(
                                                                    factor_value=','.join(values), current_status=check_update, 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            db.session.execute(update_sql)
            values = ''
   
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())

def updateSourceCoreElementFactorRelationData():
    """
    更新指定来源的要素-因子-因子取值
    ---
    tags:
      - 业务方案要素-因子-因子取值
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
            elementType:
              type: string
              description: 要素类型
            element:
              type: string
              description: 要素
            factorType:
              type: string
              description: 因子
            factorValue:
              type: string
              description: 因子取值
          example:   # 示例值
            elementType: "业务"
            element: "扩展应用要素"
            factorType: "中断时间测量"
            factorValue: "O业务中断时间测量"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    updateSrcSourceCoreElementFactorRelationData(body_params, new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def updateCoreElementFactorRelationData():
    """
    更新指定的要素-因子-因子取值
    ---
    tags:
      - 业务方案要素-因子-因子取值
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
            elementType:
              type: string
              description: 要素类型
            element:
              type: string
              description: 要素
            factorType:
              type: string
              description: 因子
            factorValue:
              type: string
              description: 因子取值
            factor_details_link:
              type: string
              description: 因子详情链接
            factorValueSrc:
              type: string
              description: 因子取值来源
          example:   # 示例值
            id: "2"
            elementType: "业务方案"
            element: "扩展应用要素"
            factorType: "中断时间测量"
            factorValue: "O业务中断时间测量"
            factor_details_link: "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aad8970a419c11f0be9b9f19a4254cf4/view"
            factorValueSrc: "feature_relation_table,feature_name"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    employ_token = request.headers.get('X-Auth-Value')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    coreElementFactorRelationData = CoreElementFactorRelationData(**body_params)
    # 提取参数
    id = coreElementFactorRelationData.id
    core_element_type = coreElementFactorRelationData.core_element_type
    core_element = coreElementFactorRelationData.core_element
    factor = coreElementFactorRelationData.factor
    factor_value = coreElementFactorRelationData.factor_value
    factor_details_link = coreElementFactorRelationData.factor_details_link
    factor_value_src = coreElementFactorRelationData.factor_value_src
    # 查询原始数据
    # 1. 查询原始记录（使用 ORM）
    record = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).filter(
        CORE_ELEMENT_FACTOR_RELATION_TABLE.id == int(id),
        CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y'
    ).first()
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.id == int(id), CORE_ELEMENT_FACTOR_RELATION_TABLE.effective_flag == 'Y')
                                                                       ).values(core_element=core_element, factor=factor, 
                                                                                factor_details_link=factor_details_link, factor_value_src=factor_value_src,
                                                             factor_value=factor_value, current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)  
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def deleteCoreElementFactorRelationData():
    """
    删除指定的要素-因子-因子取值
    ---
    tags:
      - 业务方案要素-因子-因子取值
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
    coreElementFactorRelationData = request.get_json(force=True)
    # 提取参数
    id = coreElementFactorRelationData.get("id", "")
    
    # 检查新增的数据在数据表中是否已存在
    # delete_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(CORE_ELEMENT_FACTOR_RELATION_TABLE.id.in_([int(id) for id in id.split(',')])).values(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),operator_person=new_operator_person,effective_flag='N')
    # db.session.execute(delete_sql) 
    delete_count = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(CORE_ELEMENT_FACTOR_RELATION_TABLE.id.in_([int(id) for id in id.split(',')])).delete()
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})


def importExcelCoreElementFactorRelationData():
    """
    Excel文件上传接口
    ---
    tags:
      - 业务方案要素-因子-因子取值
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
      - name: elementType  # form-data参数名
        in: formData     # 指定为表单数据
        description: 要素类型
        required: true
        type: string       
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
    employ_token = request.headers.get('X-Auth-Value')
    new_operator_person = pub_get_employ_name(employ_no)

    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    file = request.files['file']
    elementType = request.form.get('elementType')
    # 检查文件类型

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
    try:

        df = pd.read_excel(file, engine="openpyxl")
        df.iloc[:, 1] = df.iloc[:, 1].ffill()
        df = df.fillna(value='')
        df['因子取值来源'] = df['因子取值来源'].astype(str) 
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['core_element_type'] = elementType
            factor_details_link = row["因子详情链接"] if "因子详情链接" in row else '' 
            table_dict['factor_details_link'] = factor_details_link
            table_dict['factor_value_src'] = handle_factor_value_src(row["因子取值来源"])
            table_dict['factor_value'] = ','.join(single_factor_value.strip() for single_factor_value in row["因子取值"].split('、'))
            db_factor_values = db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).filter(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == table_dict['core_element_type'],
                                                                                                CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == row["要素"],
                                                                       CORE_ELEMENT_FACTOR_RELATION_TABLE.factor == row["因子"]
                                                                       )).all()
            if len(db_factor_values) > 0 and row["因子取值"] and row["因子取值来源"]:
                update_sql = update(CORE_ELEMENT_FACTOR_RELATION_TABLE).where(and_(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == table_dict['core_element_type'],
                                                                                   CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element == row["要素"],
                                                                       CORE_ELEMENT_FACTOR_RELATION_TABLE.factor == row["因子"])
                                                                       ).values(factor_details_link=factor_details_link, factor_value_src=table_dict["factor_value_src"],
                                                             factor_value=table_dict["factor_value"], current_status=check_update,
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
            else:
                insert_sql = insert(CORE_ELEMENT_FACTOR_RELATION_TABLE).values(core_element_type=table_dict['core_element_type'], core_element=row["要素"], 
                                                                               factor=row["因子"], factor_details_link=factor_details_link, factor_value_src=table_dict["factor_value_src"],
                                                             factor_value=table_dict["factor_value"], current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()
        db.session.refresh(db.session.query(CORE_ELEMENT_FACTOR_RELATION_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}

def handle_factor_value_src(factor_value_src_description):
    if '0101' in factor_value_src_description:
        return "business_model_rate_table,network_element_business_model_rate"
    elif '0103' in factor_value_src_description:
        return "business_model_table,network_element_business_model"
    elif '0301' in factor_value_src_description:
        return "feature_relation_table,feature_name"
    else:
        return None
