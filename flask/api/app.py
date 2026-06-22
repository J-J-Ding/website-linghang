# app.py
import os
import json
from flask import Flask, request, jsonify
from flask.json.provider import DefaultJSONProvider, JSONProvider
from flask_cors import CORS
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

from urllib.parse import quote_plus  # 用于编码特殊字符
from datetime import datetime, date
import log_config 
app = Flask(__name__)


from api_login import Login, API_Visit_set, API_Visit_get
from api_chat import Ask, Chat, Agent, Sse, Template, History, API_History_chat_get, API_Prompt_set, API_Prompt_get, API_Prompt_del, API_Chat_ai_pvuv_get, API_Chat_visit_pvuv_get, API_Chat_history_ai_get, API_Chat_history_visit_get
from api_test import Receive_message, Send_message, Handle_submit  # 导入 chat 函数
from api_data import Table_read, Table_write, Menu_read, Rdc_list_read, API_Icenter_block_set, API_Feature_read, API_Board_read, API_Component_read, API_Board_get, API_Board_set, API_Board_del, API_Table_get, API_Table_set, API_Table_del, API_Table_update_stats, feature_set, get_rdc_component, write_rdc_component, refresh_task
from componentTree.api_component_tree import API_Knowledge_component_tree, API_Knowledge_component_detail, API_Knowledge_component_tree_refresh
from componentTree.api_component_graph import (
    API_Knowledge_component_graph_get,
    API_Knowledge_component_graph_expand,
    API_Knowledge_component_graph_detail,
    API_Knowledge_component_graph_layout_save,
    API_Knowledge_component_graph_layout_list,
    API_Knowledge_component_graph_refresh,
    API_Knowledge_component_graph_stats
)
from featureTreeNew.api_feature_tree import API_Knowledge_feature_tree, API_Knowledge_feature_detail, API_Knowledge_feature_tree_refresh
from featureTreeNew.api_feature_graph import API_Knowledge_feature_graph_get, API_Knowledge_feature_graph_refresh
from componentTree.data_model import KNOWLEDGE_COMPONENT_TREE
from componentTree.db_config import DB_DATABASE_KNOWLEDGE_ENGINEERING, DB_USER, DB_PASSWORD, DB_PORT
from knowledge_dashboard.db_config import DB_DATABASE_KNOW_BOARD, DB_USER, DB_PASSWORD, DB_PORT
from knowledge_dashboard.know_controller import query_comp_tree_board_graph_sum_data_dict, query_comp_tree_board_table_sum_data_dict, query_comp_tree_board_table_cumulative_detail_list, query_comp_tree_board_table_change_detail_list
from feature_dashboard.feature_controller import query_feature_tree_board_graph_sum_data_dict, query_feature_tree_board_table_sum_data_dict, query_feature_tree_board_table_cumulative_detail_list, query_feature_tree_board_table_change_detail_list

from api_design import API_Design_set, API_Design_batch_set, API_Design_get, API_Design_delete, API_Scene_set, API_Scene_get, API_Scene_delete, API_Scene_update, API_Performance_set, API_Performance_get, API_Fault_set, API_Fault_get
from agent_component import API_Component_status_get

from electric_knowledge.ai_application import process_request_dot_r001, process_request_dot_r002, process_request_split_r003, process_request_split_r004, process_request_split_r005, process_request_split_r006, process_request_split_r007, process_query_board_all_feature_rdc_status, process_query_board_slice_feature_rdc_status, process_query_board_key_changed_content, process_query_board_key_changed_feature, process_query_supported_change_mode_and_affected_features, process_dot_to_board_recommendation

