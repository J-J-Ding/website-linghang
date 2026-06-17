from sqlalchemy import or_, and_, func, distinct
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from requirement_schedule.data_model import db, REQUIREMENT_DEV_HUMAN_RESOURCE, PERSON_SKILL_MAP
from flask import request, jsonify, send_file
import logging
import pandas as pd
import io

# 导入 manpower_calculate 用于在更新人力投入后重新计算可用人力
try:
    from requirement_schedule.all_team_manpower import manpower_calculate
except ImportError:
    from all_team_manpower import manpower_calculate

logger = logging.getLogger("Logger")


def pad_employee_id(employee_id: str) -> str:
    """
    工号补零处理：如果工号少于8位，前面补零到8位
    
    Args:
        employee_id: 原始工号字符串
        
    Returns:
        补零后的工号字符串
    """
    if not employee_id:
        return employee_id
    # 移除可能存在的前导/尾随空格
    employee_id = str(employee_id).strip()
    # 如果是纯数字且少于8位，补零
    if employee_id.isdigit() and len(employee_id) < 8:
        return employee_id.zfill(8)
    return employee_id

# 认证凭据配置
MANPOWER_CALCULATE_USERNAME = "10326873"
MANPOWER_CALCULATE_ENCRYPTED_PASSWORD = "YnV6YWlodTE5OTcu"


