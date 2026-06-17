import struct
import os
from flask import request, jsonify,send_file
from datetime import datetime, timedelta
import json
import time
import re
import traceback
from typing import Generator, List, Dict, Optional, Any, Union
from ask_ai_request import Chat_ai_stream
from api_utils import Replace_question
from SshService import JumpSSHClient, Command,WindowsSSHClient
from ai_health import Agent_health_sync

import asyncio
import aiohttp
import threading
import uuid
from collections import defaultdict
import math
import tempfile
import base64
import csv
import io
import tarfile

SERVER_API_URL = "http://10.90.251.221:3001/api"

def get_sample_health_data():
    try:
        sample_hex_data = """
        02 07 01 01 28 26 00 00 00 64 64 00 00 00 00 00
        00 00 00 00 00 00 00 00 00 1A 02 02 05 2F 03 05
        08 01 01 28 26 01 00 00 64 64 00 00 00 00 00 00
        00 00 00 00 00 00 00 00 1A 02 02 05 2F 09 05 08
        01 01 28 26 01 00 00 64 64 00 00 00 00 00 00 00
        00 00 00 00 00 00 00 1A 02 02 05 2F 0E 05 09 01
        01 28 26 01 00 00 64 64 00 00 00 00 00 00 00 00
        00 00 00 00 00 00 1A 02 02 05 2F 13 01 09 01 01
        28 26 01 00 00 64 64 00 00 00 00 00 00 00 00 00
        00 00 00 00 00 1A 02 02 05 2F 19 0E 0E 01 01 28
        26 01 00 00 64 64 00 00 00 00 00 00 00 08 09 10
        0B 0C 0C 14 1A 02 02 05 2F 1F 05 0F 01 01 28 26
        01 00 00 64 64 00 00 00 00 00 00 00 37 0D 14 11
        0E 0C 18 1A 02 02 05 2F 24 05 
        """

        hex_bytes = sample_hex_data.replace('\n', ' ').split()
        file_data = bytes([int(x, 16) for x in hex_bytes])

        parsed_data = parse_binary_log_new(file_data)

        return parsed_data

    except Exception as e:
        print(f"生成示例数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def get_sample_data():
    """
    获取示例健康数据
    """
    try:
        sample_data = get_sample_health_data()

        if not sample_data:
            return jsonify({
                'status': 'error',
                'message': '生成示例数据失败'
            }), 500

        return jsonify({
            'status': 'success',
            'message': '示例数据加载成功',
            'data': sample_data
        })

    except Exception as e:
        print(f"获取示例数据错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取示例数据失败: {str(e)}'
        }), 500

def parse_health_log():
    """
    解析网元健康二进制日志文件
    """
    try:
        start_time = time.time()

        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未找到上传文件'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400

        if not file.filename.lower().endswith('.log'):
            return jsonify({
                'status': 'error',
                'message': '仅支持 .log 格式的二进制日志文件'
            }), 400

        file_data = file.read()
        file_size = len(file_data)
        print(f"开始解析文件: {file.filename}, 大小: {file_size} 字节")

        if file_size > 10 * 1024 * 1024:  # 10MB
            print(f"文件大小超过限制: {file_size} 字节")
            return jsonify({
                'status': 'error',
                'message': '文件大小超过10MB限制'
            }), 400

        parsed_data = parse_binary_log_new(file_data)

        parse_time = time.time() - start_time
        print(f"解析完成，耗时: {parse_time:.2f}秒，解析到 {len(parsed_data)} 条记录")

        if not parsed_data:
            print("未解析到有效数据")
            return jsonify({
                'status': 'error',
                'message': '未解析到有效数据，请检查文件格式'
            }), 400

        #按时间间隔抽样
        response_data = parsed_data
        original_count = len(parsed_data)
        is_sampled = False

        if original_count > 10000:
            print(f"数据量过大（{original_count}条），进行时间间隔抽样...")
            is_sampled = True

            # 计算数据的时间范围
            try:
                # 尝试解析时间戳
                time_format = "%Y-%m-%d %H:%M:%S"
                start_timestamp = parsed_data[0].get('timestamp')
                end_timestamp = parsed_data[-1].get('timestamp')

                if start_timestamp and end_timestamp:
                    start_dt = datetime.strptime(start_timestamp, time_format)
                    end_dt = datetime.strptime(end_timestamp, time_format)
                    time_span = (end_dt - start_dt).total_seconds()
                    print(f"数据时间跨度: {time_span:.0f}秒 ({time_span / 3600:.1f}小时)")

                    # 根据时间跨度决定抽样间隔
                    if time_span > 86400:  # 超过1天
                        # 每59秒取1个点 + 头尾
                        time_interval = 59
                    elif time_span > 3600:  # 超过1小时
                        time_interval = 29
                    else:
                        time_interval = 1

                    print(f"使用时间间隔抽样: 每{time_interval}秒")

                    # 按时间间隔抽样
                    sampled_data = [parsed_data[0]]  # 包含第一个点
                    last_sampled_time = start_dt

                    for i in range(1, original_count - 1):
                        current_timestamp = parsed_data[i].get('timestamp')
                        if current_timestamp:
                            try:
                                current_dt = datetime.strptime(current_timestamp, time_format)
                                time_diff = (current_dt - last_sampled_time).total_seconds()

                                if time_diff >= time_interval:
                                    sampled_data.append(parsed_data[i])
                                    last_sampled_time = current_dt
                            except:
                                # 如果时间解析失败，使用简单抽样
                                if i % (original_count // 5000) == 0:
                                    sampled_data.append(parsed_data[i])

                    # 确保包含最后一个点
                    if original_count > 1:
                        sampled_data.append(parsed_data[-1])

                    response_data = sampled_data

                else:
                    # 如果时间戳解析失败，使用简单抽样
                    print("时间戳解析失败，使用简单抽样")
                    response_data = smart_simple_sample(parsed_data)

            except Exception as time_err:
                print(f"时间解析错误，使用简单抽样: {time_err}")
                response_data = smart_simple_sample(parsed_data)

            print(f"抽样后数据量: {len(response_data)}条")
            print(f"抽样保留比例: {len(response_data) / original_count * 100:.1f}%")

        return jsonify({
            'status': 'success',
            'message': f'日志解析成功',
            'data': response_data,
        })

    except Exception as e:
        print(f"解析日志文件错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'解析日志文件失败: {str(e)}'
        }), 500


