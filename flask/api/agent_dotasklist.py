import re
import io
import json
import time
import pandas as pd
from typing import Generator
from bs4 import BeautifulSoup
from ask_ai_request import Ask_ai, Chat_ai_stream
from get_icenter import Icenter_table_update
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown, Get_icenter_html
from api_utils import Replace_question

def Agent_ai_dotasklist(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建    
    system_prompt = "你是一名专业的助手，擅长处理各类事务。"
    if not messages:
        yield system_prompt
        return

    # 健壮性检查：输入是否为字符串
    question = messages[-1]["content"]
    if not isinstance(question, str):
        yield "输入必须为字符串类型\n\n"
        return
    
    matches = [
        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
    ]

    # 定义匹配URL的正则表达式（支持http/https和常见域名格式）
    url_pattern = re.compile(
        r'https?://'  # http:// 或 https://
        r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+'  # 域名
        r'(?::\d+)?'  # 端口号（可选）
        r'(?:/[-\w@:%+.~#?&/=]*)?'  # 路径和查询参数（可选）
    )
    
    # 查找所有URL
    url = url_pattern.findall(question)
    
    # 提取非链接部分（移除所有URL后的剩余文本）
    question_without_url = url_pattern.sub('', question).strip()

    # 检查是否匹配到URL
    if not url:
        yield "请提供任务清单连接\n\n"
        return
        
    # 添加用户的问题到消息列表
    # messages.append({"role": "user", "content": question})

    yield "#### ✅Step1：获取任务模版...\n\n"
    # 1、获取icenter页面内容
    page_replace = Get_icenter_html(url[0])
    # print(page_replace)

    yield "#### ✅Step2：提取任务列表...\n\n"
    # 2、将页面内容表格转存成DataFrame
    # # 提取表格部分（从第二行开始）
    # table_dfs = pd.read_html(io.StringIO(page_replace))

    # 解析 HTML
    soup = BeautifulSoup(page_replace, 'html.parser')

    # 找到所有表格
    tables = soup.find_all('table')

    table_dfs = []
    for table in tables:
        # 提取表格数据（保留链接）
        data = []
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all(['th', 'td']):
                # 检查是否存在链接
                link = cell.find('a')
                if link and link.get('href'):
                    # 保留链接地址
                    row_data.append(link['href'])
                else:
                    # 普通文本内容
                    row_data.append(cell.get_text(strip=True))
            data.append(row_data)
        
        # 创建 DataFrame
        if data:
            # 创建时直接去除列名中的多余空格
            columns = [col.strip() for col in data[0]]
            df = pd.DataFrame(data[1:], columns=columns)            
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            table_dfs.append(df)

    # # 假设只需要第一个表格
    if len(table_dfs) > 0:
        table_df = table_dfs[0]
    else:
        yield ValueError("未在页面中找到任何表格！")
        return

    # 清理列名中的空格和冒号等字符
    table_df.columns = table_df.columns.str.strip()
    table_df = table_df.loc[:, ~table_df.columns.str.contains('Unnamed')] # 去除列名包含Unnamed的
    table_df = table_df[table_df["任务"] != " --- "]
    table_df = table_df.apply(lambda x: x.astype(str).str.strip())
    
    # 3、将DataFrame中的链接替换成页面内容
    table_df["输入"] = table_df["输入"].apply(lambda x: Replace_question(x, matches) if isinstance(x, str) else x)
    
    yield "#### ✅Step3：批量执行任务...\n\n"
    # 4、针对每行任务，获取提示词，组装“输入”+“提示词”内容作为入参，调用Ask_ai接口，将返回值填入“输出”列
    # 获取第一行的提示词作为默认值（假设"提示词"列存在）
    default_prompt = table_df.at[0, '提示词'] if '提示词' in table_df.columns else ''

    # 定义处理每行的函数
    def process_row(row):
        # 获取任务列的值并去除首尾空格
        task_value = str(row.get('任务', '')).strip()
        prompt_value = str(row.get('提示词', '')).strip()

        # 检查任务列是否为"---"或空字符串
        if task_value == "---" or task_value == "" or pd.isna(row.get('任务')):
            return None  # 跳过处理
        
        # 获取当前行的提示词，如果为空则使用默认提示词
        if prompt_value == "---" or prompt_value == "" or pd.isna(row.get('提示词')):
            current_prompt = default_prompt
        else:
            current_prompt = prompt_value

        # print(f"序号：{row['序号']} | 任务:{row['任务']} | 提示词:{row['提示词']}")

        # 组装输入内容（假设"输入"列存在）
        if '输入' in row and pd.notna(row['输入']):
            input_content = f"# 任务：\n\n {row['任务']}\n\n# 上下文：\n\n {row['输入']}\n\n# 要求：\n\n {current_prompt}\n\n"
        else:
            input_content = current_prompt
            
        # print(f"input_content:{input_content}")
        # 调用AI接口获取结果
        try:
            output = Ask_ai(input_content, model)
            print(f"output:{output}")
        except Exception as e:
            output = f"调用AI接口出错：{str(e)}"
        
        # 返回处理后的结果
        return output

    # 初始化输出列
    outputs = []

    # 添加进度提示
    total_tasks = len(table_df)
    yield f"🔍 共检测到 {total_tasks} 个任务，开始逐个处理...\n\n"

    # 逐行处理并 yield 输出
    for idx, row in table_df.iterrows():
        result = process_row(row)

        # 构造要输出的内容
        task_name = row.get("任务", "")
        output_line = f"【任务{idx}】{task_name}：Done!\n\n"

        # 实时 yield 输出
        yield output_line

        # 保存结果用于后续更新表格
        outputs.append(result)

    table_df['输出'] = outputs
    table_df = table_df[table_df["任务"] != ""]

    # 打印处理后的DataFrame
    # print(table_df.to_string())
    # print(table_df.to_json(orient='records', force_ascii=False, indent=2))

    # 5、将数据可视化显示出来
    # table_df.to_csv('output.csv', index=False)
    # table_df.to_excel('output.xlsx', index=False)
    # table_df.to_json('output.json', orient='records', force_ascii=False, indent=2)
    # table_df.to_excel('output.xlsx', index=False)
    # result = table_df.to_markdown(tablefmt='pipe', index=False)
    result = table_df.to_json(orient='records', force_ascii=False, indent=2)

    yield "#### ✅Step4：任务处理结果回填...\n\n"
    # 更新对应页面的tasklist输出列
    Icenter_table_update(url[0], result)

    # yield "#### ✅Step5：任务处理结果总结...\n\n"
    # 重组问题，让AI进行最后的总结，提升回答的效果
    # question = result + "\n" + "# " + question_without_url
    # answer = Ask_ai(question, model)

    # for char in answer:
    #     yield char

    # yield "\n\n"
    yield "#### ✅Done：全部任务处理完成!\n\n"
    return

def Agent_demo(messages: list, model: str = "qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_dotasklist(messages, model):
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
    question = """
        https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/a0742be79ec64f98b33c184366956cfd/view  
        帮我处理
        """
    
    messages = [
        {"role": "system", "content": "你是一个专业的助手"},
        {"role": "user", "content": question}
    ]

    # print("-----单词问答-----")
    # print(Agent_dotasklist(question, messages, "qwen"))
    
    print("-----多轮问答(流式)-----")
    response = Agent_demo(messages, "qwen")
