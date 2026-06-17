import os
import json
import httpx
import logging
import requests
import mimetypes
import pandas as pd

from pathlib import Path
from fastmcp import FastMCP
from typing import Dict, Any
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
# 关闭代理，避免内网干扰
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("all_proxy", None)


# 创建 MCP 服务器
mcp = FastMCP("Req Manage Agent MCP Server")
httpx_client = httpx.AsyncClient(timeout=30.0)


@mcp.tool(name="查询指定单板的单板全局状态数据")
def query_board_whole_status_data(board: str):
    """
    接口作用: 查询指定单板的单板全局状态数据

    入参:
        board: 单板名称

    示例: 查询单板M5C4R(80A1H)的单板全局状态数据
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusByParams"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "board": board
        }
        del_key_list = ["board", "boardBusinessModel", "boardType", "create_time", "effective_flag", "id", "operator_person", "parent", "status", "update_time"]
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") != "success":
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
        board_whole_status_data_list = response_data.get("data", [])
        for board_item in board_whole_status_data_list:
            for del_key_item in del_key_list:
                board_item.pop(del_key_item)
            for feature_item in board_item.get("childrenList"):
                for del_key_item in del_key_list:
                    feature_item.pop(del_key_item)
                for subfeature_item in feature_item.get("childrenList"):
                    for del_key_item in del_key_list:
                        subfeature_item.pop(del_key_item)
        return board_whole_status_data_list
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定单板完全交付/未完全交付的特性集合")
def query_board_all_feature_rdc_status(board_name_str: str, rdc_status: str):
    """
    接口作用: 查询指定单板完全交付/未完全交付的特性集合

    入参:
        board_name_str: 单板名称, 如果有多块单板, 中间使用英文逗号分隔
        rdc_status: 特性对应的状态, 如果是查询单板完全交付的特性集合, 传入supported，如果是查询对应单板未完全交付的特性集合，传入not_supported。

    示例: 查询M2U1P单板当前完全交付的特性集合
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/ai_application/process_query_board_all_feature_rdc_status"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": board_name_str,
            "query_mode": rdc_status
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("result", {})
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定单板在某里程碑中已交付/未交付的需求集合")
def query_fault_data_by_feature(board_name: str, preplan_version: str, rdc_status: str):
    """
    接口作用: 查询指定单板在某里程碑中已交付/未交付的需求集合
    入参:
        board_name: 单板名称
        preplan_version: 里程碑名称
        rdc_status: 需求状态(查询已交付需求传入support, 传入未交付需求传入not_support, 查询所有需求传入空)

    示例: 查询M3CB4R在智能OTN V3.00R1中未交付的所有需求
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_whole_status_data_service/query_rdc_list_by_board_name_and_preplan_version"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "board_name": board_name,
            "preplan_version": preplan_version,
            "rdc_status": rdc_status,
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        # 检查返回状态
        if response_data.get("status") == "success":
            rdc_list = response_data.get("data", [])
            object_key_list = ["board", "rdcIdent", "rdcTitle", "requirementPrePlanVersion", "requirementStatus"]
            seen_rdc_ident = set()
            filtered_list = []
            for rdc_item in rdc_list:
                # 提取所需字段，缺失字段设为 None 或保留原值（这里用 .get 保证安全）
                filtered_item = {key: rdc_item.get(key) for key in object_key_list}
                rdc_ident = filtered_item.get("rdcIdent")
                # 如果 rdcIdent 为 None 或空，也可选择保留（根据业务需求），这里按去重逻辑处理
                if rdc_ident in seen_rdc_ident:
                    continue
                seen_rdc_ident.add(rdc_ident)
                filtered_list.append(filtered_item)
            return {"rdc_num": len(filtered_list), "rdc_detail_list": filtered_list}
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询单板树中所有的单板名称")
def query_board_name_list():
    """
    接口作用: 查询所有的单板名称

    示例: 查询所有的单板名称
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams"
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            board_info_list = response_data.get("data")
            return [item.get("board") for item in board_info_list]
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询单板树中指定单板的硬件信息")
def query_board_info_by_board_name(board_name: str):
    """
    接口作用: 查询单板树中指定单板的硬件信息
    入参:
        board_name: 要查找的单板名称
    示例: 查询M1BSO(80CDH)单板的硬件信息
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams"
        headers = {
            "Content-Type": "application/json"
        }
        params = {"board": board_name}
        response = requests.get(url, headers=headers, params=params)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("data", [])
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询单板树中指定单板的客户侧光模块&线路侧光模块")
def query_board_optical_module_info_by_board_name(board_name: str):
    """
    接口作用: 查询指定单板的客户侧光模块&线路侧光模块

    入参:
        board_name: 单板名称

    示例: 查询M1EGEP(7096H)单板的客户侧和线路侧光模块
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams"
        headers = {
            "Content-Type": "application/json"
        }
        params = {"board": board_name}
        response = requests.get(url, headers=headers, params=params)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            board_info_list = response_data.get("data")
            if len(board_info_list) > 0:
                board_info_dict = board_info_list[0]
                return {
                    "board": board_info_dict.get("board"),
                    "客户侧光模块": board_info_dict.get("客户侧光模块"),
                    "线路侧光模块": board_info_dict.get("线路侧光模块")
                }
            else:
                return f"数据库中不存在单板: {board_name}"
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询单板树中使用相同部件的单板")
def query_board_info_by_board_name(factor_type: str, factor_value: str):
    """
    接口作用: 查询单板树中使用相同部件的单板
    入参:
        factor_type: 要找到的单板部件类型（客户侧光层业务、板卡类型、GEARBOX、线路侧光层业务、开销逻辑、单板业务模型、业务FRM芯片、单板支持的子架、产品、时钟芯片、客户侧电层业务、控制逻辑、子卡、单板配置类型、部件承载电层业务模式、物理端口数量、线路侧电层业务、客户侧光模块、单板软件平台、线路侧光模块、单板硬件PCB、交换FRM芯片）
        factor_value: 要查找的单板部件名称
    示例: 查询单板硬件PCB都为PCB(123351852330)的单板
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams"
        headers = {
            "Content-Type": "application/json"
        }
        if factor_type == "":
            return "factor_type不能为空, 必须为以下中的一种：客户侧光层业务、板卡类型、GEARBOX、线路侧光层业务、开销逻辑、单板业务模型、业务FRM芯片、单板支持的子架、产品、时钟芯片、客户侧电层业务、控制逻辑、子卡、单板配置类型、部件承载电层业务模式、物理端口数量、线路侧电层业务、客户侧光模块、单板软件平台、线路侧光模块、单板硬件PCB、交换FRM芯片"
        if factor_value == "":
            return "factor_value不能为空"
        params = {"factorTypeCn": factor_type, "factorValue": factor_value}
        response = requests.get(url, headers=headers, params=params)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            board_list = response_data.get("data", [])
            remove_field_list = ["id", "status", "create_time", "update_time", "operator_person", "effective_flag"]
            cleaned_board_list = [{k: v for k, v in item.items() if k not in remove_field_list}for item in board_list]
            return cleaned_board_list
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询所有的特性一级分类&特性二级分类&特性&子特性")
def query_feature_dict():
    """
    接口作用: 查询所有的特性一级分类&特性二级分类&特性&子特性

    示例: 查询所有的特性
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureInfoDict"
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            feature_dict = response_data.get("data")
            return feature_dict
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定特性/子特性关联的所有故障详情")
def query_fault_data_by_feature(feature_name: str, children_feature_flag: str):
    """
    接口作用: 查询指定特性/子特性关联的所有故障详情
    入参:
        feature_name: 特性/子特性名称
        children_feature_flag: 如果feature_name是子特性, 那么children_feature_flag是Y, 否则children_feature_flag是N(子特性的feature_name以FS开头, 特性以F开头)

    示例: 查询子特性灰光模块性能关联的所有故障数据
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_whole_status_data_service/query_fault_list_by_feature"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "feature_name": feature_name,
            "children_feature_flag": children_feature_flag
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("data", [])
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定的新增单板包含关键变更内容的特性列表")
def query_new_board_containing_key_change_features(board_name_str: str):
    """
    接口作用: 以特性为key值, 返回特性以及特性保护的关键变更内容列表

    入参:
        board_name_str: 单板名称, 只支持一次查询一块单板
    示例: 查询M1CB8R(8150H)查询指定的新增单板包含关键变更内容的特性列表
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/ai_application/process_query_board_key_changed_feature"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": board_name_str
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("result", {})
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定的新增单板关键变更内容及波及特性列表")
def query_new_board_containing_key_change_content(board_name_str: str):
    """
    接口作用: 查询指定的新增单板的关键变更内容及波及的特性列表

    入参:
        board_name_str: 单板名称, 只支持一次查询一块单板
    示例: 查询M1CB8R(8150H)查询指定的新增单板关键变更内容及波及特性列表
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/ai_application/process_query_board_key_changed_content"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": board_name_str
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("result", {})
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="查询指定单板的软件需求字典中指定内容")
async def query_board_hardware_software_manual(question: str):
    """
    接口作用: 查询指定单板的软件需求字典中指定内容
    入参:
        question: 指定单板名称的软件需求字典的具体章节
    示例:         
        请搜索M1MOM4G单板软件需求字典的单板属性信息
    """
    url = "https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat"
    appId = 'b53795dba2114cb1ad912741180c0813'
    appKey = 'prod_1600ee51c1944a43b7891dc5c188f59a'

    data = {
        "chatUuid": "",
        "chatName": "",
        "stream": False,
        "keep": False,
        "text": question,
        "model": "nebulacoder"
    }

    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {appId}-{appKey}",
        "X-Emp-No": "10329743",
        "X-Auth-Value": ""
    }

    try:
        # 异步非阻塞请求
        response = await httpx_client.post(url, json=data, headers=headers)
        print(f"请求 '{question}' 返回状态码: {response.status_code}")

        if response.status_code == 200:
            response_json = response.json()
            result = response_json.get("bo", {}).get("result", "未找到结果")
            return result
        else:
            return f"查询失败：HTTP {response.status_code}"

    except Exception as e:
        logging.error(f"请求异常: {e}", exc_info=True)
        return f"执行出错：{str(e)}"


@mcp.tool(name="查询指定单板在某场景业务切片下波及的特性需求交付信息")
def query_board_svc_slice_feature_rdc_status(board_name_str: str, hd_slices_str: str):
    """
    接口作用: 查询指定单板在某场景业务切片下波及的特性需求交付信息

    入参:
        board_name_str: 单板名称
        hd_slices_str: 场景的业务切片信息，markdown格式，切片信息中包含硬件部署，格式举例：| 核心业务方案"| 业务方案 | 业务方案切片 | 硬件拓扑部署 |\n| ------- | ----------- | ---------- | \n| 核心业务方案 | CL_LC, 2.5G灰光, E1oFG-FG-OTN-CB, 2.5G灰光  | M1SE1P x M2A2P x M2U1P == M2U1P x M2A2P x M1SE1P |\n| 核心业务方案 | CL_LC, 2.5G灰光, E1oFG-FG-OTN-CB, 10G灰光 | M1SE1P x M2A2P x M2U2P == M2U2P x M2A2P x M1SE1P |\n|"

    示例: 查询M2A2P单板在切片场景下波及的特性的需求交付信息
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/ai_application/process_query_board_slice_feature_rdc_status"
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "board_name": board_name_str,
            "data": hd_slices_str
        }
        response = requests.post(url, headers=headers, json=params)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("result", {})
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="更新指定单板的RDC数据")
def associated_linghang_system(emp_no: str, board_name: str, data_type: str, file_path: str) -> Dict[str, Any]:
    """
    接口作用: 上传指定单板 RDC 数据 Excel 文件

    入参:
        emp_no:      员工工号
        board_name:  单板名称
        data_type:   特性类型  new / old,特性类型,如果是新特性类型datatype就是new,旧特性类型datatype就是old
        file_path:   本地绝对/相对路径，支持 .xlsx / .xls / .csv

    示例: 上传单板M1CB8R(8150H)的新特性类型Excel文件
    """
    # 1. 基础校验
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"文件不存在: {file_path}")
    if path.suffix.lower() not in (".xlsx", ".xls", ".csv"):
        raise ValueError("仅支持 .xlsx / .xls / .csv 格式")
    # 2. 请求地址
    url = ("http://10.239.69.183:3001/api/electric_knowledge/front_board_whole_status_data_service/importOldBoardWholeStatusData")
    # 3. 构造 multipart/form-data
    mime, _ = mimetypes.guess_type(str(path))
    with open(path, "rb") as f:
        files = {"file": (path.name, f, mime or "application/octet-stream")}
        headers = {
            "X-Emp-No": emp_no,
            "board": board_name,
            "dataType": data_type,
        }
        try:
            resp = requests.post(url, files=files, headers=headers, timeout=60)
            # resp.raise_for_status()
            result = resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"转发到后端失败: {e}")
    # 4. 业务状态判断
    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "未知错误"))
    return {"message": result.get("message", "导入成功")}


