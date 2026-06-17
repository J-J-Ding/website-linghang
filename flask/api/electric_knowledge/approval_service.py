# electric_knowledge/approval_service.py
"""
审核服务核心模块
实现完整的审批流程：提交审核、审批操作、状态联动、数据生效
"""

from datetime import datetime
from flask import request, jsonify
from sqlalchemy import and_, update
import importlib
import logging

from electric_knowledge.data_model import (
    db, APPROVAL_CONFIG_TABLE, APPROVAL_LIST_TABLE, APPROVAL_DETAIL_TABLE
)
from electric_knowledge.approval_registry import BIZ_MODULE_REGISTRY, init_approval_config_table
from electric_knowledge.utils_pub import pub_get_employ_name

logger = logging.getLogger("Logger")

# 状态常量
APPROVAL_STATUS_PENDING = 1      # 待审
APPROVAL_STATUS_IN_PROGRESS = 2  # 审核中
APPROVAL_STATUS_APPROVED = 3     # 审核结束-通过
APPROVAL_STATUS_REJECTED = 4     # 审核结束-驳回
APPROVAL_STATUS_WITHDRAWN = 5    # 撤回

# 业务表状态映射（approval_status -> 业务表current_status）
BIZ_STATUS_MAP = {
    'add': {
        APPROVAL_STATUS_PENDING: '审核中-新增',
        APPROVAL_STATUS_IN_PROGRESS: '审核中-新增',
        APPROVAL_STATUS_APPROVED: '正常',
        APPROVAL_STATUS_REJECTED: '正常',
        APPROVAL_STATUS_WITHDRAWN: '正常'
    },
    'update': {
        APPROVAL_STATUS_PENDING: '审核中-修改',
        APPROVAL_STATUS_IN_PROGRESS: '审核中-修改',
        APPROVAL_STATUS_APPROVED: '正常',
        APPROVAL_STATUS_REJECTED: '正常',
        APPROVAL_STATUS_WITHDRAWN: '正常'
    },
    'delete': {
        APPROVAL_STATUS_PENDING: '审核中-删除',
        APPROVAL_STATUS_IN_PROGRESS: '审核中-删除',
        APPROVAL_STATUS_APPROVED: '已删除',
        APPROVAL_STATUS_REJECTED: '正常',
        APPROVAL_STATUS_WITHDRAWN: '正常'
    }
}


