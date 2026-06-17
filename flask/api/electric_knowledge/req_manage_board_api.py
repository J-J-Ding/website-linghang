import logging

from flask import request, jsonify
from electric_knowledge.utils_pub import pub_generate_date_range, pub_get_employ_name
from electric_knowledge.req_manage_board_data_service import update_req_manage_board_pr_info_table_pr_info_list, del_req_manage_board_pr_info_table_by_script_update_date,\
query_req_manage_board_pr_info_table_pr_split_summary_data_list, update_req_manage_board_pr_split_summary_table_data_list, query_req_manage_board_pr_split_summary_table_line_data_list_by_preplanning_and_date, \
query_req_manage_board_pr_split_summary_table_table_data_list_by_preplanning_and_date, query_req_manage_board_pr_split_summary_table_preplanning_list, query_req_manage_board_pr_split_detail_table_table_data_list_by_preplanning_and_date, \
update_req_manage_check_pr_info_table_check_pr_info_list, update_req_manage_check_pr_info_table_handle_pr_info_list, query_req_manage_check_pr_info_table_by_filter_dict, \
query_req_manage_check_pr_info_table_value_dict_by_field_list, update_req_manage_check_pr_info_table_cal_field, \
update_req_manage_check_pr_summary_table_data_list, query_req_manage_check_pr_summary_table_by_date_range_and_preplanning, \
update_req_manage_check_pr_info_table_man_fields_by_id_list


logger = logging.getLogger("Logger")


def service_update_pr_info_list():
    request_body = request.get_json() or {}
    pr_info_list = request_body.get("pr_info_list", [])
    update_req_manage_board_pr_info_table_pr_info_list(pr_info_list)
    return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_del_pr_info_list_by_script_update_date():
    request_body = request.get_json() or {}
    script_update_date = request_body.get("script_update_date", "")
    if script_update_date:
        del_req_manage_board_pr_info_table_by_script_update_date(script_update_date)
    return jsonify({"code": 200, "status": "success", "message": "删除成功"})


def service_update_req_manage_board_pr_split_summary_data_list():
    request_body = request.get_json() or {}
    summary_date = request_body.get("summary_date", "")
    if summary_date:
        summary_data_list = query_req_manage_board_pr_info_table_pr_split_summary_data_list(summary_date)
        update_req_manage_board_pr_split_summary_table_data_list(summary_data_list)
    else:
        logger.error(f"缺少日期{summary_date}")
    return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_query_preplanning_list():
    data_list = query_req_manage_board_pr_split_summary_table_preplanning_list()
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data_list})


def service_query_req_manage_board_pr_split_summary_line_data_list_by_preplanning_and_date():
    request_body = request.get_json() or {}
    preplanning_list = request_body.get("preplanning_list", "")
    start_date = request_body.get("start_date", "")
    end_date = request_body.get("end_date", "")
    auto_field = request_body.get("auto_field", "")
    standard_field = request_body.get("standard_field", "")
    obj_field_name = f"{auto_field}_{standard_field}_num"
    date_list = pub_generate_date_range(start_date, end_date)
    data_list = query_req_manage_board_pr_split_summary_table_line_data_list_by_preplanning_and_date(preplanning_list, date_list, obj_field_name)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data_list})


def service_query_req_manage_board_pr_split_summary_table_data_list_by_preplanning_and_date():
    request_body = request.get_json() or {}
    preplanning_list = request_body.get("preplanning_list", "")
    start_date = request_body.get("start_date", "")
    end_date = request_body.get("end_date", "")
    data_list = query_req_manage_board_pr_split_summary_table_table_data_list_by_preplanning_and_date(preplanning_list, start_date, end_date)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data_list})


def service_query_req_manage_board_pr_split_detail_table_data_list_by_preplanning_and_date():
    request_body = request.get_json() or {}
    preplanning = request_body.get("preplanning", "")
    auto_field = request_body.get("auto_field", "")
    standard_field = request_body.get("standard_field", "")
    start_date = request_body.get("start_date", "")
    end_date = request_body.get("end_date", "")
    data_list = query_req_manage_board_pr_split_detail_table_table_data_list_by_preplanning_and_date(preplanning, auto_field, standard_field, start_date, end_date)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data_list})


