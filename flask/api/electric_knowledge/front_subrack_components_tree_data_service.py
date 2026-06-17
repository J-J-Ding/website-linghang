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
from io import BytesIO

from electric_knowledge.data_model import db, SUBRACK_COMPONENTS_TREE_TABLE
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class SubrackComponentsTreeData(BaseModel):
    id: Optional[str] = None
    belong_product: Optional[str] = Field(None, alias="product")
    subrack_type: Optional[str] = Field(None, alias="shelfType")
    components: Optional[str] = Field(None, alias="part")
    component_business_plan: Optional[str] = Field(None, alias="businessScheme")
    business_plan_slicing: Optional[str] = Field(None, alias="schemeSlice")
    business_plan_details_link: Optional[str] = Field(None, alias="schemeSliceDetailLink")
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


def contains_all(list1, list2):
    return set(list2).issubset(list1)

def querySrcShelfPartTreeByParams(query_params: dict={}):    # 构建基础查询
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    if subrackComponentsTreeData.subrack_type:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type.in_(subrackComponentsTreeData.subrack_type.split(',')))
    if subrackComponentsTreeData.components:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.components.in_(subrackComponentsTreeData.components.split(',')))
   
    if subrackComponentsTreeData.component_business_plan:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan.in_(subrackComponentsTreeData.component_business_plan.split(',')))
    if subrackComponentsTreeData.business_plan_slicing:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing.in_(subrackComponentsTreeData.business_plan_slicing.split(',')))
   
    if subrackComponentsTreeData.current_status:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.current_status.in_(subrackComponentsTreeData.current_status.split(',')))
    try:
        baseSubrackComponentsTreeDatas = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).filter(and_(*conditions)).order_by(SUBRACK_COMPONENTS_TREE_TABLE.components, SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan, SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing).all() 
        results = []
        results = [
            SubrackComponentsTreeData.model_validate(item).model_dump(by_alias=True)
            for item in baseSubrackComponentsTreeDatas
        ]
        
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": []})

def queryShelfPartTreeByParams():    # 构建基础查询
    """
    查询指定的子架部件树取值
    ---
    tags:
      - 子架部件树
    description: 查询指定的子架部件树取值
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
      - name: shelfType
        in: query
        description: 子架类型
        required: false
        type: string
      - name: part
        in: query
        description: 部件名称
        required: false
        type: string
      - name: businessScheme
        in: query
        description: 部件业务方案
        required: false
        type: string
      - name: schemeSlice
        in: query
        description: 业务方案切片
        required: false
        type: string
      - name: schemeSliceDetailLink
        in: query
        description: 业务方案切片详情链接
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
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
          {
                "id": 1,
                "product": "19700产品",
                "shelfType": "电交叉子架",
                "part": "子架主控部件表",
                "businessScheme": "NCPM主控",
                "schemeSlice": "M1NCPM [CPU-NXP_PDCPK，内存-8G，交换芯片-博通，PHY芯片-马威尔，逻辑厂家-ALTERA]",
                "schemeSliceDetailLink": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aad8970a419c11f0be9b9f19a4254cf4/view",
                "status": "正常",
                "create_time": "2025-07-07T20:59:47",
                "update_time": "2025-07-11T18:56:24",
                "operator_person": "张进朋10305454",
                "effective_flag": "Y",
            }]}
    """
    
    query_params = request.args.to_dict()
    return querySrcShelfPartTreeByParams(query_params)

