<template>
  <div class="channel-alert-analysis">
    <!-- 时间选择区域 -->
    <div class="time-selection-section">
      <div class="time-range-selector">
        <div class="section-header-project">
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
              确定
            </t-button>
          </div>
        </div>
      </div>

      <div class="analysis-results-section">
        <div class="section-header">
          <h2>受通道告警影响的业务列表</h2>
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
            row-key="id"
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
            <template #alarm_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.alarm_time, 'full') }}
              </div>
            </template>
            
            <template #start_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.start_time, 'full') }}
              </div>
            </template>
            
            <template #end_time="{ row }">
              <div class="time-cell">
                {{ formatDate(row.end_time, 'full') }}
              </div>
            </template>
            
            <template #businessDate="{ row }">
              <div class="date-cell">
                {{ formatDate(row.businessDate, 'slash') }}
              </div>
            </template>
            
            <template #operation="{ row }">
              <div class="operation-buttons">
                <t-button 
                  theme="primary" 
                  variant="text" 
                  size="small"
                  @click="handleAnalyzeBusiness(row)"
                >
                  分析
                </t-button>
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
            
            <template #alertNode="{ row }">
              <div class="alert-node-cell">
                <span class="node-name">{{ row.alertNode }}</span>
                <span class="node-id">({{ row.nodeId }})</span>
              </div>
            </template>
            
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
    
    <!-- 拓扑图区域 -->
    <div class="topology-section">
      <div class="section-header">
        <h2>业务拓扑图展示</h2>
        <div class="topology-controls">
          <t-button variant="outline" size="small" @click="zoomIn">
            <template #icon><t-icon name="zoom-in" /></template>
            放大
          </t-button>
          <t-button variant="outline" size="small" @click="zoomOut">
            <template #icon><t-icon name="zoom-out" /></template>
            缩小
          </t-button>
          <t-button variant="outline" size="small" @click="resetZoom">
            <template #icon><t-icon name="fullscreen" /></template>
            重置
          </t-button>
          <t-tag :theme="isDragging ? 'primary' : 'default'">
            {{ isDragging ? '拖拽中...' : '点击拖拽移动视图' }}
          </t-tag>
        </div>
      </div>
      
      <div class="topology-container">
        <!-- 左侧图例 -->
        <div class="topology-legend">
          <div class="legend-title">图例</div>
          <div class="legend-items">
            <div class="legend-item">
              <div class="legend-color normal-node"></div>
              <span>正常节点</span>
            </div>
            <div class="legend-item">
              <div class="legend-color alert-node"></div>
              <span>告警节点</span>
            </div>
            <div class="legend-item">
              <div class="legend-line normal-path"></div>
              <span>正常路径</span>
            </div>
            <div class="legend-item">
              <div class="legend-line selected-path"></div>
              <span>选中路径</span>
            </div>
            <div class="legend-item">
              <div class="legend-line selected-share-path"></div>
              <span>共享路径</span>
            </div>
          </div>
          
          <div class="selected-business-list">
            <div class="list-title">已选中的业务路径：</div>
            <div class="business-items">
              <div 
                v-for="business in selectedBusinesses" 
                :key="business.id"
                class="business-item"
                :class="{ active: hoveredBusinessId === business.id }"
                @mouseenter="highlightBusinessPath(business.id)"
                @mouseleave="clearHighlight"
              >
                <div class="business-info">
                  <div class="business-id">{{ business.businessId }}</div>
                  <div class="business-path">{{ getPathPreview(business.affectedPath) }}</div>
                </div>
                <t-button 
                  variant="text" 
                  size="small" 
                  @click.stop="removeBusinessFromTopology(business.id)"
                >
                  <template #icon><t-icon name="close" /></template>
                </t-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 中间拓扑图 -->
        <div 
          class="topology-canvas" 
          ref="topologyContainer"
          @wheel="handleWheel"
          @mousedown="startDrag"
          @mousemove="handleDrag"
          @mouseup="stopDrag"
          @mouseleave="stopDrag"
        >
          <div 
            class="topology-svg-container" 
            :style="{
              transform: `translate(${panX}px, ${panY}px) scale(${zoomLevel})`,
              transformOrigin: '0 0'
            }"
          >
            <svg class="topology-svg" :width="svgWidth" :height="svgHeight">
              <!-- 路径连接线 -->
              <g class="links">
                <path 
                  v-for="(link, index) in topologyLinks" 
                  :key="`link-${index}`"
                  :d="link.d"
                  :class="['link', link.type]"
                  :stroke="getLinkColor(link)"
                  :stroke-width="getLinkStrokeWidth(link)"
                  :stroke-dasharray="link.type === 'affected' ? '5,5' : 'none'"
                  fill="none"
                  :marker-end="link.type === 'business' ? 'url(#arrowHighlight)' : 'url(#arrow)'"
                />
              </g>
              
              <!-- 节点 -->
              <g class="nodes">
                <g 
                  v-for="node in topologyNodes" 
                  :key="node.id"
                  :transform="`translate(${node.x},${node.y})`"
                  class="node-group"
                  @click="selectNode(node)"
                >
                  <circle 
                    :r="node.radius"
                    :class="['node', node.status]"
                    :fill="getNodeColor(node)"
                    :stroke="getNodeBorderColor(node)"
                    :stroke-width="2"
                  />
                  <text 
                    class="node-label" 
                    text-anchor="middle" 
                    dy="20"
                    :fill="node.status === 'alert' ? '#cf1322' : '#1890ff'"
                    :style="{ fontSize: `${12 / zoomLevel}px` }"
                  >
                    {{ node.name }}
                  </text>
                  <!-- IP地址显示 -->
                  <text 
                    v-if="node.ip"
                    class="node-ip-label" 
                    text-anchor="middle" 
                    dy="34"
                    :fill="'#888'"
                    :style="{ fontSize: `${10 / zoomLevel}px` }"
                  >
                    ({{ node.ip }})
                  </text>
                </g>
              </g>
              
              <!-- 箭头标记定义 -->
              <defs>
                <marker 
                  id="arrow" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#d9d9d9" />
                </marker>
                <marker 
                  id="arrowHighlight" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#52c41a" />
                </marker>
              </defs>
            </svg>
          </div>
          
          <div class="viewport-indicator" v-if="zoomLevel > 1 || panX !== 0 || panY !== 0">
            <div class="indicator-text">
              视图位置: {{ Math.round(panX) }}, {{ Math.round(panY) }}
            </div>
          </div>
        </div>
        
        <!-- 右侧节点信息 -->
        <div class="node-info-panel">
          <div class="panel-title">节点信息</div>
          <div v-if="selectedNode" class="node-details">
            <div class="detail-item">
              <span class="detail-label">节点名称：</span>
              <span class="detail-value">{{ selectedNode.name }}</span>
            </div>
            <div v-if="selectedNode.ip" class="detail-item">
              <span class="detail-label">IP地址：</span>
              <span class="detail-value">{{ selectedNode.ip }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">节点ID：</span>
              <span class="detail-value">{{ selectedNode.id }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">状态：</span>
              <t-tag 
                :theme="selectedNode.status === 'normal' ? 'success' : 'danger'" 
                size="small"
              >
                {{ selectedNode.status === 'normal' ? '正常' : '告警' }}
              </t-tag>
            </div>
            <div class="detail-item">
              <span class="detail-label">连接数：</span>
              <span class="detail-value">{{ selectedNode.connections }}</span>
            </div>
            <div v-if="selectedNode.connectionDetails && selectedNode.connectionDetails.length > 0" class="detail-item">
              <span class="detail-label">连接节点：</span>
              <div class="connection-list">
                <div 
                  v-for="(conn, index) in selectedNode.connectionDetails.slice(0, 5)" 
                  :key="index"
                  class="connection-item"
                >
                  <span class="connection-direction" :class="conn.direction">
                    {{ conn.direction === 'out' ? '→' : '←' }}
                  </span>
                  <span class="connection-name">{{ conn.nodeName }}</span>
                  <span class="connection-interface">[{{ conn.interfaces }}]</span>
                </div>
                <div v-if="selectedNode.connectionDetails.length > 5" class="connection-item more">
                  +{{ selectedNode.connectionDetails.length - 5 }} 更多连接
                </div>
              </div>
            </div>
            <div v-if="selectedNode.businesses && selectedNode.businesses.length > 0" class="detail-item">
              <span class="detail-label">影响业务：</span>
              <div class="business-list">
                <div 
                  v-for="businessId in selectedNode.businesses.slice(0, 3)" 
                  :key="businessId"
                  class="business-tag"
                >
                  {{ getBusinessById(businessId)?.businessId || businessId }}
                </div>
                <div v-if="selectedNode.businesses.length > 3" class="business-tag more">
                  +{{ selectedNode.businesses.length - 3 }}更多
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-selection">
            <t-icon name="info-circle" size="large" />
            <p>点击拓扑图中的节点查看详情</p>
          </div>
        </div>
      </div>
      
      <!-- 拓扑图状态栏 -->
      <div class="topology-status-bar">
        <div class="status-item">
          <span class="status-label">总节点数：</span>
          <span class="status-value">{{ topologyNodes.length }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">总链路数：</span>
          <span class="status-value">{{ topologyLinks.length }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">告警节点数：</span>
          <span class="status-value">{{ alarmNodeCount }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">显示路径数：</span>
          <span class="status-value">{{ selectedBusinesses.length }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">缩放比例：</span>
          <span class="status-value">{{ Math.round(zoomLevel * 100) }}%</span>
        </div>
        <div class="status-item">
          <span class="status-label">视图位置：</span>
          <span class="status-value">{{ Math.round(panX) }}, {{ Math.round(panY) }}</span>
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
          </div>
        </div>
        
        <div class="path-info-section">
          <h3>受影响路径</h3>
          <div class="path-display">
            <div class="path-nodes">
              <span 
                v-for="(node, index) in getPathNodesFromOmsDict(selectedBusiness.oms_dict_list)" 
                :key="index"
                :class="['path-node', { 'alert-node': isAlertNode(node.name) }]"
              >
                {{ node.name }}
                <span v-if="index < getPathNodesFromOmsDict(selectedBusiness.oms_dict_list).length - 1" class="path-arrow">→</span>
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
  </div>
</template>

<script setup lang="jsx">
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { 
  MessagePlugin
} from 'tdesign-vue-next';
import dayjs from 'dayjs';
import { Utils } from "@/utils/utils";
import { getAlarmList, getProjectList, topologyDataList } from "@/api/analysis";
import { useRoute } from 'vue-router';
import * as XLSX from 'xlsx';
import { storage } from "@/utils/storage";
// 状态管理
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
const svgWidth = ref(1200);
const svgHeight = ref(800);

// 防抖相关
const hoverDebounce = ref(null);

// 拓扑图数据
const topologyNodes = ref([]);
const topologyLinks = ref([]);

// 容器引用
const topologyContainer = ref(null);

const projectName = ref(null);
const PROJECT_CACHE_KEY = 'selected_project_name';
// 表格列定义
const columns = [
  {
    colKey: 'row-select',
    type: 'multiple',
    width: 70,
  },
  {
    title: '告警时间',
    colKey: 'alarm_time',
    width: 200,
    cell: 'alarm_time',
  },
  {
    title: '告警详情',
    colKey: 'alarm_str',
    width: 350,
    cell: 'alarm_str',
  },
  {
    title: '时间',
    colKey: 'time_range',
    width: 250,
    cell: (h, { row }) => {
      return h('div', { 
          style: 'white-space: pre-line; line-height: 1.5;'
        }, `开始时间：${row.start_time} \n 结束时间：${row.end_time}`);
    },
  },
  {
    title: '业务ID',
    colKey: 'call_id',
    width: 220,
    ellipsis: true,
  },
  {
    title: '波长',
    colKey: 'current_wave_str',
    width: 100,
  },
  {
    title: '连接属性',
    colKey: 'current_conn_attr',
    width: 150,
  },
  {
    title: '受影响路径',
    colKey: 'current_route_str',
    minWidth: 400,
    ellipsis: {
      props: {
        theme: 'light',
        placement: 'bottom-right',
      },
      content: (h, { row }) => (
        <div style={{
          maxWidth: '700px',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          wordWrap: 'break-word',
          maxHeight: '300px',
          overflowY: 'auto',
          padding: '8px',
          scrollbarWidth: 'thin',
          scrollbarColor: '#c1c1c1 #f1f1f1'
        }}>
          {row?.current_route_str || ''}
        </div>
      ),
    }
  },
  {
    title: '动作结果',
    colKey: 'result',
    width: 150,
    cell: (h, { row }) => {
      return row.result ? '成功' : '失败';
    },
  },
  {
    title: '失败原因',
    colKey: 'fail_reason',
    width: 200,
    ellipsis: { theme: 'light', placement: 'bottom' },
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

const formatTimeRange = (range) => {
  if (!range || !Array.isArray(range)) return [];
  return range.map(formatDateTime);
};

const handleProjectNameChange = (newValue) => {
  if (newValue) {
    // 当项目名称变化时，保存到缓存
    storage.set(PROJECT_CACHE_KEY, newValue);
    console.log('项目名称已缓存:', newValue);
  }
};

const formattedTimeRange = computed(() => formatTimeRange(timeRange.value));

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

const businessList = ref([]);

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
    return projectInfo;
  } catch (error) {
    MessagePlugin.error('获取项目列表失败，请重试');
    return [];
  }
};

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

/**
 * 解析 oms_dict_list 中的 label 字段
 * 支持两种格式:
 * 1. "13.22.9.54(Dhamnod,[01-02])->([04-01],Indore2)13.22.1.14"
 * 2. "(OEP:[02-13])13.22.1.22(Bhopal2,[03-13])->([01-03],Itarsi)13.22.1.94"
 * 
 * 返回: { sourceId: '13.22.9.54', sourceName: 'Dhamnod', targetId: '13.22.1.14', targetName: 'Indore2', ports: { source: '[01-02]', target: '[04-01]' }, hasRelay: false }
 */
const parseOmsLabel = (label) => {
  if (!label || typeof label !== 'string') return null;
  
  // 匹配格式1: IP(名称,[端口])->([端口],名称)IP
  const regex1 = /^([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^)]+)\)([\d.]+)$/;
  const match1 = label.match(regex1);
  
  if (match1) {
    const [, sourceId, sourceName, sourcePort, targetPort, targetName, targetId] = match1;
    return {
      sourceId: sourceId,
      sourceName: sourceName,
      targetId: targetId,
      targetName: targetName,
      ports: {
        source: sourcePort,
        target: targetPort
      },
      hasRelay: false,
      relayInfo: null
    };
  }
  
  // 匹配格式2: (OEP:[端口])IP1(名称1,[端口1])->([端口2],名称2)IP2
  const regex2 = /^\(OEP:(\[[^\]]+\])\)([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^)]+)\)([\d.]+)$/;
  const match2 = label.match(regex2);
  
  if (match2) {
    const [, oepPort, sourceId, sourceName, sourcePort, targetPort, targetName, targetId] = match2;
    return {
      sourceId: sourceId,
      sourceName: sourceName,
      targetId: targetId,
      targetName: targetName,
      ports: {
        source: sourcePort,
        target: targetPort
      },
      hasRelay: true,
      relayInfo: {
        type: 'OEP',
        port: oepPort,
        beforeSource: true
      }
    };
  }
  
  // 匹配格式3: IP1(名称1,[端口1])->([端口2],名称2)IP2(OEP:[端口]) 【修改后】
  const regex3 = /^([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^)]+)\)([\d.]+)\(OEP:(\[[^\]]+\])\)$/;
  const match3 = label.match(regex3);
  
  if (match3) {
    const [, sourceId, sourceName, sourcePort, targetPort, targetName, targetId, oepPort] = match3;
    return {
      sourceId: sourceId,
      sourceName: sourceName,
      targetId: targetId,
      targetName: targetName,
      ports: {
        source: sourcePort,
        target: targetPort
      },
      hasRelay: true,
      relayInfo: {
        type: 'OEP',
        port: oepPort,
        afterTarget: true
      }
    };
  }

  // 匹配格式4: IP1(名称1,[端口1])->([端口2],名称2(附加信息))IP2
  const regex4 = /^([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^(]+)\(([^)]+)\)\)([\d.]+)$/;
  const match4 = label.match(regex4);
  
  if (match4) {
    const [, sourceId, sourceName, sourcePort, targetPort, targetName, targetSuffix, targetId] = match4;
    return {
      sourceId: sourceId,
      sourceName: sourceName,
      targetId: targetId,
      targetName: `${targetName}(${targetSuffix})`,
      ports: {
        source: sourcePort,
        target: targetPort
      },
      hasRelay: false,
      relayInfo: null
    };
  }

  const regex5 = /^([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^)]+)\)([\d.]+)\(OEP:(\[[^\]]+\])\)$/;
  const match5 = label.match(regex5);
  if (match5) {
    const [, sourceId, sourceName, sourcePort, targetPort, targetName, targetId, oepPort] = match5;
    return {
      sourceId: sourceId,
      sourceName: sourceName,
      targetId: targetId,
      targetName: targetName,
      ports: { source: sourcePort, target: targetPort },
      hasRelay: true,
      relayInfo: {
        type: 'OEP',
        port: oepPort,
        afterTarget: true   // OEP 在目标IP之后
      }
    };
  }

  console.warn('无法解析OMS label:', label);
  return null;
};

