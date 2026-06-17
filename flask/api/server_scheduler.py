import schedule
import time
import threading
import sys
import os
import signal
import logging
from datetime import datetime
from functools import wraps
from server_rdc_update import issue_update, review_update
from server_db_backup import backup_db_files
from server_config_update import Basic_config_overwrite
from task_common import tasks_update
from branch_common import get_branch_leakage_data

# 创建日志目录（如果不存在）
import os
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
log_file_path = os.path.join(log_dir, 'server_scheduler.log')

# 检查logger是否已经配置
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
else:
    # 如果已配置，则添加文件处理器
    logger = logging.getLogger()
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

class TaskScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.tasks = []  # 记录添加的任务，用于启动时执行
    
    def add_task(self, task_func, schedule_type, *args, **kwargs):
        """
        添加定时任务
        
        :param task_func: 任务函数
        :param schedule_type: 调度类型，例如 "daily_at_12", "daily_at_24", "hourly", "every_30_minutes"
        :param args: 任务函数的位置参数
        :param kwargs: 任务函数的关键字参数
        """
        if schedule_type == "daily_at_12":
            schedule.every().day.at("12:00").do(task_func, *args, **kwargs)
        elif schedule_type == "daily_at_24":
            schedule.every().day.at("00:00").do(task_func, *args, **kwargs)
        elif schedule_type == "hourly":
            schedule.every().hour.do(task_func, *args, **kwargs)
        elif schedule_type == "every_2_hours":
            schedule.every(2).hours.do(task_func, *args, **kwargs)
        elif schedule_type == "every_30_minutes":
            schedule.every(30).minutes.do(task_func, *args, **kwargs)
        else:
            raise ValueError(f"不支持的调度类型: {schedule_type}")
        
        # 记录任务用于启动时执行
        self.tasks.append((task_func, args, kwargs))
        print(f"任务 {task_func.__name__} 已添加，调度类型: {schedule_type}")
    
    def execute_all_tasks_now(self):
        """立即执行所有已添加的任务"""
        if not self.tasks:
            print("没有已安排的任务需要立即执行")
            logging.info("没有已安排的任务需要立即执行")
            return
            
        print("正在启动时执行所有任务...")
        logging.info("正在启动时执行所有任务...")
        for task_func, args, kwargs in self.tasks:
            try:
                # 获取原函数的名称 (使用functools.wraps后，__name__会指向原函数)
                original_func_name = task_func.__name__
                print(f"正在执行任务: {original_func_name}")
                logging.info(f"开始执行任务: {original_func_name}")
                task_func(*args, **kwargs)
                print(f"任务 {original_func_name} 执行完成")
                logging.info(f"任务 {original_func_name} 执行完成")
            except Exception as e:
                logging.error(f"执行任务 {original_func_name} 时出错: {e}")
                print(f"执行任务 {original_func_name} 时出错: {e}")
        print("所有启动任务执行完成")
        logging.info("所有启动任务执行完成")
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("调度器已在运行中")
            return
            
        # 首先执行一次所有任务
        self.execute_all_tasks_now()
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            print("调度器未在运行")
            return
            
        self.running = False
        if self.thread:
            self.thread.join()
        print("任务调度器已停止")
    
    def _run_scheduler(self):
        """运行调度器的内部方法"""
        while self.running:
            schedule.run_pending()
            # 刷新日志确保及时写入
            for handler in logging.getLogger().handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            time.sleep(1)
    
    def list_tasks(self):
        """列出所有已安排的任务"""
        jobs = schedule.get_jobs()
        if not jobs:
            print("没有已安排的任务")
            return
            
        print("已安排的任务:")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job}")

# 通用的日志装饰器
def logged_task(task_func):
    """为任务函数添加日志记录的装饰器"""
    @wraps(task_func)
    def wrapper(*args, **kwargs):
        task_name = task_func.__name__
        logging.info(f"开始执行 {task_name} 任务")
        logging.getLogger().handlers[0].flush()  # 确保日志立即写入文件
        try:
            result = task_func(*args, **kwargs)
            logging.info(f"{task_name} 任务执行成功")
            logging.getLogger().handlers[0].flush()  # 确保日志立即写入文件
            return result
        except Exception as e:
            logging.error(f"执行 {task_name} 任务时出错: {e}")
            logging.getLogger().handlers[0].flush()  # 确保日志立即写入文件
            raise
    return wrapper

# 示例任务函数
def sample_task(name):
    """示例任务"""
    print(f"[{datetime.now()}] 执行任务: {name}")

if __name__ == "__main__":
    logging.info("调度器程序启动")
    # 创建调度器实例
    scheduler = TaskScheduler()
    
    # 添加RDC更新任务，每日12点执行issue_update，每日24点(00:00)执行review_update
    # 现在只需要修改import和以下add_task调用即可添加新任务
    scheduler.add_task(logged_task(issue_update), "hourly")
    scheduler.add_task(logged_task(review_update), "hourly")
    scheduler.add_task(logged_task(tasks_update), "hourly")
    scheduler.add_task(logged_task(Basic_config_overwrite), "hourly")
    scheduler.add_task(logged_task(backup_db_files), "every_2_hours")
    scheduler.add_task(logged_task(get_branch_leakage_data), "hourly")

    # 启动调度器
    scheduler.start()
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n接收到停止信号")
        logging.info("调度器接收到停止信号")
        scheduler.stop()
        logging.info("调度器已停止")
