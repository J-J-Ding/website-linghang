<template>
  <div class="kanban-main">
      <t-tooltip content="返回代码生成助手" placement="top">
          <t-button class="back-to-chat" size="large" theme="primary" shape="circle" variant="base" @click="jumpToChatPage">
              <icon name="arrow-left" />
          </t-button>
      </t-tooltip>

      <t-space direction="vertical">
          <t-card title="团队度量衡-AI辅助生成率" class="kanban-card" hover-shadow>
              <template #actions>
                  <t-space>
                      <t-button shape="circle" variant="outline" @click="refreshTask">
                          <icon name="refresh" />
                      </t-button>
                      <t-select
                        v-model="selectedIteration"
                        placeholder="选择迭代"
                        :options="IterationOptions"
                        multiple
                        minCollapsedNum="1"
                        clearable
                        autoWidth
                      />
                  </t-space>
              </template>
              <div id="teamAccessChart" style="width: 100%; height: 700px"></div>
          </t-card>
          <t-card title="团队度量衡-AI生成代码行数" class="kanban-card" hover-shadow>
              <template #actions>
                  <t-space>
                      <t-button shape="circle" variant="outline" @click="refreshTask">
                          <icon name="refresh" />
                      </t-button>
                      <t-select
                        v-model="selectedRowIteration"
                        placeholder="选择迭代"
                        :options="IterationOptions"
                        multiple
                        minCollapsedNum="1"
                        clearable
                        autoWidth
                      />
                  </t-space>
              </template>
              <div id="teamRowAccessChart" style="width: 100%; height: 700px"></div>
          </t-card>
          <t-card title="组件度量衡-AI辅助生成率" class="kanban-card" hover-shadow>
              <template #actions>
                  <t-space>
                      <t-button shape="circle" variant="outline" @click="refreshTask">
                          <icon name="refresh" />
                      </t-button>
                      <t-select
                        v-model="selectedComponentIteration"
                        placeholder="选择迭代"
                        :options="IterationOptions"
                        multiple
                        minCollapsedNum="1"
                        clearable
                        autoWidth
                      />
                  </t-space>
              </template>
              <div id="componentAccessChart" style="width: 100%; height: 700px"></div>
          </t-card>
          <t-card title="组件度量衡-AI生成代码行数" class="kanban-card" hover-shadow>
              <template #actions>
                  <t-space>
                      <t-button shape="circle" variant="outline" @click="refreshTask">
                          <icon name="refresh" />
                      </t-button>
                      <t-select
                        v-model="selectedRowComponentIteration"
                        placeholder="选择迭代"
                        :options="IterationOptions"
                        multiple
                        minCollapsedNum="1"
                        clearable
                        autoWidth
                      />
                  </t-space>
              </template>
              <div id="componentRowAccessChart" style="width: 100%; height: 700px"></div>
          </t-card>
          <t-card title="页面访问量" class="kanban-card" hover-shadow>
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
                </t-space>
            </template>
            <div id="websiteAccessChart" style="width: 100%; height: 700px"></div>
          </t-card>

      </t-space>

  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { Icon } from 'tdesign-icons-vue-next';
import { useRouter } from 'vue-router';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const jumpToChatPage = () => {
router.push('/ai/code/genCode');
};

// 时间范围选项
const timeRanges = [
{ label: '最近7天', days: '7' },
{ label: '最近30天', days: '30' },
{ label: '最近90天', days: '90' },
];
const selectedRange = ref(timeRanges[1]);

const IterationOptions = [
  { label: '2025S14', value: '2025S14' },
  { label: '2025S15', value: '2025S15' },
  { label: '2025S16', value: '2025S16' },
  { label: '2025S17', value: '2025S17' },
  { label: '2025S18', value: '2025S18' },
  { label: '2025S19', value: '2025S19' },
  { label: '2025S20', value: '2025S20' },
  { label: '2025S21', value: '2025S21' },
  { label: '2025S22', value: '2025S22' },
  { label: '2025S23', value: '2025S23' },
  { label: '2025S24', value: '2025S24' },
  { label: '2025S25', value: '2025S25' },
]

