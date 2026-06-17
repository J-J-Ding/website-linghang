"""
iCenter 页面处理模块
提供 URL 解析、子页面查询、知识提取等功能
"""

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from requirementsTree.uac_token import get_uac_token

logger = logging.getLogger(__name__)


# ==================== iCenter 提取类 ====================

class IcenterExtractor:
    """
    基于 HTML 解析的 iCenter 页面提取器

    封装认证、页面获取、HTML 解析的公共逻辑，
    各提取方法只需关注具体的解析规则。
    """

    # ---- 章节匹配正则（\s+ 匹配 \xa0 等特殊空白） ----
    PATTERN_FEATURE_INDEX = r'5\.1\.1\s+波及特性索引'
    PATTERN_WAVE_FUNCTION = r'5\.1\s+波及功能'
    PATTERN_WAVE_COMPONENT = r'8\.2\s+波及组件'
    PATTERN_MODULE_DESIGN = r'模块设计-'

    def __init__(self):
        user_num, token = get_uac_token()
        if not token:
            raise RuntimeError("获取 UAC token 失败")
        from get_icenter import IcenterAPI
        self._api = IcenterAPI(user_num, token=token)

    # ---- 静态方法 ----

    @staticmethod
    def _parse_url(url):
        """
        从 iCenter 页面 URL 中解析 spaceId 和 pageId
        支持两种格式:
          - https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
          - https://i.zte.com.cn/#/shared/{spaceId}/wiki/page/{pageId}
        解析失败则抛出 ValueError
        """
        parsed = urlparse(url)
        fragment = parsed.fragment
        if not fragment:
            raise ValueError(f"URL 中无 fragment（#/space/...或#/shared/...），无法解析: {url}")

        parts = [p for p in fragment.split('/') if p]
        space_id = None
        page_id = None
        for i, part in enumerate(parts):
            if part in ("space", "shared") and i + 1 < len(parts):
                space_id = parts[i + 1]
            if part == "page" and i + 1 < len(parts):
                page_id = parts[i + 1]
        if not space_id:
            raise ValueError(f"无法从 URL 解析 spaceId: {url}")
        if not page_id:
            raise ValueError(f"无法从 URL 解析 pageId: {url}")
        return space_id, page_id

    @staticmethod
    def _extract_column_by_header(table, header_text):
        """
        从 HTML 表格中提取指定列头对应的所有数据（排除列头本身和空值）
        """
        rows = table.find_all('tr')
        if not rows:
            return []

        header_cells = rows[0].find_all(['th', 'td'])
        col_index = None
        for i, cell in enumerate(header_cells):
            if header_text in cell.get_text(strip=True):
                col_index = i
                break

        if col_index is None:
            logger.warning(f"表头中未找到 '{header_text}'")
            return []

        values = []
        for row in rows[1:]:
            cells = row.find_all(['th', 'td'])
            if col_index < len(cells):
                text = cells[col_index].get_text(strip=True)
                if text:
                    values.append(text)

        return values

    @staticmethod
    def _extract_section_html(heading_tag):
        """
        从标题标签开始，提取到下一个同级或更高级标题之间的所有HTML内容
        """
        heading_level = int(heading_tag.name[1])  # h2 -> 2
        parts = []

        sibling = heading_tag.next_sibling
        while sibling:
            if hasattr(sibling, 'name') and sibling.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                if int(sibling.name[1]) <= heading_level:
                    break
            parts.append(str(sibling))
            sibling = sibling.next_sibling

        return ''.join(parts).strip()

    @staticmethod
    def _find_heading(soup, pattern, level):
        """
        查找匹配正则的标题标签
        level: 标题等级 1~6，对应 h1~h6（必选）
        pattern: 正则表达式字符串或编译后的正则对象
        """
        tag_name = f'h{level}'
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        return soup.find(
            lambda tag: tag.name == tag_name
            and pattern.search(tag.get_text(strip=True))
        )

    @staticmethod
    def _find_all_headings(soup, pattern, level):
        """
        查找所有匹配正则的标题标签
        level: 标题等级 1~6，对应 h1~h6（必选）
        pattern: 正则表达式字符串或编译后的正则对象
        """
        tag_name = f'h{level}'
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        return soup.find_all(
            lambda tag: tag.name == tag_name
            and pattern.search(tag.get_text(strip=True))
        )

    # ---- 实例方法 ----

    def _fetch_html(self, url):
        """
        获取 iCenter 页面的 HTML 内容和标题，返回 (BeautifulSoup, title) 元组，失败返回 (None, '')
        token 失效时自动重建实例重试一次
        """
        try:
            space_id, page_id = self._parse_url(url)
        except ValueError as e:
            logger.warning(f"URL 解析失败: {e}")
            return None, ''

        try:
            content, title = self._api.get_page_info(space_id, page_id)
        except Exception as e:
            logger.warning(f"获取页面内容异常: {e}, url={url}")
            content, title = None, None

        if not content:
            # 可能是 token 失效，重建实例重试
            logger.warning(f"获取页面内容失败，尝试刷新 token 重试: {url}")
            try:
                user_num, token = get_uac_token()
                if token:
                    from get_icenter import IcenterAPI
                    self._api = IcenterAPI(user_num, token=token)
                    content, title = self._api.get_page_info(space_id, page_id)
            except Exception as e:
                logger.warning(f"刷新 token 重试也异常: {e}, url={url}")
                content, title = None, None
            if not content:
                logger.warning(f"重试后仍获取页面内容失败: {url}")
                return None, ''

        return BeautifulSoup(content, 'html.parser'), title or ''

    # ---- 对外提取方法 ----

    def requirement_instance_extract(self, instance_url):
        """
        从需求实例化页面提取特性列表和章节内容

        1. 找到 "5.1.1 波及特性索引(BA）" 章节的第一个表格，提取"设功能（标准特性）"列
        2. 获取"5.1 波及功能【BA/规划SE】"整章节的HTML内容

        Returns:
            dict: {"success", "url", "page_title", "features", "sections"}
        """
        soup, page_title = self._fetch_html(instance_url)
        if not soup:
            return {"success": False, "error": "获取页面内容失败", "url": instance_url,
                    "page_title": "", "features": [], "sections": []}

        # 提取特性列表
        features = []
        feature_h = self._find_heading(soup, self.PATTERN_FEATURE_INDEX, level=3)
        if feature_h:
            table = feature_h.find_next('table')
            if table:
                features = self._extract_column_by_header(table, '设功能（标准特性）')
                logger.info(f"提取到 {len(features)} 个波及特性: {features}")
            else:
                logger.warning("找到'5.1.1 波及特性索引'标题但未找到后续表格")
        else:
            logger.warning("未找到'5.1.1 波及特性索引'章节标题")

        # 提取整章节内容
        sections = []
        section_h = self._find_heading(soup, self.PATTERN_WAVE_FUNCTION, level=2)
        if section_h:
            section_title = section_h.get_text(strip=True)
            sections.append({
                "section_title": section_title,
                "section_type": section_title,
                "raw_html": self._extract_section_html(section_h),
            })
        else:
            logger.warning("未找到'5.1 波及功能'章节标题")

        return {"success": True, "url": instance_url, "page_title": page_title, "features": features, "sections": sections}

    def requirement_solution_extract(self, solution_url):
        """
        从需求方案页面提取组件列表和章节内容

        1. 找到 "8.2 波及组件" 章节的第一个表格，提取"组件名称"列
        2. 获取"8.2 波及组件"整章节的HTML内容

        Returns:
            dict: {"success", "url", "page_title", "components", "sections"}
        """
        soup, page_title = self._fetch_html(solution_url)
        if not soup:
            return {"success": False, "error": "获取页面内容失败", "url": solution_url,
                    "page_title": "", "components": [], "sections": []}

        # 提取组件列表
        components = []
        section_h = self._find_heading(soup, self.PATTERN_WAVE_COMPONENT, level=2)
        if section_h:
            table = section_h.find_next('table')
            if table:
                components = self._extract_column_by_header(table, '组件名称')
                logger.info(f"提取到 {len(components)} 个波及组件: {components}")
            else:
                logger.warning("找到'8.2 波及组件'标题但未找到后续表格")
        else:
            logger.warning("未找到'8.2 波及组件'章节标题")

        # 提取整章节内容
        sections = []
        if section_h:
            section_title = section_h.get_text(strip=True)
            sections.append({
                "section_title": section_title,
                "section_type": section_title,
                "raw_html": self._extract_section_html(section_h),
            })

        return {"success": True, "url": solution_url, "page_title": page_title, "components": components, "sections": sections}

    def component_design_extract(self, design_url):
        """
        从组件功能设计页面提取"模块设计-"开头的章节内容

        找到所有标题包含"模块设计-"的章节（编号不固定，如10、11、12等），
        提取每个匹配章节的标题和HTML内容。

        Returns:
            dict: {"success", "url", "page_title", "sections"}
        """
        soup, page_title = self._fetch_html(design_url)
        if not soup:
            return {"success": False, "error": "获取页面内容失败", "url": design_url,
                    "page_title": "", "sections": []}

        sections = []
        for heading in self._find_all_headings(soup, self.PATTERN_MODULE_DESIGN, level=1):
            section_title = heading.get_text(strip=True)
            sections.append({
                "section_title": section_title,
                "section_type": section_title,
                "raw_html": self._extract_section_html(heading),
            })

        logger.info(f"提取到 {len(sections)} 个模块设计章节")
        return {"success": True, "url": design_url, "page_title": page_title, "sections": sections}

    def get_first_children(self, page_url):
        """获取 iCenter 页面的一级子页面，返回 {title: url} 或 None"""
        space_id, page_id = self._parse_url(page_url)
        return self._api.get_first_children(space_id, page_id)

    def fetch_requirement_solutions(self, instance_url):
        """
        从需求实例化的 iCenter 页面中提取需求方案子页面

        逻辑：获取实例化页面的一级子页面，筛选以"【需求方案】"开头的页面

        Returns:
            list[dict]: 需求方案列表，每项包含 name、full_title 和 url
                查询失败返回空列表
        """
        if not instance_url or not instance_url.strip():
            return []

        try:
            children = self.get_first_children(instance_url)
            if not children:
                return []

            solutions = []
            for title, url in children.items():
                if title.startswith("【需求方案】"):
                    solution_name = title[len("【需求方案】"):]
                    solutions.append({
                        "name": solution_name if solution_name else title,
                        "full_title": title,
                        "url": url,
                    })

            logger.info(f"从实例化页面提取到 {len(solutions)} 个需求方案: {[s['name'] for s in solutions]}")
            return solutions

        except Exception as e:
            logger.error(f"从实例化页面提取需求方案失败: {str(e)}")
            return []

    def fetch_component_designs(self, solution_url):
        """
        从需求方案的 iCenter 页面中提取组件功能设计子页面

        逻辑：获取方案页面的一级子页面，筛选以"【组件功能设计】"开头的页面

        Returns:
            list[dict]: 组件功能设计列表，每项包含 name、full_title 和 url
                查询失败返回空列表
        """
        if not solution_url or not solution_url.strip():
            return []

        try:
            children = self.get_first_children(solution_url)
            if not children:
                return []

            designs = []
            for title, url in children.items():
                if title.startswith("【组件功能设计】"):
                    design_name = title[len("【组件功能设计】"):]
                    designs.append({
                        "name": design_name if design_name else title,
                        "full_title": title,
                        "url": url,
                    })

            logger.info(f"从方案页面提取到 {len(designs)} 个组件功能设计: {[d['name'] for d in designs]}")
            return designs

        except Exception as e:
            logger.error(f"从方案页面提取组件功能设计失败: {str(e)}")
            return []


