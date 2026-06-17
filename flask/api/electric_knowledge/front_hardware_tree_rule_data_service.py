from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import pandas as pd

from electric_knowledge.data_model import db, HARDWARE_TREE_RULE_TABLE
from flask import request, jsonify


# 定义查询参数模型
class HardwareTreeRuleTableData(BaseModel):
    id: Optional[int] = None
    hardware_type: Optional[str] = None
    factor_name: Optional[str] = None
    situation: Optional[str] = None
    input_format: Optional[str] = None
    input_remark: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def query_hardware_tree_rule_dict_by_situation():
    """
    根据场景查询硬件树填写规则
    ---
    tags:
      - 单板树
    description: 根据场景查询硬件树填写规则（POST 请求，参数在 body 中）
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        description: 请求体
        required: true
        schema:
          type: object
          properties:
            hardware_type:
              type: string
              description: 硬件类型, 单板/子架
              example: "单板"
            situation:
              type: string
              description: 场景, 支线路合一卡/线路侧L卡/xx
              example: "支线路合一卡"
          required:
            - hardware_type
            - situation
    responses:
      200:
        description: 成功返回不同场景下的信息填写规则
        examples:
          application/json: {
              "code": 200,
              "status": "success",
              "message": "获取成功",
              "data": {
                "单板名称": {
                  "required_flag": true,
                  "input_format": "",
                  "input_remark": "格式：单板名称(Board ID)，Board ID应该是4位十六进制数字+字母H"
                },
                "产品": {
                  "required_flag": true,
                  "input_format": "",
                  "input_remark": null
                },
              }
          }
    """
    data = request.get_json(force=True)
    hardware_type = data.get("hardware_type")
    situation = data.get("situation")

    if not hardware_type or not situation:
        return jsonify({
            "code": 400,
            "status": "error",
            "message": "缺少必要参数: hardware_type 或 situation",
            "data": {}
        }), 400

    rule_dict = service_query_hardware_tree_rule_dict_by_situation(hardware_type, situation)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": rule_dict})


def service_query_hardware_tree_rule_dict_by_situation(hardware_type, object_situation_str):
    rule_dict = {}
    object_situation_list = object_situation_str.split(',')
    # 根据 related_rdc_ident 查询所有匹配的记录
    data_model_list = db.session.query(HARDWARE_TREE_RULE_TABLE).filter(HARDWARE_TREE_RULE_TABLE.hardware_type == hardware_type).all()
    for data_model_item in data_model_list:
        raw_situation_str = (data_model_item.situation or "").strip()
        raw_situation_list = raw_situation_str.split(",")
        factor_name = data_model_item.factor_name
        rule_dict[factor_name] = {
            "required_flag": True if raw_situation_str == "所有" or bool(set(object_situation_list) & set(raw_situation_list)) else False,
            "input_format": data_model_item.input_format,
            "input_remark": data_model_item.input_remark,
        }
    return rule_dict