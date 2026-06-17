
import pymysql
import base64
import requests
import json
import hashlib
import logging
from socket import socket, AF_INET, SOCK_DGRAM
from pymysql.err import OperationalError, ProgrammingError, DataError

try:
    from requirement_schedule import db_mapping_config
except ImportError:
    import db_mapping_config

logger = logging.getLogger("Logger")

# 需要从嵌套字典中取 'name' 字段的键名列表
data_multidict_lst = ['BelongProduct', 'System_AreaPath', 'Team', 'System_WorkItemType']

# HTTP 请求超时时间（秒）
REQUEST_TIMEOUT = 30


# ===================== 辅助函数：获取本机IP =====================
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


# ===================== 密码解码函数 =====================
def decode_password(encoded_str: str) -> str:
    """
    简易密码解码函数（Base64解码）
    :param encoded_str: 编码后的密码字符串
    :return: 解码后的明文密码
    :raises ValueError: 解码失败时抛出
    """
    try:
        decoded_bytes = base64.b64decode(encoded_str)
        plain_text = decoded_bytes.decode("utf-8")
        return plain_text
    except Exception as e:
        raise ValueError(f"密码 Base64 解码失败: {str(e)}") from e


# ===================== 整合后的认证函数 =====================
def get_x_auth_val(user: str, encrypted_pwd: str, req_ip: str = None, decode_pwd: bool = True) -> str:
    """
    从网站获取验证识别码(x_auth_val)，支持加密密码自动解码。
    :param user: 用户名（明文）
    :param encrypted_pwd: 加密后的密码字符串（若 decode_pwd=False 则为明文密码）
    :param req_ip: 请求的 IP 地址，None 时自动获取本机 IP
    :param decode_pwd: True 表示对 encrypted_pwd 做 Base64 解码；False 表示直接使用明文
    :return: x_auth_val token 字符串
    :raises RuntimeError: 认证失败时抛出，携带具体原因
    """
    # 1. 密码解码（如果需要）
    if decode_pwd:
        pwd = decode_password(encrypted_pwd)  # 失败时抛出 ValueError
    else:
        pwd = encrypted_pwd

    # 2. 获取请求 IP
    if req_ip is None:
        req_ip = get_local_ip()
        if req_ip is None:
            raise RuntimeError("无法获取本机 IP 地址，认证终止")

    # 3. 构造验证码并发送认证请求
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
            headers={'Content-type': 'application/json'},
            timeout=REQUEST_TIMEOUT  # 修复：防止无限挂起
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"认证请求超时（{REQUEST_TIMEOUT}s）")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"认证网络请求异常: {e}") from e
    except Exception as e:
        raise RuntimeError(f"解析认证响应异常: {e}") from e

    # 检查认证结果
    # 安全获取嵌套的 code 值
    auth_code_dict = result.get("code")
    auth_bo_dict = result.get("bo")
    auth_code = auth_code_dict.get("code") if isinstance(auth_code_dict, dict) else None
    bo_code = auth_bo_dict.get("code") if isinstance(auth_bo_dict, dict) else None
    
    if auth_code == "0000" and bo_code == "0000":
        token = result.get('other', {}).get('token')
        if not token:
            raise RuntimeError("认证成功但 token 为空")
        return token
    else:
        error_msg = result.get('message', '未知错误')
        if not error_msg and isinstance(auth_bo_dict, dict):
            error_msg = auth_bo_dict.get('message', error_msg)
        raise RuntimeError(f"UAC 认证失败：{error_msg} (code={auth_code}, bo.code={bo_code})")


def date_split(data):
    """将 ISO 日期时间字符串截取为 YYYY-MM-DD，None 则原样返回"""
    if data:
        return data.split('T')[0]
    return data


def get_pr_name(pr_owner):
    """从开发负责人列表中提取 nameDisplayLong"""
    user_id_lst = []
    for each_dict in pr_owner:
        each_id = each_dict.get("nameDisplayLong")
        if each_id:
            user_id_lst.append(each_id)
    return user_id_lst


def format_effective(effective_flag):
    """将 'effectived' 转为 '1'，其他非空值转为 '0'，None 保持 None"""
    if effective_flag:
        return '1' if effective_flag == 'effectived' else '0'
    return effective_flag


