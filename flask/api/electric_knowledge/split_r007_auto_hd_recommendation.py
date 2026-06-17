#!/usr/bin/python3
import re
from itertools import chain
from collections import defaultdict
from functools import partial
from typing import List, Dict, Set, Any, Tuple, Optional, Union
from electric_knowledge.front_board_tree_data_service import querySrcBoardTreeByParams
from electric_knowledge.front_net_business_model_data_service import querySrcNetBusinessByParams
from electric_knowledge.front_business_speed_type_relation_data_service import querySrcBusinessSpeedTypeByParams
from electric_knowledge.front_board_atom_model_relation_data_service import querySrcBoardBusinessAtomByParams
from electric_knowledge.utils_pub import pub_get_column_values_from_markdown_table, pub_dict_list_to_markdown_table_reordered
import logging

logger = logging.getLogger("Logger")

# ---------- 工具 ----------
no_svc_models = ['B_V_FG', 'B_FG_O', 'B_OSU_O', 'B_V_O']

def board_name_format(board_name: str) -> str:
    """
    将单板名称和端口列表转换为指定格式的字符串。
    规则：
    1. 若括号内为纯数字/字母/混合的代码（如“(80A1H)”），则去掉该括号及其内容。
    2. 若括号内为纯字母（如“(FG)”），则保留该括号及其内容。
    3. 若同时出现“(FG)(80A1H)”形式，仅保留“(FG)”部分。
    """
    # 用正则匹配所有括号内容
    matches = re.findall(r'\(([^)]+)\)', board_name)
    if not matches:
        prefix = board_name
    else:
        alpha_brackets = [m for m in matches if m.isalpha()]
        if alpha_brackets:
            keep = alpha_brackets[0]
            idx = board_name.find(f'({keep})') + len(keep) + 2
            prefix = board_name[:idx]
        else:
            prefix = re.sub(r'\([^)]*\)', '', board_name)

    return prefix

def get_board_name_by_tree(product_forms: str, board_type: str, mod_type: str, svc_type: str, client_flag: bool = True):
    if '客户侧' in board_type:
        factor = "客户侧电层业务"
    else:
        factor = "线路侧电层业务"

    if mod_type in no_svc_models:
        params = {
            "factorTypeCn":"产品,板卡类型,单板业务模型",
            "factorValue": product_forms + "," + "桥接B卡" + "," + mod_type
        }
    else:
        params = {
            "factorTypeCn":"产品,板卡类型,单板业务模型," + factor,
            "factorValue": product_forms + "," + board_type + "," + mod_type + "," + svc_type
        }

    resps = querySrcBoardTreeByParams(params, markdown_flag=True)
    # logger.info(f"---params: {params}-")
    # logger.info(f"---resps: {resps}---")
    return resps

def clean_list(s: str) -> List[str]:
    return [part.strip() for part in re.sub(r"[，,]\s*", ",", s or "").split(",") if part.strip()]

def extract_client_side(hd_req: List[Dict[str, str]]) -> Tuple[Set[str], Set[str]]:
    if len(hd_req) < 2:
        return set(), set()
    first, last = hd_req[1], hd_req[-1]
    boards = set(clean_list(first.get("入口单板模型", "")))
    boards.update(clean_list(last.get("出口单板模型", "")))
    services = set(clean_list(first.get("入口业务类型", "")))
    services.update(clean_list(last.get("出口业务类型", "")))
    # 单板模型分组
    g_boards = group_board_model_list(boards)

    return g_boards, services

def extract_line_side(hd_req: List[Dict[str, str]]) -> Tuple[Set[str], Set[str]]:
    if len(hd_req) < 2:
        return set(), set()
    boards, services = set(), set()

    first, last = hd_req[1], hd_req[-1]
    boards.update(clean_list(first.get("出口单板模型", "")))
    services.update(clean_list(first.get("出口业务类型", "")))
    boards.update(clean_list(last.get("入口单板模型", "")))
    services.update(clean_list(last.get("入口业务类型", "")))
    if len(hd_req) > 2:
        for row in hd_req[2:-1]:
            boards.update(clean_list(row.get("入口单板模型", "")))
            boards.update(clean_list(row.get("出口单板模型", "")))
            services.update(clean_list(row.get("入口业务类型", "")))
            services.update(clean_list(row.get("出口业务类型", "")))
    g_boards = group_board_model_list(boards)

    return g_boards, services

