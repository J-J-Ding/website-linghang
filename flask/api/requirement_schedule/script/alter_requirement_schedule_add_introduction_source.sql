-- =====================================================================
-- 为 requirement_schedule_table 表新增"引入来源"字段
-- 用于"可用人力"页面中统计"非本团队主交付PR关联US"的工作量（已用人力2）
--
-- 执行前请确保已连接到正确的数据库：requirement_automatic_schedule
-- =====================================================================

USE `requirement_automatic_schedule`;

-- 检查并添加 introduction_source 字段（引入来源）
SET @col_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule'
      AND TABLE_NAME   = 'requirement_schedule_table'
      AND COLUMN_NAME  = 'introduction_source'
);

SET @sql = IF(
    @col_exists = 0,
    'ALTER TABLE `requirement_schedule_table`
     ADD COLUMN `introduction_source` VARCHAR(100) NULL
         COMMENT ''引入来源（如"非本团队主交付PR"）''
         AFTER `plan_delivery_date`',
    'SELECT ''字段 introduction_source 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为新字段添加索引（如果不存在）
SET @idx_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = 'requirement_automatic_schedule'
      AND TABLE_NAME   = 'requirement_schedule_table'
      AND INDEX_NAME   = 'idx_introduction_source'
);

SET @sql = IF(
    @idx_exists = 0,
    'ALTER TABLE `requirement_schedule_table`
     ADD INDEX `idx_introduction_source` (`introduction_source`)',
    'SELECT ''索引 idx_introduction_source 已存在，跳过添加'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =====================================================================
-- 脚本执行完成
-- =====================================================================
