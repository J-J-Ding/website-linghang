from sqlalchemy import and_
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from requirement_schedule.data_model import db, FEATURE_VIEW_TABLE, PERSON_SKILL_MAP
from flask import request, jsonify, send_file
import logging
import pandas as pd
import io
import re

logger = logging.getLogger("Logger")


class FeatureViewData(BaseModel):
    id: Optional[int] = None
    feature_first_classification: Optional[str] = None
    feature_second_classification: Optional[str] = None
    feature_name: Optional[str] = None
    sub_feature_name: Optional[str] = None
    feature_identifier: Optional[str] = None
    domain: Optional[str] = None
    team: Optional[str] = None
    verification_mode: Optional[str] = None
    verification_team: Optional[str] = None
    priority: Optional[str] = None
    dev_workload: Optional[float] = None
    detail_workload: Optional[float] = None
    estimated_dev_workload: Optional[float] = None
    estimated_verification_workload: Optional[float] = None
    estimated_system_test_workload: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


def _build_feature_tree(flat_data):
    """
    将平铺的特性视图数据组织成树形结构。
    规则：
    - sub_feature_name 为空的记录 → 父节点（特性级）
    - sub_feature_name 非空 且 feature_name 非空 → 挂到对应父节点的 childrenList
    - sub_feature_name 非空 且 feature_name 为空 → 孤立顶层节点
    父节点匹配 key = (feature_first_classification, feature_second_classification, feature_name)
    """
    # 与正例保持一致：
    # 1) 父节点：feature_name 非空且 sub_feature_name 为空
    # 2) 子节点：sub_feature_name 非空，且展示时父级字段置空
    # 3) 归属优先级：
    #    - 子行有 feature_name -> 直接挂该特性
    #    - 子行 feature_name 为空 -> 通过 feature_identifier(如 FS010121-01) 推导父特性编码 F010121 匹配
    #    - 若仍无法定位且同分类只有一个父特性 -> 挂唯一父特性
    grouped = {}
    ordered_keys = []
    orphan_subs = []
    parent_keys_by_class = {}
    parent_key_by_code = {}
    # 全局映射： (domain, F编码) -> 父节点key
    # 同一个 F编码在不同 domain 下可能对应不同父节点；如果不隔离 domain，会导致错挂。
    parent_key_by_code_global = {}

    def _feature_code(feature_name):
        matched = re.match(r'^(F\d{6})', str(feature_name or '').strip())
        return matched.group(1) if matched else ''

    def _parent_code_from_identifier(feature_identifier):
        # FS010121-01 -> F010121
        matched = re.match(r'^FS(\d{6})', str(feature_identifier or '').strip())
        return f"F{matched.group(1)}" if matched else ''

    def _parent_code_from_sub_feature_name(sub_feature_name):
        # FS010121-01-xxx -> F010121（子特性名称通常以 FSxxxxxx 开头）
        matched = re.match(r'^FS(\d{6})', str(sub_feature_name or '').strip())
        return f"F{matched.group(1)}" if matched else ''

    # 第一遍：建立父节点索引
    for item in flat_data:
        f1 = item.get('feature_first_classification') or ''
        f2 = item.get('feature_second_classification') or ''
        feature = item.get('feature_name') or ''
        sub_feature = item.get('sub_feature_name') or ''
        if not feature:
            continue

        key = (f1, f2, feature)
        class_key = (f1, f2)
        if class_key not in parent_keys_by_class:
            parent_keys_by_class[class_key] = []
        if key not in parent_keys_by_class[class_key]:
            parent_keys_by_class[class_key].append(key)

        # 仅用“纯父行”覆盖父节点内容，保证父节点字段与正例一致
        if not sub_feature:
            if key not in grouped:
                parent_row = {**item}
                parent_row['parent'] = True
                parent_row['childrenList'] = []
                parent_row['sub_feature_name'] = ''
                grouped[key] = parent_row
                ordered_keys.append(key)
            else:
                children = grouped[key].get('childrenList', [])
                parent_row = {**item}
                parent_row['parent'] = True
                parent_row['childrenList'] = children
                parent_row['sub_feature_name'] = ''
                grouped[key] = parent_row

            code = _feature_code(feature)
            if code:
                if class_key not in parent_key_by_code:
                    parent_key_by_code[class_key] = {}
                parent_key_by_code[class_key][code] = key
                # 全局映射（同 (domain, code) 可能存在多个父节点时，优先保留第一次出现的）
                domain_key = item.get('domain') or ''
                global_map_key = (domain_key, code)
                if global_map_key not in parent_key_by_code_global:
                    parent_key_by_code_global[global_map_key] = key

    # 对于仅出现子行但无父行的特性，补一个虚拟父节点
    for item in flat_data:
        f1 = item.get('feature_first_classification') or ''
        f2 = item.get('feature_second_classification') or ''
        feature = item.get('feature_name') or ''
        sub_feature = item.get('sub_feature_name') or ''
        if not feature or not sub_feature:
            continue
        key = (f1, f2, feature)
        if key not in grouped:
            grouped[key] = {
                'id': None,
                'feature_first_classification': f1,
                'feature_second_classification': f2,
                'feature_name': feature,
                'sub_feature_name': '',
                'feature_identifier': '',
                'domain': item.get('domain') or '',
                'team': '',
                'verification_mode': '',
                'verification_team': '',
                'priority': '',
                'dev_workload': None,
                'detail_workload': None,
                'estimated_dev_workload': None,
                'estimated_verification_workload': None,
                'estimated_system_test_workload': None,
                'create_time': None,
                'update_time': None,
                'operator_person': '',
                'effective_flag': '1',
                'parent': True,
                'childrenList': [],
            }
            ordered_keys.append(key)
        code = _feature_code(feature)
        if code:
            class_key = (f1, f2)
            if class_key not in parent_key_by_code:
                parent_key_by_code[class_key] = {}
            parent_key_by_code[class_key][code] = key
            # 虚拟父节点也写入全局映射
            domain_key = item.get('domain') or ''
            global_map_key = (domain_key, code)
            if global_map_key not in parent_key_by_code_global:
                parent_key_by_code_global[global_map_key] = key

    # 第二遍：挂子节点
    for item in flat_data:
        f1 = item.get('feature_first_classification') or ''
        f2 = item.get('feature_second_classification') or ''
        feature = item.get('feature_name') or ''
        sub_feature = item.get('sub_feature_name') or ''
        if not sub_feature:
            continue

        target_key = None
        class_key = (f1, f2)
        if feature:
            target_key = (f1, f2, feature)
        else:
            # 优先从 sub_feature_name 推导父编码，避免 feature_identifier 与子特性内容不一致导致挂错
            parent_code = _parent_code_from_sub_feature_name(sub_feature) or _parent_code_from_identifier(
                item.get('feature_identifier') or ''
            )
            if parent_code:
                # 先用全局 (domain, code) 映射定位父节点
                child_domain = item.get('domain') or ''
                target_key = parent_key_by_code_global.get((child_domain, parent_code))
                # 兼容：如果全局找不到，再尝试 class_key 下的映射
                if not target_key:
                    target_key = (parent_key_by_code.get(class_key) or {}).get(parent_code)
            if not target_key:
                class_parents = parent_keys_by_class.get(class_key, [])
                if len(class_parents) == 1:
                    target_key = class_parents[0]

        if not target_key or target_key not in grouped:
            orphan_subs.append({**item, 'parent': False, 'childrenList': []})
            continue

        child_row = {**item}
        child_row['parent'] = False
        # 子节点展示字段按正例置空
        child_row['feature_first_classification'] = ''
        child_row['feature_second_classification'] = ''
        child_row['feature_name'] = ''
        child_row['childrenList'] = []
        grouped[target_key]['childrenList'].append(child_row)

    return [grouped[k] for k in ordered_keys] + orphan_subs


