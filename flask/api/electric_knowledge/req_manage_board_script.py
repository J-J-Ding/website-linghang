import os
import json
import re
import requests

import pandas as pd
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta


LINGHANG_BASE_URL = "http://10.239.69.183:3001"
SCRIPT_UPDATE_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")
BJ_OFFSET = timedelta(hours=8)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"



def sync_pr_info_to_linghang(user_num, user_token):
    """
    全量查询 PR 信息并同步到领航系统。
    """
    pr_info_list = get_pr_info_list(user_num, user_token)
    send_pr_info_list(pr_info_list)
    del_pr_info_list_by_script_update_date(SCRIPT_UPDATE_DATE)
    return pr_info_list


def auto_classify_pr_to_board_global_status(user_num, pr_info_list):
    all_board_info_list = get_all_board_info_list()
    global_status_board_name_list = get_global_status_board_name_list()

    if not all_board_info_list or not global_status_board_name_list:
        print("数据异常：单板信息或全局状态列表为空")
        return

    all_board_info_dict = {
        board_info_item.get("board").split('(', 1)[0]: board_info_item
        for board_info_item in all_board_info_list
        if "test" not in board_info_item.get("board", "")
    }


    def extract_board_names_from_title(system_title):
        """从 PR 标题中提取单板名称列表"""
        # 规则：M+ 数字+(后面必须要有大写字母)，且整体长度不低于 5，结尾如果是 X 数字则去掉
        # 第一步：先匹配所有符合 M+ 数字 + 大写字母开头的候选项
        raw_candidates = re.findall(r'M\d[A-Z][A-Za-z0-9]+', system_title.upper())

        # 第二步：处理每个候选项，去掉末尾的 X 数字模式或单独的 X
        processed_candidates = []
        for candidate in raw_candidates:
            # 使用正则去掉末尾的 X 数字模式（X 后跟 1 位或多位数字）或单独的 X
            cleaned = re.sub(r'X\d*$', '', candidate)
            # 确保清理后长度仍不低于 5
            if len(cleaned) >= 5:
                processed_candidates.append(cleaned)

        return processed_candidates

    for board_name, board_info_dict in all_board_info_dict.items():
        raw_board_name = board_info_dict.get("board")
        if not raw_board_name:
            continue

        # 检查是否已在全局状态表中
        if raw_board_name in global_status_board_name_list:
            print(f"{raw_board_name} 已在单板全局状态表中存在")
        else:
            print(f"{raw_board_name} 不在单板全局状态表中，需构造批量导入文件")
            board_model = board_info_dict.get("单板业务模型", "")
            if board_model == "MGR_C-MGR_L|MGR_L":
                board_model = "MGR_C,MGR_L"
            board_model = board_model.replace('|', ',')
            board_feature_list = query_board_feature_list_by_board_model(board_model)
            feature_excel_path = generate_board_global_status_feature_excel(board_info_dict, board_feature_list)
            upload_board_global_status_feature_excel(user_num, feature_excel_path)

        # 筛选与当前单板相关的 PR
        board_pr_info_list = []
        for pr_info_item in pr_info_list:
            system_id = pr_info_item.get("system_id", "")
            system_title = pr_info_item.get("system_title", "")
            # 实时从标题中提取单板名称列表
            title_board_names = extract_board_names_from_title(system_title)
            # 如果当前 board_name 在标题的单板名称列表中，则是相关 PR
            if board_name in title_board_names:
                board_pr_info_list.append(["产品需求", system_id, system_title])
        if board_pr_info_list:
            print(f"{raw_board_name} 存在 {len(board_pr_info_list)} 条需导入的需求")
            pr_excel_path = generate_board_global_status_pr_excel(raw_board_name, board_pr_info_list)
            # 上传为 new 和 old（根据现有逻辑）
            upload_board_global_status_pr_excel(user_num, pr_excel_path, raw_board_name, "new")
            upload_board_global_status_pr_excel(user_num, pr_excel_path, raw_board_name, "old")
        else:
            print(f"{raw_board_name} 无相关需求")


def utc_to_beijing_str(utc_str: str) -> str:
    if not utc_str:
        return ""
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    return (dt + BJ_OFFSET).strftime(DATETIME_FORMAT)


