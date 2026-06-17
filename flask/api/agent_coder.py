
import time
from typing import Generator, List
from datetime import datetime
from ask_ai_request import Chat_ai_stream

# -*- coding: utf-8 -*-
import re
import requests
import json
import csv
import os
import socket
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import difflib
from api_utils import Get_UACtoken

def decrypt(ciphertext_b64: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).digest()
    iv = b'\x00' * 16
    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    return plaintext.decode()

username = "10243863"
password = decrypt("3WcVfR1AjnchVfz8UjdqUg==", "my_secure_password")
uactoken = Get_UACtoken(username, password)

appid = 'e125553c8d8f4b8d87e6043937c6b9b3'
apikey = '2d7764298e5f4df7a5c48d2dda493ebc'

def Agent_ai_tl_generate_code(text):
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
        "stream": False,
        "text": text,
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
        response_json = response.json()
        result = response_json["bo"]["result"]

    except Exception as e:
        raise RuntimeError(f"请求异常: {str(e)}")
    return result

# 标准的AI智能体函数
def Agent_ai_l2_mvp_coder(messages: list = [], model="nebula") -> Generator[str, None, None]:
    system_prompt = "你是一名专业的软件开发工程师。"
    
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    yield "### Step1：识别代码变更点...\n\n"
    yield "从详细设计-业务代码文件设计章节识别到变更代码所在文件：/L2/final/port_config.xml\n\n"
    yield "### Step2：编写代码...\n\n"
    yield "### 📝代码变更内容总结：\n\n"
    yield "port_config.xml\n"
    prompt = Agent_ai_tl_generate_code("https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/7d0ff9e2468c11f0855ea35286050162/view")
    message = [
                {"role": "user", "content": prompt},
            ]
    for chunk in Chat_ai_stream(message, "nebula"):
        yield chunk


# 测试函数，调用AI智能体
def Agent_demo(messages, model="qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_l2_mvp_coder(messages, model):
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
        {"role": "system", "content": "你是一个专业的助手"},
    ]

    messages.append({"role": "user", "content":"你好"})
    Agent_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    # Agent_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"第二高的呢？"})
    # Agent_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"第三高的呢？"})
    # Agent_demo(messages, "qwen")
