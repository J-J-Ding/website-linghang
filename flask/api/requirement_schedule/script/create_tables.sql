-- =====================================================
-- 需求排期助手数据库表创建脚本
-- 数据库名: requirement_automatic_schedule
-- 数据库地址: 10.239.69.17
-- 创建时间: 2025-01-XX
-- =====================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `requirement_automatic_schedule` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `requirement_automatic_schedule`;

-- =====================================================
-- 1. 需求清单主表
-- =====================================================
CREATE TABLE IF NOT EXISTS `requirement_schedule_table` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  -- 只读字段
  `work_item_type` VARCHAR(50) NULL COMMENT '工作项类型',
  `identifier` VARCHAR(100) NULL COMMENT '标识',
  `title` VARCHAR(500) NULL COMMENT '标题',
  `reuse_degree` VARCHAR(50) NULL COMMENT '复用程度',
  `feature_identifier` VARCHAR(100) NULL COMMENT '特性标识',
  `feature_attribute` VARCHAR(200) NULL COMMENT '特性属性',
  `verification_mode` VARCHAR(100) NULL COMMENT '验证方式',
  `verification_team` VARCHAR(100) NULL COMMENT '验证团队',
  `requirement_sort` VARCHAR(50) NULL COMMENT '需求排序',
  `priority` VARCHAR(50) NULL COMMENT '优先级',
  `domain` VARCHAR(100) NULL COMMENT '领域',
  `team` VARCHAR(100) NULL COMMENT '团队',
  -- 可编辑字段
  `first_evaluation_conclusion` TEXT NULL COMMENT '评估结论（第一次）',
  `second_evaluation_conclusion` TEXT NULL COMMENT '评估结论（第二次）',
  `estimated_workload` FLOAT NULL COMMENT '预计工作量（人天）',
  `estimated_dev_workload` FLOAT NULL COMMENT '预计开发工作量（人天）',
  `estimated_verification_workload` FLOAT NULL COMMENT '预计验证工作量（人天）',
  `estimated_system_test_workload` FLOAT NULL COMMENT '预计系统测试工作量（人天）',
  `plan_start_dev_date` VARCHAR(20) NULL COMMENT '计划开始开发日期（YYYY-MM-DD）',
  `plan_finish_dev_date` VARCHAR(20) NULL COMMENT '计划完成开发日期（YYYY-MM-DD）',
  `plan_start_integration_test_date` VARCHAR(20) NULL COMMENT '计划开始集成测试日期（YYYY-MM-DD）',
  `plan_finish_integration_test_date` VARCHAR(20) NULL COMMENT '计划完成集成测试日期（YYYY-MM-DD）',
  `plan_start_system_test_date` VARCHAR(20) NULL COMMENT '计划开始系统测试日期（YYYY-MM-DD）',
  `plan_finish_system_test_date` VARCHAR(20) NULL COMMENT '计划完成系统测试日期（YYYY-MM-DD）',
  -- 筛选字段
  `belong_product` VARCHAR(100) NULL COMMENT '所属产品',
  `product_roadmap` VARCHAR(100) NULL COMMENT '产品路标',
  `requirement_preplanning` VARCHAR(100) NULL COMMENT '需求预规划',
  -- 系统字段
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `operator_person` VARCHAR(50) NULL COMMENT '操作人',
  `effective_flag` VARCHAR(10) NULL DEFAULT '1' COMMENT '有效标志（1-有效，0-无效）',
  PRIMARY KEY (`id`),
  INDEX `idx_effective_flag` (`effective_flag`),
  INDEX `idx_belong_product` (`belong_product`),
  INDEX `idx_product_roadmap` (`product_roadmap`),
  INDEX `idx_requirement_preplanning` (`requirement_preplanning`),
  INDEX `idx_domain` (`domain`),
  INDEX `idx_team` (`team`),
  INDEX `idx_work_item_type` (`work_item_type`),
  INDEX `idx_create_time` (`create_time`),
  INDEX `idx_update_time` (`update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求清单主表';

-- =====================================================
-- 2. 筛选字段历史输入表
-- =====================================================
CREATE TABLE IF NOT EXISTS `requirement_schedule_filter_history_table` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `filter_type` VARCHAR(50) NOT NULL COMMENT '筛选类型（product_roadmap, requirement_preplanning, domain, team）',
  `filter_value` VARCHAR(200) NOT NULL COMMENT '筛选值',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `operator_person` VARCHAR(50) NULL COMMENT '操作人',
  `effective_flag` VARCHAR(10) NULL DEFAULT '1' COMMENT '有效标志（1-有效，0-无效）',
  PRIMARY KEY (`id`),
  INDEX `idx_filter_type` (`filter_type`),
  INDEX `idx_filter_value` (`filter_value`),
  INDEX `idx_effective_flag` (`effective_flag`),
  INDEX `idx_update_time` (`update_time`),
  UNIQUE KEY `uk_filter_type_value` (`filter_type`, `filter_value`, `effective_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='筛选字段历史输入表';

-- =====================================================
-- 3. 权限配置表
-- =====================================================
CREATE TABLE IF NOT EXISTS `requirement_schedule_permission_table` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(100) NULL COMMENT '姓名',
  `user_id` VARCHAR(50) NULL COMMENT '工号',
  `role_name` VARCHAR(100) NOT NULL COMMENT '角色名称',
  `role_code` VARCHAR(50) NOT NULL COMMENT '角色代码',
  `can_edit` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否可编辑（1-可编辑，0-不可编辑）',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `operator_person` VARCHAR(50) NULL COMMENT '操作人',
  `effective_flag` VARCHAR(10) NULL DEFAULT '1' COMMENT '有效标志（1-有效，0-无效）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_code` (`role_code`),
  INDEX `idx_effective_flag` (`effective_flag`),
  INDEX `idx_can_edit` (`can_edit`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限配置表';

-- =====================================================
-- 初始化权限配置表数据（可选）
-- =====================================================
-- 插入默认权限配置示例
INSERT INTO `requirement_schedule_permission_table` 
(`name`, `user_id`, `role_name`, `role_code`, `can_edit`, `operator_person`, `effective_flag`) 
VALUES 
(NULL, NULL, '管理员', 'admin', 1, 'system', '1'),
(NULL, NULL, '项目经理', 'project_manager', 1, 'system', '1'),
(NULL, NULL, '开发人员', 'developer', 1, 'system', '1'),
(NULL, NULL, '测试人员', 'tester', 0, 'system', '1'),
(NULL, NULL, '只读用户', 'readonly', 0, 'system', '1')
ON DUPLICATE KEY UPDATE 
  `update_time` = CURRENT_TIMESTAMP;

-- =====================================================
-- 初始化筛选字段历史数据（可选）
-- =====================================================
-- 插入默认产品路标
INSERT INTO `requirement_schedule_filter_history_table` 
(`filter_type`, `filter_value`, `operator_person`, `effective_flag`) 
VALUES 
('product_roadmap', 'M721 V5.50R1', 'system', '1'),
('product_roadmap', '智能OTN V3.00R1', 'system', '1'),
('requirement_preplanning', 'M721 V5.50R1', 'system', '1'),
('requirement_preplanning', '智能OTN V3.00R1', 'system', '1')
ON DUPLICATE KEY UPDATE 
  `update_time` = CURRENT_TIMESTAMP;

-- =====================================================
-- 脚本执行完成
-- =====================================================
