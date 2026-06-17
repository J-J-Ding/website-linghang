# 组件知识图谱实现总结

## 实现概述

已完成组件知识图谱的后端核心功能实现，包括数据库设计、服务层、API 接口和前端类型定义。

## 已完成内容

### 1. 数据库设计 ✅

**文件**: `graph_schema.sql`

创建了 5 张表：

1. **knowledge_component_graph** - 图谱缓存表
   - 主键：id
   - 唯一键：(seed_component_id, max_depth)
   - 字段：图谱状态、节点数、边数、图谱数据 JSON、过期时间等

2. **knowledge_component_graph_node** - 图谱节点明细表
   - 主键：id
   - 唯一键：(graph_id, node_id)
   - 字段：节点类型、节点名称、位置坐标、层级等

3. **knowledge_component_graph_edge** - 图谱边明细表
   - 主键：id
   - 唯一键：(graph_id, edge_id)
   - 字段：源节点、目标节点、关系类型、关系标注等

4. **knowledge_component_section** - 组件章节信息表
   - 主键：id
   - 唯一键：(component_id, section_id)
   - 字段：章节标题、章节类型、内容摘要等

5. **knowledge_component_graph_layout** - 图谱布局配置表
   - 主键：id
   - 字段：布局名称、布局类型、节点位置、视口配置等

### 2. 服务层实现 ✅

**文件**: `graph_service.py`

核心类：

- **NodeType** - 节点类型枚举
- **RelationType** - 关系类型枚举
- **GraphNode** - 图谱节点类
- **GraphEdge** - 图谱边类
- **ComponentGraph** - 图谱容器类
- **GraphService** - 图谱生成服务类

核心方法：

- `generate_graph()` - 生成图谱
- `expand_node()` - 展开节点（懒加载）
- `cache_graph_to_db()` - 缓存图谱到数据库
- `get_cached_graph()` - 从数据库获取缓存图谱
- `_find_module_for_component()` - 查找组件所属模块
- `_extract_sections_from_icenter()` - 提取 iCenter 页面章节
- `_extract_dependent_components()` - 提取依赖组件
- `_extract_affected_features()` - 提取波及特性

### 3. API 接口实现 ✅

**文件**: `api_component_graph.py`

实现了 7 个 API 接口：

1. **API_Knowledge_component_graph_get** - 获取图谱
2. **API_Knowledge_component_graph_expand** - 展开节点
3. **API_Knowledge_component_graph_detail** - 获取节点详情
4. **API_Knowledge_component_graph_layout_save** - 保存布局
5. **API_Knowledge_component_graph_layout_list** - 获取布局列表
6. **API_Knowledge_component_graph_refresh** - 刷新图谱
7. **API_Knowledge_component_graph_stats** - 获取统计信息

### 4. 路由注册 ✅

**文件**: `app.py`

已在第 260-267 行注册了 7 个新 API 路由：

```python
app.route('/api/api_data/API_Knowledge_component_graph_get', methods=['POST'])(API_Knowledge_component_graph_get)
app.route('/api/api_data/API_Knowledge_component_graph_expand', methods=['POST'])(API_Knowledge_component_graph_expand)
app.route('/api/api_data/API_Knowledge_component_graph_detail', methods=['POST'])(API_Knowledge_component_graph_detail)
app.route('/api/api_data/API_Knowledge_component_graph_layout_save', methods=['POST'])(API_Knowledge_component_graph_layout_save)
app.route('/api/api_data/API_Knowledge_component_graph_layout_list', methods=['POST'])(API_Knowledge_component_graph_layout_list)
app.route('/api/api_data/API_Knowledge_component_graph_refresh', methods=['POST'])(API_Knowledge_component_graph_refresh)
app.route('/api/api_data/API_Knowledge_component_graph_stats', methods=['POST'])(API_Knowledge_component_graph_stats)
```

### 5. 前端类型定义 ✅

**文件**: `tdesign/src/types/graph.ts`

定义了完整的 TypeScript 类型：

- 枚举：`GraphNodeType`, `GraphRelationType`, `GraphStatus`
- 接口：`GraphNode`, `GraphEdge`, `GraphData`
- API 请求/响应类型
- 视觉配置：`NODE_TYPE_VISUAL_MAP`, `RELATION_TYPE_VISUAL_MAP`
- 工具函数：`filterGraphData()`, `isNodeExpandable()` 等

### 6. 文档 ✅

**文件**: `GRAPH_API_README.md`

包含：
- API 接口详细文档
- 请求/响应示例
- 使用流程说明
- 缓存策略说明
- 性能优化建议
- 前端集成指南

## 待完成内容

### 1. 数据库初始化 ⚠️

需要执行 SQL 脚本创建表：

```bash
# 连接到 db5 数据库
mysql -u {username} -p -h {host} -P {port} db5

# 执行建表脚本
source /path/to/flask/api/componentTree/graph_schema.sql
```

### 2. 前端组件开发 ⚠️

需要开发以下前端组件：

```
src/components/graph/
├── ComponentGraph.vue          # 图谱主组件
├── GraphToolbar.vue            # 工具栏（过滤、刷新、保存布局）
├── GraphLegend.vue             # 图例（节点类型、关系类型）
├── GraphDetailPanel.vue        # 详情面板
└── GraphLayoutDialog.vue       # 布局配置对话框
```

### 3. 图可视化库选型 ⚠️

**推荐**: G6 (AntV)
- 文档：https://g6.antv.antgroup.com/
- 安装：`npm install @antv/g6`

**备选**: ECharts Graph
- 文档：https://echarts.apache.org/zh/index.html

### 4. 节点展开逻辑完善 ⚠️