# ==================== 领域到 SKILLM 页面映射 ====================

# system_areapath 到 iCenter SKILLM 页面 content_id 的映射
# 所有 SKILLM 页面都在同一个 space: fbff14a6a14c4985874248df3ac610c1
SYSTEM_AREAPATH_TO_SKILLM_MAP = {
    "05-支撑": "07eff86df14511f08d432fb0242413c8",
    "01-L0 光系统": "ea0065ddf14411f09b3c39f507ac033d",
    "02-L1": "faa7db6af14411f0abba3128eb5b9bed",
    "03-L2": "0260f03bf14511f0abbaa1eb2d0402f0",
    "13-智能控制": "0d54bd3cf14511f0a129d19e54bf3454",
}

SKILLM_SPACE_ID = "fbff14a6a14c4985874248df3ac610c1"

# 开发技能库固定入口页面
SKILLM_ROOT_URL = f"https://i.zte.com.cn/index/ispace/#/space/{SKILLM_SPACE_ID}/wiki/page/e45a5803f13211f098712da37e8c0e58/view"

# system_areapath 前缀 → 一级子页面标题关键词的映射
# 用于在固定入口页面的一级子页面中按领域定位目标子页面
SYSTEM_AREAPATH_PREFIX_TO_DOMAIN_KEYWORD = [
    ("00-L0", "L0领域"),
    ("01-L1", "L1领域"),
    ("03-L2", "L2领域"),
    ("05-支撑", "支撑领域"),
    ("13-智能控制", "智控领域"),
]