def queryFeatureViewByParams():
    """
    根据条件查询特性视图（返回树形结构）
    ---
    tags:
      - 特性视图
    parameters:
      - name: domain
        in: query
        type: string
        required: false
      - name: team
        in: query
        type: string
        required: false
    """
    try:
        domain = request.args.get('domain', '').strip()
        # 兼容 team 单选/多选（前端可能传 team[]=xxx 或重复 team 参数）
        team_list = request.args.getlist('team')
        if not team_list:
            team_single = request.args.get('team', '').strip()
            team_list = [team_single] if team_single else []

        conditions = [FEATURE_VIEW_TABLE.effective_flag == '1']
        if domain:
            conditions.append(FEATURE_VIEW_TABLE.domain == domain)
        if team_list:
            conditions.append(FEATURE_VIEW_TABLE.team.in_(team_list))

        query = db.session.query(FEATURE_VIEW_TABLE).filter(and_(*conditions))
        results = query.order_by(
            FEATURE_VIEW_TABLE.feature_first_classification,
            FEATURE_VIEW_TABLE.feature_second_classification,
            FEATURE_VIEW_TABLE.feature_name,
            FEATURE_VIEW_TABLE.sub_feature_name,
            FEATURE_VIEW_TABLE.id,
        ).all()
        flat_data = [item.to_dict() for item in results]
        tree_data = _build_feature_tree(flat_data)
        return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": tree_data})
    except Exception as e:
        logger.error(f"查询特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"查询失败: {str(e)}", "data": []})


def createFeatureView():
    """创建特性视图记录"""
    try:
        data = request.get_json() or {}
        record = FEATURE_VIEW_TABLE(
            feature_first_classification=data.get('feature_first_classification', ''),
            feature_second_classification=data.get('feature_second_classification', ''),
            feature_name=data.get('feature_name', ''),
            sub_feature_name=data.get('sub_feature_name', ''),
            feature_identifier=data.get('feature_identifier', ''),
            domain=data.get('domain', ''),
            team=data.get('team', ''),
            verification_mode=data.get('verification_mode', ''),
            verification_team=data.get('verification_team', ''),
            priority=data.get('priority', ''),
            dev_workload=data.get('dev_workload'),
            detail_workload=data.get('detail_workload'),
            estimated_dev_workload=data.get('estimated_dev_workload'),
            estimated_verification_workload=data.get('estimated_verification_workload'),
            estimated_system_test_workload=data.get('estimated_system_test_workload'),
            create_time=datetime.now(),
            update_time=datetime.now(),
            operator_person=data.get('operator_person', ''),
            effective_flag='1',
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": "创建成功", "data": record.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"创建失败: {str(e)}", "data": []})


def updateFeatureView():
    """更新特性视图记录（支持批量）"""
    try:
        data = request.get_json() or {}
        rows: List[dict] = data.get('data', [])
        if not rows:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})

        updated = 0
        for row in rows:
            rid = row.get('id')
            if not rid:
                continue
            update_data = {}
            for k in [
                'feature_first_classification', 'feature_second_classification', 'feature_name', 'sub_feature_name',
                'feature_identifier', 'domain', 'team', 'verification_mode', 'verification_team', 'priority',
                'dev_workload', 'detail_workload', 'estimated_dev_workload', 'estimated_verification_workload',
                'estimated_system_test_workload',
            ]:
                if k in row:
                    update_data[k] = row.get(k)
            if update_data:
                update_data['update_time'] = datetime.now()
                db.session.query(FEATURE_VIEW_TABLE).filter(FEATURE_VIEW_TABLE.id == rid).update(update_data)
                updated += 1

        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": f"成功更新 {updated} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"更新失败: {str(e)}", "data": []})


