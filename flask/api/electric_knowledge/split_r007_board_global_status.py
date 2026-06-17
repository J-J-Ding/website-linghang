#!/usr/bin/python3
import json
import re
import datetime
import time
import copy
from enum import Enum
from copy import deepcopy
from typing import List, Dict, Any, Set, Optional, Sequence, Iterable, Tuple
from collections import OrderedDict, Counter
from electric_knowledge.front_board_tree_data_service import querySrcBoardTreeByParams, query_board_tree_board_design_url_by_board_name
from electric_knowledge.front_business_speed_type_relation_data_service import querySrcBusinessSpeedTypeByParams
from electric_knowledge.front_board_change_analysis_data_service import addSrcBoardChangeAnalysisData
from electric_knowledge.front_feature_board_relation_data_service import querySrcFeatureBoardRelation
from electric_knowledge.front_board_whole_status_data_service import isBoardWholeStatusRDCByParams,addSrcBoardWholeStatusData,updateSrcBoardWholeStatusData,querySrcBoardWholeStatusByParams, querySrcBoardWholeStatusRDCByParams, deleteChangeAnalysisData, syncSrcBoardWholeStatusDataRDC, queryBoardWholeStatusByField, queryBoardWholeStatusByBoardNameAndPreplanVersion, queryBoardWholeStatusDataByBoardName,  deleteBoardWholeStatusDataByBoardName
from electric_knowledge.front_rdc_fault_data_service import addRdcFaultTableData, queryRdcFaultListByRdcIdentList
from electric_knowledge.utils_pub import pub_get_employ_name
from electric_knowledge.utils_rdc import create_RDC, query_RDC, get_rdc_relation_id_dict, get_rdc_change_req_info_list, create_RDC_MR, update_RDC_relatedWorkItemId,add_tag_RDC
from electric_knowledge.front_feature_change_relation_data_service import querySrcFeatureChangeRelation
from electric_knowledge.front_mr_feature_data_service import querySrcMrFeatureByParams, importExcelMrFeatureData
from electric_knowledge.front_rdc_split_task_data_service import add_task_info_dict, update_task_info_dict, query_task_info_dict_by_task_id
from flask import request, jsonify
from collections import defaultdict
import threading
import logging
import uuid

logger = logging.getLogger("Logger")
start_time = datetime.datetime.now()
request_interval = 0.5

def log_step():
    now_time = datetime.datetime.now()
    logger.info(f'--------now_time:{now_time.strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f"--------cost_time(从开始拆分->当前:秒):{(now_time - start_time).total_seconds():.2f}")

def str_to_list(s: str) -> List[str]:
    """按逗号拆分，去掉首尾空格，并过滤掉空字符串。"""
    return [item for item in (part.strip() for part in s.split(',')) if item]

############### 单板关联特性/子特性规则 start ############################
def need_filter_sub_features(target_feature, reserved_sub_prefix, record: Dict[str, Any]) -> bool:
    """返回 True 表示该记录需要被过滤掉"""
    if record.get("feature") != target_feature:
        return False
    if not record.get("subFeature"):
        return False
    # 是 SFP/SFP+ 且属于目标 feature 的子特性，检查是否在白名单
    sub = record.get("subFeature")
    return not sub.startswith(reserved_sub_prefix)

def filter_records_by_sub_features(target_feature, reserved_sub_prefix, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据 _need_filter 的判定结果，返回保留的记录列表"""
    return [r for r in records if not need_filter_sub_features(target_feature, reserved_sub_prefix, r)]

def filter_by_sub_features(records: List[Dict[str, Any]], blacklist: Iterable[str]) -> List[Dict[str, Any]]:
    """
    返回新列表：去掉 feature 出现在 blacklist 里的所有记录
    """
    # 防止用户把单个字符串当参数
    if isinstance(blacklist, str):
        blacklist = [blacklist]

    black_set = set(blacklist)          # O(1) 查询
    return [r for r in records if r.get('subFeature') not in black_set]

def filter_by_features(records: List[Dict[str, Any]], blacklist: Iterable[str]) -> List[Dict[str, Any]]:
    """
    返回新列表：去掉 feature 出现在 blacklist 里的所有记录
    """
    # 防止用户把单个字符串当参数
    if isinstance(blacklist, str):
        blacklist = [blacklist]

    black_set = set(blacklist)
    return [r for r in records if r.get('feature') not in black_set]

def filter_color_svc_basic_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    过滤"F010101-E-彩光业务基础"的子特性：
    当板卡为 SFP/SFP+ 模块时，只保留
        FS010101-01-彩光业务-波长调谐
    其余子特性全部丢弃；其它情况原样返回。
    """
    target_feature = "F010101-E-彩光业务基础"
    # 需要保留的子特性前缀（可精确或前缀匹配，这里用前缀，方便扩展）
    reserved_sub_prefix = (
        "FS010101-01-E-彩光业务-波长调谐"
    )
    return filter_records_by_sub_features(target_feature, reserved_sub_prefix, records)

def filter_color_svc_admin_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    target_feature = "F010121-E-彩光业务维护管理"
    # 需要保留的子特性前缀（可精确或前缀匹配，这里用前缀，方便扩展）
    reserved_sub_prefix = (
        "FS010121-03-E-彩光模块核心模块复位",
        "FS010121-04-E-彩光模块模块热插拔",
        "FS010121-05-E-彩光光模块属性上报",
        "FS010121-06-E-彩光模块激光器设置",
        "FS010121-10-E-彩光模块光模块商务包装"
    )
    #只保留target_feature特性中的reserved_sub_prefix子特性
    return filter_records_by_sub_features(target_feature, reserved_sub_prefix, records)

def filter_color_svc_not_involved_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F010131-E-彩光业务光模块能力上报",
        "F010132-E-彩光业务光标签应用",
        "F010133-E-彩光业务SOP防雷应用",
        "F010134-E-彩光业务APO功率查询应用",
        "F070133-E-业务单板-时间性能-光模升级加载+中断时间要求",
        "F070181-E-业务单板-巡检-线路侧光模块巡检"
    )
    # 过滤掉blacklist中的特性子特性
    return filter_by_features(records, blacklist)

def filter_gray_svc_not_involved_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F010201-E-灰光业务基础",
        "F010221-E-灰光业务维护管理",
        "F010222-E-灰光业务性能告警"
    )
    # 过滤掉blacklist中的特性子特性
    return filter_by_features(records, blacklist)

def filter_gray_svc_admin_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    target_feature = "F010221-E-灰光业务维护管理"
    # 需要保留的子特性前缀（可精确或前缀匹配，这里用前缀，方便扩展）
    reserved_sub_prefix = (
        "FS010221-03-E-灰光模块-光模块属性上报"
    )
    #只保留target_feature特性中的reserved_sub_prefix子特性
    return filter_records_by_sub_features(target_feature, reserved_sub_prefix, records)

def filter_cfp_mod_not_involved_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    target_feature = "F010201-E-灰光业务基础"
    # 需要保留的子特性前缀（可精确或前缀匹配，这里用前缀，方便扩展）
    reserved_sub_prefix = (
        "FS010201-11-E-cfp/cfp2灰光模块"
    )
    return filter_records_by_sub_features(target_feature, reserved_sub_prefix, records)

def filter_ele_svc_admin_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F030103-E-电层保护-支路冗余oduk通道层1+1保护",
        "F040114-E-O业务GCC-GFP协议电监控"
    )
    # 过滤掉blacklist中的特性子特性
    return filter_by_features(records, blacklist)

def filter_gray_sub_feature_by_cfp(data: List[Dict], module_str: str) -> List[Dict]:
    """
    仅对 feature 为 F010201-E-灰光业务基础" 的条目按关键字过滤；
    其余 feature 直接保留。返回顺序与原数据一致。
    """
    if not module_str.strip():
        return data[:]          # 无关键字，全部保留
    feature = data
    keywords = {kw.strip().lower() for kw in module_str.split(',') if kw.strip()}
    if not keywords:
        return data[:]
    if 'qsfpdd' in keywords:
        keywords.remove('qsfpdd')
        keywords.add('qsfp-dd(8*56)')
    if 'qsfpdd' not in keywords and 'sfp' in keywords:
        data = filter_gray_svc_admin_features(data)
    if 'cfp' not in keywords:
        blacklist = (
            "FS050132-02-E-光模块硬件异常告警"
        )
        feature = filter_by_sub_features(data, blacklist)

    result = []
    for item in feature:
        if item.get("feature") != "F010201-E-灰光业务基础":
            result.append(item)               # 非灰光，直接保留
            continue
        # 灰光条目：subFeature 包含任一关键字则保留
        if any(k in item.get("subFeature", "").lower() for k in keywords):
            result.append(item)
            # logger.info(item)
    return result

def extract_m_number(board_name: str) -> Optional[int]:
    m = re.match(r'(?i)M(\d+)', board_name or '')
    return int(m.group(1)) if m else None

def filter_m_val_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F070121-E-业务单板-平滑升级-M值替换平滑升级"
    )
    return filter_by_features(records, blacklist)

def filter_new_board_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F070141-E-业务单板-防呆-备件替换防呆(Flash、5347、逻辑等器件)"
    )
    return filter_by_features(records, blacklist)

def filter_p_svc_cross_admin_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "F020406-E-P业务交叉管理"
    )
    return filter_by_features(records, blacklist)

def filter_board_sa_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blacklist = (
        "FS050101-01-E-SA流控预防/检测/修复/隔离功能",
        "FS050101-02-E-SA交换系统非对称防呆",
        "FS050101-03-E-SA单播路由过滤及多播路由计算功能",
        "FS050101-11-E-SF流控预防/检测/修复/隔离功能",
        "FS050102-01-E-单板启动SA优雅上线",
        "FS050102-02-E-单板复位SA优雅下线",
        "FS050102-11-E-单板启动SF优雅上线",
        "FS050102-12-E-单板复位SF优雅下线"
    )
    return filter_by_sub_features(records, blacklist)

