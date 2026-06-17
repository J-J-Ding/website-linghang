-- 数据库：wh_ai_db
-- 数据表：issue_impact_case_table
-- 新增3个字段：指派给、工作项类型、案例发生时间

USE wh_ai_db;

-- 方式1：直接添加字段（如果字段已存在会报错，需要先检查）
-- 添加"指派给"字段
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `assign_to` VARCHAR(64) NULL COMMENT '指派给';

-- 添加"工作项类型"字段（如果不存在）
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `work_item_type` VARCHAR(32) NULL COMMENT '工作项类型：外场故障/内场故障';

-- 添加"案例发生时间"字段（如果不存在）
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `case_occur_time` DATETIME NULL COMMENT '案例发生时间';

-- 方式2：使用存储过程检查字段是否存在后再添加（推荐，避免重复执行报错）
DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_not_exists$$

CREATE PROCEDURE add_column_if_not_exists(
    IN table_name VARCHAR(255),
    IN column_name VARCHAR(255),
    IN column_definition TEXT
)
BEGIN
    DECLARE column_exists INT DEFAULT 0;
    
    SELECT COUNT(*) INTO column_exists
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = table_name
      AND COLUMN_NAME = column_name;
    
    IF column_exists = 0 THEN
        SET @sql = CONCAT('ALTER TABLE `', table_name, '` ADD COLUMN `', column_name, '` ', column_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('字段 ', column_name, ' 添加成功') AS result;
    ELSE
        SELECT CONCAT('字段 ', column_name, ' 已存在，跳过') AS result;
    END IF;
END$$

DELIMITER ;

-- 使用存储过程添加字段
CALL add_column_if_not_exists('issue_impact_case_table', 'assign_to', 'VARCHAR(64) NULL COMMENT ''指派给''');
CALL add_column_if_not_exists('issue_impact_case_table', 'work_item_type', 'VARCHAR(32) NULL COMMENT ''工作项类型：外场故障/内场故障''');
CALL add_column_if_not_exists('issue_impact_case_table', 'case_occur_time', 'DATETIME NULL COMMENT ''案例发生时间''');

-- 清理存储过程
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

