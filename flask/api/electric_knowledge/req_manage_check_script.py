import re
import os
import json
import jieba
import logging
import requests

from collections import defaultdict
from datetime import datetime, timedelta


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
LINGHANG_BASE_URL = "http://10.239.69.183:3001"
SCRIPT_UPDATE_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")
BJ_OFFSET = timedelta(hours=8)
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "2026-01-01"
USER_NUM = '10305454'
USER_TOKEN = '8edb980981dd9d737db9eea61a0f8ed3'
PR_FIELD_LIST = ["System_Id", "System_State", "System_CreatedDate", "System_CreatedBy", "System_ChangedDate", "System_ChangedBy",\
                 "System_AppointedTo", "System_AreaPath", "Team", "System_Title", "BelongProduct", "RequirementPrePlanning", "System_Description_html",\
                 "AcceptanceCriteria_html", "RequirementAnalysisOwner", "SpecificationByExampleUrl", "SpecificationByExampleState", "DesignSpecificationUrl",\
                 "DesignState", "FeatureUrl", "BelongFeatureCatalog", "FeatureId", "FeatureName_Cn", "CheckResultOfChipScheme", "IsAutoCreated",\
                 "AssessResult_First", "ReuseDegree", "PlanStartDateOfDevelopment", "PlanFinishDateOfDevelopment", "AccessCheck", "BelongReleaseVersion",\
                 "IsMasterDeliveryArea"]

# 全局变量：用于Impact分析结果共享
SIMPLE_MR_PR_DICT = {}
SIMPLE_MR_PR_DICT_WITH_IMPACT = {}


def segment_title(title):
    """切分需求标题并过滤无用词"""
    if not title:
        return set()
    stop_words = {'的', '了', '在', '是', '和', '与', '及', '等', '或', '一个', '一种', '基于', '用于', '一种', '方法', '系统', '装置', '设备', '模块', '功能', '实现', '提供', '支持', '完成', '进行', '处理', '分析', '设计', '开发', '测试', '验证', '优化', '改进', '新增', '修改', '删除', '更新', '维护', '管理', '配置', '设置', '调整', '升级', '迁移', '集成', '对接', '适配', '兼容', '扩展', '增强', '完善', '修复', '解决', '避免', '防止', '减少', '降低', '提高', '提升', '改善', '加强', '确保', '保证', '满足', '符合', '遵循', '按照', '根据', '参考', '借鉴', '吸收', '采纳', '接受', '拒绝', '废弃', '暂停', '挂起', '阻塞', '依赖', '关联', '相关', '对应', '映射', '转换', '翻译', '解释', '说明', '描述', '定义', '声明', '实现', '调用', '访问', '操作', '执行', '运行', '启动', '停止', '重启', '初始化', '销毁', '创建', '删除', '添加', '修改', '查询', '检索', '过滤', '排序', '分组', '聚合', '统计', '计算', '评估', '评价', '判断', '决策', '推荐', '预测', '预警', '监控', '告警', '日志', '审计', '跟踪', '追溯', '记录', '存储', '缓存', '备份', '恢复', '同步', '异步', '并行', '串行', '批量', '单次', '定时', '周期', '实时', '延迟', '即时', '自动', '手动', '智能', '人工', '在线', '离线', '本地', '远程', '云端', '边缘', '分布式', '集中式', '微服务', '单体', '架构', '框架', '平台', '引擎', '内核', '接口', '协议', '标准', '规范', '流程', '规则', '策略', '算法', '模型', '数据', '信息', '内容', '文本', '字符', '字符串', '数字', '数值', '布尔', '日期', '时间', '状态', '类型', '格式', '编码', '解码', '加密', '解密', '压缩', '解压', '打包', '解包', '解析', '生成', '构建', '编译', '解释', '执行', '部署', '发布', '上线', '下线', '回滚', '灰度', '金丝雀', '蓝绿', 'A/B', '测试', '实验', '对比', '分析', '挖掘', '学习', '训练', '推理', '预测', '分类', '聚类', '回归', '降维', '特征', '标签', '权重', '参数', '超参数', '损失', '梯度', '反向', '传播', '正向', '计算', '图', '网络', '节点', '边', '路径', '距离', '相似度', '匹配', '搜索', '索引', '倒排', '正向', '词典', '词库', '词表', '词性', '标注', '识别', '抽取', '提取', '融合', '对齐', '映射', '转换', '变换', '变形', '归一化', '标准化', '正则化', '规范化', '离散化', '连续化', '二值化', '多值化', '独热', '嵌入', '向量', '矩阵', '张量', '标量', '数组', '列表', '集合', '字典', '树', '图', '表', '数据库', '表', '字段', '记录', '行', '列', '键', '值', '主键', '外键', '索引', '约束', '触发器', '存储过程', '函数', '视图', '游标', '事务', '锁', '并发', '隔离', '级别', '一致性', '持久性', '原子性', '可用性', '分区', '容错', '冗余', '复制', '分片', '分区', '负载均衡', '故障', '转移', '恢复', '备份', '快照', '镜像', '模板', '实例', '容器', '虚拟机', '物理机', '服务器', '客户端', '浏览器', '移动端', '桌面端', 'Web 端', '小程序', '公众号', 'APP', 'H5', 'PC', '移动', '无线', '有线', '网络', '通信', '传输', '接收', '发送', '上传', '下载', '推送', '拉取', '订阅', '发布', '消息', '通知', '提醒', '提示', '警告', '错误', '异常', '日志', '埋点', '统计', '分析', '报表', '图表', '可视化', '大屏', '看板', '仪表盘', '监控', '告警', '巡检', '健康', '检查', '诊断', '优化', '调优', '性能', '效率', '质量', '安全', '稳定', '可靠', '可用', '可扩展', '可维护', '可测试', '可观测', '可追溯', '可审计', '可配置', '可定制', '可插拔', '可扩展', '可复用', '可移植', '可部署', '可运维', '可监控', '可管理', '可控制', '可调节', '可切换', '可降级', '可熔断', '可限流', '可缓存', '可预加载', '可懒加载', '可异步', '可同步', '可并行', '可串行', '可批量', '可单次', '可定时', '可周期', '可实时', '可延迟', '可即时', '可自动', '可手动', '可智能', '可人工', '可在线', '可离线', '可本地', '可远程', '可云端', '可边缘', '可分布式', '可集中式', '可微服务', '可单体'}
    stop_words.update({"单板", "特性"})
    words = jieba.lcut(title)
    return set(
        w for w in words 
        if w not in stop_words 
        and len(w) > 2  # 去掉长度<=2的词
        and re.search(r'[\u4e00-\u9fa5]', w)  # 必须包含中文字符
    )


