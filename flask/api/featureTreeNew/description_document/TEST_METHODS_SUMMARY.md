# 组件知识图谱 API 测试方法总览

## 📋 目录

1. [Postman 测试](#postman-测试)
2. [命令行测试](#命令行测试)
3. [浏览器测试页面](#浏览器测试页面)
4. [浏览器控制台脚本](#浏览器控制台脚本)
5. [Vue 组件集成](#vue-组件集成)

---

## 🚀 Postman 测试（推荐）

### 快速开始

1. **导入 Postman 集合**
   - 文件：`POSTMAN_COLLECTION.json`
   - 操作：Postman → Import → 选择文件

2. **配置环境变量**
   ```
   base_url: http://10.239.69.183:3030
   api_path: /api/api_data
   ```

3. **发送请求**
   - 选择：`1. 获取组件知识图谱`
   - 点击 **Send**

### 请求配置

**URL**:
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

### 预期响应

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
    "nodes": [...],
    "edges": [...]
  }
}
```

### 详细文档

查看：[POSTMAN_GUIDE.md](POSTMAN_GUIDE.md)

---

## 💻 命令行测试

### 使用 Python 脚本

**运行默认测试**:
```bash
cd flask/api/componentTree
python test_graph_api_postman.py
```

**运行所有测试用例**:
```bash
python test_graph_api_postman.py --all
```

**检查 API 连通性**:
```bash
python test_graph_api_postman.py --check
```

**显示帮助**:
```bash
python test_graph_api_postman.py --help
```

### 使用 curl

```bash
curl -X POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get \
  -H "Content-Type: application/json" \
  -d '{
    "seedComponentId": "C-F023-PRTC 组件",
    "scope": "L1",
    "maxDepth": 2,
    "forceRefresh": false,
    "operatorPerson": "测试用户"
  }'
```

### 使用 httpie（推荐）

```bash
# 安装 httpie
pip install httpie

# 发送请求
http POST http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get \
  seedComponentId="C-F023-PRTC 组件" \
  scope="L1" \
  maxDepth=2 \
  forceRefresh=false \
  operatorPerson="测试用户"
```

---

## 🌐 浏览器测试页面

### 访问地址

```
http://localhost:3002/test-graph-api.html
```

或

```
http://10.239.69.183:3030/test-graph-api.html
```

### 功能特点

- ✅ 图形化界面
- ✅ 参数配置表单
- ✅ 实时统计信息
- ✅ 节点/边列表展示
- ✅ 错误提示

### 使用步骤

1. 启动前端服务：`npm run dev`
2. 打开测试页面
3. 填写参数
4. 点击"测试获取图谱"
5. 查看结果

---

## 🔧 浏览器控制台脚本

### 加载测试脚本

在浏览器控制台（F12）中运行：

```javascript
// 加载测试脚本
const script = document.createElement('script');
script.src = '/test-graph-quick.js';
document.head.appendChild(script);
```

### 测试命令

```javascript
// 单次测试
testGetGraph({
  seedComponentId: 'C-F023-PRTC 组件',
  scope: 'L1',
  maxDepth: 2
});

// 批量测试
runAllTests();

// 检查连通性
checkConnectivity();

// 显示帮助
showHelp();
```

### 文件位置

- `tdesign/public/test-graph-quick.js`

---

## 📦 Vue 组件集成

### 1. 导入 API 封装

```typescript
import { getComponentGraph } from '@/api/graph';
import type { GetGraphParams } from '@/api/graph';
```

### 2. 调用示例

```typescript
const params: GetGraphParams = {
  seedComponentId: 'C-F023-PRTC 组件',
  scope: 'L1',
  maxDepth: 2,
  forceRefresh: false,
  operatorPerson: '张三'
};

try {
  const response = await getComponentGraph(params);
  console.log('图谱数据:', response.data);
} catch (error) {
  console.error('获取图谱失败:', error);
}
```

### 3. 完整组件示例

查看：`tdesign/src/components/graph/ComponentGraph.example.vue`

---

## 📊 测试用例汇总

### 用例 1: 使用 title 查询

```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2
}
```

**预期**: ✅ 成功

---

### 用例 2: 使用 node_id 查询

```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1",
  "maxDepth": 2
}
```

**预期**: ✅ 成功

---

### 用例 3: 强制刷新

```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": true
}
```

**预期**: ✅ 重新生成

---

### 用例 4: 不同深度

```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 1
}
```

**预期**: ✅ 1 度关系

---

### 用例 5: 缺少参数

```json
{
  "scope": "L1"
}
```

**预期**: ❌ 400 错误

---

## ⚠️ 常见错误排查

### 错误 1: 405 Method Not Allowed

**原因**: 使用了 GET 方法

**解决**: 确保使用 **POST** 方法

---

### 错误 2: 400 缺少参数

**原因**: 
- Body 格式错误
- Content-Type 未设置
- 参数未序列化

**解决**:
1. Body 选择 **raw** 格式
2. 设置 `Content-Type: application/json`
3. 使用 `JSON.stringify()` 或等价的 JSON 序列化

---

### 错误 3: 500 组件不存在

**原因**: seedComponentId 不正确

**解决**: 检查组件 ID 或 title 是否存在

---

## 🔍 调试技巧

### 1. 查看后端日志

后端会打印详细参数：

```
================================================================================
[API_Knowledge_component_graph_get] 接收到请求参数:
  - 完整请求体：{"seedComponentId":"C-F023-PRTC 组件","scope":"L1","maxDepth":2}
  - seedComponentId: C-F023-PRTC 组件
  - scope: L1
  - maxDepth: 2
  - forceRefresh: false
  - operatorPerson: 测试用户
