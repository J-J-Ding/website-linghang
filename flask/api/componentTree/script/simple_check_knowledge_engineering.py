#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的组件检查脚本 - 数据库：knowledge_engineering
直接打印 SQL，不执行
"""

print("=" * 80)
print("组件数据库检查 SQL")
print("数据库：knowledge_engineering")
print("表名：knowledge_component_tree")
print("=" * 80)
print()

# SQL 1: 检查特定组件
print("-- 1. 检查 'C-F023-PRTC 组件设计' 是否存在 (scope=L1)")
print("""
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
  AND (node_id = 'C-F023-PRTC 组件设计' OR title = 'C-F023-PRTC 组件设计');
""")

# SQL 2: 模糊匹配
print("\n-- 2. 模糊匹配包含 'PRTC' 的组件（所有 scope）")
print("""
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND title LIKE '%PRTC%'
ORDER BY scope, level, title
LIMIT 30;
""")

# SQL 3: 所有 Scope 统计
print("\n-- 3. 所有 Scope 统计")
print("""
SELECT 
    scope,
    COUNT(*) AS total_count,
    SUM(CASE WHEN node_type = 'component' AND effective_flag = 'Y' THEN 1 ELSE 0 END) AS component_count
FROM knowledge_component_tree
GROUP BY scope
ORDER BY scope;
""")

# SQL 4: 包含 'C-F023' 的组件
print("\n-- 4. 包含 'C-F023' 的所有组件")
print("""
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title LIKE '%C-F023%' OR node_id LIKE '%C-F023%')
ORDER BY scope, level, title
LIMIT 30;
""")

# SQL 5: 检查不带"设计"的组件
print("\n-- 5. 检查不带'设计'的 C-F023-PRTC 组件")
print("""
SELECT 
    node_id,
    title,
    scope,
    level
FROM knowledge_component_tree
WHERE effective_flag = 'Y'
  AND (title = 'C-F023-PRTC 组件' OR title LIKE 'C-F023-PRTC%')
ORDER BY scope, level, title
LIMIT 20;
""")

print("=" * 80)
print("\n使用方法:")
print("1. 复制上面的 SQL")
print("2. 在 MySQL 客户端中执行:")
print("   mysql -u username -p -h host knowledge_engineering")
print("3. 粘贴 SQL 并回车")
print("4. 查看结果，找到正确的组件 ID 和 scope")
print("=" * 80)
