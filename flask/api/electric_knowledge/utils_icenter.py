import os
import re
import yaml
import copy
import logging
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from get_icenter import IcenterAPI
from electric_knowledge.utils_pub import pub_remove_after_parentheses


logger = logging.getLogger("Logger")
icenter_templateId_path = "./icenter_templateId.yml"


def classify_feature(s: str):
    """
    识别特性名称级别并提取标识符

    :param s: 输入的特性名称字符串
    :return: (标识符, 级别) 元组，级别为"一级"、"二级"或"无效"
    """
    # 正则表达式：匹配第一个连字符前的部分
    # ^        : 字符串开头
    # ([^-]+)  : 捕获组：一个或多个非连字符的字符
    # -        : 匹配第一个连字符
    pattern = r'^([^-]+)-'
    # 尝试匹配
    match = re.match(pattern, s)
    if not match:
        return  "undefine"
    # 提取第一个连字符前的部分
    identifier = match.group(1)
    # 统计连字符数量判断级别
    hyphen_count = s.count('-')
    if hyphen_count <= 2:
        return  "2"
    elif hyphen_count > 2:
        return  "1"
    else:
        # 实际上不会发生，因为匹配成功至少有一个连字符
        return  "undefine"


def extract_target(text):
    # 匹配模式：F开头+3位数字 - 非破折号内容 - 4位数字
    pattern1 = r'F\d{3}-[^-]+-\d{4}'
    pattern2 = r'F\d{3}-[^-]+-\d{3}'
    match1 = re.search(pattern1, text)
    if not match1:
        match2 = re.search(pattern2, text)
        return match2.group() if match2 else None
    else:
        return match1.group() if match1 else None


def find_string_in_column(df: pd.DataFrame, column: str, search_str: str, case_sensitive: bool = True) -> list:
    """
    快速查找字符串在DataFrame指定列中出现的所有行号（0-based位置索引）

    参数:
    df : DataFrame - 目标数据表
    column : str - 列名
    search_str : str - 要搜索的字符串
    case_sensitive : bool - 是否区分大小写（默认区分）

    返回:
    list - 匹配行的位置索引列表（0-based整数）
    """
    try:
        # 1. 安全转换列类型为字符串（处理NaN和非字符串类型）
        col_series = df[column].astype(str)
        # 2. 生成布尔掩码（向量化操作，regex=False提升速度）
        mask = col_series.str.contains(
            search_str,
            regex=False,
            case=case_sensitive
        )
        # 3. 使用numpy高效获取位置索引（0-based）
        # np.where 返回 (row_indices,) 元组，取[0]并转为列表
        return np.where(mask)[0].tolist()
    except KeyError:
        print(f"列 '{column}' 不存在于DataFrame中")
        return []


def replace_br_td(text, replace_str1, replace_str2):
    # 定义匹配模式：关联用例链接 + 任意内容 + <br></td> + 任意内容 + <br></td>
    pattern = r'(关联用例链接.*?)(><br></td>)(.*?)(><br></td>)'
    def replace_func(match):
        # match.group(1): "关联用例链接xxx"
        # match.group(2): 第一个 "<br></td>"
        # match.group(3): "yyy" 
        # match.group(4): 第二个 "<br></td>"
        return (match.group(1) +
                '>' + replace_str1 + '<br></td>' +
                match.group(3) +
                '><a href="' + replace_str2 + '">' + replace_str2 + '</a><br></td>')
    # 使用re.DOTALL标志，使得.可以匹配换行符
    result = re.sub(pattern, replace_func, text, flags=re.DOTALL)
    return result


def new_Icenter_content_html_set(url, html, icentapi, request_type='old'):
    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]
    # 获取页面内容与当前版本
    title, content_body, current_version = icentapi.get_page_edit(pageId)
    if not current_version:
        # 没有查询到版本号，尝试空间2.0的接口
        bo_data = icentapi.get_page_info(spaceId, pageId, type='whole')
        if not bo_data.get('currentVersion', ''):
            # 空间2.0如果返回标题为空，说明1.0和2.0都失败
            print("无法获取当前版本号，终止更新")
            return False
        else:
            current_version = bo_data['currentVersion']
    # 更新页面
    result = icentapi.page_set(pageId, spaceId, title, html, current_version, request_type)
    return result


def icenter_children_get(url, icenterapi):
    """
    获取指定iCenter页面的所有子页面链接和对应标题

    Args:
        url (str): 父页面URL，格式如：
            https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view

    Returns:
        tuple: 包含三个元素的元组：
            - 第一个元素是子页面完整URL列表 (list of str)
            - 第二个元素是子页面标题列表 (list of str)
            - 第三个元素是标题到URL的映射字典 (dict: { title: url })
    """
    contentid, spaceid = icenterapi.get_pageid_spaceid(url)
    result = icenterapi.get_first_children(spaceid, contentid)
    # 关键修复：处理 None 的情况
    if not result:  # None 或 空列表 都视为无子页面
        return [], [], {}
    return list(result.values()), list(result.keys()), result


def get_yaml_config(yaml_path:str):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取绝对路径
    config_path = os.path.join(current_dir, yaml_path)
    config_path = os.path.abspath(config_path)  # 规范化路径
    with open(config_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data


def write_yaml_config(data:dict, yaml_path:str):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取绝对路径
    config_path = os.path.join(current_dir, yaml_path)
    config_path = os.path.abspath(config_path)  # 规范化路径
    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file,  allow_unicode=True, sort_keys=False)


def atom_create_page(icenterAPI:IcenterAPI, spaceId:str, pageId:str, create_title:str, contentBody:str="", templateId: str="", request_type:str="new"):
    create_page_flag = False
    resp_flag, page_id = icenterAPI.is_exist(spaceId, pageId, create_title)
    if not resp_flag:
        response, create_page_flag = icenterAPI.create_page(spaceId, pageId, create_title, contentBody, templateId, request_type)
        if create_page_flag:
            if request_type == "new":
                page_id = response['bo']
            else:
                page_id = response['bo']
    return resp_flag, page_id, create_page_flag


def atom_delete_page(icenterAPI:IcenterAPI, spaceId:str, pageId:str, create_title:str, multi:bool=True):
    delete_page_flag = False
    resp_flag, page_id = icenterAPI.is_exist(spaceId, pageId, create_title)
    if resp_flag:
        delete_page_flag = icenterAPI.delete_page(spaceId, page_id, multi)
    else:
        delete_page_flag = True
    return delete_page_flag


def query_icenter_templates(icenterAPI:IcenterAPI, spaceId:str="fbff14a6a14c4985874248df3ac610c1", type:str='feature'):
    templates = icenterAPI.get_template_list(spaceId)
    template_result = dict()
    if type == 'feature':
        for key, value in templates.items():
            if '特性分析' in key or '特性名称' in key:
                template_result[value[0]] = value[1]
    elif type == 'board':
        for key, value in templates.items():
            if '单板方案' in key or '核心数据' in key:
                template_result[value[0]] = value[1]
    return template_result


