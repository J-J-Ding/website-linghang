# -*- coding:utf-8 -*-
# @Time    : 2025/8/8 上午11:35
# @Author  : WangHao
# @File    : gerrit_download.py
# @Project : codereview_edit
# @Remark  :
import os
import subprocess
from typing import Tuple, Optional


def run_command(cmd: str) -> Tuple[bool, str]:
    """
    执行终端命令并返回执行结果

    调用subprocess.run执行命令，捕获标准输出和错误输出，
    根据返回码判断命令是否执行成功

    Args:
        cmd: 待执行的命令字符串

    Returns:
        元组(执行成功标志, 输出内容)
        - 执行成功时: (True, 标准输出内容)
        - 执行失败时: (False, 错误信息)
    """
    try:
        # 执行命令，捕获输出并以文本形式返回
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False  # 不自动抛出异常，手动处理返回码
        )
        
        # 根据返回码判断执行结果
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
            
    except Exception as e:
        return False, f"命令执行异常: {str(e)}"


def code_library_download(code_library: str, branch: str) -> Optional[str]:
    """
    从Gerrit服务器克隆指定代码库和分支到本地缓存目录

    处理代码库路径格式，创建必要的缓存目录，执行git clone命令
    并返回执行结果信息

    Args:
        code_library: 代码库路径（支持带前导斜杠的格式）
        branch: 要克隆的分支名称

    Returns:
        克隆操作的输出信息；若发生异常则返回错误描述
    """
    try:
        # 标准化代码库路径（移除前导斜杠，避免路径错误）
        normalized_library = code_library.lstrip('/')
        if not normalized_library:
            return "错误：代码库路径不能为空"

        # 构建缓存目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(current_dir, 'gerrit_code', normalized_library)

        # 检查并创建缓存目录（支持递归创建，忽略已存在的目录）
        os.makedirs(os.path.dirname(cache_dir), exist_ok=True)

        # 构建Git克隆命令
        git_cmd = (
            f"git clone -b {branch} "
            f"ssh://zxrpo@gerritro.zte.com.cn:29418/{normalized_library} "
            f"{cache_dir}"
        )

        # 执行克隆命令并返回结果
        output = run_command(git_cmd)
        return output

    except Exception as e:
        return f"代码库下载失败: {str(e)}"


if __name__ == "__main__":
    # 示例：下载指定代码库和分支
    target_library = "19700/300_SOFT"
    target_branch = "master"
    
    try:
        # 执行代码库下载
        download_result = code_library_download(target_library, target_branch)
        
        # 输出执行结果
        if download_result:
            print("代码库下载结果:")
            print(download_result)
            
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
