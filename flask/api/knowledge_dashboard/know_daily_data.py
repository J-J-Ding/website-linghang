import os
import re
import aes
import sys
import time
import pymysql
import datetime
import requests
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from flask import Flask
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from knowledge_dashboard import know_table
from electric_knowledge.data_model import db
from knowledge_dashboard.get_icenter import Icenter_content_html_get, Icenter_content_html_set, Icenter_children_get, Icenter_title_get, Icenter_block_get, Icenter_block_set, Get_icenter


# 数据库配置
DB_HOST = "10.239.69.17"
DB_DATABASE_KNOW_BOARD = "knowledge_engineering"
DB_USER = "root"
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = 3306
DB6_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_DATABASE_KNOW_BOARD}",
    'bind_key': 'db5'
}

# 应用数据库配置
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB6_CONFIG['url']
app.config['SQLALCHEMY_BINDS'] = {DB6_CONFIG['bind_key']: DB6_CONFIG['url']}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 30, 'pool_recycle': 3600, 'pool_pre_ping': True}
db.init_app(app)

# 配置日志记录
logger = logging.getLogger(__name__)

# 全局变量
AES_KEY = "asdasdasdasdasdb"
ICENTER_USER_ID = ""
CUR_DATE = ""
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


def init_icenter_env(en_httppassword):
    eg = aes.EncryptDate(AES_KEY)
    passwd = eg.decrypt(en_httppassword)
    X_Emp_No = re.sub(r"\D", "", ICENTER_USER_ID)
    os.environ["USERNAME"] = X_Emp_No
    os.environ["PASSWORD"] = passwd


