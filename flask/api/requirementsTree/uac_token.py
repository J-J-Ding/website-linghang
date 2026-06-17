"""
需求树模块专用的 UAC token 获取
独立于 componentTree/icenter_token，功能隔离
AES 加解密逻辑内联，不依赖外部 aes 模块
"""

import os
import re
import base64
import socket
import json
import hashlib
import logging

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

logger = logging.getLogger(__name__)

AES_KEY = "asdasdasdasdasdb"


class _AESECB:
    """AES-ECB 加解密（pkcs7 填充），等价于 knowledge_dashboard/aes.py 的 EncryptDate"""

    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(self.key.encode("utf-8"), AES.MODE_ECB)

    def encrypt(self, plaintext):
        padded = pad(plaintext.encode("utf-8"), AES.block_size, style="pkcs7")
        return str(base64.b64encode(self.cipher.encrypt(padded)), encoding="utf-8")

    def decrypt(self, ciphertext):
        raw = base64.decodebytes(ciphertext.encode("utf-8"))
        decrypted = self.cipher.decrypt(raw).decode("utf-8")
        return decrypted[:-ord(decrypted[-1])]


def get_host_ip():
    """获取本机出口 IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"get_host_ip 失败: {e}")
        s.close()
        return ""


def get_token(emp_no, passwd, loginsyscode, originsyscode):
    """调用 UAC 认证接口获取 token"""
    url = "https://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
    clientip = get_host_ip()
    text = {
        "account": emp_no,
        "passWord": passwd,
        "loginClientIp": clientip,
        "loginSystemCode": loginsyscode,
        "originSystemCode": originsyscode,
        "other": {
            "networkArea": "1",
            "networkAccessType": "1",
        },
        "verifyCode": hashlib.md5(
            str(emp_no + passwd + clientip + loginsyscode + originsyscode).encode(encoding='utf-8')
        ).hexdigest(),
    }
    headers = {'Content-type': 'application/json'}
    resp = requests.post(url, data=json.dumps(text), headers=headers)
    return resp.json()


def token_ok(token_status, emp_no, passwd, loginsyscode, originsyscode):
    """
    获取 UAC token
    返回: (success: bool, token: str)
    """
    if token_status == 0:
        ret = get_token(emp_no, passwd, loginsyscode, originsyscode)
        if ret.get('code', {}).get('code') == '0000' and ret.get('bo', {}).get('code') == '0000':
            token = ret.get('other', {}).get('token', '')
            return True, token
        else:
            logger.error(f"UAC 认证失败: {ret}")
            return False, ""
    else:
        return True, ""


def get_uac_token():
    """
    从环境变量获取 UAC 认证信息，返回 (user_num, token)
    失败返回 (None, None)
    """
    en_httppassword = os.environ.get('PASSWORD', '')
    X_Emp_No = os.environ.get('USERNAME', '')
    if not en_httppassword or not X_Emp_No:
        logger.error("缺少环境变量 USERNAME 或 PASSWORD")
        return None, None
    # eg = _AESECB(AES_KEY)
    # passwd = eg.decrypt(en_httppassword)
    passwd = en_httppassword
    X_Emp_No = re.sub(r"\D", "", X_Emp_No)
    loginsyscode = 'Portal'
    originsyscode = ''
    token_status = 0
    _, token = token_ok(token_status, X_Emp_No, passwd, loginsyscode, originsyscode)
    if not token:
        logger.error("获取 UAC token 失败")
        return None, None
    return X_Emp_No, token
