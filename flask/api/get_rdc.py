#!/usr/bin/env python3
# coding:utf-8
__author__ = "wanlei"

import re
import os
import ast
import json
import sqlite3
import requests
import html2text
import markdown
import pandas as pd
from pathlib import Path


USER_ID = 'GZFP-OTN'
WORK_SPACE = 'OTNAG'
API_KEY = 'txhD6JifwPDwwoNHj5WPist7jhpLKOZ7'
X_Auth_Value = '86d3d61a3e0f5944a09fb5c263eded6b'
RDC_X_Auth_Value = '26b50aeb387744a5982a965c8886339e'


class DataSyncFromRDC(object):
    def __init__(self, user_id="10154505", token=X_Auth_Value):
        self._user_id = user_id
        self._token = token
        # self._outfield_faults_list = []
        self._header_dict = {
            'Content-Type': 'application/json',
            'X-Emp-No': user_id,
            'X-Api-Key': API_KEY,
            'X-Auth-Value': token,
            "X-Tenant-Id": "10001",
            'X-Lang-Id': 'zh_CN',
        }

    def get_item_type(self, item_id):
        # 从item_id中提取工作区信息，例如OTNAG-1234567中的OTNAG是工作区
        parts = item_id.split('-')
        if len(parts) < 2:
            print(f"无效的item_id格式: {item_id}")
            return None
        
        workspace_key = parts[0]
        
        # 使用指定的API接口，其中workItemTypeKey就是item_id
        url = f'https://rdcloud.zte.com.cn/api/wic/workspaces/{workspace_key}/work_item_types/{item_id}?apikey={API_KEY}'
        
        try:
            response = requests.get(url=url, headers=self._header_dict)
            if response.status_code != 200:
                print(f"获取工作项类型失败，状态码: {response.status_code}，响应内容: {response.text}")
                return None
            
            response_dict = json.loads(response.content)
            return response_dict
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None
    
    def get_data_detail(self, item_id):
        url1 = 'https://rdcloud.zte.com.cn/api/rdc/gateway/rest/work-item/detail?apikey={}'.format(API_KEY)
        body_data = {
            "workItemIds": [item_id],
            "expand": "relations"
        }
        response = requests.post(url=url1, json=body_data, headers=self._header_dict)

        try:
            response_dict = json.loads(response.content)
            
            # # 将response_dict保存到项目data目录下的文件
            # import os
            # from pathlib import Path
            
            # # 创建data目录（如果不存在）
            # data_dir = Path(__file__).parent.parent / 'data'
            # data_dir.mkdir(exist_ok=True)
            
            # # 保存到data目录下的文件
            # output_file_path = data_dir / f"response_dict_{item_id.replace('-', '_')}.json"
            # with open(output_file_path, 'w', encoding='utf-8') as f:
            #     json.dump(response_dict, f, ensure_ascii=False, indent=2)
            # print(f"Response dictionary saved to: {output_file_path}")
        except Exception as e:
            print(f'item_id:{item_id}, 无法解析的response: {response.content}, 失败提示: {str(e)}')
            return {}

        result_dict = {}

        bo = response_dict.get('bo')
        if not bo:
            print("response_dict['bo'] 不存在")
            return {}

        items = bo.get('items')
        if not items:
            print("response_dict['bo']['items'] 不存在或为空")
            return {}

        fields = items[0].get('fields')
        if not fields:
            print("response_dict['bo']['items'][0]['fields'] 不存在或为空")
            return {}

        for info in fields:
            label = info.get('label')
            value = info.get('value')
            if label and value:
                result_dict[label] = value

        return result_dict

    def get_data_detail_list(self, item_id_list):
        url1 = 'https://rdcloud.zte.com.cn/api/rdc/gateway/rest/work-item/detail?apikey={}'.format(API_KEY)
        body_data = {
            "workItemIds": item_id_list,
            "expand": "relations"
        }
        response = requests.post(url=url1, json=body_data, headers=self._header_dict)
        try:
            response_dict = json.loads(response.content)
        except Exception as e:
            print('item_id_list:{}, 无法解析的response: {}, 失败提示: {}'.format(item_id_list, response.content, str(e)))
            return []
        return response_dict.get('bo', {}).get('items', [])

    def query_work_items(self, query_conditions, query_items, page_size=10000):
        url1 = f'https://rdcloud.zte.com.cn/api/wic/workspaces/{WORK_SPACE}/queries/query_work_items?apikey={API_KEY}'
        body_data = {
            "appCode": "",
            "appendDomainImg": False,
            "createFrom": "ZXRDCloud",
            "createTime": "2025-06-07T00:31:39.188Z",
            "crossWorkspace": False,
            "crossWorkspaceAccessList": [],
            "crossWorkspaceKeyMapping": {
                "filter": []
            },
            "disable": False,
            "filterItems": [],
            "flowManager": True,
            "id": "6843886b1f809626be8ea5f6",
            "lastUpdateBy": "陈雷10171727",
            "lastUpdateTime": "2025-06-07T00:31:39.188Z",
            "queryCondition": {
                "depth": 0,
                "relatedOptions": "linksOneHopMustContain",
                "relatedType": [],
                "removeTop": False,
                "sourceClauses": query_conditions,
                "targetClauses": [],
                "treeOptions": "top",
                "type": "flat"
            },
            "queryDraftFilter": "noDraft",
            "queryType": "filter",
            "resultType": "flat",
            "scrollId": "",
            "selectItems": query_items,
            "sortItems": [
                {
                    "isAscending": False,
                    "key": "ChangeSubmissionTime"
                }
            ],
            "teamId": "bdv_106024",
            "tenantKey": "ZTE",
            "userId": "10171727",
            "viewBackupId": "",
            "viewName": "0.0.1 故障复盘数1749292007530",
            "viewNameEn": "query_1749292006000_521",
            "viewNameZh": "0.0.1 故障复盘数1749292007530",
            "viewType": "public",
            "workItemTypeKeys": [],
            "workspaceKey": "OTNAG",
            "pageNo": 1,
            "pageSize": page_size,
            "appendParams": {}
        }
        response = requests.post(url=url1, json=body_data, headers=self._header_dict)
        try:
            response_dict = json.loads(response.content)
        except Exception as e:
            print('无法解析的response: {}, 失败提示: {}'.format(response.content, str(e)))
            return {}
        return response_dict

    def update_work_item(self, workItemId, updata_dict):
        url = f'https://rdcloud.zte.com.cn/api/wic/v1/work_items/update/{workItemId}?apikey={API_KEY}'
        response = None
        try:
            response = requests.put(url=url, json=updata_dict, headers=self._header_dict)
            if response.status_code != 200:
                print(f"API请求失败，状态码: {response.status_code}，响应内容: {response.text}")
            else:
                print(f"API请求成功，状态码: {response.status_code}，响应内容: {response.text}")
        except Exception as e:
            print(f"请求异常: {str(e)}")
            if response:
                print('无法解析的response: {}, 失败提示: {}'.format(response.content, str(e)))
            else:
                print('请求失败，无响应内容，失败提示: {}'.format(str(e)))
        
        return response

    def add_tags(self, workItemId, tags):
        """
        为工作项添加标签
        :param workItemId: 工作项ID
        :param tags: 标签列表，可以是字符串列表或字典列表 [{'tag': '标签名'}]
        :return: API响应结果
        """
        # 获取当前工作项的详细信息以获取现有标签
        current_data = self.get_data_detail(workItemId)
        if not current_data:
            print(f"无法获取工作项 {workItemId} 的详细信息")
            return {}

        # 获取现有的标签
        existing_tags = current_data.get('标签', [])
        
        # 根据传入的标签格式，处理标签
        if isinstance(tags, str):
            # 如果tags是字符串，转换为字典格式
            new_tags = [{'tag': tags}]
        elif isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
            # 如果tags是字符串列表，转换为字典列表
            new_tags = [{'tag': tag} for tag in tags]
        elif isinstance(tags, list) and all(isinstance(tag, dict) for tag in tags):
            # 如果tags已经是字典列表，直接使用
            new_tags = tags
        else:
            print("标签格式不正确，请传入字符串、字符串列表或字典列表 [{'tag': '标签名'}]")
            return {}

        # 合并现有标签和新标签，避免重复
        existing_tag_names = set()
        for tag in existing_tags:
            if isinstance(tag, dict) and 'tag' in tag:
                existing_tag_names.add(tag['tag'])
        
        for new_tag in new_tags:
            if isinstance(new_tag, dict) and new_tag.get('tag') not in existing_tag_names:
                existing_tags.append(new_tag)

        # 构建更新字典
        updata_dict = {
            "fields": [
                {"key": "System_Tag", "value": existing_tags}
            ]
        }

        # 调用更新工作项的方法
        return self.update_work_item(workItemId, updata_dict)


