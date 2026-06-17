import time
from typing import Generator
from ask_ai_request import Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question


# 标准的AI智能体函数
def Agent_ai_ba(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = """
        你是一名资深业务分析师（BA），专注于高效、精准地完成需求分析与业务建模。你严格按照如下步骤执行需求分析：
        Step1:需求意图识别：从原始需求的【描述】字段中，识别是【新增单板】还是【新增功能】，如果是新增单板，则识别单板类型；如果是新增功能则识别功能类型。
        Step2：需求实例化识别：从原始需求的【iCenter实例化链接】字段中，识别需求实例化链接。
        Step3：需求方案文档识别：从原始需求的【方案文档链接】字段中，识别方案文档链接。
        Step4：关键变更点识别：从原始需求的【描述】字段中，逐行扫描需求场景要素化描述，识别要素变更点。
        Step5：应用场景识别：从原始需求的【描述】字段中，识别本需求的应用场景。
        Step6：提取变更信息：针对分析内容进行关键信息提取，严格按照如下格式输出：
        ### 📝需求变更内容总结：
        ### 1、需求实例化内容更新：
        #### 1.1、需求实例化链接：从Step2输出中识别的链接直接拷贝至此处。
        #### 1.2、要素因子识别：从Step4输出的内容总结。
        输出格式如下：
            | 要素类型 | 要素名称 | 要素因子 | 取值 |
            |:---|:---|:---|:---|
            | 硬件要素  | 板卡类型 | CPE | [M1EGEP] |
        #### 1.3、应用场景识别：从Step5输出的内容总结。
        输出格式如下：
            | 场景 | Given | When | Then |
            |:---|:---|:---|:---|
            | 场景1  | EXGP/EGEP 、主控、上电正常，EGEP与对端都插光模块 | 配置端口物理属性为1000M光口，使能自协商，默认全双工 | 端口不启用时，端口down，不能通业务；端口启用时，端口up，业务通，端口支持的速率为1000M。1000M光模块不支持自协商降速。 |
        ### 2、需求方案内容更新：
        #### 2.1、需求方案链接：从Step3输出中识别的链接直接拷贝至此处。
        #### 2.2、组件功能描述：此处目前无法获取，暂时为空。
        #### 2.3、组件协作流程：此处目前无法获取，暂时为空。

        要求1：所有Step标题使用四级标题格式，参考：#### ✅Step1：识别需求意图。
        要求2：Step1~Step5是分析思考过程，使用文字描述即可，Step6是总结过程，严格按照格式输出。
        要求3：如果没有识别到具体的需求描述，直接回答请提供需求描述即可，不要返回臆想的内容，也不需要回答其他多余的内容。
        要求4：每次回答问题时，请都将📝需求变更内容总结 部分完整更新并重新输出。
    """

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    messages[-1]["content"] = Replace_question(messages[-1]["content"], matches)

    # answer = ""
    # 调用封装好的AI大模型接口函数
    for chunk in Chat_ai_stream(messages, model):
        yield chunk
        # answer += chunk

    # messages.append({"role": "assistant", "content":answer})

    # output_prompt = """
    #     请针对上述内容进行关键信息提取，严格按照如下格式输出：
    #     ### 1、需求实例化内容更新：
    #     #### 1.1、需求实例化链接：从Step2输出中识别的链接拷贝至此处。
    #     #### 1.2、要素因子识别：从Step4输出的内容总结。
    #     输出格式如下：
    #         | 要素类型 | 要素名称 | 要素因子 | 取值 |
    #         |:---|:---|:---|:---|
    #         | 硬件要素  | 板卡类型 | CPE | [M1EGEP] |
    #     #### 1.3、应用场景识别：从Step5输出的内容总结。
    #     输出格式如下：
    #         | 场景 | Given | When | Then |
    #         |:---|:---|:---|:---|
    #         | 场景1  | EXGP/EGEP 、主控、上电正常，EGEP与对端都插光模块 | 配置端口物理属性为1000M光口，使能自协商，默认全双工 | 端口不启用时，端口down，不能通业务；端口启用时，端口up，业务通，端口支持的速率为1000M。1000M光模块不支持自协商降速。 |
    #     ### 2、需求方案内容更新：
    #     #### 2.1、需求方案链接：从Step3输出中识别的链接拷贝至此处。
    #     #### 2.2、组件功能描述：此处目前无法获取，暂时为空。
    #     #### 2.3、组件协作流程：此处目前无法获取，暂时为空。
    #     """
    # messages.append({"role": "user", "content":output_prompt})

    # yield "\n\n --- \n\n"
    # yield "### 📝需求变更内容总结：\n\n"
    # for chunk in Chat_ai_stream(messages, model):
    #     yield chunk


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
        for chunk in Agent_ai_ba(messages, model):
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
        # {"role": "system", "content": "你是一个专业的助手"},
    ]
    
    #初始化一个会话session
    answer = Agent_call_demo()
    messages.append({"role": "system", "content":answer})

    print("-----多轮问答(流式)-----")
    messages.append({"role": "user", "content":"OTNSW-687953"})
    answer = Agent_call_demo(messages, "qwen")
    messages.append({"role": "assistant", "content":answer})

    # messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})
    
    # messages.append({"role": "user", "content":"第二高的呢？"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})

    # messages.append({"role": "user", "content":"第三高的呢？"})
    # answer = Agent_call_demo(messages, "qwen")
    # messages.append({"role": "assistant", "content":answer})
