from datetime import datetime, timedelta
import time
try:
    from requirement_schedule import auto_scheduling_process, db_mapping_config
except ImportError:
    import auto_scheduling_process
    import db_mapping_config
import base64
import json
import hashlib
import requests
import traceback
from socket import socket, AF_INET, SOCK_DGRAM
import pymysql
from pymysql.err import OperationalError, ProgrammingError, DataError
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

@app.route("/test", methods=["POST"])
def manpower_calculate(username, encrypted_password):
    """

    :param username:
    :param encrypted_password:
    :return:
    """
    db = None
    cursor = None
    try:
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        # 人力视图表2
        select_sql = "select * from requirement_dev_human_resource"
        cursor.execute(select_sql)
        results_data_lst = cursor.fetchall()
        # 团队归类 团队名称表
        team_work_dict, total_team_name_lst = get_team_data(cursor)
        # 版本日期数据
        vesion_workday_dict = get_version_date_data(cursor)
        # (子)团队个人各月所需交付投入占比和产品占比
        team_month_proportion_dict = product_proportion(results_data_lst, vesion_workday_dict, total_team_name_lst)
        # 按月计算(子)团队成员可用人数并累加和所有人力
        version_available_personnel_dict = number_of_available_personnel(team_month_proportion_dict)
        # 汇总全部人力
        db_dict = collect_sub_team_manpower(version_available_personnel_dict)
        # 计算(子)团队个人已占用人力资源 和剩余可用人力
        team_occupied_remaining_workload(team_work_dict, db_dict, vesion_workday_dict, username, encrypted_password)
        # 计算整个团队版本周期内剩余可用人力（汇总时月负值归零）
        # collect_sub_team_powerman_dict = toppriority.collect_sub_team_powerman(version_available_personnel_dict)
        # 入库
        remaining_manpower(cursor, db_dict)
        db.commit()
        print("===== 所有数据优先级已更新，事务已提交 =====", flush=True)
        return "", 200
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        error_msg = f"数据库操作异常，已回滚事务，错误信息：{str(e)}"
        print(error_msg)
        print(traceback.print_exc())
        return jsonify({"code": 500, "status": "error", "message": error_msg}), 500
    except Exception as e:
        if db:
            db.rollback()
        error_msg = f"程序运行异常，已回滚事务，错误信息：{str(e)}"
        print(error_msg)
        print(traceback.print_exc())
        return jsonify({"code": 500, "status": "error", "message": error_msg}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def remaining_manpower(cursor, db_dict):
    # 数据预处理完毕，开始数据库操作：先删旧数据再批量插入（在同一事务内，失败可回滚）
    cursor.execute("DELETE FROM domain_team_available_human_resource")
    insert_sql = f"insert into domain_team_available_human_resource " \
                 f"(department, domain, team, team_type, skill_category, total_human_resource, zte_human_resource, " \
                 f"outsourcing_human_resource, demand_delivery_available, remaining_available_human_resource, " \
                 f"used_human_resource, used_human_resource1, date) values (%s, %s, %s, %s, %s, %s, %s, %s, " \
                 f"%s, %s, %s, %s, %s)"
    for each_month, team_dict in db_dict.items():
        for sub_team, data in team_dict.items():
            department = data.get("部门")
            domain = data.get("领域")
            team_type = data.get("团队类型")
            skill_type = data.get("技能类型")
            total_count = data.get("总人力")
            zte_count = data.get("中兴人力")
            out_count = data.get("外包人力")
            total_manpower = data.get("可用人力")
            remaining_count = data.get("剩余人力")
            used_count = data.get("已用人力")
            cursor.execute(insert_sql, (department, domain, sub_team, team_type, skill_type, str(total_count),
                                        str(zte_count), str(out_count), str(total_manpower), str(remaining_count),
                                        str(used_count), str(used_count), each_month))
            print(f"插入数据成功{each_month}月{department}")

def collect_sub_team_manpower(version_available_personnel_dict):
    db_dict = {}
    for each_month, sub_team_dict in version_available_personnel_dict.items():
        for sub_team, person_lst in sub_team_dict.items():
            zte_count = 0
            out_count = 0
            total_count = len(person_lst)
            if '_' in sub_team:
                skill_type = sub_team.split("_")[1]
            else:
                skill_type = None
            department = None
            team_type = None
            domain = None
            total_manpower = Decimal(0.00)
            for each_person in person_lst:
                department = each_person[4]
                domain = each_person[5]
                total_manpower += each_person[2]
                if each_person[6] == "中兴":
                    zte_count += 1
                else:
                    out_count += 1
            db_dict.setdefault(each_month, {}).setdefault(sub_team, {"部门":department , "领域":domain ,
                                                                     "团队类型":team_type , "技能类型":skill_type ,
                                                                     "总人力":total_count , "中兴人力":zte_count ,
                                                                     "外包人力":out_count , "可用人力":total_manpower,
                                                                     "剩余人力":total_manpower, "已用人力":Decimal(0.00),
                                                                     })
    return db_dict

def number_of_available_personnel(team_month_proportion_dict):
    """
    以团队来划分人员并计算每月所有人力
    :param team_month_proportion_dict:团队月全部人力字典
    :param month_weekly_workday:版本法定日期表
    :return:version_available_personnel_dict团队月产品全部人力字典
    """
    version_available_personnel_dict = {}
    for month, value_lst in team_month_proportion_dict.items():
        work_day = auto_scheduling_process.get_month_legal_workdays(month)
        sub_team_each_dict = {}
        if not value_lst:
            version_available_personnel_dict[month] = sub_team_each_dict
            continue
        for each_value in value_lst:
            team, proportion_str, *product_pro_str_list = each_value
            product_pro_str_list = product_pro_str_list[:4]
            for index, each in enumerate(product_pro_str_list):
                if not each:
                    product_pro_str_list[index] = Decimal(0.0)# 仅取前4个产品占比
            proportion = auto_scheduling_process.safe_float(proportion_str)
            # product_pro = sum([Decimal(x) for x in product_pro_str_list])
            # available_human = 1 * Decimal(proportion) * product_pro * work_day
            available_human = 1 * Decimal(proportion) * work_day
            available_human = available_human.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            new_item = [team, proportion_str]
            # available_human加进去（替换原来的4个占比）
            new_item.append(available_human)
            # 把后面的字段（除了前2个 + 占比）全部加回去
            new_item.extend(each_value[6:])
            sub_team_each_dict.setdefault(team, []).append(new_item)
        version_available_personnel_dict.setdefault(month, sub_team_each_dict)
        print(version_available_personnel_dict)
    return version_available_personnel_dict

def team_occupied_remaining_workload(team_work_dict, db_dict, vesion_workday_dict, username, encrypted_password):
    for each_team, pr_lst in team_work_dict.items():
        for each_product in list(vesion_workday_dict.keys()):
            work_type = ""
            for each_pr in pr_lst:
                each_work_type = each_pr.get("work_item_type")
                if work_type != each_work_type:
                    work_type = each_work_type
                else:
                    continue
            all_data_dict = get_PR_field(each_team.split('_')[0], each_product, work_type,
                                     username, encrypted_password, "2026-12-31", "2026-01-01")
            if all_data_dict and all_data_dict["bo"] and all_data_dict["bo"]["result"] and all_data_dict["bo"]["result"]["items"]:
                if "_" in each_team:
                    sub_team_name = each_team.split('_')[1]
                    # 过滤技能类型函数，原3条条件已加入接口筛选
                    filter_pr_data_lst = auto_scheduling_process.filter_pr_data(sub_team_name, all_data_dict["bo"]["result"]["items"])
                    occupation_merge(filter_pr_data_lst, each_team, db_dict)
                else:
                    occupation_merge(all_data_dict["bo"]["result"]["items"], each_team, db_dict)


    # 获取数据中团队下出现的所有产品和版本 后续如分产品可用以下代码
    # pr_team_existence_version_dict = {}
    # for sub_team, pr_lst in team_work_dict.items():
    #     product = None
    #     for each_pr in pr_lst:
    #         sub_product = each_pr.get("belong_product")
    #         if sub_product == product:
    #             break
    #         else:
    #             product = sub_product
    #         work_type = each_pr.get("work_item_type")
    #         date_lst = vesion_workday_dict.get(sub_product)
    #         if not date_lst:
    #             continue
    #         for each_month in date_lst:
    #             start_time = each_month.get("版本启动日期")
    #             end_time = each_month.get("完成开发日期")
    #             # {团队:[{产品: {"工作项":..., "启动日期":..., "完成日期":...}},...]}
    #             if sub_team not in pr_team_existence_version_dict.keys():
    #                 pr_team_existence_version_dict[sub_team] = [{sub_product:{"工作项":work_type, "版本启动日期":start_time,
    #                                                                                          "完成开发日期":end_time}}]
    #             else:
    #                 pr_team_existence_version_dict[sub_team].append({sub_product:{"工作项":work_type, "版本启动日期":start_time,
    #                                                                                          "完成开发日期":end_time}})
    #
    # for sub_team, product_lst in pr_team_existence_version_dict.items():
    #     for each_product in product_lst:
    #         product = list(each_product.keys())[0]
    #         work_type = each_product.get(product).get("工作项")
    #         all_data_dict = get_PR_field(sub_team.split('_')[0], product, work_type,
    #                                  username, encrypted_password, "2026-12-31", "2026-01-01")  # 需要填入动态参数
    #         # 团队可能区分有技能类型和没有技能类型，如有技能类型则需过滤出同一技能类型的pr
    #         if all_data_dict["bo"] and all_data_dict["bo"]["result"] and all_data_dict["bo"]["result"]["items"]:
    #             if "_" in sub_team:
    #                 sub_team_name = sub_team.split('_')[1]
    #                 # 过滤技能类型函数，原3条条件已加入接口筛选
    #                 filter_pr_data_lst = auto_scheduling_process.filter_pr_data(sub_team_name, all_data_dict["bo"]["result"]["items"])
    #                 occupation_merge(filter_pr_data_lst, sub_team, db_dict)
    #             else:
    #                 occupation_merge(all_data_dict["bo"]["result"]["items"], sub_team, db_dict)

def occupation_merge(filter_pr_data_lst, each_team, db_dict):
    # 月度汇总字典 key：月份，value：{ "total_workload": 总工作量, "total_days": 总工作日 }
    monthly_summary = defaultdict(lambda: {"total_workload": Decimal(0)})
    # ===================== 遍历所有任务 周数据汇总成月数据 =====================
    for each_pr in filter_pr_data_lst:
        pr_id = each_pr.get("id", "未知ID")
        feature_identifier = each_pr.get("FeatureId")
        estimated_dev_workload = auto_scheduling_process.safe_float(each_pr.get("EstimatedEffortOfDevelopment"))
        # 过滤无效任务
        if not feature_identifier or not estimated_dev_workload:
            print(f"[跳过] PR {pr_id} 缺少唯一标识或工作量")
            continue
        # 解析时间
        try:
            pr_start_time = each_pr["PlanStartDateOfDevelopment"].split("T")[0]
            pr_end_time = each_pr["PlanFinishDateOfDevelopment"].split("T")[0]
            start = datetime.strptime(pr_start_time, "%Y-%m-%d").date()
            end = datetime.strptime(pr_end_time, "%Y-%m-%d").date()
        except:
            print(f"[时间错误] PR {pr_id}")
            continue
        # 计算时间拆分
        try:
            total_workday_count, _, _, _, _, month_week_workday_dict = \
                auto_scheduling_process.calculate_month_and_workdays(start, end)
            if total_workday_count <= 0:
                continue
        except:
            print(f"[计算工作日失败] PR {pr_id}")
            continue
        # 日均工作量
        daily_workload = Decimal(str(estimated_dev_workload)) / Decimal(str(total_workday_count))
        # ===================== 按周计算，汇总到月 =====================
        for each_month, weekly_list in month_week_workday_dict.items():
            month_total_workload = Decimal(0)
            for week_dict in weekly_list:
                if not week_dict:
                    continue
                week_name, week_days = next(iter(week_dict.items()))
                week_workload = daily_workload * Decimal(str(week_days))
                # 累加到当前月份
                month_total_workload += week_workload
            # 把当前任务的【月度数据】汇总到总字典
            monthly_summary[each_month]["total_workload"] += month_total_workload
    # ===================== 按月扣减 =====================
    print(f"\n==================== 开始统一扣减 {each_team} 人力 ====================")
    for month, data in monthly_summary.items():
        start_time, finish_time = get_month_start_end(month)
        start = datetime.strptime(start_time, "%Y-%m-%d").date()
        end = datetime.strptime(finish_time, "%Y-%m-%d").date()
        total_workday_count, _, _, _, _, _ = \
            auto_scheduling_process.calculate_month_and_workdays(start, end)
        total_workload = data["total_workload"]
        if total_workload <= 0:
            continue
        try:
            print(f"month,{month}")
            print(f"each_team, {each_team}")
            team_data = db_dict.get(month, {}).get(each_team, {})
            team_data["剩余人力"] = team_data.get("剩余人力", 0)
            team_data["已用人力"] = team_data.get("已用人力", 0)
            # 每月执行一次扣减
            team_data["剩余人力"] -= total_workload
            team_data["已用人力"] += total_workload
            print(f"[{month}月] 总计扣减：工作量={float(total_workload):.2f}，工作日={total_workday_count}天，月/天{total_workload / Decimal(total_workday_count)}")
        except Exception as e:
            print(f"[{month}月] 扣减失败")
            traceback.print_exc()

def get_version_date_data(cursor):
    vesion_workday_dict = {}
    # 版本产品字典
    select_sql = "select * from version_table"
    data_lst = auto_scheduling_process.condition_query(cursor, select_sql, ())
    # 取当下时间的年份以及12个月
    timestamp = int(time.time())
    year = time.localtime(timestamp).tm_year
    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    # 获取各产品数据
    for each_data in data_lst:
        product = each_data.get("belong_product")
        # 去重
        if product not in vesion_workday_dict:
            for each_month in months:
                start_time, finish_time = get_month_start_end(each_month)
                start = datetime.strptime(start_time, "%Y-%m-%d").date()
                end = datetime.strptime(finish_time, "%Y-%m-%d").date()
                # 数据库中出现向前跨年情况，官方未给出法定节假日情况，默认按fallback是工作日
                workday_count, month_lst, total_weeks, week_lst, week_workday_dict, month_week_workday_dict \
                                                = auto_scheduling_process.calculate_month_and_workdays(start, end)
                if product not in vesion_workday_dict:
                    vesion_workday_dict[product] = []
                vesion_workday_dict[product].append({"月": month_lst, "天": workday_count, "月-天": month_week_workday_dict,
                                   "版本启动日期": start, "完成开发日期": end})
    return vesion_workday_dict

def get_month_start_end(month_str):
    """
    输入："yyyy-mm"
    返回：(开始日期 "yyyy-mm-dd", 结束日期 "yyyy-mm-dd")
    """
    # 转成年月对象
    dt = datetime.strptime(month_str, "%Y-%m")
    # 当月1号
    start_date = dt.replace(day=1)
    # 计算当月最后一天
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    end_date = next_month - timedelta(days=1)  # 最后一天
    # 返回 yyyy-mm-dd 字符串
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def get_team_data(cursor):
    select_sql = "select * from requirement_schedule_table"
    data_lst = auto_scheduling_process.condition_query(cursor, select_sql, ())
    # 团队pr字典 团队列表
    team_work_dict = {}
    total_team_name_lst = []
    for each_dict in data_lst:
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

def product_proportion(results_data_lst, vesion_workday_dict, total_team_name_lst):
    team_time_dict = {}
    for each_data in results_data_lst:
        team = each_data.get("team")
        skill = each_data.get("skill_category")
        value = '_'.join([team, skill]) if skill else team
        team_time = each_data.get("year_month")
        ratio = each_data.get("demand_human_power_ratio")
        zxone_19700 = each_data.get("zxone_19700")
        zxone_9700 = each_data.get("zxone_9700")
        zxmp_M721 = each_data.get("zxmp_m21")
        zxone_nton = each_data.get("zxone_nton")
        person_name = each_data.get("name")
        department = each_data.get("department")
        domain = each_data.get("domain")
        person_belong = each_data.get("person_belong")
        id = each_data.get("employee_id")
        team_time_dict[team_time] = team_time_dict.get(team_time, [])
        team_time_dict[team_time].append(
            [value, ratio, zxone_19700, zxone_9700, zxmp_M721, zxone_nton, person_name, department, domain,
             person_belong, id])
    # (子)团队个人版本内各月所需交付投入占比，产品占比
    team_month_proportion_dict = {}
    month_lst = []
    for product, date_lst in vesion_workday_dict.items():
        for each in date_lst:
            each_month = each.get("月")
            month_lst = list(set(month_lst + each_month))
    for each_month in month_lst:
        team_infos_lst = team_time_dict.get(each_month)
        team_month_proportion_dict[each_month] = team_infos_lst
    return team_month_proportion_dict

def get_PR_field(team_name, product, work_type, username, encrypted_password, end_time, start_time):
    work_type = db_mapping_config.work_type_dict.get(work_type)
    team_code = db_mapping_config.team_code_mapping_dict.get(team_name)
    product_value = db_mapping_config.product_mapping_dict.get(product)
    URL = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/WIC/rest/workspaces/OTNSW/queries/query_work_items"
    x_auth = get_x_auth_val(user=username, encrypted_pwd=encrypted_password)
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
                },
                {
                    "field": "EstimatedEffortOfDevelopment",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">",
                    "rightGroup": 0,
                    "value": "0"
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

if __name__ == '__main__':
    # 启动Flask服务，支持局域网访问
    CORS(app, supports_credentials=True)
    app.run(host="0.0.0.0", port=5071, debug=False)