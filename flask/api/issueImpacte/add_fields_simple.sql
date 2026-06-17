-- 数据库：wh_ai_db
-- 数据表：issue_impact_case_table
-- 新增3个字段：指派给、工作项类型、案例发生时间

USE wh_ai_db;

-- 添加"指派给"字段
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `assign_to` VARCHAR(64) NULL COMMENT '指派给';

-- 添加"工作项类型"字段
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `work_item_type` VARCHAR(32) NULL COMMENT '工作项类型：外场故障/内场故障';

-- 添加"案例发生时间"字段
ALTER TABLE `issue_impact_case_table` 
ADD COLUMN `case_occur_time` DATETIME NULL COMMENT '案例发生时间';

