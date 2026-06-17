import request_require_schedule from '@/utils/request_require_schedule.js'

/**
 * 构建含多值数组参数的查询字符串
 * @param {Object} params - 查询参数，数组字段会展开为多个同名参数
 */
function buildQueryString(params) {
    const queryParts = []
    const arrayKeys = ['domain', 'team']
    for (const [key, val] of Object.entries(params)) {
        if (val === undefined || val === null || val === '') continue
        if (arrayKeys.includes(key) && Array.isArray(val)) {
            val.forEach(v => {
                if (v !== undefined && v !== null && v !== '') {
                    queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`)
                }
            })
        } else if (!arrayKeys.includes(key) || !Array.isArray(val)) {
            queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(val)}`)
        }
    }
    return queryParts.join('&')
}

/**
 * 查询可用人力聚合数据
 * @param {Object} params - 查询参数
 * @param {string} params.start_month      - 起始年月，格式 YYYY-MM（必填）
 * @param {string} params.end_month        - 截止年月，格式 YYYY-MM（必填）
 * @param {string} [params.department]     - 部门
 * @param {Array}  [params.domain]         - 领域（多选）
 * @param {Array}  [params.team]           - 团队（多选）
 * @param {string} [params.skill_category] - 技能/特性分类
 */
export function queryAvailableHumanResourceByParams(params) {
    const qs = buildQueryString(params)
    return request_require_schedule({
        url: `/api/available_human_resource/queryAvailableHumanResourceByParams${qs ? '?' + qs : ''}`,
        method: 'get',
    })
}

/**
 * 获取可用人力页面筛选选项
 * 返回：belong_product（固定枚举）、department、domain、team
 */
export function getAvailableHumanResourceOptions() {
    return request_require_schedule({
        url: '/api/available_human_resource/getAvailableHumanResourceOptions',
        method: 'get',
    })
}