def get_data(id_num, temporary_dict):
    """
    将单行工作项数据映射为数据库插入元组（31 列）。
    :param id_num: 数据库自增 ID
    :param temporary_dict: 经过字段预处理的单行数据字典
    :return: 31 元素元组
    """
    work_item_type = temporary_dict.get("System_WorkItemType")        # 工作项类型
    identifier = temporary_dict.get("System_Id")                      # 标识
    title = temporary_dict.get("System_Title")                        # 标题
    reuse_degree = temporary_dict.get("ReuseDegree")                  # 复用程度
    feature_identifier = temporary_dict.get("FeatureId")             # 特性标识
    feature_attribute = temporary_dict.get("FeatureAttribute")       # 特性属性
    verification_mode = temporary_dict.get("VerificationMode")       # 验证方式
    verification_team = temporary_dict.get("VerificationTeam")       # 验证团队
    requirement_sort = temporary_dict.get("RequirementSortOrder")    # 需求排序
    priority = temporary_dict.get("Priority")                        # 优先级
    domain = temporary_dict.get("System_AreaPath")                   # 领域
    team = temporary_dict.get("Team")                                # 团队
    first_evaluation_conclusion = temporary_dict.get("AssessResult_First")   # 评估结论（第一次）
    estimated_workload = temporary_dict.get("EstimatedEffort")               # 预计工作量
    estimated_dev_workload = temporary_dict.get("EstimatedEffortOfDevelopment")       # 预计开发工作量
    estimated_verification_workload = temporary_dict.get("EstimatedEffortOfVerification")  # 预计验证工作量
    estimated_system_test_workload = temporary_dict.get("EstimatedEffortOfSystemTest")     # 预计系统测试工作量

    plan_start_dev_date = date_split(temporary_dict.get("PlanStartDateOfDevelopment"))
    plan_finish_dev_date = date_split(temporary_dict.get("PlanFinishDateOfDevelopment"))
    plan_start_integration_test_date = date_split(temporary_dict.get("PlanStartDateOfIntegrationTest"))
    plan_finish_integration_test_date = date_split(temporary_dict.get("PlanFinishDateOfIntegrationTest"))
    plan_start_system_test_date = date_split(temporary_dict.get("PlanStartDateOfSystemTest"))
    plan_finish_system_test_date = date_split(temporary_dict.get("PlanFinishDateOfSystemTest"))

    belong_product = temporary_dict.get("BelongProduct")             # 所属产品
    product_roadmap = temporary_dict.get("ProductRoadmap")           # 产品路标
    requirement_preplanning = temporary_dict.get("RequirementPrePlanning")  # 需求预规划
    effective_flag = format_effective(temporary_dict.get("System_AdminState"))  # 有效标志
    belong_feature_catalog = temporary_dict.get("BelongFeatureCatalog")        # 所属特性分类
    skill_type = temporary_dict.get("SkillType")                     # 技能类型

    # 修复 Bug1：development_lead 为 None 或空时直接赋 None，不再对其取下标
    development_lead = temporary_dict.get("DevelopmentOwner")
    if development_lead:
        unique_ids = get_pr_name(development_lead)
        pr_owner = ','.join(unique_ids) if unique_ids else None
    else:
        pr_owner = None  # 修复：原代码此处会对 None/[] 取 [0] 导致崩溃

    return (
        id_num, work_item_type, identifier, title, reuse_degree,
        feature_identifier, feature_attribute, verification_mode,
        verification_team, requirement_sort, priority, domain, team,
        first_evaluation_conclusion, estimated_workload,
        estimated_dev_workload, estimated_verification_workload,
        estimated_system_test_workload, plan_start_dev_date,
        plan_finish_dev_date, plan_start_integration_test_date,
        plan_finish_integration_test_date, plan_start_system_test_date,
        plan_finish_system_test_date, belong_product, product_roadmap,
        requirement_preplanning, effective_flag, belong_feature_catalog,
        pr_owner, skill_type,
    )


# 只同步以下5个领域的数据
ALLOWED_DOMAINS = {'01-L0光系统', '02-L1', '03-L2', '05-支撑', '13-智能控制'}


