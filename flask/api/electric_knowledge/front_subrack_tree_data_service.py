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

from electric_knowledge.data_model import db, SUBRACK_TREE_TABLE
from electric_knowledge.front_business_coreelement_factor_relation_data_service import querySrcCoreElementFactorValueDict
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

extra_columns = ["shelf", "status", "create_time", "update_time", "operator_person", "effective_flag"]

# 定义查询参数模型
class ShelfTreeData(BaseModel):
    id: Optional[str] = None
    subrack_name: Optional[str] = Field(None, alias="shelf")
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

def querySrcShelfTreeByParams(query_params: dict={}, markdown_flag:bool=False):    # 构建基础查询
    conditions = [SUBRACK_TREE_TABLE.effective_flag == 'Y']
    shelfTreeData = ShelfTreeData(**query_params)
    if shelfTreeData.subrack_name:
        conditions.append(SUBRACK_TREE_TABLE.subrack_name.in_(shelfTreeData.subrack_name.split(',')))
    if shelfTreeData.factor_type_cn:
        conditions.append(SUBRACK_TREE_TABLE.factor_type_cn.in_(shelfTreeData.factor_type_cn.split(',')))
    if shelfTreeData.factor_type_en:
        conditions.append(SUBRACK_TREE_TABLE.factor_type_en.in_(shelfTreeData.factor_type_en.split(',')))
    if shelfTreeData.factor_value:
        conditions.append(SUBRACK_TREE_TABLE.factor_value.in_(shelfTreeData.factor_value.split(',')))
    if shelfTreeData.current_status:
        conditions.append(SUBRACK_TREE_TABLE.current_status.in_(shelfTreeData.current_status.split(',')))
    try:
        baseShelfTreeDatas = db.session.query(SUBRACK_TREE_TABLE).filter(and_(*conditions)).order_by(SUBRACK_TREE_TABLE.subrack_name, SUBRACK_TREE_TABLE.factor_type_cn, SUBRACK_TREE_TABLE.factor_type_en, SUBRACK_TREE_TABLE.factor_value).all() 
        results = []
        tmp_dict = dict()
        tmp_item = dict()
        prev_subrack_name = ''
        for item in baseShelfTreeDatas:
            tmp_item = ShelfTreeData.model_validate(item).model_dump(by_alias=True)
            if  prev_subrack_name and tmp_item['shelf'] != prev_subrack_name:
                prev_tmp_item.pop('factorTypeCn', None)
                prev_tmp_item.pop('factorTypeEn', None)
                prev_tmp_item.pop('factorValue', None)
                results.append(copy.deepcopy({**prev_tmp_item, **tmp_dict}))
                tmp_dict = dict()
            prev_subrack_name = tmp_item['shelf']
            prev_tmp_item = copy.deepcopy(tmp_item)
            tmp_dict[tmp_item['factorTypeCn']] = tmp_item['factorValue']
        if tmp_item:
            tmp_item.pop('factorTypeCn', None)
            tmp_item.pop('factorTypeEn', None)
            tmp_item.pop('factorValue', None)
            results.append(copy.deepcopy({**tmp_item, **tmp_dict}))
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        return ([], 400)
    
