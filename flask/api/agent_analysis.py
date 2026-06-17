
import time
import sqlite3
from pathlib import Path
from typing import Generator
from ask_ai_request import Chat_ai_stream
from datetime import datetime

def Agent_ai_analysis(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    db_file = Path(__file__).parent.parent / 'data' / 'rdc.db'
    print(db_file)
    db_table = 'bug_table'
    max_retries = 3  # SQL执行失败时的最大重试次数
    current_date = datetime.now().strftime("%Y-%m-%d")
    system_prompt = "你是一名专业的数据分析师，精通SQL语言，根据表结构和用户问题生成SQL查询语句。"

    # 如果messages未传入参数，则使用默认系统提示词，并将系统提示词返回，表示会话已创建
    if not messages:
        yield system_prompt
        return
    
    # 表结构描述（用于AI生成SQL）
    TABLE_SCHEMA = f"""
    表名: {db_table}
    字段说明:
    1. 标识 - 主键 (TEXT)
    2. 主题 - 故障主题描述 (TEXT)：关键信息！包含一些核心的名词，可以作为模糊匹配的首要参考字段。
    3. 描述 - 故障详细描述 (TEXT)：详细描述故障现象、故障发现版本、复现步骤等信息。
    4. 开发复盘负责人 (TEXT)：姓名+工号，进行复盘的责任人。
    5. 缺陷等级 (TEXT)：主要包含A/B/C/D四个等级。A级为致命问题，B级为严重问题，C级为一般问题，D为轻微问题。
    6. 发现活动 (TEXT)：主要包含系统测试、领域测试、集成测试、方案测试等。
    7. 发现方法 (TEXT)：主要包含手工测试、自动化测试
    8. 提交日期 - 格式YYYY-MM-DD (TEXT)：故障提交的时间，通常与时间相关的统计均参考此字段。
    9. 关闭日期 - 格式YYYY-MM-DD (TEXT)：故障关闭的时间。
    10. 故障引入人 (TEXT)：姓名+工号，编码引入此故障的具体人。
    11. 引入点所属领域 (TEXT)：关键信息！引入故障的领域，主要包括：支撑领域、L2领域、L0领域、L1领域、智控领域。也可以简称：L0、L1、L2、支撑、智控。
    12. 引入点所属团队 (TEXT)：关键信息！引入故障的团队。所有提及团队的问题均重点参考此字段信息。
    13. 技术根因分析 (TEXT)：关键信息！包含机理分析（5W），修改方案，波及分析，风险评估等关键内容。
    14. 引入来源 (TEXT)：主要包括老需求首次发现，新需求首次发现，修改引入。
    15. 故障引入点根因一级分类 (TEXT)：主要包括：需求、方案、详设、编码、版本构建。常说的需求故障，还是编码故障，就通过此判断。
    16. 故障引入点根因二级分类 (TEXT)：主要是对一级根因的细分。
    17. 故障引入点根因三级分类 (TEXT)：主要是一些自定义分类。
    18. 故障引入gerrit入库链接 (TEXT)
    19. 一级特性 (TEXT)：关键信息！故障泄露所归属的特性。如果问xx类故障优先参考这个字段。
    20. 二级特性 (TEXT)：主要是对一级特性的细分。
    21. 引入点复盘状态 (TEXT)
    22. 最早可拦截阶段 (TEXT)
    23. 自测无法拦截的原因 (TEXT)
    24. 代码走查未拦截原因 (TEXT)
    25. 代码走查未拦截原因说明 (TEXT)
    26. 是否可通过补充代码UT/FT拦截 (TEXT)
    27. 是否可通过补充仿真FT拦截 (TEXT)
    28. 是否可通过补充硬件FT/流水线FT拦截 (TEXT)
    29. 故障定界定位方式 (TEXT)
    30. 是否需要复现定位或者占用环境定位 (TEXT)
    31. 定位时长 (TEXT)
    32. 控制点复盘状态 (TEXT)
    33. 引入点改进举措 (TEXT)
    34. 控制点改进举措 (TEXT)
    """
    
    # 获取用户最后一个问题
    user_question = messages[-1]["content"] if messages else ""

    # ====== Step 1: 自然语言转SQL ======
    yield "#### ✅Step1：自然语言提问内容转SQL...\n\n"

    sql_prompt = f"""
    你是SQL专家，根据表结构和用户问题生成SQL查询语句。注意只允许对数据库的查询操作，不允许任何修改操作。优先采用模糊匹配来查询。
    
    当前日期：{current_date}（用于时间计算参考）。
    表结构信息:
    {TABLE_SCHEMA}
    
    用户问题："{user_question}"
    
    要求：
    1. 只输出SQL语句，不要包含任何解释
    2. 使用SQLite兼容语法
    3. 表名和字段名用双引号包裹
    4. 日期处理使用DATE函数
    5. 确保只生成SELECT查询

    经验：
    1. 如果问题是xx类故障，可以在故障引入点根因一级分类，故障引入点根因二级分类、故障引入点根因三级分类 中使用模糊匹配查找。注意：问题中的一些术语需要转义：a.<详设>转成<详细设计>。b.<方案>转成<方案设计>。
    2. 如果问题是xx特性故障，可以依次在一级特性、二级特性 中使用模糊匹配查找。
    3. 如果问题是xx领域故障，可以在引入点所属领域 中使用模糊匹配查找。
    4. 如果问题是xx团队故障，可以在引入点所属团队 中使用模糊匹配查找。
    """
    
    # 创建SQL生成专用消息
    sql_messages = [
        {"role": "system", "content": "你是SQL专家，根据用户问题和表结构生成SQL语句"},
        {"role": "user", "content": sql_prompt}
    ]
    
    # 流式生成SQL
    yield "> SQL生成成功："
    sql_response = ""
    for chunk in Chat_ai_stream(sql_messages, model):
        # yield chunk
        sql_response += chunk

    # 提取SQL语句（移除可能的代码块标记）
    sql = sql_response.strip().replace("```sql", "").replace("```", "").strip()
    yield f"{sql}\n\n"

    # ====== Step 2: 执行SQL（含重试机制） ======
    yield "#### ✅Step2：执行SQL...\n\n"

    result = None
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 安全校验：只允许SELECT查询
            if not sql.strip().upper().startswith("SELECT"):
                raise ValueError("只允许执行SELECT查询语句")
                
            cursor.execute(sql)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = {"columns": columns, "data": results}
            conn.close()
            yield f"> SQL执行成功：{result}\n\n"
            break  # 执行成功则退出重试循环
            
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                # 生成错误修正提示
                error_prompt = f"""
                上次生成的SQL执行失败，错误信息：{error_msg}
                请修正SQL语句，确保符合SQLite语法和表结构
                原始用户问题："{user_question}"
                失败SQL：{sql}
                """
                sql_messages.append({"role": "assistant", "content": sql})
                sql_messages.append({"role": "user", "content": error_prompt})
                
                # 重新生成SQL
                yield f"SQL生成重试(第{attempt}次)："
                sql_response = ""
                for chunk in Chat_ai_stream(sql_messages, model):
                    yield chunk
                    sql_response += chunk
                yield "\n\n"

                sql = sql_response.strip().replace("```sql", "").replace("```", "").strip()
            else:
                result = {"error": f"SQL执行失败（尝试{max_retries}次）: {error_msg}"}
                yield f"SQL执行失败（尝试{max_retries}次）: {error_msg}\n\n"
                break

    # ====== Step 3: SQL结果转自然语言 ======
    yield "#### ✅Step3：SQL查询结果转自然语言...\n\n"
    if "error" in result:
        # 直接返回错误信息
        yield f"查询失败: {result['error']}\n\n"
        return

    # 准备结果解释提示
    nl_prompt = f"""
    用户原始问题："{user_question}"
    
    数据库返回结果：
    - 字段列表：{result['columns']}
    - 数据样例（前100行）: {result['data'][:100] if len(result['data']) > 3 else result['data']}
    - 总行数：{len(result['data'])}
    
    请用自然语言解释查询结果：
    1. 简洁明了，突出重点
    2. 发现异常值或趋势时给出提示
    """
    
    # 创建结果解释专用消息
    nl_messages = [
        {"role": "system", "content": "你是数据分析师，用自然语言解释SQL查询结果"},
        {"role": "user", "content": nl_prompt}
    ]
    
    # 流式生成自然语言解释
    yield "SQL查询结果："
    for chunk in Chat_ai_stream(nl_messages, model):
        yield chunk
    yield "\n\n"

    yield "#### ✅Done：全部任务处理完成!\n\n"

    # 将完整的回答追加到 messages 中
    # full_answer = ''.join(answer)
    # messages.append({"role": "assistant", "content": full_answer})


# 假设的AI流式调用函数（需根据实际API实现）
# def Chat_ai_stream(messages: List[Dict[str, str]], model: str) -> Generator[str, None, None]:
#     # 这里应该是调用实际AI API的代码
#     # 示例：模拟流式返回
#     yield "思考中..."
#     yield "最终响应"


def Agent_ai_demo(messages, model="qwen") -> str:
    """执行流式问答并打印结果，返回完整响应
    
    参数:
        messages: 聊天记录列表
        model: 模型名称
        
    返回:
        完整响应内容
    """
    answer = []
    
    try:
        for chunk in Agent_ai_analysis(messages, model):
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
    question = "你好"
    
    messages = [
        {"role": "system", "content": "你是一个专业的助手"},
    ]
    
    # print("-----多轮问答(流式)-----")
    # messages.append({"role": "user", "content":"你好"})
    # Agent_ai_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"世界最高山是什么？不用回答其他内容，直接告诉我答案就行。"})
    # Agent_ai_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"第二高的呢。"})
    # Agent_ai_demo(messages, "qwen")

    # messages.append({"role": "user", "content":"第三高的呢。"})
    # Agent_ai_demo(messages, "qwen")

    question = "请帮我查询 【引入点所属领域】包含 L2 的数据有多少条？"
    question = "请帮我查询 【引入点所属领域】包含 L2 的故障今年有多少？"
    question = "请帮我查询 【引入点所属领域】包含 支撑 的故障有多少？"
    question = "请将集结号团队25年全部故障的根因分析提取出来，并整理分析主要根因有哪些。"

    print("-----数据分析(流式)-----")
    messages.append({"role": "user", "content":question})
    Agent_ai_demo(messages, "qwen")
    print(messages)