def extract_fs_code(title):
    """提取标题中的 FS/F + 6位数字 编码（如 FS030301、F030301）"""
    if not title:
        return set()
    return set(re.findall(r'(?:FS|F)(\d{6})(?!\d)', title.upper()))


def extract_f3_code(title):
    """提取标题中的 F + 3位数字 编码（如 F123，后面不能紧跟数字）"""
    if not title:
        return set()
    return set(re.findall(r'F(\d{3})(?!\d)', title.upper()))


def extract_board_name(title):
    """提取标题中的单板名称：M + 单数字 + 字母/数字串（数字不连续），自动过滤末尾数量后缀如x32"""
    if not title:
        return set()
    # 先匹配 M+数字+字母数字组合
    candidates = re.findall(r'M\d[A-Za-z0-9]+', title.upper())
    valid_boards = set()
    for cand in candidates:
        # 剥离末尾常见的数量后缀（如 x32, X8, 或纯数字量）
        cand_clean = re.sub(r'[xX]\d+$', '', cand)
        cand_clean = re.sub(r'\d+$', '', cand_clean)
        if len(cand_clean) <= 2:
            continue
        # 验证：从第3个字符开始，不能有连续数字
        if not re.search(r'\d{2}', cand_clean[2:]):
            valid_boards.add(cand_clean)
    return valid_boards


def calculate_impact(other_title, master_title):
    """
    判断两个需求标题是否存在影响关系（严格按4条新规则实现）
    重合的单板名称会自动加入返回的匹配词集合中
    """
    other_words = segment_title(other_title)
    master_words = segment_title(master_title)
    common_words = other_words & master_words
    word_count = len(common_words)

    other_fs = extract_fs_code(other_title)
    master_fs = extract_fs_code(master_title)
    other_f3 = extract_f3_code(other_title)
    master_f3 = extract_f3_code(master_title)
    other_boards = extract_board_name(other_title)
    master_boards = extract_board_name(master_title)

    has_fs_both = bool(other_fs) and bool(master_fs)
    has_f3_both = bool(other_f3) and bool(master_f3)
    has_board_both = bool(other_boards) and bool(master_boards)
    has_board_only_one = bool(other_boards) ^ bool(master_boards)

    fs_match = other_fs & master_fs
    f3_match = other_f3 & master_f3
    board_match = other_boards & master_boards  # 重合的单板集合

    # 🟢 规则（1）：双方都有 FS/F+6位数字
    if has_fs_both:
        if fs_match:
            res_words = common_words | fs_match
            if has_board_both:
                if board_match:
                    return True, res_words | board_match  # 注入重合单板
                return False, set()  # 都有单板但不重合 -> 无关系
            return True, res_words
        return False, set()  # 编码不同，直接无关系

    # 🟢 规则（2）：双方都有 F+3位数字
    if has_f3_both:
        if f3_match:
            res_words = common_words | f3_match
            if has_board_both:
                if board_match:
                    return True, res_words | board_match  # 注入重合单板
                return False, set()
            return True, res_words
        return False, set()

    # 🟢 规则（3）：双方都有单板名称（且未触发规则1/2）
    if has_board_both:
        if board_match and word_count >= 3:
            return True, common_words | board_match  # 注入重合单板
        return False, set()

    # 🟢 规则（4）：仅一方有单板名称
    if has_board_only_one:
        if word_count >= 3:
            return True, common_words
        return False, set()

    # 🟢 兜底逻辑：无特殊标识，关键词≥2
    if word_count >= 2:
        return True, common_words

    return False, set()


def analyze_mr_pr_impact(simple_mr_pr_dict):
    """分析MR下PR之间的Impact影响关系"""
    result_dict = {}
    for mr_id, categories in simple_mr_pr_dict.items():
        master_dict = categories.get("master", {})
        other_dict = categories.get("other", {})
        result_dict[mr_id] = {
            "other": {},
            "impact_summary": {}
        }
        for other_pr_id, other_info in other_dict.items():
            other_title = other_info.get("system_title", "")
            impacted_masters = []
            common_words_list = []
            for master_pr_id, master_info in master_dict.items():
                master_title = master_info.get("system_title", "")
                has_impact, common_words = calculate_impact(other_title, master_title)
                if has_impact:
                    impacted_masters.append({
                        "pr_id": master_pr_id,
                        "system_title": master_title
                    })
                    common_words_list.append({
                        "master_pr_id": master_pr_id,
                        "common_words": list(common_words)
                    })
            result_dict[mr_id]["other"][other_pr_id] = {
                "system_title": other_title,
                "impacted_masters": impacted_masters,
                "impact_details": common_words_list
            }
        result_dict[mr_id]["impact_summary"] = {
            "total_other_prs": len(other_dict),
            "total_impacted_other_prs": sum(1 for v in result_dict[mr_id]["other"].values() if v["impacted_masters"]),
            "total_master_prs": len(master_dict),
            "total_impacted_master_prs": len(set(
                item.get("pr_id") if isinstance(item, dict) else item
                for v in result_dict[mr_id]["other"].values()
                for item in v["impacted_masters"]
            ))
        }
    return result_dict


def get_current_date():
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


def utc_to_beijing_str(utc_str: str) -> str:
    if not utc_str:
        return ""
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    return (dt + BJ_OFFSET).strftime(TIME_FORMAT)


