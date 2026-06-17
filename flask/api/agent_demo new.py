import time
from typing import Generator
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question


# 标准的AI智能体函数
def Agent_ai_demo(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = "你是一名助手，回答问题非常言简意赅。"

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 示例1：模拟流式返回
    yield "第1步：获取详设功能组件波及...\n\n"
    yield "处理中...\n\n"

    # yield "第2步：识别变更点和变更值...\n\n"
    # yield "处理中...\n\n"

    # yield "第3步：编写代码...\n\n"
    # yield "处理中...\n\n"

    # yield "处理完成！\n\n"
        
    # 示例2：调用封装好的AI大模型接口函数
    answer = ""
    for chunk in Chat_ai_stream(messages, model):
        yield chunk
        answer += chunk

    messages.append({"role": "assistant", "content":answer})
    
    
    #示例3：调用多个大模型接口函数，实现模型间调用组合
    messages.append({"role": "user", "content":"新问题"})
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
        for chunk in Agent_ai_demo(messages, model):
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