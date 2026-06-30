#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
import socket
import json
import getpass
import hashlib


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(e)
        s.close()
        return ""

def token_ok(token_status, X_Emp_No, passwd, loginsyscode, originsyscode):
    if token_status == 0:
        ret = get_token(X_Emp_No, passwd, loginsyscode, originsyscode)
        #dynpwd = input("请输入动态码：")
        #X_Auth_Value = get_token(passwd,dynpwd)['other']['token']
        if ret['code']['code'] == '0000' and ret['bo']['code'] == '0000' :
            X_Auth_Value = ret['other']['token']
            token_status = 1
            return True, X_Auth_Value
        else:
            return False, ""
    else:
        return True, ""


def get_token(X_Emp_No, passwd, loginsyscode, originsyscode):
    #url = "https://uac.zte.com.cn/uactoken/auth/token/verify.serv"
    url = "https://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
    clientip = get_host_ip()

    text =\
    {
        "account": X_Emp_No,
        "passWord": passwd,
        "loginClientIp": clientip,
        "loginSystemCode": loginsyscode,
        "originSystemCode": originsyscode,
        "other": {
            "networkArea":'1',
            "networkAccessType":'1'
        },
        "verifyCode":hashlib.md5(str(X_Emp_No+passwd+clientip+loginsyscode+originsyscode).encode(encoding='utf-8')).hexdigest()    
    }
    headers = {'Content-type': 'application/json'}
    #content = requests.post(url,json=text,headers=headers)
    content = requests.post(url,data=json.dumps(text),headers=headers)
    #print(content.text)
    return content.json()