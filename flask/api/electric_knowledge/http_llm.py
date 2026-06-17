from openai import OpenAI
import httpx
import re
import os
import pandas as pd
from io import StringIO
import requests
import socket
import hashlib
import json
import pymysql
from itertools import product
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
from typing import List, Union

logger = logging.getLogger("Logger")

from electric_knowledge.db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE, DB_PORT
from electric_knowledge.data_process import MySQLDataImporter
from electric_knowledge.split_r003_completion_algorithm import process_md_table
from electric_knowledge.split_r004_atom_network_algorithm import svc_atom_network_split
from electric_knowledge.split_r005_atom_net_essential_expression import svc_atom_net_essential_expression
from electric_knowledge.split_r006_auto_net_slice_recommendation import auto_network_slice_recommendation
from electric_knowledge.split_r007_auto_hd_recommendation import recommend_board_hd_svc_deployment
from electric_knowledge.utils_pub import pub_get_column_values_from_markdown_table, pub_dict_list_to_markdown_table_reordered
from electric_knowledge.front_board_change_analysis_data_service import querySrcBoardChangeAnalysisByParams
from electric_knowledge.split_r008_board_fs_rd_status import get_board_all_feature_rdc_status,get_board_slice_feature_rdc_status,get_board_key_changed_feature, get_board_change_mode_and_affected_features
from electric_knowledge.front_board_atom_model_relation_data_service import querySrcBoardBusinessAtomByParams
from electric_knowledge.front_business_coreelement_factor_relation_data_service import querySrcCoreElementFactorRelationByParams
from electric_knowledge.front_feature_board_relation_data_service import querySrcFeatureBoardRelation
from electric_knowledge.front_board_tree_data_service import querySrcBoardTreeByParams


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


need_update_columns = ['入口光层业务', '网元业务模型', '出口光层业务']
network_business_model = "网元业务模型"
need_update_columns_src = [network_business_model]

employ_no = '10329743'

DB_CONFIG = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_DATABASE,
    'port': DB_PORT,
    'charset': 'utf8mb3',
    'cursorclass': pymysql.cursors.DictCursor
}

importer = MySQLDataImporter(DB_CONFIG)

def requests_new(method, url, headers, body, data, files=None):
    if method == 'POST':
        response = requests.post(url, headers=headers, json=body, data=data, files=files, verify=False)
    elif method == 'GET':
        response = requests.get(url, headers=headers, verify=False)
    return response


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(e)
        s.close()
        return ""
    
def md5_encrypt(text):
    # 创建一个MD5对象
    md5 = hashlib.md5()
    # 将字符串转换为字节流并进行加密
    md5.update(text.encode('utf-8'))
    # 获取加密后的结果
    encrypted_text = md5.hexdigest()
    return encrypted_text
  
def prob_verify_tocken(operator_env, employ_no, passWord):
    if operator_env == "prod":
        url="https://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
    else:
        url="https://uac.test.zte.com.cn/uaccommauth/auth/comm/verify.serv"
    body={
        "account": employ_no,
        "passWord": passWord,
        "loginClientIp": get_host_ip(),
        "loginSystemCode": "Portal"
    }
    encrypted_text = md5_encrypt(body["account"]+body["passWord"]+body["loginClientIp"]+body["loginSystemCode"])
    body["verifyCode"]=encrypted_text
    receive = requests.post(
        json=body,
        url=url
    )
    if receive.status_code != 200:
        logger.info(f"----------获取uac token失败！uac 接口调用失败！")
        return employ_no, None
    else:
        res = receive.json()
        if res['bo']['code'] == '0000' and 'other' in res:
            account=res['other']['account']
            token=res['other']['token']
        else:
            logger.info(f"----------获取uac token失败！请重新输入长度小于32位的人事密码或者大于等于32位的uac token")
            return employ_no, None
    return account, token
    
def get_dn_aiapplication(content, appId: str=None, appKey:str=None, multi_flag:bool=False):
    url = "https://studio.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat"
    if not appId and not appKey:
        appId = "29b2522a45784ebfa7792489cbb07939"
        appKey = "prod_b561feeb7e114fa6b5cb6e2455724af9"
    data = {
        "chatUuid":"",
        "chatName":"",
        "stream":False,
        "keep": False,
        "text":content
    }  # 需要POST的数据
    if multi_flag:
         data = {
          "chatUuid":"",
          "chatName":"",
          "stream":False,
          "keep": False,
          "text": content,
          "variables":{"src_flag": "Y"}
        }  # 需要POST的数据
        
    headers = {"content-type": 'application/json',
               "Authorization": "Bearer " + appId + "-" + appKey,
               "X-Emp-No": "10329743",
               "X-Auth-Value": ''}  # 请求头部，一般API需要JSON格式的数据，所以设置content-type为application/json
    # print("----------headers:" + str(headers))
    response = requests.post(url, data=json.dumps(data), headers=headers)  # 发起POST请求
    # print(query)
    # print(response.status_code)  # 打印响应的状态码
    # print(str(response))  # 打印响应的JSON数据
    if response.status_code == 200:
        response_json = response.json()
        # print("----------response_json:" + str(response_json))
        result = response_json["bo"]["result"]
    else:
        result = ""
    # print(result) 
    return result

def get_mysqldb_data(table_name, columns):
    columns_str = ', '.join(columns)
    results = []
    if importer.connect():
        importer.cursor.execute(f"select {columns_str} from {table_name} ")
        results = importer.cursor.fetchall()
    return results

def get_business_model_data(data_type:str=''):
    business_model_rate_table_name = 'business_scenario_db.business_model_rate_table'
    business_model_rate_columns = ['network_element_business_model_rate', 'business_type_list']
    business_model_rate_data = get_mysqldb_data(business_model_rate_table_name, business_model_rate_columns)
    business_model_data = []
    if not data_type:
        business_model_table_name = 'business_scenario_db.business_model_table'
        business_model_columns = ['network_element_business_model', 'input_business_type_list', 'crossconnect_type', 'output_business_type_list',
                                  'input_board_model_list', 'output_board_model_list', 'typical_board_examples']
        business_model_data = get_mysqldb_data(business_model_table_name, business_model_columns)
    return business_model_rate_data, business_model_data
        
def process_markdown_table(table_str):
    # 分割表格行
    lines = table_str.strip().split('\n')
    
    # 解析表头和数据行
    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]
    
    # 确定列索引（假设列顺序固定）
    columns = [col.strip() for col in header.split('|') if col.strip()]
    product_index = columns.index('产品形态')
    model_index = columns.index('网元业务模型')
    
    # 处理每一行数据
    processed_rows = []
    for row in data_rows:
        row_line = row.strip().strip('|')
        cells = [c.strip() for c in row_line.split('|')]
        if len(cells) != len(columns):
            continue  # 跳过格式错误的行
        
        if '产品' not in cells[product_index]:
            cells[product_index] += '产品'
        product_type = cells[product_index]
        model_value = cells[model_index]
        
        # 根据产品形态处理网元业务模型
        if 'M721' in product_type:
            parts = model_value.split('/')
            filtered_parts = [part for part in parts if 'OTN-LB' not in part.upper()]
            cells[model_index] = '/'.join(filtered_parts)
        elif '19700' in product_type:
            parts = model_value.split('/')
            filtered_parts = [part for part in parts if 'OTN-CB' not in part.upper()]
            cells[model_index] = '/'.join(filtered_parts)
        processed_rows.append(cells)
    
    # 重新构建Markdown表格
    # 表头和分隔线
    new_table = [header, separator]
    for row in processed_rows:
        new_table.append('| ' + ' | '.join(row) + ' |')
    
    return '\n'.join(new_table)

