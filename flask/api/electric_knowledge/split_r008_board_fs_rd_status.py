import json
import re
import datetime
import copy
from typing import List, Dict, Any, Set, Optional, Sequence, Iterable, Tuple
from collections import OrderedDict, defaultdict
from electric_knowledge.front_board_tree_data_service import querySrcBoardTreeByParams
from electric_knowledge.front_feature_board_relation_data_service import querySrcFeatureBoardRelation
from electric_knowledge.front_board_whole_status_data_service import queryBoardGlobalStatusBoardList,isBoardWholeStatusRDCByParams,addSrcBoardWholeStatusData,updateSrcBoardWholeStatusData,querySrcBoardWholeStatusByParams, querySrcBoardWholeStatusRDCByParams
from electric_knowledge.front_rdc_fault_data_service import addRdcFaultTableData
from flask import request, jsonify
from electric_knowledge.front_feature_change_relation_data_service import querySrcFeatureChangeRelation

def convert_rdc_result_to_markdown(feature_list, query_mode: str):
    # 按board分组数据
    board_groups = {}
    for item in feature_list:
        board = item.get('board', '')
        if board not in board_groups:
            board_groups[board] = []
        board_groups[board].append(item)
    
    markdown_output = ""
    
    print(f"[-DEBUG-] board_groups: {len(board_groups)} boards found")

    # 处理每个board组
    for board, items in board_groups.items():
        # 创建items的副本，避免修改原始数据
        filtered_items = items.copy()
        
        # 如果query_mode为"supported"，则过滤需求状态
        if query_mode == "supported":
            filtered_items = [item for item in filtered_items if item.get('requirementStatus') in ["可交付", "已交付", "已支持"]]
            
            # 如果没有符合条件的数据，跳过这个board
            if not filtered_items:
                print(f"[-DEBUG-] No supported items found for board: {board}")
                continue

        if query_mode == "not_supported":
            filtered_items = [item for item in filtered_items if item.get('requirementStatus') not in ["可交付", "已交付", "已支持"]]
            
            # 如果没有符合条件的数据，跳过这个board
            if not filtered_items:
                print(f"[-DEBUG-] No not_supported items found for board: {board}")
                continue

        print(f"[-DEBUG-] Processing board: {board}, items count: {len(filtered_items)}")

        # 添加board标题
        markdown_output += f"## {board} all feature rdc result\n\n"
        
        # 表头
        headers = ["特性", "子特性", "RDC标识", "RDC标题", "需求预规划", "交付状态"]
        markdown_output += "| " + " | ".join(headers) + " |\n"
        markdown_output += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # 先按feature和subFeature排序，确保相同特性和子特性连续出现
        # 处理None值，确保排序稳定
        sorted_items = sorted(filtered_items, key=lambda x: (
            x.get('feature', '') or '', 
            x.get('subFeature', '') or ''
        ))
        
        # 跟踪当前特性和子特性
        current_feature = None
        current_subfeature = None
        
        # 添加数据行
        for item in sorted_items:
            feature = item.get('feature')
            subfeature = item.get('subFeature')
            
            # 处理None值
            feature = feature if feature is not None else ""
            subfeature = subfeature if subfeature is not None else ""
            
            # 判断是否需要显示特性和子特性
            show_feature = feature != current_feature
            show_subfeature = subfeature != current_subfeature
            
            # 更新当前特性和子特性
            current_feature = feature
            current_subfeature = subfeature
            
            # 构建行数据
            feature_display = feature if show_feature else ""
            subfeature_display = subfeature if show_subfeature else ""
            
            # 处理其他字段的None值
            rdc_ident = item.get('rdcIdent') or ""
            rdc_title = item.get('rdcTitle') or ""
            preplan_version = item.get('requirementPrePlanVersion') or ""
            status = item.get('requirementStatus') or ""
            
            row = [
                feature_display,
                subfeature_display,
                rdc_ident,
                rdc_title,
                preplan_version,
                status
            ]
            
            markdown_output += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        markdown_output += "\n"  # 在board组之间添加空行
    
    return markdown_output

def parse_markdown_table(markdown_text: str):
    """解析Markdown表格，返回行数据列表"""
    lines = markdown_text.strip().split('\n')
    table_data = []
    headers = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 分割单元格
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        
        if i == 0:
            # 第一行是表头
            headers = cells
        elif not re.match(r'^[\s:-]+$', ''.join(cells)):
            # 不是分隔线的数据行
            row_dict = {}
            for j, cell in enumerate(cells):
                if j < len(headers):
                    row_dict[headers[j]] = cell
            table_data.append(row_dict)
    
    return table_data

def clean_board_name(board):
    # 处理多种情况：
    # 1. 只有一个括号：M2U1P(70B7H) -> M2U1P
    # 2. 多个括号：M2U1P(FG)(70B7H) -> M2U1P(FG)
    # 3. 没有括号：M2U1P -> M2U1P
    # 4. 只有右括号：M2U1P) -> M2U1P
    # 5. 只有左括号：M2U1P( -> M2U1P
    
    # 匹配最后一个完整的括号及其内容
    pattern = r'\([^)]*\)$'
    result = re.sub(pattern, '', board)
    
    # 去除可能残留的空白字符
    return result.rstrip()

def parse_primary_network_element(slice_info):
    """从业务方案切片中解析网元业务模型"""
    network_elements = []

    # 去除括号内容
    clean_slice = re.sub(r'\([^)]*\)', '', slice_info)
    
    # 按逗号分割
    parts = [part.strip() for part in clean_slice.split(',') if part.strip()]
    
    # 根据切片格式提取网元业务模型
    if len(parts) >= 3 and parts[0] == "CL_LC":
        # CL==LC格式：第三个字段是网元业务模型
        network_elements.append(parts[2])
    elif len(parts) >= 5 and parts[0] == "CL_LL_LC":
        # CL==LL==LC格式：第三个和第五个字段是网元业务模型
        network_elements.append(parts[2])
        network_elements.append(parts[4])
    
    return network_elements

def parse_protection_type_and_element(slice_info):
    """
    从切片信息中解析保护类型和网元业务模型
    
    Args:
        slice_info: 业务方案切片信息，例如 "CL_LC, EoFG-FG-OTN, fg终结oduk通道层1+1保护"
        
    Returns:
        tuple: (protection_type, network_elements) 保护类型和网元业务模型数组
    """
    if not slice_info:
        return None, []
    
    # 按逗号分割切片信息
    parts = [part.strip() for part in slice_info.split(',')]
    
    protection_type = None
    network_elements = []
    
    # 检查切片类型
    if len(parts) > 0:
        slice_type = parts[0]
        
        if slice_type == "CL_LC":
            # CL_LC类型：第二个字段是网元业务模型，第三个字段是保护类型
            if len(parts) >= 3:
                network_elements = [parts[1]]  # 单个网元业务模型
                protection_type = parts[2]
        
        elif slice_type == "CL_LL_LC":
            # CL_LL_LC类型：第二个、第三个字段是网元业务模型，第四个字段是保护类型
            if len(parts) >= 4:
                network_elements = [parts[2]]  # 两个网元业务模型
                protection_type = parts[3]
        
        else:
            # 处理其他可能的切片类型
            # 这里可以根据需要添加其他类型的解析逻辑
            pass
    
    return protection_type, network_elements


