from socket import socket

import paramiko
import time
import os
import re
from dataclasses import dataclass
from contextlib import contextmanager
from typing import Callable, Optional, Union, List, Tuple, Pattern, Generator, Dict, Any
from datetime import datetime, timedelta
import json

# ==============================
# Windows跳板机专用SSH客户端
# ==============================

class WindowsSSHClient:
    """
    Windows跳板机专用SSH客户端
    用于连接Windows跳板机并解压tar文件
    """

    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ssh_client = None
        self.sftp_client = None

    def connect(self):
        """连接到Windows跳板机"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=30
            )
            print(f"✅ 已连接到Windows跳板机: {self.host}")
            return True
        except Exception as e:
            print(f"❌ 连接Windows跳板机失败: {str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def execute_command(self, command: str) -> Tuple[str, str]:
        """在Windows跳板机上执行命令"""
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        stdout_str = stdout.read().decode('gbk', errors='ignore')
        stderr_str = stderr.read().decode('gbk', errors='ignore')
        return stdout_str, stderr_str

    def find_recent_tar_files(self, base_path: str, max_days_lookback: int = 2) -> List[Dict]:
        """
        查找所有tar文件 没有日期限制，返回所有文件
        Args:
            base_path: 基础路径
            max_days_lookback: 保留参数但完全忽略
        """

        files_info = []

        # 检查目录是否存在
        check_cmd = f'if exist "{base_path}" (echo EXISTS) else (echo NOT_EXISTS)'
        stdout, stderr = self.execute_command(check_cmd)

        if "NOT_EXISTS" in stdout:
            print(f"❌ 目录不存在: {base_path}")
            return files_info

        print(f"✅ 目录存在: {base_path}")

        # 获取当前日期（仅用于日志输出）
        today = datetime.now()
        print(f"📅 当前日期: {today.strftime('%Y-%m-%d')}")

        # 使用dir命令查找所有tar文件
        dir_cmd = f'dir "{base_path}\\*.tar" /B /T:W /OD'
        stdout, stderr = self.execute_command(dir_cmd)

        if not stdout.strip():
            print(f"❌ 未找到.tar文件: {base_path}")
            return files_info

        tar_files = []
        file_lines = stdout.strip().split('\n')

        # 解析文件名
        for line in file_lines:
            line = line.strip()
            if line and line.endswith('.tar'):
                tar_files.append(line)

        print(f"🔍 找到 {len(tar_files)} 个tar文件")

        if not tar_files:
            return files_info

        print(f"📊 开始处理 {len(tar_files)} 个tar文件...")

        # 处理所有文件，不做任何日期过滤
        processed_count = 0
        skipped_count = 0

        for tar_file in tar_files:
            processed_count += 1
            try:
                full_path = os.path.join(base_path, tar_file)

                # 获取文件详细信息
                detail_cmd = f'dir "{full_path}" /T:W'
                detail_stdout, _ = self.execute_command(detail_cmd)

                # 解析日期
                file_date = None
                date_patterns = [
                    r'(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2})',  # 2026/02/06 15:30
                    r'(\d{2})[/-](\d{2})[/-](\d{4})\s+(\d{2}):(\d{2})',  # 06/02/2026 15:30
                    r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})',  # 2026-02-06 15:30
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, detail_stdout)
                    if match:
                        try:
                            if len(match.group(1)) == 4:  # 年份在前
                                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                            else:  # 日期在前
                                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

                            file_date = datetime(year, month, day)
                            break
                        except:
                            continue

                if not file_date:
                    # 如果没有找到日期，使用文件修改时间或当前日期
                    file_date = today
                    print(f"⚠️ 无法解析 {tar_file} 的日期，使用当前日期")

                # 获取文件大小
                size_cmd = f'for %i in ("{full_path}") do @echo %~zi'
                size_stdout, _ = self.execute_command(size_cmd)
                file_size = 0
                try:
                    file_size = int(size_stdout.strip())
                except:
                    pass

                file_info = {
                    'filename': tar_file,
                    'full_path': full_path,
                    'date': file_date.strftime('%Y-%m-%d'),
                    'datetime': file_date,
                    'size': file_size
                }

                files_info.append(file_info)

                if processed_count % 100 == 0:
                    print(f"📊 进度: 已处理 {processed_count}/{len(tar_files)} 个文件，已添加 {len(files_info)} 个文件")

            except Exception as e:
                skipped_count += 1
                print(f"⚠️ 处理文件失败 {tar_file}: {str(e)}")
                continue

        print(
            f"📊 文件处理完成，共处理 {processed_count} 个文件，成功添加 {len(files_info)} 个文件，跳过 {skipped_count} 个文件")

        print(f"✅ 返回所有 {len(files_info)} 个tar文件")

        files_info.sort(key=lambda x: x['datetime'], reverse=True)

        # 输出按日期统计的信息
        date_stats = {}
        for file_info in files_info:
            date = file_info['date']
            date_stats[date] = date_stats.get(date, 0) + 1

        print(f"📊 按日期统计:")
        for date, count in sorted(date_stats.items(), reverse=True):
            print(f"  - {date}: {count}个文件")

        return files_info

    def _collect_all_items_recursive(self, directory_path: str, max_depth: int = 5, current_depth: int = 0) -> List[
        str]:
        """
        递归收集目录中的所有文件和子目录路径
        """
        all_items = []

        if current_depth >= max_depth:
            return all_items

        try:
            directory_path = directory_path.replace('/', '\\')

            # 检查目录是否存在
            if not self._check_directory_exists(directory_path):
                return all_items

            # 列出目录内容
            list_cmd = f'dir "{directory_path}" /B'
            stdout, _ = self.execute_command(list_cmd)

            if stdout.strip():
                items = [item.strip() for item in stdout.strip().splitlines() if item.strip()]

                for item in items:
                    item_path = os.path.join(directory_path, item)
                    item_path = item_path.replace('/', '\\')

                    # 添加到列表
                    all_items.append(item_path)

                    # 如果是目录，递归收集
                    if self._is_directory(item_path):
                        if 'sysdisk0' in item.lower():
                            continue
                        sub_items = self._collect_all_items_recursive(
                            item_path, max_depth, current_depth + 1
                        )
                        all_items.extend(sub_items)

        except Exception as e:
            print(f"⚠️ 递归收集文件失败 {directory_path}: {str(e)}")

        return all_items

    def _extract_tar_file_fixed(self, tar_path: str, extract_path: str) -> bool:
        """
        Windows Server 2012 环境解压tar文件  使用7z解压，支持无后缀的tar包
        """

        tar_path = tar_path.replace('/', '\\')
        extract_path = extract_path.replace('/', '\\')

        print(f"🔄 解压文件: {os.path.basename(tar_path)}")
        print(f"📁 解压到: {extract_path}")

        # 确保解压目录存在
        mkdir_cmd = f'mkdir "{extract_path}" 2>nul'
        self.execute_command(mkdir_cmd)

        # 使用7z直接解压
        seven_zip_paths = [
            r'"C:\Program Files\7-Zip\7z.exe"',
            r'"C:\Program Files (x86)\7-Zip\7z.exe"',
        ]

        # 首先检查文件是否有.tar后缀，如果没有，先复制一个带后缀的临时文件
        tar_filename = os.path.basename(tar_path)
        tar_dir = os.path.dirname(tar_path)

        # 如果文件名不包含.tar后缀，创建临时文件
        if not tar_filename.lower().endswith('.tar'):
            temp_tar_path = os.path.join(tar_dir, f"{tar_filename}.tar")
            print(f"🔄 文件无.tar后缀，创建临时文件: {temp_tar_path}")

            # 复制文件到临时文件
            copy_cmd = f'copy "{tar_path}" "{temp_tar_path}" 2>nul'
            copy_stdout, copy_stderr = self.execute_command(copy_cmd)

            # 使用临时文件进行解压
            tar_to_use = temp_tar_path
            is_temp_file = True
        else:
            tar_to_use = tar_path
            is_temp_file = False

        # 尝试所有7z路径
        for seven_zip_path in seven_zip_paths:
            check_exe_cmd = f'if exist {seven_zip_path} (echo EXISTS) else (echo NOT_EXISTS)'
            check_exe_stdout, _ = self.execute_command(check_exe_cmd)

            if "NOT_EXISTS" in check_exe_stdout:
                continue

            tar_cmd_7z = f'{seven_zip_path} x "{tar_to_use}" -o"{extract_path}" -y 2>&1'
            print(f"📄 执行命令: {tar_cmd_7z}")

            stdout_7z, stderr_7z = self.execute_command(tar_cmd_7z)

            # 检查是否解压成功
            check_cmd = f'dir "{extract_path}" /B'
            stdout_check, _ = self.execute_command(check_cmd)

            if stdout_check.strip():
                file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
                print(f"✅ 7z解压成功，解压出 {file_count} 个文件/目录")

                # 清理临时文件
                if is_temp_file:
                    del_cmd = f'del "{temp_tar_path}" 2>nul'
                    self.execute_command(del_cmd)
                    print(f"🧹 清理临时文件: {temp_tar_path}")

                return True
            else:
                print(f"❌ 7z解压失败，输出: {stdout_7z[:200] if stdout_7z else '空'}")

        # 清理临时文件（如果解压失败也要清理）
        if is_temp_file:
            del_cmd = f'del "{temp_tar_path}" 2>nul'
            self.execute_command(del_cmd)
            print(f"🧹 清理临时文件: {temp_tar_path}")

        # 尝试使用7z先列出内容，再尝试不同的解压参数
        print(f"🔄 尝试使用不同的7z解压参数...")

        for seven_zip_path in seven_zip_paths:
            check_exe_cmd = f'if exist {seven_zip_path} (echo EXISTS) else (echo NOT_EXISTS)'
            check_exe_stdout, _ = self.execute_command(check_exe_cmd)

            if "NOT_EXISTS" in check_exe_stdout:
                continue

            # 尝试使用 -t* 自动检测格式
            tar_cmd_7z = f'{seven_zip_path} x "{tar_path}" -o"{extract_path}" -t* -y 2>&1'
            print(f"📄 执行命令: {tar_cmd_7z}")

            stdout_7z, stderr_7z = self.execute_command(tar_cmd_7z)

            check_cmd = f'dir "{extract_path}" /B'
            stdout_check, _ = self.execute_command(check_cmd)

            if stdout_check.strip():
                file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
                print(f"✅ 7z自动格式检测解压成功，解压出 {file_count} 个文件/目录")
                return True

        # 如果文件无后缀，尝试使用7z的e命令
        if not tar_filename.lower().endswith('.tar'):
            print(f"🔄 尝试使用7z e命令解压无后缀文件...")

            for seven_zip_path in seven_zip_paths:
                check_exe_cmd = f'if exist {seven_zip_path} (echo EXISTS) else (echo NOT_EXISTS)'
                check_exe_stdout, _ = self.execute_command(check_exe_cmd)

                if "NOT_EXISTS" in check_exe_stdout:
                    continue

                # e命令：解压到当前目录，不保留目录结构
                tar_cmd_7z = f'{seven_zip_path} e "{tar_path}" -o"{extract_path}" -y 2>&1'
                print(f"📄 执行命令: {tar_cmd_7z}")

                stdout_7z, stderr_7z = self.execute_command(tar_cmd_7z)

                check_cmd = f'dir "{extract_path}" /B'
                stdout_check, _ = self.execute_command(check_cmd)

                if stdout_check.strip():
                    file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
                    print(f"✅ 7z e命令解压成功，解压出 {file_count} 个文件/目录")
                    return True

        print(f"❌ 所有7z解压方式都失败")
        return False

    def _recursive_extract_and_find(self, tar_path: str, extract_base_path: str,
                                    extract_subdir: str = "", current_depth: int = 0,
                                    max_depth: int = 10) -> List[str]:
        """
        递归解压tar包到指定子目录  使用7z解压
        """
        if current_depth >= max_depth:
            print(f"⚠️ 达到最大递归深度 {max_depth}")
            return []

        # 参数验证
        if not tar_path or not extract_base_path:
            return []

        # 统一路径格式
        tar_path = tar_path.replace('/', '\\')
        extract_base_path = extract_base_path.replace('/', '\\')

        if extract_subdir:
            # 只取文件名部分作为子目录，不要任何路径
            extract_subdir = os.path.basename(extract_subdir.replace('/', '\\'))
            # 如果还有.tar后缀，去掉
            if extract_subdir.lower().endswith('.tar'):
                extract_subdir = os.path.splitext(extract_subdir)[0]

        # 解压文件（包括无后缀的大文件）
        if self._is_directory(tar_path):
            print(f"⚠️ 跳过目录: {tar_path}")
            return []

        #  构建解压路径 始终在当前目录下创建子目
        if extract_subdir:
            # 直接使用文件名作为子目录名
            extract_path = os.path.join(extract_base_path, extract_subdir)
        else:
            tar_filename = os.path.basename(tar_path)
            # 移除.tar后缀
            tar_name_without_ext = os.path.splitext(tar_filename)[0]
            extract_path = os.path.join(extract_base_path, tar_name_without_ext)

        extract_path = extract_path.replace('/', '\\')

        print(f"\n📊 深度 {current_depth}: 解压 {os.path.basename(tar_path)}")
        print(f"📁 解压到: {extract_path}")

        kpi_logs = []

        try:
            # 1. 创建解压目录
            mkdir_cmd = f'mkdir "{extract_path}" 2>nul'
            self.execute_command(mkdir_cmd)

            # 2. 解压tar文件
            print(f"🔄 正在解压: {os.path.basename(tar_path)}")
            if not self._extract_tar_file_fixed(tar_path, extract_path):
                print(f"❌ 解压失败: {os.path.basename(tar_path)}")
                return []
            print(f"✅ 解压成功")

            # 3. 获取解压目录中的所有内容
            items = self._list_directory(extract_path)
            print(f"📋 解压出 {len(items)} 个项目:")
            for item in items:
                print(f"  - {item}")

            # 4. 遍历所有项目
            for item in items:
                item_path = os.path.join(extract_path, item)
                item_path = item_path.replace('/', '\\')

                is_dir = self._is_directory(item_path)

                if is_dir:
                    print(f"📁 处理目录: {item}")

                    # 检查目录下是否有同名无后缀文件
                    dir_name = os.path.basename(item_path)
                    same_name_file = os.path.join(item_path, dir_name)
                    same_name_file = same_name_file.replace('/', '\\')

                    if self._file_exists(same_name_file):
                        file_size = self._get_file_size(same_name_file)
                        print(f"🎯 发现同名无后缀文件: {same_name_file} ({file_size} 字节)")
                        print(f"🔄 这是一个需要解压的tar包文件")

                        #  在当前目录下创建子目录
                        new_extract_subdir = dir_name + "_extracted"
                        # 新的解压路径是当前extract_path下的子目录
                        new_extract_path = os.path.join(extract_path, new_extract_subdir)

                        print(f"📁 递归解压到子目录: {new_extract_path}")

                        # 递归解压这个同名文件
                        nested_kpi_logs = self._recursive_extract_and_find(
                            same_name_file,
                            extract_path,  # 使用当前extract_path作为基础路径
                            new_extract_subdir,  # 只传目录名
                            current_depth + 1,
                            max_depth
                        )

                        if nested_kpi_logs:
                            print(f"✅ 从同名文件中找到 {len(nested_kpi_logs)} 个kpi日志")
                            kpi_logs.extend(nested_kpi_logs)

                    # 检查home目录
                    home_path = os.path.join(item_path, 'home')
                    home_path = home_path.replace('/', '\\')
                    if self._check_directory_exists(home_path):
                        print(f"✅ 找到home目录: {home_path}")
                        home_kpi_logs = self._find_kpi_in_home_directory(home_path)
                        if home_kpi_logs:
                            print(f"✅ 找到 {len(home_kpi_logs)} 个kpi日志")
                            kpi_logs.extend(home_kpi_logs)

                    # 递归查找该目录下的所有文件
                    all_files = self._list_directory(item_path)
                    for file_name in all_files:
                        file_full_path = os.path.join(item_path, file_name)
                        file_full_path = file_full_path.replace('/', '\\')

                        # 跳过目录
                        if self._is_directory(file_full_path):
                            continue

                        # 检查文件大小，大文件可能是tar包
                        file_size = self._get_file_size(file_full_path)

                        # 如果是.tar文件或大文件（> 10MB），尝试解压
                        if file_name.lower().endswith('.tar') or file_size > 1024 * 1024 * 10:
                            print(f"  📦 发现潜在tar文件: {file_name} (大小: {file_size} 字节)")

                            # 在当前目录下创建子目录
                            file_name_without_ext = os.path.splitext(file_name)[0]
                            if not file_name_without_ext:
                                file_name_without_ext = file_name + "_extracted"

                            nested_kpi_logs = self._recursive_extract_and_find(
                                file_full_path,
                                extract_path,  # 使用当前extract_path作为基础路径
                                file_name_without_ext,
                                current_depth + 1,
                                max_depth
                            )
                            if nested_kpi_logs:
                                kpi_logs.extend(nested_kpi_logs)

                else:
                    # 处理文件
                    file_size = self._get_file_size(item_path)

                    # 如果是大文件（> 1MB），尝试作为tar包解压
                    if file_size > 1024 * 1024:  # 1MB
                        print(f"🤔 发现大文件: {item} ({file_size} 字节)")
                        print(f"🔄 尝试作为tar包解压...")

                        # 在当前目录下创建子目录
                        new_extract_subdir = item + "_extracted"

                        # 递归解压这个文件
                        nested_kpi_logs = self._recursive_extract_and_find(
                            item_path,
                            extract_path,  # 使用当前extract_path作为基础路径
                            new_extract_subdir,
                            current_depth + 1,
                            max_depth
                        )

                        if nested_kpi_logs:
                            kpi_logs.extend(nested_kpi_logs)

                    # 如果是.tar文件
                    elif item.lower().endswith('.tar'):
                        print(f"  📦 发现tar文件: {item}")

                        # 在当前目录下创建子目录
                        tar_name_without_ext = os.path.splitext(item)[0]

                        nested_kpi_logs = self._recursive_extract_and_find(
                            item_path,
                            extract_path,  # 使用当前extract_path作为基础路径
                            tar_name_without_ext,
                            current_depth + 1,
                            max_depth
                        )
                        if nested_kpi_logs:
                            kpi_logs.extend(nested_kpi_logs)

            return kpi_logs

        except Exception as e:
            print(f"❌ 递归解压失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        try:
            file_path = file_path.replace('/', '\\')

            # 检查路径中是否包含非法字符
            if '/F:' in file_path or '\\F:' in file_path:
                print(f"⚠️ 检测到非法路径: {file_path}")
                return False

            # 检查文件是否存在
            check_cmd = f'if exist "{file_path}" (echo EXISTS) else (echo NOT_EXISTS)'
            stdout, _ = self.execute_command(check_cmd)

            # 再检查是否是文件（不是目录）
            check_dir_cmd = f'if exist "{file_path}\\" (echo IS_DIR) else (echo NOT_DIR)'
            stdout_dir, _ = self.execute_command(check_dir_cmd)

            is_file = "EXISTS" in stdout and "IS_DIR" not in stdout_dir
            return is_file
        except:
            return False

    def _find_tar_files_in_directory(self, directory_path: str) -> List[str]:
        """查找目录中的所有.tar文件"""
        tar_files = []

        try:
            directory_path = directory_path.replace('/', '\\')

            check_cmd = f'if exist "{directory_path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
            stdout, _ = self.execute_command(check_cmd)
            if "NOT_EXISTS" in stdout:
                return tar_files

            # 查找.tar文件
            list_cmd = f'dir "{directory_path}\\*.tar" /B'
            stdout, _ = self.execute_command(list_cmd)

            if stdout.strip():
                for line in stdout.strip().splitlines():
                    file_name = line.strip()
                    if file_name and file_name.lower().endswith('.tar'):
                        full_path = os.path.join(directory_path, file_name)
                        full_path = full_path.replace('/', '\\')
                        tar_files.append(full_path)
                        print(f"      📦 找到tar文件: {file_name}")

        except Exception as e:
            print(f"⚠️ 查找tar文件失败: {str(e)}")

        return tar_files


    def find_tar_files(self, base_path: str, days_back: int = 7) -> List[Dict]:
        """
        查找指定目录下的tar文件，按日期过滤

        Args:
            base_path: 基础路径，如 "D:\\111"
            days_back: 回溯天数，默认7天

        Returns:
            返回tar文件信息列表
        """
        files_info = []

        # 检查目录是否存在 - 使用更可靠的命令
        check_cmd = f'if exist "{base_path}" (echo EXISTS) else (echo NOT_EXISTS)'
        stdout, stderr = self.execute_command(check_cmd)

        if "NOT_EXISTS" in stdout:
            print(f"❌ 目录不存在: {base_path}")
            return files_info

        print(f"✅ 目录存在: {base_path}")

        ps_cmd = f'powershell "Get-ChildItem -Path \'{base_path}\' -Filter *.tar | Select-Object Name, FullName, LastWriteTime, Length | ConvertTo-Json"'
        stdout, stderr = self.execute_command(ps_cmd)

        if stderr and "无法将" in stderr:
            # 使用dir命令
            print("⚠️ PowerShell不可用，使用dir命令")
            return self._find_tar_files_with_dir(base_path, days_back)

        try:
            if stdout.strip():

                files_data = json.loads(stdout)

                # 如果是单个文件，转换为列表
                if isinstance(files_data, dict):
                    files_data = [files_data]

                today = datetime.now()

                for file_data in files_data:
                    try:
                        # 解析文件名
                        filename = file_data.get('Name', '')
                        full_path = file_data.get('FullName', '')

                        if not filename or not filename.endswith('.tar'):
                            continue

                        # 解析修改时间
                        last_write_str = file_data.get('LastWriteTime', '')
                        if last_write_str:
                            try:
                                # PowerShell返回的时间格式可能是 "2026-02-06T15:30:45.1234567+08:00"
                                if 'T' in last_write_str:
                                    file_date_str = last_write_str.split('T')[0]
                                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                                else:
                                    # 尝试其他格式
                                    file_date = datetime.strptime(last_write_str.split()[0], '%Y/%m/%d')
                            except:
                                # 如果解析失败，使用当前日期
                                file_date = today
                        else:
                            file_date = today

                        # 检查是否在指定天数内
                        if (today - file_date).days <= days_back:
                            file_info = {
                                'filename': filename,
                                'full_path': full_path,
                                'date': file_date.strftime('%Y-%m-%d'),
                                'datetime': file_date,
                                'size': file_data.get('Length', 0)
                            }
                            files_info.append(file_info)

                            print(
                                f"📁 找到tar文件: {filename} - 日期: {file_date.strftime('%Y-%m-%d')} - 大小: {file_info['size']}字节")

                    except Exception as e:
                        print(f"⚠️ 处理文件信息失败: {str(e)}")
                        continue

            # 按日期排序（最新的在前）
            files_info.sort(key=lambda x: x['datetime'], reverse=True)

            return files_info

        except Exception as e:
            print(f"❌ JSON解析失败，使用dir命令: {str(e)}")
            return self._find_tar_files_with_dir(base_path, days_back)

    def _find_tar_files_with_dir(self, base_path: str, days_back: int = 7) -> List[Dict]:
        """
        使用dir命令查找tar文件
        """

        files_info = []

        # 使用dir命令查找tar文件
        dir_cmd = f'dir "{base_path}\\*.tar" /B /T:W /O:-D'
        stdout, stderr = self.execute_command(dir_cmd)

        if not stdout.strip():
            dir_cmd = f'dir "{base_path}" /B'
            stdout, stderr = self.execute_command(dir_cmd)

        if not stdout.strip():
            print(f"❌ 未找到.tar文件: {base_path}")
            return files_info

        tar_files = []
        file_lines = stdout.strip().split('\n')

        # 解析文件名
        for line in file_lines:
            line = line.strip()
            if line and line.endswith('.tar'):
                tar_files.append(line)

        print(f"🔍 找到 {len(tar_files)} 个tar文件: {tar_files}")

        if not tar_files:
            return files_info

        today = datetime.now()

        # 获取每个文件的详细信息
        for tar_file in tar_files:
            try:
                full_path = os.path.join(base_path, tar_file)

                # 获取文件详细信息
                detail_cmd = f'dir "{full_path}" /T:W'
                detail_stdout, _ = self.execute_command(detail_cmd)

                # 解析文件日期 - 匹配多种格式
                date_patterns = [
                    r'(\d{4})[/-](\d{2})[/-](\d{2})\s+(\d{2}):(\d{2})',  # 2026/02/06 15:30
                    r'(\d{2})[/-](\d{2})[/-](\d{4})\s+(\d{2}):(\d{2})',  # 06/02/2026 15:30
                    r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})',  # 2026-02-06 15:30
                ]

                file_date = None
                for pattern in date_patterns:
                    match = re.search(pattern, detail_stdout)
                    if match:
                        try:
                            if len(match.group(1)) == 4:  # 年份在前
                                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                            else:  # 日期在前
                                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

                            file_date = datetime(year, month, day)
                            break
                        except:
                            continue

                if not file_date:
                    # 如果没有找到日期，使用当前日期
                    file_date = today
                    print(f"⚠️ 无法解析 {tar_file} 的日期，使用当前日期")

                # 检查是否在指定天数内
                if (today - file_date).days <= days_back:
                    # 获取文件大小
                    size_cmd = f'for %i in ("{full_path}") do @echo %~zi'
                    size_stdout, _ = self.execute_command(size_cmd)
                    file_size = 0
                    try:
                        file_size = int(size_stdout.strip())
                    except:
                        pass

                    file_info = {
                        'filename': tar_file,
                        'full_path': full_path,
                        'date': file_date.strftime('%Y-%m-%d'),
                        'datetime': file_date,
                        'size': file_size
                    }
                    files_info.append(file_info)

                    print(f"📁 找到tar文件: {tar_file} - 日期: {file_date.strftime('%Y-%m-%d')} - 大小: {file_size}字节")

            except Exception as e:
                print(f"⚠️ 处理文件失败 {tar_file}: {str(e)}")
                continue

        # 按日期排序（最新的在前）
        files_info.sort(key=lambda x: x['datetime'], reverse=True)

        return files_info

    def _get_file_size(self, file_path: str) -> int:
        """
        获取文件大小（字节）
        """
        try:
            file_path = file_path.replace('/', '\\')

            ps_cmd = f'powershell -command "(Get-Item \'{file_path}\').Length"'
            stdout, _ = self.execute_command(ps_cmd)

            if stdout.strip():
                try:
                    return int(stdout.strip())
                except:
                    pass

            # 备选方法
            size_cmd = f'for %i in ("{file_path}") do @echo %~zi'
            stdout, _ = self.execute_command(size_cmd)

            if stdout.strip():
                return int(stdout.strip())

            return 0
        except:
            return 0


    def _ensure_remote_dir_exists(self, remote_dir: str):
        """确保远程目录存在"""

        try:
            self.sftp_client.stat(remote_dir)
        except IOError:
            # 目录不存在，创建
            parent_dir = os.path.dirname(remote_dir)
            if parent_dir and parent_dir != remote_dir:
                self._ensure_remote_dir_exists(parent_dir)

            mkdir_cmd = f'mkdir "{remote_dir}"'
            self.execute_command(mkdir_cmd)


    def find_kpi_logs_in_tar(self, tar_path: str, extract_base_path: str) -> List[str]:
        """
        在指定的base_path下解压tar文件并查找kpi日志
        保留kpi日志，清理解压的文件
        """

        print(f"\n{'=' * 60}")
        print(f"📦 处理tar文件: {os.path.basename(tar_path)}")
        print(f"{'=' * 60}")

        # 根据tar文件名创建子目录
        tar_filename = os.path.basename(tar_path)
        tar_name_without_ext = os.path.splitext(tar_filename)[0]

        print(f"📁 解压到子目录: {tar_name_without_ext}")

        kpi_logs = self._recursive_extract_and_find(
            tar_path,
            extract_base_path,
            tar_name_without_ext
        )

        print(f"\n🔍 找到 {len(kpi_logs)} 个 kpi 日志，开始清理其他文件...")
        self.cleanup_extracted_files_except_kpi(extract_base_path, tar_name_without_ext, kpi_logs)

        return kpi_logs

    def cleanup_extracted_files_except_kpi(self, extract_base_path: str, tar_name: str, kpi_logs: List[str]):
        """
        清理解压目录中除了 kpi 日志外的所有文件
        如果没找到 kpi 日志，则删除整个目录
        如果找到 kpi 日志，则只保留 kpi 日志文件
        """
        try:

            print(f"\n{'=' * 60}")
            print(f"🧹 开始清理: extract_base_path={extract_base_path}, tar_name={tar_name}")
            print(f"{'=' * 60}")

            # 构建 tar 解压的完整路径
            tar_extract_path = os.path.join(extract_base_path, tar_name)
            tar_extract_path = tar_extract_path.replace('/', '\\')

            print(f"📁 原始解压目录: {tar_extract_path}")

            # 如果没有找到任何 kpi 日志，直接删除整个目录
            if not kpi_logs:
                print(f"⚠️ 未找到任何 kpi 日志文件，删除整个目录")
                del_cmd = f'rmdir /S /Q "{tar_extract_path}" 2>nul'
                self.execute_command(del_cmd)
                print(f"✅ 已删除: {tar_extract_path}")
                return True

            # 如果找到了 kpi 日志，只保留这些文件
            print(f"📊 找到 {len(kpi_logs)} 个 kpi 日志文件:")
            for i, log in enumerate(kpi_logs):
                print(f"  {i + 1}. {log}")

            # 创建临时目录存放 kpi 日志 - 使用更简单的临时目录名
            temp_dir = os.path.join(extract_base_path, f"{tar_name}_temp")
            temp_dir = temp_dir.replace('/', '\\')
            print(f"📁 临时目录: {temp_dir}")

            # 删除可能存在的旧临时目录
            del_cmd = f'rmdir /S /Q "{temp_dir}" 2>nul'
            self.execute_command(del_cmd)
            print(f"✅ 已清理旧临时目录")

            # 创建临时目录
            mkdir_cmd = f'mkdir "{temp_dir}" 2>nul'
            self.execute_command(mkdir_cmd)
            print(f"✅ 已创建临时目录")

            copied_filenames = []

            for kpi_log in kpi_logs:
                kpi_log = kpi_log.replace('/', '\\')
                print(f"\n📄 处理kpi日志: {kpi_log}")

                path_parts = kpi_log.split('\\')
                filename = path_parts[-1] if path_parts else kpi_log
                print(f"  📝 方法1提取文件名: '{filename}'")

                if '/' in filename:
                    filename = filename.split('/')[-1]
                    print(f"  📝 方法2处理正斜杠后: '{filename}'")

                filename = filename.strip()
                print(f"  📝 最终文件名: '{filename}'")

                # 构建临时文件路径 - 直接放在临时目录下
                temp_file = os.path.join(temp_dir, filename)
                temp_file = temp_file.replace('/', '\\')
                print(f"  📝 临时文件路径: {temp_file}")

                # 检查源文件是否存在
                check_cmd = f'if exist "{kpi_log}" (echo EXISTS) else (echo NOT_EXISTS)'
                check_stdout, _ = self.execute_command(check_cmd)
                if "EXISTS" in check_stdout:
                    print(f"  ✅ 源文件存在")

                    # 复制文件到临时目录
                    copy_cmd = f'copy "{kpi_log}" "{temp_file}" 2>nul'
                    copy_stdout, copy_stderr = self.execute_command(copy_cmd)
                    print(f"  📋 复制结果: {copy_stdout[:100] if copy_stdout else '空'}")

                    # 验证文件是否成功复制
                    verify_cmd = f'if exist "{temp_file}" (echo EXISTS) else (echo NOT_EXISTS)'
                    verify_stdout, _ = self.execute_command(verify_cmd)
                    if "EXISTS" in verify_stdout:
                        print(f"  ✅ 文件复制成功: {temp_file}")
                        copied_filenames.append(filename)
                    else:
                        print(f"  ❌ 文件复制失败: {temp_file}")
                else:
                    print(f"  ❌ 源文件不存在: {kpi_log}")

            # 验证临时目录中的文件
            print(f"\n🔍 验证临时目录内容: {temp_dir}")
            verify_cmd = f'dir "{temp_dir}" /B'
            stdout, _ = self.execute_command(verify_cmd)

            if stdout and stdout.strip():
                temp_files = [f.strip() for f in stdout.strip().splitlines() if f.strip()]
                print(f"📋 临时目录中有 {len(temp_files)} 个文件:")
                for i, f in enumerate(temp_files):
                    print(f"  {i + 1}. {f}")
            else:
                print(f"⚠️ 警告：临时目录为空！")
                print(f"  临时目录: {temp_dir}")
                print(f"  尝试复制的文件数: {len(copied_filenames)}")
                return False

            # 删除原始解压目录
            print(f"\n🗑️ 删除原始解压目录: {tar_extract_path}")
            del_cmd = f'rmdir /S /Q "{tar_extract_path}" 2>nul'
            del_stdout, del_stderr = self.execute_command(del_cmd)
            print(f"  ✅ 已删除")

            # 重新创建根目录
            print(f"📁 重新创建目录: {tar_extract_path}")
            mkdir_cmd = f'mkdir "{tar_extract_path}" 2>nul'
            self.execute_command(mkdir_cmd)
            print(f"  ✅ 已创建")

            # 从临时目录恢复文件到根目录
            print(f"\n📋 恢复 kpi 日志到根目录: {tar_extract_path}")
            for filename in copied_filenames:
                # 临时文件路径
                temp_file = os.path.join(temp_dir, filename)
                temp_file = temp_file.replace('/', '\\')

                # 目标文件路径 - 直接放在根目录下
                target_file = os.path.join(tar_extract_path, filename)
                target_file = target_file.replace('/', '\\')

                print(f"  📄 恢复文件: {filename}")
                print(f"    源: {temp_file}")
                print(f"    目标: {target_file}")

                # 复制文件到目标位置
                copy_cmd = f'copy "{temp_file}" "{target_file}" 2>nul'
                copy_stdout, _ = self.execute_command(copy_cmd)

                # 验证文件是否成功复制
                verify_cmd = f'if exist "{target_file}" (echo EXISTS) else (echo NOT_EXISTS)'
                verify_stdout, _ = self.execute_command(verify_cmd)
                if "EXISTS" in verify_stdout:
                    print(f"  ✅ 恢复成功")
                else:
                    print(f"  ❌ 恢复失败")

            # 验证根目录中的文件
            print(f"\n🔍 验证根目录内容: {tar_extract_path}")
            verify_cmd = f'dir "{tar_extract_path}" /B'
            stdout, _ = self.execute_command(verify_cmd)

            if stdout and stdout.strip():
                root_files = [f.strip() for f in stdout.strip().splitlines() if f.strip()]
                print(f"📋 根目录中有 {len(root_files)} 个文件:")
                for i, f in enumerate(root_files):
                    print(f"  {i + 1}. {f}")
            else:
                print(f"⚠️ 警告：根目录为空！")

            # 清理临时目录
            print(f"\n🧹 清理临时目录: {temp_dir}")
            del_cmd = f'rmdir /S /Q "{temp_dir}" 2>nul'
            self.execute_command(del_cmd)
            print(f"  ✅ 已清理")

            print(f"\n✅ 清理完成")
            return True

        except Exception as e:
            print(f"❌ 清理文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


    def _find_nested_tars_in_directory(self, directory_path: str) -> List[str]:
        """
        递归查找目录中的所有tar文件
        """
        tar_files = []

        if not directory_path:
            return tar_files

        try:
            directory_path = directory_path.replace('/', '\\')

            # 检查目录是否存在
            if not self._check_directory_exists(directory_path):
                return tar_files

            find_cmd = f'dir "{directory_path}\\*.tar" /S /B'
            stdout, _ = self.execute_command(find_cmd)

            if stdout.strip():
                files = [f.strip() for f in stdout.strip().splitlines() if f.strip()]
                for file in files:
                    if file.lower().endswith('.tar'):
                        if file not in tar_files:
                            tar_files.append(file)
                            print(f"      📦 递归找到tar文件: {os.path.basename(file)}")

            # 手动递归查找
            list_cmd = f'dir "{directory_path}" /B'
            stdout, _ = self.execute_command(list_cmd)

            if stdout.strip():
                items = [item.strip() for item in stdout.strip().splitlines() if item.strip()]

                for item in items:
                    item_path = os.path.join(directory_path, item)
                    item_path = item_path.replace('/', '\\')

                    if item.lower().endswith('.tar'):
                        if item_path not in tar_files:
                            tar_files.append(item_path)
                            print(f"      📦 找到tar文件: {item}")

                    elif self._is_directory(item_path):
                        if 'sysdisk0' not in item.lower():
                            sub_tar_files = self._find_nested_tars_in_directory(item_path)
                            for sub_file in sub_tar_files:
                                if sub_file not in tar_files:
                                    tar_files.append(sub_file)

        except Exception as e:
            print(f"⚠️ 查找嵌套tar文件失败 {directory_path}: {str(e)}")

        return tar_files

    def _collect_all_files(self, base_path: str, file_list: list, current_depth: int = 0, max_depth: int = 3,
                           current_rel_path: str = ""):
        """
        递归收集目录中的所有文件
        """
        if current_depth >= max_depth:
            return

        try:
            # 列出当前目录
            list_cmd = f'dir "{base_path}" /B'
            stdout, _ = self.execute_command(list_cmd)

            if stdout.strip():
                files = [f.strip() for f in stdout.strip().splitlines() if f.strip()]

                for file in files:
                    # 构建相对路径
                    if current_rel_path:
                        rel_path = os.path.join(current_rel_path, file)
                    else:
                        rel_path = file

                    # 添加到文件列表
                    file_list.append(rel_path)

                    # 检查是否是目录
                    file_path = os.path.join(base_path, file)
                    if self._is_directory(file_path):
                        # 递归收集子目录
                        self._collect_all_files(file_path, file_list, current_depth + 1, max_depth, rel_path)

        except Exception as e:
            print(f"⚠️ 收集文件失败 {base_path}: {str(e)}")

    def _recursive_list_directory(self, path: str, max_depth: int = 3, current_depth: int = 0,
                                  current_rel_path: str = "") -> List[str]:
        """
        递归列出目录中的所有文件和子目录
        """
        if current_depth >= max_depth:
            return []

        all_files = []

        try:
            # 列出当前目录
            list_cmd = f'dir "{path}" /B'
            stdout, _ = self.execute_command(list_cmd)

            if stdout.strip():
                files = [f.strip() for f in stdout.strip().splitlines() if f.strip()]

                for file in files:
                    # 构建相对路径
                    if current_rel_path:
                        rel_path = os.path.join(current_rel_path, file)
                    else:
                        rel_path = file

                    all_files.append(rel_path)

                    # 检查是否是目录
                    file_path = os.path.join(path, file)
                    if self._is_directory(file_path):
                        # 递归列出子目录
                        sub_files = self._recursive_list_directory(
                            file_path,
                            max_depth,
                            current_depth + 1,
                            rel_path
                        )
                        all_files.extend(sub_files)

            return all_files

        except Exception as e:
            print(f"⚠️ 递归列出目录失败 {path}: {str(e)}")
            return []

    def _find_kpi_in_home_directory(self, home_path: str) -> List[str]:
        """
        只查找 home/log/DRVFMAGENT 目录 kpi日志
        """

        kpi_logs = []

        home_path = home_path.replace('/', '\\')

        if home_path.endswith('\\home'):
            home_path = home_path[:-5]  # 移除末尾的 \home
        elif home_path.endswith('home'):
            home_path = home_path[:-4]  # 移除末尾的 home

        print(f"🔍 在home目录中查找kpi日志: {home_path}")

        # 首先检查home目录是否存在
        if not self._check_directory_exists(home_path):
            print(f"❌ home目录不存在: {home_path}")
            return kpi_logs

        # 只查找特定的 DRVFMAGENT 目录路径
        drvfmagent_path = os.path.join(home_path, "log", "DRVFMAGENT")
        drvfmagent_path = drvfmagent_path.replace('/', '\\')

        print(f"🔍 查找标准路径: {drvfmagent_path}")

        # 检查标准路径是否存在
        if not self._check_directory_exists(drvfmagent_path):
            print(f"❌ DRVFMAGENT目录不存在: {drvfmagent_path}")

            # 尝试直接在当前目录下查找
            alt_drvfmagent_path = os.path.join(home_path, "DRVFMAGENT")
            if self._check_directory_exists(alt_drvfmagent_path):
                drvfmagent_path = alt_drvfmagent_path
                print(f"✅ 找到替代DRVFMAGENT目录: {drvfmagent_path}")
            else:
                return kpi_logs

        print(f"✅ 找到DRVFMAGENT目录: {drvfmagent_path}")

        # 在DRVFMAGENT目录中查找kpi文件
        print(f"🔍 在DRVFMAGENT目录中查找kpi文件: {drvfmagent_path}")

        kpi_cmd = f'dir "{drvfmagent_path}\\kpi_*.log" /B'
        kpi_stdout, _ = self.execute_command(kpi_cmd)

        if kpi_stdout.strip():
            files = [f.strip() for f in kpi_stdout.strip().splitlines() if f.strip()]
            for file in files:
                if file:
                    if re.match(r'^kpi_\d+_\d+\.log$', file, re.IGNORECASE):
                        full_path = os.path.join(drvfmagent_path, file)
                        kpi_logs.append(full_path)
                        print(f"✅ 找到标准kpi文件: {full_path}")
                    else:
                        print(f"⚠️ 忽略非标准文件: {file}")
        else:
            print(f"📭 DRVFMAGENT目录中没有kpi_*.log文件")

            list_cmd = f'dir "{drvfmagent_path}" /B'
            list_stdout, _ = self.execute_command(list_cmd)

            if list_stdout.strip():
                files = [f.strip() for f in list_stdout.strip().splitlines() if f.strip()]
                print(f"📋 DRVFMAGENT目录文件列表 (共{len(files)}个):")
                for i, file in enumerate(files[:10]):  # 显示前10个
                    print(f"  {i + 1}. {file}")
                if len(files) > 10:
                    print(f"  ... 还有 {len(files) - 10} 个文件")

        print(f"📊 在home目录中找到 {len(kpi_logs)} 个kpi日志文件")
        return kpi_logs

    def _clean_and_create_dir(self, path: str) -> bool:
        """清理并创建目录，但不清空extract_base_path目录本身"""
        import os

        # 检查是否是extract_base_path本身
        base_path = os.path.dirname(path)

        # 清理目录（只清空当前目录，不递归删除父目录）
        cleanup_cmd = f'if exist "{path}\\" (rmdir /S /Q "{path}" 2>nul && mkdir "{path}" 2>nul) else (mkdir "{path}" 2>nul)'
        stdout, stderr = self.execute_command(cleanup_cmd)

        # 检查目录
        check_cmd = f'if exist "{path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
        stdout, _ = self.execute_command(check_cmd)

        if "EXISTS" in stdout:
            print(f"📁 目录准备就绪: {path}")
            return True
        else:
            print(f"❌ 目录创建失败: {path}")
            return False

    def _extract_tar_file(self, tar_path: str, extract_path: str) -> bool:
        """
        解压tar文件 多种解压方式
        """
        print(f"🔄 解压命令: tar -xf \"{tar_path}\" -C \"{extract_path}\"")

        # 规范化路径
        tar_path = tar_path.replace('/', '\\')
        extract_path = extract_path.replace('/', '\\')

        # 确保解压目录存在
        mkdir_cmd = f'mkdir "{extract_path}" 2>nul'
        self.execute_command(mkdir_cmd)

        # 1: 尝试tar命令
        tar_cmd = f'tar -xf "{tar_path}" -C "{extract_path}" 2>&1'
        stdout, stderr = self.execute_command(tar_cmd)

        # 检查是否解压成功
        check_cmd = f'dir "{extract_path}" /B'
        stdout_check, _ = self.execute_command(check_cmd)

        if stdout_check.strip():
            file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
            print(f"✅ tar命令解压成功，解压出 {file_count} 个文件/目录")
            return True

        # 2: 尝试7z命令
        print(f"🔄 tar命令失败，尝试7z解压...")

        seven_zip_paths = [
            r'"C:\Program Files\7-Zip\7z.exe"',
            r'"C:\Program Files (x86)\7-Zip\7z.exe"',
            '7z.exe',
            '7z'
        ]

        for seven_zip_path in seven_zip_paths:
            print(f"🔄 尝试7z路径: {seven_zip_path}")

            # 检查7z程序是否存在
            if seven_zip_path not in ['7z.exe', '7z']:
                check_exe_cmd = f'if exist {seven_zip_path} (echo EXISTS) else (echo NOT_EXISTS)'
                check_exe_stdout, _ = self.execute_command(check_exe_cmd)
                if "NOT_EXISTS" in check_exe_stdout:
                    continue

            extract_path_7z = extract_path.replace('\\', '\\\\')
            tar_cmd_7z = f'{seven_zip_path} x "{tar_path}" -o"{extract_path}" -y 2>&1'
            print(f"📄 执行命令: {tar_cmd_7z}")

            stdout_7z, stderr_7z = self.execute_command(tar_cmd_7z)

            stdout_check, _ = self.execute_command(check_cmd)

            if stdout_check.strip():
                file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
                print(f"✅ 7z解压成功，解压出 {file_count} 个文件/目录")
                return True
            else:
                print(f"❌ 7z解压失败，输出: {stdout_7z[:200] if stdout_7z else '空'}")

        # 3: 尝试使用copy + 重命名的方式处理特殊情况
        print(f"🔄 尝试使用copy命令处理...")
        tar_filename = os.path.basename(tar_path)
        temp_tar_path = os.path.join(os.path.dirname(extract_path), f"temp_{tar_filename}")

        # 复制文件到解压目录并重命名为.tar扩展名
        copy_cmd = f'copy "{tar_path}" "{temp_tar_path}" 2>nul'
        self.execute_command(copy_cmd)

        # 尝试解压重命名后的文件
        tar_cmd_retry = f'tar -xf "{temp_tar_path}" -C "{extract_path}" 2>&1'
        stdout, stderr = self.execute_command(tar_cmd_retry)

        # 检查是否解压成功
        stdout_check, _ = self.execute_command(check_cmd)

        if stdout_check.strip():
            file_count = len([line.strip() for line in stdout_check.strip().splitlines() if line.strip()])
            print(f"✅ 通过copy重命名解压成功，解压出 {file_count} 个文件/目录")

            # 清理临时文件
            del_cmd = f'del "{temp_tar_path}" 2>nul'
            self.execute_command(del_cmd)
            return True
        else:
            # 清理临时文件
            del_cmd = f'del "{temp_tar_path}" 2>nul'
            self.execute_command(del_cmd)

        print(f"❌ 所有解压方式都失败")
        return False

    def _upload_directory(self, local_dir: str, remote_dir: str):
        """上传目录到Windows服务器"""

        for root, dirs, files in os.walk(local_dir):
            for dir_name in dirs:
                local_dir_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(local_dir_path, local_dir)
                remote_dir_path = os.path.join(remote_dir, rel_path.replace('/', '\\'))

                # 创建远程目录
                mkdir_cmd = f'mkdir "{remote_dir_path}" 2>nul'
                self.execute_command(mkdir_cmd)

            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(local_file_path, local_dir)
                remote_file_path = os.path.join(remote_dir, rel_path.replace('/', '\\'))

                # 确保远程目录存在
                remote_file_dir = os.path.dirname(remote_file_path)
                mkdir_cmd = f'mkdir "{remote_file_dir}" 2>nul'
                self.execute_command(mkdir_cmd)

                # 上传文件
                try:
                    self.sftp_client.put(local_file_path, remote_file_path)
                except Exception as e:
                    print(f"⚠️ 上传文件失败 {file_name}: {e}")

    def _list_directory(self, path: str) -> List[str]:
        """列出目录内容，返回相对路径"""
        path = path.replace('/', '\\')
        list_cmd = f'dir "{path}" /B'
        stdout, _ = self.execute_command(list_cmd)

        if stdout.strip():
            files = []
            for line in stdout.strip().splitlines():
                file = line.strip()
                if file:
                    files.append(file)
            return files
        return []

    def _is_directory(self, path: str) -> bool:
        """检查是否为目录"""
        try:
            path = path.replace('/', '\\')
            # 移除可能的尾随空格
            path = path.strip()

            # 检查路径是否以反斜杠结尾
            if not path.endswith('\\'):
                check_path = path + '\\'
            else:
                check_path = path

            check_cmd = f'if exist "{check_path}" (echo IS_DIR) else (echo NOT_DIR)'
            stdout, _ = self.execute_command(check_cmd)

            # 清理输出，只检查关键词
            stdout = stdout.strip().upper()
            return "IS_DIR" in stdout
        except Exception as e:
            print(f"⚠️ 检查目录失败 {path}: {str(e)}")
            return False

    def _check_directory_exists(self, path: str) -> bool:
        """检查目录是否存在 - 修复路径重复问题"""
        path = path.replace('/', '\\')

        # 移除路径中的重复部分
        parts = path.split('\\')
        unique_parts = []
        seen = set()

        for part in parts:
            if part and part not in seen:
                unique_parts.append(part)
                seen.add(part)
            elif part and part in seen:
                # 跳过重复的目录名
                print(f"⚠️ 检测到重复路径部分: {part}")
                continue

        clean_path = '\\'.join(unique_parts)

        if clean_path != path:
            print(f"🔄 清理重复路径: {path} -> {clean_path}")
            path = clean_path

        check_cmd = f'if exist "{path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
        stdout, _ = self.execute_command(check_cmd)
        result = "EXISTS" in stdout
        return result


    def _find_kpi_in_drvfmagent(self, extract_path: str) -> List[str]:
        """
        在extract_path中查找home/log/DRVFMAGENT/kpi_数字_数字.log文件
        """
        kpi_logs = []

        # 构建DRVFMAGENT目录路径
        drvfmagent_path = os.path.join(extract_path, "home", "log", "DRVFMAGENT")
        drvfmagent_path = drvfmagent_path.replace('/', '\\')

        print(f"🔍 查找kpi文件: {drvfmagent_path}")

        # 检查目录是否存在
        check_cmd = f'if exist "{drvfmagent_path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
        check_stdout, _ = self.execute_command(check_cmd)

        if "EXISTS" not in check_stdout:
            print(f"❌ DRVFMAGENT目录不存在")

            # 列出home目录结构，帮助调试
            home_path = os.path.join(extract_path, "home")
            home_path = home_path.replace('/', '\\')

            print(f"📋 检查home目录结构:")
            check_home_cmd = f'dir "{home_path}" /S /B | findstr /i "log"'
            home_stdout, _ = self.execute_command(check_home_cmd)

            if home_stdout.strip():
                print(f"🔍 home目录下的log相关路径:")
                paths = home_stdout.strip().split('\n')[:10]  # 只显示前10个
                for i, path in enumerate(paths):
                    print(f"  {i + 1}. {path}")
            else:
                print(f"  📭 home目录下未找到log相关目录")

            return kpi_logs

        # 查找kpi_数字_数字.log文件
        kpi_cmd = f'dir "{drvfmagent_path}\\kpi_*.log" /B'
        kpi_stdout, _ = self.execute_command(kpi_cmd)

        if kpi_stdout.strip():
            files = kpi_stdout.strip().split('\n')
            for file in files:
                if file.strip():
                    # 验证文件名格式
                    if re.match(r'^kpi_\d+_\d+\.log$', file.strip(), re.IGNORECASE):
                        full_path = os.path.join(drvfmagent_path, file.strip())
                        kpi_logs.append(full_path)
                        print(f"✅ 找到标准kpi文件: {full_path}")
                    else:
                        print(f"⚠️ 忽略非标准文件: {file.strip()}")
        else:
            print(f"📋 DRVFMAGENT目录文件列表:")
            list_cmd = f'dir "{drvfmagent_path}" /B'
            list_stdout, _ = self.execute_command(list_cmd)

            if list_stdout.strip():
                files = list_stdout.strip().split('\n')
                for file in files:
                    print(f"  - {file}")

                    # 检查是否有其他可能的kpi文件
                    if 'kpi' in file.lower() and file.lower().endswith('.log'):
                        print(f"    ⚠️ 发现非标准kpi文件: {file}")
            else:
                print(f"  📭 目录为空")

        print(f"📊 找到 {len(kpi_logs)} 个kpi日志文件")
        return kpi_logs

    def _recursive_find_kpi_windows(self, search_path: str, max_depth: int = 3, current_depth: int = 0) -> List[str]:
        """
        递归查找kpi日志 查找DRVFMAGENT目录
        """
        if current_depth >= max_depth:
            return []

        kpi_logs = []

        try:
            # 如果已经到达home/log/DRVFMAGENT目录，直接查找kpi文件
            if "DRVFMAGENT" in search_path.upper() and "LOG" in search_path.upper() and "HOME" in search_path.upper():
                # 查找kpi_*.log文件
                find_cmd = f'dir "{search_path}\\kpi_*.log" /B'
                stdout, _ = self.execute_command(find_cmd)

                if stdout.strip():
                    files = stdout.strip().split('\n')
                    for file in files:
                        if file.strip():
                            # 验证格式
                            if re.match(r'^kpi_\d+_\d+\.log$', file.strip(), re.IGNORECASE):
                                full_path = os.path.join(search_path, file.strip())
                                kpi_logs.append(full_path)
                                print(f"✅ 在DRVFMAGENT找到kpi文件: {full_path}")
                return kpi_logs

            # 如果不是DRVFMAGENT目录，继续搜索
            list_cmd = f'dir "{search_path}" /B'
            stdout, _ = self.execute_command(list_cmd)

            if not stdout.strip():
                return []

            items = stdout.strip().split('\n')

            for item in items:
                item = item.strip()
                if not item:
                    continue

                item_path = os.path.join(search_path, item)

                # 检查是否是目录
                dir_check_cmd = f'if exist "{item_path}\\" (echo IS_DIR) else (echo NOT_DIR)'
                stdout_dir, _ = self.execute_command(dir_check_cmd)

                if "IS_DIR" in stdout_dir:
                    # 如果是home目录，优先搜索
                    if "home" in item.lower():
                        # 直接构建home/log/DRVFMAGENT路径
                        drvfmagent_path = os.path.join(search_path, "home", "log", "DRVFMAGENT")

                        # 检查DRVFMAGENT是否存在
                        check_cmd = f'if exist "{drvfmagent_path}\\" (echo EXISTS) else (echo NOT_EXISTS)'
                        check_stdout, _ = self.execute_command(check_cmd)

                        if "EXISTS" in check_stdout:
                            # 在DRVFMAGENT中查找kpi文件
                            sub_kpi_logs = self._recursive_find_kpi_windows(drvfmagent_path, max_depth,
                                                                            current_depth + 1)
                            if sub_kpi_logs:
                                kpi_logs.extend(sub_kpi_logs)
                                return kpi_logs

                    # 继续递归搜索
                    sub_kpi_logs = self._recursive_find_kpi_windows(item_path, max_depth, current_depth + 1)
                    kpi_logs.extend(sub_kpi_logs)

        except Exception as e:
            print(f"⚠️ 递归查找失败 {search_path}: {str(e)}")

        return kpi_logs

@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: Optional[int]
    success: bool
    raw_output: str = ""

    def __str__(self):
        return (
            f"Command: {self.command}\n"
            f"Exit Code: {self.exit_code}\n"
            f"Success: {self.success}\n"
            f"Stdout:\n{self.stdout}\n"
            f"Stderr:\n{self.stderr}\n"
            f"Raw Output:\n{self.raw_output}"
        )


@dataclass
class Command:
    command: str

    # 成功/失败判定
    success_marker: Union[str, Pattern] = "#"
    failure_marker: Union[str, Pattern] = "Error"

    # 超时控制
    single_wait_timeout: int = 10  # 单次命令执行后最多等待多久（秒）
    total_poll_timeout: Optional[int] = None  # 轮询总超时（秒），None 表示不轮询

    # 轮询控制
    poll_interval: int = 30  # 轮询间隔（仅当 total_poll_timeout is not None 时生效）

    @property
    def is_polling_command(self) -> bool:
        return self.total_poll_timeout is not None and self.total_poll_timeout > 0

    def matches_success(self, output: str) -> bool:
        if isinstance(self.success_marker, str):
            return self.success_marker in output
        else:
            return bool(self.success_marker.search(output))

    def matches_failure(self, output: str) -> bool:
        if isinstance(self.failure_marker, str):
            return self.failure_marker in output
        else:
            return bool(self.failure_marker.search(output))


class JumpSSHClient:
    def __init__(
            self,
            jump_host: str,
            jump_user: str,
            jump_password: str,
            timeout: int = 10
    ):
        self.jump_host = jump_host
        self.jump_user = jump_user
        self.jump_password = jump_password
        self.timeout = timeout
        self.ssh_jump = None
        self.transport = None

    def connect_jump(self):
        print(f"正在连接跳板机: {self.jump_user}@{self.jump_host}")
        self.ssh_jump = paramiko.SSHClient()
        self.ssh_jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_jump.connect(
                hostname=self.jump_host,
                username=self.jump_user,
                password=self.jump_password,
                port=22,
                timeout=self.timeout
            )
            self.transport = self.ssh_jump.get_transport()
            if not self.transport.is_active():
                raise ConnectionError("跳板机 Transport 未激活")
            print("✅ 跳板机连接成功")
        except Exception as e:
            print(f"❌ 跳板机连接失败: {e}")
            raise

    def close(self):
        if self.ssh_jump:
            self.ssh_jump.close()
            print("跳板机连接已关闭")

    def __enter__(self):
        self.connect_jump()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def exec_on_jump(
            self,
            command: str,
            validator: Optional[Callable[[CommandResult], bool]] = None
    ) -> CommandResult:
        print(f"在跳板机执行命令: {command}")
        stdin, stdout, stderr = self.ssh_jump.exec_command(command, timeout=self.timeout)

        try:
            exit_code = stdout.channel.recv_exit_status()
        except Exception:
            exit_code = None

        stdout_str = stdout.read().decode('utf-8', errors='ignore')
        stderr_str = stderr.read().decode('utf-8', errors='ignore')

        temp_result = CommandResult(
            command=command,
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=exit_code,
            success=False
        )

        success = validator(temp_result) if validator else (exit_code == 0)

        result = CommandResult(
            command=command,
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=exit_code,
            success=success
        )

        if success:
            print(f"命令执行成功: {command}")
        else:
            print(f"命令执行失败: {command}")
            print(f"详细结果:\n{result}")

        return result

    def ssh_to_target(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            target_port: int = 22,
            shell_prompt: str = "#",
            validator: Optional[Callable[[CommandResult], bool]] = None
    ) -> Tuple[Union[None, paramiko.Channel], CommandResult]:
        ssh_cmd = f"ssh -o StrictHostKeyChecking=no -p {target_port} {target_user}@{target_host}"
        print(f"通过跳板机执行 SSH: {ssh_cmd}")

        def default_ssh_validator(res: CommandResult) -> bool:
            return shell_prompt in res.raw_output

        use_validator = validator or default_ssh_validator

        channel = self.transport.open_session()
        channel.get_pty()
        channel.exec_command(ssh_cmd)

        output = ""
        start_time = time.time()
        password_sent = False
        prompt_patterns = [r"[Pp]assword:?"]

        while True:
            if channel.recv_ready():
                chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                output += chunk
                print(f"SSH 输出片段: {repr(chunk)}")

                if not password_sent:
                    for pattern in prompt_patterns:
                        if re.search(pattern, chunk):
                            print("检测到密码提示，发送目标设备密码...")
                            channel.send(target_password + "\n")
                            password_sent = True
                            time.sleep(1)
                            break

            if shell_prompt in output:
                break

            if time.time() - start_time > self.timeout + 5:
                print("SSH 登录超时")
                break

            time.sleep(0.2)

        temp_result = CommandResult(
            command=ssh_cmd,
            stdout=output,
            stderr="",
            exit_code=None,
            success=False,
            raw_output=output
        )
        success = use_validator(temp_result)

        result = CommandResult(
            command=ssh_cmd,
            stdout=output,
            stderr="",
            exit_code=None,
            success=success,
            raw_output=output
        )

        if success:
            print("✅ 目标设备 SSH 登录成功")
            return channel, result
        else:
            print("❌ 目标设备 SSH 登录失败")
            channel.close()
            return None, result

    def exec_commands_on_target(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            commands: List[Command],
            target_port: int = 22,
            login_timeout: int = 15,
            default_completion: str = "#"
    ) -> Generator[CommandResult, None, None]:
        print(f"准备在目标设备 {target_user}@{target_host} 上执行 {len(commands)} 条命令")

        original_timeout = getattr(self, 'timeout', login_timeout)
        self.timeout = login_timeout

        try:
            with self.interactive_ssh_to_target(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    target_port=target_port,
                    shell_prompt=default_completion
            ) as (channel, login_result):

                if not (channel and login_result.success):
                    print("❌ SSH 登录失败")
                    yield CommandResult(
                        command="",
                        stdout="",
                        stderr="Login failed",
                        exit_code=None,
                        success=False
                    )
                    return

                time.sleep(0.3)
                while channel.recv_ready():
                    channel.recv(4096)

                for i, cmd in enumerate(commands, 1):
                    if not cmd.is_polling_command:
                        # ── 普通命令 ───────────────────────
                        print(f"执行普通命令 [{i}]: {cmd.command}")
                        channel.send(cmd.command.rstrip() + "\n")

                        output = ""
                        start = time.time()
                        success = False

                        while True:
                            if channel.recv_ready():
                                chunk = channel.recv(4096).decode('utf-8', errors='ignore')
                                output += chunk

                            if cmd.matches_failure(output):
                                break
                            if cmd.matches_success(output):
                                success = True
                                break
                            if time.time() - start > cmd.single_wait_timeout:
                                print(f"普通命令 [{i}] 超时 ({cmd.single_wait_timeout}s)")
                                break
                            time.sleep(0.2)

                        yield CommandResult(
                            command=cmd.command,
                            stdout=output,
                            stderr="",
                            exit_code=0 if success else 1,
                            success=success,
                            raw_output=output
                        )

                        if not success:
                            print(f"❌ 普通命令 [{i}] 失败，终止后续命令")
                            break

                    else:
                        # ── 轮询命令 ───────────────────────
                        total_timeout = cmd.total_poll_timeout
                        interval = cmd.poll_interval
                        single_timeout = cmd.single_wait_timeout

                        print(f"启动轮询命令 [{i}]: '{cmd.command}' "
                                    f"(总超时={total_timeout}s, 间隔={interval}s)")

                        poll_start = time.time()
                        attempt = 0
                        final_success = False

                        while True:
                            elapsed_total = time.time() - poll_start
                            if elapsed_total > total_timeout:
                                print(f"轮询命令 [{i}] 总超时 ({total_timeout}s)")
                                break

                            attempt += 1
                            if attempt > 1:
                                # 计算还需等待多久
                                wait_time = min(interval, int(total_timeout - elapsed_total))
                                if wait_time > 0:
                                    time.sleep(wait_time)

                            channel.send(cmd.command.rstrip() + "\n")

                            output = ""
                            read_start = time.time()
                            while True:
                                if channel.recv_ready():
                                    chunk = channel.recv(4096).decode('utf-8', errors='ignore')
                                    output += chunk

                                if cmd.matches_failure(output):
                                    final_success = False
                                    break
                                if cmd.matches_success(output):
                                    final_success = True
                                    break
                                if time.time() - read_start > single_timeout:
                                    break  # 单次读取超时，进入下一轮
                                time.sleep(0.2)

                            # Yield 当前轮询结果
                            yield CommandResult(
                                command=f"{cmd.command} (poll #{attempt})",
                                stdout=output,
                                stderr="",
                                exit_code=0 if final_success else 1,
                                success=final_success,
                                raw_output=output
                            )

                            if final_success:
                                print(f"✅ 轮询命令 [{i}] 第 {attempt} 次成功")
                                break

                            if cmd.matches_failure(output):
                                print(f"轮询命令 [{i}] 检测到失败标志，提前终止")
                                break

                        if not final_success:
                            print(f"❌ 轮询命令 [{i}] 最终失败，终止后续命令")
                            break

        finally:
            self.timeout = original_timeout

    def generate_log_file(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            shelf_number: int,
            slot_number: int,
            today_only: bool = True,
            target_port: int = 22,
            default_completion: str = "#"
    ) -> bool:

        if today_only:
            reap_command = f"reap-log {shelf_number} {slot_number} date-start today"
        else:
            reap_command = f"reap-log {shelf_number} {slot_number}"

        # 构建命令序列
        commands = [
            # 进入配置模式
            Command(
                command="con t",
                success_marker="ZXPOTN(config)#",
                failure_marker="Error",
                single_wait_timeout=15
            ),
            # 进入 OTN 模式
            Command(
                command="otn",
                success_marker="ZXPOTN(config-otn)#",
                failure_marker="Error",
                single_wait_timeout=15
            ),
            # 触发日志收集
            Command(
                command=reap_command,
                success_marker="ZXPOTN(config-otn)#",  # 假设命令执行后返回 prompt
                failure_marker="Error",
                single_wait_timeout=20  # reap 可能稍慢
            )
        ]

        print(f"开始执行日志生成流程: {reap_command}")

        try:
            results = self.exec_commands_on_target(
                target_host=target_host,
                target_user=target_user,
                target_password=target_password,
                target_port=target_port,
                default_completion=default_completion,
                commands=commands
            )

            for result in results:
                if not result.success:
                    print(f"❌ 命令执行失败: {result.command}")
                    return False

            print("✅ 日志文件已成功生成并确认就绪")
            return True

        except Exception as e:
            print(f"执行日志生成时发生异常: {e}")
            return False

    def wait_for_file_generation(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            file_pattern: str,
            download_dir: str = "/logtar",
            check_interval: int = 30,
            timeout: int = 480,
            target_port: int = 22,
            default_completion: str = "#"
    ) -> Tuple[bool, str]:
        """
        等待文件生成
        """
        print(f"开始等待文件生成，文件模式: {file_pattern}，超时: {timeout}秒，检查间隔: {check_interval}秒")

        regex_pattern = file_pattern.replace('*', '.*')
        compiled_pattern = re.compile(regex_pattern)

        print(f"构建的正则表达式: {compiled_pattern.pattern}")

        start_time = time.time()
        attempt_count = 0

        try:
            with self.interactive_ssh_to_target(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    target_port=target_port,
                    shell_prompt=default_completion
            ) as (channel, login_result):

                if not login_result.success:
                    print("无法登录目标设备检查文件")
                    return False, ""

                while time.time() - start_time < timeout:
                    attempt_count += 1
                    elapsed = int(time.time() - start_time)
                    print(f"第 {attempt_count} 次检查文件 (已等待 {elapsed}秒)...")

                    try:
                        time.sleep(0.5)
                        while channel.recv_ready():
                            channel.recv(4096)

                        check_command = f"dir /sysdisk0{download_dir}"
                        print(f"执行检查命令: {check_command}")

                        channel.send(check_command + "\n")
                        time.sleep(3)

                        output = ""
                        check_start_time = time.time()

                        while time.time() - check_start_time < 25:
                            if channel.recv_ready():
                                chunk = channel.recv(16384).decode('utf-8', errors='ignore')
                                output += chunk

                            if default_completion in output:
                                break

                            time.sleep(0.5)

                        print(f"获取到检查输出，长度: {len(output)} 字符")

                        tar_filename = self._parse_dir_output_for_tar_enhanced(output, compiled_pattern,
                                                                               default_completion)

                        if tar_filename:
                            if self._is_valid_target_filename(tar_filename, file_pattern):
                                print(f"✅ 找到目标文件: {tar_filename}")
                                return True, tar_filename
                            else:
                                print(f"找到的文件名不符合要求: {tar_filename}，继续等待...")

                        remaining = timeout - (time.time() - start_time)
                        if remaining <= 0:
                            break

                        wait_time = min(check_interval, remaining)
                        if wait_time > 0:
                            print(f"文件尚未生成，{wait_time}秒后再次检查...")
                            time.sleep(wait_time)

                    except Exception as e:
                        print(f"第 {attempt_count} 次检查文件时发生异常: {e}")
                        if time.time() - start_time < timeout:
                            time.sleep(min(check_interval, timeout - (time.time() - start_time)))

        except Exception as e:
            print(f"SSH连接异常: {e}")
            return False, ""

        print(f"经过 {attempt_count} 次检查，未找到匹配的文件")
        return False, ""

    def _is_valid_target_filename(self, filename: str, original_pattern: str) -> bool:
        """验证找到的文件名是否是真正的目标文件"""
        if not filename:
            return False

        if not filename.endswith('.tar'):
            return False

        if not ('log_' in filename or 'log' in filename and filename.find('log') > 0):
            return False

        return True

    def get_log_file_name(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            file_pattern: Pattern[str],
            download_dir: str = "/logtar",
            check_interval: int = 30,
            timeout: int = 480,
            target_port: int = 22,
            default_completion: str = "#"
    ) -> Tuple[bool, str]:
        """
        获取日志文件名
        """
        # 将 Pattern 转换为字符串模式用于等待函数
        # pattern_str = file_pattern.pattern.replace(r'\(', '').replace(r'\)', '').replace(r'\.', '.').replace(r'\d+',
        #                                                                                                      '.*')
        pattern_str = file_pattern.patter

        found, tar_filename = self.wait_for_file_generation(
            target_host=target_host,
            target_user=target_user,
            target_password=target_password,
            file_pattern=pattern_str,
            download_dir=download_dir,
            check_interval=check_interval,
            timeout=timeout,
            target_port=target_port,
            default_completion=default_completion
        )

        if found and tar_filename:
            return True, tar_filename
        else:
            return False, ""

    def get_remote_file_size(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            target_port: int = 22,
            default_completion: str = "#"
    ) -> int:
        """
        获取远程文件大小（字节）
        """
        try:
            filename = os.path.basename(remote_path)

            dir_command = f"dir /sysdisk0/logtar"

            commands = [
                Command(
                    command=dir_command,
                    success_marker=default_completion,
                    failure_marker="Error",
                    single_wait_timeout=15
                )
            ]

            print(f"获取文件大小: {remote_path}")

            results = list(self.exec_commands_on_target(
                target_host=target_host,
                target_user=target_user,
                target_password=target_password,
                target_port=target_port,
                default_completion=default_completion,
                commands=commands
            ))

            if not results or not results[0].success:
                print("获取目录列表失败")
                return -1

            output = results[0].raw_output
            file_size = self._parse_file_size_from_dir(output, filename)

            if file_size > 0:
                print(f"文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")
                return file_size
            else:
                print("无法从目录输出中解析文件大小")
                return -1

        except Exception as e:
            print(f"获取文件大小时出错: {e}")
            return -1

    def _parse_file_size_from_dir(self, output: str, filename: str) -> int:
        """
        从 dir 命令输出中解析特定文件的大小
        """
        print(f"开始解析文件大小，文件名: {filename}")

        cleaned_output = re.sub(r'\x1b\[[0-9;]*[mK]', '', output)
        cleaned_output = re.sub(r'\x1b\[\d+;\d+H', '', cleaned_output)  # 移除光标定位字符
        cleaned_output = re.sub(r'\r', '', cleaned_output)

        print(f"清理后的输出内容:\n{cleaned_output}")

        lines = cleaned_output.split('\n')
        print(f"共 {len(lines)} 行需要处理")

        filename_patterns = [filename]

        if filename.endswith('.tar'):
            base_name = filename[:-4]
            filename_patterns.append(base_name + '.ta')
            filename_patterns.append(base_name)

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            print(f"检查行 {i}: {repr(line)}")

            # 检查是否是文件行（包含----标记）
            if '----' in line and not any(keyword in line for keyword in ['<DIR>', 'attribute', 'Directory of']):
                print(f"找到文件行: {line}")

                size_match = re.search(r'(\d+)\s+\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}', line)
                if size_match:
                    file_size = int(size_match.group(1))
                    print(f"当前行包含大小: {file_size}")

                    current_filename_part = self._extract_filename_part_from_file_line(line)
                    print(f"当前行文件名部分: {repr(current_filename_part)}")

                    for pattern in filename_patterns:
                        if pattern in current_filename_part:
                            print(f"✅ 找到匹配文件，大小: {file_size}")
                            return file_size

                    # 如果当前行文件名不完整，检查下一行
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        original_next_line = lines[i + 1]
                        print(f"检查下一行: {repr(next_line)}")

                        if (original_next_line.startswith(
                                '                                                        ') and
                                next_line and
                                not any(keyword in next_line for keyword in
                                        ['<DIR>', '----', 'attribute', 'Directory of'])):

                            # 组合文件名
                            combined_filename = current_filename_part + next_line
                            print(f"组合文件名: {combined_filename}")

                            for pattern in filename_patterns:
                                if pattern in combined_filename:
                                    print(f"✅ 找到跨行匹配文件，大小: {file_size}")
                                    return file_size

            i += 1

        print(f"在所有行中未找到文件 {filename} 的大小信息")
        return -1

    def _extract_filename_part_from_file_line(self, line: str) -> str:
        """
        从文件行中提取文件名部分
        """
        filename_match = re.search(r'\d{2}:\d{2}\s+(.+)', line)
        if filename_match:
            filename_part = filename_match.group(1).strip()
            return filename_part

        parts = line.split()
        if len(parts) >= 6:
            filename_parts = parts[5:]
            return ' '.join(filename_parts)

        return ""

    def smart_download_file(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            local_path: str,
            target_port: int = 22,
            size_threshold_mb: int = 200,
            max_retries: int = 3,
            retry_delay: int = 5
    ) -> bool:
        """
        智能下载文件
        """
        print(f"开始智能下载: {remote_path} -> {local_path}")

        for attempt in range(max_retries):
            try:
                file_size = self.get_remote_file_size(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    remote_path=remote_path,
                    target_port=target_port
                )

                if file_size <= 0:
                    print("无法获取文件大小，使用分块下载作为备选")
                    return self.download_file_via_sftp_with_retry(
                        target_host=target_host,
                        target_user=target_user,
                        target_password=target_password,
                        remote_path=remote_path,
                        local_path=local_path,
                        target_port=target_port
                    )

                file_size_mb = file_size / 1024 / 1024
                print(f"文件大小: {file_size_mb:.2f} MB, 阈值: {size_threshold_mb} MB")

                # 根据文件大小选择下载方法
                if file_size_mb > size_threshold_mb:
                    print("文件较大，使用带断点续传的分块下载")
                    return self.download_file_via_sftp_with_retry(
                        target_host=target_host,
                        target_user=target_user,
                        target_password=target_password,
                        remote_path=remote_path,
                        local_path=local_path,
                        target_port=target_port
                    )
                else:
                    print("文件较小，使用简单下载方法")
                    return self.download_file_via_sftp(
                        target_host=target_host,
                        target_user=target_user,
                        target_password=target_password,
                        remote_path=remote_path,
                        local_path=local_path,
                        target_port=target_port
                    )

            except Exception as e:
                print(f"智能下载失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"{retry_delay}秒后重试...")
                    time.sleep(retry_delay)

        print(f"经过 {max_retries} 次尝试后下载仍然失败")
        return False

    def _parse_dir_output_for_tar_enhanced(self, output: str, file_pattern: Pattern[str], prompt: str) -> str:
        """
        dir 命令输出解析
        """
        print("开始解析 dir 命令输出")

        # 清理输出：移除 ANSI 转义字符
        cleaned_output = re.sub(r'\x1b\[[0-9;]*[mK]', '', output)
        cleaned_output = re.sub(r'\x1b\[\d+;\d+H', '', cleaned_output)  # 移除光标定位字符
        cleaned_output = re.sub(r'\r', '', cleaned_output)

        print(f"清理后的输出内容:\n{cleaned_output}")

        lines = cleaned_output.split('\n')
        print(f"共 {len(lines)} 行需要处理")

        tar_filenames = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # 跳过空行、提示行、目录头等
            if (not line.strip() or
                    prompt in line or
                    line.startswith('Directory of') or
                    line.strip().startswith('attribute') or
                    line.strip().startswith('dir /sysdisk0') or
                    'KB total' in line or
                    line.startswith('ZXPOTN#')):
                i += 1
                continue

            print(f"检查行 {i}: {repr(line)}")

            if '----' in line:
                filename, skip_lines = self._extract_tar_filename_with_multiline(line, lines, i)

                if filename:
                    print(f"找到跨行 tar 文件: {filename}")
                    tar_filenames.append(filename)
                    i += skip_lines
                    continue
                else:
                    filename = self._extract_tar_filename_from_file_line(line)
                    if filename:
                        print(f"在当前行找到 tar 文件: {filename}")
                        tar_filenames.append(filename)

            i += 1

        print(f"找到的所有 tar 文件名: {tar_filenames}")

        # 精确匹配模式
        for filename in tar_filenames:
            if file_pattern.search(filename):
                print(f"✅ 精确匹配到目标文件: {filename}")
                return filename

        print("在所有行中未找到匹配的 tar 文件名")
        return ""

    def _extract_tar_filename_with_multiline(self, current_line: str, all_lines: List[str], current_index: int) -> \
            Tuple[str, int]:
        """
        处理跨行文件名的情况
        """
        if current_index + 1 < len(all_lines):
            next_line = all_lines[current_index + 1].rstrip()

            if (next_line.startswith('                                                        ') and
                    next_line.strip() and
                    not any(keyword in next_line for keyword in ['<DIR>', '----', 'attribute', 'Directory of'])):

                current_filename_part = self._extract_filename_part(current_line)
                next_filename_part = next_line.strip()

                if current_filename_part and next_filename_part:
                    # 合并文件名
                    combined_filename = current_filename_part + next_filename_part
                    print(
                        f"合并跨行文件名: '{current_filename_part}' + '{next_filename_part}' = '{combined_filename}'")

                    if self._is_valid_combined_filename(combined_filename):
                        return combined_filename, 1

        return "", 0

    def _is_valid_combined_filename(self, filename: str) -> bool:
        """
        验证合并后的文件名是否有效  检查是否是有效的 tar 文件名
        """
        clean_filename = re.sub(r'\s+', '', filename)

        if (clean_filename.endswith('.tar') and
                ('log_' in clean_filename or re.search(r'\d+_\d+_log', clean_filename)) and
                re.match(r'\d+_\d+_log', clean_filename)):
            return True

        return False

    def _extract_filename_part(self, line: str) -> str:
        """
        从文件行中提取文件名部分
        """
        filename_match = re.search(r'\d{2}:\d{2}\s+(.+)', line)
        if filename_match:
            filename_part = filename_match.group(1).strip()
            return filename_part

        parts = line.split()
        if len(parts) >= 6:
            filename_parts = parts[5:]
            return ' '.join(filename_parts)

        return ""

    def _extract_tar_filename_from_file_line(self, line: str) -> str:
        """
        从文件行中提取 tar 文件名（只提取真正的 tar 文件）
        """
        line = re.sub(r'\x1b\[[0-9;]*[mK]', '', line)

        filename_part = self._extract_filename_part(line)
        if not filename_part:
            return ""

        clean_filename = re.sub(r'\s+', '', filename_part)

        # 检查是否是 tar 文件（支持 .tar 和跨行的 .ta + r 情况）
        if clean_filename.endswith('.tar'):
            if 'log_' in clean_filename or 'log' in clean_filename:
                return clean_filename
        elif clean_filename.endswith('.ta'):
            return ""

        if (('log_' in clean_filename or 'log' in clean_filename) and '.tar' in clean_filename) or \
                (('log_' in clean_filename or 'log' in clean_filename) and re.search(r'\d+_\d+_log', clean_filename)):
            return clean_filename

        return ""

    def download_file_with_progress(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            shelf_number: int,
            slot_number: int,
            today_only: bool = True,
            download_dir: str = "/logtar",
            local_dir: str = ".",
            check_interval: int = 30,
            timeout: int = 480,
            target_port: int = 22,
            default_completion: str = "#"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        全流程下载日志文件，带进度反馈。
        每个阶段通过 yield 返回状态字典，最终成功时包含 Markdown 下载链接。
        """

        def safe_abs_path(p: str) -> str:
            try:
                return os.path.abspath(p)
            except Exception:
                return p

        # === Step 1: 触发日志生成 ===
        print("开始触发日志文件生成...")
        yield {
            "status": "generating",
            "progress": 0,
            "message": "🚀 正在触发设备生成日志文件..."
        }

        success_gen = self.generate_log_file(
            target_host=target_host,
            target_user=target_user,
            target_password=target_password,
            target_port=target_port,
            default_completion=default_completion,
            shelf_number=shelf_number,
            slot_number=slot_number,
            today_only = today_only
        )

        if not success_gen:
            print("❌ 触发日志生成失败")
            yield {
                "status": "failed",
                "progress": 0,
                "message": "❌ 触发日志生成失败",
                "markdown": ""
            }
            return

        print("✅ 日志生成命令已成功下发")
        yield {
            "status": "generated",
            "progress": 5,
            "message": "✅ 日志生成命令已成功下发"
        }

        # === Step 2: 查找生成的日志文件 ===
        file_pattern = f"{shelf_number}_{slot_number}_log.*\\.tar"
        print(f"开始轮询查找文件")
        yield {
            "status": "searching",
            "progress": 5,
            "message": f"🔍 正在轮询查找日志文件（最长等待 {timeout} 秒）...",
            "details": {
                "pattern": file_pattern,
                "directory": download_dir,
                "timeout_sec": timeout
            }
        }

        found, tar_filename = self.wait_for_file_generation(
            target_host=target_host,
            target_user=target_user,
            target_password=target_password,
            file_pattern=file_pattern,
            download_dir=download_dir,
            check_interval=check_interval,
            timeout=timeout,
            target_port=target_port,
            default_completion=default_completion
        )

        if not found or not tar_filename:
            print("❌ 超时或未找到匹配的日志文件")
            yield {
                "status": "failed",
                "progress": 0,
                "message": "❌ 超时或未找到匹配的日志文件",
                "markdown": ""
            }
            return

        print("✅ 找到日志文件: {tar_filename}")
        yield {
            "status": "found",
            "progress": 30,
            "message": f"✅ 找到日志文件: {tar_filename}"
        }

        # === Step 3: 准备本地路径 ===
        remote_path = f"{download_dir}/{tar_filename}"
        local_path = os.path.abspath(os.path.join(local_dir, tar_filename))
        os.makedirs(local_dir, exist_ok=True)
        print(f"准备下载文件: {remote_path} -> {local_path}")
        yield {
            "status": "downloading",
            "progress": 30,
            "message": f"📥 开始下载文件: {tar_filename}"
        }

        # === Step 4: 带进度的下载 ===
        download_success = False
        try:
            download_success = self.smart_download_file(
                target_host=target_host,
                target_user=target_user,
                target_password=target_password,
                remote_path=remote_path,
                local_path=local_path,
                target_port=target_port
            )

            if download_success:
                yield {
                    "status": "success",
                    "progress": 100,
                    "message": "✅ 文件下载完成"
                }
            else:
                yield {
                    "status": "failed",
                    "progress": 30,
                    "message": "❌ 文件下载失败"
                }

        except Exception as e:
            print("下载过程中发生异常")
            yield {
                "status": "failed",
                "progress": 0,
                "message": f"❌ 下载异常: {str(e)}",
                "markdown": ""
            }
            return

        if not download_success:
            print("❌ 文件下载失败")
            yield {
                "status": "failed",
                "progress": 0,
                "message": "❌ 文件下载未成功完成",
                "markdown": ""
            }
            return

        # === Step 5: 成功完成，返回 Markdown 下载链接 ===
        yield {
            "status": "completed",
            "progress": 100,
            "message": "✅ 日志文件已成功下载",
            "filename": tar_filename,  # e.g., "device_1_41.tar"
            "dir_type": "在线诊断用户下载目录",  # 必须和 /download 路由中的 key 一致
            "local_path": local_path
        }

    def _parse_dir_output_for_tar(self, output: str, file_pattern: Pattern[str], prompt: str) -> str:
        """
        dir 命令输出解析
        """
        lines = output.split('\n')
        print(f"开始解析 {len(lines)} 行输出")

        # 使用正则表达式直接匹配文件名
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or prompt in line:
                continue

            print(f"检查行 {i}: {line}")

            match = file_pattern.search(line)
            if match:
                filename = match.group(1)
                if filename.endswith('.ta'):
                    filename = filename[:-3] + '.tar'
                print(f"✅ 通过正则匹配找到文件: {filename}")
                return filename
        print("在所有行中未找到匹配的文件名")
        return ""

    def verify_and_download_file_with_progress(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            local_path: str,
            target_port: int = 22,
            max_retries: int = 3,
            retry_delay: int = 5,
            base_progress: int = 30
    ) -> Generator[Dict[str, Any], None, bool]:
        """验证并下载文件，支持进度 yield"""

        for attempt in range(max_retries):
            yield {
                "status": "verifying",
                "progress": base_progress,
                "message": f"尝试验证远程文件是否存在 (第 {attempt + 1} 次)"
            }

            if not self.verify_remote_file_exists(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    remote_path=remote_path,
                    target_port=target_port
            ):
                yield {"status": "error", "message": f"远程文件不存在: {remote_path}"}
                return False

            # 执行带进度的 SFTP 下载
            download_success = self.smart_download_file(
                target_host=target_host,
                target_user=target_user,
                target_password=target_password,
                remote_path=remote_path,
                local_path=local_path,
                target_port=target_port
            )

            if download_success:
                yield {"status": "success", "message": "文件下载完成"}
                return True
            else:
                yield {
                    "status": "retrying",
                    "progress": base_progress,
                    "message": f"下载失败，{retry_delay}秒后重试..."
                }
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        print(f"经过 {max_retries} 次尝试后文件下载仍然失败")
        return False

    def download_file_via_sftp_with_progress_yield(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            local_path: str,
            target_port: int = 22,
            chunk_size: int = 1048576,
            max_retries: int = 5,
            retry_delay: int = 10,
            base_progress: int = 30
    ) -> Generator[Dict[str, Any], None, bool]:
        """带进度反馈的 SFTP 下载（使用 yield）"""

        temp_path = local_path + ".downloading"
        downloaded_size = 0
        remote_size = 0

        # 获取远程文件大小
        try:
            with self.sftp_to_target(target_host, target_user, target_password, target_port) as sftp:
                remote_size = sftp.stat(remote_path).st_size
            print(f"远程文件大小: {remote_size} 字节 ({remote_size / 1024 / 1024:.2f} MB)")
        except Exception as e:
            print(f"获取远程文件大小失败: {e}")
            yield {"status": "error", "message": f"无法获取远程文件信息: {e}"}
            return False

        if os.path.exists(temp_path):
            downloaded_size = os.path.getsize(temp_path)
            print(f"发现未完成下载，已下载: {downloaded_size} 字节")

        for attempt in range(max_retries):
            try:
                print(f"下载尝试 {attempt + 1}/{max_retries}, 已下载: {downloaded_size}/{remote_size} 字节")
                progress_start = base_progress
                progress_range = 70  # 下载占 70% 进度（30~100）

                with self.sftp_to_target(target_host, target_user, target_password, target_port) as sftp:
                    with sftp.open(remote_path, 'rb') as remote_file:
                        if downloaded_size > 0:
                            remote_file.seek(downloaded_size)

                        mode = 'ab' if downloaded_size > 0 else 'wb'
                        with open(temp_path, mode) as local_file:
                            last_yield_time = time.time()

                            while downloaded_size < remote_size:
                                try:
                                    remote_file.settimeout(30)
                                    data = remote_file.read(chunk_size)
                                    if not data:
                                        break

                                    local_file.write(data)
                                    local_file.flush()
                                    downloaded_size += len(data)

                                    # 每 1 秒或进度变化较大时 yield
                                    current_time = time.time()
                                    if current_time - last_yield_time >= 1:
                                        progress = progress_start + (downloaded_size / remote_size) * progress_range
                                        yield {
                                            "status": "downloading",
                                            "progress": min(99, int(progress)),
                                            "message": f"下载中: {downloaded_size}/{remote_size} 字节"
                                        }
                                        last_yield_time = current_time

                                except (socket.timeout, EOFError) as e:
                                    print(f"读取中断: {e}")
                                    break

                        # 验证完整性
                        if downloaded_size == remote_size:
                            if os.path.exists(local_path):
                                os.remove(local_path)
                            os.rename(temp_path, local_path)
                            yield {"status": "success", "message": "文件下载完成"}
                            return True
                        else:
                            print("下载不完整")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)

            except Exception as e:
                print(f"下载出错 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"{retry_delay}秒后重试...")
                    time.sleep(retry_delay)

        # 清理临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        return False

    def verify_remote_file_exists(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            target_port: int = 22
    ) -> bool:
        """验证远程文件是否存在"""
        try:
            with self.sftp_to_target(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    target_port=target_port
            ) as sftp:
                try:
                    sftp.stat(remote_path)
                    print(f"✅ 远程文件存在: {remote_path}")
                    return True
                except FileNotFoundError:
                    print(f"❌ 远程文件不存在: {remote_path}")
                    return False
                except Exception as e:
                    print(f"❌ 验证文件时出错: {e}")
                    return False
        except Exception as e:
            print(f"❌ SFTP 连接失败: {e}")
            return False

    @contextmanager
    def interactive_ssh_to_target(self, **kwargs):
        channel, result = self.ssh_to_target(**kwargs)
        try:
            if channel and result.success:
                yield channel, result
            else:
                raise RuntimeError(f"SSH 登录失败: {result}")
        finally:
            if channel and not channel.closed:
                channel.close()
                print("目标设备 SSH 会话已关闭")

    @contextmanager
    def sftp_to_target(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            target_port: int = 22
    ):
        """
        通过跳板机建立 SFTP 连接（用于文件传输）
        """
        print(f"通过跳板机建立 SFTP 到 {target_user}@{target_host}:{target_port}")
        tunnel = None
        target_client = None
        sftp = None

        try:
            dest_addr = (target_host, target_port)
            local_addr = ('127.0.0.1', 22)  # 本地地址任意，仅用于通道标识

            tunnel = self.transport.open_channel(
                "direct-tcpip",
                dest_addr,
                local_addr,
                timeout=self.timeout
            )

            if tunnel is None:
                raise paramiko.ssh_exception.ChannelException(2, "Failed to open tunnel")

            target_client = paramiko.SSHClient()
            target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target_client.connect(
                hostname=target_host,
                username=target_user,
                password=target_password,
                sock=tunnel,
                timeout=30,
                banner_timeout=60,
                auth_timeout=60,
                allow_agent=False,
                look_for_keys=False,
                compress=True
            )

            transport = target_client.get_transport()
            if transport:
                transport.set_keepalive(30)
                transport.use_compression(True)  # 启用压缩

            sftp = target_client.open_sftp()

            sftp.CHUNK_SIZE = 524288  # 512KB 块
            sftp.MAX_REQUEST_SIZE = 524288

            print("✅ SFTP 隧道建立成功")
            yield sftp
        except Exception as e:
            print(f"❌ SFTP 连接失败: {e}")
            raise
        finally:
            if sftp:
                sftp.close()
            if target_client:
                target_client.close()
            if tunnel:
                tunnel.close()
            print("SFTP 隧道已关闭")

    def download_file_via_sftp(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            local_path: str,
            target_port: int = 22
    ) -> bool:
        """便捷方法：下载单个文件"""
        try:
            with self.sftp_to_target(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    target_port=target_port
            ) as sftp:
                print(f"正在下载 {remote_path} → {local_path}")

                try:
                    file_size = sftp.stat(remote_path).st_size
                    print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
                except:
                    file_size = 0

                sftp.get(remote_path, local_path)

                if os.path.exists(local_path):
                    local_size = os.path.getsize(local_path)
                    print(f"✅ 文件已保存至: {os.path.abspath(local_path)}")
                    print(f"下载文件大小: {local_size} 字节")
                    return True
                else:
                    print("❌ 文件下载后本地文件不存在")
                    return False

        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            return False

    def download_file_via_sftp_with_retry(
            self,
            target_host: str,
            target_user: str,
            target_password: str,
            remote_path: str,
            local_path: str,
            target_port: int = 22,
            chunk_size: int = 1048576,
            max_retries: int = 5,
            retry_delay: int = 10
    ) -> bool:
        """带断点续传的分块下载"""

        temp_path = local_path + ".downloading"
        downloaded_size = 0

        try:
            with self.sftp_to_target(
                    target_host=target_host,
                    target_user=target_user,
                    target_password=target_password,
                    target_port=target_port
            ) as sftp:
                remote_size = sftp.stat(remote_path).st_size
            print(f"远程文件大小: {remote_size} 字节 ({remote_size / 1024 / 1024:.2f} MB)")
        except Exception as e:
            print(f"获取远程文件信息失败: {e}")
            return False

        if os.path.exists(temp_path):
            downloaded_size = os.path.getsize(temp_path)
            print(f"发现未完成下载，已下载: {downloaded_size} 字节")

        for attempt in range(max_retries):
            try:
                print(f"下载尝试 {attempt + 1}/{max_retries}, 已下载: {downloaded_size}/{remote_size} 字节")

                with self.sftp_to_target(
                        target_host=target_host,
                        target_user=target_user,
                        target_password=target_password,
                        target_port=target_port
                ) as sftp:

                    with sftp.open(remote_path, 'rb') as remote_file:
                        if downloaded_size > 0:
                            remote_file.seek(downloaded_size)

                        with open(temp_path, 'ab' if downloaded_size > 0 else 'wb') as local_file:
                            last_progress_time = time.time()

                            while True:
                                try:
                                    remote_file.settimeout(30)
                                    data = remote_file.read(chunk_size)

                                    if not data:
                                        break

                                    local_file.write(data)
                                    local_file.flush()
                                    downloaded_size += len(data)

                                    # 每 5 秒记录一次进度
                                    current_time = time.time()
                                    if current_time - last_progress_time >= 5:
                                        progress = (downloaded_size / remote_size) * 100
                                        print(f"下载进度: {progress:.1f}% ({downloaded_size}/{remote_size})")
                                        last_progress_time = current_time

                                except socket.timeout:
                                    print("读取超时，继续尝试...")
                                    continue
                                except EOFError:
                                    print("EOF错误，可能连接中断")
                                    break

                    # 验证下载完整性
                    if downloaded_size == remote_size:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        os.rename(temp_path, local_path)
                        print(f"✅ 文件下载完成: {local_path}")
                        return True
                    else:
                        print(f"下载不完整: {downloaded_size}/{remote_size}")
                        if attempt < max_retries - 1:
                            print(f"{retry_delay}秒后继续下载...")
                            time.sleep(retry_delay)

            except Exception as e:
                print(f"下载失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"{retry_delay}秒后重试...")
                    time.sleep(retry_delay)

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        return False


# ==============================
# 主程序示例
# ==============================
def main():
    JUMP_HOST = "10.233.100.240"
    JUMP_USER = "jbc"
    JUMP_PASS = "Gy100@bjj"

    TARGET_HOST = "36.18.12.23"
    TARGET_USER = "root"
    TARGET_PASS = "Root_1234"

    try:
        print("🔧 正在建立跳板机连接...")
        with JumpSSHClient(
                jump_host=JUMP_HOST,
                jump_user=JUMP_USER,
                jump_password=JUMP_PASS,
                timeout=15
        ) as client:

            print("🚀 开始执行日志下载任务...\n")

            # 调用 download_file_with_progress（它是 client 的方法）
            gen = client.download_file_with_progress(
                target_host=TARGET_HOST,
                target_user=TARGET_USER,
                target_password=TARGET_PASS,
                shelf_number=1,
                slot_number=41,
                download_dir="/logtar",
                local_dir=".",
                check_interval=30,
                timeout=480,
                default_completion="ZXPOTN"
            )

            success = False
            local_path = ""

            # 消费生成器，打印每一步
            for progress_update in gen:
                # 美化输出：只打印关键信息
                status = progress_update.get("status")
                message = progress_update.get("message", "")
                progress = progress_update.get("progress", 0)

                # 打印进度行（可选：覆盖上一行实现动态效果，这里保持简单）
                print(f"[{progress:3d}%] {message}")

                # 如果是最终完成状态，记录路径
                if status == "completed":
                    success = True
                    local_path = progress_update.get("local_path", "")

            print("\n" + "=" * 60)

            if success:
                abs_path = os.path.abspath(local_path)
                print("✅ 任务成功完成！")
                print(f"📁 日志文件已保存至: {abs_path}")

                # 可选：打印 Markdown 链接（虽然终端不渲染，但可复制）
                markdown = progress_update.get("markdown", "")
                if markdown:
                    print(f"🔗 Markdown 下载链接: {markdown}")
            else:
                print("❌ 任务失败！未收到完成信号。")
                print("💡 请检查网络、设备状态或超时设置。")

    except Exception as e:
        print("💥 主流程发生未预期异常")
        print(f"\n💥 异常退出: {e}")


if __name__ == "__main__":
    main()
