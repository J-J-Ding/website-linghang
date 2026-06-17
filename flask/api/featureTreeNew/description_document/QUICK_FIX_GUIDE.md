# 快速修复指南 - 组件不存在问题

## 🎯 当前问题

后端报错：
```
图谱生成失败：Component C-F023-PRTC 组件设计 not found in scope L1
```

---

## 🔍 诊断步骤

### 步骤 1: 执行 SQL 查询

**连接数据库**:
```bash
mysql -u username -p -h host db5
```

**执行查询**（复制粘贴以下 SQL）:

```sql
-- 1. 检查 'C-F023-PRTC 组件设计' 是否存在
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (node_id = 'C-F023-PRTC 组件设计' OR title = 'C-F023-PRTC 组件设计');

-- 2. 模糊匹配包含 'PRTC' 的组件
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND title LIKE '%PRTC%'
LIMIT 20;

-- 3. 所有 Scope 统计
SELECT 
    scope,
    COUNT(*) AS total_count
FROM knowledge_component_tree
GROUP BY scope
ORDER BY scope;

-- 4. 包含 'C-F023' 的所有组件
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title LIKE '%C-F023%' OR node_id LIKE '%C-F023%')
LIMIT 20;
```

---

## 📊 可能的结果与解决方案

### 结果 A: 组件存在，但 node_id 不同

**SQL 输出示例**:
```
node_id: a6fa84ef6e7511f080eaf9504434accd
title: C-F023-PRTC 组件设计
scope: L1
```

**解决方案**: 使用 node_id 而不是 title

**Postman 请求**:
```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1",
  "maxDepth": 2
}
```

---

### 结果 B: 组件在其它 scope

**SQL 输出示例**:
```
node_id: xxx
title: C-F023-PRTC 组件设计
scope: L0  ← 不是 L1
```

**解决方案**: 使用正确的 scope

**Postman 请求**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L0"  ← 改为实际的 scope
}
```

---

### 结果 C: 组件名称不完全匹配

**SQL 输出示例**:
```
找到多个包含 PRTC 的组件:
- C-F023-PRTC 组件
- C-F023-PRTC 组件设计
- C-F023-PRTC 子组件
```

**解决方案**: 使用准确的组件名称

**Postman 请求**（选择其中一个）:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",  ← 不带"设计"
  "scope": "L1"
}
```

---

### 结果 D: 数据库为空

**SQL 输出示例**:
```
Empty set
```

**原因**: 
- 数据库未初始化
- 组件树数据未导入
- 表不存在

**解决方案**:
1. 检查数据库连接
2. 确认表已创建：`SHOW TABLES LIKE 'knowledge_component_tree';`
3. 导入组件树数据

---

## 🎯 快速测试（推荐）

### 方法 1: 使用已有的组件

从 SQL 查询结果中找一个存在的组件：

```json
{
  "seedComponentId": "找到的组件 ID 或名称",
  "scope": "L1",
  "maxDepth": 2
}
```

### 方法 2: 遍历所有 Scope

尝试不同的 scope：

```json
// 测试 L0
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L0"
}

// 测试 L2
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L2"
}

// 测试 WASON
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "WASON"
}
```

---

## 📝 调试技巧

### 技巧 1: 列出所有组件

```sql
SELECT 
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND node_type = 'component'
ORDER BY scope, title
LIMIT 100;
```

---

### 技巧 2: 检查组件树结构

```sql
SELECT 
    node_id,
    title,
    level,
    parent_id,
    node_type,
    scope
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
ORDER BY scope, level, title
LIMIT 200;
```

---

### 技巧 3: 统计信息

```sql
SELECT 
    scope,
    node_type,
    COUNT(*) AS count
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
GROUP BY scope, node_type;
```

---

## ✅ 验证

执行 SQL 查询后，你应该能够：

1. ✅ 找到正确的组件 ID（node_id）
2. ✅ 确定组件所在的 scope
3. ✅ 确认组件是否有效（effective_flag='Y'）

然后用正确的参数请求 API：

```json
{
  "seedComponentId": "正确的 ID 或名称",
  "scope": "正确的范围",
  "maxDepth": 2
}
```

---

## 📞 需要帮助？

请提供：
1. SQL 查询结果
2. 你使用的请求参数
3. 后端完整日志

---

**创建时间**: 2026-05-19  
**适用版本**: v1.0.0  
**问题类型**: 500 - Component not found
