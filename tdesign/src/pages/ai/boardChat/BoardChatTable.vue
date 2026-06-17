<template>
    <div class="kanban-main">
        <t-tooltip content="返回单板助手" placement="right">
          <t-button 
            class="back-button-circle"
            theme="primary" 
            shape="circle"
            variant="base"
            @click="goBackToBoardChat">
            <icon name="arrow-left" style="color: white;" /> <!-- 白色向左箭头 -->
          </t-button>
        </t-tooltip>

      <t-space direction="vertical">
        <t-space>
          <!-- 卡片1：单板助手用户对话统计卡片 -->
          <t-card :title="card1Title" class="kanban-card" hover-shadow>
            <template #actions>
              <t-space direction="vertical" align="center" class="card-actions-container">
                <!-- 按钮区域 - 下载按钮在左边，刷新按钮在右边 -->
                <t-space align="center">
                  <!-- 下载失败对话按钮在左边 -->
                  <t-tooltip content="下载失败对话表" placement="top">
                    <t-button 
                      shape="circle" 
                      variant="outline" 
                      @click="handleDownloadFailedConversationsExcel"
                      :loading="downloadingFailedConversations"
                      class="download-btn"
                    >
                      <icon name="download" />
                    </t-button>
                  </t-tooltip>
                
                  <!-- 刷新按钮在右边 -->
                  <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                    <icon name="refresh" />
                  </t-button>
                </t-space>
                <!-- 下载失败对话提示消息 -->
                <div v-if="downloadFailedConversationsMessage" 
                     class="download-failed-message" 
                     :class="downloadFailedConversationsMessageType">
                  {{ downloadFailedConversationsMessage }}
                </div>
              </t-space>
            </template>
            <div class="combined-stats-container">
              <div class="board-chat-user-stats">
                <t-space size="large">
                  <div class="board-chat-stat-item">
                    <div class="board-chat-stat-label">累计用户数</div>
                    <div class="board-chat-stat-value">{{ boardChatUserStats.totalUsers }}</div>
                  </div>
                  <div class="board-chat-stat-item">
                    <div class="board-chat-stat-label">本周新增用户数</div>
                    <div class="board-chat-stat-value">{{ boardChatUserStats.weeklyUsers }}</div>
                    <div class="board-chat-stat-trend" :class="boardChatUserStats.weeklyTrend >= 0 ? 'trend-up' : 'trend-down'">
                      <icon :name="boardChatUserStats.weeklyTrend >= 0 ? 'caret-up' : 'caret-down'" />
                      {{ Math.abs(boardChatUserStats.weeklyTrend) }}%
                    </div>
                  </div>
                  <div class="board-chat-stat-item">
                    <div class="board-chat-stat-label">上周新增用户数</div>
                    <div class="board-chat-stat-value">{{ boardChatUserStats.lastWeekUsers }}</div>
                  </div>
                </t-space>
              </div>
              <div class="stats-divider"></div>
              <div class="conversation-stats-section">
                <!-- 统计数字显示 -->
                <div class="conversation-stats-layout">
                  <div class="conversation-stats-vertical">
                    <div class="conversation-stat-item">
                      <div class="conversation-stat-label">累计对话次数</div>
                      <div class="conversation-stat-value">{{ conversationStats.total_conversations }}</div>
                    </div>
                    <div class="conversation-stat-vertical-item">
                      <div class="conversation-stat-label success-rate">成功次数（成功率）</div>
                      <div class="conversation-stat-value success">
                        {{ conversationStats.total_success_count }}次（{{ conversationStats.total_success_rate }}%）
                      </div>
                    </div>
                    <div class="conversation-stat-vertical-item">
                      <div class="conversation-stat-label failure-rate">失败次数（失败率）</div>
                      <div class="conversation-stat-value failure">
                        {{ conversationStats.total_failure_count }}次（{{ conversationStats.total_failure_rate }}%）
                      </div>
                    </div>
                  </div>
                  <!-- 饼图 -->
                  <div class="conversation-chart-container">
                    <div id="conversationStatsChart" style="width: 100%; height: 300px"></div>
                  </div>
                </div>
              </div>
            </div>
          </t-card>
  
          <!-- 卡片2：单板助手访问量统计卡片 -->
          <t-card :title="card2Title" class="kanban-card" hover-shadow>
            <template #actions>
              <t-space>
                <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                  <icon name="refresh" />
                </t-button>
                <t-radio-group variant="default-filled" :value="boardChatSelectedRange.days" @change="handleBoardChatTimeRangeChange">
                  <t-radio-button value="7">最近7天</t-radio-button>
                  <t-radio-button value="30">最近30天</t-radio-button>
                  <t-radio-button value="90">最近90天</t-radio-button>
                </t-radio-group>
              </t-space>
            </template>
            <div id="boardChatAccessStatsChart" style="width: 100%; height: 500px"></div>
          </t-card>
        </t-space>
  
        <t-space>
          <!-- 卡片3：单板助手单板访问表格 -->
          <t-card :title="card3Title" class="kanban-card" hover-shadow>
            <template #actions>
              <t-space>
                <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                  <icon name="refresh" />
                </t-button>
              </t-space>
            </template>
            <div id="boardChatBoardAccessChart" style="width: 100%; height: 500px"></div>
          </t-card>
          <!-- 卡片4：单板助手用户访问记录表格 -->
          <t-card :title="card4Title" class="kanban-card" hover-shadow>
            <template #actions>
              <t-space>
                <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                  <icon name="refresh" />
                </t-button>
              </t-space>
            </template>
            <t-table 
              :data="boardChatUserRecords" 
              :columns="boardChatRecordColumns" 
              :hover="true" 
              :max-height="480"
              rowKey="recordId"
              class="board-chat-records-table"
            />
          </t-card>
        </t-space>
        <!-- 卡片5：用户满意度 -->
        <t-space>
          <t-card :title="card5Title" class="kanban-card" hover-shadow>
            <template #actions>
              <t-space direction="vertical" align="center" class="card-actions-container">
                <!-- 按钮区域 -->
                <t-space align="center">
                  <t-tooltip content="下载评价表" placement="top">
                    <t-button 
                      shape="circle" 
                      variant="outline" 
                      @click="handleDownloadFeedbackExcel"
                      :loading="downloadingFeedbackExcel"
                      class="download-btn"
                    >
                      <icon name="download" />
                    </t-button>
                  </t-tooltip>

                  <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                    <icon name="refresh" />
                  </t-button>
                </t-space>
                
                <!-- 提示消息区域 -->
                <div v-if="downloadMessage" class="download-message" :class="downloadMessageType">
                  {{ downloadMessage }}
                </div>
              </t-space>
            </template>
            <div class="feedback-stats-container">
              <!-- 上部：满意度统计 -->
              <div class="satisfaction-stats-section">
                <div class="satisfaction-stats-layout">
                  <!-- 左侧：统计数字 -->
                  <div class="satisfaction-stats-vertical">
                    <div class="satisfaction-stat-item">
                      <div class="satisfaction-stat-label">累计收到评论数</div>
                      <div class="satisfaction-stat-value">{{ feedbackStats.total_feedbacks }}次</div>
                    </div>
                    <div class="satisfaction-stat-vertical-item">
                      <div class="satisfaction-stat-label good-rate">好评数（好评率）</div>
                      <div class="satisfaction-stat-value good">
                        {{ feedbackStats.good_feedbacks }}次（{{ feedbackStats.good_rate }}%）
                      </div>
                    </div>
                    <div class="satisfaction-stat-vertical-item">
                      <div class="satisfaction-stat-label bad-rate">差评数（差评率）</div>
                      <div class="satisfaction-stat-value bad">
                        {{ feedbackStats.bad_feedbacks }}次（{{ feedbackStats.bad_rate }}%）
                      </div>
                    </div>
                  </div>
                  <!-- 右侧：饼图 -->
                  <div class="satisfaction-chart-container">
                    <div id="feedbackStatsChart" style="width: 100%; height: 180px"></div>
                  </div>
                </div>
              </div>
              <!-- 分隔线 -->
              <div class="section-divider"></div>
              <!-- 下部：月度差评率趋势 -->
              <div class="negative-trend-section">
                <div id="negativeTrendChart" style="width: 100%; height: 300px"></div>
              </div>
            </div>
          </t-card>
        </t-space>        
      </t-space>
    </div>
  </template>
  
  <script setup lang="jsx">
  import axios from 'axios';
  import * as echarts from 'echarts';
  import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { MessagePlugin } from 'tdesign-vue-next';
  import { Icon } from 'tdesign-icons-vue-next';
  import { getBoardChatUserStats, getBoardChatAccessStatsData, getBoardChatUserRecords, getBoardStatistics, getAllUsersConversationSummary, 
            getBoardChatFeedbackStats, getMonthlyBadFeedbackRate, download_feedback_excel, download_failed_conversations_excel} from '@/api/boardChat.js';
  
  const router = useRouter();
  const goBackToBoardChat = () => {
    router.back();
};

  // 图表标题
  const card1Title = '用户对话统计';
  const card2Title = '访问量统计';
  const card3Title = '单板访问统计';
  const card4Title = '用户访问记录';
  const card5Title = '用户满意度';
  const downloadingFeedbackExcel = ref(false);
  const downloadMessage = ref(''); // 下载提示消息
  const downloadMessageType = ref(''); // 消息类型：success/error
  const downloadingFailedConversations = ref(false);
  const downloadFailedConversationsMessage = ref('');
  const downloadFailedConversationsMessageType = ref('');

  // 单板维护助手时间范围选项
  const boardChatTimeRanges = [
    { label: '最近7天', days: '7' },
    { label: '最近30天', days: '30' },
    { label: '最近90天', days: '90' },
  ];
  const boardChatSelectedRange = ref(boardChatTimeRanges[0]);
  
  // 单板维护助手用户规模统计相关数据
  const boardChatUserStats = ref({
    totalUsers: 0,
    weeklyUsers: 0,
    lastWeekUsers: 0,
    weeklyTrend: 0
  });
  
  // 单板维护助手访问量统计数据
  const boardChatAccessStatsData = ref([]);
  
  // 单板维护助手用户访问记录数据
  const boardChatUserRecords = ref([]);
  
  const boardChatBoardAccessStats = ref([]);
  
  // 单板维护助手用户记录表格列定义
  const boardChatRecordColumns = [
    { colKey: 'rank', title: '序号', width: 40 },
    { colKey: 'user_id', title: '用户ID', width: 60 },
    { colKey: 'visit_count', title: '访问次数', width: 40 },
    { colKey: 'last_visit', title: '最近访问时间', width: 60 },
  ];

  // 单板助手对话统计数据
  const conversationStats = ref({
    total_conversations: 0,
    total_success_count: 0,
    total_failure_count: 0,
    total_success_rate: 0,
    total_failure_rate: 0
  });

  // 用户满意度统计数据
  const feedbackStats = ref({
    total_feedbacks: 0,
    good_feedbacks: 0,
    bad_feedbacks: 0,
    good_rate: 0,
    bad_rate: 0
  });

  // 访问量统计图表实例
  let boardChatAccessStatsChart = null;
  let boardChatBoardAccessChart = null;
  let conversationStatsChart = null;
  let feedbackStatsChart = null;
  let negativeTrendChart = null;

  // 单板维护助手数据存储
  const boardChatUserStatsData = ref({});
  const boardChatAccessStatsChartData = ref([]);
  const boardChatUserRecordsData = ref([]);
  const boardChatBoardStatsData = ref([]);
  const negativeTrendData = ref([]);

