from collections import defaultdict
from datetime import datetime, timedelta, date as dt_date
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy import String, Column, DateTime, JSON, and_, desc, DECIMAL, func
from electric_knowledge.data_model import db
from knowledge_dashboard import pub
import decimal


class KnowFeatureTreePageTable(db.Model):
    """特性树页面明细表"""
    __bind_key__ = "db5"
    __tablename__ = "know_feature_tree_page_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    page_title = Column(String(256), nullable=True)
    field_name = Column(String(128), nullable=True)
    feature_num = Column(String(128), nullable=True)
    feature_name = Column(String(256), nullable=True)
    page_type_name = Column(String(128), nullable=True)
    type_flag = Column(String(16), nullable=True)
    is_sub_feature = Column(INTEGER, nullable=True, default=0)
    scheme_num = Column(INTEGER, nullable=True, default=0)
    page_url = Column(String(512), nullable=True)
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
    feature_engineering = Column(JSON, nullable=True)
    script_date = Column(String(128), nullable=True)

    def as_dict(self):
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if hasattr(value, '__float__'):
                result[c.name] = float(value) if value is not None else None
            else:
                result[c.name] = value
        return result


class KnowFeatureTreeBoardTable(db.Model):
    """特性树看板统计表"""
    __bind_key__ = "db5"
    __tablename__ = "know_feature_tree_board_table"
    id = Column(INTEGER(unsigned=True), autoincrement=True, primary_key=True, nullable=False)
    date = Column(String(128), nullable=True)
    field_name = Column(String(128), nullable=True)
    analysis_sum_num = Column(INTEGER, nullable=True)
    analysis_initial_num = Column(INTEGER, nullable=True)
    analysis_reviewed_num = Column(INTEGER, nullable=True)
    analysis_revision_num = Column(INTEGER, nullable=True)
    analysis_finish_num = Column(INTEGER, nullable=True)
    analysis_blank_num = Column(INTEGER, nullable=True)
    analysis_sum_editor_num = Column(INTEGER, nullable=True)
    analysis_sum_edit_num = Column(INTEGER, nullable=True)
    analysis_sum_view_visitor_num = Column(INTEGER, nullable=True)
    analysis_sum_view_visit_num = Column(INTEGER, nullable=True)
    analysis_sum_ai_adapt_num = Column(DECIMAL(10, 2), nullable=True)
    analysis_sum_ai_gene_num = Column(DECIMAL(10, 2), nullable=True)
    analysis_change_detail = Column(JSON, nullable=True)
    scheme_sum_num = Column(INTEGER, nullable=True)
    scheme_initial_num = Column(INTEGER, nullable=True)
    scheme_reviewed_num = Column(INTEGER, nullable=True)
    scheme_revision_num = Column(INTEGER, nullable=True)
    scheme_finish_num = Column(INTEGER, nullable=True)
    scheme_blank_num = Column(INTEGER, nullable=True)
    scheme_sum_editor_num = Column(INTEGER, nullable=True)
    scheme_sum_edit_num = Column(INTEGER, nullable=True)
    scheme_sum_view_visitor_num = Column(INTEGER, nullable=True)
    scheme_sum_view_visit_num = Column(INTEGER, nullable=True)
    scheme_sum_ai_adapt_num = Column(DECIMAL(10, 2), nullable=True)
    scheme_sum_ai_gene_num = Column(DECIMAL(10, 2), nullable=True)
    scheme_change_detail = Column(JSON, nullable=True)
    update_time = Column(nullable=True, server_default=func.now(), onupdate=func.now())

    def as_dict(self):
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if hasattr(value, '__float__'):
                result[c.name] = float(value) if value is not None else None
            else:
                result[c.name] = value
        return result


# ==================== Page Table 查询方法 ====================


def query_know_feature_tree_page_table_feature_tree_page_list_by_field_name_page_status_page_type(field_name, page_status, page_type):
    latest_script_date = db.session.query(KnowFeatureTreePageTable.script_date).distinct().order_by(
        KnowFeatureTreePageTable.script_date.desc()
    ).first()
    if not latest_script_date or not latest_script_date[0]:
        return []
    latest_date = latest_script_date[0]

    if page_status == "总数":
        if field_name == "波分中心":
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.script_date == latest_date
            ).all()
        else:
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.field_name == field_name,
                KnowFeatureTreePageTable.script_date == latest_date
            ).all()
    else:
        if field_name == "波分中心":
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.page_status == page_status,
                KnowFeatureTreePageTable.script_date == latest_date
            ).all()
        else:
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.field_name == field_name,
                KnowFeatureTreePageTable.page_status == page_status,
                KnowFeatureTreePageTable.script_date == latest_date
            ).all()

    data_list = []
    if page_type == "analysis":
        data_list = [item.as_dict() for item in model_list if item.page_type_name in ("特性分析", "子特性分析")]
    else:
        data_list = [item.as_dict() for item in model_list if item.page_type_name in ("特性方案", "子特性方案")]
    return data_list


