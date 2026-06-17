"""
组件知识图谱 API 接口
提供图谱生成、查询、展开、布局保存等功能
作者：AI Assistant
创建时间：2026-05-19
"""

import os
import json
from flask import request, jsonify
from datetime import datetime
import logging

from componentTree.graph_service import (
    get_graph_service, GraphService, 
    NodeType, RelationType, 
    NODE_TYPE_LABELS, RELATION_TYPE_LABELS
)
from componentTree.data_model import (
    KNOWLEDGE_COMPONENT_TREE,
    query_graph_layouts,
    save_graph_layout,
    query_graph_stats
)

logger = logging.getLogger(__name__)


def API_Knowledge_component_graph_get():
    """
    获取组件知识图谱
    
    请求参数：
    - seedComponentId: 种子组件 ID（必填）
    - scope: 范围 L0/L1/L2/WASON/OSP（必填）
    - maxDepth: 最大展开深度，默认 2（可选）
    - forceRefresh: 是否强制刷新，默认 false（可选）
    
    返回格式：
    {
        "code": 200,
        "status": "success",
        "message": "获取成功",
        "data": {
            "seedComponentId": "xxx",
            "seedComponentName": "xxx",
            "scope": "L0",
            "maxDepth": 2,
            "status": "completed",
            "totalNodes": 50,
            "totalEdges": 45,
            "nodes": [
                {
                    "id": "center1",
                    "name": "SC001-SC_MP_IF 网管接口子组件设计",
                    "type": "component",
                    "expanded": true,
                    "level": 0,
                    "url": "https://...",
                    "spaceId": "xxx",
                    "contentId": "xxx",
                    "pageStatus": "已定稿"
                },
                {
                    "id": "center1_mod1",
                    "name": "M001-SC_MIM_CHECK 消息校验",
                    "type": "module",
                    "level": 1,
                    "url": "https://...",
                    "pageStatus": "修订中"
                },
                {
                    "id": "center1_chap1",
                    "name": "5.3.1 流程设计",
                    "type": "section",
                    "desc": "5.3.1 流程设计",
                    "level": 1,
                    "pageStatus": ""
                },
                {
                    "id": "center1_dep1",
                    "name": "SC001-TAP 终端适配执行",
                    "type": "dependent_component",
                    "level": 1,
                    "url": "https://...",
                    "pageStatus": "初始"
                },
                {
                    "id": "center1_feat1",
                    "name": "F010604-管控与 WASON",
                    "type": "affected_feature",
                    "level": 1,
                    "url": "https://...",
                    "pageStatus": "已初审"
                }
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "source": "center1",
                    "target": "center1_mod1",
                    "relationType": "belongs_to",
                    "relationLabel": "属于"
                },
                {
                    "id": "edge_2",
                    "source": "center1",
                    "target": "center1_chap1",
                    "relationType": "contains",
                    "relationLabel": "包含"
                },
                {
                    "id": "edge_3",
                    "source": "center1",
                    "target": "center1_dep1",
                    "relationType": "depends_on",
                    "relationLabel": "依赖"
                },
                {
                    "id": "edge_4",
                    "source": "center1",
                    "target": "center1_feat1",
                    "relationType": "affects",
                    "relationLabel": "影响"
                }
            ],
            "generatedAt": "2026-05-19T10:00:00",
            "expiresAt": "2026-05-19T11:00:00"
        }
    }
    
    节点 pageStatus 字段说明：
    - component（组件）、module（模块）、dependent_component（依赖组件）：从页面表格中提取"页面状态"字段
    - affected_feature（波及特性）：从页面表格中提取"页面设计状态"字段
    - section（章节）：不获取页面状态，返回空字符串
    - 状态值包括：初始、已初审、修订中、已定稿
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_get] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - seedComponentId: {req.get('seedComponentId', '')}")
        print(f"  - scope: {req.get('scope', '')}")
        print(f"  - maxDepth: {req.get('maxDepth', 2)}")
        print(f"  - forceRefresh: {req.get('forceRefresh', False)}")
        print(f"  - operatorPerson: {req.get('operatorPerson', '')}")
        print("=" * 80)
        # ====================================
        
        seed_component_id = req.get("seedComponentId", "")
        scope = req.get("scope", "")
        max_depth = req.get("maxDepth", 2)
        force_refresh = req.get("forceRefresh", False)
        
        if not seed_component_id or not scope:
            print(f"[ERROR] 缺少必填参数 - seedComponentId: '{seed_component_id}', scope: '{scope}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：seedComponentId, scope",
                "data": None
            }), 400
        
        # ========== 调试信息：查询数据库 ==========
        print("=" * 80)
        print("[DEBUG] 开始查询数据库...")
        print(f"  - 查询条件:")
        print(f"    * scope: '{scope}'")
        print(f"    * effective_flag: 'Y'")
        print(f"    * seed_component_id: '{seed_component_id}'")
        print(f"  - 查询方式：node_id='{seed_component_id}' OR title='{seed_component_id}'")
        print("=" * 80)
        # =========================================
        
        graph_service = get_graph_service()
        
        # 尝试从缓存获取（强制刷新时跳过缓存）
        if not force_refresh:
            cached_graph = graph_service.get_cached_graph(seed_component_id, max_depth)
            if cached_graph and len(cached_graph.nodes) > 0:
                logger.info(f"Cache hit for graph {seed_component_id} with {len(cached_graph.nodes)} nodes")
                return jsonify({
                    "code": 200,
                    "status": "success",
                    "message": "获取成功",
                    "data": cached_graph.to_dict()
                })
            elif cached_graph and len(cached_graph.nodes) == 0:
                logger.warning(f"Cache found but empty for graph {seed_component_id}, will regenerate")
        
        # 生成新图谱
        logger.info(f"Generating new graph for {seed_component_id}")
        graph = graph_service.generate_graph(seed_component_id, scope, max_depth)
        
        if graph.status == 'failed':
            # ========== 调试信息：组件不存在 ==========
            print("=" * 80)
            print("[ERROR] 组件不存在，尝试诊断原因...")
            print(f"  - 查询的组件：'{seed_component_id}'")
            print(f"  - 查询的 scope: '{scope}'")
            print(f"  - 可能的原因:")
            print(f"    1. 组件 ID 或名称错误")
            print(f"    2. scope 不匹配（组件在其他范围）")
            print(f"    3. effective_flag 不是 'Y'")
            print(f"    4. 数据库中没有这个组件")
            print(f"  - 建议：运行 check_component.py 脚本检查数据库")
            print("=" * 80)
            # =========================================
            
            return jsonify({
                "code": 500,
                "status": "error",
                "message": f"图谱生成失败：{graph.error_message}",
                "data": None
            }), 500
        
        # 缓存到数据库
        operator_person = req.get("operatorPerson", "")
        graph_service.cache_graph_to_db(graph, operator_person)
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "获取成功",
            "data": graph.to_dict()
        })
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_get error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"获取图谱失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_expand():
    """
    展开节点（懒加载）
    
    请求参数：
    - graphId: 图谱 ID（必填）
    - nodeId: 节点 ID（必填）
    
    返回格式：
    {
        "code": 200,
        "status": "success",
        "message": "展开成功",
        "data": {
            "newNodes": [...],
            "newEdges": [...]
        }
    }
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_expand] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - graphId: {req.get('graphId', '')}")
        print(f"  - nodeId: {req.get('nodeId', '')}")
        print("=" * 80)
        # ====================================
        
        graph_id = req.get("graphId", "")
        node_id = req.get("nodeId", "")
        
        if not graph_id or not node_id:
            print(f"[ERROR] 缺少必填参数 - graphId: '{graph_id}', nodeId: '{node_id}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：graphId, nodeId",
                "data": None
            }), 400
        
        # TODO: 实现节点展开逻辑
        # 目前返回空数据
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "展开成功",
            "data": {
                "newNodes": [],
                "newEdges": []
            }
        })
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_expand error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"展开节点失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_detail():
    """
    获取节点详情（复用现有的 API_Knowledge_component_detail 逻辑）
    
    请求参数：
    - nodeId: 节点 ID（必填）
    - nodeType: 节点类型（必填）
    - url: 节点 URL（可选）
    
    返回格式：参考 API_Knowledge_component_detail
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_detail] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - nodeId: {req.get('nodeId', '')}")
        print(f"  - nodeType: {req.get('nodeType', '')}")
        print(f"  - url: {req.get('url', '')}")
        print("=" * 80)
        # ====================================
        
        node_id = req.get("nodeId", "")
        node_type = req.get("nodeType", "")
        url = req.get("url", "")
        
        if not node_id or not node_type:
            print(f"[ERROR] 缺少必填参数 - nodeId: '{node_id}', nodeType: '{node_type}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：nodeId, nodeType",
                "data": None
            }), 400
        
        # TODO: 根据节点类型返回不同的详情
        # 目前直接调用现有的 API_Knowledge_component_detail
        
        from componentTree.api_component_tree import API_Knowledge_component_detail
        return API_Knowledge_component_detail()
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_detail error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"获取节点详情失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_layout_save():
    """
    保存用户布局
    
    请求参数：
    - graphId: 图谱 ID（必填）
    - layoutName: 布局名称（必填）
    - layoutType: 布局类型 custom/dagre/force/circular（可选）
    - isDefault: 是否默认布局（可选）
    - isPublic: 是否公开（可选）
    - nodePositions: 节点位置数据 {node_id: {x, y}}（必填）
    - viewportConfig: 视口配置 {zoom, centerX, centerY}（可选）
    - filterConfig: 过滤配置 {node_types: [], relation_types: []}（可选）
    - description: 布局描述（可选）
    
    返回格式：
    {
        "code": 200,
        "status": "success",
        "message": "保存成功",
        "data": {
            "layoutId": 123
        }
    }
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_layout_save] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - graphId: {req.get('graphId', '')}")
        print(f"  - layoutName: {req.get('layoutName', '我的布局')}")
        print(f"  - layoutType: {req.get('layoutType', 'custom')}")
        print(f"  - isDefault: {req.get('isDefault', False)}")
        print(f"  - isPublic: {req.get('isPublic', False)}")
        print(f"  - nodePositions: {len(req.get('nodePositions', {}))} 个节点位置")
        print(f"  - operatorPerson: {req.get('operatorPerson', '')}")
        print("=" * 80)
        # ====================================
        
        graph_id = req.get("graphId", "")
        layout_name = req.get("layoutName", "我的布局")
        layout_type = req.get("layoutType", "custom")
        is_default = req.get("isDefault", False)
        is_public = req.get("isPublic", False)
        node_positions = req.get("nodePositions", {})
        viewport_config = req.get("viewportConfig", {})
        filter_config = req.get("filterConfig", {})
        description = req.get("description", "")
        operator_person = req.get("operatorPerson", "")
        
        if not graph_id or not node_positions:
            print(f"[ERROR] 缺少必填参数 - graphId: '{graph_id}', nodePositions: {len(node_positions)} 个")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：graphId, nodePositions",
                "data": None
            }), 400
        
        # 调用 data_model 中的函数
        layout_data = {
            'graphId': graph_id,
            'layoutName': layout_name,
            'layoutType': layout_type,
            'isDefault': is_default,
            'isPublic': is_public,
            'nodePositions': node_positions,
            'viewportConfig': viewport_config,
            'filterConfig': filter_config,
            'description': description,
            'operatorPerson': operator_person,
        }
        
        result = save_graph_layout(layout_data)
        
        if result['status'] == 'success':
            return jsonify({
                "code": 200,
                "status": "success",
                "message": "保存成功",
                "data": {
                    "layoutId": result['layout_id']
                }
            })
        else:
            return jsonify({
                "code": 500,
                "status": "error",
                "message": f"保存布局失败：{result.get('message')}",
                "data": None
            }), 500
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_layout_save error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"保存布局失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_layout_list():
    """
    获取用户布局列表
    
    请求参数：
    - graphId: 图谱 ID（必填）
    - operatorPerson: 操作人（可选，默认查询当前用户）
    
    返回格式：
    {
        "code": 200,
        "status": "success",
        "message": "获取成功",
        "data": [
            {
                "layoutId": 123,
                "layoutName": "我的布局",
                "layoutType": "custom",
                "isDefault": true,
                "isPublic": false,
                "operatorPerson": "xxx",
                "description": "xxx",
                "createTime": "2026-05-19T10:00:00"
            }
        ]
    }
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_layout_list] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - graphId: {req.get('graphId', '')}")
        print(f"  - operatorPerson: {req.get('operatorPerson', '')}")
        print("=" * 80)
        # ====================================
        
        graph_id = req.get("graphId", "")
        operator_person = req.get("operatorPerson", "")
        
        if not graph_id:
            print(f"[ERROR] 缺少必填参数 - graphId: '{graph_id}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：graphId",
                "data": None
            }), 400
        
        # 调用 data_model 中的函数
        layouts = query_graph_layouts(graph_id, operator_person)
        
        # 转换字段名和格式
        result_layouts = []
        for layout in layouts:
            result_layout = {
                'layoutId': layout['id'],
                'layoutName': layout['layout_name'],
                'layoutType': layout['layout_type'],
                'isDefault': bool(layout['is_default']),
                'isPublic': bool(layout['is_public']),
                'operatorPerson': layout['operator_person'],
                'description': layout.get('description', ''),
                'createTime': layout['create_time'].isoformat() if layout.get('create_time') else None,
            }
            result_layouts.append(result_layout)
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "获取成功",
            "data": result_layouts
        })
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_layout_list error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"获取布局列表失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_refresh():
    """
    刷新图谱（重新生成）
    
    请求参数：
    - seedComponentId: 种子组件 ID（必填）
    - scope: 范围（必填）
    - maxDepth: 最大深度（可选）
    
    返回格式：同 API_Knowledge_component_graph_get
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_refresh] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - seedComponentId: {req.get('seedComponentId', '')}")
        print(f"  - scope: {req.get('scope', '')}")
        print(f"  - maxDepth: {req.get('maxDepth', 2)}")
        print("=" * 80)
        # ====================================
        
        seed_component_id = req.get("seedComponentId", "")
        scope = req.get("scope", "")
        max_depth = req.get("maxDepth", 2)
        
        if not seed_component_id or not scope:
            print(f"[ERROR] 缺少必填参数 - seedComponentId: '{seed_component_id}', scope: '{scope}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：seedComponentId, scope",
                "data": None
            }), 400
        
        # 强制刷新
        req["forceRefresh"] = True
        
        # 调用生成接口
        return API_Knowledge_component_graph_get()
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_refresh error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"刷新图谱失败：{str(e)}",
            "data": None
        }), 500


