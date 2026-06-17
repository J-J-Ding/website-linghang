import os
import glob
import shutil
import schedule
import time
from datetime import datetime, timedelta

# 源目录和目标目录
SOURCE_DIR = "/home/10171727@zte.intra/workspace/AI/AI/public/website-linghang/flask/data"
BACKUP_BASE_DIR = "/media/vdc/10171727B/db_backup"

def backup_db_files():
    """备份数据库文件并清理旧备份"""
    try:
        # 创建带时间戳的备份文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(BACKUP_BASE_DIR, f"sql_data_backup_{timestamp}")
        
        # 确保目标目录存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 查找所有.db文件并复制
        db_files = glob.glob(os.path.join(SOURCE_DIR, "*.db"))
        if not db_files:
            print("未找到任何.db文件")
            return False
            
        for db_file in db_files:
            filename = os.path.basename(db_file)
            destination = os.path.join(backup_dir, filename)
            shutil.copy2(db_file, destination)
            print(f"已备份: {filename}")
            
        print(f"备份完成，备份目录: {backup_dir}")
        
        # 清理2天前的备份
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f"备份过程中出错: {e}")
        return False

def cleanup_old_backups():
    """清理2天前的备份文件夹"""
    try:
        # 计算2天前的时间
        two_days_ago = datetime.now() - timedelta(days=2)
        
        # 查找所有备份文件夹
        pattern = os.path.join(BACKUP_BASE_DIR, "sql_data_backup_*")
        backup_dirs = glob.glob(pattern)
        
        deleted_count = 0
        for backup_dir in backup_dirs:
            # 从文件夹名提取时间戳
            dir_name = os.path.basename(backup_dir)
            try:
                # 提取时间戳部分 (格式: sql_data_backup_YYYYMMDD_HHMMSS)
                timestamp_str = dir_name.replace("sql_data_backup_", "")
                backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # 如果备份时间早于2天前，则删除
                if backup_time < two_days_ago:
                    shutil.rmtree(backup_dir)
                    print(f"已删除旧备份: {dir_name}")
                    deleted_count += 1
                    
            except ValueError:
                print(f"无法解析时间戳的备份文件夹: {dir_name}")
                
        print(f"清理完成，共删除 {deleted_count} 个旧备份")
        
    except Exception as e:
        print(f"清理旧备份时出错: {e}")


if __name__ == "__main__":
    # 立即执行一次备份
    backup_db_files()