@mcp.tool(name="更新指定单板的变更分析内容")
def calculation_board_change_analysis(emp_no: str, emp_token: str, board_name: str):
    """
    接口作用: 计算指定单板的变更分析并回填RDC

    入参:
        emp_no: 员工工号
        emp_token: 员工token
        board_name: 单板名称

    示例: 重新计算单板M1CB8R(8150H)的变更分析
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/front_board_whole_status_data_service/update_change_analysis_data"
        headers = {
            "Content-Type": "application/json",
            "X-Emp-No": emp_no,
            "X-Auth-Value": emp_token
        }
        data = {"board": board_name}
        logger.info(f"----计算变更分析前时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        response = requests.post(url, headers=headers, json=data, timeout=600)
        response_data = response.json()
        logger.info(f"----计算变更分析后时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # 检查返回状态
        if response_data.get("status") == "success":
            logger.info(f"----计算变更分析成功时间:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return response_data.get("message", '变更分析成功')
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="读取并返回txt/xlsx/pdf文件内容")
def query_text_from_file(file_path: str) -> str:
    """
    接口作用: 解析并返回txt/xlsx/pdf文件内容

    入参:
        file_path: 文件路径

    出参：
        文件文本内容

    示例: 请你读取文件中的内容
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    suffix = file_path.suffix.lower()
    try:
        if suffix == '.txt':
            return read_text_file(str(file_path))
        elif suffix in ('.xlsx', '.xls'):
            # 读取所有 sheet，拼接为文本
            text_parts = []
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
                df = df.fillna('')  # 将 NaN 替换为空字符串
                # 将每行拼接为 tab 分隔，每 sheet 之间用换行分隔
                sheet_text = '\n'.join(
                    '\t'.join(row) for row in df.values
                )
                text_parts.append(f"=== Sheet: {sheet_name} ===\n{sheet_text}")
            return '\n\n'.join(text_parts)
        elif suffix == '.pdf':
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"--- Page {page_num} ---\n{text}")
            return '\n\n'.join(text_parts)
        else:
            return "未知格式, 无法解析"
    except Exception as e:
        return f"解析文件 {file_path} 失败: {e}"


