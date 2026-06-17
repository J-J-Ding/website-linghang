import logging

from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
from electric_knowledge.utils_pub import pub_calculate_ratio, pub_generate_date_range
from electric_knowledge.data_model import db, REQ_MANAGE_BOARD_PR_INFO_TABLE, REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE, REQ_MANAGE_CHECK_PR_INFO_TABLE, REQ_MANAGE_CHECK_PR_SUMMARY_TABLE
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func


logger = logging.getLogger("Logger")
TOTAL_LABEL = "所有"
NULL_DISPLAY = "无"
EMPTY_VALUES = {None, ""}


class ReqManageBoardPrInfoTable(BaseModel):
    id: Optional[int] = None
    system_id: Optional[str] = None  # 基本-需求标识
    system_state: Optional[str] = None  # 基本-状态
    system_createddate: Optional[str] = None  # 基本-需求创建时间
    system_createdby: Optional[str] = None  # 基本-需求创建人
    system_changeddate: Optional[str] = None  # 基本-需求更新时间
    system_changedby: Optional[str] = None  # 基本-需求更新人
    system_appointedto: Optional[str] = None  # 基本-指派给
    system_areapath: Optional[str] = None  # 基本-领域
    team: Optional[str] = None  # 基本-团队
    system_title: Optional[str] = None  # 基本-需求标题
    belongproduct: Optional[str] = None  # 基本-所属产品
    requirementpreplanning: Optional[str] = None  # 基本-需求预规划
    system_description_html: Optional[str] = None  # 基本-描述
    acceptancecriteria_html: Optional[str] = None  # 基本-验收准则
    requirementanalysisowner: Optional[str] = None  # 需求分析-需求分析负责人
    specificationbyexampleurl: Optional[str] = None  # 需求分析-iCenter实例化链接
    specificationbyexamplestate: Optional[str] = None  # 需求分析-需求实例化状态
    designspecificationurl: Optional[str] = None  # 需求分析-方案文档链接
    designstate: Optional[str] = None  # 需求分析-方案状态
    featureurl: Optional[str] = None  # 需求分析-特性内容链接
    belongfeaturecatalog: Optional[str] = None  # 需求分析-所属特性分类
    featureid: Optional[str] = None  # 需求分析-特性标识
    featurename_cn: Optional[str] = None  # 需求分析-特性名称
    checkresultofchipscheme: Optional[str] = None  # 需求分析-特性链接检查结论
    isautocreated: Optional[str] = None  # 需求分析-是否自动拆分
    assessresult_first: Optional[str] = None  # 需求评估-初评结论
    reusedegree: Optional[str] = None  # 需求开发-复用程度
    script_update_date: Optional[str] = None  # 脚本更新日期


def update_req_manage_board_pr_info_table_pr_info_list(pr_info_list):
    UPDATE_FIELD_LIST = [
        "system_state", "system_createddate", "system_createdby", "system_changeddate", "system_changedby", "system_appointedto", "system_areapath", "team",
        "system_title", "belongproduct", "requirementpreplanning", "system_description_html", "acceptancecriteria_html",
        "requirementanalysisowner", "specificationbyexampleurl", "specificationbyexamplestate", "designspecificationurl",
        "designstate", "featureurl", "belongfeaturecatalog", "featureid", "featurename_cn", "checkresultofchipscheme",
        "isautocreated", "assessresult_first", "reusedegree", "script_update_date",
    ]
    try:
        for index, pr_info_item in enumerate(pr_info_list):
            print(index)
            system_id = pr_info_item.get("system_id")
            if system_id is None: continue
            obj_model = db.session.query(REQ_MANAGE_BOARD_PR_INFO_TABLE).filter_by(system_id=system_id).first()
            if obj_model:
                for field in UPDATE_FIELD_LIST:
                    if field in pr_info_item:
                        setattr(obj_model, field, pr_info_item[field])
            else:
                new_data = {"system_id": system_id}
                for field in UPDATE_FIELD_LIST:
                    if field in pr_info_item:
                        new_data[field] = pr_info_item[field]
                new_record = REQ_MANAGE_BOARD_PR_INFO_TABLE(**new_data)
                db.session.add(new_record)
        db.session.commit()
    except Exception as e:
        logger.error(f"An error occurred in update_req_manage_board_pr_info_table_pr_info_list: {e}")
        db.session.rollback()


def del_req_manage_board_pr_info_table_by_script_update_date(script_update_date):
    try:
        deleted_count = db.session.query(REQ_MANAGE_BOARD_PR_INFO_TABLE).filter(REQ_MANAGE_BOARD_PR_INFO_TABLE.script_update_date != script_update_date).delete(synchronize_session=False)
        db.session.commit()
        return deleted_count
    except Exception as e:
        logger.error(f"An error occurred in in del_req_manage_board_pr_info_table_by_script_update_date: {e}")
        db.session.rollback()


