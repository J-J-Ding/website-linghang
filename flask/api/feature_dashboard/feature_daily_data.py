import os
import re
import sys
import datetime
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from flask import Flask
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from feature_dashboard import feature_table
from electric_knowledge.data_model import db
from knowledge_dashboard.get_icenter import Icenter_children_get, Get_icenter
from knowledge_dashboard.know_daily_data import get_comp_tree_page_info
from knowledge_dashboard import aes


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

# 特性树领域目录字典 — key 即 field_name，通过目录归属判定领域
FEATURE_TREE_DIR_DICT = {
    "L0": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/d4a2c95fd72311efa6e991b9604c470f/view"
    ],
    "L1": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    ],
    "L2": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/99da86d820b511f09fccbb17049e688c/view"
    ],
    "智控": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b6c030a5ef2d11efab0767decfd9208f/view"
    ],
    "支撑": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9b8d3215ef8711ef9f097df5f06ee3d8/view"
    ],
}

# 跳过的标题（精确匹配）
SKIP_TITLE_PATTERNS = [
    "汇总信息",
    "优质特性",
    "EDFA增益控制特性分析",
    "特性分析-所有页面统计汇总",
    "特性分析-已定稿页面统计汇总",
    "特性方案-已定稿页面统计汇总",
]

# ── 正则模式 ──
# FD 特性目录（跳过，不参与统计）
FD_PATTERN = re.compile(r'^FD\d+-[A-Z]-.+$')

# F 特性分析（编号可能含-dd后缀，如F160101-05）
F_ANALYSIS_PATTERN = re.compile(r'^F(\d+(?:-\d+)?)-([A-Z])-(.+)-特性分析$')
# F 特性方案
F_SCHEME_PATTERN = re.compile(r'^F(\d+(?:-\d+)?)-([A-Z])-(.+)-特性方案$')

# FS 子特性分析
FS_ANALYSIS_PATTERN = re.compile(r'^FS(\d+(?:-\d+)+)-([A-Z])-(.+)-特性分析$')
# FS 子特性方案
FS_SCHEME_PATTERN = re.compile(r'^FS(\d+(?:-\d+)+)-([A-Z])-(.+)-特性方案$')
# FS 子特性分析（兼容"子特性分析"后缀）
FS_SUB_ANALYSIS_PATTERN = re.compile(r'^FS(\d+(?:-\d+)+)-([A-Z])-(.+)-子特性分析$')
# FS 子特性方案（兼容"子特性方案"后缀）
FS_SUB_SCHEME_PATTERN = re.compile(r'^FS(\d+(?:-\d+)+)-([A-Z])-(.+)-子特性方案$')


def init_icenter_env(en_httppassword):
    eg = aes.EncryptDate(AES_KEY)
    passwd = eg.decrypt(en_httppassword)
    X_Emp_No = re.sub(r"\D", "", ICENTER_USER_ID)
    os.environ["USERNAME"] = X_Emp_No
    os.environ["PASSWORD"] = passwd


def should_skip_title(title):
    """判断标题是否应跳过"""
    if not title or not isinstance(title, str):
        return True
    title_stripped = title.strip()
    for pattern in SKIP_TITLE_PATTERNS:
        if title_stripped == pattern:
            return True
    if "（待删除）" in title_stripped or "(待删除)" in title_stripped:
        return True
    return False


def parse_feature_title(title):
    """
    解析特性树页面标题，返回结构化信息。
    FD目录返回 None（不参与统计）。
    不匹配的标题也返回 None。
    返回格式: {
        "feature_num": "F010101" 或 "FS030110-01",
        "type_flag": "O",
        "feature_name": "业务波CDWSS波长选择",
        "page_type_name": "特性分析"/"特性方案"/"子特性分析"/"子特性方案",
        "is_sub_feature": 0 或 1,
    }
    """
    if not title or not isinstance(title, str):
        return None
    title_stripped = title.strip()

    # FD 目录页面 — 跳过
    if FD_PATTERN.match(title_stripped):
        return None

    # F 特性分析
    match = F_ANALYSIS_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"F{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "特性分析",
            "is_sub_feature": 0,
        }

    # F 特性方案
    match = F_SCHEME_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"F{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "特性方案",
            "is_sub_feature": 0,
        }

    # FS 子特性分析
    match = FS_ANALYSIS_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"FS{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "特性分析",
            "is_sub_feature": 1,
        }

    # FS 子特性方案
    match = FS_SCHEME_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"FS{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "特性方案",
            "is_sub_feature": 1,
        }

    # FS 子特性分析（兼容"子特性分析"后缀）
    match = FS_SUB_ANALYSIS_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"FS{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "子特性分析",
            "is_sub_feature": 1,
        }

    # FS 子特性方案（兼容"子特性方案"后缀）
    match = FS_SUB_SCHEME_PATTERN.match(title_stripped)
    if match:
        return {
            "feature_num": f"FS{match.group(1)}",
            "type_flag": match.group(2),
            "feature_name": match.group(3),
            "page_type_name": "子特性方案",
            "is_sub_feature": 1,
        }

    return None


