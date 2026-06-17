import os
import chardet
import argparse
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import FileResponse, PlainTextResponse

app = FastAPI(
    title="文件读取服务",
    description="通过完整路径读取服务器上的文件内容，支持单个文件和目录递归遍历",
    version="1.0.5"
)

# 全局变量存储配置，将通过命令行参数设置
BASE_DIR = None

# 可选：添加简单认证（示例使用 Token）
def verify_token(token: str = Query(..., description="访问令牌")):
    if token != "your-secret-token":  # 替换为你的实际 token
        raise HTTPException(status_code=403, detail="无效的访问令牌")
    return token

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取前10KB用于编码检测
    result = chardet.detect(raw_data)
    return result['encoding']

def read_single_file(full_path, encoding=None):
    """读取单个文件内容的辅助函数"""
    try:
        # 如果未指定编码，自动检测
        if not encoding:
            encoding = detect_encoding(full_path)
            if not encoding:
                encoding = 'utf-8'  # 默认编码
        
        # 尝试用检测到的编码读取
        with open(full_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        return {
            "encoding_used": encoding,
            "content": content,
            "success": True
        }
    except UnicodeDecodeError:
        # 如果所有编码尝试都失败，返回二进制内容（Base64编码）
        with open(full_path, 'rb') as f:
            content = f.read()
        return {
            "encoding_used": "binary",
            "message": "文件不是文本文件或编码无法识别，返回二进制内容",
            "content_base64": content.hex(),  # 用十六进制表示二进制内容
            "success": False
        }
    except Exception as e:
        return {
            "error": f"读取文件失败: {str(e)}",
            "success": False
        }

def recursive_list_files(full_dir_path, base_dir, output, encoding):
    """递归遍历目录下的所有文件和子目录"""
    for entry in os.scandir(full_dir_path):
        if entry.is_file():
            # 处理文件
            relative_path = os.path.relpath(entry.path, base_dir)
            file_info = read_single_file(entry.path, encoding)
            
            # 添加文件标题
            output.append(f"### 文件: {relative_path}")
            output.append("```c")
            
            # 添加文件内容或错误信息
            if file_info["success"] and "content" in file_info:
                output.append(file_info["content"])
            elif "error" in file_info:
                output.append(f"错误: {file_info['error']}")
            else:
                output.append(file_info.get("message", "未知错误"))
            
            output.append("```\n")
        elif entry.is_dir(follow_symlinks=False):
            # 递归处理子目录
            recursive_list_files(entry.path, base_dir, output, encoding)

@app.get("/read", response_class=PlainTextResponse)
def read_file(
    filepath: str = Query(..., description="从 BASE_DIR 起始的完整相对路径，例如 L2/plat/port/src/sspPortApi.c 或 L2/plat/port/src/*"),
    # token: str = Depends(verify_token)  # 启用认证（可注释掉关闭）
    encoding: str = Query(None, description="指定文件编码，如gbk, utf-8, 不指定则自动检测")
):
    # 确保BASE_DIR已正确设置
    if not BASE_DIR:
        return "服务器配置错误，未设置基础目录"
    
    # 存储输出内容的列表
    output = []
    
    # 检查是否是批量读取目录下所有文件（包括子目录）
    if filepath.endswith('*'):
        # 处理目录批量读取
        dirpath = filepath[:-1]  # 去除末尾的*
        full_dir_path = os.path.join(BASE_DIR, dirpath)
        
        # 规范化路径，解决不同系统路径分隔符问题
        full_dir_path = os.path.normpath(full_dir_path)
        base_dir_abs = os.path.abspath(BASE_DIR)
        
        # 防止路径穿越攻击
        if not os.path.abspath(full_dir_path).startswith(base_dir_abs):
            return "禁止访问（路径越权）"
        
        if not os.path.exists(full_dir_path):
            return f"目录未找到: {full_dir_path}"
        
        if not os.path.isdir(full_dir_path):
            return f"指定路径不是一个目录: {full_dir_path}"
        
        # 递归读取目录下所有文件（包括子目录）
        recursive_list_files(full_dir_path, base_dir_abs, output, encoding)
        
        if not output:
            return f"目录 {dirpath} 及其子目录中未找到任何文件"
    else:
        # 处理单个文件读取
        full_path = os.path.join(BASE_DIR, filepath)
        full_path = os.path.normpath(full_path)

        # 防止路径穿越攻击
        if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
            return "禁止访问（路径越权）"

        if not os.path.exists(full_path):
            return f"文件未找到: {full_path}"

        if not os.path.isfile(full_path):
            return "指定路径不是一个文件"

        file_info = read_single_file(full_path, encoding)
        
        # 添加单个文件内容
        output.append(f"### 文件: {filepath}")
        output.append("```c")
        
        if file_info["success"] and "content" in file_info:
            output.append(file_info["content"])
        elif "error" in file_info:
            output.append(f"错误: {file_info['error']}")
        else:
            output.append(file_info.get("message", "未知错误"))
        
        output.append("```\n")
    
    # 合并所有内容为一个字符串并返回
    return "\n".join(output)

@app.get("/download")
def download_file(
    filepath: str = Query(..., description="从 BASE_DIR 起始的完整相对路径，例如 L2/plat/port/src/sspPortApi.c"),
    # token: str = Depends(verify_token)
):
    if not BASE_DIR:
        raise HTTPException(status_code=500, detail="服务器配置错误，未设置基础目录")
        
    full_path = os.path.join(BASE_DIR, filepath)

    if not os.path.abspath(full_path).startswith(os.path.abspath(BASE_DIR)):
        raise HTTPException(status_code=403, detail="禁止访问")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件未找到")

    return FileResponse(
        full_path,
        filename=os.path.basename(full_path),
        as_attachment=True
    )

@app.get("/list")
def list_files(
    dirpath: str = Query("", description="要列出的子目录，如 L2 或 L2/plat"),
    recursive: bool = Query(False, description="是否递归列出子目录内容")
):
    if not BASE_DIR:
        raise HTTPException(status_code=500, detail="服务器配置错误，未设置基础目录")
        
    target_dir = os.path.join(BASE_DIR, dirpath)
    target_dir = os.path.normpath(target_dir)
    real_base = os.path.abspath(BASE_DIR)
    real_path = os.path.abspath(target_dir)

    # 安全检查
    if not real_path.startswith(real_base):
        raise HTTPException(status_code=403, detail="路径越权")

    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="目录不存在")

    if not os.path.isdir(real_path):
        raise HTTPException(status_code=400, detail="目标不是目录")

    def recursive_list(current_path, relative_path):
        items = []
        for entry in os.scandir(current_path):
            is_dir = entry.is_dir(follow_symlinks=False)
            item_relative_path = os.path.join(relative_path, entry.name)
            size = None if is_dir else os.path.getsize(entry.path)
            item = {
                "name": entry.name,
                "path": item_relative_path,
                "type": "directory" if is_dir else "file",
                "size": size
            }
            items.append(item)
            if is_dir and recursive:
                items.extend(recursive_list(entry.path, item_relative_path))
        return items

    try:
        files = recursive_list(real_path, dirpath)
        return {
            "dirpath": dirpath,
            "recursive": recursive,
            "items_count": len(files),
            "items": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取目录失败: {str(e)}")

if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='文件读取服务')
    parser.add_argument('base_dir', help='文件服务的基础目录路径')
    parser.add_argument('--host', default='127.0.0.1', help='服务器绑定的IP地址，默认是127.0.0.1')
    parser.add_argument('--port', type=int, default=4001, help='服务器监听的端口号，默认是4001')
    args = parser.parse_args()
    
    # 验证并设置基础目录
    if not os.path.isdir(args.base_dir):
        print(f"错误: {args.base_dir} 不是有效的目录")
        exit(1)
    
    BASE_DIR = os.path.abspath(args.base_dir)
    print(f"文件服务基础目录设置为: {BASE_DIR}")
    print(f"服务将运行在: http://{args.host}:{args.port}")
    
    # 启动服务
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)



    # 服务器启动实例
    # python file_server.py /home/10171727@zte.intra/workspace/M2F1K --host 10.90.251.221 --port 4001
    # ./file_server /home/10171727@zte.intra/workspace/M2F1K --host 10.90.251.221 --port 4001

    # curl --noproxy '10.90.251.221' "http://10.90.251.221:4001/read?filepath=L2/plat/port/src/sspPortApi.c"
    # curl --noproxy '10.90.251.221' "http://10.90.251.221:4001/read?filepath=L2/plat/port/src/*"
    # curl --noproxy '10.89.207.215' "http://10.89.207.215:4001/read?filepath=code/otn/inert/dcn/agent/dcn_comm/service/include/protec/*cdcntimingctrl_serv_pro_api.h"

    # 编译命令
    # python -m PyInstaller --onefile --name fileserver file_server.py
    
    
    # 使用 systemd 创建自启动服务
    # sudo vi /etc/systemd/system/fileserver.service
    # [Unit]
    # Description=File Server Daemon
    # After=network.target

    # [Service]
    # Type=simple
    # User=10171727@zte.intra
    # WorkingDirectory=/home/10171727@zte.intra/workspace/M2F1K
    # ExecStart=/home/10171727@zte.intra/workspace/AI/AI/public/website-linghang/flask/api/dist/fileserver /home/10171727@zte.intra/workspace/M2F1K --host 10.90.251.221 --port 4001
    # Restart=always  # 崩溃后自动重启
    # RestartSec=5
    # StandardOutput=syslog
    # StandardError=syslog
    # SyslogIdentifier=fileserver

    # [Install]
    # WantedBy=multi-user.target


    # 守护进程启动
    # sudo systemctl daemon-reload
    # sudo systemctl enable fileserver  # 设置开机自启
    # sudo systemctl start fileserver   # 立即启动
    # sudo systemctl status fileserver  # 检查状态

    # sudo systemctl stop fileserver    # 停止服务
    # sudo systemctl disable fileserver # 禁用开机自启