def query_req_manage_board_pr_info_table_pr_split_summary_data_list(summary_date):
    # ========== 原有输入校验与条件定义（保持不变）==========
    if not isinstance(summary_date, str):
        logger.error(f"日期参数必须为字符串，当前类型: {type(summary_date)}")
        return []
    try:
        target_date_obj = datetime.strptime(summary_date.strip(), "%Y-%m-%d")
        target_date_str = target_date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        logger.error(f"日期格式无效: '{summary_date}'，应为 'YYYY-MM-DD'。错误: {e}")
        return []
    next_day_start = (target_date_obj + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    # 条件定义（保持原逻辑）
    standard_condition = (REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog == '01-标准')
    special_condition = or_(
        REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog != '01-标准',
        REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog.is_(None)
    )
    auto_condition = (REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated == '1')
    man_condition = or_(
        REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated.is_(None),
        REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated != '1'
    )

    # ========== 执行分组查询（保持不变）==========
    try:
        query = db.session.query(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.requirementpreplanning.label('preplanning'),
            func.count().label('all_all_num'),
            func.sum(case((standard_condition, 1), else_=0)).label('all_standard_num'),
            func.sum(case((special_condition, 1), else_=0)).label('all_special_num'),
            func.sum(case((auto_condition, 1), else_=0)).label('auto_all_num'),
            func.sum(case((auto_condition & standard_condition, 1), else_=0)).label('auto_standard_num'),
            func.sum(case((auto_condition & special_condition, 1), else_=0)).label('auto_special_num'),
            func.sum(case((man_condition, 1), else_=0)).label('man_all_num'),
            func.sum(case((man_condition & standard_condition, 1), else_=0)).label('man_standard_num'),
            func.sum(case((man_condition & special_condition, 1), else_=0)).label('man_special_num')
        ).filter(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate < next_day_start,
            REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate.isnot(None)
        ).group_by(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.requirementpreplanning
        ).order_by(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.requirementpreplanning.is_(None),
            REQ_MANAGE_BOARD_PR_INFO_TABLE.requirementpreplanning
        )
        results = query.all()
        summary_data_list = []
        # 安全转换辅助函数
        def safe_int(value) -> int:
            if value is None:
                return 0
            try:
                return int(float(value))
            except (ValueError, TypeError):
                logger.warning(f"数值转换异常: {value} (类型: {type(value)})")
                return 0
        # ========== 生成分组统计结果 ==========
        for row in results:
            summary = {
                "summary_date": target_date_str,
                "preplanning": row.preplanning,
                "all_all_num": safe_int(row.all_all_num),
                "all_standard_num": safe_int(row.all_standard_num),
                "all_special_num": safe_int(row.all_special_num),
                "auto_all_num": safe_int(row.auto_all_num),
                "auto_standard_num": safe_int(row.auto_standard_num),
                "auto_special_num": safe_int(row.auto_special_num),
                "man_all_num": safe_int(row.man_all_num),
                "man_standard_num": safe_int(row.man_standard_num),
                "man_special_num": safe_int(row.man_special_num)
            }
            summary_data_list.append(summary)
        # ========== 关键增强：生成全局总计行 ==========
        total_summary = {
            "summary_date": target_date_str,
            "preplanning": TOTAL_LABEL,
            "all_all_num": sum(item["all_all_num"] for item in summary_data_list),
            "all_standard_num": sum(item["all_standard_num"] for item in summary_data_list),
            "all_special_num": sum(item["all_special_num"] for item in summary_data_list),
            "auto_all_num": sum(item["auto_all_num"] for item in summary_data_list),
            "auto_standard_num": sum(item["auto_standard_num"] for item in summary_data_list),
            "auto_special_num": sum(item["auto_special_num"] for item in summary_data_list),
            "man_all_num": sum(item["man_all_num"] for item in summary_data_list),
            "man_standard_num": sum(item["man_standard_num"] for item in summary_data_list),
            "man_special_num": sum(item["man_special_num"] for item in summary_data_list)
        }
        summary_data_list.append(total_summary)  # 追加至末尾（符合“分组+总计”阅读习惯）
        # ========== 增强日志：明确分组数与总计值 ==========
        group_count = len(summary_data_list) - 1  # 排除总计行
        logger.info(
            f"统计完成 | 日期: {target_date_str} | "
            f"有效分组数: {group_count} | "
            f"总计需求量: {total_summary['all_all_num']} | "
            f"含总计行: 是"
        )
        # ========== 可选：运行时数据校验（开发环境建议开启）==========
        # 验证总计行逻辑一致性（避免代码逻辑错误）
        if total_summary["all_all_num"] != total_summary["auto_all_num"] + total_summary["man_all_num"]:
            logger.warning(
                f"总计行数据异常: 全量({total_summary['all_all_num']}) ≠ 自动({total_summary['auto_all_num']}) + 手动({total_summary['man_all_num']})"
            )
        if total_summary["all_all_num"] != total_summary["all_standard_num"] + total_summary["all_special_num"]:
            logger.warning(
                f"总计行数据异常: 全量({total_summary['all_all_num']}) ≠ 标准({total_summary['all_standard_num']}) + 特殊({total_summary['all_special_num']})"
            )
        return summary_data_list
    except Exception as e:
        logger.exception(f"数据库统计查询失败 (summary_date={summary_date}): {str(e)}")
        return []


def query_req_manage_board_pr_split_detail_table_table_data_list_by_preplanning_and_date(preplanning, auto_field, standard_field, start_date, end_date):
    """
    查询满足条件的需求信息列表（明细数据）
    参数：
        preplanning: 需求预规划类别，"所有" 表示不限制
        auto_field: 自动/手动维度过滤条件，取值: "auto" | "man" | "all"
        standard_field: 标准/特殊维度过滤条件，取值: "standard" | "special" | "all"
        start_date: 开始日期，格式 YYYY-MM-DD（包含）
        end_date: 结束日期，格式 YYYY-MM-DD（包含）
    返回：
        list[dict]: 满足条件的需求信息字典列表
    """
    # ========== 常量定义 ==========
    VALID_AUTO_VALUES = {"auto", "man", "all"}
    VALID_STANDARD_VALUES = {"standard", "special", "all"}
    # ========== 1. 输入参数基础校验 ==========
    # 1.1 类型校验
    if not all(isinstance(arg, str) for arg in [preplanning, auto_field, standard_field, start_date, end_date]):
        logger.error(
            f"参数类型错误，期望全部为字符串 | "
            f"preplanning:{type(preplanning)}, auto_field:{type(auto_field)}, standard_field:{type(standard_field)}, "
            f"start_date:{type(start_date)}, end_date:{type(end_date)}"
        )
        return []
    # 1.2 枚举值校验
    if auto_field not in VALID_AUTO_VALUES:
        logger.error(f"auto_field 值无效，期望 {VALID_AUTO_VALUES}，实际值: '{auto_field}'")
        return []
    if standard_field not in VALID_STANDARD_VALUES:
        logger.error(f"standard_field 值无效，期望 {VALID_STANDARD_VALUES}，实际值: '{standard_field}'")
        return []
    # ========== 2. 日期解析与时间边界计算 ==========
    try:
        start_date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date.strip(), "%Y-%m-%d")
        # 时间边界：[start_date 00:00:00, end_date+1 00:00:00) 左闭右开
        start_datetime = start_date_obj.strftime("%Y-%m-%d 00:00:00")
        end_datetime = (end_date_obj + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    except ValueError as e:
        logger.error(f"日期格式解析失败: start_date='{start_date}', end_date='{end_date}'，期望 'YYYY-MM-DD'。错误: {e}")
        return []
    # ========== 3. 动态构建 SQLAlchemy 查询条件 ==========
    conditions = []
    # 3.1 预规划类别条件（支持"所有"通配）
    if preplanning != TOTAL_LABEL:
        conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.requirementpreplanning == preplanning)
    # 3.2 创建时间范围条件 [start, end] 闭区间
    conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate >= start_datetime)
    conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate < end_datetime)
    conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate.isnot(None))
    # 3.3 自动/手动维度条件（auto_field 参数）
    if auto_field == 'auto':
        conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated == '1')
    elif auto_field == 'man':
        # 手动 = 非'1' 或 为空，与统计函数逻辑保持一致
        conditions.append(or_(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated.is_(None),
            REQ_MANAGE_BOARD_PR_INFO_TABLE.isautocreated != '1'
        ))
    # auto_field == 'all' 时不添加条件
    # 3.4 标准/特殊维度条件（standard_field 参数）
    if standard_field == 'standard':
        conditions.append(REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog == '01-标准')
    elif standard_field == 'special':
        # 特殊 = 非'01-标准' 或 为空，与统计函数逻辑保持一致
        conditions.append(or_(
            REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog != '01-标准',
            REQ_MANAGE_BOARD_PR_INFO_TABLE.belongfeaturecatalog.is_(None)
        ))
    # standard_field == 'all' 时不添加条件
    # ========== 4. 执行数据库查询 ==========
    try:
        query = db.session.query(REQ_MANAGE_BOARD_PR_INFO_TABLE).filter(*conditions)
        # 添加默认排序：按创建时间倒序升序，便于追踪最新数据
        query = query.order_by(REQ_MANAGE_BOARD_PR_INFO_TABLE.system_createddate.desc())
        results = query.all()
        # ========== 5. 结果转换：模型 -> 字典（便于JSON序列化） ==========
        # ========== 5. 结果转换：模型 -> 字典（便于JSON序列化） ==========
        detail_data_list = []
        EXCLUDE_FIELDS = {"system_description_html", "acceptancecriteria_html"}
        for item in results:
            # 兼容 Pydantic v1/v2 及 SQLAlchemy 原生模型
            if hasattr(item, 'model_dump'):  # Pydantic v2
                item_dict = item.model_dump()
            elif hasattr(item, 'dict'):  # Pydantic v1
                item_dict = item.dict()
            else:  # SQLAlchemy 原生对象
                item_dict = {
                    c.key: getattr(item, c.key) 
                    for c in item.__table__.columns
                }
            # 新增：过滤掉不需要返回的字段
            for field in EXCLUDE_FIELDS:
                item_dict.pop(field, None)  # 使用 pop+default 避免 KeyError
            detail_data_list.append(item_dict)
        # ========== 6. 日志记录与返回 ==========
        logger.info(
            f"明细查询成功 | preplanning: '{preplanning}' | "
            f"auto_field: '{auto_field}' | standard_field: '{standard_field}' | "
            f"时间范围: [{start_date}, {end_date}] | 匹配记录数: {len(detail_data_list)}"
        )
        return detail_data_list
    except Exception as e:
        logger.exception(
            f"明细查询异常 | preplanning: '{preplanning}' | "
            f"auto_field: '{auto_field}' | standard_field: '{standard_field}' | "
            f"时间范围: [{start_date}, {end_date}] | 错误: {str(e)}"
        )
        return []


