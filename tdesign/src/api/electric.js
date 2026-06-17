import request_fast from '@/utils/request_fast.js'


// 要素因子-业务
export function queryCoreElementFactorRelationByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationByParams',
        method: 'get',
        params: params
    })
}

export function queryCoreElementFactorRelationTree(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationTree',
        method: 'get',
        params: params
    })
}

export function queryCoreElementFactorRelationStatusList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationStatusList',
        method: 'get',
        params: params
    })
}

export function queryCoreElementFactorRelationCoreElementList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationCoreElementList',
        method: 'get',
        params: params
    })
}

export function queryCoreElementFactorRelationFactorList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorList',
        method: 'get',
        params: params
    })
}

export function queryCoreElementFactorRelationFactorValueList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorValueList',
        method: 'get',
        params: params
    })
}

export function addCoreElementFactorRelationData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/addCoreElementFactorRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateCoreElementFactorRelationData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/updateCoreElementFactorRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteCoreElementFactorRelationData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/deleteCoreElementFactorRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updatezTestPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/updateElementFactorToZtest',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryCoreElementFactorRelationFactorValueSrcList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorRelationFactorValueSrcList',
        method: 'get',
        params: params,
    })
}

export function importExcelCoreElementFactorRelationData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/importExcelCoreElementFactorRelationData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 业务模型-光口业务速率&业务类型
export function queryBusinessSpeedTypeByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeByParams',
        method: 'get',
        params: params
    })
}

export function queryBusinessSpeedTypeStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeStatusList',
        method: 'get',
    })
}

export function queryBusinessSpeedTypeBusinessSpeedList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeBusinessSpeedList',
        method: 'get',
        params: params
    })
}

export function queryBusinessSpeedTypeBusinessTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/queryBusinessSpeedTypeBusinessTypeList',
        method: 'get',
        params: params
    })
}


export function addBusinessSpeedTypeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/addBusinessSpeedTypeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBusinessSpeedTypeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/updateBusinessSpeedTypeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteBusinessSpeedTypeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/deleteBusinessSpeedTypeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelbaseBusinessSpeedTypeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_business_speed_type_relation_data_service/importExcelbaseBusinessSpeedTypeData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 业务模型-单板业务模型
/* Started by AICoder, pid:jb72eg2dae00bc5142c00b72311a926db717a97f */
export function queryBoardBusinessAtomByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomByParams',
        method: 'get',
        params: params
    })
}

export function queryBoardBusinessAtomTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomTree',
        method: 'get',
    })
}

export function queryBoardBusinessAtomStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomStatusList',
        method: 'get',
    })
}

export function queryBoardBusinessAtomBoardBusinessTypeList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomBoardBusinessTypeList',
        method: 'get',
    })
}


export function queryBoardBusinessAtomBoardBusinessList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/queryBoardBusinessAtomBoardBusinessList',
        method: 'get',
    })
}


export function addBoardBusinessAtomData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/addBoardBusinessAtomData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardBusinessAtomData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/updateBoardBusinessAtomData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteBoardBusinessAtomData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/deleteBoardBusinessAtomData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelBoardAtomModelData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_atom_model_relation_data_service/importExcelBoardAtomModelData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function queryBoardBusinessGroupByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupByParams',
        method: 'get',
        params: params
    })
}

export function queryBoardBusinessGroupTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupTree',
        method: 'get',
    })
}

export function queryBoardBusinessGroupStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupStatusList',
        method: 'get',
    })
}


export function queryBoardBusinessGroupBoardBusinessTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupBoardBusinessTypeList',
        method: 'get',
        params: params
    })
}

export function queryBoardBusinessGroupBoardBusinessList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/queryBoardBusinessGroupBoardBusinessList',
        method: 'get',
        params: params
    })
}


export function addBoardBusinessGroupData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/addBoardBusinessGroupData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardBusinessGroupData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/updateBoardBusinessGroupData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteBoardBusinessGroupData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/deleteBoardBusinessGroupData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelBoardGroupModelData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_group_model_relation_data_service/importExcelBoardGroupModelData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
/* Ended by AICoder, pid:jb72eg2dae00bc5142c00b72311a926db717a97f */

