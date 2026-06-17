from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func, literal_column, case
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from io import BytesIO
import re

from electric_knowledge.data_model import db, BOARD_TREE_TABLE
from electric_knowledge.front_business_coreelement_factor_relation_data_service import querySrcCoreElementFactorValueDict
from electric_knowledge.front_board_whole_status_data_service import deleteBoardWholeStatusDataByBoardName
from electric_knowledge.front_hardware_tree_rule_data_service import service_query_hardware_tree_rule_dict_by_situation
from electric_knowledge.front_board_opt_biz_data_service import deleteSrcBoardOptBizData, addSrcBoardOptBizData, querySrcBoardOptBizByParams
from electric_knowledge.utils_pub import pub_remove_after_parentheses, pub_get_employ_name
from electric_knowledge.utils_rdc import create_RDC, query_RDC
from electric_knowledge.utils_icenter import create_icenter_page, update_icenter_page, query_icenter_page
from flask import request, jsonify
import logging

logger = logging.getLogger("Logger")


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

extra_columns = ["board", "status", "create_time", "update_time", "operator_person", "effective_flag"]

# 定义查询参数模型
class BoardTreeData(BaseModel):
    id: Optional[str] = None
    board_name: Optional[str] = Field(None, alias="board")
    factor_type_cn: Optional[str] = Field(None, alias="factorTypeCn")
    factor_type_en: Optional[str] = Field(None, alias="factorTypeEn")
    factor_value: Optional[str] = Field(None, alias="factorValue")
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


def querySrcBoardTreeByParams(query_params: dict={}, markdown_flag:bool=False, part_match_flag:bool=True):
    conditions = [BOARD_TREE_TABLE.effective_flag == 'Y']
    boardTreeData = BoardTreeData(**query_params)
    if boardTreeData.board_name:
        reversed_field = func.reverse(BOARD_TREE_TABLE.board_name)
        last_paren_pos = func.locate('(', reversed_field)
        split_result = case(
            (last_paren_pos > 0, 
            func.left(BOARD_TREE_TABLE.board_name, func.length(BOARD_TREE_TABLE.board_name) - last_paren_pos + 1)),
            else_=BOARD_TREE_TABLE.board_name
        )
        # 过滤条件：分割后的结果包含 '123'
        src_board_list = boardTreeData.board_name.split(',')
        feature_conditions1 = [split_result.like('%' + board.strip() + '%') for board in src_board_list if board is not None and board.strip() != '']
        feature_conditions2 = [BOARD_TREE_TABLE.board_name == board.strip() for board in src_board_list if board is not None and board.strip() != '']
        feature_conditions1.extend(feature_conditions2)
        conditions.append(or_(*feature_conditions1))
    factor_type_cn_list = []
    if boardTreeData.factor_type_cn:
        factor_type_cn_list = boardTreeData.factor_type_cn.split(',')
        conditions.append(BOARD_TREE_TABLE.factor_type_cn.in_(factor_type_cn_list))
    if boardTreeData.factor_type_en:
        conditions.append(BOARD_TREE_TABLE.factor_type_en.in_(boardTreeData.factor_type_en.split(',')))
    if boardTreeData.current_status:
        conditions.append(BOARD_TREE_TABLE.current_status.in_(boardTreeData.current_status.split(',')))
    factor_value_list = []
    if boardTreeData.factor_value:
        factor_value_list = boardTreeData.factor_value.split(',')
        conditions.append(or_(*[contains_split_value(BOARD_TREE_TABLE.factor_value, factor_value, part_match_flag=part_match_flag) for factor_value in factor_value_list]))
    
    try:
        baseBoardTreeDatas = db.session.query(BOARD_TREE_TABLE).filter(and_(*conditions)).order_by(BOARD_TREE_TABLE.board_name, BOARD_TREE_TABLE.factor_type_cn, BOARD_TREE_TABLE.factor_type_en, BOARD_TREE_TABLE.factor_value).all()
        results = []
        tmp_dict = dict()
        tmp_item = dict()
        prev_board_name = ''
        for item in baseBoardTreeDatas:
            tmp_item = BoardTreeData.model_validate(item).model_dump(by_alias=True)
            if  prev_board_name and tmp_item['board'] != prev_board_name:
                prev_tmp_item.pop('factorTypeCn', None)
                prev_tmp_item.pop('factorTypeEn', None)
                prev_tmp_item.pop('factorValue', None)
                results.append(copy.deepcopy({**prev_tmp_item, **tmp_dict}))
                tmp_dict = dict()
            prev_board_name = tmp_item['board']
            prev_tmp_item = copy.deepcopy(tmp_item)
            tmp_dict[tmp_item['factorTypeCn']] = tmp_item['factorValue']
        if tmp_item:
            tmp_item.pop('factorTypeCn', None)
            tmp_item.pop('factorTypeEn', None)
            tmp_item.pop('factorValue', None)
            results.append(copy.deepcopy({**tmp_item, **tmp_dict}))
        if markdown_flag:
            new_results = []
            if  len(factor_type_cn_list) == len(factor_value_list):
                for result in results:
                    factor_type_num = 0
                    for cond in factor_type_cn_list:
                        # 直接通过索引查询，O(1) 时间复杂度
                        if cond in result:
                            factor_type_num += 1
                        else:
                            break
                    if factor_type_num == len(factor_type_cn_list):
                        new_results.append(result)
            return new_results
        return (results, 200)
    except Exception as e:
        return ([], 400)

