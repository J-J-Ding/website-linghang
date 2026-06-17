import copy
import json
import time
from typing import Generator, List, Dict
from ask_ai_request import Chat_ai_stream
from concurrent.futures import ThreadPoolExecutor
import os
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question, Get_file_from_server, Replace_icenter

class CodeModule:
    SYSTEM_PROMPT = """# Persona（角色）：
你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范，负责维护{module_name}。

# Task（任务）：
你可以回答用户提出的所有针对{module_name}的问题，也可以针对用户提出的需求对模块码进行修改，如果是咨询，可以直接回答，如何是需求变更，先给出变更修改的代码，然后给出本次修改涉及的所有修改点的修改要点、波及分析、风险分析，使用表格形式输出。

# Context（上下文）：
## 这是模块描述
{module_design}

## 这是相关的核心代码：
{module_code}

## 注意事项：
1、如果没有获取到核心代码文件内容，请不要臆想和猜测，如实回答未获取到代码内容。
2、修改的代码尽量使用现有代码的风格。"""

    def __init__(self, data: Dict):
        try:
            code_server = "http://" + data.get('server', '0.0.0.0') + ":4001/read"
            module_files = data.get('file', '未知文件')
            module_name = data.get('component', '未知模块')
            module_description = data.get('description', '未知描述')

            # 打印提取的context内容
            print("\n===== 提取的context内容 =====")
            print(f"组件名称: {module_name}")
            print(f"组件描述: {module_description}")
            print(f"组件文件: {module_files}")
            print(f"代码服务器: {code_server}")
            print("=============================\n")

            module_design = Replace_icenter(module_description)
            module_code = self.read_files(code_server, module_files)
        except Exception as e:
            print(f"\n处理context时发生错误: {str(e)}\n")
            module_name = "未知模块"
            module_design = "未知描述"
            module_code = "文件列表获取失败"

        self.module_name = module_name
        self.module_design = module_design
        self.module_code = module_code

    def get_system_prompt(self):
        return self.SYSTEM_PROMPT.format(module_name=self.module_name, module_design=self.module_design, module_code=self.module_code)

    def read_files(self, code_server, files):
        # 逐个获取文件内容
        file_contents = []
        total_bytes = 0  # 用于统计总字节数

        try:
            # 分割字符串并过滤空值
            files_array = [file.strip() for file in files.split('\n') if file.strip()]

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
            return "\n".join(file_contents)
        except Exception as e:
            print(f"\n获取代码文件时发生错误: {str(e)}\n")
            return "文件列表获取失败"

    def run(self, messages=None, model: str = "nebula"):
        if messages is None:
            messages = [{"role": "system", "content": self.get_system_prompt()}, {"role": "user", "content": "请介绍一下你自己"}]
        for chunk in Chat_ai_stream(messages, model):
            yield chunk

    def run_once(self, question, model: str = "nebula"):
        messages = [{"role": "system", "content": self.get_system_prompt()}, {"role": "user", "content": question}]
        answer = ""
        for chunk in self.run(messages, model):
            answer += chunk
        return answer


