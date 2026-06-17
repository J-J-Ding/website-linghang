from sqlalchemy import or_, and_
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from requirement_schedule.data_model import db, PERSON_SKILL_MAP
from flask import request, jsonify, send_file
import logging
import pandas as pd
import io

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


# 定义查询参数模型
class PersonSkillMapData(BaseModel):
    id: Optional[int] = None
    department: Optional[str] = None
    project_group: Optional[str] = None
    domain: Optional[str] = None
    team: Optional[str] = None
    person_belong: Optional[str] = None
    employee_id: Optional[str] = None
    name: Optional[str] = None
    leave_time: Optional[str] = None
    skill_category: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def queryPersonSkillMapByParams():
    """
    查询人员技能地图
    ---
    tags:
      - 人员技能地图
    description: 查询人员技能地图
    parameters:
      - name: department
        in: query
        description: 部门
        required: false
        type: string
      - name: project_group
        in: query
        description: 项目组
        required: false
        type: string
      - name: domain
        in: query
        description: 领域
        required: false
        type: string
      - name: team
        in: query
        description: 团队
        required: false
        type: string
      - name: person_belong
        in: query
        description: 人员归属
        required: false
        type: string
      - name: employee_id
        in: query
        description: 工号
        required: false
        type: string
      - name: name
        in: query
        description: 姓名
        required: false
        type: string
      - name: leave_time
        in: query
        description: 离职时间（为空表示在职）
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
    """
    try:
        query_params = request.args.to_dict()
        conditions = []
        
        if query_params.get('department'):
            conditions.append(PERSON_SKILL_MAP.department.like(f"%{query_params['department']}%"))
        if query_params.get('project_group'):
            conditions.append(PERSON_SKILL_MAP.project_group.like(f"%{query_params['project_group']}%"))
        if query_params.get('domain'):
            conditions.append(PERSON_SKILL_MAP.domain.like(f"%{query_params['domain']}%"))
        if query_params.get('team'):
            conditions.append(PERSON_SKILL_MAP.team.like(f"%{query_params['team']}%"))
        if query_params.get('person_belong'):
            conditions.append(PERSON_SKILL_MAP.person_belong == query_params['person_belong'])
        if query_params.get('employee_id'):
            conditions.append(PERSON_SKILL_MAP.employee_id.like(f"%{query_params['employee_id']}%"))
        if query_params.get('name'):
            conditions.append(PERSON_SKILL_MAP.name.like(f"%{query_params['name']}%"))
        if query_params.get('leave_time') is not None:
            if query_params['leave_time'] == '':
                # 查询在职人员（leave_time为空）
                conditions.append(or_(
                    PERSON_SKILL_MAP.leave_time == '',
                    PERSON_SKILL_MAP.leave_time.is_(None)
                ))
            elif query_params['leave_time'] == 'has_leave':
                # 查询已离职人员（leave_time不为空）
                conditions.append(and_(
                    PERSON_SKILL_MAP.leave_time != '',
                    PERSON_SKILL_MAP.leave_time.isnot(None)
                ))
            else:
                conditions.append(PERSON_SKILL_MAP.leave_time.like(f"%{query_params['leave_time']}%"))
        
        query = db.session.query(PERSON_SKILL_MAP)
        if conditions:
            query = query.filter(and_(*conditions))
        
        results = query.order_by(PERSON_SKILL_MAP.id.desc()).all()
        data = [item.to_dict() for item in results]
        
        # 工号补零处理：确保所有工号显示为8位
        for item in data:
            if item.get('employee_id'):
                item['employee_id'] = pad_employee_id(item['employee_id'])
        
        logger.info(f"查询人员技能地图成功 - 共 {len(data)} 条记录")
        return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data})
    except Exception as e:
        logger.error(f"查询人员技能地图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"查询失败: {str(e)}", "data": []})


def createPersonSkillMap():
    """
    创建人员技能地图记录
    ---
    tags:
      - 人员技能地图
    description: 创建人员技能地图记录
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [department, project_group, domain, team, person_belong, employee_id, name]
          properties:
            department:
              type: string
            project_group:
              type: string
            domain:
              type: string
            team:
              type: string
            person_belong:
              type: string
            employee_id:
              type: string
            name:
              type: string
            leave_time:
              type: string
            skill_category:
              type: string
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})
        
        # 检查必填字段
        required_fields = ['department', 'project_group', 'domain', 'team', 'person_belong', 'employee_id', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"code": 400, "status": "error", "message": f"{field}不能为空", "data": []})
        
        # 工号补零处理
        employee_id_padded = pad_employee_id(data['employee_id'])
        
        # 检查工号是否已存在
        existing = db.session.query(PERSON_SKILL_MAP).filter(
            PERSON_SKILL_MAP.employee_id == employee_id_padded
        ).first()
        if existing:
            return jsonify({"code": 400, "status": "error", "message": f"工号 {employee_id_padded} 已存在", "data": []})
        
        # 创建新记录
        new_record = PERSON_SKILL_MAP(
            department=data['department'],
            project_group=data['project_group'],
            domain=data['domain'],
            team=data['team'],
            person_belong=data['person_belong'],
            employee_id=employee_id_padded,
            name=data['name'],
            leave_time=data.get('leave_time', ''),
            skill_category=data.get('skill_category', '')
        )
        
        db.session.add(new_record)
        db.session.commit()
        
        # 同步更新 requirement_dev_human_resource（延迟导入避免循环依赖）
        try:
            from requirement_schedule.human_resource_setting import syncRequirementDevHumanResource
            syncRequirementDevHumanResource(data['domain'], data['team'])
        except Exception as sync_error:
            logger.warning(f"同步 requirement_dev_human_resource 失败: {str(sync_error)}")
        
        logger.info(f"创建人员技能地图记录成功 - 工号: {data['employee_id']}, 姓名: {data['name']}")
        return jsonify({"code": 200, "status": "success", "message": "创建成功", "data": new_record.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建人员技能地图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"创建失败: {str(e)}", "data": []})


def updatePersonSkillMap():
    """
    更新人员技能地图记录
    ---
    tags:
      - 人员技能地图
    description: 更新人员技能地图记录（支持单个和批量）
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
              description: 人员技能地图数据数组
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        person_list = data.get('data', [])
        
        if not person_list:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})
        
        updated_count = 0
        for person_data in person_list:
            person_id = person_data.get('id')
            if not person_id:
                continue
            
            # 检查工号是否被其他记录使用
            employee_id = person_data.get('employee_id')
            if employee_id:
                # 工号补零处理
                employee_id_padded = pad_employee_id(employee_id)
                existing = db.session.query(PERSON_SKILL_MAP).filter(
                    and_(
                        PERSON_SKILL_MAP.employee_id == employee_id_padded,
                        PERSON_SKILL_MAP.id != person_id
                    )
                ).first()
                if existing:
                    logger.warning(f"工号 {employee_id_padded} 已被其他记录使用，跳过更新")
                    continue
            
            # 构建更新数据
            update_data = {}
            if 'department' in person_data:
                update_data['department'] = person_data['department']
            if 'project_group' in person_data:
                update_data['project_group'] = person_data['project_group']
            if 'domain' in person_data:
                update_data['domain'] = person_data['domain']
            if 'team' in person_data:
                update_data['team'] = person_data['team']
            if 'person_belong' in person_data:
                update_data['person_belong'] = person_data['person_belong']
            if 'employee_id' in person_data:
                update_data['employee_id'] = pad_employee_id(person_data['employee_id'])
            if 'name' in person_data:
                update_data['name'] = person_data['name']
            if 'leave_time' in person_data:
                update_data['leave_time'] = person_data.get('leave_time', '')
            if 'skill_category' in person_data:
                update_data['skill_category'] = person_data.get('skill_category', '')
            
            if update_data:
                # 获取更新前的记录信息（用于同步）
                old_record = db.session.query(PERSON_SKILL_MAP).filter(
                    PERSON_SKILL_MAP.id == person_id
                ).first()
                
                db.session.query(PERSON_SKILL_MAP) \
                    .filter(PERSON_SKILL_MAP.id == person_id) \
                    .update(update_data)
                updated_count += 1
                
                # 同步更新 requirement_dev_human_resource（延迟导入避免循环依赖）
                if old_record:
                    domain = update_data.get('domain', old_record.domain)
                    team = update_data.get('team', old_record.team)
                    try:
                        from requirement_schedule.human_resource_setting import syncRequirementDevHumanResource
                        syncRequirementDevHumanResource(domain, team)
                    except Exception as sync_error:
                        logger.warning(f"同步 requirement_dev_human_resource 失败: {str(sync_error)}")
        
        db.session.commit()
        logger.info(f"更新人员技能地图记录成功 - 共更新 {updated_count} 条记录")
        return jsonify({"code": 200, "status": "success", "message": f"成功更新 {updated_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新人员技能地图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"更新失败: {str(e)}", "data": []})


def deletePersonSkillMap():
    """
    删除人员技能地图记录
    ---
    tags:
      - 人员技能地图
    description: 删除人员技能地图记录（支持单个和批量）
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: []
          properties:
            ids:
              type: array
              description: 要删除的记录ID数组
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({"code": 400, "status": "error", "message": "ID列表不能为空", "data": []})
        
        # 查询待删除的记录，检查是否有已离职人员（离职人员不允许删除）
        records_to_delete = db.session.query(PERSON_SKILL_MAP).filter(
            PERSON_SKILL_MAP.id.in_(ids)
        ).all()
        
        departed = [
            r for r in records_to_delete
            if r.leave_time and str(r.leave_time).strip()
        ]
        if departed:
            names_str = '、'.join([
                f"{r.name}(工号:{r.employee_id}，离职时间:{r.leave_time})"
                for r in departed
            ])
            logger.warning(f"尝试删除已离职人员，已拒绝: {names_str}")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": f"以下人员已离职，不允许删除，如需修改请直接编辑记录：{names_str}",
                "data": []
            })
        
        deleted_count = db.session.query(PERSON_SKILL_MAP) \
            .filter(PERSON_SKILL_MAP.id.in_(ids)) \
            .delete(synchronize_session=False)
        
        db.session.commit()
        logger.info(f"删除人员技能地图记录成功 - 共删除 {deleted_count} 条记录")
        return jsonify({"code": 200, "status": "success", "message": f"成功删除 {deleted_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除人员技能地图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"删除失败: {str(e)}", "data": []})


def getPersonSkillMapOptions():
    """
    获取人员技能地图的选项数据（用于下拉框等）
    ---
    tags:
      - 人员技能地图
    description: 获取人员技能地图的选项数据
    parameters:
      - name: option_type
        in: query
        description: 选项类型 (department, project_group, domain, team, person_belong, skill_category)
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
    """
    try:
        option_type = request.args.get('option_type')
        if not option_type:
            return jsonify({"code": 400, "status": "error", "message": "option_type参数不能为空", "data": []})
        
        valid_types = ['department', 'project_group', 'domain', 'team', 'person_belong', 'skill_category']
        if option_type not in valid_types:
            return jsonify({"code": 400, "status": "error", "message": f"option_type必须是以下之一: {', '.join(valid_types)}", "data": []})
        
        # 获取对应字段的唯一值
        column_map = {
            'department': PERSON_SKILL_MAP.department,
            'project_group': PERSON_SKILL_MAP.project_group,
            'domain': PERSON_SKILL_MAP.domain,
            'team': PERSON_SKILL_MAP.team,
            'person_belong': PERSON_SKILL_MAP.person_belong,
            'skill_category': PERSON_SKILL_MAP.skill_category
        }
        
        column = column_map[option_type]
        results = db.session.query(column) \
            .filter(and_(
                column.isnot(None),
                column != ''
            )) \
            .distinct() \
            .order_by(column) \
            .all()
        
        options = [item[0] for item in results if item[0] and item[0].strip()]
        
        logger.info(f"获取{option_type}选项成功 - 共 {len(options)} 个选项")
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": options})
    except Exception as e:
        logger.error(f"获取选项失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def exportPersonSkillMap():
    """
    批量导出人员技能地图
    ---
    tags:
      - 人员技能地图
    description: 根据筛选条件导出人员技能地图为 Excel 文件（.xlsx）
    parameters:
      - name: department
        in: query
        type: string
        required: false
      - name: project_group
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
      - name: person_belong
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
      - name: leave_time
        in: query
        type: string
        required: false
    responses:
      200:
        description: 返回 Excel 文件
    """
    try:
        query_params = request.args.to_dict()
        conditions = []

        if query_params.get('department'):
            conditions.append(PERSON_SKILL_MAP.department.like(f"%{query_params['department']}%"))
        if query_params.get('project_group'):
            conditions.append(PERSON_SKILL_MAP.project_group.like(f"%{query_params['project_group']}%"))
        if query_params.get('domain'):
            conditions.append(PERSON_SKILL_MAP.domain.like(f"%{query_params['domain']}%"))
        if query_params.get('team'):
            conditions.append(PERSON_SKILL_MAP.team.like(f"%{query_params['team']}%"))
        if query_params.get('person_belong'):
            conditions.append(PERSON_SKILL_MAP.person_belong == query_params['person_belong'])
        if query_params.get('employee_id'):
            conditions.append(PERSON_SKILL_MAP.employee_id.like(f"%{query_params['employee_id']}%"))
        if query_params.get('name'):
            conditions.append(PERSON_SKILL_MAP.name.like(f"%{query_params['name']}%"))
        if query_params.get('leave_time') is not None:
            if query_params['leave_time'] == '':
                conditions.append(or_(
                    PERSON_SKILL_MAP.leave_time == '',
                    PERSON_SKILL_MAP.leave_time.is_(None)
                ))
            elif query_params['leave_time'] == 'has_leave':
                conditions.append(and_(
                    PERSON_SKILL_MAP.leave_time != '',
                    PERSON_SKILL_MAP.leave_time.isnot(None)
                ))
            else:
                conditions.append(PERSON_SKILL_MAP.leave_time.like(f"%{query_params['leave_time']}%"))

        query = db.session.query(PERSON_SKILL_MAP)
        if conditions:
            query = query.filter(and_(*conditions))

        results = query.order_by(PERSON_SKILL_MAP.id.asc()).all()

        # 构建导出数据
        rows = []
        for item in results:
            rows.append({
                '部门': item.department or '',
                '项目组': item.project_group or '',
                '领域': item.domain or '',
                '团队': item.team or '',
                '人员归属': item.person_belong or '',
                '工号': pad_employee_id(item.employee_id) if item.employee_id else '',
                '姓名': item.name or '',
                '离职时间': item.leave_time or '',
                '技能/特性分类': item.skill_category or '',
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='人员技能地图')
        output.seek(0)

        logger.info(f"导出人员技能地图成功 - 共 {len(rows)} 条记录")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='人员技能地图.xlsx'
        )
    except Exception as e:
        logger.error(f"导出人员技能地图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"导出失败: {str(e)}", "data": []})


def importPersonSkillMap():
    """
    批量导入人员技能地图
    ---
    tags:
      - 人员技能地图
    description: 批量导入人员技能地图（Excel文件）
    consumes:
      - multipart/form-data
    parameters:
      - name: X-Emp-No
        in: header
        description: 员工工号
        required: true
        type: string
      - name: file
        in: formData
        description: 上传的Excel文件(xlsx格式)
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
        
        # 读取Excel文件
        df = pd.read_excel(file, engine="openpyxl")
        df = df.fillna(value='')  # 填充空值
        
        # 检查必填字段
        required_columns = ['部门', '项目组', '领域', '团队', '人员归属', '工号', '姓名']
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
        affected_pairs = set()  # 记录受影响的 (domain, team) 对，用于事后同步 02
        
        # 辅助函数：统一处理空值（将None、空字符串统一处理）
        def normalize_value(value):
            """将None、空字符串统一处理为空字符串"""
            if value is None:
                return ''
            return str(value).strip() if str(value).strip() else ''
        
        # 辅助函数：比较两个值是否相同（处理空值）
        def values_equal(val1, val2):
            """比较两个值是否相同，统一处理空值"""
            val1_normalized = normalize_value(val1)
            val2_normalized = normalize_value(val2)
            return val1_normalized == val2_normalized
        
        for index, row in df.iterrows():
            try:
                # 读取并处理字段值
                department = normalize_value(row['部门']) if pd.notna(row['部门']) else ''
                project_group = normalize_value(row['项目组']) if pd.notna(row['项目组']) else ''
                domain = normalize_value(row['领域']) if pd.notna(row['领域']) else ''
                team = normalize_value(row['团队']) if pd.notna(row['团队']) else ''
                person_belong = normalize_value(row['人员归属']) if pd.notna(row['人员归属']) else ''
                employee_id = pad_employee_id(normalize_value(row['工号'])) if pd.notna(row['工号']) else ''
                name = normalize_value(row['姓名']) if pd.notna(row['姓名']) else ''
                leave_time = normalize_value(row['离职时间']) if '离职时间' in df.columns and pd.notna(row.get('离职时间')) else ''
                skill_category = normalize_value(row['技能/特性分类']) if '技能/特性分类' in df.columns and pd.notna(row.get('技能/特性分类')) else ''
                
                # 验证必填字段
                if not all([department, project_group, domain, team, person_belong, employee_id, name]):
                    skipped_count += 1
                    error_messages.append(f"第{index + 2}行：必填字段不能为空")
                    continue
                
                # 检查工号是否已存在
                existing = db.session.query(PERSON_SKILL_MAP).filter(
                    PERSON_SKILL_MAP.employee_id == employee_id
                ).first()
                
                if existing:
                    # 比较除工号外的所有字段，判断是否有变化
                    fields_changed = (
                        not values_equal(existing.department, department) or
                        not values_equal(existing.project_group, project_group) or
                        not values_equal(existing.domain, domain) or
                        not values_equal(existing.team, team) or
                        not values_equal(existing.person_belong, person_belong) or
                        not values_equal(existing.name, name) or
                        not values_equal(existing.leave_time, leave_time) or
                        not values_equal(existing.skill_category, skill_category)
                    )
                    
                    if fields_changed:
                        # 有字段变化，更新所有字段
                        existing.department = department
                        existing.project_group = project_group
                        existing.domain = domain
                        existing.team = team
                        existing.person_belong = person_belong
                        existing.name = name
                        existing.leave_time = leave_time
                        existing.skill_category = skill_category
                        updated_count += 1
                        if domain and team:
                            affected_pairs.add((domain, team))
                    else:
                        # 所有字段完全相同，跳过（不执行任何数据库操作）
                        skipped_count += 1
                else:
                    # 工号不存在，创建新记录
                    new_record = PERSON_SKILL_MAP(
                        department=department,
                        project_group=project_group,
                        domain=domain,
                        team=team,
                        person_belong=person_belong,
                        employee_id=employee_id,
                        name=name,
                        leave_time=leave_time,
                        skill_category=skill_category
                    )
                    db.session.add(new_record)
                    inserted_count += 1
                    if domain and team:
                        affected_pairs.add((domain, team))
                    
            except Exception as e:
                skipped_count += 1
                error_messages.append(f"第{index + 2}行处理失败: {str(e)}")
                logger.error(f"处理第{index + 2}行数据失败: {str(e)}", exc_info=True)
                continue
        
        db.session.commit()
        
        # 导入成功后，自动同步更新 02 需求交付人力投入（当年全12个月）
        if affected_pairs:
            current_year = str(datetime.now().year)
            try:
                from requirement_schedule.human_resource_setting import syncRequirementDevHumanResource
                for domain_val, team_val in affected_pairs:
                    syncRequirementDevHumanResource(domain_val, team_val, current_year)
                logger.info(f"批量导入人员技能地图后同步完成 - 共 {len(affected_pairs)} 个(领域,团队)组合")
            except Exception as sync_error:
                logger.warning(f"批量导入后同步 requirement_dev_human_resource 失败: {str(sync_error)}")
        
        message = f"批量导入完成: 成功新增 {inserted_count} 条, 更新 {updated_count} 条, 跳过 {skipped_count} 条"
        if error_messages:
            message += f"\n错误详情: {'; '.join(error_messages[:10])}"  # 最多显示10条错误
        
        logger.info(f"批量导入人员技能地图完成 - 新增: {inserted_count}, 更新: {updated_count}, 跳过: {skipped_count}")
        return jsonify({
            "code": 200,
            "status": "success",
            "message": message,
            "data": {
                "inserted": inserted_count,
                "updated": updated_count,
                "skipped": skipped_count
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量导入人员技能地图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"批量导入失败: {str(e)}", "data": []})
