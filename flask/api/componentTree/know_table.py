from utils import pub
from collections import defaultdict
from sqlalchemy.dialects.mysql import INTEGER
from datetime import datetime, timedelta, date as dt_date
from sqlalchemy import String, Column, DateTime, Text, delete, JSON, Boolean, and_, or_, desc, DECIMAL
from model import db_store


class KnowCompTreePageTable(db_store.BaseModel):
    __tablename__ = "know_comp_tree_page_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    page_title = Column(String(128))
    field_name = Column(String(128))
    comp_name = Column(String(128))
    module_name = Column(String(128))
    module_num = Column(INTEGER)
    page_url = Column(String(256))
    page_status = Column(String(128))
    page_person = Column(String(128))
    page_se = Column(String(128))
    page_tl = Column(String(128))
    page_tse = Column(String(128))
    finish_flag = Column(String(128))
    update_by = Column(String(128))
    update_date = Column(String(128))
    editor_num = Column(INTEGER)
    edit_num = Column(INTEGER)
    view_visitor_num = Column(INTEGER)
    view_visit_num = Column(INTEGER)
    ai_adapt_num = Column(DECIMAL(10, 2))
    ai_gene_num = Column(DECIMAL(10, 2))
    comp_engineering = Column(JSON)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@db_store.session_safe_crawler
def query_know_comp_tree_page_table_comp_tree_page_list_by_field_name_page_status_page_type(*args, **kwargs):
    return __query_know_comp_tree_page_table_comp_tree_page_list_by_field_name_page_status_page_type


def __query_know_comp_tree_page_table_comp_tree_page_list_by_field_name_page_status_page_type(session, field_name, page_status, page_type):
    if page_status == "总数":
        if field_name == "波分中心":
            model_list = session.query(KnowCompTreePageTable).all()
        else:
            model_list = session.query(KnowCompTreePageTable).filter(KnowCompTreePageTable.field_name == field_name).all()
    else:
        if field_name == "波分中心":
            model_list = session.query(KnowCompTreePageTable).filter(KnowCompTreePageTable.page_status == page_status).all()
        else:
            model_list = session.query(KnowCompTreePageTable).filter(KnowCompTreePageTable.field_name == field_name,KnowCompTreePageTable.page_status == page_status).all()
    data_list = []
    if page_type == "comp":
        data_list = [item.as_dict() for item in model_list if item.module_name==""]
    else:
        data_list = [item.as_dict() for item in model_list if item.module_name]
    return data_list


@db_store.session_safe_crawler
def update_know_comp_tree_page_table_comp_tree_page_list(*args, **kwargs):
    return __update_know_comp_tree_page_table_comp_tree_page_list


def __update_know_comp_tree_page_table_comp_tree_page_list(session, comp_tree_page_list):
    session.query(KnowCompTreePageTable).delete()
    session.commit()
    for comp_tree_page_item in comp_tree_page_list:
        # 为列表中的每一项创建一个全新的数据库记录
        new_comp_tree_page_model = KnowCompTreePageTable(**comp_tree_page_item)
        session.add(new_comp_tree_page_model)


@db_store.session_safe_crawler
def query_know_comp_tree_page_table_comp_tree_page_list_by_comp_name(*args, **kwargs):
    return __query_know_comp_tree_page_table_comp_tree_page_list_by_comp_name


def __query_know_comp_tree_page_table_comp_tree_page_list_by_comp_name(session, comp_name):
    model_list = session.query(KnowCompTreePageTable).filter(KnowCompTreePageTable.comp_name == comp_name).all()
    return [item.as_dict() for item in model_list]


@db_store.session_safe_crawler
def query_know_comp_tree_page_table_page_url_list_by_comp_name(*args, **kwargs):
    return __query_know_comp_tree_page_table_page_url_list_by_comp_name


def __query_know_comp_tree_page_table_page_url_list_by_comp_name(session, comp_name):
    if not comp_name or not isinstance(comp_name, str) or not comp_name.strip():
        return []
    model_list = session.query(KnowCompTreePageTable).filter(
        KnowCompTreePageTable.comp_name.ilike(f"%{comp_name.strip()}%")
    ).all()
    return [
        {
            "comp_name": item.comp_name,
            "module_name": item.module_name,
            "icenter_title": item.page_title,
            "icenter_url": item.page_url
        }
        for item in model_list
    ]