def get_feature_name(item_id):
    rdc_obj = DataSyncFromRDC('10171727', X_Auth_Value)
    result_dict = rdc_obj.get_data_detail(item_id)
    if not result_dict:
        return False, "没有从rdc获取到特性名称"

    return True, result_dict.get('标题')

def get_rdc_filed(item_id):
    data_rdc = DataSyncFromRDC('10154505', X_Auth_Value)
    result_dict = data_rdc.get_data_detail(item_id)
    return result_dict




def convert_field_value(label, value):
    if value is None:
        return ""
    
    if label in ("引入者", "发现人", "指派给", "会签人1", "开发负责人", "需求分析负责人"):
        return value.get("nameDisplayLongZh", "") if isinstance(value, dict) else str(value)
    elif label in ("领域", "团队", "状态", "所属团队", "所属产品", "所属项目", "iChange发现版本号"):
        return value.get("name", "") if isinstance(value, dict) else str(value)
    elif label == "工作项类型":
        return value.get("workItemTypeRootNameZh", "") if isinstance(value, dict) else str(value)
    elif label == "故障引入环节":
        return ",".join(value) if isinstance(value, list) else str(value)
    elif label == "迭代":
        return value.get("value", "") if isinstance(value, dict) else str(value)
    elif isinstance(value, dict) and "baseDataValue" in value:
        base_data = value.get("baseDataValue", {})
        return base_data.get("label", base_data.get("name", ""))
    elif isinstance(value, str) and value.startswith("<"):
        try:
            h = html2text.HTML2Text()
            h.body_width = 0
            h.single_line_break = True
            h.wrap_links = False
            converted = h.handle(value).strip()
            return f"```\n{converted}\n```"
        except Exception:
            return value
    else:
        return value


