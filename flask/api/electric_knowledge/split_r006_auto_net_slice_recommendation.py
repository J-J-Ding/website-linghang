#!/usr/bin/python3
#!/usr/bin/python3

import re
from itertools import product
from typing import Dict, List, Tuple
from collections import OrderedDict

# ---------- 公共解析 ----------
def parse_cl_lc_type(text: str):
    """
    提取 (拓扑, 模型) 二元组
    支持跨行、空格随意
    """
    pattern = re.compile(r'\(\s*([^,)]+?)\s*,\s*([^,=]+?)\s*==', re.S)
    return [(t.strip(), m.strip()) for t, m in pattern.findall(text)]

def parse_cl_ll_lc_type(text: str) -> List[Tuple[str, str, str]]:
    """
    提取 (拓扑, CL模型, LL模型)，只保留 CL_LL_LC 拓扑
    正则匹配:(..., CL == LL == ...)
    """
    pat = re.compile(r'\(\s*([^,)]+)\s*,\s*([^,=]+?)\s*==\s*([^,=]+?)\s*==', re.S)
    return [(t.strip(), cl.strip(), ll.strip())
            for t, cl, ll in pat.findall(text)
            if t.strip().upper() == "CL_LL_LC"]

def split_strip(part):
    return [s.strip() for s in part.split(',') if s.strip()]

def parse_entry_exit_rate(text: str):
    """
    提取 entry / exit 列表
    支持中英文冒号、逗号及空格
    """
    # 统一把中文符号换成英文
    text = text.replace(':', ':').replace('，', ',').replace(' ', '')

    entry_pat = re.search(r'入口光层业务因子:([^:\n]+)(?=\n|$)', text, re.M)
    exit_pat  = re.search(r'出口光层业务因子:([^:\n]+)(?=\n|$)', text, re.M)

    return {
        "entry": split_strip(entry_pat.group(1)) if entry_pat else [],
        "exit":  split_strip(exit_pat.group(1))  if exit_pat  else []
    }

RATE_MAP = {
	  "2.5G及以下灰光": 2.5, 
    "10G灰光": 10,
    "100G灰光": 100,
    "200G灰光": 200,
    "400G灰光": 400,
    "800G灰光": 800,
	  "100G彩光": 100,
    "200G彩光": 200,
    "400G彩光": 400,
    "800G彩光": 800
}

def compare_rate(entry, exit_factor):
    return RATE_MAP.get(entry, 0) <= RATE_MAP.get(exit_factor, 0)

def is_valid_entry_rate_and_model(entry_factor: str, topo_model: str) -> bool:
    special_models = ['E1-V-SDH', 'E1oFG-FG-OTN-CB', 'SDH-FG-OTN', 'SDH-FG-OTN-LB', 'VCoFG-FG-OTN', 'SDH-OSU-OTN-LB', 'SDH-OSU-OTN']
    
    if topo_model in special_models and '2.5G' not in entry_factor:
        print(f"[特殊] 模型 {topo_model} 不支持入口速率 {entry_factor}")
        return False
    return True


# 场景生成:仅保留数值
def scene(rate: str, is_split: bool) -> str:
    num = rate.split('G')[0]
    return f"{num}G拆分" if is_split else f"{num}G直通"

# ---------- CL=LC 主函数 ----------
def generate_cl_lc_recommendation(input1: str, input2: str) -> str:
    topo_model = parse_cl_lc_type(input1)
    factors    = parse_entry_exit_rate(input2)
    #print(f"-----topo_model:{topo_model}------")
    cl_lc_models = sorted({m for t, m in topo_model if t.upper() == "CL_LC"})
    #print(f"-----cl_lc_models:{cl_lc_models}------")
    entry_factors = factors["entry"]
    exit_factors  = factors["exit"]

    combos = product(["CL_LC"], entry_factors, cl_lc_models, exit_factors)
    combos = [(t, e, m, x) for t, e, m, x in combos
              if compare_rate(e,x) and is_valid_entry_rate_and_model(e, m)]

    header = (f"cl_lc_models:{cl_lc_models}, "
              f"entry_factors:{entry_factors}, "
              f"exit_factors:{exit_factors}\n")

    table_header = ("| ID | 拓扑因子 | 入口光层业务因子 | 网元业务模型因子 | 出口光层业务因子 |\n"
                    "| --- | --- | --- | --- | --- |\n")

    table_rows = [f"| {i+1} | {t} | {e} | {m} | {x} |"
                  for i, (t, e, m, x) in enumerate(combos)]

    return  table_header + "\n".join(table_rows)

