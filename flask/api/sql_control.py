import os
import sqlite3
import pandas as pd
from pathlib import Path
from tabulate import tabulate

def test_sql_control():
    """
    临时函数：在 ../data/feature.db 中创建新的 board_temperature_check 表
    """
    feature_db_path = '../data/feature.db'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(feature_db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(feature_db_path)
        cur = conn.cursor()
        print(f"✅ 已连接到数据库：{feature_db_path}")

        # 创建 board_temperature_checker 表
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS board_temperature_check (
            "单板名称" TEXT PRIMARY KEY,
            "是否带有IPMC" TEXT,
            "FRU中的温度检测点" TEXT,
            "FRU中的温度检测点id" TEXT,
            "FRU中的温度检测点定标温度" TEXT,
            "软件是否上报检测点温度参与风扇调速" TEXT,
            "软件上报温度是否有归一化处理" TEXT,
            "单板是否支持关键器件超温告警上报以及告警上报条件" TEXT,
            "备注" TEXT
        )
        '''
        
        cur.execute(create_table_sql)
        print("✅ 已创建表 board_temperature_checker")

        conn.commit()
        print("✅ 表创建操作完成")

    except sqlite3.Error as e:
        print(f"❌ 数据库操作出错: {e}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"❌ 发生未预期错误: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("🔗 数据库连接已关闭")

def clean_phy_data():
    """
    清理phy表中的数据，去除每个字段值的前后空格
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect('../data/feature.db')
        cur = conn.cursor()
        
        # 检查phy表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='phy';")
        table_exists = cur.fetchone()
        
        if not table_exists:
            print("phy 表不存在")
            return
            
        # 获取phy表的所有记录
        cur.execute('SELECT * FROM phy')
        rows = cur.fetchall()
        
        if not rows:
            print("phy表中没有数据")
            return
            
        # 获取列名
        column_names = [description[0] for description in cur.description]
        print(f"phy表列名: {column_names}")
        
        # 构建更新语句
        # 注意：我们不能直接更新主键列"PHY型号"，所以我们需要特殊的处理
        non_key_columns = [col for col in column_names if col != "PHY型号"]
        print(f"非主键列: {non_key_columns}")
        
        # 对于非主键列，我们可以直接更新
        if non_key_columns:
            set_clauses = []
            for col in non_key_columns:
                set_clauses.append(f'"{col}" = TRIM("{col}")')
            
            update_sql = f'UPDATE phy SET {", ".join(set_clauses)}'
            print(f"更新非主键列SQL: {update_sql}")
            
            cur.execute(update_sql)
            print(f"已更新 {cur.rowcount} 行非主键列的前后空格")
        
        # 对于主键列"PHY型号"，我们需要特殊的处理
        # 由于它是主键，我们不能直接UPDATE SET，需要重新创建表
        print("检查PHY型号列是否需要清理...")
        cur.execute('SELECT "PHY型号" FROM phy WHERE "PHY型号" != TRIM("PHY型号")')
        rows_needing_fix = cur.fetchall()
        
        if rows_needing_fix:
            print(f"发现 {len(rows_needing_fix)} 行PHY型号需要清理:")
            for i, row in enumerate(rows_needing_fix):
                original = row[0]
                trimmed = original.strip()
                print(f"  {i+1}. 原始: [{original}] -> 清理后: [{trimmed}]")
            
            # 由于PHY型号是主键，我们需要重建表
            print("由于PHY型号是主键，需要重建表来清理数据...")
            
            # 获取表结构
            cur.execute("PRAGMA table_info(phy)")
            columns_info = cur.fetchall()
            
            # 构建新的列定义（对所有列应用TRIM）
            new_columns_def = []
            column_names_list = []
            for col_info in columns_info:
                col_name = col_info[1]
                col_type = col_info[2]
                new_columns_def.append(f'TRIM("{col_name}") AS "{col_name}"')
                column_names_list.append(f'"{col_name}"')
            
            # 创建临时表
            columns_def_str = ", ".join(new_columns_def)
            column_names_str = ", ".join(column_names_list)
            
            create_temp_sql = f'''
                CREATE TABLE phy_temp AS 
                SELECT {columns_def_str} 
                FROM phy
            '''
            print(f"创建临时表SQL: {create_temp_sql}")
            
            cur.execute(create_temp_sql)
            print("已创建临时表并清理了所有数据")
            
            # 删除原表
            cur.execute("DROP TABLE phy")
            print("已删除原表")
            
            # 重新创建原表结构
            create_original_sql = '''
            CREATE TABLE phy (
                "PHY型号" TEXT PRIMARY KEY,
                "厂家" TEXT,
                "端口配置" TEXT,
                "端口类型" TEXT,
                "封装类型" TEXT,
                "速率支持" TEXT,
                "典型特性" TEXT,
                "支持单板" TEXT
            )
            '''
            cur.execute(create_original_sql)
            print("已重新创建原表结构")
            
            # 从临时表复制数据到原表
            copy_sql = f'''
                INSERT INTO phy ({column_names_str})
                SELECT {column_names_str}
                FROM phy_temp
            '''
            cur.execute(copy_sql)
            print(f"已从临时表复制 {cur.rowcount} 行数据到原表")
            
            # 删除临时表
            cur.execute("DROP TABLE phy_temp")
            print("已删除临时表")
        else:
            print("PHY型号列不需要清理")
            
        conn.commit()
        print("数据清理完成")
        
    except sqlite3.Error as e:
        print(f"数据清理时出错: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def clean_table_text_fields(db_path, table_name):
    """
    通用函数：清理指定数据库表中所有TEXT类型字段的数据，去除两边多余的空格
    
    参数:
        db_path (str): 数据库文件路径
        table_name (str): 要清理的表名
    
    返回:
        bool: 清理成功返回True，失败返回False
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 检查表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        table_exists = cur.fetchone()
        
        if not table_exists:
            print(f"表 '{table_name}' 不存在于数据库 '{db_path}' 中")
            return False
            
        print(f"开始清理表 '{table_name}' 中的TEXT类型字段...")
        
        # 获取表结构信息
        cur.execute("PRAGMA table_info(?)", (table_name,))
        columns_info = cur.fetchall()
        
        if not columns_info:
            print(f"无法获取表 '{table_name}' 的结构信息")
            return False
            
        # 筛选出TEXT类型的字段
        text_columns = []
        all_columns = []
        primary_keys = []
        
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2].upper()
            is_primary_key = col_info[5]  # 1表示主键，0表示非主键
            
            all_columns.append({'name': col_name, 'type': col_type, 'is_pk': is_primary_key})
            
            # 记录主键字段
            if is_primary_key:
                primary_keys.append(col_name)
            
            # 筛选TEXT类型的字段
            if 'TEXT' in col_type or 'VARCHAR' in col_type or col_type == '':
                text_columns.append(col_name)
        
        print(f"表 '{table_name}' 中的字段信息:")
        print(f"  所有字段: {[col['name'] for col in all_columns]}")
        print(f"  TEXT类型字段: {text_columns}")
        print(f"  主键字段: {primary_keys}")
        
        if not text_columns:
            print(f"表 '{table_name}' 中没有TEXT类型的字段需要清理")
            return True
            
        # 检查是否有需要清理的数据
        needs_cleaning = False
        for col_name in text_columns:
            cur.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" != TRIM("{col_name}")')
            count = cur.fetchone()[0]
            if count > 0:
                needs_cleaning = True
                print(f"字段 '{col_name}' 中有 {count} 条记录需要清理")
                
        if not needs_cleaning:
            print(f"表 '{table_name}' 中的所有TEXT字段都已经是干净的，无需清理")
            return True
            
        # 如果有主键字段，可以直接UPDATE清理
        if primary_keys:
            print(f"表 '{table_name}' 有主键字段，可以直接UPDATE清理...")
            
            # 构建UPDATE语句，对每个TEXT字段应用TRIM
            set_clauses = [f'"{col_name}" = TRIM("{col_name}")' for col_name in text_columns]
            where_conditions = [f'"{col_name}" != TRIM("{col_name}")' for col_name in text_columns]
            
            update_sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE {" OR ".join(where_conditions)}'
            print(f"执行UPDATE语句: {update_sql}")
            
            cur.execute(update_sql)
            updated_rows = cur.rowcount
            print(f"成功清理了 {updated_rows} 行数据")
            
        else:
            # 如果没有主键字段，需要重建表来清理数据
            print(f"表 '{table_name}' 没有主键字段，需要重建表来清理数据...")
            
            # 构建新的列定义（对所有TEXT列应用TRIM）
            new_columns_def = []
            column_names_list = []
            
            for col_info in all_columns:
                col_name = col_info['name']
                if col_name in text_columns:
                    new_columns_def.append(f'TRIM("{col_name}") AS "{col_name}"')
                else:
                    new_columns_def.append(f'"{col_name}"')
                column_names_list.append(f'"{col_name}"')
            
            # 创建临时表
            columns_def_str = ", ".join(new_columns_def)
            column_names_str = ", ".join(column_names_list)
            
            create_temp_sql = f'''
                CREATE TABLE "{table_name}_temp" AS 
                SELECT {columns_def_str} 
                FROM "{table_name}"
            '''
            print(f"创建临时表SQL: {create_temp_sql}")
            
            cur.execute(create_temp_sql)
            print("已创建临时表并清理了所有TEXT字段的数据")
            
            # 删除原表
            cur.execute(f'DROP TABLE "{table_name}"')
            print(f"已删除原表 '{table_name}'")
            
            # 重新创建原表结构
            column_definitions = []
            for col_info in all_columns:
                col_name = col_info['name']
                col_type = col_info['type']
                pk_suffix = " PRIMARY KEY" if col_info['is_pk'] else ""
                
                if col_type:
                    column_definitions.append(f'"{col_name}" {col_type}{pk_suffix}')
                else:
                    column_definitions.append(f'"{col_name}" TEXT{pk_suffix}')
            
            columns_str = ", ".join(column_definitions)
            create_original_sql = f'CREATE TABLE "{table_name}" ({columns_str})'
            
            print(f"重新创建原表SQL: {create_original_sql}")
            cur.execute(create_original_sql)
            print(f"已重新创建原表 '{table_name}' 结构")
            
            # 从临时表复制数据到原表
            copy_sql = f'''
                INSERT INTO "{table_name}" ({column_names_str})
                SELECT {column_names_str}
                FROM "{table_name}_temp"
            '''
            cur.execute(copy_sql)
            print(f"已从临时表复制 {cur.rowcount} 行数据到原表")
            
            # 删除临时表
            cur.execute(f'DROP TABLE "{table_name}_temp"')
            print("已删除临时表")
            
        conn.commit()
        print(f"✅ 表 '{table_name}' 中TEXT字段的空格清理完成")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 清理表 '{table_name}' 时出错: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ 清理过程中发生未知错误: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("数据库连接已关闭")



def copy_review_table_to_rdc_db(source_db_path='../data/feature.db', target_db_path='../data/sql_rdc.db'):
    """
    将feature.db数据库中的review表复制到sql_rdc.db数据库的review表中，包括字段和内容
    
    参数:
        source_db_path (str): 源数据库路径
        target_db_path (str): 目标数据库路径
    """
    source_conn = None
    target_conn = None
    
    try:
        # 连接源数据库
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()
        
        # 检查源数据库中是否存在review表
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='review'")
        if not source_cursor.fetchone():
            print(f"源数据库 {source_db_path} 中不存在 review 表")
            return False
            
        # 获取源表结构
        source_cursor.execute("PRAGMA table_info(review)")
        source_columns = source_cursor.fetchall()
        
        if not source_columns:
            print("源数据库中的 review 表没有字段信息")
            return False
            
        print(f"源表字段信息: {source_columns}")
        
        # 连接目标数据库
        target_conn = sqlite3.connect(target_db_path)
        target_cursor = target_conn.cursor()
        
        # 删除目标数据库中已存在的review表（如果存在）
        target_cursor.execute("DROP TABLE IF EXISTS review")
        print("已删除目标数据库中已存在的 review 表")
        
        # 根据源表结构创建目标表
        # 构建字段定义
        column_definitions = []
        for col in source_columns:
            col_name = col[1]
            col_type = col[2]
            not_null = " NOT NULL" if col[3] == 1 else ""
            default_value = f" DEFAULT {col[4]}" if col[4] is not None else ""
            primary_key = " PRIMARY KEY" if col[5] == 1 else ""
            
            # 特殊处理某些字段类型
            if col_type.upper() == "TEXT" or col_type.upper() == "VARCHAR":
                column_def = f'"{col_name}" TEXT{not_null}{default_value}{primary_key}'
            else:
                column_def = f'"{col_name}" {col_type}{not_null}{default_value}{primary_key}'
                
            column_definitions.append(column_def)
            
        columns_str = ", ".join(column_definitions)
        create_table_sql = f"CREATE TABLE review ({columns_str})"
        
        print(f"创建表SQL: {create_table_sql}")
        target_cursor.execute(create_table_sql)
        print("已在目标数据库中创建 review 表")
        
        # 从源表读取所有数据
        source_cursor.execute("SELECT * FROM review")
        rows = source_cursor.fetchall()
        
        if not rows:
            print("源表中没有数据")
            target_conn.commit()
            return True
            
        print(f"从源表读取到 {len(rows)} 条数据")
        
        # 获取字段名用于插入数据
        column_names = [col[1] for col in source_columns]
        column_names_str = "\", \"".join(column_names)
        formatted_column_names = f'"{column_names_str}"'
        placeholders = ", ".join(["?" for _ in column_names])
        insert_sql = f'INSERT INTO review ({formatted_column_names}) VALUES ({placeholders})'
        
        print(f"插入数据SQL: {insert_sql}")
        
        # 批量插入数据
        target_cursor.executemany(insert_sql, rows)
        print(f"已将 {len(rows)} 条数据插入到目标表中")
        
        # 提交事务
        target_conn.commit()
        print("数据复制完成")
        return True
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if target_conn:
            target_conn.rollback()
        return False
    except Exception as e:
        print(f"复制过程中发生错误: {e}")
        if target_conn:
            target_conn.rollback()
        return False
    finally:
        # 关闭数据库连接
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()


def fix_board_eeprom_column():
    """
    修改board表中的字段名：将"母版EEPROM"改为"母板EEPROM"
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect('../data/feature.db')
        cur = conn.cursor()
        
        try:
            cur.execute('ALTER TABLE board ADD COLUMN "母板EEPROM" TEXT')
            print("已添加新字段: 母板EEPROM")
        except sqlite3.Error as e:
            print(f"添加字段'母板EEPROM'时出错: {e}")
                
        conn.commit()
        print("字段名修改完成")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
    finally:
        # 确保连接无论是否出错都会关闭
        if 'conn' in locals() and conn:
            conn.close()


def remove_old_eeprom_column():
    """
    删除board表中的旧字段"母版EEPROM"
    通过重建表的方式来删除字段
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect('../data/feature.db')
        cur = conn.cursor()
        
        # 获取现有表结构
        cur.execute("PRAGMA table_info(board)")
        columns_info = cur.fetchall()
        
        # 构建新的字段列表（排除要删除的字段）
        new_columns = []
        column_names = []
        for col_info in columns_info:
            col_name = col_info[1]
            # 跳过要删除的字段
            if col_name != "母版EEPROM":
                new_columns.append(f'"{col_name}" {col_info[2]}')  # 字段名和类型
                column_names.append(f'"{col_name}"')
        
        # 如果没有找到要删除的字段，检查是否有特殊字符的字段需要处理
        if len(new_columns) == len(columns_info):
            print("未找到要删除的字段'母版EEPROM'")
            # 检查是否有含有特殊字符的字段需要修正
            special_columns = [col for col in columns_info if '/' in col[1]]
            if special_columns:
                print("发现含有特殊字符的字段，需要修正:")
                for col in special_columns:
                    print(f"  - {col[1]}")
            return
            
        # 创建新表的SQL语句
        new_columns_str = ", ".join(new_columns)
        new_table_sql = f'''
            CREATE TABLE board_new (
                {new_columns_str}
            )
        '''
        
        # 开始事务
        cur.execute("BEGIN TRANSACTION")
        
        # 创建新表
        cur.execute(new_table_sql)
        print("已创建新表board_new")
        
        # 复制数据
        column_names_str = ", ".join(column_names)
        copy_data_sql = f'''
            INSERT INTO board_new SELECT {column_names_str} FROM board
        '''
        cur.execute(copy_data_sql)
        print("已将数据复制到新表")
        
        # 删除原表
        cur.execute("DROP TABLE board")
        print("已删除原表")
        
        # 重命名新表
        cur.execute("ALTER TABLE board_new RENAME TO board")
        print("已将新表重命名为board")
        
        # 提交事务
        conn.commit()
        print("旧字段'母版EEPROM'已成功删除")
        
    except sqlite3.Error as e:
        # 回滚事务
        if 'conn' in locals():
            conn.rollback()
        print(f"删除字段时出错: {e}")
    finally:
        # 确保连接无论是否出错都会关闭
        if 'conn' in locals() and conn:
            conn.close()


def set_board_name_as_primary_key():
    """
    将board表中的board_name字段设置为主键
    通过重建表的方式来修改主键约束
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect('../data/feature.db')
        cur = conn.cursor()
        
        # 获取现有表结构
        cur.execute("PRAGMA table_info(board)")
        columns_info = cur.fetchall()
        
        # 构建新的字段列表，将board_name设置为主键
        new_columns = []
        column_names = []
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2]
            
            # 如果是board_name字段，设置为主键
            if col_name == "board_name":
                new_columns.append(f'"{col_name}" {col_type} PRIMARY KEY')
            else:
                new_columns.append(f'"{col_name}" {col_type}')
            
            column_names.append(f'"{col_name}"')
        
        # 创建新表的SQL语句
        new_columns_str = ", ".join(new_columns)
        new_table_sql = f'''
            CREATE TABLE board_new (
                {new_columns_str}
            )
        '''
        
        # 开始事务
        cur.execute("BEGIN TRANSACTION")
        
        # 创建新表
        cur.execute(new_table_sql)
        print("已创建新表board_new，board_name字段已设置为主键")
        
        # 复制数据
        column_names_str = ", ".join(column_names)
        copy_data_sql = f'''
            INSERT INTO board_new SELECT {column_names_str} FROM board
        '''
        cur.execute(copy_data_sql)
        print("已将数据复制到新表")
        
        # 删除原表
        cur.execute("DROP TABLE board")
        print("已删除原表")
        
        # 重命名新表
        cur.execute("ALTER TABLE board_new RENAME TO board")
        print("已将新表重命名为board")
        
        # 提交事务
        conn.commit()
        print("board_name字段已成功设置为主键")
        
    except sqlite3.Error as e:
        # 回滚事务
        if 'conn' in locals():
            conn.rollback()
        print(f"设置主键时出错: {e}")
    finally:
        # 确保连接无论是否出错都会关闭
        if 'conn' in locals() and conn:
            conn.close()


def rename_table_column(table_name, old_column_name, new_column_name, db_path='../data/feature.db'):
    """
    安全地将数据库表中的一个字段改名为另一个字段，同时保留原始数据
    
    参数:
        table_name (str): 表名
        old_column_name (str): 原字段名
        new_column_name (str): 新字段名
        db_path (str): 数据库路径
    
    注意: 这个操作会重建整个表，确保在执行前备份数据
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 获取现有表结构
        cur.execute(f"PRAGMA table_info({table_name})")
        columns_info = cur.fetchall()
        
        # 检查原字段是否存在
        old_column_exists = any(col[1] == old_column_name for col in columns_info)
        if not old_column_exists:
            print(f"字段 '{old_column_name}' 不存在于表 '{table_name}' 中")
            return False
            
        # 检查新字段是否已存在
        new_column_exists = any(col[1] == new_column_name for col in columns_info)
        if new_column_exists:
            print(f"字段 '{new_column_name}' 已存在于表 '{table_name}' 中")
            return False
        
        # 构建新的字段列表
        new_columns = []
        old_to_new_columns = {}  # 映射旧字段名到新字段名
        
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2]
            
            # 如果是需要重命名的字段
            if col_name == old_column_name:
                new_columns.append(f'"{new_column_name}" {col_type}')
                old_to_new_columns[f'"{col_name}"'] = f'"{new_column_name}"'
            else:
                new_columns.append(f'"{col_name}" {col_type}')
                old_to_new_columns[f'"{col_name}"'] = f'"{col_name}"'
        
        # 创建新表的SQL语句
        new_columns_str = ", ".join(new_columns)
        new_table_name = f"{table_name}_new"
        new_table_sql = f'''
            CREATE TABLE {new_table_name} (
                {new_columns_str}
            )
        '''
        
        # 开始事务
        cur.execute("BEGIN TRANSACTION")
        
        # 创建新表
        cur.execute(new_table_sql)
        print(f"已创建新表 {new_table_name}")
        
        # 构建字段映射字符串用于数据复制
        old_columns_str = ", ".join(old_to_new_columns.keys())
        new_columns_str = ", ".join(old_to_new_columns.values())
        
        # 复制数据
        copy_data_sql = f'''
            INSERT INTO {new_table_name} ({new_columns_str}) 
            SELECT {old_columns_str} FROM {table_name}
        '''
        cur.execute(copy_data_sql)
        print(f"已将数据从 {table_name} 复制到 {new_table_name}")
        
        # 删除原表
        cur.execute(f"DROP TABLE {table_name}")
        print(f"已删除原表 {table_name}")
        
        # 重命名新表
        cur.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")
        print(f"已将 {new_table_name} 重命名为 {table_name}")
        
        # 提交事务
        conn.commit()
        print(f"字段 '{old_column_name}' 已成功重命名为 '{new_column_name}'")
        return True
        
    except sqlite3.Error as e:
        # 回滚事务
        if 'conn' in locals():
            conn.rollback()
        print(f"重命名字段时出错: {e}")
        return False
    finally:
        # 确保连接无论是否出错都会关闭
        if 'conn' in locals() and conn:
            conn.close()

    
def create_bug_table(db_name='../data/feature.db'):
    # 连接到SQLite数据库（如果不存在则创建）
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 创建表结构的SQL语句，使用参数化方式避免中文在命令行的问题
    create_table_sql = '''
    CREATE TABLE "review" (
        "标识" TEXT PRIMARY KEY,
        "主题" TEXT,
        "描述" TEXT,
        "开发复盘负责人" TEXT,
        "缺陷等级" TEXT,
        "发现活动" TEXT,
        "发现方法" TEXT,
        "提交日期" TEXT,
        "关闭日期" TEXT,
        "故障引入人" TEXT,
        "引入点所属领域" TEXT,
        "引入点所属团队" TEXT,
        "技术根因分析" TEXT,
        "引入来源" TEXT,
        "故障引入点根因一级分类" TEXT,
        "故障引入点根因二级分类" TEXT,
        "故障引入点根因三级分类" TEXT,
        "故障引入gerrit入库链接" TEXT,
        "一级特性" TEXT,
        "二级特性" TEXT,
        "引入点复盘状态" TEXT,
        "最早可拦截阶段" TEXT,
        "自测无法拦截的原因" TEXT,
        "代码走查未拦截原因" TEXT,
        "代码走查未拦截原因说明" TEXT,
        "是否可通过补充代码UT/FT拦截" TEXT,
        "是否可通过补充仿真FT拦截" TEXT,
        "是否可通过补充硬件FT/流水线FT拦截" TEXT,
        "故障定界定位方式" TEXT,
        "是否需要复现定位或者占用环境定位" TEXT,
        "定位时长" TEXT,
        "控制点复盘状态" TEXT,
        "引入点改进举措" TEXT,
        "控制点改进举措" TEXT
    )
    '''
    
    try:
        # 执行创建表的SQL语句
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"表 'bug_table' 创建成功（或已存在）")
    except sqlite3.Error as e:
        print(f"创建表时出错: {e}")
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

def export_sqlite_to_excel(db_path, table_name, excel_path, sheet_name='Sheet1'):
    """
    ✅ 纯 pandas 实现：导出指定列到 Excel 的指定 Sheet，保留其他 Sheet
    ✅ 不使用 openpyxl.load_workbook，不操作 Workbook
    ✅ 自动处理文件损坏/非法格式 → 删除重建
    ✅ 100% pandas 接口
    """
    try:
        # 连接数据库 & 查询数据
        conn = sqlite3.connect(db_path)
        columns = ['ROWID', 'request_id', 'session_id', 'model', 'agent', 'timestamp', '"user"']
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # 如果目标文件存在，尝试用 pandas 读取所有 sheets（检测是否合法）
        original_sheets = {}
        file_is_valid = False

        if os.path.exists(excel_path):
            try:
                # 🧪 尝试读取所有 sheet 名称，验证文件是否合法
                with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
                    sheet_names = xls.sheet_names
                    # 读取其他 sheet 的数据（除了目标 sheet）
                    for name in sheet_names:
                        if name != sheet_name:
                            original_sheets[name] = pd.read_excel(xls, sheet_name=name)
                file_is_valid = True
            except Exception:
                # ❌ 文件损坏/非法 → 标记为无效，后续重建
                print(f"⚠️ 检测到文件 '{excel_path}' 损坏或格式非法，将重建...")
                file_is_valid = False

        # 📝 写入数据（覆盖目标 sheet，保留其他 sheet）
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
            # 1. 先写入目标 sheet（覆盖）
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # 2. 如果原文件合法，把其他 sheets 重新写回去
            if file_is_valid:
                for name, data in original_sheets.items():
                    data.to_excel(writer, sheet_name=name, index=False)

        print(f"✅ 成功导出到 '{excel_path}' 的 '{sheet_name}'，其他 Sheet 已保留")

    except sqlite3.Error as e:
        print(f"SQLite错误: {e}")
    except Exception as e:
        print(f"❌ 导出失败: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def excel_to_sqlite(excel_file_path, excel_sheet, db_file_path, db_table, column_mapping=None):
    """
    将 Excel 文件中的数据导入到 SQLite 数据库表中，基于主键进行覆盖（upsert）。
    仅处理 column_mapping 字典中指定的列。

    参数:
        excel_file_path (str): Excel 文件的路径。
        excel_sheet (str): 要读取的工作表名称。
        db_file_path (str): SQLite 数据库文件的路径。
        db_table (str): 目标数据库表名。
        column_mapping (dict, optional): 字典，键为 Excel 列名，值为数据库列名。例如 {'Excel列A': 'db_col_a', 'Excel列B': 'db_col_b'}。
    """
    # 1. 检查 Excel 文件是否存在
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"Excel 文件未找到: {excel_file_path}")

    # --- 关键修改：确定要处理的列 ---
    # 如果提供了有效的 column_mapping，则只处理这些列
    columns_to_read = None
    if column_mapping is not None and isinstance(column_mapping, dict):
        # 获取 column_mapping 中所有作为键的 Excel 列名
        requested_excel_columns = list(column_mapping.keys())
        print(f"准备读取 Excel 中指定的列: {requested_excel_columns}")
        columns_to_read = requested_excel_columns
    else:
        print("未提供有效的 column_mapping，将读取 Excel 中的所有列。")
        # columns_to_read 保持为 None，pandas 会读取所有列

    # 2. 读取 Excel 文件 (只读取需要的列)
    print(f"正在读取 Excel 文件: {excel_file_path}")
    try:
        df = pd.read_excel(excel_file_path, sheet_name=excel_sheet, usecols=columns_to_read)
        print(f"成功读取工作表 '{excel_sheet}'，共 {len(df)} 行数据。")
    except Exception as e:
        raise Exception(f"读取 Excel 文件时出错: {e}")

    # 3. 处理列名映射
    # 此时 df 的列名是 Excel 的原始列名
    if column_mapping is not None and isinstance(column_mapping, dict):
        # 检查读取到的列是否都在 mapping 的键中
        missing_cols = [col for col in df.columns if col not in column_mapping]
        if missing_cols:
            print(f"警告: 以下列已从 Excel 读取但不在 column_mapping 中，将被忽略: {missing_cols}")
        
        # 只保留存在于 column_mapping 键中的列，并进行重命名
        # 注意：usecols 已经限制了读取，这里主要是重命名和最终筛选
        cols_in_mapping = [col for col in df.columns if col in column_mapping]
        df_to_insert = df[cols_in_mapping].rename(columns=column_mapping)
        print(f"已应用列名映射，准备导入的列: {list(df_to_insert.columns)}")
    else:
        df_to_insert = df.copy()
        print("未应用列名映射，使用 Excel 原始列名。")

    # 4. 连接到 SQLite 数据库
    print(f"正在连接到数据库: {db_file_path}")
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
    except Exception as e:
        raise Exception(f"连接数据库时出错: {e}")

    # 5. 准备 SQL 语句
    # 获取最终要插入的列名 (数据库列名)
    columns = df_to_insert.columns.tolist()
    if not columns:
        raise ValueError("没有要插入的列。请检查 column_mapping 和 Excel 列名是否匹配。")

    columns_str = ', '.join(columns)
    placeholders = ', '.join(['?' for _ in columns])

    # 使用 INSERT OR REPLACE 语句
    # 假设表有主键或唯一约束，冲突时会替换整行
    sql = f"INSERT OR REPLACE INTO {db_table} ({columns_str}) VALUES ({placeholders})"

    print(f"使用 SQL: {sql}")

    # 6. 执行批量插入
    try:
        # 将 DataFrame 转换为元组列表
        data_tuples = [tuple(row) for row in df_to_insert.values]
        cursor.executemany(sql, data_tuples)
        conn.commit() # 提交事务
        print(f"数据已成功 '覆盖式' 导入到表 '{db_table}' 中 (共 {cursor.rowcount} 行受影响)。")
    except Exception as e:
        conn.rollback() # 出错时回滚
        cursor.close()
        conn.close()
        raise Exception(f"执行 INSERT OR REPLACE 时出错: {e}")

    # 7. 关闭连接
    cursor.close()
    conn.close()
    print("数据库连接已关闭。")

def update_feature_board_from_excel(excel_file_path, excel_sheet, db_file_path, 
                                   feature_name_col_excel='特性名称', 
                                   boards_col_excel='支持单板',
                                   delimiter=','):
    """
    从 Excel 文件读取特性对单板的支持情况，并同步更新 feature_board 关联表。

    参数:
        excel_file_path (str): Excel 文件路径。
        excel_sheet (str): 工作表名称。
        db_file_path (str): SQLite 数据库文件路径。
        feature_name_col_excel (str): Excel 中特性名称列的列名。默认 '特性名称'。
        boards_col_excel (str): Excel 中支持单板列的列名。默认 '支持单板'。
        delimiter (str): 单板之间的分隔符。默认为逗号 ','。
    """
    print(f"开始更新 feature_board 关联表...")
    print(f"Excel: {excel_file_path} | Sheet: {excel_sheet} | DB: {db_file_path}")

    # 1. 检查文件
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"❌ Excel 文件未找到: {excel_file_path}")

    # 2. 只读取需要的两列
    columns_to_read = [feature_name_col_excel, boards_col_excel]
    print(f"正在读取 Excel 中的列: {columns_to_read}")
    try:
        df = pd.read_excel(excel_file_path, sheet_name=excel_sheet, usecols=columns_to_read)
        print(f"✅ 成功读取 {len(df)} 行数据。")
    except Exception as e:
        raise Exception(f"❌ 读取 Excel 文件时出错: {e}")

    # 3. 数据清洗与验证
    # 去除列名前后的空格 (以防万一)
    df.columns = df.columns.str.strip()
    # 确保指定的列存在
    if feature_name_col_excel not in df.columns or boards_col_excel not in df.columns:
        raise ValueError(f"❌ Excel 中未找到指定的列: '{feature_name_col_excel}' 或 '{boards_col_excel}'")

    # 去除数据中的首尾空格
    df[feature_name_col_excel] = df[feature_name_col_excel].astype(str).str.strip()
    df[boards_col_excel] = df[boards_col_excel].astype(str).str.strip()

    # 处理空值
    # 对于 boards_col_excel，空值或 'nan' 视为空字符串
    df[boards_col_excel] = df[boards_col_excel].replace('nan', '').fillna('')

    # 4. 解析单板数据
    # a. 分割 'boards_col_excel' 列
    # 使用指定的分隔符分割，并去除每个单板名称的空格
    df['board_list'] = df[boards_col_excel].apply(
        lambda x: [board.strip() for board in x.split(delimiter) if board.strip()] if x else []
    )

    # b. 展开 (explode) 列表，生成每行一个 (feature_name, board_name) 的组合
    df_exploded = df.explode('board_list').rename(columns={'board_list': 'board_name'})
    
    # c. 过滤掉 board_name 为空的行 (来自原数据为空的情况)
    df_final = df_exploded.dropna(subset=['board_name'])
    df_final = df_final[df_final['board_name'] != '']
    
    # d. 重命名特性名称列为数据库中的列名
    df_final = df_final.rename(columns={feature_name_col_excel: 'feature_name'})
    
    # e. 只保留最终需要的两列
    df_final = df_final[['feature_name', 'board_name']].copy()
    
    # f. 去除重复的 (feature_name, board_name) 组合，确保符合数据库唯一性约束
    initial_count = len(df_final)
    df_final = df_final.drop_duplicates(subset=['feature_name', 'board_name'], keep='first')
    removed_count = initial_count - len(df_final)
    if removed_count > 0:
        print(f"🧹 已去除 {removed_count} 条重复的特性-单板关联记录。")

    print(f"🔍 解析完成，共生成 {len(df_final)} 条特性-单板关联记录。")

    # --- 数据库操作 ---
    print(f"🔗 正在连接数据库: {db_file_path}")
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
    except Exception as e:
        raise Exception(f"❌ 连接数据库时出错: {e}")

    # --- 使用事务确保数据一致性 ---
    try:
        conn.execute("BEGIN") # 开始事务

        # --- 步骤1: 获取本次 Excel 中包含的所有特性名称 ---
        # 这些特性在 feature_board 表中的旧记录将被删除
        feature_names_in_excel = df_final['feature_name'].unique().tolist()
        if not feature_names_in_excel:
            print("ℹ️  Excel 中未找到有效的特性-单板关联数据，无需更新。")
            conn.commit()
            return

        # --- 步骤2: 删除旧的关联记录 ---
        # 构建占位符 (?,?,?,...)
        placeholders = ','.join(['?' for _ in feature_names_in_excel])
        delete_sql = f"DELETE FROM feature_board WHERE feature_name IN ({placeholders})"
        cursor.execute(delete_sql, feature_names_in_excel)
        deleted_count = cursor.rowcount
        print(f"🗑️  已删除 {deleted_count} 条旧的关联记录 (属于本次更新的特性)。")

        # --- 步骤3: 插入新的关联记录 ---
        if not df_final.empty:
            insert_sql = "INSERT INTO feature_board (feature_name, board_name) VALUES (?, ?)"
            # 转换为元组列表
            new_records = [tuple(row) for row in df_final.values]
            cursor.executemany(insert_sql, new_records)
            inserted_count = cursor.rowcount
            print(f"✅ 已插入 {inserted_count} 条新的关联记录。")
        else:
            inserted_count = 0
            print("ℹ️  无新的关联记录需要插入。")

        # --- 提交事务 ---
        conn.commit()
        print(f"🎉 关联表 'feature_board' 更新成功！删除 {deleted_count} 条，新增 {inserted_count} 条。")

    except Exception as e:
        # --- 发生错误，回滚事务 ---
        conn.rollback()
        print(f"❌ 更新过程中发生错误，事务已回滚: {e}")
        raise # 重新抛出异常

    finally:
        # --- 关闭数据库连接 ---
        if 'conn' in locals():
            conn.close()
            print("🔌 数据库连接已关闭。")


def test_update_feature_board_from_excel():
    EXCEL_PATH = "../data/feature.xlsx"
    EXCEL_SHEET_NAME = "总表"
    DB_PATH = "../data/feature.db"

    try:
        update_feature_board_from_excel(
            excel_file_path=EXCEL_PATH,
            excel_sheet=EXCEL_SHEET_NAME,
            db_file_path=DB_PATH,
            feature_name_col_excel='特性名称',   # 根据你的 Excel 实际列名调整
            boards_col_excel='单板',         # 根据你的 Excel 实际列名调整
            delimiter=','                        # 根据你的分隔符调整
        )
        print("✅ feature_board 关联表更新流程完成。")
    except Exception as error:
        print(f"❌ 更新失败: {error}")   


def test_excel_to_sqlite_feature():
    # ✅ 方案一：使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    EXCEL_SHEET = "总表"
    DB_PATH = "../data/feature.db"
    DB_TABLE = "feature"

    MY_COLUMN_MAPPING = {
        '特性编号': 'feature_id',
        '特性名称': 'feature_name',
        '特性功能': 'feature_function',
        '特性等级': 'feature_level',
        '特性设计': 'feature_page',
        '领域': 'domain',
        '组件': 'component'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")

def test_excel_to_sqlite_board():
    # ✅ 方案一：使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "单板树"
    DB_TABLE = "board"

    MY_COLUMN_MAPPING = {
        '单板编号': 'board_id',
        '单板名称': 'board_name',
        '单板类型': '单板类型',
        '领域': 'domain',
        '产品': '产品',
        '子架': '子架',
        '主控': '主控',
        '子卡': '子卡',
        '交换芯片': '交换芯片',
        '面板端口': '面板端口',
        '转发能力': '转发能力',
        '软件平台': '软件平台',
        '交叉方式': '交叉方式',
        'PHY芯片': 'PHY芯片',
        '时钟芯片': '时钟芯片',
        '内存': '内存',
        'SDSSD': 'SDSSD',  # 已修正字段名，去除斜杠
        'FPGA': 'FPGA',
        'CPLD': 'CPLD',
        'FLASH': 'FLASH',
        '子架EEPROM': '子架EEPROM',
        '母板EEPROM': '母板EEPROM'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")

def test_excel_to_sqlite_module():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "光模块"
    DB_TABLE = "module"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        'PN': 'PN',
        '模块类型': '模块类型',
        '接口类型': '接口类型',
        '速率Mbps': '速率Mbps',
        '距离': '距离',
        '制造厂商': '制造厂商',
        '应用代码': '应用代码',
        '波长类型': '波长类型',
        '物料代码': '物料代码',
        '支持单板': '支持单板'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")


def test_excel_to_sqlite_sd():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "sd"
    DB_TABLE = "sd"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        'SD类型': 'SD类型',
        '厂家': '厂家',
        '容量': '容量',
        '材质': '材质',
        '接口类型': '接口类型',
        '代码': '代码',
        '支持主控': '支持主控',
        '总写入次数': '总写入次数',
        '单block大小': '单block大小',
        '理论TBW': '理论TBW',
        '每日写入上限': '每日写入上限'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")


def test_excel_to_sqlite_repo():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "代码库"
    DB_TABLE = "repo"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        '代码库': '代码库',
        '分支': '分支',
        '变更次数': '变更次数',
        '新增行': '新增行',
        '删除行': '删除行',
        '领域': '领域',
        '关联故障': '关联故障',
        '关联组件': '关联组件'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")


def test_excel_to_sqlite_api():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "命令库"
    DB_TABLE = "api"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        '命令类型': '命令类型',
        '命令码': '命令码',
        '命令名称': '命令名称',
        '命令来源': '命令来源',
        '关联特性': '关联特性',
        '关联命令': '关联命令',
        '关联组件': '关联组件',
        '数据存储': '数据存储',
        '处理流程': '处理流程',
        '白盒梳理': '白盒梳理'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 命令库数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")


def test_excel_to_sqlite_switch():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "交换芯片"
    DB_TABLE = "switch"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        '型号': '型号',
        '厂家': '厂家',
        '交换容量': '交换容量',
        '端口配置': '端口配置',
        '端口容量': '端口容量',
        '路由表容量': '路由表容量',
        '支持主控': '支持主控',
        '支持单板': '支持单板'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 交换机数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")

def test_excel_to_sqlite_component():
    # ✅ 使用相对路径 (保持原有结构)
    EXCEL_PATH = "../data/feature.xlsx"
    DB_PATH = "../data/feature.db"
    EXCEL_SHEET = "组件树"
    DB_TABLE = "component"

    # 定义Excel列名与数据库表字段的映射关系
    MY_COLUMN_MAPPING = {
        '组件编号': '组件编号',
        '组件名称': '组件名称',
        '组件类型': '组件类型',
        '组件描述': '组件描述',
        '代码目录': '代码目录',
        '代码规模': '代码规模',
        '代码服务器': '代码服务器',
        '智能体状态': '智能体状态',
        '领域': '领域',
        '团队': '团队',
        '守护人': '守护人'
    }

    try:
        # 调用函数，传入 column_mapping
        excel_to_sqlite(EXCEL_PATH, EXCEL_SHEET, DB_PATH, DB_TABLE, column_mapping=MY_COLUMN_MAPPING)
        print("✅ Excel 数据导入 SQLite 数据库完成！")
    except Exception as error:
        print(f"❌ 操作失败: {error}")


def test_set_board_name_primary_key():
    """
    测试函数：将board_name字段设置为主键
    """
    print("开始设置board_name为主键...")
    set_board_name_as_primary_key()
    print("设置完成！")


def test_copy_review_table():
    """
    测试函数：复制review表到sql_rdc.db
    """
    print("开始复制review表到sql_rdc.db...")
    success = copy_review_table_to_rdc_db()
    if success:
        print("✅ review表复制成功！")
    else:
        print("❌ review表复制失败！")



if __name__ == '__main__':
    
    # 如果需要修改字段名，取消下面这行的注释
    # fix_board_eeprom_column()

    # 如果需要设置board_name为主键，取消下面这行的注释
    # test_set_board_name_primary_key()

    # 替换为你的实际路径
    # database_path = Path(__file__).parent.parent / 'data' / 'chat.db'
    # table_to_export = "chat_list"      # 要导出的表名
    # output_excel = Path(__file__).parent.parent / 'data' / 'chat_list.xlsx'

    # export_sqlite_to_excel(database_path, table_to_export, output_excel)

    # test_excel_to_sqlite_feature()
    # test_excel_to_sqlite_board()
    # test_excel_to_sqlite_module()
    # test_update_feature_board_from_excel()
    # test_excel_to_sqlite_component()
    # create_bug_table()
    
    # 导入SD数据
    # test_excel_to_sqlite_sd()

    # 导入repo数据
    # test_excel_to_sqlite_repo()
    
    # 导入命令库数据
    # test_excel_to_sqlite_api()
    
    # 导入交换机数据
    # test_excel_to_sqlite_switch()
    
    # 复制review表
    # test_copy_review_table()
    

    # 清理PHY数据
    # clean_phy_data()

    # 临时操作数据库的函数
    test_sql_control()
