import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from flask import jsonify, request


import requests
import re
from datetime import datetime
from sqlalchemy import or_

from get_icenter import (
    Get_icenter_page_detail,
    Icenter_children_get,
    Icenter_content_html_get,
    Icenter_title_get,
)

logger = logging.getLogger(__name__)


FEATURE_TREE_SOURCE_URLS = {
    "O": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/d4a2c95fd72311efa6e991b9604c470f/view"
    ],
    "E": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    ],
    "P": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/99da86d820b511f09fccbb17049e688c/view"
    ],
    "C": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b6c030a5ef2d11efab0767decfd9208f/view"
    ],
    "S": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9b8d3215ef8711ef9f097df5f06ee3d8/view"
    ],
    "SEC": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b8f0daf0519311f085cecbd38b00b54b/view"
    ],
}


FEATURE_TREE_SCOPE_CONFIG = {
    "O": {
        "title": "光层业务特性（O-含L0/智控/支撑）",
        "source_keys": ["L0", "WASON", "OSP"],
    },
    "E": {
        "title": "电层业务特性（E-含L1/支撑）",
        "source_keys": ["L1", "OSP"],
    },
    "P": {
        "title": "分组业务特性（P-含L2/支撑）",
        "source_keys": ["L2", "OSP"],
    },
    "C": {
        "title": "智控协同业务特性（C）",
        "source_keys": [],
    },
    "S": {
        "title": "支撑领域特性（S）",
        "source_keys": [],
    },
    "SEC": {
        "title": "产品安全特性（SEC）",
        "source_keys": [],
    },
}


FEATURE_SKIP_TITLES = {
    "汇总信息",
    "优质特性",
    "特性分析-所有页面统计汇总",
    "特性分析-已定稿页面统计汇总",
    "特性方案-已定稿页面统计汇总",
}


def normalize_feature_scope(raw_scope):
    raw = str(raw_scope or "O").strip()
    alias_map = {
        "光层业务特性（O-含L0/智控/支撑）": "O",
        "光层业务特性": "O",
        "电层业务特性（E-含L1/支撑）": "E",
        "电层业务特性": "E",
        "分组业务特性（P-含L2/支撑）": "P",
        "分组业务特性": "P",
        "智控协同业务特性（C）": "C",
        "智控协同业务特性": "C",
        "产品安全特性（SEC）": "SEC",
        "产品安全特性": "SEC",
        "智控": "C",
        "支撑": "O",
    }
    if raw in alias_map:
        return alias_map[raw]
    upper = raw.upper()
    return upper if upper in FEATURE_TREE_SCOPE_CONFIG else "O"


def parse_icenter_ids(page_url):
    if not page_url or not isinstance(page_url, str):
        return "", ""
    match = re.search(r"/space/([a-zA-Z0-9]{32})/wiki/page/([a-zA-Z0-9]{32})/view", page_url)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def safe_icenter_children(page_url):
    try:
        _, _, children_map = Icenter_children_get(page_url)
        if isinstance(children_map, dict):
            return children_map
    except Exception as err:
        logger.warning(f"Get feature iCenter children failed: {str(err)}")
    return {}


def is_skip_feature_title(title):
    if not title or not isinstance(title, str):
        return True
    cleaned = title.strip()
    return cleaned in FEATURE_SKIP_TITLES or "（待删除）" in cleaned or "(待删除)" in cleaned


def parse_feature_title_meta(title):
    if not title or not isinstance(title, str):
        return {}
    text = title.strip()
    patterns = [
        ("sub_analysis", re.compile(r"^FS(\d+(?:-\d+)+)-([A-Z]{1,3})-(.+)-子?特性分析$")),
        ("sub_scheme", re.compile(r"^FS(\d+(?:-\d+)+)-([A-Z]{1,3})-(.+)-子?特性方案$")),
        ("analysis", re.compile(r"^F(\d+(?:-\d+)?)-([A-Z]{1,3})-(.+)-特性分析$")),
        ("scheme", re.compile(r"^F(\d+(?:-\d+)?)-([A-Z]{1,3})-(.+)-特性方案$")),
        ("feature", re.compile(r"^FD(\d+(?:-\d+)?)-([A-Z]{1,3})-(.+)$")),
        ("feature", re.compile(r"^F(\d+(?:-\d+)?)-([A-Z]{1,3})-(.+)$")),
        ("sub_feature", re.compile(r"^FS(\d+(?:-\d+)+)-([A-Z]{1,3})-(.+)$")),
    ]
    for page_type, pattern in patterns:
        match = pattern.match(text)
        if not match:
            continue
        prefix = "FS" if page_type.startswith("sub_") else ("FD" if text.startswith("FD") else "F")
        return {
            "nodeType": page_type,
            "featureNum": f"{prefix}{match.group(1)}",
            "typeFlag": match.group(2),
            "featureName": match.group(3),
            "pageTypeName": {
                "analysis": "特性分析",
                "scheme": "特性方案",
                "sub_analysis": "子特性分析",
                "sub_scheme": "子特性方案",
                "feature": "特性目录",
                "sub_feature": "子特性",
            }.get(page_type, ""),
            "isSubFeature": 1 if page_type.startswith("sub_") else 0,
        }
    return {}