def queryShelfPartTreeTree():    # 构建基础查询
    """
    查询全部子架部件树取值记录（树形结构）
    ---
    tags:
      - 子架部件树
    description: 查询全部子架部件树取值记录（树形结构）
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
      - name: shelfType
        in: query
        description: 子架类型
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
                "label": "子卡器件表",
                "value": "子卡器件表",
                "children": [
                    {
                        "label": "子架专用_ARM架构",
                        "value": "子架专用_ARM架构",
                        "children": [
                            {
                                "label": "ARM架构_CCSM5子卡_6W11处理器_单核1G主频_2G内存_256M闪存",
                                "value": 1
                            },
                            {
                                "label": "ARM架构_CC128S子卡_128S处理器_双核1G主频_512M内存_256M闪存",
                                "value": 2
                            }
                        ]
                    },
                    {
                        "label": "子架专用_PPC架构",
                        "value": "子架专用_PPC架构",
                        "children": [
                            {
                                "label": "PPC架构_CCSM3子卡_MPC860处理器_单核50M主频_64M内存_16M闪存",
                                "value": 3
                            },
                            {
                                "label": "PPC架构_CCSM4子卡_MPC8306处理器_单核133M主频_128M内存_64M闪存",
                                "value": 4
                            }
                        ]
                    }
                ]
            },
            {
                "label": "GEARBOX器件表",
                "value": "GEARBOX器件表",
                "children": [
                    {
                        "label": "默升科技(CREDO)",
                        "value": "默升科技(CREDO)",
                        "children": [
                            {
                                "label": "CREDO_CRT55321",
                                "value": 5
                            }
                        ]
                    },
                    {
                        "label": "联发科(MediaTek)",
                        "value": "联发科(MediaTek)",
                        "children": [
                            {
                                "label": "联发科_MT3775",
                                "value": 6
                            }
                        ]
                    },
                    {
                        "label": "集益威(Gigayet)",
                        "value": "集益威(Gigayet)",
                        "children": [
                            {
                                "label": "集益威_JW8056",
                                "value": 7
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    if subrackComponentsTreeData.subrack_type:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type.in_(subrackComponentsTreeData.subrack_type.split(',')))
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.components, SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan, SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.components, SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan, SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing).order_by(SUBRACK_COMPONENTS_TREE_TABLE.components, SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan, SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing)
    ShelfComponentsTreeDatas = query.all()

    result = []
    current_level1 = None
    current_level2 = None
    current_level3 = None

    for data in ShelfComponentsTreeDatas:
        # 提取各层数据
        level1 = data[0]  # components (第一层)
        level2 = data[1]  # component_business_plan (第二层)
        level3 = data[2]  # business_plan_slicing (第三层)
        
        # 处理第一层
        if current_level1 is None or level1 != current_level1['label']:
            # 将前一个第一层节点添加到结果
            if current_level3 is not None:
                current_level2['children'].append(copy.deepcopy(current_level3))
            if current_level2 is not None:
                current_level1['children'].append(copy.deepcopy(current_level2))
            if current_level1 is not None:
                result.append(copy.deepcopy(current_level1))
            # 创建新的第一层节点
            current_level1 = {
                'label': level1,
                'value': level1,
                'children': []
            }
            # 重置下层节点
            current_level2 = None
            current_level3 = None
        
        # 处理第二层
        
        if current_level2 is None or level2 != current_level2['label']:
            # 将前一个第二层节点添加到第一层
            if current_level3 is not None:
                current_level2['children'].append(copy.deepcopy(current_level3))
            if current_level2 is not None:
                current_level1['children'].append(copy.deepcopy(current_level2))
            # 创建新的第二层节点
            current_level2 = {
                'label': level2,
                'value': level2,
                'children': []
            }
            # 重置下层节点
            current_level3 = None
        
        # 处理第三层
        if current_level3 is None or level3 != current_level3['label']:
            # 将前一个第三层节点添加到第二层
            if current_level3 is not None:
                current_level2['children'].append(copy.deepcopy(current_level3))
            # 创建新的第三层节点
            current_level3 = {
                'label': level3,
                'value': level3
            }

    # 添加最后一个节点到结果
    if current_level3 is not None:
        current_level2['children'].append(copy.deepcopy(current_level3))
    if current_level2 is not None:
        current_level1['children'].append(copy.deepcopy(current_level2))
    if current_level1 is not None:
        result.append(copy.deepcopy(current_level1))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def queryShelfPartTreeStatusList():    # 构建基础查询
    """
    查询子架部件树全部状态列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树全部状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    # 构建查询
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.current_status).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.current_status)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryShelfPartTreeProductList():    # 构建基础查询
    """
    查询子架部件树所属产品列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树所属产品列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    # 构建查询
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.belong_product).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.belong_product)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryShelfPartTreeShelfTypeList():    # 构建基础查询
    """
    查询子架部件树子架类型列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树子架类型列表
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    # 构建查询
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryShelfPartTreePartList():    # 构建基础查询
    """
    查询子架部件树全部部件列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树全部部件列表
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
      - name: shelfType
        in: query
        description: 子架类型
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    if subrackComponentsTreeData.subrack_type:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type.in_(subrackComponentsTreeData.subrack_type.split(',')))
    # 构建查询
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.components).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.components)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryShelfPartTreeBusinessSchemeList():    # 构建基础查询
    """
    查询子架部件树全部部件业务方案列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树全部部件业务方案列表
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
      - name: shelfType
        in: query
        description: 子架类型
        required: false
        type: string
      - name: part
        in: query
        description: 部件名称
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    if subrackComponentsTreeData.subrack_type:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type.in_(subrackComponentsTreeData.subrack_type.split(',')))
    if subrackComponentsTreeData.components:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.components == subrackComponentsTreeData.components)

    # 构建查询
    query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def querySrcShelfPartTreeSchemeSliceList(query_params:dict, key_flag:bool=False):    # 构建基础查询
    conditions = [SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y']
    subrackComponentsTreeData = SubrackComponentsTreeData(**query_params)
    if subrackComponentsTreeData.belong_product:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.belong_product.in_(subrackComponentsTreeData.belong_product.split(',')))
    if subrackComponentsTreeData.subrack_type:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.subrack_type.in_(subrackComponentsTreeData.subrack_type.split(',')))
    if subrackComponentsTreeData.components:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.components == subrackComponentsTreeData.components)
    if subrackComponentsTreeData.component_business_plan:
        conditions.append(SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan == subrackComponentsTreeData.component_business_plan)

    # 构建查询
    if not key_flag:
        query = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing).filter(and_(*conditions)).group_by(SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing)
    else:
        concat_expr = func.concat(
                func.coalesce(SUBRACK_COMPONENTS_TREE_TABLE.belong_product, ''), '->',
                func.coalesce(SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing, '')
        )
        query = db.session.query(concat_expr.label('combined_value')).filter(and_(*conditions)).group_by(concat_expr)
    # 动态添加过滤条件
    # 执行查询
    ShelfComponentsTreeDatas = query.all()
    result = []
    for subrackComponentsTreeData in ShelfComponentsTreeDatas:
        result.append(subrackComponentsTreeData[0])

    return list(set(result))