def add_mysql_data(all_data_dict, cursor) -> int:
    """
    将 RDC 返回数据写入 requirement_schedule_table。
    策略：先确认数据可解析，再在事务内 DELETE + 批量 INSERT，最后 commit。
    说明：只写入领域在 ALLOWED_DOMAINS 中的行，其余跳过。
    :param all_data_dict: RDC API 返回的完整响应字典
    :return: 成功写入的行数
    :raises RuntimeError: 数据解析或数据库操作失败时抛出
    """
    # 先安全解析数据，确认有效后再操作数据库
    # 使用安全的方式获取嵌套数据，避免 None.get() 错误
    bo_dict = all_data_dict.get('bo')
    if not isinstance(bo_dict, dict):
        raise RuntimeError(
            f"RDC 响应结构异常，bo 字段不是字典类型。"
            f"响应概要：{str(all_data_dict)[:300]}"
        )
    
    result_dict = bo_dict.get('result')
    if not isinstance(result_dict, dict):
        raise RuntimeError(
            f"RDC 响应结构异常，bo.result 字段不是字典类型。"
            f"响应概要：{str(all_data_dict)[:300]}"
        )
    
    items = result_dict.get('items')
    if items is None:
        raise RuntimeError(
            f"RDC 响应结构异常，缺少 bo.result.items。"
            f"响应概要：{str(all_data_dict)[:300]}"
        )
    # 保护：RDC 返回 0 条时，不覆盖旧数据
    if isinstance(items, list) and len(items) == 0:
        raise RuntimeError("RDC 返回 0 条数据，本次不同步（不覆盖旧数据）")

    # 预处理所有行数据，同时按领域过滤
    rows = []
    skipped_domain_count = 0
    seq = 1  # 写入序号（跳过行不占用序号）
    for each_dict in items:
        # 跳过 None 项（RDC 可能返回 null 项）
        if each_dict is None:
            skipped_domain_count += 1
            continue
        
        temporary_dict = {}
        for key, value in each_dict.items():
            if key in data_multidict_lst:
                # value 可能为 None 或非 dict，安全取值
                if isinstance(value, dict):
                    value = value.get('name')
                else:
                    value = None
            elif key == 'VerificationTeam':
                if isinstance(value, list):
                    value = ','.join(
                        [item.replace('[', '').replace(']', '') for item in value]
                    )
                elif isinstance(value, str):
                    value = value.replace('[', '').replace(']', '')
                else:
                    value = None
            temporary_dict[key] = value

        # 领域过滤：System_AreaPath 已被提取为 name 字符串
        domain_val = temporary_dict.get("System_AreaPath") or ''
        # 取领域前缀匹配（RDC 返回值可能带完整路径，如 "02-L1/xxx"，取第一段）
        domain_prefix = domain_val.split('/')[0].strip()
        if domain_prefix not in ALLOWED_DOMAINS:
            skipped_domain_count += 1
            continue

        rows.append((seq, temporary_dict))
        seq += 1

    print(f"add_mysql_data: RDC 共 {len(items)} 条，领域过滤后保留 {len(rows)} 条，跳过 {skipped_domain_count} 条")

    if len(rows) == 0:
        raise RuntimeError(
            f"领域过滤后无有效数据（允许领域：{ALLOWED_DOMAINS}），本次不同步"
        )

    # 数据预处理完毕，开始数据库操作：先删旧数据再批量插入（在同一事务内，失败可回滚）
    cursor.execute("DELETE FROM requirement_schedule_table")

    insert_sql = (
        "INSERT INTO requirement_schedule_table ("
        "id, work_item_type, identifier, title, reuse_degree, "
        "feature_identifier, feature_attribute, verification_mode, "
        "verification_team, requirement_sort, priority, domain, team, "
        "first_evaluation_conclusion, estimated_workload, "
        "estimated_dev_workload, estimated_verification_workload, "
        "estimated_system_test_workload, plan_start_dev_date, "
        "plan_finish_dev_date, plan_start_integration_test_date, "
        "plan_finish_integration_test_date, plan_start_system_test_date, "
        "plan_finish_system_test_date, belong_product, product_roadmap, "
        "requirement_preplanning, effective_flag, belong_feature_catalog, "
        "development_lead, skill_type"
        ") VALUES ("
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        ")"
    )
    insert_values = []
    for id_num, temporary_dict in rows:
        insert_values.append(get_data(id_num, temporary_dict))

    # 批量插入，提高性能并降低超时/失败概率
    cursor.executemany(insert_sql, insert_values)
    return len(rows)


