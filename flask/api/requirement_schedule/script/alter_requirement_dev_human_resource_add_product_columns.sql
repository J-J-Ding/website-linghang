-- 为 requirement_dev_human_resource 表补加四个产品人力占比字段
-- 若字段已存在则忽略

USE `requirement_automatic_schedule`;

-- ZXONE 19700
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'zxone_19700'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `zxone_19700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT ', QUOTE('ZXONE 19700 人力占比（范围0~1，2位小数，默认值0.00）')),
    'SELECT "Column zxone_19700 already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ZXONE 9700
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'zxone_9700'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `zxone_9700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT ', QUOTE('ZXONE 9700 人力占比（范围0~1，2位小数，默认值0.00）')),
    'SELECT "Column zxone_9700 already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ZXMP M21
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'zxmp_m721'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `zxmp_m721` DECIMAL(3, 2) DEFAULT 0.00 COMMENT ', QUOTE('ZXMP M21 人力占比（范围0~1，2位小数，默认值0.00）')),
    'SELECT "Column zxmp_m721 already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ZXONE NTON
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE table_schema = DATABASE()
      AND table_name = 'requirement_dev_human_resource'
      AND column_name = 'zxone_nton'
);
SET @sql = IF(@col_exists = 0,
    CONCAT('ALTER TABLE `requirement_dev_human_resource` ADD COLUMN `zxone_nton` DECIMAL(3, 2) DEFAULT 0.00 COMMENT ', QUOTE('ZXONE NTON 人力占比（范围0~1，2位小数，默认值0.00）')),
    'SELECT "Column zxone_nton already exists, skipping..." AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
