import json
import hashlib
import pymysql
import pymysql.cursors
import requests
import base64
try:
    from requirement_schedule import db_mapping_config
except ImportError:
    import db_mapping_config
from socket import socket, AF_INET, SOCK_DGRAM
from pymysql.err import OperationalError, ProgrammingError, DataError
from requirement_schedule.all_team_manpower import manpower_calculate

def get_db_data(cursor):
    select_sql = "SELECT * FROM return_rdc_pr_id_table"
    cursor.execute(select_sql)
    data_id_lst = cursor.fetchall()
    return data_id_lst

def preview_backfill_count(params=None):
    """
    预览待回填到 RDC 的需求数量（不执行回填操作）
    :param params: 查询参数字典，包含 requirement_preplanning, work_type, domain, team 等
    :return: dict 包含 status、message 和 count
    """
    db = None
    cursor = None
    try:
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)

        if params:
            data_id_lst = get_pr_ids_by_params(params, cursor)
        else:
            data_id_lst = get_db_data(cursor)

        count = len(data_id_lst)
        return {"status": "success", "message": "统计完成", "count": count}
    except (OperationalError, ProgrammingError, DataError) as e:
        print(f"数据库错误：{e}")
        return {"status": "error", "message": f"数据库错误：{e}", "count": 0}
    except Exception as e:
        print(f"其他错误：{e}")
        return {"status": "error", "message": f"统计失败：{e}", "count": 0}
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

def backfill_RDC_data(employ_no=None, encrypted_password=None, params=None):
    """
    将 requirement_schedule_table 中的排期结果回填到 RDC
    :param employ_no: 工号
    :param encrypted_password: Base64 加密的密码
    :param params: 查询参数字典，包含 requirement_preplanning, work_type, domain, team 等
    :return: dict 包含 status 和 message
    """
    db = None
    cursor = None
    try:
        # 参数验证
        if not employ_no:
            print("错误：employ_no 不能为空")
            return {"status": "error", "message": "employ_no 不能为空"}
        if not encrypted_password:
            print("错误：encrypted_password 不能为空")
            return {"status": "error", "message": "encrypted_password 不能为空"}
        
        db = pymysql.connect(**db_mapping_config.db_config)
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        # 根据查询参数获取数据
        if params:
            data_id_lst = get_pr_ids_by_params(params, cursor)
        else:
            data_id_lst = get_db_data(cursor)
        
        results_data_lst = get_pr(data_id_lst, cursor)
        update_RDC(results_data_lst, employ_no, encrypted_password, cursor)
        # 更新人力视图数据库

        manpower_calculate(employ_no, encrypted_password)
        return {"status": "success", "message": "RDC 数据回填成功"}
    except (OperationalError, ProgrammingError, DataError) as e:
        print(f"数据库错误：{e}")
        return {"status": "error", "message": f"数据库错误：{e}"}
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{str(e)}")
        return {"status": "error", "message": f"请求失败：{str(e)}"}
    except Exception as e:
        print(f"其他错误：{e}")
        return {"status": "error", "message": f"回填失败：{e}"}
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def get_pr_ids_by_params(params, cursor):
    """
    根据查询参数获取 PR ID 列表
    :param params: 查询参数字典
    :param cursor: 数据库游标
    :return: PR ID 列表
    """
    base_sql = "SELECT id FROM requirement_schedule_table WHERE effective_flag = '1'"
    sql_params = []
    
    if params.get('requirement_preplanning'):
        req_val = params['requirement_preplanning']
        req_list = req_val.split(',') if isinstance(req_val, str) else req_val
        req_list = [x.strip() for x in req_list if x.strip()]
		
        placeholders = ', '.join(['%s'] * len(req_list))
        base_sql += f" AND requirement_preplanning IN ({placeholders})"
        sql_params.extend(req_list)
    
    if params.get('work_type'):
        # work_type 对应 work_item_type 字段
        val = params['work_type']
        lst = val.split(',') if isinstance(val, str) else val
        lst = [x.strip() for x in lst if x.strip()]

        placeholders = ', '.join(['%s'] * len(lst))
        base_sql += f" AND work_item_type IN ({placeholders})"
        sql_params.extend(lst)
    
    if params.get('domain'):
        val = params['domain']
        lst = val.split(',') if isinstance(val, str) else val
        lst = [x.strip() for x in lst if x.strip()]

        placeholders = ', '.join(['%s'] * len(lst))
        base_sql += f" AND domain IN ({placeholders})"
        sql_params.extend(lst)
    
    if params.get('team'):
        val = params['team']
        lst = val.split(',') if isinstance(val, str) else lst
        lst = [x.strip() for x in lst if x.strip()]

        placeholders = ', '.join(['%s'] * len(lst))
        base_sql += f" AND team IN ({placeholders})"
        sql_params.extend(lst)
    
    cursor.execute(base_sql, sql_params)
    results = cursor.fetchall()
    if not results:
        print(f"暂无需要回填的pr")
    # 转换为字典列表，格式与 get_db_data 一致
    return [{'pr_id': item['id']} for item in results]

def get_pr(data_id_lst, cursor):
    results_data_lst = []
    sql = "SELECT * FROM requirement_schedule_table where id=%s"
    for each_id in data_id_lst:
        id = each_id.get("pr_id")
        cursor.execute(sql, id)
        results_data_lst += cursor.fetchall()
    return results_data_lst

