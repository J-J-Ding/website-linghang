from datetime import datetime
from typing import List, Optional  # 始终导入这些类型
from electric_knowledge.http_llm import get_dn_aiapplication, extract_transformation_tables, split_markdown_table_by_column, extract_atom_network, extract_atom_net_essential_expression, extract_auto_network_slice_recommendation, extract_recommend_board_hd_svc_deployment, extract_src_req_sum, extract_network_element_business_model_sum, extract_board_change_analysis, extract_get_board_all_feature_rdc_status, extract_get_board_slice_feature_rdc_status, extract_get_board_key_changed_feature, extract_query_change_mode_and_affected_features, call_xingxiaomi_agent,  process_board_related_element_factor, dot_to_board_recommendation

from flask import request, jsonify
# 创建Pydantic模型用于数据验证
import logging

logger = logging.getLogger("Logger")

def process_request_dot_r001():
    """
    process_request_dot_r001
    ---
    tags:
      - AI应用
    description: process_request_dot_r001
    parameters:
      - name: X-Emp-No
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: X-Auth-Value
        in: header
        description: 用户工号，请求头参数，用于身份验证或额外配置（例如 API 密钥或会话令牌）
        required: true
        type: string
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: rdc空间名称
            request_type:
              type: string
              description: 请求类型
          example:   # 示例值
            data: "OTNSW"
            request_type: "网元业务模型部署汇总表"
    responses:
      200:
        description: 成功返回查询内容
    """
    data = request.get_json()
    logger.info(f"-------input_data:{data}\n")
    # 提取参数

    input_str = data.get('data')
    request_type = data.get('request_type')
    # operator_env = 'prod'
    # employ_no = request.headers.get('X-Emp-No')
    # pwd = request.headers.get('X-Auth-Value')
    # X-Auth-Value = data.get('X-Auth-Value')
    # account, token = prob_verify_tocken(operator_env, employ_no, pwd)
    # 在这里执行你的处理逻辑，根据输入数据生成输出数据
    # 这里只是简单地将输入的数据返回作为响应    
    logger.info(f"-------{datetime.now()}:开始提取转换")
    message = ''
    output_data = ""
    if request_type == '产品知识问答':
        appId = 'b53795dba2114cb1ad912741180c0813'
        appKey = 'prod_1600ee51c1944a43b7891dc5c188f59a'
        output_data = get_dn_aiapplication(input_str, appId, appKey)
        message = "产品知识问答完成"
    elif '原始需求表汇总' in request_type:
        product_name = request_type.split('-')[1]
        logger.info(f"-------产品名称：{product_name}")
        markdown_table1 = input_str.replace('\_', '_')
        split_data = markdown_table1.split('\n\nxxxyyy#\n\n')
        logger.info(f"-------split_data:{split_data}")
        output_data = extract_src_req_sum(split_data, product_name)
        message = "基于原始需求表汇总完成"
    elif request_type == '网元业务模型部署表汇总':
        markdown_table1 = input_str.replace('\_', '_')
        output_data = extract_network_element_business_model_sum(markdown_table1)
        message = "基于原始需求汇总表生成网元业务模型部署汇总表完成"
    elif request_type == '变更分析':
        output_data = extract_board_change_analysis(input_str)
    elif request_type == '兴小秘单板硬件':
        result = call_xingxiaomi_agent(input_str)
        output_data = ''
        if result:
            output_data = result.get('content', '')
    elif request_type == '波及要素因子':
        output_data = process_board_related_element_factor(input_str)
        message = "波及要素因子查询完成"
    elif "推荐硬件部署" in request_type:
        product_name = request_type.split('-')[1] + "产品"
        src_flag = True
        mid_flag = False
        data_type = "推荐单板基本信息"
        # 调用处理流水线
        appId = '75b19ec72a894519b7a75eb27c236764'
        appKey = 'prod_e00cb0fcf9fe49c7b2ca9a4bac0ae032'
        dot_md_str = get_dn_aiapplication(input_str, appId, appKey, multi_flag=True)
        output_data = dot_to_board_recommendation(
            dot_md_str=dot_md_str,
            product_name=product_name,
            src_flag=src_flag,
            mid_flag=mid_flag,
            data_type=data_type
        )
        message = "推荐硬件部署完成"
    logger.info(f"-------output_data:{output_data}")
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": message,
        "result": output_data
    })


