import os

# 数据库配置
DB_HOST = "10.239.69.17"
DB_HOST2 = "10.156.129.73"
DB_USER = "root"
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE_WH = "wh_ai_db"  # 故障波及案例单管理数据库
DB_PORT = 3306
