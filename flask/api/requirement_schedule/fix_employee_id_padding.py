"""
修复数据库中工号未补零的历史数据

此脚本用于修复以下两个表中的工号数据：
1. person_skill_map - 人员技能地图表
2. requirement_dev_human_resource - 需求开发投入人力设置表

工号规则：纯数字且少于8位的工号，前面补零到8位
例如：103229 -> 00103229

使用方法（在 flask/api 目录下执行）：
    cd flask/api
    python -c "from requirement_schedule.fix_employee_id_padding import main; main()"

    或者：
    cd flask/api
    python -m requirement_schedule.fix_employee_id_padding

注意：执行前请先备份数据库！
"""

import sys
import os
import logging

# 确保在 flask/api 目录下运行
# 将 flask/api 添加到 sys.path 的最前面，保证优先导入
_api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    employee_id = str(employee_id).strip()
    if employee_id.isdigit() and len(employee_id) < 8:
        return employee_id.zfill(8)
    return employee_id


def fix_person_skill_map(db, PERSON_SKILL_MAP):
    """
    修复 person_skill_map 表中未补零的工号
    """
    logger.info("=" * 60)
    logger.info("开始修复 person_skill_map 表...")
    
    try:
        records = db.session.query(PERSON_SKILL_MAP).all()
        logger.info(f"共查询到 {len(records)} 条记录")
        
        fixed_count = 0
        duplicate_count = 0
        error_count = 0
        
        for record in records:
            original_id = record.employee_id
            if not original_id:
                continue
                
            padded_id = pad_employee_id(original_id)
            
            if padded_id == original_id:
                continue
            
            logger.info(f"发现需要补零的工号: {original_id} -> {padded_id}")
            
            # 检查补零后的工号是否已存在
            existing = db.session.query(PERSON_SKILL_MAP).filter(
                PERSON_SKILL_MAP.employee_id == padded_id,
                PERSON_SKILL_MAP.id != record.id
            ).first()
            
            if existing:
                logger.warning(f"工号 {padded_id} 已存在（ID: {existing.id}），跳过记录 ID: {record.id}")
                duplicate_count += 1
                continue
            
            try:
                record.employee_id = padded_id
                fixed_count += 1
                logger.info(f"已修复: ID={record.id}, {original_id} -> {padded_id}")
            except Exception as e:
                logger.error(f"修复失败: ID={record.id}, 错误: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        logger.info("-" * 40)
        logger.info(f"person_skill_map 修复完成:")
        logger.info(f"  - 修复记录数: {fixed_count}")
        logger.info(f"  - 重复跳过数: {duplicate_count}")
        logger.info(f"  - 错误数: {error_count}")
        
        return fixed_count, duplicate_count, error_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"修复 person_skill_map 失败: {str(e)}", exc_info=True)
        raise


def fix_requirement_dev_human_resource(db, REQUIREMENT_DEV_HUMAN_RESOURCE):
    """
    修复 requirement_dev_human_resource 表中未补零的工号
    """
    logger.info("=" * 60)
    logger.info("开始修复 requirement_dev_human_resource 表...")
    
    try:
        records = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE).all()
        logger.info(f"共查询到 {len(records)} 条记录")
        
        fixed_count = 0
        error_count = 0
        
        for record in records:
            original_id = record.employee_id
            if not original_id:
                continue
                
            padded_id = pad_employee_id(original_id)
            
            if padded_id == original_id:
                continue
            
            logger.info(f"发现需要补零的工号: {original_id} -> {padded_id}")
            
            try:
                record.employee_id = padded_id
                fixed_count += 1
                logger.info(f"已修复: ID={record.id}, {original_id} -> {padded_id}")
            except Exception as e:
                logger.error(f"修复失败: ID={record.id}, 错误: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        logger.info("-" * 40)
        logger.info(f"requirement_dev_human_resource 修复完成:")
        logger.info(f"  - 修复记录数: {fixed_count}")
        logger.info(f"  - 错误数: {error_count}")
        
        return fixed_count, 0, error_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"修复 requirement_dev_human_resource 失败: {str(e)}", exc_info=True)
        raise


def verify_fix(db, PERSON_SKILL_MAP, REQUIREMENT_DEV_HUMAN_RESOURCE):
    """
    验证修复结果：检查是否还有未补零的工号
    """
    logger.info("=" * 60)
    logger.info("验证修复结果...")
    
    psm_records = db.session.query(PERSON_SKILL_MAP).all()
    psm_unfixed = []
    for record in psm_records:
        if record.employee_id:
            padded = pad_employee_id(record.employee_id)
            if padded != record.employee_id:
                psm_unfixed.append((record.id, record.employee_id, padded))
    
    rdhr_records = db.session.query(REQUIREMENT_DEV_HUMAN_RESOURCE).all()
    rdhr_unfixed = []
    for record in rdhr_records:
        if record.employee_id:
            padded = pad_employee_id(record.employee_id)
            if padded != record.employee_id:
                rdhr_unfixed.append((record.id, record.employee_id, padded))
    
    logger.info("-" * 40)
    if psm_unfixed:
        logger.warning(f"person_skill_map 仍有 {len(psm_unfixed)} 条未补零记录:")
        for item in psm_unfixed[:10]:
            logger.warning(f"  ID={item[0]}: {item[1]} (应为 {item[2]})")
        if len(psm_unfixed) > 10:
            logger.warning(f"  ... 还有 {len(psm_unfixed) - 10} 条")
    else:
        logger.info("person_skill_map: 所有工号已正确补零")
    
    if rdhr_unfixed:
        logger.warning(f"requirement_dev_human_resource 仍有 {len(rdhr_unfixed)} 条未补零记录:")
        for item in rdhr_unfixed[:10]:
            logger.warning(f"  ID={item[0]}: {item[1]} (应为 {item[2]})")
        if len(rdhr_unfixed) > 10:
            logger.warning(f"  ... 还有 {len(rdhr_unfixed) - 10} 条")
    else:
        logger.info("requirement_dev_human_resource: 所有工号已正确补零")
    
    return len(psm_unfixed) == 0 and len(rdhr_unfixed) == 0


def main():
    """
    主函数：在 Flask 应用上下文中执行修复
    """
    logger.info("=" * 60)
    logger.info("工号补零修复脚本启动")
    logger.info("=" * 60)
    
    # 延迟导入，确保在 flask/api 目录下运行时路径正确
    from app import app
    from requirement_schedule.data_model import db, PERSON_SKILL_MAP, REQUIREMENT_DEV_HUMAN_RESOURCE
    
    with app.app_context():
        try:
            # 修复 person_skill_map
            psm_fixed, psm_dup, psm_err = fix_person_skill_map(db, PERSON_SKILL_MAP)
            
            # 修复 requirement_dev_human_resource
            rdhr_fixed, _, rdhr_err = fix_requirement_dev_human_resource(db, REQUIREMENT_DEV_HUMAN_RESOURCE)
            
            # 验证修复结果
            all_fixed = verify_fix(db, PERSON_SKILL_MAP, REQUIREMENT_DEV_HUMAN_RESOURCE)
            
            logger.info("=" * 60)
            if all_fixed:
                logger.info("所有工号已成功修复！")
            else:
                logger.warning("部分工号未能修复，请检查日志")
            
            logger.info("=" * 60)
            logger.info("修复脚本执行完成")
            
        except Exception as e:
            logger.error(f"脚本执行失败: {str(e)}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