def infer_feature_node_type(title, level):
    meta = parse_feature_title_meta(title)
    if meta.get("nodeType"):
        return meta["nodeType"]
    if title and re.match(r"^D\d+-.+", title.strip()):
        return "category"
    if level <= 2:
        return "category"
    return "category"


def build_feature_tree_node(title, page_url, level, max_level, sort_no=0):
    if is_skip_feature_title(title):
        return None

    space_id, content_id = parse_icenter_ids(page_url)
    node_type = infer_feature_node_type(title, level)
    meta = parse_feature_title_meta(title)
    node = {
        "id": content_id or f"feature-{level}-{sort_no}-{title}",
        "spaceId": space_id,
        "title": title,
        "level": level,
        "nodeType": node_type,
        "url": page_url,
        "sortNo": sort_no,
        "hasChildren": False,
        "children": [],
        **meta,
    }

    if level >= max_level:
        return node

    children = []
    for idx, (child_title, child_url) in enumerate(safe_icenter_children(page_url).items()):
        child_node = build_feature_tree_node(child_title, child_url, level + 1, max_level, idx)
        if child_node:
            children.append(child_node)

    node["children"] = children
    node["hasChildren"] = bool(children)
    return node

# ---------------------------------

import os
import json
from get_icenter import IcenterAPI
from requirementsTree.uac_token import get_uac_token

import re

def extract_page_id_from_url(url: str):
    """从链接里提取pageId"""
    match = re.search(r'/page/([0-9a-f]+)/view', url)
    return match.group(1) if match else ""

def parse_title_link_key(key: str):
    """拆分 '[标题](url)' 格式字符串，返回(title, pageId)"""
    # 分割标题和链接
    title_part, url_part = key.split("](", 1)
    title = title_part.lstrip("[")
    url = url_part.rstrip(")")
    page_id = extract_page_id_from_url(url)
    return title, page_id

# def flatten_icenter_md_tree(root_dict, parent_id, space_id):
#     """
#     适配你当前的嵌套字典结构：{"[标题](url)": 子字典, ...}
#     :param root_dict: 当前层级字典 {link_key: child_dict}
#     :param parent_id: 父节点pageId，根节点传""
#     :param space_id: 空间ID
#     :return: 扁平bo列表
#     """
#     bo_list = []
#     # 遍历当前层级所有 [标题](url) 键
#     for link_key, child_dict in root_dict.items():
#         title, page_id = parse_title_link_key(link_key)
#         # 组装bo对象
#         bo_item = {
#             "id": page_id,
#             "spaceId": space_id,
#             "title": title,
#             "parentId": parent_id,
#             "parentPath": "",
#             "leaf": len(child_dict) == 0,
#             "sortNo": 0
#         }
#         bo_list.append(bo_item)
#         # 递归子节点
#         child_bo = flatten_icenter_md_tree(child_dict, page_id, space_id)
#         bo_list.extend(child_bo)
#     return bo_list

def flatten_icenter_md_tree(root_dict, parent_id, parent_path, space_id):
    bo_list = []
    for link_key, child_dict in root_dict.items():
        title, page_id = parse_title_link_key(link_key)
        
        # 拼接当前节点完整父路径
        if parent_id == "":
            curr_parent_path = ""
        else:
            curr_parent_path = f"{parent_path},{parent_id}"

        bo_item = {
            "node_id": page_id,
            "spaceId": space_id,
            "title": title,
            "parentId": parent_id,
            "parentPath": curr_parent_path,  # 动态生成链路
            "leaf": len(child_dict) == 0,
            "sortNo": 0
        }
        bo_list.append(bo_item)

        # 递归下层：把当前path、当前id传给子节点作为父参数
        child_bo = flatten_icenter_md_tree(child_dict, page_id, curr_parent_path, space_id)
        bo_list.extend(child_bo)
    return bo_list