def contains_split_value(column, value, delimiter='|', part_match_flag=True):
    delimiter1 = ','
    if part_match_flag:
        return or_(
            column == value,
            column.startswith(f"{value}{delimiter}"),
            column.endswith(f"{delimiter}{value}"),
            column.contains(f"{delimiter}{value}{delimiter}"),
            column.startswith(f"{value}{delimiter1}"),
            column.endswith(f"{delimiter1}{value}"),
            column.contains(f"{delimiter1}{value}{delimiter1}"),
            column.startswith(f"{value}")
        )
    else:
        return column == value


# 单板树
def queryBoardTreeByParams():    # 构建基础查询
    """
    查询指定的单板树取值
    ---
    tags:
      - 单板树
    description: 查询指定的单板树取值
    parameters:
      - name: board
        in: query
        description: 单板名称
        required: false
        type: string
      - name: factorTypeCn
        in: query
        description: 因子类型中文名称
        required: false
        type: string
      - name: factorTypeEn
        in: query
        description: 因子类型英文名称
        required: false
        type: string
      - name: factorValue
        in: query
        description: 因子取值
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
                "board": "单板1",
                "产品因子": "19700产品",
                "部件承载电层业务模式因子": "FRM部件_承载电层业务,光模块部件_承载电层业务,FPGA部件承载_电层业务+FRM部件承载_电层业务",
                "单板配置类型因子": "FlexO(0x01)",
                "物理端口数量因子": "C2,C4,C5",
                "客户侧光层业务因子": "SFP_LR-10K,SFP_ER-40K,SFP_ZR-80K",
                "线路侧光层业务因子": "10G_NULL_NULL,400G_SD-FEC2-NODIFF-20%_DP_QPSK,400G_OFEC_DP-QPSK",
                "status": "正常",
                "create_time": "2025-07-07T20:59:47",
                "update_time": "2025-07-11T18:56:24",
                "operator_person": "张进朋10305454",
                "effective_flag": "Y",
            }]}
    """
    
    query_params = request.args.to_dict()
    results, code = querySrcBoardTreeByParams(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})


