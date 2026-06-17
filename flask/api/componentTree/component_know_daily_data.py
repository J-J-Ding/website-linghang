import os
import re
import aes
import sys
import pymysql
import datetime
import requests
from componentTree.icenter_token import token_ok, get_token, get_host_ip
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from bs4 import BeautifulSoup
from componentTree.data_model import query_knowledge_component_tree_nodes, replace_knowledge_component_tree_nodes
from get_icenter import Icenter_content_html_get, Icenter_content_html_set, Icenter_children_get, Icenter_title_get, Icenter_block_get, Icenter_block_set


AES_KEY = "asdasdasdasdasdb"
ICENTER_USER_ID = ""
ICENTER_USER_TOKEN = ""
CUR_DATE = ""

# 组件树页面列表
COMP_TREE_DIR_DICT = {
    "支撑": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9ce9fdc00ee711f0b2c3b75a02dcbeb7/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/108a98d63bc511f0b7898f0a658efff7/view"
    ],
    "L0": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c47642211f4e11f0aee1853811e2336a/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/8af116ba5bd611f08c8fa7466ab6b7a3/view"
    ],
    "L1": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9de71306f96e11efb81c0bfbc4e63315/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c082f09ef96e11ef9e50cb809b24249f/view"
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c90f0c4ff96e11ef8a7d6f3b17d16194/view"
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/bf17306d66ef11f083f1976d88e954ad/view"
    ],
    "L2": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/6b10aa01204d11f09f38bd067b2197b5/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/3c5021928f7711f0a290d3dfc9605be0/view"
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/084f733e8f7711f0a5362d460b990f16/view"
    ],
    "智控": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/07887b1b4b5a11f08200e91213ab284f/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/971cdd9367b811f084bb83141293d8d2/view"
    ],
}


def get_user_token(en_httppassword):
    eg = aes.EncryptDate(AES_KEY)
    passwd = eg.decrypt(en_httppassword)
    X_Emp_No = re.sub(r"\D", "", ICENTER_USER_ID)
    loginsyscode = 'Portal'
    originsyscode = ''
    token_status = 0
    ret, token = icenter_token.token_ok(token_status, X_Emp_No, passwd, loginsyscode, originsyscode)
    if token:
        os.environ['USERNAME'] = X_Emp_No
        os.environ['PASSWORD'] = passwd
        return token
    else:
        print("获取用户TOCKEN失败")


