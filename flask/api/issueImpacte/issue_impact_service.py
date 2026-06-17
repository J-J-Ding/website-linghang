from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from flask import jsonify, request
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError

from electric_knowledge.data_model import db
from issueImpacte.data_model import IssueImpactCaseTable
from issueImpacte.version_service import recalculate_all_version_relations, delete_case_relations


def _safe_parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """解析前端传入的日期字符串."""
    if not value:
        return None
    candidate = value.replace('Z', '+00:00') if isinstance(value, str) else value
    for fmt in (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d',
    ):
        try:
            return datetime.strptime(candidate, fmt)
        except (ValueError, TypeError):
            continue
    try:
        return datetime.fromisoformat(candidate)
    except (ValueError, TypeError):
        return None


def _assign_model_fields(model: IssueImpactCaseTable, data: Dict[str, Any]) -> IssueImpactCaseTable:
    """将字典字段写入 SQLAlchemy 模型，并转换特殊字段."""
    # 字段映射：前端字段名 -> 数据库字段名
    field_map = {
        'caseId': 'case_id',
        'caseTitle': 'case_title',
        'belongProject': 'belong_project',
        'caseFoundSite': 'case_found_site',
        'priority': 'priority',
        'qualityTopic': 'quality_topic',
        'functionCategory': 'function_category',
        'component': 'component',
        'part': 'part',
        'status': 'status',
        'workItemId': 'work_item_id',
        'workItemType': 'work_item_type',
        'workItemTitle': 'work_item_title',
        'caseTriggerSite': 'case_trigger_site',
        'affectBusiness': 'affect_business',
        'modifyFaultRecord': 'modify_fault_record',
        'faultCode': 'fault_code',
        'modifiedCode': 'modified_code',
        'introduceFaultRecord': 'introduce_fault_record',
        'needHorizontalPush': 'need_horizontal_push',
        'needNotice': 'need_notice',
        'horizontalPushTicket': 'horizontal_push_ticket',
        'rdcNoticeTicket': 'rdc_notice_ticket',
        'rdcReviewTicket': 'rdc_review_ticket',
        'createBy': 'create_by',
        'updateBy': 'update_by',
        'assignTo': 'assign_to',
    }

    datetime_fields = {
        'caseOccurTime': 'case_occur_time',
    }

    for payload_key, model_key in field_map.items():
        if payload_key in data:
            value = data.get(payload_key)
            # 对于有唯一约束的字段（如 work_item_id），空字符串应转换为 None
            # 避免多个空字符串违反唯一约束
            if model_key == 'work_item_id':
                # 如果值为空字符串或 None，设置为 None（数据库中的 NULL）
                if not value or (isinstance(value, str) and not value.strip()):
                    value = None
            else:
                # 对于其他字符串字段，将 None 转换为空字符串
                if value is None:
                    value = ""
            # 确保值被正确设置
            setattr(model, model_key, value)

    for payload_key, model_key in datetime_fields.items():
        if payload_key in data:
            setattr(model, model_key, _safe_parse_datetime(data.get(payload_key)))
    
    return model


