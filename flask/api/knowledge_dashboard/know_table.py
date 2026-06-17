import decimal
from collections import defaultdict
from sqlalchemy.dialects.mysql import INTEGER
from datetime import datetime, timedelta, date as dt_date
from sqlalchemy import String, Column, DateTime, Text, delete, JSON, Boolean, and_, or_, desc, DECIMAL, func
from electric_knowledge.data_model import db
from knowledge_dashboard import pub


class KnowCompTreePageTable(db.Model):
    __bind_key__ = "db5"
    __tablename__ = "know_comp_tree_page_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    page_title = Column(String(128), nullable=True)
    field_name = Column(String(128), nullable=True)
    comp_name = Column(String(128), nullable=True)
    module_name = Column(String(128), nullable=True)
    module_num = Column(INTEGER, nullable=True)
    page_url = Column(String(256), nullable=True)
    page_status = Column(String(128), nullable=True)
    page_person = Column(String(128), nullable=True)
    page_se = Column(String(128), nullable=True)
    page_tl = Column(String(128), nullable=True)
    page_tse = Column(String(128), nullable=True)
    finish_flag = Column(String(128), nullable=True)
    update_by = Column(String(128), nullable=True)
    update_date = Column(String(128), nullable=True)
    editor_num = Column(INTEGER, nullable=True)
    edit_num = Column(INTEGER, nullable=True)
    view_visitor_num = Column(INTEGER, nullable=True)
    view_visit_num = Column(INTEGER, nullable=True)
    ai_adapt_num = Column(DECIMAL(10, 2), nullable=True)
    ai_gene_num = Column(DECIMAL(10, 2), nullable=True)
    comp_engineering = Column(JSON, nullable=True)
    script_date = Column(String(128), nullable=True)

    def as_dict(self):
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            # 将 Decimal 类型转换为 float 以支持 JSON 序列化
            if hasattr(value, '__float__'):
                result[c.name] = float(value) if value is not None else None
            else:
                result[c.name] = value
        return result


def query_know_comp_tree_page_table_comp_tree_page_list_by_field_name_page_status_page_type_script_date(field_name, page_type, page_status, script_date):
    if page_status == "节点总数":
        if field_name == "波分中心":
            model_list = db.session.query(KnowCompTreePageTable).filter(
                KnowCompTreePageTable.script_date == script_date
            ).all()
        else:
            model_list = db.session.query(KnowCompTreePageTable).filter(
                KnowCompTreePageTable.field_name == field_name,
                KnowCompTreePageTable.script_date == script_date
            ).all()
    else:
        if field_name == "波分中心":
            model_list = db.session.query(KnowCompTreePageTable).filter(
                KnowCompTreePageTable.page_status == page_status,
                KnowCompTreePageTable.script_date == script_date
            ).all()
        else:
            model_list = db.session.query(KnowCompTreePageTable).filter(
                KnowCompTreePageTable.field_name == field_name,
                KnowCompTreePageTable.page_status == page_status,
                KnowCompTreePageTable.script_date == script_date
            ).all()
    data_list = []
    if page_type == "comp":
        data_list = [item.as_dict() for item in model_list if item.module_name == ""]
    else:
        data_list = [item.as_dict() for item in model_list if item.module_name]
    return data_list


