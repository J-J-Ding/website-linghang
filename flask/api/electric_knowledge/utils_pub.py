import re
import json
import random
import string
import logging
import requests
import pandas as pd

from io import StringIO
from datetime import datetime, timedelta

from electric_knowledge.data_model import db, FIELDTEAMMEMBERS


logger = logging.getLogger("Logger")


def pub_remove_after_parentheses(text):
    """移除括号及括号后面的所有内容"""
    # 匹配第一个左括号及其后面的所有内容
    pattern = r'\([^)]*\).*'
    result = re.sub(pattern, '', text)
    return result


def pub_random_string():
    # 定义字符集：大写字母 + 小写字母 + 数字
    characters = string.ascii_letters + string.digits
    # 生成 10 位随机字符串
    pub_random_string = ''.join(random.choice(characters) for _ in range(10))
    return pub_random_string


def pub_get_column_values_from_markdown_table(table_md: str, column_name: str, network_business_model: str='', need_update_columns:list=[]):
    # pandas 读取 markdown 表格
    df = pd.read_csv(StringIO(table_md), sep='|', engine='python', skipinitialspace=True)
    # 去掉空白列名
    df = df.loc[:, ~(df.columns.str.strip() == '')]
    # 去掉首尾空格
    df.columns = df.columns.str.strip('_')
    df.columns = df.columns.str.strip()
    # 提取指定列
    if column_name in df.columns:
        if column_name != network_business_model:
            df[column_name] = df[column_name].str.strip()
            return df.loc[1:,column_name].tolist()
        else:
            return df.loc[1:,need_update_columns].apply(lambda row: ','.join(row.astype(str)), axis=1).tolist()
    else:
        logger.error(f"未找到列名: {column_name}，可用列: {df.columns.tolist()}")
        raise ValueError(f"未找到列名: {column_name}")


def pub_dict_list_to_markdown_table_reordered(dict_list:list, fields:list=['A', 'B', 'C', 'D', 'E'], replace_dict:dict={}):
    """
    将包含字典的列表转换为markdown表格, 并对列进行重排序
    将D列重命名为"123"并放在第1列, 其余列按字母顺序排序

    Args:
        dict_list: 包含字典的列表，每个字典应包含指定字段
        fields: 需要提取的原始字段列表，默认为['A', 'B', 'C', 'D', 'E']

    Returns:
        str: markdown格式的表格字符串
    """
    old_column = ''
    new_column = ''
    if replace_dict:
        old_column = list(replace_dict.keys())[0]
        new_column = replace_dict[old_column]
    if not dict_list:
        # 如果输入列表为空，返回空表格
        # 创建新的字段列表：123作为第1列，其余按字母排序
        new_fields = [f if f != old_column else new_column for f in fields]
        other_fields = sorted([f for f in new_fields if f != new_column])
        if new_column:
            final_fields = [new_column] + other_fields
        else:
            final_fields = other_fields
        header = "| " + " | ".join(final_fields) + " |"
        separator = "| " + " | ".join(['---'] * len(final_fields)) + " |"
        return header + "\n" + separator
    # 创建字段映射：新字段名 -> 原字段名
    new_to_original = {}
    for f in fields:
        if f == old_column:
            new_to_original[new_column] = old_column
        else:
            new_to_original[f] = f
    # 确定最终的字段顺序：123在前，其余按字母排序
    temp_fields = [f if f != old_column else new_column for f in fields]
    other_fields = sorted([f for f in temp_fields if f != new_column])
    if new_column:
        final_fields = [new_column] + other_fields
    else:
        final_fields = other_fields
    # 构建表头
    header = "| " + " | ".join(final_fields) + " |"
    # 构建分隔行
    separator = "| " + " | ".join(['---'] * len(final_fields)) + " |"
    # 构建数据行
    rows = []
    for item in dict_list:
        row_data = []
        for new_field in final_fields:
            # 根据新字段名找到原始字段名来获取数据
            original_field = new_to_original.get(new_field, new_field)
            value = item.get(original_field, '')
            # 转换为字符串并转义管道符
            str_value = str(value).replace('|', '\\|').replace('\n', '\\n') if value is not None else ''
            row_data.append(str_value)
        row = "| " + " | ".join(row_data) + " |"
        rows.append(row)
    # 组合所有部分
    markdown_table = header + "\n" + separator + "\n" + "\n".join(rows)
    return markdown_table


