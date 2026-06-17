<template>
  <div class="kanban-main">
    <t-space direction="vertical">
      <t-space>
        <!-- 卡片1：AI智能体访问量图表 -->
        <t-card :title="card1Title" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button v-if="!aiLoading" shape="circle" variant="outline" @click="handleUpdateAI">
                <icon name="refresh" />
              </t-button>
              <t-button
                v-else
                shape="circle"
                variant="outline"
                :loading="true"
                :loading-props="{ text: '' }"
                @click="handleUpdateAI"
              >
              </t-button>
              <t-radio-group variant="default-filled" :value="selectedRangeAI.days" @change="handleTimeRangeChangeAI">
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
              <t-button v-if="!websiteLoading" shape="circle" variant="outline" @click="handleUpdateWebsite">
                <icon name="refresh" />
              </t-button>
              <t-button
                v-else
                shape="circle"
                variant="outline"
                :loading="true"
                :loading-props="{ text: '' }"
                @click="handleUpdateWebsite"
              >
              </t-button>
              <t-radio-group
                variant="default-filled"
                :value="selectedRangeWebsite.days"
                @change="handleTimeRangeChangeWebsite"
              >
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
    </t-space>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { Icon } from 'tdesign-icons-vue-next';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

// 图表标题
const card1Title = 'AI智能体调用量';
const card2Title = 'AI智能体近期访客';
const card3Title = '网站访问量';
const card4Title = '网站近期访客';

// 时间范围选项
const timeRanges = [
  { label: '最近7天', days: '7' },
  { label: '最近30天', days: '30' },
  { label: '最近90天', days: '90' },
];
const selectedRangeAI = ref(timeRanges[1]); // AI section time range
const selectedRangeWebsite = ref(timeRanges[1]); // Website section time range

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
// 加载状态
const aiLoading = ref(false);
const websiteLoading = ref(false);

