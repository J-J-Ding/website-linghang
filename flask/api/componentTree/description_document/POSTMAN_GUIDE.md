# Postman 测试组件知识图谱 API 指南

## 📥 步骤 1: 导入 Postman 集合

### 方式 A: 导入 JSON 文件（推荐）

1. 打开 Postman
2. 点击左上角的 **Import** 按钮
3. 选择文件：`flask/api/componentTree/POSTMAN_COLLECTION.json`
4. 点击 **Import**

### 方式 B: 手动创建集合

1. 点击 **New** → **Collection**
2. 命名为：`组件知识图谱 API`
3. 添加环境变量：
   - `base_url`: `http://10.239.69.183:3030`
   - `api_path`: `/api/api_data`

---

## 🚀 步骤 2: 测试获取图谱 API

### 2.1 选择请求

在左侧集合中找到：
```
组件知识图谱 API → 1. 获取组件知识图谱
```

### 2.2 配置请求参数

**请求 URL**:
```
POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
```

**Headers**:
```
Content-Type: application/json
```

**Body** (raw, JSON):
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": false,
  "operatorPerson": "测试用户"
}
```

### 2.3 发送请求

点击 **Send** 按钮

---

## 📊 步骤 3: 查看响应

### 成功响应 (200 OK)

```json
{
  "code": 200,
  "status": "success",
  "message": "图谱获取成功",
  "data": {
    "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
    "seedComponentName": "C-F023-PRTC 组件",
    "scope": "L1",
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
        "contentId": "xxx"
      },
      ...
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "center1",
        "target": "center1_mod1",
        "relationType": "belongs_to",
        "relationLabel": "属于"
      },
      ...
    ],
    "generatedAt": "2026-05-19T10:00:00",
    "expiresAt": "2026-05-19T11:00:00"
  }
}
```

### 错误响应 (400 Bad Request)

```json
{
  "code": 400,
  "status": "error",
  "message": "缺少必填参数：seedComponentId, scope"
}
```

**原因**: 参数未正确传递

**解决**: 检查 Body 是否为 JSON 格式，Content-Type 是否正确

---

## 🔍 步骤 4: 查看后端打印日志

发送请求后，后端会打印详细日志：

```
================================================================================
[API_Knowledge_component_graph_get] 接收到请求参数:
  - 完整请求体：{"seedComponentId":"C-F023-PRTC 组件","scope":"L1","maxDepth":2,"forceRefresh":false,"operatorPerson":"测试用户"}
  - seedComponentId: C-F023-PRTC 组件
  - scope: L1
  - maxDepth: 2
  - forceRefresh: false
  - operatorPerson: 测试用户
================================================================================
```

如果看到：
```
  - 完整请求体：{}
  - seedComponentId: 
  - scope: 
```

说明**参数没有正确传递**，请检查：
1. ✅ Content-Type 是否为 `application/json`
2. ✅ Body 是否选择了 **raw** 格式
3. ✅ Body 是否是有效的 JSON

---

## 🧪 步骤 5: 测试不同场景

### 测试用例 1: 使用 title 查询

**Body**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2
}
```

**预期**: ✅ 成功返回图谱数据

---

### 测试用例 2: 使用 node_id 查询

**Body**:
```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1",
  "maxDepth": 2
}
```

**预期**: ✅ 成功返回图谱数据

---

### 测试用例 3: 强制刷新

**Body**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": true
}
```

**预期**: ✅ 重新生成图谱（忽略缓存）

---

### 测试用例 4: 不同深度

**Body**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 1
}
```

**预期**: ✅ 返回 1 度关系的图谱

---

### 测试用例 5: 缺少必填参数

**Body**:
```json
{
  "scope": "L1"
}
```

**预期**: ❌ 返回 400 错误

```json
{
  "code": 400,
  "status": "error",
  "message": "缺少必填参数：seedComponentId"
}
```

---

## 📋 其他 API 接口

### 2. 展开节点

**URL**: `POST /api/api_data/API_Knowledge_component_graph_expand`

**Body**:
```json
{
  "graphId": "graph_123",
  "nodeId": "node_456"
}
```

---

### 3. 获取节点详情

**URL**: `POST /api/api_data/API_Knowledge_component_graph_detail`