def service_update_req_manage_check_pr_info_table_check_pr_info_list():
    request_body = request.get_json() or {}
    check_pr_info_list = request_body.get("data_list", "")
    update_req_manage_check_pr_info_table_check_pr_info_list(check_pr_info_list)
    return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_update_req_manage_check_pr_info_table_handle_pr_info_list():
    request_body = request.get_json() or {}
    script_update_date = request_body.get("script_update_date", "")
    handle_date = request_body.get("handle_date", "")
    update_count = update_req_manage_check_pr_info_table_handle_pr_info_list(script_update_date, handle_date)
    return jsonify({"code": 200, "status": "success", "message": "更新成功", "data": {"update_count": update_count}})


def service_query_req_manage_check_pr_info_table_by_filter_dict():
    request_body = request.get_json() or {}
    filter_dict = request_body.get("filter_dict", {})
    date_range_dict = request_body.get("date_range_dict", {})
    pr_info_list = query_req_manage_check_pr_info_table_by_filter_dict(filter_dict, date_range_dict)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": {"pr_info_list": pr_info_list}})


def service_query_req_manage_check_pr_info_table_value_dict_by_field_list():
    request_body = request.get_json() or {}
    field_list = request_body.get("field_list", [])
    value_dict = query_req_manage_check_pr_info_table_value_dict_by_field_list(field_list)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": {"value_dict": value_dict}})


def service_update_req_manage_check_pr_info_table_cal_field():
    update_req_manage_check_pr_info_table_cal_field()
    return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_update_req_manage_check_pr_summary_table_data_list():
    request_body = request.get_json() or {}
    summary_date = request_body.get("summary_date", "")
    if summary_date:
        update_req_manage_check_pr_summary_table_data_list(summary_date)
        return jsonify({"code": 200, "status": "success", "message": "汇总统计完成"})
    else:
        logger.error(f"缺少日期参数")
        return jsonify({"code": 400, "status": "error", "message": "缺少日期参数"})


def service_query_req_manage_check_pr_summary_table_by_date_range_and_preplanning():
    request_body = request.get_json() or {}
    start_date = request_body.get("start_date", "")
    end_date = request_body.get("end_date", "")
    requirementpreplanning_list = request_body.get("requirementpreplanning_list", [])
    data_list = query_req_manage_check_pr_summary_table_by_date_range_and_preplanning(start_date, end_date, requirementpreplanning_list)
    return jsonify({"code": 200, "status": "success", "message": "查询成功", "data": data_list})


def service_update_req_manage_check_pr_info_table_man_fields_by_id_list():
    """
    根据 ID 列表批量更新记录的 man_*字段（人工标注字段）
    POST 请求，JSON Body 格式：
    {
        "man_problem_flag": "是否问题",  // 可选，为空则不更新
        "man_handle_person": "整改责任人",  // 可选，为空则不更新
        "man_handle_date": "整改截止日期",  // 可选，为空则不更新
        "man_handle_flag": "是否已整改",  // 可选，为空则不更新
        "id_list": [1, 2, 3]  // 必填，记录 ID 列表
    }
    注意：man_update_person 从请求头 X-Emp-No 自动获取，man_update_date 由后端自动生成（精确到秒）
    """
    from datetime import datetime
    request_body = request.get_json() or {}
    # 提取参数
    id_list = request_body.get("id_list", [])
    man_problem_flag = request_body.get("man_problem_flag")
    man_handle_person = request_body.get("man_handle_person")
    man_handle_date = request_body.get("man_handle_date")
    man_handle_flag = request_body.get("man_handle_flag")
    # 从请求头获取工号
    employ_no = request.headers.get('X-Emp-No')
    # 基础校验
    if not id_list:
        logger.error("ID 列表为空")
        return jsonify({"code": 400, "status": "error", "message": "ID 列表不能为空"})
    if not employ_no:
        logger.error("请求头中缺少 X-Emp-No")
        return jsonify({"code": 400, "status": "error", "message": "请求头中缺少 X-Emp-No"})
    # 调用 pub_get_employ_name 获取姓名并拼接工号，格式："刘威 10139282"
    man_update_person = pub_get_employ_name(employ_no)
    # 后端自动生成 man_update_date（精确到秒）
    man_update_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 构建更新数据字典
    update_data = {
        "id_list": id_list,
        "man_update_person": man_update_person,
        "man_update_date": man_update_date,
        "man_problem_flag": man_problem_flag,
        "man_handle_person": man_handle_person,
        "man_handle_date": man_handle_date,
        "man_handle_flag": man_handle_flag,
    }
    # 调用服务层函数
    updated_count = update_req_manage_check_pr_info_table_man_fields_by_id_list(update_data)
    return jsonify({
        "code": 200,
        "status": "success",
        "message": f"成功更新 {updated_count} 条记录",
        "data": {"update_count": updated_count}
    })
