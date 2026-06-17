-- 创建故障波及版本表
CREATE TABLE IF NOT EXISTS `issue_impact_version_table` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `version_id` VARCHAR(64) NOT NULL COMMENT '版本ID',
  `version_name` VARCHAR(128) NOT NULL COMMENT '版本名称',
  `belong_project` VARCHAR(128) DEFAULT NULL COMMENT '归属项目',
  `release_time` DATE DEFAULT NULL COMMENT '发布时间',
  `historical_release_time` DATE NOT NULL COMMENT '历史版本发布时间',
  `target_network` VARCHAR(512) DEFAULT NULL COMMENT '目标网络（逗号分隔）',
  `involved_boards` VARCHAR(512) DEFAULT NULL COMMENT '涉及单板（逗号分隔）',
  `branch` VARCHAR(128) NOT NULL COMMENT '版本分支',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` VARCHAR(64) DEFAULT NULL COMMENT '创建人',
  `update_by` VARCHAR(64) DEFAULT NULL COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_version_id` (`version_id`),
  UNIQUE KEY `uk_version_name` (`version_name`),
  KEY `idx_release_time` (`release_time`),
  KEY `idx_historical_release_time` (`historical_release_time`),
  KEY `idx_branch` (`branch`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='故障波及版本表';

-- 创建故障波及版本案例关联表
CREATE TABLE IF NOT EXISTS `issue_impact_version_case_relation_table` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `version_id` VARCHAR(64) NOT NULL COMMENT '版本ID',
  `case_id` VARCHAR(64) NOT NULL COMMENT '案例ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_version_case` (`version_id`, `case_id`),
  KEY `idx_version_id` (`version_id`),
  KEY `idx_case_id` (`case_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='故障波及版本案例关联表';
