from flask import request, jsonify

def Receive_message():
    data = request.get_json()
    message = data.get('message')
    print("收到消息:", message)
    return jsonify({"status": "success"})

def Send_message():
    return jsonify({"message": "hello world!"})

def Handle_submit():
    data = request.get_json()
    print("收到表单数据：")
    print(data)
    return jsonify({"status": "success", "message": "数据已接收"})
