import requests
import time
import json
from typing import Generator
from pprint import pprint
# import pandas as pd
# import pandasai as pdai
# from openai import OpenAI
# from pandasai import Agent, SmartDataframe
# from pandasai_litellm import LiteLLM

# 定义映射关系表
KNOWLEDGE_MAP = {
    'Feature': {
        'L0': '',
        'L1': '',
        'L2': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/36c23907568611f08986edd3c38d5330/view',
        'OSP': '',
        'WASON': ''
    },
}

# 模型配置字典
MODEL_CONFIG = {
    "deepseek-V3": {
        "key": "sk-a0b7c2f0a1194f30ae7fb110e841743f",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat"
    },
    "deepseek-R1": {
        "key": "sk-a0b7c2f0a1194f30ae7fb110e841743f",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-reasoner"
    },
    "qwen": {
        "key": "sk-0431b0b121cc42b8aeb55cdb6e00a922",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus-latest"
    },
    "qwen3-coder": {
        "key": "sk-0431b0b121cc42b8aeb55cdb6e00a922",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen3-coder-plus"
    },
    "kimi-K2":{
        "key":"sk-LlagMyRsxgXORA5rw5UG6qzkJLXDOv2jsUxuOZ2gCYgRS89U",
        "url":"https://api.moonshot.cn/v1/chat/completions",
        "model":"kimi-k2-0711-preview"
    },
    "nebula": {
        "key": "dc2b13d7-ac3a-4338-bea0-a334cc1ae1c7",
        "url": "https://nebulacoder-maas.zte.com.cn/v1/chat/completions",
        "model": "nebulacoder-lite-v7.0"
    },
    "qwen3-zte": {
        "key": "10171727",
        "url": "http://10.57.165.185:26003/v1/chat/completions",
        "model": "Qwen3-235B-A22B"
    }
}