def handle_comp_tree():
    comp_tree_page_list = []
    total_comp_num = 0
    total_module_num = 0

    for field, field_comp_tree_dir_list in COMP_TREE_DIR_DICT.items():
        print(f"开始处理领域：【{field}】, 领域目录数：{len(field_comp_tree_dir_list)}")
        field_comp_num = 0
        field_module_num = 0

        for index, field_comp_tree_dir_item in enumerate(field_comp_tree_dir_list, 1):
            print(f"\n处理领域目录 [{index}/{len(field_comp_tree_dir_list)}]: {field_comp_tree_dir_item}")
            icenter_children_get_list = Icenter_children_get(field_comp_tree_dir_item)
            if len(icenter_children_get_list) == 0:
                print(f"目录 {field_comp_tree_dir_item} 无子节点，跳过")
                continue
            comp_tree_page_dict = icenter_children_get_list[2]
            print(f"获取到 {len(comp_tree_page_dict)} 个组件页面")

            # 遍历组件页面
            for comp_tree_page_title, comp_tree_page_url in comp_tree_page_dict.items():
                comp_name = is_valid_comp_tree_page_title_format(comp_tree_page_title)
                if not comp_name:
                    print(f"组件标题格式验证失败，跳过：{comp_tree_page_title}")
                    continue
                print(f"处理组件 [{comp_name}]: {comp_tree_page_title}")
                
                # 添加重试逻辑调用 Get_icenter
                get_icenter_list = None
                for attempt in range(3):
                    try:
                        get_icenter_list = Get_icenter(comp_tree_page_url)
                        if get_icenter_list and get_icenter_list[0] is not None:  # title不为None
                            break
                        else:
                            print(f"[第{attempt+1}次尝试] 组件页面获取返回空结果，等待后重试...")
                            if attempt < 2:
                                time.sleep(2 ** attempt)
                    except Exception as e:
                        print(f"[第{attempt+1}次尝试] 组件页面获取异常：{e}")
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                
                if get_icenter_list is None or get_icenter_list[0] is None:
                    print(f"严重错误：组件页面 {comp_tree_page_url} 三次尝试均失败，跳过此组件")
                    continue
                comp_tree_page_context = get_icenter_list[1]
                page_info = get_icenter_list[3]
                print(f"页面信息：{page_info}")
                # 获取组件页面第一个表格
                comp_tree_page_info_dict = get_comp_tree_page_info(comp_tree_page_context)
                page_status = comp_tree_page_info_dict.get("page_status")
                if not page_status:
                    print(f"组件页面状态为空，标记为'空页面'")
                    page_status = "空页面"
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
                    "comp_engineering": {},
                    "script_date": CUR_DATE
                }
                print(f"组件状态：{page_status}, 完成标志：{comp_tree_page_item['finish_flag']}")
                icenter_children_get_list = Icenter_children_get(comp_tree_page_url)
                if len(icenter_children_get_list) == 0:
                    print(f"组件子节点获取失败：{comp_tree_page_url}")
                    continue
                module_page_dict = icenter_children_get_list[2]
                print(f"组件包含 {len(module_page_dict)} 个子节点")

                # 遍历模块页面
                temp_module_num = 0
                valid_module_num = 0

                for module_page_title, module_page_url in module_page_dict.items():
                    print(f"检查子节点：{module_page_title}")
                    sub_comp_name = is_valid_sub_comp_tree_page_title_format(module_page_title)
                    if not sub_comp_name:
                        module_name = is_valid_module_page_title_format(module_page_title)
                        if not module_name:
                            print(f"模块标题格式验证失败，跳过：{module_page_title}")
                            continue
                        print(f"处理模块 [{module_name}]: {module_page_title}")
                        
                        # 添加重试逻辑调用 Get_icenter
                        get_icenter_list = None
                        for attempt in range(3):
                            try:
                                get_icenter_list = Get_icenter(module_page_url)
                                if get_icenter_list and get_icenter_list[0] is not None:  # title不为None
                                    break
                                else:
                                    print(f"[第{attempt+1}次尝试] 模块页面获取返回空结果，等待后重试...")
                                    if attempt < 2:
                                        time.sleep(2 ** attempt)
                            except Exception as e:
                                print(f"[第{attempt+1}次尝试] 模块页面获取异常：{e}")
                                if attempt < 2:
                                    time.sleep(2 ** attempt)
                        
                        if get_icenter_list is None or get_icenter_list[0] is None:
                            print(f"警告：模块页面 {module_page_url} 三次尝试均失败，跳过此模块")
                            continue
                        module_page_context = get_icenter_list[1]
                        page_info = get_icenter_list[3]
                        comp_tree_page_info_dict = get_comp_tree_page_info(module_page_context)
                        page_status = comp_tree_page_info_dict.get("page_status")
                        if not page_status:
                            print(f"模块页面状态为空，跳过")
                            continue
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
                                "script_date": CUR_DATE
                            }
                        )
                        temp_module_num += 1
                        valid_module_num += 1
                        field_module_num += 1
                        print(f"模块已添加，状态：{page_status}")
                    else:
                        print(f"检测到子组件节点：{module_page_title}")
                        icenter_children_get_list = Icenter_children_get(module_page_url)
                        if len(icenter_children_get_list) == 0:
                            print(f"子组件节点获取失败：{module_page_url}")
                            continue
                        sub_module_page_dict = icenter_children_get_list[2]
                        print(f"子组件包含 {len(sub_module_page_dict)} 个孙节点")
                        for sub_module_page_title, sub_module_page_url in sub_module_page_dict.items():
                            sub_comp_name = is_valid_sub_comp_tree_page_title_format(sub_module_page_title)
                            if not sub_comp_name:
                                module_name = is_valid_module_page_title_format(sub_module_page_title)
                                if not module_name:
                                    print(f"模块标题格式验证失败，跳过：{sub_module_page_title}")
                                    continue
                                print(f"处理模块 [{module_name}]: {sub_module_page_title}")
                                
                                # 添加重试逻辑调用 Get_icenter
                                get_icenter_list = None
                                for attempt in range(3):
                                    try:
                                        get_icenter_list = Get_icenter(sub_module_page_url)
                                        if get_icenter_list and get_icenter_list[0] is not None:  # title不为None
                                            break
                                        else:
                                            print(f"[第{attempt+1}次尝试] 孙模块页面获取返回空结果，等待后重试...")
                                            if attempt < 2:
                                                time.sleep(2 ** attempt)
                                    except Exception as e:
                                        print(f"[第{attempt+1}次尝试] 孙模块页面获取异常：{e}")
                                        if attempt < 2:
                                            time.sleep(2 ** attempt)
                                
                                if get_icenter_list is None or get_icenter_list[0] is None:
                                    print(f"警告：孙模块页面 {sub_module_page_url} 三次尝试均失败，跳过此模块")
                                    continue
                                module_page_context = get_icenter_list[1]
                                page_info = get_icenter_list[3]
                                comp_tree_page_info_dict = get_comp_tree_page_info(module_page_context)
                                page_status = comp_tree_page_info_dict.get("page_status")
                                if not page_status:
                                    print(f"模块页面状态为空，跳过")
                                    continue
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
                                        "script_date": CUR_DATE
                                    }
                                )
                                temp_module_num += 1
                                valid_module_num += 1
                                field_module_num += 1
                                print(f"模块状态：{page_status}")
                # 最后补充组件数据
                comp_tree_page_item["module_num"] = temp_module_num
                comp_tree_page_list.append(comp_tree_page_item)
                field_comp_num += 1
                total_comp_num += 1
                total_module_num += temp_module_num
                print(f"组件处理完成：{comp_name}, 模块数：{temp_module_num}")
        print(f"领域【{field}】处理完成统计, 组件数{field_comp_num}, 模块数{field_module_num}")
    print(f"组件树数据采集完成统计, 总组件数{total_comp_num},  总模块数{total_module_num}, 总页面数{len(comp_tree_page_list)}")
    # 初始化统计看板数据
    print(f"\n开始统计数据看板, 领域数{len(COMP_TREE_DIR_DICT)}")
    comp_tree_board_dict = {
        field: {
            "date": CUR_DATE,
            "field_name": field,
            "comp_sum_num": 0,
            "comp_initial_num": 0,
            "comp_reviewed_num": 0,
            "comp_revision_num": 0,
            "comp_finish_num": 0,
            "comp_blank_num": 0,
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
            "module_blank_num": 0,
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
        "空页面": ("blank", 1),
    }

    # 数值字段映射（item 字段 -> 看板字段后缀）
    numeric_fields_map = {
        "editor_num": "sum_editor_num",
        "edit_num": "sum_edit_num",
        "view_visitor_num": "sum_view_visitor_num",
        "view_visit_num": "sum_view_visit_num",
        "ai_adapt_num": "sum_ai_adapt_num",
        "ai_gene_num": "sum_ai_gene_num",
    }

    # 遍历页面列表进行计数
    print(f"开始遍历 {len(comp_tree_page_list)} 个页面进行统计...")
    stat_comp_num = 0
    stat_module_num = 0

    for index, item in enumerate(comp_tree_page_list, 1):
        field_name = item.get("field_name")
        page_status = item.get("page_status")
        module_name = item.get("module_name")
        # 跳过无效字段或状态
        if not field_name or field_name not in comp_tree_board_dict:
            print(f"[{index}/{len(comp_tree_page_list)}] 跳过无效领域：{field_name}")
            continue
        # 判断是 comp 还是 module
        prefix = "module" if module_name else "comp"
        if prefix == "comp":
            stat_comp_num += 1
        else:
            stat_module_num += 1
        print(f"[{index}/{len(comp_tree_page_list)}] 统计 {prefix}: {item.get('page_title')} | 状态：{page_status} | 领域：{field_name}")
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
    print(f"统计完成：组件 {stat_comp_num} 个，模块 {stat_module_num} 个")
    # 输出各领域统计详情
    print(f"\n各领域统计详情:")
    for field_name, field_stats in comp_tree_board_dict.items():
        print(f"【{field_name}】(日期：{field_stats['date']})")
        print(f"组件总计：{field_stats['comp_sum_num']} (初始:{field_stats['comp_initial_num']}, 已初审:{field_stats['comp_reviewed_num']}, 修订中:{field_stats['comp_revision_num']}, 已定稿:{field_stats['comp_finish_num']}, 空页面:{field_stats['comp_blank_num']})")
        print(f"模块总计：{field_stats['module_sum_num']} (初始:{field_stats['module_initial_num']}, 已初审:{field_stats['module_reviewed_num']}, 修订中:{field_stats['module_revision_num']}, 已定稿:{field_stats['module_finish_num']}, 空页面:{field_stats['module_blank_num']})")
        print(f"编辑人数：组件={field_stats['comp_sum_editor_num']}, 模块={field_stats['module_sum_editor_num']}")
        print(f"编辑次数：组件={field_stats['comp_sum_edit_num']}, 模块={field_stats['module_sum_edit_num']}")

    # 汇总所有领域的数据为"波分中心"
    print(f"\n开始汇总'波分中心'数据...")
    pw_center_summary = {
        "date": CUR_DATE,
        "field_name": "波分中心",
        "comp_sum_num": 0,
        "comp_initial_num": 0,
        "comp_reviewed_num": 0,
        "comp_revision_num": 0,
        "comp_finish_num": 0,
        "comp_blank_num": 0,
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
        "module_blank_num": 0,
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
    print(f"'波分中心'汇总完成:")
    print(f"组件总计：{pw_center_summary['comp_sum_num']} (初始:{pw_center_summary['comp_initial_num']}, 已初审:{pw_center_summary['comp_reviewed_num']}, 修订中:{pw_center_summary['comp_revision_num']}, 已定稿:{pw_center_summary['comp_finish_num']}, 空页面:{pw_center_summary['comp_blank_num']})")
    print(f"模块总计：{pw_center_summary['module_sum_num']} (初始:{pw_center_summary['module_initial_num']}, 已初审:{pw_center_summary['module_reviewed_num']}, 修订中:{pw_center_summary['module_revision_num']}, 已定稿:{pw_center_summary['module_finish_num']}, 空页面:{pw_center_summary['module_blank_num']})")

    # 将汇总数据加入看板字典
    comp_tree_board_dict["波分中心"] = pw_center_summary

    # # 获取变更详情数据
    # print(f"\n开始计算变更详情...")
    # ret = know_table.get_know_comp_tree_page_table_change_detail_dict(comp_tree_page_list)

    # # 将变更详情整合到看板字典中
    # print(f"正在将变更详情整合到看板数据...")
    # for field_name, board_item in comp_tree_board_dict.items():
    #     # 获取该领域的变更数据，如果没有则使用空字典
    #     change_data = ret.get(field_name, {"comp": [], "module": []})
    #     # 添加两个新字段
    #     board_item["comp_change_detail"] = change_data["comp"]
    #     board_item["module_change_detail"] = change_data["module"]
    comp_tree_board_list = list(comp_tree_board_dict.values())

    # 存储组件树信息和看板数据
    print(f"\n开始写入数据库...")
    print(f"写入组件树页面表：{len(comp_tree_page_list)} 条记录")
    print(f"写入组件树看板表：{len(comp_tree_board_list)} 条记录")
    know_table.update_know_comp_tree_page_table_comp_tree_page_list(comp_tree_page_list)
    know_table.add_know_comp_tree_board_table_comp_tree_board_list(comp_tree_board_list)
    print("✓ 组件树数据处理全部完成！")


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
    if not isinstance(component_str, str) or not component_str.strip():
        return ""
    if component_str.startswith("SC"):
        return True
    else:
        return False


def is_valid_module_page_title_format(module_str):
    if not isinstance(module_str, str) or not module_str.strip():
        return ""
    pattern = r'^M\d+-(.*)$'
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
                for index, tr in enumerate(trs):
                    # ✅ 先检查 tr 是否有效
                    if not tr:
                        print(f"第 {index} 行为空，跳过")
                        continue
                    th = tr.find('th')
                    # ✅ 确保 th 存在后再调用其方法
                    if not th:
                        continue
                    try:
                        th_text = th.get_text().strip()
                    except Exception as e:
                        print(f"第 {index} 行获取 th 文本失败：{e}")
                        continue
                    if th_text == "页面状态":
                        td = th.find_next_sibling('td')
                        if td:  
                            select_tag = td.find('select')
                            if select_tag:
                                selected_option = select_tag.find('option', selected=True)
                                if selected_option:
                                    person_info_dict["page_status"] = selected_option.get_text().strip().replace("\ufeff", "")
                                else:
                                    person_info_dict["page_status"] = ''
                            else:
                                person_info_dict["page_status"] = td.get_text().strip().replace("\ufeff", "")
                        else:
                            print("未找到'页面状态'对应的 td 单元格")
                    elif th_text == "页面守护人":
                        td = th.find_next_sibling('td')
                        if td:  
                            person_info_dict["page_person"] = td.get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["page_person"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["page_person"])
                                if matches:
                                    person_info_dict["page_person"] = ', '.join(matches)
                    elif th_text == "SE":
                        td = th.find_next_sibling('td')
                        if td:  
                            person_info_dict["page_se"] = td.get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["page_se"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["page_se"])
                                if matches:
                                    person_info_dict["page_se"] = ', '.join(matches)
                    elif th_text == "TL":
                        td = th.find_next_sibling('td')
                        if td:  
                            person_info_dict["page_tl"] = td.get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["page_tl"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["page_tl"])
                                if matches:
                                    person_info_dict["page_tl"] = ', '.join(matches)
                    elif th_text == "TSE":
                        td = th.find_next_sibling('td')
                        if td:  
                            person_info_dict["page_tse"] = td.get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["page_tse"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["page_tse"])
                                if matches:
                                    person_info_dict["page_tse"] = ', '.join(matches)
            except Exception as e:
                logger.error(f"获取表格信息失败：{e}", exc_info=True)
    return person_info_dict



if __name__ == "__main__":
    ICENTER_USER_ID = "10210415"
    en_httppassword = "tVAD4WMW4hy+nFNghziM9A=="

    init_icenter_env(en_httppassword)

    with app.app_context():
        CUR_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
        print("开始处理组件树数据")
        handle_comp_tree()
        print("结束处理组件树数据")
