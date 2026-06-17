#!/usr/bin/python3
import re
import ast
from collections import defaultdict
from typing import List, Dict, Set
from electric_knowledge.front_net_business_model_data_service import querySrcNetBusinessByParams
from electric_knowledge.front_feature_board_relation_data_service import querySrcFeatureBoardRelation
import logging

logger = logging.getLogger("Logger")
#=================== 表1 ===================
# ------------------ 工具 ------------------
def parse_md_table_to_dict_list(md: str) -> List[Dict[str, str]]:
    lines = [ln.strip() for ln in md.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    header_line = lines[0]
    body_lines = [ln for ln in lines[1:] if not re.match(r'^\|[-:\s|]+$', ln)]
    headers = [h.strip() for h in header_line.strip('|').split('|')]
    rows = []
    for line in body_lines:
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows

def split_values(text: str) -> List[str]:
    return [v.strip() for v in text.split('/') if v.strip()]

def numeric_key(s: str) -> float:
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    return float(m.group(1)) if m else float('inf')

def sort_by_numeric(values: List[str]) -> List[str]:
    return sorted(set(values), key=numeric_key)

def join_unique(values: List[str]) -> str:
    return ','.join(values)

# ------------------ 核心业务流程 ------------------
def core_business_elements_process(input_md: str) -> str:
    rows = parse_md_table_to_dict_list(input_md)
    if not rows:
        return "| ID | 要素 | 因子 | 因子取值 | 变更分析 |\n| --- | --- | --- | --- | --- |\n"
    client_side = sort_by_numeric(
        split_values(rows[0]['入口光层业务']) +
        split_values(rows[-1]['出口光层业务'])
    )
    ne_models = sorted({v for r in rows for v in split_values(r['网元业务模型'])})
    line_side = []
    line_side.extend(split_values(rows[0]['出口光层业务']))
    for r in rows[1:-1]:
        line_side.extend(split_values(r['入口光层业务']))
        line_side.extend(split_values(r['出口光层业务']))
    line_side.extend(split_values(rows[-1]['入口光层业务']))
    line_side = sort_by_numeric(line_side)
    output_md = f"""
| ID | 要素 | 因子 | 因子取值 | 变更分析 |
| --- | --- | --- | --- | --- |
| 1  | 拓扑要素 | 拓扑因子 | CxL=LxC场景,CxL=LxL=LxC场景 |  |
| 2  | 业务要素 | 客户侧光层业务因子 | {join_unique(client_side)} |  |
| 3  | 业务要素 | 网元业务模型因子 | {join_unique(ne_models)} |  |
| 4  | 业务要素 | 线路侧光层业务因子 | {join_unique(line_side)} |  |
""".strip()
    return output_md

# ------------------ JSON 解析 ------------------
def parse_board_support_info_json(json_list: List[Dict]) -> List[str]:
    result: List[str] = []
    emitted: Set[str] = set()

    for item in json_list:
        ft = item.get("featureFirstType", "")
        sub_ft = item.get("subFeature", "")
        if ft not in {"高可用业务", "扩展应用业务"} or sub_ft:
            continue
        st = item.get("featureSecondType", "")
        prefix = st.split('业务')[0] if '业务' in st else None
        item_str = str(item)
        if item_str not in emitted:
            emitted.add(item_str)
            result.append(item_str)
    return result

# ------------------ 高可用 / 扩展应用要素 ------------------
expand_keywords: Dict[str, List[str]] = {
    "DM时延测量因子": ["DM时延", "DM单向时延", "DM双向时延"],
    "时钟时间因子": ["带内时钟", "带内时间"],
    "无损带宽调整": ["无损带宽", "lcas带宽容量"]
}
expand_single: Dict[str, str] = {
    "LLCF故障双向透传因子": "LLCF故障双向透传",
    "APR光功率自动降低因子": "APR光功率自动降低",
    "电监控因子": "电监控",
    "LF延迟下插因子": "LF延迟下插",
    "加密因子": "加密",
    "中断时间测量": "中断时间测量",
    "自动发现": "自动发现"
}
ha_map: Dict[str, Set[str]] = {
    "O保护因子": set(),
    "O恢复因子": set(),
    "FG保护因子": set(),
    "OSU保护因子": set(),
    "PKT保护因子": set(),
    "VC保护因子": set()
}

def extract_desc(feature: str) -> str:
    multi_str_keywords = [
            'O业务GCC-GFP协议电监控', 'O业务GCC-HDLC协议电监控', 
            'O业务国际-AES加密', 'O业务国密-SM加密',
            'O业务OTN-TTI自动发现', 'O业务以太网-LLDP邻居自动发现',
            'P业务终结OSU-DM双向时延测量', 'P业务终结OSU-DM单向时延测量',
            'P业务终结FG-DM双向时延测量', 'P业务终结FG-DM单向时延测量',
            'P业务终结ODU-DM双向时延测量', 'P业务终结ODU-DM单向时延测量'
        ]
    for keyword in multi_str_keywords:
        if keyword in feature:
            return '-'.join(feature.split('-')[-2:]).replace('特性', '').strip()
    return feature.split('-')[-1].replace('特性', '').strip()

ha_rows = []
expand_rows = []

def high_available_or_scalable_process_json(json_rows: List[str]) -> str:
    global ha_rows, expand_rows
    ha_rows.clear()
    expand_rows.clear()
    for value_set in ha_map.values():
        value_set.clear()
    idx = 1
    expand_map: Dict[str, Set[str]] = {k: set() for k in list(expand_keywords) + list(expand_single)}
    for row_str in json_rows:
        try:
            item = eval(row_str)
        except Exception:
            continue
        ft = item.get("featureFirstType", "")
        st = item.get("featureSecondType", "")
        feature = item.get("feature", "")
        net_model   = item.get("netBusinessModel", "")
        board_model = item.get("related_board_models", "").replace(",", "/")
        desc = extract_desc(feature)
        # print(desc)

        if ft == "扩展应用业务":
            for factor, keys in expand_keywords.items():
                for k in keys:
                    if k in feature:
                        expand_map[factor].add(desc)
                        expand_rows.append(f"| {idx} | {net_model} | {board_model} | 扩展应用要素 | {factor} | {desc} |  |")
            for factor, key in expand_single.items():
                if key in feature:
                    expand_map[factor].add(desc)
                    expand_rows.append(f"| {idx} | {net_model} | {board_model} | 扩展应用要素 | {factor} | {desc} |  |")
        elif ft == "高可用业务":
            prefix = st.split('业务')[0] if '业务' in st else None
            if prefix == "O":
                if 'wason' in desc:
                    ha_map["O恢复因子"].add(desc)
                    ha_rows.append(f"| {idx} | {net_model} | {board_model} | 高可用要素 | O恢复因子 | {desc} |  |")
                else:
                    ha_map["O保护因子"].add(desc)
                    ha_rows.append(f"| {idx} | {net_model} | {board_model} | 高可用要素 | O保护因子 | {desc} |  |")
            else:
                key_map = {'FG': 'FG保护因子', 'OSU': 'OSU保护因子',
                           'P': 'PKT保护因子', 'VC': 'VC保护因子'}
                if prefix in key_map:
                    ha_map[key_map[prefix]].add(desc)
                    ha_rows.append(f"| {idx} | {net_model} | {board_model} | 高可用要素 | {key_map[prefix]} | {desc} |  |")

    ha_order = ["O保护因子", "O恢复因子", "FG保护因子", "OSU保护因子", "PKT保护因子", "VC保护因子"]
    expand_order = [
        "LLCF故障双向透传因子", "APR光功率自动降低因子", "DM时延测量因子",
        "电监控因子", "LF延迟下插因子", "加密因子",
        "时钟时间因子", "无损带宽调整", "中断时间测量", "自动发现"
    ]
    lines = []
    for idx, factor in enumerate(ha_order, 5):
        content = ','.join(sorted(ha_map[factor])) if ha_map[factor] else ''
        lines.append(f"| {idx} | 高可用要素 | {factor} | {content} |  |")
    for idx, factor in enumerate(expand_order, 11):
        content = ','.join(sorted(expand_map[factor])) if expand_map[factor] else ''
        lines.append(f"| {idx} | 扩展应用要素 | {factor} | {content} |  |")
    # print(f"======= ha_rows: {ha_rows} \n  expand_rows: {expand_rows}==========")
    return '\n'.join(lines)

def extract_model_factors(table: str) -> str:
    """
    从给定的 Markdown 表格字符串中提取
    “网元业务模型因子” 对应的取值，并以
    “逗号分隔、无空格” 的字符串返回。
    """
    # 匹配含有“网元业务模型因子”的那一行
    pattern = re.compile(r'\|\s*\d+\s*\|\s*业务要素\s*\|\s*网元业务模型因子\s*\|\s*([^|]+)\s*\|')
    m = pattern.search(table)
    if not m:
        return ""

    # 去掉首尾空白，并按 “, ” 或 “,” 切分
    raw = m.group(1).strip()
    factors = [f.strip() for f in re.split(r'\s*,\s*', raw)]
    return ",".join(factors)

# def extract_unique_board_models(data: List[Dict[str, str]]) -> str:
#     """
#     提取所有 inputBoardBusinessModel / outputBoardBusinessModel 取值，
#     去重后按字母顺序排序，并以 “/” 拼接返回。
#     """
#     models = set()

#     for item in data:
#         # 处理 inputBoardBusinessModel
#         if item.get("inputBoardBusinessModel"):
#             for m in item["inputBoardBusinessModel"].split(","):
#                 models.add(m.strip())

#         # 处理 outputBoardBusinessModel
#         if item.get("outputBoardBusinessModel"):
#             for m in item["outputBoardBusinessModel"].split(","):
#                 models.add(m.strip())

#     return "/".join(sorted(models))


# 根据网元模型从原始需求表中获取单板模型
def extract_unique_board_models(md_str: str, net_mod: str) -> str:
    """
    提取指定网元业务模型对应的所有入口/出口单板类型，去重后按任意顺序输出。
    """
    wanted = {m.strip() for m in net_mod.split(',')}
    boards = set()

    for ln in md_str.splitlines()[2:]:
        cells = [c.strip() for c in ln.split('|')][1:-1]
        if len(cells) >= 9 and cells[2] in wanted:
            boards.update(re.split(r'[,，/]\s*', cells[4]))
            boards.update(re.split(r'[,，/]\s*', cells[7]))
    return '|'.join(boards)

# 从原始需求表中获取网元模型与单板模型对应关系
def build_model_board_map(md_str: str) -> List[Dict[str, str]]:
    """
    从第三行开始解析 Markdown 表格，排除表头及分隔线，
    生成每个网元业务模型唯一对应的入口+出口单板类型（去重后）。
    """
    mapping: Dict[str, List[str]] = {}   # 保持顺序去重

    # 按行读取，跳过前两行（表头+分隔线），第三行开始
    for ln in list(md_str.splitlines())[2:]:
        if not ln.strip() or '---' in ln:
            continue
        cells = [c.strip() for c in ln.split('|')][1:-1]
        if len(cells) < 9 or cells[2] == '网元业务模型':
            continue

        model, in_type, out_type = cells[2], cells[4], cells[7]
        boards = {b.strip() for b in re.split(r'[,，/]\s*', f"{in_type},{out_type}") if b}

        # 保持出现顺序去重
        seen = set(mapping.setdefault(model, []))
        mapping[model].extend(b for b in boards if b not in seen and not seen.add(b))

    # 组装结果
    return [{"netBusinessModel": m, "mod_type": ",".join(bs)} for m, bs in mapping.items()]
#=================== 表2 ===================
def extract_unique_models(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    提取每个方案的 netBusinessModel，
    并把该方案中 inputBoardBusinessModel 与 outputBoardBusinessModel
    出现过的所有取值去重后合并，用英文逗号连接。
    返回格式：
    [
        {"netBusinessModel": "...", "mod_type": "..."},
        ...
    ]
    """
    result = []

    for item in data:
        models = set()

        # 收集 input
        if item.get("inputBoardBusinessModel"):
            models.update(m.strip() for m in item["inputBoardBusinessModel"].split(","))

        # 收集 output
        if item.get("outputBoardBusinessModel"):
            models.update(m.strip() for m in item["outputBoardBusinessModel"].split(","))

        # 按字母排序后拼接
        mod_type = ",".join(sorted(models)) if models else ""

        result.append({
            "netBusinessModel": item.get("netBusinessModel", ""),
            "mod_type": mod_type
        })

    return result

def enrich_features_with_net_models(
    input1: List[Dict[str, str]],
    input2: List[str]            # 注意：这里传的是字符串列表
) -> List[str]:
    """
    1. 为每条 feature 字符串计算 netBusinessModel 并追加；
    2. 返回仍保持字符串列表，格式与需求示例一致。
    """
    # 1. 建立板模型 -> netBusinessModel 集合 映射
    board2net: Dict[str, Set[str]] = {}
    for item in input1:
        nb = item["netBusinessModel"]
        for m in item["mod_type"].split(","):
            m = m.strip()
            if m:
                board2net.setdefault(m, set()).add(nb)

    # 2. 逐条处理
    enriched: List[str] = []
    for feat_str in input2:
        feat_dict: Dict[str, str] = ast.literal_eval(feat_str)

        union: Set[str] = set()
        for m in feat_dict["related_board_models"].split(","):
            m = m.strip()
            if m in board2net:
                union.update(board2net[m])

        # 追加字段
        feat_dict["netBusinessModel"] = "/".join(sorted(union))

        # 重新变成字符串（保持单引号风格，与输入一致）
        enriched.append(str(feat_dict))

    return enriched

def expand_business_factor(md_table: str) -> str:
    """
    把输入的 Markdown 表格中“业务要素”行按“因子取值”拆成多行，
    并补充“网元业务模型 | 单板原子模型”两列，全部填 xx。
    """
    lines = [ln.strip() for ln in md_table.splitlines() if ln.strip()]
    if len(lines) < 2:
        return md_table

    # 1. 解析表头
    header = [c.strip() for c in lines[0].split('|') if c.strip()]
    sep    = lines[1]

    # 2. 找到“要素”“因子取值”列索引
    try:
        ele_idx  = header.index('要素')
        val_idx  = header.index('因子取值')
    except ValueError as e:
        raise ValueError('输入表格缺少必要列：要素、因子取值') from e

    # 3. 构造新表头
    new_header = ['ID', '网元业务模型', '单板原子模型'] + header
    # 把“ID”列重新放到最前
    id_idx = header.index('ID')
    new_header = ['ID', '网元业务模型', '单板原子模型'] + \
                 [h for i, h in enumerate(header) if i != id_idx]

    new_sep = '| --- ' * len(new_header) + '|'

    # 4. 处理数据行（只保留“业务要素”）
    new_rows: List[str] = []
    for ln in lines[2:]:
        cols = [c.strip() for c in ln.split('|') if c.strip()]
        if cols[ele_idx] != '业务要素':
            continue

        vals = [v.strip() for v in cols[val_idx].split(',') if v.strip()]
        for v in vals:
            new_cols = cols.copy()
            new_cols[val_idx] = v
            # 重新排序：ID 列放最前
            row_id = new_cols[id_idx]
            rest   = [c for i, c in enumerate(new_cols) if i != id_idx]
            # 插入两列 xx
            new_row = [row_id, 'xx', 'xx'] + rest
            new_rows.append('| ' + ' | '.join(new_row) + ' |')

    # 5. 拼接输出
    return '| ' + ' | '.join(new_header) + ' |\n' + new_sep + '\n' + '\n'.join(new_rows) + "\n"

def renumber_md_table(md: str) -> str:
    """
    将 Markdown 表格中 ID 列重新编号为 1,2,3...
    仅处理包含表头、分隔符和数据行的标准 Markdown 表格。
    """
    lines = [ln.rstrip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 3:
        return md  # 不足表头+分隔+数据，原样返回

    header, sep, *data = lines
    new_lines = [header, sep]

    # 找到 ID 列索引
    cols_head = [c.strip() for c in header.split('|') if c.strip()]
    try:
        id_idx = cols_head.index('ID')
    except ValueError:
        return md  # 无 ID 列

    # 逐行重编号
    for new_id, ln in enumerate(data, start=1):
        cells = [c.strip() for c in ln.split('|')][1:-1]  # 去掉左右空
        cells[id_idx] = str(new_id)
        new_line = '| ' + ' | '.join(cells) + ' |'
        new_lines.append(new_line)

    return '\n'.join(new_lines)

# ------------------ 表1主入口 ------------------
def svc_atom_net_essential_expression(input_md: str, hd_req: str, mid_flag:bool=False) -> str:
    # 核心业务要素
    core_svc = core_business_elements_process(input_md)
    # print(core_svc)

    # 获取网络模型并集
    net_model = extract_model_factors(core_svc)
    # print(f"net_model: {net_model}")

    # 根据网络模型获取所有单板模型
    # query_params:dict = {"netBusinessModel": net_model}
    # mod_info = querySrcNetBusinessByParams(query_params, markdown_flag=True)
    mod_type = extract_unique_board_models(hd_req, net_model)
    # logger.info(f"1111mod_type: {mod_type}")
    
    # 根据单板模型获取特性和子特性
    board_mod_features = querySrcFeatureBoardRelation(mod_type.replace('|',','))
    features = parse_board_support_info_json(board_mod_features)
    # logger.info(f"features:{features}")

    # 获取网元与单板模型对应表
    # net_mod_table = extract_unique_models(mod_info)
    net_mod_table = build_model_board_map(hd_req)
    # logger.info(f"2222net_mod_table: {net_mod_table}")

    # 获取包含单板模型和网元业务模型的特性子特性列表
    tb_list = enrich_features_with_net_models(net_mod_table, features)
    h_av_sc = high_available_or_scalable_process_json(tb_list)
    # logger.info(f"h_av_sc: {h_av_sc}")

    if mid_flag:
        mid_table = expand_business_factor(core_svc)
        # print(mid_table)
        for ha in ha_rows:
            mid_table += ha + "\n"
        for expand in expand_rows:
            mid_table += expand + "\n"
        return renumber_md_table(mid_table)
    else:
        return core_svc + '\n' + h_av_sc
