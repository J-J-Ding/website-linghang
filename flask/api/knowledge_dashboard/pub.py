from flask import jsonify


def pub_get_ratio(dividend, divisor, decimal_places=2):
    """计算比率，返回百分比数值（保留指定小数位数）"""
    if divisor == 0:
        return 0
    else:
        ratio = dividend / divisor
        percentage = round(ratio * 100, decimal_places)
        return percentage


def pub_ok(data):
    """返回成功的 JSON 响应"""
    return jsonify({"result": True, "code": 0, "errorCode": "0", "msg": "操作成功", "body": {"data": data}})


def pub_bad(msg, http_code=400):
    """返回错误的 JSON 响应"""
    return (jsonify({"result": False, "code": 1, "errorCode": "1", "msg": msg, "body": {"data": None}}), http_code)