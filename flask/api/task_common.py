import sqlite3
import html2text
import ast
import re
from typing import Set
from get_rdc import Rdc_list_get
from bs4 import BeautifulSoup

def get_cell_content(tables, header):
    right_cell_text = ""
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            for i in range(len(cells)):
                cell = cells[i]
                cell_text = cell.get_text(strip=True)
                if cell_text == header:
                    if i + 1 < len(cells):
                        right_cell = cells[i + 1]
                        right_cell_text = right_cell.get_text(strip=True).strip()
                    break
    return right_cell_text

def tasks_update():
    query_condition = [
        {
            "field": "System_WorkItemType",
            "leftGroup": 0,
            "logicalOperator": "",
            "operator": "=",
            "rightGroup": 0,
            "value": "Task:OTNAG:任务"
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
            "field": "System_Id",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "!=",
            "rightGroup": 0,
            "value": "null"
        },
        {
            "field": "System_State",
            "leftGroup": 0,
            "logicalOperator": "AND",
            "operator": "in",
            "rightGroup": 0,
            "value": "Active,Closed,New"
        },
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
            "key": "System_Description_html",
            "name": "描述",
            "type": "html",
            "width": ""
        },
        {
            "key": "System_State",
            "name": "状态",
            "type": "state",
            "width": ""
        },
        {
            "key": "System_AppointedTo",
            "name": "指派给",
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
            "key": "System_AreaPath",
            "name": "领域",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "System_Tag",
            "name": "标签",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "System_IterationPath",
            "name": "迭代",
            "type": "advancedData",
            "width": ""
        },
        {
            "key": "MinorCategory",
            "name": "子类",
            "type": "string",
            "width": ""
        }
    ]


    review_map = {
        "标识": "标识",
        "标题": "标题",
        "描述": "描述",
        "状态": "状态",
        "指派给": "指派给",
        "领域": "领域",
        "团队": "团队",
        "标签": "标签",
        "迭代": "迭代",
        "子类": "子类"
    }

    # 获取review数据
    review_list = Rdc_list_get(query_condition, query_items, review_map, 10000, {})
    for i, item in enumerate(review_list):
        if item["团队"] == 'L2-超体' or item["团队"] == 'L2-全能':
            item["团队"] = 'L2-超能'
        if item["团队"] == 'L2-追风':
            item["团队"] = 'L2-集结号'
        if item["标签"]:
            tag_list = ast.literal_eval(item["标签"])
            if 'AI辅助生成' in [item['tag'] for item in tag_list]:
                item["是否AI生成"] = "是"
                soup = BeautifulSoup(item["描述"], 'lxml')
                tables = soup.find_all('table')
                if len(tables) > 0:
                    ai_output = get_cell_content(tables, "AI输出")
                    ai_output = re.sub(r'/\*.*?\*/', '', ai_output, flags=re.DOTALL)
                    review_list[i]["生成代码行数"] = str(len(ai_output.split("\n")))
                    review_list[i]['波及组件'] = get_cell_content(tables, "波及组件")
                else:
                    review_list[i]["生成代码行数"] = "0"
                    review_list[i]['波及组件'] = ''  
            else:
                review_list[i]["是否AI生成"] = "否"
                review_list[i]["生成代码行数"] = "0"
                review_list[i]['波及组件'] = ''
        else:
            review_list[i]["是否AI生成"] = "否"
            review_list[i]["生成代码行数"] = "0"
            review_list[i]['波及组件'] = ''
        description = item["描述"]
        h = html2text.HTML2Text()
        h.body_width = 0 # 设置为0表示不限制行宽
        h.single_line_break = True     
        h.wrap_links = False
        description = h.handle(description).strip()
        description = re.sub(r'\n{3,}', '\n\n', description) 
        review_list[i]["描述"] = description
    # 处理数据并更新到数据库
    if not review_list:
        print("没有需要更新的数据")
        return
    
    all_iterations = {
          '2025S14', '2025S15', '2025S16', '2025S17', '2025S18',
          '2025S19', '2025S20', '2025S21', '2025S22', '2025S23', 
          '2025S24', '2025S25'
    }

    all_iterations = sorted(all_iterations)  
    target_teams = [
        'L0-极光', 'L0-光速', 'L0-疾电之光', 
        'L2-集结号', "L2-超能", '支撑-BaseMan守垒员', '支撑-StarWar', '支撑-乘风破浪', '支撑-茅店神',
        '支撑-破冰号', '支撑-北极星', '支撑-猿宇宙', '仿真-天问'
    ]
    component_set = { item["波及组件"] for item in review_list if item["迭代"] in all_iterations }
    stats_dict = {}
    for it in all_iterations:
        for team in target_teams:
            if it and team:
                key = (it, team)
                stats_dict[key] = { "任务总数": 0, "AI辅助生成数": 0, "AI生成代码行数": 0 }

    component_dict = {}
    for it in all_iterations:
        for component in component_set:
            if it and component:
                key = (it, component)
                component_dict[key] = { "任务总数": 0, "AI辅助生成数": 0, "AI生成代码行数": 0 }

    for item in review_list:
        if item["子类"] == '03-Story开发类' or item["子类"] == '04-Story验证类':  
            key_stats = (item["迭代"], item["团队"])
            if key_stats in stats_dict:
                stats_dict[key_stats]["任务总数"] += 1
                if item.get("是否AI生成") == "是":
                    stats_dict[key_stats]["AI辅助生成数"] += 1
                    code_lines = int(item.get("生成代码行数", 0))
                    stats_dict[key_stats]["AI生成代码行数"] += code_lines
            key_component = (item["迭代"], item["波及组件"])
            if key_component in component_dict:
                component_dict[key_component]["任务总数"] += 1
                if item.get("是否AI生成") == "是":
                    component_dict[key_component]["AI辅助生成数"] += 1
                    code_lines = int(item.get("生成代码行数", 0))
                    component_dict[key_component]["AI生成代码行数"] += code_lines

    stats_list = []
    for (it, team), stats in stats_dict.items():
        stats_with_key = { "迭代": it, "团队": team, **stats }
        stats_list.append(stats_with_key)

    component_list = []
    for (it, component), comp_stats in component_dict.items():
        comp_with_key = { "迭代": it, "波及组件": component, **comp_stats }
        component_list.append(comp_with_key)

    write_task_database(review_list, "task", "标识")  
    write_task_database(stats_list, "team_summary", "迭代, 团队")
    write_task_database(component_list, "component_summary", "迭代, 波及组件")
   
