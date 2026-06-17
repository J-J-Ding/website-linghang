import os
import re
import time
import json
from datetime import datetime
from typing import Generator, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool


def clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)

@tool
def get_current_time() -> str:
    """获取当前系统时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def Agent_ai_chat_langchain(messages: List[Dict] = [], config: dict = None) -> Generator[str, None, None]:
    """
    最简版 LangChain AI 聊天函数（支持工具调用 + 流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model 和 temperature
    
    Yields:
        逐字符返回 AI 回答
    """

    if not messages:
        yield "你是一名专业的AI助手。"
        return

    # 每次请求都清除代理设置
    clear_proxy()

    # 获取配置
    # model_name = config.get("model", "Qwen3-235B-A22B")

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model="Qwen3-235B-A22B",
        api_key="10171727",
        base_url="http://10.208.65.74:31098/v1",
        timeout=30,
        streaming=True,
    ).bind_tools([get_current_time])

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
        # 注意：不处理 tool 消息，由本函数生成

    try:
        accumulated_content = ""
        tool_calls_buffer = []

        # 第一次流式调用
        for chunk in llm.stream(langchain_messages):
            if chunk.content:
                for char in chunk.content:
                    yield char
                    accumulated_content += char

            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                tool_calls_buffer.extend(chunk.tool_calls)

        # =============================
        # 🛠️ 处理工具调用
        # =============================
        if tool_calls_buffer:
            # ✅ 新增：主动输出“正在调用工具”提示（逐字符）
            tool_prompt = ""
            for tool_call in tool_calls_buffer:
                if tool_call["name"] == "get_current_time":
                    tool_prompt = "调用Tool：获取系统时间...\n"

            if tool_prompt:
                for char in tool_prompt:
                    yield char  # 逐字符输出提示
                    time.sleep(0.01)  # 可选：模拟打字机效果
                yield "\n"  # 可选：换行

            # 添加 AI 的工具调用请求消息
            ai_message = AIMessage(
                content=accumulated_content,
                tool_calls=tool_calls_buffer
            )
            langchain_messages.append(ai_message)

            # 执行每个工具
            for tool_call in tool_calls_buffer:
                if tool_call["name"] == "get_current_time":
                    try:
                        result = get_current_time.invoke({})
                    except Exception as e:
                        result = f"工具执行出错: {str(e)}"

                    tool_message = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"]
                    )
                    langchain_messages.append(tool_message)

            # 再次流式调用，获取最终回复
            for final_chunk in llm.stream(langchain_messages):
                final_content = final_chunk.content
                if final_content:
                    for char in final_content:
                        yield char

    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        for char in error_msg:
            yield char

def Agent_call_test(messages: List[Dict] = [], config: dict = None) -> str: # type: ignore
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
    messages.append({"role": "user", "content": "今天是几号？"})
    print("\n👤 用户: 今天是几号？")
    answer = Agent_call_test(messages, config)
    messages.append({"role": "assistant", "content": answer})


    print("\n✅ 测试完成！最终对话历史:")
    for msg in messages:
        role = "🧑‍💻 用户" if msg["role"] == "user" else "🤖 AI"
        print(f"{role}: {msg['content']}")


if __name__ == "__main__":
    clear_proxy()
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