class ApprovalService:
    """审批服务核心类"""

    # ========== 业务模块注册机制 ==========

    @staticmethod
    def get_biz_module(biz_type: str):
        """
        动态获取业务模块和Model类
        返回: (module, model_class, config_dict)
        """
        config = BIZ_MODULE_REGISTRY.get(biz_type)
        if not config:
            # 尝试从数据库加载配置
            db_config = db.session.query(APPROVAL_CONFIG_TABLE).filter(
                APPROVAL_CONFIG_TABLE.biz_type == biz_type,
                APPROVAL_CONFIG_TABLE.effective_flag == 'Y'
            ).first()
            if db_config:
                config = {
                    'module_path': db_config.module_path,
                    'model_class_name': db_config.model_class_name,
                    'biz_table_name': db_config.biz_table_name,
                    'default_approver': db_config.default_approver,
                    'need_approval': db_config.need_approval
                }
            else:
                raise ValueError(f"未注册的业务类型: {biz_type}")

        # 动态导入模块
        module = importlib.import_module(config['module_path'])
        model_class = getattr(module, config['model_class_name'])

        return module, model_class, config

    # ========== 状态联动逻辑 ==========

    @staticmethod
    def get_biz_status(change_type: str, approval_status: int) -> str:
        """将审批状态映射为业务表current_status"""
        return BIZ_STATUS_MAP.get(change_type, {}).get(approval_status, '正常')

    @staticmethod
    def sync_biz_status(biz_type: str, biz_id: str, change_type: str, approval_status: int, operator_person:str):
        """
        同步更新业务表的current_status字段
        """
        try:
            module, model_class, config = ApprovalService.get_biz_module(biz_type)
            biz_status = ApprovalService.get_biz_status(change_type, approval_status)

            # 查询业务表记录
            record = db.session.query(model_class).filter(model_class.id == int(biz_id)).first()
            if record and hasattr(record, 'current_status'):
                if operator_person:
                    update_sql = update(model_class).where(and_(model_class.id == int(biz_id), model_class.effective_flag == 'Y'))\
                                                  .values(current_status=biz_status, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                          operator_person=operator_person)
                else:
                    update_sql = update(model_class).where(and_(model_class.id == int(biz_id), model_class.effective_flag == 'Y'))\
                                                  .values(current_status=biz_status, update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                db.session.execute(update_sql)
                db.session.commit()
                logger.info(f"同步业务状态: {biz_type}.{biz_id} -> {biz_status}")
        except Exception as e:
            logger.error(f"同步业务状态失败: {str(e)}")

    # ========== 核心审批方法 ==========

    @staticmethod
    def submit_change(biz_type: str, biz_id: str, change_type: str,
                      new_data: dict, old_data: dict = None, zh_en_name_relation: dict = None,
                      change_reason: str = None, submitter_person: str = None,
                     assigned_persons: str = None, token: str = None):
        """
        提交变更申请
        返回: {'code': int, 'message': str, 'data': dict}
        """
        try:
            # 1. 检查是否已有待审记录
            existing = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.biz_type == biz_type,
                APPROVAL_LIST_TABLE.biz_id == biz_id,
                APPROVAL_LIST_TABLE.biz_id != '',
                APPROVAL_LIST_TABLE.approval_status.in_([APPROVAL_STATUS_PENDING, APPROVAL_STATUS_IN_PROGRESS])
            ).first()

            if existing:
                return {'code': 400, 'message': '该记录已有待审申请，请等待审批完成', 'data': None}

            # 2. 获取业务配置
            module, model_class, config = ApprovalService.get_biz_module(biz_type)

            # 3. 计算差异
            diff_data = ApprovalService._compute_diff(old_data, new_data)

            # 4. 确定审批人
            if not assigned_persons:
                assigned_persons = config.get('default_approver', '')

            # 5. 创建审批记录
            approval_record = APPROVAL_LIST_TABLE(
                biz_type=biz_type,
                biz_id=biz_id,
                change_type=change_type,
                change_reason=change_reason,
                old_data=old_data,
                new_data=new_data,
                diff_data=diff_data,
                zh_en_name_relation=zh_en_name_relation,
                approval_status=APPROVAL_STATUS_PENDING,
                approval_result='',
                submitter_person=submitter_person,
                assigned_persons=assigned_persons,
                current_approver=assigned_persons.split(',')[0] if assigned_persons else '',
                reject_reason='',
                create_time=datetime.now(),
                update_time=datetime.now(),
                token=token
            )
            db.session.add(approval_record)
            db.session.flush()  # 获取ID

            # 6. 同步业务表状态为"审核中"
            if biz_id:
                ApprovalService.sync_biz_status(biz_type, biz_id, change_type, APPROVAL_STATUS_PENDING, submitter_person)

            db.session.commit()
            logger.info(f"提交审批成功: {biz_type}.{biz_id}, record_id={approval_record.id}")

            return {
                'code': 200,
                'message': '提交审批成功',
                'data': {
                    'approval_id': approval_record.id,
                    'approval_status': APPROVAL_STATUS_PENDING
                }
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"提交审批失败: {str(e)}")
            return {'code': 500, 'message': f'提交审批失败: {str(e)}', 'data': None}

    @staticmethod
    def batch_approve(record_ids: list, approval_person: str, action: str,
                      comment: str = None, reject_reason: str = None):
        """
        批量审批
        action: approve/reject
        """
        results = []
        success_count = 0
        for record_id in record_ids:
            result = ApprovalService.single_approve(
                record_id, approval_person, action, comment, reject_reason
            )
            results.append({'record_id': record_id, **result})
            if result.get('code') == 200:
                success_count += 1

        return {
            'code': 200,
            'message': f'批量审批完成，成功{success_count}条',
            'data': {
                'total': len(record_ids),
                'success_count': success_count,
                'results': results
            }
        }

    @staticmethod
    def single_approve(record_id: int, approval_person: str, action: str,
                       comment: str = None, reject_reason: str = None
                       ):
        """
        单条审批
        action: approve/reject
        返回: {'code': int, 'message': str, 'data': dict}
        """
        try:
            # 1. 查询审批记录
            record = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.id == record_id
            ).first()

            if not record:
                return {'code': 404, 'message': '审批记录不存在', 'data': None}

            if record.approval_status not in [APPROVAL_STATUS_PENDING, APPROVAL_STATUS_IN_PROGRESS]:
                return {'code': 400, 'message': '该记录已审批完成或已撤回', 'data': None}

            # 2. 检查审批权限（是否在assigned_persons中）
            if record.assigned_persons:
                approver_list = [p.strip() for p in record.assigned_persons.split(',')]
                if approval_person not in approver_list:
                    return {'code': 403, 'message': '您不是该记录的指定审批人', 'data': None}

            # 3. 执行审批动作
            if action == 'approve':
                # 通过审批
                record.approval_status = APPROVAL_STATUS_APPROVED
                record.approval_result = 'approved'
                record.update_time = datetime.now()

                # 4. 生效变更数据
                ApprovalService._apply_change(record)

                # 5. 同步业务状态为"正常"
                if record.biz_id:
                    ApprovalService.sync_biz_status(record.biz_type, record.biz_id, record.change_type, APPROVAL_STATUS_APPROVED, record.submitter_person)

                message = '审批通过，数据已生效'

            elif action == 'reject':
                # 驳回
                record.approval_status = APPROVAL_STATUS_REJECTED
                record.approval_result = 'rejected'
                record.reject_reason = reject_reason or comment
                record.update_time = datetime.now()

                # 同步业务状态为"正常"（恢复原状态）
                if record.biz_id:
                    ApprovalService.sync_biz_status(record.biz_type, record.biz_id, record.change_type, APPROVAL_STATUS_REJECTED, '')

                message = '审批驳回'

            else:
                return {'code': 400, 'message': '无效的审批动作', 'data': None}

            # 6. 记录审批详情
            detail = APPROVAL_DETAIL_TABLE(
                record_id=record_id,
                approval_person=approval_person,
                action=action,
                comment=comment
            )
            db.session.add(detail)

            db.session.commit()
            logger.info(f"审批完成: record_id={record_id}, action={action}, by={approval_person}")

            return {'code': 200, 'message': message, 'data': record.to_dict()}

        except Exception as e:
            db.session.rollback()
            logger.error(f"审批失败: {str(e)}")
            return {'code': 500, 'message': f'审批失败: {str(e)}', 'data': None}

    @staticmethod
    def revoke(record_id: int, submitter_person: str):
        """
        撤回审批申请（仅提交人可撤回，且状态为待审）
        """
        try:
            record = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.id == record_id
            ).first()

            if not record:
                return {'code': 404, 'message': '审批记录不存在', 'data': None}

            if record.submitter_person != submitter_person:
                return {'code': 403, 'message': '仅提交人可撤回', 'data': None}

            if record.approval_status != APPROVAL_STATUS_PENDING:
                return {'code': 400, 'message': '仅待审状态可撤回', 'data': None}

            # 更新状态
            record.approval_status = APPROVAL_STATUS_WITHDRAWN
            record.approval_result = 'withdrawn'
            record.update_time = datetime.now()

            # 同步业务状态
            if record.biz_id:
                ApprovalService.sync_biz_status(record.biz_type, record.biz_id, record.change_type, APPROVAL_STATUS_WITHDRAWN, '')

            # 记录详情
            detail = APPROVAL_DETAIL_TABLE(
                record_id=record_id,
                approval_person=submitter_person,
                action='withdraw',
                comment='提交人撤回'
            )
            db.session.add(detail)

            db.session.commit()

            return {'code': 200, 'message': '撤回成功', 'data': record.to_dict()}

        except Exception as e:
            db.session.rollback()
            return {'code': 500, 'message': f'撤回失败: {str(e)}', 'data': None}

    @staticmethod
    def get_my_pending(approval_person: str, biz_type: str = None, page: int = 1, size: int = 20):
        """
        获取我待审批的记录列表
        """
        try:
            query = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.assigned_persons.like(f'%{approval_person}%'),
                APPROVAL_LIST_TABLE.approval_status.in_([APPROVAL_STATUS_PENDING,APPROVAL_STATUS_IN_PROGRESS])
            )

            if biz_type:
                query = query.filter(APPROVAL_LIST_TABLE.biz_type == biz_type)

            total = query.count()
            records = query.order_by(APPROVAL_LIST_TABLE.create_time.desc()).offset((page-1)*size).limit(size).all()

            return {
                'code': 200,
                'message': '获取成功',
                'data': {
                    'total': total,
                    'page': page,
                    'size': size,
                    'list': [r.to_dict() for r in records]
                }
            }
        except Exception as e:
            return {'code': 500, 'message': f'获取失败: {str(e)}', 'data': None}

    @staticmethod
    def get_my_submitted(submitter_person: str, approval_status: int = None, page: int = 1, size: int = 20):
        """
        获取我提交的审批记录
        """
        try:
            query = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.submitter_person == submitter_person
            )

            if approval_status:
                query = query.filter(APPROVAL_LIST_TABLE.approval_status == approval_status)

            total = query.count()
            records = query.order_by(APPROVAL_LIST_TABLE.create_time.desc()).offset((page-1)*size).limit(size).all()

            return {
                'code': 200,
                'message': '获取成功',
                'data': {
                    'total': total,
                    'page': page,
                    'size': size,
                    'list': [r.to_dict() for r in records]
                }
            }
        except Exception as e:
            return {'code': 500, 'message': f'获取失败: {str(e)}', 'data': None}

    @staticmethod
    def get_detail(record_id: int):
        """
        获取审批详情（包含审批历史）
        """
        try:
            record = db.session.query(APPROVAL_LIST_TABLE).filter(
                APPROVAL_LIST_TABLE.id == record_id
            ).first()

            if not record:
                return {'code': 404, 'message': '记录不存在', 'data': None}

            # 获取审批详情列表
            details = db.session.query(APPROVAL_DETAIL_TABLE).filter(
                APPROVAL_DETAIL_TABLE.record_id == record_id
            ).order_by(APPROVAL_DETAIL_TABLE.update_time.desc()).all()

            return {
                'code': 200,
                'message': '获取成功',
                'data': {
                    'record': record.to_dict(),
                    'details': [d.to_dict() for d in details]
                }
            }
        except Exception as e:
            return {'code': 500, 'message': f'获取失败: {str(e)}', 'data': None}

    @staticmethod
    def admin_list(biz_type: str = None, approval_status: int = None,
                   submitter: str = None, page: int = 1, size: int = 20):
        """
        管理员查询审批列表
        """
        try:
            query = db.session.query(APPROVAL_LIST_TABLE)

            if biz_type:
                query = query.filter(APPROVAL_LIST_TABLE.biz_type == biz_type)
            if approval_status:
                query = query.filter(APPROVAL_LIST_TABLE.approval_status == approval_status)
            if submitter:
                query = query.filter(APPROVAL_LIST_TABLE.submitter_person == submitter)

            total = query.count()
            records = query.order_by(APPROVAL_LIST_TABLE.create_time.desc()).offset((page-1)*size).limit(size).all()

            return {
                'code': 200,
                'message': '获取成功',
                'data': {
                    'total': total,
                    'page': page,
                    'size': size,
                    'list': [r.to_dict() for r in records]
                }
            }
        except Exception as e:
            return {'code': 500, 'message': f'获取失败: {str(e)}', 'data': None}

    @staticmethod
    def get_biz_config_list():
        """
        获取业务配置列表
        """
        try:
            configs = db.session.query(APPROVAL_CONFIG_TABLE).filter(
                APPROVAL_CONFIG_TABLE.effective_flag == 'Y'
            ).all()

            return {
                'code': 200,
                'message': '获取成功',
                'data': [{
                    'biz_type': c.biz_type,
                    'need_approval': c.need_approval,
                    'approval_flow_type': c.approval_flow_type,
                    'default_approver': c.default_approver,
                    'admin_persons': c.admin_persons
                } for c in configs]
            }
        except Exception as e:
            return {'code': 500, 'message': f'获取失败: {str(e)}', 'data': None}

    # ========== 内部方法 ==========

    @staticmethod
    def _compute_diff(old_data: dict, new_data: dict) -> dict:
        """
        计算新旧数据的差异
        返回: {'type': str, 'changed_fields': list, 'diff': dict}
        """
        if not old_data and new_data:
            return {'type': 'add', 'new_data': new_data}
        if old_data and not new_data:
            return {'type': 'delete', 'old_data': old_data}

        diff = {}
        changed_fields = []

        # 排除不需要比较的字段
        exclude_fields = ['id', 'create_time', 'update_time', 'effective_flag', 'current_status']

        for key in set(list(old_data.keys()) + list(new_data.keys())):
            if key in exclude_fields:
                continue
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                diff[key] = {'old': old_val, 'new': new_val}
                changed_fields.append(key)

        return {'type': 'update', 'changed_fields': changed_fields, 'diff': diff}

    @staticmethod
    def _apply_change(record: APPROVAL_LIST_TABLE):
        """
        审批通过后，调用业务模块的Src函数生效数据
        """
        biz_type = record.biz_type
        change_type = record.change_type
        new_data = record.new_data
        biz_id = record.biz_id
        submitter_person = record.submitter_person or ''
        submitter_emp_no = submitter_person[-8:]
        token = record.token

        try:
            module, model_class, config = ApprovalService.get_biz_module(biz_type)

            # 根据变更类型调用对应的service函数
            # Src函数签名: addSrc(employ_no, token, body_params), updateSrc(employ_no, body_params), deleteSrc(employ_no, token, featureRelationData)
            if change_type == 'add':
                service_func_name = config.get('service_add', 'addSrcData')
                service_func = getattr(module, service_func_name, None)
                if service_func:
                    result = service_func(submitter_emp_no, token, new_data)
                    logger.info(f"生效新增数据: {biz_type}, result={result}")

            elif change_type == 'update':
                service_func_name = config.get('service_update', 'updateSrcData')
                service_func = getattr(module, service_func_name, None)
                if service_func:
                    # 确保new_data包含id
                    if 'id' not in new_data and biz_id:
                        new_data['id'] = biz_id
                    result = service_func(submitter_emp_no, new_data)
                    logger.info(f"生效更新数据: {biz_type}.{biz_id}, result={result}")

            elif change_type == 'delete':
                service_func_name = config.get('service_delete', 'deleteSrcData')
                service_func = getattr(module, service_func_name, None)
                if service_func:
                    # deleteSrcFeatureRelationData(employ_no, token, featureRelationData)
                    featureRelationData = {'id': biz_id}
                    result = service_func(submitter_emp_no, token, featureRelationData)
                    logger.info(f"生效删除数据: {biz_type}.{biz_id}, result={result}")

        except Exception as e:
            logger.error(f"生效数据失败: {str(e)}")