def smart_simple_sample(parsed_data):
    """
    智能简单抽样：包含头尾，中间均匀抽样
    """
    original_count = len(parsed_data)

    # 目标抽样到大约5000-8000条数据
    target_sample_count = min(8000, max(3000, original_count // 15))

    if original_count <= target_sample_count:
        return parsed_data

    # 计算抽样率
    sample_rate = max(1, original_count // target_sample_count)

    sampled_data = [parsed_data[0]]

    # 对中间数据进行抽样
    for i in range(1, original_count - 1):
        if i % sample_rate == 0:
            sampled_data.append(parsed_data[i])

    if original_count > 1:
        sampled_data.append(parsed_data[-1])

    # 如果抽样后数据还是太多，进一步抽样
    if len(sampled_data) > 10000:
        final_sampled_data = [sampled_data[0]]
        second_sample_rate = max(1, len(sampled_data) // 8000)

        for i in range(1, len(sampled_data) - 1):
            if i % second_sample_rate == 0:
                final_sampled_data.append(sampled_data[i])

        final_sampled_data.append(sampled_data[-1])
        return final_sampled_data

    return sampled_data


def parse_binary_log_new(file_data):
    """
    二进制日志文件结构

    TDeviceInfo (24字节):
    BYTE    cpuUsage;           # 1字节 - 偏移 0
    BYTE    memUsage;           # 1字节 - 偏移 1  
    BYTE    keyProcState;       # 1字节 - 偏移 2
    BYTE    switchState;        # 1字节 - 偏移 3
    BYTE    boardEnvTemp;       # 1字节 - 偏移 4
    BYTE    diskSpace;          # 1字节 - 偏移 5
    BYTE    loadmode;           # 1字节 - 偏移 6
    BYTE    syncState;          # 1字节 - 偏移 7
    BYTE    queueUsage;         # 1字节 - 偏移 8
    BYTE    ssdRemainLife;      # 1字节 - 偏移 9
    BYTE    validSpareBlocks;   # 1字节 - 偏移 10
    BYTE    cpuStatus;          # 1字节 - 偏移 11
    BYTE    switchChipStatus;   # 1字节 - 偏移 12
    BYTE    clockChipStatus;    # 1字节 - 偏移 13
    BYTE    phyChipStatus;      # 1字节 - 偏移 14
    BYTE    boardEepromStatus;       # 1字节 - 偏移 15
    BYTE    backplaneEepromStatus;   # 1字节 - 偏移 16
    BYTE    fpgaStatus;              # 1字节 - 偏移 17
    BYTE    procMemUsage[7];    # 7字节 - 偏移 18-24
    BYTE    timestamp[6];       # 6字节 - 偏移 25-30

    总大小: 31字节
    """
    STRUCT_SIZE = 31
    data_list = []

    file_size = len(file_data)
    print(f"开始解析二进制数据，文件大小: {file_size} 字节")
    start_time = time.time()

    if len(file_data) < STRUCT_SIZE:
        print(f"文件太小，无法解析: {len(file_data)} 字节")
        return data_list

    record_count = len(file_data) // STRUCT_SIZE
    print(f"预计解析 {record_count} 条记录")

    process_names = ['WASON', 'QXOAGENT', 'MIM', 'UEM', 'TOPUEM', 'USM', 'UPP2OTNAGENT']

    for i in range(record_count):
        # 检查是否超时（超过30秒）
        if time.time() - start_time > 30:
            print(f"解析超时，已处理 {i}/{record_count} 条记录")
            raise TimeoutError("文件解析超时")

        offset = i * STRUCT_SIZE
        chunk = file_data[offset:offset + STRUCT_SIZE]

        if len(chunk) < STRUCT_SIZE:
            print(f"记录 {i} 数据不完整，跳过")
            continue

        try:
            hex_str = ' '.join([f'{b:02x}' for b in chunk])

            cpu_usage = chunk[0]
            mem_usage = chunk[1]
            key_proc_state = chunk[2]
            switch_state = chunk[3]
            board_env_temp = chunk[4]
            disk_space = chunk[5]
            loadmode = chunk[6]
            sync_state = chunk[7]
            queue_usage = chunk[8]
            ssd_remain_life = chunk[9]
            valid_spare_blocks = chunk[10]
            proc_mem_bytes = chunk[18:25]
            proc_mem_usage = list(proc_mem_bytes)
            timestamp_bytes = chunk[25:31]

            # 解析时间戳: 格式为 年(后2位) 月 日 时 分 秒
            year = timestamp_bytes[0] + 2000  # 年份只保留后两位，需要加上2000
            month = timestamp_bytes[1]
            day = timestamp_bytes[2]
            hour = timestamp_bytes[3]
            minute = timestamp_bytes[4]
            second = timestamp_bytes[5]

            timestamp_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

            record = {
                'timestamp': timestamp_str,
                'cpuUsage': cpu_usage,
                'memUsage': mem_usage,
                'diskSpace': disk_space,
                'queueUsage': queue_usage,
                'ssdRemainLife': ssd_remain_life,
                'validSpareBlocks': valid_spare_blocks,
                'procMemUsage': {
                    'WASON': proc_mem_usage[0],
                    'QXOAGENT': proc_mem_usage[1],
                    'MIM': proc_mem_usage[2],
                    'UEM': proc_mem_usage[3],
                    'TOPUEM': proc_mem_usage[4],
                    'USM': proc_mem_usage[5],
                    'UPP2OTNAGENT': proc_mem_usage[6]
                },
                'rawData': {
                    'loadmode': loadmode,
                    'syncState': sync_state
                }
            }

            data_list.append(record)

        except Exception as e:
            print(f"解析记录 {i} 错误: {e}")
            continue

    total_time = time.time() - start_time
    print(f"解析完成，共解析 {len(data_list)} 条有效记录，耗时: {total_time:.2f}秒")
    return data_list


def Agent_ai_health(chat_history: list = [], config: Dict = None) -> Generator[str, None, None]:
    """
    网元健康诊断智能体 - 使用大模型分析健康指标数据
    """
    try:
        if config is None:
            config = {}
        elif isinstance(config, str):
            try:
                config = json.loads(config)
            except:
                config = {}

        if chat_history is None:
            system_prompt = """你是一个专业的网元健康诊断专家，专门分析网络设备的健康状态数据。

你的能力包括：
1. 分析CPU、内存、磁盘、队列使用率等系统资源
2. 评估SSD寿命和有效备用块状态  
3. 监控关键进程的内存使用
4. 生成详细的健康诊断报告
5. 提供优化建议和故障预警

请基于提供的健康指标数据，给出专业的诊断分析和建议。"""
            return [system_prompt]

        if chat_history and len(chat_history) > 0:
            # 获取最新的用户消息
            last_user_message = None
            for msg in reversed(chat_history):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break

            if last_user_message:
                try:
                    # 检查是否是健康数据查询（JSON格式）
                    if last_user_message.startswith('{') and 'metrics' in last_user_message:
                        # 这是健康数据分析请求
                        health_data = json.loads(last_user_message)
                        metrics = health_data.get('metrics', [])
                        summary = health_data.get('summary', {})

                        if not metrics:
                            yield "未找到有效的健康指标数据进行分析。请确保已正确上传并解析日志文件。"
                            return

                        # 构建给大模型的提示词
                        analysis_prompt = build_health_analysis_prompt(metrics, summary)

                        new_messages = [
                            {"role": "system", "content": "你是一个专业的网元健康诊断专家"},
                            {"role": "user", "content": analysis_prompt}
                        ]

                        # 调用大模型接口，使用流式输出
                        for chunk in Chat_ai_stream(new_messages, "nebula"):
                            yield chunk

                    else:
                        # 这是用户对话请求，从config中获取诊断报告信息
                        diagnosis_report = {}
                        health_metrics = []

                        # 安全地从config中获取数据
                        if isinstance(config, dict):
                            diagnosis_report = config.gets('diagnosisReport', {})
                            health_metrics = config.get('healthMetrics', [])

                        # 如果config中没有数据，尝试从其他途径获取
                        if not diagnosis_report and 'diagnosisReport' in config:
                            diagnosis_report = config['diagnosisReport']
                        if not health_metrics and 'healthMetrics' in config:
                            health_metrics = config['healthMetrics']

                        # 构建专门的对话提示词
                        chat_prompt = build_ai_chat_prompt(last_user_message, diagnosis_report, health_metrics)

                        new_messages = [
                            {"role": "system",
                             "content": "你是一个专业的网元健康诊断专家，请严格按照指定的格式回答用户问题"},
                            {"role": "user", "content": chat_prompt}
                        ]

                        # 调用大模型接口，使用流式输出
                        for chunk in Chat_ai_stream(new_messages, "nebula"):
                            yield chunk

                except json.JSONDecodeError:
                    # 如果不是JSON格式，当作普通对话处理，但仍然使用诊断数据
                    diagnosis_report = {}
                    health_metrics = []

                    if isinstance(config, dict):
                        diagnosis_report = config.get('diagnosisReport', {})
                        health_metrics = config.get('healthMetrics', [])

                    chat_prompt = build_ai_chat_prompt(last_user_message, diagnosis_report, health_metrics)

                    new_messages = [
                        {"role": "system",
                         "content": "你是一个专业的网元健康诊断专家，请严格按照指定的格式回答用户问题"},
                        {"role": "user", "content": chat_prompt}
                    ]

                    for chunk in Chat_ai_stream(new_messages, "nebula"):
                        yield chunk
                except Exception as e:
                    print(f"分析健康数据时发生错误: {str(e)}")
                    yield f"分析健康数据时发生错误: {str(e)}"
            else:
                yield "请提供健康指标数据进行分析。您可以上传健康日志文件，系统会自动解析并生成诊断报告。"
        else:
            yield "请提供健康指标数据进行分析。"

    except Exception as e:
        print(f"健康诊断智能体错误: {str(e)}")
        yield f"健康诊断分析过程中发生错误: {str(e)}"


def build_health_analysis_prompt(metrics: List[Dict], summary: Dict) -> str:
    """
    构建给大模型的健康数据分析提示词，支持在线诊断数据
    """
    if not metrics:
        return "无有效数据可供分析"

    # 在线诊断数据格式
    if isinstance(metrics, list) and len(metrics) > 0:
        first_item = metrics[0]
        if isinstance(first_item, dict) and 'component' in first_item:
            return build_online_diagnosis_prompt(metrics)

    # 离线日志数据
    latest = metrics[-1] if metrics else {}

    trends = analyze_health_trends(metrics)

    prompt = f"""请分析以下网元健康指标数据，并生成详细的专业诊断报告：

## 重要要求：
1. 必须给出具体的健康评分（0-100分）
2. 评分标准：
   - 90-100分：优秀，各项指标均正常
   - 80-89分：良好，主要指标正常，少数指标需关注
   - 70-79分：一般，部分指标异常但无严重问题
   - 60-69分：警告，多个指标异常需要关注
   - 0-59分：危险，存在严重问题需要立即处理
   
## 当前健康指标数据：
- CPU使用率: {latest.get('cpuUsage', 0)}%
- 内存使用率: {latest.get('memUsage', 0)}%
- 磁盘使用率: {latest.get('diskSpace', 0)}%
- 队列使用率: {latest.get('queueUsage', 0)}%
- SSD剩余寿命: {latest.get('ssdRemainLife', 100)}%
- SSD有效备用块: {latest.get('validSpareBlocks', 100)}
- 进程内存使用率: {json.dumps(latest.get('procMemUsage', {}), ensure_ascii=False)}

## 数据统计信息：
- 数据点数: {len(metrics)} 个
- 时间范围: {metrics[0].get('timestamp', '')} 到 {metrics[-1].get('timestamp', '')}
- 平均CPU使用率: {summary.get('averageMetrics', {}).get('cpuUsage', 0)}%
- 平均内存使用率: {summary.get('averageMetrics', {}).get('memUsage', 0)}%
- 平均磁盘使用率: {summary.get('averageMetrics', {}).get('diskSpace', 0)}%

## 趋势分析：
- CPU趋势: {trends.get('cpuTrend', 0):+.1f}%
- 内存趋势: {trends.get('memTrend', 0):+.1f}%
- 磁盘趋势: {trends.get('diskTrend', 0):+.1f}%
- 队列趋势: {trends.get('queueTrend', 0):+.1f}%

请按照以下专业格式生成诊断报告：

## 一、总体健康评估
**健康状态**: [🟢 健康 / 🟡 警告 / 🔴 危险]
**总体评分**: [0-100分]
**评估摘要**: [简要描述系统整体健康状况]

## 二、详细指标分析

### CPU使用率分析
**当前值**: {latest.get('cpuUsage', 0)}%
**状态**: [🟢 正常 / 🟡 警告 / 🔴 危险]
**分析**: [详细分析CPU使用情况]
**建议**: [优化建议]

### 内存使用率分析  
**当前值**: {latest.get('memUsage', 0)}%
**状态**: [🟢 正常 / 🟡 警告 / 🔴 危险]
**分析**: [详细分析内存使用情况]
**建议**: [优化建议]

### 磁盘使用率分析
**当前值**: {latest.get('diskSpace', 0)}%
**状态**: [🟢 正常 / 🟡 警告 / 🔴 危险]
**分析**: [详细分析磁盘使用情况]
**建议**: [优化建议]

### 队列使用率分析
**当前值**: {latest.get('queueUsage', 0)}%
**状态**: [🟢 正常 / 🟡 警告 / 🔴 危险]
**分析**: [详细分析队列使用情况]
**建议**: [优化建议]

### SSD健康状态分析
**剩余寿命**: {latest.get('ssdRemainLife', 100)}%
**有效备用块**: {latest.get('validSpareBlocks', 100)}
**状态**: [🟢 良好 / 🟡 注意 / 🔴 危险]
**分析**: [详细分析SSD健康状态]
**建议**: [维护建议]

### 进程内存分析
**状态**: [🟢 正常 / 🟡 警告 / 🔴 危险]
**分析**: [分析各进程内存使用情况]
**建议**: [进程优化建议]

## 三、趋势分析与预测
[基于历史数据的趋势分析和未来预测]

## 四、综合优化建议
[按优先级排列的综合建议]

## 五、紧急处理事项
[如存在紧急问题，列出需要立即处理的事项]

请使用专业的网络设备健康诊断术语，基于行业标准阈值给出准确的评估和实用的建议。
重点关注：性能瓶颈、资源预警、硬件健康、系统稳定性等方面。"""

    return prompt


def build_ai_chat_prompt(user_question: str, diagnosis_report: Dict, health_metrics: List[Dict]) -> str:
    """
    构建AI健康助手对话的专用提示词
    确保大模型按照特定格式输出回答
    """
    try:
        # 确保参数类型正确
        if diagnosis_report is None:
            diagnosis_report = {}
        if health_metrics is None:
            health_metrics = []

        # 获取最新的健康指标
        latest_metrics = {}
        if health_metrics and len(health_metrics) > 0:
            latest_metrics = health_metrics[-1] if isinstance(health_metrics[-1], dict) else {}

        ssd_life = latest_metrics.get('ssdRemainLife', 100)
        spare_blocks = latest_metrics.get('validSpareBlocks', 100)

        # 计算SSD预计使用月数
        ssd_remaining_months = (ssd_life / 2) * 9 if ssd_life > 0 else 0

        # 获取当前日期
        current_date = datetime.now().strftime("%Y年%m月%d日")

        prompt = f"""你是一个专业的网元健康诊断专家，专门回答用户关于网元健康状态的问题。

## 当前可用的诊断信息：
{json.dumps(diagnosis_report, ensure_ascii=False, indent=2) if diagnosis_report else '暂无诊断报告信息'}

## 最新的健康指标数据：
- CPU使用率: {latest_metrics.get('cpuUsage', 0)}%
- 内存使用率: {latest_metrics.get('memUsage', 0)}%
- 磁盘使用率: {latest_metrics.get('diskSpace', 0)}%
- 队列使用率: {latest_metrics.get('queueUsage', 0)}%
- SSD剩余寿命: {ssd_life}%
- SSD有效备用块: {spare_blocks}

## 用户问题：
{user_question}

## 回答要求：
请基于诊断报告和健康指标数据，按照以下结构化格式回答用户问题：

### 对于SSD相关问题的回答格式：
根据诊断报告，SSD的剩余寿命情况如下：

当前状态：[状态图标和描述]
剩余寿命：[具体百分比]%
有效备用块数量：[具体数量]个

智能分析：
[详细的分析说明，包括当前状态评估、风险分析等]

智能决策：
[具体的维护建议和优化措施，按条列出]

智能预测：
按照9个月消耗2%，SSD剩余{ssd_life}%的使用寿命还可以继续使用{ssd_remaining_months:.0f}个月

报告生成时间：{current_date}
诊断人员：网元健康诊断专家

### 对于其他指标问题的回答格式：
根据诊断报告，[指标名称]的情况如下：

当前状态：[状态图标和描述]
当前值：[具体数值]

智能分析：
[详细的分析说明]

智能决策：
[具体的优化建议]

智能预测：
[基于趋势的预测分析]

报告生成时间：{current_date}
诊断人员：网元健康诊断专家

## 重要说明：
1. 对于SSD剩余寿命预测，使用标准模型：每9个月消耗2%寿命
2. 计算方式：剩余月数 = (当前剩余寿命百分比 / 2) * 9
3. 保持专业、准确、实用的风格
4. 所有数值和预测都要基于提供的诊断数据
5. 使用表情图标(🟢🟡🔴)来表示状态等级
6. 必须严格按照上述格式输出，不要添加额外的说明或格式

请现在回答用户的问题："""

        return prompt

    except Exception as e:
        print(f"构建提示词错误: {str(e)}")
        return f"请基于用户问题 '{user_question}' 提供专业的网元健康诊断建议。"

def analyze_health_trends(metrics: List[Dict]) -> Dict[str, float]:
    """
    分析健康指标趋势
    """
    if len(metrics) < 2:
        return {}

    first = metrics[0]
    last = metrics[-1]

    return {
        'cpuTrend': last.get('cpuUsage', 0) - first.get('cpuUsage', 0),
        'memTrend': last.get('memUsage', 0) - first.get('memUsage', 0),
        'diskTrend': last.get('diskSpace', 0) - first.get('diskSpace', 0),
        'queueTrend': last.get('queueUsage', 0) - first.get('queueUsage', 0)
    }


def build_online_diagnosis_prompt(diagnosis_data: List[Dict]) -> str:
    """
    构建在线诊断数据分析提示词
    """
    try:
        cpu_data = [item for item in diagnosis_data if item.get('item') == 'CPU Utilization']
        memory_data = [item for item in diagnosis_data if item.get('item') == 'Memory Usage']
        disk_data = [item for item in diagnosis_data if item.get('item') == 'Disk Usage Rate']
        queue_data = [item for item in diagnosis_data if item.get('item') == 'TIPC Queue Usage']
        ssd_life_data = [item for item in diagnosis_data if item.get('item') == 'SSD Remain Life']
        spare_blocks_data = [item for item in diagnosis_data if item.get('item') == 'Valid Spare Blocks']

        # 同时支持BOARD组件中的内存使用率
        board_memory_data = [item for item in diagnosis_data if
                             item.get('component') == 'BOARD' and item.get('item') == 'Memory Usage']


        cpu_value = extract_numeric_value(cpu_data[0].get('result', '0%')) if cpu_data else 0
        if board_memory_data:
            memory_value = extract_numeric_value(board_memory_data[0].get('result', '0%'))
        else:
            memory_value = extract_numeric_value(memory_data[0].get('result', '0%')) if memory_data else 0

        disk_value = extract_numeric_value(disk_data[0].get('result', '0%')) if disk_data else 0
        queue_value = extract_numeric_value(queue_data[0].get('result', '0%')) if queue_data else 0
        ssd_life_value = extract_numeric_value(ssd_life_data[0].get('result', '100%')) if ssd_life_data else 100
        spare_blocks_value = extract_numeric_value(
            spare_blocks_data[0].get('result', '100')) if spare_blocks_data else 100


        cpu_status = cpu_data[0].get('status', 'Normal') if cpu_data else 'Normal'
        if board_memory_data:
            memory_status = board_memory_data[0].get('status', 'Normal')
        else:
            memory_status = memory_data[0].get('status', 'Normal') if memory_data else 'Normal'

        disk_status = disk_data[0].get('status', 'Normal') if disk_data else 'Normal'
        queue_status = queue_data[0].get('status', 'Normal') if queue_data else 'Normal'
        ssd_status = ssd_life_data[0].get('status', 'Normal') if ssd_life_data else 'Normal'

        prompt = f"""请分析以下网元在线健康诊断指标数据，并生成详细的专业诊断报告：

## 当前在线诊断指标数据：
- CPU使用率: {cpu_value}% [{cpu_status}]
- 内存使用率: {memory_value}% [{memory_status}]
- 磁盘使用率: {disk_value}% [{disk_status}]
- 队列使用率: {queue_value}% [{queue_status}]
- SSD剩余寿命: {ssd_life_value}% [{ssd_status}]
- SSD有效备用块: {spare_blocks_value}个

## 数据说明：
- 数据来源：实时在线诊断
- 检测时间：当前实时数据
- 数据可靠性：实时采集，准确性高

请按照以下专业格式生成在线诊断报告：

## 一、总体健康评估
**健康状态**: [根据各项指标状态综合评估：🟢 健康 / 🟡 警告 / 🔴 危险]
**总体评分**: [0-100分，基于各项指标状态和数值评估]
**评估摘要**: [简要描述系统实时健康状况]

## 二、详细指标分析

### CPU使用率分析
**当前值**: {cpu_value}%
**状态**: [根据数值和阈值评估：{get_status_emoji(cpu_status)} {get_status_text(cpu_status)}]
**分析**: [详细分析CPU使用情况，考虑实时负载和性能瓶颈]
**建议**: [针对CPU的优化建议]

### 内存使用率分析  
**当前值**: {memory_value}%
**状态**: [根据数值和阈值评估：{get_status_emoji(memory_status)} {get_status_text(memory_status)}]
**分析**: [详细分析内存使用情况，检查内存泄漏和碎片化]
**建议**: [内存优化建议]

### 磁盘使用率分析
**当前值**: {disk_value}%
**状态**: [根据数值和阈值评估：{get_status_emoji(disk_status)} {get_status_text(disk_status)}]
**分析**: [详细分析磁盘使用情况，检查存储空间和IO性能]
**建议**: [磁盘管理和优化建议]

### 队列使用率分析
**当前值**: {queue_value}%
**状态**: [根据数值和阈值评估：{get_status_emoji(queue_status)} {get_status_text(queue_status)}]
**分析**: [详细分析队列使用情况，检查通信性能和拥塞情况]
**建议**: [队列优化建议]

### SSD健康状态分析
**剩余寿命**: {ssd_life_value}%
**有效备用块**: {spare_blocks_value}个
**状态**: [根据SSD寿命和备用块评估：{get_ssd_status_emoji(ssd_life_value)} {get_ssd_status_text(ssd_life_value)}]
**分析**: [详细分析SSD健康状态，寿命预测和可靠性评估]
**建议**: [SSD维护和更换建议]

## 三、趋势分析与预测
[基于实时数据的特点，给出趋势分析和预测]

## 四、综合优化建议
[按优先级排列的实时优化建议]

## 五、紧急处理事项
[如存在紧急问题，列出需要立即处理的事项]

请使用专业的网络设备健康诊断术语，基于行业标准阈值给出准确的评估和实用的建议。
重点关注：实时性能瓶颈、资源预警、硬件健康、系统稳定性等方面。"""

        return prompt

    except Exception as e:
        print(f"构建在线诊断提示词错误: {str(e)}")
        return "请分析网元在线健康诊断数据，给出专业的诊断报告。"

def extract_numeric_value(value_str: str) -> float:
    """从字符串中提取数值"""
    if not value_str:
        print("extract_numeric_value: 输入为空")
        return 0.0

    value_str = str(value_str)

    # 尝试多种匹配模式
    patterns = [
        r'(\d+(\.\d+)?)%',  # 带百分号: 75%
        r'(\d+(\.\d+)?)\s*%',  # 带空格: 75 %
        r'^\s*(\d+(\.\d+)?)\s*$',  # 纯数字: 75
        r'(\d+(\.\d+)?)',  # 任何数字
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, value_str)
        if match:
            result = float(match.group(1))
            return result

    print(f"extract_numeric_value: 未匹配到数字, 返回0")
    return 0.0

def get_status_emoji(status: str) -> str:
    """根据状态获取表情符号"""
    status_map = {
        'Normal': '🟢',
        'Warning': '🟡',
        'Error': '🔴',
        'Critical': '🔴'
    }
    return status_map.get(status, '🟢')


def get_status_text(status: str) -> str:
    """根据状态获取文本"""
    status_map = {
        'Normal': '正常',
        'Warning': '警告',
        'Error': '异常',
        'Critical': '危险'
    }
    return status_map.get(status, '正常')


def get_ssd_status_emoji(life_value: float) -> str:
    """根据SSD寿命获取表情符号"""
    if life_value >= 70:
        return '🟢'
    elif life_value >= 30:
        return '🟡'
    else:
        return '🔴'


def get_ssd_status_text(life_value: float) -> str:
    """根据SSD寿命获取状态文本"""
    if life_value >= 70:
        return '良好'
    elif life_value >= 30:
        return '注意'
    else:
        return '危险'


def execute_online_diagnosis():
    """
    执行在线健康诊断
    """
    try:
        data = request.get_json()
        print("=== execute_online_diagnosis 开始 ===")
        print(f"请求数据: {data}")

        if not data:
            return jsonify({
                'status': 'error',
                'message': '未收到请求数据'
            }), 400

        # 提取参数
        jump_name = data.get('jump_name')
        target_ip = data.get('target_ip')
        shelf_number = data.get('shelf_number')
        slot_number = data.get('slot_number')

        # 参数验证
        if not all([jump_name, target_ip, shelf_number, slot_number]):
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400

        # 加载跳板机配置
        jump_config = load_jump_server_config(jump_name)
        if not jump_config:
            return jsonify({
                'status': 'error',
                'message': f'跳板机配置加载失败: {jump_name}'
            }), 400

        jump_host, jump_user, jump_password = jump_config

        # 执行诊断命令
        try:
            # 导入SshService
            import SshService
            JumpSSHClient = SshService.JumpSSHClient
            Command = SshService.Command

            with JumpSSHClient(
                    jump_host=jump_host,
                    jump_user=jump_user,
                    jump_password=jump_password,
                    timeout=30
            ) as client:

                # 构建命令序列
                commands = [
                    Command(
                        command="terminal length 0",
                        success_marker="ZXPOTN#",
                        failure_marker="Error",
                        single_wait_timeout=10
                    ),
                    Command(
                        command="diag",
                        success_marker="ZXPOTN(diag)#",
                        failure_marker="Error",
                        single_wait_timeout=10
                    ),
                    Command(
                        command=f"diag shell mpu-{shelf_number}/{slot_number}/0",
                        success_marker="ZXPOTN(diag-shell-MPU",
                        failure_marker="Error",
                        single_wait_timeout=10
                    ),
                    Command(
                        command="exec sh drvfmagent",
                        success_marker="[DRVFMAGENT]#",
                        failure_marker="Error",
                        single_wait_timeout=15
                    ),
                    Command(
                        command="exec diagFmShowKpiMonitor()",
                        success_marker="[DRVFMAGENT] end  time:",  # 等待输出结束标记
                        failure_marker="Error",
                        single_wait_timeout=30
                    )
                ]

                print(f"开始执行诊断命令，目标设备: {target_ip}, 子架: {shelf_number}, 槽位: {slot_number}")

                # 执行命令
                results = list(client.exec_commands_on_target(
                    target_host=target_ip,
                    target_user="root",
                    target_password="Root_1234",
                    commands=commands,
                    target_port=22,
                    default_completion="ZXPOTN"
                ))

                # 检查命令执行结果
                for i, result in enumerate(results):
                    print(f"\n=== 命令 {i + 1}: {result.command} ===")
                    print(f"成功: {result.success}")
                    print(f"输出长度: {len(result.raw_output)}")

                if not results or len(results) < 5:
                    print("结果不完整")
                    return jsonify({
                        'status': 'error',
                        'message': '命令执行结果不完整'
                    }), 500

                # 获取最后一条命令的输出
                last_result = results[-1]
                output = last_result.raw_output

                # 解析输出数据
                parsed_data = parse_diag_output(output)
                if parsed_data:
                    return jsonify({
                        'status': 'success',
                        'message': '在线诊断执行成功',
                        'data': parsed_data
                    })
                else:
                    print("解析失败，查看输出格式...")
                    # 检查输出是否包含预期内容
                    if "[DRVFMAGENT]NE Info:" in output:
                        print("输出包含 '[DRVFMAGENT]NE Info:'，但解析失败")
                    if "[DRVFMAGENT]Board Info:" in output:
                        print("输出包含 '[DRVFMAGENT]Board Info:'，但解析失败")

                    return jsonify({
                        'status': 'error',
                        'message': '解析诊断数据失败，请检查输出格式'
                    }), 500

        except Exception as e:
            print(f"SSH执行诊断命令失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'执行诊断命令失败: {str(e)}'
            }), 500

    except Exception as e:
        print(f"执行在线诊断错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'执行在线诊断失败: {str(e)}'
        }), 500

def load_jump_server_config(jump_name):
    """
    从openssh.json加载跳板机配置
    """
    try:
        # from AgentHandle.path_config import OpenSSH_IP_PATH

        with open('openssh.json', 'r', encoding='utf-8') as f:
            all_servers = json.load(f)

        if jump_name in all_servers:
            config = all_servers[jump_name]
            return (
                config.get('JUMP_HOST'),
                config.get('JUMP_USER'),
                config.get('JUMP_PASS')
            )
        else:
            print(f"跳板机 {jump_name} 未在配置文件中找到")
            return None

    except Exception as e:
        print(f"加载跳板机配置失败: {str(e)}")
        return None


def parse_diag_output(output):
    """
    解析diagFmShowKpiMonitor命令的输出
    """
    try:
        if len(output) < 100:
            print("输出太短，无法解析")
            return []

        # 清理ANSI转义字符和特殊控制字符

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)

        control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
        clean_output = control_chars.sub('', clean_output)

        clean_output = re.sub(r'.\x08', '', clean_output)

        lines = clean_output.split('\n')

        merged_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\r')
            if '|' in line and '+' not in line:
                if i + 1 < len(lines) and '|' in lines[i + 1] and '+' not in lines[i + 1]:
                    merged_line = line + lines[i + 1].rstrip('\r')
                    merged_lines.append(merged_line)
                    i += 2
                else:
                    merged_lines.append(line)
                    i += 1
            else:
                merged_lines.append(line)
                i += 1

        # 提取表格数据行
        table_data = []
        for line in merged_lines:
            if '|' in line and re.search(r'\|\s*\d+\s*\|', line):
                # 跳过表头行
                if 'Component' in line or 'Item' in line:
                    continue
                table_data.append(line)
                print(f"找到数据行: {line[:80]}...")

        parsed_data = []
        for line in table_data:
            try:
                parts = re.split(r'\s*\|\s*', line.strip())

                if len(parts) >= 6:
                    parts = [p.strip() for p in parts]

                    try:
                        item_no = int(parts[0])
                    except ValueError:
                        continue

                    item_data = {
                        'no': item_no,
                        'component': parts[1],
                        'item': parts[2],
                        'result': parts[3],
                        'referenceValue': parts[4],
                        'status': parts[5]
                    }

                    parsed_data.append(item_data)
            except Exception as e:
                print(f"解析行失败: {e}, 行: {line[:100]}")
                continue

        print(f"成功解析 {len(parsed_data)} 条数据")

        # 如果没有解析到数据，尝试解析方法2
        if not parsed_data:
            print("尝试备用解析方法...")
            parsed_data = parse_diag_output_backup(clean_output)

        return parsed_data

    except Exception as e:
        print(f"解析诊断输出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def parse_diag_output_backup(output):
    """
    直接使用正则表达式提取
    """
    try:
        # 匹配表格行：|  1 | NE           | Load Mode             | zdb            | zdb             | Normal     |
        pattern = r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

        matches = re.findall(pattern, output)
        parsed_data = []

        for match in matches:
            if len(match) == 6:
                try:
                    item_no = int(match[0].strip())
                    # 跳过表头
                    if match[1].strip() == "Component":
                        continue

                    item_data = {
                        'no': item_no,
                        'component': match[1].strip(),
                        'item': match[2].strip(),
                        'result': match[3].strip(),
                        'referenceValue': match[4].strip(),
                        'status': match[5].strip()
                    }
                    parsed_data.append(item_data)
                except Exception as e:
                    print(f"备用方法解析行失败: {e}")
                    continue

        return parsed_data

    except Exception as e:
        print(f"备用解析方法失败: {str(e)}")
        return []

def getjumpservers():
    """获取所有跳板机配置选项"""
    try:
        with open('openssh.json', 'r', encoding='utf-8') as f:
            jump_servers = json.load(f)

        options = []
        for server_name, config in jump_servers.items():
            options.append({
                "label": server_name,
                "value": server_name,
                "config": config
            })

        return jsonify({
            "status": "success",
            "data": options
        })

    except Exception as e:
        print(f"获取跳板机列表失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"获取跳板机列表失败: {str(e)}"
        }), 500


# ==============================
# 批量KPI处理器
# ==============================

class BatchKPIProcessor:
    """
    批量KPI日志处理器
    支持并发分析多个kpi日志文件
    """

    def __init__(self, server_api_url: str, max_workers: int = 10):
        self.server_api_url = server_api_url
        self.max_workers = max_workers
        self.results = []  # 存储分析结果
        self.results_lock = threading.Lock()  # 结果列表的线程锁
        self.progress_callback = None  # 进度回调函数
        self.is_running = False
        self.jump_server_name = "燕郊_1B4-1实验室"

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def _update_progress(self, current: int, total: int, message: str = ""):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def _extract_problem_items_count(self, analysis_text: str, health_score: int = None) -> tuple:
        """
        从分析报告中提取有问题的检测项数量
        如果传入 health_score，则优先使用它进行估算
        返回: (有问题的项数, 总检测项数)
        """
        try:
            total_items = 7

            # 1.直接从文本中提取每个检测项的状态
            # 定义检测项及其状态关键词
            items_status_patterns = {
                'CPU使用率': {
                    'keywords': ['CPU使用率', 'CPU', 'cpu', 'Cpu', '中央处理器'],
                    'problem_indicators': ['警告', '危险', '偏高', '过高', '异常', '超标', '严重',
                                           '🟡', '🔴', 'warning', 'critical', 'high']
                },
                '内存使用率': {
                    'keywords': ['内存使用率', '内存', 'Memory', 'memory', 'MEM'],
                    'problem_indicators': ['警告', '危险', '偏高', '过高', '异常', '内存泄漏', '超标',
                                           '🟡', '🔴', 'warning', 'critical', 'high']
                },
                '磁盘使用率': {
                    'keywords': ['磁盘使用率', '磁盘', 'SSD磁盘', 'SSD 磁盘', 'Disk', 'disk'],
                    'problem_indicators': ['警告', '危险', '偏高', '过高', '异常', '满盘',
                                           '🟡', '🔴', 'warning', 'critical', 'high']
                },
                '队列使用率': {
                    'keywords': ['队列使用率', '队列', 'Queue', 'queue'],
                    'problem_indicators': ['警告', '危险', '偏高', '过高', '异常', '拥塞',
                                           '🟡', '🔴', 'warning', 'critical', 'high']
                },
                'SSD剩余寿命': {
                    'keywords': ['SSD剩余寿命', 'SSD寿命', 'SSD Remain Life', '剩余寿命'],
                    'problem_indicators': ['警告', '危险', '偏低', '过低', '即将耗尽', '需要更换',
                                           '🟡', '🔴', 'warning', 'critical', 'low']
                },
                'SSD有效备用块': {
                    'keywords': ['SSD有效备用块', '有效备用块', 'Valid Spare Blocks', '备用块'],
                    'problem_indicators': ['警告', '危险', '偏低', '过低', '即将耗尽',
                                           '🟡', '🔴', 'warning', 'critical', 'low']
                },
                '进程内存': {
                    'keywords': ['进程内存', 'Process Memory', '进程'],
                    'problem_indicators': ['警告', '危险', '偏高', '过高', '异常',
                                           '🟡', '🔴', 'warning', 'critical', 'high']
                }
            }

            problem_count = 0

            # 遍历每个检测项，检查其状态
            for item_name, patterns in items_status_patterns.items():
                item_found = False
                item_has_problem = False

                # 查找这个检测项
                for keyword in patterns['keywords']:
                    if keyword in analysis_text:
                        item_found = True

                        # 获取keyword附近的文本（前后150个字符）
                        keyword_pos = analysis_text.find(keyword)
                        if keyword_pos >= 0:
                            start_pos = max(0, keyword_pos - 150)
                            end_pos = min(len(analysis_text), keyword_pos + 150)
                            context = analysis_text[start_pos:end_pos]

                            # 检查上下文中是否有问题指示词
                            for indicator in patterns['problem_indicators']:
                                if indicator in context:
                                    item_has_problem = True
                                    break

                        break

                # 如果找到了这个检测项且有问题的判断，计数
                if item_found and item_has_problem:
                    problem_count += 1

            # 2. 如果通过文本分析没找到问题项，或者没有传入health_score，使用评分估算
            if health_score is not None:
                # 使用传入的健康评分进行估算
                if problem_count == 0 or abs(problem_count - self._estimate_problem_count_by_score(health_score)) > 2:
                    # 如果文本分析的结果与评分估算的结果相差太大，使用评分估算
                    problem_count = self._estimate_problem_count_by_score(health_score)
                    print(f"📊 使用评分估算问题项: {problem_count}/{total_items} (评分: {health_score})")
                else:
                    print(f"📊 文本分析提取问题项: {problem_count}/{total_items} (评分: {health_score})")
            else:
                # 如果没有传入评分，尝试从文本中提取
                score_from_text = self._extract_health_score(analysis_text)
                if problem_count == 0:
                    problem_count = self._estimate_problem_count_by_score(score_from_text)
                    print(f"📊 从文本提取评分后估算: {problem_count}/{total_items} (评分: {score_from_text})")
                else:
                    print(f"📊 文本分析提取问题项: {problem_count}/{total_items}")

            # 确保问题项数量在合理范围内
            problem_count = max(0, min(total_items, problem_count))

            return problem_count, total_items

        except Exception as e:
            print(f"❌ 提取问题项数量失败: {str(e)}")
            return 0, 7

    def _estimate_problem_count_by_score(self, score: int) -> int:
        """
        根据健康评分估算问题项数量
        评分越高，问题项越少
        """
        if score >= 95:
            return 0
        elif score >= 90:
            return 0
        elif score >= 85:
            return 1
        elif score >= 80:
            return 2
        elif score >= 75:
            return 2
        elif score >= 70:
            return 3
        elif score >= 65:
            return 3
        elif score >= 60:
            return 4
        elif score >= 55:
            return 4
        elif score >= 50:
            return 5
        elif score >= 40:
            return 5
        elif score >= 30:
            return 6
        else:
            return 7

    async def analyze_single_kpi(self, session: aiohttp.ClientSession,
                                 kpi_path: str, log_filename: str,
                                 tar_filename: str) -> dict:
        """
        分析单个KPI日志文件
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                print(f"🚀 开始分析: {log_filename} (尝试 {attempt + 1}/{max_retries})")

                # 获取KPI数据
                kpi_data = self._get_kpi_data_directly(kpi_path, log_filename, tar_filename)

                if not kpi_data or 'metrics' not in kpi_data:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    return self._create_failed_result(
                        tar_filename, log_filename, kpi_path,
                        "无法获取KPI数据"
                    )

                # 每次重试都创建新的session
                async with aiohttp.ClientSession() as new_session:
                    health_data = {
                        "metrics": kpi_data['metrics'],
                        "summary": {
                            "source": tar_filename,
                            "log_file": log_filename,
                            "timestamp": datetime.now().isoformat(),
                            "data_points": len(kpi_data['metrics'])
                        }
                    }

                    # 调用大模型
                    response_text = await self._call_ai_model(new_session, health_data, log_filename)

                    if response_text:
                        health_score = self._extract_health_score_from_report(response_text)

                        problem_items_count, total_items_count = self._extract_problem_items_count(
                            response_text,
                            health_score  # 传入已提取的评分
                        )

                        result = {
                            "tar_filename": tar_filename,
                            "log_filename": log_filename,
                            "kpi_path": kpi_path,
                            "health_score": health_score,
                            "problem_items": problem_items_count,
                            "total_items": total_items_count,
                            "analysis_result": response_text,
                            "raw_metrics": kpi_data['metrics'][:50],
                            "total_metrics": len(kpi_data['metrics']),
                            "status": "completed",
                            "timestamp": datetime.now().isoformat()
                        }

                        print(
                            f"✅ 分析完成: {log_filename} - 评分: {health_score}, 问题项: {problem_items_count}/{total_items_count}")
                        return result

                    if attempt < max_retries - 1:
                        print(f"⚠️ 第 {attempt + 1} 次调用大模型失败，{retry_delay}秒后重试...")
                        await asyncio.sleep(retry_delay)
                    else:
                        return self._create_failed_result(
                            tar_filename, log_filename, kpi_path,
                            "大模型分析失败"
                        )

            except Exception as e:
                print(f"❌ 分析失败: {log_filename}, 错误: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    return self._create_failed_result(
                        tar_filename, log_filename, kpi_path,
                        f"分析异常: {str(e)}"
                    )

        return self._create_failed_result(
            tar_filename, log_filename, kpi_path,
            "达到最大重试次数"
        )

    def _get_kpi_data_directly(self, kpi_path: str, log_filename: str, tar_filename: str):
        """
        直接读取和解析KPI文件 添加抽样
        """
        try:
            print(f"🔍 直接读取KPI文件: {kpi_path}")

            # 1. 规范化路径
            kpi_path = kpi_path.replace('/', '\\')

            # 2. 从openssh.json加载跳板机配置
            with open('openssh.json', 'r', encoding='utf-8') as f:
                jump_servers = json.load(f)

            if self.jump_server_name not in jump_servers:
                print(f"❌ 跳板机 {self.jump_server_name} 不存在")
                return None

            jump_config = jump_servers[self.jump_server_name]
            jump_host = jump_config.get("JUMP_HOST")
            jump_user = jump_config.get("JUMP_USER")
            jump_pass = jump_config.get("JUMP_PASS")

            if not all([jump_host, jump_user, jump_pass]):
                print(f"❌ 跳板机配置不完整")
                return None

            # 3. 连接到Windows跳板机
            with WindowsSSHClient(jump_host, jump_user, jump_pass) as win_client:
                # 4. 下载文件并解析
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                try:
                    # 5. 使用更可靠的方式读取二进制文件
                    print(f"📥 下载文件到本地: {tmp_path}")

                    # 使用 PowerShell 的 Get-Content 读取二进制文件
                    ps_cmd = f'powershell "$bytes = Get-Content -Path \'{kpi_path}\' -Encoding Byte -ReadCount 0; [System.Convert]::ToBase64String($bytes)"'
                    base64_stdout, base64_stderr = win_client.execute_command(ps_cmd)

                    if not base64_stdout or base64_stdout.strip() == "":
                        print(f"❌ PowerShell读取失败，尝试备用方法")

                        # 备用方法：使用 certutil
                        certutil_cmd = f'certutil -encode "{kpi_path}" %temp%\\temp.b64 && type %temp%\\temp.b64 && del %temp%\\temp.b64'
                        base64_stdout, base64_stderr = win_client.execute_command(certutil_cmd)

                        if not base64_stdout or '-----BEGIN CERTIFICATE-----' not in base64_stdout:
                            print(f"❌ 所有读取方法都失败")
                            return None

                        # 提取base64内容
                        lines = base64_stdout.split('\n')
                        base64_lines = []
                        in_section = False

                        for line in lines:
                            line = line.strip()
                            if '-----BEGIN CERTIFICATE-----' in line:
                                in_section = True
                                continue
                            elif '-----END CERTIFICATE-----' in line:
                                break
                            elif in_section and line:
                                base64_lines.append(line)

                        if not base64_lines:
                            print(f"❌ 没有提取到base64内容")
                            return None

                        base64_str = ''.join(base64_lines)
                    else:
                        # PowerShell 直接返回了 base64 字符串
                        base64_str = base64_stdout.strip()

                    # 解码base64
                    try:
                        file_bytes = base64.b64decode(base64_str)
                        print(f"✅ 文件下载成功: {len(file_bytes)} 字节")
                    except Exception as e:
                        print(f"❌ base64解码失败: {e}")
                        return None

                    # 写入临时文件
                    with open(tmp_path, 'wb') as f:
                        f.write(file_bytes)

                    # 6. 使用parse_binary_log_new解析
                    with open(tmp_path, 'rb') as f:
                        file_data = f.read()

                    from deal_health import parse_binary_log_new
                    parsed_data = parse_binary_log_new(file_data)

                    if parsed_data:
                        print(f"✅ 解析成功，原始数据点数: {len(parsed_data)}")

                        # 7. 添加抽样逻辑（与parse_health_log保持一致）
                        response_data = parsed_data
                        original_count = len(parsed_data)

                        # 如果数据量过大，进行抽样
                        if original_count > 10000:
                            print(f"📊 数据量过大（{original_count}条），进行时间间隔抽样...")

                            try:
                                # 解析时间戳
                                time_format = "%Y-%m-%d %H:%M:%S"
                                start_timestamp = parsed_data[0].get('timestamp')
                                end_timestamp = parsed_data[-1].get('timestamp')

                                if start_timestamp and end_timestamp:
                                    start_dt = datetime.strptime(start_timestamp, time_format)
                                    end_dt = datetime.strptime(end_timestamp, time_format)
                                    time_span = (end_dt - start_dt).total_seconds()

                                    print(f"📊 数据时间跨度: {time_span:.0f}秒 ({time_span / 3600:.1f}小时)")

                                    # 根据时间跨度决定抽样间隔
                                    if time_span > 86400:  # 超过1天
                                        # 每59秒取1个点 + 头尾
                                        time_interval = 59
                                    elif time_span > 3600:  # 超过1小时
                                        time_interval = 29
                                    else:
                                        time_interval = 1

                                    print(f"📊 使用时间间隔抽样: 每{time_interval}秒")

                                    # 按时间间隔抽样
                                    sampled_data = [parsed_data[0]]  # 包含第一个点
                                    last_sampled_time = start_dt

                                    for i in range(1, original_count - 1):
                                        current_timestamp = parsed_data[i].get('timestamp')
                                        if current_timestamp:
                                            try:
                                                current_dt = datetime.strptime(current_timestamp, time_format)
                                                time_diff = (current_dt - last_sampled_time).total_seconds()

                                                if time_diff >= time_interval:
                                                    sampled_data.append(parsed_data[i])
                                                    last_sampled_time = current_dt
                                            except:
                                                # 如果时间解析失败，使用简单抽样
                                                if i % (original_count // 5000) == 0:
                                                    sampled_data.append(parsed_data[i])

                                    # 确保包含最后一个点
                                    if original_count > 1:
                                        sampled_data.append(parsed_data[-1])

                                    response_data = sampled_data
                                    print(f"📊 抽样后数据量: {len(response_data)}条")
                                else:
                                    # 如果时间戳解析失败，使用简单抽样
                                    print("⚠️ 时间戳解析失败，使用简单抽样")
                                    response_data = self._smart_simple_sample(parsed_data)
                            except Exception as time_err:
                                print(f"⚠️ 时间解析错误，使用简单抽样: {time_err}")
                                response_data = self._smart_simple_sample(parsed_data)

                        return {
                            "metrics": response_data,
                            "log_info": {
                                "filename": log_filename,
                                "tar_filename": tar_filename,
                                "path": kpi_path,
                                "total_points": len(response_data),
                                "original_points": original_count,
                                "file_size": len(file_bytes),
                                "local_temp_file": tmp_path,
                                "jump_server": self.jump_server_name
                            }
                        }
                    else:
                        print(f"❌ 解析失败")
                        return None

                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            print(f"🧹 清理临时文件: {tmp_path}")
                    except:
                        pass

        except Exception as e:
            print(f"❌ 直接获取KPI数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _smart_simple_sample(self, parsed_data):
        """
        简单抽样：包含头尾，中间均匀抽样
        """
        original_count = len(parsed_data)

        # 目标抽样到大约5000-8000条数据
        target_sample_count = min(8000, max(3000, original_count // 15))

        if original_count <= target_sample_count:
            return parsed_data

        # 计算抽样率
        sample_rate = max(1, original_count // target_sample_count)

        sampled_data = [parsed_data[0]]

        # 对中间数据进行抽样
        for i in range(1, original_count - 1):
            if i % sample_rate == 0:
                sampled_data.append(parsed_data[i])

        if original_count > 1:
            sampled_data.append(parsed_data[-1])

        # 如果抽样后数据还是太多，进一步抽样
        if len(sampled_data) > 10000:
            final_sampled_data = [sampled_data[0]]
            second_sample_rate = max(1, len(sampled_data) // 8000)

            for i in range(1, len(sampled_data) - 1):
                if i % second_sample_rate == 0:
                    final_sampled_data.append(sampled_data[i])

            final_sampled_data.append(sampled_data[-1])
            return final_sampled_data

        return sampled_data

    async def _call_ai_model(self, session: aiohttp.ClientSession, health_data: dict, log_filename: str):
        """
        调用大模型接口
        """
        try:
            request_id = f"batch_kpi_{uuid.uuid4()}"

            payload = {
                "content": json.dumps(health_data),
                "session_id": f"batch_session_{int(time.time())}",
                "request_id": request_id,
            }

            print(f"🤖 调用健康专用大模型分析: {log_filename}")

            # 使用同步接口，避免大量流式连接
            async with session.post(
                    f"{self.server_api_url}/api_chat/Agent_health_sync",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
            ) as response:

                if response.status != 200:
                    print(f"❌ 大模型接口错误: {response.status}")
                    return None

                result = await response.json()

                if result.get("status") == "success":
                    return result.get("data", {}).get("response", "")
                else:
                    print(f"❌ 大模型返回错误: {result.get('message')}")
                    return None

        except Exception as e:
            print(f"❌ 调用大模型失败: {e}")
            return None

    def _create_failed_result(self, tar_filename, log_filename, kpi_path, error_msg):
        """创建失败结果"""
        return {
            "tar_filename": tar_filename,
            "log_filename": log_filename,
            "kpi_path": kpi_path,
            "health_score": 0,
            "problem_items": 0, 
            "total_items": 7,  
            "analysis_result": error_msg,
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }

    def _extract_health_score_from_report(self, analysis_text: str) -> int:
        """
        从分析报告中提取健康评分
        """
        try:
            # 1. 先尝试从"总体评分"中提取
            patterns = [
                r'总体评分[：:\s]*\[?(\d{1,3})\]?\s*分',
                r'评分[：:\s]*\[?(\d{1,3})\]?\s*分',
                r'分数[：:\s]*\[?(\d{1,3})\]?',
                r'健康评分[：:\s]*(\d{1,3})',
                r'Score[：:\s]*(\d{1,3})',
                r'(\d{1,3})\s*分\s*\[',
                r'\[\s*(\d{1,3})\s*\]\s*分'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, analysis_text)
                if matches:
                    try:
                        score = int(matches[-1])
                        return max(0, min(100, score))
                    except:
                        continue

            # 2. 如果没有找到评分，根据健康状态进行更精细的估算
            # 检查是否有完整的"健康状态"行
            health_status_patterns = [
                r'健康状态[：:\s]*([🟢🟡🔴\s]*)([^\n]*)',
                r'状态[：:\s]*([🟢🟡🔴\s]*)([^\n]*)'
            ]

            for pattern in health_status_patterns:
                matches = re.findall(pattern, analysis_text)
                if matches:
                    for match in matches:
                        emoji = match[0].strip()
                        text = match[1].strip()

                        # 根据表情符号和文本综合判断
                        if '🟢' in emoji or '健康' in text or '正常' in text or '良好' in text:
                            # 健康状态，进一步根据关键词细分
                            if '优秀' in text or '极好' in text or '完美' in text:
                                return 95
                            elif '非常健康' in text or '很健康' in text:
                                return 90
                            else:
                                return 85
                        elif '🟡' in emoji or '警告' in text or '注意' in text or '偏高' in text:
                            # 警告状态，进一步细分
                            if '轻微' in text or '轻度' in text or '略高' in text:
                                return 75
                            elif '中度' in text or '明显' in text:
                                return 65
                            else:
                                return 60
                        elif '🔴' in emoji or '危险' in text or '严重' in text or '异常' in text:
                            # 危险状态
                            if '严重' in text or '危急' in text:
                                return 20
                            elif '中度' in text:
                                return 40
                            else:
                                return 30

            # 3. 最后根据整体文本内容判断
            text_lower = analysis_text.lower()
            if any(word in text_lower for word in ['优秀', '极好', '完美', 'excellent', 'outstanding']):
                return 95
            elif any(word in text_lower for word in ['很好', '非常好', 'very good', 'very healthy']):
                return 90
            elif any(word in text_lower for word in ['良好', '健康', '正常', 'good', 'healthy', 'normal']):
                return 85
            elif any(word in text_lower for word in ['一般', '中等', '中等水平', 'average', 'medium']):
                return 75
            elif any(word in text_lower for word in ['警告', '注意', '需要关注', 'warning', 'attention']):
                return 60
            elif any(word in text_lower for word in ['较差', '不好', '差', 'poor', 'bad']):
                return 45
            elif any(word in text_lower for word in ['危险', '严重', '异常', 'critical', 'danger', 'error']):
                return 30
            else:
                # 默认返回中间值
                return 70

        except Exception as e:
            print(f"提取健康评分失败: {str(e)}")
            return 50  # 默认值


    def _extract_health_score(self, analysis_text: str) -> int:
        """
        从大模型响应中提取健康评分
        """
        # 尝试多种匹配模式
        patterns = [
            r'总体评分[：:\s]*\[?(\d{1,3})\]?\s*分',
            r'评分[：:\s]*\[?(\d{1,3})\]?',
            r'分数[：:\s]*\[?(\d{1,3})\]?',
            r'(\d{1,3})\s*分',
            r'健康评分[：:\s]*(\d{1,3})',
            r'score[：:\s]*(\d{1,3})',
            r'Score[：:\s]*(\d{1,3})'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, analysis_text)
            if matches:
                try:
                    # 取最后一个匹配（通常是最新的评分）
                    score = int(matches[-1])
                    # 确保分数在合理范围内
                    return max(0, min(100, score))
                except:
                    continue

        # 如果没有找到评分，根据关键词估算
        if any(word in analysis_text for word in ["健康", "正常", "良好", "优秀", "正常", "OK"]):
            return 85
        elif any(word in analysis_text for word in ["警告", "注意", "偏高", "较高", "Warning"]):
            return 60
        elif any(word in analysis_text for word in ["危险", "严重", "异常", "Critical", "Error"]):
            return 30
        else:
            # 默认返回中间值
            return 50

    async def process_batch(self, kpi_files: list) -> list:
        """
        批量处理KPI文件  控制并发数
        """
        self.is_running = True
        self.results = []
        total_files = len(kpi_files)

        print(f"🚀 开始批量分析 {total_files} 个KPI文件")
        self._update_progress(0, total_files, "开始批量分析...")

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(5)  # 限制同时5个并发

        async def bounded_analyze(kpi_info):
            """带并发限制的分析函数"""
            async with semaphore:
                return await self.analyze_single_kpi(
                    None,  # 不使用共享session，让每个任务自己创建
                    kpi_info["kpi_path"],
                    kpi_info["log_filename"],
                    kpi_info["tar_filename"]
                )

        # 创建任务列表
        tasks = [bounded_analyze(kpi_info) for kpi_info in kpi_files]

        # 使用as_completed逐步处理结果
        valid_results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                if result:
                    valid_results.append(result)

                # 更新进度
                self._update_progress(
                    i + 1,
                    total_files,
                    f"已完成 {i + 1}/{total_files} 个文件分析"
                )

            except Exception as e:
                print(f"❌ 任务 {i} 异常: {str(e)}")
                # 创建失败记录
                if i < len(kpi_files):
                    failed_result = self._create_failed_result(
                        kpi_files[i]["tar_filename"],
                        kpi_files[i]["log_filename"],
                        kpi_files[i]["kpi_path"],
                        f"分析异常: {str(e)}"
                    )
                    valid_results.append(failed_result)

        # 更新结果列表
        with self.results_lock:
            self.results = valid_results
            # 按评分从高到低排序
            self.results.sort(key=lambda x: x.get("health_score", 0), reverse=True)

        self.is_running = False
        self._update_progress(total_files, total_files, f"分析完成，共分析 {len(valid_results)} 个文件")

        print(f"✅ 批量分析完成，共分析 {len(valid_results)} 个文件")
        return valid_results

    def get_sorted_results(self) -> list:
        """获取排序后的结果"""
        with self.results_lock:
            return sorted(self.results, key=lambda x: x["health_score"], reverse=True)


# ==============================
# 批量处理相关函数
# ==============================

# 全局变量存储批量处理状态
batch_processing_status = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current": 0,
    "message": "",
    "results": []
}
batch_status_lock = threading.Lock()


# def get_batch_kpi_logs():
#     """
#     获取批量KPI日志文件
#     """
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({
#                 "status": "error",
#                 "message": "请求数据为空"
#             }), 400
#
#         # 获取参数
#         jump_server_name = data.get("jump_server_name")
#         # base_path = data.get("base_path", "D:\\123\\111\\backbrd")
#         base_path = data.get("base_path", "F:\\")
#
#         # 规范化base_path
#         base_path = base_path.rstrip('\\')
#
#         print(f"🔍 开始查找tar文件，基础路径: {base_path}")
#
#         # 从openssh.json加载Windows跳板机配置
#         with open('openssh.json', 'r', encoding='utf-8') as f:
#             jump_servers = json.load(f)
#
#         if jump_server_name not in jump_servers:
#             return jsonify({
#                 "status": "error",
#                 "message": f"跳板机 {jump_server_name} 不存在"
#             }), 400
#
#         jump_config = jump_servers[jump_server_name]
#         jump_host = jump_config.get("JUMP_HOST")
#         jump_user = jump_config.get("JUMP_USER")
#         jump_pass = jump_config.get("JUMP_PASS")
#
#         if not all([jump_host, jump_user, jump_pass]):
#             return jsonify({
#                 "status": "error",
#                 "message": "跳板机配置不完整"
#             }), 400
#
#         # 连接到Windows跳板机
#         with WindowsSSHClient(jump_host, jump_user, jump_pass) as win_client:
#             # 创建解压目录（如果不存在）
#             extract_base_path = os.path.join(base_path, "health_kpi_log")
#
#             print(f"🛠️ 基础路径: {base_path}")
#             print(f"🛠️ 解压目录: {extract_base_path}")
#
#             # 首先检查基础目录是否存在
#             check_base_cmd = f'if exist "{base_path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
#             check_base_stdout, _ = win_client.execute_command(check_base_cmd)
#             print(f"基础目录检查: {check_base_stdout}")
#
#             if "NOT_EXISTS" in check_base_stdout:
#                 return jsonify({
#                     "status": "error",
#                     "message": f"基础目录不存在: {base_path}"
#                 }), 400
#
#             # 创建解压目录（如果不存在）
#             mkdir_cmd = f'mkdir "{extract_base_path}" 2>nul'
#             mkdir_result, _ = win_client.execute_command(mkdir_cmd)
#
#             # 检查是否创建成功
#             check_extract_cmd = f'if exist "{extract_base_path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
#             check_extract_stdout, _ = win_client.execute_command(check_extract_cmd)
#             print(f"解压目录检查: {check_extract_stdout}")
#
#             # 查找tar文件
#             print(f"\n🔍 查找tar文件，路径: {base_path}")
#             tar_files = win_client.find_recent_tar_files(base_path, max_days_lookback=2)
#
#             print(f"找到 {len(tar_files)} 个tar文件")
#
#             if not tar_files:
#                 return jsonify({
#                     "status": "success",
#                     "message": "未找到tar文件",
#                     "data": {
#                         "kpi_files": [],
#                         "total_tar_files": 0,
#                         "total_kpi_files": 0,
#                         "statistics": {
#                             "total_tar_files": 0,
#                             "total_kpi_files": 0,
#                             "processed_tar_files": 0,
#                             "files_with_kpi": 0
#                         }
#                     }
#                 })
#
#             kpi_files_info = []
#             processed_files = set()  # 记录已处理的kpi文件，避免重复
#
#             # 统计信息
#             statistics = {
#                 "total_tar_files": len(tar_files),
#                 "processed_tar_files": 0,
#                 "files_with_kpi": 0,
#                 "total_kpi_files": 0,
#                 "tar_files_by_date": {}
#             }
#
#             # 按日期统计tar文件
#             for file_info in tar_files:
#                 tar_date = file_info['date']
#                 if tar_date not in statistics["tar_files_by_date"]:
#                     statistics["tar_files_by_date"][tar_date] = 0
#                 statistics["tar_files_by_date"][tar_date] += 1
#
#             # 处理每个tar文件
#             for i, file_info in enumerate(tar_files):
#                 tar_path = file_info['full_path']
#                 tar_filename = file_info['filename']
#                 tar_date = file_info['date']
#
#                 print(f"\n{'=' * 60}")
#                 print(f"📦 处理第 {i + 1}/{len(tar_files)} 个tar文件: {tar_filename}")
#                 print(f"📅 文件日期: {tar_date}")
#                 print(f"{'=' * 60}")
#
#                 # 在extract_base_path下解压并查找kpi日志
#                 print(f"\n🔧 开始解压并查找kpi日志...")
#                 kpi_logs = win_client.find_kpi_logs_in_tar(tar_path, extract_base_path)
#
#                 print(f"\n📊 查找结果: 找到 {len(kpi_logs)} 个kpi日志")
#
#                 # 更新统计信息
#                 statistics["processed_tar_files"] += 1
#                 if len(kpi_logs) > 0:
#                     statistics["files_with_kpi"] += 1
#                 statistics["total_kpi_files"] += len(kpi_logs)
#
#                 for kpi_log_path in kpi_logs:
#                     log_filename = os.path.basename(kpi_log_path)
#
#                     # 创建基于tar文件名 + kpi文件名的唯一标识
#                     unique_key = f"{tar_filename}|{log_filename}"
#
#                     # 检查是否已经处理过相同tar文件中的相同kpi文件
#                     if unique_key in processed_files:
#                         print(f"⚠️ 跳过重复的kpi文件（相同tar文件）: {log_filename} in {tar_filename}")
#                         continue
#
#                     processed_files.add(unique_key)
#
#                     # 提取tar文件名（不含路径和扩展名）
#                     tar_name_without_ext = os.path.splitext(tar_filename)[0]
#
#                     # 构建新的kpi路径：解压目录 + tar文件名 + kpi日志文件名
#                     new_kpi_path = os.path.join(extract_base_path, tar_name_without_ext, log_filename)
#                     new_kpi_path = new_kpi_path.replace('/', '\\')
#
#                     print(f"  ✅ 原始kpi路径: {kpi_log_path}")
#                     print(f"  ✅ 新kpi路径: {new_kpi_path}")
#
#                     kpi_files_info.append({
#                         "tar_filename": tar_filename,
#                         "log_filename": log_filename,
#                         "kpi_path": new_kpi_path,  # 使用新的路径
#                         "file_date": tar_date,
#                         "file_size": file_info['size']
#                     })
#                     print(f"  ✅ 记录kpi日志: {log_filename} from {tar_filename}")
#
#                 print(f"✅ 从 {tar_filename} 找到 {len(kpi_logs)} 个非重复kpi日志")
#
#             print(f"\n{'=' * 60}")
#             print(f"📋 最终统计信息:")
#             print(f"  - 总tar文件数: {statistics['total_tar_files']}")
#             print(f"  - 已处理tar文件数: {statistics['processed_tar_files']}")
#             print(f"  - 包含kpi的tar文件数: {statistics['files_with_kpi']}")
#             print(f"  - 总kpi日志文件数: {len(kpi_files_info)}")
#             print(f"  - 按日期分布:")
#             for date, count in statistics["tar_files_by_date"].items():
#                 print(f"    {date}: {count} 个文件")
#             print(f"{'=' * 60}")
#
#             if kpi_files_info:
#                 return jsonify({
#                     "status": "success",
#                     "message": f"找到 {len(kpi_files_info)} 个kpi日志文件",
#                     "data": {
#                         "kpi_files": kpi_files_info,
#                         "total_kpi_files": len(kpi_files_info),
#                         "statistics": {
#                             "total_tar_files": len(tar_files),
#                             "processed_tar_files": statistics["processed_tar_files"],
#                             "files_with_kpi": statistics["files_with_kpi"],
#                             "total_kpi_files": len(kpi_files_info)
#                         }
#                     }
#                 })
#             else:
#                 return jsonify({
#                     "status": "success",
#                     "message": "未找到kpi日志文件",
#                     "data": {
#                         "kpi_files": [],
#                         "total_kpi_files": 0,
#                         "statistics": statistics
#                     }
#                 })
#
#     except Exception as e:
#         print(f"❌ 获取批量KPI日志失败: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             "status": "error",
#             "message": f"获取批量KPI日志失败: {str(e)}"
#         }), 500

def get_batch_kpi_logs():
    """
    获取批量KPI日志文件 - 跳过解压直接返回文件信息
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求数据为空"
            }), 400

        # 获取参数
        jump_server_name = data.get("jump_server_name")
        base_path = data.get("base_path", "F:\\")

        # 规范化base_path
        base_path = base_path.rstrip('\\')

        print(f"🔍 开始查找KPI文件，基础路径: {base_path}")

        # 从openssh.json加载Windows跳板机配置
        with open('openssh.json', 'r', encoding='utf-8') as f:
            jump_servers = json.load(f)

        if jump_server_name not in jump_servers:
            return jsonify({
                "status": "error",
                "message": f"跳板机 {jump_server_name} 不存在"
            }), 400

        jump_config = jump_servers[jump_server_name]
        jump_host = jump_config.get("JUMP_HOST")
        jump_user = jump_config.get("JUMP_USER")
        jump_pass = jump_config.get("JUMP_PASS")

        if not all([jump_host, jump_user, jump_pass]):
            return jsonify({
                "status": "error",
                "message": "跳板机配置不完整"
            }), 400

        # 连接到Windows跳板机
        with WindowsSSHClient(jump_host, jump_user, jump_pass) as win_client:
            # 健康KPI日志的基础路径
            health_kpi_base = os.path.join(base_path, "health_kpi_log")

            print(f"🛠️ 健康KPI日志基础路径: {health_kpi_base}")

            # 检查目录是否存在
            check_cmd = f'if exist "{health_kpi_base}\\" (echo EXISTS) else (echo NOT_EXISTS)'
            check_base_stdout, _ = win_client.execute_command(check_cmd)
            print(f"健康KPI日志目录检查: {check_base_stdout}")

            if "NOT_EXISTS" in check_base_stdout:
                return jsonify({
                    "status": "error",
                    "message": f"健康KPI日志目录不存在: {health_kpi_base}"
                }), 400

            # 查找所有网元目录下的kpi日志文件
            kpi_files_info = []

            # 列出health_kpi_log下的所有目录（每个网元一个目录）
            list_dirs_cmd = f'dir "{health_kpi_base}" /B /AD'
            dirs_stdout, _ = win_client.execute_command(list_dirs_cmd)

            if not dirs_stdout.strip():
                return jsonify({
                    "status": "success",
                    "message": "未找到网元目录",
                    "data": {
                        "kpi_files": [],
                        "total_tar_files": 0,
                        "total_kpi_files": 0,
                        "statistics": {
                            "total_tar_files": 0,
                            "total_kpi_files": 0,
                            "processed_tar_files": 0,
                            "files_with_kpi": 0
                        }
                    }
                })

            # 解析目录列表
            dirs = [d.strip() for d in dirs_stdout.strip().splitlines() if d.strip()]
            print(f"找到 {len(dirs)} 个网元目录")

            # 遍历每个网元目录，查找kpi日志文件
            for dir_name in dirs:
                dir_path = os.path.join(health_kpi_base, dir_name)

                # 查找目录中的kpi_*.log文件
                find_kpi_cmd = f'dir "{dir_path}\\kpi_*.log" /B'
                kpi_stdout, _ = win_client.execute_command(find_kpi_cmd)

                if kpi_stdout.strip():
                    kpi_files = [f.strip() for f in kpi_stdout.strip().splitlines() if f.strip()]

                    for kpi_file in kpi_files:
                        kpi_path = os.path.join(dir_path, kpi_file)

                        # 从目录名提取tar文件名（格式：tar文件名_IP）
                        tar_filename = dir_name + '.tar'

                        kpi_files_info.append({
                            "tar_filename": tar_filename,
                            "log_filename": kpi_file,
                            "kpi_path": kpi_path,
                            "file_date": "",  # 可以从文件属性获取，但这里简化处理
                            "file_size": 0
                        })

                        print(f"✅ 找到KPI文件: {kpi_file} in {dir_name}")

            print(f"\n{'=' * 60}")
            print(f"📋 最终统计信息:")
            print(f"  - 总KPI日志文件数: {len(kpi_files_info)}")
            print(f"{'=' * 60}")

            # 按日期统计（这里简化，都归为今天）
            statistics = {
                "total_tar_files": len(set([f["tar_filename"] for f in kpi_files_info])),
                "processed_tar_files": len(set([f["tar_filename"] for f in kpi_files_info])),
                "files_with_kpi": len(set([f["tar_filename"] for f in kpi_files_info])),
                "total_kpi_files": len(kpi_files_info),
                "tar_files_by_date": {"2026-02-26": len(kpi_files_info)}
            }

            if kpi_files_info:
                return jsonify({
                    "status": "success",
                    "message": f"找到 {len(kpi_files_info)} 个kpi日志文件",
                    "data": {
                        "kpi_files": kpi_files_info,
                        "total_kpi_files": len(kpi_files_info),
                        "statistics": statistics
                    }
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "未找到kpi日志文件",
                    "data": {
                        "kpi_files": [],
                        "total_kpi_files": 0,
                        "statistics": statistics
                    }
                })

    except Exception as e:
        print(f"❌ 获取批量KPI日志失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"获取批量KPI日志失败: {str(e)}"
        }), 500


def analyze_batch_kpi_logs():
    """
    批量分析KPI日志
    """
    global batch_processing_status

    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求数据为空"
            }), 400

        kpi_files = data.get("kpi_files", [])

        if not kpi_files:
            return jsonify({
                "status": "error",
                "message": "未提供KPI文件信息"
            }), 400

        # 检查是否已有分析在进行
        with batch_status_lock:
            if batch_processing_status["is_running"]:
                return jsonify({
                    "status": "error",
                    "message": "已有批量分析在进行中"
                }), 400

            # 重置状态
            batch_processing_status = {
                "is_running": True,
                "progress": 0,
                "total": len(kpi_files),
                "current": 0,
                "message": "开始批量分析...",
                "results": [],
                "start_time": time.time()
            }

        # 启动后台线程进行批量分析
        def run_batch_analysis():
            global batch_processing_status
            try:
                # 创建处理器
                processor = BatchKPIProcessor(SERVER_API_URL, max_workers=10)

                def progress_callback(current, total, message):
                    with batch_status_lock:
                        batch_processing_status["current"] = current
                        batch_processing_status["total"] = total
                        batch_processing_status["message"] = message
                        batch_processing_status["progress"] = int((current / total) * 100)

                processor.set_progress_callback(progress_callback)

                # 运行批量分析
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                results = loop.run_until_complete(processor.process_batch(kpi_files))

                with batch_status_lock:
                    batch_processing_status["results"] = results
                    batch_processing_status["is_running"] = False
                    batch_processing_status["message"] = f"分析完成，共分析 {len(results)} 个文件"
                    batch_processing_status["end_time"] = time.time()

                    duration = batch_processing_status["end_time"] - batch_processing_status["start_time"]
                    batch_processing_status["duration"] = f"{duration:.1f}秒"

                print(f"✅ 批量分析完成，耗时 {duration:.1f}秒")

            except Exception as e:
                print(f"❌ 批量分析失败: {str(e)}")
                import traceback
                traceback.print_exc()

                with batch_status_lock:
                    batch_processing_status["is_running"] = False
                    batch_processing_status["message"] = f"分析失败: {str(e)}"

            finally:
                loop.close()

        # 启动后台线程
        analysis_thread = threading.Thread(target=run_batch_analysis, daemon=True)
        analysis_thread.start()

        return jsonify({
            "status": "success",
            "message": "批量分析已开始",
            "data": {
                "total_files": len(kpi_files),
                "started_at": time.time()
            }
        })

    except Exception as e:
        print(f"❌ 启动批量分析失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"启动批量分析失败: {str(e)}"
        }), 500


def get_batch_analysis_status():
    """
    获取批量分析状态
    """
    global batch_processing_status

    with batch_status_lock:
        # 准备返回数据
        response_data = {
            "is_running": batch_processing_status.get("is_running", False),
            "progress": batch_processing_status.get("progress", 0),
            "current": batch_processing_status.get("current", 0),
            "total": batch_processing_status.get("total", 0),
            "message": batch_processing_status.get("message", "")
        }

        # 如果分析完成，包含结果
        if not batch_processing_status.get("is_running", False) and batch_processing_status.get("results"):
            results = batch_processing_status["results"]

            # 确保每个结果都有必要字段且类型正确
            formatted_results = []
            for result in results:

                problem_items = result.get("problem_items")
                if problem_items is None:
                    problem_items = 0
                elif isinstance(problem_items, str):
                    try:
                        problem_items = int(problem_items)
                    except:
                        problem_items = 0
                elif isinstance(problem_items, (int, float)):
                    problem_items = int(problem_items)
                else:
                    problem_items = 0

                # 确保 total_items 是整数
                total_items = result.get("total_items")
                if total_items is None:
                    total_items = 7
                elif isinstance(total_items, str):
                    try:
                        total_items = int(total_items)
                    except:
                        total_items = 7
                elif isinstance(total_items, (int, float)):
                    total_items = int(total_items)
                else:
                    total_items = 7

                # 确保 health_score 是数字
                health_score = result.get("health_score", 0)
                if health_score is None:
                    health_score = 0.0
                elif isinstance(health_score, str):
                    try:
                        health_score = float(health_score)
                    except:
                        health_score = 0.0
                elif isinstance(health_score, (int, float)):
                    health_score = float(health_score)
                else:
                    health_score = 0.0

                # 确保 health_score 是有效数字
                if math.isnan(health_score):
                    health_score = 0.0

                formatted_result = {
                    "tar_filename": str(result.get("tar_filename", "")),
                    "log_filename": str(result.get("log_filename", "")),
                    "kpi_path": str(result.get("kpi_path", "")),
                    "health_score": health_score,
                    "problem_items": problem_items,  
                    "total_items": total_items, 
                    "analysis_result": str(result.get("analysis_result", "")),
                    "status": str(result.get("status", "failed")),
                    "timestamp": str(result.get("timestamp", ""))
                }

                formatted_results.append(formatted_result)

            response_data["results"] = formatted_results
            response_data["duration"] = batch_processing_status.get("duration", "")

        return jsonify({
            "status": "success",
            "data": response_data
        })


def get_kpi_detail_data():
    """
    获取单个KPI日志的详细数据
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "请求数据为空"
            }), 400

        log_filename = data.get("log_filename")
        kpi_path = data.get("kpi_path")
        tar_filename = data.get("tar_filename")
        jump_server_name = data.get("jump_server_name", "燕郊_1B4-1实验室")
        sampling = data.get("sampling", True)

        if not all([log_filename, kpi_path, jump_server_name]):
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: log_filename, kpi_path, jump_server_name"
            }), 400

        print(f"🔍 获取真实KPI数据: {log_filename}")
        print(f"📁 文件路径: {kpi_path}")
        print(f"🖥️  跳板机: {jump_server_name}")
        print(f"📊 抽样处理: {'启用' if sampling else '禁用'}")

        # 1. 从openssh.json加载跳板机配置
        with open('openssh.json', 'r', encoding='utf-8') as f:
            jump_servers = json.load(f)

        if jump_server_name not in jump_servers:
            return jsonify({
                "status": "error",
                "message": f"跳板机 {jump_server_name} 不存在"
            }), 400

        jump_config = jump_servers[jump_server_name]

        jump_host = jump_config.get("JUMP_HOST")
        jump_user = jump_config.get("JUMP_USER")
        jump_pass = jump_config.get("JUMP_PASS")

        if not all([jump_host, jump_user, jump_pass]):
            return jsonify({
                "status": "error",
                "message": "跳板机配置不完整"
            }), 400

        # 2. 连接到Windows跳板机并读取文件

        with WindowsSSHClient(jump_host, jump_user, jump_pass) as win_client:
            # 3. 检查文件是否存在
            check_cmd = f'if exist "{kpi_path}" (echo EXISTS) else (echo NOT_EXISTS)'
            stdout, stderr = win_client.execute_command(check_cmd)

            if "NOT_EXISTS" in stdout:
                print(f"❌ 文件不存在: {kpi_path}")
                return jsonify({
                    "status": "error",
                    "message": f"KPI文件不存在: {kpi_path}"
                }), 404

            print(f"✅ 文件存在: {kpi_path}")

            # 4. 使用改进的文件读取方法
            print(f"📖 使用PowerShell读取二进制文件...")

            # 使用PowerShell的Get-Content
            ps_cmd = f'powershell "$bytes = Get-Content \'{kpi_path}\' -Encoding Byte -ReadCount 0; [System.BitConverter]::ToString($bytes)"'
            stdout, stderr = win_client.execute_command(ps_cmd)

            if not stdout or stderr:
                print(f"⚠️ PowerShell读取失败: {stderr}")
                return jsonify({
                    "status": "error",
                    "message": "读取文件失败"
                }), 500

            print(f"📄 获取到输出，长度: {len(stdout)} 字符")

            # 5. 解析PowerShell输出的十六进制数据
            try:
                # 移除空格、换行符
                hex_str = stdout.replace(' ', '').replace('\r', '').replace('\n', '').replace('\t', '')
                # 移除可能的BOM字符
                hex_str = hex_str.lstrip('\ufeff')

                if not hex_str or len(hex_str) < 100:
                    print(f"❌ 十六进制数据太短: {len(hex_str)}")
                    return jsonify({
                        "status": "error",
                        "message": "文件内容格式不正确"
                    }), 500

                file_bytes = bytes.fromhex(hex_str.replace('-', ''))
                print(f"✅ 解析成功，原始字节长度: {len(file_bytes)}")
            except Exception as e:
                print(f"❌ 解析十六进制失败: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"解析文件内容失败: {e}"
                }), 500

            # 6. 使用parse_binary_log_new解析
            print(f"🔧 开始解析二进制数据...")
            original_parsed_data = parse_binary_log_new(file_bytes)

            if not original_parsed_data:
                print(f"❌ 解析失败，数据为空")
                return jsonify({
                    "status": "error",
                    "message": "解析KPI数据失败"
                }), 500

            print(f"✅ 解析成功，原始数据点数: {len(original_parsed_data)}")

            # 7. 抽样处理
            response_data = original_parsed_data
            sampling_info = {
                "sampling_enabled": sampling,
                "original_count": len(original_parsed_data),
                "sampled_count": len(original_parsed_data),
                "sampling_rate": 1.0,
                "method": "none"
            }

            if sampling and len(original_parsed_data) > 10000:
                print(f"📊 数据量过大（{len(original_parsed_data)}条），进行抽样处理...")
                response_data = smart_sample_data(original_parsed_data, sampling_info)
                print(f"📊 抽样后数据量: {len(response_data)}条")
                print(f"📊 抽样率: {sampling_info['sampling_rate']:.1%}")

            # 8. 返回结果
            return jsonify({
                "status": "success",
                "message": "获取KPI详细数据成功",
                "data": {
                    "metrics": response_data,
                    "log_info": {
                        "filename": log_filename,
                        "tar_filename": tar_filename,
                        "path": kpi_path,
                        "total_points": len(response_data),
                        "original_points": len(original_parsed_data),
                        "file_size": len(file_bytes),
                        "jump_server": jump_server_name,
                        "sampling_info": sampling_info
                    }
                }
            })

    except Exception as e:
        print(f"❌ 获取真实KPI详细数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"获取详细数据失败: {str(e)}"
        }), 500