# 定义查询参数模型
class HumanResourceSettingData(BaseModel):
    id: Optional[int] = None
    department: Optional[str] = None
    domain: Optional[str] = None
    team: Optional[str] = None
    person_belong: Optional[str] = None
    employee_id: Optional[str] = None
    name: Optional[str] = None
    leave_time: Optional[str] = None
    skill_category: Optional[str] = None
    year_month: Optional[str] = None
    demand_human_power_ratio: Optional[float] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def queryHumanResourceSettingByParams():
    """
    根据条件查询需求开发投入人力设置
    ---
    tags:
      - 需求开发投入人力设置
    description: 根据条件查询需求开发投入人力设置
    parameters:
      - name: department
        in: query
        type: string
        required: false
        description: 部门
      - name: domain
        in: query
        type: string
        required: false
        description: 领域
      - name: team
        in: query
        type: string
        required: false
        description: 团队
      - name: year
        in: query
        type: string
        required: false
        description: 年份（如 2026）
      - name: employee_id
        in: query
        type: string
        required: false
        description: 工号（支持模糊查询）
      - name: name
        in: query
        type: string
        required: false
        description: 姓名（支持模糊查询）
    responses:
      200:
        description: 成功返回数据
    """
    try:
        department = request.args.get('department', '').strip()
        domain = request.args.get('domain', '').strip()
        # 支持团队多选：接收数组或单个值
        team_param = request.args.getlist('team')  # 获取所有team参数值（支持多选）
        if not team_param:
            team_param = request.args.get('team', '').strip()  # 兼容单个值的情况
            if team_param:
                team_param = [team_param]
        else:
            team_param = [t.strip() for t in team_param if t.strip()]  # 过滤空值
        year = request.args.get('year', '').strip()
        employee_id = request.args.get('employee_id', '').strip()
        name = request.args.get('name', '').strip()

        logger.info(f"查询需求开发投入人力设置 - department: {department}, domain: {domain}, team: {team_param}, year: {year}, employee_id: {employee_id}, name: {name}")

        # 构建查询条件
        conditions = []
        if department:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.department == department)
        if domain:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.domain == domain)
        if team_param and len(team_param) > 0:
            # 支持多选：使用 IN 查询
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.team.in_(team_param))
        if year:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.year_month.like(f"{year}-%"))
        if employee_id:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id.like(f"%{employee_id}%"))
        if name:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.name.like(f"%{name}%"))

        query = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE)
        if conditions:
            query = query.filter(and_(*conditions))

        results = query.order_by(
            REQUIREMENT_DEV_HUMAN_RESOURCE.year_month,
            REQUIREMENT_DEV_HUMAN_RESOURCE.domain,
            REQUIREMENT_DEV_HUMAN_RESOURCE.team,
            REQUIREMENT_DEV_HUMAN_RESOURCE.person_belong
        ).all()

        data = [item.to_dict() for item in results]

        # 工号补零处理：确保所有工号显示为8位
        for item in data:
            if item.get('employee_id'):
                item['employee_id'] = pad_employee_id(item['employee_id'])

        logger.info(f"查询需求开发投入人力设置成功 - 共 {len(data)} 条记录")
        return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data})
    except Exception as e:
        logger.error(f"查询需求开发投入人力设置失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"查询失败: {str(e)}", "data": []})


def aggregateFromPersonSkillMap():
    """
    从 person_skill_map 聚合生成/更新 requirement_dev_human_resource
    ---
    tags:
      - 需求开发投入人力设置
    description: 基于 person_skill_map 表聚合生成/更新 requirement_dev_human_resource 表的数据。
                 为每个 (department, domain, team, person_belong, employee_id, skill_category) 组合生成指定年份的12个月数据。
    parameters:
      - name: department
        in: query
        type: string
        required: false
        description: 部门筛选条件
      - name: domain
        in: query
        type: string
        required: false
        description: 领域筛选条件
      - name: team
        in: query
        type: string
        required: false
        description: 团队筛选条件
      - name: year
        in: query
        type: string
        required: false
        description: 年份（如 2026），如果不提供则使用当前年份
    responses:
      200:
        description: 成功返回数据
    """
    try:
        department = request.args.get('department', '').strip()
        domain = request.args.get('domain', '').strip()
        team = request.args.get('team', '').strip()
        year = request.args.get('year', '').strip()

        # 如果年份为空，使用当前年份
        if not year:
            year = str(datetime.now().year)

        logger.info(f"从 person_skill_map 聚合数据 - department: {department}, domain: {domain}, team: {team}, year: {year}")

        # 构建 person_skill_map 查询条件
        psm_conditions = []
        if department:
            psm_conditions.append(PERSON_SKILL_MAP.department == department)
        if domain:
            psm_conditions.append(PERSON_SKILL_MAP.domain == domain)
        if team:
            psm_conditions.append(PERSON_SKILL_MAP.team == team)

        # 查询 person_skill_map 数据
        psm_query = db.session.query(PERSON_SKILL_MAP)
        if psm_conditions:
            psm_query = psm_query.filter(and_(*psm_conditions))

        psm_results = psm_query.all()

        if not psm_results:
            logger.info("person_skill_map 中没有匹配的数据")
            return jsonify({"code": 200, "status": "success", "message": "没有需要聚合的数据", "data": []})

        # 按 (department, domain, team, person_belong, employee_id, skill_category) 分组聚合
        # 为每个人员生成数据
        grouped_data = {}
        
        for psm in psm_results:
            # 工号补零处理
            padded_employee_id = pad_employee_id(psm.employee_id)

            # 构建分组键：按"部门"、"领域"、"团队"、"人员归属"、"工号"、"技能/特性分类"分组
            group_key = (
                psm.department or '',
                psm.domain,
                psm.team,
                psm.person_belong,
                padded_employee_id,
                psm.skill_category or ''
            )

            # 如果该组合已存在，跳过（去重）
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'department': psm.department or '',
                    'domain': psm.domain,
                    'team': psm.team,
                    'person_belong': psm.person_belong,
                    'employee_id': padded_employee_id,
                    'name': psm.name,
                    'leave_time': psm.leave_time or '',
                    'skill_category': psm.skill_category or ''
                }

        # 为每个分组生成12个月的数据
        # 优化：先批量查询已存在的记录，避免逐条查询
        created_count = 0
        updated_count = 0

        # 收集所有需要处理的员工ID和年月
        employee_ids = list(set(g['employee_id'] for g in grouped_data.values()))
        year_months = [f"{year}-{month:02d}" for month in range(1, 13)]

        # 批量查询已存在的记录：一次查询获取所有相关记录
        existing_records = {}
        if employee_ids and year_months:
            existing_query = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE).filter(
                and_(
                    REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id.in_(employee_ids),
                    REQUIREMENT_DEV_HUMAN_RESOURCE.year_month.in_(year_months)
                )
            ).all()

            # 构建查找字典：以 (year_month, domain, team, person_belong, employee_id, skill_category) 为键
            for rec in existing_query:
                key = (rec.year_month, rec.domain, rec.team, rec.person_belong, 
                       rec.employee_id, rec.skill_category)
                existing_records[key] = rec

        # 处理所有记录
        for group_key, group_info in grouped_data.items():
            for month in range(1, 13):
                year_month = f"{year}-{month:02d}"
                lookup_key = (year_month, group_info['domain'], group_info['team'],
                             group_info['person_belong'], group_info['employee_id'], 
                             group_info['skill_category'])

                existing = existing_records.get(lookup_key)
                if existing:
                    # 更新基础字段，保留 demand_human_power_ratio 和产品字段
                    existing.department = group_info['department']
                    existing.name = group_info['name']
                    existing.leave_time = group_info['leave_time']
                    updated_count += 1
                else:
                    # 创建新记录
                    new_record = REQUIREMENT_DEV_HUMAN_RESOURCE(
                        department=group_info['department'],
                        domain=group_info['domain'],
                        team=group_info['team'],
                        person_belong=group_info['person_belong'],
                        employee_id=group_info['employee_id'],
                        name=group_info['name'],
                        leave_time=group_info['leave_time'],
                        skill_category=group_info['skill_category'],
                        year_month=year_month,
                        demand_human_power_ratio=1.00
                    )
                    db.session.add(new_record)
                    created_count += 1

        db.session.commit()
        logger.info(f"聚合完成 - 创建：{created_count}, 更新：{updated_count}")
        message = f"聚合完成 - 创建：{created_count} 条，更新：{updated_count} 条"
        
        # 聚合成功后，调用 manpower_calculate 重新计算可用人力
        if created_count > 0 or updated_count > 0:
            try:
                logger.info("开始调用 manpower_calculate 重新计算可用人力...")
                manpower_calculate(
                    username=MANPOWER_CALCULATE_USERNAME,
                    encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
                )
                logger.info("manpower_calculate 调用成功，可用人力已重新计算")
            except Exception as calc_error:
                logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)
                # 不阻断主流程，记录错误即可
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": message,
            "data": {"created": created_count, "updated": updated_count}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"从 person_skill_map 聚合数据失败：{str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"聚合失败：{str(e)}", "data": []})


