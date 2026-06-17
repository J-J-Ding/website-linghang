from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Column, Boolean, Integer, String, FLOAT, Text, DateTime, ForeignKey


db = SQLAlchemy()
# 加载环境变量
# load_dotenv()

class QualityCaseTable(db.Model):
    __bind_key__ = 'db1'
    __tablename__ = 'quality_case_table'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    case_id = Column(Integer, nullable=True)  # 案例ID
    work_item_type = Column(String(32), nullable=True)  # 工作项类型
    work_item_id = Column(String(64), nullable=True)  # 工作项ID
    work_item_title = Column(String(512), nullable=True)  # 工作项标题
    modify_fault_record = Column(String(255), nullable=True)  # 修改故障记录
    introduce_fault_record = Column(String(255), nullable=True)  # 引入故障记录
    fault_branch = Column(String(128), nullable=True)  # 故障分支
    key_fault_code = Column(Text, nullable=True)  # 关键故障代码
    modified_code = Column(Text, nullable=True)  # 修改后代码
    status = Column(String(32), nullable=True)  # 状态
    assignee = Column(String(64), nullable=True)  # 指派人
    horizontal_push_ticket = Column(Integer, nullable=True)  # 横推单
    notice_ticket = Column(String(64), nullable=True)  # 通告单
    review_ticket = Column(Integer, nullable=True)  # 复盘单
    case_category = Column(String(32), nullable=True)  # 案例分类
    performance_category = Column(String(64), nullable=True)  # 性能分类
    create_time = Column(DateTime, default=datetime.now, nullable=False)  # 创建时间
    completion_time = Column(DateTime, nullable=True)  # 完成时间
    problem_description = Column(String(1024), nullable=True)  # 问题描述
    belong_project = Column(String(128), nullable=True)  # 归属项目
    occurrence_time = Column(DateTime, nullable=True)  # 发生时间
    trigger_first_office = Column(String(128), nullable=True)  # 触发首局
    closure_time = Column(DateTime, nullable=True)  # 闭环时间
    closure_responsible_person = Column(String(64), nullable=True)  # 闭环责任人
    affect_business_flag = Column(String(8), nullable=True)  # 是否影响业务
    root_cause = Column(Text, nullable=True)  # 问题根因
    emergency_method = Column(Text, nullable=True)  # 应急方法
    inspection_method = Column(Text, nullable=True)  # 巡检方法
    avoidance_method = Column(Text, nullable=True)  # 规避方法
    solution_version = Column(String(128), nullable=True)  # 解决版本
    version_time = Column(DateTime, nullable=True)  # 版本时间
    code_document_link = Column(String(255), nullable=True)  # 代码/文档链接
    problem_code_annotation = Column(String(255), nullable=True)  # 问题代码标注
    self_test_record = Column(String(255), nullable=True)  # 自测记录
    system_test_record = Column(String(255), nullable=True)  # 系测记录
    introduction_point_root_cause = Column(String(128), nullable=True)  # 引入点根因分类
    feature = Column(String(128), nullable=True)  # 特性
    component = Column(String(128), nullable=True)  # 组件
    board_part = Column(String(128), nullable=True)  # 单板部件
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)  # 更新时间

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "work_item_type": self.work_item_type,
            "work_item_id": self.work_item_id,
            "work_item_title": self.work_item_title,
            "modify_fault_record": self.modify_fault_record,
            "introduce_fault_record": self.introduce_fault_record,
            "fault_branch": self.fault_branch,
            "key_fault_code": self.key_fault_code,
            "modified_code": self.modified_code,
            "status": self.status,
            "assignee": self.assignee,
            "horizontal_push_ticket": self.horizontal_push_ticket,
            "notice_ticket": self.notice_ticket,
            "review_ticket": self.review_ticket,
            "case_category": self.case_category,
            "performance_category": self.performance_category,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "occurrence_time": self.occurrence_time.isoformat() if self.occurrence_time else None,
            "closure_time": self.closure_time.isoformat() if self.closure_time else None,
            "problem_description": self.problem_description,
            "belong_project": self.belong_project,
            "trigger_first_office": self.trigger_first_office,
            "closure_responsible_person": self.closure_responsible_person,
            "affect_business_flag": self.affect_business_flag,  # 修正字段名
            "root_cause": self.root_cause,
            "emergency_method": self.emergency_method,
            "inspection_method": self.inspection_method,
            "avoidance_method": self.avoidance_method,
            "solution_version": self.solution_version,
            "version_time": self.version_time.isoformat() if self.version_time else None,
            "code_document_link": self.code_document_link,
            "problem_code_annotation": self.problem_code_annotation,
            "self_test_record": self.self_test_record,
            "system_test_record": self.system_test_record,
            "introduction_point_root_cause": self.introduction_point_root_cause,
            "feature": self.feature,
            "component": self.component,
            "board_part": self.board_part,
            "update_time": self.update_time.isoformat() if self.update_time else None
        }