`graph_service.py` 中的 `expand_node()` 方法目前返回空数据，需要实现：
- 依赖组件的二级关联（依赖的依赖）
- 波及特性的二级关联（特性的其他组件）

### 5. 知识技能节点 ⚠️

目前 `skill` 节点类型已预留，但数据来源未实现。后续可从以下表获取：
- `person_skill_map` - 人员技能地图表
- `module_featurecheckpoint_content_data` - 模块特性检查点内容数据

## 使用流程

### 后端启动

1. **执行数据库初始化**
   ```bash
   mysql -u username -p -h host -P 3306 db5 < flask/api/componentTree/graph_schema.sql
   ```

2. **启动 Flask 后端**
   ```bash
   cd flask/api
   gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 app:app
   ```

### 前端集成

1. **安装 G6**
   ```bash
   cd tdesign
   npm install @antv/g6
   ```

2. **创建图谱组件**
   ```vue
   <template>
     <div class="component-graph">
       <div ref="graphContainer" class="graph-container"></div>
       <GraphToolbar />
       <GraphLegend />
     </div>
   </template>
   
   <script setup lang="ts">
   import { ref, onMounted } from 'vue';
   import { Graph } from '@antv/g6';
   import { getGraphData } from '@/api/graph';
   
   const graphContainer = ref<HTMLDivElement | null>(null);
   let graph: Graph | null = null;
   
   onMounted(async () => {
     // 获取图谱数据
     const graphData = await getGraphData({
       seedComponentId: 'SC001-xxx',
       scope: 'L0',
       maxDepth: 2
     });
     
     // 初始化 G6 图谱
     graph = new Graph({
       container: graphContainer.value!,
       width: 800,
       height: 600,
       // ... 其他配置
     });
     
     graph.data(graphData);
     graph.render();
   });
   </script>
   ```

3. **调用 API**
   ```typescript
   // src/api/graph.ts
   import request from '@/utils/request';
   import type { GetGraphRequest, GetGraphResponse } from '@/types/graph';
   
   export async function getGraphData(params: GetGraphRequest) {
     const response = await request.post<GetGraphResponse>(
       '/api/api_data/API_Knowledge_component_graph_get',
       params
     );
     return response.data.data;
   }
   ```

## 测试验证

### 1. 使用 Postman 测试

**请求示例**：
```http
POST http://localhost:3001/api/api_data/API_Knowledge_component_graph_get
Content-Type: application/json

{
  "seedComponentId": "SC001-xxx",
  "scope": "L0",
  "maxDepth": 2
}
```

### 2. 检查数据库

```sql
-- 查看缓存的图谱
SELECT id, seed_component_name, status, total_nodes, total_edges, generated_at 
FROM knowledge_component_graph 
ORDER BY create_time DESC 
LIMIT 10;

-- 查看节点分布
SELECT node_type, COUNT(*) as count 
FROM knowledge_component_graph_node 
GROUP BY node_type;

-- 查看关系分布
SELECT relation_type, COUNT(*) as count 
FROM knowledge_component_graph_edge 
GROUP BY relation_type;
```

### 3. 查看日志

```bash
# 查看 Flask 日志
tail -f flask/api/app.log | grep "Graph"

# 查看错误日志
tail -f flask/api/app.log | grep "ERROR"
```

## 性能优化建议

### 1. 数据库索引

```sql
-- 添加索引优化查询性能
CREATE INDEX idx_graph_node_type ON knowledge_component_graph_node(graph_id, node_type, level);
CREATE INDEX idx_graph_edge_relation ON knowledge_component_graph_edge(graph_id, relation_type);
CREATE INDEX idx_graph_expires ON knowledge_component_graph(expires_at);
```

### 2. 缓存策略

- 图谱缓存有效期：1 小时
- 支持强制刷新
- 懒加载展开节点

### 3. 前端优化

- 视口裁剪（只渲染可见节点）
- 节点聚合（大规模图谱）
- Web Worker（复杂布局计算）

## 常见问题

### Q1: 图谱生成失败

**原因**: 组件 ID 不存在或 iCenter 页面无法访问

**解决**: 
1. 检查组件 ID 是否正确
2. 检查 iCenter 网络连接
3. 查看日志中的详细错误信息

### Q2: 章节提取失败

**原因**: iCenter 页面结构变化或正则匹配失败

**解决**:
1. 检查 `_extract_sections_from_icenter()` 方法中的正则表达式
2. 添加更多兼容模式（如"五、组件对外接口"）

### Q3: 前端渲染性能差

**原因**: 节点数量过多（>1000）

**解决**:
1. 启用懒加载
2. 使用视口裁剪
3. 节点聚合（Cluster）

## 下一步计划

1. **完善节点展开逻辑** - 实现依赖组件和波及特性的二级关联
2. **开发前端组件** - 基于 G6 实现图谱可视化
3. **添加单元测试** - 覆盖核心函数和 API 接口
4. **性能测试** - 测试 1000+ 节点的渲染性能
5. **知识技能集成** - 从人员技能地图表获取数据

## 相关文件清单

```
flask/api/componentTree/
├── graph_schema.sql              # 数据库建表脚本
├── graph_service.py              # 图谱生成服务
├── api_component_graph.py        # API 接口实现
├── GRAPH_API_README.md           # API 接口文档
├── IMPLEMENTATION_SUMMARY.md     # 实现总结（本文件）
└── data_model.py                 # 数据模型（已有）

tdesign/src/types/
└── graph.ts                      # TypeScript 类型定义

flask/api/
└── app.py                        # 路由注册（已修改）
```

---

*实现完成时间：2026-05-19*
*作者：AI Assistant*