def get_pr_info_list(USER_NUM, USER_TOKEN):
    url = "https://icosg.dt.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/OTNSW/queries/after_work_items"
    base_body = {
        "queryCondition": {
            "depth": 0, "relatedOptions": "linksOneHopMustContain", "relatedType": [],
            "removeTop": False,
            "sourceClauses": [
                {"field": "System_WorkItemType", "leftGroup": 0, "logicalOperator": "", "operator": "=", "rightGroup": 0, "value": "PR"},
                {"field": "System_AreaPath", "leftGroup": 0, "logicalOperator": "AND", "operator": "=", "rightGroup": 0, "value": "bdv_105454"},
                {"leftGroup": 0, "rightGroup": 0, "logicalOperator": "AND", "field": "System_CreatedDate", "operator": ">=", "value": "2022-01-01"}
            ],
            "targetClauses": [], "treeOptions": "top", "type": "flat"
        },
        "selectItems": [{"key": item} for item in PR_FIELD_LIST],
        "sortItems": [{"isAscending": "false", "key": "System_CreatedDate"}],
        "sortValue": True, "pageNo": 1, "pageSize": 10000
    }
    headers = {
        "X-Tenant-Id": "ZTE", "X-Emp-No": USER_NUM, "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id": "zh_CN", "Content-Type": "application/json", "X-Auth-Value": USER_TOKEN
    }
    pr_info_list = []
    current_search_after = None
    while True:
        body = base_body.copy()
        if current_search_after is not None:
            body["searchAfter"] = current_search_after
        response = requests.post(url, json=body, headers=headers)
        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
        data = response.json()
        items = data.get("bo", {}).get("result", {}).get("items", [])
        for item in items:
            pr_info_list.append({
                "system_id": item.get("System_Id"), "system_state": item.get("System_State", {}).get("name", ""),
                "system_createddate": utc_to_beijing_str(item.get("System_CreatedDate")),
                "system_createdby": item.get("System_CreatedBy", {}).get("nameDisplayLong", ""),
                "system_changeddate": utc_to_beijing_str(item.get("System_ChangedDate")),
                "system_changedby": item.get("System_ChangedBy", {}).get("nameDisplayLong", ""),
                "system_appointedto": item.get("System_AppointedTo", {}).get("nameDisplayLong", ""),
                "system_areapath": item.get("System_AreaPath", {}).get("label", ""),
                "team": item.get("Team", {}).get("label", ""), "system_title": item.get("System_Title"),
                "belongproduct": item.get("BelongProduct", {}).get("label", ""),
                "requirementpreplanning": item.get("RequirementPrePlanning"),
                "system_description_html": item.get("System_Description_html"),
                "acceptancecriteria_html": item.get("AcceptanceCriteria_html"),
                "requirementanalysisowner": item.get("RequirementAnalysisOwner", {}).get("nameDisplayLong", ""),
                "specificationbyexampleurl": item.get("SpecificationByExampleUrl"),
                "specificationbyexamplestate": item.get("SpecificationByExampleState"),
                "designspecificationurl": item.get("DesignSpecificationUrl"),
                "designstate": item.get("DesignState"), "featureurl": item.get("FeatureUrl"),
                "belongfeaturecatalog": item.get("BelongFeatureCatalog"),
                "featureid": item.get("FeatureId"), "featurename_cn": item.get("FeatureName_Cn"),
                "checkresultofchipscheme": item.get("CheckResultOfChipScheme"),
                "isautocreated": item.get("IsAutoCreated"), "assessresult_first": item.get("AssessResult_First"),
                "reusedegree": item.get("ReuseDegree"),
                "planstartdateofdevelopment": utc_to_beijing_str(item.get("PlanStartDateOfDevelopment")),
                "planfinishdateofdevelopment": utc_to_beijing_str(item.get("PlanFinishDateOfDevelopment")),
                "accesscheck": item.get("AccessCheck"),
                "belongreleaseversion": item.get("BelongReleaseVersion", {}).get("baseDataValue", {}).get("label"),
                "ismasterdeliveryarea": item.get("IsMasterDeliveryArea"),
                "script_update_date": SCRIPT_UPDATE_DATE,
            })
        print("完成1次查询")
        if len(items) == 10000:
            current_search_after = items[-1].get("sortValues")
        else:
            break
    return pr_info_list


def get_pr_check_result_list(all_pr_info_list):
    obj_pr_info_list = [item for item in all_pr_info_list if item.get("system_state") not in ["已拒绝", "已废弃"]]
    reject_pr_ident_list = [item.get("system_id") for item in all_pr_info_list if item.get("system_state") in ["已拒绝", "已废弃"]]
    sum_check_result_list = []
    sum_check_result_list += check_specification_by_example_state(obj_pr_info_list); print(len(sum_check_result_list))
    sum_check_result_list += check_design_state(obj_pr_info_list); print(len(sum_check_result_list))
    sum_check_result_list += check_feature_state(obj_pr_info_list); print(len(sum_check_result_list))
    sum_check_result_list += check_requirement_preplanning(obj_pr_info_list); print(len(sum_check_result_list))
    sum_check_result_list += check_access_check(obj_pr_info_list); print(len(sum_check_result_list))
    sum_check_result_list += check_belong_release_version(obj_pr_info_list); print(len(sum_check_result_list))
    # 🔧 拆分后的两个独立检查函数
    sum_check_result_list += check_assessresult_first_compliance(obj_pr_info_list, reject_pr_ident_list); print(len(sum_check_result_list))
    sum_check_result_list += check_plan_date_impact_conflict(obj_pr_info_list, reject_pr_ident_list); print(len(sum_check_result_list))
    return sum_check_result_list