def filter_key_cmp_temp_features(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    target_feature = "F050111-E-关键器件温度触发风扇调整"
    # 需要保留的子特性前缀（可精确或前缀匹配，这里用前缀，方便扩展）
    reserved_sub_prefix = (
        "FS050111-01-E-单板关键器件温度上报",
        "FS050111-03-E-单板核心器件超温越限告警"
    )
    return filter_records_by_sub_features(target_feature, reserved_sub_prefix, records)

# ---------- 1. 通用业务分类器 ----------
def analyze_business_services(input_str: str,
                              rules: List[Tuple[str, Set[str]]]) -> str:
    """
    输入:
        input_str: 逗号分隔的业务关键字
        rules: [(业务类型名, {关键字集合}), ...]
    输出:
        命中的业务类型名，用逗号拼接，每类最多一次
    """
    if not input_str.strip():
        return ""
    services = {s.strip() for s in input_str.split(',') if s.strip()}
    hit = [name for name, key_set in rules if services & key_set]
    return ",".join(hit)

def should_keep_features(item: Dict, target_feature, all_names) -> bool:
    """
    只过滤 feature 为 target_feature 且 subFeature 包含 all_names 中特定名称的项，其他情况全部保留。
    """
    if item.get("feature") != target_feature:
        return True
    sub = item.get("subFeature", "")
    for n in all_names:
        # logger.info(f"------n: {n}, sub: {sub}----")
        if n in sub:
            return False
    return True 
        
# ---------- 2. 通用 feature 过滤器 ----------
def filter_svc_sub_feature(data: List[Dict],
                       input_str: str,
                       target_feature: str,
                       rules:List[Tuple[str, Set[str]]]) -> List[Dict]:
    """
    仅对 feature==target_feature 的条目按 module_str 关键字过滤；
    其余 feature 直接保留。顺序不变。
    """
    all_names = {name for name, _ in rules}
    module_str = analyze_business_services(input_str, rules)
    if not module_str.strip():
        return [
            item for item in data
            if should_keep_features(item, target_feature, all_names)
        ]
    keywords = {kw.strip().upper() for kw in module_str.split(',') if kw.strip()}
    if not keywords:
        return [
            item for item in data
            if should_keep_features(item, target_feature, all_names)
        ]
    #logger.info(keywords)
    #logger.info(all_names)
    return[item for item in data 
            if should_keep_features(item, target_feature, all_names) 
            or any(k in item.get("subFeature", "").upper() for k in keywords)
    ]

def filter_svc_feature(data: List[Dict],
                       input_str: str,
                       target_feature: str,
                       rules:List[Tuple[str, Set[str]]]) -> List[Dict]:
    """
    仅对 feature==target_feature 的条目按 module_str 关键字过滤,不包含关键字直接删除；
    其余 feature 直接保留。顺序不变。
    """
    module_str = analyze_business_services(input_str, rules)
    blacklist = (target_feature)
    if not module_str.strip():
        return filter_by_features(data, blacklist)
    keywords = {kw.strip().upper() for kw in module_str.split(',') if kw.strip()}
    if not keywords:
        return filter_by_features(data, blacklist)
    return [
        item if item.get("feature") != target_feature
        else item
        for item in data
        if item.get("feature") != target_feature or any(k in item.get("feature").upper() for k in keywords)
    ]

# ---------- 3. 把原先写死的数据提出来当作"配置" ----------

gs_feature_f010133 = "F010133-E-彩光业务SOP防雷应用"
gs_feature_f010133_info = [
    ('SOP防雷',
        {"OTU4"})
    ]

gs_feature_f040128 = "F040128-E-O业务带内时钟"
gs_feature_f040129 = "F040129-E-O业务带内时间"
gs_feature_f040128_info = [
    ('OTN',
        {"OTU0", "OTU1", "OTU2", "OTU3", "OUTC1", "OUTC2", "OUTC4", "OUTC8"}),
    ("GFP-F",
        {"GE", "10GE", "40GE", "100GE"}),
    ("IMP",
        {"200GE", "400GE", "800GE"}),
    ("SDH",
        {"STM1", "STM4", "STM16", "STM64"})
    ]

gs_feature_f040140 = "F040140-E-O业务OTN-TTI自动发现"
gs_feature_f040140_info_l = [
    ('O业务OTN-TTI自动发现',
        {"OTU0", "OTU1", "OTU2"})
    ]
gs_feature_f040140_info_c = [
    ('O业务OTN-TTI自动发现',
        {"OTU0", "OTU1", "OTU2", "OTU3", "OTU4"})
    ]

gs_feature_f040141 = "F040141-E-O业务以太网-LLDP邻居自动发现"
gs_feature_f040141_info = [
    ('LLDP邻居自动发现',
        {'FE', 'GE', '10GE', '25GE', '50GE', "40GE", '100GE', '200GE', '400GE', '800GE'})
    ]

gs_feature_f070157 = "F070157-E-业务单板-定位定界-Error_Info上报/Error_dump/Tid信令跟踪"
gs_feature_f070157_info = [
    ('ODU业务',
        {"L_O", "C_O", "E_EoO", "E_EoS_O"}),
    ('OSU业务',
        {"L_OSU", "E_EoOSU", "C_OSU", "B_OSU_O"}),
    ('VC业务',
        {"L_V", "E_EoS", "C_V", "B_V_FG", "B_V_O", "L_FG_V", "L_SDH_V"}),
    ('FG业务',
        {"L_FG", "C_FG", "C_V_FG", "E_EoFG", "B_FG_O", "B_V_FG"})
    ]

gs_feature_f020305 = "F020305-E-FG业务维护管理"
gs_feature_f020205 = "F020205-E-OSU业务维护管理"
gs_feature_f020305_info = [
    ('以太网GFP-FCS模式',
        {'GE', '10GE', "40GE", '100GE'})
    ]

gs_feature_f020101 = "F020101-E-O业务基础"
gs_feature_f020101_info = [
    ('odu->otucn业务',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
        'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('odu->otuk业务',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}),
    ('otu业务端口绑定',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16'}),
    ('odu->flex-o业务',
        {'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('flex-o业务端口绑定',
        {'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('odu->以太网业务',
        {'FE', 'GE', '10GE', '25GE', '50GE', "40GE", '100GE', '200GE', '400GE', '800GE'}),
    ('odu->otn业务',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}),
    ('odu->sdh业务',
        {'STM1', 'STM4', 'STM16', 'STM64'}),
    ('odu->other客户业务',
        {'E1', 'FC', '1GFC', '2GFC', '4GFC', '8GFC', '10GFC', '16GFC', '32GFC'}),
    ('odu->flex-e透传',
        {'25GE-PHY', '50GE-PHY', '100GE-PHY', '200GE-PHY', '400GE-PHY', '800GE-PHY'})
    ]

gs_feature_f020102 = "F020102-E-O业务性能告警"
gs_feature_f020102_info = [
    ('OTUCn/ODUCn高阶',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
        'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('OTUk/ODUk高阶',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}),
    ('FlexO-i',
        {'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('以太网',
        {'FE', 'GE', '10GE', '25GE', "40GE", '50GE', '100GE', '200GE', '400GE', '800GE'}),
    ('Other客户侧',
        {'E1', 'FC', '1GFC', '2GFC', '4GFC', '8GFC', '10GFC', '16GFC', '32GFC'}),
    ('SDH MS/RS',
        {'STM1', 'STM4', 'STM16', 'STM64'}),
    ('FlexE 透传',
        {'25GE-PHY', '50GE-PHY', '100GE-PHY', '200GE-PHY', '400GE-PHY', '800GE-PHY'})
]

gs_feature_f020103 = "F020103-E-O业务开销配置管理"
gs_feature_f020103_info = [
    ('OTUCn/ODUCn',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
        'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('OPUCn-PT/MSI开销',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
        'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('OTUk/ODUk',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}),
    ('OPUk-PT/MSI开销',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}),
    ('FlexO',
        {'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f020104 = "F020104-E-O业务维护信号"
gs_feature_f020104_info = [
    ('ODUCn高阶端口锁定',
        {'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('ODUk高阶',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'})
]

gs_feature_f020105 = "F020105-E-O业务维护管理"
gs_feature_f020105_info = [
    ('以太网业务FEC配置',
        {'FE', 'GE', '10GE', '25GE', "40GE", '50GE', '100GE', '200GE', '400GE', '800GE'}),
    ('以太网GFP-FCS模式配置',
        {'FE', 'GE', '10GE', '100GE'}),
    ('光口PRBS',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]
gs_feature_f020105_opt_info = [
    ('OTN业务FEC配置',
        {'SFP', 'QSFP', 'CFP'})
]

gs_feature_f040118 = "F040118-E-O业务扩展GCC电监控"
gs_feature_f040118_info = [
    ('ESC-扩展GCC',
        {'OTU2', 'OTU1', 'OTU0'})
]

gs_feature_f020106 = "F020106-E-O业务交叉管理"
gs_feature_f020106_info = [
    ('2A1Z',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('2A2Z',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f030101 = "F030101-E-电层保护-oduk 通道层1+1保护"
gs_feature_f030101_info = [
    ('触发倒换',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f030102 = "F030102-E-电层保护-oduk通道层1+1级联保护"
gs_feature_f030102_info = [
    ('oduk1+1',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f030103 = "F030103-E-电层保护-支路冗余oduk通道层1+1保护"
gs_feature_f030103_info = [
    ('触发倒换',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f030121 = "F030121-E-O业务电层wason"
gs_feature_f030121_info = [
    ('wason',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f030161 = "F030161-E-O业务光层wason"
gs_feature_f030161_info = [
    ('wason',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f040109 = "F040109-E-O业务DM双向时延测量"
gs_feature_f040109_info = [
    ('高阶ODU',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16'})
]

gs_feature_f040115 = "F040115-E-O业务GCC-HDLC协议电监控"
gs_feature_f040115_info = [
    ('ESC',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f040116 = "F040116-E-O业务GCC电监控默认开通"
gs_feature_f040116_info = [
    ('ESC',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f040117 = "F040117-E-O业务GCC电监控保持功能"
gs_feature_f040117_info = [
    ('ESC',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f040120 = "F040120-E-O业务LF延迟下插"
gs_feature_f040120_info = [
    ("GFP",
        {"GE", "10GE", "40GE", "100GE"}),
    ("IMP",
        {"200GE", "400GE", "800GE"}),
]

gs_feature_f040132 = "F040132-E-O业务无损带宽调整"
gs_feature_f040132_info = [
    ('BW-O业务',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'})
]

gs_feature_f050121 = "F050121-E-数据一致性-下行对账(CLI)-对账结果上报-数据不一致告警及原因上报"
gs_feature_f050121_info = [
    ('FEC命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('恢复模式命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]

gs_feature_f050122 = "F050122-E-数据一致性-下行自动纠正(CLI)"
gs_feature_f050122_info = [
    ('FEC命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('恢复模式命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('FS050122-12-E',
        {'OTU4', 'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16'})
]

gs_feature_f050123 = "F050123-E-数据一致性-上行对账(CLI)，支持底层配置查询"
gs_feature_f050123_info = [
    ('FEC命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'}),
    ('恢复模式命令',
        {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4', 
         'OTUC1', 'OTUC2', 'OTUC4', 'OTUC8', 'OTUC10', 'OTUC12', 'OTUC16',
         'FlEXO-1', 'FlEXO-2', 'FlEXO-4', 'FlEXO-8', 'FlEXO-12', 'FlEXO-6'})
]


# ---------- 4. 兼容原函数名的快捷封装 ----------
def filter_color_sop_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_feature(data, module_str, gs_feature_f010133, gs_feature_f010133_info)

def filter_o_svc_clock_time_feature(data: List[Dict], module_str: str) -> List[Dict]:
    feature = filter_svc_sub_feature(data, module_str, gs_feature_f040128, gs_feature_f040128_info)
    feature = filter_svc_sub_feature(feature, module_str, gs_feature_f040129, gs_feature_f040128_info)
    return feature

def filter_o_svc_otn_tti_feature(data: List[Dict], module_str: str, board_type: str, flag: bool) -> List[Dict]:
    if "客户侧C卡" in board_type:
        return filter_svc_feature(data, module_str, gs_feature_f040140, gs_feature_f040140_info_c)
    elif "线路侧L卡" in board_type and flag:
        return filter_svc_feature(data, module_str, gs_feature_f040140, gs_feature_f040140_info_l) 
    else:
        return filter_by_features(data, (gs_feature_f040140))

def filter_o_svc_lldp_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_feature(data, module_str, gs_feature_f040141, gs_feature_f040141_info)

def filter_error_info_sub_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f070157, gs_feature_f070157_info)

def filter_fg_osu_svc_admin_feature(data: List[Dict], module_str: str) -> List[Dict]:
    feature = filter_svc_sub_feature(data, module_str, gs_feature_f020305, gs_feature_f020305_info)
    feature = filter_svc_sub_feature(feature, module_str, gs_feature_f020205, gs_feature_f020305_info)
    return feature

def filter_o_svc_basic_feature(data: List[Dict], module_str: str, cfg_type: str) -> List[Dict]:
    if "Variable" not in cfg_type:
        blacklist = (
        "FS020101-22-E-odu->flex-e感知业务(FLEXEoO-C卡)",
        "FS020101-23-E-odu->flex-e终结业务(FLEXEoO-C卡)",
        "FS020101-06-E-variable-otucn业务动态切换(OTUCn-O-L卡)"
    )
    else:
        blacklist = (
        "FS020101-22-E-odu->flex-e感知业务(FLEXEoO-C卡)",
        "FS020101-23-E-odu->flex-e终结业务(FLEXEoO-C卡)"
    )
    feature = filter_by_sub_features(data, blacklist)
    feature = filter_svc_sub_feature(feature, module_str, gs_feature_f020101, gs_feature_f020101_info)
    
    # # 支线路合一分别过滤
    # otu_set = {'OTU0', 'OTU1', 'OTU2', 'OTU3', 'OTU4'}
    # # 分割字符串，去除首尾空格，并过滤空元素
    # l_svc_types = [s.strip() for s in svc_type_l.split(',') if s.strip()]
    # c_svc_types = [s.strip() for s in svc_type_c.split(',') if s.strip()]
    # # 如果没有交集（即不包含任何OTU元素），则过滤blacklist
    # if not set(svc_type_l) & otu_set:
    #     blacklist = (
    #         "FS020101-03-E-odu->otuk业务",
    #         "FS020101-04-E-终结odu->otuk业务"
    #     )
    #     feature = filter_by_sub_features(feature, blacklist)
    # if not set(c_svc_types) & otu_set:
    #     blacklist = (
    #         "FS020101-32-E-odu->otn业务(OTNoO-C卡)"
    #     )
    #     feature = filter_by_sub_features(feature, blacklist)
    return feature
    
def filter_o_svc_perf_alm_feature(data: List[Dict], module_str: str) -> List[Dict]:
    blacklist = (
        "FS020102-22-E-FlexE 感知性能",
        "FS020102-23-E-FlexE 感知告警",
        "FS020102-24-E-FlexE 终结性能",
        "FS020102-25-E-FlexE 终结告警"
    )
    feature = filter_by_sub_features(data, blacklist)
    feature = filter_svc_sub_feature(feature, module_str, gs_feature_f020102, gs_feature_f020102_info)
    return feature

def filter_o_svc_oh_cfg_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f020103, gs_feature_f020103_info)

def filter_o_svc_maintain_signal_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f020104, gs_feature_f020104_info)

def filter_o_svc_maintain_admin_feature(data: List[Dict], module_str: str, opt_type: str) -> List[Dict]:
    feature = filter_svc_sub_feature(data, module_str, gs_feature_f020105, gs_feature_f020105_info)
    feature = filter_svc_sub_feature(feature, opt_type, gs_feature_f020105, gs_feature_f020105_opt_info)
    return feature
    
def filter_o_svc_extend_gcc_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040118, gs_feature_f040118_info)

def filter_o_svc_cross_admin_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f020106, gs_feature_f020106_info)

def filter_ele_oduk_prt_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f030101, gs_feature_f030101_info)

def filter_ele_oduk_cascade_prt_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f030102, gs_feature_f030102_info)

def filter_ele_tru_oduk_prt_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f030103, gs_feature_f030103_info)

def filter_o_svc_ele_wason_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f030121, gs_feature_f030121_info)

def filter_o_svc_opt_wason_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f030161, gs_feature_f030161_info)

def filter_o_svc_gcc_hdlc_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040115, gs_feature_f040115_info)

def filter_o_svc_gcc_default_on_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040116, gs_feature_f040116_info)

def filter_o_svc_lf_delay_insert_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040117, gs_feature_f040117_info)

def filter_o_svc_gcc_maintain_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040120, gs_feature_f040120_info)

def filter_o_svc_bw_adj_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f040132, gs_feature_f040132_info)

def filter_cli_reconciliation_report_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f050121, gs_feature_f050121_info)

def filter_cli_auto_correction_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f050122, gs_feature_f050122_info)

def filter_cli_cfg_query_feature(data: List[Dict], module_str: str) -> List[Dict]:
    return filter_svc_sub_feature(data, module_str, gs_feature_f050123, gs_feature_f050123_info)

def filter_other_feature(board_tree, features) -> List[Dict]:
    svc_frm = board_tree.get("业务FRM芯片","")
    cross_frm = board_tree.get("交换FRM芯片","")
    gearbox = board_tree.get("GEARBOX","")
    port_num = board_tree.get("物理端口数量","")

    logger.info(f"svc_frm: {svc_frm}, cross_frm: {cross_frm}, gearbox: {gearbox}, port_num: {port_num}")
    blacklist = ()
    if not svc_frm:
        logger.info("svc_frm is null")
        blacklist += (
        "FS060101-08-E-业务单板-基础启动-成帧芯片-framer初始化",
        "FS080101-08-E-业务单板工装-基础启动-成帧芯片-framer初始化"
        )
    if not cross_frm:
        logger.info("cross_frm is null")
        blacklist += (
        "FS060101-09-E-业务单板-基础启动-成帧芯片-SA初始化",
        "FS080101-09-E-业务单板工装-基础启动-成帧芯片-SA初始化",
        "FS080102-41-E-背板链路测试项"
        )
    if not gearbox:
        logger.info("gearbox is null")
        blacklist += (
        "FS060101-07-E-业务单板-基础启动-CDR芯片初始化",
        "FS080101-07-E-业务单板工装-基础启动-CDR芯片初始化",    
        "FS080102-31-E-gearbox芯片测试项"
        )
    if not port_num:
        logger.info("port_num is null")
        blacklist += (
        "FS060101-10-E-业务单板-基础启动-光模块初始化",
        "FS070171-03-E-端口功耗性能上报",
        "FS070171-04-E-空闲端口查询",
        "FS070171-06-E-空闲端口手动关断",
        "FS080101-10-E-业务单板工装-基础启动-光模块初始化"
        )
    return filter_by_sub_features(features, blacklist)

def filter_c_or_l_feature(board_tree, features) -> List[Dict]:
    svc_frm = board_tree.get("业务FRM芯片","")
    cross_frm = board_tree.get("交换FRM芯片","")
    gearbox = board_tree.get("GEARBOX","")
    port_num = board_tree.get("物理端口数量","")

    logger.info(f"svc_frm: {svc_frm}, cross_frm: {cross_frm}, gearbox: {gearbox}, port_num: {port_num}")
    blacklist = ()
    if not svc_frm:
        logger.info("svc_frm is null")
        blacklist += (
        "FS060101-08-E-业务单板-基础启动-成帧芯片-framer初始化",
        "FS080101-08-E-业务单板工装-基础启动-成帧芯片-framer初始化"
        )
    if not cross_frm:
        logger.info("cross_frm is null")
        blacklist += (
        "FS060101-09-E-业务单板-基础启动-成帧芯片-SA初始化",
        "FS080101-09-E-业务单板工装-基础启动-成帧芯片-SA初始化",
        "FS080102-41-E-背板链路测试项"
        )
    if not gearbox:
        logger.info("gearbox is null")
        blacklist += (
        "FS060101-07-E-业务单板-基础启动-CDR芯片初始化",
        "FS080101-07-E-业务单板工装-基础启动-CDR芯片初始化",    
        "FS080102-31-E-gearbox芯片测试项"
        )
    if not port_num:
        logger.info("port_num is null")
        blacklist += (
        "FS060101-10-E-业务单板-基础启动-光模块初始化",
        "FS070171-03-E-端口功耗性能上报",
        "FS070171-04-E-空闲端口查询",
        "FS070171-06-E-空闲端口手动关断",
        "FS080101-10-E-业务单板工装-基础启动-光模块初始化"
        )
    return filter_by_sub_features(features, blacklist)

def filter_shelf_feature(board_tree, features) -> List[Dict]:
    board_name = board_tree.get("board")
    shelf_type = board_tree.get("单板支持的子架", "")
    if not shelf_type:
        logger.info("shelf_type is null")
        return features
    s_type = process_shelf_type_string(shelf_type)

    shelf_type_g2 = filter_shelf_type_patterns(s_type, 'G2', 'G2-E')
    shelf_type_s3f = filter_shelf_type_patterns(s_type, 'M1S3F', 'M1S3F-E')
    shelf_type_s3fe = filter_shelf_type_patterns(s_type, 'M2S3F-E(B)', 'M2S3F-E(FB)')
    logger.info(f"shelf_type:{shelf_type},shelf_type_g2:{shelf_type_g2}, shelf_type_s3f:{shelf_type_s3f}, shelf_type_s3fe:{shelf_type_s3fe}")
    if len(shelf_type_g2) > 0 and len(shelf_type_s3f) > 0 and len(shelf_type_s3fe) > 0:
        return features
    if len(shelf_type_g2) < 1 and len(shelf_type_s3f) < 1 and len(shelf_type_s3fe) < 1:
        blacklist = (
        "F020601-E-背板带宽动态调整"
        )
        return filter_by_features(features, blacklist)
    if len(shelf_type_g2) < 1:
        blacklist = (
        "FS020601-01-E-G2/G2-E(1+1)->G2/G2-E(3+1)背板带宽动态调整"
        )
        features = filter_by_sub_features(features, blacklist)
    if len(shelf_type_s3f) < 1:
        blacklist = (
        "FS020601-02-E-S3F/S3F-E-1T(3+2)->S3F/S3F-E-1T(7+2)背板带宽动态调整"
        )
        features = filter_by_sub_features(features, blacklist)
    if len(shelf_type_s3fe) < 1:
        blacklist = (
        "FS020601-03-E-S3F-E-1.6T(4+2)->S3F-E-1.6T(7+2)背板带宽动态调整"
        )
        features = filter_by_sub_features(features, blacklist)

    return features

def filter_details_features_by_board_type(board_tree, features, is_c_flag=False):
    otn_tti_flag = True
    board_name = board_tree.get("board","")
    board_type = board_tree.get("板卡类型","")
    mod_type_l = board_tree.get("线路侧光模块","")
    mod_type_c = board_tree.get("客户侧光模块","")
    svc_type_l = board_tree.get("线路侧电层业务","")
    svc_type_c = board_tree.get("客户侧电层业务","")
    opt_svc_l = board_tree.get("线路侧光层业务","")
    opt_svc_c = board_tree.get("客户侧光层业务","")

    # 过滤没有器件的子特性
    features = filter_other_feature(board_tree, features)

    # 客户侧模块
    if is_c_flag:
        svc_type = svc_type_c
        opt_svc = opt_svc_c
        mod_cfp = get_package_types_cfp(mod_type_c)
        features = filter_gray_sub_feature_by_cfp(features, mod_cfp)
    else:
        svc_type = svc_type_l
        opt_svc = opt_svc_l
        # 线路侧模块
        if is_gray_optical_mod(mod_type_l):
            features = filter_color_svc_basic_features(features)    # 2.1 F010101-E-彩光业务基础
            features = filter_color_svc_admin_features(features)    # 2.2 F010121-E-彩光业务维护管理
            features = filter_color_svc_not_involved_features(features) # 2.3 F010130/F010131/F010132/F010133/F070181特性
            mod_cfp = get_package_types_cfp(mod_type_l)
            features = filter_gray_sub_feature_by_cfp(features, mod_cfp)    # 2.4 F010102-E-灰光业务基础
        elif is_cfp_optical_mod(mod_type_l):
            features = filter_cfp_mod_not_involved_features(features) 
            otn_tti_flag = False
        else:
            features = filter_gray_svc_not_involved_features(features)
        features = filter_color_sop_feature(features, svc_type_l)   # 2.3 F010133-E-彩光业务SOP防雷应用

    m_val = extract_m_number(board_name)
    if m_val == 1:
        features = filter_m_val_features(features)
    features = filter_new_board_features(features)

    board_svc_mod = board_tree.get("单板业务模型").replace("/", ",")
    features = filter_error_info_sub_feature(features, board_svc_mod)
    
    # 电层业务
    features = filter_ele_svc_admin_features(features)
    features = filter_o_svc_clock_time_feature(features, svc_type)
    features = filter_o_svc_otn_tti_feature(features, svc_type, board_type, otn_tti_flag)
    features = filter_o_svc_lldp_feature(features, svc_type) 
    features = filter_fg_osu_svc_admin_feature(features, svc_type)
    features = filter_o_svc_extend_gcc_feature(features, svc_type)
    cfg_type = board_tree.get("单板配置类型")
    if not cfg_type:
        cfg_type = ''
    features = filter_o_svc_basic_feature(features, svc_type, cfg_type) 
    features = filter_o_svc_perf_alm_feature(features, svc_type) 
    features = filter_o_svc_oh_cfg_feature(features, svc_type) 
    features = filter_o_svc_maintain_signal_feature(features, svc_type) 
    
    features = filter_o_svc_cross_admin_feature(features, svc_type) 
    features = filter_ele_oduk_prt_feature(features, svc_type) 
    features = filter_ele_oduk_cascade_prt_feature(features, svc_type) 
    features = filter_ele_tru_oduk_prt_feature(features, svc_type) 
    features = filter_o_svc_ele_wason_feature(features, svc_type) 
    features = filter_o_svc_opt_wason_feature(features, svc_type) 
    features = filter_o_svc_gcc_hdlc_feature(features, svc_type) 
    features = filter_o_svc_gcc_default_on_feature(features, svc_type) 
    features = filter_o_svc_lf_delay_insert_feature(features, svc_type) 
    features = filter_o_svc_gcc_maintain_feature(features, svc_type) 
    features = filter_cli_reconciliation_report_feature(features, svc_type) 
    features = filter_cli_auto_correction_feature(features, svc_type) 
    features = filter_cli_cfg_query_feature(features, svc_type) 
    features = filter_o_svc_bw_adj_feature(features, svc_type) 

    features = filter_shelf_feature(board_tree, features)
    features = filter_o_svc_maintain_admin_feature(features, svc_type, opt_svc) 
    
    product_name = board_tree.get("产品")
    if "9700" not in product_name:
        features = filter_p_svc_cross_admin_features(features)
        features = filter_board_sa_features(features)

    port_list = board_tree.get("物理端口数量")
    if not port_list:
        port_list = 'C0'
    if max(map(int, re.findall(r'\d+', port_list))) < 2:
        features = filter_key_cmp_temp_features(features)
    
    # 统计每个 feature 出现的次数
    feat_cnt = Counter(d['feature'] for d in features)
    # 过滤掉 feature 值只出现一次的内容
    # filtered = [d for d in features if feat_cnt[d['feature']] > 1]
    filtered = [d for d in features if feat_cnt[d['feature']] > 1 or (feat_cnt[d['feature']] == 1 and d['subFeature'])]

    # logger.info(features)    
    return filtered    
############### 单板关联特性/子特性规则 end ############################

def split_multiline(text: str) -> List[str]:
    """
    将多行文本按逗号或换行符分割为列表，并去除空白字符
    """
    if not text:
        return []
    parts = re.split(r'[,\n]+', text)
    return [p.strip() for p in parts if p.strip()]

def is_gray_optical_mod(input_string: str) -> bool:
    """
    检查输入字符串是否包含列表 [CFP, QSFP, QSFPDD] 中的任意一个数据。
    如果包含，则返回"彩光"，否则返回"灰光"。

    :param input_string: 输入字符串
    :return: "彩光"或"灰光"
    """
    if not input_string:
        return False
    # 定义需要检查的关键字列表
    keywords = ["QSFPDD", "QSFP", "SFP"]
    
    # 将输入字符串转换为大写，以便进行大小写不敏感的比较
    input_string_upper = input_string.upper()
    
    # 检查输入字符串中是否包含列表中的任意一个关键字
    for keyword in keywords:
        if keyword in input_string_upper:
            return True
    
    # 如果没有找到任何关键字，则返回"灰光"
    return False

def is_cfp_optical_mod(input_string: str) -> bool:
    # 定义需要检查的前缀列表
    prefixes = ["CFP", "CFP2"]
    
    # 将输入字符串转换为大写，以便进行大小写不敏感的比较
    input_string_upper = input_string.upper()
    
    # 检查输入字符串是否以列表中的任意一个前缀开头
    for prefix in prefixes:
        if input_string_upper.startswith(prefix):
            return True
    return False

def generate_simple_add_analysis(values: List[str]) -> str:
    """
    对于简单的新增项（如子架、端口数量、配置类型等），直接生成"新增-xxx"格式
    """
    if not values:
        return ""
    return ";\n ".join([f"新增-单板产品形态要素-单板配置类型因子-{v}因子取值" for v in values])

def generate_simple_add_analysis_shelf(values: List[str]) -> str:
    """
    对于简单的新增项（如子架、端口数量、配置类型等），直接生成"新增-xxx"格式
    """
    if not values:
        return ""
    return ";\n ".join([f"新增-单板产品形态要素-单板支持的子架因子-{v}子架因子取值" for v in values])

def generate_simple_add_analysis_port(values: List[str]) -> str:
    """
    对于简单的新增项（如子架、端口数量、配置类型等），直接生成"新增-xxx"格式
    """
    if not values:
        return ""
    return ";\n ".join([f"新增-单板产品形态要素-物理端口数量因子-{v}端口因子取值" for v in values])

def get_product_factor_by_board(board_name: str):
    """
    根据单板名称查询其"产品因子"
    :param board_name: 单板名称，例如 "M4C4R(80A1H)"
    :return: 产品因子字符串；若未查到则返回空字符串
    """
    params = {"board": board_name}

    resp = querySrcBoardTreeByParams(params, markdown_flag=True)
    if len(resp) > 0 :
        return resp[0]
    else:
        logger.info("未找到单板数据")
        return []

def get_board_by_factor(factor_name: str, factor_val: str) -> List[Dict[str, Any]]:
    """
    根据指定因子名与值，查询并返回匹配的单板列表。
    若未查询到，打印提示并返回空列表。
    """
    params = {"factorTypeCn":factor_name,
              "factorValue": factor_val}

    resp = querySrcBoardTreeByParams(params, markdown_flag=True)
    if resp:
        return resp
    logger.info("未找到单板数据")
    return []

def get_board_by_factor2(factor_name: str, factor_val: str, factor_name2: str, factor_val2: str) -> List[Dict[str, Any]]:
    """
    根据指定因子名与值，查询并返回匹配的单板列表。
    若未查询到，打印提示并返回空列表。
    """
    params = {"factorTypeCn":factor_name + ',' + factor_name2,
              "factorValue": factor_val + ',' + factor_val2}

    resp = querySrcBoardTreeByParams(params, markdown_flag=True)
    if resp:
        return resp
    logger.info("未找到单板数据")
    return []

# =============================================
# 核心处理函数
# =============================================

#================ 1 单板状态表特性子特性填写==============
# ---------- 1. 固定模板 ----------
TEMPLATE = {
    "id": "1",
    "parent": '2',
    "changeAnalysis": "",
    "mileStone": "",
    "rdcTitle": "",
    "rdcIdent": "",
    "requirementPrePlanVersion": "",
    "requirementStatus": "",
    "parentNodeRdc": "",
    "status": "正常",
    "rdcProblemNum": "3",
    "create_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "operator_person": "郭章建10329743",
    "effective_flag": "Y",
    "featureFirstType": "光层业务", 
    "featureSecondType": "灰光业务",
    "description": "description",
    "acceptanceCriteria": "acceptanceCriteria",
    "featureContentLink": "featureContentLink", 
}

# ---------- 2. 提取四个字段 ----------
def extract_board_global_status(src: Dict[str, str]) -> Dict[str, str]:
    return {
        "product": src.get("产品", ""),
        "boardType": src.get("板卡类型", ""),
        "boardBusinessModel": src.get("单板业务模型", ""),
        "board": src.get("board", "")
    }

def extract_board_product_by_global_status(src: Dict[str, str]) -> Dict[str, str]:
    return {
        "product": src.get("产品", ""),
        "boardType": src.get("板卡类型", "")
    }
# ---------- 3. 合并 ----------
def merge_to_global_status_list(
    board_factor: Dict[str, str],
    features: List[Dict[str, str]],
    employ_no
) -> List[Dict[str, str]]:
    """
    :param board_factor: 由 extract_board_global_status 得到的 4 字段字典
    :param features: 输入特性列表
    :return: 符合目标格式的 JSON 列表
    """
    results = []
    for idx, item in enumerate(features, 1):
        record = TEMPLATE.copy()
        record.update(board_factor)  # 写入 product / boardType / boardBusinessModel / board
        record["id"] = str(idx)
        record["featureFirstType"] = item.get("featureFirstType", "")
        record["featureSecondType"] = item.get("featureSecondType", "")
        record["feature"] = item.get("feature", "")
        record["subFeature"] = item.get("subFeature", "")
        record["description"] = item.get("description", "")
        record["acceptanceCriteria"] = item.get("acceptanceCriteria", "")
        record["featureContentLink"] = item.get("featureContentLink", "")
        record["belong_domain"] = item.get("belong_domain", "")
        record["belong_team"] = item.get("belong_team", "")
        record["operator_person"] = employ_no
        if item.get("feature") and not item.get("subFeature"):
            record["changeAnalysis"] = "普通变更: 新增" + item.get("feature", "").split('-', 1)[-1].strip() + ";\n关键变更: "
        results.append(record)
    return results

#================ 2 变更分析 ==============
# ---------- 获取 ----------
def get_factor_val_by_board_tree(board_name: str, factor_name: str) -> List[str]:
    """按英文逗号拆分子卡，去空去重"""
    factor_val = []
    seen = set()
    board_data = get_product_factor_by_board(board_name)

    for sc in board_data.get(factor_name, "").split(","):
        sc = sc.strip()
        if sc and sc not in seen:
            factor_val.append(sc)
            seen.add(sc)
    return factor_val

# ---------- 获取同的单板名称列表 ----------
def get_boards_with_same_factor_val(board_name: str, factor_name:str, factor_val: str) -> Set[str]:
    """返回拥有相同子卡的所有单板名称（别名），排除 except_alias"""

    boards: Set[str] = set()
    board_datas = get_board_by_factor(factor_name, factor_val)
    # 如果目标子卡在其中，且不是需排除的单板，则收集
    for item in board_datas:
        board = item.get("board")
        if board != board_name:
            boards.add(board)

    return boards

def get_boards_with_same_two_factor_val(board_name: str, factor_name:str, factor_val: str, factor_name2: str, factor_val2: str) -> Set[str]:
    """返回拥有相同子卡的所有单板名称（别名），排除 except_alias"""

    boards: Set[str] = set()
    board_datas = get_board_by_factor2(factor_name, factor_val, factor_name2, factor_val2)
    # 如果目标子卡在其中，且不是需排除的单板，则收集
    for item in board_datas:
        board = item.get("board")
        if board != board_name:
            boards.add(board)

    return boards

# ---------- 遍历同名单板的对应特性的子特性的RDC状态 ----------
def format_change_analysis(board_name: str, element:str, factor:str, feature_key: str) -> Optional[List[str]]:
    factor_vals = get_factor_val_by_board_tree(board_name, factor)
    if not factor_vals:
        return []

    results = []
    for factor_val in factor_vals:
        same_boards = get_boards_with_same_factor_val(board_name, factor, factor_val)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        if same_boards and isBoardWholeStatusRDCByParams(info):
            results.append(f"新增-{element}要素-{factor}因子-{factor_val}因子取值-非首次使用; ")
        else:
            results.append(f"新增-{element}要素-{factor}因子-{factor_val}因子取值-首次使用; ")

    return results

def format_change_analysis_add(board_name: str, factor: str, factor_vals: str, feature_key: str) -> Optional[List[str]]:
    if not factor_vals:
        return []

    results = []
    val_list = factor_vals.split(",")
    for factor_val in val_list:
        same_boards = get_boards_with_same_factor_val(board_name, factor, factor_val)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        if same_boards and isBoardWholeStatusRDCByParams(info):
            results.append(f"新增-单板部件要素-{factor}因子-{factor_val}因子取值-非首次使用, ")
        else:
            results.append(f"新增-单板部件要素-{factor}因子-{factor_val}因子取值-首次使用, ")

    return results
    
def get_cross_by_board_mod(val: str):
    svc_val = re.split(r'(?:_Eo|_)(?=[^_]+$)', val)[-1].upper()
    if svc_val == "S" or svc_val == "V":
        svc_val = "VC"
    return svc_val

def board_svc_mod_and_cross_frm_change(board_name: str, board_svc, cross_frm) -> Optional[List[str]]:
    results = []
    board_svc = board_svc.split(",")
    for svc_type in board_svc:
        svc_val = get_cross_by_board_mod(svc_type)
        feature_key = svc_val + "业务交叉管理"
        for cross_type in cross_frm:
            # 获取取值相同的单板数据
            same_boards = get_boards_with_same_two_factor_val(board_name, "单板业务模型", svc_type, "交换FRM芯片", cross_type)
            #logger.info(same_boards)
            info = {
                    "board": ",".join(sorted(same_boards)),
                    "feature": feature_key,
                    "requirementStatus": "可交付,已支持"
            }
            #logger.info(info)
            if same_boards and isBoardWholeStatusRDCByParams(info):
                results.append(f"新增-单板部件要素-交叉FRM芯片因子[{cross_type}]-{svc_type}-非首次使用, ")
            else:
                results.append(f"新增-单板部件要素-交叉FRM芯片因子[{cross_type}]-{svc_type}-首次使用, ")

    return results

def board_svc_mod_and_svc_frm_change(board_name: str, board_svc, svc_frm) -> Optional[List[str]]:
    results = []
    board_svc = board_svc.split(",")
    for svc_type in board_svc:
        svc_val = get_cross_by_board_mod(svc_type)
        feature_key = svc_val + "业务基础"
        for frm_type in svc_frm:
            # 获取取值相同的单板数据
            same_boards = get_boards_with_same_two_factor_val(board_name, "单板业务模型", svc_type, "业务FRM芯片", frm_type)
            #logger.info(same_boards)
            info = {
                    "board": ",".join(sorted(same_boards)),
                    "feature": feature_key,
                    "requirementStatus": "可交付,已支持"
            }
            #logger.info(info)
            if same_boards and isBoardWholeStatusRDCByParams(info):
                results.append(f"新增-单板部件要素-业务FRM芯片因子[{frm_type}]-{svc_type}-非首次使用, ")
            else:
                results.append(f"新增-单板部件要素-业务FRM芯片因子[{frm_type}]-{svc_type}-首次使用, ")

    return results
    
def ele_layer_svc_and_svc_frm_change(board_name: str, factor: str, ele_layer_svc, svc_frm) -> Optional[List[str]]:
    results = []
    for svc_type in ele_layer_svc:
        feature_key = "O业务基础"
        for frm_type in svc_frm:
            # 获取取值相同的单板数据
            same_boards = get_boards_with_same_two_factor_val(board_name, factor, svc_type, "业务FRM芯片", frm_type)
            #logger.info(same_boards)
            info = {
                    "board": ",".join(sorted(same_boards)),
                    "feature": feature_key,
                    "requirementStatus": "可交付,已支持"
            }
            #logger.info(info)
            if same_boards and isBoardWholeStatusRDCByParams(info):
                results.append(f"新增-单板部件要素-业务FRM芯片因子[{frm_type}]-{svc_type}{factor}-非首次使用, ")
            else:
                results.append(f"新增-单板部件要素-业务FRM芯片因子[{frm_type}]-{svc_type}{factor}-首次使用, ")

    return results

def board_svc_mod_and_frm_change(board_name: str, factor: str, element2: str, factor2: str) -> Optional[List[str]]:
    # 获取因子1的取值 单板业务模型
    factor_vals = get_factor_val_by_board_tree(board_name, factor)
    if not factor_vals:
        logger.info(f"board_name:{board_name}, factor:{factor} val is null")
        return []

    # 获取因子2的取值 业务FRM芯片
    factor_vals2 = get_factor_val_by_board_tree(board_name, factor2)
    if not factor_vals2:
        logger.info(f"board_name:{board_name}, factor:{factor2} val is null")
        return []

    results = []

    # 遍历因子1的取值
    for val in factor_vals:
        svc_val = get_cross_by_board_mod(val)
        if factor == "单板业务模型" and factor2 == "业务FRM芯片":
            feature_key = svc_val + "业务基础"
        elif factor2 == "交换FRM芯片":
            feature_key = svc_val + "业务交叉管理"
        else:
            feature_key = "O业务基础"
        # 遍历因子2的取值
        for val2 in factor_vals2:
            # 获取与因子1和因子2取值相同的单板数据
            same_boards = get_boards_with_same_two_factor_val(board_name, factor, val, factor2, val2)
            #logger.info(same_boards)
            info = {
                    "board": ",".join(sorted(same_boards)),
                    "feature": feature_key,
                    "requirementStatus": "可交付,已支持"
            }
            #logger.info(info)
            if same_boards and isBoardWholeStatusRDCByParams(info):
                results.append(f"新增-{element2}要素-{factor2}因子[{val2}]-{val}{factor}-非首次使用; ")
            else:
                results.append(f"新增-{element2}要素-{factor2}因子[{val2}]-{val}{factor}-首次使用; ")

    return results

def board_svc_mod_and_frm_change_add(board_name: str, factor: str, factor_vals, element2: str, factor2: str) -> Optional[List[str]]:
    if not factor_vals:
        logger.info(f"board_name:{board_name}, factor:{factor} val is null")
        return []

    val_list = factor_vals.split(",")
    # 获取因子2的取值 业务FRM芯片
    factor_vals2 = get_factor_val_by_board_tree(board_name, factor2)
    if not factor_vals2:
        logger.info(f"board_name:{board_name}, factor:{factor2} val is null")
        return []

    results = []
    # 遍历因子1的取值
    for val in val_list:
        svc_val = get_cross_by_board_mod(val)
        if factor == "单板业务模型" and factor2 == "业务FRM芯片":
            feature_key = svc_val + "业务基础"
        elif factor2 == "交换FRM芯片":
            feature_key = svc_val + "业务交叉管理"
        else:
            feature_key = "O业务基础"
        # 遍历因子2的取值
        for val2 in factor_vals2:
            # 获取与因子1和因子2取值相同的单板数据
            same_boards = get_boards_with_same_two_factor_val(board_name, factor, val, factor2, val2)
            #logger.info(same_boards)
            info = {
                    "board": ",".join(sorted(same_boards)),
                    "feature": feature_key,
                    "requirementStatus": "可交付,已支持"
            }
            #logger.info(info)
            if same_boards and isBoardWholeStatusRDCByParams(info):
                results.append(f"新增-{element2}要素-{factor2}因子[{val2}]-{val}{factor}-非首次使用; ")
            else:
                results.append(f"新增-{element2}要素-{factor2}因子[{val2}]-{val}{factor}-首次使用; ")

    return results

def oh_logic_write_global_st(board_name: str, features: str, boards: List[str], oh: str, key: str, employ_no: str) -> List[str]:
    """
    处理"高可用业务"特征
    返回: 本次产生的所有 analysis 字符串列表
    """
    results = []
    feature = get_feature_by_global_class(features, key)
    for item in feature:
        feature_key = item.get("feature")
        info = {
            "board": ",".join(sorted(boards)),
            "feature": feature_key,
            "requirementStatus": "可交付,已支持"
        }
        if boards and isBoardWholeStatusRDCByParams(info):
            analysis = f"新增-单板部件要素-开销逻辑因子-{oh}因子取值-非首次使用; "
            feature_key = "F060101-E-业务单板-基础启动"
            results.append(analysis)
            change_analysis_to_global_st(board_name, feature_key, analysis, employ_no)
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'
            change_development_type_to_global_st(board_name, feature_key, development_type, reuse_degree, employ_no)
            return results
        else:
            analysis = f"新增-单板部件要素-开销逻辑因子-{oh}因子取值-首次使用; "
            results.append(analysis)
            change_analysis_to_global_st(board_name, feature_key, analysis, employ_no)
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'
            change_development_type_to_global_st(board_name, feature_key, development_type, reuse_degree, employ_no)

    return results

def elec_svc_and_oh_change_to_global_st(board_name: str, board_features: str, employ_no) -> Optional[List[str]]:
    # 获取业务FRM芯片
    oh_types = get_factor_val_by_board_tree(board_name, "开销逻辑")
    if not oh_types:
        logger.info(f"board_name:{board_name}, 开销逻辑 val is null")
        return []

    results = []

    # 遍历业务FRM芯片的取值
    for oh in oh_types:
        # 获取与业务模型和业务FRM芯片取值相同的单板数据
        same_boards = get_boards_with_same_factor_val(board_name, "开销逻辑", oh)
        analysis = oh_logic_write_global_st(board_name, board_features, same_boards, oh, "高可用业务", employ_no)
        results.append(analysis)
        analysis = oh_logic_write_global_st(board_name, board_features, same_boards, oh, "扩展应用业务", employ_no)
        results.append(analysis)
    return results

def get_package_types_cfp(parts: str) -> str:
    """
    从形如 '新易盛_QSFP28(4*28)_物料代码1_PN1,SFP光模块,SFP+光模块' 的字符串中
    提取并返回 'QSFP28,SFP,SFP+'。
    """
    items = [s.strip() for s in parts.split(',') if s.strip()]
    result: List[str] = []

    for item in items:
        if '_' in item:
            # 切分：厂家 | 封装类型(通道信息) | 其它
            seg = item.split('_', 2)
            if len(seg) < 3:
                continue
            package_part = seg[1]              # 'QSFP28(4*28)'
            package = package_part.split('(')[0].strip()
            if package:
                result.append(package)
        else:
            # 直接提取光模块类型，如 SFP、SFP+
            match = re.match(r'^([A-Za-z0-9+-]+)', item.strip())
            if match:
                result.append(match.group(1))
    return ','.join(result).lower() # 返回排序后的结果，保持一致性

def normalize_and_deduplicate(strings: List[str]) -> List[str]:
    """
    将列表中的 'SFP+' 替换为 'SFP'，然后对列表进行去重处理。
    """
    # 替换 'SFP+' 为 'SFP' 并去重
    normalized_set = {s.replace("SFP+", "SFP") for s in strings}
    return list(normalized_set)

# 客户侧光层业务变更波及分析规则
def client_opt_svc_change_impact_analysis_rules(board_name: str, svc_types: str, feature_list, employ_no):
    svc_types = normalize_and_deduplicate(svc_types.split(","))
    features = get_sub_feature_by_feature(feature_list, "灰光业务基础")
    factor = "客户侧光层业务"
    results = []
    for svc_id in svc_types:
        cfp_type = svc_id.split('_')[0].lower()
        if "qsfpdd" in cfp_type:
            cfp_type = "qsfp-dd(8*56)"
        sub_feature = get_sub_feature_by_gray_opt_cfp(features, cfp_type)
        if len(sub_feature) > 0:
            feature_key = sub_feature[0]
        else:
            continue
        # 1 加校验去除客户侧非法业务和模块组合，以相同封装类型为准
        # 2 按照业务和光模块组合查找是否有可交付的单板
        # 3 RDC状态细化到 F010201-E-灰光业务基础 中的具体封装类型
        same_boards = get_boards_with_same_factor_val(board_name, factor, svc_id)
        info = {
                "board": ",".join(sorted(same_boards)),
                "subFeature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        if same_boards and isBoardWholeStatusRDCByParams(info):
            part = f"新增-单板业务要素-{factor}因子-{svc_id}因子取值-非首次使用, "
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'            
            results.append(part)
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)  
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            part = f"新增-单板业务要素-{factor}因子-{svc_id}因子取值-首次使用, "
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'            
            results.append(part)
            add_svc_features = [                 
                "F010201-E-灰光业务基础",
                "F010221-E-灰光业务维护管理",
                "F010222-E-灰光业务性能告警",
                "F060101-E-业务单板-基础启动"
                ]
            for i in add_svc_features:
                change_analysis_to_global_st(board_name, i, part, employ_no)
                change_development_type_to_global_st(board_name, i, development_type, reuse_degree, employ_no)
 
    return results

# 线路侧光层业务变更波及分析规则
def line_opt_svc_change_impact_analysis_rules(board_name: str, svc_types: str, feature_list, employ_no):
    svc_types = normalize_and_deduplicate(svc_types.split(","))
    feature_key = "F010101-E-彩光业务基础"
    factor = "线路侧光层业务"
    results = []
    for svc_id in svc_types:
        same_boards = get_boards_with_same_factor_val(board_name, factor, svc_id)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        if same_boards and isBoardWholeStatusRDCByParams(info):
            part = f"新增-单板业务要素-{factor}因子-{svc_id}因子取值-非首次使用, "
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'            
            results.append(part)
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            part = f"新增-单板业务要素-{factor}因子-{svc_id}因子取值-首次使用, "
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'            
            results.append(part)
            feature = "F010101-E-彩光业务基础"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)

    return results

# 客户侧光模块变更波及分析规则
def client_opt_change_impact_analysis_rules(board_name: str, factor: str, mod_types: str, feature_list, employ_no):
    mod_types = normalize_and_deduplicate(mod_types.split(","))
    features = get_sub_feature_by_feature(feature_list, "灰光业务基础")
    # factor = "客户侧光模块"
    results = []
    for mod_id in mod_types:
        cfp_type = get_package_types_cfp(mod_id) # 封装类型
        if "qsfpdd" in cfp_type:
            cfp_type = "qsfp-dd(8*56)"
        sub_feature = get_sub_feature_by_gray_opt_cfp(features, cfp_type)
        if len(sub_feature) > 0:
            feature_key = sub_feature[0]
        else:
            continue
        # 1 加校验去除客户侧非法业务和模块组合，以相同封装类型为准
        # 2 按照业务和光模块组合查找是否有可交付的单板
        # 3 RDC状态细化到 F010201-E-灰光业务基础 中的具体封装类型
        same_boards = get_boards_with_same_factor_val(board_name, factor, mod_id)
        info = {
                "board": ",".join(sorted(same_boards)),
                "subFeature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        if same_boards and isBoardWholeStatusRDCByParams(info):
            part = f"新增-单板部件件要素-{factor}因子-{mod_id}因子取值-非首次使用, "
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'            
        else:
            part = f"新增-单板部件件要素-{factor}因子-{mod_id}因子取值-首次使用, "
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'            

        results.append(part)
        # 光模块 首次非首次都波及
        client_features = [
            "F060101-E-业务单板-基础启动",
            "F050111-E-关键器件温度触发风扇调整",
            "F070171-E-业务单板-能耗管理-能耗感知和优化",
            "F080101-E-业务单板工装-基础启动",
            "F080102-E-业务单板工装-功能测试"
            ]
        for i in client_features:
            change_analysis_to_global_st(board_name, i, part, employ_no)
            change_development_type_to_global_st(board_name, i, development_type, reuse_degree, employ_no)

    return results

# 线路侧灰光模块变更波及分析规则
def line_gray_opt_change_impact_analysis_rules(board_name: str, mod_types: str, feature_list, employ_no):
    mod_types = normalize_and_deduplicate(mod_types.split(","))
    global_class = "彩光业务"
    feature_key = "F010101-E-彩光业务基础"
    factor = "线路侧光模块"
    results = []
    for mod_id in mod_types:
        if "CFP" in mod_id:
            feature_key = "F010201-E-灰光业务基础"
            global_class = "灰光业务"
        same_boards = get_boards_with_same_factor_val(board_name, factor, mod_id)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        # 光模块    波及
        # 首次      彩光业务所有特性
        # 非首次    F060101-E-业务单板-基础启动
        if same_boards and isBoardWholeStatusRDCByParams(info):
            part = f"新增-单板部件件要素-{factor}因子-{mod_id}因子取值-非首次使用, "
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'            
            results.append(part)
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)

        else:
            part = f"新增-单板部件件要素-{factor}因子-{mod_id}因子取值-首次使用, "
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'
            results.append(part)
            first_feature = get_feature_by_sencond_global_class(feature_list, global_class)
            for i in first_feature:
                change_analysis_to_global_st(board_name, i.get("feature",""), part, employ_no)
                change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)


        # 新增光模块首次非首次都要波及
        line_features = [                 
            "F050111-E-关键器件温度触发风扇调整",
            "F070171-E-业务单板-能耗管理-能耗感知和优化",
            "F080101-E-业务单板工装-基础启动",
            "F080102-E-业务单板工装-功能测试"
            ]
        for i in line_features:
            change_analysis_to_global_st(board_name, i, part, employ_no)
            change_development_type_to_global_st(board_name, i, development_type, reuse_degree, employ_no)

    return results

# 线路侧彩光模块变更波及分析规则
def line_color_opt_change_impact_analysis_rules(board_name: str, mod_types: str, feature_list, employ_no):
    feature_key = "F010101-E-彩光业务基础"
    factor = "线路侧光模块"
    results = []
    mod_types = mod_types.split(",")
    for mod_id in mod_types:
        color_feature = ""
        # 获取线路侧PN
        mod_pn = mod_id.split('_', 1)[0]
        # logger.info(f"====== mod_pn: {mod_pn} = mod_id {mod_id} =======")
        same_boards = get_boards_with_same_factor_val(board_name, factor, mod_pn)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        # 光模块    波及
        # 首次      彩光业务所有特性 "F070181-E-业务单板-巡检-线路侧光模块巡检",  
        # 非首次    F060101-E-业务单板-基础启动
        if same_boards and isBoardWholeStatusRDCByParams(info):
            part = f"新增-单板部件件要素-{factor}因子-{mod_pn}因子取值-非首次使用, "
            results.append(part)
            feature = "F060101-E-业务单板-基础启动"
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            part = f"新增-单板部件件要素-{factor}因子-{mod_pn}因子取值-首次使用, "
            results.append(part)
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'
            feature = "F070181-E-业务单板-巡检-线路侧光模块巡检"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
            color_feature = get_feature_by_sencond_global_class(feature_list, "彩光业务")
            for i in color_feature:
                change_analysis_to_global_st(board_name, i.get("feature", ""), part, employ_no)
                change_development_type_to_global_st(board_name, i.get("feature", ""), development_type, reuse_degree, employ_no)

        # 光模块首次非首次都要波及
        line_features = [
            "F050111-E-关键器件温度触发风扇调整",
            "F070171-E-业务单板-能耗管理-能耗感知和优化",
            "F080101-E-业务单板工装-基础启动",
            "F080102-E-业务单板工装-功能测试",
            "F070133-E-业务单板-时间性能-光模升级加载+中断时间要求"
        ]
        for i in line_features:
            change_analysis_to_global_st(board_name, i, part, employ_no)
            change_development_type_to_global_st(board_name, i, development_type, reuse_degree, employ_no)

    return results

def build_kv_map_csv(table: str) -> Dict[str, str]:
    """
    现在 table 是以逗号分隔的 key:value 对，形如
    "M2S6F:M2S6K,M1S3F:M1S3K,..."
    """
    kv: Dict[str, str] = {}
    for pair in table.split(','):
        pair = pair.strip()
        if ':' not in pair:
            continue
        k, v = pair.split(':', 1)
        kv[k] = v
        kv[v] = k
    return kv

# 处理子架合并问题
def process_shelf_type_string(raw: str) -> List[str]:
    table = "M2S6F:M2S6K,M1S3F:M1S3K,M1S3F-E:M1S3K-E,M2S3F-E(B):M2S3K-E(B),M2S3F-E(FB):M2S3K-E(FB),M2S3F-E(B|FB):M2S3K-E(B|FB),M1G2:M1G2K,M1G2-E:M1G2K-E,M1S3G:M1S3K(G)"
    kv = build_kv_map_csv(table)
    items = [s.strip() for s in raw.split(',')]
    seen = set()
    result: List[str] = []

    for it in items:
        if it in seen:
            continue
        other = kv.get(it)
        if other and other in items:
            pair = f"{it}|{other}" if it < other else f"{other}|{it}"
            result.append(pair)
            seen.add(other)
        else:
            result.append(it)
    return result

# ---------- 完成单板变更分析原表填写 ----------
def generate_change_analysis(board_tree, board_features, employ_no) -> Dict[str, Any]:
    """
    根据单板名称，从单板树-数据表获取数据，生成变更分析表
    """
    # 1. 从单板树中查找指定单板
    board_name = board_tree.get("board", "")
    # 2. 初始化变更分析结果字典
    change_analysis = {
        "board": board_tree.get("board", ""),
    }

    # 3. 处理简单的新增项（子架、端口数量、配置类型等）
    # 3.1 配置类型变更分析
    config_types = split_multiline(board_tree.get("单板配置类型", ""))
    change_analysis["配置类型变更分析"] = generate_simple_add_analysis(config_types)

    # 3.2 单板支持的子架变更分析
    subracks = process_shelf_type_string(board_tree.get("单板支持的子架", ""))
    change_analysis["单板支持的子架变更分析"] = generate_simple_add_analysis_shelf(subracks)

    # 3.3 物理端口数量变更分析
    ports = split_multiline(board_tree.get("物理端口数量", ""))
    change_analysis["物理端口数量变更分析"] = generate_simple_add_analysis_port(ports)

    # 获取RDC状态的特性
    feature_key = "业务单板-基础启动"
    # FS060101-04-业务单板-基础启动-单板BSP初始化
    analysis = format_change_analysis(board_name, "单板部件", "子卡", feature_key)
    change_analysis["子卡变更分析"] = '\n'.join(analysis)

    # FS060101-07-业务单板-基础启动-CDR芯片初始化
    analysis = format_change_analysis(board_name, "单板部件", "GEARBOX", feature_key)
    change_analysis["GEARBOX变更分析"] = '\n'.join(analysis)

    # FS060101-05-业务单板-基础启动-时钟芯片正常锁定
    analysis = format_change_analysis(board_name, "单板部件", "时钟芯片", feature_key)
    change_analysis["时钟芯片变更分析"] = '\n'.join(analysis)

    # FS060101-02-业务单板-基础启动-逻辑正常加载
    analysis = format_change_analysis(board_name, "单板部件", "控制逻辑", feature_key)
    change_analysis["控制逻辑变更分析"] = '\n'.join(analysis)

    # XX业务基础特性
    analysis = board_svc_mod_and_frm_change(board_name, "单板业务模型", "单板部件", "业务FRM芯片")
    change_analysis["单板业务模型_业务FRM芯片变更分析"] = '\n'.join(analysis)

    # XX业务交叉管理特性
    analysis = board_svc_mod_and_frm_change(board_name, "单板业务模型", "单板部件", "交换FRM芯片")
    change_analysis["单板业务模型_交换FRM芯片变更分析"] = '\n'.join(analysis)

    # O业务基础特性
    analysis = board_svc_mod_and_frm_change(board_name, "客户侧电层业务", "单板部件", "业务FRM芯片")
    analysis_line = board_svc_mod_and_frm_change(board_name, "线路侧电层业务", "单板部件", "业务FRM芯片")
    analysis.append('\n'.join(analysis_line))
    change_analysis["电层业务_业务FRM芯片变更分析"] = '\n'.join(analysis)

    # 需要分别波及的高可用和扩展分类下的所有特性，单独记录高可用和扩展每个特性是否首次，与特性波及时映射一一对应
    # "单板业务模型", "开销逻辑"
    analysis = elec_svc_and_oh_change_to_global_st(board_name, board_features, employ_no)

    # 1 先按照业务、光模块单独查找是否有可交付的单板，确定业务和光模块分别是否首次
    # 2 加校验去除客户侧非法业务和模块组合，以相同光层业务(封装类型)为准
    # 3 RDC状态细化到 F010201-E-灰光业务基础 中的具体封装类型
    c_mod_type = board_tree.get("客户侧光模块", "")
    analysis = client_opt_change_impact_analysis_rules(board_name, "客户侧光模块", c_mod_type, board_features, employ_no)
    change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)

    # 线路侧光层业务
    mod_type = board_tree.get("线路侧光模块", "")
    if mod_type:
        if is_gray_optical_mod(mod_type):
            logger.info(f"------灰光模块--- mod_type:{mod_type} -----")
            analysis = line_gray_opt_change_impact_analysis_rules(board_name, mod_type, board_features, employ_no)
        elif is_cfp_optical_mod(mod_type):
            analysis = client_opt_change_impact_analysis_rules(board_name, "线路侧光模块", mod_type, board_features, employ_no)
        else:
            logger.info(f"------彩光模块--------")
            # 1 先按照业务、光模块、(都是非首次需查找组合: 业务+光模块)三种情况单独查找是否有可交付的单板，确定业务和光模块分别是否首次，组合是否首次
            # 2 加校验去除线路侧非法业务和模块组合，以相同光层业务(XXX)为准--未确定
            # 3 业务RDC状态细化到 F010101-E-彩光业务基础 FS010101-02-B10G彩光业务-FEC纠错+FS010101-03-B10G彩光业务-调制码型
            analysis = line_color_opt_change_impact_analysis_rules(board_name, mod_type, board_features, employ_no)
    else:
        analysis = []
    change_analysis["线路侧光模块变更分析"] = '\n'.join(analysis)

    c_opt_svc = board_tree.get("客户侧光层业务", "")
    analysis = client_opt_svc_change_impact_analysis_rules(board_name, c_opt_svc, board_features, employ_no)
    change_analysis["客户侧光层业务变更分析"] = '\n'.join(analysis)

    l_opt_svc = board_tree.get("线路侧光层业务", "")
    analysis = line_opt_svc_change_impact_analysis_rules(board_name, l_opt_svc, board_features, employ_no)
    change_analysis["线路侧光层业务变更分析"] = '\n'.join(analysis)

    # # 创建变更分析表
    addSrcBoardChangeAnalysisData(change_analysis, markdown_flag=True)

    return change_analysis
#
# ---------- 变更分析写到全局状态表 ----------
def get_feature_by_global_st(data: List[Dict]) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (not item.get("subFeature")) and item.get("feature")
    ]

def get_feature_by_global_class(data: List[Dict], first_type: str) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (not item.get("subFeature")) and item.get("feature") and first_type == item.get("featureFirstType")
    ]

def get_feature_by_sencond_global_class(data: List[Dict], first_type: str) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (not item.get("subFeature")) and item.get("feature") and first_type == item.get("featureSecondType")
    ]

def get_other_feature_by_global_class(data: List[Dict], first_type: str) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (not item.get("subFeature")) and item.get("feature") and first_type != item.get("featureFirstType")
    ]

def get_same_feature_by_global_class(data: List[Dict], first_type: str, feature_key) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (not item.get("subFeature")) and (feature_key in item.get("feature")) and first_type == item.get("featureFirstType")
    ]

def get_sub_feature_by_gray_opt_cfp(data: List[Dict], cfp_type: str) -> List[str]:
    """
    返回 subFeature 包含 cfp_type 的所有记录的 subFeature 字段值。
    """
    return [
        item.get("subFeature", "")  # 获取 subFeature 的值，如果不存在则返回空字符串
        for item in data
        if cfp_type in item.get("subFeature", "")  # 检查 subFeature 是否包含 cfp_type
    ]

def get_sub_feature_by_feature(data: List[Dict], feature: str) -> List[Dict]:
    """
    返回 subFeature 为空字符串、None 或缺失，
    且 feature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("subFeature")) and feature in item.get("feature")
    ]

# 将变更分析内容填写到指定特性中
def find_board_global_st_by_feature(board_name: str, feature: str) -> Optional[Dict[str, Any]]:
    """公共查询：返回唯一一条符合(board, feature, parent=2)的记录，找不到返回 None"""
    query_params = {
        "board": board_name,
        "parent": "2",          # 特性存在，子特性 & RDC 不存在
        "feature": feature
    }
    records = querySrcBoardWholeStatusByParams(query_params, markdown_flag=True)
    if not records:
        logger.info("未找到变更分析对应的特性")
        return None
    return records[0]

def get_change_analysis_by_global_st(board_name: str, feature: str) -> str:
    """只读接口：返回已有 changeAnalysis 内容（空串表示无）"""
    record = find_board_global_st_by_feature(board_name, feature)
    return record.get("changeAnalysis", "") if record else ""

def get_development_type_by_global_st(board_name: str, feature: str, sub_feature: str) -> str:
    development_type = "验证性需求"
    reuse_degree = "零代码"
    zero_list = [
        "FS020102-51-E-告警屏蔽",
        "FS020102-52-E-性能门限",
        "FS020102-53-E-性能屏蔽",
        "FS020102-54-E-性能清零计数器",
        "FS020102-55-E-性能基准值",
        "FS020102-56-E-零性能抑制",
        "FS020102-57-E-性能实时测量",
        "FS020102-58-E-告警预投入",
        "FS020102-59-E-端口使能",
        "FS020102-60-E-告警防抖",
        "FS020102-61-E-告警反转",
        "FS030141-01-E-apsd-oac1+1单向保护",
        "FS030141-02-E-apsd-oac1+1双向保护",
        "FS030142-01-E-非apsd-oac1+1单向保护",
        "FS030142-02-E-非apsd-oac1+1双向保护",
        "FS030143-01-E-och1+1单向保护",
        "FS030143-02-E-och1+1双向保护",
        "FS030143-11-E-och1+1 SOP入口光功率触发倒换",
        "FS030144-01-E-cdc-och1+1单向保护",
        "FS030144-02-E-cdc-och1+1双向保护",
        "FS040109-05-E-DM-O业务-双向端到端查询时延结果要求两位小数精度",
        "FS040409-03-E-DM-P业务终结OSU业务双向端到端查询时延结果要求两位小数精度",
        "FS040410-03-E-DM-P业务终结OSU业务单向端到端查询时延结果要求两位小数精度",
        "FS040411-03-E-DM-P业务终结FG业务双向端到端查询时延结果要求两位小数精度",
        "FS040413-03-E-DM-P业务终结ODU业务双向端到端查询时延结果要求两位小数精度",
        "FS040414-03-E-DM-P业务终结ODU业务单向端到端查询时延结果要求两位小数精度",
        "FS070121-01-E-业务单板-平滑升级-M值替换平滑升级",
        "FS070122-01-E-业务单板-业务性能-交叉板冗余保护及平滑升级-业务无损",
        "FS070122-02-E-业务单板-业务性能-主控板主备倒换-业务无损",
        "FS070131-01-E-业务单板-时间性能-版本升级操作加载时间要求",
        "FS070132-01-E-业务单板-时间性能-启动时间要求",
        "FS070133-01-E-业务单板-时间性能-光模升级加载+中断时间要求",
        "FS070151-01-E-业务单板-定位定界-单板内存/CPU越限告警",
        "FS070153-01-E-业务单板-定位定界-安全通道故障诊断",
        "FS070154-01-E-业务单板-定位定界-线卡标准日志",
        "FS070155-01-E-业务单板-定位定界-日志转储",
        "FS070156-01-E-业务单板-定位定界-单板报文记录(U口/S口/CTI报文等)"
    ]
    
    # 遍历并分类每个需求项
    if any(item in sub_feature for item in zero_list):
        development_type = "验证性需求"
        reuse_degree = "零代码"
        return development_type, reuse_degree

    """只读接口：返回已有 changeAnalysis 内容（空串表示无）"""
    record = find_board_global_st_by_feature(board_name, feature)
    if record:
        development_type = record.get("developmentType", "")
        reuse_degree = record.get("reuseDegree", "")
    if development_type is None:
        development_type = "新增单板-新增功能需求"
        reuse_degree = "全代码"  
        
    return development_type, reuse_degree

# 从特性&子特性获取RDC信息
def get_feature_content_link_by_features(features: List[Dict[str, str]], subfeature: str) -> str:
    for item in features:
        if subfeature in item.get("subFeature",""):
            return item.get("featureContentLink")
    return ""

# 从特性&子特性获取RDC信息
def get_rdc_description_by_features(features: List[Dict[str, str]], sub_feature: str) -> dict:
    for item in features:
        if sub_feature in item.get("subFeature"):
            return item
    return {}

def change_analysis_to_global_st(
        board_name: str,
        feature: str,
        analysis: str,
        employ_no: str
) -> Optional[Dict[str, Any]]:
    """写入接口：无重复则追加 changeAnalysis 并回写"""
    if not analysis:                       # 空内容直接跳过
        return None

    record = find_board_global_st_by_feature(board_name, feature)
    if not record:                         # 查不到记录
        return None

    existing = record.get("changeAnalysis") or ""
    if analysis in existing:               # 已存在，无需写入
        return record

    # 追加并更新
    record["changeAnalysis"] = existing + ("\n" if existing else "") + analysis
    updateSrcBoardWholeStatusData([record], employ_no)
    return record

def change_development_type_to_global_st(
        board_name: str,
        feature: str,
        development_type: str,
        reuse_degree: str,
        employ_no: str
) -> Optional[Dict[str, Any]]:
    """写入接口：无重复则追加 changeAnalysis 并回写"""
    if not development_type and not reuse_degree:                       # 空内容直接跳过
        return None

    record = find_board_global_st_by_feature(board_name, feature)
    if not record:                         # 查不到记录
        return None

    # existing = record.get("DevelopmentType") or ""
    # if development_type in existing:               # 已存在，无需写入
    #     return record
    # 追加并更新
    record["developmentType"] = development_type
    record["reuseDegree"] = reuse_degree

    updateSrcBoardWholeStatusData([record], employ_no)

    return record

# 5 添加变更分析
def board_format_change_analysis(board_tree, board_features, employ_no):
    board_name = board_tree.get("board")

    # 创建单板变更分析原表
    change_analysis = generate_change_analysis(board_tree, board_features, employ_no)
    development_type = '新增单板-无新增器件及功能需求'
    reuse_degree = '配置化'
    # 波及分析
    # F060101-E-业务单板-基础启动 和 F060102-业务单板-基础管理特性
    cfg_analysis = change_analysis["配置类型变更分析"]
    features = [
        "F060101-E-业务单板-基础启动",
        "F060102-E-业务单板-基础管理"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, cfg_analysis, employ_no)
        change_development_type_to_global_st(board_name, item, development_type, reuse_degree, employ_no)

    # F020601-背板带宽动态调整特性 和 F020602-背板性能告警特性 和 F020611-新增子架特性
    shelf_analysis = change_analysis["单板支持的子架变更分析"]
    features = [
        "F020601-E-背板带宽动态调整",
        "F020602-E-背板性能告警", 
        "F020611-E-新增子架"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, shelf_analysis, employ_no)
        change_development_type_to_global_st(board_name, item, development_type, reuse_degree, employ_no)

    # F060101-E-业务单板-基础启动 和 F060102-业务单板-基础管理特性
    count_analysis = change_analysis["物理端口数量变更分析"]
    features = [
        "F060101-E-业务单板-基础启动",
        "F060102-E-业务单板-基础管理"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, count_analysis, employ_no)
        change_development_type_to_global_st(board_name, item, development_type, reuse_degree, employ_no)
        
    # F060101-E-业务单板-基础启动
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, change_analysis["子卡变更分析"], employ_no)
    change_analysis_to_global_st(board_name, feature, change_analysis["控制逻辑变更分析"], employ_no)

    # F060101-E-业务单板-基础启动 和 F020101-XX业务基础特性 XX:O/FG..
    gearbox_analysis = change_analysis["GEARBOX变更分析"]
    if "非首次" in gearbox_analysis:
        development_type = '新增单板-无新增器件及功能需求'
        reuse_degree = '配置化'
    else:
        development_type = '新增单板-新增器件需求'
        reuse_degree = '全代码'         
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, gearbox_analysis, employ_no)
    ele_feature = get_same_feature_by_global_class(board_features, "电层业务", "业务基础")
    for i in ele_feature:
        change_analysis_to_global_st(board_name, i.get("feature",""), gearbox_analysis, employ_no)
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)
        
    # F060101-E-业务单板-基础启动 和 F020101-XX业务基础特性 XX:O/FG..
    timer_analysis = change_analysis["时钟芯片变更分析"]
    if "非首次" in gearbox_analysis:
        development_type = '新增单板-无新增器件及功能需求'
        reuse_degree = '配置化'
    else:
        development_type = '新增单板-新增器件需求'
        reuse_degree = '全代码'         
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, timer_analysis, employ_no)
    for i in ele_feature:
        change_analysis_to_global_st(board_name, i.get("feature",""), timer_analysis, employ_no)
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)
        
    # 非首次: F060101-E-业务单板-基础启动 和 首次:F020106-XX业务交叉管理特性 XX:O/FG..
    s = change_analysis["单板业务模型_交换FRM芯片变更分析"]
    ele_feature = get_same_feature_by_global_class(board_features, "电层业务", "业务交叉管理")
    for part in s.split("\n"):
        if "非首次使用" in part:
            feature = "F060101-E-业务单板-基础启动"
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'            
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码'   
            for i in ele_feature:
                change_analysis_to_global_st(board_name, i.get("feature",""), part, employ_no)
                change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)

    # 首次除光层业务、F020602-背板性能告警特性、F020611-新增子架特性外其他所有特性 和 非首次F060101-E-业务单板-基础启动
    other_features = get_other_feature_by_global_class(board_features, "光层业务")
    blacklist = (
        "F050111-E-关键器件温度触发风扇调整",
        "F070133-E-业务单板-时间性能-光模升级加载+中断时间要求",
        "F070131-E-业务单板-时间性能-版本升级操作加载时间要求",
        "F070132-E-业务单板-时间性能-启动时间要求",
        "F050131-E-ODUk硬件异常保护",
        "F050132-E-单板硬件及接口类性能告警",
        "F070151-E-业务单板-定位定界-单板内存/CPU越限告警",
        "F070152-E-业务单板-定位定界-线卡复位原因记录",
        "F070153-E-业务单板-定位定界-安全通道故障诊断",
        "F070154-E-业务单板-定位定界-线卡标准日志",
        "F070155-E-业务单板-定位定界-日志转储",
        "F070156-E-业务单板-定位定界-单板报文记录(U口/S口/CTI报文等)",
        "F070157-E-业务单板-定位定界-Error_Info上报/Error_dump/Tid信令跟踪",
        "F070158-E-业务单板-定位定界-一键收割",
        "F070171-E-业务单板-能耗管理-能耗感知和优化",
        "F070181-E-业务单板-巡检-线路侧光模块巡检",
        "F080101-E-业务单板工装-基础启动",
        "F080102-E-业务单板工装-功能测试"
    )
    # 过滤掉blacklist中的特性子特性
    other_feature = filter_by_features(other_features, blacklist)
    s = change_analysis["电层业务_业务FRM芯片变更分析"]
    for part in s.split("\n"):
        if "非首次使用" in part:
            feature = "F060101-E-业务单板-基础启动"
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码' 
            for i in other_feature:
                if "F020602-E-背板性能告警" != i.get("feature") and "F020611-E-新增子架" != i.get("feature"):
                    change_analysis_to_global_st(board_name, i.get("feature",""), part, employ_no)
                    change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)


    #首次除光层业务外其他所有特性 和 非首次F060101-E-业务单板-基础启动
    s = change_analysis["单板业务模型_业务FRM芯片变更分析"]
    for part in s.split("\n"):
        if "非首次使用" in part:
            development_type = '新增单板-无新增器件及功能需求'
            reuse_degree = '配置化'
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
            change_development_type_to_global_st(board_name, feature, development_type, reuse_degree, employ_no)
        else:
            development_type = '新增单板-新增器件需求'
            reuse_degree = '全代码' 
            for i in other_feature:
                change_analysis_to_global_st(board_name, i.get("feature",""), part, employ_no)
                change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)

    return change_analysis

#================ 3 RDC拆分 ==============
RDC_TABLE = {
  "rdc_space": "OTNSW",
  "rdc_title": "测试RDC接口需要",
  "description": "456",
  "acceptance_criteria": "123",
  "workItem_type": "PR",
  "employ_no": "10164361"
}

def get_sub_feature_by_global_st(data: List[Dict]) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("feature")) and item.get("subFeature")
    ]

def get_opt_sub_feature_by_global_st(data: List[Dict], second_class:str) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if ("光层业务" in item.get("featureFirstType")) and 
           ("F010201-E-灰光业务基础" not in item.get("feature")) and 
           ("F010101-E-彩光业务基础" not in item.get("feature")) and item.get("subFeature") and 
           (second_class in item.get("featureSecondType"))
    ]

def get_sub_feature_by_global_st_color(feature: str, data: List[Dict]) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (feature in item.get("feature")) and item.get("subFeature")
    ]

def get_ele_sub_feature_by_global_st(data: List[Dict]) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("feature")) and item.get("subFeature") and (
            (item.get("featureFirstType") == "电层业务" and item.get("featureSecondType") != "BP业务")
            or item.get("featureFirstType") == "扩展应用业务"
            or item.get("featureFirstType") == "高可用业务"
        )
    ]

def get_bp_sub_feature_by_global_st(data: List[Dict]) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("feature")) and item.get("subFeature") and (
            (item.get("featureFirstType") == "电层业务" and item.get("featureSecondType") == "BP业务")
        )
    ]

def get_feature_by_global_st_class(data: List[Dict], first) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("feature")) and item.get("subFeature") and (item.get("featureFirstType") == first)
    ]

def filter_feature_by_global_st_class(data: List[Dict], first) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if (item.get("feature")) and item.get("subFeature") and (item.get("featureFirstType") != first)
    ]

def get_feature_by_global_st_first(data: List[Dict], first, second) -> List[Dict]:
    """
    返回 feature 非空空字符串、None 或缺失，
    且 subFeature 非空（存在且不为空字符串）的所有记录。
    """
    return [
        item for item in data
        if ((item.get("feature")) and item.get("subFeature") and item.get("featureFirstType") == first and item.get("featureSecondType") == second)
    ]

def rdc_product_name_convert(product_name) -> str:
    name_map = {
        '19700':'ZXONE ',
        'M721':'ZXMP ',
        '9700':'ZXONE ',
        '7000':'ZXONE '
    }
    k = product_name[:-2] if product_name.endswith('产品') else product_name
    return name_map.get(k,'') + k

def rdc_req_category_convert(feature):
    """
    如果入参字典中 feature 字段的值在 ha_list 里，则打印"高可用需求"。
    """
    serviceability_req = [
        'F070101-E-业务单板-无损升级-单板软件程序升级-业务无损',
        'F070102-E-业务单板-无损升级-开销逻辑升级-业务无损',
        'F070121-E-业务单板-平滑升级-M值替换平滑升级',
        'F070131-E-业务单板-时间性能-版本升级操作加载时间要求',
        'F070132-E-业务单板-时间性能-启动时间要求',
        'F070133-E-业务单板-时间性能-光模块升级加载+中断时间要求',
        'F070141-E-业务单板-防呆-备件替换防呆(Flash、5347、逻辑等器件)',
        'F070151-E-业务单板-定位定界-单板内存/CPU越限告警',
        'F070152-E-业务单板-定位定界-线卡复位原因记录',
        'F070153-E-业务单板-定位定界-安全通道故障诊断',
        'F070154-E-业务单板-定位定界-线卡标准日志',
        'F070155-E-业务单板-定位定界-日志转储',
        'F070156-E-业务单板-定位定界-单板报文记录(U口/S口/CTI报文等)',
        'F070157-E-业务单板-定位定界-Error_Info上报/Error_dump/Tid信令跟踪',
        'F070158-E-业务单板-定位定界-一键收割',
        'F070171-E-业务单板-能耗管理-能耗感知和优化',
        'F070181-E-业务单板-巡检-线路侧光模块巡检'
    ]
    
    high_availability_req = [
        'F010130-E-彩光业务光模块能力上报',
        'F050101-E-流控防护自愈',
        'F050102-E-交换系统优雅上下线',
        'F050121-E-数据一致性-下行对账(CLI)-对账结果上报-数据不一致告警及原因上报',
        'F050122-E-数据一致性-下行自动纠正(CLI)',
        'F050123-E-数据一致性-上行对账(CLI)，支持底层配置查询',
        'F050124-E-数据一致性-清库下库强制同步(网管)',
        'F050125-E-数据一致性-单业务全量强制同步(WASON)',
        'F040118-E-O业务扩展GCC电监控',
        'F050131-E-ODUk硬件异常保护',
        'F050132-E-单板硬件及接口类性能告警'
    ]

    workwear_req = [
        'F080101-E-业务单板工装-基础启动',
        'F080102-E-业务单板工装-功能测试'
    ]

    if feature in serviceability_req:
        return '04-可服务性需求'
    elif feature in workwear_req:
        return '99-工装需求'
    else:
        return '01-基本需求'

def rdc_info_to_global_map(board_name, rdc_info, subfeature, employ_no):
    query_params = {
        "board": board_name,
        "subFeature": subfeature
    }
    subFeature = querySrcBoardWholeStatusByParams(query_params, markdown_flag= True)
    if len(subFeature) > 0 :
        subFeature = subFeature[0]
    else:
        logger.info("未找到单板数据")
        return []
    # logger.info(f"===========lsa --- subFeature: {subFeature}=========")
    rdc_ret_val = []
    for item in rdc_info:
        #logger.info(item)
        record = copy.deepcopy(subFeature)
        #logger.info(f"------record:{record}-----------")
        record["rdcTitle"] = item.get("rdcTitle", "")
        record["rdcIdent"] = item.get("rdcIdent", "")
        record["requirementPrePlanVersion"] = item.get("requirementPrePlanVersion", "")
        record["requirementStatus"] = item.get("requirementStatus", "")
        record["parentNodeRdc"] = item.get("parentNodeRdc", "")
        record["rdcProblemNum"] = item.get("rdcProblemNum", "")
        rdc_ret_val.append(record)
    #logger.info(f"===========lsa --- rdc_ret_val: {rdc_ret_val}=========")
    addSrcBoardWholeStatusData(rdc_ret_val, employ_no)
    return rdc_ret_val

# 根据子特性创建多条RDC数据
pr_rdc_info_table = []

def clear_pr_rdc_info_table():
    """清空全局变量 pr_table"""
    global pr_rdc_info_table
    pr_rdc_info_table.clear()

def rdc_info_to_subfeature(board_name, features_list, rdc_name, item, body_params, opt_svc_analysis:str=""):
    requirementPrePlanning = body_params.get('requirementPrePlanning', '')
    specificationByExampleUrl = body_params.get('specificationByExampleUrl', '')
    employ_no = body_params.get('employ_no', '')
    priority_shelf = body_params.get('subrack', '')
    if priority_shelf:
        priority_shelf = '-[' + priority_shelf + ']'

    results = []
    if len(rdc_name) < 1:
        return []
    logger.info(f"---rdc_name:{rdc_name}\n")
    for handler in logger.handlers:
        handler.flush()
    description = "描述"
    criteria = "验收准则"
    belong_domain = "02-L1"
    belongProduct = "ZXONE 19700"
    requirementCategory = "01-基本需求"
    verificationTeam = "系统测试"
    partName = "BOARD"
    feature = item.get("feature")
    subfeature = item.get("subFeature")
    #board_design_url = query_board_tree_board_design_url_by_board_name(board_name)
    board_design_url = body_params.get('designSpecificationUrl', '')

    change_analysis = get_change_analysis_by_global_st(board_name, feature)
    analysis = ""
    if change_analysis:
        analysis = str(change_analysis).replace(':', ':<br>').replace(';', ';<br>')
    if opt_svc_analysis:
        analysis = analysis + "<br>" + opt_svc_analysis
    feature_link = get_feature_content_link_by_features(features_list, subfeature)
    rdc_info = get_rdc_description_by_features(features_list, subfeature)
    requirementType = body_params.get('requirementType', '')
    belongTeam = body_params.get('belongTeam', '')
    belong_team = ""
    if "平台团队" in requirementType:
        belong_team = "L1-平台团队"
    rdc_ret_val = []
    if isinstance(rdc_info, dict) and rdc_info:
        description = rdc_info.get("description","")
        # 添加空值检查
        if description is not None:
            # 在特定字段前添加换行符
            fields_to_add_br = ["功能描述：", "修改点/验证点：", "单板/组件：", "方案：", "特殊要求："]
            
            for field in fields_to_add_br:
                if field in description:
                    # 在字段前添加换行符
                    description = description.replace(field, f"<br>{field}")        

        criteria = rdc_info.get("acceptanceCriteria","")
        belong_domain = rdc_info.get("belong_domain","02-L1") 
        belongProduct = rdc_product_name_convert(rdc_info.get("product",""))
        requirementCategory = rdc_req_category_convert(feature)
        verificationTeam = ("中试" if requirementCategory == "99-工装需求" else "系统测试")
        partName = rdc_info.get("board")
        if not belong_team:
            rdc_belongTeam = rdc_info.get("belong_team", "")
            if len(rdc_belongTeam.split(',')) == 2:
                belong_team = "L1-保护团队"
            elif len(rdc_belongTeam.split(',')) > 2:
                belong_team = belongTeam
            else:
                belong_team = rdc_belongTeam
        # logger.info(f"-------belong_team:{belong_team}")
        for handler in logger.handlers:
            handler.flush()
        development_type, reuse_degree= get_development_type_by_global_st(board_name, feature, subfeature)
        for idx in rdc_name:
            record = RDC_TABLE.copy()
            record["rdc_title"] = str(idx + priority_shelf + "-L1")
            record["employ_no"] = str(employ_no)
            record["description"] = description
            record["acceptance_criteria"] = criteria
            record["featureContentLink"] = feature_link
            #新增字段
            record["belong_domain"] = "02-L1"
            record["belongProduct"] = belongProduct
            record["requirementPrePlanning"] = str(requirementPrePlanning)
            record["specificationByExampleUrl"] = str(specificationByExampleUrl)
            record["designSpecificationUrl"] = board_design_url
            record["requirementPurpose"] = "01-商用"
            record["priority"] = "5"
            record["requirementCategory"] = requirementCategory
            record["belongFeatureCatalog"] = "01-标准"
            record["requirementType"] = "01-功能需求"
            record["verificationMode"] = "测试"
            record["verificationTeam"] = verificationTeam
            record["changeAnalysis"] = analysis
            record["partName"] = partName
            record["belongTeam"] = belong_team
            record["DevelopmentType"] = development_type
            record["ReuseDegree"] = reuse_degree
            results.append(record)
        # logger.info(f"----------results:{results}\n")
        rdc_info, permission_flag = create_RDC(results, body_params.get("task_id"))
        if not permission_flag:
            return rdc_ret_val
        time.sleep(request_interval)
        global pr_rdc_info_table
        for rdc_item in rdc_info:
            pr_rdc_info_table.append({
                'rdcIdent': rdc_item.get("rdcIdent", ""),
                'rdcTitle': rdc_item.get("rdcTitle", ""),
                'analysis': analysis
            })

        rdc_ret_val = rdc_info_to_global_map(board_name, rdc_info, subfeature, employ_no)
        # logger.info("--------rdc_info_to_global_map执行完成")
        for handler in logger.handlers:
            handler.flush()
    else:
        logger.error(f"------子特性：{subfeature} 在features_list中未被找到")
        for handler in logger.handlers:
            handler.flush()
    return rdc_ret_val

def prefix_other_domain_list(prefix: str, items: List[str]) -> List[str]:
    """
    把 prefix 作为列表每一项的前缀，返回新列表
    """
    return [f"{prefix}{item}" for item in items]

def convert_depend_domain_string(product_name, depend_domain):
    """
    根据产品名称转换字符串中的地点信息
    
    参数:
        product_name: 产品名称，如 "M721"
        input_string: 需要转换的字符串
    
    返回:
        转换后的字符串
    """
    # 仅对 M721 产品进行转换
    if "M721" in product_name:
        # 将 06-硬件北京 替换为 07-硬件武汉
        result = re.sub(r'06-硬件北京', '07-硬件武汉', depend_domain)
        # 将 06-逻辑北京 替换为 07-逻辑武汉
        result = re.sub(r'06-逻辑北京', '07-逻辑武汉', result)
        return result
    else:
        # 其他产品不修改
        return depend_domain
    
def rdc_info_to_other_domain(board_name, rdc_name, mr_info, body_params, head_employ_no):
    requirementPrePlanning = body_params.get('requirementPrePlanning', '')
    specificationByExampleUrl = body_params.get('specificationByExampleUrl', '')
    employ_no = body_params.get('employ_no', '')
    results = []
    if len(rdc_name) < 1:
        return []
    depend_domain = pr_rdc_split_other_fields(mr_info.get('depend_belong_domain',''))
    if len(depend_domain) < 1:
        return []

    description = "描述"
    criteria = "验收准则"
    belong_domain = "02-L1"
    belongProduct = "ZXONE 19700"
    requirementCategory = "01-基本需求"
    verificationTeam = "系统测试"
    #partName = "BOARD"

    description = mr_info.get("description", "")
    if description:
        # 在特定字段前添加换行符
        # fields_to_add_br = ["需求描述：", "功能描述：", "F0", "所属产品：", "<", "涉及领域：", "#板卡/模块：", "#质量属性："]
        fields_to_add_br = [ "一、需求背景&目标", "用户名：", "背景：", "目的：", "商用/测试：", "交付时间：", 
         "二、需求描述", "本需求涵盖", "F0", 
		 "三、波及产品", "产品：", "子架&主控：", "波及领域：", "板卡：", "光模块：", 
		 "四、质量属性", "性能：", "可靠性：", "可维护性：", "兼容性：", "可移植性：", "可扩展性：", "易用性：", "维测（定界定位）："]

        for field in fields_to_add_br:
            if field in description:
                # 在字段前添加换行符
                description = description.replace(field, f"<br>{field}")  

    accept_criteria = mr_info.get("acceptanceCriteria", "")
    # 添加空值检查
    if accept_criteria:
        # 在特定字段前添加换行符
        fields_to_add_br = ["GIVEN:", "WHEN:", "F0", "THEN:"]
        for field in fields_to_add_br:
            if field in accept_criteria:
                # 在字段前添加换行符
                accept_criteria = accept_criteria.replace(field, f"<br>{field}")   

    #board_design_url = query_board_tree_board_design_url_by_board_name(board_name)
    board_design_url = body_params.get('designSpecificationUrl', '')
    belongProduct = rdc_product_name_convert(mr_info.get("belongProduct", ""))
    for idx in depend_domain:
        idx = convert_depend_domain_string(belongProduct, idx)
        record = RDC_TABLE.copy()
        record["rdc_title"] = str(rdc_name + '-'+idx.split("-", 1)[1] )
        record["employ_no"] = str(head_employ_no)
        record["description"] = description
        record["acceptance_criteria"] = accept_criteria
        record["featureContentLink"] = ""
        #新增字段
        record["belong_domain"] = str(idx) 
        record["belongProduct"] = belongProduct
        record["requirementPrePlanning"] = str(requirementPrePlanning)
        record["specificationByExampleUrl"] = str(specificationByExampleUrl)
        record["designSpecificationUrl"] = board_design_url
        record["requirementPurpose"] = "01-商用"
        record["priority"] = "5"
        record["requirementCategory"] = requirementCategory
        record["belongFeatureCatalog"] = "03-非标"
        record["requirementType"] = "01-功能需求"
        record["verificationMode"] = "测试"
        record["verificationTeam"] = verificationTeam
        record["changeAnalysis"] = "analysis"
        record["partName"] = str(board_name)
        rdc_title = record["rdc_title"]
        if "管控" in rdc_title and "新增" in rdc_title and "光模块" in rdc_title:
            record["rdc_title"] = rdc_title + '单点'
            results.append(record)
            record["rdc_title"] = rdc_title + '端到端'
            results.append(record)
        else:
            results.append(record)           
        logger.info(f"--other rdc_name:{record['rdc_title']}\n")
    # logger.info(f"----------results:{results}\n")
    rdc_info, permission_flag = create_RDC(results, body_params.get("task_id"))
    if not permission_flag:
        for handler in logger.handlers:
            handler.flush()
        return rdc_info
    time.sleep(request_interval)
    # logger.info("--------rdc_info_to_global_map执行完成")
    for handler in logger.handlers:
        handler.flush()
    return rdc_info

def mr_rdc_info_to_subfeature(board_name, rdc_name, mr_info, analysis, body_params):
    employ_no = body_params.get('employ_no', '')
    requirementPrePlanning = body_params.get('requirementPrePlanning', '')
    specificationByExampleUrl = body_params.get('specificationByExampleUrl', '')
    requirementSource = body_params.get('requirementSource', '')
    expectedFinishDate = body_params.get('expectedFinishDate', "")
    if expectedFinishDate:
        expectedFinishDate = f"{expectedFinishDate}T00:00:00.000+08:00"
    else:
        expectedFinishDate = "2030-12-31T00:00:00.000+08:00"
    requirementPurpose = body_params.get('requirementPurpose', '')
    customer = body_params.get('customer', "")
    targetMarket = body_params.get('targetMarket', '')
    marketTarget = body_params.get('marketTarget', '')
    results = []

    description = mr_info.get("description", "")
    # 添加空值检查
    if description:
        # 在特定字段前添加换行符
        # fields_to_add_br = ["需求描述：", "功能描述：", "F0", "所属产品：", "<", "涉及领域：", "#板卡/模块：", "#质量属性："]
        fields_to_add_br = [ "一、需求背景&目标", "用户名：", "背景：", "目的：", "商用/测试：", "交付时间：", 
         "二、需求描述", "本需求涵盖", "F0", 
		 "三、波及产品", "产品：", "子架&主控：", "波及领域：", "板卡：", "光模块：", 
		 "四、质量属性", "性能：", "可靠性：", "可维护性：", "兼容性：", "可移植性：", "可扩展性：", "易用性：", "维测（定界定位）："]
        for field in fields_to_add_br:
            if field in description:
                # 在字段前添加换行符
                description = description.replace(field, f"<br>{field}")  

    accept_criteria = mr_info.get("acceptanceCriteria", "")
    # 添加空值检查
    if accept_criteria:
        # 在特定字段前添加换行符
        fields_to_add_br = ["GIVEN:", "WHEN:", "F0", "THEN:"]
        for field in fields_to_add_br:
            if field in accept_criteria:
                # 在字段前添加换行符
                accept_criteria = accept_criteria.replace(field, f"<br>{field}") 

    #board_design_url = query_board_tree_board_design_url_by_board_name(board_name)
    board_design_url = body_params.get('designSpecificationUrl', '')

    src_depend_belong_domain = mr_info.get("depend_belong_domain","")
   
    depend_belong_domain = [
        {"name": item.strip(), "value": item.strip()}
        for item in src_depend_belong_domain.split(",")
        if item.strip()
    ]
    global mr_rdc_info_table_all
    for item in mr_rdc_info_table_all:
        if item.get('rdcTitle',"") == rdc_name:
            return [item]

    logger.info(f"----------mr rdc_name:{rdc_name} depend_belong_domain: {depend_belong_domain}\n")
    record = RDC_TABLE.copy()
    record["workItem_type"] = "MR"
    record["employ_no"] = str(employ_no)
    record["rdc_title"] = rdc_name
    record["description"] = description
    record["acceptance_criteria"] = accept_criteria
    record["belong_domain"] = mr_info.get("belong_domain","")
    record["depend_domain"] = depend_belong_domain
    belongProduct = rdc_product_name_convert(mr_info.get("belongProduct", ""))
    record["belongProduct"] = belongProduct
    record["changeAnalysis"] = analysis
    record["requirementPrePlanning"] = str(requirementPrePlanning)
    record["specificationByExampleUrl"] = str(specificationByExampleUrl)
    record["designSpecificationUrl"] = board_design_url
    record["requirementSource"] = requirementSource
    record["expectedFinishDate"] = expectedFinishDate
    record["requirementPurpose"] = requirementPurpose
    record["customer"] = customer
    record["targetMarket"] = targetMarket
    record["marketTarget"] = marketTarget
    record["requirementSubmitter"] = str(employ_no)
    record["acceptanceOwner"] = str(employ_no)
    record["requirementCategory"] = mr_info.get("requirementCategory","")
    record["verificationMode"] = mr_info.get("verificationMode","")
    record["verificationTeam"] = mr_info.get("verificationTeam","")

    record["priority"] = "5"
    record["IsKeyRequirement"] = "否"
    record["IsChipRequirement"] = "否"
    record["IsCompetitiveRequirement"] = "否"
    record["IsMediumLongTermRequirement"] = "否"
    
    results.append(record)
    # logger.info(f"----------results:{results}\n")
    rdc_info, permission_flag = create_RDC_MR(results, body_params.get("task_id"))
    if not permission_flag:
        return rdc_info
    time.sleep(request_interval)
    # logger.info(f"-------- rdc_info: {rdc_info} --------")

    global mr_rdc_info_table
    for rdc_item in rdc_info:
        mr_title = rdc_item.get("rdcTitle", "")
        mr_rdc_info_table_all.append({
                'rdcIdent': rdc_item.get("rdcIdent", ""),
                'rdcTitle': mr_title
            })
        if "M021" in mr_title or "M022" in mr_title or "M132" in mr_title or "M351" in mr_title:
            mr_rdc_info_table.append({
                'rdcIdent': rdc_item.get("rdcIdent", ""),
                'rdcTitle': mr_title
            })

    return rdc_info

def format_board_name(board_name: str) -> Tuple[str, str]:
    """
    将单板名称和端口列表转换为指定格式的字符串。
    
    返回: (prefix, alpha_bracket)
    - prefix: 处理后的前缀（不含任何括号及其内容）
    - alpha_bracket: 纯字母括号内容（含括号），若无则为空字符串
    
    规则：
    1. 若括号内为纯数字/字母/混合的代码（如"(80A1H)"），则去掉该括号及其内容。
    2. 若括号内为纯字母（如"(FG)"），提取出来作为 alpha_bracket（含括号），prefix 中不含该括号。
    3. 若同时出现"(FG)(80A1H)"形式，alpha_bracket="(FG)"，prefix 去掉所有括号。
    """
    matches = re.findall(r'\(([^)]+)\)', board_name)
    
    if not matches:
        return board_name, ""
    
    alpha_brackets = [m for m in matches if m.isalpha()]
    alpha_bracket = f"({alpha_brackets[0]})" if alpha_brackets else ""
    
    # 去掉所有括号及其内容，得到纯净前缀
    prefix = re.sub(r'\([^)]*\)', '', board_name)
    
    return prefix, alpha_bracket

def format_board_port(board_name: str, port_list: List[str]) -> str:
    prefix, svc = format_board_name(board_name)
    ports_digits = [port[1:] for port in port_list]
    return f"{prefix}x{'/x'.join(ports_digits)}{svc}"

def get_package_types(parts: List[str]) -> List[str]:
    """
    从形如 ['新易盛_QSFP28(4*28)_物料代码1_PN1', ...] 或 ['SFP光模块', 'SFP+光模块'] 的列表中
    提取并返回 ['QSFP28_物料代码1_PN1', ...] 或 ['SFP', 'SFP+']
    """
    result = []
    for item in parts:
        # 检查是否包含 '_'，用于区分两种格式
        if '_' in item:
            # 按 '_' 切分成三段：厂家 | 封装类型(通道信息) | 物料代码1_PN...
            seg = item.split('_', 2)
            if len(seg) < 3:
                continue  # 格式异常，跳过
            package_part = seg[1]  # 'QSFP28(4*28)'
            package = package_part.split('(')[0]  # 'QSFP28'
            remain = seg[2]  # '物料代码1_PN1'
            result.append(f"{package}_{remain}")
        else:
            # 对于没有 '_' 的格式，直接提取光模块类型
            # 使用正则表达式提取光模块类型（如 SFP, SFP+）
            match = re.match(r'([A-Za-z0-9+-]+)', item)
            if match:
                result.append(match.group(1))
    return result

def get_sub_feature(data: Dict[str, str]) -> str:
    """
    从字典中提取 subFeature 字段的值。
    若缺失则返回空字符串。
    """
    return data.get("subFeature", "")

def add_board_suffix(parts: List[str], board_suffix: str) -> List[str]:
    return [f"{board_suffix}-{item}" for item in parts]

def add_board_suffix_str(parts: str, board_suffix: str) -> List[str]:
    return [f"{board_suffix}-{item}" for item in parts.split(",") if item]

def rdc_package_type_splite(board_tree, features_list, mod_type, feature, body_params):
    board_name = board_tree.get("board")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    # logger.info(features_list)
    # mod_type = get_factor_val_by_board_tree(board_name, factor)
    # cfp = list(set(get_package_types(mod_type)))
    # cfp = mod_type
    # logger.info(f"====mod_type: {mod_type}, cfp: {cfp}======")
    # # 获取灰光子特性列表（有的需要一对一，需进一步处理）单板模型对应的所有灰光特性子特性
    sub_feature = get_opt_sub_feature_by_global_st(features_list, feature)#测试替换
    # logger.info(sub_feature)
    logger.info("--------rdc_package_type_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        # 组装RDC名称
        rdc_name = add_board_suffix(mod_type, subfeature +"-" + hd_sub)
        # 创建RDC并将数据回填到子特性中，多个时会拷贝创建
        ret = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return sub_feature

# 线路侧模块简称合并处理
def extract_module_prefix(pn_list: List[str]) -> List[str]:
    """
    支持两种格式：
      - C08M1_PN2        -> 前缀 C08M1，后缀 PN2
      - C04M3            -> 前缀 C04M3，后缀 空串
    输出保持原顺序并去重拼接，例如：
    ["C08M1_PN2/PN4", "C04M4_PN3", "C04M3"]
    """
    groups: Dict[str, List[str]] = OrderedDict()

    for pn in pn_list:
        if '_' in pn:
            prefix, suffix = pn.split('_', 1)
        else:
            prefix, suffix = pn, ""          # 无下划线时后缀为空
        groups.setdefault(prefix, []).append(suffix)

    # 组装：后缀为空时直接输出前缀，否则 prefix_suffix1/suffix2...
    return [
        f"{prefix}_{'/'.join(s for s in suffixes if s)}" if any(suffixes)
        else prefix
        for prefix, suffixes in groups.items()
    ]

def extract_module_prefix_str(pn_str: str) -> List[str]:
    """
    支持两种格式（输入为逗号分隔的字符串）：
      - C08M1_PN2        -> 前缀 C08M1，后缀 PN2
      - C04M3            -> 前缀 C04M3，后缀 空串
    输出保持原顺序并去重拼接，例如：
    ["C08M1_PN2/PN4", "C04M4_PN3", "C04M3"]
    """
    pn_list = [s.strip() for s in pn_str.split(',') if s.strip()]  # 转回列表
    groups: Dict[str, List[str]] = OrderedDict()

    for pn in pn_list:
        if '_' in pn:
            prefix, suffix = pn.split('_', 1)
        else:
            prefix, suffix = pn, ""
        groups.setdefault(prefix, []).append(suffix)

    return [
        f"{prefix}_{'/'.join(s for s in suffixes if s)}" if any(suffixes)
        else prefix
        for prefix, suffixes in groups.items()
    ]

# 线路侧模块模块简称的rdc
def rdc_mod_type_splite(board_tree, features_list, mod_type, body_params, opt_svc_analysis:str=""):
    board_name = board_tree.get("board")
    hd_sub = get_hd_sub_type_by_name(board_tree)

    # 获取模块封装类型_物料代码_PN
    # mod_type = get_factor_val_by_board_tree(board_name, "线路侧光模块")
    cfp = extract_module_prefix(mod_type)
    sub_feature = get_opt_sub_feature_by_global_st(features_list, "彩光业务")
    rdc_ret_val = []
    logger.info("---------rdc_mod_type_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        rdc_name = add_board_suffix(cfp, subfeature +"-" + hd_sub)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params, opt_svc_analysis)
    return rdc_ret_val

def get_hd_sub_type_by_name(board_tree):
    board_name = board_tree.get("board", "")
    board_type = board_tree.get("板卡类型", "")
    # 组装单板名称端口数 如M2C4Rx5/x6
    logger.info(f"-------get_hd_sub_type_by_name: board_type:{board_type}---------")
    if "支线路合一" in board_type or "桥接B" in board_type:
        prefix, svc = format_board_name(board_name)
        return f"{prefix}{svc}"

    subcards = get_factor_val_by_board_tree(board_name, "物理端口数量")
    card = format_board_port(board_name, subcards)
    logger.info(f"-------get_hd_sub_type_by_name: card:{card}---------")

    return card

def filter_shelf_type_patterns(items: List[str], *patterns: str) -> List[str]:
    """
    返回列表中 至少包含任意一个给定 pattern 的条目
    :param items: 待过滤字符串列表
    :param patterns: 可变长度模式字符串，如 'G2', 'G2-E'
    """
    filtered = [it for it in items if any(p in it for p in patterns)]
    return list(dict.fromkeys(filtered))

def rdc_bp_svc_feature_splite(board_tree, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    shelf_type = board_tree.get("单板支持的子架", "")
    if not shelf_type:
        logger.info("shelf_type is null")
        return 
    s_type = process_shelf_type_string(shelf_type)
    board_features = get_feature_by_global_st_first(features_list, "电层业务", "BP业务")
    sub_feature = get_sub_feature_by_global_st(board_features)
    rdc_ret_val = []
    logger.info("----------rdc_bp_svc_feature_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        shelf_type = s_type
        if "FS020601-01" in subfeature:
            shelf_type = filter_shelf_type_patterns(s_type, 'G2', 'G2-E')
        if "FS020601-02" in subfeature:
            shelf_type = filter_shelf_type_patterns(s_type, 'M1S3F', 'M1S3F-E')
        if "FS020601-03" in subfeature:
            shelf_type = filter_shelf_type_patterns(s_type, 'M2S3F-E(B)', 'M2S3F-E(FB)', 'M2S3F-E(B|FB)')
        if "FS020601-11" in subfeature:   
            rdc_name = subfeature + "-" + hd_sub  
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, [rdc_name], i, body_params)
            continue
        if "FS020611-04" in subfeature:
            shelf_type = filter_shelf_type_patterns(s_type, 'M2S3F-E(B)', 'M2S3F-E(FB)', 'M2S3F-E(B|FB)')
        if len(shelf_type) < 1:
            continue          
        rdc_name = add_board_suffix(shelf_type, subfeature + "-" + hd_sub)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def rdc_basic_boot_feature_splite(board_tree, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    cfg_type = board_tree.get("单板配置类型", "")

    board_features = get_feature_by_global_st_first(features_list, "单板基础启动管理", "光电业务(业务板)")
    sub_feature = get_sub_feature_by_global_st(board_features)
    rdc_ret_val = []
    logger.info("------------rdc_basic_boot_feature_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        if cfg_type:
            b_cfg_type = ",".join(part.split('_', 1)[0] + "配置类型" for part in cfg_type.split(',')) 
            rdc_name = add_board_suffix_str(b_cfg_type, subfeature + "-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
        else:
            rdc_name = subfeature + "-" + hd_sub
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, [rdc_name], i, body_params)
    return rdc_ret_val

def rdc_other_feature_splite(board_tree, first, second, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    board_features = get_feature_by_global_st_first(features_list, first, second)
    sub_feature = get_sub_feature_by_global_st(board_features)
    rdc_ret_val = []
    logger.info("---------rdc_other_feature_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        rdc_name = [subfeature + "_" + hd_sub]
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def rdc_workwear_feature_splite(board_tree, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board", "")
    c_mod_type = board_tree.get("客户侧光模块", "")
    mod_type = board_tree.get("线路侧光模块", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    board_features = get_feature_by_global_st_first(features_list, "工装可生产性", "光电业务(业务板)")
    sub_feature = get_sub_feature_by_global_st(board_features)
    rdc_ret_val = []
    logger.info("-------------rdc_workwear_feature_splite")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        if c_mod_type and "灰光模块" in subfeature:
            rdc_name = [subfeature + "_" + hd_sub]
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
        if mod_type and "彩光模块" in subfeature:
            rdc_name = [subfeature + "_" + hd_sub]
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
        if "灰光模块" not in subfeature and "彩光模块" not in subfeature:
            rdc_name = [subfeature + "_" + hd_sub]
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def business_rate_classification(input_str: str) -> List[str]:
    flexo_set = {"FlEXO-1", "FlEXO-2", "FlEXO-4", "FlEXO-8", "FlEXO-12", "FlEXO-16"}
    otuc_set = {"OTUC1", "OTUC2", "OTUC4", "OTUC8", "OTUC12", "OTUC16"}
    ge_set = {"100GE", "200GE", "400GE", "800GE"}
    ge_phy_set = {"100GE-PHY", "200GE-PHY", "400GE-PHY", "800GE-PHY"}

    items = [s.strip() for s in input_str.split(",") if s.strip()]

    ge_done: Dict[str, str] = {}   # base -> 最终字符串
    others: List[str] = []
    out_lines: List[str] = []
    # 分类
    for it in items:
        if it in flexo_set and it not in out_lines:
            out_lines.append(it)
        elif it in otuc_set and it not in out_lines:
            out_lines.append(it)
        elif it in ge_set or it in ge_phy_set:
            base = it.split("-")[0]
            if base in ge_done:
                continue
            phy = base + "-PHY"
            if base in items and phy in items:
                ge_done[base] = f"{base}/{phy}"
            else:
                ge_done[base] = base
        elif it not in others:
            others.append(it)

    for base in ge_done:
        out_lines.append(ge_done[base])

    if others:
        out_lines.append("/".join(others))

    return out_lines

def filter_svc_rate_by_cfg_type(cfg_type: str, svc_rate: List[str]) -> List[str]:
    """
    仅返回 svc_rate 中出现在 cfg_type 里的字段（大小写不敏感，子串即可）
    """
    if not cfg_type:
        return svc_rate
    cfg_type = cfg_type.lower()
    return [item for item in svc_rate if item.lower() in cfg_type]

def ele_layer_o_svc_split_rules(sub_feature, module_str: str, target_feature: str, rules: List[Tuple[str, Set[str]]]):
    module_set = {k.strip().upper() for k in re.split(r'[,/]', module_str) if k.strip()}
    feat = sub_feature.get("feature")
    sub  = sub_feature.get("subFeature", "")
    if feat.upper() == target_feature.upper() or target_feature.upper() in feat.upper():
        for key_info, kw_set in rules:
            kw_upper = {k.upper() for k in kw_set}
            hit = set()
            for kw in kw_upper:
                if kw in module_set:
                    hit.add(kw)
            # hit = module_set & {k.upper() for k in kw_set}
            if key_info in sub and hit:
                return hit
    return ""

def rdc_ele_svc_feature_splite_info(sub_feature, svc):
    # 特征码与对应 info 的全局变量映射表
    feature_info_map = (
        (gs_feature_f020101, gs_feature_f020101_info),
        (gs_feature_f020102, gs_feature_f020102_info),
        (gs_feature_f020103, gs_feature_f020103_info),
        (gs_feature_f020104, gs_feature_f020104_info),
        (gs_feature_f020105, gs_feature_f020105_info),
        (gs_feature_f030101, gs_feature_f030101_info),
        (gs_feature_f030102, gs_feature_f030102_info),
        (gs_feature_f030121, gs_feature_f030121_info),
        (gs_feature_f040109, gs_feature_f040109_info),
        (gs_feature_f040115, gs_feature_f040115_info),
        (gs_feature_f040120, gs_feature_f040120_info),
        (gs_feature_f040128, gs_feature_f040128_info),
        (gs_feature_f040129, gs_feature_f040128_info),
        (gs_feature_f040132, gs_feature_f040132_info),
        (gs_feature_f040140, gs_feature_f040140_info_l),
        (gs_feature_f040141, gs_feature_f040141_info)
    )

    for feat, info in feature_info_map:
        svc_type = ele_layer_o_svc_split_rules(sub_feature, svc, feat, info)
        if svc_type:                # 一旦命中立即返回
            return svc_type
    return None                     # 全部未命中

class CfgScene(Enum):
    """配置场景枚举"""
    SVC_RATE = 1      # 业务速率配置类型
    RELAY = 2         # 中继配置类型
    OTHER = 3         # other_cfg_flag 走默认 rate_type

def handle_sub_features(board_tree, cfg_type, sub_feature, scene: CfgScene, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board","")
    scv_c = board_tree.get("客户侧电层业务","")
    scv_l = board_tree.get("线路侧电层业务","")
    svc = scv_c + "," + scv_l
    rdc_ret_val = []
    # 客户侧业务拆分
    GROUP_C = [
        "F030141-E-O业务", "F030142-E-O业务", "F040101-E-O业务",
        "F040105-E-O业务", "F040136-E-O业务"
    ]

    # 线路侧业务拆分
    GROUP_L = ["F030143-E-O业务", "F030144-E-O业务", "F030161-E-O业务"]

    # 默认不拆分
    GROUP_SKIP = [
        "F030103-E-O业务", "F030104-E-O业务", "F030105-E-O业务",
        "F030106-E-O业务", "F040114-E-O业务"
    ]

    hd_sub = get_hd_sub_type_by_name(board_tree)
    rate_type = business_rate_classification(svc)
    # logger.info(f"---- scv_c: {scv_c} scv_l: {scv_l}--rate_type:{rate_type}, cfg_type:{cfg_type}-----")
    logger.info("------------handle_sub_features")
    log_step()
    for i in sub_feature:
        feature = i.get('feature')
        subfeature = i.get("subFeature")
        if scene == CfgScene.SVC_RATE or scene == CfgScene.RELAY:
            var = re.split(r'_(?:业务速率配置类型|中继配置类型)', cfg_type)[0].strip('[]')
            rate = ','.join(filter_svc_rate_by_cfg_type(cfg_type, rate_type))
            sub_str = subfeature + "-" + hd_sub + "-" + var
        else: 
            sub_str = subfeature + "-" + hd_sub
            rate = ','.join(rate_type)
        
        # 统一判断
        svc_type = rdc_ele_svc_feature_splite_info(i, rate)
        if svc_type:
            rdc_name = add_board_suffix(svc_type, sub_str)
        elif scv_c and (any(f in feature for f in GROUP_C) or "FS040209-01-E-DM-客户侧" in subfeature):
            scv_c_type = business_rate_classification(scv_c)
            rdc_name = add_board_suffix(scv_c_type, sub_str)
        elif scv_l and (any(f in feature for f in GROUP_L) or "FS040209-01-E-DM-线路侧" in subfeature):
            scv_l_type = business_rate_classification(scv_l)
            rate = filter_svc_rate_by_cfg_type(cfg_type, scv_l_type)
            rdc_name = add_board_suffix(rate, sub_str)
            logger.info(f"---- scv_l: {scv_l} sub_str: {sub_str}--scv_l_type:{scv_l_type}, rdc_name:{rdc_name}-----")
        elif any(f in feature for f in GROUP_SKIP):
            continue
        else:
            rdc_name = [sub_str]
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)

    return rdc_ret_val


def handle_sub_features_update_board(board_tree, cfg_type, part, sub_feature, scene: CfgScene, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board","")
    scv_c = board_tree.get("客户侧电层业务","")
    scv_l = board_tree.get("线路侧电层业务","")
    svc = scv_c + "," + scv_l
    rdc_ret_val = []
    # 客户侧业务拆分
    GROUP_C = [
        "F030141-E-O业务", "F030142-E-O业务", "F040101-E-O业务",
        "F040105-E-O业务", "F040136-E-O业务"
    ]

    # 线路侧业务拆分
    GROUP_L = ["F030143-E-O业务", "F030144-E-O业务", "F030161-E-O业务"]

    # 默认不拆分
    GROUP_SKIP = [
        "F030103-E-O业务", "F030104-E-O业务", "F030105-E-O业务",
        "F030106-E-O业务", "F040114-E-O业务"
    ]

    hd_sub = get_hd_sub_type_by_name(board_tree)
    rate_type = business_rate_classification(svc)
    #logger.info(f"---- scv_c: {scv_c} scv_l: {scv_l}--rate_type:{rate_type}, cfg_type:{cfg_type}-----")
    logger.info("------------handle_sub_features_update_board")
    log_step()
    for i in sub_feature:
        feature = i.get('feature')
        subfeature = i.get("subFeature")
        if scene == CfgScene.SVC_RATE or scene == CfgScene.RELAY:
            var = re.split(r'_(?:业务速率配置类型|中继配置类型)', cfg_type)[0].strip('[]')
            rate = ','.join(filter_svc_rate_by_cfg_type(cfg_type, rate_type))
            sub_str = subfeature + "-" + hd_sub + "-" + var
        else: 
            sub_str = subfeature + "-" + hd_sub
            rate = ','.join(rate_type)
        
        # 统一判断
        svc_type = rdc_ele_svc_feature_splite_info(i, rate)
        if svc_type:
            rdc_name = add_board_suffix(svc_type, sub_str)
            logger.info(f"---- svc_type: {svc_type} sub_str: {sub_str}, rdc_name:{rdc_name}-----")
        elif scv_c and (any(f in feature for f in GROUP_C) or "FS040209-01-E-DM-客户侧" in subfeature):
            scv_c_type = business_rate_classification(scv_c)
            rdc_name = add_board_suffix(scv_c_type, sub_str)
            logger.info(f"---- have scv_c for client_rdc: {scv_c} sub_str: {sub_str}--scv_l_type:{scv_c_type}, rdc_name:{rdc_name}-----")
        elif scv_l and (any(f in feature for f in GROUP_L) or "FS040209-01-E-DM-线路侧" in subfeature):
            scv_l_type = business_rate_classification(scv_l)
            rate = filter_svc_rate_by_cfg_type(cfg_type, scv_l_type)
            rdc_name = add_board_suffix(rate, sub_str)
            logger.info(f"---- have scv_l for line rdc: {scv_l} sub_str: {sub_str}--scv_l_type:{scv_l_type}, rdc_name:{rdc_name}-----")
        elif not scv_c and (any(f in feature for f in GROUP_C) or "FS040209-01-E-DM-客户侧" in subfeature):
            rdc_name = add_board_suffix_str(part, sub_str)
            logger.info(f"----not scv_c for client_rdc add part: sub_str: {sub_str}--part:{part}, rdc_name:{rdc_name}-----")
        elif not scv_l and (any(f in feature for f in GROUP_L) or "FS040209-01-E-DM-线路侧" in subfeature):
            rdc_name = add_board_suffix_str(part, sub_str)
            logger.info(f"----not scv_l for line_rdc add part: sub_str: {sub_str}--part:{part}, rdc_name:{rdc_name}-----")            
        elif any(f in feature for f in GROUP_SKIP):
            continue
        else:
            rdc_name = add_board_suffix_str(part, sub_str)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)

    return rdc_ret_val

def rdc_ele_svc_feature_splite(board_tree, features_list, body_params, is_c_l_flag: False, relay_splite: True):
    cfg_type = board_tree.get("单板配置类型","")
    head_employ_no = body_params.get('employ_no', '')
    rdc_ret_val = []
    other_cfg_flag = True

    sub_feature = get_ele_sub_feature_by_global_st(features_list) 
    if not cfg_type:
        return handle_sub_features(board_tree, "", sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)

    for seg in cfg_type.split(","):
        seg = seg.strip()
        if "业务速率配置类型" in seg:
            rdc_ret_val += handle_sub_features(board_tree, seg, sub_feature, CfgScene.SVC_RATE, features_list, body_params, is_c_l_flag)
            continue

        if "中继配置类型" in seg and relay_splite:
            board_factor = extract_board_global_status(board_tree)
            part_cont = '新增中继类型' 
            cfg_features = querySrcFeatureChangeRelation(part_cont)
            merged_list = merge_to_global_status_list(board_factor, cfg_features, head_employ_no)
            addSrcBoardWholeStatusData(merged_list, head_employ_no)
            sub_feature = get_sub_feature_by_global_st(merged_list)
            rdc_ret_val += handle_sub_features(board_tree, seg, sub_feature, CfgScene.RELAY, merged_list, body_params, is_c_l_flag)

            continue

        if other_cfg_flag:
            other_cfg_flag = False
            rdc_ret_val += handle_sub_features(board_tree, "", sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)
            continue

    return rdc_ret_val

def mod_type_and_svc_type_ortho_join(svc_type: List[str], mod_type: List[str]) -> List[str]:
    """
    正交拼接：svc_type 每个元素与 mod_type 每个元素拼接，用 '_' 连接。
    自动过滤掉空字符串。
    """
    if len(mod_type) < 1:
        return svc_type
    # 过滤空串
    svc_type = [s for s in svc_type if s]
    mod_type = [m for m in mod_type if m]
    
    # 正交拼接
    return [f"{svc_id}_{mod_id}" for svc_id in svc_type for mod_id in mod_type]

def extract_cfp_code_left(pn_list: List[str]) -> List[str]:
    """
    取每个字符串第二个 '_' 左侧的部分并去重，保持首次出现顺序
    """
    seen = set()
    out = []
    for s in pn_list:
        # 按 '_' 拆分，取前 2 段再拼回去
        parts = s.split('_', 2)[:2]
        key = '_'.join(parts)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out

_pat1 = re.compile(r'^[^_]+_(.+?)_[^_]+')
_pat2 = re.compile(r'(^|[^A-Za-z0-9])(SFP\+?|XFP|CFP2?)(?=[^A-Za-z0-9]|$)', re.I)

def get_pkg_type(s: str) -> Optional[str]:
    s = s.strip()
    # 1. 旧规则
    m = _pat1.match(s)
    if m:
        return m.group(1)
    # 2. 新规则
    m = _pat2.search(s)
    return m.group(2).upper() if m else None

def extract_all_pkg_type(lst: List[str]) -> Set[str]:
    """带调试信息的版本，方便一眼看出哪条没提取到"""
    result = set()
    for idx, s in enumerate(lst, 1):
        pkg = get_pkg_type(s)
        if pkg:
            result.add(pkg)
        else:
            logger.info(f'[WARN] 第{idx}行未提取到封装类型: {s!r}')
    # 合并 SFP / SFP+
    if {'SFP', 'SFP+'}.issubset(result):
        result -= {'SFP', 'SFP+'}
        result.add('SFP/SFP+')
    if {'CFP', 'CFP2'}.issubset(result):
        result -= {'CFP', 'CFP2'}
        result.add('CFP/CFP2')
    return result

# ---------- 1. 速率映射 ----------
def get_speed_by_type(data: List[Dict], biz_type: str) -> Optional[str]:
    """
    根据业务类型字符串（如 "800GE"）返回对应的 businessSpeed。
    若未匹配到，返回 None。
    """
    biz_type = biz_type.split("/")[0].strip()
    for item in data:
        # 按逗号拆分成列表并去掉首尾空格
        types = [t.strip() for t in item.get("businessType", "").split(",")]
        if biz_type in types:
            return re.findall(r'(\d+(?:\.\d+)?)G', item.get("businessSpeed"))
    return ""

def below_rate(val: int, rate_type) -> List[str]:   # ← 改成 List[str]
    return [r for r in rate_type
            if int(re.search(r'\d+', r).group()) <= val]

def get_left_part(text):
    """获取字符串中第一个'/'左侧的内容，如果不包含'/'则返回原字符串"""
    return text.split("/")[0] if "/" in text else text

def rdc_client_mod_type_splite_color(board_name, c_mod_type, hd_sub, scv_c, features_list, body_params):
    rdc_ret_val = []
    cfp = c_mod_type.split(',')
    rate_type = business_rate_classification(scv_c)
    logger.info(f"---rate_type:{rate_type}------")
    mod_cfp = extract_all_pkg_type(cfp)
    mod_cfp_list = list(mod_cfp)
    rate_table = querySrcBusinessSpeedTypeByParams({}, markdown_flag=True)
    col: Dict[str, List[str]] = {k: [s for s in cfp if k in s] for k in mod_cfp}
    sub_feature = get_sub_feature_by_global_st_color("灰光业务基础", features_list)
    logger.info("----------rdc_client_mod_type_splite_color")
    log_step()
    for i in sub_feature:
        subfeature = i.get("subFeature")
        sub_cfp = re.search(r'E-([^灰]+)灰光模块', subfeature).group(1).upper()
        for pkg_type, row_list in col.items():
            for svc_id in rate_type:
                first_svc = get_left_part(svc_id)
                rate = list(map(float, get_speed_by_type(rate_table, first_svc)))
                logger.info(f"--------- svc_id: {svc_id}, first_svc: {first_svc}, rate: {rate} ---------------")

                if len(row_list) < 1:
                    row_list = mod_cfp_list
                logger.info(f"000 sub_cfp:{sub_cfp}, pkg_type:{pkg_type}, rate:{rate}, row_list:{row_list} ")
                if sub_cfp.startswith('XFP') and pkg_type.startswith('XFP') and rate[0] < 50:
                    rdc = add_board_suffix_str(svc_id, subfeature +"-" + hd_sub)
                    rdc_name = mod_type_and_svc_type_ortho_join(rdc, row_list)  
                    rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params) 
                    continue
                if sub_cfp.startswith('SFP') and pkg_type.startswith('SFP') and rate[0] < 50:
                    rdc = add_board_suffix_str(svc_id, subfeature +"-" + hd_sub)
                    rdc_name = mod_type_and_svc_type_ortho_join(rdc, row_list)  
                    rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
                    continue 
                if sub_cfp.startswith('CFP') and pkg_type.startswith('CFP') and rate[0] < 50:
                    rdc = add_board_suffix_str(svc_id, subfeature +"-" + hd_sub)
                    rdc_name = mod_type_and_svc_type_ortho_join(rdc, row_list)  
                    rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
                    continue 
                if "QSFPDD(8*56)" in pkg_type and "QSFP-DD(8*56)" in sub_cfp:
                    lan, lane_rate = map(int, re.search(r'\((\d+)\*(\d+)\)', pkg_type).groups())
                    if rate[0] < lan * lane_rate:
                        rdc = add_board_suffix_str(svc_id, subfeature +"-" + hd_sub)
                        rdc_name = mod_type_and_svc_type_ortho_join(rdc, row_list)  
                        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params) 
                        continue
                if "QSFP" in pkg_type and pkg_type == sub_cfp:
                    lan, lane_rate = map(int, re.search(r'\((\d+)\*(\d+)\)', pkg_type).groups())
                    if rate[0] < lan * lane_rate:
                        rdc = add_board_suffix_str(svc_id, subfeature +"-" + hd_sub)
                        rdc_name = mod_type_and_svc_type_ortho_join(rdc, row_list)  
                        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params) 
                        continue 
    return rdc_ret_val

def rdc_mod_type_splite_color(board_tree, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    scv_c = board_tree.get("客户侧电层业务","")
    scv_l = board_tree.get("线路侧电层业务","")
    c_mod_type = board_tree.get("客户侧光模块","")
    l_mod_type = board_tree.get("线路侧光模块","")
    rdc_ret_val = []

    mod_opt_svc = board_tree.get("opt_biz_relation", "")
    if mod_opt_svc:
        mod_opt_svc = mod_opt_svc.get("add","")
        
    if l_mod_type:
        mod_type = str_to_list(l_mod_type)
        for mod_id in mod_type:
            analysis = ""
            if is_gray_optical_mod(mod_id):
                # cfp = get_package_types(l_mod_type.split(','))
                # cfp = extract_cfp_code_left(cfp)
                cfp = mod_id.split(',')
                rate_type = business_rate_classification(scv_l)
                sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)
            elif is_cfp_optical_mod(mod_id):
                cfp = mod_id.split(',')
                rate_type = business_rate_classification(scv_l)
                sub_feature = get_sub_feature_by_global_st_color("灰光业务基础", features_list)            
            else:
                cfp = extract_module_prefix_str(mod_id)
                rate_type = business_rate_classification(scv_l)
                sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)
                if len(mod_opt_svc) > 0:
                    opt_svc = get_biz_by_opt(mod_id, mod_opt_svc)
                    analysis = f"支持-{opt_svc}-光层业务"

            logger.info("-------------rdc_mod_type_splite_color")
            log_step()
            for i in sub_feature:
                subfeature = i.get("subFeature")
                if "彩光业务-低温冷启动" in subfeature:
                    rdc = add_board_suffix_str(hd_sub, subfeature)
                else:
                    rdc = add_board_suffix(rate_type, subfeature +"-" + hd_sub)
                rdc_name = mod_type_and_svc_type_ortho_join(rdc, cfp)
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params, analysis)

    if c_mod_type:
        rdc_ret_val = rdc_client_mod_type_splite_color(board_name, c_mod_type, hd_sub, scv_c, features_list, body_params)
                         
    return rdc_ret_val

def rdc_opt_svc_and_mod_splite(board_tree, features, body_params, is_c_l_flag: False):
    c_mod_type = board_tree.get("客户侧光模块", "")
    l_mod_type = board_tree.get("线路侧光模块", "")

    if c_mod_type:
        c_mod_type = str_to_list(c_mod_type)
        rdc_package_type_splite(board_tree, features, c_mod_type, "灰光业务", body_params)

    mod_opt_svc = board_tree.get("opt_biz_relation", "")
    if mod_opt_svc:
        mod_opt_svc = mod_opt_svc.get("add","")

    if l_mod_type:
        mod_type = str_to_list(l_mod_type)
        for mod_id in mod_type:
            analysis = ""
            if is_gray_optical_mod(mod_id):
                logger.info("---------is 线路侧 灰光---------")
                rdc_package_type_splite(board_tree, features, [mod_id], "彩光业务", body_params)
            elif is_cfp_optical_mod(mod_id):
                rdc_package_type_splite(board_tree, features, [mod_id], "灰光业务", body_params)
            else:
                logger.info("---------is 线路侧 PN---------")
                if len(mod_opt_svc) > 0:
                    opt_svc = get_biz_by_opt(mod_id, mod_opt_svc)
                    analysis = f"支持-{opt_svc}-光层业务"
                rdc_mod_type_splite(board_tree, features, [mod_id], body_params, analysis) 

def rdc_add_board_whole_st_data(board_tree, features, board_type, body_params, relay_splite):
    board_type = board_tree.get("板卡类型", "")
    is_c_l_flag = False
    if "支线路合一" in board_type or "桥接B" in board_type:
        is_c_l_flag = True
    logger.info(f"------------- board_type: {board_type} ---------------")
    rdc_opt_svc_and_mod_splite(board_tree, features, body_params, is_c_l_flag)
    rdc_mod_type_splite_color(board_tree, features, body_params, is_c_l_flag)
    rdc_ele_svc_feature_splite(board_tree, features, body_params, is_c_l_flag, relay_splite)
    rdc_bp_svc_feature_splite(board_tree, features, body_params, is_c_l_flag)
    rdc_basic_boot_feature_splite(board_tree, features, body_params, is_c_l_flag)
    rdc_other_feature_splite(board_tree, "高可靠性", "网元级业务", features, body_params, is_c_l_flag)
    rdc_other_feature_splite(board_tree, "可维可服", "光电业务(业务板)", features, body_params, is_c_l_flag)
    rdc_workwear_feature_splite(board_tree, features, body_params, is_c_l_flag)

def split_mgr_c_and_mgr_l(mgr_l_list: List[Dict], mgr_c_list: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    将两份 MGL 数据拆分成：
    1. 仅 mgr_l_list 中存在（独有）
    2. 仅 mgr_c_list 中存在（独有）
    3. 两份列表中都存在（共有）

    匹配键：feature + subFeature
    """
    # 用 (feature, subFeature) 作为唯一键
    def key(d: Dict) -> Tuple[str, str]:
        return d.get("feature", ""), d.get("subFeature", "")

    set_list = {key(item) for item in mgr_l_list}
    set_c = {key(item) for item in mgr_c_list}

    only_in_l = [item for item in mgr_l_list if key(item) not in set_c]
    only_in_c = [item for item in mgr_c_list if key(item) not in set_list]
    common = [item for item in mgr_l_list if key(item) in set_c]

    return only_in_l, only_in_c, common

def merge_mgr_c_and_mgr_l(mgr_l_list: List[Dict], mgr_c_list: List[Dict]) -> List[Dict]:
    key = lambda d: (d.get("rdcIdent", ""), d.get("rdcTitle", ""))

    seen = set()
    merged = []

    for src in (mgr_l_list, mgr_c_list):   # 先遍历 list，再遍历 c
        for item in src:
            k = key(item)
            if k not in seen:
                seen.add(k)
                merged.append(item)
    return merged

def merge_feature_mgr_c_and_mgr_l(mgr_l_list: List[Dict], mgr_c_list: List[Dict]) -> List[Dict]:
    key = lambda d: (d.get("feature", ""), d.get("subFeature", ""))

    seen = set()
    merged = []

    for src in (mgr_l_list, mgr_c_list):   # 先遍历 list，再遍历 c
        for item in src:
            k = key(item)
            if k not in seen:
                seen.add(k)
                merged.append(item)
    return merged

def filter_c_l_and_board(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    过滤 rdTitle 包含任意 pattern 的记录
    返回 (匹配列表, 剩余列表)
    """
    patterns = [
        'FS020102-51-E-告警屏蔽',
        'FS020102-52-E-性能门限',
        'FS020102-53-E-性能屏蔽',
        'FS020102-54-E-性能清零计数器',
        'FS020102-55-E-性能基准值',
        'FS020102-56-E-零性能抑制',
        'FS020102-57-E-性能实时测量',
        'FS020102-58-E-告警预投入',
        'FS020102-59-E-端口使能',
        'FS020102-60-E-告警防抖',
        'FS020102-61-E-告警反转',
        'FS040109-04-E-DM-O业务-双向时延性能及越限告警',
        'FS040109-05-E-DM-O业务-双向端到端查询时延结果要求两位小数精度',
        'FS040109-06-E-DM-O业务-双向时延单板支持按端口进行重要数据补偿功能']

    board, c_l_share = [], []
    for rec in records:
        first_class = rec.get("featureFirstType", "")
        title = rec.get("subFeature", "")
        if ("高可靠性" in first_class or "单板基础启动管理" in first_class or  "可维可服" in first_class 
            or "工装可生产性" in first_class) or any(p in title for p in patterns):
            board.append(rec)
        else:
            c_l_share.append(rec)
    return board, c_l_share
    
pr_bundle = {
        'c_pri': [],      # 主用交叉
        'c_pub': [],      # 主用公共
        'l_pri': [],      # 线路主用
        'l_pub': [],      # 线路公共
        'board': []       # 单板
    }

def clear_pr_bundle():
    """清空数据，但保持字典结构"""
    global pr_bundle
    pr_bundle['c_pri'].clear()
    pr_bundle['c_pub'].clear()
    pr_bundle['l_pri'].clear()
    pr_bundle['l_pub'].clear()
    pr_bundle['board'].clear()


def src_add_board_whole_st_data(body_params, head_employ_no, task_id):
    body_params["task_id"] = task_id
    body_params['text'] = ""
    board_name = body_params.get('board', '')
    split_rdc_flag = body_params.get('split_rdc_flag', '')
    stock_flag = body_params.get('stock_flag', '')
    force_split_flag = body_params.get('force_split_flag', '')
    create_mr_flag = body_params.get('createMR', '')

    from app import app
    with app.app_context():
        try:
            if not body_params.get("designSpecificationUrl"):
                body_params["designSpecificationUrl"] = query_board_tree_board_design_url_by_board_name(board_name)
            board_tree = get_product_factor_by_board(board_name)
            if len(board_tree) < 1:
                logger.error("--------单板数据不存在--------")
                task_info_dict = {
                    "task_status": "completed",
                    "task_err_reason": "单板数据不存在",
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)
                return

            # 2 从单板数获取"产品"、"板卡类型"、"单板业务模型"、"单板标识"
            board_factor = extract_board_global_status(board_tree)

            if stock_flag == "Y":
                # 从数据库目标单板的数据
                board_whole_status_data_list = queryBoardWholeStatusDataByBoardName(board_name)
                if force_split_flag != "Y":
                    stock_rdc_num = 0
                    for item in board_whole_status_data_list:
                        if item.get("related_rdc"):
                            stock_rdc_num += 1
                    # 如果数据库已经有需求拆分结果且没有要求强制覆盖拆分结果，那么就不操作且提醒前端
                    if stock_rdc_num:
                        message = f"{board_name}单板存在已关联的{stock_rdc_num}个PR, 不能作为存量单板进行需求拆分"
                        logger.info(message)
                        task_info_dict = {
                            "task_status": "completed",
                            "task_err_reason": f"{board_name}单板存在已关联的{stock_rdc_num}个PR, 不能作为存量单板进行需求拆分",
                            "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        update_task_info_dict(task_id, task_info_dict)
                        return
                # 删除数据原有的单板需求波及和需求拆分结果
                deleteBoardWholeStatusDataByBoardName(board_name)

            board_type = ','.join(set(board_factor["boardBusinessModel"].replace('-', '|').split('|')))
            logger.info(f"------ board_type:{board_type}, {board_factor['boardType']} -----\n")
            features = querySrcFeatureBoardRelation(board_type)

            global pr_rdc_info_table
            # 3 根据"单板业务模型"从特性树获取特性子特性并集'boardBusinessModel': 'L_O/L_V'
            if "支线路合一" in board_factor["boardType"]:
                features_l = querySrcFeatureBoardRelation("MGR_L")
                filter_features_l = filter_details_features_by_board_type(board_tree, features_l, is_c_flag=False)
                features_c = querySrcFeatureBoardRelation("MGR_C")
                filter_features_c = filter_details_features_by_board_type(board_tree, features_c, is_c_flag=True)

                filter_features = merge_mgr_c_and_mgr_l(filter_features_l, filter_features_c)
                merged_list = merge_to_global_status_list(board_factor, filter_features, head_employ_no)
                if len(merged_list) < 1:
                    logger.error(f"--------待合并到全局状态表的数据{merged_list}为空")
                    task_info_dict = {
                        "task_status": "completed",
                        "task_err_reason": f"待合并到全局状态表的数据{merged_list}为空",
                        "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    update_task_info_dict(task_id, task_info_dict)
                    return
                addSrcBoardWholeStatusData(merged_list, head_employ_no)

                # 5 添加变更分析
                results = board_format_change_analysis(board_tree, merged_list, head_employ_no)

                only_l_list, only_c_list, both_list = split_mgr_c_and_mgr_l(filter_features_l, filter_features_c)
                # both_list分成单板级和客户侧线路侧两部分
                board, c_l_share = filter_c_l_and_board(both_list)

                merged_l = merge_to_global_status_list(board_factor, only_l_list, head_employ_no)
                merged_c = merge_to_global_status_list(board_factor, only_c_list, head_employ_no)
                merged_l_c = merge_to_global_status_list(board_factor, c_l_share, head_employ_no)
                merged_board = merge_to_global_status_list(board_factor, board, head_employ_no)
                if split_rdc_flag.upper() == "Y":
                    pr_body_params = copy.deepcopy(body_params)
                    pr_body_params["employ_no"] = head_employ_no
                    global pr_bundle
                    clear_pr_bundle()
                    clear_pr_rdc_info_table()
                    rdc_add_board_whole_st_data(board_tree, merged_l, board_type, pr_body_params,relay_splite=True)
                    pr_bundle['l_pri'] = copy.deepcopy(pr_rdc_info_table)

                    clear_pr_rdc_info_table()
                    rdc_add_board_whole_st_data(board_tree, merged_c, board_type, pr_body_params, relay_splite=False)
                    pr_bundle['c_pri'] = copy.deepcopy(pr_rdc_info_table)

                    clear_pr_rdc_info_table()
                    rdc_add_board_whole_st_data(board_tree, merged_board, board_type, pr_body_params, relay_splite=False)
                    pr_bundle['board'] = copy.deepcopy(pr_rdc_info_table)

                    clear_pr_rdc_info_table()
                    rdc_add_board_whole_st_data(board_tree, merged_l_c, board_type, pr_body_params, relay_splite=False)
                    pr_bundle['c_pub'] = copy.deepcopy(pr_rdc_info_table)

                    clear_pr_rdc_info_table()
                    rdc_add_board_whole_st_data(board_tree, merged_l_c, board_type, pr_body_params, relay_splite=False)
                    pr_bundle['l_pub'] = copy.deepcopy(pr_rdc_info_table)

                    if create_mr_flag:
                        logger.info(f"create_mr_flag: {create_mr_flag}, 需要拆分MR")
                        rdc_mr_split_by_pr(board_tree, pr_rdc_info_table, body_params, head_employ_no)
                    return
            elif "客户侧" in board_factor["boardType"]:
                filter_features = filter_details_features_by_board_type(board_tree, features, is_c_flag=True)
            else:
                filter_features = filter_details_features_by_board_type(board_tree, features, is_c_flag=False)
            merged_list = merge_to_global_status_list(board_factor, filter_features, head_employ_no)
            addSrcBoardWholeStatusData(merged_list, head_employ_no)
            if len(merged_list) < 1:
                logger.error(f"--------待合并到全局状态表的数据{merged_list}为空")
                task_info_dict = {
                    "task_status": "completed",
                    "task_err_reason": f"待合并到全局状态表的数据{merged_list}为空",
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)
                return
            # 5 添加变更分析
            results = board_format_change_analysis(board_tree, merged_list, head_employ_no)
            if split_rdc_flag.upper() == "Y":
                ## 6 创建RDC回填编号和状态
                clear_pr_rdc_info_table()
                pr_body_params = copy.deepcopy(body_params)
                pr_body_params["employ_no"] = head_employ_no
                rdc_add_board_whole_st_data(board_tree, merged_list, board_type, pr_body_params,relay_splite=True)
                if create_mr_flag:
                    logger.info(f"create_mr_flag: {create_mr_flag}, 需要拆分MR")
                    rdc_mr_split_by_pr(board_tree, pr_rdc_info_table, body_params, head_employ_no)
        except Exception as e:
            logger.error(f"[{task_id}] 后台任务发生严重异常: {e}", exc_info=True)
            for handler in logger.handlers:
                handler.flush()
        finally:
            logger.info(f"[{task_id}] 后台任务线程结束")
            task_info_dict = {
                "task_status": "completed",
                "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update_task_info_dict(task_id, task_info_dict)
            for handler in logger.handlers:
                handler.flush()



def add_board_whole_st_data():
    """
    新增单板数据到单板全局状态表中
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
            employ_no:
              type: string
              description: 人员工号
            split_rdc_flag:
              type: string
              description: 是否拆分RDC标识
            requirementPrePlanning:
              type: string
              description: 需求预规划
            specificationByExampleUrl:
              type: string
              description: 需求实例化链接
            stock_flag:
              type: string
              description: 是否存量单板拆分
            force_split_flag:
              type: string
              description: 是否覆盖单板原有已拆分的RDC
            requirementType:
              type: string
              description: 需求类型
            belongTeam:
              type: string
              description: 归属团队
          example:   # 示例值
            board: "xx"
            employ_no: "123456"
            split_rdc_flag: "Y"
            requirementPrePlanning: "https://i.zte.com.cn/index/ispace"
            specificationByExampleUrl: "https://i.zte.com.cn/index/ispace"
            stock_flag: "N"
            force_split_flag: "N"
            requirementType: "平台团队需求"
            belongTeam: "L1-平台团队"
    responses:
      200:
        description: 成功新增数据
    """
    head_employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    logger.info(f"-------body_params:{body_params}")
    start_time = datetime.datetime.now()
    logger.info(f'--------start_time:{start_time.strftime("%Y-%m-%d %H:%M:%S")}')
    task_id = str(uuid.uuid4())
    stock_flag = body_params.get('stock_flag', '')
    task_info_dict = {}
    task_info_dict["employ_no"] = head_employ_no
    task_info_dict["employ_name"] = pub_get_employ_name(head_employ_no)
    task_info_dict["task_type"] = "存量单板" if stock_flag == "Y" else "新增单板"
    task_info_dict["task_param"] = body_params
    task_info_dict["task_status"] = "pending"
    task_info_dict["task_start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_task_info_dict(task_id, task_info_dict)
    thread = threading.Thread(target=src_add_board_whole_st_data, args=[body_params, head_employ_no, task_id])
    thread.daemon = False
    thread.start()
  
    return jsonify({"code": 200, "status": "success", "message": "新增单板处理逻辑进程启动，请根据返回的task_id调用get_task_result接口获取最终的执行结果", "data": [task_id]})


def get_rdc_split_task_result_dict():
    """
    查询需求拆分结果
    ---
    tags:
      - 单板全局状态
    description: 查询需求拆分结果
    parameters:
      - name: task_id
        in: query
        description: 任务id
        required: true
        type: string
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": {}}
    """
    query_params = request.args.to_dict()
    task_id = query_params.get("task_id", "")
    task_result_dict = query_task_info_dict_by_task_id(task_id)
    if not task_result_dict:
        return jsonify({"code": 500, "status": "failed", "message": f"获取失败", "data": task_result_dict})
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": task_result_dict})



#================ 5 RDC更新流程 =====================
def build_rdc_params(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    将输入的 List[Dict] 转换成
    {
        "rdc_space": "OTNSW",
        "rdcIdent_list": [...],
        "workItemType_list": ["PR", "PR", ...]
    }
    其中 rdcIdent_list 取自每条数据的 "rdcIdent" 字段，
    每条对应一个 "PR"。
    """
    rdc_idents = [item.get("rdcIdent", "") for item in data]
    return {
        "rdc_space": "OTNSW",
        "rdcIdent_list": rdc_idents,
        "workItemType_list": ["PR"] * len(rdc_idents)
    }

# 3. 数据回填并打印结果
def backfill_status(src_list: List[Dict[str, Any]],
                    api_resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将接口返回的 requirementStatus 回填到源列表中
    """
    # 以 rdcIdent 为 key 建立索引，方便 O(1) 查询
    status_map: Dict[str, str] = {
        item["rdcIdent"]: item["requirementStatus"]
        for item in api_resp.get("data", [])
    }

    # 遍历源列表并回填
    for row in src_list:
        rdc = row.get("rdcIdent")
        if rdc in status_map:
            row["requirementStatus"] = status_map[rdc]

    return src_list


def get_rdc_fault_num_dict(relation_id_dict):
    rdc_fault_num_dict = {}
    for rdc_list in relation_id_dict.values():
        for rdc_id in rdc_list:
            rdc_fault_num_dict[rdc_id] = rdc_fault_num_dict.get(rdc_id, 0) + 1
    return rdc_fault_num_dict


def build_rdc_fault_params(change_req_dict, board_tree, employ_no):
    """
    根据 change_req_dict 按 rdc_space 分组构建多个参数字典。
    
    Args:
        change_req_dict: dict, key 为 rdc_ident (如 "OTNSW-123"), value 为二维列表（每个元素是故障列表）
        board_tree: list, 至少包含一个 dict with "board" key
        employ_no: str
    
    Returns:
        List[dict]: 每个 dict 对应一个 rdc_space 分组的参数
    """
    if not change_req_dict:
        return []

    # Step 1: 按 rdc_space 分组 rdc_ident
    groups = defaultdict(list)
    for rdc_ident in change_req_dict.keys():
        rdc_space = rdc_ident.split('-')[0]
        groups[rdc_space].append(rdc_ident)

    # 获取公共字段
    related_board_name = board_tree[0].get("board") if board_tree else None

    result = []
    for rdc_space, rdc_idents in groups.items():
        # 合并该组所有 values（二维 -> 一维）
        flattened_values = []
        for ident in rdc_idents:
            values = change_req_dict[ident]
            if isinstance(values, list):
                for sublist in values:
                    if isinstance(sublist, list):
                        flattened_values.extend(sublist)
                    else:
                        # 如果不是二维，而是直接一维，则直接加（兼容性）
                        flattened_values.append(sublist)
            else:
                # 理论上不会发生，但防御性处理
                flattened_values.append(values)

        # 构造该组参数
        group_params = {
            "employ_no": employ_no,
            "related_board_name": related_board_name,
            "rdc_space": rdc_space,
            "change_req_dict": {ident: change_req_dict[ident] for ident in rdc_idents},
            "workItemType_list": ["chgRequest"] * len(flattened_values)
        }
        result.append(group_params)

    return result


# 全局状态表RDC更新
def update_board_whole_st_data():
    """
    更新单板全局状态RDC取值记录
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
            requirementType:
              type: string
              description: 需求类型
            belongTeam:
              type: string
              description: 归属团队
          example:   # 示例值
            board: "xx1,xx2"
            requirementType: "平台团队需求"
            belongTeam: "L1-平台团队"
    responses:
      200:
        description: 更新RDC状态数据
    """
    query_params = request.get_json()
    # 1 获取RDC非空单板全局状态表
    board_tree = querySrcBoardWholeStatusRDCByParams(query_params, markdown_flag=True)

    # 2 组装查询RDC状态的输入数据
    employ_no = request.headers.get('X-Emp-No')
    rdc_params = build_rdc_params(board_tree)
    # 3 根据输入查询RDC状态
    rdc_params["employ_no"] = employ_no
    # 查询关联故障
    relation_id_dict = get_rdc_relation_id_dict({"rdcIdent_list": rdc_params["rdcIdent_list"], "linkRelationName": "related", "relatedWorkItemTypeKey": "chgRequest"})
    rdc_fault_num_dict = get_rdc_fault_num_dict(relation_id_dict)
    # 查询关联MR
    relation_mr_dict = get_rdc_relation_id_dict({"rdcIdent_list": rdc_params["rdcIdent_list"], "linkRelationName": "father", "relatedWorkItemTypeKey": "MR"})
    rdc_to_mr_dict = {}
    for mr_id, rdc_id_list in relation_mr_dict.items():
        for rdc_id in rdc_id_list:
            rdc_to_mr_dict[rdc_id] = mr_id
    body_params = query_RDC(rdc_params)
    for item in body_params:
        item["related_fault_num"] = rdc_fault_num_dict.get(item.get("rdcIdent"), 0)
        item["related_parent_rdc"] = rdc_to_mr_dict.get(item.get("rdcIdent"), "")
    # 4 RDC状态更新到对应数据中
    # employ_no = '10164361'
    updateSrcBoardWholeStatusData(body_params, employ_no)
    # 5 根据查询到的变更请求查询故障详细数据并更新到数据表
    if len(board_tree) > 0:
        rdc_fault_param_list = build_rdc_fault_params(relation_id_dict, board_tree, employ_no)
        rdc_fault_data_list = []
        for rdc_fault_param_item in rdc_fault_param_list:
            rdc_fault_data_item = get_rdc_change_req_info_list(rdc_fault_param_item)
            rdc_fault_data_list += rdc_fault_data_item
        addRdcFaultTableData(rdc_fault_data_list)

    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": body_params})

# 变更分析数据更新
def update_to_global_status_list(features: List[Dict[str, str]], employ_no) -> List[Dict[str, str]]:
    """
    :param board_factor: 由 extract_board_global_status 得到的 4 字段字典
    :param features: 输入特性列表
    :return: 符合目标格式的 JSON 列表
    """
    results = []
    update_feature = [] 
    for item in features:
        if not item.get("feature"):
            continue
        feature_data = querySrcFeatureBoardRelation("", "", "", item.get("feature"))
        if len(feature_data) < 1:
            continue
        new_item = copy.deepcopy(item)
        new_item.update({
            "featureFirstType": feature_data[0].get("featureFirstType"),
            "featureSecondType": feature_data[0].get("featureSecondType")
        })
        if item.get("feature") and not item.get("subFeature"):
            new_item["changeAnalysis"] = "普通变更: 新增" + item.get("feature", "").split('-', 1)[-1].strip() + ";\n关键变更: "
            update_feature.append(new_item)
        results.append(new_item)
    
    # 仅更新 特性的变更分析
    updateSrcBoardWholeStatusData(update_feature, employ_no)
    return results
# 变更分析数据更新
def update_change_analysis_data():
    """
    更新变更分析数据
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户工号对应的token，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
          example:   # 示例值
            board: "xx1,xx2"
    responses:
      200:
        description: 更新变更分析数据
    """
    body_params = request.get_json()
    board_name = body_params.get('board', '')
    employ_no = request.headers.get('X-Emp-No')
    token = request.headers.get('X-Auth-Value')
    board_tree = get_product_factor_by_board(board_name)
    if len(board_tree) < 1:
        logger.error("--------单板数据不存在--------")
        return ""
    # 1 删除现有数据
    deleteChangeAnalysisData(board_name, employ_no)
    # 2 获取单板全局状态表信息
    query_params = {
        "board": board_name
    }
    feature_list = querySrcBoardWholeStatusByParams(query_params, markdown_flag= True)
    # 3 单板全局状态表添加"featureFirstType"和"featureSecondType"字段更新
    merged_list = update_to_global_status_list(feature_list, employ_no)
    # 4 更新单板全局状态表和变更分析结果表的变更分析
    results = board_format_change_analysis(board_tree, merged_list, employ_no)
     # 5 更新后的变更分析填写到RDC中
    rdc_fields = {"analysisReport":""}
    error_workItems = syncSrcBoardWholeStatusDataRDC(body_params, employ_no, token, rdc_fields)
    return jsonify({"code": 200, "status": "success", "message": "更新变更分析成功", "data": error_workItems})


def query_fault_list_by_feature():
    """
    查询某一特性/子特性下的所有故障
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: body 
        in: body 
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          required: [feature_name, children_feature_flag]
          properties:
            feature_name:
              type: string
              description: 特性/子特性名称
            children_feature_flag:
              type: string
              description: 是否是子特性, Y/N
          example:
            feature_name: "FS010222-01-E-灰光模块性能"
            children_feature_flag: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":[]}
    """
    body_params = request.get_json()
    feature_name = body_params.get('feature_name', '')
    children_feature_flag = body_params.get('children_feature_flag', '')
    field_name = "feature_name"
    if children_feature_flag == 'Y':
        field_name = "children_feature_name"
    board_whole_status_data_list = queryBoardWholeStatusByField(field_name, feature_name)
    rdc_ident_list = [item.get("related_rdc") for item in board_whole_status_data_list if item.get("related_rdc")]
    rdc_fault_list = queryRdcFaultListByRdcIdentList(rdc_ident_list)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": rdc_fault_list})


def query_rdc_list_by_board_name_and_preplan_version():
    """
    查询某单板在某里程碑下未交付/已交付的 RDC 需求列表
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，通过 JSON Body 提交查询条件
    parameters:
      - name: body
        in: body
        required: true
        description: 请求体参数（JSON 格式）
        schema:
          type: object
          properties:
            board_name:
              type: string
              description: 单板名称，支持多个值，用英文逗号分隔（例如："BoardA,BoardB"）。模糊匹配（包含即可）。
              example: "FS01,CloudServer"
            preplan_version:
              type: string
              description: 预规划版本号（related_requirement_preplanning_version），支持多个值，用英文逗号分隔。精确匹配。
              example: "智能OTN V3.00R1"
            rdc_status:
              type: string
              description: RDC 需求状态过滤条件。
                - `"support"`：仅返回"可交付"或"已支持"状态；
                - `"not_support"`：排除"可交付"、"已支持"、"已废弃"状态；
                - 空值或其他值：不过滤状态。
              enum: ["support", "not_support", ""]
              example: "support"
          example:
            board_name: "M5C4R"
            preplan_version: "智能OTN V3.00R1"
            rdc_status: "support"
    responses:
      200:
        description: 成功返回数据
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "获取成功"
            data:
              type: array
              items:
                type: object
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data": []}
    """
    try:
        body_params = request.get_json()
        if not isinstance(body_params, dict):
            body_params = {}

        board_name = body_params.get('board_name', '')
        preplan_version = body_params.get('preplan_version', '')
        rdc_status = body_params.get('rdc_status', '')

        rdc_list = queryBoardWholeStatusByBoardNameAndPreplanVersion(
            board_name=board_name,
            preplan_version=preplan_version,
            rdc_status=rdc_status
        )

        return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": rdc_list})
    except Exception as e:
        logger.info(f"Query RDC list failed: {e}")
        return jsonify({"code": 500,"status": "error","message": "查询失败","data": []}), 500

############################### 新增器件变更场景 #####################################

########################## 新增器件完成单板变更分析特性波及 ##########################
# 3.1 单板配置类型变更分析
def cfg_generate_change_analysis(board_name, cfg_type, features, employ_no):
    cfg_analysis = []

    config_types = split_multiline(cfg_type)
    cfg_analysis = generate_simple_add_analysis(config_types)
    features = [
        "F060101-E-业务单板-基础启动",
        "F060102-E-业务单板-基础管理"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, cfg_analysis, employ_no)

    return cfg_analysis

# 3.2 子架变更分析
def shelf_type_generate_change_analysis(board_name, shelf_type, features, employ_no):
    subracks = process_shelf_type_string(shelf_type)
    # F020601-背板带宽动态调整特性 和 F020602-背板性能告警特性 和 F020611-新增子架特性
    shelf_analysis = generate_simple_add_analysis_shelf(subracks)
    features = [
        "F020601-E-背板带宽动态调整",
        "F020602-E-背板性能告警", 
        "F020611-E-新增子架"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, shelf_analysis, employ_no)

    return shelf_analysis

# 3.3 物理端口数量变更分析
def port_generate_change_analysis(board_name, port_num, features, employ_no):
    ports = split_multiline(port_num)

    # F060101-E-业务单板-基础启动 和 F060102-业务单板-基础管理特性
    count_analysis = generate_simple_add_analysis_port(ports)
    features = [
        "F060101-E-业务单板-基础启动",
        "F060102-E-业务单板-基础管理"
    ]
    for item in features:
        change_analysis_to_global_st(board_name, item, count_analysis, employ_no)
    
    return count_analysis

# 3.4 控制逻辑变更分析        
def control_logic_generate_change_analysis(board_name, control_logic, features, employ_no):
    # 获取RDC状态的特性
    feature_key = "业务单板-基础启动"
    # FS060101-02-业务单板-基础启动-逻辑正常加载
    analysis = format_change_analysis_add(board_name, "控制逻辑", control_logic, feature_key)
    control_logic_analysis = '\n'.join(analysis)

    # F060101-E-业务单板-基础启动
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, control_logic_analysis, employ_no)

    return control_logic_analysis
 
# 3.5 gearbox变更分析 
def gearbox_generate_change_analysis(board_name, gearbox, features, employ_no):
    # 获取RDC状态的特性
    feature_key = "业务单板-基础启动"
    # FS060101-07-业务单板-基础启动-CDR芯片初始化
    analysis = format_change_analysis_add(board_name, "GEARBOX", gearbox, feature_key)
    gearbox_analysis = '\n'.join(analysis)

    # F060101-E-业务单板-基础启动 和 F020101-XX业务基础特性 XX:O/FG..
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, gearbox_analysis, employ_no)
    ele_feature = get_same_feature_by_global_class(features, "电层业务", "业务基础")
    for i in ele_feature:
        change_analysis_to_global_st(board_name, i.get("feature"), gearbox_analysis, employ_no)

    return gearbox_analysis

# 3.6 时钟芯片变更分析 
def timer_chip_generate_change_analysis(board_name, timer, features, employ_no):
    # 获取RDC状态的特性
    feature_key = "业务单板-基础启动"
    # FS060101-05-业务单板-基础启动-时钟芯片正常锁定
    analysis = format_change_analysis_add(board_name, "时钟芯片", timer, feature_key)
    timer_analysis = '\n'.join(analysis)

    # F060101-E-业务单板-基础启动 和 F020101-XX业务基础特性 XX:O/FG..
    feature = "F060101-E-业务单板-基础启动"
    change_analysis_to_global_st(board_name, feature, timer_analysis, employ_no)
    ele_feature = get_same_feature_by_global_class(features, "电层业务", "业务基础")
    for i in ele_feature:
        change_analysis_to_global_st(board_name, i.get("feature"), timer_analysis, employ_no)

    return timer_analysis

BLACKLIST = (
    "F050111-E-关键器件温度触发风扇调整",
    "F070133-E-业务单板-时间性能-光模升级加载+中断时间要求",
    "F070131-E-业务单板-时间性能-版本升级操作加载时间要求",
    "F070132-E-业务单板-时间性能-启动时间要求",
    "F050131-E-ODUk硬件异常保护",
    "F050132-E-单板硬件及接口类性能告警",
    "F070151-E-业务单板-定位定界-单板内存/CPU越限告警",
    "F070152-E-业务单板-定位定界-线卡复位原因记录",
    "F070153-E-业务单板-定位定界-安全通道故障诊断",
    "F070154-E-业务单板-定位定界-线卡标准日志",
    "F070155-E-业务单板-定位定界-日志转储",
    "F070156-E-业务单板-定位定界-单板报文记录(U口/S口/CTI报文等)",
    "F070157-E-业务单板-定位定界-Error_Info上报/Error_dump/Tid信令跟踪",
    "F070158-E-业务单板-定位定界-一键收割",
    "F070171-E-业务单板-能耗管理-能耗感知和优化",
    "F070181-E-业务单板-巡检-线路侧光模块巡检",
    "F080101-E-业务单板工装-基础启动",
    "F080102-E-业务单板工装-功能测试"
)

# 3.7 电层业务变更分析
def ele_svc_generate_change_analysis(board_name, c_svc, l_svc, features, employ_no) -> Dict[str, Any]:
    change_analysis = []
    analysis = []

    # O业务基础特性
    analysis = board_svc_mod_and_frm_change_add(board_name, "客户侧电层业务", c_svc, "单板部件", "业务FRM芯片")
    analysis_line = board_svc_mod_and_frm_change_add(board_name, "线路侧电层业务", l_svc,"单板部件", "业务FRM芯片")
    analysis.append('\n'.join(analysis_line))

    # 首次除光层业务、F020602-背板性能告警特性、F020611-新增子架特性外其他所有特性 和 非首次F060101-E-业务单板-基础启动
    other_features = get_other_feature_by_global_class(features, "光层业务")
    # 过滤掉blacklist中的特性子特性
    other_feature = filter_by_features(other_features, BLACKLIST)

    s = '\n'.join(analysis)
    for part in s.split("\n"):
        if "非首次使用" in part:
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
        else:
            for i in other_feature:
                if "F020602-E-背板性能告警" != i.get("feature") and "F020611-E-新增子架" != i.get("feature"):
                    change_analysis_to_global_st(board_name, i.get("feature"), part, employ_no)

    return analysis

# 3.8 单板业务模型变更分析 
def board_svc_generate_change_analysis(board_name, board_svc, features, employ_no) -> Dict[str, Any]:
    # XX业务交叉管理特性
    analysis = board_svc_mod_and_frm_change_add(board_name, "单板业务模型", board_svc, "单板部件", "交换FRM芯片")
    cross_analysis = '\n'.join(analysis)

    # 非首次: F060101-E-业务单板-基础启动 和 首次:F020106-XX业务交叉管理特性 XX:O/FG..
    ele_feature = get_same_feature_by_global_class(features, "电层业务", "业务交叉管理")
    for part in cross_analysis.split("\n"):
        if "非首次使用" in part:
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
        else:
            for i in ele_feature:
                change_analysis_to_global_st(board_name, i.get("feature"), part, employ_no)

    # XX业务基础特性
    analysis = board_svc_mod_and_frm_change_add(board_name, "单板业务模型", board_svc, "单板部件", "业务FRM芯片")
    # 首次除光层业务、F020602-背板性能告警特性、F020611-新增子架特性外其他所有特性 和 非首次F060101-E-业务单板-基础启动
    other_features = get_other_feature_by_global_class(features, "光层业务")
    # 过滤掉blacklist中的特性子特性
    other_feature = filter_by_features(other_features, BLACKLIST)   
    #首次除光层业务外其他所有特性 和 非首次F060101-E-业务单板-基础启动
    svc_analysis = '\n'.join(analysis)
    for part in svc_analysis.split("\n"):
        if "非首次使用" in part:
            feature = "F060101-E-业务单板-基础启动"
            change_analysis_to_global_st(board_name, feature, part, employ_no)
        else:
            for i in other_feature:
                change_analysis_to_global_st(board_name, i.get("feature"), part, employ_no)

    return analysis

# 3.9 开销逻辑变更分析
def oh_logic_generate_change_analysis(board_name, oh_type, features, employ_no) -> Dict[str, Any]:
    oh_types = oh_type.split(",")
    results = []
    for oh in oh_types:
        same_boards = get_boards_with_same_factor_val(board_name, "开销逻辑", oh)
        analysis = oh_logic_write_global_st(board_name, features, same_boards, oh, "高可用业务", employ_no)
        results.append(analysis)
        analysis = oh_logic_write_global_st(board_name, features, same_boards, oh, "扩展应用业务", employ_no)
        results.append(analysis)

    return results

def board_svc_frm_generate_change_analysis(board_name: str, svc_frm, features, employ_no) -> Optional[List[str]]:
    factor_vals2 = svc_frm.split(",")
    results = []
    feature_key = "O业务基础"
    # 遍历因子2的取值
    for val2 in factor_vals2:
        # 获取与因子1和因子2取值相同的单板数据
        same_boards = get_boards_with_same_factor_val(board_name, "业务FRM芯片", val2)
        #logger.info(same_boards)
        info = {
                "board": ",".join(sorted(same_boards)),
                "feature": feature_key,
                "requirementStatus": "可交付,已支持"
        }
        #logger.info(info)
        if same_boards and isBoardWholeStatusRDCByParams(info):
            results.append(f"新增-单板部件要素-业务FRM芯片因子[{val2}]-非首次使用; ")
        else:
            results.append(f"新增-单板部件要素-业务FRM芯片因子[{val2}]-首次使用; ")
    svc_analysis ='\n'.join(results)
    logger.info(f"--- svc_analysis:{svc_analysis} ----\n")
    for i in features:
        change_analysis_to_global_st(board_name, i.get("feature",""), svc_analysis, employ_no)

    return results

######################## 新增器件函数入口 ############################
def add_opt_mod_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    c_mod_type = add_board.get("客户侧光模块", "")
    l_mod_type = add_board.get("线路侧光模块", "")
    l_opt_svc = add_board.get("线路侧光层业务", "")
    mod_opt_svc = add_board.get("opt_biz_relation", "")
    mod_opt_svc = mod_opt_svc.get("add","")
    
    change_analysis = []
    analysis = []
    logger.info(f"---c_mod_type:{c_mod_type} l_mod_type:{l_mod_type}----\n")
    if not c_mod_type and not l_mod_type and not l_opt_svc and not mod_opt_svc:
        return [],[]
   
    if c_mod_type and l_mod_type:
        part_cont = '新增线路侧光模块,新增客户侧光模块'
    elif l_mod_type and ("CFP" not in l_mod_type):
        part_cont = '新增线路侧光模块'
    elif c_mod_type:
        part_cont = '新增客户侧光模块'
    else:
        part_cont = '新增线路侧光层业务'

    if l_opt_svc:
        part_cont = part_cont +',新增线路侧光层业务'
    else:
        part_cont = part_cont

    opt_features = querySrcFeatureChangeRelation(part_cont)
    opt_filter = filter_features_by_part(features, opt_features)
    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(opt_filter, employ_no)
    # 6 根据过滤后的特性完成变更波及分析
    if c_mod_type:
        analysis = client_opt_change_impact_analysis_rules(board_name, "客户侧光模块", c_mod_type, features, employ_no)
    # 线路侧sfp等按照灰光处理
    if l_mod_type:
        mod_type = str_to_list(l_mod_type)
        for mod_id in mod_type:
            if is_gray_optical_mod(mod_id):
                logger.info(f"------灰光模块--- mod_type:{mod_id} -----")
                analysis = line_gray_opt_change_impact_analysis_rules(board_name, mod_id, features, employ_no)
            elif is_cfp_optical_mod(mod_id):
                analysis = client_opt_change_impact_analysis_rules(board_name, "线路侧光模块", mod_id, features, employ_no)
            else:
                logger.info(f"------彩光模块--------")
                analysis = line_color_opt_change_impact_analysis_rules(board_name, mod_id, features, employ_no)
    # change_analysis["线路侧光层业务_线路侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)

    # 定义特征码列表
    feature_list = [
        "F030141-E-O业务光层保护-APSD模式OAC1+1保护",
        "F030143-E-O业务光层保护-普通OCH1+1保护"
    ]
    for item in opt_filter:
        # 使用 any() 和 for 循环检查是否包含任意一个特征码
        if any(feature in item.get('feature', '') for feature in feature_list):
            development_type = '验证性需求'
            reuse_degree = '零代码'
        elif "非首次" in analysis: 
            development_type = '存量单板-新增器件-非首次使用需求'
            reuse_degree = '配置化'
        else:
            development_type = '存量单板-新增器件-首次使用需求'
            reuse_degree = '微范式'
        change_development_type_to_global_st(board_name, item.get("feature",""), development_type, reuse_degree, employ_no)            

    return opt_filter, analysis

def add_opt_svc_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    c_opt_svc = add_board.get("客户侧光层业务", "")
    l_opt_svc = add_board.get("线路侧光层业务", "")
    mod_opt_svc = add_board.get("opt_biz_relation", "")
    change_analysis = []
    analysis = []
    logger.info(f"---c_opt_svc:{c_opt_svc} l_opt_svc:{l_opt_svc}--mod_opt_svc:{mod_opt_svc}--\n")
    if not c_opt_svc and not l_opt_svc and not mod_opt_svc:
        return [],[]
    if c_opt_svc and l_opt_svc:
        part_cont = '新增线路侧光层业务,新增客户侧光层业务'
    elif c_opt_svc:
        part_cont = '新增客户侧光层业务'
    else:
        part_cont = '新增线路侧光层业务'

    svc_features = querySrcFeatureChangeRelation(part_cont)
    svc_filter = filter_features_by_part(features, svc_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(svc_filter, employ_no)
    if c_opt_svc:
        analysis = client_opt_svc_change_impact_analysis_rules(board_name, c_opt_svc, svc_filter, employ_no)
        # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
        logger.info(analysis)

    # 线路侧sfp等按照灰光处理
    if l_opt_svc:
        analysis = line_opt_svc_change_impact_analysis_rules(board_name, l_opt_svc, svc_filter, employ_no)
        # change_analysis["线路侧光层业务_线路侧光模块变更分析"] = '\n'.join(analysis)
        logger.info(analysis)

    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in svc_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return svc_filter, analysis

def add_shelf_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_shelf = add_board.get("单板支持的子架", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_shelf: {add_shelf} ----\n")
    if not add_shelf:
        return [],[]

    part_cont = '新增子架适配'    
    features = filter_shelf_feature(add_board, features)
    shelf_features = querySrcFeatureChangeRelation(part_cont)
    shelf_filter = filter_features_by_part(features, shelf_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(shelf_filter, employ_no)
    analysis = shelf_type_generate_change_analysis(board_name, add_shelf, shelf_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)

    # 定义特征码列表
    feature_list = [
        "F040109-E-O业务DM双向时延测量",
        "F040114-E-O业务GCC-GFP协议电监控",
        "F040115-E-O业务GCC-HDLC协议电监控",
        "F040128-E-O业务带内时钟",
        "F040514-E-VC业务DCC电监控"
    ]

    for item in shelf_filter:
        # 使用 any() 和 for 循环检查是否包含任意一个特征码
        if any(feature in item.get('feature', '') for feature in feature_list):
            development_type = '子架回插需求'
            reuse_degree = '配置化'
        else:
            development_type = '验证性需求'
            reuse_degree = '零代码'
        change_development_type_to_global_st(board_name, item.get("feature",""), development_type, reuse_degree, employ_no)            

    return shelf_filter, analysis

def add_timer_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_timer = add_board.get("时钟芯片", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_timer: {add_timer} ----\n")
    if not add_timer:
        return [],[]

    part_cont = '新增时钟芯片'
    timer_features = querySrcFeatureChangeRelation(part_cont)
    timer_filter = filter_features_by_part(features, timer_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(timer_filter, employ_no)
    analysis = timer_chip_generate_change_analysis(board_name, add_timer, timer_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)

    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in timer_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return timer_filter, analysis

def add_cfg_type_generate_change_analysis(board_name, add_board, board_tree, features, body_params, head_employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("单板配置类型", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_cfg_type: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    development_type = '存量单板-新增功能需求'
    reuse_degree = '全代码'     
    if "中继配置类型" in add_cfg:
        l_mod = board_tree.get("线路侧光模块", "")
        l_svc = board_tree.get("线路侧电层业务", "")
        l_mod_type = extract_module_prefix_str(l_mod)

        board_factor = extract_board_global_status(add_board)
        part_cont = '新增中继类型' 
        cfg_features = querySrcFeatureChangeRelation(part_cont)

        filter_features = filter_details_features_by_board_type(board_tree, cfg_features, is_c_flag=False)

        merged_list = merge_to_global_status_list(board_factor, filter_features, head_employ_no)

        addSrcBoardWholeStatusData(merged_list, head_employ_no)
        analysis = cfg_generate_change_analysis(board_name, add_cfg, merged_list, head_employ_no)
        for i in merged_list:
            change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, head_employ_no)            

        split_rdc_flag = body_params.get('split_rdc_flag', '')
        if split_rdc_flag.upper() == "Y":
            global pr_rdc_info_table
            clear_pr_rdc_info_table()
            part = f"新增-中继配置类型"
            body_params['text'] = "-" + part
            employ_no = body_params.get('employ_no', '')
            body_params["employ_no"] = head_employ_no
            rdc_ret_val = rdc_relay_cfg_feature_splite_add(add_board, board_tree, merged_list, part, body_params, head_employ_no)
            body_params["employ_no"] = employ_no
            # 1 查询所有MR信息
            mr_tabel = querySrcMrFeatureByParams(markdown_flag=True)
            rdc_mr_traverse_split_by_pr(board_tree, mr_tabel, pr_rdc_info_table, l_svc, l_mod_type, body_params, head_employ_no)
        return "", analysis
    else:
        part_cont = '新增配置类型' 
        cfg_features = querySrcFeatureChangeRelation(part_cont)
        cfg_filter = filter_features_by_part(features, cfg_features)

        #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
        results = addSrcBoardWholeStatusData(cfg_filter, head_employ_no)
        analysis = cfg_generate_change_analysis(board_name, add_cfg, cfg_filter, head_employ_no)  
        for i in cfg_filter:
            change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, head_employ_no)
    logger.info(analysis)
    return cfg_filter, analysis

def add_ports_num_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("物理端口数量", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_ports_num: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    
    part_cont = '新增硬件子类型' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    port_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(port_filter, employ_no)
    analysis = port_generate_change_analysis(board_name, add_cfg, port_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)

    development_type = '新增单板-无新增器件及功能需求'
    reuse_degree = '配置化'    
    # 定义特征码列表
    for item in port_filter:
        change_development_type_to_global_st(board_name, item.get("feature",""), development_type, reuse_degree, employ_no)

    return port_filter, analysis

def add_gearbox_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("GEARBOX", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_gearbox: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    
    part_cont = '新增GEARBOX' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    gearbox_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(gearbox_filter, employ_no)
    analysis = gearbox_generate_change_analysis(board_name, add_cfg, gearbox_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in gearbox_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return gearbox_filter, analysis

def add_ctr_logic_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("控制逻辑", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_ctr_logic: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    
    part_cont = '新增控制逻辑' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    cfg_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(cfg_filter, employ_no)
    analysis = control_logic_generate_change_analysis(board_name, add_cfg, cfg_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in cfg_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return cfg_filter, analysis

def add_board_model_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("单板业务模型", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_board_model: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]

    part_cont = '业务FRM芯片_新增单板业务模型,交换FRM芯片_新增单板业务模型' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    cfg_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(cfg_filter, employ_no)
    analysis = board_svc_generate_change_analysis(board_name, add_cfg, cfg_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in cfg_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return cfg_filter, analysis

def add_ele_svc_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    c_add_cfg = add_board.get("客户侧电层业务", "")
    l_add_cfg = add_board.get("线路侧电层业务", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- c_add_ele_svc: {c_add_cfg}, l_add_ele_svc: {l_add_cfg} ----\n")
    if not c_add_cfg and not l_add_cfg:
        return [],[]
    
    part_cont = '业务FRM芯片_新增电层业务' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    cfg_filter = filter_features_by_part(features, cfg_features)

    logger.info(f"-luofeng--- cfg_features: {cfg_features}, cfg_features: {cfg_features} ----\n")
    logger.info(f"-luofeng--- cfg_filter: {cfg_filter}, cfg_filter: {cfg_filter} ----\n")


    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(cfg_filter, employ_no)
    analysis = ele_svc_generate_change_analysis(board_name, c_add_cfg, l_add_cfg, cfg_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in cfg_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return cfg_filter, analysis

def add_oh_logic_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("开销逻辑", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_oh_logic: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    
    part_cont = '新增开销逻辑' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    cfg_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(cfg_filter, employ_no)
    analysis = oh_logic_generate_change_analysis(board_name, add_cfg, cfg_filter, employ_no)
    # change_analysis["客户侧光层业务_客户侧光模块变更分析"] = '\n'.join(analysis)
    # logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in cfg_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            

    return cfg_filter, analysis

def add_svc_frm_generate_change_analysis(board_name, add_board, features, employ_no) -> Dict[str, Any]:
    add_cfg = add_board.get("业务FRM芯片", "")
    change_analysis = []
    analysis = []
    logger.info(f"---- add_svc_frm: {add_cfg} ----\n")
    if not add_cfg:
        return [],[]
    
    part_cont = '新增业务FRM芯片' 
    cfg_features = querySrcFeatureChangeRelation(part_cont)
    cfg_filter = filter_features_by_part(features, cfg_features)

    #5 过滤后的特性若全局状态表中没有则追加(保证全局状态表是完整的)
    results = addSrcBoardWholeStatusData(cfg_filter, employ_no)
    analysis = board_svc_frm_generate_change_analysis(board_name, add_cfg, cfg_filter, employ_no)
    # change_analysis["单板业务模型_业务FRM芯片变更分析"] = '\n'.join(analysis)
    # logger.info(analysis)
    if "非首次" in analysis:
        development_type = '存量单板-新增器件-非首次使用需求'
        reuse_degree = '配置化'
    else:
        development_type = '存量单板-新增器件-首次使用需求'
        reuse_degree = '微范式'
    for i in cfg_filter:
        change_development_type_to_global_st(board_name, i.get("feature",""), development_type, reuse_degree, employ_no)            
    return cfg_filter, analysis

########################## RDC拆分 #############################
def rdc_mod_type_splite_add(board_tree, mod_type, part, features_list, body_params, opt_svc_analysis:str=""):
    board_name = board_tree.get("board", "")
    mod_type = mod_type.split(',')
    if len(mod_type) < 1:
        return ""
    hd_sub = get_hd_sub_type_by_name(board_tree)
    cfp = extract_module_prefix(mod_type)
    
    sub_feature = get_opt_sub_feature_by_global_st(features_list, "彩光业务")
    rdc_ret_val = []
    part_list = str_to_list(part)
    for i in sub_feature:
        subfeature = i.get("subFeature")
        mod_name = add_board_suffix(cfp, subfeature +"-" + hd_sub)
        rdc_name = mod_type_and_svc_type_ortho_join(mod_name, part_list)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params, opt_svc_analysis)
    return rdc_ret_val

def rdc_package_type_splite_add(board_tree, mod_type, part, features, second_class, body_params):
    rdc_ret_val = []
    board_name = board_tree.get("board", "")
    mod_type = mod_type.split(',')
    if len(mod_type) < 1:
        return ""
    hd_sub = get_hd_sub_type_by_name(board_tree)
    part_list = str_to_list(part)
    # 获取灰光子特性列表（有的需要一对一，需进一步处理）单板模型对应的所有灰光特add_po性子特性
    sub_feature = get_opt_sub_feature_by_global_st(features, second_class)
    for i in sub_feature:
        subfeature = i.get("subFeature")
        # 组装RDC名称
        mod_name = add_board_suffix(mod_type, subfeature +"-" + hd_sub)
        rdc_name = mod_type_and_svc_type_ortho_join(mod_name, part_list)
        # 创建RDC并将数据回填到子特性中，多个时会拷贝创建
        rdc_ret_val = rdc_info_to_subfeature(board_name, features, rdc_name, i, body_params)

    return rdc_ret_val

def rdc_ele_svc_feature_splite_rules(board_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag:False):
    board_name = board_tree.get("board", '')
    employ_no = body_params.get('employ_no', '')

    logger.info(f"--rdc_ele_svc_feature_splite_rules-- cfg_type: {cfg_type}, svc: {svc}, part:{part}-----")

    if not cfg_type and not svc and not part:
        logger.info("cfg_type is null")
        return
    other_cfg_flag = True
    rdc_ret_val = []
    hd_sub = get_hd_sub_type_by_name(board_tree)
    sub_feature = get_ele_sub_feature_by_global_st(features_list) 
    if ("电层业务" not in part) and ("配置类型" not in part):
        for i in sub_feature:
            subfeature = i.get("subFeature")
            rdc_name = add_board_suffix_str(part, subfeature + "-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
        return rdc_ret_val
    rate_type = business_rate_classification(svc)
    # logger.info(f"sub_feature: {sub_feature}") 
    # logger.info(f"rate_type: {rate_type}")
    if not cfg_type:
        return handle_sub_features_update_board(board_tree, "", part, sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)
        #return handle_sub_features(board_tree, "", sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)

    for seg in cfg_type.split(","):
        seg = seg.strip()
        if "业务速率配置类型" in seg:
            rdc_ret_val += handle_sub_features_update_board(board_tree, seg, part, sub_feature, CfgScene.SVC_RATE, features_list, body_params, is_c_l_flag)
            #rdc_ret_val += handle_sub_features(board_tree, seg, sub_feature, CfgScene.SVC_RATE, features_list, body_params, is_c_l_flag)
            continue

        if "中继配置类型" in seg:
            continue
        #     board_factor = extract_board_global_status(board_tree)
        #     board_features = querySrcFeatureBoardRelation("MGR_L")
        #     filter_features = filter_details_features_by_board_type(board_tree, board_features, is_c_flag=False) 
        #     merged_list = merge_to_global_status_list(board_factor, filter_features, employ_no)
        #     addSrcBoardWholeStatusData(merged_list, employ_no)
        #     sub_feature = get_sub_feature_by_global_st(merged_list)
        #     rdc_ret_val = handle_sub_features_update_board(board_tree, seg, part, sub_feature, CfgScene.RELAY, merged_list, body_params, is_c_l_flag)
        #     continue

        if other_cfg_flag:
            other_cfg_flag = False
            rdc_ret_val += handle_sub_features_update_board(board_tree, "", part, sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)
            #rdc_ret_val += handle_sub_features(board_tree, "", sub_feature, CfgScene.OTHER, features_list, body_params, is_c_l_flag)
            continue
    return rdc_ret_val

def rdc_ele_svc_feature_splite_add(add_tree, board_tree, part, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board")
    # 增量
    add_cfg_type = add_tree.get("单板配置类型", "")
    add_scv_c = add_tree.get("客户侧电层业务", "")
    add_scv_l = add_tree.get("线路侧电层业务", "")
    # 存量
    cfg_type = board_tree.get("单板配置类型", "")
    scv_c = board_tree.get("客户侧电层业务", "")
    scv_l = board_tree.get("线路侧电层业务", "")

    if not add_cfg_type and not add_scv_c and not add_scv_l:  #配置类型、业务类型都没有新增
        cfg_type = ""
        svc = ""
        # logger.info(f"-------features_list:{features_list}")
        return rdc_ele_svc_feature_splite_rules(add_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag)
    elif not add_scv_c and not add_scv_l:    #只新增配置类型， 业务类型没有新增---基本上不会出现
        cfg_type = add_cfg_type
        svc = scv_c + "," + scv_l
        return rdc_ele_svc_feature_splite_rules(add_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag)
    elif not add_cfg_type:   #配置类型没有新增， 业务类型有新增-
        cfg_type = cfg_type
        svc = add_scv_c + "," + add_scv_l
        return rdc_ele_svc_feature_splite_rules(add_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag)
    else:  #配置类型和业务类型同时新增 ---只考虑增量的组合就行，不需要考虑全量的内容
        # 配置类型增量 与 业务全量(增量+存量)
        # cfg_type = add_cfg_type
        # svc = add_scv_c + "," + add_scv_l + "," + scv_c + "," + scv_l
        # rdc_ele_svc_feature_splite_rules(add_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag)

        # 配置类型存量 与 业务增量
        cfg_type = add_cfg_type
        svc = add_scv_c + "," + add_scv_l
        return rdc_ele_svc_feature_splite_rules(add_tree, cfg_type, svc, part, features_list, body_params, is_c_l_flag)

def rdc_bp_svc_feature_splite_add(board_tree, part, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board", "")   
    hd_sub = get_hd_sub_type_by_name(board_tree)
    sub_feature = get_bp_sub_feature_by_global_st(features_list)
    rdc_ret_val = []
    for i in sub_feature:
        subfeature = i.get("subFeature")
        if "子架" in part:
            shelf_type = str_to_list(part)
            if "FS020601-01" in subfeature:
                shelf_type = filter_shelf_type_patterns(shelf_type, 'G2', 'G2-E')
            if "FS020601-02" in subfeature:
                shelf_type = filter_shelf_type_patterns(shelf_type, 'M1S3F', 'M1S3F-E')
            if "FS020601-03" in subfeature:
                shelf_type = filter_shelf_type_patterns(shelf_type, 'M2S3F-E(B)', 'M2S3F-E(FB)', 'M2S3F-E(B|FB)') 
            if "FS020601-11" in subfeature:   
                rdc_name = subfeature + "-" + hd_sub  
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, [rdc_name], i, body_params)
                continue 
            if "FS020611-04" in subfeature:
                shelf_type = filter_shelf_type_patterns(shelf_type, 'M2S3F-E(B)', 'M2S3F-E(FB)', 'M2S3F-E(B|FB)')     
            if len(shelf_type) < 1:
                continue
            rdc_name = add_board_suffix(shelf_type, subfeature + "-" + hd_sub)
        else:
            rdc_name = add_board_suffix_str(part, subfeature + "-" + hd_sub)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def rdc_relay_cfg_feature_splite_add(add_tree, board_tree, features_list, part, body_params, head_employ_no):
    board_name = add_tree.get("board", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    sub_feature = get_sub_feature_by_global_st(features_list)
    rdc_ret_val = []
    for i in sub_feature:
        subfeature = i.get("subFeature")
        rdc_name = add_board_suffix_str(part, subfeature + "-" + hd_sub)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def rdc_other_feature_splite_add(board_tree, first, part, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    sub_feature = get_feature_by_global_st_class(features_list, first)
    rdc_ret_val = []
    for i in sub_feature:
        subfeature = i.get("subFeature")
        rdc_name = add_board_suffix_str(part, subfeature + "-" + hd_sub)
        rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    return rdc_ret_val

def rdc_workwear_feature_splite_add(board_tree, features_list, part, body_params, is_c_l_flag):
    board_name = board_tree.get("board", "")
    c_mod_type = board_tree.get("客户侧光模块", "")
    mod_type = board_tree.get("线路侧光模块", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    sub_feature = get_feature_by_global_st_class(features_list, "工装可生产性")
    rdc_ret_val = []
    part_c = add_prefix_suffix(board_tree, "客户侧光模块")
    part_l = add_prefix_suffix(board_tree, "线路侧光模块")
    for i in sub_feature:
        subfeature = i.get("subFeature")
        if c_mod_type and "灰光模块" in subfeature:
            rdc_name = add_board_suffix_str(part_c, subfeature + "-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
            continue
        if mod_type and "彩光模块" in subfeature:
            rdc_name = add_board_suffix_str(part_l, subfeature + "-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
            continue
        if "灰光模块" not in subfeature and "彩光模块" not in subfeature:
            if len(part_c) < 1 and len(part_l) < 1:
                rdc_name = [subfeature + "_" + hd_sub + "_" + part]
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)            
            if len(part_c) > 0:
                rdc_name = add_board_suffix_str(part_c, subfeature + "-" + hd_sub)
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
            if len(part_l) > 0:
                rdc_name = add_board_suffix_str(part_l, subfeature + "-" + hd_sub)
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
            continue

    return rdc_ret_val

def rdc_mod_type_splite_color_rules(add_tree, board_tree, c_mod_type, l_mod_type, c_svc, l_svc, features_list, body_params, is_c_l_flag):
    rdc_ret_val = []
    board_name = add_tree.get("board", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    
    if not l_mod_type and not c_mod_type:
        return rdc_ret_val
    if l_mod_type:
        part_l = add_prefix_suffix(add_tree, "光模块")
        rate_type = business_rate_classification(l_svc)
        mod_type = str_to_list(l_mod_type)
        for mod_id in mod_type:
            if is_gray_optical_mod(mod_id):
                mod_cfp = get_package_types(mod_id)
                cfp = extract_cfp_code_left(mod_cfp)
                sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)
            elif is_cfp_optical_mod(mod_id):
                # cfp = str_to_list(mod_id)
                # rdc_name = add_board_suffix_str(part_l, subfeature + "-" + hd_sub)
                # mod_cfp = get_package_types(mod_id)
                # cfp = extract_cfp_code_left(mod_cfp) 
                sub_feature = get_sub_feature_by_global_st_color("灰光业务基础", features_list)
            else:
                cfp = extract_module_prefix_str(mod_id)
                sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)
            for i in sub_feature:
                subfeature = i.get("subFeature")
                if "彩光业务-低温冷启动" in subfeature:
                    rdc = add_board_suffix_str(subfeature, hd_sub)
                else:
                    rdc = add_board_suffix(rate_type, subfeature +"-" + hd_sub)
                # rdc_name = mod_type_and_svc_type_ortho_join(rdc, cfp)
                rdc_name = add_board_suffix_str(part_l, rdc)
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
    if c_mod_type:
        rdc_ret_val = rdc_client_mod_type_splite_color(board_name, c_mod_type, hd_sub, c_svc, features_list, body_params)

    return rdc_ret_val

# 线路侧模块模块简称的rdc
def rdc_mod_type_splite_color_add(add_tree, board_tree, part, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board","")
    # 增量
    add_c_mod = add_tree.get("客户侧光模块","")
    add_l_mod = add_tree.get("线路侧光模块","")
    add_scv_c = add_tree.get("客户侧电层业务","")
    add_scv_l = add_tree.get("线路侧电层业务","")
    # 存量
    c_mod = board_tree.get("客户侧光模块","")
    l_mod = board_tree.get("线路侧光模块","")
    scv_c = board_tree.get("客户侧电层业务","")
    scv_l = board_tree.get("线路侧电层业务","")

    if not add_c_mod and not add_l_mod and not add_scv_c and not add_scv_l:
        return ""
    elif (add_c_mod or add_l_mod) and (not add_scv_c and not add_scv_l):
        c_mod_type = add_c_mod
        l_mod_type = add_l_mod
        svc = scv_c + "," + scv_l
        return rdc_mod_type_splite_color_rules(add_tree, board_tree, c_mod_type, l_mod_type, scv_c, scv_l, features_list, body_params, is_c_l_flag)
    elif (add_scv_c or add_scv_l) and (not add_c_mod and not add_l_mod):
        c_mod_type = c_mod
        l_mod_type = l_mod
        svc = add_scv_c + "," + add_scv_l
        return rdc_mod_type_splite_color_rules(add_tree, board_tree, c_mod_type, l_mod_type, add_scv_c, add_scv_l, features_list, body_params, is_c_l_flag)
    else:
        # 光模块增量 与 业务全量(增量+存量)
        c_mod_type = add_c_mod
        l_mod_type = add_l_mod
        c_svc = add_scv_c + "," + scv_c
        l_svc = add_scv_l + "," + scv_l
        rdc_mod_type_splite_color_rules(add_tree, board_tree, c_mod_type, l_mod_type, c_svc, l_svc, features_list, body_params, is_c_l_flag)

        # 配置类型存量 与 业务增量
        c_mod_type = c_mod
        l_mod_type = l_mod
        svc = add_scv_c + "," + add_scv_l
        return rdc_mod_type_splite_color_rules(add_tree, board_tree, c_mod_type, l_mod_type, add_scv_c, add_scv_l, features_list, body_params, is_c_l_flag)

def rdc_opt_svc_and_mod_splite_add(add_tree, board_tree, part, features, body_params, is_c_l_flag):
    rdc_ret_val = []
    board_name = board_tree.get("board", "")
    hd_sub = get_hd_sub_type_by_name(board_tree)
       
    #logger.info(f"-------rdc_opt_svc_and_mod_splite_add: board_tree{board_tree}---------")
    logger.info(f"-------rdc_opt_svc_and_mod_splite_add: hd_sub{hd_sub}---------")

    # 新增光层也要波及
    add_c_mod = add_tree.get("客户侧光模块", "")
    # add_c_scv = add_tree.get("客户侧光层业务", "")
    add_l_mod = add_tree.get("线路侧光模块", "")
    add_l_scv = add_tree.get("线路侧光层业务", "")

    c_mod = board_tree.get("客户侧光模块", "")
    
    mod_opt_svc = add_tree.get("opt_biz_relation", "")
    mod_opt_svc = mod_opt_svc.get("add","")
    if not mod_opt_svc and not add_c_mod:
        sub_feature = get_opt_sub_feature_by_global_st(features, "灰光业务")
        sub_feature += get_opt_sub_feature_by_global_st(features, "彩光业务")
        for i in sub_feature:
            subfeature = i.get("subFeature")
            rdc_name = add_board_suffix_str(part, subfeature +"-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features, rdc_name, i, body_params)
        return rdc_ret_val

    if add_c_mod:
        text_c = add_prefix_suffix(add_tree, "客户侧光模块")
        rdc_package_type_splite_add(add_tree, "", text_c, features, "灰光业务", body_params)

    # if add_c_scv:
    #     text_c = add_prefix_suffix(add_tree, "客户侧光层业务")
    #     rdc_package_type_splite_add(add_tree, c_mod, text_c, features, "灰光业务", body_params)   
    
    opt_nums = get_unique_opt_list(mod_opt_svc)
    if len(opt_nums) < 0:
        return rdc_ret_val
    for mod_id in opt_nums:
        svc_type = get_biz_by_opt(mod_id, mod_opt_svc)
        if mod_id in add_l_mod:
            mod_type = f'新增-{mod_id}-光模块'
            text_l = ""
            analysis = f'新增-{svc_type}-光层业务'
            if is_gray_optical_mod(mod_id):
                logger.info("---------is 线路侧 灰光---------")
                rdc_package_type_splite_add(add_tree, mod_type, text_l, features, "彩光业务", body_params)
            elif is_cfp_optical_mod(mod_id):
                rdc_package_type_splite_add(add_tree, mod_type, text_l, features, "灰光业务", body_params)
            else:
                logger.info(f"---------is 线路侧{mod_id}---------")
                rdc_mod_type_splite_add(add_tree, mod_type, text_l, features, body_params, analysis)

        else:
            for svc_id in svc_type:
                mod_type = mod_id
                text_l = f'新增-{svc_id}-光层业务' 
                analysis = text_l    
                if is_gray_optical_mod(mod_id):
                    logger.info("---------is 线路侧 灰光---------")
                    rdc_package_type_splite_add(add_tree, mod_type, text_l, features, "彩光业务", body_params)
                elif is_cfp_optical_mod(mod_id):
                    rdc_package_type_splite_add(add_tree, mod_type, text_l, features, "灰光业务", body_params)
                else:
                    logger.info(f"---------is 线路侧{mod_id}---------")
                    rdc_mod_type_splite_add(add_tree, mod_type, text_l, features, body_params, analysis)


def rdc_opt_svc_splite_add(add_tree, board_tree, part, features_list, body_params, is_c_l_flag):
    board_name = board_tree.get("board","")
    # 增量
    add_l_mod = add_tree.get("线路侧光模块","")
    add_c_mod = board_tree.get("客户侧光模块","")
    add_scv_c = add_tree.get("客户侧光层业务","")

    rdc_ret_val = []
    hd_sub = get_hd_sub_type_by_name(board_tree)
    text_c = add_prefix_suffix(add_tree, "客户侧光层业务")

    mod_opt_svc = add_tree.get("opt_biz_relation", "")
    mod_opt_svc = mod_opt_svc.get("add","")
    
    logger.info(f"--luofeng-------mod_opt_svc{mod_opt_svc}---------")

    if not mod_opt_svc and not add_c_mod:
        sub_feature = get_opt_sub_feature_by_global_st(features_list, "彩光业务基础")
        sub_feature += get_opt_sub_feature_by_global_st(features_list, "灰光业务基础")

        logger.info(f"--luofeng-------sub_feature{sub_feature}---------")

        for i in sub_feature:
            subfeature = i.get("subFeature")
            rdc_name = add_board_suffix_str(part, subfeature +"-" + hd_sub)
            rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params)
        return rdc_ret_val

    # if add_scv_c:
    #     rdc_ret_val = rdc_client_mod_type_splite_color(board_name, c_mod_type, hd_sub, c_svc, features_list, body_params)

    opt_nums = get_unique_opt_list(mod_opt_svc)
    if len(opt_nums) < 0:
        return rdc_ret_val
    
    for mod_id in opt_nums:
        if is_gray_optical_mod(mod_id):
            mod_cfp = get_package_types(mod_id)
            cfp = extract_cfp_code_left(mod_cfp)
            sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)
        elif is_cfp_optical_mod(mod_id):
            mod_cfp = get_package_types(mod_id)
            cfp = extract_cfp_code_left(mod_cfp)
            sub_feature = get_sub_feature_by_global_st_color("灰光业务基础", features_list)
        else:
            cfp = extract_module_prefix_str(mod_id)
            sub_feature = get_sub_feature_by_global_st_color("彩光业务基础", features_list)

        svc_type = get_biz_by_opt(mod_id, mod_opt_svc)
        if mod_id in add_l_mod:
            mod_type = f'新增-{cfp[0]}-光模块'
            text_l = []
            analysis = f'新增-{svc_type}-光层业务'
            for i in sub_feature:
                subfeature = i.get("subFeature")
                if "彩光业务-低温冷启动" in subfeature:
                    continue
                else:
                    rdc = add_board_suffix_str(mod_type, subfeature +"-" + hd_sub)
                rdc_name = mod_type_and_svc_type_ortho_join(rdc, text_l)
                rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params, analysis)
        else:
            for svc_id in svc_type:
                mod_type = mod_id
                text_l = [f'新增-{svc_id}-光层业务']
                analysis = f'新增-{svc_id}-光层业务'
                for i in sub_feature:
                    subfeature = i.get("subFeature")
                    if "彩光业务-低温冷启动" in subfeature:
                        continue
                    else:
                        rdc = add_board_suffix_str(mod_type, subfeature +"-" + hd_sub)
                    rdc_name = mod_type_and_svc_type_ortho_join(rdc, text_l)
                    rdc_ret_val = rdc_info_to_subfeature(board_name, features_list, rdc_name, i, body_params, analysis)
            


    return rdc_ret_val

# 根据光模块获取新增映射业务类型
def get_biz_by_opt(target_opt: str, records: List[Dict[str, str]]) -> List[str]:
    """
    根据 opt 字段精确匹配，返回对应 biz 字段值组成的列表（保持原顺序）。
    """
    return [r['biz'] for r in records if r.get('opt') == target_opt]

def get_opt_by_biz(target_biz: str, records: List[Dict[str, str]]) -> List[str]:
    """
    根据 biz 字段精确匹配，返回对应 opt 字段值组成的列表（保持原顺序）。
    """
    return [r['opt'] for r in records if r.get('biz') == target_biz]

def get_unique_opt_list(records: List[Dict[str, str]]) -> List[str]:
    """
    按出现顺序去重，返回 biz 值列表
    """
    seen = dict.fromkeys(r.get('opt') for r in records if r.get('opt'))
    return list(seen)

# rdc拆分总入口
def rdc_add_board_whole_st_data_add(add_tree, board_tree, part, features, body_params, head_employ_no):
    split_rdc_flag = body_params.get('split_rdc_flag', '')
    if split_rdc_flag.upper() != "Y":
        return ""
    body_params["employ_no"] = head_employ_no
    board_type = board_tree.get("板卡类型", "")
    is_c_l_flag = False
    if "支线路合一" in board_type or "桥接B" in board_type:
        is_c_l_flag = True
    rdc_opt_svc_and_mod_splite_add(add_tree, board_tree, part, features, body_params, is_c_l_flag)
    rdc_opt_svc_splite_add(add_tree, board_tree, part, features, body_params, is_c_l_flag)
    rdc_mod_type_splite_color_add(add_tree, board_tree, part, features, body_params, is_c_l_flag)
    rdc_ele_svc_feature_splite_add(add_tree, board_tree, part, features, body_params, is_c_l_flag)
    rdc_bp_svc_feature_splite_add(add_tree, part, features, body_params, is_c_l_flag)
    rdc_other_feature_splite_add(add_tree, "单板基础启动管理", part, features, body_params, is_c_l_flag)
    rdc_other_feature_splite_add(add_tree, "高可靠性", part, features, body_params, is_c_l_flag)
    rdc_other_feature_splite_add(add_tree, "可维可服", part, features, body_params, is_c_l_flag)
    rdc_workwear_feature_splite_add(add_tree, features, part, body_params, is_c_l_flag)

    return

# 定义全局变量并初始化
factor_values: List[str] = []

def get_factor_val_by_input() -> List[str]:
    return factor_values

def set_factor_val_by_input(values: List[str]):
    global factor_values
    factor_values = values

def get_feature_tuple(item: Dict[str, Any]) -> tuple:
    """从字典中提取(feature, subFeature)元组，处理缺失键和None值"""
    feature = item.get('feature') or ''
    sub_feature = item.get('subFeature') or ''
    return (feature, sub_feature)

def filter_features_by_part(board_features: List[Dict[str, Any]], part_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 从board_features和part_features中提取所有(feature, subFeature)组合，分别形成集合
    board_list = {get_feature_tuple(item) for item in board_features}
    part_list = {get_feature_tuple(item) for item in part_features}
    
    # 计算交集（仅获取共同的特征组合）
    intersection = board_list & part_list
    
    # 将交集转换回列表格式（从board_features中获取完整的字典条目）
    result = [
        item for item in board_features
        if get_feature_tuple(item) in intersection
    ]
    
    return result

##### 获取存量硬件树数据 #####
def filter_board_tree_clear_values(add_board: Dict[str, Any], board_tree: Dict[str, Any]) -> Dict[str, Any]:
    """
    按照add_board中非空取值项进行过滤，排除board项。
    过滤后若值相同，则保留key但value设为空字符串。
    
    参数:
        add_board: 新增板卡字典
        board_tree: 板卡树字典
        
    返回:
        过滤后的board_tree
    """
    # 深拷贝board_tree，避免修改原数据
    filtered_tree = copy.deepcopy(board_tree)
    # 预先保存board和product的原始值，确保最终输出绝对不变
    original_protected_values = {
        'board': filtered_tree.get('board'),
        'product': filtered_tree.get('product'),
        'boardType': filtered_tree.get('boardType')
    }    
    # 遍历add_board中的所有键值对
    for key, add_value in add_board.items():
        # 排除board项
        if key == 'board':
            continue
        
        # 只处理add_board中非空的值
        if not add_value:  # 空字符串、None、[]等都视为空
            continue
        
        # 如果key不存在于board_tree中，跳过
        if key not in filtered_tree:
            continue
        
        tree_value = filtered_tree[key]
        
        # 如果值相同（无论类型），则将filtered_tree中的值设为空字符串
        if _values_are_equal(add_value, tree_value):
            filtered_tree[key] = ''  # 保留key，value设为空

    for key, original_value in original_protected_values.items():
        filtered_tree[key] = original_value

    return filtered_tree

def _values_are_equal(val1: Any, val2: Any) -> bool:
    """
    比较两个值是否相等，特别处理字符串和datetime类型
    """
    # 处理None值
    if val1 is None and val2 is None:
        return True
    if val1 is None or val2 is None:
        return False

    # 处理字符串类型（包括逗号分隔的列表字符串）
    if isinstance(val1, str) and isinstance(val2, str):
        return _compare_string_values(val1, val2)
    
    # 其他类型直接比较
    return val1 == val2

def _compare_string_values(str1: str, str2: str) -> bool:
    """
    比较两个字符串值，如果包含逗号则按集合比较（忽略顺序和空白）
    """
    # 去除首尾空白
    str1_clean = str1.strip()
    str2_clean = str2.strip()
    
    # 如果不包含逗号，直接比较
    if ',' not in str1_clean and ',' not in str2_clean:
        return str1_clean == str2_clean
    
    # 按逗号分割成列表，去除每个元素的空白，过滤空字符串
    list1 = [item.strip() for item in str1_clean.split(',') if item.strip()]
    list2 = [item.strip() for item in str2_clean.split(',') if item.strip()]
    
    # 按集合比较（忽略顺序）
    return set(list1) == set(list2)
    
# 增加后缀
def add_prefix_suffix(add_board, suffix:str) -> str:
    """
    将形如 '奥拉_AU5327,新港海岸_NCS23347' 的字符串
    转换为 '新增奥拉_AU5327时钟芯片,新增新港海岸_NCS23347时钟芯片'
    """
    if not suffix:          # 空串直接返回
        return ''
    raw = add_board.get(suffix, "")
    if "子架" in suffix:
        suffix = "子架"
        shelf = process_shelf_type_string(raw)
        raw = ','.join(shelf)
    if "端口数量" in suffix:
        suffix = "硬件子类型"
        tmp = re.sub(r'\d+', lambda m: f'x{m.group()}', raw)
        # 提取所有 xN 片段
        raw = ','.join(re.findall(r'x\d+', tmp))
    if "光模块" in suffix:
        suffix = "光模块"
    if "业务FRM" in suffix:
        suffix = "芯片"
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    return ','.join(f'新增-{part}-{suffix}' for part in parts)

def merge_board_info(add_board: dict, extit: dict) -> dict:
    """
    将 extit 中的 '板卡类型' 和 '产品' 字段拷贝到 add_board 中。
    
    参数:
        add_board (dict): 目标字典，待补充字段
        extit (dict): 源字典，提供需要拷贝的字段
    
    返回:
        dict: 更新后的 add_board
    """
    # 拷贝指定字段
    add_board["板卡类型"] = extit.get("板卡类型", "")
    add_board["产品"] = extit.get("产品", "")
    return add_board

def rdc_info_to_other_domain_by_mr(board_name, mr_id, body_params, head_employ_no):
    employ_no = body_params.get("employ_no", "")
    rdc_params = {}
    rdc_params["employ_no"] = employ_no
    rdc_params["rdcIdent_list"] = [mr_id]
    rdc_params["workItemType_list"] = "MR"
    body_data = query_RDC(rdc_params)

    rdc_name = body_data[0].get("rdcTitle","")
    if len(rdc_name) < 1:
        return []
    mr_flag = rdc_name.split('-')[0]

    src_depend_domain = body_data[0].get("depend_domain","")

    if not src_depend_domain:
        return []

    # depend_domain = [
    #     item['baseDataValue']['property']['Property_Name'] 
    #     for item in src_depend_domain 
    #     if item['baseDataValue']['property']['Property_Name'] != '02-L1'
    # ]
    depend_domain = []
    for item in src_depend_domain:
        if "baseDataValue" in item:
            tmp_depend_domain = item['baseDataValue']['property']['Property_Name']
            if tmp_depend_domain != '02-L1':
                depend_domain.append(tmp_depend_domain)
             

    if len(depend_domain) < 1:
        return []

    src_belongProduct = body_data[0].get("belongProduct","")
    belongProduct = src_belongProduct.get('value')
    
    specificationByExampleUrl = body_data[0].get("specificationByExampleUrl","")
    board_design_url = body_data[0].get("designSpecificationUrl","")
    description = body_data[0].get("description","")
    accept_criteria = body_data[0].get("acceptanceCriteria", "")
    requirementPrePlanning = body_data[0].get("productRoadmap", "")

    logger.info(f"----------requirementPrePlanning:{requirementPrePlanning}\n")

    results = []
    #description = "描述"
    criteria = "验收准则"
    requirementCategory = "01-基本需求"
    verificationTeam = "系统测试"

    # 添加空值检查
    if accept_criteria:
        # 在特定字段前添加换行符
        fields_to_add_br = ["GIVEN:", "WHEN:", "F0", "THEN:"]
        for field in fields_to_add_br:
            if field in accept_criteria:
                # 在字段前添加换行符
                accept_criteria = accept_criteria.replace(field, f"<br>{field}")   

    for idx in depend_domain:
        record = RDC_TABLE.copy()
        record["rdc_title"] = str(rdc_name + '-'+idx.split("-", 1)[1] )
        record["employ_no"] = str(head_employ_no)
        record["description"] = str(description)
        record["acceptance_criteria"] = accept_criteria
        record["featureContentLink"] = ""
        #新增字段
        record["belong_domain"] = str(idx) 
        record["belongProduct"] = str(belongProduct)
        record["requirementPrePlanning"] = str(requirementPrePlanning)
        record["specificationByExampleUrl"] = str(specificationByExampleUrl)
        record["designSpecificationUrl"] = str(board_design_url)
        record["requirementPurpose"] = "01-商用"
        record["priority"] = "5"
        record["requirementCategory"] = requirementCategory
        record["belongFeatureCatalog"] = "03-非标"
        record["requirementType"] = "01-功能需求"
        record["verificationMode"] = "测试"
        record["verificationTeam"] = verificationTeam
        record["changeAnalysis"] = "analysis"
        record["partName"] = str(board_name)
        results.append(record)
        logger.info(f"--other rdc_name:{record['rdc_title']}\n")
    # logger.info(f"----------results:{results}\n")
    rdc_info, permission_flag = create_RDC(results, body_params.get("task_id"))
    if not permission_flag:
        for handler in logger.handlers:
            handler.flush()
        return
    time.sleep(request_interval)
    body = build_link_body(mr_id, rdc_info)
    update_RDC_relatedWorkItemId(body, head_employ_no)  
    logger.info("--------rdc_info_to_global_map执行完成")
    for handler in logger.handlers:
        handler.flush()

def get_rdc_info_from_related_mr(mr_id, employ_no):
    rdc_params = {}
    rdc_params["employ_no"] = employ_no
    rdc_params["rdcIdent_list"] = [mr_id]
    rdc_params["workItemType_list"] = "MR"

    body_data = query_RDC(rdc_params)

    # 如果没有查询到数据，返回空列表
    if not body_data or len(body_data) == 0:
        return []

    rdc_name = body_data[0].get("rdcTitle","")     #MR标题
    if len(rdc_name) < 1:
        return []

    mr_flag = rdc_name.split('-')[0]
    
    specificationByExampleUrl = body_data[0].get("specificationByExampleUrl","")  #MR需求实例化链接
    board_design_url = body_data[0].get("designSpecificationUrl","")              #MR方案链接
    requirementPrePlanning = body_data[0].get("productRoadmap", "")               #MR产品路标

    # 构建返回的MR信息字典
    mr_info = {
        "mr_title": rdc_name,                       # MR标题
        "specification_by_example_url": specificationByExampleUrl,  # MR需求实例化链接
        "board_design_url": board_design_url,       # MR方案链接
        "requirement_pre_planning": requirementPrePlanning  # MR产品路标
    }
    
    # 返回包含MR信息的列表
    return [mr_info]
 
                
# 新增光模块变更分析数据更新
def add_new_part_update_change_analysis_data():
    """
    更新光模块变更分析数据
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户工号对应的token，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
            mr_ident:
              type: string
              description: mr标识
          example:   # 示例值
            board: "xx1,xx2"
            mr_ident: "OTNSW-83259"
    responses:
      200:
        description: 更新变更分析数据
    """
    head_employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    logger.info(f"-------body_params:{body_params}")
    start_time = datetime.datetime.now()
    logger.info(f'--------start_time:{start_time.strftime("%Y-%m-%d %H:%M:%S")}')
    task_id = str(uuid.uuid4())
    task_info_dict = {}
    task_info_dict["employ_no"] = head_employ_no
    task_info_dict["employ_name"] = pub_get_employ_name(head_employ_no)
    task_info_dict["task_type"] = "变更单板"
    task_info_dict["task_param"] = body_params
    task_info_dict["task_status"] = "pending"
    task_info_dict["task_start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_task_info_dict(task_id, task_info_dict)
    thread = threading.Thread(target=src_add_new_part_update_change_analysis_data, args=[body_params, head_employ_no, task_id])
    thread.daemon = False
    thread.start()

    return jsonify({"code": 200, "status": "success", "message": "进程启动，请根据返回的task_id调用get_task_result接口获取最终的执行结果", "data": [task_id]})


def src_add_new_part_update_change_analysis_data(body_params, head_employ_no, task_id):
    body_params["task_id"] = task_id
    # 因为前端已修改，但后端未修改，所以临时规避，后期删除
    if not body_params.get("employ_no"):
        body_params["employ_no"] = head_employ_no
    board_name = body_params.get('board', '')
    mr_employ_no = body_params["employ_no"]
    split_rdc_flag = body_params.get('split_rdc_flag', '')
    body_params['text'] = ""
    mr_ident = body_params.get('mr_ident', '')
    
    from app import app
    with app.app_context():
        try:
            board_tree = get_product_factor_by_board(board_name)
            if len(board_tree) < 1:
                logger.error("--------单板数据不存在--------")
                task_info_dict = {
                    "task_status": "completed",
                    "task_err_reason": '单板数据不存在',
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)
                return jsonify({"code": 404, "status": "error", "message": "单板数据不存在", "data": "单板数据不存在"})

            related_mr_info = []
            if mr_ident:
                related_mr_info = get_rdc_info_from_related_mr(mr_ident, head_employ_no)

                if len(related_mr_info) > 0:
                    body_params["requirementPrePlanning"] = related_mr_info[0].get("requirement_pre_planning","")
                    body_params["specificationByExampleUrl"] = related_mr_info[0].get("specification_by_example_url","")

            if not body_params.get("designSpecificationUrl", ""):
                body_params["designSpecificationUrl"] = query_board_tree_board_design_url_by_board_name(board_name)

            # 1 获取新增模块列表,新增项前端已写入硬件树分类中,按照线路侧、客户侧等分别存储
            add_board = body_params.get('data', {})
            global pr_rdc_info_table

            add_board = merge_board_info(add_board, board_tree)
            logger.info(f"--------add_board:{add_board}")
            # 全量 = 增量 + 存量
            exist_tree = filter_board_tree_clear_values(add_board, board_tree)
            logger.info(f"----- exist_tree: {exist_tree} -----")
            # 2 根据单板模型获取特性子特性
            # 从单板数获取"产品"、"板卡类型"、"单板业务模型"、"单板标识"
            board_factor = extract_board_global_status(board_tree)
            logger.info(f"---------board_factor:{board_factor}\n")

            # 根据"单板业务模型"从特性树获取特性子特性并集'boardBusinessModel': 'L_O/L_V'
            board_type = ','.join(set(board_factor["boardBusinessModel"].replace('-', '|').split('|')))
            logger.info(f"---------board_type:{board_type}\n")
            features = querySrcFeatureBoardRelation(board_type)

            # 3 根据通用过滤流程进行过滤
            if "支线路合一" in board_factor["boardType"]:
                # features_l = querySrcFeatureBoardRelation("MGR_L")
                # filter_features_l = filter_details_features_by_board_type(board_tree, features_l, is_c_flag=False)
                # features_c = querySrcFeatureBoardRelation("MGR_C")
                # filter_features_c = filter_details_features_by_board_type(board_tree, features_c, is_c_flag=True)
                # filter_features = merge_feature_mgr_c_and_mgr_l(filter_features_l, filter_features_c)

                add_cfg = add_board.get("业务FRM芯片", "")
                features_l = querySrcFeatureBoardRelation("MGR_L")
                features_c = querySrcFeatureBoardRelation("MGR_C")
                if not add_cfg:
                    filter_features_l = filter_details_features_by_board_type(board_tree, features_l, is_c_flag=False)
                    filter_features_c = filter_details_features_by_board_type(board_tree, features_c, is_c_flag=True)
                    filter_features = merge_feature_mgr_c_and_mgr_l(filter_features_l, filter_features_c)
                else:
                    part_cont = '新增业务FRM芯片' 
                    cfg_features = querySrcFeatureChangeRelation(part_cont)
                    cfg_filter_l = filter_features_by_part(features_l, cfg_features)
                    filter_features_l = filter_details_features_by_board_type(board_tree, cfg_filter_l, is_c_flag=False)
                    cfg_filter_c = filter_features_by_part(features_c, cfg_features)
                    filter_features_c = filter_details_features_by_board_type(board_tree, cfg_filter_c, is_c_flag=True)
                    filter_features = merge_mgr_c_and_mgr_l(filter_features_l, filter_features_c)
                    merged_list = merge_to_global_status_list(board_factor, filter_features, head_employ_no)
                    if len(merged_list) < 1:
                        logger.error(f"--------待合并到全局状态表的数据{merged_list}为空")
                        return
                    addSrcBoardWholeStatusData(merged_list, head_employ_no)

                    # 5 添加变更分析
                    results = board_format_change_analysis(board_tree, merged_list, head_employ_no)
                    
                    feature_key = "业务基础"
                    analysis = format_change_analysis(board_name, "单板部件", "业务FRM芯片", feature_key)
                    for item in merged_list:
                        if "非首次" in analysis:
                            development_type = '存量单板-新增器件-首次使用需求'
                            reuse_degree = '微范式'
                        else:
                            development_type = '新增单板-新增器件需求'
                            reuse_degree = '全代码'
                        change_development_type_to_global_st(board_name, item.get("feature",""), development_type, reuse_degree, head_employ_no)

                    only_l_list, only_c_list, both_list = split_mgr_c_and_mgr_l(filter_features_l, filter_features_c)
                    # both_list分成单板级和客户侧线路侧两部分
                    board, c_l_share = filter_c_l_and_board(both_list)

                    merged_l = merge_to_global_status_list(board_factor, only_l_list, head_employ_no)
                    merged_c = merge_to_global_status_list(board_factor, only_c_list, head_employ_no)
                    merged_l_c = merge_to_global_status_list(board_factor, c_l_share, head_employ_no)
                    merged_board = merge_to_global_status_list(board_factor, board, head_employ_no)
                    if split_rdc_flag.upper() == "Y":
                        part = add_prefix_suffix(add_board, "业务FRM芯片")
                        global pr_bundle
                        clear_pr_bundle()
                        clear_pr_rdc_info_table()
                        rdc_add_board_whole_st_data_add(add_board, board_tree, part, merged_l, body_params, head_employ_no)
                        pr_bundle['l_pri'] = copy.deepcopy(pr_rdc_info_table)
                        clear_pr_rdc_info_table()
                        rdc_add_board_whole_st_data_add(add_board, board_tree, part, merged_c, body_params, head_employ_no)
                        pr_bundle['c_pri'] = copy.deepcopy(pr_rdc_info_table)
                        clear_pr_rdc_info_table()
                        rdc_add_board_whole_st_data_add(add_board, board_tree, part, merged_board, body_params, head_employ_no)
                        pr_bundle['board'] = copy.deepcopy(pr_rdc_info_table)

                        clear_pr_rdc_info_table()
                        part = add_prefix_suffix(add_board, "业务FRM芯片_客户侧")
                        rdc_add_board_whole_st_data_add(add_board, board_tree, part, merged_l_c, body_params, head_employ_no)
                        pr_bundle['c_pub'] = copy.deepcopy(pr_rdc_info_table)

                        clear_pr_rdc_info_table()
                        part = add_prefix_suffix(add_board, "业务FRM芯片_线路侧")
                        rdc_add_board_whole_st_data_add(add_board, board_tree, part, merged_l_c, body_params, head_employ_no)
                        pr_bundle['l_pub'] = copy.deepcopy(pr_rdc_info_table)
                        
                        logger.info(f"--pr_bundle : {pr_bundle}")
                        logger.info(f"create_mr_flag: 需要拆分MR")
                        body_params['text'] = "-" + part
                        body_params["employ_no"] = mr_employ_no
                        rdc_mr_split_by_pr(board_tree, pr_rdc_info_table, body_params, head_employ_no)

            elif "客户侧" in board_factor["boardType"]:
                filter_features = filter_details_features_by_board_type(board_tree, features, is_c_flag=True)
            else:
                filter_features = filter_details_features_by_board_type(board_tree, features, is_c_flag=False)  
            merged_list = merge_to_global_status_list(board_factor, filter_features, head_employ_no)
            # 4.1 根据新增光模块场景对特性进行过滤
            part_filter, analysis = add_opt_mod_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text_c = add_prefix_suffix(add_board, "客户侧光模块")
                text_l = add_prefix_suffix(add_board, "线路侧光模块")
                text = text_c + ',' + text_l
                body_params['text'] = "-"+text_l
                clear_pr_rdc_info_table()
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)
                body_params["employ_no"] = mr_employ_no
                rdc_mr_split_by_pr(add_board, pr_rdc_info_table, body_params, head_employ_no, is_change=True)

            # 4.2 根据新增光层业务场景对特性进行过滤
            # part_filter, analysis = add_opt_svc_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            # if len(part_filter) > 0:
            #     text_c = add_prefix_suffix(add_board, "客户侧光层业务")
            #     text_l = add_prefix_suffix(add_board, "线路侧光层业务")
            #     text = text_c + ',' + text_l
            #     rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, pr_body_params)

            # 4.3 根据新增电层业务场景对特性进行过滤
            part_filter, analysis = add_ele_svc_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text_c = add_prefix_suffix(add_board, "客户侧电层业务")
                text_l = add_prefix_suffix(add_board, "线路侧电层业务")
                text = text_c + ',' + text_l
                # body_params['text'] = "-" + text_l
                clear_pr_rdc_info_table()
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)
                body_params["employ_no"] = mr_employ_no
                rdc_mr_split_by_pr(add_board, pr_rdc_info_table, body_params, head_employ_no, is_change=True)

            # 4.4 根据新增时钟芯片场景对特性进行过滤
            part_filter, analysis = add_timer_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "时钟芯片")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)

            # 4.5 根据新增配置类型(灰光、中继)场景对特性进行过滤
            part_filter, analysis = add_cfg_type_generate_change_analysis(board_name, add_board, board_tree, merged_list, body_params, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "单板配置类型").replace("业务速率配置类型_", "")
                clear_pr_rdc_info_table()
                body_params['text'] = text
                clear_pr_rdc_info_table()
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)
                body_params["employ_no"] = mr_employ_no
                rdc_mr_split_by_pr(add_board, pr_rdc_info_table, body_params, head_employ_no, is_change=True)
                
            # 4.6 根据新增物理端口数量场景对特性进行过滤
            part_filter, analysis = add_ports_num_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "物理端口数量")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)

            # 4.7 根据新增GEARBOX场景对特性进行过滤
            part_filter, analysis = add_gearbox_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "GEARBOX")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)

            # 4.8 根据新增控制逻辑场景对特性进行过滤
            part_filter, analysis = add_ctr_logic_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "控制逻辑")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)

            # 4.9 根据新增子架适配场景对特性进行过滤
            part_filter, analysis = add_shelf_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "单板支持的子架")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)
                
            # 4.10 根据新增单板业务模型场景对特性进行过滤
            part_filter, analysis = add_board_model_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "单板业务模型")
                clear_pr_rdc_info_table()
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)
                body_params['text'] = "-" + text
                body_params["employ_no"] = mr_employ_no
                rdc_mr_split_by_pr(add_board, pr_rdc_info_table, body_params, head_employ_no, is_change=True)

            # 4.11 根据新增开销逻辑场景对特性进行过滤
            part_filter, analysis = add_oh_logic_generate_change_analysis(board_name, add_board, merged_list, head_employ_no)
            if len(part_filter) > 0:
                text = add_prefix_suffix(add_board, "开销逻辑")
                rdc_add_board_whole_st_data_add(add_board, exist_tree, text, part_filter, body_params, head_employ_no)

            if len(pr_rdc_info_table) > 0 and mr_ident:
                logger.info(f"关联已有MR: {mr_ident}")
                body = build_link_body(mr_ident, pr_rdc_info_table)
                update_RDC_relatedWorkItemId(body, head_employ_no)
            if mr_ident:
                rdc_info_to_other_domain_by_mr(board_name, mr_ident, body_params, head_employ_no)

            # 任务成功完成
            logger.info("拆分成功")
            task_info_dict = {
                "task_status": "completed",
                "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update_task_info_dict(task_id, task_info_dict)

        except Exception as e:
            logger.error(f"[{task_id}] 后台任务发生严重异常: {e}", exc_info=True)
            task_info_dict = {
                "task_status": "completed",
                "task_err_reason": str(e),
                "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update_task_info_dict(task_id, task_info_dict)
            return jsonify({"code": 500, "status": "error", "message": f"处理异常: {str(e)}", "data": ""})
        finally:
            logger.info(f"[{task_id}] 后台任务线程结束")
            for handler in logger.handlers:
                handler.flush()



# 查询单板新增的特性-子特性数据
def query_board_new_features():
    """
    查询指定单板新增的特性-子特性数据
    ---
    tags:
      - 特性-单板
    description: 查询指定单板新增的特性-子特性数据
    parameters:
      - name: board
        in: query
        description: 单板
        required: true
        type: string
    responses:
      200:
        description: 更新变更分析数据
    """
    query_params = request.args.to_dict()
    logger.info(f"---------query_params:{query_params}\n")

    # 因为前端已修改，但后端未修改，所以临时规避，后期删除
   
    board_name = query_params.get('board', '')
    board_tree = get_product_factor_by_board(board_name)
    if len(board_tree) < 1:
        logger.error("--------单板数据不存在--------")
        return ""

    # 2 根据单板模型获取特性子特性
    # 从单板数获取"产品"、"板卡类型"、"单板业务模型"、"单板标识"
    board_factor = extract_board_global_status(board_tree)
    logger.info(f"---------board_factor:{board_factor}\n")

    # 根据"单板业务模型"从特性树获取特性子特性并集'boardBusinessModel': 'L_O/L_V'
    board_type = ','.join(set(board_factor["boardBusinessModel"].replace('-', '|').split('|')))
    logger.info(f"---------board_type:{board_type}\n")
    feature_datas = querySrcFeatureBoardRelation(board_type)
    board_features = dict()
    board_datas = queryBoardWholeStatusDataByBoardName(board_name)
    for record in board_datas:
        if record['parent'] == '2':
            board_features[record['feature_name']] = []
        elif record['parent'] == '1':
            board_features[record['feature_name']].append(record['children_feature_name'])
    add_feature_dict = dict()
    for feature_data in feature_datas:
        if feature_data['feature'] not in add_feature_dict:
            add_feature_dict[feature_data['feature']] = []
        # 临时注释
        # if feature_data['feature'] not in board_features:
        #     add_feature_dict[feature_data['feature']].append(feature_data['subFeature'])
        # elif feature_data['subFeature'] not in board_features[feature_data['feature']]:
        #     add_feature_dict[feature_data['feature']].append(feature_data['subFeature'])
        # 临时新增
        add_feature_dict[feature_data['feature']].append(feature_data['subFeature'])
    # 将add_feature_dict转换为树形结构
    tree_result = []
    for feature, sub_features in add_feature_dict.items():
        children = [{"label": sub_feature, "value": sub_feature} for sub_feature in sub_features if sub_feature.strip()]
        if children:
            tree_result.append({
                "label": feature,
                "value": feature,
                "children": children
            })
    return jsonify({"code": 200, "status": "success", "message": "单板新增的特性-子特性数据查询成功", "data": tree_result})

def extract_solution_link(description):
    """
    从description字段中提取"方案："后面的链接
    
    Args:
        description: 包含方案链接的字符串
        
    Returns:
        提取到的链接字符串，如果没有找到则返回None
    """
    if not description:
        return None
    
    # 使用正则表达式匹配"方案："后面的URL
    # 匹配模式：方案：后面跟着的http/https链接
    pattern = r'方案[：:]\s*(https?://[^\s\n]+)'
    
    match = re.search(pattern, description)
    if match:
        return match.group(1)
    
    return ""

# 新增特性-子特性变更分析数据更新
def add_new_feature_update_change_analysis_data():
    """
    更新特性变更分析数据
    ---
    tags:
      - 单板全局状态
    description: 接收 POST 请求，支持通过 Header 和 JSON Body 参数进行身份验证与数据提交
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户工号对应的token，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: [board]
          properties:
            board:
              type: string
              description: 单板名称
            feature:
              type: string
              description: 特性
            subFeature:
              type: string
              description: 子特性
            mr_ident:
              type: string
              description: mr标识
            requirementType:
              type: string
              description: 需求类型
            belongTeam:
              type: string
              description: 归属团队
          example:   # 示例值
            board: "xx1,xx2"
            feature: "F070181-E-业务单板-巡检-线路侧光模块巡检"
            subFeature: "FS070181-01-E-线路侧光模块巡检"
            mr_ident: "OTNSW-83259"
            requirementType: "平台团队需求"
            belongTeam: "L1-平台团队"
    responses:
      200:
        description: 更新变更分析数据
    """
    # 1 获取单板数-数据库
    head_employ_no = request.headers.get('X-Emp-No')
    body_params = request.get_json()
    logger.info(f"-------body_params:{body_params}")
    start_time = datetime.datetime.now()
    logger.info(f'--------start_time:{start_time.strftime("%Y-%m-%d %H:%M:%S")}')
    task_id = str(uuid.uuid4())
    task_info_dict = {}
    task_info_dict["employ_no"] = head_employ_no
    task_info_dict["employ_name"] = pub_get_employ_name(head_employ_no)
    task_info_dict["task_type"] = "新增特性"
    task_info_dict["task_param"] = body_params
    task_info_dict["task_status"] = "pending"
    task_info_dict["task_start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_task_info_dict(task_id, task_info_dict)
    thread = threading.Thread(target=src_add_new_feature_update_change_analysis_data, args=[body_params, head_employ_no, task_id])
    thread.daemon = False
    thread.start()

    return jsonify({"code": 200, "status": "success", "message": "处理逻辑进程启动，请根据返回的task_id调用get_task_result接口获取最终的执行结果", "data": [task_id]})


# 新增特性-子特性变更分析数据更新
def src_add_new_feature_update_change_analysis_data(body_params, head_employ_no, task_id):
    body_params["task_id"] = task_id
    board_name = body_params.get('board', '')
    add_feature = body_params.get('feature', '')
    add_subFeature = body_params.get('subFeature', '')
    mr_ident = body_params.get('mr_ident','')
    stock_flag = body_params.get('associate_MR','')
    # 因为前端已修改，但后端未修改，所以临时规避，后期删除
    if not body_params.get("employ_no"):
        body_params["employ_no"] = head_employ_no
    mr_employ_no = body_params["employ_no"]
    body_params['text'] = ""
    mr_ident = body_params.get('mr_ident', '')

    from app import app
    with app.app_context():
        try:
            board_tree = get_product_factor_by_board(board_name)
            if len(board_tree) < 1:
                logger.error("--------单板数据不存在--------")
                task_info_dict = {
                    "task_status": "completed",
                    "task_err_reason": '单板数据不存在',
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)
                return jsonify({"code": 404, "status": "error", "message": "单板数据不存在", "data": "单板数据不存在"})

            related_mr_info = []
            if mr_ident:
                related_mr_info = get_rdc_info_from_related_mr(mr_ident, head_employ_no)

                if len(related_mr_info) > 0:
                    body_params["requirementPrePlanning"] = related_mr_info[0].get("requirement_pre_planning","")
                    body_params["specificationByExampleUrl"] = related_mr_info[0].get("specification_by_example_url","")
                    body_params["designSpecificationUrl"] = related_mr_info[0].get("board_design_url","")
                    

            global pr_rdc_info_table
            # 2 根据单板模型获取特性子特性
            # 从单板数获取"产品"、"板卡类型"、"单板业务模型"、"单板标识"
            board_factor = extract_board_global_status(board_tree)
            logger.info(f"---------board_factor:{board_factor}\n")

            # 根据"单板业务模型"从特性树获取特性子特性并集'boardBusinessModel': 'L_O/L_V'
            features = querySrcFeatureBoardRelation("", "", "", "", add_subFeature)
            for feature in features:
                feature["product"] = board_factor.get("product", "")
            merged_list = merge_to_global_status_list(board_factor, features, head_employ_no)
            addSrcBoardWholeStatusData(merged_list, head_employ_no)
            for item in merged_list:
                development_type = '存量单板-功能补齐'
                reuse_degree = '全代码'
                change_development_type_to_global_st(board_name, item.get("feature",""), development_type, reuse_degree, head_employ_no)
                development_type, reuse_degree= get_development_type_by_global_st(board_name, item.get("feature",""), add_subFeature)

            hd_sub = get_hd_sub_type_by_name(board_tree)
            clear_pr_rdc_info_table()
            for i in features:
                subfeature = i.get("subFeature", "")
                rdc_name = add_board_suffix_str(hd_sub, subfeature)
                # 方案通过描述信息中的方案进行提取
                link = extract_solution_link(i.get("description", ""))
                rdc_ret_val = rdc_info_to_subfeature(board_name, features, rdc_name, i, body_params)

            if len(pr_rdc_info_table) > 0 and mr_ident:
                logger.info(f"关联已有MR: {mr_ident}")
                body = build_link_body(mr_ident, pr_rdc_info_table)
                update_RDC_relatedWorkItemId(body, head_employ_no)

            if mr_ident:
                rdc_info_to_other_domain_by_mr(board_name, mr_ident, body_params, head_employ_no)
            
            # 任务成功完成
            if stock_flag == True:
                logger.info("拆分成功")
                task_info_dict = {
                    "task_status": "completed",
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)
            else:
                task_info_dict = {
                    "task_status": "completed",
                    "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                update_task_info_dict(task_id, task_info_dict)

        except Exception as e:
            logger.error(f"[{task_id}] 后台任务发生严重异常: {e}", exc_info=True)
            task_info_dict = {
                "task_status": "completed",
                "task_err_reason": str(e),
                "task_end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update_task_info_dict(task_id, task_info_dict)
            return jsonify({"code": 500, "status": "error", "message": f"处理异常: {str(e)}", "data": ""})
        finally:
            logger.info(f"[{task_id}] 后台任务线程结束")
            for handler in logger.handlers:
                handler.flush()



################ MR创建与关联 ###################
def split_by_keywords(records: List[Dict], keywords: List[str]) -> Tuple[List[Dict], List[Dict]]:
    kw_lower = [k.lower() for k in keywords]
    remaining, filtered = [], []
    for rec in records:
        title = rec.get("rdcTitle", "").lower()
        (filtered if any(k in title for k in kw_lower) else remaining).append(rec)
    return remaining, filtered

def print_dict_list(label: str, lst: List[Dict]) -> None:
    logger.info(f'----- {label} -----')
    if not lst:
        logger.info("no_tag")
    else:
        for rec in lst:
            logger.info(rec)

def group_by_suffix_v2(key_str: str, records: List[dict], is_flag: bool = False) -> List[Dict[str, List[dict]]]:
    keys = [k for k in map(str.strip, key_str.split(',')) if k]
    groups: Dict[str, List[dict]] = {"no_tag": []}

    # 构造正则：含/就拆成“或”关系，不含/就整段精确匹配
    patterns = {}
    for k in keys:
        # if '/' in k:
        if is_flag:
            parts = [re.escape(p) for p in k.split('/')]
            patterns[k] = re.compile('|'.join(parts))      # 800GE|800GE-PHY
        else:
            patterns[k] = re.compile(re.escape(k))         # 完整匹配

    for rec in records:
        title = re.sub(r'-L1$', '', rec['rdcTitle'])
        target_key = "no_tag"
        for k in keys:
            if patterns[k].search(title):
                target_key = k
                break
        groups.setdefault(target_key, []).append(rec)

    result = [{"no_tag": groups.pop("no_tag")}] if groups.get("no_tag") else []
    result.extend([{k: groups[k]} for k in keys if k in groups])
    return result


def group_by_suffix_fs_name(board: str, records: List[dict]) -> List[Dict[str, List[dict]]]:
    """
    按 rdcTitle 中 board 后第一个 '-' 之后内容分组，返回 List[Dict[str, List[dict]]]
    """
    pat = re.compile(rf'{re.escape(board)}[^-]*-(.+)')
    groups: Dict[str, List[dict]] = {}

    for rec in records:
        # 去掉末尾 -L1
        title = re.sub(r'-L1$', '', rec['rdcTitle'])
        # 提取分组 key
        m = pat.search(title)
        if m:
            key = m.group(1).strip()
        else:
            key = "no_tag"
        groups.setdefault(key, []).append(rec)

    # 转成题目要求的 List[Dict[str, List[dict]]] 格式
    result = [{k: v} for k, v in groups.items()]
    # logger.info(result)
    return result

def add_mr_name_prefix(fs_list, mr_name):
    """
    为列表中的键名添加前缀或替换
    :param fs_list: 原始列表数据
    :param mr_name: 输入字符串
    :return: 处理后的列表
    """
    result = []
    for item in fs_list:
        new_item = {}
        for key, value in item.items():
            if key == 'no_tag':
                new_key = mr_name
            else:
                new_key = f"{mr_name}-{key}"
            new_item[new_key] = value
        result.append(new_item)
    return mr_name, result

def get_all_keys(record_list: List[Dict[str, Any]]) -> List[str]:
    """
    提取列表中所有字典的键，去重后返回一个列表。
    """
    keys = set()
    for d in record_list:
        keys.update(d.keys())
    return list(keys)

def merge_analysis_unique(data: List[Dict[str, str]]) -> str:
    normal_items = set()
    key_items    = set()

    for item in data:
        ana = item.get("analysis", "")
        # 按逗号拆分并去空白
        for seg in (s.strip() for s in ana.split(',') if s.strip()):
            if '因子' in seg:
                key_items.add(seg)
            else:
                normal_items.add(seg)

    # 拼回原文本格式（有序）
    normal_block = ",<br>".join(sorted(normal_items))
    key_block    = ",<br>".join(sorted(key_items))

    result = f"普通变更:<br> {normal_block}<br>\n关键变更:<br> {key_block}"
    return result.replace(";", "")

def build_link_body(related_id: str, work_ids: List[str]) -> List[Dict[str, Any]]:
    """
    根据入参构造 body 数据
    :param related_id:  填入 relatedWorkItemId 的字符串
    :param work_ids:    填入 workItemId 的字符串列表
    :return:            符合要求的 body 列表
    """
    if not related_id or len(work_ids) < 1:
        return [] 
    return [
        {
            "workItemId": wid.get("rdcIdent", ""),
            "relatedWorkItemId": related_id,
            "linkRelationName": "父级"
        }
        for wid in work_ids
    ]

def max_rate_under_1200(svc_type:str):
    """
    在所有 tags 对应的速率里，返回小于 1200 的最大速率及其 svc_id。
    若无满足条件的数据，返回 (None, -1.0)
    """
    tags = svc_type.split(",")
    best_id: Optional[str] = tags[0]
    best_rate: float = -1.0
    rate_table = querySrcBusinessSpeedTypeByParams({}, markdown_flag=True)
    for svc_id in tags:
        rate_vals: List[float] = list(map(float, get_speed_by_type(rate_table, svc_id)))
        # 只保留 <1200 的速率
        under_1200 = [v for v in rate_vals if v < 1200]
        if under_1200:
            max_under = max(under_1200)
            if max_under > best_rate:
                best_rate = max_under
                best_id   = svc_id

    return best_id

def get_c_svc_ge_phy_merge(key: str, items: List[str]) -> str:
    """
    返回第一个包含 key 中任意片段的字符串；未命中返回 ""
    """
    for s in items:
        if any(k in s for k in key.split('/')):
            return s
    return ""

def pr_rdc_split_other_fields(domain_str: str) -> List[str]:
    """
    按逗号拆分并去掉空元素，过滤掉 '02-L1'
    """
    return [item.strip() for item in domain_str.split(',')
            if item.strip() and item.strip() != '02-L1']

def rdc_mr_traverse_split_by_pr(board_tree, mr_tabel, pr_table, svc_type, mod_type, body_params, head_employ_no):
    board_name = board_tree.get("board","")
    hd_sub = get_hd_sub_type_by_name(board_tree)
    employ_no = body_params.get('employ_no', '')
    priority_shelf = body_params.get('subrack', '')
    if priority_shelf:
        priority_shelf = '-[' + priority_shelf + ']'
    if body_params['text']:
        priority_shelf = body_params['text']
    if "STM" in svc_type:
        svc_rate = business_rate_classification(svc_type)
        svc_type = svc_rate[0]
        def_tag_svc = svc_rate[0]
        # # 判断小于100G速率
        # first_svc = get_left_part(svc_rate[0])
        # rate_table = querySrcBusinessSpeedTypeByParams({}, markdown_flag=True)
		# rate = list(map(float, get_speed_by_type(rate_table, first_svc)))
    elif "GE" in svc_type:
        c_svc_rate = max_rate_under_1200(svc_type)
        svc_rate = business_rate_classification(svc_type)
        def_tag_svc = get_c_svc_ge_phy_merge(c_svc_rate, svc_rate)
        svc_type = ','.join(svc_rate)
    else:
        def_tag_svc = max_rate_under_1200(svc_type)
    pr_table_temp = pr_table

    # 1 清除mr记录
    global mr_rdc_info_table_all
    clear_mr_rdc_info_table_all()

    logger.info(f"-----svc_type:{svc_type}--def_tag_svc: {def_tag_svc}------")
    # 2 遍历MR逐个处理
    for item in mr_tabel:
        mr_title = item.get('mr_title','').replace("xxxx", hd_sub)
        mr_name = "-".join(mr_title.split("-", 2)[:2])
        logger.info(f"--mr_title:{mr_title}---- mr_tabel: {mr_name} ------")

        # 筛选该MR下包含的所有PR
        fs_str = item.get('relatedSubFeatures','')
        keywords = [k.strip() for k in fs_str.split(',') if k.strip()]
        remaining, filtered = split_by_keywords(pr_table_temp, keywords)
        if len(filtered) < 1:
            continue

        # 按照业务类型对PR进行分组
        group_fs = group_by_suffix_v2(svc_type, filtered, is_flag=True)
        svc_tags = ['_'.join(filter(None, svc_type.split(',')))] #svc_type.split(",")
        # logger.info(group_fs)

        # 按照模块类型对PR进行分组
        mod_group_fs = group_by_suffix_v2(','.join(mod_type), filtered)
        mod_tags = ['_'.join(filter(None, mod_type))] # mod_type

        # 单个分组
        if "业务类型" in mr_title:
            # 两层分组
            for mr_item in group_fs:
                # 获取MR与PR信息
                tags, svc_pr_info = next(iter(mr_item.items()))
                if tags == "no_tag":
                    rdc_space = RDC_TABLE.get("rdc_space", "")
                    workItemIds = [item['rdcIdent'] for item in svc_pr_info]
                    add_tag_RDC(rdc_space, svc_tags, workItemIds, employ_no)
                    rdc_mr_name = mr_name
                    tags = def_tag_svc
                    if len(group_fs) > 1:
                        continue
                elif tags == def_tag_svc and len(group_fs) > 1:
                    tags, no_tag_pr_info = next(iter(group_fs[0].items()))
                    svc_pr_info = svc_pr_info + no_tag_pr_info
                    rdc_mr_name = mr_name + "-" + def_tag_svc
                else: 
                    rdc_mr_name = mr_name + "-" + tags
                if "模块简称" in mr_title :
                    mod_group_fs = group_by_suffix_v2(','.join(mod_type), svc_pr_info)
                    for mod_item in mod_group_fs:
                        # 获取MR与PR信息
                        tags, pr_info = next(iter(mod_item.items()))
                        if tags == "no_tag":
                            mod_mr_name = rdc_mr_name + priority_shelf
                        else:
                            mod_mr_name = rdc_mr_name + "-" + tags + priority_shelf
                        # 创建MR返回MR_ID
                        analysis = merge_analysis_unique(pr_info)
                        other_domain = rdc_info_to_other_domain(board_name, rdc_mr_name, item, body_params, head_employ_no)
                        mr_result = mr_rdc_info_to_subfeature(board_name, mod_mr_name, item, analysis, body_params)
                        if len(mr_result) > 0:
                            mr_id = mr_result[0].get("rdcIdent", "")
                            # 根据MR_ID关联所有子PR_ID更新RDC关系
                            body = build_link_body(mr_id, pr_info)
                            update_RDC_relatedWorkItemId(body, employ_no)
                            body = build_link_body(mr_id, other_domain)
                            update_RDC_relatedWorkItemId(body, employ_no)
                else:
                    rdc_mr_name = rdc_mr_name + priority_shelf
                    analysis = merge_analysis_unique(svc_pr_info)
                    other_domain = rdc_info_to_other_domain(board_name, rdc_mr_name, item, body_params, head_employ_no)
                    mr_result = mr_rdc_info_to_subfeature(board_name, rdc_mr_name, item, analysis, body_params)
                    if len(mr_result) > 0:
                        mr_id = mr_result[0].get("rdcIdent", "")
                        # 根据MR_ID关联所有子PR_ID更新RDC关系
                        body = build_link_body(mr_id, svc_pr_info)
                        update_RDC_relatedWorkItemId(body, employ_no)
                        body = build_link_body(mr_id, other_domain)
                        update_RDC_relatedWorkItemId(body, employ_no)

        elif "模块简称" in mr_title or "封装类型" in mr_title:
            for mr_item in mod_group_fs:
                # 获取MR与PR信息
                tags, pr_info = next(iter(mr_item.items()))
                if tags == "no_tag":
                    rdc_space = RDC_TABLE.get("rdc_space", "")
                    workItemIds = [item['rdcIdent'] for item in pr_info]
                    add_tag_RDC(rdc_space, mod_tags, workItemIds, employ_no)
                    rdc_mr_name = mr_name
                    tags = def_tag_svc
                    if len(group_fs) > 1:
                        continue
                elif tags == def_tag_svc and len(group_fs) > 1:
                    tags, no_tag_pr_info = next(iter(group_fs[0].items()))
                    pr_info = pr_info + no_tag_pr_info
                    rdc_mr_name = mr_name + "-" + def_tag_svc
                else: 
                    rdc_mr_name = mr_name + "-" + tags
                # 创建MR返回MR_ID
                rdc_mr_name = rdc_mr_name + priority_shelf
                analysis = merge_analysis_unique(pr_info)
                
                other_domain = rdc_info_to_other_domain(board_name, rdc_mr_name, item, body_params, head_employ_no)
                mr_result = mr_rdc_info_to_subfeature(board_name, rdc_mr_name, item, analysis, body_params)
                if len(mr_result) > 0:
                    mr_id = mr_result[0].get("rdcIdent", "")
                    # 根据MR_ID关联所有子PR_ID更新RDC关系
                    body = build_link_body(mr_id, pr_info)
                    update_RDC_relatedWorkItemId(body, employ_no)
                    body = build_link_body(mr_id, other_domain)
                    update_RDC_relatedWorkItemId(body, employ_no)
        else:
            if "单板支持yyy子架" in mr_title:
                shelf_group = group_by_suffix_fs_name(hd_sub, filtered)
                for mr_item in shelf_group:
                    # 获取MR与PR信息
                    tags, pr_info = next(iter(mr_item.items()))
                    rdc_mr_name = mr_name.replace("yyy", tags)
                    analysis = merge_analysis_unique(pr_info)
                    if "新增" in priority_shelf:
                        rdc_mr_name = mr_name + priority_shelf                    
                    other_domain = rdc_info_to_other_domain(board_name, rdc_mr_name, item, body_params, head_employ_no)
                    mr_result = mr_rdc_info_to_subfeature(board_name, rdc_mr_name, item, analysis, body_params)
                    if len(mr_result) > 0:
                        mr_id = mr_result[0].get("rdcIdent", "")
                        # 根据MR_ID关联所有子PR_ID更新RDC关系
                        body = build_link_body(mr_id, pr_info)
                        update_RDC_relatedWorkItemId(body, employ_no)
                        body = build_link_body(mr_id, other_domain)
                        update_RDC_relatedWorkItemId(body, employ_no)
                continue
            elif "单板支持工装测试" in mr_title:
                rdc_mr_name = mr_name
                if "新增" in priority_shelf:
                    rdc_mr_name = mr_name + priority_shelf
            else:
                rdc_mr_name = mr_name + priority_shelf

            analysis = merge_analysis_unique(filtered)
            other_domain = rdc_info_to_other_domain(board_name, rdc_mr_name, item, body_params, head_employ_no)
            mr_result = mr_rdc_info_to_subfeature(board_name, rdc_mr_name, item, analysis, body_params)
            if len(mr_result) > 0:
                mr_id = mr_result[0].get("rdcIdent", "")
                # 根据MR_ID关联所有子PR_ID更新RDC关系
                body = build_link_body(mr_id, filtered)
                update_RDC_relatedWorkItemId(body, employ_no)
                body = build_link_body(mr_id, other_domain)
                update_RDC_relatedWorkItemId(body, employ_no)                
        pr_table_temp = remaining
    global mr_rdc_info_table
    logger.info(f"---剩余PR未关联MR--remaining: {remaining}---mr_rdc_info_table:{mr_rdc_info_table}----")

# 根据子特性创建多条RDC数据
mr_rdc_info_table = []
mr_rdc_info_table_all = []

def clear_mr_rdc_info_table():
    """清空全局变量 pr_table"""
    global mr_rdc_info_table
    mr_rdc_info_table.clear()

def clear_mr_rdc_info_table_all():
    """清空全局变量 pr_table"""
    global mr_rdc_info_table_all
    mr_rdc_info_table_all.clear()

def mgr_l_and_c_rdc_mr_split(board_tree, mr_tabel, pr_bundle, body_params, head_employ_no):
    employ_no = body_params.get('employ_no', '')
    board_name = board_tree.get("board", "")

    c_mod = board_tree.get("客户侧光模块", "")
    l_mod = board_tree.get("线路侧光模块", "")
    c_svc = board_tree.get("客户侧电层业务", "")
    l_svc = board_tree.get("线路侧电层业务", "")
    c_mod_type = c_mod.split(',')
    l_mod_type = extract_module_prefix_str(l_mod)

    c_pri_pr_table = pr_bundle['c_pri']
    c_pub_pr_table = pr_bundle['c_pub']
    l_pri_pr_table = pr_bundle['l_pri']
    l_pub_pr_table = pr_bundle['l_pub']
    board_pr_table = pr_bundle['board']

    # logger.info(f"--mgr_l_and_c_rdc_mr_split: board_tree{board_tree}")
    # logger.info(f"--mgr_l_and_c_rdc_mr_split: mr_tabel{mr_tabel}")
    # logger.info(f"--mgr_l_and_c_rdc_mr_split: pr_bundle{pr_bundle}")

    hd_sub = get_hd_sub_type_by_name(board_tree)

    # 1 清除mr记录
    global mr_rdc_info_table
    clear_mr_rdc_info_table()
    # 线路侧默认业务
    def_tag_svc = max_rate_under_1200(l_svc)

    # 2 拆分线路侧和单板级MR
    l_pr_table = merge_mgr_c_and_mgr_l(l_pri_pr_table, l_pub_pr_table)
    l_total = merge_mgr_c_and_mgr_l(l_pr_table, board_pr_table)
    rdc_mr_traverse_split_by_pr(board_tree, mr_tabel, l_total, l_svc, l_mod_type, body_params, head_employ_no)

    # 3 根据M021 M022 M132MR的特性过滤客户侧PR
    c_total = merge_mgr_c_and_mgr_l(c_pri_pr_table, c_pub_pr_table)
    c_pr_table = c_total
    for item in mr_tabel:
        mr_title = item.get('mr_title','').replace("xxxx", hd_sub)
        mr_name = "-".join(mr_title.split("-", 2)[:2])
        # 挂载客户侧MR
        if "M021" in mr_name or "M022" in mr_name or "M132" in mr_name or "M351" in mr_name:
            fs_str = item.get('relatedSubFeatures','')
            keywords = [k.strip() for k in fs_str.split(',') if k.strip()]
            remaining, filtered = split_by_keywords(c_pr_table, keywords)
            if len(filtered) < 1:
                continue
            # 挂载到包含def_tag_svc的MR下面，
            for mr_item in mr_rdc_info_table:
                if mr_name in mr_item.get('rdcTitle','') and (def_tag_svc in mr_item.get('rdcTitle','') or "M351" in mr_name):
                    mr_id = mr_item.get("rdcIdent", "")
                    body = build_link_body(mr_id, filtered)
                    update_RDC_relatedWorkItemId(body, employ_no)
            c_pr_table = remaining
        else:
            continue
            
    # 4 拆分剩余的客户侧PR
    rdc_mr_traverse_split_by_pr(board_tree, mr_tabel, c_pr_table, c_svc, c_mod_type, body_params, head_employ_no)

def rdc_mr_split_by_pr(board_tree, pr_table, body_params, head_employ_no, is_change=False):
    board_name = board_tree.get("board", "")
    board_type = board_tree.get("板卡类型", "")
    c_mod = board_tree.get("客户侧光模块", "")
    l_mod = board_tree.get("线路侧光模块", "")
    c_svc = board_tree.get("客户侧电层业务", "")
    l_svc = board_tree.get("线路侧电层业务", "")
    mr_ident = body_params.get('mr_ident', '')

    if mr_ident:
        logger.info(f"关联已有MR: {mr_ident}, not need split mr")
        return

    c_mod_type = c_mod.split(',')
    l_mod_type = extract_module_prefix_str(l_mod)

    logger.info(f"--board_name: {board_name}-board_type: {board_type} c_mod:{c_mod}-l_mod:{l_mod}-c_svc:{c_svc}-l_svc:{l_svc}")

    # 1 查询所有MR信息
    mr_tabel = querySrcMrFeatureByParams(markdown_flag=True)

    if "支线路合一" in board_type and is_change == False:
        global pr_bundle
        mgr_l_and_c_rdc_mr_split(board_tree, mr_tabel, pr_bundle, body_params, head_employ_no)
        return
    elif "支线路合一" in board_type and is_change == True:
        mod_type = l_mod_type + c_mod_type
        svc_type = l_svc + c_svc
    elif "线路侧" in board_type:
        mod_type = l_mod_type
        svc_type = l_svc
    elif "客户侧" in board_type:
        mod_type = c_mod_type
        svc_type = c_svc
    else:
        mod_type = ""
        svc_type = ""

    rdc_mr_traverse_split_by_pr(board_tree, mr_tabel, pr_table, svc_type, mod_type, body_params, head_employ_no)



