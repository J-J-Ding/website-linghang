#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单板组装助手 API
"""
import os
import shutil
import subprocess
from flask import request, jsonify, Response
from pathlib import Path


def handle_options():
    """
    处理 OPTIONS 预检请求
    """
    from flask import request as flask_request
    origin = flask_request.headers.get('Origin', '*')
    response = Response()
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, x-user-name')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH')
    response.headers.add('Access-Control-Max-Age', '3600')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200


def generate_elements():
    """
    组装要素生成
    将模板文件拷贝到目标目录
    """
    try:
        print('=== 开始组装要素生成 ===')
        print(f'请求方法: {request.method}')
        print(f'请求URL: {request.url}')
        print(f'Content-Type: {request.content_type}')
        print(f'请求头: {dict(request.headers)}')
        
        # 安全地获取JSON数据
        # 直接使用 request.data 来避免 Content-Type 检查问题
        import json
        data = None
        try:
            # 首先尝试使用 get_json，如果失败则使用 request.data
            try:
                data = request.get_json(force=True, silent=True)
                print(f'通过 get_json 获取的数据: {data}')
            except Exception as e1:
                print(f'get_json 失败，尝试使用 request.data: {str(e1)}')
            
            # 如果 get_json 返回 None 或失败，尝试从 request.data 解析
            if data is None:
                raw_data = request.get_data(as_text=True)
                print(f'原始请求数据: {raw_data}')
                if raw_data and raw_data.strip():
                    try:
                        data = json.loads(raw_data)
                        print(f'从原始数据解析的JSON: {data}')
                    except json.JSONDecodeError as je:
                        print(f'JSON解析错误: {str(je)}')
                        return jsonify({
                            'status': 'error',
                            'message': f'JSON格式错误: {str(je)}'
                        }), 400
        except Exception as json_error:
            print(f'JSON解析错误: {str(json_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'JSON解析失败: {str(json_error)}'
            }), 400
        
        if not data:
            print('错误: 请求数据为空')
            return jsonify({
                'status': 'error',
                'message': '请求数据为空'
            }), 400

        # 获取参数
        try:
            board_name = data.get('boardName', '').strip() if data.get('boardName') else ''
            business_model = data.get('businessModel', '').strip() if data.get('businessModel') else ''
            ip = data.get('ip', '').strip() if data.get('ip') else ''
            code_path = data.get('codePath', '').strip() if data.get('codePath') else ''
            user = data.get('user', 'guest')
            
            print(f'解析参数 - 单板名称: {board_name}, 业务模型: {business_model}, IP: {ip}, 代码路径: {code_path}, 用户: {user}')
        except Exception as param_error:
            print(f'参数解析错误: {str(param_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'参数解析失败: {str(param_error)}'
            }), 400

        # 验证必填参数
        if not board_name:
            print('错误: 单板名称不能为空')
            return jsonify({
                'status': 'error',
                'message': '单板名称不能为空'
            }), 400
        
        # 验证代码路径参数
        if not code_path:
            print('错误: 代码路径不能为空')
            return jsonify({
                'status': 'error',
                'message': '代码路径不能为空'
            }), 400

        # 源文件目录（固定路径）
        SOURCE_DIR = Path('/otn_ai/project/board_makefile')
        DEFAULT_SOURCE_FILE = 'M7LB4R_hw_cfg.mk'
        
        print(f'源文件目录: {SOURCE_DIR}')
        print(f'源文件目录是否存在: {SOURCE_DIR.exists()}')
        
        # 检查源文件目录是否存在
        if not SOURCE_DIR.exists():
            error_msg = f'源文件目录不存在: {SOURCE_DIR}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 404
        
        # 根据单板名称模糊匹配查找源文件
        source_file = None
        try:
            # 1. 首先尝试精确匹配：{board_name}_hw_cfg.mk
            exact_filename = f'{board_name}_hw_cfg.mk'
            exact_file = SOURCE_DIR / exact_filename
            if exact_file.exists():
                source_file = exact_file
                print(f'找到精确匹配文件: {exact_file}')
            else:
                # 2. 模糊匹配：查找包含单板名称的 .mk 文件
                print(f'精确匹配未找到，尝试模糊匹配: {board_name}')
                matching_files = []
                if SOURCE_DIR.is_dir():
                    for file_path in SOURCE_DIR.glob('*.mk'):
                        if board_name.lower() in file_path.name.lower():
                            matching_files.append(file_path)
                            print(f'找到模糊匹配文件: {file_path.name}')
                
                if matching_files:
                    # 使用第一个匹配的文件
                    source_file = matching_files[0]
                    print(f'使用模糊匹配文件: {source_file}')
                else:
                    # 3. 如果都找不到，使用默认文件作为后备
                    default_file = SOURCE_DIR / DEFAULT_SOURCE_FILE
                    if default_file.exists():
                        source_file = default_file
                        print(f'使用默认文件作为后备: {default_file}')
                    else:
                        # 4. 如果默认文件也不存在，列出目录中可用的文件
                        available_files = []
                        if SOURCE_DIR.is_dir():
                            available_files = [f.name for f in SOURCE_DIR.glob('*.mk')]
                        
                        error_msg = f'未找到单板 "{board_name}" 对应的配置文件，且默认文件 {DEFAULT_SOURCE_FILE} 也不存在。'
                        if available_files:
                            error_msg += f'\n目录中可用的文件: {", ".join(sorted(available_files))}'
                        else:
                            error_msg += f'\n源文件目录 {SOURCE_DIR} 中没有任何 .mk 文件。'
                        
                        print(f'错误: {error_msg}')
                        return jsonify({
                            'status': 'error',
                            'message': error_msg,
                            'data': {
                                'board_name': board_name,
                                'source_dir': str(SOURCE_DIR),
                                'available_files': available_files
                            }
                        }), 404
        
        except Exception as path_error:
            print(f'源文件查找错误: {str(path_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'源文件查找失败: {str(path_error)}'
            }), 500
        
        if source_file is None or not source_file.exists():
            # 列出目录中可用的文件
            available_files = []
            try:
                if SOURCE_DIR.is_dir():
                    available_files = [f.name for f in SOURCE_DIR.glob('*.mk')]
            except Exception:
                pass
            
            error_msg = f'源文件不存在: {source_file}'
            if available_files:
                error_msg += f'\n目录中可用的文件: {", ".join(sorted(available_files))}'
            
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': {
                    'board_name': board_name,
                    'source_dir': str(SOURCE_DIR),
                    'available_files': available_files
                }
            }), 404
        
        print(f'最终使用的源文件: {source_file}')

        # 目标目录：{code_path}/boardassemble/05_assembly_config
        try:
            # 构建目标目录路径
            code_path_obj = Path(code_path)
            target_dir = code_path_obj / 'boardassemble' / '05_assembly_config'
            print(f'代码路径: {code_path}')
            print(f'目标目录: {target_dir}')
            print(f'目标目录是否存在: {target_dir.exists()}')
        except Exception as target_path_error:
            print(f'目标路径创建错误: {str(target_path_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'目标路径创建失败: {str(target_path_error)}'
            }), 500
        
        # 确保目标目录存在
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f'目标目录创建/确认成功: {target_dir}')
        except PermissionError as pe:
            error_msg = f'无法创建目标目录，权限不足: {target_dir}。错误: {str(pe)}'
            print(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500
        except Exception as de:
            error_msg = f'无法创建目标目录: {target_dir}。错误: {str(de)}'
            print(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500

        # 根据单板名称生成目标文件名
        # 例如：M3LB4R_hw_cfg.mk
        target_filename = f'{board_name}_hw_cfg.mk'
        target_file = target_dir / target_filename
        
        print(f'目标文件路径: {target_file}')

        # 拷贝文件
        try:
            shutil.copy2(source_file, target_file)
            print(f'文件拷贝成功: {source_file} -> {target_file}')
        except PermissionError as pe:
            error_msg = f'文件拷贝失败，权限不足。源文件: {source_file}，目标文件: {target_file}。错误: {str(pe)}'
            print(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500
        except OSError as oe:
            error_msg = f'文件拷贝失败，系统错误。源文件: {source_file}，目标文件: {target_file}。错误: {str(oe)}'
            print(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500

        # 读取生成的文件内容
        file_content = ''
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            print(f'文件内容读取成功，长度: {len(file_content)} 字符')
        except Exception as read_error:
            print(f'警告: 读取文件内容失败: {str(read_error)}')
            # 即使读取失败，也继续返回成功，只是不包含文件内容
            file_content = f'文件已生成，但读取内容失败: {str(read_error)}'

        print('=== 组装要素生成成功 ===')
        result = {
            'status': 'success',
            'message': f'文件已成功拷贝到: {target_file}',
            'data': {
                'source_file': str(source_file),
                'target_file': str(target_file),
                'board_name': board_name,
                'business_model': business_model,
                'file_content': file_content  # 添加文件内容
            }
        }
        print(f'返回结果: {result}')
        return jsonify(result), 200

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f'生成失败: {str(e)}'
        print(f'组装要素生成错误: {error_msg}')
        print(f'错误堆栈: {error_trace}')
        # 在开发环境下返回详细错误信息
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__
        }), 500


def get_board_names():
    """
    获取单板名称选项列表
    """
    try:
        # TODO: 从数据库获取单板名称列表
        # 这里先返回默认选项
        board_names = [
            'client_brd',
            'line_brc',
            'M1MOM4G',
            'M7LB4R',
            'M8C4R',
            'M8TDB4H',
            'tlm_brd_frm',
            'tlm_brd'
        ]
        
        return jsonify({
            'status': 'success',
            'data': [{'name': name, 'value': name} for name in board_names]
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取单板名称列表失败: {str(e)}'
        }), 500


def get_business_models():
    """
    获取业务模型选项列表
    """
    try:
        # TODO: 从数据库获取业务模型列表
        # 这里先返回默认选项
        business_models = [
            {'value': 'sc', 'label': 'sc(客户版)', 'description': '客户版'},
            {'value': 'sl', 'label': 'sl(线路板)', 'description': '线路板'},
            {'value': 'mf', 'label': 'mf(支线路有framer板)', 'description': '支线路有framer板'},
            {'value': 'mn', 'label': 'mn(支线路无framer板)', 'description': '支线路无framer板'}
        ]
        
        return jsonify({
            'status': 'success',
            'data': business_models
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取业务模型列表失败: {str(e)}'
        }), 500


def generate_framework():
    """
    框架代码生成
    执行 shell 脚本生成框架代码
    """
    try:
        print('=== 开始框架代码生成 ===')
        print(f'请求方法: {request.method}')
        print(f'请求URL: {request.url}')
        print(f'Content-Type: {request.content_type}')
        
        # 安全地获取JSON数据
        import json
        data = None
        try:
            data = request.get_json(force=True, silent=True)
            print(f'通过 get_json 获取的数据: {data}')
        except Exception as e1:
            print(f'get_json 失败，尝试使用 request.data: {str(e1)}')
        
        if data is None:
            raw_data = request.get_data(as_text=True)
            print(f'原始请求数据: {raw_data}')
            if raw_data and raw_data.strip():
                try:
                    data = json.loads(raw_data)
                    print(f'从原始数据解析的JSON: {data}')
                except json.JSONDecodeError as je:
                    print(f'JSON解析错误: {str(je)}')
                    return jsonify({
                        'status': 'error',
                        'message': f'JSON格式错误: {str(je)}'
                    }), 400
        
        if not data:
            print('错误: 请求数据为空')
            return jsonify({
                'status': 'error',
                'message': '请求数据为空'
            }), 400

        # 获取参数
        try:
            board_name = data.get('boardName', '').strip() if data.get('boardName') else ''
            business_model = data.get('businessModel', '').strip() if data.get('businessModel') else ''
            ip = data.get('ip', '').strip() if data.get('ip') else ''
            code_path = data.get('codePath', '').strip() if data.get('codePath') else ''
            user = data.get('user', 'guest')
            
            print(f'解析参数 - 单板名称: {board_name}, 业务模型: {business_model}, IP: {ip}, 代码路径: {code_path}, 用户: {user}')
        except Exception as param_error:
            print(f'参数解析错误: {str(param_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'参数解析失败: {str(param_error)}'
            }), 400

        # 验证必填参数
        if not board_name:
            print('错误: 单板名称不能为空')
            return jsonify({
                'status': 'error',
                'message': '单板名称不能为空'
            }), 400
        
        if not code_path:
            print('错误: 代码路径不能为空')
            return jsonify({
                'status': 'error',
                'message': '代码路径不能为空'
            }), 400

        # 构建脚本路径：{code_path}/boardassemble/06_build_system/gen_one_board.sh
        try:
            code_path_obj = Path(code_path)
            script_dir = code_path_obj / 'boardassemble' / '06_build_system'
            script_path = script_dir / 'gen_one_board.sh'
            
            print(f'代码路径: {code_path}')
            print(f'脚本目录: {script_dir}')
            print(f'脚本路径: {script_path}')
            print(f'脚本是否存在: {script_path.exists()}')
        except Exception as path_error:
            print(f'路径构建错误: {str(path_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'路径构建失败: {str(path_error)}'
            }), 500
        
        if not script_path.exists():
            error_msg = f'脚本文件不存在: {script_path}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 404

        # 确保脚本路径是绝对路径
        script_abs_path = script_path.resolve()  # 使用 resolve() 获取绝对路径并解析符号链接
        
        # 再次检查脚本文件是否存在（使用绝对路径）
        if not script_abs_path.exists():
            error_msg = f'脚本文件不存在: {script_abs_path}（绝对路径）'
            print(f'错误: {error_msg}')
            # 列出目录内容以便调试
            try:
                if script_dir.exists():
                    dir_contents = list(script_dir.iterdir())
                    print(f'脚本目录内容: {[str(p.name) for p in dir_contents]}')
            except Exception as list_error:
                print(f'无法列出目录内容: {str(list_error)}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 404
        
        # 检查脚本是否可执行
        if not os.access(script_abs_path, os.X_OK):
            print(f'警告: 脚本文件不可执行，尝试添加执行权限: {script_abs_path}')
            try:
                os.chmod(script_abs_path, 0o755)
                print(f'已添加执行权限: {script_abs_path}')
            except Exception as chmod_error:
                print(f'添加执行权限失败: {str(chmod_error)}')
                # 即使添加权限失败，也继续尝试执行

        # 执行命令：必须在脚本所在目录执行，使用 bash
        try:
            print(f'准备执行脚本: {script_abs_path}，参数: {board_name}')
            print(f'工作目录: {script_dir}')
            print(f'脚本绝对路径: {script_abs_path}')
            print(f'脚本文件大小: {script_abs_path.stat().st_size} 字节')
            
            # 重要：必须先 cd 到脚本所在目录，再执行脚本
            # 使用 bash 执行，确保 bash 语法（如 [[ ]]）能正常工作
            # 设置环境变量，确保子脚本也使用 bash 执行
            script_name = script_abs_path.name  # 获取脚本文件名
            # 在命令中先 cd 到脚本目录，然后使用 bash 执行脚本
            # 通过设置 SHELL 环境变量，确保子脚本也使用 bash
            cmd = f'cd "{script_dir}" && SHELL=/bin/bash bash ./{script_name} {board_name}'
            
            print(f'执行命令: {cmd}')
            print(f'工作目录: {script_dir}')
            print(f'脚本文件名: {script_name}')
            print(f'脚本绝对路径: {script_abs_path}')
            
            # 脚本中有交互式输入（read -p "是否覆盖? (y/N): "），需要提供输入
            # 使用 subprocess.Popen 来正确处理交互式输入
            # 关键：cwd 设置为脚本目录，确保脚本中的相对路径能正确工作
            # 设置环境变量，确保子脚本也使用 bash 执行
            import os as os_module
            env = os_module.environ.copy()
            env['SHELL'] = '/bin/bash'  # 设置默认 shell 为 bash
            env['BASH_ENV'] = ''  # 清除 BASH_ENV，避免干扰
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(script_dir),  # 在脚本所在目录执行，这样脚本中的相对路径能正确工作
                stdin=subprocess.PIPE,  # 提供标准输入管道
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                env=env  # 使用修改后的环境变量
            )
            
            # 自动提供 "y\n" 来确认覆盖操作
            try:
                stdout, stderr = process.communicate(input='y\n', timeout=300)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                returncode = process.returncode
                raise subprocess.TimeoutExpired(cmd, 300, stdout, stderr)
            
            # 创建类似 subprocess.run 返回的结果对象
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            
            result = Result(returncode, stdout, stderr)
            
            print(f'脚本执行完成，返回码: {result.returncode}')
            print(f'标准输出长度: {len(result.stdout)} 字符')
            print(f'错误输出长度: {len(result.stderr)} 字符')
            
            # 如果标准输出太长，只打印前1000个字符
            stdout_preview = result.stdout[:1000] if len(result.stdout) > 1000 else result.stdout
            stderr_preview = result.stderr[:1000] if len(result.stderr) > 1000 else result.stderr
            print(f'标准输出预览:\n{stdout_preview}')
            if result.stderr:
                print(f'错误输出预览:\n{stderr_preview}')
            
        except subprocess.TimeoutExpired:
            error_msg = '脚本执行超时（超过5分钟）'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500
        except Exception as exec_error:
            error_msg = f'脚本执行失败: {str(exec_error)}'
            print(f'错误: {error_msg}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500

        # 根据返回码判断执行结果
        if result.returncode == 0:
            print('=== 框架代码生成成功 ===')
            return jsonify({
                'status': 'success',
                'message': '框架代码生成完成',
                'data': {
                    'board_name': board_name,
                    'script_path': str(script_path),
                    'output': result.stdout,
                    'return_code': result.returncode
                }
            }), 200
        else:
            error_msg = f'脚本执行失败，返回码: {result.returncode}'
            if result.stderr:
                error_msg += f'\n错误信息: {result.stderr}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': {
                    'board_name': board_name,
                    'script_path': str(script_path),
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                }
            }), 500

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f'框架代码生成失败: {str(e)}'
        print(f'框架代码生成错误: {error_msg}')
        print(f'错误堆栈: {error_trace}')
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__
        }), 500


def generate_config():
    """
    配置参数生成
    执行 shell 脚本生成配置参数
    """
    try:
        print('=== 开始配置参数生成 ===')
        print(f'请求方法: {request.method}')
        print(f'请求URL: {request.url}')
        print(f'Content-Type: {request.content_type}')
        
        # 安全地获取JSON数据
        import json
        data = None
        try:
            data = request.get_json(force=True, silent=True)
            print(f'通过 get_json 获取的数据: {data}')
        except Exception as e1:
            print(f'get_json 失败，尝试使用 request.data: {str(e1)}')
        
        if data is None:
            raw_data = request.get_data(as_text=True)
            print(f'原始请求数据: {raw_data}')
            if raw_data and raw_data.strip():
                try:
                    data = json.loads(raw_data)
                    print(f'从原始数据解析的JSON: {data}')
                except json.JSONDecodeError as je:
                    print(f'JSON解析错误: {str(je)}')
                    return jsonify({
                        'status': 'error',
                        'message': f'JSON格式错误: {str(je)}'
                    }), 400
        
        if not data:
            print('错误: 请求数据为空')
            return jsonify({
                'status': 'error',
                'message': '请求数据为空'
            }), 400

        # 获取参数
        try:
            board_name = data.get('boardName', '').strip() if data.get('boardName') else ''
            business_model = data.get('businessModel', '').strip() if data.get('businessModel') else ''
            ip = data.get('ip', '').strip() if data.get('ip') else ''
            code_path = data.get('codePath', '').strip() if data.get('codePath') else ''
            user = data.get('user', 'guest')
            
            print(f'解析参数 - 单板名称: {board_name}, 业务模型: {business_model}, IP: {ip}, 代码路径: {code_path}, 用户: {user}')
        except Exception as param_error:
            print(f'参数解析错误: {str(param_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'参数解析失败: {str(param_error)}'
            }), 400

        # 验证必填参数
        if not board_name:
            print('错误: 单板名称不能为空')
            return jsonify({
                'status': 'error',
                'message': '单板名称不能为空'
            }), 400
        
        if not business_model:
            print('错误: 业务模型不能为空')
            return jsonify({
                'status': 'error',
                'message': '业务模型不能为空'
            }), 400
        
        if not code_path:
            print('错误: 代码路径不能为空')
            return jsonify({
                'status': 'error',
                'message': '代码路径不能为空'
            }), 400

        # 构建脚本路径：{code_path}/boardassemble/51_gen_pri_data/template_render/run_template_render.sh
        try:
            code_path_obj = Path(code_path)
            script_dir = code_path_obj / 'boardassemble' / '51_gen_pri_data' / 'template_render'
            script_path = script_dir / 'run_template_render.sh'
            
            print(f'代码路径: {code_path}')
            print(f'脚本目录: {script_dir}')
            print(f'脚本路径: {script_path}')
            print(f'脚本是否存在: {script_path.exists()}')
        except Exception as path_error:
            print(f'路径构建错误: {str(path_error)}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'路径构建失败: {str(path_error)}'
            }), 500
        
        if not script_path.exists():
            error_msg = f'脚本文件不存在: {script_path}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 404

        # 确保脚本路径是绝对路径
        script_abs_path = script_path.resolve()
        
        # 再次检查脚本文件是否存在（使用绝对路径）
        if not script_abs_path.exists():
            error_msg = f'脚本文件不存在: {script_abs_path}（绝对路径）'
            print(f'错误: {error_msg}')
            # 列出目录内容以便调试
            try:
                if script_dir.exists():
                    dir_contents = list(script_dir.iterdir())
                    print(f'脚本目录内容: {[str(p.name) for p in dir_contents]}')
            except Exception as list_error:
                print(f'无法列出目录内容: {str(list_error)}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 404
        
        # 检查脚本是否可执行
        if not os.access(script_abs_path, os.X_OK):
            print(f'警告: 脚本文件不可执行，尝试添加执行权限: {script_abs_path}')
            try:
                os.chmod(script_abs_path, 0o755)
                print(f'已添加执行权限: {script_abs_path}')
            except Exception as chmod_error:
                print(f'添加执行权限失败: {str(chmod_error)}')
                # 即使添加权限失败，也继续尝试执行

        # 执行命令：./run_template_render.sh [单板名称] [单板模型] gen_all tmp_true
        try:
            script_name = script_abs_path.name
            # 命令格式：./run_template_render.sh [单板名称] [单板模型] gen_all tmp_true
            cmd = f'cd "{script_dir}" && SHELL=/bin/bash bash ./{script_name} {board_name} {business_model} gen_all tmp_true'
            
            print(f'执行命令: {cmd}')
            print(f'工作目录: {script_dir}')
            print(f'脚本文件名: {script_name}')
            print(f'脚本绝对路径: {script_abs_path}')
            
            # 设置环境变量，确保子脚本也使用 bash 执行
            import os as os_module
            env = os_module.environ.copy()
            env['SHELL'] = '/bin/bash'
            env['BASH_ENV'] = ''
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(script_dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )
            
            # 执行脚本（不需要交互式输入）
            try:
                stdout, stderr = process.communicate(timeout=300)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                returncode = process.returncode
                raise subprocess.TimeoutExpired(cmd, 300, stdout, stderr)
            
            # 创建类似 subprocess.run 返回的结果对象
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            
            result = Result(returncode, stdout, stderr)
            
            print(f'脚本执行完成，返回码: {result.returncode}')
            print(f'标准输出长度: {len(result.stdout)} 字符')
            print(f'错误输出长度: {len(result.stderr)} 字符')
            
            # 如果标准输出太长，只打印前1000个字符
            stdout_preview = result.stdout[:1000] if len(result.stdout) > 1000 else result.stdout
            stderr_preview = result.stderr[:1000] if len(result.stderr) > 1000 else result.stderr
            print(f'标准输出预览:\n{stdout_preview}')
            if result.stderr:
                print(f'错误输出预览:\n{stderr_preview}')
            
        except subprocess.TimeoutExpired:
            error_msg = '脚本执行超时（超过5分钟）'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500
        except Exception as exec_error:
            error_msg = f'脚本执行失败: {str(exec_error)}'
            print(f'错误: {error_msg}')
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 500

        # 根据返回码判断执行结果
        if result.returncode == 0:
            print('=== 配置参数生成成功 ===')
            return jsonify({
                'status': 'success',
                'message': '配置参数生成完成',
                'data': {
                    'board_name': board_name,
                    'business_model': business_model,
                    'script_path': str(script_path),
                    'output': result.stdout,
                    'return_code': result.returncode
                }
            }), 200
        else:
            error_msg = f'脚本执行失败，返回码: {result.returncode}'
            if result.stderr:
                error_msg += f'\n错误信息: {result.stderr}'
            print(f'错误: {error_msg}')
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': {
                    'board_name': board_name,
                    'business_model': business_model,
                    'script_path': str(script_path),
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                }
            }), 500

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f'配置参数生成失败: {str(e)}'
        print(f'配置参数生成错误: {error_msg}')
        print(f'错误堆栈: {error_trace}')
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'error_type': type(e).__name__
        }), 500