def check_specification_by_example_state(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "分析中" and p.get("team") and p.get("assessresult_first") == "可纳入" \
        and p.get("planstartdateofdevelopment") and p.get("planfinishdateofdevelopment") and p.get("specificationbyexamplestate") != "02-已完成":
            t = {**p, "problem_type": "需求实例化未完成", "problem_description": '需求实例化状态不是"02-已完成", 无法将需求从"分析中"翻转至"已分析"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


def check_design_state(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "分析中" and p.get("team") and p.get("assessresult_first") == "可纳入" \
        and p.get("planstartdateofdevelopment") and p.get("planfinishdateofdevelopment") and p.get("designstate") != "02-已完成":
            t = {**p, "problem_type": "方案文档未完成", "problem_description": '方案状态不是"02-已完成", 无法将需求从"分析中"翻转至"已分析"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


def check_feature_state(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "分析中" and p.get("team") and p.get("assessresult_first") == "可纳入" \
        and p.get("planstartdateofdevelopment") and p.get("planfinishdateofdevelopment") and p.get("belongfeaturecatalog") == "01-标准" \
        and p.get("checkresultofchipscheme") != "01-正确":
            t = {**p, "problem_type": "特性内容未完成", "problem_description": '特性链接检查结论不是"01-正确", 无法将需求从"分析中"翻转至"已分析"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


def check_requirement_preplanning(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "分析中" and p.get("team") and p.get("assessresult_first") == "可纳入" \
        and p.get("planstartdateofdevelopment") and p.get("planfinishdateofdevelopment") and p.get("requirementpreplanning") == "待规划版本":
            t = {**p, "problem_type": "需求预规划未确定", "problem_description": '需求预规划不能是"待规划版本", 无法将需求从"分析中"翻转至"已分析"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


def check_access_check(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "已分析" and p.get("assessresult_first") == "可纳入" and p.get("planstartdateofdevelopment") \
        and p.get("planfinishdateofdevelopment") and p.get("accesscheck") and p.get("accesscheck") != "通过":
            t = {**p, "problem_type": "AI准入检查不通过", "problem_description": 'AI准入检查不通过, 无法将需求从"已分析"翻转至"开发中"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


def check_belong_release_version(pr_info_list):
    check_result_list = []
    for p in pr_info_list:
        if p.get("system_state") == "开发中" and not p.get("belongreleaseversion"):
            t = {**p, "problem_type": "发布版本未填", "problem_description": '发布版本未填, 无法将需求从"开发中"翻转至"已开发"',
                 "check_date": DATE_FORMAT, "default_problem_flag": "是", "default_handle_person": p.get("requirementanalysisowner"),
                 "default_handle_date": DATE_FORMAT, "default_handle_flag": "否", "actual_handle_date": ""}
            check_result_list.append(t)
    return check_result_list


# ============================================================================
# 🔧 拆分函数1: 检查初评结论合规性（修复版 - 支持影响数量统计 + 避免误报）
# ============================================================================
def check_assessresult_first_compliance(pr_info_list, reject_pr_ident_list):
    """
    检查需求初评结论的合规性（支持detail_list存储到数据库）
    """
    check_result_list = []
    # 【1】初始化基础变量
    all_pr_info_dict = {item.get("system_id"): item for item in pr_info_list}
    master_pr_ident_list = [
        item.get("system_id") 
        for item in pr_info_list 
        if item.get("ismasterdeliveryarea")
    ]
    if not master_pr_ident_list:
        logger.info("未找到主交付领域PR，初评结论检查跳过")
        return check_result_list
    # 【2】获取MR-PR父子关系
    master_mr_pr_dict = get_rdc_relation_id_dict({
        "rdcIdent_list": master_pr_ident_list,
        "linkRelationName": "father",
        "relatedWorkItemTypeKey": "MR",
        "employ_no": USER_NUM
    })
    if not master_mr_pr_dict:
        logger.info("未找到主交付领域PR关联的MR，初评结论检查跳过")
        return check_result_list
    # 【3】初始化分组字典
    obj_mr_pr_dict = {}
    for mr_ident in master_mr_pr_dict.keys():
        obj_mr_pr_dict[mr_ident] = {
            "master": master_mr_pr_dict[mr_ident],
            "other": []
        }
    # 【4】获取每个MR下的所有子级PR
    master_mr_ident_list = list(master_mr_pr_dict.keys())
    all_pr_mr_dict = get_rdc_relation_id_dict({
        "rdcIdent_list": master_mr_ident_list,
        "linkRelationName": "son",
        "relatedWorkItemTypeKey": "PR",
        "employ_no": USER_NUM
    })
    all_mr_pr_dict = reverse_dict_key_value(all_pr_mr_dict)
    # 【5】计算"other"类PR
    all_other_pr_ident_list = []
    for mr_ident in all_mr_pr_dict.keys():
        if mr_ident not in obj_mr_pr_dict:
            continue
        all_pr_of_single_mr_set = set(all_mr_pr_dict.get(mr_ident, []))
        master_pr_of_single_mr_set = set(obj_mr_pr_dict[mr_ident]["master"])
        other_pr_of_single_mr_list = list(all_pr_of_single_mr_set - master_pr_of_single_mr_set)
        all_other_pr_ident_list += other_pr_of_single_mr_list
        for other_pr_item in other_pr_of_single_mr_list:
            if other_pr_item not in reject_pr_ident_list:
                obj_mr_pr_dict[mr_ident]["other"].append(other_pr_item)
    obj_mr_pr_dict = {k: v for k, v in obj_mr_pr_dict.items() if len(v.get("other"))}
    if not obj_mr_pr_dict:
        logger.info("未找到存在依赖关系的MR分组，初评结论检查跳过")
        return check_result_list
    obj_mr_pr_dict = convert_list_to_dict_structure(obj_mr_pr_dict)
    # 【6】批量获取other类PR的详细信息
    all_other_pr_ident_list = list(set(all_other_pr_ident_list))
    all_other_pr_info_dict = {}
    if all_other_pr_ident_list:
        rdc_param_dict = {
            "rdcIdent_list": all_other_pr_ident_list,
            "workItemType_list": ["PR"] * len(all_other_pr_ident_list),
            "employ_no": USER_NUM
        }
        all_other_pr_info_list = get_rdc_info_list(rdc_param_dict)
        all_other_pr_info_dict = {
            item.get("system_id"): item 
            for item in all_other_pr_info_list 
            if item.get("system_state") not in ["已拒绝", "已废弃"]
        }
        logger.info(f"成功获取 {len(all_other_pr_info_dict)}/{len(all_other_pr_ident_list)} 条other类PR详情")
    # 【7】执行初评结论检查（核心逻辑 - 支持detail_list）
    processed_prs = set()
    for mr_id, categories in obj_mr_pr_dict.items():
        master_dict = categories.get("master", {})
        other_dict = categories.get("other", {})
        # 填充 master 的详细信息
        for pr_ident in list(master_dict.keys()):
            if pr_ident in all_pr_info_dict:
                master_dict[pr_ident] = all_pr_info_dict[pr_ident]
        # 填充 other 的详细信息
        for pr_ident in list(other_dict.keys()):
            if pr_ident in all_other_pr_info_dict:
                other_dict[pr_ident] = all_other_pr_info_dict[pr_ident]
        # 收集非"可纳入"的PR ID列表
        master_reject_list = [
            pid for pid, info in master_dict.items() 
            if info and info.get("assessresult_first") != "可纳入"
        ]
        other_reject_list = [
            pid for pid, info in other_dict.items() 
            if info and info.get("assessresult_first") != "可纳入"
        ]
        # ====================================================================
        # 🔹 场景1: master中非"可纳入"的PR，影响本领域/跨领域"可纳入"的PR
        # ====================================================================
        for reject_pr_id in master_reject_list:
            if reject_pr_id in processed_prs:
                continue
            reject_pr_info = master_dict.get(reject_pr_id)
            if not reject_pr_info:
                continue
            # 收集受影响的"可纳入"PR详细信息（构建detail_list）
            affected_detail_list = []
            # master领域内受影响
            for pid, info in master_dict.items():
                if pid != reject_pr_id and (info or {}).get("assessresult_first") == "可纳入":
                    affected_detail_list.append({
                        "pr_id": pid,
                        "system_title": info.get("system_title", ""),
                        "system_state": info.get("system_state", ""),
                        "team": info.get("team", ""),
                        "belongproduct": info.get("belongproduct", ""),
                        "assessresult_first": info.get("assessresult_first", ""),
                        "requirementanalysisowner": info.get("requirementanalysisowner", ""),
                        "planstartdateofdevelopment": info.get("planstartdateofdevelopment", ""),
                        "planfinishdateofdevelopment": info.get("planfinishdateofdevelopment", ""),
                        "impact_type": "同领域"  # 标记影响类型
                    })
            # other领域受影响
            for pid, info in other_dict.items():
                if (info or {}).get("assessresult_first") == "可纳入":
                    affected_detail_list.append({
                        "pr_id": pid,
                        "system_title": info.get("system_title", ""),
                        "system_state": info.get("system_state", ""),
                        "team": info.get("team", ""),
                        "belongproduct": info.get("belongproduct", ""),
                        "assessresult_first": info.get("assessresult_first", ""),
                        "requirementanalysisowner": info.get("requirementanalysisowner", ""),
                        "planstartdateofdevelopment": info.get("planstartdateofdevelopment", ""),
                        "planfinishdateofdevelopment": info.get("planfinishdateofdevelopment", ""),
                        "impact_type": "跨领域"  # 标记影响类型
                    })
            if affected_detail_list:
                affected_count = len(affected_detail_list)
                affected_pr_ids = [d["pr_id"] for d in affected_detail_list]
                # 问题描述预览
                affected_pr_preview = ", ".join(affected_pr_ids[:5])
                affected_pr_suffix = f"...等{affected_count}个" if affected_count > 5 else f"等{affected_count}个"
                check_result_list.append({
                    **reject_pr_info,
                    "problem_type": "非可纳入影响本领域PR翻转",
                    "problem_description": (
                        f'PR的初评结论不是"可纳入", 影响本领域及其它领域共{affected_count}个'
                        f'可纳入状态的PR需求翻转（涉及: {affected_pr_preview}{affected_pr_suffix}）'
                    ),
                    "check_date": DATE_FORMAT,
                    "default_problem_flag": "是",
                    "default_handle_person": reject_pr_info.get("requirementanalysisowner"),
                    "default_handle_date": DATE_FORMAT,
                    "default_handle_flag": "否",
                    "actual_handle_date": "",
                    "impact_check_flag": "MR分组逻辑",
                    # ✅ 保留原有字段（向后兼容）
                    "affected_pr_count": affected_count,
                    "affected_pr_ids": affected_pr_ids,
                    # ✅ 新增detail_list字段（支持数据库存储详细信息）
                    "detail_list": affected_detail_list
                })
                processed_prs.add(reject_pr_id)
        # ====================================================================
        # 🔹 场景2: other中非"可纳入"的PR，影响主交付领域"可纳入"的PR
        # ====================================================================
        for reject_pr_id in other_reject_list:
            if reject_pr_id in processed_prs:
                continue
            reject_pr_info = other_dict.get(reject_pr_id)
            if not reject_pr_info:
                continue
            # 收集master中受影响的"可纳入"PR详细信息
            affected_detail_list = []
            for pid, info in master_dict.items():
                if (info or {}).get("assessresult_first") == "可纳入":
                    affected_detail_list.append({
                        "pr_id": pid,
                        "system_title": info.get("system_title", ""),
                        "system_state": info.get("system_state", ""),
                        "team": info.get("team", ""),
                        "belongproduct": info.get("belongproduct", ""),
                        "assessresult_first": info.get("assessresult_first", ""),
                        "requirementanalysisowner": info.get("requirementanalysisowner", ""),
                        "planstartdateofdevelopment": info.get("planstartdateofdevelopment", ""),
                        "planfinishdateofdevelopment": info.get("planfinishdateofdevelopment", ""),
                        "impact_type": "跨领域影响主交付"
                    })
            if affected_detail_list:
                affected_count = len(affected_detail_list)
                affected_pr_ids = [d["pr_id"] for d in affected_detail_list]
                affected_pr_preview = ", ".join(affected_pr_ids[:5])
                affected_pr_suffix = f"...等{affected_count}个" if affected_count > 5 else f"等{affected_count}个"
                check_result_list.append({
                    **reject_pr_info,
                    "problem_type": "非可纳入影响主交付领域PR翻转",
                    "problem_description": (
                        f'PR的初评结论不是"可纳入", 影响主交付领域共{affected_count}个'
                        f'可纳入状态的PR需求翻转（涉及: {affected_pr_preview}{affected_pr_suffix}）'
                    ),
                    "check_date": DATE_FORMAT,
                    "default_problem_flag": "是",
                    "default_handle_person": reject_pr_info.get("requirementanalysisowner"),
                    "default_handle_date": DATE_FORMAT,
                    "default_handle_flag": "否",
                    "actual_handle_date": "",
                    "impact_check_flag": "MR分组逻辑",
                    # ✅ 保留原有字段
                    "affected_pr_count": affected_count,
                    "affected_pr_ids": affected_pr_ids,
                    # ✅ 新增detail_list字段
                    "detail_list": affected_detail_list
                })
                processed_prs.add(reject_pr_id)
    logger.info(f"✅ 初评结论检查完成 | MR分组: {len(obj_mr_pr_dict)} | "
               f"检查非可纳入PR: {len(master_reject_list)+len(other_reject_list)}个 | 发现问题: {len(check_result_list)}条")
    return check_result_list


def check_plan_date_impact_conflict(pr_info_list, reject_pr_ident_list):
    """
    检查需求计划日期的Impact冲突（完整版逻辑 - 修复版）

    【核心规则】
    1. 基于智能文本匹配识别需求间的影响关系
    2. Impact关联的需求之间，依赖方(other)的计划结束日期不应比被依赖方(master)晚3天及以上

    :param pr_info_list: 所有PR需求信息列表
    :param reject_pr_ident_list: 已拒绝/已废弃的PR ID列表
    :return: 检查结果列表
    """
    check_result_list = []
    # 构建快速查找字典
    all_master_pr_info_dict = {item.get("system_id"): item for item in pr_info_list}
    # 筛选主交付领域PR
    master_pr_ident_list = [item.get("system_id") for item in pr_info_list if item.get("ismasterdeliveryarea")]
    if not master_pr_ident_list:
        logger.info("未找到主交付领域PR，计划日期冲突检查跳过")
        return check_result_list
    # 获取主交付领域PR关联的MR
    master_mr_pr_dict = get_rdc_relation_id_dict({
        "rdcIdent_list": master_pr_ident_list,
        "linkRelationName": "father",
        "relatedWorkItemTypeKey": "MR",
        "employ_no": USER_NUM
    })
    if not master_mr_pr_dict:
        logger.info("未找到主交付领域PR关联的MR，计划日期冲突检查跳过")
        return check_result_list
    # 初始化分组字典
    obj_mr_pr_dict = {}
    for mr_ident in master_mr_pr_dict.keys():
        obj_mr_pr_dict[mr_ident] = {"master": master_mr_pr_dict[mr_ident], "other": []}
    # 获取每个MR下的所有子级PR
    master_mr_ident_list = list(master_mr_pr_dict.keys())
    all_pr_mr_dict = get_rdc_relation_id_dict({
        "rdcIdent_list": master_mr_ident_list,
        "linkRelationName": "son",
        "relatedWorkItemTypeKey": "PR",
        "employ_no": USER_NUM
    })
    all_mr_pr_dict = reverse_dict_key_value(all_pr_mr_dict)
    # 计算"other"类PR
    all_other_pr_ident_list = []
    for mr_ident in all_mr_pr_dict.keys():
        if mr_ident not in obj_mr_pr_dict:
            continue
        all_pr_of_single_mr_set = set(all_mr_pr_dict.get(mr_ident, []))
        master_pr_of_single_mr_set = set(obj_mr_pr_dict[mr_ident]["master"])
        other_pr_of_single_mr_list = list(all_pr_of_single_mr_set - master_pr_of_single_mr_set)
        all_other_pr_ident_list += other_pr_of_single_mr_list
        for other_pr_item in other_pr_of_single_mr_list:
            if other_pr_item not in reject_pr_ident_list:
                obj_mr_pr_dict[mr_ident]["other"].append(other_pr_item)
    # 只保留有other的MR
    obj_mr_pr_dict = {k: v for k, v in obj_mr_pr_dict.items() if len(v.get("other"))}
    if not obj_mr_pr_dict:
        logger.info("未找到存在依赖关系的MR分组，计划日期冲突检查跳过")
        return check_result_list
    obj_mr_pr_dict = convert_list_to_dict_structure(obj_mr_pr_dict)
    # 批量获取other类PR的详细信息
    all_other_pr_ident_list = list(set(all_other_pr_ident_list))
    all_other_pr_info_dict = {}
    if all_other_pr_ident_list:
        rdc_param_dict = {
            "rdcIdent_list": all_other_pr_ident_list,
            "workItemType_list": ["PR"] * len(all_other_pr_ident_list),
            "employ_no": USER_NUM
        }
        all_other_pr_info_list = get_rdc_info_list(rdc_param_dict)
        all_other_pr_info_dict = {
            item.get("system_id"): item 
            for item in all_other_pr_info_list 
            if item.get("system_state") not in ["已拒绝", "已废弃"]
        }
        logger.info(f"成功获取 {len(all_other_pr_info_dict)}/{len(all_other_pr_ident_list)} 条other类PR详情用于日期检查")
    else:
        all_other_pr_info_dict = {}
    # ========================================================================
    # 构建全局变量 SIMPLE_MR_PR_DICT（用于Impact分析）
    # ========================================================================
    global SIMPLE_MR_PR_DICT, SIMPLE_MR_PR_DICT_WITH_IMPACT
    SIMPLE_MR_PR_DICT = {}
    for mr_id, cats in obj_mr_pr_dict.items():
        master_ids = list(cats.get("master", {}).keys())
        other_ids = list(cats.get("other", {}).keys())
        SIMPLE_MR_PR_DICT[mr_id] = {
            "master": {
                pid: {"system_title": all_master_pr_info_dict.get(pid, {}).get("system_title", "")}
                for pid in master_ids
            },
            "other": {
                pid: {"system_title": all_other_pr_info_dict.get(pid, {}).get("system_title", "")}
                for pid in other_ids
            }
        }
    # 执行Impact关系分析
    SIMPLE_MR_PR_DICT_WITH_IMPACT = analyze_mr_pr_impact(SIMPLE_MR_PR_DICT)
    # ========================================================================
    # 日期冲突检查核心逻辑 (✅ 修复版：收集所有冲突而非仅第一个)
    # ========================================================================
    # 预构建 impact_details 快速查找表，避免重复计算或查找
    impact_details_lookup = {}
    for mr_id, impact_data in SIMPLE_MR_PR_DICT_WITH_IMPACT.items():
        for other_pr_id, other_impact_info in impact_data.get("other", {}).items():
            for detail in other_impact_info.get("impact_details", []):
                key = (mr_id, other_pr_id, detail.get("master_pr_id"))
                impact_details_lookup[key] = set(detail.get("common_words", []))
    for mr_id, impact_data in SIMPLE_MR_PR_DICT_WITH_IMPACT.items():
        other_dict = impact_data.get("other", {})
        for other_pr_id, other_impact_info in other_dict.items():
            impacted_masters = other_impact_info.get("impacted_masters", [])
            if not impacted_masters:
                continue
            other_pr_info = all_other_pr_info_dict.get(other_pr_id)
            if not other_pr_info:
                continue
            other_pf = other_pr_info.get("planfinishdateofdevelopment")
            other_ps = other_pr_info.get("planstartdateofdevelopment")
            fmt_other_pf = tran_date(other_pf) if other_pf else None
            if not fmt_other_pf: 
                continue
            # ✅ 修复步骤 1: 创建一个列表来收集当前 Other PR 所有冲突的 Master
            conflict_detail_list = []
            # 🔹 日期冲突检查: other比master晚3天及以上
            for master_item in impacted_masters:
                master_pr_id = master_item.get("pr_id")
                master_pr_info = all_master_pr_info_dict.get(master_pr_id)
                if not master_pr_info:
                    continue
                master_pf = master_pr_info.get("planfinishdateofdevelopment")
                master_ps = master_pr_info.get("planstartdateofdevelopment")
                fmt_master_pf = tran_date(master_pf) if master_pf else None
                if not fmt_master_pf:
                    continue
                date_diff_days = (fmt_other_pf - fmt_master_pf).days
                if date_diff_days >= 3:
                    # 从lookup表获取匹配关键词
                    match_words = list(impact_details_lookup.get((mr_id, other_pr_id, master_pr_id), set()))
                    # ✅ 修复步骤 2: 将符合条件的 Master 添加到收集列表中
                    conflict_detail_list.append({
                        "pr_id": master_pr_id,
                        "system_title": master_pr_info.get("system_title", ""),
                        "team": master_pr_info.get("team", ""),
                        "planfinishdateofdevelopment": master_pf,
                        "planstartdateofdevelopment": master_ps,
                        "assessresult_first": master_pr_info.get("assessresult_first", ""),
                        "match_words": match_words
                    })
            # ✅ 修复步骤 3: 遍历完所有 Masters 后，如果存在冲突，则生成一条汇总记录
            if conflict_detail_list:
                # 构建问题描述，展示所有冲突的 Master
                conflict_summaries = [f"{d['pr_id']}({d['planfinishdateofdevelopment']})" for d in conflict_detail_list]
                # 为了描述简洁，可以只显示前几个，但 detail_list 保留全部
                preview_count = 3
                preview_str = ", ".join(conflict_summaries[:preview_count])
                suffix = f"等{len(conflict_detail_list)}个" if len(conflict_detail_list) > preview_count else ""
                check_result_list.append({
                    **other_pr_info,
                    "problem_type": "计划结束开发日期存在问题",
                    "problem_description": (
                        f"依赖领域PR[{other_pr_id}]的计划结束开发日期{other_pf} "
                        f"比其影响的主交付领域PR{suffix}{preview_str}晚3天及以上"
                    ),
                    "check_date": DATE_FORMAT,
                    "default_problem_flag": "是",
                    "default_handle_person": other_pr_info.get("requirementanalysisowner"),
                    "default_handle_date": DATE_FORMAT,
                    "default_handle_flag": "否",
                    "actual_handle_date": "",
                    "impact_check_flag": "Impact分组逻辑",
                    # ✅ 修复步骤 4: 这里放入所有收集到的冲突详情
                    "detail_list": conflict_detail_list
                })
    # ========================================================================
    # 生成审计日志
    # ========================================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filepath = os.path.join(os.getcwd(), f"impact_date_check_report_{timestamp}.txt")
    impact_problem_details = []
    # 重新遍历以生成详细日志（也可以复用上面的逻辑，但为了保持日志独立性，这里再次遍历或使用已生成的数据）
    # 注意：为了日志准确，建议直接基于 SIMPLE_MR_PR_DICT_WITH_IMPACT 和原始数据重新计算日志内容，
    # 或者直接从 check_result_list 提取。这里保持原有逻辑结构，重新计算以确保日志完整性。
    for mr_id, impact_data in SIMPLE_MR_PR_DICT_WITH_IMPACT.items():
        for other_pr_id, other_impact_info in impact_data.get("other", {}).items():
            impacted_masters = other_impact_info.get("impacted_masters", [])
            if not impacted_masters: 
                continue
            other_pr_info = all_other_pr_info_dict.get(other_pr_id)
            if not other_pr_info: 
                continue
            other_pf = other_pr_info.get("planfinishdateofdevelopment")
            fmt_other_pf = tran_date(other_pf) if other_pf else None
            if not fmt_other_pf: 
                continue
            for master_item in impacted_masters:
                master_pr_id = master_item.get("pr_id")
                master_pr_info = all_master_pr_info_dict.get(master_pr_id)
                if not master_pr_info: 
                    continue
                master_pf = master_pr_info.get("planfinishdateofdevelopment")
                fmt_master_pf = tran_date(master_pf) if master_pf else None
                if not fmt_master_pf: 
                    continue
                date_diff_days = (fmt_other_pf - fmt_master_pf).days
                if date_diff_days >= 3:
                    impact_problem_details.append({
                        "mr_id": mr_id, 
                        "other_pr": other_pr_id, 
                        "master_pr": master_pr_id,
                        "date_diff_days": date_diff_days,
                        "other_pr_title": other_pr_info.get("system_title", ""),
                        "master_pr_title": master_pr_info.get("system_title", ""),
                        "other_plan_finish": other_pf, 
                        "master_plan_finish": master_pf,
                    })
    try:
        print(f"📋 Impact日期检查日志 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"{'='*70}\n\n")
        print(f"📊 统计: 共发现 {len(impact_problem_details)} 条日期校验问题（other比master晚3天及以上）\n\n")
        if impact_problem_details:
            print("🔍 问题详情列表:\n")
            for i, d in enumerate(impact_problem_details, 1):
                print(f"  {i}. MR[{d['mr_id']}]\n")
                print(f"     └─ Other(依赖方):  [{d['other_pr']}]《{d['other_pr_title']}》→ {d['other_plan_finish']}\n")
                print(f"     └─ Master(被依赖): [{d['master_pr']}]《{d['master_pr_title']}》→ {d['master_plan_finish']}\n")
                print(f"     └─ 日期差: other比master晚 {d['date_diff_days']}天 (>=3天 ⚠️)\n\n")
        else:
            print("✅ 未发现 Impact 关联下的日期校验问题。\n")
        print(f"\n{'='*70}\n")
    except Exception as e:
        logger.warning(f"日志保存失败: {e}")
    logger.info(f"计划日期检查完成，发现 {len(check_result_list)} 条日期冲突记录（每条记录可能包含多个冲突Master）")
    return check_result_list


def get_rdc_relation_id_dict(rdc_params: dict):
    rdcIdent_list = rdc_params.get("rdcIdent_list", [])
    linkRelationName = rdc_params.get("linkRelationName", "")
    relatedWorkItemTypeKey = rdc_params.get("relatedWorkItemTypeKey", "")
    employ_no = rdc_params.get("employ_no", "")
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/relations/query_related_byTime"
    headers = {"X-Tenant-Id": "ZTE", "X-Emp-No": employ_no, "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a", "X-Lang-Id": "zh_CN", "Content-Type": "application/json"}
    batch_size = 200; relation_id_dict = defaultdict(list)
    for i in range(0, len(rdcIdent_list), batch_size):
        batch = rdcIdent_list[i:i + batch_size]
        body = {"workItemIds": batch, "linkRelationName": linkRelationName, "visible": True}
        try:
            response = requests.post(url, data=json.dumps(body), headers=headers, timeout=30)
            result_list = response.json().get("bo", {}).get("items", []) if response.status_code == 200 else []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for batch {batch}: {e}"); result_list = []
        if linkRelationName == "father" and result_list:
            for r in result_list:
                rid, sid = r.get("relatedWorkItemId"), r.get("workItemId")
                if rid and sid and sid not in relation_id_dict[rid]: relation_id_dict[rid].append(sid)
        else:
            for r in result_list:
                if r.get("relatedWorkItemTypeKey") == relatedWorkItemTypeKey:
                    rid, sid = r.get("relatedWorkItemId"), r.get("workItemId")
                    if rid and sid and sid not in relation_id_dict[rid]: relation_id_dict[rid].append(sid)
    return dict(relation_id_dict)


def get_rdc_info_list(rdc_params):
    rdcIdent_list = rdc_params.get("rdcIdent_list", [])
    workItemType_list = rdc_params.get("workItemType_list", [])
    employ_no = rdc_params.get("employ_no", "")
    if not rdcIdent_list: return []
    groups = defaultdict(list)
    for rid in rdcIdent_list:
        if "-" not in rid: logger.warning(f"Invalid RDC ID format: {rid}"); continue
        groups[rid.split("-")[0]].append(rid)
    final_result = []
    for space, ids in groups.items():
        url = f"https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/{space}/queries/v2/list_detail"
        headers = {"X-Tenant-Id": "ZTE", "X-Emp-No": employ_no, "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a", "X-Lang-Id": "zh_CN", "Content-Type": "application/json"}
        body = {"ids": ids, "workItemTypeKeys": workItemType_list, "select": PR_FIELD_LIST}
        try:
            res = requests.post(url, data=json.dumps(body), headers=headers, timeout=30)
            if res.status_code == 200 and res.json().get('code', {}).get('code') == '0000':
                for item in res.json().get("bo", []):
                    final_result.append({
                        "system_id": item.get("System_Id"), "system_state": item.get("System_State", {}).get("name", ""),
                        "system_createddate": utc_to_beijing_str(item.get("System_CreatedDate")),
                        "system_createdby": item.get("System_CreatedBy", {}).get("nameDisplayLong", ""),
                        "system_changeddate": utc_to_beijing_str(item.get("System_ChangedDate")),
                        "system_changedby": item.get("System_ChangedBy", {}).get("nameDisplayLong", ""),
                        "system_appointedto": item.get("System_AppointedTo", {}).get("nameDisplayLong", ""),
                        "system_areapath": item.get("System_AreaPath", {}).get("label", ""),
                        "team": item.get("Team", {}).get("label", ""), "system_title": item.get("System_Title"),
                        "belongproduct": item.get("BelongProduct", {}).get("label", ""),
                        "requirementpreplanning": item.get("RequirementPrePlanning"),
                        "system_description_html": item.get("System_Description_html"),
                        "acceptancecriteria_html": item.get("AcceptanceCriteria_html"),
                        "requirementanalysisowner": item.get("RequirementAnalysisOwner", {}).get("nameDisplayLong", ""),
                        "specificationbyexampleurl": item.get("SpecificationByExampleUrl"),
                        "specificationbyexamplestate": item.get("SpecificationByExampleState"),
                        "designspecificationurl": item.get("DesignSpecificationUrl"),
                        "designstate": item.get("DesignState"), "featureurl": item.get("FeatureUrl"),
                        "belongfeaturecatalog": item.get("BelongFeatureCatalog"),
                        "featureid": item.get("FeatureId"), "featurename_cn": item.get("FeatureName_Cn"),
                        "checkresultofchipscheme": item.get("CheckResultOfChipScheme"),
                        "isautocreated": item.get("IsAutoCreated"), "assessresult_first": item.get("AssessResult_First"),
                        "reusedegree": item.get("ReuseDegree"),
                        "planstartdateofdevelopment": utc_to_beijing_str(item.get("PlanStartDateOfDevelopment")),
                        "planfinishdateofdevelopment": utc_to_beijing_str(item.get("PlanFinishDateOfDevelopment")),
                        "accesscheck": item.get("AccessCheck"),
                        "belongreleaseversion": item.get("BelongReleaseVersion", {}).get("baseDataValue", {}).get("label"),
                        "ismasterdeliveryarea": item.get("IsMasterDeliveryArea"),
                        "script_update_date": SCRIPT_UPDATE_DATE,
                    })
        except Exception as e: logger.error(f"Network error querying {space}: {e}")
    return final_result


def send_check_pr_info_list_to_linghang(data_list, batch_size=1000):
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_check_pr_info_list"
    headers = {"Content-Type": "application/json"}
    total, suc, fail = len(data_list), 0, 0
    for i in range(0, total, batch_size):
        bd = data_list[i:i+batch_size]; bn = i//batch_size+1; tb = (total+batch_size-1)//batch_size
        try:
            r = requests.post(url, json={"data_list": bd}, headers=headers, timeout=30)
            if r.status_code == 200: suc += len(bd); print(f"[成功] {bn}/{tb}")
            else: fail += len(bd); print(f"[失败] {bn}/{tb}")
        except: fail += len(bd); print(f"[异常] {bn}/{tb}")
    print(f"总计:{total} | 成功:{suc} | 失败:{fail}"); return suc, fail


def update_handle_pr_info_list_to_linghang(script_update_date, handle_date):
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_handle_pr_info_list"
    try:
        r = requests.post(url, json={"script_update_date": script_update_date, "handle_date": handle_date}, headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200: print(f"本次完成 {r.json().get('data',{}).get('update_count',0)} 条需求整改")
    except Exception as e: logger.error(f"[异常] {e}")


def update_cal_field_to_linghang():
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_cal_field"
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200: print(f"[成功] 计算字段更新成功")
    except Exception as e: logger.error(f"[异常] {e}")


def update_check_pr_summary_table_to_linghang(summary_date):
    url = f"{LINGHANG_BASE_URL}/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_summary_table_data_list"
    try:
        r = requests.post(url, json={"summary_date": summary_date}, headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code == 200: print(f"[成功] 汇总统计数据更新成功")
    except Exception as e: logger.error(f"[异常] {e}")


def reverse_dict_key_value(original_dict):
    rev = defaultdict(list)
    for k, vl in original_dict.items():
        for v in vl: rev[v].append(k)
    return dict(rev)


def convert_list_to_dict_structure(original_dict):
    res = {}
    for mr, cats in original_dict.items():
        res[mr] = {cat: {pid: {} for pid in plist} for cat, plist in cats.items()}
    return res


def tran_date(date_str, fmt="%Y-%m-%d %H:%M:%S"):
    try: return datetime.strptime(date_str, fmt) if date_str else None
    except: return None


def start_run():
    global DATE_FORMAT
    DATE_FORMAT = get_current_date()
    all_pr_info_list = get_pr_info_list(USER_NUM, USER_TOKEN)
    # all_pr_info_list = [item for item in all_pr_info_list if item.get("requirementpreplanning")=="M721 V5.50R1"]
    pr_check_result_list = get_pr_check_result_list(all_pr_info_list)
    send_check_pr_info_list_to_linghang(pr_check_result_list)
    update_handle_pr_info_list_to_linghang(SCRIPT_UPDATE_DATE, DATE_FORMAT)
    update_cal_field_to_linghang()
    update_check_pr_summary_table_to_linghang(DATE_FORMAT)


if __name__ == "__main__":
    start_run()