class ReqManageBoardPrSplitSummaryTable(BaseModel):
    id: Optional[int] = None
    summary_date: Optional[str] = None
    preplanning: Optional[str] = None
    all_all_num: Optional[int] = None
    all_standard_num: Optional[int] = None
    all_special_num: Optional[int] = None
    auto_all_num: Optional[int] = None
    auto_standard_num: Optional[int] = None
    auto_special_num: Optional[int] = None
    man_all_num: Optional[int] = None
    man_standard_num: Optional[int] = None
    man_special_num: Optional[int] = None


def update_req_manage_board_pr_split_summary_table_data_list(data_list):
    try:
        for data_item in data_list:
            summary_date = data_item.get("summary_date")
            preplanning = data_item.get("preplanning")
            obj_model = db.session.query(REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE).filter_by(summary_date=summary_date,preplanning=preplanning).first()
            if obj_model:
                obj_model.all_all_num = data_item.get("all_all_num")
                obj_model.all_standard_num = data_item.get("all_standard_num")
                obj_model.all_special_num = data_item.get("all_special_num")
                obj_model.auto_all_num = data_item.get("auto_all_num")
                obj_model.auto_standard_num = data_item.get("auto_standard_num")
                obj_model.auto_special_num = data_item.get("auto_special_num")
                obj_model.man_all_num = data_item.get("man_all_num")
                obj_model.man_standard_num = data_item.get("man_standard_num")
                obj_model.man_special_num = data_item.get("man_special_num")
            else:
                new_record = REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE(
                    summary_date = summary_date,
                    preplanning = preplanning,
                    all_all_num = data_item.get("all_all_num"),
                    all_standard_num = data_item.get("all_standard_num"),
                    all_special_num = data_item.get("all_special_num"),
                    auto_all_num = data_item.get("auto_all_num"),
                    auto_standard_num = data_item.get("auto_standard_num"),
                    auto_special_num = data_item.get("auto_special_num"),
                    man_all_num = data_item.get("man_all_num"),
                    man_standard_num = data_item.get("man_standard_num"),
                    man_special_num = data_item.get("man_special_num"),
                )
                db.session.add(new_record)
        db.session.commit()
    except Exception as e:
        logger.error(f"An error occurred in update_req_manage_board_pr_split_summary_table_data_list: {e}")
        db.session.rollback()


def query_req_manage_board_pr_split_summary_table_preplanning_list():
    """
    查询表格中 requirementpreplanning 字段所有出现过的不重复值。
    返回格式示例：["预规划 A", "预规划 B", "预规划 C", None]
    """
    try:
        # 使用 distinct() 进行去重查询，只选取 requirementpreplanning 这一列
        results = db.session.query(REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE.preplanning).distinct().all()
        # 将查询结果从 [(val1,), (val2,), ...] 展平为 [val1, val2, ...]
        # item[0] 是因为 query 返回的是元组列表，即使只查一列
        raw_list = [item[0] for item in results]
        preplanning_list = sorted(raw_list, key=lambda x: (x is None, x if x is not None else ""))
        if "所有" in preplanning_list:
            preplanning_list.remove("所有")  # 从原位置删除
            preplanning_list.insert(0, "所有") # 插入到第 0 位（最前面）
        return preplanning_list
    except Exception as e:
        logger.error(f"An error occurred in query_req_manage_board_pr_info_table_preplanning_list: {e}")
        db.session.rollback()
        return []


def query_req_manage_board_pr_split_summary_table_line_data_list_by_preplanning_and_date(preplanning_list, date_list, obj_field_name):
    result = []
    # 1. 批量查询有效数据（过滤None值避免后续key冲突）
    records = db.session.query(REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE).filter(
        REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE.preplanning.in_(preplanning_list),
        REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE.summary_date.in_(date_list)
    ).all()
    # 2. 构建高效查询字典 {(preplanning, date): record}
    record_map = {
        (rec.preplanning, rec.summary_date): rec
        for rec in records
        if rec.preplanning is not None and rec.summary_date is not None
    }
    # 3. 按预规划维度生成时间序列数据
    for preplanning in preplanning_list:
        all_all_num_list = []
        obj_num_list = []
        obj_rate_list = []
        # 初始化“上一个有效值”（用于日期缺失时继承）
        last_all_all = 0
        last_obj_num = 0
        for date in date_list:
            key = (preplanning, date)
            if key in record_map:
                rec = record_map[key]
                # 安全获取字段值：None转0，保留0的有效性
                curr_all = rec.all_all_num if rec.all_all_num is not None else 0
                curr_obj = getattr(rec, obj_field_name, None)
                curr_obj = curr_obj if curr_obj is not None else 0
                # 更新“上一个有效值”
                last_all_all = curr_all
                last_obj_num = curr_obj
            # 追加当前有效值（含继承逻辑）
            all_all_num_list.append(last_all_all)
            obj_num_list.append(last_obj_num)
            # 计算比率（假设pub_calculate_ratio已处理分母为0）
            obj_rate_list.append(pub_calculate_ratio(last_obj_num, last_all_all, True, 2))
        # 4. 拼装结果（修正原代码变量名错误：all_num_list → all_all_num_list）
        result.append({
            "preplanning": preplanning,
            "date_list": date_list,
            "all_all_num_list": all_all_num_list,
            "obj_num_list": obj_num_list,
            "obj_rate_list": obj_rate_list,
        })
    return result


