from datetime import datetime, date
from typing import Any, Dict, List, Optional
import uuid

from flask import jsonify, request
from sqlalchemy import and_, func, or_, distinct
from sqlalchemy.exc import SQLAlchemyError

from electric_knowledge.data_model import db
from issueImpacte.data_model import IssueImpactCaseTable
from issueImpacte.version_data_model import IssueImpactVersionTable, IssueImpactVersionCaseRelationTable


def _safe_parse_date(value: Optional[str]) -> Optional[date]:
    """解析前端传入的日期字符串（仅日期，不包含时间）."""
    if not value:
        return None
    if isinstance(value, str):
        value = value.strip()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _generate_version_id() -> str:
    """生成版本ID"""
    return f"VERSION_{uuid.uuid4().hex[:16].upper()}"


def _match_boards(version_boards: str, case_board: str) -> bool:
    """
    匹配单板逻辑：
    - 如果版本涉及单板是 "BoardA,BoardB" 且案例单板是 "BoardA"，匹配
    - 如果版本涉及单板是 "BoardA" 且案例单板是 "BoardA,BoardB"，匹配
    - 如果版本涉及单板是 "BoardA,BoardB" 且案例单板是 "BoardA,BoardC"，匹配（交集）
    """
    if not version_boards or not case_board:
        return False
    
    version_board_list = [b.strip() for b in version_boards.split(',') if b.strip()]
    case_board_list = [b.strip() for b in case_board.split(',') if b.strip()]
    
    # 检查是否有交集
    return bool(set(version_board_list) & set(case_board_list))


