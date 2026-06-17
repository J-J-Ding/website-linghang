# 代码重构总结 - 数据库操作分离

## 重构目标

将数据库模型定义和操作函数从 `graph_service.py` 分离到 `data_model.py` 中，遵循项目的现有架构模式。

## 重构内容

### 1. data_model.py - 数据模型层 ✅

**新增内容**：

#### 数据库模型类（5 个）

1. **KNOWLEDGE_COMPONENT_GRAPH** - 图谱缓存表模型
2. **KNOWLEDGE_COMPONENT_GRAPH_NODE** - 图谱节点明细表模型
3. **KNOWLEDGE_COMPONENT_GRAPH_EDGE** - 图谱边明细表模型
4. **KNOWLEDGE_COMPONENT_SECTION** - 组件章节信息表模型
5. **KNOWLEDGE_COMPONENT_GRAPH_LAYOUT** - 图谱布局配置表模型

#### 数据库操作函数（10 个）

1. **query_cached_graph()** - 查询缓存的图谱
2. **save_graph_to_db()** - 保存图谱到数据库
3. **save_graph_nodes()** - 保存图谱节点
4. **save_graph_edges()** - 保存图谱边
5. **query_graph_nodes()** - 查询图谱节点列表
6. **query_graph_edges()** - 查询图谱边列表
7. **save_graph_layout()** - 保存图谱布局
8. **query_graph_layouts()** - 查询图谱布局列表
9. **query_graph_stats()** - 查询图谱统计信息
10. **cache_component_section()** - 缓存组件章节信息
11. **query_component_sections()** - 查询组件章节信息

**设计模式**：
- 使用 SQLAlchemy ORM
- 绑定到 `db5` 数据库
- 提供 `to_dict()` 方法转换模型为字典
- 所有操作函数都包含异常处理和事务管理

### 2. graph_service.py - 业务逻辑层 ✅

**移除内容**：
- ❌ 所有直接数据库连接代码
- ❌ 所有 SQL 查询语句
- ❌ 所有数据库事务管理代码

**保留内容**：
- ✅ 图谱生成业务逻辑
- ✅ iCenter 页面解析逻辑
- ✅ 节点和边的构建逻辑
- ✅ 模块查找算法
- ✅ 章节提取逻辑
- ✅ 依赖组件提取逻辑
- ✅ 波及特性提取逻辑

**调用方式**：
```python
# 从 data_model.py 导入操作函数
from componentTree.data_model import (
    query_cached_graph,
    save_graph_to_db,
    save_graph_nodes,
    save_graph_edges,
)

# 业务逻辑中直接调用
cached_graph = query_cached_graph(seed_component_id, max_depth)
result = save_graph_to_db(graph_data, operator_person)
save_graph_nodes(graph_id, nodes_list)
save_graph_edges(graph_id, edges_list)
```

### 3. api_component_graph.py - API 接口层 ✅

**修改内容**：
- 移除了所有直接数据库连接代码
- 移除了所有 SQL 查询语句
- 改为调用 `data_model.py` 中的操作函数

**修改的函数**：
1. `API_Knowledge_component_graph_layout_save()` - 现在调用 `save_graph_layout()`
2. `API_Knowledge_component_graph_layout_list()` - 现在调用 `query_graph_layouts()`
3. `API_Knowledge_component_graph_stats()` - 现在调用 `query_graph_stats()`

## 架构分层

```
┌─────────────────────────────────────┐
│         API 接口层                   │
│    (api_component_graph.py)         │
│  - 处理 HTTP 请求/响应                │
│  - 参数验证                          │
│  - 调用业务逻辑层                    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         业务逻辑层                   │
│      (graph_service.py)             │
│  - 图谱生成算法                      │
│  - 页面解析逻辑                      │
│  - 数据转换逻辑                      │
│  - 调用数据模型层                    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         数据模型层                   │
│       (data_model.py)               │
│  - SQLAlchemy ORM 模型               │
│  - 数据库 CRUD 操作                   │
│  - 事务管理                          │
└─────────────────────────────────────┘
```

## 代码对比

### 重构前（graph_service.py）

```python
# ❌ 直接数据库操作
conn = get_db_connection(...)
cursor = conn.cursor()
cursor.execute("SELECT * FROM ...", (params,))
rows = cursor.fetchall()
cursor.close()
conn.close()
```

### 重构后（data_model.py）

