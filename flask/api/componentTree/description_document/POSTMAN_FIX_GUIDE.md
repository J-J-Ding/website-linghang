# Postman 参数位置修复指南

## ❌ 问题诊断

你当前的配置：

```
URL: http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get?seedComponentId=C-F023-PRTC 组件&scope=L1
```

**后端日志**:
```
- 完整请求体：{}
- seedComponentId: 
- scope: 
```

**原因**: 参数放在了 **URL Query String** 中，但后端期望参数在 **HTTP Body** 中。

---

## ✅ 正确配置（3 步）

### 步骤 1: 清理 URL

**URL 栏只输入**:
```
http://10.239.69.183:3030/api/api_data/API_Knowledge_component_graph_get
```

⚠️ **不要带任何参数！**

**请求方法**: 选择 **POST**

---

### 步骤 2: 设置 Headers

点击 **Headers** 标签，确保有：

| Key | Value |
|-----|-------|
| Content-Type | application/json |

---

### 步骤 3: 设置 Body

1. 点击 **Body** 标签
2. 选择 **raw** 单选框
3. 右侧下拉框选择 **JSON**
4. 在文本框中输入：

```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": false,
  "operatorPerson": "测试用户"
}
```

---

## 📸 可视化说明

### 错误配置（当前）

```
┌─────────────────────────────────────────────────────────┐
│ POST                                                    │
│ http://10.239.69.183:3030/api/..._get?seedComponentId=… │
└─────────────────────────────────────────────────────────┘
Params   Authorization   Headers   Body   (空)
```

❌ **问题**: Body 是空的，参数在 URL 中

---

### 正确配置

```
┌─────────────────────────────────────────────────────────┐
│ POST                                                    │
│ http://10.239.69.183:3030/api/api_data/API_..._get      │
└─────────────────────────────────────────────────────────┘
Params   Authorization   Headers   Body ✅
                                    ┌──────────────────┐
                                    │ {                │
                                    │   "seedComponentId": "C-F023-PRTC 组件",
                                    │   "scope": "L1", │
                                    │   "maxDepth": 2  │
                                    │ }                │
                                    └──────────────────┘
```

✅ **正确**: 参数在 Body 中

---

## 🔍 参数位置对比

### URL Query String（❌ 错误）

```
?seedComponentId=C-F023-PRTC 组件&scope=L1
```

- 参数在 URL 中
- 后端无法读取
- 适用于 GET 请求
- **不适用于本 API**

---

### HTTP Body（✅ 正确）

```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1"
}
```

- 参数在 Body 中
- 后端可以读取
- 适用于 POST 请求
- **本 API 使用这种方式**

---

## 🎯 快速修复步骤

### 方法 1: 手动修复

1. 删除 URL 中的 `?seedComponentId=...&scope=L1`
2. 点击 **Body** 标签
3. 选择 **raw** + **JSON**
4. 粘贴 JSON 参数

---

### 方法 2: 使用 Postman 集合（推荐）

1. 点击 **Import**
2. 选择 `POSTMAN_COLLECTION.json`
3. 导入后直接点击 **"1. 获取组件知识图谱"**
4. 参数已经配置好，直接 **Send**

---

## 📋 检查清单

发送请求前，请确认：

- [ ] URL 后面**没有** `?` 和参数
- [ ] 请求方法是 **POST**
- [ ] Headers 中有 `Content-Type: application/json`
- [ ] Body 选择了 **raw** 格式
- [ ] Body 选择了 **JSON** 类型
- [ ] Body 中有 `seedComponentId` 和 `scope` 参数

---

## 🧪 验证方法

### 1. 查看 Postman Console

点击 Postman 底部的 **Console** 按钮，查看实际请求：

**正确的请求**:
```http
POST /api/api_data/API_Knowledge_component_graph_get HTTP/1.1
Host: 10.239.69.183:3030
Content-Type: application/json

{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1"
}
```

**错误的请求**:
```http
POST /api/api_data/API_Knowledge_component_graph_get?seedComponentId=...&scope=L1 HTTP/1.1
Host: 10.239.69.183:3030

(空 Body)
```

---

### 2. 查看后端日志

**正确的日志**:
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

**错误的日志**（你当前看到的）:
```
================================================================================
[API_Knowledge_component_graph_get] 接收到请求参数:
  - 完整请求体：{}
  - seedComponentId: 
  - scope: 
================================================================================
[ERROR] 缺少必填参数 - seedComponentId: '', scope: ''
```

---

## 💡 为什么这样设计？

### RESTful API 最佳实践

1. **GET 请求**: 参数放在 URL Query String
   - 用于查询数据
   - 参数可见、可缓存
   - 示例：`/api/users?id=123`

2. **POST 请求**: 参数放在 Body
   - 用于提交数据
   - 支持复杂结构（嵌套 JSON）
   - 无长度限制
   - 示例：`POST /api/users` + Body: `{"name":"张三"}`

---

### 本 API 使用 POST 的原因

1. **参数较多**: 5 个参数（seedComponentId, scope, maxDepth, forceRefresh, operatorPerson）
2. **可能需要复杂结构**: 未来可能支持嵌套参数
3. **安全性**: 参数不在 URL 中显示
4. **一致性**: 所有图谱 API 都使用 POST

---

## 📚 相关文档

- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - Postman 详细使用指南
- [POSTMAN_COLLECTION.json](POSTMAN_COLLECTION.json) - Postman 集合文件
- [TEST_METHODS_SUMMARY.md](TEST_METHODS_SUMMARY.md) - 所有测试方法总览

---

## 🆘 仍然有问题？

如果按照上述步骤仍然报错，请检查：

1. **后端服务是否启动**: 访问 `http://10.239.69.183:3030` 确认
2. **数据库表是否创建**: 执行 `graph_schema.sql`
3. **组件数据是否存在**: 查询 `knowledge_component_tree` 表
4. **网络是否通畅**: 使用 `ping 10.239.69.183` 测试

---

**文档创建时间**: 2026-05-19  
**适用版本**: v1.0.0  
**问题类型**: 参数位置错误（URL vs Body）
