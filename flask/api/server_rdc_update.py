import sqlite3
import html2text
import ast
import re
from typing import Set
from api_data import Rdc_list_get
from bs4 import BeautifulSoup

def issue_update():
    print("issue_update")
    
    query_condition = [
        {
            "field": "System_WorkItemType",
            "leftGroup": 0,
            "logicalOperator": "",
            "operator": "=",
            "rightGroup": 0,
            "value": "chgRequest:OTNAG:变更请求"
        },
        {
            "field": "System_CreatedDate",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": ">=",
            "rightGroup": 0,
            "value": "2025-06-01"
        },
        {
            "field": "System_CreatedDate",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "<",
            "rightGroup": 0,
            "value": "2026-01-01"
        },
        {
            "field": "System_Id",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "!=",
            "rightGroup": 0,
            "value": "null"
        }
    ]
    
    query_items = [
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
            "width": "",
            "isAscending": "true"
        },
        {
            "key": "System_WorkItemType",
            "name": "工作项类型",
            "type": "workItemType",
            "width": ""
        },
        {
            "key": "System_State",
            "name": "状态",
            "type": "state",
            "width": ""
        },
        {
            "key": "System_Description_html",
            "name": "描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "ChangeMajorType",
            "name": "变更大类",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectLevel",
            "name": "缺陷等级",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectSource",
            "name": "缺陷来源",
            "type": "string",
            "width": ""
        },
        {
            "key": "DiscoveryActivity",
            "name": "发现活动",
            "type": "string",
            "width": ""
        },
        {
            "key": "DiscoverWay",
            "name": "发现方法",
            "type": "string",
            "width": ""
        },
        {
            "key": "iChangeDiscoveryVersion",
            "name": "iChange发现版本号",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "System_CreatedDate",
            "name": "创建时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "ClosedTime",
            "name": "已关闭日期",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "BelongProduct",
            "name": "所属产品",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "BelongProject",
            "name": "所属项目",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "System_AreaPath",
            "name": "领域",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "Team",
            "name": "团队",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "IntroductedBy",
            "name": "引入者",
            "type": "user",
            "width": ""
        },
        {
            "key": "ImportResponserDept",
            "name": "引入责任部门",
            "type": "string",
            "width": ""
        },
        {
            "key": "Discoverer",
            "name": "发现人",
            "type": "user",
            "width": ""
        },
        {
            "key": "DiscovererDept",
            "name": "发现人部门",
            "type": "string",
            "width": ""
        }
    ]

    items_map = {
        "标识": "标识",
        "标题": "标题",
        "描述": "描述",
        "状态": "状态",

        "变更大类": "变更大类",
        "缺陷等级": "缺陷等级",
        "缺陷来源": "缺陷来源",
        "发现活动": "发现活动",
        "发现方法": "发现方法",
        "iChange发现版本号": "发现版本",
        "创建时间": "创建时间",
        "已关闭日期": "关闭时间",

        "所属产品": "所属产品",
        "所属项目": "所属项目",
        "领域": "领域",
        "团队": "团队",

        "引入者": "引入人",
        "引入责任部门": "引入人部门",

        "发现人": "发现人",
        "发现人部门": "发现人部门",
    }

    # 获取issue数据
    issue_list = Rdc_list_get(query_condition, query_items, items_map, 10000)
    
    # 处理数据并更新到数据库
    if not issue_list:
        print("没有需要更新的数据")
        return

    # 数据库连接与操作
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect('../data/sql_rdc.db')
        cursor = conn.cursor()
        
        # 检查数据库中是否存在issue表，如果不存在则创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issue'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # 创建issue表
            create_table_sql = '''
            CREATE TABLE issue (
                "标识" TEXT PRIMARY KEY,
                "标题" TEXT,
                "描述" TEXT,
                "状态" TEXT,
            )
            '''
            cursor.execute(create_table_sql)
            print("已创建issue表")
        
        # 获取数据库表中实际存在的字段
        cursor.execute("PRAGMA table_info(issue)")
        table_fields: Set[str] = {row[1] for row in cursor.fetchall()}
        print(f"数据库表中存在的字段: {sorted(table_fields)}")
        
        # 从数据中获取所有字段名，并筛选出数据库中存在的字段
        if not issue_list:
            print("没有数据可处理")
            return
            
        data_fields = list(issue_list[0].keys())
        # 筛选出数据库中存在的字段
        existing_fields = [field for field in data_fields if field in table_fields]
        
        # 检查主键是否存在
        if "标识" not in existing_fields:
            print("数据库表中缺少主键字段'标识'，无法更新数据库")
            return
            
        # 找出数据中有但数据库中没有的字段，并提示
        missing_fields = [field for field in data_fields if field not in table_fields]
        if missing_fields:
            print(f"以下字段在数据库中不存在，将被跳过: {missing_fields}")
        
        # 构建UPSERT SQL语句，只包含数据库中存在的字段
        non_primary_fields = [f for f in existing_fields if f != "标识"]
        insert_fields = ", ".join([f'"{f}"' for f in existing_fields])
        placeholders = ", ".join(["?" for _ in existing_fields])
        update_clause = ", ".join([f'"{f}" = excluded."{f}"' for f in non_primary_fields])
        
        sql = f"""
        INSERT INTO "issue" ({insert_fields})
        VALUES ({placeholders})
        ON CONFLICT("标识") DO UPDATE SET {update_clause}
        """
        
        # 处理数据
        total = len(issue_list)
        updated = 0
        inserted = 0
        
        for i, item in enumerate(issue_list, 1):
            # 只提取数据库中存在的字段的值
            values = [item.get(field) for field in existing_fields]
            
            try:
                cursor.execute(sql, values)
                # 判断是插入还是更新
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                
                # 每100条提交一次
                if i % 100 == 0:
                    conn.commit()
                    print(f"已处理 {i}/{total} 条数据（插入: {inserted}, 更新: {updated}）")
            
            except sqlite3.Error as e:
                print(f"处理第 {i} 条数据时出错: {e}")
                print(f"出错数据: {item}")
                conn.rollback()
        
        # 提交剩余数据
        conn.commit()
        print(f"数据处理完成 - 总计: {total}, 插入: {inserted}, 更新: {updated}")
        if missing_fields:
            print(f"已跳过 {len(missing_fields)} 个数据库中不存在的字段")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return issue_list

