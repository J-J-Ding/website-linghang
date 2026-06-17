import os
import re
import csv
import json
import time
import pandas as pd
from typing import Generator, List, Dict, Any
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question



def parse_json_response(response: str) -> dict:
    """解析包含在Markdown代码块中的JSON响应"""
    # 提取json代码块内容
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if not json_match:
        raise ValueError("未找到有效的JSON代码块")
    
    # 提取json内容
    json_str = json_match.group(1)
    
    # 解析JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {str(e)}")


# 标准的AI智能体函数
def Agent_ai_autowork(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = "你是一个高级任务规划专家，擅长识别用户意图和目标，对复杂任务进行分解和规划。"

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


    # 1. 识别用户意图并生成计划
    yield "#### ✅Step1：识别用户意图...\n\n"
    user_task = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
    if not user_task:
        yield "错误：未找到用户任务"
        return

    plan_prompt = f"""
    你是一个高级任务规划专家，擅长识别用户意图和目标，对复杂任务进行分解和规划，请将以下任务分解为逐步解决的方案：
    任务：{user_task}
    
    要求：
    1. 将目标分解为可顺序执行的3-5个子步骤，遵循MECE原则（相互独立、完全穷尽）
    2. 每步骤包含：
       - 目标：清晰的任务目标
       - 指令：具体的处理方式
    3. 用JSON格式返回：{{"steps": [{{"step":"step1", "goal":"目标", "process":"指令"}}]}}
    """
    
    plan_messages = [
        {"role": "system", "content": "你是任务分解专家，输出严格JSON格式"},
        {"role": "user", "content": plan_prompt}
    ]
    
    plan_response = ""
    for chunk in Chat_ai_stream(plan_messages, model):
        # yield chunk
        plan_response += chunk
    
    try:
        plan_data = parse_json_response(plan_response)
        steps = plan_data["steps"]
    except (ValueError, KeyError) as e:
        yield f"计划生成失败: {str(e)}"
        return

    # 2. 构建计划列表
    yield "\n\n#### ✅Step2：创建任务计划...\n\n"
    plan_list = []
    for step in steps:
        plan_list.append({
            "步骤": step["step"],
            "目标": step["goal"],
            "指令": step["process"],
            "输出": "",
            "状态": "进行中"
        })
    
    # 创建DataFrame
    df = pd.DataFrame(plan_list)

    # 生成HTML输出
    html_output = df[["步骤", "目标", "指令"]].to_html(index=False)
    yield html_output
    yield "\n\n"

    # 3. 执行任务计划
    yield "#### ✅Step3：执行任务计划...\n\n"
    # exec_messages = messages.copy()  # 使用原始消息作为上下文
    exec_messages = [
        {"role": "system", "content": "你是一名助手，会针对目标准确的执行任务，只输出目标需要的结果，不做过多扩展和解释说明。"}
    ]

    for i, item in enumerate(plan_list):
        yield f"\n> 🔧 执行步骤 {item['步骤']}: {item['目标']}\n\n"
        
        # 准备输入
        input_data = user_task if i == 0 else plan_list[i-1]["输出"]
        instruction = item["指令"].replace("{input}", input_data)
        
        # 添加当前指令到消息
        exec_messages.append({"role": "user", "content": instruction})
        
        # 执行AI处理
        step_output = []
        for chunk in Chat_ai_stream(exec_messages, model):
            yield chunk
            step_output.append(chunk)
        
        output_content = "".join(step_output)
        plan_list[i]["输出"] = output_content
        plan_list[i]["状态"] = "已完成"  # 更新状态为已完成
        
        # 添加AI响应到消息
        exec_messages.append({"role": "assistant", "content": output_content})
        
        yield "\n\n"

    # 4. 总结提炼最终结果
    yield "#### ✅Step4：总结最终结果...\n\n"
    summary_prompt = f"""
    基于以下任务执行结果，总结提炼最终答案：
    原始任务: {user_task}
    
    要求：
    1. 只输出最终结果，忽略中间过程
    2. 直接回答用户问题，不需要解释过程
    3. 内容简洁明了
    """
    
    summary_messages = exec_messages.copy()
    summary_messages.append({"role": "user", "content": summary_prompt})
    
    for chunk in Chat_ai_stream(summary_messages, model):
        yield chunk
    yield "\n\n"

    # 创建DataFrame
    df = pd.DataFrame(plan_list)

    # 生成HTML输出
    html_output = df[["步骤", "目标", "状态"]].to_html(index=False)
    yield html_output
    yield "\n\n"

    yield "#### ✅Done：全部任务执行完成！\n\n"

# 测试函数，调用AI智能体
def Agent_call_demo(messages, model="qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_autowork(messages, model):
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
    
    system_prompt = Agent_ai_autowork()
    messages.append({"role": "system", "content":system_prompt})

    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"请帮我实现一个冒泡还需的函数，使用C语言，并生成UT用例对其进行测试，要求对所有场景进行充分的覆盖。"})
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
