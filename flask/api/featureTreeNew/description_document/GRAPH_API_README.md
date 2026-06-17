# 组件知识图谱 API 接口文档

## 概述

组件知识图谱功能用于可视化展示组件的全链路关联关系，包括：
- **所属模块**：通过 knowledge_component_tree 数据表向上查找
- **章节信息**：从 iCenter 页面提取 5.3.1 流程设计、5.7.7 FT 代码文件设计、4 组件对外接口
- **依赖组件**：从 iCenter 页面的"8 依赖组件"表格提取
- **波及特性**：从 iCenter 页面的"7 关联特性"表格提取
- **知识技能**：预留节点类型（暂不实现）

## 数据库设计

### 新增表结构

1. **knowledge_component_graph** - 图谱缓存表
2. **knowledge_component_graph_node** - 图谱节点明细表
3. **knowledge_component_graph_edge** - 图谱边明细表
4. **knowledge_component_section** - 组件章节信息表
5. **knowledge_component_graph_layout** - 图谱布局配置表

详细 SQL 脚本见：`graph_schema.sql`

### 数据库初始化

```bash
# 连接到 db5 数据库
mysql -u {username} -p -h {host} -P {port} {database}

# 执行建表脚本
source /path/to/graph_schema.sql
```

## API 接口列表

### 1. API_Knowledge_component_graph_get - 获取图谱

**功能**：生成或获取缓存的组件知识图谱

**请求参数**：
```json
{
  "seedComponentId": "SC001-xxx",  // 种子组件 ID（必填）
  "scope": "L0",                    // 范围 L0/L1/L2/WASON/OSP（必填）
  "maxDepth": 2,                    // 最大展开深度，默认 2（可选）
  "forceRefresh": false,            // 是否强制刷新，默认 false（可选）
  "operatorPerson": "xxx"           // 操作人（可选）
}
```

**返回格式**：
```json
{
  "code": 200,
  "status": "success",
  "message": "获取成功",
  "data": {
    "seedComponentId": "SC001-xxx",
    "seedComponentName": "SC001-SC_MP_IF 网管接口子组件设计",
    "scope": "L0",
    "maxDepth": 2,
    "status": "completed",
    "totalNodes": 50,
    "totalEdges": 45,
    "nodes": [
      {
        "id": "component_SC001",
        "name": "SC001-SC_MP_IF 网管接口子组件设计",
        "type": "component",
        "expanded": true,
        "level": 0,
        "url": "https://i.zte.com.cn/...",
        "spaceId": "xxx",
        "contentId": "xxx"
      },
      {
        "id": "module_M001",
        "name": "M001-SC_MIM_CHECK 消息校验",
        "type": "module",
        "level": 1
      },
      {
        "id": "section_SC001_5_3_1",
        "name": "5.3.1 流程设计",
        "type": "section",
        "desc": "5.3.1 流程设计",
        "level": 1
      },
      {
        "id": "component_dep_SC002",
        "name": "SC002-TAP 终端适配执行",
        "type": "dependent_component",
        "level": 1,
        "url": "https://i.zte.com.cn/..."
      },
      {
        "id": "feature_F010604",
        "name": "F010604-管控与 WASON",
        "type": "affected_feature",
        "level": 1,
        "url": "https://i.zte.com.cn/..."
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "component_SC001",
        "target": "module_M001",
        "relationType": "belongs_to",
        "relationLabel": "属于"
      },
      {
        "id": "edge_2",
        "source": "component_SC001",
        "target": "section_SC001_5_3_1",
        "relationType": "contains",
        "relationLabel": "包含"
      },
      {
        "id": "edge_3",
        "source": "component_SC001",
        "target": "component_dep_SC002",
        "relationType": "depends_on",
        "relationLabel": "依赖"
      },
      {
        "id": "edge_4",
        "source": "component_SC001",
        "target": "feature_F010604",
        "relationType": "affects",
        "relationLabel": "影响"
      }
    ],
    "generatedAt": "2026-05-19T10:00:00",
    "expiresAt": "2026-05-19T11:00:00"
  }
}
```

**节点类型说明**：
- `component`: 组件
- `module`: 模块
- `section`: 章节
- `dependent_component`: 依赖组件
- `affected_feature`: 波及特性
- `skill`: 知识技能（预留）

**关系类型说明**：
- `belongs_to`: 属于（组件→模块）
- `contains`: 包含（组件→章节）
- `depends_on`: 依赖（组件→依赖组件）
- `affects`: 影响（组件→波及特性）
- `requires`: 需要（组件→知识技能，预留）

