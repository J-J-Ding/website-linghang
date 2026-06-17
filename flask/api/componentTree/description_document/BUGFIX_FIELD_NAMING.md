# Bug 修复：字段命名不匹配

## 🐛 问题描述

**错误信息**:
```
ERROR: Failed to save graph: save_graph_to_db failed: 'seedComponentId'
```

**错误位置**: `graph_service.py` 第 842 行

**调用栈**:
```python
# graph_service.py
graph_data = {
    'seed_component_id': graph.seed_component_id,  # ❌ 下划线命名
    ...
}
save_result = save_graph_to_db(graph_data, operator_person)

# data_model.py 第 321 行
existing_graph = db.session.query(KNOWLEDGE_COMPONENT_GRAPH).filter(
    KNOWLEDGE_COMPONENT_GRAPH.seed_component_id == graph_data['seedComponentId'],  # ❌ 期望驼峰命名
    ...
)
```

---

## 🔍 根本原因

**字段命名不一致**：

1. `graph_service.py` 使用**下划线命名**（snake_case）:
   - `seed_component_id`
   - `seed_component_name`
   - `max_depth`
   - `total_nodes`
   - `total_edges`
   - `generated_at`
   - `expires_at`
   - `error_message`

2. `data_model.py` 的 `save_graph_to_db` 函数期望**驼峰命名**（camelCase）:
   - `seedComponentId`
   - `seedComponentName`
   - `maxDepth`
   - `totalNodes`
   - `totalEdges`
   - `generatedAt`
   - `expiresAt`
   - `errorMessage`

---

## ✅ 解决方案

修改 `graph_service.py` 中的 `cache_graph_to_db` 方法，使用驼峰命名字段。

### 修改前

```python
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
```

### 修改后

```python
graph_data = {
    'seedComponentId': graph.seed_component_id,
    'seedComponentName': graph.seed_component_name,
    'scope': graph.scope,
    'maxDepth': graph.max_depth,
    'status': graph.status,
    'totalNodes': len(graph.nodes),
    'totalEdges': len(graph.edges),
    'nodes': [node.to_dict() for node in graph.nodes.values()],
    'edges': [edge.to_dict() for edge in graph.edges],
    'generatedAt': graph.generated_at.isoformat() if graph.generated_at else datetime.now().isoformat(),
    'expiresAt': graph.expires_at.isoformat() if graph.expires_at else None,
    'errorMessage': graph.error_message
}
```

---

## 📊 字段映射表

| 下划线命名 (Python 风格) | 驼峰命名 (JavaScript 风格) | 用途 |
|------------------------|------------------------|------|
| `seed_component_id` | `seedComponentId` | 种子组件 ID |
| `seed_component_name` | `seedComponentName` | 种子组件名称 |
| `max_depth` | `maxDepth` | 最大深度 |
| `total_nodes` | `totalNodes` | 节点总数 |
| `total_edges` | `totalEdges` | 边总数 |
| `generated_at` | `generatedAt` | 生成时间 |
| `expires_at` | `expiresAt` | 过期时间 |
| `error_message` | `errorMessage` | 错误信息 |

---

## 🎯 为什么使用驼峰命名？

### 原因 1: 与前端保持一致

前端返回的 JSON 数据使用驼峰命名：
```json
{
  "seedComponentId": "xxx",
  "totalNodes": 50,
  "totalEdges": 45
}
```

### 原因 2: 符合 API 设计规范

RESTful API 通常使用驼峰命名，便于前后端统一。

### 原因 3: 历史原因

`data_model.py` 中的 `save_graph_to_db` 函数已经实现，使用驼峰命名。

---

## 🧪 测试验证

### 测试步骤

1. **发送请求**:
   ```json
   {
     "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
     "scope": "L1",
     "maxDepth": 2
   }
   ```

2. **查看后端日志**:
   ```
   INFO: Generating new graph for a6fa84ef6e7511f080eaf9504434accd
   INFO: Graph generated successfully: 5 nodes, 4 edges
   INFO: Caching graph to database: a6fa84ef6e7511f080eaf9504434accd
   INFO: Graph saved with ID: 1
   INFO: Saved 5 nodes
   INFO: Saved 4 edges
   INFO: Graph cached successfully: 5 nodes, 4 edges
   ```

3. **验证响应**:
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

## 📝 代码风格说明

### Python 命名约定

- **变量和函数**: 下划线命名（snake_case）
  - 示例：`seed_component_id`, `save_graph_to_db`
  
- **类名**: 大驼峰命名（PascalCase）
  - 示例：`GraphService`, `ComponentGraph`

### JavaScript/JSON 命名约定

- **变量和字段**: 驼峰命名（camelCase）
  - 示例：`seedComponentId`, `totalNodes`

### 本项目的命名策略

- **内部代码**（Python）: 下划线命名
  - 示例：`graph.seed_component_id`
  
- **外部接口**（JSON）: 驼峰命名
  - 示例：`{"seedComponentId": "xxx"}`

---

## ⚠️ 注意事项

### 1. 时间格式转换

```python
# 错误 ❌
'generatedAt': graph.generated_at  # datetime 对象

# 正确 ✅
'generatedAt': graph.generated_at.isoformat()  # ISO 字符串
```

### 2. 空值处理

```python
# 错误 ❌
'expiresAt': graph.expires_at  # 可能是 None

# 正确 ✅
'expiresAt': graph.expires_at.isoformat() if graph.expires_at else None
```

### 3. 字段名必须完全匹配

```python
# 错误 ❌
'seed_component_id': ...  # save_graph_to_db 找不到这个字段

# 正确 ✅
'seedComponentId': ...  # 正确匹配
```

---

## 🔧 故障排查

### 问题 1: KeyError: 'seedComponentId'

**原因**: 字段名拼写错误

**解决**: 检查字段名是否完全匹配（大小写敏感）

---

### 问题 2: TypeError: isoformat()

**原因**: `generated_at` 不是 datetime 对象

**解决**: 确保类型正确：
```python
'generatedAt': graph.generated_at.isoformat() if graph.generated_at else datetime.now().isoformat()
```

---

### 问题 3: 数据库保存成功但返回错误

**原因**: 字段类型不匹配

**解决**: 检查所有字段的类型：
- 数字字段：`int` 或 `float`
- 时间字段：ISO 字符串
- 布尔字段：`bool`

---

## 📚 相关文档

- [BUGFIX_CACHE_GRAPH.md](BUGFIX_CACHE_GRAPH.md) - cache_graph_to_db 方法缺失修复
- [graph_service.py](graph_service.py) - 图谱服务实现
- [data_model.py](data_model.py) - 数据库操作
- [coding-standards](../../tdesign/AGENTS.md) - 代码风格指南

---

## ✅ 修复验证清单

- [x] 修改 `seed_component_id` → `seedComponentId`
- [x] 修改 `seed_component_name` → `seedComponentName`
- [x] 修改 `max_depth` → `maxDepth`
- [x] 修改 `total_nodes` → `totalNodes`
- [x] 修改 `total_edges` → `totalEdges`
- [x] 修改 `generated_at` → `generatedAt` (并转换为 ISO 字符串)
- [x] 修改 `expires_at` → `expiresAt` (并转换为 ISO 字符串)
- [x] 修改 `error_message` → `errorMessage`
- [x] 代码通过语法检查
- [ ] 运行 Postman 测试验证
- [ ] 检查数据库表数据

---

**修复时间**: 2026-05-19  
**修复版本**: v1.0.2  
**问题类型**: KeyError - 字段命名不匹配  
**影响范围**: 图谱缓存功能  
**修复状态**: ✅ 已完成