def get_pr_info_list(user_num, user_token):
    # url = "https://icosg.dt.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/OTNAG/queries/after_work_items"  # OTNAG
    url = "https://icosg.dt.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/OTNSW/queries/after_work_items"  # OTNSW
    # 基础请求体（第一次请求不包含searchAfter）
    base_body = {
        "queryCondition": {
            "depth": 0,
            "relatedOptions": "linksOneHopMustContain",
            "relatedType": [],
            "removeTop": False,
            "sourceClauses": [
                {
                    "field": "System_WorkItemType",
                    "leftGroup": 0,
                    "logicalOperator": "",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": "PR"
                },
                {
                    "field": "System_State",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "not in",
                    "rightGroup": 0,
                    "value": "已拒绝,已废弃"
                },
                {
                    "field": "System_AreaPath",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "=",
                    "rightGroup": 0,
                    # "value": "bdv_106092" # OTNAG
                    "value": "bdv_105454"  # OTNSW
                },
                {
                    "leftGroup": 0,
                    "rightGroup": 0,
                    "logicalOperator": "AND",
                    "field": "System_CreatedDate",
                    "operator": ">=",
                    "value": "2022-01-01"
                }
            ],
            "targetClauses": [],
            "treeOptions": "top",
            "type": "flat"
        },
        "selectItems": [
            {"key": "System_Id"},
            {"key": "System_State"},
            {"key": "System_CreatedDate"},
            {"key": "System_CreatedBy"},
            {"key": "System_ChangedDate"},
            {"key": "System_ChangedBy"},
            {"key": "System_AppointedTo"},
            {"key": "System_AreaPath"},
            {"key": "Team"},
            {"key": "System_Title"},
            {"key": "BelongProduct"},
            {"key": "RequirementPrePlanning"},
            {"key": "System_Description_html"},
            {"key": "AcceptanceCriteria_html"},
            {"key": "RequirementAnalysisOwner"},
            {"key": "SpecificationByExampleUrl"},
            {"key": "SpecificationByExampleState"},
            {"key": "DesignSpecificationUrl"},
            {"key": "DesignState"},
            {"key": "FeatureUrl"},
            {"key": "BelongFeatureCatalog"},
            {"key": "FeatureId"},
            {"key": "FeatureName_Cn"},
            {"key": "CheckResultOfChipScheme"},
            {"key": "IsAutoCreated"},
            {"key": "AssessResult_First"},
            {"key": "ReuseDegree"},
        ],
        "sortItems": [
            {
                "isAscending": "false",
                "key": "System_CreatedDate"
            }
        ],
        "sortValue": True,
        "pageNo": 1,
        "pageSize": 10000
    }

    headers = {
        "X-Tenant-Id": "ZTE",
        "X-Emp-No": user_num,
        "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id": "zh_CN",
        "Content-Type": "application/json",
        "X-Auth-Value": user_token
    }

    pr_info_list = []
    current_search_after = None

    while True:
        # 构造当前请求体
        body = base_body.copy()
        if current_search_after is not None:
            body["searchAfter"] = current_search_after

        # 发送请求
        response = requests.post(url, json=body, headers=headers)

        # 检查请求状态
        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")

        # 解析响应
        data = response.json()

        # 提取当前页数据
        items = data.get("bo", {}).get("result", {}).get("items", [])
        for item in items:
            pr_info_list.append({
                "system_id": item.get("System_Id"),
                "system_state": item.get("System_State", {}).get("name", ""),
                "system_createddate": utc_to_beijing_str(item.get("System_CreatedDate")),
                "system_createdby": item.get("System_CreatedBy", {}).get("nameDisplayLong", ""),
                "system_changeddate": utc_to_beijing_str(item.get("System_ChangedDate")),
                "system_changedby": item.get("System_ChangedBy", {}).get("nameDisplayLong", ""),
                "system_appointedto": item.get("System_AppointedTo", {}).get("nameDisplayLong", ""),
                "system_areapath": item.get("System_AreaPath", {}).get("label", ""),
                "team": item.get("Team", {}).get("label", ""),
                "system_title": item.get("System_Title"),
                "belongproduct": item.get("BelongProduct", {}).get("label", ""),
                "requirementpreplanning": item.get("RequirementPrePlanning"),
                "system_description_html": item.get("System_Description_html"),
                "acceptancecriteria_html": item.get("AcceptanceCriteria_html"),
                "requirementanalysisowner": item.get("RequirementAnalysisOwner", {}).get("nameDisplayLong", ""),
                "specificationbyexampleurl": item.get("SpecificationByExampleUrl"),
                "specificationbyexamplestate": item.get("SpecificationByExampleState"),
                "designspecificationurl": item.get("DesignSpecificationUrl"),
                "designstate": item.get("DesignState"),
                "featureurl": item.get("FeatureUrl"),
                "belongfeaturecatalog": item.get("BelongFeatureCatalog"),
                "featureid": item.get("FeatureId"),
                "featurename_cn": item.get("FeatureName_Cn"),
                "checkresultofchipscheme": item.get("CheckResultOfChipScheme"),
                "isautocreated": item.get("IsAutoCreated"),
                "assessresult_first": item.get("AssessResult_First"),
                "reusedegree": item.get("ReuseDegree"),
                "script_update_date": SCRIPT_UPDATE_DATE,
            })

        # 检查是否还有下一页
        # pprint(items[0])
        # pprint(pr_info_list[0])
        print("完成1次查询")
        if len(items) == 10000:
            current_search_after = items[-1].get("sortValues")
        else:
            break  # 没有下一页则退出循环
    return pr_info_list