def handle_latest_icenter_templates(icenterAPI:IcenterAPI, spaceId:str="fbff14a6a14c4985874248df3ac610c1", type:str='feature'):
    template_result = query_icenter_templates(icenterAPI, spaceId=spaceId, type=type)
    yml_data = get_yaml_config(icenter_templateId_path)
    replace_flag = False
    if type.lower() == 'feature':
        for key, value in template_result.items():
            if yml_data['feature']['feature_analysis']['templateId'].strip() == key:
                if yml_data['feature']['feature_analysis']['updateDate'] < value:
                    yml_data['feature']['feature_analysis']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['feature']['feature_analysis']['updateDate'] = value
                    replace_flag = True
            elif yml_data['feature']['feature_name']['templateId'].strip() == key:
                if yml_data['feature']['feature_name']['updateDate'] < value:
                    yml_data['feature']['feature_name']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['feature']['feature_name']['updateDate'] = value
                    replace_flag = True
            elif yml_data['feature']['children_feature_design']['templateId'].strip() == key:
                if yml_data['feature']['children_feature_design']['updateDate'] < value:
                    yml_data['feature']['children_feature_design']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['feature']['children_feature_design']['updateDate'] = value
                    replace_flag = True
    elif type.lower() == 'board':
        for key, value in template_result.items():
            if yml_data['board']['board_solution']['templateId'].strip() == key:
                if yml_data['board']['board_solution']['updateDate'] < value:
                    yml_data['board']['board_solution']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_solution']['updateDate'] = value
                    replace_flag = True
            elif yml_data['board']['board_basic_functions']['templateId'].strip() == key:
                if yml_data['board']['board_basic_functions']['updateDate'] < value:
                    yml_data['board']['board_basic_functions']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_basic_functions']['updateDate'] = value
                    replace_flag = True
            elif yml_data['board']['board_business_functions']['templateId'].strip() == key:
                if yml_data['board']['board_business_functions']['updateDate'] < value:
                    yml_data['board']['board_business_functions']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_business_functions']['updateDate'] = value
                    replace_flag = True
            elif yml_data['board']['board_oam_functions']['templateId'].strip() == key:
                if yml_data['board']['board_oam_functions']['updateDate'] < value:
                    yml_data['board']['board_oam_functions']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_oam_functions']['updateDate'] = value
                    replace_flag = True
            elif yml_data['board']['board_high_availability_functions']['templateId'].strip() == key:
                if yml_data['board']['board_high_availability_functions']['updateDate'] < value:
                    yml_data['board']['board_high_availability_functions']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_high_availability_functions']['updateDate'] = value
                    replace_flag = True
            elif yml_data['board']['board_extended_application_functions']['templateId'].strip() == key:
                if yml_data['board']['board_extended_application_functions']['updateDate'] < value:
                    yml_data['board']['board_extended_application_functions']['contentBody'] = icenterAPI.get_template_contents(key, spaceId)
                    yml_data['board']['board_extended_application_functions']['updateDate'] = value
                    replace_flag = True
    if replace_flag:
        write_yaml_config(yml_data, icenter_templateId_path)
    return yml_data