def is_valid_svc_and_board_model(svc: str, model: str, src_hd_req: List[Dict[str, str]]) -> bool:
    for row in src_hd_req:
        # 处理入口单板模型（分割并清理空格）
        entry_boards = [
            board.strip() 
            for board in row.get("入口单板模型", "").split(",") 
            if board.strip()  # 过滤空字符串
        ]
        
        # 处理出口单板模型
        exit_boards = [
            board.strip() 
            for board in row.get("出口单板模型", "").split(",") 
            if board.strip()
        ]
        
        # 处理业务类型（同样分割为列表进行精确匹配）
        entry_svcs = [
            svc_type.strip() 
            for svc_type in row.get("入口业务类型", "").split("/") 
            if svc_type.strip()
        ]
        
        exit_svcs = [
            svc_type.strip() 
            for svc_type in row.get("出口业务类型", "").split("/") 
            if svc_type.strip()
        ]
        
        # 精确匹配检查
        entry_valid = (svc in entry_svcs) and (model in entry_boards)
        exit_valid = (svc in exit_svcs) and (model in exit_boards)
        
        if entry_valid or exit_valid:
            return True
    
    return False

def group_board_model_list(boards: Set[str]) -> Dict[str, List[str]]:
    gs_board_type = querySrcBoardBusinessAtomByParams({}, markdown_flag=True)
    type_map = {d["boardBusiness"]: d["boardBusinessType"] for d in gs_board_type}
    groups: Dict[str, List[str]] = {}
    for m in boards:
        t = type_map.get(m, "未知分类")
        groups.setdefault(t, []).append(m)
    return groups

# ---------- Markdown 解析 ----------
def parse_md_table_to_dict(md: str) -> List[Dict[str, str]]:
    lines = [ln.strip() for ln in md.strip().splitlines() if ln.strip()]
    if not lines or not lines[0].startswith("|"):
        return []

    header_line = lines[0].strip()
    if not (header_line.startswith("|") and header_line.endswith("|")):
        return []
    headers = [h.strip() for h in header_line[1:-1].split("|")]

    data_lines = [ln for ln in lines[1:] if not ln.startswith("|---")]
    rows = []
    for ln in data_lines:
        if not (ln.startswith("|") and ln.endswith("|")):
            continue
        parts = [p.strip() for p in ln[1:-1].split("|")]
        if len(parts) == len(headers):
            rows.append(dict(zip(headers, parts)))
    return rows

# 1 中间过程数据表
def intermediate_process_data_table(hd_req: List[Dict[str, str]]) -> str:
    if len(hd_req) < 2:                      # 空数据保护
        return "无数据"

    # 客户侧
    client_groups, client_services = extract_client_side(hd_req)
    #print(f"----- client_groups:{client_groups}\n client_services:{client_services}----------")

    # 线路侧
    line_groups, line_services = extract_line_side(hd_req)
    #print(f"----- line_groups:{line_groups}\n line_services:{line_services}----------")

    md = ["",
          "| 业务类型 | 单板分类 | 原始需求分组的单板模型列表 | 单板表中单板业务模型 | 推荐单板名称 |",
          "| --- | --- | --- | --- | --- |"]
    for svc in sorted(client_services):
        for tp, models in sorted(client_groups.items()):
            md.append(f"| {svc} | {tp} | {','.join(sorted(models))} |  |  |")
    for svc in sorted(line_services):
        for tp, models in sorted(line_groups.items()):
            md.append(f"| {svc} | {tp} | {','.join(sorted(models))} |  |  |")

    return "\n".join(md)

RDC_TABLE = {
  "业务类型": "OTNSW",
  "单板分类": "测试RDC接口需要",
  "原始需求数据表中提取的单板模型": "456",
  "单板表中单板业务模型": "123",
  "推荐单板名称": "PR",
}
# 1 中间过程数据表
def process_board_val_by_tree(
    client_services: Set[str],
    client_groups: Dict[str, List[str]],
    product_form: str,
    src_hd_req: List[Dict[str, str]],
    client_flag: bool = True
) -> List[Dict[str, str]]:
    """
    处理客户侧业务类型和单板模型，生成推荐单板记录。

    :param client_services: 客户侧业务类型集合
    :param client_groups: 客户侧单板分组
    :param product_form: 产品形态
    :param results: 存储最终结果的列表
    :src_hd_req 原始需求数据表
    """
    results = []

    for svc in sorted(client_services):
        for tp, models in sorted(client_groups.items()):
            for model in sorted(models):
                """
                通过和原始需求表进行校验, 增加业务类型svc和单板模型model有效性校验
                """
                if not is_valid_svc_and_board_model(svc, model, src_hd_req):
                    continue
                ret_infos = get_board_name_by_tree(product_form, tp, model, svc, client_flag)
                if len(ret_infos) > 0:
                    for ret in ret_infos:
                        #print(f"lsa==========ret:{ret}")
                        board_name = board_name_format(ret.get('board'))
                        cf_mod = ret.get('单板业务模型')
                        record = RDC_TABLE.copy()
                        if model in no_svc_models:
                            record["业务类型"] = "--"
                        else:
                            record["业务类型"] = str(svc)
                        record["单板分类"] = str(tp)
                        record["原始需求数据表中提取的单板模型"] = str(model)
                        record["单板表中单板业务模型"] = str(cf_mod).replace('|', '/')
                        record["推荐单板名称"] = str(board_name)
                        results.append(record)
                else:
                    record = RDC_TABLE.copy()
                    if model in no_svc_models:
                        record["业务类型"] = "--"
                    else:
                        record["业务类型"] = str(svc)
                    record["单板分类"] = str(tp)
                    record["原始需求数据表中提取的单板模型"] = str(model)
                    record["单板表中单板业务模型"] = ""
                    record["推荐单板名称"] = ""
                    results.append(record)
    return results



