"""
需求树 API 模块
提供需求树的查询接口，数据从 knowledge_requirement_tree 表加载
"""

import logging
from datetime import datetime
from flask import request, jsonify
from requirementsTree.data_model import (
    query_requirement_tree,
    query_requirement_tree_grouped,
    replace_requirement_tree_nodes,
    query_requirement_graph_layouts,
    save_requirement_graph_layout,
    query_requirement_graph_stats,
    query_requirement_tree_group_detail,
)
from requirementsTree.rdc_fetcher import fetch_requirement_data_online
from requirementsTree.icenter_fetcher import enrich_icenter_data
from requirementsTree.requirement_graph_service import (
    get_requirement_graph_service,
    get_pr_skill_mapping,
)

logger = logging.getLogger(__name__)

VALID_SCOPES = {"智能OTN", "M721", "NTON", "SRV"}


def _normalize_scope(raw_scope):
    """将前端传入的 scope 标准化，不合法则返回 None"""
    if raw_scope and raw_scope in VALID_SCOPES:
        return raw_scope
    return None


def _fetch_and_enrich(scope):
    """在线拉取需求数据：先从 RDC 拉取基础信息，再从 iCenter 补充方案和组件功能设计链接"""
    flat_nodes = fetch_requirement_data_online(scope)
    if flat_nodes:
        enrich_icenter_data(flat_nodes)
    return flat_nodes


# ============================================================================
# 需求导航树 API
# ============================================================================

def API_Knowledge_requirement_tree():
    """
    需求树接口：查询指定 scope 下的完整三层树结构（项目 → 里程碑 → 市场需求）
    """
    try:
        req = request.get_json(silent=True) or {}
        scope = _normalize_scope(req.get("scope") or req.get("tab"))
        if not scope:
            return jsonify({
                "code": 400,
                "message": f"无效的 scope，合法值: {sorted(VALID_SCOPES)}",
                "data": {"tree": []},
            }), 400

        # forceRefresh: 先在线拉取再返回树数据
        force_refresh = req.get("forceRefresh", False)
        if force_refresh:
            try:
                flat_nodes = _fetch_and_enrich(scope)
                if flat_nodes:
                    replace_requirement_tree_nodes(
                        scope, flat_nodes,
                        operator_person=req.get("operator") or "system",
                        sync_batch=req.get("syncBatch") or "",
                    )
            except Exception as e:
                logger.warning(f"forceRefresh 同步失败，返回缓存数据: {str(e)}")
        
        # 根据 groupBy 参数决定查询方式
        group_by = req.get("groupBy", "")
        if group_by:
            tree = query_requirement_tree_grouped(scope, group_by=group_by)
        else:
            tree = query_requirement_tree(scope)
        
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {"tree": tree},
        })
    except Exception as e:
        logger.error(f"API_Knowledge_requirement_tree error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取需求树失败: {str(e)}",
            "data": {"tree": []},
        }), 500


def API_Knowledge_requirement_tree_refresh():
    """
    手动刷新需求树缓存接口：按 scope 在线拉取数据并回写本地表。
    """
    try:
        req = request.get_json(silent=True) or {}
        scope = _normalize_scope(req.get("scope") or req.get("tab"))
        if not scope:
            return jsonify({
                "code": 400,
                "message": f"无效的 scope，合法值: {sorted(VALID_SCOPES)}",
                "data": {},
            }), 400

        # 在线拉取数据
        flat_nodes = _fetch_and_enrich(scope)
        if not flat_nodes:
            return jsonify({
                "code": 500,
                "message": "同步失败：未获取到数据",
                "data": {"scope": scope},
            }), 500

        # 写入数据库
        result = replace_requirement_tree_nodes(
            scope=scope,
            flat_nodes=flat_nodes,
            operator_person=req.get("operator") or "system",
            sync_batch=req.get("syncBatch") or "",
        )

        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "code": 200,
            "message": "同步成功",
            "data": {
                "scope": scope,
                "nodeCount": len(flat_nodes),
                "refreshedAt": refreshed_at,
                "result": result,
            },
        })
    except Exception as e:
        logger.error(f"API_Knowledge_requirement_tree_refresh error: {str(e)}")
        return jsonify({"code": 500, "message": f"刷新需求树失败: {str(e)}", "data": {}}), 500


# ============================================================================
# 需求图谱 API
# ============================================================================

