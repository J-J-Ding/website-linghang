import os
import json
import base64
import hashlib
import sqlite3
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from api_utils import Get_UACtoken
from typing import Union

SECRET_KEY = 'secret-key-bofenruanjiankaifayibu-linghang-ai'  # 必须与前端一致

def decrypt_password(encrypted_password: str, secret_key: str) -> Union[str , None]:
    # Base64 解码
    data = base64.b64decode(encrypted_password)
    
    # 检查是否以 'Salted__' 开头
    assert data[:8] == b'Salted__'

    salt = data[8:16]
    encrypted = data[16:]

    # 使用 EVP_BytesToKey 生成 key & iv（OpenSSL 使用的方式）
    def derive_key_iv(password: bytes, salt: bytes, key_len: int, iv_len: int):
        d = d_i = b''
        while len(d) < key_len + iv_len:
            d_i = hashlib.md5(d_i + password + salt).digest()
            d += d_i
        return d[:key_len], d[key_len:key_len+iv_len]

    key, iv = derive_key_iv(secret_key.encode('utf-8'), salt, 32, 16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)

    try:
        # 去除 PKCS7 填充
        decrypted = unpad(decrypted, AES.block_size)
        return decrypted.decode('utf-8')
    except Exception as e:
        print("Padding error or decryption failed:", e)
        return None
    
def Login():
    # 检查请求方法
    if request.method != 'POST':
        return jsonify({
            "code": 405,
            "message": "Method Not Allowed"
        }), 405
    
    # 检查Content-Type
    if not request.is_json:
        return jsonify({
            "code": 400,
            "message": "请求必须为JSON格式"
        }), 400
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "用户名或密码不能为空"
            }), 400

        decrypted_password = decrypt_password(password, SECRET_KEY)
        if not decrypted_password:
            return jsonify({'code': 400, 'message': '密码解密失败'})
        
        # 获取token
        uactoken = Get_UACtoken(username, decrypted_password)
        
        # 检查token是否为空
        if not uactoken:  # 这里会检查None和空字符串''
            return jsonify({
                "code": 401,
                "message": "用户名或密码错误"
            }), 401

        # OTP 用户注册校验：通过 username 查询 fieldteammembers
        otp_url = f"https://otp.zx.zte.com.cn//api/organization/fieldteammembers/{username}"
        try:
            otp_resp = requests.get(otp_url, timeout=8)
            otp_resp.raise_for_status()
            otp_data = otp_resp.json()
        except Exception as e:
            print(f"OTP 用户查询异常: {str(e)}")
            return jsonify({
                "code": 502,
                "message": "用户信息校验服务异常，请稍后重试"
            }), 502

        otp_bo = otp_data.get("bo", {})
        if not otp_bo:
            return jsonify({
                "code": 403,
                "message": "请联系管理员陈雷/汪浩进行注册"
            }), 403

        return jsonify({
            "code": 200,
            "message": "登录成功",
            "username": username,
            "uactoken": uactoken,
        })

    except Exception as e:
        print(f"登录处理异常: {str(e)}")
        return jsonify({
            "code": 500,
            "message": "服务器内部错误"
        }), 500

# 数据库路径
DB_PATH = '../data/visit.db'

def API_Visit_set():
    if request.method != 'POST':
        return jsonify({"code": 405, "message": "Method Not Allowed"}), 405

    if not request.is_json:
        return jsonify({"code": 400, "message": "请求必须为JSON格式"}), 400

    try:
        data = request.get_json()
        page_now = data.get('page_now', '/unknown')
        page_before = data.get('page_before', '')
        user_id = data.get('user_id', 'guest')
        user_agent = data.get('user_agent', '')
        timestamp = data.get('timestamp')

        # 写入数据库
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO visit
            (page_now, page_before, user_id, user_agent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (page_now, page_before, user_id, user_agent, timestamp))

        conn.commit()
        conn.close()

        return jsonify({"code": 200, "message": "统计上报成功"})

    except Exception as e:
        print(f"访问统计处理异常: {str(e)}")
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500

def API_Visit_get():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 启用字典式访问
        cur = conn.cursor()

        # 查询所有记录，按客户端时间倒序
        cur.execute('''
            SELECT 
                ROWID,    
                page_now,
                user_id, 
                timestamp
            FROM visit
            ORDER BY ROWID
        ''')

        rows = cur.fetchall()
        conn.close()

        # 转为字典列表
        data = [dict(row) for row in rows]

        return jsonify({
            "code": 200,
            "message": "success",
            "data": data
        })

    except Exception as e:
        print(f"读取访问日志失败: {str(e)}")
        return jsonify({
            "code": 500,
            "message": "服务器内部错误"
        }), 500
    
def test_Login():
    encrypted_password = 'U2FsdGVkX195dX1n7nVqApbUaS1TQ06MzqQn6wOM0E8='
    decrypted_password = decrypt_password(encrypted_password, SECRET_KEY)
    print(f"解密：{decrypted_password}")

if __name__ == "__main__":
    test_Login()