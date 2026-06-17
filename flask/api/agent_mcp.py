import os
import time
import logging
import json
import inspect
import requests
import openai
import asyncio
from dataclasses import asdict 
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from contextlib import contextmanager
from openai import OpenAI
from typing import Generator, Optional
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question, Get_file_from_server, Replace_icenter

@contextmanager
def clear_proxy():
    old_proxies = {p: os.environ.get(p) for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')}
    
    try:
        for p in old_proxies:
            os.environ.pop(p, None)
        yield
    finally:
        for p, val in old_proxies.items():
            if val is not None:
                os.environ[p] = val

class LLMClient:
    def __init__(self, model_name: str, url: str, api_key: str) -> None:
        self.model_name: str = model_name
        self.url: str = url
        self.client = OpenAI(api_key=api_key, base_url=url, http_client=None)

    def get_response(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content


class ChatSession:
    def __init__(self, llm_client: LLMClient, mcp_client: stdio_client, ) -> None:
        self.mcp_client: Client = mcp_client
        self.llm_client: LLMClient = llm_client

    async def process_llm_response(self, llm_response: str) -> str:
        try:
            # 尝试移除可能的markdown格式
            if llm_response.startswith('```json'):
                llm_response = llm_response.strip('```json').strip('```').strip()
            
            # 处理可能的多个工具调用
            if llm_response.startswith('['):  # 多个工具调用的数组格式
                tool_calls = json.loads(llm_response)
                results = []
                for tool_call in tool_calls:
                    if "tool" in tool_call and "arguments" in tool_call:
                        tools = await self.mcp_client.list_tools()
                        if any(tool.name == tool_call["tool"] for tool in tools):
                            try:
                                result = await self.mcp_client.call_tool(
                                    tool_call["tool"], tool_call["arguments"]
                                )
                                results.append(f"{tool_call['tool']}执行结果: {result}")
                            except Exception as e:
                                results.append(f"{tool_call['tool']}执行错误: {str(e)}")
                return "\n".join(results) if results else llm_response
            else:  # 单个工具调用
                tool_call = json.loads(llm_response)
                if "tool" in tool_call and "arguments" in tool_call:
                    # 检查工具是否可用
                    # tools = await self.mcp_client.list_tools()
                    tools_result = await self.mcp_client.list_tools()          # ListToolsResult
                    tools = tools_result.tools
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            # 执行工具调用
                            result = await self.mcp_client.call_tool(
                                tool_call["tool"], tool_call["arguments"]
                            )
                            return f"Tool execution result: {result}"
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logging.error(error_msg)
                            return error_msg
                    return f"No server found with tool: {tool_call['tool']}"
                return llm_response
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接返回原始响应
            return llm_response

    async def start(self, tools_description) -> Generator[str, None, None]: 
        # 初始化本次聊天
        messages = []
        # 系统提示，指导LLM如何使用工具和返回响应
        system_prompt = f'''
                你是一个智能助手，严格遵循以下协议返回响应：

                可用工具：{tools_description}

                响应规则：
                1、当需要计算时，返回严格符合以下格式的纯净JSON，其中不允许对用户输入的英文进行大小写的转换：
                {{
                    "tool": "tool-name",
                    "arguments": {{
                        "argument-name": "value"
                    }}
                }}
                2、禁止包含以下内容：
                - Markdown标记（如```json）
                - 自然语言解释（如"结果："）
                - 格式化数值（必须保持原始精度）
                - 单位符号（如元、kg）

                校验流程：
                ✓ 参数数量与工具定义一致
                ✓ 数值类型为number
                ✓ JSON格式有效性检查

                正确示例：
                用户：单价88.5买235个多少钱？
                响应：{{"tool":"multiply","arguments":{{"a":88.5,"b":235}}}}

                错误示例：
                用户：总金额是多少？
                错误响应：总价500元 → 含自然语言
                错误响应：```json{{...}}``` → 含Markdown

                3、在收到工具的响应后：
                - 将原始数据转化为自然、对话式的回应
                - 保持回复简洁但信息丰富
                - 聚焦于最相关的信息
                - 使用用户问题中的适当上下文
                - 避免简单重复使用原始数据
                '''

        messages.append({"role": "system", "content": system_prompt})

        while True:
            try:
                user_input = input("用户: ").strip()
                if user_input in ["quit", "exit", "退出"]:
                    print('AI助手退出')
                    break
                messages.append({"role": "user", "content": user_input})

                # 获取LLM的初始响应
                llm_response = ""
                # llm_response = self.llm_client.get_response(messages)
                for chunk in Chat_ai_stream(messages, "nebula"):
                    llm_response = llm_response + chunk
                    yield chunk
                print("\n")
                # 处理可能的工具调用
                result = await self.process_llm_response(llm_response)

                # 如果处理结果与原始响应不同，说明执行了工具调用，需要进一步处理
                while result != llm_response:
                    print("mcp的调用结果：", result)
                    print("\n")
                    messages.append({"role": "assistant", "content": llm_response})
                    messages.append({"role": "system", "content": result})

                    # 将工具执行结果发送回LLM获取新响应
                    # llm_response = self.llm_client.get_response(messages)
                    # result = await self.process_llm_response(llm_response)
                    # print(llm_response)
                    for chunk in Chat_ai_stream(messages, "nebula"):
                        yield chunk

                    break

                messages.append({"role": "assistant", "content": llm_response})

            except KeyboardInterrupt:
                print('AI助手退出')
                break

# 测试用例
async def test_Agent_call_demo():
    GRAPHDB_ROOT = "graphdb_service/mcp-server-graphdb"
    mcp_env = os.environ.copy()
    mcp_env.update({
        "all_proxy": "socks://proxyhk.zte.com.cn:80",
        "http_proxy":  "http://proxyhk.zte.com.cn:80",
        "https_proxy": "http://proxyhk.zte.com.cn:80",
        "ftp_proxy":  "http://proxyhk.zte.com.cn:80",
        "no_proxy": "::1,10.*.*.*,10.0.0.0/8,10.192.45.187,10.234.68.5,10.30.6.48,10.3.76.100,10.40.13.107,10.40.66.240,10.41.13.247,10.54.12.47,10.54.20.104,10.54.20.61,10.54.20.73,10.54.20.99,10.57.163.170,10.88.138.100,10.88.138.8,10.88.40.91,10.88.98.10,127.0.0.0/8,gerrit.zte.com.cn,gitlab.zte.com.cn,localhost,nsdlmirrors.zte.com.cn,*.sanechips.com.cn,.sanechips.com.cn,sanechips.com.cn,*.xydigit.com,.xydigit.com,xydigit.com,*.zte.com.cn,.zte.com.cn,zte.com.cn,*zte.intra,zte.intra",
    })
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "server", "graphdb", "stdio"],
        env=mcp_env,
        cwd=GRAPHDB_ROOT
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as mcp_client:
            # 初始化LLM客户端，使用通义千问模型
            llm_client = LLMClient(
                model_name='nebulacoder-lite-v7.0',
                api_key='10243863',
                url='http://nebulacoder.dev.zte.com.cn:40081/v1'
            )

            # 获取可用工具列表并格式化为系统提示的一部分
            await mcp_client.initialize()
            tools_result = await mcp_client.list_tools()
            tools = tools_result.tools
            tools_description = json.dumps(
                [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                for t in tools],
                ensure_ascii=False,
                indent=2
            )

            # 启动聊天会话
            chat_session = ChatSession(llm_client=llm_client, mcp_client=mcp_client)
            async for chunk in chat_session.start(tools_description):  # 使用 async for
                print(chunk, end='', flush=True) 

if __name__ == "__main__":
    with clear_proxy():
        asyncio.run(test_Agent_call_demo())