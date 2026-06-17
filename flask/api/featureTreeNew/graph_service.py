"""
组件知识图谱服务
功能：生成、缓存、查询组件知识图谱
作者：AI Assistant
创建时间：2026-05-19
说明：本文件只包含业务逻辑，数据库操作全部在 data_model.py 中
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from sqlalchemy import or_
from componentTree.data_model import (
    KNOWLEDGE_COMPONENT_TREE,
    query_knowledge_component_tree_nodes,
    query_cached_graph,
    save_graph_to_db,
    save_graph_nodes,
    save_graph_edges,
    cache_component_section,
    query_graph_nodes,
    query_graph_edges,
)
from componentTree.component_know_daily_data import (
    is_valid_comp_tree_page_title_format,
    is_valid_module_page_title_format,
    is_valid_sub_comp_tree_page_title_format,
)
from componentTree.api_component_tree import _safe_icenter_children
from get_icenter import Icenter_content_html_get, Icenter_title_get
from electric_knowledge.data_model import db
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 节点类型和关系类型定义
# ============================================================================

class NodeType:
    """节点类型枚举"""
    COMPONENT = 'component'  # 组件
    MODULE = 'module'  # 模块
    SECTION = 'section'  # 章节
    DEPENDENT_COMPONENT = 'dependent_component'  # 依赖组件
    AFFECTED_FEATURE = 'affected_feature'  # 波及特性
    SKILL = 'skill'  # 知识技能（预留）


class RelationType:
    """关系类型枚举"""
    BELONGS_TO = 'belongs_to'  # 属于（组件→模块）
    CONTAINS = 'contains'  # 包含（组件→章节）
    DEPENDS_ON = 'depends_on'  # 依赖（组件→依赖组件）
    AFFECTS = 'affects'  # 影响（组件→波及特性）
    REQUIRES = 'requires'  # 需要（组件→知识技能，预留）


# 节点类型显示名称映射
NODE_TYPE_LABELS = {
    NodeType.COMPONENT: '组件',
    NodeType.MODULE: '模块',
    NodeType.SECTION: '章节',
    NodeType.DEPENDENT_COMPONENT: '依赖组件',
    NodeType.AFFECTED_FEATURE: '波及特性',
    NodeType.SKILL: '知识技能',
}

# 关系类型显示名称映射
RELATION_TYPE_LABELS = {
    RelationType.BELONGS_TO: '属于',
    RelationType.CONTAINS: '包含',
    RelationType.DEPENDS_ON: '依赖',
    RelationType.AFFECTS: '影响',
    RelationType.REQUIRES: '需要',
}


# ============================================================================
# 图谱数据模型
# ============================================================================

class GraphNode:
    """图谱节点"""
    
    def __init__(self, node_id: str, name: str, node_type: str, **kwargs):
        self.id = node_id
        self.name = name
        self.type = node_type
        self.expanded = kwargs.get('expanded', False)
        self.desc = kwargs.get('desc', '')
        self.url = kwargs.get('url', '')
        self.space_id = kwargs.get('space_id', '')
        self.content_id = kwargs.get('content_id', '')
        self.level = kwargs.get('level', 1)
        self.parent_component_id = kwargs.get('parent_component_id', '')
        self.position_x = kwargs.get('position_x')
        self.position_y = kwargs.get('position_y')
        self.page_status = kwargs.get('page_status', '')  # 页面状态：初始、已初审、修订中、已定稿
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'expanded': self.expanded,
            'desc': self.desc,
            'url': self.url,
            'spaceId': self.space_id,
            'contentId': self.content_id,
            'level': self.level,
            'positionX': self.position_x,
            'positionY': self.position_y,
            'parentComponentId': self.parent_component_id,
            'pageStatus': self.page_status,
        }
        
        # 为 section 类型节点添加 section_content 字段（用于缓存到 knowledge_component_section 表）
        if self.type == NodeType.SECTION:
            # 从 node_id 中提取 section_id: section_{component_id}_{section_id} -> {section_id}
            # 例如：section_7ab20ebe768611f0bcef311396d0e924_section_5_3_1_流程设计 -> section_5_3_1_流程设计
            section_id_raw = self.id
            if section_id_raw.startswith('section_') and self.parent_component_id:
                # 移除 'section_' 前缀和 component_id
                section_id_raw = section_id_raw[8:]  # 移除 'section_'
                if section_id_raw.startswith(self.parent_component_id + '_'):
                    section_id_raw = section_id_raw[len(self.parent_component_id) + 1:]
            
            result['section_id'] = section_id_raw
            result['section_title'] = self.name
            # 提取 section_type: 优先使用空格/连字符分割，纯中文标题使用完整标题
            if ' ' in self.name:
                result['section_type'] = self.name.split(' ')[0]
            elif '-' in self.name:
                result['section_type'] = self.name.split('-')[0]
            else:
                # 纯中文标题（如"组件对外接口"）使用完整标题作为 type
                result['section_type'] = self.name
            result['section_content'] = self.desc
        
        return result


class GraphEdge:
    """图谱边"""
    
    def __init__(self, edge_id: str, source: str, target: str, relation_type: str, **kwargs):
        self.id = edge_id
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.relation_label = kwargs.get('relation_label', RELATION_TYPE_LABELS.get(relation_type, ''))
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'relationType': self.relation_type,
            'relationLabel': self.relation_label,
        }


class ComponentGraph:
    """组件知识图谱"""
    
    def __init__(self, seed_component_id: str, seed_component_name: str, scope: str, max_depth: int = 2):
        self.seed_component_id = seed_component_id
        self.seed_component_name = seed_component_name
        self.scope = scope
        self.max_depth = max_depth
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.status = 'pending'
        self.error_message = ''
        self.generated_at = None
        self.expires_at = None
    
    def add_node(self, node: GraphNode):
        """添加节点（自动去重）"""
        if node.id not in self.nodes:
            self.nodes[node.id] = node
    
    def add_edge(self, edge: GraphEdge):
        """添加边"""
        self.edges.append(edge)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'seedComponentId': self.seed_component_id,
            'seedComponentName': self.seed_component_name,
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

class GraphService:
    """图谱生成服务类"""
    
    def __init__(self):
        pass
    
    def _parse_icenter_ids(self, page_url: str) -> Tuple[Optional[str], Optional[str]]:
        """从 iCenter URL 解析 spaceId 和 contentId"""
        if not page_url:
            return None, None
        
        # 匹配模式：https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{contentId}/view
        pattern = r'/space/([^/]+)/wiki/page/([^/]+)/view'
        match = re.search(pattern, page_url)
        if match:
            return match.group(1), match.group(2)
        
        # 兼容旧格式：https://i.zte.com.cn/wiki/page/{contentId}/view
        pattern_old = r'/wiki/page/([^/]+)/view'
        match_old = re.search(pattern_old, page_url)
        if match_old:
            return None, match_old.group(1)
        
        return None, None
    
    def _extract_cell_name_and_url(self, cell) -> Tuple[str, str]:
        """从单元格提取显示名与链接，优先使用 <a href>"""
        if not cell:
            return "", ""
        
        link = cell.find("a")
        if link:
            name = link.get_text(strip=True).replace("\ufeff", "")
            href = (link.get("href") or "").strip()
            if href and href.startswith("/"):
                href = f"https://i.zte.com.cn{href}"
            if href and not href.startswith(("http://", "https://")):
                href = ""
            if name:
                return name, href
        
        name = cell.get_text(strip=True).replace("\ufeff", "")
        return name, ""
    
    def _dedupe_related_items(self, items: List[Dict]) -> List[Dict]:
        """按名称去重，优先保留有链接的数据"""
        if not isinstance(items, list):
            return []
        
        deduped = []
        seen_index = {}
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            name = (item.get("name") or "").strip()
            url = (item.get("url") or "").strip()
            
            if not name:
                continue
            
            if name in seen_index:
                idx = seen_index[name]
                if not deduped[idx].get("url") and url:
                    deduped[idx]["url"] = url
                continue
            
            seen_index[name] = len(deduped)
            deduped.append({"name": name, "url": url})
        
        return deduped
    
    def _extract_page_status(self, page_url: str, node_type: str) -> str:
        """
        从 iCenter 页面提取页面状态
        
        Args:
            page_url: iCenter 页面 URL
            node_type: 节点类型，用于确定查找的 key
                - component/module/dependent_component: 查找 "页面状态"
                - affected_feature: 查找 "页面设计状态"
        
        Returns:
            str: 页面状态值（初始、已初审、修订中、已定稿）或空字符串
        """
        if not page_url:
            return ""
        
        # 根据节点类型确定查找的 key
        if node_type in [NodeType.COMPONENT, NodeType.MODULE, NodeType.DEPENDENT_COMPONENT]:
            status_key = "页面状态"
        elif node_type == NodeType.AFFECTED_FEATURE:
            status_key = "页面设计状态"
        else:
            # 其他类型节点不获取状态
            return ""
        
        try:
            page_html = Icenter_content_html_get(page_url)
            if not page_html:
                logger.warning(f"Failed to get HTML content from {page_url}")
                return ""
            
            soup = BeautifulSoup(page_html, "html.parser")
            table = soup.find("table")
            if not table:
                logger.warning(f"No table found in page {page_url}")
                return ""
            
            for tr in table.find_all("tr"):
                th = tr.find("th")
                if not th:
                    continue
                key = th.get_text(strip=True).replace("\ufeff", "")
                if key == status_key:
                    td = th.find_next_sibling("td")
                    if not td:
                        continue
                    # 处理 select 下拉框
                    select_tag = td.find("select")
                    if select_tag:
                        selected_option = select_tag.find("option", selected=True)
                        if selected_option:
                            return selected_option.get_text(strip=True).replace("\ufeff", "")
                    # 直接取文本
                    return td.get_text(strip=True).replace("\ufeff", "")
            
            logger.warning(f"Status key '{status_key}' not found in page {page_url}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting page status from {page_url}: {str(e)}")
            return ""
    
    def _find_module_for_component(self, component_node: Dict, all_nodes: List[Dict]) -> Optional[Dict]:
        """
        向上查找组件的所属模块
        通过 parent_id 递归向上查找最近的 node_type='module' 祖先节点
        """
        if not component_node:
            return None
        
        current_node = component_node
        visited = set()
        
        while current_node is not None:
            node_id = current_node.get('node_id') or current_node.get('id')
            if node_id in visited:
                logger.warning(f"Cycle detected while finding module for component {node_id}")
                break
            
            visited.add(node_id)
            
            node_type = current_node.get('node_type', '')
            if node_type == 'module':
                return current_node
            
            if node_type in ['root', 'category']:
                break
            
            parent_id = current_node.get('parent_id')
            if not parent_id:
                break
            
            parent_node = None
            for node in all_nodes:
                if node.get('node_id') == parent_id or node.get('id') == parent_id:
                    parent_node = node
                    break
            
            if not parent_node:
                break
            
            current_node = parent_node
        
        return None
    
    def _find_parent_component(self, node: Dict, all_nodes: List[Dict]) -> Optional[Dict]:
        """
        向上查找父组件（只用于子组件节点）
        子组件的父节点一定是组件（C 开头）
        
        Args:
            node: 子组件节点
            all_nodes: 所有节点列表
        
        Returns:
            父组件节点，如果找不到则返回 None
        """
        if not node:
            return None
        
        node_id = node.get('node_id') or node.get('id')
        node_title = node.get('title', '')
        parent_id = node.get('parent_id')
        
        logger.info(f"Finding parent component for sub-component: {node_title} (id={node_id})")
        
        # 方法 1: 从 all_nodes 中查找父节点
        if parent_id:
            for n in all_nodes:
                if (n.get('node_id') == parent_id or n.get('id') == parent_id):
                    parent_title = n.get('title', '')
                    # 验证父节点是否是组件（C 开头）
                    if is_valid_comp_tree_page_title_format(parent_title):
                        logger.info(f"  Found parent component: {parent_title}")
                        return n
                    else:
                        logger.info(f"  Parent is not a component: {parent_title}")
                        break
        
        # 方法 2: 如果 all_nodes 中没有，尝试通过 iCenter 接口查找
        # 这需要知道父节点的 URL，暂时不实现
        
        logger.warning(f"  Parent component not found for {node_title}")
        return None
    
    def _find_child_modules(self, component_node: Dict, all_nodes: List[Dict]) -> List[Dict]:
        """
        向下查找组件包含的模块
        通过调用 _safe_icenter_children 接口获取子节点，并使用标准验证函数判断是否为模块
        
        Args:
            component_node: 组件节点
            all_nodes: 所有节点列表（备用，当接口失败时使用）
        
        Returns:
            模块节点列表
        """
        if not component_node:
            return []
        
        component_id = component_node.get('node_id') or component_node.get('id')
        component_title = component_node.get('title', '')
        component_url = component_node.get('url', '')
        
        logger.info(f"Finding child modules for component: {component_title} (id={component_id})")
        
        child_modules = []
        
        # 方法 1: 通过 _safe_icenter_children 接口获取子节点（优先）
        if component_url:
            try:
                logger.info(f"  Calling _safe_icenter_children with URL: {component_url}")
                children_map = _safe_icenter_children(component_url)
                
                if children_map:
                    logger.info(f"  Found {len(children_map)} children via _safe_icenter_children")
                    
                    # 遍历子节点
                    for child_title, child_url in children_map.items():
                        # 判断是否为模块：主要依赖标题判断
                        is_module = False
                        match_reason = ""
                        
                        # 规则 1: 使用 is_valid_module_page_title_format 验证标题格式（Mxxx-xxx）
                        if is_valid_module_page_title_format(child_title):
                            is_module = True
                            match_reason = f"valid module title (Mxxx-xxx)"
                        
                        # 规则 2: 标题包含"模块"字样
                        elif '模块' in child_title:
                            is_module = True
                            match_reason = "contains '模块' keyword"
                        
                        if is_module:
                            logger.info(f"  ✓ Found child module [{match_reason}]: {child_title}")
                            # 构造节点对象
                            space_id, content_id = self._parse_icenter_ids(child_url)
                            child_modules.append({
                                'node_id': content_id,
                                'title': child_title,
                                'url': child_url,
                                'space_id': space_id,
                                'node_type': 'module',  # 明确标记为 module
                                'level': component_node.get('level', 0) + 1,
                                'parent_id': component_id,
                            })
                        else:
                            logger.info(f"  ✗ Skipping non-module: {child_title}")
                else:
                    logger.warning(f"  _safe_icenter_children returned empty children_map")
                    
            except Exception as e:
                logger.error(f"  _safe_icenter_children failed: {str(e)}")
                # 失败时回退到方法 2
        
        # 方法 2: 如果接口失败或返回空，从 all_nodes 中查找（兜底）
        if not child_modules:
            logger.info(f"  Fallback to searching all_nodes...")
            all_children = [node for node in all_nodes if node.get('parent_id', '') == component_id]
            logger.info(f"  Found {len(all_children)} child nodes in all_nodes")
            
            for node in all_children:
                node_title = node.get('title', '')
                node_type = node.get('node_type', '')
                
                # 判断是否为模块
                is_module = False
                match_reason = ""
                
                if is_valid_module_page_title_format(node_title):
                    is_module = True
                    match_reason = f"valid module title (Mxxx-xxx)"
                elif '模块' in node_title:
                    is_module = True
                    match_reason = "contains '模块' keyword"
                elif node_type == 'module':
                    is_module = True
                    match_reason = "node_type='module'"
                
                if is_module:
                    logger.info(f"  ✓ Found child module [{match_reason}]: {node_title}")
                    child_modules.append(node)
                else:
                    logger.debug(f"  ✗ Skipping non-module: {node_title} (type={node_type})")
        
        logger.info(f"Found {len(child_modules)} child modules for component {component_title}")
        if child_modules:
            logger.info(f"  Module titles: {[m['title'] for m in child_modules]}")
        return child_modules
    
    def _extract_sections_from_icenter(self, page_url: str, component_id: str) -> List[Dict]:
        """
        从 iCenter 页面提取目标章节及其内容
        目标章节：5.3.1 流程设计、5.7 FT测试设计、4 组件对外接口
        """
        sections = []
        
        if not page_url:
            return sections
        
        try:
            # 判断 URL 类型并获取 HTML
            is_ispace = 'i.zte.com.cn' in page_url or 'ispace' in page_url
            print(f"   🌐 URL 类型：{'iSpace' if is_ispace else 'iCenter'}")
            print(f"   📄 解析 URL: {page_url}")
            
            page_html = Icenter_content_html_get(page_url)
            if not page_html:
                print(f"   ❌ 获取 HTML 失败 (is_ispace={is_ispace})")
                logger.warning(f"Failed to get HTML from {page_url} (is_ispace={is_ispace})")
                return sections
            
            print(f"   ✅ 获取 HTML 成功，长度：{len(page_html)}")
            soup = BeautifulSoup(page_html, "html.parser")
            
            # 保留 SECTION_PATTERNS，只提取预定义的章节
            SECTION_PATTERNS = {
                '5.3.1 流程设计': r'流程设计',  # 匹配任何包含"流程设计"的标题
                '5.7 FT测试设计': r'FT测试设计',  # 匹配任何包含"FT 代码文件设计"的标题
                '4 组件对外接口': r'组件对外接口',  # 匹配任何包含"组件对外接口"的标题
            }
            
            heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
            
            found_sections = {}
            section_title_tags = {}  # 记录每个章节标题对应的标签节点
            
            print(f"   🔍 开始查找章节标题，总标题数：{len(soup.find_all(heading_tags))}")
            
            # 遍历所有 h1-h6 标题，找到所有目标章节
            checked_count = 0
            for tag in soup.find_all(heading_tags):
                text = tag.get_text(strip=True).replace("\ufeff", "")
                checked_count += 1
                
                for section_type, pattern in SECTION_PATTERNS.items():
                    if re.search(pattern, text):
                        print(f"      ✅ 匹配到章节：{section_type} -> '{text}' (pattern: {pattern}, level: {tag.name})")
                        if section_type not in found_sections:
                            found_sections[section_type] = {
                                'section_id': f"section_{section_type.replace('.', '_').replace(' ', '_')}",
                                'section_title': text,
                                'section_type': section_type,
                                'level': int(tag.name[1]),  # h1=1, h2=2, ..., h6=6
                            }
                            section_title_tags[section_type] = tag
                        break
            
            print(f"   📊 检查了 {checked_count} 个标题，找到 {len(found_sections)} 个章节：{list(found_sections.keys())}")
            
            # 第二遍：为每个章节提取内容
            for section_type, section_data in found_sections.items():
                title_tag = section_title_tags.get(section_type)
                if title_tag:
                    # 提取章节内容
                    section_content = self._extract_section_content(title_tag, soup)
                    section_data['section_content'] = section_content
                    section_data['content_word_count'] = len(section_content) if section_content else 0
                else:
                    section_data['section_content'] = ''
                    section_data['content_word_count'] = 0
            
            sections = list(found_sections.values())
            
            # 缓存到数据库
            if sections:
                try:
                    cache_component_section(component_id, page_url, sections)
                except Exception as e:
                    logger.warning(f"Failed to cache sections: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error extracting sections from {page_url}: {str(e)}")
        
        return sections
    
    def _extract_section_content(self, title_tag, soup: BeautifulSoup, return_html: bool = True) -> str:
        """
        从章节标题节点开始提取章节内容
        
        Args:
            title_tag: 章节标题的 BeautifulSoup 标签节点
            soup: BeautifulSoup 对象
            return_html: 是否返回 HTML 格式（默认 True）
        
        Returns:
            章节内容（HTML 格式或纯文本）
        """
        if not title_tag:
            print(f"   ⚠️  title_tag 为空，返回空内容")
            logger.warning("title_tag is None, returning empty content")
            return ""
        
        try:
            content_parts = []
            
            # 获取当前章节的标题和级别
            current_title = title_tag.get_text(strip=True).replace("\ufeff", "")
            current_level = int(title_tag.name[1]) if title_tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"] else 7
            print(f"   📝 提取章节内容：'{current_title}' (级别：h{current_level})")
            print(f"   return_html={return_html}")
            
            # 从标题的下一个兄弟节点开始遍历
            sibling_count = 0
            collected_count = 0
            for sibling in title_tag.next_siblings:
                sibling_count += 1
                
                # 检查是否是下一个章节标题（遇到任意 h1-h6 标题时停止）
                # 这样可以确保只提取当前章节的内容，不会跨越章节边界
                if hasattr(sibling, 'name') and sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    sibling_level = int(sibling.name[1])
                    sibling_text = sibling.get_text(strip=True).replace("\ufeff", "")
                    
                    # 遇到同级或更高级别的标题时停止（表示新章节开始）
                    if sibling_level <= current_level:
                        print(f"      ⏹️  遇到同级/更高级章节：'{sibling_text}' (h{sibling_level})，已遍历 {sibling_count} 个节点，收集 {collected_count} 个内容元素")
                        if return_html:
                            result = self._clean_html_content(content_parts)
                            print(f"      HTML 结果长度：{len(result)}")
                            return result
                        else:
                            result = self._clean_content(content_parts)
                            print(f"      文本结果长度：{len(result)}")
                            return result
                
                # 收集内容元素
                if self._is_content_element(sibling):
                    content_parts.append(sibling)
                    collected_count += 1
                    # 打印前几个收集的元素
                    if collected_count <= 3:
                        if hasattr(sibling, 'name'):
                            print(f"         收集元素 {collected_count}: <{sibling.name}> (HTML={return_html})")
                        else:
                            print(f"         收集元素 {collected_count}: 文本节点")
            
            print(f"      到达文档末尾：共 {sibling_count} 个兄弟节点，收集 {collected_count} 个内容元素")
            if return_html:
                result = self._clean_html_content(content_parts)
                print(f"      HTML 结果长度：{len(result)}")
                return result
            else:
                result = self._clean_content(content_parts)
                print(f"      文本结果长度：{len(result)}")
                return result
        
        except Exception as e:
            logger.error(f"Error extracting section content: {str(e)}", exc_info=True)
            print(f"   ❌ 提取内容失败：{str(e)}")
            return ""
    
    def _is_content_element(self, tag) -> bool:
        """
        判断标签是否是内容元素
        
        Args:
            tag: BeautifulSoup 标签
        
        Returns:
            True 如果是内容元素
        """
        if not hasattr(tag, 'name'):
            return False
        
        # 排除非内容标签
        if tag.name in ['script', 'style', 'noscript', 'nav', 'header', 'footer', 'aside']:
            return False
        
        # 排除广告、导航等
        class_list = tag.get('class', [])
        if class_list:
            class_str = ' '.join(class_list).lower()
            if any(keyword in class_str for keyword in ['ad', 'nav', 'sidebar', 'footer', 'header']):
                return False
        
        # 接受内容标签
        if tag.name in ['p', 'table', 'ul', 'ol', 'pre', 'div', 'blockquote', 'dl', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return True
        
        # 文本节点也接受
        if hasattr(tag, 'get_text') and tag.get_text(strip=True):
            return True
        
        return False
    
    def _clean_html_content(self, content_elements: list) -> str:
        """
        清理和保留 HTML 格式的内容
        
        Args:
            content_elements: 内容元素列表（BeautifulSoup 标签）
        
        Returns:
            清理后的 HTML 字符串
        """
        if not content_elements:
            return ""
        
        try:
            html_parts = []
            for elem in content_elements:
                if hasattr(elem, 'decode'):
                    # 保留 HTML 标签
                    html = elem.decode()
                    # 清理不需要的标签（script, style 等）
                    if elem.name not in ['script', 'style', 'noscript']:
                        html_parts.append(html)
                else:
                    # 文本节点
                    text = str(elem).strip()
                    if text:
                        html_parts.append(f'<p>{text}</p>')
            
            # 合并 HTML
            full_html = ''.join(html_parts)
            
            # 清理多余的空白字符（但保留 HTML 结构）
            full_html = re.sub(r'>\s+<', '><', full_html)  # 标签间的空白
            
            return full_html
        
        except Exception as e:
            logger.error(f"Error cleaning HTML content: {str(e)}")
            return ""
    
    def _clean_content(self, content_elements: list) -> str:
        """
        清理和格式化内容
        
        Args:
            content_elements: 内容元素列表
        
        Returns:
            清理后的纯文本内容
        """
        if not content_elements:
            return ""
        
        try:
            # 提取文本并清理
            text_parts = []
            for elem in content_elements:
                if hasattr(elem, 'get_text'):
                    text = elem.get_text(strip=True)
                else:
                    text = str(elem).strip()
                
                if text:
                    text_parts.append(text)
            
            # 合并文本
            full_text = '\n'.join(text_parts)
            
            # 清理多余空白
            full_text = re.sub(r'\n\s*\n', '\n\n', full_text)  # 多个空行变一个
            full_text = re.sub(r'[ \t]+', ' ', full_text)  # 多个空格变一个
            full_text = full_text.strip()
            
            return full_text
        
        except Exception as e:
            logger.error(f"Error cleaning content: {str(e)}")
            return ""
    
    def _extract_dependent_components(self, page_url: str) -> List[Dict]:
        """从 iCenter 页面的"8 依赖组件"表格提取依赖组件"""
        related_components = []
        
        if not page_url:
            logger.warning(f"No URL provided for extracting dependent components")
            return related_components
        
        try:
            logger.info(f"Extracting dependent components from: {page_url}")
            page_html = Icenter_content_html_get(page_url)
            if not page_html:
                logger.warning(f"Failed to get HTML from {page_url}")
                return related_components
            
            soup = BeautifulSoup(page_html, "html.parser")
            logger.info(f"HTML parsed successfully, found {len(soup.find_all('table'))} tables")
            
            section_anchor = None
            section_pattern = re.compile(r"^\s*(8|八)?[\.\、\s-]*依赖组件")
            heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
            candidate_tags = heading_tags + ["p", "strong", "span", "div"]
            
            for tag in soup.find_all(candidate_tags):
                text = tag.get_text(strip=True).replace("\ufeff", "")
                if section_pattern.search(text):
                    logger.info(f"Found section anchor: {text}")
                    section_anchor = tag
                    break
            
            if not section_anchor:
                logger.warning(f"No section found matching pattern '{section_pattern.pattern}'")
            
            def extract_components_from_table(table):
                extracted = []
                rows = table.find_all("tr")
                if not rows:
                    return extracted
                
                header_cells = rows[0].find_all(["th", "td"])
                component_col_idx = -1
                
                logger.info(f"Checking table with {len(rows)} rows, header: {[c.get_text(strip=True) for c in header_cells]}")
                
                for idx, cell in enumerate(header_cells):
                    header_text = cell.get_text(strip=True).replace("\ufeff", "")
                    if "组件" in header_text:
                        logger.info(f"Found component column at index {idx}: '{header_text}'")
                        component_col_idx = idx
                        break
                
                if component_col_idx < 0:
                    logger.warning(f"No component column found in table header")
                    return extracted
                
                def is_component_name(value):
                    """判断是否为组件名称（支持多种格式）"""
                    if not value:
                        return False
                    text = value.strip()
                    if not text or text == "PRTC":
                        return False
                    
                    # 格式 1: C001-XXX 或 C-F023-PRTC 组件
                    if re.match(r"^[A-Za-z]+(?:-[A-Za-z]+)*\d+.*组件", text):
                        return True
                    
                    # 格式 2: 包含"组件"字样
                    if "组件" in text and re.search(r"\d", text):
                        return True
                    
                    # 格式 3: 标准组件命名（字母 - 数字）
                    if "-" in text and re.search(r"\d", text):
                        return True
                    
                    return False
                
                logger.info(f"Extracting from table starting at row 1, total {len(rows)-1} data rows")
                for row_idx, row in enumerate(rows[1:], start=1):
                    cells = row.find_all(["td", "th"])
                    logger.info(f"Row {row_idx}: {len(cells)} cells - {[c.get_text(strip=True) for c in cells]}")
                    
                    if component_col_idx < len(cells):
                        name, url = self._extract_cell_name_and_url(cells[component_col_idx])
                        logger.info(f"  -> Extracted: name='{name}', url='{url}', is_component={is_component_name(name)}")
                        if is_component_name(name):
                            extracted.append({"name": name, "url": url})
                
                logger.info(f"Table extraction complete: {len(extracted)} components found")
                return extracted
            
            def is_table_in_hint_block(table):
                prev_heading = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                if prev_heading:
                    heading_text = prev_heading.get_text(strip=True).replace("\ufeff", "")
                    if "提示" in heading_text:
                        return True
                
                prev_text_tag = table.find_previous(["div", "p", "span", "strong"])
                if prev_text_tag:
                    text = prev_text_tag.get_text(strip=True).replace("\ufeff", "")
                    if "提示" in text:
                        return True
                
                has_begin_before = False
                for prev_text in table.find_all_previous(string=True, limit=400):
                    text = str(prev_text).replace("\ufeff", "")
                    if "Example Begin" in text:
                        has_begin_before = True
                        break
                
                if not has_begin_before:
                    return False
                
                has_end_after = False
                for next_text in table.find_all_next(string=True, limit=400):
                    text = str(next_text).replace("\ufeff", "")
                    if "Example End" in text:
                        has_end_after = True
                        break
                
                if has_end_after:
                    return True
                
                return False
            
            if section_anchor:
                for sibling in section_anchor.find_all_next():
                    if sibling == section_anchor:
                        continue
                    if sibling.name in heading_tags and sibling.get_text(strip=True):
                        break
                    if sibling.name == "table":
                        if is_table_in_hint_block(sibling):
                            continue
                        related_components.extend(extract_components_from_table(sibling))
            
            if not related_components:
                for table in soup.find_all("table"):
                    if is_table_in_hint_block(table):
                        continue
                    related_components.extend(extract_components_from_table(table))
            
            example_components = {"C001-LCMOTN 组件", "C002-URM 组件"}
            related_components = self._dedupe_related_items(related_components)
            filtered_components = [
                item for item in related_components 
                if item.get("name") not in example_components
            ]
            
            logger.info(f"Extracted {len(related_components)} components before filtering, {len(filtered_components)} after filtering")
            if filtered_components:
                logger.info(f"Component names: {[c['name'] for c in filtered_components]}")
            
            return filtered_components
            
        except Exception as e:
            logger.error(f"Error extracting dependent components from {page_url}: {str(e)}", exc_info=True)
        
        return related_components
    
    def _extract_affected_features(self, page_url: str) -> List[Dict]:
        """从 iCenter 页面的"7 关联特性"表格提取波及特性"""
        related_features = []
        
        if not page_url:
            return related_features
        
        try:
            page_html = Icenter_content_html_get(page_url)
            if not page_html:
                return related_features
            
            soup = BeautifulSoup(page_html, "html.parser")
            
            feature_section_anchor = None
            feature_section_pattern = re.compile(r"^\s*(7|七)?[\.\、\s-]*关联特性")
            heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
            candidate_tags = heading_tags + ["p", "strong", "span", "div"]
            
            for tag in soup.find_all(candidate_tags):
                text = tag.get_text(strip=True).replace("\ufeff", "")
                if feature_section_pattern.search(text):
                    feature_section_anchor = tag
                    break
            
            def extract_features_from_table(table):
                extracted = []
                rows = table.find_all("tr")
                if not rows:
                    return extracted
                
                header_cells = rows[0].find_all(["th", "td"])
                feature_col_idx = -1
                
                for idx, cell in enumerate(header_cells):
                    header_text = cell.get_text(strip=True).replace("\ufeff", "")
                    if "特性" in header_text:
                        feature_col_idx = idx
                        break
                
                if feature_col_idx < 0:
                    return extracted
                
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    if feature_col_idx < len(cells):
                        name, url = self._extract_cell_name_and_url(cells[feature_col_idx])
                        if name:
                            extracted.append({"name": name, "url": url})
                
                return extracted
            
            def is_table_in_hint_block(table):
                prev_heading = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                if prev_heading:
                    heading_text = prev_heading.get_text(strip=True).replace("\ufeff", "")
                    if "提示" in heading_text:
                        return True
                return False
            
            if feature_section_anchor:
                for sibling in feature_section_anchor.find_all_next():
                    if sibling == feature_section_anchor:
                        continue
                    if sibling.name in heading_tags and sibling.get_text(strip=True):
                        break
                    if sibling.name == "table":
                        if is_table_in_hint_block(sibling):
                            continue
                        related_features.extend(extract_features_from_table(sibling))
            
            if not related_features:
                for table in soup.find_all("table"):
                    if is_table_in_hint_block(table):
                        continue
                    related_features.extend(extract_features_from_table(table))
            
            related_features = self._dedupe_related_items(related_features)
            
        except Exception as e:
            logger.error(f"Error extracting affected features from {page_url}: {str(e)}")
        
        return related_features
    
    def generate_graph(self, seed_component_id: str, scope: str, max_depth: int = 2) -> ComponentGraph:
        """
        生成组件知识图谱
        
        Args:
            seed_component_id: 种子组件 ID（node_id 或 title 均可）
            scope: 范围（L0/L1/L2/WASON/OSP 等）
            max_depth: 最大展开深度（默认 2 度）
        
        Returns:
            ComponentGraph: 图谱对象
        """
        # 防止重复执行：添加执行追踪
        import traceback
        call_stack = traceback.format_stack()
        print(f"\n{'='*80}")
        print(f"🔍 generate_graph 被调用")
        print(f"   Seed: {seed_component_id}")
        print(f"   Scope: {scope}")
        print(f"   MaxDepth: {max_depth}")
        print(f"调用栈（最近 5 层）:")
        for i, line in enumerate(call_stack[-5:-1], 1):
            print(f"   {i}. {line.strip()}")
        print(f"{'='*80}\n")
        
        logger.info(f"=== generate_graph CALLED ===")
        logger.info(f"Seed: {seed_component_id}, Scope: {scope}, MaxDepth: {max_depth}")
        
        print(f"\n{'='*80}")
        print(f"🚀 开始生成图谱 | Seed: {seed_component_id} | Scope: {scope} | MaxDepth: {max_depth}")
        print(f"{'='*80}")
        
        logger.info(f"Generating graph for seed component {seed_component_id}, scope={scope}, max_depth={max_depth}")
        
        graph = ComponentGraph(seed_component_id, "", scope, max_depth)
        
        try:
            # Step 1: 查询种子组件信息（支持 node_id 或 title 查询）
            print(f"\n📌 Step 1: 查询种子组件信息")
            print(f"   - 查询条件：scope={scope}, effective_flag=Y")
            print(f"   - 支持 node_id 或 title 查询：{seed_component_id}")
            
            seed_component = db.session.query(KNOWLEDGE_COMPONENT_TREE).filter(
                KNOWLEDGE_COMPONENT_TREE.scope == scope,
                KNOWLEDGE_COMPONENT_TREE.effective_flag == "Y",
                or_(
                    KNOWLEDGE_COMPONENT_TREE.node_id == seed_component_id,
                    KNOWLEDGE_COMPONENT_TREE.title == seed_component_id
                )
            ).first()
            
            if not seed_component:
                print(f"   ❌ 未找到组件：{seed_component_id} in scope {scope}")
                graph.status = 'failed'
                graph.error_message = f"Component {seed_component_id} not found in scope {scope}"
                return graph
            
            print(f"   ✅ 找到组件：{seed_component.title}")
            print(f"      - node_id: {seed_component.node_id}")
            print(f"      - url: {seed_component.url}")
            print(f"      - space_id: {seed_component.space_id}")
            graph.seed_component_name = seed_component.title
            
            # Step 2: 添加种子组件节点
            print(f"\n📌 Step 2: 添加种子组件节点")
            
            # 种子组件在图谱中始终作为组件节点
            print(f"   ℹ️  种子组件：{seed_component.title}")
            
            # 提取种子组件的页面状态
            seed_page_status = ""
            if seed_component.url:
                seed_page_status = self._extract_page_status(seed_component.url, NodeType.COMPONENT)
                print(f"   📄 页面状态：{seed_page_status}")
            
            seed_node = GraphNode(
                node_id=f"component_{seed_component_id}",
                name=seed_component.title,
                node_type=NodeType.COMPONENT,  # 种子组件始终作为组件节点
                url=seed_component.url,
                space_id=seed_component.space_id,
                content_id=self._parse_icenter_ids(seed_component.url)[1] if seed_component.url else None,
                level=0,
                expanded=True,
                page_status=seed_page_status
            )
            graph.add_node(seed_node)
            print(f"   ✅ 添加成功 | ID: {seed_node.id} | Type: {seed_node.type} | Level: {seed_node.level}")
            
            # Step 3: 查询所有相关节点（用于后续查找模块等）
            print(f"\n📌 Step 3: 查询组件树所有节点")
            all_nodes = query_knowledge_component_tree_nodes(scope, max_level=10)
            print(f"   ✅ 查询到 {len(all_nodes)} 个节点 | Scope: {scope}")
            
            # Step 4: 向下查找子节点（模块和子组件都要添加）
            print(f"\n📌 Step 4: 查找子节点")
            print(f"   Step 4-Down: 向下查找子节点...")
            child_nodes = self._find_child_modules(seed_component.to_dict(), all_nodes)
            print(f"   找到 {len(child_nodes)} 个子节点")
            
            # 分类处理：模块和子组件都要添加
            module_count = 0
            sub_comp_count = 0
            
            for child_node in child_nodes:
                child_title = child_node['title']
                child_url = child_node.get('url', '')
                print(f"      - {child_title} (node_id: {child_node['node_id']})")
                
                # 判断是否为子组件（SC 开头）
                if is_valid_sub_comp_tree_page_title_format(child_title):
                    # 是子组件，也要添加
                    print(f"         → 子组件节点，添加到图谱")
                    sub_comp_count += 1
                    
                    # 提取子组件的页面状态
                    sub_comp_page_status = ""
                    if child_url:
                        sub_comp_page_status = self._extract_page_status(child_url, NodeType.MODULE)
                        print(f"         📄 页面状态：{sub_comp_page_status}")
                    
                    sub_comp_node = GraphNode(
                        node_id=f"sub_comp_{child_node['node_id']}",
                        name=child_node['title'],
                        node_type=NodeType.MODULE,  # 子组件作为模块类型
                        url=child_url,
                        level=1,
                        parent_component_id=seed_component_id,
                        page_status=sub_comp_page_status
                    )
                    graph.add_node(sub_comp_node)
                    
                    edge = GraphEdge(
                        edge_id=f"edge_{seed_component_id}_contains_{child_node['node_id']}",
                        source=seed_node.id,
                        target=sub_comp_node.id,
                        relation_type=RelationType.CONTAINS,
                        relation_label='包含'
                    )
                    graph.add_edge(edge)
                    
                else:
                    # 是模块，直接添加
                    print(f"         → 模块节点")
                    module_count += 1
                    
                    # 提取模块的页面状态
                    module_page_status = ""
                    if child_url:
                        module_page_status = self._extract_page_status(child_url, NodeType.MODULE)
                        print(f"         📄 页面状态：{module_page_status}")
                    
                    module_node = GraphNode(
                        node_id=f"module_{child_node['node_id']}",
                        name=child_node['title'],
                        node_type=NodeType.MODULE,
                        url=child_url,
                        level=1,
                        parent_component_id=seed_component_id,
                        page_status=module_page_status
                    )
                    graph.add_node(module_node)
                    
                    edge = GraphEdge(
                        edge_id=f"edge_{seed_component_id}_contains_{child_node['node_id']}",
                        source=seed_node.id,
                        target=module_node.id,
                        relation_type=RelationType.CONTAINS,
                        relation_label='包含'
                    )
                    graph.add_edge(edge)
            
            print(f"   ✅ 添加了 {module_count + sub_comp_count} 个节点和关系边（{module_count} 个模块，{sub_comp_count} 个子组件）")
            
            if not child_nodes:
                print(f"   ⚠️  警告：未找到任何子节点")
            
            # Step 5: 提取种子组件的章节信息
            print(f"\n📌 Step 5: 提取章节信息")
            if seed_component.url:
                print(f"   - 解析 URL: {seed_component.url}")
                print(f"   🔍 开始提取章节...")
                sections = self._extract_sections_from_icenter(seed_component.url, seed_component_id)
                print(f"   📊 提取结果：{len(sections)} 个章节")
                logger.info(f"Step 5: Extracting sections from URL: {seed_component.url}")
                logger.info(f"Step 5: Extracted {len(sections)} sections")
                print(f"   ✅ 提取到 {len(sections)} 个章节:")
                
                # 打印每个章节的标题和内容对应关系
                for idx, section in enumerate(sections, 1):
                    section_title = section['section_title']
                    section_content = section.get('section_content', '')
                    content_word_count = section.get('content_word_count', len(section_content))
                    section_level = section.get('level', 1)  # 获取章节级别（h1=1, h2=2, ..., h6=6）
                    
                    print(f"\n   [{'='*50}]")
                    print(f"   章节 {idx}/{len(sections)}")
                    print(f"   标题：{section_title}")
                    print(f"   类型：{section['section_type']}")
                    print(f"   级别：h{section_level}")
                    print(f"   字数：{content_word_count}")
                    print(f"   section_id: {section['section_id']}")
                    print(f"   section_content 长度：{len(section_content)}")
                    print(f"   <====Context begin{'='*55}>")
                    print(f"   {section_content[:500]}{'...' if len(section_content) > 500 else ''}")
                    print(f"   <====Context end{'='*57}>")
                    
                    # 验证 section_content 是否为空
                    if not section_content:
                        print(f"   ⚠️  警告：章节内容为空！使用标题作为 desc")
                    
                    section_node = GraphNode(
                        node_id=f"section_{seed_component_id}_{section['section_id']}",
                        name=section['section_title'],
                        node_type=NodeType.SECTION,
                        desc=section_content if section_content else section_title,  # 使用 desc 字段存储章节内容，如果为空则使用标题
                        level=section_level,  # 使用从 HTML 中提取的实际级别
                        parent_component_id=seed_component_id
                    )
                    graph.add_node(section_node)
                    
                    # 验证节点创建
                    print(f"   ✅ 节点创建成功：desc 长度={len(section_node.desc)}")
                    
                    edge = GraphEdge(
                        edge_id=f"edge_{seed_component_id}_contains_{section['section_id']}",
                        source=seed_node.id,
                        target=section_node.id,
                        relation_type=RelationType.CONTAINS
                    )
                    graph.add_edge(edge)
                
                print(f"\n   ✅ 添加了 {len(sections)} 个章节节点和关系边")
            else:
                print(f"   ⚠️  组件无 URL，跳过章节提取")
            
            # Step 6: 提取依赖组件
            print(f"\n📌 Step 6: 提取依赖组件")
            if seed_component.url:
                dependent_components = self._extract_dependent_components(seed_component.url)
                print(f"   ✅ 提取到 {len(dependent_components)} 个依赖组件:")
                for dep_comp in dependent_components:
                    print(f"      - {dep_comp['name']}")
                    dep_comp_id = f"dep_comp_{dep_comp['name']}"
                    dep_comp_url = dep_comp['url']
                    
                    # 提取依赖组件的页面状态
                    dep_comp_page_status = ""
                    if dep_comp_url:
                        dep_comp_page_status = self._extract_page_status(dep_comp_url, NodeType.DEPENDENT_COMPONENT)
                        print(f"         📄 页面状态：{dep_comp_page_status}")
                    
                    dep_comp_node = GraphNode(
                        node_id=f"component_{dep_comp_id}",
                        name=dep_comp['name'],
                        node_type=NodeType.DEPENDENT_COMPONENT,
                        url=dep_comp_url,
                        level=1,
                        parent_component_id=seed_component_id,
                        page_status=dep_comp_page_status
                    )
                    graph.add_node(dep_comp_node)
                    
                    edge = GraphEdge(
                        edge_id=f"edge_{seed_component_id}_depends_on_{dep_comp_id}",
                        source=seed_node.id,
                        target=dep_comp_node.id,
                        relation_type=RelationType.DEPENDS_ON
                    )
                    graph.add_edge(edge)
                print(f"   ✅ 添加了 {len(dependent_components)} 个 depends_on 关系边")
            else:
                print(f"   ⚠️  组件无 URL，跳过依赖组件提取")
            
            # Step 7: 提取波及特性
            print(f"\n📌 Step 7: 提取波及特性")
            if seed_component.url:
                affected_features = self._extract_affected_features(seed_component.url)
                print(f"   ✅ 提取到 {len(affected_features)} 个波及特性:")
                for feature in affected_features:
                    print(f"      - {feature['name']}")
                    feature_id = f"feature_{feature['name']}"
                    feature_url = feature['url']
                    
                    # 提取波及特性的页面状态（注意：波及特性使用"页面设计状态"作为 key）
                    feature_page_status = ""
                    if feature_url:
                        feature_page_status = self._extract_page_status(feature_url, NodeType.AFFECTED_FEATURE)
                        print(f"         📄 页面状态：{feature_page_status}")
                    
                    feature_node = GraphNode(
                        node_id=f"feature_{feature_id}",
                        name=feature['name'],
                        node_type=NodeType.AFFECTED_FEATURE,
                        url=feature_url,
                        level=1,
                        parent_component_id=seed_component_id,
                        page_status=feature_page_status
                    )
                    graph.add_node(feature_node)
                    
                    edge = GraphEdge(
                        edge_id=f"edge_{seed_component_id}_affects_{feature_id}",
                        source=seed_node.id,
                        target=feature_node.id,
                        relation_type=RelationType.AFFECTS
                    )
                    graph.add_edge(edge)
                print(f"   ✅ 添加了 {len(affected_features)} 个 affects 关系边")
            else:
                print(f"   ⚠️  组件无 URL，跳过波及特性提取")
            
            # Step 8: 标记节点展开状态
            print(f"\n📌 Step 8: 标记节点展开状态")
            for node in list(graph.nodes.values()):
                if node.level < max_depth and node.type in [NodeType.DEPENDENT_COMPONENT, NodeType.AFFECTED_FEATURE]:
                    node.expanded = False
            print(f"   ✅ 已标记需要懒加载的节点")
            
            # 完成图谱生成
            graph.status = 'completed'
            graph.generated_at = datetime.now()
            graph.expires_at = datetime.now() + timedelta(hours=24)
            
            # 按节点类型统计
            node_type_counts = {}
            for node in graph.nodes.values():
                node_type_counts[node.type] = node_type_counts.get(node.type, 0) + 1
            
            print(f"\n{'='*80}")
            print(f"✅ 图谱生成完成")
            print(f"   - 总节点数：{len(graph.nodes)}")
            print(f"   - 总边数：{len(graph.edges)}")
            print(f"   - 节点类型分布:")
            for node_type, count in sorted(node_type_counts.items()):
                print(f"      * {node_type}: {count}")
            print(f"{'='*80}\n")
            
            logger.info(f"Graph generated successfully: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
            logger.info(f"Node type breakdown: {node_type_counts}")
            if len(graph.nodes) == 0:
                logger.error(f"WARNING: Graph has NO nodes! Check previous log steps for details.")
                logger.error(f"  - seed_component.url: {seed_component.url}")
                logger.error(f"  - all_nodes count: {len(all_nodes)}")
            
        except Exception as e:
            print(f"\n❌ 图谱生成失败：{str(e)}")
            logger.error(f"Error generating graph: {str(e)}")
            graph.status = 'failed'
            graph.error_message = str(e)
        
        return graph
    
    def cache_graph(self, graph: ComponentGraph, operator_person: str = ""):
        """
        缓存图谱到数据库（调用 data_model.py 中的函数）
        
        Args:
            graph: 图谱对象
            operator_person: 操作人
        """
        try:
            # 转换为字典格式
            graph_data = graph.to_dict()
            
            # 保存图谱主表
            result = save_graph_to_db(graph_data, operator_person)
            
            if result['status'] == 'success':
                graph_id = result['graph_id']
                
                # 保存节点
                nodes_list = [node.to_dict() for node in graph.nodes.values()]
                save_graph_nodes(graph_id, nodes_list)
                
                # 保存边
                edges_list = [edge.to_dict() for edge in graph.edges]
                save_graph_edges(graph_id, edges_list)
                
                logger.info(f"Graph cached to DB with id={graph_id}")
            else:
                logger.error(f"Failed to save graph: {result.get('message')}")
                
        except Exception as e:
            logger.error(f"Error caching graph: {str(e)}")
            raise
    
    def get_cached_graph(self, seed_component_id: str, max_depth: int = 2) -> Optional[ComponentGraph]:
        """
        从数据库获取缓存的图谱（调用 data_model.py 中的函数）
        
        Args:
            seed_component_id: 种子组件 ID
            max_depth: 最大深度
        
        Returns:
            ComponentGraph or None
        """
        try:
            # 查询缓存
            cached_graph = query_cached_graph(seed_component_id, max_depth)
            
            if not cached_graph:
                return None
            
            # 解析 graph_data
            graph_data = cached_graph.graph_data
            if isinstance(graph_data, str):
                graph_data = json.loads(graph_data)
            
            # 重建图谱对象
            graph = ComponentGraph(
                seed_component_id=cached_graph.seed_component_id,
                seed_component_name=cached_graph.seed_component_name,
                scope=cached_graph.scope,
                max_depth=cached_graph.max_depth
            )
            graph.status = cached_graph.status
            graph.error_message = cached_graph.error_message or ''
            graph.generated_at = cached_graph.generated_at
            graph.expires_at = cached_graph.expires_at
            
            # 重建节点
            nodes = query_graph_nodes(cached_graph.id)
            for node_data in nodes:
                raw_data = node_data.get('raw_data') or {}
                node = GraphNode(
                    node_id=node_data['node_id'],
                    name=node_data['node_name'],
                    node_type=node_data['node_type'],
                    url=raw_data.get('url', ''),
                    space_id=raw_data.get('spaceId', ''),
                    content_id=raw_data.get('contentId', ''),
                    desc=raw_data.get('desc', ''),
                    page_status=raw_data.get('pageStatus', ''),
                    parent_component_id=node_data.get('parent_component_id'),
                    level=node_data.get('level', 1),
                    expanded=bool(node_data.get('is_expanded', 0)),
                    position_x=float(node_data['position_x']) if node_data.get('position_x') else None,
                    position_y=float(node_data['position_y']) if node_data.get('position_y') else None,
                )
                graph.nodes[node.id] = node
            
            # 重建边
            edges = query_graph_edges(cached_graph.id)
            for edge_data in edges:
                edge = GraphEdge(
                    edge_id=edge_data['edge_id'],
                    source=edge_data['source_node_id'],
                    target=edge_data['target_node_id'],
                    relation_type=edge_data['relation_type'],
                    relation_label=edge_data.get('relation_label', ''),
                )
                graph.edges.append(edge)
            
            return graph
            
        except Exception as e:
            logger.error(f"Error getting cached graph: {str(e)}")
            return None
    
    def cache_graph_to_db(self, graph: 'ComponentGraph', operator_person: str = ""):
        """
        缓存图谱到数据库
        
        Args:
            graph: 图谱对象
            operator_person: 操作人
        """
        try:
            logger.info(f"Caching graph to database: {graph.seed_component_id}")
            
            # 调用 data_model 中的函数保存图谱
            # 注意：save_graph_to_db 期望驼峰命名的字段
            graph_data = {
                'seedComponentId': graph.seed_component_id,
                'seedComponentName': graph.seed_component_name,
                'scope': graph.scope,
                'maxDepth': graph.max_depth,
                'status': graph.status,
                'totalNodes': len(graph.nodes),
                'totalEdges': len(graph.edges),
                'nodes': [node.to_dict() for node in graph.nodes.values()],
                'edges': [edge.to_dict() for edge in graph.edges],
                'generatedAt': graph.generated_at.isoformat() if graph.generated_at else datetime.now().isoformat(),
                'expiresAt': graph.expires_at.isoformat() if graph.expires_at else None,
                'errorMessage': graph.error_message
            }
            
            # 保存图谱主表
            save_result = save_graph_to_db(graph_data, operator_person)
            
            if save_result.get('status') == 'error':
                logger.error(f"Failed to save graph: {save_result.get('message')}")
                return
            
            graph_id = save_result.get('graph_id')
            logger.info(f"Graph saved with ID: {graph_id}")
            
            # 保存节点（注意：save_graph_nodes 期望驼峰命名的字段）
            if graph.nodes:
                nodes_data = []
                for node in graph.nodes.values():
                    nodes_data.append(node.to_dict())  # 使用 to_dict() 方法，已经是驼峰命名
                save_graph_nodes(graph_id, nodes_data)
                logger.info(f"Saved {len(nodes_data)} nodes")
            
            # 保存边（注意：save_graph_edges 期望驼峰命名的字段）
            if graph.edges:
                edges_data = []
                for edge in graph.edges:
                    edges_data.append(edge.to_dict())  # 使用 to_dict() 方法，已经是驼峰命名
                save_graph_edges(graph_id, edges_data)
                logger.info(f"Saved {len(edges_data)} edges")
            
            # 缓存组件章节信息（只缓存种子组件）
            seed_node = graph.nodes.get(f"component_{graph.seed_component_id}")
            if seed_node and seed_node.url:
                try:
                    # 从 graph_data 中获取章节信息
                    sections = [node for node in graph.nodes.values() if node.type == NodeType.SECTION]
                    if sections:
                        cache_component_section(graph.seed_component_id, seed_node.url, sections)
                        logger.info(f"Cached {len(sections)} sections for component {graph.seed_component_name}")
                except Exception as e:
                    logger.warning(f"Failed to cache sections for component {graph.seed_component_name}: {e}")
            
            logger.info(f"Graph cached successfully: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
            
        except Exception as e:
            logger.error(f"Error caching graph to database: {str(e)}")
            raise


# 全局服务实例
_graph_service_instance = None

def get_graph_service() -> GraphService:
    """获取图谱服务单例"""
    global _graph_service_instance
    if _graph_service_instance is None:
        _graph_service_instance = GraphService()
    return _graph_service_instance
