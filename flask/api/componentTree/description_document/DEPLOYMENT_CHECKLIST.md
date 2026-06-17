# 组件知识图谱部署检查清单

## 部署前检查

### 1. 数据库准备 ✅

- [ ] 确认已连接到 db5 数据库
- [ ] 执行建表脚本 `graph_schema.sql`
- [ ] 验证 5 张表已创建成功
- [ ] 添加必要的索引（可选，提升性能）

**SQL 验证脚本**:
```sql
-- 检查表是否存在
SHOW TABLES LIKE 'knowledge_component_graph%';

-- 检查表结构
DESC knowledge_component_graph;
DESC knowledge_component_graph_node;
DESC knowledge_component_graph_edge;
DESC knowledge_component_section;
DESC knowledge_component_graph_layout;

-- 添加性能优化索引（可选）
CREATE INDEX IF NOT EXISTS idx_graph_node_type ON knowledge_component_graph_node(graph_id, node_type, level);
CREATE INDEX IF NOT EXISTS idx_graph_edge_relation ON knowledge_component_graph_edge(graph_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_graph_expires ON knowledge_component_graph(expires_at);
```

### 2. 后端依赖检查 ✅

- [ ] 确认已安装 `BeautifulSoup4`
- [ ] 确认已安装 `requests`
- [ ] 确认 `get_icenter.py` 可用
- [ ] 确认 `componentTree/data_model.py` 可用

**依赖安装**:
```bash
cd flask/api
pip install beautifulsoup4 requests
```

### 3. 代码文件检查 ✅

- [ ] `graph_schema.sql` - 数据库建表脚本
- [ ] `graph_service.py` - 图谱生成服务
- [ ] `api_component_graph.py` - API 接口实现
- [ ] `test_graph_api.py` - 测试脚本
- [ ] `GRAPH_API_README.md` - API 文档
- [ ] `IMPLEMENTATION_SUMMARY.md` - 实现总结
- [ ] `DEPLOYMENT_CHECKLIST.md` - 部署清单（本文件）

### 4. 路由注册检查 ✅

- [ ] 在 `app.py` 中已导入新的 API 函数
- [ ] 在 `app.py` 中已注册 7 个新路由
- [ ] 确认路由前缀正确：`/api/api_data/`

**验证方法**:
```bash
# 检查 app.py 中的导入
grep -n "from componentTree.api_component_graph import" flask/api/app.py

# 检查路由注册
grep -n "API_Knowledge_component_graph" flask/api/app.py
```

### 5. 后端启动测试 ✅

**启动 Flask 后端**:
```bash
cd flask/api
gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 app:app
```

**验证服务启动成功**:
```bash
# 检查端口监听
netstat -tlnp | grep 3001

# 或使用 curl 测试健康检查
curl http://localhost:3001/
```

### 6. API 接口测试 ✅

**运行测试脚本**:
```bash
cd flask/api/componentTree
python test_graph_api.py
```

**或使用 Postman 手动测试**:
```http
POST http://localhost:3001/api/api_data/API_Knowledge_component_graph_get
Content-Type: application/json

{
  "seedComponentId": "SC001-xxx",
  "scope": "L0",
  "maxDepth": 2
}
```

### 7. 日志检查 ✅

**查看日志**:
```bash
# 查看 Flask 应用日志
tail -f flask/api/app.log

# 过滤图谱相关日志
tail -f flask/api/app.log | grep "Graph"

# 查看错误日志
tail -f flask/api/app.log | grep "ERROR"
```

**预期日志内容**:
```
INFO - Generating graph for seed component SC001-xxx, scope=L0, max_depth=2
INFO - Graph generated successfully: 50 nodes, 45 edges
INFO - Graph cached to DB with id=1
```

### 8. 数据库验证 ✅