def convert_to_markdown_table(input_data: List[Dict[str, str]], head: bool = True) -> str:
    """
    将输入数据转换为 Markdown 表格格式。
    :param input_data: 输入的列表数据，每一项是一个字典
    :param head: 是否包含表头，默认为 True
    :return: Markdown 格式的字符串
    """
    # 创建一个列表来存储所有行的数据
    rows = []
    
    # 遍历输入数据，提取所需字段并格式化
    for item in input_data:
        # 提取字段值
        business_type = item.get("业务类型", "")
        board_category = item.get("单板分类", "")
        original_model = item.get("原始需求数据表中提取的单板模型", "")
        board_model = item.get("单板表中单板业务模型", "")
        recommended_board = item.get("推荐单板名称", "")
        # 将提取的数据添加到行列表中
        rows.append([business_type, board_category, original_model, board_model, recommended_board])
    # 创建 Markdown 表格字符串
    if head:
        # 定义输出的表头
        headers = ["业务类型", "单板分类", "原始需求分组的单板模型列表", "单板表中单板业务模型", "推荐单板名称"]
        markdown_table = "| " + " | ".join(headers) + " |\n"
        markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    else:
        markdown_table = ""
    # 如果没有数据，直接返回空字符串
    if not rows:
        return markdown_table
    for row in rows:
        markdown_table += "| " + " | ".join(row) + " |\n"
    return markdown_table

def get_recommend_board_table(product_form: str, mgr_hd_req: List[Dict[str, str]], src_hd_req: List[Dict[str, str]]) -> str:
    if len(mgr_hd_req) < 2:
        return "无数据"
    # 客户侧
    client_groups, client_services = extract_client_side(mgr_hd_req)

    # 线路侧
    line_groups, line_services = extract_line_side(mgr_hd_req)

    # 调用封装后的函数处理客户侧业务类型和单板模型
    client_results = process_board_val_by_tree(client_services, client_groups, product_form, src_hd_req, True)
    markdown_table = convert_to_markdown_table(client_results, True)

    # 处理线路侧业务类型和单板模型
    line_results = process_board_val_by_tree(line_services, line_groups, product_form, src_hd_req, False)
    markdown_table += convert_to_markdown_table(line_results, False)

    return markdown_table

#==============================================
# ---------- 1. 速率映射 ----------
def get_speed_by_type(data: List[Dict], biz_type: str) -> Optional[str]:
    """
    根据业务类型字符串（如 "800GE"）返回对应的 businessSpeed。
    若未匹配到，返回 None。
    """
    for item in data:
        # 按逗号拆分成列表并去掉首尾空格
        types = [t.strip() for t in item.get("businessType", "").split(",")]
        if biz_type in types:
            return item.get("businessSpeed")
    return ""

# 根据单板业务模型获取入口和出口单板列表
def get_board_models_by_netmodel(net_model: str) -> Tuple[List[str], List[str]]:
    """
    修复：永远返回两个列表，而不是 None
    """
    query_params:dict = {"netBusinessModel": net_model}
    item = querySrcNetBusinessByParams(query_params, markdown_flag=True)
    if len(item) > 0:
        return (
                [m.strip() for m in item[0].get("inputBoardBusinessModel", "").split(",")],
                [m.strip() for m in item[0].get("outputBoardBusinessModel", "").split(",")]
            )
    return [], []

# 根据原始需求表中获取首次匹配的入口和出口单板列表
def get_board_models_by_original_require_table(md_table: str, netmodel: str) -> Tuple[List[str], List[str]]:
    """
    仅取**首次**出现的同名网元业务模型行，
    返回去重后的入口单板模型列表和出口单板模型列表。
    """
    lines = [ln.rstrip() for ln in md_table.splitlines() if ln.strip()]
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.split('|')][1:-1]
        if len(cells) < 9:
            continue
        if cells[2] == netmodel:
            in_raw  = re.split(r'[,，/]\s*', cells[4])
            out_raw = re.split(r'[,，/]\s*', cells[7])
            return sorted(dict.fromkeys(filter(None, in_raw))), \
                   sorted(dict.fromkeys(filter(None, out_raw)))

    return [], []