const selectedIteration = ref([]);
selectedIteration.value = IterationOptions.map(option => option.value);

const selectedRowIteration = ref([]);
selectedRowIteration.value = IterationOptions.map(option => option.value);

const selectedComponentIteration = ref([]);
selectedComponentIteration.value = IterationOptions.map(option => option.value);

const selectedRowComponentIteration = ref([]);
selectedRowComponentIteration.value = IterationOptions.map(option => option.value);

// 网站访问量图表数据
let websiteAccessChart = null;
const websiteAccessChartData = ref([]);
// 团队AI辅助生成率
let teamAccessChart = null;
const teamAccessChartData = ref([]);
// 团队AI生成代码行数
let teamRowAccessChart = null;
const teamRowAccessChartData = ref([]);
// 组件AI辅助生成率
let componentAccessChart = null;
const componentAccessChartData = ref([]);
// 组件AI生成代码行数
let componentRowAccessChart = null;
const componentRowAccessChartData = ref([]);

// 获取网站访问量数据 (PV/UV)
const getWebsiteAccessData = async () => {
try {
  const params = {
    period: parseInt(selectedRange.value.days),
  };

  params.page = "代码生成助手";
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

// 获取团队数据
const getTeamAccessData = async () => {
  const target_teams = [
    'L0-极光', 'L0-光速', 'L0-疾电之光', 'L2-集结号', "L2-超能",
    '支撑-BaseMan守垒员', '支撑-StarWar', '支撑-乘风破浪', '支撑-茅店神',
    '支撑-破冰号', '支撑-北极星', '支撑-猿宇宙', '仿真-天问'
  ]
  const requestData = { table_name: 'task_team_summary', conditions: {},};
    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });
    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }
    const responseData = await response.json();
    const dataList = responseData.data;
    const grouped = {};
    for (const item of dataList) {
      const { 迭代, 团队, 任务总数, AI辅助生成数, AI生成代码行数 } = item;
      if (!grouped[迭代]) {
        grouped[迭代] = {};
      }
      let AI辅助生成率 = 0;
      if (任务总数 > 0) {
        AI辅助生成率 = (AI辅助生成数 / 任务总数) * 100;
      }
      AI辅助生成率 = (任务总数 > 0 ? (AI辅助生成数 / 任务总数) * 100 : 0).toFixed(2) + '%';
      grouped[迭代][团队] = { 任务总数, AI辅助生成数, AI生成代码行数, AI辅助生成率};
    }
    const result = [];
    for (const 迭代 in grouped) {
      const 团队统计 = grouped[迭代];
      const row = { 迭代: 迭代 };
      for (const 团队 in 团队统计) {
        if (target_teams.includes(团队)){
          row[团队] = 团队统计[团队];
        }
      }
      result.push(row);
    }
    return result;
};

// 获取组件数据
const getComponentAccessData = async () => {
  const requestData = { table_name: 'task_component_summary', conditions: {},};
    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });
    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }
    const responseData = await response.json();
    const dataList = responseData.data;
    const grouped = {};
    for (const item of dataList) {
      const { 迭代, 波及组件, 任务总数, AI辅助生成数, AI生成代码行数 } = item;
      if (!grouped[迭代]) {
        grouped[迭代] = {};
      }
      let AI辅助生成率 = 0;
      if (任务总数 > 0) {
        AI辅助生成率 = (AI辅助生成数 / 任务总数) * 100;
      }
      AI辅助生成率 = (任务总数 > 0 ? (AI辅助生成数 / 任务总数) * 100 : 0).toFixed(2) + '%';
      grouped[迭代][波及组件] = { 任务总数, AI辅助生成数, AI生成代码行数, AI辅助生成率};
    }
    const result = [];
    for (const 迭代 in grouped) {
      const 组件统计 = grouped[迭代];
      const row = { 迭代: 迭代 };
      for (const 波及组件 in 组件统计) {
        row[波及组件] = 组件统计[波及组件];
      }
      result.push(row);
    }
    return result;
};

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

