import re
import os
import json
import time
import socket
import hashlib
import requests
import subprocess
import sqlite3
from typing import Optional
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown, Get_icenter_content_markdown


def Get_gitlog(repository):
    """
    获取 Gerrit 中指定仓库的所有 Git 提交日志（分页）
    
    参数:
        repository (str): 仓库名称，如 "OTN/AI"
    
    返回:
        list: 包含所有 commit 的列表，每个元素是 dict
    """
    username = "10171727"
    hostname = "gerrit.zte.com.cn"
    port = 29418
    branch = "master"
    limit = 500   # 每次最大获取数量（由 Gerrit 控制，默认最多 500）
    start = 0     # 初始偏移量
    all_commits = []

    while True:
        print(f"正在获取偏移量 {start} 的提交记录...")

        # 构建命令
        cmd = (
            f'ssh -p {port} {username}@{hostname} '
            f'gerrit query --format=JSON --start={start} '
            f'"project:{repository} branch:{branch}"'
        )

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            output = result.stdout.strip()
            if not output:
                print("没有更多提交记录了。")
                break

            # 按行解析 JSON 数据
            lines = output.splitlines()
            batch = []
            for line in lines:
                try:
                    data = json.loads(line)
                    if "commit" in data:
                        batch.append(data)
                except json.JSONDecodeError:
                    continue

            if not batch:
                print("当前批次无有效提交记录。")
                break

            all_commits.extend(batch)
            start += limit  # 更新偏移量
            time.sleep(0.5)  # 避免请求过快

        except subprocess.CalledProcessError as e:
            print("执行命令失败:", e.stderr)
            break

    print(f"✅ 共获取到 {len(all_commits)} 条提交记录。")
    return all_commits

def Replace_question(question, matches):
    """
    替换 question 中符合 matches 正则表达式的内容，仅替换原始匹配项。
    
    :param question: 原始问题字符串
    :param matches: 包含 (pattern, replacer_func) 的列表
        matches = [
            (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
            (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
        ]
    :return: 替换后的新字符串
    """

    # 构建命名组的正则表达式，便于识别是哪个模式匹配了
    named_patterns = [
        f"(?P<GROUP_{i}>{pattern})"
        for i, (pattern, _) in enumerate(matches)
    ]
    full_pattern = "|".join(named_patterns)

    # 编译正则表达式
    regex = re.compile(full_pattern)

    # 替换回调函数
    def replace_callback(match):
        for i in range(len(matches)):
            group_name = f"GROUP_{i}"
            if match.group(group_name):
                pattern, replacer = matches[i]
                return replacer(match.group(0))
        return "[未知替换]"

    # 只做一次扫描和替换，不会重复处理替换后的内容
    result = regex.sub(replace_callback, question)
    return result

def Replace_icenter(content):
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_content_markdown),
    ]

    return Replace_question(content, matches)


def Replace_rdc(content):
    matches = [
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    return Replace_question(content, matches)


class UACTokenGenerator:

    def __init__(self):
        pass

    @staticmethod
    def get_host_ip():
        hostname = socket.gethostname()
        first_ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        return first_ip

    @staticmethod
    def get_token(username, password):
        url = "http://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
        client_ip = UACTokenGenerator.get_host_ip()
        loginsyscode = 'Portal'
        originsyscode = ''
        token = ''

        text = {
            "account": username,
            "passWord": password,
            "loginClientIp": client_ip,
            "loginSystemCode": loginsyscode,
            "originSystemCode": originsyscode,
            "other": {
                "networkArea":'1',
                "networkAccessType":'1'
            },
            "verifyCode":hashlib.md5(str(username+password+client_ip+loginsyscode+originsyscode)
                                    .encode(encoding='utf-8')).hexdigest()  
        }
        headers = {'Content-type': 'application/json'}
        response = requests.post(url,data=json.dumps(text),headers=headers)
        try:
            # print(f"Status Code: {response.status_code}")
            content = response.json()
        except Exception as e:
            print(f"Invalid JSON response: {response.text}\n")
            raise e
        if content['code']['code'] == '0000' and content['bo']['code'] == '0000' :
            token = content['other']['token']
            # print(token)
        return token

def Get_UACtoken(username, password):
    return UACTokenGenerator.get_token(username, password)

def Get_file_from_server(url: str, filepath: str) -> Optional[str]:
    """
    从指定的文件服务器 URL 获取文件内容（自动绕过代理）
    适配服务端返回的字符串格式（支持单个文件和目录批量读取）

    :param url: 完整的请求 URL，例如 "http://10.90.251.221:4001/read"
    :param filepath: 从 BASE_DIR 起始的完整相对路径，例如 "L2/plat/port/src/sspPortApi.c" 或 "L2/plat/port/src/*"
    :return: 服务器返回的字符串内容，失败时返回 None
    """
    try:
        # 构造查询参数
        params = {
            "filepath": filepath
        }

        # 禁用代理，直接连接（等价于 curl --noproxy）
        proxies = {
            "http": None,
            "https": None
        }

        # 发送 GET 请求
        response = requests.get(
            url=url,
            params=params,
            timeout=30,
            proxies=proxies  # 绕过代理
        )

        # 检查响应状态
        if response.status_code == 200:
            # 直接返回纯文本内容（服务端已统一为字符串格式）
            return response.text
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
        return None

def test_Replace_question():
    # question = "请查看文档 http://example.com 和 https://test.com，还有参考编号 ABC-123 和 XYZ-456。"
    question = """
        https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/6d4ac8ab72f04ec38d636c273f1e0363/view
        https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/c684c02eae7e46388ea425275dbf18bf/view
        https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/8f7b002c277a4651aba07d5d69bebd36/view
        请总结上述页面内容。
        OTNAG-1507978
        OTNAG-1506280
        请总结上述单号内容。
    """
    # 定义规则：每个元素是一个 (pattern, replacer) 对
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]
    
    result = Replace_question(question, matches)
    print(result)


def test_Get_UACtoken():
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    uactoken = Get_UACtoken(username, password)
    print(f"uactoken:{uactoken}")


def test_Get_gitlog():
    log = Get_gitlog("OTN/AI")
    print(log)
    return

def test_get_file_from_server():
    file_content = Get_file_from_server("http://10.90.251.221:4001/read", "L2/plat/port/src/*")
    print(file_content)


def Get_username():
    """
    从数据库中获取用户ID和用户名的映射关系
    
    返回:
        dict: 以用户ID为键，用户名为值的字典
    """
    # 连接到数据库
    db_path = "../data/sql_config.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查询user表中的工号和姓名
        cursor.execute("SELECT 工号, 姓名 FROM user")
        rows = cursor.fetchall()
        
        # 创建userid:username字典
        user_dict = {}
        for row in rows:
            userid, username = row
            user_dict[userid] = username
        
        return user_dict
    finally:
        conn.close()

def test_Replace_icenter():
    print(Replace_icenter("https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/7d61b4e46ed511f0b0a0092e8c89e184/view"))

def test_Get_username():
    print(Get_username())

if __name__ == "__main__":
    # test_Get_UACtoken()
    # test_Replace_question()
    # test_Get_gitlog()
    # test_Replace_icenter()
    test_Get_username()
