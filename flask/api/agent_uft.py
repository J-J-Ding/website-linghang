import os
import time
from typing import Generator
from ask_ai_request import Chat_ai_stream
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question, Get_rdc_markdown

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, '.', 'uft_test.txt')

with open('uft_test.txt', 'r', encoding='utf-8') as file:
    knowledge = file.read()

prompt = f"""# Persona（角色）：
        你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范。

        # Task（任务）：
        你可以回答用户提出的针对代码的问题，结合代码给出具体的配置步骤和函数的调用顺序。

        # Context（上下文）：
        ## 这是核心代码：
        {knowledge}"""


# 标准的AI智能体函数
def Agent_ai_develop(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = prompt

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, model):
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
        for chunk in Agent_ai_develop(messages, model):
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

    # 初始化一个会话session

    print("-----多轮问答(流式)-----")
    messages.append({"role": "system", "content": prompt})
    messages.append({"role": "user", "content": "聚合组(Trunk)成员端口创建有哪些配置步骤"})
    #messages.append({"role": "user", "content": "聚合组(Trunk)成员端口激活有哪些配置步骤"})
    #messages.append({"role": "user", "content": "聚合组(Trunk)成员端口移除有哪些配置步骤"})
    #messages.append({"role": "user", "content": "删除聚合组有哪些配置步骤"})
    #messages.append({"role": "user", "content": "手工主备模块快切有哪些配置步骤"})
    # messages.append({"role": "user", "content": "更新聚合组负载分担方式有哪些配置步骤"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    test_Agent_call_demo()