def query_req_manage_board_pr_split_summary_table_table_data_list_by_preplanning_and_date(preplanning_list, start_date, end_date):
    """
    查询指定预规划列表在 [start_date, end_date] 闭区间内的各项数据增量。
    逻辑：Result = Data(end_date) - Data(start_date - 1 day)
    示例：start_date="2024-01-15" → 基准日期="2024-01-14"
          差值 = 截止到 1-31 总量 - 截止到 1-14 总量 = 1-15~1-31 的增量 ✓
    返回格式：列表包含字典，字典结构与 ReqManageBoardPrSplitSummaryTable 一致（数值为差值）
    """

    # 定义需要计算差值的所有数值字段名
    NUM_FIELDS = [
        "all_all_num", "all_standard_num", "all_special_num",
        "auto_all_num", "auto_standard_num", "auto_special_num",
        "man_all_num", "man_standard_num", "man_special_num"
    ]

    result = []

    try:
        # ========== 1. 日期校验与解析 ==========
        if not all(isinstance(d, str) for d in [start_date, end_date]):
            logger.error(f"日期参数必须为字符串 | start_date:{type(start_date)}, end_date:{type(end_date)}")
            return []
        try:
            start_date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date.strip(), "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"日期格式解析失败，期望 'YYYY-MM-DD' | 错误: {e}")
            return []
        # ========== 2. 计算基准日期：start_date 的前一天 ==========
        # 核心修改点：用前一天作为减法基准，确保包含 start_date 当天
        start_date_previous_obj = start_date_obj - timedelta(days=1)
        start_date_previous = start_date_previous_obj.strftime("%Y-%m-%d")
        end_date_str = end_date_obj.strftime("%Y-%m-%d")  # 标准化格式

        # ========== 3. 批量查询数据库 ==========
        # 查询两个关键时间点：基准日期(前一天) 和 结束日期
        target_dates = [start_date_previous, end_date_str]

        records = db.session.query(REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE).filter(
            REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE.preplanning.in_(preplanning_list),
            REQ_MANAGE_BOARD_PR_SPLIT_SUMMARY_TABLE.summary_date.in_(target_dates)
        ).all()

        # ========== 4. 构建 O(1) 查找字典 ==========
        record_map = {
            (rec.preplanning, rec.summary_date): rec
            for rec in records
            if rec.preplanning is not None and rec.summary_date is not None
        }

        # ========== 5. 遍历计算差值 ==========
        for preplanning in preplanning_list:
            # 获取结束日期记录
            rec_end = record_map.get((preplanning, end_date_str))
            # 获取基准日期记录（start_date 的前一天）← 关键修改
            rec_start = record_map.get((preplanning, start_date_previous))

            item_result = {"preplanning": preplanning}

            for field in NUM_FIELDS:
                # 安全获取字段值，None 则视为 0
                val_end = getattr(rec_end, field, None) if rec_end else None
                val_start = getattr(rec_start, field, None) if rec_start else None
                num_end = val_end if val_end is not None else 0
                num_start = val_start if val_start is not None else 0
                item_result[field] = num_end - num_start  # 计算增量
            result.append(item_result)
        # ========== 6. 日志记录 ==========
        logger.info(
            f"增量查询成功 | preplanning_count: {len(preplanning_list)} | "
            f"时间区间: [{start_date}, {end_date}] (基准日期: {start_date_previous}) | "
            f"返回记录数: {len(result)}"
        )
        return result

    except Exception as e:
        logger.exception(
            f"增量查询异常 | preplanning_list: {preplanning_list} | "
            f"时间区间: [{start_date}, {end_date}] | 错误: {str(e)}"
        )
        db.session.rollback()
        return []


class ReqManageCheckPrInfoTable(BaseModel):
    id: Optional[int] = None
    problem_type: Optional[str] = None  # 问题类型
    problem_description: Optional[str] = None  # 问题描述
    check_date: Optional[str] = None  # 检查日期
    default_problem_flag: Optional[str] = None  # 默认是否问题
    default_handle_person: Optional[str] = None  # 默认整改责任人
    default_handle_date: Optional[str] = None  # 默认整改截止日期
    default_handle_flag: Optional[str] = None  # 默认是否已整改
    man_problem_flag: Optional[str] = None  # 人工标注是否问题
    man_handle_person: Optional[str] = None  # 人工标注整改责任人
    man_handle_date: Optional[str] = None  # 人工标注整改截止日期
    man_handle_flag: Optional[str] = None  # 人工标注是否已整改
    cal_problem_flag: Optional[str] = None  # 计算是否问题
    cal_handle_person: Optional[str] = None  # 计算整改责任人
    cal_handle_date: Optional[str] = None  # 计算整改截止日期
    cal_handle_flag: Optional[str] = None  # 计算是否已整改
    actual_handle_date: Optional[str] = None  # 实际整改完成日期
    handle_delay_flag: Optional[str] = None  # 是否达到整改截止日期
    man_update_person: Optional[str] = None  # 人工标注更新人
    man_update_date: Optional[str] = None  # 人工标注更新日期
    system_id: Optional[str] = None  # 基本-需求标识
    system_state: Optional[str] = None  # 基本-状态
    system_createddate: Optional[str] = None  # 基本-需求创建时间
    system_createdby: Optional[str] = None  # 基本-需求创建人
    system_changeddate: Optional[str] = None  # 基本-需求更新时间
    system_changedby: Optional[str] = None  # 基本-需求更新人
    system_appointedto: Optional[str] = None  # 基本-指派给
    system_areapath: Optional[str] = None  # 基本-领域
    team: Optional[str] = None  # 基本-团队
    system_title: Optional[str] = None  # 基本-需求标题
    belongproduct: Optional[str] = None  # 基本-所属产品
    requirementpreplanning: Optional[str] = None  # 基本-需求预规划
    system_description_html: Optional[str] = None  # 基本-描述
    acceptancecriteria_html: Optional[str] = None  # 基本-验收准则
    requirementanalysisowner: Optional[str] = None  # 需求分析-需求分析负责人
    specificationbyexampleurl: Optional[str] = None  # 需求分析-iCenter实例化链接
    specificationbyexamplestate: Optional[str] = None  # 需求分析-需求实例化状态
    designspecificationurl: Optional[str] = None  # 需求分析-方案文档链接
    designstate: Optional[str] = None  # 需求分析-方案状态
    featureurl: Optional[str] = None  # 需求分析-特性内容链接
    belongfeaturecatalog: Optional[str] = None  # 需求分析-所属特性分类
    featureid: Optional[str] = None  # 需求分析-特性标识
    featurename_cn: Optional[str] = None  # 需求分析-特性名称
    checkresultofchipscheme: Optional[str] = None  # 需求分析-特性链接检查结论
    isautocreated: Optional[str] = None  # 需求分析-是否自动拆分
    assessresult_first: Optional[str] = None  # 需求评估-初评结论
    reusedegree: Optional[str] = None  # 需求开发-复用程度
    planstartdateofdevelopment: Optional[str] = None  # 需求评估-计划开始开发日期
    planfinishdateofdevelopment: Optional[str] = None  # 需求评估-计划完成开发日期
    accesscheck: Optional[str] = None  # 需求分析-AI准入检查
    belongreleaseversion: Optional[str] = None  # 基本-发布版本
    ismasterdeliveryarea: Optional[str] = None  # 基本-是否主交付领域
    script_update_date: Optional[str] = None  # 脚本更新日期
    detail_list: Optional[List[Any]] = None


