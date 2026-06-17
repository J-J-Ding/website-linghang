# 组件知识图谱 API 使用说明

## 问题说明

### 原始问题

调用 `API_Knowledge_component_graph_get` 接口时报错：
```json
{
    "code": 400,
    "status": "error",
    "message": "缺少必填参数：seedComponentId, scope"
}
```

或

```json
{
    "code": 500,
    "status": "error",
    "message": "图谱生成失败：Component C-F023-PRTC 组件 not found"
}
```

---

## 根本原因分析

### 1. 组件树四级结构

```
Level 0: 根节点 (root)
    └─ Level 1: 领域分类 (category)
        └─ Level 2: 组件/子组件/模块 (component/module)
            └─ Level 3: 子组件/模块 (component/module)
                └─ Level 4: 模块 (module)
```

### 2. 数据库字段说明

在 `knowledge_component_tree` 表中：

| 字段名 | 说明 | 示例值 |
|--------|------|--------|
| `node_id` | 节点唯一标识（content_id） | `a6fa84ef6e7511f080eaf9504434accd` |
| `title` | 节点标题（显示名称） | `C-F023-PRTC 组件` |
| `level` | 层级 | `2` |
| `node_type` | 节点类型 | `component` |
| `parent_id` | 父节点 ID | `9de71306f96e11efb81c0bfbc4e63315` |
| `scope` | 领域范围 | `L1` |

### 3. 错误原因

**错误的请求**：
```json
{
    "seedComponentId": "C-F023-PRTC 组件",  // ❌ 这是 title，不是 node_id
    "scope": "L1"
}
```

**后端查询逻辑**（修改前）：
```python
seed_component = db.session.query(KNOWLEDGE_COMPONENT_TREE).filter(
    KNOWLEDGE_COMPONENT_TREE.node_id == seed_component_id,  # ← 只匹配 node_id
    KNOWLEDGE_COMPONENT_TREE.scope == scope,
    KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y"
).first()
```

**结果**：
- 用 `"C-F023-PRTC 组件"` 匹配 `node_id` 字段
- 数据库中 `node_id = "a6fa84ef6e7511f080eaf9504434accd"`
- ❌ **查询失败**

---

## 解决方案

### 方案一：使用正确的 node_id（推荐）

#### 步骤 1: 调用组件树接口获取 node_id

```bash
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_tree
Content-Type: application/json

{
    "tab": "L1",
    "maxLevel": 4
}
```

#### 步骤 2: 从返回数据中提取 node_id

```json
{
  "code": 200,
  "data": {
    "root": {
      "children": [
        {
          "title": "L1 领域 - 应用 - 组件树",
          "children": [
            {
              "id": "a6fa84ef6e7511f080eaf9504434accd",  // ← 这就是 seedComponentId
              "title": "C-F023-PRTC 组件",
              "level": 2,
              "nodeType": "component"
            }
          ]
        }
      ]
    }
  }
}
```

#### 步骤 3: 使用 node_id 调用图谱接口

```bash
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
Content-Type: application/json

{
    "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",  // ✅ 使用 node_id
    "scope": "L1",
    "maxDepth": 2,
    "forceRefresh": false
}
```

---

### 方案二：支持 title 查询（已实现）

#### 修改内容

修改 `graph_service.py` 中的 `generate_graph()` 函数：

```python
from sqlalchemy import or_

# Step 1: 查询种子组件信息（支持 node_id 或 title 查询）
seed_component = db.session.query(KNOWLEDGE_COMPONENT_TREE).filter(
    KNOWLEDGE_COMPONENT_TREE.scope == scope,
    KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
    or_(
        KNOWLEDGE_COMPONENT_TREE.node_id == seed_component_id,
        KNOWLEDGE_COMPONENT_TREE.title == seed_component_id
    )
).first()
```

#### 现在两种方式都可以

```bash
# 方式 A: 使用 node_id
{
    "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
    "scope": "L1"
}

# 方式 B: 使用 title（新增支持）
{
    "seedComponentId": "C-F023-PRTC 组件",
    "scope": "L1"
}
```

