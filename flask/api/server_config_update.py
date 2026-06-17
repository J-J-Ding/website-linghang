# 更新基础数据库
import json
import sqlite3
import sys
import os
from typing import Set
from flask import request, jsonify

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 从api目录导入所需模块
from api.get_rdc import Rdc_list_get
from api.api_data import Icenter_table_get

TABLE_MAP = {
    'user': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/225d56c88fcf11f0adaaf1054887738d/view',
    'team': 'https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/30f7417e8fd211f0ae1cdb0d734db3c7/view',
}

DB_PATH = "../data/sql_config.db"     # SQLite 数据库文件路径

def Basic_config_overwrite():
    print("Basic_config_update: 开始更新基础配置数据...")

    # 定义各表的配置信息：表名、插入字段、字段顺序
    table_configs = {
        'team': {
            'fields': ['团队', '领域', '部门'],
            'insert_sql': "INSERT OR REPLACE INTO team (团队, 领域, 部门) VALUES (?, ?, ?)"
        },
        'user': {
            'fields': ['工号', '姓名', '岗位', '部门', '领域', '团队'],
            'insert_sql': "INSERT OR REPLACE INTO user (工号, 姓名, 岗位, 部门, 领域, 团队) VALUES (?, ?, ?, ?, ?, ?)"
        }
        # 如需添加新表，在此处扩展配置即可
    }

    try:
        # 1. 连接 SQLite 数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 2. 通用更新逻辑：遍历所有表配置进行处理
        for table_name, config in table_configs.items():
            print(f"📥 正在获取 {table_name} 数据...")
            
            # 获取表数据
            table_data = Icenter_table_get(TABLE_MAP[table_name])
            if not table_data:
                print(f"⚠️  警告：未获取到 {table_name} 数据")
                continue

            # 清空旧数据
            cursor.execute(f"DELETE FROM {table_name}")
            
            # 插入新数据
            for row in table_data:
                # 按配置的字段顺序提取数据
                row_values = [row.get(field) for field in config['fields']]
                cursor.execute(config['insert_sql'], row_values)

            print(f"✅ {table_name} 表更新完成，共插入 {len(table_data)} 条记录")

        # 3. 提交事务
        conn.commit()
        print("🎉 基础配置数据全部更新完成！")

    except sqlite3.Error as e:
        print(f"❌ 数据库操作错误: {str(e)}")
        if conn:
            conn.rollback()  # 出错时回滚事务
    finally:
        # 确保连接关闭
        if conn:
            conn.close()

DB_CHAT_PATH = "../data/chat.db"
def Basic_config_update():
    print("Basic_config_update: 开始增量更新基础配置数据...")

    # 表配置：指定各表的主键（用于索引匹配）和需要更新的列
    table_configs = {
        'prompt': {
            'primary_key': '主题',  # 用于匹配行的主键
            'update_columns': ['摘要', '内容', '场景', '创建人'],  # 仅更新这些列
        }
        # 可以扩展其他表
    }

    try:
        # 连接数据库
        conn = sqlite3.connect(DB_CHAT_PATH)
        cursor = conn.cursor()

        for table_name, config in table_configs.items():
            print(f"📥 正在获取 {table_name} 增量数据...")
            
            # 获取最新数据
            new_data = Icenter_table_get(TABLE_MAP[table_name])
            if not new_data:
                print(f"⚠️  警告：未获取到 {table_name} 数据")
                continue

            # 记录更新和插入的数量
            updated_count = 0
            inserted_count = 0

            # 构建插入时的列名：主键 + 更新列
            insert_columns = [config['primary_key']] + config['update_columns']

            # 处理每条数据
            for row in new_data:
                pk = row.get(config['primary_key'])
                if not pk:
                    print(f"⚠️  跳过无效行（缺少主键）：{row}")
                    continue

                # 检查数据库中是否存在该主键
                cursor.execute(
                    f"SELECT 1 FROM {table_name} WHERE {config['primary_key']} = ?",
                    (pk,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    # 存在则仅更新指定列
                    set_clause = ", ".join([f"{col} = ?" for col in config['update_columns']])
                    update_sql = f"UPDATE {table_name} SET {set_clause} WHERE {config['primary_key']} = ?"
                    
                    # 准备参数：更新列的值 + 主键值
                    params = [row.get(col) for col in config['update_columns']] + [pk]
                    cursor.execute(update_sql, params)
                    updated_count += 1
                else:
                    # 不存在则插入新记录：插入主键 + 指定更新列
                    placeholders = ", ".join(["?"] * len(insert_columns))
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(insert_columns)}) VALUES ({placeholders})"
                    
                    # 按插入列顺序准备参数
                    params = [row.get(col) for col in insert_columns]
                    cursor.execute(insert_sql, params)
                    inserted_count += 1

            print(f"✅ {table_name} 表处理完成：更新 {updated_count} 条，新增 {inserted_count} 条")

        conn.commit()
        print("🎉 基础配置数据增量更新完成！")

    except sqlite3.Error as e:
        print(f"❌ 数据库操作错误: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def API_Config_update():
    """
    API 接口：更新系统配置数据
    前端可以直接调用此接口来触发全量数据更新
    """
    print("API_Config_update: 接收到配置更新请求")
    
    try:
        # 更新基础配置数据
        Basic_config_overwrite()
                
        return jsonify({
            "status": "success",
            "message": "所有配置数据更新成功"
        })
            
    except Exception as e:
        error_msg = f"配置更新过程中发生未预期错误: {str(e)}"
        print(error_msg)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


if __name__ == "__main__":
    Basic_config_overwrite()
    # Basic_config_update()
    # Review_update()
