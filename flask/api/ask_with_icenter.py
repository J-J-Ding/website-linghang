import re
import io
import json
from typing import List
from get_icenter import Get_icenter
from ask_ai_request import Ask_ai, Chat_ai

def extract_urls(text: str) -> List[str]:
    """从文本中提取所有HTTP/HTTPS链接
    
    Args:
        text (str): 输入文本
        
    Returns:
        List[str]: 找到的所有URL列表
    """
    # 匹配 http:// 或 https:// 开头的URL
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    return urls

def replace_urls_with_content(original_text: str) -> str:
    """用get_icenter返回的内容替换文本中的链接
    
    Args:
        original_text (str): 原始文本
        get_icenter_func (function): get_icenter函数
        
    Returns:
        str: 替换后的文本
    """
    urls = extract_urls(original_text)
    result_text = original_text
    
    for url in urls:
        try:
            # 调用get_icenter函数获取内容
            title, content, content_markdown = Get_icenter(url)
            
            # 替换URL为返回的内容
            result_text = result_text.replace(url, "\n\n# "+title+"\n"+content_markdown+"\n\n")
        except Exception as e:
            print(f"处理URL {url} 时出错: {e}")
            # 出错时保留原链接
            continue
            
    return result_text

def Replace_icenter(question):
    urls = extract_urls(question)
    
    for url in urls:
        try:
            title, content, content_markdown, updatetime = Get_icenter(url)
            # 直接在 question 上做替换
            question = question.replace(url, "\n\n# " + title + "\n" + content_markdown + "\n" + "最后更新时间：" + updatetime['updateDate'])
        except Exception as e:
            print(f"处理URL {url} 时出错: {e}")
            continue
            
    return question

def Ask_with_icenter(question, model="nebula"):
    question_replace = replace_urls_with_content(question)
    result = Ask_ai(question_replace, model)
    return result

def Chat_with_icenter(question, messages, model="nebula"):
    question_replace = replace_urls_with_content(question)
    result = Chat_ai(question_replace, messages, model)
    return result

# 示例使用
if __name__ == "__main__":
    # 示例文本(包含多个链接)
    question = """
    https://i.zte.com.cn/#/shared/eb89d0a39f5e4296962be08878f1d2b6/wiki/page/90689ca3f57543efaf011bea7847fc56/view
    我想针对上述内容发一个简答的小思考，表达这个新技术能力很强，我会用这个技术做点具体的xx事情，内容不要超过100个字。最后说一下你是什么大模型。
    """
    
    result = Ask_with_icenter(question, "qwen")
    
    print(result)