def update_RDC(rdc_params_list,  employ_no, encrypted_password, cursor):
    for rdc_params in rdc_params_list:
        workItems = rdc_params.get("identifier", "")
        System_WorkItemType = rdc_params.get("work_item_type", "") # 工作项类型
        System_Id = rdc_params.get("identifier", "") # 标识
        System_Title = rdc_params.get("title", "") # 标题
        ReuseDegree = rdc_params.get("reuse_degree", "") # 复用程度
        FeatureId = rdc_params.get("feature_identifier", "") # 特性标识
        FeatureAttribute = rdc_params.get("feature_attribute", "") # 特性属性
        VerificationMode = rdc_params.get("verification_mode", "") # 验证方式
        VerificationTeam = rdc_params.get("verification_team", "") # 验证团队
        RequirementSortOrder = rdc_params.get("requirement_sort", "") # 需求排序
        Priority = rdc_params.get("priority", "") # 优先级
        System_AreaPath_name = rdc_params.get("domain", "") # 领域
        Team_name = rdc_params.get("team", "") # 团队
        AssessResult_First = rdc_params.get("first_evaluation_conclusion", "") # 评估结论（第一次）
        EstimatedEffort = rdc_params.get("estimated_workload", "") # 预计工作量
        EstimatedEffortOfDevelopment = rdc_params.get("estimated_dev_workload", "") # 预计开发工作量
        EstimatedEffortOfVerification = rdc_params.get("estimated_verification_workload", "") # 预计验证工作量
        EstimatedEffortOfSystemTest = rdc_params.get("estimated_system_test_workload", "") # 预计系统测试工作量
        PlanStartDateOfDevelopment = rdc_params.get("plan_start_dev_date", "") # 计划开始开发日期
        PlanFinishDateOfDevelopment = rdc_params.get("plan_finish_dev_date", "") # 计划完成开发日期
        PlanStartDateOfIntegrationTest = rdc_params.get("plan_start_integration_test_date", "") # 计划开始集成测试日期
        PlanFinishDateOfIntegrationTest = rdc_params.get("plan_finish_integration_test_date", "") # 计划完成集成测试日期
        PlanStartDateOfSystemTest = rdc_params.get("plan_start_system_test_date", "") # 计划开始系统测试日期
        PlanFinishDateOfSystemTest = rdc_params.get("plan_finish_system_test_date", "") # 计划完成系统测试日期
        BelongProduct_name = rdc_params.get("belong_product", "") # 所属产品
        ProductRoadmap = rdc_params.get("product_roadmap", "") # 产品路标
        RequirementPrePlanning = rdc_params.get("requirement_preplanning", "") # 需求预规划
        effective_flag = rdc_params.get("effective_flag", "") # 有效标志
        if effective_flag == "1":
            System_AdminState = "effectived"
        else:
            System_AdminState = "ineffectived"
        BelongFeatureCatalog = rdc_params.get("belong_feature_catalog", "") # 所属特性分类
        DevelopmentOwner_name = rdc_params.get("development_lead", "") # 开发负责人
        # DevelopmentOwner = backfill_manager(DevelopmentOwner_name)
        SkillType = rdc_params.get("skill_type", "")  # 技能类型

        url = f"https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/update/{workItems}"
        x_auth = get_x_auth_val(user=employ_no, encrypted_pwd=encrypted_password)
        headers = {"X-Tenant-Id":"ZTE",
                  "X-Emp-No": employ_no,
                  "X-Auth-Value": x_auth,
                  "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
                  "X-Lang-Id":"zh_CN",
                  "Content-Type":"application/json"
                  }
        body = {
          "fields": [
              {
                  "key": "Priority",
                  "type": "string",
                  "value": str(int(float(Priority)))
              },
              {
                  "key": "AssessResult_First",
                  "type": "string",
                  "value": AssessResult_First
              },
              {
                  "key": "EstimatedEffortOfDevelopment",
                  "type": "double",
                  "value": EstimatedEffortOfDevelopment
              },
              {
                  "key": "PlanStartDateOfDevelopment",
                   "type": "date",
                  "value": PlanStartDateOfDevelopment
              },
              {
                  "key": "PlanFinishDateOfDevelopment",
                  "type": "date",
                  "value": PlanFinishDateOfDevelopment
              },
              {
                  "key": "SkilDevelopmentOwnerlType",
                  "type": "user",
                  "value": DevelopmentOwner_name
              },
          ]
        }
        body = {k: v if v is not None else "" for k, v in body.items()}
        body = clean_none(body)
        response = requests.put(url, json=body, headers=headers)  # 发起POST请求
        print(f"请求URL: {url}, 响应状态码: {response.status_code}")
        # 状态码非200时，加入错误列表
        if response.status_code != 200:
            print(f"错误工作项：{workItems}")
            print(f"响应内容：{response.text}")
        else:
            # 安全解析JSON（避免解析失败报错）
            try:
                response_json = response.json()
                print(f"接口返回：{response_json}")
                # 安全获取code.code（避免KeyError）
                code_value = response_json.get("code", "")
                if code_value.get("code") != "0000":
                    print(f"业务错误，工作项：{workItems}")
                    print(f"错误信息：{response_json.get('msg')}")
                else:
                    print(f"更新数据成功{workItems}")
                    cursor.execute("DELETE FROM requirement_schedule_table")
            except ValueError:
                # JSON解析失败（响应不是合法JSON)
                print(f"响应不是合法JSON,错误工作项列表：{workItems}")
                print(f"原始响应：{response.text}")

def clean_none(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if v is None:
                new_dict[k] = ""  # 关键：None 改成 ""，不删除字段
            else:
                new_dict[k] = clean_none(v)
        return new_dict
    elif isinstance(obj, list):
        return [clean_none(item) for item in obj]
    else:
        return obj

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
    # 回填
    backfill_RDC_data()