def markdown_to_dataframe(md):
    lines = [line.strip() for line in md.strip().split('\n') if line.strip()]
    
    # 移除分隔行（包含 --- 的行）
    data_lines = []
    for line in lines:
        if not re.match(r'^\|\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$', line):
            data_lines.append(line)
    
    # 提取单元格
    rows = []
    for line in data_lines:
        # 去掉首尾 |
        line = re.sub(r'^\|\s*|\s*\|$', '', line)
        cells = [cell.strip() for cell in line.split('|')]
        rows.append(cells)
    
    # 第一行是 header
    if not rows:
        return pd.DataFrame()
    
    header = rows[0]
    data = rows[1:]
    return pd.DataFrame(data, columns=header)

def get_results(param1: str, param2: str, param3: str, mysql_data: list, split_signal: str = ','):
    error_info_list = []
    # 在实际应用中，请替换为您的真实函数逻辑
    network_element_business_model_list = []
    input_board_model_list = []
    output_board_model_list = []
    for mysqlData in mysql_data:
        input_business_type_list = set(mysqlData['input_business_type_list'].split(split_signal))
        output_business_type_list = set(mysqlData['output_business_type_list'].split(split_signal))
        if param2.upper() == mysqlData['crossconnect_type']:
            if param1 in input_business_type_list and param3 in output_business_type_list:
                network_element_business_model_list.append(mysqlData['network_element_business_model'])
                input_board_model_list.append(mysqlData['input_board_model_list'])
                output_board_model_list.append(mysqlData['output_board_model_list'])
                error_info_list.append('')
            elif param1 in output_business_type_list and param3 in input_business_type_list:
                network_element_business_model_list.append(mysqlData['network_element_business_model'])
                input_board_model_list.append(mysqlData['output_board_model_list'])
                output_board_model_list.append(mysqlData['input_board_model_list'])
                error_info_list.append('')
    if len(error_info_list) < 1:
        error_info_list.append("输入业务：" + param1 + '，' + "交叉类型：" + param2.upper() + '，' + "输出业务：" + param3 + " 对应的网元业务模型未找到匹配项。请确认LLM是否正确提取了原始输入业务或输出业务")
    return '/'.join(network_element_business_model_list), '/'.join(input_board_model_list), '/'.join(output_board_model_list), '/'.join(error_info_list)


def process_dataframe(md_str, mysql_data):
    """
    Processes a source DataFrame according to the specified logic.

    Args:
        src_df: pandas DataFrame representing the source markdown table.
                Must have columns A, B, C, D, E, F.
    Returns:
        pandas DataFrame representing the destination markdown table dst_table.
    """
    # logger.info(f"--------md_str:{md_str}")
    src_df = markdown_to_dataframe(md_str)
    if not all(col in src_df.columns for col in ['站点名称', '产品形态', '入口光层业务', '网元业务模型', '出口光层业务']):
        raise ValueError("Source DataFrame must contain columns 站点名称, 产品形态, 入口光层业务, 网元业务模型, 出口光层业务.")

    dst_rows = []

    # Iterate through each row of the source table
    for index, row in src_df.iterrows():
        # 1. Split values in columns C, D, E by '/'
        c_parts = row['入口光层业务'].strip().split('-')[0].split('/')
        net_model_list = row['网元业务模型'].split('+')
        d_parts = []
        for net_model in net_model_list:
            if '-' not in net_model:
                d_parts = net_model.strip().split('/')
                break
        e_parts = row['出口光层业务'].strip().split('-')[0].split('/')

        # 2. Generate all combinations (Cartesian product) of the split parts
        combinations = list(product(c_parts, d_parts, e_parts))

        results_with_params = []
        for param1, param2, param3 in combinations:
            result = get_results(param1, param2, param3, mysql_data)
            if not result[0]:
                continue
            results_with_params.append({
                'params': (param1, param2, param3),
                'result': result
            })

        # 4. Group results by the 'result' value to collect associated parameters
        result_groups = {}
        for item in results_with_params:
            res_val = item['result']
            params = item['params']
            if res_val not in result_groups:
                result_groups[res_val] = []
            result_groups[res_val].append(params)

        # 5. For each unique result, create a new row in dst_table
        for unique_result, param_list in result_groups.items():
            network_element_business_model_list = unique_result[0].split('/')
            input_board_model_list = unique_result[1].split('/')
            output_board_model_list = unique_result[2].split('/')
            for index, network_element_business_model in enumerate(network_element_business_model_list):
                # Extract the original A and B values
                if 'M721' in row['产品形态'].upper() and 'OTN-LB' in network_element_business_model.upper():
                    continue
                elif '19700' in row['产品形态'].upper() and 'OTN-CB' in network_element_business_model.upper():
                    continue
                if '产品' not in row['产品形态']:
                    row['产品形态'] = row['产品形态'] + '产品'
                new_row = {'站点名称': row['站点名称'], '产品形态': row['产品形态']}
                # Collect all param1, param2, param3 values that led to this unique_result
                all_param1 = set()
                all_param2 = set()
                all_param3 = set()
                for p1, p2, p3 in param_list:
                    all_param1.add(p1)
                    all_param2.add(p2)
                    all_param3.add(p3)

                # Join the unique parameters back with '/'
                new_row['入口业务类型'] = '/'.join(sorted(list(all_param1)))
                new_row['交叉类型'] = '/'.join(sorted(list(all_param2)))
                new_row['出口业务类型'] = '/'.join(sorted(list(all_param3)))
                new_row['网元业务模型'] = network_element_business_model
                new_row['入口单板模型'] = input_board_model_list[index]
                new_row['出口单板模型'] = output_board_model_list[index]

                dst_rows.append(new_row)

    # Create the destination DataFrame
    dst_df = pd.DataFrame(dst_rows, columns=['站点名称', '产品形态', '网元业务模型', '入口业务类型', '入口单板模型', '交叉类型', '出口业务类型', '出口单板模型'])
    # Optional: Reset index if needed
    dst_df.reset_index(drop=True, inplace=True)
    return dst_df

