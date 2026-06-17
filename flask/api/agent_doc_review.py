import time
import re
import traceback
import os
import markdown
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Generator, List, Dict, Optional, Any, Union
from get_rdc import Get_rdc_markdown
from agent_utils import Get_model_config, Clear_proxy
from get_icenter import Get_icenter_markdown, Get_icenter, Icenter_block_set, Icenter_comment_add
from api_utils import Replace_question
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

#详设文档对应url，解析出来之后用
design_document_url = ""


@tool("时间查询工具")
def get_current_datetime() -> str:
    """
    获取当前系统日期和时间的工具

    Returns:
        str: 当前日期和时间的字符串，格式为 'YYYY-MM-DD HH:MM:SS'
    """
    current_time = datetime.datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


@tool("平方计算工具")
def calculate_square(number: int) -> int:
    """
    计算一个数的平方的工具

    Args:
        number: 需要计算平方的数值

    Returns:
        float: 该数的平方值
    """
    return number ** 2


def Agent_doc_review_langgraph(messages: List[Dict] = [], config: dict = None) -> Generator[str, None, None]:
    """
    最简版 LangGraph AI 聊天函数（流式输出）(组件评审助手内部工具定制接口)

    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature

    Yields:
        逐字符返回 AI 回答
    """

    if not messages:
        yield "你是一名专业的AI助手。"
        return

    Clear_proxy()

    # model_name = config.get("model_name", "Qwen3-235B-A22B")
    # model_name = "nebulacoder-lite-v7.0"
    # url = "http://nebulacoder.dev.zte.com.cn:40081/v1"
    # key = "10171727"
    model_name, api_key, base_url = Get_model_config(config.get("model", "qwen3-zte"))

    # 构建 LangChain LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        timeout=30,
        streaming=True,  # 支持流式输出
    )

    # 转换消息为 LangChain 格式
    langchain_messages = []
    for message in messages:
        content = message["content"]
        if message["role"] == "system":
            langchain_messages.append(SystemMessage(content=content))
        elif message["role"] == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif message["role"] == "assistant":
            langchain_messages.append(AIMessage(content=content))

    # 创建 LangGraph agent
    try:
        agent = create_react_agent(llm, tools=[calculate_square, get_current_datetime])

        # 使用 stream 方法来获取流式输出
        for chunk in agent.stream({"messages": langchain_messages}):
            # 检查是否为工具调用
            for key, value in chunk.items():
                if 'messages' in value:
                    for msg in value['messages']:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            # 输出工具调用信息
                            for tool_call in msg.tool_calls:
                                # 工具名称现在已经是别名
                                tool_info = f"[调用工具: {tool_call['name']}] "
                                for char in tool_info:
                                    yield char

                        if hasattr(msg, 'content') and msg.content:
                            # 流式输出 AI 回答的每个字符
                            for char in msg.content:
                                yield char
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        print(error_msg)
        for char in error_msg:
            yield char

def extract_design_review_checklist(markdown_content: str) -> list[str]:
    """
    从Markdown内容中提取设计评审检查单并过滤URL链接

    Args:
        markdown_content: Markdown格式的文本内容

    Returns:
        提取并过滤URL后的设计评审检查单内容，如果未找到则返回None
    """
    # 查找"设计评审检查单"出现的位置
    title_index = markdown_content.find('设计评审检查单')
    if title_index == -1:
        return []

    # 从标题位置开始提取剩余内容
    remaining_content = markdown_content[title_index:]

    # 找到下一个顶级标题的开始位置（以#开头的行为新章节）
    lines = remaining_content.split('\n')
    content_lines = []

    # 跳过标题行，从第二行开始收集内容
    for i, line in enumerate(lines[1:], 1):
        # 如果遇到新的顶级标题（以#开头的行），则停止收集
        if line.strip().startswith('#') and i > 0:
            break
        content_lines.append(line)

    checklist_content = '\n'.join(content_lines).strip()

    if not checklist_content:
        return []

    # 提取URL链接
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, checklist_content)

    return urls

def extract_otnsw_ids(text):
    # 定位“1.2 功能描述”章节内容
    start_marker = "1 功能描述"
    end_marker = "2 功能设计"

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError("未能找到 '1.2 功能描述' 或 '2 功能设计' 章节")

    section_text = text[start_idx:end_idx]

    # 使用正则表达式匹配所有 OTNSW- 开头的编号
    otnsw_pattern = r'OTNSW-\d+'
    matches = re.findall(otnsw_pattern, section_text)

    return matches

def extract_test_case_design(text):
    """
    从文档文本中提取第7章“测试用例设计”的全部内容。
    
    :param text: 完整的文档字符串
    :return: 第7章的文本内容（字符串），若未找到则返回空
    """
    # 使用正则匹配章节起始与结束
    pattern = r"(7 测试用例设计\s*={3,}.*?)(?=\n\d+\s+\S+|$)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        #raise ValueError("未找到 '7 测试用例设计' 章节")
        return ""
    return match.group(1).strip()

