"""
组件树相关 API 模块（平滑迁移入口）。

当前实现先从旧模块 `api_data` 复用导出，避免一次性改名导致大范围 import 断裂。
后续可逐步把组件树相关实现从 `api_data.py` 迁移到此文件内。
"""

import os
import re
import json
import logging
import sqlite3
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Set
from flask import request, jsonify
from ask_ai_request import Ask_ai
from get_icenter import Icenter_content_html_get, Icenter_content_html_set, Icenter_children_get, Icenter_title_get, Icenter_block_get, Icenter_block_set, Get_icenter_page_detail, IcenterAPI
from get_rdc import Rdc_list_get, change_description_and_tags
from task_common import tasks_update
from componentTree.data_model import query_knowledge_component_tree_nodes, replace_knowledge_component_tree_nodes
from componentTree.component_know_daily_data  import is_valid_comp_tree_page_title_format, is_valid_module_page_title_format

def html_table_to_dataframe(html):
    """从HTML字符串中提取表格数据并返回DataFrame
    
    Args:
        html_content (str): 包含表格的HTML字符串
        
    Returns:
        pd.DataFrame or None: 包含第一个表格数据的DataFrame，如果没有有效表格则返回None
    """
    # 参数检查
    if not html or not isinstance(html, str):
        print("Warning: 输入的HTML内容无效")
        return None

    try:
        # 解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            print("Warning: HTML中没有找到表格")
            return None

        # 处理第一个表格
        table = tables[0]
        data = []
        
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all(['th', 'td']):
                # 提取内容：优先获取链接，否则获取文本
                link = cell.find('a')
                content = link['href'] if link and link.get('href') else cell.get_text(strip=False)
                row_data.append(content)
            if row_data:  # 忽略空行
                data.append(row_data)
        
        # 创建DataFrame
        columns = [str(col).strip() for col in data[0]]  # 确保列名为字符串
        df = pd.DataFrame(data[1:], columns=columns)
        
        # 清理数据：去除字符串两端的空白
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df

    except Exception as e:
        print(f"Error: 处理HTML表格时发生错误 - {str(e)}")
        return None


def icenter_table_update(html, table_json):
    """
    根据JSON数据更新HTML中的表格内容，保持原有样式不变
    
    参数:
        html (str): 包含表格的HTML字符串
        json (dict): 包含更新数据的JSON对象
        
    返回:
        html (str): 更新后的HTML字符串
    """
    try:
        # 1. 将HTML表格转换为DataFrame
        table_df = html_table_to_dataframe(html)
        if table_df is None:
            raise ValueError("无法从HTML中提取表格数据")
        
        # 2. 将JSON数据转换为DataFrame用于更新
        table_json_obj = json.loads(table_json)
        update_df = pd.DataFrame(table_json_obj)
        if update_df.empty:
            raise ValueError("JSON数据为空或无效")
        
        # 3. 确保两个DataFrame结构匹配
        if not set(update_df.columns).issubset(set(table_df.columns)):
            raise ValueError("JSON中的列名与HTML表格不匹配")
        
        # 4. 更新表格数据
        for col in update_df.columns:
            table_df[col] = update_df[col]
        
        # 5. 将更新后的DataFrame转换回HTML，同时保留原HTML的样式
        soup = BeautifulSoup(html, 'html.parser')
        original_table = soup.find('table')
        
        if not original_table:
            raise ValueError("HTML中没有找到表格元素")
        
        # 清除原表格内容但保留所有属性
        new_table = original_table
        new_table.clear()
        
        # 重新构建表头
        thead = soup.new_tag('thead')
        tr = soup.new_tag('tr')
        for col in table_df.columns:
            th = soup.new_tag('th')
            th.string = str(col)
            tr.append(th)
        thead.append(tr)
        new_table.append(thead)
        
        # 重新构建表体
        tbody = soup.new_tag('tbody')
        for _, row in table_df.iterrows():
            tr = soup.new_tag('tr')
            for col in table_df.columns:
                td = soup.new_tag('td')
                # 保留原单元格中的链接结构（如果存在）
                if pd.notna(row[col]) and str(row[col]).startswith(('http://', 'https://')):
                    a = soup.new_tag('a', href=row[col])
                    a.string = row[col]
                    td.append(a)
                else:
                    td.string = str(row[col])
                tr.append(td)
            tbody.append(tr)
        new_table.append(tbody)
        
        return str(soup)
    
    except Exception as e:
        print(f"Error: 更新表格时发生错误 - {str(e)}")
        return html  # 发生错误时返回原HTML


# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _normalize_tree_scope(raw_scope):
    raw = str(raw_scope or "L1").strip()
    if raw in {"支撑", "OSP"}:
        return "OSP"
    scope = raw.upper()
    if scope in {"L2"}:
        return "L2"
    if scope in {"L0"}:
        return "L0"
    if scope in {"WASON", "智控".upper(), "ZK", "ZHIKONG"}:
        return "WASON"
    return "L1"


def _get_tree_scope_config(scope):
    if scope == "L2":
        return {
            "root_title": "L2领域组件树",
            "categories": [
                {"title": "L2领域-E卡平台-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/6b10aa01204d11f09f38bd067b2197b5/view"},
                {"title": "L2领域-小设备平台-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/3c5021928f7711f0a290d3dfc9605be0/view"},
                {"title": "L2领域-大设备平台-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/084f733e8f7711f0a5362d460b990f16/view"},
            ],
        }
    if scope == "L0":
        return {
            "root_title": "L0领域组件树",
            "categories": [
                {"title": "L0领域-应用-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c47642211f4e11f0aee1853811e2336a/view"},
                {"title": "L0领域-技术-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/8af116ba5bd611f08c8fa7466ab6b7a3/view"},
            ],
        }
    if scope == "WASON":
        return {
            "root_title": "智控领域组件树",
            "categories": [
                {"title": "智控领域-应用-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/07887b1b4b5a11f08200e91213ab284f/view"},
                {"title": "智控领域-技术-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/971cdd9367b811f084bb83141293d8d2/view"},
            ],
        }
    if scope == "OSP":
        return {
            "root_title": "支撑领域组件树",
            "categories": [
                {"title": "支撑领域-应用-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9ce9fdc00ee711f0b2c3b75a02dcbeb7/view"},
                {"title": "支撑领域-技术-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/108a98d63bc511f0b7898f0a658efff7/view"},
            ],
        }
    return {
        "root_title": "L1领域组件树",
        "categories": [
            {"title": "L1领域-应用-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9de71306f96e11efb81c0bfbc4e63315/view"},
            {"title": "L1领域-技术-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c082f09ef96e11ef9e50cb809b24249f/view"},
            {"title": "L1领域-驱动-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c90f0c4ff96e11ef8a7d6f3b17d16194/view"},
            {"title": "L1领域-组装-组件树", "url": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/bf17306d66ef11f083f1976d88e954ad/view"},
        ],
    }


def _build_root_node_online(scope, max_level, root_title=""):
    """
    构建根节点在线数据
    
    策略：
    - Level 1: 领域分类页面（如 "L1 领域 - 应用 - 组件树"）
    - Level 2: 从 Level 1 页面的子节点中，筛选出组件 (C-*)
    - Level 3: 继续递归获取，可能是子组件 (C-*) 和模块 (M-*)
    - Level 4: 递归终止条件为 max_level ，可能是模块、或者没有子节点终止

    
    这样可以处理 iCenter 页面结构不规范的情况（模块直接挂在领域分类下）
    """
    config = _get_tree_scope_config(scope)
    children = []
    for item in config["categories"]:
        # Level 1 固定为 category 类型
        children.append(_build_tree_node(item["title"], item["url"], 1, "category", max_level))

    return {
        "id": f"root-{scope.lower()}",
        "spaceId": "",
        "title": root_title or config["root_title"],
        "level": 0,
        "nodeType": "root",
        "url": "",
        "hasChildren": len(children) > 0,
        "children": children,
    }


def _flatten_tree_nodes(root_node):
    flat_nodes = []
    queue = [(root_node, None, 0)]
    while queue:
        current, parent_id, sort_no = queue.pop(0)
        node_id = current.get("id")
        if not node_id:
            continue
        flat_nodes.append(
            {
                "id": node_id,
                "parentId": parent_id,
                "level": int(current.get("level", 0)),
                "nodeType": current.get("nodeType", "category"),
                "title": current.get("title", ""),
                "url": current.get("url", ""),
                "spaceId": current.get("spaceId", ""),
                "sortNo": int(current.get("sortNo", sort_no)),
                "hasChildren": bool(current.get("hasChildren", False)),
            }
        )
        for idx, child in enumerate(current.get("children", [])):
            queue.append((child, node_id, idx))
    return flat_nodes


def _build_tree_from_cached_nodes(cached_nodes, default_root_title):
    if not cached_nodes:
        return None

    node_map = {}
    valid_node_ids = set()  # 记录有效节点 ID
    roots = []
    
    # 第一遍：创建所有节点并校验
    for row in cached_nodes:
        node_type = row.get("node_type", "category")
        title = row.get("title", "")
        
        # 校验节点标题格式
        if not _validate_node_title(title, node_type):
            logger.warning(f"Cached node title validation failed: title={title}, node_type={node_type}, node_id={row.get('node_id')}")
            continue  # 跳过无效节点
        
        node = {
            "id": row.get("node_id"),
            "spaceId": row.get("space_id", ""),
            "title": title,
            "level": int(row.get("level", 0)),
            "nodeType": node_type,
            "url": row.get("url", ""),
            "hasChildren": row.get("has_children") == "Y",
            "children": [],
        }
        node_map[row.get("node_id")] = node
        valid_node_ids.add(row.get("node_id"))

    # 第二遍：建立父子关系（只处理有效节点）
    for row in cached_nodes:
        node_id = row.get("node_id")
        parent_id = row.get("parent_id")
        
        # 跳过无效节点
        if node_id not in valid_node_ids:
            continue
        
        current = node_map.get(node_id)
        if not current:
            continue
        
        # 如果父节点无效，则将当前节点提升为根节点
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(current)
        else:
            roots.append(current)

    if not roots:
        return None

    root_candidates = [item for item in roots if item.get("nodeType") == "root" or item.get("level") == 0]
    if root_candidates:
        return root_candidates[0]

    return {
        "id": "root-cache",
        "spaceId": "",
        "title": default_root_title,
        "level": 0,
        "nodeType": "root",
        "url": "",
        "hasChildren": len(roots) > 0,
        "children": roots,
    }


def _count_total_nodes(root_node):
    if not root_node:
        return 0
    count = 0
    queue = [root_node]
    while queue:
        current = queue.pop(0)
        count += 1
        queue.extend(current.get("children", []))
    return count


def _has_second_level_children(root_node):
    """
    判断是否存在二级及以下节点（不是只有一级目录）。
    """
    if not root_node:
        return False
    for first_level in root_node.get("children", []):
        if first_level.get("children"):
            return True
    return False


def _is_valid_subcomponent_format(subcomp_str):
    """
    验证子组件页面标题格式是否正确
    
    子组件命名规则：SC{编号}-{子组件名称}
    示例：SC001-数据处理，SC12-控制管理
    
    Args:
        subcomp_str: 待验证的子组件名称字符串
    
    Returns:
        bool: 格式是否正确
    """
    if not isinstance(subcomp_str, str) or not subcomp_str.strip():
        return False
    pattern = r'^SC\d+-(.*)$'
    match = re.match(pattern, subcomp_str)
    return bool(match)


def _infer_child_type(child_title: str, next_level: int) -> str:
    """
    智能推断子节点类型
    
    策略：
    - Level 1: 固定为 category
    - Level 2: 根据标题格式判断（C-* → component）
    - Level 3: 关键层级！只能是子组件或模块
              - 如果是 SC* 格式 → component（子组件，有 Level 4）
              - 如果是 M* 格式 → module（模块，叶子节点）
              - 其他 → 按 module 处理（兜底）
    - Level 4: 固定为 module
    """
    # 1. 严格根据标题格式判断（最高优先级）
    is_subcomponent_format = _is_valid_subcomponent_format(child_title)
    is_module_format = bool(is_valid_module_page_title_format(child_title))
    is_component_format = bool(is_valid_comp_tree_page_title_format(child_title))
    
    logger.debug(f"_infer_child_type: title={child_title}, next_level={next_level}, is_sc={is_subcomponent_format}, is_mod={is_module_format}, is_comp={is_component_format}")
    
    # Level 3 特殊处理：只能是子组件或模块
    if next_level == 3:
        if is_subcomponent_format:
            logger.info(f"Detected sub-component format at Level 3: {child_title}")
            return "component"  # 子组件属于 component 类型，还有 Level 4
        if is_module_format:
            logger.info(f"Detected module format at Level 3: {child_title}")
            return "module"  # 模块是叶子节点
        # Level 3 既不是 SC* 也不是 M*，按 module 处理（兜底）
        logger.warning(f"Level 3 title does not match SC* or M* format: {child_title}, defaulting to module")
        return "module"
    
    # 其他层级：优先根据标题格式判断
    if is_component_format:
        logger.info(f"Detected component format at Level {next_level}: {child_title}")
        return "component"
    if is_module_format:
        logger.info(f"Detected module format at Level {next_level}: {child_title}")
        return "module"
    
    # 2. 如果没有特定格式，根据层级判断（兜底策略）
    if next_level == 2:
        return "category"
    elif next_level == 4:
        return "module"
    else:
        return "category"


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
    is_component_format = bool(is_valid_comp_tree_page_title_format(title))
    is_subcomponent_format = _is_valid_subcomponent_format(title)
    is_module_format = bool(is_valid_module_page_title_format(title))
    
    logger.debug(f"_validate_node_title: title={title}, node_type={node_type}, is_comp={is_component_format}, is_sc={is_subcomponent_format}, is_mod={is_module_format}")
    
    # 如果标题符合组件/子组件/模块格式，直接通过
    # 原因：标题格式本身已经证明了有效性，node_type 可能因层级划分不准确而标记错误
    if is_component_format or is_subcomponent_format or is_module_format:
        return True
    
    # 如果不符合任何特定格式，仅当 node_type 为 category/root 时通过
    if node_type in ["category", "root"]:
        return True
    
    # 如果是 component/module 类型但不符合对应格式，则失败
    logger.warning(f"Node title format mismatch: title={title}, expected node_type={node_type}")
    return False

def Icenter_table_get(url):
    """从iCenter页面提取表格数据并返回Python原生JSON格式（list of dict）

    Args:
        url (str): 要抓取的iCenter页面URL

    Returns:
        list: 表格数据的Python列表，每个元素是字典（key为列名，value为单元格内容）
              如果无数据或出错，返回空列表 []

    Raises:
        ValueError: 当输入URL无效时
    """
    # 输入验证
    if not url or not isinstance(url, str):
        raise ValueError("无效的URL参数")

    try:
        logger.info(f"开始获取iCenter表格数据，URL: {url}")

        # 1、获取iCenter页面内容
        page_html = Icenter_content_html_get(url)
        if not page_html:
            logger.warning("获取页面内容失败或返回空内容")
            return []  # 改为返回空列表，而不是 None

        # 2、解析页面内容
        soup = BeautifulSoup(page_html, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            logger.warning("页面中没有找到任何表格")
            return []

        # 处理第一个表格
        first_table = tables[0]
        data = []

        # 提取表头
        header_row = first_table.find('tr')
        if not header_row:
            logger.warning("表格中没有找到表头行")
            return []

        headers = []
        for th in header_row.find_all(['th', 'td']):
            link = th.find('a')
            if link and link.get('href'):
                content = link['href']
            else:
                # 使用 prettify() 保留原始HTML结构，再提取文本
                content = th.prettify()
                # 移除标签但保留换行符
                content = BeautifulSoup(content, 'html.parser').get_text(strip=False)
                content = re.sub(r'\n\s*\n', '\n', content.strip())
            headers.append(content.strip())

        # 提取表格数据
        for row in first_table.find_all('tr')[1:]:  # 跳过表头行
            row_data = {}
            for idx, cell in enumerate(row.find_all(['th', 'td'])):
                try:
                    link = cell.find('a')
                    if link and link.get('href'):
                        content = link['href']
                    else:
                        # 关键修改：保留原始换行
                        content = cell.prettify()
                        content = BeautifulSoup(content, 'html.parser').get_text(strip=False)
                        content = re.sub(r'\n\s*\n', '\n', content.strip())

                    # 用列名作为 key，内容作为 value
                    col_name = headers[idx] if idx < len(headers) else f"column_{idx}"
                    row_data[col_name] = content.strip() if isinstance(content, str) else str(content)
                except Exception as cell_error:
                    logger.warning(f"处理单元格时出错: {str(cell_error)}")
                    col_name = headers[idx] if idx < len(headers) else f"column_{idx}"
                    row_data[col_name] = ""

            # 确保行数据与表头一致
            if len(row_data) == len(headers):
                data.append(row_data)
            else:
                logger.warning(f"跳过不匹配的行数据，表头长度: {len(headers)}, 行数据长度: {len(row_data)}")

        if not data:
            logger.warning("没有提取到有效的表格数据")
            return []

        # ✅ 返回真正的 Python list，不是字符串！
        logger.info(f"成功提取表格数据，共 {len(data)} 条记录")
        return data  # ✅ 直接返回 list，调用方无需 json.loads()

    except Exception as e:
        logger.error(f"处理表格数据时发生未预期错误: {str(e)}", exc_info=True)
        return []  # 出错时返回空列表，安全

def Icenter_table_set(url, table_json):
    """将JSON格式的表格数据更新到iCenter页面
    
    Args:
        url (str): 要更新的iCenter页面URL
        table_json (str): 包含表格数据的JSON字符串
        
    Returns:
        bool: 更新成功返回True，失败返回False
        
    Raises:
        ValueError: 当输入参数无效时
    """
    # 输入验证
    if not url or not isinstance(url, str):
        raise ValueError("无效的URL参数")
    if not table_json or not isinstance(table_json, str):
        raise ValueError("无效的table_json参数")
    
    try:
        logger.info(f"开始更新iCenter表格数据，URL: {url}")
        
        # 验证JSON格式
        try:
            json.loads(table_json)
        except json.JSONDecodeError:
            logger.error("提供的table_json不是有效的JSON格式")
            return False

        # 1、获取icenter页面内容
        page_html = Icenter_content_html_get(url)
        if not page_html:
            logger.warning("获取页面内容失败或返回空内容")
            return False

        # 2、更新表格内容
        page_html_update = icenter_table_update(page_html, table_json)
        if not page_html_update:
            logger.warning("表格更新失败")
            return False
        
        # 3、提交更新后的内容
        result = Icenter_content_html_set(url, page_html_update)
        if not result:
            logger.warning("内容提交失败")
            return False
        
        logger.info("表格数据更新成功")
        return True
        
    except Exception as e:
        logger.error(f"更新表格数据时发生未预期错误: {str(e)}", exc_info=True)
        return False


# 定义映射关系表
TABLE_MAP = {
    'Scene': {
        'L0': '',
        'L1': '',
        'L2': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/2e7e224e568611f09bfd69b1e8bb6823/view',
        'OSP': '',
        'WASON': ''
    },
    'Feature': {
        'L0': '',
        'L1': '',
        'L2': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/36c23907568611f08986edd3c38d5330/view',
        'OSP': '',
        'WASON': ''
    },
    'Board': {
        'F1K': 'https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/b618c0bd292d4489a0a4dc618a4212eb/view',
        'F2K': '',
        'E2K': '',
        'E4K': ''
    },
    'Component': {
        'L0': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c47642211f4e11f0aee1853811e2336a/view',
        'L1': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9de71306f96e11efb81c0bfbc4e63315/view',
        'L2': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/6b10aa01204d11f09f38bd067b2197b5/view',
        'OSP': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9ce9fdc00ee711f0b2c3b75a02dcbeb7/view',
        'WASON': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/07887b1b4b5a11f08200e91213ab284f/view',
        'DATA':'https://i.zte.com.cn/#/shared/87ffb6c09cba4461a89499f817320b6c/wiki/page/e15f99fc952611f0b1f8234919c65b0a/view'
    },
    'Quality': {
        'version': 'https://i.zte.com.cn/#/shared/cb9fffb8150d498c99109876c5b26595/wiki/page/83126f5f6f7711f0bcf7a78ab3b6d853/view',
    },
}

def Table_read():
    print("Table_read")
    # 获取前端发送的JSON数据
    data = request.get_json()
    
    # 提取参数
    table = data.get('table')
    domain = data.get('domain')
    
    print(f"收到请求 - 表名: {table}, 域: {domain}")
    
    # 检查表是否存在
    if table not in TABLE_MAP:
        return jsonify({
            "status": "error",
            "message": f"表名 {table} 不存在"
        }), 400

    table_data = []

    if domain == "all":
        # 遍历该表下所有 domain，跳过空 URL
        for domain_key, url in TABLE_MAP[table].items():
            if url:  # 只处理非空的 URL
                print(f"正在获取数据: {domain_key} -> {url}")
                try:
                    data_part = Icenter_table_get(url)
                    if isinstance(data_part, list):
                        table_data.extend(data_part)
                    else:
                        print(f"警告: Icenter_table_get 返回非列表类型: {type(data_part)}")
                except Exception as e:
                    print(f"获取 {url} 时出错: {e}")
        print(f"所有 domain 数据合并完成，共 {len(table_data)} 条记录")

    else:
        # 单个 domain 的情况
        if domain not in TABLE_MAP[table]:
            return jsonify({
                "status": "error",
                "message": f"域 {domain} 在表 {table} 中不存在"
            }), 400

        url = TABLE_MAP[table][domain]
        if not url:
            return jsonify({
                "status": "error",
                "message": f"{domain}领域对应的 URL 为空"
            }), 400

        try:
            table_data = Icenter_table_get(url)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"获取数据失败: {str(e)}"
            }), 500

    # 返回响应
    return jsonify({
        "status": "success",
        "message": f"表格数据获取成功，共 {len(table_data)} 条记录",
        "tableData": table_data
    })


