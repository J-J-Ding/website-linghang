#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件存在性检查工具
用于诊断为什么找不到组件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from componentTree.data_model import KNOWLEDGE_COMPONENT_TREE, init_db
from sqlalchemy import or_

def check_component(component_id_or_title, scope):
    """检查组件是否存在
    
    Args:
        component_id_or_title: 组件 ID 或名称
        scope: 范围 (L0/L1/L2/WASON/OSP)
    """
    print("=" * 80)
    print(f"检查组件：{component_id_or_title}")
    print(f"范围：{scope}")
    print("=" * 80)
    
    try:
        # 查询组件
        component = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            or_(
                KNOWLEDGE_COMPONENT_TREE.node_id == component_id_or_title,
                KNOWLEDGE_COMPONENT_TREE.title == component_id_or_title
            )
        ).first()
        
        if component:
            print("\n✅ 组件存在！")
            print(f"\n详细信息:")
            print(f"  - node_id: {component.node_id}")
            print(f"  - title: {component.title}")
            print(f"  - scope: {component.scope}")
            print(f"  - level: {component.level}")
            print(f"  - parent_id: {component.parent_id}")
            print(f"  - node_type: {component.node_type}")
            print(f"  - url: {component.url}")
            print(f"  - space_id: {component.space_id}")
            print(f"  - effective_flag: {component.effective_flag}")
        else:
            print("\n❌ 组件不存在！")
            print("\n可能的原因:")
            print("  1. 组件 ID 或名称错误")
            print("  2. scope 不匹配（组件在其他范围）")
            print("  3. effective_flag 不是 'Y'")
            print("  4. 数据库中没有这个组件")
            
            # 尝试查找相似的组件
            print(f"\n尝试查找相似的组件...")
            similar_components = KNOWLEDGE_COMPONENT_TREE.query.filter(
                KNOWLEDGE_COMPONENT_TREE.scope == scope,
                KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
                KNOWLEDGE_COMPONENT_TREE.title.like(f"%{component_id_or_title}%")
            ).all()
            
            if similar_components:
                print(f"\n找到 {len(similar_components)} 个相似的组件:")
                for comp in similar_components[:10]:  # 只显示前 10 个
                    print(f"  - {comp.title} (node_id: {comp.node_id})")
            else:
                print(f"  没有找到相似的组件")
            
            # 显示该 scope 下的所有组件
            print(f"\n{scope} 范围内的所有组件:")
            all_components = KNOWLEDGE_COMPONENT_TREE.query.filter(
                KNOWLEDGE_COMPONENT_TREE.scope == scope,
                KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
                KNOWLEDGE_COMPONENT_TREE.node_type == "component"
            ).all()
            
            if all_components:
                print(f"  共 {len(all_components)} 个组件:")
                for comp in all_components[:20]:  # 只显示前 20 个
                    print(f"    - {comp.title} (node_id: {comp.node_id})")
                if len(all_components) > 20:
                    print(f"    ... 还有 {len(all_components) - 20} 个组件")
            else:
                print(f"  {scope} 范围内没有组件")
        
    except Exception as e:
        print(f"\n❌ 查询失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


def list_all_scopes():
    """列出所有 scope 下的组件"""
    print("\n" + "=" * 80)
    print("所有 Scope 下的组件统计")
    print("=" * 80)
    
    scopes = KNOWLEDGE_COMPONENT_TREE.query.distinct(KNOWLEDGE_COMPONENT_TREE.scope).all()
    scope_list = [s.scope for s in scopes if s.scope]
    
    for scope in sorted(scope_list):
        count = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.node_type == "component"
        ).count()
        
        print(f"\n{scope}: {count} 个组件")
        
        # 显示前 5 个
        components = KNOWLEDGE_COMPONENT_TREE.query.filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.node_type == "component"
        ).limit(5).all()
        
        for comp in components:
            print(f"  - {comp.title} (node_id: {comp.node_id})")
        
        if count > 5:
            print(f"  ... 还有 {count - 5} 个组件")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 默认测试
    if len(sys.argv) == 1:
        print("用法:")
        print("  python check_component.py <component_id_or_title> [scope]")
        print("\n示例:")
        print("  python check_component.py 'C-F023-PRTC 组件' L1")
        print("  python check_component.py 'a6fa84ef6e7511f080eaf9504434accd' L1")
        print("\n不传参数时，显示所有 scope 的组件统计")
        print("=" * 80)
        list_all_scopes()
    elif len(sys.argv) >= 2:
        component_id = sys.argv[1]
        scope = sys.argv[2] if len(sys.argv) > 2 else "L1"
        check_component(component_id, scope)
    else:
        print("参数错误")
        print("用法：python check_component.py <component_id_or_title> [scope]")
