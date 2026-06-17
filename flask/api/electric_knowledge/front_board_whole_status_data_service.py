from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union, Dict, Any  # 始终导入这些类型
import json
import copy
import pandas as pd
from collections import defaultdict

from electric_knowledge.data_model import db, BOARD_WHOLE_STATUS_TABLE, BOARD_CHANGE_ANALYSIS_TABLE
from flask import request, jsonify
from electric_knowledge.utils_pub import pub_get_employ_name, deduplicate_list_by_keys
from electric_knowledge.utils_rdc import update_RDC_by_key
from electric_knowledge.utils_icenter import find_string_in_column, classify_feature, extract_target
from electric_knowledge.front_old_children_feature_data_service import querySrcOldChildrenFeatureDataByParams
from electric_knowledge.front_feature_board_relation_data_service import querySrcFeatureBoardRelation
import logging

logger = logging.getLogger("Logger")


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BaseBoardWholeStatusData(BaseModel):
    id: Optional[str] = None
    board_name: Optional[str] = Field(None, alias="board")
    product_factor_value: Optional[str] = Field(None, alias="product")
    board_type_factor_value: Optional[str] = Field(None, alias="boardType")
    board_service_model_factor_values: Optional[str] = Field(None, alias="boardBusinessModel")
    feature_name: Optional[str] = Field(None, alias="feature")
    children_feature_name: Optional[str] = Field(None, alias="subFeature")
    parent: Optional[str] = None
    change_analysis: Optional[str] = Field(None, alias="changeAnalysis")
    milestone: Optional[str] = Field(None, alias="mileStone")
    related_rdc: Optional[str] = Field(None, alias="rdcIdent")
    related_rdc_title: Optional[str] = Field(None, alias="rdcTitle")
    related_requirement_preplanning_version: Optional[str] = Field(None, alias="requirementPrePlanVersion")
    related_requirement_status: Optional[str] = Field(None, alias="requirementStatus")
    related_parent_rdc: Optional[str] = Field(None, alias="parentNodeRdc")
    development_type: Optional[str] = Field(None, alias="developmentType")
    reusedegree: Optional[str] = Field(None, alias="reuseDegree")
    current_status: Optional[str] = Field(None, alias="status")
    related_fault_num: Optional[int] = None
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

