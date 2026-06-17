import os

# 数据库配置
DB_HOST = "10.239.69.17"
DB_DATABASE_KNOW_BOARD = "knowledge_engineering"  # 知识工程数据库
DB_USER = "root"
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = 3306

# 表配置
TABLE_KNOWLEDGE_COMPONENT_TREE = "knowledge_component_tree"