def review_update():
    print("review_update")
  
    query_condition = [
        {   
            "field": "System_WorkItemType",
            "leftGroup": 0,
            "logicalOperator": "",
            "operator": "=",
            "rightGroup": 0,
            "value": "EcFaultReview:OTNAG:故障复盘,BugReview:OTNAG:故障复盘"
        },
        {
            "field": "ChangeSubmissionTime",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": ">=",
            "rightGroup": 0,
            "value": "2023-01-01"
        },
        {
            "field": "ProblemAttribution",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "in",
            "rightGroup": 0,
            "value": "L0领域,L2/L3领域,支撑领域,L1领域,智能控制领域"
        },
        {
            "field": "DiscoveryActivity",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "in",
            "rightGroup": 0,
            "value": "集成测试,领域测试,系统测试,安全功能测试,性能容量测试,方案测试,工程模拟测试,验证阶段新需求测试,综合场景测试,验证阶段可靠性测试"
        }
    ]

    query_items = [
        {
            "key": "System_Id",
            "name": "标识",
            "type": "workItemNo",
            "width": "278"
        },
        {
            "key": "System_Title",
            "name": "标题",
            "type": "string",
            "width": ""
        },
        {
            "key": "System_WorkItemType",
            "name": "工作项类型",
            "type": "workItemType",
            "width": ""
        },
        {
            "key": "MasterArea",
            "name": "主领域",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroductionLink",
            "name": "故障引入环节",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectSource",
            "name": "缺陷来源",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroduceReason1",
            "name": "故障引入一级原因",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultIntroduceReason2",
            "name": "故障引入二级原因",
            "type": "string",
            "width": ""
        },
        {
            "key": "ProblemAttribution",
            "name": "问题归属",
            "type": "string",
            "width": ""
        },
        {
            "key": "Component",
            "name": "组件",
            "type": "string",
            "width": ""
        },
        {
            "key": "FunctionModuleLevel1",
            "name": "功能模块层级1",
            "type": "string",
            "width": ""
        },
        {
            "key": "FunctionModuleLevel2",
            "name": "功能模块层级2",
            "type": "string",
            "width": ""
        },
        {
            "key": "IsTailorable",
            "name": "是否可裁剪",
            "type": "boolean",
            "width": ""
        },
        {
            "key": "IdentificationPhase",
            "name": "识别阶段",
            "type": "string",
            "width": ""
        },
        {
            "key": "CodeWalkThroughState",
            "name": "代码走查状态",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReason2_UnitTest",
            "name": "故障泄露二级原因（单元测试）",
            "type": "string",
            "width": ""
        },
        {
            "key": "SimulationTestResult",
            "name": "仿真测试结果",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReasonDetails_FunctionTest",
            "name": "故障泄露原因描述（功能测试）",
            "type": "string",
            "width": ""
        },
        {
            "key": "DiscoveryActivity",
            "name": "发现活动",
            "type": "string",
            "width": ""
        },
        {
            "key": "DevelopmentOwner",
            "name": "开发负责人",
            "type": "user",
            "width": ""
        },
        {
            "key": "ChangeSubmissionTime",
            "name": "变更提交时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "TaskClosedTime",
            "name": "任务关闭日期",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "Countersigner1",
            "name": "会签人1",
            "type": "user",
            "width": ""
        },
        {
            "key": "SolutionDescription_html",
            "name": "解决方案描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "NeedCustomCatalog",
            "name": "需要自定义分类",
            "type": "string",
            "width": ""
        },
        {
            "key": "TaskSubmitTime",
            "name": "任务提交时间",
            "type": "dateTime",
            "width": ""
        },
        {
            "key": "sj_creattest",
            "name": "是否触发创建自测报告",
            "type": "string",
            "width": ""
        },
        {
            "key": "OtherChangeReason",
            "name": "其他原因说明",
            "type": "string",
            "width": ""
        },
        {
            "key": "DefectLocationMode",
            "name": "缺陷定位方式",
            "type": "string",
            "width": ""
        },
        {
            "key": "IsKeyPara",
            "name": "是否关键字",
            "type": "boolean",
            "width": ""
        },
        {
            "key": "FaultIntroPoint_Ba",
            "name": "故障引入点（方案）",
            "type": "string",
            "width": ""
        },
        {
            "key": "TestMethod",
            "name": "测试方法",
            "type": "string",
            "width": ""
        },
        {
            "key": "ShowCaseUrl",
            "name": "ShowCase链接",
            "type": "string",
            "width": ""
        },
        {
            "key": "AuditDuration",
            "name": "审核时长",
            "type": "string",
            "width": ""
        },
        {
            "key": "Progress_html",
            "name": "进展",
            "type": "html",
            "width": ""
        },
        {
            "key": "WorkItemProgressOfMicroElectronics_html",
            "name": "微院工作项进展",
            "type": "html",
            "width": ""
        },
        {
            "key": "System_Description_html",
            "name": "描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "ControlLevel",
            "name": "控制级别",
            "type": "string",
            "width": ""
        },
        {
            "key": "FaultLinksReason1_SystemTestDesign",
            "name": "故障泄露一级原因（系统测试_测试设计）",
            "type": "string",
            "width": ""
        }
    ]

    review_map = {
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
        "控制级别": "故障控制点根因一级分类IT",
        "故障泄露一级原因（系统测试_测试设计）": "故障控制点根因二级分类IT",
        "故障引入点（方案）": "控制点复盘状态",

        "进展": "引入点改进举措",
        "微院工作项进展": "控制点改进举措"
    }

    # 获取review数据
    review_list = Rdc_list_get(query_condition, query_items, review_map, 10000)
    
    # 处理数据并更新到数据库
    if not review_list:
        print("没有需要更新的数据")
        return

    # 数据库连接与操作
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect('../data/sql_rdc.db')
        cursor = conn.cursor()
        
        # 获取数据库表中实际存在的字段
        cursor.execute("PRAGMA table_info(review)")
        table_fields: Set[str] = {row[1] for row in cursor.fetchall()}
        print(f"数据库表中存在的字段: {sorted(table_fields)}")
        
        # 从数据中获取所有字段名，并筛选出数据库中存在的字段
        if not review_list:
            print("没有数据可处理")
            return
            
        data_fields = list(review_list[0].keys())
        # 筛选出数据库中存在的字段
        existing_fields = [field for field in data_fields if field in table_fields]
        
        # 检查主键是否存在
        if "标识" not in existing_fields:
            print("数据库表中缺少主键字段'标识'，无法更新数据库")
            return
            
        # 找出数据中有但数据库中没有的字段，并提示
        missing_fields = [field for field in data_fields if field not in table_fields]
        if missing_fields:
            print(f"以下字段在数据库中不存在，将被跳过: {missing_fields}")
        
        # 构建UPSERT SQL语句，只包含数据库中存在的字段
        non_primary_fields = [f for f in existing_fields if f != "标识"]
        insert_fields = ", ".join([f'"{f}"' for f in existing_fields])
        placeholders = ", ".join(["?" for _ in existing_fields])
        update_clause = ", ".join([f'"{f}" = excluded."{f}"' for f in non_primary_fields])
        
        sql = f"""
        INSERT INTO "review" ({insert_fields})
        VALUES ({placeholders})
        ON CONFLICT("标识") DO UPDATE SET {update_clause}
        """
        
        # 处理数据
        total = len(review_list)
        updated = 0
        inserted = 0
        
        for i, item in enumerate(review_list, 1):
            # 只提取数据库中存在的字段的值
            values = [item.get(field) for field in existing_fields]
            
            try:
                cursor.execute(sql, values)
                # 判断是插入还是更新
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                
                # 每100条提交一次
                if i % 100 == 0:
                    conn.commit()
                    print(f"已处理 {i}/{total} 条数据（插入: {inserted}, 更新: {updated}）")
            
            except sqlite3.Error as e:
                print(f"处理第 {i} 条数据时出错: {e}")
                print(f"出错数据: {item}")
                conn.rollback()
        
        # 提交剩余数据
        conn.commit()
        print(f"数据处理完成 - 总计: {total}, 插入: {inserted}, 更新: {updated}")
        if missing_fields:
            print(f"已跳过 {len(missing_fields)} 个数据库中不存在的字段")
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return review_list


if __name__ == "__main__":
    # issue_update()
    # review_update()
    tasks_update()