def query_issue_impact_case_list():
    """
    查询案例单列表，支持条件过滤与分页。
    默认仅返回非关闭/删除状态的数据。
    """
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    payload = request.json or {}
    page = max(int(payload.get('page', 1)), 1)
    page_size = max(int(payload.get('pageSize', 20)), 1)
    only_open = payload.get('onlyOpen', True)
    
    # 获取查询条件（支持 conditions 对象或直接字段）
    conditions = payload.get('conditions', {})
    if not conditions and payload:
        # 如果没有 conditions，尝试从 payload 中提取查询条件
        conditions = {
            k: v for k, v in payload.items() 
            if k not in ['page', 'pageSize', 'onlyOpen', 'table_name', 'user']
        }

    query = db.session.query(IssueImpactCaseTable)
    filters = []

    # 默认只显示未关闭的案例
    if only_open:
        filters.append(IssueImpactCaseTable.status.notin_(['已关闭', '已删除']))

    # 应用查询条件
    if conditions:
        if case_id := conditions.get('caseId'):
            filters.append(IssueImpactCaseTable.case_id.ilike(f'%{case_id}%'))
        
        if case_title := conditions.get('caseTitle'):
            filters.append(IssueImpactCaseTable.case_title.ilike(f'%{case_title}%'))
        
        if belong_project := conditions.get('belongProject'):
            filters.append(IssueImpactCaseTable.belong_project.ilike(f'%{belong_project}%'))
        
        if case_found_site := conditions.get('caseFoundSite'):
            filters.append(IssueImpactCaseTable.case_found_site.ilike(f'%{case_found_site}%'))
        
        if priority := conditions.get('priority'):
            filters.append(IssueImpactCaseTable.priority == priority)
        
        if quality_topic := conditions.get('qualityTopic'):
            filters.append(IssueImpactCaseTable.quality_topic.ilike(f'%{quality_topic}%'))
        
        if function_category := conditions.get('functionCategory'):
            filters.append(IssueImpactCaseTable.function_category.ilike(f'%{function_category}%'))
        
        if component := conditions.get('component'):
            filters.append(IssueImpactCaseTable.component.ilike(f'%{component}%'))
        
        if part := conditions.get('part'):
            filters.append(IssueImpactCaseTable.part.ilike(f'%{part}%'))
        
        if assign_to := conditions.get('assignTo'):
            filters.append(IssueImpactCaseTable.assign_to.ilike(f'%{assign_to}%'))
        
        # 支持状态数组查询
        if status_list := conditions.get('status'):
            if isinstance(status_list, list):
                filters.append(IssueImpactCaseTable.status.in_(status_list))
            else:
                filters.append(IssueImpactCaseTable.status == status_list)

    query = query.filter(and_(*filters)) if filters else query
    total = query.count()
    # rows = (
    #     query.order_by(IssueImpactCaseTable.update_time.desc())
    #     .offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .all()
    # )
    rows = (
        query.order_by(IssueImpactCaseTable.update_time.desc()).all()
    )

    return jsonify(
        {
            "status": "success",
            "message": "获取成功",
            "data": [item.to_dict() for item in rows],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )


def create_issue_impact_case():
    """
    新建案例单，如果提供了工作项ID则按照工作项ID去重。
    工作项ID为可选项，如果提供则会进行去重检查，确保同一工作项不重复创建案例单。
    """
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    payload = request.json or {}
    conditions = payload.get('conditions', {})
    
    # 从 conditions 或 payload 中获取工作项ID（可选字段）
    work_item_id = conditions.get('workItemId') or payload.get('workItemId')
    
    # 如果提供了工作项ID，检查是否已存在相同工作项ID的案例（去重检查）
    if work_item_id and isinstance(work_item_id, str) and work_item_id.strip():
        existed = (
            db.session.query(IssueImpactCaseTable)
            .filter(IssueImpactCaseTable.work_item_id == work_item_id)
            .first()
        )
        if existed:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "该工作项已经生成案例单，请直接编辑",
                        "data": existed.to_dict(),
                    }
                ),
                409,
            )

    model = IssueImpactCaseTable()
    
    # 合并 conditions 和 payload 的数据
    data = {**conditions, **{k: v for k, v in payload.items() if k != 'conditions'}}
    
    _assign_model_fields(model, data)
    
    # 设置默认值
    if not model.status:
        model.status = '新建'
    
    if not model.case_id:
        model.case_id = _next_case_id()
    
    # 根据工作项类型设置默认优先级
    if not model.priority and model.work_item_type == '外场故障':
        model.priority = '高'
    
    # 设置创建人
    user = payload.get('user') or conditions.get('user')
    if user:
        model.create_by = user
        model.update_by = user

    try:
        db.session.add(model)
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "message": "创建成功",
                "data": model.to_dict(),
            }
        )
    except SQLAlchemyError as exc:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": f"创建失败：{exc}",
                }
            ),
            500,
        )


