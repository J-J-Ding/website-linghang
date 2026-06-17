import request_assistant_issueImpacte from '@/utils/request_assistant_issueImpacte.js';

// 查询案例列表
export function queryIssueImpacte(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/query',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 创建案例
export function createIssueImpacte(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/create',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 更新案例
export function updateIssueImpacte(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/update',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 删除案例
export function deleteIssueImpacte(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/delete',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

// 批量导入案例
export function importIssueImpacte(data) {
    // FormData 不需要手动设置 Content-Type，axios 会自动设置正确的 boundary
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/import',
        method: 'post',
        data: data,
    })
}

// 确认案例源
export function confirmCaseSource(data) {
    return request_assistant_issueImpacte({
        url: '/api/issueImpacte/case/confirm_source',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}