# 业务模型-单板全局状态
def queryBoardGlobalStatusTree():    # 构建基础查询
    """
    查询全部单板全局状态取值记录（树形结构）
    ---
    tags:
      - 单板全局状态
    description: 查询全部单板全局状态取值记录（树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [
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
    conditions = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseBoardWholeStatusData = BaseBoardWholeStatusData(**query_params)
    
    query0 = db.session.query(BOARD_WHOLE_STATUS_TABLE.product_factor_value, BOARD_WHOLE_STATUS_TABLE.milestone, BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values).group_by(BOARD_WHOLE_STATUS_TABLE.product_factor_value, BOARD_WHOLE_STATUS_TABLE.milestone, BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values).order_by(BOARD_WHOLE_STATUS_TABLE.product_factor_value, BOARD_WHOLE_STATUS_TABLE.milestone, BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values)
    baseBoardWholeStatusDatas = query0.all()
    
    result = []
    current_level1 = None
    current_level2 = None
    current_level3 = None

    for data in baseBoardWholeStatusDatas:
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
        
        # 处理第四层（叶子节点）
        if level4 is not None and level4 != "":
            if 'children' not in current_level3:
                current_level3['children'] = []
            current_level3['children'].append({
                'label': level4,
                'value': level4
            })

    # 添加最后一个节点到结果
    if current_level3 is not None:
        current_level2['children'].append(copy.deepcopy(current_level3))
    if current_level2 is not None:
        current_level1['children'].append(copy.deepcopy(current_level2))
    if current_level1 is not None:
        result.append(copy.deepcopy(current_level1))

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


# 业务模型-单板全局状态
def querySimpleBoardGlobalStatusTree():
    """
    查询全部单板全局状态取值记录（简化版-树形结构）
    ---
    tags:
      - 单板全局状态
    description: 查询全部单板全局状态取值记录（简化版-树形结构）
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": {
             "19700产品": {
                "板卡类型1": {
                    "单板业务模型1": ["单板标识因子1", "单板标识因子2"],
                    "单板业务模型2": ["单板标识因子3", "单板标识因子4"]
                },
                "板卡类型2": {
                    "单板业务模型3": ["单板标识因子5", "单板标识因子6"],
                    "单板业务模型4":  ["单板标识因子7", "单板标识因子8"]
                }
            },
            "M721产品": {
                "M721产品_板卡类型1": {
                    "M721产品_单板业务模型1": ["M721产品_单板标识因子1", "M721产品_单板标识因子2"],
                    "M721产品_单板业务模型2": ["M721产品_单板标识因子3", "M721产品_单板标识因子4"]
                },
                "M721产品_板卡类型2": {
                    "M721产品_单板业务模型3": ["M721产品_单板标识因子5", "M721产品_单板标识因子6"],
                    "M721产品_单板业务模型4": ["M721产品_单板标识因子7", "M721产品_单板标识因子8"]
                }
            }
        }
    }
    """
    # 1. 构建查询条件
    conditions = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseBoardWholeStatusData = BaseBoardWholeStatusData(**query_params)

    # 2. 执行查询
    query0 = db.session.query(
        BOARD_WHOLE_STATUS_TABLE.product_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_type_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values,
        BOARD_WHOLE_STATUS_TABLE.board_name
    ).filter(
        *conditions
    ).group_by(
        BOARD_WHOLE_STATUS_TABLE.product_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_type_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values,
        BOARD_WHOLE_STATUS_TABLE.board_name
    ).order_by(
        BOARD_WHOLE_STATUS_TABLE.product_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_type_factor_value,
        BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values,
        BOARD_WHOLE_STATUS_TABLE.board_name
    )
    baseBoardWholeStatusDatas = query0.all()

    # 3. 构建嵌套字典结构
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in baseBoardWholeStatusDatas:
        product = normalize_comma_separated(row[0])
        board_type = normalize_comma_separated(row[1])
        service_model = normalize_comma_separated(row[2])
        board_name = row[3]

        if board_name:  # 仅当 board_name 非空时添加
            tree[product][board_type][service_model].append(board_name)

    # 4. 转为普通 dict
    def to_dict(d):
        if isinstance(d, defaultdict):
            return {k: to_dict(v) for k, v in d.items()}
        return d
    result = to_dict(tree)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})


def normalize_comma_separated(value):
    """对逗号分隔的字符串进行拆分、去重、排序、重连"""
    if not value or not isinstance(value, str):
        return value
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return ""
    # 去重 + 排序（升序）
    unique_sorted = sorted(set(parts))
    return ",".join(unique_sorted)


def queryBoardGlobalStatusRdcFilterDataDict():
    """
    查询指定的特性-子特性-RDC标识-需求状态取值
    ---
    tags:
      - 单板全局状态
    description: 查询指定的特性-子特性-RDC标识-需求状态取值
    parameters:
      - name: board
        in: query
        description: 单板标识
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
          "code": 200,
          "status": "success",
          "message": "获取成功",
          "data": {
            "feature": [
              {
                "label": "F010220-灰光业务维护管理特性",
                "value": "F010220-灰光业务维护管理特性",
                "children": [
                  {
                    "label": "FS010220-01-灰光模块-核心模块复位",
                    "value": "FS010220-01-灰光模块-核心模块复位"
                  },
                  {
                    "label": "FS010220-02-灰光模块-模块热插拔管理",
                    "value": "FS010220-02-灰光模块-模块热插拔管理"
                  }
                ]
              },
              {
                "label": "F020101-O业务基础特性",
                "value": "F020101-O业务基础特性",
                "children": [
                  {
                    "label": "FS020101-11-odu->flex-o业务(FLEXOoO-C卡)",
                    "value": "FS020101-11-odu->flex-o业务(FLEXOoO-C卡)"
                  },
                  {
                    "label": "FS020101-12-flex-o业务端口绑定",
                    "value": "FS020101-12-flex-o业务端口绑定"
                  }
                ]
              }
            ],
            "rdcIdent": [
              "xx1",
              "xx3",
              "xx2",
              "xx4"
            ],
            "requirementStatus": [
              "新建"
            ],
            "status": [
              "审核中-修改",
              "审核中-新增"
            ],
            "requirementPreplanningVersion": [
              "待规划版本",
              "智能OTN V2.00R7",
              "智能OTN V2.00R8P01",
              "智能OTN V3.00R2"
            ]
          }
        }
    """
    # 构建基础查询条件
    base_conditions = [
        BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y',
        BOARD_WHOLE_STATUS_TABLE.feature_name.is_not(None)
    ]

    try:
        # 解析查询参数
        query_params = request.args.to_dict()
        base_data = BaseBoardWholeStatusData(**query_params)

        # 动态添加过滤条件
        filters = base_conditions.copy()

        if not base_data.board_name:
            final_result = {
                "feature": [],
                "rdcIdent": [],
                "requirementStatus": [],
                "status": [],
                "requirementPreplanningVersion": []
            }
            return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": final_result})

        if base_data.board_name:
            board_list = [b.strip() for b in base_data.board_name.split(',') if b.strip()]
            if board_list:
                filters.append(BOARD_WHOLE_STATUS_TABLE.board_name.in_(board_list))

        # 第一次查询：获取相关枚举值字段
        enum_fields = db.session.query(
            BOARD_WHOLE_STATUS_TABLE.related_rdc,
            BOARD_WHOLE_STATUS_TABLE.related_requirement_status,
            BOARD_WHOLE_STATUS_TABLE.current_status,
            BOARD_WHOLE_STATUS_TABLE.related_requirement_preplanning_version
        ).filter(and_(*filters)).all()

        rdc_idents = {item.related_rdc for item in enum_fields if item.related_rdc}
        req_statuses = {item.related_requirement_status for item in enum_fields if item.related_requirement_status}
        statuses = {item.current_status for item in enum_fields if item.current_status}
        preplan_versions = {item.related_requirement_preplanning_version for item in enum_fields if item.related_requirement_preplanning_version}

        # 第二次查询：获取 feature_name 与 children_feature_name（注意：不能复用 filters，因需额外条件）
        feature_conditions = base_conditions.copy()
        if base_data.board_name:
            feature_conditions.append(BOARD_WHOLE_STATUS_TABLE.board_name.in_(board_list))
        feature_conditions.append(BOARD_WHOLE_STATUS_TABLE.children_feature_name.is_not(None))
        feature_conditions.append(BOARD_WHOLE_STATUS_TABLE.children_feature_name != "")

        feature_data = db.session.query(
            BOARD_WHOLE_STATUS_TABLE.feature_name,
            BOARD_WHOLE_STATUS_TABLE.children_feature_name
        ).filter(and_(*feature_conditions)) \
         .group_by(BOARD_WHOLE_STATUS_TABLE.feature_name, BOARD_WHOLE_STATUS_TABLE.children_feature_name) \
         .order_by(BOARD_WHOLE_STATUS_TABLE.feature_name, BOARD_WHOLE_STATUS_TABLE.children_feature_name) \
         .all()

        # 构建嵌套结构
        results = []
        current_parent = None

        for feat_name, child_name in feature_data:
            if current_parent is None or current_parent['label'] != feat_name:
                if current_parent is not None:
                    results.append(copy.deepcopy(current_parent))
                current_parent = {
                    'label': feat_name,
                    'value': feat_name,
                    'children': []
                }

            # 添加子节点（确保非空且非空白）
            if child_name and child_name.strip():
                current_parent['children'].append({
                    'label': child_name,
                    'value': child_name
                })

        if current_parent is not None:
            results.append(copy.deepcopy(current_parent))

        final_result = {
            "feature": results,
            "rdcIdent": list(rdc_idents),
            "requirementStatus": list(req_statuses),
            "status": list(statuses),
            "requirementPreplanningVersion": list(preplan_versions)
        }
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": final_result})

    except Exception as e:
        return jsonify({"code": 400, "status": "error", "message": "获取失败", "data": {}})


def isBoardWholeStatusRDCByParams(query_params:dict={}):    # 构建基础查询

    conditions = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y']
    baseBoardWholeStatusData = BaseBoardWholeStatusData(**query_params)
    if baseBoardWholeStatusData.board_name:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_name.in_(baseBoardWholeStatusData.board_name.split(',')))
    if baseBoardWholeStatusData.product_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.product_factor_value.in_(baseBoardWholeStatusData.product_factor_value.split(',')))
    if baseBoardWholeStatusData.board_type_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_type_factor_value.in_(baseBoardWholeStatusData.board_type_factor_value.split(',')))
    if baseBoardWholeStatusData.board_service_model_factor_values:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values.in_(baseBoardWholeStatusData.board_service_model_factor_values.split(',')))
    feature_list = []
    if baseBoardWholeStatusData.feature_name:
        feature_list = baseBoardWholeStatusData.feature_name.split(',')
        feature_conditions = [BOARD_WHOLE_STATUS_TABLE.feature_name.like(f"%{term}%") for term in feature_list if term is not None and term.strip() != '']
        conditions.append(or_(*feature_conditions))

    if baseBoardWholeStatusData.children_feature_name:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.children_feature_name.in_(baseBoardWholeStatusData.children_feature_name.split(',')))
    related_rdc_list = []
    if baseBoardWholeStatusData.related_rdc:
        related_rdc_list.append(baseBoardWholeStatusData.related_rdc.split(','))
    if baseBoardWholeStatusData.related_requirement_status:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.related_requirement_status.in_(baseBoardWholeStatusData.related_requirement_status.split(',')))
    if baseBoardWholeStatusData.current_status:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.current_status.in_(baseBoardWholeStatusData.current_status.split(',')))
    if baseBoardWholeStatusData.operator_person:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.operator_person == baseBoardWholeStatusData.operator_person)
    try:
        baseBoardWholeStatusDatas = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(*conditions)).all()
        if len(baseBoardWholeStatusDatas) > 0:
            isFlag = True
        else:
            isFlag = False
    except Exception as e:
        isFlag = False
    return isFlag


def querySrcBoardWholeStatusByParams(query_params: dict = {}, markdown_flag: bool = False):
    query_params = query_params or {}
    base_data = BaseBoardWholeStatusData(**query_params)
    Board = BOARD_WHOLE_STATUS_TABLE

    # === 1. 构建基础查询条件 ===
    conditions = [Board.effective_flag == 'Y']

    def add_equal(field_value: str, column):
        if field_value:
            conditions.append(column == field_value)

    def add_in(field_value: str, column):
        if field_value:
            values = [v.strip() for v in field_value.split(',') if v.strip()]
            if values:
                conditions.append(column.in_(values))

    add_equal(base_data.operator_person, Board.operator_person)
    add_in(base_data.product_factor_value, Board.product_factor_value)
    add_in(base_data.board_type_factor_value, Board.board_type_factor_value)
    add_in(base_data.board_service_model_factor_values, Board.board_service_model_factor_values)
    add_in(base_data.current_status, Board.current_status)

    # === 2. 处理 board_name 智能匹配 ===
    board_name_filter_applied = False
    board_name_condition = None
    if base_data.board_name:
        board_name_filter_applied = True
        src_boards = [b.strip() for b in base_data.board_name.split(',') if b.strip()]

        # 构建“去括号后”的字段表达式（用于模糊匹配）
        reversed_name = func.reverse(Board.board_name)
        last_paren_pos = func.locate('(', reversed_name)
        split_result = case(
            (last_paren_pos > 0,
            func.left(Board.board_name, func.length(Board.board_name) - last_paren_pos + 1)),
            else_=Board.board_name
        )

        # 模糊匹配：split_result LIKE '%b%'
        like_conditions = [split_result.like(f'%{b}%') for b in src_boards]
        # 精确匹配：board_name == 'b'
        eq_conditions = [Board.board_name == b for b in src_boards]

        # 合并所有条件：只要满足任一（模糊或精确）即匹配
        board_name_condition = or_(*like_conditions, *eq_conditions)
        conditions.append(board_name_condition)

    # === 3. 提取过滤字段（避免重复 split）===
    feature_list = board_whole_status_split_csv(base_data.feature_name)
    children_feature_list = board_whole_status_split_csv(base_data.children_feature_name)
    rdc_list = board_whole_status_split_csv(base_data.related_rdc)
    req_status_list = board_whole_status_split_csv(base_data.related_requirement_status)
    preplan_version_list = board_whole_status_split_csv(base_data.related_requirement_preplanning_version)

    # === 4. 构建主查询 ===
    main_query = db.session.query(Board).filter(and_(*conditions))

    if markdown_flag:
        # Markdown 模式：直接按字段 in 过滤
        extra_conds = []
        if feature_list:
            extra_conds.append(Board.feature_name.in_(feature_list))
        if children_feature_list:
            extra_conds.append(Board.children_feature_name.in_(children_feature_list))
        if rdc_list:
            extra_conds.append(Board.related_rdc.in_(rdc_list))
        if req_status_list:
            extra_conds.append(Board.related_requirement_status.in_(req_status_list))

        data = main_query.filter(and_(*extra_conds)).order_by(
            Board.board_service_model_factor_values,
            Board.feature_name,
            Board.children_feature_name,
            Board.parent.desc()
        ).all()

        results = [BaseBoardWholeStatusData.model_validate(item).model_dump(by_alias=True) for item in data]
        return results

    # === 5. 非 Markdown 模式：反向查询 + 精确匹配 ===
    final_features = feature_list
    final_children = children_feature_list

    need_backfill = (preplan_version_list or rdc_list or req_status_list)
    if need_backfill and board_name_filter_applied:
        # 构建反向查询条件
        backfill_conds = [Board.effective_flag == 'Y']
        if board_name_condition is not None:
            backfill_conds.append(board_name_condition)
        if preplan_version_list:
            backfill_conds.append(Board.related_requirement_preplanning_version.in_(preplan_version_list))
        if rdc_list:
            backfill_conds.append(Board.related_rdc.in_(rdc_list))
        if req_status_list:
            backfill_conds.append(Board.related_requirement_status.in_(req_status_list))

        backfill_results = db.session.query(
            Board.feature_name,
            Board.children_feature_name
        ).filter(and_(*backfill_conds)).distinct().all()

        backfill_features = {row.feature_name for row in backfill_results if row.feature_name}
        backfill_children = {row.children_feature_name for row in backfill_results if row.children_feature_name}

        if feature_list or children_feature_list:
            final_features = [f for f in feature_list if f in backfill_features]
            final_children = [c for c in children_feature_list if c in backfill_children]
        else:
            final_features = list(backfill_features)
            final_children = list(backfill_children)

    # === 6. 构建非 Markdown 的 feature/children 匹配条件 ===
    extra_conds = []
    if base_data.feature_name or base_data.children_feature_name or base_data.related_rdc or base_data.related_requirement_status or base_data.related_requirement_preplanning_version:
        allowed_condition = or_(
            and_(
                Board.feature_name.in_(final_features),
                (Board.children_feature_name.is_(None)) | (Board.children_feature_name == '')
            ),
            and_(
                (Board.feature_name.is_(None)) | (Board.feature_name == ''),
                (Board.children_feature_name.is_(None)) | (Board.children_feature_name == '')
            ),
            and_(
                Board.feature_name.in_(final_features),
                Board.children_feature_name.in_(final_children)
            )
        )
        extra_conds.append(allowed_condition)

    data = main_query.filter(and_(*extra_conds)).order_by(
        Board.product_factor_value,
        Board.board_type_factor_value,
        Board.board_service_model_factor_values,
        Board.board_name,
        Board.feature_name,
        Board.children_feature_name,
        Board.related_rdc,
        Board.parent.desc()
    ).all()

    results = [BaseBoardWholeStatusData.model_validate(item).model_dump(by_alias=True) for item in data]

    # === 7. 构建树形结构（使用 final_* 过滤列表！）===
    return board_whole_status_build_hierarchy_tree(results, final_features, final_children, rdc_list, req_status_list, preplan_version_list), 200


def board_whole_status_split_csv(s):
    if not s:
        return []
    return [v.strip() for v in s.split(',') if v.strip()]


def board_whole_status_build_hierarchy_tree(results, feature_filter, children_filter, rdc_filter, req_status_filter, preplan_version_filter):
    level1 = None
    level2 = None
    level3 = None
    final = []

    for item in results:
        parent = item.get('parent')
        if not parent:
            continue

        if parent == '3':  # Level 1 root
            board_whole_status_flush_levels(level3, level2, level1, final)
            level1 = board_whole_status_reset_level(3, item)
            level2 = level3 = None

        elif parent == '2':  # Feature level
            if level3 is not None:
                level2.setdefault('childrenList', []).append(level3)
                level3 = None

            # Flush previous feature if it exists and is different
            if level2 is not None and level2.get('feature') != item['feature']:
                level1.setdefault('childrenList', []).append(level2)
                level2 = None

            if feature_filter and item['feature'] not in feature_filter:
                continue

            level2 = board_whole_status_reset_level(2, item)

        elif parent == '1':  # Sub-feature level
            if level3 is not None and level3.get('subFeature') != item['subFeature']:
                level2.setdefault('childrenList', []).append(level3)
                level3 = None

            if children_filter and item['subFeature'] not in children_filter:
                continue

            level3 = board_whole_status_reset_level(1, item)

        elif parent == '0':  # Leaf node (RDC)
            if (rdc_filter and item['rdcIdent'] not in rdc_filter) or \
               (req_status_filter and item['requirementStatus'] not in req_status_filter) or \
               (preplan_version_filter and item['requirementPrePlanVersion'] not in preplan_version_filter):
                continue
            leaf = board_whole_status_reset_level(0, item)
            if level3 is None:
                # 防御性：理论上 level3 应已存在，但以防万一
                continue
            level3.setdefault('childrenList', []).append(leaf)

    # Flush remaining
    board_whole_status_flush_levels(level3, level2, level1, final)
    return final


def board_whole_status_flush_levels(level3, level2, level1, final_list):
    if level3 is not None:
        level2.setdefault('childrenList', []).append(level3)
    if level2 is not None:
        level1.setdefault('childrenList', []).append(level2)
    if level1 is not None:
        final_list.append(level1)


def board_whole_status_reset_level(level, src):
    d = copy.deepcopy(src)
    if level == 3:
        for k in ['changeAnalysis', 'rdcIdent', 'requirementPrePlanVersion', 'requirementStatus', 'parentNodeRdc']:
            d[k] = ''
        d['feature'] = '所有支持的特性/子特性'
        d['childrenList'] = []
    elif level == 2:
        for k in ['board', 'product', 'boardType', 'boardBusinessModel', 'boardIdent',
                  'rdcIdent', 'requirementPrePlanVersion', 'requirementStatus', 'parentNodeRdc']:
            d[k] = ''
        d['childrenList'] = []
    elif level == 1:
        for k in ['board', 'product', 'boardType', 'boardBusinessModel', 'boardIdent',
                  'rdcIdent', 'requirementPrePlanVersion', 'requirementStatus', 'parentNodeRdc']:
            d[k] = ''
        d['feature'] = d.get('subFeature', '')
        d['childrenList'] = []
    elif level == 0:
        for k in ['board', 'product', 'boardType', 'boardBusinessModel', 'boardIdent', 'feature', 'changeAnalysis']:
            d[k] = ''
        d['rdcProblemNum'] = '1'
    return d

def querySrcBoardWholeStatusRDCByParams(query_params:dict={}, markdown_flag:bool=False):    # 构建基础查询

    conditions = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y',
                  BOARD_WHOLE_STATUS_TABLE.related_rdc.is_not(None),
                  BOARD_WHOLE_STATUS_TABLE.related_rdc != '']
    baseBoardWholeStatusData = BaseBoardWholeStatusData(**query_params)
    if baseBoardWholeStatusData.board_name:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_name.in_(baseBoardWholeStatusData.board_name.split(',')))
    if baseBoardWholeStatusData.product_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.product_factor_value.in_(baseBoardWholeStatusData.product_factor_value.split(',')))
    if baseBoardWholeStatusData.board_type_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_type_factor_value.in_(baseBoardWholeStatusData.board_type_factor_value.split(',')))
    if baseBoardWholeStatusData.board_service_model_factor_values:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values.in_(baseBoardWholeStatusData.board_service_model_factor_values.split(',')))
    if baseBoardWholeStatusData.feature_name:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.feature_name.in_(baseBoardWholeStatusData.feature_name.split(',')))
    if baseBoardWholeStatusData.children_feature_name:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.children_feature_name.in_(baseBoardWholeStatusData.children_feature_name.split(',')))
    if baseBoardWholeStatusData.related_rdc:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.related_rdc.in_(baseBoardWholeStatusData.related_rdc.split(',')))
    if baseBoardWholeStatusData.related_requirement_status:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.related_requirement_status.in_(baseBoardWholeStatusData.related_requirement_status.split(',')))
    if baseBoardWholeStatusData.current_status:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.current_status.in_(baseBoardWholeStatusData.current_status.split(',')))
    # operator_person = request.args.get('operator_person')
    if baseBoardWholeStatusData.operator_person:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.operator_person == baseBoardWholeStatusData.operator_person)
    
    try:
        query = db.session.query(BOARD_WHOLE_STATUS_TABLE) \
        .filter(and_(*conditions)).order_by(BOARD_WHOLE_STATUS_TABLE.product_factor_value, BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, BOARD_WHOLE_STATUS_TABLE.board_name,  BOARD_WHOLE_STATUS_TABLE.feature_name, 
                                             BOARD_WHOLE_STATUS_TABLE.children_feature_name, BOARD_WHOLE_STATUS_TABLE.related_rdc, BOARD_WHOLE_STATUS_TABLE.parent)
        baseBoardWholeStatusDatas = query.all()
        results = [
            BaseBoardWholeStatusData.model_validate(item).model_dump(by_alias=True)
            for item in baseBoardWholeStatusDatas
        ]
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        return ([], 400)
    
def queryBoardGlobalStatusByParams():    # 构建基础查询
    """
    查询全部单板全局状态取值记录
    ---
    tags:
      - 单板全局状态
    description: 查询全部单板全局状态取值记录
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            board:
              type: string
              description: 单板标识
            product:
              type: string
              description: 产品因子取值
            boardType:
              type: string
              description: 板卡类型因子取值
            boardBusinessModel:
              type: string
              description: 单板业务模型因子取值
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            status:
              type: string
              description: 当前状态
            rdcIdent:
              type: string
              description: RDC标识
            requirementStatus:
              type: string
              description: 需求状态
            related_fault_num:
              type: string
              description: 关联故障数
          example:   # 示例值
            board: "M4C4R(80A7H)"
            product: "19700产品"
            boardType: "客户侧C卡"
            boardBusinessModel: "C_O"
            feature: "F010220-灰光业务维护管理特性"
            subFeature: "FS010220-01-灰光模块-核心模块复位"
            status: "xx"
            rdcIdent: "xx"
            requirementStatus: "xx"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    query_params = request.get_json()
    results, code = querySrcBoardWholeStatusByParams(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})
    
