# 数据库检查指南 - knowledge_engineering

## 🎯 问题诊断

**错误信息**:
```
图谱生成失败：Component C-F023-PRTC 组件设计 not found in scope L1
```

**数据库**: `knowledge_engineering`  
**表名**: `knowledge_component_tree`

---

## 📝 执行 SQL 查询

### 步骤 1: 连接数据库

```bash
mysql -u username -p -h host knowledge_engineering
```

替换：
- `username`: 数据库用户名
- `host`: 数据库主机地址（如 localhost, 127.0.0.1, 或远程 IP）

---

### 步骤 2: 执行诊断 SQL

**复制并粘贴以下 SQL 到 MySQL 客户端**:

```sql
-- ============================================
-- 诊断查询 1: 检查特定组件
-- ============================================
SELECT 
    '=== 检查 C-F023-PRTC 组件设计 (L1) ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (node_id = 'C-F023-PRTC 组件设计' OR title = 'C-F023-PRTC 组件设计');

-- ============================================
-- 诊断查询 2: 模糊匹配 PRTC 相关组件
-- ============================================
SELECT 
    '=== 包含 PRTC 的所有组件 ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND title LIKE '%PRTC%'
ORDER BY scope, level, title
LIMIT 30;

-- ============================================
-- 诊断查询 3: 所有 Scope 统计
-- ============================================
SELECT 
    '=== 所有 Scope 统计 ===' AS info;

SELECT 
    scope,
    COUNT(*) AS total_count,
    SUM(CASE WHEN node_type = 'component' AND effective_flag = 'Y' THEN 1 ELSE 0 END) AS component_count
FROM knowledge_component_tree
GROUP BY scope
ORDER BY scope;

-- ============================================
-- 诊断查询 4: C-F023 相关组件
-- ============================================
SELECT 
    '=== C-F023 相关组件 ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title LIKE '%C-F023%' OR node_id LIKE '%C-F023%')
ORDER BY scope, level, title
LIMIT 30;

-- ============================================
-- 诊断查询 5: 检查不带"设计"的组件
-- ============================================
SELECT 
    '=== 检查 C-F023-PRTC 组件（不带设计） ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title = 'C-F023-PRTC 组件' OR title LIKE 'C-F023-PRTC%')
ORDER BY scope, level, title
LIMIT 20;
```

---

## 📊 分析查询结果

### 查询 1: 检查特定组件

**目标**: 检查 `C-F023-PRTC 组件设计` 在 L1 范围是否存在

**预期结果**:
- ✅ **有结果**: 组件存在，记录详细信息
- ❌ **无结果**: 组件不存在或 scope 不对

---

### 查询 2: 模糊匹配 PRTC

**目标**: 找到所有包含 "PRTC" 的组件

**重点关注**:
- `node_id`: 组件的真实 ID（用于 API 请求）
- `title`: 组件的准确名称
- `scope`: 组件所属的范围（L0/L1/L2/WASON/OSP）

---

### 查询 3: Scope 统计

**目标**: 查看每个 scope 有多少组件

**示例输出**:
```
scope | total_count | component_count
------|-------------|----------------
L0    | 500         | 200
L1    | 800         | 350
L2    | 600         | 280
```

---

### 查询 4: C-F023 相关组件

**目标**: 找到所有 C-F023 系列的组件

**可能的结果**:
- C-F023-PRTC 组件
- C-F023-PRTC 组件设计
- C-F023-PRTC 子组件
- C-F023-XXX 其他组件

---

### 查询 5: 精确匹配

**目标**: 检查不带"设计"的 `C-F023-PRTC 组件`

**如果这个查询有结果**，说明应该使用：
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1"
}
```

---

## 🎯 根据结果修正请求

### 情况 A: 组件存在，但 node_id 不同

**查询结果**:
```
node_id: a6fa84ef6e7511f080eaf9504434accd
title: C-F023-PRTC 组件设计
scope: L1
```

**修正后的请求**:
```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1",
  "maxDepth": 2
}
```

---

### 情况 B: 组件在其它 scope

**查询结果**:
```
node_id: xxx
title: C-F023-PRTC 组件设计
scope: L0  ← 不是 L1
```

**修正后的请求**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L0",
  "maxDepth": 2
}
```

---

### 情况 C: 组件名称不匹配

**查询结果**:
```
找到多个组件:
- C-F023-PRTC 组件 (scope: L1)
- C-F023-PRTC 组件设计 (scope: L0)
- C-F023-PRTC 子组件 (scope: L1)
```

**解决方案**: 选择正确的组件

**请求示例 1**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1",
  "maxDepth": 2
}
```

**请求示例 2**:
```json
{
  "seedComponentId": "C-F023-PRTC 子组件",
  "scope": "L1",
  "maxDepth": 2
}
```

---

### 情况 D: 数据库为空

**查询结果**:
```
Empty set
```

**可能原因**:
1. 数据库连接错误
2. 表不存在
3. 数据未导入

**检查步骤**:
```sql
-- 检查表是否存在
SHOW TABLES LIKE 'knowledge_component_tree';

-- 检查总记录数
SELECT COUNT(*) FROM knowledge_component_tree;
```

---

## 🔧 快速修复（推荐）

### 方法 1: 使用查询结果中的组件

从 SQL 查询结果中找一个存在的组件：

```json
{
  "seedComponentId": "从查询结果中复制 node_id 或 title",
  "scope": "从查询结果中复制 scope",
  "maxDepth": 2
}
```

### 方法 2: 尝试所有可能的名称

依次测试：

**测试 1**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L1"
}
```

**测试 2**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L1"
}
```

**测试 3**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L0"
}
```

**测试 4**:
```json
{
  "seedComponentId": "C-F023-PRTC 组件设计",
  "scope": "L0"
}
```

---

## 📞 需要帮助？

请提供以下信息：

1. **SQL 查询结果**（特别是查询 2 和 4）
2. **你尝试的请求参数**
3. **后端完整日志**

---

## 📚 相关文档

- [check_component_knowledge_engineering.sql](check_component_knowledge_engineering.sql) - 完整 SQL 脚本
- [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) - 快速修复指南
- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - Postman 使用指南

---

**创建时间**: 2026-05-19  
**数据库**: knowledge_engineering  
**表名**: knowledge_component_tree  
**适用版本**: v1.0.0
