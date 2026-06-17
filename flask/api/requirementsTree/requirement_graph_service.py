"""
需求树知识图谱服务
功能：生成、缓存、查询需求树知识图谱
说明：本文件只包含业务逻辑，数据库操作全部在 data_model.py 中
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

from requirementsTree.data_model import (
    KNOWLEDGE_REQUIREMENT_TREE,
    query_cached_requirement_graph,
    save_requirement_graph_to_db,
    save_requirement_graph_nodes,
    save_requirement_graph_edges,
    query_requirement_graph_nodes,
    query_requirement_graph_edges,
    query_req_analysis_design_skills_by_page_link,
)
from electric_knowledge.data_model import db
from requirementsTree.icenter_fetcher import (
    knowledge_requirement_instance_extract,
    knowledge_requirement_solution_extract,
    knowledge_component_design_extract,
    knowledge_skill_extract,
    get_skillm_page_url,
    SKILLM_ROOT_URL,
    fetch_requirement_solutions,
    fetch_component_designs,
)
from requirementsTree.rdc_inone import _get_repository

logger = logging.getLogger(__name__)


# ============================================================================
# URL 解析与匹配辅助函数
# ============================================================================

def _parse_icenter_url_ids(url):
    """
    从 iCenter 页面 URL 中解析 space_id 和 content_id。
    支持两种格式:
      - https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
      - https://i.zte.com.cn/#/shared/{spaceId}/wiki/page/{pageId}
    解析失败返回 (None, None)
    """
    if not url or not isinstance(url, str):
        return None, None
    try:
        parsed = urlparse(url)
        fragment = parsed.fragment
        if not fragment:
            return None, None
        parts = [p for p in fragment.split('/') if p]
        space_id = None
        content_id = None
        for i, part in enumerate(parts):
            if part in ("space", "shared") and i + 1 < len(parts):
                space_id = parts[i + 1]
            if part == "page" and i + 1 < len(parts):
                content_id = parts[i + 1]
        return space_id, content_id
    except Exception:
        return None, None


def _match_by_space_and_content_id(rdc_url, icenter_urls):
    """
    通过比较 space_id 和 content_id 判断 RDC 方案链接与 iCenter 方案链接是否匹配。
    只要 icenter_urls 中任意一个 URL 的 space_id 和 content_id 与 rdc_url 的一致，即判定为匹配。
    """
    rdc_space_id, rdc_content_id = _parse_icenter_url_ids(rdc_url)
    if not rdc_space_id or not rdc_content_id:
        return False
    for url in icenter_urls:
        ic_space_id, ic_content_id = _parse_icenter_url_ids(url)
        if ic_space_id == rdc_space_id and ic_content_id == rdc_content_id:
            return True
    return False


# ============================================================================
# 节点类型和关系类型定义
# ============================================================================

class NodeType:
    """节点类型枚举"""
    PRODUCT_REQUIREMENT = 'product_requirement'        # 产品需求（PR）
    MARKET_REQUIREMENT = 'market_requirement'          # 市场需求（种子）
    REQUIREMENT_INSTANCE = 'requirement_instance'      # 需求实例化
    REQUIREMENT_SOLUTION = 'requirement_solution'      # 需求方案
    COMPONENT_DESIGN = 'component_design'              # 组件功能设计
    FEATURE = 'feature'                                # 特性
    SECTION = 'section'                                # 章节
    COMPONENT = 'component'                            # 组件
    SKILL = 'skill'                                    # 技能
    REQUIREMENT_ANALYSIS_SKILL = 'requirement_analysis_skill'  # 需求分析技能
    SOLUTION_DESIGN_SKILL = 'solution_design_skill'            # 方案设计技能


class RelationType:
    """关系类型枚举"""
    CONTAINS = 'contains'      # 包含（层次从属）
    RELATES_TO = 'relates_to'  # 关联（语义关联，核心链路）
    AFFECTS = 'affects'        # 波及（影响传播）
    VERIFIES = 'verifies'      # 校验（RDC方案与iCenter方案一致性）

# 节点类型显示名称映射
NODE_TYPE_LABELS = {
    NodeType.PRODUCT_REQUIREMENT: '产品需求',
    NodeType.MARKET_REQUIREMENT: '市场需求',
    NodeType.REQUIREMENT_INSTANCE: '需求实例化',
    NodeType.REQUIREMENT_SOLUTION: '需求方案',
    NodeType.COMPONENT_DESIGN: '组件功能设计',
    NodeType.FEATURE: '特性',
    NodeType.SECTION: '章节',
    NodeType.COMPONENT: '组件',
    NodeType.SKILL: '技能',
    NodeType.REQUIREMENT_ANALYSIS_SKILL: '需求分析技能',
    NodeType.SOLUTION_DESIGN_SKILL: '方案设计技能',
}

# 关系类型显示名称映射
RELATION_TYPE_LABELS = {
    RelationType.CONTAINS: '包含',
    RelationType.RELATES_TO: '关联',
    RelationType.AFFECTS: '波及',
    RelationType.VERIFIES: '校验',
}


# ============================================================================
# 图谱数据模型
# ============================================================================

class RequirementGraphNode:
    """需求图谱节点"""

    def __init__(self, node_id: str, name: str, node_type: str, **kwargs):
        self.id = node_id
        self.name = name
        self.type = node_type
        self.expanded = kwargs.get('expanded', False)
        self.url = kwargs.get('url', '')
        self.tree_node_id = kwargs.get('tree_node_id', '')
        self.raw_data = kwargs.get('raw_data', {})
        self.source_type = kwargs.get('source_type', 'auto')
        self.level = kwargs.get('level', 1)
        self.position_x = kwargs.get('position_x')
        self.position_y = kwargs.get('position_y')

    def to_dict(self) -> Dict:
        """转换为字典格式（驼峰命名，供前端和 save 函数使用）"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'typeLabel': NODE_TYPE_LABELS.get(self.type, self.type),
            'expanded': self.expanded,
            'url': self.url,
            'treeNodeId': self.tree_node_id,
            'rawData': self.raw_data,
            'sourceType': self.source_type,
            'level': self.level,
            'positionX': self.position_x,
            'positionY': self.position_y,
        }


