from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from io import BytesIO
from flask import request, jsonify
from electric_knowledge.data_model import db
from test_demo.data_model import TEST_BUSINESS_MODEL_RATE_TABLE


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'
START_RELATED_VERSION = 'V1.00.001'



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

def queryTestBusinessModelRateTableDataByParams():    # 构建基础查询
    """
    查询指定的业务模型速率表数据
    ---
    tags:
      - test-demo
    description: 查询指定的业务模型速率表数据
    parameters:
      - name: network_element_business_model_rate
        in: query
        description: 业务模型速率
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
      
    }]}
    """
    conditions = [TEST_BUSINESS_MODEL_RATE_TABLE.effective_flag == 'Y']
    # coreElementFactorRelationDataFilter = CoreElementFactorRelationDataFilter(**request.json)
    network_element_business_model_rate = request.args.get('network_element_business_model_rate')
    
    if network_element_business_model_rate:
        # query = query.filter(CORE_ELEMENT_FACTOR_RELATION_TABLE.belong_domain == coreElementFactorRelationDataFilter.belong_domain)  # 模糊匹配名称
        conditions.append(TEST_BUSINESS_MODEL_RATE_TABLE.network_element_business_model_rate == network_element_business_model_rate)
    operator_person = request.args.get('operator_person')
    if operator_person:
        # query = query.filter(CORE_ELEMENT_FACTOR_RELATION_TABLE.core_element_type == coreElementFactorRelationDataFilter.core_element_type)
        conditions.append(TEST_BUSINESS_MODEL_RATE_TABLE.operator_person == operator_person)
    
    try:
        baseBusinessModelRateTableDatas = db.session.query(TEST_BUSINESS_MODEL_RATE_TABLE) \
        .filter(and_(*conditions)).all() \
     
        results = []
        for item in baseBusinessModelRateTableDatas:
            
            # 验证并转换为Pydantic模型
            results.append(item.to_dict())

        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": results})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": {}})


def addTestBusinessModelRateTableData():
    """
    新增指定的业务模型速率表数据
    ---
    tags:
      - test-demo
    description: 新增指定的业务模型速率表数据
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
              description: 归属领域
            business_type_list:
              type: string
              description: 要素类型
          example:   # 示例值
            network_element_business_model_rate: "10G"
            business_type_list: "STM64,10GE,OTU2,OTU2E"
    responses:
      200:
        description: 成功更新数据
    """
    new_operator_person = request.headers.get('X-Emp-No')
    coreElementFactorRelationData = request.get_json()
    # 提取参数
    network_element_business_model_rate = coreElementFactorRelationData.get("network_element_business_model_rate", "")
    business_type_list = coreElementFactorRelationData.get("business_type_list", "")
    # 检查新增的数据在数据表中是否已存在
    
    insert_sql = insert(TEST_BUSINESS_MODEL_RATE_TABLE).values(network_element_business_model_rate=network_element_business_model_rate, business_type_list=business_type_list, 
                                                          create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                          update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
    db.session.execute(insert_sql)

    # 创建新用户
    db.session.commit()
    db.session.refresh(db.session.query(TEST_BUSINESS_MODEL_RATE_TABLE).first())
    return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})