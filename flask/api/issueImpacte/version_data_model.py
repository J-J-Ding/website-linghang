from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, UniqueConstraint

from electric_knowledge.data_model import db


class IssueImpactVersionTable(db.Model):
    """
    故障波及版本表
    """
    __bind_key__ = 'db3'
    __tablename__ = 'issue_impact_version_table'
    
    # 主键
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    version_id = Column(String(64), nullable=False, unique=True, comment='版本ID')
    
    # 版本基本信息
    version_name = Column(String(128), nullable=False, unique=True, comment='版本名称')
    belong_project = Column(String(128), nullable=True, comment='归属项目')
    release_time = Column(Date, nullable=True, comment='发布时间')
    historical_release_time = Column(Date, nullable=False, comment='历史版本发布时间')
    target_network = Column(String(512), nullable=True, comment='目标网络（逗号分隔）')
    involved_boards = Column(String(512), nullable=True, comment='涉及单板（逗号分隔）')
    branch = Column(String(128), nullable=False, comment='版本分支')
    
    # 系统字段
    create_time = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')
    create_by = Column(String(64), nullable=True, comment='创建人')
    update_by = Column(String(64), nullable=True, comment='更新人')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "versionId": self.version_id,
            "versionName": self.version_name,
            "belongProject": self.belong_project,
            "releaseTime": self.release_time.strftime('%Y-%m-%d') if self.release_time else None,
            "historicalReleaseTime": self.historical_release_time.strftime('%Y-%m-%d') if self.historical_release_time else None,
            "targetNetwork": self.target_network,
            "involvedBoards": self.involved_boards,
            "branch": self.branch,
            "createTime": self.create_time.isoformat() if self.create_time else None,
            "updateTime": self.update_time.isoformat() if self.update_time else None,
            "createBy": self.create_by,
            "updateBy": self.update_by,
        }


class IssueImpactVersionCaseRelationTable(db.Model):
    """
    故障波及版本案例关联表
    主键：版本ID + 案例ID
    """
    __bind_key__ = 'db3'
    __tablename__ = 'issue_impact_version_case_relation_table'
    
    # 主键
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    version_id = Column(String(64), nullable=False, comment='版本ID')
    case_id = Column(String(64), nullable=False, comment='案例ID')
    
    # 系统字段
    create_time = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')
    
    # 唯一约束：版本ID + 案例ID
    __table_args__ = (
        UniqueConstraint('version_id', 'case_id', name='uq_version_case'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "versionId": self.version_id,
            "caseId": self.case_id,
            "createTime": self.create_time.isoformat() if self.create_time else None,
            "updateTime": self.update_time.isoformat() if self.update_time else None,
        }