// 添加下载失败对话表的函数
const handleDownloadFailedConversationsExcel = async () => {
  try {
    downloadingFailedConversations.value = true;
    downloadFailedConversationsMessage.value = '';

    const response = await download_failed_conversations_excel();

    if (!response.data || response.data.size === 0) {
      downloadFailedConversationsMessage.value = '下载失败：文件为空';
      downloadFailedConversationsMessageType.value = 'error';
      return;
    }

    // 创建下载链接
    const blob = response.data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    const now = new Date();
    const dateStr = `${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}`;
    link.download = `对话失败记录表_${dateStr}.xlsx`;
    
    link.href = url;
    document.body.appendChild(link);
    link.click();
    
    // 清理
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    }, 100);

    // 显示成功提示
    downloadFailedConversationsMessage.value = '失败对话表下载成功';
    downloadFailedConversationsMessageType.value = 'success';
    setTimeout(() => {
      downloadFailedConversationsMessage.value = '';
      downloadFailedConversationsMessageType.value = '';
    }, 2000);
  } catch (error) {
    console.error('下载失败对话表失败:', error);
    // 显示错误提示
    let errorMsg = '下载失败';
    if (error.response) {
      if (error.response.status === 404) {
        errorMsg = '下载失败：API接口不存在';
      } else if (error.response.status === 401 || error.response.status === 403) {
        errorMsg = '下载失败：无权限访问';
      } else if (error.response.status === 500) {
        errorMsg = '下载失败：服务器内部错误';
      } else {
        errorMsg = `下载失败：服务器错误 ${error.response.status}`;
      }
    } else if (error.request) {
      errorMsg = '下载失败：网络错误或无响应';
    } else {
      errorMsg = '下载失败：' + error.message;
    }
    
    downloadFailedConversationsMessage.value = errorMsg;
    downloadFailedConversationsMessageType.value = 'error';
    
    // 3秒后自动隐藏错误提示
    setTimeout(() => {
      downloadFailedConversationsMessage.value = '';
      downloadFailedConversationsMessageType.value = '';
    }, 3000);
  } finally {
    downloadingFailedConversations.value = false;
  }
};