def _calculate_version_case_relations(version: IssueImpactVersionTable):
    """
    计算版本与案例的关联关系
    匹配条件：
    1. 案例发生时间 > 历史版本发布时间（仅比较日期）
    2. 目标网络匹配（如果版本目标网络包含案例发现局点）
    3. 涉及单板匹配（交集匹配）
    """
    try:
        # 获取版本筛选条件
        historical_release_time = version.historical_release_time
        target_networks = [n.strip() for n in version.target_network.split(',')] if version.target_network else []
        involved_boards = version.involved_boards
        
        # 查询所有案例
        all_cases = IssueImpactCaseTable.query.filter(
            IssueImpactCaseTable.case_occur_time.isnot(None)
        ).all()
        
        matched_case_ids = []
        
        for case in all_cases:
            # 条件1：案例发生时间 > 历史版本发布时间（仅比较日期）
            if not case.case_occur_time:
                continue
            
            case_occur_date = case.case_occur_time.date()
            if case_occur_date <= historical_release_time:
                continue
            
            # 条件2：目标网络匹配
            if target_networks and case.case_found_site:
                if case.case_found_site not in target_networks:
                    continue
            
            # 条件3：涉及单板匹配
            if involved_boards and case.part:
                if not _match_boards(involved_boards, case.part):
                    continue
            
            matched_case_ids.append(case.case_id)
        
        # 删除旧的关联关系
        IssueImpactVersionCaseRelationTable.query.filter(
            IssueImpactVersionCaseRelationTable.version_id == version.version_id
        ).delete()
        
        # 创建新的关联关系
        for case_id in matched_case_ids:
            if case_id:  # 确保case_id不为空
                relation = IssueImpactVersionCaseRelationTable(
                    version_id=version.version_id,
                    case_id=case_id
                )
                db.session.add(relation)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def query_version_list():
    """查询版本列表，支持条件过滤与分页"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json() or {}
        user = data.get('user', 'guest')
        page = data.get('page', 1)
        page_size = data.get('pageSize', 20)
        sort_by = data.get('sortBy', 'release_time')
        descending = data.get('descending', True)
        conditions = data.get('conditions', {})
        
        # 构建查询
        query = IssueImpactVersionTable.query
        
        # 应用筛选条件
        if conditions.get('versionName'):
            query = query.filter(
                IssueImpactVersionTable.version_name.like(f"%{conditions['versionName']}%")
            )
        
        if conditions.get('releaseTime'):
            release_time = _safe_parse_date(conditions['releaseTime'])
            if release_time:
                query = query.filter(
                    func.date(IssueImpactVersionTable.release_time) == release_time
                )
        
        if conditions.get('belongProject'):
            query = query.filter(
                IssueImpactVersionTable.belong_project == conditions['belongProject']
            )
        
        if conditions.get('targetNetwork'):
            target_networks = [n.strip() for n in conditions['targetNetwork'].split(',') if n.strip()]
            if target_networks:
                filters = []
                for network in target_networks:
                    filters.append(IssueImpactVersionTable.target_network.like(f"%{network}%"))
                query = query.filter(or_(*filters))
        
        if conditions.get('boards'):
            boards = [b.strip() for b in conditions['boards'].split(',') if b.strip()]
            if boards:
                filters = []
                for board in boards:
                    filters.append(IssueImpactVersionTable.involved_boards.like(f"%{board}%"))
                query = query.filter(or_(*filters))
        
        if conditions.get('branch'):
            query = query.filter(
                IssueImpactVersionTable.branch == conditions['branch']
            )
        
        # 排序
        if hasattr(IssueImpactVersionTable, sort_by):
            order_column = getattr(IssueImpactVersionTable, sort_by)
            if descending:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        versions = query.offset(offset).limit(page_size).all()
        
        # 获取每个版本关联的案例数量
        result_list = []
        for version in versions:
            version_dict = version.to_dict()
            case_count = IssueImpactVersionCaseRelationTable.query.filter(
                IssueImpactVersionCaseRelationTable.version_id == version.version_id
            ).count()
            version_dict['caseCount'] = case_count
            result_list.append(version_dict)
        
        return jsonify({
            'status': 'success',
            'data': result_list,
            'total': total,
            'page': page,
            'pageSize': page_size
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def create_version():
    """创建版本"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json() or {}
        user = data.get('user', 'guest')
        conditions = data.get('conditions', {})
        
        # 验证必填字段
        if not conditions.get('versionName'):
            return jsonify({
                'status': 'error',
                'message': '版本名称不能为空'
            }), 400
        
        if not conditions.get('historicalReleaseTime'):
            return jsonify({
                'status': 'error',
                'message': '历史版本发布时间不能为空'
            }), 400
        
        if not conditions.get('branch'):
            return jsonify({
                'status': 'error',
                'message': '版本分支不能为空'
            }), 400
        
        # 检查版本名称是否已存在
        existing = IssueImpactVersionTable.query.filter(
            IssueImpactVersionTable.version_name == conditions['versionName']
        ).first()
        if existing:
            return jsonify({
                'status': 'error',
                'message': '版本名称已存在'
            }), 400
        
        # 创建版本
        version = IssueImpactVersionTable(
            version_id=_generate_version_id(),
            version_name=conditions['versionName'],
            belong_project=conditions.get('belongProject'),
            release_time=_safe_parse_date(conditions.get('releaseTime')),
            historical_release_time=_safe_parse_date(conditions['historicalReleaseTime']),
            target_network=conditions.get('targetNetwork', ''),
            involved_boards=conditions.get('involvedBoards', ''),
            branch=conditions['branch'],
            create_by=user,
            update_by=user
        )
        
        db.session.add(version)
        db.session.flush()  # 获取version_id
        
        # 计算并创建关联关系
        _calculate_version_case_relations(version)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '创建成功',
            'data': version.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'创建失败: {str(e)}'
        }), 500


