-- 组件树节点缓存表初始化脚本
-- 目标数据库: knowledge_engineering
-- 目标表: knowledge_component_tree

CREATE DATABASE IF NOT EXISTS `knowledge_engineering`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `knowledge_engineering`;

CREATE TABLE IF NOT EXISTS `knowledge_component_tree` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `scope` VARCHAR(32) NOT NULL COMMENT '树范围: L1/WASON',
  `node_id` VARCHAR(128) NOT NULL COMMENT '节点ID(业务唯一)',
  `parent_id` VARCHAR(128) DEFAULT NULL COMMENT '父节点ID',
  `level` TINYINT UNSIGNED NOT NULL COMMENT '树层级(1~4)',
  `node_type` VARCHAR(32) NOT NULL COMMENT '节点类型: domain/category/component/module',
  `title` VARCHAR(256) NOT NULL COMMENT '节点标题',
  `url` VARCHAR(1024) DEFAULT NULL COMMENT 'iCenter页面URL',
  `space_id` VARCHAR(64) DEFAULT NULL COMMENT 'iCenter空间ID',
  `sort_no` INT NOT NULL DEFAULT 0 COMMENT '排序号',
  `has_children` CHAR(1) NOT NULL DEFAULT 'N' COMMENT '是否有子节点(Y/N)',
  `effective_flag` VARCHAR(10) DEFAULT 'Y' COMMENT '生效标记(Y/N)',
  `sync_batch` VARCHAR(64) DEFAULT NULL COMMENT '同步批次号',
  `operator_person` VARCHAR(64) DEFAULT NULL COMMENT '操作人',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `node_payload` JSON DEFAULT NULL COMMENT '扩展信息(JSON)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_scope_node_effective` (`scope`, `node_id`, `effective_flag`),
  KEY `idx_scope_parent` (`scope`, `parent_id`, `effective_flag`, `sort_no`),
  KEY `idx_scope_level` (`scope`, `level`, `effective_flag`, `sort_no`),
  KEY `idx_scope_update_time` (`scope`, `update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组件树节点缓存表';