---

### 2. API_Knowledge_component_graph_expand - 展开节点

**功能**：懒加载展开节点的关联关系

**请求参数**：
```json
{
  "graphId": 123,      // 图谱 ID（必填）
  "nodeId": "xxx"      // 节点 ID（必填）
}
```

**返回格式**：
```json
{
  "code": 200,
  "status": "success",
  "message": "展开成功",
  "data": {
    "newNodes": [...],
    "newEdges": [...]
  }
}
```

**说明**：
- 目前仅支持展开依赖组件和波及特性节点
- 返回新增的节点和边列表

---

### 3. API_Knowledge_component_graph_detail - 获取节点详情

**功能**：获取节点的详细信息（复用现有的 API_Knowledge_component_detail）

**请求参数**：
```json
{
  "nodeId": "xxx",       // 节点 ID（必填）
  "nodeType": "component", // 节点类型（必填）
  "url": "https://..."    // 节点 URL（可选）
}
```

**返回格式**：参考 `API_Knowledge_component_detail`

---

### 4. API_Knowledge_component_graph_layout_save - 保存布局

**功能**：保存用户的图谱布局配置

**请求参数**：
```json
{
  "graphId": 123,              // 图谱 ID（必填）
  "layoutName": "我的布局",     // 布局名称（必填）
  "layoutType": "custom",       // 布局类型 custom/dagre/force/circular（可选）
  "isDefault": true,           // 是否默认布局（可选）
  "isPublic": false,           // 是否公开（可选）
  "nodePositions": {           // 节点位置数据（必填）
    "node1": {"x": 100, "y": 200},
    "node2": {"x": 300, "y": 400}
  },
  "viewportConfig": {          // 视口配置（可选）
    "zoom": 1.0,
    "centerX": 500,
    "centerY": 300
  },
  "filterConfig": {            // 过滤配置（可选）
    "node_types": ["component", "module"],
    "relation_types": ["belongs_to"]
  },
  "description": "xxx",        // 布局描述（可选）
  "operatorPerson": "xxx"      // 操作人（可选）
}
```

**返回格式**：
```json
{
  "code": 200,
  "status": "success",
  "message": "保存成功",
  "data": {
    "layoutId": 123
  }
}
```

---

### 5. API_Knowledge_component_graph_layout_list - 获取布局列表

**功能**：获取用户的布局列表

**请求参数**：
```json
{
  "graphId": 123,              // 图谱 ID（必填）
  "operatorPerson": "xxx"      // 操作人（可选）
}
```

**返回格式**：
```json
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
```

---

### 6. API_Knowledge_component_graph_refresh - 刷新图谱

**功能**：强制刷新图谱（重新生成）

**请求参数**：同 `API_Knowledge_component_graph_get`

**返回格式**：同 `API_Knowledge_component_graph_get`

---

### 7. API_Knowledge_component_graph_stats - 获取统计信息

**功能**：获取图谱的统计信息

**请求参数**：
```json
{
  "graphId": 123      // 图谱 ID（必填）
}
```

**返回格式**：
```json
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
```

---

## 使用流程

### 1. 生成图谱

```javascript
// 用户从组件树选择种子组件
const seedComponentId = 'SC001-xxx';
const scope = 'L0';

// 调用 API 生成图谱
const response = await fetch('/api/api_data/API_Knowledge_component_graph_get', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    seedComponentId: seedComponentId,
    scope: scope,
    maxDepth: 2
  })
});

const result = await response.json();
const graphData = result.data;
```

### 2. 渲染图谱

```javascript
// 使用 G6 或 ECharts 渲染
// 节点数据：graphData.nodes
// 边数据：graphData.edges

// 节点类型映射颜色
const nodeTypeColors = {
  component: '#1890ff',
  module: '#722ed1',
  section: '#13c2c2',
  dependent_component: '#fa8c16',
  affected_feature: '#f5222d',
  skill: '#8c8c8c'
};

// 关系类型映射颜色
const relationTypeColors = {
  belongs_to: '#595959',
  contains: '#595959',
  depends_on: '#595959',
  affects: '#595959',
  requires: '#595959'
};
```

### 3. 保存布局

```javascript
// 用户拖拽节点后保存布局
const nodePositions = {};
graphData.nodes.forEach(node => {
  nodePositions[node.id] = {
    x: node.x,  // 从图可视化库获取
    y: node.y
  };
});

await fetch('/api/api_data/API_Knowledge_component_graph_layout_save', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    graphId: graphData.id,
    layoutName: '我的布局',
    nodePositions: nodePositions,
    operatorPerson: 'xxx'
  })
});
```

