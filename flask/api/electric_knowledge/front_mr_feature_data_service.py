from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, func
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union  # 始终导入这些类型
import json
import copy
import pandas as pd

from electric_knowledge.data_model import db, MR_INFO_TABLE
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify
import logging

logger = logging.getLogger("Logger")

check_update = '审核中-修改'
check_add = '审核中-新增'
check_delete = '审核中-删除'
normal = '正常'

# 定义查询参数模型
class MrFeatureData(BaseModel):
    id: Optional[str] = None
    belong_domain: Optional[str] = None
    depend_belong_domain: Optional[str] = None
    team: Optional[str] = None
    belong_product: Optional[str] = Field(None, alias="belongProduct")
    related_type: Optional[str] = Field(None, alias="relatedType")
    workitem_type: Optional[str] = Field(None, alias="workitemType")
    workitem_id: Optional[str] = Field(None, alias="workitemId")
    workitem_status: Optional[str] = Field(None, alias="workitemStatus")
    title: Optional[str] = Field(None, alias="mr_title")
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = Field(None, alias="acceptanceCriteria")
    product_roadmap: Optional[str] = Field(None, alias="productRoadmap")
    related_requirement_preplanning_version: Optional[str] = Field(None, alias="relatedRequirementPreplanning")
    specification_by_example_url: Optional[str] = Field(None, alias="specificationByExampleUrl")
    design_specification_url: Optional[str] = Field(None, alias="designSpecificationUrl")
    requirement_source: Optional[str] = Field(None, alias="requirementSource")
    requirement_submitter: Optional[str] = Field(None, alias="requirementSubmitter")
    expected_finish_date: Optional[str] = Field(None, alias="expectedFinishDate")
    requirement_purpose: Optional[str] = Field(None, alias="requirementPurpose")
    priority: Optional[str] = Field(None, alias="priority")
    is_medium_long_term_requirement: Optional[str] = Field(None, alias="IsMediumLongTermRequirement")
    is_competitive_requirement: Optional[str] = Field(None, alias="IsCompetitiveRequirement")
    is_key_requirement: Optional[str] = Field(None, alias="IsKeyRequirement")
    is_chip_requirement: Optional[str] = Field(None, alias="IsChipRequirement")
    requirement_category: Optional[str] = Field(None, alias="requirementCategory")
    market_target: Optional[str] = Field(None, alias="marketTarget")
    target_market: Optional[str] = Field(None, alias="targetMarket")
    customer: Optional[str] = None
    belong_feature_category: Optional[str] = Field(None, alias="belongFeatureCategory")
    requirement_type: Optional[str] = Field(None, alias="requirementType")
    verification_mode: Optional[str] = Field(None, alias="verificationMode")
    verification_team: Optional[str] = Field(None, alias="verificationTeam")
    related_sub_features: Optional[str] = Field(None, alias="relatedSubFeatures")
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

def querySrcMrFeatureByParams(query_params: dict={}, markdown_flag:bool=False, part_match_flag:bool=True):    # 构建基础查询
    conditions = [MR_INFO_TABLE.effective_flag == 'Y']
    mrFeatureData = MrFeatureData(**query_params)
    if mrFeatureData.belong_domain:
        conditions.append(MR_INFO_TABLE.belong_domain == mrFeatureData.belong_domain)
    if mrFeatureData.title:
        if part_match_flag:
            like_search_str = f"%{mrFeatureData.title}%"
            conditions.append(MR_INFO_TABLE.title.like(like_search_str))
        else:
            conditions.append(MR_INFO_TABLE.title.in_(mrFeatureData.title.split(',')))
    if mrFeatureData.current_status:
        conditions.append(MR_INFO_TABLE.current_status.in_(mrFeatureData.current_status.split(',')))
    try:
        baseMrFeatureDatas = db.session.query(MR_INFO_TABLE).filter(and_(*conditions)).order_by(MR_INFO_TABLE.title).all()
        results = [
            MrFeatureData.model_validate(item).model_dump(by_alias=True)
            for item in baseMrFeatureDatas
        ]
        if markdown_flag:
            return results
        return (results, 200)
    except Exception as e:
        return ([], 400)

