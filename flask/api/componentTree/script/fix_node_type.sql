-- ============================================================================
-- 组件树节点类型修复脚本
-- 说明：修正 node_type 与 title 不匹配的问题
-- 执行时间：2026-05-19
-- ============================================================================

USE `knowledge_engineering`;

-- ============================================================================
-- 1. 备份原数据（可选，建议先执行）
-- ============================================================================
-- CREATE TABLE knowledge_component_tree_backup_20260519 AS 
-- SELECT * FROM knowledge_component_tree WHERE scope = 'L1';

-- ============================================================================
-- 2. 查看需要修复的数据（预览）
-- ============================================================================
SELECT 
    id,
    node_id,
    title,
    node_type as old_type,
    CASE 
        WHEN title REGEXP '^C-[A-Za-z][0-9]+-(.*) 组件$' THEN 'component'
        WHEN title REGEXP '^SC[0-9]+-(.*)$' THEN 'component'
        WHEN title REGEXP '^M[0-9.]+-(.*)$' THEN 'module'
        ELSE node_type
    END as new_type
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (
    -- node_type 是 category 但标题符合组件/子组件/模块格式
    (node_type = 'category' AND (
      title REGEXP '^C-[A-Za-z][0-9]+-(.*) 组件$' OR
      title REGEXP '^SC[0-9]+-(.*)$' OR
      title REGEXP '^M[0-9.]+-(.*)$'
    ))
  )
ORDER BY level, node_id;

-- ============================================================================
-- 3. 修复组件格式（C-*）
-- ============================================================================
UPDATE knowledge_component_tree 
SET node_type = 'component',
    node_payload = JSON_SET(
      COALESCE(node_payload, JSON_OBJECT()),
      '$.nodeType', 'component'
    ),
    update_time = NOW()
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND node_type = 'category'
  AND title REGEXP '^C-[A-Za-z][0-9]+-(.*) 组件$';

-- ============================================================================
-- 4. 修复子组件格式（SC-*）
-- ============================================================================
UPDATE knowledge_component_tree 
SET node_type = 'component',
    node_payload = JSON_SET(
      COALESCE(node_payload, JSON_OBJECT()),
      '$.nodeType', 'component'
    ),
    update_time = NOW()
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND node_type = 'category'
  AND title REGEXP '^SC[0-9]+-(.*)$';

-- ============================================================================
-- 5. 修复模块格式（M-*）
-- ============================================================================
UPDATE knowledge_component_tree 
SET node_type = 'module',
    node_payload = JSON_SET(
      COALESCE(node_payload, JSON_OBJECT()),
      '$.nodeType', 'module'
    ),
    update_time = NOW()
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND node_type = 'category'
  AND title REGEXP '^M[0-9.]+-(.*)$';

-- ============================================================================
-- 6. 验证修复结果
-- ============================================================================
SELECT 
    '修复后统计' as info,
    node_type,
    COUNT(*) as count
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
GROUP BY node_type
ORDER BY level, node_type;

-- ============================================================================
-- 7. 检查是否还有不匹配的数据
-- ============================================================================
SELECT 
    '未修复的数据' as info,
    id,
    node_id,
    title,
    node_type,
    level
FROM knowledge_component_tree
WHERE scope = 'L1'
  AND effective_flag = 'Y'
  AND (
    (node_type = 'category' AND (
      title REGEXP '^C-[A-Za-z][0-9]+-(.*) 组件$' OR
      title REGEXP '^SC[0-9]+-(.*)$' OR
      title REGEXP '^M[0-9.]+-(.*)$'
    ))
    OR
    (node_type = 'component' AND NOT (
      title REGEXP '^C-[A-Za-z][0-9]+-(.*) 组件$' OR
      title REGEXP '^SC[0-9]+-(.*)$'
    ))
    OR
    (node_type = 'module' AND NOT (
      title REGEXP '^M[0-9.]+-(.*)$'
    ))
  )
ORDER BY level, node_id;
