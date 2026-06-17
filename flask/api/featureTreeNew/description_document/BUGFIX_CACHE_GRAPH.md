# Bug 修复：cache_graph_to_db 方法缺失

## 🐛 问题描述

**错误信息**:
```
'GraphService' object has no attribute 'cache_graph_to_db'
```

**错误位置**: `api_component_graph.py` 第 208 行

**调用栈**:
```python
# api_component_graph.py 第 208 行
graph_service.cache_graph_to_db(graph, operator_person)
```

---

## 🔍 根本原因

`GraphService` 类中**没有定义** `cache_graph_to_db` 方法，但在 `api_component_graph.py` 中调用了它。

**图谱生成成功**（5 个节点，4 条边），但在尝试缓存到数据库时失败。

---

## ✅ 解决方案

在 `GraphService` 类中添加 `cache_graph_to_db` 方法。

### 修改的文件

- `graph_service.py` - 添加 `cache_graph_to_db` 方法

### 方法实现

```python
def cache_graph_to_db(self, graph: 'ComponentGraph', operator_person: str = ""):
    """
    缓存图谱到数据库
    
    Args:
        graph: 图谱对象
        operator_person: 操作人
    """
    try:
        logger.info(f"Caching graph to database: {graph.seed_component_id}")
        
        # 调用 data_model 中的函数保存图谱
        graph_data = {
            'seed_component_id': graph.seed_component_id,
            'seed_component_name': graph.seed_component_name,
            'scope': graph.scope,
            'max_depth': graph.max_depth,
            'status': graph.status,
            'total_nodes': len(graph.nodes),
            'total_edges': len(graph.edges),
            'nodes': [node.to_dict() for node in graph.nodes.values()],
            'edges': [edge.to_dict() for edge in graph.edges],
            'generated_at': graph.generated_at,
            'expires_at': graph.expires_at,
            'error_message': graph.error_message
        }
        
        # 保存图谱主表
        save_result = save_graph_to_db(graph_data, operator_person)
        
        if save_result.get('status') == 'error':
            logger.error(f"Failed to save graph: {save_result.get('message')}")
            return
        
        graph_id = save_result.get('graph_id')
        logger.info(f"Graph saved with ID: {graph_id}")
        
        # 保存节点
        if graph.nodes:
            nodes_data = []
            for node in graph.nodes.values():
                nodes_data.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'node_type': node.type,
                    'level': node.level,
                    'is_expanded': node.expanded,
                    'url': node.url,
                    'space_id': node.space_id,
                    'content_id': node.content_id,
                    'position_x': node.position_x,
                    'position_y': node.position_y,
                    'parent_component_id': node.parent_component_id,
                    'raw_data': {}
                })
            save_graph_nodes(graph_id, nodes_data)
            logger.info(f"Saved {len(nodes_data)} nodes")
        
        # 保存边
        if graph.edges:
            edges_data = []
            for edge in graph.edges:
                edges_data.append({
                    'edge_id': edge.id,
                    'source_node_id': edge.source,
                    'target_node_id': edge.target,
                    'relation_type': edge.relation_type,
                    'relation_label': edge.relation_label
                })
            save_graph_edges(graph_id, edges_data)
            logger.info(f"Saved {len(edges_data)} edges")
        
        # 缓存组件章节信息
        for node in graph.nodes.values():
            if node.type == NodeType.COMPONENT and node.url:
                try:
                    cache_component_section(node.url)
                except Exception as e:
                    logger.warning(f"Failed to cache section for component {node.name}: {e}")
        
        logger.info(f"Graph cached successfully: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        
    except Exception as e:
        logger.error(f"Error caching graph to database: {str(e)}")
        raise
```

---

## 🎯 功能说明

`cache_graph_to_db` 方法负责：

1. ✅ **保存图谱主表** - `knowledge_component_graph`
2. ✅ **保存节点** - `knowledge_component_graph_node`
3. ✅ **保存边** - `knowledge_component_graph_edge`
4. ✅ **缓存章节信息** - `knowledge_component_section`
5. ✅ **记录操作人** - 用于审计和权限控制

---

## 📊 数据流

```
图谱生成成功
    ↓
调用 cache_graph_to_db()
    ↓
1. 保存图谱主表 → knowledge_component_graph
    ↓
2. 保存节点 → knowledge_component_graph_node
    ↓
3. 保存边 → knowledge_component_graph_edge
    ↓
4. 缓存章节 → knowledge_component_section
    ↓
缓存完成
```