# ==================== 模块级便捷函数 ====================

_cached_extractor = None


def _get_extractor():
    """获取缓存的 IcenterExtractor 实例，同一进程内复用，token 失效时由 _fetch_html 自动刷新"""
    global _cached_extractor
    if _cached_extractor is None:
        _cached_extractor = IcenterExtractor()
    return _cached_extractor


def knowledge_requirement_instance_extract(instance_url):
    """从需求实例化页面提取特性列表和章节内容"""
    return _get_extractor().requirement_instance_extract(instance_url)


def knowledge_requirement_solution_extract(solution_url):
    """从需求方案页面提取组件列表和章节内容"""
    return _get_extractor().requirement_solution_extract(solution_url)


def knowledge_component_design_extract(design_url):
    """从组件功能设计页面提取模块设计章节内容"""
    return _get_extractor().component_design_extract(design_url)


def fetch_requirement_solutions(instance_url):
    """从需求实例化页面提取需求方案子页面"""
    return _get_extractor().fetch_requirement_solutions(instance_url)


def fetch_component_designs(solution_url):
    """从需求方案页面提取组件功能设计子页面"""
    return _get_extractor().fetch_component_designs(solution_url)


def get_skillm_page_url(system_areapath):
    """
    根据 system_areapath 获取对应的 SKILLM 页面 URL
    
    Args:
        system_areapath: 系统领域路径，如 "01-L0 光系统"、"02-L1" 等
        
    Returns:
        str: SKILLM 页面 URL，如果找不到映射则返回 None
    """
    content_id = SYSTEM_AREAPATH_TO_SKILLM_MAP.get(system_areapath)
    if not content_id:
        logger.warning(f"未找到 system_areapath '{system_areapath}' 对应的 SKILLM 页面映射")
        return None
    
    url = f"https://i.zte.com.cn/index/ispace/#/space/{SKILLM_SPACE_ID}/wiki/page/{content_id}/view"
    return url


