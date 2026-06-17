# knowledge_component_graph_node 数据表创建指南

## 📋 表结构说明

**表名**: `knowledge_component_graph_node`  
**数据库**: `knowledge_engineering`  
**用途**: 存储图谱中每个节点的详细信息

---

## 🎯 字段定义

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 主键 ID |
| `graph_id` | INT UNSIGNED | NOT NULL, FK | 关联的图谱 ID（外键） |
| `node_id` | VARCHAR(128) | NOT NULL, UNIQUE | 节点唯一标识（前端用） |
| `node_type` | VARCHAR(32) | NOT NULL | 节点类型 |
| `node_name` | TEXT | NOT NULL | 节点名称（支持长文本，如完整章节标题） |
| `raw_data` | JSON | NULL | 原始数据（包含 url, space_id, content_id 等） |
| `parent_component_id` | VARCHAR(128) | NULL | 所属组件 ID（用于模块/章节/依赖节点） |
| `level` | INT | DEFAULT 1 | 节点层级（距离种子组件的度数） |
| `is_expanded` | TINYINT(1) | DEFAULT 0 | 是否已展开（用于懒加载） |
| `position_x` | DECIMAL(10, 2) | NULL | 布局 X 坐标（用户保存的布局） |
| `position_y` | DECIMAL(10, 2) | NULL | 布局 Y 坐标（用户保存的布局） |
| `create_time` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 🔑 索引设计

### 主键索引
```sql
PRIMARY KEY (`id`)
```

### 唯一索引
```sql
UNIQUE KEY `uk_graph_node` (`graph_id`, `node_id`)
```
确保同一个图谱中节点 ID 唯一

### 普通索引
```sql
KEY `idx_node_type` (`node_type`)
KEY `idx_parent_component` (`parent_component_id`)
```

### 复合索引（可选）
```sql
INDEX `idx_graph_type_level` (`graph_id`, `node_type`, `level`)
INDEX `idx_graph_parent` (`graph_id`, `parent_component_id`)
```

---

## 🔗 外键约束

```sql
CONSTRAINT `fk_graph_node` 
FOREIGN KEY (`graph_id`) 
REFERENCES `knowledge_component_graph` (`id`) 
ON DELETE CASCADE
```

**说明**: 当图谱被删除时，级联删除所有相关节点

---

## 📊 节点类型枚举

| 节点类型 | 说明 | 示例 |
|---------|------|------|
| `component` | 组件节点 | C-F023-PRTC 组件 |
| `module` | 模块节点 | M001-消息校验模块 |
| `section` | 章节节点 | 5.3.1 流程设计 |
| `dependent_component` | 依赖组件 | SC001-TAP 终端适配 |
| `affected_feature` | 波及特性 | F010604-管控与 WASON |
| `skill` | 知识技能（预留） | Python 编程 |

---

## 🚀 创建步骤

### 步骤 1: 确认前置条件

```sql
-- 1. 检查数据库是否存在
SELECT SCHEMA_NAME FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME = 'knowledge_engineering';

-- 2. 检查主表是否存在
SELECT TABLE_NAME FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'knowledge_engineering' 
  AND TABLE_NAME = 'knowledge_component_graph';
```

---

### 步骤 2: 执行创建脚本

**方式 A: 命令行执行**
```bash
mysql -u username -p -h host knowledge_engineering < create_graph_node_table.sql
```

**方式 B: MySQL 客户端**
```sql
SOURCE /path/to/create_graph_node_table.sql;
```

**方式 C: 手动执行**
```sql
USE knowledge_engineering;

CREATE TABLE IF NOT EXISTS `knowledge_component_graph_node` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `graph_id` INT UNSIGNED NOT NULL COMMENT '关联的图谱 ID',
  `node_id` VARCHAR(128) NOT NULL COMMENT '节点唯一标识（前端用）',
  `node_type` VARCHAR(32) NOT NULL COMMENT '节点类型',
  `node_name` TEXT NOT NULL COMMENT '节点名称（支持长文本，如完整章节标题）',
  `raw_data` JSON COMMENT '原始数据',
  `parent_component_id` VARCHAR(128) COMMENT '所属组件 ID',
  `level` INT DEFAULT 1 COMMENT '节点层级',
  `is_expanded` TINYINT(1) DEFAULT 0 COMMENT '是否已展开',
  `position_x` DECIMAL(10, 2) COMMENT '布局 X 坐标',
  `position_y` DECIMAL(10, 2) COMMENT '布局 Y 坐标',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  UNIQUE KEY `uk_graph_node` (`graph_id`, `node_id`),
  KEY `idx_node_type` (`node_type`),
  KEY `idx_parent_component` (`parent_component_id`),
  CONSTRAINT `fk_graph_node` FOREIGN KEY (`graph_id`) REFERENCES `knowledge_component_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件知识图谱节点明细表';
```

---

### 步骤 3: 验证创建结果

```sql
-- 1. 查看表结构
DESCRIBE knowledge_component_graph_node;

-- 2. 查看索引
SHOW INDEX FROM knowledge_component_graph_node;

-- 3. 查看表信息
SELECT 
  TABLE_NAME,
  TABLE_COMMENT,
  ENGINE,
  CHARSET,
  TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'knowledge_engineering' 
  AND TABLE_NAME = 'knowledge_component_graph_node';
