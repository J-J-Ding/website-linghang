from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, DECIMAL, and_, or_
from sqlalchemy.dialects.mysql import INTEGER
import re
import json

from electric_knowledge.data_model import db


def _validate_node_title(title: str, node_type: str) -> bool:
    """
    根据节点类型校验标题格式
    
    校验策略：
    - 如果标题符合组件/子组件/模块格式，直接通过（基于标题格式识别，忽略 node_type）
    - 如果不符合特定格式，仅当 node_type 为 category/root 时通过
    
    Args:
        title: 节点标题
        node_type: 节点类型（component/module/category/root）
    
    Returns:
        bool: 校验是否通过
    """
    if not title or not isinstance(title, str):
        return False
    
    # 优先根据标题格式自动识别类型
    is_component_format = False
    is_subcomponent_format = False
    is_module_format = False
    
    # 组件格式：C-[A-Za-z]\d+-(.*)组件 $
    if re.match(r'^C-[A-Za-z]\d+-(.*)组件$', title):
        is_component_format = True
    
    # 子组件格式：SC{编号}-{名称} $
    if re.match(r'^SC\d+-(.*)$', title):
        is_subcomponent_format = True
    
    # 模块格式：M\d+-(.*)$ 或 M\d+.\d+-(.*)$
    if re.match(r'^M[\d.]+-(.*)$', title):
        is_module_format = True
    
    # 如果标题符合组件/子组件/模块格式，直接通过
    # 原因：标题格式本身已经证明了有效性，node_type 可能因层级划分不准确而标记错误
    if is_component_format or is_subcomponent_format or is_module_format:
        return True
    
    # 如果不符合任何特定格式，仅当 node_type 为 category/root 时通过
    if node_type in ["category", "root"]:
        return True
    
    # 如果是 component/module 类型但不符合对应格式，则失败
    print(f"Warning: Node title format mismatch: title={title}, expected node_type={node_type}")
    return False


class KNOWLEDGE_COMPONENT_TREE(db.Model):
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_tree"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    scope = Column(String(32), nullable=False)  # L0/L1/L2/WASON/OSP 等
    node_id = Column(String(128), nullable=False)
    parent_id = Column(String(128), nullable=True)
    level = Column(Integer, nullable=False)
    node_type = Column(String(32), nullable=False)
    title = Column(String(256), nullable=False)
    url = Column(String(1024), nullable=True)
    space_id = Column(String(64), nullable=True)
    sort_no = Column(Integer, nullable=False, default=0)
    has_children = Column(String(1), nullable=False, default="N")
    effective_flag = Column(String(10), nullable=True, default="Y")
    sync_batch = Column(String(64), nullable=True)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    node_payload = Column(JSON, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def query_knowledge_component_tree_nodes(scope, max_level=4):
    model_list = (
        db.session.query(KNOWLEDGE_COMPONENT_TREE)
        .filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
            KNOWLEDGE_COMPONENT_TREE.level <= max_level,
        )
        .order_by(
            KNOWLEDGE_COMPONENT_TREE.level.asc(),
            KNOWLEDGE_COMPONENT_TREE.parent_id.asc(),
            KNOWLEDGE_COMPONENT_TREE.sort_no.asc(),
            KNOWLEDGE_COMPONENT_TREE.id.asc(),
        )
        .all()
    )
    return [item.to_dict() for item in model_list]