def extract_acceptance_criteria_from_string(text: str) -> str:
    """
    从字符串文本中尝试提取“验收准则”字段的内容。
    适用于包含“验收准则”字段的文本，例如需求卡片或包含该字段的Markdown/HTML片段。
    如果在文本中找不到“验收准则”，则返回空字符串。

    :param text: 输入的原始文本字符串 (str)
    :return: 提取出的验收准则内容，已去除HTML标签 (str)。如果未找到，则返回空字符串。
    """
    # 正则表达式匹配“验收准则”及其内容
    # 匹配模式: "验收准则" 后面跟着冒号或换行，然后是内容，直到遇到下一个顶级标题或表格行或文本结尾
    # 使用非贪婪匹配 .*?
    # 考虑到可能在表格中，如 | 6 | 验收准则 | <p>...</p> |
    # 或者在描述列表中，如 | 字段 | 描述 | ... | 6 | 验收准则 | <p>...</p> |
    
    # 尝试匹配表格形式（更适用于你之前提供的需求卡片结构化文本）
    table_pattern = r'\|\s*\d+\s*\|\s*验收准则\s*\|\s*(.*?)\s*\|\s*\n'
    match = re.search(table_pattern, text, re.DOTALL)
    
    if match:
        raw_content = match.group(1).strip()
        # 移除HTML标签
        clean_content = re.sub(r'<[^>]+>', '', raw_content)
        # 清理多余的空白和换行
        clean_content = re.sub(r'\s*\n\s*', '\n', clean_content).strip()
        return clean_content

    # 如果表格形式没找到，尝试简单的标题形式（适用于普通文本）
    title_pattern = r'验收准则\s*[:：]?\s*(.*?)(?=\n\s*\d+\s+\||\n\s*[\d#]\s+\w+|\n\s*\|\s*\d+\s*\||\Z)'
    match = re.search(title_pattern, text, re.DOTALL)
    
    if match:
        raw_content = match.group(1).strip()
        clean_content = re.sub(r'<[^>]+>', '', raw_content)
        clean_content = re.sub(r'\s*\n\s*', '\n', clean_content).strip()
        return clean_content

    # 如果都没找到，返回空字符串
    return ""

def extract_section_titles(content: str, content_markdown: str) -> List[Dict[str, str]]:
    """从页面内容中提取所有章节标题，并清理标题文本

    Args:
        content (str): 页面的原始HTML内容
        content_markdown (str): 页面的Markdown格式内容

    Returns:
        List[Dict[str, str]]: 包含标题信息的字典列表，每个字典包含：
            - level (str): 标题级别（h1, h2, h3等）
            - text (str): 清理后的标题文本（去掉数字和空格）
            - original_text (str): 原始标题文本
    """

    def clean_title_text(text: str) -> str:
        """清理标题文本，去掉数字和多余空格"""
        if not text:
            return text

        # 去掉所有数字（可选，根据需求开启）
        text = re.sub(r'\d+', '', text)

        # 规范化空格：多个空格合并为一个，去掉首尾空格
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    section_titles = []

    # 优先从HTML内容中提取
    html_pattern = r'<h([1-6])[^>]*>(.*?)</h\1>'
    html_matches = re.findall(html_pattern, content, re.DOTALL | re.IGNORECASE)

    for level, html_content in html_matches:
        # 提取纯文本，去掉HTML标签
        text = re.sub(r'<[^>]+>', '', html_content).strip()
        if text:
            cleaned_text = clean_title_text(text)
            section_titles.append({
                'level': f'h{level}',
                'text': cleaned_text,
                'original_text': text
            })

    # 如果HTML中没有找到标题，尝试从Markdown中提取
    if not section_titles:
        md_pattern = r'^(#{1,6})\s+(.+)$'
        md_lines = content_markdown.split('\n')

        for line in md_lines:
            md_match = re.match(md_pattern, line.strip())
            if md_match:
                level = len(md_match.group(1))
                text = md_match.group(2).strip()
                if text:
                    cleaned_text = clean_title_text(text)
                    section_titles.append({
                        'level': f'h{level}',
                        'text': cleaned_text,
                        'original_text': text
                    })

    return section_titles

def get_page_sections(url: str) -> List[Dict[str, str]]:
    """只获取页面的章节标题信息

    Args:
        url (str): iCenter页面的完整URL

    Returns:
        List[Dict[str, str]]: 章节标题列表
    """
    title, content, content_markdown, updatetime = Get_icenter(url)
    return extract_section_titles(content, content_markdown)

def get_document_report_info(text: str) -> Dict[str, Optional[str]]:
    """
    从评审报告文本中提取关键信息

    Args:
        text (str): 评审报告文本

    Returns:
        Dict[str, Optional[str]]: 包含提取信息的字典
    """
    result = {
        "document_name": None,
        "review_conclusion": None,
        "advantages_summary": [],
        "improvement_suggestions": []
    }

    # 提取文档名称 - 改进匹配模式
    doc_name_patterns = [
        r"评审文档[：:\s]+\**(.+?)\**\s*$",  # 匹配中文冒号和星号
        r"评审文档[：:\s]+(.+?)\s*$",        # 匹配中文冒号
        r"\*\*评审文档\*\*[：:\s]*(.+?)\s*$" # 匹配加粗格式
    ]

    for pattern in doc_name_patterns:
        doc_name_match = re.search(pattern, text, re.MULTILINE)
        if doc_name_match:
            result["document_name"] = doc_name_match.group(1).strip()
            break

    # 提取评审结论 - 改进匹配模式
    conclusion_patterns = [
        r"评审结论[：:\s]+\**(.+?)\**\s*$",  # 匹配中文冒号和星号
        r"评审结论[：:\s]+(.+?)\s*$",        # 匹配中文冒号
        r"\*\*评审结论\*\*[：:\s]*(.+?)\s*$" # 匹配加粗格式
    ]

    for pattern in conclusion_patterns:
        conclusion_match = re.search(pattern, text, re.MULTILINE)
        if conclusion_match:
            result["review_conclusion"] = conclusion_match.group(1).strip()
            break

    # 提取优点总结
    advantages_section = re.search(r"四、优点总结.*?(?=五、改进建议|\n## |$)", text, re.DOTALL)
    if advantages_section:
        advantages_text = advantages_section.group(0)
        # 提取带编号的优点项
        advantages_items = re.findall(r"\d+\.\s*(.+?)(?=\n\d+\.|\n## |$)", advantages_text)
        if advantages_items:
            result["advantages_summary"] = [item.strip() for item in advantages_items]
        else:
            # 如果没有编号，尝试提取段落内容
            lines = advantages_text.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('##') and not line.startswith('四、'):
                    clean_line = re.sub(r'^\d+\.\s*', '', line.strip())
                    if clean_line and len(clean_line) > 10:  # 过滤过短的文本
                        result["advantages_summary"].append(clean_line)

    # 提取改进建议
    improvements_section = re.search(r"五、改进建议.*?(?=\n## |$)", text, re.DOTALL)
    if improvements_section:
        improvements_text = improvements_section.group(0)
        # 提取带编号的改进建议项
        improvements_items = re.findall(r"\d+\.\s*(.+?)(?=\n\d+\.|\n## |$)", improvements_text)
        if improvements_items:
            result["improvement_suggestions"] = [item.strip() for item in improvements_items]
        else:
            # 如果没有编号，尝试提取段落内容
            lines = improvements_text.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('##') and not line.startswith('五、'):
                    clean_line = re.sub(r'^\d+\.\s*', '', line.strip())
                    if clean_line and len(clean_line) > 10:  # 过滤过短的文本
                        result["improvement_suggestions"].append(clean_line)

    # 如果优点总结为空，尝试其他提取方式
    if not result["advantages_summary"]:
        alt_advantages = re.findall(r"优点总结.*?[\n：:\s]+\s*(.+?)(?=\n##|\n五、|\n改进建议|$)", text, re.DOTALL)
        if alt_advantages:
            result["advantages_summary"] = [item.strip() for item in alt_advantages if len(item.strip()) > 10]

    # 如果改进建议为空，尝试其他提取方式
    if not result["improvement_suggestions"]:
        alt_improvements = re.findall(r"改进建议.*?[\n：:\s]+\s*(.+?)(?=\n##|$)", text, re.DOTALL)
        if alt_improvements:
            result["improvement_suggestions"] = [item.strip() for item in alt_improvements if len(item.strip()) > 10]

    # 最后尝试直接搜索整个文本
    if not result["document_name"]:
        # 直接搜索包含"池化单板APO详细设计"的文本
        direct_doc_match = re.search(r"(M001-池化单板APO详细设计)", text)
        if direct_doc_match:
            result["document_name"] = direct_doc_match.group(1)

    if not result["review_conclusion"]:
        # 直接搜索包含"评审通过"的文本
        direct_conclusion_match = re.search(r"(评审通过)", text)
        if direct_conclusion_match:
            result["review_conclusion"] = direct_conclusion_match.group(1)

    return result

