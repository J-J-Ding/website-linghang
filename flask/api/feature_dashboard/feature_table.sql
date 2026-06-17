-- ============================================================
-- 特性树度量看板 建表 SQL
-- 数据库: knowledge_engineering
-- ============================================================

-- 1. 特性树页面明细表
CREATE TABLE IF NOT EXISTS `know_feature_tree_page_table` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `page_title` VARCHAR(256) DEFAULT NULL COMMENT '页面标题',
  `field_name` VARCHAR(128) DEFAULT NULL COMMENT '领域名称（目录归属）',
  `feature_num` VARCHAR(128) DEFAULT NULL COMMENT '特性编号（如F010101或FS030110-01）',
  `feature_name` VARCHAR(256) DEFAULT NULL COMMENT '特性名称（如"业务波CDWSS波长选择"）',
  `page_type_name` VARCHAR(128) DEFAULT NULL COMMENT '页面类型名称（特性分析/特性方案/子特性分析/子特性方案）',
  `type_flag` VARCHAR(16) DEFAULT NULL COMMENT '业务标识（O/E/P/C/S）',
  `is_sub_feature` INT DEFAULT 0 COMMENT '是否子特性（0=否, 1=是）',
  `scheme_num` INT DEFAULT 0 COMMENT '关联特性方案数',
  `page_url` VARCHAR(512) DEFAULT NULL COMMENT '页面URL',
  `page_status` VARCHAR(128) DEFAULT NULL COMMENT '页面状态（初始/已初审/修订中/已定稿/空页面）',
  `page_person` VARCHAR(128) DEFAULT NULL COMMENT '页面负责人',
  `page_se` VARCHAR(128) DEFAULT NULL COMMENT 'SE',
  `page_tl` VARCHAR(128) DEFAULT NULL COMMENT 'TL',
  `page_tse` VARCHAR(128) DEFAULT NULL COMMENT 'TSE',
  `finish_flag` VARCHAR(128) DEFAULT NULL COMMENT '定稿标识',
  `update_by` VARCHAR(128) DEFAULT NULL COMMENT '更新人',
  `update_date` VARCHAR(128) DEFAULT NULL COMMENT '更新日期',
  `editor_num` INT DEFAULT NULL COMMENT '编辑人数',
  `edit_num` INT DEFAULT NULL COMMENT '编辑次数',
  `view_visitor_num` INT DEFAULT NULL COMMENT '浏览访客数',
  `view_visit_num` INT DEFAULT NULL COMMENT '浏览次数',
  `ai_adapt_num` DECIMAL(10,2) DEFAULT NULL COMMENT 'AI采纳数',
  `ai_gene_num` DECIMAL(10,2) DEFAULT NULL COMMENT 'AI生成数',
  `feature_engineering` JSON DEFAULT NULL COMMENT '特性工程信息（JSON）',
  `script_date` VARCHAR(128) DEFAULT NULL COMMENT '脚本采集日期',
  PRIMARY KEY (`id`),
  KEY `idx_script_date` (`script_date`),
  KEY `idx_field_name` (`field_name`),
  KEY `idx_feature_num` (`feature_num`),
  KEY `idx_page_type_name` (`page_type_name`),
  KEY `idx_field_script` (`field_name`, `script_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='特性树页面明细表';


-- 2. 特性树看板统计表
CREATE TABLE IF NOT EXISTS `know_feature_tree_board_table` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `date` VARCHAR(128) DEFAULT NULL COMMENT '统计日期',
  `field_name` VARCHAR(128) DEFAULT NULL COMMENT '领域名称（目录归属）',
  -- 特性分析维度
  `analysis_sum_num` INT DEFAULT NULL COMMENT '特性分析总数',
  `analysis_initial_num` INT DEFAULT NULL COMMENT '特性分析-初始数',
  `analysis_reviewed_num` INT DEFAULT NULL COMMENT '特性分析-已初审数',
  `analysis_revision_num` INT DEFAULT NULL COMMENT '特性分析-修订中数',
  `analysis_finish_num` INT DEFAULT NULL COMMENT '特性分析-已定稿数',
  `analysis_blank_num` INT DEFAULT NULL COMMENT '特性分析-空页面数',
  `analysis_sum_editor_num` INT DEFAULT NULL COMMENT '特性分析-编辑人数合计',
  `analysis_sum_edit_num` INT DEFAULT NULL COMMENT '特性分析-编辑次数合计',
  `analysis_sum_view_visitor_num` INT DEFAULT NULL COMMENT '特性分析-浏览访客数合计',
  `analysis_sum_view_visit_num` INT DEFAULT NULL COMMENT '特性分析-浏览次数合计',
  `analysis_sum_ai_adapt_num` DECIMAL(10,2) DEFAULT NULL COMMENT '特性分析-AI采纳数合计',
  `analysis_sum_ai_gene_num` DECIMAL(10,2) DEFAULT NULL COMMENT '特性分析-AI生成数合计',
  `analysis_change_detail` JSON DEFAULT NULL COMMENT '特性分析-变更详情（JSON）',
  -- 特性方案维度
  `scheme_sum_num` INT DEFAULT NULL COMMENT '特性方案总数',
  `scheme_initial_num` INT DEFAULT NULL COMMENT '特性方案-初始数',
  `scheme_reviewed_num` INT DEFAULT NULL COMMENT '特性方案-已初审数',
  `scheme_revision_num` INT DEFAULT NULL COMMENT '特性方案-修订中数',
  `scheme_finish_num` INT DEFAULT NULL COMMENT '特性方案-已定稿数',
  `scheme_blank_num` INT DEFAULT NULL COMMENT '特性方案-空页面数',
  `scheme_sum_editor_num` INT DEFAULT NULL COMMENT '特性方案-编辑人数合计',
  `scheme_sum_edit_num` INT DEFAULT NULL COMMENT '特性方案-编辑次数合计',
  `scheme_sum_view_visitor_num` INT DEFAULT NULL COMMENT '特性方案-浏览访客数合计',
  `scheme_sum_view_visit_num` INT DEFAULT NULL COMMENT '特性方案-浏览次数合计',
  `scheme_sum_ai_adapt_num` DECIMAL(10,2) DEFAULT NULL COMMENT '特性方案-AI采纳数合计',
  `scheme_sum_ai_gene_num` DECIMAL(10,2) DEFAULT NULL COMMENT '特性方案-AI生成数合计',
  `scheme_change_detail` JSON DEFAULT NULL COMMENT '特性方案-变更详情（JSON）',
  `update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_date` (`date`),
  KEY `idx_field_name` (`field_name`),
  KEY `idx_field_date` (`field_name`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='特性树看板统计表';