def _resolve_domain_keyword(system_areapath):
    """
    根据 system_areapath 前缀解析出对应的一级子页面标题关键词

    Args:
        system_areapath: PR 的系统领域路径，如 "00-L0光模块"、"01-L1" 等

    Returns:
        str: 一级子页面标题关键词，如 "L0领域"、"L1领域" 等；未匹配返回 None
    """
    if not system_areapath:
        return None
    for prefix, keyword in SYSTEM_AREAPATH_PREFIX_TO_DOMAIN_KEYWORD:
        if system_areapath.startswith(prefix):
            return keyword
    return None


def _recursive_match_skills(extractor, page_url, detail_category, parent_title, skills, depth, max_depth=4):
    """
    递归遍历子页面，标题包含 detail_category 则收录为技能节点

    Args:
        extractor: IcenterExtractor 实例
        page_url: 当前页面 URL
        detail_category: 细分类别，用于匹配子页面标题
        parent_title: 父页面标题，用于构建 full_title
        skills: 结果列表，就地追加
        depth: 当前递归深度（1=二级子页面）
        max_depth: 最大递归深度
    """
    if depth > max_depth:
        return

    children = extractor.get_first_children(page_url)
    if not children:
        return

    for child_title, child_url in children.items():
        print(f"{'  ' * depth}[fetch_skills] depth={depth}, title={child_title}")

        if detail_category:
            if detail_category in child_title:
                print(f"{'  ' * depth}[fetch_skills] ✓ 匹配到技能：{child_title}")
                skills.append({
                    "name": child_title,
                    "full_title": f"{parent_title} > {child_title}" if parent_title else child_title,
                    "url": child_url,
                })
        else:
            print(f"{'  ' * depth}[fetch_skills] 添加技能（无 detail_category 过滤）：{child_title}")
            skills.append({
                "name": child_title,
                "full_title": f"{parent_title} > {child_title}" if parent_title else child_title,
                "url": child_url,
            })

        # 无论是否匹配，都继续递归子页面（匹配到的页面下可能还有更细粒度的技能）
        _recursive_match_skills(extractor, child_url, detail_category, child_title, skills, depth + 1, max_depth)


