from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func, literal_column
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from io import BytesIO

from electric_knowledge.data_model import db, FEATURE_BOARD_RELATION_TABLE, FEATURE_RELATION_TABLE
from electric_knowledge.utils_pub import pub_random_string, pub_get_employ_name
from flask import request, jsonify
import logging

logger = logging.getLogger("Logger")


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class FeatureBoardRelationData(BaseModel):
    id: Optional[str] = None
    feature_first_classification: Optional[str] = Field(None, alias="featureFirstType")
    feature_second_classification: Optional[str] = Field(None, alias="featureSecondType")
    feature_name: Optional[str] = Field(None, alias="feature")
    children_feature_name: Optional[str] = Field(None, alias="subFeature")
    related_board_model: Optional[str] = Field(None, alias="relatedBoardModel")
    related_flag: Optional[str] = Field(None, alias="relatedFlag")
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

def querySrcFeatureBoardByParams(query_params:dict={}, markdown_flag:bool=False):    # 构建基础查询
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y']    
    featureRelationData = FeatureBoardRelationData(**query_params)
    # AND 条件的筛选字段
    if featureRelationData.feature_first_classification:
        conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_first_classification.in_(featureRelationData.feature_first_classification.split(',')))
    if featureRelationData.feature_second_classification:
        conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_second_classification.in_(featureRelationData.feature_second_classification.split(',')))
    # 处理 feature_name 和 children_feature_name 的 OR 逻辑
    if featureRelationData.feature_name:
        feature_name_list = featureRelationData.feature_name.split(',')
        if featureRelationData.children_feature_name:
            children_feature_name_list = featureRelationData.children_feature_name.split(',')
            feature_name_condition = FEATURE_BOARD_RELATION_TABLE.feature_name.in_(feature_name_list)
            children_feature_name_in_condition = FEATURE_BOARD_RELATION_TABLE.children_feature_name.in_(children_feature_name_list)
            children_feature_name_empty_condition = or_(
                FEATURE_BOARD_RELATION_TABLE.children_feature_name.is_(None),
                FEATURE_BOARD_RELATION_TABLE.children_feature_name == ''
            )
            or_condition = and_(
                feature_name_condition,
                or_(children_feature_name_in_condition, children_feature_name_empty_condition)
            )
            conditions.append(or_condition)
        else:
            # 只有 feature_name 条件，children_feature_name 可以是空或在任何值
            conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_name.in_(feature_name_list))
    elif featureRelationData.children_feature_name:
        # 只有 children_feature_name 条件
        conditions.append(FEATURE_BOARD_RELATION_TABLE.children_feature_name.in_(featureRelationData.children_feature_name.split(',')))

    if featureRelationData.related_board_model:
        conditions.append(FEATURE_BOARD_RELATION_TABLE.related_board_model.in_(featureRelationData.related_board_model.split(',')))    
    if featureRelationData.related_flag:
        conditions.append(FEATURE_BOARD_RELATION_TABLE.related_flag.in_([featureRelationData.related_flag,'1', '1.0']))
    if featureRelationData.current_status:
        conditions.append(FEATURE_BOARD_RELATION_TABLE.current_status.in_(featureRelationData.current_status.split(',')))
    try:
        baseFeatureRelationDatas = db.session.query(FEATURE_BOARD_RELATION_TABLE).filter(and_(*conditions)).order_by(FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name, FEATURE_BOARD_RELATION_TABLE.related_board_model).all() 
        results = []
        related_board_model_list = []
        tmp_dict = dict()
        copy_tmp_dict = dict()
        prev_feature = ''
        prev_sub_feature = ''
        feature_item = dict()
        for item in baseFeatureRelationDatas:
            tmp_item = FeatureBoardRelationData.model_validate(item).model_dump(by_alias=True)
            copy_tmp_item = copy.deepcopy(tmp_item)              
            if tmp_item['feature'] != prev_feature or (not tmp_item['subFeature']):
                if prev_feature and tmp_item['feature'] != prev_feature:
                    if feature_item:
                        copy_tmp_item1.pop('relatedBoardModel', None)
                        copy_tmp_item1.pop('relatedFlag', None)
                        feature_item['childrenList'].append(copy.deepcopy({**copy_tmp_item1, **copy_tmp_dict}))
                        results.append(copy.deepcopy(feature_item))
                        feature_item = dict()
                    copy_tmp_dict = dict()
                    prev_sub_feature = ''
                tmp_item['childrenList'] = []
                tmp_item['subFeature'] = ''
                tmp_item['create_time'] = ''
                tmp_item['update_time'] = ''
                tmp_item['effective_flag'] = ''
                tmp_dict[tmp_item['relatedBoardModel']] = tmp_item['relatedFlag']                
                prev_feature = tmp_item['feature']
                related_board_model_list.append({"boardBusiness":tmp_item['relatedBoardModel'], "status":tmp_item['status'],
                                                 "operator_person":tmp_item['operator_person']})
                tmp_item['operator_person'] = ''
                tmp_item1 = copy.deepcopy(tmp_item)
            else:
                if tmp_dict:
                    tmp_item1.pop('relatedBoardModel', None)
                    tmp_item1.pop('relatedFlag', None)
                    feature_item = copy.deepcopy({**tmp_item1, **tmp_dict})
                    tmp_dict = dict()
                
                copy_tmp_item['featureFirstType_bak'] = copy_tmp_item['featureFirstType']
                copy_tmp_item['featureSecondType_bak'] = copy_tmp_item['featureSecondType']
                copy_tmp_item['feature_bak'] = copy_tmp_item['feature']
                copy_tmp_item['featureFirstType'] = ''
                copy_tmp_item['featureSecondType'] = ''
                copy_tmp_item['feature'] = ''
                relatedBoardModel = copy_tmp_item['relatedBoardModel']
                related_board_model_list.append({"boardBusiness":copy_tmp_item['relatedBoardModel'], "status":copy_tmp_item['status'],
                                                 "operator_person":copy_tmp_item['operator_person']})
                relatedFlag = copy_tmp_item['relatedFlag']
                if prev_sub_feature and copy_tmp_item['subFeature'] != prev_sub_feature:
                    copy_tmp_item1.pop('relatedBoardModel', None)
                    copy_tmp_item1.pop('relatedFlag', None)
                    feature_item['childrenList'].append(copy.deepcopy({**copy_tmp_item1, **copy_tmp_dict}))
                    copy_tmp_dict = dict()
                copy_tmp_dict[relatedBoardModel] = relatedFlag
                prev_sub_feature = copy_tmp_item['subFeature']
                copy_tmp_item1 = copy.deepcopy(copy_tmp_item)
                if relatedBoardModel not in feature_item:
                    feature_item[relatedBoardModel] = relatedFlag
        if copy_tmp_dict:
            copy_tmp_item1.pop('relatedBoardModel', None)
            copy_tmp_item1.pop('relatedFlag', None)
            feature_item['childrenList'].append(copy.deepcopy({**copy_tmp_item1, **copy_tmp_dict}))
            
        if tmp_dict:
            tmp_item1.pop('relatedBoardModel', None)
            tmp_item1.pop('relatedFlag', None)
            feature_item = copy.deepcopy({**tmp_item1, **tmp_dict})
            feature_item['childrenList'] = []
        results.append(copy.deepcopy(feature_item))
        if markdown_flag:
            return results
        return (results, remove_duplicate_dicts(related_board_model_list, "boardBusiness"), 200)
    except Exception as e:
        return ([], [], 400)