def update_req_manage_check_pr_info_table_check_pr_info_list(data_list):
    try:
        for data_item in data_list:
            problem_type = data_item.get("problem_type")
            system_id = data_item.get("system_id")
            # 使用 problem_type 和 system_id 作为联合唯一键进行查找
            obj_model = db.session.query(REQ_MANAGE_CHECK_PR_INFO_TABLE).filter_by(
                problem_type=problem_type, 
                system_id=system_id
            ).first()
            if obj_model:
                # 找到记录，覆盖更新所有字段
                obj_model.problem_type = data_item.get("problem_type")
                obj_model.problem_description = data_item.get("problem_description")
                obj_model.default_problem_flag = data_item.get("default_problem_flag")
                obj_model.default_handle_person = data_item.get("default_handle_person")
                obj_model.default_handle_date = data_item.get("default_handle_date")
                obj_model.default_handle_flag = data_item.get("default_handle_flag")
                obj_model.actual_handle_date = data_item.get("actual_handle_date")
                obj_model.system_id = data_item.get("system_id")
                obj_model.system_state = data_item.get("system_state")
                obj_model.system_createddate = data_item.get("system_createddate")
                obj_model.system_createdby = data_item.get("system_createdby")
                obj_model.system_changeddate = data_item.get("system_changeddate")
                obj_model.system_changedby = data_item.get("system_changedby")
                obj_model.system_appointedto = data_item.get("system_appointedto")
                obj_model.system_areapath = data_item.get("system_areapath")
                obj_model.team = data_item.get("team")
                obj_model.system_title = data_item.get("system_title")
                obj_model.belongproduct = data_item.get("belongproduct")
                obj_model.requirementpreplanning = data_item.get("requirementpreplanning")
                obj_model.system_description_html = data_item.get("system_description_html")
                obj_model.acceptancecriteria_html = data_item.get("acceptancecriteria_html")
                obj_model.requirementanalysisowner = data_item.get("requirementanalysisowner")
                obj_model.specificationbyexampleurl = data_item.get("specificationbyexampleurl")
                obj_model.specificationbyexamplestate = data_item.get("specificationbyexamplestate")
                obj_model.designspecificationurl = data_item.get("designspecificationurl")
                obj_model.designstate = data_item.get("designstate")
                obj_model.featureurl = data_item.get("featureurl")
                obj_model.belongfeaturecatalog = data_item.get("belongfeaturecatalog")
                obj_model.featureid = data_item.get("featureid")
                obj_model.featurename_cn = data_item.get("featurename_cn")
                obj_model.checkresultofchipscheme = data_item.get("checkresultofchipscheme")
                obj_model.isautocreated = data_item.get("isautocreated")
                obj_model.assessresult_first = data_item.get("assessresult_first")
                obj_model.reusedegree = data_item.get("reusedegree")
                obj_model.planstartdateofdevelopment = data_item.get("planstartdateofdevelopment")
                obj_model.planfinishdateofdevelopment = data_item.get("planfinishdateofdevelopment")
                obj_model.accesscheck = data_item.get("accesscheck")
                obj_model.belongreleaseversion = data_item.get("belongreleaseversion")
                obj_model.ismasterdeliveryarea = data_item.get("ismasterdeliveryarea")
                obj_model.script_update_date = data_item.get("script_update_date")
                obj_model.detail_list = data_item.get("detail_list")
            else:
                # 未找到记录，新建
                new_record = REQ_MANAGE_CHECK_PR_INFO_TABLE(
                    problem_type=data_item.get("problem_type"),
                    problem_description=data_item.get("problem_description"),
                    check_date=data_item.get("check_date"),
                    default_problem_flag=data_item.get("default_problem_flag"),
                    default_handle_person=data_item.get("default_handle_person"),
                    default_handle_date=data_item.get("default_handle_date"),
                    default_handle_flag=data_item.get("default_handle_flag"),
                    actual_handle_date=data_item.get("actual_handle_date"),
                    system_id=data_item.get("system_id"),
                    system_state=data_item.get("system_state"),
                    system_createddate=data_item.get("system_createddate"),
                    system_createdby=data_item.get("system_createdby"),
                    system_changeddate=data_item.get("system_changeddate"),
                    system_changedby=data_item.get("system_changedby"),
                    system_appointedto=data_item.get("system_appointedto"),
                    system_areapath=data_item.get("system_areapath"),
                    team=data_item.get("team"),
                    system_title=data_item.get("system_title"),
                    belongproduct=data_item.get("belongproduct"),
                    requirementpreplanning=data_item.get("requirementpreplanning"),
                    system_description_html=data_item.get("system_description_html"),
                    acceptancecriteria_html=data_item.get("acceptancecriteria_html"),
                    requirementanalysisowner=data_item.get("requirementanalysisowner"),
                    specificationbyexampleurl=data_item.get("specificationbyexampleurl"),
                    specificationbyexamplestate=data_item.get("specificationbyexamplestate"),
                    designspecificationurl=data_item.get("designspecificationurl"),
                    designstate=data_item.get("designstate"),
                    featureurl=data_item.get("featureurl"),
                    belongfeaturecatalog=data_item.get("belongfeaturecatalog"),
                    featureid=data_item.get("featureid"),
                    featurename_cn=data_item.get("featurename_cn"),
                    checkresultofchipscheme=data_item.get("checkresultofchipscheme"),
                    isautocreated=data_item.get("isautocreated"),
                    assessresult_first=data_item.get("assessresult_first"),
                    reusedegree=data_item.get("reusedegree"),
                    planstartdateofdevelopment=data_item.get("planstartdateofdevelopment"),
                    planfinishdateofdevelopment=data_item.get("planfinishdateofdevelopment"),
                    accesscheck=data_item.get("accesscheck"),
                    belongreleaseversion=data_item.get("belongreleaseversion"),
                    ismasterdeliveryarea=data_item.get("ismasterdeliveryarea"),
                    script_update_date=data_item.get("script_update_date"),
                    detail_list=data_item.get("detail_list"),
                )
                db.session.add(new_record)
        db.session.commit()
    except Exception as e:
        logger.error(f"An error occurred in update_req_manage_check_pr_info_table_data_list: {e}")
        db.session.rollback()


def update_req_manage_check_pr_info_table_handle_pr_info_list(script_update_date, handle_date):
    try:
        # 使用 SQLAlchemy 批量 UPDATE，直接在数据库层执行，避免将数据加载到内存
        stmt = update(REQ_MANAGE_CHECK_PR_INFO_TABLE).where(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.script_update_date != script_update_date,
            REQ_MANAGE_CHECK_PR_INFO_TABLE.default_handle_flag == "否"
        ).values(
            default_handle_flag="是",
            actual_handle_date=handle_date,
            script_update_date=script_update_date
        )
        result = db.session.execute(stmt)
        db.session.commit()
        updated_count = result.rowcount
        logger.info(f"成功更新 {updated_count} 条记录 (script_update_date={script_update_date})")
        return updated_count
    except Exception as e:
        logger.error(f"An error occurred in update_req_manage_check_pr_info_table_data_list: {e}")
        db.session.rollback()


