from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, DECIMAL, or_
from sqlalchemy.dialects.mysql import INTEGER

from electric_knowledge.data_model import db


class KNOWLEDGE_REQUIREMENT_TREE(db.Model):
    """项目-里程碑-市场需求 三层树状结构表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_requirement_tree"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    scope = Column(String(32), nullable=False)  # 作用域/分区键，支持多棵树
    node_id = Column(String(128), nullable=False)  # 节点唯一标识
    parent_id = Column(String(128), nullable=True)  # 父节点 ID，根节点为 NULL
    level = Column(Integer, nullable=False)  # 层级：1=项目，2=里程碑，3=市场需求
    node_type = Column(String(32), nullable=False)  # 节点类型：project / milestone / market_requirement

    # ---- 项目属性（level=1）----
    project_name = Column(String(256), nullable=True)  # 项目名称

    # ---- 里程碑属性（level=2）----
    milestone_name = Column(String(256), nullable=True)  # 里程碑名称

    # ---- 市场需求属性（level=3）----
    rdc_id = Column(String(128), nullable=True)  # RDC 标识
    title = Column(String(512), nullable=True)  # 标题名称
    status = Column(String(64), nullable=True)  # 状态
    main_domain = Column(String(128), nullable=True)  # 主领域
    market_req_url = Column(String(1024), nullable=True)  # 市场需求自身链接
    instance_url = Column(String(1024), nullable=True)  # 需求实例化链接
    instance_status = Column(String(64), nullable=True)  # 需求实例化状态：01-未完成/02-已完成/03-不涉及
    solution_status = Column(String(32), nullable=True)  # 需求方案状态：01-未完成/02-已完成/03-不涉及
    solution_doc_url = Column(String(1024), nullable=True)  # 方案文档链接（RDC）
    access_check = Column(String(64), nullable=True)  # AI准入检查
    icenter_solution_urls = Column(JSON, nullable=True)  # iCenter方案文档链接列表（level=3）
    icenter_component_designs = Column(JSON, nullable=True)  # iCenter组件功能设计链接（level=3），key为方案URL，value为组件功能设计URL列表

    # ---- 通用字段 ----
    sort_no = Column(Integer, nullable=False, default=0)  # 排序号
    has_children = Column(String(1), nullable=False, default="N")  # 是否有子节点 Y/N
    effective_flag = Column(String(10), nullable=True, default="Y")  # 有效标记 Y/N
    sync_batch = Column(String(64), nullable=True)  # 同步批次号
    operator_person = Column(String(64), nullable=True)  # 操作人
    create_time = Column(DateTime, nullable=False, default=datetime.now)  # 创建时间
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)  # 更新时间
    node_payload = Column(JSON, nullable=True)  # 拓展信息（json）

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 增（Create）
# ============================================================================

def replace_requirement_tree_nodes(scope, flat_nodes, operator_person="system", sync_batch=""):
    """
    批量替换指定 scope 的整棵树（软删除旧数据 + 插入新数据）
    输入为扁平的三级节点列表，自动按 project_name + milestone_name 归组构建树

    每个节点格式:
    {
        "project_name": "智能OTN V3.00",
        "milestone_name": "智能OTN V3.00R1P01",
        "rdc_id": "OTNSW-590400",
        "title": "M4LB2Rx2/x5支持...",
        "status": "已分析",
        "main_domain": "02-L1",
        "instance_url": "https://...",
        "solution_status": "02-已完成",
        "solution_doc_url": "https://...",
        "operator_person": "system"
    }
    """
    if not isinstance(flat_nodes, list):
        return {"status": "error", "message": "flat_nodes must be list", "errors": []}

    # ================================================================
    # 阶段一：纯数据校验
    # ================================================================
    errors = []
    for idx, node in enumerate(flat_nodes):
        if not isinstance(node, dict):
            errors.append(f"node[{idx}] is not dict")
            continue
        if not node.get("project_name", "").strip():
            errors.append(f"node[{idx}] missing project_name")
        if not node.get("milestone_name", "").strip():
            errors.append(f"node[{idx}] missing milestone_name")
        if not node.get("rdc_id", "").strip():
            errors.append(f"node[{idx}] missing rdc_id")
        if not node.get("title", "").strip():
            errors.append(f"node[{idx}] missing title")

    if errors:
        return {"status": "error", "message": "validation failed", "errors": errors}

    # ================================================================
    # 阶段二：归组 — 按 project_name → milestone_name 组织层级
    # ================================================================
    # { project_name: { milestone_name: [req_nodes] } }
    grouped = {}
    for node in flat_nodes:
        pname = node["project_name"].strip()
        mname = node["milestone_name"].strip()
        grouped.setdefault(pname, {}).setdefault(mname, []).append(node)

    # ================================================================
    # 阶段三：在事务中执行替换（全成功或全失败）
    # ================================================================
    try:
        # 1. 锁定该 scope 下所有行，防止并发替换
        db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        ).order_by(
            KNOWLEDGE_REQUIREMENT_TREE.id
        ).with_for_update().all()

        # 2. 软删除该 scope 下所有有效节点
        now = datetime.now()
        db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).update(
            {
                KNOWLEDGE_REQUIREMENT_TREE.effective_flag: "N",
                KNOWLEDGE_REQUIREMENT_TREE.update_time: now,
                KNOWLEDGE_REQUIREMENT_TREE.operator_person: operator_person,
            },
            synchronize_session=False,
        )

        # 3. 生成所有新节点对象
        new_nodes = []
        for proj_idx, (pname, milestones) in enumerate(grouped.items()):
            project_node_id = uuid.uuid4().hex
            project_node = KNOWLEDGE_REQUIREMENT_TREE(
                scope=scope,
                node_id=project_node_id,
                parent_id=None,
                level=1,
                node_type="project",
                project_name=pname,
                has_children="N",
                effective_flag="Y",
                sync_batch=sync_batch,
                operator_person=operator_person,
                sort_no=proj_idx,
            )
            new_nodes.append(project_node)
            project_ms_count = 0

            for ms_idx, (mname, requirements) in enumerate(milestones.items()):
                milestone_node_id = uuid.uuid4().hex
                milestone_node = KNOWLEDGE_REQUIREMENT_TREE(
                    scope=scope,
                    node_id=milestone_node_id,
                    parent_id=project_node_id,
                    level=2,
                    node_type="milestone",
                    milestone_name=mname,
                    has_children="N",
                    effective_flag="Y",
                    sync_batch=sync_batch,
                    operator_person=operator_person,
                    sort_no=ms_idx,
                )
                new_nodes.append(milestone_node)
                project_ms_count += 1
                ms_req_count = 0

                # 按 rdc_id 排序：先按字母前缀，再按数字部分，如 "OTNSW-544343" → ("OTNSW-", 544343)
                def _rdc_sort_key(r):
                    import re
                    rdc = r.get("rdc_id", "")
                    m = re.match(r'([^\d]*)(\d+)', rdc)
                    if m:
                        return (m.group(1), int(m.group(2)))
                    return (rdc, 0)
                sorted_requirements = sorted(requirements, key=_rdc_sort_key)

                for req_idx, req in enumerate(sorted_requirements):
                    req_node = KNOWLEDGE_REQUIREMENT_TREE(
                        scope=scope,
                        node_id=uuid.uuid4().hex,
                        parent_id=milestone_node_id,
                        level=3,
                        node_type="market_requirement",
                        rdc_id=req["rdc_id"].strip(),
                        title=req["title"].strip(),
                        status=req.get("status", ""),
                        main_domain=req.get("main_domain", ""),
                        market_req_url=req.get("market_req_url", ""),
                        instance_url=req.get("instance_url", ""),
                        instance_status=req.get("instance_status", ""),
                        solution_status=req.get("solution_status", ""),
                        solution_doc_url=req.get("solution_doc_url", ""),
                        access_check=req.get("access_check", ""),
                        icenter_solution_urls=req.get("icenter_solution_urls"),
                        icenter_component_designs=req.get("icenter_component_designs"),
                        has_children="N",
                        effective_flag="Y",
                        sync_batch=sync_batch,
                        operator_person=operator_person,
                        sort_no=req_idx,
                    )
                    new_nodes.append(req_node)
                    ms_req_count += 1

                if ms_req_count > 0:
                    milestone_node.has_children = "Y"

            if project_ms_count > 0:
                project_node.has_children = "Y"

        # 4. 一次性批量插入所有节点
        db.session.add_all(new_nodes)
        db.session.commit()

        return {
            "status": "success",
            "message": f"replace scope={scope}, total nodes inserted={len(new_nodes)}",
        }

    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"replace_requirement_tree_nodes failed: {str(e)}"}


def add_project_node(scope, project_name, sort_no=0, operator_person="system"):
    """
    新增项目节点（level=1）

    Args:
        scope: 作用域
        project_name: 项目名称
        sort_no: 排序号
        operator_person: 操作人

    Returns:
        dict: {"status": "success", "node_id": "xxx"} 或 {"status": "error", "message": "..."}
    """
    if not project_name or not project_name.strip():
        return {"status": "error", "message": "project_name is required"}

    try:
        node = KNOWLEDGE_REQUIREMENT_TREE(
            scope=scope,
            node_id=uuid.uuid4().hex,
            parent_id=None,
            level=1,
            node_type="project",
            project_name=project_name.strip(),
            has_children="N",
            effective_flag="Y",
            operator_person=operator_person,
            sort_no=sort_no,
        )
        db.session.add(node)
        db.session.commit()
        return {"status": "success", "node_id": node.node_id}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"add_project_node failed: {str(e)}"}


def add_milestone_node(scope, project_node_id, milestone_name, sort_no=0, operator_person="system"):
    """
    新增里程碑节点（level=2）

    Args:
        scope: 作用域
        project_node_id: 父项目节点的 node_id
        milestone_name: 里程碑名称
        sort_no: 排序号
        operator_person: 操作人

    Returns:
        dict: {"status": "success", "node_id": "xxx"} 或 {"status": "error", "message": "..."}
    """
    if not milestone_name or not milestone_name.strip():
        return {"status": "error", "message": "milestone_name is required"}

    try:
        # 查找父项目节点
        project_node = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
            KNOWLEDGE_REQUIREMENT_TREE.node_id == project_node_id,
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.level == 1,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).first()

        if not project_node:
            return {"status": "error", "message": f"project node not found: {project_node_id}"}

        node = KNOWLEDGE_REQUIREMENT_TREE(
            scope=scope,
            node_id=uuid.uuid4().hex,
            parent_id=project_node_id,
            level=2,
            node_type="milestone",
            milestone_name=milestone_name.strip(),
            has_children="N",
            effective_flag="Y",
            operator_person=operator_person,
            sort_no=sort_no,
        )
        db.session.add(node)

        # 更新父节点 has_children
        if project_node.has_children != "Y":
            project_node.has_children = "Y"

        db.session.commit()
        return {"status": "success", "node_id": node.node_id}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"add_milestone_node failed: {str(e)}"}


def add_market_requirement_node(scope, milestone_node_id, rdc_id, title,
                                status="", main_domain="", market_req_url="",
                                instance_url="", solution_status="", solution_doc_url="",
                                icenter_solution_urls=None, icenter_component_designs=None,
                                sort_no=0, operator_person="system"):
    """
    新增市场需求节点（level=3）

    Args:
        scope: 作用域
        milestone_node_id: 父里程碑节点的 node_id
        rdc_id: RDC 标识
        title: 标题名称
        status: 状态
        main_domain: 主领域
        market_req_url: 市场需求自身链接
        instance_url: 需求实例化链接
        solution_status: 需求方案状态
        solution_doc_url: 方案文档链接
        sort_no: 排序号
        operator_person: 操作人

    Returns:
        dict: {"status": "success", "node_id": "xxx"} 或 {"status": "error", "message": "..."}
    """
    if not rdc_id or not rdc_id.strip():
        return {"status": "error", "message": "rdc_id is required"}
    if not title or not title.strip():
        return {"status": "error", "message": "title is required"}

    try:
        # 查找父里程碑节点
        milestone_node = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
            KNOWLEDGE_REQUIREMENT_TREE.node_id == milestone_node_id,
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.level == 2,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).first()

        if not milestone_node:
            return {"status": "error", "message": f"milestone node not found: {milestone_node_id}"}

        node = KNOWLEDGE_REQUIREMENT_TREE(
            scope=scope,
            node_id=uuid.uuid4().hex,
            parent_id=milestone_node_id,
            level=3,
            node_type="market_requirement",
            rdc_id=rdc_id.strip(),
            title=title.strip(),
            status=status,
            main_domain=main_domain,
            market_req_url=market_req_url,
            instance_url=instance_url,
            solution_status=solution_status,
            solution_doc_url=solution_doc_url,
            icenter_solution_urls=icenter_solution_urls,
            icenter_component_designs=icenter_component_designs,
            has_children="N",
            effective_flag="Y",
            operator_person=operator_person,
            sort_no=sort_no,
        )
        db.session.add(node)

        # 更新父节点 has_children
        if milestone_node.has_children != "Y":
            milestone_node.has_children = "Y"

        db.session.commit()
        return {"status": "success", "node_id": node.node_id, "rdc_id": rdc_id.strip()}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"add_market_requirement_node failed: {str(e)}"}


# ============================================================================
# 删（Delete）
# ============================================================================


# ============================================================================
# 改（Update）
# ============================================================================


# ============================================================================
# 查（Read）
# ============================================================================

def query_projects_by_scope(scope):
    """
    查询指定 scope 下所有项目节点

    Args:
        scope: 作用域

    Returns:
        List[Dict]: 项目节点列表
    """
    nodes = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        KNOWLEDGE_REQUIREMENT_TREE.level == 1,
    ).order_by(
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    ).all()

    return [node.to_dict() for node in nodes]


def query_milestones_by_project(scope, project_name):
    """
    查询指定项目下所有里程碑节点

    Args:
        scope: 作用域
        project_name: 项目名称

    Returns:
        List[Dict]: 里程碑节点列表
    """
    # 查找项目节点
    project_node = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.project_name == project_name,
        KNOWLEDGE_REQUIREMENT_TREE.level == 1,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).first()

    if not project_node:
        return []

    # 查找里程碑节点
    nodes = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.parent_id == project_node.node_id,
        KNOWLEDGE_REQUIREMENT_TREE.level == 2,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).order_by(
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    ).all()

    return [node.to_dict() for node in nodes]


def query_market_requirements_by_milestone(scope, project_name, milestone_name):
    """
    查询指定里程碑下所有市场需求节点

    Args:
        scope: 作用域
        project_name: 项目名称
        milestone_name: 里程碑名称

    Returns:
        List[Dict]: 市场需求节点列表
    """
    # 先查找项目节点
    project_node = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.project_name == project_name,
        KNOWLEDGE_REQUIREMENT_TREE.level == 1,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).first()

    if not project_node:
        return []

    # 查找里程碑节点
    milestone_node = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.parent_id == project_node.node_id,
        KNOWLEDGE_REQUIREMENT_TREE.milestone_name == milestone_name,
        KNOWLEDGE_REQUIREMENT_TREE.level == 2,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).first()

    if not milestone_node:
        return []

    # 查找市场需求节点
    nodes = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.parent_id == milestone_node.node_id,
        KNOWLEDGE_REQUIREMENT_TREE.level == 3,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).order_by(
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    ).all()

    return [node.to_dict() for node in nodes]


def query_requirement_tree(scope):
    """
    查询指定 scope 下的完整树结构（嵌套格式）

    Args:
        scope: 作用域

    Returns:
        List[Dict]: 嵌套树结构
    """
    # 查询所有有效节点
    all_nodes = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).order_by(
        KNOWLEDGE_REQUIREMENT_TREE.level.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    ).all()

    # 按 node_id 建索引
    node_map = {}
    for node in all_nodes:
        node_dict = node.to_dict()
        node_dict["children"] = []
        node_map[node.node_id] = node_dict

    # 按 parent_id 组装嵌套树
    tree = []
    for node_dict in node_map.values():
        parent_id = node_dict.get("parent_id")
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(node_dict)
        elif not parent_id:
            tree.append(node_dict)

    return tree


def query_requirement_tree_grouped(scope, group_by="main_domain"):
    """
    查询指定 scope 下的树结构，并在 milestone 和 market_requirement 之间
    插入一层虚拟分组节点（不落库）

    Args:
        scope: 作用域
        group_by: 分组方式，支持:
            - "main_domain": 按主交付领域
            - "knowledge_completeness": 按知识完备度
            - "specific_business": 按特定业务类（待实现）

    Returns:
        List[Dict]: 嵌套树结构（4层）
    """
    # 1. 获取原始3层树
    tree = query_requirement_tree(scope)

    # 2. 选择分组计算函数
    group_handlers = {
        "main_domain": _group_by_main_domain,
        "knowledge_completeness": _group_by_knowledge_completeness,
        "specific_business": _group_by_specific_business,
    }
    handler = group_handlers.get(group_by)
    if not handler:
        raise ValueError(f"不支持的分组方式: {group_by}，可选: {list(group_handlers.keys())}")

    # 3. 遍历每个 milestone，用对应函数计算分组并插入虚拟节点
    import copy
    grouped_tree = copy.deepcopy(tree)

    for project_node in grouped_tree:
        for milestone_node in project_node.get("children", []):
            req_children = milestone_node.get("children", [])
            milestone_node["children"] = handler(milestone_node["node_id"], req_children, scope)

    return grouped_tree


# ==================== 分组处理函数 ====================

def _build_group_node(milestone_node_id, group_value, group_reqs, group_field, scope, sort_no=0):
    """构建一个虚拟分组节点"""
    return {
        "node_id": f"group_{milestone_node_id}_{group_value}",
        "parent_id": milestone_node_id,
        "node_type": "group",
        "group_field": group_field,
        "group_value": group_value,
        "display_name": group_value,
        "level": 2,
        "has_children": "Y" if len(group_reqs) > 0 else "N",
        "effective_flag": "Y",
        "scope": scope,
        "sort_no": sort_no,
        "children": group_reqs,
    }


def _group_by_main_domain(milestone_node_id, req_children, scope):
    """按主交付领域字段值分组"""
    groups = {}
    ungrouped = []
    for req_node in req_children:
        value = req_node.get("main_domain", "") or ""
        if value:
            groups.setdefault(value, []).append(req_node)
        else:
            ungrouped.append(req_node)

    result = []
    for sort_no, (value, reqs) in enumerate(sorted(groups.items())):
        result.append(_build_group_node(milestone_node_id, value, reqs, "main_domain", scope, sort_no))
    # 无 main_domain 值的需求放到最后
    result.extend(ungrouped)
    return result


def _group_by_knowledge_completeness(milestone_node_id, req_children, scope):
    """
    按知识完备度分组:
        A类：instance_url、solution_doc_url、icenter_solution_urls、icenter_component_designs 均有值
        B类：instance_url、solution_doc_url 有值，但 icenter_solution_urls、icenter_component_designs 任意一个及以上没值
        C类：instance_url 有值，但 solution_doc_url 没值
        D类：instance_url 没值
    """
    GROUP_ORDER = ["A类-实例化、方案、详设关联", "B类-实例化、方案关联", "C类-仅实例化", "D类-无实例化"]

    groups = {}
    for req_node in req_children:
        instance_url = req_node.get("instance_url", "") or ""
        solution_doc_url = req_node.get("solution_doc_url", "") or ""
        icenter_solutions = req_node.get("icenter_solution_urls") or []
        icenter_designs = req_node.get("icenter_component_designs") or {}

        has_instance = bool(instance_url.strip())
        has_solution_doc = bool(solution_doc_url.strip())
        has_icenter_solutions = bool(icenter_solutions)
        has_icenter_designs = bool(icenter_designs)

        if has_instance and has_solution_doc and has_icenter_solutions and has_icenter_designs:
            category = "A类-实例化、方案、详设关联"
        elif has_instance and has_solution_doc:
            category = "B类-实例化、方案关联"
        elif has_instance:
            category = "C类-仅实例化"
        else:
            category = "D类-无实例化"

        groups.setdefault(category, []).append(req_node)

    result = []
    for sort_no, category in enumerate(GROUP_ORDER):
        if category in groups:
            display_name = f"{category}（{len(groups[category])}）"
            result.append(_build_group_node(milestone_node_id, display_name, groups[category], "knowledge_completeness", scope, sort_no))
    return result


def _group_by_specific_business(milestone_node_id, req_children, scope):
    """按特定业务类分组（待实现）"""
    # TODO: 实现特定业务类分组逻辑
    return req_children


def query_all_nodes_by_scope(scope):
    """
    查询指定 scope 下所有有效节点的扁平列表

    Args:
        scope: 作用域

    Returns:
        List[Dict]: 扁平节点列表
    """
    nodes = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
    ).order_by(
        KNOWLEDGE_REQUIREMENT_TREE.level.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    ).all()

    return [node.to_dict() for node in nodes]


# ============================================================================
# 需求树分组详情查询
# ============================================================================

# 知识完备度分类条件映射
_KNOWLEDGE_COMPLETENESS_CONDITIONS = {
    "A类-实例化、方案、详设关联": {
        "has_instance": True,
        "has_solution_doc": True,
        "has_icenter_solutions": True,
        "has_icenter_designs": True,
    },
    "B类-实例化、方案关联": {
        "has_instance": True,
        "has_solution_doc": True,
        "has_icenter_solutions": False,
        "has_icenter_designs": False,
    },
    "C类-仅实例化": {
        "has_instance": True,
        "has_solution_doc": False,
    },
    "D类-无实例化": {
        "has_instance": False,
    },
}

# 分组详情返回字段
_GROUP_DETAIL_FIELDS = [
    "rdc_id", "title", "main_domain", "access_check",
    "instance_url", "instance_status", "solution_doc_url", "solution_status",
]


def _json_col_not_empty(Model, col, func):
    """构建 JSON 列"有值"的过滤条件（非 SQL NULL、非 JSON null、非空数组/空对象）"""
    from sqlalchemy import cast, String
    return db.and_(
        col.isnot(None),
        cast(col, String) != "null",
        func.json_length(col) > 0,
    )


def _json_col_is_empty(Model, col, func):
    """构建 JSON 列"为空"的过滤条件（SQL NULL、JSON null、空数组/空对象）"""
    from sqlalchemy import cast, String
    return db.or_(
        col.is_(None),
        cast(col, String) == "null",
        func.coalesce(func.json_length(col), 0) <= 0,
    )


def _build_knowledge_completeness_filter(query, category):
    """根据知识完备度分类名称构建 SQLAlchemy 过滤条件

    由 _KNOWLEDGE_COMPLETENESS_CONDITIONS 字典驱动，避免硬编码 if-elif 链，
    确保定义与实现始终一致。

    MySQL JSON 列空值判断说明：
    - json_length(NULL) = NULL
    - json_length('[]') = 0 / json_length('{}') = 0
    - json_length('[...]') > 0 / json_length('{...}') > 0
    - json_length('null') = 1（JSON null 是有效 JSON 值，需额外排除）
    """
    from sqlalchemy import func

    conditions = _KNOWLEDGE_COMPLETENESS_CONDITIONS.get(category)
    if not conditions:
        raise ValueError(f"不支持的分类: {category}")

    Model = KNOWLEDGE_REQUIREMENT_TREE
    filters = []

    # instance_url: 普通字符串列
    if "has_instance" in conditions:
        if conditions["has_instance"]:
            filters.append(Model.instance_url != "")
            filters.append(Model.instance_url.isnot(None))
        else:
            filters.append(db.or_(Model.instance_url.is_(None), Model.instance_url == ""))

    # solution_doc_url: 普通字符串列
    if "has_solution_doc" in conditions:
        if conditions["has_solution_doc"]:
            filters.append(Model.solution_doc_url != "")
            filters.append(Model.solution_doc_url.isnot(None))
        else:
            filters.append(db.or_(Model.solution_doc_url.is_(None), Model.solution_doc_url == ""))

    # icenter_solution_urls: JSON 列
    if "has_icenter_solutions" in conditions:
        if conditions["has_icenter_solutions"]:
            filters.extend(_json_col_not_empty(Model, Model.icenter_solution_urls, func))
        else:
            filters.append(_json_col_is_empty(Model, Model.icenter_solution_urls, func))

    # icenter_component_designs: JSON 列
    if "has_icenter_designs" in conditions:
        if conditions["has_icenter_designs"]:
            filters.extend(_json_col_not_empty(Model, Model.icenter_component_designs, func))
        else:
            filters.append(_json_col_is_empty(Model, Model.icenter_component_designs, func))

    return query.filter(*filters)


def query_requirement_tree_group_detail(scope, group_by, category, milestone_name=None, project_name=None):
    """
    查询指定分组下的 MR 详情列表

    Args:
        scope: 作用域
        group_by: 分组方式，目前仅支持 "knowledge_completeness"
        category: 分类名称，如 "A类-实例化、方案、详设关联"
        milestone_name: 里程碑名称（可选，限定范围）
        project_name: 项目名称（可选，限定范围）

    Returns:
        List[Dict]: MR 详情列表，仅包含 _GROUP_DETAIL_FIELDS 中的字段
    """
    # 基础查询：level=3, market_requirement, 有效
    query = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
        KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
        KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        KNOWLEDGE_REQUIREMENT_TREE.level == 3,
        KNOWLEDGE_REQUIREMENT_TREE.node_type == "market_requirement",
    )

    # 按项目/里程碑限定范围（使用子查询避免多次额外查询）
    Model = KNOWLEDGE_REQUIREMENT_TREE
    if project_name:
        # 子查询：项目下所有里程碑的 node_id
        project_subq = db.session.query(KNOWLEDGE_REQUIREMENT_TREE.node_id).filter(
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.project_name == project_name,
            KNOWLEDGE_REQUIREMENT_TREE.level == 1,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).correlate(None).subquery()
        milestone_subq = db.session.query(KNOWLEDGE_REQUIREMENT_TREE.node_id).filter(
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.parent_id.in_(db.session.query(project_subq.c.node_id)),
            KNOWLEDGE_REQUIREMENT_TREE.level == 2,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).correlate(None).subquery()
        query = query.filter(Model.parent_id.in_(db.session.query(milestone_subq.c.node_id)))

    if milestone_name:
        # 子查询：指定里程碑的 node_id
        milestone_subq = db.session.query(KNOWLEDGE_REQUIREMENT_TREE.node_id).filter(
            KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
            KNOWLEDGE_REQUIREMENT_TREE.milestone_name == milestone_name,
            KNOWLEDGE_REQUIREMENT_TREE.level == 2,
            KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
        ).correlate(None).subquery()
        query = query.filter(Model.parent_id.in_(db.session.query(milestone_subq.c.node_id)))

    # 按分组方式构建过滤条件
    if group_by == "knowledge_completeness":
        query = _build_knowledge_completeness_filter(query, category)
    else:
        raise ValueError(f"不支持的分组方式: {group_by}")

    # 排序
    query = query.order_by(
        KNOWLEDGE_REQUIREMENT_TREE.sort_no.asc(),
        KNOWLEDGE_REQUIREMENT_TREE.id.asc(),
    )

    nodes = query.all()

    # 只返回指定字段
    result = []
    for node in nodes:
        node_dict = node.to_dict()
        item = {}
        for field in _GROUP_DETAIL_FIELDS:
            item[field] = node_dict.get(field, "") or ""
        result.append(item)

    return result


# ============================================================================
# 需求树知识图谱数据模型
# ============================================================================

class KNOWLEDGE_REQUIREMENT_GRAPH(db.Model):
    """需求树知识图谱缓存表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_requirement_graph"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    seed_requirement_node_id = Column(String(128), nullable=False)
    seed_requirement_name = Column(String(512), nullable=False)
    scope = Column(String(32), nullable=False)
    max_depth = Column(Integer, nullable=False, default=2)
    status = Column(String(32), nullable=False, default='pending')
    total_nodes = Column(Integer, nullable=False, default=0)
    total_edges = Column(Integer, nullable=False, default=0)
    graph_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    refreshed_at = Column(DateTime, nullable=True)
    operator_person = Column(String(64), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_REQUIREMENT_GRAPH_NODE(db.Model):
    """需求树知识图谱节点表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_requirement_graph_node"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)
    node_id = Column(String(128), nullable=False)
    node_type = Column(String(32), nullable=False)
    node_name = Column(Text, nullable=False)
    tree_node_id = Column(String(128), nullable=True)
    raw_data = Column(JSON, nullable=True)
    source_type = Column(String(32), nullable=False, default='auto')
    level = Column(Integer, nullable=False, default=1)
    is_expanded = Column(Integer, nullable=False, default=0)
    position_x = Column(DECIMAL(10, 2), nullable=True)
    position_y = Column(DECIMAL(10, 2), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_REQUIREMENT_GRAPH_EDGE(db.Model):
    """需求树知识图谱边表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_requirement_graph_edge"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)
    edge_id = Column(String(128), nullable=False)
    source_node_id = Column(String(128), nullable=False)
    target_node_id = Column(String(128), nullable=False)
    relation_type = Column(String(32), nullable=False)
    relation_label = Column(String(64), nullable=True)
    source_type = Column(String(32), nullable=False, default='auto')
    raw_data = Column(JSON, nullable=True)
    effective_flag = Column(String(10), nullable=False, default='Y')
    create_time = Column(DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT(db.Model):
    """需求树知识图谱布局配置表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_requirement_graph_layout"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    graph_id = Column(INTEGER(unsigned=True), nullable=False)
    layout_name = Column(String(128), nullable=False)
    layout_type = Column(String(32), default='custom')
    is_default = Column(Integer, default=0)
    is_public = Column(Integer, default=0)
    operator_person = Column(String(64), nullable=False)
    node_positions = Column(JSON, nullable=True)
    viewport_config = Column(JSON, nullable=True)
    filter_config = Column(JSON, nullable=True)
    description = Column(String(512), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL(db.Model):
    """需求分析与方案设计技能信息表"""
    __bind_key__ = "db5"
    __tablename__ = "knowledge_req_analysis_design_skill"

    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    mr_name = Column(String(512), nullable=False, comment='MR需求名称')
    mr_link = Column(String(1024), nullable=False, comment='MR需求链接')
    page_name = Column(String(512), nullable=False, comment='iCenter页面名称')
    page_link = Column(String(1024), nullable=False, comment='iCenter页面链接')
    chapter_name = Column(String(256), nullable=False, comment='文档章节名称')
    use_skill = Column(JSON, nullable=False, comment='关联技能集合，JSON数组')
    know_type = Column(Integer, nullable=False, comment='1：需求分析技能 2：方案设计技能')
    accumulate_business_knowledge = Column(JSON, nullable=True, comment='沉淀的业务知识，JSON格式')
    knowledge_content = Column(String(1024), nullable=False, comment='使用的业务知识')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ============================================================================
# 需求分析与方案设计技能查询函数
# ============================================================================

def query_req_analysis_design_skills_by_mr(mr_name="", mr_link=""):
    """
    根据 MR 名称或链接查询需求分析与方案设计技能数据

    Args:
        mr_name: MR需求名称（模糊匹配）
        mr_link: MR需求链接（精确匹配）

    Returns:
        List[Dict]: 匹配的技能记录列表
    """
    query = db.session.query(KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL)

    filters = []
    if mr_name:
        filters.append(KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.mr_name.like(f"%{mr_name}%"))
    if mr_link:
        filters.append(KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.mr_link == mr_link)

    if filters:
        query = query.filter(or_(*filters))

    results = query.order_by(
        KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.id.asc()
    ).all()

    return [record.to_dict() for record in results]


def query_req_analysis_design_skills_by_page_link(page_link, know_type=None):
    """
    根据 iCenter 页面链接查询关联的技能数据

    Args:
        page_link: iCenter页面链接（精确匹配）
        know_type: 技能类型（可选），1=需求分析技能，2=方案设计技能

    Returns:
        List[Dict]: 匹配的技能记录列表
    """
    query = db.session.query(KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL).filter(
        KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.page_link == page_link,
    )
    if know_type is not None:
        query = query.filter(KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.know_type == know_type)
    results = query.order_by(
        KNOWLEDGE_REQ_ANALYSIS_DESIGN_SKILL.id.asc()
    ).all()

    return [record.to_dict() for record in results]


# ============================================================================
# 图谱数据操作函数
# ============================================================================

def query_cached_requirement_graph(seed_requirement_node_id: str, max_depth: int = 2):
    """查询缓存的图谱，不存在或已过期返回 None"""
    now = datetime.now()
    graph = db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH.seed_requirement_node_id == seed_requirement_node_id,
        KNOWLEDGE_REQUIREMENT_GRAPH.max_depth == max_depth,
        KNOWLEDGE_REQUIREMENT_GRAPH.status == 'completed',
        or_(
            KNOWLEDGE_REQUIREMENT_GRAPH.expires_at.is_(None),
            KNOWLEDGE_REQUIREMENT_GRAPH.expires_at > now
        )
    ).first()
    return graph


def save_requirement_graph_to_db(graph_data: dict, operator_person: str = ""):
    """保存图谱到数据库（upsert）"""
    try:
        existing_graph = db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH).filter(
            KNOWLEDGE_REQUIREMENT_GRAPH.seed_requirement_node_id == graph_data['seedRequirementNodeId'],
            KNOWLEDGE_REQUIREMENT_GRAPH.max_depth == graph_data['maxDepth']
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
            new_graph = KNOWLEDGE_REQUIREMENT_GRAPH(
                seed_requirement_node_id=graph_data['seedRequirementNodeId'],
                seed_requirement_name=graph_data['seedRequirementName'],
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
        return {'status': 'error', 'message': f'save_requirement_graph_to_db failed: {str(e)}'}


def save_requirement_graph_nodes(graph_id: int, nodes: list):
    """保存图谱节点（先删后插）"""
    try:
        db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_NODE).filter(
            KNOWLEDGE_REQUIREMENT_GRAPH_NODE.graph_id == graph_id
        ).delete()

        for node in nodes:
            db_node = KNOWLEDGE_REQUIREMENT_GRAPH_NODE(
                graph_id=graph_id,
                node_id=node['id'],
                node_type=node['type'],
                node_name=node['name'],
                tree_node_id=node.get('treeNodeId'),
                raw_data=node.get('rawData', {}),
                source_type=node.get('sourceType', 'auto'),
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


def save_requirement_graph_edges(graph_id: int, edges: list):
    """保存图谱边（先删后插）"""
    try:
        db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_EDGE).filter(
            KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.graph_id == graph_id
        ).delete()

        for edge in edges:
            db_edge = KNOWLEDGE_REQUIREMENT_GRAPH_EDGE(
                graph_id=graph_id,
                edge_id=edge['id'],
                source_node_id=edge['source'],
                target_node_id=edge['target'],
                relation_type=edge['relationType'],
                relation_label=edge.get('relationLabel', ''),
                source_type=edge.get('sourceType', 'auto'),
                raw_data=edge.get('rawData', {}),
                effective_flag=edge.get('effectiveFlag', 'Y'),
            )
            db.session.add(db_edge)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise e


def query_requirement_graph_nodes(graph_id: int):
    """查询图谱节点列表"""
    nodes = db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_NODE).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_NODE.graph_id == graph_id
    ).all()
    return [node.to_dict() for node in nodes]


def query_requirement_graph_edges(graph_id: int):
    """查询图谱边列表（仅有效的）"""
    edges = db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_EDGE).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.graph_id == graph_id,
        KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.effective_flag == 'Y',
    ).all()
    return [edge.to_dict() for edge in edges]


def save_requirement_graph_layout(layout_data: dict):
    """保存图谱布局"""
    try:
        if layout_data.get('isDefault'):
            db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT).filter(
                KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.graph_id == layout_data['graphId'],
                KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.operator_person == layout_data.get('operatorPerson', '')
            ).update({
                KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.is_default: 0
            })

        new_layout = KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT(
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
        return {'status': 'error', 'message': f'save_requirement_graph_layout failed: {str(e)}'}


def query_requirement_graph_layouts(graph_id: int, operator_person: str = ""):
    """查询图谱布局列表"""
    layouts = db.session.query(KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.graph_id == graph_id,
        or_(
            KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.operator_person == operator_person,
            KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.is_public == 1
        )
    ).order_by(
        KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.is_default.desc(),
        KNOWLEDGE_REQUIREMENT_GRAPH_LAYOUT.create_time.desc()
    ).all()
    return [layout.to_dict() for layout in layouts]


def query_requirement_graph_stats(graph_id: int):
    """查询图谱统计信息"""
    node_type_stats = db.session.query(
        KNOWLEDGE_REQUIREMENT_GRAPH_NODE.node_type,
        db.func.count(KNOWLEDGE_REQUIREMENT_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_REQUIREMENT_GRAPH_NODE.node_type).all()

    relation_type_stats = db.session.query(
        KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.relation_type,
        db.func.count(KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.id)
    ).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.graph_id == graph_id,
        KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.effective_flag == 'Y',
    ).group_by(KNOWLEDGE_REQUIREMENT_GRAPH_EDGE.relation_type).all()

    level_stats = db.session.query(
        KNOWLEDGE_REQUIREMENT_GRAPH_NODE.level,
        db.func.count(KNOWLEDGE_REQUIREMENT_GRAPH_NODE.id)
    ).filter(
        KNOWLEDGE_REQUIREMENT_GRAPH_NODE.graph_id == graph_id
    ).group_by(KNOWLEDGE_REQUIREMENT_GRAPH_NODE.level).all()

    return {
        'nodeTypeStats': {item[0]: item[1] for item in node_type_stats},
        'relationTypeStats': {item[0]: item[1] for item in relation_type_stats},
        'levelStats': {str(item[0]): item[1] for item in level_stats}
    }
