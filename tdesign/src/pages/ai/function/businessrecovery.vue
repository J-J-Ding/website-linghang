<template>
  <div class="channel-alert-analysis">
    <!-- 时间选择区域 -->
    <div class="time-selection-section">
      <div class="time-range-selector">
        <div class="section-header-project">
          <!-- <h2>{{ projectName }}</h2> -->
          <t-select 
          v-model="projectName"
          label="项目名称: "
          filterable
          placeholder="请选择项目名称" 
          @popup-visible-change="showSelectProjectDialog">
            <t-option v-for="item in projectOption" :key="item.project_name" :value="item.project_name" :label="item.project_name"></t-option>
          </t-select>
        </div>

        <div class="time-range-header">
          <div class="preset-buttons">
            <t-button variant="outline" size="small" @click="setTimeRange('today')">今天</t-button>
            <t-button variant="outline" size="small" @click="setTimeRange('yesterday')">昨天</t-button>
            <t-button variant="outline" size="small" @click="setTimeRange('last7days')">最近7天</t-button>
            <t-button variant="outline" size="small" @click="setTimeRange('last30days')">最近30天</t-button>
          </div>
        </div>
        
        <div class="time-range-picker">
          <t-date-range-picker
            v-model="timeRange"
            format="YYYY-MM-DD HH:mm:ss"
            value-type="YYYY-MM-DD HH:mm:ss"
            :enable-time-picker="true"
            :clearable="false"
            allow-input
            @change="handleTimeRangeChange"
          />
          
          <div class="time-display">
            <t-button theme="primary" @click="handleAnalyze">
              业务分析
            </t-button>
          </div>

          <div class="data-statistics">
            <t-button theme="success" @click="handleDataStatistics">
              数据统计
            </t-button>
          </div>
        </div>
      </div>

      <div class="analysis-results-section">
        <div class="section-header">
          <h2>业务恢复分析列表</h2>
          <div class="section-controls">
            <t-button variant="outline" size="small" @click="exportResults">
              <template #icon><t-icon name="download" /></template>
              导出结果
            </t-button>
          </div>
        </div>
        
        <div class="results-table-container">
          <t-table
            :data="businessList"
            :columns="columns"
            row-key="call_id"
            :selected-row-keys="selectedRowKeyList"
            :select-on-row-click="false"
            :hover="true"
            :max-height="tableHeight"
            bordered
            resizable
            :pagination="pagination"
            @page-change="handlePageChange"
            @select-change="handleSelectChange"
            @active-change="onActiveChange"
          >
            <!-- 自定义告警时间单元格 -->
            <!-- <template #alarm_time="{ row }">
              <div class="alert-time-cell">
                <span class="alert-date">{{ formatDate(row.alarm_time, 'date') }}</span>
                <span class="alert-time">{{ formatDate(row.alarm_time, 'time') }}</span>
              </div>
            </template> -->
            <template #alarm_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.alarm_time, 'full') }}
              </div>
            </template>
            
            <!-- 自定义业务动作时间单元格 -->
            <template #start_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.start_time, 'full') }}
              </div>
            </template>
            
            <!-- 自定义结束时间单元格 -->
            <template #end_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.end_time, 'full') }}
              </div>
            </template>
            
            <!-- 自定义业务日期单元格 -->
            <template #businessDate="{ row }">
              <div class="date-cell">
                {{ formatDate(row.businessDate, 'slash') }}
              </div>
            </template>
            
            <!-- 自定义操作单元格 -->
            <template #operation="{ row }">
              <div class="operation-buttons">
                <!-- <t-button 
                  theme="primary" 
                  variant="text" 
                  size="small"
                  @click="handleAnalyzeBusiness(row)"
                >
                  分析
                </t-button> -->
                <t-button 
                  theme="default" 
                  variant="text" 
                  size="small"
                  @click="handleViewDetails(row)"
                >
                  详情
                </t-button>
              </div>
            </template>
            
            <!-- 自定义告警节点单元格 -->
            <template #alertNode="{ row }">
              <div class="alert-node-cell">
                <span class="node-name">{{ row.alertNode }}</span>
                <span class="node-id">({{ row.nodeId }})</span>
              </div>
            </template>
            
            <!-- 自定义受影响路径单元格 -->
            <template #affectedPath="{ row }">
              <div class="path-cell">
                <div class="path-text" :title="row.affectedPath">
                  {{ row.affectedPath }}
                </div>
                <div v-if="row.sourcePort" class="source-port">
                  源口：{{ row.sourcePort }}
                </div>
              </div>
            </template>
          </t-table>
        </div>
      </div>
    </div>
    
    <!-- 分析详情弹窗 -->
    <t-dialog
      v-model:visible="detailDialogVisible"
      header="业务详情分析"
      width="800px"
      :footer="false"
      @close="handleDetailDialogClose"
    >
      <div v-if="selectedBusiness" class="detail-dialog-content">
        <div class="business-info-section">
          <h3>业务基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">业务ID：</span>
              <span class="info-value">{{ selectedBusiness.businessId }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">波长：</span>
              <span class="info-value">{{ selectedBusiness.wavelength }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">属性：</span>
              <span class="info-value">{{ selectedBusiness.property }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">告警时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.alarm_time, 'full') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.start_time, 'full') }}</span>
            </div>
            <!-- <div class="info-item">
              <span class="info-label">结束时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.end_time, 'full') }}</span>
            </div> -->
          </div>
        </div>
        
        <div class="path-info-section">
          <h3>受影响路径</h3>
          <div class="path-display">
            <div class="path-nodes">
              <span 
                v-for="(node, index) in getPathNodes(selectedBusiness.affectedPath)" 
                :key="index"
                :class="['path-node', { 'alert-node': isAlertNode(node) }]"
              >
                {{ node }}
                <span v-if="index < getPathNodes(selectedBusiness.affectedPath).length - 1" class="path-arrow">→</span>
              </span>
            </div>
            <div v-if="selectedBusiness.sourcePort" class="source-port-info">
              <span class="port-label">源口：</span>
              <span class="port-value">{{ selectedBusiness.sourcePort }}</span>
            </div>
          </div>
        </div>
        
        <div class="action-history-section">
          <h3>历史动作记录</h3>
          <t-table
            :data="actionHistory"
            :columns="actionColumns"
            row-key="id"
            :hover="true"
            size="small"
          >
            <template #time="{ row }">
              {{ formatDate(row.time, 'full') }}
            </template>
            <template #operation="{ row }">
              <t-tag :theme="getActionTagTheme(row.action)" size="small">
                {{ row.action }}
              </t-tag>
            </template>
          </t-table>
        </div>
        
        <div class="dialog-footer">
          <t-button @click="detailDialogVisible = false">关闭</t-button>
          <t-button theme="primary" @click="handleGoToFunction2">
            转到功能二：路径上业务历史动作和原因分析
          </t-button>
        </div>
      </div>
    </t-dialog>

    <t-dialog
      v-model:visible="statisticsDialogVisible"
      header="数据统计"
      width="800px"
      :footer="false"
      @close="statisticsDialogVisible = false"
    >
      <div class="statistics-dialog-content">
        <!-- 使用 t-descriptions 展示主要指标 -->
        <t-descriptions :column="2" bordered :label-style="{ width: '140px', fontWeight: '500' }">
          <t-descriptions-item label="恢复总次数">
            {{ statisticsData.restore_cnt }}
          </t-descriptions-item>
          <t-descriptions-item label="恢复成功次数">
            {{ statisticsData.restore_succ_cnt }}
          </t-descriptions-item>
          <t-descriptions-item label="恢复成功率">
            <span class="rate-detail">({{ statisticsData.restore_succ_cnt }}/{{ statisticsData.restore_cnt }})</span>
            <span class="success-rate">{{ statisticsData.restore_succ_rate }}%</span>
          </t-descriptions-item>
          <t-descriptions-item label="变路由重试总次数">
            {{ statisticsData.route_retry_num }}
          </t-descriptions-item>
        </t-descriptions>

        <!-- 失败原因大类占比 -->
        <div class="stat-section">
          <div class="section-title">失败原因细分占比</div>
          <t-descriptions :column="1" bordered :label-style="{ width: '220px', fontWeight: '500' }">
            <t-descriptions-item label="恢复失败原因细分统计">
              {{ statisticsData.fail_reason_stat }}
            </t-descriptions-item>
          </t-descriptions>
        </div>

        <!-- 失败原因细分占比 -->
        <div class="stat-section">
          <div class="section-title">失败原因大类统计</div>
          <t-descriptions :column="1" bordered :label-style="{ width: '220px', fontWeight: '500' }">
            <t-descriptions-item label="恢复失败原因大类统计">
              {{ statisticsData.fail_reason_class_stat }}
            </t-descriptions-item>
          </t-descriptions>
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="jsx">
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { 
  MessagePlugin
} from 'tdesign-vue-next';
import dayjs from 'dayjs';
import { Utils } from "@/utils/utils";
import { getProjectList, getRenewStatsList, getRenewStatsSum } from "@/api/analysis";
import { useRoute } from 'vue-router'; // 导入useRoute
import * as XLSX from 'xlsx';
import { storage } from "@/utils/storage";
// 状态管理
const PROJECT_CACHE_KEY = 'selected_project_name';
const timeRange = ref([]);
const detailDialogVisible = ref(false);
const selectedBusiness = ref(null);
const selectedRowKeyList = ref([]);
const hoveredBusinessId = ref(null);
const selectedNode = ref(null);
const route = useRoute();
// 拖拽和缩放状态
const zoomLevel = ref(1);
const panX = ref(0);
const panY = ref(0);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const lastPan = ref({ x: 0, y: 0 });
const projectOption = ref([]);
// SVG尺寸
const svgWidth = ref(800);
const svgHeight = ref(600);