# ---------- CL=LL=LC 主函数 ----------
def generate_cl_ll_lc_recommendation(input1: str, input2: str) -> str:
    pairs = parse_cl_ll_lc_type(input1)  # [(CL, LL), ...]
    fac   = parse_entry_exit_rate(input2)

    combos = []
    for i, ((cl_model, ll_model), cl_in, cl_out, ll_out) in enumerate(
            product({(cl, ll) for _, cl, ll in pairs},
                    fac["entry"], fac["exit"], fac["exit"])):

        if RATE_MAP[cl_in] > RATE_MAP[cl_out] or RATE_MAP[cl_out] > RATE_MAP[ll_out]:
            continue

        if not is_valid_entry_rate_and_model(cl_in, cl_model):
            continue

        # L入场景:基于 CL入口；L出场景:基于 LL出口
        lin_scene  = scene(cl_out,  RATE_MAP[cl_in] < RATE_MAP[cl_out])
        lout_scene = scene(ll_out, RATE_MAP[cl_in] < RATE_MAP[ll_out])

        combos.append((i + 1, "CL_LL_LC", cl_in, cl_model,
                       cl_out, ll_model, ll_out, lin_scene, lout_scene))

    header = ("| ID | 拓扑因子 | CL 入口光层业务因子 | CL 网元业务模型因子 | "
              "CL 出口光层业务因子 | LL 网元业务模型因子 | LL 出口光层业务因子 | "
              "L入涵盖场景 | L出涵盖场景 |\n"
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
    body = "\n".join(
        f"| {i} | {t} | {cin} | {cm} | {cout} | {lm} | {lout} | {lin} | {lout_scene} |"
        for i, t, cin, cm, cout, lm, lout, lin, lout_scene in combos
    )
    return header + body

def parse_cl_lc_core_slices(md: str) -> List[Tuple[str, str, str, str]]:
    """
    解析形如示例的 Markdown 表格，返回四元组列表。
    """
    # 去掉表头与分隔行
    rows = [line.strip('| \n') for line in md.splitlines() if line.strip()]
    rows = rows[2:]          # 跳过表头与 --- 行

    result: List[Tuple[str, str, str, str]] = []
    for row in rows:
        # 按竖线切，再 strip
        cols = [c.strip() for c in row.split('|')]
        if len(cols) < 5:          # 跳过异常行
            continue
        topo, entry, model, exit_ = cols[1], cols[2], cols[3], cols[4]

        # 统一简化 “2.5G及以下灰光” → “2.5G灰光”
        entry = entry.replace("2.5G及以下灰光", "2.5G灰光")
        exit_ = exit_.replace("2.5G及以下灰光", "2.5G灰光")

        result.append((topo, entry, model, exit_))
    return result

def parse_cl_ll_lc_core_slices(md: str) -> List[Tuple[str, str, str, str, str, str]]:
    """
    解析 CL/LL 八列表格，返回六元组：
    (拓扑因子, CL入口, CL模型, CL出口, LL模型, LL出口)
    """
    # 去掉表头、分隔行和空行
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    rows = lines[2:]          # 跳过前两行

    result: List[Tuple[str, str, str, str, str, str]] = []
    for ln in rows:
        if not ln.startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if len(cells) < 8:
            continue

        # 依次取：拓扑、CL入口、CL模型、CL出口、LL模型、LL出口
        topo, cl_in, cl_model, cl_out, ll_model, ll_out = cells[1:7]

        # 统一把“2.5G及以下灰光”替换成“2.5G灰光”
        cl_in  = re.sub(r'2\.5G及以下灰光', '2.5G灰光', cl_in)
        cl_out = re.sub(r'2\.5G及以下灰光', '2.5G灰光', cl_out)
        ll_out = re.sub(r'2\.5G及以下灰光', '2.5G灰光', ll_out)

        result.append((topo, cl_in, cl_model, cl_out, ll_model, ll_out))
    return result

def get_protection_dict(md: str) -> Dict[str, Dict[str, List[str]]]:
    """
    解析 Markdown 表格，返回：
    {
        '级联': { 'O保护': [...], 'FG保护': [...], ... },
        '非级联': { 'O保护': [...], 'FG保护': [...], ... }
    }
    """
    cascade: Dict[str, List[str]] = {}
    normal: Dict[str, List[str]] = {}

    for line in md.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 4:
            continue

        category, factor_name, values = cells[1], cells[2], cells[3]

        if category != '高可用要素' or not factor_name.endswith('保护因子'):
            continue

        prefix = factor_name.replace('因子', '')

        # 统一分隔符
        values = re.sub(r'[、，；;]', ',', values)
        items = [re.sub(r'[（）()\s]', '', v.strip()) for v in values.split(',') if v.strip()]

        cascade_list = [item for item in items if '级联保护' in item]
        normal_list = [item for item in items if '级联保护' not in item]

        # 去重保留顺序
        cascade[prefix] = list(dict.fromkeys(cascade_list))
        normal[prefix] = list(dict.fromkeys(normal_list))

    return {'级联': cascade, '非级联': normal}

# 3. 根据关键字获取非级联保护因子
def discascade_factors(key: str, protection_dict) -> List[str]:
    return protection_dict['非级联'].get(key + '保护', [])

# 3. 根据关键字获取级联保护因子
def cascade_factors(key: str, protection_dict) -> List[str]:
    return protection_dict['级联'].get(key + '保护', [])

# --------------------------------------------------
# 2. 提取关键字 & 匹配保护
# --------------------------------------------------
def extract_cl_key_prtc(model: str) -> str:
    m = re.search(r'-([A-Za-z]+)-', model)
    if not m:
        return ''
    
    result = m.group(1).upper()
    
    # 执行字符替换
    result = result.replace('V', 'VC')  # 将 V 替换为 VC
    result = result.replace('P', 'PKT')  # 将 P 替换为 PKT
    
    return result

def extract_cl_key_expand(model: str) -> str:
    m = re.search(r'-([A-Za-z]+)-', model)
    if not m:
        return ''
    
    result = m.group(1).upper()
    
    # 执行字符替换
    result = result.replace('V', 'VC')  # 将 V 替换为 VC
    
    return result    

def extract_multi_key(model: str) -> str:
    multi_V = ['VCoFG-FG-OTN', 'VCoFG-FG-OTN-CB', 'E1oFG-FG-OTN-CB', 'EoSoFG-FG-OTN-CB']
    if model in multi_V:
        return 'VC'
    return ''

def is_valid_fac_model_combination(fac: str, model: str) -> bool:
    if not fac or not model:
        return False
    
    # 特殊规则：'VCoFG-FG-OTN' 只支持 'vc复用段1+1保护'
    if model == 'VCoFG-FG-OTN':
        if fac == 'vc复用段1+1保护':
            return True
        else:
            print(f"[VALIDATION] 模型 {model} 只支持 'vc复用段1+1保护'，不支持 {fac}")
            return False
    
    # 特殊规则：以下模型不支持 'vc复用段1+1保护'
    unsupported_models = [
        'VCoFG-FG-OTN-CB',
        'E1oFG-FG-OTN-CB', 
        'EoSoFG-FG-OTN-CB'
    ]
    
    if model in unsupported_models and fac == 'vc复用段1+1保护':
        print(f"[VALIDATION] 模型 {model} 不支持保护类型 {fac}")
        return False
    
    # 默认情况下，其他组合都认为是有效的
    return True

# 2. 提取 LL模型中的关键字（FG / V）
def extract_cl_ll_key(model: str) -> str:
    m = re.search(r'-([A-Za-z]+)-', model)
    if not m:
        return ''
    key = m.group(1).upper()
    return 'VC' if key == 'V' else key
# --------------------------------------------------
# 3. 正交展开
# --------------------------------------------------
def expand_cl_cl_protection(rows: List[Tuple[str, str, str, str]], protection_dict) -> List[Tuple[str, ...]]:
    result = []
    for topo, entry, model, exit_ in rows:
        if not is_valid_entry_rate_and_model(entry, model):
            continue
        key = extract_cl_key_prtc(model)
        if not key:
            print(f"[DEBUG] 无法从模型提取关键字：{model}")
            continue
        facs = discascade_factors(key, protection_dict)
        if not facs:
            print(f"[DEBUG] 关键字 {key} 未匹配到任何保护取值")
            continue
        for fac in facs:
            result.append((topo, model, fac))
        ext_key = extract_multi_key(model)
        if not ext_key:
            continue
        print(f"[DEBUG] 从模型提取额外关键字：网元业务模型{model} 额外交叉类型{ext_key}")
        facs = discascade_factors(ext_key, protection_dict)
        if not facs:
            print(f"[DEBUG] 关键字 {ext_key} 未匹配到任何保护取值")
            continue
        for fac in facs:
            # 添加有效性校验
            if is_valid_fac_model_combination(fac, model):
                result.append((topo, model, fac))
            else:
                print(f"[DEBUG] 跳过无效组合: 保护因素 {fac} 与模型 {model}")      

    # 去重处理：使用OrderedDict保持顺序去重
    unique_result = list(OrderedDict.fromkeys(result))
    return unique_result

# 4. 正交展开
def expand_cl_ll_cl_protection(rows: List[Tuple[str, ...]], protection_dict) -> List[Tuple[str, ...]]:
    result = []
    for row in rows:
        topo, entry, cl_model, cl_exit, ll_model, ll_exit = row
        if not is_valid_entry_rate_and_model(entry, cl_model):
            continue
        key = extract_cl_ll_key(ll_model)
        for fac in cascade_factors(key, protection_dict):
            result.append((topo, cl_model, ll_model, fac))

    # 去重处理：使用OrderedDict保持顺序去重
    unique_result = list(OrderedDict.fromkeys(result))
    return unique_result

def classify_extension_factors(md: str) -> Dict[str, List[str]]:
    """
    按非级联保护因子类型（O/FG/OSU/PKT/VC）分类扩展应用要素的取值
    """
    # 非级联键名集合
    keys = {'O', 'FG', 'OSU', 'P', 'VC'}

    # 结果容器
    result: Dict[str, List[str]] = {k: [] for k in keys}

    for line in md.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 4:
            continue

        category, factor_name, values = cells[1], cells[2], cells[3]

        if category != '扩展应用要素':
            continue

        # 统一分隔符
        values = re.sub(r'[、，；;]', ',', values)
        items = [v.strip() for v in values.split(',') if v.strip()]

        for item in items:
            # 提取前缀：如 "O业务..." -> O
            m = re.match(r'^([A-Za-z]+)[^A-Za-z]', item, re.I)
            #print(f"---m:{m.group(1).upper()}------")
            if not m:
                continue
            key = m.group(1).upper()
            if key in keys:
                # 统一清理：去掉括号、空格
                clean = re.sub(r'[（）()\s]', '', item)
                result[key].append(clean)

    # 去重并保持顺序
    for k in result:
        result[k] = list(dict.fromkeys(result[k]))
    return result

# --------------------------------------------------
# 3. 正交展开
# --------------------------------------------------
def is_valid_model_for_expand_fac(fac: str, model: str) -> bool:
    if not fac or not model:
        return False
        
    # 特殊规则：以下网元业务模型支持无损带宽调整 或 LCAS带宽容量调整'
    support_bw_adj_model = [
        'EoFG-P-OTN', 'EoFG-FG-OTN', 'EoFG-FG-OTN-LB', 'OTN-FG-OTN', 
        'EoOSU-P-OTN', 'EoOSU-OSU-OTN', 'EoOSU-OSU-OTN-LB', 'OTN-OSU-OTN', 
        'ETH-O-OTN', 'EoO-P-OTN', 'EoO-O-OTN', 'OTN-O-OTN'
    ]   
    
    support_lcas_model = [
        'EoS-V-SDH', 'EoS-V-OTN-LB', 'EoS-V-OTN'
    ] 
    
    if "无损" in fac and model not in support_bw_adj_model:
        return False
    if  "LCAS带宽容量调整" in fac and model not in support_lcas_model:
        return False

    # 默认情况下，其他组合都支持
    return True

def expand_cl_cl(rows: List[Tuple[str, str, str, str]], protection_dict) -> List[Tuple[str, ...]]:
    result = []
    for topo, entry, model, exit_ in rows:
        if not is_valid_entry_rate_and_model(entry, model):
            continue
        key = extract_cl_key_expand(model)
        #print(key)
        if not key:
            print(f"[DEBUG] 无法从模型提取关键字：{model}")
            continue
        facs = protection_dict.get(key, [])
        if not facs:
            print(f"[DEBUG] 关键字 {key} 未匹配到任何保护取值")
            continue
        for fac in facs:
            if not is_valid_model_for_expand_fac(fac, model):
                continue
            result.append((topo, model, fac))

        if model == 'EoFG-P-OTN':
            result.append((topo, model, 'FG业务无损带宽调整'))
        if model == 'EoOSU-P-OTN':
            result.append((topo, model, 'OSU业务无损带宽调整'))
        if model == 'EoO-P-OTN':
            result.append((topo, model, 'O业务无损带宽调整'))

        key = extract_multi_key(model)
        if not key:
            continue
        facs = protection_dict.get(key, [])
        if not facs:
            print(f"[DEBUG] 关键字 {key} 未匹配到任何保护取值")
            continue
        for fac in facs:
            result.append((topo, model, fac))

    # 去重处理：使用OrderedDict保持顺序去重
    unique_result = list(OrderedDict.fromkeys(result))
    return unique_result

def expand_cl_ll_cl(rows: List[Tuple[str, ...]], protection_dict) -> List[Tuple[str, ...]]:
    result = []
    for row in rows:
        topo, entry, cl_model, cl_exit, ll_model, ll_exit = row
        if not is_valid_entry_rate_and_model(entry, cl_model):
            continue
        key = extract_cl_key_expand(cl_model)
        key_ll = extract_cl_key_expand(ll_model)
        # print(f"key: {key}, key_ll: {key_ll}")
        if not key or key != key_ll:
            print(f"[DEBUG] 无法从模型提取关键字：{cl_model}")
            continue
            
        facs = protection_dict.get(key, [])
        if not facs:
            print(f"[DEBUG] 关键字 {key} 未匹配到任何保护取值")
            continue
        for fac in facs:
            if ("无损" in fac or "LCAS带宽容量调整" in fac) and is_valid_model_for_expand_fac(fac, cl_model):
                result.append((topo, cl_model, ll_model, fac))
    
    # 去重处理：使用OrderedDict保持顺序去重
    unique_result = list(OrderedDict.fromkeys(result))
    return unique_result

def extract_optical_factors(md_str: str) -> str:
    """
    从给定的 markdown 表格字符串中提取客户侧光层业务因子和线路侧光层业务因子，
    并按指定格式返回。
    """
    # 使用正则提取客户侧和线路侧光层业务因子
    customer_pattern = r'客户侧光层业务因子.*?\|(.*?)\|'
    line_pattern = r'线路侧光层业务因子.*?\|(.*?)\|'

    customer_match = re.search(customer_pattern, md_str)
    line_match = re.search(line_pattern, md_str)

    if customer_match and line_match:
        customer_factor = customer_match.group(1).strip()
        line_factor = line_match.group(1).strip()
    else:
        customer_factor = "未找到"
        line_factor = "未找到"

    output = f"""入口光层业务因子:{customer_factor}
出口光层业务因子:{line_factor}
"""
    return output

def tuples_to_str(data: List[Tuple[str, str, str, str]]) -> str:
    """
    将 tuple 列表转换成指定格式的字符串
    """
    return "\n".join(str(item) for item in data)

def auto_network_slice_recommendation(atom_network: str, md_str: str):
    opt_svc_rate = extract_optical_factors(md_str)
    cl_lc_table = generate_cl_lc_recommendation(atom_network, opt_svc_rate)
    cl_lc_core_slices = parse_cl_lc_core_slices(cl_lc_table)
    cl_ll_lc_table = generate_cl_ll_lc_recommendation(atom_network, opt_svc_rate)
    cl_ll_lc_core_slices = parse_cl_ll_lc_core_slices(cl_ll_lc_table)
    
    # 高可用切片
    protection_dict = get_protection_dict(md_str)
    cl_cl_high_available_slices = expand_cl_cl_protection(cl_lc_core_slices, protection_dict)
    cl_ll_cl_high_available_slices = expand_cl_ll_cl_protection(cl_ll_lc_core_slices, protection_dict)

    # 扩展应用切片
    extend_elements = classify_extension_factors(md_str)
    cl_cl_extend_slices = expand_cl_cl(cl_lc_core_slices, extend_elements)
    cl_ll_cl_extend_slices = expand_cl_ll_cl(cl_ll_lc_core_slices, extend_elements)
    # print(f"extend_elements: {extend_elements} \n cl_ll_cl_extend_slices: {cl_ll_cl_extend_slices}")

    result = "\n业务要素----\n"
    result += tuples_to_str(cl_lc_core_slices)
    result += "\n"
    result += tuples_to_str(cl_ll_lc_core_slices)
    result += "\n高可用要素----\n"
    result += tuples_to_str(cl_cl_high_available_slices)
    result += "\n"
    result += tuples_to_str(cl_ll_cl_high_available_slices)
    result += "\n可扩展要素----\n"
    result += tuples_to_str(cl_cl_extend_slices)
    result += "\n"
    result += tuples_to_str(cl_ll_cl_extend_slices)

    return result




