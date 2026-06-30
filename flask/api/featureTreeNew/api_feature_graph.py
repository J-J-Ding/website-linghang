import logging
from datetime import datetime

from flask import jsonify, request

from featureTreeNew.api_feature_tree import (
    infer_feature_node_type,
    normalize_feature_scope,
    parse_feature_title_meta,
    parse_icenter_ids,
    safe_icenter_children,
)

logger = logging.getLogger(__name__)


def feature_relation_label(node_type):
    if node_type in {"feature", "sub_feature"}:
        return "包含特性"
    if node_type in {"analysis", "sub_analysis"}:
        return "包含分析"
    if node_type in {"scheme", "sub_scheme"}:
        return "包含方案"
    if node_type == "related_feature":
        return "关联特性"
    return "包含目录"


def feature_row_to_graph_node(row, seed_node_id):
    payload = row.get("node_payload") or {}
    node_id = row.get("node_id")
    return {
        "id": node_id,
        "name": row.get("title", ""),
        "type": row.get("node_type", "category"),
        "expanded": False,
        "desc": payload.get("desc") or row.get("title", ""),
        "url": row.get("url", ""),
        "spaceId": row.get("space_id", ""),
        "contentId": node_id,
        "level": 1,
        "parentFeatureId": seed_node_id,
        "pageStatus": payload.get("pageStatus", ""),
        "featureNum": payload.get("featureNum", ""),
        "featureName": payload.get("featureName", ""),
        "typeFlag": payload.get("typeFlag", ""),
        "pageTypeName": payload.get("pageTypeName", ""),
        "isSubFeature": payload.get("isSubFeature", 0),
    }


def build_feature_graph_from_tree(seed_feature_id, scope, max_depth=2):
    from featureTreeNew.feature_data_model import query_knowledge_feature_tree_nodes

    tree_scope = normalize_feature_scope(scope)
    rows = query_knowledge_feature_tree_nodes(tree_scope, max_level=8)
    seed_row = None
    for row in rows:
        if row.get("node_id") == seed_feature_id or row.get("title") == seed_feature_id:
            seed_row = row
            break

    if not seed_row:
        return None, f"未找到特性节点：{seed_feature_id}"

    seed_node_id = seed_row.get("node_id")
    child_rows = [row for row in rows if row.get("parent_id") == seed_node_id]
    nodes = [feature_row_to_graph_node(row, seed_node_id) for row in child_rows]
    edges = [
        {
            "id": f"{seed_node_id}_to_{row.get('node_id')}",
            "source": seed_node_id,
            "target": row.get("node_id"),
            "relationType": "contains",
            "relationLabel": feature_relation_label(row.get("node_type", "")),
            "rawData": {},
        }
        for row in child_rows
    ]

    now = datetime.now()
    return {
        "seedFeatureId": seed_node_id,
        "seedFeatureName": seed_row.get("title", ""),
        "scope": tree_scope,
        "maxDepth": max_depth,
        "status": "completed",
        "totalNodes": len(nodes),
        "totalEdges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "generatedAt": now.isoformat(),
        "expiresAt": None,
        "errorMessage": "",
    }, ""