def calculate_cross_type(network_element: str) -> list:
    """
    根据网元业务模型计算业务交叉类型
    
    Args:
        network_element: 网元业务模型字符串，如 "EoFG-FG-OTN", "EoFG-P-OTN", "EoFG-V-OTN"
    
    Returns:
        业务交叉类型列表，如 ["FG"], ["P"], ["VC"] 或 ["FG", "VC"]
    """
    if not network_element or not isinstance(network_element, str):
        return []
    
    cross_types = []
    
    # 特殊网元业务模型列表，需要同时返回FG和VC交叉类型
    special_network_elements = [
        'VCoFG-FG-OTN', 
        'VCoFG-FG-OTN-CB', 
        'E1oFG-FG-OTN-CB', 
        'EoSoFG-FG-OTN-CB'
    ]
    
    # 按连字符分割网元业务模型
    parts = network_element.split('-')
    
    # 确保有足够的组成部分
    if len(parts) < 3:
        return cross_types
    
    # 提取中间的交叉类型
    primary_cross_type = parts[1]
    
    # 特殊处理：如果交叉类型是 "V"，返回 "VC"
    if primary_cross_type == "V":
        primary_cross_type = "VC"
    
    # 添加主要交叉类型
    cross_types.append(primary_cross_type)
    
    # 检查是否为特殊网元业务模型，需要同时返回FG和VC交叉类型
    if network_element in special_network_elements:
        # 如果主要交叉类型不是VC，则添加VC
        if "VC" not in cross_types:
            cross_types.append("VC")
        # 如果主要交叉类型不是FG，则添加FG
        if "FG" not in cross_types:
            cross_types.append("FG")
    
    return cross_types

def is_related_feature_for_core_svc(network_element: str, feature: str) -> bool:
    core_svc_related_features = ['业务基础', '业务性能告警', '业务开销配置管理', '业务维护信号', '业务维护管理', '业务交叉管理']
    crs_types = calculate_cross_type(network_element)

    # 确保crs_types是列表，如果不是，则转换为列表
    if not isinstance(crs_types, list):
        if isinstance(crs_types, str):
            crs_types = [crs_types]
        else:
            return False
    
    # 如果crs_types为空列表，返回False
    if not crs_types:
        return False

    # 遍历所有交叉类型
    for crs_type in crs_types:
        # 确保crs_type是字符串
        if not isinstance(crs_type, str):
            continue
            
        for item in core_svc_related_features:
            tmp_feature = crs_type + item

            # 如果tmp_feature在feature中，返回True
            if tmp_feature in feature:
                return True

    return False


def is_related_feature_for_ha_svc(protection_type: str, feature: str) -> bool:
    # 如果protection_type不是字符串，或者为空字符串，返回False
    if not isinstance(protection_type, str) or not protection_type:
        return False

    if protection_type in feature:
        return True

    return False

def get_affected_network_elements(hd_rows, board):
    """
    根据核心业务方案的业务切片，计算某个单板波及的所有网元业务模型
    
    Args:
        hd_rows: 硬件切片数据行列表
        board: 单板名称
        
    Returns:
        set: 波及的网元业务模型集合
    """
    
    def is_cl_ll_lc_topology(hardware_deployment):
        """判断是否为CL=LL=LC拓扑"""
        if not hardware_deployment:
            return False
        # CL=LL=LC拓扑通常包含"=="连接符
        return "==" in hardware_deployment
    
    def is_endpoint_board(hardware_deployment, board):
        """判断板卡是否在拓扑的首尾节点"""
        if not hardware_deployment or not board:
            return False
        
        # 按"=="分割拓扑节点
        nodes = [node.strip() for node in hardware_deployment.split('==')]
        if len(nodes) < 2:
            return False
        
        # 检查是否在首节点或尾节点
        first_node = nodes[0]
        last_node = nodes[-1]
        
        # 检查板卡是否在首节点或尾节点中
        return board in first_node or board in last_node
    
    def get_first_network_element(slice_info):
        """获取切片信息中的第一个网元业务模型"""
        if not slice_info:
            return None
            
        # 清理并分割切片信息
        parts = [part.strip() for part in slice_info.split(',')]
        if not parts:
            return None
            
        # 根据切片类型确定第一个网元业务模型的位置
        slice_type = parts[0]
        if slice_type == 'CL_LC':
            # 对于CL_LC切片类型，网元业务模型通常在第三个位置
            if len(parts) >= 3:
                return parts[2]
        elif slice_type == 'CL_LL_LC':
            # 对于CL_LL_LC切片类型，第一个网元业务模型在第二个位置
            if len(parts) >= 2:
                return parts[1]
        else:
            # 对于未知切片类型，尝试找到第一个可能的网元业务模型
            for part in parts[1:]:  # 跳过第一个切片类型字段
                if is_likely_network_element(part):
                    return part
                    
        return None
    
    affected_elements = set()
    
    for row in hd_rows:
        # 只处理核心业务方案
        if row.get('业务方案', '') != '核心业务方案':
            continue
            
        slice_info = row.get('业务方案切片', '')
        topology = row.get('硬件拓扑部署', '')
        
        # 检查硬件拓扑部署中是否包含该单板
        if board not in topology:
            continue
        
        # 判断是否为CL=LL=LC拓扑且板卡在首尾节点
        if is_cl_ll_lc_topology(topology) and is_endpoint_board(topology, board):
            # 对于CL=LL=LC拓扑的首尾节点，只取第一个网元业务模型
            first_network_element = get_first_network_element(slice_info)
            if first_network_element:
                affected_elements.add(first_network_element)
        else:
            # 正常情况：解析所有相关的网元业务模型
            network_elements = parse_network_elements_from_slice(slice_info, topology, board)
            affected_elements.update(network_elements)
    
    return affected_elements


def parse_board_combinations(topology):
    """
    解析硬件拓扑部署中的单板组合
    
    Args:
        topology: 硬件拓扑部署字符串
        
    Returns:
        list: 单板组合列表，每个组合是单板名称的列表
    """
    if not topology:
        return []
    
    combinations = []
    # 分割组合，支持 "==" 和 "=" 作为分隔符
    for comb_str in topology.replace('==', '=').split('='):
        comb_str = comb_str.strip()
        if not comb_str:
            continue
        
        # 分割单板，支持 "x" 和 "*" 作为连接符
        boards = []
        for board in comb_str.replace('x', '*').split('*'):
            board = board.strip()
            if board:
                boards.append(board)
        
        if boards:
            combinations.append(boards)
    
    return combinations


def is_board_in_combination(target_board, combination):
    """
    检查目标单板是否在单板组合中
    
    Args:
        target_board: 目标单板名称
        combination: 单板组合列表
        
    Returns:
        bool: 是否在组合中
    """
    return any(target_board in board or board in target_board 
               for board in combination)


def is_likely_network_element(text):
    """
    判断文本是否可能是网元业务模型
    
    Args:
        text: 待判断的文本
        
    Returns:
        bool: 是否可能是网元业务模型
    """
    if not text:
        return False
    
    # 网元业务模型通常包含特定关键字或模式
    network_element_indicators = [
        'FG-OTN', 'OTN', 'E1oFG', 'CB', 'CPE', 'AGG', 'CORE'
    ]
    
    return any(indicator in text.upper() for indicator in network_element_indicators)

