-- 故障波及案例单表
-- 根据案例单录入详设（开发）文档设计
-- 表名: issue_impact_case_table

CREATE TABLE IF NOT EXISTS `issue_impact_case_table` (
    -- 主键
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    
    -- 案例基本信息
    `case_id` VARCHAR(64) NULL UNIQUE COMMENT '案例ID',
    `case_title` VARCHAR(512) NULL COMMENT '案例标题',
    `belong_project` VARCHAR(128) NULL COMMENT '归属项目',
    `case_found_site` VARCHAR(128) NULL COMMENT '案例发现局点',
    `priority` VARCHAR(32) NULL COMMENT '优先级：高/中/低',
    `quality_topic` VARCHAR(128) NULL COMMENT '关联质量专题',
    `function_category` VARCHAR(128) NULL COMMENT '功能分类',
    `component` VARCHAR(128) NULL COMMENT '组件',
    `part` VARCHAR(128) NULL COMMENT '部件',
    `status` VARCHAR(32) NULL DEFAULT '新建' COMMENT '状态：新建/分析中/横推中/审批中/已完成/已关闭',
    
    -- 工作项信息
    `work_item_id` VARCHAR(64) NULL UNIQUE COMMENT '工作项ID（用于去重）',
    `work_item_type` VARCHAR(32) NULL COMMENT '工作项类型：外场故障/内场故障',
    `work_item_title` VARCHAR(512) NULL COMMENT '工作项标题',
    
    -- 案例时间信息
    `case_occur_time` DATETIME NULL COMMENT '案例发生时间',
    `case_trigger_site` VARCHAR(128) NULL COMMENT '案例触发局点',
    
    -- 业务影响
    `affect_business` VARCHAR(8) NULL COMMENT '是否影响业务：是/否',
    
    -- 故障信息
    `modify_fault_record` VARCHAR(255) NULL COMMENT '修改故障入库记录',
    `fault_code` TEXT NULL COMMENT '故障代码',
    `modified_code` TEXT NULL COMMENT '修改后代码',
    `introduce_fault_record` VARCHAR(255) NULL COMMENT '引入故障入库记录',
    
    -- 流程相关
    `need_horizontal_push` VARCHAR(8) NULL COMMENT '是否需要横推：是/否',
    `need_notice` VARCHAR(8) NULL COMMENT '是否需要通告：是/否',
    `horizontal_push_ticket` VARCHAR(64) NULL COMMENT '横推单ID',
    `rdc_notice_ticket` VARCHAR(64) NULL COMMENT 'RDC通告单ID',
    `rdc_review_ticket` VARCHAR(64) NULL COMMENT 'RDC复盘单ID',
    
    -- 指派信息
    `assign_to` VARCHAR(64) NULL COMMENT '指派给',
    
    -- 系统字段
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `create_by` VARCHAR(64) NULL COMMENT '创建人',
    `update_by` VARCHAR(64) NULL COMMENT '更新人',
    
    -- 索引
    INDEX `idx_case_id` (`case_id`),
    INDEX `idx_work_item_id` (`work_item_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_belong_project` (`belong_project`),
    INDEX `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='故障波及案例单表';

