-- 创建版本视图表
USE `requirement_automatic_schedule`;

-- 创建版本表
CREATE TABLE IF NOT EXISTS `version_table` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID（自增）',
    `belong_product` VARCHAR(100) NOT NULL COMMENT '所属产品',
    `product_roadmap` VARCHAR(100) NOT NULL COMMENT '所属项目',
    `requirement_preplanning` VARCHAR(100) NOT NULL COMMENT '需求预规划',
    `start_dev_date` VARCHAR(20) DEFAULT NULL COMMENT '启动开发日期（YYYY-MM-DD）',
    `finish_dev_date` VARCHAR(20) DEFAULT NULL COMMENT '完成开发日期（YYYY-MM-DD）',
    `achievement_appraisal_date` VARCHAR(20) DEFAULT NULL COMMENT '成果鉴定日期（YYYY-MM-DD）',
    `cycle_days` INT DEFAULT NULL COMMENT '周期（天）',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `operator_person` VARCHAR(50) DEFAULT NULL COMMENT '操作人',
    `effective_flag` VARCHAR(10) DEFAULT '1' COMMENT '有效标志（1-有效，0-无效）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_belong_product_product_roadmap_requirement_preplanning` (`belong_product`, `product_roadmap`, `requirement_preplanning`),
    INDEX `idx_belong_product` (`belong_product`),
    INDEX `idx_product_roadmap` (`product_roadmap`),
    INDEX `idx_requirement_preplanning` (`requirement_preplanning`),
    INDEX `idx_effective_flag` (`effective_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='版本视图表';