def Get_rdc_markdown(id):
    data_rdc = DataSyncFromRDC('10154505', X_Auth_Value)
    result_dict = data_rdc.get_data_detail(id)
    
    # 转换特殊字段
    converted_dict = {}
    for label, value in result_dict.items():
        converted_dict[label] = convert_field_value(label, value)
    
    item_type = converted_dict.get("工作项类型", "")

    # 类型描述
    item_type_descript = {
        "故障复盘": "故障复盘的详细信息",
        "变更请求": "泄露故障的详细信息",
        "产品需求": "产品需求的详细信息",
        "市场需求": "市场需求的详细信息",
        "任务": "任务的详细信息",
        "用户故事": "用户故事的详细信息"
    }

    # 白名单：你想保留的 label 值
    whitelist_labels = {
        "故障复盘": [
            "主题",
            "工作项类型",
            "开发复盘负责人",
            "技术根因分析",
            "引入来源",
            "故障引入点根因一级分类",
            "故障引入点根因二级分类",
            "故障引入点根因三级分类",
            "故障引入gerrit入库链接",
            "引入点所属领域",
            "引入点归属团队",
            "一级特性",
            "二级特性",
            "引入点复盘状态",
            "自测无法拦截的原因",
            "最早可拦截阶段",
            "代码走查未拦截原因",
            "代码走查未拦截原因说明",
            "是否可通过补充代码UT/FT拦截",
            "是否可通过补充仿真FT拦截",
            "是否可通过补充硬件FT/流水线FT拦截",
            "故障定界定位方式",
            "是否需要复现定位或者占用环境定位",
            "定位时长",
            "控制点复盘状态",
            "引入点改进举措",
            "控制点改进举措"
        ],
        "变更请求": [
            "标题",
            "工作项类型",
            "所属产品",
            "所属项目",
            "状态",
            "缺陷等级",
            "领域",
            "所属团队",
            "描述",
            "变更大类",
            "发现版本",
            "引入者",
            "引入责任部门",
            "变更来源",
            "发现方法",
            "发现活动",
            "发现人",
            "发现人部门",
            "研究结论",
            "波及功能模块",
            "波及版本",
            "其他影响",
            "引入活动",
            "缺陷类型"
        ],
        "产品需求": [
            "标题",
            "工作项类型",
            "领域",
            "团队",
            "状态",
            "描述",
            "验收准则",
            "所属产品",
            "所属项目",
            "需求预规划",
            "需求用途",
            "需求类型",
            "需求类别",
            "市场需求标识",
            "需求实例化链接",
            "方案文档链接",
            "特性内容链接",
            "所属特性分类",
            "特性属性",
            "特性标识",
            "特性名称（中文）",
            "需求分析负责人",
            "评估结论（第一次）",
            "评估说明",
            "计划开始开发日期",
            "计划完成开发日期",
            "计划开始集成测试日期",
            "计划完成集成测试日期", 
            "计划开始系统测试日期",
            "计划完成系统测试日期",
            "计划交付日期",
            "开发负责人",
            "开发类型",
            "复用程度",
            "详设文档链接",
            "自测报告链接",
            "构建版本",
            "进展和风险描述",
            "AI辅助活动",
            "会签说明",
            "变更原因",
            "变更影响分析",
            "是否团队内交付",
            "验证方式",
            "验证团队",
            "验证阶段",
            "需求终结团队",
            "测试报告链接",
            "测试执行记录"
        ],
        "市场需求": [
            "标题",
            "工作项类型",
            "所属产品",
            "产品路标",
            "描述",
            "验收准则",
            "需求用途",
            "优先级",
            "客户",
            "iCenter实例化链接",
            "方案文档链接"
        ],
        "缺陷": [
            "标题",
            "工作项类型",
            "领域",
            "所属团队",
            "描述",
            "发现活动"
        ],
        "任务": [
            "标题",
            "工作项类型",
            "描述",
            "领域",
            "团队",
            "类别",
            "指派给",
            "创建时间"
        ],
        "用户故事": [
            "标题",
            "工作项类型",
            "指派给",
            "类型",
            "领域",
            "团队",
            "迭代",
            "描述",
            "验收准则",
            "引入来源",
            "优先级",
            "部件名称",
            "故事点",
            "预估工作量",
            "实际工作量",
            "计划交付日期",
            "所属产品",
            "所属项目",
            "需求预规划",
            "发布版本",
            "市场需求标识",
            "主交付团队",
            "其他交付团队"
        ]

    }

    # 获取当前类型对应的白名单列表
    labels_in_type = whitelist_labels.get(item_type, [])

    # 按照whitelist_labels的顺序过滤空值字段，并保持顺序
    ordered_dict = {}
    for label in labels_in_type:
        if label in converted_dict and converted_dict[label] not in (None, '', ' '):
            ordered_dict[label] = converted_dict[label]

    markdown_output = ""

    title = ordered_dict.get("主题", ordered_dict.get("标题", ""))
    descript = item_type_descript.get(item_type, "")

    if title:
        markdown_output += f"# {title}\n\n"

    # 为每个##标题添加编号
    section_number = 1
    for key, value in ordered_dict.items():
        markdown_output += f"## {section_number}. {key}\n\n{value}\n\n"
        section_number += 1

    return markdown_output

