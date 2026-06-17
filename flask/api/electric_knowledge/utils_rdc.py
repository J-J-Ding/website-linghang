import json
import time
import copy
import string
import logging
import hashlib
import requests
import traceback
from typing import Dict, List, Any
from collections import defaultdict


logger = logging.getLogger("Logger")
APP_CODE = "d09fddc101a14bb3bfa0fbd02ed1932a"
TABLE = [
    {
        "value": "description" ,
        "type": "html",
        "key": "System_Description_html"
    },
    {
        "value": "analysisReport",
        "type": "html",
        "key": "AnalysisReport_html"
    },
    {
        "value": "acceptance_criteria",
        "type": "html",
        "key": "AcceptanceCriteria_html"
    },
    {
        "value": "requirementPrePlanning",
        "type": "string",
        "key": "RequirementPrePlanning"
    },
    {
        "value": "featureContentLink",
        "type": "string",
        "key": "FeatureUrl"
    },
    {
        "value":  "belong_domain",
        "type": "advancedData",
        "key": "System_AreaPath"
    },
    {
        "value": "belongProduct",
        "type": "advancedData",
        "key": "BelongProduct"
    },
    {
        "value": "specificationByExampleUrl",
        "type": "string",
        "key": "SpecificationByExampleUrl"
    },
    {
        "value": "designSpecificationUrl",
        "type": "string",
        "key": "DesignSpecificationUrl"
    },
    {
        "value": "requirementPurpose",
        "type": "string",
        "key": "RequirementPurpose"
    },
    {
        "value": "priority",
        "type": "string",
        "key": "Priority"
    },
    {
        "value": "requirementCategory",
        "type": "string",
        "key": "RequirementCategory"
    },
    {
        "value": "belongFeatureCatalog",
        "type": "string",
        "key": "BelongFeatureCatalog"
    },
    {
        "value": "requirementType",
        "type": "string",
        "key": "RequirementType"
    },
    {
        "value": "verificationMode",
        "type": "string",
        "key": "VerificationMode"
    },
    {
        "value": "verificationTeam",
        "type": "string",
        "key": "VerificationTeam"
    },
    {
        "value": "partName",
        "type": "string",
        "key": "PartName"
    },
    {
        "value": "developmenttype",
        "type": "string",
        "key": "DevelopmentType"
    },
    {
        "value": "reusedegree",
        "type": "string",
        "key": "ReuseDegree"
    }
]


def get_rdc_inone_headers(user_num):
    return {
        "X-Tenant-Id": "ZTE",
        "Content-Type": "application/json",
        "appCode": APP_CODE,
        "X-Emp-No": user_num,
        'X-Auth-Value': 'f5f3fa253674c3e338b792eb8408f919'
    }


def get_rdc_pr_team_list(user_num, user_token):
    """
    调用指定GET接口，提取namePath为5G-OTN/02-L1/对应字典的name组成列表
    """
    # 接口地址
    url = "https://rdcloud.zte.com.cn/zte-rdcloud-rdc-rdcserver/rdc/team/queryTeamListByProject?spaceId=80880"
    # 请求头（根据实际情况可能需要添加，比如认证信息）
    headers = {
        "X-Emp-No": user_num,
        'X-Auth-Value': user_token
    }
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers, timeout=30)
        # 检查请求是否成功
        response.raise_for_status()
        # 解析JSON响应
        result = response.json()
        # 初始化目标列表
        target_names = []
        # 检查响应结构是否正确
        if result.get("code") == "1" and isinstance(result.get("bo"), list):
            # 遍历bo列表中的每个字典
            for item in result["bo"]:
                # 判断namePath是否符合要求
                if item.get("namePath").startswith("5G-OTN/02-L1/"):
                    # 提取name并添加到列表
                    name = item.get("name")
                    if name:  # 避免空值
                        target_names.append(name)
        return target_names
    except requests.exceptions.RequestException as e:
        print(f"请求接口失败: {e}")
        return []
    except ValueError as e:
        print(f"解析JSON失败: {e}")
        return []
    except Exception as e:
        print(f"未知错误: {e}")
        return []


