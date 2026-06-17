import requests
import socket
import json
import os
import hashlib
import datetime
import markdownify
import urllib3
# from log import daylogger

# 屏蔽告警
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def dict_merge(d1, d2):
    tmp_dict = dict()
    tmp_dict.update(d1)
    tmp_dict.update(d2)
    return tmp_dict


class RdcClient:

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://inone.zte.com.cn/"
        # self.api_key = api_key
        # self.user = user
        # self.passowrd = password
        self.loginsyscode = 'Portal'
        self.originsyscode = ''
        # token_dic = self.get_token()
        # self.X_Auth_Value = token_dic['other']['token']
        self.tenant_id = 'ZTE'

        self.headers = {
            'X-Tenant-Id': 'ZTE',
            'X-Emp-No': 'otnbranch',
            'X-Auth-Value': '592ac38421e1413789b6958ccd5d831a',
            'appcode': 'ZXONE-19700-autobuild',
            'X-Lang-Id': 'zh_CN'
        }

    def __is_response_ok(self, response):
        if response.status_code != 200:
            daylogger.info('*****%s'%'HTTP Response %s: %s' % (response.status_code, response.text))
            return False
        result = response.json()
        if type(result['code']) == dict and result['code']['code'] != '0000':
            daylogger.info('*****%s'%'Server Response %s: %s'%(result["code"]["code"], result["code"]["msg"]))
            return False
        if type(result['code']) == str and result['code'] != '0000':
            daylogger.info('*****%s'%'Server Response %s'%result["code"])
            return False
        return True

    def __get(self, url, params={}, headers={}):
        url = self.base_url + url
        return self.session.get(url, json=params, headers=dict_merge(self.headers, headers), verify=False, timeout=30)

    def __delete(self, url, params={}, headers={}):
        url = self.base_url + url
        return self.session.delete(url, json=params, headers=dict_merge(self.headers, headers), verify=False, timeout=30)

    def __post(self, url, params={}, headers={}):
        url = self.base_url + url
        return self.session.post(url, json=params, headers=dict_merge(self.headers, headers), verify=False, timeout=30)

    def __put(self, url, params={}, headers={}):
        url = self.base_url + url
        return self.session.put(url, json=params, headers=dict_merge(self.headers, headers), verify=False, timeout=30)

    def create_workitem(self, workItemTypeKey, workspaceKey, fieldlist):
        url = f"ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/{workspaceKey}/work_items"
        params = {
            "workItemTypeKey": workItemTypeKey,
            "fields": fieldlist
        }
        response = self.__post(url, params)
        if self.__is_response_ok(response):
            content = response.json()['bo']
            return True, content
        else:
            return False, ""

    def create_selfdata(self, workItemTypeKey, workspaceKey, workItemId, nodeKey, selfbuildlist):
        url = "ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/tableComponent/selfBuildData"
        params = {
            "nodeKey": nodeKey,
            "selfBuildDataVOList": selfbuildlist,
            "workItemTypeKey": workItemTypeKey,
            "workspaceKey": workspaceKey,
            "tenantKey": self.tenant_id,
            "workItemId": workItemId
        }
        response = self.__post(url, params)
        if self.__is_response_ok(response):
            content = response.json()['bo']
            return True, content
        else:
            return False, ""

    def query_workitem(self, workspaceKey, workitemIds, workItemTypeKey):
        url = f"ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/{workspaceKey}/work_items/{workitemIds}?workItemTypeKey={workItemTypeKey}"

        params = {}
        response = self.__get(url, params)
        if self.__is_response_ok(response):
            content = response.json()['bo']
            return True, content
        else:
            return False, ""

    def modify_workitems(self, workItemTypeKey, workspaceKey, workItemId, fieldlist):
        url = f'ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/update/{workItemId}'
        params = {
            # "workItemTypeKey": workItemTypeKey,
            "fields": fieldlist
        }
        response = self.__put(url, params)
        if self.__is_response_ok(response):
            content = response.json()['bo']
            return True, content
        else:
            return False, ""

    def change_person(self, workItemId, workspaceKey, workItemTypeKey, useID):
        url = f'ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/workspaces/{workspaceKey}/work_items/updateWorkItems/transfer'
        params = {
                "workItems": [
                    {
                        "id": workItemId,
                        "workspaceKey": workspaceKey,
                        "workItemTypeKey": workItemTypeKey
                }],
                "fields": [
                    {
                        "key": "System_AssignedTo",
                        "value": [{
                            "userId": useID,
                        }]
                    }
                ]
        }

        response = self.__put(url, params)
        if self.__is_response_ok(response):
            content = response.json()['bo']
            return True, content
        else:
            return False, ""

    def query_work_items(self, WorkspaceKey, field, sourceClauses, **kwargs):
        url = 'https://rdcloud.zte.com.cn/api/wic/workspaces/%s/queries/after_work_items' % WorkspaceKey
        url = url + "?apikey=" + "7XAHNLVl916xQxDeoXiOg4hUjLeAMia1"

        result = []
        # WorkspaceKey, field, q_type, related_type, sourceClauses, targetClauses
        body = self.create_body(WorkspaceKey, field, sourceClauses, **kwargs)
        headers = dict({
            "X-Tenant-Id": "ZTE",
            "X-Emp-No": "autoTools",
            "Content-Type": "application/json"
        })

        curPage = 1
        while True:
            response = requests.session().post(
                url,
                headers=headers,
                data=json.dumps(body),
                verify=False, timeout=2000).json()
            res = response['bo']['result']['items']
            if res == None:
                break
            result.extend(response['bo']['result']['items'])
            totalRow = int(response['bo']['result']['totalRow'])
            pageSize = int(response['bo']['result']['pageSize'])

            totalPage = totalRow // pageSize + 1
            if curPage >= totalPage or len(response['bo']['result']['items']) == 0:
                break
            else:
                curPage += 1
                body["searchAfter"] = res[-1]["sortValues"]

        # with open("z.json", "w") as f:
        #     f.write(json.dumps(result))
        return result

    def create_body(self, WorkspaceKey, selectItems, sourceClauses=[], **kwargs):
        # 存在关联关系的
        #
        # 关联类型为：直接关联，不跨工作区
        # 关联选项：有匹配关系的工作项
        # 关联类型：被测试、
        # 关联类型 "relatedType"  列表
        # 相关    "linkRelatedType_1"
        # 父级    "linkRelatedType_2"
        # 子级    "linkRelatedType_3"
        # 测试    "linkRelatedType_4"
        # 被测试  "linkRelatedType_5"

        # 查询过滤条件字段说明
        # {
        #     "field": "System_WorkItemType",  过滤字段
        #     "leftGroup": 0,   sql左括号
        #     "logicalOperator": "",    与其他字段的操作逻辑   and or
        #     "operator": "=",  操作类型
        #     "rightGroup": 0,  右括号
        #     "value": "PR:OTNAG:产品需求"  过滤的条件
        # }
        q_type = kwargs.get("q_type", "1")
        related_type = kwargs.get("related_type", [])
        targetClauses = kwargs.get("targetClauses", [])
        if q_type == "2":
            q = {
                "relatedOptions": "linksOneHopMustContain",
                "treeOptions": "top",
                "type": "oneHop",
                "relatedType": related_type
            }
        else:
            q = {
                "type": "flat",
                "relatedType": []
            }

        queryCondition = {
            "depth": 0,
            "removeTop": True,
            "sourceClauses": sourceClauses,
            "targetClauses": targetClauses
        }
        queryCondition.update(q)

        maxSize = 2000
        body = {
            "pageSize": maxSize,
            "sortValue": True,

            "conditions": [
                "System_WorkspaceKey='%s'" % WorkspaceKey
            ],
            "queryCondition": queryCondition,
            "resultType": "flat",
            "selectItems": [{"key": field} for field in selectItems],
            "sortItems": [
                {
                    "isAscending": False,
                    "key": "System_Id"
                }
            ],
            "tenantKey": self.tenant_id,
            "workspaceKey": "%s" % WorkspaceKey
        }

        return body

    def items_format(self, fields=[], items=[]):
        rdc_items = []
        save_field = list(fields)
        for rdc in items:
            try:
                _item = {}
                for field in save_field:
                    field_value = rdc.get(field, '')
                    if type(field_value) == dict:
                        field_value = field_value.get("name", '')
                    _item[field] = field_value

                # 处理子级
                _item["children"] = []
                children = rdc.get("children", [])
                for _ch in children:
                    _ch_dict = {}
                    for ch_field in save_field:
                        field_value = _ch.get(ch_field, '')
                        if type(field_value) == dict:
                            field_value = field_value.get("name", '')
                        _ch_dict[ch_field] = field_value
                    _item["children"].append(_ch_dict)

                rdc_items.append(_item)
            except:
                print("Process Error :", rdc.get("System_Id"))
                pass
        return rdc_items

    # def get_auth_value(self):
    #     url = 'https://uactest.zte.com.cn:5555/zte-sec-uac-iportalbff/external/appadmin/keys/auth.serv'
    #     params = {
    #         "accessKey": "79a3f533-5b90-44ad-a95e-56efc32c67ba",
    #         "secretKey": "0IYX4Abf7UZFpuYMTh4V9bQZs1yhphK4mCEvEAKDFeolQbHgaolbRkMTqR7iE8AqSrUnp0jjC+jW0Z61ONbZOA=="
    #     }
    #     head_admin = {
    #         'X-Auth-Value': "",
    #         'X-Tenant-Id': "10001",
    #         'X-App-Id': "A1108424020394549248",
    #         'X-Itp-Value': 'accessKey=230788290775en3ajrtfww3t687nxeml',
    #         'Content-Type': 'application/json',
    #     }
    #     response = self.__post(url, params, head_admin)
    #     if self.__is_response_ok(response):
    #         content = response.json()['bo']
    #         return True, content
    #     else:
    #         return False, ""

