-- ============================================
-- 组件存在性检查 SQL 脚本
-- 用途：诊断为什么找不到组件
-- 用法：mysql -u username -p -h host db5 < check_component.sql
-- ============================================

-- 1. 检查 'C-F023-PRTC 组件' 是否存在
SELECT 
    '=== 检查组件：C-F023-PRTC 组件 ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type,
    url,
    space_id,
    effective_flag
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (node_id = 'C-F023-PRTC 组件' OR title = 'C-F023-PRTC 组件');

-- 2. 如果没有找到，尝试模糊匹配
SELECT 
    '=== 模糊匹配包含 'PRTC' 的组件 ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type,
    url,
    space_id,
    effective_flag
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND title LIKE '%PRTC%'
LIMIT 20;

-- 3. 显示 L1 范围内的所有组件
SELECT 
    '=== L1 范围内的所有组件（前 50 个）===' AS info;

SELECT 
    node_id,
    title,
    level,
    parent_id,
    node_type,
    url
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND node_type = 'component'
ORDER BY title
LIMIT 50;

-- 4. 统计 L1 范围内的组件数量
SELECT 
    '=== L1 范围组件统计 ===' AS info;

SELECT 
    scope,
    node_type,
    effective_flag,
    COUNT(*) AS component_count
FROM knowledge_component_tree
WHERE scope = 'L1'
GROUP BY scope, node_type, effective_flag;

-- 5. 检查所有不同的 scope
SELECT 
    '=== 所有 Scope 统计 ===' AS info;

SELECT 
    scope,
    COUNT(*) AS total_count,
    SUM(CASE WHEN node_type = 'component' AND effective_flag = 'Y' THEN 1 ELSE 0 END) AS component_count
FROM knowledge_component_tree
GROUP BY scope
ORDER BY scope;

-- 6. 检查是否有组件名称包含 'C-F023'
SELECT 
    '=== 包含 'C-F023' 的组件 ===' AS info;

SELECT 
    node_id,
    title,
    scope,
    level,
    parent_id,
    node_type,
    url,
    space_id,
    effective_flag
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title LIKE '%C-F023%' OR node_id LIKE '%C-F023%')
LIMIT 20;

-- 7. 检查组件树结构
SELECT 
    '=== 组件树结构（L1 范围）===' AS info;

SELECT 
    node_id,
    title,
    level,
    parent_id,
    node_type,
    scope
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
ORDER BY level, title
LIMIT 100;
