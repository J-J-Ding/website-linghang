import os
import re
import traceback
import json as json_lib

from pathlib import Path
from flask import current_app
from contextlib import contextmanager
from flask import request, jsonify, Response

from electric_knowledge.utils_pub import pub_get_employ_name
from electric_knowledge.req_manage_ai_cfg import MODEL_CONFIG, Chat_ai_stream
from electric_knowledge.req_manage_data_service import get_chat_record_list_by_session_id, add_single_chat_record, get_chat_record_list_by_user_id, get_prompt_list_by_search_str, \
update_single_prompt_content, update_single_prompt_reference_count, del_single_prompt, get_all_mcp_cfg_dict
from electric_knowledge.req_manage_api import LLMClient, FastMCPCompatibleClient, ChatSession


@contextmanager
def clear_proxy():
    old_proxies = {p: os.environ.get(p) for p in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')}
    try:
        for p in old_proxies:
            os.environ.pop(p, None)
        yield
    finally:
        for p, val in old_proxies.items():
            if val is not None:
                os.environ[p] = val


def get_tool_info_list(all_flag, obj_tool_name_list):
    try:
        mcp_cfg_dict = get_all_mcp_cfg_dict()
        with clear_proxy():
            mcp_client = FastMCPCompatibleClient(list(mcp_cfg_dict.keys()))
            raw_tool_dict = mcp_client.list_tools()
        tool_info_list = []
        for raw_mcp_url,raw_tool_list in raw_tool_dict.items():
            mcp_cfg_info = mcp_cfg_dict.get(raw_mcp_url)
            for raw_tool_item in raw_tool_list:
                name = raw_tool_item.name
                if not name: continue
                if (not all_flag) and (name not in obj_tool_name_list):
                    continue
                if mcp_cfg_info.get("need_tool") and name not in str(mcp_cfg_info.get("need_tool")):
                    continue
                if mcp_cfg_info.get("not_need_tool") and name in str(mcp_cfg_info.get("not_need_tool")):
                    continue
                desc = raw_tool_item.description
                if isinstance(desc, list):
                    desc = str(desc)
                schema = raw_tool_item.inputSchema
                tool_info_list.append({
                    "name": name,
                    "description": desc,
                    "inputSchema": schema
                })
        return tool_info_list
    except Exception as e:
        print(f"获取工具信息失败: {e}")
        return []


def service_add_req_manage_agent_single_chat_record():
    """
    新增单条聊天记录并流式返回模型响应
    ---
    tags:
      - 需求管理助手
    description: 接收用户消息，保存至数据库，调用大模型（支持工具调用）并以 SSE 流式返回响应
    consumes:
      - application/json
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号
        required: true
        type: string
        example: "10305454"
      - name: X-Auth-Value
        in: header
        description: 用户认证Token
        required: false
        type: string
      - name: body
        in: body
        description: 请求体，包含会话信息与用户输入
        required: true
        schema:
          type: object
          properties:
            session_id:
              type: string
              example: "sess_20251111_abc123"
            request_id:
              type: string
              example: "req_789xyz"
            model:
              type: string
              example: "qwen-max"
            content:
              type: string
              example: "请帮我查询单板状态"
          required: [session_id, request_id, content]
    responses:
      200:
        description: 成功启动流式对话，返回 text/event-stream
        headers:
          Content-Type:
            description: 响应类型
            type: string
            example: "text/event-stream"
      400:
        description: 请求参数缺失或模型配置错误
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            status:
              type: string
              example: "faild"
            message:
              type: string
              example: "请求体中缺少session_id、request_id或content"
    """
    try:
        # 1. 解析请求头
        user_id = request.headers.get('X-Emp-No')
        raw_result = pub_get_employ_name(user_id)
        user_name = extract_name_from_result(raw_result)
        user_token = request.headers.get('X-Auth-Value')
        # 2. 解析 form-data 普通字段
        session_id = request.form.get("session_id")
        request_id = request.form.get("request_id")
        model = request.form.get("model", "")
        tool_name_str = request.form.get("tool_name_str", "")
        content = request.form.get("content", "").strip()
        if not session_id or not request_id or not content:
            return {"code": 400, "status": "failed", "message": "请求体中缺少session_id、request_id或content"}
        llm_cfg = MODEL_CONFIG.get(model)
        if not llm_cfg:
            return {"code": 400, "status": "failed", "message": f"请求体中的模型名称未知: {model}"}
        # 3. 处理 fileList 多文件上传
        saved_file_path_list = []
        uploaded_file_list = request.files.getlist('file')
        if uploaded_file_list and any(f.filename.strip() for f in uploaded_file_list):
            current_dir = Path(__file__).resolve().parent
            base_dir = current_dir.parents[5]
            upload_dir = base_dir/"agent"/request_id
            upload_dir.mkdir(parents=True, exist_ok=True)
            for uploaded_file in uploaded_file_list:
                if not uploaded_file or not uploaded_file.filename:
                    continue  # 跳过空文件
                file_path = upload_dir / uploaded_file.filename
                uploaded_file.save(str(file_path))
                saved_file_path_list.append(str(file_path))
        if len(saved_file_path_list) > 0:
            content += f"\n\n已上传文件\n" + "\n".join(saved_file_path_list)
        # 3. 保存用户消息
        user_msg = {
            "session_id": session_id,
            "role": "user",
            "user_id": user_id,
            "user_name": user_name,
            "model": llm_cfg.get("model", model),
            "tool_name_str": tool_name_str,
            "content": content,
        }
        add_single_chat_record(user_msg)
        # 4. 获取历史
        chat_history = get_chat_record_list_by_session_id(session_id)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history if msg["role"] != "system"]
        # 5. 初始化 system prompt（如果尚未存在）
        tool_info_list = get_tool_info_list(False, tool_name_str)
        tool_info_desc = json_lib.dumps(tool_info_list, ensure_ascii=False, indent=2)
        system_prompt = f"""
你是一个智能助手，用户工号为 {user_id}，认证令牌为 {user_token}。请严格遵守以下规则：


可用工具（仅在必要时使用）：
{tool_info_desc}


【调用规则】
1. 仅当用户问题必须依赖外部工具才能回答时，才调用工具。
2. 若无需工具，请直接用自然语言简洁回答。
3. 若需调用工具，请在**单次响应中**返回严格合法的 JSON（注意单次响应中只能包含一个工具）：
   - 工具：{{"tool": "工具名", "arguments": {{...}}}}
4. 禁止使用 Markdown、代码块、注释或调用未列出的工具。
5. 不要解释你的推理过程，不要重复用户问题。


【响应规则】
- 系统会自动执行你返回的工具调用，并将结果注入对话上下文。
- 在后续推理中，你应基于工具结果直接回答用户问题。
- 最终回答必须是自然语言，**不要包含任何 JSON 或工具调用格式**。


【文件处理】
- 用户可能上传了文件，其路径会以“已上传文件”开头，后跟一个或多个绝对路径。
- 不要猜测文件内容，必须通过工具读取。


【重要！空结果处理规则】
- 如果工具返回空列表 `[]`、空对象 `{{}}` 或空字符串，请不要直接回答“未找到”。
- 你必须假设：**可能是你传入的参数有误**（如字段名错误、值不规范、缺少必要条件）。
- 请根据工具描述，检查并修正参数，至少重试一次。
- 仅当重试后依然返回空，才可回答“未找到相关信息”。


【重要！失败后必须重试】
- 若工具返回空、error错误或信息不足：
   a) 必须分析失败原因（如关键词模糊、参数缺失）；
   b) 必须至少调整一次参数或换关键词，重新生成工具调用；
   c) 仅当连续5次重试均失败，或用户明确要求停止时，才可回答“未找到相关信息”。


【失败重试示例】
- 用户问：“查设备A的状态”
- 你调用工具：{{"tool": "查询设备状态", "arguments": {{"id": "A"}}}}
- 工具返回 error: "id_not_found"
- 你应该改为：{{"tool": "查询设备状态", "arguments": {{"name": "A", "fuzzy_match": true}}}}
- 绝不允许失败5次以内就直接放弃
- 绝不允许失败5次以内就直接放弃
"""
        system_msg = user_msg.copy()
        system_msg.update(role="system", content=system_prompt)
        messages.insert(0, {"role": "system", "content": system_prompt})
        add_single_chat_record(system_msg)
        # 6. 确保最后一条是 user（防止重复触发）
        if messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": content})
        # 7. 创建客户端
        with clear_proxy():
            llm_client = LLMClient(**llm_cfg)
            mcp_cfg_dict = get_all_mcp_cfg_dict()
            mcp_client = FastMCPCompatibleClient(list(mcp_cfg_dict.keys()))
            chat_session = ChatSession(llm_client, mcp_client)
        # 捕获当前 Flask app 实例（必须在请求上下文中）
        app = current_app._get_current_object()
        # 8. 流式响应生成器
        def generate():
            with app.app_context():
                # 初始 messages 包含 system + 历史 + user
                current_messages = messages.copy()
                accumulated_response = ""
                max_steps = 20  # 防止无限循环
                step = 0
                tool_flag = False
                while step < max_steps:
                    step += 1
                    llm_resp_full = ""
                    is_tool_call = False
                    # 流式调用 LLM
                    judge_flag = False
                    for chunk in Chat_ai_stream(current_messages, model):
                        if not chunk: continue
                        llm_resp_full += chunk
                        if not judge_flag:
                            if llm_resp_full.startswith('{"'):
                                yield f"data: {json_lib.dumps({'text': '<tool_name>**【执行工具】**'})}\n\n"
                            elif tool_flag:
                                yield f"data: {json_lib.dumps({'text': ''})}\n\n"
                            judge_flag = True
                        # 实时透传给前端（可选：工具调用时不显示，或标记类型）
                        yield f"data: {json_lib.dumps({'text': chunk})}\n\n"
                    # 尝试解析是否为工具调用
                    clean_resp = llm_resp_full.strip()
                    if clean_resp.startswith("```json"):
                        clean_resp = clean_resp[7:].rstrip("```").strip()
                    elif clean_resp.startswith("```tool_code"):
                        clean_resp = clean_resp[12:].rstrip("```").strip()
                    clean_resp_fixed = clean_resp.replace('\n', '\\n').replace('\r', '\\r')
                    tool_calls = None
                    try:
                        # 尝试解析为单个或多个工具调用
                        parsed = json_lib.loads(clean_resp)
                        if isinstance(parsed, list):
                            tool_calls = parsed  # 多个工具
                        elif isinstance(parsed, dict) and "tool" in parsed:
                            tool_calls = [parsed]  # 单个工具
                    except (json_lib.JSONDecodeError, TypeError):
                        tool_calls = None
                    if tool_calls:
                        tool_flag = True
                        if judge_flag:
                            yield f"data: {json_lib.dumps({'text': '<br><br>'})}\n\n"
                            yield f"data: {json_lib.dumps({'text': '</tool_name>'})}\n\n"
                        is_tool_call = True
                        results = []
                        for call in tool_calls:
                            if "tool" in call and "arguments" in call:
                                try:
                                    result = chat_session.mcp_client.call_tool(call["tool"], call["arguments"])
                                    single_result = f"<tool_result>**【执行成功】**{result}<br><br></tool_result>"
                                    results.append(single_result)
                                    yield f"data: {json_lib.dumps({'text': single_result})}\n\n"
                                except Exception as e:
                                    single_result = f"<tool_result>**【执行失败】**{e}<br><br></tool_result>"
                                    results.append(single_result)
                                    yield f"data: {json_lib.dumps({'text': single_result})}\n\n"
                            else:
                                results.append("无效的工具调用格式")

                        tool_result_str = "\n".join(results)
                        # 保存 LLM 的工具调用请求
                        add_single_chat_record({
                            **user_msg,
                            "role": "assistant",
                            "content": llm_resp_full,
                            "origin": llm_resp_full,
                        })
                        # 保存工具结果（作为 system 消息）
                        add_single_chat_record({
                            **user_msg,
                            "role": "system",
                            "content": tool_result_str,
                            "origin": tool_result_str,
                        })
                        # 将工具结果追加到对话历史，继续下一轮推理
                        current_messages.append({"role": "assistant", "content": llm_resp_full})
                        current_messages.append({"role": "system", "content": tool_result_str})
                        # # 可选：向前端发送工具结果（非流式部分）
                        # yield f"data: {json_lib.dumps({'tool_result': tool_result_str})}\n\n"
                    else:
                        # 不是工具调用，视为最终回答
                        accumulated_response = llm_resp_full
                        # 保存最终回答
                        add_single_chat_record({
                            **user_msg,
                            "role": "assistant",
                            "content": accumulated_response,
                            "origin": accumulated_response,
                        })
                        break
                yield "data: [DONE]\n\n"
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        traceback.print_exc()
        return {"code": 400, "status": "faild", "message": f"未知错误: {e}"}