// 获取AI访问量数据 (PV/UV)
const getAiAccessData = async () => {
  try {
    const params = {
      period: parseInt(selectedRangeAI.value.days),
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
      period: parseInt(selectedRangeWebsite.value.days),
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
    const params = {
      period: parseInt(selectedRangeAI.value.days),
    };

    // 添加agent筛选参数
    if (selectedAgent.value) {
      params.agent = selectedAgent.value;
    }

    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_history_ai_get`, params);
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
    const params = {
      period: parseInt(selectedRangeWebsite.value.days),
    };

    // 添加page筛选参数
    if (selectedPage.value) {
      params.page = selectedPage.value;
    }

    const res = await axios.post(`${SERVER_API_URL}/api_chat/API_Chat_history_visit_get`, params);
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
  { colKey: 'user', title: '用户', width: 120 },
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
  { colKey: 'user', title: '用户', width: 120 },
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

  // 添加 resize 事件监听器
  window.addEventListener('resize', () => {
    if (aiAccessChart) aiAccessChart.resize();
    if (websiteAccessChart) websiteAccessChart.resize();
  });

  // 获取初始数据
  await handleUpdate();
});

// 监听数据变化
watch(
  [aiAccessChartData, selectedRangeAI],
  () => {
    if (aiAccessChartData.value.length > 0) {
      updateAiChartData();
    }
  },
  { deep: true },
);

watch(
  [websiteAccessChartData, selectedRangeWebsite],
  () => {
    if (websiteAccessChartData.value.length > 0) {
      updateWebsiteChartData();
    }
  },
  { deep: true },
);

watch(
  [aiVisitorStatsData, selectedRangeAI],
  () => {
    if (aiVisitorStatsData.value.length > 0) {
      updateAiVisitorStats();
    }
  },
  { deep: true },
);

watch(
  [websiteVisitorStatsData, selectedRangeWebsite],
  () => {
    if (websiteVisitorStatsData.value.length > 0) {
      updateWebsiteVisitorStats();
    }
  },
  { deep: true },
);

// 处理智能体类型变化
async function handleAgentChange(value) {
  try {
    // 设置加载状态
    aiLoading.value = true;

    selectedAgent.value = value;

    // 更新AI访问量数据和AI访客统计数据
    const [aiAccessData, aiVisitorData] = await Promise.all([getAiAccessData(), getAiVisitorStats()]);

    aiAccessChartData.value = aiAccessData;
    aiVisitorStatsData.value = aiVisitorData;

    updateAiChartData();
    updateAiVisitorStats();
  } catch (error) {
    console.error('AI数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    aiLoading.value = false;
  }
}

// 处理页面变化
async function handlePageChange(value) {
  try {
    // 设置加载状态
    websiteLoading.value = true;

    selectedPage.value = value;

    // 更新网站访问量数据和网站访客统计数据
    const [websiteAccessData, websiteVisitorData] = await Promise.all([
      getWebsiteAccessData(),
      getWebsiteVisitorStats(),
    ]);

    websiteAccessChartData.value = websiteAccessData;
    websiteVisitorStatsData.value = websiteVisitorData;

    updateWebsiteChartData();
    updateWebsiteVisitorStats();
  } catch (error) {
    console.error('网站数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    websiteLoading.value = false;
  }
}

// 切换AI时间范围
async function handleTimeRangeChangeAI(days) {
  try {
    // 设置加载状态
    aiLoading.value = true;

    const numDays = parseInt(days, 10);
    const range = timeRanges.find((r) => parseInt(r.days, 10) === numDays);

    if (range) {
      selectedRangeAI.value = range;

      // 获取新AI数据
      const [aiAccessData, aiVisitorData] = await Promise.all([getAiAccessData(), getAiVisitorStats()]);

      // 更新AI数据
      aiAccessChartData.value = aiAccessData;
      aiVisitorStatsData.value = aiVisitorData;

      // 更新AI视图
      updateAiChartData();
      updateAiVisitorStats();
    }
  } catch (error) {
    console.error('AI数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    aiLoading.value = false;
  }
}

// 切换网站时间范围
async function handleTimeRangeChangeWebsite(days) {
  try {
    // 设置加载状态
    websiteLoading.value = true;

    const numDays = parseInt(days, 10);
    const range = timeRanges.find((r) => parseInt(r.days, 10) === numDays);

    if (range) {
      selectedRangeWebsite.value = range;

      // 获取新网站数据
      const [websiteAccessData, websiteVisitorData] = await Promise.all([
        getWebsiteAccessData(),
        getWebsiteVisitorStats(),
      ]);

      // 更新网站数据
      websiteAccessChartData.value = websiteAccessData;
      websiteVisitorStatsData.value = websiteVisitorData;

      // 更新网站视图
      updateWebsiteChartData();
      updateWebsiteVisitorStats();
    }
  } catch (error) {
    console.error('网站数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    websiteLoading.value = false;
  }
}

// 更新AI数据
const handleUpdateAI = async () => {
  try {
    // 设置加载状态
    aiLoading.value = true;

    // 并行获取AI相关数据
    const [aiAccessData, aiVisitorData] = await Promise.all([getAiAccessData(), getAiVisitorStats()]);

    // 更新数据
    aiAccessChartData.value = aiAccessData;
    aiVisitorStatsData.value = aiVisitorData;

    // 更新视图
    updateAiChartData();
    updateAiVisitorStats();
  } catch (error) {
    console.error('AI数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    aiLoading.value = false;
  }
};

// 更新网站数据
const handleUpdateWebsite = async () => {
  try {
    // 设置加载状态
    websiteLoading.value = true;

    // 并行获取网站相关数据
    const [websiteAccessData, websiteVisitorData] = await Promise.all([
      getWebsiteAccessData(),
      getWebsiteVisitorStats(),
    ]);

    // 更新数据
    websiteAccessChartData.value = websiteAccessData;
    websiteVisitorStatsData.value = websiteVisitorData;

    // 更新视图
    updateWebsiteChartData();
    updateWebsiteVisitorStats();
  } catch (error) {
    console.error('网站数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    websiteLoading.value = false;
  }
};

// 更新所有数据（保留原函数用于初始化）
const handleUpdate = async () => {
  try {
    // 设置加载状态
    aiLoading.value = true;
    websiteLoading.value = true;

    // 并行获取所有数据
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
  } catch (error) {
    console.error('数据更新失败:', error);
  } finally {
    // 无论成功或失败都取消加载状态
    aiLoading.value = false;
    websiteLoading.value = false;
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
});
</script>

<style scoped>
.kanban-main {
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
    background-color: transparent !important; /* 透明背景 */
    font-weight: bold !important; /* 加粗字体 */
    color: inherit; /* 可选：保持默认文字颜色 */
  }

  /* 可选：去除表头 hover 效果（如果不需要） */
  :deep(.t-table th:hover) {
    background-color: transparent !important;
  }
}
</style>
