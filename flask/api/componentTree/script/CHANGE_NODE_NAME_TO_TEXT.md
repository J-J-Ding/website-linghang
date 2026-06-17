# node_name 字段类型变更说明

## 📋 变更概述

将 `knowledge_component_graph_node` 表的 `node_name` 字段从 `VARCHAR(256)` 改为 `TEXT` 类型，以支持存储完整的章节标题，避免内容截断。

## 🎯 变更原因

**问题**: 
```
ERROR: (pymysql.err.DataError) (1406, "Data too long for column 'node_name' at row 1")
```

**原因**: 
- 章节标题可能超过 256 字符（如 "5.7.7 FT 代码文件设计 - 详细流程说明"）
- `VARCHAR(256)` 限制了最大长度
- 需要支持更长的章节标题

**解决方案**: 
- 将字段类型改为 `TEXT`
- `TEXT` 类型最大支持 65,535 字节（约 64KB）
- 足够存储完整的章节标题

---

## 📁 已修改的文件

### 1. 数据库变更

#### ✅ 变更脚本（已存在）
**文件**: `alter_node_name_to_text.sql`
```sql
ALTER TABLE `knowledge_component_graph_node` 
MODIFY COLUMN `node_name` TEXT NOT NULL COMMENT '节点名称（支持长文本，如完整章节标题）';
```

#### ✅ 创建脚本（已更新）
**文件**: `create_graph_node_table.sql`
```sql
`node_name` TEXT NOT NULL COMMENT '节点名称（支持长文本，如完整章节标题）',
```

#### ✅ Schema 文档（已更新）
**文件**: `graph_schema.sql`
```sql
`node_name` TEXT NOT NULL COMMENT '节点名称（支持长文本，如完整章节标题）',
```

### 2. Python 模型（已更新）

**文件**: `data_model.py`
```python
node_name = Column(Text, nullable=False)  # 节点名称（支持长文本，如完整章节标题）
```

### 3. 文档（已更新）

**文件**: `description_document/GRAPH_NODE_TABLE_GUIDE.md`
- 字段定义表格：`TEXT` 类型
- 示例代码：`TEXT` 类型
- 注释说明：支持长文本

---

## 🚀 部署步骤

### 步骤 1: 执行数据库变更脚本

```bash
# 方式 1: 命令行执行
mysql -u username -p -h host knowledge_engineering < alter_node_name_to_text.sql

# 方式 2: MySQL 客户端
mysql> USE knowledge_engineering;
mysql> SOURCE /path/to/alter_node_name_to_text.sql;
```

### 步骤 2: 验证修改结果

```sql
-- 查看表结构
DESC knowledge_component_graph_node;

-- 查看字段类型
SHOW COLUMNS FROM knowledge_component_graph_node LIKE 'node_name';

-- 预期结果：
-- Field: node_name
-- Type: text
-- Null: NO
-- Key: 
-- Default: NULL
```

### 步骤 3: 重启 Flask 应用

```bash
# 重启后端服务
cd flask/api
gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 app:app
```

### 步骤 4: 测试验证

```bash
# 测试 API，确保不再出现 "Data too long" 错误
curl -X POST http://localhost:3001/api/component-tree/generate-graph \
  -H "Content-Type: application/json" \
  -d '{"componentId": "xxx", "maxDepth": 2}'
```

---

## 📊 字段类型对比

| 特性 | VARCHAR(256) | TEXT |
|------|-------------|------|
| 最大长度 | 256 字符 | 65,535 字节（64KB） |
| 存储方式 | 行内存储 | 行外存储（指针 + 数据） |
| 索引支持 | 可直接索引 | 需指定前缀长度 |
| 性能 | 较快 | 略慢（但可接受） |
| 适用场景 | 短文本 | 长文本、文章内容 |

---

## ⚠️ 注意事项

### 1. 索引影响

`TEXT` 类型不能直接创建索引，如需索引需指定前缀长度：

```sql
-- ❌ 错误
CREATE INDEX idx_node_name ON knowledge_component_graph_node(node_name);

-- ✅ 正确（索引前 255 字符）
CREATE INDEX idx_node_name ON knowledge_component_graph_node(node_name(255));
```

**当前表结构**: 没有对 `node_name` 创建索引，无需额外操作。

### 2. 查询性能

`TEXT` 类型查询可能略慢于 `VARCHAR`，但影响可接受：
- 章节标题查询通常带 `graph_id` 过滤（已有索引）
- 查询量不大，性能影响可忽略

### 3. 数据迁移

如果表中已有数据，`ALTER TABLE` 会自动转换：
- `VARCHAR(256)` → `TEXT`: 无损转换
- 无需手动迁移数据

### 4. 应用兼容性

SQLAlchemy 的 `Text` 类型与 MySQL 的 `TEXT` 类型完全兼容：
- ✅ 读取：自动映射
- ✅ 写入：自动转换
- ✅ 查询：无需修改

---

## 🔍 测试用例

### 测试 1: 插入长标题

```sql
-- 插入超过 256 字符的章节标题
INSERT INTO knowledge_component_graph_node (
  graph_id, node_id, node_type, node_name, level
) VALUES (
  1,
  'section_test',
  'section',
  '5.7.7 FT 代码文件设计 - 非常长的章节标题用于测试 TEXT 类型是否支持超过 256 字符的内容...' || REPEAT('测试内容', 50),
  1
);

-- 应该成功插入
```

### 测试 2: 查询长标题

```sql
SELECT node_id, node_name, LENGTH(node_name) AS name_length
FROM knowledge_component_graph_node
WHERE node_type = 'section'
ORDER BY LENGTH(node_name) DESC
LIMIT 10;
```

### 测试 3: API 测试

```bash
# 生成包含长章节标题的图谱
POST /api/component-tree/generate-graph
{
  "componentId": "C-F023-PRTC",
  "maxDepth": 2
}

# 预期结果：
# ✅ 不再出现 "Data too long" 错误
# ✅ 图谱正常生成并缓存
```

---

## 📝 回滚方案

如果需要回滚到 `VARCHAR(256)`:

```sql
-- 回滚字段类型
ALTER TABLE `knowledge_component_graph_node` 
MODIFY COLUMN `node_name` VARCHAR(256) NOT NULL COMMENT '节点名称';

-- 注意：如果已有数据超过 256 字符，会被截断！
-- 建议先备份数据
CREATE TABLE knowledge_component_graph_node_backup AS 
SELECT * FROM knowledge_component_graph_node;
```

---

## ✅ 验证清单

- [x] 数据库表结构已修改
- [x] Python 数据模型已更新
- [x] 文档已更新
- [ ] 执行数据库变更脚本
- [ ] 验证表结构
- [ ] 测试插入长标题
- [ ] 测试 API 功能
- [ ] 重启 Flask 应用
- [ ] 生产环境部署

---

## 📚 相关文档

- [alter_node_name_to_text.sql](alter_node_name_to_text.sql) - 数据库变更脚本
- [create_graph_node_table.sql](create_graph_node_table.sql) - 表创建脚本
- [graph_schema.sql](graph_schema.sql) - 完整表结构
- [GRAPH_NODE_TABLE_GUIDE.md](description_document/GRAPH_NODE_TABLE_GUIDE.md) - 使用指南

---

**变更时间**: 2026-05-21  
**影响范围**: knowledge_component_graph_node 表  
**向后兼容**: ✅ 是（TEXT 兼容 VARCHAR）  
**需要重启**: ✅ 是（Flask 应用）
