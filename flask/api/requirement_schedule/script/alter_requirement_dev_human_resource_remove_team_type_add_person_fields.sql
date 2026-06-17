-- 修改 requirement_dev_human_resource 表结构
-- 删除 team_type 字段，新增 person_belong, employee_id, name, leave_time 字段
-- 修改唯一性约束为 (year_month, domain, team, person_belong, employee_id, skill_category)

USE `requirement_automatic_schedule`;

-- 1. 安全删除旧的唯一性约束（如果存在）
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND index_name = 'uk_year_month_domain_team_team_type_skill_category'
);
SET @sql = IF(@index_exists > 0,
    'ALTER TABLE `requirement_dev_human_resource` DROP INDEX `uk_year_month_domain_team_team_type_skill_category`',
    'SELECT "Index uk_year_month_domain_team_team_type_skill_category does not exist, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. 安全删除 team_type 字段（如果存在）
-- 检查字段是否存在，如果存在则删除
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'team_type'
);

SET @sql = IF(@col_exists > 0,
    'ALTER TABLE `requirement_dev_human_resource` DROP COLUMN `team_type`',
    'SELECT "Column team_type does not exist, skipping..." AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 新增人员相关字段（如果不存在）
-- person_belong
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'person_belong'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `person_belong` VARCHAR(20) NOT NULL DEFAULT ', QUOTE(''), ' COMMENT ', QUOTE('人员归属（如中兴、外包）'), ' AFTER `team`'),
    'SELECT "Column person_belong already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- employee_id
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'employee_id'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `employee_id` VARCHAR(20) NOT NULL DEFAULT ', QUOTE(''), ' COMMENT ', QUOTE('工号'), ' AFTER `person_belong`'),
    'SELECT "Column employee_id already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- name
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'name'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `name` VARCHAR(20) NOT NULL DEFAULT ', QUOTE(''), ' COMMENT ', QUOTE('姓名'), ' AFTER `employee_id`'),
    'SELECT "Column name already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- leave_time
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'leave_time'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `leave_time` VARCHAR(20) DEFAULT ', QUOTE(''), ' COMMENT ', QUOTE('离职时间（在职则为空）'), ' AFTER `name`'),
    'SELECT "Column leave_time already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. 创建新的唯一性约束（如果不存在）
-- 使用缩短的名称以避免超过 MySQL 64 字符限制
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND index_name = 'uk_ym_domain_team_pb_eid_skill'
);
SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `requirement_dev_human_resource` ADD UNIQUE KEY `uk_ym_domain_team_pb_eid_skill` (`year_month`, `domain`, `team`, `person_belong`, `employee_id`, `skill_category`)',
    'SELECT "Unique key already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5. 添加索引（如果不存在）
-- idx_person_belong
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND index_name = 'idx_person_belong'
);
SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `requirement_dev_human_resource` ADD INDEX `idx_person_belong` (`person_belong`)',
    'SELECT "Index idx_person_belong already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- idx_employee_id
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND index_name = 'idx_employee_id'
);
SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `requirement_dev_human_resource` ADD INDEX `idx_employee_id` (`employee_id`)',
    'SELECT "Index idx_employee_id already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- idx_name
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND index_name = 'idx_name'
);
SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `requirement_dev_human_resource` ADD INDEX `idx_name` (`name`)',
    'SELECT "Index idx_name already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