def extract_data(work_type="产品需求", username="10326873", encrypted_password="YnV6YWlodTE5OTcu"):
    """
    从 RDC 平台拉取工作项数据并写入数据库。
    :param work_type: 工作项类型，必须是 work_type_dict 中的键
    :param username: 工号
    :param encrypted_password: Base64 编码的密码
    :raises ValueError: 参数不合法时抛出
    :raises RuntimeError: 认证或数据拉取失败时抛出
    """
    db = None
    cursor = None
    try:
        import pymysql.cursors as pymysql_cursors
        db = pymysql.connect(**db_mapping_config.db_config, cursorclass=pymysql_cursors.DictCursor)
        cursor = db.cursor()
        version = get_version_requirement_perplanning(cursor)
        # 获取版本视图中所有版本做属于操作
        all_data_dict = get_rdc_data(version, encrypted_password, username, work_type)
        
        # 保护：如果 RDC 返回 None 或空字典，直接报错
        if not all_data_dict:
            logger.error("RDC 返回空数据")
            raise RuntimeError("RDC 返回空数据")
        
        # 保护：如果 RDC 返回失败码，直接报错，不继续写库
        # 安全获取嵌套的 code 值，避免 None.get() 错误
        code_dict = all_data_dict.get("code")
        bo_dict = all_data_dict.get("bo")
        code_code = code_dict.get("code") if isinstance(code_dict, dict) else None
        bo_code = bo_dict.get("code") if isinstance(bo_dict, dict) else None
        
        # 获取错误消息（如果有）
        error_message = all_data_dict.get("message", "")
        if not error_message and isinstance(bo_dict, dict):
            error_message = bo_dict.get("message", error_message)
        
        if code_code and code_code != "0000":
            # 记录完整的响应以便调试
            logger.error(f"RDC 返回失败 - code.code: {code_code}, message: {error_message}, 完整响应：{json.dumps(all_data_dict, ensure_ascii=False)[:500]}")
            raise RuntimeError(f"RDC 返回失败 (code.code={code_code}): {error_message}")
        if bo_code and bo_code != "0000":
            # 记录完整的响应以便调试
            logger.error(f"RDC 返回失败 - bo.code: {bo_code}, message: {error_message}, 完整响应：{json.dumps(all_data_dict, ensure_ascii=False)[:500]}")
            raise RuntimeError(f"RDC 返回失败 (bo.code={bo_code}): {error_message}")

        # add_mysql_data 失败时会抛出 RuntimeError，调用方可感知
        count = add_mysql_data(all_data_dict, cursor)

        db.commit()
        print(f"extract_data 完成，共写入 {count} 条数据")
        return count
    except (OperationalError, ProgrammingError, DataError) as e:
        if db:
            db.rollback()
        # 修复 Bug4：重新抛出异常，让调用方感知失败
        raise RuntimeError(f"数据库操作异常（已回滚）: {str(e)}") from e
    except Exception as e:
        if db:
            db.rollback()
        raise RuntimeError(f"写入数据异常（已回滚）: {str(e)}") from e
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def get_version_requirement_perplanning(cursor):
    version_sql = "SELECT requirement_preplanning FROM version_table WHERE requirement_preplanning IS NOT NULL AND requirement_preplanning != ''"
    cursor.execute(version_sql)
    results_data_lst = cursor.fetchall()
    requirement_preplanning_lst = []
    for each_data in results_data_lst:
        val = each_data.get("requirement_preplanning")
        if val:
            requirement_preplanning_lst.append(val)
    version = ','.join(requirement_preplanning_lst)
    return version