def update_version():
    """更新版本"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json() or {}
        user = data.get('user', 'guest')
        conditions = data.get('conditions', {})
        version_id = conditions.get('versionId')
        
        if not version_id:
            return jsonify({
                'status': 'error',
                'message': '版本ID不能为空'
            }), 400
        
        # 查找版本
        version = IssueImpactVersionTable.query.filter(
            IssueImpactVersionTable.version_id == version_id
        ).first()
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': '版本不存在'
            }), 404
        
        # 如果版本名称改变，检查是否重复
        new_version_name = conditions.get('versionName')
        if new_version_name and new_version_name != version.version_name:
            existing = IssueImpactVersionTable.query.filter(
                IssueImpactVersionTable.version_name == new_version_name,
                IssueImpactVersionTable.version_id != version_id
            ).first()
            if existing:
                return jsonify({
                    'status': 'error',
                    'message': '版本名称已存在'
                }), 400
        
        # 更新字段
        if 'versionName' in conditions:
            version.version_name = conditions['versionName']
        if 'belongProject' in conditions:
            version.belong_project = conditions.get('belongProject')
        if 'releaseTime' in conditions:
            version.release_time = _safe_parse_date(conditions.get('releaseTime'))
        if 'historicalReleaseTime' in conditions:
            version.historical_release_time = _safe_parse_date(conditions['historicalReleaseTime'])
        if 'targetNetwork' in conditions:
            version.target_network = conditions.get('targetNetwork', '')
        if 'involvedBoards' in conditions:
            version.involved_boards = conditions.get('involvedBoards', '')
        if 'branch' in conditions:
            version.branch = conditions['branch']
        
        version.update_by = user
        
        db.session.flush()
        
        # 重新计算关联关系
        _calculate_version_case_relations(version)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '更新成功',
            'data': version.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'更新失败: {str(e)}'
        }), 500


def delete_version():
    """删除版本（仅删除版本记录，保留关联关系和案例数据）"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json() or {}
        conditions = data.get('conditions', {})
        version_id = conditions.get('versionId')
        
        if not version_id:
            return jsonify({
                'status': 'error',
                'message': '版本ID不能为空'
            }), 400
        
        # 查找版本
        version = IssueImpactVersionTable.query.filter(
            IssueImpactVersionTable.version_id == version_id
        ).first()
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': '版本不存在'
            }), 404
        
        # 删除版本（关联关系保留）
        db.session.delete(version)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '删除成功'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除失败: {str(e)}'
        }), 500


