-- ============================================================================
-- 需求树知识图谱建表 SQL
-- 共 4 张表：graph / graph_node / graph_edge / graph_layout
-- 与组件树图谱的差异：去掉 section 表，新增 tree_node_id / source_type / effective_flag 字段
-- ============================================================================

-- 1. 图谱主表
CREATE TABLE IF NOT EXISTS `knowledge_requirement_graph` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT  COMMENT '主键 ID',
  `seed_requirement_node_id`    VARCHAR(128) NOT NULL                 COMMENT '种子需求节点 ID（关联 knowledge_requirement_tree.node_id）',
  `seed_requirement_name`       VARCHAR(512) NOT NULL                 COMMENT '种子需求名称（冗余，取 rdc_id | title）',
  `scope`                       VARCHAR(32)  NOT NULL                 COMMENT '作用域（智能OTN/M721/NTON）',
  `max_depth`                   INT          NOT NULL DEFAULT 2       COMMENT '最大展开深度',
  `status`                      VARCHAR(32)  NOT NULL DEFAULT 'pending' COMMENT '状态：pending/generating/completed/failed/expired',
  `total_nodes`                 INT          NOT NULL DEFAULT 0       COMMENT '节点总数',
  `total_edges`                 INT          NOT NULL DEFAULT 0       COMMENT '边总数',
  `graph_data`                  JSON         DEFAULT NULL             COMMENT '完整图谱数据快照',
  `error_message`               TEXT         DEFAULT NULL             COMMENT '错误信息',
  `generated_at`                DATETIME     DEFAULT NULL             COMMENT '生成时间',
  `expires_at`                  DATETIME     DEFAULT NULL             COMMENT '过期时间',
  `refreshed_at`                DATETIME     DEFAULT NULL             COMMENT '刷新时间',
  `operator_person`             VARCHAR(64)  DEFAULT NULL             COMMENT '操作人',
  `create_time`                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time`                 DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_seed_depth` (`seed_requirement_node_id`, `max_depth`),
  KEY `idx_scope` (`scope`),
  KEY `idx_status` (`status`),
  KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求树知识图谱缓存表';


-- 2. 图谱节点表
CREATE TABLE IF NOT EXISTS `knowledge_requirement_graph_node` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT  COMMENT '主键 ID',
  `graph_id`              INT UNSIGNED NOT NULL                 COMMENT '关联图谱 ID',
  `node_id`               VARCHAR(128) NOT NULL                 COMMENT '节点唯一标识',
  `node_type`             VARCHAR(32)  NOT NULL                 COMMENT '节点类型：market_requirement/requirement_instance/requirement_solution/component_design',
  `node_name`             TEXT         NOT NULL                 COMMENT '节点显示名称',
  `tree_node_id`          VARCHAR(128) DEFAULT NULL             COMMENT '关联树节点 ID（仅 market_requirement 有值）',
  `raw_data`              JSON         DEFAULT NULL             COMMENT '原始业务数据',
  `source_type`           VARCHAR(32)  NOT NULL DEFAULT 'auto'  COMMENT '数据来源：auto/manual/external',
  `level`                 INT          NOT NULL DEFAULT 1       COMMENT '距种子的度数（种子=0）',
  `is_expanded`           TINYINT(1)   NOT NULL DEFAULT 0       COMMENT '是否已展开',
  `position_x`            DECIMAL(10,2) DEFAULT NULL            COMMENT '布局 X 坐标',
  `position_y`            DECIMAL(10,2) DEFAULT NULL            COMMENT '布局 Y 坐标',
  `create_time`           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_graph_node` (`graph_id`, `node_id`),
  KEY `idx_node_type` (`node_type`),
  KEY `idx_tree_node_id` (`tree_node_id`),
  KEY `idx_source_type` (`source_type`),
  KEY `idx_graph_type_level` (`graph_id`, `node_type`, `level`),
  CONSTRAINT `fk_req_graph_node` FOREIGN KEY (`graph_id`)
    REFERENCES `knowledge_requirement_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求树知识图谱节点表';


-- 3. 图谱边表
CREATE TABLE IF NOT EXISTS `knowledge_requirement_graph_edge` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT  COMMENT '主键 ID',
  `graph_id`          INT UNSIGNED NOT NULL                 COMMENT '关联图谱 ID',
  `edge_id`           VARCHAR(128) NOT NULL                 COMMENT '边唯一标识',
  `source_node_id`    VARCHAR(128) NOT NULL                 COMMENT '源节点 ID',
  `target_node_id`    VARCHAR(128) NOT NULL                 COMMENT '目标节点 ID',
  `relation_type`     VARCHAR(32)  NOT NULL                 COMMENT '关系类型：contains/relates_to/affects',
  `relation_label`    VARCHAR(64)  DEFAULT NULL             COMMENT '关系标注：包含/关联/波及',
  `source_type`       VARCHAR(32)  NOT NULL DEFAULT 'auto'  COMMENT '数据来源：auto/manual/external',
  `raw_data`          JSON         DEFAULT NULL             COMMENT '原始数据',
  `effective_flag`    VARCHAR(10)  NOT NULL DEFAULT 'Y'     COMMENT '有效标记 Y/N（软删除）',
  `create_time`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_graph_edge` (`graph_id`, `edge_id`),
  KEY `idx_source` (`source_node_id`),
  KEY `idx_target` (`target_node_id`),
  KEY `idx_relation_type` (`relation_type`),
  KEY `idx_source_type` (`source_type`),
  KEY `idx_graph_source_type` (`graph_id`, `source_node_id`, `relation_type`),
  KEY `idx_graph_target` (`graph_id`, `target_node_id`),
  CONSTRAINT `fk_req_graph_edge` FOREIGN KEY (`graph_id`)
    REFERENCES `knowledge_requirement_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求树知识图谱边表';


-- 4. 图谱布局配置表
CREATE TABLE IF NOT EXISTS `knowledge_requirement_graph_layout` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT  COMMENT '主键 ID',
  `graph_id`          INT UNSIGNED NOT NULL                 COMMENT '关联图谱 ID',
  `layout_name`       VARCHAR(128) NOT NULL                 COMMENT '布局名称',
  `layout_type`       VARCHAR(32)  DEFAULT 'custom'         COMMENT 'custom/dagre/force/circular',
  `is_default`        INT          DEFAULT 0                COMMENT '是否为默认布局（0/1）',
  `is_public`         INT          DEFAULT 0                COMMENT '是否公开（0/1）',
  `operator_person`   VARCHAR(64)  NOT NULL                 COMMENT '创建人',
  `node_positions`    JSON         DEFAULT NULL             COMMENT '节点位置数据',
  `viewport_config`   JSON         DEFAULT NULL             COMMENT '视口配置',
  `filter_config`     JSON         DEFAULT NULL             COMMENT '过滤配置',
  `description`       VARCHAR(512) DEFAULT NULL             COMMENT '布局描述',
  `create_time`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_graph_id` (`graph_id`),
  KEY `idx_operator` (`operator_person`),
  CONSTRAINT `fk_req_graph_layout` FOREIGN KEY (`graph_id`)
    REFERENCES `knowledge_requirement_graph` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求树知识图谱布局配置表';
