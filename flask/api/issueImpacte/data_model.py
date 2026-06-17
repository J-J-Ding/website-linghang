from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime

from electric_knowledge.data_model import db


class IssueImpactCaseTable(db.Model):
    """
    故障波及案例单表
    根据案例单录入详设（开发）文档设计
    """
    __bind_key__ = 'db3'
    __tablename__ = 'issue_impact_case_table'
    
    # 主键
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    
    # 案例基本信息
    case_id = Column(String(64), nullable=True, unique=True, comment='案例ID')
    case_title = Column(String(512), nullable=True, comment='案例标题')
    belong_project = Column(String(128), nullable=True, comment='归属项目')
    case_found_site = Column(String(128), nullable=True, comment='案例发现局点')
    priority = Column(String(32), nullable=True, comment='优先级：高/中/低')
    quality_topic = Column(String(128), nullable=True, comment='关联质量专题')
    function_category = Column(String(128), nullable=True, comment='功能分类')
    component = Column(String(128), nullable=True, comment='组件')
    part = Column(String(128), nullable=True, comment='部件')
    status = Column(String(32), nullable=True, default='新建', comment='状态：新建/分析中/横推中/审批中/已完成/已关闭')
    
    # 工作项信息
    work_item_id = Column(String(64), nullable=True, unique=True, comment='工作项ID（用于去重）')
    work_item_type = Column(String(32), nullable=True, comment='工作项类型：外场故障/内场故障')
    work_item_title = Column(String(512), nullable=True, comment='工作项标题')
    
    # 案例时间信息
    case_occur_time = Column(DateTime, nullable=True, comment='案例发生时间')
    case_trigger_site = Column(String(128), nullable=True, comment='案例触发局点')
    
    # 业务影响
    affect_business = Column(String(8), nullable=True, comment='是否影响业务：是/否')
    
    # 故障信息
    modify_fault_record = Column(String(255), nullable=True, comment='修改故障入库记录')
    fault_code = Column(Text, nullable=True, comment='故障代码')
    modified_code = Column(Text, nullable=True, comment='修改后代码')
    introduce_fault_record = Column(String(255), nullable=True, comment='引入故障入库记录')
    
    # 流程相关
    need_horizontal_push = Column(String(8), nullable=True, comment='是否需要横推：是/否')
    need_notice = Column(String(8), nullable=True, comment='是否需要通告：是/否')
    horizontal_push_ticket = Column(String(64), nullable=True, comment='横推单ID')
    rdc_notice_ticket = Column(String(64), nullable=True, comment='RDC通告单ID')
    rdc_review_ticket = Column(String(64), nullable=True, comment='RDC复盘单ID')
    
    # 指派信息
    assign_to = Column(String(64), nullable=True, comment='指派给')
    
    # 系统字段
    create_time = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')
    create_by = Column(String(64), nullable=True, comment='创建人')
    update_by = Column(String(64), nullable=True, comment='更新人')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "caseId": self.case_id,
            "caseTitle": self.case_title,
            "belongProject": self.belong_project,
            "caseFoundSite": self.case_found_site,
            "priority": self.priority,
            "qualityTopic": self.quality_topic,
            "functionCategory": self.function_category,
            "component": self.component,
            "part": self.part,
            "status": self.status,
            "workItemId": self.work_item_id,
            "workItemType": self.work_item_type,
            "workItemTitle": self.work_item_title,
            "caseOccurTime": self.case_occur_time.isoformat() if self.case_occur_time else None,
            "caseTriggerSite": self.case_trigger_site,
            "affectBusiness": self.affect_business,
            "modifyFaultRecord": self.modify_fault_record,
            "faultCode": self.fault_code,
            "modifiedCode": self.modified_code,
            "introduceFaultRecord": self.introduce_fault_record,
            "needHorizontalPush": self.need_horizontal_push,
            "needNotice": self.need_notice,
            "horizontalPushTicket": self.horizontal_push_ticket,
            "rdcNoticeTicket": self.rdc_notice_ticket,
            "rdcReviewTicket": self.rdc_review_ticket,
            "createTime": self.create_time.isoformat() if self.create_time else None,
            "updateTime": self.update_time.isoformat() if self.update_time else None,
            "createBy": self.create_by,
            "updateBy": self.update_by,
            "assignTo": self.assign_to if self.assign_to else "",
        }

