from fastapi import HTTPException
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Union, Dict, Any  # 始终导入这些类型
import json
import pandas as pd
import requests
import time
import hmac
import os
from hashlib import sha256
from get_icenter import IcenterAPI, Content_body_update
from electric_knowledge.data_model import db
from electric_knowledge.utils_icenter import atom_create_page, icenter_children_get
from electric_knowledge.utils_pub import pub_get_employ_name
from flask import request, jsonify
import logging


logger = logging.getLogger("Logger")


def hmacSha256(appSecret, param):
    appsecret = appSecret.encode('utf-8')
    data = param.encode('utf-8')
    signature = hmac.new(appsecret, data, digestmod=sha256).hexdigest()
    return signature

def create_board_data_dictionary_ic_page(board_name, employ_no:str='', token:str=''):
    print(f"employ_no: {employ_no}")
    print(f"employ_token: {token}")
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        #icenterAPI = IcenterAPI(account=employ_no, password=token)
        icenterAPI = IcenterAPI(account=employ_no, token=token)

    url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/96f4dcac2d3d11f095d7db88d9173342/view"
   
    create_title = board_name + '单板'
    first_children_url, first_children_title, first_children_map = icenter_children_get(url, icenterAPI)

    for first_key, first_value in first_children_map.items():
      print(f"first_key[{first_key}], first_value[{first_value}]")
      if (first_key == "R00-单板需求字典-AI知识库用"):
        pageId, spaceId = icenterAPI.get_pageid_spaceid(first_value)
        resp_flag, new_page_id, create_page_flag = atom_create_page(icenterAPI, spaceId, pageId, create_title)
        if create_page_flag:
            print(f"新创建{board_name}单板icenter页面成功")
            create_flag = True
            return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 
        elif resp_flag:       
            print(f"{board_name}单板icenter页面已存在")
            create_flag = False
            return create_flag, "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + new_page_id + "/view" 

def update_board_data_dictionary_ic_page(url, data_dictionary, employ_no='', token=''):
    if not token:
        icenterAPI = IcenterAPI(os.getenv('USERNAME'), password=os.getenv('PASSWORD'))
    elif token:
        #icenterAPI = IcenterAPI(account=employ_no, password=token)
        icenterAPI = IcenterAPI(account=employ_no, token=token)

    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]

    # 获取页面内容与当前版本
    bo_data = icenterAPI.get_page_info(spaceId, pageId, type='whole')
    if not bo_data.get('currentVersion', ''):
        print("无法获取当前版本号，终止更新")
        return {"status": "fail", "msg": "Failed to get current version"}
    else:
        current_version = bo_data.get('currentVersion', '')
        title = bo_data.get('title', '')

    print(f"当前页面title:   {title}")
  
    # 更新页面
    result = icenterAPI.page_set(pageId, spaceId, title, data_dictionary, current_version)

    if (result == True):
      return {"status": "ok", "msg": "update icenter ok"}
    else:
      return {"status": "fail", "msg": "update icenter error"}


def extract_section_no_header(df, start_marker, end_marker, include_start=True, include_end=False):
    """
    从DataFrame中提取指定标记之间的部分（没有表头行的情况）
    Args:
        df: 原始DataFrame（没有表头行）
        start_marker: 起始标记
        end_marker: 结束标记
        include_start: 是否包含起始标记行
        include_end: 是否包含结束标记行
    Returns:
        DataFrame: 提取的部分数据，如果未找到则返回None
    """
    # 查找起始和结束标记的位置
    start_index = None
    end_index = None
    
    for idx, row in df.iterrows():
        # 第一列是索引0（没有列名，只有数字索引）
        cell_value = str(row.iloc[0]).strip()
        
        if cell_value == start_marker:
            start_index = idx
        elif cell_value == end_marker:
            end_index = idx
    
    # 检查是否找到起始标记
    if start_index is None:
        print(f"未找到起始标记'{start_marker}'")
        return None
    
    # 确定提取范围
    if include_start:
        extract_start = start_index
    else:
        extract_start = start_index + 1
    
    if end_index is None:
        # 没有找到结束标记，提取从开始位置到末尾
        extracted_df = df.iloc[extract_start:]
    else:
        if include_end:
            extract_end = end_index + 1
        else:
            extract_end = end_index
        extracted_df = df.iloc[extract_start:extract_end]
    
    # 检查提取的数据是否为空
    if extracted_df.empty:
        print(f"提取的数据为空（标记：{start_marker} 到 {end_marker}）")
        return None
    
    return extracted_df