// 添加下载评价表的函数
const handleDownloadFeedbackExcel = async () => {
  try {
    downloadingFeedbackExcel.value = true;
    downloadMessage.value = '';

    const response = await download_feedback_excel();

    if (!response.data || response.data.size === 0) {
      downloadMessage.value = '下载失败：文件为空';
      downloadMessageType.value = 'error';
      return;
    }

    // 创建下载链接
    const blob = response.data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    const now = new Date();
    const dateStr = `${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}`;
    link.download = `用户满意度评价表_${dateStr}.xlsx`;
    
    link.href = url;
    document.body.appendChild(link);
    link.click();
    
    // 清理
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    }, 100);

    // 显示成功提示
    downloadMessage.value = '评价表下载成功';
    downloadMessageType.value = 'success';
    setTimeout(() => {
      downloadMessage.value = '';
      downloadMessageType.value = '';
    }, 2000);
  } catch (error) {
    console.error('下载失败:', error);
    // 显示错误提示
    let errorMsg = '下载失败';
    if (error.response) {
      if (error.response.status === 404) {
        errorMsg = '下载失败：API接口不存在';
      } else if (error.response.status === 401 || error.response.status === 403) {
        errorMsg = '下载失败：无权限访问';
      } else if (error.response.status === 500) {
        errorMsg = '下载失败：服务器内部错误';
      } else {
        errorMsg = `下载失败：服务器错误 ${error.response.status}`;
      }
    } else if (error.request) {
      errorMsg = '下载失败：网络错误或无响应';
    } else {
      errorMsg = '下载失败：' + error.message;
    }
    
    downloadMessage.value = errorMsg;
    downloadMessageType.value = 'error';
    
    // 3秒后自动隐藏错误提示
    setTimeout(() => {
      downloadMessage.value = '';
      downloadMessageType.value = '';
    }, 3000);
  } finally {
    downloadingFeedbackExcel.value = false;
  }
};

// 获取用户满意度统计数据的API函数（包含趋势数据）
const GetFeedbackStats = async () => {
  try {
    const res = await getBoardChatFeedbackStats();

    if (res.status === 'success' && res.data) {
      return res.data;
    }
    // 如果API返回空数据，返回默认值
    return {
      total_feedbacks: 0,
      good_feedbacks: 0,
      bad_feedbacks: 0,
      good_rate: 0,
      bad_rate: 0
    };
  } catch (err) {
    // 如果请求失败，返回默认值
    console.error('用户满意度统计数据请求失败:', err);
    return {
      total_feedbacks: 0,
      good_feedbacks: 0,
      bad_feedbacks: 0,
      good_rate: 0,
      bad_rate: 0
    };
  }
};

// 获取月度差评率趋势数据的API函数
const GetMonthlyBadFeedbackRate = async () => {
  try {
    const res = await getMonthlyBadFeedbackRate();

    if (res.status === 'success' && res.data) {
      return res.data;
    }
    // 如果API返回空数据，返回空数组
    return [];
  } catch (err) {
    // 如果请求失败，返回空数组
    console.error('月度差评率数据请求失败:', err);
    return [];
  }
};

  // 获取单板维护助手用户规模统计数据
  const GetBoardChatUserStats = async () => {
    try {
      const res = await getBoardChatUserStats();
      if (res.status === 'success' && res.data) {
        return res.data;
      }
      // 如果API返回空数据，返回默认值
      return {
        totalUsers: 0,
        weeklyUsers: 0,
        lastWeekUsers: 0,
        weeklyTrend: 0
      };
    } catch (err) {
      // 如果请求失败，返回默认值
      console.error('单板维护助手用户规模数据请求失败:', err);
      return {
        totalUsers: 0,
        weeklyUsers: 0,
        lastWeekUsers: 0,
        weeklyTrend: 0
      };
    }
  };
  
  // 获取单板维护助手访问量统计数据
  const GetBoardChatAccessStatsData = async () => {
    try {
      const res = await getBoardChatAccessStatsData({
        days: parseInt(boardChatSelectedRange.value.days)
      });
  
      if (res.status === 'success' && res.data) {
        // 根据选择的时间范围返回对应的数据
        const days = parseInt(boardChatSelectedRange.value.days);
        let data = [];
        
        if (days === 7 && res.data.week) {
          data = res.data.week;
        } else if (days === 30 && res.data.month) {
          data = res.data.month;
        } else if (days === 90 && res.data.quarter) {
          data = res.data.quarter;
        }
  
        // 统一数据格式，将data字段改为date
        return data.map(item => ({
          date: item.date, // 将data字段改为date
          count: item.count
        }));
  
        return res.data;
      }
      // 如果API返回空数据，返回空数组，让图表函数生成默认数据
      console.log('API返回空数据，使用默认图表数据');
      return [];
    } catch (err) {
      // 如果请求失败，返回空数组
      console.error('单板维护助手访问量统计数据请求失败:', err);
      return [];
    }
  };

  // 获取单板维护助手用户访问记录数据
  const GetBoardChatUserRecords = async () => {
    try {
      const res = await getBoardChatUserRecords({
        period: parseInt(boardChatSelectedRange.value.days)
      });
      if (res.status === 'success' && res.users) {
        return res.users;
      }
      // 如果API返回空数据，返回空数组
      return [];
    } catch (err) {
      // 如果请求失败，返回空数组
      console.error('单板维护助手用户记录数据请求失败:', err);
      return [];
    }
  };
  
  const GetBoardChatBoardAccessStats = async () => {
    try {
      const res = await getBoardStatistics();
    
      if (res.status === 'success' && res.boards) {
      // 对数据进行排序：按访问次数降序排列
      const sortedData = res.boards
        .map(item => ({
          board_name: item.board_name,
          visit_count: item.visit_count || 0,
        }))
        .sort((a, b) => b.visit_count - a.visit_count);
      
        return sortedData;
      }
      // 如果API返回空数据，返回空数组
      return [];
    } catch (err) {
      console.error('单板访问统计数据请求失败:', err);
      // 请求失败时返回模拟数据
      return [];
    }
  };

  // 获取对话统计数据的API函数
  const GetConversationStats = async () => {
    try {
      const res = await getAllUsersConversationSummary();

      if (res.status === 'success' && res.data) {
        return res.data;
      }
      // 如果API返回空数据，返回默认值
      return {
        total_conversations: 0,
        total_success_count: 0,
        total_failure_count: 0,
        total_success_rate: 0,
        total_failure_rate: 0
      };
    } catch (err) {
      // 如果请求失败，返回默认值
      console.error('对话统计数据请求失败:', err);
      return {
        total_conversations: 0,
        total_success_count: 0,
        total_failure_count: 0,
        total_success_rate: 0,
        total_failure_rate: 0
      };
    }
  };