# ========== API包装函数（用于路由注册）==========

def submit_change():
    """
    提交变更申请
    ---
    tags:
      - 审核服务
    description: 接收POST请求，提交变更申请进入审批流程
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户token，用于身份验证
        required: true
        type: string
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [biz_type, change_type, new_data]
          properties:
            biz_type:
              type: string
              description: 业务类型
            biz_ids:
              type: list
              description: 业务记录ID（新增时可为空）
            change_type:
              type: string
              description: 变更类型（add/update/delete）
            old_datas:
              type: list
              description: 原数据内容（修改/删除时需要）
            new_datas:
              type: list
              description: 新数据内容
            zh_en_name_relation:
              type: object
              description: 前端列的中英文对应关系
            change_reason:
              type: string
              description: 变更原因
            assigned_persons:
              type: string
              description: 指定审批人（多个用逗号分隔）
          example:
            biz_type: "特性-子特性"
            biz_ids: ["123"]
            change_type: "update"
            old_datas: [{"feature_name": "原特性名称"}]
            new_datas: [{"feature_name": "新特性名称"}]
            zh_en_name_relation: {"feature_name": "特性名称"}
            change_reason: "数据更新"
            assigned_persons: "张进朋10305454,罗峰10164361"
    responses:
      200:
        description: 提交审批成功
        examples:
          application/json: {"code": 200, "message": "提交审批成功", "data": {"approval_id": 1, "approval_status": 1}}
      400:
        description: 该记录已有待审申请
        examples:
          application/json: {"code": 400, "message": "该记录已有待审申请，请等待审批完成", "data": null}
      500:
        description: 提交审批失败
        examples:
          application/json: {"code": 500, "message": "提交审批失败: 错误信息", "data": null}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    token = request.headers.get('X-Auth-Value', '')
    submitter_person = pub_get_employ_name(employ_no)
    body = request.get_json()
    biz_ids = body.get('biz_ids', [])
    new_datas = body.get('new_datas', [])
    old_datas = body.get('old_datas', [])
    result = {}
    for index, biz_id in enumerate(biz_ids):
        result = ApprovalService.submit_change(
            biz_type=body.get('biz_type', ''),
            biz_id=biz_id,
            change_type=body.get('change_type', ''),
            new_data=new_datas[index],
            old_data=old_datas[index],
            zh_en_name_relation=body.get('zh_en_name_relation', {}),
            change_reason=body.get('change_reason', ''),
            submitter_person=submitter_person,
            assigned_persons=body.get('assigned_persons', ''),
            token=token
        )

    return jsonify(result)


def batch_approve():
    """
    批量审批
    ---
    tags:
      - 审核服务
    description: 接收POST请求，批量审批多条记录
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [record_ids, action]
          properties:
            record_ids:
              type: array
              description: 审批记录ID列表
              items:
                type: integer
            action:
              type: string
              description: 审批动作（approve/reject）
            comment:
              type: string
              description: 审批意见
            reject_reason:
              type: string
              description: 驳回原因（驳回时使用）
          example:
            record_ids: [1, 2, 3]
            action: "approve"
            comment: "批量审批通过"
            reject_reason: ""
    responses:
      200:
        description: 批量审批完成
        examples:
          application/json: {"code": 200, "message": "批量审批完成，成功3条", "data": {"total": 3, "success_count": 3, "results": []}}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    approval_person = pub_get_employ_name(employ_no)
    body = request.get_json()

    result = ApprovalService.batch_approve(
        record_ids=body.get('record_ids', []),
        approval_person=approval_person,
        action=body.get('action'),
        comment=body.get('comment'),
        reject_reason=body.get('reject_reason')
    )

    return jsonify(result)