def process_request_dot_r002():
    """
    process_request_dot_r002
    ---
    tags:
      - AI应用
    description: process_request_dot_r002
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            src_flag:
              type: string
              description: 是否生成原始需求表格
          example:   # 示例值
            data: "L1"
            src_flag: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":''}
    """
    data = request.get_json()
    logger.info(f"-------input_data:{data}\n")
    # 提取参数
    # dot_code = data.get('data')
    # markdown_table = get_llm_result(dot_code)
    markdown_table = data.get('data')
    src_flag = data.get('src_flag')
    # 在这里执行你的处理逻辑，根据输入数据生成输出数据
    # 这里只是简单地将输入的数据返回作为响应    
    logger.info(f"-------{datetime.now()}:开始提取转换")
    if src_flag.upper() == 'Y':
        data = extract_transformation_tables(markdown_table, True)
    else:
        data = extract_transformation_tables(markdown_table)

    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "dot语言代码关键信息提取&转换完成",
        "result": data
    })

def process_request_split_r003():
    """
    process_request_split_r003
    ---
    tags:
      - AI应用
    description: process_request_split_r003
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: md表格字符串
            product_name:
              type: string
              description: 产品形态名称
          example:   # 示例值
            data: "L1"
            product_name: "19700"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":''}
    """
    data = request.get_json()
    # 提取参数
    markdown_table = data.get('data')
    product_name = data.get('product_name')
    
    logger.info(f"-------{datetime.now()}:开始提取转换")
    data = split_markdown_table_by_column(markdown_table, '产品形态', product_name)
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "多产品的网元业务模型自动拆分和补齐完成",
        "result": data
    })

def process_request_split_r004():
    """
    process_request_split_r004
    ---
    tags:
      - AI应用
    description: process_request_split_r004
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: md表格字符串
          example:   # 示例值
            data: "L1"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":''}
    """
    data = request.get_json()
    # 提取参数
    markdown_table = data.get('data')
    logger.info(f"-------{datetime.now()}:开始提取转换")
    data = extract_atom_network(markdown_table)
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于业务模型部署自动生成原子网络拆分完成",
        "result": data
    })

def process_request_split_r005():
    """
    process_request_split_r005
    ---
    tags:
      - AI应用
    description: process_request_split_r005
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: md表格字符串
            mid_flag:
              type: string
              description: 输出中间产物标识
          example:   # 示例值
            data: "L1"
            mid_flag: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":''}
    """
    data = request.get_json()
    # 提取参数
    src_markdown_table = data.get('data')
    src_markdown_table = src_markdown_table.replace('\_', '_')
    new_data = src_markdown_table.split('\n\n')
    
    mid_flag = data.get('mid_flag')
    if mid_flag == 'Y':
        mid_flag = True
    else:
        mid_flag = False

    logger.info(f"-------{datetime.now()}:开始提取转换")
    # baseNetBusinessDatas = querySrcNetBusinessByParams(markdown_flag=True)
    # columns = ['ID', '归属领域', '网元业务方案', '网元业务模型',  '入口业务类型', '交叉类型', '出口业务类型', '入口单板原子模型', '出口单板原子模型', '典型单板实例']
    # svc_model_cfg = "| " + " | ".join(columns) + " |\n"
    # svc_model_cfg += "| " + " | ".join(["---"] * len(columns)) + " |\n"
    # # 添加数据行
    # for row in baseNetBusinessDatas:
    #     svc_model_cfg += "| " + " | ".join(str(row[value]) for value in row) + " |\n"
    data = extract_atom_net_essential_expression(new_data[1], new_data[0], mid_flag)
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于单产品的网元业务模型部署生成原子网络的要素化表达完成",
        "result": data
    })


def process_request_split_r006():
    """
    process_request_split_r006
    ---
    tags:
      - AI应用
    description: process_request_split_r006
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 原子网络字符串
          example:   # 示例值
            data: "L1"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "data":''}
    """
    data = request.get_json()
    # 提取参数
    src_markdown_table = data.get('data')
    src_markdown_table = src_markdown_table.replace('\_', '_')
    new_data = src_markdown_table.split('\n\nxxxyyy#\n\n')
    # split_str = '| ID'
    logger.info(f"-------{datetime.now()}:开始提取转换")
    # atom_network = extract_atom_network(markdown_table)
    # markdown_text = extract_atom_net_essential_expression(markdown_table, False)
    # split_data = markdown_table.split('\n\n|')
    # data = extract_auto_network_slice_recommendation(atom_network, markdown_text)
    data = extract_auto_network_slice_recommendation(new_data[0], new_data[1])
    
    # logger.info(f"----------atom_network_markdown_text:{atom_network_markdown_text}")
    # atom_network = atom_network_markdown_text.split(split_str)[0]
    # markdown_text = atom_network_markdown_text.split(split_str)[1]
    # logger.info(f"----------atom_network:{atom_network}")
    # logger.info(f"----------markdown_text:{markdown_text}")
    # logger.info(f"-------输入数据：{split_data}")
    # if len(split_data) > 1:
    #     data = extract_auto_network_slice_recommendation(split_data[0].replace('\n\n', '\n'), '|' + split_data[1])
    # else:
    #     logger.info("输入有误")
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于原子网络拆分和要素化表达自动生成网络切片完成",
        "result": data
    })

