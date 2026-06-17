import re
import time
import json
from datetime import datetime
from typing import Generator, List
from dataclasses import dataclass
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question
from agent_base import MessageDict, ConfigDict
from api_data import TOOL_Table_get

# 定义映射关系表
KNOWLEDGE_MAP = {
    'CodingStandards': "https://i.zte.com.cn/index/ispace/#/space/c72da2d6076d4eb9838129067ae770a9/wiki/page/8e31c4382c094f729e4ff1fa3d694713/view",
    'CodingBugCases': """https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/f3dd24f2505b442d89b73fd88ae789a6/view,
                         https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/8eea261542b049c69afa430807852033/view""",
    'CodingStandardsNasa': "https://i.zte.com.cn/#/shared/0e69ad53585c48c69b427ef6fd3e33da/wiki/page/4ba923b1362842e18652f84c20a76e32/view"
}

# def Agent_basic_chat(messages: List[MessageDict] = [], config: ConfigDict = {}) -> Generator[str, None, None]:
#     return 


def Agent_ai_chat(messages: list = [], config: dict = {}) -> Generator[str, None, None]:
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        # 提取并打印context中的内容
        try:
            # 从config中获取context字符串
            context_str = config.get("context", "{}")
            # 解析JSON字符串为字典
            context_data = json.loads(context_str)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"解析context失败: {str(e)}")
            print(f"原始context内容: {config.get('context', '空')}")
            context_data = {}
        except Exception as e:
            print(f"处理context时发生错误: {str(e)}")
            context_data = {}

        # 提取context_data中的链接地址，如：https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/b1e5b7c38e1311f0b38c8f6255d8de76/view
        context_data_link = ''
        context_data_link_content = ''

        try:
            url_match = re.search(r"https://i\.zte\.com\.cn/[^\s<>\"']*", json.dumps(context_data, ensure_ascii=False))
            if url_match:
                context_data_link = url_match.group(0)
                context_data_link_content = Replace_question(context_data_link, matches)
        except Exception as e:
            print(f"提取链接内容失败: {str(e)}")
            print(f"原始context_data内容: {context_data}")
            context_data_link = ''
            context_data_link_content = ''

        # 获取通识类知识
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        knowledge_type = config.get('knowledge', '')
        knowledge_result = TOOL_Table_get(knowledge_type)
        
        # 从TOOL_Table_get的返回结果中提取数据
        if knowledge_result and knowledge_result.get('status') == 'success':
            knowledge_content = knowledge_result.get('data', [])
            # 将数据转换为字符串格式以便在系统提示中使用
            knowledge_content = str(knowledge_content) if knowledge_content else "无"
        else:
            knowledge_content = "无"

        system_prompt = f"""
            # Persona（角色）：
            你是一个专业的助手。

            # Task（任务）：
            你可以回答用户提出的任何问题。

            # Context（通识知识）
            这是你掌握的通识类知识，可以帮助你了解一些基础信息
            1. 当前时间：{current_time}
            2. 通识知识：{knowledge_content}
            
            # Context（私域知识）：
            这是你当前掌握的一些私有信息，你可以根据用户提出的问题，选择是否使用这些信息回答相关的问题。
            {context_data}

            ## 一些更加详细的链接内容：
            ### {context_data_link}
            #### {context_data_link_content}

            # 注意事项：
            1. 当回答时引用了图片链接，可以直接使用markdown格式输出，这样就可以在前端渲染出来。
            2. 不知道的信息，禁止捏造事实和随意回答，要确保回答的内容都是你确实掌握的信息。
            """
        yield system_prompt.strip()
        return

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, "nebula"):
        yield chunk


# 挂接文档知识的智能体
def Agent_ai_chat_doc(messages: list = [], config: str = '', model: str = "nebula") -> Generator[str, None, None]:
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    knowledge = Replace_question(KNOWLEDGE_MAP[config], matches)

    system_prompt = f"""
        # Persona（角色）：
        你是一名专业的AI助手，能够根据自己掌握的知识回答客户提出的问题。

        # Task（任务）：
        对用户提出的问题进行回答，请注意要根据自己的知识上下文回答，如何涉及到不是知识范畴内的问题，尽量不要胡乱回答，避免幻觉。

        # Context（知识上下文）：
        {knowledge}

        # Format（格式）：
        先简单使用一句话概括你所具有的知识上下文，然后再根据用户提出的问题，给出专业的回答。
    """

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, model):
        yield chunk

# 挂接知识库的智能体
def Agent_ai_chat_rag(messages: list = [], config: str = '', model: str = "nebula") -> Generator[str, None, None]:
    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    knowledge = Replace_question(KNOWLEDGE_MAP[config], matches)

    system_prompt = f"""
        # Persona（角色）：
        你是一位拥有10年代码审查经验的资深架构师，精通C/C++编程语言的编码规范。

        # Task（任务）：
        对提交的代码进行全面的规范符合性审查，并提供可操作的改进建议。对没有问题和不涉及的规范项标记✔️，对违反编码规范的地方标记❌，并给出具体的问题代码和修改建议代码对比。

        # Context（上下文）：
        ## 这是具体的编码规范要求：
        {knowledge}

        # Format（格式）：
        输出时请逐项对编码规范做检查，使用如下格式：
        ✅【没问题】1. 指针使用规范。
        ✅【不涉及】2. 动态内存使用规范。
        ❌【有问题】3. 返回值使用规范。
        问题代码：（具体问题描述）
        xxxx code
        修改建议：
        xxxx code

        总结：违反规范1条，符合规范12条。

        # 附加功能：
        支持交互式追问特定规范细节
        对争议性问题标注"规范灰色地带"说明
        如未提供代码可以提示贴上代码，不需要过多回复
    """

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 默认支持icenter和rdc解析能力
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    for chunk in Chat_ai_stream(messages, model):
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
        for chunk in Agent_ai_chat_doc(messages, model):
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

    #初始化一个会话session
    Agent_call_demo()
    
    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"你好"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})
    
    messages.append({"role": "user", "content":"第二高的呢？"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    messages.append({"role": "user", "content":"第三高的呢？"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

if __name__ == "__main__":    
    test_Agent_call_demo()
