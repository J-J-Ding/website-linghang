-- 创建团队映射表和需求开发投入人力设置表
USE `requirement_automatic_schedule`;

-- 1. 创建团队映射表（person_skill_map.team 到 requirement_dev_human_resource.team 的映射）
CREATE TABLE IF NOT EXISTS `team_mapping` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID（自增）',
    `source_team` VARCHAR(50) NOT NULL COMMENT '源团队名称（person_skill_map.team）',
    `target_team` VARCHAR(50) NOT NULL COMMENT '目标团队名称（requirement_dev_human_resource.team）',
    `team_type` VARCHAR(30) NOT NULL COMMENT '团队类型（requirement_dev_human_resource.team_type）',
    `domain` VARCHAR(50) DEFAULT NULL COMMENT '领域（可选，用于区分同一团队名称在不同领域的映射）',
    PRIMARY KEY (`id`),
    INDEX `idx_source_team` (`source_team`),
    INDEX `idx_target_team` (`target_team`),
    INDEX `idx_domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='团队映射表';

-- 2. 创建需求开发投入人力设置表
CREATE TABLE IF NOT EXISTS `requirement_dev_human_resource` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID（自增）',
    `department` VARCHAR(50) DEFAULT '' COMMENT '部门',
    `domain` VARCHAR(50) NOT NULL COMMENT '领域（如01-LO光系统）',
    `team` VARCHAR(50) NOT NULL COMMENT '团队（如LO-管理团队）',
    `team_type` VARCHAR(30) NOT NULL COMMENT '团队类型（如管理团队、开发团队）',
    `skill_category` VARCHAR(100) DEFAULT '' COMMENT '技能/特性分类',
    `year_month` VARCHAR(7) NOT NULL COMMENT '年月（格式如 "2026-01"）',
    `demand_human_power_ratio` DECIMAL(3, 2) NOT NULL DEFAULT 1.00 COMMENT '需求人力占比（范围0~1，2位小数，默认值1.00）',
    `zxone_19700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE 19700（范围0~1，2位小数，默认值0.00）',
    `zxone_9700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE 9700（范围0~1，2位小数，默认值0.00）',
    `zxmp_m721` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXMP M21（范围0~1，2位小数，默认值0.00）',
    `zxone_nton` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE NTON（范围0~1，2位小数，默认值0.00）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_year_month_domain_team_team_type_skill_category` (`year_month`, `domain`, `team`, `team_type`, `skill_category`),
    INDEX `idx_department` (`department`),
    INDEX `idx_domain` (`domain`),
    INDEX `idx_team` (`team`),
    INDEX `idx_year_month` (`year_month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='需求开发投入人力设置表';
