"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""
import socket
import hashlib
import requests
import json
import sys
import os
from mcp.server.fastmcp import FastMCP
# from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Graphdb")

class UACTokenGenerator:

    def __init__(self):
        pass

    @staticmethod
    def get_host_ip():
        hostname = socket.gethostname()
        first_ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        return first_ip

    @staticmethod
    def get_token(emp_no, password):
        url = "http://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
        client_ip = UACTokenGenerator.get_host_ip()
        loginsyscode = 'Portal'
        originsyscode = ''
        token = ''

        text =\
        {
            "account": emp_no,
            "passWord": password,
            "loginClientIp": client_ip,
            "loginSystemCode": loginsyscode,
            "originSystemCode": originsyscode,
            "other": {
                "networkArea":'1',
                "networkAccessType":'1'
            },
            "verifyCode":hashlib.md5(str(emp_no+password+client_ip+loginsyscode+originsyscode)
                                    .encode(encoding='utf-8')).hexdigest()  
        }
        headers = {'Content-type': 'application/json'}
        content = requests.post(url,data=json.dumps(text),headers=headers).json()
        if content['code']['code'] == '0000' and content['bo']['code'] == '0000' :
            token = content['other']['token']
            # print(token)
        return token




# Add an addition tool
@mcp.tool()
def add(a: float, b: float) -> float:
    """加法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之和
    """
    return 100

@mcp.tool()
def graphdb(question: str) -> str:
    emp_no = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    uac_token = UACTokenGenerator.get_token(emp_no, password)

    auth_info = 'Bearer 452f368f6040457b8ff761e2c564e12d-e65dae460b8143a0a851dfc489f1e9d2'
    req_args = {
        'headers': {
            'Content-type': 'application/json',
            'X-Emp-No': emp_no,
            'X-Tenant-Id': 'ZTE',
            'X-Auth-Value': uac_token,
            'X-Lang-Id': 'zh_CN',
            'Authorization': ''
        }
    }
    req_args.update({'json': {
        "chatUuid": "",
        "model": "ZTEAIM-Saturn",
        "chatName": "AiQoSCode",
        "keep": False,
        "stream": False,
        "text": question
    }})
    req_args.get('headers').update({'Authorization': auth_info})
    chat_url = 'https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat'
    req = requests.post(chat_url, **req_args)

    if req.status_code == 200:
        response_json = req.json()
        result = response_json["bo"]["result"]
    else:
        result = ""

    return result


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."

if __name__ == "__main__":
    mcp.run(transport='sse', host="127.0.0.1", port=8031)

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# app = FastAPI()

# class InputData(BaseModel):
#     data: str

# class OutputData(BaseModel):
#     message: str
#     data: str

# @app.post("/graphRag")
# def process_request(inputData:InputData):
#     data = graphdb(inputData.data)
#     if data:
#         message = "查询成功"
#     else:
#         message = "查询失败"
#     output_data = OutputData(message=message, data=data)
#     return output_data

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=4002)