from electric_knowledge.front_business_coreelement_factor_relation_data_service import db, queryCoreElementFactorRelationByParams, queryCoreElementFactorRelationTree, queryCoreElementFactorRelationStatusList, queryCoreElementFactorRelationCoreElementList, queryCoreElementFactorRelationFactorList, queryCoreElementFactorRelationFactorValueSrcList, queryCoreElementFactorRelationFactorValueList, addCoreElementFactorRelationData, updateCoreElementFactorRelationData, deleteCoreElementFactorRelationData, importExcelCoreElementFactorRelationData, queryCoreElementFactorValueDict, updateSourceCoreElementFactorRelationData
from electric_knowledge.front_business_speed_type_relation_data_service import queryBusinessSpeedTypeTree, queryBusinessSpeedTypeByParams, queryBusinessSpeedTypeStatusList, queryBusinessSpeedTypeBusinessSpeedList, queryBusinessSpeedTypeBusinessTypeList, addBusinessSpeedTypeData, updateBusinessSpeedTypeData, deleteBusinessSpeedTypeData, importExcelbaseBusinessSpeedTypeData
from electric_knowledge.front_board_atom_model_relation_data_service import queryBoardBusinessAtomTree, queryBoardBusinessAtomByParams, queryBoardBusinessAtomBoardBusinessTypeList, queryBoardBusinessAtomBoardBusinessList, queryBoardBusinessAtomStatusList, addBoardBusinessAtomData, updateBoardBusinessAtomData, deleteBoardBusinessAtomData, importExcelBoardAtomModelData
from electric_knowledge.front_board_group_model_relation_data_service import queryBoardBusinessGroupTree, queryBoardBusinessGroupByParams, queryBoardBusinessGroupBoardBusinessTypeList, queryBoardBusinessGroupBoardBusinessList, queryBoardBusinessGroupStatusList, addBoardBusinessGroupData, updateBoardBusinessGroupData, deleteBoardBusinessGroupData, importExcelBoardGroupModelData
from electric_knowledge.front_net_business_model_data_service import queryNetBusinessTree, queryNetBusinessByParams, queryNetBusinessNetBusinessSchemeList, queryNetBusinessNetBusinessModelList, queryNetBusinessBusinessTypeList, queryNetBusinessCrossTypeList, queryNetBusinessBoardBusinessModelList, queryNetBusinessStatusList , addNetBusinessData, updateNetBusinessData, deleteNetBusinessData, importExcelbaseNetBusinessData
from electric_knowledge.front_feature_relation_data_service import queryFeatureTreeTree, queryFeatureTreeByParams, queryFeatureTreeStatusList, queryFeatureTreeFeatureFirstTypeList, queryFeatureTreeFeatureSecondTypeList, queryFeatureTreeFeatureList, queryFeatureTreeSubFeatureList, addFeatureRelationData, updateFeatureRelationData, deleteFeatureRelationData, importExcelFeatureRelationData, addFeatureIcenterPage, deleteFeatureIcenterPage, syncFeatureIcenterPage, updateFeatureIcenterPage
from electric_knowledge.front_feature_board_relation_data_service import  queryFeatureBoardTree, queryFeatureInfoDict, queryFeatureBoardByParams, queryFeatureBoardStatusList, queryFeatureBoardBoardList,  updateFeatureBoardData, importExcelFeatureBoardData
from electric_knowledge.front_feature_change_relation_data_service import importExcelFeatureChangeData
from electric_knowledge.front_board_tree_data_service import queryBoardTreeByParams, queryBoardTreeFactorList, queryBoardTreeFactorValueDict, importExcelBoardTreeData, createRDC, queryRDC, addBoardTreeData, updateBoardTreeData, deleteBoardTreeData, addBoardIcenterPage, updateBoardIcenterPage, syncBoardIcenterPage
from electric_knowledge.front_subrack_tree_data_service import queryShelfTreeByParams, queryShelfTreeFactorList, queryShelfTreeFactorValueDict, importExcelShelfTreeData, addShelfTreeData, updateShelfTreeData, deleteShelfTreeData
from electric_knowledge.front_board_change_analysis_data_service import importExcelBoardChangeAnalysisData
from electric_knowledge.front_board_components_tree_data_service import queryBoardComponentsTreeByParams, queryBoardPartTreeTree, queryBoardComponentsTreeStatusList, queryBoardPartTreePartList, queryBoardPartTreeBusinessSchemeList, queryBoardPartTreeSchemeSliceList, importExcelBoardComponentsTreeData, addBoardComponentsTreeData, updateBoardComponentsTreeData, deleteBoardComponentsTreeData
from electric_knowledge.front_board_whole_status_data_service import  queryBoardGlobalStatusByParams, querySimpleBoardGlobalStatusTree, queryBoardGlobalStatusTree, queryBoardGlobalStatusBoardList, addBoardWholeStatusData, updateBoardWholeStatusData, queryBoardGlobalStatusRdcFilterDataDict, syncBoardWholeStatusDataRDC, importExcelbaseBoardWholeStatusData, importOldBoardWholeStatusData
from electric_knowledge.front_rdc_fault_data_service import queryRdcFaultByRdcIdent
from electric_knowledge.split_r007_board_global_status import add_board_whole_st_data, add_new_part_update_change_analysis_data, update_board_whole_st_data, update_change_analysis_data, query_fault_list_by_feature, query_rdc_list_by_board_name_and_preplan_version, get_rdc_split_task_result_dict, query_board_new_features, add_new_feature_update_change_analysis_data
from electric_knowledge.split_r008_board_fs_rd_status import get_board_all_feature_rdc_status,get_board_slice_feature_rdc_status,get_board_key_changed_feature
from electric_knowledge.front_subrack_components_tree_data_service import queryShelfPartTreeProductList, queryShelfPartTreeShelfTypeList,  queryShelfPartTreeTree, queryShelfPartTreeStatusList, queryShelfPartTreeByParams, queryShelfPartTreePartList, queryShelfPartTreeBusinessSchemeList, queryShelfPartTreeSchemeSliceList, addShelfPartTreeData, updateShelfPartTreeData, deleteShelfPartTreeData, importExcelShelfPartTreeData
from electric_knowledge.front_old_children_feature_data_service import importExcelOldChildrenFeatureData
from electric_knowledge.product_image_data_service import get_image, upload_image
from electric_knowledge.req_manage_agent import service_add_req_manage_agent_single_chat_record, service_get_history_chat_record_list, service_get_prompt_list_by_search_str, \
service_update_single_prompt_content, service_update_single_prompt_reference_count, service_del_single_prompt, service_get_tool_name_list
from electric_knowledge.req_manage_board_api import service_update_pr_info_list, service_del_pr_info_list_by_script_update_date, service_update_req_manage_board_pr_split_summary_data_list, service_query_req_manage_board_pr_split_summary_line_data_list_by_preplanning_and_date, \
service_query_req_manage_board_pr_split_summary_table_data_list_by_preplanning_and_date, service_query_preplanning_list, service_query_req_manage_board_pr_split_detail_table_data_list_by_preplanning_and_date, service_update_req_manage_check_pr_info_table_check_pr_info_list, \
service_update_req_manage_check_pr_info_table_handle_pr_info_list, service_query_req_manage_check_pr_info_table_by_filter_dict, service_query_req_manage_check_pr_info_table_value_dict_by_field_list, \
service_update_req_manage_check_pr_info_table_cal_field, service_update_req_manage_check_pr_summary_table_data_list, service_query_req_manage_check_pr_summary_table_by_date_range_and_preplanning, \
service_update_req_manage_check_pr_info_table_man_fields_by_id_list
from electric_knowledge.front_hardware_tree_rule_data_service import query_hardware_tree_rule_dict_by_situation
from requirement_schedule.requirement_schedule import queryRequirementScheduleByParams, updateRequirementSchedule, getFilterHistory, saveFilterHistory, checkEditPermission, syncRdcData, autoScheduling, previewBackfillRdcData, backfillRdcData
from requirement_schedule.person_skill_map import queryPersonSkillMapByParams, createPersonSkillMap, updatePersonSkillMap, deletePersonSkillMap, getPersonSkillMapOptions, importPersonSkillMap, exportPersonSkillMap
from electric_knowledge.db_config import DB_HOST, DB_HOST2, DB_USER, DB_PASSWORD, DB_DATABASE, DB_DATABASE2, DB_PORT

# 审核管理API导入
from electric_knowledge.approval_service import submit_change, batch_approve, single_approve, revoke, get_my_pending, get_my_submitted, get_detail, admin_list, get_biz_config_list


from quality.quality_case_service import query_all_quality_case_list_by_param

from deal_health import parse_health_log, get_sample_data, execute_online_diagnosis, getjumpservers,get_batch_kpi_logs, analyze_batch_kpi_logs, get_batch_analysis_status,get_kpi_detail_data,export_ssd_life_data
from ai_health import Agent_health, Agent_health_sync

from issueImpacte.db_config import DB_DATABASE_WH
from requirement_schedule.db_config import DB_DATABASE_REQUIREMENT_SCHEDULE, DB_USER, DB_PASSWORD, DB_PORT
from issueImpacte.issue_impact_service import query_issue_impact_case_list,create_issue_impact_case,update_issue_impact_case,delete_issue_impact_case,import_issue_impact_case_batch,confirm_case_source

from boardAssembly.board_assembly_api import generate_elements, generate_framework, generate_config, get_board_names, get_business_models, handle_options
from electric_knowledge.front_board_board_data_dictionary import import_board_data_dictionary_to_knowledge_base
from electric_knowledge.front_mr_feature_data_service import importExcelMrFeatureData
from electric_knowledge.front_board_opt_biz_data_service import queryBoardOptBizByParams, importExcelBoardOptBizData
from electric_knowledge.module_featurecheckpoint_content_data_service import queryModuleFeaturecheckpointContentDataByParams, importExcelModuleFeaturecheckpointContentData


# 在 app.run() 之前调用配置函数

class CustomJSONEncoder(json.JSONEncoder):
    """核心自定义编码器"""
    def default(self, o):
        if isinstance(o, datetime):
            # 使用您需要的格式：YYYY-MM-DD HH:MM:SS
            return o.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(o)

class CustomJSONProvider(JSONProvider):
    """确保jsonify使用自定义编码器"""
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)
    
    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


app.json = CustomJSONProvider(app)
# CORS 配置 - 允许跨域请求
cors_origins = [
    'http://10.90.178.249:3002', 'http://localhost:3002','http://local.zte.com.cn:3002','http://10.56.195.211:3002', 'http://10.80.176.64:3011',  'http://10.239.69.183:3011',
    'http://10.80.176.53:3002','http://10.80.176.64:3002','http://10.239.69.183:5020/login','http://10.239.69.183:5020/visits','http://10.239.69.183:5020',
    'http://10.90.166.68:3002','http://10.239.69.183:7002','http://10.239.69.183:9002','http://10.239.69.30:9002', 'http://10.239.69.183:3002',
    'http://10.239.69.30:3002', 'http://10.90.175.164:3002', 'http://10.90.251.221:3002','http://wsit.zx.zte.com.cn:3002',
    'https://wsit.zx.zte.com.cn','https://wsit.zx.zte.com.cn:3002','http://10.239.69.191:3000', 'http://10.80.173.91:3002',
    'http://10.80.176.48:3002', 'http://10.239.69.183:3032', 'https"//i.zte.com.cn'
]