def mr_info_to_db(pre_table_dict, related_sub_features, new_operator_person):
    pre_table_dict['related_sub_features'] = ','.join(list(set(related_sub_features)))
    db_mr_values = db.session.query(MR_INFO_TABLE).filter(MR_INFO_TABLE.title == pre_table_dict['title']
                                                      ).all()
    if len(db_mr_values) > 0:
        update_sql = update(MR_INFO_TABLE).where(MR_INFO_TABLE.title == pre_table_dict['title']                 
                                                              ).values(
                                                    belong_domain=pre_table_dict['belong_domain'], depend_belong_domain=pre_table_dict['depend_belong_domain'], 
                                                    team=pre_table_dict["team"], belong_product=pre_table_dict["belong_product"], related_type=pre_table_dict["related_type"], 
                                                    workitem_type=pre_table_dict["workitem_type"], workitem_id=pre_table_dict["workitem_id"], workitem_status=pre_table_dict["workitem_status"], 
                                                    description=pre_table_dict["description"], acceptance_criteria=pre_table_dict["acceptance_criteria"], product_roadmap=pre_table_dict["product_roadmap"], 
                                                      related_requirement_preplanning_version=pre_table_dict["related_requirement_preplanning_version"], specification_by_example_url=pre_table_dict["specification_by_example_url"], design_specification_url=pre_table_dict["design_specification_url"], 
                                                      requirement_source=pre_table_dict["requirement_source"], requirement_submitter=pre_table_dict["requirement_submitter"], expected_finish_date=pre_table_dict["expected_finish_date"], 
                                                      requirement_purpose=pre_table_dict["requirement_purpose"], priority=pre_table_dict["priority"],  is_medium_long_term_requirement=pre_table_dict["is_medium_long_term_requirement"], 
                                                      is_competitive_requirement=pre_table_dict["is_competitive_requirement"], is_key_requirement=pre_table_dict["is_key_requirement"],  is_chip_requirement=pre_table_dict["is_chip_requirement"], 
                                                      requirement_category=pre_table_dict["requirement_category"], market_target=pre_table_dict["market_target"], target_market=pre_table_dict["target_market"], 
                                                      customer=pre_table_dict["customer"], belong_feature_category=pre_table_dict["belong_feature_category"], requirement_type=pre_table_dict["requirement_type"], 
                                                      verification_mode=pre_table_dict["verification_mode"], verification_team=pre_table_dict["verification_team"], related_sub_features=pre_table_dict["related_sub_features"], 
                                                      current_status=check_update,
                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person)
        db.session.execute(update_sql)
    else:
        insert_sql = insert(MR_INFO_TABLE).values(belong_domain=pre_table_dict['belong_domain'], depend_belong_domain=pre_table_dict['depend_belong_domain'], 
                                                    team=pre_table_dict["team"], belong_product=pre_table_dict["belong_product"], related_type=pre_table_dict["related_type"], 
                                                    workitem_type=pre_table_dict["workitem_type"], workitem_id=pre_table_dict["workitem_id"], workitem_status=pre_table_dict["workitem_status"], 
                                                    title=pre_table_dict["title"], description=pre_table_dict["description"], acceptance_criteria=pre_table_dict["acceptance_criteria"], product_roadmap=pre_table_dict["product_roadmap"], 
                                                      related_requirement_preplanning_version=pre_table_dict["related_requirement_preplanning_version"], specification_by_example_url=pre_table_dict["specification_by_example_url"], design_specification_url=pre_table_dict["design_specification_url"], 
                                                      requirement_source=pre_table_dict["requirement_source"], requirement_submitter=pre_table_dict["requirement_submitter"], expected_finish_date=pre_table_dict["expected_finish_date"], 
                                                      requirement_purpose=pre_table_dict["requirement_purpose"], priority=pre_table_dict["priority"],  is_medium_long_term_requirement=pre_table_dict["is_medium_long_term_requirement"], 
                                                      is_competitive_requirement=pre_table_dict["is_competitive_requirement"], is_key_requirement=pre_table_dict["is_key_requirement"],  is_chip_requirement=pre_table_dict["is_chip_requirement"], 
                                                      requirement_category=pre_table_dict["requirement_category"], market_target=pre_table_dict["market_target"], target_market=pre_table_dict["target_market"], 
                                                      customer=pre_table_dict["customer"], belong_feature_category=pre_table_dict["belong_feature_category"], requirement_type=pre_table_dict["requirement_type"], 
                                                      verification_mode=pre_table_dict["verification_mode"], verification_team=pre_table_dict["verification_team"], related_sub_features=pre_table_dict["related_sub_features"], 
                                                      current_status=check_add, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator_person=new_operator_person, effective_flag='Y')
        db.session.execute(insert_sql)