def get_multi_sections_from_info_dictionary(input_file, sheet_id=None, 
                                            sections=None,
                                            default_start_marker='单板配置类型', 
                                            default_end_marker='硬件子类型',
                                            default_include_start=True,
                                            default_include_end=False):
    """
    从'信息字典'sheet页中提取多个特定部分的内容并合并到同一个HTML表格中
    假设第一行开始就是数据行，没有表头行
    Args:
        input_file: 输入Excel文件
        sheet_id: 指定工作表的索引
        sections: 要提取的部分列表，每个部分是一个字典，包含以下键：
                  - start_marker: 起始标记
                  - end_marker: 结束标记
                  - include_start: 是否包含起始标记行
                  - include_end: 是否包含结束标记行
                  如果sections为None，则使用默认标记提取一个部分
        default_start_marker: 默认起始标记
        default_end_marker: 默认结束标记
        default_include_start: 默认是否包含起始标记行
        default_include_end: 默认是否包含结束标记行
    Returns:
        str: 生成的HTML表格，包含提取的所有部分内容
    """
    try:
        # 读取指定sheet页，header=None表示没有表头行
        try:
            if sheet_id is not None:
                df = pd.read_excel(input_file, sheet_name=sheet_id, header=None)
            else:
                df = pd.read_excel(input_file, sheet_name=0, header=None)
        except Exception as e:
            print(f"读取工作表失败: {str(e)}")
            return ""
        
        # 清理数据
        df = df.fillna('')
        df = df.astype(str)
        
        # 确保至少有1列数据
        if df.shape[1] < 1:
            print("数据列数不足，无法提取信息")
            return ""
        
        # 如果没有指定sections，使用默认配置
        if sections is None:
            sections = [{
                'start_marker': default_start_marker,
                'end_marker': default_end_marker,
                'include_start': default_include_start,
                'include_end': default_include_end
            }]
        
        # 提取所有部分的数据
        all_extracted_data = []
        
        for section_config in sections:
            start_marker = section_config.get('start_marker', default_start_marker)
            end_marker = section_config.get('end_marker', default_end_marker)
            include_start = section_config.get('include_start', default_include_start)
            include_end = section_config.get('include_end', default_include_end)
            
            # 提取当前部分的数据
            section_df = extract_section_no_header(df, start_marker, end_marker, include_start, include_end)
            
            if section_df is not None and not section_df.empty:
                all_extracted_data.append(section_df)
        
        # 检查是否提取到数据
        if not all_extracted_data:
            print("未提取到任何有效数据")
            return ""
        
        # 合并所有部分的数据
        merged_df = pd.concat(all_extracted_data, ignore_index=True)
        
        # 生成HTML表格（没有表头行）
        html_table = '<table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">'
        
        # 添加数据行（直接开始tbody，没有thead）
        html_table += '<tbody>'
        for idx, row in merged_df.iterrows():
            html_table += f'<tr>'           
            for cell in row:
                cell_str = str(cell).replace('\n', '<br>')
                html_table += f'<td>{cell_str}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'
        
        return html_table
        
    except Exception as e:
        print(f"提取过程中出错: {str(e)}")
        return ""


def get_additional_info_dictionary_to_html_table(input_file, sheet_index=None):
    sections = [
        {
            'start_marker': '单板配置类型',
            'end_marker': '硬件子类型',
            'include_start': True,
            'include_end': False
        },
        {
            'start_marker': '业务模型',
            'end_marker': '背板FEC类型',
            'include_start': True,
            'include_end': False
        },
        {
            'start_marker': 'OSU协议类型',
            'end_marker': 'FEC性能增强',
            'include_start': True,
            'include_end': False  # 包含结束标记行
        }
      ]

    addit_info_table = get_multi_sections_from_info_dictionary(input_file, sheet_id=sheet_index, sections=sections)
   
    return addit_info_table

def get_description_info_dictionary_to_html_table(input_file, sheet_index=None): 
    sections = [
        {
            'start_marker': '硬件子类型',
            'end_marker': 'FEC类型',
            'include_start': True,
            'include_end': False
        }
      ]

    desc_info_table = get_multi_sections_from_info_dictionary(input_file, sheet_id=sheet_index, sections=sections)
    
    return desc_info_table

