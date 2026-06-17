from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd
from io import BytesIO

from electric_knowledge.data_model import db, BOARD_CHANGE_ANALYSIS_TABLE
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class BoardChangeAnalysisData(BaseModel):
    id: Optional[str] = None
    board_name: Optional[str] = Field(None, alias="board")
    change_analysis_type_cn: Optional[str] = Field(None, alias="changeAnalysisTypeCn")
    change_analysis_type_en: Optional[str] = Field(None, alias="changeAnalysisTypeEn")
    change_analysis_value: Optional[str] = Field(None, alias="changeAnalysisValue")
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


def querySrcBoardChangeAnalysisByParams(query_params: dict={}, markdown_flag:bool=False):    # 构建基础查询
    conditions = [BOARD_CHANGE_ANALYSIS_TABLE.effective_flag == 'Y']
    boardChangeAnalysisData = BoardChangeAnalysisData(**query_params)
    if boardChangeAnalysisData.board_name:
        conditions.append(BOARD_CHANGE_ANALYSIS_TABLE.board_name.in_(boardChangeAnalysisData.board_name.split(',')))
    if boardChangeAnalysisData.change_analysis_type_cn:
        conditions.append(BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn.in_(boardChangeAnalysisData.change_analysis_type_cn.split(',')))
    if boardChangeAnalysisData.change_analysis_type_en:
        conditions.append(BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_en.in_(boardChangeAnalysisData.change_analysis_type_en.split(',')))
    if boardChangeAnalysisData.change_analysis_value:
        conditions.append(BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_value.in_(boardChangeAnalysisData.change_analysis_value.split(',')))
    if boardChangeAnalysisData.current_status:
        conditions.append(BOARD_CHANGE_ANALYSIS_TABLE.current_status.in_(boardChangeAnalysisData.current_status.split(',')))
    try:
        baseBoardChangeAnalysisDatas = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).filter(and_(*conditions)).order_by(BOARD_CHANGE_ANALYSIS_TABLE.board_name, BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn, BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_en, BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_value).all() 
        results = []
        tmp_dict = dict()
        tmp_item = dict()
        prev_board_name = ''
        for item in baseBoardChangeAnalysisDatas:
            tmp_item = BoardChangeAnalysisData.model_validate(item).model_dump(by_alias=True)
            if prev_board_name and tmp_item['board'] != prev_board_name:
                new_tmp_item = copy.deepcopy(tmp_item)
                new_tmp_item.pop('changeAnalysisTypeCn', None)
                new_tmp_item.pop('changeAnalysisTypeEn', None)
                new_tmp_item.pop('changeAnalysisValue', None)
                new_tmp_item['board'] = prev_board_name
                results.append(copy.deepcopy({**new_tmp_item, **tmp_dict}))
                tmp_dict = dict()
            
            tmp_dict[tmp_item['changeAnalysisTypeCn']] = tmp_item['changeAnalysisValue']
            prev_board_name = tmp_item['board']
        if tmp_item:
            tmp_item.pop('changeAnalysisTypeCn', None)
            tmp_item.pop('changeAnalysisTypeEn', None)
            tmp_item.pop('changeAnalysisValue', None)
            results.append(copy.deepcopy({**tmp_item, **tmp_dict}))
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        return ([], 400)


