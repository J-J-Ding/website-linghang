import time
from typing import Generator
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question


# 标准的AI智能体函数
def Agent_ai_se(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = """
        你是一位资深软件开发架构师，拥有 10 年以上分布式系统与微服务架构经验。你的核心职责是保障系统的高可用、可扩展性和技术前瞻性，同时指导团队遵循最佳工程实践。
        """
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    answer = ""
    # 调用封装好的AI大模型接口函数
    for chunk in Chat_ai_stream(messages, model):
        yield chunk
        answer += chunk


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
        for chunk in Agent_ai_se(messages, model):
            # 实现逐字打印效果
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(0.01)  # 模拟延迟
            answer.append(chunk)
        
        print()  # 最终换行
        return "".join(answer)

    except RuntimeError as e:
        print(f"发生错误：{e}")

if __name__ == "__main__":    
    # 初始化本次聊天
    messages = [
        # {"role": "system", "content": "你是一个专业的助手"},
    ]
    
    #初始化一个会话session
    answer = Agent_call_demo()
    messages.append({"role": "system", "content":answer})

    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"OTNSW-687953"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    # messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})
    
    # messages.append({"role": "user", "content":"第二高的呢？"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})

    # messages.append({"role": "user", "content":"第三高的呢？"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})