def Ask_ai(question, model_name="qwen"):
    config = MODEL_CONFIG[model_name]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['key']}"
    }

    data = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "你是一个专业的助手"},
            {"role": "user", "content": question}
        ],
        "stream": False
    }

    response = requests.post(config["url"], headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']
        return answer
    else:
        print("请求失败，错误码：", response.status_code)
        return None

def Chat_ai(question, messages, model_name="qwen"):
    config = MODEL_CONFIG[model_name]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['key']}"
    }

    # 添加用户的问题到消息列表
    messages.append({"role": "user", "content": question})

    data = {
        "model": config["model"],
        "messages": messages,
        "stream": False
    }

    response = requests.post(config["url"], headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        answer = result['choices'][0]['message']['content']
        # 添加助手的回答到消息列表
        messages.append({"role": "assistant", "content": answer})
        return answer
    else:
        print("请求失败，错误码：", response.status_code)
        return None

def Chat_ai_stream(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    根据 messages 获取聊天记录，返回格式为：
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    """
    config = MODEL_CONFIG[model]
    system_prompt = f"""
            # Persona（角色）：
            你是一个专业的助手。

            # Task（任务）：
            你可以回答用户提出的任何问题。

            # 注意事项：
            1. 当回答时引用了图片链接，可以直接使用markdown格式输出，这样就可以在前端渲染出来。
            2. 不知道的信息，禁止捏造事实和随意揣测，要确保回答的内容都是你确实掌握的信息。
            """
    answer = []

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return
    
    try:
        # 发送流式请求
        response = requests.post(
            url=config["url"],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['key']}"
            },
            json={
                "model": config["model"],
                "messages": messages,
                "stream": True,
                # "max_tokens":32768,
            },
            stream=True
        )

        if response.status_code != 200:
            raise RuntimeError(f"请求失败，状态码：{response.status_code}")

        # 处理流式响应
        for chunk in response.iter_lines():
            if not chunk:
                continue
                
            try:
                decoded_chunk = chunk.decode('utf-8')
                if not decoded_chunk.startswith("data:"):
                    continue
                    
                json_data = decoded_chunk[5:].strip()
                if json_data == "[DONE]":
                    continue
                    
                chunk_data = json.loads(json_data)
                if "choices" in chunk_data and chunk_data.get("choices", [{}])!=[]:
                    delta = chunk_data["choices"][0].get("delta", {})
                    if "content" in delta:
                        answer.append(delta["content"])
                        yield delta["content"]
                        
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

    except Exception as e:
        raise RuntimeError(f"请求异常: {str(e)}")


def Chat_ai_agent(question: str, messages: list, model: str = "qwen") -> Generator[str, None, None]:
    config = MODEL_CONFIG[model]
    answer = []
    messages.append({"role": "user", "content": question})  # 更新消息列表

    # 调用其他处理函数并获取它们的流式输出
    def process_other_functions() -> Generator[str, None, None]:
        # 示例1: 调用处理函数A
        for chunk in other_processing_function_a(question):
            yield f"[Processing A] {chunk}\n"
        
        # 示例2: 调用处理函数B
        result = other_processing_function_b(question)
        if result:
            yield f"[Processing B] {result}\n"
    
    # 首先产生其他处理函数的输出
    yield from process_other_functions()

    try:
        # 发送流式请求
        response = requests.post(
            url=config["url"],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['key']}"
            },
            json={
                "model": config["model"],
                "messages": messages,
                "stream": True
            },
            stream=True
        )

        if response.status_code != 200:
            raise RuntimeError(f"请求失败，状态码：{response.status_code}")

        # 处理流式响应
        for chunk in response.iter_lines():
            if not chunk:
                continue
                
            try:
                decoded_chunk = chunk.decode('utf-8')
                if not decoded_chunk.startswith("data:"):
                    continue
                    
                json_data = decoded_chunk[5:].strip()
                if json_data == "[DONE]":
                    continue
                    
                chunk_data = json.loads(json_data)
                if "choices" in chunk_data:
                    delta = chunk_data["choices"][0].get("delta", {})
                    if "content" in delta:
                        answer.append(delta["content"])
                        yield delta["content"]
                        
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

        # 更新聊天记录
        if answer:
            messages.append({"role": "assistant", "content": "".join(answer)})

    except Exception as e:
        raise RuntimeError(f"请求异常: {str(e)}")


def Chat_agent_stream(messages: list, model: str = "qwen") -> Generator[str, None, None]:
    """Modified version that only handles processing functions without API calls"""
    answer = []

    def process_other_functions() -> Generator[str, None, None]:
        """Handle all processing functions with streaming output"""
        # Example processing function A - streaming
        for chunk in other_processing_function_a():
            yield f"[Processing] {chunk}\n"
        
        # Example processing function B - direct return
        result = other_processing_function_b()
        if result:
            yield f"[Result] {result}\n"
        
    # Main generator yields processing outputs
    yield from process_other_functions()


# 示例处理函数A - 流式输出
def other_processing_function_a() -> Generator[str, None, None]:
    # 模拟处理过程
    steps = [
        "开始分析用户问题：检测到问题类型为'技术支持类'查询，正在初始化问题分类模块...",
        "问题分类完成：确定属于'网络连接故障'子类别，加载相关解决方案数据库...",
        "检索知识库：已匹配到12条相关解决方案，正在按优先级排序...",
        "分析解决方案：排除8条不适用方案，剩余4条潜在解决方案进入深度验证...",
        "验证方案1：检查设备网络适配器状态 - 需要获取用户设备信息...",
        "验证方案2：检测本地DNS设置 - 正在模拟测试环境...",
        "验证方案3：重置网络套接字 - 准备执行脚本...",
        "验证方案4：检查代理服务器设置 - 需要用户权限确认...",
        "生成响应框架：整合3个最优解决方案，构建分步骤指导流程...",
        "本地化处理：适配用户所在地区(检测为华东区域)的网络配置标准...",
        "安全检查：验证所有建议操作符合网络安全规范...",
        "生成最终响应：正在格式化输出内容，添加示意图标记...",
        "质量检测：通过BERT模型验证响应易读性得分92/100...",
        "添加补充说明：插入常见问题解答链接和视频教程参考...",
        "最终校验：确认所有技术术语都有悬浮解释框定义..."
    ]

    for step in steps:
        yield step
        # 模拟处理延迟
        import time
        time.sleep(0.5)

# 示例处理函数B - 直接返回结果
def other_processing_function_b() -> str:
    # 模拟直接返回结果
    return "预处理完成"

def chat_stream_demo(messages: list, model: str = "qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        question: 用户问题
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Chat_ai_stream(messages, model):
            # 实现逐字打印效果
            for char in chunk:
                print(char, end="", flush=True)
            answer.append(chunk)
        
        print()  # 最终换行
        return "".join(answer)

    except RuntimeError as e:
        print(f"发生错误：{e}")


if __name__ == "__main__":
    model = "qwen3-zte"  # 可以选择 "deepseek-V3", "deepseek-R1", "qwen", "nebular" ，“kimi-K2”中的一个
    messages = [
        {"role": "system", "content": "你是一个专业的助手"}
    ]

    # print("-----单轮问答-----")
    # print(Ask_ai("世界上最高的山是什么？只需要告诉我名字就行，不用回答其他内容。", model))
        
    # print("-----多轮问答-----")
    # messages = [
    #     {"role": "system", "content": "你是一个专业的助手"}
    # ]
    # print(Chat_ai("世界上最高的山是什么？只需要告诉我名字就行，不用回答其他内容。", messages, model))
    # print(Chat_ai("第二高的呢", messages, model))
    # print(Chat_ai("第三高的呢", messages, model))

    print("-----多轮问答(流式)-----")
    answer = Chat_ai_stream()

    messages.append({"role": "user", "content":"你好"})
    answer = chat_stream_demo(messages, model)
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    answer = chat_stream_demo(messages, model)
    messages.append({"role": "assistant", "content":answer})
    
    messages.append({"role": "user", "content":"第二高的呢？"})
    answer = chat_stream_demo(messages, model)
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"第三高的呢？"})
    answer = chat_stream_demo(messages, model)
    messages.append({"role": "assistant", "content":answer})

    # # 配置大模型
    # config = MODEL_CONFIG["nebula"]
    # llm = LiteLLM(model="openai/"+config["model"], api_key=config["key"], api_base=config["url"])
    # pdai.config.set({"llm":llm})
    # # print(pdai)

    # # 示例1，单表对话
    # # df=pdai.read_csv("data.csv")
    # # print(df)

    # # 修改后的代码
    # # response = df.chat("笔记本电脑的价格是多少？，另外你是什么大模型？")
    # # pandas_df = response.value
    # # print(pandas_df)
    # # print(type(pandas_df))

    # # response_description = pdai.DataFrame(response.value).chat("解释一下这些数据。")
    # # print(response_description)

    # # 示例2，智能体连续对话
    # # Sample DataFrames
    # sales_by_country = pdai.read_csv("../data/data.csv")

    # # agent = Agent(sales_by_country)
    # agent = Agent(
    #     sales_by_country,
    #     description="你是一名数据分析师，你的核心目标是帮助用户完成数据分析任务，使用中文回答。",
    #     memory_size=10,
    # )
    # response = agent.chat('你好，我是陈雷，请问销售额排名前5的国家是哪些？请在每次回答我的时候说 你好陈雷。')
    # print(f"第1次:\n {response}")

    # response = agent.chat('第6名的国家呢？')
    # print(f"第2次: \n{response}")

    # response = agent.chat('第7名的国家呢？')
    # print(f"第3次: \n{response}")

    # response = agent.chat('第8名的国家呢？')
    # print(f"第4次: \n{response}")

    # response = agent.chat('第9名的国家呢？')
    # print(f"第5次:\n {response}")