def Replace_rdc(question):
    """
    检查 question 的前 max_search_len (默认20) 个字符，
    是否含有类似 OTNAG-1234567 的编号：
      - 如果有，调用 Get_rdc_markdown() 替换第一个匹配项并返回新问题；
      - 如果没有，直接返回原问题。
    """

    # print(f"rdc-question: {question}")
    
    # 提取前 N 个字符用于判断
    prefix = question[:20]

    # 正则匹配类似 OTNAG-1234567 的字符串
    pattern = r'\bOTN[A-Z]{2}-\d+\b'
    match = re.search(pattern, prefix)

    if match:
        item_id = match.group(0)
        print(f"处理编号：{item_id}")
        replacement = Get_rdc_markdown(item_id)  # 获取替换内容

        # 只替换第一个出现的编号（限定在前 20 字符内）
        # 使用 replace 替换第一个匹配项
        question = question[:20].replace(item_id, replacement, 1) + question[20:]
    
    return question


# src_data_excel, dest_data_db， dest_data_db_table
def bug_table_update():
    try:
        # 配置部分
        excel_file = Path(__file__).parent.parent / 'data' / 'bug.xlsx'
        db_file = Path(__file__).parent.parent / 'data' / 'rdc.db'
        table_name = 'bug_table'

        # 步骤一：检查文件是否存在
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel 文件 {excel_file} 不存在")

        # 步骤二：读取 Excel 数据，并根据映射关系构建目标 DataFrame
        df_excel = pd.read_excel(excel_file)

        # 构建数据字典
        data = {}
        for excel_col, db_col in BUG_REVIEW_MAP.items():
            if excel_col in df_excel.columns:
                data[db_col] = df_excel[excel_col].astype(str).replace('nan', '')
            else:
                data[db_col] = [''] * len(df_excel)

        df = pd.DataFrame(data)

        # 步骤三：连接数据库并建表
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        columns_sql = ', '.join([f'"{col}" TEXT' for col in df.columns])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql}, PRIMARY KEY("标识"));'
        cursor.execute(create_table_sql)

        # 步骤四：同步数据到数据库（清空 + 全量插入）
        cursor.execute(f'DELETE FROM "{table_name}"')  # 清空原表

        # 构建插入语句
        values_placeholders = ', '.join(['?'] * len(df.columns))
        columns_str = ', '.join([f'"{col}"' for col in df.columns])
        insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({values_placeholders});'

        # 将 DataFrame 转换为元组列表进行插入
        records = df.to_records(index=False)
        cursor.executemany(insert_sql, records)

        conn.commit()
        conn.close()

        record_count = len(df)
        print(f"【成功】本次共更新了 {record_count} 条数据")

    except Exception as e:
        print(f"【错误】数据写入失败: {str(e)}")
        return False
        
