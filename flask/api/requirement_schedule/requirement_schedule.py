from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, case, distinct
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union
import json
import copy
from requirement_schedule.data_model import db, REQUIREMENT_SCHEDULE_TABLE, REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE, REQUIREMENT_SCHEDULE_PERMISSION_TABLE
from flask import request, jsonify
import logging

logger = logging.getLogger("Logger")

# 定义查询参数模型
class RequirementScheduleData(BaseModel):
    id: Optional[int] = None
    work_item_type: Optional[str] = None
    identifier: Optional[str] = None
    title: Optional[str] = None
    reuse_degree: Optional[str] = None
    feature_identifier: Optional[str] = None
    feature_attribute: Optional[str] = None
    verification_mode: Optional[str] = None
    verification_team: Optional[str] = None
    requirement_sort: Optional[str] = None
    priority: Optional[str] = None
    domain: Optional[str] = None
    team: Optional[str] = None
    first_evaluation_conclusion: Optional[str] = None
    second_evaluation_conclusion: Optional[str] = None
    estimated_workload: Optional[float] = None
    estimated_dev_workload: Optional[float] = None
    estimated_verification_workload: Optional[float] = None
    estimated_system_test_workload: Optional[float] = None
    plan_start_dev_date: Optional[str] = None
    plan_finish_dev_date: Optional[str] = None
    plan_start_integration_test_date: Optional[str] = None
    plan_finish_integration_test_date: Optional[str] = None
    plan_start_system_test_date: Optional[str] = None
    plan_finish_system_test_date: Optional[str] = None
    plan_delivery_date: Optional[str] = None
    belong_product: Optional[str] = None
    product_roadmap: Optional[str] = None
    requirement_preplanning: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def queryRequirementScheduleByParams():
    """
    查询需求清单
    ---
    tags:
      - 需求排期助手
    description: 查询需求清单
    parameters:
      - name: belong_product
        in: query
        description: 所属产品
        required: false
        type: string
      - name: product_roadmap
        in: query
        description: 产品路标
        required: false
        type: string
      - name: requirement_preplanning
        in: query
        description: 需求预规划
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
      - name: work_item_type
        in: query
        description: 工作项类型
        required: false
        type: string
    responses:
      200:
        description: 成功返回数据
    """
    conditions = [REQUIREMENT_SCHEDULE_TABLE.effective_flag == '1']
    print("11111111111111111111111111111111111111111\n")
    query_params = request.args.to_dict()
    print(query_params)
    requirementScheduleData = RequirementScheduleData(**query_params)
    print(requirementScheduleData)
    if requirementScheduleData.belong_product:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.belong_product == requirementScheduleData.belong_product)
    if requirementScheduleData.product_roadmap:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.product_roadmap == requirementScheduleData.product_roadmap)
    if requirementScheduleData.requirement_preplanning:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.requirement_preplanning == requirementScheduleData.requirement_preplanning)
    if requirementScheduleData.domain:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.domain.like(f"%{requirementScheduleData.domain}%"))
    if requirementScheduleData.team:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.team.like(f"%{requirementScheduleData.team}%"))
    if requirementScheduleData.work_item_type:
        conditions.append(REQUIREMENT_SCHEDULE_TABLE.work_item_type == requirementScheduleData.work_item_type)
    
    try:
        results = db.session.query(REQUIREMENT_SCHEDULE_TABLE) \
            .filter(and_(*conditions)) \
            .order_by(REQUIREMENT_SCHEDULE_TABLE.id.desc()).all()
        
        data = [item.to_dict() for item in results]
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": data})
    except Exception as e:
        logger.error(f"查询需求清单失败: {str(e)}")
        return jsonify({"code": 400, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def updateRequirementSchedule():
    """
    更新需求清单（支持单个和批量）
    ---
    tags:
      - 需求排期助手
    description: 更新需求清单
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
              description: 需求清单数据数组
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        requirement_list = data.get('data', [])
        employ_no = request.headers.get('X-Emp-No', '')
        current_time = datetime.now()
        
        if not requirement_list:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})
        
        updated_count = 0
        for req_data in requirement_list:
            req_id = req_data.get('id')
            if not req_id:
                continue
            
            # 只更新可编辑字段
            update_data = {
                'first_evaluation_conclusion': req_data.get('first_evaluation_conclusion'),
                'estimated_dev_workload': req_data.get('estimated_dev_workload'),
                'estimated_verification_workload': req_data.get('estimated_verification_workload'),
                'estimated_system_test_workload': req_data.get('estimated_system_test_workload'),
                'plan_start_dev_date': req_data.get('plan_start_dev_date'),
                'plan_finish_dev_date': req_data.get('plan_finish_dev_date'),
                'plan_start_integration_test_date': req_data.get('plan_start_integration_test_date'),
                'plan_finish_integration_test_date': req_data.get('plan_finish_integration_test_date'),
                'plan_start_system_test_date': req_data.get('plan_start_system_test_date'),
                'plan_finish_system_test_date': req_data.get('plan_finish_system_test_date'),
                'plan_delivery_date': req_data.get('plan_delivery_date'),
                'update_time': current_time,
                'operator_person': employ_no
            }
            
            # 移除None值
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            db.session.query(REQUIREMENT_SCHEDULE_TABLE) \
                .filter(REQUIREMENT_SCHEDULE_TABLE.id == req_id) \
                .update(update_data)
            updated_count += 1
        
        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": f"成功更新 {updated_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新需求清单失败: {str(e)}")
        return jsonify({"code": 400, "status": "error", "message": f"更新失败: {str(e)}", "data": []})


def getFilterHistory():
    """
    获取筛选字段历史输入
    ---
    tags:
      - 需求排期助手
    description: 获取筛选字段历史输入
    parameters:
      - name: filter_type
        in: query
        description: 筛选类型 (product_roadmap, requirement_preplanning, domain, team)
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
    """
    try:
        filter_type = request.args.get('filter_type')
        if not filter_type:
            return jsonify({"code": 400, "status": "error", "message": "filter_type参数不能为空", "data": []})
        
        logger.info(f"获取筛选字段历史输入 - filter_type: {filter_type}")
        
        # "领域"和"团队"从主表获取唯一值，同时合并历史表中的值
        if filter_type in ['domain', 'team']:
            try:
                # 从主表查询对应字段的唯一值（非空）
                if filter_type == 'domain':
                    column_field = REQUIREMENT_SCHEDULE_TABLE.domain
                else:  # team
                    column_field = REQUIREMENT_SCHEDULE_TABLE.team
                
                # 从主表获取唯一值
                main_table_results = db.session.query(column_field) \
                    .filter(
                        and_(
                            column_field.isnot(None),
                            column_field != '',
                            REQUIREMENT_SCHEDULE_TABLE.effective_flag == '1'
                        )
                    ) \
                    .distinct() \
                    .all()
                
                # 从历史表获取值（用户新创建的）
                history_results = db.session.query(REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE) \
                    .filter(
                        and_(
                            REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.filter_type == filter_type,
                            REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.effective_flag == '1'
                        )
                    ) \
                    .all()
                
                # 合并主表和历史表的值
                main_values = [item[0] for item in main_table_results if item[0] and item[0].strip()]
                history_values = [item.filter_value for item in history_results if item.filter_value and item.filter_value.strip()]
                
                # 合并、去重并排序
                unique_values = sorted(list(set(main_values + history_values)))
                logger.info(f"获取{filter_type}成功 - 主表值数量: {len(main_values)}, 历史表值数量: {len(history_values)}, 合并后数量: {len(unique_values)}")
            except Exception as e:
                logger.error(f"查询{filter_type}失败: {str(e)}", exc_info=True)
                raise
        else:
            # "产品路标"和"需求预规划"从历史表获取
            try:
                results = db.session.query(REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE) \
                    .filter(
                        and_(
                            REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.filter_type == filter_type,
                            REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.effective_flag == '1'
                        )
                    ) \
                    .order_by(REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.update_time.desc()) \
                    .all()
                
                # 去重并返回唯一值列表
                unique_values = list(set([item.filter_value for item in results if item.filter_value]))
                logger.info(f"获取{filter_type}成功 - 历史表记录数量: {len(results)}, 唯一值数量: {len(unique_values)}")
            except Exception as e:
                logger.error(f"查询{filter_type}失败: {str(e)}", exc_info=True)
                raise
        
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": unique_values})
    except Exception as e:
        logger.error(f"获取筛选字段历史输入失败 - filter_type: {filter_type}, 错误: {str(e)}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"错误堆栈: {error_trace}")
        return jsonify({"code": 500, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def saveFilterHistory():
    """
    保存筛选字段历史输入
    ---
    tags:
      - 需求排期助手
    description: 保存筛选字段历史输入
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: []
          properties:
            filter_type:
              type: string
              description: 筛选类型
            filter_value:
              type: string
              description: 筛选值
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        filter_type = data.get('filter_type')
        filter_value = data.get('filter_value')
        employ_no = request.headers.get('X-Emp-No', '')
        current_time = datetime.now()
        
        if not filter_type or not filter_value:
            return jsonify({"code": 400, "status": "error", "message": "filter_type和filter_value不能为空", "data": []})
        
        # 检查是否已存在
        existing = db.session.query(REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE) \
            .filter(
                and_(
                    REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.filter_type == filter_type,
                    REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.filter_value == filter_value,
                    REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE.effective_flag == '1'
                )
            ) \
            .first()
        
        if existing:
            # 更新更新时间
            existing.update_time = current_time
            existing.operator_person = employ_no
        else:
            # 新增
            new_record = REQUIREMENT_SCHEDULE_FILTER_HISTORY_TABLE(
                filter_type=filter_type,
                filter_value=filter_value,
                create_time=current_time,
                update_time=current_time,
                operator_person=employ_no,
                effective_flag='1'
            )
            db.session.add(new_record)
        
        db.session.commit()
        return jsonify({"code": 200, "status": "success", "message": "保存成功", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存筛选字段历史输入失败: {str(e)}")
        return jsonify({"code": 400, "status": "error", "message": f"保存失败: {str(e)}", "data": []})


def syncRdcData():
    """
    从中兴内部 RDC 平台拉取工作项数据，写入 requirement_schedule_table 表。
    请求体 JSON 字段：
      - work_type: 工作项类型，默认 '产品需求'
      - username: 工号（必填）
      - password: 明文密码（必填），后端自动 Base64 编码后传给认证接口
    """
    import base64
    try:
        data = request.get_json() or {}
        work_type = data.get('work_type', '产品需求')
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({"code": 400, "status": "error", "message": "工号和密码不能为空", "data": []})

        # 将明文密码 Base64 编码，供 batchdataentry.extract_data 解码使用
        encoded_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

        logger.info(f"开始从 RDC 同步数据 - 工作项类型: {work_type}, 工号: {username}")
        from requirement_schedule.batchdataentry import extract_data
        count = extract_data(
            work_type=work_type,
            username=username,
            encrypted_password=encoded_password
        )
        logger.info(f"RDC 数据同步完成，共写入 {count} 条记录")
        return jsonify({"code": 200, "status": "success", "message": f"RDC 数据同步成功，共写入 {count} 条数据", "data": []})
    except ValueError as e:
        # 参数不合法（work_type / team 不在映射表中）
        logger.warning(f"RDC 同步参数错误: {str(e)}")
        return jsonify({"code": 400, "status": "error", "message": f"参数错误: {str(e)}", "data": []})
    except RuntimeError as e:
        # 认证失败 / 网络超时 / 数据库写入失败
        logger.error(f"RDC 数据同步失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"RDC 数据同步失败: {str(e)}", "data": []})
    except Exception as e:
        logger.error(f"RDC 数据同步未知异常: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"RDC 数据同步失败: {str(e)}", "data": []})


def autoScheduling():
    """
    需求自动排期 - 调用完整流程：PR排序→工作量评估→PR采纳评估→自动排期
    ---
    tags:
      - 需求排期助手
    description: 需求自动排期
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [requirement_preplanning, work_type, username, password]
          properties:
            requirement_preplanning:
              type: string
              description: 需求预规划（必填）
            work_type:
              type: string
              description: 工作项类型（必填）
            domain:
              type: array
              description: 领域列表（可选，多选）
            team:
              type: array
              description: 团队列表（可选）
            username:
              type: string
              description: 用户名/工号（必填）
            password:
              type: string
              description: 密码（必填，明文，后端自动Base64编码）
    responses:
      200:
        description: 成功返回数据
    """
    import base64 as _b64
    try:
        data = request.get_json() or {}
        requirement_preplanning = data.get('requirement_preplanning', '')
        work_type = data.get('work_type', '')
        domain = data.get('domain', [])
        team = data.get('team', [])
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        print("=" * 80)
        print("[autoScheduling] 接收到请求参数:")
        print(f"  - requirement_preplanning: {requirement_preplanning}")
        print(f"  - work_type: {work_type}")
        print(f"  - domain: {domain}")
        print(f"  - team: {team}")
        print(f"  - username: {username}")
        print(f"  - password: {'***' if password else '(空)'}")
        print("=" * 80)

        if not requirement_preplanning:
            print(f"[autoScheduling] ERROR: 需求预规划为空")
            return jsonify({"code": 400, "status": "error", "message": "需求预规划不能为空", "data": []})
        if not work_type:
            print(f"[autoScheduling] ERROR: 工作项类型为空")
            return jsonify({"code": 400, "status": "error", "message": "工作项类型不能为空", "data": []})
        if not username:
            print(f"[autoScheduling] ERROR: 用户名为空")
            return jsonify({"code": 400, "status": "error", "message": "用户名不能为空", "data": []})
        if not password:
            print(f"[autoScheduling] ERROR: 密码为空")
            return jsonify({"code": 400, "status": "error", "message": "密码不能为空", "data": []})

        # 确保 domain/team 为列表类型
        if isinstance(domain, str):
            domain = [domain] if domain else []
        if isinstance(team, str):
            team = [team] if team else []

        # 将明文密码 Base64 编码，与 auto_scheduling_process.base64_encode 逻辑一致
        encrypted_password = _b64.b64encode(password.encode('utf-8')).decode('utf-8')

        print(f"[autoScheduling] 参数校验通过，domain(列表): {domain}, team(列表): {team}")
        print(f"[autoScheduling] 密码已Base64编码，长度: {len(encrypted_password)}")

        logger.info(f"开始需求自动排期 - 需求预规划: {requirement_preplanning}, 工作项类型: {work_type}, 领域: {domain}, 团队: {team}, 用户: {username}")

        from requirement_schedule.auto_scheduling_process import pr_sort, update_db_data, task_assignment, PR_allocate

        # Step 1: PR优先级排序
        print(f"[autoScheduling] Step 1/4: 开始PR优先级排序...")
        pr_sort(team, domain, requirement_preplanning, work_type)
        print(f"[autoScheduling] Step 1/4: PR排序已完成 ✅")
        logger.info("需求自动排期 - PR排序已完成")

        # Step 2: PR预计开发工作量评估
        print(f"[autoScheduling] Step 2/4: 开始工作量评估...")
        update_db_data(team, domain, requirement_preplanning, work_type)
        print(f"[autoScheduling] Step 2/4: 工作量评估已完成 ✅")
        logger.info("需求自动排期 - 工作量评估已完成")

        # Step 3: 评估PR是否可纳入（第一次评估）
        print(f"[autoScheduling] Step 3/4: 开始PR采纳评估...")
        task_assignment(team, domain, requirement_preplanning, work_type, username, encrypted_password)
        print(f"[autoScheduling] Step 3/4: PR采纳评估已完成 ✅")
        logger.info("需求自动排期 - PR采纳评估已完成")

        # Step 4: PR开发日期自动排期
        print(f"[autoScheduling] Step 4/4: 开始自动排期...")
        PR_allocate(team, domain, requirement_preplanning, work_type, username, encrypted_password)
        print(f"[autoScheduling] Step 4/4: 自动排期已完成 ✅")
        logger.info("需求自动排期 - 自动排期已完成")

        print("=" * 80)
        print(f"[autoScheduling] 全部流程执行成功！")
        print("=" * 80)

        return jsonify({"code": 200, "status": "success", "message": "需求自动排期执行成功", "data": []})
    except Exception as e:
        print("=" * 80)
        print(f"[autoScheduling] 执行失败: {str(e)}")
        print("=" * 80)
        logger.error(f"需求自动排期失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"需求自动排期失败: {str(e)}", "data": []})


def previewBackfillRdcData():
    """
    预览待回填到 RDC 的需求数量（不执行回填操作）
    ---
    tags:
      - 需求排期助手
    description: 预览待回填到 RDC 的需求数量
    """
    try:
        data = request.get_json(silent=True) or {}

        query_params = {
            "requirement_preplanning": (data.get("requirement_preplanning") or "").strip(),
            "work_type": (data.get("work_type") or "").strip(),
            "domain": (data.get("domain") or "").strip(),
            "team": (data.get("team") or "").strip(),
        }

        from requirement_schedule.returnRDC import preview_backfill_count

        result = preview_backfill_count(params=query_params)

        if result.get('status') == 'success':
            return jsonify({
                "code": 200,
                "status": "success",
                "message": result.get('message', '统计完成'),
                "data": {"count": result.get('count', 0)}
            })
        else:
            return jsonify({
                "code": 500,
                "status": "error",
                "message": result.get('message', '统计失败'),
                "data": {"count": 0}
            })
    except Exception as e:
        logger.error(f"预览回填统计失败：{str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"预览回填统计失败：{str(e)}", "data": {"count": 0}})


def backfillRdcData():
    """
    将 requirement_schedule_table 中的排期结果回填到 RDC（调用 returnRDC.backfill_RDC_data）
    ---
    tags:
      - 需求排期助手
    description: 数据回填到 RDC
    """
    try:
        import base64
        data = request.get_json(silent=True) or {}
        
        # 优先使用请求体中的 username，如果没有则使用请求头中的 X-Emp-No
        employ_no = (data.get('username') or '').strip()
        if not employ_no:
            employ_no = request.headers.get('X-Emp-No', '')
        
        if not employ_no:
            return jsonify({"code": 400, "status": "error", "message": "工号不能为空", "data": []})
        
        password = data.get('password', '')
        if password:
            password = password.strip()
        
        # 兼容：允许直接传入 encrypted_password（Base64 字符串）
        encrypted_password = data.get('encrypted_password', '')
        if encrypted_password:
            encrypted_password = encrypted_password.strip()
        
        if password and not encrypted_password:
            encrypted_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        
        if not encrypted_password:
            return jsonify({"code": 400, "status": "error", "message": "密码不能为空", "data": []})

        query_params = {
            "requirement_preplanning": (data.get("requirement_preplanning") or "").strip(),
            "work_type": (data.get("work_type") or "").strip(),
            "domain": (data.get("domain") or "").strip(),
            "team": (data.get("team") or "").strip(),
        }

        from requirement_schedule.returnRDC import backfill_RDC_data

        result = backfill_RDC_data(employ_no=employ_no, encrypted_password=encrypted_password, params=query_params)

        if result.get('status') == 'success':
            return jsonify({"code": 200, "status": "success", "message": result.get('message', 'RDC 数据回填成功'), "data": []})
        else:
            return jsonify({"code": 500, "status": "error", "message": result.get('message', 'RDC 数据回填失败'), "data": []})
    except Exception as e:
        logger.error(f"RDC 数据回填失败：{str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"RDC 数据回填失败：{str(e)}", "data": []})


def checkEditPermission():
    """
    检查用户是否有编辑权限
    ---
    tags:
      - 需求排期助手
    description: 检查用户是否有编辑权限
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
    """
    try:
        employ_no = request.headers.get('X-Emp-No', '')
        # TODO: 根据工号获取用户角色，然后查询权限表
        # 这里暂时返回True，实际应该查询REQUIREMENT_SCHEDULE_PERMISSION_TABLE
        # 假设有权限
        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": {"can_edit": True}})
    except Exception as e:
        logger.error(f"检查编辑权限失败: {str(e)}")
        return jsonify({"code": 400, "status": "error", "message": f"获取失败: {str(e)}", "data": {"can_edit": False}})