# ---------- 2. 解析 Markdown 表 ----------
def parse_md_table_to_list(md: str) -> List[Dict[str, str]]:
    """
    把 Markdown 表格字符串解析成字典列表
    支持 | 头1 | 头2 | 头3 | 这样的标准写法
    业务类型为 '--' 的数据也会被正常保留
    """
    # print(f"11111111 {md} ")
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    if not lines:
        return []

    # 真正的分隔行：整行只包含 |、空格、冒号、连字符
    sep_re = re.compile(r'^\|?[\s:|-]+\|$')

    # 如果第二行是分隔行就把它去掉，否则不动
    if len(lines) >= 2 and sep_re.match(lines[1]):
        lines.pop(1)

    if not lines:
        return []

    # 表头
    header_line = lines.pop(0)
    headers = [h.strip() for h in header_line.strip('|').split('|')]

    # 其余全是数据
    data = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip('|').split('|')]
        data.append(dict(zip(headers, cells)))
    # print(f"22222222 {data} ")
    return data

# ---------- 3. 主函数 ----------
def get_recommend_pairs(md_table: str, model_list: List[str]) -> List[Tuple[str, str]]:
    """
    返回 [(推荐单板名称, 速率), ...] 的平铺列表
    """
    targets = set(model_list)
    rows = parse_md_table_to_list(md_table)
    res = []
    rate_table = querySrcBusinessSpeedTypeByParams({}, markdown_flag=True)
    # print(f"------------rows:{rows}")
    for row in rows:
        models = [m.strip() for m in row.get("原始需求分组的单板模型列表", "").split(",")]
        #print(f"row:{row}, models:{models}")
        if any(m in targets for m in models):
            board = row.get("推荐单板名称", "").strip()
            rate = get_speed_by_type(rate_table, row.get("业务类型", "").strip())
            if rate:
                res.append((board, rate))
            if "--" == row.get("业务类型"):
                res.append((board, "--"))
    return res

def list_netmodels(md: str, product_name: str = "") -> List[str]:
    """
    只返回「业务要素 → 网元业务模型」里的所有模型名称。
    当 product_name 为：
        - "M721"  时，过滤掉包含 "OTN-LB" 的模型；
        - "19700" 时，过滤掉包含 "OTN-CB" 的模型；
    其他值或空字符串不做任何过滤。
    """
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    models = []

    # 正则：捕获“业务要素 | 网元业务模型 | 取值”这一行
    pattern = re.compile(
        r'\|\s*\d+\s*\|\s*业务要素\s*\|\s*网元业务模型因子\s*\|\s*([^|]+?)\s*\|',
        flags=re.I
    )

    # 根据 product_name 决定过滤关键字
    if product_name == "M721产品":
        bad_kw = "OTN-LB"
    elif product_name == "19700产品":
        bad_kw = "OTN-CB"
    else:
        bad_kw = None

    for line in lines:
        m = pattern.search(line)
        if m:
            raw = m.group(1).strip()
            # 按逗号/空格分割并去空
            for model in filter(None, re.split(r'[,，\s/]+', raw)):
                model = model.strip()
                if bad_kw and bad_kw in model:
                    continue
                models.append(model)

    return models

def net_hardware_deployment_table(req: str, net_md: str, mid_md: str, product_name: str = ""):
    nets = list_netmodels(net_md, product_name)
    hdr = "| 网元业务模型 | 入口单板 | 出口单板 | 变更分析 |\n| --- | --- | --- | --- |"
    rows = []

    for net in nets:
        # in_models, out_models = get_board_models_by_netmodel(net)
        in_models, out_models = get_board_models_by_original_require_table(req, net)
        logger.info(f"net: {net}, in_models: {in_models}, out_models: {out_models}")
        # ------------ 入口 ------------
        in_merged = defaultdict(set)
        for name, val in get_recommend_pairs(mid_md, list(dict.fromkeys(in_models))):
            if name:                       # 过滤空 key
                in_merged[name].add(val)

        in_str = ','.join(
            f"{{{k}, {list(dict.fromkeys(v))}}}"
            for k, v in in_merged.items()
            if v  # 跳过空集合
        ) or ''                           # 完全为空时返回空字符串

        # ------------ 出口 ------------
        out_merged = defaultdict(set)
        for name, val in get_recommend_pairs(mid_md, list(dict.fromkeys(out_models))):
            if name:
                out_merged[name].add(val)

        out_str = ','.join(
            f"{{{k}, {list(dict.fromkeys(v))}}}"
            for k, v in out_merged.items()
            if v
        ) or ''

        rows.append(f"| {net} | {in_str} | {out_str} |  |")

    return hdr + "\n" + "\n".join(rows)