/**
 * 从 oms_dict_list 中提取所有节点名称（用于路径展示）
 */
const getPathNodesFromOmsDict = (omsDictList) => {
  if (!omsDictList || !Array.isArray(omsDictList)) return [];
  
  const nodes = [];
  
  omsDictList.forEach((item, index) => {
    const parsed = parseOmsLabel(item.label);
    if (parsed) {
      if (index === 0) {
        nodes.push({ name: parsed.sourceName, id: parsed.sourceId });
        // 如果有前置中继点，也加入
        if (parsed.hasRelay && parsed.relayInfo?.beforeSource) {
          nodes.push({ name: `OEP:${parsed.relayInfo.port}`, id: `OEP_${index}` });
        }
      }
      nodes.push({ name: parsed.targetName, id: parsed.targetId });
      // 如果有后置中继点，也加入
      if (parsed.hasRelay && parsed.relayInfo?.afterTarget) {
        nodes.push({ name: `OEP:${parsed.relayInfo.port}`, id: `OEP_${index}_after` });
      }
    }
  });
  
  return nodes;
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
    const response = await getAlarmList(params);
    businessList.value = response.data.map((item, index) => ({
      ...item,
      id: item.alarm_id || `business_${index}_${Date.now()}_${Math.random()}`,
      businessId: item.call_id,
      wavelength: item.current_wave_str,
      property: item.current_conn_attr,
      affectedPath: item.current_route_str,
      alertNode: extractNodeName(item.alarm_str),
      nodeId: item.node_id,
      sourcePort: extractSourcePort(item.alarm_str),
      oms_dict_list: typeof item.oms_dict_list === 'string' 
        ? (() => { try { return JSON.parse(item.oms_dict_list); } catch(e) { return []; } })() 
        : (item.oms_dict_list || [])
    }));
    pagination.total = response.total;
    
    console.log('业务数据加载完成:', businessList.value);
  } catch (error) {
    console.error('获取业务列表失败:', error);
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
  // 匹配模式: "HOV-OCCURED-13.22.1.182(Gwalior,[03-08])-SF"
  const match = alarmStr.match(/\(([^,]+),/);
  return match ? match[1] : '';
};

const extractNodeId = (alarmStr) => {
  if (!alarmStr) return '';
  // 匹配模式: "HOV-OCCURED-13.22.1.182(Gwalior,[03-08])-SF"
  // 提取IP地址格式的ID
  const match = alarmStr.match(/(\d+\.\d+\.\d+\.\d+)\(/);
  return match ? match[1] : '';
};

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
};

const handleAnalyze = async () => {
  if (!timeRange.value || timeRange.value.length !== 2) {
    MessagePlugin.warning('请先选择时间范围');
    return;
  }

  if (!projectName.value) {
    MessagePlugin.warning('请先选择项目');
    return;
  }

  await getAlarmTable(projectName.value, 1, 1, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  
  const topologyData = await getNodeDataList(projectName.value);
  if (topologyData) {
    setTimeout(() => {
      generateTopologyData(topologyData);
    }, 500);
  }
};

const handleSelectChange = (selectedRowKeys) => {
  selectedRowKeyList.value = selectedRowKeys;
  console.log('selectedRowKeys', selectedRowKeys);
  if (topologyNodes.value.length > 0) {
    updateTopologyData();
  }
};

const handleAnalyzeBusiness = (row) => {
  MessagePlugin.info(`正在跳转到业务分析页面: ${row.businessId}`);

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
  window.open(`${baseUrl}/quality/logAnalysis/businessAnalysis?${params}`, '_blank');
};

const handleViewDetails = (row) => {
  MessagePlugin.info(`正在跳转到告警分析页面: ${row.businessId}`);

  const params = new URLSearchParams({
    project_name: projectName.value,
    businessId: row.businessId,
    alarm_id: row.alarm_id,
    alarm_time: row.alarm_time,
    alertNode: row.alertNode,
    nodeId: row.nodeId,
    start_time: row.start_time,
    end_time: row.end_time,
    wavelength: row.wavelength,
    property: row.property,
    affectedPath: row.affectedPath,
    sourcePort: row.sourcePort || '',
    businessDate: row.businessDate,
    alertId: `alert_${row.id}_${Date.now()}`,
    alertType: 'channel_alert'
  }).toString();
  
  const baseUrl = Utils.getBaseUrl();
  window.open(`${baseUrl}/quality/logAnalysis/alarmAnalysis?${params}`, '_blank');
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
    const tableData = await exportAlarmTable(projectName.value, 0, pagination.defaultCurrent, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
    
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
    XLSX.utils.book_append_sheet(workbook, worksheet, '受通道告警影响的业务数据')

    const date = new Date()
    const formattedDate =
      `${date.getFullYear().toString().slice(2)}` +
      `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
      `${date.getDate().toString().padStart(2, '0')}` +
      `${date.getHours().toString().padStart(2, '0')}` +
      `${date.getMinutes().toString().padStart(2, '0')}`
    const fileName = `受通道告警影响的业务列表_${formattedDate}.xlsx`

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
  if (!path || typeof path !== 'string') return '无路径信息';
  const nodes = path.split('-');
  if (nodes.length <= 3) return path;
  return `${nodes[0]}-...-${nodes[nodes.length - 1]}`;
};

const removeBusinessFromTopology = (businessId) => {
  const index = selectedRowKeyList.value.indexOf(businessId);
  if (index !== -1) {
    selectedRowKeyList.value.splice(index, 1);
    MessagePlugin.info(`已从拓扑图上移除业务`);
    updateTopologyData();
  }
};

const highlightBusinessPath = (businessId) => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  hoverDebounce.value = setTimeout(() => {
    hoveredBusinessId.value = businessId;
  }, 30);
};

const clearHighlight = () => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  hoverDebounce.value = setTimeout(() => {
    hoveredBusinessId.value = null;
  }, 30);
};

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

const zoomAroundPoint = (clientX, clientY, factor) => {
  const oldZoom = zoomLevel.value;
  const newZoom = Math.max(0.5, Math.min(3, zoomLevel.value * factor));
  if (oldZoom === newZoom) return;

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

const handleWheel = (event) => {
  event.preventDefault();
  const delta = event.deltaY > 0 ? 0.9 : 1.1;
  const rect = topologyContainer.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  zoomAroundPoint(x, y, delta);
};

const startDrag = (event) => {
  if (event.button !== 0) return;
  isDragging.value = true;
  dragStart.value = {
    x: event.clientX - panX.value,
    y: event.clientY - panY.value
  };
  lastPan.value = { x: panX.value, y: panY.value };
  if (topologyContainer.value) {
    topologyContainer.value.style.cursor = 'grabbing';
  }
  event.preventDefault();
};

const handleDrag = (event) => {
  if (!isDragging.value) return;
  panX.value = event.clientX - dragStart.value.x;
  panY.value = event.clientY - dragStart.value.y;
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
    if (topologyContainer.value) {
      topologyContainer.value.style.cursor = 'grab';
    }
  }
};

const selectNode = (node) => {
  const connectionDetails = topologyLinks.value
    .filter(link => link.sourceId === node.id || link.targetId === node.id)
    .map(link => {
      if (link.sourceId === node.id) {
        return { 
          direction: 'out', 
          nodeName: link.targetName, 
          nodeId: link.targetId, 
          interfaces: link.localIfIndex 
        };
      } else {
        return { 
          direction: 'in', 
          nodeName: link.sourceName, 
          nodeId: link.sourceId, 
          interfaces: link.remoteIfIndex 
        };
      }
    });

  selectedNode.value = {
    ...node,
    connections: connectionDetails.length,
    connectionDetails: connectionDetails
  };

  // 如果选中的是告警节点，显示告警信息
  if (node.status === 'alert') {
    MessagePlugin.warning(`告警节点: ${node.name}，该节点存在通道告警`);
  } else {
    MessagePlugin.info(`选中节点: ${node.name}`);
  }
};

const getBusinessById = (businessId) => {
  return businessList.value.find(b => b.id === businessId);
};

const onActiveChange = (highlightRowKeys, ctx) => {
  console.log(highlightRowKeys, ctx);
};

const getNodeColor = (node) => {
  if (selectedNode.value?.id === node.id) return '#52c41a';
  if (node.status === 'alert') return '#ff4d4f';

  if (hoveredBusinessId.value) {
    const business = businessList.value.find(b => b.id === hoveredBusinessId.value);
    if (business && business.oms_dict_list && Array.isArray(business.oms_dict_list)) {
      const pathNodes = extractPathNodeNames(business.oms_dict_list);
      if (pathNodes.includes(node.name)) return '#1890ff';
    }
  }

  const isInSelectedBusiness = selectedBusinesses.value.some((business) => {
    if (business.oms_dict_list && Array.isArray(business.oms_dict_list)) {
      const pathNodes = extractPathNodeNames(business.oms_dict_list);
      return pathNodes.includes(node.name);
    }
    return false;
  });

  if (isInSelectedBusiness) return '#91d5ff';
  return '#d9d9d9';
};

const getNodeBorderColor = (node) => {
  if (node.status === 'alert') return '#cf1322';
  if (selectedNode.value?.id === node.id) return '#389e0d';
  if (node.businesses && node.businesses.length > 0) return '#1890ff';
  return '#bfbfbf';
};

const getLinkColor = (link) => {
  if (hoveredBusinessId.value && link.businesses && link.businesses.includes(hoveredBusinessId.value)) {
    return '#ff7a45';
  }
  if (link.type === 'business' && link.businesses && link.businesses.length > 0) {
    if (link.businesses.length > 1) return '#008000';
    return '#52c41a';
  }
  return '#d9d9d9';
};

const getLinkStrokeWidth = (link) => {
  if (hoveredBusinessId.value && link.businesses && link.businesses.includes(hoveredBusinessId.value)) {
    return 4;
  }
  if (link.type === 'business') return 3;
  return 1.5;
};

/**
 * 从 oms_dict_list 中提取节点名称列表
 * 返回: ["Dhamnod", "Indore2", ...]
 */
const extractPathNodeNames = (omsDictList) => {
  if (!omsDictList || !Array.isArray(omsDictList)) return [];
  
  const nodeNames = [];
  
  omsDictList.forEach((item, index) => {
    const parsed = parseOmsLabel(item.label);
    if (parsed) {
      if (index === 0) {
        nodeNames.push(parsed.sourceName);
      }
      nodeNames.push(parsed.targetName);
    }
  });
  
  return nodeNames;
};

/**
 * 从 oms_dict_list 中提取节点IP列表
 * 返回: ["13.22.9.54", "13.22.1.14", ...]
 */
const extractPathNodeIps = (omsDictList) => {
  if (!omsDictList || !Array.isArray(omsDictList)) return [];
  
  const nodeIps = [];
  
  omsDictList.forEach((item, index) => {
    const parsed = parseOmsLabel(item.label);
    if (parsed) {
      if (index === 0) {
        nodeIps.push(parsed.sourceId);
      }
      nodeIps.push(parsed.targetId);
    }
  });
  
  return nodeIps;
};

/**
 * 从 oms_dict_list 中提取所有链接关系
 * 返回: [{ sourceId, sourceName, targetId, targetName, sourcePort, targetPort, hasRelay }, ...]
 */
const extractPathLinks = (omsDictList) => {
  if (!omsDictList || !Array.isArray(omsDictList)) return [];
  
  const links = [];
  
  omsDictList.forEach(item => {
    const parsed = parseOmsLabel(item.label);
    if (parsed) {
      links.push(parsed);
    }
  });
  
  return links;
};

const getNodeDataList = async (name) => {
  try {
    const params = {
      project_name: name,
    };
    const response = await topologyDataList(params);
    console.log('获取到的节点数据:', response);
    return response;
  } catch (error) {
    MessagePlugin.error('获取拓扑数据失败，请重试');
    return null;
  }
};

const generateBaseTopology = (apiData) => {
  console.log('开始生成拓扑图，数据:', apiData);
  
  if (!apiData || !apiData.data || !apiData.data.nodes || apiData.data.nodes.length === 0) {
    console.log('没有可用的拓扑数据');
    topologyNodes.value = [];
    topologyLinks.value = [];
    return;
  }

  const { nodes: apiNodes, links: apiLinks } = apiData.data;

  const calculatePositions = (nodes) => {
    const canvasWidth = svgWidth.value || 1200;
    const canvasHeight = svgHeight.value || 800;
    const margin = 80;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach((node) => {
      minX = Math.min(minX, node.x);
      maxX = Math.max(maxX, node.x);
      minY = Math.min(minY, node.y);
      maxY = Math.max(maxY, node.y);
    });

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    return nodes.map((node) => ({
      ...node,
      canvasX: margin + ((node.x - minX) / rangeX) * (canvasWidth - 2 * margin),
      canvasY: margin + ((node.y - minY) / rangeY) * (canvasHeight - 2 * margin)
    }));
  };

  const positionedNodes = calculatePositions(apiNodes);

  // 创建节点对象，同时记录IP地址信息
  topologyNodes.value = positionedNodes.map((node) => ({
    id: node.id,
    name: node.name,
    ip: node.ip || node.id, // 保存IP地址
    status: node.status || 'normal',
    connections: node.connections || 0,
    x: node.canvasX,
    y: node.canvasY,
    radius: 14,
    businesses: []
  }));

  // 处理连接线数据
  const processedLinks = [];
  const linkMap = new Map();

  apiLinks.forEach((link) => {
    const sourceNode = topologyNodes.value.find(n => n.id === link.localNodeId);
    const targetNode = topologyNodes.value.find(n => n.id === link.remoteNodeId);

    if (!sourceNode || !targetNode) {
      console.log(`节点未找到: source=${link.localNodeId}, target=${link.remoteNodeId}`);
      return;
    }

    const linkKey = `${link.localNodeId}-${link.remoteNodeId}`;
    
    if (!linkMap.has(linkKey)) {
      linkMap.set(linkKey, {
        sourceId: link.localNodeId,
        targetId: link.remoteNodeId,
        sourceName: sourceNode.name,
        targetName: targetNode.name,
        interfaces: [],
        sourceX: sourceNode.x,
        sourceY: sourceNode.y,
        targetX: targetNode.x,
        targetY: targetNode.y
      });
    }
    
    const existingLink = linkMap.get(linkKey);
    existingLink.interfaces.push({
      localIfIndex: link.localIfIndex,
      remoteIfIndex: link.remoteIfIndex
    });
  });

  // 生成SVG路径（单向，从source到target）
  linkMap.forEach((linkData) => {
    const { sourceX, sourceY, targetX, targetY, sourceId, targetId, sourceName, targetName, interfaces } = linkData;
    
    const dx = targetX - sourceX;
    const dy = targetY - sourceY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    
    const interfaceCount = interfaces.length;
    
    interfaces.forEach((iface, index) => {
      const offset = interfaceCount > 1 ? (index - (interfaceCount - 1) / 2) * 15 : 0;
      const midX = (sourceX + targetX) / 2;
      const midY = (sourceY + targetY) / 2;
      
      const controlX = midX + offset * 0.3;
      const controlY = midY - dist * 0.1;
      
      processedLinks.push({
        source: sourceName,
        target: targetName,
        sourceId: sourceId,
        targetId: targetId,
        sourceName: sourceName,
        targetName: targetName,
        // 确保路径从source到target（单向）
        d: `M${sourceX},${sourceY} Q${controlX},${controlY} ${targetX},${targetY}`,
        type: 'base',
        businessId: null,
        businesses: [],
        weight: 1,
        localIfIndex: iface.localIfIndex,
        remoteIfIndex: iface.remoteIfIndex,
        hasArrow: true,
        direction: `${sourceId}->${targetId}`
      });
    });
  });

  topologyLinks.value = processedLinks;
  
  console.log('生成的节点数:', topologyNodes.value.length);
  console.log('生成的链接数:', topologyLinks.value.length);
  console.log('节点列表:', topologyNodes.value.map(n => ({ id: n.id, name: n.name, ip: n.ip })));
  
  // 更新节点连接数
  topologyNodes.value.forEach((node) => {
    node.connections = topologyLinks.value.filter(
      link => link.sourceId === node.id || link.targetId === node.id
    ).length;
  });
};

const generateTopologyData = (apiData) => {
  if (apiData) {
    generateBaseTopology(apiData);
  }
  
  if (selectedBusinesses.value.length > 0) {
    updateTopologyData();
  }
};

/**
 * 优化后的拓扑图更新函数 - 使用 oms_dict_list 绘制业务路径连线
 * 支持通过名称或IP地址匹配节点
 */
/**
 * 优化后的拓扑图更新函数 - 使用 oms_dict_list 绘制业务路径连线
 * 支持通过名称或IP地址匹配节点，支持双向链路匹配，并自动修正箭头方向
 */
const updateTopologyData = () => {
  console.log('开始更新拓扑图，选中的业务数量:', selectedBusinesses.value.length);
  
  // 重置所有链接为基础状态
  topologyLinks.value.forEach(link => {
    link.type = 'base';
    link.businessId = null;
    link.businesses = [];
    // 清除之前可能设置的翻转标记
    delete link.isReversedForBusiness;
  });
  
  // 重置节点业务关联和告警状态
  topologyNodes.value.forEach((node) => {
    node.businesses = [];
    node.status = 'normal';
  });
  
  // 存储需要翻转方向的链接（原始方向与业务方向相反）
  const linksToReverse = [];
  
  // 处理选中的业务，高亮业务路径和标记告警节点
  selectedBusinesses.value.forEach((business) => {
    const omsDictList = business.oms_dict_list;
    console.log('处理业务:', business.id, 'oms_dict_list:', omsDictList);
    
    // 从alarm_str中提取告警节点信息
    const alarmNodeName = extractNodeName(business.alarm_str);
    const alarmNodeId = extractNodeId(business.alarm_str);
    
    // 在拓扑节点中标记告警节点
    if (alarmNodeName || alarmNodeId) {
      const alertNode = topologyNodes.value.find(node => 
        (alarmNodeId && (node.id === alarmNodeId || node.ip === alarmNodeId)) ||
        (alarmNodeName && node.name === alarmNodeName)
      );
      
      if (alertNode) {
        alertNode.status = 'alert';
        console.log('标记告警节点:', alertNode.name, '为红色');
      }
    }
    
    if (!omsDictList || !Array.isArray(omsDictList) || omsDictList.length === 0) {
      console.warn('业务没有 oms_dict_list 数据:', business.id);
      return;
    }
    
    // 提取所有路径链接
    const pathLinks = extractPathLinks(omsDictList);
    console.log('解析出的路径链接:', pathLinks.map(l => ({ 
      source: `${l.sourceName}(${l.sourceId})`, 
      target: `${l.targetName}(${l.targetId})` 
    })));
    
    if (pathLinks.length === 0) return;
    
    // 遍历每个路径链接
    pathLinks.forEach((parsedLink) => {
      const { sourceId, sourceName, targetId, targetName } = parsedLink;
      
      // 在拓扑节点中查找对应的完整节点信息 - 支持多种匹配方式
      let sourceNode = topologyNodes.value.find(n => 
        n.id === sourceId || 
        n.ip === sourceId || 
        n.name === sourceName ||
        n.id === sourceName ||
        n.name === sourceId
      );
      
      let targetNode = topologyNodes.value.find(n => 
        n.id === targetId || 
        n.ip === targetId || 
        n.name === targetName ||
        n.id === targetName ||
        n.name === targetId
      );
      
      if (!sourceNode || !targetNode) {
        console.warn(`节点未找到: source=${sourceName}(${sourceId}), target=${targetName}(${targetId})`);
        console.log('可用节点:', topologyNodes.value.map(n => ({ id: n.id, name: n.name, ip: n.ip })));
        return;
      }
      
      console.log(`业务路径方向: ${sourceNode.name}(${sourceNode.id}) -> ${targetNode.name}(${targetNode.id})`);
      
      // 查找正向链接 (source -> target)
      let links = topologyLinks.value.filter(l => 
        l.sourceId === sourceNode.id && l.targetId === targetNode.id
      );
      
      let isReversed = false;
      
      // 如果找不到正向链接，尝试反向链接 (target -> source)
      if (links.length === 0) {
        links = topologyLinks.value.filter(l => 
          l.sourceId === targetNode.id && l.targetId === sourceNode.id
        );
        if (links.length > 0) {
          isReversed = true;
          console.log(`使用反向链路: ${targetNode.name} -> ${sourceNode.name} (业务方向: ${sourceNode.name} -> ${targetNode.name})`);
        }
      }
      
      if (links.length > 0) {
        links.forEach(link => {
          link.type = 'business';
          if (!link.businesses) link.businesses = [];
          if (!link.businesses.includes(business.id)) {
            link.businesses.push(business.id);
          }
          link.businessId = business.id;
          // 标记是否为反向链路，用于后续修正箭头方向
          link.isReversedForBusiness = isReversed;
          
          // 如果是反向链路，记录需要翻转的链接信息
          if (isReversed && !linksToReverse.some(l => l.link === link)) {
            linksToReverse.push({
              link: link,
              expectedSourceId: sourceNode.id,
              expectedTargetId: targetNode.id,
              expectedSourceName: sourceNode.name,
              expectedTargetName: targetNode.name
            });
          }
        });
        
        // 更新节点业务关联
        if (!sourceNode.businesses.includes(business.id)) {
          sourceNode.businesses.push(business.id);
        }
        if (!targetNode.businesses.includes(business.id)) {
          targetNode.businesses.push(business.id);
        }
      } else {
        console.warn(`未找到链接: ${sourceNode.name}(${sourceNode.id}) <-> ${targetNode.name}(${targetNode.id})`);
      }
    });
  });
  
  // 修正反向链路的箭头方向：重新计算SVG路径，使箭头指向业务路径的正确方向
  linksToReverse.forEach(({ link, expectedSourceId, expectedTargetId, expectedSourceName, expectedTargetName }) => {
    // 获取预期源节点和目标节点
    const sourceNode = topologyNodes.value.find(n => n.id === expectedSourceId);
    const targetNode = topologyNodes.value.find(n => n.id === expectedTargetId);
    
    if (sourceNode && targetNode) {
      // 业务期望的方向是 sourceNode -> targetNode
      // 但link的原始方向是 targetNode -> sourceNode
      // 所以我们需要重新计算路径，使路径从sourceNode指向targetNode
      const dx = targetNode.x - sourceNode.x;
      const dy = targetNode.y - sourceNode.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const midX = (sourceNode.x + targetNode.x) / 2;
      const midY = (sourceNode.y + targetNode.y) / 2;
      
      // 使用贝塞尔曲线，略微弯曲使线条更美观
      const controlX = midX;
      const controlY = midY - dist * 0.1;
      
      // 重新生成路径，方向为 sourceNode -> targetNode（业务期望的方向）
      link.d = `M${sourceNode.x},${sourceNode.y} Q${controlX},${controlY} ${targetNode.x},${targetNode.y}`;
      console.log(`翻转链路方向: 原方向 ${link.sourceName}->${link.targetName}, 新方向 ${expectedSourceName}->${expectedTargetName}`);
      
      // 同时更新链路的source和target信息，保持一致性
      link.sourceId = sourceNode.id;
      link.targetId = targetNode.id;
      link.sourceName = sourceNode.name;
      link.targetName = targetNode.name;
    }
  });
  
  console.log('拓扑图更新完成，告警节点数:', topologyNodes.value.filter(n => n.status === 'alert').length);
  console.log('高亮链接数:', topologyLinks.value.filter(l => l.type === 'business').length);
  console.log('翻转的链接数:', linksToReverse.length);
};

const parseRouteParams = async () => {
  const { id, name } = route.query;
  
  if (name) {
    // 如果路由参数中有 name，优先使用路由参数
    projectName.value = name;
    // 同时更新缓存
    storage.set(PROJECT_CACHE_KEY, name);
  } else {
    // 优先从缓存读取
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
  }
};

// 监听表格选择变化，自动更新拓扑图
watch(selectedRowKeyList, () => {
  if (topologyNodes.value.length > 0) {
    updateTopologyData();
  }
});

watch(() => route.query, (newQuery) => {
  if (newQuery.id) {
    parseRouteParams();
  }
}, { deep: true });

watch(projectName, (newValue, oldValue) => {
  if (newValue && newValue !== oldValue) {
    handleProjectNameChange(newValue);
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
  
  // 设置默认时间范围为最近365天
  setTimeRange('last365days');
  
  // 获取告警数据
  await getAlarmTable(projectName.value, 1, pagination.defaultCurrent, pagination.defaultPageSize, formattedTimeRange.value[0], formattedTimeRange.value[1]);
  
  // 获取拓扑数据
  const topologyData = await getNodeDataList(projectName.value);
  if (topologyData) {
    generateTopologyData(topologyData);
  }
  
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
  background: #52c41a;
}

.legend-line.selected-share-path {
  background: #008000;
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

.topology-svg-container {
  position: absolute;
  top: 0;
  left: 0;
  transition: transform 0.1s ease;
  will-change: transform;
}

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

.node-ip-label {
  font-weight: 400;
  text-anchor: middle;
  pointer-events: none;
  user-select: none;
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

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 4px;
  background: white;
  border-radius: 3px;
  border: 1px solid #dee2e6;
}

.connection-direction {
  font-weight: bold;
  width: 14px;
  text-align: center;
}

.connection-direction.out {
  color: #52c41a;
}

.connection-direction.in {
  color: #1890ff;
}

.connection-name {
  color: #1f2d3d;
  font-weight: 500;
}

.connection-interface {
  color: #6c757d;
  font-size: 11px;
}

.connection-item.more {
  justify-content: center;
  color: #999;
  font-style: italic;
  border-style: dashed;
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
</style>