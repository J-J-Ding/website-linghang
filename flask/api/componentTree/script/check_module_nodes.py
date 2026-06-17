#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 module 类型节点
用于诊断为什么找不到模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from componentTree.data_model import KNOWLEDGE_COMPONENT_TREE, init_db

def check_module_nodes(scope):
    """检查 scope 下的 module 节点
    
    Args:
        scope: 范围 (L0/L1/L2/WASON/OSP)
    """
    print("=" * 80)
    print(f"检查 Module 节点")
    print(f"范围：{scope}")
    print("=" * 80)
    
    try:
        # 查询所有 module 类型节点
        module_nodes = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.node_type == "module"
        ).all()
        
        print(f"\n找到 {len(module_nodes)} 个 module 节点:")
        for node in module_nodes[:20]:  # 只显示前 20 个
            print(f"  - node_id: {node.node_id}, title: {node.title}, level: {node.level}, parent_id: {node.parent_id}")
        
        if len(module_nodes) > 20:
            print(f"  ... 还有 {len(module_nodes) - 20} 个")
        
        # 查询特定组件的父节点链
        component_id = "a6fa84ef6e7511f080eaf9504434accd"
        component = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.node_id == component_id
        ).first()
        
        if component:
            print(f"\n{'=' * 80}")
            print(f"组件 {component_id} 的详细信息:")
            print(f"  - title: {component.title}")
            print(f"  - node_type: {component.node_type}")
            print(f"  - level: {component.level}")
            print(f"  - parent_id: {component.parent_id}")
            
            # 递归向上查找父节点
            print(f"\n父节点链:")
            current = component
            visited = set()
            level = 0
            
            while current and level < 10:  # 最多追溯 10 层
                node_id = current.node_id
                if node_id in visited:
                    print(f"  [L{level}] {current.title} (node_id={node_id}, type={current.node_type}) - 检测到循环！")
                    break
                visited.add(node_id)
                
                print(f"  [L{level}] {current.title} (node_id={node_id}, type={current.node_type}, level={current.level})")
                
                if current.node_type == 'module':
                    print(f"    ^^^ 找到 MODULE 节点！")
                    break
                
                if not current.parent_id:
                    print(f"    (已到达根节点，无 parent_id)")
                    break
                
                # 查找父节点
                parent = KNOWLEDGE_COMPONENT_TREE.query.filter(
                    KNOWLEDGE_COMPONENT_TREE.scope == scope,
                    KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
                    KNOWLEDGE_COMPONENT_TREE.node_id == current.parent_id
                ).first()
                
                if not parent:
                    print(f"    (父节点 {current.parent_id} 未找到)")
                    break
                
                current = parent
                level += 1
        
        else:
            print(f"\n❌ 组件 {component_id} 未找到！")
        
        # 统计 node_type 分布
        print(f"\n{'=' * 80}")
        print("Node Type 分布统计:")
        all_nodes = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y"
        ).all()
        
        type_counts = {}
        for node in all_nodes:
            node_type = node.node_type
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        for node_type, count in sorted(type_counts.items()):
            print(f"  - {node_type}: {count} 个")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()
    check_module_nodes("L1")