def query_know_comp_tree_page_table_change_detail_list_by_start_date_and_end_date(field_name, page_type, page_status, start_date, end_date):
    """
    根据开始日期和结束日期查询组件树页面表的变更详情列表
    对比 start_date 和 end_date 两个日期的数据，生成变更详情
    
    变更类型 (change_type)：
    - add: 新增（包括"新增节点"和"xx 转为已定稿"）
    - del: 删除（包括"删除节点"和"已定稿转为 xx"）
    
    变更详情 (change_detail)：
    - 新增节点：end_date 存在但 start_date 不存在的记录
    - xx 转为已定稿：start_date 状态不是已定稿，end_date 状态是已定稿
    - 删除节点：start_date 存在但 end_date 不存在的记录
    - 已定稿转为 xx：start_date 状态是已定稿，end_date 状态不是已定稿
    
    Args:
        field_name: 领域名称（如"波分中心"等）
        page_type: 页面类型（"comp"表示组件，"module"表示模块）
        page_status: 目标页面状态（如"已定稿"等）
        start_date: 开始日期，格式为字符串 "YYYY-MM-DD"
        end_date: 结束日期，格式为字符串 "YYYY-MM-DD"
        
    Returns:
        list: 变更详情列表，每一项包含变更类型、变更原因及详细信息
    """
    # 步骤 1：查询开始日期的数据
    if field_name == "波分中心":
        start_model_list = db.session.query(KnowCompTreePageTable).filter(
            KnowCompTreePageTable.page_status == page_status,
            KnowCompTreePageTable.script_date == start_date
        ).all()
    else:
        start_model_list = db.session.query(KnowCompTreePageTable).filter(
            KnowCompTreePageTable.field_name == field_name,
            KnowCompTreePageTable.page_status == page_status,
            KnowCompTreePageTable.script_date == start_date
        ).all()
    
    # 步骤 2：查询结束日期的数据
    if field_name == "波分中心":
        end_model_list = db.session.query(KnowCompTreePageTable).filter(
            KnowCompTreePageTable.page_status == page_status,
            KnowCompTreePageTable.script_date == end_date
        ).all()
    else:
        end_model_list = db.session.query(KnowCompTreePageTable).filter(
            KnowCompTreePageTable.field_name == field_name,
            KnowCompTreePageTable.page_status == page_status,
            KnowCompTreePageTable.script_date == end_date
        ).all()
    
    # 步骤 3：将数据转换为字典格式，使用唯一标识键
    # 组件用"comp:{comp_name}"，模块用"module:{comp_name}:{module_name}"
    # 使用 comp_name+module_name 的组合作为 key，避免重复
    start_map = {}
    for page in start_model_list:
        page_dict = page.as_dict()
        comp_name = page_dict["comp_name"]
        module_name = page_dict["module_name"]
        
        if not module_name and comp_name:  # 组件
            key = f"comp:{comp_name}"
            start_map[key] = page_dict
        elif module_name:  # 模块
            # 使用 comp_name 和 module_name 的组合作为 key
            key = f"module:{comp_name}:{module_name}"
            start_map[key] = page_dict
    
    end_map = {}
    for page in end_model_list:
        page_dict = page.as_dict()
        comp_name = page_dict["comp_name"]
        module_name = page_dict["module_name"]

        if not module_name and comp_name:  # 组件
            key = f"comp:{comp_name}"
            end_map[key] = page_dict
        elif module_name:  # 模块
            # 使用 comp_name 和 module_name 的组合作为 key
            key = f"module:{comp_name}:{module_name}"
            end_map[key] = page_dict
    
    # 步骤 4：对比两个映射，生成变更详情列表
    change_detail_list = []
    
    # 4.1 处理 end_date 中存在的记录
    for key, end_page in end_map.items():
        # 按 page_type 过滤
        if page_type == "comp" and end_page["module_name"]:
            continue  # 跳过模块
        if page_type == "module" and not end_page["module_name"]:
            continue  # 跳过组件
        
        if key not in start_map:
            # 情况 1：新增节点（end_date 存在但 start_date 不存在）
            change_item = end_page.copy()
            change_item["change_type"] = "add"
            change_item["change_detail"] = "新增节点"
            change_detail_list.append(change_item)
        else:
            start_page = start_map[key]
            # 检查状态变化：从其他状态变为当前 page_status
            if start_page["page_status"] != page_status:
                # 情况 2：xx 转为已定稿（从其他状态变为指定状态）
                change_item = end_page.copy()
                change_item["change_type"] = "add"
                change_item["change_detail"] = f"{start_page['page_status']}转为{page_status}"
                change_detail_list.append(change_item)
    
    # 4.2 处理 start_date 中存在但 end_date 中不存在或状态变化的记录（删除类型）
    for key, start_page in start_map.items():
        # 按 page_type 过滤
        if page_type == "comp" and start_page["module_name"]:
            continue  # 跳过模块
        if page_type == "module" and not start_page["module_name"]:
            continue  # 跳过组件
        
        if key not in end_map:
            # 情况 3：删除节点（start_date 存在但 end_date 不存在）
            change_item = start_page.copy()
            change_item["change_type"] = "del"
            change_item["change_detail"] = "删除节点"
            change_detail_list.append(change_item)
        else:
            end_page = end_map[key]
            # 检查状态变化：从当前 page_status 变为其他状态
            if end_page["page_status"] != page_status:
                # 情况 4：已定稿转为 xx（从指定状态变为其他状态）
                change_item = start_page.copy()
                change_item["change_type"] = "del"
                change_item["change_detail"] = f"{page_status}转为{end_page['page_status']}"
                change_detail_list.append(change_item)
    return change_detail_list


