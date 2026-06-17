import os
import requests
from datetime import datetime
from fastmcp import FastMCP
from agent_utils import Clear_proxy
from get_icenter import Get_icenter_content_markdown
from api_data import TOOL_Table_get

Clear_proxy()

mcp = FastMCP(name="icenter_tools")

@mcp.tool("获取icenter页面内容")
async def icenter_read(url: str) -> str:
    """从iCenter平台读取指定页面的Markdown格式内容

    该工具用于从iCenter知识库平台获取指定页面的内容，并将其转换为Markdown格式返回。
    支持获取页面的标题、内容、人员信息、目录结构等完整信息，并自动转换为Markdown格式。

    参数:
    url: iCenter页面的完整URL链接，例如:
        https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view

    返回:
    str: 页面内容的Markdown格式字符串，包含页面标题和转换后的内容
    
    示例:
    >>> content = await icenter_read("https://i.zte.com.cn/index/ispace/#/space/xxx/wiki/page/xxx/view")
    >>> print(content)  # 返回页面的Markdown格式内容
    """
    return Get_icenter_content_markdown(url)


@mcp.tool("查询数据库表内容")
async def sql_table_get(table_name: str, conditions: dict) -> dict:
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

    调用示例：
    示例1：查询单板库表的所有数据
    入参：
    {
        "table_name": "单板库",
        "conditions": {}
    }

    示例2：按条件查询光模块库表
    入参：
    {
        "table_name": "光模块库",
        "conditions": {
            "模块类型": "QSFP28",
            "速率Mbps": 25000
        }
    }

    目前已经支持的数据库：
    "SD器件库": {
        "key_field": "SD类型",
        "fields": [
            "SD类型", "厂家", "容量", "材质", "接口类型", 
            "代码", "支持主控", "总写入次数", "单block大小", "理论TBW", 
            "每日写入上限"
        ]
    },
    "光模块库": {
        "key_field": "PN",
        "fields": [
            "PN", "模块类型", "接口类型", "速率Mbps", "距离", 
            "制造厂商", "应用代码", "波长类型", "物料代码", "支持单板"
        ]
    },
    "单板库": {
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
        "key_field": "代码库",
        "fields": [
            "代码库", "分支", "变更次数", "新增行", "删除行", 
            "领域", "关联故障", "关联组件"
        ]
    },
    "命令库": {
        "key_field": ["命令类型", "命令码"],  # 复合主键
        "fields": [
            "命令类型", "命令码", "命令名称", "命令来源", "关联特性", 
            "关联命令", "关联组件", "数据存储", "处理流程", "白盒梳理"
        ]
    },
    "故障库": {
        "key_field": "标识",
        "fields": [
            "标识", "标题", "描述", "状态",
            "变更大类", "缺陷等级", "缺陷来源", "发现活动", "发现方法", "发现版本", "创建时间", "关闭时间",
            "所属产品", "所属项目", "领域", "团队",
            "引入人", "引入人部门", "发现人", "发现人部门", "进展", "备注", "计划解决日期", "自测报告链接"
        ]
    },
    "交换芯片库": {
        "key_field": "型号",
        "fields": [
            "型号", "厂家", "交换容量", "端口配置", "端口容量", 
            "路由表容量", "支持主控", "支持单板"
        ]
    },
    "PHY库": {
        "key_field": "PHY型号",
        "fields": [
            "PHY型号", "厂家", "端口配置", "端口类型", "封装类型", 
            "速率支持", "典型特性", "支持单板"
        ]
    },
    "分支库": {
        "key_field": "分支名称",  # 主键
        "fields": [
            "分支名称", "分支状态", "分支活跃度", "合入策略", "拉取时间", 
            "关联项目", "关联版本", "关联单板", "待合入需求", "待合入故障", 
            "代码链接"
        ]
    },
    "任务库": {
        "key_field": "标识",
        "fields": [
            "标识", "标题", "描述", "状态", "指派给", "领域", "团队", "迭代"
        ]
    },
    "版本库": {
        "key_field": ["版本"],
        "fields": [
            "版本", "目标", "分支", "主控", 
            "需求情况", "故障情况", "版本风险情况", "团队风险情况",
            "版本号", "关联故障"
        ]
    },
    "时钟芯片库": {
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
    }
    """

    # 调用实际的工具函数来获取数据
    response = TOOL_Table_get(table_name, conditions)
    
    # 返回查询结果
    return response 



if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)