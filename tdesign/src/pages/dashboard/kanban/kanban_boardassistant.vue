<template>
  <div class="kanban-main">
    <t-space direction="vertical">
      <t-space>
        <!-- 卡片1：AI智能体访问量图表 -->
        <t-card :title="card1Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button shape="circle" variant="outline" @click="handleUpdate">
                <icon name="refresh" />
              </t-button>
              <t-radio-group variant="default-filled" :value="selectedRange.days" @change="handleTimeRangeChange">
                <t-radio-button value="7">最近7天</t-radio-button>
                <t-radio-button value="30">最近30天</t-radio-button>
                <t-radio-button value="90">最近90天</t-radio-button>
              </t-radio-group>
              <t-select
                v-model="selectedAgent"
                placeholder="选择智能体类型"
                :options="agentOptions"
                clearable
                autoWidth
                @change="handleAgentChange"
              />
            </t-space>
          </template>
          <div id="aiAccessChart" style="width: 100%; height: 500px"></div>
        </t-card>

        <!-- 卡片2：AI智能体近期访客 -->
        <t-card :title="card2Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-tag theme="primary" size="large" variant="light-outline">周活跃: {{ weeklyActiveCount }}人</t-tag>
            </t-space>
          </template>
          <t-table :data="aiVisitorStats" :columns="visitorColumns" :hover="true" :max-height="480" rowKey="user" />
        </t-card>
      </t-space>
      <t-space>
        <!-- 卡片3：网站访问量图表 -->
        <t-card :title="card3Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button shape="circle" variant="outline" @click="handleUpdate">
                <icon name="refresh" />
              </t-button>
              <t-radio-group variant="default-filled" :value="selectedRange.days" @change="handleTimeRangeChange">
                <t-radio-button value="7">最近7天</t-radio-button>
                <t-radio-button value="30">最近30天</t-radio-button>
                <t-radio-button value="90">最近90天</t-radio-button>
              </t-radio-group>
              <t-select
                v-model="selectedPage"
                placeholder="选择页面类型"
                :options="pageOptions"
                clearable
                autoWidth
                @change="handlePageChange"
              />
            </t-space>
          </template>
          <div id="websiteAccessChart" style="width: 100%; height: 500px"></div>
        </t-card>

        <!-- 卡片4：网站近期访客 -->
        <t-card :title="card4Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-tag theme="primary" size="large" variant="light-outline"
                >周活跃: {{ weeklyWebsiteActiveCount }}人</t-tag
              >
            </t-space>
          </template>
          <t-table
            :data="websiteVisitorStats"
            :columns="websiteVisitorColumns"
            :hover="true"
            :max-height="480"
            rowKey="user"
          />
        </t-card>
      </t-space>

      <t-space>
        <!-- 卡片5：单板助手用户规模统计卡片 -->
        <t-card :title="card5Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
              <icon name="refresh" />
            </t-button>
          </template>
          <div class="board-chat-user-stats">
            <t-space size="large">
              <div class="board-chat-stat-item">
                <div class="board-chat-stat-label">累计用户数</div>
                <div class="board-chat-stat-value">{{ boardChatUserStats.totalUsers }}</div>
              </div>
              <div class="board-chat-stat-item">
                <div class="board-chat-stat-label">本周用户数</div>
                <div class="board-chat-stat-value">{{ boardChatUserStats.weeklyUsers }}</div>
                <div class="board-chat-stat-trend" :class="boardChatUserStats.weeklyTrend >= 0 ? 'trend-up' : 'trend-down'">
                  <icon :name="boardChatUserStats.weeklyTrend >= 0 ? 'caret-up' : 'caret-down'" />
                  {{ Math.abs(boardChatUserStats.weeklyTrend) }}%
                </div>
              </div>
              <div class="board-chat-stat-item">
                <div class="board-chat-stat-label">上周用户数</div>
                <div class="board-chat-stat-value">{{ boardChatUserStats.lastWeekUsers }}</div>
              </div>
            </t-space>
          </div>
        </t-card>

        <!-- 卡片6：单板助手访问量统计卡片 -->
        <t-card :title="card6Title" class="kanban-card" hover-shadow>
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
        <!-- 卡片7：单板维护助手用户访问记录表格 -->
        <t-card :title="card7Title" class="kanban-card" hover-shadow>
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

        <!-- 卡片8：单板维护助手用户满意度表格 -->
        <t-card :title="card8Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button shape="circle" variant="outline" @click="handleBoardChatUpdate">
                <icon name="refresh" />
              </t-button>
            </t-space>
          </template>
          <t-table 
            :data="boardChatUserSatisfaction" 
            :hover="true" 
            :max-height="480"
            rowKey="recordId"
            class="board-chat-records-table"
          />
        </t-card>
      </t-space>
    </t-space>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { Icon } from 'tdesign-icons-vue-next';