def Table_write():
    try:
        print("\n=== 数据接受开始... ===")

        # 获取前端发送的JSON数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '未接收到有效数据'
            }), 400
        
        table = data.get('table')
        domain = data.get('domain')        
        table_data = data.get('tableData', [])

        print("\n=== 数据接收完成! ===")
        
        # 将列表转换为 JSON 字符串
        table_data_json = json.dumps(table_data, ensure_ascii=False)
        print(table_data_json)
        
        # 根据不同的表和领域选择不同的 URL
        if table == 'Feature' and domain == 'L2':
            url = TABLE_MAP['Feature']['L2']
            result = Icenter_table_set(url, table_data_json)  # 传递 JSON 字符串
        else:
            result = False

        # 返回成功响应
        return jsonify({
            'status': 'success' if result else 'error',
            'message': '数据接收成功' if result else '不支持的表格或领域',
        })
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'服务器处理错误: {str(e)}'
        }), 500

def API_Icenter_block_get():
    return


def API_Icenter_block_set():
    print("\n=== 写icenter页面block内容 ===")
    
    # 导入所需模块
    import json
    # 导入markdown及必要的扩展
    import markdown
    from markdown.extensions import tables  # 表格扩展
    
    try:
        # 获取前端发送的JSON数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '未接收到有效数据'
            }), 400
        
        # 获取前端传递的参数
        workflow = data.get('workflow')
        content = data.get('content')
        
        if content is None:
            return jsonify({
                'status': 'error',
                'message': '未找到字符串内容'
            }), 400
        
        # 解析并打印接收到的字符串
        print(f"流程: {workflow}")
        print(f"内容: {content}")

        # 构建提示信息，请求AI转换为JSON格式
        question = f"""
            {content}
            请将上述内容严格转换为JSON格式输出，格式如下：
            {{
                "url": "需求实例化链接",
                "blockTag": "波及特性分析",
                "blockContent": "将波及特性分析内容直接写在这里，不需要任何其他处理"
            }}
            请只返回JSON格式数据，不要添加任何额外说明文字。
        """
        
        # 调用AI接口获取转换后的JSON
        answer = Ask_ai(question, "nebula")
        print("AI返回的原始数据:", answer)
        
        # 解析AI返回的JSON数据
        try:
            # 移除可能存在的前后空格和代码块标记
            cleaned_answer = answer.strip().replace('```json', '').replace('```', '').strip()
            answer_json = json.loads(cleaned_answer)
            
            # 提取所需字段
            url = answer_json.get('url')
            block_tag = answer_json.get('blockTag')
            block_content_markdown = answer_json.get('blockContent')
            
            # 检查必要字段是否存在
            if not all([url, block_tag, block_content_markdown]):
                return jsonify({
                    'status': 'error',
                    'message': 'AI返回的JSON数据不完整，缺少必要字段'
                }), 500
                
            print(f"解析到的URL: {url}")
            print(f"解析到的blockTag: {block_tag}")
            print("原始Markdown内容:", block_content_markdown)
            
            # 将Markdown转换为HTML，启用表格扩展
            try:
                # 使用tables扩展来正确解析表格
                block_content_html = markdown.markdown(
                    block_content_markdown,
                    extensions=[tables.TableExtension()]  # 启用表格扩展
                )
                print("转换后的HTML内容:", block_content_html)
            except Exception as e:
                print(f"Markdown转HTML失败: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Markdown转换为HTML时出错: {str(e)}'
                }), 500
            
            # 调用Icenter_block_set回写内容
            res = Icenter_block_set(
                url=url,
                block_id=None,
                block_title=None,
                block_tag=block_tag,
                block_content=block_content_html  # 传入转换后的HTML内容
            )
            
            print("回写结果:", res)
            
        except json.JSONDecodeError as e:
            print(f"解析AI返回的JSON失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'AI返回的数据不是有效的JSON格式: {str(e)}'
            }), 500

        # 返回成功响应
        return jsonify({
            'status': 'success',
            'message': '字符串接收并处理成功',
            'received_length': len(content),
            'write_result': res,
            'conversion_status': 'Markdown已成功转换为HTML'
        })
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'服务器处理错误: {str(e)}'
        }), 500
    
# 定义映射关系表
MENU_MAP = {
    'Scene': {
        'L0': '',
        'L1': '',
        'L2': '',
        'OSP': '',
        'WASON': ''
    },
    'Feature': {
        'L0': '',
        'L1': '',
        'L2': '',
        'OSP': '',
        'WASON': ''
    },
    'Board': {
        'F1K': '',
        'F2K': '',
        'E2K': '',
        'E4K': ''
    },
    'Component': {
        'L0': '',
        'L1': '',
        'L2': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/6b10aa01204d11f09f38bd067b2197b5/view',
        'OSP': '',
        'WASON': ''
    }
}

def Menu_read():
    print("Menu_read")

    # 获取 GET 请求的 query 参数
    table = request.args.get('table')
    domain = request.args.get('domain')

    # 参数校验
    if not table:
        return jsonify({
            "status": "success",
            "message": "缺少 table 参数，跳过处理",
            "menuData": []
        })
    if not domain:
        return jsonify({
            "status": "success",
            "message": "缺少 domain 参数，跳过处理",
            "menuData": []
        })

    print(f"收到请求 - 表: {table}, 领域: {domain}")

    menu_title = []

    # 安全访问 MENU_MAP，避免 KeyError
    try:
        # 使用 .get() 逐层安全访问
        table_data = MENU_MAP.get(table)
        if not table_data:
            print(f"警告: table '{table}' 在 MENU_MAP 中不存在")
            pass  # 跳过，menu_title 保持为空
        else:
            domain_data = table_data.get(domain)
            if not domain_data:
                print(f"警告: domain '{domain}' 在 table '{table}' 中不存在")
                pass  # 跳过
            else:
                _, menu_title, _ = Icenter_children_get(domain_data)
    except Exception as e:
        print(f"获取菜单数据时发生异常: {e}")
        # 异常时不中断，继续返回空菜单

    # 返回响应（即使没有数据也返回 success）
    return jsonify({
        "status": "success",
        "message": "菜单数据获取成功",
        "menuData": menu_title
    })

def Rdc_list_read():
    print("Rdc_list_read")

    # query_conditions = request.args.get('query_conditions')
    # query_items = request.args.get('query_items')
    # query_items_convert = request.args.get('query_items_convert')

    query_conditions = [
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "",
            "field": "System_WorkItemType",
            "operator": "=",
            "value": "chgRequest:OTNAG:变更请求"
        },
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "AND",
            "field": "ChangeMajorType",
            "operator": "=_accurate",
            "value": "缺陷/故障"
        },
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "AND",
            "field": "System_State",
            "operator": "not in",
            "value": [
            "已确认拒绝",
            "已确认重复",
            "已取消"
            ]
        },
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "AND",
            "field": "DiscoveryActivity",
            "operator": "in",
            "value": "集成测试,领域测试,系统测试,渗透测试,安全功能测试,性能容量测试,验证阶段可靠性测试,验证阶段新需求测试,独立安全测评,方案测试,工程模拟测试,外场测试,外部第三方测评,试验局验证,试验局测试,外部认证测试,综合场景测试"
        },
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "AND",
            "field": "ImportResponserDept",
            "operator": "in",
            "value": "波分软件开发一部/有线研究院/系统产品_有线产品经营部/中兴通讯股份有限公司，波分软件开发二部/有线研究院/系统产品_有线产品经营部/中兴通讯股份有限公司"
        },
        {
            "leftGroup": 0,
            "rightGroup": 0,
            "logicalOperator": "AND",
            "field": "System_CreatedDate",
            "operator": ">=",
            "value": "2023-01-01"
        }
    ]

    query_items = [
        {
            "key": "System_Id",
            "name": "标识",
            "type": "workItemNo",
            "width": ""
        },
        {
            "key": "System_Title",
            "name": "标题",
            "type": "string",
            "width": "",
            "isAscending": True
        },
        {
            "key": "System_WorkItemType",
            "name": "工作项类型",
            "type": "workItemType",
            "width": ""
        },
        {
            "key": "System_AreaPath",
            "name": "领域",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "BelongTeamLimitRange",
            "name": "所属团队",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "DiscoveryActivity",
            "name": "发现活动",
            "type": "string",
            "width": ""
        },
        {
            "key": "System_CreatedDate",
            "name": "创建时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "BelongProduct",
            "name": "所属产品",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "BelongProject",
            "name": "所属项目",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "IntroductedBy",
            "name": "引入者",
            "type": "user",
            "width": ""
        },
        {
            "key": "ImportResponserDept",
            "name": "引入责任部门",
            "type": "string",
            "width": ""
        },
        {
            "key": "DiscoverWay",
            "name": "发现方法",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectLevel",
            "name": "缺陷等级",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectSource",
            "name": "缺陷来源",
            "type": "string",
            "width": ""
        }
    ]

    query_items_convert = {
        "标识": "标识",
        "标题": "主题",
        "领域": "领域",
        "所属团队": "团队",
        "引入者": "引入人",
        "引入责任部门": "引入部门",
        "发现活动": "发现活动",
        "缺陷等级": "故障等级",
        "缺陷来源": "故障来源",
        "所属产品": "所属产品",
        "所属项目": "所属项目",
        "创建时间": "提交日期",
    }

    rdc_list = Rdc_list_get(query_conditions, query_items, query_items_convert, 10000)

    # return rdc_list
    return jsonify({
        "status": "success",
        "message": "菜单数据获取成功",
        "result": rdc_list
    })