// 防抖相关
const hoverDebounce = ref(null);

// 拓扑图数据
const topologyNodes = ref([]);
const topologyLinks = ref([]);

// 容器引用
const topologyContainer = ref(null);

const projectName = ref(null); // 添加项目名称变量

// 表格列定义（添加复选框列）
const columns = [
  {
    colKey: 'row-select',
    type: 'multiple',
    width: 70,
  },
  {
    title: '业务id',
    colKey: 'call_id',
    width: 200,
    cell: 'call_id',
  },
  {
    title: '恢复总次数',
    colKey: 'restore_cnt',
    width: 100,
    cell: 'restore_cnt',
  },
  // {
  //   title: '时间',
  //   colKey: 'time_range',
  //   width: 250,
  //   cell: (h, { row }) => {
  //     return h('div', { 
  //         style: 'white-space: pre-line; line-height: 1.5;'
  //       }, `开始时间：${row.start_time} \n 结束时间：${row.end_time}`);
  //   },
  // },
  {
    title: '恢复成功次数',
    colKey: 'restore_succ_cnt',
    width: 100,
    cell: 'restore_succ_cnt',
  },
  {
    title: '恢复成功率',
    colKey: 'restore_succ_rate',
    width: 100,
  },
  {
    title: '通道告警触发恢复占比',
    colKey: 'hov_alarm_restore_rate',
    width: 150,
  },
  {
    title: '预置使用占比',
    colKey: 'preroute_rate',
    width: 150,
  },
  {
    title: '恢复失败原因统计',
    colKey: 'fail_reason_stat',
    width: 200,
    ellipsis: { theme: 'light', placement: 'bottom' },
  },
  {
    title: '变路由重试次数',
    colKey: 'route_retry_num',
    width: 100,
  },
  {
    title: '操作',
    colKey: 'operation',
    width: 120,
    fixed: 'right',
    cell: 'operation',
  },
];

// 动作历史表格列
const actionColumns = [
  {
    title: '时间',
    colKey: 'time',
    width: 180
  },
  {
    title: '动作',
    colKey: 'action',
    width: 100
  },
  {
    title: '操作人',
    colKey: 'operator',
    width: 100
  },
  {
    title: '原因',
    colKey: 'reason',
    minWidth: 200
  }
];

// 分页配置
const pagination = reactive({
  defaultPageSize: 10,
  total: 0,
  defaultCurrent: 1,
  pageSizeOptions: [10, 20, 50, 100, 200],
  showJumper: true,
  showPageSize: true
});

const tableHeight = ref('400px');

const statisticsDialogVisible = ref(false);

// 统计数据结构（请根据实际后端数据调整）
const statisticsData = ref({
  restore_cnt: null,
  restore_succ_cnt: null,
  restore_succ_rate: null,
  route_retry_num: null,
  fail_reason_stat: null,
  fail_reason_class_stat: null,
});

// 获取大类进度条颜色
const getCategoryColor = (index) => {
  const colors = ['#0052d9', '#e37318', '#2ba471'];
  return colors[index % colors.length];
};

// 获取细分进度条颜色
const getDetailColor = (index) => {
  const colors = ['#0052d9', '#e37318', '#2ba471', '#ca6e3e', '#029cd4', '#b45f06'];
  return colors[index % colors.length];
};