def API_Knowledge_component_graph_stats():
    """
    获取图谱统计信息
    
    请求参数：
    - graphId: 图谱 ID（必填）
    
    返回格式：
    {
        "code": 200,
        "status": "success",
        "message": "获取成功",
        "data": {
            "totalNodes": 50,
            "totalEdges": 45,
            "nodeTypeStats": {
                "component": 10,
                "module": 5,
                "section": 3,
                "dependent_component": 20,
                "affected_feature": 12,
                "skill": 0
            },
            "relationTypeStats": {
                "belongs_to": 5,
                "contains": 3,
                "depends_on": 20,
                "affects": 12,
                "requires": 0
            },
            "levelStats": {
                "0": 1,
                "1": 30,
                "2": 19
            }
        }
    }
    """
    try:
        req = request.get_json(silent=True) or {}
        
        # ========== 打印接收到的参数 ==========
        print("=" * 80)
        print("[API_Knowledge_component_graph_stats] 接收到请求参数:")
        print(f"  - 完整请求体：{json.dumps(req, ensure_ascii=False, indent=2)}")
        print(f"  - graphId: {req.get('graphId', '')}")
        print("=" * 80)
        # ====================================
        
        graph_id = req.get("graphId", "")
        
        if not graph_id:
            print(f"[ERROR] 缺少必填参数 - graphId: '{graph_id}'")
            return jsonify({
                "code": 400,
                "status": "error",
                "message": "缺少必填参数：graphId",
                "data": None
            }), 400
        
        # 调用 data_model 中的函数
        stats = query_graph_stats(graph_id)
        
        return jsonify({
            "code": 200,
            "status": "success",
            "message": "获取成功",
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"API_Knowledge_component_graph_stats error: {str(e)}")
        return jsonify({
            "code": 500,
            "status": "error",
            "message": f"获取统计信息失败：{str(e)}",
            "data": None
        }), 500