def handle_01_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title01 = '01-' + board_name + '-单板-业务功能-核心数据'
    board_type = board_infos.get('板卡类型', '')
    board_business_functions_contentBody = yml_data['board']['board_business_functions']['contentBody']
    resp_flag01, new_page_id01, create_page_flag01 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title01, board_business_functions_contentBody, yml_data['board']['board_business_functions']['templateId'], request_type=request_type)
    new_board_business_functions_contentBody = board_business_functions_contentBody
    # 01-业务功能 模版页面 的 1.1.1 - 1.1.2 章节， (kCBykBMZ) 对应 1.1.1 光层业务功能-线路侧100G模块-基本配置-核心数据[otc-100g-base-c_m-100g]， 
    # (OcDLeKwK) 对应1.1.2 光层业务功能-客户侧模块-基本配置-核心数据[otc-10g-base-c_m-10g] ， 
    # (me4EnFkl) 对应1.1.3 光层业务功能-客户侧模块-MPO-核心数据[otc-10g-mpo-c_m-10g]
    # (THXoQv0b) 对应 1.1.6. 光层业务功能-线路侧100G_C04M4模块-基本配置-核心数据[otc-100g_c04m4-base-c_m-c04m4]
    delete_2_5_content = find_pattern_between('<h3 block-id=\"OcDLeKwK\"', '<h3 block-id=\"THXoQv0b\"', board_business_functions_contentBody)
    lineside_optical_layer = board_infos.get('线路侧光层业务', '')
    electrical_layer_service_mode = board_infos.get('部件承载电层业务模式', '')
    service_frm_chips = board_infos.get('业务FRM芯片', '')
    service_frm_chip_list = service_frm_chips.split(',')
    new_service_frm_chip_list = []
    for service_frm_chip in service_frm_chip_list:
        if service_frm_chip.strip():
            if 'fpga' in service_frm_chip.lower():
                need_name = 'fpga'
            if '业务frm' in service_frm_chip.lower():
                if electrical_layer_service_mode == '光模块部件_承载电层业务':
                    need_name = 'otc_v1'
                else:
                    need_name = service_frm_chip.split('_')[0]
            if need_name not in new_service_frm_chip_list:
                new_service_frm_chip_list.append(need_name.lower())
                if need_name == 'otc_v1':
                    break
    logger.info(f"----------new_service_frm_chip_list:{new_service_frm_chip_list}")
    # 0代表 合一单板（有frm）， 1 代表 合一单板（无frm）, 2 代表分离线路侧板 ， 3 代表 分离客户侧板， 4 代表桥接B卡和包交换PS交叉卡
    new_board_type = '0'
    if board_type in ['线路侧L卡']:
        if lineside_optical_layer and 'SFP' in lineside_optical_layer.upper():
            delete_1_content = find_pattern_between('<h3 block-id=\"kCBykBMZ\"', '<h3 block-id=\"OcDLeKwK\"', board_business_functions_contentBody)
            delete_2_content = find_pattern_between('<h3 block-id=\"OcDLeKwK\"', '<h3 block-id=\"me4EnFkl\"', board_business_functions_contentBody)
            new_board_business_functions_contentBody = board_business_functions_contentBody.replace(delete_1_content, '')
            new_board_business_functions_contentBody = new_board_business_functions_contentBody.replace(delete_2_5_content, delete_2_content)
        else:
            new_board_business_functions_contentBody = board_business_functions_contentBody.replace(delete_2_5_content, '')
        new_board_type = '2'
    elif board_type in ['客户侧C卡', '客户侧E卡']:
        delete_1_content = find_pattern_between('<h3 block-id=\"kCBykBMZ\"', '<h3 block-id=\"OcDLeKwK\"', board_business_functions_contentBody)
        new_board_business_functions_contentBody = board_business_functions_contentBody.replace(delete_1_content, '')
        new_board_type = '3'
    elif board_type in ['支线路合一卡']:
        if lineside_optical_layer and 'SFP' in lineside_optical_layer.upper():
            delete_1_content = find_pattern_between('<h3 block-id=\"kCBykBMZ\"', '<h3 block-id=\"OcDLeKwK\"', board_business_functions_contentBody)
            new_board_business_functions_contentBody = board_business_functions_contentBody.replace(delete_1_content, '')
        else:
            new_board_business_functions_contentBody = board_business_functions_contentBody
        if electrical_layer_service_mode == '光模块部件_承载电层业务':
            new_board_type = '1'
    elif board_type in ['桥接B卡' ,'包交换PS交叉卡']:
        delete_content = find_pattern_between('<h3 block-id=\"kCBykBMZ\"', '<h3 block-id=\"THXoQv0b\"', board_business_functions_contentBody)
        new_board_business_functions_contentBody = board_business_functions_contentBody.replace(delete_content, '')
        new_board_type = '4'
    lineside_optical_modules = board_infos.get('线路侧光模块', '')
    lineside_optical_module_list = lineside_optical_modules.split(',')
    lineside_optical_modules_content = find_pattern_between('<h3 block-id=\"THXoQv0b\"', '</div>', board_business_functions_contentBody, greed_flag=True) + '</div>'
    new_board_business_functions_contentBody = new_board_business_functions_contentBody.replace(lineside_optical_modules_content, '')
    copy_content = ''
    for lineside_optical_module in lineside_optical_module_list:
        pure_lineside_optical_module = lineside_optical_module.upper()
        if 'C04M4' in pure_lineside_optical_module:
            # THXoQv0b BtPxjivG
            copy_content += find_pattern_between('<h3 block-id=\"THXoQv0b\"', '<h3 block-id=\"BtPxjivG\"', board_business_functions_contentBody)

        elif 'C08M1' in pure_lineside_optical_module:
            # BtPxjivG Q91t39Lj
            copy_content += find_pattern_between('<h3 block-id=\"BtPxjivG\"', '<h3 block-id=\"Q91t39Lj\"', board_business_functions_contentBody)
        elif 'CD1' in pure_lineside_optical_module or 'PMCDDP1' in pure_lineside_optical_module:
            # Q91t39Lj EJlg5xBn
            copy_content += find_pattern_between('<h3 block-id=\"Q91t39Lj\"', '<h3 block-id=\"EJlg5xBn\"', board_business_functions_contentBody)
        elif 'M16M1' in pure_lineside_optical_module:
            # EJlg5xBn h2 l4X5J9FW
            copy_content += find_pattern_between('<h3 block-id=\"EJlg5xBn\"', '<h2 block-id=\"l4X5J9FW\"', board_business_functions_contentBody)
        else:
            pass
    new_board_business_functions_contentBody += copy_content
    # 01-业务功能 模版页面 提取单板树中的GEARBOX芯片内容，根据芯片名称来决定章节名称 <h3 block-id=\"\orzZZ1MI\" 8IJcCrm0 eRYCwGVA WSPQUgq9  he O7R9eKJe
    # 1.3. 业务_时钟数据恢复_功能-核心数据[svc_gearbox]
    first_content = find_pattern_between('<h2 block-id=\"l4X5J9FW\"', '<h3 block-id=\"orzZZ1MI\"', board_business_functions_contentBody)
    # gearbox_title_content = find_pattern_between('<h2 block-id=\"oKZo4rs1\"', '<h3 block-id=\"orzZZ1MI\"', board_business_functions_contentBody)
    # # 待填充的 second_content 代表 01-业务功能 模版页面中的全部 svc_gearbox 的 h3内容块
    gearboxs = board_infos.get('GEARBOX', '')
    gearbox_list = gearboxs.split(',')
    new_gearbox_list = []
    for gearbox in gearbox_list:
        if gearbox.strip():
            need_name = gearbox.split('_')[1]
            if need_name not in new_gearbox_list:
                new_gearbox_list.append(need_name.lower())
    logger.info(f"----------new_gearbox_list:{new_gearbox_list}")
    # 按实际的  svc_gearbox 芯片取值来增量添加 对应的内容块，从 业务_成帧_功能-核心数据[svc_frm] 二级标题内容块往前插入，每1个不同取值的svc_gearbox 芯片，就插入1个块
    copy_content = ''
    for gearbox in new_gearbox_list:
        if 'crt55321' in gearbox: # orzZZ1MI  8IJcCrm0 eRYCwGVA WSPQUgq9 8zrx4Q6a Lfz8Irqr 4AIgEBHV M0lwaSgq PSMuN1wy FYIZS4dC O4q7nE89 VVyIyIjZ RSo0hQfM  O7R9eKJe
            if new_board_type in ['2', '3']:
                copy_content += find_pattern_between('<h3 block-id=\"orzZZ1MI\"', '<h3 block-id=\"8IJcCrm0\"', board_business_functions_contentBody)
            elif new_board_type in ['0']:
                copy_content += find_pattern_between('<h3 block-id=\"8IJcCrm0\"', '<h3 block-id=\"eRYCwGVA\"', board_business_functions_contentBody)
            elif new_board_type in ['1']:
                copy_content += find_pattern_between('<h3 block-id=\"eRYCwGVA\"', '<h3 block-id=\"WSPQUgq9\"', board_business_functions_contentBody)
        elif 'crt88322' in gearbox: # WSPQUgq9 M0lwaSgq
            if new_board_type in ['2', '3']:
                copy_content += find_pattern_between('<h3 block-id=\"WSPQUgq9\"', '<h3 block-id=\"8zrx4Q6a\"', board_business_functions_contentBody)
            elif new_board_type in ['0']:
                copy_content += find_pattern_between('<h3 block-id=\"8zrx4Q6a\"', '<h3 block-id=\"4AIgEBHV\"', board_business_functions_contentBody)
            elif new_board_type in ['1']:
                copy_content += find_pattern_between('<h3 block-id=\"4AIgEBHV\"', '<h3 block-id=\"M0lwaSgq\"', board_business_functions_contentBody)
        elif 'jw8056' in gearbox: # M0lwaSgq O4q7nE89 
            if new_board_type in ['2', '3']:
                copy_content += find_pattern_between('<h3 block-id=\"M0lwaSgq\"', '<h3 block-id=\"PSMuN1wy\"', board_business_functions_contentBody)
            elif new_board_type in ['0']:
                copy_content += find_pattern_between('<h3 block-id=\"PSMuN1wy\"', '<h3 block-id=\"FYIZS4dC\"', board_business_functions_contentBody)
            elif new_board_type in ['1']:
                copy_content += find_pattern_between('<h3 block-id=\"FYIZS4dC\"', '<h3 block-id=\"O4q7nE89\"', board_business_functions_contentBody)
        elif 'mt3775' in gearbox: # O4q7nE89 h2 O7R9eKJe
            if new_board_type in ['2', '3']:
                copy_content += find_pattern_between('<h3 block-id=\"O4q7nE89\"', '<h3 block-id=\"VVyIyIjZ\"', board_business_functions_contentBody)
            elif new_board_type in ['0']:
                copy_content += find_pattern_between('<h3 block-id=\"VVyIyIjZ\"', '<h3 block-id=\"RSo0hQfM\"', board_business_functions_contentBody)
            elif new_board_type in ['1']:
                copy_content += find_pattern_between('<h3 block-id=\"RSo0hQfM\"', '<h2 block-id=\"O7R9eKJe\"', board_business_functions_contentBody)
        else:
            pass
    tmp_new_board_business_functions_contentBody = new_board_business_functions_contentBody + first_content + copy_content
    # 1.4. 业务_成帧_功能-核心数据[svc_frm]
    title_content = find_pattern_between('<h2 block-id=\"O7R9eKJe\"', '<h3 block-id=\"s696XMg7\"', board_business_functions_contentBody)
    new_copy_content = ''
    if new_board_type in ['2', '3']: # 支线路分离-客户侧-zx300(FRM芯片)，对应 01-业务功能 模版页面的 1.4.1 ~ 1.4.4 章节 中间有换行 + 不确定数量的空格，导致有问题
        copy_content = find_pattern_between('<h3 block-id=\"s696XMg7\"', '<h3 block-id=\"8bp0teUe\"', board_business_functions_contentBody)
        for service_frm_chip in new_service_frm_chip_list:
            if service_frm_chip == 'zx300':
                new_copy_content += copy_content
        new_board_business_functions_contentBody = tmp_new_board_business_functions_contentBody + title_content + new_copy_content
    elif new_board_type in ['1']:   # 支线路合一-无frm单板-otc(FRM芯片)，对应 01-业务功能 模版页面的 1.4.9 章节
        copy_content = find_pattern_between('<h3 block-id=\"IOMjHIMk\"', '</div>', board_business_functions_contentBody, greed_flag=True) + '</div>'
        new_board_business_functions_contentBody = tmp_new_board_business_functions_contentBody + title_content + copy_content
    elif new_board_type in ['0']: # 支线路合一-有frm单板-zx300(FRM芯片)，对应 01-业务功能 模版页面的 1.4.5 ~ 1.4.8 章节
        copy_content = find_pattern_between('<h3 block-id=\"8bp0teUe\"', '<h3 block-id=\"IOMjHIMk\"', board_business_functions_contentBody)
        for service_frm_chip in new_service_frm_chip_list:
            if service_frm_chip == 'zx300':
                new_copy_content += copy_content
        new_board_business_functions_contentBody = tmp_new_board_business_functions_contentBody + title_content + new_copy_content
    else:
        new_board_business_functions_contentBody = tmp_new_board_business_functions_contentBody + title_content
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id01 + "/view" 
    new_Icenter_content_html_set(url, new_board_business_functions_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag01:
        logger.info(f"  创建页面成功: ")
        create_flag01 = True
        page_url01 = url
    elif resp_flag01:
        create_flag01 = False
        page_url01 = url
    return new_board_type, new_service_frm_chip_list


def find_pattern_between(start, end, text, greed_flag=False, start_is_regex=False, end_is_regex=False):
    """
    改进版：可以选择是否将start和end视为正则表达式
    """
    if start_is_regex:
        escaped_start = start  # 已经是正则表达式，不转义
    else:
        escaped_start = re.escape(start)
    if end_is_regex:
        escaped_end = end  # 已经是正则表达式，不转义
    else:
        escaped_end = re.escape(end)
    pattern = rf'({escaped_start}.*?)(?={escaped_end})'
    if greed_flag:
        pattern = rf'({escaped_start}.*)(?={escaped_end})'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        return ''


def new_handle_00_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title00 = '00-' + board_name + '-单板-基础功能-核心数据'
    board_basic_functions_contentBody = yml_data['board']['board_basic_functions']['contentBody']
    resp_flag00, new_page_id00, create_page_flag00 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title00, board_basic_functions_contentBody, yml_data['board']['board_basic_functions']['templateId'], request_type=request_type)
    new_board_basic_functions_contentBody = filter_chapter_content(board_basic_functions_contentBody, board_infos)
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id00 + "/view" 
    new_Icenter_content_html_set(url, new_board_basic_functions_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag00 or resp_flag00:
        logger.info(f"  创建页面成功 或 页面已存在 ")
        create_flag00 = True
        page_url00 = url
    else:
        create_flag00 = False
    return create_flag00


def new_handle_01_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title01 = '01-' + board_name + '-单板-业务功能-核心数据'
    board_business_functions_contentBody = yml_data['board']['board_business_functions']['contentBody']
    resp_flag01, new_page_id01, create_page_flag01 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title01, board_business_functions_contentBody, yml_data['board']['board_business_functions']['templateId'], request_type=request_type)
    new_board_business_functions_contentBody = filter_chapter_content(board_business_functions_contentBody, board_infos)
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id01 + "/view" 
    new_Icenter_content_html_set(url, new_board_business_functions_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag01 or resp_flag01:
        logger.info(f"  创建页面成功 或 页面已存在 ")
        create_flag01 = True
        page_url01 = url
    else:
        create_flag01 = False
    return create_flag01


def new_handle_02_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title02 = '02-' + board_name + '-单板-OAM功能-核心数据'
    board_business_oam_contentBody = yml_data['board']['board_oam_functions']['contentBody']
    resp_flag02, new_page_id02, create_page_flag02 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title02, board_business_oam_contentBody, yml_data['board']['board_oam_functions']['templateId'], request_type=request_type)
    new_board_business_oam_contentBody = filter_chapter_content(board_business_oam_contentBody, board_infos)
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id02 + "/view" 
    new_Icenter_content_html_set(url, new_board_business_oam_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag02 or resp_flag02:
        logger.info(f"  创建页面成功 或 页面已存在 ")
        create_flag02 = True
        page_url02 = url
    else:
        create_flag02 = False
    return create_flag02


def new_handle_03_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title03 = '03-' + board_name + '-单板-高可用功能-核心数据'
    board_high_availability_contentBody = yml_data['board']['board_high_availability_functions']['contentBody']
    resp_flag03, new_page_id03, create_page_flag03 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title03, board_high_availability_contentBody, yml_data['board']['board_high_availability_functions']['templateId'], request_type=request_type)
    new_board_high_availability_contentBody = filter_chapter_content(board_high_availability_contentBody, board_infos)
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id03 + "/view" 
    new_Icenter_content_html_set(url, new_board_high_availability_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag03 or resp_flag03:
        logger.info(f"  创建页面成功 或 页面已存在 ")
        create_flag03 = True
        page_url03 = url
    else:
        create_flag03 = False
    return create_flag03


def new_handle_04_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type):
    page_title04 = '04-' + board_name + '-单板-扩展应用功能-核心数据'
    board_extended_application_contentBody = yml_data['board']['board_extended_application_functions']['contentBody']
    resp_flag04, new_page_id04, create_page_flag04 = atom_create_page(icenterAPI, spaceId, forth_pageId, page_title04, board_extended_application_contentBody, yml_data['board']['board_extended_application_functions']['templateId'], request_type=request_type)
    new_board_extended_application_contentBody = filter_chapter_content(board_extended_application_contentBody, board_infos)
    url = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id04 + "/view" 
    new_Icenter_content_html_set(url, new_board_extended_application_contentBody, icenterAPI, request_type=request_type)
    if create_page_flag04 or resp_flag04:
        logger.info(f"  创建页面成功 或 页面已存在 ")
        create_flag04 = True
        page_url04 = url
    else:
        create_flag04 = False
    return create_flag04