def interactive_sql_shell(db_path='example.db'):
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"已连接到数据库 '{db_path}'。请输入SQL语句（以 ';' 结束），输入 exit; 或 quit; 退出。")

    while True:
        print("\nSQL> ", end="")  # 提示符
        lines = []

        while True:
            line = input("... ")  # 多行输入提示
            if not line:
                continue  # 忽略空行
            lines.append(line)
            full_input = " ".join(lines).strip()
            if full_input.endswith(";"):
                break

        sql = full_input
        if sql.lower() in ("exit;", "quit;"):
            print("正在退出...")
            break

        try:
            cursor.execute(sql)

            # 如果是 SELECT 查询，打印结果
            if sql.lower().lstrip().startswith("select"):
                rows = cursor.fetchall()
                print("查询结果：")
                for row in rows:
                    print(row)
            else:
                conn.commit()
                print("操作已执行。")
        except Exception as e:
            print(f"❌ SQL 执行错误：{e}")

    # 关闭连接
    conn.close()
    print("数据库连接已关闭。")

BUG_REVIEW_MAP = {
    "标识": "标识",
    "标题": "主题",
    "描述": "描述",
    "开发负责人": "开发复盘负责人",
    "缺陷/故障等级": "缺陷等级",
    "发现活动": "发现活动",
    "测试方法": "发现方法",
    "变更提交时间": "提交日期",
    "任务关闭日期": "关闭日期",

    "会签人1": "故障引入人",
    "问题归属": "引入点所属领域",
    "故障引入环节": "引入点所属团队",

    "解决方案描述": "技术根因分析",
    "缺陷来源": "引入来源",
    "故障引入一级原因": "故障引入点根因一级分类",
    "故障引入二级原因": "故障引入点根因二级分类",
    "需要自定义分类": "故障引入点根因三级分类",
    "ShowCase链接": "故障引入gerrit入库链接",
    "功能模块层级1": "一级特性",
    "功能模块层级2": "二级特性",
    "故障引入点（开发）": "引入点复盘状态",

    "识别阶段": "最早可拦截阶段",
    "是否触发创建自测报告": "自测无法拦截的原因",
    "代码走查状态": "代码走查未拦截原因",
    "其他原因说明": "代码走查未拦截原因说明",
    "故障泄露二级原因（单元测试）": "是否可通过补充代码UT/FT拦截",
    "仿真测试结果": "是否可通过补充仿真FT拦截",
    "故障泄露原因描述（功能测试）": "是否可通过补充硬件FT/流水线FT拦截",
    "缺陷定位方式": "故障定界定位方式",
    "是否关键字": "是否需要复现定位或者占用环境定位",
    "定位时长": "定位时长",
    "故障引入点（方案）": "控制点复盘状态",

    "进展": "引入点改进举措",
    "微院工作项进展": "控制点改进举措"
}

