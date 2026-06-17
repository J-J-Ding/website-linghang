// src/api/comp.js
import request from '@/utils/request_comp'

export function mainGetUserInfo(userId) {
    return request({
        url: '/main/get_user_info/',
        method: 'get',
        params: { "user_id": userId },
        urlType: "comp_api",
    })
}

export function mainUpdateUserInfo(userId, currentPage, currentTitle) {
    return request({
        url: '/main/update_user_info/',
        method: 'get',
        params: { "user_id": userId, "page": currentPage, "title": currentTitle  },
        urlType: "comp_api",
    })
}

export function mainAddUserActInfo(sendData) {
    return request({
        url: '/main/add_user_act_info/',
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        data: JSON.stringify(sendData),
        urlType: "comp_api",
    })
}


export function compQueryCompBasInfoList() {
    return request({
        url: '/comp/query_comp_base_info_list/',
        method: 'get',
        headers: { 'Content-Type': 'application/json' },
        urlType: "comp_api",
    })
}

export function compQueryCompProfileList() {
    return request({
        url: '/comp/query_comp_profile_list/',
        method: 'get',
        headers: { 'Content-Type': 'application/json' },
        urlType: "comp_api",
    })
}

export function knowQueryCompTreeBoardGraphSumDataDict(params) {
    return request({
        url: '/know/query_comp_tree_board_graph_sum_data_dict/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryCompTreeBoardTableSumDataDict(params) {
    return request({
        url: '/know/query_comp_tree_board_table_sum_data_dict/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryCompTreeBoardTableCumulativeDetailList(params) {
    return request({
        url: '/know/query_comp_tree_board_table_cumulative_detail_list/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}

export function knowQueryCompTreeBoardTableChangeDetailList(params) {
    return request({
        url: '/know/query_comp_tree_board_table_change_detail_list/',
        method: 'get',
        params: params,
        urlType: "comp_api",
    })
}