def get_icenter_space_all_page(scope: str):
    """参数scope：O/E/P/C/S/SEC 字母标识"""
    try:
        user_num, token = get_uac_token()
        # print('-------------------------', user_num, token)
        if not token:
            logger.error("UAC token为空")
            return []

        api = IcenterAPI(user_num, token=token)
        print('-------------------------', api)

        # 匹配字母scope拿链接
        if scope not in FEATURE_TREE_SOURCE_URLS:
            logger.warning(f"scope={scope} 不存在配置")
            return []
        root_url = FEATURE_TREE_SOURCE_URLS[scope][0]
        # print('-------------------------', root_url)
        real_space_id, root_page_id = parse_icenter_root_url(root_url)
        # print('-------------------------', real_space_id, root_page_id)


        # 标准调用
        md_tree = api.get_children(real_space_id, root_page_id, 10)
        # print('-------------------------', md_tree)
        if not md_tree:
            logger.warning(f"real_space_id={real_space_id}, root={root_page_id} 返回空树")
            return []

        flat_bo = flatten_icenter_md_tree(md_tree, parent_id="", parent_path="", space_id=real_space_id)
        # flat_bo = _convert_markdown_tree_to_nodes(md_tree)
        
        # print('-------------------------', flat_bo)
        return flat_bo
    except Exception as e:
        logger.error(f"拉取失败 scope={scope}, err={str(e)}")
        return []
    
def _convert_markdown_tree_to_nodes(md_tree):
    """
    将 get_children 返回的 markdown 树转换为前端 tree 所需节点数组。
    输入示例：
      {
        "[D01-波道资源](https://i.zte.com.cn/...)": {
          "[FD010101-O-业务波CDWSS波长选择](...)": { ... },
          ...
        },
        ...
      }
    输出：
      [
        {
          "node_id": "https://i.zte.com.cn/...",   # 使用 URL 作为唯一ID
          "display_name": "D01-波道资源",
          "url": "https://i.zte.com.cn/...",
          "children": [ ... ]
        },
        ...
      ]
    """
    def parse_node(md_key, children_map):
        # 匹配 [标题](链接)
        m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', md_key)
        if not m:
            return {
                "node_id": md_key,
                "display_name": md_key,
                "url": "",
                "children": []
            }
        title, url = m.groups()
        children_list = [parse_node(child_key, child_children or {}) for child_key, child_children in (children_map or {}).items()]
        return {
            "node_id": url,
            "display_name": title,
            "url": url,
            "children": children_list
        }

    if not md_tree or not isinstance(md_tree, dict):
        return []
    return [parse_node(k, v) for k, v in md_tree.items()]

# def build_tree_from_icenter_bo(bo_list: list, root_page_id: str, max_level: int):
#     """
#     知识库扁平bo数组 → 前端标准树形结构
#     :param bo_list: 知识库返回bo数组
#     :param root_page_id: 当前scope根页面ID
#     :param max_level: 最大展示层级
#     :return: 根节点dict
#     """
#     node_map = {}
#     root_node = None
#     # ========== 新增常量定义，放在最前面 ==========
#     ICENTER_PAGE_URL_TPL = "https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view"
    
#     for item in bo_list:
#         item_id = item["node_id"]
#         space_id = item["spaceId"]
#         title = item["title"].strip()
#         # 计算层级：parentPath按-分割，长度-1为level
#         level = len(item["parentPath"].split(",")) - 1
#         # print('-------------------------', item_id, space_id, title, level)
#         # 拼接知识库url
#         node_url = ICENTER_PAGE_URL_TPL.format(spaceId=space_id, pageId=item_id)
#         # 自动区分nodeType，匹配前端图谱判断逻辑
#         if title.startswith("FD"):
#             node_type = "feature"
#         elif title.startswith("F"):
#             node_type = "sub_feature"
#         elif title.startswith("D"):
#             node_type = "category"
#         else:
#             node_type = "other"

#         tree_node = {
#             "id": item_id,
#             "spaceId": space_id,
#             "title": title,
#             "level": level,
#             "nodeType": node_type,
#             "url": node_url,
#             "sortNo": item.get("sortNo", 0),
#             "hasChildren": not item["leaf"],
#             "children": [],
#             "parentId": item["parentId"]
#         }
#         node_map[item_id] = tree_node
#         # if item_id == root_page_id:
#         if True:
#             root_node = tree_node
    
#     # print('-------------------------', item_id)

#     # 父子节点挂载
#     for node in node_map.values():
#         p_id = node["parentId"]
#         # 超过最大层级不再挂载子节点
#         if node["level"] >= max_level:
#             continue
#         if p_id in node_map:
#             node_map[p_id]["children"].append(node)
#             # 同层级按sortNo升序排序
#             node_map[p_id]["children"].sort(key=lambda x: x["sortNo"])
#     # print('-------------------------', node_map)
    
