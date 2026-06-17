import os
import time
import json
import inspect
import requests
from typing import Generator, Optional
from flask import request, jsonify
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question, Get_file_from_server, Replace_icenter
from api_data import TOOL_Table_get


def get_messages_bytes(messages):
    """
    计算messages中所有内容的总字节数
    
    Args:
        messages: 可以是字符串列表、字典列表或其他可迭代对象
    
    Returns:
        int: 总字节数
    """
    total_bytes = 0
    
    for item in messages:
        if isinstance(item, str):
            # 如果是字符串，直接编码为字节
            total_bytes += len(item.encode('utf-8'))
        elif isinstance(item, dict):
            # 如果是字典，将所有值转换为字符串后编码
            for value in item.values():
                if isinstance(value, str):
                    total_bytes += len(value.encode('utf-8'))
                else:
                    total_bytes += len(str(value).encode('utf-8'))
        elif isinstance(item, bytes):
            # 如果已经是字节，直接加长度
            total_bytes += len(item)
        else:
            # 其他类型转换为字符串后编码
            total_bytes += len(str(item).encode('utf-8'))
    
    return total_bytes


def API_Component_status_get():
    """
    获取组件状态的 API 接口
    前端传参：{
        "domain": "L2",
        "component": "PORT",
        "description": "端口管理模块",  # ✅ 允许为空字符串 ""
        "code_server": "http://192.168.1.100:4001/read",
        "file_list": "src/port.cpp\\nsrc/port.h"
    }
    """
    try:
        # 获取前端发送的 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求体不能为空"
            }), 400

        # 👇 提取所有 5 个参数
        domain = data.get("domain")
        component = data.get("component")
        description = data.get("description")
        code_server = data.get("code_server")
        file_list = data.get("file_list")

        # 👇 参数校验：domain, component, code_server, file_list 必须非空；description 可空
        required_params = {
            "domain": domain,
            "component": component,
        }

        missing = [k for k, v in required_params.items() if not v]
        if missing:
            return jsonify({
                "status": "error",
                "message": f"缺少必要参数: {missing}"
            }), 400

        print(f"收到组件状态请求 - 领域：{domain}，组件：{component}，描述：{repr(description)}，代码服务器：{code_server}，代码目录：{file_list}")

        # 👇 调用你的计算函数
        status = component_status_get(domain, component, description, code_server, file_list)

        # ✅ 正确从返回值中提取数据（假设 status 是 dict）
        code_size = status.get("code_size", 0)
        description_size = status.get("description_size", 0)
        token_size = status.get("token_size", 0)
        agent_status = status.get("agent_status", "未支持")

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "组件状态获取成功",
            "data": {
                "code_size": code_size,
                "description_size": description_size,
                "token_size": token_size,
                "agent_status": agent_status
            }
        }), 200

    except Exception as e:
        print(f"组件状态接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": f"服务器内部错误: {str(e)}"
        }), 500

def component_status_get(domain: str, component: str, description: str, code_server: str, file_list: str) -> dict:
    """
    根据组件信息获取代码量、描述量、token量和状态

    Args:
        domain (str): 领域（用于日志/扩展）
        component (str): 组件名称
        description (str): 组件描述文本
        code_server (str): 代码服务器地址，如 "http://192.168.1.100:4001/read"
        file_list (str): 文件路径列表，每行一个，如 "src/a.cpp\nsrc/b.h"

    Returns:
        dict: {
            "code_size": int,
            "description_size": int,
            "token_size": int,
            "agent_status": bool
        }
    """
    code_server = "http://" + code_server + ":4001/read"
    code_size = 0
    description_size = len(description.encode('utf-8')) if description else 0
    token_size = 0
    agent_status = "未支持"

    try:
        print(f"📊 开始计算组件指标 - 领域: {domain}, 组件: {component}")
        print(f"📄 描述字节数: {description_size}")
        print(f"🌐 代码服务器: {code_server}")
        print(f"📂 文件列表:\n{file_list}")

        if file_list:
            files_array = [file.strip() for file in file_list.split('\n') if file.strip()]
            for file_path in files_array:
                print(f"正在获取文件: {file_path}")
                content = Get_file_from_server(code_server, file_path)
                if content is not None:
                    content_bytes = len(content.encode('utf-8'))
                    code_size += content_bytes
                    print(f"✅ 获取成功，字节数: {content_bytes}")
                else:
                    print(f"❌ 获取失败: {file_path}")

        print(f"📈 总代码字节数: {code_size}")

        # 计算最终指标
        total_size = code_size + description_size
        token_size = total_size // 3

        # ✅ 根据 file_list 和 code_size 设置 agent_status 字符串
        if not file_list:  # 包括 None、空字符串、纯空白等
            agent_status = "未支持"
        elif code_size > 1000:
            agent_status = "正常"
        else:
            agent_status = "异常"

        print(f"🧮 Token 估算值: {token_size}")
        print(f"🟢 Agent 状态: {agent_status}")

    except Exception as e:
        print(f"⚠️ 计算组件指标时发生错误: {e}")
        # 出错时保持默认值：code_size=0, agent_status=False 等

    return {
        "code_size": code_size,
        "description_size": description_size,
        "token_size": token_size,
        "agent_status": agent_status
    }