def update_know_comp_tree_page_table_comp_tree_page_list(comp_tree_page_list):
    # 从 comp_tree_page_list 的第一个元素获取 script_date
    script_date = comp_tree_page_list[0].get("script_date")
    # 删除与 script_date 相同的记录
    db.session.query(KnowCompTreePageTable).filter(KnowCompTreePageTable.script_date == script_date).delete()
    db.session.commit()
    for comp_tree_page_item in comp_tree_page_list:
        # 为列表中的每一项创建一个全新的数据库记录
        new_comp_tree_page_model = KnowCompTreePageTable(**comp_tree_page_item)
        db.session.add(new_comp_tree_page_model)
    db.session.commit()



class KnowCompTreeBoardTable(db.Model):
    __bind_key__ = "db5"
    __tablename__ = "know_comp_tree_board_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    date = Column(String(128), nullable=True)
    field_name = Column(String(128), nullable=True)
    comp_sum_num = Column(INTEGER, nullable=True)
    comp_initial_num = Column(INTEGER, nullable=True)
    comp_reviewed_num = Column(INTEGER, nullable=True)
    comp_revision_num = Column(INTEGER, nullable=True)
    comp_finish_num = Column(INTEGER, nullable=True)
    comp_blank_num = Column(INTEGER, nullable=True)
    comp_sum_editor_num = Column(INTEGER, nullable=True)
    comp_sum_edit_num = Column(INTEGER, nullable=True)
    comp_sum_view_visitor_num = Column(INTEGER, nullable=True)
    comp_sum_view_visit_num = Column(INTEGER, nullable=True)
    comp_sum_ai_adapt_num = Column(DECIMAL(10, 2), nullable=True)
    comp_sum_ai_gene_num = Column(DECIMAL(10, 2), nullable=True)
    comp_change_detail = Column(JSON, nullable=True)
    module_sum_num = Column(INTEGER, nullable=True)
    module_initial_num = Column(INTEGER, nullable=True)
    module_reviewed_num = Column(INTEGER, nullable=True)
    module_revision_num = Column(INTEGER, nullable=True)
    module_finish_num = Column(INTEGER, nullable=True)
    module_blank_num = Column(INTEGER, nullable=True)
    module_sum_editor_num = Column(INTEGER, nullable=True)
    module_sum_edit_num = Column(INTEGER, nullable=True)
    module_sum_view_visitor_num = Column(INTEGER, nullable=True)
    module_sum_view_visit_num = Column(INTEGER, nullable=True)
    module_sum_ai_adapt_num = Column(DECIMAL(10, 2), nullable=True)
    module_sum_ai_gene_num = Column(DECIMAL(10, 2), nullable=True)
    module_change_detail = Column(JSON, nullable=True)
    update_time = Column(nullable=True, server_default=func.now(), onupdate=func.now())

    def as_dict(self):
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            # 将 Decimal 类型转换为 float 以支持 JSON 序列化
            if hasattr(value, '__float__'):
                result[c.name] = float(value) if value is not None else None
            else:
                result[c.name] = value
        return result