#     return node_map

def build_tree_from_icenter_bo(bo_list: list, root_page_id: str, max_level: int):
    """
    知识库扁平bo数组 → 前端标准树形结构
    :param bo_list: 知识库返回bo数组
    :param root_page_id: 当前scope根页面ID
    :param max_level: 最大展示层级
    :return: 根节点dict
    """
    node_map = {}
    root_node = None
    ICENTER_PAGE_URL_TPL = "https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view"
    
    for item in bo_list:
        # 兼容脏数据，防止读取报错
        if not item:
            continue
        # 修复1：字段修正，原来写死node_id是错的
        item_id = item["node_id"]
        space_id = item["spaceId"]
        title = item["title"].strip()
        # 沿用你原来的层级算法，不改动，避免层级错乱
        level = len(item["parentPath"].split(",")) - 1
        # 拼接知识库url
        node_url = ICENTER_PAGE_URL_TPL.format(spaceId=space_id, pageId=item_id)
        # 自动区分nodeType
        if title.startswith("FD"):
            node_type = "feature"
        elif title.startswith("F"):
            node_type = "sub_feature"
        elif title.startswith("D"):
            node_type = "category"
        else:
            node_type = "other"

        tree_node = {
            "node_id": item_id,
            "spaceId": space_id,
            "title": title,
            "level": level,
            "nodeType": node_type,
            "url": node_url,
            "sortNo": item.get("sortNo", 0),
            "hasChildren": not item["leaf"],
            "children": [],
            "parentId": item["parentId"]
        }
        node_map[item_id] = tree_node
        # 修复2：删掉if True，正确匹配根ID
        if item_id == root_page_id:
            root_node = tree_node

    to_delete = []
    # 父子节点挂载
    for node in node_map.values():
        p_id = node["parentId"]
        if node["level"] >= max_level:
            continue
        if p_id in node_map:
            node_map[p_id]["children"].append(node)
            node_map[p_id]["children"].sort(key=lambda x: x["sortNo"])
            # 先标记
            for k, v in node_map.items():
                if v is node:
                    to_delete.append(k)

    # 循环结束后再删
    for k in to_delete:
        del node_map[k]
                
    node_map_list = list(node_map.values())

    # 层级裁剪函数
    # def trim_limit(node, limit):
    #     if not node:
    #         return node_map_list
    #     if node["level"] >= limit:
    #         node["children"] = []
    #         node["hasChildren"] = False
    #         return
    #     for child in node["children"]:
    #         trim_limit(child, limit)

    # if root_node:
    #     trim_limit(root_node, max_level)
    #     return node_map_list
    # 无根节点返回空字典，不会返回null
    return node_map_list

# ---------------------------------

# def build_feature_page_node_online(scope, max_level):
#     config = FEATURE_TREE_SCOPE_CONFIG.get(scope, FEATURE_TREE_SCOPE_CONFIG["O"])
#     scope_children = []
#     seen = set()
#     for source_key in config["source_keys"]:
#         for source_url in FEATURE_TREE_SOURCE_URLS.get(source_key, []):
#             for child_title, child_url in safe_icenter_children(source_url).items():
#                 dedupe_key = f"{child_title}|{child_url}"
#                 if dedupe_key in seen:
#                     continue
#                 seen.add(dedupe_key)
#                 child_node = build_feature_tree_node(child_title, child_url, 3, max_level, len(scope_children))
#                 if child_node:
#                     scope_children.append(child_node)

#     scope_node = {
#         "id": f"feature-scope-{scope.lower()}",
#         "spaceId": "",
#         "title": config["title"],
#         "level": 2,
#         "nodeType": "category",
#         "url": "",
#         "sortNo": 0,
#         "hasChildren": bool(scope_children),
#         "children": scope_children,
#     }
#     tree_node = {
#         "id": f"feature-tree-{scope.lower()}",
#         "spaceId": "",
#         "title": "特性树",
#         "level": 1,
#         "nodeType": "category",
#         "url": "",
#         "sortNo": 0,
#         "hasChildren": True,
#         "children": [scope_node],
#     }
#     return {
#         "id": f"root-feature-{scope.lower()}",
#         "spaceId": "",
#         "title": "30 特性树",
#         "level": 0,
#         "nodeType": "root",
#         "url": "",
#         "sortNo": 0,
#         "hasChildren": True,
#         "children": [tree_node],
#     }

import re
# 解析知识库根页面url，提取spaceId、pageId
ICENTER_URL_PATTERN = re.compile(r'/space/([^/]+)/wiki/page/([^/]+)/view')