# 使用全局 CORS 配置，确保所有路由都能正确处理预检请求
# Flask-CORS 会自动处理 OPTIONS 预检请求和 CORS 头
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'x-user-name', 'x-emp-no', 'x-auth-value'],
     supports_credentials=True,
     automatic_options=True,
     max_age=3600)


# 动态生成 swagger.json
@app.route("/swagger.json")
def swagger_spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Flask API"
    return jsonify(swag)

# 配置 Swagger UI
SWAGGER_URL = '/docs'  # 文档访问路径
API_URL = '/swagger.json'  # 动态生成的 JSON 文件路径

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Flask API 文档"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

encoded_password = quote_plus(DB_PASSWORD)
# DB_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

DB1_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?connect_timeout=60",
    'bind_key': 'db1'
}

DB2_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST2}:{DB_PORT}/{DB_DATABASE2}",
    'bind_key': 'db2'
}
DB3_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE_WH}",
    'bind_key': 'db3'
}
DB4_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE_REQUIREMENT_SCHEDULE}",
    'bind_key': 'db4'
}
DB5_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE_KNOWLEDGE_ENGINEERING}",
    'bind_key': 'db5'
}
DB6_CONFIG = {
    'url': f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_DATABASE_KNOW_BOARD}",
    'bind_key': 'db6'
}

# Flask-SQLAlchemy配置
app.config['SQLALCHEMY_DATABASE_URI'] = DB1_CONFIG['url']
app.config['SQLALCHEMY_BINDS'] = {
    DB1_CONFIG['bind_key']: DB1_CONFIG['url'],
    DB2_CONFIG['bind_key']: DB2_CONFIG['url'],
    DB3_CONFIG['bind_key']: DB3_CONFIG['url'],
    DB4_CONFIG['bind_key']: DB4_CONFIG['url'],
    DB5_CONFIG['bind_key']: DB5_CONFIG['url'],
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
env = os.environ
app.config['UPLOAD_FOLDER'] = '/otn_ai/' + env.get("IMAGE_ENV","") + '/gzj/uploads' if env.get("IMAGE_ENV","") else './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
app.config['IMAGE_BASE_URL'] = '/api/images/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)


# Test模块路由
app.route('/api/api_test/Receive_message', methods=['POST'])(Receive_message)
app.route('/api/api_test/Send_message', methods=['GET'])(Send_message)
app.route('/api/api_test/Handle_submit', methods=['POST'])(Handle_submit)

# Chat模块路由
app.route('/api/api_chat/Ask', methods=['POST'])(Ask)
app.route('/api/api_chat/Chat', methods=['POST'])(Chat)
app.route('/api/api_chat/Agent', methods=['POST'])(Agent)
app.route('/api/api_chat/Sse', methods=['GET'])(Sse)
app.route('/api/api_chat/Template', methods=['GET'])(Template)
app.route('/api/api_chat/History', methods=['GET'])(History)
app.route('/api/api_chat/API_History_chat_get', methods=['POST'])(API_History_chat_get)
app.route('/api/api_chat/API_Prompt_set', methods=['POST'])(API_Prompt_set)
app.route('/api/api_chat/API_Prompt_get', methods=['POST'])(API_Prompt_get)
app.route('/api/api_chat/API_Prompt_del', methods=['POST'])(API_Prompt_del)
app.route('/api/api_chat/API_Chat_ai_pvuv_get', methods=['POST'])(API_Chat_ai_pvuv_get)
app.route('/api/api_chat/API_Chat_visit_pvuv_get', methods=['POST'])(API_Chat_visit_pvuv_get)

app.route('/api/api_chat/API_Chat_history_ai_get', methods=['POST'])(API_Chat_history_ai_get)
app.route('/api/api_chat/API_Chat_history_visit_get', methods=['POST'])(API_Chat_history_visit_get)

app.route('/api/api_chat/Agent_health', methods=['POST'])(Agent_health)
app.route('/api/api_chat/Agent_health_sync', methods=['POST'])(Agent_health_sync)

# Login模块路由
app.route('/api/api_login/Login', methods=['POST'])(Login)
app.route('/api/api_login/API_Visit_set', methods=['POST'])(API_Visit_set)
app.route('/api/api_login/API_Visit_get', methods=['GET'])(API_Visit_get)

# Data模版路由
app.route('/api/api_data/Table_read', methods=['POST'])(Table_read)
app.route('/api/api_data/Table_write', methods=['POST'])(Table_write)
app.route('/api/api_data/Menu_read', methods=['GET'])(Menu_read)
app.route('/api/api_data/Rdc_list_read', methods=['GET'])(Rdc_list_read)
app.route('/api/api_data/API_Icenter_block_set', methods=['POST'])(API_Icenter_block_set)
app.route('/api/api_data/API_Feature_read', methods=['POST'])(API_Feature_read)
app.route('/api/api_data/API_Board_read', methods=['POST'])(API_Board_read)
app.route('/api/api_data/API_Component_read', methods=['POST'])(API_Component_read)
app.route('/api/api_data/API_Board_get', methods=['POST'])(API_Board_get)
app.route('/api/api_data/API_Board_set', methods=['POST'])(API_Board_set)
app.route('/api/api_data/API_Board_del', methods=['POST'])(API_Board_del)
app.route('/api/api_data/API_Table_get', methods=['POST'])(API_Table_get)
app.route('/api/api_data/API_Table_set', methods=['POST'])(API_Table_set)
app.route('/api/api_data/API_Table_del', methods=['POST'])(API_Table_del)
app.route('/api/api_data/API_Table_update_stats', methods=['POST'])(API_Table_update_stats)
app.route('/api/api_data/feature_set', methods=['POST'])(feature_set)
app.route('/api/api_data/get_rdc_component', methods=['POST'])(get_rdc_component)
app.route('/api/api_data/write_rdc_component', methods=['POST'])(write_rdc_component)
app.route('/api/api_data/refresh_task', methods=['GET'])(refresh_task)
app.route('/api/api_data/API_Knowledge_component_tree', methods=['POST'])(API_Knowledge_component_tree)
app.route('/api/api_data/API_Knowledge_component_detail', methods=['POST'])(API_Knowledge_component_detail)
app.route('/api/api_data/API_Knowledge_component_tree_refresh', methods=['POST'])(API_Knowledge_component_tree_refresh)
# 组件知识图谱 API 路由
app.route('/api/api_data/API_Knowledge_component_graph_get', methods=['POST'])(API_Knowledge_component_graph_get)
app.route('/api/api_data/API_Knowledge_component_graph_expand', methods=['POST'])(API_Knowledge_component_graph_expand)
app.route('/api/api_data/API_Knowledge_component_graph_detail', methods=['POST'])(API_Knowledge_component_graph_detail)
app.route('/api/api_data/API_Knowledge_component_graph_layout_save', methods=['POST'])(API_Knowledge_component_graph_layout_save)
app.route('/api/api_data/API_Knowledge_component_graph_layout_list', methods=['POST'])(API_Knowledge_component_graph_layout_list)
app.route('/api/api_data/API_Knowledge_component_graph_refresh', methods=['POST'])(API_Knowledge_component_graph_refresh)
app.route('/api/api_data/API_Knowledge_component_graph_stats', methods=['POST'])(API_Knowledge_component_graph_stats)

# 新版特性树 API 路由
app.route('/api/api_data/API_Knowledge_feature_tree', methods=['POST'])(API_Knowledge_feature_tree)
app.route('/api/api_data/API_Knowledge_feature_detail', methods=['POST'])(API_Knowledge_feature_detail)
app.route('/api/api_data/API_Knowledge_feature_tree_refresh', methods=['POST'])(API_Knowledge_feature_tree_refresh)
app.route('/api/api_data/API_Knowledge_feature_graph_get', methods=['POST'])(API_Knowledge_feature_graph_get)
app.route('/api/api_data/API_Knowledge_feature_graph_refresh', methods=['POST'])(API_Knowledge_feature_graph_refresh)

# 需求树 API 路由
from requirementsTree.api_requirement_tree import (
    API_Knowledge_requirement_tree,
    API_Knowledge_requirement_tree_refresh,
    API_Knowledge_requirement_graph_get,
    API_Knowledge_requirement_graph_expand,
    API_Knowledge_requirement_graph_detail,
    API_Knowledge_requirement_graph_layout_save,
    API_Knowledge_requirement_graph_layout_list,
    API_Knowledge_requirement_graph_refresh,
    API_Knowledge_requirement_graph_stats,
    API_Knowledge_requirement_tree_group_detail,
)
app.route('/api/api_data/API_Knowledge_requirement_tree', methods=['POST'])(API_Knowledge_requirement_tree)
app.route('/api/api_data/API_Knowledge_requirement_tree_refresh', methods=['POST'])(API_Knowledge_requirement_tree_refresh)
app.route('/api/api_data/API_Knowledge_requirement_graph_get', methods=['POST'])(API_Knowledge_requirement_graph_get)
app.route('/api/api_data/API_Knowledge_requirement_graph_expand', methods=['POST'])(API_Knowledge_requirement_graph_expand)
app.route('/api/api_data/API_Knowledge_requirement_graph_detail', methods=['POST'])(API_Knowledge_requirement_graph_detail)
app.route('/api/api_data/API_Knowledge_requirement_graph_layout_save', methods=['POST'])(API_Knowledge_requirement_graph_layout_save)
app.route('/api/api_data/API_Knowledge_requirement_graph_layout_list', methods=['POST'])(API_Knowledge_requirement_graph_layout_list)
app.route('/api/api_data/API_Knowledge_requirement_graph_refresh', methods=['POST'])(API_Knowledge_requirement_graph_refresh)
app.route('/api/api_data/API_Knowledge_requirement_graph_stats', methods=['POST'])(API_Knowledge_requirement_graph_stats)
app.route('/api/api_data/API_Knowledge_requirement_tree_group_detail', methods=['POST'])(API_Knowledge_requirement_tree_group_detail)

# 组件功能设计助手模块路由
app.route('/api/api_data/API_Design_get', methods=['GET'])(API_Design_get)
app.route('/api/api_data/API_Design_set', methods=['POST'])(API_Design_set)
app.route('/api/api_data/API_Design_batch_set', methods=['POST'])(API_Design_batch_set)
app.route('/api/api_data/API_Design_delete', methods=['POST'])(API_Design_delete)
app.route('/api/api_data/API_Scene_set', methods=['POST'])(API_Scene_set)
app.route('/api/api_data/API_Scene_get', methods=['GET'])(API_Scene_get)
app.route('/api/api_data/API_Scene_delete', methods=['POST'])(API_Scene_delete)
app.route('/api/api_data/API_Scene_update', methods=['POST'])(API_Scene_update)
app.route('/api/api_data/API_Performance_set', methods=['POST'])(API_Performance_set)
app.route('/api/api_data/API_Performance_get', methods=['GET'])(API_Performance_get)
app.route('/api/api_data/API_Fault_set', methods=['POST'])(API_Fault_set)
app.route('/api/api_data/API_Fault_get', methods=['GET'])(API_Fault_get)
# app.route('/api/server_update/API_Config_update', methods=['POST'])(API_Config_update)

# 组件状态路由
app.route('/api/agent_component/API_Component_status_get', methods=['POST'])(API_Component_status_get)

# 知识看板 - 组件树统计
app.route('/know/query_comp_tree_board_graph_sum_data_dict/', methods=['GET'])(query_comp_tree_board_graph_sum_data_dict)
app.route('/know/query_comp_tree_board_table_sum_data_dict/', methods=['GET'])(query_comp_tree_board_table_sum_data_dict)
app.route('/know/query_comp_tree_board_table_cumulative_detail_list/', methods=['GET'])(query_comp_tree_board_table_cumulative_detail_list)
app.route('/know/query_comp_tree_board_table_change_detail_list/', methods=['GET'])(query_comp_tree_board_table_change_detail_list)

# 知识看板 - 特性树统计
app.route('/know/query_feature_tree_board_graph_sum_data_dict/', methods=['GET'])(query_feature_tree_board_graph_sum_data_dict)
app.route('/know/query_feature_tree_board_table_sum_data_dict/', methods=['GET'])(query_feature_tree_board_table_sum_data_dict)
app.route('/know/query_feature_tree_board_table_cumulative_detail_list/', methods=['GET'])(query_feature_tree_board_table_cumulative_detail_list)
app.route('/know/query_feature_tree_board_table_change_detail_list/', methods=['GET'])(query_feature_tree_board_table_change_detail_list)

# 电层知识管理
# 业务模型-光口业务速率&业务类型
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeTree', methods=['GET'])(queryBusinessSpeedTypeTree)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeByParams', methods=['GET'])(queryBusinessSpeedTypeByParams)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeStatusList', methods=['GET'])(queryBusinessSpeedTypeStatusList)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeBusinessSpeedList', methods=['GET'])(queryBusinessSpeedTypeBusinessSpeedList)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeBusinessTypeList', methods=['GET'])(queryBusinessSpeedTypeBusinessTypeList)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/addBusinessSpeedTypeData', methods=['POST'])(addBusinessSpeedTypeData)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/updateBusinessSpeedTypeData', methods=['POST'])(updateBusinessSpeedTypeData)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/deleteBusinessSpeedTypeData', methods=['POST'])(deleteBusinessSpeedTypeData)
app.route('/api/electric_knowledge/front_business_speed_type_relation_data_service/importExcelbaseBusinessSpeedTypeData', methods=['POST'])(importExcelbaseBusinessSpeedTypeData)

