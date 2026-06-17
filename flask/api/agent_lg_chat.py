import os
import re
import time
import json
import logging
from datetime import datetime
from typing import Generator, Dict, Any, List, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from agent_base import MessageDict, ConfigDict

from api_data import TOOL_Table_get
from api_utils import Replace_question
from get_icenter import Get_icenter_content_markdown, Icenter_content_html_get, Icenter_content_html_set, Get_icenter_markdown
from get_rdc import Get_rdc_markdown, Rdc_field_set, Rdc_field_get
from agent_utils import Get_model_config, Clear_proxy

# 抑制 httpx 的日志输出
logging.getLogger("httpx").setLevel(logging.WARNING)

@tool("查询当前时间")
def current_datetime_get() -> str:
    """
    获取当前系统日期和时间的工具
    
    Returns:
        str: 当前日期和时间的字符串，格式为 'YYYY-MM-DD HH:MM:SS'
    """
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


@tool("计算整数平方")
def calculate_square(number: int) -> int:
    """
    计算一个数的平方的工具
    
    Args:
        number: 需要计算平方的数值
        
    Returns:
        float: 该数的平方值
    """
    return number ** 2

@tool("查询编码规范")
def code_standards_get() -> str:
    """
    获取编码规范红线
            
    Returns:
        str: 编码规范红线的具体内容
    """
    
    return Get_icenter_content_markdown("https://i.zte.com.cn/index/ispace/#/space/c72da2d6076d4eb9838129067ae770a9/wiki/page/8e31c4382c094f729e4ff1fa3d694713/view")

@tool("获取不安全函数治理方法")
def unsafe_function_get() -> str:
    """
    获取不安全函数治理方法
            
    Returns:
        str: 不安全函数治理方法的具体内容
    """
    
    return Get_icenter_content_markdown("https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/18f342a80d5f444d8d4477b6e06612d0/view")

@tool("查询数据库表")
def sql_table_get(table_name: str, conditions: dict) -> dict:
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

@tool("查询RDC工作项")
def get_rdc_content(item_id: str) -> str:
    """
    RDC工作项ID包含这些类型：OTNAG-123456，OTNAG-1234567, OTNSW-123456，通过此工具可以获取工作项的具体内容。
    入参：
    - 工作项id

    返回值：
    - 工作项具体内容
    """

    content = Rdc_field_get(item_id)
    return content

@tool("更新RDC工作项")
def set_rdc_content(item_id: str, item_dict: dict) -> str:
    """
    RDC工作项ID包含这些类型：OTNAG-123456，OTNAG-1234567, OTNSW-123456，通过此工具可以更新工作项的具体内容。
    入参：
    - item_id: 工作项ID，格式如 "OTNAG-123456"
    - item_dict: 包含需要更新的字段及对应值的字典，格式为 {field_name: field_value}
                 其中field_name可以是中文字段名，如：
                 - 任务类工作项: "标题", "描述", "指派给" 等
                 - 变更请求: "期望解决日期" 等
                 - 市场需求: "备注", "变更原因", "变更影响分析" 等
                 field_value为对应的字段值，可以是文本、HTML内容等
                 示例：
                 - 单个键值对: {"标题": "新标题"}
                 - 多个键值对: {"标题": "新标题", "描述": "新描述", "指派给": "张三"}

    返回值：
    - 更新操作的结果信息，通常是API响应的code字段，如果操作失败则返回"更新操作完成"
    """

    print(f"set_rdc_content:item_dict{item_dict}")
    result = Rdc_field_set(item_id, item_dict)
    print(f"set_rdc_content:result{result}")

    # 确保返回字符串类型
    return str(result) if result is not None else "更新操作完成"


@tool("查询icenter页面内容")
def get_icenter_content(url: str) -> str:
    """
    查询iCenter平台指定页面的HTML内容
    
    参数：
    - url: iCenter页面的完整URL，例如：
           'https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/98e51ae6a8df11f0871e754a0abbc624/view'
    
    返回值：
    - 页面的HTML内容，如果查询失败则返回空字符串
    """
    content = Icenter_content_html_get(url)
    return content if content is not None else ""


