from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import re
import pandas as pd
from flask import request, jsonify
from electric_knowledge.utils_icenter import create_icenter_page, delete_icenter_page, query_icenter_page, update_icenter_page
from electric_knowledge.front_hardware_tree_rule_data_service import service_query_hardware_tree_rule_dict_by_situation
from electric_knowledge.utils_pub import pub_random_string, pub_get_employ_name
from electric_knowledge.data_model import db, FEATURE_RELATION_TABLE
from electric_knowledge.utils_icenter import new_update_icenter_page
from electric_knowledge.utils_rdc import get_rdc_pr_team_list
from electric_knowledge.approval_service import ApprovalService
import logging

logger = logging.getLogger("Logger")

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class FeatureRelationData(BaseModel):
    id: Optional[str] = None
    feature_first_classification: Optional[str] = Field(None, alias="featureFirstType")
    feature_second_classification: Optional[str] = Field(None, alias="featureSecondType")
    feature_name: Optional[str] = Field(None, alias="feature")
    children_feature_name: Optional[str] = Field(None, alias="subFeature")
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = Field(None, alias="acceptanceCriteria")
    feature_content_link: Optional[str] = Field(None, alias="featureContentLink")
    belong_team: Optional[str] = Field(None, alias="belongTeam")
    estimated_dev_workload: Optional[int] = Field(None, alias="estimatedDevWorkload")
    requirement_sort: Optional[int] = Field(None, alias="requirementSort")
    parent: Optional[bool] = None
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


