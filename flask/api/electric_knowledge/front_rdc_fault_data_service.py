from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import pandas as pd

from electric_knowledge.data_model import db, RDC_FAULT_TABLE
from flask import request, jsonify


# 定义查询参数模型
class RdcFaultTableData(BaseModel):
    id: Optional[int] = None
    rdc_ident: Optional[str] = None
    rdc_title: Optional[str] = None
    related_board_name: Optional[str] = None
    related_rdc_ident: Optional[str] = None
    rdc_created_by: Optional[str] = None
    rdc_created_time: Optional[str] = None
    rdc_changed_by: Optional[str] = None
    rdc_changed_time: Optional[str] = None
    rdc_field: Optional[str] = None
    rdc_team: Optional[str] = None
    rdc_introducted_by: Optional[str] = None
    requirement_status: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def queryRdcFaultByRdcIdent():
    """
    根据RDC编号查询对应的故障详情
    ---
    tags:
      - 单板全局状态
    description: 根据RDC编号查询对应的故障详情记录
    parameters:
      - name: rdc_ident
        in: query
        description: RDC编号
        required: true
        type: string
    responses:
      200:
        description: 成功返回RDC故障详情数据
        examples:
          application/json: {
            "code": 200, 
            "status": "success", 
            "message": "获取成功", 
            "data": [
              {
                "id": 1,
                "rdc_ident": "RDC001",
                "rdc_title": "故障标题1",
                "related_board_name": "单板A",
                "related_rdc_ident": "PR123",
                "rdc_created_by": "张三",
                "rdc_created_time": "2023-01-01",
                "rdc_changed_by": "李四",
                "rdc_changed_time": "2023-01-02",
                "rdc_field": "字段1",
                "rdc_team": "团队A",
                "rdc_introducted_by": "王五",
                "requirement_status": "进行中",
                "update_time": "2023-01-02 10:00:00"
              }
            ]
          }
    """
    query_params = request.args.to_dict()
    related_rdc_ident = query_params.get("rdc_ident")
    if not related_rdc_ident:
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": []})
    # 根据 related_rdc_ident 查询所有匹配的记录
    matching_records = db.session.query(RDC_FAULT_TABLE).filter(
        RDC_FAULT_TABLE.related_rdc_ident == related_rdc_ident
    ).all()
    # 将每个 SQLAlchemy 模型对象转换为字典
    result_list = []
    for record in matching_records:
        record_dict = {key: value for key, value in record.__dict__.items() if not key.startswith('_')}
        result_list.append(record_dict)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result_list})


def deleteRdcFaultByBoardName(board_name: str):
    """根据单板名称删除RDC故障记录"""
    if not board_name: 
        return 0
    # 删除相关记录
    db.session.query(RDC_FAULT_TABLE).filter(
        RDC_FAULT_TABLE.related_board_name == board_name
    ).delete()
    db.session.commit()
    return 0


def insertRdcFaultData(body_params_list: List[dict]):
    """批量插入RDC故障记录"""
    for body_params in body_params_list:
        rdc_data = RdcFaultTableData(**body_params)
        # 提取字段
        rdc_ident = rdc_data.rdc_ident
        rdc_title = rdc_data.rdc_title
        related_board_name = rdc_data.related_board_name
        related_rdc_ident = rdc_data.related_rdc_ident
        rdc_created_by = rdc_data.rdc_created_by
        rdc_created_time = rdc_data.rdc_created_time
        rdc_changed_by = rdc_data.rdc_changed_by
        rdc_changed_time = rdc_data.rdc_changed_time
        rdc_field = rdc_data.rdc_field
        rdc_team = rdc_data.rdc_team
        rdc_introducted_by = rdc_data.rdc_introducted_by
        requirement_status = rdc_data.requirement_status
        # 检查是否存在相同 rdc_ident
        existing = db.session.query(RDC_FAULT_TABLE).filter(RDC_FAULT_TABLE.rdc_ident == rdc_ident).first()
        if existing:
            # 如果存在，则删除旧记录
            db.session.delete(existing)
            db.session.commit()
        # 插入新记录
        insert_stmt = insert(RDC_FAULT_TABLE).values(
            rdc_ident=rdc_ident,
            rdc_title=rdc_title,
            related_board_name=related_board_name,
            related_rdc_ident=related_rdc_ident,
            rdc_created_by=rdc_created_by,
            rdc_created_time=rdc_created_time,
            rdc_changed_by=rdc_changed_by,
            rdc_changed_time=rdc_changed_time,
            rdc_field=rdc_field,
            rdc_team=rdc_team, 
            rdc_introducted_by=rdc_introducted_by,
            requirement_status=requirement_status,
            update_time=datetime.now()
        )
        db.session.execute(insert_stmt)
    db.session.commit()
    # 刷新会话
    first_record = db.session.query(RDC_FAULT_TABLE).first()
    if first_record:
        db.session.refresh(first_record)
    return 0


def addRdcFaultTableData(body_params_list: List[dict]):
    """
    新增RDC故障表数据
    1. 检查是否有related_board_name相同的数据库记录
    2. 如果有，先删除相关的所有记录
    3. 再新增所有记录
    """
    if len(body_params_list) == 0:
        return 0
    # 获取单板名称（所有元素的related_board_name都相同）
    board_name = body_params_list[0].get("related_board_name")
    if board_name:
        # 1. 查询现有记录
        existing_records = db.session.query(RDC_FAULT_TABLE).filter(
            RDC_FAULT_TABLE.related_board_name == board_name
        ).all()
        # 2. 如果存在相关记录，先删除
        if existing_records:
            print(f"----------单板：{board_name} 已存在记录，先删除后新增")
            deleteRdcFaultByBoardName(board_name)
    # 3. 批量插入新记录
    result = insertRdcFaultData(body_params_list)
    return result


def queryRdcFaultListByRdcIdentList(rdc_list: list):
    try:
        model_list = db.session.query(RDC_FAULT_TABLE).filter(RDC_FAULT_TABLE.related_rdc_ident.in_(rdc_list)).all()
        return [RdcFaultTableData.model_validate(model_item).model_dump() for model_item in model_list]
    except Exception as e:
        print(f"查询异常：{str(e)}")
        return []