class KnowCompTreeBoardTable(db_store.BaseModel):
    __tablename__ = "know_comp_tree_board_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    date = Column(String(128))
    field_name = Column(String(128))
    comp_sum_num = Column(INTEGER)
    comp_initial_num = Column(INTEGER)
    comp_reviewed_num = Column(INTEGER)
    comp_revision_num = Column(INTEGER)
    comp_finish_num = Column(INTEGER)
    comp_sum_editor_num = Column(INTEGER)
    comp_sum_edit_num = Column(INTEGER)
    comp_sum_view_visitor_num = Column(INTEGER)
    comp_sum_view_visit_num = Column(INTEGER)
    comp_sum_ai_adapt_num = Column(DECIMAL(10, 2))
    comp_sum_ai_gene_num = Column(DECIMAL(10, 2))
    module_sum_num = Column(INTEGER)
    module_initial_num = Column(INTEGER)
    module_reviewed_num = Column(INTEGER)
    module_revision_num = Column(INTEGER)
    module_finish_num = Column(INTEGER)
    module_sum_editor_num = Column(INTEGER)
    module_sum_edit_num = Column(INTEGER)
    module_sum_view_visitor_num = Column(INTEGER)
    module_sum_view_visit_num = Column(INTEGER)
    module_sum_ai_adapt_num = Column(DECIMAL(10, 2))
    module_sum_ai_gene_num = Column(DECIMAL(10, 2))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@db_store.session_safe_crawler
def query_know_comp_tree_board_table_latest_comp_tree_board_list(*args, **kwargs):
    return __query_know_comp_tree_board_table_latest_comp_tree_board_list


def __query_know_comp_tree_board_table_latest_comp_tree_board_list(session):
    latest_date = session.query(KnowCompTreeBoardTable.date).order_by(KnowCompTreeBoardTable.date.desc()).limit(1).scalar()
    if not latest_date: return []
    records = session.query(KnowCompTreeBoardTable).filter(KnowCompTreeBoardTable.date == latest_date).all()
    return [record.as_dict() for record in records]


@db_store.session_safe_crawler
def query_know_comp_tree_board_table_comp_tree_board_sum_list(*args, **kwargs):
    return __query_know_comp_tree_board_table_comp_tree_board_sum_list