```python
# ✅ ORM 模型定义
class KNOWLEDGE_COMPONENT_GRAPH(db.Model):
    __tablename__ = "knowledge_component_graph"
    id = Column(INTEGER(unsigned=True), primary_key=True)
    seed_component_id = Column(String(128), nullable=False)
    # ...

# ✅ 操作函数
def query_cached_graph(seed_component_id: str, max_depth: int = 2):
    graph = db.session.query(KNOWLEDGE_COMPONENT_GRAPH).filter(
        KNOWLEDGE_COMPONENT_GRAPH.seed_component_id == seed_component_id,
        KNOWLEDGE_COMPONENT_GRAPH.max_depth == max_depth,
        # ...
    ).first()
    return graph
```

### 重构后（graph_service.py）

```python
# ✅ 只调用操作函数
from componentTree.data_model import query_cached_graph

cached_graph = query_cached_graph(seed_component_id, max_depth)
```

## 优势

### 1. 代码组织更清晰
- 数据模型集中在 `data_model.py`，易于维护
- 业务逻辑集中在 `graph_service.py`，专注于算法
- API 接口层只处理请求/响应

### 2. 遵循项目规范
- 与现有的 `KNOWLEDGE_COMPONENT_TREE` 模型保持一致
- 使用相同的 SQLAlchemy ORM 模式
- 函数命名风格一致

### 3. 易于测试
- 数据模型层可以独立测试
- 业务逻辑层可以 Mock 数据库操作
- API 接口层可以独立测试

### 4. 易于扩展
- 新增数据库操作只需在 `data_model.py` 中添加函数
- 修改业务逻辑不影响数据模型
- 修改 API 接口不影响业务逻辑

### 5. 事务管理统一
- 所有数据库事务都在 `data_model.py` 中处理
- 业务逻辑层不需要关心事务
- 减少事务相关的 bug

## 文件变更清单

### 修改的文件

1. **data_model.py**
   - 新增：5 个 ORM 模型类
   - 新增：11 个数据库操作函数
   - 行数：从 158 行增加到约 550 行

2. **graph_service.py**
   - 移除：所有直接数据库操作
   - 新增：导入 `data_model.py` 中的函数
   - 行数：从 982 行减少到约 650 行

3. **api_component_graph.py**
   - 移除：3 个函数的直接数据库操作
   - 新增：调用 `data_model.py` 中的函数
   - 行数：从 633 行减少到约 500 行

### 保持不变的文件

- `graph_schema.sql` - 数据库建表脚本
- `test_graph_api.py` - 测试脚本
- `GRAPH_API_README.md` - API 文档
- `IMPLEMENTATION_SUMMARY.md` - 实现总结

## 验证方法

### 1. 语法检查
```bash
# 检查 Python 语法
python -m py_compile flask/api/componentTree/data_model.py
python -m py_compile flask/api/componentTree/graph_service.py
python -m py_compile flask/api/componentTree/api_component_graph.py
```

### 2. 导入测试
```python
# 测试导入
from componentTree.data_model import (
    KNOWLEDGE_COMPONENT_GRAPH,
    KNOWLEDGE_COMPONENT_GRAPH_NODE,
    KNOWLEDGE_COMPONENT_GRAPH_EDGE,
    KNOWLEDGE_COMPONENT_SECTION,
    KNOWLEDGE_COMPONENT_GRAPH_LAYOUT,
    query_cached_graph,
    save_graph_to_db,
    # ...
)

from componentTree.graph_service import (
    get_graph_service,
    GraphService,
    ComponentGraph,
    # ...
)
```

### 3. 功能测试
```bash
# 运行测试脚本
cd flask/api/componentTree
python test_graph_api.py
```

## 注意事项

### 1. 数据库连接
- 所有数据库操作都通过 `db.session` 进行
- 不需要手动管理连接
- 事务由 SQLAlchemy 自动管理

### 2. 异常处理
- `data_model.py` 中的函数都包含异常处理
- 业务逻辑层可以捕获并处理异常
- API 接口层返回友好的错误信息

### 3. 导入顺序
```python
# 先导入数据模型
from componentTree.data_model import ...

# 再导入业务逻辑
from componentTree.graph_service import ...

# 最后导入 API 接口
from componentTree.api_component_graph import ...
```

### 4. 模型使用
```python
# ✅ 正确：使用 ORM 模型
graph = db.session.query(KNOWLEDGE_COMPONENT_GRAPH).filter(...).first()

# ❌ 错误：不要直接使用 SQL
cursor.execute("SELECT * FROM knowledge_component_graph ...")
```

## 后续工作

### 1. 单元测试
- 为 `data_model.py` 中的每个操作函数编写单元测试
- Mock 数据库连接
- 测试异常处理

### 2. 性能优化
- 添加数据库连接池配置
- 优化查询语句
- 添加缓存层（Redis）

### 3. 文档更新
- 更新 `GRAPH_API_README.md`
- 添加数据模型层的使用示例
- 补充架构说明

---

*重构完成时间：2026-05-19*
*重构原则：数据库操作与业务逻辑分离*