def parse_icenter_root_url(url: str):
    match = ICENTER_URL_PATTERN.search(url)
    if not match:
        return None, None
    space_id = match.group(1)
    root_page_id = match.group(2)
    return space_id, root_page_id

# 动态生成scope配置，复用FEATURE_TREE_SOURCE_URLS + FEATURE_TREE_SCOPE_CONFIG
def get_icenter_scope_config(scope: str):
    """根据scope自动获取space_id、root_page_id、title"""
    if scope not in FEATURE_TREE_SOURCE_URLS or len(FEATURE_TREE_SOURCE_URLS[scope]) == 0:
        return None
    root_url = FEATURE_TREE_SOURCE_URLS[scope][0]
    space_id, root_page_id = parse_icenter_root_url(root_url)
    if not space_id or not root_page_id:
        return None
    title = FEATURE_TREE_SCOPE_CONFIG[scope]["title"]
    return {
        "space_id": space_id,
        "root_page_id": root_page_id,
        "title": title,
        "root_url": root_url
    }

def build_feature_page_node_online(scope, max_level):
    # 1. 根据scope匹配对应知识库空间、根页面ID
    scope_cfg = get_icenter_scope_config(scope)
    # 兜底O域
    if not scope_cfg:
        scope_cfg = get_icenter_scope_config("O")
    space_id = scope_cfg["space_id"]
    root_page_id = scope_cfg["root_page_id"]
    root_title = scope_cfg["title"]
    root_url = scope_cfg["root_url"]

    # 2. 拉取当前业务域知识库所有页面
    bo_list = get_icenter_space_all_page(scope)
    logger.info(f"拉取知识库 bo_list 长度: {len(bo_list)}, space_id={space_id}, root_page_id={root_page_id}")
    if not bo_list:
        logger.warning(f"scope={scope} 知识库无页面数据，返回兜底空树")

    # 3. 扁平bo数组转完整嵌套树形
    icenter_root = build_tree_from_icenter_bo(bo_list, root_page_id, max_level)
    if not icenter_root:
        logger.warning(f"scope={scope} 未找到知识库页面 {root_page_id}")
        return None
    # print('------------------', icenter_root)

    # 4. 封装全局
    final_root = {
        "id": f"root-feature-{scope.lower()}",
        "spaceId": space_id,
        "title": root_title,
        "nodeType": "root",
        "url": root_url,
        "hasChildren": True if len(icenter_root)>0 else False,
        "children": icenter_root
    }
    return final_root


# def flatten_feature_tree_nodes(root_node):
#     flat_nodes = []
#     queue = [(root_node, None, 0)]
#     while queue:
#         current, parent_id, sort_no = queue.pop(0)
#         node_id = current.get("id")
#         if not node_id:
#             continue
#         flat_nodes.append(
#             {
#                 "id": node_id,
#                 "parentId": parent_id,
#                 "level": int(current.get("level", 0)),
#                 "nodeType": current.get("nodeType", "category"),
#                 "title": current.get("title", ""),
#                 "url": current.get("url", ""),
#                 "spaceId": current.get("spaceId", ""),
#                 "sortNo": int(current.get("sortNo", sort_no)),
#                 "hasChildren": bool(current.get("hasChildren", False)),
#                 **{
#                     key: current.get(key)
#                     for key in ["featureNum", "typeFlag", "featureName", "pageTypeName", "isSubFeature"]
#                     if current.get(key) is not None
#                 },
#             }
#         )
#         for idx, child in enumerate(current.get("children", [])):
#             queue.append((child, node_id, idx))
#     return flat_nodes

def flatten_feature_tree_nodes(root_node):
    """递归扁平化树形节点，用于写入缓存表"""
    flat_list = []
    if not root_node:
        return flat_list

    def dfs(node):
        flat_list.append(node)
        for child in node.get("children", []):
            dfs(child)
    dfs(root_node)
    return flat_list