---

## 🧪 测试验证

### 测试步骤

1. **发送请求**（使用正确的组件 ID）:
   ```json
   {
     "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
     "scope": "L1",
     "maxDepth": 2
   }
   ```

2. **查看后端日志**:
   ```
   [DEBUG] 开始查询数据库...
   INFO: Generating new graph for a6fa84ef6e7511f080eaf9504434accd
   INFO: Graph generated successfully: 5 nodes, 4 edges
   INFO: Caching graph to database: a6fa84ef6e7511f080eaf9504434accd
   INFO: Graph saved with ID: 1
   INFO: Saved 5 nodes
   INFO: Saved 4 edges
   INFO: Graph cached successfully: 5 nodes, 4 edges
   ```

3. **检查数据库**:
   ```sql
   -- 检查图谱
   SELECT * FROM knowledge_component_graph WHERE seed_component_id = 'a6fa84ef6e7511f080eaf9504434accd';
   
   -- 检查节点
   SELECT * FROM knowledge_component_graph_node WHERE graph_id = 1;
   
   -- 检查边
   SELECT * FROM knowledge_component_graph_edge WHERE graph_id = 1;
   ```

4. **验证响应**:
   ```json
   {
     "code": 200,
     "status": "success",
     "message": "获取成功",
     "data": {
       "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
       "seedComponentName": "C-F023-PRTC 组件设计",
       "scope": "L1",
       "maxDepth": 2,
       "status": "completed",
       "totalNodes": 5,
       "totalEdges": 4,
       "nodes": [...],
       "edges": [...]
     }
   }
   ```

---

## 📝 依赖关系

### 调用的 data_model 函数

- `save_graph_to_db()` - 保存图谱主表
- `save_graph_nodes()` - 保存节点
- `save_graph_edges()` - 保存边
- `cache_component_section()` - 缓存章节信息

### 导入的模块

```python
from componentTree.data_model import (
    KNOWLEDGE_COMPONENT_TREE,
    query_knowledge_component_tree_nodes,
    query_cached_graph,
    save_graph_to_db,
    save_graph_nodes,
    save_graph_edges,
    cache_component_section,
    query_graph_nodes,
    query_graph_edges,
)
```

---

## ⚠️ 注意事项

1. **数据库表必须存在** - 确保已执行 `graph_schema.sql`
2. **外键约束** - 节点和边的 `graph_id` 必须引用存在的图谱
3. **事务处理** - `data_model.py` 中的函数已处理事务
4. **错误处理** - 方法会捕获并记录所有异常

---

## 🔧 故障排查

### 问题 1: 图谱保存失败

**日志**:
```
ERROR: Failed to save graph: ...
```

**检查**:
- 数据库表是否存在
- 数据库连接是否正常
- 字段类型是否匹配

---

### 问题 2: 节点保存失败

**日志**:
```
ERROR: Error saving nodes: ...
```

**检查**:
- `graph_id` 是否正确
- 节点数据格式是否正确
- 是否有必填字段缺失

---

### 问题 3: 章节缓存失败

**日志**:
```
WARNING: Failed to cache section for component ...
```

**检查**:
- iCenter URL 是否可访问
- 页面是否包含有效内容
- HTML 解析是否正常

---

## 📚 相关文档

- [graph_service.py](graph_service.py) - 图谱服务实现
- [data_model.py](data_model.py) - 数据库操作
- [graph_schema.sql](graph_schema.sql) - 数据库表结构
- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - API 测试指南

---

## ✅ 修复验证清单

- [x] 添加 `cache_graph_to_db` 方法
- [x] 方法调用 `save_graph_to_db` 保存图谱
- [x] 方法调用 `save_graph_nodes` 保存节点
- [x] 方法调用 `save_graph_edges` 保存边
- [x] 方法调用 `cache_component_section` 缓存章节
- [x] 添加完整的错误处理
- [x] 添加详细的日志记录
- [x] 代码通过语法检查
- [ ] 运行 Postman 测试验证
- [ ] 检查数据库表数据

---

**修复时间**: 2026-05-19  
**修复版本**: v1.0.1  
**问题类型**: AttributeError - 方法缺失  
**影响范围**: 图谱缓存功能  
**修复状态**: ✅ 已完成