def fetch_skills(skillm_url, detail_category=None, system_areapath=None):
    """
    从开发技能库固定入口页面中提取技能子页面

    逻辑：
    1. 访问固定入口页面（SKILLM_ROOT_URL），获取一级子页面
    2. 根据 system_areapath 前缀匹配，找到领域对应的一级子页面
    3. 在该领域子页面下递归遍历子层级（二级、三级、四级...）
    4. 子页面标题中如果包含 detail_category，收录为技能节点

    Args:
        skillm_url: 入口页面 URL（建议传入 SKILLM_ROOT_URL，兼容旧调用）
        detail_category: 细分类别，用于筛选子页面标题
        system_areapath: PR 的系统领域路径，如 "01-L1"，用于定位领域子页面

    Returns:
        list[dict]: 技能列表，每项包含 name、full_title 和 url
            查询失败返回空列表
    """
    # 优先使用固定入口 URL
    root_url = SKILLM_ROOT_URL if SKILLM_ROOT_URL else skillm_url
    if not root_url or not root_url.strip():
        return []

    extractor = _get_extractor()

    try:
        print("=" * 60)
        print(f"[fetch_skills] 开始提取开发技能")
        print(f"[fetch_skills] root_url: {root_url}")
        print(f"[fetch_skills] system_areapath: {system_areapath}")
        print(f"[fetch_skills] detail_category: {detail_category}")

        # 解析领域关键词
        domain_keyword = _resolve_domain_keyword(system_areapath)
        print(f"[fetch_skills] domain_keyword: {domain_keyword}")
        if not domain_keyword:
            print(f"[fetch_skills] 无法解析领域关键词，system_areapath='{system_areapath}'")
            logger.warning(f"无法解析领域关键词，system_areapath='{system_areapath}'")
            return []

        # 获取一级子页面（领域分类层）
        level1_children = extractor.get_first_children(root_url)
        print(f"[fetch_skills] 一级子页面数量：{len(level1_children) if level1_children else 0}")
        if level1_children:
            for title, url in level1_children.items():
                print(f"  - {title}: {url}")

        if not level1_children:
            print(f"[fetch_skills] 未找到一级子页面")
            return []

        # 在一级子页面中找到领域匹配的页面
        domain_page_url = None
        domain_page_title = None
        for title, url in level1_children.items():
            if domain_keyword in title:
                domain_page_url = url
                domain_page_title = title
                print(f"[fetch_skills] ✓ 领域匹配：'{title}' 包含关键词 '{domain_keyword}'")
                break

        if not domain_page_url:
            print(f"[fetch_skills] 未找到领域匹配的一级子页面，domain_keyword='{domain_keyword}'")
            logger.warning(f"未找到领域匹配的一级子页面，domain_keyword='{domain_keyword}'")
            return []

        # 在领域子页面下递归遍历，匹配 detail_category
        skills = []
        _recursive_match_skills(
            extractor, domain_page_url, detail_category,
            domain_page_title, skills, depth=1, max_depth=4,
        )

        print(f"[fetch_skills] 最终提取到 {len(skills)} 个开发技能")
        print("=" * 60)
        logger.info(f"从开发技能库提取到 {len(skills)} 个技能，domain={domain_keyword}")
        return skills

    except Exception as e:
        logger.error(f"从开发技能库提取技能失败：{str(e)}")
        print(f"[fetch_skills] 异常：{str(e)}")
        return []