def build_feature_tree_from_cached_nodes(cached_nodes, default_root_title="30 特性树"):
    if not cached_nodes:
        return None
    node_map = {}
    roots = []
    for row in cached_nodes:
        payload = row.get("node_payload") or {}
        node = {
            "id": row.get("node_id"),
            "parentId": row.get("parent_id"),
            "spaceId": row.get("space_id", ""),
            "title": row.get("title", ""),
            "level": int(row.get("level", 0)),
            "nodeType": row.get("node_type", "category"),
            "url": row.get("url", ""),
            "sortNo": row.get("sort_no", 0),
            "hasChildren": row.get("has_children") == "Y",
            "children": [],
        }
        for key in ["featureNum", "typeFlag", "featureName", "pageTypeName", "isSubFeature"]:
            if key in payload:
                node[key] = payload.get(key)
        node_map[node["id"]] = node

    for node in node_map.values():
        parent_id = node.get("parentId")
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(node)
        else:
            roots.append(node)

    root_candidates = [item for item in roots if item.get("nodeType") == "root" or item.get("level") == 0]
    if root_candidates:
        return root_candidates[0]
    return {
        "id": "root-feature-cache",
        "spaceId": "",
        "title": default_root_title,
        "level": 0,
        "nodeType": "root",
        "url": "",
        "hasChildren": bool(roots),
        "children": roots,
    }


def has_feature_data_children(root_node):
    if not root_node:
        return False
    queue = list(root_node.get("children", []))
    while queue:
        current = queue.pop(0)
        if current.get("level", 0) >= 3:
            return True
        queue.extend(current.get("children", []))
    return False

from flask import Flask

# 关键：创建app实例，不写就会报app未定义
app = Flask(__name__)

@app.route("/featureTreeNew/api_feature_tree")
def API_Knowledge_feature_tree():
    try:
        from featureTreeNew.feature_data_model import (
            query_knowledge_feature_tree_nodes,
            replace_knowledge_feature_tree_nodes,
        )

        req = request.get_json(silent=True) or {}
        # print('-----------', req)
        max_level = int(req.get("maxLevel", 6))
        max_level = 3 if max_level < 3 else min(max_level, 8)
        tree_scope = normalize_feature_scope(req.get("tab") or req.get("domain") or "O")
        # root_title = 'texingshu'

        # cache_available = True
        # try:
        #     cached_nodes = query_knowledge_feature_tree_nodes(scope=tree_scope, max_level=max_level)
        # except Exception as cache_err:
        #     logger.warning(f"Query feature tree cache failed, fallback to online tree: {str(cache_err)}")
        #     cached_nodes = []
        #     cache_available = False

        # root_node = build_feature_tree_from_cached_nodes(cached_nodes, root_title)
        # if (not root_node) or (not has_feature_data_children(root_node)):
        #     root_node = build_feature_page_node_online(tree_scope, max_level)
        #     if cache_available and has_feature_data_children(root_node):
        #         try:
        #             replace_knowledge_feature_tree_nodes(
        #                 scope=tree_scope,
        #                 node_list=flatten_feature_tree_nodes(root_node),
        #                 operator_person=req.get("operator") or "system",
        #                 sync_batch=req.get("syncBatch") or "",
        #             )
        #         except Exception as replace_err:
        #             logger.warning(f"Replace feature tree cache failed: {str(replace_err)}")
        #     elif cached_nodes:
        #         root_node = build_feature_tree_from_cached_nodes(cached_nodes, root_title)
        # 直接调用在线生成树，完全跳过缓存查表/写缓存
        page_node = build_feature_page_node_online(tree_scope, max_level)
        # print('root_node: ', page_node)

        return jsonify({"code": 200, "message": "success", "data": {"root": page_node}})
    except Exception as err:
        logger.error(f"API_Knowledge_feature_tree error: {str(err)}")
        return jsonify({"code": 500, "message": f"获取特性树失败: {str(err)}", "data": {"root": None}}), 500


def API_Knowledge_feature_tree_refresh():
    try:
        from featureTreeNew.feature_data_model import replace_knowledge_feature_tree_nodes

        req = request.get_json(silent=True) or {}
        max_level = int(req.get("maxLevel", 6))
        max_level = 3 if max_level < 3 else min(max_level, 8)
        tree_scope = normalize_feature_scope(req.get("tab") or req.get("domain") or "O")
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        root_node = build_feature_page_node_online(tree_scope, max_level)
        node_list = flatten_feature_tree_nodes(root_node)
        try:
            result = replace_knowledge_feature_tree_nodes(
                scope=tree_scope,
                node_list=node_list,
                operator_person=req.get("operator") or "system",
                sync_batch=req.get("syncBatch") or "",
            )
        except Exception as replace_err:
            result = {"status": "error", "message": f"cache unavailable: {str(replace_err)}"}

        return jsonify(
            {
                "code": 200,
                "message": "refresh success",
                "data": {
                    "scope": tree_scope,
                    "nodeCount": len(node_list),
                    "refreshedAt": refreshed_at,
                    "result": result,
                },
            }
        )
    except Exception as err:
        logger.error(f"API_Knowledge_feature_tree_refresh error: {str(err)}")
        return jsonify({"code": 500, "message": f"刷新特性树失败: {str(err)}", "data": {}}), 500