### 4. 懒加载展开

```javascript
// 用户点击未展开的节点
const nodeId = 'component_dep_SC002';

const response = await fetch('/api/api_data/API_Knowledge_component_graph_expand', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    graphId: graphData.id,
    nodeId: nodeId
  })
});

const result = await response.json();
// 将 result.data.newNodes 和 result.data.newEdges 添加到图谱中
```

---

## 缓存策略

### 1. 缓存有效期

- 图谱缓存有效期：**1 小时**
- 过期后自动重新生成
- 支持强制刷新（`forceRefresh: true`）

### 2. 缓存键

```
UNIQUE KEY: (seed_component_id, max_depth)
```

同一组件和深度的图谱只缓存一份。

### 3. 缓存更新

- 组件树刷新时，建议同步刷新相关图谱
- iCenter 页面更新时，建议清除相关缓存

---

## 性能优化

### 1. 分层懒加载

- 默认只展示 2 度关系
- 点击节点时按需展开
- 避免一次性加载过多数据

### 2. 视口裁剪

- 前端只渲染视口内的节点
- 支持缩放和拖拽
- 节点聚合（大规模图谱）

### 3. 数据库索引

```sql
-- 优化查询性能的关键索引
CREATE INDEX idx_graph_node_type ON knowledge_component_graph_node(graph_id, node_type, level);
CREATE INDEX idx_graph_edge_relation ON knowledge_component_graph_edge(graph_id, relation_type);
CREATE INDEX idx_graph_expires ON knowledge_component_graph(expires_at);
```

---

## 错误处理

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 500 | 服务器错误 |

### 错误响应

```json
{
  "code": 500,
  "status": "error",
  "message": "图谱生成失败：Component xxx not found"
}
```

---

## 开发调试

### 1. 日志查看

```bash
# 查看 Flask 应用日志
tail -f /path/to/flask/api/app.log

# 过滤图谱相关日志
tail -f /path/to/flask/api/app.log | grep "Graph"
```

### 2. 数据库查询

```sql
-- 查看缓存的图谱
SELECT * FROM knowledge_component_graph 
WHERE seed_component_id = 'SC001-xxx';

-- 查看图谱节点
SELECT * FROM knowledge_component_graph_node 
WHERE graph_id = 123;

-- 查看图谱边
SELECT * FROM knowledge_component_graph_edge 
WHERE graph_id = 123;
```

### 3. 测试工具

使用 Postman 或 curl 测试 API：

```bash
curl -X POST http://localhost:3001/api/api_data/API_Knowledge_component_graph_get \
  -H "Content-Type: application/json" \
  -d '{
    "seedComponentId": "SC001-xxx",
    "scope": "L0",
    "maxDepth": 2
  }'
```

---

## 前端集成建议

### 1. 图可视化库选型

**推荐：G6**
- 支持自定义节点样式
- 支持交互（拖拽、缩放、点击）
- 支持布局算法（DAG、力导向、圆形）
- 文档完善：https://g6.antv.antgroup.com/

**备选：ECharts Graph**
- 与 ECharts 生态集成好
- 性能优秀
- 文档：https://echarts.apache.org/zh/index.html

### 2. 组件结构

```
src/components/graph/
├── ComponentGraph.vue          # 图谱主组件
├── GraphToolbar.vue            # 工具栏（过滤、刷新、保存布局）
├── GraphLegend.vue             # 图例（节点类型、关系类型）
├── GraphDetailPanel.vue        # 详情面板
└── GraphLayoutDialog.vue       # 布局配置对话框
```

### 3. 状态管理

```typescript
// store/graph.ts
interface GraphState {
  currentGraph: GraphData | null;
  isLoading: boolean;
  nodeFilters: string[];  // 选中的节点类型
  relationFilters: string[];  // 选中的关系类型
  layouts: LayoutInfo[];
}
```

---

## 后续优化方向

1. **知识技能节点**：实现从人员技能地图表获取数据
2. **智能布局**：根据节点类型和关系自动优化布局
3. **路径高亮**：支持查询两个节点之间的路径并高亮显示
4. **导出功能**：支持导出图谱为 PNG/SVG
5. **版本对比**：对比不同版本的图谱差异

---

## 相关文件

- **数据库脚本**：`graph_schema.sql`
- **服务实现**：`graph_service.py`
- **API 接口**：`api_component_graph.py`
- **路由注册**：`app.py`（第 260-267 行）

---

*文档创建时间：2026-05-19*
*最后更新：2026-05-19*