def read_text_file(file_path: str) -> str:
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(file_path, 'rb') as f:
        raw = f.read()
        return raw.decode('latin-1', errors='ignore')


@mcp.tool(name="查询所有的单板变更模式或某变更模式波及的特性子特性列表")
def query_supported_change_mode_and_affected_features(change_mod_str: str):
    """
    接口作用: 查询所有的单板变更模式或某变更模式波及的特性子特性列表

    入参:
        change_mod_str: 变更模式，用来查询某种变更模式波及的特性子特性列表时，需要传入具体的变更模式；如果是查询所有的单板变更模式，则传入特殊的字符"query_supported_change_mode"
    示例: 
        请查询所有的单板变更模式;
        请查询新增子架适配波及的特性及子特性
    """
    try:
        url = "http://10.239.69.183:3001/api/electric_knowledge/ai_application/process_query_supported_change_mode_and_affected_features"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "data": change_mod_str
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            return response_data.get("result", {})
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="导入指定单板的数据字典到知识库")
async def import_board_data_dictionary(emp_no: str,  emp_token: str, board_name: str, file_path: str) -> Dict[str, Any]:
    """
    接口作用: 上传指定单板 数据字典 数据 Excel 文件，并完成格式转换导入到知识库中

    入参:
        emp_no:      员工工号
        emp_token:   员工token
        board_name:  单板名称，因为数据字典是不区分M值，所以单板名称不带M值，如M3L4T，去掉M值的单板名称为 L4T
        file_path:   本地绝对/相对路径，支持 .xlsx / .xls / .csv

    示例: 请导入TEST单板数据字典到知识库
    """
    # 1. 基础校验
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"文件不存在: {file_path}")
    if path.suffix.lower() not in (".xlsx", ".xls", ".csv"):
        raise ValueError("仅支持 .xlsx / .xls / .csv 格式")
    # 2. 请求地址
    url = ("http://10.239.69.183:3001/api/electric_knowledge/front_board_board_data_dictionary/import_board_data_dictionary_to_knowledge_base")
    # 3. 构造 multipart/form-data
    mime, _ = mimetypes.guess_type(str(path))
    with open(path, "rb") as f:
        files = {"file": (path.name, f, mime or "application/octet-stream")}
        headers = {
            "X-Emp-No": emp_no,
            "X-Auth-Value": emp_token,
            "board": board_name
        }
        try:
            resp = await httpx_client.post(url, files=files, headers=headers)
            result = resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"转发到后端失败: {e}")
    # 4. 业务状态判断
    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "未知错误"))
    return {"message": result.get("message", "导入成功")}