def get_knowledge(src_contents, mysql_data, need_update_column, split_signal):
    content_list = []
    inputoutput_business = ''
    after_business = ''
    error_info = ""
    if need_update_column != network_business_model:
        content_list = src_contents.split('-')
        before_business = content_list[0]
        if len(content_list) > 1:
            after_business = content_list[1]
        before_business_list = before_business.split('/')
        inputoutput_business_list = []
        for beforeBusiness in before_business_list:
            mysqlData_Flag = False
            for mysqlData in mysql_data:
                if beforeBusiness in mysqlData['business_type_list'].split(split_signal):
                    mysqlData_Flag = True
                    inputoutput_business = mysqlData['network_element_business_model_rate']
                    if after_business.strip():
                        inputoutput_business += after_business.strip()
                    if inputoutput_business not in inputoutput_business_list:
                        inputoutput_business_list.append(inputoutput_business)
            if not mysqlData_Flag:
                error_info += need_update_column + "列业务类型取值为" + beforeBusiness + "没有找到对应的光口业务速率匹配项。请确认LLM是否正确提取了原始业务类型取值" + " /"
                inputoutput_business = beforeBusiness
                if after_business.strip():
                    inputoutput_business += after_business.strip()
                if inputoutput_business not in inputoutput_business_list:
                    inputoutput_business_list.append(inputoutput_business)
        result = '/'.join(inputoutput_business_list)
        error_info = error_info[:-1]
    else:
        src_contents_list = src_contents.split(',')
        crossconnect_type_list = []
        for content in src_contents_list[1].split('+'):
            if '-' not in content:
                crossconnect_type_list = content.strip().split('/')
                break

        c_parts = src_contents_list[0].strip().split('-')[0].split('/')
        d_parts = crossconnect_type_list
        e_parts = src_contents_list[2].strip().split('-')[0].split('/')
        # 2. Generate all combinations (Cartesian product) of the split parts
        combinations = list(product(c_parts, d_parts, e_parts))
        network_element_business_model_list = []
        for param1, param2, param3 in combinations:
            result = get_results(param1, param2, param3, mysql_data)
            if not result[0]:
                continue
            network_element_business_model_list.extend(result[0].split('/'))
        result = '/'.join(list(set(network_element_business_model_list)))
        error_info = ''

    if (not result.strip()):
        result = 'Not Found'
    return result, error_info
   
def get_llm_result(content:str, employ_no:str=employ_no):
    final_content = """
你是一名graphviz dot代码专家，给定如下的dot代码：
{dot_code}
请先仔细理解上述dot代码，然后以每个box为中心，分别提取出与该box相关联的包含 E01、E02、E03和E04取值的tooltip对应的label属性值（tooltip取值中'-'的前后部分取值和label取值中'-'的前后部分取值是一一对应的），并按照如下5个字段的取值逻辑输出成md表格（每个box形成一行）：
1. 站点名称：包含 E01的tooltip对应的label属性值xxxx-yyyy中的yyyy
2. 产品形态：包含 E01的tooltip对应的label属性值xxxx-yyyy中的xxxx
3. 入口光层业务：包含 E02的tooltip对应的label属性值
4. 网元业务模型：由3部分组成：4.1. 包含 E02的tooltip对应的label属性值；4.2. 包含 E03的tooltip对应的label属性值；4.3. 包含 E04的tooltip对应的label属性值，这3部分通过+按顺序拼接起来
5. 出口光层业务：包含 E04的tooltip对应的label属性值
每个box形成输出表格中的一行（包含上述的5个字段），输出内容请不要添加任何解释或注释或说明""".format(dot_code=content)
    # print(f"----------prompt:{final_content}\n")
    openai_api_key = employ_no
    openai_api_base = "http://nebulacoder.dev.zte.com.cn:40081/v1/"
    # openai_api_base = "http://10.55.19.154:30800/api/nebulacoder-server/v1/v1/"
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
        http_client=httpx.Client(trust_env=False)
    )
    
    stream = False
    # 调用接口
    response = client.chat.completions.create(
        model="nebulacoder-v6.0",
        messages=[{"role": "user", "content": final_content}],
        stream=stream,
        max_tokens=8192,
        temperature=0.1,
    )

    output = ""
    try:
        # print(response)
        # print("\n\n")
        output = response.choices[0].message.content
        # print(f"[Output]\n{output}")
    except Exception as err:
        logger.error(f"Error: {err}")
    return output

def extract_markdown_tables(md_text):
    # 匹配 markdown 表格的正则表达式
    table_pattern = re.compile(
        r'(?:^|\n)'                # 行首或换行
        r'((?:\|.*\|.*\n)+'        # 至少一行以|开头和结尾的内容
        r'(?:\|[\s:-]+\|.*\n)'     # 分隔行（至少一行: - : |）
        r'(?:\|.*\|.*\n?)+)',      # 至少一行数据
        re.MULTILINE
    )
    tables = table_pattern.findall(md_text)
    return [table.strip() for table in tables]

    
def split_markdown_table_by_column(markdown_text: str, split_column: str, product_name:str) -> dict:
    """
    根据指定列的不同取值将Markdown表格拆分为多个子表格
    
    :param markdown_text: 包含Markdown表格的字符串
    :param split_column: 用于拆分的列名
    :return: 字典，键为拆分列的不同取值，值为对应的子表格字符串
    """
    
    # result = process_md_table(markdown_text)
    # print(f"--------------result:{result}")
    # return result
    lines = markdown_text.splitlines()
    table_lines = []
    in_table = False
    
    # 1. 定位并提取表格行
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_table:
                break  # 遇到空行结束表格
            continue
            
        if '|' in stripped:
            if not in_table:
                in_table = True
            table_lines.append(stripped)
        elif in_table:
            break  # 遇到非表格行结束表格
    
    if len(table_lines) < 2:
        return {}  # 没有有效的表格
    
    # 2. 解析表头
    header_line = table_lines[0].strip('| ')
    headers = [h.strip() for h in header_line.split('|')]
    
    try:
        split_index = headers.index(split_column.strip())
    except ValueError:
        return {}  # 列名不存在
    
    # 3. 提取分隔行（如果有）
    separator_line = None
    if len(table_lines) > 1 and any('---' in line for line in table_lines[1:2]):
        separator_line = table_lines[1]
    
    # 4. 分组数据行
    groups = {}
    data_start = 2 if separator_line else 1
    for line in table_lines[data_start:]:
        # 跳过可能的分隔行
        if '---' in line or '--' in line:
            continue
            
        row_line = line.strip('|\n')
        cells = [c.strip() for c in row_line.split('|')]
        if len(cells) < len(headers):
            continue  # 跳过列数不匹配的行
            
        group_key = cells[split_index]
        
        if group_key not in groups:
            groups[group_key] = []
        
        groups[group_key].append(line)
    
    # 5. 为每个分组创建子表格
    result = ''
    for key, rows in groups.items():
        product_flag = False
        # 创建子表格
        sub_table = [table_lines[0]]  # 表头行
        if separator_line:
            sub_table.append(separator_line)  # 分隔行
        for row in rows:
            # print(f"---------------row: {row}")
            if product_name in row:
                product_flag = True
                sub_table.append(row)  # 数据行
        # print(f"------------rows: {rows}")
        # print(f"---------------sub_table:{sub_table}") 
        # 转换为字符串
        if product_flag:
            result += process_md_table('\n'.join(sub_table))

    return result