def extract_h3_blocks_to_dict(html):
    """
    提取所有 <h3 block-id="..."> 块，每个块到下一个带 block-id 的 <h2> 或 <h3> 之前（或不包含该标签）为止。
    返回字典 { 纯文本标题: 块HTML源码 }
    """
    # 匹配所有带 block-id 的 h2 或 h3 标签开始位置
    # 兼容属性值用单引号或双引号，也兼容 block-id 前后无额外空格的情况（通过 \b 单词边界）
    pattern = r'<\s*(h[23])\s[^>]*\bblock-id\s*=\s*["\'][^"\']*["\'][^>]*>'
    all_tags = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
    # 如果没有任何 h3 标签，直接返回空字典
    if not any(m.group(1) == 'h3' for m in all_tags):
        return {}
    result = {}
    for i, m in enumerate(all_tags):
        # 只处理 <h3> 作为块起点
        if m.group(1).lower() != 'h3':
            continue
        start = m.start()
        # 找到下一个带 block-id 的 h2 或 h3 的开始位置，作为当前块的结束
        end = len(html)  # 默认到文档末尾
        for j in range(i + 1, len(all_tags)):
            end = all_tags[j].start()
            break  # 取最近的一个
        block_html = html[start:end]
        # 从 block_html 中提取当前 <h3> 标签内部的内容，生成纯文本 key
        # 使用与上面相同的标签匹配模式，但限定在 block_html 内部
        h3_match = re.search(
            r'<\s*h3\s[^>]*\bblock-id\s*=\s*["\'][^"\']*["\'][^>]*>(.*?)</h3\s*>',
            block_html,
            re.IGNORECASE | re.DOTALL
        )
        if not h3_match:
            # 若标签未闭合，可跳过或根据需求处理
            continue
        inner = h3_match.group(1)
        key = re.sub(r'<[^>]+>', '', inner).strip()
        # 重复的 key 会被覆盖，如需保留多个可改为列表
        result[key] = block_html
    return result


# ---------- 第2步：从 h3 内部 HTML 中提取纯文本 ----------
def step2_inner_to_plain_text(h3_inner):
    """
    去除所有 HTML 标签，得到连续的纯文本。
    并去除首尾空白。
    """
    text = re.sub(r'<[^>]+>', '', h3_inner)
    return text.strip()


# ---------- 第3步：从纯文本中提取最后的 "x-x" 部分 ----------
def step3_extract_last_part(plain_text):
    """
    从形如 '单板描述功能-资源描述-基本配置-核心数据[bd_des-res-base-c_m-c_h]' 的文本中，
    提取方括号内最后两段（如 'c_m-c_h'）。
    如果找不到方括号，或方括号内不足两段，则返回 None。
    """
    match = re.search(r'\[([^\]]+)\]', plain_text)
    if not match:
        return None
    bracket_content = match.group(1)          # 例如 "bd_des-res-base-c_m-c_h"
    parts = bracket_content.split('-')
    if len(parts) >= 2:
        return '-'.join(parts[-2:])           # 取最后两段拼接
    return None