def get_rdc_data(version, encrypted_password, username, work_type):
    # 校验 work_type 合法性
    resolved_work_type = db_mapping_config.work_type_dict.get(work_type)
    if resolved_work_type is None:
        valid = list(db_mapping_config.work_type_dict.keys())
        raise ValueError(f"无效的 work_type='{work_type}'，合法值: {valid}")
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/WIC/rest/workspaces/OTNSW/queries/query_work_items"
    body = {
        "queryCondition": {
            "depth": 6,
            "relatedType": ["linkRelatedType_3"],
            "removeTop": True,
            "sourceClauses": [
                {
                    "field": "System_WorkItemType",
                    "leftGroup": 0,
                    "logicalOperator": "",
                    "operator": "=",
                    "rightGroup": 0,
                    "value": resolved_work_type
                },
                {
                    "field": "RequirementPrePlanning",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "in",
                    "rightGroup": 0,
                    "value": version
                },
                {
                    "field": "System_State",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": "not in",
                    "rightGroup": 0,
                    "value": ["已废弃", "已拒绝", "已支持"]
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
                    "field": "System_CreatedDate",
                    "leftGroup": 0,
                    "logicalOperator": "AND",
                    "operator": ">=",
                    "rightGroup": 0,
                    "value": "2025-01-01"
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
            {"key": "System_WorkspaceKey", "name": "工作区Id", "type": "string", "width": "82.19998168945312"},
            {"key": "System_WorkItemType", "name": "工作项类型", "type": "workItemType", "width": "105"},
            {"key": "System_Id", "name": "标识", "type": "workItemNo", "width": ""},
            {"key": "System_Title", "name": "标题", "type": "string", "width": "137.79998779296875"},
            {"key": "BelongFeatureCatalog", "name": "所属特性分类", "type": "string", "width": "113.79998779296875"},
            {"key": "System_AreaPath", "name": "领域", "type": "advancedData", "width": "84"},
            {"key": "Team", "name": "团队", "type": "advancedData", "width": "114.20001220703125"},
            {"key": "FeatureId", "name": "特性标识", "type": "string", "width": "119.01251220703125"},
            {"key": "ReuseDegree", "name": "复用程度", "type": "string", "width": "81.79998779296875"},
            {"key": "FeatureAttribute", "name": "特性属性", "type": "string", "width": "54.7999267578125"},
            {"key": "RequirementSortOrder", "name": "需求排序", "type": "double", "width": "81.012451171875"},
            {"key": "Priority", "name": "优先级", "type": "string", "width": "68.4375"},
            {"key": "AssessResult_First", "name": "评估结论（第一次）", "type": "string", "width": ""},
            {"key": "EstimatedEffort", "name": "预计工作量", "type": "double", "width": ""},
            {"key": "EstimatedEffortOfDevelopment", "name": "预计开发工作量", "type": "double",
             "width": "56.7999267578125"},
            {"key": "EstimatedEffortOfVerification", "name": "预计验证工作量", "type": "double", "width": ""},
            {"key": "EstimatedEffortOfSystemTest", "name": "预计系统测试工作量", "type": "double", "width": ""},
            {"key": "PlanStartDateOfDevelopment", "name": "计划开始开发日期", "type": "date",
             "width": "106.5999755859375"},
            {"key": "PlanFinishDateOfDevelopment", "name": "计划完成开发日期", "type": "date",
             "width": "74.449951171875"},
            {"key": "PlanStartDateOfIntegrationTest", "name": "计划开始集成测试日期", "type": "date", "width": ""},
            {"key": "PlanFinishDateOfIntegrationTest", "name": "计划完成集成测试日期", "type": "date", "width": ""},
            {"key": "PlanStartDateOfSystemTest", "name": "计划开始系统测试日期", "type": "date", "width": ""},
            {"key": "PlanFinishDateOfSystemTest", "name": "计划完成系统测试日期", "type": "date", "width": ""},
            {"key": "ProductRoadmap", "name": "产品路标", "type": "string", "width": ""},
            {"key": "RequirementPrePlanning", "name": "需求预规划", "type": "string", "width": ""},
            {"key": "BelongProduct", "name": "所属产品", "type": "advancedData", "width": ""},
            {"key": "VerificationMode", "name": "验证方式", "type": "string", "width": ""},
            {"key": "VerificationTeam", "name": "验证团队", "type": "string", "width": ""},
            {"key": "DevelopmentOwner", "name": "开发负责人", "type": "user", "width": ""},
            {"key": "SkillType", "name": "技能类型", "type": "user", "width": ""},
        ],
        "pageSize": 8000
    }
    # 修复 Bug2：获取 token，失败时直接抛出异常，不再带 None token 发请求
    x_auth = get_x_auth_val(user=username, encrypted_pwd=encrypted_password)
    header = {
        "X-Tenant-Id": "ZTE",
        "X-Lang-Id": "zh_CN",
        "X-Emp-No": username,
        "X-Auth-Value": x_auth,
        "appcode": "4811ee4055a74cb4b52e7295e1d1858d",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=body, headers=header, timeout=REQUEST_TIMEOUT)  # 修复：加超时
        response.raise_for_status()
        all_data_dict = response.json()  # 修复：去掉多余的 dict() 包装
    except requests.exceptions.Timeout:
        raise RuntimeError(f"RDC 数据请求超时（{REQUEST_TIMEOUT}s）")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"RDC 数据请求网络异常: {e}") from e
    except Exception as e:
        raise RuntimeError(f"解析 RDC 响应异常: {e}") from e
    return all_data_dict


# 保留旧函数名作为别名，避免其他地方调用报错
extrac_data = extract_data


if __name__ == '__main__':

    extract_data()
