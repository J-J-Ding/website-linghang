# 500 错误诊断指南 - Component not found

## 📋 错误信息

```json
{
    "code": 500,
    "status": "error",
    "message": "图谱生成失败：Component C-F023-PRTC 组件 not found in scope L1",
    "data": null
}
```

---

## 🔍 错误原因

后端在 `knowledge_component_tree` 表中查询不到符合条件的组件。

**查询条件**:
```sql
SELECT * FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (node_id = 'C-F023-PRTC 组件' OR title = 'C-F023-PRTC 组件')
```

**可能的原因**:
1. ❌ 组件 ID 或名称错误
2. ❌ scope 不匹配（组件在其他范围，如 L0/L2/WASON/OSP）
3. ❌ effective_flag 不是 'Y'（组件已失效）
4. ❌ 数据库中根本没有这个组件

---

## 🛠️ 诊断步骤

### 步骤 1: 查看后端调试日志

现在后端会打印详细的调试信息：

```
================================================================================
[DEBUG] 开始查询数据库...
  - 查询条件:
    * scope: 'L1'
    * effective_flag: 'Y'
    * seed_component_id: 'C-F023-PRTC 组件'
  - 查询方式：node_id='C-F023-PRTC 组件' OR title='C-F023-PRTC 组件'
================================================================================
================================================================================
[ERROR] 组件不存在，尝试诊断原因...
  - 查询的组件：'C-F023-PRTC 组件'
  - 查询的 scope: 'L1'
  - 可能的原因:
    1. 组件 ID 或名称错误
    2. scope 不匹配（组件在其他范围）
    3. effective_flag 不是 'Y'
    4. 数据库中没有这个组件
  - 建议：运行 check_component.py 脚本检查数据库
================================================================================
```

---

### 步骤 2: 运行诊断脚本

**方法 A: Python 脚本**

```bash
cd flask/api/componentTree

# 检查特定组件
python check_component.py 'C-F023-PRTC 组件' L1

# 显示所有 scope 的组件统计
python check_component.py
```

**方法 B: SQL 查询**

```bash
mysql -u username -p -h host db5 < check_component.sql
```

或者手动执行 SQL：

```sql
-- 1. 检查组件是否存在
SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type,
    url,
    space_id,
    effective_flag
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (node_id = 'C-F023-PRTC 组件' OR title = 'C-F023-PRTC 组件');

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

-- 3. 显示 L1 范围内的所有组件（前 50 个）
SELECT 
    node_id,
    title,
    level,
    parent_id,
    node_type
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND node_type = 'component'
ORDER BY title
LIMIT 50;
```

---

### 步骤 3: 分析诊断结果

#### 情况 A: 组件存在，但 node_id 不同

**输出示例**:
```
node_id: a6fa84ef6e7511f080eaf9504434accd
title: C-F023-PRTC 组件
scope: L1
```

**原因**: 应该使用 `node_id` 而不是 `title`

**解决**: 
```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1"
}
```

---

#### 情况 B: 组件在其它 scope

**输出示例**:
```
node_id: xxx
title: C-F023-PRTC 组件
scope: L0  ← 不是 L1
```

**原因**: scope 不匹配

**解决**: 使用正确的 scope
```json
{
  "seedComponentId": "C-F023-PRTC 组件",
  "scope": "L0"  ← 改为实际的 scope
}
```

---

#### 情况 C: 组件名称不完全匹配

**输出示例**:
```
找到 3 个相似的组件:
  - C-F023-PRTC 组件设计
  - C-F023-PRTC 组件 V2
  - C-F023-PRTC 子组件
```

**原因**: 组件名称不完全一致

**解决**: 使用准确的组件名称
```json
{
  "seedComponentId": "C-F023-PRTC 组件设计",  ← 使用准确的名称
  "scope": "L1"
}
```

---

#### 情况 D: 组件根本不存在

**输出示例**:
```
❌ 组件不存在！
L1 范围内没有组件
```

**原因**: 
- 数据库未初始化
- 组件树数据未导入
- 组件已被删除

**解决**: 
1. 检查数据库是否已初始化
2. 导入组件树数据
3. 确认组件是否有效（effective_flag='Y'）

---

## 🎯 常见解决方案

### 方案 1: 使用正确的 node_id

**问题**: 使用了 title 而不是 node_id

**解决**: 
1. 查询组件的 node_id:
   ```sql
   SELECT node_id, title FROM knowledge_component_tree
   WHERE title = 'C-F023-PRTC 组件' AND scope = 'L1';
   ```

2. 使用 node_id 请求:
   ```json
   {
     "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
     "scope": "L1"
   }
   ```

---

### 方案 2: 使用正确的 scope

**问题**: scope 不匹配

**解决**:
1. 查询组件的实际 scope:
   ```sql
   SELECT scope FROM knowledge_component_tree
   WHERE title = 'C-F023-PRTC 组件';
   ```

2. 使用正确的 scope 请求:
   ```json
   {
     "seedComponentId": "C-F023-PRTC 组件",
     "scope": "L0"  ← 实际的 scope
   }
   ```

---

### 方案 3: 检查 effective_flag

**问题**: 组件已失效（effective_flag != 'Y'）

**解决**:
```sql
-- 查看所有状态的组件
SELECT node_id, title, effective_flag, scope
FROM knowledge_component_tree
WHERE title LIKE '%PRTC%';

-- 如果确实是 Y，但查询不到，可能是缓存问题
-- 清理缓存后重试
```

---

### 方案 4: 数据库未初始化

**问题**: knowledge_component_tree 表为空

**解决**:
1. 检查表是否存在:
   ```sql
   SHOW TABLES LIKE 'knowledge_component_tree';
   ```

2. 检查数据量:
   ```sql
   SELECT COUNT(*) FROM knowledge_component_tree;
   ```

3. 如果为空，需要导入组件树数据

---

## 📊 诊断检查清单

- [ ] 运行 `python check_component.py 'C-F023-PRTC 组件' L1`
- [ ] 检查组件是否存在
- [ ] 检查组件的 node_id 和 title
- [ ] 检查组件的 scope
- [ ] 检查 effective_flag 是否为 'Y'
- [ ] 确认数据库中是否有组件数据
- [ ] 查看后端调试日志
- [ ] 尝试使用 node_id 而不是 title
- [ ] 尝试不同的 scope（L0/L2/WASON/OSP）

---

## 🔧 调试技巧

### 技巧 1: 列出所有组件

```bash
python check_component.py
```

显示所有 scope 下的组件统计，帮助找到正确的组件和 scope。

---

### 技巧 2: 模糊搜索

```sql
SELECT node_id, title, scope
FROM knowledge_component_tree
WHERE title LIKE '%PRTC%'
  AND effective_flag = 'Y';
```

找到所有包含 "PRTC" 的组件。

---

### 技巧 3: 检查组件树结构

```sql
SELECT 
    node_id,
    title,
    level,
    parent_id,
    node_type,
    scope
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
ORDER BY level, title
LIMIT 100;
```

查看组件树的层次结构。

---

## 📞 仍然有问题？

请提供以下信息：

1. **后端完整日志**（包括 DEBUG 信息）
2. **check_component.py 的输出**
3. **SQL 查询结果**
4. **你使用的请求参数**

---

## 📚 相关文档

- [check_component.py](check_component.py) - 组件检查脚本
- [check_component.sql](check_component.sql) - SQL 诊断脚本
- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - Postman 使用指南
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 部署检查清单

---

**文档创建时间**: 2026-05-19  
**适用版本**: v1.0.0  
**错误类型**: 500 - Component not found