import { getBoardChatUserStats, getBoardChatAccessStatsData, getBoardChatUserRecords, } from '@/api/boardChat.js';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

// 图表标题
const card1Title = 'AI智能体调用量';
const card2Title = 'AI智能体近期访客';
const card3Title = '网站访问量';
const card4Title = '网站近期访客';
const card5Title = '单板维护助手用户规模';
const card6Title = '单板维护助手访问量统计';
const card7Title = '单板维护助手用户访问记录';
const card8Title = '单板维护助手用户满意度';
// 时间范围选项
const timeRanges = [
  { label: '最近7天', days: '7' },
  { label: '最近30天', days: '30' },
  { label: '最近90天', days: '90' },
];
const selectedRange = ref(timeRanges[1]);

// 智能体类型选项
const agentOptions = [
  { label: '问答智能体', value: 'chat' },
  { label: '组件智能体', value: 'component' },
  { label: '详设智能体', value: 'TlCheckAgent' },
];
const selectedAgent = ref(null); // 默认不筛选

// 页面选项
const pageOptions = [
  { label: '场景树', value: '场景树' },
  { label: '特性树', value: '特性树' },
  { label: '组件树', value: '组件树' },
  { label: '单板树', value: '单板树' },
  { label: '硬件树', value: '硬件树' },
  { label: '需求库', value: '需求库' },
  { label: '故障库', value: '故障库' },
  { label: '代码库', value: '代码库' },
  { label: '命令库', value: '命令库' },
  { label: 'AI助手', value: 'AI助手' },
  { label: '单板助手', value: '单板助手' },
  { label: '智能诊断助手', value: '智能诊断助手' },
  { label: '故障处理助手', value: '故障处理助手' },
  { label: '代码生成助手', value: '代码生成助手' },
  { label: '故障波及助手', value: '故障波及助手' },
  { label: '单板组装助手', value: '单板组装助手' },
];
const selectedPage = ref(null); // 默认不筛选

// 图表相关
let aiAccessChart = null;
let websiteAccessChart = null;

// AI访问量图表数据
const aiAccessChartData = ref([]);
// 网站访问量图表数据
const websiteAccessChartData = ref([]);
// AI访客统计数据
const aiVisitorStatsData = ref([]);
// 网站访客统计数据
const websiteVisitorStatsData = ref([]);

// 周活跃人数统计
const weeklyActiveCount = ref(0);
// 网站周活跃人数统计
const weeklyWebsiteActiveCount = ref(0);

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

const boardChatUserSatisfaction = ref([]);

// 单板维护助手用户记录表格列定义
const boardChatRecordColumns = [
  { colKey: 'rank', title: '序号', width: 40 },
  { colKey: 'user_id', title: '用户ID', width: 60 },
  { colKey: 'visit_count', title: '访问次数', width: 40 },
  { colKey: 'last_visit', title: '最近访问时间', width: 60 },
];

// 访问量统计图表实例
let boardChatAccessStatsChart = null;