# 子架树
def queryShelfTreeByParams():    # 构建基础查询
    """
    查询指定的子架树取值
    ---
    tags:
      - 子架树
    description: 查询指定的子架树取值
    parameters:
      - name: shelf
        in: query
        description: 子架名称
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
                "shelf": "子架1",
                "产品因子": "19700产品",
                "部件承载电层业务模式因子": "FRM部件_承载电层业务,光模块部件_承载电层业务,FPGA部件承载_电层业务+FRM部件承载_电层业务",
                "子架配置类型因子": "FlexO(0x01)",
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
    results, code = querySrcShelfTreeByParams(query_params)
    if code == 200:
        message = "获取成功"
    else:
        message = "获取失败"
    return jsonify({"code": code, "status": "success", "message": message, "data": results})

def queryShelfTreeFactorList():    # 构建基础查询
    """
    查询子架树全部因子类型列表
    ---
    tags:
      - 子架树
    description: 查询子架树全部因子类型列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {
        "code": 200,
        "message": "获取成功",
        "status": "success",
        "data": ["产品因子", "部件承载电层业务模式因子", "子架配置类型因子", "物理端口数量因子", "客户侧光层业务因子", "线路侧光层业务因子"]
    }
    """
    conditions = [SUBRACK_TREE_TABLE.effective_flag == 'Y']
    query_params = request.args.to_dict()
    shelfTreeData = ShelfTreeData(**query_params)
    query = db.session.query(SUBRACK_TREE_TABLE.factor_type_cn).filter(and_(*conditions)).group_by(SUBRACK_TREE_TABLE.factor_type_cn)
    baseShelfFactorTypeDatas = query.all()
    result = []
    for baseShelfFactorTypeData in baseShelfFactorTypeDatas:
        result.append(baseShelfFactorTypeData[0])
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": list(set(result))})


def querySrcShelfTreeFactorValueDict(query_params:dict={}, factor_list_flag:bool=False):    # 构建基础查询
    shelfTreeData = ShelfTreeData(**query_params)
    conditions = [SUBRACK_TREE_TABLE.effective_flag == 'Y']
    if factor_list_flag:
        factor_list = db.session.query(SUBRACK_TREE_TABLE.factor_type_cn).filter(and_(*conditions)).group_by(SUBRACK_TREE_TABLE.factor_type_cn).all()
        return factor_list
    conditions.append(SUBRACK_TREE_TABLE.current_status.is_not(None))
    d_values = literal_column(
    f"GROUP_CONCAT(DISTINCT {SUBRACK_TREE_TABLE.factor_value.key} SEPARATOR ',')").label('factor_values')
    baseShelfStatusDatas = db.session.query(SUBRACK_TREE_TABLE.factor_type_cn, d_values).filter(and_(*conditions)).group_by(SUBRACK_TREE_TABLE.factor_type_cn).all()
    result = {}
    for item in baseShelfStatusDatas:
        result[item[0]] = list(set(item[1].split(',')))
    baseShelfStatusDatas_shelf = db.session.query(SUBRACK_TREE_TABLE.subrack_name).filter(and_(*conditions)).group_by(SUBRACK_TREE_TABLE.subrack_name).all()
    result["shelf"] = []
    for item in baseShelfStatusDatas_shelf:
        result["shelf"].append(item[0])
    baseShelfStatusDatas_status = db.session.query(SUBRACK_TREE_TABLE.current_status).filter(and_(*conditions)).group_by(SUBRACK_TREE_TABLE.current_status).all()
    result["status"] = []
    for item in baseShelfStatusDatas_status:
        result["status"].append(item[0])
    return result

def queryShelfTreeFactorValueDict():    # 构建基础查询
    """
    查询子架树的全部因子对应的取值列表
    ---
    tags:
      - 子架树
    description: 查询子架树的全部因子对应的取值列表
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": ['11', '22']}
    """
    query_params = request.args.to_dict()
    result = querySrcShelfTreeFactorValueDict(query_params)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": result})

def syncUpdateCoreelementFactorRelation(new_operator_person:str):
    from electric_knowledge.front_business_coreelement_factor_relation_data_service import updateSrcSourceCoreElementFactorRelationData
    params_dict = {"elementType": "单板", "element": "单板产品形态要素", "factorType": "单板支持的子架因子"}
    updateSrcSourceCoreElementFactorRelationData(params_dict, new_operator_person)

def addShelfTreeData():
    """
    新增指定的子架树取值
    ---
    tags:
      - 子架树
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
          required: [shelf]
          properties:
            shelf:
              type: string
              description: 子架名称
          example:   # 示例值
            shelf: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功新增数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    query_params = {"core_element_type": "子架"}
    factor_dict, code = querySrcCoreElementFactorValueDict(query_params)
    factor_dict_list = list(factor_dict.keys())
    # 提取参数
    for key, value in body_params.items():
        if key in factor_dict_list:
            factor_type_cn = key
            factor_value = value
            # 检查新增的数据在数据表中是否已存在
            insert_sql = insert(SUBRACK_TREE_TABLE).values(subrack_name=body_params["shelf"], factor_type_cn=factor_type_cn, factor_value=factor_value,  current_status=check_add,create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                           update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
            db.session.execute(insert_sql)
    db.session.commit()
    db.session.refresh(db.session.query(SUBRACK_TREE_TABLE).first())
    syncUpdateCoreelementFactorRelation(new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "新增成功", "data": []})

