from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import pandas as pd

from electric_knowledge.data_model import db, BOARD_OPT_BIZ_TABLE
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify
import logging

logger = logging.getLogger("Logger")

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BoardOptBizData(BaseModel):
    id: Optional[str] = None
    board_name: Optional[str] = Field(None, alias="board")
    l_c_type: Optional[str] = Field(None, alias="l_c_type")
    opt_value: Optional[str] = Field(None, alias="opt")
    biz_value: Optional[str] = Field(None, alias="biz")
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

def querySrcBoardOptBizByParams(query_params: dict={}, markdown_flag:bool=False, part_match_flag:bool=True):    # 构建基础查询
    conditions = [BOARD_OPT_BIZ_TABLE.effective_flag == 'Y']
    boardOptBizData = BoardOptBizData(**query_params)
    
    if boardOptBizData.board_name:
        if part_match_flag:
            like_search_str = f"%{boardOptBizData.board_name}%"
            conditions.append(BOARD_OPT_BIZ_TABLE.board_name.like(like_search_str))
        else:
            conditions.append(BOARD_OPT_BIZ_TABLE.board_name.in_(boardOptBizData.board_name.split(',')))
    if boardOptBizData.l_c_type:
        if part_match_flag:
            like_search_str = f"%{boardOptBizData.l_c_type}%"
            conditions.append(BOARD_OPT_BIZ_TABLE.l_c_type.like(like_search_str))
        else:
            conditions.append(BOARD_OPT_BIZ_TABLE.l_c_type.in_(boardOptBizData.l_c_type.split(',')))
    if boardOptBizData.opt_value:
        if part_match_flag:
            like_search_str = f"%{boardOptBizData.opt_value}%"
            conditions.append(BOARD_OPT_BIZ_TABLE.opt_value.like(like_search_str))
        else:
            conditions.append(BOARD_OPT_BIZ_TABLE.opt_value.in_(boardOptBizData.opt_value.split(',')))
            
    if boardOptBizData.biz_value:
        if part_match_flag:
            like_search_str = f"%{boardOptBizData.biz_value}%"
            conditions.append(BOARD_OPT_BIZ_TABLE.biz_value.like(like_search_str))
        else:
            conditions.append(BOARD_OPT_BIZ_TABLE.biz_value.in_(boardOptBizData.biz_value.split(',')))
    if boardOptBizData.current_status:
        conditions.append(BOARD_OPT_BIZ_TABLE.current_status.in_(boardOptBizData.current_status.split(',')))
   
    try:
        baseBoardOptBizDatas = db.session.query(BOARD_OPT_BIZ_TABLE).filter(and_(*conditions)).order_by(BOARD_OPT_BIZ_TABLE.board_name, BOARD_OPT_BIZ_TABLE.opt_value).all()
        results = [
            BoardOptBizData.model_validate(item).model_dump(by_alias=True)
            for item in baseBoardOptBizDatas
        ]
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        return ([], 400)

def queryBoardOptBizByParams():    # 构建基础查询
    """
    查询指定的单板的光模块-光层业务映射关系
    ---
    tags:
      - 单板光模块-光层业务
    description: 查询指定的单板的光模块-光层业务映射关系
    parameters:
      - name: board
        in: query
        description: 单板名称
        required: false
        type: string
      - name: l_c_type
        in: query
        description: 类型
        required: false
        type: string
      - name: opt
        in: query
        description: 光模块名称
        required: false
        type: string
      - name: biz
        in: query
        description: 光层业务
        required: false
        type: string
      - name: part_match_flag
        in: query
        description: 是否模糊匹配
        required: false
        type: boolean
      - name: status
        in: query
        description: 当前状态
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": [{}]}
    """
    query_params = request.args.to_dict()
    part_match_flag = True
    if query_params.get('part_match_flag', 'false').lower() in ('false'):
        part_match_flag = False
    results, code = querySrcBoardOptBizByParams(query_params, part_match_flag=part_match_flag)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})

def deleteSrcBoardOptBizData(boardOptBizData):
    boards = boardOptBizData.get("board", "")
    toDeleteBoards = boards.split(',')
    toDeleteBoards = [board.strip() for board in toDeleteBoards if board.strip()]

    l_c_types = boardOptBizData.get("l_c_type", "")
    toDeleteTypes = l_c_types.split(',')
    toDeleteTypes = [l_c_type.strip() for l_c_type in toDeleteTypes if l_c_type.strip()]

    opts = boardOptBizData.get("opt", "")
    toDeleteOpts = opts.split(',')
    toDeleteOpts = [opt.strip() for opt in toDeleteOpts if opt.strip()]

    bizs = boardOptBizData.get("biz", "")
    toDeleteBizs = bizs.split(',')
    toDeleteBizs = [biz.strip() for biz in toDeleteBizs if biz.strip()]
    conditions = []
    if toDeleteBoards:
        conditions.append(BOARD_OPT_BIZ_TABLE.board_name.in_(toDeleteBoards))
    if toDeleteTypes:
        conditions.append(BOARD_OPT_BIZ_TABLE.l_c_type.in_(toDeleteTypes))
    if toDeleteOpts:
        conditions.append(BOARD_OPT_BIZ_TABLE.opt_value.in_(toDeleteOpts))
    if toDeleteBizs:
        conditions.append(BOARD_OPT_BIZ_TABLE.biz_value.in_(toDeleteBizs))
    delete_count = db.session.query(BOARD_OPT_BIZ_TABLE).filter(and_(*conditions)).delete() 
    db.session.commit()