// 单板维护助手数据存储
const boardChatUserStatsData = ref({});
const boardChatAccessStatsChartData = ref([]);
const boardChatUserRecordsData = ref([]);

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

// 处理单板维护助手时间范围变化
async function handleBoardChatTimeRangeChange(days) {
  const numDays = parseInt(days, 10);
  const range = boardChatTimeRanges.find((r) => parseInt(r.days, 10) === numDays);

  if (range) {
    boardChatSelectedRange.value = range;

    try {
      // 获取新数据
      const [accessStatsData, userRecordsData] = await Promise.all([
        GetBoardChatAccessStatsData(),
        GetBoardChatUserRecords(),
      ]);

      boardChatAccessStatsChartData.value = accessStatsData;
      boardChatUserRecordsData.value = userRecordsData;

      updateBoardChatAccessStatsChart();
      updateBoardChatUserRecords();
    } catch (error) {
      // 如果获取失败，使用默认数据
      console.error('获取单板维护助手数据失败:', error);
      boardChatAccessStatsChartData.value = [];
      boardChatUserRecordsData.value = [];

      updateBoardChatAccessStatsChart();
      updateBoardChatUserRecords();
      MessagePlugin.error('数据加载失败，已显示默认数据');
    }
  }
}

// 单板维护助手数据更新
const handleBoardChatUpdate = async () => {
  try {
    const [userStatsData, accessStatsData, userRecordsData] = await Promise.all([
      GetBoardChatUserStats(),
      GetBoardChatAccessStatsData(),
      GetBoardChatUserRecords()
    ]);

    boardChatUserStatsData.value = userStatsData || {};
    boardChatAccessStatsChartData.value = accessStatsData || [];
    boardChatUserRecordsData.value = userRecordsData || [];

    // 数据更新后立即刷新图表和统计
    updateBoardChatUserStats();
    updateBoardChatAccessStatsChart();
    updateBoardChatUserRecords();
  } catch (error) {
    console.error('单板维护助手数据更新失败:', error);
    boardChatUserStatsData.value = {};
    boardChatAccessStatsChartData.value = [];
    boardChatUserRecordsData.value = [];

    // 更新失败后使用默认数据刷新图表
    updateBoardChatUserStats();
    updateBoardChatAccessStatsChart();
    updateBoardChatUserRecords();

    MessagePlugin.error('单板维护助手数据更新失败，已显示默认数据');
  }
};

// 获取AI访问量数据 (PV/UV)
const getAiAccessData = async () => {
  try {
    const params = {
      period: parseInt(selectedRange.value.days),
    };

    // 添加agent筛选参数
    if (selectedAgent.value) {
      params.agent = selectedAgent.value;
    }

    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_ai_pvuv_get`, params);
    if (res.data.status === 'success') {
      return res.data.data;
    }
    return [];
  } catch (err) {
    console.error('AI访问量数据请求失败:', err);
    return [];
  }
};

// 获取网站访问量数据 (PV/UV)
const getWebsiteAccessData = async () => {
  try {
    const params = {
      period: parseInt(selectedRange.value.days),
    };

    // 添加page筛选参数
    if (selectedPage.value) {
      params.page = selectedPage.value;
    }

    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_visit_pvuv_get`, params);
    if (res.data.status === 'success') {
      return res.data.data;
    }
    return [];
  } catch (err) {
    console.error('网站访问量数据请求失败:', err);
    return [];
  }
};

// 获取AI访客统计数据
const getAiVisitorStats = async () => {
  try {
    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_history_ai_get`, {
      period: parseInt(selectedRange.value.days),
    });
    if (res.data.status === 'success') {
      return res.data.data;
    }
    return [];
  } catch (err) {
    console.error('AI访客统计数据请求失败:', err);
    return [];
  }
};

// 获取网站访客统计数据
const getWebsiteVisitorStats = async () => {
  try {
    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_history_visit_get`, {
      period: parseInt(selectedRange.value.days),
    });
    if (res.data.status === 'success') {
      return res.data.data;
    }
    return [];
  } catch (err) {
    console.error('网站访客统计数据请求失败:', err);
    return [];
  }
};

