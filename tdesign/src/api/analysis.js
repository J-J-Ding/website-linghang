import request from '@/utils/request_analysis.js';

export function getAlarmList(data) {
    return request({
        url: '/channel_alarm/alarm_call_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getProjectList(data) {
    return request({
        url: '/project_manage/project_list_new',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function uploadFileList(formData) {
    return request({
        url: '/project_manage/file_upload',
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data', // 改为form-data
        },
        data: formData,
    })
}

export function addProjectList(data) {
    return request({
        url: '/project_manage/project_add_new',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteProjectList(data) {
    return request({
        url: '/project_manage/project_delete_new',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function editProjectList(data) {
    return request({
        url: '/project_manage/project_edit',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryProjectDetail(data) {
    return request({
        url: '/project_manage/project_detail',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryDataParse(data) {
    return request({
        url: '/project_manage/data_parse',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getHistoricalList(data) {
    return request({
        url: '/business_historical/historical_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function searchOMS(data) {
    return request({
        url: '/business_historical/keyword_search_oms',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getAnalysisList(data) {
    return request({
        url: '/business_analysis/analysis_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function searchOMSAlert(data) {
    return request({
        url: '/business_analysis/query_oms_alert',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getFiberList(data) {
    return request({
        url: '/fiber_break/fiber_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function searchHOVAlert(data) {
    return request({
        url: '/fiber_break/query_hov_alert',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getProjectFileList(data) {
    return request({
        url: '/project_manage/project_file_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteUploadFile(data) {
    return request({
        url: '/project_manage/delete_file',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function topologyDataList(data) {
    return request({
        url: '/project_manage/topology_data_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getRenewStatsList(data) {
    return request({
        url: '/renew_stats/renew_stats_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getRenewStatsSum(data) {
    return request({
        url: '/renew_stats/renew_stats_sum',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getRenewDetailList(data) {
    return request({
        url: '/renew_detail/renew_detail_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryAllCall(data) {
    return request({
        url: '/renew_detail/query_all_call',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryActionFlowAllCall(data) {
    return request({
        url: '/action_flow/action_flow_all_call',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function queryActionFlowList(data) {
    return request({
        url: '/action_flow/action_flow_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}
