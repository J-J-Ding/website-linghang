
import time
from typing import Generator
from datetime import datetime
from ask_ai_request import Chat_ai_stream
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

appid = '24782e901c9f466790323868b89dbfc9'
apikey = '29d4b9365caf42a59214449623603a00'

def parse_markdown_pageId(markdown: str) -> str:
    pattern = r'/wiki/page/([a-f0-9]+)'
    match = re.search(pattern, markdown)

    if match:
        extracted_value = match.group(1)
        return extracted_value
    else:
        return None

def get_icenter_md_result(icenter_url):
    url = "https://yxrde.zx.zte.com.cn/gateway/api/corpus/icenter-md"
    headers = {
        "Content-Type": "application/json"
    }
    
    # 要发送的数据
    data = {
        "account": "10243863",
        "token": uactoken,
        "icenter_url": icenter_url,
        "is_md": False,
        "is_save_img": False,
        "is_containChildren": False, 
        "lineBreakInTable": " ",
        "is_metadata": False
    }
    
    # # 将数据转换为JSON格式的字符串
    # json_data = json.dumps(data)
    
    # 发送POST请求
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.text

    except requests.exceptions.RequestException as e:
        # 如果请求失败，打印错误信息
        print("请求失败，错误信息：", e)
        return None

def parse_markdown_sections(md_content):
    sections = []
    pattern = re.compile(r'^(#+)\s+(.*?)$', re.MULTILINE)
    matches = list(pattern.finditer(md_content))

    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = re.sub(r'^\d+(?:\.\d+)*[\s、.]+', '', match.group(2))

        next_index = i + 1
        if next_index < len(matches):
            next_match = matches[next_index]
            next_pos = next_match.start()
            content = md_content[match.end():next_pos].strip()
        else:
            content = md_content[match.end():].strip()

        sections.append({'level': level, 'title': title, 'content': content})

    return sections

def build_section_paths(sections):
    stack = []
    paths = []
    for section in sections:
        level = section['level']
        title = section['title']

        while stack and stack[-1]['level'] >= level:
            stack.pop()

        stack.append(section)
        path = [f"{'#' * s['level']}{s['title']}" for s in stack]
        path_str = "".join(path)
        paths.append({'section': section, 'path': path, 'path_str': path_str})

    return paths

def get_affected_components(page_id, section_infos):
    pattern_str = '^#波及影响分析##波及组件$'

    section_maps = {section_info["path_str"]: section_info for section_info in section_infos}
    if pattern_str:
        pattern = re.compile(pattern_str)
        match_infos = [section_info for section_info in section_infos if pattern.search(section_info['path_str'])]
        result = match_infos[0]['section']['content']
        parts = result.split("【沉淀特性方案对应章节】", 1)
        components = ''
        if len(parts) > 1:
            components = parts[0].strip()
        return components

def parse_section_content(page_id, section_infos):
    pattern_str = '^#模块设计.+##模块接口设计###接口设计.+####功能描述$'
    pattern_str2 = '^#模块设计.+##模块接口设计###接口设计.+####功能设计#####流程设计$'
    result = list()
    section_maps = {section_info["path_str"]: section_info for section_info in section_infos}
    if pattern_str:
        pattern = re.compile(pattern_str)
        match_infos = [section_info for section_info in section_infos if pattern.search(section_info['path_str'])]
        result.append(match_infos[0])
    if pattern_str2:
        pattern2 = re.compile(pattern_str2)
        match_infos = [section_info for section_info in section_infos if pattern2.search(section_info['path_str'])]
        result.append(match_infos[0])
    return result

def Agent_ai_coder_get_feature_design():
    icenter_url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/ba89542746cc11f09a4cc5a932d7eaac/view"
    page_id = parse_markdown_pageId(icenter_url)
    md_text = get_icenter_md_result(icenter_url)
    sections = parse_markdown_sections(md_text)
    section_infos = build_section_paths(sections)
    affected_components = get_affected_components(page_id, section_infos)
    return affected_components

def Agent_ai_coder_get_function_design():
    icenter_url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/2b3fa9e3481911f088c471b06fcadbcd/vieww"
    page_id = parse_markdown_pageId(icenter_url)
    md_text = get_icenter_md_result(icenter_url)
    sections = parse_markdown_sections(md_text)
    section_infos = build_section_paths(sections)
    result = parse_section_content(page_id, section_infos)
    return result

def Agent_ai_tl_generate_design(text):
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
def Agent_ai_tl(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    yield "暂不支持"
    return 

    system_prompt = "你是一名助手"

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    affected_components = Agent_ai_coder_get_feature_design()
    yield "# 第1步：获取需求方案的波及组件...\n"
    yield "处理中...\n"
    yield affected_components + "\n\n"

    yield "# 第2步：识别详设的变更点和变更内容...\n"
    yield "处理中...\n"
    result = Agent_ai_coder_get_function_design()
    yield "### 详设变更的功能模块\n"
    yield result[0]['path'][0][1:] + "\n"
    yield "### 详设变更的接口设计\n"
    yield result[1]['path'][2][3:] + "\n\n"

    yield "# 第3步：生成详设中接口设计变更的内容...\n"
    yield "处理中...\n"
    yield "### 生成的接口功能描述\n"
    prompt = Agent_ai_tl_generate_design("# 页面标题 【组件功能设计】【MVP 2.0】【国网电力】SUPP组件-分组客户侧单板需求(F4Kx4) - 支持基于EOO/EOOSU的Qinq EPL业务 # 生成类型 功能描述")
    messages1 = [
                {"role": "user", "content": prompt},
            ]

    answer = ""
    for chunk in Chat_ai_stream(messages1, model):
        yield chunk
        answer += chunk

    messages.append({"role": "user", "content":messages1[0]["content"]})
    messages.append({"role": "assistant", "content":answer})

    yield "\n### 生成的接口流程设计\n"
    prompt = Agent_ai_tl_generate_design("# 页面标题 【组件功能设计】【MVP 2.0】【国网电力】SUPP组件-分组客户侧单板需求(F4Kx4) - 支持基于EOO/EOOSU的Qinq EPL业务 # 生成类型 流程设计")
    messages2 = [
                {"role": "user", "content": prompt},
            ]
    
    answer = ""
    for chunk in Chat_ai_stream(messages2, model):
        yield chunk
        answer += chunk

    messages.append({"role": "user", "content":messages2[0]["content"]})
    messages.append({"role": "assistant", "content":answer})

    yield "\n\n"

    question = """
        请提取变更信息：针对内容进行关键信息提取，严格按照如下格式输出：
        ### 📝详设变更内容总结：
        ### 1、接口功能描述：从Step3输出的接口功能描述内容获取，请详细摘录，保持原有内容的完整性，包括文字、表格、图片等信息。
        ### 2、接口流程设计：从step3输出的接口流程设计内容获取，请详细摘录，保持原有内容的完整性，包括文字、表格、图片等信息。
        """
    
    messages.append({"role": "user", "content":question})

    # 调用封装好的AI大模型接口函数
    for chunk in Chat_ai_stream(messages, model):
        yield chunk


# 测试函数，调用AI智能体
def Agent_call_demo(messages, model="qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_tl(messages, model):
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

    messages.append({"role": "user", "content":"你好"})
    answer = Agent_call_demo(messages, "nebula")
