import request_require_schedule from '@/utils/request_require_schedule.js'



// 需求排期助手
export function queryRequirementScheduleByParams(params) {
    return request_require_schedule({
        url: '/api/requirement_schedule/queryRequirementScheduleByParams',
        method: 'get',
        params: params
    })
}

export function updateRequirementSchedule(data) {
    return request_require_schedule({
        url: '/api/requirement_schedule/updateRequirementSchedule',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getFilterHistory(params) {
    return request_require_schedule({
        url: '/api/requirement_schedule/getFilterHistory',
        method: 'get',
        params: params
    })
}

export function saveFilterHistory(data) {
    return request_require_schedule({
        url: '/api/requirement_schedule/saveFilterHistory',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function checkEditPermission() {
    return request_require_schedule({
        url: '/api/requirement_schedule/checkEditPermission',
        method: 'get',
    })
}

// 从 RDC 平台同步数据到 requirement_schedule_table
export function syncRdcData(data) {
    return request_require_schedule({
        url: '/api/requirement_schedule/syncRdcData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 需求自动排期 - 调用 pr_sort 进行PR优先级排序
export function autoScheduling(data) {
    return request_require_schedule({
        url: '/api/requirement_schedule/autoScheduling',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 预览待回填到 RDC 的需求数量（不执行回填操作）
export function previewBackfillRdcData(data = {}) {
    return request_require_schedule({
        url: '/api/requirement_schedule/previewBackfillRdcData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data,
    })
}

// 数据回填到 RDC（根据 task_time_mapping 中的排期结果回写 work items）
export function backfillRdcData(data = {}) {
    return request_require_schedule({
        url: '/api/requirement_schedule/backfillRdcData',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data,
    })
}

// 手动触发同步需求交付人力投入数据
export function triggerSyncRequirementDevHumanResource(params) {
    return request_require_schedule({
        url: '/api/human_resource_setting/triggerSyncRequirementDevHumanResource',
        method: 'get',
        params: params
    })
}