def get_other_info_dictionary_to_html_table(input_file, sheet_index=None):
    sections = [
        {
            'start_marker': 'FEC类型',
            'end_marker': '业务模型',
            'include_start': True,
            'include_end': False
        },
        {
            'start_marker': '背板FEC类型',
            'end_marker': 'OSU协议类型',
            'include_start': True,
            'include_end': False
        },
        {
            'start_marker': 'FEC性能增强',
            'end_marker': '',
            'include_start': True,
            'include_end': False  # 包含结束标记行
        }
      ]

    other_info_table = get_multi_sections_from_info_dictionary(input_file, sheet_id=sheet_index, sections=sections)

    return other_info_table

def get_sheet_context_to_html_table(input_file, sheet_index=None, header=None):
    """
    将Excel文件的指定sheet页转换为完整的HTML表格
    Args:
        input_file: 输入Excel文件
        sheet_index: 指定工作表的索引，默认为None
                    如果为None，先尝试读取名为'说明'的工作表，失败则读取第一个工作表
                    如果指定了索引，则读取对应索引的工作表
        header: 是否读取表头，默认为None表示自动判断（尝试第一行作为表头）
                如果为0，表示第一行作为表头
                如果为None，表示没有表头行，第一行就是数据
    Returns:
        str: 生成的完整HTML表格
    """
    try:
        # 决定要读取哪个工作表
        sheet_name = None
        if sheet_index is not None:
            sheet_name = sheet_index
        else:
            # 先尝试读取名为'说明'的工作表
            try:
                # 检查是否有'说明'工作表
                xl = pd.ExcelFile(input_file)
                if '说明' in xl.sheet_names:
                    sheet_name = '说明'
                else:
                    sheet_name = 0
            except:
                sheet_name = 0
        
        # 读取工作表
        df = pd.read_excel(input_file, sheet_name=sheet_name, header=header)
        
        # 清理数据
        df = df.fillna('')
        df = df.astype(str)
        
        # 生成HTML表格
        html_table = '<table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">'
        
        # 如果有表头（header=0），添加表头行
        if header == 0 and len(df.columns) > 0:
            html_table += '<tbody><tr>'
            for col in df.columns:
                html_table += f'<td>{col}</td>'
            html_table += '</tr></tbody>'
        
        # 添加数据行
        html_table += '<tbody>'
        for idx, row in df.iterrows():
            html_table += '<tr>'
            for cell in row:
                cell_str = str(cell).replace('\n', '<br>')
                html_table += f'<td>{cell_str}</td>'
            html_table += '</tr>'
        html_table += '</tbody></table>'
        
        return html_table
        
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")
        return ""