def get_version_detail(version_id: str):
    """获取版本详情"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        version = IssueImpactVersionTable.query.filter(
            IssueImpactVersionTable.version_id == version_id
        ).first()
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': '版本不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': version.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def query_version_cases(version_id: str):
    """查询版本关联的案例列表"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json() or {}
        page = data.get('page', 1)
        page_size = data.get('pageSize', 20)
        sort_by = data.get('sortBy', 'case_occur_time')
        descending = data.get('descending', True)
        conditions = data.get('conditions', {})
        
        # 获取版本关联的案例ID列表
        relations = IssueImpactVersionCaseRelationTable.query.filter(
            IssueImpactVersionCaseRelationTable.version_id == version_id
        ).all()
        
        case_ids = [r.case_id for r in relations]
        
        if not case_ids:
            return jsonify({
                'status': 'success',
                'data': [],
                'total': 0,
                'page': page,
                'pageSize': page_size
            }), 200
        
        # 构建查询
        query = IssueImpactCaseTable.query.filter(
            IssueImpactCaseTable.case_id.in_(case_ids)
        )
        
        # 应用筛选条件（与案例列表查询相同的条件）
        if conditions.get('caseId'):
            query = query.filter(
                IssueImpactCaseTable.case_id.like(f"%{conditions['caseId']}%")
            )
        
        if conditions.get('caseTitle'):
            query = query.filter(
                IssueImpactCaseTable.case_title.like(f"%{conditions['caseTitle']}%")
            )
        
        if conditions.get('belongProject'):
            query = query.filter(
                IssueImpactCaseTable.belong_project == conditions['belongProject']
            )
        
        if conditions.get('caseFoundSite'):
            query = query.filter(
                IssueImpactCaseTable.case_found_site.like(f"%{conditions['caseFoundSite']}%")
            )
        
        if conditions.get('priority'):
            query = query.filter(
                IssueImpactCaseTable.priority == conditions['priority']
            )
        
        if conditions.get('qualityTopic'):
            query = query.filter(
                IssueImpactCaseTable.quality_topic.like(f"%{conditions['qualityTopic']}%")
            )
        
        if conditions.get('functionCategory'):
            query = query.filter(
                IssueImpactCaseTable.function_category.like(f"%{conditions['functionCategory']}%")
            )
        
        if conditions.get('component'):
            query = query.filter(
                IssueImpactCaseTable.part.like(f"%{conditions['component']}%")
            )
        
        # 排序
        if hasattr(IssueImpactCaseTable, sort_by):
            order_column = getattr(IssueImpactCaseTable, sort_by)
            if descending:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        cases = query.offset(offset).limit(page_size).all()
        
        result_list = [case.to_dict() for case in cases]
        
        return jsonify({
            'status': 'success',
            'data': result_list,
            'total': total,
            'page': page,
            'pageSize': page_size
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def get_target_network_options():
    """获取目标网络选项（从案例发现局点提取）"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        # 查询所有不重复的案例发现局点
        sites = db.session.query(
            distinct(IssueImpactCaseTable.case_found_site)
        ).filter(
            IssueImpactCaseTable.case_found_site.isnot(None),
            IssueImpactCaseTable.case_found_site != ''
        ).all()
        
        options = [site[0] for site in sites if site[0]]
        options.sort()
        
        return jsonify({
            'status': 'success',
            'data': options
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def get_board_options():
    """获取涉及单板选项（从案例单板提取）"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        # 查询所有不重复的单板
        boards = db.session.query(
            distinct(IssueImpactCaseTable.part)
        ).filter(
            IssueImpactCaseTable.part.isnot(None),
            IssueImpactCaseTable.part != ''
        ).all()
        
        # 处理逗号分隔的单板
        all_boards = set()
        for board in boards:
            if board[0]:
                board_list = [b.strip() for b in board[0].split(',') if b.strip()]
                all_boards.update(board_list)
        
        options = sorted(list(all_boards))
        
        return jsonify({
            'status': 'success',
            'data': options
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def get_branch_options():
    """获取版本分支选项（从历史版本分支提取）"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        # 查询所有不重复的版本分支
        branches = db.session.query(
            distinct(IssueImpactVersionTable.branch)
        ).filter(
            IssueImpactVersionTable.branch.isnot(None),
            IssueImpactVersionTable.branch != ''
        ).all()
        
        options = [branch[0] for branch in branches if branch[0]]
        options.sort()
        
        return jsonify({
            'status': 'success',
            'data': options
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def get_belong_project_options():
    """获取归属项目选项（从案例库提取）"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        # 查询所有不重复的归属项目
        projects = db.session.query(
            distinct(IssueImpactCaseTable.belong_project)
        ).filter(
            IssueImpactCaseTable.belong_project.isnot(None),
            IssueImpactCaseTable.belong_project != ''
        ).all()
        
        options = [project[0] for project in projects if project[0]]
        options.sort()
        
        return jsonify({
            'status': 'success',
            'data': options
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询失败: {str(e)}'
        }), 500


def recalculate_all_version_relations():
    """
    重新计算所有版本的关联关系
    当案例数据更新时调用此函数
    """
    try:
        versions = IssueImpactVersionTable.query.all()
        for version in versions:
            _calculate_version_case_relations(version)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def delete_case_relations(case_id: str):
    """
    删除案例的所有关联关系
    当案例被删除时调用此函数
    """
    try:
        IssueImpactVersionCaseRelationTable.query.filter(
            IssueImpactVersionCaseRelationTable.case_id == case_id
        ).delete()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e