def __query_know_comp_tree_board_table_comp_tree_board_sum_list(session, start_date, end_date, page_type, data_type):
    # ===== 输入转换：支持字符串或 date 类型，统一转为 date 用于计算 =====
    if isinstance(start_date, str):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    elif isinstance(start_date, (dt_date, datetime)):
        start_date_obj = start_date if isinstance(start_date, dt_date) else start_date.date()
    else:
        raise TypeError(f"start_date must be str or date/datetime, got {type(start_date)}")

    if isinstance(end_date, str):
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    elif isinstance(end_date, (dt_date, datetime)):
        end_date_obj = end_date if isinstance(end_date, dt_date) else end_date.date()
    else:
        raise TypeError(f"end_date must be str or date/datetime, got {type(end_date)}")
    # ===================================================================
    if page_type not in ['comp', 'module'] or not data_type:
        return []
    ratio_mapping = {
        'finish_rate': 'finish_num',
    }
    is_ratio_type = data_type in ratio_mapping
    # 生成完整日期范围（使用 date 类型计算）
    def daterange(start, end):
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    all_dates = list(daterange(start_date_obj, end_date_obj))  # date 类型列表
    # 查询原始数据
    if is_ratio_type:
        numerator_suffix = ratio_mapping[data_type]
        numerator_field_name = f"{page_type}_{numerator_suffix}"
        denominator_field_name = f"{page_type}_sum_num"
        column_names = {c.name for c in KnowCompTreeBoardTable.__table__.columns}
        if numerator_field_name not in column_names or denominator_field_name not in column_names:
            return []
        numerator_col = getattr(KnowCompTreeBoardTable, numerator_field_name)
        denominator_col = getattr(KnowCompTreeBoardTable, denominator_field_name)
        raw_list = session.query(
            KnowCompTreeBoardTable.date,
            KnowCompTreeBoardTable.field_name,
            numerator_col.label('numerator'),
            denominator_col.label('denominator')
        ).filter(
            KnowCompTreeBoardTable.date >= start_date,
            KnowCompTreeBoardTable.date <= end_date
        ).order_by(KnowCompTreeBoardTable.date.asc()).all()
        field_data_map = defaultdict(dict)
        for item in raw_list:
            # 把数据库中的 date 转为字符串键
            if isinstance(item.date, (dt_date, datetime)):
                key_str = item.date.strftime("%Y-%m-%d")
            else:  # 假设是字符串
                key_str = item.date
            num = item.numerator if item.numerator is not None else 0
            den = item.denominator if item.denominator is not None else 0
            field_data_map[item.field_name][key_str] = (num, den)
        comp_tree_board_echart_list = []
        for field_name in field_data_map.keys():
            last_numerator = None
            last_denominator = None
            for d in all_dates:
                d_str = d.strftime("%Y-%m-%d")
                if d_str in field_data_map[field_name]:
                    num, den = field_data_map[field_name][d_str]
                    last_numerator = num
                    last_denominator = den

                if last_numerator is None or last_denominator is None:
                    value = 0
                else:
                    value = pub.pub_get_ratio(
                        dividend=last_numerator,
                        divisor=last_denominator,
                        decimal_places=2
                    ) if last_denominator != 0 else 0

                comp_tree_board_echart_list.append({
                    "date": d_str,
                    "field_name": field_name,
                    "value": value
                })
    else:
        target_column_name = f"{page_type}_{data_type}"
        column_names = {c.name for c in KnowCompTreeBoardTable.__table__.columns}
        if target_column_name not in column_names:
            return []
        target_column = getattr(KnowCompTreeBoardTable, target_column_name)
        module_list = session.query(
            KnowCompTreeBoardTable.date,
            KnowCompTreeBoardTable.field_name,
            target_column.label('data')
        ).filter(
            KnowCompTreeBoardTable.date >= start_date,
            KnowCompTreeBoardTable.date <= end_date
        ).order_by(KnowCompTreeBoardTable.date.asc()).all()
        field_data_map = defaultdict(dict)
        for item in module_list:
            if isinstance(item.date, (dt_date, datetime)):
                key_str = item.date.strftime("%Y-%m-%d")
            else:
                key_str = item.date
            field_data_map[item.field_name][key_str] = item.data
        comp_tree_board_echart_list = []
        for field_name in field_data_map.keys():
            last_valid_data = None
            for d in all_dates:
                d_str = d.strftime("%Y-%m-%d")  # 转字符串查字典
                if d_str in field_data_map[field_name]:
                    last_valid_data = field_data_map[field_name][d_str]

                if last_valid_data is None:
                    output_value = 0
                else:
                    output_value = float(last_valid_data) if last_valid_data is not None else 0
                comp_tree_board_echart_list.append({
                    "date": d_str,
                    "field_name": field_name,
                    "value": output_value
                })
    return comp_tree_board_echart_list


@db_store.session_safe_crawler
def add_know_comp_tree_board_table_comp_tree_board_list(*args, **kwargs):
    return __add_know_comp_tree_board_table_comp_tree_board_list


def __add_know_comp_tree_board_table_comp_tree_board_list(session, comp_tree_board_list):
    if len(comp_tree_board_list) == 0: return
    date = comp_tree_board_list[0].get("date")
    session.query(KnowCompTreeBoardTable).filter(KnowCompTreeBoardTable.date==date).delete()
    session.commit()
    for comp_tree_board_item in comp_tree_board_list:
        # 为列表中的每一项创建一个全新的数据库记录
        new_comp_tree_board_model = KnowCompTreeBoardTable(**comp_tree_board_item)
        session.add(new_comp_tree_board_model)


