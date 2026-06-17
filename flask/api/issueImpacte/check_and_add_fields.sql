-- 数据库：wh_ai_db
-- 数据表：issue_impact_case_table
-- 先检查字段是否存在，然后只添加不存在的字段

USE wh_ai_db;

-- 检查字段是否存在，如果不存在则添加
-- 1. 检查并添加"指派给"字段
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

-- 2. 检查并添加"工作项类型"字段
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'wh_ai_db' 
      AND TABLE_NAME = 'issue_impact_case_table' 
      AND COLUMN_NAME = 'work_item_type'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE `issue_impact_case_table` ADD COLUMN `work_item_type` VARCHAR(32) NULL COMMENT ''工作项类型：外场故障/内场故障''',
    'SELECT ''字段 work_item_type 已存在，跳过'' AS result'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 检查并添加"案例发生时间"字段
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

-- 查询当前表结构，确认字段是否已添加
SELECT 
    COLUMN_NAME AS '字段名',
    COLUMN_TYPE AS '字段类型',
    IS_NULLABLE AS '是否可空',
    COLUMN_COMMENT AS '字段注释'
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'wh_ai_db'
  AND TABLE_NAME = 'issue_impact_case_table'
  AND COLUMN_NAME IN ('assign_to', 'work_item_type', 'case_occur_time')
ORDER BY COLUMN_NAME;