class CodeComponent:
    SYSTEM_PROMPT = """# Persona（角色）：
你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范，负责维护{component_name}。

# Task（任务）：
你可以回答用户提出的所有针对{component_name}的问题，也可以针对用户提出的需求对模块码进行修改，如果是咨询，可以直接回答，如何是需求变更，先给出变更修改的代码，然后给出本次修改涉及的所有修改点的修改要点、波及分析、风险分析，使用表格形式输出。
# Context（上下文）：
## 这是模块描述
{module_designs}"""

    SPLIT_PROMPT = """# Persona（角色）：
你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范，负责维护{component_name}，当前{component_name}包含的模块有：
{module_designs}
# Task（任务）：
请根据模块的功能，选择回答用户的提问需要用到的模块，并根据模块功能对用户问题进行针对性的修改，更符合模块的具体功能，参考输出格式以json的形式给出回复，不要包含任何格式标记（包括```、json等）。

# 输出格式
[{{"name":"模块名称1", "question":"子问题1"}}，{{"name":"模块名称2", "question":"子问题2"}}]"""

    QUESTION_PROMPT = """# Context（上下文）
## 问题涉及的模块
{modules}

{answer}
# 用户提问
{question}"""

    def __init__(self, name, module_datas: List):
        self.component_name = name
        self.module_infos = {}
        for module_data in module_datas:
            code_module = CodeModule(module_data)
            if code_module.module_name and code_module.module_name != "未知模块":
                self.module_infos[code_module.module_name] = {"module_design": code_module.module_design, "module_agent": code_module}

    def get_module_design(self):
        infos = []
        for index, (key, info) in enumerate(self.module_infos.items()):
            infos.append(f"{index + 1}.{key}:{info['module_design']}")
        return "\n".join(infos)

    def get_system_prompt(self):
        return self.SYSTEM_PROMPT.format(component_name=self.component_name, module_designs=self.get_module_design())

    def question_split(self, question, model: str = "nebula"):
        prompt = self.SPLIT_PROMPT.format(component_name=self.component_name, module_designs=self.get_module_design())
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        answer = ""
        for chunk in Chat_ai_stream(messages, model):
            answer += chunk
        print(answer)
        return json.loads(answer)

    # 定义一个包装函数，以便在ThreadPoolExecutor中使用
    def run_module(self, module_name, question, model):
        return module_name, self.module_infos[module_name]["module_agent"].run_once(question, model)

    def ask_module(self, module_questions, model):
        num = len(module_questions)
        with ThreadPoolExecutor(max_workers=num) as executor:
            # 提交任务给线程池
            futures = [executor.submit(self.run_module, module_question["name"], module_question["question"], model) for module_question in module_questions]

            # 等待所有任务完成并获取结果
            results = [future.result() for future in futures]
        return results

    def run(self, messages=None, model: str = "nebula"):
        if messages is None:
            messages = []
        question = messages[-1]["content"]
        module_questions = self.question_split(question, model)
        module_answers = self.ask_module(module_questions, model)

        info = []
        answer = []
        for index, module_answer in enumerate(module_answers):
            module_name = module_answer[0]
            answer.append(f"## {module_name}模块回复\n{module_answer[1]}")
            info.append(f"{index + 1}.{module_name}:{self.module_infos[module_name]['module_design']}")

        messages[-1]["content"] = self.QUESTION_PROMPT.format(modules="\n".join(info), answer="\n".join(answer), question=question)

        for chunk in Chat_ai_stream(messages, model):
            yield chunk


def Agent_ai_component_new(messages: list = [], config: dict = {}, model: str = "qwen") -> Generator[str, None, None]:
    context = {
        'component': 'PORT组件',
        'context': [
            {
                "component": "PORT组件-端口初始化模块",
                "description": "",
                "server": "10.90.204.255",
                "file": "L2/plat/port/inc/sspPortInit.h\n  L2/plat/port/src/sspPortInit.c"
            },
            {
                "component": "PORT组件-端口配置模块",
                "description": "",
                "server": "10.90.204.255",
                "file": "L2/plat/port/inc/sspPortApi.h\n L2/plat/port/src/sspPortApi.c"
            },
            # {
            #     "component": "PORT组件-端口信息同步模块",
            #     "description": "",
            #     "server": "10.90.204.255",
            #     "file": "L2/plat/port/inc/sspPortSync.h\n L2/plat/port/src/sspPortSync.c"
            # },
            # {
            #     "component": "PORT组件-端口Link事件模块",
            #     "description": "",
            #     "server": "10.90.204.255",
            #     "file": "L2/plat/port/inc/sspPortLink.h\n L2/plat/port/src/sspPortLink.c"
            # }
        ]
    }

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        print(config)

        # 提取并打印context中的内容
        try:
            # 从config中获取context字符串
            context_data = context.get("context", "[]")
            component_name = context.get("component", "未知组件")

            # context_str = config.get("context", "[]")
            # component_name = config.get("component", "未知组件")
            # 解析JSON字符串为字典
            # context_data = json.loads(context_str)

            if len(context_data) == 1:
                code_module = CodeModule(context_data[0])
                system_prompt = code_module.get_system_prompt().strip()
            elif len(context_data) > 1:
                code_component = CodeComponent(component_name, context_data)
                system_prompt = code_component.get_system_prompt().strip()
            else:
                raise Exception("context为空，初始化组件/模块智能体失败")

        except json.JSONDecodeError as e:
            print(f"\n解析context失败: {str(e)}")
            print(f"原始context内容: {config.get('context', '空')}\n")
            module_name = "未知模块"
            module_design = "未知描述"
            module_code = "文件列表获取失败"
            system_prompt = CodeModule.SYSTEM_PROMPT.format(module_name=module_name, module_design=module_design,
                                                               module_code=module_code)
        except Exception as e:
            print(f"\n处理context时发生错误: {str(e)}\n")
            module_name = "未知模块"
            module_design = "未知描述"
            module_code = "文件列表获取失败"
            system_prompt = CodeModule.SYSTEM_PROMPT.format(module_name=module_name, module_design=module_design,
                                                            module_code=module_code)

        yield system_prompt.strip()
        return

    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]
    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    # 从config中获取context字符串
    context_data = context.get("context", "[]")
    component_name = context.get("component", "未知组件")
    # context_str = config.get("context", "[]")
    # component_name = config.get("component", "未知组件")
    # 解析JSON字符串为字典
    # context_data = json.loads(context_str)

    if len(context_data) <= 1:
        code_module = CodeModule(context_data[0])
        for chunk in code_module.run(messages, "nebula"):
            yield chunk
    else:
        code_component = CodeComponent(component_name, context_data)
        for chunk in code_component.run(messages, model):
            yield chunk


