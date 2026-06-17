import os
import json
import uuid
import time
import sqlite3
from datetime import datetime
from urllib.parse import unquote
from flask import request, jsonify, Response
from ask_ai_request import Ask_ai, Chat_ai_stream
from get_rdc import Get_rdc_markdown
from get_icenter import Get_icenter_markdown
from api_utils import Replace_question, Get_username

from agent_dotasklist import Agent_ai_dotasklist
from agent_analysis import Agent_ai_analysis
from agent_demo import Agent_ai_demo
from agent_dnstdio import Agent_ai_dnstdio, Agent_ai_dnstdio_basic, Agent_ai_dnstdio_Fz, Agent_ai_dnstdio_Md, General_Agent_ai_dnstdio_basic, Agent_ai_dnstdio_contentEval
from agent_dnstdio_demo import Agent_ai_dnstdio_demo
from agent_coder import Agent_ai_l2_mvp_coder
from agent_bugdiag import Agent_ai_bugdiag
from agent_autowork import Agent_ai_autowork
from agent_se import Agent_ai_se
from agent_tl import Agent_ai_tl
from agent_tl_check import Agent_ai_tl_check
from agent_component import Agent_ai_component, Agent_ai_componentNew
from agent_module import Agent_ai_component_new
from agent_chat import Agent_ai_chat_doc, Agent_ai_chat
from agent_search import Agent_ai_search
from agent_bug import Agent_ai_bug
from agent_lg_chat import Agent_langgraph_chat, Agent_langgraph_superchat
from agent_doc_review import Agent_doc_review
from agent_lg_ft import Agent_ft_langgraph
from deal_health import Agent_ai_health


# 定义 agent 处理函数的映射表
AGENT_MAP = {
    "DoTaskListAgent":    (Agent_ai_dotasklist, "批量任务智能体"),
    "BugAnalysisAgent":   (Agent_ai_analysis, "故障复盘数据分析智能体"),
    "BugDiagAgent":       (Agent_ai_bugdiag, "故障诊断智能体"),
    "DeepResearchAgent":  (Agent_ai_autowork, "深度研究智能体"),
    "L2MvpAgent":         (Agent_ai_l2_mvp_coder, "L2领域MVP智能体"),
    "DNstdioAgent":       (Agent_ai_dnstdio, "DNstdio智能体"),
    "CustomerAgent":      (Agent_ai_demo, "自定义智能体"),
    # "BaAgent":            (Agent_ai_ba, "需求分析智能体"),
    "BaAgent":            (Agent_ai_dnstdio_demo, "需求分析智能体"),
    "SeAgent":            (Agent_ai_se, "方案设计智能体"),
    "TlAgent":            (Agent_ai_tl, "详细设计智能体"),
    "ChatAgent":          (Agent_ai_chat_doc, "文档知识问答智能体"),
    "iCenterSearchAgent": (Agent_ai_search, "空间搜索智能体"),
    "ComponentAgent":     (Agent_ai_component, "组件智能体"),
    "ModuleAgent":        (Agent_ai_component_new, "模块智能体"),
    "BoardAgent":         (Agent_ai_component_new, "单板智能体"),
    "ComponentAgentNew":  (Agent_ai_componentNew, "新组件智能体"),
    "TlCheckAgent":       (Agent_ai_tl_check, "详设评审智能体"),
    "DNstdioBasicAgent":  (Agent_ai_dnstdio_basic, "DNstdio-通用智能体"),
    "DNstdioFzAgent":     (Agent_ai_dnstdio_Fz, "DNstdio-光层仿真单板模型生成"),
    "DNstdioMdAgent":     (Agent_ai_dnstdio_Md, "DNstdio-光层仿真modeldata生成"),
    "DNstdioCntEvalAgent": (Agent_ai_dnstdio_contentEval, "DNstdio-内容域测评"),
    "BugAgent":           (Agent_ai_bug, "故障助手"),
    "DN":                 (General_Agent_ai_dnstdio_basic, "通用DNstdio智能体"),
    "HealthDiagnosisAgent": (Agent_ai_health, "网元健康体检智能体")
}

# 定义 Langgraph框架 agent智能体处理函数的映射表
REACT_AGENT_MAP = {
    "BasicChatAgent":     (Agent_langgraph_chat, "基础AI助手"),
    "SuperChatAgent":     (Agent_langgraph_superchat, "超级AI助手"),
    "DocReviewAgent":     (Agent_doc_review, "组件设计评审助手"),
    "FtAgent":            (Agent_ft_langgraph, "FT生成智能体"),
}

# 定义前端页面名到后端page_now字段值的映射
PAGE_MAPPING = {
    "场景树": "/knowledge/scene",
    "特性树": "/knowledge/feature",
    "组件树": ["/knowledge/component", "/knowledge/component2"],  # 组件树对应两个页面地址
    "单板树": ["/knowledge/board","/knowledge/boardpro","/knowledge/boardmax"],
    "硬件树": "/knowledge/device",  # 硬件树匹配/knowledge/device开头的所有路径
    "需求库": "/knowledge/generalKnowledge/requirement",
    "故障库": "/knowledge/generalKnowledge/issue",
    "代码库": "/knowledge/generalKnowledge/repo",
    "命令库": "/knowledge/generalKnowledge/api",
    "AI助手": "/ai/chat",
    "单板助手": "/ai/boardChat",
    "智能诊断助手": "/ai/diag",
    "故障处理助手": "/ai/issueProcess",
    "代码生成助手": ["/ai/genCode","/ai/code/genCode"],
    "故障波及助手": "/ai/issueImpacte"
}

