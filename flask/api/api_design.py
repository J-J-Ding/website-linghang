import sqlite3
from flask import request, jsonify

# 数据库参数
DESIGN_DB_PATH = "../data/designs.db"
DESIGN_TABLE_NAME = "designs"
SCENE_TABLE_NAME = "scenes"
PERFORMANCE_TABLE_NAME = "performances"
FAULT_TABLE_NAME = "faults"

#详设跟踪
def API_Design_set():
    """
        更新详细设计导入数据表，从前端接收JSON数据
        如果详细设计名称已存在则更新所有内容，如果是新增则直接增加行
        数据库表内容为：团队、详设名称、详设链接、进度、责任人、详设进展、预期定稿日期、组件设计评审结果、组件设计评审报告
        """
    try:
        # 解析请求数据
        data = request.json
        print(f"data: {data}\n\n")
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        design_link = data.get("design_link")
        if not design_link:
            return jsonify({"status": "error", "message": "Missing design_link"}), 400

        team = data.get("team", "")
        design_name = data.get("design_name", "")
        design_link = data.get("design_link", "")
        progress = data.get("progress", "")
        responsible = data.get("responsible", "")
        design_progress = data.get("design_progress", "")
        expected_completion_date = data.get("expected_completion_date", "")
        review_result = data.get("review_result", "")
        review_report = data.get("review_report", "")
        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            # 检查是否存在相同记录
            cursor.execute(f"SELECT design_id FROM {DESIGN_TABLE_NAME} WHERE design_link = ?", (design_link,))
            existing_record = cursor.fetchone()
            if existing_record:
                # 记录存在，执行更新
                design_id = existing_record[0]
                cursor.execute(f'''
                               UPDATE {DESIGN_TABLE_NAME}
                               SET team                     = ?,
                                   design_name              = ?,
                                   progress                 = ?,
                                   responsible              = ?,
                                   design_progress          = ?,
                                   expected_completion_date = ?,
                                   review_result            = ?,
                                   review_report            = ?,
                                   create_time              = ?
                               WHERE design_id = ?
                               ''', (
                                   team,
                                   design_name,
                                   progress,
                                   responsible,
                                   design_progress,
                                   expected_completion_date,
                                   review_result,
                                   review_report,
                                   current_time,
                                   design_id
                               ))
                print(f"更新了详设记录，design_id: {design_id}")
            else:
                # 记录不存在，执行插入
                cursor.execute(f'''
                               INSERT INTO {DESIGN_TABLE_NAME}
                               (team, design_name, design_link, progress, responsible,
                                design_progress, expected_completion_date, review_result,
                                review_report, create_time)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (
                                   team,
                                   design_name,
                                   design_link,
                                   progress,
                                   responsible,
                                   design_progress,
                                   expected_completion_date,
                                   review_result,
                                   review_report,
                                   current_time
                               ))
                print(f"新增了详设记录，design_id: {cursor.lastrowid}")
            conn.commit()
        return jsonify({"status": "success", "message": "design data saved successfully"}), 200
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"An error occurred in API_Design_set: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Design_batch_set():
    """
    批量更新详细设计导入数据表，从前端接收JSON数据
    接收一个包含多个设计数据的数组，对每个设计数据执行单条导入逻辑
    如果详设名称已存在则更新所有内容，如果是新增则直接增加行
    数据库表内容为：团队、详设名称、详设链接、进度、责任人、详设进展、预期定稿日期、组件设计评审结果、组件设计评审报告
    """
    try:
        # 解析请求数据
        data = request.json
        print(f"data: {data}\n\n")
        
        if not data or 'designs' not in data:
            return jsonify({"status": "error", "message": "No 'designs' array provided in JSON data"}), 400

        designs_list = data.get('designs', [])
        if not isinstance(designs_list, list):
            return jsonify({"status": "error", "message": "'designs' must be an array"}), 400

        if not designs_list:
            return jsonify({"status": "error", "message": "Empty 'designs' array provided"}), 400

        success_count = 0
        failed_count = 0
        failed_items = []
        errors = []

        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            for i, design_data in enumerate(designs_list):
                try:
                    # 检查单个设计数据的必要字段
                    design_link = design_data.get("design_link")
                    if not design_link:
                        failed_count += 1
                        failed_items.append(i)
                        errors.append(f"Item {i}: Missing design_link")
                        continue # 跳过这个无效项，继续处理下一个

                    # 获取单个设计的所有字段
                    team = design_data.get("team", "")
                    design_name = design_data.get("design_name", "")
                    # design_link 已在上面获取
                    progress = design_data.get("progress", "")
                    responsible = design_data.get("responsible", "")
                    design_progress = design_data.get("design_progress", "")
                    expected_completion_date = design_data.get("expected_completion_date", "")
                    review_result = design_data.get("review_result", "")
                    review_report = design_data.get("review_report", "")

                    # 检查是否存在相同记录 (通过 design_link)
                    cursor.execute(f"SELECT design_id FROM {DESIGN_TABLE_NAME} WHERE design_link = ?", (design_link,))
                    existing_record = cursor.fetchone()
                    
                    if existing_record:
                        # 记录存在，执行更新
                        design_id = existing_record[0]
                        cursor.execute(f'''
                                       UPDATE {DESIGN_TABLE_NAME}
                                       SET team                     = ?,
                                           design_name              = ?,
                                           progress                 = ?,
                                           responsible              = ?,
                                           design_progress          = ?,
                                           expected_completion_date = ?,
                                           review_result            = ?,
                                           review_report            = ?,
                                           create_time              = ?
                                       WHERE design_id = ?
                                       ''', (
                                           team,
                                           design_name,
                                           progress,
                                           responsible,
                                           design_progress,
                                           expected_completion_date,
                                           review_result,
                                           review_report,
                                           current_time,
                                           design_id
                                       ))
                        print(f"更新了详设记录，design_id: {design_id}, design_name: {design_name}")
                    else:
                        # 记录不存在，执行插入
                        cursor.execute(f'''
                                       INSERT INTO {DESIGN_TABLE_NAME}
                                       (team, design_name, design_link, progress, responsible,
                                        design_progress, expected_completion_date, review_result,
                                        review_report, create_time)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                       ''', (
                                           team,
                                           design_name,
                                           design_link,
                                           progress,
                                           responsible,
                                           design_progress,
                                           expected_completion_date,
                                           review_result,
                                           review_report,
                                           current_time
                                       ))
                        inserted_id = cursor.lastrowid
                        print(f"新增了详设记录，design_id: {inserted_id}, design_name: {design_name}")
                    
                    success_count += 1

                except Exception as e_item:
                    # 处理单个设计数据的错误
                    failed_count += 1
                    failed_items.append(i)
                    error_msg = f"Item {i} (design_link: {design_data.get('design_link', 'N/A')}): {str(e_item)}"
                    errors.append(error_msg)
                    print(f"处理单个设计数据时出错: {error_msg}")
                    # 不中断整个批量过程，继续处理下一个
                    continue

            conn.commit()

        # 构建响应信息
        response_data = {
            "status": "success",
            "message": f"批量处理完成。成功: {success_count} 条，失败: {failed_count} 条。",
            "success_count": success_count,
            "failed_count": failed_count
        }

        if failed_count > 0:
            response_data["failed_items"] = failed_items
            response_data["error_details"] = errors
            # 可以选择返回 207 Multi-Status 或 200 OK，这里选择 200 OK
            # 因为整体操作完成，只是部分项有错误
            return jsonify(response_data), 200
        else:
            # 所有项都成功
            return jsonify(response_data), 200

    except Exception as e:
        # 发生严重错误时回滚
        print(f"An error occurred in API_Design_batch_set: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500
    # finally:  # 在 with 语句块中，连接会自动关闭
    #     if conn:
    #         conn.close()
    #         print("数据库连接已关闭。")

def API_Design_get():
    """
    API 接口：从本地 SQLite 数据库获取核心详设信息
    - 目前按查询整张表返回
    """
    print("API_Design_get: 接收到获取数据库核心详设跟踪进展请求")

    def row_to_dict(row):
        """将 SQLite Row 对象转换为标准化字典"""

        # 安全地访问数据库行的字段，避免 KeyError
        def safe_get(row, key, default=""):
            try:
                return row[key] or default
            except:
                return default
        return {
            "design_id": safe_get(row, 'design_id'),
            "team": safe_get(row, 'team'),
            "design_name": safe_get(row, 'design_name'),
            "design_link": safe_get(row, 'design_link'),
            "progress": safe_get(row, 'progress'),
            "responsible": safe_get(row, 'responsible'),
            "design_progress": safe_get(row, 'design_progress'),
            "expected_completion_date": safe_get(row, 'expected_completion_date'),
            "review_result": safe_get(row, 'review_result'),
            "review_report": safe_get(row, 'review_report'),
        }

    conn = None
    try:
        conn = sqlite3.connect(DESIGN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 如果没有提供任何参数或参数为空，查询整张表
        print("正在查询所有核心详设信息")
        cursor.execute(f"SELECT * FROM {DESIGN_TABLE_NAME}")
        message = "所有核心详设信息获取成功"
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "status": "success",
                "message": f"数据库中没有核心详设记录",
                "core_design_data": []
            })

        # ✅ 统一处理：无论单条还是多条，都用 row_to_dict 转换
        core_design_data = [row_to_dict(row) for row in rows]
        print(f"成功获取数据，共 {len(core_design_data)} 条记录")
        return jsonify({
            "status": "success",
            "message": message,
            "core_design_data": core_design_data
        })
    except Exception as e:
        print(f"获取核心详设数据时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Design_delete():
    """
            删除详细设计数据，从前端接收JSON数据
            根据详设链接关键字来删除数据，单个链接只对应唯一一条数据
            """
    conn = None
    try:
        data = request.json
        print(f"data: {data}\n\n")
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        delete_design_id = data.get("design_id")
        print(f"need delete design_id：{delete_design_id}\n\n")
        if not delete_design_id:
            return jsonify({"status": "error", "message": "No design_id provided"}), 400
        try:
            design_id = int(delete_design_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "设计ID格式不正确"}), 400

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(f"SELECT design_id FROM {DESIGN_TABLE_NAME} WHERE design_id = ?", (design_id,))
            existing = cursor.fetchone()

            if not existing:
                print(f"记录不存在，design_id: {design_id}")
                return jsonify({"status": "success", "message": "该详设链接不存在"}), 404

            # 执行删除
            cursor.execute(f"DELETE FROM {DESIGN_TABLE_NAME} WHERE design_id = ?", (design_id,))
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                conn.commit()
                print(f"成功删除设计记录，design_id: {design_id}")
                return jsonify({"status": "success", "message": f"删除design_id:{design_id}操作成功"}), 200
            else:
                conn.rollback()
                print(f"删除失败，design_id: {design_id}")
                return jsonify({"status": "error", "message": f"删除design_id:{design_id}操作失败，未影响任何记录."}), 500
    except Exception as e:
        # 发生错误时回滚
        if conn:
            conn.rollback()
        print(f"An error occurred in API_Design_delete: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

# 场景库
def API_Scene_set():
    """
            更新场景库数据表，从前端接收JSON数据
            如果详细设计名称已存在则更新所有内容，如果是新增则直接增加行
            数据库表内容为：组件、功能模块、业务场景、关联场景、维护团队、场景对应详设链接、创建时间
            """
    try:
        # 解析请求数据
        data = request.json
        print(f"data: {data}\n\n")
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        component = data.get("component")
        function_module = data.get("function_module")
        business_scenario = data.get("business_scenario")
        related_scenarios = data.get("related_scenarios")
        if not component or not function_module or not business_scenario or not related_scenarios:
            return jsonify({"status": "error", "message": "Missing relevant data"}), 400

        maintenance_team = data.get("maintenance_team", "")
        detail_link = data.get("detail_link", "")
        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            # 检查是否存在相同记录
            cursor.execute(f'''SELECT scene_id FROM {SCENE_TABLE_NAME} 
                                    WHERE component = ? AND 
                                          function_module = ? AND 
                                          business_scenario = ? AND 
                                          related_scenarios = ?
                                ''', (component, function_module, business_scenario, related_scenarios))
            existing_record = cursor.fetchone()
            if existing_record:
                # 记录存在，执行更新
                scene_id = existing_record[0]
                cursor.execute(f'''
                                   UPDATE {SCENE_TABLE_NAME}
                                   SET component          = ?,
                                       function_module    = ?,
                                       business_scenario  = ?,
                                       related_scenarios  = ?,
                                       maintenance_team   = ?,
                                       detail_link        = ?,
                                       create_time        = ?
                                   WHERE scene_id = ?
                                   ''', (
                    component,
                    function_module,
                    business_scenario,
                    related_scenarios,
                    maintenance_team,
                    detail_link,
                    current_time,
                    scene_id
                ))
                print(f"更新了场景库记录，scene_id: {scene_id}")
            else:
                # 记录不存在，执行插入
                cursor.execute(f'''
                                   INSERT INTO {SCENE_TABLE_NAME}
                                   (component, function_module, business_scenario, related_scenarios, maintenance_team,
                                    detail_link, create_time)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)
                                   ''', (
                    component,
                    function_module,
                    business_scenario,
                    related_scenarios,
                    maintenance_team,
                    detail_link,
                    current_time,
                ))
                print(f"新增了场景库记录，scene_id: {cursor.lastrowid}")
            conn.commit()
        return jsonify({"status": "success", "message": "scene data saved successfully"}), 200
    except Exception as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"An error occurred in API_Scene_set: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Scene_get():
    """
    API 接口：从本地 SQLite 数据库获取场景库信息
    - 目前按查询整张表返回
    """
    print("API_Scene_get: 接收到获取数据库场景库信息请求")

    def row_to_dict(row):
        """将 SQLite Row 对象转换为标准化字典"""

        # 安全地访问数据库行的字段，避免 KeyError
        def safe_get(row, key, default=""):
            try:
                return row[key] or default
            except:
                return default

        return {
            "scene_id": safe_get(row, 'scene_id'),
            "component": safe_get(row, 'component'),
            "function_module": safe_get(row, 'function_module'),
            "business_scenario": safe_get(row, 'business_scenario'),
            "related_scenarios": safe_get(row, 'related_scenarios'),
            "maintenance_team": safe_get(row, 'maintenance_team'),
            "detail_link": safe_get(row, 'detail_link'),
            "create_time": safe_get(row, 'create_time')
        }

    conn = None
    try:
        conn = sqlite3.connect(DESIGN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 如果没有提供任何参数或参数为空，查询整张表
        print("正在查询所有场景库数据信息")
        cursor.execute(f"SELECT * FROM {SCENE_TABLE_NAME}")
        message = "所有场景库数据信息获取成功"
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "status": "success",
                "message": f"数据库中没有场景库数据信息记录",
                "scenes_data": []
            })

        # ✅ 统一处理：无论单条还是多条，都用 row_to_dict 转换
        scenes_data = [row_to_dict(row) for row in rows]
        print(f"成功获取数据，共 {len(scenes_data)} 条记录")
        # print(f"scenes_data:{scenes_data}")  'related_scenarios': '["2","3","4"]'
        return jsonify({
            "status": "success",
            "message": message,
            "scenes_data": scenes_data
        })
    except Exception as e:
        print(f"获取场景库数据信息时发生未预期错误: {e}")
        return jsonify({
            "status": "error",
            "message": f"内部服务器错误: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Scene_delete():
    """
    删除场景库数据，从前端接收JSON数据
    根据详设链接关键字来删除数据，单个链接只对应唯一一条数据
    """
    conn = None
    try:
        # 解析请求数据
        data = request.json
        print(f"data: {data}\n\n")
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        delete_scene_id = data.get("scene_id")
        print(f"need delete scene_id：{delete_scene_id}\n\n")
        if not delete_scene_id:
            return jsonify({"status": "error", "message": "No scene_id provided"}), 400
        try:
            scene_id = int(delete_scene_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "设计ID格式不正确"}), 400

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()
            # 执行删除
            cursor.execute(f"DELETE FROM {SCENE_TABLE_NAME} WHERE scene_id = ?", (scene_id,))
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                conn.commit()
                print(f"成功删除设计记录，scene_id: {scene_id}")
                return jsonify({"status": "success", "message": f"scene_id:{scene_id}操作成功"}), 200
            else:
                conn.rollback()
                print(f"删除失败，scene_id: {scene_id}")
                return jsonify(
                    {"status": "error", "message": f"scene_id:{scene_id}操作失败，未影响任何记录."}), 500
    except Exception as e:
        # 发生错误时回滚
        if conn:
            conn.rollback()
        print(f"An error occurred in API_Scene_delete: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

def API_Scene_update():
    """
        更新场景库数据，从前端接收JSON数据
        根据详设链接关键字来更新数据，单个链接只对应唯一一条数据
    """
    conn = None
    try:
        # 解析请求数据
        data = request.json
        print(f"data: {data}\n\n")
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 获取必要字段
        update_scene_id = data.get("scene_id")
        print(f"need update scene_id：{update_scene_id}\n\n")
        if not update_scene_id:
            return jsonify({"status": "error", "message": "No scene_id provided"}), 400
        try:
            scene_id = int(update_scene_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "场景库传入后端ID格式不正确"}), 400

        component = data.get("component")
        function_module = data.get("function_module")
        business_scenario = data.get("business_scenario")
        related_scenarios = data.get("related_scenarios")
        if not component or not function_module or not business_scenario or not related_scenarios:
            return jsonify({"status": "error", "message": "Missing relevant data"}), 400

        maintenance_team = data.get("maintenance_team", "")
        detail_link = data.get("detail_link", "")
        # 获取当前时间
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()
            # 执行更新
            cursor.execute(f'''UPDATE {SCENE_TABLE_NAME}
                                   SET component          = ?,
                                       function_module    = ?,
                                       business_scenario  = ?,
                                       related_scenarios  = ?,
                                       maintenance_team   = ?,
                                       detail_link        = ?,
                                       create_time        = ?
                                   WHERE scene_id = ?
                                   ''', (
                                        component,
                                        function_module,
                                        business_scenario,
                                        related_scenarios,
                                        maintenance_team,
                                        detail_link,
                                        current_time,
                                        scene_id
                                    ))
            updated_count = cursor.rowcount
            if updated_count > 0:
                conn.commit()
                print(f"成功更新场景数据记录，scene_id: {scene_id}")
                return jsonify({"status": "success", "message": f"scene_id:{scene_id}操作成功"}), 200
            else:
                conn.rollback()
                print(f"更新失败，scene_id: {scene_id}")
                return jsonify(
                    {"status": "error", "message": f"scene_id:{scene_id}操作失败，未影响任何记录."}), 500
    except Exception as e:
        # 发生错误时回滚
        if conn:
            conn.rollback()
        print(f"An error occurred in API_Scene_update: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("数据库连接已关闭。")

#性能库
def API_Performance_set():
    """
    更新或新增组件设计性能库数据表，从前端接收 JSON 数据。
    如果 component + performance_type + performance_metrics 组合已存在，则更新；
    否则插入新记录。
    数据库表字段：组件、性能类型、性能指标、性能边界值、说明、创建时间
    """
    try:
        data = request.json
        print(f"API_Performance_set received data: {data}\n")

        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 必填字段校验
        component = data.get("component")
        performance_type = data.get("performance_type")
        performance_metrics = data.get("performance_metrics")
        performance_boundary = data.get("performance_boundary")
        if not component or not performance_type or not performance_metrics or not performance_boundary:
            return jsonify({"status": "error", "message": "Missing required fields: component, performance_type, performance_metrics, performance_boundary"}), 400

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = None
        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            # 判断是否已存在（基于关键字段组合）
            cursor.execute(f'''
                SELECT performance_id FROM {PERFORMANCE_TABLE_NAME}
                WHERE component = ? AND performance_type = ? AND performance_metrics = ?
            ''', (component, performance_type, performance_metrics))
            existing = cursor.fetchone()

            if existing:
                # 更新
                performance_id = existing[0]
                cursor.execute(f'''
                    UPDATE {PERFORMANCE_TABLE_NAME}
                    SET component = ?,
                        performance_type = ?,
                        performance_metrics = ?,
                        performance_boundary = ?,
                        create_time = ?
                    WHERE performance_id = ?
                ''', (
                    component,
                    performance_type,
                    performance_metrics,
                    performance_boundary,
                    current_time,
                    performance_id
                ))
                print(f"Updated performance record, ID: {performance_id}")
            else:
                # 插入
                cursor.execute(f'''
                    INSERT INTO {PERFORMANCE_TABLE_NAME}
                    (component, performance_type, performance_metrics, performance_boundary, create_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    component,
                    performance_type,
                    performance_metrics,
                    performance_boundary,
                    current_time
                ))
                print(f"Inserted new performance record, ID: {cursor.lastrowid}")

            conn.commit()

        return jsonify({"status": "success", "message": "Performance data saved successfully"}), 200

    except Exception as e:
        print(f"Error in API_Performance_set: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

def API_Performance_get():
    """
    API 接口：从本地 SQLite 数据库获取组件设计性能库全部数据。
    返回整张表内容。
    """
    print("API_Performance_get: Received request to fetch performance data")

    def row_to_dict(row):
        """将 SQLite Row 转为标准字典"""
        def safe_get(r, key, default=""):
            try:
                return r[key] or default
            except:
                return default

        return {
            "performance_id": safe_get(row, "performance_id"),
            "component": safe_get(row, "component"),
            "performance_type": safe_get(row, "performance_type"),
            "performance_metrics": safe_get(row, "performance_metrics"),
            "performance_boundary": safe_get(row, "performance_boundary"),
            "create_time": safe_get(row, "create_time")
        }

    conn = None
    try:
        conn = sqlite3.connect(DESIGN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {PERFORMANCE_TABLE_NAME}")
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "status": "success",
                "message": "No performance data found",
                "performance_data": []
            })

        performance_data = [row_to_dict(row) for row in rows]
        print(f"Fetched {len(performance_data)} performance records")

        return jsonify({
            "status": "success",
            "message": "Performance data retrieved successfully",
            "performance_data": performance_data
        })

    except Exception as e:
        print(f"Error in API_Performance_get: {e}")
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

