import os
import time
import requests
import json
from typing import Generator
from api_utils import Get_UACtoken

username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
uactoken = Get_UACtoken(username, password)

# 波分产品故障问答助手 - 杨东晨
appid = '0aa7b65305104ab9ae4499deffa674f6'
apikey = 'cbccc65b19504a4ab61144979ab11dcb'

def Agent_ai_bugdiag(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = "你是一名助手，来自DNstdio，回答问题非常言简意赅。"

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return
    
    auth_info = f'Bearer {appid}-{apikey}'
    req_args = {
        'headers': {
            'Content-type': 'application/json',
            'X-Emp-No': username,
            'X-Tenant-Id': 'ZTE',
            'X-Auth-Value': uactoken,
            'X-Lang-Id': 'zh_CN',
            'Authorization': ''
        }
    }
    req_args.update({'json': {
        "chatUuid": "",
        "model": "ZTEAIM-Saturn",
        "chatName": "AiQoSCode",
        "keep": True,
        "stream": True,
        "text": messages[-1]["content"],
        # "text":"",
        # "messages":messages,
    }})
    req_args.get('headers').update({'Authorization': auth_info})
    chat_url = 'https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat'
    # 初始化answer列表
    answer = []

    try:
        # 发送流式请求
        response = requests.post(chat_url, **req_args, stream=True)

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
                if "result" in chunk_data:
                    content = chunk_data["result"]
                    if content:  # 只有当内容非空时才处理
                        answer.append(content)
                        yield content
                        
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"解析错误: {e}")
                continue

    except Exception as e:
        raise RuntimeError(f"请求异常: {str(e)}")


# 测试函数，调用AI智能体
def agent_call_demo(messages, model="qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_bugdiag(messages, model):
            # 实现逐字打印效果
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(0.05)  # 模拟延迟
            answer.append(chunk)
        
        print()  # 最终换行
        return "".join(answer)

    except RuntimeError as e:
        print(f"发生错误：{e}")

def test_agent_call_demo():
    # 初始化本次聊天
    messages = [
        {"role": "system", "content": "你是一个专业的助手"},
    ]
    
    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"端口down是什么问题？"})
    answer = agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})


if __name__ == "__main__":
    test_agent_call_demo()