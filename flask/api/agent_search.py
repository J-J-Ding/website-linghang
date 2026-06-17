import os
import re
import time
from typing import Generator
import platform
import requests
import json
from get_icenter import IcenterAPI

# 配置路径和选项
# 根据操作系统自动选择正确的 ChromeDriver 路径
system = platform.system().lower()
current_dir = os.path.dirname(os.path.abspath(__file__))
if system == 'linux':
    CHROME_DRIVER_PATH = os.path.join(current_dir, "../resource/chromedriver/chromedriver-linux64/chromedriver")
else:
    raise NotImplementedError(f"Unsupported operating system: {system}")


class ICenterSearcher:
    def __init__(self, emp_no, token):
        self.emp_no, self.token = emp_no, token

    def _ai_page_search(self, question, space_id):
        api_url = "https://search.zte.com.cn/zte-icenter-search-api/v2/ai-search"
        header = {
            "Content-Type": "application/json",
            "X-Emp-No": self.emp_no,
            "X-Auth-Value": self.token
        }
        payload = {
            "app": "ai_search",
            "domain": "space",
            "isDeepThinking": True,
            "keyword": question,
            "searchFilters": {"space": {"type": "space", "value": [space_id]}},
            "sorter": "CHUNK_SORT"
        }

        try:
            with requests.post(api_url, headers=header, json=payload, stream=True) as response:
                response.raise_for_status()  # 检查 HTTP 错误

                # 逐行读取（适用于按行返回的 JSON 或文本）
                for line in response.iter_lines():
                    if line:  # 过滤空行
                        decoded_line = line.decode('utf-8').strip()
                        if not decoded_line.startswith("data:"):
                            continue

                        # 去掉开头的 "data:"
                        decoded_line = decoded_line[5:]
                        # 如果是 JSON 格式，可以尝试解析
                        try:
                            data = json.loads(decoded_line)
                            yield data
                        except json.JSONDecodeError:
                            yield decoded_line
        except Exception as e:
            print(f"执行ai-search错误：{str(e)}")
            yield {"info_type": "error", "result": "icenter检索错误，请重试"}

    def _ai_common_search(self, question):
        api_url = "https://search.zte.com.cn/zte-icenter-search-api/v2/ai-search"
        header = {
            "Content-Type": "application/json",
            "X-Emp-No": self.emp_no,
            "X-Auth-Value": self.token
        }
        payload = {
            "app": "ai_search",
            "correctKeyword": True,
            "domain": "universal",
            "isDeepThinking": True,
            "keyword": question,
            "keywordCorrected": False,
            "page": 1,
            "searchFilters": {},
            "searchTag": "space_page",
            "size": 15,
            "sorter": "CHUNK_SORT"
        }
        try:
            with requests.post(api_url, headers=header, json=payload, stream=True) as response:
                response.raise_for_status()  # 检查 HTTP 错误

                # 逐行读取（适用于按行返回的 JSON 或文本）
                for line in response.iter_lines():
                    if line:  # 过滤空行
                        decoded_line = line.decode('utf-8').strip()
                        if not decoded_line.startswith("data:"):
                            continue

                        # 去掉开头的 "data:"
                        decoded_line = decoded_line[5:]
                        # 如果是 JSON 格式，可以尝试解析
                        try:
                            data = json.loads(decoded_line)
                            yield data
                        except json.JSONDecodeError:
                            yield decoded_line
        except Exception as e:
            print(f"执行ai-search错误：{str(e)}")
            yield {"info_type": "error", "result": "icenter检索错误，请重试"}

    def search_and_show(self, keyword: str, space_id: str = None, space_name: str = None):
        print(f"正在搜索关键词：{keyword}")

        if space_id:
            for data in self._ai_page_search(keyword, space_id):
                yield data
        else:
            for data in self._ai_common_search(keyword):
                yield data
        print("icenter搜索结束")

prompt = "请结合上下文信息有条理地回复用户的问题。"

# 标准的AI智能体函数
def Agent_ai_search(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    system_prompt = prompt

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    message = messages[-1]["content"]

    pattern_space_id = r'/space/([a-zA-Z0-9]+)/'
    pattern_shared_id = r'/shared/([a-zA-Z0-9]+)/'

    match_space_id = re.search(pattern_space_id, message)
    match_shared_id = re.search(pattern_shared_id, message)
    if match_space_id:
        space_id = match_space_id.group(1)
        # 正则表达式模式匹配URL
        pattern_url = r'https:\/\/i\.zte\.com\.cn\/index\/ispace\/#\/space\/[a-zA-Z0-9]+\/wiki\/page\/[a-zA-Z0-9]+\/view'

        # 使用re.sub()方法替换URL为空字符串
        question = re.sub(pattern_url, '', message)
    elif match_shared_id:
        space_id = match_shared_id.group(1)
        # 正则表达式模式匹配URL
        pattern_url = r'https:\/\/i\.zte\.com\.cn\/#\/shared\/[a-zA-Z0-9]+\/wiki\/page\/[a-zA-Z0-9]+\/view'

        # 使用re.sub()方法替换URL为空字符串
        question = re.sub(pattern_url, '', message)
    else:
        print("未找到空间id，在通用空间搜索")
        question = message
        space_id = None

    icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    token = icentapi.token
    searcher = ICenterSearcher(emp_no=os.getenv('USERNAME'), token=token)
    # 接收生成器
    results_generator = searcher.search_and_show(question, space_id)

    search_start = False
    for item in results_generator:
        if isinstance(item, str) and item == "[START]":
            search_start = True
            yield f"[搜索开始] {question}\n\n"
        elif isinstance(item, dict) and item["info_type"] == "references":
            references_fusion = item["references_fusion"]
            for reference in references_fusion:
                title = reference["title"]
                url = reference["sourceUrl"]
                result_str = f"[{title}]({url})\n\n"
                yield result_str  # ✅ 实时返回搜索结果
        elif isinstance(item, dict) and item["info_type"] == "answer":
            yield item['result']  # ✅ 实时返回搜索结果
        # 可选：检测 finishReason 是否为 'stop' 表示结束
        elif isinstance(item, dict) and 'finishReason' in item and item['finishReason'] == 'stop':
            return
        elif isinstance(item, str) and item == "[DONE]":
            return  # ✅ 返回结束
        elif isinstance(item, dict) and item["info_type"] == "error":
            yield item['result']
            return

    if not search_start:
        yield "没能理解您的问题，请给出更详细的描述"


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
        for chunk in Agent_ai_search(messages, model):
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
    # messages.append({"role": "user", "content": "https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/f8db7a4a20e442a2b8e4fcf96efb3992/view OTN DCN邻居配置和DCN邻居配置功能有什么区别"})
    # messages.append({"role": "user", "content": "https://i.zte.com.cn/#/shared/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/f8db7a4a20e442a2b8e4fcf96efb3992/view OTN DCN邻居配置和DCN邻居配置功能有什么区别"})
    messages.append({"role": "user", "content": "OTN DCN邻居配置和DCN邻居配置功能有什么区别"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    test_Agent_call_demo()