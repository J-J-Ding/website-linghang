import logging
from flask import request, jsonify
from feature_dashboard.feature_service import (
    service_query_feature_tree_board_sum_latest_list,
    service_query_feature_tree_board_detail_list,
    service_query_feature_tree_board_sum_list,
    service_query_feature_tree_board_sum_detail_list,
    service_query_feature_tree_board_graph_sum_data_dict,
    service_query_feature_tree_board_table_sum_data_dict,
    service_query_feature_tree_board_table_cumulative_detail_list,
)


logger = logging.getLogger(__name__)


def _ok(data):
    """构造成功响应，统一返回格式 {result: True, code: 0, body: {data: ...}}"""
    return jsonify({"result": True, "code": 0, "errorCode": "0", "msg": "操作成功", "body": {"data": data}})


def _bad(msg, http_code=400):
    """构造失败响应，统一返回格式 {result: False, code: 1, msg: ...}，默认 HTTP 400"""
    return (jsonify({"result": False, "code": 1, "errorCode": "1", "msg": msg, "body": {"data": None}}), http_code)


def query_feature_tree_board_graph_sum_data_dict():
    """
    查询特性树看板图表汇总数据（累计趋势 + 每日增量）

    GET /know/query_feature_tree_board_graph_sum_data_dict/

    请求参数:
        page_type (str): 页面类型，analysis=特性分析, scheme=特性方案
        data_type (str): 数据指标类型，如 finish_rate(定稿率) 等
        start_date (str): 起始日期，格式 YYYY-MM-DD
        end_date (str): 结束日期，格式 YYYY-MM-DD

    返回:
        各领域在指定日期范围内的累计趋势数据和每日增量数据
    """
    try:
        page_type = request.args.get("page_type")
        data_type = request.args.get("data_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        return _ok(service_query_feature_tree_board_graph_sum_data_dict(page_type, data_type, start_date, end_date))
    except Exception as e:
        return _bad(f"查询失败: {str(e)}", 500)


def query_feature_tree_board_table_sum_data_dict():
    """
    查询特性树看板表格汇总数据（按领域分组的每日统计）

    GET /know/query_feature_tree_board_table_sum_data_dict/

    请求参数:
        page_type (str): 页面类型，analysis=特性分析, scheme=特性方案
        start_date (str): 起始日期，格式 YYYY-MM-DD
        end_date (str): 结束日期，格式 YYYY-MM-DD

    返回:
        各领域在指定日期范围内的表格汇总数据，包含前后日对比及增量
    """
    try:
        page_type = request.args.get("page_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        return _ok(service_query_feature_tree_board_table_sum_data_dict(page_type, start_date, end_date))
    except Exception as e:
        return _bad(f"查询失败: {str(e)}", 500)


def query_feature_tree_board_table_cumulative_detail_list():
    """
    查询特性树看板累计明细列表（按领域、页面类型、状态筛选页面记录）

    GET /know/query_feature_tree_board_table_cumulative_detail_list/

    请求参数:
        field_name (str): 领域名称，如 L0/L1/L2/智控/支撑
        page_type (str): 页面类型，analysis=特性分析, scheme=特性方案
        page_status (str): 页面状态，如 initial/reviewed/revision/finish/blank
        script_date (str): 脚本采集日期，格式 YYYY-MM-DD

    返回:
        符合筛选条件的特性树页面记录列表
    """
    try:
        field_name = request.args.get("field_name")
        page_type = request.args.get("page_type")
        page_status = request.args.get("page_status")
        script_date = request.args.get("script_date")
        if not all([field_name, page_type, page_status, script_date]):
            return _bad("缺少必需参数: field_name, page_type, page_status, script_date")
        return _ok(service_query_feature_tree_board_table_cumulative_detail_list(field_name, page_type, page_status, script_date))
    except Exception as e:
        return _bad(f"查询失败: {str(e)}", 500)


def query_feature_tree_board_table_change_detail_list():
    """
    查询特性树看板变更明细列表（下钻查询指定日期、领域、页面类型的详细记录）

    GET/POST /know/query_feature_tree_board_table_change_detail_list/

    请求参数:
        field_name (str): 领域名称，如 L0/L1/L2/智控/支撑
        page_type (str): 页面类型，必须为 analysis 或 scheme
        date (str): 查询日期，格式 YYYY-MM-DD

    返回:
        指定条件下特性树页面的详细记录列表
    """
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            field_name = data.get("field_name")
            page_type = data.get("page_type")
            date = data.get("date")
        else:
            field_name = request.args.get("field_name")
            page_type = request.args.get("page_type")
            date = request.args.get("date")
        if not field_name:
            return _bad("缺少必需参数: field_name")
        if not page_type:
            return _bad("缺少必需参数: page_type")
        if not date:
            return _bad("缺少必需参数: date")
        if page_type not in ["analysis", "scheme"]:
            return _bad(f"page_type 必须为 analysis 或 scheme，当前值: {page_type}")
        result_data = service_query_feature_tree_board_sum_detail_list(field_name, page_type, date)
        return _ok(result_data)
    except Exception as e:
        logger.error(f"查询异常: {str(e)}", exc_info=True)
        return _bad(f"查询失败: {str(e)}", 500)