def remove_duplicate_dicts(dict_list, main_key:str=''):
    """
    安全去除列表中重复的字典（完全匹配所有键值对）

    :param dict_list: 字典列表
    :return: 去重后的字典列表
    """
    seen = set()
    unique_list = []
    for d in dict_list:
        # 将字典转换为排序后的JSON字符串（确保相同字典生成相同字符串）
        dict_str = json.dumps(d, sort_keys=True)
        if (not main_key) and dict_str not in seen:
            seen.add(dict_str)
            unique_list.append(d)
        elif main_key and d[main_key] not in seen:
            seen.add(d[main_key])
            unique_list.append(d)
    return unique_list


# 特性-单板
def queryFeatureBoardByParams():    # 构建基础查询
    """
    查询特性单板取值记录列表
    ---
    tags:
      - 特性-单板
    description: 查询特性单板取值记录列表
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            relatedBoardModel:
              type: string
              description: 单板模型
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            relatedFlag:
              type: string
              description: 关联标识
            status:
              type: string
              description: 当前状态
          example:   # 示例值
            relatedBoardModel: "L1"
            feature: "灰光业务"
            subFeature: "F010102-灰光业务基础特性"
            relatedFlag: "xx"
            status: "xx"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """    
    # query_params = request.args.to_dict()
    body_params = request.get_json()
    results, board, code = querySrcFeatureBoardByParams(body_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results, "board": board})
    