def update_issue_impact_case():
    """更新案例单信息."""
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    payload = request.json or {}
    conditions = payload.get('conditions', {})
    
    # 从 conditions 或 payload 中获取案例ID
    case_id = conditions.get('caseId') or payload.get('caseId')
    if not case_id:
        return jsonify({"status": "fail", "message": "缺少案例ID"}), 400

    model = db.session.query(IssueImpactCaseTable).filter(
        IssueImpactCaseTable.case_id == case_id
    ).first()
    if not model:
        return jsonify({"status": "fail", "message": "案例单不存在"}), 404

    # 合并 conditions 和 payload 的数据
    data = {**conditions, **{k: v for k, v in payload.items() if k not in ['conditions', 'caseId']}}
    _assign_model_fields(model, data)
    
    # 设置更新人
    user = payload.get('user') or conditions.get('user')
    if user:
        model.update_by = user

    try:
        db.session.commit()
        
        # 案例数据更新后，重新计算所有版本的关联关系
        try:
            recalculate_all_version_relations()
        except Exception as e:
            # 关联关系更新失败不影响案例更新，只记录日志
            print(f"警告：更新版本关联关系失败: {str(e)}")
        
        return jsonify(
            {
                "status": "success",
                "message": "更新成功",
                "data": model.to_dict(),
            }
        )
    except SQLAlchemyError as exc:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": f"更新失败：{exc}",
                }
            ),
            500,
        )


def delete_issue_impact_case():
    """
    删除案例单，按要求只做状态更新。
    根据详设：删除后案例状态置为"已删除"
    """
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    payload = request.json or {}
    conditions = payload.get('conditions', {})
    
    # 从 conditions 或 payload 中获取案例ID
    case_id = conditions.get('caseId') or payload.get('caseId')
    if not case_id:
        return jsonify({"status": "fail", "message": "缺少案例ID"}), 400

    model = db.session.query(IssueImpactCaseTable).filter(
        IssueImpactCaseTable.case_id == case_id
    ).first()
    if not model:
        return jsonify({"status": "fail", "message": "案例单不存在"}), 404

    model.status = '已删除'
    
    # 设置更新人
    user = payload.get('user') or conditions.get('user')
    if user:
        model.update_by = user

    try:
        db.session.commit()
        
        # 删除案例后，自动删除关联关系表中的记录
        try:
            delete_case_relations(case_id)
        except Exception as e:
            # 关联关系删除失败不影响案例删除，只记录日志
            print(f"警告：删除版本关联关系失败: {str(e)}")
        
        return jsonify(
            {
                "status": "success",
                "message": "删除成功（案例状态已置为已删除）",
                "data": model.to_dict(),
            }
        )
    except SQLAlchemyError as exc:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": f"删除失败：{exc}",
                }
            ),
            500,
        )