def updateHumanResourceSetting():
    """
    更新需求开发投入人力设置
    ---
    tags:
      - 需求开发投入人力设置
    description: 更新需求开发投入人力设置（支持单个和批量）
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: []
          properties:
            data:
              type: array
              description: 需求开发投入人力设置数据数组
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        setting_list = data.get('data', [])

        if not setting_list:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})

        updated_count = 0
        for setting_data in setting_list:
            setting_id = setting_data.get('id')
            if not setting_id:
                continue

            # 构建更新数据
            update_data = {}
            if 'demand_human_power_ratio' in setting_data:
                ratio = setting_data['demand_human_power_ratio']
                # 验证范围 0~1
                if ratio is not None:
                    try:
                        ratio = float(ratio)
                    except Exception:
                        return jsonify({"code": 400, "status": "error", "message": "需求人力占比必须是数字", "data": []})
                    if ratio < 0 or ratio > 1:
                        return jsonify({"code": 400, "status": "error", "message": "需求人力占比必须在0~1之间", "data": []})
                    update_data['demand_human_power_ratio'] = ratio
            
            # 更新 4 个产品字段（范围 0~1，且和为 1 或 0）
            product_fields = ['zxone_19700', 'zxone_9700', 'zxmp_m721', 'zxone_nton']
            product_values = {}
            has_product_value = any(field in setting_data for field in product_fields)
            
            if has_product_value:
                total_ratio = 0.0
                for field in product_fields:
                    value = setting_data.get(field, 0)
                    if value is None or value == '':
                        value = 0
                    try:
                        value = float(value)
                    except Exception:
                        return jsonify({"code": 400, "status": "error", "message": f"{field} 必须是数字", "data": []})
                    if value < 0 or value > 1:
                        return jsonify({"code": 400, "status": "error", "message": "4 个产品投入占比必须都在 0~1 之间", "data": []})
                    product_values[field] = value
                    total_ratio += value
            
                # 获取需求人力占比（用于判断产品占比之和应该为 0 还是 1）
                demand_ratio = setting_data.get('demand_human_power_ratio', None)
                if demand_ratio is not None:
                    try:
                        demand_ratio = float(demand_ratio)
                    except Exception:
                        return jsonify({"code": 400, "status": "error", "message": "需求人力占比必须是数字", "data": []})
                
                # 根据需求人力占比判断产品占比之和的期望值
                # 需求人力占比为 0 时，产品占比之和应为 0；否则应为 1
                if demand_ratio is not None and demand_ratio == 0:
                    expected_total = 0.0
                    error_message = "需求人力占比为 0 时，产品投入占比之和必须为 0"
                else:
                    expected_total = 1.0
                    error_message = "4 个产品投入占比之和必须为 1.00"
            
                # 允许微小浮点误差
                if abs(total_ratio - expected_total) > 1e-6:
                    return jsonify({"code": 400, "status": "error", "message": error_message, "data": []})
            
                # 校验通过后写入更新数据
                update_data.update(product_values)

            if update_data:
                db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE) \
                    .filter(REQUIREMENT_DEV_HUMAN_RESOURCE.id == setting_id) \
                    .update(update_data)
                updated_count += 1

        db.session.commit()
        logger.info(f"更新需求开发投入人力设置成功 - 共更新 {updated_count} 条记录")
        
        # 更新成功后，调用 manpower_calculate 重新计算可用人力
        if updated_count > 0:
            try:
                logger.info("开始调用 manpower_calculate 重新计算可用人力...")
                manpower_calculate(
                    username=MANPOWER_CALCULATE_USERNAME,
                    encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
                )
                logger.info("manpower_calculate 调用成功，可用人力已重新计算")
            except Exception as calc_error:
                logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)
                # 不阻断主流程，记录错误即可
        
        return jsonify({"code": 200, "status": "success", "message": f"成功更新 {updated_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新需求开发投入人力设置失败：{str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"更新失败：{str(e)}", "data": []})


def deleteHumanResourceSetting():
    """
    删除需求开发投入人力记录（支持单条或批量）
    ---
    tags:
      - 需求开发投入人力设置
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            ids:
              type: array
              description: 要删除的记录ID列表
    responses:
      200:
        description: 删除成功
    """
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"code": 400, "status": "error", "message": "ids 不能为空", "data": []})

        deleted_count = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE) \
            .filter(REQUIREMENT_DEV_HUMAN_RESOURCE.id.in_(ids)) \
            .delete(synchronize_session=False)
        db.session.commit()
        logger.info(f"删除需求开发投入人力记录成功 - 共删除 {deleted_count} 条")
        
        # 删除成功后，调用 manpower_calculate 重新计算可用人力
        if deleted_count > 0:
            try:
                logger.info("开始调用 manpower_calculate 重新计算可用人力...")
                manpower_calculate(
                    username=MANPOWER_CALCULATE_USERNAME,
                    encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
                )
                logger.info("manpower_calculate 调用成功，可用人力已重新计算")
            except Exception as calc_error:
                logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)
                # 不阻断主流程，记录错误即可
        
        return jsonify({"code": 200, "status": "success", "message": f"成功删除 {deleted_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除需求开发投入人力记录失败：{str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"删除失败：{str(e)}", "data": []})


def batchDeleteHumanResourceSetting():
    """
    批量删除需求开发投入人力记录（按筛选条件删除）
    ---
    tags:
      - 需求开发投入人力设置
    description: 按筛选条件批量删除记录。条件为"团队"或"工号"；同时提供时按工号删除（工号优先）。
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            team:
              type: array
              description: 团队列表
              items:
                type: string
            employee_id:
              type: array
              description: 工号列表
              items:
                type: string
    responses:
      200:
        description: 删除成功
    """
    try:
        print("===== batchDeleteHumanResourceSetting 开始 =====")
        print(f"request.method: {request.method}")
        print(f"request.content_type: {request.content_type}")
        print(f"request.headers Content-Type: {request.headers.get('Content-Type')}")
        print(f"request.raw_data: {request.get_data(as_text=True)}")

        data = request.get_json()
        print(f"request.get_json() 结果: {data}")

        if data is None:
            print("WARNING: request.get_json() 返回 None，尝试手动解析")
            raw = request.get_data(as_text=True)
            import json
            try:
                data = json.loads(raw)
                print(f"手动解析 JSON 成功: {data}")
            except Exception as parse_err:
                print(f"手动解析 JSON 失败: {parse_err}")
                return jsonify({"code": 400, "status": "error", "message": f"请求体解析失败，原始数据：{raw[:200]}", "data": []})

        team_list = data.get('team', [])
        employee_id_list = data.get('employee_id', [])
        print(f"team_list: {team_list}")
        print(f"employee_id_list: {employee_id_list}")

        # 过滤空值，并对工号做补零处理
        team_list = [t.strip() for t in team_list if t and str(t).strip()]
        employee_id_list = [pad_employee_id(e.strip()) for e in employee_id_list if e and str(e).strip()]
        print(f"过滤后 team_list: {team_list}")
        print(f"过滤后 employee_id_list: {employee_id_list}")

        # 至少需要提供一个条件，防止误删全表
        if not team_list and not employee_id_list:
            print("ERROR: 团队和工号都为空，拒绝执行")
            return jsonify({"code": 400, "status": "error", "message": "至少需要提供团队或工号作为删除条件", "data": []})

        # 工号优先：同时提供团队和工号时，按工号删除
        if employee_id_list:
            condition = REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id.in_(employee_id_list)
            condition_desc = f"工号：{', '.join(employee_id_list)}"
        else:
            condition = REQUIREMENT_DEV_HUMAN_RESOURCE.team.in_(team_list)
            condition_desc = f"团队：{', '.join(team_list)}"

        print(f"删除条件: {condition_desc}")
        logger.info(f"批量删除需求开发投入人力记录 - 条件：{condition_desc}")

        deleted_count = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE) \
            .filter(condition) \
            .delete(synchronize_session=False)
        db.session.commit()
        print(f"删除完成，共删除 {deleted_count} 条")
        logger.info(f"批量删除需求开发投入人力记录成功 - 条件：{condition_desc}，共删除 {deleted_count} 条")

        # 删除成功后，调用 manpower_calculate 重新计算可用人力
        if deleted_count > 0:
            try:
                logger.info("开始调用 manpower_calculate 重新计算可用人力...")
                manpower_calculate(
                    username=MANPOWER_CALCULATE_USERNAME,
                    encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
                )
                logger.info("manpower_calculate 调用成功，可用人力已重新计算")
            except Exception as calc_error:
                logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)

        print("===== batchDeleteHumanResourceSetting 完成 =====")
        return jsonify({"code": 200, "status": "success", "message": f"按{condition_desc}批量删除成功，共删除 {deleted_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        print(f"===== batchDeleteHumanResourceSetting 异常: {str(e)} =====")
        logger.error(f"批量删除需求开发投入人力记录失败：{str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"批量删除失败：{str(e)}", "data": []})


def getHumanResourceSettingOptions():
    """
    获取需求开发投入人力设置的筛选选项
    ---
    tags:
      - 需求开发投入人力设置
    description: 获取部门、领域、团队的选项列表
    parameters:
      - name: option_type
        in: query
        type: string
        required: true
        description: 选项类型 (department, domain, team)
    responses:
      200:
        description: 成功返回数据
    """
    try:
        option_type = request.args.get('option_type', '').strip()
        if not option_type:
            return jsonify({"code": 400, "status": "error", "message": "option_type参数不能为空", "data": []})

        logger.info(f"获取需求开发投入人力设置选项 - option_type: {option_type}")

        column_map = {
            'department': REQUIREMENT_DEV_HUMAN_RESOURCE.department,
            'domain': REQUIREMENT_DEV_HUMAN_RESOURCE.domain,
            'team': REQUIREMENT_DEV_HUMAN_RESOURCE.team,
        }

        column_field = column_map.get(option_type)
        if not column_field:
            return jsonify({"code": 400, "status": "error", "message": f"不支持的option_type: {option_type}", "data": []})

        try:
            results = db.session.query(column_field) \
                .filter(
                    and_(
                        column_field.isnot(None),
                        column_field != ''
                    )
                ) \
                .distinct() \
                .all()

            values = [item[0] for item in results if item[0] and str(item[0]).strip()]
            unique_values = sorted(list(set(values)))
            logger.info(f"获取{option_type}成功 - 数量: {len(unique_values)}")
        except Exception as e:
            logger.error(f"查询{option_type}失败: {str(e)}", exc_info=True)
            raise

        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": unique_values})
    except Exception as e:
        logger.error(f"获取需求开发投入人力设置选项失败 - option_type: {option_type}, 错误: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def syncRequirementDevHumanResource(domain, team, year=None):
    """
    同步更新 requirement_dev_human_resource（当 person_skill_map 更新时调用）
    内部函数，不对外暴露
    基于 person_skill_map 表生成数据
    :param year: 指定年份（如 '2026'），若不传则默认使用当前年份，生成该年全 12 个月的数据
    """
    try:
        # 使用指定年份，若未指定则用当前年份
        current_year = str(year).strip() if year and str(year).strip() else str(datetime.now().year)

        # 查询 person_skill_map 中匹配的记录
        psm_records = db.session.query(PERSON_SKILL_MAP).filter(
            and_(
                PERSON_SKILL_MAP.domain == domain,
                PERSON_SKILL_MAP.team == team
            )
        ).all()

        if not psm_records:
            return

        # 按 (department, domain, team, person_belong, employee_id, skill_category) 分组
        # 为每个人员生成数据
        grouped_data = {}
        for psm in psm_records:
            # 工号补零处理
            padded_employee_id = pad_employee_id(psm.employee_id)

            # 构建分组键：按"部门"、"领域"、"团队"、"人员归属"、"工号"、"技能/特性分类"分组
            group_key = (
                psm.department or '',
                psm.domain,
                psm.team,
                psm.person_belong,
                padded_employee_id,
                psm.skill_category or ''
            )
            # 如果该组合已存在，跳过（去重）
            if group_key not in grouped_data:
                grouped_data[group_key] = {
                    'department': psm.department or '',
                    'domain': psm.domain,
                    'team': psm.team,
                    'person_belong': psm.person_belong,
                    'employee_id': padded_employee_id,
                    'name': psm.name,
                    'leave_time': psm.leave_time or '',
                    'skill_category': psm.skill_category or ''
                }

        # 更新或创建 requirement_dev_human_resource 记录
        for group_key, group_info in grouped_data.items():
            for month in range(1, 13):
                year_month = f"{current_year}-{month:02d}"

                # 检查记录是否已存在（唯一性约束：year_month, domain, team, person_belong, employee_id, skill_category）
                existing = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE).filter(
                    and_(
                        REQUIREMENT_DEV_HUMAN_RESOURCE.year_month == year_month,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.domain == group_info['domain'],
                        REQUIREMENT_DEV_HUMAN_RESOURCE.team == group_info['team'],
                        REQUIREMENT_DEV_HUMAN_RESOURCE.person_belong == group_info['person_belong'],
                        REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id == group_info['employee_id'],
                        REQUIREMENT_DEV_HUMAN_RESOURCE.skill_category == group_info['skill_category']
                    )
                ).first()

                if existing:
                    # 更新基础字段，保留 demand_human_power_ratio 和产品字段
                    existing.department = group_info['department']
                    existing.name = group_info['name']
                    existing.leave_time = group_info['leave_time']
                else:
                    # 创建新记录
                    new_record = REQUIREMENT_DEV_HUMAN_RESOURCE(
                        department=group_info['department'],
                        domain=group_info['domain'],
                        team=group_info['team'],
                        person_belong=group_info['person_belong'],
                        employee_id=group_info['employee_id'],
                        name=group_info['name'],
                        leave_time=group_info['leave_time'],
                        skill_category=group_info['skill_category'],
                        year_month=year_month,
                        demand_human_power_ratio=1.00
                    )
                    db.session.add(new_record)

        db.session.commit()
        logger.info(f"同步 requirement_dev_human_resource 成功 - domain: {domain}, team: {team}")
        
        # 同步成功后，调用 manpower_calculate 重新计算可用人力
        try:
            logger.info("开始调用 manpower_calculate 重新计算可用人力...")
            manpower_calculate(
                username=MANPOWER_CALCULATE_USERNAME,
                encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
            )
            logger.info("manpower_calculate 调用成功，可用人力已重新计算")
        except Exception as calc_error:
            logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)
            # 不阻断主流程，记录错误即可
    except Exception as e:
        db.session.rollback()
        logger.error(f"同步 requirement_dev_human_resource 失败：{str(e)}", exc_info=True)


def triggerSyncRequirementDevHumanResource():
    """
    手动触发同步需求交付人力投入数据
    ---
    tags:
      - 需求开发投入人力设置
    description: 手动触发同步指定 (领域，团队) 的需求交付人力投入数据，支持指定年份
    parameters:
      - name: domain
        in: query
        type: string
        required: true
        description: 领域（如 05-支撑）
      - name: team
        in: query
        type: string
        required: true
        description: 团队（如 支撑 - 北极星）
      - name: year
        in: query
        type: string
        required: false
        description: 年份（如 2026），不传则使用当前年份
    responses:
      200:
        description: 成功返回数据
    """
    try:
        domain = request.args.get('domain', '').strip()
        team = request.args.get('team', '').strip()
        year = request.args.get('year', '').strip()

        if not domain:
            return jsonify({"code": 400, "status": "error", "message": "domain 参数不能为空", "data": []})
        if not team:
            return jsonify({"code": 400, "status": "error", "message": "team 参数不能为空", "data": []})

        logger.info(f"手动触发同步需求交付人力投入 - domain: {domain}, team: {team}, year: {year if year else '当前年份'}")

        # 调用同步函数
        syncRequirementDevHumanResource(domain, team, year if year else None)

        return jsonify({
            "code": 200,
            "status": "success",
            "message": f"同步成功 - 领域：{domain}, 团队：{team}, 年份：{year if year else '当前年份'}",
            "data": []
        })
    except Exception as e:
        logger.error(f"手动触发同步需求交付人力投入失败：{str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"同步失败：{str(e)}", "data": []})


def importHumanResourceSetting():
    """
    批量导入开发人力投入数据
    ---
    tags:
      - 需求开发投入人力设置
    description: 批量导入开发人力投入数据（Excel文件），存在则更新，不存在则新增
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        description: 上传的Excel文件(.xlsx格式)
        required: true
        type: file
    responses:
      200:
        description: 成功返回数据
    """
    try:
        if 'file' not in request.files:
            return jsonify({"code": 400, "status": "error", "message": "未上传文件", "data": []})

        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"code": 400, "status": "error", "message": "仅支持上传 .xlsx 格式文件", "data": []})

        df = pd.read_excel(file, engine="openpyxl", dtype={'工号': str})
        df = df.fillna(value='')

        # 必填列（唯一键相关）；技能/特性分类 为可选字段
        required_columns = ['领域', '团队', '人员归属', '工号', '年月']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                "code": 400,
                "status": "error",
                "message": f"Excel文件缺少必填列: {', '.join(missing_columns)}",
                "data": []
            })

        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        error_messages = []
        failed_rows = []  # 校验失败的行，可供前端下载

        def normalize_str(value):
            if value is None:
                return ''
            return str(value).strip()

        def normalize_float(value, default=0.0):
            if value is None or value == '':
                return default
            try:
                return float(value)
            except Exception:
                return default

        # 预加载 person_skill_map 数据，构建工号 → 记录 的查找字典，用于校验
        psm_all = db.session.query(PERSON_SKILL_MAP).all()
        psm_lookup = {p.employee_id: p for p in psm_all}

        for index, row in df.iterrows():
            try:
                domain       = normalize_str(row.get('领域', ''))
                team         = normalize_str(row.get('团队', ''))
                person_belong = normalize_str(row.get('人员归属', ''))
                employee_id  = pad_employee_id(normalize_str(row.get('工号', '')))
                skill_category = normalize_str(row.get('技能/特性分类', ''))
                year_month   = normalize_str(row.get('年月', ''))

                # 必填字段不能为空（技能/特性分类 为可选，允许为空）
                if not all([domain, team, person_belong, employee_id, year_month]):
                    skipped_count += 1
                    error_messages.append(f"第{index + 2}行：必填字段（领域/团队/人员归属/工号/年月）不能为空")
                    continue

                department   = normalize_str(row.get('部门', ''))
                name         = normalize_str(row.get('姓名', ''))
                leave_time   = normalize_str(row.get('离职时间', ''))
                demand_human_power_ratio = normalize_float(row.get('需求人力占比'), 1.0)
                zxone_19700  = normalize_float(row.get('ZXONE 19700'), 0.0)
                zxone_9700   = normalize_float(row.get('ZXONE 9700'), 0.0)
                zxmp_m721    = normalize_float(row.get('ZXMP M721'), 0.0)
                zxone_nton   = normalize_float(row.get('ZXONE NTON'), 0.0)

                # ---- 校验1：工号必须在 person_skill_map 中存在 ----
                psm_record = psm_lookup.get(employee_id)
                if psm_record is None:
                    skipped_count += 1
                    reason = f"工号 {employee_id} 不在人员技能地图中，请先维护01人员技能地图"
                    error_messages.append(f"第{index + 2}行：{reason}")
                    failed_rows.append({
                        '行号': index + 2, '部门': department, '领域': domain, '团队': team,
                        '人员归属': person_belong, '工号': employee_id, '姓名': name,
                        '技能/特性分类': skill_category, '年月': year_month,
                        '需求人力占比': demand_human_power_ratio,
                        'ZXONE 19700': zxone_19700, 'ZXONE 9700': zxone_9700,
                        'ZXMP M721': zxmp_m721, 'ZXONE NTON': zxone_nton,
                        '失败原因': reason
                    })
                    continue

                # ---- 校验2：技能/特性分类必须在 person_skill_map 对应记录的技能列表里 ----
                psm_skill_str = psm_record.skill_category or ''
                if psm_skill_str and skill_category:
                    psm_skills = [s.strip() for s in psm_skill_str.split('；') if s.strip()]
                    if psm_skills and skill_category not in psm_skills:
                        skipped_count += 1
                        reason = (
                            f"工号 {employee_id} 的技能分类 '{skill_category}' 未在人员技能地图中"
                            f"（当前技能：{psm_skill_str}），请先更新01人员技能地图"
                        )
                        error_messages.append(f"第{index + 2}行：{reason}")
                        failed_rows.append({
                            '行号': index + 2, '部门': department, '领域': domain, '团队': team,
                            '人员归属': person_belong, '工号': employee_id, '姓名': name,
                            '技能/特性分类': skill_category, '年月': year_month,
                            '需求人力占比': demand_human_power_ratio,
                            'ZXONE 19700': zxone_19700, 'ZXONE 9700': zxone_9700,
                            'ZXMP M721': zxmp_m721, 'ZXONE NTON': zxone_nton,
                            '失败原因': reason
                        })
                        continue

                # 查找已有记录（唯一键：year_month, domain, team, person_belong, employee_id, skill_category）
                existing = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE).filter(
                    and_(
                        REQUIREMENT_DEV_HUMAN_RESOURCE.year_month == year_month,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.domain == domain,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.team == team,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.person_belong == person_belong,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id == employee_id,
                        REQUIREMENT_DEV_HUMAN_RESOURCE.skill_category == skill_category
                    )
                ).first()

                if existing:
                    existing.department = department
                    existing.name = name
                    existing.leave_time = leave_time
                    existing.demand_human_power_ratio = demand_human_power_ratio
                    existing.zxone_19700 = zxone_19700
                    existing.zxone_9700 = zxone_9700
                    existing.zxmp_m721 = zxmp_m721
                    existing.zxone_nton = zxone_nton
                    updated_count += 1
                else:
                    new_record = REQUIREMENT_DEV_HUMAN_RESOURCE(
                        department=department,
                        domain=domain,
                        team=team,
                        person_belong=person_belong,
                        employee_id=employee_id,
                        name=name,
                        leave_time=leave_time,
                        skill_category=skill_category,
                        year_month=year_month,
                        demand_human_power_ratio=demand_human_power_ratio,
                        zxone_19700=zxone_19700,
                        zxone_9700=zxone_9700,
                        zxmp_m721=zxmp_m721,
                        zxone_nton=zxone_nton
                    )
                    db.session.add(new_record)
                    inserted_count += 1

            except Exception as row_err:
                skipped_count += 1
                error_messages.append(f"第{index + 2}行处理失败: {str(row_err)}")

        db.session.commit()
        failed_count = len(failed_rows)
        msg = f"导入完成：新增 {inserted_count} 条，更新 {updated_count} 条，跳过 {skipped_count} 条"
        if failed_count:
            msg += f"（其中 {failed_count} 行因校验失败被跳过，可下载失败数据）"
        logger.info(f"导入开发人力投入完成 - 新增：{inserted_count}, 更新：{updated_count}, 跳过：{skipped_count}, 失败：{failed_count}")
        
        # 导入成功后，调用 manpower_calculate 重新计算可用人力
        if inserted_count > 0 or updated_count > 0:
            try:
                logger.info("开始调用 manpower_calculate 重新计算可用人力...")
                manpower_calculate(
                    username=MANPOWER_CALCULATE_USERNAME,
                    encrypted_password=MANPOWER_CALCULATE_ENCRYPTED_PASSWORD
                )
                logger.info("manpower_calculate 调用成功，可用人力已重新计算")
            except Exception as calc_error:
                logger.error(f"调用 manpower_calculate 失败：{str(calc_error)}", exc_info=True)
                # 不阻断主流程，记录错误即可
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": msg,
            "data": {
                "inserted": inserted_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "errors": error_messages,
                "failed_rows": failed_rows
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"导入开发人力投入失败：{str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"导入失败：{str(e)}", "data": []})


def exportHumanResourceSetting():
    """
    批量导出开发人力投入数据
    ---
    tags:
      - 需求开发投入人力设置
    description: 根据筛选条件导出开发人力投入数据为 Excel 文件（.xlsx）
    parameters:
      - name: department
        in: query
        type: string
        required: false
      - name: domain
        in: query
        type: string
        required: false
      - name: team
        in: query
        type: string
        required: false
      - name: year
        in: query
        type: string
        required: false
      - name: employee_id
        in: query
        type: string
        required: false
      - name: name
        in: query
        type: string
        required: false
    responses:
      200:
        description: 返回 Excel 文件
    """
    try:
        department = request.args.get('department', '').strip()
        domain = request.args.get('domain', '').strip()
        team_param = request.args.getlist('team')
        if not team_param:
            t = request.args.get('team', '').strip()
            team_param = [t] if t else []
        else:
            team_param = [t.strip() for t in team_param if t.strip()]
        year = request.args.get('year', '').strip()
        employee_id = request.args.get('employee_id', '').strip()
        name = request.args.get('name', '').strip()

        conditions = []
        if department:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.department == department)
        if domain:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.domain == domain)
        if team_param:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.team.in_(team_param))
        if year:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.year_month.like(f"{year}-%"))
        if employee_id:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id.like(f"%{employee_id}%"))
        if name:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.name.like(f"%{name}%"))

        query = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE)
        if conditions:
            query = query.filter(and_(*conditions))

        results = query.order_by(
            REQUIREMENT_DEV_HUMAN_RESOURCE.year_month,
            REQUIREMENT_DEV_HUMAN_RESOURCE.domain,
            REQUIREMENT_DEV_HUMAN_RESOURCE.team,
            REQUIREMENT_DEV_HUMAN_RESOURCE.person_belong
        ).all()

        rows = []
        for item in results:
            rows.append({
                '部门': item.department or '',
                '领域': item.domain or '',
                '团队': item.team or '',
                '人员归属': item.person_belong or '',
                '工号': pad_employee_id(item.employee_id) if item.employee_id else '',
                '姓名': item.name or '',
                '离职时间': item.leave_time or '',
                '技能/特性分类': item.skill_category or '',
                '年月': item.year_month or '',
                '需求人力占比': float(item.demand_human_power_ratio) if item.demand_human_power_ratio is not None else 1.00,
                'ZXONE 19700': float(item.zxone_19700) if item.zxone_19700 is not None else 0.00,
                'ZXONE 9700': float(item.zxone_9700) if item.zxone_9700 is not None else 0.00,
                'ZXMP M721': float(item.zxmp_m721) if item.zxmp_m721 is not None else 0.00,
                'ZXONE NTON': float(item.zxone_nton) if item.zxone_nton is not None else 0.00,
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='开发人力投入')
        output.seek(0)

        logger.info(f"导出开发人力投入数据成功 - 共 {len(rows)} 条记录")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='开发人力投入.xlsx'
        )
    except Exception as e:
        logger.error(f"导出开发人力投入数据失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"导出失败: {str(e)}", "data": []})
