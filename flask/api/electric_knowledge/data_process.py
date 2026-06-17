import requests
import os
import pandas as pd
import csv


import re
import json

from pathlib import Path
import itertools
from datetime import datetime

import pymysql


class MySQLDataImporter:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            print(f"成功连接到数据库: {self.db_config['host']}/{self.db_config['database']}")
            return True
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("数据库连接已关闭")
    
    def import_data(self, data, table_name, batch_size=10, conflict_strategy='ignore'):
        """
        导入数据到MySQL表
        
        参数:
        data: List[Dict] - 要导入的数据
        table_name: str - 目标表名
        batch_size: int - 批处理大小
        conflict_strategy: str - 冲突处理策略 ('ignore', 'update')
        """
        if not data:
            print("数据为空，无需导入")
            return 0
        
        # 获取列名
        columns = list(data[0].keys())
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # 构建SQL语句
        if conflict_strategy == 'ignore':
            insert_sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        elif conflict_strategy == 'update':
            update_clause = ', '.join([f"{col} = VALUES({col})" for col in columns])
            insert_sql = f"""
                INSERT INTO {table_name} ({columns_str}) 
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_clause}
            """
        else:
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # 准备数据
        values = self.prepare_values(data, columns)
        
        total_rows = len(values)
        imported_rows = 0
        
        try:
            # 禁用索引（提高导入速度）
            self.cursor.execute(f"ALTER TABLE {table_name} DISABLE KEYS")
            
            # 分批导入
            for i in range(0, total_rows, batch_size):
                batch = values[i:i + batch_size]
                self.cursor.executemany(insert_sql, batch)
                self.connection.commit()
                
                batch_imported = len(batch)
                imported_rows += batch_imported
                print(f"批次 {i//batch_size + 1}: 导入 {batch_imported} 条, 总计 {imported_rows}/{total_rows}")
            
            print(f"成功导入 {imported_rows}/{total_rows} 条数据到表 {table_name}")
            
        except pymysql.Error as e:
            print(f"导入失败: {e}")
            self.connection.rollback()
            return 0
        finally:
            # 重新启用索引
            try:
                self.cursor.execute(f"ALTER TABLE {table_name} ENABLE KEYS")
            except:
                pass
            
        return imported_rows
    
    def prepare_values(self, data, columns):
        """准备数据值，处理特殊类型"""
        values = []
        for item in data:
            row = []
            for col in columns:
                value = item.get(col)
                
                # 处理特殊类型
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = None  # 保持None，PyMySQL会处理为NULL
                
                row.append(value)
            values.append(tuple(row))
        return values