def process_request_split_r007():
    """
    process_request_split_r007
    ---
    tags:
      - AI应用
    description: process_request_split_r007
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
            data_type:
              type: string
              description: 数据类型
          example:   # 示例值
            data: "L1"
            product_name: "Y"
            data_type: "推荐单板基本信息"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    markdown_table = data.get('data')
    product_name = data.get('product_name')
    data_type = data.get('data_type')

    logger.info(f"-------{datetime.now()}:开始提取转换")
    logger.info(f"-------产品名称：{product_name}")
    # logger.info(f"-------输入数据：{markdown_table}")
    
    markdown_table1 = markdown_table.replace('\_', '_')
    split_data = markdown_table1.split('\n\nxxxyyy#\n\n')
    data = ''
    logger.info(f"-------split_data：{split_data}")
    logger.info(f"-------len(split_data)：{len(split_data)}")
    if len(split_data) < 5:
        data = extract_recommend_board_hd_svc_deployment(product_name, split_data[0], split_data[1], split_data[2].replace('\n\n', '\n'), split_data[3], data_type)
    else:
        data = extract_recommend_board_hd_svc_deployment(product_name, split_data[0], split_data[1], split_data[2].replace('\n\n', '\n'), split_data[3], data_type, split_data[4])
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": f"{data_type}完成",
        "result": data
    })


def ensure_string_array(data):
    """确保输入数据是字符串数组"""
    if data is None:
        return []
    
    if isinstance(data, str):
        # 处理逗号分隔的字符串
        if ',' in data:
            return [item.strip() for item in data.split(',') if item.strip()]
        else:
            return [data.strip()] if data.strip() else []
    
    if isinstance(data, list):
        # 处理列表，将所有元素转换为字符串
        result = []
        for item in data:
            if item is not None:
                result.append(str(item).strip())
        return result
    
    # 其他类型，转换为包含单个元素的数组
    return [str(data)]


def process_query_board_all_feature_rdc_status():
    """
    process_query_board_all_feature_rdc_status
    ---
    tags:
      - AI应用
    description: process_query_board_all_feature_rdc_status
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
          example:   # 示例值
            data: "L1"
            product_name: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    board_names = data.get('data')
    product_name = data.get('product_name')
    query_mode = data.get('query_mode')
    logger.info(f"-------{datetime.now()}:开始提取转换")  
    logger.info(f"-------产品名称：{product_name}")
    logger.info(f"-------查询模式：{query_mode}")
    logger.info(f"-------输入数据：{data}")

    # 强制转换为字符串数组
    board_names = ensure_string_array(board_names)

    logger.info(f"-------转换后的board_names: {board_names}")

    data = ''

    # if len(split_data) > 3:
    data = extract_get_board_all_feature_rdc_status(product_name, query_mode, board_names)
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于单板名称查询关联特性的需求交付状态",
        "result": data
    })


def process_query_board_slice_feature_rdc_status():
    """
    process_query_board_slice_feature_rdc_status
    ---
    tags:
      - AI应用
    description: process_query_board_slice_feature_rdc_status
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
          example:   # 示例值
            data: "L1"
            product_name: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    markdown_table = data.get('data')
    product_name = data.get('product_name')
    #query_mode = data.get('query_mode')
    board_name = data.get('board_name')
    logger.info(f"-------{datetime.now()}:开始提取转换")
    logger.info(f"-------产品名称：{product_name}")    
    #logger.info(f"-------查询模式：{query_mode}")

    # logger.info(f"-------输入数据：{markdown_table}")
    board_names = ensure_string_array(board_name)
    logger.info(f"-------单板名称：{board_name}")

    #markdown_table1 = markdown_table.replace('\_', '_')
    #split_data = markdown_table1.split('\n\nxxxyyy#\n\n')

    data = ''
    logger.info(f"-------hd_slices：{markdown_table}")
    data = extract_get_board_slice_feature_rdc_status(product_name, "all", board_names, markdown_table)
    logger.info(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于单板名称查询关联特性的需求交付状态",
        "result": data
    })


def process_query_board_key_changed_content():
    """
    process_query_board_key_changed_content
    ---
    tags:
      - AI应用
    description: process_query_board_key_changed_content
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
          example:   # 示例值
            data: "L1"
            product_name: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    board_names = data.get('data')   
    product_name = data.get('product_name')
    print(f"-------{datetime.now()}:开始提取转换")  
    print(f"-------产品名称：{product_name}")
    print(f"-------输入数据：{data}")

    # 强制转换为字符串数组
    board_names = ensure_string_array(board_names)

    print(f"-------转换后的board_names: {board_names}")

    data = ''

    data = extract_get_board_key_changed_feature(product_name, 'content', board_names)
    print(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于单板名称查询单板关键变更内容及波及特性列表",
        "result": data
    })


