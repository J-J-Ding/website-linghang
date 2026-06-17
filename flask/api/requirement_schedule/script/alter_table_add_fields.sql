-- =====================================================
-- 需求排期助手权限配置表字段添加脚本
-- 为已存在的 requirement_schedule_permission_table 表添加新字段
-- =====================================================

USE `requirement_automatic_schedule`;

-- 添加 name 字段（姓名）作为第2列
ALTER TABLE `requirement_schedule_permission_table` 
ADD COLUMN `name` VARCHAR(100) NULL COMMENT '姓名' AFTER `id`;

-- 添加 user_id 字段（工号）作为第3列
ALTER TABLE `requirement_schedule_permission_table` 
ADD COLUMN `user_id` VARCHAR(50) NULL COMMENT '工号' AFTER `name`;

-- 为新字段添加索引
ALTER TABLE `requirement_schedule_permission_table` 
ADD INDEX `idx_user_id` (`user_id`);

ALTER TABLE `requirement_schedule_permission_table` 
ADD INDEX `idx_name` (`name`);

-- =====================================================
-- 脚本执行完成
-- =====================================================
