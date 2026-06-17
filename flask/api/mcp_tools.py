import os
import requests
from datetime import datetime
from fastmcp import FastMCP
from agent_utils import Clear_proxy
from get_icenter import Get_icenter_markdown, Set_icenter_markdown, Icenter_children_get, Icenter_page_create, Icenter_block_get, Icenter_block_set
from get_rdc import Get_rdc_markdown, PR_ai_development, PR_ai_change
from api_data import TOOL_Testcase_table_get, TOOL_Testcase_table_set

Clear_proxy()

mcp = FastMCP(name="mcp_tools_local")

@mcp.tool()
async def icenter_read(url: str) -> str:
    """从iCenter平台读取指定页面的Markdown格式内容

    该工具用于从iCenter平台获取指定页面的内容，并将其转换为Markdown格式返回。

    参数:
    url: iCenter页面的完整URL链接，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view

    返回:
    str: 页面内容的Markdown格式字符串，包含页面标题和转换后的内容
    
    示例:
    >>> content = await icenter_read("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view")
    >>> print(content)  # 返回页面的Markdown格式内容
    """
    return Get_icenter_markdown(url)

@mcp.tool()
async def icenter_write(url: str, content: str) -> bool:
    """向iCenter平台写入指定页面的内容
    
    该工具用于向iCenter平台指定页面写入内容，接收Markdown格式的内容并更新到页面。

    参数:
    url: iCenter页面的完整URL链接，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
    content: 要写入的页面内容，必须为Markdown格式，例如:
        "# 标题\n\n这是内容"
    
    返回:
    bool: 写入操作是否成功的布尔值
    
    示例:
    >>> success = await icenter_write("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view", "# 新标题\\n\\n这是新内容")
    >>> print(success)  # 返回True表示写入成功，False表示失败
    """
    return Set_icenter_markdown(url, content)

@mcp.tool()
async def icenter_children_get(url: str) -> dict:
    """获取指定iCenter页面的多级子页面（树形结构）
    
    该工具用于获取指定iCenter页面的所有子页面信息，以树形结构返回。
    键为Markdown链接格式 `[标题](URL)`，值为空字典 `{}`（叶子节点）或嵌套的子页面字典。

    参数:
    url: 父页面的完整URL，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view

    返回:
    dict: 树形结构，键为Markdown链接格式，值为空字典或嵌套字典，例如:
        {
            "[L0领域](https://...)": {
                "[001-特性不变+新增组网场景+新增硬件（新增单板）](https://...)": {},
                "[003-存量单板+功能补齐](https://...)": {
                    "[【SKILLS】光板配置文件生成技能](https://...)": {}
                }
            }
        }
    
    示例:
    >>> children = await icenter_children_get("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view")
    >>> print(children)
    """
    return Icenter_children_get(url)

@mcp.tool()
async def icenter_create(parent_url: str, title: str, content: str = "") -> str:
    """在iCenter平台创建新页面
    
    该工具用于在iCenter平台指定父页面下创建新页面。

    参数:
    parent_url: 父页面的完整URL，新页面将创建在该页面下，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
    title: 新页面的标题
    content: 新页面的内容，必须为Markdown格式，例如:
        "# 标题\n\n这是内容"

    返回:
    str: 成功时返回Markdown格式的链接 [title](url)，失败时返回空字符串
    
    示例:
    >>> new_url = await icenter_create("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view", "新页面标题", "页面内容")
    >>> print(new_url)  # 返回 [新页面标题](https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/yyy/view)
    """
    return Icenter_page_create(parent_url, title, content)

@mcp.tool()
async def icenter_block_read(url: str, block_id: str = "", block_title: str = "", block_tag: str = "") -> str:
    """从iCenter平台读取指定页面中某个区块的内容
    
    该工具用于从iCenter平台获取指定页面中特定区块的内容，并将其转换为Markdown格式返回。
    
    参数:
    url: iCenter页面的完整URL链接，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
    block_id: 区块ID，可选参数，用于定位特定区块
    block_title: 区块标题，可选参数，用于定位特定区块
    block_tag: 区块标签，可选参数，用于定位特定区块
    
    返回:
    str: 区块内容的Markdown格式字符串
    
    注意:
    - 至少需要提供 block_id、block_title 或 block_tag 中的一个参数来定位区块
    
    示例:
    >>> content = await icenter_block_read("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view", block_title="需求描述")
    >>> print(content)  # 返回指定区块的Markdown格式内容
    """
    return Icenter_block_get(url, block_id, block_title, block_tag)


@mcp.tool()
async def icenter_block_write(url: str, block_content: str, block_id: str = "", block_title: str = "", block_tag: str = "") -> bool:
    """向iCenter平台写入指定页面中某个区块的内容
    
    该工具用于向iCenter平台指定页面的特定区块写入内容，接收Markdown格式的内容并更新到区块。
    
    参数:
    url: iCenter页面的完整URL链接，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view
    block_content: 要写入的区块内容，必须为Markdown格式，例如:
        "# 标题\n\n这是内容"
    block_id: 区块ID，可选参数，用于定位特定区块
    block_title: 区块标题，可选参数，用于定位特定区块
    block_tag: 区块标签，可选参数，用于定位特定区块
    
    返回:
    bool: 写入操作是否成功的布尔值
    
    注意:
    - 至少需要提供 block_id、block_title 或 block_tag 中的一个参数来定位区块
    
    示例:
    >>> success = await icenter_block_write("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view",
                                           "# 新标题\\n\\n这是新内容", block_title="需求描述")
    >>> print(success)  # 返回True表示写入成功，False表示失败
    """
    return Icenter_block_set(url, block_id, block_title, block_tag, block_content)


