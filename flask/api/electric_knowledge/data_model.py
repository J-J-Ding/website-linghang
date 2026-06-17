from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Boolean, Integer, String, FLOAT, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql


db = SQLAlchemy()

class FACTOR_VALUE_SRC_CONFIG_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = 'factor_value_src_config_table'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    factor_value_src = db.Column(db.String(500), nullable=True)
    factor_value_src_description = db.Column(db.String(500), nullable=True)
    factor_value_src_custom_rules = db.Column(db.Text(65536), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)
    core_element_factor_relation_table_items = relationship("CORE_ELEMENT_FACTOR_RELATION_TABLE", back_populates="factor_value_src_config_table") 

    def to_dict(self):
        return {"id": self.id,
                "factor_value_src": self.factor_value_src, "factor_value_src_description": self.factor_value_src_description,
                "factor_value_src_custom_rules": self.factor_value_src_custom_rules, "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag}

class CORE_ELEMENT_FACTOR_RELATION_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = 'core_element_factor_relation_table'
    id = db.Column(db.Integer, primary_key=True)
    core_element_type = db.Column(db.String(50), nullable=True)
    core_element = db.Column(db.String(200), nullable=True)
    factor = db.Column(db.String(200), nullable=True)
    factor_details_link = db.Column(db.String(500), nullable=True)
    factor_value_src = db.Column(db.String(500), db.ForeignKey('factor_value_src_config_table.factor_value_src'), nullable=True)
    factor_value = db.Column(db.Text(65536), nullable=True)
    factor_ext_value = db.Column(db.Text(65536), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)
    factor_value_src_config_table = relationship("FACTOR_VALUE_SRC_CONFIG_TABLE", back_populates="core_element_factor_relation_table_items") 

    @property
    def factor_value_src_description(self):
        return self.factor_value_src_config_table.factor_value_src_description if self.factor_value_src_config_table else None

    def to_dict(self):
        return {"id": self.id, "core_element_type": self.core_element_type,
                "core_element": self.core_element, "factor": self.factor, "factor_details_link": self.factor_details_link,
                "factor_value_src": self.factor_value_src, "factor_value": self.factor_value, "current_status": self.current_status,
                "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag,
                "factor_value_src_description": self.factor_value_src_description}

# 业务模型-光口业务速率&业务类型
class BUSINESS_MODEL_RATE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "business_model_rate_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    network_element_business_model_rate = db.Column(db.String(100), nullable=True)
    business_type_list = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {"id": self.id, "network_element_business_model_rate": self.network_element_business_model_rate, 
                "business_type_list": self.business_type_list, "current_status": self.current_status, 
                "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag
                }

class BUSINESS_MODEL_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "business_model_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    network_element_business_solution = db.Column(db.String(100), nullable=True)
    network_element_business_model = db.Column(db.String(100), nullable=True)
    input_business_type_list = db.Column(db.String(200), nullable=True)
    crossconnect_type = db.Column(db.String(100), nullable=True)
    output_business_type_list = db.Column(db.String(200), nullable=True)
    input_board_model_list = db.Column(db.String(200), nullable=True)
    output_board_model_list = db.Column(db.String(200), nullable=True)
    typical_board_examples = db.Column(db.String(500), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)


class BOARD_MODEL_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_model_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    board_model_classification = db.Column(db.String(100), nullable=True)
    board_model = db.Column(db.String(100), nullable=True)
    board_model_description = db.Column(db.String(200), nullable=True)
    crossconnect_type = db.Column(db.String(100), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {"id": self.id, "board_model_classification": self.board_model_classification, 
                "board_model": self.board_model, "board_model_description": self.board_model_description, "crossconnect_type": self.crossconnect_type, 
                "current_status": self.current_status, "create_time": self.create_time,
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag
                }

class BOARD_VALID_MODEL_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_valid_model_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    board_model_classification = db.Column(db.String(100), nullable=True)
    valid_combination_board_model = db.Column(db.String(100), nullable=True)
    valid_combination_board_model_description = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {"id": self.id, "board_model_classification": self.board_model_classification, 
                "valid_combination_board_model": self.valid_combination_board_model, "valid_combination_board_model_description": self.valid_combination_board_model_description, 
                "current_status": self.current_status, "create_time": self.create_time,
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag
                }

class FEATURE_RELATION_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "feature_relation_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    feature_first_classification = db.Column(db.String(100), nullable=True)
    feature_second_classification = db.Column(db.String(100), nullable=True)
    feature_name = db.Column(db.String(200), nullable=True)
    children_feature_name = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text(65536), nullable=True)
    acceptance_criteria = db.Column(db.Text(65536), nullable=True)
    feature_content_link = db.Column(db.String(300), nullable=True)
    belong_team = db.Column(db.String(100), nullable=True)
    estimated_dev_workload = db.Column(db.String(10), nullable=True)
    requirement_sort = db.Column(db.String(10), nullable=True)
    parent = db.Column(db.Boolean, default=False)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class OLD_CHILDREN_FEATURE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "old_children_feature_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    old_children_feature_name = db.Column(db.String(200), nullable=True)
    children_feature_name = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class FEATURE_BOARD_RELATION_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "feature_board_relation_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    feature_first_classification = db.Column(db.String(100), nullable=True)
    feature_second_classification = db.Column(db.String(100), nullable=True)
    feature_name = db.Column(db.String(200), nullable=True)
    children_feature_name = db.Column(db.String(200), nullable=True)
    related_board_model = db.Column(db.String(100), nullable=True)
    related_flag = db.Column(db.String(10), default='0')
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class FEATURE_CHANGE_RELATION_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "feature_change_relation_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    feature_first_classification = db.Column(db.String(100), nullable=True)
    feature_second_classification = db.Column(db.String(100), nullable=True)
    feature_name = db.Column(db.String(200), nullable=True)
    children_feature_name = db.Column(db.String(200), nullable=True)
    related_change = db.Column(db.String(100), nullable=True)
    related_flag = db.Column(db.String(10), default='0')
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class BOARD_TREE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_tree_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    board_name = db.Column(db.String(100), nullable=True)
    factor_type_cn = db.Column(db.String(100), nullable=True)
    factor_type_en = db.Column(db.String(100), nullable=True)
    factor_value = db.Column(db.Text(65536), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class BOARD_COMPONENTS_TREE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_components_tree_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    components = db.Column(db.String(100), nullable=True)
    component_business_plan = db.Column(db.String(100), nullable=True)
    business_plan_slicing = db.Column(db.String(200), nullable=True)
    business_plan_details_link = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class SUBRACK_TREE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "subrack_tree_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    subrack_name = db.Column(db.String(100), nullable=True)
    factor_type_cn = db.Column(db.String(100), nullable=True)
    factor_type_en = db.Column(db.String(100), nullable=True)
    factor_value = db.Column(db.Text(65536), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class SUBRACK_COMPONENTS_TREE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "subrack_components_tree_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    belong_product = db.Column(db.String(50), nullable=True)
    subrack_type = db.Column(db.String(50), nullable=True)
    components = db.Column(db.String(100), nullable=True)
    component_business_plan = db.Column(db.String(100), nullable=True)
    business_plan_slicing = db.Column(db.String(200), nullable=True)
    business_plan_details_link = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class BOARD_CHANGE_ANALYSIS_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_change_analysis_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    board_name = db.Column(db.String(100), nullable=True)
    change_analysis_type_cn = db.Column(db.String(100), nullable=True)
    change_analysis_type_en = db.Column(db.String(100), nullable=True)
    change_analysis_value = db.Column(db.Text(65536), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

class BOARD_OPT_BIZ_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_opt_biz_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    board_name = db.Column(db.String(100), nullable=True)
    l_c_type = db.Column(db.String(10), nullable=True)
    opt_value = db.Column(db.String(200), nullable=True)
    biz_value = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)


class MR_INFO_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "mr_info_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    belong_domain = db.Column(db.String(50), nullable=True)
    depend_belong_domain = db.Column(db.String(50), nullable=True)
    team = db.Column(db.String(50), nullable=True)
    belong_product = db.Column(db.String(50), nullable=True)
    related_type = db.Column(db.String(50), nullable=True)
    workitem_type = db.Column(db.String(50), nullable=True)
    workitem_id = db.Column(db.String(50), nullable=True)
    workitem_status = db.Column(db.String(50), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(Text, nullable=True)
    acceptance_criteria = db.Column(Text, nullable=True)
    product_roadmap = db.Column(db.String(100), nullable=True)
    related_requirement_preplanning_version = db.Column(db.String(100), nullable=True)
    specification_by_example_url = db.Column(db.String(200), nullable=True)
    design_specification_url = db.Column(db.String(200), nullable=True)
    requirement_source = db.Column(db.String(50), nullable=True)
    requirement_submitter = db.Column(db.String(50), nullable=True)
    expected_finish_date = db.Column(db.String(50), nullable=True)
    requirement_purpose = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    is_medium_long_term_requirement = db.Column(db.String(50), nullable=True)
    is_competitive_requirement = db.Column(db.String(50), nullable=True)
    is_key_requirement = db.Column(db.String(50), nullable=True)
    is_chip_requirement = db.Column(db.String(50), nullable=True)
    requirement_category = db.Column(db.String(50), nullable=True)
    market_target = db.Column(db.String(50), nullable=True)
    target_market = db.Column(db.String(50), nullable=True)
    customer = db.Column(db.String(50), nullable=True)
    belong_feature_category = db.Column(db.String(50), nullable=True)
    requirement_type = db.Column(db.String(50), nullable=True)
    verification_mode = db.Column(db.String(50), nullable=True)
    verification_team = db.Column(db.String(100), nullable=True)
    related_sub_features = db.Column(Text, nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)


class BOARD_WHOLE_STATUS_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "board_whole_status_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    board_name = db.Column(db.String(50), nullable=True)
    product_factor_value = db.Column(db.String(50), nullable=True)
    board_type_factor_value = db.Column(db.String(200), nullable=True)
    board_service_model_factor_values = db.Column(db.String(200), nullable=True)
    feature_name = db.Column(db.String(200), nullable=True)
    children_feature_name = db.Column(db.String(200), nullable=True)
    parent = db.Column(db.String(10), default=False, nullable=True)
    change_analysis = db.Column(db.Text, nullable=True)
    milestone = db.Column(db.String(100), nullable=True)
    related_rdc = db.Column(db.String(100), nullable=True)
    related_rdc_title = db.Column(db.String(500), nullable=True)
    related_requirement_preplanning_version = db.Column(db.String(100), nullable=True)
    related_requirement_status = db.Column(db.String(50), nullable=True)
    related_parent_rdc = db.Column(db.String(100), nullable=True)
    development_type = db.Column(db.String(100), nullable=True)
    reusedegree = db.Column(db.String(32), nullable=True)
    current_status = db.Column(db.String(50), nullable=True)
    related_fault_num = db.Column(db.Integer, nullable=True)
    create_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)


class RDC_FAULT_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "rdc_fault_table"
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    rdc_ident = db.Column(db.String(50), nullable=True)
    rdc_title = db.Column(db.String(256), nullable=True)
    related_board_name = db.Column(db.String(50), nullable=True)
    related_rdc_ident = db.Column(db.String(50), nullable=True)
    rdc_created_by = db.Column(db.String(50), nullable=True)
    rdc_created_time = db.Column(db.String(50), nullable=True)
    rdc_changed_by = db.Column(db.String(50), nullable=True)
    rdc_changed_time = db.Column(db.String(50), nullable=True)
    rdc_field = db.Column(db.String(50), nullable=True)
    rdc_team = db.Column(db.String(50), nullable=True)
    rdc_introducted_by = db.Column(db.String(50), nullable=True)
    requirement_status = db.Column(db.String(50), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)


class RDC_SPLIT_TASK_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "rdc_split_task_table"
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    task_id = db.Column(db.String(50), nullable=True)
    employ_no = db.Column(db.String(50), nullable=True)
    employ_name = db.Column(db.String(50), nullable=True)
    task_start_time = db.Column(db.String(50), nullable=True)
    task_end_time = db.Column(db.String(50), nullable=True)
    task_type = db.Column(db.String(50), nullable=True)
    task_param = db.Column(db.JSON, nullable=True)
    task_status = db.Column(db.String(50), nullable=True)
    task_result = db.Column(db.String(50), nullable=True)
    task_err_reason = db.Column(Text, nullable=True)
    split_result = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        """将模型对象转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'employ_no': self.employ_no,
            'employ_name': self.employ_name,
            'task_start_time': self.task_start_time,
            'task_end_time': self.task_end_time,
            'task_type': self.task_type,
            'task_param': self.task_param,
            'task_status': self.task_status,
            'task_result': self.task_result,
            'task_err_reason': self.task_err_reason,
            'split_result': self.split_result,
        }


class REQ_MANAGE_AGENT_CHAT_RECORD(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_agent_chat_record"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    session_id = Column(String(64), index=True, nullable=False)
    request_id = Column(String(64), index=True, nullable=False)
    role = Column(String(32), nullable=False)
    user_id = Column(String(64))
    user_name = Column(String(64))
    model = Column(String(64))
    tool_name_str = Column(Text)
    content = Column(Text)
    timestamp = Column(DateTime, default=db.func.now())


class REQ_MANAGE_AGENT_PROMPT(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_agent_prompt"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    title = db.Column(db.String(255), index=True, unique=True, nullable=False)
    description = db.Column(db.String(1024))
    tool_name_str = db.Column(db.Text)
    content = db.Column(db.Text)
    creator_id = db.Column(db.String(64))
    creator_name = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=db.func.now())
    reference_count = db.Column(db.Integer, default=0)


class REQ_MANAGE_AGENT_MCP_CFG(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_agent_mcp_cfg"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    mcp_name = db.Column(db.String(1024))
    mcp_url = db.Column(db.String(1024))
    need_tool = db.Column(db.Text)
    not_need_tool = db.Column(db.Text)
    creator_id = db.Column(db.String(64))
    creator_name = db.Column(db.String(64))
    create_time = db.Column(db.DateTime, default=db.func.now())


class REQ_MANAGE_BOARD_PR_INFO_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_board_pr_info_table"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    system_id = db.Column(db.String(32))
    system_state = db.Column(db.String(32))
    system_createddate = db.Column(db.String(1024))
    system_createdby = db.Column(db.String(32))
    system_changeddate = db.Column(db.String(1024))
    system_changedby = db.Column(db.String(32))
    system_appointedto = db.Column(db.String(32))
    system_areapath = db.Column(db.String(32))
    team = db.Column(db.String(32))
    system_title = db.Column(db.String(1024))
    belongproduct = db.Column(db.String(32))
    requirementpreplanning = db.Column(db.String(32))
    system_description_html = db.Column(db.Text)
    acceptancecriteria_html = db.Column(db.Text)
    requirementanalysisowner = db.Column(db.String(32))
    specificationbyexampleurl = db.Column(db.String(1024))
    specificationbyexamplestate = db.Column(db.String(32))
    designspecificationurl = db.Column(db.String(1024))
    designstate = db.Column(db.String(32))
    featureurl = db.Column(db.String(1024))
    belongfeaturecatalog = db.Column(db.String(32))
    featureid = db.Column(db.String(32))
    featurename_cn = db.Column(db.String(1024))
    checkresultofchipscheme = db.Column(db.String(32))
    isautocreated = db.Column(db.String(32))
    assessresult_first = db.Column(db.String(32))
    reusedegree = db.Column(db.String(32))
    script_update_date = db.Column(db.String(32))


class REQ_MANAGE_CHECK_PR_INFO_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_check_pr_info_table"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    problem_type = db.Column(db.String(1024))
    problem_description = db.Column(db.String(1024))
    check_date = db.Column(db.String(32))
    default_problem_flag = db.Column(db.String(32))
    default_handle_person = db.Column(db.String(32))
    default_handle_date = db.Column(db.String(32))
    default_handle_flag = db.Column(db.String(32))
    man_problem_flag = db.Column(db.String(32))
    man_handle_person = db.Column(db.String(32))
    man_handle_date = db.Column(db.String(32))
    man_handle_flag = db.Column(db.String(32))
    cal_problem_flag = db.Column(db.String(32))
    cal_handle_person = db.Column(db.String(32))
    cal_handle_date = db.Column(db.String(32))
    cal_handle_flag = db.Column(db.String(32))
    actual_handle_date = db.Column(db.String(32))
    handle_delay_flag = db.Column(db.String(32))
    man_update_person = db.Column(db.String(32))
    man_update_date = db.Column(db.String(32))
    system_id = db.Column(db.String(32))
    system_state = db.Column(db.String(32))
    system_createddate = db.Column(db.String(1024))
    system_createdby = db.Column(db.String(32))
    system_changeddate = db.Column(db.String(1024))
    system_changedby = db.Column(db.String(32))
    system_appointedto = db.Column(db.String(32))
    system_areapath = db.Column(db.String(32))
    team = db.Column(db.String(32))
    system_title = db.Column(db.String(1024))
    belongproduct = db.Column(db.String(32))
    requirementpreplanning = db.Column(db.String(32))
    system_description_html = db.Column(db.Text)
    acceptancecriteria_html = db.Column(db.Text)
    requirementanalysisowner = db.Column(db.String(32))
    specificationbyexampleurl = db.Column(db.String(1024))
    specificationbyexamplestate = db.Column(db.String(32))
    designspecificationurl = db.Column(db.String(1024))
    designstate = db.Column(db.String(32))
    featureurl = db.Column(db.String(1024))
    belongfeaturecatalog = db.Column(db.String(32))
    featureid = db.Column(db.String(32))
    featurename_cn = db.Column(db.String(1024))
    checkresultofchipscheme = db.Column(db.String(32))
    isautocreated = db.Column(db.String(32))
    assessresult_first = db.Column(db.String(32))
    reusedegree = db.Column(db.String(32))
    planstartdateofdevelopment = db.Column(db.String(32))
    planfinishdateofdevelopment = db.Column(db.String(32))
    accesscheck = db.Column(db.String(32))
    belongreleaseversion = db.Column(db.String(256))
    ismasterdeliveryarea = db.Column(db.String(32))
    script_update_date = db.Column(db.String(32))
    detail_list = db.Column(db.JSON)


class REQ_MANAGE_CHECK_PR_SUMMARY_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_check_pr_summary_table"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    summary_date = db.Column(db.String(32))
    requirementpreplanning = db.Column(db.String(32))
    all_num = db.Column(db.Integer)
    problem_num = db.Column(db.Integer)
    not_problem_num = db.Column(db.Integer)
    handle_num = db.Column(db.Integer)
    not_handle_num = db.Column(db.Integer)
    delay_num = db.Column(db.Integer)
    not_delay_num = db.Column(db.Integer)


class REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "req_manage_board_pr_split_summary_table"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    summary_date = db.Column(db.String(32))
    preplanning = db.Column(db.String(32))
    all_all_num = db.Column(db.Integer)
    all_standard_num = db.Column(db.Integer)
    all_special_num = db.Column(db.Integer)
    auto_all_num = db.Column(db.Integer)
    auto_standard_num = db.Column(db.Integer)
    auto_special_num = db.Column(db.Integer)
    man_all_num = db.Column(db.Integer)
    man_standard_num = db.Column(db.Integer)
    man_special_num = db.Column(db.Integer)


class PRODUCT_IMAGE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "product_image_table"  # 对应数据库中的表名
    id = db.Column(db.String(40), primary_key=True, nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    extension = db.Column(db.String(10), nullable=True)
    mime_type = db.Column(db.String(50), nullable=True)
    size = db.Column(db.Integer, nullable=True)
    upload_time = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    delete_time = db.Column(db.DateTime, nullable=True)  # 自动删除时间

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'url': f"/api/images/{self.id}",
            'size': self.size,
            'mime_type': self.mime_type,
            'upload_time': self.upload_time.isoformat(),
            'expires': self.delete_time.isoformat() if self.delete_time else None
        }


class FIELDTEAMMEMBERS(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "fieldteammembers"  # 对应数据库中的表名
    
    employee_name = db.Column(db.String(50), nullable=True)
    employee_number = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    is_delete = db.Column(db.Integer)
    department = db.Column(db.String(50), nullable=True)
    human_resource = db.Column(db.FLOAT, nullable=True)
    field_id = db.Column(db.Integer)
    team_id = db.Column(db.Integer)
    district = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text(65536), nullable=True)


class HARDWARE_TREE_RULE_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "hardware_tree_rule_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    hardware_type = db.Column(db.String(100), nullable=True)
    factor_name = db.Column(db.String(100), nullable=True)
    situation = db.Column(db.String(100), nullable=True)
    input_format = db.Column(db.String(100), nullable=True)
    input_remark = db.Column(db.String(200), nullable=True)


# 业务模块-特性&检测点内容表
class MODULE_FEATURECHECKPOINT_CONTENT_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "module_featurecheckpoint_content_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    module_name = db.Column(db.String(50), nullable=True)
    featurecheckpoint_name = db.Column(db.String(100), nullable=True)
    featurecheckpoint_content = db.Column(Text(length=16777215), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {"id": self.id, "module_name": self.module_name, "featurecheckpoint_name": self.featurecheckpoint_name, 
                "featurecheckpoint_content": self.featurecheckpoint_content, "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person
                }
    
# 业务模块-特性VS检测点关系表
class MODULE_FEATURE_CHECKPOINT_RELATION_TABLE(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = "module_feature_checkpoint_relation_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    module_name = db.Column(db.String(50), nullable=True)
    feature_name = db.Column(db.String(200), nullable=True)
    checkpoint_name = db.Column(db.String(100), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {"id": self.id, "module_name": self.module_name, "feature_name": self.feature_name, 
                "checkpoint_name": self.checkpoint_name, "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person
                }
    
# 审批流程配置表
class APPROVAL_CONFIG_TABLE(db.Model):
    """审批配置表 - 定义各业务表的审批规则"""
    __bind_key__ = 'db1'
    __tablename__ = 'approval_config_table'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    biz_type = db.Column(db.String(50), unique=True, nullable=False, comment='业务表标识')
    biz_table_name = db.Column(db.String(100), nullable=False, comment='数据库表名')
    module_path = db.Column(db.String(200), nullable=False, comment='业务模块路径')
    model_class_name = db.Column(db.String(50), nullable=False, comment='Model类名')
    need_approval = db.Column(db.Boolean, default=True, comment='是否需要审批')
    approval_flow_type = db.Column(db.String(20), default='single', comment='审批流程类型: single/multi')
    default_approver = db.Column(db.String(100), nullable=True, comment='默认审批人(工号+姓名)')
    admin_persons = db.Column(db.String(200), nullable=True, comment='管理员列表(可查看所有审核单)')
    description = db.Column(db.Text, nullable=True, comment='配置说明')
    create_time = db.Column(db.DateTime, default=db.func.now(), nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=True)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), default='Y')

    def to_dict(self):
        return {
            'id': self.id,
            'biz_type': self.biz_type,
            'biz_table_name': self.biz_table_name,
            'module_path': self.module_path,
            'model_class_name': self.model_class_name,
            'need_approval': self.need_approval,
            'approval_flow_type': self.approval_flow_type,
            'default_approver': self.default_approver,
            'admin_persons': self.admin_persons,
            'description': self.description,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'operator_person': self.operator_person,
            'effective_flag': self.effective_flag
        }


# 审核记录表
class APPROVAL_LIST_TABLE(db.Model):
    """审批记录表（主表）- 按设计文档重构"""
    __bind_key__ = 'db1'
    __tablename__ = 'approval_list_table'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    biz_type = db.Column(db.String(50), nullable=False, index=True, comment='业务表标识')
    biz_id = db.Column(db.String(100), nullable=False, index=True, comment='业务记录主键ID')

    # 变更类型：add新增, update修改, delete删除
    change_type = db.Column(db.String(20), nullable=False, comment='变更类型: add/update/delete')
    change_reason = db.Column(db.Text, nullable=True, comment='变更理由')

    # 数据快照
    old_data = db.Column(db.JSON, nullable=True, comment='变更前数据(修改/删除时记录)')
    new_data = db.Column(db.JSON, nullable=True, comment='变更后数据(新增/修改时记录)')
    diff_data = db.Column(db.JSON, nullable=True, comment='差异字段对比')
    zh_en_name_relation = db.Column(db.JSON, nullable=True, comment='中英文列名对应关系')

    # 审批状态：1待审, 2审核中, 3审核结束-通过, 4审核结束-驳回, 5撤回
    approval_status = db.Column(db.SmallInteger, default=1, nullable=False, comment='审批状态: 1待审/2审核中/3通过/4驳回/5撤回')
    approval_result = db.Column(db.String(20), nullable=True, comment='审批结果: approved/rejected/withdrawn')

    # 人员信息
    submitter_person = db.Column(db.String(50), nullable=False, comment='提交人')
    assigned_persons = db.Column(db.String(200), nullable=True, comment='指定审批人列表(逗号分隔)')
    current_approver = db.Column(db.String(50), nullable=True, comment='当前审批人')

    # 驳回信息
    reject_reason = db.Column(db.Text, nullable=True, comment='驳回理由')

    # 时间戳
    create_time = db.Column(db.DateTime, default=db.func.now(), nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=True)
    token = db.Column(db.String(100), nullable=True)

    # 关联详情表
    details = relationship("APPROVAL_DETAIL_TABLE", back_populates="approval_list", cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'biz_type': self.biz_type,
            'biz_id': self.biz_id,
            'change_type': self.change_type,
            'change_reason': self.change_reason,
            'old_data': self.old_data,
            'new_data': self.new_data,
            'diff_data': self.diff_data,
            'zh_en_name_relation': self.zh_en_name_relation,
            'approval_status': self.approval_status,
            'approval_result': self.approval_result,
            'submitter_person': self.submitter_person,
            'assigned_persons': self.assigned_persons,
            'current_approver': self.current_approver,
            'reject_reason': self.reject_reason,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'token': self.token
        }

class APPROVAL_DETAIL_TABLE(db.Model):
    """审批详情表（子表）- 记录每次审批操作"""
    __bind_key__ = 'db1'
    __tablename__ = 'approval_detail_table'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(db.Integer, db.ForeignKey('approval_list_table.id', ondelete='CASCADE'), nullable=False, index=True, comment='关联审批主表ID')

    approval_person = db.Column(db.String(50), nullable=False, comment='审批人')

    # 操作：approve通过, reject驳回, withdraw撤回, reassign转交
    action = db.Column(db.String(20), nullable=False, comment='审批动作: approve/reject/withdraw/reassign')
    comment = db.Column(db.Text, nullable=True, comment='审批意见')

    create_time = db.Column(db.DateTime, default=db.func.now(), nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=True)

    # 关联主表
    approval_list = db.relationship('APPROVAL_LIST_TABLE', back_populates='details')

    def to_dict(self):
        return {
            'id': self.id,
            'record_id': self.record_id,
            'approval_person': self.approval_person,
            'action': self.action,
            'comment': self.comment,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
