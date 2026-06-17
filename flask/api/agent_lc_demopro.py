#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain AI问答示例
使用 config.json 管理模型配置 - 支持多轮对话和工具调用（流式输出）
"""

import os
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.agents import AgentFinish


def load_config():
    """从 config.json 加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"❌ 配置文件 {config_path} 不存在")
        return {"models": {}, "default_model": ""}
    except json.JSONDecodeError:
        print(f"❌ 配置文件 {config_path} 格式错误")
        return {"models": {}, "default_model": ""}


@tool
def get_current_time() -> str:
    """获取当前系统时间，返回格式化的时间字符串，包括日期和时间。"""
    now = datetime.now()
    return f"当前系统时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')} ({now.strftime('%A')})"


def clear_proxy():
    for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
        os.environ.pop(p, None)


def init_environment():
    clear_proxy()

    """初始化环境"""
    # 加载配置
    config = load_config()
    
    if not config["models"]:
        print("⚠️  没有找到任何模型配置")
        return False
        
    return True


def create_llm_with_tools(model_name="nebula"):
    """创建带有工具的LLM实例"""
    import httpx
    
    # 加载配置
    config = load_config()
    models = config["models"]
    
    # 检查模型配置是否存在
    if model_name not in models:
        print(f"❌ 模型 {model_name} 不存在于配置中")
        print(f"✅ 可用模型: {', '.join(models.keys())}")
        return None
    
    # 检查模型配置是否完整
    model_info = models[model_name]
    if not model_info.get("key") or not model_info.get("url") or not model_info.get("model"):
        print(f"❌ 模型 {model_name} 配置不完整")
        print(f"   KEY: {'✓' if model_info.get('key') else '✗'}")
        print(f"   URL: {'✓' if model_info.get('url') else '✗'}")
        print(f"   MODEL: {'✓' if model_info.get('model') else '✗'}")
        return None
    
    # 从模型配置中获取参数
    api_key = model_info["key"]
    base_url = model_info["url"]
    model = model_info["model"]
    
    # 针对URL进行处理，以适配LangChain要求的格式
    # 通常需要去除具体的端点路径，只保留基础URL
    if "/chat/completions" in base_url:
        base_url = base_url.replace("/chat/completions", "")
    
    # 处理代理设置
    http_client = httpx.Client(
        timeout=60.0,
        # 不设置代理参数，避免socks代理问题
    )

    print(f"🔍 使用API服务: {base_url}")
    print(f"🔑 使用API密钥: {'*' * (len(api_key) - 4) + api_key[-4:]}")  # 隐藏密钥
    print(f"🤖 使用模型: {model} (配置名: {model_name})")
    
    llm = ChatOpenAI(
        model=model,
        temperature=0.7,
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )
    
    # 定义可用的工具
    tools = [get_current_time]
    
    # 创建支持工具调用的提示模板
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是一个有用的AI助手，请用中文回答问题，保持对话自然流畅。

你有以下可用的工具：
1. get_current_time: 获取当前系统时间

当用户问到时间相关问题时，请使用get_current_time工具获取准确时间信息。"""
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    
    # 创建工具调用代理
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    
    return agent_executor


def simple_chat_with_tools(model_name="nebula"):
    """支持工具调用的简单对话"""
    print("💬 开始与AI对话 (输入 'quit' 或 'exit' 退出)")
    print("-" * 50)

    agent_executor = create_llm_with_tools(model_name)
    if agent_executor is None:
        print("❌ 无法创建LLM实例，程序退出。")
        return

    # 初始化对话历史
    conversation_history = []

    while True:
        user_input = input("\n👤 您: ").strip()

        if user_input.lower() in ["quit", "exit", "退出", "q"]:
            print("👋 再见！")
            break

        if not user_input:
            continue

        print("🤖 AI: ", end="", flush=True)

        try:
            # 准备聊天历史传递给agent
            chat_history_for_agent = []
            for msg in conversation_history:
                if isinstance(msg, HumanMessage):
                    chat_history_for_agent.append(("human", msg.content))
                elif isinstance(msg, AIMessage):
                    chat_history_for_agent.append(("ai", msg.content))

            # 使用流式输出方式，支持处理工具调用
            full_response = ""
            for chunk in agent_executor.stream(
                {
                    "input": user_input,
                    "chat_history": chat_history_for_agent,
                }
            ):
                # 检查是否为工具调用
                if "actions" in chunk:
                    for action in chunk["actions"]:
                        print(f"\n🔧 正在调用工具: {action.tool}")
                        print(f"   工具输入: {action.tool_input}")
                # 检查是否为工具结果
                elif "steps" in chunk:
                    for step in chunk["steps"]:
                        print(f"✅ 工具调用完成，结果: {str(step.observation)[:100]}...")
                # 检查是否为最终输出
                elif "output" in chunk:
                    token = chunk["output"]
                    print(token, end="", flush=True)
                    full_response += token

            print()  # 换行
            
            # 更新对话历史
            conversation_history.append(HumanMessage(content=user_input))
            conversation_history.append(AIMessage(content=full_response))
            
        except Exception as e:
            print(f"\n❌ 出现错误: {e}")
            print("💡 请检查您的API密钥和网络连接")


def main():
    """主函数"""
    print("🚀 LangChain AI问答 (使用config.json - 支持多轮对话和工具调用 - 流式输出)")
    print("=" * 65)

    # 初始化环境
    if not init_environment():
        return

    # 加载配置以获取模型列表
    config = load_config()
    models = config["models"]
    default_model = config.get("default_model", "nebula")

    # 显示可用模型
    print("\n📋 可用模型:")
    for i, model in enumerate(models.keys(), 1):
        print(f"  {i}. {model}")
    
    print(f"\n💡 请输入模型编号或名称 (默认: {default_model})")
    
    # 获取用户选择的模型
    try:
        user_input = input("模型选择: ").strip()
    except:
        # 如果输入不可用，使用默认模型
        user_input = ""
    
    selected_model = default_model  # 默认模型
    
    if user_input:
        # 检查是否是编号
        if user_input.isdigit():
            model_index = int(user_input) - 1
            if 0 <= model_index < len(models):
                selected_model = list(models.keys())[model_index]
            else:
                print(f"❌ 无效的模型编号，使用默认模型 {selected_model}")
        elif user_input in models:
            selected_model = user_input
        else:
            print(f"❌ 模型 {user_input} 不存在，使用默认模型 {selected_model}")
    else:
        selected_model = default_model  # 使用配置中的默认模型
    
    print(f"🎯 选择模型: {selected_model}")
    
    try:
        # 开始对话
        simple_chat_with_tools(selected_model)
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断，再见！")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")


if __name__ == "__main__":
    main()