def queryBoardGlobalStatusBoardList():    # 构建基础查询
    """
    查询单板全局状态单板取值列表
    ---
    tags:
      - 单板全局状态
    description: 查询单板全局状态单板取值列表
    parameters:
      - name: board
        in: query
        description: 单板名称
        required: false
        type: string
      - name: product
        in: query
        description: 产品因子取值
        required: false
        type: string
      - name: boardType
        in: query
        description: 板卡类型因子取值
        required: false
        type: string
      - name: boardBusinessModel
        in: query
        description: 单板业务模型因子取值
        required: false
        type: string
      - name: milestone
        in: query
        description: 里程碑
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
           '11', '22'
          ]}
    """
    conditions = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    baseBoardWholeStatusData = BaseBoardWholeStatusData(**query_params)
    if baseBoardWholeStatusData.product_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.product_factor_value.in_(baseBoardWholeStatusData.product_factor_value.split(',')))
    if baseBoardWholeStatusData.milestone:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.milestone.in_(baseBoardWholeStatusData.milestone.split(',')))    
    if baseBoardWholeStatusData.board_type_factor_value:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_type_factor_value.in_(baseBoardWholeStatusData.board_type_factor_value.split(',')))
    if baseBoardWholeStatusData.board_service_model_factor_values:
        conditions.append(BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values.in_(baseBoardWholeStatusData.board_service_model_factor_values.split(',')))
    # 构建查询
    query = db.session.query(BOARD_WHOLE_STATUS_TABLE.board_name).filter(and_(*conditions)).group_by(BOARD_WHOLE_STATUS_TABLE.board_name)
    # 动态添加过滤条件
    # 执行查询
    baseBaseBoardWholeStatusDatas = query.all()
    result = []
    for baseBaseBoardWholeStatusData in baseBaseBoardWholeStatusDatas:
        result.append(baseBaseBoardWholeStatusData[0])

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})

