from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, FLOAT, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from electric_knowledge.data_model import db

# 加载环境变量
# load_dotenv()

class TEST_BUSINESS_MODEL_RATE_TABLE(db.Model):
    __bind_key__ = 'db_demo'
    __tablename__ = "test_business_model_rate_table"  # 对应数据库中的表名
    id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    network_element_business_model_rate = db.Column(db.String(100), nullable=True)
    business_type_list = db.Column(db.String(200), nullable=True)
    create_time = db.Column(db.DateTime, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    operator_person = db.Column(db.String(50), nullable=True)
    effective_flag = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {"id": self.id, "network_element_business_model_rate": self.network_element_business_model_rate, 
                "business_type_list": self.business_type_list, "create_time": self.create_time, 
                "update_time": self.update_time, "operator_person": self.operator_person, "effective_flag": self.effective_flag,
                }