def extract_fields(data, query_items, query_items_convert, html_fields):
    """
    从给定的 data 字典中提取 query_items 中指定的字段，并应用特殊处理规则。
    
    功能包括：
    - 提取字段值
    - 特殊字段处理（用户、数组、字典）
    - HTML 转 Markdown
    - 字段名按 BUG_REVIEW_MAP 映射为新中文名
    
    :param data: 原始数据字典
    :param query_items: 指定要提取字段的配置列表
    :return: 提取后的字典，key 为映射后的新中文名，value 为处理后的字符串
    """
    # -------------------------------
    # 1. 列名映射表（旧中文名 -> 新中文名）
    # -------------------------------

    # -------------------------------
    # 2. 特殊处理规则
    # -------------------------------
    SPECIAL_PROCESS_RULES = {
        "引入者": lambda x: x.get("nameDisplayLongZh", "") if isinstance(x, dict) else "",
        "发现人": lambda x: x.get("nameDisplayLongZh", "") if isinstance(x, dict) else "",
        "指派给": lambda x: x.get("nameDisplayLongZh", "") if isinstance(x, dict) else "",
        "领域": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "团队": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "状态": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "所属团队": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "所属产品": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "所属项目": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "iChange发现版本号": lambda x: x.get("name", "") if isinstance(x, dict) else "",
        "会签人1": lambda x: x.get("nameDisplayLongZh", "") if isinstance(x, dict) else "",
        "开发负责人": lambda x: x.get("nameDisplayLongZh", "") if isinstance(x, dict) else "",
        "工作项类型": lambda x: x.get("workItemTypeRootNameZh", "") if isinstance(x, dict) else "",
        "故障引入环节": lambda x: ",".join(x) if isinstance(x, list) else "",
        "迭代": lambda x: x.get("value", "") if isinstance(x, dict) else "",
    }
    # 需要 HTML 转 Markdown 的字段
    # HTML_FIELDS = {"解决方案描述", "进展", "微院工作项进展"}
    # HTML_FIELDS = {"描述","解决方案描述","进展","微院工作项进展"}

    result = {}
    for item in query_items:
        key = item["key"]
        name = item["name"]

        # 从原始数据中获取值
        value = data.get(key)

        # --- 提前处理无效值 ---
        if value is None:
            value = ""
        elif not isinstance(value, str) and not isinstance(value, (dict, list)):
            value = str(value)

        # --- 特殊字段处理 ---
        if name in SPECIAL_PROCESS_RULES:
            rule_func = SPECIAL_PROCESS_RULES[name]
            value = rule_func(value) or ""
            # 确保结果是字符串
            if not isinstance(value, str):
                value = str(value)
            result[query_items_convert.get(name, name)] = value
            continue  # 特殊字段处理完直接进入下一循环

        # 在 HTML 转 Markdown 处理部分：
        if name in html_fields and isinstance(value, str):
            try:
                h = html2text.HTML2Text()
                h.body_width = 0 # 设置为0表示不限制行宽
                h.single_line_break = True      # 使用单换行
                h.wrap_links = False
                value = h.handle(value).strip()

                # 可选：进一步清理多余空行（保险）
                value = re.sub(r'\n{3,}', '\n\n', value)  # 多于2个连续换行 → 2个
            except Exception as e:
                print(f"Warning: HTML to Markdown failed on '{name}': {e}")
                value = ""
                
        # --- 兜底：确保 value 是字符串 ---
        if not isinstance(value, str):
            value = str(value)

        # -------------------------------
        # 3. 字段名映射：使用 BUG_REVIEW_MAP，未映射的保留原名
        # -------------------------------
        new_name = query_items_convert.get(name, name)  # 如果没有映射，使用原名
        result[new_name] = value    
    return result