def Get_rdc(rdc):
    Rdcclient = RdcClient()
    templist = [
        {
            "key": "System_State",
            "value": u'已锁定'
        },
    ]
    res = Rdcclient.query_workitem('OTNAG', "OTNAG-1496761", 'BugReview')
    formatted = json.dumps(res[1], indent=4, ensure_ascii=False)  # 缩进4空格，支持中文
 
    # 将格式化后的内容写入 text.md 文件
    with open("text.json", "w", encoding="utf-8") as f:
        f.write(formatted)

    jsondata = json.loads(formatted)
    # markdown = markdownify.markdownify(jsondata["items"][0]['fields'][170]['persistentValue'])
    # print(markdown)

    # item = jsondata["items"][0]['fields'][170]
    # item = json.dumps(item, indent=4, ensure_ascii=False)  # 缩进4空格，支持中文

    # 白名单：你想保留的 label 值
    whitelist_labels = {"引入点所属领域", "引入点归属团队", "引入来源", "技术根因分析"}  # 可以按需添加更多

    # 原始数据
    original_fields = jsondata["items"][0]['fields']

    # 只保留 label 和 value 字段
    new_fields = [
        {
            "label": item.get("label"),
            "value": item.get("value")
        }
        for item in original_fields
        # if item.get("label") in whitelist_labels
        if item.get("value") not in (None, '', ' ', False)  # 过滤掉空值，包括 None、空字符串等
    ]

    # 打印新的 fields 的 JSON 格式内容
    # print(json.dumps(new_fields, indent=4, ensure_ascii=False))

    # 构建 Markdown 表格
    markdown_table = "| 序号 | Label | Value |\n"
    markdown_table += "|------|-------|-------|\n"

    for idx, item in enumerate(new_fields, start=1):
        label = item.get("label", "")
        value = item.get("value", "")
        markdown_table += f"| {idx} | {label} | {value} |\n"

    # 输出结果
    print(markdown_table)