def API_Knowledge_requirement_graph_get():
    """
    获取需求树知识图谱

    请求参数：
    - seedNodeId: 种子需求节点 ID（必填，knowledge_requirement_tree.node_id）
    - scope: 作用域（必填）
    - maxDepth: 最大展开深度，默认 2（可选）
    - forceRefresh: 是否强制刷新，默认 false（可选）
    """
    try:
        req = request.get_json(silent=True) or {}
        scope = _normalize_scope(req.get("scope") or req.get("tab"))
        seed_node_id = req.get("seedNodeId", "")
        max_depth = req.get("maxDepth", 2)
        force_refresh = req.get("forceRefresh", False)

        if not scope:
            return jsonify({
                "code": 400,
                "message": f"无效的 scope，合法值: {sorted(VALID_SCOPES)}",
                "data": None,
            }), 400

        if not seed_node_id:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：seedNodeId",
                "data": None,
            }), 400

        graph_service = get_requirement_graph_service()

        # 尝试从缓存获取（强制刷新时跳过缓存）
        if not force_refresh:
            cached_graph = graph_service.get_cached_graph(seed_node_id, max_depth)
            if cached_graph and len(cached_graph.nodes) > 0:
                logger.info(f"Cache hit for requirement graph {seed_node_id}")
                return jsonify({
                    "code": 200,
                    "message": "获取成功",
                    "data": cached_graph.to_dict()
                })

        # 生成新图谱
        logger.info(f"Generating new requirement graph for {seed_node_id}")
        graph = graph_service.generate_graph(seed_node_id, scope, max_depth)

        if graph.status == 'failed':
            return jsonify({
                "code": 500,
                "message": f"图谱生成失败：{graph.error_message}",
                "data": None,
            }), 500

        # 缓存到数据库
        operator_person = req.get("operatorPerson", "")
        graph_service.cache_graph_to_db(graph, operator_person)

        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": graph.to_dict()
        })

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_get error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取需求图谱失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_expand():
    """
    展开节点（懒加载）

    请求参数：
    - graphId: 图谱 ID（必填）
    - nodeId: 节点 ID（必填）
    """
    try:
        req = request.get_json(silent=True) or {}
        graph_id = req.get("graphId", "")
        node_id = req.get("nodeId", "")

        if not graph_id or not node_id:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：graphId, nodeId",
                "data": None,
            }), 400

        # TODO: 实现节点展开逻辑
        return jsonify({
            "code": 200,
            "message": "展开成功",
            "data": {
                "newNodes": [],
                "newEdges": []
            }
        })

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_expand error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"展开节点失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_detail():
    """
    获取节点详情

    请求参数：
    - nodeId: 节点 ID（必填）
    - nodeType: 节点类型（必填）
    - url: 节点 URL（可选）
    """
    try:
        req = request.get_json(silent=True) or {}
        node_id = req.get("nodeId", "")
        node_type = req.get("nodeType", "")

        if not node_id or not node_type:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：nodeId, nodeType",
                "data": None,
            }), 400

        # TODO: 根据节点类型返回不同的详情
        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": {
                "nodeId": node_id,
                "nodeType": node_type,
            }
        })

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_detail error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取节点详情失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_layout_save():
    """
    保存用户布局

    请求参数：
    - graphId: 图谱 ID（必填）
    - layoutName: 布局名称（必填）
    - layoutType: 布局类型（可选）
    - isDefault: 是否默认布局（可选）
    - isPublic: 是否公开（可选）
    - nodePositions: 节点位置数据（必填）
    - viewportConfig: 视口配置（可选）
    - filterConfig: 过滤配置（可选）
    - description: 布局描述（可选）
    """
    try:
        req = request.get_json(silent=True) or {}
        graph_id = req.get("graphId", "")
        layout_name = req.get("layoutName", "我的布局")
        node_positions = req.get("nodePositions", {})

        if not graph_id or not node_positions:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：graphId, nodePositions",
                "data": None,
            }), 400

        layout_data = {
            'graphId': graph_id,
            'layoutName': layout_name,
            'layoutType': req.get("layoutType", "custom"),
            'isDefault': req.get("isDefault", False),
            'isPublic': req.get("isPublic", False),
            'nodePositions': node_positions,
            'viewportConfig': req.get("viewportConfig", {}),
            'filterConfig': req.get("filterConfig", {}),
            'description': req.get("description", ""),
            'operatorPerson': req.get("operatorPerson", ""),
        }

        result = save_requirement_graph_layout(layout_data)

        if result['status'] == 'success':
            return jsonify({
                "code": 200,
                "message": "保存成功",
                "data": {"layoutId": result['layout_id']}
            })
        else:
            return jsonify({
                "code": 500,
                "message": f"保存布局失败：{result.get('message')}",
                "data": None,
            }), 500

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_layout_save error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"保存布局失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_layout_list():
    """
    获取用户布局列表

    请求参数：
    - graphId: 图谱 ID（必填）
    - operatorPerson: 操作人（可选）
    """
    try:
        req = request.get_json(silent=True) or {}
        graph_id = req.get("graphId", "")
        operator_person = req.get("operatorPerson", "")

        if not graph_id:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：graphId",
                "data": None,
            }), 400

        layouts = query_requirement_graph_layouts(graph_id, operator_person)

        result_layouts = []
        for layout in layouts:
            result_layouts.append({
                'layoutId': layout['id'],
                'layoutName': layout['layout_name'],
                'layoutType': layout['layout_type'],
                'isDefault': bool(layout['is_default']),
                'isPublic': bool(layout['is_public']),
                'operatorPerson': layout['operator_person'],
                'description': layout.get('description', ''),
                'createTime': layout['create_time'].isoformat() if layout.get('create_time') else None,
            })

        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": result_layouts
        })

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_layout_list error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取布局列表失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_refresh():
    """
    刷新图谱（重新生成）

    请求参数：
    - seedNodeId: 种子需求节点 ID（必填）
    - scope: 作用域（必填）
    - maxDepth: 最大深度（可选）
    """
    try:
        req = request.get_json(silent=True) or {}
        req["forceRefresh"] = True
        return API_Knowledge_requirement_graph_get()

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_refresh error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"刷新图谱失败：{str(e)}",
            "data": None,
        }), 500