def queryFeatureBoardTree():    # 构建基础查询
    """
    查询全部特性-单板取值记录（树形结构）
    ---
    tags:
      - 特性-单板
    description: 查询全部特性-单板取值记录（树形结构）
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
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y', FEATURE_BOARD_RELATION_TABLE.children_feature_name.is_not(None)]
    query_params = request.args.to_dict()
    featureRelationData = FeatureBoardRelationData(**query_params)
    query = db.session.query(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name).filter(and_(*conditions)).group_by(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name).order_by(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name)
    baseFeatureBoardRelationTreeDatas = query.all()
    result = []
    current_level1 = None
    current_level2 = None
    current_level3 = None

    for data in baseFeatureBoardRelationTreeDatas:
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


def queryFeatureInfoDict():    # 构建基础查询
    """
    查询全部特性-单板取值记录（树形结构）
    ---
    tags:
      - 特性-单板
    description: 查询全部特性-单板取值记录（树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
        "code": 200,
        "message": "获取成功",
        "status": "success",
        "data": {
            "光层业务": {
                "灰光业务": {
                    "灰光业务特性1": ["灰光业务子特性1", "灰光业务子特性2"],
                    "灰光业务特性2": ["灰光业务子特性3", "灰光业务子特性4"]
                },
                "彩光业务": {
                    "彩光业务特性1": ["彩光业务子特性1", "彩光业务子特性2"],
                    "彩光业务特性2": ["彩光业务子特性3", "彩光业务子特性4"]
                }
            },
        }
    }
    """
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y', FEATURE_BOARD_RELATION_TABLE.children_feature_name.is_not(None)]
    query = db.session.query(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name).filter(and_(*conditions)).group_by(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name).order_by(FEATURE_BOARD_RELATION_TABLE.feature_first_classification, FEATURE_BOARD_RELATION_TABLE.feature_second_classification, FEATURE_BOARD_RELATION_TABLE.feature_name, FEATURE_BOARD_RELATION_TABLE.children_feature_name)
    baseFeatureBoardRelationTreeDatas = query.all()

    result = {}

    for data in baseFeatureBoardRelationTreeDatas:
        # 提取各层数据
        level1 = data[0]  # feature_first_classification (第一层)
        level2 = data[1]  # feature_second_classification (第二层)
        level3 = data[2]  # feature_name (第三层)
        level4 = data[3]  # children_feature_name (第四层)
        if level1 not in result: result[level1] = {}
        if level2 not in result[level1]: result[level1][level2] = {}
        if level3 not in result[level1][level2]: result[level1][level2][level3] = []
        if level4 not in result[level1][level2][level3]: result[level1][level2][level3].append(level4)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def querySrcFeatureBoardRelation(boardBusinessModel: str="", featureFirstType:str="", featureSecondType:str="",feature:str="", subFeature:str=""):    # 构建基础查询
   
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y',  
                  FEATURE_BOARD_RELATION_TABLE.related_flag > '0.0']
    if boardBusinessModel.strip():
        conditions.append(FEATURE_BOARD_RELATION_TABLE.related_board_model.in_(boardBusinessModel.split(',')))
    if featureFirstType.strip():
        conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_first_classification.in_(featureFirstType.split(',')))
    if featureSecondType.strip():
        conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_second_classification==featureSecondType.strip())
    if feature.strip():
        conditions.append(FEATURE_BOARD_RELATION_TABLE.feature_name.in_(feature.strip().split(',')))
    if subFeature.strip():
        conditions.append(FEATURE_BOARD_RELATION_TABLE.children_feature_name.in_(subFeature.strip().split(',')))
    d_values = literal_column(f"GROUP_CONCAT(DISTINCT {FEATURE_BOARD_RELATION_TABLE.related_board_model.key} SEPARATOR ',')").label('related_board_models')
    src_results = db.session.query(
            FEATURE_BOARD_RELATION_TABLE.feature_first_classification,
            FEATURE_BOARD_RELATION_TABLE.feature_second_classification,
            FEATURE_BOARD_RELATION_TABLE.feature_name,
            FEATURE_BOARD_RELATION_TABLE.children_feature_name,
            FEATURE_RELATION_TABLE.description,
            FEATURE_RELATION_TABLE.acceptance_criteria,
            FEATURE_RELATION_TABLE.feature_content_link,
            FEATURE_RELATION_TABLE.belong_team,              # ✅ 新增
            FEATURE_RELATION_TABLE.estimated_dev_workload,   # ✅ 新增
            FEATURE_RELATION_TABLE.requirement_sort,         # ✅ 新增
            d_values
        ).join(
            FEATURE_RELATION_TABLE,
            and_(
                FEATURE_BOARD_RELATION_TABLE.feature_name == FEATURE_RELATION_TABLE.feature_name,
                FEATURE_BOARD_RELATION_TABLE.children_feature_name == FEATURE_RELATION_TABLE.children_feature_name
            ),
            isouter=True
        ).filter(and_(*conditions)).group_by(
            FEATURE_BOARD_RELATION_TABLE.feature_first_classification,
            FEATURE_BOARD_RELATION_TABLE.feature_second_classification,
            FEATURE_BOARD_RELATION_TABLE.feature_name,
            FEATURE_BOARD_RELATION_TABLE.children_feature_name,
            FEATURE_RELATION_TABLE.description,
            FEATURE_RELATION_TABLE.acceptance_criteria,
            FEATURE_RELATION_TABLE.feature_content_link,
            FEATURE_RELATION_TABLE.belong_team,
            FEATURE_RELATION_TABLE.estimated_dev_workload,
            FEATURE_RELATION_TABLE.requirement_sort,
        ).all()
    results = []
    for src_result in src_results:
        results.append({
            "featureFirstType": src_result[0],
            "featureSecondType": src_result[1],
            "feature": src_result[2],
            "subFeature": src_result[3],
            "description": src_result[4],
            "acceptanceCriteria": src_result[5],
            "featureContentLink": src_result[6],
            "belong_team": src_result[7],
            "estimated_dev_workload": src_result[8],
            "requirement_sort": src_result[9],
            "related_board_models": src_result[10]
        })
    return results

    
def queryFeatureBoardBoardList():    # 构建基础查询
    """
    查询特性-单板的全部单板取值列表
    ---
    tags:
      - 特性-单板
    description: 查询特性-单板的全部单板取值列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y', FEATURE_BOARD_RELATION_TABLE.current_status.is_not(None)]
    query_params = request.args.to_dict()
    featureRelationData = FeatureBoardRelationData(**query_params)
    query = db.session.query(FEATURE_BOARD_RELATION_TABLE.related_board_model).filter(and_(*conditions)).group_by(FEATURE_BOARD_RELATION_TABLE.related_board_model)
    # 动态添加过滤条件
    
    # 执行查询
    baseFeatureRelationStatusDatas = query.all()
    result = []
    for baseFeatureRelationStatusData in baseFeatureRelationStatusDatas:
        result.append(baseFeatureRelationStatusData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def queryFeatureBoardStatusList():    # 构建基础查询
    """
    查询特性-单板取值记录的全部状态列表
    ---
    tags:
      - 特性-单板
    description: 查询特性-单板取值记录的全部状态列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    conditions = [FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y', FEATURE_BOARD_RELATION_TABLE.current_status.is_not(None)]
    query_params = request.args.to_dict()
    featureRelationData = FeatureBoardRelationData(**query_params)
    query = db.session.query(FEATURE_BOARD_RELATION_TABLE.current_status).filter(and_(*conditions)).group_by(FEATURE_BOARD_RELATION_TABLE.current_status)

    # 执行查询
    baseFeatureRelationStatusDatas = query.all()
    result = []
    for baseFeatureRelationStatusData in baseFeatureRelationStatusDatas:
        result.append(baseFeatureRelationStatusData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def updateFeatureBoardData():
    """
    更新指定的特性-单板取值
    ---
    tags:
      - 特性-单板
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
            relatedBoardModel:
              type: string
              description: 单板模型
            relatedFlag:
              type: string
              description: 关联标志
          example:   # 示例值
            id: "2"
            featureFirstType: "光层业务"
            featureSecondType: "灰光业务"
            feature: "F010102-灰光业务基础特性"
            subFeature: "xx"
            relatedBoardModel: "xx"
            relatedFlag: "xx"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    related_board_model = ''
    for body_param in body_params:
        if not related_board_model:
            key_list = list(body_param.keys())
            key_list.remove("id")
            related_board_model = key_list[0]

        # 提取参数
        id = body_param["id"]
        # related_flag = 1 if featureRelationData.related_flag else 0
        related_flag = body_param[related_board_model]
        # 检查新增的数据在数据表中是否已存在
        new_operator_person = pub_get_employ_name(employ_no)
        
        update_sql = update(FEATURE_BOARD_RELATION_TABLE).where(and_(FEATURE_BOARD_RELATION_TABLE.id == int(id), FEATURE_BOARD_RELATION_TABLE.effective_flag == 'Y')
                                                                      ).values(
                                                            related_board_model=related_board_model , related_flag=related_flag, current_status=check_update, 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    
        db.session.execute(update_sql)
    db.session.commit()

    db.session.refresh(db.session.query(FEATURE_BOARD_RELATION_TABLE).first())
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})