def new_modify_markdown_table(
    markdown_text: str, 
    column_name: str = None, 
    new_values: list = None, 
    add_new_column: bool = False, 
    default_value: str = "",
    duplicate_rows: bool = False,
    columns_to_delete: list = None
) -> str:
    """
    多功能Markdown表格处理函数
    
    :param markdown_text: 包含Markdown表格的字符串
    :param column_name: 需要操作的目标列名
    :param new_values: 要赋值的值列表
    :param add_new_column: 是否新增列
    :param default_value: 新增列时空白单元格的默认值
    :param duplicate_rows: 是否将每行数据复制为两行
    :param columns_to_delete: 要删除的列名列表
    :return: 更新后的Markdown文本
    """
    lines = markdown_text.splitlines()
    table_row_indices = []
    in_table = False
    
    # 1. 定位表格范围
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if in_table:
                break  # 遇到空行结束表格
            continue
            
        if '|' in stripped:
            if not in_table:
                in_table = True
            table_row_indices.append(i)
        elif in_table:
            break  # 遇到非表格行结束表格
    
    if not table_row_indices:
        return markdown_text  # 没有找到表格
    
    # 2. 提取表格内容
    table_lines = [lines[i].strip() for i in table_row_indices]
    
    # 3. 解析表头
    header_line = table_lines[0].strip('| ')
    headers = [h.strip() for h in header_line.split('|')]
    
    # 4. 处理删除列操作（优先执行）
    if columns_to_delete:
        # 确定要删除的列索引
        delete_indices = []
        for col in columns_to_delete:
            try:
                idx = headers.index(col.strip())
                if idx not in delete_indices:
                    delete_indices.append(idx)
            except ValueError:
                pass
        
        # 按索引从大到小排序，以便安全删除
        delete_indices.sort(reverse=True)
        
        # 更新所有行（包括表头、分隔行和数据行）
        for i in range(len(table_lines)):
            row_line = table_lines[i].strip('| ')
            cells = [c.strip() for c in row_line.split('|')]
            
            # 删除指定索引的列
            for idx in delete_indices:
                if idx < len(cells):
                    del cells[idx]
            
            # 重新构建行
            table_lines[i] = '| ' + ' | '.join(cells) + ' |'
        
        # 更新表头
        for idx in delete_indices:
            if idx < len(headers):
                del headers[idx]
    
    # 5. 处理行复制操作
    if duplicate_rows:
        # 确定数据行范围
        data_start = 1
        if len(table_lines) > 1 and any('---' in line for line in table_lines[1:2]):
            data_start = 2
        
        # 复制数据行
        new_table_lines = table_lines[:data_start]  # 保留表头和分隔行
        for i in range(data_start, len(table_lines)):
            # 将每行添加两次
            new_table_lines.append(table_lines[i])
            new_table_lines.append(table_lines[i])
        
        table_lines = new_table_lines
    
    # 6. 处理列操作（新增或更新）
    if column_name is not None and new_values is not None:
        try:
            col_index = headers.index(column_name.strip())
            column_exists = True
        except ValueError:
            col_index = len(headers)  # 新增列位置（默认在最后）
            column_exists = False
        
        # 处理新增列情况
        if add_new_column and not column_exists:
            # 更新表头行
            headers.append(column_name)
            table_lines[0] = '| ' + ' | '.join(headers) + ' |'
            
            # 更新分隔行
            if len(table_lines) > 1 and '---' in table_lines[1]:
                sep_line = table_lines[1].strip('| ')
                sep_cells = [s.strip() for s in sep_line.split('|')]
                sep_cells.append("---")  # 新增列分隔符
                table_lines[1] = '| ' + ' | '.join(sep_cells) + ' |'
            elif len(table_lines) > 1:
                # 添加分隔行（如果不存在）
                sep_line = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
                table_lines.insert(1, sep_line)
        
        # 确定数据行范围
        data_start = 1
        if len(table_lines) > 1 and any('---' in line for line in table_lines[1:2]):
            data_start = 2
        data_rows = len(table_lines) - data_start
        
        # 准备新值（处理长度问题）
        if new_values is None:
            new_values = []
        
        values_to_assign = new_values[:]  # 复制列表
        if len(values_to_assign) < data_rows:
            values_to_assign += [default_value] * (data_rows - len(values_to_assign))
        elif len(values_to_assign) > data_rows:
            values_to_assign = values_to_assign[:data_rows]
        
        # 更新/新增列数据
        for i in range(data_start, len(table_lines)):
            # 解析当前行
            row_line = table_lines[i].strip('| ')
            cells = [c.strip() for c in row_line.split('|')]
            
            # 确保单元格数量与列数一致
            if len(cells) < len(headers):
                cells += [default_value] * (len(headers) - len(cells))
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]
            
            # 更新或添加单元格值
            if col_index < len(cells):
                cells[col_index] = str(values_to_assign[i - data_start])
            else:
                cells.append(str(values_to_assign[i - data_start]))
            
            # 重新构建行
            table_lines[i] = '| ' + ' | '.join(cells) + ' |'
    
    # 7. 替换原始表格内容
    updated_lines = lines.copy()
    for idx, table_idx in enumerate(table_row_indices):
        if idx < len(table_lines):
            updated_lines[table_idx] = table_lines[idx]
        else:
            # 处理新增行情况（如果行数增加了）
            updated_lines[table_idx] = table_lines[-1]
    
    # 处理行数增加的情况
    if len(table_lines) > len(table_row_indices):
        # 找到表格结束位置
        last_table_line = table_row_indices[-1]
        
        # 在原始表格位置之后插入新增的行
        for i in range(len(table_row_indices), len(table_lines)):
            updated_lines.insert(last_table_line + (i - len(table_row_indices)) + 1, table_lines[i])
    
    return "\n".join(updated_lines)

def duplicate_rows_based_on_column(markdown_text: str, column_name: str, duplication_rules: dict) -> str:
    """
    根据指定列的取值复制表格行
    
    :param markdown_text: 包含Markdown表格的字符串
    :param column_name: 用于确定复制次数的列名
    :param duplication_rules: 复制规则字典 {列值: 复制次数}
    :return: 更新后的Markdown文本
    """
    lines = markdown_text.splitlines()
    table_row_indices = []
    in_table = False
    
    # 1. 定位表格范围
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if in_table:
                break  # 遇到空行结束表格
            continue
            
        if '|' in stripped:
            if not in_table:
                in_table = True
            table_row_indices.append(i)
        elif in_table:
            break  # 遇到非表格行结束表格
    
    if not table_row_indices:
        return markdown_text  # 没有找到表格
    
    # 2. 提取表格内容
    table_lines = [lines[i] for i in table_row_indices]
    
    # 3. 解析表头
    header_line = table_lines[0].strip().strip('|')
    headers = [h.strip() for h in header_line.split('|')]
    
    try:
        col_index = headers.index(column_name.strip())
    except ValueError:
        return markdown_text  # 列名不存在
    
    # 4. 确定数据行范围
    data_start = 1  # 跳过表头行
    # 检查是否有分隔行
    if len(table_lines) > 1 and any('---' in cell or '--' in cell for cell in table_lines[1].split('|')):
        data_start = 2  # 如果有分隔行，数据从第2行开始
    
    # 5. 处理行复制
    new_table_lines = table_lines[:data_start]  # 保留表头行和分隔行
    for i in range(data_start, len(table_lines)):
        # 解析当前行
        row_line = table_lines[i].strip().strip('|')
        cells = [c.strip() for c in row_line.split('|')]
        
        # 确保单元格数量与列数一致
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        elif len(cells) > len(headers):
            cells = cells[:len(headers)]
        
        # 获取当前行指定列的值
        cell_value = cells[col_index]
        
        # 确定复制次数
        duplicate_count = duplication_rules.get(cell_value, 1)
        
        # 复制行
        for _ in range(duplicate_count):
            # 重新构建行（保持原始格式）
            new_line = "| " + " | ".join(cells) + " |"
            new_table_lines.append(new_line)
    
    # 6. 替换原始表格内容
    updated_lines = lines.copy()
    for idx, table_idx in enumerate(table_row_indices):
        if idx < len(new_table_lines):
            updated_lines[table_idx] = new_table_lines[idx]
        else:
            # 如果新表格行数增加，插入新行
            updated_lines.insert(table_idx + idx, new_table_lines[idx])
    
    # 处理行数增加的情况
    if len(new_table_lines) > len(table_row_indices):
        # 计算原始表格的结束位置
        last_table_line = table_row_indices[-1]
        # 插入新增的行
        for i in range(len(table_row_indices), len(new_table_lines)):
            updated_lines.insert(last_table_line + i - len(table_row_indices) + 1, new_table_lines[i])
    
    return "\n".join(updated_lines)

