"""
人力透视表API
"""
from flask import request, jsonify
from sqlalchemy import and_, func, case
from requirement_schedule.data_model import REQUIREMENT_DEV_HUMAN_RESOURCE, TEAM_MAPPING, db
import logging

logger = logging.getLogger("Logger")


def queryHumanResourcePivotByParams():
    """
    根据条件查询人力透视表（透视格式：年月作为列）
    ---
    tags:
      - 人力透视表
    description: 根据条件查询人力透视表，将年月作为列进行透视
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
        type: array
        required: false
        description: 团队（支持多选）
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

        logger.info(f"查询人力透视表 - department: {department}, domain: {domain}, team: {team_param}, year: {year}, employee_id: {employee_id}, name: {name}")

        # 构建查询条件
        conditions = []
        if department:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.department == department)
        if domain:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.domain == domain)
        if team_param and len(team_param) > 0:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.team.in_(team_param))
        if year:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.year_month.like(f"{year}-%"))
        if employee_id:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.employee_id.like(f"%{employee_id}%"))
        if name:
            conditions.append(REQUIREMENT_DEV_HUMAN_RESOURCE.name.like(f"%{name}%"))

        # 查询数据
        query = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE)
        if conditions:
            query = query.filter(and_(*conditions))

        results = query.order_by(
            REQUIREMENT_DEV_HUMAN_RESOURCE.department,
            REQUIREMENT_DEV_HUMAN_RESOURCE.domain,
            REQUIREMENT_DEV_HUMAN_RESOURCE.team,
            REQUIREMENT_DEV_HUMAN_RESOURCE.skill_category,
            REQUIREMENT_DEV_HUMAN_RESOURCE.year_month
        ).all()

        # 获取团队类型映射（从team_mapping表）
        # 构建 team -> team_type 的映射字典
        team_type_map = {}
        try:
            team_mappings = db.session.query(TEAM_MAPPING).all()
            for mapping in team_mappings:
                # 优先使用领域匹配的映射，如果没有领域匹配则使用通用映射
                key = (mapping.target_team, mapping.domain or '')
                if key not in team_type_map or mapping.domain:  # 如果有领域匹配，优先使用
                    team_type_map[key] = mapping.team_type
        except Exception as e:
            logger.warning(f"获取团队类型映射失败: {str(e)}")

        # 转换为透视表格式
        # 按 (department, domain, team, team_type, skill_category) 分组，去除重复数据
        # 对于同一分组下的不同人员，聚合各个月份的需求人力占比（求和）
        pivot_data = {}
        year_months = set()  # 收集所有年月，用于生成列

        for item in results:
            # 获取团队类型
            team_type = ''
            # 优先尝试领域匹配
            if (item.team, item.domain) in team_type_map:
                team_type = team_type_map[(item.team, item.domain)]
            elif (item.team, '') in team_type_map:
                team_type = team_type_map[(item.team, '')]
            
            # 使用组合键进行分组：部门-领域-团队-团队类型-技能/特性分类
            key = (
                item.department or '',
                item.domain,
                item.team,
                team_type,
                item.skill_category or ''
            )
            
            if key not in pivot_data:
                pivot_data[key] = {
                    'department': item.department or '',
                    'domain': item.domain,
                    'team': item.team,
                    'team_type': team_type,
                    'skill_category': item.skill_category or '',
                    'year_months': {}  # 存储各个月份的聚合值（求和）
                }
            
            # 聚合该年月的需求人力占比（同一分组下不同人员的值求和）
            year_month = item.year_month
            year_months.add(year_month)
            current_value = float(item.demand_human_power_ratio) if item.demand_human_power_ratio else 1.00
            if year_month in pivot_data[key]['year_months']:
                # 如果该年月已有值，则累加
                pivot_data[key]['year_months'][year_month] += current_value
            else:
                # 如果该年月还没有值，则直接赋值
                pivot_data[key]['year_months'][year_month] = current_value

        # 将年月排序
        sorted_year_months = sorted(list(year_months))

        # 转换为列表格式，每个年月作为单独的字段
        result_list = []
        for key, data in pivot_data.items():
            row = {
                'department': data['department'],
                'domain': data['domain'],
                'team': data['team'],
                'team_type': data['team_type'],
                'skill_category': data['skill_category']
            }
            # 添加各个月份的列（聚合后的值）
            for ym in sorted_year_months:
                value = data['year_months'].get(ym, None)
                # 保留2位小数
                if value is not None:
                    row[ym] = round(value, 2)
                else:
                    row[ym] = None
            result_list.append(row)

        logger.info(f"查询人力透视表成功 - 共 {len(result_list)} 条记录，{len(sorted_year_months)} 个月份列")
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "查询成功",
            "data": result_list,
            "year_months": sorted_year_months  # 返回年月列表，用于前端动态生成列
        })
    except Exception as e:
        logger.error(f"查询人力透视表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"查询失败: {str(e)}", "data": [], "year_months": []})


def getHumanResourcePivotOptions():
    """
    获取人力透视表的筛选选项
    ---
    tags:
      - 人力透视表
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

        logger.info(f"获取人力透视表选项 - option_type: {option_type}")

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
        logger.error(f"获取人力透视表选项失败 - option_type: {option_type}, 错误: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"获取失败: {str(e)}", "data": []})