def queryShelfPartTreeSchemeSliceList():    # 构建基础查询
    """
    查询子架部件树全部业务方案切片列表
    ---
    tags:
      - 子架部件树
    description: 查询子架部件树全部业务方案切片列表
    parameters:
      - name: product
        in: query
        description: 归属产品
        required: false
        type: string
      - name: shelfType
        in: query
        description: 子架类型
        required: false
        type: string
      - name: part
        in: query
        description: 部件名称
        required: false
        type: string
      - name: businessScheme
        in: query
        description: 部件业务方案
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    query_params = request.args.to_dict()
    results = querySrcShelfPartTreeSchemeSliceList(query_params)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})

def syncUpdateCoreelementFactorRelation(components:list, new_operator_person:str):
    from electric_knowledge.front_business_coreelement_factor_relation_data_service import updateSrcSourceCoreElementFactorRelationData
    for component in components:
        factorType = component[:-2].replace('子架', '') + "因子"
        params_dict = {"elementType": "子架", "element": "子架核心部件要素", "factorType": factorType}
        updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)

def addShelfPartTreeData():
    """
    新增指定的子架部件树取值
    ---
    tags:
      - 子架部件树
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
            product:
              type: string
              description: 归属产品
            shelfType:
              type: string
              description: 子架类型
            part:
              type: string
              description: 部件
            businessScheme:
              type: string
              description: 部件业务方案
            schemeSlice:
              type: string
              description: 部件业务方案切片
            schemeSliceDetailLink:
              type: string
              description: 业务方案切片详情链接
          example:   # 示例值
            product: "19700产品" 
            shelfType: "传输子架"
            part: "客户侧C卡"
            businessScheme: "C_O"
            schemeSlice: ""
            schemeSliceDetailLink: ""
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    baseShelfComponentsTreeData = SubrackComponentsTreeData(**body_params)
    belong_product = baseShelfComponentsTreeData.belong_product
    subrack_type = baseShelfComponentsTreeData.subrack_type
    components = baseShelfComponentsTreeData.components
    component_business_plan = baseShelfComponentsTreeData.component_business_plan
    business_plan_slicing = baseShelfComponentsTreeData.business_plan_slicing
    business_plan_details_link = baseShelfComponentsTreeData.business_plan_details_link if baseShelfComponentsTreeData.business_plan_details_link else '' 

    # 检查新增的数据在数据表中是否已存在
    db_business_plan_slicing_values = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE.components, SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan, SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing).filter(and_(SUBRACK_COMPONENTS_TREE_TABLE.components == components,
                                                          SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan == SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan,
                                                           SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing.in_(business_plan_slicing.split(',')))).all()
    tmp_add_business_plan_slicing_list = business_plan_slicing.split(',')
    db_business_plan_slicing_list = []
    for db_business_plan_slicing_value in db_business_plan_slicing_values:
        db_business_plan_slicing_list.extend(db_business_plan_slicing_value[2].split(','))
    
    if contains_all(db_business_plan_slicing_list, tmp_add_business_plan_slicing_list):
        return {"code": 201, "status": "success", "message": "新增的子架部件-部件业务方案切片取值已存在!", "data": []}
    else:
        insert_sql = insert(SUBRACK_COMPONENTS_TREE_TABLE).values(belong_product=belong_product, subrack_type=subrack_type, components=components, component_business_plan=component_business_plan, 
                                                      business_plan_slicing=business_plan_slicing, business_plan_details_link=business_plan_details_link, current_status=check_add, 
                                                      create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)
        # 创建新用户
        db.session.commit()
        db.session.refresh(db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).first())
        syncUpdateCoreelementFactorRelation([components], new_operator_person)
        return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})
    