# Started by AICoder, pid:m6b3ec1fbcxb02c14c5a0bf4c00c2b5ce4537ff8 
def queryBoardTreeFactorList():    # 构建基础查询
    """
    查询单板树全部因子类型列表
    ---
    tags:
      - 单板树
    description: 查询单板树全部因子类型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
        "code": 200,
        "message": "获取成功",
        "status": "success",
        "data": ["产品", "部件承载电层业务模式", "单板配置类型", "物理端口数量", "客户侧光层业务", "线路侧光层业务"]
    }
    """
    # 定义因子类型的固定顺序
    FIXED_FACTOR_ORDER = ['板卡类型', '单板业务模型', '产品', '单板支持的子架', '单板硬件PCB', '单板软件平台',  
      '单板配置类型', '物理端口数量', '部件承载电层业务模式', '客户侧光层业务', 
      '客户侧电层业务', '线路侧光层业务', '线路侧电层业务', '客户侧光模块', '线路侧光模块', 
      '业务FRM芯片', '交换FRM芯片', 'GEARBOX', '时钟芯片', '子卡', '开销逻辑', '控制逻辑'] 

    conditions = [BOARD_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    boardTreeData = BoardTreeData(**query_params)

    query = db.session.query(BOARD_TREE_TABLE.factor_type_cn).filter(and_(*conditions)).group_by(BOARD_TREE_TABLE.factor_type_cn)
    baseBoardFactorTypeDatas = query.all()
    
    # 获取所有因子类型
    all_factors = []
    for baseBoardFactorTypeData in baseBoardFactorTypeDatas:
        all_factors.append(baseBoardFactorTypeData[0])
    
    # 去重
    unique_factors = list(set(all_factors))
    special_factors = '单板方案链接'
    if special_factors in unique_factors:
        unique_factors.remove(special_factors)
    
    # 按照固定顺序对因子类型进行排序
    sorted_factors = []
    
    # 首先添加固定顺序的因子类型
    for fixed_factor in FIXED_FACTOR_ORDER:
        if fixed_factor in unique_factors:
            sorted_factors.append(fixed_factor)
            # 从原始列表中移除已添加的因子
            unique_factors.remove(fixed_factor)
    # 然后对其余因子类型按字母顺序排序
    sorted_factors.extend(sorted(unique_factors))
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": sorted_factors})



def querySrcBoardTreeFactorValueDict(query_params:dict={}, factor_list_flag:bool=False):
    boardTreeData = BoardTreeData(**query_params)
    conditions = [BOARD_TREE_TABLE.effective_flag == 'Y']
    if factor_list_flag:
        factor_list = db.session.query(BOARD_TREE_TABLE.factor_type_cn).filter(and_(*conditions)).group_by(BOARD_TREE_TABLE.factor_type_cn).all()
        return factor_list
    conditions.append(BOARD_TREE_TABLE.current_status.is_not(None))
    d_values = literal_column(
    f"GROUP_CONCAT(DISTINCT {BOARD_TREE_TABLE.factor_value.key} SEPARATOR ',')").label('factor_values')
    baseBoardStatusDatas = db.session.query(BOARD_TREE_TABLE.factor_type_cn, d_values).filter(and_(*conditions)).group_by(BOARD_TREE_TABLE.factor_type_cn).all()
    result = {}
    for item in baseBoardStatusDatas:
        result[item[0]] = list(set(item[1].split(',')))
    baseBoardStatusDatas_board = db.session.query(BOARD_TREE_TABLE.board_name).filter(and_(*conditions)).group_by(BOARD_TREE_TABLE.board_name).all()
    result["board"] = []
    for item in baseBoardStatusDatas_board:
        result["board"].append(item[0])
    baseBoardStatusDatas_status = db.session.query(BOARD_TREE_TABLE.current_status).filter(and_(*conditions)).group_by(BOARD_TREE_TABLE.current_status).all()
    result["status"] = []
    for item in baseBoardStatusDatas_status:
        result["status"].append(item[0])
    return result

def queryBoardTreeFactorValueDict():    # 构建基础查询
    """
    查询单板树的全部因子对应的取值列表
    ---
    tags:
      - 单板树
    description: 查询单板树的全部因子对应的取值列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    query_params = request.args.to_dict()
    result = querySrcBoardTreeFactorValueDict(query_params)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def addBoardTreeData():
    """
    新增指定的单板树取值
    ---
    tags:
      - 单板树
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
          example:   # 示例值
            board: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    # boardTreeData = BoardTreeData(**body_params)
    query_params = {"core_element_type": "单板"}
    factor_dict, code = querySrcCoreElementFactorValueDict(query_params)
    factor_dict_list = list(factor_dict.keys())
    board_name = body_params['board']
    opt_biz_relations = dict()
    opt_biz_relations['opt_biz_relation'] = dict()
    opt_biz_relations['opt_biz_relation']['add'] = []
    opt_biz_relation_list = []
    for key, value in body_params.items():
        # if key not in extra_columns:
        if key in factor_dict_list:
            factor_type_cn = key
            factor_value = value
        # 检查新增的数据在数据表中是否已存在
            insert_sql = insert(BOARD_TREE_TABLE).values(board_name=body_params["board"],
                                                        factor_type_cn=factor_type_cn, factor_value=factor_value,  current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
            db.session.execute(insert_sql)
        elif key.lower() == 'linerelation':
            for signal_relation in value:
                params = {"board": board_name,
                              "l_c_type":"线路侧",
                              "opt": signal_relation['module'],
                              "biz": signal_relation['service']
                               }
                
                if signal_relation['checked']:
                    opt_biz_relations['opt_biz_relation']['add'].append(params)
                    addSrcBoardOptBizData(params, new_operator_person)
                    opt_biz_relation_list.append(params["opt"] + "<->" + params["biz"])
                else:
                    deleteSrcBoardOptBizData(params)
    insert_sql = insert(BOARD_TREE_TABLE).values(board_name=body_params["board"],
                                                        factor_type_cn="映射关系", factor_value=','.join(opt_biz_relation_list),  current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
    db.session.execute(insert_sql)
    db.session.commit()
    db.session.refresh(db.session.query(BOARD_TREE_TABLE).first())
    return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": opt_biz_relations})

def updateSrcBoardTreeData(body_params, new_operator_person):
    board_name = body_params["board"]
    query_params = {"board_name": board_name}
    board_tree_datas = querySrcBoardTreeByParams(query_params, markdown_flag=True)
    inc_params = dict()
    for key, value in board_tree_datas[0].items():
        if key in body_params and key != 'id':
            # inc_result = list(set(body_params[key].replace('|', ',').split(',')) - set(value.replace('|', ',').split(',')))
            inc_result = list(set(body_params[key].split(',')) - set(value.split(',')))
            inc_params[key] = ','.join(inc_result)
    inc_params['board'] = board_name
    # 提取参数
    core_element_query_params = {"core_element_type": "单板"}
    factor_dict, code = querySrcCoreElementFactorValueDict(core_element_query_params)
    factor_dict_list = list(factor_dict.keys())
    query_params = {"board": board_name, "l_c_type": "线路侧"}
    opt_biz_results = querySrcBoardOptBizByParams(query_params, markdown_flag=True, part_match_flag=False)
    change_list = dict()
    change_list["add"] = []
    change_list["delete"] = []
    opt_biz_relation_list = []
    for key, value in body_params.items():
        if key in factor_dict_list:
            factor_type_cn = key
            factor_value = value
        # 检查新增的数据在数据表中是否已存在
            update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name == board_name, BOARD_TREE_TABLE.factor_type_cn == factor_type_cn, BOARD_TREE_TABLE.effective_flag == 'Y')
                                                                              ).values(
                                                                    factor_value=factor_value , 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            db.session.execute(update_sql)
        elif key.lower() == 'linerelation':
            for signal_relation in value:
                params = {"board": board_name,
                              "l_c_type":"线路侧",
                              "opt": signal_relation['module'],
                              "biz": signal_relation['service']
                               }
                if signal_relation['checked']:
                    addSrcBoardOptBizData(params, new_operator_person)
                    opt_biz_relation_list.append(params["opt"] + "<->" + params["biz"])
                    num = 0
                    for opt_biz_result in opt_biz_results:
                        if signal_relation['module'] == opt_biz_result['opt'] and signal_relation['service'] == opt_biz_result['biz']:
                            num += 1
                    if num < 1:
                        change_list["add"].append(params)
                else:
                    deleteSrcBoardOptBizData(params)
                    num = 0
                    for opt_biz_result in opt_biz_results:
                        if signal_relation['module'] == opt_biz_result['opt'] and signal_relation['service'] == opt_biz_result['biz']:
                            num += 1
                    if num > 0:
                        change_list["delete"].append(params)
    for opt_biz_result in opt_biz_results:
        num = 0
        for signal_relation in body_params['lineRelation']:
            if signal_relation['module'] == opt_biz_result['opt'] and signal_relation['service'] == opt_biz_result['biz']:
                num += 1
        if num < 1:
            params = {"board": board_name,
                              "l_c_type":"线路侧",
                              "opt": opt_biz_result['opt'],
                              "biz": opt_biz_result['biz']
                               }
            change_list["delete"].append(params)
            deleteSrcBoardOptBizData(params)
    inc_params['opt_biz_relation'] = change_list
    update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name == board_name, BOARD_TREE_TABLE.factor_type_cn == "映射关系", BOARD_TREE_TABLE.effective_flag == 'Y')
                                                                              ).values(
                                                                    factor_value=','.join(opt_biz_relation_list) , 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
    db.session.execute(update_sql)
    db.session.commit()
    db.session.refresh(db.session.query(BOARD_TREE_TABLE).first())
    return inc_params
    

def updateBoardTreeData():
    """
    更新指定的单板树取值
    ---
    tags:
      - 单板树
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
          example:   # 示例值
            board: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    inc_params = updateSrcBoardTreeData(body_params, new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": inc_params})

def deleteBoardTreeData():
    """
    删除指定的单板树取值
    ---
    tags:
      - 单板树
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
          example:   # 示例值
            board: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    # 提取参数
    boardTreeData = BoardTreeData(**body_params)
    # 提取参数
    board_name = boardTreeData.board_name
   
    # 检查新增的数据在数据表中是否已存在
    delete_count = db.session.query(BOARD_TREE_TABLE).where(BOARD_TREE_TABLE.board_name.in_(board_name.split(','))).delete()
    # 创建新用户 
    db.session.commit()
    # for board_name_item in board_name.split(','):
    #     deleteBoardWholeStatusDataByBoardName(board_name_item)
    deleteBoardWholeStatusDataByBoardName(board_name)
    boardOptBizData = {"board": board_name}
    deleteSrcBoardOptBizData(boardOptBizData)
    # db.session.refresh(db.session.query(BOARD_TREE_TABLE).all())
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def createRDC():
    """
    创建RDC
    ---
    tags:
      - 单板树
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
            rdc_space:
              type: string
              description: rdc空间名称
            rdc_title:
              type: string
              description: rdc标题
            description:
              type: string
              description: 描述
            acceptance_criteria:
              type: string
              description: 验收准则
            workItem_type:
              type: string
              description: 工作项类型
          example:   # 示例值
            rdc_space: "OTNSW"
            rdc_title: "测试RDC接口需要"
            description: "xx"
            acceptance_criteria: "xx"
            workItem_type: "PR"
    responses:
      200:
        description: 成功创建RDC
    """
    employ_no = request.headers.get('X-Emp-No')
    # new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    body_params["employ_no"] = employ_no
    # 提取参数
    results, _ = create_RDC([body_params])
    return jsonify({"code": 200, "status": "success", "message": "创建成功", "data": results})

def queryRDC():
    """
    批量查询RDC详情
    ---
    tags:
      - 单板树
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
            rdc_space:
              type: string
              description: rdc空间名称
            rdcIdent_list:
              type: list
              description: 描述
            workItemType_list:
              type: list
              description: 验收准则
          example:   # 示例值
            rdc_space: "OTNSW"
            rdcIdent_list: ["OTNSW-175", "OTNSW-176"]
            workItemType_list: ["PR", "PR"]
    responses:
      200:
        description: 成功查询RDC详情
    """
    employ_no = request.headers.get('X-Emp-No')
    # new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    body_params["employ_no"] = employ_no
    # 提取参数
    results = query_RDC(body_params)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": results})

def importExcelBoardTreeData():
    """
    Excel文件上传接口
    ---
    tags:
      - 单板树
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
        df = df.fillna(value='')
        # factor_list = querySrcBoardTreeFactorValueDict({}, factor_list_flag=True)
        # columns_to_iterate = [col for col in df.columns if col not in ['ID', '单板名称', '操作人', '编号', '关联版本号', '更新时间', '数据状态']]

        query_params = {"core_element_type": "单板"}
        factor_dict, code = querySrcCoreElementFactorValueDict(query_params)
        factor_list = list(factor_dict.keys())
        factor_list.extend(['映射关系', '单板方案链接'])
        columns_to_iterate = [col for col in df.columns if col.replace("\n", "") in factor_list and col.replace("\n", "") != '单板名称']

        # 导入前先检查数据格式
        input_err_info_list = []
        for _, row in df.iterrows():
            situation = row.get("板卡类型")
            board_name = row["单板名称"]
            all_rule_dict = service_query_hardware_tree_rule_dict_by_situation("单板", situation)
            if not all_rule_dict: continue
            column_list = ["单板名称", *columns_to_iterate]
            for column_item in column_list:
                factor_key = column_item.replace("\n", "")
                single_rule_dict = all_rule_dict.get(factor_key)
                if not single_rule_dict: continue
                required_flag = single_rule_dict.get("required_flag")
                input_format = single_rule_dict.get("input_format")
                input_remark = single_rule_dict.get("input_remark")
                factor_value = row[factor_key]
                if required_flag and not factor_value:
                    input_err_info_list.append(f"【{board_name}】的【{factor_key}】为必填项，不能为空。")
                if factor_value and input_format:
                    factor_value_list = factor_value.split(',')
                    for factor_value_item in factor_value_list:
                        try:
                            pattern = re.compile(input_format)
                            if not pattern.fullmatch(factor_value_item):
                                input_err_info_list.append(f"【{board_name}】的【{factor_key}】【{factor_value_item}】格式存在问题。{input_remark}")
                        except re.error as e:
                            input_err_info_list.append(f"【{factor_key}】的正则表达式【{input_format}】存在问题。")
        if len(input_err_info_list) > 0:
            return {"code": 201, "status": "failed", "message": '导入失败', "data": input_err_info_list}
        # 数据库操作
        for _, row in df.iterrows():
            for columns in columns_to_iterate:
                table_dict = dict()
                # 假设 Excel 表头与数据库字段名一致
                table_dict['board_name'] = row["单板名称"] if "单板名称" in row else '' 
                table_dict['factor_type_en'] = ''
                table_dict['factor_type_cn'] = columns.replace("\n", "")
                table_dict['factor_value'] = row[columns]
                db_factor_values = db.session.query(BOARD_TREE_TABLE).filter(and_(BOARD_TREE_TABLE.board_name == table_dict['board_name'],
                                                                                          BOARD_TREE_TABLE.factor_type_cn == table_dict["factor_type_cn"]
                                                                          )).all()
                if len(db_factor_values) > 0 and row["单板名称"]:
                    update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name == table_dict['board_name'],
                                                                                          BOARD_TREE_TABLE.factor_type_cn == table_dict["factor_type_cn"]
                                                                          )).values(factor_value=table_dict['factor_value'], current_status=check_update, 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                    db.session.execute(update_sql)
                else:
                    insert_sql = insert(BOARD_TREE_TABLE).values(board_name=table_dict['board_name'], factor_type_cn=table_dict["factor_type_cn"], 
                                                                factor_value=table_dict["factor_value"], current_status=normal,  create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                    db.session.execute(insert_sql)
                    # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BOARD_TREE_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")

def addBoardIcenterPage():
    """
    新增指定的单板方案iCenter页面
    ---
    tags:
      - 单板树
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
            board:
              type: string
              description: 单板名称
          example:   # 示例值
            board: "M1BSO(80CDH)"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    
    board_infos = querySrcBoardTreeByParams(body_params, markdown_flag=True)[0]
    product_name = board_infos.get('产品', 'xx')
    board_type = board_infos.get('板卡类型', 'xx')
    board_business_model = board_infos.get('单板业务模型', 'xx')
    board_name = board_infos.get('board', '')
    # 提取参数
    create_flag, page_url = create_icenter_page(product_name, board_type, board_business_model, board_name, board_infos, employ_no=employ_no, token=token, type='board', request_type='new')
    factor_type_cn = '单板方案链接' 
    board_data_list = []
    if not create_flag:
        board_data_list.append(board_name)
       
    if page_url:
        baseBoardTreeDatas = db.session.query(BOARD_TREE_TABLE).filter(and_(BOARD_TREE_TABLE.board_name == board_name,
                                                                                          BOARD_TREE_TABLE.factor_type_cn == factor_type_cn
                                                                          )).all()
        if len(baseBoardTreeDatas) > 0:
            update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name == board_name, 
                                                                BOARD_TREE_TABLE.factor_type_cn == factor_type_cn
                                                                )).values(factor_value=page_url, current_status=normal, 
                                                              update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            db.session.execute(update_sql)
        else:
            insert_sql = insert(BOARD_TREE_TABLE).values(board_name=board_name,
                                                        factor_type_cn=factor_type_cn, factor_value=page_url,  current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
            db.session.execute(insert_sql)
    db.session.commit()
     
    return jsonify({"code": 200, "status": "success", "message": "新增iCenter页面成功", "data": board_data_list})


def updateBoardIcenterPage():
    """
    读取空间2.0最新的模版内容，来更新指定的单板方案iCenter页面内容
    ---
    tags:
      - 单板树
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
            board:
              type: string
              description: 单板名称
          example:   # 示例值
            board: "M1BSO(80CDH),M1C2H(80B8H)"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    body_params = request.get_json()
    # 提取参数
    # boardTreeData = BoardTreeData(**body_params)    
    board_infos = querySrcBoardTreeByParams(body_params, markdown_flag=True)
    for board_info in board_infos:
        product_name = board_info.get('产品', 'xx')
        board_type = board_info.get('板卡类型', 'xx')
        board_business_model = board_info.get('单板业务模型', 'xx')
        board_name = board_info.get('board', '')
    
        update_icenter_page(product_name, board_type, board_business_model, board_name, employ_no, token, type='board', request_type='new')
     
    return jsonify({"code": 200, "status": "success", "message": "读取空间2.0最新的模版内容，来更新指定的单板方案iCenter页面内容成功", "data": []})

def syncBoardIcenterPage():
    """
    从空间2.0同步指定的单板方案iCenter页面url到前端页面
    ---
    tags:
      - 单板树
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
            data_type: "board"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    results = query_icenter_page(body_params.get("data_type", ""))
    factor_type_cn = '单板方案链接'
    board_list = []
    for result in results:
        board_name = result["board_name"]
        board_list.append(board_name)
        board_content_link = result["board_content_link"]
        update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name.like(f'%{board_name}%'), 
                                                        BOARD_TREE_TABLE.factor_type_cn == factor_type_cn,
                                                        BOARD_TREE_TABLE.effective_flag == 'Y')
                                                                       ).values(factor_value=board_content_link,  
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)

        db.session.execute(update_sql)
    db.session.commit()
    board_names = db.session.query(BOARD_TREE_TABLE.board_name).group_by(BOARD_TREE_TABLE.board_name).all()
    for board_name in board_names:
        src_board_name = board_name[0]
        new_board_name = pub_remove_after_parentheses(src_board_name)
        if new_board_name not in board_list:
            update_sql = update(BOARD_TREE_TABLE).where(and_(BOARD_TREE_TABLE.board_name == src_board_name, 
                                                        BOARD_TREE_TABLE.factor_type_cn == factor_type_cn,
                                                        BOARD_TREE_TABLE.effective_flag == 'Y')
                                                                       ).values(factor_value='', 
                                                             update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            db.session.execute(update_sql)
       
    db.session.commit()
     
    return jsonify({"code": 200, "status": "success", "message": "同步iCenter 2.0页面url到前端页面成功", "data": []})


def query_board_tree_board_design_url_by_board_name(board_name):
    object_model = db.session.query(BOARD_TREE_TABLE).filter(
        BOARD_TREE_TABLE.board_name == board_name,
        BOARD_TREE_TABLE.factor_type_cn == "单板方案链接",
        BOARD_TREE_TABLE.effective_flag == "Y"
    ).first()
    board_design_url = ""
    if object_model:
        board_design_url = object_model.factor_value
    if not board_design_url:
        logger.info(f"{board_name}对应的单板方案链接为空")
        board_design_url = "单板方案缺失"
    return board_design_url
    