def get_rdc_change_req_info_list(rdc_params:dict):
    results = []
    rdc_space = rdc_params.get("rdc_space", "")
    related_board_name = rdc_params.get("related_board_name", "")
    change_req_dict = rdc_params.get("change_req_dict", {})
    rdcIdent_list = list(change_req_dict.keys())
    workItemType_list = rdc_params.get("workItemType_list", [])
    employ_no =rdc_params.get("employ_no","")
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/" + rdc_space + "/queries/v2/list_detail"
    headers = {
        "X-Tenant-Id":"ZTE",
        "X-Emp-No": employ_no,
        "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id":"zh_CN",
        "Content-Type":"application/json"
    }
    body = {
        "ids":rdcIdent_list,
        "workItemTypeKeys": workItemType_list,
        "select": ["System_Id", "System_State", "System_Title", "System_CreatedBy", "System_CreatedDate", "System_ChangedBy", "System_ChangedDate", "System_AreaPath", "BelongTeamLimitRange", "IntroductedBy"]
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        results = response_json["bo"]
    else:
        results = []
    final_result = []
    for result in results:
        final_result.append({
            "rdc_ident": result['System_Id'],
            "rdc_title": result['System_Title'],
            "related_board_name": related_board_name,
            "related_rdc_ident": change_req_dict[result['System_Id']][0],
            "rdc_created_by": result.get('System_CreatedBy', {}).get("nameDisplayLong"),
            "rdc_created_time": result.get('System_CreatedDate'),
            "rdc_changed_by": result.get('System_ChangedBy', {}).get("nameDisplayLong"),
            "rdc_changed_time": result.get('System_ChangedDate'),
            "rdc_field": result.get('System_AreaPath', {}).get("name"),
            "rdc_team": result.get('BelongTeamLimitRange', {}).get("name", "").split('/')[-1],
            "rdc_introducted_by": result.get('IntroductedBy', {}).get("nameDisplayLong"),
            "requirement_status": result['System_State']['nameZh']
        })
    return final_result


def create_RDC(rdc_params_list:list, task_id=""):
    results = []
    max_retries = 2
    for rdc_params in rdc_params_list:
        workItemTypeKey = rdc_params.get("workItem_type", "") if rdc_params.get("workItem_type", "") else "PR"
        rdc_space = rdc_params.get("rdc_space", "")
        rdc_title = rdc_params.get("rdc_title", "")
        description = rdc_params.get("description", "")
        if not description:
            description = " "
        acceptance_criteria = rdc_params.get("acceptance_criteria", "")
        if not acceptance_criteria:
            acceptance_criteria = " "
        employ_no =rdc_params.get("employ_no","")
        featureContentLink = rdc_params.get("featureContentLink", "")
        if not featureContentLink:
            featureContentLink = " "
        analysisReport =rdc_params.get("changeAnalysis","")
        if not analysisReport:
            analysisReport = " "
        belong_domain = rdc_params.get("belong_domain", "")
        if not belong_domain:
            belong_domain = " "
        development_type = rdc_params.get("DevelopmentType", "") #开发类型
        reuse_degree = rdc_params.get("ReuseDegree", "")  #复用程度
        if (not reuse_degree) and belong_domain in ['02-L1', '05-支撑', '01-L0光系统', '03-L2', '13-智能控制']:
            reuse_degree = "全代码"
        belongProduct =rdc_params.get("belongProduct","")
        requirementPrePlanning = rdc_params.get("requirementPrePlanning", "")
        specificationByExampleUrl = rdc_params.get("specificationByExampleUrl", "")
        designSpecificationUrl = rdc_params.get("designSpecificationUrl", "")
        requirementPurpose = rdc_params.get("requirementPurpose", "")
        priority = rdc_params.get("priority", "")
        requirementCategory = rdc_params.get("requirementCategory", "")
        belongFeatureCatalog = rdc_params.get("belongFeatureCatalog", "")
        requirementType = rdc_params.get("requirementType", "")
        verificationMode = rdc_params.get("verificationMode", "")
        verificationTeam = rdc_params.get("verificationTeam", "")
        partName = rdc_params.get("partName", "")
        belongTeam = rdc_params.get("belongTeam", "")
        url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/" + rdc_space + "/work_items"
        headers = {
            "X-Tenant-Id":"ZTE",
            "X-Emp-No": employ_no,
            "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
            "X-Lang-Id":"zh_CN",
            "Content-Type":"application/json",
            "User-Agent": f"RDCClient-{getHashCode(rdc_title)}"  
        }
        body = {
            "workItemTypeKey":workItemTypeKey,
            "fields": [
                {
                    "value": False,
                    "type": "boolean",
                    "key": "ShouldConnect"
                },
                {
                    "value": {
                        "userId": employ_no
                    },
                    "type": "user",
                    "key": "System_CreatedBy"
                },
                {
                    "value": "不需要DoD检查",
                    "type": "string",
                    "key": "DodCheckResult"
                },
                {
                    "value": "<p>" + description + "</p>",
                    "type": "html",
                    "key": "System_Description_html"
                },

                {
                    "value": "<p>" + analysisReport + "</p>",
                    "type": "html",
                    "key": "AnalysisReport_html"
                },

                {
                    "value": "<p>" + acceptance_criteria + "</p>",
                    "type": "html",
                    "key": "AcceptanceCriteria_html"
                },
                {
                    "value": requirementPrePlanning,
                    "type": "string",
                    "key": "RequirementPrePlanning"
                },
                {
                    "value": "0",
                    "type": "string",
                    "key": "ProgressFlag"
                },
                {
                    "value": rdc_title,
                    "type": "string",
                    "key": "System_Title"
                },
                {
                    "value": False,
                    "type": "boolean",
                    "key": "IsChangedRequirement"
                },
                {
                    "value": False,
                    "type": "boolean",
                    "key": "IsKeyRequirement"
                },
                {
                    "value": featureContentLink,
                    "type": "string",
                    "key": "FeatureUrl"
                },
                {
                    "value":  belong_domain,
                    "type": "advancedData",
                    "key": "System_AreaPath"
                },
                {
                    "value": belongProduct,
                    "type": "advancedData",
                    "key": "BelongProduct"
                },
                {
                    "value": specificationByExampleUrl,
                    "type": "string",
                    "key": "SpecificationByExampleUrl"
                },
                {
                    "value": designSpecificationUrl,
                    "type": "string",
                    "key": "DesignSpecificationUrl"
                },
                {
                    "value": requirementPurpose,
                    "type": "string",
                    "key": "RequirementPurpose"
                },
                {
                    "value": priority,
                    "type": "string",
                    "key": "Priority"
                },
                {
                    "value": requirementCategory,
                    "type": "string",
                    "key": "RequirementCategory"
                },
                {
                    "value": belongFeatureCatalog,
                    "type": "string",
                    "key": "BelongFeatureCatalog"
                },
                {
                    "value": requirementType,
                    "type": "string",
                    "key": "RequirementType"
                },
                {
                    "value": verificationMode,
                    "type": "string",
                    "key": "VerificationMode"
                },
                {
                    "value": [
                        "[" + verificationTeam + "]"
                    ],
                    "type": "string",
                    "key": "VerificationTeam"
                },
                {
                    "value": partName,
                    "type": "string",
                    "key": "PartName"
                },
                {
                    "value": True,
                    "type": "boolean",
                    "key": "IsAutoCreated",
                },
                {
                    "value": belongTeam,
                    "type": "advancedData",
                    "key": "Team"
                },
                {
                    "value": development_type,
                    "type": "string",
                    "key": "DevelopmentType"
                },
                {
                    "value": reuse_degree,
                    "type": "string",
                    "key": "ReuseDegree"
                }
            ]
        }
        for handler in logger.handlers:
            handler.flush()
        result = dict()
        related_parent_rdc = ""
        related_problem_num = 1
        for attempt in range(max_retries):
            try:
                response = requests.post(url, data=json.dumps(body), headers=headers, verify=True, timeout=(10, 120))
                if response.status_code == 200:
                    response_json = response.json()
                    if response_json['code']['code'] == '0000':
                        result = response_json["bo"]
                        break
                    else:
                        failed_msg = response_json['code']['msg']
                        logger.error(f"-----------RDC标题为 {rdc_title} 对应的PR_RDC创建失败，失败原因：{failed_msg}")
                        if task_id:
                            from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                            task_info_dict = {"task_err_reason": f"PR: {failed_msg}"}
                            update_task_info_dict(task_id, task_info_dict)
                        if '无权限' in failed_msg:
                            return results, False
                else:
                    logger.error(f"-----------RDC标题为 {rdc_title} 对应的PR_RDC创建失败，失败原因：RDC创建API返回状态码为 非200")
                    if task_id:
                        from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                        task_info_dict = {"task_err_reason": f"PR: RDC创建API返回状态码为 非200"}
                        update_task_info_dict(task_id, task_info_dict)
            except requests.exceptions.RequestException as e:
                logger.error(f"-----请求异常 pr_rdc_title:\n{rdc_title}\n失败原因:\n{e}\n{traceback.format_exc()}")
                if task_id:
                    from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                    task_info_dict = {"task_err_reason": f"PR: {e}{traceback.format_exc()}"}
                    update_task_info_dict(task_id, task_info_dict)
            except Exception as e:
                logger.error(f"-----------RDC标题为 {rdc_title} 对应的PR_RDC创建失败，失败原因：{e}\n{traceback.format_exc()}")
                if task_id:
                    from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                    task_info_dict = {"task_err_reason": f"PR: {e}{traceback.format_exc()}"}
                    update_task_info_dict(task_id, task_info_dict)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        results.append({
            "rdcIdent": result.get("id",""), 
            "rdcTitle":result.get("System_Title",""),
            "requirementPrePlanVersion":result.get("RequirementPrePlanning",""),
            "requirementStatus": result.get("System_State", {}).get("nameZh",""), 
            "parentNodeRdc": related_parent_rdc, 
            "rdcProblemNum":related_problem_num})
    return results, True


def getHashCode(content):
    if not content:
        return ''
    hash_object = hashlib.blake2b(str(content).encode('utf-8'), digest_size=32)
    return hash_object.hexdigest()


def create_RDC_MR(rdc_params_list:list, task_id=""):
    results = []
    max_retries = 2
    for rdc_params in rdc_params_list:
        employ_no =rdc_params.get("employ_no","")
        workItemTypeKey = rdc_params.get("workItem_type", "") if rdc_params.get("workItem_type", "") else "PR"
        rdc_space = rdc_params.get("rdc_space", "")
        rdc_title = rdc_params.get("rdc_title", "")
        description = rdc_params.get("description", "")
        if not description:
            description = " "
        acceptance_criteria = rdc_params.get("acceptance_criteria", "")
        if not acceptance_criteria:
            acceptance_criteria = " "
        analysisReport = rdc_params.get("changeAnalysis","")
        if not analysisReport:
            analysisReport = " "
        belong_domain = rdc_params.get("belong_domain", "")
        if not belong_domain:
            belong_domain = "02-L1"
        depend_domain = rdc_params.get("depend_domain", "")
        if not depend_domain:
            depend_domain = "02-L1"
        belongProduct =rdc_params.get("belongProduct","")
        requirementPrePlanning = rdc_params.get("requirementPrePlanning", "")
        specificationByExampleUrl = rdc_params.get("specificationByExampleUrl", "")
        designSpecificationUrl = rdc_params.get("designSpecificationUrl", "")
        requirementPurpose = rdc_params.get("requirementPurpose", "")
        priority = rdc_params.get("priority", "")
        requirementCategory = rdc_params.get("requirementCategory", "")
        verificationMode = rdc_params.get("verificationMode", "")
        verificationTeam = rdc_params.get("verificationTeam", "")
        marketTarget = rdc_params.get("marketTarget", "")
        targetMarket = rdc_params.get("targetMarket", "")
        acceptanceOwner = rdc_params.get("acceptanceOwner", "")
        # 新增MR创建时的字段提取
        requirement_source = rdc_params.get("requirementSource", "")
        requirement_submitter = rdc_params.get("requirementSubmitter", "")
        customer = rdc_params.get("customer", "")
        expected_finish_date = rdc_params.get("expectedFinishDate", "")
        # 将字符串"是"/"否"转换为boolean值
        is_key_requirement = rdc_params.get("IsKeyRequirement", "").lower() == "是"
        is_chip_requirement = rdc_params.get("IsChipRequirement", "").lower() == "是"
        is_competitive_requirement = rdc_params.get("IsCompetitiveRequirement", "").lower() == "是"
        is_medium_long_term_requirement = rdc_params.get("IsMediumLongTermRequirement", "").lower() == "是"
        url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/" + rdc_space + "/work_items"
        headers = {
            "X-Tenant-Id":"ZTE",
            "X-Emp-No": employ_no,
            "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
            "Content-Type":"application/json",
            "User-Agent": f"RDCClient-{getHashCode(rdc_title)}"  
        }
        body = {
            "workItemTypeKey":workItemTypeKey,
            "fields": [
                {
                    "value": False,
                    "type": "boolean",
                    "key": "ShouldConnect" #"是否需要拉通"
                },
                {
                    "value": {
                        "userId": employ_no
                    },
                    "type": "user",
                    "key": "System_CreatedBy" #"创建人"
                },
                {
                    "value": "不需要DoD检查",
                    "type": "string",
                    "key": "DodCheckResult"  # "DoD检查结果"
                },
                {
                    "value": "<p>" + description + "</p>",
                    "type": "html",
                    "key": "System_Description_html"  # "描述"
                },
                {
                    "value": "<p>" + analysisReport + "</p>",
                    "type": "html",
                    "key": "AnalysisReport_html" # "分析说明"
                },
                {
                    "value": "<p>" + acceptance_criteria + "</p>",
                    "type": "html",
                    "key": "AcceptanceCriteria_html" # "验收准则"
                },
                {
                    "value": requirementPrePlanning,
                    "type": "string",
                    "key": "RequirementPrePlanning" # "需求预规划"
                },
                {
                    "value": requirementPrePlanning,
                    "type": "string",
                    "key": "ProductRoadmap" # "产品路标"同PR需求预规划字段
                },
                {
                    "value": "0",
                    "type": "string",
                    "key": "ProgressFlag" # "进展标识"
                },
                {
                    "value": rdc_title,
                    "type": "string",
                    "key": "System_Title" # "标题"
                },
                {
                    "value": False,
                    "type": "boolean",
                    "key": "IsChangedRequirement" # "是否变更需求"
                },
                {
                    "value": is_key_requirement,
                    "type": "boolean",
                    "key": "IsKeyRequirement"  # "是否关键需求"
                },
                {
                    "value":  depend_domain,
                    "type": "advancedData",
                    "key": "DependentArea" # "依赖领域"
                },
                {
                    "value":  belong_domain,
                    "type": "advancedData",
                    "key": "System_AreaPath" # "领域"
                },
                {
                    "value": belongProduct,
                    "type": "advancedData",
                    "key": "BelongProduct" # "所属产品"
                },
                {
                    "value": specificationByExampleUrl,
                    "type": "string",
                    "key": "SpecificationByExampleUrl" # "需求实例化链接"
                },
                {
                    "value": designSpecificationUrl,
                    "type": "string",
                    "key": "DesignSpecificationUrl" # "方案文档链接"
                },
                {
                    "value": requirementPurpose,
                    "type": "string",
                    "key": "RequirementPurpose"  # "需求用途"
                },
                {
                    "value": priority,
                    "type": "string",
                    "key": "Priority" # "优先级"
                },
                {
                    "value": requirementCategory,
                    "type": "string",
                    "key": "RequirementCategory" # "需求类别"
                },
                {
                    "value": verificationMode,
                    "type": "string",
                    "key": "VerificationMode" # "验证方式"
                },
                {
                    "value":  verificationTeam,
                    "type": "string",
                    "key": "VerificationTeam" # "验证团队"
                },
                #MR 新增
                {
                    "value": requirement_source,
                    "type": "string",
                    "key": "RequirementSource" # "需求来源"
                },
                {
                    "value": requirement_submitter,
                    "type": "user",
                    "key": "RequirementSubmitter" # "需求提出人"
                },
                {
                    "value": expected_finish_date,
                    "type": "date",
                    "key": "ExpectedFinishDate" # "期望完成日期"
                },
                {
                    "value": is_chip_requirement,
                    "type": "boolean",
                    "key": "IsChipRequirement" # "是否芯片需求"
                },
                {
                    "value": is_competitive_requirement,
                    "type": "boolean",
                    "key": "IsCompetitiveRequirement" # "是否竞争力需求"
                },
                {
                    "value": is_medium_long_term_requirement,
                    "type": "boolean",
                    "key": "IsMediumLongTermRequirement" # "是否中长期需求"
                },
                {
                    "value": False,
                    "type": "boolean",
                    "key": "IsServiceableBaselinedRequirement" # "可服基线需求"
                },
                {
                    "value": customer,
                    "type": "advancedData",
                    "key": "Customer"  #"客户"
                },
                {
                    "value": targetMarket,
                    "type": "string",
                    "key": "TargetMarket"  #"目标市场"
                },
                {
                    "value": marketTarget,
                    "type": "string",
                    "key": "MarketTarget"  #"市场目标"
                },
                {
                    "value": acceptanceOwner,
                    "type": "user",
                    "key": "AcceptanceOwner"  #"需求验收负责人"
                },
                {
                    "value": True,
                    "type": "boolean",
                    "key": "IsAutoCreated"  # "是否自动拆分"
                }
            ]
        }
        for handler in logger.handlers:
            handler.flush()
        result = dict()
        related_parent_rdc = ""
        related_problem_num = 1
        for attempt in range(max_retries):
            try:
                response = requests.post(url, data=json.dumps(body), headers=headers, verify=True, timeout=(10, 120))  # 发起POST请求
                if response.status_code == 200:
                    response_json = response.json()
                    if response_json['code']['code'] == '0000':
                        result = response_json["bo"]
                        break
                    else:
                        failed_msg = response_json['code']['msg']
                        logger.error(f"-----------RDC标题为 {rdc_title} 对应的MR_RDC创建失败，失败原因：{failed_msg}")
                        if task_id:
                            from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                            task_info_dict = {"task_err_reason": f"MR: {failed_msg}"}
                            update_task_info_dict(task_id, task_info_dict)
                        if '无权限' in failed_msg:
                            return results, False
                else:
                    logger.error(f"-----------RDC标题为 {rdc_title} 对应的MR_RDC创建失败，失败原因：RDC创建API返回状态码为 非200")
                    if task_id:
                        from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                        task_info_dict = {"task_err_reason": "MR_RDC创建API返回状态码为 非200"}
                        update_task_info_dict(task_id, task_info_dict)
            except requests.exceptions.RequestException as e:
                logger.error(f"-----请求异常 mr_rdc_title:\n{rdc_title}\n失败原因:\n{e}\n{traceback.format_exc()}")
            except Exception as e:
                logger.error(f"-----------RDC标题为 {rdc_title} 对应的MR_RDC创建失败，失败原因：{e}\n{traceback.format_exc()}")
                if task_id:
                    from electric_knowledge.front_rdc_split_task_data_service import update_task_info_dict
                    task_info_dict = {"task_err_reason": f"MR: {e}{traceback.format_exc()}"}
                    update_task_info_dict(task_id, task_info_dict)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        results.append({
            "rdcIdent": result.get("id",""),
            "rdcTitle":result.get("System_Title",""),
            "requirementPrePlanVersion":result.get("RequirementPrePlanning",""),
            "requirementStatus": result.get("System_State", {}).get("nameZh",""), 
            "parentNodeRdc": related_parent_rdc,
            "rdcProblemNum":related_problem_num})
    return results, True


def update_RDC_relatedWorkItemId(body:list, employ_no):
    if not body:
        return []
    results = []
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/relations/batch_create"
    headers = {
        "X-Tenant-Id":"ZTE",
        "X-Emp-No": employ_no,
        "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id":"zh_CN",
        "Content-Type":"application/json"
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)  # 发起POST请求
    related_parent_rdc = ""
    related_problem_num = 1
    if response.status_code == 200:
        response_json = response.json()
        if response_json['code']['code'] == '0000':
            result = response_json["bo"]
        else:
            logger.error(f"-----------body:{body}")
    else:
        logger.error(f"-----------body:{body}")
    if result:
        results.append({
            "rdcIdent": result.get("id",""), 
            "rdcTitle":result.get("System_Title",""),
            "requirementPrePlanVersion":result.get("RequirementPrePlanning",""),
            "parentNodeRdc": related_parent_rdc, 
            "rdcProblemNum":related_problem_num})
    return results


def add_tag_RDC(rdc_space:str, tags:list, workItemIds:list, employ_no):
    results = []
    rdc_title = "add_tag_RDC"
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/" + rdc_space + "/work_items/tag/batchAdd"
    headers = {
        "X-Tenant-Id":"ZTE",
        "X-Emp-No": employ_no,
        "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id":"zh_CN",
        "Content-Type":"application/json"
    }
    body = {
        "tags":tags,
        "userId":employ_no,
        "workItemIds":workItemIds
    }
    response = requests.post(url, data=json.dumps(body), headers=headers)
    related_parent_rdc = ""
    related_problem_num = 1
    if response.status_code == 200:
        response_json = response.json()
        if response_json['code']['code'] == '0000':
            result = response_json["bo"]
        else:
            logger.error(f"-----------RDC标题为 {rdc_title} 对应的RDC创建失败，失败原因：{response_json['code']['msg']}")
            logger.error(f"-----------body:{body}")
    else:
        logger.error(f"-----------RDC标题为 {rdc_title} 对应的RDC创建失败，失败原因：RDC创建API返回状态码为 非200")
        logger.error(f"-----------body:{body}")
    return results


def query_RDC(rdc_params: dict):
    rdcIdent_list = rdc_params.get("rdcIdent_list", [])
    workItemType_list = rdc_params.get("workItemType_list", [])
    employ_no = rdc_params.get("employ_no", "")
    if not rdcIdent_list:
        return []
    # Step 1: 按前缀分组
    groups = defaultdict(list)
    for rdc_id in rdcIdent_list:
        if "-" not in rdc_id:
            logger.warning(f"Invalid RDC ID format (no '-'): {rdc_id}, skipping.")
            continue
        prefix = rdc_id.split("-")[0]
        groups[prefix].append(rdc_id)
    final_result = []
    # Step 2: 对每个分组发起独立请求
    for rdc_space, ids_in_group in groups.items():
        url = f"https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/{rdc_space}/queries/v2/list_detail"
        headers = {
            "X-Tenant-Id": "ZTE",
            "X-Emp-No": employ_no,
            "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
            "X-Lang-Id": "zh_CN",
            "Content-Type": "application/json"
        }
        body = {
            "ids": ids_in_group,
            "workItemTypeKeys": workItemType_list,
            "select": ["System_Id", "System_State", "System_Title", "System_Description_html", "AcceptanceCriteria_html", "RequirementPrePlanning", "SpecificationByExampleUrl", "DesignSpecificationUrl", "DependentArea", "BelongProduct", "ProductRoadmap"]
        }
        try:
            response = requests.post(url, data=json.dumps(body), headers=headers, timeout=30)
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get('code', {}).get('code') == '0000':
                    results = response_json.get("bo", [])
                    for result in results:
                        final_result.append({
                            "rdcIdent": result['System_Id'],
                            "rdcTitle": result['System_Title'],
                            "requirementPrePlanVersion": result.get('RequirementPrePlanning'),
                            "requirementStatus": result['System_State'].get('nameZh'),
                            "description": result.get('System_Description_html'),
                            "acceptanceCriteria": result.get('AcceptanceCriteria_html'),
                            "specificationByExampleUrl": result.get('SpecificationByExampleUrl'),
                            "designSpecificationUrl": result.get('DesignSpecificationUrl'),
                            "depend_domain": result.get('DependentArea'),
                            "belongProduct": result.get('BelongProduct'),
                            "productRoadmap": result.get('ProductRoadmap')
                        })
                else:
                    msg = response_json.get('code', {}).get('msg', 'Unknown error')
                    logger.error(f"RDC query failed for space '{rdc_space}', IDs {ids_in_group}. Reason: {msg}")
            else:
                logger.error(f"HTTP {response.status_code} when querying RDC space '{rdc_space}' for IDs {ids_in_group}")
        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error when querying RDC space '{rdc_space}' for IDs {ids_in_group}: {e}")
    return final_result


def build_RDC_new_body(workItems: Any, table: List[Dict[str, Any]], contacts: Dict[str, str]) -> Dict[str, Any]:
    filled_table = copy.deepcopy(table)
    val_2_key = {item["value"]: item["key"] for item in filled_table if isinstance(item["value"], str)}
    rdc_params_list = [{"key": val_2_key[c_key], "value": c_val} for c_key, c_val in contacts.items() if c_key in val_2_key]
    return {"workItems": workItems, "fields": rdc_params_list}


def update_RDC_by_key(rdc_params_list:list, employ_no: str, token: str):
    error_workItems = []
    for rdc_params in rdc_params_list:
        workItems = rdc_params.get("workItems", [])
        fields = rdc_params.get("fields", [])
        if not fields:
            fields = " "
        url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/batch_update"
        headers = {"X-Tenant-Id":"ZTE",
                  "X-Emp-No": employ_no,
                  "X-Auth-Value": token,
                  "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
                  "X-Lang-Id":"zh_CN",
                  "Content-Type":"application/json"
                   }
        body = build_RDC_new_body(workItems, TABLE, fields[0])
        response = requests.put(url, data=json.dumps(body), headers=headers)  
        if response.status_code == 200:
            response_json = response.json()
            if response_json["code"]["code"] != '0000':
                error_workItems.extend(workItems)
        else:
            error_workItems.extend(workItems)
    return error_workItems


def get_rdc_relation_id_dict(rdc_params: dict):
    rdcIdent_list = rdc_params.get("rdcIdent_list", [])
    linkRelationName = rdc_params.get("linkRelationName", "")
    relatedWorkItemTypeKey = rdc_params.get("relatedWorkItemTypeKey", "")
    employ_no = rdc_params.get("employ_no", "")
    url = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/relations/query_related_byTime"
    headers = {
        "X-Tenant-Id": "ZTE",
        "X-Emp-No": employ_no,
        "appcode": "d09fddc101a14bb3bfa0fbd02ed1932a",
        "X-Lang-Id": "zh_CN",
        "Content-Type": "application/json"
    }
    batch_size = 200
    relation_id_dict = defaultdict(list)
    for i in range(0, len(rdcIdent_list), batch_size):
        batch = rdcIdent_list[i:i + batch_size]
        body = {
            "workItemIds": batch,
            "linkRelationName": linkRelationName,
            "visible": True,
        }
        try:
            response = requests.post(url, data=json.dumps(body), headers=headers, timeout=30)
            if response.status_code == 200:
                response_json = response.json()
                result_list = response_json.get("bo", {}).get("items", [])
            else:
                logger.error(f"HTTP {response.status_code} when querying relations for batch: {batch}")
                result_list = []
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request failed for batch {batch}: {e}")
            result_list = []
        # 累积所有匹配的关系（支持多对一）
        if linkRelationName == "father":
            # father 类型：遍历所有结果，建立父子关系
            for result in result_list:
                related_id = result.get("relatedWorkItemId")
                source_id = result.get("workItemId")
                if related_id and source_id and source_id not in relation_id_dict[related_id]:
                    relation_id_dict[related_id].append(source_id)
        else:
            for result in result_list:
                if result.get("relatedWorkItemTypeKey") == relatedWorkItemTypeKey:
                    related_id = result.get("relatedWorkItemId")
                    source_id = result.get("workItemId")
                    if related_id and source_id and source_id not in relation_id_dict[related_id]:
                        relation_id_dict[related_id].append(source_id)
    # 转为普通 dict（可选，便于序列化）
    return dict(relation_id_dict)


# 测试调用
if __name__ == "__main__":
    print(11111, 22222)