def deleteFeatureView():
    """删除特性视图记录（逻辑删除）"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"code": 400, "status": "error", "message": "ids不能为空", "data": []})
        deleted = db.session.query(FEATURE_VIEW_TABLE).filter(FEATURE_VIEW_TABLE.id.in_(ids)).update(
            {"effective_flag": "0", "update_time": datetime.now()},
            synchronize_session=False,
        )
        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": f"成功删除 {deleted} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"删除失败: {str(e)}", "data": []})


def getFeatureViewOptions():
    """获取筛选选项（domain/team）"""
    try:
        option_type = request.args.get('option_type', '').strip()
        if option_type not in ['domain', 'team']:
            return jsonify({"code": 400, "status": "error", "message": f"不支持的option_type: {option_type}", "data": []})

        # 下拉选项从 person_skill_map 取（与“开发人力投入”一致），保证表为空时也有选项
        column_field = PERSON_SKILL_MAP.domain if option_type == 'domain' else PERSON_SKILL_MAP.team
        results = db.session.query(column_field).filter(
            and_(
                column_field.isnot(None),
                column_field != '',
            )
        ).distinct().all()
        values = sorted(list(set([item[0] for item in results if item and item[0]])))
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": values})
    except Exception as e:
        logger.error(f"获取特性视图选项失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def importFeatureView():
    """批量导入特性视图（xlsx）"""
    try:
        if 'file' not in request.files:
            return jsonify({"code": 400, "status": "error", "message": "未上传文件", "data": []})
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({"code": 400, "status": "error", "message": "仅支持上传 .xlsx 格式文件", "data": []})

        df = pd.read_excel(file, engine="openpyxl").fillna(value='')

        # 统一清洗 Excel 表头：去掉首尾空格、全角空格等，避免 row.get('特性一级分类') 取不到导致整列写空。
        df.columns = [
            str(c).replace('\u3000', ' ').strip() if c is not None else c for c in df.columns
        ]

        # Excel 合并单元格常见现象：同一合并区域内后续/前置行可能被解析成空字符串，
        # 这里对关键字段做双向填充，保证 rows 的分类/域/团队 不会变成 ''。
        for col in ['领域', '团队', '特性一级分类', '特性二级分类']:
            if col in df.columns:
                df[col] = df[col].replace('', pd.NA)
                df[col] = df[col].ffill().bfill().fillna('')

        inserted, updated, skipped = 0, 0, 0
        for _, row in df.iterrows():
            try:
                rid = row.get('ID', '')
                payload = {
                    'feature_first_classification': str(row.get('特性一级分类', '')).strip(),
                    'feature_second_classification': str(row.get('特性二级分类', '')).strip(),
                    'feature_name': str(row.get('特性', '')).strip(),
                    'sub_feature_name': str(row.get('子特性', '')).strip(),
                    'feature_identifier': str(row.get('特性标识', '')).strip(),
                    'domain': str(row.get('领域', '')).strip(),
                    'team': str(row.get('团队', '')).strip(),
                    'verification_mode': str(row.get('验证方式', '')).strip(),
                    'verification_team': str(row.get('验证团队', '')).strip(),
                    'priority': str(row.get('优先级', '')).strip(),
                    'dev_workload': row.get('开发工作量（人天）', None) if row.get('开发工作量（人天）', '') != '' else None,
                    'detail_workload': row.get('详设工作量（人天）', None) if row.get('详设工作量（人天）', '') != '' else None,
                    'estimated_dev_workload': row.get('预计开发工作量', None) if row.get('预计开发工作量', '') != '' else None,
                    'estimated_verification_workload': row.get('预计验证工作量', None) if row.get('预计验证工作量', '') != '' else None,
                    'estimated_system_test_workload': row.get('预计系统测试工作量', None) if row.get('预计系统测试工作量', '') != '' else None,
                }

                if rid:
                    existing = db.session.query(FEATURE_VIEW_TABLE).filter(
                        and_(FEATURE_VIEW_TABLE.id == int(rid), FEATURE_VIEW_TABLE.effective_flag == '1')
                    ).first()
                else:
                    existing = None

                if existing:
                    for k, v in payload.items():
                        setattr(existing, k, v)
                    existing.update_time = datetime.now()
                    updated += 1
                else:
                    record = FEATURE_VIEW_TABLE(
                        **payload,
                        create_time=datetime.now(),
                        update_time=datetime.now(),
                        operator_person='',
                        effective_flag='1',
                    )
                    db.session.add(record)
                    inserted += 1
            except Exception:
                skipped += 1

        db.session.commit()
        return jsonify({
            "code": 200,
            "status": "success",
            "message": f"导入完成：新增 {inserted} 条，更新 {updated} 条，跳过 {skipped} 条",
            "data": {"inserted": inserted, "updated": updated, "skipped": skipped},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"导入特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"导入失败: {str(e)}", "data": []})


def exportFeatureView():
    """导出特性视图（xlsx）"""
    try:
        domain = request.args.get('domain', '').strip()
        team_list = request.args.getlist('team')
        if not team_list:
            team_single = request.args.get('team', '').strip()
            team_list = [team_single] if team_single else []

        conditions = [FEATURE_VIEW_TABLE.effective_flag == '1']
        if domain:
            conditions.append(FEATURE_VIEW_TABLE.domain == domain)
        if team_list:
            conditions.append(FEATURE_VIEW_TABLE.team.in_(team_list))

        results = db.session.query(FEATURE_VIEW_TABLE).filter(and_(*conditions)).order_by(
            FEATURE_VIEW_TABLE.domain, FEATURE_VIEW_TABLE.team, FEATURE_VIEW_TABLE.id
        ).all()

        rows = []
        for item in results:
            rows.append({
                'ID': item.id,
                '特性一级分类': item.feature_first_classification or '',
                '特性二级分类': item.feature_second_classification or '',
                '特性': item.feature_name or '',
                '子特性': item.sub_feature_name or '',
                '特性标识': item.feature_identifier or '',
                '领域': item.domain or '',
                '团队': item.team or '',
                '验证方式': item.verification_mode or '',
                '验证团队': item.verification_team or '',
                '优先级': item.priority or '',
                '开发工作量（人天）': item.dev_workload if item.dev_workload is not None else '',
                '详设工作量（人天）': item.detail_workload if item.detail_workload is not None else '',
                '预计开发工作量': item.estimated_dev_workload if item.estimated_dev_workload is not None else '',
                '预计验证工作量': item.estimated_verification_workload if item.estimated_verification_workload is not None else '',
                '预计系统测试工作量': item.estimated_system_test_workload if item.estimated_system_test_workload is not None else '',
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='特性视图')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='特性视图.xlsx',
        )
    except Exception as e:
        logger.error(f"导出特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"导出失败: {str(e)}", "data": []})


def countFeatureViewByDomainTeam():
    """
    统计符合条件的特性视图记录数量（用于删除前确认）
    ---
    tags:
      - 特性视图
    parameters:
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
    """
    try:
        domain = request.args.get('domain', '').strip()
        team = request.args.get('team', '').strip()

        # 至少传入一个条件
        if not domain and not team:
            return jsonify({"code": 400, "status": "error", "message": "domain 和 team 至少需要传入一个", "data": {"count": 0}})

        conditions = [FEATURE_VIEW_TABLE.effective_flag == '1']
        if domain:
            conditions.append(FEATURE_VIEW_TABLE.domain == domain)
        if team:
            conditions.append(FEATURE_VIEW_TABLE.team == team)

        count = db.session.query(FEATURE_VIEW_TABLE).filter(and_(*conditions)).count()
        return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": {"count": count}})
    except Exception as e:
        logger.error(f"统计特性视图数量失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"查询失败: {str(e)}", "data": {"count": 0}})


def deleteFeatureViewByDomainTeam():
    """
    按领域/团队批量删除特性视图记录（逻辑删除）
    ---
    tags:
      - 特性视图
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            domain:
              type: string
              description: 领域
            team:
              type: string
              description: 团队
    """
    try:
        data = request.get_json() or {}
        domain = data.get('domain', '').strip()
        team = data.get('team', '').strip()

        # 至少传入一个条件
        if not domain and not team:
            return jsonify({"code": 400, "status": "error", "message": "domain 和 team 至少需要传入一个", "data": []})

        conditions = [FEATURE_VIEW_TABLE.effective_flag == '1']
        if domain:
            conditions.append(FEATURE_VIEW_TABLE.domain == domain)
        if team:
            conditions.append(FEATURE_VIEW_TABLE.team == team)

        deleted = db.session.query(FEATURE_VIEW_TABLE).filter(and_(*conditions)).update(
            {"effective_flag": "0", "update_time": datetime.now()},
            synchronize_session=False,
        )
        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": f"成功删除 {deleted} 条记录", "data": {"deleted": deleted}})
    except Exception as e:
        db.session.rollback()
        logger.error(f"按领域/团队删除特性视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"删除失败: {str(e)}", "data": []})