class RequirementGraphEdge:
    """需求图谱边"""

    def __init__(self, edge_id: str, source: str, target: str, relation_type: str, **kwargs):
        self.id = edge_id
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.relation_label = kwargs.get('relation_label', RELATION_TYPE_LABELS.get(relation_type, ''))
        self.source_type = kwargs.get('source_type', 'auto')
        self.raw_data = kwargs.get('raw_data', {})

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'relationType': self.relation_type,
            'relationLabel': self.relation_label,
            'sourceType': self.source_type,
            'rawData': self.raw_data,
        }


class RequirementGraph:
    """需求树知识图谱"""

    def __init__(self, seed_requirement_node_id: str, seed_requirement_name: str, scope: str, max_depth: int = 2):
        self.seed_requirement_node_id = seed_requirement_node_id
        self.seed_requirement_name = seed_requirement_name
        self.scope = scope
        self.max_depth = max_depth
        self.nodes: Dict[str, RequirementGraphNode] = {}
        self.edges: List[RequirementGraphEdge] = []
        self.status = 'pending'
        self.error_message = ''
        self.generated_at = None
        self.expires_at = None

    def add_node(self, node: RequirementGraphNode):
        """添加节点（自动去重）"""
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def add_edge(self, edge: RequirementGraphEdge):
        """添加边"""
        self.edges.append(edge)

    def to_dict(self) -> Dict:
        """转换为字典格式（供前端和缓存使用）"""
        return {
            'seedRequirementNodeId': self.seed_requirement_node_id,
            'seedRequirementName': self.seed_requirement_name,
            'scope': self.scope,
            'maxDepth': self.max_depth,
            'status': self.status,
            'totalNodes': len(self.nodes),
            'totalEdges': len(self.edges),
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'generatedAt': self.generated_at.isoformat() if self.generated_at else None,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'errorMessage': self.error_message,
        }


# ============================================================================
# 图谱生成服务
# ============================================================================