def review_update():
    print("review_update")
  
    query_condition = [
        {   
            "field": "System_WorkItemType",
            "leftGroup": 0,
            "logicalOperator": "",
            "operator": "=",
            "rightGroup": 0,
            "value": "EcFaultReview:OTNAG:故障复盘,BugReview:OTNAG:故障复盘"
        },
        {
            "field": "ChangeSubmissionTime",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": ">=",
            "rightGroup": 0,
            "value": "2023-01-01"
        },
        {
            "field": "ProblemAttribution",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "in",
            "rightGroup": 0,
            "value": "L0领域,L2/L3领域,支撑领域,L1领域,智能控制领域"
        },
        {
            "field": "DiscoveryActivity",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "in",
            "rightGroup": 0,
            "value": "集成测试,领域测试,系统测试,安全功能测试,性能容量测试,方案测试,工程模拟测试,验证阶段新需求测试,综合场景测试,验证阶段可靠性测试"
        },
        {
            "field": "ProblemAttribution",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "!=_accurate",
            "rightGroup": 0,
            "value": None
        }
    ]

    query_items = [
        {
            "key": "System_Id",
            "name": "标识",
            "type": "workItemNo",
            "width": "278"
        },
        {
            "key": "System_Title",
            "name": "标题",
            "type": "string",
            "width": ""
        },
        {
            "key": "System_WorkItemType",
            "name": "工作项类型",
            "type": "workItemType",
            "width": ""
        },
        {
            "key": "MasterArea",
            "name": "主领域",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroductionLink",
            "name": "故障引入环节",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectSource",
            "name": "缺陷来源",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroduceReason1",
            "name": "故障引入一级原因",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroduceReason2",
            "name": "故障引入二级原因",
            "type": "string",
            "width": ""
        },
        {
            "key": "ProblemAttribution",
            "name": "问题归属",
            "type": "string",
            "width": ""
        },
        {
            "key": "Component",
            "name": "组件",
            "type": "string",
            "width": ""
        },
        {
            "key": "FunctionModuleLevel1",
            "name": "功能模块层级1",
            "type": "string",
            "width": ""
        },
        {
            "key": "FunctionModuleLevel2",
            "name": "功能模块层级2",
            "type": "string",
            "width": ""
        },
        {
            "key": "IsTailorable",
            "name": "是否可裁剪",
            "type": "boolean",
            "width": ""
        },
        {
            "key": "IdentificationPhase",
            "name": "识别阶段",
            "type": "string",
            "width": ""
        },
        {
            "key": "CodeWalkThroughState",
            "name": "代码走查状态",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReason2_UnitTest",
            "name": "故障泄露二级原因（单元测试）",
            "type": "string",
            "width": ""
        },
        {
            "key": "SimulationTestResult",
            "name": "仿真测试结果",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReasonDetails_FunctionTest",
            "name": "故障泄露原因描述（功能测试）",
            "type": "string",
            "width": ""
        },
        {
            "key": "DiscoveryActivity",
            "name": "发现活动",
            "type": "string",
            "width": ""
        },
        {
            "key": "DevelopmentOwner",
            "name": "开发负责人",
            "type": "user",
            "width": ""
        },
        {
            "key": "ChangeSubmissionTime",
            "name": "变更提交时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "TaskClosedTime",
            "name": "任务关闭日期",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "Countersigner1",
            "name": "会签人1",
            "type": "user",
            "width": ""
        },
        {
            "key": "SolutionDescription_html",
            "name": "解决方案描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "NeedCustomCatalog",
            "name": "需要自定义分类",
            "type": "string",
            "width": ""
        },
        {
            "key": "TaskSubmitTime",
            "name": "任务提交时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "sj_creattest",
            "name": "是否触发创建自测报告",
            "type": "string",
            "width": ""
        },
        {
            "key": "OtherChangeReason",
            "name": "其他原因说明",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectLocationMode",
            "name": "缺陷定位方式",
            "type": "string",
            "width": ""
        },
        {
            "key": "IsKeyPara",
            "name": "是否关键字",
            "type": "boolean",
            "width": ""
        },
        {
            "key": "FaultIntroPoint_Ba",
            "name": "故障引入点（方案）",
            "type": "string",
            "width": ""
        },
        {
            "key": "TestMethod",
            "name": "测试方法",
            "type": "string",
            "width": ""
        },
        {
            "key": "ShowCaseUrl",
            "name": "ShowCase链接",
            "type": "string",
            "width": ""
        },
        {
            "key": "AuditDuration",
            "name": "审核时长",
            "type": "string",
            "width": ""
        },
        {
            "key": "Progress_html",
            "name": "进展",
            "type": "html",
            "width": ""
        },
        {
            "key": "WorkItemProgressOfMicroElectronics_html",
            "name": "微院工作项进展",
            "type": "html",
            "width": ""
        },
        {
            "key": "System_Description_html",
            "name": "描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "ControlLevel",
            "name": "控制级别",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReason1_SystemTestDesign",
            "name": "故障泄露一级原因（系统测试_测试设计）",
            "type": "string",
            "width": ""
        }
    ]

    review_map = {
        "标识": "标识",
        "标题": "主题",
        "描述": "描述",
        "开发负责人": "开发复盘负责人",
        "缺陷/故障等级": "缺陷等级",
        "发现活动": "发现活动",
        "测试方法": "发现方法",
        "变更提交时间": "提交日期",
        "任务关闭日期": "关闭日期",

        "会签人1": "故障引入人",
        "问题归属": "引入点所属领域",
        "故障引入环节": "引入点所属团队",

        "解决方案描述": "技术根因分析",
        "缺陷来源": "引入来源",
        "故障引入一级原因": "故障引入点根因一级分类",
        "故障引入二级原因": "故障引入点根因二级分类",
        "需要自定义分类": "故障引入点根因三级分类",
        "ShowCase链接": "故障引入gerrit入库链接",
        "功能模块层级1": "一级特性",
        "功能模块层级2": "二级特性",
        "故障引入点（开发）": "引入点复盘状态",

        "识别阶段": "最早可拦截阶段",
        "是否触发创建自测报告": "自测无法拦截的原因",
        "代码走查状态": "代码走查未拦截原因",
        "其他原因说明": "代码走查未拦截原因说明",
        "故障泄露二级原因（单元测试）": "是否可通过补充代码UT/FT拦截",
        "仿真测试结果": "是否可通过补充仿真FT拦截",
        "故障泄露原因描述（功能测试）": "是否可通过补充硬件FT/流水线FT拦截",
        "缺陷定位方式": "故障定界定位方式",
        "是否关键字": "是否需要复现定位或者占用环境定位",
        "定位时长": "定位时长",
        "控制级别": "故障控制点根因一级分类IT",
        "故障泄露一级原因（系统测试_测试设计）": "故障控制点根因二级分类IT",
        "故障引入点（方案）": "控制点复盘状态",

        "进展": "引入点改进举措",
        "微院工作项进展": "控制点改进举措"
    }

    # 获取review数据
    review_list = Rdc_list_get(query_condition, query_items, review_map, 10000)
    
    # 处理数据并更新到数据库
    if not review_list:
        print("没有需要更新的数据")
        return

    # 数据库连接与操作
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect('/home/10171727@zte.intra/workspace/AI/AI/public/website-linghang/flask/data/feature.db')
        cursor = conn.cursor()
        
        # 获取数据库表中实际存在的字段
        cursor.execute("PRAGMA table_info(review)")
        table_fields: Set[str] = {row[1] for row in cursor.fetchall()}
        print(f"数据库表中存在的字段: {sorted(table_fields)}")
        
        # 从数据中获取所有字段名，并筛选出数据库中存在的字段
        if not review_list:
            print("没有数据可处理")
            return
            
        data_fields = list(review_list[0].keys())
        # 筛选出数据库中存在的字段
        existing_fields = [field for field in data_fields if field in table_fields]
        
        # 检查主键是否存在
        if "标识" not in existing_fields:
            print("数据库表中缺少主键字段'标识'，无法更新数据库")
            return
            
        # 找出数据中有但数据库中没有的字段，并提示
        missing_fields = [field for field in data_fields if field not in table_fields]
        if missing_fields:
            print(f"以下字段在数据库中不存在，将被跳过: {missing_fields}")
        
        # 构建UPSERT SQL语句，只包含数据库中存在的字段
        non_primary_fields = [f for f in existing_fields if f != "标识"]
        insert_fields = ", ".join([f'"{f}"' for f in existing_fields])
        placeholders = ", ".join(["?" for _ in existing_fields])
        update_clause = ", ".join([f'"{f}" = excluded."{f}"' for f in non_primary_fields])
        
        sql = f"""
        INSERT INTO "review" ({insert_fields})
        VALUES ({placeholders})
        ON CONFLICT("标识") DO UPDATE SET {update_clause}
        """
        
        # 处理数据
        total = len(review_list)
        updated = 0
        inserted = 0
        
        for i, item in enumerate(review_list, 1):
            # 只提取数据库中存在的字段的值
            values = [item.get(field) for field in existing_fields]
            
            try:
                cursor.execute(sql, values)
                # 判断是插入还是更新
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                
                # 每100条提交一次
                if i % 100 == 0:
                    conn.commit()
                    print(f"已处理 {i}/{total} 条数据（插入: {inserted}, 更新: {updated}）")
            
            except sqlite3.Error as e:
                print(f"处理第 {i} 条数据时出错: {e}")
                print(f"出错数据: {item}")
                conn.rollback()
        
        # 提交剩余数据
        conn.commit()
        print(f"数据处理完成 - 总计: {total}, 插入: {inserted}, 更新: {updated}")
        if missing_fields:
            print(f"已跳过 {len(missing_fields)} 个数据库中不存在的字段")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return review_list

# --- 定义配置参数 ---
DB_PATH = "../data/feature.db"     # SQLite 数据库文件路径
DB_TABLE = "feature"               # 目标数据库表名