function updateAIGenerationRateChart(iter, chart_data, chart) {
  const iterations = iter.value;
  const filteredDataByIteration = chart_data.value.filter(
    item => iterations.includes(item.迭代)
  );
  const allTeams = new Set();
  chart_data.value.forEach(iterData => {
    Object.keys(iterData).forEach(key => {
      if (key !== '迭代') allTeams.add(key);
    });
  });
  const teamNames = Array.from(allTeams);
  const seriesData = {};
  teamNames.sort();
  teamNames.forEach(team => {
    seriesData[team] = [];
  });

  iterations.forEach((iteration, index) => {
    const iterData = filteredDataByIteration.find(item => item.迭代 === iteration);
    teamNames.forEach(team => {
      const stats = iterData[team];
      if (stats && stats.AI辅助生成率) {
        const rate = parseFloat(stats.AI辅助生成率.replace('%', ''));
        seriesData[team].push(rate);
      } else {
        seriesData[team].push(0);
      }
    });
  });
  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      enterable: true,
      confine: true,
      formatter: (params) => {
        const iteration = params[0].axisValue; // 当前横轴：迭代名称
        const iterData = chart_data.value.find(d => d.迭代 === iteration);
        // ✅ 将 params 按 value（AI辅助生成率）从高到低排序
        const sortedParams = [...params].sort((a, b) => b.value - a.value);
        let tooltipText = `<div style="font-weight: bold; margin-bottom: 8px;user-select: text;">📊 迭代：${iteration}</div>`;
        tooltipText += `
          <div style="
            max-height: 500px;       /* 最大高度，超过可滚动 */
            overflow-y: auto;        /* 垂直滚动条 */
            padding: 8px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: #fafafa;
            font-size: 13px;
            user-select: text;
          ">
        `;
        sortedParams.forEach((param) => {
          const team = param.seriesName;
          const value = param.value; // AI辅助生成率（数字，比如 89.3）
          const teamStats = iterData[team];
          if (teamStats) {
            const taskTotal = teamStats.任务总数 || 0;
            const aiGenerated = teamStats.AI辅助生成数 || 0;
            const aiRateStr = teamStats.AI辅助生成率 || '0.00%';
            tooltipText += `
              <div style="margin: 6px 0; padding: 4px; border-left: 3px solid ${param.color}; background: #f9f9f9;">
                <p>
                  <b style="color: ${param.color};">🔹 ${team}</b>
                  任务总数: <b>${taskTotal}</b>
                  AI生成数: <b>${aiGenerated}</b>
                  AI辅助生成率: <b style="color: ${param.color};">${aiRateStr}</b>
                </p>
              </div>
            `;
          }
        });
        tooltipText += `
          </div>  <!-- 结束滚动容器 -->
        `;
        return tooltipText;
      },
    },
    legend: {
      type: "scroll",
      data: teamNames,
      top: 0,
      itemGap: 15
    },
    xAxis: {
      type: 'category',
      data: iterations,
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: 'AI辅助生成率 (%)',
      nameLocation: 'middle',
      nameGap: 35,
      min: 0,
      max: 100,
    },
    series: teamNames.map(team => ({
      name: team,
      type: 'line',
      data: seriesData[team],
      smooth: true,
      itemStyle: {
        color: getRandomColor(),
      },
      label: {
        show: true,
        position: 'top',
        valueAnimation: true,
        formatter: '{c}%',
      },
    })),
    grid: {
      left: '5%',
      right: '5%',
      bottom: '5%',
      top: '10%',
      containLabel: true,
    },
  };
  if (chart) {
    chart.setOption(option, true);
  }
}