def extract_feature_related_items_from_html(soup, keyword):
    related_items = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        target_idx = -1
        for idx, cell in enumerate(rows[0].find_all(["th", "td"])):
            if keyword in cell.get_text(strip=True):
                target_idx = idx
                break
        if target_idx < 0:
            continue
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if target_idx >= len(cells):
                continue
            cell = cells[target_idx]
            link = cell.find("a")
            name = cell.get_text(strip=True).replace("\ufeff", "")
            url = ""
            if link:
                url = (link.get("href") or "").strip()
                if url.startswith("/"):
                    url = f"https://i.zte.com.cn{url}"
            if name:
                related_items.append({"name": name, "url": url})

    deduped = []
    seen = set()
    for item in related_items:
        if item["name"] in seen:
            continue
        seen.add(item["name"])
        deduped.append(item)
    return deduped


def API_Knowledge_feature_detail():
    try:
        req = request.get_json(silent=True) or {}
        page_url = req.get("url", "")
        title = req.get("title", "")
        node_type = req.get("nodeType", "")
        space_id = req.get("spaceId", "")
        content_id = req.get("contentId", "")

        if not space_id or not content_id:
            parsed_space_id, parsed_content_id = parse_icenter_ids(page_url)
            space_id = space_id or parsed_space_id
            content_id = content_id or parsed_content_id

        display_title = title
        if not display_title and page_url:
            try:
                display_title = Icenter_title_get(page_url) or ""
            except Exception:
                display_title = ""

        guardian = ""
        status = ""
        operator = ""
        operate_time = ""
        related_components = []
        related_features = []

        if page_url:
            try:
                page_detail = Get_icenter_page_detail(page_url)
                if isinstance(page_detail, dict):
                    operator = page_detail.get("relator") or page_detail.get("updateBy") or ""
                    operate_time = page_detail.get("lastUpdateTime") or page_detail.get("updateDate") or ""
            except Exception as detail_err:
                logger.warning(f"Get feature page detail failed: {str(detail_err)}")

            try:
                page_html = Icenter_content_html_get(page_url)
                if page_html:
                    soup = BeautifulSoup(page_html, "html.parser")
                    for tr in soup.find_all("tr"):
                        th = tr.find("th")
                        td = th.find_next_sibling("td") if th else None
                        if not td:
                            continue
                        key = th.get_text(strip=True).replace("\ufeff", "")
                        if key in {"页面守护人", "守护人"}:
                            guardian = td.get_text(strip=True).replace("\ufeff", "")
                        elif key in {"页面状态", "页面设计状态"}:
                            select_tag = td.find("select")
                            if select_tag:
                                selected_option = select_tag.find("option", selected=True)
                                status = (
                                    selected_option.get_text(strip=True).replace("\ufeff", "")
                                    if selected_option
                                    else td.get_text(strip=True).replace("\ufeff", "")
                                )
                            else:
                                status = td.get_text(strip=True).replace("\ufeff", "")
                    related_components = extract_feature_related_items_from_html(soup, "组件")
                    related_features = extract_feature_related_items_from_html(soup, "特性")
            except Exception as html_err:
                logger.warning(f"Get feature page html failed: {str(html_err)}")

        meta = parse_feature_title_meta(display_title)
        detail_page_url = page_url
        if not detail_page_url and space_id and content_id:
            detail_page_url = f"https://i.zte.com.cn/index/ispace/#/space/{space_id}/wiki/page/{content_id}/view"

        return jsonify(
            {
                "code": 200,
                "message": "success",
                "data": {
                    "basicInfo": {
                        "name": display_title,
                        "spaceId": space_id,
                        "contentId": content_id,
                        "nodeType": node_type,
                        **meta,
                    },
                    "guardian": guardian,
                    "status": status,
                    "changeLog": "",
                    "operator": operator,
                    "operateTime": operate_time,
                    "relations": "",
                    "relatedComponents": related_components,
                    "relatedFeatures": related_features,
                    "qualityScore": "",
                    "contentCompleteness": "",
                    "contentStandardization": "",
                    "url": detail_page_url,
                },
            }
        )
    except Exception as err:
        logger.error(f"API_Knowledge_feature_detail error: {str(err)}")
        return jsonify({"code": 500, "message": f"获取特性详情失败: {str(err)}", "data": {}}), 500

# """
# 特性树 API 模块
# 从 iCenter 抓取多级子树，转换为前端 tree 组件所需结构
# """

# import os
# import json
# import re
# from flask import request, jsonify
# from get_icenter import IcenterAPI
# from requirementsTree.uac_token import get_uac_token