def Rdc_list_get(query_conditions, query_items, query_items_convert, page_size=10000, html_fields = {"描述","解决方案描述","进展","微院工作项进展"}):
    """
    查询 RDC 工作项列表，并对每条数据应用 extract_fields 进行字段提取、HTML 转 Markdown 和字段名映射。
    
    :param query_condition: 查询条件（RQL）
    :param query_items: 字段配置列表，包含 key, name 等
    :param page_size: 分页大小，默认 10000（最大值）
    :return: 转换后的字典列表，每条数据字段已处理、已映射
    """
    # 假设 DataSyncFromRDC 是已定义的类
    data_rdc = DataSyncFromRDC('10171727', X_Auth_Value)
    
    # 查询原始数据
    response = data_rdc.query_work_items(query_conditions, query_items, page_size=page_size)
    
    # 解析响应
    items = response.get('bo', {}).get('result', {}).get('items', [])
    
    if not items:
        return []
    
    print(f"1、获取完成：记录{len(items)}条。")

    # 对每条数据应用 extract_fields 进行转换
    processed_list = []
    for item_data in items:
        try:
            # 调用你已实现的 extract_fields 函数
            converted_item = extract_fields(item_data, query_items, query_items_convert, html_fields)
            processed_list.append(converted_item)
        except Exception as e:
            # 可选：记录错误或跳过异常数据
            print(f"处理单据时出错（ID: {item_data.get('System_Id', 'Unknown')}）: {str(e)}")
            # 仍可选择跳过或保留原始数据用于排查
            continue
    
    print(f"2、转换完成。")
    return processed_list

def change_description_and_tags(content, workItemId, tag_str):
    fields_list = [{"key": "System_Description_html", "value": content}]
    data_rdc = DataSyncFromRDC()
    if tag_str:
        tag_list = ast.literal_eval(tag_str)
        if 'AI辅助生成' not in [item['tag'] for item in tag_list]:
            tag_list.append({'tag': 'AI辅助生成'})
            fields_list.append({"key": "System_Tag", "value": tag_list})
    else:
        tag_list = [{'tag': 'AI辅助生成'}]
        fields_list.append({"key": "System_Tag", "value": tag_list})
    updata_dict = {"fields": fields_list}
    data_rdc.update_work_item(workItemId, updata_dict)

def Rdc_fieldtype_get(item_id):
    data_rdc = DataSyncFromRDC()
    return data_rdc.get_item_type(item_id)

def Rdc_tags_add(item_id, tag_list):
    data_rdc = DataSyncFromRDC()
    return data_rdc.add_tags(item_id, tag_list)

RDC_FIELD_MAP = {
    "TASK":
    {
        "标题": "System_Title",
        "描述": "System_Description_html",
        "指派给": "System_AppointedTo",
    },
    "变更请求":
    {
        "期望解决日期": "ExpectedResolvedDate",
    },
    "市场需求":
    {
        "备注": "Remark_html",
        "会签说明": "CountersignatureReport_html",
        "变更原因": "ChangeReason_html",
        "变更影响分析": "ChangeImpactAnalysis_html"
    }
}

def Rdc_field_get(item_id):
    return Get_rdc_markdown(item_id)

