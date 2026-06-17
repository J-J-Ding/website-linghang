import re
import time
import json
from datetime import datetime
from typing import Generator
from dataclasses import dataclass
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question
from api_utils import Replace_icenter


def Agent_ai_bug(messages: list = [], config: dict = {}) -> Generator[str, None, None]:
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        system_prompt = Replace_icenter("https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/20957cff9ad311f08a491175694f0bf2/view")
        yield system_prompt.strip()
        return

    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, messages[-1]["model"]):
        yield chunk

# 测试函数，调用AI智能体
def Agent_call_demo(messages: list = [], model: str = "nebula") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_bug(messages, model):
            # 实现逐字打印效果
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(0.01)  # 模拟延迟
            answer.append(chunk)
        
        print()  # 最终换行
        return "".join(answer)

    except RuntimeError as e:
        print(f"发生错误：{e}")


# 测试用例
def test_Agent_call_demo():
    # 初始化本次聊天
    messages = []

    #初始化一个会话session
    Agent_call_demo()
    
    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"你好"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})
    
    messages.append({"role": "user", "content":"第二高的呢？"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"第三高的呢？"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})


if __name__ == "__main__":    
    test_Agent_call_demo()
