from sqlalchemy import and_, or_, distinct, func
from requirement_schedule.data_model import (
    db, REQUIREMENT_SCHEDULE_TABLE, PERSON_SKILL_MAP,
    REQUIREMENT_DEV_HUMAN_RESOURCE, TEAM_MAPPING,
    DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE
)
from flask import request, jsonify
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

logger = logging.getLogger("Logger")

# ----------------------------------------------------------------
# 常量配置
# ----------------------------------------------------------------
# 每月工作天数（用于将"人天"换算为"人力"人月单位）
WORKING_DAYS_PER_MONTH = 20

# 所属产品固定枚举值（与需求清单页面保持一致，label 即 value，与数据库存储值相同）
BELONG_PRODUCT_OPTIONS = ['ZXONE 19700', 'ZXONE 9700', 'ZXMP M721', 'ZXONE 7000', 'ZXONE NTON']

# 所属产品显示名 → requirement_dev_human_resource 中对应字段名映射
# ZXONE 7000 暂无对应产品人力占比字段，不在此映射中
PRODUCT_COLUMN_MAP = {
    'ZXONE 19700': 'zxone_19700',
    'ZXONE 9700': 'zxone_9700',
    'ZXMP M721': 'zxmp_m721',
    'ZXONE NTON': 'zxone_nton',
}

# 主交付 PR 工作项类型（兼容历史英文值和当前中文值）
# 线上实际常见为“产品需求”，若仅过滤 PR 会导致已用人力1被错误算成0。
PR_WORK_ITEM_TYPES = ['PR', '产品需求']

# 用户故事工作项类型
US_WORK_ITEM_TYPE = '用户故事'

# 非本团队主交付 PR 引入来源值
NON_TEAM_PR_SOURCE = '非本团队主交付PR'


def _gen_month_list(start_month: str, end_month: str) -> list:
    """生成 start_month ~ end_month 之间（含）的所有年月列表，格式 YYYY-MM"""
    result = []
    try:
        cur = datetime.strptime(start_month, '%Y-%m')
        end = datetime.strptime(end_month, '%Y-%m')
        while cur <= end:
            result.append(cur.strftime('%Y-%m'))
            cur += relativedelta(months=1)
    except Exception:
        pass
    return result