def API_Feature_read():
    """
    API 接口：从本地 SQLite 数据库读取指定 domain 下的所有 feature 数据。
    根据前端传入的 board 参数决定返回的 board 字段内容：
    - 若 board 为空，则返回该特性实际支持的所有单板列表。
    - 若 board 不为空，则返回 [board] (支持) 或 [] (不支持)。

    同时，关联 review 表，将 '二级特性' 与 'feature_name' 匹配的复盘记录摘要附加到对应特性中。
    """
    print("API_Feature_read: 接收到读取 feature 表的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # --- 提取参数 ---
    requested_domain = data.get('domain')
    requested_board = data.get('board')  # 可能是空字符串、None 或具体的单板名
    print(f"收到请求 - 目标表: {DB_TABLE}, 请求的领域: {requested_domain}, 请求的单板: '{requested_board}'")

    # 初始化返回数据列表
    table_data = []

    # --- 构建 SQL 查询 (feature + board) ---
    base_sql = f"""
    SELECT 
        f.feature_id,
        f.feature_name, 
        f.feature_function,
        f.feature_level,
        f.feature_page,
        f.domain,
        f.component,
        GROUP_CONCAT(fb.board_name, ',') AS all_boards_str 
    FROM feature f
    LEFT JOIN feature_board fb ON f.feature_name = fb.feature_name
    """

    # --- 根据 domain 参数决定查询条件 ---
    if requested_domain is None or requested_domain.strip() == "" or requested_domain.lower() == "all":
        final_sql = f"{base_sql} GROUP BY f.feature_name ORDER BY f.feature_id"
        params = ()
        print("查询条件: 所有领域 (domain=all 或未指定)")
    else:
        final_sql = f"{base_sql} WHERE f.domain = ? GROUP BY f.feature_name ORDER BY f.feature_id"
        params = (requested_domain,)
        print(f"查询条件: domain = '{requested_domain}'")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- 第一步：查询 feature 数据 ---
        print(f"正在执行 SQL (feature): {final_sql}")
        cursor.execute(final_sql, params)
        feature_rows = cursor.fetchall()

        # 如果没有查到任何特性，直接返回空列表
        if not feature_rows:
            print("未查询到任何特性记录。")
            return jsonify({
                "status": "success",
                "message": "未查询到符合条件的特性数据。",
                "tableData": []
            })

        # --- 第二步：提取所有 feature_name，用于批量查询 review ---
        # 从 feature_rows 中提取所有 feature_name
        feature_names = [row['feature_name'] for row in feature_rows]
        print(f"提取到 {len(feature_names)} 个特性名称用于关联复盘数据: {feature_names}")

        # --- 第三步：查询 review 表，批量获取所有相关的复盘记录 ---
        # 使用 IN 语句一次性查询，比循环查询效率高得多
        # 注意：SQLite 的 ? 占位符不能直接用于 IN 列表，需要动态生成占位符
        placeholders = ','.join('?' * len(feature_names))
        
        # 连接到新的数据库位置
        review_conn = sqlite3.connect("../data/sql_rdc.db")
        review_conn.row_factory = sqlite3.Row
        review_cursor = review_conn.cursor()
        
        review_sql = f"""
        SELECT 
            "标识", 
            "主题", 
            "提交日期",
            "一级特性",           -- 新增字段
            "二级特性",           -- 这个字段用于映射，保留
            "故障引入点根因一级分类", -- 新增字段
            "故障引入点根因二级分类",  -- 新增字段
            "故障控制点根因一级分类IT", -- 新增字段
            "故障控制点根因二级分类IT"  -- 新增字段
        FROM review 
        WHERE "二级特性" IN ({placeholders})
        ORDER BY "二级特性", "提交日期" DESC -- 按特性分组，按提交日期倒序（最新的在前）
        """
        print(f"正在执行 SQL (review): {review_sql}")
        review_cursor.execute(review_sql, feature_names)
        review_rows = review_cursor.fetchall()

        # --- 第四步：构建 review 映射字典 ---
        # key: feature_name (即 "二级特性" 的值)
        # value: 该特性对应的 review 摘要列表
        review_map = {}
        for row in review_rows:
            feature_name = row['二级特性']
            # 构建 review 摘要字典
            review_summary = {
                "标识": row['标识'],
                "主题": row['主题'],
                "提交日期": row['提交日期'],
                "一级特性": row['一级特性'], 
                "二级特性": row['二级特性'], 
                "故障引入点根因一级分类": row['故障引入点根因一级分类'],
                "故障引入点根因二级分类": row['故障引入点根因二级分类'],
                "故障控制点根因一级分类IT": row['故障控制点根因一级分类IT'],
                "故障控制点根因二级分类IT": row['故障控制点根因二级分类IT']
                # 只返回前端需要的摘要字段
            }
            # 如果这个 feature_name 还没有在字典中，先创建一个空列表
            if feature_name not in review_map:
                review_map[feature_name] = []
            # 将摘要添加到对应列表
            review_map[feature_name].append(review_summary)

        print(f"成功关联 {len(review_rows)} 条复盘记录，涉及 {len(review_map)} 个特性。")

        # --- 第五步：处理 feature 数据并合并 review ---
        for row in feature_rows:
            feature_dict = dict(row)
            
            # --- 处理单板信息 ---
            all_boards_str = feature_dict.get('all_boards_str')
            all_boards_list = []
            if all_boards_str:
                all_boards_list = [board.strip() for board in all_boards_str.split(',')]
            
            final_board_list = []
            if not requested_board or requested_board.strip() == "":
                final_board_list = all_boards_list
            else:
                if requested_board in all_boards_list:
                    final_board_list = [requested_board]
                else:
                    final_board_list = []
            
            feature_dict['board'] = final_board_list
            del feature_dict['all_boards_str'] # 清理临时字段

            # --- 关键修改：添加 review 信息 ---
            # 获取当前 feature_name
            current_feature_name = feature_dict['feature_name']
            # 从 review_map 中获取对应的 review 列表，如果没找到则返回空列表
            feature_dict['review'] = review_map.get(current_feature_name, [])

            table_data.append(feature_dict)

        print(f"成功读取并处理 {len(table_data)} 条特性记录（包含复盘信息）。")

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"读取数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if 'conn' in locals():
            conn.close()
            print("数据库连接已关闭。")
        if 'review_conn' in locals():
            review_conn.close()
            print("复盘数据数据库连接已关闭。")

    # --- 构造返回消息 ---
    base_msg = f"所有领域下的所有特性数据获取成功" if (not requested_domain or requested_domain.lower() == "all" or requested_domain.strip() == "") else f"领域 '{requested_domain}' 的所有特性数据获取成功"
    
    if not requested_board or requested_board.strip() == "":
        message = f"{base_msg}（查询全部单板支持情况），共 {len(table_data)} 条记录"
    else:
        message = f"{base_msg}，已标记是否支持单板 '{requested_board}'，共 {len(table_data)} 条记录"

    return jsonify({
        "status": "success",
        "message": message,
        "tableData": table_data
    })

def API_Board_read():
    """
    API 接口：从本地 SQLite 数据库读取所有 board 的信息，并关联查询所有特性列表
    （包含feature_id, feature_name, feature_level），并标记每个特性是否被支持。
    同时查询SDSSD数据，从sd表中获取Board表中SDSSD字段对应的SD类型属性。
    同时查询PHY数据，从phy表中获取Board表中PHY芯片字段对应的PHY型号属性。
    同时查询交换芯片数据，从switch表中获取Board表中交换芯片字段对应的型号属性。
    同时查询模块数据，从module表中获取Board表中单板名称对应的模块属性。

    返回格式：
    [
      {
        "单板编号": "xxx",
        "单板名称": "xxx",
        "单板类型": "xxx",
        "产品": "xxx",
        "子架": "xxx",
        "子卡": "xxx",
        "交换芯片": "xxx",
        "支持特性": [
            {
                "feature_id": "xxx",
                "feature_name": "xxx",
                "feature_level": "xxx",
                "feature_support": "已支持"或"未支持"
            },
            ...
        ],
        "SDSSD数据": [
            {
                "SD类型": "xxx",
                "厂家": "xxx",
                "容量": "xxx",
                "材质": "xxx",
                "接口类型": "xxx", 
                "代码": "xxx", 
                "总写入次数": "xxx", 
                "单block大小": "xxx", 
                "理论TBW": "xxx", 
                "每日写入上限": "xxx"
            },
            ...
        ],
        "PHY数据": [
            {
                "PHY型号": "xxx",
                "厂家": "xxx",
                "端口配置": "xxx",
                "端口类型": "xxx",
                "封装类型": "xxx", 
                "速率支持": "xxx", 
                "典型特性": "xxx"
            },
            ...
        ],
        "交换芯片数据": [
            {
                "型号": "xxx",
                "厂家": "xxx",
                "交换容量": "xxx",
                "端口配置": "xxx",
                "端口容量": "xxx", 
                "路由表容量": "xxx", 
            },
            ...
        ],
        "模块数据": [
            {
                "PN": "xxx",
                "模块类型": "xxx",
                "接口类型": "xxx",
                "速率Mbps": "xxx",
                "距离": "xxx",
                "制造厂商": "xxx",
                "应用代码": "xxx",
                "波长类型": "xxx",
                "物料代码": "xxx"
            },
            ...
        ]
      },
      ...
    ]
    """
    print("API_Board_read: 接收到读取 board 表的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # --- 提取参数 ---
    domain = data.get('domain')
    print(f"收到请求 - 目标表: {DB_TABLE}, 请求的领域: {domain}")

    # --- 初始化返回数据 ---
    board_data = []

    conn = None
    conn_sd = None
    conn_phy = None
    conn_switch = None
    conn_module = None
    conn_clock = None
    conn_cpu = None

    try:
        import sqlite3
        from flask import jsonify

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        cursor = conn.cursor()

        # 1. 查询指定 domain 的单板基本信息
        print(f"正在查询 domain='{domain}' 的单板基本信息")
        cursor.execute("""
            SELECT * FROM board 
            WHERE domain = ? 
            ORDER BY board_id
        """, (domain,))
        boards = cursor.fetchall()

        if not boards:
            print(f"未查询到 领域 为'{domain}' 的任何单板记录。")
            return jsonify({
                "status": "success",
                "message": f"未查询到 领域 为 '{domain}' 的单板数据。",
                "boardData": []
            })

        # 2. 获取指定领域下的特性信息
        print(f"正在查询领域='{domain}'的特性信息")
        cursor.execute("SELECT feature_id, feature_name, feature_level FROM feature WHERE domain = ? ORDER BY feature_id", (domain,))
        domain_features = cursor.fetchall()

        # 3. 遍历每个单板，填充其支持的特性和模块
        for board in boards:
            current_board = {
                "boardid": board['boardid'] if board['boardid'] else "",
                "functionid": board['functionid'] if board['functionid'] else "",
                "单板编号": board['board_id'],
                "单板名称": board['board_name'],
                "单板类型": board['单板类型'] if board['单板类型'] else "",
                "领域": board['domain'] if board['domain'] else "",
                "产品": board['产品'] if board['产品'] else "",
                "子架": board['子架'] if board['子架'] else "",
                "主控": board['主控'] if board['主控'] else "",
                "子卡": board['子卡'] if board['子卡'] else "",
                "交换芯片": board['交换芯片'] if board['交换芯片'] else "",
                "面板端口": board['面板端口'] if board['面板端口'] else "",
                "转发能力": board['转发能力'] if board['转发能力'] else "",
                "软件平台": board['软件平台'] if board['软件平台'] else "",
                "交叉方式": board['交叉方式'] if board['交叉方式'] else "",
                "PHY芯片": board['PHY芯片'] if board['PHY芯片'] else "",
                "时钟芯片": board['时钟芯片'] if board['时钟芯片'] else "",
                "内存": board['内存'] if board['内存'] else "",
                "SDSSD": board['SDSSD'] if board['SDSSD'] else "",
                "FPGA": board['FPGA'] if board['FPGA'] else "",
                "CPLD": board['CPLD'] if board['CPLD'] else "",
                "FLASH": board['FLASH'] if board['FLASH'] else "",
                "子架EEPROM": board['子架EEPROM'] if board['子架EEPROM'] else "",
                "母板EEPROM": board['母板EEPROM'] if board['母板EEPROM'] else "",
                "支持特性": [],  # 用于收集该领域下的特性及支持状态
                "支持模块": [],  # 用于收集所有模块信息
                "SDSSD数据": [],  # 用于收集匹配的SDSSD数据
                "PHY数据": [],    # 用于收集匹配的PHY数据
                "交换芯片数据": [], # 用于收集匹配的交换芯片数据
                "时钟芯片数据": [],
                "模块数据": [],    # 用于收集匹配的模块数据
                "CPU数据": [],    # 用于收集匹配的CPU数据
                "update_time": board['update_time'] if board['update_time'] else "",
                "update_user": board['update_user'] if board['update_user'] else ""
            }

            # 查询当前单板（通过 board_name）支持的特性 ID 列表（仅限该领域）
            cursor.execute("""
                SELECT f.feature_id 
                FROM feature_board fb
                JOIN feature f ON fb.feature_name = f.feature_name
                WHERE fb.board_name = ? AND f.domain = ?
            """, (board['board_name'], domain))
            supported_feature_ids = [row['feature_id'] for row in cursor.fetchall()]

            # 遍历该领域下的特性，判断是否支持
            for feature in domain_features:
                feature_info = {
                    "feature_id": feature['feature_id'],
                    "feature_name": feature['feature_name'],
                    "feature_level": feature['feature_level'] if feature['feature_level'] else "",
                    "feature_support": "已支持" if feature['feature_id'] in supported_feature_ids else "不支持"
                }
                current_board["支持特性"].append(feature_info)

            # 4. 查询当前单板支持的完整模块信息
            cursor.execute("""
                SELECT PN, 模块类型, 接口类型, 速率Mbps, 距离, 制造厂商, 应用代码, 波长类型, 物料代码
                FROM module 
                WHERE 支持单板 LIKE ?
            """, ('%' + board['board_name'] + '%',))
            
            modules = cursor.fetchall()
            for module in modules:
                module_info = {
                    "PN": module['PN'],
                    "模块类型": module['模块类型'],
                    "接口类型": module['接口类型'],
                    "速率Mbps": module['速率Mbps'],
                    "距离": module['距离'],
                    "制造厂商": module['制造厂商'],
                    "应用代码": module['应用代码'],
                    "波长类型": module['波长类型'],
                    "物料代码": module['物料代码']
                }
                current_board["支持模块"].append(module_info)

            # 5. 根据Board表中的SDSSD字段值（逗号分隔），查询sd表中匹配的SDSSD数据
            board_sdssd = board['SDSSD']
            if board_sdssd and board_sdssd.strip():
                sdssd_values = [val.strip() for val in board_sdssd.split(',') if val.strip()]
                print(f"正在查询单板 {board['board_name']} 的SDSSD数据: {sdssd_values}")
                conn_sd = sqlite3.connect("../data/feature.db")
                conn_sd.row_factory = sqlite3.Row
                cursor_sd = conn_sd.cursor()

                for sdssd_type in sdssd_values:
                    cursor_sd.execute("""
                        SELECT "SD类型", "厂家", "容量", "材质", "接口类型", 
                               "代码", "总写入次数", "单block大小", "理论TBW", 
                               "每日写入上限"
                        FROM sd
                        WHERE "SD类型" = ?
                    """, (sdssd_type,))
                    matching_sd_data = cursor_sd.fetchall()

                    for sd_record in matching_sd_data:
                        sd_info = {
                            "SD类型": sd_record['SD类型'] if sd_record['SD类型'] else "",
                            "厂家": sd_record['厂家'] if sd_record['厂家'] else "",
                            "容量": sd_record['容量'] if sd_record['容量'] else "",
                            "材质": sd_record['材质'] if sd_record['材质'] else "",
                            "接口类型": sd_record['接口类型'] if sd_record['接口类型'] else "",
                            "代码": sd_record['代码'] if sd_record['代码'] else "",
                            "总写入次数": sd_record['总写入次数'] if sd_record['总写入次数'] else "",
                            "单block大小": sd_record['单block大小'] if sd_record['单block大小'] else "",
                            "理论TBW": sd_record['理论TBW'] if sd_record['理论TBW'] else "",
                            "每日写入上限": sd_record['每日写入上限'] if sd_record['每日写入上限'] else ""
                        }
                        current_board["SDSSD数据"].append(sd_info)

                conn_sd.close()
                conn_sd = None
            else:
                print(f"单板 {board['board_name']} 的SDSSD字段为空，跳过查询SDSSD数据")

            # 6. 根据Board表中的PHY芯片字段值（逗号分隔），查询phy表中匹配的PHY数据
            board_phy = board['PHY芯片']
            if board_phy and board_phy.strip():
                phy_values = [val.strip() for val in board_phy.split(',') if val.strip()]
                print(f"正在查询单板 {board['board_name']} 的PHY数据: {phy_values}")
                conn_phy = sqlite3.connect("../data/feature.db")
                conn_phy.row_factory = sqlite3.Row
                cursor_phy = conn_phy.cursor()

                for phy_model in phy_values:
                    cursor_phy.execute("""
                        SELECT "PHY型号", "厂家", "端口配置", "端口类型", "封装类型", 
                               "速率支持", "典型特性", "支持单板"
                        FROM phy
                        WHERE "PHY型号" = ?
                    """, (phy_model,))
                    matching_phy_data = cursor_phy.fetchall()

                    for phy_record in matching_phy_data:
                        phy_info = {
                            "PHY型号": phy_record['PHY型号'] if phy_record['PHY型号'] else "",
                            "厂家": phy_record['厂家'] if phy_record['厂家'] else "",
                            "端口配置": phy_record['端口配置'] if phy_record['端口配置'] else "",
                            "端口类型": phy_record['端口类型'] if phy_record['端口类型'] else "",
                            "封装类型": phy_record['封装类型'] if phy_record['封装类型'] else "",
                            "速率支持": phy_record['速率支持'] if phy_record['速率支持'] else "",
                            "典型特性": phy_record['典型特性'] if phy_record['典型特性'] else "",
                            "支持单板": phy_record['支持单板'] if phy_record['支持单板'] else ""
                        }
                        current_board["PHY数据"].append(phy_info)

                conn_phy.close()
                conn_phy = None
            else:
                print(f"单板 {board['board_name']} 的PHY芯片字段为空，跳过查询PHY数据")

            # 7. 根据Board表中的交换芯片字段值（逗号分隔），查询switch表中匹配的交换芯片数据
            board_switch = board['交换芯片']
            if board_switch and board_switch.strip():
                switch_values = [val.strip() for val in board_switch.split(',') if val.strip()]
                print(f"正在查询单板 {board['board_name']} 的交换芯片数据: {switch_values}")
                conn_switch = sqlite3.connect("../data/feature.db")
                conn_switch.row_factory = sqlite3.Row
                cursor_switch = conn_switch.cursor()

                for switch_model in switch_values:
                    cursor_switch.execute("""
                        SELECT "型号", "厂家", "交换容量", "端口配置", "端口容量", 
                               "路由表容量"
                        FROM switch
                        WHERE "型号" = ?
                    """, (switch_model,))
                    matching_switch_data = cursor_switch.fetchall()

                    for switch_record in matching_switch_data:
                        switch_info = {
                            "型号": switch_record['型号'] if switch_record['型号'] else "",
                            "厂家": switch_record['厂家'] if switch_record['厂家'] else "",
                            "交换容量": switch_record['交换容量'] if switch_record['交换容量'] else "",
                            "端口配置": switch_record['端口配置'] if switch_record['端口配置'] else "",
                            "端口容量": switch_record['端口容量'] if switch_record['端口容量'] else "",
                            "路由表容量": switch_record['路由表容量'] if switch_record['路由表容量'] else "",
                        }
                        current_board["交换芯片数据"].append(switch_info)

                conn_switch.close()
                conn_switch = None
            else:
                print(f"单板 {board['board_name']} 的交换芯片字段为空，跳过查询交换芯片数据")

            # 8. 根据Board表中的单板名称，查询module表中匹配的模块数据
            board_name = board['board_name']
            if board_name and board_name.strip():
                module_values = [board_name.strip()]
                print(f"正在查询单板 {board['board_name']} 的模块数据")
                conn_module = sqlite3.connect("../data/feature.db")
                conn_module.row_factory = sqlite3.Row
                cursor_module = conn_module.cursor()

                for module_board in module_values:
                    cursor_module.execute("""
                        SELECT "PN", "模块类型", "接口类型", "速率Mbps", "距离", 
                               "制造厂商", "应用代码", "波长类型", "物料代码", "支持单板"
                        FROM module
                        WHERE "支持单板" LIKE ?
                    """, ('%' + module_board + '%',))
                    matching_module_data = cursor_module.fetchall()

                    for module_record in matching_module_data:
                        module_info = {
                            "PN": module_record['PN'] if module_record['PN'] else "",
                            "模块类型": module_record['模块类型'] if module_record['模块类型'] else "",
                            "接口类型": module_record['接口类型'] if module_record['接口类型'] else "",
                            "速率Mbps": module_record['速率Mbps'] if module_record['速率Mbps'] else "",
                            "距离": module_record['距离'] if module_record['距离'] else "",
                            "制造厂商": module_record['制造厂商'] if module_record['制造厂商'] else "",
                            "应用代码": module_record['应用代码'] if module_record['应用代码'] else "",
                            "波长类型": module_record['波长类型'] if module_record['波长类型'] else "",
                            "物料代码": module_record['物料代码'] if module_record['物料代码'] else "",
                            "支持单板": module_record['支持单板'] if module_record['支持单板'] else ""
                        }
                        current_board["模块数据"].append(module_info)

                conn_module.close()
                conn_module = None
            else:
                print(f"单板 {board['board_name']} 的单板名称字段为空，跳过查询模块数据")

            # 9. 根据Board表中的“时钟芯片”字段值（逗号分隔），查询clock表中匹配的时钟芯片数据
            board_clock_chip = board['时钟芯片']
            if board_clock_chip and board_clock_chip.strip():
                clock_values = [val.strip() for val in board_clock_chip.split(',') if val.strip()]
                print(f"正在查询单板 {board['board_name']} 的时钟芯片数据: {clock_values}")
                conn_clock = sqlite3.connect("../data/feature.db")
                conn_clock.row_factory = sqlite3.Row
                cursor_clock = conn_clock.cursor()

                for clock_model in clock_values:
                    cursor_clock.execute("""
                        SELECT "型号", "厂家", "支持单板"
                        FROM clock
                        WHERE "型号" = ?
                    """, (clock_model,))
                    matching_clock_data = cursor_clock.fetchall()

                    for clock_record in matching_clock_data:
                        clock_info = {
                            "型号": clock_record['型号'] if clock_record['型号'] else "",
                            "厂家": clock_record['厂家'] if clock_record['厂家'] else "",
                        }
                        current_board["时钟芯片数据"].append(clock_info)

                conn_clock.close()
                conn_clock = None
            else:
                print(f"单板 {board['board_name']} 的“时钟芯片”字段为空，跳过查询时钟芯片数据")

            # 10. 根据Board表中的"子卡"字段值（逗号分隔），查询cpu表中匹配的CPU数据
            board_subcard = board["子卡"]
            if board_subcard and board_subcard.strip():
                subcard_values = [val.strip() for val in board_subcard.split(",") if val.strip()]
                print(f"正在查询单板 {board['board_name']} 的CPU数据: {subcard_values}")
                conn_cpu = sqlite3.connect("../data/feature.db")
                conn_cpu.row_factory = sqlite3.Row
                cursor_cpu = conn_cpu.cursor()

                for subcard_model in subcard_values:
                    cursor_cpu.execute("""
                        SELECT "子卡型号", "子卡ID", "CPU架构", "DRAM容量"
                        FROM cpu
                        WHERE "子卡型号" = ?
                    """, (subcard_model,))
                    matching_cpu_data = cursor_cpu.fetchall()

                    for cpu_record in matching_cpu_data:
                        cpu_info = {
                            "子卡型号": cpu_record["子卡型号"] if cpu_record["子卡型号"] else "",
                            "子卡ID": cpu_record["子卡ID"] if cpu_record["子卡ID"] else "",
                            "CPU架构": cpu_record["CPU架构"] if cpu_record["CPU架构"] else "",
                            "DRAM容量": cpu_record["DRAM容量"] if cpu_record["DRAM容量"] else "",
                        }
                        current_board["CPU数据"].append(cpu_info)

                conn_cpu.close()
                conn_cpu = None
            else:
                print(f"单板 {board['board_name']} 的子卡字段为空，跳过查询CPU数据")
            board_data.append(current_board)

        print(f"成功读取并处理 {len(board_data)} 条属于 domain='{domain}' 的单板记录。")

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"读取单板数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("主数据库连接已关闭。")
        if conn_sd:  # 确保连接已关闭
            conn_sd.close()
            print("SDSSD数据库连接已关闭。")
        if conn_phy:  # 确保连接已关闭
            conn_phy.close()
            print("PHY数据库连接已关闭。")
        if conn_switch:  # 确保连接已关闭
            conn_switch.close()
            print("交换芯片数据库连接已关闭。")
        if conn_module:  # 确保连接已关闭
            conn_module.close()
            print("模块数据库连接已关闭。")
        if conn_clock:  # 关闭 clock 数据库连接
            conn_clock.close()
            print("时钟芯片数据库连接已关闭。")
        if conn_cpu:  # 关闭 cpu 数据库连接
            conn_cpu.close()
            print("CPU数据库连接已关闭。")

    # --- 返回成功响应 ---
    return jsonify({
        "status": "success",
        "message": f"领域 为'{domain}' 的单板数据获取成功，共 {len(board_data)} 条记录。",
        "boardData": board_data
    })

def API_Board_get():
    """
    API 接口：从本地 SQLite 数据库获取单板信息
    - 若提供 board_name，则返回该单板信息
    - 若 board_name 为空字符串或未提供，则返回所有单板信息
    - 若提供 domain，则按领域筛选单板
    - 若未提供任何参数，则查询整张表返回
    """
    print("API_Board_get: 接收到获取单板信息的请求")

    # 获取前端发送的JSON数据，如果没有数据则设为None
    data = request.get_json() or {}
    
    # 即使没有传入参数，也要继续执行查询整表的逻辑
    board_name = data.get('board_name') if data else None
    domain = data.get('domain') if data else None

    def row_to_dict(row):
        """将 SQLite Row 对象转换为标准化字典"""
        # 安全地访问数据库行的字段，避免 KeyError
        def safe_get(row, key, default=""):
            try:
                return row[key] or default
            except:
                return default
                
        return {
            "boardid": safe_get(row, 'boardid'),
            "functionid": safe_get(row, 'functionid'),
            "board_id": safe_get(row, 'board_id'),
            "board_name": safe_get(row, 'board_name'),
            "单板类型": safe_get(row, '单板类型'),
            "领域": safe_get(row, '领域'),  # 有些表可能没有这个字段
            "产品": safe_get(row, '产品'),
            "子架": safe_get(row, '子架'),
            "主控": safe_get(row, '主控'),
            "子卡": safe_get(row, '子卡'),
            "交换芯片": safe_get(row, '交换芯片'),
            "面板端口": safe_get(row, '面板端口'),
            "转发能力": safe_get(row, '转发能力'),
            "软件平台": safe_get(row, '软件平台'),
            "交叉方式": safe_get(row, '交叉方式'),
            "PHY芯片": safe_get(row, 'PHY芯片'),
            "时钟芯片": safe_get(row, '时钟芯片'),
            "内存": safe_get(row, '内存'),
            "SDSSD": safe_get(row, 'SDSSD'),
            "FPGA": safe_get(row, 'FPGA'),
            "CPLD": safe_get(row, 'CPLD'),
            "FLASH": safe_get(row, 'FLASH'),
            "子架EEPROM": safe_get(row, '子架EEPROM'),
            "母板EEPROM": safe_get(row, '母板EEPROM'),
            "domain": safe_get(row, 'domain'),
            "update_time": safe_get(row, 'update_time'),
            "update_user": safe_get(row, 'update_user')
        }

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 如果提供了board_name，查询特定单板
        if board_name:
            print(f"正在查询单板 '{board_name}' 的信息")
            cursor.execute("SELECT * FROM board WHERE board_name = ?", (board_name,))
            rows = cursor.fetchall()

            if not rows:
                return jsonify({
                    "status": "error",
                    "message": f"未找到名称为 '{board_name}' 的单板记录"
                }), 404

            message = f"单板 '{board_name}' 信息获取成功"
        else:
            # 根据是否提供domain参数决定查询条件
            if domain:
                print(f"正在查询领域 '{domain}' 的所有单板信息")
                cursor.execute("SELECT * FROM board WHERE domain = ? ORDER BY board_id", (domain,))
                message = f"领域 '{domain}' 的单板信息获取成功"
            else:
                # 如果没有提供任何参数或参数为空，查询整张表
                print("正在查询所有单板信息")
                cursor.execute("SELECT * FROM board ORDER BY board_id")
                message = "所有单板信息获取成功"
            
            rows = cursor.fetchall()

            if not rows:
                domain_msg = f"领域 '{domain}' 的" if domain else ""
                return jsonify({
                    "status": "success",
                    "message": f"数据库中没有{domain_msg}单板记录",
                    "boardData": []
                })

        # ✅ 统一处理：无论单条还是多条，都用 row_to_dict 转换
        board_data = [row_to_dict(row) for row in rows]

        print(f"成功获取数据，共 {len(board_data)} 条记录")
        return jsonify({
            "status": "success",
            "message": message,
            "boardData": board_data
        })

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"获取单板数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Board_set():
    """
    API 接口：在本地 SQLite 数据库中设置（新增或修改）单板信息
    
    如果指定 board_name 的单板不存在，则新增一行；
    如果已存在，则修改该行信息。
    
    请求参数：
    - board_id: 单板编号
    - board_name: 单板名称（主键）
    - 单板类型: 单板类型
    - 产品: 产品
    - 子架: 子架
    - 主控: 主控
    - 子卡: 子卡
    - 交换芯片: 交换芯片
    - 面板端口: 面板端口
    - 转发能力: 转发能力
    - 软件平台: 软件平台
    - 交叉方式: 交叉方式
    - domain: 领域
    - update_user: 更新人
    
    返回格式：
    {
        "status": "success",
        "message": "单板信息设置成功"
    }
    """
    print("API_Board_set: 接收到设置单板信息的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # 提取参数
    board_name = data.get('board_name')
    if not board_name:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: board_name"
        }), 400

    # 获取更新人信息
    update_user = data.get('update_user', '')
    if not update_user:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: update_user"
        }), 400

    print(f"收到请求 - 目标单板: {board_name}, 更新人: {update_user}")

    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查单板是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM board 
            WHERE board_name = ?
        """, (board_name,))
        
        exists = cursor.fetchone()[0] > 0

        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建SQL语句和参数
        if exists:
            # 更新已存在的单板信息
            sql = """
                UPDATE board SET
                    board_id = ?,
                    单板类型 = ?,
                    产品 = ?,
                    子架 = ?,
                    主控 = ?,
                    子卡 = ?,
                    交换芯片 = ?,
                    面板端口 = ?,
                    转发能力 = ?,
                    软件平台 = ?,
                    交叉方式 = ?,
                    PHY芯片 = ?,
                    时钟芯片 = ?,
                    内存 = ?,
                    SDSSD = ?,
                    FPGA = ?,
                    CPLD = ?,
                    FLASH = ?,
                    子架EEPROM = ?,
                    母板EEPROM = ?,
                    domain = ?,
                    boardid = ?,
                    functionid = ?,
                    update_time = ?,
                    update_user = ?
                WHERE board_name = ?
            """
            params = (
                data.get('board_id', ''),
                data.get('单板类型', ''),
                data.get('产品', ''),
                data.get('子架', ''),
                data.get('主控', ''),
                data.get('子卡', ''),
                data.get('交换芯片', ''),
                data.get('面板端口', ''),
                data.get('转发能力', ''),
                data.get('软件平台', ''),
                data.get('交叉方式', ''),
                data.get('PHY芯片', ''),
                data.get('时钟芯片', ''),
                data.get('内存', ''),
                data.get('SDSSD', ''),
                data.get('FPGA', ''),
                data.get('CPLD', ''),
                data.get('FLASH', ''),
                data.get('子架EEPROM', ''),
                data.get('母板EEPROM', ''),
                data.get('domain', ''),
                data.get('boardid', ''),
                data.get('functionid', ''),
                current_time,
                update_user,
                board_name
            )
            action = "更新"
        else:
            # 新增单板信息
            sql = """
                INSERT INTO board (
                    board_id, board_name, 单板类型, 产品, 子架, 主控, 子卡, 
                    交换芯片, 面板端口, 转发能力, 软件平台, 交叉方式, PHY芯片, 时钟芯片,
                    内存, SDSSD, FPGA, CPLD, FLASH, 子架EEPROM, 母板EEPROM, domain,
                    boardid, functionid, update_time, update_user
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('board_id', ''),
                board_name,
                data.get('单板类型', ''),
                data.get('产品', ''),
                data.get('子架', ''),
                data.get('主控', ''),
                data.get('子卡', ''),
                data.get('交换芯片', ''),
                data.get('面板端口', ''),
                data.get('转发能力', ''),
                data.get('软件平台', ''),
                data.get('交叉方式', ''),
                data.get('PHY芯片', ''),
                data.get('时钟芯片', ''),
                data.get('内存', ''),
                data.get('SDSSD', ''),
                data.get('FPGA', ''),
                data.get('CPLD', ''),
                data.get('FLASH', ''),
                data.get('子架EEPROM', ''),
                data.get('母板EEPROM', ''),
                data.get('domain', ''),
                data.get('boardid', ''),
                data.get('functionid', ''),
                current_time,
                update_user
            )
            action = "新增"

        # 执行SQL语句
        print(f"正在{action}单板 '{board_name}' 的信息")
        cursor.execute(sql, params)
        conn.commit()

        print(f"成功{action}单板 '{board_name}' 的信息")

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": f"单板 '{board_name}' 信息{action}成功"
        })

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"{action}单板数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")