@tool("更新icenter页面内容")
def set_icenter_content(url: str, content: str) -> str:
    """
    更新iCenter平台指定页面的HTML内容
    
    参数：
    - url: iCenter页面的完整URL，例如：
           'https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view'
    - content: 要更新到页面的HTML内容，例如：
               '<h1>标题</h1><ul><li>列表项1</li><li>列表项2</li></ul>'
    
    返回值：
    - 更新操作的结果信息，成功返回"True"，失败返回"False"
    
    调用示例：
    示例1：更新简单文本内容
    result = set_icenter_content(
        "https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/18f342a80d5f44d8d4477b6e06612d0/view",
        "<h1>项目进度报告</h1><h2>本周进展</h2><ul><li>完成需求分析</li><li>完成方案设计</li></ul><h2>下周计划</h2><ul><li>开始编码实现</li></ul>"
    )
    
    示例2：更新包含表格的内容
    result = set_icenter_content(
        "https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/18f342a80d5f444d8d4477b6e06612d0/view",
        "<h1>测试报告</h1><table><tr><th>测试项</th><th>状态</th><th>备注</th></tr><tr><td>功能测试</td><td>通过</td><td>无异常</td></tr><tr><td>性能测试</td><td>待测</td><td>排期中</td></tr></table>"
    )
    """
    print(f"set_icenter_content:content{content}")
    result = Icenter_content_html_set(url, content)
    print(f"set_icenter_content:result{result}")
    return str(result)


def create_context_folder(config: ConfigDict) -> None:
    """
    根据配置信息创建上下文文件夹和context.md文件
    
    Args:
        config: 配置字典，包含 session_id 和 user 信息
    """
    # 从config中提取session_id和user信息
    session_id = config.get("session_id", "unknown")
    user = config.get("user", "unknown")
    
    # 获取系统当前时间
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # 构建文件夹名称
    folder_name = f"{current_time}_{session_id}_{user}"
    
    # 在../assets/目录下创建文件夹
    assets_path = os.path.join("..", "assets", "context")
    folder_path = os.path.join(assets_path, folder_name)
    
    # 确保assets目录存在
    os.makedirs(assets_path, exist_ok=True)
    
    # 创建文件夹
    os.makedirs(folder_path, exist_ok=True)
    
    # 在新建的文件夹中创建context.md文件
    context_file_path = os.path.join(folder_path, "context.md")
    with open(context_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# 对话上下文信息\n\n")
        f.write(f"- Session ID: {session_id}\n")
        f.write(f"- User: {user}\n")
        f.write(f"- 创建时间: {current_time}\n")
        f.write(f"- 对话状态: 初始状态（无消息）\n")


def Agent_langgraph_superchat(messages: List[MessageDict] = [], config: ConfigDict = {}) -> Generator[str, None, None]:
    """
    最简版 LangGraph AI 聊天函数（流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature
    
    Yields:
        逐字符返回 AI 回答
    """
        
    if not messages:
        # 调用函数创建上下文文件夹
        create_context_folder(config)
        
        yield ""
        return
    
    Clear_proxy()
    
    # 获取模型配置
    model_name, api_key, base_url = Get_model_config(config.get("model", "qwen3-zte"))

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key, # pyright: ignore[reportArgumentType]
        base_url=base_url,
        timeout=600,
        streaming=True,  # 支持流式输出
    )

    tools = [
        current_datetime_get, 
        calculate_square, 
        code_standards_get,
        unsafe_function_get,
        sql_table_get,
        get_rdc_content,
        set_rdc_content,
        get_icenter_content,
        set_icenter_content
    ]

    # 转换消息为 LangChain 格式
    langchain_messages = []
    for message in messages:
        content = message["content"]
        if message["role"] == "system":
            langchain_messages.append(SystemMessage(content=content))
        elif message["role"] == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif message["role"] == "assistant":
            langchain_messages.append(AIMessage(content=content))

    # 创建 LangGraph agent
    try:
        agent = create_react_agent(llm, tools)
                
        for chunk in agent.stream({"messages": langchain_messages}):
            # 检查是否为工具调用
            for key, value in chunk.items():
                if 'messages' in value:
                    for msg in value['messages']:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            # 输出工具调用信息
                            for tool_call in msg.tool_calls:
                                # 输出工具调用信息，格式化显示
                                arguments = tool_call.get('args', {})
                                if arguments:
                                    # 格式化参数显示
                                    args_display = json.dumps(arguments, ensure_ascii=False)
                                    tool_info = f"🔍 [正在调用工具] {tool_call['name']}... 📋 输入：{args_display}\n\n"
                                else:
                                    tool_info = f"🔍 [正在调用工具] {tool_call['name']}... 📋 输入：无\n\n"
                                
                                for char in tool_info:
                                    yield char
                        
                        # 只输出非工具消息的内容
                        if hasattr(msg, 'content') and msg.content:
                            # 检查消息是否是 ToolMessage（工具执行结果）
                            if not isinstance(msg, ToolMessage):
                                # 流式输出 AI 回答的每个字符
                                for char in msg.content:
                                    yield char
                            else:
                                # 处理工具执行结果，格式化显示
                                # 检查是否是错误信息
                                content_str = str(msg.content)
                                
                                # 限制输出长度为前200个字符，超过的部分用...代替
                                if len(content_str) > 200:
                                    truncated_content = content_str[:200] + "..."
                                else:
                                    truncated_content = content_str
                                
                                if '"status": "error"' in content_str:
                                    result_info = f"❌ [工具执行结果] {msg.name}... 📋 输出：{truncated_content}\n\n"
                                else:
                                    result_info = f"✅ [工具执行结果] {msg.name}... 📋 输出：{truncated_content}\n\n"
                                
                                for char in result_info:
                                    yield char
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        for char in error_msg:
            yield char