def handle_comp_tree():
    comp_tree_page_list = []
    for field,field_comp_tree_dir_list in COMP_TREE_DIR_DICT.items():
        for field_comp_tree_dir_dir_item in field_comp_tree_dir_list:
            icenter_children_get_list = get_icenter.Icenter_children_get(field_comp_tree_dir_dir_item)
            if len(icenter_children_get_list) == 0: continue
            comp_tree_page_dict = icenter_children_get_list[2]
            # 遍历组件页面
            for comp_tree_page_title,comp_tree_page_url in comp_tree_page_dict.items():
                comp_name = is_valid_comp_tree_page_title_format(comp_tree_page_title)
                if not comp_name: continue
                get_icenter_list = get_icenter.Get_icenter(comp_tree_page_url)
                if len(get_icenter_list) == 0: continue
                comp_tree_page_context = get_icenter_list[1]
                page_info = get_icenter_list[3]
                print(page_info)
                # 获取组件页面第一个表格
                comp_tree_page_info_dict = get_comp_tree_page_info(comp_tree_page_context)
                page_status = comp_tree_page_info_dict.get("page_status")
                comp_engineering_info_dict = get_comp_engineering_info_dict(comp_tree_page_context)
                if not page_status: "空页面"
                comp_tree_page_item = {
                    "page_title": comp_tree_page_title,
                    "field_name": field,
                    "comp_name": comp_name,
                    "module_name": "",
                    "module_num": 0,
                    "page_url": comp_tree_page_url,
                    "page_status": page_status,
                    "page_person": comp_tree_page_info_dict.get("page_person", ""),
                    "page_se": comp_tree_page_info_dict.get("page_se", ""),
                    "page_tl": comp_tree_page_info_dict.get("page_tl", ""),
                    "page_tse": comp_tree_page_info_dict.get("page_tse", ""),
                    "update_by": page_info.get("updateBy"),
                    "update_date": page_info.get("updateDate"),
                    "editor_num": page_info.get("edit", {}).get("editor_num", 0),
                    "edit_num": page_info.get("edit", {}).get("edit_num", 0),
                    "view_visitor_num": (page_info.get("view") or {}).get("totalVisitorCount", 0),
                    "view_visit_num": (page_info.get("view") or {}).get("totalViewCount", 0),
                    "ai_adapt_num": page_info.get("ai", {}).get("ai_adapt_num", 0),
                    "ai_gene_num": page_info.get("ai", {}).get("ai_gene_num", 0),
                    "finish_flag": "Y" if page_status == "已定稿" else "N",
                    "comp_engineering": comp_engineering_info_dict,
                }
                print(comp_tree_page_title)
                icenter_children_get_list = get_icenter.Icenter_children_get(comp_tree_page_url)
                if len(icenter_children_get_list) == 0: continue
                module_page_dict = icenter_children_get_list[2]
                # 遍历模块页面
                temp_module_num = 0
                for module_page_title,module_page_url in module_page_dict.items():
                    print(module_page_title)
                    sub_comp_name = is_valid_sub_comp_tree_page_title_format(module_page_title)
                    if not sub_comp_name:
                        module_name = is_valid_module_page_title_format(module_page_title)
                        if not module_name: continue
                        get_icenter_list = get_icenter.Get_icenter(module_page_url)
                        if len(get_icenter_list) == 0: continue
                        module_page_context = get_icenter_list[1]
                        page_info = get_icenter_list[3]
                        comp_tree_page_info_dict = get_comp_tree_page_info(module_page_context)
                        page_status = comp_tree_page_info_dict.get("page_status")
                        if not page_status: continue
                        comp_tree_page_list.append(
                            {
                                "page_title": module_page_title,
                                "field_name": field,
                                "comp_name": comp_name,
                                "module_name": module_name,
                                "module_num": 0,
                                "page_url": module_page_url,
                                "page_status": page_status,
                                "page_person": comp_tree_page_info_dict.get("page_person", ""),
                                "page_se": comp_tree_page_info_dict.get("page_se", ""),
                                "page_tl": comp_tree_page_info_dict.get("page_tl", ""),
                                "page_tse": comp_tree_page_info_dict.get("page_tse", ""),
                                "update_by": page_info.get("updateBy"),
                                "update_date": page_info.get("updateDate"),
                                "editor_num": page_info.get("edit", {}).get("editor_num", 0),
                                "edit_num": page_info.get("edit", {}).get("edit_num", 0),
                                "view_visitor_num": (page_info.get("view") or {}).get("totalVisitorCount", 0),
                                "view_visit_num": (page_info.get("view") or {}).get("totalViewCount", 0),
                                "ai_adapt_num": page_info.get("ai", {}).get("ai_adapt_num", 0),
                                "ai_gene_num": page_info.get("ai", {}).get("ai_gene_num", 0),
                                "finish_flag": "Y" if page_status == "已定稿" else "N",
                            }
                        )
                        temp_module_num += 1
                        print(module_page_title)
                    else:
                        icenter_children_get_list = get_icenter.Icenter_children_get(module_page_url)
                        if len(icenter_children_get_list) == 0: continue
                        sub_module_page_dict = icenter_children_get_list[2]
                        for sub_module_page_title,sub_module_page_url in sub_module_page_dict.items():
                            sub_comp_name = is_valid_sub_comp_tree_page_title_format(sub_module_page_title)
                            if not sub_comp_name:
                                module_name = is_valid_module_page_title_format(sub_module_page_title)
                                if not module_name: continue
                                get_icenter_list = get_icenter.Get_icenter(sub_module_page_url)
                                if len(get_icenter_list) == 0: continue
                                module_page_context = get_icenter_list[1]
                                page_info = get_icenter_list[3]
                                comp_tree_page_info_dict = get_comp_tree_page_info(module_page_context)
                                page_status = comp_tree_page_info_dict.get("page_status")
                                if not page_status: continue
                                comp_tree_page_list.append(
                                    {
                                        "page_title": sub_module_page_title,
                                        "field_name": field,
                                        "comp_name": comp_name,
                                        "module_name": module_name,
                                        "module_num": 0,
                                        "page_url": sub_module_page_url,
                                        "page_status": page_status,
                                        "page_person": comp_tree_page_info_dict.get("page_person", ""),
                                        "page_se": comp_tree_page_info_dict.get("page_se", ""),
                                        "page_tl": comp_tree_page_info_dict.get("page_tl", ""),
                                        "page_tse": comp_tree_page_info_dict.get("page_tse", ""),
                                        "update_by": page_info.get("updateBy"),
                                        "update_date": page_info.get("updateDate"),
                                        "editor_num": page_info.get("edit", {}).get("editor_num", 0),
                                        "edit_num": page_info.get("edit", {}).get("edit_num", 0),
                                        "view_visitor_num": (page_info.get("view") or {}).get("totalVisitorCount", 0),
                                        "view_visit_num": (page_info.get("view") or {}).get("totalViewCount", 0),
                                        "ai_adapt_num": page_info.get("ai", {}).get("ai_adapt_num", 0),
                                        "ai_gene_num": page_info.get("ai", {}).get("ai_gene_num", 0),
                                        "finish_flag": "Y" if page_status == "已定稿" else "N",
                                    }
                                )
                                temp_module_num += 1
                                print(sub_module_page_title)
                # 最后补充组件数据
                comp_tree_page_item["module_num"] = temp_module_num
                comp_tree_page_list.append(comp_tree_page_item)
    # 初始化统计看板数据
    comp_tree_board_dict = {
        field: {
            "date": CUR_DATE,
            "field_name": field,
            "comp_sum_num": 0,
            "comp_initial_num": 0,
            "comp_reviewed_num": 0,
            "comp_revision_num": 0,
            "comp_finish_num": 0,
            "comp_sum_editor_num": 0,
            "comp_sum_edit_num": 0,
            "comp_sum_view_visitor_num": 0,
            "comp_sum_view_visit_num": 0,
            "comp_sum_ai_adapt_num": 0,
            "comp_sum_ai_gene_num": 0,
            "module_sum_num": 0,
            "module_initial_num": 0,
            "module_reviewed_num": 0,
            "module_revision_num": 0,
            "module_finish_num": 0,
            "module_sum_editor_num": 0,
            "module_sum_edit_num": 0,
            "module_sum_view_visitor_num": 0,
            "module_sum_view_visit_num": 0,
            "module_sum_ai_adapt_num": 0,
            "module_sum_ai_gene_num": 0,
        } for field in COMP_TREE_DIR_DICT.keys()
    }

    # 状态与字段映射关系
    status_to_field_map = {
        "初始": ("initial", 1),
        "已初审": ("reviewed", 1),
        "修订中": ("revision", 1),
        "已定稿": ("finish", 1),
    }

    # 需要累加的数值字段映射（item字段名 → 看板字段后缀）
    numeric_fields_map = {
        "editor_num": "sum_editor_num",
        "edit_num": "sum_edit_num",
        "view_visitor_num": "sum_view_visitor_num",
        "view_visit_num": "sum_view_visit_num",
        "ai_adapt_num": "sum_ai_adapt_num",
        "ai_gene_num": "sum_ai_gene_num",
    }

    # 遍历页面列表进行计数
    for item in comp_tree_page_list:
        field_name = item.get("field_name")
        page_status = item.get("page_status")
        module_name = item.get("module_name")
        # 跳过无效字段或状态
        if not field_name or field_name not in comp_tree_board_dict:
            continue
        # 判断是 comp 还是 module
        prefix = "module" if module_name else "comp"
        # 1. 处理状态字段
        if page_status in status_to_field_map:
            status_key, _ = status_to_field_map[page_status]
            status_field = f"{prefix}_{status_key}_num"
            comp_tree_board_dict[field_name][status_field] += 1
            # 同时增加总数（sum_num）
            sum_field = f"{prefix}_sum_num"
            comp_tree_board_dict[field_name][sum_field] += 1
        # 2. 处理数值累加字段（如 edit_num, view_num 等）
        for item_key, board_suffix in numeric_fields_map.items():
            value = item.get(item_key, 0)
            if isinstance(value, (int, float)):
                board_key = f"{prefix}_{board_suffix}"
                comp_tree_board_dict[field_name][board_key] += value
    # 汇总所有领域的数据为“波分中心”
    pw_center_summary = {
        "date": CUR_DATE,
        "field_name": "波分中心",
        "comp_sum_num": 0,
        "comp_initial_num": 0,
        "comp_reviewed_num": 0,
        "comp_revision_num": 0,
        "comp_finish_num": 0,
        "comp_sum_editor_num": 0,
        "comp_sum_edit_num": 0,
        "comp_sum_view_visitor_num": 0,
        "comp_sum_view_visit_num": 0,
        "comp_sum_ai_adapt_num": 0,
        "comp_sum_ai_gene_num": 0,
        "module_sum_num": 0,
        "module_initial_num": 0,
        "module_reviewed_num": 0,
        "module_revision_num": 0,
        "module_finish_num": 0,
        "module_sum_editor_num": 0,
        "module_sum_edit_num": 0,
        "module_sum_view_visitor_num": 0,
        "module_sum_view_visit_num": 0,
        "module_sum_ai_adapt_num": 0,
        "module_sum_ai_gene_num": 0,
    }

    # 累加各领域数据
    for field_data in comp_tree_board_dict.values():
        for key in pw_center_summary:
            if key not in ["date", "field_name"]:
                pw_center_summary[key] += field_data.get(key, 0)

    # 将汇总数据加入看板字典
    comp_tree_board_dict["波分中心"] = pw_center_summary
    comp_tree_board_list = list(comp_tree_board_dict.values())

    # 存储组件树信息和看板数据
    know_table.update_know_comp_tree_page_table_comp_tree_page_list(comp_tree_page_list)
    know_table.add_know_comp_tree_board_table_comp_tree_board_list(comp_tree_board_list)