def send_pr_info_list(pr_info_list):
    batch_size = 4000
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_pr_info_list"
    headers = {'Content-Type': 'application/json'}
    results = []

    # 分批处理
    for i in range(0, len(pr_info_list), batch_size):
        batch = pr_info_list[i:i + batch_size]
        try:
            response = requests.post(
                url,
                data=json.dumps({"pr_info_list": batch}),
                headers=headers,
            )
            response.raise_for_status()
            result = {
                "status_code": response.status_code,
                "response_json": response.json() if response.content else None,
                "batch_index": i // batch_size,
                "batch_size": len(batch)
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"[Batch {i // batch_size}] Request failed: {error_msg}")
            result = {
                "status_code": None,
                "error": error_msg,
                "batch_index": i // batch_size,
                "batch_size": len(batch)
            }
        results.append(result)
    return results


def del_pr_info_list_by_script_update_date(script_update_date):
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/del_pr_info_list_by_script_update_date"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps({"script_update_date": script_update_date}), headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Request failed: {e}")
    return None


def get_all_board_info_list():
    query_url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams"
    headers = {'accept': 'application/json'}
    try:
        response = requests.get(query_url, headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Request failed: {e}")
        return []


def get_global_status_board_name_list():
    query_url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/front_board_whole_status_data_service/querySimpleBoardGlobalStatusTree"
    headers = {'accept': 'application/json'}
    try:
        response = requests.get(query_url, headers=headers)
        response.raise_for_status()
        query_data = response.json().get("data", {})
        global_status_board_name_list = []
        def _traverse(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    _traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, str):
                        global_status_board_name_list.append(item.strip())
        _traverse(query_data)
        return list(set(global_status_board_name_list))
    except Exception as e:
        print(f"Request failed: {e}")
        return []


def query_board_feature_list_by_board_model(board_model):
    if not board_model: return []
    board_model_set = set(board_model.split(","))
    board_feature_list = []
    query_url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardByParams"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    payload = {"relatedBoardModel": board_model}

    try:
        response = requests.post(query_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        raw_data = response.json().get("data", [])

        for raw_item in raw_data:
            feature_name = raw_item.get("feature")
            children_list = raw_item.get("childrenList", [])
            # 收集当前 feature 下所有匹配的子特性
            matched_sub_features = []
            for sub_item in children_list:
                # 检查是否有任一 board model 在该子项中值为 "2"
                if any(sub_item.get(model) == "2" for model in board_model_set):
                    sub_feature = sub_item.get("subFeature")
                    if sub_feature is not None:
                        matched_sub_features.append(sub_feature)
            # 如果有匹配的子特性，则将子特性和父特性都加入结果
            if matched_sub_features:
                board_feature_list.append(feature_name)
                board_feature_list.extend(matched_sub_features)
        return board_feature_list
    except Exception as e:
        print(f"Request failed: {e}")
        return []


def generate_board_global_status_feature_excel(board_info_dict, board_feature_list):
    # 获取当前脚本所在目录的绝对路径
    current_file = Path(__file__).resolve()
    # 向上回退 6 层到达 /otn_ai/test/zjp/
    file_root = current_file.parents[6]
    # 构建输出目录
    output_dir = file_root / "script" / "board_global_status_feature_excel"
    output_dir.mkdir(parents=True, exist_ok=True)
    # 文件名：单板名 + 日期
    board_name = board_info_dict.get("board", "unknown_board")
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_{board_name}_feature.xlsx"
    # 构造 Excel 数据
    columns = ["产品因子取值", "板卡类型因子取值", "单板业务模型因子取值", "单板名称", "特性/子特性", "关联RDC标识"]
    data = [
        [
            board_info_dict.get("产品"),
            board_info_dict.get("板卡类型"),
            board_info_dict.get("单板业务模型"),
            board_name,
            "所有支持的特性/子特性",
            ""
        ]
    ]
    for feature in board_feature_list:
        data.append(["", "", "", "",feature,""])
    # 保存 Excel
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Excel文件生成成功!路径: {output_path}")
    return output_path


def upload_board_global_status_feature_excel(user_num, file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"上传失败：文件不存在 - {file_path}")
        return False
    # 构建上传 URL
    upload_url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/front_board_whole_status_data_service/importExcelbaseBoardWholeStatusData"
    headers = {
        "X-Emp-No": user_num,
        "accept": "application/json"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            print(f"准备上传单板特性清单文件: {file_path}")
            response = requests.post(upload_url, headers=headers, files=files, timeout=3000)
        # 检查 HTTP 状态
        response.raise_for_status()
        # 尝试解析响应（有些接口成功只返回 200 无 body）
        try:
            result = response.json()
            # 根据常见后端设计，可能有 code 字段判断逻辑成功
            if result.get("code") == 200 or result.get("success") is True:
                print(f"Excel 文件上传成功！路径: {file_path}")
                return True
            else:
                print(f"接口返回业务错误: {result}")
                return False
        except ValueError:
            # 无 JSON 响应，但 HTTP 200 视为成功
            print(f"Excel 文件上传成功（无返回体）！路径: {file_path}")
            return True
    except Exception as e:
        print(f"上传请求失败: {e}")
        return False


def generate_board_global_status_pr_excel(board_name, board_pr_list):
    # 获取当前脚本所在目录的绝对路径
    current_file = Path(__file__).resolve()
    # 向上回退 6 层到达 /otn_ai/test/zjp/
    file_root = current_file.parents[6]
    # 构建输出目录
    output_dir = file_root / "script" / "board_global_status_pr_excel"
    output_dir.mkdir(parents=True, exist_ok=True)
    # 文件名：单板名 + 日期
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_{board_name}_pr.xlsx"
    # 构造 Excel 数据
    columns = ["工作项类型", "标识", "标题"]
    # 保存 Excel
    df = pd.DataFrame(board_pr_list, columns=columns)
    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Excel文件生成成功!路径: {output_path}")
    return output_path


def upload_board_global_status_pr_excel(user_num, file_path, board_name, feature_type):
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"上传失败：文件不存在 - {file_path}")
        return False
    # 构建上传 URL
    upload_url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/front_board_whole_status_data_service/importOldBoardWholeStatusData"
    headers = {
        "X-Emp-No": user_num,
        "board": board_name,
        "dataType": feature_type,
        "accept": "application/json"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            print(f"准备上传单板需求文件: {file_path}")
            response = requests.post(upload_url, headers=headers, files=files, timeout=3000)
        # 检查 HTTP 状态
        response.raise_for_status()
        # 尝试解析响应（有些接口成功只返回 200 无 body）
        try:
            result = response.json()
            # 根据常见后端设计，可能有 code 字段判断逻辑成功
            if result.get("code") == 200 or result.get("success") is True:
                print(f"Excel 文件上传成功！路径: {file_path}")
                return True
            else:
                print(f"接口返回业务错误: {result}")
                return False
        except ValueError:
            # 无 JSON 响应，但 HTTP 200 视为成功
            print(f"Excel 文件上传成功（无返回体）！路径: {file_path}")
            return True
    except Exception as e:
        print(f"上传请求失败: {e}")
        return False


def update_req_manage_board_pr_split_summary_data(start_date, end_date):
    date_list = generate_date_range(start_date, end_date)
    for date_item in date_list:
        print(f"正在统计{date_item}的自动拆分数据")
        send_summary_date_to_linghang(date_item)


def generate_date_range(start_date, end_date):
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        print(f"日期格式错误，应为 'YYYY-MM-DD' 格式: {e}")
        return []

    if start_dt > end_dt:
        print(f"开始日期({start_date})不能晚于结束日期({end_date})")
        return []

    date_list = []
    current_dt = start_dt
    while current_dt <= end_dt:
        date_list.append(current_dt.strftime("%Y-%m-%d"))
        current_dt += timedelta(days=1)
    return date_list


def send_summary_date_to_linghang(summary_date):
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_req_manage_board_pr_split_summary_data_list"
    headers = {"Content-Type": "application/json"}
    payload = {"summary_date": summary_date}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        success = response.status_code == 200
        if not success:
            print(f"[失败] {summary_date} → 状态码: {response.status_code}")
        else:
            print(f"[成功] {summary_date} → 状态码: {response.status_code}")
    except Exception as e:
        print(f"[异常] {summary_date} → 错误: {e}")


def get_current_date():
    """
    获取当前最新的日期，格式为 YYYY-MM-DD
    """
    # 获取当前的日期和时间
    now = datetime.now()
    # 将日期格式化为字符串 '2026-02-25' 这种格式
    # %Y 代表四位年份，%m 代表两位月份，%d 代表两位日期
    date_str = now.strftime("%Y-%m-%d")
    return date_str


def start_run():
    user_num = '10305454'
    user_token = '8edb980981dd9d737db9eea61a0f8ed3'
    # 全量查询并获取PR信息
    pr_info_list = sync_pr_info_to_linghang(user_num, user_token)
    # 自动分类PR到单板全局状态
    auto_classify_pr_to_board_global_status(user_num, pr_info_list)
    # 统计需求自动拆分的数据
    update_req_manage_board_pr_split_summary_data("2026-01-01", get_current_date())


if __name__ == "__main__":
    start_run()