def gen_core_svc_slice_rdc_result(hd_rows, board, query_mode, items, markdown_output):
    """
    生成网元业务模型的切片行和特性行
    
    Args:
        hd_rows: 硬件切片数据
        board: 当前板卡名称
        query_mode: 查询模式
        items: 特性列表
        markdown_output: 当前的markdown输出
        
    Returns:
        str: 更新后的markdown输出
    """
    
    def escape_markdown_cell(content):
        """转义markdown表格单元格中的特殊字符"""
        if not content:
            return ""
        # 转义竖线，防止破坏表格结构
        return str(content).replace('|', '\\|')
    
    def add_markdown_row(cells):
        """添加markdown表格行，自动处理转义"""
        escaped_cells = [escape_markdown_cell(cell) for cell in cells]
        return "| " + " | ".join(str(cell) for cell in escaped_cells) + " |\n"
    
    def is_cl_ll_lc_topology(hardware_deployment):
        """判断是否为CL=LL=LC拓扑"""
        if not hardware_deployment:
            return False
        # CL=LL=LC拓扑通常包含"=="连接符
        return "==" in hardware_deployment
    
    def is_endpoint_board(hardware_deployment, board):
        """判断板卡是否在拓扑的首尾节点"""
        if not hardware_deployment or not board:
            return False
        
        # 按"=="分割拓扑节点
        nodes = [node.strip() for node in hardware_deployment.split('==')]
        if len(nodes) < 2:
            return False
        
        # 检查是否在首节点或尾节点
        first_node = nodes[0]
        last_node = nodes[-1]
        
        # 检查板卡是否在首节点或尾节点中
        return board in first_node or board in last_node
    
    def get_first_network_element(slice_info):
        """获取切片信息中的第一个网元业务模型"""
        network_elements = parse_primary_network_element(slice_info)
        return network_elements[0] if network_elements else None
    
    # 按网元业务模型分组
    network_element_groups = {}
    
    for hd_row in hd_rows:
        # 检查硬件拓扑部署列是否包含当前board
        if hd_row.get('业务方案', '') == "核心业务方案":
            hardware_deployment = hd_row.get('硬件拓扑部署', '')
            if hardware_deployment and board in hardware_deployment:
                slice_info = hd_row.get('业务方案切片', '')
                
                # 判断是否为CL=LL=LC拓扑且板卡在首尾节点
                if is_cl_ll_lc_topology(hardware_deployment) and is_endpoint_board(hardware_deployment, board):
                    # 对于CL=LL=LC拓扑的首尾节点，只取第一个网元业务模型
                    first_network_element = get_first_network_element(slice_info)
                    if first_network_element:
                        if first_network_element not in network_element_groups:
                            network_element_groups[first_network_element] = []
                        network_element_groups[first_network_element].append(hd_row)
                else:
                    # 正常情况：解析所有网元业务模型
                    network_elements = parse_primary_network_element(slice_info)
                    
                    # 将每个网元业务模型添加到对应的组
                    for network_element in network_elements:
                        if network_element not in network_element_groups:
                            network_element_groups[network_element] = []
                        network_element_groups[network_element].append(hd_row)
    
    # 用于存储已出现的特性内容，用于去重
    seen_features = {}
    
    # 按网元业务模型输出切片行和特性行
    for network_element, hd_rows_group in network_element_groups.items():
        # 先收集该网元业务模型相关的所有特性
        related_features = []
        for item in items:
            # 处理None值，确保feature不是None
            feature_value = item.get('feature') or ''
            if feature_value and is_related_feature_for_core_svc(network_element, feature_value):
                related_features.append(item)
        
        # 构建特性内容的唯一标识，用于去重
        feature_signature = ""
        if related_features:
            # 创建一个特性内容的签名，用于比较是否重复
            feature_items = []
            for item in related_features:
                feature = item.get('feature') or ''
                subfeature = item.get('subFeature') or ''
                rdc_ident = item.get('rdcIdent') or ''
                rdc_title = item.get('rdcTitle') or ''
                feature_items.append(f"{feature}|{subfeature}|{rdc_ident}|{rdc_title}")
            
            feature_signature = "||".join(sorted(feature_items))
        
        # 检查是否与前面某个网元业务模型的特性重复
        duplicate_network_element = None
        if feature_signature and feature_signature in seen_features:
            duplicate_network_element = seen_features[feature_signature]
        else:
            # 如果不是重复的，记录这个特性签名
            seen_features[feature_signature] = network_element
        
        # 输出该网元业务模型的所有切片行
        for i, hd_row in enumerate(hd_rows_group):
            # 判断是否是最后一个切片行
            is_last_slice = (i == len(hd_rows_group) - 1)
            
            # 如果是最后一个切片行，在特性列中填写关联特性
            if is_last_slice:
                if duplicate_network_element:
                    # 如果特性重复，显示重复信息，前面增加单板名称
                    feature_column = f"{board}单板{network_element}网元业务模型关联特性和{duplicate_network_element}关联特性重复"
                else:
                    # 如果不重复，正常显示关联特性，前面增加单板名称
                    feature_column = f"{board}单板{network_element}网元业务模型关联特性"
            else:
                feature_column = ""
            
            row_data = [
                hd_row.get('业务方案', '') or '',
                hd_row.get('业务方案切片', '') or '',
                hd_row.get('硬件拓扑部署', '') or '',
                feature_column,  # 特性列
                '', '', '', ''  # 其他特性相关列为空
            ]
            markdown_output += add_markdown_row(row_data)
        
        # 如果特性重复，则不输出特性行
        if duplicate_network_element:
            continue
        
        # 在该网元业务模型的所有切片行后面输出相关的特性行
        # 按特性和子特性分组，处理显示逻辑
        current_feature = None
        current_subfeature = None
        
        for item in related_features:
            # 处理None值
            feature = item.get('feature') or ''
            subfeature = item.get('subFeature') or ''
            
            # 判断是否需要显示特性和子特性
            show_feature = feature != current_feature
            show_subfeature = subfeature != current_subfeature
            
            # 更新当前特性和子特性
            current_feature = feature
            current_subfeature = subfeature
            
            # 构建行数据
            feature_display = feature if show_feature else ""
            subfeature_display = subfeature if show_subfeature else ""
            
            # 检查是否是空行（既没有特性/子特性内容，也没有需求内容）
            is_empty_row = not feature_display and not subfeature_display

            # 处理其他字段的None值
            rdc_ident = item.get('rdcIdent') or ''
            rdc_title = item.get('rdcTitle') or ''
            rdc_version = item.get('requirementPrePlanVersion') or ''
            requirement_status = item.get('requirementStatus') or ''
            
            # 对于非 "not_supported" 和 "supported" 查询模式，不过滤任何需求
            if query_mode not in ["not_supported", "supported"]:
                # 输出特性/子特性行和需求详情
                row_data = [
                    '', '', '',  # 切片相关列为空
                    feature_display,
                    subfeature_display,
                    rdc_ident,
                    rdc_title,
                    rdc_version,
                    requirement_status
                ]
            else:
                # 对于 "supported" 和 "not_supported" 模式，根据需求状态过滤
                supported_statuses = ["可交付", "已交付", "已支持"]
                is_supported = requirement_status in supported_statuses
                
                if ((query_mode == "supported") and not is_supported) or \
                   ((query_mode == "not_supported") and is_supported):
                    # 只输出特性/子特性行，不输出需求详情
                    # 跳过完全空行
                    if is_empty_row:
                        continue
                        
                    row_data = [
                        '', '', '',  # 切片相关列为空
                        feature_display,
                        subfeature_display,
                        '', '', '', ''  # 需求相关列为空
                    ]
                else:
                    # 输出特性/子特性行和需求详情
                    row_data = [
                        '', '', '',  # 切片相关列为空
                        feature_display,
                        subfeature_display,
                        rdc_ident,
                        rdc_title,
                        rdc_version,
                        requirement_status
                    ]
            
            # 只有当行不为空时才输出
            # 注意：即使特性/子特性为空，只要需求内容不为空，就不算空行
            has_requirement_content = len(row_data) > 6 and any(row_data[6:])  # 检查是否有需求内容
            if not is_empty_row or has_requirement_content:
                markdown_output += add_markdown_row(row_data)

    return markdown_output