def is_valid_comp_tree_page_title_format(component_str):
    if not isinstance(component_str, str) or not component_str.strip():
        return ""
    pattern = r'^C-[A-Za-z]\d+-(.*)组件$'
    match = re.match(pattern, component_str)
    if match:
        return match.group(1)
    else:
        return ""


def is_valid_sub_comp_tree_page_title_format(component_str):
    """
    验证子组件页面标题格式是否正确
    
    子组件命名规则：SC{编号}-{子组件名称}
    示例：SC001-数据处理，SC12-控制管理
    
    Args:
        component_str: 待验证的子组件名称字符串
    
    Returns:
        bool: 格式是否正确
    """
    if not isinstance(component_str, str) or not component_str.strip():
        return False
    pattern = r'^SC\d+-(.*)$'
    match = re.match(pattern, component_str)
    return bool(match)


def is_valid_module_page_title_format(module_str):
    """
    验证模块页面标题格式是否正确
    
    模块命名规则：M{编号}-{模块名称}
    编号可以是纯数字或带小数点的数字（如 M007、M007.3）
    示例：M001-数据备份处理，M007.3-CRYPT_DOMAIN_FSM_DECRYPT 模块
    
    Args:
        module_str: 待验证的模块名称字符串
    
    Returns:
        str: 如果格式正确返回模块名称部分，否则返回空字符串
    """
    if not isinstance(module_str, str) or not module_str.strip():
        return ""
    # 支持带小数点的编号，如 M007.3
    pattern = r'^M[\d.]+-(.*)$'
    match = re.match(pattern, module_str)
    if match:
        return match.group(1)
    else:
        return ""

