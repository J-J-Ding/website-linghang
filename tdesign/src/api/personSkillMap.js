import request_require_schedule from '@/utils/request_require_schedule.js'

// 人员技能地图
export function queryPersonSkillMapByParams(params) {
    return request_require_schedule({
        url: '/api/person_skill_map/queryPersonSkillMapByParams',
        method: 'get',
        params: params
    })
}

export function createPersonSkillMap(data) {
    return request_require_schedule({
        url: '/api/person_skill_map/createPersonSkillMap',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updatePersonSkillMap(data) {
    return request_require_schedule({
        url: '/api/person_skill_map/updatePersonSkillMap',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function deletePersonSkillMap(data) {
    return request_require_schedule({
        url: '/api/person_skill_map/deletePersonSkillMap',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getPersonSkillMapOptions(params) {
    return request_require_schedule({
        url: '/api/person_skill_map/getPersonSkillMapOptions',
        method: 'get',
        params: params
    })
}

export function importPersonSkillMap(data) {
    return request_require_schedule({
        url: '/api/person_skill_map/importPersonSkillMap',
        method: 'post',
        data: data,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

export function exportPersonSkillMap(params) {
    return request_require_schedule({
        url: '/api/person_skill_map/exportPersonSkillMap',
        method: 'get',
        params: params,
        responseType: 'blob'
    })
}