# 业务模型-单板业务模型-单板原子模型
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomTree', methods=['GET'])(queryBoardBusinessAtomTree)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomByParams', methods=['GET'])(queryBoardBusinessAtomByParams)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomBoardBusinessTypeList', methods=['GET'])(queryBoardBusinessAtomBoardBusinessTypeList)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomBoardBusinessList', methods=['GET'])(queryBoardBusinessAtomBoardBusinessList)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomStatusList', methods=['GET'])(queryBoardBusinessAtomStatusList)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/addBoardBusinessAtomData', methods=['POST'])(addBoardBusinessAtomData)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/updateBoardBusinessAtomData', methods=['POST'])(updateBoardBusinessAtomData)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/deleteBoardBusinessAtomData', methods=['POST'])(deleteBoardBusinessAtomData)
app.route('/api/electric_knowledge/front_board_atom_model_relation_data_service/importExcelBoardAtomModelData', methods=['POST'])(importExcelBoardAtomModelData)

# 业务模型-单板业务模型-单板有效模型
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupTree', methods=['GET'])(queryBoardBusinessGroupTree)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupByParams', methods=['GET'])(queryBoardBusinessGroupByParams)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupBoardBusinessTypeList', methods=['GET'])(queryBoardBusinessGroupBoardBusinessTypeList)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupBoardBusinessList', methods=['GET'])(queryBoardBusinessGroupBoardBusinessList)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupStatusList', methods=['GET'])(queryBoardBusinessGroupStatusList)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/addBoardBusinessGroupData', methods=['POST'])(addBoardBusinessGroupData)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/updateBoardBusinessGroupData', methods=['POST'])(updateBoardBusinessGroupData)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/deleteBoardBusinessGroupData', methods=['POST'])(deleteBoardBusinessGroupData)
app.route('/api/electric_knowledge/front_board_group_model_relation_data_service/importExcelBoardGroupModelData', methods=['POST'])(importExcelBoardGroupModelData)