@mcp.tool(name="查询指定特性（检测点）名称的表格数据")
def query_module_featurecheckpoint_content(featurecheckpointName: str):
    """
    接口作用: 查询指定特性（检测点）名称的表格数据

    入参:
        featurecheckpointName: 特性（检测点）名称

    示例: 
        1. 查询特性FS040309-03-E-DM-FG业务双向时延越限告警的表格数据
        2. 查询特性FS020102-10-E-FlexE 透传告警对应的检测点的表格数据
    """
    try:
        headers = {
            "Content-Type": "application/json"
        }
        url = f"http://10.239.69.183:3001/api/electric_knowledge/module_featurecheckpoint_content_data_service/queryModuleFeaturecheckpointContentDataByParams?featurecheckpointName={featurecheckpointName}"
        response = requests.get(url, headers=headers)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") != "success":
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
        module_featurecheckpoint_content_data_list = response_data.get("data", [])
        result = ""
        for featurecheckpoint_item in module_featurecheckpoint_content_data_list:
            if featurecheckpointName != featurecheckpoint_item.get("featurecheckpointName", ""):
                result += featurecheckpointName + "\n" + featurecheckpoint_item.get("featurecheckpointContent", "") + "\n\n"
            else:
                result += featurecheckpoint_item.get("featurecheckpointName", "") + "\n" + featurecheckpoint_item.get("featurecheckpointContent", "") + "\n\n"
        return result[:-2]
    except Exception as e:
        return f"执行出错：{e}"


