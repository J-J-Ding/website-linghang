# coding=utf-8
import os
import requests
import json
import sqlite3
from typing import Generator
import markdown2 as md2

from api_utils import Get_UACtoken
from get_icenter import Get_icenter_title_markdown, Icenter_block_set, Icenter_page_create, Icenter_page_isexist, Icenter_content_html_set, Get_icenter_parentpath

username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
uactoken = Get_UACtoken(username, password)

DNSTDIO_MAP = {
    "DNstdioBasicAgent": ("089ea6e45c1046798ddaf4a7dd8e8c06", "e5aff3f0c6064803bfcef9846c0abb59", "DNstdio-通用智能体"),
    "需求分析": ("4819bc3d56e940618ab725ebab68c86b", "prod_d0cdb7d9e6b347399aa5dc9b16f1b9e1", "需求分析智能体"),
    "DNstdioFzAgent": ("a1eb481abbb84e88aa648159ceeda8f0", "fa5a28a439584a838640e663be47152b",
                       "DNstdio-光层仿真单板模型生成"),
    "DNstdioMdAgent": ("dad897445985463f91ec8a7b50c75046", "ee061a0145ae4512862cb17f9a7785da",
                       "DNstdio-光层仿真modeldata生成"),
    "DNstdioCntEvalAgent": ("53d2265999574e1c864703934a4a728f", "prod_793ab14970ca4aa287c97b6b4ef7523b",
                            "DNstdio-内容域测评"),
}