def smart_sample_data(parsed_data, sampling_info):
    """
    抽样数据 与parse_health_log中的抽样逻辑保持一致
    """
    try:
        original_count = len(parsed_data)

        # 计算数据的时间范围
        time_format = "%Y-%m-%d %H:%M:%S"
        start_timestamp = parsed_data[0].get('timestamp')
        end_timestamp = parsed_data[-1].get('timestamp')

        if start_timestamp and end_timestamp:
            start_dt = datetime.strptime(start_timestamp, time_format)
            end_dt = datetime.strptime(end_timestamp, time_format)
            time_span = (end_dt - start_dt).total_seconds()

            print(f"📊 数据时间跨度: {time_span:.0f}秒 ({time_span / 3600:.1f}小时)")

            # 根据时间跨度决定抽样间隔
            if time_span > 86400:  # 超过1天
                # 每59秒取1个点 + 头尾
                time_interval = 59
            elif time_span > 3600:  # 超过1小时
                time_interval = 29
            else:
                time_interval = 1

            print(f"📊 使用时间间隔抽样: 每{time_interval}秒")
            sampling_info["method"] = f"time_interval_{time_interval}s"

            # 按时间间隔抽样
            sampled_data = [parsed_data[0]]  # 包含第一个点
            last_sampled_time = start_dt

            for i in range(1, original_count - 1):
                current_timestamp = parsed_data[i].get('timestamp')
                if current_timestamp:
                    try:
                        current_dt = datetime.strptime(current_timestamp, time_format)
                        time_diff = (current_dt - last_sampled_time).total_seconds()

                        if time_diff >= time_interval:
                            sampled_data.append(parsed_data[i])
                            last_sampled_time = current_dt
                    except:
                        # 如果时间解析失败，使用简单抽样
                        if i % (original_count // 5000) == 0:
                            sampled_data.append(parsed_data[i])

            # 确保包含最后一个点
            if original_count > 1:
                sampled_data.append(parsed_data[-1])

            sampling_info["sampled_count"] = len(sampled_data)
            sampling_info["sampling_rate"] = len(sampled_data) / original_count

            return sampled_data
        else:
            # 如果时间戳解析失败，使用简单抽样
            print("⚠️ 时间戳解析失败，使用简单抽样")
            sampling_info["method"] = "simple_sampling"
            return simple_sample_data(parsed_data, sampling_info)

    except Exception as time_err:
        print(f"⚠️ 时间解析错误，使用简单抽样: {time_err}")
        sampling_info["method"] = "simple_sampling_fallback"
        return simple_sample_data(parsed_data, sampling_info)


def simple_sample_data(parsed_data, sampling_info):
    """
    简单抽样：包含头尾，中间均匀抽样
    """
    original_count = len(parsed_data)

    # 目标抽样到大约1000-2000条数据（适合图表显示）
    target_sample_count = min(2000, max(500, original_count // 10))

    if original_count <= target_sample_count:
        sampling_info["sampled_count"] = original_count
        sampling_info["sampling_rate"] = 1.0
        return parsed_data

    # 计算抽样率
    sample_rate = max(1, original_count // target_sample_count)

    sampled_data = [parsed_data[0]]

    # 对中间数据进行抽样
    for i in range(1, original_count - 1):
        if i % sample_rate == 0:
            sampled_data.append(parsed_data[i])

    if original_count > 1:
        sampled_data.append(parsed_data[-1])

    # 如果抽样后数据还是太多，进一步抽样
    if len(sampled_data) > 5000:
        final_sampled_data = [sampled_data[0]]
        second_sample_rate = max(1, len(sampled_data) // 2000)

        for i in range(1, len(sampled_data) - 1):
            if i % second_sample_rate == 0:
                final_sampled_data.append(sampled_data[i])

        final_sampled_data.append(sampled_data[-1])
        sampled_data = final_sampled_data

    sampling_info["sampled_count"] = len(sampled_data)
    sampling_info["sampling_rate"] = len(sampled_data) / original_count

    return sampled_data

def export_ssd_life_data():
    """
    导出所有网元的SSD寿命数据
    为每个网元生成单独的CSV文件，并生成总览CSV文件
    将所有文件打包成TAR下载
    """
    try:
        jump_server_name = None
        base_path = "F:\\"

        if request.method == 'POST':
 
            data = request.get_json()
            if data:
                jump_server_name = data.get("jump_server_name")
                base_path = data.get("base_path", "F:\\")
        else: 
            jump_server_name = request.args.get("jump_server_name")
            base_path = request.args.get("base_path", "F:\\")

        print(f"📥 收到导出请求 - 方法: {request.method}, 跳板机: {jump_server_name}, 路径: {base_path}")

        if not jump_server_name:
            return jsonify({
                "status": "error",
                "message": "缺少跳板机名称"
            }), 400

        # 规范化base_path
        base_path = base_path.rstrip('\\')
        health_kpi_base = os.path.join(base_path, "health_kpi_log")

        print(f"🔍 开始导出SSD寿命数据，基础路径: {health_kpi_base}")
        print(f"🖥️ 跳板机: {jump_server_name}")

        # 从openssh.json加载Windows跳板机配置
        with open('openssh.json', 'r', encoding='utf-8') as f:
            jump_servers = json.load(f)

        if jump_server_name not in jump_servers:
            return jsonify({
                "status": "error",
                "message": f"跳板机 {jump_server_name} 不存在"
            }), 400

        jump_config = jump_servers[jump_server_name]
        jump_host = jump_config.get("JUMP_HOST")
        jump_user = jump_config.get("JUMP_USER")
        jump_pass = jump_config.get("JUMP_PASS")

        if not all([jump_host, jump_user, jump_pass]):
            return jsonify({
                "status": "error",
                "message": "跳板机配置不完整"
            }), 400

        # 连接到Windows跳板机
        from SshService import WindowsSSHClient

        # 创建内存中的TAR文件
        tar_buffer = io.BytesIO()

        # 统计信息
        stats = {
            'total_dirs': 0,
            'processed_dirs': 0,
            'failed_dirs': 0,
            'no_kpi_files': 0,
            'read_failed': 0,
            'read_failed_details': [],
            'parse_failed': 0,
            'parse_failed_details': [],
            'failed_details': [],
            'retry_success': 0  # 记录重试成功的次数
        }

        with WindowsSSHClient(jump_host, jump_user, jump_pass) as win_client:
            # 检查健康KPI日志目录是否存在
            check_cmd = f'if exist "{health_kpi_base}\\" (echo EXISTS) else (echo NOT_EXISTS)'
            check_base_stdout, _ = win_client.execute_command(check_cmd)

            if "NOT_EXISTS" in check_base_stdout:
                return jsonify({
                    "status": "error",
                    "message": f"健康KPI日志目录不存在: {health_kpi_base}"
                }), 400

            # 列出所有网元目录
            list_dirs_cmd = f'dir "{health_kpi_base}" /B /AD'
            dirs_stdout, _ = win_client.execute_command(list_dirs_cmd)

            if not dirs_stdout.strip():
                return jsonify({
                    "status": "error",
                    "message": "未找到网元目录"
                }), 400

            # 解析目录列表
            dirs = [d.strip() for d in dirs_stdout.strip().splitlines() if d.strip()]
            stats['total_dirs'] = len(dirs)
            print(f"📁 找到 {stats['total_dirs']} 个网元目录")

            # 收集所有网元的SSD寿命数据
            all_ne_data = []  # 用于总览表

            # 创建TAR文件，使用gzip压缩
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar_file:

                for idx, dir_name in enumerate(dirs, 1):
                    try:
                        dir_path = os.path.join(health_kpi_base, dir_name)

                        # 打印进度
                        if idx % 50 == 0:
                            print(f"📊 进度: {idx}/{stats['total_dirs']} 个目录")

                        # 查找目录中的kpi_*.log文件
                        find_kpi_cmd = f'dir "{dir_path}\\kpi_*.log" /B'
                        kpi_stdout, _ = win_client.execute_command(find_kpi_cmd)

                        if not kpi_stdout.strip():
                            stats['no_kpi_files'] += 1
                            stats['failed_details'].append({
                                'dir_name': dir_name,
                                'reason': '没有kpi_*.log文件'
                            })
                            print(f"⚠️ 网元 {dir_name} 没有kpi_*.log文件")
                            continue

                        kpi_files = [f.strip() for f in kpi_stdout.strip().splitlines() if f.strip()]

                        # 处理该网元下的所有kpi文件
                        ne_ssd_data = []
                        has_error = False
                        file_read_errors = []

                        for kpi_file in kpi_files:
                            kpi_path = os.path.join(dir_path, kpi_file)

                            # 打印正在处理的文件
                            print(f"📄 处理文件: {kpi_file} in {dir_name}")

                            # 尝试多次读取文件
                            file_bytes = None
                            read_success = False
                            retry_count = 0
                            max_retries = 3

                            while retry_count < max_retries and not read_success:
                                try:
                                    if retry_count > 0:
                                        print(f"🔄 重试 {retry_count}/{max_retries} 读取 {kpi_file}")
                                        time.sleep(1)  # 重试前等待1秒

                                    # 1: PowerShell读取
                                    ps_cmd = f'powershell "$bytes = Get-Content \'{kpi_path}\' -Encoding Byte -ReadCount 0; [System.Convert]::ToBase64String($bytes)"'
                                    base64_stdout, stderr = win_client.execute_command(ps_cmd)

                                    if base64_stdout and base64_stdout.strip():
                                        try:
                                            base64_str = base64_stdout.strip()
                                            # 清理输出，只取base64部分
                                            if ' ' in base64_str:
                                                base64_str = base64_str.split()[-1]

                                            file_bytes = base64.b64decode(base64_str)
                                            if len(file_bytes) >= 31:  # 最小结构大小
                                                read_success = True
                                                if retry_count > 0:
                                                    stats['retry_success'] += 1
                                                    print(f"✅ 重试 {retry_count} 次后读取成功")
                                                break
                                        except Exception as e:
                                            print(f"⚠️ base64解码失败 (尝试 {retry_count + 1}): {str(e)}")

                                    # 2: 如果PowerShell失败，使用type命令
                                    if not read_success:
                                        print(f"🔄 尝试使用type命令读取 {kpi_file}")
                                        type_cmd = f'type "{kpi_path}"'
                                        type_stdout, type_stderr = win_client.execute_command(type_cmd)

                                        if type_stdout and len(type_stdout) > 0:
                                            # type命令输出的是文本，需要转换
                                            file_bytes = type_stdout.encode('utf-8', errors='ignore')
                                            if len(file_bytes) >= 31:
                                                read_success = True
                                                if retry_count > 0:
                                                    stats['retry_success'] += 1
                                                print(f"✅ 使用type命令读取成功")
                                                break

                                except Exception as e:
                                    print(f"⚠️ 读取尝试 {retry_count + 1} 失败: {str(e)}")

                                retry_count += 1

                            if not read_success:
                                stats['read_failed'] += 1
                                error_detail = {
                                    'dir_name': dir_name,
                                    'file_name': kpi_file,
                                    'file_path': kpi_path,
                                    'retry_count': retry_count,
                                    'error_type': 'read_failed_after_retry'
                                }
                                stats['read_failed_details'].append(error_detail)
                                file_read_errors.append(kpi_file)
                                has_error = True
                                print(f"❌ 所有读取方法都失败 {kpi_file} in {dir_name}")
                                continue

                            try:
                                # 解析二进制数据
                                parsed_data = parse_binary_log_new(file_bytes)

                                # 提取每个时间点的SSD寿命
                                for record in parsed_data:
                                    if 'ssdRemainLife' in record:
                                        ne_ssd_data.append({
                                            'timestamp': record.get('timestamp', ''),
                                            'ssd_life': record.get('ssdRemainLife', 0)
                                        })

                                print(f"✅ 成功解析 {kpi_file}, 得到 {len(parsed_data)} 条记录")

                            except Exception as e:
                                stats['parse_failed'] += 1
                                stats['parse_failed_details'].append({
                                    'dir_name': dir_name,
                                    'file_name': kpi_file,
                                    'file_path': kpi_path,
                                    'error_type': 'parse_error',
                                    'error_msg': str(e)
                                })
                                has_error = True
                                print(f"❌ 解析文件失败 {kpi_file}: {str(e)}")
                                continue

                        # 如果该网元有SSD数据
                        if ne_ssd_data:
                            stats['processed_dirs'] += 1

                            # 生成该网元的CSV文件名
                            ne_name = dir_name
                            csv_filename = f"{ne_name}_ssdlife.csv"

                            # 创建网元CSV内容
                            csv_buffer = io.StringIO()
                            csv_writer = csv.writer(csv_buffer)
                            csv_writer.writerow(['Timestamp', 'SSD_Remaining_Life(%)'])

                            for item in ne_ssd_data:
                                csv_writer.writerow([item['timestamp'], item['ssd_life']])

                            # 创建TAR信息对象并添加到TAR文件
                            csv_data = csv_buffer.getvalue().encode('utf-8-sig')
                            csv_info = tarfile.TarInfo(name=csv_filename)
                            csv_info.size = len(csv_data)
                            csv_info.mtime = time.time()
                            tar_file.addfile(tarinfo=csv_info, fileobj=io.BytesIO(csv_data))

                            # 获取最新的一条记录用于总览表
                            latest = ne_ssd_data[-1]
                            all_ne_data.append({
                                'ne_name': ne_name,
                                'latest_ssd_life': latest['ssd_life'],
                                'latest_timestamp': latest['timestamp']
                            })

                            if file_read_errors:
                                print(f"⚠️ 网元 {ne_name} 部分文件读取失败: {', '.join(file_read_errors)}")
                            print(f"✅ 处理网元: {ne_name}, 数据点: {len(ne_ssd_data)}, 最新寿命: {latest['ssd_life']}%")
                        else:
                            if has_error:
                                stats['failed_dirs'] += 1
                                stats['failed_details'].append({
                                    'dir_name': dir_name,
                                    'reason': f'所有文件读取失败: {", ".join(file_read_errors)}'
                                })
                                print(f"❌ 网元 {dir_name} 所有文件读取失败")
                            else:
                                stats['no_kpi_files'] += 1

                    except Exception as e:
                        stats['failed_dirs'] += 1
                        stats['failed_details'].append({
                            'dir_name': dir_name,
                            'reason': str(e)
                        })
                        print(f"❌ 处理网元目录失败 {dir_name}: {str(e)}")
                        continue

                # 生成总览CSV文件 按SSD寿命从低到高排序
                if all_ne_data:
                    all_ne_data.sort(key=lambda x: x['latest_ssd_life'])

                    overview_buffer = io.StringIO()
                    csv_writer = csv.writer(overview_buffer)
                    csv_writer.writerow(
                        ['Rank', 'NE_Name', 'Latest_SSD_Life(%)', 'Latest_Timestamp', 'Health_Status'])

                    for idx, ne in enumerate(all_ne_data, 1):
                        # 根据寿命添加健康状态
                        life = ne['latest_ssd_life']
                        if life >= 70:
                            status = '健康'
                        elif life >= 30:
                            status = '警告'
                        else:
                            status = '危险'

                        csv_writer.writerow([
                            idx,
                            ne['ne_name'],
                            f"{life:.1f}",
                            ne['latest_timestamp'],
                            status
                        ])

                    # 添加总览CSV到TAR
                    overview_data = overview_buffer.getvalue().encode('utf-8-sig')
                    overview_info = tarfile.TarInfo(name='total_ssdlife.csv')
                    overview_info.size = len(overview_data)
                    overview_info.mtime = time.time()
                    tar_file.addfile(tarinfo=overview_info, fileobj=io.BytesIO(overview_data))

                    # 添加详细的统计信息文件
                    stats_content = f"""SSD寿命数据导出统计报告
{'=' * 70}

📊 基本统计:
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
跳板机: {jump_server_name}
基础路径: {health_kpi_base}

📁 目录统计:
总网元目录数: {stats['total_dirs']}
成功处理网元: {stats['processed_dirs']}
处理失败网元: {stats['failed_dirs']}
无KPI文件网元: {stats['no_kpi_files']}
文件读取失败: {stats['read_failed']}
解析失败: {stats['parse_failed']}

{'=' * 70}

📈 寿命统计:
总有效网元: {len(all_ne_data)}
健康网元(≥70%): {len([n for n in all_ne_data if n['latest_ssd_life'] >= 70])}
警告网元(30-69%): {len([n for n in all_ne_data if 30 <= n['latest_ssd_life'] < 70])}
危险网元(<30%): {len([n for n in all_ne_data if n['latest_ssd_life'] < 30])}
平均寿命: {sum(n['latest_ssd_life'] for n in all_ne_data) / len(all_ne_data):.1f}%

{'=' * 70}

寿命最低的前10个网元:
"""
                    # 添加前10个最低寿命网元
                    for i, ne in enumerate(all_ne_data[:10], 1):
                        stats_content += f"{i:2d}. {ne['ne_name']:30} {ne['latest_ssd_life']:.1f}%\n"

                    # 添加读取失败详情
                    if stats['read_failed_details']:
                        stats_content += f"\n{'=' * 70}\n"
                        stats_content += "❌ 文件读取失败详情:\n"
                        for i, failed in enumerate(stats['read_failed_details'], 1):
                            stats_content += f"\n{i}. 网元: {failed['dir_name']}\n"
                            stats_content += f"   文件: {failed['file_name']}\n"
                            stats_content += f"   路径: {failed['file_path']}\n"
                            stats_content += f"   重试次数: {failed.get('retry_count', 0)}\n"

                    # 添加解析失败详情
                    if stats['parse_failed_details']:
                        stats_content += f"\n{'=' * 70}\n"
                        stats_content += "❌ 文件解析失败详情:\n"
                        for i, failed in enumerate(stats['parse_failed_details'], 1):
                            stats_content += f"\n{i}. 网元: {failed['dir_name']}\n"
                            stats_content += f"   文件: {failed['file_name']}\n"
                            stats_content += f"   路径: {failed['file_path']}\n"
                            stats_content += f"   错误: {failed.get('error_msg', 'unknown')}\n"

                    # 添加处理失败详情
                    if stats['failed_details']:
                        stats_content += f"\n{'=' * 70}\n"
                        stats_content += "❌ 网元处理失败详情:\n"
                        for i, failed in enumerate(stats['failed_details'], 1):
                            stats_content += f"\n{i}. 网元: {failed['dir_name']}\n"
                            stats_content += f"   原因: {failed.get('reason', 'unknown')}\n"

                    stats_data = stats_content.encode('utf-8')
                    stats_info = tarfile.TarInfo(name='statistics.txt')
                    stats_info.size = len(stats_data)
                    stats_info.mtime = time.time()
                    tar_file.addfile(tarinfo=stats_info, fileobj=io.BytesIO(stats_data))

                    print(f"\n{'=' * 70}")
                    print(f"📊 最终统计:")
                    print(f"  - 总目录数: {stats['total_dirs']}")
                    print(f"  - 成功处理: {stats['processed_dirs']}")
                    print(f"  - 处理失败: {stats['failed_dirs']}")
                    print(f"  - 无KPI文件: {stats['no_kpi_files']}")
                    print(f"  - 文件读取失败: {stats['read_failed']}")
                    print(f"  - 重试成功: {stats['retry_success']}")
                    print(f"  - 解析失败: {stats['parse_failed']}")
                    print(f"{'=' * 70}")
                    print(f"✅ 总览文件生成完成")

            print(f"✅ 所有数据处理完成，共处理 {len(all_ne_data)} 个网元")

            # 准备返回TAR文件
            tar_buffer.seek(0)

            # 生成文件名
            filename = f'ssd_life_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tar.gz'

            print(f"📤 准备返回文件: {filename}, 大小: {tar_buffer.getbuffer().nbytes} 字节")

            return send_file(
                tar_buffer,
                # mimetype='application/gzip',
                mimetype='application/x-gzip',
                as_attachment=True,
                download_name=filename
            )

    except Exception as e:
        print(f"❌ 导出SSD寿命数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"导出SSD寿命数据失败: {str(e)}"
        }), 500