# 业务方案要素因子
def queryFeatureTreeByParams():    # 构建基础查询
    """
    查询指定的特性-子特性取值
    ---
    tags:
      - 特性-子特性
    description: 查询特性-子特性取值记录列表
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            featureFirstType:
              type: string
              description: 特性一级分类
            featureSecondType:
              type: string
              description: 特性二级分类
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            description:
              type: string
              description: 描述
            status:
              type: string
              description: 当前状态
          example:   # 示例值
            featureFirstType: "光层业务"
            featureSecondType: "灰光业务"
            feature: "F010201-E-灰光业务基础"
            subFeature: "FS010201-01-E-sfp/sfp+灰光模块"
            description: ""
            status: "正常"
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
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y']
    
    query_params = request.get_json()
    featureRelationData = FeatureRelationData(**query_params)
    
    # AND 条件的筛选字段
    if featureRelationData.feature_first_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_first_classification.in_(featureRelationData.feature_first_classification.split(',')))
    if featureRelationData.feature_second_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_second_classification.in_(featureRelationData.feature_second_classification.split(',')))
    if featureRelationData.description:
        conditions.append(FEATURE_RELATION_TABLE.description.like(f"%{featureRelationData.description}%")) 
    if featureRelationData.current_status:
        conditions.append(FEATURE_RELATION_TABLE.current_status.in_(featureRelationData.current_status.split(',')))
    
    # 处理 feature_name 和 children_feature_name 的 OR 逻辑
    # (feature_name 在列表中和 children_feature_name 在列表中) or (feature_name 在列表中和 children_feature_name 为空)
    if featureRelationData.feature_name:
        feature_name_list = featureRelationData.feature_name.split(',')
        if featureRelationData.children_feature_name:
            children_feature_name_list = featureRelationData.children_feature_name.split(',')
            feature_name_condition = FEATURE_RELATION_TABLE.feature_name.in_(feature_name_list)
            children_feature_name_in_condition = FEATURE_RELATION_TABLE.children_feature_name.in_(children_feature_name_list)
            children_feature_name_empty_condition = or_(
                FEATURE_RELATION_TABLE.children_feature_name.is_(None),
                FEATURE_RELATION_TABLE.children_feature_name == ''
            )
            or_condition = and_(
                feature_name_condition,
                or_(children_feature_name_in_condition, children_feature_name_empty_condition)
            )
            conditions.append(or_condition)
        else:
            # 只有 feature_name 条件，children_feature_name 可以是空或在任何值
            conditions.append(FEATURE_RELATION_TABLE.feature_name.in_(feature_name_list))
    elif featureRelationData.children_feature_name:
        # 只有 children_feature_name 条件，正常情况前端不允许只传children_feature_name
        conditions.append(FEATURE_RELATION_TABLE.children_feature_name.in_(featureRelationData.children_feature_name.split(',')))
    
    try:
        baseFeatureRelationDatas = db.session.query(FEATURE_RELATION_TABLE).filter(and_(*conditions)).order_by(FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).all()
        prev_feature = ''
        results = []
        parent_flag = False
        for item in baseFeatureRelationDatas:
            tmp_item = FeatureRelationData.model_validate(item).model_dump(by_alias=True)
            copy_tmp_item = copy.deepcopy(tmp_item)              
            if tmp_item['feature'] != prev_feature:
                if prev_feature:
                    results.append(copy.deepcopy(feature_item))
                tmp_item['parent'] = True
                tmp_item['childrenList'] = []
                tmp_item['subFeature'] = ''
                feature_item = copy.deepcopy(tmp_item)
                parent_flag = True
            else:
                copy_tmp_item['parent'] = False
                copy_tmp_item['featureFirstType_bak'] = copy_tmp_item['featureFirstType']
                copy_tmp_item['featureSecondType_bak'] = copy_tmp_item['featureSecondType']
                copy_tmp_item['feature_bak'] = copy_tmp_item['feature']
                copy_tmp_item['featureFirstType'] = ''
                copy_tmp_item['featureSecondType'] = ''
                copy_tmp_item['feature'] = ''
                feature_item['childrenList'].append(copy.deepcopy(copy_tmp_item))
                parent_flag = False

            if parent_flag:
                prev_feature = tmp_item['feature']
        if parent_flag:
            copy_tmp_item['parent'] = False
            copy_tmp_item['featureFirstType_bak'] = copy_tmp_item['featureFirstType']
            copy_tmp_item['featureSecondType_bak'] = copy_tmp_item['featureSecondType']
            copy_tmp_item['feature_bak'] = copy_tmp_item['feature']
            copy_tmp_item['featureFirstType'] = ''
            copy_tmp_item['featureSecondType'] = ''
            copy_tmp_item['feature'] = ''
            feature_item['childrenList'].append(copy.deepcopy(copy_tmp_item))
            # print(f"------------feature_item:\n{feature_item}")
        results.append(copy.deepcopy(feature_item))
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": {}})


def queryFeatureTreeTree():    # 构建基础查询
    """
    查询全部特性-子特性取值记录（树形结构）
    ---
    tags:
      - 特性-子特性
    description: 查询全部特性-子特性取值记录（树形结构）
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
                "label": "光层业务",
                "value": "光层业务",
                "children": [
                    {
                        "label": "灰光业务",
                        "value": "灰光业务",
                        "children": [
                            {
                                "label": "灰光业务特性1",
                                "value": "灰光业务特性1",
                                "children": [
                                    {
                                        "label": "灰光业务子特性1",
                                        "value": "灰光业务子特性1",
                                    },
                                    {
                                        "label": "灰光业务子特性2",
                                        "value": "灰光业务子特性2",
                                    },
                                ]
                            },
                            {
                                "label": "灰光业务特性2",
                                "value": "灰光业务特性2",
                                "children": [
                                    {
                                        "label": "灰光业务子特性3",
                                        "value": "灰光业务子特性3",
                                    },
                                    {
                                        "label": "灰光业务子特性4",
                                        "value": "灰光业务子特性4",
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        "label": "彩光业务",
                        "value": "彩光业务",
                        "children": [
                            {
                                "label": "彩光业务特性1",
                                "value": "彩光业务特性1",
                                "children": [
                                    {
                                        "label": "彩光业务子特性1",
                                        "value": "彩光业务子特性1",
                                    },
                                    {
                                        "label": "彩光业务子特性2",
                                        "value": "彩光业务子特性2",
                                    },
                                ]
                            },
                            {
                                "label": "彩光业务特性2",
                                "value": "彩光业务特性2",
                                "children": [
                                    {
                                        "label": "彩光业务子特性3",
                                        "value": "彩光业务子特性3",
                                    },
                                    {
                                        "label": "彩光业务子特性4",
                                        "value": "彩光业务子特性4",
                                    },
                                ]
                            },
                        ]
                    },
                ]
            },
            {
                "label": "电层业务",
                "value": "电层业务",
                "children": [
                    {
                        "label": "O业务",
                        "value": "O业务",
                        "children": [
                            {
                                "label": "O业务特性1",
                                "value": "O业务特性1",
                                "children": [
                                    {
                                        "label": "O业务子特性1",
                                        "value": "O业务子特性1",
                                    },
                                    {
                                        "label": "O业务子特性2",
                                        "value": "O业务子特性2",
                                    },
                                ]
                            },
                            {
                                "label": "O业务特性2",
                                "value": "O业务特性2",
                                "children": [
                                    {
                                        "label": "O业务子特性3",
                                        "value": "O业务子特性3",
                                    },
                                    {
                                        "label": "O业务子特性4",
                                        "value": "O业务子特性4",
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        "label": "OSU业务",
                        "value": "OSU业务",
                        "children": [
                            {
                                "label": "OSU业务特性1",
                                "value": "OSU业务特性1",
                                "children": [
                                    {
                                        "label": "OSU业务子特性1",
                                        "value": "OSU业务子特性1",
                                    },
                                    {
                                        "label": "OSU业务子特性2",
                                        "value": "OSU业务子特性2",
                                    },
                                ]
                            },
                            {
                                "label": "OSU业务特性2",
                                "value": "OSU业务特性2",
                                "children": [
                                    {
                                        "label": "OSU业务子特性3",
                                        "value": "OSU业务子特性3",
                                    },
                                    {
                                        "label": "OSU业务子特性4",
                                        "value": "OSU业务子特性4",
                                    },
                                ]
                            },
                        ]
                    },
                ]
            },
        ]
    }
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y', FEATURE_RELATION_TABLE.children_feature_name.is_not(None)]
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    query = db.session.query(FEATURE_RELATION_TABLE.feature_first_classification, FEATURE_RELATION_TABLE.feature_second_classification, FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.feature_first_classification, FEATURE_RELATION_TABLE.feature_second_classification, FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).order_by(FEATURE_RELATION_TABLE.feature_first_classification, FEATURE_RELATION_TABLE.feature_second_classification, FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name)
    baseFeatureRelationTreeDatas = query.all()

    result = []
    current_level1 = None
    current_level2 = None
    current_level3 = None
    for data in baseFeatureRelationTreeDatas:
        # 提取各层数据
        level1 = data[0]  # feature_first_classification (第一层)
        level2 = data[1]  # feature_second_classification (第二层)
        level3 = data[2]  # feature_name (第三层)
        level4 = data[3]  # children_feature_name (第四层)

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
                'value': level1 + '-' + pub_random_string(),
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
                'value': level2 + '-' + pub_random_string(),
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
                'value': level3 + '-' + pub_random_string()
            }
        
        # 处理第四层（叶子节点）
        if level4 is not None and level4 != "":
            # print(f"-------------level4:{level4}")
            if 'children' not in current_level3:
                current_level3['children'] = []
            current_level3['children'].append({
                'label': level4,
                'value': level4 + '-' + pub_random_string()
            })

    # 添加最后一个节点到结果
    if current_level3 is not None:
        current_level2['children'].append(copy.deepcopy(current_level3))
    if current_level2 is not None:
        current_level1['children'].append(copy.deepcopy(current_level2))
    if current_level1 is not None:
        result.append(copy.deepcopy(current_level1))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def queryFeatureTreeStatusList():    # 构建基础查询
    """
    查询特性-子特性取值记录的全部状态列表
    ---
    tags:
      - 特性-子特性
    description: 查询特性-子特性取值记录的全部状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y', FEATURE_RELATION_TABLE.current_status.is_not(None)]
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    query = db.session.query(FEATURE_RELATION_TABLE.current_status).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.current_status)
    # 执行查询
    baseFeatureRelationStatusDatas = query.all()
    result = []
    for baseFeatureRelationStatusData in baseFeatureRelationStatusDatas:
        result.append(baseFeatureRelationStatusData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryFeatureTreeFeatureFirstTypeList():    # 构建基础查询
    """
    查询特性一级分类取值记录列表
    ---
    tags:
      - 特性-子特性
    description: 查询特性一级分类取值记录列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    query = db.session.query(FEATURE_RELATION_TABLE.feature_first_classification).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.feature_first_classification)
    # 执行查询
    baseFeatureRelationFeatureFirstTypeDatas = query.all()
    result = []
    for baseFeatureRelationFeatureFirstTypeData in baseFeatureRelationFeatureFirstTypeDatas:
        result.append(baseFeatureRelationFeatureFirstTypeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryFeatureTreeFeatureSecondTypeList():    # 构建基础查询
    """
    查询特性二级分类取值记录列表
    ---
    tags:
      - 特性-子特性
    description: 查询特性二级分类取值记录列表
    parameters:
      - name: featureFirstType
        in: query
        description: 特性一级分类
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    if featureRelationData.feature_first_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_first_classification == featureRelationData.feature_first_classification)
    # 构建查询
    query = db.session.query(FEATURE_RELATION_TABLE.feature_second_classification).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.feature_second_classification)
    # 执行查询
    baseFeatureRelationFeatureData = query.all()
    result = []
    for baseFeatureRelationFeatureSecondTypeData in baseFeatureRelationFeatureData:
        result.append(baseFeatureRelationFeatureSecondTypeData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryFeatureTreeFeatureList():    # 构建基础查询
    """
    查询特性取值记录列表
    ---
    tags:
      - 特性-子特性
    description: 查询特性取值记录列表
    parameters:
      - name: featureFirstType
        in: query
        description: 特性一级分类
        required: false
        type: string
      - name: featureSecondType
        in: query
        description: 特性二级分类
        required: false
        type: string
      - name: feature
        in: query
        description: 特性
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y', FEATURE_RELATION_TABLE.feature_name != '']
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    if featureRelationData.feature_first_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_first_classification == featureRelationData.feature_first_classification)
    if featureRelationData.feature_second_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_second_classification == featureRelationData.feature_second_classification)
    if featureRelationData.feature_name:
        conditions.append(
            FEATURE_RELATION_TABLE.feature_name.in_(featureRelationData.feature_name.split(','))
        )

    # 构建查询
    query = db.session.query(FEATURE_RELATION_TABLE.feature_name).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.feature_name)
    # 动态添加过滤条件
    # 执行查询
    baseFeatureRelationFeatureDatas = query.all()
    result = []
    for baseFeatureRelationFeatureData in baseFeatureRelationFeatureDatas:
        result.append(baseFeatureRelationFeatureData[0])
    # 执行查询
   
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def queryFeatureTreeSubFeatureList():    # 构建基础查询
    """
    查询子特性取值记录列表
    ---
    tags:
      - 特性-子特性
    description: 查询子特性取值记录列表
    parameters:
      - name: featureFirstType
        in: query
        description: 特性一级分类
        required: false
        type: string
      - name: featureSecondType
        in: query
        description: 特性二级分类
        required: false
        type: string
      - name: feature
        in: query
        description: 特性
        required: false
        type: string
      - name: subFeature
        in: query
        description: 子特性
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y', FEATURE_RELATION_TABLE.children_feature_name != '']
    query_params = request.args.to_dict()
    featureRelationData = FeatureRelationData(**query_params)
    if featureRelationData.feature_first_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_first_classification == featureRelationData.feature_first_classification)
    if featureRelationData.feature_second_classification:
        conditions.append(FEATURE_RELATION_TABLE.feature_second_classification == featureRelationData.feature_second_classification)
    if featureRelationData.feature_name:
        conditions.append(
            FEATURE_RELATION_TABLE.feature_name.in_(featureRelationData.feature_name.split(','))
        )
    if featureRelationData.children_feature_name:
        conditions.append(
            FEATURE_RELATION_TABLE.children_feature_name.in_(featureRelationData.children_feature_name.split(','))
        )

    # 构建查询
    query = db.session.query(FEATURE_RELATION_TABLE.children_feature_name).filter(and_(*conditions)).group_by(FEATURE_RELATION_TABLE.children_feature_name)
    # 动态添加过滤条件
    # 执行查询
    baseFeatureRelationSubFeatureDatas = query.all()
    result = []
    for baseFeatureRelationSubFeatureData in baseFeatureRelationSubFeatureDatas:
        result.append(baseFeatureRelationSubFeatureData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def addSrcFeatureRelationData(employ_no, token, body_params):
    new_operator_person = pub_get_employ_name(employ_no)
    # 提取参数
    featureRelationData = FeatureRelationData(**body_params)
    # 提取参数
    feature_first_classification = featureRelationData.feature_first_classification
    feature_second_classification = featureRelationData.feature_second_classification
    feature_name = featureRelationData.feature_name
    children_feature_name = featureRelationData.children_feature_name
    description = featureRelationData.description
    acceptance_criteria = featureRelationData.acceptance_criteria
    feature_content_link = featureRelationData.feature_content_link
    belong_team = featureRelationData.belong_team
    estimated_dev_workload = featureRelationData.estimated_dev_workload
    requirement_sort = featureRelationData.requirement_sort
    # 检查新增的数据在数据表中是否已存在
    db_children_feature_values = db.session.query(FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name)\
                                           .filter(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_first_classification,
                                                        FEATURE_RELATION_TABLE.feature_second_classification == feature_second_classification,
                                                        FEATURE_RELATION_TABLE.feature_name == feature_name, FEATURE_RELATION_TABLE.children_feature_name == children_feature_name)).all()
    tmp_add_children_feature_value_list = children_feature_name.split(',')
    db_children_feature_value_list = []
    for db_children_feature_value in db_children_feature_values:
        db_children_feature_value_list.extend(db_children_feature_value[1].split(','))
    
    if contains_all(db_children_feature_value_list, tmp_add_children_feature_value_list):
        return False
    else:
        db_feature_values = db.session.query(FEATURE_RELATION_TABLE.feature_name).filter(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_first_classification,
                                                                                                                                                    FEATURE_RELATION_TABLE.feature_second_classification == feature_second_classification,
                                                                                                                                                    FEATURE_RELATION_TABLE.feature_name == feature_name)).all()
        if len(db_feature_values) < 1:
            create_flag, page_url = create_icenter_page(feature_first_classification, feature_second_classification, feature_name, '', employ_no=employ_no, token=token, type='feature')
            insert_feature_sql = insert(FEATURE_RELATION_TABLE).values(feature_first_classification=feature_first_classification, feature_name=feature_name,
                                                                       feature_second_classification=feature_second_classification, feature_content_link=page_url,parent = 1, current_status=check_add,
                                                                       create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                       update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
            db.session.execute(insert_feature_sql)
            db.session.commit()
        create_flag, page_url = create_icenter_page(feature_first_classification, feature_second_classification, feature_name, children_feature_name, employ_no=employ_no, token=token, type='feature')
        insert_children_feature_sql = insert(FEATURE_RELATION_TABLE).values(feature_first_classification=feature_first_classification, feature_name=feature_name,
                                                                            feature_second_classification=feature_second_classification, children_feature_name=children_feature_name,
                                                                            description=description, acceptance_criteria=acceptance_criteria, feature_content_link=page_url, belong_team=belong_team,
                                                                            estimated_dev_workload=estimated_dev_workload, requirement_sort=requirement_sort, parent = 0, current_status=check_add,
                                                                            create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_children_feature_sql)
        db.session.commit()
        # 创建新用户
        db.session.refresh(db.session.query(FEATURE_RELATION_TABLE).first())
        return create_flag


def addFeatureRelationData():
    """
    新增指定的特性-子特性取值
    ---
    tags:
      - 特性-子特性
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token
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
            change_type:
              type: string
              description: 变更类型（add/update/delete）
            old_data:
              type: object
              description: 原数据内容（修改/删除时需要）
            new_data:
              type: object
              description: 新数据内容
            zh_en_name_relation:
              type: object
              description: 前端列的中英文对应关系
            change_reason:
              type: string
              description: 变更原因
            assigned_persons:
              type: string
              description: 指定审批人（多个用逗号分隔）
          example:   # 示例值
            change_type: "update"
            old_data: {"feature_name": "原特性名称"}
            new_data: {"feature_name": "新特性名称"}
            zh_en_name_relation: {"feature_name": "特性名称"}
            change_reason: "数据更新"
            assigned_persons: "张进朋10305454,罗峰10164361"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()

    # 提交审核流程
    biz_type = '特性-子特性'

    result = ApprovalService.submit_change(
        biz_type=biz_type,
        biz_id='',
        change_type='add',
        new_data=body_params.get("new_data", {}),
        old_data={},
        zh_en_name_relation=body_params.get("zh_en_name_relation", ""),
        change_reason=body_params.get("change_reason", ""),
        submitter_person=new_operator_person,
        assigned_persons=body_params.get("assigned_persons", ""),
        token=token
    )

    if result['code'] == 200:
        return jsonify({"code": 200, "status": "success", "message": "已提交审核，等待审批通过后生效", "data": {"approval_id": result['data']['approval_id']}})
    else:
        return jsonify({"code": result['code'], "status": "failed", "message": result['message'], "data": None})

def updateSrcFeatureRelationData(employ_no, body_params):
    new_operator_person = pub_get_employ_name(employ_no)
    # 提取参数
    featureRelationData = FeatureRelationData(**body_params)
    # 提取参数
    id = featureRelationData.id
    feature_first_classification = featureRelationData.feature_first_classification 
    feature_second_classification = featureRelationData.feature_second_classification
    feature_name = featureRelationData.feature_name
    children_feature_name = featureRelationData.children_feature_name
    description = featureRelationData.description
    acceptance_criteria = featureRelationData.acceptance_criteria
    feature_content_link = featureRelationData.feature_content_link
    belong_team = featureRelationData.belong_team
    estimated_dev_workload = featureRelationData.estimated_dev_workload
    requirement_sort = featureRelationData.requirement_sort
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    toUpdateId = [int(id)]
    to_update_datas = db.session.query(FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).filter(FEATURE_RELATION_TABLE.id == int(id)).all()
    for to_update_data in to_update_datas:
        if not to_update_data[1]:
            to_update_ids = db.session.query(FEATURE_RELATION_TABLE.id).filter(FEATURE_RELATION_TABLE.feature_name==to_update_data[0]).all()
            for to_update_id in to_update_ids:
                toUpdateId.append(to_update_id[0])
    final_toUpdateId = list(set(toUpdateId))
    extra_toUpdateId = [x for x in final_toUpdateId if x not in set([int(id)])]

    update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.id == int(id), FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                               .values(feature_first_classification=feature_first_classification, feature_second_classification=feature_second_classification,
                                                       feature_name=feature_name, children_feature_name=children_feature_name, description=description, acceptance_criteria=acceptance_criteria,
                                                       belong_team=belong_team, estimated_dev_workload=estimated_dev_workload, requirement_sort=requirement_sort,
                                                       feature_content_link=feature_content_link, current_status=check_update, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                       operator_person=new_operator_person)
    db.session.execute(update_sql)
    db.session.commit()
    if extra_toUpdateId:
        update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.id.in_(extra_toUpdateId), FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                                   .values(feature_first_classification=feature_first_classification, feature_second_classification=feature_second_classification,
                                                           feature_name=feature_name, current_status=check_update, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                           operator_person=new_operator_person)
    db.session.execute(update_sql)
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(FEATURE_RELATION_TABLE).first())
    return []