def queryBoardTreeFactorList():    # 构建基础查询
    """
    查询单板变更分析全部变更分析类型列表
    ---
    tags:
      - 单板变更分析
    description: 查询单板变更分析全部变更分析类型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
        "code": 200,
        "message": "获取成功",
        "status": "success",
        "data": ["产品因子", "部件承载电层业务模式因子", "单板配置类型因子", "物理端口数量因子", "客户侧光层业务因子", "线路侧光层业务因子"]
    }
    """
    conditions = [BOARD_CHANGE_ANALYSIS_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    boardChangeAnalysisData = BoardChangeAnalysisData(**query_params)
    query = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn).filter(and_(*conditions)).group_by(BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn)
    baseBoardFactorTypeDatas = query.all()
    result = []
    for baseBoardFactorTypeData in baseBoardFactorTypeDatas:
        result.append(baseBoardFactorTypeData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def updateSrcBoardChangeAnalysisData(body_params:dict={}, employ_no:str='10251481', markdown_flag:bool=False):
    # 提取参数
    boardChangeAnalysisData = BoardChangeAnalysisData(**body_params)
    # 提取参数
    id = boardChangeAnalysisData.id
    board_name = boardChangeAnalysisData.board_name
    change_analysis_type_cn = boardChangeAnalysisData.change_analysis_type_cn
    change_analysis_type_en = boardChangeAnalysisData.change_analysis_type_en
    change_analysis_value = boardChangeAnalysisData.change_analysis_value
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    try:
        update_sql = update(BOARD_CHANGE_ANALYSIS_TABLE).where(and_(BOARD_CHANGE_ANALYSIS_TABLE.board_name == board_name, BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn == change_analysis_type_cn, BOARD_CHANGE_ANALYSIS_TABLE.effective_flag == 'Y')
                                                                          ).values(change_analysis_value=change_analysis_value, 
                                                                current_status=check_update, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        
        db.session.execute(update_sql)
        db.session.commit()
        db.session.refresh(db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).first())
        if markdown_flag:
            return 200
        return ([], 200)
    except Exception as e:
        if markdown_flag:
            return 400
        return ([], 400)

def addSrcBoardChangeAnalysisData(body_params:dict={}, employ_no:str='10251481', markdown_flag:bool=False):
    board = ''
    if body_params:
        board = body_params.get('board', '')
    if not board:
        print(f"--------没有传入单板名称！")
        return ([], 400)
    # 检查新增的数据在数据表中是否已存在
    new_operator_person = pub_get_employ_name(employ_no)
    body_params.pop('board', None)
    try:
        for key, value in body_params.items():
            tmp_data = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).filter(and_(BOARD_CHANGE_ANALYSIS_TABLE.board_name == board, BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn == key, BOARD_CHANGE_ANALYSIS_TABLE.effective_flag == 'Y')).all()
            if len(tmp_data) > 0:
                print(f"--------插入的单板和因子类型已存在，本次新增操作变为更新操作！")
                updateSrcBoardChangeAnalysisData({"board": board, "changeAnalysisTypeCn":key, "changeAnalysisValue":value})
            else:
                insert_sql = insert(BOARD_CHANGE_ANALYSIS_TABLE).values(board_name=board, change_analysis_type_cn=key,
                                                                        change_analysis_value=value, current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                db.session.execute(insert_sql)
                db.session.commit()
        db.session.refresh(db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).first())
        if markdown_flag:
            return 200
        return ([], 200)
    except Exception as e:
        if markdown_flag:
            return 400
        return ([], 400)


def importExcelBoardChangeAnalysisData():
    """
    Excel文件上传接口
    ---
    tags:
      - 单板变更分析
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
        # df.iloc[:, 1] = df.iloc[:, 1].ffill()
        # df.iloc[:, 2] = df.iloc[:, 2].ffill()
        # df.iloc[:, 3] = df.iloc[:, 3].ffill()
        df = df.fillna(value='')
        # df['特性一级分类'] = df['特性一级分类'].astype(str) 
        columns_to_iterate = [col for col in df.columns if col not in ['ID', '单板标识']]

        # 数据库操作
        for _, row in df.iterrows():
            for columns in columns_to_iterate:
                table_dict = dict()
                # 假设 Excel 表头与数据库字段名一致
                table_dict['board_name'] = row["单板标识"] if "单板标识" in row else '' 
                table_dict['change_analysis_type_en'] = ''
                table_dict['change_analysis_type_cn'] = columns.replace("\n", "")
                table_dict['change_analysis_value'] = row[columns.replace("\n", "")]
            
                db_change_analysis_values = db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).filter(and_(BOARD_CHANGE_ANALYSIS_TABLE.board_name == table_dict['board_name'],
                                                                                          BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn == table_dict["change_analysis_type_cn"]
                                                                          )).all()
                if len(db_change_analysis_values) > 0 and row["单板标识"] and row[columns.replace("\n", "")]:
                    update_sql = update(BOARD_CHANGE_ANALYSIS_TABLE).where(and_(BOARD_CHANGE_ANALYSIS_TABLE.board_name == table_dict['board_name'],
                                                                                          BOARD_CHANGE_ANALYSIS_TABLE.change_analysis_type_cn == table_dict["change_analysis_type_cn"]
                                                                          )).values(change_analysis_value=table_dict['change_analysis_value'], current_status=check_update,
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                    db.session.execute(update_sql)
                else:
                    insert_sql = insert(BOARD_CHANGE_ANALYSIS_TABLE).values(board_name=table_dict['board_name'], 
                                                                                  change_analysis_type_cn=table_dict["change_analysis_type_cn"], 
                                                                change_analysis_value=table_dict["change_analysis_value"], current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                    db.session.execute(insert_sql)
                    # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(BOARD_CHANGE_ANALYSIS_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")
    