def concatenate_lists(*lists):
    """
    将多个列表中相同下标的字符串元素拼接成一个新列表
    
    参数:
        *lists: 多个长度相同的字符串列表
        
    返回:
        新列表，每个元素是输入列表中相同位置字符串的拼接结果
    """
    # 使用zip组合所有列表中相同位置的元素，然后拼接字符串
    return [''.join(items) for items in zip(*lists)]


def extract_transformation_tables(llm_output_md, src_flag:bool = False):
    tables = extract_markdown_tables(llm_output_md)
    business_model_rate_data, business_model_data = get_business_model_data()
    split_signal = ','
    if src_flag:
        new_need_update_columns = need_update_columns_src
    else:
        new_need_update_columns = need_update_columns
    for i, table in enumerate(tables, 1):
        logger.info(f"大模型提取得到的表格{i}：\n{table}\n")
        updated_table = table
        if src_flag:
            # updated_table = new_modify_markdown_table(updated_table, columns_to_delete=["入口光层业务", "出口光层业务"])
            # updated_table = new_modify_markdown_table(updated_table, duplicate_rows=True)
            dst_df = process_dataframe(updated_table, business_model_data)
            updated_table = dst_df.to_markdown(index=False)
            updated_table = new_modify_markdown_table(updated_table, '变更分析', [''] * len(dst_df), add_new_column=True)
            logger.info(f"--------{updated_table}")
        else:
            new_need_update_columns = need_update_columns
            for need_update_column in new_need_update_columns:
                results = []
                error_infos = []
                aa_values = pub_get_column_values_from_markdown_table(table, need_update_column, network_business_model, need_update_columns)
                if need_update_column != network_business_model:
                    mysql_data = business_model_rate_data
                else:
                    mysql_data = business_model_data
                
                with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    all_results = executor.map(lambda aa_value: get_knowledge(aa_value.strip(), mysql_data, need_update_column, split_signal), aa_values)
                
                for (result, error_info) in all_results:
                    results.append(result)
                    error_infos.append(error_info)
              
                executor.shutdown()
                if len(error_infos) < 2:
                    error_infos = error_infos * len(results)
                updated_table = new_modify_markdown_table(updated_table, need_update_column, results)
        
            # updated_table = new_modify_markdown_table(updated_table, '变更分析', error_infos, add_new_column=True)
            updated_table = process_markdown_table(updated_table)
        logger.info(f"转换后的表格{i}：\n{updated_table}\n")
        return updated_table
    
def parse_markdown_table(table_str: str) -> pd.DataFrame:
    """
    将单个Markdown表格字符串解析为pandas DataFrame。
    """
    lines = table_str.strip().split('\n')
    if not lines:
        raise ValueError("表格字符串为空或格式不正确")
    
    if len(lines) < 2:
        raise ValueError("表格至少需要表头和分隔行")
    
    # 找到分隔行（通常是第二行，包含 - 和 : 的行）
    # 分隔行的特征：包含 |，且包含 - 或 : 字符
    filtered_lines = []
    for i, line in enumerate(lines):
        # 检查是否为分隔行（第二行通常是分隔行，且包含 - 或 :）
        is_separator = (i > 0 and 
                       '|' in line and 
                       ('-' in line or ':' in line) and
                       all(c in ' |:-' for c in line.strip()))
        
        if not is_separator:
            filtered_lines.append(line)
    
    # 重构表格字符串（不含分隔行）
    processed_table_str = '\n'.join(filtered_lines)
    
    # 使用pandas读取
    df = pd.read_csv(StringIO(processed_table_str), sep='|', header=0, index_col=False)
    
    # 去除首尾空列
    df = df.iloc[:, 1:-1] if len(df.columns) >= 2 else df
    
    # 去除列名和单元格中的首尾空格
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    return df

def process_single_table(df: pd.DataFrame) -> dict:
    """
    处理单个表格：按产品形态拆分，并对每个子表格进行站点名称替换。
    
    Args:
        df (pd.DataFrame): 原始表格的DataFrame。
        
    Returns:
        dict: 一个字典，键是产品形态，值是处理后的DataFrame。
              处理后的DataFrame中，'站点名称'列已被替换为'首站点'、'中间站点'、'尾站点'。
    """
    processed_tables = {}
    
    # 按'产品形态'列进行分组
    grouped = df.groupby('产品形态')
    
    for product_shape, group_df in grouped:
        if '--' in product_shape:
            continue
        # 重置索引以确保后续操作的连续性
        group_df = group_df.reset_index(drop=True)
        
        # 获取所有唯一的站点名称，保持其在原表格中首次出现的顺序
        unique_sites = group_df['站点名称'].drop_duplicates(keep='first').tolist()
        
        # 创建一个映射字典
        site_mapping = {}
        if unique_sites:
            first_site = unique_sites[0]
            
            middle_sites = unique_sites[1:-1] if len(unique_sites) > 2 else []
            
            site_mapping[first_site] = '首站点'
            if len(unique_sites) > 1:
                last_site = unique_sites[-1]
                site_mapping[last_site] = '尾站点'
            for site in middle_sites:
                site_mapping[site] = '中间站点'
        
        # 创建一个新的DataFrame副本以避免修改原始数据
        modified_df = group_df.copy()
        # 应用映射进行替换
        modified_df['站点名称'] = modified_df['站点名称'].map(site_mapping)
        
        processed_tables[product_shape] = modified_df
    
    return processed_tables

def merge_and_sort_tables(table_list: list) -> pd.DataFrame:
    """
    将多个具有相同列结构的DataFrame列表进行纵向合并，
    并根据'站点名称'列的特定值（首站点、中间站点、尾站点）进行排序。
    
    Args:
        table_list (list): 包含pandas DataFrame的列表。
        
    Returns:
        pd.DataFrame: 合并并排序后的DataFrame。
    """
    if not table_list:
        return pd.DataFrame()
    
    # 纵向合并所有表格
    combined_df = pd.concat(table_list, ignore_index=True)
    
    # 定义排序的优先级
    sort_order = {'首站点': 0, '中间站点': 1, '尾站点': 2}
    
    # 创建一个辅助列来表示排序优先级
    combined_df['sort_key'] = combined_df['站点名称'].map(sort_order)
    
    # 按照辅助列进行排序
    sorted_df = combined_df.sort_values(by='sort_key', kind='stable').reset_index(drop=True)
    
    # 删除辅助列
    sorted_df = sorted_df.drop(columns=['sort_key'])

    # --- 新增的去重步骤 ---
    # 去除所有列都完全相同的重复行，保留第一次出现的行
    deduplicated_df = sorted_df.drop_duplicates(keep='first').reset_index(drop=True)
    
    return deduplicated_df

