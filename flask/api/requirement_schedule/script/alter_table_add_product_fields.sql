-- 为 requirement_dev_human_resource 表添加4个产品字段
USE `requirement_automatic_schedule`;

-- 检查字段是否存在，如果不存在则添加
DELIMITER //
CREATE PROCEDURE AddProductFields()
BEGIN
    -- 添加 ZXONE 19700 字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'requirement_dev_human_resource'
                   AND COLUMN_NAME = 'zxone_19700') THEN
        ALTER TABLE `requirement_dev_human_resource`
        ADD COLUMN `zxone_19700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE 19700（范围0~1，2位小数，默认值0.00）' AFTER `demand_human_power_ratio`;
    END IF;

    -- 添加 ZXONE 9700 字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'requirement_dev_human_resource'
                   AND COLUMN_NAME = 'zxone_9700') THEN
        ALTER TABLE `requirement_dev_human_resource`
        ADD COLUMN `zxone_9700` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE 9700（范围0~1，2位小数，默认值0.00）' AFTER `zxone_19700`;
    END IF;

    -- 添加 ZXMP M21 字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'requirement_dev_human_resource'
                   AND COLUMN_NAME = 'zxmp_m721') THEN
        ALTER TABLE `requirement_dev_human_resource`
        ADD COLUMN `zxmp_m721` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXMP M21（范围0~1，2位小数，默认值0.00）' AFTER `zxone_9700`;
    END IF;

    -- 添加 ZXONE NTON 字段
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'requirement_dev_human_resource'
                   AND COLUMN_NAME = 'zxone_nton') THEN
        ALTER TABLE `requirement_dev_human_resource`
        ADD COLUMN `zxone_nton` DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'ZXONE NTON（范围0~1，2位小数，默认值0.00）' AFTER `zxmp_m721`;
    END IF;
END //
DELIMITER ;

CALL AddProductFields();
DROP PROCEDURE AddProductFields;
