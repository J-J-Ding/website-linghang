import request_assistant from '@/utils/request_assistant.js'
import request_assistant_new from '@/utils/request_assistant_new.js'

export function getBoardNamestFactorRelationByParams() {
    return request_assistant({
        url: '/api/boardAssembly/getBoardNamestFactorRelationByParams',
        method: 'get',
    })
}

export function getBusinessModels() {
    return request_assistant({
        url: '/api/boardAssembly/getBusinessModels',
        method: 'get',
    })
}

export function generateElements(data) {
    return request_assistant({
        url: '/api/boardAssembly/generateElements',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function generateFramework(data) {
    return request_assistant_new({
        url: '/api/boardAssembly/generateFramework',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function generateConfig(data) {
    return request_assistant({
        url: '/api/boardAssembly/generateConfig',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}