def Agent_langgraph_superchat_invoke(messages: List[MessageDict] = [], config: ConfigDict = {}) -> str:
    """
    最简版 LangGraph AI 聊天函数（非流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature
    
    Returns:
        完整的 AI 回答字符串
    """
        
    if not messages:
        return "你是一名专业的AI助手。"
    
    Clear_proxy()

    # 从config.json中获取配置
    model_key = config.get("model", "qwen3-zte")  # 默认使用qwen3-zte
    
    # 获取模型配置
    model_name, api_key, base_url = Get_model_config(model_key)

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key, # pyright: ignore[reportArgumentType]
        base_url=base_url,
        timeout=30,
        streaming=False, # 不使用流式输出
    )

    tools = [
        current_datetime_get, 
        calculate_square, 
        code_standards_get,
        unsafe_function_get,
        sql_table_get
    ]

    # 转换消息为 LangChain 格式
    langchain_messages = []
    for message in messages:
        content = message["content"]
        if message["role"] == "system":
            langchain_messages.append(SystemMessage(content=content))
        elif message["role"] == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif message["role"] == "assistant":
            langchain_messages.append(AIMessage(content=content))

    # 创建 LangGraph agent
    try:
        agent = create_react_agent(llm, tools)
        
        # 使用 invoke 方法直接获取结果
        result = agent.invoke({"messages": langchain_messages})
        
        # 获取最后一条AI消息的内容
        last_message = result.get('messages', [])[-1] if result.get('messages') else None
        if last_message and hasattr(last_message, 'content') and last_message.content:
            return str(last_message.content)
        else:
            return ""
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        return error_msg


def Agent_langgraph_chat(messages: List[MessageDict] = [], config:  ConfigDict = {}) -> Generator[str, None, None]:
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    if not messages:        
        # 获取通识类知识
        knowledge_public = ""
        knowledge_private = ""

        system_prompt = f"""
            # Persona（角色）：
            你是一名专业的助手。

            # Task（任务）：
            你可以回答用户提出的任何问题。

            # Context（通识知识）
            这是你掌握的通识类知识，可以帮助你了解一些基础信息。
            {knowledge_public}
            
            # Context（私域知识）：
            这是你当前掌握的一些私有信息，你可以根据用户提出的问题，选择是否使用这些信息回答相关的问题。
            {knowledge_private}

            # 注意事项：
            1. 当回答时引用了图片链接，可以直接使用markdown格式输出，这样就可以在前端将图片渲染出来。
            2. 不知道的信息，**禁止**捏造事实和随意回答，要确保回答的内容都是你确实掌握的信息。
            """
        yield system_prompt.strip()
        return
    
    Clear_proxy()
    
    # 获取模型配置
    model_name, api_key, base_url = Get_model_config(config.get("model", "nebula"))

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key, # pyright: ignore[reportArgumentType]
        base_url=base_url,
        timeout=600,
        streaming=True,  # 支持流式输出
    )

    tools = [
        current_datetime_get,
    ]

    # 转换消息为 LangChain 格式
    langchain_messages = []
    for message in messages:
        content = message["content"]
        if message["role"] == "system":
            langchain_messages.append(SystemMessage(content=content))
        elif message["role"] == "user":
            # 应用Replace_question到最新的用户消息
            if message is messages[-1]:  # 如果是最后一条消息（最新的用户消息）
                content = Replace_question(content, matches)
            langchain_messages.append(HumanMessage(content=content))
        elif message["role"] == "assistant":
            langchain_messages.append(AIMessage(content=content))

    # 创建 LangGraph agent
    try:
        agent = create_react_agent(llm, tools)
                
        for chunk in agent.stream({"messages": langchain_messages}):
            for key, value in chunk.items():
                if 'messages' in value:
                    for msg in value['messages']:
                        if hasattr(msg, 'content') and msg.content and not isinstance(msg, ToolMessage):
                            # 流式输出 AI 回答的每个字符
                            for char in msg.content:
                                yield char
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        for char in error_msg:
            yield char



