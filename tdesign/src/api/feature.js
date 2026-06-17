// src/api/feature.js
import request from '@/utils/request_comp'

export function knowQueryFeatureTreeBoardGraphSumDataDict(params) {
    return request({
        url: '/know/query_feature_tree_board_graph_sum_data_dict/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryFeatureTreeBoardTableSumDataDict(params) {
    return request({
        url: '/know/query_feature_tree_board_table_sum_data_dict/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryFeatureTreeBoardTableCumulativeDetailList(params) {
    return request({
        url: '/know/query_feature_tree_board_table_cumulative_detail_list/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryFeatureTreeBoardTableChangeDetailList(params) {
    return request({
        url: '/know/query_feature_tree_board_table_change_detail_list/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}