# ---------- 1. 解析硬件部署表 ----------
def parse_hw_table(md: str) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """
    解析新版 Markdown 硬件部署表
    返回: { 网元业务模型: { "input": [...], "output": [...] } }
    其中 [...] 内每一项为 {"board": 单板名, "rate": 速率}
    """
    # 去掉表头/分隔线，仅保留数据行
    rows = [
        line.strip("|").split("|") for line in md.splitlines()
        if line.strip() and not re.match(r"^\|? *:?-+:? *\|", line)
    ]
    if not rows:
        return {}

    headers = [h.strip() for h in rows[0]]
    data_rows = [dict(zip(headers, [c.strip() for c in row])) for row in rows[1:]]

    hw: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

    # 正则：{单板名, ['r1', 'r2', ...]}
    pattern = re.compile(r"\{([^,]+),\s*\[([^\]]+)\]\}")

    for row in data_rows:
        model = row["网元业务模型"]
        hw.setdefault(model, {})

        # 入口单板
        in_items = []
        for m in pattern.finditer(row.get("入口单板", "")):
            board = m.group(1).strip()
            rates = [r.strip().strip("'") for r in m.group(2).split(",")]
            for rate in rates:
                in_items.append({"board": board, "rate": rate})
        hw[model]["input"] = in_items

        # 出口单板
        out_items = []
        for m in pattern.finditer(row.get("出口单板", "")):
            board = m.group(1).strip()
            rates = [r.strip().strip("'") for r in m.group(2).split(",")]
            for rate in rates:
                out_items.append({"board": board, "rate": rate})
        hw[model]["output"] = out_items

    return hw

# 从硬件需求表中获取单板名称列表
def get_board_names(md_str: str) -> List[str]:
    """
    从 Markdown 表格中提取“单板名称”列（首列）并返回列表。
    跳过表头与分隔线行。
    """
    names: List[str] = []
    for ln in md_str.splitlines()[2:]:        # 跳过表头+分隔线
        if not ln.strip() or '---' in ln:
            continue
        # 按竖线分割后取第 1 列
        cell = ln.split('|')[1].strip()
        if cell and cell != '单板名称':        # 排除表头字段
            names.append(cell)
    return names

# 优先选择硬件需求表中单板作为推荐单板
def filter_md_recommended_only(md_str: str, allowed: List[str]) -> str:
    allowed_set = set(allowed)
    lines = [ln.rstrip() for ln in md_str.splitlines()]
    if len(lines) < 3:
        return md_str

    header, sep, *body = lines
    key_cols = (0, 1, 2)   # 业务类型、单板分类、原始需求分组
    groups: dict[tuple, List[int]] = {}   # key -> list of body line indices
    keep = [True] * len(body)

    # 先扫描建立分组
    for idx, ln in enumerate(body):
        if not ln.strip() or '---' in ln:
            continue
        cells = [c.strip() for c in ln.split('|')][1:-1]
        if len(cells) < 5:          # 字段不足
            continue
        key = tuple(cells[i] for i in key_cols)
        groups.setdefault(key, []).append(idx)

    # 对每组决定是否过滤
    for key, idx_list in groups.items():
        # 该组是否有推荐单板在 allowed
        has_allowed = any(
            cells[4].strip() in allowed_set
            for i in idx_list
            for cells in [body[i].split('|')[1:-1]]
        )
        if has_allowed:
            for i in idx_list:
                cells = body[i].split('|')[1:-1]
                if cells[4].strip() not in allowed_set:
                    keep[i] = False
        # 组内无 allowed 时无需处理，全部保留

    # 重新组装正文
    new_body = [ln for i, ln in enumerate(body) if keep[i]]
    return '\n'.join([header, sep] + new_body)

# ---------- 2. 过滤单板（去掉灰光/彩光后缀） ----------
def normalize_rate(rate: str) -> str:
    """'2.5G及以下灰光' → '2.5G及以下'"""
    return re.sub(r"(灰光|彩光)$", "", rate).strip()

def filter_boards(hw: Dict[str, Dict[str, List[str]]],
                  net_model: str,
                  in_rate: str,
                  out_rate: str) -> Tuple[List[str], List[str]]:
    in_rate = normalize_rate(in_rate)
    out_rate = normalize_rate(out_rate)
    # print(f"hw: {hw}, in_rate: {in_rate}, net_model: {net_model}, out_rate: {out_rate}\n")
 
    if net_model not in hw:
        return [], []

    in_boards = [blk["board"] for blk in hw[net_model]["input"]
                 if in_rate in normalize_rate(blk["rate"])]

    out_boards = [blk["board"] for blk in hw[net_model]["output"]
                  if out_rate in normalize_rate(blk["rate"])]
    #print(f"in_rate: {in_rate}, in_boards: {in_boards}, net_model: {net_model}, out_rate: {out_rate}, out_boards: {out_boards}\n")
    return in_boards, out_boards

def filter_boards_cb(hw: Dict[str, Dict[str, List[str]]],
                  net_model: str,
                  in_rate: str,
                  out_rate: str) -> Tuple[List[str], List[str], List[str]]:
    in_rate = normalize_rate(in_rate)
    out_rate = normalize_rate(out_rate)
    # print(f"hw: {hw}, in_rate: {in_rate}, net_model: {net_model}, out_rate: {out_rate}\n")
 
    if net_model not in hw:
        return [], []
            
    in_boards = [blk["board"] for blk in hw[net_model]["input"]
                 if in_rate in normalize_rate(blk["rate"])]

    out_boards = [blk["board"] for blk in hw[net_model]["output"]
                  if out_rate in normalize_rate(blk["rate"])]

    b_boards =  [blk['board'] for blk in hw[net_model]['input'] 
                 if blk.get('rate') == '--']

    logger.info(f"in_rate: {in_rate}, in_boards: {in_boards}, net_model: {net_model}, out_rate: {out_rate}, out_boards: {out_boards}, b_boards: {b_boards}\n")
    return in_boards, out_boards, b_boards