```

---

## 📝 数据插入示例

### 示例 1: 插入组件节点

```sql
INSERT INTO knowledge_component_graph_node (
  graph_id, node_id, node_type, node_name, raw_data, level, is_expanded
) VALUES (
  1,
  'component_center1',
  'component',
  'C-F023-PRTC 组件设计',  -- TEXT 类型支持长文本
  '{
    "url": "https://i.zte.com.cn/space/xxx/wiki/page/yyy/view",
    "space_id": "xxx",
    "content_id": "yyy"
  }',
  0,
  1
);
```

---

### 示例 2: 插入模块节点

```sql
INSERT INTO knowledge_component_graph_node (
  graph_id, node_id, node_type, node_name, parent_component_id, level
) VALUES (
  1,
  'module_M001',
  'module',
  'M001-消息校验模块',
  'component_center1',
  1
);
```

---

### 示例 3: 插入章节节点

```sql
INSERT INTO knowledge_component_graph_node (
  graph_id, node_id, node_type, node_name, parent_component_id, level
) VALUES (
  1,
  'section_5.3.1',
  'section',
  '5.3.1 流程设计',
  'component_center1',
  1
);
```

---

### 示例 4: 插入依赖组件

```sql
INSERT INTO knowledge_component_graph_node (
  graph_id, node_id, node_type, node_name, level, raw_data
) VALUES (
  1,
  'dep_SC001',
  'dependent_component',
  'SC001-TAP 终端适配',
  1,
  '{
    "url": "https://i.zte.com.cn/space/zzz/wiki/page/www/view"
  }'
);
```

---

## 🔍 常用查询

### 查询 1: 获取图谱的所有节点

```sql
SELECT 
  node_id,
  node_type,
  node_name,
  level,
  is_expanded
FROM knowledge_component_graph_node
WHERE graph_id = 1
ORDER BY level, node_type, node_name;
```

---

### 查询 2: 按节点类型过滤

```sql
SELECT 
  node_id,
  node_name,
  level
FROM knowledge_component_graph_node
WHERE graph_id = 1
  AND node_type = 'component'
ORDER BY level;
```

---

### 查询 3: 获取特定组件的所有关联节点

```sql
SELECT 
  node_id,
  node_type,
  node_name,
  level
FROM knowledge_component_graph_node
WHERE graph_id = 1
  AND parent_component_id = 'component_center1'
ORDER BY node_type;
```

---

### 查询 4: 统计各类型节点数量

```sql
SELECT 
  node_type,
  COUNT(*) AS node_count
FROM knowledge_component_graph_node
WHERE graph_id = 1
GROUP BY node_type;
```

---

### 查询 5: 获取节点层级分布

```sql
SELECT 
  level,
  COUNT(*) AS node_count
FROM knowledge_component_graph_node
WHERE graph_id = 1
GROUP BY level
ORDER BY level;
```

---

## ⚠️ 注意事项

### 1. 外键依赖

必须先创建 `knowledge_component_graph` 表：
```sql
-- 先创建主表
SOURCE create_graph_table.sql;

-- 再创建节点表
SOURCE create_graph_node_table.sql;
```

---

### 2. 字符集设置

使用 `utf8mb4` 支持中文和 emoji：
```sql
DEFAULT CHARSET=utf8mb4
```

---

### 3. 引擎选择

使用 `InnoDB` 支持外键和事务：
```sql
ENGINE=InnoDB
```

---

### 4. JSON 字段

MySQL 5.7+ 支持 JSON 类型，可以存储结构化数据：
```sql
`raw_data` JSON COMMENT '原始数据'
```

---

### 5. 级联删除

外键设置 `ON DELETE CASCADE`，删除图谱时自动删除节点：
```sql
CONSTRAINT `fk_graph_node` 
FOREIGN KEY (`graph_id`) 
REFERENCES `knowledge_component_graph` (`id`) 
ON DELETE CASCADE
```

---

## 🔧 故障排查

### 问题 1: 外键约束失败

**错误**: `Cannot add foreign key constraint`

**原因**: 主表不存在或引擎不匹配

**解决**:
```sql
-- 1. 检查主表是否存在
SHOW TABLES LIKE 'knowledge_component_graph';

-- 2. 检查主表引擎
SHOW TABLE STATUS WHERE Name = 'knowledge_component_graph';

-- 3. 确保两个表都是 InnoDB 引擎
```

---

### 问题 2: 字符集不匹配

**错误**: `Illegal mix of collations`

**原因**: 数据库和表的字符集不一致

**解决**:
```sql
-- 修改数据库字符集
ALTER DATABASE knowledge_engineering CHARACTER SET utf8mb4;

-- 重新创建表
DROP TABLE IF EXISTS knowledge_component_graph_node;
SOURCE create_graph_node_table.sql;
```

---

### 问题 3: 唯一键冲突

**错误**: `Duplicate entry for key 'uk_graph_node'`

**原因**: 重复插入相同的 graph_id 和 node_id 组合

**解决**:
```sql
-- 使用 INSERT ... ON DUPLICATE KEY UPDATE
INSERT INTO knowledge_component_graph_node (...)
VALUES (...)
ON DUPLICATE KEY UPDATE node_name = VALUES(node_name);
```

---

## 📚 相关文档

- [graph_schema.sql](graph_schema.sql) - 完整数据库表结构
- [create_graph_node_table.sql](create_graph_node_table.sql) - 节点表创建脚本
- [BUGFIX_FIELD_NAMING.md](BUGFIX_FIELD_NAMING.md) - 字段命名规范
- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - API 测试指南

---

## ✅ 创建验证清单

- [ ] 数据库 `knowledge_engineering` 已存在
- [ ] 主表 `knowledge_component_graph` 已创建
- [ ] 执行 `create_graph_node_table.sql` 脚本
- [ ] 验证表结构（DESCRIBE）
- [ ] 验证索引（SHOW INDEX）
- [ ] 测试插入数据
- [ ] 测试查询数据
- [ ] 测试级联删除

---

**文档创建时间**: 2026-05-19  
**数据库**: knowledge_engineering  
**表名**: knowledge_component_graph_node  
**适用版本**: v1.0.0
