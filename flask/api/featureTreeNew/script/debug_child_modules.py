#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试：检查特定组件的子节点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from componentTree.data_model import KNOWLEDGE_COMPONENT_TREE, init_db
from componentTree.component_know_daily_data import is_valid_module_page_title_format

def check_child_modules(component_id, scope):
    """检查组件的子节点"""
    print("=" * 80)
    print(f"检查组件的子节点")
    print(f"组件 ID: {component_id}")
    print(f"范围：{scope}")
    print("=" * 80)
    
    try:
        # 查询组件本身
        component = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.node_id == component_id
        ).first()
        
        if not component:
            print(f"\n❌ 组件 {component_id} 未找到！")
            return
        
        print(f"\n✅ 组件信息:")
        print(f"  - title: {component.title}")
        print(f"  - node_type: {component.node_type}")
        print(f"  - level: {component.level}")
        print(f"  - parent_id: {component.parent_id}")
        print(f"  - url: {component.url}")
        print(f"  - space_id: {component.space_id}")
        
        # 查询所有子节点
        child_nodes = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.parent_id == component_id
        ).all()
        
        print(f"\n📊 找到 {len(child_nodes)} 个子节点:")
        
        if not child_nodes:
            print("  (无子节点)")
        else:
            for i, child in enumerate(child_nodes, 1):
                is_module = False
                match_reason = ""
                
                # 规则 1: node_type='module'
                if child.node_type == 'module':
                    is_module = True
                    match_reason = "node_type='module'"
                
                # 规则 2: 使用 is_valid_module_page_title_format 验证
                elif is_valid_module_page_title_format(child.title):
                    is_module = True
                    match_reason = "valid module title (Mxxx-xxx)"
                
                # 规则 3: 标题包含"模块"字样
                elif '模块' in child.title:
                    is_module = True
                    match_reason = "contains '模块' keyword"
                
                status = "✅ MODULE" if is_module else "❌ non-module"
                print(f"\n  [{i}] {status} [{match_reason}]")
                print(f"      - node_id: {child.node_id}")
                print(f"      - title: {child.title}")
                print(f"      - node_type: {child.node_type}")
                print(f"      - level: {child.level}")
                print(f"      - parent_id: {child.parent_id}")
                print(f"      - url: {child.url or '(empty)'}")
        
        # 统计
        module_count = 0
        for child in child_nodes:
            if child.node_type == 'module' or is_valid_module_page_title_format(child.title) or '模块' in child.title:
                module_count += 1
        
        print(f"\n📈 统计:")
        print(f"  - 总子节点数：{len(child_nodes)}")
        print(f"  - 模块节点数：{module_count}")
        print(f"  - 非模块节点数：{len(child_nodes) - module_count}")
        
        # 显示 node_type 分布
        type_counts = {}
        for child in child_nodes:
            type_counts[child.node_type] = type_counts.get(child.node_type, 0) + 1
        
        print(f"\n  Node Type 分布:")
        for node_type, count in sorted(type_counts.items()):
            print(f"    - {node_type}: {count}")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()
    check_child_modules("a6fa84ef6e7511f080eaf9504434accd", "L1")