def service_get_history_chat_record_list():
    """
    获取当前用户的所有历史聊天记录
    ---
    tags:
      - 需求管理助手
    description: 根据用户工号查询其全部聊天会话记录（按时间倒序）
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        description: 请求体（user_id 字段将被忽略，实际使用 Header 中 X-Emp-No）
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: string
              example: "10305454"
    responses:
      200:
        description: 成功返回聊天记录列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "获取成功"
            data:
              type: array
              items:
                type: object
                properties:
                  session_id:
                    type: string
                  role:
                    type: string
                  content:
                    type: string
                  timestamp:
                    type: string
                    format: date-time
    """
    request_body = request.get_json() or {}
    user_id = request_body.get('user', '')
    chat_record_list = get_chat_record_list_by_user_id(user_id)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": chat_record_list})


def service_get_prompt_list_by_search_str():
    """
    根据关键词模糊搜索常用语
    ---
    tags:
      - 需求管理助手
    description: 支持对 常用语 的标题、内容、创建人等字段进行模糊搜索
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        description: 搜索关键词
        required: true
        schema:
          type: object
          properties:
            search_str:
              type: string
              example: "单板"
          required: [search_str]
    responses:
      200:
        description: 成功返回匹配的常用语列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "获取成功"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  content:
                    type: string
                  creator_id:
                    type: string
                  creator_name:
                    type: string
                  create_time:
                    type: string
                    format: date-time
                  reference_count:
                    type: integer
    """
    request_body = request.get_json() or {}
    search_str = request_body.get("search", "").strip()
    prompt_list = get_prompt_list_by_search_str(search_str)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": prompt_list})


