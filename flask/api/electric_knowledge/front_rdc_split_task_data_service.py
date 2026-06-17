import logging

from datetime import datetime
from sqlalchemy import insert, update

from electric_knowledge.data_model import db, RDC_SPLIT_TASK_TABLE


logger = logging.getLogger("Logger")


def query_task_info_dict_by_task_id(task_id):
    """
    根据task_id 查询单条 RDC 拆分任务信息
    """
    try:
        obj_model = db.session.query(RDC_SPLIT_TASK_TABLE).filter(RDC_SPLIT_TASK_TABLE.task_id == task_id).first()
        if not obj_model:
            return None
        return obj_model.to_dict()
    except Exception as e:
        logger.error(f"查询任务失败：{str(e)}")
        return None


def add_task_info_dict(task_id, task_info_dict):
    """
    添加 RDC 拆分任务记录
    """
    try:
        # 检查任务 ID 是否已存在
        obj_model = db.session.query(RDC_SPLIT_TASK_TABLE).filter(RDC_SPLIT_TASK_TABLE.task_id == task_id).first()
        if obj_model:
            logger.warning(f"任务 ID {task_id} 已存在")
            return False
        insert_sql = insert(RDC_SPLIT_TASK_TABLE).values(
            task_id=task_id,
            employ_no=task_info_dict.get("employ_no"),
            employ_name=task_info_dict.get("employ_name"),
            task_start_time=task_info_dict.get("task_start_time"),
            task_type=task_info_dict.get("task_type"),
            task_param=task_info_dict.get("task_param"),
            task_status=task_info_dict.get("task_status"),
        )
        db.session.execute(insert_sql)
        db.session.commit()
        logger.info(f"创建任务成功：{task_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建任务失败：{str(e)}")
        return False


def update_task_info_dict(task_id, task_info_dict):
    """
    根据 task_id 和字典更新 RDC 拆分任务记录

    特殊处理：
    - task_err_reason: 累加模式，将新值与原有值去重后合并（用逗号分隔）
    - task_result: 根据 task_err_reason 自动计算（无论是否传入 task_err_reason 都会更新）
      - 如果 task_err_reason 有值（非空），则 task_result 为 "failed"
      - 如果 task_err_reason 无值（空或 None），则 task_result 为 "success"
    """
    try:
        # 检查任务是否存在
        existing_task = db.session.query(RDC_SPLIT_TASK_TABLE).filter(RDC_SPLIT_TASK_TABLE.task_id == task_id).first()
        if not existing_task:
            logger.warning(f"任务 ID {task_id} 不存在")
            return False
        # 过滤出有效的更新字段，只更新 task_info_dict 中存在且对应表字段的键
        update_value_dict = {}
        for key, value in task_info_dict.items():
            if key != 'task_id' and hasattr(existing_task, key):
                update_value_dict[key] = value
        # 特殊处理 task_err_reason：累加模式，去重合并
        if 'task_err_reason' in update_value_dict:
            new_err_reason = update_value_dict['task_err_reason']
            old_err_reason = existing_task.task_err_reason
            if new_err_reason:
                if old_err_reason:
                    # 将原有值和新值合并，去重
                    old_items = set(old_err_reason.split(',')) if old_err_reason else set()
                    new_items = set(new_err_reason.split(',')) if new_err_reason else set()
                    merged_items = old_items | new_items  # 并集去重
                    # 过滤空字符串
                    merged_items = {item.strip() for item in merged_items if item.strip()}
                    update_value_dict['task_err_reason'] = ','.join(sorted(merged_items))
                else:
                    # 原有值为空，直接使用新值（去除空项）
                    new_items = [item.strip() for item in new_err_reason.split(',') if item.strip()]
                    update_value_dict['task_err_reason'] = ','.join(new_items)
        # 始终根据 task_err_reason 设置 task_result
        # 优先使用更新后的 task_err_reason，如果没有则使用数据库中的现有值
        final_err_reason = update_value_dict.get('task_err_reason', existing_task.task_err_reason)
        if final_err_reason:
            update_value_dict['task_result'] = 'failed'
        else:
            update_value_dict['task_result'] = 'success'
        if not update_value_dict:
            logger.warning(f"没有有效的更新字段")
            return False
        update_sql = update(RDC_SPLIT_TASK_TABLE).where(RDC_SPLIT_TASK_TABLE.task_id == task_id).values(**update_value_dict)
        db.session.execute(update_sql)
        db.session.commit()
        logger.info(f"更新任务成功：{task_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新任务失败：{str(e)}")
        return False