# 高可用业务
def gen_hi_and_expand_availability_slice_rdc_result(svc_class, hd_rows, board, query_mode, items, markdown_output):
    """
    生成高可用业务方案的网元业务模型切片行和特性行
    
    Args:
        hd_rows: 硬件切片数据
        board: 当前板卡名称
        items: 特性列表
        markdown_output: 当前的markdown输出
        
    Returns:
        str: 更新后的markdown输出
    """
    # 按保护类型分组网元业务模型
    protection_type_groups = {}

    network_lists = get_affected_network_elements(hd_rows, board)

    #print(f"[-DEBUG-] 11111111111111gen_hi_and_expand_availability_slice_rdc_result: {network_lists}")

    for hd_row in hd_rows:
        # 检查硬件拓扑部署列是否包含当前board
        if hd_row.get('业务方案', '') == svc_class:
            slice_info = hd_row.get('业务方案切片', '')
            
            # 解析保护类型和网元业务模型
            protection_type, network_element = parse_protection_type_and_element(slice_info)

            for network in network_element:
                if network in network_lists:
                    if protection_type:
                        if protection_type not in protection_type_groups:
                            protection_type_groups[protection_type] = []
                        protection_type_groups[protection_type].append({
                            'hd_row': hd_row,
                        })
    
    # 按保护类型输出切片行和特性行
    for protection_type, element_data_list in protection_type_groups.items():
        # 输出该保护类型的所有网元业务模型的切片行
        for element_data in element_data_list:
            hd_row = element_data['hd_row']
            #feature_column = f"{board}单板{protection_type}因子取值关联特性"

            row_data = [
                hd_row.get('业务方案', '') or '',
                hd_row.get('业务方案切片', '') or '',
                board,
                '', '', '', '', ''  # 特性相关列为空
            ]
            markdown_output += "| " + " | ".join(str(cell) for cell in row_data) + " |\n"
        
        # 在该保护类型的所有切片行后面输出相关的特性行
        # 收集该保护类型下所有网元业务模型的相关特性
        all_related_features = []
        for item in items:
            # 处理None值，确保feature不是None
            feature_value = item.get('feature') or ''
            if feature_value and is_related_feature_for_ha_svc(protection_type, feature_value):
                # 避免重复添加相同的特性
                if item not in all_related_features:
                    all_related_features.append(item)
        
        # 按特性和子特性分组，处理显示逻辑
        current_feature = None
        current_subfeature = None
        
        for item in all_related_features:
            # 处理None值
            feature = item.get('feature') or ''
            subfeature = item.get('subFeature') or ''
            
            # 判断是否需要显示特性和子特性
            show_feature = feature != current_feature
            show_subfeature = subfeature != current_subfeature
            
            # 更新当前特性和子特性
            current_feature = feature
            current_subfeature = subfeature
            
            # 构建行数据
            feature_display = feature if show_feature else ""
            subfeature_display = subfeature if show_subfeature else ""
            
            # 检查是否是空行（既没有特性/子特性内容，也没有需求内容）
            is_empty_row = not feature_display and not subfeature_display
            
            # 处理其他字段的None值
            rdc_ident = item.get('rdcIdent') or ''
            rdc_title = item.get('rdcTitle') or ''
            rdc_version = item.get('requirementPrePlanVersion') or ''
            requirement_status = item.get('requirementStatus') or ''
            
            # 对于非 "not_supported" 和 "supported" 查询模式，不过滤任何需求
            if query_mode not in ["not_supported", "supported"]:
                # 输出特性/子特性行和需求详情
                row_data = [
                    '', '', '',  # 切片相关列为空
                    feature_display,
                    subfeature_display,
                    rdc_ident,
                    rdc_title,
                    rdc_version,
                    requirement_status,
                    '', '', '',
                ]
            else:
                # 对于 "supported" 和 "not_supported" 模式，根据需求状态过滤
                if ((query_mode == "supported") and (requirement_status not in ["可交付", "已交付", "已支持"])) or \
                   ((query_mode == "not_supported") and (requirement_status in ["可交付", "已交付", "已支持"])):
                    # 只输出特性/子特性行，不输出需求详情
                    # 跳过完全空行
                    if is_empty_row:
                        continue
                        
                    row_data = [
                        '', '', '',  # 切片相关列为空
                        feature_display,
                        subfeature_display,
                    ]
                else:
                    # 输出特性/子特性行和需求详情
                    row_data = [
                        '', '', '',  # 切片相关列为空
                        feature_display,
                        subfeature_display,
                        rdc_ident,
                        rdc_title,
                        requirement_status,
                        '', '', '',
                    ]
            
            # 只有当行不为空时才输出
            # 注意：即使特性/子特性为空，只要需求内容不为空，就不算空行
            has_requirement_content = len(row_data) > 6 and any(row_data[6:])  # 检查是否有需求内容
            if not is_empty_row or has_requirement_content:
                markdown_output += "| " + " | ".join(str(cell) for cell in row_data) + " |\n"
    
    return markdown_output

def convert_slice_rdc_result_to_markdown(query_mode: str, hd_slices: str, feature_list: str):
    # 按board分组数据
    board_groups = {}
    for item in feature_list:
        board = item.get('board', '')
        if board not in board_groups:
            board_groups[board] = []
        board_groups[board].append(item)
    
    markdown_output = ""

    # 解析hd_slices表格
    hd_rows = parse_markdown_table(hd_slices)
    
    #print(f"[-DEBUG-] query_mode:{query_mode}")

    # 处理每个board组
    for board, items in board_groups.items():
        board = clean_board_name(board)
        print(f"[-DEBUG-] board:{board}")

        # 添加board标题
        markdown_output += f"{board} slice feature rdc result:\n"
        
        # 表头
        headers = ["业务方案", "业务方案切片", "硬件拓扑部署", "特性", "子特性", "RDC标识", "RDC标题", "需求预规划版本", "交付状态"]
        markdown_output += "| " + " | ".join(headers) + " |\n"
        markdown_output += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # 生成核心业务方案切片特性子特性需求表
        markdown_output = gen_core_svc_slice_rdc_result(hd_rows, board, query_mode, items, markdown_output)
        
        # 生成高可用业务方案切片特性子特性需求表
        markdown_output = gen_hi_and_expand_availability_slice_rdc_result('高可用业务方案',hd_rows, board, query_mode, items, markdown_output)

        # 生成扩展应用业务方案切片特性子特性需求表
        markdown_output = gen_hi_and_expand_availability_slice_rdc_result('可扩展业务方案', hd_rows, board, query_mode, items, markdown_output)

        markdown_output += "\n\n"  # 添加空行分隔不同board的结果
    
    return markdown_output


