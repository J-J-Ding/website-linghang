import os
import json
import httpx
import openai
from openai import OpenAI
from typing import Generator

# 模型配置字典
MODEL_CONFIG = {
    "deepseek-V3": {
        "key": "sk-a0b7c2f0a1194f30ae7fb110e841743f",
        "url": "https://api.deepseek.com",
        "model": "deepseek-chat"
    },
    "deepseek-R1": {
        "key": "sk-a0b7c2f0a1194f30ae7fb110e841743f",
        "url": "https://api.deepseek.com",
        "model": "deepseek-reasoner"
    },
    "qwen": {
        "key": "sk-0431b0b121cc42b8aeb55cdb6e00a922",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus"
    },
    "nebular": {
        "key": "10171727",
        "url": "http://nebulacoder.dev.zte.com.cn:40081/v1/",
        "model": "nebulacoder-v6.0"
    }
}

def clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)

def Ask(question, model_name="qwen", stream=False):
    config = MODEL_CONFIG[model_name]
    
    client = OpenAI(
        api_key=config["key"],
        base_url=config["url"],
        http_client=httpx.Client(trust_env=False)
    )

    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": "你是一个专业的助手"},
            {"role": "user", "content": question}
        ],
        stream=False,
        # max_tokens=1000,
        # temperature=0.1,
    )

    try:
        answer = response.choices[0].message.content
    except Exception as err:
        print(f"Error: {err}")

    return answer

def Chat(question, messages, model_name="qwen", stream=False):
    clear_proxy()

    config = MODEL_CONFIG[model_name]
    client = OpenAI(api_key=config["key"], base_url=config["url"])
    
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        stream=stream
    )
    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    return answer

def Chat_openai(question: str, model_name: str = "qwen", stream: bool = False) -> Generator[str, None, None]:
    config = MODEL_CONFIG[model_name]

    client = OpenAI(
        api_key=config["key"],
        base_url=config["url"],
        http_client=httpx.Client(trust_env=False)
    )

    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": "你是一个专业的助手"},
            {"role": "user", "content": question}
        ],
        stream=stream,  # 控制是否流式响应
    )

    try:
        if stream:
            # 流式响应逐块 yield
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    answer = chunk.choices[0].delta.content
                    yield answer
        else:
            # 非流式响应，一次性返回完整结果
            answer = response.choices[0].message.content
            yield answer
    except Exception as err:
        yield f"Error: {err}"


if __name__ == "__main__":
    model = "qwen"  # 可以选择 "deepseek-V3", "deepseek-R1", "qwen", "nebular" 中的一个
    
    # 单次问答示例
    # print("-----单轮问答-----")
    # print(Ask("世界上最高的山是什么？只需要告诉我名字就行，不用回答其他内容。", model))
        
    # 多轮问答示例
    # print("-----多轮问答-----")
    # messages = [
    #     {"role": "system", "content": "你是一个专业的助手"}
    # ]
    # print(Chat("世界上最高的山是什么？只需要告诉我名字就行，不用回答其他内容。", messages, model))
    # print(Chat("第二高的呢", messages, model))
    # print(Chat("第三高的呢", messages, model))
    # print(json.dumps(messages, indent=4, ensure_ascii=False))

    # 流式问答与多轮问答兼容，可自由切换
    print("-----流式问答-----")

    for token in Chat_openai("你好，讲个笑话吧", model, stream=True):
        print(token, end="", flush=True)
    print()
    
    # # 非流式问答
    # print("-----非流式问答-----")

    # answer = ''.join(Chat_openai("你好，讲个笑话吧", model, stream=False))
    # print(answer)