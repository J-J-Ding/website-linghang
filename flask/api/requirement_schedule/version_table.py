from sqlalchemy import or_, and_
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from requirement_schedule.data_model import db, VERSION_TABLE
from flask import request, jsonify, send_file
import logging
import pandas as pd
import io

logger = logging.getLogger("Logger")


# 定义查询参数模型
class VersionTableData(BaseModel):
    id: Optional[int] = None
    belong_product: Optional[str] = None
    product_roadmap: Optional[str] = None
    requirement_preplanning: Optional[str] = None
    start_dev_date: Optional[str] = None
    finish_dev_date: Optional[str] = None
    achievement_appraisal_date: Optional[str] = None
    cycle_days: Optional[int] = None
    version_status: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


def calculateCycleDays(start_date, achievement_appraisal_date):
    """计算周期天数：周期 = 成果鉴定日期 - 启动开发日期"""
    if not start_date or not achievement_appraisal_date:
        return None
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        achievement = datetime.strptime(achievement_appraisal_date, '%Y-%m-%d')
        delta = achievement - start
        return delta.days if delta.days >= 0 else None
    except Exception as e:
        logger.warning(f"计算周期天数失败: {start_date}, {achievement_appraisal_date}, 错误: {str(e)}")
        return None


def queryVersionTableByParams():
    """
    根据条件查询版本视图
    ---
    tags:
      - 版本视图
    description: 根据条件查询版本视图
    parameters:
      - name: belong_product
        in: query
        type: string
        required: false
        description: 所属产品
      - name: product_roadmap
        in: query
        type: string
        required: false
        description: 所属项目
      - name: requirement_preplanning
        in: query
        type: string
        required: false
        description: 需求预规划
    responses:
      200:
        description: 成功返回数据
    """
    try:
        belong_product = request.args.get('belong_product', '').strip()
        product_roadmap = request.args.get('product_roadmap', '').strip()
        requirement_preplanning = request.args.get('requirement_preplanning', '').strip()
        version_status = request.args.get('version_status', '').strip()

        logger.info(f"查询版本视图 - belong_product: {belong_product}, product_roadmap: {product_roadmap}, requirement_preplanning: {requirement_preplanning}, version_status: {version_status}")

        # 构建查询条件
        conditions = [VERSION_TABLE.effective_flag == '1']
        if belong_product:
            conditions.append(VERSION_TABLE.belong_product == belong_product)
        if product_roadmap:
            conditions.append(VERSION_TABLE.product_roadmap == product_roadmap)
        if requirement_preplanning:
            conditions.append(VERSION_TABLE.requirement_preplanning == requirement_preplanning)
        if version_status:
            conditions.append(VERSION_TABLE.version_status == version_status)

        query = db.session.query(VERSION_TABLE)
        if conditions:
            query = query.filter(and_(*conditions))

        results = query.order_by(
            VERSION_TABLE.belong_product,
            VERSION_TABLE.product_roadmap,
            VERSION_TABLE.requirement_preplanning
        ).all()

        data = [item.to_dict() for item in results]
        
        # 计算周期天数（如果未存储）：周期 = 成果鉴定日期 - 启动开发日期
        for item in data:
            if not item.get('cycle_days') and item.get('start_dev_date') and item.get('achievement_appraisal_date'):
                cycle_days = calculateCycleDays(item['start_dev_date'], item['achievement_appraisal_date'])
                if cycle_days is not None:
                    item['cycle_days'] = cycle_days
        
        logger.info(f"查询版本视图成功 - 共 {len(data)} 条记录")
        return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data})
    except Exception as e:
        logger.error(f"查询版本视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"查询失败: {str(e)}", "data": []})


def createVersionTable():
    """
    创建版本视图记录
    ---
    tags:
      - 版本视图
    description: 创建版本视图记录
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [belong_product, product_roadmap, requirement_preplanning]
          properties:
            belong_product:
              type: string
            product_roadmap:
              type: string
            requirement_preplanning:
              type: string
            start_dev_date:
              type: string
            finish_dev_date:
              type: string
            achievement_appraisal_date:
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
        required_fields = ['belong_product', 'product_roadmap', 'requirement_preplanning']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"code": 400, "status": "error", "message": f"{field}不能为空", "data": []})
        
        # 检查唯一性约束
        existing = db.session.query(VERSION_TABLE).filter(
            and_(
                VERSION_TABLE.belong_product == data['belong_product'],
                VERSION_TABLE.product_roadmap == data['product_roadmap'],
                VERSION_TABLE.requirement_preplanning == data['requirement_preplanning'],
                VERSION_TABLE.effective_flag == '1'
            )
        ).first()
        if existing:
            return jsonify({"code": 400, "status": "error", "message": "该组合已存在", "data": []})
        
        # 计算周期天数：周期 = 成果鉴定日期 - 启动开发日期
        cycle_days = None
        if data.get('start_dev_date') and data.get('achievement_appraisal_date'):
            cycle_days = calculateCycleDays(data['start_dev_date'], data['achievement_appraisal_date'])
        
        # 创建新记录
        new_record = VERSION_TABLE(
            belong_product=data['belong_product'],
            product_roadmap=data['product_roadmap'],
            requirement_preplanning=data['requirement_preplanning'],
            start_dev_date=data.get('start_dev_date', ''),
            finish_dev_date=data.get('finish_dev_date', ''),
            achievement_appraisal_date=data.get('achievement_appraisal_date', ''),
            cycle_days=cycle_days,
            version_status=data.get('version_status', ''),
            create_time=datetime.now(),
            update_time=datetime.now(),
            operator_person=data.get('operator_person', ''),
            effective_flag='1'
        )
        
        db.session.add(new_record)
        db.session.commit()
        
        logger.info(f"创建版本视图记录成功 - belong_product: {data['belong_product']}, product_roadmap: {data['product_roadmap']}")
        return jsonify({"code": 200, "status": "success", "message": "创建成功", "data": new_record.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建版本视图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"创建失败: {str(e)}", "data": []})


def updateVersionTable():
    """
    更新版本视图记录
    ---
    tags:
      - 版本视图
    description: 更新版本视图记录（支持单个和批量）
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
              description: 版本视图数据数组
    responses:
      200:
        description: 成功返回数据
    """
    try:
        data = request.get_json()
        version_list = data.get('data', [])

        if not version_list:
            return jsonify({"code": 400, "status": "error", "message": "数据不能为空", "data": []})

        updated_count = 0
        for version_data in version_list:
            version_id = version_data.get('id')
            if not version_id:
                continue

            # 构建更新数据
            update_data = {}
            if 'belong_product' in version_data:
                update_data['belong_product'] = version_data['belong_product']
            if 'product_roadmap' in version_data:
                update_data['product_roadmap'] = version_data['product_roadmap']
            if 'requirement_preplanning' in version_data:
                update_data['requirement_preplanning'] = version_data['requirement_preplanning']
            if 'start_dev_date' in version_data:
                update_data['start_dev_date'] = version_data['start_dev_date']
            if 'finish_dev_date' in version_data:
                update_data['finish_dev_date'] = version_data['finish_dev_date']
            if 'achievement_appraisal_date' in version_data:
                update_data['achievement_appraisal_date'] = version_data['achievement_appraisal_date']
            
            # 如果日期字段有更新，重新计算周期天数：周期 = 成果鉴定日期 - 启动开发日期
            if 'start_dev_date' in update_data or 'achievement_appraisal_date' in update_data:
                start_date = update_data.get('start_dev_date') or version_data.get('start_dev_date')
                achievement_date = update_data.get('achievement_appraisal_date') or version_data.get('achievement_appraisal_date')
                if start_date and achievement_date:
                    cycle_days = calculateCycleDays(start_date, achievement_date)
                    if cycle_days is not None:
                        update_data['cycle_days'] = cycle_days
                elif 'start_dev_date' in update_data or 'achievement_appraisal_date' in update_data:
                    update_data['cycle_days'] = None

            if 'version_status' in version_data:
                update_data['version_status'] = version_data['version_status']
            if 'operator_person' in version_data:
                update_data['operator_person'] = version_data['operator_person']
            
            update_data['update_time'] = datetime.now()

            if update_data:
                db.session.query(VERSION_TABLE) \
                    .filter(VERSION_TABLE.id == version_id) \
                    .update(update_data)
                updated_count += 1

        db.session.commit()
        logger.info(f"更新版本视图记录成功 - 共更新 {updated_count} 条记录")
        return jsonify({"code": 200, "status": "success", "message": f"成功更新 {updated_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新版本视图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"更新失败: {str(e)}", "data": []})


def deleteVersionTable():
    """
    删除版本视图记录
    ---
    tags:
      - 版本视图
    description: 删除版本视图记录（支持单个和批量，逻辑删除）
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
        
        deleted_count = db.session.query(VERSION_TABLE) \
            .filter(VERSION_TABLE.id.in_(ids)) \
            .update({
                'effective_flag': '0',
                'update_time': datetime.now()
            }, synchronize_session=False)
        
        db.session.commit()
        logger.info(f"删除版本视图记录成功 - 共删除 {deleted_count} 条记录")
        return jsonify({"code": 200, "status": "success", "message": f"成功删除 {deleted_count} 条记录", "data": []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除版本视图记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"删除失败: {str(e)}", "data": []})


def getVersionTableOptions():
    """
    获取版本视图的筛选选项
    ---
    tags:
      - 版本视图
    description: 获取所属产品、所属项目、需求预规划的选项列表
    parameters:
      - name: option_type
        in: query
        type: string
        required: true
        description: 选项类型 (belong_product, product_roadmap, requirement_preplanning)
    responses:
      200:
        description: 成功返回数据
    """
    try:
        option_type = request.args.get('option_type', '').strip()
        if not option_type:
            return jsonify({"code": 400, "status": "error", "message": "option_type参数不能为空", "data": []})

        logger.info(f"获取版本视图选项 - option_type: {option_type}")

        column_map = {
            'belong_product': VERSION_TABLE.belong_product,
            'product_roadmap': VERSION_TABLE.product_roadmap,
            'requirement_preplanning': VERSION_TABLE.requirement_preplanning,
            'version_status': VERSION_TABLE.version_status,
        }

        column_field = column_map.get(option_type)
        if not column_field:
            return jsonify({"code": 400, "status": "error", "message": f"不支持的option_type: {option_type}", "data": []})

        try:
            results = db.session.query(column_field) \
                .filter(
                    and_(
                        column_field.isnot(None),
                        column_field != '',
                        VERSION_TABLE.effective_flag == '1'
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
        logger.error(f"获取版本视图选项失败 - option_type: {option_type}, 错误: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"获取失败: {str(e)}", "data": []})


def importVersionTable():
    """
    批量导入版本视图
    ---
    tags:
      - 版本视图
    description: 批量导入版本视图（Excel文件）
    consumes:
      - multipart/form-data
    parameters:
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
        required_columns = ['所属产品', '所属项目', '需求预规划']
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
        
        # 辅助函数：统一处理空值
        def normalize_value(value):
            """将None、空字符串统一处理为空字符串"""
            if value is None:
                return ''
            return str(value).strip() if str(value).strip() else ''
        
        # 辅助函数：比较两个值是否相同
        def values_equal(val1, val2):
            """比较两个值是否相同，统一处理空值"""
            val1_normalized = normalize_value(val1)
            val2_normalized = normalize_value(val2)
            return val1_normalized == val2_normalized
        
        for index, row in df.iterrows():
            try:
                # 读取并处理字段值
                belong_product = normalize_value(row['所属产品']) if pd.notna(row['所属产品']) else ''
                product_roadmap = normalize_value(row['所属项目']) if pd.notna(row['所属项目']) else ''
                requirement_preplanning = normalize_value(row['需求预规划']) if pd.notna(row['需求预规划']) else ''
                start_dev_date = normalize_value(row['启动开发日期']) if '启动开发日期' in df.columns and pd.notna(row.get('启动开发日期')) else ''
                finish_dev_date = normalize_value(row['完成开发日期']) if '完成开发日期' in df.columns and pd.notna(row.get('完成开发日期')) else ''
                achievement_appraisal_date = normalize_value(row['成果鉴定日期']) if '成果鉴定日期' in df.columns and pd.notna(row.get('成果鉴定日期')) else ''
                version_status = normalize_value(row['版本状态']) if '版本状态' in df.columns and pd.notna(row.get('版本状态')) else ''
                
                # 验证必填字段
                if not all([belong_product, product_roadmap, requirement_preplanning]):
                    skipped_count += 1
                    error_messages.append(f"第{index + 2}行：必填字段不能为空")
                    continue
                
                # 计算周期天数
                cycle_days = None
                if start_dev_date and achievement_appraisal_date:
                    cycle_days = calculateCycleDays(start_dev_date, achievement_appraisal_date)
                
                # 检查唯一性约束（按 (belong_product, product_roadmap, requirement_preplanning) 分组去重）
                existing = db.session.query(VERSION_TABLE).filter(
                    and_(
                        VERSION_TABLE.belong_product == belong_product,
                        VERSION_TABLE.product_roadmap == product_roadmap,
                        VERSION_TABLE.requirement_preplanning == requirement_preplanning,
                        VERSION_TABLE.effective_flag == '1'
                    )
                ).first()
                
                if existing:
                    # 比较字段，判断是否有变化
                    fields_changed = (
                        not values_equal(existing.start_dev_date, start_dev_date) or
                        not values_equal(existing.finish_dev_date, finish_dev_date) or
                        not values_equal(existing.achievement_appraisal_date, achievement_appraisal_date) or
                        not values_equal(existing.cycle_days, cycle_days) or
                        not values_equal(existing.version_status, version_status)
                    )
                    
                    if fields_changed:
                        # 有字段变化，更新
                        existing.start_dev_date = start_dev_date
                        existing.finish_dev_date = finish_dev_date
                        existing.achievement_appraisal_date = achievement_appraisal_date
                        existing.cycle_days = cycle_days
                        existing.version_status = version_status
                        existing.update_time = datetime.now()
                        updated_count += 1
                    else:
                        # 所有字段完全相同，跳过
                        skipped_count += 1
                else:
                    # 不存在，创建新记录
                    new_record = VERSION_TABLE(
                        belong_product=belong_product,
                        product_roadmap=product_roadmap,
                        requirement_preplanning=requirement_preplanning,
                        start_dev_date=start_dev_date,
                        finish_dev_date=finish_dev_date,
                        achievement_appraisal_date=achievement_appraisal_date,
                        cycle_days=cycle_days,
                        version_status=version_status,
                        create_time=datetime.now(),
                        update_time=datetime.now(),
                        operator_person='',
                        effective_flag='1'
                    )
                    db.session.add(new_record)
                    inserted_count += 1
                    
            except Exception as e:
                skipped_count += 1
                error_messages.append(f"第{index + 2}行处理失败: {str(e)}")
                logger.error(f"处理第{index + 2}行数据失败: {str(e)}", exc_info=True)
                continue
        
        db.session.commit()
        
        message = f"批量导入完成: 成功新增 {inserted_count} 条, 更新 {updated_count} 条, 跳过 {skipped_count} 条"
        if error_messages:
            message += f"\n错误详情: {'; '.join(error_messages[:10])}"  # 最多显示10条错误
        
        logger.info(f"批量导入版本视图完成 - 新增: {inserted_count}, 更新: {updated_count}, 跳过: {skipped_count}")
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
        logger.error(f"批量导入版本视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 400, "status": "error", "message": f"批量导入失败: {str(e)}", "data": []})


def exportVersionTable():
    """
    批量导出版本视图
    ---
    tags:
      - 版本视图
    description: 批量导出版本视图（Excel文件）
    parameters:
      - name: belong_product
        in: query
        type: string
        required: false
        description: 所属产品筛选条件
      - name: product_roadmap
        in: query
        type: string
        required: false
        description: 所属项目筛选条件
      - name: requirement_preplanning
        in: query
        type: string
        required: false
        description: 需求预规划筛选条件
    responses:
      200:
        description: 成功返回Excel文件
    """
    try:
        belong_product = request.args.get('belong_product', '').strip()
        product_roadmap = request.args.get('product_roadmap', '').strip()
        requirement_preplanning = request.args.get('requirement_preplanning', '').strip()
        version_status = request.args.get('version_status', '').strip()
        
        logger.info(f"导出版本视图 - belong_product: {belong_product}, product_roadmap: {product_roadmap}, requirement_preplanning: {requirement_preplanning}, version_status: {version_status}")
        
        # 构建查询条件
        conditions = [VERSION_TABLE.effective_flag == '1']
        if belong_product:
            conditions.append(VERSION_TABLE.belong_product == belong_product)
        if product_roadmap:
            conditions.append(VERSION_TABLE.product_roadmap == product_roadmap)
        if requirement_preplanning:
            conditions.append(VERSION_TABLE.requirement_preplanning == requirement_preplanning)
        if version_status:
            conditions.append(VERSION_TABLE.version_status == version_status)
        
        query = db.session.query(VERSION_TABLE)
        if conditions:
            query = query.filter(and_(*conditions))
        
        results = query.order_by(
            VERSION_TABLE.belong_product,
            VERSION_TABLE.product_roadmap,
            VERSION_TABLE.requirement_preplanning
        ).all()
        
        # 转换为字典列表
        data_list = []
        for item in results:
            data_list.append({
                '所属产品': item.belong_product or '',
                '所属项目': item.product_roadmap or '',
                '需求预规划': item.requirement_preplanning or '',
                '启动开发日期': item.start_dev_date or '',
                '完成开发日期': item.finish_dev_date or '',
                '成果鉴定日期': item.achievement_appraisal_date or '',
                '周期 (天)': item.cycle_days if item.cycle_days is not None else '',
                '版本状态': item.version_status or ''
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data_list)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='版本视图', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = f"版本视图导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        logger.info(f"导出版本视图成功 - 共 {len(data_list)} 条记录")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"导出版本视图失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "status": "error", "message": f"导出失败: {str(e)}", "data": []})