def single_approve():
    """
    单条审批
    ---
    tags:
      - 审核服务
    description: 接收POST请求，审批单条记录
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [record_id, action]
          properties:
            record_id:
              type: integer
              description: 审批记录ID
            action:
              type: string
              description: 审批动作（approve/reject）
            comment:
              type: string
              description: 审批意见
            reject_reason:
              type: string
              description: 驳回原因（驳回时使用）
          example:
            record_id: 1
            action: "approve"
            comment: "审批通过"
            reject_reason: ""
    responses:
      200:
        description: 审批成功
        examples:
          application/json: {"code": 200, "message": "审批通过，数据已生效", "data": {}}
      400:
        description: 无效的审批动作或记录已审批完成
        examples:
          application/json: {"code": 400, "message": "该记录已审批完成或已撤回", "data": null}
      403:
        description: 无审批权限
        examples:
          application/json: {"code": 403, "message": "您不是该记录的指定审批人", "data": null}
      404:
        description: 审批记录不存在
        examples:
          application/json: {"code": 404, "message": "审批记录不存在", "data": null}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    approval_person = pub_get_employ_name(employ_no)
    body = request.get_json()

    result = ApprovalService.single_approve(
        record_id=body.get('record_id'),
        approval_person=approval_person,
        action=body.get('action'),
        comment=body.get('comment'),
        reject_reason=body.get('reject_reason', '')
    )

    return jsonify(result)


def revoke():
    """
    撤回审批申请
    ---
    tags:
      - 审核服务
    description: 接收POST请求，撤回已提交的审批申请（仅提交人可撤回，且状态为待审）
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [record_id]
          properties:
            record_id:
              type: integer
              description: 审批记录ID
          example:
            record_id: 1
    responses:
      200:
        description: 撤回成功
        examples:
          application/json: {"code": 200, "message": "撤回成功", "data": {}}
      400:
        description: 仅待审状态可撤回
        examples:
          application/json: {"code": 400, "message": "仅待审状态可撤回", "data": null}
      403:
        description: 仅提交人可撤回
        examples:
          application/json: {"code": 403, "message": "仅提交人可撤回", "data": null}
      404:
        description: 审批记录不存在
        examples:
          application/json: {"code": 404, "message": "审批记录不存在", "data": null}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    submitter_person = pub_get_employ_name(employ_no)
    body = request.get_json()

    result = ApprovalService.revoke(
        record_id=body.get('record_id'),
        submitter_person=submitter_person
    )

    return jsonify(result)


