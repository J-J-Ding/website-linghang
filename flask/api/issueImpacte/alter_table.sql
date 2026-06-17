-- 如果表已存在，使用以下 ALTER TABLE 语句添加新字段
-- 添加"指派给"字段

ALTER TABLE `issue_impact_case_table` 
ADD COLUMN IF NOT EXISTS `assign_to` VARCHAR(64) NULL COMMENT '指派给' 
AFTER `rdc_review_ticket`;

-- 如果需要添加索引
-- ALTER TABLE `issue_impact_case_table` ADD INDEX `idx_assign_to` (`assign_to`);

