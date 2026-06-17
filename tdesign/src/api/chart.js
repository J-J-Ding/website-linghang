import request_chart from '@/utils/request_chart.js';

export function queryChartData(data) {
    return request_chart({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_summary_line_data_list_by_preplanning_and_date',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryTableData(data) {
    return request_chart({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_summary_table_data_list_by_preplanning_and_date',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryPreplan() {
    return request_chart({
        url: '/api/electric_knowledge/req_manage_board/query_preplanning_list',
        method: 'get',
    })
}

export function queryManageBoard(data) {
    return request_chart({
        url: '/api/electric_knowledge/req_manage_board/query_req_manage_board_pr_split_detail_table_data_list_by_preplanning_and_date',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}