def convert_feature_result_to_markdown(feature_list, query_mode: str):
    # 添加详细的数据分析
    print(f"[-DEBUG-] Total items in feature_list: {len(feature_list)}")
    
    # 分析subFeature字段的情况
    none_subfeature_count = 0
    valid_subfeature_count = 0
    for item in feature_list:
        if item.get('subFeature') is None:
            none_subfeature_count += 1
        else:
            valid_subfeature_count += 1
    
    print(f"[-DEBUG-] SubFeature analysis: None={none_subfeature_count}, Valid={valid_subfeature_count}")
    
    # 放宽数据验证条件，允许subFeature为None
    valid_feature_list = []
    for item in feature_list:
        # 只确保feature字段存在
        if item.get('feature'):
            valid_feature_list.append(item)
        else:
            print(f"[-WARNING-] Skipping invalid item: feature={item.get('feature')}")
    
    # 如果没有有效数据，直接返回
    if not valid_feature_list:
        print("[-ERROR-] No valid data found after filtering")
        return "## 无有效数据\n\n"
    
    # 按board和feature分组数据
    board_feature_groups = {}
    
    for item in valid_feature_list:
        board = item.get('board', '')
        feature = item.get('feature', '')
        
        if board not in board_feature_groups:
            board_feature_groups[board] = {}
        
        if feature not in board_feature_groups[board]:
            board_feature_groups[board][feature] = []
        
        board_feature_groups[board][feature].append(item)
    
    markdown_output = ""
    print(f"[-DEBUG-] Processing {len(board_feature_groups)} boards with valid data")

    # 处理每个board
    for board, features in board_feature_groups.items():
        print(f"[-DEBUG-] Processing board: {board}, features count: {len(features)}")
        
        # 根据query_mode筛选features
        filtered_features = {}
        
        if query_mode == "supported":
            # 只保留所有子特性都是交付状态的特性
            for feature, subfeatures in features.items():
                # 确保该特性下有子特性
                if not subfeatures:
                    print(f"[-DEBUG-] Feature {feature} has no subfeatures, skipping")
                    continue
                
                # 首先，过滤掉subFeature为None的记录，因为它们无法正确分组
                valid_subfeatures = [s for s in subfeatures if s.get('subFeature') is not None]
                
                # 如果没有有效的子特性记录，检查是否所有记录都是subFeature为None
                if not valid_subfeatures:
                    # 检查这些None子特性记录的状态
                    none_subfeatures = [s for s in subfeatures if s.get('subFeature') is None]
                    none_statuses = [s.get('requirementStatus') for s in none_subfeatures]
                    
                    # 如果没有需求关联，按照交付内容处理
                    all_none_delivered = all(status in ["可交付", "已交付", "已支持", None] for status in none_statuses)
                    if all_none_delivered:
                        # 创建一个虚拟的子特性记录，表示该特性没有明确的子特性但所有内容都已交付
                        virtual_subfeature = {
                            'feature': feature,
                            'subFeature': '无明确子特性',
                            'requirementStatus': '可交付',
                            'has_no_requirements': True  # 标记为未关联需求
                        }
                        filtered_features[feature] = [virtual_subfeature]
                        print(f"[-DEBUG-] Feature {feature} has no explicit subfeatures but all content is delivered")
                    else:
                        print(f"[-DEBUG-] Feature {feature} has no valid subfeatures and not all content is delivered, skipping")
                    continue
                
                # 按子特性分组，检查每个子特性的状态
                subfeature_status = {}
                subfeature_requirements = {}
                for subfeature in valid_subfeatures:
                    subfeature_name = subfeature.get('subFeature', '')
                    status = subfeature.get('requirementStatus', '')
                    rdc_ident = subfeature.get('rdcIdent', '')
                    
                    if subfeature_name not in subfeature_status:
                        subfeature_status[subfeature_name] = []
                        subfeature_requirements[subfeature_name] = []
                    
                    subfeature_status[subfeature_name].append(status)
                    subfeature_requirements[subfeature_name].append({
                        'rdc_ident': rdc_ident,
                        'status': status
                    })
                
                # 检查是否所有子特性的所有需求都是交付状态
                all_subfeatures_supported = True
                for subfeature_name, statuses in subfeature_status.items():
                    # 过滤掉None状态，只考虑有明确状态的需求
                    valid_statuses = [s for s in statuses if s is not None]
                    
                    # 如果没有有效状态，视为已交付（按照交付内容处理）
                    if not valid_statuses:
                        print(f"[-DEBUG-] Feature {feature} has subfeature {subfeature_name} with no valid status, treating as delivered")
                        continue
                    
                    # 检查所有有效状态是否都是交付状态
                    all_delivered = all(status in ["可交付", "已交付", "已支持"] for status in valid_statuses)
                    if not all_delivered:
                        all_subfeatures_supported = False
                        print(f"[-DEBUG-] Feature {feature} has unsupported subfeature: {subfeature_name} with valid statuses: {valid_statuses}")
                        break
                
                if all_subfeatures_supported:
                    # 去重：只保留唯一的子特性，并标记是否有关联需求
                    unique_subfeatures = {}
                    for subfeature in valid_subfeatures:
                        subfeature_name = subfeature.get('subFeature', '')
                        if subfeature_name not in unique_subfeatures:
                            # 检查该子特性是否有关联需求
                            has_requirements = False
                            for req in subfeature_requirements.get(subfeature_name, []):
                                if req['rdc_ident'] and req['status']:
                                    has_requirements = True
                                    break
                            
                            # 添加标记
                            subfeature['has_no_requirements'] = not has_requirements
                            unique_subfeatures[subfeature_name] = subfeature
                    
                    filtered_features[feature] = list(unique_subfeatures.values())
                    print(f"[-DEBUG-] Feature {feature} is fully supported with {len(filtered_features[feature])} unique subfeatures")
            
            if not filtered_features:
                print(f"[-DEBUG-] No fully supported features found for board: {board}")
                continue
                
            # 添加board标题
            markdown_output += f"## {board} - 完全支持的特性\n\n"
            
            # 表头 - 增加编号列和备注列
            headers = ["编号", "特性", "子特性", "备注"]
            markdown_output = _add_table_header(markdown_output, headers)
            
            # 生成表格内容
            markdown_output = _generate_simple_table_with_numbering_and_notes(markdown_output, filtered_features)
        
        elif query_mode == "not_supported":
            # 保留至少有一个子特性不是交付状态的特性
            for feature, subfeatures in features.items():
                # 确保该特性下有子特性
                if not subfeatures:
                    print(f"[-DEBUG-] Feature {feature} has no subfeatures, skipping")
                    continue
                
                # 首先，过滤掉subFeature为None的记录，因为它们无法正确分组
                valid_subfeatures = [s for s in subfeatures if s.get('subFeature') is not None]
                
                # 如果没有有效的子特性记录，检查是否所有记录都是subFeature为None
                if not valid_subfeatures:
                    # 检查这些None子特性记录的状态
                    none_subfeatures = [s for s in subfeatures if s.get('subFeature') is None]
                    none_statuses = [s.get('requirementStatus') for s in none_subfeatures]
                    
                    # 如果没有需求关联，按照交付内容处理，所以不包含在not_supported中
                    all_none_delivered = all(status in ["可交付", "已交付", "已支持", None] for status in none_statuses)
                    if not all_none_delivered:
                        # 创建一个虚拟的子特性记录，表示该特性没有明确的子特性但有未交付内容
                        virtual_subfeature = {
                            'feature': feature,
                            'subFeature': '无明确子特性',
                            'requirementStatus': '未交付',
                            'rdcIdent': '未关联需求'  # 在RDC标识列注明
                        }
                        filtered_features[feature] = [virtual_subfeature]
                        print(f"[-DEBUG-] Feature {feature} has no explicit subfeatures but has undelivered content")
                    else:
                        print(f"[-DEBUG-] Feature {feature} has no valid subfeatures and all content is delivered, skipping")
                    continue
                
                # 按子特性分组，检查每个子特性的状态
                subfeature_status = {}
                for subfeature in valid_subfeatures:
                    subfeature_name = subfeature.get('subFeature', '')
                    status = subfeature.get('requirementStatus', '')
                    
                    if subfeature_name not in subfeature_status:
                        subfeature_status[subfeature_name] = []
                    
                    subfeature_status[subfeature_name].append(status)
                
                # 检查是否有任何子特性包含非交付状态的需求
                has_unsupported_subfeature = False
                for subfeature_name, statuses in subfeature_status.items():
                    # 过滤掉None状态，只考虑有明确状态的需求
                    valid_statuses = [s for s in statuses if s is not None]
                    
                    # 如果没有有效状态，视为已交付（按照交付内容处理）
                    if not valid_statuses:
                        print(f"[-DEBUG-] Feature {feature} has subfeature {subfeature_name} with no valid status, treating as delivered")
                        continue
                    
                    # 检查是否所有有效状态都是交付状态
                    all_delivered = all(status in ["可交付", "已交付", "已支持"] for status in valid_statuses)
                    if not all_delivered:
                        has_unsupported_subfeature = True
                        print(f"[-DEBUG-] Feature {feature} has unsupported subfeature: {subfeature_name} with valid statuses: {valid_statuses}")
                        break
                
                if has_unsupported_subfeature:
                    # 标记没有RDC标识的记录
                    for subfeature in valid_subfeatures:
                        rdc_ident = subfeature.get('rdcIdent')
                        if not rdc_ident:
                            subfeature['rdcIdent'] = '未关联需求'
                    
                    filtered_features[feature] = valid_subfeatures
                    print(f"[-DEBUG-] Feature {feature} is not fully supported, including all {len(valid_subfeatures)} requirements")
            
            if not filtered_features:
                print(f"[-DEBUG-] No unsupported features found for board: {board}")
                continue
                
            # 添加board标题
            markdown_output += f"## {board} - 未完全支持的特性\n\n"
            
            # 表头 - 显示特性、子特性和需求信息，增加编号列
            headers = ["编号", "特性", "子特性", "RDC标识", "RDC标题", "需求预规划", "交付状态"]
            markdown_output = _add_table_header(markdown_output, headers)
            
            # 生成表格内容
            markdown_output = _generate_detailed_table_with_numbering(markdown_output, filtered_features)
        
        else:
            # 其他查询模式 - 使用原有逻辑，输出所有数据
            print(f"[-DEBUG-] Using default mode for query_mode: {query_mode}")
            
            # 添加board标题
            markdown_output += f"## {board} - 所有特性\n\n"
            
            # 表头 - 显示特性、子特性和需求信息，增加编号列
            headers = ["编号", "特性", "子特性", "RDC标识", "RDC标题", "需求预规划", "交付状态"]
            markdown_output = _add_table_header(markdown_output, headers)
            
            # 标记没有RDC标识的记录
            for feature, subfeatures in features.items():
                for subfeature in subfeatures:
                    rdc_ident = subfeature.get('rdcIdent')
                    if not rdc_ident:
                        subfeature['rdcIdent'] = '未关联需求'
            
            # 生成表格内容
            markdown_output = _generate_detailed_table_with_numbering(markdown_output, features)
        
        markdown_output += "\n"  # 在board组之间添加空行
    
    return markdown_output