def build_page_item(title, url, field_name, parsed, page_detail, page_info):
    """构建特性树页面记录"""
    page_status = page_detail.get("page_status")
    if not page_status:
        page_status = "空页面"
    return {
        "page_title": title,
        "field_name": field_name,
        "feature_num": parsed["feature_num"],
        "feature_name": parsed["feature_name"],
        "page_type_name": parsed["page_type_name"],
        "type_flag": parsed["type_flag"],
        "is_sub_feature": parsed["is_sub_feature"],
        "scheme_num": 0,
        "page_url": url,
        "page_status": page_status,
        "page_person": page_detail.get("page_person", ""),
        "page_se": page_detail.get("page_se", ""),
        "page_tl": page_detail.get("page_tl", ""),
        "page_tse": page_detail.get("page_tse", ""),
        "update_by": page_info.get("updateBy"),
        "update_date": page_info.get("updateDate"),
        "editor_num": page_info.get("edit", {}).get("editor_num", 0),
        "edit_num": page_info.get("edit", {}).get("edit_num", 0),
        "view_visitor_num": (page_info.get("view") or {}).get("totalVisitorCount", 0),
        "view_visit_num": (page_info.get("view") or {}).get("totalViewCount", 0),
        "ai_adapt_num": page_info.get("ai", {}).get("ai_adapt_num", 0),
        "ai_gene_num": page_info.get("ai", {}).get("ai_gene_num", 0),
        "finish_flag": "Y" if page_status == "已定稿" else "N",
        "feature_engineering": {},
        "script_date": CUR_DATE,
    }