def get_my_pending():
    """
    获取我待审批的记录列表
    ---
    tags:
      - 审核服务
    description: 查询当前用户待审批的记录列表
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: biz_type
        in: query
        description: 业务类型（可选筛选条件）
        required: false
        type: string
      - name: page
        in: query
        description: 页码
        required: false
        type: integer
        default: 1
      - name: size
        in: query
        description: 每页条数
        required: false
        type: integer
        default: 20
    responses:
      200:
        description: 获取成功
        examples:
          application/json: {"code": 200, "message": "获取成功", "data": {"total": 10, "page": 1, "size": 20, "list": []}}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    approval_person = pub_get_employ_name(employ_no)
    biz_type = request.args.get('biz_type')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    result = ApprovalService.get_my_pending(approval_person, biz_type, page, size)
    return jsonify(result)


def get_my_submitted():
    """
    获取我提交的审批记录列表
    ---
    tags:
      - 审核服务
    description: 查询当前用户提交的审批记录列表
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，用于身份验证
        required: true
        type: string
      - name: status
        in: query
        description: 审批状态（1-待审，2-审核中，3-通过，4-驳回，5-撤回）
        required: false
        type: integer
      - name: page
        in: query
        description: 页码
        required: false
        type: integer
        default: 1
      - name: size
        in: query
        description: 每页条数
        required: false
        type: integer
        default: 20
    responses:
      200:
        description: 获取成功
        examples:
          application/json: {"code": 200, "message": "获取成功", "data": {"total": 10, "page": 1, "size": 20, "list": []}}
    """
    employ_no = request.headers.get('X-Emp-No', '')
    submitter_person = pub_get_employ_name(employ_no)
    approval_status = request.args.get('status', type=int)
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    result = ApprovalService.get_my_submitted(submitter_person, approval_status, page, size)
    return jsonify(result)


def get_detail():
    """
    获取审批详情
    ---
    tags:
      - 审核服务
    description: 获取审批记录详情（包含审批历史）
    parameters:
      - name: record_id
        in: query
        description: 审批记录ID
        required: true
        type: integer
    responses:
      200:
        description: 获取成功
        examples:
          application/json: {"code": 200, "message": "获取成功", "data": {"record": {}, "details": []}}
      404:
        description: 记录不存在
        examples:
          application/json: {"code": 404, "message": "记录不存在", "data": null}
    """
    query_params = request.args.to_dict()
    result = ApprovalService.get_detail(query_params.get("record_id", 1))
    return jsonify(result)


def admin_list():
    """
    管理员查询审批列表
    ---
    tags:
      - 审核服务
    description: 管理员查询审批记录列表（支持多条件筛选）
    parameters:
      - name: biz_type
        in: query
        description: 业务类型
        required: false
        type: string
      - name: status
        in: query
        description: 审批状态（1-待审，2-审核中，3-通过，4-驳回，5-撤回）
        required: false
        type: integer
      - name: submitter
        in: query
        description: 提交人姓名
        required: false
        type: string
      - name: page
        in: query
        description: 页码
        required: false
        type: integer
        default: 1
      - name: size
        in: query
        description: 每页条数
        required: false
        type: integer
        default: 20
    responses:
      200:
        description: 获取成功
        examples:
          application/json: {"code": 200, "message": "获取成功", "data": {"total": 100, "page": 1, "size": 20, "list": []}}
    """
    biz_type = request.args.get('biz_type')
    approval_status = request.args.get('status', type=int)
    submitter = request.args.get('submitter')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    result = ApprovalService.admin_list(biz_type, approval_status, submitter, page, size)
    return jsonify(result)


def get_biz_config_list():
    """
    获取业务配置列表
    ---
    tags:
      - 审核服务
    description: 获取所有有效的业务审批配置列表
    responses:
      200:
        description: 获取成功
        examples:
          application/json: {"code": 200, "message": "获取成功", "data": [{"biz_type": "特性-子特性", "need_approval": "Y", "approval_flow_type": "single", "default_approver": "张三", "admin_persons": "张三,李四"}]}
    """
    # 先尝试初始化配置表
    init_approval_config_table()
    result = ApprovalService.get_biz_config_list()
    return jsonify(result)