# ---------- 3. 正交并镜像 ----------
def orthogonal_mirror(in_boards: List[str], out_boards: List[str]) -> List[str]:
    if not in_boards or not out_boards:
        return []
    return [f"{c} x {l} == {l} x {c}" for c in in_boards for l in out_boards]

def orthogonal_mirror_ll(in_boards: List[str], out_boards: List[str], ll_out_boards: List[str]) -> List[str]:
    if not in_boards or not out_boards or not ll_out_boards:
        return []
    return [f"{c} x {l1} == {l1} x {l2} == {l2} x {c}" for c in in_boards for l1 in out_boards for l2 in ll_out_boards]

def orthogonal_mirror_cb(in_boards: List[str], out_boards: List[str], bridge_boards: List[str]) -> List[str]:
    if not in_boards or not out_boards or not bridge_boards:
        return []
    return [f"{c} x {b} x {l} == {l} x {b} x {c}" for c in in_boards for l in out_boards for b in bridge_boards]

def orthogonal_mirror_ll_cb(in_boards: List[str], out_boards: List[str], ll_out_boards: List[str], bridge_boards: List[str]) -> List[str]:
    if not in_boards or not out_boards or not ll_out_boards or not bridge_boards:
        return []
    return [f"{c} x {b} x {l1} == {l1} x {l2} == {l2} x {b} x {c}" for c in in_boards for l1 in out_boards for l2 in ll_out_boards for b in bridge_boards]



def slice_hardware_deployment(m, hw):
    inner = m.group(0)
    fields = re.findall(r"'([^']*)'", inner)
    # logger.info(f"-------fields:{fields}")
    cnt = len(fields)
    if cnt not in {4, 5, 6, 7}:
        return inner

    scheme, *tail = fields
    lines = []

    # 公共逻辑封装
    def add_line(fmt: str, *args):
        lines.append(fmt.format(*args))

    if cnt == 4:
        in_rate, model, out_rate = tail 
        if "OTN-CB" in model:
            ib, ob, bb = filter_boards_cb(hw, model, in_rate, out_rate)
            coms = orthogonal_mirror_cb(ib, ob, bb)
        else:
            ib, ob = filter_boards(hw, model, in_rate, out_rate)
            coms = orthogonal_mirror(ib, ob)
        for p in coms:
            add_line('["{}", "{}", "{}", "{}"], "{}"', scheme, in_rate, model, out_rate, p)

    elif cnt == 5:
        in_rate, model, out_rate, bh = tail
        if "OTN-CB" in model:
            ib, ob, bb = filter_boards_cb(hw, model, in_rate, out_rate)
            coms = orthogonal_mirror_cb(ib, ob, bb)
        else:
            ib, ob = filter_boards(hw, model, in_rate, out_rate)
            coms = orthogonal_mirror(ib, ob)
        for p in coms:
            add_line('["{}", "{}", "{}", "{}", "{}"], "{}"', scheme, in_rate, model, out_rate, bh, p)

    elif cnt == 6:
        c_in, c_model, c_out, ll_model, ll_out = tail
        if "OTN-CB" in c_model:
            ib1, ob1, bb1 = filter_boards_cb(hw, c_model, c_in, c_out)
            ib2, ob2, bb2 = filter_boards_cb(hw, ll_model, c_out, ll_out)
            coms = orthogonal_mirror_ll_cb(ib1, ob1, ob2, bb1)
        else:
            ib1, ob1 = filter_boards(hw, c_model, c_in, c_out)
            ib2, ob2 = filter_boards(hw, ll_model, c_out, ll_out)
            coms = orthogonal_mirror_ll(ib1, ob1, ob2)
        for p in coms:
            add_line('["{}", "{}", "{}", "{}", "{}", "{}"], "{}"', scheme, c_in, c_model, c_out, ll_model, ll_out, p)

    else:  # cnt == 7
        c_in, c_model, c_out, ll_model, ll_out, bh = tail
        if "OTN-CB" in c_model:
            ib1, ob1, bb1 = filter_boards_cb(hw, c_model, c_in, c_out)
            ib2, ob2, bb2 = filter_boards_cb(hw, ll_model, c_out, ll_out)
            coms = orthogonal_mirror_ll_cb(ib1, ob1, ob2, bb1)
        else:
            ib1, ob1 = filter_boards(hw, c_model, c_in, c_out)
            ib2, ob2 = filter_boards(hw, ll_model, c_out, ll_out)
            coms = orthogonal_mirror_ll(ib1, ob1, ob2)
        for p in coms:
            add_line('["{}", "{}", "{}", "{}", "{}", "{}", "{}"], "{}"', scheme, c_in, c_model, c_out, ll_model, ll_out, bh, p)

    inner = inner.replace('(', '[').replace(')', ']').replace("'", "").replace('"', '')
    #inner = re.search(r'\((.*)\)', inner).group(1)
    return "\n".join(lines) if lines else inner