def addSrcBoardWholeStatusData(body_params_list:list, employ_no:str):
    new_operator_person = pub_get_employ_name(employ_no)
    # 提取参数
    
    board_flag = False
    feature_flag = False
    children_feature_flag = False
    rdc_flag = False
    pre_board_name = ''
    pre_feature_name = ''
    pre_children_feature_name = ''
    pre_related_rdc = ''
    for body_params in body_params_list:
        baseBoardWholeStatusData = BaseBoardWholeStatusData(**body_params)
        board_name = baseBoardWholeStatusData.board_name if baseBoardWholeStatusData.board_name else ''
        product_factor_value = baseBoardWholeStatusData.product_factor_value if baseBoardWholeStatusData.product_factor_value else ''
        board_type_factor_value = baseBoardWholeStatusData.board_type_factor_value if baseBoardWholeStatusData.board_type_factor_value else ''
        board_service_model_factor_values = baseBoardWholeStatusData.board_service_model_factor_values if baseBoardWholeStatusData.board_service_model_factor_values else ''
        feature_name = baseBoardWholeStatusData.feature_name if baseBoardWholeStatusData.feature_name else ''
        children_feature_name = baseBoardWholeStatusData.children_feature_name if baseBoardWholeStatusData.children_feature_name else ''
        parent = str(baseBoardWholeStatusData.parent) if baseBoardWholeStatusData.parent else '0'
        change_analysis = baseBoardWholeStatusData.change_analysis if baseBoardWholeStatusData.change_analysis else ''
        milestone = baseBoardWholeStatusData.milestone if baseBoardWholeStatusData.milestone else ''
        related_rdc = baseBoardWholeStatusData.related_rdc if baseBoardWholeStatusData.related_rdc else ''
        related_rdc_title = baseBoardWholeStatusData.related_rdc_title if baseBoardWholeStatusData.related_rdc_title else ''
        related_requirement_preplanning_version = baseBoardWholeStatusData.related_requirement_preplanning_version if baseBoardWholeStatusData.related_requirement_preplanning_version else ''
        related_requirement_status = baseBoardWholeStatusData.related_requirement_status if baseBoardWholeStatusData.related_requirement_status else ''
        related_parent_rdc = baseBoardWholeStatusData.related_parent_rdc if baseBoardWholeStatusData.related_parent_rdc else ''
       
        # 检查新增的数据在数据表中是否已存在
        db_board_whole_status_values = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name,
                                                        BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc
                                                                      )).all()
        if len(db_board_whole_status_values) > 0:
            logger.info(f"----------子特性：{children_feature_name} 和rdc编号：{related_rdc} 已存在，先删除后新增")
            db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name,
                                                                    BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc
                                                                      )).delete()
            db.session.commit()
        
        if board_name and (board_name != pre_board_name):
            db_board_whole_status_values = db.session.query(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name, 
                                                                                                    BOARD_WHOLE_STATUS_TABLE.parent == '3')).group_by(
                                                    BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone
                                                    ).all()
            if len(db_board_whole_status_values) < 1:
                insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=product_factor_value, 
                                                        board_type_factor_value=board_type_factor_value, board_service_model_factor_values=board_service_model_factor_values, 
                                                         parent='3', milestone = milestone,
                                                            current_status=check_add,create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')

                db.session.execute(insert_sql)
                board_flag = True
            else:
                board_flag = True
            pre_board_name = board_name
        
        # 新增特性子特性
        if feature_name and (feature_name != pre_feature_name):
            db_board_whole_status_values = db.session.query(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name,
                                                                                               BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name,
                                                                                               BOARD_WHOLE_STATUS_TABLE.parent == '2'
                                                                                               )).group_by(
                                                        BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone
                                                    ).all()
            if len(db_board_whole_status_values) < 1:
                insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=product_factor_value, 
                                                        board_type_factor_value=board_type_factor_value, board_service_model_factor_values=board_service_model_factor_values, feature_name=feature_name, 
                                                        parent='2', change_analysis = change_analysis, milestone = milestone,
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
               
                feature_flag = True
            else:
                feature_flag = True
            pre_feature_name = feature_name 
        
        # 新增特性子特性
        if children_feature_name and (children_feature_name != pre_children_feature_name):
            db_board_whole_status_values = db.session.query(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name,
                                                                                               BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name,
                                                                                               BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name,
                                                                                               BOARD_WHOLE_STATUS_TABLE.parent == '1')).group_by(
                                                        BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                    BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, 
                                                    BOARD_WHOLE_STATUS_TABLE.milestone
                                                    ).all()
            if len(db_board_whole_status_values) < 1:
                insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=product_factor_value, 
                                                    board_type_factor_value=board_type_factor_value, board_service_model_factor_values=board_service_model_factor_values, feature_name=feature_name, 
                                                    children_feature_name=children_feature_name, parent='1', 
                                                    milestone = milestone,
                                                        current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                children_feature_flag = True
            else:
                children_feature_flag = True
            pre_children_feature_name = children_feature_name 
        
        # 新增rdc
        if related_rdc and (related_rdc != pre_related_rdc):
            db_board_whole_status_values = db.session.query(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                        BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, BOARD_WHOLE_STATUS_TABLE.feature_name,
                                                        BOARD_WHOLE_STATUS_TABLE.milestone
                                                        ).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name,
                                                                      BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc
                                                                      )).group_by(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.product_factor_value,
                                                        BOARD_WHOLE_STATUS_TABLE.board_type_factor_value, BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values, BOARD_WHOLE_STATUS_TABLE.feature_name, BOARD_WHOLE_STATUS_TABLE.milestone).all()
            if len(db_board_whole_status_values) < 1:
                insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=product_factor_value, 
                                                        board_type_factor_value=board_type_factor_value, board_service_model_factor_values=board_service_model_factor_values, feature_name=feature_name, 
                                                        children_feature_name=children_feature_name, parent='0', 
                                                        milestone = milestone,related_rdc=related_rdc, related_rdc_title=related_rdc_title, related_requirement_preplanning_version=related_requirement_preplanning_version,
                                                        related_requirement_status=related_requirement_status,related_parent_rdc=related_parent_rdc,
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')

                db.session.execute(insert_sql) 
                rdc_flag = True
            else:
                rdc_flag = True
            pre_related_rdc = related_rdc        
                  
        db.session.commit()
      
        #     # 创建新用户
    db.session.refresh(db.session.query(BOARD_WHOLE_STATUS_TABLE).first())
    return 200