---

## 完整测试流程

### 测试 1: 使用 node_id

```bash
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
Content-Type: application/json

{
    "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
    "scope": "L1",
    "maxDepth": 2
}
```

**预期响应**：
```json
{
    "code": 200,
    "status": "success",
    "message": "获取成功",
    "data": {
        "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
        "seedComponentName": "C-F023-PRTC 组件",
        "scope": "L1",
        "maxDepth": 2,
        "status": "completed",
        "totalNodes": 50,
        "totalEdges": 45,
        "nodes": [...],
        "edges": [...]
    }
}
```

### 测试 2: 使用 title（修改后支持）

```bash
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
Content-Type: application/json

{
    "seedComponentId": "C-F023-PRTC 组件",
    "scope": "L1",
    "maxDepth": 2
}
```

**预期响应**：同上

---

## 常见错误及解决方案

### 错误 1: 405 Method Not Allowed

**原因**：使用了 GET 方法而不是 POST

**解决**：确保使用 POST 方法

```bash
# ❌ 错误
GET http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get

# ✅ 正确
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
```

### 错误 2: 400 缺少必填参数

**原因**：
- Content-Type 未设置为 `application/json`
- 参数放在了 URL 而不是 Body 中
- JSON 格式错误

**解决**：
1. 设置 Header: `Content-Type: application/json`
2. 参数放在 Body 中，选择 raw + JSON 格式
3. 确保 JSON 格式正确

### 错误 3: 500 Component not found

**原因**：
- `seedComponentId` 值错误（用 title 当 node_id 用）
- `scope` 范围不匹配
- 组件在数据库中不存在

**解决**：
1. 先调用组件树接口获取正确的 node_id
2. 确保 scope 与组件所属领域一致
3. 检查组件是否存在于数据库

---

## Postman 配置示例

### Request 配置

```
Method: POST
URL: http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
```

### Headers

```
Content-Type: application/json
```

### Body (raw - JSON)

```json
{
    "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
    "scope": "L1",
    "maxDepth": 2,
    "forceRefresh": false,
    "operatorPerson": "测试用户"
}
```

---

## 参数说明

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `seedComponentId` | String | ✅ 是 | - | 种子组件 ID（node_id 或 title 均可） |
| `scope` | String | ✅ 是 | - | 范围：L0/L1/L2/WASON/OSP |
| `maxDepth` | Integer | ❌ 否 | 2 | 最大展开深度（1-5） |
| `forceRefresh` | Boolean | ❌ 否 | false | 是否强制刷新缓存 |
| `operatorPerson` | String | ❌ 否 | "" | 操作人姓名 |

---

## 数据流程图

```
用户请求
    ↓
Step 1: 查询缓存 (knowledge_component_graph)
    ↓
[缓存命中] → 返回缓存数据 ✅
    ↓
[缓存未命中]
    ↓
Step 2: 查询种子组件 (knowledge_component_tree)
    ↓
[组件不存在] → 返回错误 ❌
    ↓
[组件存在]
    ↓
Step 3: 查询所有节点 (用于查找模块)
    ↓
Step 4: 查找所属模块 (递归向上查找 parent_id)
    ↓
Step 5: 提取章节信息 (解析 iCenter 页面)
    ↓
Step 6: 提取依赖组件 (解析"8 依赖组件"表格)
    ↓
Step 7: 提取波及特性 (解析"7 关联特性"表格)
    ↓
Step 8: 组装图谱数据 (nodes + edges)
    ↓
Step 9: 缓存到数据库 (knowledge_component_graph)
    ↓
返回图谱数据 ✅
```

---

## 相关文档

- [API 接口文档](./GRAPH_API_README.md)
- [部署检查清单](./DEPLOYMENT_CHECKLIST.md)
- [实现总结](./IMPLEMENTATION_SUMMARY.md)
- [节点类型修复脚本](./fix_node_type.sql)

---

*更新时间：2026-05-19*