def svc_slice_hardware_deployment(txt: str, hw_md: str) -> str:
    hw = parse_hw_table(hw_md)
    lines = txt.splitlines(keepends=True)
    tuple_pat = re.compile(r"\([^)]*\)")
    new_lines = []

    for line in lines:
        if not tuple_pat.search(line):
            new_lines.append(line)
            continue

        new_line = tuple_pat.sub(partial(slice_hardware_deployment, hw=hw), line)
        new_lines.append(new_line)

    return ''.join(new_lines)


# 从要素化表达中提取业务要素
def extract_top_n_md_rows(md_string: str, n: int) -> str:
    """
    从 Markdown 格式的字符串中提取前 n 行数据，并返回新的 Markdown 格式的字符串。

    :param md_string: 输入的 Markdown 格式字符串
    :param n: 要提取的行数
    :return: 提取后的 Markdown 格式字符串
    """
    # 按行分割输入的 Markdown 字符串
    lines = md_string.strip().split('\n')

    # 提取表头部分（前3行）
    header = lines[:3]

    # 提取数据部分的前 n 行
    data = lines[3:3+n]

    # 将表头和数据部分合并
    result = header + data

    # 将结果合并为一个新的字符串
    return '\n'.join(result)

# 获取单产品形态数据
def filter_product_by_name(md_str: str, product_name: str) -> str:
    """
    根据产品形态名称过滤 Markdown 表格中的行。
    如果 product_name == '721'，额外剔除网元业务模型中包含 'OTN-LB' 的行。
    """
    md_str = md_str.replace('/', ',')
    lines = md_str.strip().splitlines()
    # 1. 找到表头
    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("| 站点名称"):
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("未找到表头")

    # 2. 提取表头和分隔线
    header = lines[header_idx]
    separator = lines[header_idx + 1]

    # 3. 提取数据行
    data_lines = lines[header_idx + 2:]

    # 4. 过滤
    filtered = [header, separator]
    for line in data_lines:
        # 跳过空行
        if not line.strip():
            continue
        # 按竖线拆分，注意前后可能有空格
        parts = [seg.strip() for seg in line.split('|')]
        if len(parts) < 3:
            continue

        # 产品形态过滤
        if parts[2].replace(" ", "") != product_name:
            continue

        # 额外规则：product_name 为 '721' 时剔除含 OTN-LB 的网元业务模型
        if (product_name == 'M721产品' and len(parts) >= 3 and 'OTN-LB' in parts[3]) or \
           (product_name == '19700产品' and len(parts) >= 3 and 'OTN-CB' in parts[3]):
            continue

        filtered.append(line)

    # 5. 拼接为新的 Markdown 字符串
    return '\n'.join(filtered)


def merge_site_rows(md_table: str) -> str:
    """
    合并连续且站点名称相同的行
    去重后把指定列用英文逗号拼接
    """
    lines = [ln.rstrip() for ln in md_table.splitlines() if ln.strip()]
    if len(lines) < 3:
        return md_table

    header, sep, *data = lines
    cols_head = [c.strip() for c in header.split('|')][1:-1]
    site_idx  = cols_head.index('站点名称')

    # 需要合并的列索引
    merge_cols = [
        cols_head.index('网元业务模型'),
        cols_head.index('入口业务类型'),
        cols_head.index('入口单板模型'),
        cols_head.index('交叉类型'),
        cols_head.index('出口业务类型'),
        cols_head.index('出口单板模型')
    ]

    new_rows: List[str] = [header, sep]

    # 按连续同名分组
    groups: List[List[List[str]]] = []
    for ln in data:
        cells = [c.strip() for c in ln.split('|')][1:-1]
        if not groups or cells[site_idx] != groups[-1][0][site_idx]:
            groups.append([cells])
        else:
            groups[-1].append(cells)

    # 生成合并后的行
    for group in groups:
        first = group[0]
        merged = first[:]  # 站点名称、产品形态等保持首行不变

        # 收集各合并列的所有值
        buckets: Dict[int, set] = {i: set() for i in merge_cols}
        for cells in group:
            for col in merge_cols:
                for item in re.split(r'[,，]\s*', cells[col]):
                    if item:
                        buckets[col].add(item)

        # 用逗号拼接
        for col in merge_cols:
            merged[col] = ','.join(sorted(buckets[col]))

        new_rows.append('| ' + ' | '.join(merged) + ' |')

    return '\n'.join(new_rows)