// 修改原有 handleDataStatistics 函数
const handleDataStatistics = async () => {
  // 这里可以调用API获取真实统计数据，目前使用模拟数据
  // 例如: 
  await getDataStatistics(projectName.value, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  statisticsDialogVisible.value = true;
};

const formatTimeRange = (range) => {
  if (!range || !Array.isArray(range)) return [];
  return range.map(formatDateTime);
};

// 计算属性：格式化后的时间（给业务使用）
const formattedTimeRange = computed(() => formatTimeRange(timeRange.value));

// 计算属性
// const defaultTimeRange = computed(() => {
//   const now = new Date();
//   const sevenDaysAgo = new Date();
//   sevenDaysAgo.setDate(now.getDate() - 7);
//   return [sevenDaysAgo, now];
// });

// 根据表格复选框选择状态获取选中的业务
const selectedBusinesses = computed(() => {
  const selected = businessList.value.filter((business) => 
    selectedRowKeyList.value.includes(business.id)
  );
  console.log('选中的业务:', selected);
  return selected;
});

const alarmNodeCount = computed(() => {
  return topologyNodes.value.filter((node) => node.status === 'alert').length;
});

// 网格样式
// const gridStyle = computed(() => {
//   const size = 20 * zoomLevel.value;
//   return {
//     backgroundImage: `linear-gradient(to right, #e0e0e0 1px, transparent 1px),
//                       linear-gradient(to bottom, #e0e0e0 1px, transparent 1px)`,
//     backgroundSize: `${size}px ${size}px`,
//     transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomLevel.value})`,
//     transformOrigin: '0 0'
//   };
// });

// 模拟数据
const businessList = ref([]);

// 动作历史数据
const actionHistory = ref([
  {
    id: 1,
    time: '2025-07-19 12:32:31',
    action: '告警产生',
    operator: '系统',
    reason: '通道链路中断'
  },
  {
    id: 2,
    time: '2025-07-19 12:32:34',
    action: '业务切换',
    operator: '自动',
    reason: '主路径故障，切换到备用路径'
  },
  {
    id: 3,
    time: '2025-07-19 12:34:18',
    action: '路径恢复',
    operator: '系统',
    reason: '通道链路恢复'
  }
]);

const formatDateTime = (isoString) => {
  return dayjs(isoString).format('YYYY-MM-DD HH:mm:ss');
};

const showSelectProjectDialog = async () => {
  projectOption.value = await getProjectData();
};

const getProjectData = async () => {
  try {
    const params = {
      get_total: 0,
      enable_limit: 0,
      order: 'desc',
    };
    const response = await getProjectList(params);
    const projectInfo = response.data;
    // const projectInfo = transformProjects(response.data);
    return projectInfo;
  } catch (error) {
    MessagePlugin.error('获取项目列表失败，请重试');
    return [];
  }
};

// 方法
const formatDate = (dateValue, formatType = 'full') => {
  if (!dateValue) return '';
  
  let date;
  if (typeof dateValue === 'string') {
    date = new Date(dateValue);
    if (isNaN(date.getTime())) {
      const parts = dateValue.split(/[-/ :]/);
      if (parts.length >= 3) {
        date = new Date(parts[0], parts[1] - 1, parts[2], parts[3] || 0, parts[4] || 0, parts[5] || 0);
      }
    }
  } else {
    date = new Date(dateValue);
  }
  
  if (isNaN(date.getTime())) return dateValue;
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  switch (formatType) {
    case 'date':
      return `${year}-${month}-${day}`;
    case 'time':
      return `${hours}:${minutes}:${seconds}`;
    case 'full':
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    case 'chinese':
      return `${year}年${month}月${day}日 ${hours}:${minutes}:${seconds}`;
    case 'slash':
      return `${year}/${month}/${day}`;
    case 'iso':
      return `${year}-${month}-${day}`;
    default:
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  }
};

const getAlarmTable = async (project_name, enable_limit, page, limit, stime, etime) => {
  try {
    const params = {
      project_name: project_name,
      enable_limit: enable_limit,
      page: page,
      limit: limit,
      stime: stime,
      etime: etime
    }
    const response = await getRenewStatsList(params);
    // 为每条数据添加唯一id
    businessList.value = response.data;
    pagination.total = response.total;
    
    console.log('业务数据加载完成:', businessList.value);
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const getAlarmTables = async (project_name, enable_limit, page, limit, stime, etime) => {
  try {
    const params = {
      project_name: project_name,
      enable_limit: enable_limit,
      page: page,
      limit: limit,
      stime: stime,
      etime: etime
    }
    const response = await getRenewStatsList(params);
    // 为每条数据添加唯一id
    const table = response.data;
    return table;
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const getDataStatistics = async (project_name, stime, etime) => {
  try {
    const params = {
      project_name: project_name,
      stime: stime,
      etime: etime
    }
    const response = await getRenewStatsSum(params);
    // 为每条数据添加唯一id
    statisticsData.value = response.data[0];
    console.log('statisticsData', statisticsData.value);
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const exportAlarmTable = async (project_name, enable_limit, page, limit, stime, etime) => {
  try {
    const params = {
      project_name: project_name,
      enable_limit: enable_limit,
      page: page,
      limit: limit,
      stime: stime,
      etime: etime
    }
    const response = await getAlarmList(params);
    // 为每条数据添加唯一id
    const excelData = response.data.map((item, index) => ({
      ...item,
      id: item.alarm_id || `business_${index}_${Date.now()}_${Math.random()}`,
      businessId: item.call_id,
      wavelength: item.current_wave_str,
      property: item.current_conn_attr,
      affectedPath: item.current_route_str,
      alertNode: extractNodeName(item.alarm_str),
      nodeId: item.node_id,
      sourcePort: extractSourcePort(item.alarm_str),
      time_range: `开始时间：${item.start_time} \n 结束时间：${item.end_time}`,
      result: item.result ? '成功' : '失败',
    }));
    return excelData;
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const extractNodeName = (alarmStr) => {
  if (!alarmStr) return '';
  const match = alarmStr.match(/\(([^,]+),/);
  return match ? match[1] : '';
};

// 辅助函数：从告警字符串中提取源端口
const extractSourcePort = (alarmStr) => {
  if (!alarmStr) return '';
  const match = alarmStr.match(/\[([^\]]+)\]-\[([^\]]+)\]/);
  return match ? `${match[1]}-${match[2]}` : '';
};

const handleTimeRangeChange = (value) => {
  if (value && value.length === 2) {
    MessagePlugin.success(`时间范围已设置为: ${formatDate(value[0], 'chinese')} 至 ${formatDate(value[1], 'chinese')}`);
  }
};

const setTimeRange = (rangeType) => {
  const now = new Date();
  let startDate = new Date();
  let endDate = new Date();
  
  switch (rangeType) {
    case 'today':
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(23, 59, 59, 999);
      break;
    case 'yesterday':
      startDate.setDate(now.getDate() - 1);
      startDate.setHours(0, 0, 0, 0);
      endDate.setDate(now.getDate() - 1);
      endDate.setHours(23, 59, 59, 999);
      break;
    case 'last7days':
      startDate.setDate(now.getDate() - 6);
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(23, 59, 59, 999);
      break;
    case 'last30days':
      startDate.setDate(now.getDate() - 29);
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(23, 59, 59, 999);
      break;
    case 'last365days':
      startDate.setDate(now.getDate() - 365);
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(23, 59, 59, 999);
      break;
  }
  
  timeRange.value = [startDate, endDate];
  // MessagePlugin.success(`已选择${rangeType === 'today' ? '今天' : rangeType === 'yesterday' ? '昨天' : rangeType === 'last7days' ? '最近7天' : '最近30天'}的时间范围`);
};

const handleAnalyze = async () => {
  if (!timeRange.value || timeRange.value.length !== 2) {
    MessagePlugin.warning('请先选择时间范围');
    return;
  }
  await getAlarmTable(projectName.value, 1, 1, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  setTimeout(() => {
    generateTopologyData();
  }, 1500);
};

// 处理表格行选择变化
const handleSelectChange = (selectedRowKeys) => {
  selectedRowKeyList.value = selectedRowKeys;
  // 更新拓扑图高亮显示
  if (topologyNodes.value.length > 0) {
    updateTopologyData();
  }
};

const handleAnalyzeBusiness = (row) => {
   MessagePlugin.info(`正在跳转到业务分析页面: ${row.businessId}`);
  
  // 构建URL参数
  const params = new URLSearchParams({
    businessId: row.businessId,
    alarm_time: row.alarm_time,
    alertNode: row.alertNode,
    nodeId: row.nodeId,
    start_time: row.start_time,
    end_time: row.end_time,
    wavelength: row.wavelength,
    property: row.property,
    affectedPath: row.affectedPath,
    sourcePort: row.sourcePort || '',
    oms_lists: JSON.stringify(row.is_number_collect),
    businessDate: row.businessDate,
    project_name: projectName.value,
    oms_dict_list: JSON.stringify(row.oms_dict_list),
  }).toString();
  const baseUrl = Utils.getBaseUrl();
  // 打开新页面并传递数据
  window.open(`${baseUrl}/quality/logAnalysis/businessRecoveryDetails?${params}`, '_blank');
};

const handleViewDetails = (row) => {
  MessagePlugin.info(`正在跳转到告警分析页面: ${row.businessId}`);

  // 构建URL参数
  const params = new URLSearchParams({
    project_name: projectName.value,
    // businessId: row.businessId,
    call_id: row.call_id,
    // alarm_id: row.alarm_id,
    // alarm_time: row.alarm_time,
    // alertNode: row.alertNode,
    // nodeId: row.nodeId,
    time: timeRange.value,
    start_time: formattedTimeRange.value[0],
    end_time: formattedTimeRange.value[1],
    // wavelength: row.wavelength,
    // property: row.property,
    // affectedPath: row.affectedPath,
    // sourcePort: row.sourcePort || '',
    // businessDate: row.businessDate,
    // 添加一些额外的告警相关参数
    alertId: `alert_${row.call_id}_${Date.now()}`,
    alertType: 'business_recovery'
  }).toString();
  
  const baseUrl = Utils.getBaseUrl();
  // 打开新页面并传递数据
  window.open(`${baseUrl}/quality/logAnalysis/businessRecoveryDetails?${params}`, '_blank');
};

const handleDetailDialogClose = () => {
  selectedBusiness.value = null;
};

const handleGoToFunction2 = () => {
  MessagePlugin.info('跳转到功能二：路径上业务历史动作和原因分析');
  detailDialogVisible.value = false;
};

const exportResults = async () => {
  try {
    const tableData = await getAlarmTables(projectName.value, 0, pagination.defaultCurrent, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
    // const tableData = await exportAlarmTable(projectName.value, 0, pagination.defaultCurrent, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);

    if (tableData.length === 0) {
      MessagePlugin.warning('暂无数据可导出')
      return
    }

    const exportData = tableData.map((row) => {
      const exportRow = {}
      columns.forEach((col) => {
        if (['row-select', 'operation'].includes(col.colKey)) return

        let val = row[col.colKey]
        exportRow[col.title] = val !== null && val !== undefined ? String(val) : ''
      })
      return exportRow
    })

    const worksheet = XLSX.utils.json_to_sheet(exportData)

    const columnWidths = []
    const firstRow = exportData[0]
    if (firstRow) {
      Object.keys(firstRow).forEach((key) => {
        const headerWidth = key.length
        const maxWidth = Math.max(headerWidth, ...exportData.map((row) => (row[key] ? String(row[key]).length : 0)))
        columnWidths.push({ wch: Math.min(maxWidth + 2, 60) })
      })
    }
    worksheet['!cols'] = columnWidths

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '业务恢复分析的业务数据')

    const date = new Date()
    const formattedDate =
      `${date.getFullYear().toString().slice(2)}` +
      `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
      `${date.getDate().toString().padStart(2, '0')}` +
      `${date.getHours().toString().padStart(2, '0')}` +
      `${date.getMinutes().toString().padStart(2, '0')}`
    const fileName = `业务恢复分析的业务列表_${formattedDate}.xlsx`

    XLSX.writeFile(workbook, fileName)
    MessagePlugin.success('导出成功，请查看下载文件')
    
  } catch (error) {
    console.error('数据导出失败:', error)
    MessagePlugin.error('导出失败，请重试')
  }
};

const handlePageChange = async (pageInfo) => {
  await getAlarmTable(projectName.value, 1, pageInfo.current, pageInfo.pageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  pagination.defaultCurrent = pageInfo.current;
  pagination.defaultPageSize = pageInfo.pageSize;
};

const getPathNodes = (path) => {
  // 添加空值检查
  if (!path || typeof path !== 'string') return [];
  return path.split('-');
};

const isAlertNode = (node) => {
  return node.includes('[') && node.includes(']');
};

const getActionTagTheme = (action) => {
  const themes = {
    '告警产生': 'danger',
    '业务切换': 'warning',
    '路径恢复': 'success',
    '自动修复': 'primary'
  };
  return themes[action] || 'default';
};

const getPathPreview = (path) => {
  // 添加空值检查
  if (!path || typeof path !== 'string') return '无路径信息';
  
  const nodes = path.split('-');
  if (nodes.length <= 3) return path;
  return `${nodes[0]}-...-${nodes[nodes.length - 1]}`;
};

// 拓扑图相关方法
const removeBusinessFromTopology = (businessId) => {
  // 从选中的行中移除该业务
  const index = selectedRowKeyList.value.indexOf(businessId);
  if (index !== -1) {
    selectedRowKeyList.value.splice(index, 1);
    MessagePlugin.info(`已从拓扑图上移除业务`);
    updateTopologyData();
  }
};

// 添加防抖的业务路径高亮
const highlightBusinessPath = (businessId) => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  
  hoverDebounce.value = setTimeout(() => {
    hoveredBusinessId.value = businessId;
  }, 30);
};

// 添加防抖的清除高亮
const clearHighlight = () => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  
  hoverDebounce.value = setTimeout(() => {
    hoveredBusinessId.value = null;
  }, 30);
};

// 缩放功能
const zoomIn = () => {
  const container = topologyContainer.value;
  if (!container) return;
  
  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  zoomAroundPoint(centerX, centerY, 1.2);
};

const zoomOut = () => {
  const container = topologyContainer.value;
  if (!container) return;
  
  const rect = container.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  zoomAroundPoint(centerX, centerY, 0.8);
};

const resetZoom = () => {
  zoomLevel.value = 1;
  panX.value = 0;
  panY.value = 0;
  MessagePlugin.success('已重置视图');
};

// 以指定点为中心的缩放
const zoomAroundPoint = (clientX, clientY, factor) => {
  const oldZoom = zoomLevel.value;
  const newZoom = Math.max(0.5, Math.min(3, zoomLevel.value * factor));
  
  if (oldZoom === newZoom) return;
  
  // 计算缩放后的新偏移量
  const containerX = clientX - panX.value;
  const containerY = clientY - panY.value;
  
  const worldX = containerX / oldZoom;
  const worldY = containerY / oldZoom;
  
  const newContainerX = worldX * newZoom;
  const newContainerY = worldY * newZoom;
  
  panX.value = clientX - newContainerX;
  panY.value = clientY - newContainerY;
  zoomLevel.value = newZoom;
};

// 鼠标滚轮缩放
const handleWheel = (event) => {
  event.preventDefault();
  
  const delta = event.deltaY > 0 ? 0.9 : 1.1;
  const rect = topologyContainer.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  zoomAroundPoint(x, y, delta);
};

// 拖拽功能
const startDrag = (event) => {
  if (event.button !== 0) return; // 只响应左键
  
  isDragging.value = true;
  dragStart.value = {
    x: event.clientX - panX.value,
    y: event.clientY - panY.value
  };
  lastPan.value = { x: panX.value, y: panY.value };
  
  // 设置鼠标样式
  if (topologyContainer.value) {
    topologyContainer.value.style.cursor = 'grabbing';
  }
  
  event.preventDefault();
};

const handleDrag = (event) => {
  if (!isDragging.value) return;
  
  panX.value = event.clientX - dragStart.value.x;
  panY.value = event.clientY - dragStart.value.y;
  
  // 限制边界
  const maxPanX = 200;
  const maxPanY = 200;
  const minPanX = -svgWidth.value * zoomLevel.value + 200;
  const minPanY = -svgHeight.value * zoomLevel.value + 200;
  
  panX.value = Math.max(minPanX, Math.min(maxPanX, panX.value));
  panY.value = Math.max(minPanY, Math.min(maxPanY, panY.value));
  
  event.preventDefault();
};

const stopDrag = () => {
  if (isDragging.value) {
    isDragging.value = false;
    
    // 恢复鼠标样式
    if (topologyContainer.value) {
      topologyContainer.value.style.cursor = 'grab';
    }
  }
};

const selectNode = (node) => {
  selectedNode.value = node;
  MessagePlugin.info(`选中节点: ${node.name}`);
};

const getBusinessById = (businessId) => {
  return businessList.value.find(b => b.id === businessId);
};

const onActiveChange = (highlightRowKeys, ctx) => {
  console.log(highlightRowKeys, ctx);
};

// 节点和链接颜色方法
const getNodeColor = (node) => {
  // 1. 被选中的节点
  if (selectedNode.value?.id === node.id) {
    return '#52c41a';
  }
  
  // 2. 告警节点
  if (node.status === 'alert') {
    return '#ff4d4f';
  }
  
  // 3. 悬停业务路径上的节点
  if (hoveredBusinessId.value) {
    const business = businessList.value.find(b => b.id === hoveredBusinessId.value);
    if (business && business.current_route_str) {
      const pathNodes = parsePathString(business.current_route_str);
      if (pathNodes.includes(node.id)) {
        return '#1890ff';
      }
    }
  }
  
  // 4. 选中的业务路径上的节点
  const isInSelectedBusiness = selectedBusinesses.value.some((business) => {
    if (business.current_route_str) {
      const pathNodes = parsePathString(business.current_route_str);
      return pathNodes.includes(node.id);
    }
    return false;
  });
  
  if (isInSelectedBusiness) {
    return '#91d5ff';
  }
  
  return '#d9d9d9';
};

const getNodeBorderColor = (node) => {
  if (node.status === 'alert') return '#cf1322';
  if (selectedNode.value?.id === node.id) return '#389e0d';
  if (node.businesses && node.businesses.length > 0) return '#1890ff';
  return '#bfbfbf';
};
const getLinkColor = (link) => {
  // 悬停高亮
  if (hoveredBusinessId.value && link.businesses && link.businesses.includes(hoveredBusinessId.value)) {
    return '#ff7a45';
  }
  
  // 业务路径高亮
  if (link.type === 'business' && link.businesses && link.businesses.length > 0) {
    // 多个业务共享路径
    if (link.businesses.length > 1) {
      return '#faad14';
    }
    // 单一业务路径
    return '#52c41a';
  }
  
  // 基础路径使用灰色
  return '#d9d9d9';
};

const getLinkStrokeWidth = (link) => {
  if (hoveredBusinessId.value && link.businesses && link.businesses.includes(hoveredBusinessId.value)) {
    return 4;
  }
  if (link.type === 'business') {
    return 3;
  }
  return 1.5;
};

const parsePathString = (pathStr) => {
  if (!pathStr || typeof pathStr !== 'string') return [];
  
  const nodes = [];
  // 按换行符分割
  const lines = pathStr.split('\n');
  
  lines.forEach(line => {
    if (!line.trim()) return;
    
    // 匹配格式：13.22.1.62(Jabalpur2,[03]-[01])->...
    // 提取括号内的节点名
    const nodeMatches = line.match(/\(([^,]+),/g);
    if (nodeMatches) {
      nodeMatches.forEach(match => {
        const nodeName = match.substring(1, match.length - 1);
        if (nodeName && !nodes.includes(nodeName)) {
          nodes.push(nodeName);
        }
      });
    }
    
    // 也匹配箭头后面的节点名
    const arrowMatches = line.match(/->\([^,]+,\s*([^)]+)\)/g);
    if (arrowMatches) {
      arrowMatches.forEach(match => {
        const nodeMatch = match.match(/,\s*([^)]+)\)/);
        if (nodeMatch && nodeMatch[1] && !nodes.includes(nodeMatch[1])) {
          nodes.push(nodeMatch[1]);
        }
      });
    }
  });

  console.log('解析路径:', pathStr, '=> 节点:', nodes);
  return nodes;
};

const generateBaseTopology = () => {
  // 从实际业务数据中收集所有节点
  const allNodesSet = new Set();
  const allConnections = new Map();
  
  businessList.value.forEach(business => {
    // 解析路径
    const pathStr = business.current_route_str;
    if (pathStr) {
      const nodes = parsePathString(pathStr);
      nodes.forEach(node => allNodesSet.add(node));
      
      // 记录连接关系
      for (let i = 0; i < nodes.length - 1; i++) {
        const source = nodes[i];
        const target = nodes[i + 1];
        const key = `${source}|${target}`;
        if (!allConnections.has(key)) {
          allConnections.set(key, { source, target, weight: 1 });
        } else {
          allConnections.get(key).weight++;
        }
      }
    }
    
    // 添加告警节点（从告警字符串中提取）
    if (business.alarm_str) {
      const alertNode = extractNodeName(business.alarm_str);
      if (alertNode) {
        allNodesSet.add(alertNode);
      }
    }
  });
  
  console.log('收集到的所有节点:', Array.from(allNodesSet));
  console.log('收集到的连接关系:', Array.from(allConnections.values()));
  
  // 如果没有数据，使用默认节点
  if (allNodesSet.size === 0) {
    const defaultNodes = [
      'Jabalpur2', 'Jabalpur1', 'Satna', 'Sidhi', 'Gwalior', 'Shivpuri', 
      'BIORA', 'Bhopal2', 'Bhopal3', 'Indore1', 'Indore2', 'Jhansi', 
      'Chatarpur', 'Sagar', 'Itarsi', 'Raipur3', 'L21_Bareli'
    ];
    defaultNodes.forEach(node => allNodesSet.add(node));
    
    // 添加默认连接
    const defaultConnections = [
      { source: 'Jabalpur2', target: 'Jabalpur1' },
      { source: 'Jabalpur1', target: 'Satna' },
      { source: 'Satna', target: 'Sidhi' },
      { source: 'Gwalior', target: 'Shivpuri' },
      { source: 'Shivpuri', target: 'BIORA' },
      { source: 'BIORA', target: 'Bhopal2' },
      { source: 'Bhopal2', target: 'Bhopal3' },
      { source: 'Bhopal3', target: 'Indore1' },
      { source: 'Indore1', target: 'Indore2' },
      { source: 'Shivpuri', target: 'Jhansi' },
      { source: 'Jhansi', target: 'Chatarpur' },
      { source: 'Chatarpur', target: 'Sagar' },
      { source: 'Sagar', target: 'Bhopal2' }
    ];
    defaultConnections.forEach((conn) => {
      const key = `${conn.source}|${conn.target}`;
      allConnections.set(key, conn);
    });
  }

  // 智能计算节点位置
  const nodePositions = calculateNodePositions(Array.from(allNodesSet), allConnections);

  // 创建节点对象
  topologyNodes.value = Array.from(allNodesSet).map((nodeName) => {
    const position = nodePositions[nodeName] || {
      x: Math.random() * 600 + 50,
      y: Math.random() * 500 + 50
    };

    // 判断是否为告警节点
    let isAlert = false;
    for (const business of businessList.value) {
      const alertNode = extractNodeName(business.alarm_str);
      if (alertNode === nodeName) {
        isAlert = true;
        break;
      }
    }

    return {
      id: nodeName,
      name: nodeName,
      status: isAlert ? 'alert' : 'normal',
      connections: 0,
      businesses: [],
      x: position.x,
      y: position.y,
      radius: 12,
    };
  });

  console.log('节点集信息：', topologyNodes.value);
  // 生成所有基础连接线
  const baseLinks = [];
  allConnections.forEach((conn, key) => {
    const sourceNode = topologyNodes.value.find((n) => n.id === conn.source);
    const targetNode = topologyNodes.value.find((n) => n.id === conn.target);

    if (sourceNode && targetNode) {
      const dx = targetNode.x - sourceNode.x;
      const dy = targetNode.y - sourceNode.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const offset = Math.min(30, dist / 3);
      const controlX = (sourceNode.x + targetNode.x) / 2;
      const controlY = (sourceNode.y + targetNode.y) / 2 - offset;

      baseLinks.push({
        source: conn.source,
        target: conn.target,
        d: `M${sourceNode.x},${sourceNode.y} Q${controlX},${controlY} ${targetNode.x},${targetNode.y}`,
        type: 'base',
        businessId: null,
        businesses: [],
        weight: conn.weight || 1
      });
    }
  });

  console.log('baseLinks连线信息', baseLinks);

  topologyLinks.value = baseLinks;
  console.log('生成的基础链接数:', baseLinks.length);

  // 更新节点连接数
  topologyNodes.value.forEach((node) => {
    node.connections = topologyLinks.value.filter((link) => link.source === node.id || link.target === node.id).length;
  });
};

// 新增：智能计算节点位置（力导向布局）
const calculateNodePositions = (nodes, connections) => {
  const positions = {};
  const spacing = 100;
  const cols = Math.ceil(Math.sqrt(nodes.length));

  // 初始化位置（网格布局）
  nodes.forEach((node, index) => {
    const row = Math.floor(index / cols);
    const col = index % cols;
    positions[node] = {
      x: 100 + col * spacing,
      y: 100 + row * spacing
    };
  });

  // 力导向算法优化位置
  for (let iter = 0; iter < 100; iter++) {
    const forces = {};
    nodes.forEach((node) => {
      forces[node] = { x: 0, y: 0 };
    });

    // 计算排斥力
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i];
        const nodeB = nodes[j];
        const dx = positions[nodeA].x - positions[nodeB].x;
        const dy = positions[nodeA].y - positions[nodeB].y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < 80) {
          const force = 40 / (distance + 1);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;
          forces[nodeA].x += fx;
          forces[nodeA].y += fy;
          forces[nodeB].x -= fx;
          forces[nodeB].y -= fy;
        }
      }
    }

    // 计算吸引力
    connections.forEach((conn) => {
      const nodeA = conn.source;
      const nodeB = conn.target;
      const dx = positions[nodeA].x - positions[nodeB].x;
      const dy = positions[nodeA].y - positions[nodeB].y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance > 100) {
        const force = (distance - 100) * 0.1;
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        forces[nodeA].x -= fx;
        forces[nodeA].y -= fy;
        forces[nodeB].x += fx;
        forces[nodeB].y += fy;
      }
    });
    
    // 应用力
    nodes.forEach(node => {
      positions[node].x += forces[node].x * 0.3;
      positions[node].y += forces[node].y * 0.3;
      // 边界限制
      positions[node].x = Math.max(50, Math.min(750, positions[node].x));
      positions[node].y = Math.max(50, Math.min(550, positions[node].y));
    });
  }
  
  return positions;
};

// 生成拓扑数据
const generateTopologyData = () => {
  generateBaseTopology();
  
  // 如果有选中的业务，更新拓扑图高亮
  if (selectedBusinesses.value.length > 0) {
    updateTopologyData();
  }
};

// 更新拓扑数据
const updateTopologyData = () => {
  console.log('开始更新拓扑图，选中的业务数量:', selectedBusinesses.value.length);
  
  // 重置所有链接为基础状态
  topologyLinks.value.forEach(link => {
    link.type = 'base';
    link.businessId = null;
    link.businesses = [];
  });
  
  // 重置节点业务关联
  topologyNodes.value.forEach((node) => {
    node.businesses = [];
  });
  
  // 处理选中的业务，高亮业务路径
  selectedBusinesses.value.forEach((business) => {
    const pathStr = business.current_route_str;
    console.log('处理业务:', business.id, '路径:', pathStr);
    
    if (!pathStr) {
      console.log('业务没有路径信息');
      return;
    }
    
    const nodes = parsePathString(pathStr);
    console.log('解析出的节点序列:', nodes);
    
    if (nodes.length === 0) {
      console.log('无法解析出节点');
      return;
    }
    
    // 为业务路径中的每个连续节点对创建高亮
    for (let i = 0; i < nodes.length - 1; i++) {
      const source = nodes[i];
      const target = nodes[i + 1];
      
      console.log(`处理连接: ${source} -> ${target}`);
      
      // 查找对应的链接
      let link = topologyLinks.value.find(l => 
        (l.source === source && l.target === target) ||
        (l.source === target && l.target === source)
      );
      
      if (link) {
        console.log(`找到现有链接: ${link.source} -> ${link.target}`);
        // 标记为业务路径
        link.type = 'business';
        if (!link.businesses) link.businesses = [];
        if (!link.businesses.includes(business.id)) {
          link.businesses.push(business.id);
        }
        link.businessId = business.id;
        
        // 更新节点业务关联
        const sourceNode = topologyNodes.value.find(n => n.id === source);
        const targetNode = topologyNodes.value.find(n => n.id === target);
        if (sourceNode && !sourceNode.businesses.includes(business.id)) {
          sourceNode.businesses.push(business.id);
        }
        if (targetNode && !targetNode.businesses.includes(business.id)) {
          targetNode.businesses.push(business.id);
        }
      } else {
        console.log(`未找到链接: ${source} -> ${target}，尝试创建新链接`);
        // 如果链接不存在，创建新的业务链接
        const sourceNode = topologyNodes.value.find(n => n.id === source);
        const targetNode = topologyNodes.value.find(n => n.id === target);
        
        if (sourceNode && targetNode) {
          console.log(`创建新链接: ${source}(${sourceNode.x},${sourceNode.y}) -> ${target}(${targetNode.x},${targetNode.y})`);
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const offset = Math.min(30, dist / 3);
          const controlX = (sourceNode.x + targetNode.x) / 2;
          const controlY = (sourceNode.y + targetNode.y) / 2 - offset;
          
          const newLink = {
            source,
            target,
            d: `M${sourceNode.x},${sourceNode.y} Q${controlX},${controlY} ${targetNode.x},${targetNode.y}`,
            type: 'business',
            businessId: business.id,
            businesses: [business.id],
            weight: 1
          };
          topologyLinks.value.push(newLink);
          
          // 更新节点连接数
          sourceNode.connections++;
          targetNode.connections++;
          if (!sourceNode.businesses.includes(business.id)) sourceNode.businesses.push(business.id);
          if (!targetNode.businesses.includes(business.id)) targetNode.businesses.push(business.id);
        } else {
          console.log(`节点不存在: ${!sourceNode ? source : ''} ${!targetNode ? target : ''}`);
        }
      }
    }
  });
  
  console.log('拓扑图更新完成，当前链接数:', topologyLinks.value.length);
  console.log('业务链接:', topologyLinks.value.filter(l => l.type === 'business'));
};

const parseRouteParams = async () => {
    const cachedProjectName = storage.get(PROJECT_CACHE_KEY);
    
    if (cachedProjectName) {
      // 如果缓存中有项目名称，直接使用
      projectName.value = cachedProjectName;
      console.log('从缓存读取项目名称:', cachedProjectName);
    } else {
      // 如果缓存中没有，则从接口获取第一个项目
      const nameData = await getProjectData();
      if (nameData && nameData.length > 0) {
        projectName.value = nameData[0].project_name;
        // 将获取到的项目名称也存入缓存
        storage.set(PROJECT_CACHE_KEY, projectName.value);
      }
    }
};

// 监听表格选择变化，自动更新拓扑图
watch(selectedRowKeyList, () => {
  updateTopologyData();
});

watch(() => route.query, (newQuery) => {
  if (newQuery.id) {
    parseRouteParams();
  }
}, { deep: true });

watch(projectName, (newValue, oldValue) => {
  if (newValue && newValue !== oldValue) {
    storage.set(PROJECT_CACHE_KEY, newValue);
    console.log('项目名称已更新缓存:', newValue);
  }
});

// 组件卸载前清理防抖定时器
onBeforeUnmount(() => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
});

// 初始化
onMounted(async () => {
  await parseRouteParams();
  // 设置默认时间范围为最近7天
  setTimeRange('last365days');
  await getAlarmTable(projectName.value, 1, pagination.defaultCurrent, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  // 生成拓扑数据
  generateTopologyData();
  
  // 设置初始鼠标样式
  if (topologyContainer.value) {
    topologyContainer.value.style.cursor = 'grab';
  }
});
</script>

<style scoped>
.channel-alert-analysis {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  min-height: 100vh;
}

.time-selection-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.time-range-selector {
  margin-bottom: 24px;
}

.time-range-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preset-buttons {
  display: flex;
  gap: 8px;
}

.time-range-picker {
  display: flex;
  align-items: flex-end;
  gap: 20px;
}

.time-range-picker :deep(.t-range-input) {
  min-width: 300px;
}

.time-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 200px;
}

.data-statistics {
  margin-left: auto;
  margin-right: 30px;
}

.analysis-results-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 20px;
  color: #1f2d3d;
  margin: 0;
}

.section-header-project {
  width: 300px;
  margin-bottom: 20px;
}

.section-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.results-table-container {
  overflow-x: auto;
}

.alert-time-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert-date {
  font-size: 12px;
  color: #1f2d3d;
}

.alert-time {
  font-size: 12px;
  color: #5e6d82;
}

.time-cell {
  font-size: 13px;
  color: #1f2d3d;
}

.date-cell {
  font-size: 13px;
  color: #1f2d3d;
}

.operation-buttons {
  display: flex;
  gap: 8px;
}

.alert-node-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-name {
  font-size: 13px;
  color: #1f2d3d;
}

.node-id {
  font-size: 11px;
  color: #5e6d82;
}

.path-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.path-text {
  font-size: 13px;
  color: #1f2d3d;
  word-break: break-all;
}

.source-port {
  font-size: 11px;
  color: #6c757d;
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 3px;
  border-left: 3px solid #0052d9;
}

/* 拓扑图区域 */
.topology-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.topology-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topology-container {
  display: grid;
  grid-template-columns: 200px 1fr 250px;
  gap: 16px;
  height: 600px;
  margin-bottom: 16px;
}

/* 左侧图例 */
.topology-legend {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 16px;
  background: #f8f9fa;
  overflow-y: auto;
}

.legend-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #dee2e6;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.legend-color.normal-node {
  background: #91d5ff;
  border: 2px solid #1890ff;
}

.legend-color.alert-node {
  background: #ff4d4f;
  border: 2px solid #cf1322;
}

.legend-line {
  width: 40px;
  height: 2px;
}

.legend-line.normal-path {
  background: #ccc;
}

.legend-line.selected-path {
  background: #1890ff;
}

.selected-business-list {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #dee2e6;
}

.list-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2d3d;
  margin-bottom: 12px;
}

.business-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.business-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.business-item:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.business-item.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.business-info {
  flex: 1;
  min-width: 0;
}

.business-id {
  font-size: 12px;
  color: #1f2d3d;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.business-path {
  font-size: 11px;
  color: #6c757d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 中间拓扑图 */
.topology-canvas {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
  background: #f8f9fa;
  position: relative;
  cursor: grab;
  user-select: none;
  touch-action: none;
}

.topology-canvas:active {
  cursor: grabbing;
}

/* 网格背景 */
.topology-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 2000px;
  height: 2000px;
  background-position: 0 0;
  transition: transform 0.1s ease;
  pointer-events: none;
}

/* SVG容器 */
.topology-svg-container {
  position: absolute;
  top: 0;
  left: 0;
  transition: transform 0.1s ease;
  will-change: transform;
}

/* 视图指示器 */
.viewport-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10;
  pointer-events: none;
}

.indicator-text {
  white-space: nowrap;
}

/* SVG */
.topology-svg {
  cursor: pointer;
}

.node-group {
  cursor: pointer;
  transition: filter 0.2s;
}

.node-group:hover circle {
  filter: drop-shadow(0 0 4px rgba(24, 144, 255, 0.5));
}

.node {
  transition: all 0.3s;
}

.node.normal {
  stroke: #1890ff;
}

.node.alert {
  stroke: #cf1322;
  stroke-width: 3;
}

.node-label {
  font-weight: 500;
  text-anchor: middle;
  pointer-events: none;
  user-select: none;
  transition: font-weight 0.2s;
}

.node-group:hover .node-label {
  font-weight: bold;
}

.link {
  transition: all 0.3s;
  stroke-linecap: round;
}

.link:hover {
  stroke-width: 3;
}

/* 右侧节点信息 */
.node-info-panel {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 16px;
  background: #f8f9fa;
  overflow-y: auto;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #dee2e6;
}

.node-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: #6c757d;
}

.detail-value {
  font-size: 14px;
  color: #1f2d3d;
  font-weight: 500;
}

.business-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.business-tag {
  font-size: 11px;
  color: #666;
  background: white;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #dee2e6;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.business-tag.more {
  background: #f0f0f0;
  color: #999;
}

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #6c757d;
  text-align: center;
}

.no-selection p {
  margin-top: 12px;
  font-size: 14px;
}

/* 拓扑图状态栏 */
.topology-status-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-label {
  color: #6c757d;
}

.status-value {
  color: #1f2d3d;
  font-weight: 500;
}

/* 详情弹窗样式 */
.detail-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 8px;
}

.detail-dialog-content h3 {
  font-size: 18px;
  color: #1f2d3d;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #dee2e6;
}

.business-info-section {
  margin-bottom: 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.info-label {
  font-weight: 500;
  color: #5e6d82;
  min-width: 80px;
}

.info-value {
  color: #1f2d3d;
  word-break: break-all;
}

.path-info-section {
  margin-bottom: 24px;
}

.path-display {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.path-nodes {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.path-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  font-size: 14px;
}

.path-node.alert-node {
  background: #fff2f0;
  border-color: #ffccc7;
  color: #cf1322;
}

.path-arrow {
  color: #5e6d82;
  font-weight: bold;
}

.source-port-info {
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 4px solid #0052d9;
}

.port-label {
  font-weight: 500;
  color: #5e6d82;
}

.port-value {
  color: #1f2d3d;
}

.action-history-section {
  margin-bottom: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #dee2e6;
}

/* 自定义滚动条 */
.detail-dialog-content::-webkit-scrollbar,
.topology-legend::-webkit-scrollbar,
.business-items::-webkit-scrollbar,
.node-info-panel::-webkit-scrollbar {
  width: 6px;
}

.detail-dialog-content::-webkit-scrollbar-track,
.topology-legend::-webkit-scrollbar-track,
.business-items::-webkit-scrollbar-track,
.node-info-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.detail-dialog-content::-webkit-scrollbar-thumb,
.topology-legend::-webkit-scrollbar-thumb,
.business-items::-webkit-scrollbar-thumb,
.node-info-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.detail-dialog-content::-webkit-scrollbar-thumb:hover,
.topology-legend::-webkit-scrollbar-thumb:hover,
.business-items::-webkit-scrollbar-thumb:hover,
.node-info-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .topology-container {
    grid-template-columns: 180px 1fr 200px;
  }
  
  .topology-status-bar {
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .topology-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 400px auto;
    height: auto;
  }
  
  .topology-legend,
  .node-info-panel {
    max-height: 200px;
  }
  
  .topology-status-bar {
    flex-direction: column;
    gap: 8px;
  }
  
  .status-item {
    width: 100%;
    justify-content: space-between;
  }
}

/* 缩放提示 */
.zoom-hint {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10;
  pointer-events: none;
}

/* 数据统计弹窗样式 */
.statistics-dialog-content {
  padding: 8px 0;
  max-height: 400px;
}

.success-rate {
  font-size: 18px;
  font-weight: bold;
  color: #2ba471;
}

.rate-detail {
  font-size: 12px;
  color: #8a99a9;
  margin-right: 8px;
}

.stat-section {
  margin-top: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12px;
  padding-left: 12px;
  border-left: 4px solid #0052d9;
}

.category-item,
.detail-item {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.category-item .percentage,
.detail-item .percentage {
  font-weight: 600;
  color: #0052d9;
  min-width: 45px;
}

.category-item .count,
.detail-item .count {
  font-size: 12px;
  color: #8a99a9;
  min-width: 70px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .category-item,
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .category-item .t-progress,
  .detail-item .t-progress {
    width: 100% !important;
  }
}
</style>