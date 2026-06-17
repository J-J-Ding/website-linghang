-- 数据库：wh_ai_db
-- 数据表：issue_impact_case_table
-- 只添加不存在的字段，避免重复添加报错
-- 注意：work_item_type 字段已存在，已跳过

USE wh_ai_db;

-- 只添加"指派给"字段（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'wh_ai_db' 
      AND TABLE_NAME = 'issue_impact_case_table' 
      AND COLUMN_NAME = 'assign_to'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `issue_impact_case_table` ADD COLUMN `assign_to` VARCHAR(64) NULL COMMENT ''指派给''',
    'SELECT ''字段 assign_to 已存在，跳过'' AS result'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 注意：work_item_type 字段已存在，跳过
-- SELECT '字段 work_item_type 已存在，跳过' AS result;

-- 只添加"案例发生时间"字段（如果不存在）
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'wh_ai_db' 
      AND TABLE_NAME = 'issue_impact_case_table' 
      AND COLUMN_NAME = 'case_occur_time'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `issue_impact_case_table` ADD COLUMN `case_occur_time` DATETIME NULL COMMENT ''案例发生时间''',
    'SELECT ''字段 case_occur_time 已存在，跳过'' AS result'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