def Ask():
    return

def Agent():
    try:
        # 1. 解析请求数据（原有逻辑）
        # 获取自定义头中的用户名（需要解码，因为前端可能进行了encodeURIComponent处理）
        user_id = unquote(request.headers.get('X-User-Name', ''))

        # 获取Authorization头中的token（格式通常为Bearer <token>）
        auth_header = request.headers.get('Authorization', '')
        user_token = auth_header.split('Bearer ')[-1] if auth_header.startswith('Bearer ') else ''
        
        # 打印获取到的信息
        print(f"获取到的用户信息 - user: {user_id}, user_token: {user_token}")

        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        request_id = data.get("request_id")
        if not request_id:
            return jsonify({"error": "Missing request_id"}), 400

        # 构建用户消息
        message = {
            "user": data.get("user"),
            "session_id": session_id,
            "request_id": request_id,
            "model": data.get("model"),
            "agent": data.get("agent"),
            "knowledge": data.get("knowledge"),
            "icenter": data.get("icenter"),
            "rdc": data.get("rdc"),
            "think": data.get("think"),
            "role": "user",
            "origin": data.get("content"),
            "content": data.get("content"),
            "context": data.get("context"),
            "component": data.get("component"),
        }

        # 2. 检查是否已有会话历史，若无则初始化 system 消息
        chatitem = chat_item_read(session_id)  # 返回消息列表

        need_system_prompt = not chatitem
        chat_history = chatitem if chatitem else []

        # 如果是新会话，插入 system 消息
        if need_system_prompt:
            system_message = message.copy()
            system_message["role"] = "system"
            system_message["origin"] = ""

            if message["agent"] in REACT_AGENT_MAP:
                agent_handler, agent_name = REACT_AGENT_MAP[message["agent"]]
                print(f"[{agent_name}]正在初始化 system prompt...")

                config = {}
                config["user_id"] = user_id
                config["user_token"] = user_token
                config["model"] = message["model"]
                config["context"] =  message["context"]
                config["knowledge"] =  message["knowledge"]
                config["session_id"] =  message["session_id"]
                config["request_id"] =  message["request_id"]
                
                system_prompt_parts = agent_handler([], config)
                system_content = ''.join(system_prompt_parts)
                system_message["content"] = system_content

            elif message["agent"] in AGENT_MAP:
                agent_handler, agent_name = AGENT_MAP[message["agent"]]
                print(f"[{agent_name}]正在初始化 system prompt...")
                config = {}
                config["context"] = message["context"]
                config["knowledge"] = message["knowledge"]
                system_prompt_parts = agent_handler(None, config)
                system_content = ''.join(system_prompt_parts)
                system_message["content"] = system_content

            else:
                print(f"[通用AI智能体]正在初始化 system prompt...")
                config = {}
                config["context"] = message["context"]
                config["knowledge"] = message["knowledge"]
                system_prompt_parts = Agent_ai_chat([], config)
                system_content = ''.join(system_prompt_parts)
                system_message["content"] = system_content

            # 保存 system 消息
            chat_item_save(system_message)
            chat_history.append(system_message)

        # 3. 预处理用户输入（如替换链接、工单号等）

        # 4. 保存用户消息
        chat_item_save(message)
        chat_history.append(message)

        # 5. 开始流式生成 AI 响应
        def generate_response():
            answer_chunks = []
            try:
                if message["agent"] in REACT_AGENT_MAP:
                    agent_handler, agent_name = REACT_AGENT_MAP[message["agent"]]
                    print(f"[{agent_name}]正在进行 AI 回答...")

                    # 从chat_history中提取role和content字段组成messages列表
                    messages = []
                    for item in chat_history:
                        messages.append({
                            "role": item.get("role", ""),
                            "content": item.get("content", "")
                        })
                    
                    config = {}
                    config["user_id"] = user_id
                    config["user_token"] = user_token
                    config["model"] = message["model"]
                    config["context"] =  message["context"]
                    config["knowledge"] =  message["knowledge"]
                    config["session_id"] =  message["session_id"]
                    config["request_id"] =  message["request_id"]

                    for chunk in agent_handler(messages, config):
                        answer_chunks.append(chunk)
                        for char in chunk:
                            yield f"data: {json.dumps({'text': char})}\n\n"
                            # 可选：控制输出速度
                            time.sleep(0.02)

                elif message["agent"] in AGENT_MAP:
                    agent_handler, agent_name = AGENT_MAP[message["agent"]]
                    print(f"[{agent_name}]正在进行 AI 回答...")
                    for chunk in agent_handler(chat_history, message["context"]):
                        answer_chunks.append(chunk)
                        for char in chunk:
                            yield f"data: {json.dumps({'text': char})}\n\n"
                            # 可选：控制输出速度
                            # time.sleep(0.01)
                else:
                    print("[通用AI智能体]正在进行 AI 回答...")
                    matches = [
                        (r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown),
                        (r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown),
                    ]
                    
                    chat_history[-1]["content"] = Replace_question(chat_history[-1]["content"], matches)
                    
                    for chunk in Chat_ai_stream(chat_history, chat_history[-1]["model"]):
                        answer_chunks.append(chunk)
                        for char in chunk:
                            yield f"data: {json.dumps({'text': char})}\n\n"

                # 拼接完整回答
                final_answer = ''.join(answer_chunks)

                # 构造 assistant 消息并保存
                assistant_message = message.copy()
                assistant_message["role"] = "assistant"
                assistant_message["content"] = final_answer
                assistant_message["origin"] = final_answer

                chat_item_save(assistant_message)

                # 发送结束标记
                yield f"data: [DONE]\n\n"
                print("AI回答完毕！")

            except Exception as e:
                error_msg = f"生成回答时出错：{str(e)}"
                print(error_msg)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"

        return Response(generate_response(), mimetype='text/event-stream')

    except Exception as e:
        print(f"Agent 接口异常：{e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def Chat():
    chat_db_init()

    try:
        # 获取自定义头中的用户名（需要解码，因为前端可能进行了encodeURIComponent处理）
        user_id = unquote(request.headers.get('X-User-Name', ''))

        # 获取Authorization头中的token（格式通常为Bearer <token>）
        auth_header = request.headers.get('Authorization', '')
        user_token = auth_header.split('Bearer ')[-1] if auth_header.startswith('Bearer ') else ''
        
        # 打印获取到的信息
        print(f"获取到的用户信息 - user: {user_id}, user_token: {user_token}")

        data = request.json
        matches = []

        # 构建消息对象
        message = {
            "user": data.get("user"),
            "session_id": data.get("session_id"),
            "model": data.get("model"),
            "agent": data.get("agent"),
            "knowledge": data.get("knowledge"),
            "icenter": data.get("icenter"),
            "rdc": data.get("rdc"),
            "think": data.get("think"),
            "role": "user",
            "content": data.get("content"),
            "origin": data.get("content"),
            "component": data.get("component"),
            "context": data.get("context")
        }

        if message["agent"] == "ComponentAgent":
            agent_handler, agent_name = AGENT_MAP[message["agent"]]
            print(f"正在进行 CHAT {agent_name} 处理...")

            if not chat_item_read(message["session_id"]):
                config = {}
                config["component"] = message["component"]
                config["context"] = message["context"]
                
                system_prompt = agent_handler(None, config)
                content = ''.join(system_prompt)

                system_message = message.copy()
                system_message["role"] = "system"
                system_message["content"] = content
                system_message["origin"] = content
                chat_item_save(system_message)

        elif message["agent"] in AGENT_MAP:
            agent_handler, agent_name = AGENT_MAP[message["agent"]]
            print(f"正在进行 CHAT {agent_name} 处理...")

            if not chat_item_read(message["session_id"]):
                system_prompt = agent_handler()
                content = ''.join(system_prompt)

                system_message = message.copy()
                system_message["role"] = "system"
                system_message["content"] = content
                system_message["origin"] = content
                chat_item_save(system_message)

        elif message["knowledge"] != 'NoneKnowledge':
            print(f"正在进行 Chat 知识问答模式...")

            if not chat_item_read(message["session_id"]):
                system_prompt = Agent_ai_chat_doc(None, message["knowledge"], None)
                content = ''.join(system_prompt)

                system_message = message.copy()
                system_message["role"] = "system"
                system_message["content"] = content
                system_message["origin"] = content
                chat_item_save(system_message)

        else:
            print("正在进行 Chat 问答模式...")

            if not chat_item_read(message["session_id"]):
                system_prompt = Chat_ai_stream()
                content = ''.join(system_prompt)

                system_message = message.copy()
                system_message["role"] = "system"
                system_message["content"] = content
                system_message["origin"] = content
                chat_item_save(system_message)

            if message.get("icenter"):
                matches.append((r"https://i\.zte\.com\.cn/[^\s<>\"']*", Get_icenter_markdown))

            if message["rdc"]:
                matches.append((r'\bOTN[A-Z]{2}-\d+\b', Get_rdc_markdown))

            message["content"] = Replace_question(message["content"], matches)

        # 保存用户输入到数据库
        chat_item_save(message)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def Sse():
    user_id = unquote(request.args.get('user', ''))
    user_token = unquote(request.args.get('user_token', ''))
    session_id = request.args.get('session_id')  # 从 URL 查询字符串中取 session_id
    
    # 打印获取到的信息
    print(f"SSE接口获取到的用户信息 - user: {user_id}, user_token: {user_token}")

    if not session_id:
        return jsonify({"error": "Invalid or missing session_id"}), 400

    # 获取聊天历史记录
    chatitem = chat_item_read(session_id)  # 返回格式：[{"role": "...", "content": "..."}, ...]

    if not chatitem:
        return jsonify({"error": "No chat history found"}), 400

    question = chatitem[-1]
  
    def generate():
        try:
            answer_chunks = []
            if question["agent"] in AGENT_MAP:
                agent_handler, agent_name = AGENT_MAP[question["agent"]]
                print(f"正在进行 SSE {agent_name}...")
                for chunk in agent_handler(chatitem, question["model"]):
                    answer_chunks.append(chunk)
                    # 将chunk拆分成单个字符并逐个发送
                    for char in chunk:
                        # 发送单个字符
                        yield f"data: {json.dumps({'text': char})}\n\n"
                        # time.sleep(0.02)  # 控制逐字输出速度

            elif question["knowledge"] != 'NoneKnowledge':
                print("正在进行 SSE 知识问答模式...")
                for chunk in Agent_ai_chat_doc(chatitem, question["knowledge"], question["model"]):
                    answer_chunks.append(chunk)
                    
                    # 将chunk拆分成单个字符并逐个发送
                    for char in chunk:
                        # 发送单个字符
                        yield f"data: {json.dumps({'text': char})}\n\n"
                        time.sleep(0.02)  # 控制逐字输出速度

            else:
                print("正在进行 SSE 问答模式...")
                for chunk in Chat_ai_stream(chatitem, question["model"]):
                    answer_chunks.append(chunk)
                    
                    # 将chunk拆分成单个字符并逐个发送
                    for char in chunk:
                        # 发送单个字符
                        yield f"data: {json.dumps({'text': char})}\n\n"
                        # time.sleep(0.05)  # 控制逐字输出速度


            # 最终拼接完整回复并保存
            answer = ''.join(answer_chunks)
            
            # 更新 last_chatitem
            question["role"] = "assistant"
            question["content"] = answer
            question["origin"] = answer

            # 保存到数据库
            chat_item_save(question)

            yield f"data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

def Template():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, subtitle, content FROM templates ORDER BY created_at ASC')
            rows = cursor.fetchall()

            # 构造成 JSON 格式
            templates = [{"id": row[0], "title": row[1], "subtitle": row[2], "content": row[3]} for row in rows]

            return jsonify({"status": "success", "templates": templates})
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def History():
    try:
        # 从请求参数中获取 user 值
        user = request.args.get('user')

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if user:  # 如果 user 是非空字符串，按 user 过滤
                cursor.execute('''
                    SELECT request_id, session_id, role, origin, timestamp, user, agent, model 
                    FROM chat_list 
                    WHERE user = ?
                    ORDER BY timestamp DESC
                ''', (user,))
            else:  # 如果 user 是 None 或空字符串，只返回 user 不为空的记录
                cursor.execute('''
                    SELECT request_id, session_id, role, origin, timestamp, user, agent, model
                    FROM chat_list 
                    WHERE user IS NOT NULL AND user != ''
                    ORDER BY timestamp DESC
                ''')
            
            rows = cursor.fetchall()

        # 构造成 JSON 格式
        chat_records = [
            {
                "request_id": row[0],
                "session_id": row[1],
                "role": row[2],
                "origin": row[3],
                "timestamp": row[4],
                "user": row[5],
                "agent": row[6],
                "model": row[7],
            } for row in rows
        ]

        return jsonify({"status": "success", "chat_records": chat_records})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def API_History_chat_get():
    try:
        request_body = request.get_json() or {}  # 空 Body 时默认空字典，避免报错
        user = request_body.get('user', '')  # 提取 user，默认空字符串（匹配“空则返回所有”逻辑）

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 3. 业务逻辑不变：有 user 则过滤，无则返回所有
            if user:  
                cursor.execute('''
                    SELECT request_id, session_id, role, origin, timestamp, user
                    FROM chat_list 
                    WHERE user = ?
                    ORDER BY timestamp DESC
                    LIMIT 200
                ''', (user,))
            else:  
                cursor.execute('''
                    SELECT request_id, session_id, role, origin, timestamp, user
                    FROM chat_list 
                    ORDER BY timestamp DESC
                    LIMIT 200
                ''')
            
            rows = cursor.fetchall()

        # 4. 响应格式不变，保持与前端的交互逻辑一致
        chat_records = [
            {
                "request_id": row[0],
                "session_id": row[1],
                "role": row[2],
                "origin": row[3],
                "timestamp": row[4],
                "user": row[5],
            } for row in rows
        ]

        return jsonify({"status": "success", "chat_records": chat_records})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def API_Chat_visit_pvuv_get():
    """
    从visit.db数据库的visit表中获取PV和UV数据
    输入参数：
    1. 取样周期：最近的7天，30天，90天
    2. 搜索条件：按照用户名搜索
    3. 页面筛选：按照page_now字段筛选
    
    输出格式：
    JSON格式，包含日期、访问量(PV)和访问人数(UV)
    """
    try:
        # 解析请求数据
        data = request.json or {}
        
        # 获取取样周期参数，默认为7天
        period = data.get("period", 7)
        if period not in [7, 30, 90]:
            period = 7  # 默认值
            
        # 获取用户名搜索条件
        user = data.get("user", "")
        
        # 获取页面筛选参数（前端传入页面名称，需要映射到数据库中的page_now字段）
        page = data.get("page", "")
        
        # 需要前缀匹配的页面
        prefix_match_pages = ["硬件树"]
        
        # 根据映射表获取实际的数据库字段值或值列表
        page_now = PAGE_MAPPING.get(page, "")
        
        # 检查是否是需要前缀匹配的页面
        is_prefix_match = page in prefix_match_pages
        
        with sqlite3.connect(VISIT_DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            # 1. 时间条件：最近period天
            # 2. 用户条件：如果提供了用户名，则按用户名筛选
            # 3. 页面条件：如果提供了页面，则按page_now字段筛选
            
            base_query = '''
                SELECT 
                    DATE(timestamp, 'localtime') as date,
                    COUNT(*) as pv,
                    COUNT(DISTINCT user_id) as uv
                FROM visit 
                WHERE timestamp >= DATETIME('now', '-{} days', 'localtime')
                    AND timestamp <= DATETIME('now', 'localtime')
                    AND user_id IS NOT NULL 
                    AND user_id != ''
            '''.format(period)
            
            params = []
            
            # 添加用户名筛选条件
            if user:
                base_query += ' AND user_id = ?'
                params.append(user)
            
            # 添加页面筛选条件
            if page_now:
                if is_prefix_match:
                    # 如果是前缀匹配（如硬件树），使用LIKE查询
                    base_query += ' AND page_now LIKE ?'
                    params.append(page_now + '%')
                elif isinstance(page_now, list):
                    # 如果page_now是列表（如组件树对应多个页面地址），使用IN查询
                    placeholders = ','.join(['?' for _ in page_now])
                    base_query += f' AND page_now IN ({placeholders})'
                    params.extend(page_now)
                else:
                    # 如果page_now是字符串，使用等值查询
                    base_query += ' AND page_now = ?'
                    params.append(page_now)
            
            base_query += ' GROUP BY DATE(timestamp) ORDER BY date'
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
        # 构造返回结果
        result = [
            {
                "date": row[0],
                "pv": row[1],
                "uv": row[2]
            } for row in rows
        ]
        
        # 按照要求的格式返回数据，横轴是天（日期），纵轴是访问量和访问人数
        return jsonify({
            "status": "success", 
            "data": result
        }), 200
        
    except Exception as e:
        print(f"An error occurred in API_Chat_visit_pvuv_get: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def API_Chat_ai_pvuv_get():
    """
    从chat.db数据库的chat_list表中获取PV和UV数据
    输入参数：
    1. 取样周期：最近的7天，30天，90天
    2. 搜索条件：按照用户名搜索
    3. 智能体类型：按照agent筛选
    
    输出格式：
    JSON格式，包含日期、访问量(PV)和访问人数(UV)
    """
    try:
        # 解析请求数据
        data = request.json or {}
        
        # 获取取样周期参数，默认为7天
        period = data.get("period", 7)
        if period not in [7, 30, 90]:
            period = 7  # 默认值
            
        # 获取用户名搜索条件
        user = data.get("user", "")
        
        # 获取agent筛选条件
        agent = data.get("agent", "")
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            # 1. 时间条件：最近period天
            # 2. 用户条件：如果提供了用户名，则按用户名筛选
            # 3. Agent条件：如果提供了agent，则按agent筛选
            
            base_query = '''
                SELECT 
                    DATE(timestamp, 'localtime') as date,
                    COUNT(*) as pv,
                    COUNT(DISTINCT user) as uv
                FROM chat_list 
                WHERE timestamp >= DATETIME('now', '-{} days', 'localtime')
                    AND timestamp <= DATETIME('now', 'localtime')
                    AND user IS NOT NULL 
                    AND user != ''
            '''.format(period)
            
            params = []
            
            # 添加用户名筛选条件
            if user:
                base_query += ' AND user = ?'
                params.append(user)
            
            # 添加agent筛选条件
            if agent:
                if agent == 'component':
                    # 组件智能体：agent字段包含'component'字段
                    base_query += " AND agent LIKE '%component%'"
                elif agent == 'chat':
                    # 问答智能体：agent字段等于'chat'
                    base_query += " AND agent = ?"
                    params.append('chat')
                elif agent == 'TlCheckAgent':
                    # 详设评审智能体：agent字段等于'TlCheckAgent'或'DocReviewAgent'
                    base_query += " AND (agent = ? OR agent = ?)"
                    params.extend(['TlCheckAgent', 'DocReviewAgent'])
            
            base_query += ' GROUP BY DATE(timestamp) ORDER BY date'
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
        # 构造返回结果
        result = [
            {
                "date": row[0],
                "pv": row[1],
                "uv": row[2]
            } for row in rows
        ]
        
        # 按照要求的格式返回数据，横轴是天（日期），纵轴是访问量和访问人数
        return jsonify({
            "status": "success", 
            "data": result
        }), 200
        
    except Exception as e:
        print(f"An error occurred in API_Chat_ai_pvuv_get: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def API_Chat_history_visit_get():
    """
    获取页面访问历史数据（按用户统计）
    输入参数：
    1. 时间周期：最近的7天，30天，90天
    2. 页面筛选：按照page_now字段筛选
    
    输出格式：
    JSON结构，包含：
    1. 序号：按照次数排序
    2. 用户ID：user_id字段（格式为：用户ID+用户姓名，如：10171727陈雷）
    3. 访问次数
    4. 最后访问时间
    5. 周活跃度：如果最近7天内访问次数大于零，则为活跃
    """
    try:
        # 解析请求数据
        data = request.json or {}
        
        # 获取时间周期参数，默认为7天
        period = data.get("period", 7)
        if period not in [7, 30, 90]:
            period = 7  # 默认值
            
        # 获取页面筛选参数（前端传入页面名称，需要映射到数据库中的page_now字段）
        page = data.get("page", "")
        
        # 需要前缀匹配的页面
        prefix_match_pages = ["硬件树"]
        
        # 根据映射表获取实际的数据库字段值或值列表
        page_now = PAGE_MAPPING.get(page, "")
        
        # 检查是否是需要前缀匹配的页面
        is_prefix_match = page in prefix_match_pages
        
        # 获取用户ID和姓名的映射关系
        username_dict = Get_username()
            
        with sqlite3.connect(VISIT_DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            # 1. 时间条件：最近period天
            # 2. 页面条件：如果提供了页面，则按page_now字段筛选
            
            base_query = '''
                SELECT 
                    user_id,
                    COUNT(*) as visit_count,
                    MAX(timestamp) as last_visit_time
                FROM visit 
                WHERE timestamp >= DATETIME('now', '-{} days', 'localtime')
                    AND timestamp <= DATETIME('now', 'localtime')
                    AND user_id IS NOT NULL 
                    AND user_id != ''
            '''.format(period)
            
            params = []
            
            # 添加页面筛选条件
            if page_now:
                if is_prefix_match:
                    # 如果是前缀匹配（如硬件树），使用LIKE查询
                    base_query += ' AND page_now LIKE ?'
                    params.append(page_now + '%')
                elif isinstance(page_now, list):
                    # 如果page_now是列表（如组件树对应多个页面地址），使用IN查询
                    placeholders = ','.join(['?' for _ in page_now])
                    base_query += f' AND page_now IN ({placeholders})'
                    params.extend(page_now)
                else:
                    # 如果page_now是字符串，使用等值查询
                    base_query += ' AND page_now = ?'
                    params.append(page_now)
            
            base_query += ' GROUP BY user_id ORDER BY visit_count DESC'
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            # 获取最近7天的访问数据用于计算周活跃度
            week_base_query = '''
                SELECT 
                    user_id,
                    COUNT(*) as week_visit_count
                FROM visit 
                WHERE timestamp >= DATE('now', '-7 days')
                    AND timestamp < DATE('now', '+1 days')
                    AND user_id IS NOT NULL 
                    AND user_id != ''
            '''
            
            week_params = []
            
            # 添加页面筛选条件到周查询
            if page_now:
                if is_prefix_match:
                    # 如果是前缀匹配（如硬件树），使用LIKE查询
                    week_base_query += ' AND page_now LIKE ?'
                    week_params.append(page_now + '%')
                elif isinstance(page_now, list):
                    # 如果page_now是列表（如组件树对应多个页面地址），使用IN查询
                    placeholders = ','.join(['?' for _ in page_now])
                    week_base_query += f' AND page_now IN ({placeholders})'
                    week_params.extend(page_now)
                else:
                    # 如果page_now是字符串，使用等值查询
                    week_base_query += ' AND page_now = ?'
                    week_params.append(page_now)
            
            week_base_query += ' GROUP BY user_id'
            
            cursor.execute(week_base_query, week_params)
            week_rows = cursor.fetchall()
            
            # 将周访问数据转换为字典以便快速查找
            week_visit_dict = {row[0]: row[1] for row in week_rows}
            
        # 构造返回结果
        result = []
        for index, row in enumerate(rows):
            user_id = row[0]
            visit_count = row[1]
            last_visit_time = row[2]
            
            # 获取用户姓名，如果找不到则只显示用户ID
            username = username_dict.get(user_id, "")
            full_user_id = f"{username}{user_id}"
            
            # 计算周活跃度：如果最近7天内访问次数大于零，则为活跃
            week_visit_count = week_visit_dict.get(user_id, 0)
            weekly_activity = "活跃" if week_visit_count > 0 else "不活跃"
            
            result.append({
                "index": index + 1,  # 序号从1开始
                "user_id": full_user_id,  # 返回格式为：用户姓名+用户ID
                "visit_count": visit_count,
                "last_visit_time": last_visit_time,
                "weekly_activity": weekly_activity
            })
        
        return jsonify({
            "status": "success", 
            "data": result
        }), 200
        
    except Exception as e:
        print(f"An error occurred in API_Chat_history_visit_get: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def API_Chat_history_ai_get():
    """
    获取AI访问历史数据
    输入参数：
    1. 时间周期：最近的7天，30天，90天
    2. 智能体类型：按照agent筛选
    
    输出格式：
    JSON结构，包含：
    1. 序号：按照次数排序
    2. 用户ID：user字段（格式为：用户ID+用户姓名，如：10171727陈雷）
    3. 访问次数
    4. 最后访问时间
    5. 周活跃度：如果最近7天内访问次数大于零，则为活跃
    """
    try:
        # 解析请求数据
        data = request.json or {}
        
        # 获取时间周期参数，默认为7天
        period = data.get("period", 7)
        if period not in [7, 30, 90]:
            period = 7  # 默认值
            
        # 获取agent筛选条件
        agent = data.get("agent", "")
        
        # 获取用户ID和姓名的映射关系
        username_dict = Get_username()
            
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            # 1. 时间条件：最近period天
            # 2. Agent条件：如果提供了agent，则按agent筛选
            
            base_query = '''
                SELECT 
                    user,
                    COUNT(*) as visit_count,
                    MAX(timestamp) as last_visit_time
                FROM chat_list 
                WHERE timestamp >= DATETIME('now', '-{} days', 'localtime')
                    AND timestamp <= DATETIME('now', 'localtime')
                    AND user IS NOT NULL 
                    AND user != ''
            '''.format(period)
            
            params = []
            
            # 添加agent筛选条件
            if agent:
                if agent == 'component':
                    # 组件智能体：agent字段包含'component'字段
                    base_query += " AND agent LIKE '%component%'"
                elif agent == 'chat':
                    # 问答智能体：agent字段等于'chat'
                    base_query += " AND agent = ?"
                    params.append('chat')
                elif agent == 'TlCheckAgent':
                    # 详设评审智能体：agent字段等于'TlCheckAgent'或'DocReviewAgent'
                    base_query += " AND (agent = ? OR agent = ?)"
                    params.extend(['TlCheckAgent', 'DocReviewAgent'])
            
            base_query += ' GROUP BY user ORDER BY visit_count DESC'
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            # 获取最近7天的访问数据用于计算周活跃度
            week_base_query = '''
                SELECT 
                    user,
                    COUNT(*) as week_visit_count
                FROM chat_list 
                WHERE timestamp >= DATE('now', '-7 days')
                    AND timestamp < DATE('now', '+1 days')
                    AND user IS NOT NULL 
                    AND user != ''
            '''
            
            week_params = []
            
            # 添加agent筛选条件到周查询
            if agent:
                if agent == 'component':
                    # 组件智能体：agent字段包含'component'字段
                    week_base_query += " AND agent LIKE '%component%'"
                elif agent == 'chat':
                    # 问答智能体：agent字段等于'chat'
                    week_base_query += " AND agent = ?"
                    week_params.append('chat')
                elif agent == 'TlCheckAgent':
                    # 详设评审智能体：agent字段等于'TlCheckAgent'或'DocReviewAgent'
                    week_base_query += " AND (agent = ? OR agent = ?)"
                    week_params.extend(['TlCheckAgent', 'DocReviewAgent'])
            
            week_base_query += ' GROUP BY user'
            
            cursor.execute(week_base_query, week_params)
            week_rows = cursor.fetchall()
            
            # 将周访问数据转换为字典以便快速查找
            week_visit_dict = {row[0]: row[1] for row in week_rows}
            
        # 构造返回结果
        result = []
        for index, row in enumerate(rows):
            user_id = row[0]
            visit_count = row[1]
            last_visit_time = row[2]
            
            # 获取用户姓名，如果找不到则只显示用户ID
            username = username_dict.get(user_id, "")
            full_user_id = f"{username}{user_id}"
            
            # 计算周活跃度：如果最近7天内访问次数大于零，则为活跃
            week_visit_count = week_visit_dict.get(user_id, 0)
            weekly_activity = "活跃" if week_visit_count > 0 else "不活跃"
            
            result.append({
                "index": index + 1,  # 序号从1开始
                "user_id": full_user_id, # 返回格式为：用户姓名+用户ID
                "visit_count": visit_count,
                "last_visit_time": last_visit_time,
                "weekly_activity": weekly_activity
            })
        
        return jsonify({
            "status": "success", 
            "data": result
        }), 200
        
    except Exception as e:
        print(f"An error occurred in API_Chat_history_ai_get: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def API_Prompt_get():
    """
    从数据库中获取prompt数据
    支持通过 search 字符串在 标题、副标题、内容、创建人 四个字段中进行模糊搜索
    匹配任意一项即返回该条记录
    """
    try:
        # 解析请求数据
        data = request.json or {}

        # 获取搜索关键词
        search_term = data.get("search", "").strip()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询语句：在多个字段中模糊匹配 search_term
            if search_term:
                query = """
                    SELECT 主题, 摘要, 内容, 场景, 创建人, 创建时间, 引用次数 
                    FROM prompt 
                    WHERE 主题 LIKE ? 
                       OR 摘要 LIKE ? 
                       OR 内容 LIKE ? 
                       OR 创建人 LIKE ?
                """
                # 使用 %keyword% 进行模糊匹配
                like_term = f"%{search_term}%"
                params = [like_term] * 4  # 四个字段都用同一个模糊关键词
            else:
                # 如果没有提供 search_term，则返回所有数据
                query = """
                    SELECT 主题, 摘要, 内容, 场景, 创建人, 创建时间, 引用次数 
                    FROM prompt
                """
                params = []

            # 执行查询
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # 构造返回结果（使用新字段名映射）
        prompts = [
            {
                "title": row[0],
                "subtitle": row[1],
                "content": row[2],
                "scene": row[3],
                "creator": row[4],
                "created_at": row[5],
                "reference_count": row[6]
            } for row in rows
        ]

        return jsonify({"status": "success", "prompts": prompts}), 200

    except Exception as e:
        print(f"An error occurred in API_Prompt_get: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


def API_Prompt_set():
    """
    更新prompt数据表，从前端接收JSON数据
    如果主题已存在则更新所有内容，如果是新增则直接增加行
    数据库表内容为：主题、摘要、内容、场景、创建人、引用次数
    创建时间直接取当前时间
    """
    try:
        # 解析请求数据
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        title = data.get("title")
        if not title:
            return jsonify({"status": "error", "message": "Missing title"}), 400

        subtitle = data.get("subtitle", "")
        content = data.get("content", "")
        scene = data.get("scene", "")
        creator = data.get("creator", "")
        reference_count = data.get("reference_count", 0)  # 获取引用次数，默认为0

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 检查主题是否已存在
            cursor.execute("SELECT COUNT(1) FROM prompt WHERE 主题 = ?", (title,))
            exists = cursor.fetchone()[0] > 0

            if exists:
                # 更新现有记录
                cursor.execute('''
                    UPDATE prompt 
                    SET 摘要 = ?, 内容 = ?, 场景 = ?, 创建人 = ?, 创建时间 = datetime('now', 'localtime'), 引用次数 = ?
                    WHERE 主题 = ?
                ''', (subtitle, content, scene, creator, reference_count, title))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO prompt (主题, 摘要, 内容, 场景, 创建人, 创建时间, 引用次数)
                    VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), ?)
                ''', (title, subtitle, content, scene, creator, reference_count))

            conn.commit()

        return jsonify({"status": "success", "message": "Prompt data saved successfully"}), 200

    except Exception as e:
        print(f"An error occurred in API_Prompt_set: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def API_Prompt_del():
    """
    删除 prompt 数据
    前端传入 title、creator、user
    只有当 creator 与 user 相同时，才允许删除指定 title 的记录
    """
    try:
        # 解析请求数据
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        user = data.get("user")
        title = data.get("title")
        creator = data.get("creator")

        # 校验必填字段
        if not user:
            return jsonify({"status": "error", "message": "Missing user"}), 400
        if not title:
            return jsonify({"status": "error", "message": "Missing title"}), 400
        if not creator:
            return jsonify({"status": "error", "message": "Missing creator"}), 400

        # 权限校验：只有创建者才能删除
        if creator != user:
            return jsonify({"status": "error", "message": "当前用户非模版创建人，无删除权限！"}), 403  # 403 禁止访问更合适

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # 检查是否存在该标题的记录
            cursor.execute("SELECT COUNT(1) FROM prompt WHERE 主题 = ?", (title,))
            exists = cursor.fetchone()[0] > 0

            if not exists:
                return jsonify({"status": "error", "message": "指定的标题不存在"}), 404

            # 执行删除
            cursor.execute("DELETE FROM prompt WHERE 主题 = ?", (title,))
            conn.commit()

        return jsonify({"status": "success", "message": "Prompt 数据删除成功"}), 200

    except Exception as e:
        print(f"An error occurred in API_Prompt_del: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'chat.db')
VISIT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'visit.db')
DB_LIST = "chat_list"

def chat_db_init():
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # 创建 chat_list 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_list (
                request_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user TEXT,
                model TEXT,
                agent TEXT,
                knowledge TEXT,
                icenter TEXT,
                rdc TEXT,
                think TEXT,
                role TEXT,
                content TEXT,
                origin TEXT,
                timestamp TEXT NOT NULL,
                component TEXT,
                context TEXT
            )
        ''')

        # 创建 templates 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subtitle TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        conn.commit()


def chat_item_read(session_id):
    """
    根据 session_id 获取聊天记录，返回格式为：
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        ...
    ]
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 查询指定 session_id 的所有字段
        cursor.execute('''
            SELECT * FROM chat_list
            WHERE session_id = ?
            ORDER BY timestamp ASC  -- 按时间顺序排列
        ''', (session_id,))

        rows = cursor.fetchall()

        # 获取列名（字段名）
        columns = [col[0] for col in cursor.description]

        # 转换为字典列表
        result = [
            dict(zip(columns, row)) for row in rows
        ]

        return result


def chat_item_save(chatitem):
    """
    根据 session_id 判断是否已有数据：
    - 没有：先插入 system 消息（role: system），生成新的 request_id
    - 然后插入 chat_item 的内容
    - 如果已存在，则直接插入 chat_item 的内容
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        session_id = chatitem.get("session_id")

        cursor.execute('''
            INSERT INTO chat_list (
                request_id, session_id, user, model, agent, knowledge, icenter, rdc, think, role, content, origin, timestamp, component, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            session_id,
            chatitem.get("user"),
            chatitem.get("model"),
            chatitem.get("agent"),
            chatitem.get("knowledge"),
            chatitem.get("icenter"),
            chatitem.get("rdc"),
            chatitem.get("think"),
            chatitem.get("role"),
            chatitem.get("content"),
            chatitem.get("origin"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chatitem.get("component"),
            chatitem.get("context"),
        ))

        conn.commit()


if __name__ == "__main__":
    import requests
    import json
    import uuid

    # Default values
    user_id = "10171727"
    user_token = "8bdb08ca6cb31034bc7ddf6f2c426965"
    model = "qwen3-zte"
    agent = "SuperAgent"
    session_id = str(uuid.uuid4())
    
    print("Testing SuperAgent (LangGraph-based)")
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print("="*50)
    
    # Base URL for the Flask API (assuming local testing)
    base_url = "http://localhost:3001"
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'q', '再见']:
            print("Ending conversation...")
            break
            
        # Generate a new request_id for each request
        request_id = str(uuid.uuid4())
        
        # Prepare the request data
        message_data = {
            "user": user_id,
            "session_id": session_id,
            "request_id": request_id,
            "model": model,
            "agent": agent,
            "content": user_input,
            "knowledge": "NoneKnowledge",
            "icenter": False,
            "rdc": False,
            "think": False,
            "context": "{}"
        }
        
        try:
            # Get the response from the agent endpoint directly
            agent_endpoint = f"{base_url}/api/api_chat/Agent"
            headers = {
                'Content-Type': 'application/json',
                'X-User-Name': user_id,
                'Authorization': f'Bearer {user_token}'
            }
            
            print("SuperAgent: ", end='', flush=True)
            with requests.post(agent_endpoint, headers=headers, json=message_data, stream=True) as r:
                if r.status_code == 200:
                    for line in r.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data: '):
                                data = decoded_line[6:]  # Remove 'data: ' prefix
                                if data.strip() == '[DONE]':
                                    print("")  # New line after completion
                                    break
                                try:
                                    json_data = json.loads(data)
                                    if 'text' in json_data:
                                        print(json_data['text'], end='', flush=True)
                                    elif 'error' in json_data:
                                        print(f"\nError: {json_data['error']}")
                                        break
                                except json.JSONDecodeError:
                                    print(f"\nNon-JSON data: {data}")
                else:
                    print(f"Request failed with status {r.status_code}: {r.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break
