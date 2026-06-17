import os

def count_code_lines(directory_path):
    """
    统计指定目录下.h和.c文件的代码行数
    
    Args:
        directory_path (str): 指定的目录路径
        
    Returns:
        int: 代码总行数
    """
    total_lines = 0
    file_count = 0
    
    # 用于存储每个子目录的行数统计
    dir_lines = {}
    
    # 遍历目录下的所有文件
    for root, dirs, files in os.walk(directory_path):
        dir_line_count = 0
        dir_file_count = 0
        
        for file in files:
            # 检查文件扩展名是否为.h或.c
            if file.endswith('.h') or file.endswith('.c'):
                file_path = os.path.join(root, file)
                file_line_count = 0
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 统计非空行（去除只包含空白字符的行）
                        for line in lines:
                            if line.strip():  # 如果去除空白字符后不是空字符串
                                file_line_count += 1
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            lines = f.readlines()
                            file_line_count = 0
                            for line in lines:
                                if line.strip():
                                    file_line_count += 1
                    except UnicodeDecodeError:
                        print(f"无法解码文件: {file_path}，跳过该文件")
                        continue
                except Exception as e:
                    print(f"读取文件时出错: {file_path}, 错误: {e}")
                    continue
                
                print(f"{file_path}: {file_line_count} 行")
                dir_line_count += file_line_count
                total_lines += file_line_count
                dir_file_count += 1
                file_count += 1
        
        # 记录当前目录的统计信息
        if dir_file_count > 0:
            dir_lines[root] = (dir_line_count, dir_file_count)
    
    # 打印每个目录的统计信息
    print("各子目录统计:")
    for dir_path, (dir_line_count, dir_file_count) in dir_lines.items():
        print(f"{dir_path}: {dir_file_count} 个文件, 共 {dir_line_count} 行代码")
    
    print(f"总共处理了 {file_count} 个文件")
    return total_lines

# 如果需要排除空行和注释，可以使用以下改进版本
def count_code_lines_excluding_comments(directory_path):
    """
    统计指定目录下.h和.c文件的代码行数（排除空行和注释）
    
    Args:
        directory_path (str): 指定的目录路径
        
    Returns:
        int: 代码总行数
    """
    total_lines = 0
    file_count = 0
    
    # 用于存储每个子目录的行数统计
    dir_lines = {}
    
    for root, dirs, files in os.walk(directory_path):
        dir_line_count = 0
        dir_file_count = 0
        
        for file in files:
            if file.endswith('.h') or file.endswith('.c'):
                file_path = os.path.join(root, file)
                file_line_count = 0
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines:
                            stripped_line = line.strip()
                            # 排除空行和注释行（以//开头或在/* */内的行）
                            if stripped_line and not stripped_line.startswith('//') and '/*' not in stripped_line and '*/' not in stripped_line:
                                file_line_count += 1
                except UnicodeDecodeError:
                    # 尝试其他编码
                    try:
                        with open(file_path, 'r', encoding='gbk') as f:
                            lines = f.readlines()
                            file_line_count = 0
                            for line in lines:
                                stripped_line = line.strip()
                                if stripped_line and not stripped_line.startswith('//') and '/*' not in stripped_line and '*/' not in stripped_line:
                                    file_line_count += 1
                    except UnicodeDecodeError:
                        print(f"无法解码文件: {file_path}，跳过该文件")
                        continue
                except Exception as e:
                    print(f"读取文件时出错: {file_path}, 错误: {e}")
                    continue
                
                print(f"{file_path}: {file_line_count} 行")
                dir_line_count += file_line_count
                total_lines += file_line_count
                dir_file_count += 1
                file_count += 1
        
        # 记录当前目录的统计信息
        if dir_file_count > 0:
            dir_lines[root] = (dir_line_count, dir_file_count)
    
    # 打印每个目录的统计信息
    print("各子目录统计:")
    for dir_path, (dir_line_count, dir_file_count) in dir_lines.items():
        print(f"{dir_path}: {dir_file_count} 个文件, 共 {dir_line_count} 行代码")
    
    print(f"总共处理了 {file_count} 个文件")
    return total_lines

if __name__ == "__main__":
    # 示例用法
    directory = "/home/10171727@zte.intra/workspace/M2F1K/L2/plat/Service"
    lines = count_code_lines(directory)
    print(f"目录 {directory} 下所有.h和.c文件的代码总行数: {lines}")