def addBoardWholeStatusData():
    """
    新增单板全局状态单板取值记录
    ---
    tags:
      - 单板全局状态
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
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
            product:
              type: string
              description: 产品因子取值
            boardType:
              type: string
              description: 板卡类型因子取值
            boardBusinessModel:
              type: string
              description: 单板业务模型因子取值
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            parent:
              type: string
              description: 是否父级特性
            changeAnalysis:
              type: string
              description: 变更分析
            milestone:
              type: string
              description: 里程碑
            rdcIdent:
              type: string
              description: 子特性关联RDC标识
            rdcTitle:
              type: string
              description: 子特性关联RDC标题
            requirementPrePlanVersion:
              type: string
              description: 子特性关联需求预规划版本
            requirementStatus:
              type: string
              description: 子特性关联需求状态
            parentNodeRdc:
              type: string
              description: 关联父节点RDC
          example:   # 示例值
            board: "光层业务"
            product: "灰光业务"
            boardType: "F010102-灰光业务基础特性"
            boardBusinessModel: "xx"
            feature: "xx"
            subFeature: "xx"
            parent: "光层业务"
            changeAnalysis: "灰光业务"
            milestone: "F010102-灰光业务基础特性"
            rdcIdent: "xx"
            rdcTitle: "xx"
            requirementPrePlanVersion: "xx"
            requirementStatus: "xx"
            parentNodeRdc: "xx"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    code = addSrcBoardWholeStatusData([body_params], employ_no)
    message = "新增成功"
    return {"code": code, "status": "success", "message": message, "data": []}

def updateSrcBoardWholeStatusData(body_params_list:list,employ_no:str):
    new_operator_person = pub_get_employ_name(employ_no)
    id_list = []
    feature_name_list = []
    children_feature_name_list = []
    related_rdc_list = []
    for body_params in body_params_list:
        baseBoardWholeStatusData = BaseBoardWholeStatusData(**body_params)
        # 提取参数
        id = baseBoardWholeStatusData.id
        board_name = baseBoardWholeStatusData.board_name
        product_factor_value = baseBoardWholeStatusData.product_factor_value
        board_type_factor_value = baseBoardWholeStatusData.board_type_factor_value
        board_service_model_factor_values = baseBoardWholeStatusData.board_service_model_factor_values
        change_analysis = baseBoardWholeStatusData.change_analysis if baseBoardWholeStatusData.change_analysis else ''
        feature_name = baseBoardWholeStatusData.feature_name if baseBoardWholeStatusData.feature_name else ''
        children_feature_name = baseBoardWholeStatusData.children_feature_name if baseBoardWholeStatusData.children_feature_name else ''
        development_type = baseBoardWholeStatusData.development_type if baseBoardWholeStatusData.development_type else ''
        reusedegree = baseBoardWholeStatusData.reusedegree if baseBoardWholeStatusData.reusedegree else ''
        if id:
            id_datas = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.id == int(id), BOARD_WHOLE_STATUS_TABLE.parent == '2', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')).all()
            if (len(id_datas)) < 1:
                logger.error(f"------待更新的id：{id} 不存在，无法更新")
                id_list.append(id)
                continue
            else:
                update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(and_(BOARD_WHOLE_STATUS_TABLE.id == int(id), BOARD_WHOLE_STATUS_TABLE.parent == '2', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')
                                                                              ).values(change_analysis=change_analysis,
                                                                                       development_type=development_type,
                                                                                          reusedegree=reusedegree,
                                                                                       current_status=check_update, 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        if feature_name and not (children_feature_name or id):
            feature_datas = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name, BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name, BOARD_WHOLE_STATUS_TABLE.parent == '2', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')).all()
            if (len(feature_datas)) < 1:
                logger.error(f"------待更新的特性：{feature_name} 不存在，无法更新")
                feature_name_list.append(feature_name)
                continue
            else:
                update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name, BOARD_WHOLE_STATUS_TABLE.feature_name == feature_name, BOARD_WHOLE_STATUS_TABLE.parent == '2', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')
                                                                              ).values(change_analysis=change_analysis,
                                                                              development_type=development_type,
                                                                                          reusedegree=reusedegree,
                                                                                          current_status=check_update, 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        related_rdc = baseBoardWholeStatusData.related_rdc if baseBoardWholeStatusData.related_rdc else ''
        related_rdc_title = baseBoardWholeStatusData.related_rdc_title if baseBoardWholeStatusData.related_rdc_title else ''
        related_requirement_preplanning_version = baseBoardWholeStatusData.related_requirement_preplanning_version if baseBoardWholeStatusData.related_requirement_preplanning_version else ''
        related_requirement_status = baseBoardWholeStatusData.related_requirement_status if baseBoardWholeStatusData.related_requirement_status else ''
        related_parent_rdc = baseBoardWholeStatusData.related_parent_rdc if baseBoardWholeStatusData.related_parent_rdc else ''
        related_fault_num = baseBoardWholeStatusData.related_fault_num if baseBoardWholeStatusData.related_fault_num else 0
        

        if children_feature_name and related_rdc:
            children_feature_datas = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name, BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name, BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc, BOARD_WHOLE_STATUS_TABLE.parent == '0', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')).all()
            if len(children_feature_datas) < 1:
                logger.error(f"------待更新的子特性：{children_feature_name} 不存在，无法更新")
                children_feature_name_list.append(children_feature_name)
                continue

            update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(and_(BOARD_WHOLE_STATUS_TABLE.board_name == board_name, BOARD_WHOLE_STATUS_TABLE.children_feature_name == children_feature_name, BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc,BOARD_WHOLE_STATUS_TABLE.parent == '0',BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')
                                                                          ).values(related_rdc=related_rdc,
                                                                                   related_rdc_title=related_rdc_title,
                                                                                    related_requirement_preplanning_version=related_requirement_preplanning_version,
                                                                                    related_requirement_status=related_requirement_status,
                                                                                    related_parent_rdc=related_parent_rdc,
                                                                                    related_fault_num=related_fault_num,
                                                                                    current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        if related_rdc and not (children_feature_name or id):
            related_rdcs = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc, BOARD_WHOLE_STATUS_TABLE.parent == '0', BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')).all()
            if len(related_rdcs) < 1:
                logger.error(f"------待更新的rdc编号：{related_rdc} 不存在，无法更新")
                related_rdc_list.append(related_rdc)
                continue

            update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(and_(BOARD_WHOLE_STATUS_TABLE.related_rdc == related_rdc,BOARD_WHOLE_STATUS_TABLE.parent == '0',BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y')
                                                                          ).values(
                                                                                    related_rdc_title=related_rdc_title,
                                                                                    related_requirement_preplanning_version=related_requirement_preplanning_version,
                                                                                    related_requirement_status=related_requirement_status,
                                                                                    related_parent_rdc=related_parent_rdc,
                                                                                    related_fault_num=related_fault_num,
                                                                                    current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            
        db.session.execute(update_sql)  
    # 创建新用户 
    db.session.commit()
    db.session.refresh(db.session.query(BOARD_WHOLE_STATUS_TABLE).first())
    if len(id_list) > 0 or len(feature_name_list) > 0 or len(children_feature_name_list) > 0  or len(related_rdc_list) > 0:
        return list(set(id_list)) + list(set(feature_name_list)) + list(set(children_feature_name_list)) + list(set(related_rdc_list)), 201
    return [], 200

def updateBoardWholeStatusData():
    """
    更新指定的单板全局状态取值
    ---
    tags:
      - 单板全局状态
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
            id:
              type: string
              description: 每行记录的唯一标识
            board:
              type: string
              description: 单板名称
            product:
              type: string
              description: 产品因子取值
            boardType:
              type: string
              description: 板卡类型因子取值
            boardBusinessModel:
              type: string
              description: 单板业务模型因子取值
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            parent:
              type: boolean
              description: 是否父级特性
            changeAnalysis:
              type: string
              description: 变更分析
            milestone:
              type: string
              description: 里程碑
            rdcIdent:
              type: string
              description: 子特性关联RDC标识
            requirementPrePlanVersion:
              type: string
              description: 子特性关联需求预规划版本
            requirementStatus:
              type: string
              description: 子特性关联需求状态
            parentNodeRdc:
              type: string
              description: 关联父节点RDC
            related_fault_num:
              type: int
              description: 关联故障数
          example:   # 示例值
            id: "1"
            board: "光层业务"
            product: "灰光业务"
            boardType: "F010102-灰光业务基础特性"
            boardBusinessModel: "xx"
            feature: "xx"
            subFeature: "xx"
            parent: "光层业务"
            changeAnalysis: "灰光业务"
            milestone: "F010102-灰光业务基础特性"
            rdcIdent: "xx"
            requirementPrePlanVersion: "xx"
            requirementStatus: "xx"
            parentNodeRdc: "xx"
            related_fault_num: 1
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    results, code = updateSrcBoardWholeStatusData([body_params], employ_no)
    message = "修改成功"
    if code != 200:
        message = "待修改的记录部分不存在，修改不成功的记录如下："
    return jsonify({"code": code, "status": "success", "message": message, "data": results})