class RequirementGraphService:
    """需求图谱生成服务类"""

    def generate_graph(self, seed_requirement_node_id: str, scope: str, max_depth: int = 2) -> RequirementGraph:
        """
        生成需求树知识图谱

        Args:
            seed_requirement_node_id: 种子需求节点 ID（knowledge_requirement_tree.node_id）
            scope: 作用域
            max_depth: 最大展开深度

        Returns:
            RequirementGraph: 图谱对象
        """
        logger.info(f"Generating requirement graph: seed={seed_requirement_node_id}, scope={scope}, max_depth={max_depth}")

        graph = RequirementGraph(seed_requirement_node_id, "", scope, max_depth)

        try:
            # Step 1: 查种子需求节点
            seed_node_data = db.session.query(KNOWLEDGE_REQUIREMENT_TREE).filter(
                KNOWLEDGE_REQUIREMENT_TREE.node_id == seed_requirement_node_id,
                KNOWLEDGE_REQUIREMENT_TREE.scope == scope,
                KNOWLEDGE_REQUIREMENT_TREE.effective_flag == "Y",
                KNOWLEDGE_REQUIREMENT_TREE.level == 3,
            ).first()

            if not seed_node_data:
                graph.status = 'failed'
                graph.error_message = f"Requirement node {seed_requirement_node_id} not found in scope {scope}"
                return graph

            # 构建种子名称
            rdc_id = seed_node_data.rdc_id or ""
            title = seed_node_data.title or ""
            seed_name = f"{rdc_id} | {title}" if rdc_id else title
            graph.seed_requirement_name = seed_name

            # Step 2: 添加种子节点 (level=0, source_type=auto)
            seed_graph_node = RequirementGraphNode(
                node_id=f"req_{seed_requirement_node_id}",
                name=seed_name,
                node_type=NodeType.MARKET_REQUIREMENT,
                url=seed_node_data.market_req_url or "",
                tree_node_id=seed_requirement_node_id,
                raw_data={
                    'rdc_id': rdc_id,
                    'title': title,
                    'status': seed_node_data.status or '',
                    'main_domain': seed_node_data.main_domain or '',
                    'urls': [seed_node_data.market_req_url] if seed_node_data.market_req_url else [],
                },
                source_type='auto',
                level=0,
                expanded=True,
            )
            graph.add_node(seed_graph_node)

            # Step 2.1: 从 RDC InOne API 获取子级 PR (level=1)
            if rdc_id:
                try:
                    repo = _get_repository()
                    child_prs = repo.get_child_prs(rdc_id)
                    if child_prs:
                        pr_ids = [pr['id'] for pr in child_prs]
                        pr_details = repo.get_pr_details(pr_ids)
                        pr_detail_map = {d['id']: d for d in pr_details}

                        for pr_idx, pr_info in enumerate(child_prs):
                            pr_id = pr_info['id']
                            detail = pr_detail_map.get(pr_id, {})
                            logger.debug(f"PR详情: {detail}")
                            pr_node = RequirementGraphNode(
                                node_id=f"pr_{seed_requirement_node_id}_{pr_idx}",
                                name=pr_info['title'],
                                node_type=NodeType.PRODUCT_REQUIREMENT,
                                url=f"https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/{pr_id}" if pr_id else "",
                                tree_node_id=seed_requirement_node_id,
                                raw_data={
                                    'rdc_id': pr_id,
                                    'system_areapath': detail.get('system_areapath', ''),
                                    'detail_design_url': detail.get('detail_design_url', ''),
                                    'reuse_degree': detail.get('reuse_degree', ''),
                                    'development_type': detail.get('development_type', ''),
                                    'detail_category': detail.get('detail_category', ''),
                                    'urls': [],
                                },
                                source_type='auto',
                                level=1,
                            )
                            graph.add_node(pr_node)
                            graph.add_edge(RequirementGraphEdge(
                                edge_id=f"edge_{seed_requirement_node_id}_relates_to_pr_{pr_idx}",
                                source=seed_graph_node.id,
                                target=pr_node.id,
                                relation_type=RelationType.RELATES_TO,
                                source_type='auto',
                            ))
                            logger.debug(f"PR system_areapath: {detail.get('system_areapath', '')}")
                except Exception as e:
                    logger.warning(f"获取子级 PR 失败：{e}")

            # Step 2.2: 从 PR 的 system_areapath 推导 skill 节点 (level=2)
            # 遍历已添加的 PR 节点，为每个 PR 根据其 system_areapath 添加对应的 skill 节点
            print("=" * 60)
            print("[Step 2.2] 开始为 PR 节点添加开发技能 skill 节点")
            skill_pr_count = 0
            for pr_node in list(graph.nodes.values()):
                if pr_node.type != NodeType.PRODUCT_REQUIREMENT:
                    continue

                system_areapath = pr_node.raw_data.get('system_areapath', '')
                print(f"[Step 2.2] PR: {pr_node.name}, rdc_id={pr_node.raw_data.get('rdc_id', '')}, system_areapath='{system_areapath}'")
                logger.debug(f"PR system_areapath: {system_areapath}")
                if not system_areapath:
                    print(f"[Step 2.2]   跳过：无 system_areapath")
                    continue

                # 使用固定入口 URL，不再根据 system_areapath 查映射表
                # skillm_url = get_skillm_page_url(system_areapath)  # 旧逻辑已废弃
                skillm_url = SKILLM_ROOT_URL
                print(f"[Step 2.2]   使用固定入口 URL: {skillm_url}")

                # 从开发技能库提取技能列表
                # 首先检查是否有 detail_category
                raw_detail_category = pr_node.raw_data.get('detail_category', '')
                print(f"[Step 2.2]   raw_detail_category='{raw_detail_category}'")

                # 如果没有 detail_category，直接跳过
                if not raw_detail_category:
                    print(f"[Step 2.2]   跳过：无 detail_category")
                    logger.info(f"PR {pr_node.raw_data.get('rdc_id', '')} 没有 detail_category，跳过 skill 节点查找")
                    continue

                # 根据 PR 的 reuse_degree 判断是否为配置化或微范式
                reuse_degree = pr_node.raw_data.get('reuse_degree', '')
                print(f"[Step 2.2]   reuse_degree='{reuse_degree}'")

                # 只有当 reuse_degree 包含"配置化"或"微范式"时才需要查询 SKILL
                if not reuse_degree or ('配置化' not in reuse_degree and '微范式' not in reuse_degree):
                    print(f"[Step 2.2]   跳过：reuse_degree 不包含'配置化'或'微范式'")
                    logger.info(f"PR {pr_node.raw_data.get('rdc_id', '')} 的 reuse_degree '{reuse_degree}' 不是配置化或微范式，跳过 skill 节点查找")
                    continue

                # 预处理 detail_category：去掉前面的数字和短横线，只保留后面的文本
                # 例如："004001-MIM 接口变更类" -> "MIM 接口变更类"
                detail_category = re.sub(r'^\d+-', '', raw_detail_category)
                print(f"[Step 2.2]   detail_category(预处理后)='{detail_category}'")

                try:
                    # 传入 system_areapath 用于领域匹配
                    print(f"[Step 2.2]   调用 knowledge_skill_extract(skillm_url, detail_category='{detail_category}', system_areapath='{system_areapath}')")
                    skill_result = knowledge_skill_extract(skillm_url, detail_category, system_areapath)
                    print(f"[Step 2.2]   skill_result.success={skill_result.get('success')}, skills数量={len(skill_result.get('skills', []))}")
                    if not skill_result.get('success'):
                        print(f"[Step 2.2]   提取失败：{skill_result}")
                        logger.warning(f"从开发技能库提取技能失败：{skillm_url}")
                        continue

                    skills = skill_result.get('skills', [])
                    # 使用匹配到的页面 URL（如果有的话）
                    matched_url = skill_result.get('matched_url', skillm_url)
                    print(f"[Step 2.2]   matched_url='{matched_url}'")

                    # 为每个技能创建节点
                    for skill_idx, skill_info in enumerate(skills):
                        skill_name = skill_info.get('skill_name', '')
                        skill_url = skill_info.get('skill_url', matched_url)
                        print(f"[Step 2.2]   skill[{skill_idx}]: skill_name='{skill_name}', skill_url='{skill_url}'")

                        if not skill_name:
                            continue

                        skill_node_id = f"skill_{seed_requirement_node_id}_{pr_node.id.split('_')[-1]}_{skill_idx}"
                        skill_node = RequirementGraphNode(
                            node_id=skill_node_id,
                            name=skill_name,
                            node_type=NodeType.SKILL,
                            url=skill_url,
                            tree_node_id=seed_requirement_node_id,
                            raw_data={
                                'skill_name': skill_name,
                                'system_areapath': system_areapath,
                                'detail_category': detail_category,
                                'skillm_url': skillm_url,
                                'matched_url': matched_url,
                                'urls': [skill_url] if skill_url else [],
                                # 绑定到对应的 PR 节点
                                'bound_pr_node_id': pr_node.id,
                                'bound_pr_rdc_id': pr_node.raw_data.get('rdc_id', ''),
                                'bound_pr_title': pr_node.name,
                            },
                            source_type='auto',
                            level=2,
                        )
                        graph.add_node(skill_node)

                        # 添加边：PR → Skill，关系类型 relates_to
                        graph.add_edge(RequirementGraphEdge(
                            edge_id=f"edge_{pr_node.id}_relates_to_skill_{skill_idx}",
                            source=pr_node.id,
                            target=skill_node.id,
                            relation_type=RelationType.RELATES_TO,
                            source_type='auto',
                        ))

                    skill_pr_count += 1
                    logger.info(f"为 PR {pr_node.raw_data.get('rdc_id', '')} 添加了 {len(skills)} 个 skill 节点")

                except Exception as e:
                    print(f"[Step 2.2]   异常：{e}")
                    logger.warning(f"为 PR {pr_node.raw_data.get('rdc_id', '')} 添加 skill 节点失败：{e}")

            print(f"[Step 2.2] 完成，共为 {skill_pr_count} 个 PR 添加了 skill 节点")
            print("=" * 60)

            # Step 3: 从 instance_url 推导需求实例化节点 (level=1)
            instance_url = seed_node_data.instance_url
            inst_node = None
            print(f"[Step 3] instance_url='{instance_url}', type={type(instance_url).__name__}")
            if instance_url and instance_url.strip():
                # 先提取页面数据，获取 page_title 用于节点名称
                extract_result = knowledge_requirement_instance_extract(instance_url)
                inst_page_title = extract_result.get('page_title', '')
                inst_name = inst_page_title if inst_page_title else (f"需求实例化: {rdc_id}" if rdc_id else "需求实例化")

                inst_node = RequirementGraphNode(
                    node_id=f"req_inst_{seed_requirement_node_id}",
                    name=inst_name,
                    node_type=NodeType.REQUIREMENT_INSTANCE,
                    url=instance_url,
                    tree_node_id=seed_requirement_node_id,
                    raw_data={'urls': [instance_url]},
                    source_type='auto',
                    level=1,
                )
                graph.add_node(inst_node)
                print(f"[Step 3] inst_node 创建成功: id={inst_node.id}, name='{inst_node.name}'")

                graph.add_edge(RequirementGraphEdge(
                    edge_id=f"edge_{seed_requirement_node_id}_relates_to_inst",
                    source=seed_graph_node.id,
                    target=inst_node.id,
                    relation_type=RelationType.RELATES_TO,
                    source_type='auto',
                ))

                # Step 3.1: 从需求实例化页面提取特性和章节 (level=2)

                # 特性节点：实例化 → 特性，关系类型 affects（波及）
                for feat_idx, feat_name in enumerate(extract_result.get('features', [])):
                    feat_node = RequirementGraphNode(
                        node_id=f"feat_{seed_requirement_node_id}_{feat_idx}",
                        name=feat_name,
                        node_type=NodeType.FEATURE,
                        url=instance_url,
                        tree_node_id=seed_requirement_node_id,
                        raw_data={
                            'feature_name': feat_name,
                            'urls': [instance_url],
                        },
                        source_type='auto',
                        level=2,
                    )
                    graph.add_node(feat_node)

                    graph.add_edge(RequirementGraphEdge(
                        edge_id=f"edge_{seed_requirement_node_id}_affects_feat_{feat_idx}",
                        source=inst_node.id,
                        target=feat_node.id,
                        relation_type=RelationType.AFFECTS,
                        source_type='auto',
                    ))

                # 章节节点：实例化 → 章节，关系类型 contains（包含）
                for sec_idx, sec_data in enumerate(extract_result.get('sections', [])):
                    sec_node = RequirementGraphNode(
                        node_id=f"sec_{seed_requirement_node_id}_{sec_idx}",
                        name=sec_data.get('section_title', ''),
                        node_type=NodeType.SECTION,
                        url=instance_url,
                        tree_node_id=seed_requirement_node_id,
                        raw_data={
                            'section_type': sec_data.get('section_type', ''),
                            'raw_html': sec_data.get('raw_html', ''),
                            'urls': [instance_url],
                        },
                        source_type='auto',
                        level=2,
                    )
                    graph.add_node(sec_node)

                    graph.add_edge(RequirementGraphEdge(
                        edge_id=f"edge_{seed_requirement_node_id}_contains_sec_{sec_idx}",
                        source=inst_node.id,
                        target=sec_node.id,
                        relation_type=RelationType.CONTAINS,
                        source_type='auto',
                    ))

                # Step 3.2: 从 knowledge_req_analysis_design_skill 表查询需求分析技能 (level=2)
                # 根据 instance_url 匹配 page_link，汇总为一个"需求分析技能"节点
                print("=" * 60)
                print("[Step 3.2] 开始查询需求分析技能")
                print(f"[Step 3.2] instance_url='{instance_url}'")
                try:
                    inst_skill_records = query_req_analysis_design_skills_by_page_link(instance_url, know_type=1)
                    print(f"[Step 3.2] 查询到 {len(inst_skill_records)} 条记录")
                    if inst_skill_records:
                        # 汇总所有 use_skill，并构建完整记录列表
                        all_inst_skills = {}
                        inst_skill_record_list = []
                        for rec_idx, record in enumerate(inst_skill_records):
                            use_skill = record.get('use_skill', {})
                            print(f"[Step 3.2]   record[{rec_idx}]: chapter_name='{record.get('chapter_name', '')}', know_type={record.get('know_type', '')}, use_skill={use_skill}")
                            if isinstance(use_skill, dict):
                                all_inst_skills.update(use_skill)
                            inst_skill_record_list.append({
                                'id': record.get('id'),
                                'mrName': record.get('mr_name', ''),
                                'mrLink': record.get('mr_link', ''),
                                'pageName': record.get('page_name', ''),
                                'pageLink': record.get('page_link', ''),
                                'chapterName': record.get('chapter_name', ''),
                                'useSkill': record.get('use_skill', {}),
                                'knowType': record.get('know_type', 1),
                                'accumulateBusinessKnowledge': record.get('accumulate_business_knowledge', {}),
                                'knowledgeContent': record.get('knowledge_content', ''),
                            })

                        print(f"[Step 3.2] 汇总后技能数量: {len(all_inst_skills)}, 完整记录数: {len(inst_skill_record_list)}")

                        inst_skill_node = RequirementGraphNode(
                            node_id=f"req_inst_skill_{seed_requirement_node_id}",
                            name='需求分析技能',
                            node_type=NodeType.REQUIREMENT_ANALYSIS_SKILL,
                            url=instance_url,
                            tree_node_id=seed_requirement_node_id,
                            raw_data={
                                'skills': all_inst_skills,
                                'record_count': len(inst_skill_records),
                                'records': inst_skill_record_list,
                                'urls': [instance_url],
                            },
                            source_type='auto',
                            level=2,
                        )
                        graph.add_node(inst_skill_node)
                        print(f"[Step 3.2] 添加节点: id={inst_skill_node.id}, name='{inst_skill_node.name}', type={inst_skill_node.type}")

                        graph.add_edge(RequirementGraphEdge(
                            edge_id=f"edge_{seed_requirement_node_id}_relates_to_inst_skill",
                            source=inst_node.id,
                            target=inst_skill_node.id,
                            relation_type=RelationType.RELATES_TO,
                            source_type='auto',
                        ))
                        print(f"[Step 3.2] 添加边: {inst_node.id} → {inst_skill_node.id}")
                        logger.info(f"为需求实例化节点添加了需求分析技能，包含 {len(all_inst_skills)} 个技能")
                    else:
                        print(f"[Step 3.2] 无匹配记录，跳过需求分析技能节点")
                except Exception as e:
                    print(f"[Step 3.2] 异常：{e}")
                    logger.warning(f"查询需求分析技能失败：{e}")
                print("=" * 60)

            # Step 4: 从 icenter_solution_urls 推导需求方案节点 (level=1)
            # 数据来源：优先使用入库时 iCenter 已补充的 icenter_solution_urls（列表）
            # 若为空，则从 instance_url 动态提取方案子页面
            # 无论多少个 URL，只显示一个需求方案节点，多 URL 放 raw_data 供抽屉展示
            icenter_solution_urls = seed_node_data.icenter_solution_urls
            print(f"[Step 4] icenter_solution_urls={icenter_solution_urls}, type={type(icenter_solution_urls).__name__}")
            # 确保 icenter_solution_urls 是列表类型，防止数据库 JSON 字段被反序列化为字符串或其他类型
            if not isinstance(icenter_solution_urls, list):
                print(f"[Step 4] WARNING: icenter_solution_urls 不是 list 类型，重置为空列表")
                icenter_solution_urls = []

            # 如果 icenter_solution_urls 为空但有 instance_url，尝试动态提取方案链接
            if not icenter_solution_urls and instance_url and instance_url.strip():
                print(f"[Step 4] icenter_solution_urls 为空，尝试从 instance_url 动态提取方案链接...")
                try:
                    solutions = fetch_requirement_solutions(instance_url)
                    if solutions:
                        icenter_solution_urls = [s["url"] for s in solutions]
                        print(f"[Step 4] 动态提取到 {len(icenter_solution_urls)} 个方案链接: {icenter_solution_urls}")
                    else:
                        print(f"[Step 4] 动态提取未找到方案链接")
                except Exception as e:
                    print(f"[Step 4] 动态提取方案链接异常: {e}")
                    logger.warning(f"动态提取方案链接失败: {e}")

            solution_status = seed_node_data.solution_status
            if icenter_solution_urls:
                display_url = icenter_solution_urls[0]
                # 先提取方案页面数据，获取 page_title 用于节点名称
                sol_extract_result = knowledge_requirement_solution_extract(display_url)
                sol_page_title = sol_extract_result.get('page_title', '')
                sol_name = sol_page_title if sol_page_title else (f"需求方案: {solution_status}" if solution_status else "需求方案")

                sol_node = RequirementGraphNode(
                    node_id=f"req_sol_{seed_requirement_node_id}",
                    name=sol_name,
                    node_type=NodeType.REQUIREMENT_SOLUTION,
                    url=display_url,
                    tree_node_id=seed_requirement_node_id,
                    raw_data={
                        'solution_status': solution_status or '',
                        'urls': icenter_solution_urls or [],
                    },
                    source_type='auto',
                    level=1,
                )
                graph.add_node(sol_node)

                # 校验边：对比 RDC 的 solution_doc_url 与 iCenter 的 icenter_solution_urls 是否一致
                # 通过解析 URL 中的 space_id 和 content_id 进行比较，而非字符串精确比较
                solution_doc_url = seed_node_data.solution_doc_url or ""
                icenter_solutions = icenter_solution_urls or []
                if solution_doc_url.strip():
                    is_matched = _match_by_space_and_content_id(solution_doc_url.strip(), icenter_solutions)
                    verify_label = "匹配" if is_matched else "不匹配"
                else:
                    verify_label = "不匹配"
                graph.add_edge(RequirementGraphEdge(
                    edge_id=f"edge_{seed_requirement_node_id}_verifies_sol",
                    source=seed_graph_node.id,
                    target=sol_node.id,
                    relation_type=RelationType.VERIFIES,
                    relation_label=verify_label,
                    source_type='auto',
                    raw_data={
                        'solution_doc_url': solution_doc_url.strip(),
                        'icenter_solution_urls': icenter_solutions,
                    },
                ))

                # 边：如果有实例化节点，从实例化连到方案；否则从种子连到方案
                print(f"[Step 4] edge_source 判断: inst_node={inst_node}, inst_node.id={inst_node.id if inst_node else 'N/A'}")
                edge_source = inst_node.id if inst_node else seed_graph_node.id
                graph.add_edge(RequirementGraphEdge(
                    edge_id=f"edge_{seed_requirement_node_id}_relates_to_sol",
                    source=edge_source,
                    target=sol_node.id,
                    relation_type=RelationType.RELATES_TO,
                    source_type='auto',
                ))

                # Step 5: 从 icenter_component_designs 提取组件功能设计 (level=2)
                # 数据来源：优先使用入库时 iCenter 已补充的 icenter_component_designs（JSON）
                # 若为空，则从方案链接动态提取组件功能设计子页面
                # 格式: {"方案URL1": ["组件功能设计URL1", ...], "方案URL2": [...]}
                icenter_component_designs = seed_node_data.icenter_component_designs
                print(f"[Step 5] icenter_component_designs={icenter_component_designs}, type={type(icenter_component_designs).__name__}")

                # 如果 icenter_component_designs 为空但有方案链接，尝试动态提取组件功能设计
                if (not icenter_component_designs or not isinstance(icenter_component_designs, dict)) and icenter_solution_urls:
                    print(f"[Step 5] icenter_component_designs 为空，尝试从方案链接动态提取组件功能设计...")
                    icenter_component_designs = {}
                    for sol_url in icenter_solution_urls:
                        try:
                            designs = fetch_component_designs(sol_url)
                            if designs:
                                icenter_component_designs[sol_url] = [d["url"] for d in designs]
                                print(f"[Step 5] 从方案 {sol_url} 动态提取到 {len(designs)} 个组件功能设计")
                        except Exception as e:
                            print(f"[Step 5] 动态提取组件功能设计异常, sol_url={sol_url}: {e}")
                            logger.warning(f"动态提取组件功能设计失败, sol_url={sol_url}: {e}")
                    if not icenter_component_designs:
                        print(f"[Step 5] 动态提取未找到组件功能设计")
                        icenter_component_designs = None

                if icenter_component_designs and isinstance(icenter_component_designs, dict):
                    all_design_urls = []
                    for sol_url, design_urls in icenter_component_designs.items():
                        if isinstance(design_urls, list):
                            all_design_urls.extend(design_urls)

                    for idx, design_url in enumerate(all_design_urls):
                        # 先提取页面数据，获取 page_title 用于节点名称
                        cd_extract_result = knowledge_component_design_extract(design_url)
                        cd_page_title = cd_extract_result.get('page_title', '')
                        cd_name = cd_page_title if cd_page_title else (design_url if design_url else f"组件功能设计{idx + 1}")

                        cd_node_id = f"comp_des_{seed_requirement_node_id}_{idx}"
                        cd_node = RequirementGraphNode(
                            node_id=cd_node_id,
                            name=cd_name,
                            node_type=NodeType.COMPONENT_DESIGN,
                            url=design_url,
                            raw_data={
                                'icenter_component_designs': icenter_component_designs,
                                'urls': [design_url] if design_url else [],
                            },
                            source_type='auto',
                            level=2,
                        )
                        graph.add_node(cd_node)

                        graph.add_edge(RequirementGraphEdge(
                            edge_id=f"edge_{seed_requirement_node_id}_relates_to_cd_{idx}",
                            source=sol_node.id,
                            target=cd_node.id,
                            relation_type=RelationType.RELATES_TO,
                            source_type='auto',
                        ))

                        # Step 5.1: 从组件功能设计页面提取章节 (level=3)
                        for cd_sec_idx, cd_sec_data in enumerate(cd_extract_result.get('sections', [])):
                            cd_sec_node = RequirementGraphNode(
                                node_id=f"cd_sec_{seed_requirement_node_id}_{idx}_{cd_sec_idx}",
                                name=cd_sec_data.get('section_title', ''),
                                node_type=NodeType.SECTION,
                                url=design_url,
                                tree_node_id=seed_requirement_node_id,
                                raw_data={
                                    'section_type': cd_sec_data.get('section_type', ''),
                                    'raw_html': cd_sec_data.get('raw_html', ''),
                                    'urls': [design_url] if design_url else [],
                                },
                                source_type='auto',
                                level=3,
                            )
                            graph.add_node(cd_sec_node)

                            graph.add_edge(RequirementGraphEdge(
                                edge_id=f"edge_{seed_requirement_node_id}_contains_cd_sec_{idx}_{cd_sec_idx}",
                                source=cd_node.id,
                                target=cd_sec_node.id,
                                relation_type=RelationType.CONTAINS,
                                source_type='auto',
                            ))

                # Step 5.2: 从需求方案页面提取组件和章节 (level=2)

                # 组件节点：方案 → 组件，关系类型 affects（波及）
                for comp_idx, comp_name in enumerate(sol_extract_result.get('components', [])):
                    comp_node = RequirementGraphNode(
                        node_id=f"comp_{seed_requirement_node_id}_{comp_idx}",
                        name=comp_name if comp_name else f"组件{comp_idx + 1}",
                        node_type=NodeType.COMPONENT,
                        url=display_url,
                        tree_node_id=seed_requirement_node_id,
                        raw_data={
                            'component_name': comp_name,
                            'urls': [display_url],
                        },
                        source_type='auto',
                        level=2,
                    )
                    graph.add_node(comp_node)

                    graph.add_edge(RequirementGraphEdge(
                        edge_id=f"edge_{seed_requirement_node_id}_affects_comp_{comp_idx}",
                        source=sol_node.id,
                        target=comp_node.id,
                        relation_type=RelationType.AFFECTS,
                        source_type='auto',
                    ))

                # 章节节点：方案 → 章节，关系类型 contains（包含）
                for sol_sec_idx, sol_sec_data in enumerate(sol_extract_result.get('sections', [])):
                    sol_sec_node = RequirementGraphNode(
                        node_id=f"sol_sec_{seed_requirement_node_id}_{sol_sec_idx}",
                        name=sol_sec_data.get('section_title', ''),
                        node_type=NodeType.SECTION,
                        url=display_url,
                        tree_node_id=seed_requirement_node_id,
                        raw_data={
                            'section_type': sol_sec_data.get('section_type', ''),
                            'raw_html': sol_sec_data.get('raw_html', ''),
                            'urls': [display_url],
                        },
                        source_type='auto',
                        level=2,
                    )
                    graph.add_node(sol_sec_node)

                    graph.add_edge(RequirementGraphEdge(
                        edge_id=f"edge_{seed_requirement_node_id}_contains_sol_sec_{sol_sec_idx}",
                        source=sol_node.id,
                        target=sol_sec_node.id,
                        relation_type=RelationType.CONTAINS,
                        source_type='auto',
                    ))

                # Step 5.3: 从 knowledge_req_analysis_design_skill 表查询方案设计技能 (level=2)
                # 根据 icenter_solution_urls 匹配 page_link，汇总为一个"方案设计技能"节点
                print("=" * 60)
                print("[Step 5.3] 开始查询方案设计技能")
                print(f"[Step 5.3] icenter_solution_urls={icenter_solution_urls}")
                try:
                    all_sol_skills = {}
                    all_sol_record_list = []
                    for sol_url in (icenter_solution_urls or []):
                        print(f"[Step 5.3]   查询 page_link='{sol_url}'")
                        sol_skill_records = query_req_analysis_design_skills_by_page_link(sol_url, know_type=2)
                        print(f"[Step 5.3]   查询到 {len(sol_skill_records)} 条记录")
                        for rec_idx, record in enumerate(sol_skill_records):
                            use_skill = record.get('use_skill', {})
                            print(f"[Step 5.3]     record[{rec_idx}]: chapter_name='{record.get('chapter_name', '')}', know_type={record.get('know_type', '')}, use_skill={use_skill}")
                            if isinstance(use_skill, dict):
                                all_sol_skills.update(use_skill)
                            all_sol_record_list.append({
                                'id': record.get('id'),
                                'mrName': record.get('mr_name', ''),
                                'mrLink': record.get('mr_link', ''),
                                'pageName': record.get('page_name', ''),
                                'pageLink': record.get('page_link', ''),
                                'chapterName': record.get('chapter_name', ''),
                                'useSkill': record.get('use_skill', {}),
                                'knowType': record.get('know_type', 2),
                                'accumulateBusinessKnowledge': record.get('accumulate_business_knowledge', {}),
                                'knowledgeContent': record.get('knowledge_content', ''),
                            })

                    print(f"[Step 5.3] 汇总后技能数量: {len(all_sol_skills)}, 完整记录数: {len(all_sol_record_list)}")

                    if all_sol_record_list:
                        sol_skill_node = RequirementGraphNode(
                            node_id=f"req_sol_skill_{seed_requirement_node_id}",
                            name='方案设计技能',
                            node_type=NodeType.SOLUTION_DESIGN_SKILL,
                            url=display_url,
                            tree_node_id=seed_requirement_node_id,
                            raw_data={
                                'skills': all_sol_skills,
                                'records': all_sol_record_list,
                                'urls': icenter_solution_urls or [],
                            },
                            source_type='auto',
                            level=2,
                        )
                        graph.add_node(sol_skill_node)
                        print(f"[Step 5.3] 添加节点: id={sol_skill_node.id}, name='{sol_skill_node.name}', type={sol_skill_node.type}")

                        graph.add_edge(RequirementGraphEdge(
                            edge_id=f"edge_{seed_requirement_node_id}_relates_to_sol_skill",
                            source=sol_node.id,
                            target=sol_skill_node.id,
                            relation_type=RelationType.RELATES_TO,
                            source_type='auto',
                        ))
                        print(f"[Step 5.3] 添加边: {sol_node.id} → {sol_skill_node.id}")
                        logger.info(f"为需求方案节点添加了方案设计技能，包含 {len(all_sol_skills)} 个技能")
                    else:
                        print(f"[Step 5.3] 无匹配记录，跳过方案设计技能节点")
                except Exception as e:
                    print(f"[Step 5.3] 异常：{e}")
                    logger.warning(f"查询方案设计技能失败：{e}")
                print("=" * 60)

            # Step 6: 标记未展开节点 (is_expanded=0)
            # level < max_depth 且为可继续展开的类型
            for node in list(graph.nodes.values()):
                if node.level < max_depth and node.type in [
                    NodeType.PRODUCT_REQUIREMENT,
                    NodeType.REQUIREMENT_INSTANCE,
                    NodeType.REQUIREMENT_SOLUTION,
                    NodeType.COMPONENT_DESIGN,
                    NodeType.FEATURE,
                    NodeType.SECTION,
                    NodeType.COMPONENT,
                    NodeType.SKILL,
                    NodeType.REQUIREMENT_ANALYSIS_SKILL,
                    NodeType.SOLUTION_DESIGN_SKILL,
                ]:
                    node.expanded = False

            # 完成图谱生成
            graph.status = 'completed'
            graph.generated_at = datetime.now()
            graph.expires_at = datetime.now() + timedelta(hours=24)

            # 统计skill节点数量
            skill_nodes_count = sum(1 for node in graph.nodes.values() if node.type == NodeType.SKILL)
            logger.info(f"Requirement graph generated: {len(graph.nodes)} nodes, {len(graph.edges)} edges, 其中skill节点={skill_nodes_count}")

        except Exception as e:
            logger.error(f"Error generating requirement graph: {str(e)}")
            graph.status = 'failed'
            graph.error_message = str(e)

        return graph

    def cache_graph_to_db(self, graph: RequirementGraph, operator_person: str = ""):
        """
        缓存图谱到数据库

        Args:
            graph: 图谱对象
            operator_person: 操作人
        """
        try:
            logger.info(f"Caching requirement graph: {graph.seed_requirement_node_id}")

            graph_data = graph.to_dict()

            # 保存图谱主表
            save_result = save_requirement_graph_to_db(graph_data, operator_person)

            if save_result.get('status') == 'error':
                logger.error(f"Failed to save requirement graph: {save_result.get('message')}")
                return

            graph_id = save_result.get('graph_id')
            logger.info(f"Requirement graph saved with ID: {graph_id}")

            # 保存节点
            if graph.nodes:
                nodes_data = [node.to_dict() for node in graph.nodes.values()]
                save_requirement_graph_nodes(graph_id, nodes_data)
                logger.info(f"Saved {len(nodes_data)} nodes")

            # 保存边
            if graph.edges:
                edges_data = [edge.to_dict() for edge in graph.edges]
                save_requirement_graph_edges(graph_id, edges_data)
                logger.info(f"Saved {len(edges_data)} edges")

        except Exception as e:
            logger.error(f"Error caching requirement graph: {str(e)}")
            raise

    def get_cached_graph(self, seed_requirement_node_id: str, max_depth: int = 2) -> Optional[RequirementGraph]:
        """
        从数据库获取缓存的图谱

        Args:
            seed_requirement_node_id: 种子需求节点 ID
            max_depth: 最大深度

        Returns:
            RequirementGraph or None
        """
        try:
            cached_graph = query_cached_requirement_graph(seed_requirement_node_id, max_depth)

            if not cached_graph:
                return None

            # 重建图谱对象
            graph = RequirementGraph(
                seed_requirement_node_id=cached_graph.seed_requirement_node_id,
                seed_requirement_name=cached_graph.seed_requirement_name,
                scope=cached_graph.scope,
                max_depth=cached_graph.max_depth
            )
            graph.status = cached_graph.status
            graph.error_message = cached_graph.error_message or ''
            graph.generated_at = cached_graph.generated_at
            graph.expires_at = cached_graph.expires_at

            # 重建节点
            nodes = query_requirement_graph_nodes(cached_graph.id)
            for node_data in nodes:
                node = RequirementGraphNode(
                    node_id=node_data['node_id'],
                    name=node_data['node_name'],
                    node_type=node_data['node_type'],
                    tree_node_id=node_data.get('tree_node_id', ''),
                    raw_data=node_data.get('raw_data', {}),
                    source_type=node_data.get('source_type', 'auto'),
                    level=node_data.get('level', 1),
                    expanded=bool(node_data.get('is_expanded', 0)),
                    position_x=float(node_data['position_x']) if node_data.get('position_x') else None,
                    position_y=float(node_data['position_y']) if node_data.get('position_y') else None,
                )
                # 从 raw_data 恢复 url
                if node_data.get('raw_data') and isinstance(node_data['raw_data'], dict):
                    urls = node_data['raw_data'].get('urls', [])
                    node.url = urls[0] if urls else ''
                graph.nodes[node.id] = node

            # 重建边
            edges = query_requirement_graph_edges(cached_graph.id)
            for edge_data in edges:
                edge = RequirementGraphEdge(
                    edge_id=edge_data['edge_id'],
                    source=edge_data['source_node_id'],
                    target=edge_data['target_node_id'],
                    relation_type=edge_data['relation_type'],
                    relation_label=edge_data.get('relation_label', ''),
                    source_type=edge_data.get('source_type', 'auto'),
                    raw_data=edge_data.get('raw_data', {}),
                )
                graph.edges.append(edge)

            return graph

        except Exception as e:
            logger.error(f"Error getting cached requirement graph: {str(e)}")
            return None