def Agent_ai_componentNew(messages: list = [], config: dict = {}) -> Generator[str, None, None]:
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        print(config)

        # # 提取并打印context中的内容
        # try:
        #     context_str = config.get("context", "{}")
            
        #     # 🚨 先直接解析 JSON，不要提前替换 \n
        #     context_data = json.loads(context_str)
        #     context_pe = json.dumps(context_data, ensure_ascii=False, indent=2)
        #     # ✅ 解析成功后，再处理需要换行符的字段
        #     component_files = context_data.get('代码目录', '').replace('\\n', '\n').strip() or '未知文件'
        #     component_name = context_data.get('组件名称', '未知组件').strip() or '未知组件'
        #     component_description = context_data.get('组件描述', '暂无描述').strip() or '暂无描述'
        #     code_server = "http://" + context_data.get('代码服务器', '0.0.0.0') + ":4001/read"

        #     print("\n===== 提取的context内容 =====")
        #     print(f"组件名称: {component_name}")
        #     print(f"组件描述: {component_description}")
        #     print(f"组件文件: {component_files}")
        #     print(f"代码服务器: {code_server}")
        #     print("=============================\n")

        #     component_design = Replace_icenter(component_description)

        #     file_contents = []
        #     total_bytes = 0
        #     files_array = [file.strip() for file in component_files.split('\n') if file.strip()]

        #     for file_path in files_array:
        #         print(f"正在获取文件内容: {file_path}")
        #         content = Get_file_from_server(code_server, file_path)
        #         if content:
        #             content_length = len(content)
        #             total_bytes += content_length
        #             print(f"获取成功！内容字节数: {content_length}")
        #             file_contents.append(content)
        #         else:
        #             file_contents.append(f"### 文件: {file_path}\n[无法获取该文件内容]\n")
        #             print("获取失败！")       

        #     component_code = "\n".join(file_contents)
        #     print(f"所有文件总字节数: {total_bytes}")  
                                    
        # except json.JSONDecodeError as e:
        #     print(f"\n❌ 解析context失败（JSON错误）: {str(e)}")
        #     print(f"原始context内容: {repr(context_str)}\n")
        #     component_code = "文件列表获取失败"
        #     component_name = "未知组件"
        #     component_design = "暂无描述"
        # except Exception as e:
        #     print(f"\n❌ 处理context时发生错误: {str(e)}\n")
        #     component_code = "文件列表获取失败"
        #     component_name = "未知组件"
        #     component_design = "暂无描述"


        context_str = config.get("context", "{}")
        context_data = json.loads(context_str)
        # 判断是单个对象还是对象列表
        if isinstance(context_data, dict):
            context_data = [context_data]
        all_file_contents = []  # 收集所有文件内容
        component_name_list = []
        context_pe_list = []
        component_design_list = []
        total_bytes_all = 0
        for idx, item in enumerate(context_data):
            context_pe = json.dumps(item, ensure_ascii=False, indent=2)
            # 提取字段（每个 item 是一个 dict）
            component_files = item.get('代码目录', '').replace('\\n', '\n').strip() or '未知文件'
            component_name = item.get('组件名称', '未知组件').strip() or '未知组件'
            component_description = item.get('组件描述', '暂无描述').strip() or '暂无描述'
            code_server = "http://" + item.get('代码服务器', '0.0.0.0') + ":4001/read"
            print("\n===== 提取的context内容 =====")
            print(f"组件名称: {component_name}")
            print(f"组件描述: {component_description}")
            print(f"组件文件: {component_files}")
            print(f"代码服务器: {code_server}")
            print("=============================\n")
            component_design = Replace_icenter(component_description)
            component_name_list.append(component_name)
            context_pe_list.append(context_pe)
            component_design_list.append(component_design)
            file_contents = []
            total_bytes = 0
            files_array = [f.strip() for f in component_files.split('\n') if f.strip()]
            for file_path in files_array:
                print(f"正在获取文件内容: {file_path}")
                content = Get_file_from_server(code_server, file_path)
                if content:
                    content_length = len(content)
                    total_bytes += content_length
                    total_bytes_all += content_length
                    print(f"获取成功！内容字节数: {content_length}")
                    file_contents.append(content)
                else:
                    error_msg = f"### 文件: {file_path}\n[无法获取该文件内容]\n"
                    file_contents.append(error_msg)
                    print("获取失败！")
            # 将当前组件的所有文件内容加入总列表
            all_file_contents.extend(file_contents)
            print(f"该组件总字节数: {total_bytes}")
        print(f"\n===== 所有组件处理完成，总字节数: {total_bytes_all} =====\n")
        # 最终合并所有文件内容
        component_code = "\n".join(all_file_contents)
        # 从config中获取知识库类型
        knowledge_type = config.get("knowledge", "")
        knowledge_content = ""
        
        # 根据前端传入的知识库类型，获取知识库信息
        knowledge_type_mapping = {
            '用例库': '用例库', 
            '命令库': '命令库',
            'PHY库': 'PHY库', 
            'FPGA地址库': 'FPGA地址库', 
            '时钟芯片库': '时钟芯片库',
            '交换芯片库': '交换芯片库'
        }
        
        if knowledge_type in knowledge_type_mapping:
            knowledge_name = knowledge_type_mapping[knowledge_type]
            print(f"正在获取知识库: {knowledge_name}")
            
            try:
                # 使用TOOL_Table_get函数获取知识库内容
                knowledge_result = TOOL_Table_get(knowledge_name)
                if knowledge_result["status"] == "success":
                    knowledge_data = knowledge_result["data"]
                    if knowledge_data:
                        # 格式化知识库数据为字符串
                        knowledge_content = f"## {knowledge_name}：\n"
                        for idx, item in enumerate(knowledge_data[:1000]):  # 限制最多10条记录，防止内容过长
                            knowledge_content += f"### 条目 {idx+1}:\n"
                            for key, value in item.items():
                                knowledge_content += f"- {key}: {value}\n"
                            knowledge_content += "\n"
                        print(f"成功获取{len(knowledge_data)}条{knowledge_name}数据")
                    else:
                        knowledge_content = f"## {knowledge_name}：\n未找到相关数据"
                        print(f"{knowledge_name}未找到相关数据")
                else:
                    knowledge_content = f"## {knowledge_name}：\n获取失败：{knowledge_result['message']}"
                    print(f"{knowledge_name}获取失败：{knowledge_result['message']}")
            except Exception as e:
                knowledge_content = f"## {knowledge_name}：\n获取时发生错误：{str(e)}"
                print(f"获取{knowledge_name}时发生错误：{str(e)}")
        else:
            print(f"未知的知识库类型: {knowledge_type}")

        component_name = (",").join(component_name_list)
        context_pe = ("\n").join(context_pe_list)
        component_design = ("\n").join(component_design_list)

        print(type(component_name), type(context_pe), type(component_design), type(component_code))

        system_prompt = f"""
            # Persona（角色）：
            你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范，负责维护{component_name}。

            # Task（任务）：
            你可以回答用户提出的所有针对{component_name}的问题，也可以针对用户提出的需求对模块码进行修改，如果是咨询，可以直接回答，如何是需求变更，先给出变更修改的代码，然后给出本次修改涉及的所有修改点的修改要点、波及分析、风险分析，使用表格形式输出。

            # Context（上下文）：
            ## 这是组件/模块相关信息：
            {context_pe}

            ## 这是组件/模块描述：
            {component_design}

            ## 这是相关的核心代码：
            {component_code}

            ## 这是私有知识库内容：
            {knowledge_content}

            ## 注意事项：
            1、如果没有获取到核心代码文件内容，请不要臆想和猜测，如实回答未获取到代码内容。
            2、修改的代码尽量使用现有代码的风格。
            """

        yield system_prompt.strip()
        return
    
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    
    messages_lens = get_messages_bytes(messages)
    tokens = int(messages_lens / 3)
    if tokens > 256000:
        yield(f"<上下文总token数：{tokens}。注意：大模型上下文窗口256k，超过可能存在截断问题！>")

    for chunk in Chat_ai_stream(messages, messages[-1]["model"]):
        yield chunk