// 业务模型-网元业务模型
export function queryNetBusinessByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessByParams',
        method: 'get',
        params: params
    })
}

export function queryNetBusinessTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessTree',
        method: 'get',
    })
}

export function queryNetBusinessStatusList() {
    // return request_fast({
    //     url: '/queryNetBusinessStatusList',
    //     method: 'get',
    // })
    return {
        "code": 200,
        "message": "获取成功",
        "status": "success",
        "data": ["正常", "审核中-新增", "审核中-删除", "审核中-修改"]
    }
}

export function queryNetBusinessNetBusinessSchemeList() {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessNetBusinessSchemeList',
        method: 'get'
    })
}

export function queryNetBusinessNetBusinessModelList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessNetBusinessModelList',
        method: 'get',
        params: params
    })
}

export function queryNetBusinessBusinessTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessBusinessTypeList',
        method: 'get',
        params: params
    })
}

export function queryNetBusinessBoardBusinessModelList() {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessBoardBusinessModelList',
        method: 'get'
    })
}

export function queryNetBusinessCrossTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/queryNetBusinessCrossTypeList',
        method: 'get',
        params: params
    })
}

export function addNetBusinessData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/addNetBusinessData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateNetBusinessData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/updateNetBusinessData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteNetBusinessData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/deleteNetBusinessData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelbaseNetBusinessData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_net_business_model_data_service/importExcelbaseNetBusinessData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 硬件树-单板部件树
export function queryBoardPartTreeByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardComponentsTreeByParams',
        method: 'get',
        params: params
    })
}

export function queryBoardPartTreeTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeTree',
        method: 'get',
    })
}

export function queryBoardPartTreeStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardComponentsTreeStatusList',
        method: 'get',
    })
}

export function queryBoardPartTreePartList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreePartList',
        method: 'get',
        params: params
    })
}

export function queryBoardPartTreeBusinessSchemeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeBusinessSchemeList',
        method: 'get',
        params: params
    })
}

export function queryBoardPartTreeSchemeSliceList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/queryBoardPartTreeSchemeSliceList',
        method: 'get',
        params: params
    })
}

export function addBoardPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/addBoardComponentsTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/updateBoardComponentsTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteBoardPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/deleteBoardComponentsTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelBoardPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_components_tree_data_service/importExcelBoardComponentsTreeData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 硬件树-单板树
export function queryBoardTreeByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams',
        method: 'get',
        params: params
    })
}

export function queryBoardTreeFactorList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeFactorList',
        method: 'get',
    })
}

export function queryBoardTreeFactorValueDict() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeFactorValueDict',
        method: 'get',
    })
}

export function queryBoardTreeAllFactorValueDict() {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorValueDict',
        method: 'get',
        params: {"elementType": "单板"}
    })
}

export function getTaskResult(id) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/get_task_result',
        method: 'get',
        params: {"task_id": id}
    })
}

export function addBoardTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/addBoardTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/updateBoardTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteBoardTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/deleteBoardTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelBoardTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/importExcelBoardTreeData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function queryBoardOptBizByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_opt_biz_data_service/queryBoardOptBizByParams',
        method: 'get',
        params: params
    })
}

// 硬件树-单板全局状态
export function queryBoardGlobalStatusByParams(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusByParams',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryBoardGlobalStatusFilterDataDict() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/querySimpleBoardGlobalStatusTree',
        method: 'get',
    })
}

export function queryBoardGlobalStatusRdcFilterDataDict(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/queryBoardGlobalStatusRdcFilterDataDict',
        method: 'get',
        params: params,
    })
}

export function queryBoardGlobalStatusProblemListByRdc(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/queryRdcFaultByRdcIdent',
        method: 'get',
        params: params,
    })
}