# 格式转成md格式
def hd_str_to_md_table(raw_text: str) -> str:
    # 1. 拆三段
    biz_pat = re.compile(r"业务要素----(.*?)高可用要素----", re.S)
    ha_pat = re.compile(r"高可用要素----(.*?)可扩展要素----", re.S)
    ext_pat = re.compile(r"可扩展要素----(.*)", re.S)

    biz_block = biz_pat.search(raw_text)
    ha_block = ha_pat.search(raw_text)
    ext_block = ext_pat.search(raw_text)

    # 2. 提取 (…) 与后面硬件表达式   ← 这里把括号加进第二组
    pattern = re.compile(
        r'(?:"|\')?([(\[][^(]*?[)\]])\s*[,，]?\s*["\']?([A-Z0-9\sx=+\-()]+)["\']?',
        flags=re.MULTILINE | re.IGNORECASE
    )

    rows = []

    def _add_rows(block, label):
        if not block:
            return
        for m in pattern.finditer(block):
            slice_part = m.group(1).strip().replace('"', '')
            deploy_part = m.group(2).strip()
            rows.append(f"| {label} | {slice_part} | {deploy_part} |")

    _add_rows(biz_block.group(1) if biz_block else "", "核心业务方案")
    _add_rows(ha_block.group(1) if ha_block else "", "高可用业务方案")
    _add_rows(ext_block.group(1) if ext_block else "", "可扩展业务方案")

    if not rows:
        return ""

    header = "| 业务方案 | 业务方案切片 | 硬件部署 |\n| --- | --- | --- |"
    return "\n".join(chain([header], rows))


# 原始需求数据表推荐出满足业务部署的硬件
def recommend_board_hd_svc_deployment(product_name: str, hd_req: str, factor_md_all: str, slices_all: str, hd_table: Union[str, List[str]], data_type:str, dependent_data:str=''):
    result = ""

    # 根据产品名称过滤站点并将数据按照站点名称进行合并
    # logger.info(f"--------hd_req:{hd_req}")
    req = filter_product_by_name(hd_req, product_name)
    logger.info(f"--------req:{req}")
    merg = merge_site_rows(req)
    # logger.info(f"--------merg:{merg}")
    hd_req_data = parse_md_table_to_dict(hd_req)
    logger.info(f"--------hd_req_data:{hd_req_data}")
    merg_data = parse_md_table_to_dict(merg)
    logger.info(f"--------merg_data:{merg_data}")
    if len(merg_data) < 2:
        return ""

    # result += "\n\n单板分组信息\n"
    # result = intermediate_process_data_table(merg_data)
    # print(f"------result:{result}")

    if data_type == '推荐单板基本信息':
        # result += "\n\n" + data_type.strip() + "\n"
        # logger.info(f"--------product_name:{product_name}")
        mid_md = get_recommend_board_table(product_name, merg_data, hd_req_data)
        # logger.info(f"--------mid_md:{mid_md}")
        # 如果 hd_table 是 list 类型，直接使用；否则调用 get_board_names 解析 Markdown 表格
        if isinstance(hd_table, list):
            hd_bd = hd_table
        else:
            hd_bd = get_board_names(hd_table)
        filter_mid_md = filter_md_recommended_only(mid_md, hd_bd)
        result += filter_mid_md
    elif data_type == '推荐单板详细信息':
        column = '推荐单板名称'
        board_list = list(set(pub_get_column_values_from_markdown_table(dependent_data.replace('\\', ''), column)))
        logger.info(f"--------board_list:{board_list}")
        filtered_board_list = [x for x in board_list if x is not None]
        params = {"board": ','.join(filtered_board_list)} 
        resps = querySrcBoardTreeByParams(params, markdown_flag=True)
        columns = []
        if resps:
            columns = list(resps[0].keys())
        columns = [column for column in columns if column not in ['id', 'status', 'create_time', 'update_time', 'operator_person', 'effective_flag']]
        replace_dict = {"board":"单板"}
        result += pub_dict_list_to_markdown_table_reordered(resps, columns, replace_dict)
    elif data_type == '网元业务模型的硬件部署':
    #print(f"------filter_mid_md:{filter_mid_md}")
    # result += "\n\n单板要素表达信息\n"
        factor_md = extract_top_n_md_rows(factor_md_all, 3)
        # result += factor_md
        filter_mid_md = dependent_data.replace('\\', '')
        # result += "\n\n" + data_type.strip() + "\n"
        hw_md = net_hardware_deployment_table(req, factor_md, filter_mid_md, product_name)
        logger.info(f"--------hw_md:{hw_md}")
        result += hw_md
    elif data_type == '业务方案切片的硬件部署':
        # result += "\n\n" + data_type.strip() + "\n"
        hw_md = dependent_data.replace('\\', '')
        logger.info(f"--------hw_md:{hw_md}")
        logger.info(f"--------slices_all:{slices_all}")
        slices = svc_slice_hardware_deployment(slices_all, hw_md)
        logger.info(f"--------slices1:{slices}")
        hd_slices = hd_str_to_md_table(slices)
        hd_slices = hd_slices.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace("'", "")
        result += hd_slices

    #print(result)
    return result
    