def updateFeatureRelationData():
    """
    更新指定的特性-子特性取值
    ---
    tags:
      - 特性-子特性
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
            change_type:
              type: string
              description: 变更类型（add/update/delete）
            old_data:
              type: object
              description: 原数据内容（修改/删除时需要）
            new_data:
              type: object
              description: 新数据内容
            zh_en_name_relation:
              type: object
              description: 前端列的中英文对应关系
            change_reason:
              type: string
              description: 变更原因
            assigned_persons:
              type: string
              description: 指定审批人（多个用逗号分隔）
          example:   # 示例值
            id: "2"
            change_type: "update"
            old_data: {"feature_name": "原特性名称"}
            new_data: {"feature_name": "新特性名称"}
            zh_en_name_relation: {"feature_name": "特性名称"}
            change_reason: "数据更新"
            assigned_persons: "张进朋10305454,罗峰10164361"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()

    # 提取参数
    id = body_params.get("id", "")

    if not id:
        return jsonify({"code": 400, "status": "failed", "message": "缺少id参数", "data": None})

    # 获取原数据作为old_data
    old_record = db.session.query(FEATURE_RELATION_TABLE).filter(FEATURE_RELATION_TABLE.id == int(id)).first()
    old_data = FeatureRelationData.model_validate(old_record).model_dump() if old_record else {}

    # 构建新数据
    new_data = body_params.get("new_data", {})

    # 提交审核流程
    biz_type = '特性-子特性'

    result = ApprovalService.submit_change(
        biz_type=biz_type,
        biz_id=str(id),
        change_type='update',
        new_data=new_data,
        old_data=old_data,
        zh_en_name_relation=body_params.get("zh_en_name_relation", ""),
        change_reason=body_params.get("change_reason", ""),
        submitter_person=new_operator_person,
        assigned_persons=body_params.get("assigned_persons", ""),
        token=''
    )

    if result['code'] == 200:
        return jsonify({"code": 200, "status": "success", "message": "已提交审核，等待审批通过后生效", "data": {"approval_id": result['data']['approval_id']}})
    else:
        return jsonify({"code": result['code'], "status": "failed", "message": result['message'], "data": None})

def deleteSrcFeatureRelationData(employ_no, token, featureRelationData):
    # 提取参数
    id = featureRelationData.get("id", "")
    toDeleteId = [int(id) for id in id.split(',')]
    to_delete_datas = db.session.query(FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).filter(FEATURE_RELATION_TABLE.id.in_(toDeleteId)).all()
    for to_delete_data in to_delete_datas:
        if not to_delete_data[1]:
            to_delete_ids = db.session.query(FEATURE_RELATION_TABLE.id).filter(FEATURE_RELATION_TABLE.feature_name==to_delete_data[0]).all()
            for to_delete_id in to_delete_ids:
                toDeleteId.append(to_delete_id[0])
    final_toDeleteId = list(set(toDeleteId))
    # 检查新增的数据在数据表中是否已存在
    # delete_sql = update(FEATURE_RELATION_TABLE).where(FEATURE_RELATION_TABLE.id.in_(final_toDeleteId)).values(update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),operator_person=new_operator_person,effective_flag='N')
    # db.session.execute(delete_sql) 
    qry = db.session.query(FEATURE_RELATION_TABLE).where(FEATURE_RELATION_TABLE.id.in_(final_toDeleteId))
    featureRelationDatas = qry.all()
    delete_count = qry.delete()
    db.session.commit()
    db.session.refresh(db.session.query(FEATURE_RELATION_TABLE).first())
    for item in featureRelationDatas:
        tmp_item = FeatureRelationData.model_validate(item).model_dump(by_alias=True)
        if not tmp_item["subFeature"]:
            tmp_item["subFeature"] = ''
        delete_icenter_page(tmp_item["featureFirstType"], tmp_item["featureSecondType"], tmp_item["feature"], tmp_item["subFeature"], employ_no=employ_no, token=token, type='feature')
    # 创建新用户 
    
    return []


def deleteFeatureRelationData():
    """
    删除指定的特性-子特性取值
    ---
    tags:
      - 特性-子特性
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token
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
            change_type:
              type: string
              description: 变更类型（add/update/delete）
            old_data:
              type: object
              description: 原数据内容（修改/删除时需要）
            new_data:
              type: object
              description: 新数据内容
            zh_en_name_relation:
              type: object
              description: 前端列的中英文对应关系
            change_reason:
              type: string
              description: 变更原因
            assigned_persons:
              type: string
              description: 指定审批人（多个用逗号分隔）
          example:   # 示例值
            id: "2"
            change_type: "delete"
            old_data: {"feature_name": "原特性名称"}
            new_data: {"feature_name": "新特性名称"}
            zh_en_name_relation: {"feature_name": "特性名称"}
            change_reason: "数据更新"
            assigned_persons: "张进朋10305454,罗峰10164361"
    responses:
      200:
        description: 成功删除数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json(force=True)

    # 提取参数
    id = body_params.get("id", "")
    toDeleteId = [int(id) for id in id.split(',')]

    # 获取要删除的数据作为old_data
    old_records = db.session.query(FEATURE_RELATION_TABLE).filter(FEATURE_RELATION_TABLE.id.in_(toDeleteId)).all()

    # 提交审核流程
    biz_type = '特性-子特性'
    approval_ids = []

    for record in old_records:
        old_data = FeatureRelationData.model_validate(record).model_dump()
        result = ApprovalService.submit_change(
            biz_type=biz_type,
            biz_id=str(record.id),
            change_type='delete',
            new_data={},
            old_data=old_data,
            zh_en_name_relation=body_params.get("zh_en_name_relation", ""),
            change_reason=body_params.get("change_reason", ""),
            submitter_person=new_operator_person,
            assigned_persons=body_params.get("assigned_persons", ""),
            token=token
        )
        if result['code'] == 200:
            approval_ids.append(result['data']['approval_id'])

    if approval_ids:
        return jsonify({"code": 200, "status": "success", "message": "已提交审核，等待审批通过后生效", "data": {"approval_ids": approval_ids}})
    else:
        return jsonify({"code": 400, "status": "failed", "message": "提交审核失败", "data": None})


