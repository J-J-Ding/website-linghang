import logging
from flask import request
from knowledge_dashboard import pub
from knowledge_dashboard.know_service import service_query_comp_tree_board_graph_sum_data_dict, service_query_comp_tree_board_table_sum_data_dict, \
service_query_comp_tree_board_table_cumulative_detail_list, service_query_comp_tree_board_table_change_detail_list


# 配置日志记录器
logger = logging.getLogger(__name__)


def query_comp_tree_board_graph_sum_data_dict():
    try:
        page_type = request.args.get("page_type")
        data_type = request.args.get("data_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        return pub.pub_ok(service_query_comp_tree_board_graph_sum_data_dict(page_type, data_type, start_date, end_date))
    except Exception as e:
        logger.error(f"查询失败：{str(e)}")
        return pub.pub_bad(f"查询失败：{str(e)}", 500)


def query_comp_tree_board_table_sum_data_dict():
    try:
        page_type = request.args.get("page_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        return pub.pub_ok(service_query_comp_tree_board_table_sum_data_dict(page_type, start_date, end_date))
    except Exception as e:
        logger.error(f"查询失败：{str(e)}")
        return pub.pub_bad(f"查询失败：{str(e)}", 500)


def query_comp_tree_board_table_cumulative_detail_list():
    try:
        field_name = request.args.get("field_name")
        page_type = request.args.get("page_type")
        page_status = request.args.get("page_status")
        script_date = request.args.get("script_date")
        if not all([field_name, page_type, page_status, script_date]):
            return pub.pub_bad("缺少必需参数：field_name, page_status, page_type, script_date")
        return pub.pub_ok(service_query_comp_tree_board_table_cumulative_detail_list(field_name, page_type, page_status, script_date))
    except Exception as e:
        logger.error(f"查询失败：{str(e)}")
        return pub.pub_bad(f"查询失败：{str(e)}", 500)


def query_comp_tree_board_table_change_detail_list():
    try:
        field_name = request.args.get("field_name")
        page_type = request.args.get("page_type")
        page_status = request.args.get("page_status")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        if not all([field_name, page_type, page_status, start_date, end_date]):
            return pub.pub_bad("缺少必需参数：field_name, page_status, page_type, start_date, end_date")
        return pub.pub_ok(service_query_comp_tree_board_table_change_detail_list(field_name, page_type, page_status, start_date, end_date))
    except Exception as e:
        logger.error(f"查询失败：{str(e)}")
        return pub.pub_bad(f"查询失败：{str(e)}", 500)