def query_req_manage_check_pr_info_table_by_filter_dict(filter_dict, date_range_dict: Optional[Dict[str, Dict[str, Optional[str]]]] = None):
    """
    根据过滤条件查询记录，支持 "无" 表示筛选空值/空字符串
    返回结果按 problem_type 和 check_date 排序
    
    参数：
        filter_dict: 过滤条件字典，键为字段名，值为值列表
        date_range_dict: 日期范围筛选字典（可选），格式示例：
            {
                "check_date": {"start": "2026-05-01", "end": "2026-05-10"},
                "system_createddate": {"start": "2026-01-01", "end": None},
                "default_handle_date": {"start": None, "end": "2026-06-01"}
            }
            - 如果某个字段的 start 和 end 都为 None 或不存在，则不对该字段进行筛选
            - 如果只有 start，则筛选 >= start 的记录
            - 如果只有 end，则筛选 < end+1 天的记录
    """
    try:
        # 字段白名单校验
        valid_fields = {c.name for c in REQ_MANAGE_CHECK_PR_INFO_TABLE.__table__.columns}
        invalid_fields = set(filter_dict.keys()) - valid_fields
        if invalid_fields:
            logger.warning(f"忽略无效筛选字段：{invalid_fields}")
            filter_dict = {k: v for k, v in filter_dict.items() if k in valid_fields}
        if not filter_dict:
            logger.info("无有效筛选条件，返回空结果")
            return []
        query = db.session.query(REQ_MANAGE_CHECK_PR_INFO_TABLE)
        # 处理日期范围筛选条件
        if date_range_dict and isinstance(date_range_dict, dict):
            for field_name, range_value in date_range_dict.items():
                if not isinstance(range_value, dict):
                    continue
                start_date = range_value.get("start")
                end_date = range_value.get("end")
                # 如果 start 和 end 都为 None 或空，跳过该字段
                if not start_date and not end_date:
                    continue
                field_col = getattr(REQ_MANAGE_CHECK_PR_INFO_TABLE, field_name, None)
                if field_col is None:
                    logger.warning(f"日期字段 '{field_name}' 不存在，跳过")
                    continue
                date_conditions = []
                if start_date:
                    try:
                        start_date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
                        # 使用日期字符串直接比较，兼容 "YYYY-MM-DD" 格式
                        start_date_str = start_date_obj.strftime("%Y-%m-%d")
                        date_conditions.append(field_col >= start_date_str)
                    except ValueError as e:
                        logger.warning(f"{field_name}.start 格式无效：'{start_date}'，期望 'YYYY-MM-DD'。错误：{e}")
                if end_date:
                    try:
                        end_date_obj = datetime.strptime(end_date.strip(), "%Y-%m-%d")
                        # 使用日期字符串直接比较，兼容 "YYYY-MM-DD" 格式
                        end_date_str = end_date_obj.strftime("%Y-%m-%d")
                        date_conditions.append(field_col <= end_date_str)
                    except ValueError as e:
                        logger.warning(f"{field_name}.end 格式无效：'{end_date}'，期望 'YYYY-MM-DD'。错误：{e}")
                if date_conditions:
                    query = query.filter(and_(*date_conditions))
        for field_name, value_list in filter_dict.items():
            if not value_list:
                continue
            field_col = getattr(REQ_MANAGE_CHECK_PR_INFO_TABLE, field_name)
            normal_values = [v for v in value_list if v != NULL_DISPLAY]
            need_empty_filter = NULL_DISPLAY in value_list
            conditions = []
            if normal_values:
                conditions.append(field_col.in_(normal_values))
            if need_empty_filter:
                conditions.append(or_(field_col.is_(None), field_col == ""))
            if conditions:
                query = query.filter(or_(*conditions) if len(conditions) > 1 else conditions[0])
        # 🔧【新增】排序逻辑：先 problem_type，再 check_date，NULL 值排最后
        query = query.order_by(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.problem_type.asc(),
            REQ_MANAGE_CHECK_PR_INFO_TABLE.check_date.asc()
        )
        results = query.all()
        # 🔧 结果序列化：处理不可哈希类型
        def row_to_dict(row):
            row_dict = {}
            for c in row.__table__.columns:
                val = getattr(row, c.name)
                if isinstance(val, (list, dict, set)):
                    row_dict[c.name] = NULL_DISPLAY if not val else val
                else:
                    row_dict[c.name] = NULL_DISPLAY if val in EMPTY_VALUES else val
            return row_dict
        return [row_to_dict(row) for row in results]
    except Exception as e:
        logger.error(f"筛选查询失败 | filter_dict={filter_dict} | error: {e}", exc_info=True)
        db.session.rollback()
        return []


def query_req_manage_check_pr_info_table_value_dict_by_field_list(field_list):
    try:
        from sqlalchemy import or_, and_
        # 1. 字段白名单校验
        valid_fields = {c.name for c in REQ_MANAGE_CHECK_PR_INFO_TABLE.__table__.columns}
        invalid_fields = set(field_list) - valid_fields
        if invalid_fields:
            logger.warning(f"忽略无效字段: {invalid_fields}")
            field_list = [k for k in field_list if k in valid_fields]
        if not field_list:
            logger.info("无有效字段，返回空字典")
            return {}
        result = {}
        for field_name in field_list:
            field_col = getattr(REQ_MANAGE_CHECK_PR_INFO_TABLE, field_name)
            # 2. 查询非空值（自动排除 None 和 ""）
            query = db.session.query(field_col).distinct().filter(
                and_(field_col.isnot(None), field_col != "")
            )
            normal_values = [row[0] for row in query.all()]
            # 3. 检查数据库是否存在空值，存在则添加 "无"
            has_empty = db.session.query(field_col).filter(
                or_(field_col.is_(None), field_col == "")
            ).limit(1).first() is not None
            if has_empty and NULL_DISPLAY not in normal_values:
                normal_values.append(NULL_DISPLAY)
            # 4. 排序："无" 固定放最后，其他按字典序
            def sort_key(x):
                # 非字符串值先转字符串再排序，避免类型比较错误
                sortable = x if isinstance(x, str) else str(x)
                return (0, sortable) if x != NULL_DISPLAY else (1, "")
            values = sorted(normal_values, key=sort_key) if normal_values else []
            result[field_name] = values
        return result
    except Exception as e:
        logger.error(f"获取去重值失败 | fields={field_list} | error: {e}", exc_info=True)
        db.session.rollback()
        return {}


def compute_cal_fields(record_item: Any, current_date: Optional[str] = None) -> Dict[str, str]:
    """
    根据 default_*和 man_*字段计算 cal_*字段和 handle_delay_flag
    逻辑：
    - cal_*字段优先使用 man_*字段值，如果 man_*为空则使用 default_*字段值
    - handle_delay_flag 根据 cal_handle_flag、cal_handle_date 和当前日期计算

    参数：
        record_item: 包含相关字段的记录对象或字典
        current_date: 当前日期，格式 YYYY-MM-DD，如果不传则使用系统当前日期

    返回：
        dict: 包含计算结果的字典 {cal_problem_flag, cal_handle_person, cal_handle_date, cal_handle_flag, handle_delay_flag}
    """
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    # 获取字段值的辅助函数（支持对象属性和字典键访问）
    def get_field_value(field_name: str) -> Optional[str]:
        if hasattr(record_item, field_name):
            return getattr(record_item, field_name)
        elif isinstance(record_item, dict) and field_name in record_item:
            return record_item.get(field_name)
        return None
    # 计算 cal_problem_flag
    man_problem_flag = get_field_value("man_problem_flag")
    default_problem_flag = get_field_value("default_problem_flag")
    cal_problem_flag = man_problem_flag if man_problem_flag else default_problem_flag
    # 计算 cal_handle_person
    man_handle_person = get_field_value("man_handle_person")
    default_handle_person = get_field_value("default_handle_person")
    cal_handle_person = man_handle_person if man_handle_person else default_handle_person
    # 计算 cal_handle_date
    man_handle_date = get_field_value("man_handle_date")
    default_handle_date = get_field_value("default_handle_date")
    cal_handle_date = man_handle_date if man_handle_date else default_handle_date
    # 计算 cal_handle_flag
    man_handle_flag = get_field_value("man_handle_flag")
    default_handle_flag = get_field_value("default_handle_flag")
    cal_handle_flag = man_handle_flag if man_handle_flag else default_handle_flag
    # 计算 handle_delay_flag
    if cal_handle_flag == "否" and cal_handle_date and current_date > cal_handle_date:
        handle_delay_flag = "是"
    else:
        handle_delay_flag = "否"
    return {
        "cal_problem_flag": cal_problem_flag,
        "cal_handle_person": cal_handle_person,
        "cal_handle_date": cal_handle_date,
        "cal_handle_flag": cal_handle_flag,
        "handle_delay_flag": handle_delay_flag,
    }