def get_filter_value(board_infos):
    board_type = board_infos.get('板卡类型', '')
    electrical_layer_service_mode = board_infos.get('部件承载电层业务模式', '')
    filter_value1 = []
    filter_value2 = []
    if '客户侧' in board_type:
        filter_value1 = ['c_m', 'sc']
    elif '线路侧' in board_type:
        filter_value1 = ['c_m', 'sl']
    elif '支线路合一卡' in board_type:
        if electrical_layer_service_mode == '光模块部件_承载电层业务':
            filter_value1 = ['c_m', 'mn']
        elif electrical_layer_service_mode == 'FRM部件_承载电层业务':
            filter_value1 = ['c_m', 'mf']
        elif electrical_layer_service_mode == 'FPGA部件承载_电层业务':
            filter_value1 = ['mn']
    lineside_optical_layer = board_infos.get('线路侧光层业务', '')
    clientside_optical_layer = board_infos.get('客户侧光层业务', '')
    lineside_optical_modules = board_infos.get('线路侧光模块', '')
    gearboxs = board_infos.get('GEARBOX', '')
    service_frm_chips = board_infos.get('业务FRM芯片', '')
    time_chips = board_infos.get('时钟芯片', '')
    rate_list = ['100G', '200G', '400G', '800G', '1600G']
    # 光模块器件匹配规则
    if clientside_optical_layer.strip() or (lineside_optical_layer.strip() and (not any(item.lower() in lineside_optical_layer.lower() for item in rate_list))):
        filter_value2.append('10g')
    if any(item.lower() in lineside_optical_layer.lower() for item in rate_list):
        filter_value2.append('100g')
        if lineside_optical_modules.strip():
            lineside_optical_module_list = lineside_optical_modules.split(',')
            for lineside_optical_module in lineside_optical_module_list:
                if any(item.lower() in lineside_optical_module.lower() for item in ['CD3', 'CC3', 'PMCDDP3']):
                    filter_value2.append('cd3')
                elif 'C04M4' in lineside_optical_module:
                    filter_value2.append('c04m4')
                elif any(item.lower() in lineside_optical_module.lower() for item in ['C08M1_', 'ZXC08M1']):
                    filter_value2.append('c08m1')
                elif any(item.lower() in lineside_optical_module.lower() for item in ['CD1', 'PMCDDP1']):
                    filter_value2.append('cd1x')
                elif 'M16M1_' in lineside_optical_module:
                    filter_value2.append('m16m1')
                elif 'M12M1_' in lineside_optical_module:
                    filter_value2.append('m12m1')
    # Framer模型匹配规则
    if electrical_layer_service_mode == 'FRM部件_承载电层业务' and 'ZX300_' in service_frm_chips:
        filter_value2.append('zx300')
    elif electrical_layer_service_mode == '光模块部件_承载电层业务':
        filter_value2.append('otc_v1')
    # GearBox模型匹配规则
    if gearboxs in ['联发科_MT3775', '集益威_JW8056', 'CREDO_CRT55321', 'CREDO_CRT88322', '联发科_MT3729', '博通_BCM82381']:
        filter_value2.append(gearboxs.split('_')[1].lower())
    # 时钟芯片匹配规则
    time_chip_list = time_chips.split(',')
    for time_chip in time_chip_list:
        if time_chip in ['芯科科技_SI5347', '奥拉_AU5327', '新港海岸_NCS23347']:
            filter_value2.append(time_chip.split('_')[1].lower())
    return filter_value1, filter_value2


