# Bug 修复：种子组件节点类型

## 问题描述

种子组件在图谱中被错误地判断为模块节点，应该始终作为**组件节点**（`NodeType.COMPONENT`）。

## 根本原因

之前的代码根据种子组件的标题格式（C 开头或 SC 开头）来判断节点类型：

```python
# ❌ 错误的逻辑
is_seed_sub_comp = is_valid_sub_comp_tree_page_title_format(seed_component.title)
if is_seed_sub_comp:
    seed_node_type = NodeType.MODULE  # 子组件作为模块节点
else:
    seed_node_type = NodeType.COMPONENT
```

这导致如果种子组件是子组件（SC 开头），会被错误地标记为模块类型。

## 修复方案

种子组件在图谱中始终作为**组件节点**，无论其标题格式如何：

```python
# ✅ 正确的逻辑
seed_node = GraphNode(
    node_id=f"component_{seed_component_id}",
    name=seed_component.title,
    node_type=NodeType.COMPONENT,  # 种子组件始终作为组件节点
    url=seed_component.url,
    space_id=seed_component.space_id,
    content_id=self._parse_icenter_ids(seed_component.url)[1] if seed_component.url else None,
    level=0,
    expanded=True
)
```

## 修改内容

### 1. 删除类型判断逻辑

```python
# 删除
is_seed_sub_comp = is_valid_sub_comp_tree_page_title_format(seed_component.title)
if is_seed_sub_comp:
    print(f"   ℹ️  种子组件是子组件 (SC): {seed_component.title}")
    seed_node_type = NodeType.MODULE
else:
    print(f"   ℹ️  种子组件是组件 (C): {seed_component.title}")
    seed_node_type = NodeType.COMPONENT
```

### 2. 简化 Step 4 逻辑

之前的代码根据 `is_seed_sub_comp` 变量执行不同的查找策略：
- 场景 1：种子是子组件 → 向上找父组件 + 向下找模块
- 场景 2：种子是组件 → 向下找子节点（模块或子组件）

修改后统一为一种策略：
- **Step 4-Down**: 向下查找所有子节点（模块和子组件都要添加）

```python
# Step 4: 向下查找子节点（模块和子组件都要添加）
print(f"\n📌 Step 4: 查找子节点")
child_nodes = self._find_child_modules(seed_component.to_dict(), all_nodes)

# 分类处理：模块和子组件都要添加
module_count = 0
sub_comp_count = 0

for child_node in child_nodes:
    child_title = child_node['title']
    
    # 判断是否为子组件（SC 开头）
    if is_valid_sub_comp_tree_page_title_format(child_title):
        # 是子组件，作为模块类型添加到图谱
        sub_comp_count += 1
        sub_comp_node = GraphNode(
            node_id=f"sub_comp_{child_node['node_id']}",
            name=child_node['title'],
            node_type=NodeType.MODULE,  # 子组件作为模块类型
            level=1,
            parent_component_id=seed_component_id
        )
        graph.add_node(sub_comp_node)
    else:
        # 是模块，直接添加
        module_count += 1
        module_node = GraphNode(
            node_id=f"module_{child_node['node_id']}",
            name=child_node['title'],
            node_type=NodeType.MODULE,
            level=1,
            parent_component_id=seed_component_id
        )
        graph.add_node(module_node)
```

## 节点类型说明

| 节点类型 | 来源 | 节点类型枚举 | 说明 |
|---------|------|------------|------|
| **种子组件** | knowledge_component_tree | `NodeType.COMPONENT` | 图谱的根节点，始终作为组件类型 |
| 子组件 | knowledge_component_tree | `NodeType.MODULE` | 种子组件的子节点，作为模块类型 |
| 模块 | knowledge_component_tree | `NodeType.MODULE` | 种子组件的子节点 |
| 章节 | iCenter 页面解析 | `NodeType.SECTION` | 5.3.1/5.7.7/4 等章节 |
| 依赖组件 | iCenter 页面表格 | `NodeType.DEPENDENT_COMPONENT` | "8 依赖组件"表格 |
| 波及特性 | iCenter 页面表格 | `NodeType.AFFECTED_FEATURE` | "7 关联特性"表格 |
| 知识技能 | person_skill_map 表 | `NodeType.SKILL` | 预留，暂不实现 |

## 测试验证

### 测试场景 1：种子组件是 C 开头的组件

```json
{
  "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": true
}
```

**预期结果**：
- 种子节点类型：`component`
- 子节点：模块（M 开头）和子组件（SC 开头）都作为 `module` 类型

### 测试场景 2：种子组件是 SC 开头的子组件

```json
{
  "seedComponentId": "SC001-数据处理",
  "scope": "L1",
  "maxDepth": 2,
  "forceRefresh": true
}
```

**预期结果**：
- 种子节点类型：`component`（不再是 `module`）
- 子节点：模块（M 开头）作为 `module` 类型

## 影响范围

- ✅ `graph_service.py` - `generate_graph()` 方法
- ✅ 图谱缓存逻辑 - 种子节点类型统一
- ✅ 前端展示 - 种子组件始终显示为组件节点（颜色/形状）

## 相关文档

- [图谱 API 使用说明](GRAPH_API_USAGE.md)
- [调试打印指南](DEBUG_PRINT_GUIDE.md)
- [Postman 测试集合](POSTMAN_COLLECTION.json)

## 修复日期

2026-05-20

---

*修复完成 ✅*