def update_req_manage_check_pr_info_table_cal_field():
    try:
        record_list = db.session.query(REQ_MANAGE_CHECK_PR_INFO_TABLE).all()
        current_date = datetime.now().strftime("%Y-%m-%d")
        for record_item in record_list:
            # 调用抽象函数计算字段
            cal_result = compute_cal_fields(record_item, current_date)
            # 更新记录
            record_item.cal_problem_flag = cal_result["cal_problem_flag"]
            record_item.cal_handle_person = cal_result["cal_handle_person"]
            record_item.cal_handle_date = cal_result["cal_handle_date"]
            record_item.cal_handle_flag = cal_result["cal_handle_flag"]
            record_item.handle_delay_flag = cal_result["handle_delay_flag"]
        db.session.commit()
        return None
    except Exception as e:
        logger.error(f"更新失败 | error: {e}", exc_info=True)
        db.session.rollback()
        return {}


def update_req_manage_check_pr_info_table_man_fields_by_id_list(update_data: Dict[str, Any]) -> int:
    """
    根据 ID 列表批量更新多条记录的 man_problem_flag、man_handle_person、man_handle_date、man_handle_flag 字段
    更新完成后自动计算 cal_*字段和 handle_delay_flag

    参数：
        update_data: 字典，包含以下键：
            - man_update_person: 人工标注更新人（必填），格式为"姓名 + 工号"（如"刘威 10139282"），从请求头 X-Emp-No 获取并调用 pub_get_employ_name 拼接
            - man_update_date: 人工标注更新日期（必填）
            - man_problem_flag: 人工标注是否问题（可选，为空则不更新该字段）
            - man_handle_person: 人工标注整改责任人（可选，为空则不更新该字段）
            - man_handle_date: 人工标注整改截止日期（可选，为空则不更新该字段）
            - man_handle_flag: 人工标注是否已整改（可选，为空则不更新该字段）
            - id_list: 记录 ID 列表（必填）

    返回：
        int: 更新的记录数量

    注意：
        - 如果 man_problem_flag、man_handle_person、man_handle_date、man_handle_flag 某个值为空（None 或""），
          则对应字段不进行更新
        - 更新完成后会自动计算并更新 cal_*字段和 handle_delay_flag
    """
    try:
        # 提取参数
        id_list = update_data.get("id_list", [])
        man_update_person = update_data.get("man_update_person")
        man_update_date = update_data.get("man_update_date")
        man_problem_flag = update_data.get("man_problem_flag")
        man_handle_person = update_data.get("man_handle_person")
        man_handle_date = update_data.get("man_handle_date")
        man_handle_flag = update_data.get("man_handle_flag")
        # 基础校验
        if not id_list:
            logger.warning("ID 列表为空，不执行更新")
            return 0
        if not man_update_person or not man_update_date:
            logger.warning("人工标注更新人或更新日期为空，不执行更新")
            return 0
        # 构建更新字典（只包含非空字段）
        update_values = {
            "man_update_person": man_update_person,
            "man_update_date": man_update_date,
        }
        # 只有当字段值非空时才添加到更新字典
        if man_problem_flag not in EMPTY_VALUES:
            update_values["man_problem_flag"] = man_problem_flag
        if man_handle_person not in EMPTY_VALUES:
            update_values["man_handle_person"] = man_handle_person
        if man_handle_date not in EMPTY_VALUES:
            update_values["man_handle_date"] = man_handle_date
        if man_handle_flag not in EMPTY_VALUES:
            update_values["man_handle_flag"] = man_handle_flag
        # 执行批量更新
        stmt = update(REQ_MANAGE_CHECK_PR_INFO_TABLE).where(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.id.in_(id_list)
        ).values(update_values)
        result = db.session.execute(stmt)
        updated_count = result.rowcount
        db.session.commit()
        logger.info(f"成功更新 {updated_count} 条记录的人工标注字段 | ID 列表：{id_list}")
        # 更新完成后，重新计算这些记录的 cal_*字段
        if updated_count > 0:
            current_date = datetime.now().strftime("%Y-%m-%d")
            records_to_update = db.session.query(REQ_MANAGE_CHECK_PR_INFO_TABLE).filter(
                REQ_MANAGE_CHECK_PR_INFO_TABLE.id.in_(id_list)
            ).all()
            for record_item in records_to_update:
                cal_result = compute_cal_fields(record_item, current_date)
                record_item.cal_problem_flag = cal_result["cal_problem_flag"]
                record_item.cal_handle_person = cal_result["cal_handle_person"]
                record_item.cal_handle_date = cal_result["cal_handle_date"]
                record_item.cal_handle_flag = cal_result["cal_handle_flag"]
                record_item.handle_delay_flag = cal_result["handle_delay_flag"]
            db.session.commit()
            logger.info(f"成功计算 {len(records_to_update)} 条记录的 cal_*字段")
        return updated_count
    except Exception as e:
        logger.error(f"批量更新人工标注字段失败 | error: {e}", exc_info=True)
        db.session.rollback()
        return 0


class ReqManageCheckPrSummaryTable(BaseModel):
    id: Optional[int] = None
    summary_date: Optional[str] = None
    requirementpreplanning: Optional[str] = None
    all_num: Optional[int] = None
    problem_num: Optional[int] = None
    not_problem_num: Optional[int] = None
    handle_num: Optional[int] = None
    not_handle_num: Optional[int] = None
    delay_num: Optional[int] = None
    not_delay_num: Optional[int] = None