# 业务模型-网元业务模型
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessTree', methods=['GET'])(queryNetBusinessTree)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessByParams', methods=['GET'])(queryNetBusinessByParams)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessNetBusinessSchemeList', methods=['GET'])(queryNetBusinessNetBusinessSchemeList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessNetBusinessModelList', methods=['GET'])(queryNetBusinessNetBusinessModelList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessBusinessTypeList', methods=['GET'])(queryNetBusinessBusinessTypeList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessCrossTypeList', methods=['GET'])(queryNetBusinessCrossTypeList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessBoardBusinessModelList', methods=['GET'])(queryNetBusinessBoardBusinessModelList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessStatusList', methods=['GET'])(queryNetBusinessStatusList)
app.route('/api/electric_knowledge/front_net_business_model_data_service/addNetBusinessData', methods=['POST'])(addNetBusinessData)
app.route('/api/electric_knowledge/front_net_business_model_data_service/updateNetBusinessData', methods=['POST'])(updateNetBusinessData)
app.route('/api/electric_knowledge/front_net_business_model_data_service/deleteNetBusinessData', methods=['POST'])(deleteNetBusinessData)
app.route('/api/electric_knowledge/front_net_business_model_data_service/importExcelbaseNetBusinessData', methods=['POST'])(importExcelbaseNetBusinessData)

# 要素因子
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationByParams', methods=['GET'])(queryCoreElementFactorRelationByParams)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationTree', methods=['GET'])(queryCoreElementFactorRelationTree)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationStatusList', methods=['GET'])(queryCoreElementFactorRelationStatusList)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationCoreElementList', methods=['GET'])(queryCoreElementFactorRelationCoreElementList)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorList', methods=['GET'])(queryCoreElementFactorRelationFactorList)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorValueSrcList', methods=['GET'])(queryCoreElementFactorRelationFactorValueSrcList)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorValueList', methods=['GET'])(queryCoreElementFactorRelationFactorValueList)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/addCoreElementFactorRelationData', methods=['POST'])(addCoreElementFactorRelationData)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/updateCoreElementFactorRelationData', methods=['POST'])(updateCoreElementFactorRelationData)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/deleteCoreElementFactorRelationData', methods=['POST'])(deleteCoreElementFactorRelationData)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/importExcelCoreElementFactorRelationData', methods=['POST'])(importExcelCoreElementFactorRelationData)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorValueDict', methods=['GET'])(queryCoreElementFactorValueDict)
app.route('/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/updateSourceCoreElementFactorRelationData', methods=['POST'])(updateSourceCoreElementFactorRelationData)

# 特性树-特性&子特性
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeTree', methods=['GET'])(queryFeatureTreeTree)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeByParams', methods=['POST'])(queryFeatureTreeByParams)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeStatusList', methods=['GET'])(queryFeatureTreeStatusList)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureFirstTypeList', methods=['GET'])(queryFeatureTreeFeatureFirstTypeList)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureSecondTypeList', methods=['GET'])(queryFeatureTreeFeatureSecondTypeList)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureList', methods=['GET'])(queryFeatureTreeFeatureList)
app.route('/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeSubFeatureList', methods=['GET'])(queryFeatureTreeSubFeatureList)
app.route('/api/electric_knowledge/front_feature_relation_data_service/addFeatureRelationData', methods=['POST'])(addFeatureRelationData)
app.route('/api/electric_knowledge/front_feature_relation_data_service/updateFeatureRelationData', methods=['POST'])(updateFeatureRelationData)
app.route('/api/electric_knowledge/front_feature_relation_data_service/deleteFeatureRelationData', methods=['POST'])(deleteFeatureRelationData)
app.route('/api/electric_knowledge/front_feature_relation_data_service/importExcelFeatureRelationData', methods=['POST'])(importExcelFeatureRelationData)
app.route('/api/electric_knowledge/front_feature_relation_data_service/addFeatureIcenterPage', methods=['POST'])(addFeatureIcenterPage)
app.route('/api/electric_knowledge/front_feature_relation_data_service/deleteFeatureIcenterPage', methods=['POST'])(deleteFeatureIcenterPage)
app.route('/api/electric_knowledge/front_feature_relation_data_service/syncFeatureIcenterPage', methods=['POST'])(syncFeatureIcenterPage)
app.route('/api/electric_knowledge/front_feature_relation_data_service/updateFeatureIcenterPage', methods=['POST'])(updateFeatureIcenterPage)
app.route('/api/electric_knowledge/front_feature_relation_data_service/importExcelOldChildrenFeatureData', methods=['POST'])(importExcelOldChildrenFeatureData)

# 特性树-特性&单板
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardTree', methods=['GET'])(queryFeatureBoardTree)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardByParams', methods=['POST'])(queryFeatureBoardByParams)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureInfoDict', methods=['GET'])(queryFeatureInfoDict)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardStatusList', methods=['GET'])(queryFeatureBoardStatusList)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardBoardList', methods=['GET'])(queryFeatureBoardBoardList)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/updateFeatureBoardData', methods=['POST'])(updateFeatureBoardData)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/importExcelFeatureBoardData', methods=['POST'])(importExcelFeatureBoardData)
app.route('/api/electric_knowledge/front_feature_board_relation_data_service/query_board_new_features', methods=['GET'])(query_board_new_features)

# 硬件树-单板树
app.route('/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams', methods=['GET'])(queryBoardTreeByParams)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeFactorList', methods=['GET'])(queryBoardTreeFactorList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeFactorValueDict', methods=['GET'])(queryBoardTreeFactorValueDict)
app.route('/api/electric_knowledge/front_board_tree_data_service/createRDC', methods=['POST'])(createRDC)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryRDC', methods=['POST'])(queryRDC)
app.route('/api/electric_knowledge/front_board_tree_data_service/addBoardTreeData', methods=['POST'])(addBoardTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/updateBoardTreeData', methods=['POST'])(updateBoardTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/deleteBoardTreeData', methods=['POST'])(deleteBoardTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/importExcelBoardTreeData', methods=['POST'])(importExcelBoardTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/addBoardIcenterPage', methods=['POST'])(addBoardIcenterPage)
app.route('/api/electric_knowledge/front_board_tree_data_service/updateBoardIcenterPage', methods=['POST'])(updateBoardIcenterPage)
app.route('/api/electric_knowledge/front_board_tree_data_service/syncBoardIcenterPage', methods=['POST'])(syncBoardIcenterPage)
app.route('/api/electric_knowledge/front_board_tree_data_service/query_hardware_tree_rule_dict_by_situation', methods=['POST'])(query_hardware_tree_rule_dict_by_situation)

# 硬件树-单板部件树
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardComponentsTreeByParams', methods=['GET'])(queryBoardComponentsTreeByParams)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardComponentsTreeStatusList', methods=['GET'])(queryBoardComponentsTreeStatusList)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeTree', methods=['GET'])(queryBoardPartTreeTree)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreePartList', methods=['GET'])(queryBoardPartTreePartList)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeBusinessSchemeList', methods=['GET'])(queryBoardPartTreeBusinessSchemeList)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeSchemeSliceList', methods=['GET'])(queryBoardPartTreeSchemeSliceList)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/addBoardComponentsTreeData', methods=['POST'])(addBoardComponentsTreeData)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/updateBoardComponentsTreeData', methods=['POST'])(updateBoardComponentsTreeData)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/deleteBoardComponentsTreeData', methods=['POST'])(deleteBoardComponentsTreeData)
app.route('/api/electric_knowledge/front_board_components_tree_data_service/importExcelBoardComponentsTreeData', methods=['POST'])(importExcelBoardComponentsTreeData)