// 更新用户满意度统计图表函数
function updateFeedbackStatsChart() {
  const { 
    good_feedbacks, 
    bad_feedbacks, 
    good_rate, 
    bad_rate 
  } = feedbackStats.value;

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const { name, value, percent } = params;
        if (name === '好评') {
          return `好评: ${good_feedbacks}次 (${percent}%)`;
        } else if (name === '差评') {
          return `差评: ${bad_feedbacks}次 (${percent}%)`;
        }
        return `${name}: ${value}%`;
      }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      data: ['好评', '差评']
    },
    series: [
      {
        name: '评论分布',
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold',
            formatter: '{b}: {c}%'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: good_rate,
            name: '好评',
            itemStyle: {
              color: '#52c41a' // 好评-绿色
            }
          },
          {
            value: bad_rate,
            name: '差评',
            itemStyle: {
              color: '#ff4d4f' // 差评-红色
            }
          }
        ]
      }
    ]
  };

  if (feedbackStatsChart) {
    feedbackStatsChart.setOption(option, true);
  }
}

function generateMonthList(monthCount = 12) {
  const months = [];
  const currentDate = new Date();
  
  for (let i = monthCount - 1; i >= 0; i--) {
    const date = new Date(currentDate);
    date.setMonth(date.getMonth() - i);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    months.push(`${year}年${month}月`);
  }
  
  return months;
}

