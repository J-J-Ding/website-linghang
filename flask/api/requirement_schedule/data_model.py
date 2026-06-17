from sqlalchemy import create_engine, Column, Boolean, Integer, String, FLOAT, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from urllib.parse import quote_plus

from electric_knowledge.data_model import db


# 需求排期助手相关表
class REQUIREMENT_SCHEDULE_TABLE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'requirement_schedule_table'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    # 只读字段
    work_item_type = db.Column(db.String(50), nullable=True)  # 工作项类型
    identifier = db.Column(db.String(100), nullable=True)  # 标识
    title = db.Column(db.String(500), nullable=True)  # 标题
    reuse_degree = db.Column(db.String(50), nullable=True)  # 复用程度
    feature_identifier = db.Column(db.String(100), nullable=True)  # 特性标识
    feature_attribute = db.Column(db.String(200), nullable=True)  # 特性属性
    verification_mode = db.Column(db.String(100), nullable=True)  # 验证方式
    verification_team = db.Column(db.String(100), nullable=True)  # 验证团队
    requirement_sort = db.Column(db.String(50), nullable=True)  # 需求排序
    priority = db.Column(db.String(50), nullable=True)  # 优先级
    domain = db.Column(db.String(100), nullable=True)  # 领域
    team = db.Column(db.String(100), nullable=True)  # 团队
    # 可编辑字段
    first_evaluation_conclusion = db.Column(db.Text, nullable=True)  # 评估结论（第一次）
    second_evaluation_conclusion = db.Column(db.Text, nullable=True)  # 评估结论（第二次）
    estimated_workload = db.Column(db.FLOAT, nullable=True)  # 预计工作量
    estimated_dev_workload = db.Column(db.FLOAT, nullable=True)  # 预计开发工作量
    estimated_verification_workload = db.Column(db.FLOAT, nullable=True)  # 预计验证工作量
    estimated_system_test_workload = db.Column(db.FLOAT, nullable=True)  # 预计系统测试工作量
    plan_start_dev_date = db.Column(db.String(20), nullable=True)  # 计划开始开发日期 YYYY-MM-DD
    plan_finish_dev_date = db.Column(db.String(20), nullable=True)  # 计划完成开发日期 YYYY-MM-DD
    plan_start_integration_test_date = db.Column(db.String(20), nullable=True)  # 计划开始集成测试日期 YYYY-MM-DD
    plan_finish_integration_test_date = db.Column(db.String(20), nullable=True)  # 计划完成集成测试日期 YYYY-MM-DD
    plan_start_system_test_date = db.Column(db.String(20), nullable=True)  # 计划开始系统测试日期 YYYY-MM-DD
    plan_finish_system_test_date = db.Column(db.String(20), nullable=True)  # 计划完成系统测试日期 YYYY-MM-DD
    plan_delivery_date = db.Column(db.String(20), nullable=True)  # 计划交付日期 YYYY-MM-DD
    introduction_source = db.Column(db.String(100), nullable=True)  # 引入来源（如"非本团队主交付PR"）
    # 筛选字段
    belong_product = db.Column(db.String(100), nullable=True)  # 所属产品
    product_roadmap = db.Column(db.String(100), nullable=True)  # 产品路标
    requirement_preplanning = db.Column(db.String(100), nullable=True)  # 需求预规划
    # 系统字段
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True, default='1')

    def to_dict(self):
        return {
            "id": self.id,
            "work_item_type": self.work_item_type,
            "identifier": self.identifier,
            "title": self.title,
            "reuse_degree": self.reuse_degree,
            "feature_identifier": self.feature_identifier,
            "feature_attribute": self.feature_attribute,
            "verification_mode": self.verification_mode,
            "verification_team": self.verification_team,
            "requirement_sort": self.requirement_sort,
            "priority": self.priority,
            "domain": self.domain,
            "team": self.team,
            "first_evaluation_conclusion": self.first_evaluation_conclusion,
            "second_evaluation_conclusion": self.second_evaluation_conclusion,
            "estimated_workload": self.estimated_workload,
            "estimated_dev_workload": self.estimated_dev_workload,
            "estimated_verification_workload": self.estimated_verification_workload,
            "estimated_system_test_workload": self.estimated_system_test_workload,
            "plan_start_dev_date": self.plan_start_dev_date,
            "plan_finish_dev_date": self.plan_finish_dev_date,
            "plan_start_integration_test_date": self.plan_start_integration_test_date,
            "plan_finish_integration_test_date": self.plan_finish_integration_test_date,
            "plan_start_system_test_date": self.plan_start_system_test_date,
            "plan_finish_system_test_date": self.plan_finish_system_test_date,
            "plan_delivery_date": self.plan_delivery_date,
            "introduction_source": self.introduction_source or '',
            "belong_product": self.belong_product,
            "product_roadmap": self.product_roadmap,
            "requirement_preplanning": self.requirement_preplanning,
            "create_time": self.create_time,
            "update_time": self.update_time,
            "operator_person": self.operator_person,
            "effective_flag": self.effective_flag
        }


class REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'requirement_schedule_filter_history_table'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    filter_type = db.Column(db.String(50), nullable=False)  # 筛选类型: product_roadmap, requirement_preplanning, domain, team
    filter_value = db.Column(db.String(200), nullable=False)  # 筛选值
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True, default='1')

    def to_dict(self):
        return {
            "id": self.id,
            "filter_type": self.filter_type,
            "filter_value": self.filter_value,
            "create_time": self.create_time,
            "update_time": self.update_time,
            "operator_person": self.operator_person,
            "effective_flag": self.effective_flag
        }


class REQUIREMENT_SCHEDULE_PERMISSION_TABLE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'requirement_schedule_permission_table'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)  # 姓名
    user_id = db.Column(db.String(50), nullable=True)  # 工号
    role_name = db.Column(db.String(100), nullable=False)  # 角色名称
    role_code = db.Column(db.String(50), nullable=False, unique=True)  # 角色代码
    can_edit = db.Column(db.Boolean, default=True)  # 是否可编辑
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True, default='1')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "role_name": self.role_name,
            "role_code": self.role_code,
            "can_edit": self.can_edit,
            "create_time": self.create_time,
            "update_time": self.update_time,
            "operator_person": self.operator_person,
            "effective_flag": self.effective_flag
        }


# 人员技能地图表
class PERSON_SKILL_MAP(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'person_skill_map'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)  # 部门
    project_group = db.Column(db.String(50), nullable=False)  # 项目组
    domain = db.Column(db.String(50), nullable=False)  # 领域
    team = db.Column(db.String(50), nullable=False)  # 团队
    person_belong = db.Column(db.String(20), nullable=False)  # 人员归属（如中兴、外包）
    employee_id = db.Column(db.String(20), nullable=False, unique=True)  # 工号（唯一标识）
    name = db.Column(db.String(20), nullable=False)  # 姓名
    leave_time = db.Column(db.String(20), nullable=True, default='')  # 离职时间（在职则为空）
    skill_category = db.Column(db.String(100), nullable=True, default='')  # 技能/特性分类

    def to_dict(self):
        return {
            "id": self.id,
            "department": self.department,
            "project_group": self.project_group,
            "domain": self.domain,
            "team": self.team,
            "person_belong": self.person_belong,
            "employee_id": self.employee_id,
            "name": self.name,
            "leave_time": self.leave_time or '',
            "skill_category": self.skill_category or ''
        }


