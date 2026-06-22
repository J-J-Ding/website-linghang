from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, DECIMAL, and_, or_
from sqlalchemy.dialects.mysql import INTEGER
import re
import json

from electric_knowledge.data_model import db


# ============================================================================
# 特性树专用标题格式校验工具
# ============================================================================

def _validate_feature_node_title(title: str, node_type: str) -> bool:
    """
    根据节点类型校验特性树标题格式

    校验策略：
    - 如果标题符合特性/子特性/分析/方案等格式，直接通过
    - 如果不符合特定格式，仅当 node_type 为 category/root 时通过

    特性格式示例：
      - F010101-业务波CDWSS波长选择
      - FD010101-业务波CDWSS波长选择
      - FS030110-01-子特性名称
      - F010101-业务波CDWSS波长选择-特性分析
      - F010101-业务波CDWSS波长选择-特性方案
      - F010101-业务波CDWSS波长选择-子特性分析

    Args:
        title: 节点标题
        node_type: 节点类型（feature/sub_feature/analysis/scheme/category/root）

    Returns:
        bool: 校验是否通过
    """
    if not title or not isinstance(title, str):
        return False

    # 1. 特性编号基础格式：F/FD/FS + 6位数字，可选 -数字 后缀 + 类型标识(O/E/P/C/SEC等)
    feature_base_pattern = r'^(?:F|FD|FS)\d{6}(?:-\d+)?-[A-Z]{1,3}-.+'

    # 2. 按 node_type 精细校验
    if node_type == "feature":
        # 特性节点：必须符合基础格式，且不能以"特性分析"/"特性方案"/"子特性分析"结尾
        if re.match(feature_base_pattern, title):
            if not re.search(r'-(特性分析|特性方案|子特性分析)$', title):
                return True
        return False

    if node_type == "sub_feature":
        # 子特性：通常以 F 开头，或包含子特性特征，这里放宽为包含 "子特性" 或符合基础格式且没有分析/方案后缀
        if "子特性" in title and not re.search(r'-(特性分析|特性方案)$', title):
            return True
        if re.match(feature_base_pattern, title) and not re.search(r'-(特性分析|特性方案)$', title):
            return True
        return False

    if node_type == "analysis":
        # 特性分析：必须以"特性分析"结尾
        if title.endswith("特性分析"):
            return True
        return False

    if node_type == "scheme":
        # 特性方案：必须以"特性方案"结尾
        if title.endswith("特性方案"):
            return True
        return False

    if node_type == "sub_analysis":
        if title.endswith("子特性分析") or title.endswith("特性分析"):
            return True
        return False

    if node_type == "sub_scheme":
        if title.endswith("子特性方案") or title.endswith("特性方案"):
            return True
        return False

    # 3. category / root 类型允许任何标题（但通常用于目录页）
    if node_type in ["category", "root", "feature_domain", "feature_group", "related_feature"]:
        return True

    # 4. 其他类型默认不通过
    print(f"Warning: Feature node title validation failed: title={title}, node_type={node_type}")
    return False


# ============================================================================
# 1. 特性树节点缓存表
# ============================================================================

