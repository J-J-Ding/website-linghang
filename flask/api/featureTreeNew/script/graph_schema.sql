-- 组件知识图谱数据库表结构设计
-- 创建时间：2026-05-19
-- 说明：用于缓存组件知识图谱数据，支持懒加载和布局保存

-- ============================================================================
-- 1. knowledge_component_graph - 图谱缓存表
-- 说明：存储图谱整体信息，包括生成状态、缓存时间等
-- ============================================================================
CREATE TABLE IF NOT EXISTS `knowledge_component_graph` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `seed_component_id` VARCHAR(128) NOT NULL COMMENT '种子组件 ID',
  `seed_component_name` VARCHAR(256) NOT NULL COMMENT '种子组件名称',
  `scope` VARCHAR(32) NOT NULL COMMENT '所属范围（L0/L1/L2/WASON/OSP 等）',
  `max_depth` INT DEFAULT 2 COMMENT '最大展开深度',
  `status` VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '图谱状态：pending/generating/completed/failed/expired',
  `total_nodes` INT DEFAULT 0 COMMENT '节点总数',
  `total_edges` INT DEFAULT 0 COMMENT '边总数',
  `graph_data` JSON COMMENT '完整的图谱数据（nodes+edges）',
  `error_message` TEXT COMMENT '错误信息（当 status=failed 时）',
  `generated_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  `expires_at` DATETIME COMMENT '过期时间（默认 1 小时）',
  `refreshed_at` DATETIME COMMENT '刷新时间',
  `operator_person` VARCHAR(64) COMMENT '操作人',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  UNIQUE KEY `uk_seed_component` (`seed_component_id`, `max_depth`),
  KEY `idx_scope` (`scope`),
  KEY `idx_status` (`status`),
  KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件知识图谱缓存表';

-- ============================================================================
-- 2. knowledge_component_graph_node - 图谱节点明细表
-- 说明：存储图谱中每个节点的详细信息
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
-- 3. knowledge_component_graph_edge - 图谱边明细表
-- 说明：存储图谱中节点之间的关系
-- ============================================================================
CREATE TABLE IF NOT EXISTS `knowledge_component_graph_edge` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `graph_id` INT UNSIGNED NOT NULL COMMENT '关联的图谱 ID',
  `edge_id` VARCHAR(128) NOT NULL COMMENT '边唯一标识（前端用）',
  `source_node_id` VARCHAR(128) NOT NULL COMMENT '源节点 ID',
  `target_node_id` VARCHAR(128) NOT NULL COMMENT '目标节点 ID',
  `relation_type` VARCHAR(32) NOT NULL COMMENT '关系类型：belongs_to/contains/depends_on/affects/requires',
  `relation_label` VARCHAR(64) COMMENT '关系标注文字',
  `raw_data` JSON COMMENT '原始数据',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  UNIQUE KEY `uk_graph_edge` (`graph_id`, `edge_id`),
  KEY `idx_source` (`source_node_id`),
  KEY `idx_target` (`target_node_id`),
  KEY `idx_relation_type` (`relation_type`),
  CONSTRAINT `fk_graph_edge` FOREIGN KEY (`graph_id`) REFERENCES `knowledge_component_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件知识图谱边明细表';

-- ============================================================================
-- 4. knowledge_component_section - 组件章节信息表
-- 说明：缓存从 iCenter 页面解析的章节信息，避免重复解析
-- ============================================================================
CREATE TABLE IF NOT EXISTS `knowledge_component_section` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `component_id` VARCHAR(128) NOT NULL COMMENT '组件 ID',
  `component_url` VARCHAR(1024) NOT NULL COMMENT '组件 iCenter 页面 URL',
  `section_id` VARCHAR(128) NOT NULL COMMENT '章节唯一标识',
  `section_title` VARCHAR(256) NOT NULL COMMENT '章节标题',
  `section_type` VARCHAR(32) NOT NULL COMMENT '章节类型：5.3.1 流程设计/5.7.7FT 代码文件设计/4 组件对外接口',
  `section_content` TEXT COMMENT '章节内容摘要',
  `raw_html` TEXT COMMENT '原始 HTML 片段（可选）',
  `parsed_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '解析时间',
  `operator_person` VARCHAR(64) COMMENT '操作人',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  UNIQUE KEY `uk_component_section` (`component_id`, `section_id`),
  KEY `idx_component_url` (`component_url`(255)),
  KEY `idx_section_type` (`section_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件章节信息表';

-- ============================================================================
-- 5. knowledge_component_graph_layout - 图谱布局配置表
-- 说明：保存用户自定义的图谱布局和配置
-- ============================================================================
CREATE TABLE IF NOT EXISTS `knowledge_component_graph_layout` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
  `graph_id` INT UNSIGNED NOT NULL COMMENT '关联的图谱 ID',
  `layout_name` VARCHAR(128) NOT NULL COMMENT '布局名称',
  `layout_type` VARCHAR(32) DEFAULT 'custom' COMMENT '布局类型：custom/dagre/force/circular',
  `is_default` TINYINT(1) DEFAULT 0 COMMENT '是否为默认布局',
  `is_public` TINYINT(1) DEFAULT 0 COMMENT '是否公开（0=私有，1=公开）',
  `operator_person` VARCHAR(64) NOT NULL COMMENT '创建人',
  `node_positions` JSON COMMENT '节点位置数据 {node_id: {x, y}}',
  `viewport_config` JSON COMMENT '视口配置 {zoom, centerX, centerY}',
  `filter_config` JSON COMMENT '过滤配置 {node_types: [], relation_types: []}',
  `description` VARCHAR(512) COMMENT '布局描述',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  KEY `idx_graph_id` (`graph_id`),
  KEY `idx_operator` (`operator_person`),
  KEY `idx_is_default` (`is_default`),
  CONSTRAINT `fk_graph_layout` FOREIGN KEY (`graph_id`) REFERENCES `knowledge_component_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件知识图谱布局配置表';

-- ============================================================================
-- 初始化数据 - 插入示例布局配置
-- ============================================================================
-- 注意：实际数据由后端 API 动态插入，此处仅为参考

-- ============================================================================
-- 索引优化建议
-- ============================================================================
-- 1. knowledge_component_graph 表：
--    - 复合索引：(scope, status, expires_at) 用于查询有效图谱
--    - 复合索引：(seed_component_id, max_depth, status) 用于快速查找缓存
--
-- 2. knowledge_component_graph_node 表：
--    - 复合索引：(graph_id, node_type, level) 用于按类型过滤和分层查询
--    - 复合索引：(graph_id, parent_component_id) 用于查找组件的所有关联节点
--
-- 3. knowledge_component_graph_edge 表：
--    - 复合索引：(graph_id, source_node_id, relation_type) 用于查询节点的出边
--    - 复合索引：(graph_id, target_node_id) 用于查询节点的入边
--
-- 4. knowledge_component_section 表：
--    - 复合索引：(component_id, section_type) 用于快速查找特定类型的章节
--
-- 5. knowledge_component_graph_layout 表：
--    - 复合索引：(graph_id, operator_person, is_default) 用于获取用户的默认布局