def addSrcBoardOptBizData(body_params, new_operator_person):
    # 提取参数
    boardOptBizData = BoardOptBizData(**body_params)
    board_names = boardOptBizData.board_name.split(',')
    l_c_types = boardOptBizData.l_c_type.split(',')
    opt_values = boardOptBizData.opt_value.split(',')
    biz_values = boardOptBizData.biz_value.split(',')

    # 检查新增的数据在数据表中是否已存在
    for idx, board_name in enumerate(board_names):
        l_c_type = l_c_types[idx]
        opt_value = opt_values[idx]
        biz_value = biz_values[idx]
        db_board_opt_biz_values = db.session.query(BOARD_OPT_BIZ_TABLE.board_name, BOARD_OPT_BIZ_TABLE.l_c_type).filter(and_(BOARD_OPT_BIZ_TABLE.board_name == board_name,
                                                                          BOARD_OPT_BIZ_TABLE.l_c_type == l_c_type,
                                                                          BOARD_OPT_BIZ_TABLE.opt_value == opt_value,
                                                                          BOARD_OPT_BIZ_TABLE.biz_value == biz_value)).all()
        if len(db_board_opt_biz_values) > 0:
            update_sql = update(BOARD_OPT_BIZ_TABLE).where(and_(BOARD_OPT_BIZ_TABLE.board_name == board_name,
                                                            BOARD_OPT_BIZ_TABLE.l_c_type == l_c_type,
                                                            BOARD_OPT_BIZ_TABLE.opt_value == opt_value,
                                                            BOARD_OPT_BIZ_TABLE.biz_value == biz_value
                                                                          )).values(current_status=check_update,   update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            db.session.execute(update_sql)
            db.session.commit()
            
        else:
            insert_sql = insert(BOARD_OPT_BIZ_TABLE).values(board_name=board_name, l_c_type=l_c_type, opt_value=opt_value, biz_value=biz_value,
                                                         current_status=check_add,
                                                          create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
            db.session.execute(insert_sql)

            # 创建新用户
            db.session.commit()
    db.session.refresh(db.session.query(BOARD_OPT_BIZ_TABLE).first())

def importExcelBoardOptBizData():
    """
    Excel文件上传接口
    ---
    tags:
      - 单板光模块-光层业务
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
        df = df.fillna(value='')

        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            # 假设 Excel 表头与数据库字段名一致
            table_dict['board_name'] = row["单板名称"].replace('\n', ',') if "单板名称" in row else '' 
            table_dict['l_c_type'] = row["类型"].replace('\n', ',') if "类型" in row else '' 
            table_dict['opt_value'] = row["光模块名称"] if "光模块名称" in row else '' 
            table_dict['biz_value'] = row["光层业务名称"] if "光层业务名称" in row else ''
            db_opt_biz_values = db.session.query(BOARD_OPT_BIZ_TABLE).filter(and_(BOARD_OPT_BIZ_TABLE.board_name == table_dict['board_name'],
                                                                                  BOARD_OPT_BIZ_TABLE.l_c_type == table_dict['l_c_type'],
                                                                                          BOARD_OPT_BIZ_TABLE.opt_value == table_dict["opt_value"],
                                                                                          BOARD_OPT_BIZ_TABLE.biz_value == table_dict["biz_value"]
                                                                          )).all()
            if len(db_opt_biz_values) > 0:
                update_sql = update(BOARD_OPT_BIZ_TABLE).where(and_(BOARD_OPT_BIZ_TABLE.board_name == table_dict['board_name'],
                                                                    BOARD_OPT_BIZ_TABLE.l_c_type == table_dict['l_c_type'],
                                                                          BOARD_OPT_BIZ_TABLE.opt_value == table_dict["opt_value"],
                                                                                          BOARD_OPT_BIZ_TABLE.biz_value == table_dict["biz_value"]
                                                                      )).values( current_status=check_update,
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                db.session.execute(update_sql)
            else:
                insert_sql = insert(BOARD_OPT_BIZ_TABLE).values(board_name=table_dict['board_name'], l_c_type=table_dict['l_c_type'], opt_value = table_dict["opt_value"],
                                                                biz_value = table_dict["biz_value"], current_status=normal,  create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                # 创建新用户 
            db.session.commit()
         
        db.session.refresh(db.session.query(BOARD_OPT_BIZ_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