#故障库
def API_Fault_set():
    """
    新版故障库接口：仅保留 component, identifier, title, source, reason_category, detail_link
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400

        # 必填字段
        component = data.get("component")
        identifier = data.get("identifier")
        title = data.get("title")
        source = data.get("source")
        reason_category = data.get("reason_category")
        if not all([component, identifier, title, source, reason_category]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        detail_link = data.get("detail_link", "")

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(DESIGN_DB_PATH) as conn:
            cursor = conn.cursor()

            # 以 identifier 为唯一键判断是否更新
            cursor.execute(f'''
                SELECT fault_id FROM {FAULT_TABLE_NAME} WHERE identifier = ?
            ''', (identifier,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(f'''
                    UPDATE {FAULT_TABLE_NAME}
                    SET component = ?, title = ?, source = ?, reason_category = ?,
                        detail_link = ?, create_time = ?
                    WHERE fault_id = ?
                ''', (component, title, source, reason_category, detail_link, current_time, existing[0]))
                print(f"Updated fault: {identifier}")
            else:
                cursor.execute(f'''
                    INSERT INTO {FAULT_TABLE_NAME}
                    (component, identifier, title, source, reason_category, detail_link, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (component, identifier, title, source, reason_category, detail_link, current_time))
                print(f"Inserted new fault: {identifier}")

            conn.commit()
        return jsonify({"status": "success", "message": "Fault saved successfully"}), 200

    except Exception as e:
        print(f"API_Fault_set error: {e}")
        return jsonify({"status": "error", "message": "Internal error"}), 500

def API_Fault_get():
    """只返回精简字段"""
    def row_to_dict(row):
        def safe_get(key, default=""):
            try:
                val = row[key]
                return val if val is not None else default
            except:
                return default

        return {
            "fault_id": safe_get("fault_id"),
            "component": safe_get("component"),
            "identifier": safe_get("identifier"),
            "title": safe_get("title"),
            "source": safe_get("source"),
            "reason_category": safe_get("reason_category"),
            "detail_link": safe_get("detail_link"),
            "create_time": safe_get("create_time")
        }
    conn = None
    try:
        conn = sqlite3.connect(DESIGN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {FAULT_TABLE_NAME}")
        rows = cursor.fetchall()
        print(rows)
        faults_data = [row_to_dict(row) for row in rows]
        print(faults_data)
        return jsonify({
            "status": "success",
            "faults_data": faults_data
        })
    except Exception as e:
        print(f"API_Fault_get error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()