def Agent_call_test(messages: List[MessageDict] = [], config: ConfigDict = {}) -> str:
    """
    测试函数：调用 Agent_ai_chat_langchain 并逐字打印，返回完整回答
    
    Args:
        messages: 聊天消息列表
        config: 模型配置，如 {"model_name": "...", "temperature": 0.7}
    
    Returns:
        完整的 AI 回答字符串
    """
    answer = []
    
    try:
        for chunk in Agent_langgraph_superchat(messages, config):
            # 逐字符打印，模拟打字机效果
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(0.01)  # 可调：控制打印速度
            answer.append(chunk)
        
        print()  # 换行
        return "".join(answer)
    
    except Exception as e:
        error_msg = f"[测试错误] {str(e)}"
        print(error_msg)
        return error_msg


def test_Agent_langgraph_superchat():
    """测试多轮对话功能"""
    print("🚀 开始测试 Agent_ai_chat_langchain（极简版）")
    print("=" * 60)

    # 初始化对话历史
    messages: List[MessageDict] = []

    # 默认配置 - 使用config.json中的模型键
    config: ConfigDict = {
        "model": "qwen3-zte",  # 使用config.json中定义的模型键
        "temperature": 0.7
    }

    print("----- 多轮问答测试（流式输出）-----")

    messages.append({"role": "user", "content": "你好"})
    print("\n👤 用户: 你好")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    messages.append({"role": "user", "content": "世界最高峰是什么？只回答名字。"})
    print("\n👤 用户: 世界最高峰是什么？只回答名字。")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    messages.append({"role": "user", "content": "第二高的呢？"})
    print("\n👤 用户: 第二高的呢？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    messages.append({"role": "user", "content": "今天是几号"})
    print("\n👤 用户: 今天是几号")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    messages.append({"role": "user", "content": "100的平方是多少？"})
    print("\n👤 用户: 100的平方是多少？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 测试数据库查询功能 - 查询单板库表
    messages.append({"role": "user", "content": "关联特性是MCLAG的用例有哪些？"})
    print("\n👤 用户: 关联特性是MCLAG的用例有哪些？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 测试数据库查询功能 - 按条件查询光模块库
    messages.append({"role": "user", "content": "请查询制造厂商为TACLINK的光模块"})
    print("\n👤 用户: 请查询制造厂商为TACLINK的光模块")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})


def test_direct_conversation():
    """
    直接调用 Agent_langgraph_superchat 的会话测试函数
    """
    print("🚀 开始直接测试 Agent_langgraph_superchat")
    print("=" * 60)
    
    # 配置信息
    config: ConfigDict = {
        "model": "qwen3-zte",
        "user_id": "10171727",
        "user_token": "8bdb08ca6cb31034bc7ddf6f2c426965",
        "session_id": f"session_{int(time.time())}",  # 使用时间戳创建唯一session_id
        "request_id": f"request_{int(time.time())}"   # 使用时间戳创建唯一request_id
    }
    
    # 初始化对话历史 - 首先发送一个空消息以初始化系统提示
    print("初始化对话系统...")
    initial_response_parts = []
    for chunk in Agent_langgraph_superchat([], config):
        initial_response_parts.append(chunk)
    initial_response = "".join(initial_response_parts)
    
    # 初始化消息历史
    messages: List[MessageDict] = []
    
    print("开始对话（输入 'quit' 或 'exit' 退出）")
    
    while True:
        user_input = input("\n👤 你: ")
        if user_input.lower() in ['quit', 'exit', 'q', '退出']:
            print("结束对话")
            break
            
        # 生成新的request_id用于每次提问
        config["request_id"] = f"request_{int(time.time())}_{len(messages)}"
        
        # 添加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        
        print("\n🤖 AI: ", end="", flush=True)
        
        # 调用AI获取响应
        ai_response_parts = []
        try:
            for chunk in Agent_langgraph_superchat(messages, config):
                print(chunk, end="", flush=True)  # 直接打印每个字符
                ai_response_parts.append(chunk)
            # 添加延时，确保工具调用的输出内容能够被看到
            time.sleep(2)
        except Exception as e:
            print(f"\n发生错误: {e}")
            continue
            
        ai_response = "".join(ai_response_parts)
        
        # 添加AI回复到历史
        messages.append({"role": "assistant", "content": ai_response})


if __name__ == "__main__":
    test_direct_conversation()
    # test_Agent_langgraph_superchat()
    # content = code_standards_get.invoke({})
    # print(content)