class KnowBuildInfoTable(db_store.BaseModel):
    __tablename__ = "know_build_info_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    know_type = Column(String(64))
    domain = Column(String(64))
    content = Column(String(256))
    owner = Column(String(64))
    plan_date = Column(String(64))
    status = Column(String(64))
    actual_date = Column(String(64))
    link = Column(String(64))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def parse_date_safe(date_str):
    """
    统一安全的日期解析工具
    返回 datetime.date 对象或 None
    """
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def to_date_obj(val):
    """
    统一日期对象转换工具（用于输入参数）
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return None
    return val


@db_store.session_safe_crawler
def add_know_build_info_table_know_build_info_list(*args, **kwargs):
    return __add_know_build_info_table_know_build_info_list


def __add_know_build_info_table_know_build_info_list(session, know_build_info_list):
    if len(know_build_info_list) == 0:
        return
    session.query(KnowBuildInfoTable).delete(synchronize_session=False)
    for know_build_info_item in know_build_info_list:
        new_know_build_info_model = KnowBuildInfoTable(**know_build_info_item)
        session.add(new_know_build_info_model)


@db_store.session_safe_crawler
def query_know_build_info_table_know_type_list(*args, **kwargs):
    return __query_know_build_info_table_know_type_list


def __query_know_build_info_table_know_type_list(session):
    query = session.query(KnowBuildInfoTable.know_type).distinct()
    results = query.all()
    know_type_list = [item[0] for item in results if item[0] is not None]
    know_type_list.sort()
    return know_type_list


@db_store.session_safe_crawler
def query_know_build_info_table_field_table_list(*args, **kwargs):
    return __query_know_build_info_table_field_table_list


def __query_know_build_info_table_field_table_list(session, know_type, start_date, end_date):
    today = datetime.now().date()
    # 转换起止日期
    start_dt = to_date_obj(start_date)
    end_dt = to_date_obj(end_date)
    # 基础校验
    if start_dt is None or end_dt is None:
        return []
    # 构建基础查询
    base_query = session.query(KnowBuildInfoTable)
    if know_type:
        base_query = base_query.filter(KnowBuildInfoTable.know_type == know_type)
    # 获取所有记录
    all_records = base_query.all()
    # 按领域分组
    domain_records = defaultdict(list)
    for record in all_records:
        domain_records[record.domain].append(record)
    result_list = []
    # 遍历每个领域进行统计
    for domain, records in domain_records.items():
        domain_stats = {
            "domain": domain,
            "total_plan_count": 0,
            "total_completed_count": 0,
            "total_delayed_count": 0,
            "total_completion_rate": "0%",
            "total_delay_rate": "0%",
            "current_period_plan_count": 0,
            "current_period_completed_count": 0,
            "current_period_completion_rate": "0%"
        }
        for record in records:
            # 【修复】独立解析计划日期和实际日期，互不影响
            plan_date_obj = parse_date_safe(record.plan_date)
            actual_date_obj = parse_date_safe(record.actual_date)
            # 如果计划日期解析失败，这条记录无法参与时间相关统计
            if plan_date_obj is None:
                continue
            # 1. 统计计划数（只要计划日期有效就计数）
            domain_stats["total_plan_count"] += 1
            # 2. 统计完成数
            if record.status == "已定稿":
                domain_stats["total_completed_count"] += 1
            # 3. 统计延误数（未完成 + 计划日期 < 今天）
            if record.status != "已定稿" and plan_date_obj < today:
                domain_stats["total_delayed_count"] += 1
            # 4. 统计当前周期计划数
            if start_dt <= plan_date_obj <= end_dt:
                domain_stats["current_period_plan_count"] += 1
            # 5. 统计当前周期完成数（严格要求 actual_date 在范围内）
            if actual_date_obj and record.status == "已定稿":
                if start_dt <= actual_date_obj <= end_dt:
                    domain_stats["current_period_completed_count"] += 1
        # 计算整体比率
        if domain_stats["total_plan_count"] > 0:
            domain_stats["total_completion_rate"] = f"{pub.pub_get_ratio(domain_stats['total_completed_count'], domain_stats['total_plan_count'])}%"
            domain_stats["total_delay_rate"] = f"{pub.pub_get_ratio(domain_stats['total_delayed_count'], domain_stats['total_plan_count'])}%"
        # 计算当前周期完成率
        if domain_stats["current_period_plan_count"] > 0:
            domain_stats["current_period_completion_rate"] = f"{pub.pub_get_ratio(domain_stats['current_period_completed_count'], domain_stats['current_period_plan_count'])}%"
        result_list.append(domain_stats)
    # 添加汇总行
    result_list.append(merge_domain_statistics(result_list))
    return result_list


def merge_domain_statistics(statistics_list):
    if not statistics_list:
        return {
            "domain": "整体",
            "total_plan_count": 0,
            "total_completed_count": 0,
            "total_delayed_count": 0,
            "total_completion_rate": "0%",
            "total_delay_rate": "0%",
            "current_period_plan_count": 0,
            "current_period_completed_count": 0,
            "current_period_completion_rate": "0%"
        }
    
    merged = {
        "domain": "整体",
        "total_plan_count": 0,
        "total_completed_count": 0,
        "total_delayed_count": 0,
        "total_completion_rate": "0%",
        "total_delay_rate": "0%",
        "current_period_plan_count": 0,
        "current_period_completed_count": 0,
        "current_period_completion_rate": "0%"
    }
    # 累加各领域的计数
    for stats in statistics_list:
        merged["total_plan_count"] += stats["total_plan_count"]
        merged["total_completed_count"] += stats["total_completed_count"]
        merged["total_delayed_count"] += stats["total_delayed_count"]
        merged["current_period_plan_count"] += stats["current_period_plan_count"]
        merged["current_period_completed_count"] += stats["current_period_completed_count"]
    # 计算整体比率
    if merged["total_plan_count"] > 0:
        merged["total_completion_rate"] = f"{pub.pub_get_ratio(merged['total_completed_count'], merged['total_plan_count'])}%"
        merged["total_delay_rate"] = f"{pub.pub_get_ratio(merged['total_delayed_count'], merged['total_plan_count'])}%"
    if merged["current_period_plan_count"] > 0:
        merged["current_period_completion_rate"] = f"{pub.pub_get_ratio(merged['current_period_completed_count'], merged['current_period_plan_count'])}%"
    return merged


@db_store.session_safe_crawler
def query_know_build_info_table_trend_data_dict(*args, **kwargs):
    """
    获取指定领域、类型的趋势数据
    返回格式：{ "categories": ["2023-01-01", ...], "plan_data": [10, 12, ...], "actual_data": [5, 6, ...] }
    """
    return __query_know_build_info_table_trend_data_dict


def __query_know_build_info_table_trend_data_dict(session, know_type, domain, start_date, end_date):
    # 1. 参数类型转换
    start_dt = to_date_obj(start_date)
    end_dt = to_date_obj(end_date)
    # 关键校验
    if start_dt is None or end_dt is None:
        raise ValueError(f"日期转换失败！start_date: {start_date}, end_date: {end_date}")
    if start_dt > end_dt:
        raise ValueError(f"开始日期不能晚于结束日期！start_date: {start_dt}, end_date: {end_dt}")
    # 生成日期列表（横坐标）
    date_range = []
    curr = start_dt
    while curr <= end_dt:
        date_range.append(curr)
        curr += timedelta(days=1)
    date_str_list = [d.strftime("%Y-%m-%d") for d in date_range]
    # 获取当前日期，用于判断延误
    today = datetime.now().date()
    # 2. 构建基础查询
    if domain and domain != "整体":
        query = session.query(KnowBuildInfoTable).filter(
            KnowBuildInfoTable.know_type == know_type,
            KnowBuildInfoTable.domain == domain
        )
    else:
        query = session.query(KnowBuildInfoTable).filter(
            KnowBuildInfoTable.know_type == know_type
        )
    records = query.all()
    # 3. 内存中统计
    plan_daily = defaultdict(int)      # 按计划日期统计新增计划数
    actual_daily = defaultdict(int)    # 按实际日期统计完成数
    delayed_daily = defaultdict(int)   # 【新增】按计划日期统计延误数
    for record in records:
        # 使用统一工具函数解析日期
        p_date = parse_date_safe(record.plan_date)
        a_date = parse_date_safe(record.actual_date)
        is_completed = (record.status == "已定稿")
        # 统计计划增量（按计划日期）
        if p_date:
            plan_daily[p_date] += 1
        # 统计实际增量（按实际日期，严格要求 actual_date 存在）
        if is_completed and a_date:
            actual_daily[a_date] += 1
        # 【新增】统计延误数
        # 延误定义：计划日期有效 + 状态未完成 + 计划日期 < 今天
        # 按"计划日期"分组统计，表示"本该在该日期完成但实际未完成"的任务
        if p_date and not is_completed and p_date < today:
            delayed_daily[p_date] += 1
    # 4. 生成累积序列
    # 计算起始日期之前的累积基数
    base_plan = sum(count for d, count in plan_daily.items() if d < start_dt)
    base_actual = sum(count for d, count in actual_daily.items() if d < start_dt)
    base_delayed = sum(count for d, count in delayed_daily.items() if d < start_dt)
    plan_result = []
    actual_result = []
    delayed_result = []
    running_plan = base_plan
    running_actual = base_actual
    running_delayed = base_delayed
    for d in date_range:
        running_plan += plan_daily.get(d, 0)
        running_actual += actual_daily.get(d, 0)
        running_delayed += delayed_daily.get(d, 0)  # 【新增】累积延误数
        plan_result.append(running_plan)
        actual_result.append(running_actual)
        delayed_result.append(running_delayed)      # 【新增】
    # 5. 返回结果（新增 delayed_data 字段）
    return {
        "categories": date_str_list,
        "plan_data": plan_result,
        "actual_data": actual_result,
        "delayed_data": delayed_result  # 【新增】延误累积数据
    }


@db_store.session_safe_crawler
def query_know_build_info_table_know_detail_list(*args, **kwargs):
    """
    获取下钻明细数据
    逻辑严格对齐 __query_know_build_info_table_field_table_list
    """
    return __query_know_build_info_table_know_detail_list


def __query_know_build_info_table_know_detail_list(session, know_type, domain, start_date, end_date, stat_type):
    # 转换输入日期
    start_dt = to_date_obj(start_date)
    end_dt = to_date_obj(end_date)
    today = datetime.now().date()
    # 基础校验
    if not start_dt or not end_dt:
        return []
    # 2. 构建基础查询对象
    query = session.query(KnowBuildInfoTable)
    # 固定条件：知识类型
    if know_type:
        query = query.filter(KnowBuildInfoTable.know_type == know_type)
    # 动态条件：领域
    if domain and domain != "整体":
        query = query.filter(KnowBuildInfoTable.domain == domain)
    # 获取所有符合基础条件的记录
    all_records = query.all()
    filtered_records = []
    for record in all_records:
        # 【修复】使用统一工具函数独立解析日期
        plan_date_obj = parse_date_safe(record.plan_date)
        actual_date_obj = parse_date_safe(record.actual_date)
        # 如果计划日期解析失败，这条记录无法参与大多数统计
        if plan_date_obj is None:
            continue
        include_record = False
        if stat_type == 'total_plan_count':
            # 主表逻辑：只要计划日期有效就计数
            include_record = True
        elif stat_type == 'total_completed_count':
            # 主表逻辑：状态为"已定稿"且计划日期有效
            if record.status == "已定稿":
                include_record = True
        elif stat_type == 'total_delayed_count':
            # 主表逻辑：未完成 + 计划日期 < 今天
            if record.status != "已定稿" and plan_date_obj < today:
                include_record = True
        elif stat_type == 'current_period_plan_count':
            # 主表逻辑：计划日期在 [start, end] 范围内
            if start_dt <= plan_date_obj <= end_dt:
                include_record = True
        elif stat_type == 'current_period_completed_count':
            # 主表逻辑：实际日期在 [start, end] 范围内 + 已定稿
            # 【修复】与统计表保持一致，严格要求 actual_date
            if actual_date_obj and record.status == "已定稿":
                if start_dt <= actual_date_obj <= end_dt:
                    include_record = True
        if include_record:
            filtered_records.append(record)
    # 4. 格式化结果
    result = [record.as_dict() for record in filtered_records]
    # 排序：按计划日期倒序
    result.sort(key=lambda x: x.get('plan_date', '') or '', reverse=True)
    return result


class KnowBuildUrlTable(db_store.BaseModel):
    __tablename__ = "know_build_url_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True)
    know_type = Column(String(64))
    url_title = Column(String(64))
    url_link = Column(String(256))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@db_store.session_safe_crawler
def add_know_build_url_table_know_build_url_list(*args, **kwargs):
    return __add_know_build_url_table_know_build_url_list


def __add_know_build_url_table_know_build_url_list(session, know_build_url_list):
    if len(know_build_url_list) == 0:
        return
    session.query(KnowBuildUrlTable).delete(synchronize_session=False)
    for know_build_url_item in know_build_url_list:
        new_know_build_url_model = KnowBuildUrlTable(**know_build_url_item)
        session.add(new_know_build_url_model)


@db_store.session_safe_crawler
def query_know_build_url_table_know_bulid_url_list_by_know_type(*args, **kwargs):
    return __query_know_build_url_table_know_bulid_url_list_by_know_type


@db_store.session_safe_crawler
def query_know_build_url_table_know_build_url_list_by_know_type(*args, **kwargs):
    return __query_know_build_url_table_know_build_url_list_by_know_type


def __query_know_build_url_table_know_build_url_list_by_know_type(session, know_type=None):
    query = session.query(KnowBuildUrlTable)
    # 如果指定了 know_type，则添加过滤条件
    if know_type:
        query = query.filter(KnowBuildUrlTable.know_type == know_type)
    # 执行查询
    results = query.all()
    # 转换为字典列表并返回
    return [item.as_dict() for item in results if item]



db_store.init_db()