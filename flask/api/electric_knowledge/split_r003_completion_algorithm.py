#!/usr/bin/python3

import re
from typing import List, Tuple


# ---------- 1. 速率候选 ----------
def get_rate_candidates() -> List[str]:
    return ['2.5G及以下', '10G', '100G', '200G', '400G']

# ---------- 2. 工具 ----------
def parse_key(rate_str: str) -> float:
    """把速率文本转成可排序的数值"""
    if '2.5G及以下' in rate_str:
        return 0.0
    m = re.search(r'(\d+(?:\.\d+)?)', rate_str)
    return float(m.group(1)) if m else 10

def build_rates_str(rates: List[str]) -> str:
    """统一后缀灰光并去重排序"""
    sorted_rates = sorted(set(rates), key=lambda r: parse_key(r))
    return '/'.join(f"{r}灰光" for r in sorted_rates)

def map_model(seg: str) -> str:
    m = re.match(r'OTN-(\w+)-OTN', seg.strip())
    if not m:
        return ''
    key = m.group(1).upper()
    if key == 'O':
        return 'ETH-O-OTN'
    elif key == 'FG':
        return 'OTN-FG-OTN'
    elif key == 'OSU':
        return 'CBR-OSU-OTN'
    return 'ETH-O-OTN'
# ---------- 3. 主函数 ----------
def fill_start_and_end_stations(md: str) -> str:
    lines = [ln.rstrip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 3:
        return md
    header, sep, *body = lines
    if not body:
        return md

    first_parts = [p.strip() for p in body[0].split('|')][1:-1]
    last_parts  = [p.strip() for p in body[-1].split('|')][1:-1]
    if len(first_parts) != 6 or len(last_parts) != 6:
        return md

    site_first, product, first_in_layer, first_model, first_out_layer, _ = first_parts
    site_last,  _,      last_in_layer,  last_model,  last_out_layer,  _ = last_parts

    if not (re.search(r'OTN-\w+-OTN', first_model) or re.search(r'OTN-\w+-OTN', last_model)):
        return md

    rate_candidates = get_rate_candidates()
    orig_first_key  = parse_key(first_in_layer)
    orig_last_key   = parse_key(last_out_layer)

    # ---------- 3.1 前插行入口灰光 ----------
    first_in_rates = set()
    for seg in first_model.split('/'):
        mapped = map_model(seg)
        if mapped == 'OTN-FG-OTN':
            first_in_rates.add('10G')
        else:
            lowers = [r for r in rate_candidates if parse_key(r) <= orig_first_key]
            first_in_rates.update(lowers or ['2.5G及以下'])

    # ---------- 3.2 后插行出口灰光 ----------
    last_out_rates = set()
    for seg in last_model.split('/'):
        mapped = map_model(seg)
        if mapped == 'OTN-FG-OTN':
            last_out_rates.add('10G')
        else:
            uppers = [r for r in rate_candidates if parse_key(r) <= orig_last_key]
            last_out_rates.update(uppers or ['2.5G及以下'])

    # ---------- 3.3 交集 ----------
    common_rates = sorted(set(first_in_rates) & set(last_out_rates), key=lambda r: parse_key(r))
    if not common_rates:
        common_rates = ['2.5G及以下']
    unified_gray = build_rates_str(common_rates)

    # ---------- 3.4 模型 ----------
    new_model = '/'.join(map_model(s) for s in first_model.split('/'))

    # ---------- 3.5 构造两行 ----------
    new_first_row = f"| OTN_首站点 | {product} | {unified_gray} | {new_model} | {first_in_layer} |      |"
    new_last_row  = f"| OTN_尾站点 | {product} | {last_out_layer} | {new_model} | {unified_gray} |      |"

    new_body = [new_first_row] + body + [new_last_row]
    return '\n'.join([header, sep] + new_body)

# 判断是否为 OTN-xxx-OTN
def otn_flag(model): 
    return bool(re.search(r'OTN-[\w-]*-OTN', model))

# 判断业务速率 >10G（只要字符串里出现 >10 的数字即可）
def rate_gt10(txt): 
	return any(int(m) > 10 for m in re.findall(r'\d+', txt))

# 构造新行(各列顺序与表格一致)
def mk_row(site, prod, in_lay, model, out_lay):
    return f"|{site}|{prod}|{in_lay}|{model}|{out_lay}| |"

def fill_start_or_end_stations(md: str) -> str:
    lines = [ln.rstrip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 3:                       # 表头+分隔+至少一行
        return md
    header, sep, *body = lines
    if not body:
        return md

    # 取第一行、最后一行的各列
    first_parts = [p.strip() for p in body[0].split('|')][1:-1]
    last_parts  = [p.strip() for p in body[-1].split('|')][1:-1]
    if len(first_parts) != 6 or len(last_parts) != 6:
        print(f"--first_parts:{len(first_parts)},last_parts:{len(last_parts)}---")
        return md

    # 列名：站点名称，产品形态，入口光层业务，网元业务模型，出口光层业务，变更分析
    site1, prod1, in1, model1, out1, _ = first_parts
    siteN, _    , inN, modelN, outN, _ = last_parts

    new_row = None
    # 规则1：第1行满足 OTN-xxx-OTN 且 入口>10，最后一行不满足 OTN-xxx-OTN
    if otn_flag(model1) and rate_gt10(in1):
        new_row = (
            f"|OTN_首站点|{prod1}|{outN}|{modelN}|{in1}| |"
        )
        body.insert(0, new_row)

    # 规则2：第1行不满足 OTN-xxx-OTN，最后一行满足 OTN-xxx-OTN 且 出口>10
    elif otn_flag(modelN) and rate_gt10(outN):
        new_row = (
            f"|OTN_尾站点|{prod1}|{outN}|{model1}|{in1}| |"
        )
        body.append(new_row)

    return '\n'.join([header, sep] + body)

# ----------------- 工具函数 -----------------
def _split_line(ln: str) -> List[str]:
    return [p.strip() for p in ln.split('|')][1:-1]

def _join_line(parts: List[str]) -> str:
    return '| ' + ' | '.join(parts) + ' |'

# ----------------- 业务模型推导(优先级 1-2-3) -----------------
def _derive_model(cur_model: str, nxt_model: str) -> str:
    """
    按优先级 1-2-3 推导补站点的网元业务模型
    """
    # 优先级 1：上一行是 OTN-XX-OTN
    if re.fullmatch(r'OTN-[A-Z]+-OTN', cur_model):
        return cur_model

    # 优先级 2：下一行是 OTN-XX-OTN
    if re.fullmatch(r'OTN-[A-Z]+-OTN', nxt_model):
        return nxt_model

    # 优先级 3：遍历原行各子模型
    def _single(m: str) -> str:
        seg = re.search(r'-([A-Z]+)-', m)
        if not seg:
            return 'OTN-O-OTN'
        mm = seg.group(1)
        if mm == 'FG':
            return 'OTN-FG-OTN'
        if mm == 'OSU':
            return 'OTN-OSU-OTN'
        return 'OTN-O-OTN'

    parts = [s.strip() for s in cur_model.split('/')]
    derived = [_single(p) for p in parts]
    return '/'.join(derived)

# ----------------- 主函数 -----------------
def fill_midway_stations(md: str) -> str:
    lines = [ln.rstrip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 3:
        return md
    header, sep, *body = lines
    if not body:
        return md

    for ln in body:
        if len(_split_line(ln)) != 6:
            return md

    new_body = []
    i = 0
    while i < len(body):
        cur = body[i]
        new_body.append(cur)

        if i + 1 < len(body):
            cur_parts = _split_line(cur)
            nxt_parts = _split_line(body[i + 1])

            cur_out = cur_parts[4]
            nxt_in  = nxt_parts[2]

            if cur_out != nxt_in:
                site_name = 'OTN_补站点'
                product   = cur_parts[1]
                new_in    = cur_out
                new_out   = nxt_in
                cur_model = cur_parts[3]
                nxt_model = nxt_parts[3]
                new_model = _derive_model(cur_model, nxt_model)

                new_row = [site_name, product, new_in, new_model, new_out, '']
                new_body.append(_join_line(new_row))
        i += 1

    return '\n'.join([header, sep] + new_body)
	
def _parse_rate(rate_str: str) -> int:
    """把“10G灰光”、“100G彩光”等转成纯数字(单位 G)。无法识别返回 0。"""
    m = re.search(r'(\d+(?:\.\d+)?)\s*[Gg]', rate_str)
    return int(float(m.group(1))) if m else 0

def _get_first_last_rows(md: str) -> Tuple[List[str], List[str]]:
    """返回首行、末行的单元格列表(已 trim)。"""
    lines = [ln.strip('|').strip() for ln in md.splitlines() if ln.strip()]
    body_lines = [ln for ln in lines if not re.match(r'^[-:| ]+$', ln)]
    _, *rows = body_lines
    first = [c.strip() for c in rows[0].split('|')]
    last  = [c.strip() for c in rows[-1].split('|')]
    return first, last

def process_md_table(md: str) -> str:
    """
    按 1→2→3→4 顺序处理 Markdown 表格
    返回(处理后表格 + 可选提示)的拼接字符串
    """
    first, last = _get_first_last_rows(md)

    # 列索引：固定按题目顺序
    COL_MODEL = 3   # “网元业务模型”
    COL_IN    = 2   # “入口光层业务”
    COL_OUT   = 4   # “出口光层业务”

    first_model  = first[COL_MODEL]
    first_rate   = _parse_rate(first[COL_IN])
    last_model   = last[COL_MODEL]
    last_rate    = _parse_rate(last[COL_OUT])

    pattern = r'^OTN-.*-OTN$'
    
    # 规则 4：无论之前触发与否都要执行
    md = fill_midway_stations(md)

    # 规则 1：首尾同时满足
    if (re.match(pattern, first_model) and first_rate > 10 and
        re.match(pattern, last_model)  and last_rate  > 10):
        print("fill_start_and_end_stations")
        md = fill_start_and_end_stations(md)

    # 规则 2：首或尾满足(且未触发规则 1)
    elif ((re.match(pattern, first_model) and first_rate  > 10) or
          (re.match(pattern, last_model)  and last_rate   > 10)):
        print("fill_start_or_end_stations")
        md = fill_start_or_end_stations(md)

    # 规则 3：仅首行 10G(不再看末行)
    elif re.match(pattern, first_model) and first_rate == 10:
        print("需要人工修正")
        return md 

    return md


# ------------------- 简单测试 --------------------
if __name__ == '__main__':
    test_md = """
|站点名称  | 产品形态 | 入口光层业务               | 网元业务模型        | 出口光层业务             | 变更分析 |
|---|---|---|---|---|---|
|OTN_H站点 | 19700产品| 25G及以下灰光     | OTN-A-OTN           | 10G灰光                  |          |
|OTN_A站点 | 19700产品| 100G灰光                    | OTN-B-OTN           | 100G彩光                 |          |
"""
    print(process_md_table(test_md))