def process_multiple_markdown_tables(tables_str_list: list, input_product_shape:str) -> pd.DataFrame:
    """
    处理多个Markdown表格字符串的主函数。
    
    Args:
        tables_str_list (list): 包含多个Markdown表格字符串的列表。
        
    Returns:
        dict: 一个字典，键是产品形态，值是最终合并排序后的DataFrame。
    """
    all_processed_tables = {} # 用于收集所有表格中按产品形态分组的数据

    # 1. 解析、拆分和处理每个输入表格
    for i, table_str in enumerate(tables_str_list):
        logger.info(f"正在处理第 {i+1} 个输入表格...")
        try:
            logger.info(f"--------table_str:{table_str}")
            df = parse_markdown_table(table_str)
        except Exception as e:
            logger.info(f"解析第 {i+1} 个表格时出错: {e}")
            continue # 跳过当前表格，处理下一个

        # 处理当前表格，得到按产品形态拆分的字典
        processed_dfs = process_single_table(df)
        
        # 将当前表格的处理结果合并到总字典中
        for product_shape, processed_df in processed_dfs.items():
            if product_shape not in all_processed_tables:
                all_processed_tables[product_shape] = []
            all_processed_tables[product_shape].append(processed_df)
    
    # 2. 对每个产品形态的列表进行合并和排序
    final_results = pd.DataFrame()
    for product_shape, df_list in all_processed_tables.items():
        if input_product_shape not in product_shape:
            continue
        else:
            logger.info(f"正在合并和排序产品形态 '{product_shape}' 的表格...")
            final_df = merge_and_sort_tables(df_list)
            return final_df 
        # final_results[product_shape] = final_df
        
    return final_results


def aggregate_table_by_site(df: pd.DataFrame) -> pd.DataFrame:
    """
    对一个DataFrame进行聚合处理，将“站点名称”相同的行合并为一行。
    - “站点名称”和“产品形态”列保留。
    - 其他非“站点名称”和非“产品形态”的列，其值去重后用'/'连接。

    Args:
        df (pd.DataFrame): 输入的DataFrame，必须包含“站点名称”和“产品形态”列。

    Returns:
        pd.DataFrame: 聚合处理后的DataFrame，每个“站点名称”只有一行。
    """
    if df.empty:
        return df

    # 定义要分组的列
    groupby_cols = ['站点名称', '产品形态']
    
    # 确保输入表包含必要的列
    for col in groupby_cols:
        if col not in df.columns:
            raise ValueError(f"输入的DataFrame必须包含 '{col}' 列。")

    # 获取需要聚合的其他列
    agg_cols = [col for col in df.columns if col not in groupby_cols]
    
    if not agg_cols:
        # 如果没有其他列需要聚合，直接按站点名称和产品形态去重即可
        return df.drop_duplicates(subset=groupby_cols).reset_index(drop=True)

    # 定义聚合函数：对每个组内的值进行去重并连接
    def join_unique(series):
        # 去除空值和空字符串，然后去重，最后用'/'连接
        unique_vals = series.dropna().astype(str).str.strip().unique()
        # 过滤掉空字符串
        unique_vals = [val for val in unique_vals if val != '']
        return '/'.join(unique_vals)

    # 执行聚合操作
    # as_index=False 确保分组列成为结果DataFrame的普通列
    aggregated_df = df.groupby(groupby_cols, as_index=False).agg(join_unique)
    
    return aggregated_df

def aggregate_and_reorder_table(df: pd.DataFrame, business_model_rate_data:list) -> pd.DataFrame:
    """
    对一个DataFrame进行聚合处理，将相同站点名称的行合并，并按原始站点顺序排序。

    Args:
        df (pd.DataFrame): 输入的DataFrame，必须包含'站点名称'和'产品形态'列。

    Returns:
        pd.DataFrame: 聚合并排序后的DataFrame。
    """
    if df.empty:
        return df

    # 1. 保存原始站点名称的唯一顺序
    # drop_duplicates 保持首次出现的顺序，reset_index 保留原始顺序信息
    original_order_df = df[['站点名称']].drop_duplicates(keep='first').reset_index(drop=True)
    
    # 2. 确定需要聚合的列（非站点名称、非产品形态）
    groupby_cols = ['站点名称', '产品形态']
    agg_cols = [col for col in df.columns if col not in groupby_cols]
    
    # 3. 定义聚合函数
    def join_unique(series):
        # 去除空值（NaN或None或空字符串），去重，然后用'/'拼接
        unique_vals = series.dropna().astype(str).unique()
        unique_vals = [val for val in unique_vals if val.strip()] # 进一步过滤掉纯空格字符串
        return '/'.join(unique_vals)

    agg_dict = {col: join_unique for col in agg_cols}
    
    # 4. 按站点名称和产品形态分组并聚合
    aggregated_df = df.groupby(groupby_cols, sort=False, as_index=False).agg(agg_dict)
    
    # 5. 按照原始顺序重新排序
    
    # Let's create a mapping of site to its first appearance index in the original df.
    original_site_indices = {}
    for idx, site in df['站点名称'].items():
        if site not in original_site_indices:
            original_site_indices[site] = idx
    
    # Add a temporary column for sorting
    aggregated_df['temp_sort_key'] = aggregated_df['站点名称'].map(original_site_indices)
    
    # Sort by the temporary key
    aggregated_df = aggregated_df.sort_values(by='temp_sort_key', kind='stable').reset_index(drop=True)
    
    # Drop the temporary key
    aggregated_df = aggregated_df.drop(columns=['temp_sort_key'])
    result_df = transform_and_process_table(aggregated_df, business_model_rate_data)

    return result_df


def get_business_model_rate(value: str, business_model_rate_data:list) -> str:
    """
    此处仅为示例，您需要根据实际需求替换其内容。
    例如，可以是将字符串转为大写、添加前缀、进行某种编码等。
    """
    # 示例：将输入字符串转为大写
    # 请替换为您的实际处理逻辑
    result = []
    parts = str(value).split('/')
    for part in parts:
        for business_model_rate in business_model_rate_data:
            if part in business_model_rate["business_type_list"].split(','):
                if part.upper() in ["OTU4", "OTUC2", "OTUC4",  "OTUC8",  "OTUC12", "OTUC16"] and (business_model_rate["network_element_business_model_rate"] + '彩光') not in result:
                    result.append(business_model_rate["network_element_business_model_rate"] + '彩光')
                elif (business_model_rate["network_element_business_model_rate"] + '灰光') not in result:
                    result.append(business_model_rate["network_element_business_model_rate"] + '灰光')
    return '/'.join(result)

def transform_and_process_table(df: pd.DataFrame, business_model_rate_data: list) -> pd.DataFrame:
    """
    对一个包含特定列的DataFrame进行列删除、重排序、重命名和内容处理。

    Args:
        df (pd.DataFrame): 输入的DataFrame，必须包含'站点名称', '产品形态', 'C', 'D', 'E', 'F', 'G'列。

    Returns:
        pd.DataFrame: 经过变换和处理后的DataFrame。
    """
    if df.empty:
        return df

    # 1. 处理 C 列的内容
    # 定义一个内部函数来处理单个单元格
    def process_c_cell(cell_value, business_model_rate_data):
        if pd.isna(cell_value) or cell_value == '':
            return cell_value  # 保持空值不变
        # 对每个部分应用 get_business_model_rate
        processed_parts = get_business_model_rate(cell_value, business_model_rate_data) 
        # 用 '/' 重新连接
        return processed_parts

    # 创建一个新的DataFrame副本以避免修改原始数据
    df_modified = df.copy()
    df_renamed = df_modified.rename(columns={'入口业务类型': '入口光层业务', '出口业务类型': '出口光层业务'})
    
    # 应用处理函数到 C 列
    df_renamed['入口光层业务'] = df_renamed['入口光层业务'].apply(lambda x: process_c_cell(x, business_model_rate_data=business_model_rate_data))
    df_renamed['出口光层业务'] = df_renamed['出口光层业务'].apply(lambda x: process_c_cell(x, business_model_rate_data=business_model_rate_data))

    # 3. 调整列顺序为 站点名称, 产品形态, C1, D, G1
    final_column_order = ['站点名称', '产品形态', '入口光层业务','网元业务模型',  '出口光层业务']
    df_final = df_renamed[final_column_order]

    return df_final