**Body**:
```json
{
  "nodeId": "node_123",
  "nodeType": "component",
  "url": "https://icenter.zte.com.cn/space/xxx"
}
```

---

### 4. 保存用户布局

**URL**: `POST /api/api_data/API_Knowledge_component_graph_layout_save`

**Body**:
```json
{
  "graphId": "graph_123",
  "layoutName": "我的布局 1",
  "layoutType": "force",
  "isDefault": true,
  "isPublic": false,
  "nodePositions": {
    "node_1": { "x": 100, "y": 200 },
    "node_2": { "x": 300, "y": 400 }
  },
  "viewportConfig": {
    "zoom": 1.5,
    "centerX": 500,
    "centerY": 300
  },
  "filterConfig": {
    "node_types": ["component", "module"],
    "relation_types": ["belongs_to", "contains"]
  },
  "operatorPerson": "测试用户"
}
```

---

### 5. 获取布局列表

**URL**: `POST /api/api_data/API_Knowledge_component_graph_layout_list`

**Body**:
```json
{
  "graphId": "graph_123",
  "operatorPerson": "测试用户"
}
```

---

### 6. 刷新图谱

**URL**: `POST /api/api_data/API_Knowledge_component_graph_refresh`

**Body**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2
}
```

---

### 7. 获取图谱统计

**URL**: `POST /api/api_data/API_Knowledge_component_graph_stats`

**Body**:
```json
{
  "graphId": "graph_123"
}
```

---

## ⚠️ 常见错误排查

### 错误 1: 405 Method Not Allowed

**现象**:
```
405 Method Not Allowed
The method is not allowed for the requested URL.
```

**原因**: 使用了错误的 HTTP 方法（如 GET）

**解决**: 确保使用 **POST** 方法

---

### 错误 2: 400 Bad Request

**现象**:
```json
{
  "code": 400,
  "message": "缺少必填参数：seedComponentId, scope"
}
```

**原因**: 
- Body 格式不正确
- Content-Type 未设置
- 参数未序列化

**解决**:
1. 确保 Body 选择 **raw** 格式
2. 确保 Content-Type 为 `application/json`
3. 确保 Body 是有效的 JSON

---

### 错误 3: 500 Internal Server Error

**现象**:
```json
{
  "code": 500,
  "message": "图谱生成失败：Component xxx not found"
}
```

**原因**: 组件不存在

**解决**: 检查 seedComponentId 是否正确

---

## 🎯 Postman 使用技巧

### 技巧 1: 使用环境变量

1. 点击右上角的 **Environment quick look**
2. 添加环境变量：
   ```
   base_url: http://10.239.69.183:3030
   api_path: /api/api_data
   ```
3. 在 URL 中使用：`{{base_url}}{{api_path}}/API_...`

### 技巧 2: 查看请求历史

点击 **History** 标签可以查看所有历史请求

### 技巧 3: 保存响应示例

1. 发送请求后
2. 点击 **Save Response** → **Save as Example**
3. 命名并保存

### 技巧 4: 使用 Collection Runner 批量测试

1. 点击集合名称
2. 选择 **Run** 标签
3. 配置运行次数和延迟
4. 点击 **Run**

---

## 📞 问题排查清单

如果测试失败，请按顺序检查：

- [ ] 后端服务是否启动（端口 3030）
- [ ] 数据库表是否创建（graph_schema.sql）
- [ ] 组件数据是否存在（knowledge_component_tree 表）
- [ ] Postman 请求方法是否为 POST
- [ ] Content-Type 是否为 application/json
- [ ] Body 是否为 raw 格式的 JSON
- [ ] 参数名称是否正确（seedComponentId, scope）
- [ ] 后端日志是否有打印信息

---

## 📚 相关文档

- [GRAPH_API_README.md](GRAPH_API_README.md) - API 接口详细文档
- [GRAPH_API_USAGE.md](GRAPH_API_USAGE.md) - 使用说明
- [DEBUG_PRINT_GUIDE.md](DEBUG_PRINT_GUIDE.md) - 调试打印指南
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 部署检查清单

---

**文档创建时间**: 2026-05-19  
**适用版本**: v1.0.0  
**Postman 集合**: POSTMAN_COLLECTION.json