def process_query_board_key_changed_feature():
    """
    process_query_board_key_changed_feature
    ---
    tags:
      - AI应用
    description: process_query_board_key_changed_feature
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
          example:   # 示例值
            data: "L1"
            product_name: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    board_names = data.get('data')   
    #query_mode = data.get('query_mode')
    product_name = data.get('product_name')
    print(f"-------{datetime.now()}:开始提取转换")  
    print(f"-------产品名称：{product_name}")
    print(f"-------输入数据：{data}")

    # 强制转换为字符串数组
    board_names = ensure_string_array(board_names)

    print(f"-------转换后的board_names: {board_names}")

    data = ''

    data = extract_get_board_key_changed_feature(product_name, 'feature', board_names)
    print(f"-------{datetime.now()}:结束提取转换")
    return jsonify({
        "status": "success",
        "message": "基于单板名称查询单板包含关键变更内容的特性及变更内容",
        "result": data
    })

def process_query_supported_change_mode_and_affected_features():
    """
    process_query_supported_change_mode_and_affected_features
    ---
    tags:
      - AI应用
    description: process_query_supported_change_mode_and_affected_features
    parameters:
      - name: body  # 关键修改：OpenAPI 2.0使用body参数
        in: body    # 指定参数位置为body
        required: true
        description: 请求体参数（JSON 格式）
        schema:     # 定义JSON结构
          type: object
          required: []
          properties:
            data:
              type: string
              description: 输入的dot源代码字符串
            product_name:
              type: string
              description: 产品名称
          example:   # 示例值
            data: "L1"
            product_name: "Y"
    responses:
      200:
        description: 成功返回数据
        examples:
          application/json: {"code": 200, "status": "success", "message": "获取成功", "board":''}
    """
    data = request.get_json()
    # 提取参数
    changed_mode = data.get('data')   
 
    print(f"-------{datetime.now()}:开始提取转换")  
    print(f"-------输入数据：{data}")

    print(f"-------转换后的changed_mode: {changed_mode}")

    data = ''

    data = extract_query_change_mode_and_affected_features(changed_mode)
    print(f"-------{datetime.now()}:结束提取转换")

    message = ''

    if changed_mode == 'query_supported_change_mode':
      message = '查询当前支持的单板关键变更模式结束'
    else:
      message = '基于单板变更模式查询波及的特性及子特性结束'

    return jsonify({
        "status": "success",
        "message": message,
        "result": data
    })


def process_dot_to_board_recommendation():
    """
process_dot_to_board_recommendation
---
tags:
  - AI应用
parameters:
  - name: body
    in: body
    required: true
    description: 请求体参数JSON格式
    schema:
      type: object
      required: []
      properties:
        dot_source:
          type: string
          description: DOT源码字符串
        product_name:
          type: string
          description: 产品名称默认xx产品
      example:
        dot_source: "graph TD..."
        product_name: "xx产品"
responses:
  200:
    description: 成功返回推荐结果
    examples:
      application/json:
        status: "success"
        message: "处理完成"
        result: ""
    """
    try:
        data = request.get_json()
        logger.info(f"-------input_data:{data}\n")
        # 提取参数
        dot_source = data.get('dot_source')
        product_name = data.get('product_name', '19700产品')
        src_flag = True
        mid_flag = False
        data_type = "推荐单板基本信息"

        # 调用处理流水线
        result = dot_to_board_recommendation(
            dot_source=dot_source,
            product_name=product_name,
            src_flag=src_flag,
            mid_flag=mid_flag,
            data_type=data_type
        )

        return jsonify({
            "status": "success",
            "message": "DOT 源码到推荐单板基本信息处理完成",
            "result": result
        })

    except Exception as e:
        logger.error(f"-------处理流水线异常：{str(e)}")
        return jsonify({
            "status": "error",
            "message": f"处理失败：{str(e)}",
            "result": ""
        })