def service_update_single_prompt_content():
    """
    更新指定常用语的内容
    ---
    tags:
      - 需求管理助手
    description: 仅允许创建者更新其创建的常用语内容
    consumes:
      - application/json
    parameters:
      - name: X-Emp-No
        in: header
        description: 当前操作人工号（用于权限校验）
        required: true
        type: string
        example: "10305454"
      - name: body
        in: body
        description: 更新字段
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: 常用语标题
            content:
              type: string
              example: 修改后的常用语
          required: [title, content]
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "更新成功"
      400:
        description: 更新失败
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            status:
              type: string
              example: "faild"
            message:
              type: string
              example: "无权限修改该常用语"
    """
    request_body = request.get_json() or {}
    creator_id = request.headers.get('X-Emp-No')
    request_body["creator_id"] = creator_id
    raw_result = pub_get_employ_name(creator_id)
    request_body["creator_name"] = extract_name_from_result(raw_result)
    op_ret = update_single_prompt_content(request_body)
    if op_ret:
        return jsonify({"code": 400, "status": "faild", "message": op_ret})
    else:
        return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_update_single_prompt_reference_count():
    """
    更新常用语的引用次数
    ---
    tags:
      - 需求管理助手
    description: 增加或设置常用语的引用计数
    consumes:
      - application/json
    parameters:
      - name: X-Emp-No
        in: header
        description: 操作人工号
        required: true
        type: string
        example: "10305454"
      - name: body
        in: body
        description: 更新引用次数的参数
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: 常用语xxx
          required: [title]
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "更新成功"
      400:
        description: 更新失败
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            status:
              type: string
              example: "faild"
            message:
              type: string
              example: "常用语标题不存在"
    """
    request_body = request.get_json() or {}
    creator_id = request.headers.get('X-Emp-No')
    request_body["creator_id"] = creator_id
    op_ret = update_single_prompt_reference_count(request_body)
    if op_ret:
        return jsonify({"code": 400, "status": "faild", "message": op_ret})
    else:
        return jsonify({"code": 200, "status": "success", "message": "更新成功"})