def importExcelMrFeatureData():
    """
    Excel文件上传接口
    ---
    tags:
      - MR信息（包括子特性）
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
        # raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")
        return {"code": 201, "status": "failed", "message": "仅支持上传 .xlsx 格式文件", "data": {}}
    
    try:
        # contents = await file.read()

        # # # 将内容封装为 BytesIO 对象，支持 seek 操作
        # excel_file = BytesIO(contents)
        # 读取 Excel 文件（无需保存到本地）
        df = pd.read_excel(file, engine="openpyxl")
        df = df.fillna(value='')
        # df["MR分类"] = df["MR分类"].ffill()
        # df['特性一级分类'] = df['特性一级分类'].astype(str) 
        related_sub_features = []
        pre_table_dict = dict()
        # 数据库操作
        for _, row in df.iterrows():
            table_dict = dict()
            if row["工作项类型"] in ['市场需求', 'MR']:
                # 假设 Excel 表头与数据库字段名一致
                table_dict['belong_domain'] = row["领域"] if "领域" in row else '02-L1' 
                table_dict['depend_belong_domain'] = row["依赖领域"].replace('\n', ',') if "依赖领域" in row else '' 
                table_dict['team'] = row["团队"] if "团队" in row else '' 
                table_dict['belong_product'] = row["所属产品"] if "所属产品" in row else '' 
                table_dict['related_type'] = row["关联关系"] if "关联关系" in row else '' 
                table_dict['workitem_type'] = row["工作项类型"] if "工作项类型" in row else '' 
                table_dict['workitem_id'] = row["标识"] if "标识" in row else '' 
                table_dict['workitem_status'] = row["状态"] if "状态" in row else '' 
                table_dict['title'] = row["标题"] if "标题" in row else '' 
                table_dict['description'] = row["描述"] if "描述" in row else '' 
                table_dict['acceptance_criteria'] = row["验收准则"] if "验收准则" in row else '' 
                table_dict['product_roadmap'] = row["产品路标"] if "产品路标" in row else '' 
                table_dict['related_requirement_preplanning_version'] = row["需求预规划"] if "需求预规划" in row else '' 
                table_dict['specification_by_example_url'] = row["需求实例化链接"] if "需求实例化链接" in row else '' 
                table_dict['design_specification_url'] = row["方案文档链接"] if "方案文档链接" in row else '' 
                table_dict['requirement_source'] = row["需求来源"] if "需求来源" in row else '' 
                table_dict['requirement_submitter'] = row["需求提出人"] if "需求提出人" in row else '' 
                table_dict['expected_finish_date'] = row["期望完成日期"] if "期望完成日期" in row else '' 
                table_dict['requirement_purpose'] = row["需求用途"] if "需求用途" in row else '' 
                table_dict['priority'] = row["优先级"] if "优先级" in row else '' 
                table_dict['is_medium_long_term_requirement'] = row["是否中长期需求"] if "是否中长期需求" in row else '' 
                table_dict['is_competitive_requirement'] = row["是否竞争力需求"] if "是否竞争力需求" in row else '' 
                table_dict['is_key_requirement'] = row["是否关键需求"] if "是否关键需求" in row else '' 
                table_dict['is_chip_requirement'] = row["是否芯片需求"] if "是否芯片需求" in row else '' 
                table_dict['requirement_category'] = row["需求类别"] if "需求类别" in row else '' 
                table_dict['market_target'] = row["市场目标"] if "市场目标" in row else '' 
                table_dict['target_market'] = row["目标市场"] if "目标市场" in row else '' 
                table_dict['customer'] = row["客户"] if "客户" in row else '' 
                table_dict['belong_feature_category'] = row["所属特性分类"] if "所属特性分类" in row else '' 
                table_dict['requirement_type'] = row["需求类型"] if "需求类型" in row else '' 
                table_dict['verification_mode'] = row["验证方式"] if "验证方式" in row else '' 
                table_dict['verification_team'] = row["验证团队"] if "验证团队" in row else '' 
                table_dict['related_sub_features'] = []
                table_dict['related_sub_features'] = []
                if related_sub_features:
                    mr_info_to_db(pre_table_dict, related_sub_features, new_operator_person)
                pre_table_dict = copy.deepcopy(table_dict)
                related_sub_features = []
            else:
                related_sub_features.append(row["标题"])
        mr_info_to_db(pre_table_dict, related_sub_features, new_operator_person)
        # 创建新用户 
        db.session.commit()
        db.session.refresh(db.session.query(MR_INFO_TABLE).first())
        return {"code": 200, "status": "success", "message": "导入成功", "data": []}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"处理文件失败: {str(e)}，可能原因比如导入文件部分字段列缺失等", "data": []}
