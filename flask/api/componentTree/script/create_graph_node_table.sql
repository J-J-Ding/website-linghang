-- ============================================================================
-- knowledge_component_graph_node 数据表创建脚本
-- 数据库：knowledge_engineering
-- 表名：knowledge_component_graph_node
-- 用途：存储图谱中每个节点的详细信息
-- 创建时间：2026-05-19
-- ============================================================================

-- 选择数据库
USE knowledge_engineering;

-- ============================================================================
-- 1. 创建 knowledge_component_graph_node 表
-- ============================================================================
CREATE TABLE IF NOT EXISTS `knowledge_component_graph_node` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `graph_id` INT UNSIGNED NOT NULL COMMENT '关联的图谱 ID',
  `node_id` VARCHAR(128) NOT NULL COMMENT '节点唯一标识（前端用）',
  `node_type` VARCHAR(32) NOT NULL COMMENT '节点类型：component/module/section/dependent_component/affected_feature/skill',
  `node_name` TEXT NOT NULL COMMENT '节点名称（支持长文本，如完整章节标题）',
  `raw_data` JSON COMMENT '原始数据（包含 url, space_id, content_id 等）',
  `parent_component_id` VARCHAR(128) COMMENT '所属组件 ID（用于模块/章节/依赖节点）',
  `level` INT DEFAULT 1 COMMENT '节点层级（距离种子组件的度数）',
  `is_expanded` TINYINT(1) DEFAULT 0 COMMENT '是否已展开（用于懒加载）',
  `position_x` DECIMAL(10, 2) COMMENT '布局 X 坐标（用户保存的布局）',
  `position_y` DECIMAL(10, 2) COMMENT '布局 Y 坐标（用户保存的布局）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  UNIQUE KEY `uk_graph_node` (`graph_id`, `node_id`),
  KEY `idx_node_type` (`node_type`),
  KEY `idx_parent_component` (`parent_component_id`),
  CONSTRAINT `fk_graph_node` FOREIGN KEY (`graph_id`) REFERENCES `knowledge_component_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件知识图谱节点明细表';

-- ============================================================================
-- 2. 创建索引（可选，提升查询性能）
-- ============================================================================

-- 复合索引：按图 ID、节点类型和层级查询
CREATE INDEX IF NOT EXISTS `idx_graph_type_level` 
ON `knowledge_component_graph_node` (`graph_id`, `node_type`, `level`);

-- 复合索引：按图 ID 和所属组件 ID 查询
CREATE INDEX IF NOT EXISTS `idx_graph_parent` 
ON `knowledge_component_graph_node` (`graph_id`, `parent_component_id`);

-- ============================================================================
-- 3. 验证表创建
-- ============================================================================
SELECT 
  'knowledge_component_graph_node table created successfully' AS status,
  TABLE_NAME,
  TABLE_COMMENT,
  ENGINE,
  CHARSET
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'knowledge_engineering' 
  AND TABLE_NAME = 'knowledge_component_graph_node';

-- ============================================================================
-- 4. 查看表结构
-- ============================================================================
DESCRIBE knowledge_component_graph_node;

-- ============================================================================
-- 5. 查看索引信息
-- ============================================================================
SHOW INDEX FROM knowledge_component_graph_node;

-- ============================================================================
-- 使用说明
-- ============================================================================
-- 
-- 执行方式 1: 命令行执行
-- mysql -u username -p -h host knowledge_engineering < create_graph_node_table.sql
--
-- 执行方式 2: MySQL 客户端
-- mysql> source /path/to/create_graph_node_table.sql;
--
-- 执行方式 3: 直接复制 SQL 到 MySQL Workbench 或其他 GUI 工具
--
-- 注意事项:
-- 1. 必须先创建 knowledge_component_graph 表（外键依赖）
-- 2. 确保数据库 knowledge_engineering 已存在
-- 3. 确保有创建表的权限
-- 4. 字符集使用 utf8mb4（支持中文和 emoji）
-- 5. 引擎使用 InnoDB（支持外键和事务）
--
-- ============================================================================