# 全局服务实例
_graph_service_instance = None


def get_requirement_graph_service() -> RequirementGraphService:
    """获取图谱服务单例"""
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = RequirementGraphService()
    return _graph_service_instance


# ============================================================================
# 技能与 PR 绑定关系统计服务
# ============================================================================

def get_pr_skill_mapping(graph_data: dict) -> list:
    """
    从图谱数据中提取所有 PR 和它们对应的 skill 绑定关系
    
    Args:
        graph_data: 图谱数据字典（来自 RequirementGraph.to_dict()）
        
    Returns:
        list: PR-Skill 映射列表，每项包含：
            - prNodeId: PR 节点 ID
            - prRdcId: PR RDC ID
            - prTitle: PR 标题
            - prType: PR 类型（微范式/配置化）
            - skills: 对应的 skill 列表，每项包含 skill_name 和 skill_url
    """
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    # 构建节点索引
    node_map = {}
    for node in nodes:
        node_map[node['id']] = node
    
    # 找出所有 PR 节点
    pr_nodes = [n for n in nodes if n.get('type') == NodeType.PRODUCT_REQUIREMENT]
    
    # 找出所有 skill 节点
    skill_nodes = [n for n in nodes if n.get('type') == NodeType.SKILL]
    
    # 构建 PR → Skill 的映射（通过边关系）
    pr_to_skills = {}
    for edge in edges:
        if edge.get('relationType') == RelationType.RELATES_TO:
            source_id = edge.get('source')
            target_id = edge.get('target')
            
            # 检查是否是 PR → Skill 的边
            if source_id in node_map and target_id in node_map:
                source_node = node_map[source_id]
                target_node = node_map[target_id]
                
                if source_node.get('type') == NodeType.PRODUCT_REQUIREMENT and \
                   target_node.get('type') == NodeType.SKILL:
                    if source_id not in pr_to_skills:
                        pr_to_skills[source_id] = []
                    pr_to_skills[source_id].append(target_node)
    
    # 构建结果列表
    result = []
    for pr_node in pr_nodes:
        pr_raw_data = pr_node.get('rawData', {})
        pr_rdc_id = pr_raw_data.get('rdc_id', '')
        pr_title = pr_node.get('name', '')
        
        # 判断 PR 类型：根据 reuse_degree 或 development_type 字段
        # 微范式：reuse_degree 包含"微范式"或 development_type 包含"微范式"
        # 配置化：reuse_degree 包含"配置"或 development_type 包含"配置"
        reuse_degree = pr_raw_data.get('reuse_degree', '')
        development_type = pr_raw_data.get('development_type', '')
        pr_type = '未知'
        
        if '微范式' in reuse_degree or '微范式' in development_type:
            pr_type = '微范式'
        elif '配置' in reuse_degree or '配置' in development_type:
            pr_type = '配置化'
        
        # 获取该 PR 对应的 skills
        skills = []
        if pr_node['id'] in pr_to_skills:
            for skill_node in pr_to_skills[pr_node['id']]:
                skill_raw_data = skill_node.get('rawData', {})
                skills.append({
                    'skillName': skill_node.get('name', ''),
                    'skillUrl': skill_node.get('url', ''),
                    'skillNodeId': skill_node.get('id', ''),
                })
        
        result.append({
            'prNodeId': pr_node['id'],
            'prRdcId': pr_rdc_id,
            'prTitle': pr_title,
            'prType': pr_type,
            'skills': skills,
        })
    
    # 按 PR 类型排序：微范式在前，配置化其次，未知最后
    type_order = {'微范式': 0, '配置化': 1, '未知': 2}
    result.sort(key=lambda x: (type_order.get(x['prType'], 2), x['prRdcId']))
    
    return result