def importExcelFeatureRelationData():
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
    employ_token = request.headers.get('X-Auth-Value')
    new_operator_person = pub_get_employ_name(employ_no)

    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
        
    file = request.files['file']
    # 检查文件类型

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
    
    try:
        # 获取团队名称列表
        team_list = get_rdc_pr_team_list(employ_no, employ_token)
        # contents = await file.read()

        # # # 将内容封装为 BytesIO 对象，支持 seek 操作
        # excel_file = BytesIO(contents)
        # 读取 Excel 文件（无需保存到本地）
        df = pd.read_excel(file, engine="openpyxl")
        df["特性一级分类"] = df["特性一级分类"].ffill()
        df["特性二级分类"] = df["特性二级分类"].ffill()
        df["特性"] = df["特性"].ffill()
        df = df.fillna(value='')
        df['特性一级分类'] = df['特性一级分类'].astype(str) 
        
        # 校验字段满足规则
        input_err_info_list = []
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            factor_key_list = ["特性一级分类", "特性二级分类", "特性", "子特性", "预计开发工作量(人天)", "需求优先级"]
            all_rule_dict = {}
            if not str(row["子特性"] if "子特性" in row else '' ):
                all_rule_dict = service_query_hardware_tree_rule_dict_by_situation("特性&子特性", "所有")
            else:
                all_rule_dict = service_query_hardware_tree_rule_dict_by_situation("特性&子特性", "子特性")
                row_team_list = row.get("团队").split(',')
                if len(row_team_list) == 0:
                    input_err_info_list.append(f"【{row['特性一级分类']}】【{row['特性二级分类']}】【{row['特性']}】【{row['子特性']}】的【团队】【{row_team_list}】不能为空")
                for row_team_item in row_team_list:
                    if row_team_item not in team_list:
                        input_err_info_list.append(f"【{row['特性一级分类']}】【{row['特性二级分类']}】【{row['特性']}】【{row['子特性']}】的【团队】必须在【{team_list}】内")
            for factor_key_item in factor_key_list:
                single_rule_dict = all_rule_dict.get(factor_key_item)
                if not single_rule_dict: continue
                required_flag = single_rule_dict.get("required_flag")
                input_format = single_rule_dict.get("input_format")
                input_remark = single_rule_dict.get("input_remark")
                factor_value = row[factor_key_item]
                if isinstance(factor_value, (int, float)):
                    factor_value_str = f"{factor_value:g}"
                else:
                    factor_value_str = str(factor_value)
                if required_flag and not factor_value_str:
                    input_err_info_list.append(f"【{row['特性一级分类']}】【{row['特性二级分类']}】【{row['特性']}】【{row['子特性']}】的【{factor_key_item}】为必填项，不能为空。")
                if factor_value_str and input_format:
                    try:
                        pattern = re.compile(input_format)
                        if not pattern.fullmatch(factor_value_str):
                            input_err_info_list.append(f"【{row['特性一级分类']}】【{row['特性二级分类']}】【{row['特性']}】【{row['子特性']}】的【{factor_key_item}】【{factor_value_str}】格式存在问题。{input_remark}")
                    except re.error as e:
                        input_err_info_list.append(f"【{factor_key_item}】的正则表达式【{input_format}】存在问题。")
        if len(input_err_info_list) != 0:
            return {"code": 201, "status": "failed", "message": "导入失败", "data": input_err_info_list}

        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['feature_first_classification'] = row["特性一级分类"] if "特性一级分类" in row else ''
            table_dict['feature_second_classification'] = row["特性二级分类"] if "特性二级分类" in row else ''
            table_dict['feature_name'] = row["特性"] if "特性" in row else ''
            table_dict['children_feature_name'] = str(row["子特性"] if "子特性" in row else '' )
            table_dict['description'] = row["描述"] if "描述" in row else ''
            table_dict['acceptance_criteria'] = row["验收准则"] if "验收准则" in row else ''
            table_dict['feature_content_link'] = row["特性内容链接"] if "特性内容链接" in row else ''
            table_dict['belong_team'] = row["团队"] if "团队" in row else ''
            table_dict['estimated_dev_workload'] = None if not row.get("预计开发工作量(人天)") else int(float(row["预计开发工作量(人天)"]))
            table_dict['requirement_sort'] = None if not row.get("需求优先级") else int(float(row["需求优先级"]))
            if not table_dict['children_feature_name']:
                table_dict['parent'] = 1
            else:
                table_dict['parent'] = 0
            db_factor_values = db.session.query(FEATURE_RELATION_TABLE).filter(and_(FEATURE_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                                    FEATURE_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                                    FEATURE_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                                    FEATURE_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"]
                                                                       )).all()
            if len(db_factor_values) > 0 and row["特性一级分类"] and row["特性二级分类"] and row["特性"]:
                update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                       FEATURE_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                       FEATURE_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                       FEATURE_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"]))\
                                                            .values(description=table_dict['description'], acceptance_criteria=table_dict["acceptance_criteria"],
                                                                    feature_content_link=table_dict["feature_content_link"], current_status=check_update,
                                                                    belong_team=table_dict["belong_team"], estimated_dev_workload=table_dict["estimated_dev_workload"], requirement_sort=table_dict["requirement_sort"], 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
            else:
                insert_sql = insert(FEATURE_RELATION_TABLE).values(feature_first_classification=table_dict['feature_first_classification'],
                                                                   feature_second_classification=table_dict['feature_second_classification'], feature_name=table_dict["feature_name"],
                                                                   children_feature_name=table_dict["children_feature_name"], description=table_dict['description'],
                                                                   acceptance_criteria=table_dict["acceptance_criteria"], feature_content_link=table_dict["feature_content_link"],
                                                                   belong_team=table_dict["belong_team"], estimated_dev_workload=table_dict["estimated_dev_workload"], requirement_sort=table_dict["requirement_sort"], 
                                                                   parent=table_dict["parent"], current_status=check_add, 
                                                                   create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                   operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
        db.session.commit()

        db.session.refresh(db.session.query(FEATURE_RELATION_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        print(f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等")
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")
    

def addFeatureIcenterPage():
    """
    新增指定的特性-子特性iCenter页面
    ---
    tags:
      - 特性-子特性
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token
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
            featureFirstType:
              type: string
              description: 特性一级分类
            featureSecondType:
              type: string
              description: 特性二级分类
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
          example:   # 示例值
            featureFirstType: "光层业务"
            featureSecondType: "灰光业务"
            feature: "F010102-灰光业务基础特性"
            subFeature: "xx"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    featureRelationData = FeatureRelationData(**body_params)
    # 提取参数
    feature_first_classification_list = featureRelationData.feature_first_classification.split(',')
    feature_second_classification_list = featureRelationData.feature_second_classification.split(',')
    feature_name_list = featureRelationData.feature_name.split(',')
    children_feature_name_list = featureRelationData.children_feature_name.split(',')
    description = featureRelationData.description
    acceptance_criteria = featureRelationData.acceptance_criteria
    feature_data_list = []
    for index, feature_first_classification in enumerate(feature_first_classification_list):
        feature_second_classification = feature_second_classification_list[index]
        feature_name = feature_name_list[index]
        children_feature_name = children_feature_name_list[index]
        create_flag, page_url = create_icenter_page(feature_first_classification, feature_second_classification, feature_name, children_feature_name, employ_no=employ_no, token=token, type='feature')
        if not create_flag:
            if not children_feature_name:
                feature_data_list.append(feature_name)
            else:
                feature_data_list.append(children_feature_name)

        update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_first_classification, 
                                                               FEATURE_RELATION_TABLE.feature_second_classification == feature_second_classification, 
                                                               FEATURE_RELATION_TABLE.feature_name == feature_name, 
                                                               FEATURE_RELATION_TABLE.children_feature_name == children_feature_name, 
                                                               FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                                    .values(feature_content_link=page_url, current_status=normal, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                            operator_person=new_operator_person)
        db.session.execute(update_sql)
    db.session.commit()

    return jsonify({"code": 200, "status": "success", "message": "新增iCenter页面成功", "data": feature_data_list})

def deleteFeatureIcenterPage():
    """
    删除指定的特性-子特性iCenter页面
    ---
    tags:
      - 特性-子特性
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token
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
            featureFirstType:
              type: string
              description: 特性一级分类
            featureSecondType:
              type: string
              description: 特性二级分类
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
          example:   # 示例值
            featureFirstType: "光层业务"
            featureSecondType: "灰光业务"
            feature: "F010102-灰光业务基础特性"
            subFeature: "xx"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    featureRelationData = FeatureRelationData(**body_params)
    # 提取参数

    conditions = [FEATURE_RELATION_TABLE.effective_flag == 'Y']
    if featureRelationData.feature_first_classification:
        feature_first_classification_list = featureRelationData.feature_first_classification.split(',')
        conditions.append(FEATURE_RELATION_TABLE.feature_first_classification.in_(feature_first_classification_list))
    if featureRelationData.feature_second_classification:
        feature_second_classification_list = featureRelationData.feature_second_classification.split(',')
        conditions.append(FEATURE_RELATION_TABLE.feature_second_classification.in_(feature_second_classification_list))
    if featureRelationData.feature_name:
        feature_name_list = featureRelationData.feature_name.split(',')
        conditions.append(FEATURE_RELATION_TABLE.feature_name.in_(feature_name_list))
    children_feature_name_list = []
    if featureRelationData.children_feature_name:
        children_feature_name_list = featureRelationData.children_feature_name.split(',')
        conditions.append(FEATURE_RELATION_TABLE.children_feature_name.in_(children_feature_name_list))
    to_delete_datas = db.session.query(FEATURE_RELATION_TABLE.id, FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).filter(and_(*conditions)).all()
    toDeleteId = []
    for to_delete_data in to_delete_datas:
        toDeleteId.append(to_delete_data[0])
        if not to_delete_data[2]:
            to_delete_ids = db.session.query(FEATURE_RELATION_TABLE.id).filter(FEATURE_RELATION_TABLE.feature_name==to_delete_data[1]).all()
            for to_delete_id in to_delete_ids:
                toDeleteId.append(to_delete_id[0])
    final_toDeleteId = list(set(toDeleteId))
    featureRelationDatas = db.session.query(FEATURE_RELATION_TABLE).where(FEATURE_RELATION_TABLE.id.in_(final_toDeleteId)).all()
    feature_datas = []
    for item in featureRelationDatas:
        tmp_item = FeatureRelationData.model_validate(item).model_dump(by_alias=True)
        feature_first_classification = tmp_item["featureFirstType"]
        feature_second_classification = tmp_item["featureSecondType"]
        feature_name = tmp_item["feature"]
        children_feature_name = tmp_item["subFeature"]
        if not children_feature_name:
            children_feature_name = ''
        feature_datas.append(feature_first_classification + feature_second_classification + feature_name + children_feature_name)
        delete_page_flag = delete_icenter_page(feature_first_classification, feature_second_classification, feature_name, children_feature_name, employ_no=employ_no, token=token, type='feature')
        if delete_page_flag:
            update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_first_classification,
                                                                  FEATURE_RELATION_TABLE.feature_second_classification == feature_second_classification,
                                                                  FEATURE_RELATION_TABLE.feature_name == feature_name,
                                                                  FEATURE_RELATION_TABLE.children_feature_name == children_feature_name,
                                                                  FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                                        .values(feature_content_link='', current_status=normal, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                operator_person=new_operator_person)
            db.session.execute(update_sql)
    db.session.commit()
    for index, feature_first_classification in enumerate(feature_first_classification_list):
        feature_second_classification = feature_second_classification_list[index]
        feature_name = feature_name_list[index]
        if children_feature_name_list:
            children_feature_name = children_feature_name_list[index]
        else:
            children_feature_name = ''
        if (feature_first_classification + feature_second_classification + feature_name + children_feature_name) not in feature_datas:
            delete_page_flag = delete_icenter_page(feature_first_classification, feature_second_classification, feature_name, children_feature_name, employ_no=employ_no, token=token, type='feature')

    return jsonify({"code": 200, "status": "success", "message": "删除iCenter页面成功", "data": []})


def syncFeatureIcenterPage():
    """
    从空间2.0同步指定的特性-子特性iCenter页面url到前端页面
    ---
    tags:
      - 特性-子特性
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
            data_type:
              type: string
              description: icenter空间2.0页面数据类型
          example:   # 示例值
            data_type: "feature"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    results = query_icenter_page(body_params.get("data_type", ""))
    feature_children_feature = []
    for result in results:
        feature_first_classification = result["feature_first_classification"]
        feature_second_classification = result["feature_second_classification"]
        feature_name = result["feature_name"]
        children_feature_name = result["children_feature_name"]
        feature_children_feature.append(feature_name + children_feature_name)
        feature_content_link = result["feature_content_link"]
        update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_first_classification, 
                                                               FEATURE_RELATION_TABLE.feature_second_classification == feature_second_classification, 
                                                               FEATURE_RELATION_TABLE.feature_name == feature_name, 
                                                               FEATURE_RELATION_TABLE.children_feature_name == children_feature_name, 
                                                               FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                                    .values(feature_content_link=feature_content_link, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                            operator_person=new_operator_person)

        db.session.execute(update_sql)
    db.session.commit()
    feature_datas = db.session.query(FEATURE_RELATION_TABLE.feature_first_classification, FEATURE_RELATION_TABLE.feature_second_classification, FEATURE_RELATION_TABLE.feature_name, FEATURE_RELATION_TABLE.children_feature_name).all()
    for feature_data in feature_datas:
        if (feature_data[2] + feature_data[3]) not in feature_children_feature:
            update_sql = update(FEATURE_RELATION_TABLE).where(and_(FEATURE_RELATION_TABLE.feature_first_classification == feature_data[0],
                                                               FEATURE_RELATION_TABLE.feature_second_classification == feature_data[1],
                                                               FEATURE_RELATION_TABLE.feature_name == feature_data[2],
                                                               FEATURE_RELATION_TABLE.children_feature_name == feature_data[3],
                                                               FEATURE_RELATION_TABLE.effective_flag == 'Y'))\
                                                        .values(feature_content_link='',update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),operator_person=new_operator_person)
            db.session.execute(update_sql)
    db.session.commit()
    return jsonify({"code": 200, "status": "success", "message": "同步iCenter 2.0页面url到前端页面成功", "data": []})


def updateFeatureIcenterPage():
    """
    读取空间2.0最新的模版内容，来更新指定的特性-子特性iCenter页面内容
    ---
    tags:
      - 特性-子特性
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token
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
            featureFirstType:
              type: string
              description: 特性一级分类
            featureSecondType:
              type: string
              description: 特性二级分类
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            tag_flag:
              type: boolean
              description: 是否给页面打标签
          example:   # 示例值
            featureFirstType: "光层业务"
            featureSecondType: "灰光业务"
            feature: "F010102-灰光业务基础特性"
            subFeature: "xx"
            tag_flag: False
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    body_params = request.get_json()
    tag_flag = body_params.get('tag_flag', False)
    # 提取参数
    featureRelationData = FeatureRelationData(**body_params)
    # 提取参数

    if featureRelationData.feature_first_classification:
        feature_first_classification_list = featureRelationData.feature_first_classification.split(',')
    if featureRelationData.feature_second_classification:
        feature_second_classification_list = featureRelationData.feature_second_classification.split(',')
    if featureRelationData.feature_name:
        feature_name_list = featureRelationData.feature_name.split(',')
    children_feature_name_list = []
    if featureRelationData.children_feature_name:
        children_feature_name_list = featureRelationData.children_feature_name.split(',')
    for index, feature_first_classification in enumerate(feature_first_classification_list):
        feature_second_classification = feature_second_classification_list[index]
        feature_name = feature_name_list[index]
        if children_feature_name_list:
            children_feature_name = children_feature_name_list[index]
        else:
            children_feature_name = ""
        update_icenter_page(feature_first_classification, feature_second_classification, feature_name, children_feature_name, employ_no, token, tag_flag=tag_flag)
     
    return jsonify({"code": 200, "status": "success", "message": "读取空间2.0最新的模版内容，来更新指定的特性-子特性iCenter页面内容成功", "data": []})