// 更新月度差评率趋势图表函数
function updateNegativeTrendChart() {
  // 如果API返回了趋势数据，使用API数据；否则使用默认数据
  let trendData = negativeTrendData.value || [];
  
  // 如果没有数据，显示空图表
  if (trendData.length === 0) {
    const option = {
      backgroundColor: '#ffffff',
      title: {
        text: '月度差评率趋势（%）',
        left: 'center',
        top: 5, // 减小顶部距离
        textStyle: {
          fontSize: 14, // 减小标题字体
          fontWeight: 'normal'
        }
      },
      xAxis: {
        type: 'category',
        data: [],
        axisLine: {
          show: true,
          lineStyle: {
            color: '#ccc',
            width: 1
          }
        },
        axisTick: {
          show: true,
          alignWithLabel: true,
          lineStyle: {
            color: '#ccc'
          }
        },
        axisLabel: {
          show: true,
          color: '#666',
          fontSize: 10 // 减小横坐标字体
        }
      },
      yAxis: {
        type: 'value',
        name: '差评率 (%)',
        nameLocation: 'end',
        nameTextStyle: {
          fontSize: 12, // 减小纵坐标名称字体
          color: '#666',
          fontWeight: 'bold'
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: '#ccc',
            width: 1
          }
        },
        axisTick: {
          show: true
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#f0f0f0',
            type: 'solid'
          }
        },
        min: 0,
        max: 10,
        interval: 1 // 减小纵坐标间隔为1%
      },
      series: [
        {
          name: '差评率',
          type: 'line',
          data: []
        }
      ],
      grid: {
        left: '12%', // 增加左边距
        right: '5%',
        bottom: '30%', // 大幅增加底部空间
        top: '15%', // 减小顶部空间
        containLabel: false
      }
    };
    
    if (negativeTrendChart) {
      negativeTrendChart.setOption(option, true);
    }
    return;
  }

  // 按月份排序（从早到晚）
  const sortedData = [...trendData].sort((a, b) => {
    const dateA = new Date(a.month.replace('年', '-').replace('月', ''));
    const dateB = new Date(b.month.replace('年', '-').replace('月', ''));
    return dateA - dateB;
  });

  const labels = sortedData.map(item => item.month);
  const values = sortedData.map(item => item.rate);

  // 计算Y轴配置
  const maxValue = Math.max(...values);
  let yMax = 10; // 默认最大值10%
  let yInterval = 2; // 默认间隔2%

  if (maxValue > 0) {
    yMax = Math.ceil(maxValue / 2) * 2 + 2; // 向上取整并留出一些空间
    yInterval = Math.max(1, Math.ceil(yMax / 5)); // 动态计算间隔
  }

  const option = {
    backgroundColor: '#ffffff',
    title: {
      text: '月度差评率趋势（%）',
      left: 'center',
      top: 5,
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const data = params[0];
        return `${data.name}<br/>差评率: ${data.value}%`;
      }
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: {
        show: true,
        lineStyle: {
          color: '#ccc',
          width: 1
        }
      },
      axisTick: {
        show: true,
        alignWithLabel: true,
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        show: true,
        rotate: 45,
        color: '#666',
        fontSize: 10,
        margin: 15,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '差评率 (%)',
      nameLocation: 'end',
      nameTextStyle: {
        fontSize: 12,
        color: '#666',
        fontWeight: 'bold',
        padding: [0, 0, 5, 0] // 调整名称位置
      },
      min: 0,
      max: yMax,
      interval: yInterval,
      axisLine: {
        show: true,
        lineStyle: {
          color: '#ccc',
          width: 1
        }
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: '#ccc'
        },
        length: 3
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: '#f0f0f0',
          type: 'solid',
          width: 1
        }
      },
      axisLabel: {
        show: true,
        color: '#666',
        fontSize: 10,
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '差评率',
        type: 'line',
        data: values,
        itemStyle: {
          color: '#ff4d4f' // 红色折线
        },
        lineStyle: {
          width: 2,
          color: '#ff4d4f'
        },
        symbol: 'circle',
        symbolSize: 6,
        symbolKeepAspect: true,
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%',
          color: '#ff4d4f',
          fontSize: 10,
          fontWeight: 'bold'
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            borderWidth: 1,
            borderColor: '#fff',
            shadowBlur: 5,
            shadowColor: 'rgba(255, 77, 79, 0.5)'
          }
        }
      }
    ],
    grid: {
      left: '12%',
      right: '5%',
      bottom: '30%',
      top: '15%',
      containLabel: false
    }
  };

  if (negativeTrendChart) {
    negativeTrendChart.setOption(option, true);
  }
}

  // 更新单板维护助手用户规模统计显示
  function updateBoardChatUserStats() {
    // 如果API返回空数据，使用默认值
    if (!boardChatUserStatsData.value || Object.keys(boardChatUserStatsData.value).length === 0) {
      boardChatUserStats.value = {
        totalUsers: 0,
        weeklyUsers: 0,
        lastWeekUsers: 0,
        weeklyTrend: 0
      };
    } else {
      boardChatUserStats.value = boardChatUserStatsData.value;
    }
  }
  
  // 生成默认的访问量数据
  function generateDefaultAccessData() {
    const days = parseInt(boardChatSelectedRange.value.days);
    const data = [];
    const now = new Date();
    
    // 多天数据 - 按日期
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      // 修正日期格式：YYYY-MM-DD
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
      data.push({
      date: dateStr,
      count: 0
      });
    }
  
    return data;
  }
  
  // 更新单板维护助手访问量统计图表
  function updateBoardChatAccessStatsChart() {
    // 如果API返回空数据，生成默认的图表数据
    if (!boardChatAccessStatsChartData.value || boardChatAccessStatsChartData.value.length === 0) {
      // 生成默认的访问量数据
      const defaultData = generateDefaultAccessData();
      boardChatAccessStatsChartData.value = defaultData;
    }
  
    const labels = boardChatAccessStatsChartData.value.map(item => item.date);
    const values = boardChatAccessStatsChartData.value.map(item => item.count);
  
    // 计算Y轴最大值，根据数据范围动态调整
    const maxValue = Math.max(...values);
    let yMax, yInterval;
    
    if (maxValue === 0) {
      yMax = 10; // === 修改：默认最大值改为10 ===
      yInterval = 5; // 默认间隔
    } else {
      yMax = Math.ceil(maxValue / 5) * 5; // 确保是5的倍数
      yInterval = Math.max(5, Math.ceil(yMax / 5)); // 坐标间隔至少为5
    }
  
    // 根据数据点数量调整显示效果
    const dataLength = labels.length;
    const rotateAngle = dataLength > 30 ? 45 : (dataLength > 15 ? 30 : 0);
    const bottomMargin = dataLength > 30 ? '15%' : (dataLength > 15 ? '12%' : '10%');
    const showLabel = dataLength <= 30;
    const barWidth = dataLength > 30 ? '40%' : (dataLength > 15 ? '50%' : '60%');
  
    const option = {
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params) => {
          const data = params[0];
          return `${data.name}<br/>访问量: ${data.value}`;
        }
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: {
          rotate: rotateAngle,
          formatter: function(value) {
            // 如果已经是日期格式，直接返回
            if (value.includes('-')) {
              return value;
            }
            // 其他情况返回原值
            return value;
          }
        },
        show: true
      },
      yAxis: {
          type: 'value',
        name: '访问量',
        nameLocation: 'end',
        nameGap: 10, // 名称与轴线的距离
        nameTextStyle: {
          fontSize: 14,
          color: '#666',
          fontWeight: 'bold',
          padding: [0, 0, 0, 0] // 清除内边距
        },
        show: true,
        min: 0,
        max: yMax,
        interval: yInterval,
        axisLabel: {
          formatter: function(value) {
            return Math.round(value);
          },
          margin: 5 // 为轴标签添加外边距
        },
        axisLine: {
          show: true
        },
        axisTick: {
          show: true
        }
      },
      series: [
        {
          name: '访问量',
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#1890FF'
          },
          label: {
            show: showLabel,
            position: 'top',
            formatter: '{c}'
          },
          barWidth: barWidth
        }
      ],
      grid: {
        left: '8%',
        right: '5%',
        bottom: bottomMargin,
        top: '10%',
        containLabel: false
      }
    };
  
    if (boardChatAccessStatsChart) {
      boardChatAccessStatsChart.setOption(option, true);
    }
  }
  
  // 更新单板维护助手用户记录表格
  function updateBoardChatUserRecords() {
    // 如果API返回空数据，显示空的表格
    if (!boardChatUserRecordsData.value || boardChatUserRecordsData.value.length === 0) {
      boardChatUserRecords.value = [];
    } else {
      // 按照rank从小到大排序
      const sortedData = [...boardChatUserRecordsData.value].sort((a, b) => {
        return a.rank - b.rank;
      });
  
      boardChatUserRecords.value = sortedData.map((item) => ({
        rank: item.rank,                  //序号
        user_id: item.user_id,            //工号
        visit_count: item.visit_count,    //访问次数
        last_visit: item.last_visit,      //最后访问时间
      }));
    }
  }

  function generateDefaultBoardAccessData() {
    const defaultBoards = Array.from({ length: 10 }, (_, i) => `单板${i + 1}`); // 默认10个单板
    return defaultBoards.map(board => ({
      board_name: board,
      visit_count: 0
    }));
  }

  // 更新单板维护助手各单板智能助手访问次数表格
  function updateBoardChatBoardAccessChart() {
    if (!boardChatBoardStatsData.value || boardChatBoardStatsData.value.length === 0) {
      // 如果没有数据，显示空表格
      boardChatBoardAccessStats.value = generateDefaultBoardAccessData();
    }

    // 按访问次数降序排列
    const sortedData = [...boardChatBoardStatsData.value].sort((a, b) => b.visit_count - a.visit_count);
    const boardNames = sortedData.map(item => item.board_name); // 横坐标：单板名称
    const visitCounts = sortedData.map(item => item.visit_count); // 纵坐标：访问次数

    // 动态计算Y轴配置
    const maxValue = Math.max(...visitCounts);
    let yMax, yInterval;
    if (maxValue === 0) {
      yMax = 20;
      yInterval = 10;
    } else {
      yMax = Math.ceil(maxValue / 10) * 10;
      yInterval = Math.max(10, Math.ceil(yMax / 10));
    }

    // 柱状图配置
    const option = {
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => `${params[0].name}<br/>访问次数: ${params[0].value}`
      },
      xAxis: {
        type: 'category',
        data: boardNames,
        axisLabel: {
          rotate: 60,
          ellipsis: false,
          maxWidth: 120,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        name: '访问次数',
        nameLocation: 'end',
        nameTextStyle: { fontSize: 14, color: '#666', fontWeight: 'bold' },
        min: 0,
        max: yMax,
        interval: yInterval,
        axisLabel: { formatter: value => Math.round(value), margin: 5},
        axisLine: {
          show: true
        },
        axisTick: {
          show: true
        }
      },

      series: [{
        name: '访问次数',
        type: 'bar',
        data: visitCounts,
        itemStyle: { color: '#2FC25B' }, // 绿色柱状图（与卡片2蓝色区分）
        label: {
          show: visitCounts.length <= 15, // 数据量少时显示数值
          position: 'top',
          formatter: '{c}'
        },
        barWidth: visitCounts.length > 20 ? '30%' : '50%'
      }],
      grid: {
        left: '8%',
        right: '5%',
        bottom: '15%',
        top: '10%'
      }
    };

    if (boardChatBoardAccessChart) {
    boardChatBoardAccessChart.setOption(option, true);
    }
  }

  // 更新交互统计图表函数
  function updateConversationStatsChart() {
    const { 
      success_count, 
      failure_count, 
      total_success_rate, 
      total_failure_rate 
    } = conversationStats.value;
  
    const option = {
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c}% ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        data: ['成功', '失败']
      },
      series: [
        {
          name: '交互结果',
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '18',
              fontWeight: 'bold',
              formatter: '{b}: {c}%'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            {
              value: total_success_rate,
              name: '成功',
              itemStyle: {
                color: '#52c41a' // 成功-绿色
              }
            },
            {
              value: total_failure_rate,
              name: '失败',
              itemStyle: {
                color: '#ff4d4f' // 失败-红色
              }
            }
          ]
        }
      ]
    };

    if (conversationStatsChart) {
      conversationStatsChart.setOption(option, true);
    }
  }

  // 处理单板维护助手时间范围变化
  async function handleBoardChatTimeRangeChange(days) {
    const numDays = parseInt(days, 10);
    const range = boardChatTimeRanges.find((r) => parseInt(r.days, 10) === numDays);
  
    if (range) {
      boardChatSelectedRange.value = range;
  
      try {
        // 获取新数据
        const [accessStatsData, userRecordsData, boardStatsData] = await Promise.all([
          GetBoardChatAccessStatsData(),
          GetBoardChatUserRecords(),
          GetBoardChatBoardAccessStats(),
        ]);
  
        boardChatAccessStatsChartData.value = accessStatsData;
        boardChatUserRecordsData.value = userRecordsData;
        boardChatBoardStatsData.value = boardStatsData;

        updateBoardChatAccessStatsChart();
        updateBoardChatUserRecords();
        updateBoardChatBoardAccessChart();
      } catch (error) {
        // 如果获取失败，使用默认数据
        console.error('获取单板维护助手数据失败:', error);
        boardChatAccessStatsChartData.value = [];
        boardChatUserRecordsData.value = [];
        boardChatBoardStatsData.value = [];

        updateBoardChatAccessStatsChart();
        updateBoardChatUserRecords();
        updateBoardChatBoardAccessChart();
        MessagePlugin.error('数据加载失败，已显示默认数据');
      }
    }
  }
  
  // 单板维护助手数据更新
  const handleBoardChatUpdate = async () => {
    try {
      const [userStatsData, accessStatsData, userRecordsData, boardStatsData, conversationStatsData, feedbackData, monthlyBadFeedbackData] = await Promise.all([
        GetBoardChatUserStats(),
        GetBoardChatAccessStatsData(),
        GetBoardChatUserRecords(),
        GetBoardChatBoardAccessStats(),
        GetConversationStats(),
        GetFeedbackStats(),
        GetMonthlyBadFeedbackRate(),
      ]);

      boardChatUserStatsData.value = userStatsData || {};
      boardChatAccessStatsChartData.value = accessStatsData || [];
      boardChatUserRecordsData.value = userRecordsData || [];
      boardChatBoardStatsData.value = boardStatsData || [];
      conversationStats.value = conversationStatsData || {total_conversations: 0, total_success_count: 0, total_failure_count: 0, total_success_rate: 0, total_failure_rate: 0};
      feedbackStats.value = feedbackData || { total_feedbacks: 0, good_feedbacks: 0, bad_feedbacks: 0, good_rate: 0, bad_rate: 0};
      negativeTrendData.value = monthlyBadFeedbackData || [];
      // 数据更新后立即刷新图表和统计
      updateBoardChatUserStats();
      updateBoardChatAccessStatsChart();
      updateBoardChatUserRecords();
      updateBoardChatBoardAccessChart();
      updateConversationStatsChart();
      updateFeedbackStatsChart();
      if (negativeTrendChart) {
        negativeTrendChart.dispose();
        const negativeTrendChartDom = document.getElementById('negativeTrendChart');
        if (negativeTrendChartDom) {
          negativeTrendChart = echarts.init(negativeTrendChartDom);
        }
      }
      updateNegativeTrendChart();
    } catch (error) {
      console.error('单板维护助手数据更新失败:', error);
      boardChatUserStatsData.value = {};
      boardChatAccessStatsChartData.value = [];
      boardChatUserRecordsData.value = [];
      boardChatBoardStatsData.value = [];
      conversationStats.value = {total_conversations: 0, total_success_count: 0, total_failure_count: 0, total_success_rate: 0, total_failure_rate: 0};
      feedbackStats.value = {total_feedbacks: 0, good_feedbacks: 0, bad_feedbacks: 0, good_rate: 0, bad_rate: 0};
      negativeTrendData.value = [];
      // 更新失败后使用默认数据刷新图表
      updateBoardChatUserStats();
      updateBoardChatAccessStatsChart();
      updateBoardChatUserRecords();
      updateBoardChatBoardAccessChart();
      updateConversationStatsChart();
      updateFeedbackStatsChart();
      updateNegativeTrendChart();
      MessagePlugin.error('单板维护助手数据更新失败，已显示默认数据');
    }
  };

  // 初始化图表
  onMounted(async () => {
    // 初始化单板维护助手访问量统计图表
    const accessStatsChartDom = document.getElementById('boardChatAccessStatsChart');
    if (accessStatsChartDom) {
      boardChatAccessStatsChart = echarts.init(accessStatsChartDom);
      updateBoardChatAccessStatsChart();
    }

    const boardAccessChartDom = document.getElementById('boardChatBoardAccessChart');
    if (boardAccessChartDom) {
      boardChatBoardAccessChart = echarts.init(boardAccessChartDom);
      updateBoardChatBoardAccessChart();
    }

    const conversationStatsChartDom = document.getElementById('conversationStatsChart');
    if (conversationStatsChartDom) {
      conversationStatsChart = echarts.init(conversationStatsChartDom);
      updateConversationStatsChart();
    }

    const feedbackStatsChartDom = document.getElementById('feedbackStatsChart');
    if (feedbackStatsChartDom) {
      feedbackStatsChart = echarts.init(feedbackStatsChartDom);
      updateFeedbackStatsChart();
    }

    const negativeTrendChartDom = document.getElementById('negativeTrendChart');
    if (negativeTrendChartDom) {
      negativeTrendChart = echarts.init(negativeTrendChartDom);
      updateNegativeTrendChart();
    }

    // 添加 resize 事件监听器
    window.addEventListener('resize', () => {
      if (boardChatAccessStatsChart) boardChatAccessStatsChart.resize();
      if (boardChatBoardAccessChart) boardChatBoardAccessChart.resize();
      if (conversationStatsChart) conversationStatsChart.resize();
      if (feedbackStatsChart) feedbackStatsChart.resize();
      if (negativeTrendChart) negativeTrendChart.resize();
      setTimeout(() => {
      negativeTrendChart.setOption(negativeTrendChart.getOption());
      }, 100);
    });

    // 获取单板维护助手初始数据
    await handleBoardChatUpdate();
  });
  
  // 监听单板维护助手数据变化
  watch(
    [boardChatUserStatsData],
    () => {
      if (boardChatUserStatsData.value) {
        updateBoardChatUserStats();
      }
    },
    { deep: true }
  );
  
  watch(
    [boardChatAccessStatsChartData],
    () => {
      updateBoardChatAccessStatsChart();
    },
    { deep: true }
  );
  
  watch(
    [boardChatUserRecordsData],
    () => {
      if (boardChatUserRecordsData.value.length > 0) {
        updateBoardChatUserRecords();
      }
    },
    { deep: true }
  );
  
  watch(
    [boardChatBoardStatsData],
    () => {
      updateBoardChatBoardAccessChart();
    },
    { deep: true }
  );

  watch(
    [() => conversationStats.value],
    () => {
      updateConversationStatsChart();
    },
    { deep: true }
  );

  watch(
    [() => feedbackStats.value],
    () => {
      updateFeedbackStatsChart();
    },
    { deep: true }
  );

  watch(
    [() => negativeTrendData.value],
    () => {
      updateNegativeTrendChart();
    },
    { deep: true }
  );

  // 组件销毁前清理图表实例
  onBeforeUnmount(() => {
    // 清理单板维护助手图表实例
    if (boardChatAccessStatsChart) {
      boardChatAccessStatsChart.dispose();
      boardChatAccessStatsChart = null;
    }
    if (conversationStatsChart) {
      conversationStatsChart.dispose();
      conversationStatsChart = null;
    }
    if (feedbackStatsChart) {
      feedbackStatsChart.dispose();
      feedbackStatsChart = null;
    }
    if (negativeTrendChart) {
      negativeTrendChart.dispose();
      negativeTrendChart = null;
    }
  });
  </script>
  
  <style scoped>
  .kanban-main {
    /* 调整整体布局 */
    .t-space--vertical {
      width: 100%;
    }
    
    .t-space--horizontal {
      width: 100%;
      justify-content: space-between;
    }
  
    .kanban-card {
      flex: 1;
      min-width: 800px; /* 设置最小宽度 */
    }
  
    :deep(.t-card) {
      display: flex;
      padding: 10px;
      flex-direction: column;
      height: 600px; /* 固定高度 */
      overflow: hidden; /* 防止内部溢出 */
    }
  
    :deep(.t-card__title) {
      font-size: 20px;
      font-weight: 400;
      flex-shrink: 0;
    }
  
    :deep(.t-card__actions) {
      flex-shrink: 0;
    }
  
    :deep(.t-card__body) {
      flex: 1;
      padding: 20px;
      display: flex;
      flex-direction: column;
      overflow: hidden; /* 关键：限制内容溢出 */
    }
  
    /* 表头样式：背景透明 + 字体加粗 */
    :deep(.t-table th) {
      background-color: transparent !important;
      font-weight: bold !important;
      color: inherit;
    }
  
    /* 可选：去除表头 hover 效果（如果不需要） */
    :deep(.t-table th:hover) {
      background-color: transparent !important;
    }

    .combined-stats-container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    /* 单板维护助手统计样式 */
    .board-chat-user-stats {
      padding: 20px 0;
      display: flex;
      justify-content: center;
      align-items: center;
      flex-shrink: 0;
    }
    
    .board-chat-stat-item {
      text-align: center;
      padding: 0 40px;
      border-right: 1px solid #f0f0f0;
      min-width: 150px;
    }
    
    .board-chat-stat-item:last-child {
      border-right: none;
    }
    
    .board-chat-stat-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 12px;
    }
  
    .board-chat-stat-value {
      font-size: 36px;
      font-weight: bold;
      color: #1890ff;
      margin-bottom: 8px;
    }
    
    .board-chat-stat-trend {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      gap: 4px;
    }
    
    .trend-up {
      color: #52c41a;
    }
    
    .trend-down {
      color: #ff4d4f;
    }
  
    @media (max-width: 1200px) {
      .kanban-card {
        min-width: 650px;
      }
  
      .t-space--horizontal {
        flex-wrap: wrap; /* 在小屏幕上换行 */
        justify-content: center;
      }
    }

    .back-button-circle {
      position: absolute; /* 或 absolute，视你的布局而定 */
      z-index: 4000; /* 确保浮在最上层 */
      top: 70px; /* 距离页面顶部的距离为0 */
      left: 250px; /* 距离页面左边的距离为0 */
      margin-left: 0px;
      box-shadow:
        0px 4px 12px rgba(0, 0, 0, 0.15),
        0px 16px 32px rgba(0, 0, 0, 0.2),
        0px 32px 48px rgba(0, 0, 0, 0.15);
    }

    .stats-divider {
      height: 1px;
      background-color: #f0f0f0;
      margin: 20px 0;
      flex-shrink: 0;
    }

    /* 对话统计样式 */
    .conversation-stats-section {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
    }

    .conversation-stats-layout {
      display: flex;
      align-items: center;
     justify-content: space-between;
      height: 100%;
      gap: 20px;
    }

    .conversation-stats-vertical {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-start;
      flex: 1;
      gap: 25px;
      padding-left: 40px;
    }

    .conversation-stat-vertical-item {
      text-align: left;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
    }

    .conversation-chart-container {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;
    }

    .conversation-stat-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
    }

    .conversation-stat-label.success-rate {
      color: #52c41a;
    }

    .conversation-stat-label.failure-rate {
      color: #ff4d4f;
    }

    .conversation-stat-value {
      font-size: 20px;
      font-weight: bold;
      color: #1890ff;
      line-height: 1.4;
    }

    .conversation-stat-value.success {
      color: #52c41a;
    }

    .conversation-stat-value.failure {
      color: #ff4d4f;
    }

    #conversationStatsChart {
      flex: 1;
      min-height: 0; /* 允许图表容器收缩 */
    }

    /* 用户满意度样式 */
    .feedback-stats-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      gap: 0;
      overflow: hidden;
    }

    /* 上部：满意度统计 - 占1/3高度 */
    .satisfaction-stats-section {
      flex: 0 0 auto;
      display: flex;
      flex-direction: column;
      justify-content: center;
      height: 35%;
      min-height: 200px;
      padding: 10px 0;
      box-sizing: border-box; 
    }

    .satisfaction-stats-layout {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 100%;
      gap: 20px;
      padding: 0 10px;
    }

    /* 垂直布局的统计数字 */
    .satisfaction-stats-vertical {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-start;
      flex: 1;
      gap: 5px; /* 减少间距 */
      padding-left: 20px; /* 减少左边距 */
      height: 100%;
      overflow: visible; /* 确保内容可见 */
    }

    .satisfaction-stat-vertical-item {
      text-align: left;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-bottom: 5px; /* 添加底部间距 */
    }

    .satisfaction-stat-item {
      text-align: left;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-bottom: 15px; /* 主要标题的间距 */
    }

    /* 右侧饼图 - 占一半宽度 */
    .satisfaction-chart-container {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;
      padding: 5px; /* 减少内边距 */
      min-height: 0; /* 允许收缩 */
    }

    /* 分隔线 */
    .section-divider {
      height: 1px;
      background-color:#e8e8e8;;
      margin: 3px 0;
      width: 100%;
      border: none;
      flex-shrink: 0; /* 防止被压缩 */
      z-index: 1; /* 确保在最上层 */
      position: relative;
    }

    /* 下部：月度差评率趋势 - 占2/3高度 */
    .negative-trend-section {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 60%;
      min-height: 300px;
      padding: 0; /* 添加上下内边距 */
      box-sizing: border-box;
      overflow: hidden; /* 防止内容溢出 */
    }

    #feedbackStatsChart {
      width: 100%;
      height: 100%;
      min-height: 0;
    }

    #negativeTrendChart {
      width: 100%;
      min-height: 0;
    }


    .satisfaction-stat-label {
      font-size: 13px;
      color: #666;
      margin-bottom: 6px;
    }

    .satisfaction-stat-label.good-rate {
      color: #52c41a;
    }

    .satisfaction-stat-label.bad-rate {
      color: #ff4d4f;
    }

    .satisfaction-stat-value {
      font-size: 18px;
      font-weight: bold;
      color: #1890ff;
      line-height: 1.3;
    }

    .satisfaction-stat-value.good {
      color: #52c41a;
    }

    .satisfaction-stat-value.bad {
      color: #ff4d4f;
    }

    /* 响应式调整 */
    @media (max-width: 1400px) {
      .feedback-stat-item {
        min-width: 180px;
      }
      
      .feedback-stat-row:first-child .feedback-stat-item:first-child {
        margin-right: 40px;
      }
    }

    @media (max-width: 1200px) {
      .feedback-stat-item {
        min-width: 160px;
      }
      
      .feedback-stat-row:first-child .feedback-stat-item:first-child {
        margin-right: 30px;
      }
    }

    /* 下载按钮loading状态样式 */
    :deep(.t-button--variant-outline) .t-loading {
      color: var(--td-brand-color);
    }

    /* 确保操作按钮区域布局合理 */
    :deep(.t-card__actions .t-space) {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* 工具提示样式优化 */
    .t-tooltip {
      z-index: 1000;
    }

    /* 卡片操作区域容器 */
    :deep(.card-actions-container) {
      position: relative;
      min-height: 60px; /* 为提示消息预留空间 */
    }

    /* 下载按钮样式 */
    .download-btn {
      position: relative;
    }

    /* 下载提示消息样式 */
    .download-message {
      position: absolute;
      top: 45px; /* 在按钮下方显示 */
      left: 50%;
      transform: translateX(-50%);
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
      z-index: 10;
      animation: slideDown 0.3s ease-out;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      pointer-events: none; /* 防止阻挡点击 */
    }

    /* 成功提示样式 */
    .download-message.success {
      background-color: #f6ffed;
      border: 1px solid #b7eb8f;
      color: #52c41a;
    }

    /* 错误提示样式 */
    .download-message.error {
      background-color: #fff2f0;
      border: 1px solid #ffccc7;
      color: #ff4d4f;
    }

    /* 动画效果 */
    @keyframes slideDown {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }

    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    /* 防止提示被卡片内容遮挡 */
    :deep(.t-card__header) {
      position: relative;
      z-index: 2;
    }

    /* 确保操作区域有足够的空间 */
    :deep(.t-card__actions) {
      min-height: 80px;
      position: relative;
    }

    /* 响应式调整 */
    @media (max-width: 1400px) {
      .download-message {
        font-size: 11px;
        padding: 5px 10px;
        top: 42px;
      }
    }

    @media (max-width: 1200px) {
      .download-message {
        font-size: 10px;
        padding: 4px 8px;
        top: 40px;
      }
    }

    /* 卡片1的操作区域容器 */
    :deep(.kanban-card:nth-child(1) .card-actions-container) {
      position: relative;
      min-height: 60px; /* 为提示消息预留空间 */
    }

    /* 卡片1的下载按钮样式 */
    :deep(.kanban-card:nth-child(1) .download-btn) {
      position: relative;
      margin-right: 8px;
    }

    /* 卡片1的下载提示消息样式 */
    :deep(.kanban-card:nth-child(1) .download-message) {
      position: absolute;
      top: 45px; /* 在按钮下方显示 */
      left: 50%;
      transform: translateX(-50%);
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
      z-index: 10;
      animation: slideDown 0.3s ease-out;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      pointer-events: none; /* 防止阻挡点击 */
    }

    /* 卡片1的成功提示样式 */
    :deep(.kanban-card:nth-child(1) .download-message.success) {
      background-color: #f6ffed;
      border: 1px solid #b7eb8f;
      color: #52c41a;
    }

    /* 卡片1的错误提示样式 */
    :deep(.kanban-card:nth-child(1) .download-message.error) {
      background-color: #fff2f0;
      border: 1px solid #ffccc7;
      color: #ff4d4f;
    }

    /* 确保卡片1的操作区域有足够的空间 */
    :deep(.kanban-card:nth-child(1) .t-card__actions) {
      min-height: 80px;
      position: relative;
    }

    /* 确保操作按钮区域布局合理 */
    :deep(.kanban-card:nth-child(1) .t-card__actions .t-space) {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  </style>
  