def replace_knowledge_component_tree_nodes(scope, node_list, operator_person="", sync_batch=""):
    if not isinstance(node_list, list):
        return {"status": "error", "message": "node_list must be list"}

    # 过滤无效节点
    valid_node_list = []
    for idx, node in enumerate(node_list):
        node_type = node.get("nodeType", "category")
        title = node.get("title", "")
        
        if not _validate_node_title(title, node_type):
            print(f"Warning: Node title validation failed, skipping: title={title}, node_type={node_type}, node_id={node.get('id')}")
            continue
        
        valid_node_list.append(node)
    
    if len(valid_node_list) < len(node_list):
        print(f"Info: Filtered out {len(node_list) - len(valid_node_list)} invalid nodes, keeping {len(valid_node_list)} valid nodes")

    try:
        db.session.query(KNOWLEDGE_COMPONENT_TREE).filter(
            KNOWLEDGE_COMPONENT_TREE.scope == scope,
            KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
        ).update(
            {
                KNOWLEDGE_COMPONENT_TREE.effective_flag: "N",
                KNOWLEDGE_COMPONENT_TREE.update_time: datetime.now(),
                KNOWLEDGE_COMPONENT_TREE.operator_person: operator_person,
            },
            synchronize_session=False,
        )

        for idx, node in enumerate(valid_node_list):
            model = KNOWLEDGE_COMPONENT_TREE(
                scope=scope,
                node_id=node.get("id", f"{scope}-{idx}"),
                parent_id=node.get("parentId"),
                level=int(node.get("level", 1)),
                node_type=node.get("nodeType", "category"),
                title=node.get("title", ""),
                url=node.get("url", ""),
                space_id=node.get("spaceId", ""),
                sort_no=int(node.get("sortNo", idx)),
                has_children="Y" if node.get("hasChildren") else "N",
                effective_flag="Y",
                sync_batch=sync_batch,
                operator_person=operator_person,
                node_payload=node,
            )
            db.session.add(model)

        db.session.commit()
        return {"status": "success", "message": f"replace scope={scope}, size={len(valid_node_list)}"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"replace failed: {str(e)}"}


# ============================================================================
# 组件知识图谱数据模型
# ============================================================================