function updateAIGenerationRowChart(iter, chart_data, chart) {
  const iterations = iter.value;
  const filteredDataByIteration = chart_data.value.filter(
    item => iterations.includes(item.迭代)
  );
  const allTeams = new Set();
  chart_data.value.forEach(iterData => {
    Object.keys(iterData).forEach(key => {
      if (key !== '迭代') allTeams.add(key);
    });
  });
  const teamNames = Array.from(allTeams);
  const seriesData = {};
  teamNames.sort();
  teamNames.forEach(team => {
    seriesData[team] = [];
  });

  let maxYValue = 0;

  iterations.forEach((iteration, index) => {
    const iterData = filteredDataByIteration.find(item => item.迭代 === iteration);
    teamNames.forEach(team => {
      const stats = iterData[team];
      if (stats && stats.AI生成代码行数) {
        const rate = stats.AI生成代码行数;
        maxYValue = Math.max(maxYValue, rate);
        seriesData[team].push(rate);
      } else {
        seriesData[team].push(0);
      }
    });
  });

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      enterable: true,
      confine: true,
      formatter: (params) => {
        const iteration = params[0].axisValue; // 当前横轴：迭代名称
        const iterData = chart_data.value.find(d => d.迭代 === iteration);
        const sortedParams = [...params].sort((a, b) => b.value - a.value);
        let tooltipText = `<div style="font-weight: bold; margin-bottom: 8px;user-select: text;">📊 迭代：${iteration}</div>`;
        tooltipText += `
          <div style="
            max-height: 500px;       /* 最大高度，超过可滚动 */
            overflow-y: auto;        /* 垂直滚动条 */
            padding: 8px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: #fafafa;
            font-size: 13px;
            user-select: text;
          ">
        `;
        sortedParams.forEach((param) => {
          const team = param.seriesName;
          const value = param.value;
          const teamStats = iterData[team];
          if (teamStats) {
            const aiGenerated = teamStats.AI生成代码行数 || 0;
            tooltipText += `
              <div style="margin: 6px 0; padding: 4px; border-left: 3px solid ${param.color}; background: #f9f9f9;">
                <p>
                  <b style="color: ${param.color};">🔹 ${team}</b>
                  AI生成代码行数: <b style="color: ${param.color};">${aiGenerated}</b>
                </p>
              </div>
            `;
          }
        });
        tooltipText += `
          </div>  <!-- 结束滚动容器 -->
        `;
        return tooltipText;
      },
    },
    legend: {
      type: "scroll",
      data: teamNames,
      top: 0,
      itemGap: 15
    },
    xAxis: {
      type: 'category',
      data: iterations,
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: 'AI生成代码行数 (行)',
      nameLocation: 'middle',
      nameGap: 35,
      min: 0,
      max: maxYValue,
    },
    series: teamNames.map(team => ({
      name: team,
      type: 'line',
      data: seriesData[team],
      smooth: true,
      itemStyle: {
        color: getRandomColor(),
      },
      label: {
        show: true,
        position: 'top',
        valueAnimation: true,
        formatter: '{c}',
      },
    })),
    grid: {
      left: '5%',
      right: '5%',
      bottom: '5%',
      top: '10%',
      containLabel: true,
    },
  };
  if (chart) {
    chart.setOption(option, true);
  }
}


function getRandomColor() {
  const colors = ['#1890FF', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96'];
  return colors[Math.floor(Math.random() * colors.length)];
}


// 初始化图表
onMounted(async () => {
  const websiteChartDom = document.getElementById('websiteAccessChart');
  websiteAccessChart = echarts.init(websiteChartDom);

  const teamChartDom = document.getElementById('teamAccessChart');
  teamAccessChart = echarts.init(teamChartDom);

  const teamRowChartDom = document.getElementById('teamRowAccessChart');
  teamRowAccessChart = echarts.init(teamRowChartDom);

  const componentChartDom = document.getElementById('componentAccessChart');
  componentAccessChart = echarts.init(componentChartDom);

  const componentRowChartDom = document.getElementById('componentRowAccessChart');
  componentRowAccessChart = echarts.init(componentRowChartDom);
  // 添加 resize 事件监听器
  window.addEventListener('resize', () => {
    if (websiteAccessChart) websiteAccessChart.resize();
    if (teamAccessChart) teamAccessChart.resize();
    if (teamRowAccessChart) teamRowAccessChart.resize();
    if (componentAccessChart) componentAccessChart.resize();
    if (componentRowAccessChart) componentRowAccessChart.resize();
  });
  // 获取初始数据
  await handleUpdate();
});

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
  [teamAccessChartData, selectedIteration],
  () => {
    if (teamAccessChartData.value.length > 0) {
      updateAIGenerationRateChart(selectedIteration, teamAccessChartData, teamAccessChart);
    }
  },
  { deep: true },
);