def Agent_ai_component(messages: list = [], config: dict = {}) -> Generator[str, None, None]:
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        print(config)

        # 提取并打印context中的内容
        try:
            # 从config中获取context字符串
            context_str = config.get("context", "{}")
            # 解析JSON字符串为字典
            context_data = json.loads(context_str)
            
            # 获取代码服务器地址
            code_server = "http://" + context_data.get('server', '0.0.0.0') + ":4001/read"
            component_name = context_data.get('component', '未知组件')
            component_description = context_data.get('description', '未知描述')
            component_files = context_data.get('file', '未知文件')

            # 打印提取的context内容
            print("\n===== 提取的context内容 =====")
            print(f"组件名称: {component_name}")
            print(f"组件描述: {component_description}")
            print(f"组件文件: {component_files}")
            print(f"代码服务器: {code_server}")
            print("=============================\n")

            # 解析组件描述内容
            component_design = Replace_icenter(component_description)

            # 逐个获取文件内容
            file_contents = []
            total_bytes = 0  # 用于统计总字节数

            # 分割字符串并过滤空值
            files_array = [file.strip() for file in component_files.split('\n') if file.strip()]

            for file_path in files_array:
                print(f"正在获取文件内容: {file_path}")
                # 调用适配后的get_file_from_server，直接获取字符串内容
                content = Get_file_from_server(code_server, file_path)
                if content:
                    # 计算并打印content的字节数
                    content_length = len(content)
                    total_bytes += content_length  # 累加字节数到总数
                    print(f"获取成功！内容字节数: {content_length}")
                    # 服务端已返回带格式的内容，这里直接添加到结果中
                    # 注意：不再需要额外添加格式标记，避免重复
                    file_contents.append(content)
                else:
                    file_contents.append(f"### 文件: {file_path}\n[无法获取该文件内容]\n")
                    print("获取失败！")       

            # 拼接所有文件内容（服务端已返回带格式的内容）
            component_code = "\n".join(file_contents)
            
            # 打印总字节数统计
            print(f"所有文件总字节数: {total_bytes}")  
                      
        except json.JSONDecodeError as e:
            print(f"\n解析context失败: {str(e)}")
            print(f"原始context内容: {config.get('context', '空')}\n")
            component_code = "文件列表获取失败"
            component_name = "未知组件"
        except Exception as e:
            print(f"\n处理context时发生错误: {str(e)}\n")
            component_code = "文件列表获取失败"
            component_name = "未知组件"

        system_prompt = f"""
            # Persona（角色）：
            你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范，负责维护{component_name}。

            # Task（任务）：
            你可以回答用户提出的所有针对{component_name}的问题，也可以针对用户提出的需求对模块码进行修改，如果是咨询，可以直接回答，如何是需求变更，先给出变更修改的代码，然后给出本次修改涉及的所有修改点的修改要点、波及分析、风险分析，使用表格形式输出。

            # Context（上下文）：
            ## 这是组件/模块描述
            {component_design}

            ## 这是相关的核心代码：
            {component_code}

            ## 注意事项：
            1、如果没有获取到核心代码文件内容，请不要臆想和猜测，如实回答未获取到代码内容。
            2、修改的代码尽量使用现有代码的风格。
            """

        yield system_prompt.strip()
        return
    
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, "nebula"):
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
        for chunk in Agent_ai_component(messages, model):
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

    # 初始化一个会话session

    print("-----多轮问答(流式)-----")
    messages.append({"role": "system", "content": prompt})
    #messages.append({"role": "user", "content": "Port不再支持100M，请删除有关代码"})
    messages.append({"role": "user", "content": "Port需要支持一种新的电模块APTX4869，与普通电模块不通用，请新增代码"})
    #messages.append({"role": "user", "content": "Port以前只支持100M，1000M，10GE，现在还需要支持100G，400G"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})


