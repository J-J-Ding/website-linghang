import json
import psycopg2
from typing import List, Dict, Optional
from sql_utils import Connect_to_postgresql

def query_user_table(tool_input: str) -> List[Dict]:
    """
    查询PostgreSQL数据库中用户表的数据
    
    参数（JSON字符串格式）：
    - limit: 可选，限制返回的记录数
    - conditions: 可选，查询条件字典，如 {"name": "John", "age": 30}
    
    示例输入：
    - "{}"
    - "{\"limit\": 10}"
    - "{\"conditions\": {\"name\": \"张三\"}}"
    - "{\"limit\": 5, \"conditions\": {\"status\": \"active\"}}"
    
    返回值：
    - 用户表数据列表，每个元素是一个包含用户信息的字典
    """
    try:
        # 解析输入参数
        params = json.loads(tool_input)
        limit = params.get("limit")
        conditions = params.get("conditions", {})
        
        connection = Connect_to_postgresql()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor()
            
            # 构建查询语句
            query = "SELECT * FROM \"静态数据\".用户表"
            params_list = []
            
            # 如果有查询条件，则添加WHERE子句
            if conditions and len(conditions) > 0:
                where_conditions = []
                for key, value in conditions.items():
                    where_conditions.append(f"{key} = %s")
                    params_list.append(value)
                query += " WHERE " + " AND ".join(where_conditions)
            
            # 如果有limit限制
            if limit:
                query += " LIMIT %s"
                params_list.append(limit)
            
            query += ";"
            
            # 执行查询
            cursor.execute(query, params_list)
            
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
            print(f"查询用户表时出错: {e}")
            return []
        
        finally:
            # 关闭数据库连接
            if connection:
                cursor.close()
                connection.close()
    
    except json.JSONDecodeError as e:
        print(f"解析输入参数时出错: {e}")
        return []
    except Exception as e:
        print(f"执行查询时出错: {e}")
        return []


if __name__ == "__main__":    
    # 示例：查询所有用户
    print("\n查询所有用户:")
    all_users = query_user_table("{}")
    for user in all_users:
        print(user)
    
    # 示例：查询前5条记录
    print("\n查询前5条用户记录:")
    limited_users = query_user_table("{\"limit\": 5}")
    for user in limited_users:
        print(user)
    
    # 示例：带条件查询
    print("\n带条件查询示例（假设查询name='张三'的用户）:")
    conditional_users = query_user_table("{\"conditions\": {\"姓名\": \"张三\"}}")
    for user in conditional_users:
        print(user)