def query_know_feature_tree_page_table_feature_tree_page_list_by_field_name_page_status_page_type_script_date(field_name, page_type, page_status, script_date):
    if page_status == "总数":
        if field_name == "波分中心":
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.script_date == script_date
            ).all()
        else:
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.field_name == field_name,
                KnowFeatureTreePageTable.script_date == script_date
            ).all()
    else:
        if field_name == "波分中心":
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.page_status == page_status,
                KnowFeatureTreePageTable.script_date == script_date
            ).all()
        else:
            model_list = db.session.query(KnowFeatureTreePageTable).filter(
                KnowFeatureTreePageTable.field_name == field_name,
                KnowFeatureTreePageTable.page_status == page_status,
                KnowFeatureTreePageTable.script_date == script_date
            ).all()

    data_list = []
    if page_type == "analysis":
        data_list = [item.as_dict() for item in model_list if item.page_type_name in ("特性分析", "子特性分析")]
    else:
        data_list = [item.as_dict() for item in model_list if item.page_type_name in ("特性方案", "子特性方案")]
    return data_list


def update_know_feature_tree_page_table_feature_tree_page_list(feature_tree_page_list):
    script_date = feature_tree_page_list[0].get("script_date")
    db.session.query(KnowFeatureTreePageTable).filter(KnowFeatureTreePageTable.script_date == script_date).delete()
    db.session.commit()
    for feature_tree_page_item in feature_tree_page_list:
        new_feature_tree_page_model = KnowFeatureTreePageTable(**feature_tree_page_item)
        db.session.add(new_feature_tree_page_model)
    db.session.commit()


# ==================== Board Table 查询方法 ====================


def query_know_feature_tree_board_table_latest_feature_tree_board_list():
    latest_dates = db.session.query(KnowFeatureTreeBoardTable.date).distinct().order_by(
        KnowFeatureTreeBoardTable.date.desc()
    ).limit(2).all()

    if not latest_dates or len(latest_dates) == 0:
        return []

    latest_date = latest_dates[0][0]
    previous_date = latest_dates[1][0] if len(latest_dates) > 1 else None

    latest_records = db.session.query(KnowFeatureTreeBoardTable).filter(
        KnowFeatureTreeBoardTable.date == latest_date
    ).all()

    previous_records = {}
    if previous_date:
        previous_records_list = db.session.query(KnowFeatureTreeBoardTable).filter(
            KnowFeatureTreeBoardTable.date == previous_date
        ).all()
        previous_records = {record.field_name: record for record in previous_records_list}

    result = []
    for record in latest_records:
        record_dict = record.as_dict()
        record_dict['_latest_date'] = latest_date
        record_dict['_previous_date'] = previous_date

        if record.field_name in previous_records:
            prev_record = previous_records[record.field_name]
            record_dict['_previous_data'] = prev_record.as_dict()
        else:
            record_dict['_previous_data'] = None

        result.append(record_dict)

    return result


def query_know_feature_tree_board_table_feature_tree_board_sum_detail_list(field_name, page_type, date):
    record = db.session.query(KnowFeatureTreeBoardTable).filter(
        KnowFeatureTreeBoardTable.field_name == field_name,
        KnowFeatureTreeBoardTable.date == date
    ).first()
    if not record:
        return []
    if page_type == 'analysis':
        change_detail = record.analysis_change_detail
    else:
        change_detail = record.scheme_change_detail
    if not change_detail:
        return []
    return change_detail