def build_feature_graph_from_online_seed(seed_feature_id, seed_title, seed_url, scope, max_depth=2):
    if not seed_url:
        return None, "缺少 seedUrl，且缓存中未找到该节点"

    tree_scope = normalize_feature_scope(scope)
    _, parsed_seed_id = parse_icenter_ids(seed_url)
    real_seed_id = seed_feature_id or parsed_seed_id or seed_title
    nodes = []
    edges = []

    for idx, (child_title, child_url) in enumerate(safe_icenter_children(seed_url).items()):
        space_id, content_id = parse_icenter_ids(child_url)
        node_id = content_id or f"{real_seed_id}-{idx}"
        node_type = infer_feature_node_type(child_title, 1)
        meta = parse_feature_title_meta(child_title)
        nodes.append(
            {
                "id": node_id,
                "name": child_title,
                "type": node_type,
                "expanded": False,
                "desc": child_title,
                "url": child_url,
                "spaceId": space_id,
                "contentId": node_id,
                "level": 1,
                "parentFeatureId": real_seed_id,
                "pageStatus": "",
                "featureNum": meta.get("featureNum", ""),
                "featureName": meta.get("featureName", ""),
                "typeFlag": meta.get("typeFlag", ""),
                "pageTypeName": meta.get("pageTypeName", ""),
                "isSubFeature": meta.get("isSubFeature", 0),
            }
        )
        edges.append(
            {
                "id": f"{real_seed_id}_to_{node_id}",
                "source": real_seed_id,
                "target": node_id,
                "relationType": "contains",
                "relationLabel": feature_relation_label(node_type),
                "rawData": {},
            }
        )

    now = datetime.now()
    return {
        "seedFeatureId": real_seed_id,
        "seedFeatureName": seed_title or real_seed_id,
        "scope": tree_scope,
        "maxDepth": max_depth,
        "status": "completed",
        "totalNodes": len(nodes),
        "totalEdges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "generatedAt": now.isoformat(),
        "expiresAt": None,
        "errorMessage": "",
    }, ""


def API_Knowledge_feature_graph_get():
    try:
        from featureTreeNew.feature_data_model import (
            query_cached_feature_graph,
            save_feature_graph_edges,
            save_feature_graph_nodes,
            save_feature_graph_to_db,
        )

        req = request.get_json(silent=True) or {}
        seed_feature_id = req.get("seedFeatureId") or ""
        seed_title = req.get("seedTitle") or ""
        seed_url = req.get("seedUrl") or ""
        scope = req.get("scope", "")
        max_depth = int(req.get("maxDepth", 2))
        force_refresh = bool(req.get("forceRefresh", False))
        operator_person = req.get("operatorPerson", "")

        if not seed_feature_id or not scope:
            return jsonify(
                {
                    "code": 400,
                    "status": "error",
                    "message": "缺少必填参数：seedFeatureId, scope",
                    "data": None,
                }
            ), 400

        if not force_refresh:
            try:
                cached_graph = query_cached_feature_graph(seed_feature_id, max_depth)
                if cached_graph and cached_graph.graph_data:
                    return jsonify(
                        {
                            "code": 200,
                            "status": "success",
                            "message": "获取成功",
                            "data": cached_graph.graph_data,
                        }
                    )
            except Exception as cache_err:
                logger.warning(f"Query cached feature graph failed: {str(cache_err)}")

        try:
            graph_data, error_message = build_feature_graph_from_tree(seed_feature_id, scope, max_depth)
        except Exception as tree_err:
            logger.warning(f"Build feature graph from cache failed: {str(tree_err)}")
            graph_data, error_message = None, str(tree_err)

        if not graph_data:
            graph_data, error_message = build_feature_graph_from_online_seed(
                seed_feature_id,
                seed_title,
                seed_url,
                scope,
                max_depth,
            )

        if not graph_data:
            return jsonify(
                {
                    "code": 500,
                    "status": "error",
                    "message": f"图谱生成失败：{error_message}",
                    "data": None,
                }
            ), 500

        try:
            save_result = save_feature_graph_to_db(graph_data, operator_person)
            graph_id = save_result.get("graph_id")
            if save_result.get("status") == "success" and graph_id:
                save_feature_graph_nodes(graph_id, graph_data["nodes"])
                save_feature_graph_edges(graph_id, graph_data["edges"])
        except Exception as cache_err:
            logger.warning(f"Cache feature graph failed: {str(cache_err)}")

        return jsonify(
            {
                "code": 200,
                "status": "success",
                "message": "获取成功",
                "data": graph_data,
            }
        )
    except Exception as err:
        logger.error(f"API_Knowledge_feature_graph_get error: {str(err)}")
        return jsonify(
            {
                "code": 500,
                "status": "error",
                "message": f"获取特性图谱失败：{str(err)}",
                "data": None,
            }
        ), 500


def API_Knowledge_feature_graph_refresh():
    return API_Knowledge_feature_graph_get()