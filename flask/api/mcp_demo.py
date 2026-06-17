import os
import requests
from datetime import datetime
from fastmcp import FastMCP
from agent_utils import Clear_proxy

Clear_proxy()

mcp = FastMCP(name="MyAssistantServer")

@mcp.tool()
async def add(a: float, b: float) -> float:
    """加法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之和
    """
    return a + b


@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """减法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之差 (a - b)
    """
    return a - b


@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """乘法运算

    参数:
    a: 第一个数字
    b: 第二个数字

    返回:
    两数之积
    """
    return a * b


@mcp.tool()
async def divide(a: float, b: float) -> float:
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

@mcp.tool()
async def get_current_time() -> str:
    """获取当前系统时间
    
    返回:
    格式化的当前时间字符串 (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    Clear_proxy()
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)