# 获取页面的第一个表格
def get_comp_tree_page_info(html_text):
    person_info_dict = {}
    if html_text:
        content = BeautifulSoup(html_text, 'html.parser')
        target_table = content.find('table')
        if target_table:
            try:
                trs = target_table.find_all('tr')
                for tr in trs:
                    th = tr.find('th')
                    if th and th.get_text().strip() == "页面状态":
                        td = th.find_next_sibling('td')
                        select_tag = td.find('select')
                        if select_tag:
                            selected_option = select_tag.find('option', selected=True)
                            if selected_option:
                                person_info_dict["page_status"] = selected_option.get_text().strip().replace("\ufeff", "")
                            else:
                                person_info_dict["page_status"] = ''
                        else:
                            person_info_dict["page_status"] = td.get_text().strip().replace("\ufeff", "")
                    if th and th.get_text().strip() == "页面守护人":
                        person_info_dict["page_person"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                        if ',' not in person_info_dict["page_person"]:
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["page_person"])
                            if matches:
                                person_info_dict["page_person"] = ', '.join(matches)
                    if th and th.get_text().strip() == "SE":
                        person_info_dict["SE"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                        if ',' not in person_info_dict["SE"]:
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["SE"])
                            if matches:
                                person_info_dict["SE"] = ', '.join(matches)
                    if th and th.get_text().strip() == "TL":
                        person_info_dict["TL"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                        if ',' not in person_info_dict["TL"]:
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["TL"])
                            if matches:
                                person_info_dict["TL"] = ', '.join(matches)
                    if th and th.get_text().strip() == "TSE":
                        person_info_dict["TSE"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                        if ',' not in person_info_dict["TSE"]:
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["TSE"])
                            if matches:
                                person_info_dict["TSE"] = ', '.join(matches)
            except Exception as e:
                print(f"获取表格信息失败，{e}")
    return person_info_dict