class KNOWLEDGE_COMPONENT_GRAPH(db.Model):
    """图谱缓存表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_graph"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    seed_component_id = Column(String(128), nullable=False)  # 种子组件 ID
    seed_component_name = Column(String(256), nullable=False)  # 种子组件名称
    scope = Column(String(32), nullable=False)  # L0/L1/L2/WASON/OSP 等
    max_depth = Column(Integer, default=2)  # 最大展开深度
    status = Column(String(32), nullable=False, default='pending')  # pending/generating/completed/failed/expired
    total_nodes = Column(Integer, default=0)  # 节点总数
    total_edges = Column(Integer, default=0)  # 边总数
    graph_data = Column(JSON, nullable=True)  # 完整的图谱数据（nodes+edges）
    error_message = Column(Text, nullable=True)  # 错误信息
    generated_at = Column(DateTime, nullable=True)  # 生成时间
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    refreshed_at = Column(DateTime, nullable=True)  # 刷新时间
    operator_person = Column(String(64), nullable=True)  # 操作人
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_COMPONENT_GRAPH_NODE(db.Model):
    """图谱节点明细表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_graph_node"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)  # 关联的图谱 ID
    node_id = Column(String(128), nullable=False)  # 节点唯一标识
    node_type = Column(String(32), nullable=False)  # component/module/section/dependent_component/affected_feature/skill
    node_name = Column(Text, nullable=False)  # 节点名称（支持长文本，如完整章节标题）
    raw_data = Column(JSON, nullable=True)  # 原始数据
    parent_component_id = Column(String(128), nullable=True)  # 所属组件 ID
    level = Column(Integer, default=1)  # 节点层级
    is_expanded = Column(Integer, default=0)  # 是否已展开（0/1）
    position_x = Column(DECIMAL(10, 2), nullable=True)  # 布局 X 坐标
    position_y = Column(DECIMAL(10, 2), nullable=True)  # 布局 Y 坐标
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_COMPONENT_GRAPH_EDGE(db.Model):
    """图谱边明细表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_graph_edge"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)  # 关联的图谱 ID
    edge_id = Column(String(128), nullable=False)  # 边唯一标识
    source_node_id = Column(String(128), nullable=False)  # 源节点 ID
    target_node_id = Column(String(128), nullable=False)  # 目标节点 ID
    relation_type = Column(String(32), nullable=False)  # belongs_to/contains/depends_on/affects/requires
    relation_label = Column(String(64), nullable=True)  # 关系标注文字
    raw_data = Column(JSON, nullable=True)  # 原始数据
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_COMPONENT_SECTION(db.Model):
    """组件章节信息表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_section"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    component_id = Column(String(128), nullable=False)  # 组件 ID
    component_url = Column(String(1024), nullable=False)  # 组件 iCenter 页面 URL
    section_id = Column(String(128), nullable=False)  # 章节唯一标识
    section_title = Column(String(256), nullable=False)  # 章节标题
    section_type = Column(String(32), nullable=False)  # 5.3.1 流程设计/5.7.7FT 代码文件设计/4 组件对外接口
    section_content = Column(Text, nullable=True)  # 章节内容摘要
    raw_html = Column(Text, nullable=True)  # 原始 HTML 片段
    parsed_at = Column(DateTime, nullable=True, default=datetime.now)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_COMPONENT_GRAPH_LAYOUT(db.Model):
    """图谱布局配置表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_component_graph_layout"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)  # 关联的图谱 ID
    layout_name = Column(String(128), nullable=False)  # 布局名称
    layout_type = Column(String(32), default='custom')  # custom/dagre/force/circular
    is_default = Column(Integer, default=0)  # 是否为默认布局（0/1）
    is_public = Column(Integer, default=0)  # 是否公开（0/1）
    operator_person = Column(String(64), nullable=False)  # 创建人
    node_positions = Column(JSON, nullable=True)  # 节点位置数据
    viewport_config = Column(JSON, nullable=True)  # 视口配置
    filter_config = Column(JSON, nullable=True)  # 过滤配置
    description = Column(String(512), nullable=True)  # 布局描述
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 图谱数据操作函数
# ============================================================================

def query_cached_graph(seed_component_id: str, max_depth: int = 2):
    """
    查询缓存的图谱
    
    Args:
        seed_component_id: 种子组件 ID
        max_depth: 最大深度
    
    Returns:
        图谱模型对象，如果不存在或已过期则返回 None
    """
    now = datetime.now()
    graph = db.session.query(KNOWLEDGE_COMPONENT_GRAPH).filter(
        KNOWLEDGE_COMPONENT_GRAPH.seed_component_id == seed_component_id,
        KNOWLEDGE_COMPONENT_GRAPH.max_depth == max_depth,
        KNOWLEDGE_COMPONENT_GRAPH.status == 'completed',
        or_(
            KNOWLEDGE_COMPONENT_GRAPH.expires_at.is_(None),
            KNOWLEDGE_COMPONENT_GRAPH.expires_at > now
        )
    ).first()
    
    return graph


def save_graph_to_db(graph_data: dict, operator_person: str = ""):
    """
    保存图谱到数据库
    
    Args:
        graph_data: 图谱数据字典
        operator_person: 操作人
    
    Returns:
        dict: {'status': 'success', 'graph_id': xxx} 或 {'status': 'error', 'message': xxx}
    """
    try:
        # 检查是否已存在
        existing_graph = db.session.query(KNOWLEDGE_COMPONENT_GRAPH).filter(
            KNOWLEDGE_COMPONENT_GRAPH.seed_component_id == graph_data['seedComponentId'],
            KNOWLEDGE_COMPONENT_GRAPH.max_depth == graph_data['maxDepth']
        ).first()
        
        if existing_graph:
            # 更新
            existing_graph.status = graph_data['status']
            existing_graph.total_nodes = graph_data['totalNodes']
            existing_graph.total_edges = graph_data['totalEdges']
            existing_graph.graph_data = graph_data
            existing_graph.error_message = graph_data.get('errorMessage', '')
            existing_graph.generated_at = datetime.fromisoformat(graph_data['generatedAt']) if graph_data.get('generatedAt') else datetime.now()
            existing_graph.expires_at = datetime.fromisoformat(graph_data['expiresAt']) if graph_data.get('expiresAt') else None
            existing_graph.operator_person = operator_person
            existing_graph.update_time = datetime.now()
            graph_id = existing_graph.id
        else:
            # 插入
            new_graph = KNOWLEDGE_COMPONENT_GRAPH(
                seed_component_id=graph_data['seedComponentId'],
                seed_component_name=graph_data['seedComponentName'],
                scope=graph_data['scope'],
                max_depth=graph_data['maxDepth'],
                status=graph_data['status'],
                total_nodes=graph_data['totalNodes'],
                total_edges=graph_data['totalEdges'],
                graph_data=graph_data,
                error_message=graph_data.get('errorMessage', ''),
                generated_at=datetime.fromisoformat(graph_data['generatedAt']) if graph_data.get('generatedAt') else datetime.now(),
                expires_at=datetime.fromisoformat(graph_data['expiresAt']) if graph_data.get('expiresAt') else None,
                operator_person=operator_person
            )
            db.session.add(new_graph)
            db.session.flush()
            graph_id = new_graph.id
        
        db.session.commit()
        return {'status': 'success', 'graph_id': graph_id}
        
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': f'save_graph_to_db failed: {str(e)}'}


def save_graph_nodes(graph_id: int, nodes: list):
    """
    保存图谱节点
    
    Args:
        graph_id: 图谱 ID
        nodes: 节点列表
    """
    try:
        # 先删除旧节点
        db.session.query(KNOWLEDGE_COMPONENT_GRAPH_NODE).filter(
            KNOWLEDGE_COMPONENT_GRAPH_NODE.graph_id == graph_id
        ).delete()
        
        # 插入新节点
        for node in nodes:
            db_node = KNOWLEDGE_COMPONENT_GRAPH_NODE(
                graph_id=graph_id,
                node_id=node['id'],
                node_type=node['type'],
                node_name=node['name'],
                raw_data={
                    'url': node.get('url', ''),
                    'spaceId': node.get('spaceId', ''),
                    'contentId': node.get('contentId', ''),
                    'desc': node.get('desc', ''),
                    'pageStatus': node.get('pageStatus', ''),
                },
                parent_component_id=node.get('parentComponentId'),
                level=node.get('level', 1),
                is_expanded=1 if node.get('expanded', False) else 0,
                position_x=node.get('positionX'),
                position_y=node.get('positionY'),
            )
            db.session.add(db_node)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise e


def save_graph_edges(graph_id: int, edges: list):
    """
    保存图谱边
    
    Args:
        graph_id: 图谱 ID
        edges: 边列表
    """
    try:
        # 先删除旧边
        db.session.query(KNOWLEDGE_COMPONENT_GRAPH_EDGE).filter(
            KNOWLEDGE_COMPONENT_GRAPH_EDGE.graph_id == graph_id
        ).delete()
        
        # 插入新边
        for edge in edges:
            db_edge = KNOWLEDGE_COMPONENT_GRAPH_EDGE(
                graph_id=graph_id,
                edge_id=edge['id'],
                source_node_id=edge['source'],
                target_node_id=edge['target'],
                relation_type=edge['relationType'],
                relation_label=edge.get('relationLabel', ''),
                raw_data=edge.get('rawData', {}),
            )
            db.session.add(db_edge)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise e


def query_graph_nodes(graph_id: int):
    """
    查询图谱节点列表
    
    Args:
        graph_id: 图谱 ID
    
    Returns:
        节点列表
    """
    nodes = db.session.query(KNOWLEDGE_COMPONENT_GRAPH_NODE).filter(
        KNOWLEDGE_COMPONENT_GRAPH_NODE.graph_id == graph_id
    ).all()
    
    return [node.to_dict() for node in nodes]


def query_graph_edges(graph_id: int):
    """
    查询图谱边列表
    
    Args:
        graph_id: 图谱 ID
    
    Returns:
        边列表
    """
    edges = db.session.query(KNOWLEDGE_COMPONENT_GRAPH_EDGE).filter(
        KNOWLEDGE_COMPONENT_GRAPH_EDGE.graph_id == graph_id
    ).all()
    
    return [edge.to_dict() for edge in edges]


def save_graph_layout(layout_data: dict):
    """
    保存图谱布局
    
    Args:
        layout_data: 布局数据字典
    
    Returns:
        dict: {'status': 'success', 'layout_id': xxx} 或 {'status': 'error', 'message': xxx}
    """
    try:
        # 如果设置为默认布局，先取消其他默认布局
        if layout_data.get('isDefault'):
            db.session.query(KNOWLEDGE_COMPONENT_GRAPH_LAYOUT).filter(
                KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.graph_id == layout_data['graphId'],
                KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.operator_person == layout_data.get('operatorPerson', '')
            ).update({
                KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.is_default: 0
            })
        
        # 插入新布局
        new_layout = KNOWLEDGE_COMPONENT_GRAPH_LAYOUT(
            graph_id=layout_data['graphId'],
            layout_name=layout_data['layoutName'],
            layout_type=layout_data.get('layoutType', 'custom'),
            is_default=1 if layout_data.get('isDefault') else 0,
            is_public=1 if layout_data.get('isPublic') else 0,
            operator_person=layout_data.get('operatorPerson', ''),
            node_positions=layout_data.get('nodePositions'),
            viewport_config=layout_data.get('viewportConfig'),
            filter_config=layout_data.get('filterConfig'),
            description=layout_data.get('description', '')
        )
        db.session.add(new_layout)
        db.session.flush()
        
        db.session.commit()
        return {'status': 'success', 'layout_id': new_layout.id}
        
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': f'save_graph_layout failed: {str(e)}'}


def query_graph_layouts(graph_id: int, operator_person: str = ""):
    """
    查询图谱布局列表
    
    Args:
        graph_id: 图谱 ID
        operator_person: 操作人
    
    Returns:
        布局列表
    """
    layouts = db.session.query(KNOWLEDGE_COMPONENT_GRAPH_LAYOUT).filter(
        KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.graph_id == graph_id,
        or_(
            KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.operator_person == operator_person,
            KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.is_public == 1
        )
    ).order_by(
        KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.is_default.desc(),
        KNOWLEDGE_COMPONENT_GRAPH_LAYOUT.create_time.desc()
    ).all()
    
    return [layout.to_dict() for layout in layouts]


def query_graph_stats(graph_id: int):
    """
    查询图谱统计信息
    
    Args:
        graph_id: 图谱 ID
    
    Returns:
        统计信息字典
    """
    # 节点类型统计
    node_type_stats = db.session.query(
        KNOWLEDGE_COMPONENT_GRAPH_NODE.node_type,
        db.func.count(KNOWLEDGE_COMPONENT_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_COMPONENT_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_COMPONENT_GRAPH_NODE.node_type).all()
    
    # 关系类型统计
    relation_type_stats = db.session.query(
        KNOWLEDGE_COMPONENT_GRAPH_EDGE.relation_type,
        db.func.count(KNOWLEDGE_COMPONENT_GRAPH_EDGE.id)
    ).filter(
        KNOWLEDGE_COMPONENT_GRAPH_EDGE.graph_id == graph_id
    ).group_by(KNOWLEDGE_COMPONENT_GRAPH_EDGE.relation_type).all()
    
    # 层级统计
    level_stats = db.session.query(
        KNOWLEDGE_COMPONENT_GRAPH_NODE.level,
        db.func.count(KNOWLEDGE_COMPONENT_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_COMPONENT_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_COMPONENT_GRAPH_NODE.level).all()
    
    return {
        'nodeTypeStats': {item[0]: item[1] for item in node_type_stats},
        'relationTypeStats': {item[0]: item[1] for item in relation_type_stats},
        'levelStats': {str(item[0]): item[1] for item in level_stats}
    }


def cache_component_section(component_id: str, component_url: str, sections: list, operator_person: str = ""):
    """
    缓存组件章节信息（包含章节内容）
    
    Args:
        component_id: 组件 ID
        component_url: 组件 URL
        sections: 章节列表（包含 section_content 字段）
        operator_person: 操作人
    """
    try:
        for section in sections:
            # 检查是否已存在
            existing = db.session.query(KNOWLEDGE_COMPONENT_SECTION).filter(
                KNOWLEDGE_COMPONENT_SECTION.component_id == component_id,
                KNOWLEDGE_COMPONENT_SECTION.section_id == section['section_id']
            ).first()
            
            if existing:
                # 更新
                existing.section_title = section['section_title']
                existing.section_type = section['section_type']
                existing.section_content = section.get('section_content', '')  # 更新章节内容
                existing.parsed_at = datetime.now()
                existing.operator_person = operator_person
            else:
                # 插入
                new_section = KNOWLEDGE_COMPONENT_SECTION(
                    component_id=component_id,
                    component_url=component_url,
                    section_id=section['section_id'],
                    section_title=section['section_title'],
                    section_type=section['section_type'],
                    section_content=section.get('section_content', ''),  # 保存章节内容
                    operator_person=operator_person
                )
                db.session.add(new_section)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise e


def query_component_sections(component_id: str):
    """
    查询组件的章节信息
    
    Args:
        component_id: 组件 ID
    
    Returns:
        章节列表
    """
    sections = db.session.query(KNOWLEDGE_COMPONENT_SECTION).filter(
        KNOWLEDGE_COMPONENT_SECTION.component_id == component_id
    ).all()
    
    return [section.to_dict() for section in sections]