def Rdc_field_set(item_id, field_dict):
    """
    更新RDC工作项的字段值
    :param item_id: 工作项ID
    :param field_dict: 字段字典，格式为 {field_name: field_value}
    :return: API响应的code字段
    """
    data_rdc = DataSyncFromRDC()
    
    fields_list = []
    
    for field_name, field_value in field_dict.items():
        # 在RDC_FIELD_MAP中查找对应的字段名
        actual_field_name = field_name # 默认使用原始字段名
        
        # 遍历RDC_FIELD_MAP中的所有工作项类型
        for item_type, field_map in RDC_FIELD_MAP.items():
            if field_name in field_map:
                actual_field_name = field_map[field_name]
                break
        
        fields_list.append({"key": actual_field_name, "value": field_value})
    
    response = data_rdc.update_work_item(item_id, {"fields": fields_list})
    
    # 解析响应并返回code字段
    if response is None:
        return None
    
    try:
        response_json = response.json()
        return response_json.get("code")
    except Exception as e:
        print(f"解析响应失败: {str(e)}")
        return None

def PR_ai_development(item_id, ai_content):
    """
    更新RDC工作项的会签说明字段，用于记录AI辅助内容
    :param item_id: RDC工作项ID
    :param ai_content: AI辅助记录内容，markdown格式
    :return: API响应结果
    """

    # 为RDC工作项添加标签
    Rdc_tags_add(item_id, [{'tag': 'AI辅助需求开发自动回填'}])

    # 将markdown格式的ai_content转换为html格式
    html_content = markdown.markdown(ai_content)
    
    # 构建字段更新字典
    field_dict = {
        "会签说明": html_content
    }
    
    # 调用Rdc_field_set函数更新字段
    result = Rdc_field_set(item_id, field_dict)
        
    return result

def PR_ai_change(item_id, change_impact_analysis):
    """
    回填变更影响分析到RDC工作项的对应字段上
    :param item_id: RDC工作项ID
    :param change_impact_analysis: 变更影响分析内容，markdown格式
    :return: API响应结果
    """
    
    # 为RDC工作项添加标签
    Rdc_tags_add(item_id, [{'tag': 'AI辅助需求变更自动回填'}])

    # 将markdown格式的内容转换为html格式
    html_change_impact_analysis = markdown.markdown(change_impact_analysis)
    
    # 构建字段更新字典
    field_dict = {
        "变更影响分析": html_change_impact_analysis
    }
    
    # 调用Rdc_field_set函数更新字段
    result = Rdc_field_set(item_id, field_dict)
        
    return result

if __name__ == '__main__':
    # result = get_apr_filed('OTNAG-1571776')
    # result = get_rdc_filed('OTNSW-697474')
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    # result = Rdc_tags_add("OTNAG-1571776", "测试标签")
    # result = Rdc_field_set("OTNAG-1571776", {"描述": "<p>hello world!</p>"})
    # field_dict = {
    #     "会签说明": "这是一条测试内容！",
    #     "变更原因": "测试原因",
    #     "变更影响分析": "测试分析"
    # }
    result = Rdc_field_get("OTNSW-747759")
    print(result)
    
    # result = Rdc_field_set("OTNAG-1606699", field_dict)
    # print(result)

    # result = Rdc_fieldtype_get("OTNAG-1571776")
    # print(result)

    # PR_ai_development("OTNAG-1606699", "# AI辅助工作详情\n\n## 工作概述\n该需求使用AI完成了大部分开发工作，具体包括代码生成、代码走查和验证等环节。\n\n## 具体工作内容\n\n### 1. AI生成\n- 使用AI生成了95%的代码\n- 大幅提升了开发效率\n\n### 2. AI走查  \n- 使用AI进行了全面的代码走查\n- 确保代码质量和规范性\n\n### 3. AI验证\n- 使用AI完成了全部验证工作\n- 保证功能正确性和稳定性\n\n## 总结\n通过AI辅助，本需求实现了高效的自动化开发流程。")
    # PR_ai_change("OTNAG-1606699", "变更影响分析")