# Started by AICoder, pid:g5ae2132e7m21321403b08f3b0d4a09c5d01c2ca 
def syncSrcBoardWholeStatusDataRDC(body_params: dict, employ_no: str, token: str, fields:dict, markdown_flag: bool=True):
    features = querySrcBoardWholeStatusByParams(body_params, markdown_flag)
    rdc_params_list: List[Dict[str, Any]] = []
    whole_status_feature_data_dict = dict()
    feature_data_dict = dict()
    for item in features:
        if item.get("parent") == "2":
            board_name = item.get("board")
            feature = item.get("feature")
            if board_name + feature not in whole_status_feature_data_dict:
                analysis = item.get("changeAnalysis")
                analysis = analysis.replace(':', ':<br>').replace(';', ';<br>')
                whole_status_feature_data_dict[board_name + feature] = analysis
            continue
        elif item.get("parent") != "0":
            continue
        feature = item.get("feature")
        sub_feature = item.get("subFeature")
        board_name = item.get("board")
        if feature not in feature_data_dict:
            feature_data = querySrcFeatureBoardRelation("", "", "", feature)
            feature_data_dict[feature] = feature_data
        else:
            feature_data = feature_data_dict[feature] 
        
        if len(feature_data) < 1:
            continue
        
        for sub_item in feature_data:
            if sub_item.get("subFeature") != sub_feature:
                continue
            
            if "description" in fields:
                description_content = sub_item.get("description", "")
                # 添加空值检查
                if description_content is not None:
                    # 在特定字段前添加换行符
                    fields_to_add_br = ["功能描述：", "修改点/验证点：", "单板/组件：", "方案：", "特殊要求："]
                    for field in fields_to_add_br:
                        if field in description_content:
                            # 在字段前添加换行符
                            description_content = description_content.replace(field, f"<br>{field}")
                    fields['description'] = description_content
                else:
                    # 如果 description_content 是 None，可以保留原值
                    fields['description'] = description_content
            if "acceptance_criteria" in fields:
                fields['acceptance_criteria'] = sub_item.get("acceptanceCriteria") 
            if "belong_domain" in fields:
                fields['belong_domain'] = item.get("belong_domain") 
            if "featureContentLink" in fields:
                fields['featureContentLink'] = sub_item.get("featureContentLink") 
            if "analysisReport" in fields:
                fields['analysisReport'] = whole_status_feature_data_dict[board_name + feature]
            if "partName" in fields:
                fields['partName'] = board_name
        rdc_params = {
            "workItems": [{"id": item.get("rdcIdent")}],
            "fields": [copy.deepcopy(fields)],
        }
        rdc_params_list.append(rdc_params)
    #logger.info(f"------rdc_params_list:{rdc_params_list}")
    error_workItems = update_RDC_by_key(rdc_params_list, employ_no, token)
    return error_workItems
# Ended by AICoder, pid:g5ae2132e7m21321403b08f3b0d4a09c5d01c2ca 

def syncBoardWholeStatusDataRDC():
    """
    同步指定的单板全局状态取值到RDC
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: token
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
            board:
              type: string
              description: 单板名称
            feature:
              type: string
              description: 特性名称
          example:   # 示例值
            board: "M1LB8R(8130H)"
            feature: "F010101-彩光业务基础特性"
    responses:
      200:
        description: 成功同步指定的单板全局状态取值到RDC
    """
    employ_no = request.headers.get('X-Emp-No')
    token = request.headers.get('X-Auth-Value')
    body_params = request.get_json()
    rdc_fields = body_params.get('rdc_fields', {})
    if 'rdc_fields' in body_params:
        del body_params['rdc_fields']
    
    error_workItems = syncSrcBoardWholeStatusDataRDC(body_params, employ_no, token, rdc_fields)
    code = 200
    return jsonify({"code": code, "status": "success", "message": '', "data": error_workItems})


