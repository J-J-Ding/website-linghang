import logging
import pandas as pd

from typing import Optional
from datetime import datetime
from fastapi import HTTPException
from flask import request, jsonify
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func, literal_column

from electric_knowledge.utils_pub import pub_get_employ_name
from electric_knowledge.data_model import db, FEATURE_CHANGE_RELATION_TABLE, FEATURE_RELATION_TABLE


logger = logging.getLogger("Logger")


check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'


# 定义查询参数模型
class FeatureChangeRelationData(BaseModel):
    id: Optional[str] = None
    feature_first_classification: Optional[str] = Field(None, alias="featureFirstType")
    feature_second_classification: Optional[str] = Field(None, alias="featureSecondType")
    feature_name: Optional[str] = Field(None, alias="feature")
    children_feature_name: Optional[str] = Field(None, alias="subFeature")
    related_change: Optional[str] = Field(None, alias="relatedChange")
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


def querySrcFeatureChangeRelation(change):
    """
    查询特性变更关系数据

    Args:
        change (str): 变更类型，多个值用逗号分隔

    Returns:
        list: 包含特性信息的字典列表
    """
    # 构建基础查询条件：只查询有效且有关联的记录
    conditions = [
        FEATURE_CHANGE_RELATION_TABLE.effective_flag == 'Y',
        FEATURE_CHANGE_RELATION_TABLE.related_flag > '0.0'
    ]
    # 如果提供了变更类型参数，添加到查询条件中
    if change.strip():
        conditions.append(FEATURE_CHANGE_RELATION_TABLE.related_change.in_(change.split(',')))
    # 构造聚合字段：将同一特性的多个变更类型合并为逗号分隔的字符串
    related_changes_agg = literal_column(f"GROUP_CONCAT(DISTINCT {FEATURE_CHANGE_RELATION_TABLE.related_change.key} SEPARATOR ',')").label('related_changes')
    # 执行数据库查询
    src_results = db.session.query(
        # 特性分类信息
        FEATURE_CHANGE_RELATION_TABLE.feature_first_classification,
        FEATURE_CHANGE_RELATION_TABLE.feature_second_classification,
        FEATURE_CHANGE_RELATION_TABLE.feature_name,
        FEATURE_CHANGE_RELATION_TABLE.children_feature_name,
        # 关联的特性详细信息
        FEATURE_RELATION_TABLE.description,
        FEATURE_RELATION_TABLE.acceptance_criteria,
        FEATURE_RELATION_TABLE.feature_content_link,
        FEATURE_RELATION_TABLE.belong_team,
        FEATURE_RELATION_TABLE.estimated_dev_workload,
        FEATURE_RELATION_TABLE.requirement_sort,
        # 聚合后的变更类型
        related_changes_agg
    ).join(
        # 左连接特性关系表
        FEATURE_RELATION_TABLE,
        and_(
            FEATURE_CHANGE_RELATION_TABLE.feature_name == FEATURE_RELATION_TABLE.feature_name,
            FEATURE_CHANGE_RELATION_TABLE.children_feature_name == FEATURE_RELATION_TABLE.children_feature_name
        ),
        isouter=True
    ).filter(
        and_(*conditions)
    ).group_by(
        # 按所有非聚合字段分组
        FEATURE_CHANGE_RELATION_TABLE.feature_first_classification,
        FEATURE_CHANGE_RELATION_TABLE.feature_second_classification,
        FEATURE_CHANGE_RELATION_TABLE.feature_name,
        FEATURE_CHANGE_RELATION_TABLE.children_feature_name,
        FEATURE_RELATION_TABLE.description,
        FEATURE_RELATION_TABLE.acceptance_criteria,
        FEATURE_RELATION_TABLE.feature_content_link,
        FEATURE_RELATION_TABLE.belong_team,
        FEATURE_RELATION_TABLE.estimated_dev_workload,
        FEATURE_RELATION_TABLE.requirement_sort
    ).all()
    # 格式化查询结果
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
            "related_changes": src_result[7]
        })
    return results


def importExcelFeatureChangeData():
    """
    Excel文件上传接口
    ---
    tags:
      - 特性-变更
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
    operator_person = pub_get_employ_name(employ_no)
    # 检查文件类型
    if 'file' not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    file = request.files['file']
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
    try:
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
                print(columns)
                table_dict = dict()
                table_dict['feature_first_classification'] = row["特性一级分类"] if "特性一级分类" in row else '' 
                table_dict['feature_second_classification'] = row["特性二级分类"] if "特性二级分类" in row else '' 
                table_dict['feature_name'] = row["特性"] if "特性" in row else '' 
                table_dict['children_feature_name'] = str(row["子特性"] if "子特性" in row else '' )
                table_dict['related_change'] = columns
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
                db_factor_values = db.session.query(FEATURE_CHANGE_RELATION_TABLE).filter(and_(FEATURE_CHANGE_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                                          FEATURE_CHANGE_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                                          FEATURE_CHANGE_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                                          FEATURE_CHANGE_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"],
                                                                                          FEATURE_CHANGE_RELATION_TABLE.related_change == table_dict["related_change"])).all()
                if len(db_factor_values) > 0 and row["特性一级分类"] and row["特性二级分类"] and row["特性"] and table_dict['related_change']:
                    update_sql = update(FEATURE_CHANGE_RELATION_TABLE).where(and_(FEATURE_CHANGE_RELATION_TABLE.feature_first_classification == table_dict['feature_first_classification'],
                                                                                  FEATURE_CHANGE_RELATION_TABLE.feature_second_classification == table_dict["feature_second_classification"],
                                                                                  FEATURE_CHANGE_RELATION_TABLE.feature_name == table_dict["feature_name"],
                                                                                  FEATURE_CHANGE_RELATION_TABLE.children_feature_name == table_dict["children_feature_name"],
                                                                                  FEATURE_CHANGE_RELATION_TABLE.related_change == table_dict["related_change"]))\
                                                                       .values(related_flag=table_dict['related_flag'],
                                                                               current_status=check_update,
                                                                               update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                               operator_person=operator_person)
                    db.session.execute(update_sql)
                else:
                    insert_sql = insert(FEATURE_CHANGE_RELATION_TABLE).values(feature_first_classification=table_dict['feature_first_classification'],
                                                                              feature_second_classification=table_dict['feature_second_classification'], 
                                                                              feature_name=table_dict["feature_name"],
                                                                              children_feature_name=table_dict["children_feature_name"],
                                                                              related_change=table_dict["related_change"],
                                                                              related_flag=table_dict['related_flag'],
                                                                              current_status=check_add,
                                                                              create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                              update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                              operator_person=operator_person,
                                                                              effective_flag='Y')
                    db.session.execute(insert_sql)
        db.session.commit()
        db.session.refresh(db.session.query(FEATURE_CHANGE_RELATION_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