def query_know_comp_tree_board_table_comp_tree_board_sum_list_everyday(start_date, end_date, page_type, data_type):
    """
    查询组件树看板数据，生成ECharts格式的时间序列

    Args:
        start_date: 开始日期，支持str("%Y-%m-%d")、date、datetime类型
        end_date: 结束日期，支持str("%Y-%m-%d")、date、datetime类型
        page_type: 页面类型，'comp'或'module'
        data_type: 数据类型，如'finish_num'、'sum_num'、'finish_rate'

    Returns:
        list: ECharts格式的数据列表，每个元素包含date、field_name、value
    """
    # 输入参数校验
    if page_type not in ['comp', 'module'] or not data_type:
        return []

    # 日期类型统一转换
    if isinstance(start_date, str):
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    elif isinstance(start_date, (dt_date, datetime)):
        start_date_obj = start_date if isinstance(start_date, dt_date) else start_date.date()
    else:
        raise TypeError(f"start_date must be str or date/datetime, got {type(start_date)}")

    if isinstance(end_date, str):
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    elif isinstance(end_date, (dt_date, datetime)):
        end_date_obj = end_date if isinstance(end_date, dt_date) else end_date.date()
    else:
        raise TypeError(f"end_date must be str or date/datetime, got {type(end_date)}")
    if start_date_obj > end_date_obj:
        return []

    # 比率类型映射
    ratio_mapping = {
        'finish_rate': ('finish_num', 'sum_num'),
    }
    is_ratio_type = data_type in ratio_mapping
    # 生成完整日期范围
    all_dates = [start_date_obj + timedelta(days=i) 
                 for i in range((end_date_obj - start_date_obj).days + 1)]
    # 获取数据库列名集合
    column_names = {c.name for c in KnowCompTreeBoardTable.__table__.columns}
    # 数据库查询（扩大范围至所有≤结束日期的数据，确保能获取起始点前的历史值）
    if is_ratio_type:
        numerator_suffix, denominator_suffix = ratio_mapping[data_type]
        numerator_field = f"{page_type}_{numerator_suffix}"
        denominator_field = f"{page_type}_{denominator_suffix}"
        if numerator_field not in column_names or denominator_field not in column_names:
            return []
        numerator_col = getattr(KnowCompTreeBoardTable, numerator_field)
        denominator_col = getattr(KnowCompTreeBoardTable, denominator_field)
        raw_data = db.session.query(
            KnowCompTreeBoardTable.date,
            KnowCompTreeBoardTable.field_name,
            numerator_col.label('numerator'),
            denominator_col.label('denominator')
        ).filter(
            KnowCompTreeBoardTable.date <= end_date_obj
        ).order_by(KnowCompTreeBoardTable.date.asc()).all()
        # 按field_name分组存储
        field_data_map = defaultdict(dict)
        for item in raw_data:
            if isinstance(item.date, (dt_date, datetime)):
                date_str = item.date.strftime("%Y-%m-%d")
            else:
                date_str = item.date
            num = item.numerator if item.numerator is not None else 0
            den = item.denominator if item.denominator is not None else 0
            field_data_map[item.field_name][date_str] = (num, den)
    else:
        target_field = f"{page_type}_{data_type}"
        if target_field not in column_names:
            return []
        target_col = getattr(KnowCompTreeBoardTable, target_field)
        raw_data = db.session.query(
            KnowCompTreeBoardTable.date,
            KnowCompTreeBoardTable.field_name,
            target_col.label('data')
        ).filter(
            KnowCompTreeBoardTable.date <= end_date_obj
        ).order_by(KnowCompTreeBoardTable.date.asc()).all()
        # 按field_name分组存储
        field_data_map = defaultdict(dict)
        for item in raw_data:
            if isinstance(item.date, (dt_date, datetime)):
                date_str = item.date.strftime("%Y-%m-%d")
            else:
                date_str = item.date
            field_data_map[item.field_name][date_str] = item.data if item.data is not None else 0
    # 处理每个field_name的数据，补全日期
    result = []
    for field_name, date_values in field_data_map.items():
        sorted_dates = sorted(date_values.keys())
        i = 0
        current_value = (0, 0) if is_ratio_type else 0
        for d in all_dates:
            d_str = d.strftime("%Y-%m-%d")
            # 双指针法：找到当前日期或之前的最新数据
            while i < len(sorted_dates) and sorted_dates[i] <= d_str:
                current_value = date_values[sorted_dates[i]]
                i += 1
            # 计算最终值
            if is_ratio_type:
                num, den = current_value
                value = pub.pub_get_ratio(num, den, 2) if den != 0 else 0
            else:
                value = float(current_value)
            result.append({
                "date": d_str,
                "field_name": field_name,
                "value": value
            })
    return result



