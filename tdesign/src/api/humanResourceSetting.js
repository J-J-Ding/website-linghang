import request_require_schedule from '@/utils/request_require_schedule.js'

// 需求开发投入人力设置
export function queryHumanResourceSettingByParams(params) {
    // 处理数组参数：将数组转换为多个同名参数（如 team=value1&team=value2）
    // axios 默认会将数组序列化为 team[]=value1&team[]=value2，但 Flask 的 getlist 需要 team=value1&team=value2
    // 所以我们需要手动构建 URL 参数
    const processedParams = {};
    const arrayParams = {};
    
    Object.keys(params).forEach(key => {
        if (Array.isArray(params[key]) && params[key].length > 0) {
            arrayParams[key] = params[key];
        } else {
            processedParams[key] = params[key];
        }
    });
    
    // 如果有数组参数，需要特殊处理
    if (Object.keys(arrayParams).length > 0) {
        // 构建 URL，将数组参数转换为多个同名参数
        let url = '/api/human_resource_setting/queryHumanResourceSettingByParams?';
        const urlParams = new URLSearchParams();
        
        // 添加非数组参数
        Object.keys(processedParams).forEach(key => {
            if (processedParams[key] !== '' && processedParams[key] !== null) {
                urlParams.append(key, processedParams[key]);
            }
        });
        
        // 添加数组参数（每个值作为单独的参数）
        Object.keys(arrayParams).forEach(key => {
            arrayParams[key].forEach(value => {
                urlParams.append(key, value);
            });
        });
        
        url += urlParams.toString();
        
        return request_require_schedule({
            url: url,
            method: 'get'
        });
    } else {
        return request_require_schedule({
            url: '/api/human_resource_setting/queryHumanResourceSettingByParams',
            method: 'get',
            params: processedParams
        });
    }
}

export function aggregateFromPersonSkillMap(params) {
    return request_require_schedule({
        url: '/api/human_resource_setting/aggregateFromPersonSkillMap',
        method: 'get',
        params: params
    })
}

export function updateHumanResourceSetting(data) {
    return request_require_schedule({
        url: '/api/human_resource_setting/updateHumanResourceSetting',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getHumanResourceSettingOptions(params) {
    return request_require_schedule({
        url: '/api/human_resource_setting/getHumanResourceSettingOptions',
        method: 'get',
        params: params
    })
}

export function importHumanResourceSetting(formData) {
    return request_require_schedule({
        url: '/api/human_resource_setting/importHumanResourceSetting',
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        data: formData,
    })
}

export function deleteHumanResourceSetting(data) {
    return request_require_schedule({
        url: '/api/human_resource_setting/deleteHumanResourceSetting',
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        data: data,
    })
}

export function batchDeleteHumanResourceSetting(data) {
    return request_require_schedule({
        url: '/api/human_resource_setting/batchDeleteHumanResourceSetting',
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        data: data,
    })
}

export function exportHumanResourceSetting(params) {
    // 处理数组参数（团队多选）
    const urlParams = new URLSearchParams();
    Object.keys(params || {}).forEach(key => {
        const val = params[key];
        if (Array.isArray(val)) {
            val.forEach(v => urlParams.append(key, v));
        } else if (val !== '' && val !== null && val !== undefined) {
            urlParams.append(key, val);
        }
    });
    return request_require_schedule({
        url: `/api/human_resource_setting/exportHumanResourceSetting?${urlParams.toString()}`,
        method: 'get',
        responseType: 'blob'
    })
}

export function triggerSyncRequirementDevHumanResource(params) {
    return request_require_schedule({
        url: '/api/human_resource_setting/triggerSyncRequirementDevHumanResource',
        method: 'get',
        params: params
    })
}