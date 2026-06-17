import request_require_schedule from '@/utils/request_require_schedule.js'

// 人力透视表
export function queryHumanResourcePivotByParams(params) {
    // 处理数组参数：将数组转换为多个同名参数（如 team=value1&team=value2）
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
        let url = '/api/human_resource_pivot/queryHumanResourcePivotByParams?';
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
            url: '/api/human_resource_pivot/queryHumanResourcePivotByParams',
            method: 'get',
            params: processedParams
        });
    }
}

export function getHumanResourcePivotOptions(params) {
    return request_require_schedule({
        url: '/api/human_resource_pivot/getHumanResourcePivotOptions',
        method: 'get',
        params: params
    })
}