@mcp.tool(name="导入特性（检测点）的表格数据到知识库")
async def import_featurecheckpoint_data_dictionary(emp_no: str, file_path: str) -> Dict[str, Any]:
    """
    接口作用: 上传特性（检测点）的表格数据 Excel 文件，并完成格式转换导入到知识库中

    入参:
        emp_no:      员工工号
        file_path:   本地绝对/相对路径，仅支持 .xlsx 

    示例: 请导入特性（检测点）的表格数据到知识库
    """
    # 1. 基础校验
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"文件不存在: {file_path}")
    if path.suffix.lower() not in (".xlsx"):
        raise ValueError("仅支持 .xlsx 格式")
    # 2. 请求地址
    url = (
        "http://10.239.69.183:3001/api/electric_knowledge/module_featurecheckpoint_content_data_service/importExcelModuleFeaturecheckpointContentData"
    )
    # 3. 构造 multipart/form-data
    mime, _ = mimetypes.guess_type(str(path))
    with open(path, "rb") as f:
        files = {"file": (path.name, f, mime or "application/octet-stream")}
        headers = {
            "X-Emp-No": emp_no
        }
        try:
            resp = await httpx_client.post(url, files=files, headers=headers)
            result = resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"转发到后端失败: {e}")
    # 4. 业务状态判断
    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "未知错误"))
    return {"message": result.get("message", "导入成功")}


