#!/usr/bin/env python3

from fastmcp import FastMCP

mcp = FastMCP(name="MyAssistantServer")


@mcp.tool()
def add(a: float, b: float) -> float:
    """加法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之和
    """
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """减法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之差 (a - b)
    """
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """乘法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之积
    """
    c = a * b
    print(f"{a} * {b} = {c}")
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """除法运算

    参数:
    a: 被除数
    b: 除数

    返回:
    两数之商 (a / b)

    异常:
    ValueError: 当除数为零时
    """
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b


from pathlib import Path
@mcp.tool()
def list_files() -> list:
    # 列出当前目录下的所有文件
    files = [f.name for f in Path(__file__).parent.iterdir() if not f.is_dir()]
    return files

@mcp.tool()
def list_dirs() -> list:
    # 列出当前目录下的所有文件夹
    files = [f.name for f in Path(__file__).parent.iterdir() if f.is_dir()]
    return files

@mcp.tool()
def add_word_to_file(filename: str, word: str):
    # 在文件 filename 中添加新的内容 word
    f = Path(filename)
    with f.open("a") as ff:
        ff.write(f"{word}\n")
    print(f"add word '{word}' to file '{filename}'")
    
@mcp.tool()
def delete_file(filename: str):
    # 删除指定的文件
    f = Path(filename)
    if f.exists():
        f.unlink()
        return f"Deleted file: {filename}"
    else:
        return f"File not found: {filename}"


@mcp.tool()
def create_file(filename:str):
    # 创建一个新的空文件
    f = Path(filename)
    if not f.exists():
        f.touch()
        return f"Created file: {filename}"
    else:
        return f"File already exists: {filename}"

@mcp.tool()
def create_tar_file(tar_name: str, file: list[str]):
    """创建一个tar文件，包含指定的文件列表"""
    import subprocess
    files = [f for f in file if Path(f).exists()]
    files_str = " ".join(files)
    subprocess.run(["tar", "-cvf", tar_name, *files], check=True)
    return tar_name
    
    

if __name__ == "__main__":
    mcp.run(transport='stdio')