# logger = __import__('logging').getLogger(__name__)

# # 与前端 Tabs 对应的作用域列表
# VALID_SCOPES = {"光层", "电层", "分组", "智控", "支撑", "安全"}

# def _normalize_scope(raw_scope):
#     """标准化 scope，无效返回 None"""
#     if raw_scope and raw_scope in VALID_SCOPES:
#         return raw_scope
#     return None

# def _convert_markdown_tree_to_nodes(md_tree):
#     """
#     将 get_children 返回的 markdown 树转换为前端 tree 所需节点数组。
#     输入示例：
#       {
#         "[D01-波道资源](https://i.zte.com.cn/...)": {
#           "[FD010101-O-业务波CDWSS波长选择](...)": { ... },
#           ...
#         },
#         ...
#       }
#     输出：
#       [
#         {
#           "node_id": "https://i.zte.com.cn/...",   # 使用 URL 作为唯一ID
#           "display_name": "D01-波道资源",
#           "url": "https://i.zte.com.cn/...",
#           "children": [ ... ]
#         },
#         ...
#       ]
#     """
#     def parse_node(md_key, children_map):
#         # 匹配 [标题](链接)
#         m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', md_key)
#         if not m:
#             return {
#                 "node_id": md_key,
#                 "display_name": md_key,
#                 "url": "",
#                 "children": []
#             }
#         title, url = m.groups()
#         children_list = [parse_node(child_key, child_children or {}) for child_key, child_children in (children_map or {}).items()]
#         return {
#             "node_id": url,
#             "display_name": title,
#             "url": url,
#             "children": children_list
#         }

#     if not md_tree or not isinstance(md_tree, dict):
#         return []
#     return [parse_node(k, v) for k, v in md_tree.items()]

# def _get_depth(md):
#     if not md or not isinstance(md, dict):
#         return 0
#     max_child = 0
#     for v in md.values():
#         d = _get_depth(v)
#         if d > max_child:
#             max_child = d
#     return 1 + max_child

# def _print_sample(md, level=0, max_samples=3):
#     if not md or not isinstance(md, dict):
#         return
#     for i, (k, v) in enumerate(md.items()):
#         logger.info(f"{'  '*level}L{level}: {k}")
#         if level < max_samples:
#             _print_sample(v, level+1, max_samples)

# def API_Knowledge_feature_tree():
#     """
#     特性树接口：返回 iCenter 指定根页面的多级子树结构
#     请求参数（JSON 体）：
#       - scope: 作用域（可选，目前仅用于校验，如 光层/电层/分组/智控/支撑/安全）
#       - depth: 递归深度，默认 6
#     返回：
#       { "code": 200, "message": "success", "data": { "tree": [...] } }
#     """
#     try:
#         req = request.get_json(silent=True) or {}
#         scope = _normalize_scope(req.get("scope") or req.get("tab"))
#         # scope 可用于未来按分类过滤，当前返回全量
#         depth = int(req.get("depth", 8))

#         # 获取 UAC 认证信息
#         user_num, token = get_uac_token()
#         if not token:
#             raise RuntimeError("获取 UAC token 失败")

#         api = IcenterAPI(user_num, token=token)

        # # 从环境变量获取根空间和页面 ID，提供默认值（对应执行 fetch_children.py 时的参数）
        # SPACE_ID = os.getenv('FEATURE_TREE_SPACE_ID', 'fbff14a6a14c4985874248df3ac610c1')
        # ROOT_PAGE_ID = os.getenv('FEATURE_TREE_ROOT_PAGE_ID', '730cdf86173e11f0b1e437f2f87f8184')

#         # 调用 iCenter 获取子树（markdown 树结构）
#         md_tree = api.get_children(SPACE_ID, ROOT_PAGE_ID, depth=depth)
#         if not md_tree:
#             logger.warning(f"获取特性子树失败: space={SPACE_ID}, root={ROOT_PAGE_ID}")
#             return jsonify({"code": 500, "message": "获取特性子树失败", "data": {"tree": []}}), 500

#         # 转换为前端 tree 结构
#         tree = _convert_markdown_tree_to_nodes(md_tree)
#         # _print_sample(md_tree)

#         # logger.info(f"depth: {_get_depth(md_tree)}")

#         return jsonify({
#             "code": 200,
#             "message": "success",
#             "data": {"tree": tree}
#         })

#     except Exception as e:
#         logger.exception("API_Feature_tree error")
#         return jsonify({"code": 500, "message": f"获取特性树失败: {str(e)}", "data": {"tree": []}}), 500