export function updateBoardGlobalStatusData(data) {
    // return request_fast({
    //     url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/updateCoreElementFactorRelationData',
    //     method: 'post',
    //     headers: {
    //         'Content-Type': 'application/json',
    //     },
    //     data: data,
    // })
    return {
        "code": 200,
        "message": "修改成功",
        "status": "success",
    }
}

export function addBoardGlobalStatusBoardData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/add_board_whole_st_data',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function addNewPartUpdateChangeAnalysisData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/add_new_part_update_change_analysis_data',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function addNewFeatureUpdateChangeAnalysisData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/add_new_feature_update_change_analysis_data',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateChangeAnalysisData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/update_change_analysis_data',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function syncBoardWholeStatusDataRDC(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/syncBoardWholeStatusDataRDC',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardGlobalStatusBoardData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/update_board_whole_st_data',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelBoardGlobalStatusData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/importExcelbaseBoardWholeStatusData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function queryBoardNewFeatures(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/query_board_new_features',
        method: 'get',
        params: params
    })
}

// 硬件树-子架部件树
export function queryShelfPartTreeByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeByParams',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreeTree(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeTree',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreeStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeStatusList',
        method: 'get',
    })
}

export function queryShelfPartTreeProductList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeProductList',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreeShelfTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeShelfTypeList',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreePartList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreePartList',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreeBusinessSchemeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeBusinessSchemeList',
        method: 'get',
        params: params
    })
}

export function queryShelfPartTreeSchemeSliceList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfPartTreeSchemeSliceList',
        method: 'get',
        params: params
    })
}

export function addShelfPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/addShelfPartTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateShelfPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/updateShelfPartTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteShelfPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/deleteShelfPartTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateBoardIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/updateBoardIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function syncBoardIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/syncBoardIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelShelfPartTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/importExcelShelfPartTreeData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 硬件树-子架树
export function queryShelfTreeByParams(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeByParams',
        method: 'get',
        params: params
    })
}

export function queryShelfTreeFactorList() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeFactorList',
        method: 'get',
    })
}

export function queryShelfTreeFactorValueDict() {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/queryShelfTreeFactorValueDict',
        method: 'get',
    })
}

export function queryShelfTreeAllFactorValueDict() {
    return request_fast({
        url: '/api/electric_knowledge/front_business_coreelement_factor_relation_data_service/queryCoreElementFactorValueDict',
        method: 'get',
        params: {"elementType": "子架"}
    })
}

export function addShelfTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/addShelfTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateShelfTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/updateShelfTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteShelfTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/deleteShelfTreeData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function addBoardIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/addBoardIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelShelfTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/importExcelShelfTreeData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function queryHardwareTreeRuleDictBySituation(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_tree_data_service/query_hardware_tree_rule_dict_by_situation',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 特性树-特性树
/* Started by AICoder, pid:3aa2ay67f712d63141f2082e7152c57f7683f0cb */
export function queryFeatureTreeByParams(data) {
    /* Started by AICoder, pid:3136dm25f231091145f70b65e0d44004dde5a9a0 */
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeByParams',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data
    })
    /* Ended by AICoder, pid:3136dm25f231091145f70b65e0d44004dde5a9a0 */
}
/* Ended by AICoder, pid:3aa2ay67f712d63141f2082e7152c57f7683f0cb */

/* Started by AICoder, pid:aa3e2vc21ac36fb140ff09f9209b360a34e6cdda */
export function queryFeatureTreeTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeTree',
        method: 'get',
    })
}
/* Ended by AICoder, pid:aa3e2vc21ac36fb140ff09f9209b360a34e6cdda */

export function queryFeatureTreeStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeStatusList',
        method: 'get',
    })
}

export function queryFeatureTreeFeatureFirstTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureFirstTypeList',
        method: 'get',
        params: params
    })
}

export function queryFeatureTreeFeatureSecondTypeList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureSecondTypeList',
        method: 'get',
        params: params
    })
}

export function queryFeatureTreeFeatureList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureList',
        method: 'get',
        params: params
    })
}

