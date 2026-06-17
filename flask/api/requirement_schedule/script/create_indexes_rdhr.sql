-- ========================================
-- requirement_dev_human_resource 表索引优化
-- 执行说明：在 MySQL 数据库中执行此脚本
-- 注意：ALGORITHM=INPLACE LOCK=NONE 可避免锁表，适合生产环境在线操作
-- ========================================

-- 单列索引：常用查询字段
CREATE INDEX idx_rdhr_department ON requirement_dev_human_resource(department) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_domain ON requirement_dev_human_resource(domain) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_team ON requirement_dev_human_resource(team) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_person_belong ON requirement_dev_human_resource(person_belong) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_employee_id ON requirement_dev_human_resource(employee_id) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_name ON requirement_dev_human_resource(name) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_skill_category ON requirement_dev_human_resource(skill_category) ALGORITHM=INPLACE LOCK=NONE;
CREATE INDEX idx_rdhr_year_month ON requirement_dev_human_resource(year_month) ALGORITHM=INPLACE LOCK=NONE;

-- 复合索引：排序场景（ORDER BY year_month, domain, team, person_belong）
CREATE INDEX idx_rdhr_sort_fields ON requirement_dev_human_resource(year_month, domain, team, person_belong) ALGORITHM=INPLACE LOCK=NONE;

-- 复合索引：常用查询组合（department, domain, team, year_month）
CREATE INDEX idx_rdhr_query_common ON requirement_dev_human_resource(department, domain, team, year_month) ALGORITHM=INPLACE LOCK=NONE;

-- ========================================
-- 验证索引是否创建成功
-- ========================================
SHOW INDEX FROM requirement_dev_human_resource;

-- ========================================
-- 如果需要查看查询计划，可使用以下命令测试
-- ========================================
-- EXPLAIN SELECT * FROM requirement_dev_human_resource WHERE year_month LIKE '2026-%';
-- EXPLAIN SELECT * FROM requirement_dev_human_resource WHERE employee_id = '12345678';
-- EXPLAIN SELECT * FROM requirement_dev_human_resource WHERE domain = '13-智能控制' AND team = '某个团队';