class KNOWLEDGE_FEATURE_TREE(db.Model):
    """特性树节点缓存表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_tree"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    scope = Column(String(32), nullable=False)          # L0/L1/L2/智控/支撑 等
    node_id = Column(String(128), nullable=False)       # 节点唯一标识
    parent_id = Column(String(128), nullable=True)      # 父节点 ID
    level = Column(Integer, nullable=False)             # 树层级
    node_type = Column(String(32), nullable=False)      # feature/sub_feature/analysis/scheme/category/root
    title = Column(String(256), nullable=False)         # 节点标题
    url = Column(String(1024), nullable=True)           # iCenter 页面 URL
    space_id = Column(String(64), nullable=True)        # iCenter 空间 ID
    sort_no = Column(Integer, nullable=False, default=0)
    has_children = Column(String(1), nullable=False, default="N")
    effective_flag = Column(String(10), nullable=True, default="Y")
    sync_batch = Column(String(64), nullable=True)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    node_payload = Column(JSON, nullable=True)          # 扩展信息

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def query_knowledge_feature_tree_nodes(scope, max_level=4):
    """查询特性树节点列表（按层级/父节点/排序）"""
    model_list = (
        db.session.query(KNOWLEDGE_FEATURE_TREE)
        .filter(
            KNOWLEDGE_FEATURE_TREE.scope == scope,
            KNOWLEDGE_FEATURE_TREE.effective_flag == "Y",
            KNOWLEDGE_FEATURE_TREE.level <= max_level,
        )
        .order_by(
            KNOWLEDGE_FEATURE_TREE.level.asc(),
            KNOWLEDGE_FEATURE_TREE.parent_id.asc(),
            KNOWLEDGE_FEATURE_TREE.sort_no.asc(),
            KNOWLEDGE_FEATURE_TREE.id.asc(),
        )
        .all()
    )
    return [item.to_dict() for item in model_list]


def replace_knowledge_feature_tree_nodes(scope, node_list, operator_person="", sync_batch=""):
    """
    全量替换特性树节点（先逻辑删除旧数据，再插入新数据）
    自动过滤标题格式不合规的节点
    """
    if not isinstance(node_list, list):
        return {"status": "error", "message": "node_list must be list"}

    valid_node_list = []
    for idx, node in enumerate(node_list):
        node_type = node.get("nodeType", "category")
        title = node.get("title", "")

        if not _validate_feature_node_title(title, node_type):
            print(f"Warning: Feature node validation failed, skipping: title={title}, node_type={node_type}, node_id={node.get('id')}")
            continue

        valid_node_list.append(node)

    if len(valid_node_list) < len(node_list):
        print(f"Info: Filtered out {len(node_list) - len(valid_node_list)} invalid nodes, keeping {len(valid_node_list)}")

    try:
        # 逻辑删除旧数据
        db.session.query(KNOWLEDGE_FEATURE_TREE).filter(
            KNOWLEDGE_FEATURE_TREE.scope == scope,
            KNOWLEDGE_FEATURE_TREE.effective_flag == "Y",
        ).update(
            {
                KNOWLEDGE_FEATURE_TREE.effective_flag: "N",
                KNOWLEDGE_FEATURE_TREE.update_time: datetime.now(),
                KNOWLEDGE_FEATURE_TREE.operator_person: operator_person,
            },
            synchronize_session=False,
        )

        # 插入新数据
        for idx, node in enumerate(valid_node_list):
            model = KNOWLEDGE_FEATURE_TREE(
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
# 2. 特性知识图谱缓存表
# ============================================================================

class KNOWLEDGE_FEATURE_GRAPH(db.Model):
    """特性图谱缓存表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_graph"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    seed_feature_id = Column(String(128), nullable=False)        # 种子特性 ID
    seed_feature_name = Column(String(256), nullable=False)      # 种子特性名称
    scope = Column(String(32), nullable=False)                   # L0/L1/L2/智控/支撑
    max_depth = Column(Integer, default=2)                       # 最大展开深度
    status = Column(String(32), nullable=False, default='pending')  # pending/generating/completed/failed/expired
    total_nodes = Column(Integer, default=0)
    total_edges = Column(Integer, default=0)
    graph_data = Column(JSON, nullable=True)                     # 完整图谱数据
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)                 # 过期时间（默认 24h）
    refreshed_at = Column(DateTime, nullable=True)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 3. 特性图谱节点明细表
# ============================================================================

class KNOWLEDGE_FEATURE_GRAPH_NODE(db.Model):
    """特性图谱节点明细表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_graph_node"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)     # 关联图谱 ID
    node_id = Column(String(128), nullable=False)                # 节点唯一标识
    node_type = Column(String(32), nullable=False)               # feature/sub_feature/analysis/scheme/dependency
    node_name = Column(Text, nullable=False)                     # 节点名称（支持长文本）
    raw_data = Column(JSON, nullable=True)                       # 原始数据（url, spaceId, desc, pageStatus 等）
    parent_feature_id = Column(String(128), nullable=True)       # 所属特性 ID（用于关联）
    level = Column(Integer, default=1)                           # 层级（距离种子特性的度数）
    is_expanded = Column(Integer, default=0)                     # 是否已展开（0/1）
    position_x = Column(DECIMAL(10, 2), nullable=True)           # 布局 X 坐标
    position_y = Column(DECIMAL(10, 2), nullable=True)           # 布局 Y 坐标
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 4. 特性图谱边明细表
# ============================================================================

class KNOWLEDGE_FEATURE_GRAPH_EDGE(db.Model):
    """特性图谱边明细表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_graph_edge"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)     # 关联图谱 ID
    edge_id = Column(String(128), nullable=False)                # 边唯一标识
    source_node_id = Column(String(128), nullable=False)         # 源节点 ID
    target_node_id = Column(String(128), nullable=False)         # 目标节点 ID
    relation_type = Column(String(32), nullable=False)           # contains/relates_to/implements/depends_on
    relation_label = Column(String(64), nullable=True)           # 关系标注文字（如"包含"、"关联"）
    raw_data = Column(JSON, nullable=True)                       # 原始数据
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 5. 特性分析/方案内容缓存表
# ============================================================================

