import request_board_chat from '@/utils/request_board_chat.js'

export function boardChatChatRequest(payload, config = {}) {
    return request_board_chat({
        url: '/chat/',
        method: 'post',
        data: payload,
        ...config
    })
}

export function boardChatFeedbackRequest(payload, config = {}) {
    return request_board_chat({
        url: '/boardChatFeedbackRequest',
        method: 'post',
        data: payload,
        timeout: 15000, // 15秒超时
        ...config
    })
}

export function getBoardChatFeedbackStats(config = {}) {
    return request_board_chat({
        url: '/getBoardChatFeedbackStats',
        method: 'get',
        ...config
    })
}

export function getMonthlyBadFeedbackRate(config = {}) {
    return request_board_chat({
        url: '/getMonthlyBadFeedbackRate',
        method: 'get',
        ...config
    })
}

export function get_support_list(config = {}) {
    return request_board_chat({
        url: '/get_support_list',
        method: 'get',
        ...config
    })
}


export function getBoardChatUserStats(config = {}) {
    return request_board_chat({
        url: '/getBoardChatUserStats',
        method: 'get',
        ...config
    })
}

export function getBoardChatAccessStatsData(config = {}) {
    return request_board_chat({
        url: '/getBoardChatAccessStatsData',
        method: 'get',
        ...config
    })
}

export function getBoardChatUserRecords(config = {}) {
    return request_board_chat({
        url: '/getBoardChatUserRecords',
        method: 'get',
        ...config
    })
}

export function getBoardStatistics(config = {}) {
    return request_board_chat({
        url: '/getBoardStatistics',
        method: 'get',
        ...config
    })
}

export function getAllUsersConversationSummary(config = {}) {
    return request_board_chat({
        url: '/getAllUsersConversationSummary',
        method: 'get',
        ...config
    })
}

export function BoardChatDashboardRequest(payload, config = {}) {
    return request_board_chat({
        url: '/BoardChatDashboardRequest',
        method: 'post',
        data: payload,
        ...config
    })
}

export function boardChatCreateChatEventSource(sessionId, options = {}) {
    // const baseUrl = 'http://10.156.128.2:7654/chat/SSE';
    const baseUrl = window.location.origin + '/boardChat/chat/SSE';
    const url = new URL(baseUrl + '?session_id=' + sessionId);

    url.searchParams.append('session_id', sessionId);

    // 其他自定义参数（可选）
    Object.entries(options).forEach(([key, value]) => {
        url.searchParams.append(key, value);
    });

    return new EventSource(url.toString());
}

export function generalChatCreateChatEventSource(sessionId, options = {}) {
    const baseUrl = window.location.origin + '/boardChat/general_chat/SSE';  // 不同的SSE端点
    const url = new URL(baseUrl + '?session_id=' + sessionId);
    url.searchParams.append('session_id', sessionId);
    
    Object.entries(options).forEach(([key, value]) => {
        url.searchParams.append(key, value);
    });

    return new EventSource(url.toString());
}

// 新增通用智能助手聊天请求
export function generalChatRequest(payload, config = {}) {
    return request_board_chat({
        url: '/general_chat/',  // 使用不同的接口路径
        method: 'post',
        data: payload,
        ...config
    })
}

// 新增通用智能助手反馈请求
export function generalChatFeedbackRequest(payload, config = {}) {
    return request_board_chat({
        url: '/generalChatFeedbackRequest',  // 使用不同的反馈接口
        method: 'post',
        data: payload,
        timeout: 15000,
        ...config
    })
}

export function generalChatDashboardRequest(payload, config = {}) {
    return request_board_chat({
        url: '/generalChatDashboardRequest',
        method: 'post',
        data: payload,
        ...config
    })
}

export function download_feedback_excel(config = {}) {
    return request_board_chat({
      url: '/download_feedback_excel',
      method: 'get',
      responseType: 'blob', // 重要：指定响应类型为blob
      ...config
    })
}

export function download_failed_conversations_excel(config = {}) {
    return request_board_chat({
      url: '/download_failed_conversations_excel',
      method: 'get',
      responseType: 'blob', // 重要：指定响应类型为blob
      ...config
    })
}