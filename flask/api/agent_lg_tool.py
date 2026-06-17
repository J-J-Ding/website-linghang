import os
import re
import time
import json
from datetime import datetime
from typing import Generator, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question

@tool("时间查询工具")
def get_current_datetime() -> str:
    """
    获取当前系统日期和时间的工具
    
    Returns:
        str: 当前日期和时间的字符串，格式为 'YYYY-MM-DD HH:MM:SS'
    """
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


@tool("平方计算工具")
def calculate_square(number: int) -> int:
    """
    计算一个数的平方的工具
    
    Args:
        number: 需要计算平方的数值
        
    Returns:
        float: 该数的平方值
    """
    return number ** 2


def clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)

def Agent_ai_chat_langgraph(messages: List[Dict] = [], config: dict = None) -> Generator[str, None, None]:
    """
    最简版 LangGraph AI 聊天函数（流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature
    
    Yields:
        逐字符返回 AI 回答
    """
        
    if not messages:
        yield "你是一名专业的AI助手。"
        return
    
    clear_proxy()

    # model_name = config.get("model_name", "Qwen3-235B-A22B")
    model_name = "nebulacoder-lite-v7.0"
    url = "http://nebulacoder.dev.zte.com.cn:40081/v1"
    key = "10171727"

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=key,
        base_url=url,
        timeout=30,
        streaming=True,  # 支持流式输出
    )

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
        agent = create_react_agent(llm, tools=[get_current_datetime, calculate_square])
        
        # 使用 stream 方法来获取流式输出
        for chunk in agent.stream({"messages": langchain_messages}):
            # 检查是否为工具调用
            for key, value in chunk.items():
                if 'messages' in value:
                    for msg in value['messages']:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            # 输出工具调用信息
                            for tool_call in msg.tool_calls:
                                # 工具名称现在已经是别名
                                tool_info = f"[调用工具: {tool_call['name']}] "
                                for char in tool_info:
                                    yield char
                        
                        if hasattr(msg, 'content') and msg.content:
                            # 流式输出 AI 回答的每个字符
                            for char in msg.content:
                                yield char
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        for char in error_msg:
            yield char


def Agent_call_test(messages: List[Dict] = [], config: dict = None) -> str:
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
    messages = []

    # 默认配置
    config = {
        "model_name": "Qwen3-235B-A22B",
        "temperature": 0.7
    }

    print("----- 多轮问答测试（流式输出）-----")

    # 第一轮
    messages.append({"role": "user", "content": "你好"})
    print("\n👤 用户: 你好")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 第二轮
    messages.append({"role": "user", "content": "世界最高峰是什么？只回答名字。"})
    print("\n👤 用户: 世界最高峰是什么？只回答名字。")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 第三轮
    messages.append({"role": "user", "content": "第二高的呢？"})
    print("\n👤 用户: 第二高的呢？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})


    # 第四轮
    messages.append({"role": "user", "content": "今天是几号"})
    print("\n👤 用户: 今天是几号")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 第五轮
    messages.append({"role": "user", "content": "100的平方是多少？"})
    print("\n👤 用户: 100的平方是多少？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    test_Agent_ai_chat_langgraph()


    # print("hello world!")

    # # 处理代理设置
    # http_client = httpx.Client(
    #     timeout=60.0,
    #     # 不设置代理参数，避免socks代理问题
    # )

    # llm = ChatOpenAI(
    #     model="Qwen3-235B-A22B",
    #     api_key="10171727",
    #     base_url="http://10.208.65.74:31098/v1",
    #     http_client=http_client
    # )

    # response = llm.invoke("你是谁？")
    # print(response)