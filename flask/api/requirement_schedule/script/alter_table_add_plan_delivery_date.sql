-- 为 requirement_schedule_table 表添加"计划交付日期"字段
-- 执行前请确保已连接到正确的数据库：requirement_automatic_schedule

USE requirement_automatic_schedule;

-- 添加 plan_delivery_date 字段（计划交付日期）
ALTER TABLE requirement_schedule_table 
ADD COLUMN plan_delivery_date VARCHAR(20) NULL COMMENT '计划交付日期 YYYY-MM-DD' 
AFTER plan_finish_system_test_date;