if __name__ == '__main__':
    Rdcclient = RdcClient()
    templist = [
        {
            "key": "System_State",
            "value": u'已锁定'
        },
    ]
    res = Rdcclient.query_workitem('OTNAG', "OTNAG-1496761", 'BugReview')
    formatted = json.dumps(res[1], indent=4, ensure_ascii=False)  # 缩进4空格，支持中文
 
    # 将格式化后的内容写入 text.md 文件
    with open("text.json", "w", encoding="utf-8") as f:
        f.write(formatted)

    jsondata = json.loads(formatted)
    # markdown = markdownify.markdownify(jsondata["items"][0]['fields'][170]['persistentValue'])
    # print(markdown)

    # item = jsondata["items"][0]['fields'][170]
    # item = json.dumps(item, indent=4, ensure_ascii=False)  # 缩进4空格，支持中文

    # 白名单：你想保留的 label 值
    whitelist_labels = {"引入点所属领域", "引入点归属团队", "引入来源", "技术根因分析"}  # 可以按需添加更多

    # 原始数据
    original_fields = jsondata["items"][0]['fields']

    # 只保留 label 和 value 字段
    new_fields = [
        {
            "label": item.get("label"),
            "value": item.get("value")
        }
        for item in original_fields
        # if item.get("label") in whitelist_labels
        if item.get("value") not in (None, '', ' ', False)  # 过滤掉空值，包括 None、空字符串等
    ]

    # 打印新的 fields 的 JSON 格式内容
    # print(json.dumps(new_fields, indent=4, ensure_ascii=False))

    # 构建 Markdown 表格
    markdown_table = "| 序号 | Label | Value |\n"
    markdown_table += "|------|-------|-------|\n"

    for idx, item in enumerate(new_fields, start=1):
        label = item.get("label", "")
        value = item.get("value", "")
        markdown_table += f"| {idx} | {label} | {value} |\n"

    # 输出结果
    print(markdown_table)