def quick_debug_preview(html_content: str):
    """
    快速调试预览 - 最简单的方法
    """
    # 保存到项目目录
    preview_file = "debug_preview.html"
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 获取绝对路径
    abs_path = os.path.abspath(preview_file)

    # 在PyCharm中显示文件路径，方便手动打开
    print(f"📁 HTML文件已保存: {abs_path}")
    print("在PyCharm中右键文件 → 'Open in Browser' 或使用快捷键")

    return abs_path

def convert_review_report_to_html(markdown_text: str, output_file: Optional[str] = None) -> str:
    """
    将Markdown格式的评审报告转换为HTML内容

    Args:
        markdown_text: Markdown格式的评审报告文本
        output_file: 可选，输出HTML文件路径

    Returns:
        HTML格式的字符串（只包含内容部分，最外层用div包裹）
    """

    def replace_emojis_with_text(text: str) -> str:
        """将表情符号替换为对应的文本描述（暂时去掉）"""
        # try:
        #     emoji_replacements = {
        #         '✅': '(通过)',
        #         '❌': '(不通过)',
        #         '⚠️': '(警告)',
        #         '🎉': '(庆祝)',
        #         '📋': '(文档)'
        #     }
        #
        #     for emoji, replacement in emoji_replacements.items():
        #         text = text.replace(emoji, replacement)
        #
        #     return text
        # except Exception as e:
        #     print(f"替换表情符号时出错: {str(e)}")
        #    return text
        return text

    def preprocess_markdown(text: str) -> str:
        """预处理Markdown文本，清理格式"""
        try:
            # 将表情符号替换为文本
            clean_text = replace_emojis_with_text(text)
            if not clean_text or not clean_text.strip():
                return "# 空内容\n\n没有提供有效的Markdown内容。"

            lines = clean_text.split('\n')
            processed_lines = []

            for line in lines:
                # 清理表格格式
                if '|' in line and not line.strip().startswith('#'):
                    line = '|'.join([col.strip() for col in line.split('|')])
                    line = f"|{line}|" if not line.startswith('|') else line
                    line = line if line.endswith('|') else f"{line}|"

                processed_lines.append(line)

            return '\n'.join(processed_lines)
        except Exception as e:
            print(f"预处理Markdown时出错: {str(e)}")
            return text

    def enhance_html_content(html: str) -> str:
        """增强HTML内容，添加内联样式"""
        try:
            # 为状态单元格添加内联样式
            html = html.replace('>通过<', '><span style="color: #27ae60; font-weight: bold;">通过</span><')
            html = html.replace('>不通过<', '><span style="color: #e74c3c; font-weight: bold;">不通过</span><')
            html = html.replace('>部分通过<', '><span style="color: #f39c12; font-weight: bold;">部分通过</span><')

            # 为风险等级添加内联样式
            html = html.replace('>无风险<', '><span style="color: #27ae60;">无风险</span><')
            html = html.replace('>低<', '><span style="color: #f39c12;">低</span><')

            # 为表情替换文本添加内联样式
            html = html.replace('>(通过)<', '><span style="font-weight: bold; color: #27ae60;">(通过)</span><')
            html = html.replace('>(不通过)<', '><span style="font-weight: bold; color: #e74c3c;">(不通过)</span><')
            html = html.replace('>(警告)<', '><span style="font-weight: bold;">(警告)</span><')

            return html
        except Exception as e:
            print(f"增强HTML内容时出错: {str(e)}")
            return html

    def get_current_time() -> str:
        """获取当前时间"""
        try:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "未知时间"

    def create_error_content(error_message: str) -> str:
        """创建错误内容"""
        return f'''
        <div style="padding: 20px; border: 1px solid #e74c3c; background: #fadbd8; border-radius: 5px;">
            <h2 style="color: #c0392b;">转换过程中出现错误</h2>
            <p><strong>错误信息:</strong> {error_message}</p>
            <p>请尝试切换大模型重新进行评审。</p>
        </div>
        '''

    # 主转换逻辑
    try:
        # 输入验证
        if not markdown_text or not isinstance(markdown_text, str):
            error_msg = "输入的Markdown文本为空或格式不正确"
            print(error_msg)
            return create_error_content(error_msg)

        # 预处理Markdown
        processed_md = preprocess_markdown(markdown_text)

        # 配置Markdown扩展
        extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.extra',
        ]

        # 转换为HTML
        html_content = markdown.markdown(processed_md, extensions=extensions)

        # 增强HTML内容（添加内联样式）
        enhanced_html = enhance_html_content(html_content)

        # 构建内容HTML（最外层用div包裹）
        content_html = f'''
        <div>
            <div class="review-report" style="max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                {enhanced_html}
                <div class="footer" style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
                评审时间: {get_current_time()} 
                </div>
            </div>
        </div>
        '''

        # 如果指定了输出文件，则保存完整HTML
        if output_file:
            try:
                # 保存为完整HTML文件
                full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>评审报告 - 池化单板APO详细设计</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e8f4fd;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin: 20px 0 10px 0;
        }}
        h1 {{
            font-size: 24px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 20px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
            margin-top: 30px;
        }}
        h3 {{
            font-size: 16px;
            color: #34495e;
            margin-top: 20px;
        }}
        ul, ol {{
            margin: 10px 0 10px 20px;
        }}
        li {{
            margin: 5px 0;
        }}
        p {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    {content_html}
</body>
</html>'''
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                print(f"HTML文件已保存: {output_file}")
            except Exception as e:
                print(f"保存文件时出错: {str(e)}")

        # 只返回HTML内容
        return content_html

    except Exception as e:
        error_msg = f"Markdown转换HTML失败: {str(e)}"
        print(f"转换错误: {error_msg}")
        print(f"错误详情: {traceback.format_exc()}")
        return create_error_content(error_msg)

def update_review_table(markdown_table: str, result: Dict) -> str:
    """
    更新Markdown表格中的评审信息

    :param markdown_table: 原始的Markdown表格字符串
    :param result: 包含更新信息的字典
    :return: 更新后的Markdown表格字符串
    """
    # 增强的参数验证和调试信息
    print(f"Debug: Received result dict: {result}")
    print(f"Debug: Keys in result: {list(result.keys())}")

    if not result:
        raise ValueError("result dictionary is empty")

    document_name = result.get("document_name")
    if not document_name:
        # 尝试其他可能的字段名
        possible_names = ["doc_name", "title", "document_title", "design_title", "name"]
        for name in possible_names:
            if name in result:
                document_name = result[name]
                print(f"Debug: Found document name in field '{name}': {document_name}")
                break

        if not document_name:
            raise ValueError(
                "document_name is required to identify the target row. Available keys: " + ", ".join(result.keys()))

    # 分割表格行
    lines = markdown_table.strip().split('\n')
    if len(lines) < 3:
        raise ValueError("Invalid markdown table format")

    # 解析表头，获取列索引
    header_line = lines[0]
    headers = [col.strip() for col in header_line.split('|') if col.strip()]
    print(f"Debug: Table headers: {headers}")

    # 构建列名到索引的映射
    column_mapping = {
        "详设标题": None,
        "详设链接": None,
        "负责领域": None,
        "负责团队": None,
        "详设负责人": None,
        "详设智能体评审结论": None,
        "优点总结": None,
        "改进建议": None,
        "问题说明": None
    }

    for idx, header in enumerate(headers):
        for key in column_mapping.keys():
            if key in header:
                column_mapping[key] = idx
                print(f"Debug: Mapped '{key}' to column index {idx}")
                break

    # 检查必要的列是否存在
    required_columns = ["详设标题", "详设智能体评审结论", "优点总结", "改进建议"]
    for col in required_columns:
        if column_mapping[col] is None:
            raise ValueError(f"Required column '{col}' not found in table. Available columns: {headers}")

    # 获取分隔线，用于保持表格格式
    separator_line = lines[1]
    separator_cells = [cell.strip() for cell in separator_line.split('|')[1:-1]]

    # 分析每列的对齐方式并计算最大宽度
    column_widths = []
    for i, cell in enumerate(separator_cells):
        # 计算分隔线的长度作为初始列宽
        width = len(cell)
        column_widths.append(width)

    print(f"Debug: Initial column widths: {column_widths}")

    # 查找目标行并更新
    updated_lines = []
    found_target = False

    for i, line in enumerate(lines):
        if line.startswith('|') and line.endswith('|'):
            # 解析行数据
            cells = [cell.strip() for cell in line.split('|')[1:-1]]

            if len(cells) >= len(headers):
                # 检查详设标题是否匹配
                title_cell = cells[column_mapping["详设标题"]]
                # 移除<br>标签进行比较
                clean_title = re.sub(r'<br\s*/?>', '', title_cell).strip()

                print(f"Debug: Checking row {i}, title: '{clean_title}', target: '{document_name}'")

                if clean_title == document_name:
                    found_target = True
                    print(f"Debug: Found matching row at line {i}")

                    # 更新对应单元格
                    # 详设智能体评审结论
                    conclusion_idx = column_mapping["详设智能体评审结论"]
                    new_conclusion = str(result.get("review_conclusion", "") or "")
                    cells[conclusion_idx] = new_conclusion
                    # 更新列宽
                    column_widths[conclusion_idx] = max(column_widths[conclusion_idx], len(new_conclusion))

                    # 优点总结（列表转字符串，用逗号分隔）
                    advantages_idx = column_mapping["优点总结"]
                    advantages_list = result.get("advantages_summary", []) or []
                    if isinstance(advantages_list, list):
                        new_advantages = ", ".join([str(item) for item in advantages_list])
                    else:
                        new_advantages = str(advantages_list)
                    cells[advantages_idx] = new_advantages
                    # 更新列宽
                    column_widths[advantages_idx] = max(column_widths[advantages_idx], len(new_advantages))

                    # 改进建议（列表转字符串，用逗号分隔）
                    improvements_idx = column_mapping["改进建议"]
                    improvements_list = result.get("improvement_suggestions", []) or []
                    if isinstance(improvements_list, list):
                        new_improvements = ", ".join([str(item) for item in improvements_list])
                    else:
                        new_improvements = str(improvements_list)
                    cells[improvements_idx] = new_improvements
                    # 更新列宽
                    column_widths[improvements_idx] = max(column_widths[improvements_idx], len(new_improvements))

                    # 重新构建行，保持对齐
                    formatted_cells = []
                    for j, cell in enumerate(cells):
                        # 对每个单元格进行格式化，保持列宽
                        formatted_cell = f" {cell.ljust(column_widths[j])} "
                        formatted_cells.append(formatted_cell)

                    updated_line = "|" + "|".join(formatted_cells) + "|"
                    updated_lines.append(updated_line)
                    print(f"Debug: Updated row: {updated_line}")
                else:
                    # 对于非目标行，也重新格式化以保持一致性
                    formatted_cells = []
                    for j, cell in enumerate(cells):
                        formatted_cell = f" {cell.ljust(column_widths[j])} "
                        formatted_cells.append(formatted_cell)

                    updated_line = "|" + "|".join(formatted_cells) + "|"
                    updated_lines.append(updated_line)
            else:
                updated_lines.append(line)
        elif i == 1:  # 分隔线
            # 重新生成分隔线，根据更新后的列宽
            separator_cells = []
            for width in column_widths:
                separator_cell = "-" * width
                # 保持原有的对齐方式（如果有冒号表示对齐方式）
                original_separator = separator_cells[len(separator_cells)] if len(separator_cells) < len(column_widths) else ""
                if original_separator.startswith(":") and original_separator.endswith(":"):
                    separator_cell = ":" + "-" * (width-2) + ":"
                elif original_separator.startswith(":"):
                    separator_cell = ":" + "-" * (width-1)
                elif original_separator.endswith(":"):
                    separator_cell = "-" * (width-1) + ":"
                separator_cells.append(separator_cell)

            formatted_separator_cells = []
            for j, cell in enumerate(separator_cells):
                formatted_cell = f" {cell.ljust(column_widths[j])} " if len(cell) < column_widths[j] else f" {cell} "
                formatted_separator_cells.append(formatted_cell)

            separator_line = "|" + "|".join(formatted_separator_cells) + "|"
            updated_lines.append(separator_line)
        else:
            updated_lines.append(line)

    if not found_target:
        # 打印所有找到的标题用于调试
        all_titles = []
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) > column_mapping["详设标题"]:
                    title = re.sub(r'<br\s*/?>', '', cells[column_mapping["详设标题"]]).strip()
                    if title and not title.startswith('---'):  # 跳过分隔线
                        all_titles.append(title)

        raise ValueError(f"Document with title '{document_name}' not found in table. Available titles: {all_titles}")

    return '\n'.join(updated_lines)

def update_tl_document(url:str, review_report:str):
    # 获取智能体评审结论
    review_conclusion = get_document_report_info(review_report)

    review_conclusion_block_id = ""
    review_conclusion_block_title = "详设智能体评审结论"
    review_conclusion_block_tag = "详设智能体评审结论"
    update_review_result = Icenter_block_set(url,review_conclusion_block_id,review_conclusion_block_title,review_conclusion_block_tag,review_conclusion["review_conclusion"])

    #获取智能体评审报告
    review_report_html = convert_review_report_to_html(markdown_text=review_report)
    review_report_block_id = ""
    review_report_block_title = "详设智能体评审报告"
    review_report_block_tag = "详设智能体评审报告"

    update_review_result = Icenter_block_set(url,review_report_block_id,review_report_block_title,review_report_block_tag,review_report_html)

    #评审报告保留在对应详设文档页面评论区
    Icenter_comment_add(url,review_report_html)


def optimize_parallel_execution(design_document_content, document_section_titles, config):
    """并行执行检查任务"""

    def run_parallel_checks():
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 并行执行三个独立的检查任务
            future1 = executor.submit(run_section_format_check, document_section_titles, config)
            future2 = executor.submit(run_content_completeness_check, design_document_content, config)
            future3 = executor.submit(run_checklist_check, design_document_content, config)

            # 获取所有结果
            section_answer = future1.result()
            section_content_answer = future2.result()
            document_check_answer = future3.result()

            return section_answer, section_content_answer, document_check_answer

    return run_parallel_checks()


def run_section_format_check(document_section_titles, config):
    """章节格式检查（原逻辑保持不变）"""
    section_answer = []
    section_system_prompt = """
    # Persona（角色）：
    你是一名软件功能详细设计章节检查助手，只需要检查章节标题是否存在，按照格式要求输出评审报告。

    # Task（任务）：
    你的核心任务是对提供的详细设计文档进行章节存在性进行检查，不要发散考虑。

    # Rule（规则）：
    ## 1、详设文档格式检查（纯标题存在性检查）
    **检查范围**：['输入输出描述', '功能描述', '流程设计', '数据设计', '算法设计', '代码文件设计', '规格容量对性能影响分析', '可靠性设计', '产品安全设计', '可维护性设计', '兼容性设计', '多任务互斥复核', '状态机设计复核', '定位定界设计', '日志设计', '可测试性设计', '模块对外接口', '测试用例设计', '设计评审检查单']
    **检查标准**：纯存在性检查，只验证标题是否存在

    ### 关键词匹配表（必须严格执行）：
    | 检查章节 | 匹配关键词 | 判断标准 |
    |---------|-----------|----------|
    | 输入输出描述 | "输入输出" | 章节标题包含"输入输出"即通过 |
    | 功能描述 | "功能描述" | 章节标题包含"功能描述"即通过 |
    | ...（其他章节保持不变）... | | |

    ### 格式检查的绝对规则：
    - ✅ **只看标题**：不读取、不分析、不判断章节内容
    - ✅ **忽略所有符号**：忽略".", "..", "1.1", "2.1"等编号符号
    - ✅ **存在即通过**：只要标题存在，无论内容如何都通过

    ### 检查结论输出规范：
    - **检查通过**：对应输出位置填写 ✅ 通过
    - **检查不通过**：对应输出位置填写 ❌ 不通过

    # Format（格式）：
    ### 详设文档格式检查 
    | 检查章节 | 匹配关键词 | 判断标准 | 是否通过 |
    | :--- | :--- | :--- | :--- | :--- |
    | 输入输出描述 | "输入输出" | 章节标题包含"输入输出"即通过 | ✅ 通过 / ❌ 不通过 |
    | ...（其他章节保持不变）... | | |
    """
    section_user_prompt = "详设文档的章节列表如下：\n"
    section_user_prompt += f"{document_section_titles}" + "\n\n"
    section_message = [
        {"role": "system", "content": section_system_prompt},
        {"role": "user", "content": section_user_prompt},
    ]

    for chunk in Agent_doc_review_langgraph(section_message, config):
        section_answer.append(chunk)

    return section_answer


def run_content_completeness_check(design_document_content, config):
    """章节内容完整性检查（原逻辑保持不变）"""
    section_content_answer = []
    section_content_system_prompt = """
    # Persona（角色）：
    你是一名软件功能详细设计章节内容范式检查助手，严格按照任务描述的要求进行评审，按照格式要求输出评审报告。

    # Task（任务）：
    你的核心任务是对用户提供的详细设计文档和重点章节内容进行范式检查，只要内容不为空即可通过，确保评审问题的可收敛性。

    # Rule（规则）：
    ## 2、详设文档内容检查（内容完整性检查）
    **检查标准**：章节内容不能为空，有实质性内容
    **判断标准**：
    - 通过：有具体设计描述、流程图、数据定义等实质性内容
    - 不通过：完全空白

    ## 检查结论输出规范：
    - **检查通过**：对应输出位置填写 ✅ 通过
    - **检查不通过**：对应输出位置填写 ❌ 不通过

    # Format（格式）：
    ## 一、评审基本信息
    评审文档：[填写文档名称]
    文档版本：[填写版本号]

    ## 详设文档内容检查
    | 检查章节 | 内容是否为空 | 是否通过 |
    | :--- | :--- | :--- |
    | 输入输出描述 | 检查内容是否为空  | ✅ 通过 / ❌ 不通过 |
    | ...（其他章节保持不变）... |
    """
    section_content_user_prompt = "详设文档需要重点检查的章节有：['输入输出描述', '功能描述', '流程设计', '数据设计', '算法设计', '代码文件设计', '规格容量对性能影响分析', '可靠性设计', '产品安全设计', '可维护性设计', '兼容性设计', '多任务互斥复核', '状态机设计复核', '定位定界设计', '日志设计', '可测试性设计', '模块对外接口', '测试用例设计', '设计评审检查单']" + "\n"
    section_content_user_prompt += "详设文档页面内容如下:\n"
    section_content_user_prompt += f"{design_document_content}" + "\n\n"
    section_content_message = [
        {"role": "system", "content": section_content_system_prompt},
        {"role": "user", "content": section_content_user_prompt},
    ]

    for chunk in Agent_doc_review_langgraph(section_content_message, config):
        section_content_answer.append(chunk)

    return section_content_answer


def run_checklist_check(design_document_content, config):
    """检查单检查（原逻辑保持不变）"""
    # 详设检查单排查
    document_check_list_url = str(extract_design_review_checklist(design_document_content))
    if document_check_list_url != "[]":
        check_list_content = Get_icenter_markdown(document_check_list_url)
    else:
        check_list_content = "详设页面没有提供对应的详设检查单链接 \n"

    document_check_answer = []
    document_check_system_prompt = """
        # Persona（角色）：
        你是一名软件功能详细设计检查单排查助手，严格按照任务描述的要求进行详设检查单的排查，按照格式要求输出评审报告。

        # Task（任务）：
        你的核心任务是对提供的详细设计文档和详设检查单进行检查单排查，如果用户没有提供检查单内容，则直接说明未提供检查单，跳过检查步骤。

        # Rule（规则）：
        ## 详设检查单检查（关键改进部分）
        **检查标准**：对照用户提供的详设检查单，逐项检查文档中是否存在相关内容

        ## 检查单检查执行步骤：
        1. **提取检查项**：从用户提供的检查单中提取所有"检查内容"字段，如果用户没有提供检查单内容，则直接说明未提供检查单，跳过检查步骤
        2. **内容匹配**：在详设文档全文中搜索与检查项相关的关键词和内容
        3. **相关性判断**：检查文档是否包含检查项相关的设计描述、流程图、数据定义等
        4. **结果记录**：对每个检查项给出明确的通过/不通过判断和具体说明

        ## 检查单检查防误检清单：
        - [ ] 确认已提取检查单中的所有检查项
        - [ ] 确认在文档全文中进行了关键词搜索
        - [ ] 确认对每个检查项给出了具体说明

        ### 检查结论输出规范：
        - **检查通过**：对应输出位置填写 ✅ 通过
        - **检查不通过**：对应输出位置填写 ❌ 不通过

        # Format（格式）：
        ### 详设检查单内容检查（关键改进部分）
        **检查说明**：对照用户提供的详设检查单，逐项验证文档内容符合性

        | 检查项类别 | 检查内容 | 检查结果 | 具体说明 |
        | :--- | :--- | :--- | :--- |
        """
    document_check_user_prompt = "详设检查单内容如下：\n"
    document_check_user_prompt += f"{check_list_content}" + "\n"
    document_check_user_prompt += "详设文档页面内容如下:\n"
    document_check_user_prompt += f"{design_document_content}" + "\n\n"
    document_check_message = [
        {"role": "system", "content": document_check_system_prompt},
        {"role": "user", "content": document_check_user_prompt},
    ]

    for chunk in Agent_doc_review_langgraph(document_check_message, config):
        document_check_answer.append(chunk)

    return document_check_answer

def run_test_case_check(rdc_acceptance_list, doc_test_list, config):
    test_case_check_answer = []
    test_case_check_system_prompt = """
        # Persona（角色）  
        你是一名软件功能详细设计测试用例评审助手，专注于将用户提供的验收准则与测试用例进行逐项比对，并按指定格式输出结构化评审报告。

        # Task（任务）  
        对比用户提供的验收准则与测试用例，判断每项验收准则是否在测试用例中得到覆盖。若任一内容缺失（验收准则或测试用例未提供），则跳过检查并明确说明。

        # Rules（规则）  

        ## 检查逻辑  
        1. **内容缺失处理**：若用户未提供验收准则或测试用例，直接在“检查结果”中标注“未提供”，并跳过后续检查。  
        2. **覆盖判断**：针对每条验收准则，只要在测试用例中找到对应覆盖内容（语义一致或等效），即视为通过。  
        3. **多用例覆盖**：若一条验收准则对应多个测试用例，只要其中任意一个测试用例满足该准则，即视为通过。

        ## 输出规范  
        - **通过**：✅ 通过  
        - **不通过**：❌ 不通过  
        - **缺失**：⚠️ 未提供（验收准则或测试用例缺失）

        # Format（输出格式）  

        ### 测试用例设计检查  
        **检查说明**：根据用户提供的验收准则与测试用例，逐项验证测试用例对验收准则的覆盖情况。

        | 需求编号 | 验收准则 | 检查结果 | 具体说明 |
        | :--- | :--- | :--- | :--- |
        """
    test_case_check_user_prompt = "验收准则内容如下：\n"
    test_case_check_user_prompt += f"{rdc_acceptance_list}" + "\n"
    test_case_check_user_prompt += "测试用例内容如下:\n"
    test_case_check_user_prompt += f"{doc_test_list}" + "\n\n"
    test_case_check_message = [
        {"role": "system", "content": test_case_check_system_prompt},
        {"role": "user", "content": test_case_check_user_prompt},
    ]

    for chunk in Agent_doc_review_langgraph(test_case_check_message, config):
        test_case_check_answer.append(chunk)

    return test_case_check_answer

def generate_final_report(section_answer, section_content_answer, document_check_answer, test_case_answer, config):
    """生成最终报告（原逻辑保持不变）"""
    agent_tl_check_answer = []
    agent_tl_check_system_prompt = """
    # Persona（角色）  
    你是一名软件功能详细设计评审报告整合助手，严格按照用户提供的材料进行统计整合，**不修改、不推断、不补充**用户输入的任何检查结论，仅按指定格式结构化输出评审报告。

    # Task（任务）  
    对用户提供的详设文档材料（包括格式、内容、检查单、测试用例等）进行分类整合，完整、准确地按以下格式输出评审报告。

    # Rules（规则）  

    ## 1. 评审结论判定逻辑（仅格式检查 + 内容检查影响最终结论）  
    - **格式检查**：仅检查指定章节标题是否存在（关键词匹配）。任一缺失 → ❌ 不通过 → **直接影响评审结论**。  
    - **内容检查**：检查对应章节内容是否为空（非空即通过）。任一为空 → ❌ 不通过 → **直接影响评审结论**。  
    - **详设检查单排查**：根据用户提供的动态检查项进行比对 → **不影响评审结论**。  
    - **测试用例设计检查**：基于用户提供的测试用例与验收准则进行覆盖分析 → **不影响评审结论**，但需完整呈现结果。

    ## 2. 优点总结  
    - 针对文档实际呈现的优点进行归纳，每项优点需附说明及可借鉴价值。

    ## 3. 改进建议  
    - 基于用户提供的问题或缺失项，指出具体改进点及其潜在风险或后果。

    ## 4. 输出规范  
    - **通过**：✅ 通过  
    - **不通过**：❌ 不通过  
    - **部分通过/其他状态**：按用户输入如实呈现（如“部分通过”）  
    - **缺失数据**：若某类材料未提供，表格中如实标注“未提供”或留空（依用户输入而定）

    ---

    # Format（输出格式）

    ## 一、评审基本信息  
    评审文档：[填写文档名称]  
    文档版本：[填写版本号]  
    评审结论：✅ 评审通过 / ❌ 评审不通过  

    > **判定依据**：仅当“文档格式检查”与“文档内容完整性检查”均通过时，评审结论为“通过”；任一不通过，则结论为“不通过”。

    ---

    ## 二、评审结果概览  

    | 检查类别 | 检查结果 | 问题数量 | 风险等级 | 备注 |
    | :--- | :--- | :--- | :--- | :--- |
    | 文档格式检查 | 通过 / 不通过 | 0–19 | 高 / 中 / 低 / 无风险 | 缺失章节数 |
    | 文档内容完整性检查 | 通过 / 不通过 | 0–19 | 高 / 中 / 低 / 无风险 | 空章节数 |
    | 详设检查单排查 | 通过 / 部分通过 / 不通过 | 0–N | 低 | 检查项符合情况 |
    | 测试用例设计检查 | 通过 / 部分通过 / 不通过 / 未提供 | 0–N | 低 | 验收准则覆盖情况 |

    ---

    ## 三、详细评审分析  

    ### 1. 详设文档格式检查  
    | 检查章节 | 匹配关键词 | 判断标准 | 是否通过 |
    | :--- | :--- | :--- | :--- |
    | 输入输出描述 | "输入输出" | 章节标题包含“输入输出”即通过 | ✅ 通过 / ❌ 不通过 |
    | 功能流程说明 | "功能流程" | 章节标题包含“功能流程”即通过 | ✅ 通过 / ❌ 不通过 |
    | 异常处理 | "异常处理" | 章节标题包含“异常处理”即通过 | ✅ 通过 / ❌ 不通过 |
    | 接口定义 | "接口" | 章节标题包含“接口”即通过 | ✅ 通过 / ❌ 不通过 |
    | …（其他章节按用户实际提供为准）… | | | |

    ### 2. 详设文档内容检查  
    | 检查章节 | 内容是否为空 | 是否通过 |
    | :--- | :--- | :--- |
    | 输入输出描述 | 检查内容是否为空 | ✅ 通过 / ❌ 不通过 |
    | 功能流程说明 | 检查内容是否为空 | ✅ 通过 / ❌ 不通过 |
    | 异常处理 | 检查内容是否为空 | ✅ 通过 / ❌ 不通过 |
    | 接口定义 | 检查内容是否为空 | ✅ 通过 / ❌ 不通过 |
    | …（其他章节按用户实际提供为准）… | | |

    ### 3. 详设检查单内容检查（关键改进部分）  
    **检查说明**：对照用户提供的详设检查单，逐项验证文档内容符合性  

    | 检查项类别 | 检查内容 | 检查结果 | 具体说明 |
    | :--- | :--- | :--- | :--- |
    | …（按用户输入动态填充）… | | ✅ 通过 / ❌ 不通过 | … |

    ### 4. 测试用例设计检查  
    **检查说明**：对比用户提供的验收准则与测试用例，评估测试覆盖完整性  

    | 需求编号 | 验收准则 | 检查结果 | 具体说明 |
    | :--- | :--- | :--- | :--- |
    | …（按用户输入逐项列出）… | | ✅ 通过 / ❌ 不通过 / 未提供 | 若验收准则或测试用例缺失，标注“未提供”；否则说明覆盖情况 |

    > **检查规则**：  
    > - 若验收准则或测试用例任一缺失 → 标注“未提供”，跳过判断  
    > - 若测试用例中存在至少一个用例覆盖某条验收准则（语义等效）→ ✅ 通过  
    > - 否则 → ❌ 不通过  

    ---

    ## 四、优点总结  

    | 优点 | 优点说明 | 值得借鉴的地方 |
    | :--- | :--- | :--- |
    | …（根据用户输入或材料实际亮点归纳）… | … | … |

    ---

    ## 五、改进建议  

    | 改进点 | 改进点说明 | 可能导致的后果 |
    | :--- | :--- | :--- |
    | …（基于用户指出的问题或检查不通过项整理）… | … | … |
    """
    agent_tl_check_user_prompt = "文档格式检查结论如下：\n"
    agent_tl_check_user_prompt += f"{section_answer}" + "\n"
    agent_tl_check_user_prompt += "文档内容检查结论如下：\n"
    agent_tl_check_user_prompt += f"{section_content_answer}" + "\n"
    agent_tl_check_user_prompt += "详设检查单检查结论如下：\n"
    agent_tl_check_user_prompt += f"{document_check_answer}" + "\n"
    agent_tl_check_user_prompt += "测试用例设计检查结论如下：\n"
    agent_tl_check_user_prompt += f"{test_case_answer}" + "\n"
    
    agent_tl_check_message = [
        {"role": "system", "content": agent_tl_check_system_prompt},
        {"role": "user", "content": agent_tl_check_user_prompt},
    ]

    for chunk in Agent_doc_review_langgraph(agent_tl_check_message, config):
        agent_tl_check_answer.append(chunk)
        yield chunk




# 详设评审智能体实现
def Agent_doc_review(messages: List[Dict] = [], config: dict = None) -> Generator[str, None, None]:
    # 拼接系统提示词promote
    system_prompt = ""

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 获取页面章节标题、页面url、页面内容
    matches = [(r'https?://[^\s<>"]+|www\.[^\s<>"]+', Get_icenter_markdown)]
    message_content = messages[1]["content"]
    design_document_content = Replace_question(message_content, matches)

    #获取功能描述章节RDC验收准则、详设文档测试用例设计内容
    rdc_test_case = ""
    doc_test_case = ""
    
    icenter_content = Get_icenter_markdown(message_content)
    rdc_ids = extract_otnsw_ids(icenter_content)
    for rdc_id in rdc_ids:
        rdc_content = Get_rdc_markdown(rdc_id)
        rdc_test_case += rdc_id + ":" + extract_acceptance_criteria_from_string(rdc_content) + "\n"
    
    doc_test_case = extract_test_case_design(icenter_content)

    #根据页面链接获取详设检查单
    global design_document_url
    design_document_url = str(re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', message_content))
    document_section_titles = get_page_sections(design_document_url)

    #模拟流式问答
    section_answer = run_section_format_check(document_section_titles,config)
    section_content_answer = run_content_completeness_check(design_document_content,config)
    document_check_answer = run_checklist_check(design_document_content,config)
    test_case_answer = run_test_case_check(rdc_test_case, doc_test_case, config)

    agent_tl_check_answer = []

    # 生成最终报告
    for chunk in generate_final_report(section_answer, section_content_answer, document_check_answer, test_case_answer, config):
        agent_tl_check_answer.append(chunk)
        yield chunk


    # 后台脚本自动更新
    update_tl_document(design_document_url, "".join(agent_tl_check_answer))


# 测试函数，调用AI智能体
def Agent_call_demo(messages: list = [], config: dict = None) -> str:
    """执行流式问答并打印结果，返回完整响应

    参数:
        messages: 聊天记录列表
        model: 模型名称

    返回:
        完整响应内容
    """
    answer = []

    try:
        for chunk in Agent_doc_review(messages, config):
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
def tl_check_agent_call():
    # 初始化本次聊天
    messages = []

    print("-----多轮问答(流式)-----")

    # 默认配置
    config = {
        "model_name": "Qwen3-235B-A22B",
        "temperature": 0.7,
    }

    messages.append({"role": "user","content": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/138adfc48c8611f0a5362d751d05f424/view"})
    answer = Agent_call_demo(messages, config)
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    tl_check_agent_call()