def process_html(html_content):
    """
    处理 HTML 源码：
    1. 对于每一段“连续出现的 <h2> 序列（中间没有 <h3>）”，只保留最后一个 <h2>，删除其余 <h2>。
    2. 清理因删除标签而产生的多余空行。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    # 按文档顺序获取所有 h2 和 h3 标签
    tags = soup.find_all(['h2', 'h3'])
    current_group = []   # 当前连续 h2 组
    for tag in tags:
        if tag.name == 'h2':
            current_group.append(tag)
        else:  # 遇到 h3，处理之前累积的 h2 组
            if len(current_group) >= 2:
                # 保留最后一个，删除前面的
                for t in current_group[:-1]:
                    t.decompose()
            current_group = []   # 重置组
    # 处理文档末尾可能残留的连续 h2 组
    if len(current_group) >= 2:
        for t in current_group[:-1]:
            t.decompose()
    # 获取处理后的 HTML 字符串
    result_html = str(soup)
    # 清理多余空行：将连续的两个以上换行（及其间的空白）替换为一个换行
    # 这样可以消除因删除标签而留下的空白行，且不影响单行间距
    cleaned_html = re.sub(r'\n\s*\n', '\n', result_html)
    # 可选：去掉开头的多余空白行
    cleaned_html = cleaned_html.strip()
    return cleaned_html


def filter_chapter_content(content, board_infos):
    blocks_to_dict = extract_h3_blocks_to_dict(content)
    filter_value1, filter_value2 = get_filter_value(board_infos)
    flag1 = False
    flag2 = False
    new_content = content
    for block in list(blocks_to_dict.keys()):
        pt = step2_inner_to_plain_text(block)
        lp = step3_extract_last_part(pt)
        value1, value2 = lp.split('-')
        if value1 in filter_value1 or (len(filter_value1) > 1 and filter_value1[1] in value1) or value1 == 'c_m':
            flag1 = True
        else:
            flag1 = False
        if value2 in filter_value2 or value2 == 'c_h':
            flag2 = True
        else:
            flag2 = False
        if not (flag1 and flag2):
            new_content = new_content.replace(blocks_to_dict[block], '')
    return process_html(new_content)


def create_fifth_level_page(icenterAPI, spaceId, forth_pageId, board_infos, yml_data, request_type):
    create_flag00 = False
    create_flag01 = False
    create_flag02 = False
    create_flag03 = False
    create_flag04 = False
    try:
        board_name = board_infos.get('board', '')
        request_type = 'new'
        create_flag00 = new_handle_00_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type)
        create_flag01 = new_handle_01_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type)
        create_flag02 = new_handle_02_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type)
        create_flag03 = new_handle_03_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type)
        create_flag04 = new_handle_04_template(icenterAPI, board_infos, board_name, yml_data, spaceId, forth_pageId, request_type)
    except Exception as e:
        raise Exception(f"Error occurred while creating fifth level page.{str(e)}")
    return (create_flag00 & create_flag01 & create_flag02 & create_flag03 & create_flag04), "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + forth_pageId + "/view"


def create_forth_level_page(icenterAPI, spaceId, third_title, third_pageId, board_infos, yml_data, forth_children_title:list=[], request_type:str='new'):
    board_name = board_infos.get('board', '')
    third_title_split_list = third_title.split('-')
    if len(third_title_split_list) < 4:
        prefix = third_title.rsplit('-', 1)[0].replace('S', 'SL')
    elif len(third_title_split_list) > 3:
        prefix = third_title.rsplit('-', 2)[0].replace('S', 'SL')
    forth_children_title_nums = sorted(set([int(title.split('-')[2]) for title in forth_children_title]))
    num = find_new_integer(forth_children_title_nums)
    if num < 10:
        whole_prefix = prefix + '-000' + str(num)
    elif num < 100:
        whole_prefix = prefix + '-00' + str(num)
    elif num < 1000:
        whole_prefix = prefix + '-0' + str(num)
    else:
        whole_prefix = prefix + '-' + str(num)
    create_title1 = whole_prefix + '-' + board_name + '-单板方案'
    resp_flag1, forth_pageId, create_page_flag1 = atom_create_page(icenterAPI, spaceId, third_pageId, create_title1, yml_data['board']['board_solution']['contentBody'], yml_data['board']['board_solution']['templateId'], request_type)
    if create_page_flag1:
        create_fifth_level_page(icenterAPI, spaceId, forth_pageId, board_infos, yml_data, request_type)
        return create_page_flag1, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + forth_pageId + "/view" 
    elif resp_flag1:
        create_flag = False
        return create_flag, "" 


def create_third_level_page(icenterAPI, spaceId, second_title, second_pageId, board_infos, yml_data, third_children_title:list=[], request_type:str='new'):
    prefix = second_title.rsplit('-', 1)[0].replace('D', 'S')
    third_children_title_nums = sorted(set([int(title.split('-')[1][3:]) for title in third_children_title]))
    num = find_new_integer(third_children_title_nums)
    if num < 10:
        whole_prefix = prefix + '0' + str(num)
    else:
        whole_prefix = prefix + str(num)
    third_create_title = whole_prefix + '-' + board_infos.get('单板业务模型', '')
    resp_flag, third_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, third_create_title, request_type=request_type)
    if create_page_flag:
        create_flag, page_url = create_forth_level_page(icenterAPI, spaceId, third_create_title, third_pageId, board_infos, yml_data, request_type=request_type)
        return create_flag, page_url
    elif resp_flag:
        create_flag = False
        return create_flag, "" 


def create_second_level_page(icenterAPI, spaceId, first_key, first_value, board_infos, yml_data, second_children_title:list=[], request_type:str='new'):
    prefix = first_key.rsplit('-', 1)[0]
    second_children_title_nums = sorted(set([int(title.split('-')[1][2:]) for title in second_children_title]))
    num = find_new_integer(second_children_title_nums)
    if num < 10:
        whole_prefix = prefix + str(num)
    else:
        whole_prefix = prefix[:-1] + str(num)
    second_create_title = whole_prefix + '-' + board_infos.get('板卡类型', '')
    first_pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
    resp_flag, second_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, first_pageId, second_create_title, request_type=request_type)
    if create_page_flag:
        create_flag, page_url = create_third_level_page(icenterAPI, spaceId, second_create_title, second_pageId, board_infos, yml_data, request_type=request_type)
        return create_flag, page_url
    elif resp_flag:
        create_flag = False
        return create_flag, ""


def find_new_integer(nums):
    """
    找到一个新整数，使得数组加上这个整数后，从1开始的连续整数序列尽可能长
    """
    if not nums:
        return 1
    # 将数组转换为集合，便于快速查找
    num_set = set(nums)
    # 从1开始找第一个缺失的正整数
    missing = 1
    while missing in num_set:
        missing += 1
    return missing


def create_icenter_page(part, businessScheme:str='', schemeSlice:str='', children:str='', other_info:dict={}, employ_no:str='', token:str='', type:str='boardComponents', request_type:str='new'):
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        icenterAPI = IcenterAPI(employ_no, token=token)
    if type.lower() =='boardcomponents':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b2e14c845f0511f0a7de47256a4ab960/view"
    elif type.lower() == 'feature':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
        yml_data = handle_latest_icenter_templates(icenterAPI, type=type)
    elif type.lower() == 'board':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aa5a5fc55f0511f0be86a5129dbea099/view"
        yml_data = handle_latest_icenter_templates(icenterAPI, type=type)
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)
    create_flag = False
    if type.lower() =='boardcomponents':
        for first_key, first_value in first_children_map.items():
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 2 and part == first_key_split_list[2]:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                if len(second_children_url) < 1:
                    create_title = 'HEBU-S0101-' + businessScheme
                    first_pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
                    resp_flag, second_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, first_pageId, create_title)
                    if create_page_flag:
                        create_title = 'HEBU-S0101-01-' + schemeSlice
                        resp_flag, new_page_id, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, create_title)
                        if create_page_flag:
                            print(f"  创建页面成功: ")
                            create_flag = True
                            return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                        elif resp_flag:
                            create_flag = False
                            return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                else:
                    for second_key, second_value in second_children_map.items():
                        second_key_split_list = second_key.split('-')
                        if len(second_key_split_list) > 2 and businessScheme == '-'.join(second_key_split_list[2:]):
                            third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                            if len(third_children_url) > 0:
                                mid_str = '-'
                                title_prex = max([title.split('-', 1)[0] + mid_str + title.split('-', 2)[1] + mid_str + title.split('-', 3)[2] for title in third_children_title])
                                if int(title_prex.rsplit('-', 1)[1]) < 9:
                                    mid_str = '-0'
                                create_title = title_prex.rsplit('-', 1)[0] + mid_str + str(int(title_prex.rsplit('-', 1)[1]) + 1) + '-' + schemeSlice
                            else:
                                create_title = 'HEBU-S0101-01-' + schemeSlice
                            second_pageId, spaceId = icenterAPI.get_pageid_spaceid(second_value)
                            resp_flag, new_page_id, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, create_title)
                            if create_page_flag:
                                print(f"  创建页面成功: ")
                                create_flag = True
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                            elif resp_flag:
                                create_flag = False
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                    if not create_flag:
                        mid_str = '-'
                        title_prex = max([title.split('-', 1)[0] + mid_str + title.split('-', 2)[1] for title in second_children_title])
                        mid = title_prex.rsplit('-', 1)[1]
                        create_title = title_prex.rsplit('-', 1)[0] + mid_str + mid[0] + str(int(mid[1:]) + 1) + mid_str + businessScheme
                        first_pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
                        resp_flag, second_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, first_pageId, create_title)
                        if create_page_flag:
                            create_title = 'HEBU-S0101-01-' + schemeSlice
                            resp_flag, new_page_id, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, create_title)
                            if create_page_flag:
                                print(f"  创建页面成功: ")
                                create_flag = True
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                            elif resp_flag:
                                create_flag = False
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
    elif type.lower() =='feature':
        for first_key, first_value in first_children_map.items():
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part == first_key_split_list[1]:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                if len(second_children_url) < 1:
                    create_title = first_key_split_list[0] + '01-' + businessScheme
                    first_pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
                    resp_flag, second_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, first_pageId, create_title)
                    if create_page_flag:
                        create_title = 'FD'  + schemeSlice[1:]
                        resp_flag, third_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, create_title)
                        if create_page_flag:
                            create_title1 = schemeSlice + '-特性分析'
                            create_title2 = schemeSlice + '-特性方案'
                            resp_flag1, forth_pageId, create_page_flag1 = atom_create_page(icenterAPI, spaceId, third_pageId, create_title1, yml_data['feature']['feature_analysis']['contentBody'], yml_data['feature']['feature_analysis']['templateId'])
                            resp_flag2, forth_pageId2, create_page_flag2 = atom_create_page(icenterAPI, spaceId, third_pageId, create_title2, yml_data['feature']['feature_name']['contentBody'], yml_data['feature']['feature_name']['templateId'])
                            if create_page_flag1 and children.strip():
                                resp_flag, new_page_id, create_page_flag3 = atom_create_page(icenterAPI, spaceId, forth_pageId, children + '-特性分析', yml_data['feature']['children_feature_design']['contentBody'], yml_data['feature']['children_feature_design']['templateId'])
                                if create_page_flag3:
                                    print(f"  创建页面成功: ")
                                    create_flag = True
                                    return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                                elif resp_flag:
                                    create_flag = False
                                    return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                            elif create_page_flag1:
                                print(f"  创建页面成功: ")
                                create_flag = True
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + forth_pageId + "/view" 
                            elif resp_flag1:
                                create_flag = False
                                return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + forth_pageId + "/view" 
                else:
                    for second_key, second_value in second_children_map.items():
                        second_key_split_list = second_key.split('-')
                        if len(second_key_split_list) > 1 and businessScheme == second_key_split_list[1]:
                            create_title = 'FD'  + schemeSlice[1:]
                            second_pageId, spaceId = icenterAPI.get_pageid_spaceid(second_value)
                            resp_flag, third_pageId, create_page_flag = atom_create_page(icenterAPI, spaceId, second_pageId, create_title)
                            if third_pageId:
                                create_title1 = schemeSlice + '-特性分析'
                                create_title2 = schemeSlice + '-特性方案'
                                resp_flag1, forth_pageId, create_page_flag1 = atom_create_page(icenterAPI, spaceId, third_pageId, create_title1, yml_data['feature']['feature_analysis']['contentBody'], yml_data['feature']['feature_analysis']['templateId'])
                                resp_flag2, forth_pageId2, create_page_flag2 = atom_create_page(icenterAPI, spaceId, third_pageId, create_title2, yml_data['feature']['feature_name']['contentBody'], yml_data['feature']['feature_name']['templateId'])
                                if forth_pageId and children.strip():
                                    resp_flag, new_page_id, create_page_flag3 = atom_create_page(icenterAPI, spaceId, forth_pageId, children + '-特性分析', yml_data['feature']['children_feature_design']['contentBody'], yml_data['feature']['children_feature_design']['templateId'])
                                    if create_page_flag3:
                                        logger.info(f"  创建页面成功: ")
                                        create_flag = True
                                        return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                                    elif resp_flag:
                                        create_flag = False
                                        return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
                                elif forth_pageId:
                                    if create_page_flag1:
                                        create_flag = True
                                    else:
                                        create_flag = False
                                    return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + forth_pageId + "/view" 
                                else:
                                    logger.error(f"  查询或创建 {create_title1} 页面失败 ")
                                    break
                            else:
                                logger.error(f"  查询或创建 {create_title} 页面失败 ")
                                break
    elif type.lower() =='board':
        board_infos = {'board': pub_remove_after_parentheses(children), '板卡类型': businessScheme, '单板业务模型': schemeSlice}
        new_items = {k: v for k, v in other_info.items() if k not in board_infos}
        board_infos.update(new_items)
        for first_key, first_value in first_children_map.items():
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part in first_key_split_list:
                first_pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                if len(second_children_url) < 1:
                    return create_second_level_page(icenterAPI, spaceId, first_key, first_value, board_infos, yml_data, request_type=request_type)
                else:
                    for second_key, second_value in second_children_map.items():
                        second_key_split_list = second_key.split('-')
                        if len(second_key_split_list) > 1 and businessScheme in second_key_split_list:
                            second_pageId, spaceId = icenterAPI.get_pageid_spaceid(second_value)
                            third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                            if len(third_children_url) < 1:
                                return create_third_level_page(icenterAPI, spaceId, second_key, second_pageId, board_infos, yml_data, request_type=request_type)
                            else:
                                for third_key, third_value in third_children_map.items():
                                    third_key_split_list = third_key.split('-')
                                    if (len(third_key_split_list) > 1 and len(third_key_split_list) < 4 and schemeSlice in third_key_split_list) or (len(third_key_split_list) > 3 and schemeSlice in (third_key_split_list[2] + '-' + third_key_split_list[3])):
                                        third_pageId, spaceId = icenterAPI.get_pageid_spaceid(third_value)
                                        forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                                        board_name = board_infos.get('board', '')
                                        if len(forth_children_url) < 1:
                                            return create_forth_level_page(icenterAPI, spaceId, third_key, third_pageId, board_infos, yml_data, request_type=request_type)
                                        else:
                                            for forth_key, forth_value in forth_children_map.items():
                                                forth_key_split_list = forth_key.split('-')
                                                if len(forth_key_split_list) > 1 and board_name in forth_key_split_list:
                                                    fifth_children_url, fifth_children_title, fifth_children_map = icenter_children_get(forth_value, icenterAPI)
                                                    if len(fifth_children_url) < 5:
                                                        forth_pageId, spaceId = icenterAPI.get_pageid_spaceid(forth_value)
                                                        return create_fifth_level_page(icenterAPI, spaceId, forth_pageId, board_infos, yml_data, request_type)
                                                    else:
                                                        return create_flag, forth_value
                                            if not create_flag:
                                                return create_forth_level_page(icenterAPI, spaceId, third_key, third_pageId, board_infos, yml_data, forth_children_title, request_type)
                                if not create_flag:
                                    return create_third_level_page(icenterAPI, spaceId, second_key, second_pageId, board_infos, yml_data, third_children_title, request_type)
                    if not create_flag:
                        return create_second_level_page(icenterAPI, spaceId, first_key, first_value, board_infos, yml_data, second_children_title, request_type)
    return create_flag, ""


def delete_icenter_page(part, businessScheme, schemeSlice, children:str='', employ_no:str='', token:str='', type:str='feature'):
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        icenterAPI = IcenterAPI(employ_no, token=token)
    if type.lower() =='boardcomponents':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b2e14c845f0511f0a7de47256a4ab960/view"
    elif type.lower() == 'feature':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)
    delete_page_flag = False
    if type.lower() =='feature':
        for first_key, first_value in first_children_map.items():
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part == first_key_split_list[1]:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                if len(second_children_url) < 1:
                    return True
                else:
                    for second_key, second_value in second_children_map.items():
                        second_key_split_list = second_key.split('-')
                        if len(second_key_split_list) > 1 and businessScheme == second_key_split_list[1]:
                            create_title = 'FD'  + schemeSlice[1:]
                            second_pageId, spaceId = icenterAPI.get_pageid_spaceid(second_value)
                            resp_flag, page_id = icenterAPI.is_exist(spaceId, second_pageId, create_title)
                            if resp_flag:
                                if not children.strip():
                                    delete_page_flag = icenterAPI.delete_page(spaceId, page_id, True)
                                    return delete_page_flag
                                else:
                                    create_title1 = schemeSlice + '-特性分析'
                                    resp_flag, analysis_page_id = icenterAPI.is_exist(spaceId, page_id, create_title1)
                                    if resp_flag:
                                        create_title_child = children.strip() + '-特性分析'
                                        delete_page_flag = atom_delete_page(icenterAPI, spaceId, analysis_page_id, create_title_child)
                                        return delete_page_flag
                                    else:
                                        return True
                            else:
                                return True
    return delete_page_flag


def update_icenter_page(part, businessScheme, schemeSlice, children:str='', employ_no:str='', token:str='', type:str='feature', tag_flag=False, request_type:str='old'):
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        icenterAPI = IcenterAPI(employ_no, token=token)
    if type.lower() =='boardcomponents':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b2e14c845f0511f0a7de47256a4ab960/view"
    elif type.lower() == 'feature':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
        yml_data = handle_latest_icenter_templates(icenterAPI, type=type)
    elif type.lower() == 'board':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aa5a5fc55f0511f0be86a5129dbea099/view"
        yml_data = handle_latest_icenter_templates(icenterAPI, type=type)
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)
    if type.lower() =='feature':
        for first_key, first_value in first_children_map.items():
            feature_info = dict()
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part == first_key_split_list[1]:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                for second_key, second_value in second_children_map.items():
                    second_key_split_list = second_key.split('-')
                    if len(second_key_split_list) > 1 and businessScheme == second_key_split_list[1]:
                        third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                        for third_key, third_value in third_children_map.items():
                            third_key_split_list = third_key.split('-')
                            if len(third_key_split_list) > 1 and (third_key == 'FD' + schemeSlice[1:]):
                                forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                                for forth_key, forth_value in forth_children_map.items():
                                    if '-特性分析' in forth_key:
                                        if len(children.strip()) < 1:
                                            new_Icenter_content_html_set(forth_value, yml_data['feature']['feature_analysis']['contentBody'], icenterAPI)
                                            if tag_flag:
                                                contentid, spaceid = icenterAPI.get_pageid_spaceid(forth_value)
                                                icenterAPI.add_page_tags(contentid, '特性')
                                                icenterAPI.add_page_tags(contentid, '特性分析')
                                        else:
                                            fifth_children_url, fifth_children_title, fifth_children_map = icenter_children_get(forth_value, icenterAPI)
                                            for fifth_key, fifth_value in fifth_children_map.items():
                                                if children.strip() == fifth_key[:-5]:
                                                    replace_str1 = children.strip()
                                                    contentid, spaceid = icenterAPI.get_pageid_spaceid(fifth_value)
                                                    replace_str2 = "https://aip.zte.com.cn/zTest/#/test-platform/product?currentPrjId=8a81d9936abed43e016ac060428b0000&spaceId=" + spaceid + "&suiteId=" + contentid
                                                    new_Icenter_content_html_set(fifth_value, replace_br_td(yml_data['feature']['children_feature_design']['contentBody'], replace_str1, replace_str2), icenterAPI)
                                                    if tag_flag:
                                                        icenterAPI.add_page_tags(contentid, '特性分析')
                                                        icenterAPI.add_page_tags(contentid, '子特性分析')
                                                        icenterAPI.add_page_tags(contentid, '子特性')
                                                        icenterAPI.add_page_tags(contentid, 'ST_功能')
                                                    break
                                    elif '-特性方案' in forth_key and len(children.strip()) < 1:
                                        new_Icenter_content_html_set(forth_value, yml_data['feature']['feature_name']['contentBody'],icenterAPI)
                                        if tag_flag:
                                            contentid, spaceid = icenterAPI.get_pageid_spaceid(forth_value)
                                            icenterAPI.add_page_tags(contentid, '特性方案设计')
    elif type.lower() == 'board':
        for first_key, first_value in first_children_map.items():
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part in first_key_split_list:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                for second_key, second_value in second_children_map.items():
                    second_key_split_list = second_key.split('-')
                    if len(second_key_split_list) > 1 and businessScheme in second_key_split_list:
                        third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                        for third_key, third_value in third_children_map.items():
                            third_key_split_list = third_key.split('-')
                            if (len(third_key_split_list) > 1 and len(third_key_split_list) < 4 and schemeSlice in third_key_split_list) or (len(third_key_split_list) > 3 and schemeSlice in (third_key_split_list[2] + '-' + third_key_split_list[3])):
                                forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                                board_name = pub_remove_after_parentheses(children)
                                for forth_key, forth_value in forth_children_map.items():
                                    forth_key_split_list = forth_key.split('-')
                                    if len(forth_key_split_list) > 1 and board_name in forth_key_split_list:
                                        new_Icenter_content_html_set(forth_value, yml_data['board']['board_solution']['contentBody'], icenterAPI, request_type)
                                        fifth_children_url, fifth_children_title, fifth_children_map = icenter_children_get(forth_value, icenterAPI)
                                        for fifth_key, fifth_value in fifth_children_map.items():
                                            if '基础功能' in fifth_key:
                                                new_Icenter_content_html_set(fifth_value, yml_data['board']['board_basic_functions']['contentBody'], icenterAPI, request_type)
                                            elif '业务功能' in fifth_key:
                                                new_Icenter_content_html_set(fifth_value, yml_data['board']['board_business_functions']['contentBody'], icenterAPI, request_type)
                                            elif 'OAM功能' in fifth_key:
                                                new_Icenter_content_html_set(fifth_value, yml_data['board']['board_oam_functions']['contentBody'], icenterAPI, request_type)
                                            elif '高可用功能' in fifth_key:
                                                new_Icenter_content_html_set(fifth_value, yml_data['board']['board_high_availability_functions']['contentBody'], icenterAPI, request_type)
                                            elif '扩展应用功能' in fifth_key:
                                                new_Icenter_content_html_set(fifth_value, yml_data['board']['board_extended_application_functions']['contentBody'], icenterAPI, request_type)
                                        return


def query_icenter_page(type:str='feature'):
    if type.lower() =='boardcomponents':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b2e14c845f0511f0a7de47256a4ab960/view"
    elif type.lower() == 'feature':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    elif type.lower() == 'board':
        url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/aa5a5fc55f0511f0be86a5129dbea099/view"
    icenterAPI = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)
    result = []
    if type.lower() =='feature':
        for first_key, first_value in first_children_map.items():
            feature_info = dict()
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 :
                feature_info["feature_first_classification"] = first_key_split_list[1]
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                for second_key, second_value in second_children_map.items():
                    second_key_split_list = second_key.split('-')
                    if len(second_key_split_list) > 1:
                        feature_info["feature_second_classification"] = second_key_split_list[1]
                        third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                        for third_key, third_value in third_children_map.items():
                            third_key_split_list = third_key.split('-')
                            if len(third_key_split_list) > 1:
                                forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                                for forth_key, forth_value in forth_children_map.items():
                                    if '-特性分析' in forth_key:
                                        feature_info["feature_name"] = forth_key[:-5]
                                        feature_info["children_feature_name"] = ""
                                        feature_info["feature_content_link"] = forth_value
                                        result.append(copy.deepcopy(feature_info))
                                        fifth_children_url, fifth_children_title, fifth_children_map = icenter_children_get(forth_value, icenterAPI)
                                        for fifth_key, fifth_value in fifth_children_map.items():
                                            feature_info["children_feature_name"] = fifth_key[:-5]
                                            feature_info["feature_content_link"] = fifth_value
                                            result.append(copy.deepcopy(feature_info))
    elif type.lower() =='board':
        for first_key, first_value in first_children_map.items():
            board_info = dict()
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 2 :
                board_info["product_name"] = first_key_split_list[2]
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                for second_key, second_value in second_children_map.items():
                    second_key_split_list = second_key.split('-')
                    if len(second_key_split_list) > 2:
                        board_info["board_type"] = second_key_split_list[2]
                        third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                        for third_key, third_value in third_children_map.items():
                            third_key_split_list = third_key.split('-')
                            if len(third_key_split_list) > 2 and len(third_key_split_list) < 4:
                                board_info["board_business_model"] = third_key_split_list[2]
                            elif len(third_key_split_list) > 3:
                                board_info["board_business_model"] = (third_key_split_list[2] + '-' + third_key_split_list[3])
                            forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                            for forth_key, forth_value in forth_children_map.items():
                                forth_key_split_list = forth_key.split('-')
                                if len(forth_key_split_list) > 4 and '-单板方案' in forth_key:
                                    board_info["board_name"] = forth_key_split_list[3]
                                    board_info["board_content_link"] = forth_value
                                    result.append(copy.deepcopy(board_info))                                       

    return result


def new_update_icenter_page(part, businessScheme, schemeSlice, children:str='', employ_no:str='', token:str='', type:str='feature', tag_flag=False, request_type:str='old'):
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        icenterAPI = IcenterAPI(employ_no, token=token)
    url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)
    if type.lower() =='feature':
        for first_key, first_value in first_children_map.items():
            feature_info = dict()
            first_key_split_list = first_key.split('-')
            if len(first_key_split_list) > 1 and part == first_key_split_list[1]:
                second_children_url, second_children_title, second_children_map = icenter_children_get(first_value, icenterAPI)
                for second_key, second_value in second_children_map.items():
                    second_key_split_list = second_key.split('-')
                    if len(second_key_split_list) > 1 and businessScheme == second_key_split_list[1]:
                        third_children_url, third_children_title, third_children_map = icenter_children_get(second_value, icenterAPI)
                        for third_key, third_value in third_children_map.items():
                            third_key_split_list = third_key.split('-')
                            if len(third_key_split_list) > 1 and (third_key == 'FD' + schemeSlice[1:]):
                                forth_children_url, forth_children_title, forth_children_map = icenter_children_get(third_value, icenterAPI)
                                for forth_key, forth_value in forth_children_map.items():
                                    if '-特性分析' in forth_key:
                                        if len(children.strip()) < 1:
                                            if tag_flag:
                                                contentid, spaceid = icenterAPI.get_pageid_spaceid(forth_value)
                                                icenterAPI.add_page_tags(contentid, '特性')
                                                icenterAPI.add_page_tags(contentid, '特性分析')
                                        else:
                                            fifth_children_url, fifth_children_title, fifth_children_map = icenter_children_get(forth_value, icenterAPI)
                                            for fifth_key, fifth_value in fifth_children_map.items():
                                                if children.strip() == fifth_key[:-5]:
                                                    replace_str1 = children.strip()
                                                    contentid, spaceid = icenterAPI.get_pageid_spaceid(fifth_value)
                                                    if tag_flag:
                                                        icenterAPI.add_page_tags(contentid, '特性分析')
                                                        icenterAPI.add_page_tags(contentid, '子特性分析')
                                                        icenterAPI.add_page_tags(contentid, '子特性')
                                                        icenterAPI.add_page_tags(contentid, 'ST_功能')
                                                    break