def queryAvailableHumanResourceByParams():
    """
    查询可用人力聚合数据
    ---
    tags:
      - 可用人力
    description: |
      按 (部门，领域，团队，团队类型，技能/特性分类) 分组，
      从 domain_team_available_human_resource 表直接读取总人力、中兴人力、外包人力、
      需求交付可用人力、已用人力 1/2、已用人力、剩余可用人力。
      支持起止月份范围查询（start_month / end_month），按月份聚合数据。
    parameters:
      - name: start_month
        in: query
        type: string
        required: true
        description: 起始年月（格式 YYYY-MM，如 2026-01）
      - name: end_month
        in: query
        type: string
        required: true
        description: 截止年月（格式 YYYY-MM，如 2026-03）
      - name: department
        in: query
        type: string
        required: false
        description: 部门
      - name: domain
        in: query
        type: array
        collectionFormat: multi
        required: false
        description: 领域（支持多选）
      - name: team
        in: query
        type: array
        collectionFormat: multi
        required: false
        description: 团队（支持多选）
      - name: skill_category
        in: query
        type: string
        required: false
        description: 技能/特性分类（模糊匹配）
    responses:
      200:
        description: 查询成功
    """
    try:
        start_month = request.args.get('start_month', '').strip()
        end_month = request.args.get('end_month', '').strip()
        department = request.args.get('department', '').strip()
        domain_param = [d.strip() for d in request.args.getlist('domain') if d and d.strip()]
        team_param = [t.strip() for t in request.args.getlist('team') if t and t.strip()]
        skill_category = request.args.get('skill_category', '').strip()

        # 兼容旧参数 year_month（若未传 start_month/end_month）
        year_month_compat = request.args.get('year_month', '').strip()
        if not start_month and year_month_compat:
            start_month = year_month_compat
        if not end_month and year_month_compat:
            end_month = year_month_compat

        if not start_month or not end_month:
            return jsonify({"code": 400, "status": "error",
                            "message": "start_month 和 end_month 参数不能为空", "data": []})

        # 校验格式
        month_pattern = re.compile(r'^\d{4}-\d{2}$')
        if not month_pattern.match(start_month) or not month_pattern.match(end_month):
            return jsonify({"code": 400, "status": "error",
                            "message": "月份格式不正确，请使用 YYYY-MM 格式", "data": []})

        if start_month > end_month:
            return jsonify({"code": 400, "status": "error",
                            "message": "起始月份不能大于截止月份", "data": []})

        # 生成范围内所有月份
        month_list = _gen_month_list(start_month, end_month)

        # ===============================================================
        # 从 domain_team_available_human_resource 表查询并聚合数据
        # 按 (department, domain, team, team_type, skill_category) 分组
        # 对月份范围进行 SUM 聚合
        # ===============================================================
        query_cond = []
        
        # 月份范围筛选
        if month_list:
            query_cond.append(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.date.in_(month_list))
        
        # 其他筛选条件
        if department:
            query_cond.append(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department == department)
        if domain_param:
            query_cond.append(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain.in_(domain_param))
        if team_param:
            query_cond.append(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team.in_(team_param))
        if skill_category:
            # 技能/特性分类为可选字段：匹配筛选值，或技能分类为空/null 的记录也保留
            query_cond.append(
                or_(
                    DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category.like(f'%{skill_category}%'),
                    DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category == None,   # noqa: E711
                    DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category == ''
                )
            )

        # 分组聚合查询
        group_query = db.session.query(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team_type,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category,
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.total_human_resource).label('total_human_resource'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.zte_human_resource).label('zte_human_resource'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.outsourcing_human_resource).label('outsourcing_human_resource'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.demand_delivery_available).label('demand_delivery_available'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.remaining_available_human_resource).label('remaining_available_human_resource'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.used_human_resource).label('used_human_resource'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.used_human_resource1).label('used_human_resource1'),
            func.sum(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.used_human_resource2).label('used_human_resource2'),
        ).filter(
            and_(*query_cond)
        ).group_by(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team_type,
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category,
        ).all()

        if not group_query:
            return jsonify({"code": 200, "status": "success",
                            "message": "查询成功，无匹配数据", "data": []})

        # ===============================================================
        # 组装结果
        # ===============================================================
        result_list = []
        for row in group_query:
            result_list.append({
                'belong_product': '-',  # 该表无所属产品维度，置为 '-'
                'department': row.department or '',
                'domain': row.domain or '',
                'team': row.team or '',
                'team_type': row.team_type or '',
                'skill_category': row.skill_category or '',
                'total_human_power': float(row.total_human_resource) if row.total_human_resource else 0.00,
                'zte_human_power': float(row.zte_human_resource) if row.zte_human_resource else 0.00,
                'outsource_human_power': float(row.outsourcing_human_resource) if row.outsourcing_human_resource else 0.00,
                'demand_delivery_available_power': float(row.demand_delivery_available) if row.demand_delivery_available else 0.00,
                'remaining_available_power': float(row.remaining_available_human_resource) if row.remaining_available_human_resource else 0.00,
                'used_human_power': float(row.used_human_resource) if row.used_human_resource else 0.00,
                'used_human_power_1': float(row.used_human_resource1) if row.used_human_resource1 else 0.00,
                'used_human_power_2': float(row.used_human_resource2) if row.used_human_resource2 else 0.00,
            })

        # 排序：领域 → 团队 → 技能分类
        result_list.sort(key=lambda x: (x['domain'], x['team'], x['skill_category']))

        logger.info(
            f"查询可用人力成功 - start_month:{start_month}, end_month:{end_month}, "
            f"共 {len(result_list)} 条记录"
        )
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "查询成功",
            "data": result_list
        })

    except Exception as e:
        logger.error(f"查询可用人力失败：{str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error",
                        "message": f"查询失败：{str(e)}", "data": []})


def getAvailableHumanResourceOptions():
    """
    获取可用人力页面筛选条件选项
    ---
    tags:
      - 可用人力
    description: 返回部门、领域、团队、技能分类选项（均来自 domain_team_available_human_resource 表）
    responses:
      200:
        description: 获取成功
    """
    try:
        departments = db.session.query(
            distinct(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department)
        ).filter(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department != '',
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.department != None   # noqa: E711
        ).all()

        domains = db.session.query(
            distinct(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain)
        ).filter(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain != '',
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.domain != None   # noqa: E711
        ).all()

        teams = db.session.query(
            distinct(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team)
        ).filter(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team != '',
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.team != None   # noqa: E711
        ).all()

        skill_categories = db.session.query(
            distinct(DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category)
        ).filter(
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category != '',
            DOMAIN_TEAM_AVAILABLE_HUMAN_RESOURCE.skill_category != None   # noqa: E711
        ).all()

        return jsonify({
            "code": 200,
            "status": "success",
            "message": "获取成功",
            "data": {
                "department": sorted([d[0] for d in departments if d[0]]),
                "domain": sorted([d[0] for d in domains if d[0]]),
                "team": sorted([t[0] for t in teams if t[0]]),
                "skill_category": sorted([s[0] for s in skill_categories if s[0]]),
            }
        })

    except Exception as e:
        logger.error(f"获取可用人力选项失败：{str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error",
                        "message": f"获取失败：{str(e)}", "data": {}})