def query_know_comp_tree_board_table_comp_tree_board_sum_list_twoday(start_date, end_date, page_type):
    """
    查询组件树看板指定开始和结束日期的所有指标对比数据

    Args:
        start_date: 开始日期，支持str("%Y-%m-%d")、date、datetime类型
        end_date: 结束日期，支持str("%Y-%m-%d")、date、datetime类型
        page_type: 页面类型，'comp'或'module'

    Returns:
        dict: 按field_name分组的对比数据，所有field_name都包含start_data和end_data
    """
    # 输入参数校验
    if page_type not in ['comp', 'module']:
        return {}
    
    # 日期类型统一转换为字符串（与数据库字段类型一致）
    def convert_to_date_str(date_input):
        if isinstance(date_input, str):
            try:
                datetime.strptime(date_input, "%Y-%m-%d")
                return date_input
            except ValueError:
                return None
        elif isinstance(date_input, (dt_date, datetime)):
            return date_input.strftime("%Y-%m-%d")
        else:
            return None
    
    start_date_str = convert_to_date_str(start_date)
    end_date_str = convert_to_date_str(end_date)
    
    if not start_date_str or not end_date_str or start_date_str > end_date_str:
        return {}
    
    # 定义公共字段和特殊字段映射
    common_fields = ['id', 'date', 'field_name', 'update_time']
    change_detail_db_name = f"{page_type}_change_detail"
    change_detail_metric_name = "change_detail"
    
    # 动态获取所有需要查询的列和名称映射
    prefix = f"{page_type}_"
    query_columns = []
    column_name_map = {}  # 数据库列名 -> 返回的字段名
    numeric_metric_names = []  # 数值类型指标名称
    
    # 先添加公共字段
    for field in common_fields:
        column = getattr(KnowCompTreeBoardTable, field)
        query_columns.append(column)
        column_name_map[field] = field
    
    # 再添加page_type对应的所有指标字段
    for column in KnowCompTreeBoardTable.__table__.columns:
        col_name = column.name
        
        # 处理change_detail特殊字段
        if col_name == change_detail_db_name:
            query_columns.append(column)
            column_name_map[col_name] = change_detail_metric_name
            continue
        
        # 处理其他带前缀的指标字段
        if col_name.startswith(prefix) and col_name not in common_fields:
            query_columns.append(column)
            metric_name = col_name[len(prefix):]
            column_name_map[col_name] = metric_name
            numeric_metric_names.append(metric_name)
    
    if len(query_columns) <= len(common_fields):
        return {}  # 没有找到任何指标字段
    
    # 定义类型转换函数（解决JSON序列化问题）
    def convert_to_json_serializable(value):
        """将非JSON可序列化类型转换为可序列化类型"""
        if isinstance(value, decimal.Decimal):
            return float(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, dt_date):
            return value.strftime("%Y-%m-%d")
        else:
            return value
    
    # 生成默认空数据（当没有找到任何历史数据时使用）
    def generate_default_data(field_name):
        """生成指定field_name的默认空数据"""
        default_data = {
            "id": None,
            "date": None,
            "field_name": field_name,
            "update_time": None,
            "change_detail": None
        }
        # 所有数值指标默认值为0
        for metric in numeric_metric_names:
            default_data[metric] = 0
        return default_data
    
    # ✅ 修复后的核心查询函数：获取所有field_name在指定日期或之前的最新数据
    def get_all_latest_data_before(target_date_str):
        """
        获取所有field_name在指定日期或之前的最新数据
        无论指定日期有没有数据，只要历史上有数据就会返回
        """
        # 查询所有date <= target_date_str的数据，按日期倒序排列
        all_data = db.session.query(
            *query_columns
        ).filter(
            KnowCompTreeBoardTable.date <= target_date_str
        ).order_by(
            KnowCompTreeBoardTable.date.desc()
        ).all()
        
        if not all_data:
            return {}
        
        # 按field_name分组，只保留每个field_name的最新一条数据
        result = {}
        for item in all_data:
            if item.field_name not in result:
                data = {}
                for db_col_name, return_name in column_name_map.items():
                    value = getattr(item, db_col_name)
                    
                    # 数值类型NULL转0，其他类型保持原值
                    if (return_name in numeric_metric_names and value is None):
                        data[return_name] = 0
                    else:
                        data[return_name] = convert_to_json_serializable(value)
                
                result[item.field_name] = data
        
        return result
    
    # 获取数据库中所有存在的field_name（确保不会遗漏任何领域）
    all_existing_fields = [
        row[0] for row in db.session.query(
            func.distinct(KnowCompTreeBoardTable.field_name)
        ).all()
        if row[0] is not None
    ]
    
    if not all_existing_fields:
        return {}
    
    # 分别获取开始日期和结束日期的所有field_name数据
    start_data_map = get_all_latest_data_before(start_date_str)
    end_data_map = get_all_latest_data_before(end_date_str)
    
    # 生成最终结果：所有field_name都包含start_data和end_data
    result = {}
    for field_name in all_existing_fields:
        # 获取开始日期数据，没有则使用默认值
        start_item = start_data_map.get(field_name, generate_default_data(field_name))
        # 获取结束日期数据，没有则使用默认值
        end_item = end_data_map.get(field_name, generate_default_data(field_name))
        
        # 计算差值（只计算数值指标）
        diff_metrics = {}
        for metric in numeric_metric_names:
            start_val = start_item.get(metric, 0)
            end_val = end_item.get(metric, 0)
            diff_metrics[metric] = float(end_val - start_val)
        
        result[field_name] = {
            "requested_start_date": start_date_str,
            "actual_start_date": start_item.get("date"),
            "requested_end_date": end_date_str,
            "actual_end_date": end_item.get("date"),
            "start_data": start_item,
            "end_data": end_item,
            "diff_metrics": diff_metrics
        }
    
    return result


def add_know_comp_tree_board_table_comp_tree_board_list(comp_tree_board_list):
    if len(comp_tree_board_list) == 0:
        return
    date = comp_tree_board_list[0].get("date")
    db.session.query(KnowCompTreeBoardTable).filter(KnowCompTreeBoardTable.date==date).delete()
    db.session.commit()
    for comp_tree_board_item in comp_tree_board_list:
        # 为列表中的每一项创建一个全新的数据库记录
        new_comp_tree_board_model = KnowCompTreeBoardTable(**comp_tree_board_item)
        db.session.add(new_comp_tree_board_model)
    db.session.commit()