def query_know_feature_tree_board_table_feature_tree_board_sum_list_everyday(start_date, end_date, page_type, data_type):
    if page_type not in ['analysis', 'scheme'] or not data_type:
        return []

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

    ratio_mapping = {
        'finish_rate': ('finish_num', 'sum_num'),
    }
    is_ratio_type = data_type in ratio_mapping

    all_dates = [start_date_obj + timedelta(days=i)
                 for i in range((end_date_obj - start_date_obj).days + 1)]

    column_names = {c.name for c in KnowFeatureTreeBoardTable.__table__.columns}

    if is_ratio_type:
        numerator_suffix, denominator_suffix = ratio_mapping[data_type]
        numerator_field = f"{page_type}_{numerator_suffix}"
        denominator_field = f"{page_type}_{denominator_suffix}"

        if numerator_field not in column_names or denominator_field not in column_names:
            return []

        numerator_col = getattr(KnowFeatureTreeBoardTable, numerator_field)
        denominator_col = getattr(KnowFeatureTreeBoardTable, denominator_field)

        raw_data = db.session.query(
            KnowFeatureTreeBoardTable.date,
            KnowFeatureTreeBoardTable.field_name,
            numerator_col.label('numerator'),
            denominator_col.label('denominator')
        ).filter(
            KnowFeatureTreeBoardTable.date <= end_date_obj
        ).order_by(KnowFeatureTreeBoardTable.date.asc()).all()

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

        target_col = getattr(KnowFeatureTreeBoardTable, target_field)

        raw_data = db.session.query(
            KnowFeatureTreeBoardTable.date,
            KnowFeatureTreeBoardTable.field_name,
            target_col.label('data')
        ).filter(
            KnowFeatureTreeBoardTable.date <= end_date_obj
        ).order_by(KnowFeatureTreeBoardTable.date.asc()).all()

        field_data_map = defaultdict(dict)
        for item in raw_data:
            if isinstance(item.date, (dt_date, datetime)):
                date_str = item.date.strftime("%Y-%m-%d")
            else:
                date_str = item.date
            field_data_map[item.field_name][date_str] = item.data if item.data is not None else 0

    result = []
    for field_name, date_values in field_data_map.items():
        sorted_dates = sorted(date_values.keys())
        i = 0
        current_value = (0, 0) if is_ratio_type else 0

        for d in all_dates:
            d_str = d.strftime("%Y-%m-%d")

            while i < len(sorted_dates) and sorted_dates[i] <= d_str:
                current_value = date_values[sorted_dates[i]]
                i += 1

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


def query_know_feature_tree_board_table_feature_tree_board_sum_list_twoday(start_date, end_date, page_type):
    if page_type not in ['analysis', 'scheme']:
        return {}

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

    common_fields = ['id', 'date', 'field_name', 'update_time']
    change_detail_db_name = f"{page_type}_change_detail"
    change_detail_metric_name = "change_detail"

    prefix = f"{page_type}_"
    query_columns = []
    column_name_map = {}
    numeric_metric_names = []

    for field in common_fields:
        column = getattr(KnowFeatureTreeBoardTable, field)
        query_columns.append(column)
        column_name_map[field] = field

    for column in KnowFeatureTreeBoardTable.__table__.columns:
        col_name = column.name

        if col_name == change_detail_db_name:
            query_columns.append(column)
            column_name_map[col_name] = change_detail_metric_name
            continue

        if col_name.startswith(prefix) and col_name not in common_fields:
            query_columns.append(column)
            metric_name = col_name[len(prefix):]
            column_name_map[col_name] = metric_name
            numeric_metric_names.append(metric_name)

    if len(query_columns) <= len(common_fields):
        return {}

    def convert_to_json_serializable(value):
        if isinstance(value, decimal.Decimal):
            return float(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, dt_date):
            return value.strftime("%Y-%m-%d")
        else:
            return value

    def generate_default_data(field_name):
        default_data = {
            "id": None,
            "date": None,
            "field_name": field_name,
            "update_time": None,
            "change_detail": None
        }
        for metric in numeric_metric_names:
            default_data[metric] = 0
        return default_data

    def get_all_latest_data_before(target_date_str):
        all_data = db.session.query(
            *query_columns
        ).filter(
            KnowFeatureTreeBoardTable.date <= target_date_str
        ).order_by(
            KnowFeatureTreeBoardTable.date.desc()
        ).all()

        if not all_data:
            return {}

        result = {}
        for item in all_data:
            if item.field_name not in result:
                data = {}
                for db_col_name, return_name in column_name_map.items():
                    value = getattr(item, db_col_name)

                    if (return_name in numeric_metric_names and value is None):
                        data[return_name] = 0
                    else:
                        data[return_name] = convert_to_json_serializable(value)

                result[item.field_name] = data

        return result

    all_existing_fields = [
        row[0] for row in db.session.query(
            func.distinct(KnowFeatureTreeBoardTable.field_name)
        ).all()
        if row[0] is not None
    ]

    if not all_existing_fields:
        return {}

    start_data_map = get_all_latest_data_before(start_date_str)
    end_data_map = get_all_latest_data_before(end_date_str)

    result = {}
    for field_name in all_existing_fields:
        start_item = start_data_map.get(field_name, generate_default_data(field_name))
        end_item = end_data_map.get(field_name, generate_default_data(field_name))

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


def add_know_feature_tree_board_table_feature_tree_board_list(feature_tree_board_list):
    if len(feature_tree_board_list) == 0:
        return
    date = feature_tree_board_list[0].get("date")
    db.session.query(KnowFeatureTreeBoardTable).filter(KnowFeatureTreeBoardTable.date == date).delete()
    db.session.commit()
    for feature_tree_board_item in feature_tree_board_list:
        new_feature_tree_board_model = KnowFeatureTreeBoardTable(**feature_tree_board_item)
        db.session.add(new_feature_tree_board_model)
    db.session.commit()


def parse_date_safe(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def to_date_obj(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return None
    return val