def updateShelfPartTreeData():
    """
    更新指定的子架部件树取值
    ---
    tags:
      - 子架部件树
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
              description: 每条记录唯一标识
            product:
              type: string
              description: 归属产品
            shelfType:
              type: string
              description: 子架类型
            part:
              type: string
              description: 部件
            businessScheme:
              type: string
              description: 部件业务方案
            schemeSlice:
              type: string
              description: 部件业务方案切片
            schemeSliceDetailLink:
              type: string
              description: 业务方案切片详情链接
          example:   # 示例值
            id: "1"
            product: "19700产品" 
            shelfType: "传输子架"
            part: "客户侧C卡"
            businessScheme: "C_O"
            schemeSlice: ""
            schemeSliceDetailLink: ""
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    baseShelfComponentsTreeData = SubrackComponentsTreeData(**body_params)
    id = baseShelfComponentsTreeData.id
    belong_product = baseShelfComponentsTreeData.belong_product
    subrack_type = baseShelfComponentsTreeData.subrack_type
    components = baseShelfComponentsTreeData.components
    component_business_plan = baseShelfComponentsTreeData.component_business_plan
    business_plan_slicing = baseShelfComponentsTreeData.business_plan_slicing
    business_plan_details_link = baseShelfComponentsTreeData.business_plan_details_link if baseShelfComponentsTreeData.business_plan_details_link else '' 

    # 检查更新的数据在数据表中是否已存在
    update_sql = update(SUBRACK_COMPONENTS_TREE_TABLE).where(and_(SUBRACK_COMPONENTS_TREE_TABLE.id == int(id), SUBRACK_COMPONENTS_TREE_TABLE.effective_flag == 'Y')
                                                                       ).values(belong_product=belong_product, subrack_type=subrack_type, components=components,  component_business_plan = component_business_plan,
                                  business_plan_slicing=business_plan_slicing, business_plan_details_link=business_plan_details_link, current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)
    # 创建新用户
    db.session.commit()
    db.session.refresh(db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).first())
    syncUpdateCoreelementFactorRelation([components], new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "更新成功", "data": []})

def deleteShelfPartTreeData():
    """
    删除指定的子架部件树取值
    ---
    tags:
      - 子架部件树
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
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json(force=True)
    baseShelfModelData = SubrackComponentsTreeData(**body_params)
    # 提取参数
    id = baseShelfModelData.id
    query_results = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).where(SUBRACK_COMPONENTS_TREE_TABLE.id.in_([int(id) for id in id.split(',')]))
    results = [
            SubrackComponentsTreeData.model_validate(item).model_dump(by_alias=True)
            for item in query_results.all()
    ]
    delete_count = query_results.delete()
    # 创建新用户 
    db.session.commit()
    components = []
    for result in results:
        components.append(result['part'])
    syncUpdateCoreelementFactorRelation(list(set(components)), new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def importExcelShelfPartTreeData():
    """
    Excel文件上传接口
    ---
    tags:
      - 子架部件树
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
        df["所属产品"] = df["所属产品"].ffill()
        df["子架类型"] = df["子架类型"].ffill()
        df = df.fillna(value='')

        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['belong_product'] = row["所属产品"] if "所属产品" in row else '' 
            table_dict['subrack_type'] = row["子架类型"] if "子架类型" in row else ''
            table_dict['components'] = row["部件"] if "部件" in row else '' 
            table_dict['component_business_plan'] = row["部件业务方案"] if "部件业务方案" in row else '' 
            table_dict['business_plan_slicing'] = row["业务方案切片"] if "业务方案切片" in row else ''
            table_dict['business_plan_details_link'] = row["业务方案切片详情链接"] if "业务方案切片详情链接" in row else ''
        
            db_factor_values = db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).filter(and_(SUBRACK_COMPONENTS_TREE_TABLE.components == table_dict['components'],
                                                                                      SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan == table_dict["component_business_plan"],
                                                                                      SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing == table_dict["business_plan_slicing"]
                                                                      )).all()
            if len(db_factor_values) > 0 and row["部件"] and row["部件业务方案"] and row["业务方案切片"]:
                update_sql = update(SUBRACK_COMPONENTS_TREE_TABLE).where(and_(SUBRACK_COMPONENTS_TREE_TABLE.components == table_dict['components'],
                                                                                      SUBRACK_COMPONENTS_TREE_TABLE.component_business_plan == table_dict["component_business_plan"],
                                                                                      SUBRACK_COMPONENTS_TREE_TABLE.business_plan_slicing == table_dict["business_plan_slicing"]
                                                                      )).values(belong_product=table_dict["belong_product"],subrack_type=table_dict["subrack_type"], business_plan_details_link=table_dict['business_plan_details_link'], current_status=check_update, 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)
            else:
                insert_sql = insert(SUBRACK_COMPONENTS_TREE_TABLE).values(belong_product=table_dict['belong_product'], subrack_type=table_dict['subrack_type'], components=table_dict['components'], 
                                                                              component_business_plan=table_dict["component_business_plan"], 
                                                            business_plan_slicing=table_dict["business_plan_slicing"], business_plan_details_link=table_dict['business_plan_details_link'], current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                    # 创建新用户 
            db.session.commit()
        db.session.refresh(db.session.query(SUBRACK_COMPONENTS_TREE_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