def API_Knowledge_requirement_graph_stats():
    """
    获取图谱统计信息

    请求参数：
    - graphId: 图谱 ID（必填）
    """
    try:
        req = request.get_json(silent=True) or {}
        graph_id = req.get("graphId", "")

        if not graph_id:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：graphId",
                "data": None,
            }), 400

        stats = query_requirement_graph_stats(graph_id)

        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": stats
        })

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_stats error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取统计信息失败：{str(e)}",
            "data": None,
        }), 500


# ============================================================================
# 需求树分组详情 API
# ============================================================================

def API_Knowledge_requirement_tree_group_detail():
    """
    获取需求树分组详情：返回指定分组下的 MR 信息列表

    请求参数：
    - scope: 作用域（必填）
    - groupBy: 分组方式（必填），目前仅支持 "knowledge_completeness"
    - category: 分类名称（必填），如 "A类-实例化、方案、详设关联"
    - projectName: 项目名称（可选，限定范围）
    - milestoneName: 里程碑名称（可选，限定范围）
    """
    try:
        req = request.get_json(silent=True) or {}
        scope = _normalize_scope(req.get("scope") or req.get("tab"))
        if not scope:
            return jsonify({
                "code": 400,
                "message": f"无效的 scope，合法值: {sorted(VALID_SCOPES)}",
                "data": None,
            }), 400

        group_by = req.get("groupBy", "")
        category = req.get("category", "")

        if not group_by:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：groupBy",
                "data": None,
            }), 400

        if not category:
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：category",
                "data": None,
            }), 400

        project_name = req.get("projectName") or None
        milestone_name = req.get("milestoneName") or None

        items = query_requirement_tree_group_detail(
            scope=scope,
            group_by=group_by,
            category=category,
            milestone_name=milestone_name,
            project_name=project_name,
        )

        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": {
                "category": category,
                "count": len(items),
                "items": items,
            },
        })

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None,
        }), 400

    except Exception as e:
        logger.error(f"API_Knowledge_requirement_tree_group_detail error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取分组详情失败：{str(e)}",
            "data": None,
        }), 500
		

def API_Knowledge_requirement_graph_pr_skill_mapping():
    """
    获取图谱中所有 PR 和它们对应的 skill 绑定关系
    
    请求参数：
    - graphData: 图谱数据（必填，来自 API_Knowledge_requirement_graph_get 的返回 data）
    
    返回：
    - prSkillMapping: PR-Skill 映射列表
        - prNodeId: PR 节点 ID
        - prRdcId: PR RDC ID
        - prTitle: PR 标题
        - prType: PR 类型（微范式/配置化/未知）
        - skills: 对应的 skill 列表
            - skillName: 技能名称
            - skillUrl: 技能 URL
            - skillNodeId: 技能节点 ID
    """
    try:
        req = request.get_json(silent=True) or {}
        graph_data = req.get("graphData", {})
        
        if not graph_data or not isinstance(graph_data, dict):
            return jsonify({
                "code": 400,
                "message": "缺少必填参数：graphData",
                "data": None,
            }), 400
        
        pr_skill_mapping = get_pr_skill_mapping(graph_data)
        
        return jsonify({
            "code": 200,
            "message": "获取成功",
            "data": {
                "prSkillMapping": pr_skill_mapping,
                "totalCount": len(pr_skill_mapping),
                "withSkillCount": len([p for p in pr_skill_mapping if p['skills']]),
                "withoutSkillCount": len([p for p in pr_skill_mapping if not p['skills']]),
            }
        })
        
    except Exception as e:
        logger.error(f"API_Knowledge_requirement_graph_pr_skill_mapping error: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取 PR-Skill 映射失败：{str(e)}",
            "data": None,
        }), 500	
