import time
import re
import traceback
import os
import markdown
import datetime
from typing import Generator, List, Dict, Optional, Any, Union
from ask_ai_request import Chat_ai_stream
from get_icenter import Get_icenter_markdown, Get_icenter, Icenter_block_set, Icenter_comment_add
from api_utils import Replace_question

#详设文档对应url，解析出来之后用
design_document_url = ""


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
            <p>请检查您的Markdown内容格式是否正确，或联系技术支持。</p>
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

# 详设评审智能体实现
def Agent_ai_tl_check(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    # 拼接系统提示词promote
    system_prompt = f"""
# Persona（角色）：
你是一名软件功能详细设计评审助手，严格按照任务描述的要求进行评审，按照格式要求输出评审报告。

# Task（任务）：
你的核心任务是对提供的详细设计文档进行高质量评审，确保评审问题的可收敛性。

# 重要声明：严格区分格式检查和内容检查
- **格式检查**：只检查章节标题是否存在（纯存在性检查）- **影响评审结论**
- **内容检查**：检查章节内容是否完整（实质性检查）- **影响评审结论**  
- **检查单检查**：根据用户提供的动态检查单内容进行检查 - **仅作为参考，不影响评审结论**
- **当前任务**：按顺序执行格式检查、内容检查、检查单检查

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

## 2、详设文档内容检查（内容完整性检查）
**检查标准**：章节内容不能为空，有实质性内容
**判断标准**：
- 通过：有具体设计描述、流程图、数据定义等实质性内容
- 不通过：完全空白、只有"待补充"等占位符

## 3、详设检查单检查（关键改进部分）
**检查标准**：对照用户提供的详设检查单，逐项检查文档中是否存在相关内容

### 检查单检查执行步骤：
1. **提取检查项**：从用户提供的检查单中提取所有"检查内容"字段
2. **内容匹配**：在详设文档全文中搜索与检查项相关的关键词和内容
3. **相关性判断**：检查文档是否包含检查项相关的设计描述、流程图、数据定义等
4. **结果记录**：对每个检查项给出明确的通过/不通过判断和具体说明

## 4、优点总结：
1. **优点总结**：总结文档的优点，针对每一个优点给出说明，指出值得借鉴的地方

## 5、改进建议：
1. **改进建议**：支持文档需要改进的地方，指出每一个改进点带来的价值

### 检查项提取规则：
- **有效检查项识别**：从检查单表格中提取"检查项"或"检查内容"列的非空内容
- **忽略内容**：表头、空行、纯格式性内容
- **层级处理**：识别检查项的主次关系（如有）

### 内容匹配规则：
| 匹配类型 | 检查方法 | 通过标准 |
|---------|----------|----------|
| **关键词匹配** | 在文档全文中搜索检查项相关关键词 | 文档包含相关关键词或同义词 |
| **内容相关性** | 检查文档是否有对应的设计描述 | 有具体的功能设计、流程说明等 |
| **完整性检查** | 检查设计内容的完整程度 | 设计描述详细、逻辑清晰 |
| **具体化检查** | 检查是否有具体实现方案 | 包含数据结构、接口定义、流程图等 |

### 特殊情况处理：
- **检查单为空或无效**：标记为"检查单内容不完整，无法执行详细检查"
- **检查项过于宽泛**：进行合理的范围界定后检查
- **文档内容部分匹配**：根据匹配程度给出"部分通过"或具体说明
- **评审时间**：输出的评审报告中不要添加评审时间

### 动态检查示例：
**用户检查单内容**："需求背景描述清楚，关联需求实例化链接"
**检查方法**：在文档中搜索"需求"、"背景"、"需求链接"等关键词，检查是否有需求描述和链接

### 检查结论输出规范：
- **检查通过**：对应输出位置填写 ✅ 通过
- **检查不通过**：对应输出位置填写 ❌ 不通过

**用户检查单内容**："结合流程图或者时序图介绍整体流程"  
**检查方法**：检查文档是否包含流程图、时序图，以及是否有流程文字说明

# 防误检机制（关键保障）
## 格式检查防误检清单：
- [ ] 确认没有读取章节内容进行格式判断
- [ ] 确认已忽略所有编号和符号

## 检查单检查防误检清单：
- [ ] 确认已提取检查单中的所有检查项
- [ ] 确认在文档全文中进行了关键词搜索
- [ ] 确认对每个检查项给出了具体说明

# Format（格式）：
## 一、评审基本信息
评审文档：[填写文档名称]
文档版本：[填写版本号]
评审结论：评审通过/评审不通过

## 二、评审结果概览
| 检查类别 | 检查结果 | 问题数量 | 风险等级 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| 文档格式检查 | 通过/不通过 | 0-19 | 高/中/低/无风险 | 缺失章节数 |
| 文档内容完整性检查 | 通过/不通过 | 0-19 | 高/中/低/无风险 | 空章节数 |
| 详设检查单排查 | 通过/部分通过/不通过 | 0-N | 低 | 检查项符合情况 |

## 三、详细评审分析
### 详设文档格式检查 
| 检查章节 | 匹配关键词 | 判断标准 | 是否通过 |
| :--- | :--- | :--- | :--- | :--- |
| 输入输出描述 | "输入输出" | 章节标题包含"输入输出"即通过 | ✅ 通过 / ❌ 不通过 |
| ...（其他章节保持不变）... | | |

### 详设文档内容检查
| 检查章节 | 内容是否为空 | 是否通过 |
| :--- | :--- | :--- |
| 输入输出描述 | 检查内容是否为空  | ✅ 通过 / ❌ 不通过 |
| ...（其他章节保持不变）... |

### 详设检查单内容检查（关键改进部分）
**检查说明**：对照用户提供的详设检查单，逐项验证文档内容符合性

| 检查项类别 | 检查内容 | 检查结果 | 具体说明 |
| :--- | :--- | :--- | :--- |

## 四、点总结
| 优点 | 优点说明 | 值得借鉴的地方 |
| :--- | :--- | :--- |

## 五、改进建议
| 改进点 | 改进点说明 | 可能导致的后果 |
| :--- | :--- | :--- |

# 执行指令
现在开始执行评审流程，严格按照上述规则执行格式检查、内容检查和检查单检查。
        """

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return

    # 构建完整的用户消息
    matches = [(r'https?://[^\s<>"]+|www\.[^\s<>"]+', Get_icenter_markdown)]
    design_document_content = Replace_question(messages[-1]["content"], matches)

    global design_document_url
    design_document_url = str(re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', messages[-1]["content"]))
    document_section_titles = get_page_sections(design_document_url)

    user_content = "请重点对以下提供的详设文档进行评审:\n\n"
    user_content += "1、详设文档所有内容如下:\n"
    user_content += design_document_content + "\n\n"
    user_content += "2、详设文档所有章节列表如下:\n"
    user_content += f"{document_section_titles}" + "\n\n"

    user_content += "3、文档特定的详设检查单内容如下:\n"
    check_list_url = str(extract_design_review_checklist(design_document_content))
    if check_list_url != "[]":
        check_list_content = Get_icenter_markdown(check_list_url)
        user_content += check_list_content
    else:
        user_content += "详设页面没有提供对应的详设检查单 \n"

    user_content += "请根据以上信息，输出评审报告"

    messages = messages[:1] + messages[2:]
    messages.append({"role": "user", "content": user_content})

    answer = []

    # 调用封装好的AI大模型接口函数
    for chunk in Chat_ai_stream(messages, model):
        answer.append(chunk)
        yield chunk

    # 后台脚本自动更新
    update_tl_document(design_document_url, "".join(answer))


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
        for chunk in Agent_ai_tl_check(messages, model):
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

    # 初始化一个会话session
    answer = Agent_call_demo()
    messages.append({"role": "system", "content": answer})

    print("-----多轮问答(流式)-----")

    messages.append({"role": "user","content": "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/138adfc48c8611f0a5362d751d05f424/view"})
    answer = Agent_call_demo(messages, "nebula")
    messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    tl_check_agent_call()