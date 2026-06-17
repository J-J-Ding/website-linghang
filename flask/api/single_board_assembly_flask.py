import os
import json
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# ===== CORS 配置 =====
# 注意：origin 必须是 "协议://主机:端口" 格式，不能包含路径（如 /login）
cors_origins = [
    'http://localhost:3002',
    'http://10.80.176.53:3002',
    'http://10.80.176.64:3002',
    'http://10.239.69.183:5020',        # ✅ 正确：只保留到端口
    'http://10.90.166.68:3002',
    'http://10.239.69.183:7002',
    'http://10.239.69.183:9002',
    'http://10.239.69.30:9002',
    'http://10.239.69.183:3002',
    'http://10.239.69.30:3002',
    'http://10.90.175.164:3002',
    'http://10.90.251.221:3002',
    'http://wsit.zx.zte.com.cn:3002',
    'https://wsit.zx.zte.com.cn',        # ✅ 注意：这是 HTTPS 无端口（默认 443）
    'https://wsit.zx.zte.com.cn:3002',   # ✅ 明确指定端口
    'http://10.239.69.191:3000',
    'http://10.80.173.91:3002',
    'http://10.80.176.48:3002',
    'http://10.239.69.183:3032'
]

# 清理 origins：去除末尾空格，过滤无效项
cleaned_origins = []
for origin in cors_origins:
    origin = origin.strip()
    if origin and '://' in origin:
        # 移除路径部分（只保留协议+host+port）
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        clean_origin = f"{parsed.scheme}://{parsed.netloc}"
        cleaned_origins.append(clean_origin)
    else:
        print(f"警告：跳过无效 origin: {origin}")

# 去重
cleaned_origins = list(set(cleaned_origins))
print("已配置的 CORS origins:")
for o in cleaned_origins:
    print(f"  - {o}")

CORS(
    app,
    origins=cleaned_origins,
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'x-user-name'],
    supports_credentials=True,
    max_age=3600
)

# ===== API 路由 =====
@app.route('/api/boardAssembly/generateFramework', methods=['POST'])
def generate_framework():
    """
    框架代码生成：执行 shell 脚本
    """
    try:
        print('=== 开始框架代码生成 ===')
        print(f'请求方法: {request.method}')
        print(f'请求URL: {request.url}')
        print(f'Content-Type: {request.content_type}')
        
        # 获取 JSON 数据
        data = request.get_json(force=True, silent=True)
        if data is None:
            raw_data = request.get_data(as_text=True)
            if raw_data and raw_data.strip():
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError as je:
                    return jsonify({
                        'status': 'error',
                        'message': f'JSON格式错误: {str(je)}'
                    }), 400
            else:
                return jsonify({
                    'status': 'error',
                    'message': '请求数据为空'
                }), 400

        # 提取并处理参数
        board_name = (data.get('boardName') or '').strip()
        business_model = (data.get('businessModel') or '').strip()
        ip = (data.get('ip') or '').strip()
        code_path = (data.get('codePath') or '').strip()
        code_path = f"/home{code_path}"  # 前缀固定为 /home
        user = data.get('user', 'guest')

        print(f'解析参数 - 单板名称: {board_name}, 业务模型: {business_model}, IP: {ip}, 代码路径: {code_path}, 用户: {user}')

        # 验证必填字段
        if not board_name:
            return jsonify({'status': 'error', 'message': '单板名称不能为空'}), 400
        if not code_path:
            return jsonify({'status': 'error', 'message': '代码路径不能为空'}), 400

        # 构建脚本路径
        code_path_obj = Path(code_path)
        script_dir = code_path_obj / 'boardassemble' / '06_build_system'
        script_path = script_dir / 'gen_one_board.sh'

        if not script_path.exists():
            error_msg = f'脚本文件不存在: {script_path}'
            print(f'错误: {error_msg}')
            return jsonify({'status': 'error', 'message': error_msg}), 404

        script_abs_path = script_path.resolve()
        if not script_abs_path.exists():
            error_msg = f'脚本文件不存在（绝对路径）: {script_abs_path}'
            print(f'错误: {error_msg}')
            return jsonify({'status': 'error', 'message': error_msg}), 404

        # 确保可执行
        if not os.access(script_abs_path, os.X_OK):
            try:
                os.chmod(script_abs_path, 0o755)
            except Exception as e:
                print(f'chmod 失败: {e}')

        # 执行脚本
        script_name = script_abs_path.name
        script_dir_str = str(script_dir)
        cmd = f'cd "{script_dir_str}" && SHELL=/bin/bash bash ./{script_name} {board_name}'
        print(f'执行命令: {cmd}')

        env = os.environ.copy()
        env['SHELL'] = '/bin/bash'
        env['BASH_ENV'] = ''

        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=script_dir_str,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        try:
            stdout, stderr = process.communicate(input='y\n', timeout=300)
        except subprocess.TimeoutExpired:
            process.kill()
            return jsonify({'status': 'error', 'message': '脚本执行超时（5分钟）'}), 500

        returncode = process.returncode

        if returncode == 0:
            print('=== 框架代码生成成功 ===')
            return jsonify({
                'status': 'success',
                'message': '框架代码生成完成',
                'data': {
                    'board_name': board_name,
                    'script_path': str(script_path),
                    'output': stdout,
                    'return_code': returncode
                }
            }), 200
        else:
            error_msg = f'脚本执行失败，返回码: {returncode}'
            if stderr:
                error_msg += f'\n错误信息: {stderr}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': {
                    'board_name': board_name,
                    'script_path': str(script_path),
                    'stdout': stdout,
                    'stderr': stderr,
                    'return_code': returncode
                }
            }), 500

    except Exception as e:
        import traceback
        error_msg = f'框架代码生成失败: {str(e)}'
        print(f'错误: {error_msg}')
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__
        }), 500


if __name__ == '__main__':
    app.run(host='10.239.69.183', port=3035, debug=False)