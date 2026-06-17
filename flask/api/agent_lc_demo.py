import os
import re
import time
import json
from datetime import datetime
from typing import Generator, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question

def clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)

def Agent_ai_chat_langchain(messages: List[Dict] = [], config: dict = None) -> Generator[str, None, None]:
    """
    最简版 LangChain AI 聊天函数（流式输出）
    
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
        streaming=True,  # 启用流式
    )

    # 转换消息为 LangChain 格式
    langchain_messages = []

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

    # 流式调用并逐字符输出
    try:
        for chunk in llm.stream(langchain_messages):
            content = chunk.content
            for char in content:
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
        for chunk in Agent_ai_chat_langchain(messages, config):
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


def test_Agent_ai_chat_langchain():
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
    messages.append({"role": "user", "content": "第三高的呢？"})
    print("\n👤 用户: 第三高的呢？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})

    # 第五轮
    messages.append({"role": "user", "content": "介绍一下红楼梦这本书。"})
    print("\n👤 用户: 介绍一下红楼梦这本书。")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})


    print("\n✅ 测试完成！最终对话历史:")
    for msg in messages:
        role = "🧑‍💻 用户" if msg["role"] == "user" else "🤖 AI"
        print(f"{role}: {msg['content']}")


if __name__ == "__main__":
    test_Agent_ai_chat_langchain()

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