@mcp.tool(name="查询需求预检明细表")
def query_req_manage_check_pr_info_table_by_filter_dict(filter_dict, date_range_dict):
    """
    接口作用：根据过滤条件查询需求预检明细表
    入参:
        filter_dict: 过滤条件字典，键为字段名，值为值列表
            - 支持"无"表示筛选空值/空字符串
            - 示例字典：{"problem_type": ["问题类型 A", "问题类型 A"], "cal_problem_flag": ["是"]}
            - 字段含义：需求预规划是 requirementpreplanning, 问题类型是 problem_type, 团队是 team, 整改责任人是 cal_handle_person
        date_range_dict: 日期范围筛选字典
            - 示例字典：{"check_date": {"start": "2026-05-01", "end": "2026-05-10"}}
            - 如果某个字段的 start 和 end 都为 None 或不存在，则不对该字段进行筛选
            - 如果只有 start, 则只填写 start, 如果只有 end, 则只填写 end
            - 问题发现日期就是 check_date
    出参：
        list: 满足条件的需求管理检查信息记录列表，每条记录包含以下字段：
            - problem_type: 问题类型（如"AI 准入检查不通过"、"特性链接检查异常"等）
            - problem_description: 问题描述（具体问题的详细描述）
            - system_id: 需求标识（RDC 需求 ID，如"11893756"）
            - system_title: 需求标题（需求的完整标题）
            - cal_handle_person: 整改责任人（负责整改的人员姓名）
            - team: 团队（所属团队名称）
            - requirementanalysisowner: 分析负责人（需求分析的负责人）
            - assessresult_first: 初评结论（初次评估的结论）
            - system_state: 状态（需求当前状态）
            - requirementpreplanning: 需求预规划（如"M721 V5.50R1"）
            - belongreleaseversion: 发布版本（所属的发布版本）
            - planstartdateofdevelopment: 计划开始开发时间（格式：YYYY-MM-DD）
            - planfinishdateofdevelopment: 计划结束开发时间（格式：YYYY-MM-DD）
            - system_createddate: 需求创建时间（格式：YYYY-MM-DD HH:MM:SS）
            - check_date: 问题发现日期（格式：YYYY-MM-DD）
            - cal_handle_date: 整改截止日期（格式：YYYY-MM-DD）
            - handle_delay_flag: 是否已过整改日期（"是"表示已过期，"否"表示未过期）
            - man_update_person: 一键设置人（最后人工修改的操作人）
            - man_update_date: 一键设置时间（最后人工修改的时间，格式：YYYY-MM-DD HH:MM:SS）
    示例: 
        1. 查询需求预规划为"M721 V5.50R1"且问题类型为"AI准入检查不通过"的需求预检明细表
        2. 查询需求预规划为"M721 V5.50R1"且问题发现日期为今天的需求预检明细表
    """
    try:
        # 新增：兼容字符串类型的 filter_dict，自动反序列化为字典
        if isinstance(filter_dict, str):
            filter_dict = json.loads(filter_dict)
        if isinstance(date_range_dict, str):
            date_range_dict = json.loads(date_range_dict)
        # 原有逻辑保持不变
        filter_dict["cal_problem_flag"] = "是"
        filter_dict["cal_handle_flag"] = "否"
        url = "http://10.239.69.183:3001/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_info_table_by_filter_dict"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "filter_dict": filter_dict,
            "date_range_dict": date_range_dict or {}
        }
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        # 检查返回状态
        if response_data.get("status") == "success":
            pr_info_list = response_data.get("data", {}).get("pr_info_list", [])
            # 只保留指定字段
            keep_fields = [
                'problem_type',
                'problem_description',
                'system_id',
                'system_title',
                'cal_handle_person',
                'team',
                'requirementanalysisowner',
                'assessresult_first',
                'system_state',
                'requirementpreplanning',
                'belongreleaseversion',
                'planstartdateofdevelopment',
                'planfinishdateofdevelopment',
                'system_createddate',
                'check_date',
                'cal_handle_date',
                'handle_delay_flag',
                'man_update_person',
                'man_update_date'
            ]
            filtered_list = []
            for item in pr_info_list:
                filtered_item = {field: item.get(field) for field in keep_fields}
                filtered_list.append(filtered_item)
            return filtered_list
        else:
            message = response_data.get("message", "未知错误")
            return f"查询失败：{message}"
    except Exception as e:
        return f"执行出错：{str(e)}"


def main():
    app = mcp.run(transport="http", host="10.239.69.183", port=3003)


if __name__ == "__main__":
    main()