def importExcelFeatureBoardData():
    """
    Excel文件上传接口
    ---
    tags:
      - 特性-单板
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
        df = pd.read_excel(file, engine="openpyxl")
        df["特性一级分类"] = df["特性一级分类"].ffill()
        df["特性二级分类"] = df["特性二级分类"].ffill()
        df["特性"] = df["特性"].ffill()
        df = df.fillna(value='')
        df['特性一级分类'] = df['特性一级分类'].astype(str) 
        columns_to_iterate = [col for col in df.columns if col not in ['ID', '编号', '领域', '特性一级分类', '特性二级分类', '特性', '子特性']]

        # 数据库操作
        for _, row in df.iterrows():
            for columns in columns_to_iterate:
                table_dict = dict()
                # 假设 Excel 表头与数据库字段名一致
                table_dict['feature_first_classification'] = row["特性一级分类"] if "特性一级分类" in row else '' 
                table_dict['feature_second_classification'] = row["特性二级分类"] if "特性二级分类" in row else '' 
                table_dict['feature_name'] = row["特性"] if "特性" in row else '' 
                table_dict['children_feature_name'] = str(row["子特性"] if "子特性" in row else '' )
                table_dict['related_board_model'] = columns
                if type(row[columns]) is bool:
                    if row[columns]:
                        table_dict['related_flag'] = '2'
                    else:
                        table_dict['related_flag'] = '0'
                elif type(row[columns]) is str:
                    if row[columns].upper() == 'TRUE':
                        table_dict['related_flag'] = '2'
                    elif row[columns].upper() == 'FALSE':
                        table_dict['related_flag'] = '0'
                    else:
                        table_dict['related_flag'] = row[columns]
                else:
                    table_dict['related_flag'] = str(row[columns])
            
                db_factor_values = db.session.query(FEATURE_BOARD_RELATION_TABLE).filter(and_(FEATURE_BOARD_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                                          FEATURE_BOARD_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.related_board_model == table_dict["related_board_model"]
                                                                          )).all()
                if len(db_factor_values) > 0 and row["特性一级分类"] and row["特性二级分类"] and row["特性"] and table_dict['related_board_model']:
                    update_sql = update(FEATURE_BOARD_RELATION_TABLE).where(and_(FEATURE_BOARD_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                                          FEATURE_BOARD_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"],
                                                                                          FEATURE_BOARD_RELATION_TABLE.related_board_model == table_dict["related_board_model"])
                                                                          ).values(related_flag=table_dict['related_flag'], current_status=check_update,
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                    db.session.execute(update_sql)
                else:
                    insert_sql = insert(FEATURE_BOARD_RELATION_TABLE).values(feature_first_classification=table_dict['feature_first_classification'], feature_second_classification=table_dict['feature_second_classification'], 
                                                                                  feature_name=table_dict["feature_name"], children_feature_name=table_dict["children_feature_name"], 

                                                                related_board_model=table_dict["related_board_model"], related_flag=table_dict['related_flag'], current_status=check_add,  create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                    db.session.execute(insert_sql)
                    # 创建新用户 
        db.session.commit()

        db.session.refresh(db.session.query(FEATURE_BOARD_RELATION_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")
    