# 硬件树-子架树
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeByParams', methods=['GET'])(queryShelfTreeByParams)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeFactorList', methods=['GET'])(queryShelfTreeFactorList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeFactorValueDict', methods=['GET'])(queryShelfTreeFactorValueDict)
app.route('/api/electric_knowledge/front_board_tree_data_service/addShelfTreeData', methods=['POST'])(addShelfTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/updateShelfTreeData', methods=['POST'])(updateShelfTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/deleteShelfTreeData', methods=['POST'])(deleteShelfTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/importExcelShelfTreeData', methods=['POST'])(importExcelShelfTreeData)

# 硬件树-子架部件树
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeProductList', methods=['GET'])(queryShelfPartTreeProductList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeShelfTypeList', methods=['GET'])(queryShelfPartTreeShelfTypeList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeTree', methods=['GET'])(queryShelfPartTreeTree)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeStatusList', methods=['GET'])(queryShelfPartTreeStatusList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeByParams', methods=['GET'])(queryShelfPartTreeByParams)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreePartList', methods=['GET'])(queryShelfPartTreePartList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeBusinessSchemeList', methods=['GET'])(queryShelfPartTreeBusinessSchemeList)
app.route('/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeSchemeSliceList', methods=['GET'])(queryShelfPartTreeSchemeSliceList)
app.route('/api/electric_knowledge/front_board_tree_data_service/addShelfPartTreeData', methods=['POST'])(addShelfPartTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/updateShelfPartTreeData', methods=['POST'])(updateShelfPartTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/deleteShelfPartTreeData', methods=['POST'])(deleteShelfPartTreeData)
app.route('/api/electric_knowledge/front_board_tree_data_service/importExcelShelfPartTreeData', methods=['POST'])(importExcelShelfPartTreeData)

# 单板全局状态
app.route('/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusByParams', methods=['POST'])(queryBoardGlobalStatusByParams)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusTree', methods=['GET'])(queryBoardGlobalStatusTree)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/querySimpleBoardGlobalStatusTree', methods=['GET'])(querySimpleBoardGlobalStatusTree)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusRdcFilterDataDict', methods=['GET'])(queryBoardGlobalStatusRdcFilterDataDict)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusBoardList', methods=['GET'])(queryBoardGlobalStatusBoardList)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/addBoardWholeStatusData', methods=['POST'])(addBoardWholeStatusData)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/updateBoardWholeStatusData', methods=['POST'])(updateBoardWholeStatusData)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/add_board_whole_st_data', methods=['POST'])(add_board_whole_st_data)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/add_new_part_update_change_analysis_data', methods=['POST'])(add_new_part_update_change_analysis_data)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/update_board_whole_st_data', methods=['POST'])(update_board_whole_st_data)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/syncBoardWholeStatusDataRDC', methods=['POST'])(syncBoardWholeStatusDataRDC)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/importExcelbaseBoardWholeStatusData', methods=['POST'])(importExcelbaseBoardWholeStatusData)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/importOldBoardWholeStatusData', methods=['POST'])(importOldBoardWholeStatusData)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/queryRdcFaultByRdcIdent', methods=['GET'])(queryRdcFaultByRdcIdent)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/update_change_analysis_data', methods=['POST'])(update_change_analysis_data)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/query_fault_list_by_feature', methods=['POST'])(query_fault_list_by_feature)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/query_rdc_list_by_board_name_and_preplan_version', methods=['POST'])(query_rdc_list_by_board_name_and_preplan_version)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/get_rdc_split_task_result_dict', methods=['GET'])(get_rdc_split_task_result_dict)
app.route('/api/electric_knowledge/front_board_whole_status_data_service/add_new_feature_update_change_analysis_data', methods=['POST'])(add_new_feature_update_change_analysis_data)

# 人工审核
app.route('/api/electric_knowledge/approval/submit_change', methods=['POST'])(submit_change)
app.route('/api/electric_knowledge/approval/batch_approve', methods=['POST'])(batch_approve)
app.route('/api/electric_knowledge/approval/single_approve', methods=['POST'])(single_approve)
app.route('/api/electric_knowledge/approval/revoke', methods=['POST'])(revoke)
app.route('/api/electric_knowledge/approval/get_my_pending', methods=['GET'])(get_my_pending)
app.route('/api/electric_knowledge/approval/get_my_submitted', methods=['GET'])(get_my_submitted)
app.route('/api/electric_knowledge/approval/get_detail', methods=['GET'])(get_detail)
app.route('/api/electric_knowledge/approval/admin_list', methods=['GET'])(admin_list)
app.route('/api/electric_knowledge/approval/get_biz_config_list', methods=['GET'])(get_biz_config_list)

# AI应用
app.route('/api/electric_knowledge/ai_application/process_request_dot_r001', methods=['POST'])(process_request_dot_r001)
app.route('/api/electric_knowledge/ai_application/process_request_dot_r002', methods=['POST'])(process_request_dot_r002)
app.route('/api/electric_knowledge/ai_application/process_request_split_r003', methods=['POST'])(process_request_split_r003)
app.route('/api/electric_knowledge/ai_application/process_request_split_r004', methods=['POST'])(process_request_split_r004)
app.route('/api/electric_knowledge/ai_application/process_request_split_r005', methods=['POST'])(process_request_split_r005)
app.route('/api/electric_knowledge/ai_application/process_request_split_r006', methods=['POST'])(process_request_split_r006)
app.route('/api/electric_knowledge/ai_application/process_request_split_r007', methods=['POST'])(process_request_split_r007)
app.route('/api/electric_knowledge/ai_application/process_query_board_all_feature_rdc_status', methods=['POST'])(process_query_board_all_feature_rdc_status)
app.route('/api/electric_knowledge/ai_application/process_query_board_slice_feature_rdc_status', methods=['POST'])(process_query_board_slice_feature_rdc_status)
app.route('/api/electric_knowledge/ai_application/process_query_board_key_changed_feature', methods=['POST'])(process_query_board_key_changed_feature)
app.route('/api/electric_knowledge/ai_application/process_query_board_key_changed_content', methods=['POST'])(process_query_board_key_changed_content)
app.route('/api/electric_knowledge/ai_application/process_query_supported_change_mode_and_affected_features', methods=['POST'])(process_query_supported_change_mode_and_affected_features)
app.route('/api/electric_knowledge/ai_application/process_dot_to_board_recommendation', methods=['POST'])(process_dot_to_board_recommendation)

# 其它-文件导入
app.route('/api/electric_knowledge/front_board_change_analysis_data_service/importExcelBoardChangeAnalysisData', methods=['POST'])(importExcelBoardChangeAnalysisData)
app.route('/api/electric_knowledge/front_board_board_data_dictionary/import_board_data_dictionary_to_knowledge_base', methods=['POST'])(import_board_data_dictionary_to_knowledge_base)
app.route('/api/electric_knowledge/front_mr_feature_data_service/importExcelMrFeatureData', methods=['POST'])(importExcelMrFeatureData)
app.route('/api/electric_knowledge/front_board_opt_biz_data_service/queryBoardOptBizByParams', methods=['GET'])(queryBoardOptBizByParams)
app.route('/api/electric_knowledge/front_board_opt_biz_data_service/importExcelBoardOptBizData', methods=['POST'])(importExcelBoardOptBizData)
app.route('/api/electric_knowledge/front_feature_change_relation_data_service/importExcelFeatureChangeData', methods=['POST'])(importExcelFeatureChangeData)