**查询缓存的图谱**:
```sql
-- 查看最近生成的图谱
SELECT 
    id, 
    seed_component_name, 
    scope, 
    status, 
    total_nodes, 
    total_edges, 
    generated_at, 
    expires_at 
FROM knowledge_component_graph 
ORDER BY create_time DESC 
LIMIT 10;

-- 查看某个图谱的节点分布
SELECT 
    node_type, 
    COUNT(*) as count 
FROM knowledge_component_graph_node 
WHERE graph_id = 1 
GROUP BY node_type;

-- 查看某个图谱的关系统计
SELECT 
    relation_type, 
    COUNT(*) as count 
FROM knowledge_component_graph_edge 
WHERE graph_id = 1 
GROUP BY relation_type;
```

## 前端集成步骤

### 9. 前端依赖安装 ⚠️

**安装 G6 图可视化库**:
```bash
cd tdesign
npm install @antv/g6
```

**或使用 ECharts**:
```bash
cd tdesign
npm install echarts
```

### 10. 前端类型定义 ⚠️

- [ ] 确认 `tdesign/src/types/graph.ts` 已创建
- [ ] 在需要使用的组件中导入类型

**使用示例**:
```typescript
import type { GraphData, GraphNode, GraphEdge } from '@/types/graph';
```

### 11. 前端组件开发 ⚠️

**建议的组件结构**:
```
src/components/graph/
├── ComponentGraph.vue          # 图谱主组件
├── GraphToolbar.vue            # 工具栏
├── GraphLegend.vue             # 图例
├── GraphDetailPanel.vue        # 详情面板
└── GraphLayoutDialog.vue       # 布局对话框
```

**最小化实现** (仅用于验证):
```vue
<template>
  <div ref="graphContainer" style="width: 800px; height: 600px;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Graph } from '@antv/g6';
import request from '@/utils/request';

const graphContainer = ref<HTMLDivElement | null>(null);

onMounted(async () => {
  // 获取图谱数据
  const response = await request.post('/api/api_data/API_Knowledge_component_graph_get', {
    seedComponentId: 'SC001-xxx',
    scope: 'L0',
    maxDepth: 2
  });
  
  const graphData = response.data.data;
  
  // 初始化 G6 图谱
  const graph = new Graph({
    container: graphContainer.value!,
    width: 800,
    height: 600,
    modes: {
      default: ['drag-canvas', 'zoom-canvas', 'drag-node']
    },
  });
  
  graph.data(graphData);
  graph.render();
});
</script>
```

### 12. 前端路由配置 ⚠️

**在 `tdesign/src/router/modules/ai.ts` 中添加路由**:
```typescript
{
  path: 'graph',
  name: 'AiGraph',
  component: () => import('@/pages/ai/graph/index.vue'),
  meta: { title: { zh_CN: '组件知识图谱', en_US: 'Component Graph' } },
}
```

### 13. 前端 API 封装 ⚠️

**创建 `src/api/graph.ts`**:
```typescript
import request from '@/utils/request';
import type {
  GetGraphRequest,
  GetGraphResponse,
  GraphData
} from '@/types/graph';

/**
 * 获取组件知识图谱
 */
export async function getGraphData(params: GetGraphRequest): Promise<GraphData> {
  const response = await request.post<GetGraphResponse>(
    '/api/api_data/API_Knowledge_component_graph_get',
    params
  );
  return response.data.data;
}

/**
 * 保存布局
 */
export async function saveLayout(params: SaveLayoutRequest) {
  const response = await request.post(
    '/api/api_data/API_Knowledge_component_graph_layout_save',
    params
  );
  return response.data.data;
}

/**
 * 获取布局列表
 */
export async function getLayoutList(params: GetLayoutListRequest) {
  const response = await request.post(
    '/api/api_data/API_Knowledge_component_graph_layout_list',
    params
  );
  return response.data.data;
}
```

## 性能优化检查

### 14. 数据库索引优化 ✅