def handle_feature_tree():
    """特性树数据采集主函数"""
    feature_tree_page_list = []
    total_feature_num = 0

    for field, field_dir_list in FEATURE_TREE_DIR_DICT.items():
        print(f"开始处理领域：【{field}】, 领域目录数：{len(field_dir_list)}")
        field_feature_num = 0

        for index, field_dir_url in enumerate(field_dir_list, 1):
            print(f"\n处理领域目录 [{index}/{len(field_dir_list)}]: {field_dir_url}")
            # ── 第1层：获取领域目录下的子页面 ──
            icenter_children_get_list = Icenter_children_get(field_dir_url)
            if len(icenter_children_get_list) == 0:
                print(f"目录 {field_dir_url} 无子节点，跳过")
                continue
            children_dict = icenter_children_get_list[2]
            print(f"获取到 {len(children_dict)} 个子页面")

            for child_title, child_url in children_dict.items():
                # 跳过规则
                if should_skip_title(child_title):
                    print(f"跳过标题：{child_title}")
                    continue

                # 解析标题
                parsed = parse_feature_title(child_title)
                if not parsed:
                    print(f"标题不匹配特性树格式，跳过：{child_title}")
                    continue

                print(f"处理特性 [{parsed['feature_num']}]: {child_title}")

                # 获取页面详情
                get_icenter_list = Get_icenter(child_url)
                if len(get_icenter_list) == 0:
                    print(f"页面获取失败，跳过：{child_url}")
                    continue
                page_context = get_icenter_list[1]
                page_info = get_icenter_list[3]
                page_detail = get_comp_tree_page_info(page_context)

                # 构建 page 记录
                page_item = build_page_item(child_title, child_url, field, parsed, page_detail, page_info)
                feature_tree_page_list.append(page_item)
                field_feature_num += 1
                total_feature_num += 1
                print(f"特性状态：{page_item['page_status']}, 类型：{parsed['page_type_name']}")

                # ── 第2层：如果F特性有FS子特性，继续获取 ──
                if not parsed["is_sub_feature"]:
                    sub_children_list = Icenter_children_get(child_url)
                    if len(sub_children_list) == 0:
                        continue
                    sub_children_dict = sub_children_list[2]
                    if len(sub_children_dict) == 0:
                        continue
                    print(f"F特性包含 {len(sub_children_dict)} 个子节点，检查FS子特性...")

                    for sub_title, sub_url in sub_children_dict.items():
                        if should_skip_title(sub_title):
                            continue
                        sub_parsed = parse_feature_title(sub_title)
                        if not sub_parsed:
                            continue
                        if not sub_parsed["is_sub_feature"]:
                            continue

                        print(f"  处理子特性 [{sub_parsed['feature_num']}]: {sub_title}")
                        sub_get_icenter_list = Get_icenter(sub_url)
                        if len(sub_get_icenter_list) == 0:
                            print(f"  子特性页面获取失败，跳过：{sub_url}")
                            continue
                        sub_page_context = sub_get_icenter_list[1]
                        sub_page_info = sub_get_icenter_list[3]
                        sub_page_detail = get_comp_tree_page_info(sub_page_context)

                        sub_page_item = build_page_item(sub_title, sub_url, field, sub_parsed, sub_page_detail, sub_page_info)
                        feature_tree_page_list.append(sub_page_item)
                        field_feature_num += 1
                        total_feature_num += 1
                        print(f"  子特性状态：{sub_page_item['page_status']}, 类型：{sub_parsed['page_type_name']}")

        print(f"领域【{field}】处理完成，特性数：{field_feature_num}")

    print(f"特性树数据采集完成，总特性数：{total_feature_num}，总页面数：{len(feature_tree_page_list)}")

    # ── 关联统计 scheme_num ──
    print(f"\n开始统计特性方案关联数...")
    # 构建特性方案的 key 索引
    scheme_key_count = {}
    for page in feature_tree_page_list:
        if page["page_type_name"] in ("特性方案", "子特性方案"):
            key = (page["feature_num"], page["type_flag"], page["feature_name"])
            scheme_key_count[key] = scheme_key_count.get(key, 0) + 1

    # 为特性分析页面填充 scheme_num
    for page in feature_tree_page_list:
        if page["page_type_name"] in ("特性分析", "子特性分析"):
            key = (page["feature_num"], page["type_flag"], page["feature_name"])
            page["scheme_num"] = scheme_key_count.get(key, 0)

    scheme_total = sum(1 for p in feature_tree_page_list if p["page_type_name"] in ("特性方案", "子特性方案"))
    print(f"特性方案关联统计完成，特性方案总数：{scheme_total}")

    # ── 初始化统计看板数据 ──
    print(f"\n开始统计看板数据，领域数：{len(FEATURE_TREE_DIR_DICT)}")
    feature_tree_board_dict = {
        field: {
            "date": CUR_DATE,
            "field_name": field,
            "analysis_sum_num": 0,
            "analysis_initial_num": 0,
            "analysis_reviewed_num": 0,
            "analysis_revision_num": 0,
            "analysis_finish_num": 0,
            "analysis_blank_num": 0,
            "analysis_sum_editor_num": 0,
            "analysis_sum_edit_num": 0,
            "analysis_sum_view_visitor_num": 0,
            "analysis_sum_view_visit_num": 0,
            "analysis_sum_ai_adapt_num": 0,
            "analysis_sum_ai_gene_num": 0,
            "scheme_sum_num": 0,
            "scheme_initial_num": 0,
            "scheme_reviewed_num": 0,
            "scheme_revision_num": 0,
            "scheme_finish_num": 0,
            "scheme_blank_num": 0,
            "scheme_sum_editor_num": 0,
            "scheme_sum_edit_num": 0,
            "scheme_sum_view_visitor_num": 0,
            "scheme_sum_view_visit_num": 0,
            "scheme_sum_ai_adapt_num": 0,
            "scheme_sum_ai_gene_num": 0,
        } for field in FEATURE_TREE_DIR_DICT.keys()
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
    print(f"开始遍历 {len(feature_tree_page_list)} 个页面进行统计...")
    stat_analysis_num = 0
    stat_scheme_num = 0

    for index, item in enumerate(feature_tree_page_list, 1):
        field_name = item.get("field_name")
        page_status = item.get("page_status")
        page_type_name = item.get("page_type_name")

        if not field_name or field_name not in feature_tree_board_dict:
            print(f"[{index}/{len(feature_tree_page_list)}] 跳过无效领域：{field_name}")
            continue

        # 判断是 analysis 还是 scheme
        if page_type_name in ("特性分析", "子特性分析"):
            prefix = "analysis"
            stat_analysis_num += 1
        elif page_type_name in ("特性方案", "子特性方案"):
            prefix = "scheme"
            stat_scheme_num += 1
        else:
            print(f"[{index}/{len(feature_tree_page_list)}] 未知页面类型：{page_type_name}，跳过")
            continue

        print(f"[{index}/{len(feature_tree_page_list)}] 统计 {prefix}: {item.get('page_title')} | 状态：{page_status} | 领域：{field_name}")

        # 1. 处理状态字段
        if page_status in status_to_field_map:
            status_key, _ = status_to_field_map[page_status]
            status_field = f"{prefix}_{status_key}_num"
            feature_tree_board_dict[field_name][status_field] += 1
            sum_field = f"{prefix}_sum_num"
            feature_tree_board_dict[field_name][sum_field] += 1

        # 2. 处理数值累加字段
        for item_key, board_suffix in numeric_fields_map.items():
            value = item.get(item_key, 0)
            if isinstance(value, (int, float)):
                board_key = f"{prefix}_{board_suffix}"
                feature_tree_board_dict[field_name][board_key] += value

    print(f"统计完成：特性分析 {stat_analysis_num} 个，特性方案 {stat_scheme_num} 个")

    # 输出各领域统计详情
    print(f"\n各领域统计详情:")
    for field_name, field_stats in feature_tree_board_dict.items():
        print(f"【{field_name}】(日期：{field_stats['date']})")
        print(f"特性分析总计：{field_stats['analysis_sum_num']} (初始:{field_stats['analysis_initial_num']}, 已初审:{field_stats['analysis_reviewed_num']}, 修订中:{field_stats['analysis_revision_num']}, 已定稿:{field_stats['analysis_finish_num']}, 空页面:{field_stats['analysis_blank_num']})")
        print(f"特性方案总计：{field_stats['scheme_sum_num']} (初始:{field_stats['scheme_initial_num']}, 已初审:{field_stats['scheme_reviewed_num']}, 修订中:{field_stats['scheme_revision_num']}, 已定稿:{field_stats['scheme_finish_num']}, 空页面:{field_stats['scheme_blank_num']})")

    # ── 汇总所有领域的数据为"波分中心" ──
    print(f"\n开始汇总'波分中心'数据...")
    pw_center_summary = {
        "date": CUR_DATE,
        "field_name": "波分中心",
        "analysis_sum_num": 0,
        "analysis_initial_num": 0,
        "analysis_reviewed_num": 0,
        "analysis_revision_num": 0,
        "analysis_finish_num": 0,
        "analysis_blank_num": 0,
        "analysis_sum_editor_num": 0,
        "analysis_sum_edit_num": 0,
        "analysis_sum_view_visitor_num": 0,
        "analysis_sum_view_visit_num": 0,
        "analysis_sum_ai_adapt_num": 0,
        "analysis_sum_ai_gene_num": 0,
        "scheme_sum_num": 0,
        "scheme_initial_num": 0,
        "scheme_reviewed_num": 0,
        "scheme_revision_num": 0,
        "scheme_finish_num": 0,
        "scheme_blank_num": 0,
        "scheme_sum_editor_num": 0,
        "scheme_sum_edit_num": 0,
        "scheme_sum_view_visitor_num": 0,
        "scheme_sum_view_visit_num": 0,
        "scheme_sum_ai_adapt_num": 0,
        "scheme_sum_ai_gene_num": 0,
    }

    for field_data in feature_tree_board_dict.values():
        for key in pw_center_summary:
            if key not in ["date", "field_name"]:
                pw_center_summary[key] += field_data.get(key, 0)

    print(f"'波分中心'汇总完成:")
    print(f"特性分析总计：{pw_center_summary['analysis_sum_num']} (初始:{pw_center_summary['analysis_initial_num']}, 已初审:{pw_center_summary['analysis_reviewed_num']}, 修订中:{pw_center_summary['analysis_revision_num']}, 已定稿:{pw_center_summary['analysis_finish_num']}, 空页面:{pw_center_summary['analysis_blank_num']})")
    print(f"特性方案总计：{pw_center_summary['scheme_sum_num']} (初始:{pw_center_summary['scheme_initial_num']}, 已初审:{pw_center_summary['scheme_reviewed_num']}, 修订中:{pw_center_summary['scheme_revision_num']}, 已定稿:{pw_center_summary['scheme_finish_num']}, 空页面:{pw_center_summary['scheme_blank_num']})")

    feature_tree_board_dict["波分中心"] = pw_center_summary
    feature_tree_board_list = list(feature_tree_board_dict.values())

    # ── 写入数据库 ──
    print(f"\n开始写入数据库...")
    print(f"写入特性树页面表：{len(feature_tree_page_list)} 条记录")
    print(f"写入特性树看板表：{len(feature_tree_board_list)} 条记录")
    feature_table.update_know_feature_tree_page_table_feature_tree_page_list(feature_tree_page_list)
    feature_table.add_know_feature_tree_board_table_feature_tree_board_list(feature_tree_board_list)
    print("✓ 特性树数据处理全部完成！")


if __name__ == "__main__":
    ICENTER_USER_ID = "10210415"
    en_httppassword = "tVAD4WMW4hy+nFNghziM9A=="

    init_icenter_env(en_httppassword)

    with app.app_context():
        CUR_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
        print("开始处理特性树数据")
        handle_feature_tree()
        print("结束处理特性树数据")