def Agent_ai_board(messages: list = [], config: dict = {}) -> Generator[str, None, None]:
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        # 提取并打印context中的内容
        try:
            # 从config中获取context字符串
            context_str = config.get("context", "{}")
            # 解析JSON字符串为字典
            context_data = json.loads(context_str)
            
                      
        except json.JSONDecodeError as e:
            print(f"解析context失败: {str(e)}")
            print(f"原始context内容: {config.get('context', '空')}\n")
        except Exception as e:
            print(f"处理context时发生错误: {str(e)}\n")

        system_prompt = f"""
            # Persona（角色）：
            你是一个专业的助手。

            # Task（任务）：
            你可以回答用户提出的任何问题。

            # Context（上下文）：
            这是你当前掌握的一些信息，你可以根据用户提出的问题，选择是否使用这些信息回答相关的问题。
            {context_data}
            """

        yield system_prompt.strip()
        return

    context = {'component': 'PORT组件', 'context': '[{"component":"PORT组件-端口初始化模块","description":"","server":"10.90.204.255","file":"L2/plat/port/inc/sspPortInit.h\\n  L2/plat/port/src/sspPortInit.c"},{"component":"PORT组件-端口配置模块","description":"https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/7d61b4e46ed511f0b0a0092e8c89e184/view","server":"10.90.204.255","file":"L2/plat/port/inc/sspPortApi.hc\\nL2/plat/port/src/sspPortApi.c"}]'}

    for chunk in Agent_ai_component_new(messages, context):
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
    config = {'component': 'PORT组件', 'context': '[{"component":"PORT组件-端口初始化模块","description":"","server":"10.90.204.255","file":"L2/plat/port/inc/sspPortInit.h\\n  L2/plat/port/src/sspPortInit.c"},{"component":"PORT组件-端口配置模块","description":"https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/7d61b4e46ed511f0b0a0092e8c89e184/view","server":"10.90.204.255","file":"L2/plat/port/inc/sspPortApi.hc\\nL2/plat/port/src/sspPortApi.c"}]'}

    try:
        for chunk in Agent_ai_component_new(messages, config, model):
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

    print("-----多轮问答(流式)-----")
    prompt = Agent_call_demo(None, "nebula")
    messages.append({"role": "system", "content": prompt})
    messages.append({"role": "user", "content": "组件有多少模块，分别什么功能"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})
    # messages.append({"role": "user", "content": "每个模块定义了多少函数，分别是什么"})
    messages.append({"role": "user", "content": "我需要修改端口支持的数量，需要修改哪些模块"})
    # messages.append({"role": "user", "content": "客户侧端口从20个增加到60个，应该怎么修改"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    test_Agent_call_demo()