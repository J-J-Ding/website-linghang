import logging
import os
from logging.handlers import RotatingFileHandler

# 全局标记 + 存储引用，避免重复配置
_initialized = False

def setup_logger(log_dir='../linghang/logs', log_file='app.log',
                 level=logging.INFO, max_bytes=50*1024*1024, backup_count=5):
    """
    统一日志配置入口
    
    :param target_logger_name: 你希望在业务代码中使用的 logger 名称，默认 "Logger"
    :return: 配置好的 target logger 实例（可选）
    """
    global _initialized
    if _initialized:
        return
    
    # 1. 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 2. 统一日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] [%(threadName)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 3. 文件处理器（轮转，避免文件过大）
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
        delay=True
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    
    # 4. 控制台处理器（开发环境友好，生产可关闭）
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # console_handler.setLevel(level)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # ---------- 3. 配置你的业务 Logger ----------
    business_logger = logging.getLogger("Logger")
    business_logger.setLevel(logging.INFO)
    business_logger.addHandler(file_handler)
    business_logger.addHandler(console_handler)
    business_logger.propagate = False   # 阻止日志冒泡到根 logger，避免重复

    # ---------- 4. 配置 Flask/Werkzeug 的 Logger ----------
    # Flask 开发服务器使用的是 werkzeug 的 logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)
    werkzeug_logger.propagate = False

    # 可选：如果你还希望 Flask 自身的日志（如 app.logger）也写入同一文件，
    # 可以同样配置 'flask.app' logger
    flask_app_logger = logging.getLogger("flask.app")
    flask_app_logger.setLevel(logging.INFO)
    flask_app_logger.addHandler(file_handler)
    flask_app_logger.propagate = False
    


setup_logger()