area_feature_map = {
    'd4a2c95fd72311efa6e991b9604c470f': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9ca67501e61d11f0b821e35e794d234d/view', # 光层业务
    '730cdf86173e11f0b1e437f2f87f8184': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/ac254951e61d11f09e30c11fbd216770/view', # 电层业务
    '99da86d820b511f09fccbb17049e688c': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/be865576e61d11f0a4599903f437511a/view', # 分组业务
    'b6c030a5ef2d11efab0767decfd9208f': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/d1c146cfe61d11f0b24775ca5c14fb29/view', # 智控协同业务
    '9b8d3215ef8711ef9f097df5f06ee3d8': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/eab6bdeee61d11f0b66b31493ff2d705/view', # 支撑领域
    'b8f0daf0519311f085cecbd38b00b54b': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/0a845f38e61e11f0ba0739e824c02244/view'} # 产品安全

# area_map = {
#     '光层业务': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/9ca67501e61d11f0b821e35e794d234d/view',
#     '电层业务': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/ac254951e61d11f09e30c11fbd216770/view',
#     '分组业务': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/be865576e61d11f0a4599903f437511a/view',
#     '智控协同业务': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/d1c146cfe61d11f0b24775ca5c14fb29/view',
#     '支撑领域': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/eab6bdeee61d11f0b66b31493ff2d705/view',
#     '产品安全': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/0a845f38e61e11f0ba0739e824c02244/view'}


### -----------------------------------------------------------------------

def Agent_ai_dnstdio_basic(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    DNstdio通用智能体，用于解答各种问题。
    
    参数:
        messages (list): 对话历史消息列表，格式为[{"role": "user", "content": "问题内容"}, ...]
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回智能体的回答内容
    """
    system_prompt = "你是一名专业的AI助手，来自DNstdio平台，可以帮助用户解答各种问题。"

    # 如果messages为空，则返回系统提示词并结束
    if not messages:
        yield system_prompt
        return

    for chunk in Agent_ai_dnstdio(messages, model):
        yield chunk


def Agent_ai_dnstdio_Fz(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    DNstdio光层仿真单板模型生成智能体。
    
    参数:
        messages (list): 对话历史消息列表，格式为[{"role": "user", "content": "问题内容"}, ...]
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回智能体的回答内容
    """
    system_prompt = "你是一名专业的AI助手，来自DNstdio平台，负责光层仿真单板模型生成。"

    # 如果messages为空，则返回系统提示词并结束
    if not messages:
        yield system_prompt
        return

    for chunk in Agent_ai_dnstdio(messages, model):
        yield chunk


def Agent_ai_dnstdio_Md(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    DNstdio光层仿真modeldata生成智能体。
    
    参数:
        messages (list): 对话历史消息列表，格式为[{"role": "user", "content": "问题内容"}, ...]
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回智能体的回答内容
    """
    system_prompt = "你是一名专业的AI助手，来自DNstdio平台，负责光层仿真modeldata生成。"

    # 如果messages为空，则返回系统提示词并结束
    if not messages:
        yield system_prompt
        return

    for chunk in Agent_ai_dnstdio(messages, model):
        yield chunk


### -----------------------------------------------------------------------
#
# 数据库参数
CNTEVAL_DB_PATH = "./public/website-linghang/flask/data/contenteval.db"
CNTEVAL_DB_NAME = "contenteval"


#
def _contenteval_save_db(pageid, title, link, grade, content):
    """
    保存或更新内容域测评结果到SQLite数据库。
    
    参数:
        pageid: 页面ID
        title: 页面标题
        link: 页面链接
        grade: 测评等级
        content: 测评内容
        
    返回:
        str: 操作结果提示信息
    """
    try:
        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(current_time)

        conn = None
        with sqlite3.connect(CNTEVAL_DB_PATH) as conn:
            print(f"{CNTEVAL_DB_PATH}数据库连接已打开。")
            cursor = conn.cursor()

            # 检查是否存在相同记录
            cursor.execute(f"SELECT pageid FROM {CNTEVAL_DB_NAME} WHERE pageid = ?", (pageid,))
            existing_record = cursor.fetchone()
            if existing_record:
                # 记录存在，执行更新
                design_id = existing_record[0]
                cursor.execute(f'''
                               UPDATE {CNTEVAL_DB_NAME}
                               SET pageid = ?,
                                   title  = ?,
                                   link   = ?,
                                   grade  = ?,
                                   content = ?,
                                   currenttime = ?
                               WHERE pageid = ?
                               ''', (
                    pageid,
                    title,
                    link,
                    grade,
                    content,
                    current_time,
                    pageid
                ))
                print(f"更新了测评结果，pageid: {pageid}")
            else:
                # 记录不存在，执行插入
                cursor.execute(f'''
                               INSERT INTO {CNTEVAL_DB_NAME}
                               (pageid, title, link, grade, content, currenttime)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ''', (
                    pageid,
                    title,
                    link,
                    grade,
                    content,
                    current_time
                ))
                print(f"新增了测评结果，pageid: {cursor.lastrowid}")
            conn.commit()
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"An error occurred in _contenteval_save_db: {e}")
    finally:
        if conn:
            conn.close()
            print(f"{CNTEVAL_DB_PATH}数据库连接已关闭。")
        return '数据保存完毕'


def extract_spaceid_pageid(url: str):
    """
    从Icenter页面URL中提取spaceId和pageId。
    
    参数:
        url (str): Icenter页面URL，格式如"https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageId}/view"
        
    返回:
        tuple: (spaceId, pageId)，提取出的空间ID和页面ID
    """
    parts = url.split("/")
    spaceId_index = parts.index("wiki") - 1
    spaceid = parts[spaceId_index]
    pageid = parts[-2]
    return spaceid, pageid


def create_evaluation_page(title: str, result: str, mainurl: str, output_root: str):
    """
    创建或更新内容域测评结果页面到Icenter系统。
    
    参数:
        title (str): 原页面标题
        result (str): 测评结果内容（Markdown格式）
        mainurl (str): 原页面URL
        output_root (str): 输出目录URL，用于确定新页面的父页面
        
    返回:
        tuple: (resp, isSuccess, pagetitle, url)
            resp: API响应结果
            isSuccess: 是否成功
            pagetitle: 测评报告页面标题
            url: 测评报告页面URL
    """
    # 创建测评结果页面
    # 父页面为：https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/a218772fcf2411f09f067f78e1d9e326/view
    # spaceId = "fbff14a6a14c4985874248df3ac610c1"
    # parentId = "a218772fcf2411f09f067f78e1d9e326"

    if not output_root:
        return None, False, None, None

    spaceId, parentId = extract_spaceid_pageid(output_root)
    pagetitle = title + '_测评报告'

    extensions = [
        'tables',  # 表格支持
        'code-friendly',  # 代码块
        'footnotes',
        'nl2br',  # 换行转换
        'sane_lists',  # 智能列表
        'markdown-in-html'
    ]

    linkcontent = f'\n\n<h4>主页面</h4>\n<p><a href = {mainurl}>{mainurl}</a></p>'

    # 将 Markdown 转为 HTML 或目标格式
    content_body_update = md2.markdown(result, extras=extensions)
    content_body_update = content_body_update + linkcontent
    # print(content_body_update)

    isExist, pageid = Icenter_page_isexist(spaceId, parentId, pagetitle)

    if isExist:
        url = f'https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{pageid}/view'
        resp = Icenter_content_html_set(url, content_body_update)
        print(f"更新测评结果页面：{resp} \r\n {resp}")
        return resp, resp, pagetitle, url
    else:
        url = f'https://i.zte.com.cn/index/ispace/#/space/{spaceId}/wiki/page/{parentId}/view'
        resp = Icenter_page_create(url, pagetitle, content_body_update)
        if resp:
            print(f"创建测评结果页面：{resp}")
            return resp, True, pagetitle, resp
        else:
            return "", False, pagetitle, ""


def update_evaluation_grade(message_content: str, result: str, reporttitle: str, reporturl: str):
    """
    从测评结果中提取测评等级，并更新到原Icenter页面的测评等级区块。
    
    参数:
        message_content (str): 原页面URL
        result (str): 测评结果内容
        reporttitle (str): 测评报告页面标题
        reporturl (str): 测评报告页面URL
        
    返回:
        str: 提取并格式化后的测评等级
    """
    grade = '基础级'
    parts = result.split('综合评级\n')
    if len(parts) > 1:
        grade = parts[1].split('\n')[0].strip()
    print(grade)

    grade = f'{grade} <a href = "{reporturl}" >{reporttitle}</a>'
    # 更新页面的测评等级block
    block_id = ''
    block_title = ''
    block_tag = '测评等级'

    blkrlt = Icenter_block_set(message_content, block_id, block_title, block_tag, grade)
    print(f"写入测评等级：{blkrlt}")
    return grade


def get_area_root(parent_path: str):
    """
    根据父路径获取对应的领域根页面URL。
    
    参数:
        parent_path (str): 父页面路径
        
    返回:
        str: 对应的领域根页面URL，如果未找到则返回None
    """
    for key, value in area_feature_map.items():
        if key in parent_path:
            return value
    return None


def Agent_ai_dnstdio_contentEval(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    DNstdio内容域测评智能体，用于对Icenter页面内容进行测评。
    
    参数:
        messages (list): 对话历史消息列表，最后一条消息应为{"content": "Icenter页面URL"}
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回测评结果内容
    """
    system_prompt = "你是一名专业的AI助手，来自DNstdio平台，负责内容域的测评。"

    # 如果messages为空，则返回系统提示词并结束
    if not messages:
        yield system_prompt
        return
    # print(messages)
    url = messages[-1]["content"]

    parts = url.split('/')
    pageId = parts[-2]

    title, icenter_content = Get_icenter_title_markdown(url)
    parent_path = Get_icenter_parentpath(url)
    output_root = get_area_root(parent_path)
    # print(output_root)

    evalresult = []
    # print(icenter_content)
    msg1 = {"agent": "DNstdioCntEvalAgent", "content": icenter_content}
    for chunk in Agent_ai_dnstdio([msg1], model):
        evalresult.append(chunk)

    # 拼接评测结果并更新测评等级 block
    result = ''.join(evalresult)

    # 使用提取的辅助函数创建页面
    resp, isSucess, reporttitle, reporturl = create_evaluation_page(title, result, url, output_root)

    # 填充测评等级grade
    grade = update_evaluation_grade(url, result, reporttitle, reporturl)

    # 保存测评结果到sqlite
    # saveresult = _contenteval_save_db(pageId, title, url, grade, result)
    yield result


def Agent_ai_dnstdio(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    核心函数，用于调用DNstdio平台的各种智能体服务。
    
    参数:
        messages (list): 对话历史消息列表，最后一条消息应包含{"agent": "智能体名称", "content": "请求内容"}
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回智能体的响应内容
        
    异常:
        如果请求失败或智能体未定义，将返回相应的错误信息
    """
    agent = messages[-1]["agent"]

    # 检查 model 是否存在
    if agent not in DNSTDIO_MAP:
        yield f"错误：模型 '{model}' 未在 DNSTDIO_MAP 中定义"
        return

    # 获取 appid 和 apikey
    appid, apikey, appname = DNSTDIO_MAP[agent]

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
        "stream": True,
        "text": messages[-1]["content"],
    }})
    req_args.get('headers').update({'Authorization': auth_info})

    chat_url = 'https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat'

    try:
        response = requests.post(chat_url, **req_args, stream=True)

        if response.status_code != 200:
            yield f"请求失败，状态码：{response.status_code}"
            return

        for chunk in response.iter_lines():
            if not chunk:
                continue
            try:
                decoded_chunk = chunk.decode('utf-8')
                if not decoded_chunk.startswith("data:"):
                    continue
                json_data = decoded_chunk[5:].strip()
                if json_data == "[DONE]":
                    continue
                chunk_data = json.loads(json_data)
                if "result" in chunk_data:
                    content = chunk_data["result"]
                    if content:
                        yield content
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                yield f"[解析错误] {e}"
                continue

    except Exception as e:
        yield f"[请求异常] {str(e)}"


def General_Agent_ai_dnstdio_basic(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    通用DNstdio智能体接口，支持自定义appid和apikey。
    
    参数:
        messages (list): 对话历史消息列表，第一条消息应包含{"context": "{\"appid\": \"...\", \"key\": \"...\"}"}
        model (str): 模型名称，默认为"nebula"
        
    返回:
        Generator[str, None, None]: 流式返回智能体的回答内容
    """
    system_prompt = "你是一名专业的AI助手，来自DNstdio平台，可以帮助用户解答各种问题。"

    # 如果messages为空，则返回系统提示词并结束
    if not messages:
        yield system_prompt
        return

    context = json.loads(messages[0]['context'])
    appid = context['appid']
    apikey = context['key']

    print(messages[0])

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
        "stream": True,
        "text": messages[-1]["content"],
    }})
    req_args.get('headers').update({'Authorization': auth_info})

    chat_url = 'https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat'

    try:
        response = requests.post(chat_url, **req_args, stream=True)

        if response.status_code != 200:
            yield f"请求失败，状态码：{response.status_code}"
            return

        for chunk in response.iter_lines():
            if not chunk:
                continue
            try:
                decoded_chunk = chunk.decode('utf-8')
                if not decoded_chunk.startswith("data:"):
                    continue
                json_data = decoded_chunk[5:].strip()
                if json_data == "[DONE]":
                    continue
                chunk_data = json.loads(json_data)
                if "result" in chunk_data:
                    content = chunk_data["result"]
                    if content:
                        yield content
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                yield f"[解析错误] {e}"
                continue

    except Exception as e:
        yield f"[请求异常] {str(e)}"


if __name__ == "__main__":
    pass