def pub_get_employ_name(employ_no):
    """
    根据工号查询员工姓名，若数据库中不存在，则调用外部接口获取并插入。
    返回格式："姓名工号"
    """
    # Step 1: 查询数据库
    result = db.session.query(FIELDTEAMMEMBERS.employee_name, FIELDTEAMMEMBERS.employee_number).filter(FIELDTEAMMEMBERS.employee_number == employ_no).first()
    if result:
        # 数据库存在，直接返回
        return f"{result.employee_name}{result.employee_number}"
    # Step 2: 数据库不存在，调用外部接口获取信息
    api_url = f"https://wxlteapi.zte.com.cn/zte-rd-lteact-basic/staff?workID={employ_no}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # 检查返回结构是否正常
        bo = data.get("bo")
        if not bo:
            logger.error(f"员工信息查询接口返回数据结构异常，缺少 'bo' 字段，工号: {employ_no}, 完整响应: {data}")
            raise ValueError("员工信息查询接口返回数据结构异常，缺少 'bo' 字段")
        emp_name = bo.get("empName")
        if not emp_name:
            logger.error(f"员工信息查询接口未返回员工中文名，工号: {employ_no}, 完整响应: {data}")
            raise ValueError(f"员工信息查询接口未返回员工中文名，工号: {employ_no}")
        # Step 3: 构造新记录并插入数据库
        new_employee = FIELDTEAMMEMBERS(
            employee_name=emp_name,
            employee_number=employ_no,
            department=bo.get("orgName", ""),
            district=bo.get("longWorkPlace", ""),
            description="",
            is_delete=0,
            human_resource=None,
            field_id=None,
            team_id=None
        )
        db.session.add(new_employee)
        db.session.commit()
        # Step 4: 返回拼接结果
        return f"{emp_name}{employ_no}"
    except Exception as e:
        logger.error(f"[ERROR] 获取员工信息失败，工号: {employ_no}, 错误: {e}")
        return f"未知"


def pub_generate_date_range(start_date, end_date):
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        logger.error(f"日期格式错误，应为 'YYYY-MM-DD' 格式: {e}")
        return []
    if start_dt > end_dt:
        logger.warning(f"开始日期({start_date})不能晚于结束日期({end_date})")
        return []
    date_list = []
    current_dt = start_dt
    while current_dt <= end_dt:
        date_list.append(current_dt.strftime("%Y-%m-%d"))
        current_dt += timedelta(days=1)
    return date_list


def pub_calculate_ratio(dividend, divisor, as_percentage=False, decimal_places=2):
    # 特殊规则：被除数为0 或 除数为0 时，直接返回0
    if not isinstance(dividend, (int, float)) or not isinstance(divisor, (int, float)):
        logger.warning("被除数和除数必须是数字类型（int 或 float）")
        result = 0.0 
    elif dividend == 0 or divisor == 0:
        result = 0.0
    else:
        result = dividend / divisor
    # 转换为百分比（可选）
    if as_percentage:
        result *= 100
    # 保留指定小数位
    return round(result, decimal_places)


def deduplicate_list_by_keys(dict_list, num=3,key_order=None, return_format='string'):
    """
    根据字典中前num个key对应的value组合进行去重

    参数:
        dict_list: 包含字典的列表
        key_order: 指定用于去重的key的顺序列表，如果为None则使用字典的前num个key
        return_format: 返回值格式，'dict'返回原字典，'string'返回拼接的字符串

    返回:
        去重后的列表（字典列表或字符串列表）
    """
    if not dict_list:
        return []
    seen = set()  # 用于存储已见过的value组合
    result = []   # 存储去重后的结果
    for item in dict_list:
        # 获取用于去重的key
        if key_order:
            keys_to_use = key_order[:num]  # 使用前num个指定的key
        else:
            # 使用字典的前num个key（按照插入顺序）
            keys_to_use = list(item.keys())[:num]
        # 提取前3个key对应的value，创建元组作为唯一标识
        values = [item.get(key, None) for key in keys_to_use]
        value_tuple = tuple(values)
        # 如果这个组合没见过，就添加到结果中
        if value_tuple not in seen:
            seen.add(value_tuple)
            # 根据return_format决定返回格式
            if return_format == 'string':
                # 将前3个value转换为字符串并拼接, 处理None值，转换为空字符串或"None"
                str_values = [str(v) if v is not None else '' for v in values]
                result.append(''.join(str_values))
            else:
                # 默认返回原字典
                result.append(item)
    return result