def extract_atom_network(markdown_text: str):
    return svc_atom_network_split(markdown_text)


def extract_atom_net_essential_expression(markdown_text: str, hd_req:str, mid_flag: bool):
    return svc_atom_net_essential_expression(markdown_text, hd_req, mid_flag)


def extract_recommend_board_hd_svc_deployment(
    product_name: str,
    hd_req: str,
    factor_md_all: str,
    slices_all: str,
    hd_table: Union[str, List[str]],
    data_type: str,
    dependent_data: str = ''
):
    return recommend_board_hd_svc_deployment(product_name, hd_req, factor_md_all, slices_all, hd_table, data_type, dependent_data)

def extract_auto_network_slice_recommendation(atom_network: str, markdown_text:str):
    return auto_network_slice_recommendation(atom_network, markdown_text)


def extract_src_req_sum(markdown_text_list: list, product_name:str):
    # product_name = '19700产品'
    final_df = process_multiple_markdown_tables(markdown_text_list, product_name)
    src_table_md = final_df.to_markdown(index=False)
    return src_table_md

def extract_network_element_business_model_sum(markdown_text: str):
    data_type = "business_model_rate"
    business_model_rate_data, business_model_data = get_business_model_data(data_type)
    df = parse_markdown_table(markdown_text)
    final_table_md = aggregate_and_reorder_table(df, business_model_rate_data).to_markdown(index=False)
    return final_table_md

def extract_board_change_analysis(markdown_text: str):
    board_list = clean_list(pub_get_column_values_from_markdown_table(markdown_text, '单板名称'))
    logger.info(f"--------board_list:{board_list}")
    if not board_list or pd.isna(board_list[0]):
        return '没有新增单板，返回为空'
    params = {"board": ','.join(board_list)}
    resps = querySrcBoardChangeAnalysisByParams(params, markdown_flag=True)
    columns = []
    if resps:
        columns = list(resps[0].keys())
    columns = [column for column in columns if column not in ['id', 'status','create_time', 'update_time', 'operator_person', 'effective_flag']]
    replace_dict = {"board":"单板标识"}
    return pub_dict_list_to_markdown_table_reordered(resps, columns, replace_dict)

def clean_list(lst):
    """
    使用 pandas 的 isna() 方法清理
    """
    series = pd.Series(lst)
    # 去除 None, NaN, NaT 等缺失值
    filtered_series = series.dropna()
    # 再去除空字符串
    result = [item for item in filtered_series if item != '']
    return result

def extract_get_board_all_feature_rdc_status(product_name: str, query_mode: str, board_names):
    return get_board_all_feature_rdc_status(product_name, query_mode, board_names)

def extract_get_board_slice_feature_rdc_status(product_name: str, query_mode, board_names, hd_slices):
    return get_board_slice_feature_rdc_status(product_name, query_mode, board_names, hd_slices)

def extract_get_board_key_changed_feature(product_name: str, query_mode:str, board_names):
    return get_board_key_changed_feature(product_name, query_mode, board_names)
    
def extract_query_change_mode_and_affected_features(change_mode: str):
    return get_board_change_mode_and_affected_features(change_mode)

def call_xingxiaomi_agent(question:str, agent_id:str='e831fc12-c179-4c84-87a7-05adf0125233'):
    return call_agent(question, agent_id)


def call_agent(message: str, agent_id:str='e831fc12-c179-4c84-87a7-05adf0125233'):
    result = dict()
    payload: Dict[str, Any] = {
        "message": message,
        "user_name": "10302076",
        "icenter_token": "",
        "agent_id": agent_id,
        "stream": False,
        "result_only": True
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=1800)
        if response.status_code != 200:
            raise RuntimeError(f"请求失败，状态码：{response.status_code}")
        result = response.json()

    except Exception as e:
        raise RuntimeError(f"请求异常: {str(e)}")
    return result


def process_board_related_element_factor(input_str: str) -> str:
    """
    处理波及要素因子查询

    根据输入的单板信息（板卡类型 + 交叉类型），通过三步查询流程，
    最终输出单板名称、要素、因子和因子取值的关联关系表格。

    Args:
        input_str: Markdown 表格字符串，包含单板名称、板卡类型、交叉类型三列
        logger: 日志记录器对象

    Returns:
        Markdown 表格字符串，包含单板名称、要素、因子、因子取值四列
    """
    
    logger.info(f"-------{datetime.now()}:开始处理波及要素因子")
    # 步骤 0: 解析 Markdown 表格为字典列表
    df = parse_markdown_table(input_str)
    board_rows = df.to_dict('records')
    logger.info(f"-------解析后的单板数据：{board_rows}")
    output_rows = []

    # 遍历每个单板
    for row in board_rows:
        board_name = row.get('单板名称', '').strip()
        board_business_type = row.get('板卡类型', '').strip()
        cross_type = row.get('交叉类型', '').strip()

        logger.info(f"-------处理单板：{board_name}, 板卡类型：{board_business_type}, 交叉类型：{cross_type}")

        # 步骤 1: 查询单板原子模型
        query_params_step1 = {
            'boardBusinessType': board_business_type,
            'crossType': cross_type
        }
        step1_results = querySrcBoardBusinessAtomByParams(query_params_step1, markdown_flag=True)
        board_model_list = [r['boardBusiness'] for r in step1_results if r.get('boardBusiness')]
        
        logger.info(f"-------步骤 1 查询结果 - 单板原子模型列表：{board_model_list}")

        if not board_model_list:
            logger.warning(f"-------单板 {board_name} 未找到匹配的原子模型，跳过")
            continue

        # 步骤 2: 查询关联特性
        featureFirstType = '高可用业务,扩展应用业务'
        boardBusinessModel = ','.join(board_model_list)
        step2_results = querySrcFeatureBoardRelation(boardBusinessModel, featureFirstType)
        
        logger.info(f"-------步骤 2 查询结果 - 关联特性：{step2_results}")
        if not step2_results:
            logger.warning(f"-------单板 {board_name} 未找到关联特性，跳过")
            continue

        # 按 feature_first_classification 分组
        feature_dict = {}
        for item in step2_results:
            first_class = item.get('featureFirstType', '')
            feature_name = item.get('feature', '')
            if first_class not in feature_dict:
                feature_dict[first_class] = []
            if feature_name and feature_name not in feature_dict[first_class]:
                feature_dict[first_class].append(feature_name)

        logger.info(f"-------按一级分类分组后的特性：{feature_dict}")
        # 步骤 3: 遍历每个特性一级分类，生成输出行
        for first_class, feature_name_list in feature_dict.items():
            # 3.1 构造 core_element
            core_element = first_class.replace('业务', '要素')
            logger.info(f"-------处理要素：{core_element}, 对应特性列表：{feature_name_list}")

            # 3.2 查询要素因子关系
            query_params_step3 = {'element': core_element}
            step3_results = querySrcCoreElementFactorRelationByParams(query_params_step3)
            logger.info(f"-------步骤 3 查询结果 - 要素因子关系：{step3_results}")

            if not step3_results:
                logger.warning(f"-------要素 {core_element} 未找到因子关系，跳过")
                continue

            # 3.3 Python 层面正则过滤 factor（仅针对"高可用要素"）
            factors = step3_results
            if core_element == '高可用要素':
                pattern = re.compile(cross_type + r'[\u4e00-\u9fa5]+')
                filtered_factors = [f for f in factors if pattern.match(f.get('factorType', ''))]
                logger.info(f"-------高可用要素正则过滤后的因子：{filtered_factors}")
            else:
                filtered_factors = factors
                logger.info(f"-------扩展应用要素不过滤，因子：{filtered_factors}")

            # 3.4 遍历每个 factor，进行因子取值匹配
            for factor_item in filtered_factors:
                factor = factor_item.get('factorType', '')
                factor_value = factor_item.get('factorValue', '')

                if not factor:
                    continue

                # 分割 factor_value
                factor_value_split_list = factor_value.split(',') if factor_value else []
                logger.info(f"-------因子 {factor} 的原始取值：{factor_value_split_list}")

                # 匹配：检查 factor_value_split 是否是任意 feature_name 的子串
                matched_values = []
                for fv_split in factor_value_split_list:
                    fv_split_stripped = fv_split.strip()
                    if not fv_split_stripped:
                        continue
                    for feature_name in feature_name_list:
                        if fv_split_stripped in feature_name:
                            matched_values.append(fv_split_stripped)
                            break

                # 拼接匹配值
                matched_str = ','.join(matched_values)
                logger.info(f"-------因子 {factor} 匹配后的取值：{matched_str}")

                # 生成输出一行
                output_rows.append({
                    '单板名称': board_name,
                    '要素': core_element,
                    '因子': factor,
                    '因子取值': matched_str
                })

    # 步骤 4: 将输出行转换为 Markdown 表格
    if output_rows:
        output_df = pd.DataFrame(output_rows)
        output_data = output_df.to_markdown(index=False)
    else:
        output_data = ""
    logger.info(f"-------{datetime.now()}:结束处理波及要素因子")
    return output_data