**添加索引** (如果尚未添加):
```sql
-- 图谱查询优化
CREATE INDEX IF NOT EXISTS idx_graph_seed ON knowledge_component_graph(seed_component_id, max_depth, status);
CREATE INDEX IF NOT EXISTS idx_graph_expires ON knowledge_component_graph(expires_at);

-- 节点查询优化
CREATE INDEX IF NOT EXISTS idx_graph_node_graph ON knowledge_component_graph_node(graph_id, level, node_type);

-- 边查询优化
CREATE INDEX IF NOT EXISTS idx_graph_edge_graph ON knowledge_component_graph_edge(graph_id, source_node_id, target_node_id);
```

### 15. 缓存策略验证 ✅

- [ ] 图谱缓存有效期为 1 小时
- [ ] 支持强制刷新参数 `forceRefresh: true`
- [ ] 验证缓存命中逻辑

**验证方法**:
```sql
-- 查看缓存的图谱和过期时间
SELECT 
    seed_component_name,
    generated_at,
    expires_at,
    TIMESTAMPDIFF(MINUTE, NOW(), expires_at) as minutes_until_expire
FROM knowledge_component_graph
WHERE status = 'completed'
ORDER BY expires_at DESC;
```

### 16. 前端性能优化 ⚠️

- [ ] 启用懒加载（默认只展示 2 度关系）
- [ ] 实现视口裁剪（只渲染可见节点）
- [ ] 添加节点聚合（>1000 节点时）
- [ ] 使用 Web Worker 进行布局计算

## 安全与监控

### 17. 错误处理验证 ✅

- [ ] 测试无效组件 ID 的错误处理
- [ ] 测试数据库连接失败的处理
- [ ] 测试 iCenter 页面无法访问的处理
- [ ] 验证错误日志记录

**预期错误响应**:
```json
{
  "code": 500,
  "status": "error",
  "message": "图谱生成失败：Component xxx not found"
}
```

### 18. 监控指标 ⚠️

**建议添加的监控**:
- [ ] 图谱生成成功率
- [ ] 图谱生成平均耗时
- [ ] 缓存命中率
- [ ] API 调用次数
- [ ] 错误率统计

## 回滚方案

### 19. 回滚步骤

**如果需要回滚**:

1. **删除数据库表**:
```sql
DROP TABLE IF EXISTS knowledge_component_graph_layout;
DROP TABLE IF EXISTS knowledge_component_graph_edge;
DROP TABLE IF EXISTS knowledge_component_graph_node;
DROP TABLE IF EXISTS knowledge_component_section;
DROP TABLE IF EXISTS knowledge_component_graph;
```

2. **移除代码文件**:
```bash
rm flask/api/componentTree/graph_schema.sql
rm flask/api/componentTree/graph_service.py
rm flask/api/componentTree/api_component_graph.py
rm flask/api/componentTree/test_graph_api.py
```

3. **移除路由注册**:
   - 编辑 `flask/api/app.py`
   - 删除第 20-27 行的导入
   - 删除第 260-267 行的路由注册

4. **重启 Flask 服务**

## 部署完成确认

### 20. 最终验证清单

- [ ] 数据库表创建成功
- [ ] 后端服务启动正常
- [ ] 所有 API 接口可访问
- [ ] 测试脚本运行通过
- [ ] 日志记录正常
- [ ] 错误处理正确
- [ ] 前端集成完成（如果实施）
- [ ] 性能指标达标

**签署确认**:
- 开发人员：__________ 日期：__________
- 测试人员：__________ 日期：__________
- 运维人员：__________ 日期：__________

---

## 联系支持

如遇到问题，请查看：
- API 文档：`GRAPH_API_README.md`
- 实现总结：`IMPLEMENTATION_SUMMARY.md`
- 测试脚本：`test_graph_api.py`

**常见问题**:
1. 图谱生成失败 → 检查组件 ID 和 iCenter 连接
2. 前端无法连接 → 检查 CORS 配置和端口
3. 性能问题 → 检查数据库索引和缓存策略

---

*文档版本：1.0*
*创建时间：2026-05-19*