================================================================================
```

如果看到空对象 `{}`，说明参数未正确传递。

---

### 2. 查看网络面板

**浏览器**:
1. F12 打开开发者工具
2. Network 标签
3. 查看请求详情：
   - Request Method: POST
   - Request Payload: 参数

**Postman**:
- 点击 **Console** 查看实际请求

---

### 3. 使用测试工具验证

```bash
# Python 脚本
python test_graph_api_postman.py --check

# 浏览器控制台
checkConnectivity();
```

---

## 📚 相关文档

| 文档 | 描述 |
|------|------|
| [POSTMAN_COLLECTION.json](POSTMAN_COLLECTION.json) | Postman 集合文件 |
| [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) | Postman 详细使用指南 |
| [test_graph_api_postman.py](test_graph_api_postman.py) | Python 命令行测试脚本 |
| [GRAPH_API_README.md](GRAPH_API_README.md) | API 接口详细文档 |
| [GRAPH_API_USAGE.md](GRAPH_API_USAGE.md) | 使用说明 |
| [DEBUG_PRINT_GUIDE.md](DEBUG_PRINT_GUIDE.md) | 调试打印指南 |
| [GRAPH_QUICK_START.md](../tdesign/public/GRAPH_QUICK_START.md) | 快速开始指南 |

---

## 🎯 推荐测试流程

### 方案 A: Postman（推荐新手）

1. 导入 `POSTMAN_COLLECTION.json`
2. 配置环境变量
3. 发送请求
4. 查看响应

**优点**: 图形界面，简单易用

---

### 方案 B: 命令行（推荐开发）

1. 运行 `python test_graph_api_postman.py`
2. 查看输出结果
3. 分析日志

**优点**: 快速，可批量测试

---

### 方案 C: 浏览器（推荐前端集成）

1. 打开 `test-graph-api.html`
2. 填写参数并测试
3. 查看结果

**优点**: 接近真实使用场景

---

## ✅ 测试检查清单

测试前请确认：

- [ ] 后端服务已启动（端口 3030）
- [ ] 数据库表已创建（graph_schema.sql）
- [ ] 组件数据存在（knowledge_component_tree 表）
- [ ] 请求方法为 POST
- [ ] Content-Type 为 application/json
- [ ] 参数在 Body 中（不在 URL）
- [ ] 参数已序列化为 JSON

---

**文档创建时间**: 2026-05-19  
**适用版本**: v1.0.0  
**维护者**: AI Assistant