# 其它-特性&检测点内容
app.route('/api/electric_knowledge/module_featurecheckpoint_content_data_service/queryModuleFeaturecheckpointContentDataByParams', methods=['GET'])(queryModuleFeaturecheckpointContentDataByParams)
app.route('/api/electric_knowledge/module_featurecheckpoint_content_data_service/importExcelModuleFeaturecheckpointContentData', methods=['POST'])(importExcelModuleFeaturecheckpointContentData)

# 其它-产品知识图片
app.route('/api/electric_knowledge/product_image_data_service/images/<image_id>', methods=['GET'])(get_image)
app.route('/api/electric_knowledge/product_image_data_service/upload_image', methods=['POST'])(upload_image)

# 需求管理助手
app.route('/api/electric_knowledge/req_manage_agent/ask_req_manage_agent', methods=['POST'])(service_add_req_manage_agent_single_chat_record)
app.route('/api/electric_knowledge/req_manage_agent/get_history_chat_record_list', methods=['POST'])(service_get_history_chat_record_list)
app.route('/api/electric_knowledge/req_manage_agent/get_prompt_list_by_search_str', methods=['POST'])(service_get_prompt_list_by_search_str)
app.route('/api/electric_knowledge/req_manage_agent/update_single_prompt_content', methods=['POST'])(service_update_single_prompt_content)
app.route('/api/electric_knowledge/req_manage_agent/update_single_prompt_reference_count', methods=['POST'])(service_update_single_prompt_reference_count)
app.route('/api/electric_knowledge/req_manage_agent/del_single_prompt', methods=['POST'])(service_del_single_prompt)
app.route('/api/electric_knowledge/req_manage_agent/get_tool_name_list', methods=['GET'])(service_get_tool_name_list)

# 需求管理看板
app.route('/api/electric_knowledge/req_manage_board/update_pr_info_list', methods=['POST'])(service_update_pr_info_list)
app.route('/api/electric_knowledge/req_manage_board/del_pr_info_list_by_script_update_date', methods=['POST'])(service_del_pr_info_list_by_script_update_date)
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_board_pr_split_summary_data_list', methods=['POST'])(service_update_req_manage_board_pr_split_summary_data_list)
app.route('/api/electric_knowledge/req_manage_board/query_preplanning_list', methods=['GET'])(service_query_preplanning_list)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_summary_line_data_list_by_preplanning_and_date', methods=['POST'])(service_query_req_manage_board_pr_split_summary_line_data_list_by_preplanning_and_date)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_summary_table_data_list_by_preplanning_and_date', methods=['POST'])(service_query_req_manage_board_pr_split_summary_table_data_list_by_preplanning_and_date)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_detail_table_data_list_by_preplanning_and_date', methods=['POST'])(service_query_req_manage_board_pr_split_detail_table_data_list_by_preplanning_and_date)

# 需求预检看板
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_check_pr_info_list', methods=['POST'])(service_update_req_manage_check_pr_info_table_check_pr_info_list)
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_handle_pr_info_list', methods=['POST'])(service_update_req_manage_check_pr_info_table_handle_pr_info_list)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_info_table_by_filter_dict', methods=['POST'])(service_query_req_manage_check_pr_info_table_by_filter_dict)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_info_table_value_dict_by_field_list', methods=['POST'])(service_query_req_manage_check_pr_info_table_value_dict_by_field_list)
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_cal_field', methods=['POST'])(service_update_req_manage_check_pr_info_table_cal_field)
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_summary_table_data_list', methods=['POST'])(service_update_req_manage_check_pr_summary_table_data_list)
app.route('/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_summary_table_by_date_range_and_preplanning', methods=['POST'])(service_query_req_manage_check_pr_summary_table_by_date_range_and_preplanning)
app.route('/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_man_fields_by_id_list', methods=['POST'])(service_update_req_manage_check_pr_info_table_man_fields_by_id_list)



# 质量案例
app.route('/api/quality/quality_case/query_all_quality_case_list_by_param', methods=['POST'])(query_all_quality_case_list_by_param)



# 网元健康体检
app.route('/api/parseHealthLog', methods=['POST'])(parse_health_log)
app.route('/api/getSampleHealthData', methods=['POST'])(get_sample_data)
app.route('/api/executeOnlineDiagnosis', methods=['POST'])(execute_online_diagnosis)
app.route('/api/get-jump-servers', methods=['POST'])(getjumpservers)
app.route('/api/getBatchKpiLogs', methods=['POST'])(get_batch_kpi_logs)
app.route('/api/analyzeBatchKpiLogs', methods=['POST'])(analyze_batch_kpi_logs)
app.route('/api/getBatchAnalysisStatus', methods=['GET'])(get_batch_analysis_status)
app.route('/api/getKpiDetailData', methods=['POST'])(get_kpi_detail_data)
app.route('/api/exportSsdLifeData', methods=['GET','POST'])(export_ssd_life_data)

# 故障波及案例单 - 显式添加 OPTIONS 方法以支持 CORS 预检请求
app.route('/api/issueImpacte/case/query', methods=['POST', 'OPTIONS'])(query_issue_impact_case_list)
app.route('/api/issueImpacte/case/create', methods=['POST', 'OPTIONS'])(create_issue_impact_case)
app.route('/api/issueImpacte/case/update', methods=['POST', 'OPTIONS'])(update_issue_impact_case)
app.route('/api/issueImpacte/case/delete', methods=['POST', 'OPTIONS'])(delete_issue_impact_case)
app.route('/api/issueImpacte/case/import', methods=['POST', 'OPTIONS'])(import_issue_impact_case_batch)
app.route('/api/issueImpacte/case/confirm_source', methods=['POST', 'OPTIONS'])(confirm_case_source)
# 故障波及版本管理
from issueImpacte.version_service import (
    query_version_list, create_version, update_version, delete_version,
    get_version_detail, query_version_cases,
    get_target_network_options, get_board_options, get_branch_options, get_belong_project_options
)

app.route('/api/issueImpacte/version/query', methods=['POST', 'OPTIONS'])(query_version_list)
app.route('/api/issueImpacte/version/create', methods=['POST', 'OPTIONS'])(create_version)
app.route('/api/issueImpacte/version/update', methods=['POST', 'OPTIONS'])(update_version)
app.route('/api/issueImpacte/version/delete', methods=['POST', 'OPTIONS'])(delete_version)
app.route('/api/issueImpacte/version/<version_id>', methods=['GET', 'OPTIONS'])(get_version_detail)
app.route('/api/issueImpacte/version/<version_id>/cases', methods=['POST', 'OPTIONS'])(query_version_cases)
app.route('/api/issueImpacte/version/options/target-network', methods=['GET', 'OPTIONS'])(get_target_network_options)
app.route('/api/issueImpacte/version/options/boards', methods=['GET', 'OPTIONS'])(get_board_options)
app.route('/api/issueImpacte/version/options/branches', methods=['GET', 'OPTIONS'])(get_branch_options)
app.route('/api/issueImpacte/version/options/belong-project', methods=['GET', 'OPTIONS'])(get_belong_project_options)
# 需求排期助手
app.route('/api/requirement_schedule/queryRequirementScheduleByParams', methods=['GET'])(queryRequirementScheduleByParams)
app.route('/api/requirement_schedule/updateRequirementSchedule', methods=['POST'])(updateRequirementSchedule)
app.route('/api/requirement_schedule/getFilterHistory', methods=['GET'])(getFilterHistory)
app.route('/api/requirement_schedule/saveFilterHistory', methods=['POST'])(saveFilterHistory)
app.route('/api/requirement_schedule/checkEditPermission', methods=['GET'])(checkEditPermission)
app.route('/api/requirement_schedule/syncRdcData', methods=['POST'])(syncRdcData)
app.route('/api/requirement_schedule/autoScheduling', methods=['POST'])(autoScheduling)
app.route('/api/requirement_schedule/backfillRdcData', methods=['POST'])(backfillRdcData)
app.route('/api/requirement_schedule/previewBackfillRdcData', methods=['POST'])(previewBackfillRdcData)