class KNOWLEDGE_FEATURE_DOCUMENT(db.Model):
    """特性分析/方案内容缓存表（存储从 iCenter 解析的详细内容）"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_document"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    feature_id = Column(String(128), nullable=False)             # 所属特性 ID
    feature_url = Column(String(1024), nullable=False)           # 特性 iCenter 页面 URL
    doc_id = Column(String(128), nullable=False)                 # 文档唯一标识（如 analysis_F010101）
    doc_title = Column(String(256), nullable=False)              # 文档标题（如"F010101-业务波CDWSS波长选择-特性分析"）
    doc_type = Column(String(32), nullable=False)                # analysis / scheme / sub_analysis
    doc_content = Column(Text, nullable=True)                    # 文档内容摘要/全文（HTML或纯文本）
    raw_html = Column(Text, nullable=True)                       # 原始 HTML 片段
    parsed_at = Column(DateTime, nullable=True, default=datetime.now)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 6. 特性图谱布局配置表
# ============================================================================

class KNOWLEDGE_FEATURE_GRAPH_LAYOUT(db.Model):
    """特性图谱布局配置表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_feature_graph_layout"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)     # 关联图谱 ID
    layout_name = Column(String(128), nullable=False)            # 布局名称
    layout_type = Column(String(32), default='custom')           # custom/dagre/force/circular
    is_default = Column(Integer, default=0)                      # 是否默认布局（0/1）
    is_public = Column(Integer, default=0)                       # 是否公开（0/1）
    operator_person = Column(String(64), nullable=False)         # 创建人
    node_positions = Column(JSON, nullable=True)                 # 节点位置 {node_id: {x, y}}
    viewport_config = Column(JSON, nullable=True)                # 视口配置 {zoom, centerX, centerY}
    filter_config = Column(JSON, nullable=True)                  # 过滤配置 {node_types: [], relation_types: []}
    description = Column(String(512), nullable=True)             # 布局描述
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 7. 特性图谱缓存 CRUD 操作函数（对应原图谱操作函数）
# ============================================================================

def query_cached_feature_graph(seed_feature_id: str, max_depth: int = 2):
    """
    查询缓存的特性图谱（未过期且状态为 completed）
    """
    now = datetime.now()
    graph = db.session.query(KNOWLEDGE_FEATURE_GRAPH).filter(
        KNOWLEDGE_FEATURE_GRAPH.seed_feature_id == seed_feature_id,
        KNOWLEDGE_FEATURE_GRAPH.max_depth == max_depth,
        KNOWLEDGE_FEATURE_GRAPH.status == 'completed',
        or_(
            KNOWLEDGE_FEATURE_GRAPH.expires_at.is_(None),
            KNOWLEDGE_FEATURE_GRAPH.expires_at > now
        )
    ).first()
    return graph


