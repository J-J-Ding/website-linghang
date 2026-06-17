import request_require_schedule from '@/utils/request_require_schedule.js'

// 版本视图
export function queryVersionTableByParams(params) {
    return request_require_schedule({
        url: '/api/version_table/queryVersionTableByParams',
        method: 'get',
        params: params
    })
}

export function createVersionTable(data) {
    return request_require_schedule({
        url: '/api/version_table/createVersionTable',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateVersionTable(data) {
    return request_require_schedule({
        url: '/api/version_table/updateVersionTable',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deleteVersionTable(data) {
    return request_require_schedule({
        url: '/api/version_table/deleteVersionTable',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getVersionTableOptions(params) {
    return request_require_schedule({
        url: '/api/version_table/getVersionTableOptions',
        method: 'get',
        params: params
    })
}

export function importVersionTable(data) {
    return request_require_schedule({
        url: '/api/version_table/importVersionTable',
        method: 'post',
        data: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function exportVersionTable(params) {
    return request_require_schedule({
        url: '/api/version_table/exportVersionTable',
        method: 'get',
        params: params,
        responseType: 'blob'
    })
}