def importExcelbaseBoardWholeStatusData():
    """
    Excel文件上传接口
    ---
    tags:
      - 单板全局状态
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
        df["产品因子取值"] = df["产品因子取值"].ffill()
        df["板卡类型因子取值"] = df["板卡类型因子取值"].ffill()
        df["单板业务模型因子取值"] = df["单板业务模型因子取值"].ffill()
        df["单板名称"] = df["单板名称"].ffill()
        df["特性/子特性"] = df["特性/子特性"].ffill()
        df = df.fillna(value='') 
        # 数据库操作
        pre_feature_name = ''
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['product_factor_value'] = row["产品因子取值"] if "产品因子取值" in row else '' 
            table_dict['board_type_factor_value'] = row["板卡类型因子取值"] if "板卡类型因子取值" in row else '' 
            table_dict['board_service_model_factor_values'] = row["单板业务模型因子取值"] if "单板业务模型因子取值" in row else '' 
            table_dict['board_name'] = row["单板名称"] if "单板名称" in row else '' 
            table_dict['feature_name'] =  '' 
            table_dict['children_feature_name'] =  '' 
            if row["特性/子特性"] == "所有支持的特性/子特性":
                table_dict['feature_name'] =  '' 
                table_dict['children_feature_name'] =  '' 
                table_dict['parent'] = '3'
            else:
                level = classify_feature(row["特性/子特性"])
                if level == '2':
                    table_dict['feature_name'] =  row["特性/子特性"]
                    table_dict['children_feature_name'] = ''
                    pre_feature_name = row["特性/子特性"]
                elif level == '1':
                    table_dict['feature_name'] =  pre_feature_name
                    table_dict['children_feature_name'] = row["特性/子特性"]
                if level != 'undefine':
                    table_dict['parent'] = level
                if row["关联RDC标识"].strip():
                    table_dict['parent'] = '0'
                    # print(f"----------------关联RDC标识:{row['关联RDC标识']}-------------------")
            table_dict['change_analysis'] = row["变更分析"] if "变更分析" in row else '' 
            table_dict['milestone'] = row["里程碑"] if "里程碑" in row else '' 
            table_dict['related_rdc'] = row["关联RDC标识"] if "关联RDC标识" in row else '' 
            table_dict['related_rdc_title'] = row["关联RDC标题"] if "关联RDC标题" in row else '' 
            table_dict['related_requirement_preplanning_version'] = row["关联需求预规划版本"] if "关联需求预规划版本" in row else '' 
            table_dict['related_requirement_status'] = row["关联需求状态"] if "关联需求状态" in row else '' 
            table_dict['related_parent_rdc'] = row["关联父节点RDC"] if "关联父节点RDC" in row else '' 
            table_dict['related_problem_num'] = row["关联故障数"] if "关联故障数" in row else ''
            db_factor_values = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(BOARD_WHOLE_STATUS_TABLE.product_factor_value == table_dict["product_factor_value"],
                                                                                      BOARD_WHOLE_STATUS_TABLE.milestone == table_dict['milestone'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_type_factor_value == table_dict['board_type_factor_value'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values == table_dict['board_service_model_factor_values'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_name == table_dict['board_name'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.feature_name == table_dict['feature_name'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.children_feature_name == table_dict['children_feature_name'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.parent == table_dict['parent']
                                                                       )).all()
            if len(db_factor_values) > 0:
                update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(and_(BOARD_WHOLE_STATUS_TABLE.product_factor_value == table_dict["product_factor_value"],
                                                                          BOARD_WHOLE_STATUS_TABLE.milestone == table_dict['milestone'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_type_factor_value == table_dict['board_type_factor_value'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_service_model_factor_values == table_dict['board_service_model_factor_values'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.board_name == table_dict['board_name'],
                                                                                   BOARD_WHOLE_STATUS_TABLE.feature_name == table_dict['feature_name'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.children_feature_name == table_dict['children_feature_name'],
                                                                                  BOARD_WHOLE_STATUS_TABLE.parent == table_dict['parent'])
                                                                       ).values(feature_name=table_dict['feature_name'], 
                                                                                children_feature_name=table_dict['children_feature_name'], parent=table_dict['parent'], 
                                                                                change_analysis=table_dict['change_analysis'], milestone=table_dict['milestone'], 
                                                                                related_rdc=table_dict['related_rdc'], related_rdc_title=table_dict['related_rdc_title'],
                                                                                related_requirement_preplanning_version=table_dict['related_requirement_preplanning_version'],
                                                                                related_requirement_status=table_dict['related_requirement_status'],
                                                                                related_parent_rdc=table_dict['related_parent_rdc'],
                                                                                current_status=check_update, 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)  
            else:
                insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=table_dict['board_name'], 
                                                                 product_factor_value=table_dict['product_factor_value'], board_type_factor_value=table_dict['board_type_factor_value'], 
                                                                 board_service_model_factor_values=table_dict['board_service_model_factor_values'],  feature_name=table_dict['feature_name'], children_feature_name=table_dict['children_feature_name'], 
                                                                parent=table_dict['parent'], change_analysis=table_dict['change_analysis'], milestone=table_dict['milestone'], related_rdc=table_dict['related_rdc'],
                                                                related_rdc_title=table_dict['related_rdc_title'], related_requirement_preplanning_version=table_dict['related_requirement_preplanning_version'],
                                                                related_requirement_status=table_dict['related_requirement_status'], related_parent_rdc=table_dict['related_parent_rdc'], 
                                                              current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BOARD_WHOLE_STATUS_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}    
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}

def importOldBoardWholeStatusData():
    """
    Excel文件上传存量单板RDC数据接口
    ---
    tags:
      - 单板全局状态
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
      - name: board
        in: header
        description: 单板名称
        required: true
        type: string
        example: "M1LB8TF(8131H)"
      - name: dataType
        in: header
        description: 存量RDC对应的特性类型
        required: true
        type: string
        example: "new"
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
    board_name = request.headers.get('board')
    dataType = request.headers.get('dataType')
    if 'file' not in request.files:
        return jsonify({"error": "未上传RDC数据文件"}), 400
    
    file = request.files['file']
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
    old_new_children_feature_dict = dict()
    if dataType.lower() == 'old':
        results = querySrcOldChildrenFeatureDataByParams({})
        for result in results:
            if result["oldSubFeature"] not in old_new_children_feature_dict:
                old_new_children_feature_dict[result["oldSubFeature"]] = []
            old_new_children_feature_dict[result["oldSubFeature"]].append(result["subFeature"])

    # 检查文件类型
    query_params = {"board": board_name}
    
    results = querySrcBoardWholeStatusByParams(query_params, markdown_flag=True)
    result = dict()
    feature_datas = []
    if results:
        result = results[0]
        feature_datas = querySrcFeatureBoardRelation(','.join(result["boardBusinessModel"].split('|')))
    
    try:
        df = pd.read_excel(file, engine="openpyxl")
        df = df.fillna(value='')
        new_df = df[df['工作项类型']=='产品需求']
        # 数据库操作
        column1 = '标题'
        column2 = '标识'
    
        src_db_query_result = db.session.query(
            BOARD_WHOLE_STATUS_TABLE.board_name,
                BOARD_WHOLE_STATUS_TABLE.feature_name,
                BOARD_WHOLE_STATUS_TABLE.children_feature_name,
                BOARD_WHOLE_STATUS_TABLE.related_rdc
        ).filter(BOARD_WHOLE_STATUS_TABLE.board_name==board_name).all()
        src_db_result = [BaseBoardWholeStatusData.model_validate(model_item).model_dump(by_alias=True) for model_item in src_db_query_result]
        # logger.info(f"-----src_db_result:{src_db_result}")
        db_rdc_result = deduplicate_list_by_keys(src_db_result, num=4, key_order=['board', 'feature', 'subFeature', 'rdcIdent'])
        # logger.info(f"-----db_rdc_result:{db_rdc_result}")
        db_subfeature_result = deduplicate_list_by_keys(src_db_result, num=3, key_order=['board', 'feature', 'subFeature'])
        db_feature_result = deduplicate_list_by_keys(src_db_result, num=2, key_order=['board', 'feature'])
        for feature_data in feature_datas:
            subFeature_number = '-'.join(feature_data['subFeature'].split('-',2)[:2])
            if dataType.lower() == 'new':
                row_num_list = find_string_in_column(new_df, column1, subFeature_number)
            else:
                row_num_list = []
                for key, values in old_new_children_feature_dict.items():
                    for value in values:
                        if value.startswith(subFeature_number) and extract_target(key):
                            row_index = find_string_in_column(new_df, column1, extract_target(key))
                            if row_index:
                                row_num_list.extend(row_index)
                row_num_list = list(set(row_num_list))
            for row_num in row_num_list:        
                rdc_id = new_df.iloc[row_num][column2]
                unique_rdc_data = board_name + feature_data["feature"] + feature_data["subFeature"] + rdc_id
                if feature_data["subFeature"].strip() and unique_rdc_data not in db_rdc_result:
                    # logger.info(f"--------unique_rdc_data:{unique_rdc_data}")
                    unique_feature_data = board_name + feature_data["feature"]
                    if unique_feature_data not in db_feature_result:
                        insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=result["product"], 
                                                        board_type_factor_value=result["boardType"], board_service_model_factor_values=result["boardBusinessModel"], feature_name=feature_data["feature"], 
                                                        parent='2', milestone = result["mileStone"], current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                        db.session.execute(insert_sql)
                        db_feature_result.append(unique_feature_data)
                    unique_subfeature_data = board_name + feature_data["feature"] + feature_data["subFeature"]
                    if unique_subfeature_data not in db_subfeature_result:
                        insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=board_name, product_factor_value=result["product"], 
                                                        board_type_factor_value=result["boardType"], board_service_model_factor_values=result["boardBusinessModel"], feature_name=feature_data["feature"], 
                                                        children_feature_name=feature_data["subFeature"], parent='1', milestone = result["mileStone"],
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                        db.session.execute(insert_sql)
                        db_subfeature_result.append(unique_subfeature_data)
                    insert_sql = insert(BOARD_WHOLE_STATUS_TABLE).values(board_name=result["board"], product_factor_value=result["product"], 
                                                        board_type_factor_value=result["boardType"], board_service_model_factor_values=result["boardBusinessModel"], feature_name=feature_data["feature"], 
                                                        children_feature_name=feature_data["subFeature"], parent='0', 
                                                        milestone = result["mileStone"],related_rdc=rdc_id, related_rdc_title='', related_requirement_preplanning_version='',
                                                        related_requirement_status='',related_parent_rdc='',
                                                            current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                    db.session.execute(insert_sql)
                    db_rdc_result.append(unique_rdc_data)
                
        db.session.commit()
        db.session.refresh(db.session.query(BOARD_WHOLE_STATUS_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入存量RDC标识成功", "data": []}    
    except Exception as e:
        # raise e
        return {"code": 201, "status": "failed", "message": f"导入存量RDC标识失败: {str(e)}", "data": []}
    

def deleteChangeAnalysisData(board_name:str, employ_no:str):
    new_operator_person = pub_get_employ_name(employ_no)
    update_sql = update(BOARD_WHOLE_STATUS_TABLE).where(BOARD_WHOLE_STATUS_TABLE.board_name.in_(board_name.split(','))).values(
                                                                                    change_analysis='',
                                                                                    current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            
    db.session.execute(update_sql)  
    delete_count = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).where(BOARD_CHANGE_ANALYSIS_TABLE.board_name.in_(board_name.split(','))).delete()
    # 创建新用户 
    db.session.commit()


def queryBoardWholeStatusDataByBoardName(board_name):
    model_list = db.session.query(BOARD_WHOLE_STATUS_TABLE).where(BOARD_WHOLE_STATUS_TABLE.board_name == board_name).order_by(BOARD_WHOLE_STATUS_TABLE.board_name, BOARD_WHOLE_STATUS_TABLE.feature_name, BOARD_WHOLE_STATUS_TABLE.children_feature_name).all()
    return [BaseBoardWholeStatusData.model_validate(model_item).model_dump() for model_item in model_list]



def deleteBoardWholeStatusDataByBoardName(board_names):
    board_name_list = board_names.split(',')
    # 删除单板全局状态表数据
    delete_count = db.session.query(BOARD_WHOLE_STATUS_TABLE).where(BOARD_WHOLE_STATUS_TABLE.board_name.in_(board_name_list)).delete()
    db.session.commit()
    # 删除单板变更分析表数据
    delete_count = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).where(BOARD_CHANGE_ANALYSIS_TABLE.board_name.in_(board_name_list)).delete()
    db.session.commit()


def queryBoardWholeStatusByField(field_name: str, target_value: str) -> list:
    try:
        # 1. 基础参数校验
        if not field_name or not target_value:
            print("field_name和target_value不能为空")
            return []
        # 2. 校验字段名是否存在于数据表中
        table_columns = [col.name for col in BOARD_WHOLE_STATUS_TABLE.__table__.columns]
        if field_name not in table_columns:
            print(f"字段{field_name}不存在，可选字段：{','.join(table_columns)}")
            return []
        # 3. 构建查询条件（默认查询有效数据）
        # 如果 target_value 是一个普通字符串，通常会在前后加 % 实现包含匹配
        like_pattern = f"%{target_value}%"
        conditions = [getattr(BOARD_WHOLE_STATUS_TABLE, field_name).like(like_pattern), BOARD_WHOLE_STATUS_TABLE.effective_flag == "Y"]
        # 4. 执行查询
        model_list = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(*conditions)).all()
        # 5. 转换为字典列表（使用Pydantic模型保持格式一致）
        return [BaseBoardWholeStatusData.model_validate(model_item).model_dump() for model_item in model_list]
    except Exception as e:
        print(f"查询异常：{str(e)}")
        return []


def queryBoardWholeStatusByBoardNameAndPreplanVersion(board_name, preplan_version, rdc_status):
    """
    查询 BOARD_WHOLE_STATUS_TABLE 中：
    - board_name 模糊匹配传入的逗号分隔关键词（每个关键词使用 LIKE '%关键词%'）
    - preplan_version 精确匹配传入的逗号分隔值（使用 IN）
    - effective_flag = 'Y'
    - rdc_status RDC状态
    返回扁平数据列表。
    """
    condition_list = [BOARD_WHOLE_STATUS_TABLE.effective_flag == 'Y']
    # 处理 board_name：模糊匹配（OR 组合多个 LIKE）
    if board_name:
        board_name_list = [n.strip() for n in board_name.split(',') if n.strip()]
        if board_name_list:
            like_conditions = [
                BOARD_WHOLE_STATUS_TABLE.board_name.like(f'%{keyword}%')
                for keyword in board_name_list
            ]
            condition_list.append(or_(*like_conditions))
    # 处理 related_requirement_preplanning_version：精确匹配（IN）
    if preplan_version:
        version_list = [v.strip() for v in preplan_version.split(',') if v.strip()]
        if version_list:
            condition_list.append(
                BOARD_WHOLE_STATUS_TABLE.related_requirement_preplanning_version.in_(version_list)
            )
    if rdc_status:
        if rdc_status == "support":
            condition_list.append(BOARD_WHOLE_STATUS_TABLE.related_requirement_status.in_(["可交付", "已支持"]))
        else:
            condition_list.append(BOARD_WHOLE_STATUS_TABLE.related_requirement_status.notin_(["可交付", "已支持", "已废弃"]))
    try:
        model_list = db.session.query(BOARD_WHOLE_STATUS_TABLE).filter(and_(*condition_list)).all()
        result_list = [
            BaseBoardWholeStatusData.model_validate(item).model_dump(by_alias=True)
            for item in model_list
        ]
        return result_list
    except Exception as e:
        print(f"Query failed: {e}")
        return []