def _add_table_header(markdown_output, headers):
    """添加表格头部"""
    markdown_output += "| " + " | ".join(headers) + " |\n"
    markdown_output += "|" + "|".join(["---"] * len(headers)) + "|\n"
    return markdown_output


def _generate_simple_table_with_numbering_and_notes(markdown_output, features):
    """生成简单表格（只包含特性和子特性），增加编号和备注列"""
    # 按特性排序
    sorted_features = sorted(features.items(), key=lambda x: x[0] or '')
    
    current_feature = None
    feature_number = 0
    
    for feature, subfeatures in sorted_features:
        feature_number += 1
        # 按子特性排序
        sorted_subfeatures = sorted(subfeatures, key=lambda x: x.get('subFeature', '') or '')
        
        for i, subfeature_item in enumerate(sorted_subfeatures):
            subfeature = subfeature_item.get('subFeature', '')
            
            # 构建行数据
            if i == 0:  # 特性行
                feature_display = feature
                number_display = str(feature_number)
            else:  # 子特性行
                feature_display = ""
                number_display = ""
            
            # 检查是否需要添加备注
            note = ""
            if subfeature_item.get('has_no_requirements'):
                note = "未关联需求"
            
            row = [
                number_display,
                feature_display,
                subfeature,
                note
            ]
            
            markdown_output += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    
    return markdown_output


def _generate_detailed_table_with_numbering(markdown_output, features):
    """生成详细表格（包含所有字段），增加编号"""
    # 按特性排序
    sorted_features = sorted(features.items(), key=lambda x: x[0] or '')
    
    current_feature = None
    current_subfeature = None
    feature_number = 0
    
    for feature, subfeatures in sorted_features:
        feature_number += 1
        # 按子特性排序
        sorted_subfeatures = sorted(subfeatures, key=lambda x: x.get('subFeature', '') or '')
        
        for i, subfeature_item in enumerate(sorted_subfeatures):
            subfeature = subfeature_item.get('subFeature', '')
            
            # 判断是否需要显示特性和子特性
            show_feature = feature != current_feature
            show_subfeature = subfeature != current_subfeature
            
            # 更新当前特性和子特性
            current_feature = feature
            current_subfeature = subfeature
            
            # 构建行数据
            if show_feature:  # 特性行
                feature_display = feature
                number_display = str(feature_number)
            else:  # 子特性行
                feature_display = ""
                number_display = ""
            
            subfeature_display = subfeature if show_subfeature else ""
            
            # 处理其他字段 - 确保没有换行符
            rdc_ident = _clean_field(subfeature_item.get('rdcIdent'))
            rdc_title = _clean_field(subfeature_item.get('rdcTitle'))
            preplan_version = _clean_field(subfeature_item.get('requirementPrePlanVersion'))
            status = _clean_field(subfeature_item.get('requirementStatus'))
            
            row = [
                number_display,
                feature_display,
                subfeature_display,
                rdc_ident,
                rdc_title,
                preplan_version,
                status
            ]
            
            markdown_output += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    
    return markdown_output


def _clean_field(field_value):
    """清理字段值，移除换行符和多余空格"""
    if field_value is None:
        return ""
    
    # 转换为字符串并移除换行符
    cleaned = str(field_value).replace('\n', ' ').replace('\r', ' ')
    
    # 移除多余的空格
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


