import os
import sys
import json
import dotenv
import psycopg2
from typing import List, Dict, Optional

class DatabaseHandler:
    """
    通用PostgreSQL数据库处理类
    """
    
    def __init__(self):
        """
        初始化数据库处理器，连接到PostgreSQL数据库
        """
        self.connection = self._connect_to_postgresql()
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口，自动关闭连接
        """
        self.close()

    def _connect_to_postgresql(self):
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
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        执行查询语句并返回结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表，每个元素是一个字典
        """
        if not self.connection:
            raise ConnectionError("数据库连接未建立")
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            # 获取数据
            rows = cursor.fetchall()
            # 转换为字典列表
            result = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            return result
        except Exception as e:
            print(f"执行查询时出错: {e}")
            raise e
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        执行更新语句(INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        if not self.connection:
            raise ConnectionError("数据库连接未建立")
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            return affected_rows
        except Exception as e:
            print(f"执行更新时出错: {e}")
            self.connection.rollback()
            raise e
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        批量执行更新语句
        
        Args:
            query: SQL更新语句
            params_list: 参数列表
            
        Returns:
            受影响的总行数
        """
        if not self.connection:
            raise ConnectionError("数据库连接未建立")
        
        try:
            cursor = self.connection.cursor()
            
            cursor.executemany(query, params_list)
            
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            return affected_rows
        except Exception as e:
            print(f"执行批量更新时出错: {e}")
            self.connection.rollback()
            raise e
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.connection:
            self.connection.close()
            self.connection = None

# 测试函数
if __name__ == "__main__":    
    def test_connection():
        """测试数据库连接"""
        print("测试数据库连接...")
        try:
            with DatabaseHandler() as db:
                if db.connection:
                    print("✓ 数据库连接成功")
                    return True
                else:
                    print("✗ 数据库连接失败")
                    return False
        except Exception as e:
            print(f"✗ 连接测试异常: {e}")
            return False

    def test_query():
        """测试查询功能"""
        print("\n测试查询功能...")
        try:
            with DatabaseHandler() as db:
                # 尝试查询一个系统表，确保即使没有用户表也能测试
                result = db.execute_query("SELECT version();")
                print(f"✓ 查询成功，返回 {len(result)} 行数据")
                print(f"  PostgreSQL版本: {result[0]['version'] if result else 'N/A'}")
                return True
        except Exception as e:
            print(f"✗ 查询测试异常: {e}")
            return False

    def test_update():
        """测试更新功能"""
        print("\n测试更新功能...")
        try:
            with DatabaseHandler() as db:
                # 创建一个临时测试表
                db.execute_update("""
                    CREATE TEMP TABLE test_table (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✓ 临时表创建成功")
                
                # 插入测试数据
                affected = db.execute_update(
                    "INSERT INTO test_table (name) VALUES (%s), (%s);",
                    ("测试1", "测试2")
                )
                print(f"✓ 插入操作成功，影响 {affected} 行")
                
                # 查询插入的数据
                result = db.execute_query("SELECT * FROM test_table;")
                print(f"✓ 查询插入的数据，共 {len(result)} 行")
                
                # 更新数据
                affected = db.execute_update(
                    "UPDATE test_table SET name = %s WHERE name = %s;",
                    ("更新测试", "测试1")
                )
                print(f"✓ 更新操作成功，影响 {affected} 行")
                
                return True
        except Exception as e:
            print(f"✗ 更新测试异常: {e}")
            return False

    def test_many():
        """测试批量操作功能"""
        print("\n测试批量操作功能...")
        try:
            with DatabaseHandler() as db:
                # 创建一个临时测试表
                db.execute_update("""
                    CREATE TEMP TABLE test_many_table (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50),
                        value INTEGER
                    );
                """)
                print("✓ 临时批量测试表创建成功")
                
                # 准备批量插入数据
                data = [
                    ("批量测试1", 100),
                    ("批量测试2", 200),
                    ("批量测试3", 300),
                ]
                
                # 批量插入
                affected = db.execute_many(
                    "INSERT INTO test_many_table (name, value) VALUES (%s, %s);",
                    data
                )
                print(f"✓ 批量插入成功，影响 {affected} 行")
                
                # 查询批量插入的数据
                result = db.execute_query("SELECT * FROM test_many_table;")
                print(f"✓ 查询批量插入的数据，共 {len(result)} 行")
                
                return True
        except Exception as e:
            print(f"✗ 批量操作测试异常: {e}")
            return False

    def run_all_tests():
        """运行所有测试"""
        print("开始测试 DatabaseHandler 类...")
        print("="*50)
        
        tests = [
            test_connection,
            test_query,
            test_update,
            test_many
        ]
        
        results = []
        for test_func in tests:
            results.append(test_func())
        
        print("\n" + "="*50)
        print("测试总结:")
        test_names = ["连接测试", "查询测试", "更新测试", "批量测试"]
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {name}: {status}")
        
        passed = sum(results)
        total = len(results)
        print(f"\n总体结果: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试均已通过！")
        else:
            print("⚠️  部分测试未通过，请检查数据库配置和连接。")

    # 运行测试
    run_all_tests()