@mcp.tool()
async def rdc_read(id: str) -> str:
    """从RDC平台读取指定页面的Markdown格式内容

    该工具用于从RDC平台获取指定页面的内容，并将其转换为Markdown格式返回。

    参数:
    id: RDC页面的ID，例如:OTNSW-697474，OTNAG-691234

    返回:
    str: 页面内容的Markdown格式字符串，包含页面标题和转换后的内容
    
    示例:
    >>> content = await rdc_read("some_rdc_page_id")
    >>> print(content)  # 返回页面的Markdown格式内容
    """
    return Get_rdc_markdown(id)

@mcp.tool()
async def rdc_pr_development_ai_assistance(item_id: str, ai_content: str) -> dict:
    """AI辅助需求开发，更新RDC工作项的【AI辅助记录】字段，用于记录需求开发阶段的AI辅助过程
    
    该工具用于回填RDC工作项中的【AI辅助记录】字段，当AI完成需求开发时，将开发过程总结并回填这个字段，并默认添加"AI辅助需求开发自动回填"标签。
    
    参数:
    item_id: RDC工作项ID，例如: OTNSW-697474, OTNAG-691234
    ai_content: 要写入会签说明字段的AI辅助记录，必须使用markdown格式
    
    返回:
    dict: 包含更新结果的字典
    
    示例:
    >>> result = await rdc_update_countersign_report("OTNAG-1234567", "AI分析结果：这是一个故障复盘的建议...")
    >>> print(result)  # 返回更新操作的结果
    """
    result = PR_ai_development(item_id, ai_content)
    return {"status": "success", "item_id": item_id, "result": result}


@mcp.tool()
async def rdc_pr_change_ai_assistance(item_id: str, change_impact_analysis: str) -> dict:
    """AI辅助需求变更，更新RDC工作项的【变更影响分析】字段，用于记录需求变更阶段的AI辅助过程
    
    该工具用于回填RDC工作项中的【变更影响分析】字段，当AI完成需求变更分析时，将变更影响分析内容回填到对应字段，并默认添加"AI辅助需求变更自动回填"标签。
    
    参数:
    item_id: RDC工作项ID，例如: OTNSW-697474, OTNAG-691234
    change_impact_analysis: 变更影响分析内容，必须使用markdown格式
    
    返回:
    dict: 包含更新结果的字典
    
    示例:
    >>> result = await rdc_ai_impact("OTNAG-1234567", "变更影响分析是...")
    >>> print(result)  # 返回更新操作的结果
    """
    result = PR_ai_change(item_id, change_impact_analysis)
    return {"status": "success", "item_id": item_id, "result": result}


@mcp.tool()
async def ft_testcase_get(search_params: str | dict) -> list:
    """从FT用例库获取数据，支持模糊搜索和指定字段搜索
    
    该工具用于从FT用例库查询测试用例数据。
    
    参数:
        search_params: 搜索条件，支持两种格式:
            - 字符串: 如 "LAG 删除" 表示多词空格分隔，在所有字段中模糊匹配(AND关系)
            - 字典: 如 {"用例编号": "20260414", "用例名称": "lag"} 在所有字段中模糊匹配
    
    返回:
        list: JSON格式的用例数据列表，每个元素是字典
    
    示例:
        >>> result = await ft_testcase_get("LAG")
        >>> result = await ft_testcase_get("LAG 删除")
        >>> result = await ft_testcase_get({"用例编号": "20260414", "用例名称": "lag"})
    """
    return TOOL_Testcase_table_get(search_params)


@mcp.tool()
async def ft_testcase_set(case_data: dict | list) -> dict | list:
    """设置FT用例库数据(新增或更新)，支持批量处理
    
    该工具用于在FT用例库中新增或更新测试用例，支持单条或批量操作。
    
    参数:
        case_data: 用例数据，支持单条或批量:
            - 单条(dict): {"用例名称": "LAG测试", "领域": "L2"}
            - 批量(list): [{"用例名称": "测试1"}, {"用例名称": "测试2", "领域": "L2"}]
            - 不传入用例编号: 自动生成14位编号(YYYYMMDD + 6位自增)
            - 传入用例编号: 更新已存在的用例(用例编号必须已存在，否则返回"用例不存在")
    
    返回:
        - 单条: dict 如 {"status": "success", "message": "新增成功", "用例编号": "20260414000001"}
        - 批量: list 如 [{"status": "success", "用例编号": "..."}, ...]
    
    示例:
        >>> # 单条新增
        >>> result = await ft_testcase_set({"用例名称": "LAG删除测试", "领域": "L2", "特性": "LAG"})
        >>> # 单条更新
        >>> result = await ft_testcase_set({"用例编号": "20260414000001", "用例名称": "更新"})
        >>> # 批量新增
        >>> result = await ft_testcase_set([{"用例名称": "测试1"}, {"用例名称": "测试2", "领域": "L2"}])
        >>> # 批量更新
        >>> result = await ft_testcase_set([{"用例编号": "20260414000001", "用例名称": "更新1"}, {"用例编号": "20260414000002", "用例名称": "更新2"}])
    """
    return TOOL_Testcase_table_set(case_data)


if __name__ == "__main__":
    # 直接运行方式
    mcp.run(transport="streamable-http", host="10.90.251.221", port=33072)


# gunicorn 入口点
app = mcp.streamable_http_app()