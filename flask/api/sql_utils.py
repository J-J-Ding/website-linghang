import os
import json
import dotenv
import sqlite3
import psycopg2
from typing import List, Dict, Optional

def Connect_to_postgresql():
    """
    连接到PostgreSQL数据库
    """
    try:
        # 加载环境变量
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        dotenv.load_dotenv(env_path)

        # 读取数据库配置
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取数据库连接参数
        db_config = config.get('db', {})
        host = db_config.get('host')
        port = db_config.get('port')
        main = db_config.get('main')
        user = db_config.get('user')
        
        # 获取数据库连接密码
        password = os.getenv('DB_PGSQL_PASSWORD')
        
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=main,
            user=user,
            password=password
        )
        return connection
    
    except psycopg2.Error as e:
        print(f"连接PostgreSQL数据库时出错: {e}")
        return None
    except FileNotFoundError as e:
        print(f"配置文件未找到: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        return None
    except Exception as e:
        print(f"连接数据库时发生未知错误: {e}")
        return None

def data_sync_sqlite_postgre(db_mapping, table_mapping, field_mapping):
    """
    从SQLite数据库同步数据到PostgreSQL数据库
    
    参数:
    - db_mapping (dict): 数据库映射表，格式为 {"sqlite_db_path": "postgresql_db_name"}
        例如: {"../data/feature.db": "linghang_db_main"}
    - table_mapping (dict): 表名映射，格式为 {"sqlite_table_name": "postgresql_table_name"}
        例如: {"users": "app_users", "orders": "app_orders"}
    - field_mapping (dict): 字段映射表，格式为 {"table_name": {"sqlite_field": "postgresql_field"}}
        例如: {
            "users": {
                "id": "user_id",
                "name": "full_name",
                "email": "email_address"
            }
        }
    """

    # 从db_mapping获取数据库连接信息
    sqlite_db_path = list(db_mapping.keys())[0] if db_mapping else None
    postgresql_db_path = list(db_mapping.values())[0] if db_mapping else None
    
    sqlite_conn = None
    pg_conn = None
    
    try:
        # 连接SQLite数据库
        if not sqlite_db_path:
            raise ValueError("数据库映射不能为空，需要提供SQLite数据库路径")
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # 连接PostgreSQL数据库 - 使用现有配置
        pg_conn = Connect_to_postgresql()
        if not pg_conn:
            raise Exception("无法连接到PostgreSQL数据库")
        pg_cursor = pg_conn.cursor()
        
        # 遍历表映射，同步每个表的数据
        for sqlite_table, pg_table in table_mapping.items():
            print(f"正在同步表: {sqlite_table} -> {pg_table}")
            
            # 检查SQLite表是否存在
            sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{sqlite_table}';")
            if not sqlite_cursor.fetchone():
                print(f"SQLite表 {sqlite_table} 不存在，跳过同步")
                continue
            
            # 获取SQLite表的字段信息
            sqlite_cursor.execute(f"PRAGMA table_info({sqlite_table})")
            sqlite_columns_info = sqlite_cursor.fetchall()
            sqlite_columns = [col[1] for col in sqlite_columns_info]  # 列名在索引1
            
            # 确定要同步的字段
            fields_to_sync = []
            pg_fields_to_sync = []
            
            if sqlite_table in field_mapping or pg_table in field_mapping:
                # 使用字段映射
                table_field_map = field_mapping.get(sqlite_table) or field_mapping.get(pg_table, {})
                for sqlite_field, pg_field in table_field_map.items():
                    if sqlite_field in sqlite_columns:
                        fields_to_sync.append(sqlite_field)
                        pg_fields_to_sync.append(pg_field)
                    else:
                        print(f"警告: SQLite表 {sqlite_table} 中不存在字段 {sqlite_field}，跳过该字段")
            else:
                # 没有字段映射，使用所有字段
                fields_to_sync = sqlite_columns
                pg_fields_to_sync = sqlite_columns  # 假设PostgreSQL表有相同字段名
            
            # 从SQLite读取数据
            fields_str = ', '.join([f'"{field}"' for field in fields_to_sync])
            sqlite_cursor.execute(f"SELECT {fields_str} FROM {sqlite_table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"表 {sqlite_table} 无数据，跳过同步")
                continue
            
            # 准备PostgreSQL插入语句的字段和占位符
            pg_fields_str = ', '.join([f'"{field}"' for field in pg_fields_to_sync])
            placeholders = ', '.join(['%s'] * len(pg_fields_to_sync))
            
            # 先删除PostgreSQL表中的现有数据
            if '.' in pg_table:
                schema_name, table_name = pg_table.split('.', 1)
                delete_sql = f'DELETE FROM "{schema_name}"."{table_name}"'
            else:
                delete_sql = f'DELETE FROM "{pg_table}"'
            
            print(f"正在清空PostgreSQL表 {pg_table} 中的现有数据...")
            pg_cursor.execute(delete_sql)
            
            # 准备PostgreSQL插入语句，支持schema.表名格式
            # 如果表名包含schema，则需要特殊处理
            if '.' in pg_table:
                schema_name, table_name = pg_table.split('.', 1)
                insert_sql = f'INSERT INTO "{schema_name}"."{table_name}" ({pg_fields_str}) VALUES ({placeholders})'
            else:
                insert_sql = f'INSERT INTO "{pg_table}" ({pg_fields_str}) VALUES ({placeholders})'
            
            # 执行插入操作，捕获外键约束错误并处理
            try:
                pg_cursor.executemany(insert_sql, rows)
            except psycopg2.Error as e:
                # 如果是外键约束错误，尝试过滤掉有问题的行
                if 'foreign key' in str(e).lower():
                    print(f"检测到外键约束错误，尝试过滤数据...")
                    # 过滤掉包含空值或无效外键的行
                    filtered_rows = []
                    for row in rows:
                        # 检查行中是否有空值在外键字段上
                        is_valid = True
                        for i, field in enumerate(pg_fields_to_sync):
                            # 如果字段是外键且值为空，则跳过该行
                            if field in ['团队'] and (row[i] is None or row[i] == ''):
                                is_valid = False
                                break
                        if is_valid:
                            filtered_rows.append(row)
                    
                    if filtered_rows:
                        print(f"过滤后剩余 {len(filtered_rows)} 行数据，重新插入...")
                        pg_cursor.executemany(insert_sql, filtered_rows)
                        print(f"成功插入 {len(filtered_rows)} 行数据")
                    else:
                        print("过滤后没有有效数据可插入")
                else:
                    # 如果不是外键错误，重新抛出异常
                    raise e
                # 提交事务
                pg_conn.commit()
            else:
                # 如果没有异常，正常提交
                pg_conn.commit()
            
            print(f"表 {sqlite_table} -> {pg_table} 同步完成，共 {len(rows)} 条记录")
        
        print("数据同步完成！")
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite数据库操作错误: {e}")
        if pg_conn:
            pg_conn.rollback()
        return False
    except psycopg2.Error as e:
        print(f"PostgreSQL数据库操作错误: {e}")
        if pg_conn:
            pg_conn.rollback()
        return False
    except Exception as e:
        print(f"数据同步过程中发生未知错误: {e}")
        if pg_conn:
            pg_conn.rollback()
        return False
    finally:
        # 关闭数据库连接
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_conn.close()


def sql_postgre_query(query_sql: str, params: Optional[List] = None) -> List[Dict]:
    """
    执行PostgreSQL查询并返回结果
    
    参数:
    - query_sql (str): 要执行的SQL查询语句
    - params (Optional[List]): 查询参数列表，默认为None
    
    返回:
    - List[Dict]: 查询结果，每个元素是一个包含行数据的字典
    """
    
    connection = None
    try:
        # 连接PostgreSQL数据库
        connection = Connect_to_postgresql()
        if not connection:
            print("无法连接到PostgreSQL数据库")
            return []
        
        cursor = connection.cursor()
        
        # 执行查询
        if params:
            cursor.execute(query_sql, params)
        else:
            cursor.execute(query_sql)
        
        # 获取列名
        description = cursor.description
        if description is None:
            # 如果没有结果，返回空列表
            return []
        
        columns = [desc[0] for desc in description]
        
        # 获取查询结果
        rows = cursor.fetchall()
        
        # 将结果转换为字典列表
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        
        return result
    
    except psycopg2.Error as e:
        print(f"PostgreSQL查询时出错: {e}")
        return []
    except Exception as e:
        print(f"执行查询时发生未知错误: {e}")
        return []
    finally:
        # 关闭数据库连接
        if connection:
            connection.close()


if __name__ == "__main__":
    # result = Connect_to_postgresql()
    # print(result)

    # 示例调用：同步SQLite数据库中的数据到PostgreSQL
    db_mapping = {
        "../data/visit.db": "linghang_db_main" # SQLite数据库路径: PostgreSQL数据库名
    }
    
    table_mapping = {
        "visit": "plat_schema.visit_table"  # SQLite表名: PostgreSQL表名（包含schema）
    }
    
    field_mapping = {
        "visit_table": {
            "page_now": "page_now",
            "page_before": "page_before",
            "user_id": "user_id",
            "user_agent": "user_agent",
            "timestamp": "timestamp",
        }
    }

    # 调用数据同步函数
    sync_result = data_sync_sqlite_postgre(db_mapping, table_mapping, field_mapping)
    print(f"数据同步结果: {sync_result}")
    
    # 示例调用：查询PostgreSQL表信息
    # 查询用户信息schema下的用户表结构
    # query_sql = 'SELECT * FROM "静态数据"."团队表" LIMIT 5;'
    # query_result = sql_postgre_query(query_sql)
    # print(f"查询结果: {query_result}")