// 获取聊天记录 (已废弃，但保留函数以避免其他地方调用报错)
const HistoryGet = async () => {
  console.warn('HistoryGet function is deprecated, using new API functions instead');
};

// 获取网站访问记录 (已废弃，但保留函数以避免其他地方调用报错)
const WebsiteVisitGet = async () => {
  console.warn('WebsiteVisitGet function is deprecated, using new API functions instead');
};

// 按日期聚合AI访问量 (直接使用后端返回的数据)
const groupedAiDataByDate = computed(() => {
  return aiAccessChartData.value.map((item) => ({
    date: item.date,
    count: item.pv, // 使用PV作为访问量
  }));
});

// 按日期聚合网站访问量 (直接使用后端返回的数据)
const groupedWebsiteDataByDate = computed(() => {
  return websiteAccessChartData.value.map((item) => ({
    date: item.date,
    count: item.uv, // 使用UV作为访问人数
  }));
});

// 更新AI访问图表 (PV用柱状图，UV用折线图，使用单个Y轴)
function updateAiChartData() {
  const labels = aiAccessChartData.value.map((item) => item.date);
  const pvValues = aiAccessChartData.value.map((item) => item.pv);
  const uvValues = aiAccessChartData.value.map((item) => item.uv);

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let tooltipText = params[0].axisValue;
        params.forEach((param) => {
          if (param.seriesName === '访问量(PV)') {
            tooltipText += `<br/>${param.marker} ${param.seriesName}: ${param.value}`;
          } else if (param.seriesName === '访问人数(UV)') {
            tooltipText += `<br/>${param.marker} ${param.seriesName}: ${param.value}`;
          }
        });
        return tooltipText;
      },
    },
    legend: {
      data: ['访问量(PV)', '访问人数(UV)'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '访问量(PV)',
        type: 'bar',
        data: pvValues,
        itemStyle: { color: '#1890FF' },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
      },
      {
        name: '访问人数(UV)',
        type: 'line',
        data: uvValues,
        itemStyle: { color: '#52c41a' },
        smooth: true,
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '0%',
      top: '10%',
      containLabel: true,
    },
  };

  if (aiAccessChart) {
    aiAccessChart.setOption(option, true);
  }
}

// 更新网站访问图表 (PV用柱状图，UV用折线图，使用单个Y轴)
function updateWebsiteChartData() {
  const labels = websiteAccessChartData.value.map((item) => item.date);
  const pvValues = websiteAccessChartData.value.map((item) => item.pv);
  const uvValues = websiteAccessChartData.value.map((item) => item.uv);

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let tooltipText = params[0].axisValue;
        params.forEach((param) => {
          if (param.seriesName === '访问量(PV)') {
            tooltipText += `<br/>${param.marker} ${param.seriesName}: ${param.value}`;
          } else if (param.seriesName === '访问人数(UV)') {
            tooltipText += `<br/>${param.marker} ${param.seriesName}: ${param.value}`;
          }
        });
        return tooltipText;
      },
    },
    legend: {
      data: ['访问量(PV)', '访问人数(UV)'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '访问量(PV)',
        type: 'bar',
        data: pvValues,
        itemStyle: { color: '#1890FF' },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
      },
      {
        name: '访问人数(UV)',
        type: 'line',
        data: uvValues,
        itemStyle: { color: '#52c41a' },
        smooth: true,
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '0%',
      top: '10%',
      containLabel: true,
    },
  };

  if (websiteAccessChart) {
    websiteAccessChart.setOption(option, true);
  }
}

// AI访客统计
const aiVisitorStats = ref([]);
// 网站访客统计
const websiteVisitorStats = ref([]);