def updateShelfTreeData():
    """
    更新指定的子架树取值
    ---
    tags:
      - 子架树
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
          required: [shelf]
          properties:
            shelf:
              type: string
              description: 子架名称
          example:   # 示例值
            shelf: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    query_params = {"core_element_type": "子架"}
    factor_dict, code = querySrcCoreElementFactorValueDict(query_params)
    factor_dict_list = list(factor_dict.keys())
    subrack_name = body_params["shelf"]
    for key, value in body_params.items():
        if key in factor_dict_list:
            factor_type_cn = key
            factor_value = value
        # 检查新增的数据在数据表中是否已存在
            update_sql = update(SUBRACK_TREE_TABLE).where(and_(SUBRACK_TREE_TABLE.subrack_name == subrack_name, SUBRACK_TREE_TABLE.factor_type_cn == factor_type_cn, SUBRACK_TREE_TABLE.effective_flag == 'Y')
                                                                              ).values(
                                                                    factor_value=factor_value , current_status=check_update, 
                                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
            
            db.session.execute(update_sql)
    db.session.commit()
    db.session.refresh(db.session.query(SUBRACK_TREE_TABLE).first())
    syncUpdateCoreelementFactorRelation(new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "修改成功", "data": []})

def deleteShelfTreeData():
    """
    删除指定的子架树取值
    ---
    tags:
      - 子架树
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
          required: [shelf]
          properties:
            shelf:
              type: string
              description: 子架名称
          example:   # 示例值
            shelf: "M1EGEP(7096H)"
    responses:
      200:
        description: 成功更新数据
    """
    employ_no = request.headers.get('X-Emp-No')
    new_operator_person = pub_get_employ_name(employ_no)
    body_params = request.get_json()
    # 提取参数
    shelfTreeData = ShelfTreeData(**body_params)
    # 提取参数
    subrack_name = shelfTreeData.subrack_name
    # 检查新增的数据在数据表中是否已存在
    delete_count = db.session.query(SUBRACK_TREE_TABLE).where(SUBRACK_TREE_TABLE.subrack_name.in_(subrack_name.split(','))).delete()
    # 创建新用户 
    db.session.commit()
    syncUpdateCoreelementFactorRelation(new_operator_person)
    return jsonify({"code": 200, "status": "success", "message": "删除成功", "data": []})

def importExcelShelfTreeData():
    """
    Excel文件上传接口
    ---
    tags:
      - 子架树
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
        query_params = {"core_element_type": "子架"}
        factor_dict, code = querySrcCoreElementFactorValueDict(query_params)
        columns_to_iterate = [col for col in df.columns if col.replace("\n", "") in list(factor_dict.keys()) and col.replace("\n", "") != '子架名称']
        # 数据库操作
        for _, row in df.iterrows():
            for columns in columns_to_iterate:
                table_dict = dict()
                # 假设 Excel 表头与数据库字段名一致
                table_dict['subrack_name'] = row["子架名称"] if "子架名称" in row else '' 
                table_dict['factor_type_en'] = ''
                table_dict['factor_type_cn'] = columns.replace("\n", "")
                table_dict['factor_value'] = row[columns]
            
                db_factor_values = db.session.query(SUBRACK_TREE_TABLE).filter(and_(SUBRACK_TREE_TABLE.subrack_name == table_dict['subrack_name'],
                                                                                          SUBRACK_TREE_TABLE.factor_type_cn == table_dict["factor_type_cn"]
                                                                          )).all()
                if len(db_factor_values) > 0 and row["子架名称"] and row[columns]:
                    update_sql = update(SUBRACK_TREE_TABLE).where(and_(SUBRACK_TREE_TABLE.subrack_name == table_dict['subrack_name'],
                                                                                          SUBRACK_TREE_TABLE.factor_type_cn == table_dict["factor_type_cn"]
                                                                          )).values(factor_value=table_dict['factor_value'], current_status=check_update,
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
                    db.session.execute(update_sql)
                else:
                    insert_sql = insert(SUBRACK_TREE_TABLE).values(subrack_name=table_dict['subrack_name'], 
                                                                                  factor_type_cn=table_dict["factor_type_cn"], 
                                                                factor_value=table_dict["factor_value"], current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
                    db.session.execute(insert_sql)
                    # 创建新用户 
            db.session.commit()

        db.session.refresh(db.session.query(SUBRACK_TREE_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
        # raise HTTPException(status_code=500, detail=f"处理文件失败: {str(e)}")
    