def import_board_data_dictionary_to_knowledge_base():
    """
    Excel文件上传单板数据字典接口
    ---
    tags:
      - 单板数据字典
    description: 接收POST请求，通过Header传递工号，通过form-data上传Excel文件
    consumes:  # 关键：指定请求内容类型
      - multipart/form-data
    parameters:
      - name: X-Emp-No
        in: header
        description: 员工工号，用于身份验证
        required: true
        type: string
        example: "10164361"
      - name: X-Auth-Value
        in: header
        description: 用户token
        required: true
        type: string
      - name: board
        in: header
        description: 单板名称
        required: true
        type: string
        example: "LB8TF"
      - name: file  # form-data参数名
        in: formData     # 指定为表单数据
        description: 上传的Excel文件(xlsx格式)
        required: true
        type: file       # 文件类型
        x-mimetype: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet  # 可选MIME类型限制
    responses:
      200:
        description: 文件上传成功，数据已转换并写入成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "成功导入文件"
      400:
        description: 请求参数错误
        schema:
          type: object
          properties:
            error:
              type: string
              example: "无效的文件格式"
      401:
        description: 身份验证失败
        schema:
          type: object
          properties:
            error:
              type: string
              example: "无效的工号"
    """
    employ_no = request.headers.get('X-Emp-No', '')
    employ_token = request.headers.get('X-Auth-Value', '')
    employ_name = pub_get_employ_name(employ_no)
    board_name = request.headers.get('board')

    if 'file' not in request.files:
        return jsonify({"error": "未上传RDC数据文件"}), 400
    
    file = request.files['file']
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持上传 .xlsx 格式文件")

    print(f"人事工号:   {employ_no}")
    print(f"人事名称:   {employ_name}")
    print(f"人事token:  {employ_token}")
    print(f"单板名称:   {board_name}")
    print(f"单板数据字典名称: {file.filename}")
 
    try:
        # 读取Excel文件的所有sheet页名称
        sheet_names = pd.ExcelFile(file).sheet_names
        if not sheet_names:
          return {"code": 203, "status": "failed", "message": f"excel文件为空: {str(e)}", "data": []}

        #print(f"file-sheet_names: {sheet_names}")
        
        data_dictionary = ''
        func_index = 0

        no_need_out_sheet = ['变更', '说明', '性能', '告警', 'L1标准特性']

        for i, sheet_name in enumerate(sheet_names):
          if sheet_name in no_need_out_sheet:
            continue
          
          print(f"trans_file-sheet_names[{i}]: {sheet_name}")

          if (sheet_name=='信息字典'):
            html_context = ""
            func_index += 1
            sheet_dictionary = f"<h2>功能分类{func_index}</h2><h3>功能项名称</h3><p>附加信息-信息字典</p><h3>功能项内容</h3>"
            
            #获取变更内容
            html_context = get_additional_info_dictionary_to_html_table(file, sheet_index=i)

            #从数据字典中提取内容，转为页面格式
            sheet_dictionary += html_context
            data_dictionary += sheet_dictionary

            func_index += 1
            sheet_dictionary = f"<h2>功能分类{func_index}</h2><h3>功能项名称</h3><p>描述信息-信息字典</p><h3>功能项内容</h3>"
            
            #获取变更内容
            html_context = get_description_info_dictionary_to_html_table(file, sheet_index=i)

            #从数据字典中提取内容，转为页面格式
            sheet_dictionary += html_context
            data_dictionary += sheet_dictionary

            func_index += 1
            sheet_dictionary = f"<h2>功能分类{func_index}</h2><h3>功能项名称</h3><p>其他信息-信息字典</p><h3>功能项内容</h3>"
            
            #获取变更内容
            html_context = get_other_info_dictionary_to_html_table(file, sheet_index=i)
            #从数据字典中提取内容，转为页面格式
            sheet_dictionary += html_context
            data_dictionary += sheet_dictionary
          else:            
            html_context = ""
            func_index += 1
            sheet_dictionary = f"<h2>功能分类{func_index}</h2><h3>功能项名称</h3><p>{sheet_name}</p><h3>功能项内容</h3>"
            
            #获取变更内容
            html_context = get_sheet_context_to_html_table(file, sheet_index=i, header=None)

            #从数据字典中提取内容，转为页面格式
            sheet_dictionary += html_context
            data_dictionary += sheet_dictionary

        #print(f"[DEBUG]--------data_dictionary:\n {data_dictionary}")

        #创建单板数据字典icenter页面
        create_flag, page_url = create_board_data_dictionary_ic_page(board_name, employ_no=employ_no, token=employ_token)
        print(f"create_flag: {create_flag}, page_url: {page_url}")

        #更新单板数据字典icenter页面内容
        result = update_board_data_dictionary_ic_page(page_url, data_dictionary, employ_no=employ_no, token=employ_token)
        if (result.get('status') == 'ok'): 
          print(f"update board data dictionary ok: {result}")
        else:
          print(f"update board data dictionary error: {result}")

        #触发数据字典构建知识库流水线
        appId = '00f93948-be93-494b-b1e1-2291c10bc555'
        appSecret = 'sknuTTCwZlkMKODve2b6ztATD2FaRB62gowJvW1i'
        timestamps =  str(int(round(time.time() * 1000)))
        xAppSignature = "sha256=" + hmacSha256(appSecret, appId + timestamps)
        app_code = 'd09fddc101a14bb3bfa0fbd02ed1932a'


        url = "https://icosg.dt.zte.com.cn/ipipeline/build"
  
        headers = {
            'AppCode': app_code,
            'X-Tenant-Id': 'ZTE',
            'X-App-Id': appId,
            'X-Timestamp': timestamps,
            'X-App-Signature-256': xAppSignature
        }

        data = { 
            "flowInitialId": '32a754b2-9ebe-6d83-a0e8-d143999064c3',
            "operationUser": {
                "userId": employ_no,
                "nameZh": employ_name,
                "nameEn": employ_name
            },
            "triggerMode": "manual",
            "runningParameter": {}
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        message = response_data.get("message", "未知错误")

        # 检查返回状态
        if "success" in message:
            print (f"触发数据字典流水线成功: {message}")
            return {"code": 200, "status": "success", "message": f"触发数据字典流水线成功: {message}"}
        else:
            print (f"触发数据字典流水线失败: {message}")
            return {"code": 205, "status": "failed", "message": f"触发数据字典流水线失败: {message}"}
    except Exception as e:
        return {"code": 201, "status": "failed", "message": f"触发数据字典流水线失败: {str(e)}", "data": []}