# 人员技能地图
app.route('/api/person_skill_map/queryPersonSkillMapByParams', methods=['GET'])(queryPersonSkillMapByParams)
app.route('/api/person_skill_map/createPersonSkillMap', methods=['POST'])(createPersonSkillMap)
app.route('/api/person_skill_map/updatePersonSkillMap', methods=['POST'])(updatePersonSkillMap)
app.route('/api/person_skill_map/deletePersonSkillMap', methods=['POST'])(deletePersonSkillMap)
app.route('/api/person_skill_map/getPersonSkillMapOptions', methods=['GET'])(getPersonSkillMapOptions)
app.route('/api/person_skill_map/importPersonSkillMap', methods=['POST'])(importPersonSkillMap)
app.route('/api/person_skill_map/exportPersonSkillMap', methods=['GET'])(exportPersonSkillMap)
# 需求开发投入人力设置
from requirement_schedule.human_resource_setting import (
    queryHumanResourceSettingByParams,
    aggregateFromPersonSkillMap,
    updateHumanResourceSetting,
    deleteHumanResourceSetting,
    batchDeleteHumanResourceSetting,
    getHumanResourceSettingOptions,
    exportHumanResourceSetting,
    importHumanResourceSetting,
    triggerSyncRequirementDevHumanResource
)
app.route('/api/human_resource_setting/queryHumanResourceSettingByParams', methods=['GET'])(queryHumanResourceSettingByParams)
app.route('/api/human_resource_setting/aggregateFromPersonSkillMap', methods=['GET'])(aggregateFromPersonSkillMap)
app.route('/api/human_resource_setting/updateHumanResourceSetting', methods=['POST'])(updateHumanResourceSetting)
app.route('/api/human_resource_setting/deleteHumanResourceSetting', methods=['POST'])(deleteHumanResourceSetting)
app.route('/api/human_resource_setting/batchDeleteHumanResourceSetting', methods=['POST'])(batchDeleteHumanResourceSetting)
app.route('/api/human_resource_setting/getHumanResourceSettingOptions', methods=['GET'])(getHumanResourceSettingOptions)
app.route('/api/human_resource_setting/exportHumanResourceSetting', methods=['GET'])(exportHumanResourceSetting)
app.route('/api/human_resource_setting/importHumanResourceSetting', methods=['POST'])(importHumanResourceSetting)
app.route('/api/human_resource_setting/triggerSyncRequirementDevHumanResource', methods=['GET'])(triggerSyncRequirementDevHumanResource)

# 人力透视表
from requirement_schedule.human_resource_pivot import (
    queryHumanResourcePivotByParams,
    getHumanResourcePivotOptions
)
app.route('/api/human_resource_pivot/queryHumanResourcePivotByParams', methods=['GET'])(queryHumanResourcePivotByParams)
app.route('/api/human_resource_pivot/getHumanResourcePivotOptions', methods=['GET'])(getHumanResourcePivotOptions)

# 可用人力
from requirement_schedule.available_human_resource import (
    queryAvailableHumanResourceByParams,
    getAvailableHumanResourceOptions
)
app.route('/api/available_human_resource/queryAvailableHumanResourceByParams', methods=['GET'])(queryAvailableHumanResourceByParams)
app.route('/api/available_human_resource/getAvailableHumanResourceOptions', methods=['GET'])(getAvailableHumanResourceOptions)

# 版本视图
from requirement_schedule.version_table import (
    queryVersionTableByParams,
    createVersionTable,
    updateVersionTable,
    deleteVersionTable,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    getVersionTableOptions,
    importVersionTable,
    exportVersionTable
)
app.route('/api/version_table/queryVersionTableByParams', methods=['GET'])(queryVersionTableByParams)
app.route('/api/version_table/createVersionTable', methods=['POST'])(createVersionTable)
app.route('/api/version_table/updateVersionTable', methods=['POST'])(updateVersionTable)
app.route('/api/version_table/deleteVersionTable', methods=['POST'])(deleteVersionTable)
app.route('/api/version_table/getVersionTableOptions', methods=['GET'])(getVersionTableOptions)
app.route('/api/version_table/importVersionTable', methods=['POST'])(importVersionTable)
app.route('/api/version_table/exportVersionTable', methods=['GET'])(exportVersionTable)

# 特性视图
from requirement_schedule.feature_view import (
    queryFeatureViewByParams,
    createFeatureView,
    updateFeatureView,
    deleteFeatureView,
    getFeatureViewOptions,
    importFeatureView,
    exportFeatureView,
    countFeatureViewByDomainTeam,
    deleteFeatureViewByDomainTeam,
)
app.route('/api/feature_view/queryFeatureViewByParams', methods=['GET'])(queryFeatureViewByParams)
app.route('/api/feature_view/createFeatureView', methods=['POST'])(createFeatureView)
app.route('/api/feature_view/updateFeatureView', methods=['POST'])(updateFeatureView)
app.route('/api/feature_view/deleteFeatureView', methods=['POST'])(deleteFeatureView)
app.route('/api/feature_view/getFeatureViewOptions', methods=['GET'])(getFeatureViewOptions)
app.route('/api/feature_view/importFeatureView', methods=['POST'])(importFeatureView)
app.route('/api/feature_view/exportFeatureView', methods=['GET'])(exportFeatureView)
app.route('/api/feature_view/countFeatureViewByDomainTeam', methods=['GET'])(countFeatureViewByDomainTeam)
app.route('/api/feature_view/deleteFeatureViewByDomainTeam', methods=['POST'])(deleteFeatureViewByDomainTeam)
# 单板组装助手
# 先注册 OPTIONS 处理，确保 CORS 预检请求能正确处理
app.route('/api/boardAssembly/generateElements', methods=['OPTIONS'])(handle_options)
app.route('/api/boardAssembly/generateFramework', methods=['OPTIONS'])(handle_options)
app.route('/api/boardAssembly/generateConfig', methods=['OPTIONS'])(handle_options)
app.route('/api/boardAssembly/getBoardNames', methods=['OPTIONS'])(handle_options)
app.route('/api/boardAssembly/getBusinessModels', methods=['OPTIONS'])(handle_options)

# 注册实际的处理函数
app.route('/api/boardAssembly/generateElements', methods=['POST'])(generate_elements)
app.route('/api/boardAssembly/generateFramework', methods=['POST'])(generate_framework)
app.route('/api/boardAssembly/generateConfig', methods=['POST'])(generate_config)
app.route('/api/boardAssembly/getBoardNames', methods=['GET'])(get_board_names)
app.route('/api/boardAssembly/getBusinessModels', methods=['GET'])(get_business_models)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True) # http://10.239.69.30/
