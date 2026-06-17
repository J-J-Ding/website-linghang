#!/usr/bin/python3

import re
from itertools import product

def parse_md_table(md_text):
    """解析Markdown表格,返回站点数据列表"""
    lines = [line.strip() for line in md_text.strip().split('\n') if line.strip()]
    if len(lines) < 3:  # 至少包含表头和一行数据
        raise ValueError("输入的md格式中站点个数小于2")

    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
    sites = []

    for line in lines[2:]:  # 跳过表头和分隔线
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) == len(headers):
            sites.append(dict(zip(headers, cells)))
    return sites

def generate_cl_lc(sites):
    """仅处理输出第一行数据中的网元业务模型"""
    product_form = sites[0]['产品形态']
    first_models = sites[0]['网元业务模型'].split('/')

    output = [f"01 {product_form}", "1.1 CL=LC-原子网络业务部署："]
    for model in first_models:
        model = model.strip()
        output.append(f"(CL_LC, {model} == {model}),")

    return '\n'.join(output)

def match(mid, head):
    # 防御：确保都有且仅有一个 '-'
    if '-' not in mid or '-' not in head:
        return False
    h_mid = head.split('-')[1]      # 首行中间字段
    m_mid = mid.split('-')[1]       # 中间模型中间字段
    # return (m_mid == h_mid)
    #收尾节点是更小颗粒度的OSU/FG/VC， 通过补齐CL==LL==LC的时候，中间LL的可以先按照和收尾节点交叉类型一致的增加，OTN-O-OTN的先遗留不加
    return (m_mid == 'O' and h_mid in {'OSU', 'FG', 'V', 'P'}) or (m_mid == h_mid)

def generate_cl_ll_lc(sites):
    head_models = [m.strip() for m in sites[0]['网元业务模型'].split('/')]
	# 无中间节点（只有首行+末行）
    if len(sites) == 2:
        lines = ["1.2 CL=LL=LC-原子网络业务部署："]
        for h in head_models:
            if '-' in h:
                mid = h.split('-')[1]
                lines.append(f"(CL_LL_LC, {h} == OTN-{mid}-OTN == {h}),")
        return '\n'.join(lines)

    middle_models = sorted(set(
        m.strip()
        for site in sites[1:-1]
        for m in site['网元业务模型'].split('/')
    ))

    lines = ["1.2 CL=LL=LC-原子网络业务部署："]
    for h, m in product(head_models, middle_models):
        if match(m, h):
            lines.append(f"(CL_LL_LC, {h} == {m} == {h}),")
    return '\n'.join(lines)


def svc_atom_network_split(md_text):
    """主处理函数"""
    try:
        sites = parse_md_table(md_text)
        result = generate_cl_lc(sites)
        result += '\n'
        result += generate_cl_ll_lc(sites)
        return result
    except ValueError as e:
        return str(e)
