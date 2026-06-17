import re
import time
import json
import calendar
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from knowledge_dashboard import know_table


# 配置日志记录
logger = logging.getLogger(__name__)


def service_query_comp_tree_board_graph_sum_data_dict(page_type, data_type, start_date, end_date):
    # 1. 获取原始查询数据
    raw_data_list = know_table.query_know_comp_tree_board_table_comp_tree_board_sum_list_everyday(start_date, end_date, page_type, data_type)
    # 2. 数据预处理：提取唯一日期（升序）和唯一领域
    sorted_dates = sorted({item["date"] for item in raw_data_list})
    all_fields = sorted({item["field_name"] for item in raw_data_list})
    # 3. 构建快速查询映射：(日期, 领域) -> 累计值
    date_field_map = {(item["date"], item["field_name"]): item["value"] for item in raw_data_list}
    # 4. 构建【累计数据】结构（直接对应左图"各领域已定稿累计趋势"）
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
    # 5. 构建【每日新增数据】结构（直接对应右图"各领域每日新增已定稿"）
    incremental_series = []
    for field in all_fields:
        inc_data = []
        for idx, date in enumerate(sorted_dates):
            if idx == 0:
                # 首日无前置数据，增量默认0
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


def service_query_comp_tree_board_table_sum_data_dict(page_type, start_date, end_date):
    return know_table.query_know_comp_tree_board_table_comp_tree_board_sum_list_twoday(start_date, end_date, page_type)


def service_query_comp_tree_board_table_cumulative_detail_list(field_name, page_type, page_status, script_date):
    return know_table.query_know_comp_tree_page_table_comp_tree_page_list_by_field_name_page_status_page_type_script_date(field_name, page_type, page_status, script_date)


def service_query_comp_tree_board_table_change_detail_list(field_name, page_type, page_status, start_date, end_date):
    return know_table.query_know_comp_tree_page_table_change_detail_list_by_start_date_and_end_date(field_name, page_type, page_status, start_date, end_date)
