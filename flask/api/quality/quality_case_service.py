from electric_knowledge.data_model import db
from quality.data_model import QualityCaseTable
from flask import request, jsonify


def query_all_quality_case_list_by_param():
    """查询全部质量案例数据"""
    try:
        # 构建查询
        model_list = db.session.query(QualityCaseTable).order_by(QualityCaseTable.id.asc()).all()
        # 转换为字典格式
        data_list = [item.to_dict() for item in model_list]
        # 返回结果
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": data_list})
    except Exception as e:
        return jsonify({"code": 400, "status": "success", "message": "获取失败", "data": {}})