watch(
  [teamRowAccessChartData, selectedRowIteration],
  () => {
    if (teamAccessChartData.value.length > 0) {
      updateAIGenerationRowChart(selectedRowIteration, teamRowAccessChartData, teamRowAccessChart)
    }
  },
  { deep: true },
);

watch(
  [componentAccessChartData, selectedComponentIteration],
  () => {
    if (componentAccessChartData.value.length > 0) {
      updateAIGenerationRateChart(selectedComponentIteration, componentAccessChartData, componentAccessChart);
    }
  },
  { deep: true },
);

watch(
  [componentRowAccessChartData, selectedRowComponentIteration],
  () => {
    if (componentRowAccessChartData.value.length > 0) {
      updateAIGenerationRowChart(selectedRowComponentIteration, componentRowAccessChartData, componentRowAccessChart)
    }
  },
  { deep: true },
);

// 切换时间范围
async function handleTimeRangeChange(days) {
  const numDays = parseInt(days, 10);
  const range = timeRanges.find((r) => parseInt(r.days, 10) === numDays);
  if (range) {
    selectedRange.value = range;
    // 获取新数据
    const [websiteAccessData] = await Promise.all([
      getWebsiteAccessData(),
    ]);
    // 更新数据
    websiteAccessChartData.value = websiteAccessData;
    // 更新视图
    updateWebsiteChartData();
  }
}

const refreshTask = async () => {
    MessagePlugin.loading('开始刷新任务...');
    // 刷新一次表格
    const refreshData = await fetch(`${SERVER_API_URL}/api_data/refresh_task`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    await handleUpdate();
    MessagePlugin.success('任务更新成功');
}

// 更新所有数据
const handleUpdate = async () => {
try {
  // 并行获取所有数据
  const [websiteAccessData, teamAccessData, componentAccessData] = await Promise.all([
    getWebsiteAccessData(),
    getTeamAccessData(),
    getComponentAccessData(),
  ]);
  // 更新数据
  websiteAccessChartData.value = websiteAccessData;
  teamAccessChartData.value = teamAccessData;
  teamRowAccessChartData.value = teamAccessData;
  componentAccessChartData.value = componentAccessData;
  componentRowAccessChartData.value = componentAccessData;

} catch (error) {
  console.error('数据更新失败:', error);
  MessagePlugin.error('数据更新失败');
}
};

// 组件销毁前清理图表实例
onBeforeUnmount(() => {
  if (websiteAccessChart) {
    websiteAccessChart.dispose();
    websiteAccessChart = null;
  }
  if (teamAccessChart) {
    teamAccessChart.dispose();
    teamAccessChart = null;
  }
  if (teamRowAccessChart) {
    teamRowAccessChart.dispose();
    teamRowAccessChart = null;
  }
  if (componentAccessChart) {
    componentAccessChart.dispose();
    componentAccessChart = null;
  }
  if (componentRowAccessChart) {
    componentRowAccessChart.dispose();
    componentRowAccessChart = null;
  }
});
</script>

<style scoped>
.kanban-main {
  .back-to-chat {
    margin-bottom: 15px;
  }

  .kanban-card {
    flex: 1;
    min-width: 1600px; /* 设置最小宽度 */
  }

  :deep(.t-card) {
    display: flex;
    padding: 10px;
    flex-direction: column;
    height: 700px; /* 固定高度 */
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