def test_component_status_get():
    domain = "L2"
    component = "PORT组件"
    description = "你好"
    code_server = "10.90.204.255"
    file_list = "L2/plat/port/src/*"
    status = component_status_get(domain, component, description, code_server, file_list)
    print(status)


def test_knowledge_base():
    """测试知识库功能"""
    print("=== 开始测试知识库功能 ===")
    
    # 测试不同的知识库类型
    knowledge_types = ['ApiKnowledge', 'PhyKnowledge', 'ClockKnowledge', 'SwitchKnowledge']
    
    for knowledge_type in knowledge_types:
        print(f"\n--- 测试知识库类型: {knowledge_type} ---")
        
        # 模拟config参数
        config = {
            "context": "{}",
            "knowledge_type": knowledge_type
        }
        
        # 调用函数获取system_prompt
        try:
            generator = Agent_ai_componentNew(config=config)
            system_prompt = next(generator)
            print(f"成功获取{knowledge_type}的system prompt")
            if "获取失败" in system_prompt or "未找到相关数据" in system_prompt:
                print(f"{knowledge_type} - 可能没有数据或获取失败")
            else:
                print(f"{knowledge_type} - 数据获取成功")
        except Exception as e:
            print(f"获取{knowledge_type}时出错: {str(e)}")


if __name__ == "__main__":
    # test_Agent_call_demo()
    # test_component_status_get()
    test_knowledge_base()