const visitorColumns = [
  { colKey: 'index', title: '序号', width: 80 },
  { colKey: 'user', title: '用户ID', width: 120 },
  { colKey: 'count', title: '访问次数', width: 80 },
  { colKey: 'lastVisit', title: '最近访问时间', width: 120 },
  {
    colKey: 'activity',
    title: '周活跃度',
    width: 80,
    cell: (h, { row }) => {
      return row.isActive ? <t-tag theme="success">活跃</t-tag> : <t-tag theme="warning">非活跃</t-tag>;
    },
  },
];

const websiteVisitorColumns = [
  { colKey: 'index', title: '序号', width: 80 },
  { colKey: 'user', title: '用户ID', width: 120 },
  { colKey: 'count', title: '访问次数', width: 80 },
  { colKey: 'lastVisit', title: '最近访问时间', width: 120 },
  {
    colKey: 'activity',
    title: '周活跃度',
    width: 80,
    cell: (h, { row }) => {
      return row.isActive ? <t-tag theme="success">活跃</t-tag> : <t-tag theme="warning">非活跃</t-tag>;
    },
  },
];

// 更新AI访客统计 (直接使用后端返回的数据)
function updateAiVisitorStats() {
  // 直接使用从后端获取的处理好的数据
  aiVisitorStats.value = aiVisitorStatsData.value.map((item) => ({
    index: item.index,
    user: item.user_id,
    count: item.visit_count,
    lastVisit: item.last_visit_time,
    isActive: item.weekly_activity === '活跃',
  }));

  // 计算并更新周活跃人数
  updateWeeklyActiveCount();
}

// 更新网站访客统计 (直接使用后端返回的数据)
function updateWebsiteVisitorStats() {
  // 直接使用从后端获取的处理好的数据
  websiteVisitorStats.value = websiteVisitorStatsData.value.map((item) => ({
    index: item.index,
    user: item.user_id,
    count: item.visit_count,
    lastVisit: item.last_visit_time,
    isActive: item.weekly_activity === '活跃',
  }));

  // 计算并更新网站周活跃人数
  updateWebsiteWeeklyActiveCount();
}

// 计算并更新周活跃人数
function updateWeeklyActiveCount() {
  if (aiVisitorStats.value && aiVisitorStats.value.length > 0) {
    const activeCount = aiVisitorStats.value.filter((item) => item.isActive).length;
    weeklyActiveCount.value = activeCount;
  } else {
    weeklyActiveCount.value = 0;
  }
}

// 计算并更新网站周活跃人数
function updateWebsiteWeeklyActiveCount() {
  if (websiteVisitorStats.value && websiteVisitorStats.value.length > 0) {
    const activeCount = websiteVisitorStats.value.filter((item) => item.isActive).length;
    weeklyWebsiteActiveCount.value = activeCount;
  } else {
    weeklyWebsiteActiveCount.value = 0;
  }
}