export function queryFeatureTreeSubFeatureList(params) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeSubFeatureList',
        method: 'get',
        params: params
    })
}

export function addFeatureTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/addFeatureRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateFeatureTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/updateFeatureRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteFeatureTreeData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/deleteFeatureRelationData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function addFeatureIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/addFeatureIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateFeatureIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/updateFeatureIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteFeatureIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/deleteFeatureIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function syncFeatureIcenterPage(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/syncFeatureIcenterPage',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function importExcelFeatureRelationData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_relation_data_service/importExcelFeatureRelationData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

// 特性树-特性&单板
export function queryFeatureBoardByParams(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardByParams',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}


export function queryFeatureBoardTree() {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardTree',
        method: 'get',
    })
}

export function queryFeatureBoardBoardList() {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardBoardList',
        method: 'get',
    })
}

export function queryFeatureBoardStatusList() {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/queryFeatureBoardStatusList',
        method: 'get',
    })
}


export function updateFeatureBoardData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/updateFeatureBoardData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}


export function importExcelFeatureBoardData(data) {
    return request_fast({
        url: '/api/electric_knowledge/front_feature_board_relation_data_service/importExcelFeatureBoardData',
        method: 'post',
        data: data,
        file: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}


export function importExcelData(data) {
    return {
        "code": 200,
        "message": "导入成功",
        "status": "success",
    }
}

// 案例库
export function queryCaseLibraryByParams() {
    return request_fast({
        url: '/api/quality/quality_case/query_all_quality_case_list_by_param',
        method: 'post',
    })
}
// 需求排期助手
export function queryRequirementScheduleByParams(params) {
    return request_fast({
        url: '/api/requirement_schedule/queryRequirementScheduleByParams',
        method: 'get',
        params: params
    })
}

export function updateRequirementSchedule(data) {
    return request_fast({
        url: '/api/requirement_schedule/updateRequirementSchedule',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getFilterHistory(params) {
    return request_fast({
        url: '/api/requirement_schedule/getFilterHistory',
        method: 'get',
        params: params
    })
}

export function saveFilterHistory(data) {
    return request_fast({
        url: '/api/requirement_schedule/saveFilterHistory',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function checkEditPermission() {
    return request_fast({
        url: '/api/requirement_schedule/checkEditPermission',
        method: 'get',
    })
}

export function queryReqManageCheckDict(data) {
    return request_fast({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_info_table_value_dict_by_field_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryReqManageCheckTable(data) {
    return request_fast({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_info_table_by_filter_dict',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryReqManageCheckSummaryTable(data) {
    return request_fast({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_check_pr_summary_table_by_date_range_and_preplanning',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 批量更新人工标注字段
export function updateReqManageCheckPrInfoTableManFieldsByIdList(data) {
    return request_fast({
        url: '/api/electric_knowledge/req_manage_board/update_req_manage_check_pr_info_table_man_fields_by_id_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getRdcSplitTaskResultDict(id) {
    return request_fast({
        url: '/api/electric_knowledge/front_board_whole_status_data_service/get_rdc_split_task_result_dict',
        method: 'get',
        params: {"task_id": id}
    })
}

export function submitChange(data) {
    return request_fast({
        url: '/api/electric_knowledge/approval/submit_change',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getMyPending(params) {
    return request_fast({
        url: '/api/electric_knowledge/approval/get_my_pending',
        method: 'get',
        params: params
    })
}

export function getMySubmitted(params) {
    return request_fast({
        url: '/api/electric_knowledge/approval/get_my_submitted',
        method: 'get',
        params: params
    })
}

export function getDetail(params) {
    return request_fast({
        url: '/api/electric_knowledge/approval/get_detail',
        method: 'get',
        params: params
    })
}

export function batchApprove(data) {
    return request_fast({
        url: '/api/electric_knowledge/approval/batch_approve',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function singleApprove(data) {
    return request_fast({
        url: '/api/electric_knowledge/approval/single_approve',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function revokeApprove(data) {
    return request_fast({
        url: '/api/electric_knowledge/approval/revoke',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}