def API_Board_del():
    """
    API 接口：从本地 SQLite 数据库删除指定 board_name 的单板信息
    
    请求参数：
    - board_name (必需): 要删除的单板名称
    - update_user (必需): 更新人
    
    返回格式：
    {
        "status": "success",
        "message": "单板信息删除成功"
    }
    """
    print("API_Board_del: 接收到删除单板信息的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # 提取参数
    board_name = data.get('board_name')
    if not board_name:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: board_name"
        }), 400

    # 获取更新人信息（必需参数）
    update_user = data.get('update_user')
    if not update_user:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: update_user"
        }), 400

    print(f"收到请求 - 目标单板: {board_name}, 更新人: {update_user}")

    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查单板是否存在
        cursor.execute("""
            SELECT COUNT(*) FROM board 
            WHERE board_name = ?
        """, (board_name,))
        
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            return jsonify({
                "status": "error",
                "message": f"未找到名称为 '{board_name}' 的单板记录"
            }), 404

        # 删除指定单板的信息
        print(f"正在删除单板 '{board_name}' 的信息")
        cursor.execute("""
            DELETE FROM board 
            WHERE board_name = ?
        """, (board_name,))
        
        conn.commit()

        print(f"成功删除单板 '{board_name}' 的信息")

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": f"单板 '{board_name}' 信息删除成功"
        })

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"删除单板数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")


# 定义数据库和表的映射关系
TABLE_CONFIG_MAP = {
    "SD器件库": {
        "db_path": "../data/feature.db",
        "table_name": "sd",
        "key_field": "SD类型",
        "fields": [
            "SD类型", "厂家", "容量", "材质", "接口类型", 
            "代码", "支持主控", "总写入次数", "单block大小", "理论TBW", 
            "每日写入上限"
        ]
    },
    "光模块库": {
        "db_path": "../data/feature.db",
        "table_name": "module",
        "key_field": "PN",
        "fields": [
            "PN", "模块类型", "接口类型", "速率Mbps", "距离", 
            "制造厂商", "应用代码", "波长类型", "物料代码", "支持单板"
        ]
    },
    "单板库": {
        "db_path": "../data/feature.db",
        "table_name": "board",
        "key_field": "board_name",
        "fields": [
            "board_id", "board_name", "单板类型", "产品", "子架", 
            "主控", "子卡", "交换芯片", "面板端口", "转发能力", 
            "软件平台", "交叉方式", "domain", "update_time", 
            "update_user", "PHY芯片", "时钟芯片", "内存", 
            "SDSSD", "FPGA", "CPLD", "FLASH", "子架EEPROM", 
            "母板EEPROM", "boardid", "functionid"
        ]
    },
    "代码库": {
        "db_path": "../data/feature.db",
        "table_name": "repo",
        "key_field": "代码库",
        "fields": [
            "代码库", "分支", "变更次数", "新增行", "删除行", 
            "领域", "关联故障", "关联组件"
        ]
    },
    "命令库": {
        "db_path": "../data/feature.db",
        "table_name": "api",
        "key_field": ["命令类型", "命令码"],  # 复合主键
        "fields": [
            "命令类型", "命令码", "命令名称", "命令来源", "关联特性", 
            "关联命令", "关联组件", "数据存储", "处理流程", "白盒梳理", "处理规则"
        ]
    },
    "故障库": {
        "db_path": "../data/sql_rdc.db",
        "table_name": "issue",
        "key_field": "标识",
        "fields": [
            "标识", "标题", "描述", "状态",
            "变更大类", "缺陷等级", "缺陷来源", "发现活动", "发现方法", "发现版本", "创建时间", "关闭时间",
            "所属产品", "所属项目", "领域", "团队",
            "引入人", "引入人部门", "发现人", "发现人部门", "进展", "备注", "计划解决日期", "自测报告链接"
        ]
    },
    "交换芯片库": {
        "db_path": "../data/feature.db",
        "table_name": "switch",
        "key_field": "型号",
        "fields": [
            "型号", "厂家", "交换容量", "端口配置", "端口容量", 
            "路由表容量", "支持主控", "支持单板"
        ]
    },
    "PHY库": {
        "db_path": "../data/feature.db",
        "table_name": "phy",
        "key_field": "PHY型号",
        "fields": [
            "PHY型号", "厂家", "端口配置", "端口类型", "封装类型", 
            "速率支持", "典型特性", "支持单板"
        ]
    },
    "分支库": {
        "db_path": "../data/sql_config.db",
        "table_name": "branch",
        "key_field": "分支名称",  # 主键
        "fields": [
            "分支名称", "分支状态", "分支活跃度", "合入策略", "拉取时间", 
            "关联项目", "关联版本", "关联单板", "待合入需求", "待合入故障", 
            "代码链接"
        ]
    },
    "任务库": {
        "db_path": "../data/sql_task.db",
        "table_name": "task",
        "key_field": "标识",
        "fields": [
            "标识", "标题", "描述", "状态", "指派给", "领域", "团队", "迭代"
        ]
    },
    "版本库": {
        "db_path": "../data/sql_config.db",
        "table_name": "version",
        "key_field": ["版本"],
        "fields": [
            "版本", "目标", "分支", "主控",
            "需求情况", "故障情况", "版本风险情况", "团队风险情况",
            "版本号", "关联故障", "版本状态", "版本发布时间",
            "编译构建时间", "主控系统类型", "版本链接", "关联故障横推通告"
        ]
    },
    "时钟芯片库": {
        "db_path": "../data/feature.db",
        "table_name": "clock",
        "key_field": ["型号"],
        "fields": [
            "型号", "厂家", "支持单板"
        ]
    },
    "用例库": {
        "db_path": "../data/sql_test.db",
        "table_name": "testcase",
        "key_field": "用例编号",
        "fields": [
            "用例编号", "用例名称", "领域", "特性", "功能点", "测试点", 
            "预置条件(G)", "测试步骤(W)", "预期结果(T)", "标签", "优先级", "测试类型", 
            "测试分层", "是否通用用例", "是否异常测试", "是否可自动化", 
            "编写人", "维护人", "用例来源", "导入路径"
        ]
    },
    "AI应用库": {
        "db_path": "../data/sql_config.db",
        "table_name": "dnstdio",
        "key_field": "AI应用名称",
        "fields": [
            "AI应用名称", "AI应用描述","AI应用场景", "AI应用类型",  "AI应用平台", 
            "领域", "团队",  "组件",  "是否范式", "key", "appid", "使用指导"
        ]
    },
    "task_team_summary": {
        "db_path": "../data/sql_task.db",
        "table_name": "team_summary",
        "key_field": ["迭代", "团队"],
        "fields": [
            "迭代", "团队", "任务总数", "AI辅助生成树", "AI生成代码行数"
        ]
    },
    "task_component_summary": {
        "db_path": "../data/sql_task.db",
        "table_name": "component_summary",
        "key_field": ["迭代", "波及组件"],
        "fields": [
            "迭代", "波及组件", "任务总数", "AI辅助生成树", "AI生成代码行数"
        ]
    },
    "升级前巡检库": {
        "db_path": "../data/feature.db",
        "table_name": "upgrade_before",
        "key_field": "序号",
        "fields": [
            "序号", "单板", "巡检大类", "操作项", "优先级", 
            "检查标准", "操作方法", "现网操作方法", "应急方法", "操作风险"
        ]
    },
    "FPGA地址库": {
        "db_path": "../data/feature.db",
        "table_name": "fpga_addr",
        "key_field": ["板类型", "基地址名称"],
        "fields": [
            "板类型","BOM ID", "基地址名称", "FPGA ID", "基地址"
        ]
    },
    "EEPROM库": {
        "db_path": "../data/feature.db",
        "table_name": "eeprom",
        "key_field": "主控类型",
        "fields": [
            "主控类型", "访问通道", "接口", "母板eeprom个数", "母板eeprom位置", "母板eeprom支持备份", 
            "母板eeprom失效检测", "单板eeprom1", "单板eeprom2", "背板eeprom个数", "背板eeprom互斥锁", 
            "主备互斥访问寄存器", "背板eeprom支持备份", "背板eeprom失效检测"
        ]
    },
    "分支漏合库": {
        "db_path": "../data/sql_config.db",
        "table_name": "leakage_branch",
        "key_field": "标识",
        "fields": [
            "标识", "提交链接", "首次合入时间", "提交人",
            "所属部门", "所属团队", "实际合入分支", "应波及分支",
            "遗漏分支", "是否增量"
        ]
    },
    "硬件检查库": {
        "db_path": "../data/feature.db",
        "table_name": "device_check",
        "key_field": ["器件类型", "功能大类", "功能细分"],
        "fields": [
            "器件类型", "功能大类", "功能细分", "功能细分内容"
        ]
    },
    "CPU库": {
        "db_path": "../data/feature.db",
        "table_name": "cpu",
        "key_field": "子卡型号",
        "fields": [
            "子卡型号", "子卡ID", "CPU架构", "DRAM容量", "支持主控"
        ]
    },
    "单板温度检测库": {
        "db_path": "../data/feature.db",
        "table_name": "board_temperature_check",
        "key_field": ["单板名称", "FRU中的温度检测点"],
        "fields": [
            "单板名称", "是否带有IPMC", "FRU中的温度检测点", "FRU中的温度检测点id", 
            "FRU中的温度检测点定标温度", "软件是否上报检测点温度参与风扇调速", 
            "软件上报温度是否有归一化处理", "单板是否支持关键器件超温告警上报以及告警上报条件", 
            "备注"
        ]
    },
    "PE模版库": {
        "db_path": "../data/chat.db",
        "table_name": "prompt",
        "key_field": "主题",
        "fields": [
            "主题", "摘要", "内容", "场景", "创建人", "创建时间", "引用次数"
        ]
    },
}