// 初始化图表
onMounted(async () => {
  const aiChartDom = document.getElementById('aiAccessChart');
  aiAccessChart = echarts.init(aiChartDom);

  const websiteChartDom = document.getElementById('websiteAccessChart');
  websiteAccessChart = echarts.init(websiteChartDom);

  // 初始化单板维护助手访问量统计图表
  const accessStatsChartDom = document.getElementById('boardChatAccessStatsChart');
  if (accessStatsChartDom) {
    boardChatAccessStatsChart = echarts.init(accessStatsChartDom);
    updateBoardChatAccessStatsChart();
  }

  // 添加 resize 事件监听器
  window.addEventListener('resize', () => {
    if (aiAccessChart) aiAccessChart.resize();
    if (websiteAccessChart) websiteAccessChart.resize();
    if (boardChatAccessStatsChart) boardChatAccessStatsChart.resize();
  });

  // 获取初始数据
  await handleUpdate();
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

// 监听数据变化
watch(
  [aiAccessChartData, selectedRange],
  () => {
    if (aiAccessChartData.value.length > 0) {
      updateAiChartData();
    }
  },
  { deep: true },
);

watch(
  [websiteAccessChartData, selectedRange],
  () => {
    if (websiteAccessChartData.value.length > 0) {
      updateWebsiteChartData();
    }
  },
  { deep: true },
);

watch(
  [aiVisitorStatsData, selectedRange],
  () => {
    if (aiVisitorStatsData.value.length > 0) {
      updateAiVisitorStats();
    }
  },
  { deep: true },
);

watch(
  [websiteVisitorStatsData, selectedRange],
  () => {
    if (websiteVisitorStatsData.value.length > 0) {
      updateWebsiteVisitorStats();
    }
  },
  { deep: true },
);

// 处理智能体类型变化
async function handleAgentChange(value) {
  selectedAgent.value = value;

  // 仅更新AI访问量数据，其他数据保持不变
  const aiAccessData = await getAiAccessData();
  aiAccessChartData.value = aiAccessData;
  updateAiChartData();
}

// 处理页面变化
async function handlePageChange(value) {
  selectedPage.value = value;

  // 仅更新网站访问量数据，其他数据保持不变
  const websiteAccessData = await getWebsiteAccessData();
  websiteAccessChartData.value = websiteAccessData;
  updateWebsiteChartData();
}

// 切换时间范围
async function handleTimeRangeChange(days) {
  const numDays = parseInt(days, 10);
  const range = timeRanges.find((r) => parseInt(r.days, 10) === numDays);

  if (range) {
    selectedRange.value = range;

    // 获取新数据
    const [aiAccessData, websiteAccessData, aiVisitorData, websiteVisitorData] = await Promise.all([
      getAiAccessData(),
      getWebsiteAccessData(),
      getAiVisitorStats(),
      getWebsiteVisitorStats(),
    ]);

    // 更新数据
    aiAccessChartData.value = aiAccessData;
    websiteAccessChartData.value = websiteAccessData;
    aiVisitorStatsData.value = aiVisitorData;
    websiteVisitorStatsData.value = websiteVisitorData;

    // 更新视图
    updateAiChartData();
    updateAiVisitorStats();
    updateWebsiteChartData();
    updateWebsiteVisitorStats();
  }
}

// 更新所有数据
const handleUpdate = async () => {
  try {
    // 显示加载提示
    MessagePlugin.loading('数据更新中...');

    // 并行获取所有数据
    const [aiAccessData, websiteAccessData, aiVisitorData, websiteVisitorData, BoardUserStatsData, BoardAccessStatsData, BoardUserSessionsData] = await Promise.all([
      getAiAccessData(),
      getWebsiteAccessData(),
      getAiVisitorStats(),
      getWebsiteVisitorStats(),
    ]);

    // 更新数据
    aiAccessChartData.value = aiAccessData;
    websiteAccessChartData.value = websiteAccessData;
    aiVisitorStatsData.value = aiVisitorData;
    websiteVisitorStatsData.value = websiteVisitorData;

    // 隐藏加载提示
    MessagePlugin.success('数据更新成功');
  } catch (error) {
    console.error('数据更新失败:', error);
    MessagePlugin.error('数据更新失败');
  }
};

// 组件销毁前清理图表实例
onBeforeUnmount(() => {
  if (aiAccessChart) {
    aiAccessChart.dispose();
    aiAccessChart = null;
  }
  if (websiteAccessChart) {
    websiteAccessChart.dispose();
    websiteAccessChart = null;
  }
  // 清理单板维护助手图表实例
  if (boardChatAccessStatsChart) {
    boardChatAccessStatsChart.dispose();
    boardChatAccessStatsChart = null;
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

  /* 单板维护助手统计样式 */
  .board-chat-user-stats {
    padding: 20px 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
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
}
</style>