def save_feature_graph_to_db(graph_data: dict, operator_person: str = ""):
    """
    保存特性图谱主表（存在则更新，否则插入）
    """
    try:
        existing_graph = db.session.query(KNOWLEDGE_FEATURE_GRAPH).filter(
            KNOWLEDGE_FEATURE_GRAPH.seed_feature_id == graph_data['seedFeatureId'],
            KNOWLEDGE_FEATURE_GRAPH.max_depth == graph_data['maxDepth']
        ).first()

        if existing_graph:
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
            new_graph = KNOWLEDGE_FEATURE_GRAPH(
                seed_feature_id=graph_data['seedFeatureId'],
                seed_feature_name=graph_data['seedFeatureName'],
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
        return {'status': 'error', 'message': f'save_feature_graph_to_db failed: {str(e)}'}


def save_feature_graph_nodes(graph_id: int, nodes: list):
    """保存特性图谱节点（先删后插）"""
    try:
        db.session.query(KNOWLEDGE_FEATURE_GRAPH_NODE).filter(
            KNOWLEDGE_FEATURE_GRAPH_NODE.graph_id == graph_id
        ).delete()

        for node in nodes:
            db_node = KNOWLEDGE_FEATURE_GRAPH_NODE(
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
                parent_feature_id=node.get('parentFeatureId'),
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


def save_feature_graph_edges(graph_id: int, edges: list):
    """保存特性图谱边（先删后插）"""
    try:
        db.session.query(KNOWLEDGE_FEATURE_GRAPH_EDGE).filter(
            KNOWLEDGE_FEATURE_GRAPH_EDGE.graph_id == graph_id
        ).delete()

        for edge in edges:
            db_edge = KNOWLEDGE_FEATURE_GRAPH_EDGE(
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


def query_feature_graph_nodes(graph_id: int):
    """查询特性图谱节点列表"""
    nodes = db.session.query(KNOWLEDGE_FEATURE_GRAPH_NODE).filter(
        KNOWLEDGE_FEATURE_GRAPH_NODE.graph_id == graph_id
    ).all()
    return [node.to_dict() for node in nodes]


def query_feature_graph_edges(graph_id: int):
    """查询特性图谱边列表"""
    edges = db.session.query(KNOWLEDGE_FEATURE_GRAPH_EDGE).filter(
        KNOWLEDGE_FEATURE_GRAPH_EDGE.graph_id == graph_id
    ).all()
    return [edge.to_dict() for edge in edges]


def save_feature_graph_layout(layout_data: dict):
    """保存特性图谱布局"""
    try:
        if layout_data.get('isDefault'):
            db.session.query(KNOWLEDGE_FEATURE_GRAPH_LAYOUT).filter(
                KNOWLEDGE_FEATURE_GRAPH_LAYOUT.graph_id == layout_data['graphId'],
                KNOWLEDGE_FEATURE_GRAPH_LAYOUT.operator_person == layout_data.get('operatorPerson', '')
            ).update({
                KNOWLEDGE_FEATURE_GRAPH_LAYOUT.is_default: 0
            })

        new_layout = KNOWLEDGE_FEATURE_GRAPH_LAYOUT(
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
        return {'status': 'error', 'message': f'save_feature_graph_layout failed: {str(e)}'}


def query_feature_graph_layouts(graph_id: int, operator_person: str = ""):
    """查询特性图谱布局列表（个人 + 公开）"""
    layouts = db.session.query(KNOWLEDGE_FEATURE_GRAPH_LAYOUT).filter(
        KNOWLEDGE_FEATURE_GRAPH_LAYOUT.graph_id == graph_id,
        or_(
            KNOWLEDGE_FEATURE_GRAPH_LAYOUT.operator_person == operator_person,
            KNOWLEDGE_FEATURE_GRAPH_LAYOUT.is_public == 1
        )
    ).order_by(
        KNOWLEDGE_FEATURE_GRAPH_LAYOUT.is_default.desc(),
        KNOWLEDGE_FEATURE_GRAPH_LAYOUT.create_time.desc()
    ).all()
    return [layout.to_dict() for layout in layouts]


def query_feature_graph_stats(graph_id: int):
    """查询特性图谱统计信息"""
    node_type_stats = db.session.query(
        KNOWLEDGE_FEATURE_GRAPH_NODE.node_type,
        db.func.count(KNOWLEDGE_FEATURE_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_FEATURE_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_FEATURE_GRAPH_NODE.node_type).all()

    relation_type_stats = db.session.query(
        KNOWLEDGE_FEATURE_GRAPH_EDGE.relation_type,
        db.func.count(KNOWLEDGE_FEATURE_GRAPH_EDGE.id)
    ).filter(
        KNOWLEDGE_FEATURE_GRAPH_EDGE.graph_id == graph_id
    ).group_by(KNOWLEDGE_FEATURE_GRAPH_EDGE.relation_type).all()

    level_stats = db.session.query(
        KNOWLEDGE_FEATURE_GRAPH_NODE.level,
        db.func.count(KNOWLEDGE_FEATURE_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_FEATURE_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_FEATURE_GRAPH_NODE.level).all()

    return {
        'nodeTypeStats': {item[0]: item[1] for item in node_type_stats},
        'relationTypeStats': {item[0]: item[1] for item in relation_type_stats},
        'levelStats': {str(item[0]): item[1] for item in level_stats}
    }


def cache_feature_document(feature_id: str, feature_url: str, documents: list, operator_person: str = ""):
    """
    缓存特性分析/方案等文档内容
    documents: 列表，每个元素包含 doc_id, doc_title, doc_type, doc_content 等
    """
    try:
        for doc in documents:
            existing = db.session.query(KNOWLEDGE_FEATURE_DOCUMENT).filter(
                KNOWLEDGE_FEATURE_DOCUMENT.feature_id == feature_id,
                KNOWLEDGE_FEATURE_DOCUMENT.doc_id == doc['doc_id']
            ).first()

            if existing:
                existing.doc_title = doc['doc_title']
                existing.doc_type = doc['doc_type']
                existing.doc_content = doc.get('doc_content', '')
                existing.parsed_at = datetime.now()
                existing.operator_person = operator_person
            else:
                new_doc = KNOWLEDGE_FEATURE_DOCUMENT(
                    feature_id=feature_id,
                    feature_url=feature_url,
                    doc_id=doc['doc_id'],
                    doc_title=doc['doc_title'],
                    doc_type=doc['doc_type'],
                    doc_content=doc.get('doc_content', ''),
                    operator_person=operator_person
                )
                db.session.add(new_doc)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def query_feature_documents(feature_id: str):
    """查询特性的所有文档（分析/方案）"""
    docs = db.session.query(KNOWLEDGE_FEATURE_DOCUMENT).filter(
        KNOWLEDGE_FEATURE_DOCUMENT.feature_id == feature_id
    ).all()
    return [doc.to_dict() for doc in docs]