def update_req_manage_check_pr_summary_table_data_list(summary_date):
    """
    根据 ReqManageCheckPrInfoTable 表统计数据并更新到 REQ_MANAGE_CHECK_PR_SUMMARY_TABLE
    参数：
        summary_date: 统计日期，格式 YYYY-MM-DD
    逻辑：
        1. 按 requirementpreplanning 分组统计各项指标
        2. 额外添加一行"所有"的汇总数据
        3. 使用 upsert 逻辑：存在则更新，不存在则插入
    """
    try:
        if not isinstance(summary_date, str):
            logger.error(f"日期参数必须为字符串，当前类型：{type(summary_date)}")
            return
        try:
            target_date = datetime.strptime(summary_date.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError as e:
            logger.error(f"日期格式无效：'{summary_date}'，期望 'YYYY-MM-DD'。错误：{e}")
            return
        problem_condition = (REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag == "是")
        not_problem_condition = (REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag != "是")
        handle_condition = and_(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag == "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_handle_flag == "是"
        )
        not_handle_condition = and_(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag == "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_handle_flag != "是"
        )
        delay_condition = and_(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag == "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_handle_flag != "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.handle_delay_flag == "是"
        )
        not_delay_condition = and_(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_problem_flag == "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.cal_handle_flag != "是",
            REQ_MANAGE_CHECK_PR_INFO_TABLE.handle_delay_flag != "是"
        )
        query = db.session.query(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.requirementpreplanning,
            func.count().label('all_num'),
            func.sum(case((problem_condition, 1), else_=0)).label('problem_num'),
            func.sum(case((not_problem_condition, 1), else_=0)).label('not_problem_num'),
            func.sum(case((handle_condition, 1), else_=0)).label('handle_num'),
            func.sum(case((not_handle_condition, 1), else_=0)).label('not_handle_num'),
            func.sum(case((delay_condition, 1), else_=0)).label('delay_num'),
            func.sum(case((not_delay_condition, 1), else_=0)).label('not_delay_num')
        ).group_by(
            REQ_MANAGE_CHECK_PR_INFO_TABLE.requirementpreplanning
        ).all()
        summary_data_list = []
        for row in query:
            preplanning = row.requirementpreplanning
            if preplanning is None:
                preplanning = NULL_DISPLAY
            summary_data = {
                "summary_date": target_date,
                "requirementpreplanning": preplanning,
                "all_num": row.all_num if row.all_num else 0,
                "problem_num": row.problem_num if row.problem_num else 0,
                "not_problem_num": row.not_problem_num if row.not_problem_num else 0,
                "handle_num": row.handle_num if row.handle_num else 0,
                "not_handle_num": row.not_handle_num if row.not_handle_num else 0,
                "delay_num": row.delay_num if row.delay_num else 0,
                "not_delay_num": row.not_delay_num if row.not_delay_num else 0,
            }
            summary_data_list.append(summary_data)
        total_all_num = sum(item["all_num"] for item in summary_data_list)
        total_problem_num = sum(item["problem_num"] for item in summary_data_list)
        total_not_problem_num = sum(item["not_problem_num"] for item in summary_data_list)
        total_handle_num = sum(item["handle_num"] for item in summary_data_list)
        total_not_handle_num = sum(item["not_handle_num"] for item in summary_data_list)
        total_delay_num = sum(item["delay_num"] for item in summary_data_list)
        total_not_delay_num = sum(item["not_delay_num"] for item in summary_data_list)
        summary_data_list.append({
            "summary_date": target_date,
            "requirementpreplanning": TOTAL_LABEL,
            "all_num": total_all_num,
            "problem_num": total_problem_num,
            "not_problem_num": total_not_problem_num,
            "handle_num": total_handle_num,
            "not_handle_num": total_not_handle_num,
            "delay_num": total_delay_num,
            "not_delay_num": total_not_delay_num,
        })
        for data_item in summary_data_list:
            summary_date_val = data_item.get("summary_date")
            requirementpreplanning = data_item.get("requirementpreplanning")
            obj_model = db.session.query(REQ_MANAGE_CHECK_PR_SUMMARY_TABLE).filter_by(
                summary_date=summary_date_val,
                requirementpreplanning=requirementpreplanning
            ).first()
            if obj_model:
                obj_model.all_num = data_item.get("all_num")
                obj_model.problem_num = data_item.get("problem_num")
                obj_model.not_problem_num = data_item.get("not_problem_num")
                obj_model.handle_num = data_item.get("handle_num")
                obj_model.not_handle_num = data_item.get("not_handle_num")
                obj_model.delay_num = data_item.get("delay_num")
                obj_model.not_delay_num = data_item.get("not_delay_num")
            else:
                new_record = REQ_MANAGE_CHECK_PR_SUMMARY_TABLE(
                    summary_date=summary_date_val,
                    requirementpreplanning=requirementpreplanning,
                    all_num=data_item.get("all_num"),
                    problem_num=data_item.get("problem_num"),
                    not_problem_num=data_item.get("not_problem_num"),
                    handle_num=data_item.get("handle_num"),
                    not_handle_num=data_item.get("not_handle_num"),
                    delay_num=data_item.get("delay_num"),
                    not_delay_num=data_item.get("not_delay_num"),
                )
                db.session.add(new_record)
        logger.info(
            f"汇总统计完成 | 日期：{target_date} | "
            f"分组数：{len(summary_data_list) - 1} | "
            f"含总计行：是 | "
            f"总记录数：{total_all_num}"
        )
        db.session.commit()
    except Exception as e:
        logger.error(f"An error occurred in update_req_manage_check_pr_summary_table_data_list: {e}", exc_info=True)
        db.session.rollback()


def query_req_manage_check_pr_summary_table_by_date_range_and_preplanning(start_date, end_date, requirementpreplanning_list):
    """
    查询指定日期范围和预规划列表内的汇总数据（按预规划分组返回时间序列）
    参数：
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        requirementpreplanning_list: 需求预规划列表
    返回：
        list[dict]: 按预规划分组，每组包含日期列表和各项指标的时间序列
    """
    try:
        if not all(isinstance(arg, str) for arg in [start_date, end_date]):
            logger.error(f"日期参数类型错误，期望字符串 | start_date:{type(start_date)}, end_date:{type(end_date)}")
            return []
        if not isinstance(requirementpreplanning_list, list):
            logger.error(f"requirementpreplanning_list 参数类型错误，期望列表 | type:{type(requirementpreplanning_list)}")
            return []
        try:
            start_date_obj = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date.strip(), "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"日期格式解析失败，期望 'YYYY-MM-DD' | 错误：{e}")
            return []
        date_list = pub_generate_date_range(start_date, end_date)
        records = db.session.query(REQ_MANAGE_CHECK_PR_SUMMARY_TABLE).filter(
            REQ_MANAGE_CHECK_PR_SUMMARY_TABLE.summary_date.in_(date_list),
            REQ_MANAGE_CHECK_PR_SUMMARY_TABLE.requirementpreplanning.in_(requirementpreplanning_list)
        ).all()
        record_map = {
            (rec.requirementpreplanning, rec.summary_date): rec
            for rec in records
            if rec.requirementpreplanning is not None and rec.summary_date is not None
        }
        result = []
        for requirementpreplanning in requirementpreplanning_list:
            all_num_list = []
            problem_num_list = []
            not_problem_num_list = []
            handle_num_list = []
            not_handle_num_list = []
            delay_num_list = []
            not_delay_num_list = []
            last_all = 0
            last_problem = 0
            last_not_problem = 0
            last_handle = 0
            last_not_handle = 0
            last_delay = 0
            last_not_delay = 0
            for date in date_list:
                key = (requirementpreplanning, date)
                if key in record_map:
                    rec = record_map[key]
                    last_all = rec.all_num if rec.all_num is not None else 0
                    last_problem = rec.problem_num if rec.problem_num is not None else 0
                    last_not_problem = rec.not_problem_num if rec.not_problem_num is not None else 0
                    last_handle = rec.handle_num if rec.handle_num is not None else 0
                    last_not_handle = rec.not_handle_num if rec.not_handle_num is not None else 0
                    last_delay = rec.delay_num if rec.delay_num is not None else 0
                    last_not_delay = rec.not_delay_num if rec.not_delay_num is not None else 0
                all_num_list.append(last_all)
                problem_num_list.append(last_problem)
                not_problem_num_list.append(last_not_problem)
                handle_num_list.append(last_handle)
                not_handle_num_list.append(last_not_handle)
                delay_num_list.append(last_delay)
                not_delay_num_list.append(last_not_delay)
            result.append({
                "requirementpreplanning": requirementpreplanning,
                "date_list": date_list,
                "all_num_list": all_num_list,
                "problem_num_list": problem_num_list,
                "not_problem_num_list": not_problem_num_list,
                "handle_num_list": handle_num_list,
                "not_handle_num_list": not_handle_num_list,
                "delay_num_list": delay_num_list,
                "not_delay_num_list": not_delay_num_list,
            })
        logger.info(
            f"汇总查询成功 | 时间范围：[{start_date}, {end_date}] | "
            f"preplanning_count: {len(requirementpreplanning_list)} | "
            f"返回记录数：{len(result)}"
        )
        return result
    except Exception as e:
        logger.exception(
            f"汇总查询异常 | 时间范围：[{start_date}, {end_date}] | "
            f"requirementpreplanning_list: {requirementpreplanning_list} | "
            f"错误：{str(e)}"
        )
        db.session.rollback()
        return []