# 团队映射表（person_skill_map.team 到 requirement_dev_human_resource.team 的映射）
class TEAM_MAPPING(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'team_mapping'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    source_team = db.Column(db.String(50), nullable=False)  # 源团队名称（person_skill_map.team）
    target_team = db.Column(db.String(50), nullable=False)  # 目标团队名称（requirement_dev_human_resource.team）
    team_type = db.Column(db.String(30), nullable=False)  # 团队类型（requirement_dev_human_resource.team_type）
    domain = db.Column(db.String(50), nullable=True)  # 领域（可选，用于区分同一团队名称在不同领域的映射）

    def to_dict(self):
        return {
            "id": self.id,
            "source_team": self.source_team,
            "target_team": self.target_team,
            "team_type": self.team_type,
            "domain": self.domain or ''
        }


# 需求开发投入人力设置表
class REQUIREMENT_DEV_HUMAN_RESOURCE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'requirement_dev_human_resource'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    department = db.Column(db.String(50), nullable=True, default='', index=True)  # 部门（添加索引）
    domain = db.Column(db.String(50), nullable=False, index=True)  # 领域（如01-LO光系统）（添加索引）
    team = db.Column(db.String(50), nullable=False, index=True)  # 团队（如LO-管理团队）（添加索引）
    person_belong = db.Column(db.String(20), nullable=False, index=True)  # 人员归属（如中兴、外包）（添加索引）
    employee_id = db.Column(db.String(20), nullable=False, index=True)  # 工号（添加索引）
    name = db.Column(db.String(20), nullable=False, index=True)  # 姓名（添加索引）
    leave_time = db.Column(db.String(20), nullable=True, default='')  # 离职时间（在职则为空）
    skill_category = db.Column(db.String(100), nullable=True, default='', index=True)  # 技能/特性分类（添加索引）
    year_month = db.Column(db.String(7), nullable=False, index=True)  # 年月（格式如 "2026-01"）（添加索引）
    demand_human_power_ratio = db.Column(db.DECIMAL(3, 2), nullable=False, default=1.00)  # 需求人力占比（范围0~1，2位小数，默认值1.00）
    zxone_19700 = db.Column(db.DECIMAL(3, 2), nullable=True, default=0.00)  # ZXONE 19700（范围0~1，2位小数，默认值0.00）
    zxone_9700 = db.Column(db.DECIMAL(3, 2), nullable=True, default=0.00)  # ZXONE 9700（范围0~1，2位小数，默认值0.00）
    zxmp_m721 = db.Column(db.DECIMAL(3, 2), nullable=True, default=0.00)  # ZXMP M21（范围0~1，2位小数，默认值0.00）
    zxone_nton = db.Column(db.DECIMAL(3, 2), nullable=True, default=0.00)  # ZXONE NTON（范围0~1，2位小数，默认值0.00）

    def to_dict(self):
        return {
            "id": self.id,
            "department": self.department or '',
            "domain": self.domain,
            "team": self.team,
            "person_belong": self.person_belong,
            "employee_id": self.employee_id,
            "name": self.name,
            "leave_time": self.leave_time or '',
            "skill_category": self.skill_category or '',
            "year_month": self.year_month,
            "demand_human_power_ratio": float(self.demand_human_power_ratio) if self.demand_human_power_ratio is not None else 1.00,
            "zxone_19700": float(self.zxone_19700) if self.zxone_19700 is not None else 0.00,
            "zxone_9700": float(self.zxone_9700) if self.zxone_9700 is not None else 0.00,
            "zxmp_m721": float(self.zxmp_m721) if self.zxmp_m721 is not None else 0.00,
            "zxone_nton": float(self.zxone_nton) if self.zxone_nton is not None else 0.00
        }


# 版本视图表
class VERSION_TABLE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'version_table'
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    belong_product = db.Column(db.String(100), nullable=False)  # 所属产品
    product_roadmap = db.Column(db.String(100), nullable=False)  # 所属项目
    requirement_preplanning = db.Column(db.String(100), nullable=False)  # 需求预规划
    start_dev_date = db.Column(db.String(20), nullable=True)  # 启动开发日期 YYYY-MM-DD
    finish_dev_date = db.Column(db.String(20), nullable=True)  # 完成开发日期 YYYY-MM-DD
    achievement_appraisal_date = db.Column(db.String(20), nullable=True)  # 成果鉴定日期 YYYY-MM-DD
    cycle_days = db.Column(db.Integer, nullable=True)  # 周期（天）
    version_status = db.Column(db.String(50), nullable=True, default='')  # 版本状态
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True, default='1')

    def to_dict(self):
        return {
            "id": self.id,
            "belong_product": self.belong_product,
            "product_roadmap": self.product_roadmap,
            "requirement_preplanning": self.requirement_preplanning,
            "start_dev_date": self.start_dev_date or '',
            "finish_dev_date": self.finish_dev_date or '',
            "achievement_appraisal_date": self.achievement_appraisal_date or '',
            "cycle_days": self.cycle_days,
            "version_status": self.version_status or '',
            "create_time": self.create_time,
            "update_time": self.update_time,
            "operator_person": self.operator_person or '',
            "effective_flag": self.effective_flag or '1'
        }