def service_del_single_prompt():
    """
    删除指定常用语
    ---
    tags:
      - 需求管理助手
    description: 仅允许创建者删除其创建的常用语
    consumes:
      - application/json
    parameters:
      - name: X-Emp-No
        in: header
        description: 当前操作人工号（用于权限校验）
        required: true
        type: string
        example: "10305454"
      - name: body
        in: body
        description: 需包含 prompt_id
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "常用语标题"
          required: [title]
    responses:
      200:
        description: 删除成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "删除成功"
      400:
        description: 删除失败（如无权限、ID不存在）
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            status:
              type: string
              example: "faild"
            message:
              type: string
              example: "无权限删除该常用语"
    """
    request_body = request.get_json() or {}
    creator_id = request.headers.get('X-Emp-No')
    request_body["creator_id"] = creator_id
    op_ret = del_single_prompt(request_body)
    if op_ret:
        return jsonify({"code": 400, "status": "faild", "message": op_ret})
    else:
        return jsonify({"code": 200, "status": "success", "message": "删除成功"})


def service_get_tool_name_list():
    """
    获取MCP工具接口基本信息列表
    ---
    tags:
      - 需求管理助手
    description: |
      获取所有MCP工具接口的简要信息列表。
    produces:
      - application/json
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            status:
              type: string
              example: "success"
            message:
              type: string
              example: "获取成功"
            data:
              type: array
              items:
                type: object
                example: {"name": "example_tool", "description": "An example MCP tool"}
      400:
        description: 获取失败（如服务内部错误）
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            status:
              type: string
              example: "fail"
            message:
              type: string
              example: "获取工具列表失败"
    """
    tool_info_list = get_tool_info_list(True, "")
    for item in tool_info_list:
        item.pop("inputSchema", None)
    return jsonify({"code": 200, "status": "success", "message": "获取成功", "data": tool_info_list})


def extract_name_from_result(full_str: str) -> str:
    """
    从 '姓名+工号' 字符串中提取纯姓名（移除末尾连续数字）
    例如: "张进朋10305454" → "张进朋"
          "Zhang Jinpeng123456" → "Zhang Jinpeng"
    """
    if not full_str:
        return ""
    # 从字符串末尾移除所有连续数字
    match = re.match(r'^(.*?)(\d*)$', full_str)
    if match:
        name_part = match.group(1)
        return name_part.rstrip()  # 去掉可能的尾部空格
    return full_str