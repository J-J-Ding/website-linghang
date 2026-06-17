import os

# 数据库配置
DB_HOST = "10.239.69.17"
DB_DATABASE_REQUIREMENT_SCHEDULE = "requirement_automatic_schedule"  # 需求自动排期数据库
DB_USER = "root"
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = 3306