# 特性视图表（暂不接入特性树，字段允许导入/编辑；后续接入特性树后可调整为只读并禁导入）
class FEATURE_VIEW_TABLE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'feature_view_table'

    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)

    # 特性树相关字段（当前阶段：普通字段）
    feature_first_classification = db.Column(db.String(200), nullable=True, default='')  # 特性一级分类
    feature_second_classification = db.Column(db.String(200), nullable=True, default='')  # 特性二级分类
    feature_name = db.Column(db.String(300), nullable=True, default='')  # 特性
    sub_feature_name = db.Column(db.String(300), nullable=True, default='')  # 子特性

    # 业务字段
    feature_identifier = db.Column(db.String(100), nullable=True, default='')  # 特性标识
    domain = db.Column(db.String(100), nullable=True, default='')  # 领域
    team = db.Column(db.String(100), nullable=True, default='')  # 团队
    verification_mode = db.Column(db.String(100), nullable=True, default='')  # 验证方式
    verification_team = db.Column(db.String(100), nullable=True, default='')  # 验证团队
    priority = db.Column(db.String(50), nullable=True, default='')  # 优先级

    dev_workload = db.Column(db.FLOAT, nullable=True)  # 开发工作量（人天）
    detail_workload = db.Column(db.FLOAT, nullable=True)  # 详设工作量（人天）
    estimated_dev_workload = db.Column(db.FLOAT, nullable=True)  # 预计开发工作量
    estimated_verification_workload = db.Column(db.FLOAT, nullable=True)  # 预计验证工作量
    estimated_system_test_workload = db.Column(db.FLOAT, nullable=True)  # 预计系统测试工作量

    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True, default='1')

    def to_dict(self):
        return {
            "id": self.id,
            "feature_first_classification": self.feature_first_classification or '',
            "feature_second_classification": self.feature_second_classification or '',
            "feature_name": self.feature_name or '',
            "sub_feature_name": self.sub_feature_name or '',
            "feature_identifier": self.feature_identifier or '',
            "domain": self.domain or '',
            "team": self.team or '',
            "verification_mode": self.verification_mode or '',
            "verification_team": self.verification_team or '',
            "priority": self.priority or '',
            "dev_workload": self.dev_workload,
            "detail_workload": self.detail_workload,
            "estimated_dev_workload": self.estimated_dev_workload,
            "estimated_verification_workload": self.estimated_verification_workload,
            "estimated_system_test_workload": self.estimated_system_test_workload,
            "create_time": self.create_time,
            "update_time": self.update_time,
            "operator_person": self.operator_person or '',
            "effective_flag": self.effective_flag or '1',
        }


# 领域团队可用人力表（用于可用人力的领域/团队/技能分类维度统计）
class DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE(db.Model):
    __bind_key__ = 'db4'
    __tablename__ = 'domain_team_available_human_resource'
    id = db.Column(db.BigInteger, primary_key=True, index=True, nullable=False, autoincrement=True)
    department = db.Column(db.String(50), nullable=False, default='')  # 部门
    domain = db.Column(db.String(50), nullable=False, default='')  # 领域
    team = db.Column(db.String(100), nullable=False, default='')  # 团队
    team_type = db.Column(db.String(50), nullable=True, default='')  # 团队类型
    skill_category = db.Column(db.String(100), nullable=True, default='')  # 技能/特性分类
    total_human_resource = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 总人力
    zte_human_resource = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 中兴人力
    outsourcing_human_resource = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 外包人力
    demand_delivery_available = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 需求交付可用人力
    remaining_available_human_resource = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 剩余可用人力
    used_human_resource = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 已用人力
    used_human_resource1 = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 已用人力 1（主交付 PR）
    used_human_resource2 = db.Column(db.DECIMAL(10, 2), nullable=True, default=0.00)  # 已用人力 2（非本团队主交付 PR 关联 US）
    date = db.Column(db.String(100), nullable=True, default='')  # 年月（格式如 "2026-01"）

    def to_dict(self):
        return {
            "id": self.id,
            "department": self.department or '',
            "domain": self.domain or '',
            "team": self.team or '',
            "team_type": self.team_type or '',
            "skill_category": self.skill_category or '',
            "total_human_resource": float(self.total_human_resource) if self.total_human_resource else 0.00,
            "zte_human_resource": float(self.zte_human_resource) if self.zte_human_resource else 0.00,
            "outsourcing_human_resource": float(self.outsourcing_human_resource) if self.outsourcing_human_resource else 0.00,
            "demand_delivery_available": float(self.demand_delivery_available) if self.demand_delivery_available else 0.00,
            "remaining_available_human_resource": float(self.remaining_available_human_resource) if self.remaining_available_human_resource else 0.00,
            "used_human_resource": float(self.used_human_resource) if self.used_human_resource else 0.00,
            "used_human_resource1": float(self.used_human_resource1) if self.used_human_resource1 else 0.00,
            "used_human_resource2": float(self.used_human_resource2) if self.used_human_resource2 else 0.00,
            "date": self.date or '',
        }
