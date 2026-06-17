-- 创建特性视图表（需求排期助手）
USE `requirement_automatic_schedule`;

CREATE TABLE IF NOT EXISTS `feature_view_table` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID（自增）',

    `feature_first_classification` VARCHAR(200) DEFAULT '' COMMENT '特性一级分类',
    `feature_second_classification` VARCHAR(200) DEFAULT '' COMMENT '特性二级分类',
    `feature_name` VARCHAR(300) DEFAULT '' COMMENT '特性',
    `sub_feature_name` VARCHAR(300) DEFAULT '' COMMENT '子特性',

    `feature_identifier` VARCHAR(100) DEFAULT '' COMMENT '特性标识',
    `domain` VARCHAR(100) DEFAULT '' COMMENT '领域',
    `team` VARCHAR(100) DEFAULT '' COMMENT '团队',
    `verification_mode` VARCHAR(100) DEFAULT '' COMMENT '验证方式',
    `verification_team` VARCHAR(100) DEFAULT '' COMMENT '验证团队',
    `priority` VARCHAR(50) DEFAULT '' COMMENT '优先级',

    `dev_workload` FLOAT DEFAULT NULL COMMENT '开发工作量（人天）',
    `detail_workload` FLOAT DEFAULT NULL COMMENT '详设工作量（人天）',
    `estimated_dev_workload` FLOAT DEFAULT NULL COMMENT '预计开发工作量',
    `estimated_verification_workload` FLOAT DEFAULT NULL COMMENT '预计验证工作量',
    `estimated_system_test_workload` FLOAT DEFAULT NULL COMMENT '预计系统测试工作量',

    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `operator_person` VARCHAR(50) DEFAULT NULL COMMENT '操作人',
    `effective_flag` VARCHAR(10) DEFAULT '1' COMMENT '有效标志（1-有效，0-无效）',

    PRIMARY KEY (`id`),
    INDEX `idx_domain` (`domain`),
    INDEX `idx_team` (`team`),
    INDEX `idx_effective_flag` (`effective_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='特性视图表';

