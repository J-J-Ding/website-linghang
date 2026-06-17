import request_mcp from '@/utils/request_mcp.js'

export function askReqManageAgent(signal, data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/ask_req_manage_agent',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
        signal: signal,
    })
}

export function getHistoryChatRecordList(data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/get_history_chat_record_list',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getPromptListBySearchStr(data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/get_prompt_list_by_search_str',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateSinglePromptCcontent(data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/update_single_prompt_content',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function updateSinglePromptReferenceCount(data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/update_single_prompt_reference_count',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function delSinglePrompt(data) {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/del_single_prompt',
        method: 'post',
        headers: {
            'Content-Type': 'application/json',
        },
        data: data,
    })
}

export function getToolNameList() {
    return request_mcp({
        url: '/api/electric_knowledge/req_manage_agent/get_tool_name_list',
        method: 'get',
    })
}