def get_comp_engineering_info_dict(html_text):
    """
    从HTML中提取包含“组件关键能力”的标题后的第一个表格，
    并解析“组件重生”、“组件升级”、“NSR”、“转控分离”、“ISSU”所在行的内容。
    """
    comp_engineering_info_dict = {}

    if not html_text:
        return comp_engineering_info_dict

    content = BeautifulSoup(html_text, 'html.parser')

    # 查找任意标签中包含“组件关键能力”的第一个标题（常见于 h1-h4, p, div 等）
    heading = None
    for tag in content.find_all(['h1', 'h2', 'h3', 'h4',]):
        if "组件关键能力" in tag.get_text():
            heading = tag
            break

    if not heading:
        print("未找到包含“组件关键能力”的标题")
        return comp_engineering_info_dict

    # 从该标题开始，查找其后第一个 <table>
    next_table = None
    current = heading.find_next()
    while current:
        if current.name == 'table':
            next_table = current
            break
        current = current.find_next()

    if not next_table:
        print("未找到“组件关键能力”标题后的第一个表格")
        return comp_engineering_info_dict

    # 遍历表格中的每一行
    for tr in next_table.find_all('tr'):
        cells = tr.find_all(['td', 'th'])
        if len(cells) < 2:
            continue

        key = cells[0].get_text().strip().replace("\ufeff", "")
        value = cells[1].get_text().strip().replace("\ufeff", "")

        # 精确匹配所需的能力项
        if key in {"组件重生", "组件升级", "NSR", "转控分离", "ISSU"}:
            comp_engineering_info_dict[key] = {"desc": value, "ret": "未知"}
            if "不支持" in value:
                comp_engineering_info_dict[key]["ret"] = "不支持"
            elif "不需要" in value:
                comp_engineering_info_dict[key]["ret"] = "不需要"
            else:
                comp_engineering_info_dict[key]["ret"] = "支持"
    return comp_engineering_info_dict




if __name__ == "__main__":
    ICENTER_USER_ID = sys.argv[1]
    en_httppassword = sys.argv[2]
    ICENTER_USER_TOKEN = get_user_token(en_httppassword)

    CUR_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"开始处理知识建设数据")
    # 读取组件树信息
    print(f"开始处理组件树数据")
    handle_comp_tree()
    print(f"结束处理组件树数据")
    print(f"结束处理知识建设数据")