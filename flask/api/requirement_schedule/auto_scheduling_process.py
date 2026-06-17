import pymysql.cursors
try:
    from requirement_schedule import db_mapping_config
except ImportError:
    import db_mapping_config
from flask import Flask, request, jsonify
import pymysql.cursors
import sys
import subprocess
import random
import copy
from collections import defaultdict
import pymysql.cursors
import base64
import json
import hashlib
import requests
import traceback
from socket import socket, AF_INET, SOCK_DGRAM
import pymysql
import pymysql.cursors
from pymysql.err import OperationalError, ProgrammingError, DataError
import datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from chinese_calendar import is_workday
from datetime import timedelta
import math
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
@app.route('/info', methods=['POST'])
def search():
    """
    前端传入4个参数：需求预规划(必填)，工作项类型(必填),领域(可多选),团队(可选)
    开始后续流程 排序，评估工作量，采纳pr(第一次评估)，自动排期
    :return:
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return api_response(400, "未接收到JSON数据或格式错误"), 400
    # 获取查询参数
    requirement_preplanning = json_data.get("requirement_preplanning", None)  # 需求预规划
    work_type = json_data.get("work_type", None)  # 工作项类型
    domain = json_data.get("domain", None)  # 领域
    team = json_data.get("team", None)  # 团队
    username = json_data.get("username", None)    # 用户名
    password = json_data.get("encrypted_password", None)   # 密码
    # 判断必传参数
    if not requirement_preplanning:
        return api_response(400, "未填写requirement_preplanning参数"), 400
    if not work_type:
        return api_response(400, "未填写work_type参数"), 400
    if not username:
        return api_response(400, "无用户名参数"), 400
    if not password:
        return api_response(400, "无密码参数"), 400
    try:
        # 用户密码加密
        encrypted_password = base64_encode(password)
        # pr排序
        pr_sort(team, domain, requirement_preplanning, work_type)
        print("=========================================")
        print("================排序已完成=================")
        print("=========================================")
        # PR预计开发工作量评估
        update_db_data(team, domain, requirement_preplanning, work_type)
        print("=========================================")
        print("================工作量已完成================")
        print("=========================================")
        # 评估PR是否可纳入（第一优先级）
        task_assignment(team, domain, requirement_preplanning, work_type, username, encrypted_password)
        print("=========================================")
        print("================评估已完成=================")
        print("=========================================")
        # PR开发日期自动排期（第一优先级）
        PR_allocate(team, domain, requirement_preplanning, work_type, username, encrypted_password)
        print("=========================================")
        print("================排期已完成=================")
        print("=========================================")
        return {"code": "200", "msg": "yes"}
    except Exception:
        return {"code": "400", "msg": str(traceback.print_exc())}

def api_response(code: int, msg: str, data: dict = None):
    return jsonify({
        "code": code,       # 状态码
        "msg": msg,         # 提示信息
        "data": data,       # 数据
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 时间戳
    })

def base64_encode(password: str) -> str:
    """
    对字符串（密码）进行 Base64 编码
    :param password: 原始密码字符串
    :return: Base64 编码后的字符串
    """
    # 先将字符串转为 bytes 类型（Base64 处理的是字节）
    password_bytes = password.encode('utf-8')
    # 进行 Base64 编码
    encoded_bytes = base64.b64encode(password_bytes)
    # 将 bytes 转回字符串（便于存储/传输）
    encoded_str = encoded_bytes.decode('utf-8')
    return encoded_str

def match_data(select_sql, cursor, parameter_tuple):
    """
    查询数据库
    :return:None
    """
    cursor.execute(select_sql, parameter_tuple)
    data_lst = cursor.fetchall()
    return data_lst

def get_view_feature(cursor):
    """
    通过领域获得同领域下所有子特性以及优先级,并转换为字典{"特性标识":"优先级"}
    :param cursor: 游标
    :return:feature_priority_dict
    """
    feature_priority_dict = {}
    select_sql = f"select * from feature_view_table"
    cursor.execute(select_sql)
    feature_data_lst = cursor.fetchall()
    for each_feature in feature_data_lst:
        identifier = each_feature.get("feature_identifier")
        priority = each_feature.get("priority")
        if not identifier or not priority:
            continue
        feature_priority_dict.setdefault(identifier, priority)
    return feature_priority_dict

def judge_priority(belong_feature_catalog, cursor, feature_priority_dict, feature_identifier, row_each,
                   sql_priority):
    """
    修改优先级
    :param belong_feature_catalog: 特性属性分类
    :param domain: 领域
    :param excel_priority_dict: excel解析数据
    :param feature_identifier: 特性标识
    :param row_each: 数据库数据（行）
    :param sql_priority: 数据库数据优先级
    :return: None
    """
    if belong_feature_catalog == "01-标准" and feature_identifier:
        priority = feature_priority_dict.get(feature_identifier, None)
        if priority:
            if float(priority) != float(sql_priority):
                update_sql = f'''update requirement_schedule_table set priority=%s where id=%s'''
                cursor.execute(update_sql, (str(int(float(priority))), row_each.get("id")))
                print(f"id={row_each.get('id')} 的数据修改成功")

def pr_sort(team, domain, requirement_preplanning, work_type):
    """
    前端传入4个参数：需求预规划(必填)，工作项类型(必填),领域(可多选),团队(可选)
    PR优先级排序
    规则：市场需求排序+特性优先级 ，综合判断PR的排序。
         标准特性优先级排序原则：根据复杂度、有外部依赖、业务流程判断，PR根据标准特性标识获取对应的排序。
         非标准特性，根据PR优先级排序规则判断。
    目标：刷新所有标准PR的优先级。如果库中匹配失败，则保持默认值。
    team:团队
    domain:领域
    requirement_preplanning：需求预规划
    work_type：工作项类型
    :return:
    """
    # 六种情况：
    # 1、多领域无团队
    # 2、多领域多团队/多领域单团队(只看团队)
    # 3、单领域单/多团队
    # 4、单领域无团队
    # 5、无领域单/多团队
    # 6、无领域无团队
    db = None
    cursor = None
    try:
        # Bug7修复：domain/team 可能为 None，统一转为 list
        domain = domain or []
        team = team or []

        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        results_data_lst = []

        # Bug1修复：原条件 len(domain) >= 2 漏掉单领域无团队(case4)，改为 domain and not team
        # 1、多领域无团队  4、单领域无团队
        if domain and not team:
            # Bug3修复：WHERE 条件用 AND，不能用逗号
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND domain=%s")
            for each_domain in domain:
                parameter_tuple = (requirement_preplanning, work_type, each_domain)
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # Bug2修复：原 (len(domain) >= 2 or len(domain)) <= 0 因运算符优先级永远为 False（多领域有团队走不进来）
        # 正确逻辑：多领域有团队(case2) 或 无领域有团队(case5) → 只按团队查
        # 2、多领域多团队/多领域单团队(只看团队)  5、无领域单/多团队
        elif (len(domain) >= 2 or len(domain) == 0) and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team)
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 3、单领域单/多团队
        elif len(domain) == 1 and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s AND domain=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team, domain[0])
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 6、无领域无团队
        elif not domain and not team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s")
            parameter_tuple = (requirement_preplanning, work_type)
            data_lst = match_data(select_sql, cursor, parameter_tuple)
            results_data_lst += data_lst

        # Bug6修复：pr_sort 不是路由函数，不能 return api_response()；改为抛出异常，由调用方统一处理
        if not results_data_lst:
            raise ValueError("数据库暂无匹配数据，请确认需求预规划/工作项类型后重试")

        for row_each in results_data_lst:
            # 获取特性标识与优先级
            feature_priority_dict = get_view_feature(cursor)
            belong_feature_catalog = row_each.get("belong_feature_catalog", None)  # 特性属性分类
            feature_identifier = row_each.get("feature_identifier", None)  # 特性标识
            sql_priority = row_each.get("priority", None)  # 优先级
            # 获取每行数据的特性属性分类，特性标识，优先级。将特性属性分类为‘01-标准’和特性标识不为空的进行excel同领域查找优先级，
            judge_priority(belong_feature_catalog, cursor, feature_priority_dict, feature_identifier, row_each,
                           sql_priority)
        db.commit()
        print("===== 所有数据优先级已更新，事务已提交 =====")
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        print(f"数据库操作异常，已回滚事务，错误信息：{str(e)}")
        raise  # 向上抛出，让调用方感知错误
    except Exception as e:
        if db:
            db.rollback()
        print(f"程序运行异常，已回滚事务，错误信息：{str(e)}")
        raise  # 向上抛出，让调用方感知错误（包括 ValueError "暂无匹配数据"）
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def update_db_data(team, domain, requirement_preplanning, work_type):
    """
    函数：填写所有PR的预计开发工作量。如果已有值，则继承；如果没有值，则从库中查找回填；如果查找失败，则填写默认值。
    :return:None
    """
    db = None
    cursor = None
    try:
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        update_sql = f'''update requirement_schedule_table set estimated_dev_workload=%s where id=%s'''
        # 六种情况：
        # 1、多领域无团队
        # 2、多领域多团队/多领域单团队(只看团队)
        # 3、单领域单/多团队
        # 4、单领域无团队
        # 5、无领域单/多团队
        # 6、无领域无团队
        results_data_lst = []
        # 1、多领域无团队  4、单领域无团队
        if domain and not team:
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND domain=%s")
            for each_domain in domain:
                parameter_tuple = (requirement_preplanning, work_type, each_domain)
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 正确逻辑：多领域有团队(case2) 或 无领域有团队(case5) → 只按团队查
        # 2、多领域多团队/多领域单团队(只看团队)  5、无领域单/多团队
        elif (len(domain) >= 2 or len(domain) == 0) and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team)
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 3、单领域单/多团队
        elif len(domain) == 1 and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s AND domain=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team, domain[0])
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 6、无领域无团队
        elif not domain and not team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s")
            parameter_tuple = (requirement_preplanning, work_type)
            data_lst = match_data(select_sql, cursor, parameter_tuple)
            results_data_lst += data_lst

        # Bug6修复：pr_sort 不是路由函数，不能 return api_response()；改为抛出异常，由调用方统一处理
        if not results_data_lst:
            raise ValueError("数据库暂无匹配数据，请确认需求预规划/工作项类型后重试")
        # 获取需求清单表中数据
        feature_workload_dict = get_workload_feature(cursor)
        process_data(cursor, results_data_lst, feature_workload_dict, update_sql)
        db.commit()
        print("===== 所有开发工作量评估已更新，事务已提交 =====")
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        print(f"数据库操作异常，已回滚事务，错误信息：{str(e)}")
    except Exception as e:
        if db:
            db.rollback()
        print(f"程序运行异常，已回滚事务，错误信息：{str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
def get_workload_feature(cursor):
    """
    通过领域获得同领域下所有子特性以及预计开发工作量和开发工作量,并转换为字典{"特性标识": , "预计开发工作量": ,"开发工作量": }
    :param cursor: 游标
    :return:feature_workload_dict
    """
    feature_workload_dict = {}
    select_sql = f"select * from feature_view_table"
    cursor.execute(select_sql)
    feature_data_lst = cursor.fetchall()
    for each_feature in feature_data_lst:
        identifier = each_feature.get("feature_identifier")
        dev_workload = each_feature.get("dev_workload")
        estimated_dev_workload = each_feature.get("estimated_dev_workload")
        if not identifier or not dev_workload or not estimated_dev_workload:
            continue
        feature_workload_dict.setdefault(identifier, {"dev_workload":dev_workload, "estimated_dev_workload":estimated_dev_workload})
    return feature_workload_dict

def process_data(cursor, results_data_lst, feature_workload_dict, update_sql):
    """
    判断计算工作量
    :param cursor: 数据库游标
    :param results_data_lst: 需求清单数据
    :param feature_workload_dict: 特性工作量字典
    :param update_sql: 更新的sql语句
    :return:
    """
    if feature_workload_dict:
        # 每个需求清单中的数据填写
        for each_dict in results_data_lst:
            estimated_dev_workload, feature_attribute, feature_identifier, id_num, reuse_degree = get_data(each_dict)
            feature_dict = feature_workload_dict.get(feature_identifier, None)
            # 数据库预计开发量不为空跳过   数据清单中没有特性属性跳过
            if estimated_dev_workload or not feature_dict:
                continue
            workload = None
            PR_work_load = None
            if reuse_degree == "全代码" and (feature_attribute == "全新特性" or feature_attribute == "特性修改" or not feature_attribute):
                workload = feature_dict.get("estimated_dev_workload", None)
            elif reuse_degree == "微范式" and (feature_attribute == "特性修改" or feature_attribute == "特性不修改" or not feature_attribute):
                workload = feature_dict.get("dev_workload", None)
            elif reuse_degree == "配置化" and (feature_attribute == "特性不修改" or not feature_attribute):
                workload = feature_dict.get("dev_workload", None)
            elif reuse_degree == "零代码" and (feature_attribute == "特性不修改" or not feature_attribute):
                workload = feature_dict.get("dev_workload", None)
            # 判断是否存在
            if is_valid_workload(workload):
                PR_work_load = workload_calculation(feature_attribute, reuse_degree, workload, PR_work_load)
            if PR_work_load:
                cursor.execute(update_sql, (str(PR_work_load), id_num))
                print(f"第{id_num}条数据完成更新")

def get_data(each_dict):
    """
    获取数据中的key值
    :param each_dict: 数据清单每行数据
    :return: estimated_dev_workload, feature_attribute, feature_identifier, id_num, reuse_degree
    """
    estimated_dev_workload = each_dict.get("estimated_dev_workload", None)  # 预计开发工作量
    feature_identifier = each_dict.get("feature_identifier", None)  # 特性标识
    id_num = each_dict.get("id", None)
    reuse_degree = each_dict.get("reuse_degree", None)  # 复用程度
    feature_attribute = each_dict.get("feature_attribute", None)  # 特性属性
    return estimated_dev_workload, feature_attribute, feature_identifier, id_num, reuse_degree

def workload_calculation(feature_attribute, reuse_degree, workload, PR_work_load):
    """
    复用程度判断工作量
    :param PR_work_load: pr工作量
    :param feature_attribute: 特性属性
    :param reuse_degree: 复用程度
    :param workload: excel工作量
    :return: PR_work_load
    """
    workload_num = float(workload)
    if reuse_degree == "全代码" and not feature_attribute:
        feature_attribute = "特性修改"
    elif reuse_degree == "微范式" and not feature_attribute:
        feature_attribute = "特性修改"
    elif reuse_degree == "配置化" and not feature_attribute:
        feature_attribute = "特性不修改"
    elif reuse_degree == "零代码" and not feature_attribute:
        feature_attribute = "特性不修改"
    # 优先获取系数，无则按规则计算
    coeff_key = f"{reuse_degree}_{feature_attribute}" if (reuse_degree and feature_attribute) else None
    coefficient = db_mapping_config.coefficient_dict.get(coeff_key, None)
    if coefficient:
        PR_work_load = workload_num * coefficient
    return PR_work_load

def is_valid_workload(val):
    """
    excel工作量是否为空
    :param val: 参数
    :return: True，False
    """
    if not val:
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False

def total_manpower_team(results_data_lst):
    """
    获取需求清单中所有团队(包括技能分类)
    :param results_data_lst: 需求清单列表
    :return:
    """
    total_team_dict = {}
    for each_dict in results_data_lst:
        team = each_dict.get("team")
        skill = each_dict.get("skill_category")
        leave = each_dict.get("leave_time")
        # 非在职直接跳过，无需统计
        is_on_job = (leave == "在职") or (leave == '')
        if not is_on_job:
            continue
        # 是否存在技能分类
        if skill:
            key = '_'.join([team, skill])
        else:
            key = team
        if key and key in total_team_dict:
            total_team_dict[key] += 1
        elif key and key not in total_team_dict:
            total_team_dict[key] = 1
    return total_team_dict

def condition_query(cursor, select_sql, parameter_tuple):
    """
    查询数据库
    :return:data_lst
    """
    cursor.execute(select_sql, parameter_tuple)
    data_lst = cursor.fetchall()
    return data_lst

def team_classification(cursor, team, domain, requirement_preplanning, work_type):
    """
    获取需求清单中所有团队(包括技能分类) 、需求清单列表
    :param cursor: 游标
    :return: team_work_dict, product_version_dict, total_team_name_lst
    """
    # 六种情况：
    # 1、多领域无团队
    # 2、多领域多团队/多领域单团队(只看团队)
    # 3、单领域单/多团队
    # 4、单领域无团队
    # 5、无领域单/多团队
    # 6、无领域无团队
    results_data_lst = []
    if domain and not team: # 多领域无团队  单领域无团队
        select_sql = "select * from requirement_schedule_table where domain=%s and requirement_preplanning=%s " \
                     "and work_item_type=%s"
        for each_domain in domain:
            parameter_tuple = (each_domain, requirement_preplanning, work_type)
            data_lst = condition_query(cursor, select_sql, parameter_tuple)
            results_data_lst += data_lst
    elif (len(domain) >= 2 and len(team) >= 2) or (len(domain) >= 2 and len(team) == 1) or (not domain and team): # 多领域多团队/多领域单团队/无领域单/多团队
        select_sql = "select * from requirement_schedule_table where team=%s and requirement_preplanning=%s " \
                     "and work_item_type=%s"
        for each_team in team:
            parameter_tuple = (each_team, requirement_preplanning, work_type)
            data_lst = condition_query(cursor, select_sql, parameter_tuple)
            results_data_lst += data_lst
    elif len(domain) == 1 and team: # 单领域单/多团队
        select_sql = "select * from requirement_schedule_table where team=%s and domain=%s and " \
                     "requirement_preplanning=%s and work_item_type=%s"
        for each_team in team:
            parameter_tuple = (each_team, domain[0], requirement_preplanning, work_type)
            data_lst = condition_query(cursor, select_sql, parameter_tuple)
            results_data_lst += data_lst
    elif not domain and not team: # 无领域无团队
        select_sql = "select * from requirement_schedule_table where requirement_preplanning=%s and work_item_type=%s"
        parameter_tuple = (requirement_preplanning, work_type)
        data_lst = condition_query(cursor, select_sql, parameter_tuple)
        results_data_lst += data_lst
    # 团队pr字典 团队列表
    team_work_dict = {}
    total_team_name_lst = []
    for each_dict in results_data_lst:
        team = each_dict.get("team", None)
        if not team:
            continue
        skill_type = each_dict.get("skill_type", None)
        if skill_type:
            team = '_'.join([team, skill_type])
        team_work_dict.setdefault(team, []).append(each_dict)
        if team not in total_team_name_lst:
            total_team_name_lst.append(team)
    return team_work_dict, total_team_name_lst

def task_assignment(team, domain, requirement_preplanning, work_type, username, encrypted_password):
    """
    填写所有PR的【需求评估结论（第一次）】字段。
    ①获取产品需求清单，按【团队】字段获取清单中的团队清单
    ②计算团队版本内剩余可用人力=版本内可用人力-版本内已占用人力
    ③ 根据需求清单， 按需求采纳顺序，依次判断该团队是否采纳PR
    :param product: 产品
    :param work_type:类型
    :param team_code:团队编码
    :param username:用户名
    :param encrypted_password:密码(加密)
    :return:None
    """
    db = None
    cursor = None
    try:
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        # 团队归类 团队名称表
        team_work_dict, total_team_name_lst = team_classification(cursor, team, domain, requirement_preplanning, work_type)
        # 人力视图表2
        select_sql = "select * from requirement_dev_human_resource"
        cursor.execute(select_sql)
        results_data_lst = cursor.fetchall()
        # 版本日期数据字典
        vesion_workday_dict = get_version_month(cursor, requirement_preplanning)
        # (子)团队个人各月所需交付投入占比和产品占比
        team_month_proportion_dict = team_proportion(results_data_lst, vesion_workday_dict, total_team_name_lst)
        # 按月计算(子)团队成员可用人数并累加和所有人力(分产品)
        version_available_personnel_dict = number_of_available_personnel(team_month_proportion_dict, vesion_workday_dict)
        # # 计算(子)团队个人已占用人力资源 和剩余可用人力
        team_occupied_remaining_workload(total_team_name_lst, vesion_workday_dict, version_available_personnel_dict, work_type, username, encrypted_password)
        print("version_available_personnel_dict", version_available_personnel_dict)
        # # 计算整个团队版本周期内剩余可用人力（汇总时月负值归零）
        collect_sub_team_powerman_dict = collect_sub_team_powerman(version_available_personnel_dict, vesion_workday_dict)
        # # PR采纳排序流程
        can_incloud_lst, not_incloud_lst = adopt_pr_process(total_team_name_lst, team_work_dict, collect_sub_team_powerman_dict)
        # 评估入库
        evaluate_storage_database(cursor, can_incloud_lst, not_incloud_lst)
        db.commit()
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        print(f"数据库操作异常，已回滚事务，错误信息：{str(e)}")
    except Exception as e:
        if db:
            db.rollback()
        print(f"程序运行异常，已回滚事务，错误信息：{str(e)}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def collect_sub_team_powerman(version_available_personnel_dict, vesion_workday_dict):
    """
    如果一个月中人员剩余人力为负时，清零并标记
    :param version_available_personnel_dict:团队月剩余人力字典 {month:{subteam:{name:{产品:剩余人天}}}}
    :param vesion_workday_dict:{"所属产品":"产品1"}
    :return:collect_sub_team_powerman_dict {子团队:指定产品汇总正数人力}
    """
    product_mapping_dict = {"ZXONE 19700": "产品1", "ZXONE 9700": "产品2", "ZXMP M721": "产品3", "ZXONE NTON": "产品4"}
    product = vesion_workday_dict.get("所属产品")
    product = product_mapping_dict.get(product)
    collect_sub_team_powerman_dict = {}
    for each_month, each_team in version_available_personnel_dict.items():
        for each_sub_team, each_member in each_team.items():
            count = Decimal("0.00")
            for name, prod_dict in each_member.items():
                remain_val = prod_dict.get(product, Decimal("0.00"))
                # 负数原地清零
                if remain_val < Decimal("0.00"):
                    prod_dict[product] = Decimal("0.00")
                    remain_val = Decimal("0.00")
                if remain_val > Decimal("0.00"):
                    count += remain_val
            # 同团队多月份人力累加
            collect_sub_team_powerman_dict[each_sub_team] = collect_sub_team_powerman_dict.get(each_sub_team, Decimal("0.00")) + count
            print("collect_sub_team_powerman_dict[each_sub_team]", collect_sub_team_powerman_dict[each_sub_team])
    return collect_sub_team_powerman_dict

def evaluate_storage_database(cursor, can_incloud_lst, not_incloud_lst):
    """
    对可采纳和不可采纳进行更改
    :param cursor: 游标
    :param can_incloud_lst: 可以采纳列表
    :param not_incloud_lst: 不可采纳列表
    :return: None
    """
    # 处理可纳入ID的更新
    if can_incloud_lst:
        placeholders = ", ".join(["%s"] * len(can_incloud_lst))
        sql_can_be = f"""
                   UPDATE requirement_schedule_table  
                   SET first_evaluation_conclusion = '可纳入'
                   WHERE id IN ({placeholders})
               """
        cursor.execute(sql_can_be, can_incloud_lst)
    # 无法纳入
    if not_incloud_lst:
        placeholders = ", ".join(["%s"] * len(not_incloud_lst))
        sql_can_not_be = f"""
               UPDATE requirement_schedule_table  
               SET first_evaluation_conclusion = '无法纳入'
               WHERE id IN ({placeholders})
           """
        cursor.execute(sql_can_not_be, not_incloud_lst)
    print(f"更新完成：可纳入ID {len(can_incloud_lst)} 条，无法纳入 {len(not_incloud_lst)} 条")

def adopt_pr_process(total_team_name_lst, team_work_dict, collect_sub_team_powerman_dict):
    """
    判断团队人力是否超过pr工作量，如若超过跳过pr，没有超过则采纳，并更新人力
    :param total_team_name_lst:
    :param team_work_dict:
    :param collect_sub_team_powerman_dict: {团队:Decimal剩余人力}
    :return:can_incloud_lst, not_incloud_lst 可以采纳pr id列表和不可以采纳pr id列表
    """
    # 筛选任务需求清单PR
    work_list_sub_team_pr_dict = filter_product_pr(total_team_name_lst, team_work_dict)
    # PR排序
    sort_work_list_sub_team_pr_dict = adopt_pr_sort(work_list_sub_team_pr_dict)
    can_incloud_lst = []
    not_incloud_lst = []
    for each_sub_team, pr_lst in sort_work_list_sub_team_pr_dict.items():
        team_total = collect_sub_team_powerman_dict.get(each_sub_team, Decimal("0.00"))
        # 初始化当前可用剩余人力，循环逐个PR动态扣减
        remain_power = team_total
        print("团队总共remain_power", remain_power)
        if remain_power <= Decimal("0.00"):
            for each_pr in pr_lst:
                pr_id = each_pr.get("id", "")
                not_incloud_lst.append(pr_id)
            continue
        manpower_deduct(can_incloud_lst, not_incloud_lst, remain_power, pr_lst)
    return can_incloud_lst, not_incloud_lst


def manpower_deduct(can_incloud_lst, not_incloud_lst, remain_power, pr_lst):
    """
    对有人力的团队进行采纳和扣减团队剩余人力，不改动PR原有预估工时
    :param can_incloud_lst: 可承接PR编号集合
    :param not_incloud_lst: 无法承接PR编号集合
    :param remain_power: 当前团队实时剩余可用人力(Decimal高精度)
    :param pr_lst: 当前团队待分配PR列表
    :return: None
    """
    for each_pr in pr_lst:
        start_str = each_pr.get("plan_start_dev_date", None)
        end_str = each_pr.get("plan_finish_dev_date", None)
        # 任务已配置开发起止日期，跳过该任务
        if start_str and end_str:
            continue
        first_evaluation_conclusion = each_pr.get("first_evaluation_conclusion", None)
        # 已有初评结论的任务直接跳过
        if first_evaluation_conclusion:
            continue
        workload = each_pr.get("estimated_dev_workload", None)
        if not workload:
            continue
        # PR需求工时转Decimal，规避浮点误差
        workload_dec = Decimal(str(safe_float(workload)))
        pr_id = each_pr.get("id")
        # # 任务工时小于等于0
        # if workload_dec <= Decimal("0.00"):
        #     print("PR 大于 团队人力")
        #     pr_id = each_pr.get("id", "")
        #     not_incloud_lst.append(pr_id)
        # 剩余人力足够承接：收录可用PR、扣减团队人力
        if remain_power >= workload_dec:
            can_incloud_lst.append(pr_id)
            remain_power -= workload_dec
        # 人力不足，任务放入驳回清单
        else:
            print("PR 不可可纳入")
            not_incloud_lst.append(pr_id)

def adopt_pr_sort(work_list_sub_team_pr_dict):
    """
    采纳顺序：按需求排序 数字从大到小排列；
            如果需求排序相同，则按优先级从大到小排列；
            如果优先级相同，按预计开发工作量从小到大排列；
            如果工作量也相同，则随机排列。
    :param work_list_sub_team_pr_dict: pr
    :return: work_list_sub_team_pr_dict
    """
    # 遍历每个团队的数据集
    for team_name, data_list in work_list_sub_team_pr_dict.items():
        # 跳过空列表，避免排序报错
        if not isinstance(data_list, list) or len(data_list) == 0:
            print(f"警告：团队[{team_name}]的数据为空/非列表，跳过排序")
            continue
        data_list.sort(key=sort_key)
    return work_list_sub_team_pr_dict

def sort_key(item):
    """
    排序
    :param item: pr
    :return: 排完序的pr
    """
    # 提取字段，处理空值/非数字（默认值保证排序不报错）
    num = item.get("requirement_sort", 0)
    priority = item.get("priority", 0)
    workload = item.get("estimated_dev_workload", 0)
    # 转换为数值（避免字符串排序错误）
    try:
        num = safe_float(num)
        priority = safe_float(priority)
        workload = safe_float(workload)
    except (ValueError, TypeError):
        num = 0.0
        priority = 0.0
        workload = 0.0
    # 排序键：(数字降序, 优先级降序, 工作量升序, 随机数)
    return (-num, -priority, workload, random.random())

def filter_product_pr(total_team_name_lst, team_work_dict):
    """
    筛选出需求清单中出现过的团队
    :param total_team_name_lst: 需求清单团队
    :param team_work_dict: 团队任务字典
    :return: work_list_sub_team_pr_dict
    """
    work_list_sub_team_pr_dict = {}
    for each_sub_team in total_team_name_lst:
        if each_sub_team in team_work_dict:
            each_pr = team_work_dict[each_sub_team]
            work_list_sub_team_pr_dict.setdefault(each_sub_team, []).extend(each_pr)
    return work_list_sub_team_pr_dict

def number_of_available_personnel(team_month_proportion_dict, vesion_workday_dict):
    """
    以团队来划分人员并计算每月所有人力：单产品单独核算
    :param team_month_proportion_dict: {月份:[[团队,团队占比str,产品1,产品2,产品3,产品4,姓名],...]}
    :return: {月份:{团队:{人员:{"产品1":人天,"产品2":人天...}}}}
    """
    product = vesion_workday_dict.get("所属产品")
    version_available_personnel_dict = {}
    for month, value_lst in team_month_proportion_dict.items():
        work_day = Decimal(get_month_legal_workdays(month))
        sub_team_each_dict = {}
        if not value_lst:
            version_available_personnel_dict[month] = sub_team_each_dict
            continue
        for each_value in value_lst:
            team = each_value[0]
            proportion_str = each_value[1]
            zxone_19700 = each_value[2]
            zxone_9700 = each_value[3]
            zxmp_m721 = each_value[4]
            zxone_nton = each_value[5]
            name = each_value[-1]
            product_pro_str_list = [zxone_19700, zxone_9700, zxmp_m721, zxone_nton]
            # 团队占比
            team_rate = Decimal(safe_float(proportion_str))
            prod_dict = {}
            # ：团队占比*单品占比*天数
            for idx, p_str in enumerate(product_pro_str_list, 1):
                p_rate = Decimal(safe_float(p_str))
                count = (team_rate * p_rate * work_day).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                prod_dict[f"产品{idx}"] = count
            sub_team_each_dict.setdefault(team, {})[name] = prod_dict
        version_available_personnel_dict[month] = sub_team_each_dict
    return version_available_personnel_dict

def get_month_legal_workdays(date_str: str) -> int:
    """
    计算指定月份的法定工作日数（排除周末+法定节假日，包含调休补班）
    :param date_str: 月份参数，格式如 "2026-2"、"2026-02"
    :return: 该月法定工作日总数
    """
    # 1. 解析输入参数，生成当月第一天
    year, month = map(int, date_str.split("-"))
    first_day = datetime.date(year, month, 1)

    # 2. 计算当月最后一天（下月第一天减1天）
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    last_day = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)

    # 3. 遍历当月所有日期，统计工作日
    workday_count = 0
    current_day = first_day
    while current_day <= last_day:
        try:
            is_work = is_workday(current_day)  # 自动判断：补班算工作日，节假日/周末算非工作日
        except NotImplementedError:
            is_work = current_day.weekday() < 5
        if is_work:
            workday_count += 1
        current_day += datetime.timedelta(days=1)

    return workday_count

def team_proportion(results_data_lst, vesion_workday_dict, total_team_name_lst):
    """
    通过团队表来将人力视图表中所有人员归类并统计人员每月计划产品使用人力
    :param results_data_lst: 需求清单数据
    :param month_lst: 版本经历月份
    :param total_team_name_lst:需求清单所有团队表
    :return: team_month_proportion_dict 团队个人版本内各月所需交付投入占比，产品占比
    """
    team_time_dict = {}
    for each_data in results_data_lst:
        team = each_data.get("team")
        skill = each_data.get("skill_category")
        value = '_'.join([team, skill]) if skill else team
        if value in total_team_name_lst:
            team_time = each_data.get("year_month")
            ratio = each_data.get("demand_human_power_ratio")
            zxone_19700 = each_data.get("zxone_19700")
            zxone_9700 = each_data.get("zxone_9700")
            zxmp_M721 = each_data.get("zxmp_m721")
            zxone_nton = each_data.get("zxone_nton")
            person_name = each_data.get("name")
            team_time_dict[team_time] = team_time_dict.get(team_time, [])
            team_time_dict[team_time].append([value, ratio, zxone_19700, zxone_9700, zxmp_M721, zxone_nton, person_name])
    # (子)团队个人版本内各月所需交付投入占比，产品占比
    team_month_proportion_dict = {}
    month_lst = vesion_workday_dict.get("月")
    for each_month in month_lst:
        team_infos_lst = team_time_dict.get(each_month)
        team_month_proportion_dict[each_month] = team_infos_lst
    return team_month_proportion_dict

def get_version_month(cursor, requirement_preplanning):
    """
    获取版本内详细内容：获取月份、经历天数以及月份对应法定工作日
    :param cursor: 游标
    :param requirement_preplanning: 需求与规划
    :return: 版本日期数据字典
    """
    vesion_workday_dict = {}
    # 版本产品字典
    select_sql = "select * from version_table where requirement_preplanning=%s"
    data_lst = condition_query(cursor, select_sql, requirement_preplanning)
    for each_data in data_lst:
        product = each_data.get("belong_product")
        start_time = each_data.get("start_dev_date")
        finish_time = each_data.get("finish_dev_date")
        start = datetime.datetime.strptime(start_time, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(finish_time, "%Y-%m-%d").date()
        workday_count, month_lst, total_weeks, week_lst, week_workday_dict, month_week_workday_dict = calculate_month_and_workdays(
            start, end)
        vesion_workday_dict = {"所属产品": product, "版本": requirement_preplanning,
                               "月": month_lst, "天": workday_count, "月-天": month_week_workday_dict,
                               "版本启动日期": start, "完成开发日期": end}
    return vesion_workday_dict

def upgrade_chinese_calendar():
    """
    自动升级 chinese-calendar 库，兼容 Windows/Linux/macOS，处理权限问题
    """
    try:
        # 用当前Python环境的pip升级库
        # sys.executable 获取当前运行的python解释器路径，确保pip对应正确环境
        upgrade_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "chinese-calendar",
            "--quiet"  # 静默模式，减少输出
        ]

        # 执行升级命令，捕获输出和错误
        result = subprocess.run(
            upgrade_cmd,
            check=True,  # 命令执行失败（非0返回码）则抛出异常
            capture_output=True,  # 捕获stdout/stderr
            text=True  # 输出转为字符串（而非字节）
        )

        print(f"chinese-calendar 升级成功：{result.stdout.strip()}")
        return True

    except subprocess.CalledProcessError as e:
        # 处理升级失败（如权限不足、网络问题）
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        print(f"chinese-calendar 升级失败：{error_msg}")
        # 权限不足时，尝试加 --user 参数重新升级（仅针对普通用户无全局权限场景）
        try:
            upgrade_cmd_user = upgrade_cmd + ["--user"]
            subprocess.run(upgrade_cmd_user, check=True, capture_output=True, text=True)
            print("尝试使用 --user 参数升级成功")
            return True
        except:
            print("多次升级失败，将使用当前版本继续执行")
            return False
    except Exception as e:
        print(f"升级过程异常：{str(e)}")
        return False

def calculate_month_and_workdays(start, end):
    """
    计算两个日期字符串之间的月份数和法定工作日天数
    :param start: 开始日期（格式：YYYY-MM-DD）
    :param end: 结束日期（格式：YYYY-MM-DD）
    :return: 月份数（取整）、工作日天数
    """
    # 自动升级日历库
    # upgrade_chinese_calendar()
    total_days = (end - start).days + 1
    # 初始化统计变量
    total_workday_count = 0
    week_workday_dict = {}  # {星期: 总工作日数}
    month_week_split_dict = {}  # {月份: {星期: 该月内工作日数}}
    week_first_occur = {}  # 记录星期首次出现的顺序
    week_index = 0  # 星期出现顺序的索引
    current_date = start
    date_year = None
    date_month = None
    date_week = None
    week_str = ""
    month_str = ""
    for _ in range(total_days):
        date_year = current_date.year
        date_month = current_date.month
        iso_year, iso_week, _ = current_date.isocalendar()
        week_str = f"{iso_year}-W{iso_week:02d}"
        month_str = f"{date_year}-{date_month:02d}"
        # 判断工作日
        try:
            is_work = is_workday(current_date)
        except NotImplementedError:
            is_work = current_date.weekday() < 5
        if is_work:
            total_workday_count += 1
        # 初始化周总计数 + 记录星期首次出现顺序
        if week_str not in week_workday_dict:
            week_workday_dict[week_str] = 0
            week_first_occur[week_str] = week_index  # 用索引记录顺序，避免后续排序
            week_index += 1
        # 初始化月份-星期拆分字典
        if month_str not in month_week_split_dict:
            month_week_split_dict[month_str] = {}
        month_week_split = month_week_split_dict[month_str]
        if week_str not in month_week_split:
            month_week_split[week_str] = 0
        # 累计工作日数
        if is_work:
            week_workday_dict[week_str] += 1
            month_week_split[week_str] += 1
        # 日期累加
        current_date += datetime.timedelta(days=1)
    # 生成月份列表（
    month_lst = []
    start_year, start_month = start.year, start.month
    end_year, end_month = end.year, end.month
    # 批量生成月份列表
    current_year = start_year
    current_month = start_month
    while True:
        month_lst.append(f"{current_year}-{current_month:02d}")
        if current_year == end_year and current_month == end_month:
            break
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    # 生成星期列表
    week_lst = sorted(week_workday_dict.keys(), key=lambda x: week_first_occur[x])
    total_weeks = len(week_lst)
    # 按月份分组的字典
    month_week_workday_dict = {}
    for month_str, week_data in month_week_split_dict.items():
        sorted_weeks = sorted(week_data.keys(), key=lambda x: week_first_occur[x])
        month_week_workday_dict[month_str] = [{wk: week_data[wk]} for wk in sorted_weeks]
    return total_workday_count, month_lst, total_weeks, week_lst, week_workday_dict, month_week_workday_dict

def team_occupied_remaining_workload(total_team_name_lst, vesion_workday_dict, version_available_personnel_dict, work_type, username, encrypted_password):
    """
    计算已占用人力 并对每月每个团队下的每个人进行精确扣减，算出剩余人力
    :param total_team_name_lst:需求清单团队表
    :param vesion_workday_dict:版本日期字典
    :param version_available_personnel_dict:版本中团队全部人力字典
    :param product:产品名称
    :param work_type:任务类型
    :param team_code:团队编码
    :param username:用户名
    :param encrypted_password:密码
    :return:version_available_personnel_dict:版本中团队剩余人力字典
    """
    product = vesion_workday_dict.get("所属产品")
    start_time = vesion_workday_dict.get("版本启动日期")
    end_time = vesion_workday_dict.get("完成开发日期")
    for each_team in total_team_name_lst:
        all_data_dict = get_PR_field(each_team.split('_')[0], product, work_type, username, encrypted_password, str(end_time), str(start_time)) # 需要填入动态参数
        # 团队可能区分有技能类型和没有技能类型，如有技能类型则需过滤出同一技能类型的pr
        if all_data_dict:
            if all_data_dict["bo"] and all_data_dict["bo"]["result"] and all_data_dict["bo"]["result"]["items"]:
                if "_" in each_team:
                    sub_team_name = each_team.split('_')[1]
                    # 修改： 所属产品与版本一致，开发日期>=启动时间，开发周期在版本日期内 ->  更改为过滤技能类型函数，原3条条件已加入接口筛选
                    filter_pr_data_lst = filter_pr_data(sub_team_name, all_data_dict["bo"]["result"]["items"])
                    occupation_merge(filter_pr_data_lst, each_team, version_available_personnel_dict, product)
                else:
                    occupation_merge(all_data_dict["bo"]["result"]["items"], each_team, version_available_personnel_dict, product)

def occupation_merge(filter_pr_data_lst, each_team, version_available_personnel_dict, product):
    """
    PR任务占用人力扣减：按指定产品扣减对应人员可用人天
    :param filter_pr_data_lst: pr任务列表
    :param each_team: 当前处理团队名
    :param version_available_personnel_dict: {月份:{团队:{人员:{产品X:Decimal人天}}}}
    :param product: 需要扣减的产品key，例："产品1"
    """
    print("1")
    for each_pr in filter_pr_data_lst:
        # 提取PR任务核心字段
        feature_identifier = each_pr.get("FeatureId", None)
        estimated_dev_workload = safe_float(each_pr.get("EstimatedEffortOfDevelopment", None))
        principal_list = each_pr.get("DevelopmentOwner", None)

        # 无负责人/无ID/无工作量 → 跳过
        if not principal_list or not feature_identifier or not estimated_dev_workload:
            print(f"缺少唯一标识或预估工作量或负责人{each_pr}无法计算工作量")
            continue
        # 解析起止日期
        try:
            pr_start_time = each_pr.get("PlanStartDateOfDevelopment").split("T")[0]
            pr_end_time = each_pr.get("PlanFinishDateOfDevelopment").split("T")[0]
        except Exception:
            print(f"任务开始/结束时间错误{each_pr}")
            continue
        try:
            start = datetime.datetime.strptime(pr_start_time, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(pr_end_time, "%Y-%m-%d").date()
        except Exception:
            print(f"日期格式解析失败：{each_pr}")
            continue
        # 拆分人员工号&姓名
        assigned_person_ids, emp_id_name_dict = extract_employee_id(principal_list)
        if not assigned_person_ids:
            continue
        # 拆分周期：总工作日、按月周拆分
        total_workday_count, month_lst, total_weeks, week_lst, week_workday_dict, month_week_workday_dict = calculate_month_and_workdays(start, end)
        if total_workday_count <= 0:
            print(f"任务{feature_identifier}有效工作日为0，跳过")
            continue
        # 日均单人分摊工作量
        daily_workload = Decimal(str(estimated_dev_workload)) / Decimal(total_workday_count)
        # 按月、按周分摊扣减
        for each_month, each_lst in month_week_workday_dict.items():
            for each_weekly_dict in each_lst:
                week_day_list = list(each_weekly_dict.values())
                if not week_day_list:
                    continue
                weekly_day = Decimal(week_day_list[0])
                # 本周分摊到单个人的工时
                per_person_week_cost = weekly_day * daily_workload / Decimal(len(assigned_person_ids))
                # 逐个人员扣【指定product】人力
                for emp_id in assigned_person_ids:
                    try:
                        emp_name = emp_id_name_dict[emp_id]
                        # 层级：月→团队→人→产品 扣减
                        person_product_dict = version_available_personnel_dict[each_month][each_team][emp_name]
                        if product not in person_product_dict:
                            print(f"{emp_name}无{product}可用人力，跳过扣减")
                            continue
                        # 占用消耗 = 可用人力 - 消耗工时
                        person_product_dict[product] -= per_person_week_cost
                        # 按需保留两位小数
                        person_product_dict[product] = person_product_dict[product].quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                        print(f"{emp_name}｜{each_month}｜{product}｜任务{feature_identifier}：扣减工时{per_person_week_cost:.2f}")
                    except KeyError:
                        print(f"工号{emp_id}【{emp_id_name_dict.get(emp_id,'未知')}】不在{each_team}-{each_month}人力台账中")
                    except Exception as e:
                        print(f"扣减异常：{emp_id} {str(e)}")

def extract_employee_id(principal_list):
    emp_id_name_dict = {}
    assigned_person_ids = []
    if judge(principal_list):  # 判断列表非空
        pattern = re.compile(r'\d+')  # 匹配工号（数字）
        for principal_dict in principal_list:  # 遍历每个字典
            # 提取name字段（兼容key大小写/空格，比如"name"/"Name"/"name "）
            principal_name = ""
            for k, v in principal_dict.items():
                if str(k).strip().lower() == "namedisplaylong" and judge(v):
                    principal_name = str(v).strip()
                    break
            # 从name中匹配工号
            if judge(principal_name):
                match = pattern.search(principal_name)
                if match:
                    assigned_person_ids.append(match.group())
                    pure_name = pattern.sub('', principal_name).strip()
                    emp_id_name_dict[match.group()] = pure_name
    return assigned_person_ids, emp_id_name_dict

def judge(obj):
    """通用判空函数：判断对象是否非空"""
    if obj is None:
        return False
    if isinstance(obj, (list, dict, str)) and len(obj) == 0:
        return False
    return True

def filter_pr_data(sub_team_name, all_data_lst):
    filter_pr_data_lst = []
    for each_pr in all_data_lst:
        skill_type = each_pr.get("SkillType")
        if sub_team_name == skill_type:
            filter_pr_data_lst.append(each_pr)
    return filter_pr_data_lst

def get_PR_field(team_name, product, work_type, username, encrypted_password, end_time, start_time):
    work_type = db_mapping_config.work_type_dict.get(work_type)
    team_code = db_mapping_config.team_code_mapping_dict.get(team_name)
    product_value = db_mapping_config.product_mapping_dict.get(product)
    URL = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/WIC/rest/workspaces/OTNSW/queries/query_work_items"
    # x_auth = get_x_auth_val(user=username, encrypted_pwd=encrypted_password)
    x_auth = '1af706bc5fdcb1bfdcf97f273fc857e4'
    Header = {
        "X-Tenant-Id": "ZTE",
        "X-Lang-Id": "zh_CN",
        "X-Emp-No": username,
        "X-Auth-Value": x_auth,
        "appcode": "4811ee4055a74cb4b52e7295e1d1858d",
        "Content-Type": "application/json"
    }
    body = {
        "queryCondition": {
            "depth": 6,
            "relatedType": [
                "linkRelatedType_3"
            ],
            "removeTop": True,
            "sourceClauses": [
                {
                    "field": "System_WorkItemType",
                    "leftGroup": 0,
                    "logicalOperator": "",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": work_type
                },
                {
                    "field": "Team",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "=_accurate",
                    "rightGroup": 0,
                    "value": {
                        "name": team_name,
                        "label": team_name,
                        "nameEn": "",
                        "hasNoChildren": True,
                        "value": team_code
                    }
                },
                {
                    "field": "System_State",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "not in",
                    "rightGroup": 0,
                    "value": [
                        "已废弃"
                    ]
                },
                {
                    "field": "AssessResult_First",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "like",
                    "rightGroup": 0,
                    "value": "可纳入"
                },
                {
                    "field": "FinishTimeOfDevelopment",
                    "leftGroup": 1,
                    "logicalOperator": "AND",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": None
                },
                {
                    "field": "FinishTimeOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "OR",
                    "operator": ">=",
                    "rightGroup": 1,
                    "value": start_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 2,
                    "logicalOperator": "AND",
                    "operator": "<=",
                    "rightGroup": 0,
                    "value": end_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">=",
                    "rightGroup": 1,
                    "value": start_time
                },
                {
                    "field": "PlanStartDateOfDevelopment",
                    "leftGroup": 1,
                    "logicalOperator": "OR",
                    "operator": "<",
                    "rightGroup": 0,
                    "value": end_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">",
                    "rightGroup": 2,
                    "value": end_time
                },
                {
                    "field": "System_Id",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "!=",
                    "rightGroup": 0,
                    "value": None
                },
                {
                    "field": "BelongProduct",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "=_accurate",
                    "rightGroup": 0,
                    "value": {
                        "name": product,
                        "label": product,
                        "nameEn": "",
                        "hasNoChildren": True,
                        "value": product_value
                    }
                }
            ],
            "targetClauses": [
                {
                    "field": "System_Id",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "!=",
                    "rightGroup": 0,
                    "value": None
                }
            ],
            "treeOptions": "top",
            "type": "tree"
        },
        "selectItems": [
            {
                "key": "System_WorkItemType",
                "name": "工作项类型",
                "type": "workItemType",
                "width": "105"
            },
            {
                "key": "System_Id",
                "name": "标识",
                "type": "workItemNo",
                "width": ""
            },
            {
                "key": "System_Title",
                "name": "标题",
                "type": "string",
                "width": "137.79998779296875"
            },
            {
                "key": "System_AreaPath",
                "name": "领域",
                "type": "advancedData",
                "width": "84"
            },
            {
                "key": "Team",
                "name": "团队",
                "type": "advancedData",
                "width": "114.20001220703125"
            },
            {
                "key": "FeatureId",
                "name": "特性标识",
                "type": "string",
                "width": "119.01251220703125"
            },
            {
                "key": "FeatureAttribute",
                "name": "特性属性",
                "type": "string",
                "width": "54.7999267578125"
            },
            {
                "key": "AssessResult_First",
                "name": "评估结论（第一次）",
                "type": "string",
                "width": ""
            },
            {
                "key": "EstimatedEffortOfDevelopment",
                "name": "预计开发工作量",
                "type": "double",
                "width": "56.7999267578125"
            },
            {
                "key": "PlanStartDateOfDevelopment",
                "name": "计划开始开发日期",
                "type": "date",
                "width": "106.5999755859375"
            },
            {
                "key": "PlanFinishDateOfDevelopment",
                "name": "计划完成开发日期",
                "type": "date",
                "width": "74.449951171875"
            },
            {
                "key": "ProductRoadmap",
                "name": "产品路标",
                "type": "string",
                "width": ""
            },
            {
                "key": "RequirementPrePlanning",
                "name": "需求预规划",
                "type": "string",
                "width": ""
            },
            {
                "key": "BelongProduct",
                "name": "所属产品",
                "type": "advancedData",
                "width": ""
            },
            {
                "key": "DevelopmentOwner",
                "name": "开发负责人",
                "type": "user",
                "width": ""
            },
            {
                "key": "SkillType",
                "name": "技能类型",
                "type": "user",
                "width": ""
            }
        ],
        "pageSize": 8000
    }
    response = requests.post(URL, json=body, headers=Header)
    try:
        content = response.text
        return dict(json.loads(content))  # 转字典
    except Exception as e:
        print(f'get_PR_field():{e}')

def get_feature_url(skill_catalogue):
    """
    根据skill_catalogue的值获取对应的feature_url

    参数:
        skill_catalogue (str): 技能目录名称，如'机电'、'软件'等

    返回:
        str: 对应的url字符串，如果无匹配项返回None
    """
    url_mapping = {
        '机电': ['d95b06b2517511f0b1ced5c2b4cfa078'],
        '监控': ['e6d8e4db517611f0a298b355c2f6ec5d']  # 示例：可根据实际需求添加
    }
    # 获取对应的值，无匹配时返回None（也可自定义默认值）
    feature_url_pageid_lst = url_mapping.get(skill_catalogue)

    return feature_url_pageid_lst

def get_request(usr_id, usr_token, feature_url_pageid):
    """
    带固定Header配置的GET请求函数，获取目标JSON数据
    参数:
        usr_id (str): X-Emp-No头信息
        usr_token (str): X-Auth-Value头信息
    返回:
        dict: 成功返回JSON数据（字典格式）；失败返回错误信息字符串
    """
    url = "https://icosg.dt.zte.com.cn/studio-ispace/doc/page/descendant?spaceId=fbff14a6a14c4985874248df3ac610c1&contentId=" + feature_url_pageid
    # 预配置的Header
    headers = {
        'X-Emp-No': usr_id,
        'X-Auth-Value': usr_token,
        'X-Tenant-Id': 'ZTE',
        'appcode': 'b1d488a42a7946a6a16dc896488a7e38',
        'X-Lang-Id': 'zh_CN'
    }

    try:
        # 发送GET请求，设置超时时间10秒
        response = requests.get(url, headers=headers, timeout=10)
        # 检查HTTP响应状态码（非200则抛出异常）
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except requests.exceptions.HTTPError as e:
        return f"HTTP请求错误: {str(e)} (状态码: {response.status_code})"
    except requests.exceptions.Timeout:
        return "请求超时（超过10秒）"
    except requests.exceptions.ConnectionError:
        return "网络连接错误"
    except ValueError:
        return "响应数据不是合法的JSON格式"
    except Exception as e:
        return f"请求失败: {str(e)}"

def get_x_auth_val(user: str, encrypted_pwd: str, req_ip: str = None, decode_pwd: bool = True):
    """
    从网站获取验证识别码(x_auth_val)，支持加密密码自动解码
    :param user: 用户名（明文）
    :param encrypted_pwd: 加密后的密码字符串（若decode_pwd=False则为明文密码）
    :param req_ip: 请求的IP地址。如果为None，则自动获取本机IP。
    :param decode_pwd: 是否需要解码密码（默认True，传入加密密码时用；False则直接使用明文密码）
    :return: 成功时返回x_auth_val，失败时返回None。
    """
    # 1. 密码解码（如果需要）
    if decode_pwd:
        pwd = decode_password(encrypted_pwd)
        # 检查解码是否失败
        if pwd.startswith("解码失败"):
            print(f"密码解码失败: {pwd}")
            return None
    else:
        pwd = encrypted_pwd  # 直接使用明文密码

    # 2. 获取请求IP
    if req_ip is None:
        req_ip = get_local_ip()
        if req_ip is None:
            print("无法获取本机IP地址")
            return None

    # 3. 构造验证码并发送请求（原逻辑保留）
    auth_url = 'https://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv'
    verify_code_str = f'{user}{pwd}{req_ip}Portal'
    verify_code = hashlib.md5(verify_code_str.encode(encoding='utf-8')).hexdigest()

    request_data = {
        "account": user,
        "passWord": pwd,
        "loginClientIp": req_ip,
        "loginSystemCode": "Portal",
        "originSystemCode": "",
        "other": {"networkArea": '1', "networkAccessType": '1'},
        "verifyCode": verify_code
    }

    try:
        resp = requests.post(
            url=auth_url,
            data=json.dumps(request_data),
            headers={'Content-type': 'application/json'}
        )
        result = resp.json()
        # 修复原代码的列表对比逻辑（更健壮）
        code_list = [result.get("code", {}).get("code"), result.get("bo", {}).get("code")]
        if code_list == ["0000", "0000"]:
            return result['other']['token']
        else:
            error_msg = result.get('message', '未知错误')
            print(f"认证失败: {error_msg}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"网络请求异常: {e}")
        return None
    except Exception as e:
        print(f"处理响应时发生异常: {e}")
        return None

def decode_password(encoded_str: str) -> str:
    """
    简易密码解码函数（Base64解码）
    :param encoded_str: 编码后的密码字符串
    :return: 解码后的明文密码，出错返回错误提示
    """
    try:
        decoded_bytes = base64.b64decode(encoded_str)
        plain_text = decoded_bytes.decode("utf-8")
        return plain_text
    except Exception as e:
        return f"解码失败: {str(e)}"

def get_local_ip():
    """
    建立与本地的 UDP 连接获取本地 IP
    :return: 本地 IP 地址，如果失败则返回 None
    """
    s = None
    try:
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as ex:
        print(f'socket 运行异常: {ex}')
        if s:
            s.close()
        return None

def get_database_allocable_data(results_data_lst):
    try:
        allocable_data_dict ={}
        data_sub_team_lst = []
        for each_data_dict in results_data_lst:
            team = each_data_dict.get("team")
            skill = each_data_dict.get("skill_type", None)
            if skill:
                team = '_'.join([team, skill])
            allocable_data_dict.setdefault(team, []).append(each_data_dict)
            if team not in data_sub_team_lst:
                data_sub_team_lst.append(team)
        return allocable_data_dict, data_sub_team_lst
    except Exception as e:
        print(f"get_database_allocable_data查询失败：{str(e)}")
        raise

def get_version_datetime(allocable_data_dict, cursor):
    try:
        datetime_dict = {}
        version = next(iter(allocable_data_dict.values()))[0].get("requirement_preplanning")
        select_sql = """select * from version_table where requirement_preplanning=%s"""
        cursor.execute(select_sql, version)
        version_line_data_lst = cursor.fetchall()
        if version_line_data_lst:
            version_data_dict = version_line_data_lst[0]
            start_time = datetime.datetime.strptime(version_data_dict.get("start_dev_date"), "%Y-%m-%d").date()
            finish_time = datetime.datetime.strptime(version_data_dict.get("finish_dev_date"), "%Y-%m-%d").date()
            belong_product = version_data_dict.get("belong_product")
            workday_count, month_lst, total_weeks, week_lst, week_workday_dict, month_week_workday_dict = calculate_month_and_workdays(start_time, finish_time)
            datetime_dict = {"产品":belong_product, "开始时间":start_time, "结束时间":finish_time, "版本工作天数":workday_count, "版本月份列表":month_lst,
                             "版本周数":total_weeks, "版本周列表":week_lst, "周工作日数量":week_workday_dict, "月周映射":month_week_workday_dict}
    except Exception as e:
        print(f"get_version_datetime获取失败：{str(e)}")
        raise
    return datetime_dict

def PR_allocate(team, domain, requirement_preplanning, work_type, username, encrypted_password):
    # 六种情况：
    # 1、多领域无团队
    # 2、多领域多团队/多领域单团队(只看团队)
    # 3、单领域单/多团队
    # 4、单领域无团队
    # 5、无领域单/多团队
    # 6、无领域无团队
    db = None
    cursor = None
    try:
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        results_data_lst = []
        # 1、多领域无团队  4、单领域无团队
        if domain and not team:
            # Bug3修复：WHERE 条件用 AND，不能用逗号
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND domain=%s AND first_evaluation_conclusion=%s")
            for each_domain in domain:
                parameter_tuple = (requirement_preplanning, work_type, each_domain, "可纳入")
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # Bug2修复：原 (len(domain) >= 2 or len(domain)) <= 0 因运算符优先级永远为 False（多领域有团队走不进来）
        # 正确逻辑：多领域有团队(case2) 或 无领域有团队(case5) → 只按团队查
        # 2、多领域多团队/多领域单团队(只看团队)  5、无领域单/多团队
        elif (len(domain) >= 2 or len(domain) == 0) and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s AND first_evaluation_conclusion=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team, "可纳入")
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 3、单领域单/多团队
        elif len(domain) == 1 and team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND team=%s AND domain=%s AND first_evaluation_conclusion=%s")
            for each_team in team:
                parameter_tuple = (requirement_preplanning, work_type, each_team, domain[0], "可纳入")
                data_lst = match_data(select_sql, cursor, parameter_tuple)
                results_data_lst += data_lst

        # 6、无领域无团队
        elif not domain and not team:
            # Bug3修复：AND
            select_sql = ("select * from requirement_schedule_table "
                          "where requirement_preplanning=%s AND work_item_type=%s AND first_evaluation_conclusion=%s")
            parameter_tuple = (requirement_preplanning, work_type, "可纳入")
            data_lst = match_data(select_sql, cursor, parameter_tuple)
            results_data_lst += data_lst

        if not results_data_lst:
            raise ValueError("数据库暂无匹配数据，请确认需求预规划/工作项类型后重试")
        # 获取数据清单中团队数据
        allocable_data_dict, data_sub_team_lst = get_database_allocable_data(results_data_lst)
        select_sql = "select * from requirement_dev_human_resource"
        cursor.execute(select_sql)
        results_data_lst = cursor.fetchall()
        # 各子团队人员数据
        team_product_person_dict = sub_team_person_data(results_data_lst, data_sub_team_lst)
        # 获取版本启动开发日期、完成开发日期、版本经历月份以及星期
        # {"产品":belong_product, "开始时间":start_time, "结束时间":finish_time, "版本工作天数":workday_count, "版本月份列表":month_lst, "版本周数":total_weeks, "版本周列表":week_lst, "周工作日数量":week_workday_dict}
        datetime_dict = get_version_datetime(allocable_data_dict, cursor)
        # 版本每周总人力
        month_weekly_total_manpower_dict = version_weekly_available_manpower(team_product_person_dict, datetime_dict)
        # # 版本内团队下的所有人员
        # sub_team_person_dict = version_manpower(month_weekly_total_manpower_dict)
        # 已使用人力
        used_manpower(month_weekly_total_manpower_dict, datetime_dict, data_sub_team_lst, datetime_dict.get("产品"), work_type, username, encrypted_password)
        # # 计算月份剩余工作量并标记
        calculate_the_remaining_manpower(month_weekly_total_manpower_dict)
        # # 版本内每人每迭代剩余可用人力（人天）=迭代所在周的剩余可用人力相加
        final_result = version_period_manpower(month_weekly_total_manpower_dict, datetime_dict.get("产品"))
        # # 将人力涉及最小和最大迭代时间替换为最版本开始时间和结束时间
        new_data_iteration_dict = replacement_time(datetime_dict.get("开始时间"), datetime_dict.get("结束时间"), final_result)
        # # 找到版本最小迭代
        version_start_date = find_date_key(datetime_dict.get("开始时间"))
        # 按优先级排任务
        priority_ranking(allocable_data_dict)
        # # 子团队成员分配可纳入PR
        sub_team_allocable_pr(allocable_data_dict, final_result, version_start_date, new_data_iteration_dict)
        # 新增规则 PR的计划开始开发日期，计划完成开发日期，改为对应迭代起止日期
        fill_pr_dev_date_by_iter()
        # 将分配好的任务入库
        add_database(cursor)
        db.commit()
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        print(f"数据库操作异常，已回滚事务，错误信息：{str(e)}")
    except Exception as e:
        if db:
            db.rollback()
        print(f"程序运行异常，已回滚事务，错误信息：{str(e)}")
        print(traceback.print_exc())
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def fill_pr_dev_date_by_iter():
    '''
    规则：
    ①同迭代：start、end都改成该迭代起止date对象
    ②跨迭代：start不变(原类型保留)，end改成最后迭代结束date对象
    迭代源兼容 y/m/d、y-m-d 两种格式，内部用datetime比对，落地入库全date
    '''
    fmt_list = ["%Y/%m/%d", "%Y-%m-%d"]

    def safe_parse(date_str: str) -> datetime:
        """自动适配斜杠/横杠日期格式"""
        s = date_str.strip()
        if not s:
            raise ValueError("日期字符串为空")
        for fmt in fmt_list:
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期：{date_str}，不支持格式")

    def get_iter_index(dt: datetime, cache: list) -> int | None:
        """查询日期落在第几个迭代区间，无匹配返回None"""
        for idx, (s, e, _, _) in enumerate(cache):
            if s <= dt <= e:
                return idx
        return None

    if not task_time_mapping:
        return

    iter_cache: list[tuple[datetime, datetime, datetime.date, datetime.date]] = []
    for _, [s_str, e_str] in db_mapping_config.data_iteration_dict.items():
        if not s_str or not e_str:
            continue
        s_dt = safe_parse(s_str)
        e_dt = safe_parse(e_str)
        iter_cache.append((s_dt, e_dt, s_dt.date(), e_dt.date()))

    # 遍历任务数据
    for _, each_lst in task_time_mapping.items():
        if not each_lst:
            continue
        for each_dict in each_lst:
            raw_start = each_dict["start_date"]
            raw_end = each_dict["end_date"]

            # date统一转datetime用于区间比对
            def to_datetime(d):
                if isinstance(d, datetime.date):
                    return datetime.datetime.combine(d, datetime.datetime.min.time())
                return d
            d_start = to_datetime(raw_start)
            d_end = to_datetime(raw_end)

            s_idx = get_iter_index(d_start, iter_cache)
            e_idx = get_iter_index(d_end, iter_cache)
            if s_idx is None or e_idx is None:
                continue

            if s_idx == e_idx:
                # 同迭代：替换起止为迭代date
                _, _, it_s_date, it_e_date = iter_cache[s_idx]
                each_dict["start_date"] = it_s_date
                each_dict["end_date"] = it_e_date
            else:
                # 跨迭代：start保留原值，end赋值末端迭代结束date
                _, _, _, last_e_date = iter_cache[e_idx]
                each_dict["start_date"] = raw_start
                each_dict["end_date"] = last_e_date

def priority_ranking(allocable_data_dict):
    """
    原地排序：
    1. requirement_sort 降序，越大越靠前
    2. 同requirement_sort则priority降序
    兼容Decimal、字符串带空格，杜绝nan、精度丢失导致乱序
    :param allocable_data_dict: {团队名:[{priority, requirement_sort, ...},...]}
    :return: None，直接修改原字典列表
    """
    def parse_decimal(val):
        # 去首尾空格，统一转Decimal
        s = str(val).strip()
        return Decimal(s)

    for _, task_list in allocable_data_dict.items():
        task_list.sort(
            key=lambda x: (
                -parse_decimal(x["requirement_sort"]),
                -parse_decimal(x["priority"])
            )
        )

def add_database(cursor):
    sql = f"""UPDATE requirement_schedule_table SET plan_start_dev_date=%s,plan_finish_dev_date=%s,development_lead=%s WHERE id=%s"""
    cursor.execute("DELETE FROM return_rdc_pr_id_table")
    insert_sql = f"insert into return_rdc_pr_id_table (pr_id) values (%s)"
    if task_time_mapping:
        for each_id, each_lst in task_time_mapping.items():
            start = ""
            end = ""
            name_id_str = ""
            for each_dict in each_lst:
                start = each_dict["start_date"]
                end = each_dict["end_date"]
                name_id_str += (each_dict["name"]+each_dict["assigned_pid"])
                name_id_str += ','
            name_id_str = name_id_str[:-1]
            cursor.execute(insert_sql, each_id)
            cursor.execute(sql, (start, end, name_id_str, each_id))
    print(f"更新完成")

def replacement_time(start, end, final_result):
    new_data_iteration_dict = copy.deepcopy(db_mapping_config.data_iteration_dict)
    min_key = min(final_result.keys(), key=get_s_number)
    max_key = max(final_result.keys(), key=get_s_number)
    new_data_iteration_dict[min_key][0] = str(start)
    new_data_iteration_dict[max_key][1] = str(end)
    return new_data_iteration_dict

def get_s_number(key):
    # 找到"S"的位置，取后面的部分并转为整数
    s_index = key.find("S")
    # 确保能找到"S"且后面有数字（避免报错）
    if s_index != -1 and key[s_index+1:].isdigit():
        return int(key[s_index+1:])
    # 无有效数字时返回一个极大值（避免干扰正常比较）
    return float('inf')

def find_date_key(target_date_str):
    """
    根据目标日期字符串，查找其所属的字典key
    :param target_date_str: 目标日期，格式如 "2026-02-01"
    :param date_dict: 日期分段字典
    :return: 所属的key，若未找到返回None
    """
    target_date = target_date_str
    # 遍历字典，判断日期归属
    for key, (start_str, end_str) in db_mapping_config.data_iteration_dict.items():
        # 统一日期格式：替换/为-，并补全前导零（如 2026/2/8 → 2026-02-08）
        start_str = start_str.replace("/", "-")
        end_str = end_str.replace("/", "-")
        # 转换起止日期为datetime对象
        try:
            start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"字典中 {key} 的日期格式错误：{e}")
            continue
        # 判断目标日期是否在[开始, 结束]范围内
        if start_date <= target_date <= end_date:
            return key

def version_period_manpower(month_weekly_total_manpower_dict, product: str): # 新增product参数
    iteration_date_weekly_total_manpower_dict = {}
    for each_month, week_dict in month_weekly_total_manpower_dict.items():
        for each_week, sub_team_dict in week_dict.items():
            iteration_date = get_period_by_week(each_week)
            iteration_date_weekly_total_manpower_dict.setdefault(iteration_date, []).append(sub_team_dict)
    if not iteration_date_weekly_total_manpower_dict:
        return {}
    final_result = summarize_team_data(iteration_date_weekly_total_manpower_dict, product) # 透传产品
    return final_result

def summarize_team_data(raw_data, product: str): # 新增入参product
    summary_result = {}
    for s_period, team_list in raw_data.items():
        period_map = summary_result.setdefault(s_period, {})
        for team_dict in team_list:
            for team_name, prod_dict in team_dict.items():
                # 只遍历指定产品，其他产品直接跳过
                if product not in prod_dict:
                    continue
                person_list = prod_dict[product]
                team_map = period_map.setdefault(team_name, {})
                for person in person_list:
                    user_id = person["工号"]
                    existing_person = team_map.get(user_id)
                    if existing_person:
                        existing_person["迭代总人力"] = round(
                            existing_person["迭代总人力"] + float(person["每周总人力"]), 2
                        )
                        existing_person["法定工作日"] = round(
                            existing_person["法定工作日"] + float(person["法定工作日"]), 2
                        )
                        existing_person["已用人力"] = round(
                            existing_person["已用人力"] + float(person["已用人力"]), 2
                        )
                        existing_person["剩余人力"] = round(
                            existing_person["剩余人力"] + float(person["剩余人力"]), 2
                        )
                    else:
                        team_map[user_id] = {
                            "姓名": person["姓名"],
                            "工号": user_id,
                            "迭代总人力": round(float(person["每周总人力"]), 2),
                            "法定工作日": round(float(person["法定工作日"]), 2),
                            "已用人力": round(float(person["已用人力"]), 2),
                            "剩余人力": round(float(person["剩余人力"]), 2)
                        }
    final_result = {}
    for s_period, team_map in summary_result.items():
        final_result[s_period] = [
            {team: list(person_dict.values())}
            for team, person_dict in team_map.items()
        ]
    return final_result

def get_period_by_week(week_str: str) -> str | None:
    week_pattern = re.compile(r'^(\d{4})-W(\d{1,2})$')
    match = week_pattern.match(week_str.strip())
    if not match:
        raise ValueError(f"周字符串格式错误，应为'YYYY-WNN'，当前输入：{week_str}")
    year = int(match.group(1))
    week_num = int(match.group(2))
    try:
        week_start_date = datetime.datetime.fromisocalendar(year, week_num, 1).date()
    except ValueError as e:
        raise ValueError(f"解析周数失败：{e}，输入周字符串：{week_str}")
    for period_key, (start_str, end_str) in db_mapping_config.data_iteration_dict.items():
        period_start = parse_date(start_str)
        period_end = parse_date(end_str)
        if period_start <= week_start_date <= period_end:
            return period_key
    return None

def parse_date(date_str: str) -> datetime.date:
    """兼容-和/分隔符的日期解析"""
    return datetime.datetime.strptime(date_str.replace('/', '-'), "%Y-%m-%d").date()

def calculate_the_remaining_manpower(month_weekly_total_manpower_dict):
    # 计算月份剩余工作量并获取为负数员工{月份:{团队:id}}
    negative_manpower_dict = calculate_negative_employees(month_weekly_total_manpower_dict)
    # 特殊处理：如果当月该成员剩余可用人力为负值（即在评估纳入时存在归零操作），则该月所覆盖自然周的剩余可用人力置0
    update_dictionary(month_weekly_total_manpower_dict, negative_manpower_dict)

def update_dictionary(month_weekly_total_manpower_dict, negative_manpower_dict):
    for each_month, team_dict in negative_manpower_dict.items():
        weekly_dict = month_weekly_total_manpower_dict.get(each_month, {})
        for each_sub_team, id_list in team_dict.items():
            for each_week, team_prod_dict in weekly_dict.items():
                # 修复1：多一层产品字典循环
                for prod_name, person_lst in team_prod_dict.get(each_sub_team, {}).items():
                    for each_person in person_lst:
                        employee_id = each_person.get("工号")
                        if employee_id in id_list:
                            each_person["剩余人力"] = Decimal('0.0000')

def calculate_negative_employees(month_weekly_total_manpower_dict):
    negative_manpower_dict = {}
    for each_month, weekly_dict in month_weekly_total_manpower_dict.items():
        # 月统计人力
        each_month_dict = month_manpower_statistics(each_month, weekly_dict)
        # 按月处理
        if not each_month_dict:
            continue
        # 标记月剩余工作量为负数员工
        mark_negative_employees(each_month_dict, negative_manpower_dict)
    return negative_manpower_dict

def mark_negative_employees(each_month_dict, negative_manpower_dict):
    for each_person_month, each_team_lst in each_month_dict.items():
        for each_dict in each_team_lst:
            for each_person_team, name_dict in each_dict.items():
                for emp_id, num in name_dict.items():
                    if num < 0:
                        negative_manpower_dict.setdefault(each_person_month, {}).setdefault(each_person_team,[]).append(emp_id)

def month_manpower_statistics(each_month, weekly_dict):
    each_month_dict = {}
    for each_week, sub_team_dict in weekly_dict.items():
        each_team_dict = {}
        for each_team, prod_dict in sub_team_dict.items():
            person_dict = {}
            # 修复：增加产品层循环，匹配真实数据结构
            for prod, person_lst in prod_dict.items():
                for each_person in person_lst:
                    emp_id = each_person.get("工号")
                    count = each_person.get("每周总人力", Decimal('0'))
                    used = each_person.get("已用人力", Decimal('0'))
                    remaining = count - used
                    each_person["剩余人力"] = remaining
                    if emp_id not in person_dict:
                        person_dict[emp_id] = remaining
                    else:
                        person_dict[emp_id] += remaining
            each_team_dict[each_team] = person_dict
        each_month_dict.setdefault(each_month, []).append(each_team_dict)
    return each_month_dict

def get_sub_team_total_pr(data_sub_team_lst, version_end, version_start, product, work_type, username, encrypted_password):
    team_pr_dict = {}
    for each_team in data_sub_team_lst:
        if '_' in each_team:
            each_sub_team = each_team.split('_')[0]
        else:
            each_sub_team = each_team
        sub_team_pr_lst = query_entrance(each_sub_team, product, work_type, username, encrypted_password,  str(version_end), str(version_start))["bo"]["result"]["items"]
        team_pr_dict[each_team] = sub_team_pr_lst
    return team_pr_dict

def used_manpower(month_weekly_total_manpower_dict, datetime_dict, data_sub_team_lst, product, work_type, username, encrypted_password):
    # 获取各子团队所有的已承诺pr
    version_start = datetime_dict.get("开始时间")
    version_end = datetime_dict.get("结束时间")
    team_pr_dict = get_sub_team_total_pr(data_sub_team_lst, version_end, version_start, product, work_type, username, encrypted_password)

    # ===================== 预扁平化结构 =====================
    flat_person_list = []
    for each_month, month_week_dict in month_weekly_total_manpower_dict.items():
        for each_week, sub_team_product_dict in month_week_dict.items():
            for each_sub_team, product_person_dict in sub_team_product_dict.items():
                # 遍历产品
                for prod_name, person_list in product_person_dict.items():
                    # 把每条人员数据带上 月/周/子团队/产品 信息，统一成一维列表
                    for person in person_list:
                        flat_person_list.append({
                            "month": each_month,
                            "week": each_week,
                            "sub_team": each_sub_team,
                            "product": prod_name,
                            "person": person,
                            "person_id": person.get("工号")
                        })
                        # 初始化已用人力使用Decimal保证高精度
                        person["已用人力"] = Decimal("0.00")
    # ===================== 构建 子团队+产品+工号 -> 人员映射 =====================
    team_product_user_map = defaultdict(lambda: defaultdict(dict))
    for item in flat_person_list:
        st = item["sub_team"]
        prod = item["product"]
        pid = item["person_id"]
        team_product_user_map[st][prod][pid] = item["person"]
    # ===================== PR 循环 =====================
    for each_sub_team, pr_list in team_pr_dict.items():
        sub_team_product_map = team_product_user_map.get(each_sub_team, {})
        if not sub_team_product_map:
            continue
        for each_pr in pr_list:
            # 快速过滤无效PR
            start_str = each_pr.get("PlanStartDateOfDevelopment", "")
            end_str = each_pr.get("PlanFinishDateOfDevelopment", "")
            workload = each_pr.get("EstimatedEffortOfDevelopment")
            pr_owner = each_pr.get("DevelopmentOwner")
            if not all([start_str, end_str, workload, pr_owner]):
                continue
            # 日期解析
            try:
                start = datetime.datetime.strptime(start_str.split("T")[0], "%Y-%m-%d").date()
                end = datetime.datetime.strptime(end_str.split("T")[0], "%Y-%m-%d").date()
            except Exception:
                continue
            # 版本时间过滤
            if not (start <= version_end and end >= version_start):
                continue
            workload = Decimal(str(workload))
            unique_ids = get_pr_name(pr_owner)
            owner_count = Decimal(len(unique_ids) if len(unique_ids) >= 2 else 1)
            # 计算工作日
            total_workday_count, _, _, _, _, month_week_workday_dict = calculate_month_and_workdays(start, end)
            total_workday_count = Decimal(total_workday_count)
            if total_workday_count <= Decimal("0"):
                continue
            daily_workload = workload / total_workday_count / owner_count
            # ===================== 按 月+周 累加 =====================
            for pr_month, pr_weekly_lst in month_week_workday_dict.items():
                for pr_week_dict in pr_weekly_lst:
                    for pr_week, workday in pr_week_dict.items():
                        workday_dec = Decimal(workday)
                        add = workday_dec * daily_workload
                        # 批量给责任人累加，只扣减入参指定product的人力
                        for uid in unique_ids:
                            prod_user_dict = sub_team_product_map.get(product, {})
                            person = prod_user_dict.get(uid)
                            if person:
                                person["已用人力"] = (person["已用人力"] + add).quantize(Decimal('0.0000'))

def get_pr_name(pr_owner):
    user_id_lst = []
    for each_dict in pr_owner:
        each_id = each_dict.get("userId")
        user_id_lst.append(each_id)
    return user_id_lst

def version_manpower(month_weekly_total_manpower_dict):
    sub_team_person_dict = {}
    for each_month, month_week_dict in month_weekly_total_manpower_dict.items():
        for each_week, sub_team_dict in month_week_dict.items():
            for each_sub_team, team_person_lst in sub_team_dict.items():
                filter_manpower(each_sub_team, team_person_lst, sub_team_person_dict)
    return sub_team_person_dict

def filter_manpower(each_sub_team, team_person_lst, sub_team_person_dict):
    for each_person_data_dict in team_person_lst:
        name = each_person_data_dict.get("姓名")
        id = each_person_data_dict.get("工号")
        person_lst = sub_team_person_dict.setdefault(each_sub_team, [])
        if {id:name} not in person_lst:
            person_lst.append({id:name})

def safe_float(val, default=0.0):
    """安全转换为浮点数，失败返回默认值"""
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default

def sub_team_person_data(results_data_lst, data_sub_team_lst):
    try:
        team_product_person_dict = {}
        for each_data in results_data_lst:
            sub_team = each_data.get("team")
            skill_category = each_data.get("skill_category", None)
            if skill_category:
                sub_team = '_'.join([sub_team, skill_category])
            if sub_team in data_sub_team_lst:
                year_month = each_data.get("year_month")
                name = each_data.get("name")
                employee_id = each_data.get("employee_id")
                demand_human_power_ratio = safe_float(each_data.get("demand_human_power_ratio"))
                # 各产品单独取值
                zxone_19700 = safe_float(each_data.get("zxone_19700"))
                zxone_9700 = safe_float(each_data.get("zxone_9700"))
                zxmp_m721 = safe_float(each_data.get("zxmp_m721"))
                zxone_nton = safe_float(each_data.get("zxone_nton"))

                employee_work_proportion = {
                    "姓名": name,
                    "工号": employee_id,
                    "投入PR工作量占比": demand_human_power_ratio,
                    "zxone_19700投入占比": zxone_19700,
                    "zxone_9700投入占比": zxone_9700,
                    "zxmp_m721投入占比": zxmp_m721,
                    "zxone_nton投入占比": zxone_nton
                }
                team_product_person_dict.setdefault(year_month, {}).setdefault(sub_team, []).append(employee_work_proportion)
        return team_product_person_dict
    except Exception as e:
        print(f"sub_team_person_data查询失败：{str(e)}")
        raise


def version_weekly_available_manpower(team_product_person_dict, datetime_dict):
    month_weekly_total_manpower_dict = {}
    version_date_time_dict = datetime_dict.get("月周映射", {})
    product_name = datetime_dict.get("产品", None)
    PROPORTION_PRECISION = Decimal("0.0000")  # 人力计算精度
    # 第一层循环：月份
    for month, week_work_lst in version_date_time_dict.items():
        month_person_data = team_product_person_dict.get(month, {})
        if not month_person_data:
            continue
        month_dict = month_weekly_total_manpower_dict.setdefault(month, {})
        # 第二层循环：周
        for each_week_dict in week_work_lst:
            week = next(iter(each_week_dict.keys()), None)
            work_days = next(iter(each_week_dict.values()), 0)
            if not week or work_days <= 0:
                continue
            week_dict = month_dict.setdefault(week, {})
            # 第三层循环：子团队
            for sub_team, person_data_lst in month_person_data.items():
                product_group_dict = calculate_person_manpower(person_data_lst, work_days, PROPORTION_PRECISION, product_name)
                week_dict[sub_team] = product_group_dict
    return month_weekly_total_manpower_dict

def calculate_person_manpower(person_data_lst, work_days, precision, filter_product=None):
    product_manpower_dict = {}
    REQUIRED_BASE_FIELDS = ["姓名", "工号", "投入PR工作量占比"]
    if not filter_product:
        return product_manpower_dict
    prod_raw = filter_product.replace(" ", "_").lower()
    target_key = f"{prod_raw}投入占比"
    work_days_dec = Decimal(str(work_days))
    for each_person_data_dict in person_data_lst:
        missing_fields = [f for f in REQUIRED_BASE_FIELDS if f not in each_person_data_dict]
        if missing_fields:
            continue
        name = each_person_data_dict["姓名"]
        id_ = each_person_data_dict["工号"]
        pr_work = Decimal(str(each_person_data_dict["投入PR工作量占比"]))
        if target_key not in each_person_data_dict:
            continue
        try:
            product_proportion = Decimal(str(each_person_data_dict[target_key]))
        except (ValueError, TypeError):
            continue
        weekly_total_manpower = (work_days_dec * pr_work * product_proportion).quantize(
            precision, rounding=ROUND_HALF_UP)
        item = {
            "姓名": name,
            "工号": id_,
            "产品名": filter_product,
            "每周总人力": weekly_total_manpower,
            "法定工作日": work_days
        }
        product_manpower_dict.setdefault(filter_product, []).append(item)
    return product_manpower_dict

def query_entrance(sub_team, product, work_type, username, encrypted_password, end_time, start_time):
    work_type = db_mapping_config.work_type_dict.get(work_type)
    team_code = db_mapping_config.team_code_mapping_dict.get(sub_team)
    product_value = db_mapping_config.product_mapping_dict.get(product)
    URL = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/WIC/rest/workspaces/OTNSW/queries/query_work_items"
    # x_auth = get_x_auth_val(user=username, encrypted_pwd=encrypted_password)
    x_auth = '1af706bc5fdcb1bfdcf97f273fc857e4'
    Header = {
        "X-Tenant-Id": "ZTE",
        "X-Lang-Id": "zh_CN",
        "X-Emp-No": username,
        "X-Auth-Value": x_auth,
        "appcode": "4811ee4055a74cb4b52e7295e1d1858d",
        "Content-Type": "application/json"
    }
    body = {
        "queryCondition": {
            "depth": 6,
            "relatedType": [
                "linkRelatedType_3"
            ],
            "removeTop": True,
            "sourceClauses": [
                {
                    "field": "System_WorkItemType",
                    "leftGroup": 0,
                    "logicalOperator": "",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": work_type
                },
                {
                    "field": "Team",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "=_accurate",
                    "rightGroup": 0,
                    "value": {
                        "name": sub_team,
                        "label": sub_team,
                        "nameEn": "",
                        "hasNoChildren": True,
                        "value": team_code
                    }
                },
                {
                    "field": "System_State",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "not in",
                    "rightGroup": 0,
                    "value": [
                        "已废弃"
                    ]
                },
                {
                    "field": "AssessResult_First",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "like",
                    "rightGroup": 0,
                    "value": "可纳入"
                },
                {
                    "field": "FinishTimeOfDevelopment",
                    "leftGroup": 1,
                    "logicalOperator": "AND",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": None
                },
                {
                    "field": "FinishTimeOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "OR",
                    "operator": ">=",
                    "rightGroup": 1,
                    "value": start_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 2,
                    "logicalOperator": "AND",
                    "operator": "<=",
                    "rightGroup": 0,
                    "value": end_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">=",
                    "rightGroup": 1,
                    "value": start_time
                },
                {
                    "field": "PlanStartDateOfDevelopment",
                    "leftGroup": 1,
                    "logicalOperator": "OR",
                    "operator": "<",
                    "rightGroup": 0,
                    "value": end_time
                },
                {
                    "field": "PlanFinishDateOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">",
                    "rightGroup": 2,
                    "value": end_time
                },
                {
                    "field": "System_Id",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "!=",
                    "rightGroup": 0,
                    "value": None
                },
                {
                    "field": "BelongProduct",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "=_accurate",
                    "rightGroup": 0,
                    "value": {
                        "name": product,
                        "label": product,
                        "nameEn": "",
                        "hasNoChildren": True,
                        "value": product_value
                    }
                }
            ],
            "targetClauses": [
                {
                    "field": "System_Id",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "!=",
                    "rightGroup": 0,
                    "value": None
                }
            ],
            "treeOptions": "top",
            "type": "tree"
        },
        "selectItems": [
            {
                "key": "System_WorkItemType",
                "name": "工作项类型",
                "type": "workItemType",
                "width": "105"
            },
            {
                "key": "System_Id",
                "name": "标识",
                "type": "workItemNo",
                "width": ""
            },
            {
                "key": "System_Title",
                "name": "标题",
                "type": "string",
                "width": "137.79998779296875"
            },
            {
                "key": "System_AreaPath",
                "name": "领域",
                "type": "advancedData",
                "width": "84"
            },
            {
                "key": "Team",
                "name": "团队",
                "type": "advancedData",
                "width": "114.20001220703125"
            },
            {
                "key": "FeatureId",
                "name": "特性标识",
                "type": "string",
                "width": "119.01251220703125"
            },
            {
                "key": "FeatureAttribute",
                "name": "特性属性",
                "type": "string",
                "width": "54.7999267578125"
            },
            {
                "key": "AssessResult_First",
                "name": "评估结论（第一次）",
                "type": "string",
                "width": ""
            },
            {
                "key": "EstimatedEffortOfDevelopment",
                "name": "预计开发工作量",
                "type": "double",
                "width": "56.7999267578125"
            },
            {
                "key": "PlanStartDateOfDevelopment",
                "name": "计划开始开发日期",
                "type": "date",
                "width": "106.5999755859375"
            },
            {
                "key": "PlanFinishDateOfDevelopment",
                "name": "计划完成开发日期",
                "type": "date",
                "width": "74.449951171875"
            },
            {
                "key": "ProductRoadmap",
                "name": "产品路标",
                "type": "string",
                "width": ""
            },
            {
                "key": "RequirementPrePlanning",
                "name": "需求预规划",
                "type": "string",
                "width": ""
            },
            {
                "key": "BelongProduct",
                "name": "所属产品",
                "type": "advancedData",
                "width": ""
            },
            {
                "key": "DevelopmentOwner",
                "name": "开发负责人",
                "type": "user",
                "width": ""
            },
            {
                "key": "SkillType",
                "name": "技能类型",
                "type": "user",
                "width": ""
            }
    ],
    "pageSize": 8000
    }
    response = requests.post(URL, json=body, headers=Header)
    try:
        content = response.text
        return dict(json.loads(content))  # 转字典
    except Exception as e:
        print(f'get_PR_field():{e}')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
person_last_info = {}  # {pid: {"date": date, "day_remaining": 0.1}}
task_time_mapping = {}


def add_workdays(start, days):
    if days <= 0:
        return start
    cur = start
    count = 0
    while count < days:
        # 先往后挪一天，再判断是否工作日
        cur += timedelta(days=1)
        if cur.year > 2026:
            is_wd = cur.weekday() < 5
        else:
            is_wd = is_workday(cur)
        if is_wd:
            count += 1
    return cur

def extract_numbers_from_str(s):
    return re.findall(r"\d+", str(s))

def get_iteration_date_range(iter_code, iter_date_map):
    date_range = iter_date_map.get(iter_code)
    if not date_range:
        today = datetime.datetime.today().date()
        return today, today
    start_str, end_str = date_range
    return parse_date(start_str), parse_date(end_str)

def get_next_iteration_code(code):
    if not code or len(code) < 5:
        return None
    prefix = code[:4]
    suffix = code[4:].upper()
    if not suffix.startswith("S"):
        return None
    try:
        num = int(suffix[1:])
        # 终止条件
        if code == "2027S1":
            return None
        if prefix == "2026" and num == 25:
            return "2027S1"
        return f"{prefix}S{num+1}"
    except:
        return None


def calculate_real_end_date(pid, start_date, workload, daily_man):
    current_date = start_date
    pid_str = str(pid).strip()
    person_info = person_last_info.get(pid_str, None)
    flag = False
    if not person_info:
        # 无历史记录
        remain_work = workload
    else:
        last_remain = person_info.get("day_remaining", 0.0)
        if last_remain == 0:
            # 历史剩余工时为0，开始日期先顺延1个工作日
            current_date = add_workdays(current_date, 1)
            remain_work = workload
            flag = True
        else:
            # 历史剩余工时大于0
            if workload <= last_remain:
                return current_date, flag
            # 抵扣历史余量
            remain_work = workload - last_remain
            current_date = add_workdays(current_date, 1)

    # 根据剩余工时计算最终日期
    if remain_work <= daily_man:
        return current_date, flag
    total_days = math.ceil(remain_work / daily_man)
    extra_days = total_days - 1
    return add_workdays(current_date, extra_days), flag

def select_assigned_persons(assigned_pids, final_result, start_iter, sub_team):
    valid_pids = []
    max_steps = 100
    for pid in assigned_pids:
        cur_iter = start_iter
        found = False
        step = 0
        while cur_iter and step < max_steps:
            step += 1
            if cur_iter in final_result:
                for td in final_result[cur_iter]:
                    tn = next(iter(td.keys()))
                    if tn != sub_team:
                        continue
                    for p in td[tn]:
                        if str(p.get("工号")).strip() == pid.strip():
                            valid_pids.append(pid)
                            found = True
                            break
                    if found:
                        break
            if found:
                break
            cur_iter = get_next_iteration_code(cur_iter)
    return valid_pids

def auto_select_earliest_person(final_result, start_iter, sub_team, workload, default_start_date):
    person_candidates = {}
    max_steps = 100
    step = 0
    cur_iter = start_iter
    # 仅当前迭代不存在时，向后查找
    find_step = 0
    while cur_iter and cur_iter not in final_result and find_step < max_steps:
        cur_iter = get_next_iteration_code(cur_iter)
        find_step += 1
    # 最终仍无有效迭代，直接返回 None
    if not cur_iter or cur_iter not in final_result:
        return None
    # 实际命中迭代
    real_hit_iter = cur_iter
    # 全局状态快照
    person_snapshot = person_last_info.copy()
    # 从有效迭代开始向后遍历
    while cur_iter in final_result and step < max_steps:
        step += 1
        for td in final_result[cur_iter]:
            tn = next(iter(td.keys()))
            if tn != sub_team:
                continue
            for p in td[tn]:
                pid = str(p.get("工号")).strip()
                rem = float(p.get("剩余人力", 0))
                legal = float(p.get("法定工作日", 5))
                if rem <= 0 or legal <= 0:
                    continue
                daily = round(rem / legal, 3)
                # 从快照读取状态
                if pid in person_snapshot:
                    last_date = person_snapshot[pid]["date"]
                    last_remaining = person_snapshot[pid]["day_remaining"]
                    start_date = last_date if last_remaining > 0 else add_workdays(last_date, 1)
                else:
                    start_date = default_start_date
                end_date, flag = calculate_real_end_date(pid, start_date, workload, daily)
                if flag:
                    start_date = add_workdays(start_date, 1)
                person_candidates[pid] = {
                    "daily": daily,
                    "start_date": start_date,
                    "end_date": end_date,
                    "iter": cur_iter
                }
                if daily > 0:
                    curr_work = workload
                    last_remain = person_snapshot.get(pid, {}).get("day_remaining", 0.0)
                    if last_remain >= curr_work:
                        snap_remain = round(last_remain - curr_work, 2)
                    else:
                        need_work = curr_work - last_remain
                        snap_remain = calc_day_remain(daily, need_work)
                    person_snapshot[pid] = {"date": end_date, "day_remaining": snap_remain}
        cur_iter = get_next_iteration_code(cur_iter)
    if not person_candidates:
        return None
    # 按结束日期升序，选择最早完工人员
    sorted_persons = sorted(person_candidates.items(), key=lambda x: x[1]["end_date"])
    best_pid = sorted_persons[0][0]
    best_info = sorted_persons[0][1]
    # 实际命中迭代、选中工号、人员信息
    return real_hit_iter, best_pid, best_info

# ===================== 主排期 =====================
def sub_team_allocable_pr(allocable_data_dict, final_result, version_start_date, iter_date_map):
    global person_last_info, task_time_mapping
    person_last_info.clear()
    task_time_mapping.clear()
    default_start_date, _ = get_iteration_date_range(version_start_date, iter_date_map)
    for sub_team, tasks in allocable_data_dict.items():
        for task in tasks:
            evaluation = task.get("first_evaluation_conclusion", None)
            pr_dev = task.get("plan_start_dev_date", None)
            pr_fin = task.get("plan_finish_dev_date", None)
            if evaluation == '无法纳入' or not evaluation:
                continue
            if pr_dev and pr_fin:
                continue
            task_id = task.get("id")
            workload = task.get("estimated_dev_workload")
            if not (judge(workload) and task_id):
                continue
            workload = float(workload)
            dev_lead = task.get("development_lead", "")
            assigned_pids = extract_numbers_from_str(dev_lead)
            selected_persons = []
            current_hit_iter = None
            if judge(assigned_pids):
                selected_persons = select_assigned_persons(assigned_pids, final_result, version_start_date, sub_team)
            else:
                auto_res = auto_select_earliest_person(final_result, version_start_date, sub_team, workload, default_start_date)
                if auto_res:
                    hit_iter, pid, info = auto_res
                    current_hit_iter = hit_iter
                    selected_persons = [pid]
            if not selected_persons:
                continue
            person_count = len(selected_persons)
            split_workload = round(workload / person_count, 2)
            for idx, selected_pid in enumerate(selected_persons):
                person_info = None
                for it in final_result:
                    for td in final_result[it]:
                        for tn, pl in td.items():
                            for p in pl:
                                if str(p.get("工号")).strip() == selected_pid:
                                    rem = float(p.get("剩余人力", 0))
                                    legal = float(p.get("法定工作日", 5))
                                    name = p.get("姓名", "").strip()
                                    person_info = {"daily": round(rem / legal, 3),
                                                   "name": name
                                                   }
                                    break
                            if person_info:
                                break
                        if person_info:
                            break
                if not person_info:
                    continue
                daily = person_info["daily"]
                # 只负责获取上一次的结束日期，不再手动抵扣工时
                if selected_pid in person_last_info:
                    start_date = person_last_info[selected_pid]["date"]
                else:
                    if current_hit_iter:
                        start_date, _ = get_iteration_date_range(current_hit_iter, iter_date_map)
                        print(f"分支1{start_date}")
                    else:
                        start_date = default_start_date
                        print(f"分支2{start_date}")

                # 统一调用函数计算结束日期（内部自动抵扣历史余量）
                end_date, flag = calculate_real_end_date(selected_pid, start_date, split_workload, daily)
                if flag:
                    start_date = add_workdays(start_date, 1)
                # 单独计算本次任务后的剩余工时
                last_remain = person_last_info.get(selected_pid, {}).get("day_remaining", 0.0)
                curr_work = split_workload
                if last_remain >= curr_work:
                    day_remaining = round(last_remain - curr_work, 2)
                else:
                    need_work = curr_work - last_remain
                    day_remaining = calc_day_remain(daily, need_work)
                # 更新全局人员状态
                person_last_info[selected_pid] = {
                    "date": end_date,
                    "day_remaining": day_remaining
                }
                print(f"【任务 {task_id} - 第 {idx+1} 个负责人】")
                print(f"  负责人工号：{selected_pid}")
                print(f"  总工作量：{workload} | 人均工作量：{split_workload}")
                print(f"  每日可用人力：{daily}")
                print(f"  开始日期：{start_date}")
                print(f"  结束日期：{end_date}")
                print(f"  当日剩余人力：{day_remaining}\n")
                if task_id not in task_time_mapping:
                    task_time_mapping[task_id] = []
                task_time_mapping[task_id].append({
                    "start_date": start_date,
                    "end_date": end_date,
                    "assigned_pid": selected_pid,
                    "workload": split_workload,
                    "name": person_info["name"]
                })


def calc_day_remain(daily_capacity: float, need_work: float) -> float:
    """
    计算单日剩余工时
    :param daily_capacity: 单日总产能
    :param need_work: 需要完成的工作量
    :return: 当日剩余工时（正确版）
    """
    if need_work <= 0:
        return round(daily_capacity, 2)

    # 最后一天剩余的工作量
    last_day_work = need_work % daily_capacity
    if last_day_work == 0:
        return 0.0
    # 剩余人力 = 单日产能 - 最后一天消耗
    remain = daily_capacity - last_day_work
    return round(remain, 2)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5078, debug=True)
    # search()



