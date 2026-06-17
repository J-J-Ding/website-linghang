import asyncio
import json as json_lib
from openai import OpenAI
from mcp import ClientSession
from typing import List, Dict, Any
from mcp.client.streamable_http import streamablehttp_client


def default_serializer(obj):
    """用于 json.dumps 的 default 参数，安全序列化 Tool 或 Pydantic 对象"""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class LLMClient:
    def __init__(self, model: str, url: str, key: str) -> None:
        self.model_name = model
        self.client = OpenAI(api_key=key, base_url=url)

    def get_response(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content


class FastMCPCompatibleClient:
    tool_cfg_dict = {}
    def __init__(self, mcp_url_list: List[str]):
        self.mcp_url_list = [url.rstrip("/") for url in mcp_url_list]

    def _run_async(self, coro):
        return asyncio.run(coro)

    async def _call_tool_with_url(self, mcp_url: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """尝试对单个 MCP URL 调用工具"""
        try:
            async with streamablehttp_client(mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    if result.content:
                        output = result.content[0].text
                        try:
                            return json_lib.loads(output)
                        except json_lib.JSONDecodeError:
                            return output
                    else:
                        return "无返回内容"
        except Exception as e:
            print(f"MCP {mcp_url} 调用失败: {e}")
            raise


    async def _list_tools_with_url(self, mcp_url: str) -> List[Dict[str, Any]]:
        """尝试从单个 MCP URL 获取工具列表"""
        try:
            async with streamablehttp_client(mcp_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    raw_tools = await session.list_tools()
                    processed = []
                    for t in raw_tools:
                        if isinstance(t, (tuple, list)):
                            name = t[0] if len(t) > 0 else ""
                            desc = t[1] if len(t) > 1 else ""
                            schema = t[2] if len(t) > 2 else {}
                        else:
                            name = getattr(t, 'name', str(t))
                            desc = getattr(t, 'description', "")
                            schema = getattr(t, 'input_schema', {})
                        if hasattr(schema, 'model_dump'):
                            schema = schema.model_dump()
                        elif not isinstance(schema, dict):
                            schema = {}
                        processed.append({
                            "name": name,
                            "description": desc,
                            "inputSchema": schema
                        })
                    return processed
        except Exception as e:
            print(f"MCP {mcp_url} 获取工具列表失败: {e}")
            raise


    def list_tools(self) -> List[Dict[str, Any]]:
        """获取所有 MCP 服务的工具列表，并按工具名合并（去重）"""
        merged_tool_dict = {}
        for mcp_url_item in self.mcp_url_list:
            try:
                tool_list = self._run_async(self._list_tools_with_url(mcp_url_item))
                for tool_item in tool_list:
                    name = tool_item.get("name")
                    if name == "tools":
                        merged_tool_dict[mcp_url_item] = tool_item.get("description", [])
                        for merged_tool_dict_value_item in merged_tool_dict[mcp_url_item]:
                            FastMCPCompatibleClient.tool_cfg_dict[merged_tool_dict_value_item.name] = mcp_url_item
                        break
            except Exception as e:
                print(f"警告: 从 MCP {mcp_url_item} 获取工具列表失败: {e}")
        return merged_tool_dict


    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """尝试所有 MCP，调用指定工具（只要有一个 MCP 支持该工具就成功）"""
        last_error = None
        try:
            return self._run_async(self._call_tool_with_url(FastMCPCompatibleClient.tool_cfg_dict.get(tool_name), tool_name, arguments))
        except Exception as e:
            last_error = e
            raise RuntimeError(f"所有 MCP 均无法调用工具 '{tool_name}'。最后错误: {last_error}")


class ChatSession:
    def __init__(self, llm_client: LLMClient, mcp_client: FastMCPCompatibleClient) -> None:
        self.llm_client = llm_client
        self.mcp_client = mcp_client

    def process_llm_response(self, llm_response: str) -> str:
        try:
            if llm_response.startswith("```json"):
                llm_response = llm_response[7:].rstrip("```").strip()
            if llm_response.startswith("["):
                tool_calls = json_lib.loads(llm_response)
                results = []
                for call in tool_calls:
                    if "tool" in call and "arguments" in call:
                        try:
                            result = self.mcp_client.call_tool(call["tool"], call["arguments"])
                            results.append(f"{call['tool']}执行结果: {result}")
                        except Exception as e:
                            results.append(f"{call['tool']}执行错误: {str(e)}")
                return "\n".join(results) if results else llm_response
            else:
                tool_call = json_lib.loads(llm_response)
                if "tool" in tool_call and "arguments" in tool_call:
                    try:
                        result = self.mcp_client.call_tool(tool_call["tool"], tool_call["arguments"])
                        return f"**调用工具**: {result}<br><br>"
                    except Exception as e:
                        return f"**调用工具**: Error executing tool: {str(e)}<br><br>"
                return llm_response
        except json_lib.JSONDecodeError:
            return llm_response