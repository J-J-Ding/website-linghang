import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from flask import jsonify, request

from get_icenter import (
    Get_icenter_page_detail,
    Icenter_children_get,
    Icenter_content_html_get,
    Icenter_title_get,
)

logger = logging.getLogger(__name__)


FEATURE_TREE_SOURCE_URLS = {
    "L0": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/d4a2c95fd72311efa6e991b9604c470f/view"
    ],
    "L1": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/730cdf86173e11f0b1e437f2f87f8184/view"
    ],
    "L2": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/99da86d820b511f09fccbb17049e688c/view"
    ],
    "WASON": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b6c030a5ef2d11efab0767decfd9208f/view"
    ],
    "OSP": [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9b8d3215ef8711ef9f097df5f06ee3d8/view"
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
        "source_keys": ["WASON"],
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


def build_feature_root_node_online(scope, max_level):
    config = FEATURE_TREE_SCOPE_CONFIG.get(scope, FEATURE_TREE_SCOPE_CONFIG["O"])
    scope_children = []
    seen = set()
    for source_key in config["source_keys"]:
        for source_url in FEATURE_TREE_SOURCE_URLS.get(source_key, []):
            for child_title, child_url in safe_icenter_children(source_url).items():
                dedupe_key = f"{child_title}|{child_url}"
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                child_node = build_feature_tree_node(child_title, child_url, 3, max_level, len(scope_children))
                if child_node:
                    scope_children.append(child_node)

    scope_node = {
        "id": f"feature-scope-{scope.lower()}",
        "spaceId": "",
        "title": config["title"],
        "level": 2,
        "nodeType": "category",
        "url": "",
        "sortNo": 0,
        "hasChildren": bool(scope_children),
        "children": scope_children,
    }
    tree_node = {
        "id": f"feature-tree-{scope.lower()}",
        "spaceId": "",
        "title": "特性树",
        "level": 1,
        "nodeType": "category",
        "url": "",
        "sortNo": 0,
        "hasChildren": True,
        "children": [scope_node],
    }
    return {
        "id": f"root-feature-{scope.lower()}",
        "spaceId": "",
        "title": "30 特性树",
        "level": 0,
        "nodeType": "root",
        "url": "",
        "sortNo": 0,
        "hasChildren": True,
        "children": [tree_node],
    }


def flatten_feature_tree_nodes(root_node):
    flat_nodes = []
    queue = [(root_node, None, 0)]
    while queue:
        current, parent_id, sort_no = queue.pop(0)
        node_id = current.get("id")
        if not node_id:
            continue
        flat_nodes.append(
            {
                "id": node_id,
                "parentId": parent_id,
                "level": int(current.get("level", 0)),
                "nodeType": current.get("nodeType", "category"),
                "title": current.get("title", ""),
                "url": current.get("url", ""),
                "spaceId": current.get("spaceId", ""),
                "sortNo": int(current.get("sortNo", sort_no)),
                "hasChildren": bool(current.get("hasChildren", False)),
                **{
                    key: current.get(key)
                    for key in ["featureNum", "typeFlag", "featureName", "pageTypeName", "isSubFeature"]
                    if current.get(key) is not None
                },
            }
        )
        for idx, child in enumerate(current.get("children", [])):
            queue.append((child, node_id, idx))
    return flat_nodes


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


def API_Knowledge_feature_tree():
    try:
        from featureTreeNew.feature_data_model import (
            query_knowledge_feature_tree_nodes,
            replace_knowledge_feature_tree_nodes,
        )

        req = request.get_json(silent=True) or {}
        max_level = int(req.get("maxLevel", 6))
        max_level = 3 if max_level < 3 else min(max_level, 8)
        tree_scope = normalize_feature_scope(req.get("tab") or req.get("domain") or "O")
        root_title = "30 特性树"

        cache_available = True
        try:
            cached_nodes = query_knowledge_feature_tree_nodes(scope=tree_scope, max_level=max_level)
        except Exception as cache_err:
            logger.warning(f"Query feature tree cache failed, fallback to online tree: {str(cache_err)}")
            cached_nodes = []
            cache_available = False

        root_node = build_feature_tree_from_cached_nodes(cached_nodes, root_title)
        if (not root_node) or (not has_feature_data_children(root_node)):
            root_node = build_feature_root_node_online(tree_scope, max_level)
            if cache_available and has_feature_data_children(root_node):
                try:
                    replace_knowledge_feature_tree_nodes(
                        scope=tree_scope,
                        node_list=flatten_feature_tree_nodes(root_node),
                        operator_person=req.get("operator") or "system",
                        sync_batch=req.get("syncBatch") or "",
                    )
                except Exception as replace_err:
                    logger.warning(f"Replace feature tree cache failed: {str(replace_err)}")
            elif cached_nodes:
                root_node = build_feature_tree_from_cached_nodes(cached_nodes, root_title)

        return jsonify({"code": 200, "message": "success", "data": {"root": root_node}})
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

        root_node = build_feature_root_node_online(tree_scope, max_level)
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