def get_item_relation_table_data_dict(max_level, row, application_type, operator_person, effective_flag, item_relation_table_unique_key_list):
    item_relation_table_data_dict_list = []
    for col_index in list(range(max_level, 0, -1)):
        item_relation_table_data_dict = dict()
        if row[col_index] == '*' or pd.isna(row[col_index]):
            continue
        item_relation_table_unique_key = (str(row[col_index]) + '-' + str(col_index) + '-' + application_type)
        if item_relation_table_unique_key in item_relation_table_unique_key_list:
            continue
        else:
            item_relation_table_unique_key_list.append(item_relation_table_unique_key)
        item_relation_table_data_dict['unique_id'] = item_relation_table_unique_key
        item_relation_table_data_dict['item_name'] = row[col_index]
        item_relation_table_data_dict['parent_item_name'] = row[col_index - 1] if col_index > 1 else ''
        item_relation_table_data_dict['level'] = str(col_index)
        item_relation_table_data_dict['application_type'] = application_type
        item_relation_table_data_dict['create_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item_relation_table_data_dict['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item_relation_table_data_dict['operator_person'] = operator_person
        item_relation_table_data_dict['effective_flag'] = effective_flag
        # print(f"---------------item_relation_table_data_dict:\n{item_relation_table_data_dict}\n")
        item_relation_table_data_dict_list.append(item_relation_table_data_dict)
    return item_relation_table_data_dict_list, item_relation_table_unique_key_list

def get_item_business_relation_table_data_dict(max_level, row, application_type, operator_person, effective_flag, item_business_relation_table_unique_key_list, first_row, first_row_not_null_idx):
    item_business_relation_table_data_dict_list = []
    for col_index in list(range(max_level, 0, -1)):
        if row[col_index] == '*' or pd.isna(row[col_index]):
            continue
        for (not_null_idx, not_null_idx_num) in first_row_not_null_idx:
            item_business_relation_table_unique_key = (str(row[col_index]) + '-' + str(col_index) + '-' + application_type + '-' + str(first_row[not_null_idx]))
            if item_business_relation_table_unique_key in item_business_relation_table_unique_key_list:
                continue
            else:
                item_business_relation_table_unique_key_list.append(item_business_relation_table_unique_key)
            item_business_relation_table_data_dict = dict()
            item_business_relation_table_data_dict['unique_id'] = item_business_relation_table_unique_key
            item_business_relation_table_data_dict['item_name'] = row[col_index]
            item_business_relation_table_data_dict['level'] = str(col_index)
            item_business_relation_table_data_dict['business_scenario'] = first_row[not_null_idx]
            item_business_relation_table_data_dict['application_type'] = application_type
            item_business_relation_table_data_dict['related_flag'] = 'Y' if row[col_index + max_level * not_null_idx_num] == '√' else 'N'
            item_business_relation_table_data_dict['create_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item_business_relation_table_data_dict['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item_business_relation_table_data_dict['operator_person'] = operator_person
            item_business_relation_table_data_dict['effective_flag'] = effective_flag
            # print(f"---------------item_business_relation_table_data_dict:\n{item_business_relation_table_data_dict}\n")
            item_business_relation_table_data_dict_list.append(item_business_relation_table_data_dict)

        return item_business_relation_table_data_dict_list, item_business_relation_table_unique_key_list

def deal_input(input_data_path, output_data_path):
    input_folder = Path(input_data_path)
    for xlsx_file in input_folder.glob('*.xlsx'):
        print(f"-----------xlsx_file:\n{xlsx_file}")
        if '.~' in xlsx_file.stem:
            continue
        # print(f"-----------xlsx_file_name:\n{xlsx_file.stem}")
        file_name = xlsx_file.stem
        sheets = pd.ExcelFile(xlsx_file).sheet_names
        for sheet in sheets:
            df = pd.read_excel(xlsx_file, sheet_name=sheet)
            df.to_csv(f'{output_data_path}/{file_name}_{sheet}.csv', index=False, encoding='utf-8')

def del_output(output_data_path, application_type, operator_person, effective_flag):
    output_folder = Path(output_data_path)
    all_item_relation_table_unique_key_list = []
    all_item_relation_table_data_dict_list = []
    all_item_business_relation_table_unique_key_list = []
    all_item_business_relation_table_data_dict_list = []
    for csv_file in output_folder.glob('*.csv'):
        file_name = csv_file.stem
        print(f"-----------file_name:\n{file_name}")
        df = pd.read_csv(csv_file, header=None)
        # 获取第一行数据（Series）
        first_row = df.iloc[0]
        print(f"-----------first_row:\n{first_row}")

        # 判断每一列是否为空（True表示为空，False表示非空）
        is_null = first_row.isnull() | (first_row == '') | first_row.astype(str).str.contains('Unnamed')
        # print(f"-----------is_null:\n{is_null}")
        max_level = 0
        first_row_not_null_idx = []
        first_row_not_null_idx_num = 0
        # 找到第一个非空值的列索引（从0开始）
        for idx, val in enumerate(is_null):
            # print(f"-----------val:\n{val}")
            if not val:
                if max_level < 1:
                    print(f"第一个非空值在第{idx+1}列（从1开始计数）")
                    max_level = idx
                first_row_not_null_idx_num += 1
                first_row_not_null_idx.append((idx, first_row_not_null_idx_num))
                
        else:
            print("第一行全为空")
        if max_level < 1:
            continue
        
        for col_index in list(range(max_level - 1, -1, -1)):
            df.iloc[:, col_index] = df.iloc[:, col_index].ffill()
            print(f"--------------df.iloc[:, col_index]:\n{df.iloc[:, col_index]}\n")
        start_row = 2
        # 从第3行开始遍历（跳过第一行）
        for row in itertools.islice(df.itertuples(), start_row, None):
            print(f"-----------row:\n{row}")
            row_index = row.Index  # DataFrame的实际索引值（可能是非数字）
            # 按列序号获取值（跳过索引列）
            
            item_relation_table_data_dict_list, all_item_relation_table_unique_key_list = get_item_relation_table_data_dict(max_level, row, application_type, operator_person, effective_flag, all_item_relation_table_unique_key_list)
            all_item_relation_table_data_dict_list.extend(item_relation_table_data_dict_list)
            item_business_relation_table_data_dict_list, all_item_business_relation_table_unique_key_list = get_item_business_relation_table_data_dict(max_level, row, application_type, operator_person, effective_flag, all_item_business_relation_table_unique_key_list, first_row, first_row_not_null_idx)
            all_item_business_relation_table_data_dict_list.extend(item_business_relation_table_data_dict_list)
    return all_item_relation_table_data_dict_list, all_item_business_relation_table_data_dict_list



if __name__ == "__main__":
    from db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE, DB_PORT
        # 从环境变量获取数据库配置
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
    application_type = '特性'
    operator_person = '刘大伟10132282'
    effective_flag = 'Y'
    # 获取当前文件的绝对路径
    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_dir = os.path.dirname(current_file_path)
    input_data_path = current_dir + '/input_data'
    output_data_path = current_dir + '/output_data'
    
    deal_input(input_data_path, output_data_path)
    all_item_relation_table_data_dict_list, all_item_business_relation_table_data_dict_list = del_output(output_data_path, application_type, operator_person, effective_flag)
    
    # 创建导入器
    
    if importer.connect():
        # 导入数据
        imported_count = importer.import_data(
            data=all_item_relation_table_data_dict_list,
            table_name='item_relation_table',
            batch_size=10,
            conflict_strategy='update'
        )
        print(f"成功导入 {imported_count} 条记录")

        imported_count = importer.import_data(
            data=all_item_business_relation_table_data_dict_list,
            table_name='item_business_relation_table',
            batch_size=10,
            conflict_strategy='update'
        )
        print(f"成功导入 {imported_count} 条记录")
        
        # 关闭连接
        importer.disconnect()
    