def API_Table_get():
    """
    API 接口：从本地 SQLite 数据库读取指定表的数据
    - 若前端未传入任何参数，则查询整表返回
    - 若传入参数，可以包含多个字段条件进行匹配查询
    
    请求参数：
    - user (必需): 用户名
    - table_name (必需): 表名（必须在TABLE_CONFIG_MAP中）
    - conditions (可选): 查询条件字典，如 {"主控": "ncpk", "单板类型": "E卡"}
    
    返回格式：
    {
        "status": "success",
        "message": "数据获取成功",
        "data": [...]
    }
    """
    print("API_Table_get: 接收到获取表数据的请求")

    # 获取前端发送的JSON数据
    request_data = request.get_json() or {}
    
    # 提取参数
    user = request_data.get('user')
    table_name = request_data.get('table_name')
    conditions = request_data.get('conditions', {})
    
    # 检查表名是否在映射中
    if not table_name or table_name not in TABLE_CONFIG_MAP:
        return jsonify({
            "status": "error",
            "message": f"表名 '{table_name}' 不存在或未配置",
            "data": []
        }), 400
    
    # 获取表配置
    table_config = TABLE_CONFIG_MAP[table_name]
    db_path = table_config["db_path"]
    table_name_in_db = table_config["table_name"]
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询语句
        if conditions and isinstance(conditions, dict) and len(conditions) > 0:
            # 如果提供了查询条件，则按条件查询
            where_clauses = []
            values = []
            
            for field, value in conditions.items():
                if isinstance(value, str) and ',' in value:
                    split_values = [v.strip() for v in value.split(',') if v.strip()]
                    if split_values:
                        like_conditions = []
                        for v in split_values:
                            like_conditions.append(f'"{field}" LIKE ?')
                            values.append(f"%{v}%")
                        where_clauses.append("(" + " OR ".join(like_conditions) + ")")
                    else:
                        # 全是空值的情况，添加永假条件
                        where_clauses.append("1=0")
                elif isinstance(value, list):
                    # 如果值是列表，使用 LIKE IN 子句（通过 OR 连接多个 LIKE 条件）
                    if value:  # 确保列表非空
                        # 为列表中的每个值创建 LIKE 条件
                        like_conditions = []
                        for v in value:
                            # 如果是字符串，添加通配符；否则按原值处理
                            if isinstance(v, str):
                                like_conditions.append(f'"{field}" LIKE ?')
                                values.append(f"%{v}%")
                            else:
                                like_conditions.append(f'"{field}" = ?')  # 非字符串值仍使用精确匹配
                                values.append(v)
                        where_clauses.append("(" + " OR ".join(like_conditions) + ")")
                    else:
                        # 如果列表为空，添加一个永不满足的条件
                        where_clauses.append("1=0")
                else:
                    # 否则使用 LIKE 条件（对字符串值进行模糊匹配）
                    if isinstance(value, str):
                        where_clauses.append(f'"{field}" LIKE ?')
                        values.append(f"%{value}%")
                    else:
                        # 非字符串值仍使用精确匹配
                        where_clauses.append(f'"{field}" = ?')
                        values.append(value)
            
            where_clause = " AND ".join(where_clauses)
            sql = f'SELECT * FROM "{table_name_in_db}" WHERE {where_clause}'
            cursor.execute(sql, values)
            message = f"表 '{table_name}' 中符合条件的记录获取成功"
        else:
            # 如果没有提供查询条件，则查询整表
            sql = f"SELECT * FROM {table_name_in_db}"
            cursor.execute(sql)
            message = f"表 '{table_name}' 的所有记录获取成功"
        
        rows = cursor.fetchall()
        
        # 转换为字典列表
        table_data = [dict(row) for row in rows]
        
        print(f"成功获取数据，共 {len(table_data)} 条记录")
        return jsonify({
            "status": "success",
            "message": message,
            "data": table_data
        })
        
    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}",
            "data": []
        }), 500
        
    except Exception as e:
        print(f"获取表数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}",
            "data": []
        }), 500
        
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def TOOL_Table_get(table_name, conditions=None):
    """
    内部工具函数：从本地 SQLite 数据库读取指定表的数据
    - 若未传入 conditions 或 conditions 为空，则查询整表返回
    - 若传入 conditions，可以包含多个字段条件进行匹配查询
    
    参数：
    - table_name (必需): 表名（必须在TABLE_CONFIG_MAP中）
    - conditions (可选): 查询条件字典，如 {"主控": "ncpk", "单板类型": "E卡"}
    
    返回格式：
    {
        "status": "success",
        "message": "数据获取成功",
        "data": [...]
    }
    """
    print(f"TOOL_Table_get: 接收到获取表数据的请求，表名: {table_name}")

    # 检查表名是否在映射中
    if not table_name or table_name not in TABLE_CONFIG_MAP:
        return {
            "status": "error",
            "message": f"表名 '{table_name}' 不存在或未配置",
            "data": []
        }
    
    # 获取表配置
    table_config = TABLE_CONFIG_MAP[table_name]
    db_path = table_config["db_path"]
    table_name_in_db = table_config["table_name"]
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询语句
        if conditions and isinstance(conditions, dict) and len(conditions) > 0:
            # 如果提供了查询条件，则按条件查询
            where_clauses = []
            values = []
            
            for field, value in conditions.items():
                if isinstance(value, list):
                    # 如果值是列表，使用 LIKE IN 子句（通过 OR 连接多个 LIKE 条件）
                    if value:  # 确保列表非空
                        # 为列表中的每个值创建 LIKE 条件
                        like_conditions = []
                        for v in value:
                            # 如果是字符串，去除空格后再添加通配符；否则按原值处理
                            if isinstance(v, str):
                                v_stripped = v.strip()  # 去除字符串两边的空格
                                like_conditions.append(f"{field} LIKE ?")
                                values.append(f"%{v_stripped}%")
                            else:
                                like_conditions.append(f"{field} = ?")  # 非字符串值仍使用精确匹配
                                values.append(v)
                        where_clauses.append("(" + " OR ".join(like_conditions) + ")")
                    else:
                        # 如果列表为空，添加一个永不满足的条件
                        where_clauses.append("1=0")
                else:
                    # 否则使用 LIKE 条件（对字符串值进行模糊匹配）
                    if isinstance(value, str):
                        value_stripped = value.strip()  # 去除字符串两边的空格
                        where_clauses.append(f"{field} LIKE ?")
                        values.append(f"%{value_stripped}%")
                    else:
                        # 非字符串值仍使用精确匹配
                        where_clauses.append(f"{field} = ?")
                        values.append(value)
            
            where_clause = " AND ".join(where_clauses)
            sql = f"SELECT * FROM {table_name_in_db} WHERE {where_clause}"
            cursor.execute(sql, values)
            message = f"表 '{table_name}' 中符合条件的记录获取成功！"
        else:
            # 如果没有提供查询条件，则查询整表
            sql = f"SELECT * FROM {table_name_in_db}"
            cursor.execute(sql)
            message = f"表 '{table_name}' 的所有记录获取成功！"
        
        rows = cursor.fetchall()
        
        # 转换为字典列表
        table_data = [dict(row) for row in rows]
        
        print(f"成功获取数据，共 {len(table_data)} 条记录")
        return {
            "status": "success",
            "message": message + f"共 {len(table_data)} 条记录。",
            "data": table_data
        }
        
    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return {
            "status": "error",
            "message": f"数据库错误: {str(e)}",
            "data": []
        }
        
    except Exception as e:
        print(f"获取表数据时发生未预期错误: {e}")
        return {
            "status": "error",
            "message": f"内部服务器错误: {str(e)}",
            "data": []
        }
        
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Table_set():
    """
    API 接口：在本地 SQLite 数据库中设置（新增或修改）表数据
    - 如果记录不存在，则新增一行
    - 如果记录已存在，则只更新传入的字段，未传入的字段保持原值
    
    请求参数：
    - user (必需): 用户名
    - table_name (必需): 表名（必须在TABLE_CONFIG_MAP中）
    - conditions (必需): 要更新的数据字段字典
    
    返回格式：
    {
        "status": "success",
        "message": "数据设置成功",
        "data": []
    }
    """
    print("API_Table_set: 接收到设置表数据的请求")

    # 获取前端发送的JSON数据
    request_data = request.get_json()
    if not request_data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式",
            "data": []
        }), 400

    # 提取参数
    user = request_data.get('user')
    table_name = request_data.get('table_name')
    conditions = request_data.get('conditions', {})
    
    # 检查表名是否在映射中
    if not table_name or table_name not in TABLE_CONFIG_MAP:
        return jsonify({
            "status": "error",
            "message": f"表名 '{table_name}' 不存在或未配置",
            "data": []
        }), 400
    
    # 检查是否有要更新的数据
    if not conditions:
        return jsonify({
            "status": "error",
            "message": "缺少要更新的数据",
            "data": []
        }), 400
    
    # 获取表配置
    table_config = TABLE_CONFIG_MAP[table_name]
    db_path = table_config["db_path"]
    table_name_in_db = table_config["table_name"]
    key_field = table_config["key_field"]
    
    # 检查关键字段是否存在（处理单字段和复合主键的情况）
    if isinstance(key_field, list):
        # 处理复合主键
        missing_fields = [field for field in key_field if field not in conditions]
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"缺少关键字段: {', '.join(missing_fields)}",
                "data": []
            }), 400
        
        # 构建查询条件
        where_clause = " AND ".join([f"{field} = ?" for field in key_field])
        key_values = [conditions[field] for field in key_field]
    else:
        # 处理单字段主键
        if key_field not in conditions:
            return jsonify({
                "status": "error",
                "message": f"缺少关键字段: {key_field}",
                "data": []
            }), 400
        
        where_clause = f"{key_field} = ?"
        key_values = (conditions[key_field],)
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查记录是否已存在
        check_sql = f'SELECT COUNT(*) FROM "{table_name_in_db}" WHERE {where_clause}'
        cursor.execute(check_sql, key_values)
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # 更新已存在的记录
            # 构建更新语句，只更新传入的字段（除了关键字段）
            if isinstance(key_field, list):
                # 对于复合主键，排除所有主键字段
                update_fields = {k: v for k, v in conditions.items() if k not in key_field}
            else:
                # 对于单字段主键，排除该字段
                update_fields = {k: v for k, v in conditions.items() if k != key_field}
                
            if update_fields:
                set_clause = ", ".join([f'"{field}" = ?' for field in update_fields.keys()])
                values = list(update_fields.values())
                
                # 重新构建主键的WHERE条件
                if isinstance(key_field, list):
                    pk_where_clause = " AND ".join([f'"{field}" = ?' for field in key_field])
                else:
                    pk_where_clause = f'"{key_field}" = ?'
                
                # 添加主键值作为WHERE条件
                values.extend(key_values)
                
                sql = f'UPDATE "{table_name_in_db}" SET {set_clause} WHERE {pk_where_clause}'
                cursor.execute(sql, values)
                action = "更新"
            else:
                # 如果没有其他字段需要更新，直接返回成功
                action = "检查"
        else:
            # 新增记录
            # 确保所有字段都包含在插入数据中（缺失的字段用空字符串填充）
            fields = list(conditions.keys())
            quoted_fields = [f'"{field}"' for field in fields]
            placeholders = ", ".join(["?" for _ in fields])
            values = [conditions[field] for field in fields]
            
            sql = f'INSERT INTO "{table_name_in_db}" ({", ".join(quoted_fields)}) VALUES ({placeholders})'
            cursor.execute(sql, values)
            action = "新增"
        
        conn.commit()
        
        # 构建显示的主键信息
        if isinstance(key_field, list):
            key_info = ", ".join([f"{field} = '{conditions[field]}'" for field in key_field])
        else:
            key_info = f"{key_field} = '{conditions[key_field]}'"
        
        print(f"成功{action}表 '{table_name}' 中 {key_info} 的记录")
        
        # 数据库更新成功，保存本次变更记录
        table_update_record(table_name, user, action, conditions)

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": f"表 '{table_name}' 中 {key_info} 的记录{action}成功",
            "data": []
        })
        
    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}",
            "data": []
        }), 500
        
    except Exception as e:
        print(f"删除表数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}",
            "data": []
        }), 500
        
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Table_del():
    """
    API 接口：从本地 SQLite 数据库删除指定表中的一行数据
    
    请求参数：
    - user (必需): 用户名
    - table_name (必需): 表名（必须在TABLE_CONFIG_MAP中）
    - conditions (必需): 删除条件字典，必须包含关键字段和值
    
    返回格式：
    {
        "status": "success",
        "message": "数据删除成功",
        "data": []
    }
    """
    print("API_Table_del: 接收到删除表数据的请求")

    # 获取前端发送的JSON数据
    request_data = request.get_json()
    if not request_data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式",
            "data": []
        }), 400

    # 提取参数
    user = request_data.get('user')
    table_name = request_data.get('table_name')
    conditions = request_data.get('conditions', {})
    
    # 检查必需参数
    if not table_name:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: table_name",
            "data": []
        }), 400
    
    if not conditions:
        return jsonify({
            "status": "error",
            "message": "缺少删除条件",
            "data": []
        }), 400
    
    # 检查表名是否在映射中
    if table_name not in TABLE_CONFIG_MAP:
        return jsonify({
            "status": "error",
            "message": f"表名 '{table_name}' 不存在或未配置",
            "data": []
        }), 400
    
    # 获取表配置
    table_config = TABLE_CONFIG_MAP[table_name]
    db_path = table_config["db_path"]
    table_name_in_db = table_config["table_name"]
    key_field = table_config["key_field"]
    
    # 检查关键字段是否在条件中（处理单字段和复合主键的情况）
    if isinstance(key_field, list):
        # 处理复合主键
        missing_fields = [field for field in key_field if field not in conditions]
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"删除条件中缺少关键字段: {', '.join(missing_fields)}",
                "data": [] 
            }), 400
        
        # 构建查询条件
        where_clause = " AND ".join([f'"{field}" = ?' for field in key_field])
        key_values = [conditions[field] for field in key_field]
    else:
        # 处理单字段主键
        if key_field not in conditions:
            return jsonify({
                "status": "error",
                "message": f"删除条件中缺少关键字段: {key_field}",
                "data": []
            }), 400
        
        where_clause = f'"{key_field}" = ?'
        key_values = (conditions[key_field],)
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查记录是否存在
        check_sql = f'SELECT COUNT(*) FROM "{table_name_in_db}" WHERE {where_clause}'
        cursor.execute(check_sql, key_values)
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            # 构建显示的主键信息
            if isinstance(key_field, list):
                key_info = ", ".join([f"{field} = '{conditions[field]}'" for field in key_field])
            else:
                key_info = f"{key_field} = '{conditions[key_field]}'"
                
            return jsonify({
                "status": "error",
                "message": f"表 '{table_name}' 中未找到 {key_info} 的记录",
                "data": []
            }), 404
        
        # 删除指定记录
        sql = f'DELETE FROM "{table_name_in_db}" WHERE {where_clause}'
        cursor.execute(sql, key_values)
        conn.commit()
        
        # 构建显示的主键信息
        if isinstance(key_field, list):
            key_info = ", ".join([f"{field} = '{conditions[field]}'" for field in key_field])
        else:
            key_info = f"{key_field} = '{conditions[key_field]}'"
        
        print(f"成功删除表 '{table_name}' 中 {key_info} 的记录")
        
        # 数据库更新成功，保存本次变更记录
        table_update_record(table_name, user, "删除", conditions)

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": f"表 '{table_name}' 中 {key_info} 的记录删除成功",
            "data": []
        })
        
    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}",
            "data": []
        }), 500
        
    except Exception as e:
        print(f"删除表数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}",
            "data": []
        }), 500
        
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def table_update_record(table_name, update_user, update_type, update_content):
    """
    记录表更新操作到 table_update_record 表
    
    参数:
    - table_name: 表名
    - update_user: 更新用户
    - update_type: 更新类型 (set 或 del)
    - update_content: 更新内容 (dict类型，将被转换为JSON字符串存储)
    """    
    # 将字典类型的update_content转换为JSON字符串以便存储
    if isinstance(update_content, dict):
        update_content_str = json.dumps(update_content, ensure_ascii=False)
    else:
        update_content_str = str(update_content)
    
    # 连接数据库
    conn = sqlite3.connect("../data/sql_record.db")
    cursor = conn.cursor()
    
    try:
        # 插入记录
        sql = """
        INSERT INTO table_update_record (table_name, update_user, update_type, update_content)
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql, (table_name, update_user, update_type, update_content_str))
        conn.commit()
        print(f"已记录表更新: {table_name}, 类型: {update_type}, 用户: {update_user}")
    except sqlite3.Error as e:
        print(f"记录表更新时出错: {e}")
        conn.rollback()
    finally:
        conn.close()


def feature_set():
    """
    API 接口：在本地 SQLite 数据库中设置（新增或修改）特性信息
    
    如果指定 feature_name 的特性不存在，则新增一行；
    如果已存在，则修改该行信息。
    
    请求参数：
    - feature_id: 特性ID
    - feature_name: 特性名称（主键）
    - feature_function: 特性功能
    - feature_level: 特性级别
    - feature_page: 特性页面链接
    - domain: 领域
    - component: 组件
    
    返回格式：
    {
        "status": "success",
        "message": "特性信息设置成功"
    }
    """
    print("feature_set: 接收到设置特性信息的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # 提取参数
    feature_name = data.get('feature_name')
    if not feature_name:
        return jsonify({
            "status": "error",
            "message": "缺少必需参数: feature_name"
        }), 400

    print(f"收到请求 - 目标特性: {feature_name}")

    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查特性是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM feature 
            WHERE feature_name = ?
        """, (feature_name,))
        
        exists = cursor.fetchone()[0] > 0

        # 构建SQL语句和参数
        if exists:
            # 更新已存在的特性信息
            sql = """
                UPDATE feature SET
                    feature_id = ?,
                    feature_function = ?,
                    feature_level = ?,
                    feature_page = ?,
                    domain = ?,
                    component = ?
                WHERE feature_name = ?
            """
            params = (
                data.get('feature_id', ''),
                data.get('feature_function', ''),
                data.get('feature_level', ''),
                data.get('feature_page', ''),
                data.get('domain', ''),
                data.get('component', ''),
                feature_name
            )
            action = "更新"
        else:
            # 新增特性信息
            sql = """
                INSERT INTO feature (
                    feature_id, feature_name, feature_function, feature_level, 
                    feature_page, domain, component
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('feature_id', ''),
                feature_name,
                data.get('feature_function', ''),
                data.get('feature_level', ''),
                data.get('feature_page', ''),
                data.get('domain', ''),
                data.get('component', '')
            )
            action = "新增"

        # 执行SQL语句
        print(f"正在{action}特性 '{feature_name}' 的信息")
        cursor.execute(sql, params)
        conn.commit()

        print(f"成功{action}特性 '{feature_name}' 的信息")

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": f"特性 '{feature_name}' 信息{action}成功"
        })

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"{action}特性数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")


def API_Component_read():
    """
    API 接口：从本地 SQLite 数据库读取 component 表中的所有组件信息。

    返回格式：
    [
      {
        "组件编号": "xxx",
        "组件名称": "xxx",
        "组件类型": "xxx",
        "组件描述": "xxx",
        "代码目录": "xxx",
        "代码规模": "xxx",
        "代码服务器": "xxx",
        "智能体状态": "xxx",
        "领域": "xxx",
        "团队": "xxx",
        "守护人": "xxx"
      },
      ...
    ]
    """
    print("API_Component_read: 接收到读取 component 表的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # --- 提取参数 ---
    domain = data.get('domain')  # 可选过滤条件：领域
    print(f"收到请求 - 目标表: component, 请求的领域: {domain}")

    # --- 初始化返回数据 ---
    component_data = []

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        cursor = conn.cursor()

        # 构建查询语句：根据 domain 是否存在决定是否过滤
        if domain:
            print(f"正在查询 domain='{domain}' 的组件信息")
            cursor.execute("""
                SELECT * FROM component 
                WHERE 领域 = ? 
                ORDER BY 组件编号
            """, (domain,))
        else:
            print("正在查询所有组件信息（无领域过滤）")
            cursor.execute("SELECT * FROM component ORDER BY 组件编号")

        components = cursor.fetchall()

        if not components:
            print(f"未查询到 {'领域为 ' + domain + ' 的' if domain else ''}任何组件记录。")
            return jsonify({
                "status": "success",
                "message": f"未查询到 {'领域为 ' + domain + ' 的' if domain else ''}组件数据。",
                "componentData": []
            })

        # 遍历每条组件记录，转换为字典格式
        for comp in components:
            component_info = {
                "组件编号": comp['组件编号'] if comp['组件编号'] else "",
                "组件名称": comp['组件名称'] if comp['组件名称'] else "",
                "组件类型": comp['组件类型'] if comp['组件类型'] else "",
                "组件描述": comp['组件描述'] if comp['组件描述'] else "",
                "代码目录": comp['代码目录'] if comp['代码目录'] else "",
                "代码规模": comp['代码规模'] if comp['代码规模'] else "",
                "代码服务器": comp['代码服务器'] if comp['代码服务器'] else "",
                "智能体状态": comp['智能体状态'] if comp['智能体状态'] else "",
                "领域": comp['领域'] if comp['领域'] else "",
                "团队": comp['团队'] if comp['团队'] else "",
                "守护人": comp['守护人'] if comp['守护人'] else ""
            }
            component_data.append(component_info)

        print(f"成功读取并处理 {len(component_data)} 条{'属于 domain=' + domain + ' 的' if domain else ''}组件记录。")

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"读取组件数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

    # --- 返回成功响应 ---
    return jsonify({
        "status": "success",
        "message": f"{'领域为 ' + domain + ' 的' if domain else '所有'}组件数据获取成功，共 {len(component_data)} 条记录。",
        "componentData": component_data
    })


def _parse_icenter_ids(page_url: str):
    """从 iCenter URL 中提取 spaceId 与 contentId。"""
    if not page_url or not isinstance(page_url, str):
        return "", ""
    match = re.search(r"/space/([a-zA-Z0-9]{32})/wiki/page/([a-zA-Z0-9]{32})/view", page_url)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def _safe_icenter_children(page_url: str):
    """获取一层子节点，失败时返回空映射。"""
    try:
        _, _, children_map = Icenter_children_get(page_url)
        if isinstance(children_map, dict):
            return children_map
    except Exception as e:
        logger.warning(f"Icenter children get failed: {str(e)}")
    return {}


def _build_tree_node(title: str, page_url: str, level: int, node_type: str, max_level: int):
    """递归构造树节点。"""
    space_id, content_id = _parse_icenter_ids(page_url)
    
    # 校验节点标题格式
    if not _validate_node_title(title, node_type):
        logger.warning(f"Node title validation failed: title={title}, node_type={node_type}, level={level}")
        # 返回 None 表示该节点无效
        return None
    
    node = {
        "id": content_id or f"{node_type}-{level}-{title}",
        "spaceId": space_id,
        "title": title,
        "level": level,
        "nodeType": node_type,
        "url": page_url,
        "hasChildren": False,
        "children": []
    }

    if level >= max_level:
        return node

    child_map = _safe_icenter_children(page_url)
    
    # 记录获取到的子节点信息
    if child_map:
        logger.info(f"Found {len(child_map)} children for node: title={title}, level={level}, type={node_type}")
        for child_title in list(child_map.keys())[:3]:  # 只显示前 3 个
            logger.info(f"  - Child: {child_title}")
    
    # 如果没有子节点，尝试根据当前节点的标题格式智能推断层级
    # 这可以处理 iCenter 页面结构不规范的情况
    if not child_map:
        # 如果当前节点是 category 类型，但标题符合组件或模块格式
        # 说明 iCenter 结构可能不规范，需要调整
        if node_type == "category" and level == 2:
            # Level 2 的 category 节点，如果标题符合组件格式，应该标记为 component
            if is_valid_comp_tree_page_title_format(title):
                logger.info(f"Detected component at Level 2 (category->component): title={title}")
                node["nodeType"] = "component"
            elif is_valid_module_page_title_format(title):
                logger.info(f"Detected module at Level 2 (category->module): title={title}")
                node["nodeType"] = "module"
        
        logger.info(f"No children found for node: title={title}, level={level}, type={node_type}, url={page_url[:50]}...")
        return node

    next_level = level + 1
    children = []
    valid_children_count = 0
    filtered_children_count = 0
    
    for child_title, child_url in child_map.items():
        # 智能分配子节点类型：优先根据标题格式，其次根据层级
        child_type = _infer_child_type(child_title, next_level)
        
        logger.info(f"Building child: title={child_title}, next_level={next_level}, assigned_type={child_type}")
        
        # 先校验子节点标题格式
        if not _validate_node_title(child_title, child_type):
            logger.warning(f"Child node validation failed: title={child_title}, type={child_type}, level={next_level} - SKIPPED")
            filtered_children_count += 1
            continue
        
        # 递归构建子节点，如果返回 None 则跳过
        child_node = _build_tree_node(child_title, child_url, next_level, child_type, max_level)
        if child_node is not None:
            children.append(child_node)
            valid_children_count += 1
        else:
            logger.warning(f"Child node returned None: title={child_title}, level={next_level}, type={child_type}")
            filtered_children_count += 1
    
    logger.info(f"Node children summary: title={title}, total={len(child_map)}, valid={valid_children_count}, filtered={filtered_children_count}")

    node["children"] = children
    node["hasChildren"] = len(children) > 0
    
    # 日志已经在上面输出，这里不再重复
    
    return node


def API_Knowledge_component_tree():
    """
    组件树接口：优先读取本地数据表中的数据，未命中时实时构建并回填数据表。
    """
    try:
        req = request.get_json(silent=True) or {}
        max_level = int(req.get("maxLevel", 4))
        max_level = 4 if max_level < 1 else min(max_level, 4)
        tree_scope = _normalize_tree_scope(req.get("tab") or req.get("domain") or "L1")
        root_title = req.get("rootTitle") or _get_tree_scope_config(tree_scope)["root_title"]

        # 1) 优先读取数据表数据
        cached_nodes = query_knowledge_component_tree_nodes(scope=tree_scope, max_level=max_level)
        root_node = _build_tree_from_cached_nodes(cached_nodes, root_title)

        # 2) 数据表未命中或数据表过浅(只有一级目录)时，尝试实时构建并回填数据表
        if (not root_node) or (not _has_second_level_children(root_node)):
            root_node = _build_root_node_online(tree_scope, max_level, root_title)
            if _has_second_level_children(root_node):
                node_list = _flatten_tree_nodes(root_node)
                replace_knowledge_component_tree_nodes(
                    scope=tree_scope,
                    node_list=node_list,
                    operator_person=req.get("operator") or "system",
                    sync_batch=req.get("syncBatch") or "",
                )
            elif cached_nodes:
                # 在线构建也失败时，回退旧数据表（避免接口返回空）
                root_node = _build_tree_from_cached_nodes(cached_nodes, root_title)

        return jsonify({"code": 200, "message": "success", "data": {"root": root_node}})
    except Exception as e:
        logger.error(f"API_Knowledge_component_tree error: {str(e)}")
        return jsonify({"code": 500, "message": f"获取组件树失败: {str(e)}", "data": {"root": None}}), 500


def API_Knowledge_component_tree_refresh():
    """
    手动刷新组件树缓存接口：按 scope 重新抓取 iCenter 并回写本地表。
    """
    try:
        req = request.get_json(silent=True) or {}
        max_level = int(req.get("maxLevel", 4))
        max_level = 4 if max_level < 1 else min(max_level, 4)
        tree_scope = _normalize_tree_scope(req.get("tab") or req.get("domain") or "L1")
        root_title = req.get("rootTitle") or _get_tree_scope_config(tree_scope)["root_title"]
        refreshed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        root_node = _build_root_node_online(tree_scope, max_level, root_title)
        if not _has_second_level_children(root_node):
            return jsonify(
                {
                    "code": 500,
                    "message": "同步失败：未获取到二级目录，缓存未覆盖。请检查 iCenter 子页面接口或权限。",
                    "data": {
                        "scope": tree_scope,
                        "nodeCount": _count_total_nodes(root_node),
                        "refreshedAt": refreshed_at,
                    },
                }
            ), 500

        node_list = _flatten_tree_nodes(root_node)
        result = replace_knowledge_component_tree_nodes(
            scope=tree_scope,
            node_list=node_list,
            operator_person=req.get("operator") or "system",
            sync_batch=req.get("syncBatch") or "",
        )

        return jsonify(
            {
                "code": 200,
                "message": "refresh success",
                "data": {
                    "scope": tree_scope,
                    "nodeCount": len(node_list),
                    "refreshedAt": refreshed_at,
                    "result": result,
                },
            }
        )
    except Exception as e:
        logger.error(f"API_Knowledge_component_tree_refresh error: {str(e)}")
        return jsonify({"code": 500, "message": f"刷新组件树失败: {str(e)}", "data": {}}), 500


def API_Knowledge_component_detail():
    """
    组件树右侧详情接口（独立接口）。
    """
    try:
        req = request.get_json(silent=True) or {}
        page_url = req.get("url", "")
        title = req.get("title", "")
        node_type = req.get("nodeType", "")
        space_id = req.get("spaceId", "")
        content_id = req.get("contentId", "")

        if not space_id or not content_id:
            parsed_space_id, parsed_content_id = _parse_icenter_ids(page_url)
            space_id = space_id or parsed_space_id
            content_id = content_id or parsed_content_id

        display_title = title
        if not display_title and page_url:
            try:
                fetched_title = Icenter_title_get(page_url)
                display_title = fetched_title or ""
            except Exception:
                display_title = ""

        guardian = ""
        status = ""
        operator = ""
        operate_time = ""
        related_components = []
        related_features = []
        detail_page_url = page_url
        if not detail_page_url and space_id and content_id:
            detail_page_url = (
                f"https://i.zte.com.cn/index/ispace/#/space/{space_id}/wiki/page/{content_id}/view"
            )

        if detail_page_url:
            try:
                # 使用 get_page_statistics 获取编辑统计信息

                icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
                parts = detail_page_url.split('/')
                spaceId_index = parts.index('wiki') - 1
                spaceId = parts[spaceId_index]
                pageId = parts[-2]
                
                edit_info_list, editor_num, edit_num = icentapi.get_page_statistics(spaceId, pageId)
                
                if edit_info_list and isinstance(edit_info_list, list) and len(edit_info_list) > 0:
                    # 获取最新的编辑信息（通常是列表中的第一个）
                    latest_edit = edit_info_list[0]
                    operator = latest_edit.get("relator") or latest_edit.get("updateBy") or ""
                    operate_time = latest_edit.get("lastUpdateTime") or latest_edit.get("updateDate") or ""
                    
                    # 添加调试日志
                    print(f"get_page_statistics returned: operator={operator}, operate_time={operate_time}")
                    print(f"Edit info list length: {len(edit_info_list)}")
                    print(f"Editor num: {editor_num}, Edit num: {edit_num}")
                else:
                    logger.warning(f"No edit info found in get_page_statistics")
                    
            except Exception as detail_err:
                logger.warning(f"Get page statistics failed: {str(detail_err)}")
                # 如果 get_page_statistics 失败，回退到原来的方法
                try:
                    page_detail = Get_icenter_page_detail(detail_page_url)
                    if isinstance(page_detail, dict):
                        operator = page_detail.get("relator") or page_detail.get("updateBy") or ""
                        operate_time = page_detail.get("lastUpdateTime") or page_detail.get("updateDate") or ""
                        logger.info(f"Fallback: Get_icenter_page_detail returned: operator={operator}, operate_time={operate_time}")
                    else:
                        logger.warning(f"Get_icenter_page_detail returned non-dict: {type(page_detail)}")
                except Exception as fallback_err:
                    logger.warning(f"Fallback method also failed: {str(fallback_err)}")

        def _extract_cell_name_and_url(cell):
            """从单元格提取显示名与链接，优先使用 <a href>。"""
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

        def _dedupe_related_items(items):
            """按名称去重，优先保留有链接的数据。"""
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

        if page_url:
            try:
                page_html = Icenter_content_html_get(page_url)
                if page_html:
                    soup = BeautifulSoup(page_html, "html.parser")
                    table = soup.find("table")
                    if table:
                        for tr in table.find_all("tr"):
                            th = tr.find("th")
                            if not th:
                                continue
                            key = th.get_text(strip=True).replace("\ufeff", "")
                            td = th.find_next_sibling("td")
                            if not td:
                                continue
                            if key == "页面守护人":
                                guardian = td.get_text(strip=True).replace("\ufeff", "")
                            elif key == "页面状态":
                                select_tag = td.find("select")
                                if select_tag:
                                    selected_option = select_tag.find("option", selected=True)
                                    if selected_option:
                                        status = selected_option.get_text(strip=True).replace("\ufeff", "")
                                    else:
                                        status = td.get_text(strip=True).replace("\ufeff", "")
                                else:
                                    status = td.get_text(strip=True).replace("\ufeff", "")
                            if guardian and status:
                                break

                    # 提取“8 依赖组件”章节下表格中的“组件”列
                    section_anchor = None
                    # 兼容：8 依赖组件 / 8.依赖组件 / 八 依赖组件 / 仅“依赖组件”
                    section_pattern = re.compile(r"^\s*(8|八)?[\.\、\s-]*依赖组件")
                    heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
                    candidate_tags = heading_tags + ["p", "strong", "span", "div"]

                    for tag in soup.find_all(candidate_tags):
                        text = tag.get_text(strip=True).replace("\ufeff", "")
                        if section_pattern.search(text):
                            section_anchor = tag
                            break

                    def extract_components_from_table(table):
                        extracted = []
                        rows = table.find_all("tr")
                        if not rows:
                            return extracted
                        header_cells = rows[0].find_all(["th", "td"])
                        component_col_idx = -1
                        for idx, cell in enumerate(header_cells):
                            header_text = cell.get_text(strip=True).replace("\ufeff", "")
                            # 兼容“组件”、“组件名称”
                            if "组件" in header_text:
                                component_col_idx = idx
                                break
                        if component_col_idx < 0:
                            return extracted

                        def is_component_name(value):
                            """
                            仅保留组件标识类名称，例如：
                            - SC001-TAP终端适配执行子组件
                            - C-T001-IMS组件
                            """
                            if not value:
                                return False
                            text = value.strip()
                            # 必须包含 '-'，并且包含数字（避免“守护人/能力等级/NSR”等说明项）
                            if "-" not in text or not re.search(r"\d", text):
                                return False
                            # 组件编码前缀：如 SC001- 或 C-T001-
                            if re.match(r"^[A-Za-z]+(?:-[A-Za-z]+)?\d+-", text):
                                return True
                            return False

                        for row in rows[1:]:
                            cells = row.find_all(["td", "th"])
                            if component_col_idx < len(cells):
                                name, url = _extract_cell_name_and_url(cells[component_col_idx])
                                if is_component_name(name):
                                    extracted.append({"name": name, "url": url})
                        return extracted

                    def is_table_in_hint_block(table):
                        """
                        过滤“提示”内容块中的表格，避免误提取示例数据。
                        """
                        # 1) 就近向前查找标题，如果标题包含“提示”，认为是提示章节
                        prev_heading = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                        # print(prev_heading)
                        if prev_heading:
                            heading_text = prev_heading.get_text(strip=True).replace("\ufeff", "")
                            if "提示" in heading_text:
                                return True

                        # 2) 向前查找近邻文本节点，兼容 iCenter 用 div/p 构造“提示”块
                        prev_text_tag = table.find_previous(["div", "p", "span", "strong"])
                        # print(prev_text_tag)  
                        if prev_text_tag:
                            text = prev_text_tag.get_text(strip=True).replace("\ufeff", "")
                            if "提示" in text:
                                return True

                        # 3) 表格位于 Example Begin 与 Example End 区块之间，也视为示例表格
                        # 判定逻辑（更稳）：
                        # - 表格前（previous）出现 Example Begin
                        # - 表格后（next）仍存在 Example End
                        # 这样可避免只用 previous 索引导致的“表格在 End 之后仍被误判”问题。
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
                        # 在章节范围内找表：从当前章节节点往后，直到遇到下一个标题节点
                        for sibling in section_anchor.find_all_next():
                            if sibling == section_anchor:
                                continue
                            if sibling.name in heading_tags and sibling.get_text(strip=True):
                                # 遇到下一章节标题，停止
                                break
                            if sibling.name == "table":
                                if is_table_in_hint_block(sibling):
                                    continue
                                related_components.extend(extract_components_from_table(sibling))

                    # 兜底：若章节定位失败或章节内无有效表，则全页扫描“组件列”表格
                    if not related_components:
                        for table in soup.find_all("table"):
                            if is_table_in_hint_block(table):
                                continue
                            related_components.extend(extract_components_from_table(table))

                    # 提取“7 关联特性”章节下表格中的“特性”列
                    feature_section_anchor = None
                    feature_section_pattern = re.compile(r"^\s*(7|七)?[\.\、\s-]*关联特性")
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
                            # 模糊识别“特性”列，如“特性/关联特性/特性名称”
                            if "特性" in header_text:
                                feature_col_idx = idx
                                break
                        if feature_col_idx < 0:
                            return extracted

                        for row in rows[1:]:
                            cells = row.find_all(["td", "th"])
                            if feature_col_idx < len(cells):
                                name, url = _extract_cell_name_and_url(cells[feature_col_idx])
                                if name:
                                    extracted.append({"name": name, "url": url})
                        return extracted

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

                    # 兜底：若章节定位失败或章节内无有效表，则全页扫描“特性列”表格
                    if not related_features:
                        for table in soup.find_all("table"):
                            if is_table_in_hint_block(table):
                                continue
                            related_features.extend(extract_features_from_table(table))
            except Exception as parse_err:
                logger.warning(f"Parse icenter detail failed: {str(parse_err)}")

        if related_components:
            example_components = {"C001-LCMOTN组件", "C002-URM组件"}
            related_components = _dedupe_related_items(related_components)
            related_components = [
                item for item in related_components if item.get("name") not in example_components
            ]

        if related_features:
            related_features = _dedupe_related_items(related_features)

        detail = {
            "basicInfo": {
                "name": display_title or "未命名节点",
                "spaceId": space_id,
                "contentId": content_id,
                "nodeType": node_type or "unknown",
            },
            "guardian": guardian,
            "status": status,
            "changeLog": "",
            "operator": operator,
            "operateTime": operate_time,
            "relations": "",
            "relatedComponents": related_components,
            "relatedFeatures": related_features,
            # 兼容旧前端：保留纯文本列表
            "relatedComponentNames": [item.get("name", "") for item in related_components],
            "relatedFeatureNames": [item.get("name", "") for item in related_features],
            "qualityScore": "",
            "contentCompleteness": "",
            "contentStandardization": "",
        }

        return jsonify({"code": 200, "message": "success", "data": detail})
    except Exception as e:
        logger.error(f"API_Knowledge_component_detail error: {str(e)}")
        return jsonify({"code": 500, "message": f"获取详情失败: {str(e)}", "data": {}}), 500

def API_Prompt_read():
    """
    API 接口：从本地 SQLite 数据库读取 prompt 表中的数据。
    支持根据创建人和场景进行筛选。
    
    请求参数：
    - creator (可选): 创建人
    - scene (可选): 场景
    
    返回格式：
    {
        "status": "success",
        "message": "数据获取成功",
        "tableData": [
            {
                "主题": "...",
                "摘要": "...",
                "内容": "...",
                "场景": "...",
                "创建人": "..."
            },
            ...
        ]
    }
    """
    print("API_Prompt_read: 接收到读取 prompt 表的请求")

    # 获取前端发送的JSON数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体为空或非JSON格式"
        }), 400

    # --- 提取参数 ---
    creator = data.get('创建人')
    scene = data.get('场景')
    
    print(f"收到请求 - 创建人: {creator}, 场景: {scene}")

    # --- 初始化返回数据 ---
    table_data = []

    # --- 构建 SQL 查询 ---
    # 基础SQL查询语句
    base_sql = """
    SELECT 
        主题,
        摘要,
        内容,
        场景,
        创建人
    FROM prompt
    """
    
    # 根据参数构建WHERE条件
    conditions = []
    params = []
    
    if creator is not None and creator != "":
        conditions.append("创建人 = ?")
        params.append(creator)
        
    if scene is not None and scene != "":
        conditions.append("场景 = ?")
        params.append(scene)
    
    # 组合完整的SQL语句
    if conditions:
        final_sql = base_sql + " WHERE " + " AND ".join(conditions)
    else:
        final_sql = base_sql
    
    final_sql += " ORDER BY rowid"
    
    print(f"查询SQL: {final_sql}")
    print(f"查询参数: {params}")

    # --- 数据库操作 ---
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect("../data/chat.db")
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        cursor = conn.cursor()

        # 执行查询
        cursor.execute(final_sql, params)
        rows = cursor.fetchall()

        # 处理查询结果
        for row in rows:
            # 将每行数据转换为字典格式
            table_data.append({
                "主题": row['主题'] if row['主题'] else "",
                "摘要": row['摘要'] if row['摘要'] else "",
                "内容": row['内容'] if row['内容'] else "",
                "场景": row['场景'] if row['场景'] else "",
                "创建人": row['创建人'] if row['创建人'] else ""
            })

        print(f"成功读取 {len(table_data)} 条记录。")

    except sqlite3.Error as e:
        print(f"数据库操作出错: {e}")
        return jsonify({
            "status": "error",
            "message": f"数据库错误: {str(e)}"
        }), 500

    except Exception as e:
        print(f"读取数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

    # --- 返回成功响应 ---
    return jsonify({
        "status": "success",
        "message": f"prompt数据获取成功，共 {len(table_data)} 条记录。",
        "tableData": table_data
    })

def api_username_get():
    """
    内部函数：从数据库 ../data/sql_config.db 的 user 表中获取 userid 和 username 的对应关系
    返回一个 map，其中 userid 对应数据库中的工号，username 对应数据库中的姓名
    
    返回格式：
    {
        "userid1": "username1",
        "userid2": "username2",
        ...
    }
    """    
    # 连接数据库
    conn = sqlite3.connect("../data/sql_config.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询 user 表中的所有用户数据
    cursor.execute("SELECT 工号, 姓名 FROM user")
    rows = cursor.fetchall()
    
    # 构建 userid 到 username 的映射字典
    user_map = {}
    for row in rows:
        userid = row['工号']
        username = row['姓名']
        # 只有当 userid 和 username 都存在时才添加到映射中
        if userid and username:
            user_map[userid] = username
    
    # 关闭数据库连接
    conn.close()
    
    # 返回用户映射字典
    return user_map 

def test_Icenter_table_get():
    url = "https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/14a5cfb079b54b389a58460ce2b5c87c/view"
    table_json = Icenter_table_get(url)
    print(table_json)


def test_Icenter_table_set():
    url = "https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/879f885cd07a4761af72589f8f003d8b/view"
    table_json = Icenter_table_get(url)
    
    data = json.loads(table_json)
    data[1]["编号"] = "2"  # 保持字符串类型

    updated_json = json.dumps(data, ensure_ascii=False)

    result = Icenter_table_set(url, updated_json)
    print(result)


def test_Rdc_list_read():
    result = Rdc_list_read()
    print(len(result))

def test_review_update():
    result = review_update()
    print(len(result))

def get_rdc_component():
    try:
        # 获取前端发送的JSON数据
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求体为空或非JSON格式"
            }), 400

        # 提取参数
        rdc_id = data.get('rdc_id')
        if not rdc_id:
            return jsonify({
                "status": "error",
                "message": "缺少必需参数: feature_name"
            }), 400

        query_condition = [
            {
                "field": "System_WorkItemType",
                "leftGroup": 0,
                "logicalOperator": "",
                "operator": "=",
                "rightGroup": 0,
                "value": "Task:OTNAG:任务"
            },
            {
                "field": "System_Id",
                "leftGroup": 0,
                "logicalOperator": "AND",
                "operator": "=",
                "rightGroup": 0,
                "value": rdc_id
            }
        ]

        query_items = [
            {
                "key": "System_Description_html",
                "name": "描述",
                "type": "html",
                "width": ""
            }
        ]

        review_map = {
            "描述": "描述",
        }

        # 获取review数据
        review_list = Rdc_list_get(query_condition, query_items, review_map, 1, {})
        description = review_list[0]['描述']
        print(description, 111)
        return jsonify({
            "status": "success",
            "tableData": description
        }), 200
    except Exception as e:
        print(f"读取数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

def write_rdc_component():
    try:
        # 获取前端发送的JSON数据
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求体为空或非JSON格式"
            }), 400

        # 提取参数
        rdc_id = data.get('rdc_id')
        content = data.get("content")
        content = content.replace("\n", "<br>")
        query_condition = [
            {
                "field": "System_WorkItemType",
                "leftGroup": 0,
                "logicalOperator": "",
                "operator": "=",
                "rightGroup": 0,
                "value": "Task:OTNAG:任务"
            },
            {
                "field": "System_Id",
                "leftGroup": 0,
                "logicalOperator": "AND",
                "operator": "=",
                "rightGroup": 0,
                "value": rdc_id
            }
        ]

        query_items = [
            {
                "key": "System_Description_html",
                "name": "描述",
                "type": "html",
                "width": ""
            },
            {
                "key": "System_Tag",
                "name": "标签",
                "type": "advancedData",
                "width": ""
            }

        ]

        review_map = {
            "描述": "描述",
            "标签": "标签"
        }

        # 获取review数据
        review_list = Rdc_list_get(query_condition, query_items, review_map, 1, {})
        description = review_list[0]['描述']
        tag_list = review_list[0]['标签']

        soup = BeautifulSoup(description, 'lxml')
        tables = soup.find_all('table')
        if len(tables) > 0:
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i in range(len(cells)):
                        cell = cells[i]
                        cell_text = cell.get_text(strip=True)
                        if cell_text == 'AI输出':
                            if i + 1 < len(cells):
                                right_cell = cells[i + 1]
                                right_cell.clear()  # 清空单元格原有内容
                                new_content_soup = BeautifulSoup(content, 'lxml')
                                right_cell.append(new_content_soup)
                            break
            htmltext = str(soup)
            htmltext = htmltext.replace('<html><body>', '').replace('</body></html>', '')
        else:
            target = '<strong>AI输出:</strong>'
            if target in description:
                index = description.find(target)
                htmltext = description[0:index] + f'{target}<p>{content}</p>'
            else:
                htmltext = description + f'{target}<p>{content}</p>'
        change_description_and_tags(htmltext, rdc_id, tag_list)
        return jsonify({
            "status": "success",
            "message": "修改成功"
        }), 200
    except Exception as e:
        print(f"读取数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500


def refresh_task():
    try:
        tasks_update()
        return jsonify({
            "status": "success"
        }), 200
    except Exception as e:
        print(f"读取数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500

def test_TOOL_Table_get():
    """测试 TOOL_Table_get 函数功能"""
    print("开始测试 TOOL_Table_get 函数...")
    
    # 测试1: 查询单板库表的所有数据
    print("\n--- 测试1: 查询单板库表的所有数据 ---")
    result = TOOL_Table_get("单板库", {})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    print(f"数据条数: {len(result['data'])}")
    if result['data']:
        print(f"第一条数据: {result['data'][0]}")
    
    # 测试2: 按条件查询单板库表
    print("\n--- 测试2: 按条件查询单板库表 ---")
    result = TOOL_Table_get("单板库", {"domain": "L2"})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    print(f"数据条数: {len(result['data'])}")
    if result['data']:
        print(f"第一条数据: {result['data'][0]}")
    
    # 测试3: 查询光模块库表
    print("\n--- 测试3: 查询光模块库表的所有数据 ---")
    result = TOOL_Table_get("光模块库", {})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    print(f"数据条数: {len(result['data'])}")
    if result['data']:
        print(f"第一条数据: {result['data'][0]}")
    
    # 测试4: 按条件查询光模块库表
    print("\n--- 测试4: 按条件查询光模块库表 ---")
    result = TOOL_Table_get("光模块库", {"制造厂商": "TACLINK"})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    print(f"数据条数: {len(result['data'])}")
    if result['data']:
        print(f"第一条数据: {result['data'][0]}")
    
    # 测试5: 查询不存在的表
    print("\n--- 测试5: 查询不存在的表 ---")
    result = TOOL_Table_get("不存在的表", {})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    
    # 测试6: 查询SD器件库表
    print("\n--- 测试6: 查询SD器件库表 ---")
    result = TOOL_Table_get("SD器件库", {})
    print(f"查询结果状态: {result['status']}")
    print(f"查询结果消息: {result['message']}")
    print(f"数据条数: {len(result['data'])}")
    if result['data']:
        print(f"第一条数据: {result['data'][0]}")
    
    print("\n--- TOOL_Table_get 函数测试完成 ---")

if __name__ == "__main__":
    # test_Icenter_table_get()
    # test_Icenter_table_set()
    # test_Rdc_list_read()
    # test_review_update()
    # print(api_username_get())
    test_TOOL_Table_get()  # 取消注释以运行测试
    # record_table_update("api", "10171727", "set", "这是一条测试记录。")
