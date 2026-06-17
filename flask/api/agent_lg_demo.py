import os
import re
import time
import json
from datetime import datetime
from typing import Generator, Dict, Any, List, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from agent_base import MessageDict, ConfigDict

from api_data import TOOL_Table_get
from get_icenter import Get_icenter_content_markdown, Icenter_content_html_get, Icenter_content_html_set
from get_rdc import Get_rdc_markdown, Rdc_field_set, Rdc_field_get
from agent_utils import Get_model_config, Clear_proxy

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


def Agent_ai_chat_langgraph(messages: List[MessageDict] = [], config: ConfigDict = {}) -> Generator[str, None, None]:
    """
    最简版 LangGraph AI 聊天函数（流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature
    
    Yields:
        逐字符返回 AI 回答
    """
        
    if not messages:        
        yield "你是一名AI助手。"
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
        calculate_square
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


def Agent_ai_chat_langgraph_invoke(messages: List[MessageDict] = [], config: ConfigDict = {}) -> str:
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
        for chunk in Agent_ai_chat_langgraph(messages, config):
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


def test_Agent_ai_chat_langgraph():
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

if __name__ == "__main__":
    test_Agent_ai_chat_langgraph()
    # content = code_standards_get.invoke({})
    # print(content)
