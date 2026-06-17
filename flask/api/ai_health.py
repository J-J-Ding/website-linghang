# ai_health.py
import json
import time
import uuid
from typing import Generator
import requests
from flask import Response, request, jsonify

# 模型配置
MODEL_CONFIG = {
    "nebula": {
        "key": "dc2b13d7-ac3a-4338-bea0-a334cc1ae1c7",
        "url": "https://nebulacoder-maas.zte.com.cn/v1/chat/completions",
        "model": "nebulacoder-lite-v7.0"
    },
}


def chat_ai_stream_health(messages: list = [], model: str = "nebula") -> Generator[str, None, None]:
    """
    网元健康专用的大模型流式调用
    """
    config = MODEL_CONFIG.get(model, MODEL_CONFIG["nebula"])

    system_prompt = """
        # Persona（角色）：
        你是一个专业的网元健康诊断专家。

        # Task（任务）：
        你需要分析网元健康指标数据，生成详细的健康诊断报告。

        # 注意事项：
        1. 回答要专业、准确、实用
        2. 使用🟢🟡🔴表情符号表示状态等级
        3. 严格按照要求的格式输出
    """

    # 如果没有消息，返回系统提示词
    if not messages:
        yield system_prompt
        return

    try:
        # 确保系统提示词存在
        has_system = any(msg.get("role") == "system" for msg in messages)
        if not has_system:
            messages = [{"role": "system", "content": system_prompt}] + messages

        response = requests.post(
            url=config["url"],
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['key']}"
            },
            json={
                "model": config["model"],
                "messages": messages,
                "stream": True,
            },
            stream=True,
            timeout=300  # 5分钟超时
        )

        if response.status_code != 200:
            raise RuntimeError(f"大模型请求失败，状态码：{response.status_code}")

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
                if "choices" in chunk_data and chunk_data.get("choices"):
                    delta = chunk_data["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]

            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

    except Exception as e:
        error_msg = f"大模型调用异常: {str(e)}"
        print(error_msg)
        yield error_msg


def chat_ai_sync_health(messages: list, model: str = "nebula") -> str:
    """
    同步调用大模型，返回完整响应
    """
    full_response = []
    for chunk in chat_ai_stream_health(messages, model):
        full_response.append(chunk)
    return "".join(full_response)


def Agent_ai_health_stream(chat_history: list = None, config: dict = None) -> Generator[str, None, None]:
    """
    网元健康诊断智能体 - 流式输出
    专门用于健康诊断报告生成
    """
    try:
        if config is None:
            config = {}

        # 构建消息列表
        messages = []

        # 添加系统提示词
        system_prompt = """你是一个专业的网元健康诊断专家，专门分析网络设备的健康状态数据。

你的能力包括：
1. 分析CPU、内存、磁盘、队列使用率等系统资源
2. 评估SSD寿命和有效备用块状态  
3. 监控关键进程的内存使用
4. 生成详细的健康诊断报告
5. 提供优化建议和故障预警

请基于提供的健康指标数据，给出专业的诊断分析和建议。"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加历史对话
        if chat_history:
            for msg in chat_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", "")
                    })

        # 调用大模型
        for chunk in chat_ai_stream_health(messages):
            yield chunk

    except Exception as e:
        error_msg = f"健康诊断生成失败: {str(e)}"
        print(error_msg)
        yield error_msg


def Agent_health():
    """
    网元健康专用Agent接口
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        request_id = data.get("request_id")
        if not request_id:
            return jsonify({"error": "Missing request_id"}), 400

        # 获取参数
        content = data.get("content", "")
        context = data.get("context", "")

        # 构建健康诊断专用的消息格式
        chat_history = [
            {
                "role": "user",
                "content": content,
                "context": context
            }
        ]

        def generate_response():
            try:
                # 调用健康诊断智能体
                for chunk in Agent_ai_health_stream(chat_history, {"context": context}):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"

                # 发送结束标记
                yield f"data: [DONE]\n\n"

            except Exception as e:
                error_msg = f"生成回答时出错：{str(e)}"
                print(error_msg)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"

        return Response(generate_response(), mimetype='text/event-stream')

    except Exception as e:
        print(f"Agent_health 接口异常：{e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def Agent_health_sync():
    """
    网元健康专用Agent同步接口（非流式）
    用于批量分析场景，避免大量流式连接
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        content = data.get("content", "")

        # 构建消息
        messages = [
            {"role": "user", "content": content}
        ]

        # 同步调用
        result = chat_ai_sync_health(messages)

        return jsonify({
            "status": "success",
            "data": {
                "response": result
            }
        })

    except Exception as e:
        print(f"Agent_health_sync 接口异常：{e}")
        return jsonify({"status": "error", "message": str(e)}), 500