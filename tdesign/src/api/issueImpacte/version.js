import request_assistant_issueImpacte from '@/utils/request_assistant_issueImpacte.js';

// 查询版本列表
export function queryVersion(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/query',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 创建版本
export function createVersion(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/create',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 更新版本
export function updateVersion(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/update',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 删除版本
export function deleteVersion(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/delete',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 获取版本详情
export function getVersionDetail(versionId) {
    return request_assistant_issueImpacte({
        url: `/api/issueImpacte/version/${versionId}`,
        method: 'get',
    })
}

// 查询版本关联的案例列表
export function queryVersionCases(versionId, data) {
    return request_assistant_issueImpacte({
        url: `/api/issueImpacte/version/${versionId}/cases`,
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 获取目标网络选项（从案例发现局点提取）
export function getTargetNetworkOptions() {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/options/target-network',
        method: 'get',
    })
}

// 获取涉及单板选项（从案例单板提取）
export function getBoardOptions() {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/options/boards',
        method: 'get',
    })
}

// 获取版本分支选项（从历史版本分支提取）
export function getBranchOptions() {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/options/branches',
        method: 'get',
    })
}

// 获取归属项目选项（从案例库提取）
export function getBelongProjectOptions() {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/version/options/belong-project',
        method: 'get',
    })
}