def knowledge_skill_extract(skill_url, detail_category=None, system_areapath=None):
    """
    从开发技能库提取技能列表

    Args:
        skill_url: 入口页面 URL（建议传入 SKILLM_ROOT_URL，兼容旧调用）
        detail_category: 细分类别，用于筛选子页面
        system_areapath: PR 的系统领域路径，如 "01-L1"，用于定位领域子页面

    Returns:
        dict: {
            "success": bool,
            "matched_url": str (匹配到的页面 URL),
            "matched_title": str (匹配到的页面标题),
            "skills": list
        }
        skills: [{"skill_name": str, "skill_url": str}, ...]
    """
    extractor = _get_extractor()

    # 获取子页面列表（传入 system_areapath 用于领域匹配）
    skills = fetch_skills(skill_url, detail_category, system_areapath)

    if not skills:
        # 如果没有子页面，尝试从当前页面提取
        soup, page_title = extractor._fetch_html(skill_url)
        if not soup:
            return {"success": False, "error": "获取页面内容失败", "url": skill_url,
                    "page_title": "", "skills": []}

        # 从当前页面提取技能（表格或列表）
        skill_list = []
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 1:
                    skill_name_cell = cells[0]
                    skill_name = skill_name_cell.get_text(strip=True)
                    skill_link = skill_name_cell.find('a')
                    skill_url_item = skill_link.get('href') if skill_link else None
                    if skill_name:
                        skill_list.append({
                            "skill_name": skill_name,
                            "skill_url": skill_url_item if skill_url_item else skill_url,
                        })

        if not skill_list:
            lists = soup.find_all(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                for item in items:
                    skill_name = item.get_text(strip=True)
                    skill_link = item.find('a')
                    skill_url_item = skill_link.get('href') if skill_link else None
                    if skill_name:
                        skill_list.append({
                            "skill_name": skill_name,
                            "skill_url": skill_url_item if skill_url_item else skill_url,
                        })

        return {
            "success": True,
            "matched_url": skill_url,
            "matched_title": page_title,
            "skills": skill_list
        }

    # 有子页面时，返回第一个匹配的页面 URL 和技能列表
    # skill_name 取匹配页面的短标题（name），即页面自身的标题
    if skills:
        return {
            "success": True,
            "matched_url": skills[0]["url"] if skills else skill_url,
            "matched_title": skills[0]["full_title"] if skills else "",
            "skills": [{"skill_name": s["name"], "skill_url": s["url"]} for s in skills]
        }

    return {
        "success": True,
        "matched_url": skill_url,
        "matched_title": "",
        "skills": []
    }


def enrich_icenter_data(flat_nodes):
    """
    对每条有 instance_url 的需求，从 iCenter 获取方案文档和组件功能设计链接，
    填充 icenter_solution_urls 和 icenter_component_designs 字段
    """
    extractor = _get_extractor()

    def _fetch_one(node):
        instance_url = node.get("instance_url", "")
        if not instance_url or not instance_url.strip():
            return 0
        try:
            solutions = extractor.fetch_requirement_solutions(instance_url)
            if not solutions:
                return 0

            solution_urls = [s["url"] for s in solutions]
            node["icenter_solution_urls"] = solution_urls

            component_designs = {}
            for solution in solutions:
                designs = extractor.fetch_component_designs(solution["url"])
                if designs:
                    component_designs[solution["url"]] = [d["url"] for d in designs]

            if component_designs:
                node["icenter_component_designs"] = component_designs

            return 1
        except Exception as e:
            logger.warning(f"iCenter 补充数据失败, instance_url={instance_url}: {e}")
            return 0

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(_fetch_one, flat_nodes))

    enriched_count = sum(results)
    logger.info(f"iCenter 补充完成，{enriched_count}/{len(flat_nodes)} 条需求获取到方案信息")