def write_task_database(review_list, table_name, primary_key, data_path = '../data/sql_task.db'):
    conn = None
    try:
        conn = sqlite3.connect(data_path)
        cursor = conn.cursor()

        # 获取表字段信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_fields: Set[str] = {row[1] for row in cursor.fetchall()}
        print(f"数据库表中存在的字段: {sorted(table_fields)}")

        if not review_list:
            print("没有数据可处理")
            return

        data_fields = list(review_list[0].keys())
        existing_fields = [field for field in data_fields if field in table_fields]

        missing_fields = [field for field in data_fields if field not in table_fields]
        if missing_fields:
            print(f"以下字段在数据库中不存在，将被跳过: {missing_fields}")
        # 确定要使用的字段
        non_primary_fields = [f for f in existing_fields if f != primary_key] if primary_key else existing_fields
        insert_fields = ", ".join([f'"{f}"' for f in existing_fields])
        placeholders = ", ".join(["?" for _ in existing_fields])
        update_clause = ", ".join([f'"{f}" = excluded."{f}"' for f in non_primary_fields])
        sql = f"""
            INSERT INTO "{table_name}" ({insert_fields})
            VALUES ({placeholders})
            ON CONFLICT({primary_key})
            DO UPDATE SET {update_clause}
        """
    
        # 执行插入/更新
        total = len(review_list)
        updated = 0
        inserted = 0
        for i, item in enumerate(review_list, 1):
            values = [item.get(field) for field in existing_fields]
            try:
                cursor.execute(sql, values)
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                if i % 100 == 0:
                    conn.commit()
                    print(f"已处理 {i}/{total} 条数据（插入: {inserted}, 更新: {updated}）")
            except sqlite3.Error as e:
                print(f"处理第 {i} 条数据时出错: {e}")
                print(f"出错数据: {item}")
                conn.rollback()

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

def clear_table_data(table_name, data_path='../data/sql_task.db'):
    """
    清空指定 SQLite 数据库中某张表的所有数据（保留表结构）
    Args:
        table_name (str): 要清空的表名，如 'tasks'
        data_path (str): SQLite 数据库文件路径，默认是 '../data/sql_task.db'
    """
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(data_path)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")     
        conn.commit()
        print(f"✅ 已清空表 '{table_name}' 的所有数据")
    except Exception as e:
        print(f"❌ 清空表数据时出错: {e}")
        if conn:
            conn.rollback()  # 出错回滚
    finally:
        if conn:
            conn.close()  # 确保关闭连接

if __name__ == "__main__":
    tasks_update()

