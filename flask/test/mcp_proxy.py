import asyncio
import requests
import time
import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
from fastmcp import Client
import httpx
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import load_yaml_config, app_logger
import ast
import json
import os
import hashlib

class MCPLLMClient:
    """LLM 客户端，负责与大语言模型 API 通信"""
    def __init__(self, config: Dict) -> None:
        self.model_name = config.get("model_name", "nebulacoder-lite-v7.0")
        self.api_key = config.get("api_key", "10316690")
        self.url = config.get("url", "http://nebulacoder.dev.zte.com.cn:40081/v1/chat/completions")
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 8192)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Emp-No": config.get("emp_no", "10316690"),
            "X-Auth-Value": config.get("auth_value", "252653bbe93098cb76207b22a7365a94")
        }

        self.system_prompt = """You are an AI assistant that helps users by analyzing their requests and identifying appropriate tools. Your task is to identify both the SERVER (platform/service domain) and the specific TOOL (operation type + target) that would best address the user's request.

When a user asks you to perform a task, you should:
1. Carefully read and understand the user's request
2. Identify the key requirements and intentions in the request
3. Determine whether you need to use the tool to answer the user's question. If not, return directly to the default setting. If you need to use the tool, see the following steps.
4. Determine the information of the server from user's request (SERVER)
5. Determine what specific tool from user's request (TOOL)
6. Respond using ONLY the following format:

<tool_assistant>
server: [brief description of the server/platform from user's request]
tool: [brief description of the specific tool from user's request]
</tool_assistant>

Your response should be concise but descriptive.
If you think you don't need to use tools, just reply "No tools needed"
Otherwise, remember to ONLY provide the server and tool descriptions within the <tool_assistant> tags. 
DO NOT provide any additional explanation or commentary outside the <tool_assistant> tags. 
"""

        self.system_prompt = """You are an AI assistant that identifies tools to fulfill user requests. Follow these steps:

1. Analyze the request to determine if an external tool is required. If not, respond: "No tools needed".
2. If a tool is needed, respond ONLY in this format:

<tool_assistant>
server: [brief description of the server/platform from user's request]
tool: [brief description of the specific tool from user's request]
</tool_assistant>

DO NOT add any extra text outside the tags.
"""

    def _force_system_prompt(self, messages: List[Dict[str, str]], system_prompt: Optional[str]) -> List[Dict[str, str]]:
        """强制设置系统提示词（替换首个或追加）"""
        if not system_prompt:
            return messages.copy()
        
        # 深拷贝避免修改原数据
        new_msgs = [msg.copy() for msg in messages]
        
        if new_msgs and new_msgs[0]["role"] == "system":
            # 替换首个系统消息
            new_msgs[0]["content"] = system_prompt
        else:
            # 在开头插入新系统消息
            new_msgs.insert(0, {"role": "system", "content": system_prompt})
        
        return new_msgs

    def get_response(self, messages: List[Dict], tools: Optional[List] = None, retries: int = 3) -> Dict:
        """向 LLM 发送消息并获取响应，支持重试"""

        processed_msgs = self._force_system_prompt(messages, self.system_prompt)

        payload = {
            "model": self.model_name,
            "messages": processed_msgs,
            "stream": False,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools

        # app_logger.info("==="*50)
        # app_logger.info(messages[-1])

        for attempt in range(retries):
            try:
                response = requests.post(
                    url=self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )
                response.raise_for_status()
                response_data = response.json()

                if response.status_code == 200:
                    app_logger.info("==="*50)
                    app_logger.info(response_data["choices"][0]["message"])

                    return response_data["choices"][0]["message"]
                else:
                    raise Exception(f"LLM API 请求失败：{response_data}")
            except Exception as e:
                app_logger.info(f"LLM API 请求失败（尝试 {attempt + 1}/{retries}）：{str(e)}")
                if attempt == retries - 1:
                    return {}
                time.sleep(2 ** attempt)  # 指数退避
        return {}


class MCPProxy:
    """管理多个 MCP 服务器的客户端"""
    def __init__(self, config_dict: Dict):

        self.server_configs = load_yaml_config(config_dict.get("mcp_server_config", "")).get("servers", [])
        self.llm_client = MCPLLMClient({})

        self.active_servers_list = []  # 存储活跃服务器
        self.tools = []  # 存储所有活跃服务器的唯一工具集合

        self.tools_lock = asyncio.Lock()  # 保护 self.tools 的异步锁
        self.config_lock = asyncio.Lock()  # 保护配置更新的异步锁
        self.config_dict = config_dict
        self.config_files = {
            "servers": {"path": config_dict.get("mcp_server_config", ""), "hash": "", "data": self.server_configs},
        }

        self.top_servers = 3  # 检索到的服务器
        self.top_tools = 2  # 检索到的工具
        self.tool_assistant_pattern = re.compile(
            r'<tool_assistant>\s*server:\s*(.*?)\s*tool:\s*(.*?)\s*</tool_assistant>',
            re.DOTALL
        )

        asyncio.create_task(self.sniff_servers_background())
        asyncio.create_task(self.update_configs())


    async def update_configs(self):
        """初始化和定期更新配置文件"""
        while True:
            try:
                async with self.config_lock:
                    for config_name, config_info in self.config_files.items():
                        file_path = config_info["path"]
                        if not os.path.exists(file_path):
                            app_logger.info(f"配置文件 {file_path} 不存在，跳过检查")
                            continue

                        with open(file_path, "rb") as f:
                            content = f.read()
                            current_hash = hashlib.sha256(content).hexdigest()

                        if current_hash != config_info["hash"]:
                            app_logger.info(f"检测到 {file_path} 变化，加载配置")
                            new_config = load_yaml_config(file_path)
                            if new_config:
                                if config_name == "servers":
                                    old_servers = {s["transport"] for s in self.config_files["servers"]["data"]}
                                    new_servers = {s["transport"] for s in new_config.get("servers", [])}
                                    removed_servers = old_servers - new_servers
                                    added_servers = new_servers - old_servers

                                    async with self.tools_lock:
                                        for server in removed_servers:
                                            if any(s["transport"] == server for s in self.active_servers_list):
                                                self.tools = [tool for tool in self.tools if tool["server_transport"] != server]
                                                self.active_servers_list = [s for s in self.active_servers_list if s["transport"] != server]
                                                app_logger.info(f"移除服务器 {server} 的工具和活跃状态")

                                    self.config_files["servers"]["data"] = new_config.get("servers", [])
                                    self.server_configs = new_config.get("servers", [])
                                    app_logger.info(f"工具服务器配置更新：新增 {added_servers}, 移除 {removed_servers}")

                                config_info["hash"] = current_hash
                            else:
                                app_logger.info(f"加载 {file_path} 失败，保留原有配置")
            except Exception as e:
                app_logger.info(f"检查配置文件时发生错误：{str(e)}")

            await asyncio.sleep(30)  # 每 30 秒检查一次

    async def get_server_tools(self, server: Dict) -> List[Dict]:
        """获取服务器工具列表并转换为 OpenAI 格式"""
        try:
            # 只传递 transport 参数给 Client，避免不支持的参数
            client_params = {"transport": server["transport"]}
            async with Client(**client_params) as mcp_client:
                server_tools = await mcp_client.list_tools()
                server_tool_dicts = [tool.__dict__ for tool in server_tools]
                server_tool_strings = [str(t) for t in server_tool_dicts]
                openai_tools = self.convert_tools_to_openai_format(server_tool_strings)
                # 为工具添加来源服务器标识
                for tool in openai_tools:
                    tool["server_transport"] = server["transport"]
                    tool["description_embedding"] = self.get_embedding(tool["function"]["description"])

                return openai_tools
        except Exception as e:
            raise

    async def filter_internal_duplicates(self, tools: List[Dict], server_transport: str) -> Tuple[List[Dict], List[str]]:
        """过滤服务器内部重复工具，保留第一个"""
        server_tool_names = set()
        unique_tools = []
        internal_conflicting_tools = []
        for tool in tools:
            tool_name = tool["function"]["name"]
            if tool_name in server_tool_names:
                internal_conflicting_tools.append(tool_name)
            else:
                server_tool_names.add(tool_name)
                unique_tools.append(tool)
        if internal_conflicting_tools:
            app_logger.info(f"服务器 {server_transport} 内部重复工具 {', '.join(internal_conflicting_tools)} 被移除，仅保留第一个")
        return unique_tools

    async def check_cross_server_conflicts(self, tools: List[Dict], server_transport: str) -> Tuple[List[Dict], List[str]]:
        """检查跨服务器工具冲突，排除当前服务器的旧工具"""
        async with self.tools_lock:
            existing_tool_names = {tool["function"]["name"] for tool in self.tools if tool["server_transport"] != server_transport}
        non_conflicting_tools = []
        conflicting_tools = []
        for tool in tools:
            tool_name = tool["function"]["name"]
            if tool_name in existing_tool_names:
                conflicting_tools.append(tool_name)
            else:
                non_conflicting_tools.append(tool)
        if conflicting_tools:
            app_logger.info(f"服务器 {server_transport} 的工具 {', '.join(conflicting_tools)} 因与其他服务器工具冲突被移除")
        return non_conflicting_tools

    async def update_tools_incrementally(self, server: Dict, new_tools: List[Dict]) -> Tuple[List[str], List[str], List[str]]:
        """增量更新工具链：新增、移除或更新工具"""
        async with self.tools_lock:
            old_server_tools = [tool for tool in self.tools if tool["server_transport"] == server["transport"]]
            old_tool_names = {tool["function"]["name"] for tool in old_server_tools}
            new_tool_names = {tool["function"]["name"] for tool in new_tools}

            added_tools = []
            removed_tools = []
            updated_tools = []

            # 移除已删除的工具
            for old_tool in old_server_tools:
                if old_tool["function"]["name"] not in new_tool_names:
                    self.tools.remove(old_tool)
                    removed_tools.append(old_tool["function"]["name"])

            # 添加新工具或更新现有工具
            for new_tool in new_tools:
                tool_name = new_tool["function"]["name"]
                if tool_name not in old_tool_names:
                    self.tools.append(new_tool)
                    added_tools.append(tool_name)
                else:
                    old_tool = next((t for t in old_server_tools if t["function"]["name"] == tool_name), None)
                    if old_tool and old_tool["function"] != new_tool["function"]:
                        self.tools.remove(old_tool)
                        self.tools.append(new_tool)
                        updated_tools.append(tool_name)

            return added_tools, removed_tools, updated_tools

    async def sniff_servers(self) -> bool:
        """嗅探 MCP 服务器，尝试连接并同步更新工具链"""
        found_new_server = False

        for server in self.server_configs:
            try:
                # 获取服务器工具
                openai_tools = await self.get_server_tools(server)

                # 过滤服务器内部重复工具
                unique_tools = await self.filter_internal_duplicates(openai_tools, server["transport"])

                # 检查跨服务器工具冲突
                non_conflicting_tools = await self.check_cross_server_conflicts(unique_tools, server["transport"])

                # 更新工具链
                old_tool_count = len(self.tools)
                if server in self.active_servers_list:
                    # 更新活跃服务器的工具
                    added_tools, removed_tools, updated_tools = await self.update_tools_incrementally(server, non_conflicting_tools)
                    if added_tools or removed_tools or updated_tools:
                        app_logger.info(f"服务器 {server['transport']} 工具更新：新增 {len(added_tools)} 个工具 {added_tools}, 移除 {len(removed_tools)} 个工具 {removed_tools}, 更新 {len(updated_tools)} 个工具 {updated_tools}, 工具数量从 {old_tool_count} 变更为 {len(self.tools)}")

                else:
                    # 新服务器：添加非冲突工具并标记为活跃
                    async with self.tools_lock:
                        server["description_embedding"] = self.get_embedding(server["description"])
                        self.active_servers_list.append(server)

                        self.tools.extend(non_conflicting_tools)
                    added_tools = [tool["function"]["name"] for tool in non_conflicting_tools]
                    app_logger.info(f"成功连接到 MCP 服务器：{server['transport']} ({server.get('description', '无描述')})，新增 {len(non_conflicting_tools)} 个非冲突工具 {added_tools}")
                    found_new_server = True

            except Exception as e:
                if server in self.active_servers_list:
                    # 活跃服务器断开连接，移除并更新工具链
                    async with self.tools_lock:
                        removed_tools = [tool["function"]["name"] for tool in self.tools if tool["server_transport"] == server["transport"]]
                        self.tools = [tool for tool in self.tools if tool["server_transport"] != server["transport"]]
                        self.active_servers_list.remove(server)
                    app_logger.info(f"服务器 {server['transport']} 断开连接，从活跃列表移除：{str(e)}")
                    app_logger.info(f"工具链更新，移除 {len(removed_tools)} 个工具 {removed_tools}, 当前工具数量：{len(self.tools)}")
                else:
                    app_logger.info(f"MCP 服务器 {server['transport']} 不可用：{str(e)}")

        return found_new_server

    async def sniff_servers_background(self):
        """后台定期嗅探服务器"""
        while True:
            await self.sniff_servers()
            await asyncio.sleep(60)


    def convert_tools_to_openai_format(self, tools_list: List[str]) -> List[Dict]:
        """
        将fastmcp工具列表转换为OpenAI标准的function call格式
        参数:tools_list: 工具列表，每个工具是字符串化的字典
        返回:符合OpenAI标准的工具列表
        """
        openai_tools = []
        for tool_str in tools_list:
            try:
                tool_dict = ast.literal_eval(tool_str)
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_dict.get("name", ""),
                        "description": tool_dict.get("description", "").replace("\\n", "\n").strip(),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                if "inputSchema" in tool_dict and isinstance(tool_dict["inputSchema"], dict):
                    schema = tool_dict["inputSchema"]
                    if "properties" in schema:
                        openai_tool["function"]["parameters"]["properties"] = schema["properties"]
                    if "required" in schema:
                        openai_tool["function"]["parameters"]["required"] = schema["required"]
                openai_tools.append(openai_tool)
            except (SyntaxError, ValueError) as e:
                app_logger.info(f"Error converting tool: {tool_str}. Error: {e}")
                continue
        return openai_tools

   
    def extract_tool_assistant(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract the tool assistant tag content from the text
        
        Args:
            text: The input text
        
        Returns:
            The extracted server and tool descriptions, or None, None if not found
        """
        match = self.tool_assistant_pattern.search(text)
        if match:
            server_desc = match.group(1).strip()
            tool_desc = match.group(2).strip()
            return server_desc, tool_desc
        return None, None
    
    def get_embedding(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """
        Get the embedding of the text
        
        Args:
            text: The input text
            max_retries: The maximum number of retries
        
        Returns:
            The embedding of the text, or None if failed
        """
        if not text.strip():
            return np.zeros(512)

        headers = {
            'Authorization': 'RAN-LL-23cb52a9-41d8-46e5-9b20-75c4f3805b4d',
            'Content-Type': 'application/json'
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'http://10.207.76.177:31074/v1/embeddings',
                    headers=headers,
                    json={"model": 'bge-m3', "input": text.strip()},
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()['data'][0]['embedding']
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff strategy
                    print(f"Error getting embedding, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to get embedding after {max_retries} attempts: {e}")
                    return np.zeros(512)
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate the cosine similarity between two vectors
        
        Args:
            vec1: The first vector
            vec2: The second vector
        
        Returns:
            The cosine similarity, ranging from [-1, 1], the closer to 1 the more similar
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Avoid division by zero errors caused by zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def match_servers(self, server_desc: str) -> List[Dict[str, Any]]:
        """
        Match the most relevant servers based on the server description
        
        Args:
            server_desc: The server description
        
        Returns:
            The top_servers servers, sorted by similarity in descending order
        """
        if not self.active_servers_list:
            raise ValueError("No server data loaded.")
        
        # Get the query embedding
        query_embedding = self.get_embedding(server_desc)
        if not query_embedding:
            raise ValueError("Failed to get embedding for server description")
        
        # Calculate the description similarity for each server
        server_scores = []
        for server in self.active_servers_list:
            # First check if the server has a description embedding
            if "description_embedding" not in server:
                continue
            
            # Calculate the description similarity
            desc_similarity = self.cosine_similarity(
                query_embedding, 
                server["description_embedding"]
            )
            
            # If there is a summary embedding, also calculate the summary similarity
            summary_similarity = 0
            if "summary_embedding" in server:
                summary_similarity = self.cosine_similarity(
                    query_embedding, 
                    server["summary_embedding"]
                )
            
            # Take the maximum of the description and summary similarities as the final score
            final_score = max(desc_similarity, summary_similarity)
            
            server_scores.append({
                "server": {k: v for k, v in server.items() if k != "description_embedding"} ,
                "score": final_score
            })
        
        # Sort by similarity in descending order
        server_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Return the top_servers servers with the highest scores
        return server_scores[:self.top_servers]
    
    def match_tools(self, server_list: List[Dict[str, Any]], tool_desc: str) -> List[Dict[str, Any]]:
        """
        Find the most matching tools in the filtered servers
        
        Args:
            server_list: The list of servers
            tool_desc: The tool description
        
        Returns:
            The top_tools tools, sorted by similarity in descending order
        """
        # Get the query embedding
        query_embedding = self.get_embedding(tool_desc)
        if not query_embedding:
            raise ValueError("Failed to get embedding for tool description")
        
        # Collect all tools and calculate the similarity
        tool_scores = []
        
        for server_info in server_list:

            server = server_info["server"]
            server_score = server_info["score"]

            for tool in self.tools:
                if tool["server_transport"] == server["transport"]:
                    
                    if "description_embedding" not in tool:
                        continue
                    
                    # Calculate the tool description similarity
                    tool_similarity = self.cosine_similarity(
                        query_embedding, 
                        tool["description_embedding"]
                    )
                    
                    # Combine the server score and tool score as the final score
                    final_score = (server_score * tool_similarity) * max(server_score, tool_similarity)
                    if final_score < 50:
                        continue
                    
                    tool_scores.append({
                        "tool_name": tool["function"]["name"],
                        "tool_description": tool["function"]["description"],
                        "tool": {k: v for k, v in tool.items() if k != "description_embedding" and k != "server_transport"}, 
                        "server_score": server_score,
                        "tool_score": tool_similarity,
                        "final_score": final_score
                    })
        
        # Sort by final score in descending order
        tool_scores.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Return the top_tools tools with the highest scores
        return tool_scores[:self.top_tools]


    def retrieve_tools(self, messages: List[Dict]):
        """
        Extract the tool requirement from the input text and match the most relevant tools
        
        Args:
            messages: The message dict
        
        Returns:
            The matching result, containing the matched servers and tools
        """

        llm_response = self.llm_client.get_response(messages, None)

        # Extract the server and tool descriptions from the input
        server_desc, tool_desc = self.extract_tool_assistant(llm_response["content"])
        
        if not server_desc or not tool_desc:
            return {
                "success": False,
                "error": "No tool_assistant tag found or invalid format",
                "matched_servers": [],
                "matched_tools": []
            }
        
        try:
            # First stage: match servers
            matched_servers = self.match_servers(server_desc)
            
            # Second stage: match tools in the filtered servers
            matched_tools = self.match_tools(matched_servers, tool_desc)
            
            return {
                "success": True,
                "server_description": server_desc,
                "tool_description": tool_desc,
                "matched_servers": matched_servers,
                "matched_tools": matched_tools
            }
        except Exception as e:
            app_logger.error(f"Error in retrieve_tools: {e}")
            return {
                "success": False,
                "error": str(e),
                "server_description": server_desc,
                "tool_description": tool_desc,
                "matched_servers": [],
                "matched_tools": []
            }

async def run():
    config_dict = {
        "mcp_server_config": "../config/servers.yaml",
    }

    test = ""
    messages = [{'role':'system', 'content':'hi'},{'role':'user', 'content':'dhcp server最大用户数是如何限制的？'}]

    client_manager = MCPProxy(config_dict)
    await client_manager.sniff_servers()

    print(client_manager.retrieve_tools(messages))

zteproxy = ["https_proxy", "http_proxy", "all_proxy", "no_proxy"]

from contextlib import contextmanager
@contextmanager
def run_without_envs(envs: list = None):
    env_2_remove = envs or []
    env_cache = {env: "" for env in env_2_remove}
    for env in env_2_remove:
        if env in os.environ:
            val = os.environ.pop(env)
            print(f"{env:<20}: {val}")
            env_cache[env] = val
            print(f"{env} has been removed!!")

    try:
        yield
    finally:
        for env,val in env_cache.items():
            if env in os.environ:
                print(f"柱子，你TND打歪了！{env}")
            os.environ[env] = val

if __name__ == "__main__":
    with run_without_envs(zteproxy):
        asyncio.run(run())
