from feature_dashboard import feature_table
from knowledge_dashboard import pub


def service_query_feature_tree_board_sum_latest_list(page_type):
    """
    获取最新一天的特性树看板统计数据
    :param page_type: 页面类型（analysis 或 scheme）
    :return: 各领域最新一天的统计数据（累计值）
    """
    raw_feature_tree_board_list = feature_table.query_know_feature_tree_board_table_latest_feature_tree_board_list()
    feature_tree_board_list = []
    seen_field_names = set()

    for item in raw_feature_tree_board_list:
        latest_data = item
        field_name = latest_data.get("field_name")

        if field_name in seen_field_names:
            continue

        def get_value(field_suffix):
            return latest_data.get(f"{page_type}_{field_suffix}", 0) or 0

        initial_num = get_value("initial_num")
        reviewed_num = get_value("reviewed_num")
        revision_num = get_value("revision_num")
        finish_num = get_value("finish_num")
        blank_num = get_value("blank_num")
        sum_num = get_value("sum_num")
        sum_editor_num = get_value("sum_editor_num")
        sum_edit_num = get_value("sum_edit_num")
        sum_view_visitor_num = get_value("sum_view_visitor_num")
        sum_view_visit_num = get_value("sum_view_visit_num")
        sum_ai_adapt_num = get_value("sum_ai_adapt_num")
        sum_ai_gene_num = get_value("sum_ai_gene_num")

        if not sum_num or sum_num == 0:
            continue

        seen_field_names.add(field_name)

        feature_tree_board_item = {
            "date": latest_data.get("date"),
            "field_name": field_name,
            "sum_num": sum_num,
            "initial_num": initial_num,
            "reviewed_num": reviewed_num,
            "revision_num": revision_num,
            "finish_num": finish_num,
            "blank_num": blank_num,
            "sum_editor_num": sum_editor_num,
            "sum_edit_num": sum_edit_num,
            "sum_view_visitor_num": sum_view_visitor_num,
            "sum_view_visit_num": sum_view_visit_num,
            "sum_ai_adapt_num": sum_ai_adapt_num,
            "sum_ai_gene_num": sum_ai_gene_num,
        }

        feature_tree_board_item["initial_rate"] = f"{pub.pub_get_ratio(feature_tree_board_item['initial_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["reviewed_rate"] = f"{pub.pub_get_ratio(feature_tree_board_item['reviewed_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["revision_rate"] = f"{pub.pub_get_ratio(feature_tree_board_item['revision_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["finish_rate"] = f"{pub.pub_get_ratio(feature_tree_board_item['finish_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["blank_rate"] = f"{pub.pub_get_ratio(feature_tree_board_item['blank_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["per_editor_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_editor_num'], sum_num)}" if sum_num > 0 else "0"
        feature_tree_board_item["per_edit_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_edit_num'], sum_num)}" if sum_num > 0 else "0"
        feature_tree_board_item["per_view_visitor_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_view_visitor_num'], sum_num)}" if sum_num > 0 else "0"
        feature_tree_board_item["per_view_visit_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_view_visit_num'], sum_num)}" if sum_num > 0 else "0"
        feature_tree_board_item["per_ai_adapt_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_ai_adapt_num'], sum_num)}%" if sum_num > 0 else "0%"
        feature_tree_board_item["per_ai_gene_num"] = f"{pub.pub_get_ratio_no_100(feature_tree_board_item['sum_ai_gene_num'], sum_num)}%" if sum_num > 0 else "0%"

        feature_tree_board_list.append(feature_tree_board_item)

    feature_tree_board_list.sort(key=lambda x: x["sum_num"], reverse=True)
    return feature_tree_board_list


def service_query_feature_tree_board_detail_list(field_name, page_status, page_type):
    return feature_table.query_know_feature_tree_page_table_feature_tree_page_list_by_field_name_page_status_page_type(field_name, page_status, page_type)


def service_query_feature_tree_board_table_cumulative_detail_list(field_name, page_type, page_status, script_date):
    return feature_table.query_know_feature_tree_page_table_feature_tree_page_list_by_field_name_page_status_page_type_script_date(field_name, page_type, page_status, script_date)


def service_query_feature_tree_board_sum_list(start_date, end_date, page_type, data_type):
    """
    特性树看板汇总数据趋势查询服务
    :param start_date: 起始日期
    :param end_date: 结束日期
    :param page_type: 页面类型（analysis 或 scheme）
    :param data_type: 数据类型（如 sum_num, finish_num, finish_rate 等）
    :return: ECharts 图表数据列表
    """
    return feature_table.query_know_feature_tree_board_table_feature_tree_board_sum_list_everyday(start_date, end_date, page_type, data_type)


def service_query_feature_tree_board_sum_detail_list(field_name, page_type, date):
    """
    特性树看板汇总数据的下钻查询服务
    :param field_name: 领域名称
    :param page_type: 页面类型（analysis 或 scheme）
    :param date: 查询日期
    :return: 详细记录列表
    """
    return feature_table.query_know_feature_tree_board_table_feature_tree_board_sum_detail_list(field_name, page_type, date)


def service_query_feature_tree_board_graph_sum_data_dict(page_type, data_type, start_date, end_date):
    # 1. 获取原始查询数据
    raw_data_list = feature_table.query_know_feature_tree_board_table_feature_tree_board_sum_list_everyday(start_date, end_date, page_type, data_type)
    # 2. 数据预处理：提取唯一日期（升序）和唯一领域
    sorted_dates = sorted({item["date"] for item in raw_data_list})
    all_fields = sorted({item["field_name"] for item in raw_data_list})
    # 3. 构建快速查询映射：(日期, 领域) -> 累计值
    date_field_map = {(item["date"], item["field_name"]): item["value"] for item in raw_data_list}
    # 4. 构建【累计数据】结构
    cumulative_series = []
    for field in all_fields:
        field_data = [date_field_map.get((date, field), 0.0) for date in sorted_dates]
        cumulative_series.append({
            "name": field,
            "data": field_data,
        })
    cumulative_data = {
        "date_list": sorted_dates,
        "data_list": cumulative_series
    }
    # 5. 构建【每日新增数据】结构
    incremental_series = []
    for field in all_fields:
        inc_data = []
        for idx, date in enumerate(sorted_dates):
            if idx == 0:
                increment = 0.0
            else:
                prev_date = sorted_dates[idx - 1]
                current_val = date_field_map.get((date, field), 0.0)
                prev_val = date_field_map.get((prev_date, field), 0.0)
                increment = current_val - prev_val
            inc_data.append(increment)
        incremental_series.append({
            "name": field,
            "data": inc_data,
        })
    incremental_data = {
        "date_list": sorted_dates,
        "data_list": incremental_series
    }
    # 6. 组装最终返回字典
    return {
        "cumulative_data": cumulative_data,
        "daily_data": incremental_data
    }


def service_query_feature_tree_board_table_sum_data_dict(page_type, start_date, end_date):
    raw_data_list = feature_table.query_know_feature_tree_board_table_feature_tree_board_sum_list_twoday(start_date, end_date, page_type)
    return raw_data_list