#查询单板所有特性及需求交付状态
def get_board_all_feature_rdc_status(product_name: str, query_mode: str, board_names: List[str]):

    #print(f"[-DEBUG-] product_name:{product_name}")
    #print(f"[-DEBUG-] query_mode:{query_mode}")
    #print(f"[-DEBUG-] board_names:{board_names}")

    # 参数验证
    if not board_names or not isinstance(board_names, list):
        return {
            "code": 400,
            "status": "error", 
            "message": "board_names参数必须是非空字符串数组"
        }

    # 过滤空值和去重
    valid_board_names = list(OrderedDict.fromkeys(
        name.strip() for name in board_names if name and name.strip()
    ))

    if not valid_board_names:
        return {
            "code": 400,
            "status": "error",
            "message": "没有有效的单板名称"
        }

    # 查询所有单板的RDC标识数据
    feature_list = []
    board_rdc_results = ""
    
    #print(f"[-DEBUG-] valid_board_names:{valid_board_names}")

    for board_name in valid_board_names:
        # 1. 查询单板在全局状态表中的RDC数据
        query_params = {
            "product": product_name,
            "board": board_name
            }

        #feature_list += querySrcBoardWholeStatusRDCByParams(query_params, markdown_flag= True)
        feature_list += querySrcBoardWholeStatusByParams(query_params, markdown_flag= True)

        print(f"[-DEBUG-] query_params:{query_params}")
        #print(f"[-DEBUG-] feature_list:{feature_list}")

        if not feature_list:
            print(f"单板 {board_name} 在全局状态表中没有特性数据")
            continue

    #board_rdc_results = convert_rdc_result_to_markdown(feature_list, query_mode)
    board_rdc_results = convert_feature_result_to_markdown(feature_list, query_mode)

    print(f"[-DEBUG-] board_rdc_results:{board_rdc_results}")


    # 构建响应结果
    response_data = {
        "board_rdc_identifiers": board_rdc_results,
        "summary": {
            "total_boards": len(valid_board_names),
            "found_boards": len(board_rdc_results),
            "query_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return response_data


#查询切片波及单板特性及需求交付状态
def get_board_slice_feature_rdc_status(product_name: str, query_mode: str, board_names:str, hd_slices:str):
    """
    "{board} slice feature rdc result:\n"
    | 业务方案 | 业务方案切片 | 硬件拓扑部署 | 特性 | 子特性 | rdc_ident | rdc_title | rdc_status |
    |------------| ----------- | ------- | ---- | ------| ----------| --------- | -----------|
    按照单个查询切片
 
    业务方案分类:核心业务、高可用业务、扩展应用业务
    业务方案切片:单板波及的所有业务切片(CL_LC,2.5G及以下灰光,EoFG-P-OTN,2.5G及以下灰光)
    硬件部署: 单板 PGEP x M2U1P == M2U1P x PGEP 
    ---来源于切片的硬件部署表
    特性: 根据切片关联找到相关特性
    子特性：单板特性下面所有子特性，从全局状态表中获取(已经是细化筛选之后的)
    rdc_ident/rdc_title/rdc_status:子特性关联的所有需求
    
    """
   
    # 参数验证
    if not board_names or not isinstance(board_names, list):
        return {
            "code": 400,
            "status": "error", 
            "message": "board_names参数必须是非空字符串数组"
        }

    # 过滤空值和去重
    valid_board_names = list(OrderedDict.fromkeys(
        name.strip() for name in board_names if name and name.strip()
    ))

    if not valid_board_names:
        return {
            "code": 400,
            "status": "error",
            "message": "没有有效的单板名称"
        }

    # 查询所有单板的RDC标识数据
    feature_list = []
    slice_rdc_results = ""
    
    #print(f"[-DEBUG-] valid_board_names:{valid_board_names}")

    for board_name in valid_board_names:
        # 1. 查询单板在全局状态表中的RDC数据
        query_params = {
            "product": product_name,
            "board": board_name
            }

        #feature_list += querySrcBoardWholeStatusRDCByParams(query_params, markdown_flag= True)
        feature_list += querySrcBoardWholeStatusByParams(query_params, markdown_flag= True)

        print(f"[-DEBUG-] query_params:{query_params}")
        #print(f"[-DEBUG-] feature_list:{feature_list}")

        if not feature_list:
            print(f"单板 {board_name} 在全局状态表中没有特性数据")
            continue

    slice_rdc_results = convert_slice_rdc_result_to_markdown(query_mode, hd_slices, feature_list)

    print(f"[-DEBUG-] slice_rdc_results:{slice_rdc_results}")

    # 构建响应结果
    response_data = {
            "board_rdc_identifiers": slice_rdc_results,

            "query_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return response_data

def find_feature_and_key_changes(board_name: str, feature_list):
    """
    查找变更分析内容中包含"关键变更"字符串的特性，并生成Markdown表格
    只显示关键变更内容，过滤掉普通变更内容
    
    Args:
        board_name: 板卡名称
        feature_list: 特性列表，包含各特性的详细信息
        
    Returns:
        str: 包含关键变更特性的Markdown表格
    """
    def extract_key_changes_only(content):
        """
        从变更分析内容中提取只包含关键变更的部分，保留换行格式
        """
        if not content:
            return ""
        
        content_str = str(content)
        
        # 检查是否包含关键变更
        if "关键变更" not in content_str:
            return ""
        
        # 分割内容，提取关键变更部分
        lines = content_str.split('\n')
        key_changes_lines = []
        in_key_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测关键变更部分的开始
            if "关键变更" in line:
                in_key_section = True
                key_changes_lines.append(line)
                continue
                
            # 检测其他变更部分的开始（结束关键变更部分）
            if ("普通变更" in line or "其他变更" in line) and in_key_section:
                break
                
            # 如果在关键变更部分中，添加该行
            if in_key_section:
                key_changes_lines.append(line)
        
        # 如果没有找到关键变更部分，返回空
        if not key_changes_lines:
            return ""
        
        # 保留换行符，用换行符连接各行
        return '\n'.join(key_changes_lines)
    
    def has_meaningful_key_changes(key_changes_text):
        """
        检查关键变更内容是否有实际意义，过滤掉空内容
        比如只有"关键变更:"或"关键变更："后面没有实际内容的
        """
        if not key_changes_text:
            return False
        
        # 将文本按行分割
        lines = key_changes_text.split('\n')
        
        # 检查每一行是否包含实际内容
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 如果这一行只有"关键变更"相关的标识符，没有实际内容
            if ("关键变更" in line and 
                line.replace("关键变更", "").replace(":", "").replace("：", "").strip() == ""):
                continue
                
            # 如果这一行有实际内容（不仅仅是"关键变更"标识）
            if line and not line.replace("关键变更", "").replace(":", "").replace("：", "").strip() == "":
                return True
        
        # 如果没有找到有实际内容的行，返回False
        return False
    
    def escape_markdown_table_cell(text):
        """
        转义Markdown表格单元格中的特殊字符，确保表格格式正确
        同时将换行符转换为HTML换行标签，确保在表格中正确显示多行文本
        """
        if not text:
            return ""
        # 转义表格分隔符 |
        text = str(text).replace('|', '\\|')
        # 将换行符转换为HTML换行标签，确保在Markdown表格中正确显示多行
        text = text.replace('\n', '<br>')
        return text
    
    # 查找包含"关键变更"的特性
    key_change_features = []
    
    for item in feature_list:
        change_analysis = item.get('changeAnalysis', '')
        feature = item.get('feature', '')
        
        # 检查变更分析内容是否包含"关键变更"
        if change_analysis and "关键变更" in str(change_analysis):
            # 提取只包含关键变更的内容
            key_changes_only = extract_key_changes_only(change_analysis)
            
            # 检查关键变更内容是否有实际意义
            if key_changes_only and has_meaningful_key_changes(key_changes_only):
                # 避免重复添加同一特性
                if feature not in [f['feature'] for f in key_change_features]:
                    key_change_features.append({
                        'feature': feature,
                        'changeAnalysis': key_changes_only
                    })
    
    markdown_output = ""

    # 添加board标题
    markdown_output += f"## 新增{board_name}单板的包含关键变更内容特性列表:\n\n"

    if key_change_features:
        # 表头 - 增加编号列
        headers = ["编号", "包含关键变更内容的特性", "关键变更内容"]
        markdown_output += "| " + " | ".join(headers) + " |\n"
        markdown_output += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # 按特性名称排序
        sorted_features = sorted(key_change_features, key=lambda x: x.get('feature', ''))
        
        # 添加数据行
        for index, item in enumerate(sorted_features, 1):
            feature = item.get('feature', '') or ""
            change_analysis = item.get('changeAnalysis', '') or ""
            
            # 转义表格单元格中的特殊字符，并将换行符转换为HTML换行标签
            escaped_feature = escape_markdown_table_cell(feature)
            escaped_analysis = escape_markdown_table_cell(change_analysis)
            
            # 构建表格行 - 每个特性只占一行，但变更分析内容可以有多行
            row = [str(index), escaped_feature, escaped_analysis]
            markdown_output += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        markdown_output += "\n"
        
        # 添加统计信息
        markdown_output += f"*共找到 {len(key_change_features)} 个包含关键变更的特性*\n"
    else:
        markdown_output += "未找到包含'关键变更'的特性\n"
    
    return markdown_output


def find_key_changes_and_features(board_name: str, feature_list):
    """
    查找变更分析内容中包含"关键变更"字符串的特性，并生成优化后的Markdown表格
    以关键变更内容作为行，显示受影响的特性列表，并增加编号列
    按照非首次使用和首次使用分组，非首次使用排在前面
    
    Args:
        board_name: 板卡名称
        feature_list: 特性列表，包含各特性的详细信息
        
    Returns:
        str: 包含关键变更特性的Markdown表格
    """
    def extract_key_changes(content):
        """
        从变更分析内容中提取关键变更项，过滤掉普通变更内容
        """
        if not content:
            return []
        
        content_str = str(content)
        
        # 检查是否包含关键变更
        if "关键变更" not in content_str:
            return []
        
        # 分割内容，提取关键变更部分
        lines = content_str.split('\n')
        key_changes = []
        in_key_section = False
        current_change = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测关键变更部分的开始
            if "关键变更" in line:
                in_key_section = True
                continue
                
            # 检测其他变更部分的开始（结束关键变更部分）
            if ("普通变更" in line or "其他变更" in line) and in_key_section:
                # 保存当前变更项
                if current_change:
                    key_changes.append(current_change)
                    current_change = ""
                break
                
            # 如果在关键变更部分中
            if in_key_section:
                # 检查是否是新的变更项（通常以"新增-"开头）
                if line.startswith("新增-"):
                    # 保存前一个变更项
                    if current_change:
                        key_changes.append(current_change)
                    current_change = line
                else:
                    # 否则，将当前行添加到当前变更项
                    if current_change:
                        # 添加逗号分隔符（如果当前变更项还没有结束符）
                        if not current_change.endswith((",", "，", ";")):
                            current_change += ","
                        current_change += " " + line
                    else:
                        current_change = line
        
        # 保存最后一个变更项
        if current_change:
            key_changes.append(current_change)
        
        return key_changes
    
    def escape_markdown_table_cell(text):
        """
        转义Markdown表格单元格中的特殊字符，确保表格格式正确
        """
        if not text:
            return ""
        # 转义表格分隔符 |
        text = str(text).replace('|', '\\|')
        return text
    
    # 构建关键变更到特性的映射
    key_change_to_features = {}
    
    for item in feature_list:
        change_analysis = item.get('changeAnalysis', '')
        feature = item.get('feature', '')
        
        # 检查变更分析内容是否包含"关键变更"
        if change_analysis and "关键变更" in str(change_analysis):
            # 提取关键变更项
            key_changes = extract_key_changes(change_analysis)
            
            for change in key_changes:
                if change not in key_change_to_features:
                    key_change_to_features[change] = []
                
                # 避免重复添加同一特性
                if feature not in key_change_to_features[change]:
                    key_change_to_features[change].append(feature)
    
    markdown_output = ""

    # 添加board标题
    markdown_output += f"## 新增{board_name}单板的关键变更内容及波及特性列表:\n\n"

    if key_change_to_features:
        # 将关键变更分为非首次使用和首次使用两组
        non_first_use_changes = []
        first_use_changes = []
        
        for change in key_change_to_features.keys():
            if "非首次使用" in change:
                non_first_use_changes.append(change)
            else:
                first_use_changes.append(change)
        
        # 分别对两组进行排序
        non_first_use_changes.sort()
        first_use_changes.sort()
        
        # 合并两组，非首次使用在前
        sorted_changes = non_first_use_changes + first_use_changes
        
        # 表头
        headers = ["编号", "新增单板关键变更内容", "关键变更内容波及的特性"]
        markdown_output += "| " + " | ".join(headers) + " |\n"
        markdown_output += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # 添加数据行
        for index, change in enumerate(sorted_changes, 1):
            features = key_change_to_features[change]
            
            # 转义表格单元格中的特殊字符
            escaped_change = escape_markdown_table_cell(change)
            
            # 对特性列表进行排序并格式化为多行
            sorted_features = sorted(features)
            escaped_features = "<br>".join([escape_markdown_table_cell(f) for f in sorted_features])
            
            # 构建表格行 - 关键变更内容前面增加"关键变更:<br>"
            formatted_change = "关键变更内容:<br>" + escaped_change
            row = [str(index), formatted_change, escaped_features]
            markdown_output += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        markdown_output += "\n"
        
        # 添加统计信息
        total_changes = len(key_change_to_features)
        total_features = sum(len(features) for features in key_change_to_features.values())
        
        # 分类统计
        non_first_use_count = len(non_first_use_changes)
        first_use_count = len(first_use_changes)
        
        markdown_output += f"*共找到 {total_changes} 个关键变更，影响 {total_features} 个特性*\n"
        markdown_output += f"*其中：非首次使用 {non_first_use_count} 个，首次使用 {first_use_count} 个*\n"
    else:
        markdown_output += "未找到包含'关键变更'的特性\n"
    
    return markdown_output


#查询单板所有特性及需求交付状态
def get_board_key_changed_feature(product_name: str, query_mode:str, board_names: List[str]):

    #print(f"[-DEBUG-] product_name:{product_name}")
    #print(f"[-DEBUG-] board_names:{board_names}")

    # 参数验证
    if not board_names or not isinstance(board_names, list):
        return {
            "code": 400,
            "status": "error", 
            "message": "board_names参数必须是非空字符串数组"
        }

    # 过滤空值和去重
    valid_board_names = list(OrderedDict.fromkeys(
        name.strip() for name in board_names if name and name.strip()
    ))

    if not valid_board_names:
        return {
            "code": 400,
            "status": "error",
            "message": "没有有效的单板名称"
        }

    # 查询所有单板的RDC标识数据
    feature_list = []
    key_changed_results = ""
    
    #print(f"[-DEBUG-] valid_board_names:{valid_board_names}")

    for board_name in valid_board_names:
        # 1. 查询单板在全局状态表中的RDC数据
        query_params = {
            "product": product_name,
            "board": board_name
            }

        #feature_list += querySrcBoardWholeStatusRDCByParams(query_params, markdown_flag= True)
        feature_list += querySrcBoardWholeStatusByParams(query_params, markdown_flag= True)

        print(f"[-DEBUG-] query_params:{query_params}")
        #print(f"[-DEBUG-] feature_list:{feature_list}")

        if not feature_list:
            print(f"单板 {board_name} 在全局状态表中没有特性数据")
            continue

    if  query_mode == "feature":
        key_changed_results = find_feature_and_key_changes(board_name, feature_list)
    else:
        key_changed_results = find_key_changes_and_features(board_name, feature_list)

    print(f"[-DEBUG-] key_changed_results:{key_changed_results}")


    # 构建响应结果
    response_data = {
        "key_changed_results": key_changed_results,
        "summary": {
            "total_boards": len(valid_board_names),
            "found_boards": len(key_changed_results),
            "query_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return response_data

def get_board_change_mode_and_affected_features(change_mode: str):
    support_changed_modes = ['新增客户侧光模块', '新增线路侧光模块', '新增客户侧光层业务', '新增线路侧光层业务', '新增配置类型', 
        '新增硬件子类型', '新增子架适配', '业务FRM芯片_新增单板业务模型', '交换FRM芯片_新增单板业务模型', '业务FRM芯片_新增电层业务',
        '新增开销逻辑', '新增GEARBOX', '新增时钟芯片', '新增控制逻辑']

    if change_mode == 'query_supported_change_mode':
        print(support_changed_modes)
        return support_changed_modes
    else:
        for mode in support_changed_modes:
            if change_mode in mode:
                # 获取原始数据
                raw_results = querySrcFeatureChangeRelation(mode)
                continue
        if len(raw_results) == 0:
            print(f"变更模式[{change_mode}]not supported")
 
        #print(raw_results)

        # 构建markdown表格格式的结果
        markdown_result = f"{change_mode}波及的特性子特性：\n\n"
        markdown_result += "| 特性 | 子特性 |\n"
        markdown_result += "|---|---|\n"
        
        # 按特性分组子特性
        feature_dict = {}
        
        for item in raw_results:
            feature = item.get('feature') or ''  
            sub_feature = item.get('subFeature') or ''
            
            if feature not in feature_dict:
                feature_dict[feature] = []
            
            if sub_feature and sub_feature not in feature_dict[feature]:
                feature_dict[feature].append(sub_feature)
        
        # 生成markdown表格内容
        for feature, sub_features in feature_dict.items():
            # 第一个子特性行显示特性名称
            if sub_features:
                first_sub_feature = sub_features[0]
                markdown_result += f"| {feature} | {first_sub_feature} |\n"
                
                # 其余子特性行特性列留空
                for i in range(1, len(sub_features)):
                    markdown_result += f"| | {sub_features[i]} |\n"
            else:
                # 如果没有子特性，只显示特性
                markdown_result += f"| {feature} |  |\n"
        
        print(markdown_result)
        return markdown_result