def dot_to_board_recommendation(
    dot_md_str: str,
    new_board_info: str = "",
    product_name: str = "19700产品",
    src_flag: bool = True,
    mid_flag: bool = False,
    data_type: str = "推荐单板基本信息"
) -> str:
    """
    dot_md原始需求表格到推荐单板基本信息的完整处理流水线

    处理流程：
    1. dot_md原始需求表格 → 原始需求汇总表
    2. 原始需求汇总表 → 网元业务模型部署汇总表
    3. 并行：原子网络要素化表达 + 原子网络拆分
    4. 网络切片推荐
    5. 推荐单板基本信息

    Args:
        dot_md_str: DOT 源码字符串转换成的md表格字符串
        new_board_info: 新增单板信息，支持 Markdown 表格字符串 (str) 或单板名称列表 (List[str])
        product_name: 产品名称，默认"19700 产品"
        src_flag: 是否生成原始需求表格标识，默认 True
        mid_flag: 是否输出中间产物标识，默认 False
        data_type: 数据类型，默认"推荐单板基本信息"

    Returns:
        推荐单板基本信息结果字符串

    Raises:
        Exception: 当任何步骤失败时抛出异常
    """

    try:
        # ========== 阶段 1: DOT 提取 ==========
        # logger.info(f"======= 步骤 1: 开始 DOT 源码提取 ======")
        # dot_md_str = extract_transformation_tables(dot_source, src_flag)
        logger.info(f"--------dot_md_str\n:{dot_md_str}")
        logger.info(f"======= 步骤 1 完成：原始需求表格长度={len(dot_md_str) if dot_md_str else 0}")

        # ========== 阶段 2: 原始需求汇总 ==========
        logger.info(f"======= 步骤 2: 开始原始需求汇总 ======")
        src_req_str = extract_src_req_sum([dot_md_str], product_name[:-2])
        logger.info(f"======= 步骤 2 完成：原始需求汇总表长度={len(src_req_str) if src_req_str else 0}")

        # ========== 阶段 3: 网元业务模型部署汇总 ==========
        logger.info(f"======= 步骤 3: 开始网元业务模型部署汇总 ======")
        sum_req_str = extract_network_element_business_model_sum(src_req_str)
        logger.info(f"======= 步骤 3 完成：网元业务模型部署汇总表长度={len(sum_req_str) if sum_req_str else 0}")

        # ========== 阶段 4: 并行执行 - 原子网络要素化表达 + 原子网络拆分 ==========
        logger.info(f"======= 步骤 4: 开始并行执行原子网络处理 ======")

        # 步骤 4a: 原子网络要素化表达
        # 参数映射：markdown_text=sum_req_str, hd_req=src_req_str, mid_flag=mid_flag
        atom_network_coreelement_str = extract_atom_net_essential_expression(
            markdown_text=sum_req_str,
            hd_req=src_req_str,
            mid_flag=mid_flag
        )
        logger.info(f"======= 步骤 4a 完成：原子网络要素化表达长度={len(atom_network_coreelement_str) if atom_network_coreelement_str else 0}")

        # 步骤 4b: 原子网络拆分
        atom_network_str = extract_atom_network(sum_req_str)
        logger.info(f"======= 步骤 4b 完成：原子网络拆分汇总长度={len(atom_network_str) if atom_network_str else 0}")

        # ========== 阶段 5: 网络切片推荐 ==========
        logger.info(f"======= 步骤 5: 开始网络切片推荐 ======")
        # 参数映射：atom_network=atom_network_str, markdown_text=atom_network_coreelement_str
        business_slice_str = extract_auto_network_slice_recommendation(
            atom_network=atom_network_str,
            markdown_text=atom_network_coreelement_str
        )
        logger.info(f"======= 步骤 5 完成：业务切片推荐长度={len(business_slice_str) if business_slice_str else 0}")

        # ========== 阶段 6: 推荐单板基本信息 ==========
        logger.info(f"======= 步骤 6: 开始推荐单板基本信息 ======")
        # 参数映射：
        # - product_name: 产品名称
        # - hd_req: src_req_str (原始需求汇总表)
        # - factor_md_all: atom_network_coreelement_str (原子网络要素化表达)
        # - slices_all: business_slice_str (业务切片推荐)
        # - hd_table: new_board_info (新增单板信息)，支持 str 或 List[str]
        # - data_type: 数据类型
        # - dependent_data: 依赖数据（可选，默认为空）
        results, _ = querySrcBoardTreeByParams()
        hd_table = [result["board"] for result in results if result["board"]]
        if new_board_info.strip():
            hd_table = new_board_info
        result = extract_recommend_board_hd_svc_deployment(
            product_name=product_name,
            hd_req=src_req_str,
            factor_md_all=atom_network_coreelement_str,
            slices_all=business_slice_str.replace('\n\n', '\n'),
            hd_table=hd_table,
            data_type=data_type,
            dependent_data=''
        )
        logger.info(f"======= 步骤 6 完成：推荐结果长度={len(result) if result else 0}")
        logger.info(f"======= 整个处理流水线执行完成 ======")
        return result
    except Exception as e:
        logger.error(f"======= 处理流水线执行失败：{str(e)}")
        raise