def import_issue_impact_case_batch():
    """批量导入案例单（excel)."""
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    file = request.files.get('file')
    if not file:
        return jsonify({"status": "fail", "message": "未接收到文件"}), 400

    try:
        df = pd.read_excel(file)
    except Exception as exc:
        return (
            jsonify({"status": "fail", "message": f"文件解析失败：{exc}"}),
            400,
        )

    inserted = 0
    skipped = 0
    errors = []
    
    for idx, row in df.iterrows():
        work_item_id = str(row.get('工作项ID') or '').strip()
        if not work_item_id:
            skipped += 1
            continue
        
        # 检查是否已存在
        existed = (
            db.session.query(IssueImpactCaseTable)
            .filter(IssueImpactCaseTable.work_item_id == work_item_id)
            .first()
        )
        if existed:
            skipped += 1
            continue
        
        try:
            model = IssueImpactCaseTable()
            row_dict = {
                'caseId': str(row.get('案例ID', '')).strip() or _next_case_id(),
                'workItemType': str(row.get('工作项类型', '')).strip(),
                'workItemId': work_item_id,
                'workItemTitle': str(row.get('工作项标题', '')).strip(),
                'caseTitle': str(row.get('案例标题', '')).strip(),
                'status': str(row.get('状态', '')).strip() or '新建',
                'belongProject': str(row.get('归属项目', '')).strip(),
                'caseFoundSite': str(row.get('案例发现局点', '')).strip(),
                'priority': str(row.get('优先级', '')).strip(),
                'qualityTopic': str(row.get('关联质量专题', '')).strip(),
                'functionCategory': str(row.get('功能分类', '')).strip(),
                'component': str(row.get('组件', '')).strip(),
                'part': str(row.get('部件', '')).strip(),
                'affectBusiness': str(row.get('是否影响业务', '')).strip(),
                'modifyFaultRecord': str(row.get('修改故障入库记录', '')).strip(),
                'faultCode': str(row.get('故障代码', '')).strip(),
                'modifiedCode': str(row.get('修改后代码', '')).strip(),
                'introduceFaultRecord': str(row.get('引入故障入库记录', '')).strip(),
                'caseOccurTime': str(row.get('案例发生时间', '')).strip(),
                'assignTo': str(row.get('指派给', '')).strip(),
            }
            _assign_model_fields(model, row_dict)
            db.session.add(model)
            inserted += 1
        except Exception as e:
            errors.append(f"第{idx+2}行导入失败: {str(e)}")
            skipped += 1

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return (
            jsonify({"status": "fail", "message": f"导入失败：{exc}"}),
            500,
        )

    message = f"导入完成：成功 {inserted} 条, 跳过 {skipped} 条"
    if errors:
        message += f"，错误：{'; '.join(errors[:5])}"  # 只显示前5个错误

    return jsonify(
        {
            "status": "success",
            "message": message,
            "data": {"inserted": inserted, "skipped": skipped, "errors": errors},
        }
    )


def confirm_case_source():
    """
    确认案例源：根据工作项ID智能回填基础信息。
    根据详设：添加工作项关键信息后，点击"确认案例源"，自动载入案例源相关信息
    """
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    payload = request.json or {}
    work_item_id = payload.get('workItemId') or payload.get('work_item_id')
    
    if not work_item_id:
        return jsonify({"status": "fail", "message": "缺少工作项ID"}), 400

    # 检查是否已存在相同工作项ID的案例
    existed = (
        db.session.query(IssueImpactCaseTable)
        .filter(IssueImpactCaseTable.work_item_id == work_item_id)
        .first()
    )
    if existed:
        return jsonify(
            {
                "status": "success",
                "message": "该工作项已存在案例单，返回现有数据",
                "data": existed.to_dict(),
            }
        )

    # TODO: 这里应该调用 RDC API 获取工作项信息
    # 目前返回默认推荐信息
    work_item_type = payload.get('workItemType', '内场故障')
    default_priority = '高' if work_item_type == '外场故障' else '中'
    
    recommendation = {
        "caseId": _next_case_id(),
        "workItemId": work_item_id,
        "workItemType": work_item_type,
        "priority": default_priority,
        "status": '新建',
        "belongProject": payload.get('belongProject', ''),
        "caseTriggerSite": payload.get('caseTriggerSite', ''),
        "affectBusiness": payload.get('affectBusiness', '否'),
        "functionCategory": payload.get('functionCategory', ''),
        "component": payload.get('component', ''),
        "part": payload.get('part', ''),
    }

    return jsonify(
        {
            "status": "success",
            "message": "已根据工作项生成推荐信息（需要调用RDC API获取完整信息）",
            "data": recommendation,
        }
    )


def _next_case_id() -> str:
    """生成下一个案例ID."""
    max_case = db.session.query(IssueImpactCaseTable).order_by(
        IssueImpactCaseTable.id.desc()
    ).first()
    
    if max_case and max_case.case_id:
        # 尝试从现有 case_id 中提取数字
        try:
            # 假设 case_id 格式为 CASE_数字 或纯数字
            if max_case.case_id.startswith('CASE_'):
                num = int(max_case.case_id.split('_')[1])
                return f'CASE_{num + 1}'
            else:
                num = int(max_case.case_id)
                return f'CASE_{num + 1}'
        except:
            pass
    
    # 如果没有现有记录，从 id 生成
    max_id = db.session.query(func.max(IssueImpactCaseTable.id)).scalar()
    return f'CASE_{(max_id or 0) + 1}'

