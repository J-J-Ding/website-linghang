-- =====================================================
-- 需求排期助手表字段添加脚本
-- 为已存在的 requirement_schedule_table 表添加筛选字段
-- =====================================================

USE `requirement_automatic_schedule`;

-- 检查并添加"所属产品"字段（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND COLUMN_NAME = 'belong_product'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD COLUMN `belong_product` VARCHAR(100) NULL COMMENT ''所属产品'' AFTER `plan_finish_system_test_date`',
    'SELECT ''字段 belong_product 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加"产品路标"字段（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND COLUMN_NAME = 'product_roadmap'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD COLUMN `product_roadmap` VARCHAR(100) NULL COMMENT ''产品路标'' AFTER `belong_product`',
    'SELECT ''字段 product_roadmap 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加"需求预规划"字段（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND COLUMN_NAME = 'requirement_preplanning'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD COLUMN `requirement_preplanning` VARCHAR(100) NULL COMMENT ''需求预规划'' AFTER `product_roadmap`',
    'SELECT ''字段 requirement_preplanning 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引（如果不存在）
-- 所属产品索引
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND INDEX_NAME = 'idx_belong_product'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD INDEX `idx_belong_product` (`belong_product`)',
    'SELECT ''索引 idx_belong_product 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 产品路标索引
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND INDEX_NAME = 'idx_product_roadmap'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD INDEX `idx_product_roadmap` (`product_roadmap`)',
    'SELECT ''索引 idx_product_roadmap 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 需求预规划索引
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule' 
    AND TABLE_NAME = 'requirement_schedule_table' 
    AND INDEX_NAME = 'idx_requirement_preplanning'
);

SET @sql = IF(@idx_exists = 0,
    'ALTER TABLE `requirement_schedule_table` ADD INDEX `idx_requirement_preplanning` (`requirement_preplanning`)',
    'SELECT ''索引 idx_requirement_preplanning 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================
-- 脚本执行完成
-- =====================================================
