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
            :default-value="defaultTimeRange"
            format="YYYY-MM-DD HH:mm:ss"
            :enable-time-picker="true"
            :clearable="false"
            allow-input
            @change="handleTimeRangeChange"
          />
          
          <div class="oms-display">
            <t-select 
            v-model="alarmValue" 
            placeholder="请选择要分析的复用段告警" 
            filterable
            :minCollapsedNum="1" 
            :multiple="true" 
            :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
            @popup-visible-change="showSelectOMS">
              <t-option v-for="item in alarmOptions" :key="item.id" :value="item.value" :label="item.label"></t-option>
            </t-select>
          </div>

          <div class="oms-display">
            <t-select 
            v-model="omsValue" 
            placeholder="请选择要筛选的业务" 
            :minCollapsedNum="1" 
            :multiple="true" 
            filterable
            clearable
            disabled
            :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
            :filter="filterMethod"
            :options="omsOptions" />
          </div>

          <div class="time-display">
            <t-button theme="primary" @click="handleAnalyze">
              确定
            </t-button>
          </div>
        </div>
      </div>

      <div class="analysis-results-section">
        <div class="section-header">
          <h2>断纤影响的业务列表</h2>
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
              <div class="legend-line old-path"></div>
              <span>动作前路由</span>
            </div>
            <div class="legend-item">
              <div class="legend-line new-path"></div>
              <span>动作后路由</span>
            </div>
            <div class="legend-item">
              <div class="legend-line shared-path"></div>
              <span>重合路径</span>
            </div>
          </div>
          
          <div class="selected-business-list">
            <div class="list-title">已选中的业务路径：</div>
            <div class="business-items">
              <div 
                v-for="business in selectedBusinesses" 
                :key="business.id"
                class="business-item"
                :class="{ active: hoveredcall_id === business.id }"
                @mouseenter="highlightBusinessPath(business.id)"
                @mouseleave="clearHighlight"
              >
                <div class="business-info">
                  <div class="business-id">{{ business.call_id }}</div>
                  <div class="business-path">{{ getPathPreview(business.current_route_str || business.new_route_str) }}</div>
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
                  :stroke-dasharray="getLinkDashArray(link)"
                  fill="none"
                  :marker-end="getLinkMarker(link)"
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
                <marker 
                  id="arrowOld" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#fa541c" />
                </marker>
                <marker 
                  id="arrowNew" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#1677ff" />
                </marker>
                <marker 
                  id="arrowHover" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#ff7a45" />
                </marker>
                <marker 
                  id="arrowShared" 
                  markerWidth="10" 
                  markerHeight="7" 
                  refX="10" 
                  refY="3.5" 
                  orient="auto"
                >
                  <path d="M0,0 L10,3.5 L0,7 Z" fill="#722ed1" />
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
                  v-for="call_id in selectedNode.businesses.slice(0, 3)" 
                  :key="call_id"
                  class="business-tag"
                >
                  {{ getBusinessById(call_id)?.call_id || call_id }}
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
              <span class="info-value">{{ selectedBusiness.call_id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">波长：</span>
              <span class="info-value">{{ selectedBusiness.wavelength }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">属性：</span>
              <span class="info-value">{{ selectedBusiness.current_conn_attr }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">告警时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.alarm_time, 'full') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">动作时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.start_time, 'full') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">结束时间：</span>
              <span class="info-value">{{ formatDate(selectedBusiness.end_time, 'full') }}</span>
            </div>
          </div>
        </div>
        
        <div class="path-info-section">
          <h3>受影响路径</h3>
          <div class="path-display">
            <div class="path-nodes">
              <span 
                v-for="(node, index) in getPathNodes(selectedBusiness.route_str)" 
                :key="index"
                :class="['path-node', { 'alert-node': isAlertNode(node) }]"
              >
                {{ node }}
                <span v-if="index < getPathNodes(selectedBusiness.route_str).length - 1" class="path-arrow">→</span>
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
import { getHistoricalList, getAnalysisList, searchOMSAlert, getProjectList, topologyDataList } from '@/api/analysis';
import * as XLSX from 'xlsx';
import { storage } from "@/utils/storage";
const PROJECT_CACHE_KEY = 'selected_project_name';
// 状态管理
const timeRange = ref([]);
const detailDialogVisible = ref(false);
const selectedBusiness = ref(null);
const selectedRowKeyList = ref([]);
const hoveredcall_id = ref(null);
const selectedNode = ref(null);

// 拖拽和缩放状态
const zoomLevel = ref(1);
const panX = ref(0);
const panY = ref(0);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const lastPan = ref({ x: 0, y: 0 });

// SVG尺寸
const svgWidth = ref(1200);
const svgHeight = ref(800);

// 防抖相关
const hoverDebounce = ref(null);
const projectName = ref('');

// 拓扑图数据
const topologyNodes = ref([]);
const topologyLinks = ref([]);

// 容器引用
const topologyContainer = ref(null);
const projectOption = ref([]);
const alarmValue = ref([]);
const alarmOptions = ref([]);
const omsValue = ref(['1.1.1.1_1.1.1.2_1']);
const omsOptions = ref([
  { label: '1.1.1.1_1.1.1.2_1', value: '1.1.1.1_1.1.1.2_1' },
  { label: '1.1.1.1_1.1.1.2_2', value: '1.1.1.1_1.1.1.2_2' },
]);

// 表格列定义
const columns = [
  {
    colKey: 'row-select',
    type: 'multiple',
    width: 70
  },
  {
    title: '动作原因',
    colKey: 'action_reason',
    width: 150,
    cell: 'action_reason'
  },
  {
    title: '告警时间',
    colKey: 'alarm_time',
    width: 170,
    cell: 'alarm_time'
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
    ellipsis: true
  },
  {
    title: '连接属性',
    colKey: 'current_conn_attr',
    width: 150
  },
  {
    title: '波长',
    colKey: 'wavelength',
    width: 150,
    cell: (h, params) => {
      if (!params || !params.row) return ''
      
      const { row } = params
      
      const text = row.wavelength !== undefined && row.wavelength !== null 
        ? String(row.wavelength) 
        : ''
      
      if (!text) return ''

      if (text.includes('\n')) {
        return h('div', { 
          style: 'white-space: pre-line; line-height: 1.5;'
        }, text)
      }
      
      return text
    }
  },
  {
    title: '动作前路由',
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
    title: '动作后路由',
    colKey: 'new_route_str',
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
          {row?.new_route_str || ''}
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
    minWidth: 200
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

const tableHeight = ref('600px');

// 计算属性
const defaultTimeRange = computed(() => {
  const now = new Date();
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(now.getDate() - 7);
  return [sevenDaysAgo, now];
});

const selectedBusinesses = computed(() => {
  return businessList.value.filter((business) => 
    selectedRowKeyList.value.includes(business.id)
  );
});

const alarmNodeCount = computed(() => {
  return topologyNodes.value.filter((node) => node.status === 'alert').length;
});

// 数据
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

const getHistoricalTable = async (project_name, alarm_id, page, limit, enable_limit) => {
  try {
    const params = {
      project_name: project_name,
      alarm_id: alarm_id,
      page: page,
      limit: limit,
      enable_limit: enable_limit,
    }
    const response = await getAnalysisList(params);
    // 为每行数据生成唯一ID
    businessList.value = (response.data || []).map((item, index) => ({
      ...item,
      id: `row_${index}_${Date.now()}`
    }));
    pagination.total = response.total;
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const exportAlarmTable = async (project_name, alarm_id, page, limit, enable_limit) => {
  try {
    const params = {
      project_name: project_name,
      alarm_id: alarm_id,
      page: page,
      limit: limit,
      enable_limit: enable_limit,
    }
    const response = await getAnalysisList(params);
    const excelData = response.data.map((item, index) => ({
      ...item,
      time_range: `开始时间：${item.start_time} \n 结束时间：${item.end_time}`,
      result: item.result ? '成功' : '失败',
    }));
    return excelData;
  } catch (error) {
    MessagePlugin.error('获取业务列表失败，请重试');
    return [];
  }
};

const handleTimeRangeChange = (value) => {
  console.log('时间范围:', value);
  if (value && value.length === 2) {
    MessagePlugin.success(`时间范围已设置为: ${formatDate(value[0], 'chinese')} 至 ${formatDate(value[1], 'chinese')}`);
  }
};

const filterMethod = (search, option) => {
  return option.label.indexOf(search) !== -1;
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

const formatDateTime = (isoString) => {
  return dayjs(isoString).format('YYYY-MM-DD HH:mm:ss');
};

const formatTimeRange = (range) => {
  if (!range || !Array.isArray(range)) return [];
  return range.map(formatDateTime);
};

const formattedTimeRange = computed(() => formatTimeRange(timeRange.value));

const handleAnalyze = async () => {
  if (!timeRange.value || timeRange.value.length !== 2) {
    MessagePlugin.warning('请先选择时间范围');
    return;
  }
  
  await getHistoricalTable(projectName.value, alarmValue.value, pagination.defaultCurrent, pagination.defaultPageSize, 1);
  
  // 获取拓扑数据
  const topologyData = await getNodeDataList(projectName.value);
  if (topologyData) {
    setTimeout(() => {
      generateTopologyData(topologyData);
    }, 500);
  }
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

const handleSelectChange = (selectedRowKeys) => {
  selectedRowKeyList.value = selectedRowKeys;
  console.log('selectedRowKeys', selectedRowKeys);
  if (topologyNodes.value.length > 0) {
    updateTopologyData();
  }
};

const handleAnalyzeBusiness = (row) => {
  MessagePlugin.info(`开始分析业务: ${row.call_id}`);
};

const handleViewDetails = (row) => {
  selectedBusiness.value = row;
  detailDialogVisible.value = true;
  MessagePlugin.info(`查看业务详情: ${row.call_id}`);
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
    const tableData = await exportAlarmTable(projectName.value, alarmValue.value, pagination.defaultCurrent, pagination.defaultPageSize, 0);

    if (tableData.length === 0) {
      MessagePlugin.warning('暂无数据可导出')
      return
    }

    const exportData = tableData.map((row) => {
      const exportRow = {}
      columns.forEach((col) => {
        if (['row-select'].includes(col.colKey)) return

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
    XLSX.utils.book_append_sheet(workbook, worksheet, '断纤影响的业务列数据')

    const date = new Date()
    const formattedDate =
      `${date.getFullYear().toString().slice(2)}` +
      `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
      `${date.getDate().toString().padStart(2, '0')}` +
      `${date.getHours().toString().padStart(2, '0')}` +
      `${date.getMinutes().toString().padStart(2, '0')}`
    const fileName = `断纤影响的业务列表_${formattedDate}.xlsx`

    XLSX.writeFile(workbook, fileName)
    MessagePlugin.success('导出成功，请查看下载文件')
  } catch (error) {
    console.error('数据导出失败:', error)
    MessagePlugin.error('导出失败，请重试')
  }
};

const handlePageChange = async (pageInfo) => {
  await getHistoricalTable(projectName.value, alarmValue.value, pageInfo.current, pageInfo.pageSize, 1);
  pagination.defaultCurrent = pageInfo.current;
  pagination.defaultPageSize = pageInfo.pageSize;
};

const getPathNodes = (path) => {
  if (!path || typeof path !== 'string') return [];
  return path.split('-');
};

const isAlertNode = (node) => {
  if (!node || typeof node !== 'string') return false;
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

const getPathPreview = (pathData) => {
  if (!pathData) return '暂无路径信息';
  
  if (typeof pathData === 'string') {
    if (pathData.includes('-')) {
      const nodes = pathData.split('-');
      if (nodes.length <= 3) return pathData;
      return `${nodes[0]}-...-${nodes[nodes.length - 1]}`;
    }
    return pathData;
  }
  
  if (Array.isArray(pathData)) {
    if (pathData.length === 0) return '暂无路径信息';
    const firstItem = pathData[0];
    if (firstItem && typeof firstItem === 'object' && firstItem.label) {
      return getPathPreview(firstItem.label);
    }
    return `${pathData.length}个路径段`;
  }
  
  return '暂无路径信息';
};

// 拓扑图相关方法
const removeBusinessFromTopology = (call_id) => {
  const index = selectedRowKeyList.value.indexOf(call_id);
  if (index !== -1) {
    selectedRowKeyList.value.splice(index, 1);
    MessagePlugin.info(`已从拓扑图上移除业务`);
    updateTopologyData();
  }
};

const highlightBusinessPath = (call_id) => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  
  hoverDebounce.value = setTimeout(() => {
    hoveredcall_id.value = call_id;
  }, 30);
};

const clearHighlight = () => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
  
  hoverDebounce.value = setTimeout(() => {
    hoveredcall_id.value = null;
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
          interfaces: link.localIfIndex || 'unknown',
          isVirtual: link.isVirtual || false
        };
      } else {
        return { 
          direction: 'in', 
          nodeName: link.sourceName, 
          nodeId: link.sourceId, 
          interfaces: link.remoteIfIndex || 'unknown',
          isVirtual: link.isVirtual || false
        };
      }
    });

  selectedNode.value = {
    ...node,
    connections: connectionDetails.length,
    connectionDetails: connectionDetails
  };

  if (node.status === 'alert') {
    MessagePlugin.warning(`告警节点: ${node.name}，该节点存在通道告警`);
  } else {
    MessagePlugin.info(`选中节点: ${node.name}`);
  }
};

const getBusinessById = (call_id) => {
  return businessList.value.find(b => b.id === call_id);
};

const onActiveChange = (highlightRowKeys, ctx) => {
  console.log(highlightRowKeys, ctx);
};

// 节点和链接颜色方法
const getNodeColor = (node) => {
  if (selectedNode.value?.id === node.id) return '#52c41a';
  if (node.status === 'alert') return '#ff4d4f';

  const isInSelectedBusiness = selectedBusinesses.value.some((business) => {
    const oldLinks = parseRouteStr(business.current_route_str || '');
    const newLinks = parseRouteStr(business.new_route_str || '');
    const allLinks = [...oldLinks, ...newLinks];
    
    return allLinks.some(link => 
      (link.sourceId === node.id || link.sourceId === node.ip || link.sourceName === node.name) ||
      (link.targetId === node.id || link.targetId === node.ip || link.targetName === node.name)
    );
  });

  if (isInSelectedBusiness) return '#91d5ff';
  return '#d9d9d9';
};

const getNodeBorderColor = (node) => {
  if (node.status === 'alert') return '#cf1322';
  if (selectedNode.value?.id === node.id) return '#389e0d';
  
  const isInSelectedBusiness = selectedBusinesses.value.some((business) => {
    const oldLinks = parseRouteStr(business.current_route_str || '');
    const newLinks = parseRouteStr(business.new_route_str || '');
    const allLinks = [...oldLinks, ...newLinks];
    
    return allLinks.some(link => 
      (link.sourceId === node.id || link.sourceId === node.ip || link.sourceName === node.name) ||
      (link.targetId === node.id || link.targetId === node.ip || link.targetName === node.name)
    );
  });
  
  if (isInSelectedBusiness) return '#1890ff';
  return '#bfbfbf';
};

const getLinkColor = (link) => {
  // 悬停高亮优先
  if (hoveredcall_id.value) {
    if (link.businessId === hoveredcall_id.value) {
      if (link.type === 'shared') return '#722ed1'; // 悬停时共享路径高亮为深紫色
      if (link.type === 'old-route') return '#ff7a45';
      if (link.type === 'new-route') return '#69b1ff';
    }
  }
  
  // 共享路径 - 紫色
  if (link.type === 'shared') return '#722ed1';
  // 动作前路由 - 橙色
  if (link.type === 'old-route') return '#fa541c';
  // 动作后路由 - 蓝色
  if (link.type === 'new-route') return '#1677ff';
  // 基础链路 - 灰色
  if (link.type === 'base') return '#d9d9d9';
  
  return '#d9d9d9';
};

// 获取链接线宽
const getLinkStrokeWidth = (link) => {
  if (hoveredcall_id.value && link.businessId === hoveredcall_id.value) return 4;
  if (link.type === 'shared') return 3.5;
  if (link.type === 'old-route' || link.type === 'new-route') return 3;
  return 1.5;
};

const getLinkDashArray = (link) => {
  if (link.type === 'shared') return '10,6'; // 共享路径使用虚线
  if (link.type === 'old-route') return '8,4';
  return 'none';
};

// 获取链接箭头
const getLinkMarker = (link) => {
  if (hoveredcall_id.value && link.businessId === hoveredcall_id.value) {
    if (link.type === 'shared') return 'url(#arrowShared)';
    return 'url(#arrowHover)';
  }
  if (link.type === 'shared') return 'url(#arrowShared)';
  if (link.type === 'old-route') return 'url(#arrowOld)';
  if (link.type === 'new-route') return 'url(#arrowNew)';
  return 'url(#arrow)';
};

// 解析路由字符串
const parseRouteStr = (routeStr) => {
  if (!routeStr || typeof routeStr !== 'string') return [];
  
  const links = [];
  const seenLinks = new Set();
  const lines = routeStr.trim().split('\n');
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (!trimmedLine) continue;
    
    if (seenLinks.has(trimmedLine)) {
      console.log('跳过重复路由行:', trimmedLine);
      continue;
    }
    seenLinks.add(trimmedLine);
    
    let hasOEPPrefix = false;
    let oepPortPrefix = '';
    let remainingStr = trimmedLine;
    
    const oepPrefixMatch = trimmedLine.match(/^\(OEP:(\[[^\]]+\])\)/);
    if (oepPrefixMatch) {
      hasOEPPrefix = true;
      oepPortPrefix = oepPrefixMatch[1];
      remainingStr = trimmedLine.substring(oepPrefixMatch[0].length);
    }
    
    const mainRegex = /^([\d.]+)\(([^,]+),(\[[^\]]+\])\)->\((\[[^\]]+\]),([^()]+?(?:\([^)]*\))?)\)([\d.]+)(?:\(OEP:(\[[^\]]+\])\))?$/;
    const match = remainingStr.match(mainRegex);
    
    if (match) {
      const [, sourceId, sourceName, sourcePort, targetPort, targetName, targetId, oepSuffix] = match;
      
      let cleanTargetName = targetName.trim();
      
      links.push({
        sourceId: sourceId,
        sourceName: sourceName.trim(),
        sourcePort: sourcePort,
        targetId: targetId,
        targetName: cleanTargetName,
        targetPort: targetPort,
        hasOEP: !!oepSuffix || hasOEPPrefix,
        oepPort: oepSuffix || oepPortPrefix || null,
        oepPosition: hasOEPPrefix ? 'before' : (oepSuffix ? 'after' : null)
      });
    } else {
      console.warn('无法解析路由行:', trimmedLine);
    }
  }
  
  return links;
};

// 生成拓扑数据
const generateTopologyData = (apiData) => {
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

  topologyNodes.value = positionedNodes.map((node) => ({
    id: node.id,
    name: node.name,
    ip: node.ip || node.id,
    status: node.status || 'normal',
    connections: node.connections || 0,
    x: node.canvasX,
    y: node.canvasY,
    radius: 14,
    businesses: []
  }));

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
  
  topologyNodes.value.forEach((node) => {
    node.connections = topologyLinks.value.filter(
      link => link.sourceId === node.id || link.targetId === node.id
    ).length;
  });
  
  if (selectedBusinesses.value.length > 0) {
    updateTopologyData();
  }
};

// 更新拓扑数据
// 更新拓扑数据
const updateTopologyData = () => {
  console.log('开始更新拓扑图，选中的业务数量:', selectedBusinesses.value.length);
  
  // 清理虚拟链路（之前创建的临时链路）
  topologyLinks.value = topologyLinks.value.filter(link => !link.isVirtual);
  
  // 重置所有链接
  topologyLinks.value.forEach(link => {
    link.type = 'base';
    link.businessId = null;
    link.businesses = [];
    link.hasOldRoute = false;
    link.hasNewRoute = false;
  });
  
  // 重置所有节点
  topologyNodes.value.forEach((node) => {
    node.businesses = [];
    node.status = 'normal';
  });
  
  // 先收集所有业务的链路信息
  const allBusinessLinks = []; // 存储所有链路信息
  const perBusinessLinks = new Map(); // 按业务分组存储链路，用于检测共享路径
  
  // 处理每个选中的业务
  selectedBusinesses.value.forEach((business) => {
    console.log('处理业务:', business.id, business.call_id);
    
    // 初始化该业务的链路记录
    perBusinessLinks.set(business.id, {
      oldRoutes: [],
      newRoutes: []
    });
    
    // 标记告警节点
    const alarmNodeName = extractNodeName(business.alarm_str);
    const alarmNodeId = extractNodeId(business.alarm_str);
    
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
    
    // 解析动作前路由
    if (business.current_route_str) {
      const oldRouteLinks = parseRouteStr(business.current_route_str);
      console.log(`业务 ${business.call_id} 动作前路由链接数:`, oldRouteLinks.length);
      
      oldRouteLinks.forEach((parsedLink) => {
        const linkInfo = {
          ...parsedLink,
          businessId: business.id,
          routeType: 'old-route'
        };
        allBusinessLinks.push(linkInfo);
        perBusinessLinks.get(business.id).oldRoutes.push(linkInfo);
      });
    }
    
    // 解析动作后路由
    if (business.new_route_str) {
      const newRouteLinks = parseRouteStr(business.new_route_str);
      console.log(`业务 ${business.call_id} 动作后路由链接数:`, newRouteLinks.length);
      
      newRouteLinks.forEach((parsedLink) => {
        const linkInfo = {
          ...parsedLink,
          businessId: business.id,
          routeType: 'new-route'
        };
        allBusinessLinks.push(linkInfo);
        perBusinessLinks.get(business.id).newRoutes.push(linkInfo);
      });
    }
  });
  
  // 按源目节点分组，收集每条链路上的所有业务及其路由类型
  const linkBusinessMap = new Map(); // key: "sourceId-targetId"
  
  allBusinessLinks.forEach((linkInfo) => {
    const { sourceId, sourceName, targetId, targetName, businessId, routeType } = linkInfo;
    
    let sourceNode = topologyNodes.value.find(n => 
      n.id === sourceId || n.ip === sourceId || n.name === sourceName || n.id === sourceName
    );
    let targetNode = topologyNodes.value.find(n => 
      n.id === targetId || n.ip === targetId || n.name === targetName || n.id === targetName
    );
    
    if (!sourceNode || !targetNode) {
      console.warn(`节点未找到: ${sourceName}(${sourceId}) -> ${targetName}(${targetId})`);
      return;
    }
    
    const linkKey = `${sourceNode.id}-${targetNode.id}`;
    
    if (!linkBusinessMap.has(linkKey)) {
      linkBusinessMap.set(linkKey, {
        sourceNode,
        targetNode,
        businesses: [],
        businessesWithOldRoute: new Set(), // 有动作前路由的业务
        businessesWithNewRoute: new Set(), // 有动作后路由的业务
        hasOldRoute: false,
        hasNewRoute: false,
        hasShared: false // 是否有业务同时有动作前和动作后路由经过此链路
      });
    }
    
    const linkData = linkBusinessMap.get(linkKey);
    if (!linkData.businesses.includes(businessId)) {
      linkData.businesses.push(businessId);
    }
    
    if (routeType === 'old-route') {
      linkData.businessesWithOldRoute.add(businessId);
      linkData.hasOldRoute = true;
    } else if (routeType === 'new-route') {
      linkData.businessesWithNewRoute.add(businessId);
      linkData.hasNewRoute = true;
    }
    
    // 标记节点业务
    if (!sourceNode.businesses.includes(businessId)) {
      sourceNode.businesses.push(businessId);
    }
    if (!targetNode.businesses.includes(businessId)) {
      targetNode.businesses.push(businessId);
    }
  });
  
  // 第二遍遍历：检测每个业务是否在同一链路上同时有动作前和动作后路由
  // 这表示该链路是该业务的重合路径（共享路径）
  linkBusinessMap.forEach((linkData, linkKey) => {
    const { businesses, businessesWithOldRoute, businessesWithNewRoute } = linkData;
    
    // 检查是否有业务同时在这条链路上有动作前路由和动作后路由
    for (const businessId of businesses) {
      if (businessesWithOldRoute.has(businessId) && businessesWithNewRoute.has(businessId)) {
        linkData.hasShared = true;
        break;
      }
    }
  });
  
  // 更新链路类型
  linkBusinessMap.forEach((linkData, linkKey) => {
    const { sourceNode, targetNode, businesses, hasOldRoute, hasNewRoute, hasShared } = linkData;
    
    // 查找现有的基础链路
    const existingLinks = topologyLinks.value.filter(l => 
      (l.sourceId === sourceNode.id && l.targetId === targetNode.id)
    );
    
    // 确定链路类型
    let linkType = 'base';
    if (hasShared) {
      linkType = 'shared'; // 共享路径：紫色虚线
    } else if (hasNewRoute) {
      linkType = 'new-route';
    } else if (hasOldRoute) {
      linkType = 'old-route';
    }
    
    if (existingLinks.length > 0) {
      existingLinks.forEach(link => {
        link.type = linkType;
        link.businesses = [...businesses];
        link.businessId = businesses[0];
        link.hasShared = hasShared;
        link.hasOldRoute = hasOldRoute;
        link.hasNewRoute = hasNewRoute;
      });
    } else {
      // 创建虚拟链路
      const dx = targetNode.x - sourceNode.x;
      const dy = targetNode.y - sourceNode.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const midX = (sourceNode.x + targetNode.x) / 2;
      const midY = (sourceNode.y + targetNode.y) / 2;
      const controlX = midX;
      const controlY = midY - dist * 0.15;
      
      const newLink = {
        source: sourceNode.name,
        target: targetNode.name,
        sourceId: sourceNode.id,
        targetId: targetNode.id,
        sourceName: sourceNode.name,
        targetName: targetNode.name,
        d: `M${sourceNode.x},${sourceNode.y} Q${controlX},${controlY} ${targetNode.x},${targetNode.y}`,
        type: linkType,
        businessId: businesses[0],
        businesses: [...businesses],
        weight: 1,
        localIfIndex: 'virtual',
        remoteIfIndex: 'virtual',
        hasArrow: true,
        direction: `${sourceNode.id}->${targetNode.id}`,
        isVirtual: true,
        hasShared: hasShared,
        hasOldRoute: hasOldRoute,
        hasNewRoute: hasNewRoute
      };
      
      topologyLinks.value.push(newLink);
    }
  });
  
  console.log('拓扑图更新完成，告警节点数:', topologyNodes.value.filter(n => n.status === 'alert').length);
  console.log('链路类型分布:', 
    'shared:', topologyLinks.value.filter(l => l.type === 'shared').length,
    'old-route:', topologyLinks.value.filter(l => l.type === 'old-route').length,
    'new-route:', topologyLinks.value.filter(l => l.type === 'new-route').length,
    'base:', topologyLinks.value.filter(l => l.type === 'base').length
  );
};

const extractNodeName = (alarmStr) => {
  if (!alarmStr) return '';
  const match = alarmStr.match(/\(([^,]+),/);
  return match ? match[1] : '';
};

const extractNodeId = (alarmStr) => {
  if (!alarmStr) return '';
  const match = alarmStr.match(/(\d+\.\d+\.\d+\.\d+)\(/);
  return match ? match[1] : '';
};

const applyRouteToLinks = (parsedLink, routeType, businessId) => {
  const { sourceId, sourceName, targetId, targetName } = parsedLink;
  
  let sourceNode = topologyNodes.value.find(n => 
    n.id === sourceId || n.ip === sourceId || n.name === sourceName || n.id === sourceName
  );
  let targetNode = topologyNodes.value.find(n => 
    n.id === targetId || n.ip === targetId || n.name === targetName || n.id === targetName
  );
  
  if (!sourceNode || !targetNode) {
    console.warn(`节点未找到: ${sourceName}(${sourceId}) -> ${targetName}(${targetId})`);
    return;
  }
  
  const forwardLinks = topologyLinks.value.filter(l => 
    l.sourceId === sourceNode.id && l.targetId === targetNode.id
  );
  
  if (forwardLinks.length > 0) {
    forwardLinks.forEach(link => {
      if (link.type === routeType && link.businessId === businessId) return;
      
      link.type = routeType;
      link.businessId = businessId;
      if (!link.businesses) link.businesses = [];
      if (!link.businesses.includes(businessId)) {
        link.businesses.push(businessId);
      }
    });
  } else {
    const dx = targetNode.x - sourceNode.x;
    const dy = targetNode.y - sourceNode.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const midX = (sourceNode.x + targetNode.x) / 2;
    const midY = (sourceNode.y + targetNode.y) / 2;
    
    const controlX = midX;
    const controlY = midY - dist * 0.15;
    
    const newLink = {
      source: sourceNode.name,
      target: targetNode.name,
      sourceId: sourceNode.id,
      targetId: targetNode.id,
      sourceName: sourceNode.name,
      targetName: targetNode.name,
      d: `M${sourceNode.x},${sourceNode.y} Q${controlX},${controlY} ${targetNode.x},${targetNode.y}`,
      type: routeType,
      businessId: businessId,
      businesses: [businessId],
      weight: 1,
      localIfIndex: parsedLink.sourcePort || 'unknown',
      remoteIfIndex: parsedLink.targetPort || 'unknown',
      hasArrow: true,
      direction: `${sourceNode.id}->${targetNode.id}`,
      isVirtual: true
    };
    
    topologyLinks.value.push(newLink);
  }
  
  if (!sourceNode.businesses.includes(businessId)) {
    sourceNode.businesses.push(businessId);
  }
  if (!targetNode.businesses.includes(businessId)) {
    targetNode.businesses.push(businessId);
  }
};

const showSelectOMS = async () => {
  alarmOptions.value = await getOMSData(projectName.value, formattedTimeRange.value[0], formattedTimeRange.value[1]);
};

const getOMSData = async (name, starttime, endtime) => {
  try {
    const params = {
      project_name: name,
      stime: starttime,
      etime: endtime,
    };
    const response = await searchOMSAlert(params);
    const projectInfo = response.data[0].oms_dict_list;
    return projectInfo;
  } catch (error) {
    MessagePlugin.error('获取项目列表失败，请重试');
    return [];
  }
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
  
  setTimeRange('last365days');
  
  await showSelectOMS();
  if (alarmOptions.value.length > 0) {
    alarmValue.value.push(alarmOptions.value[1]?.value);
  }

}

// 监听表格选择变化
watch(selectedRowKeyList, () => {
  if (topologyNodes.value.length > 0) {
    updateTopologyData();
  }
});

watch(projectName, (newValue, oldValue) => {
  if (newValue && newValue !== oldValue) {
    storage.set(PROJECT_CACHE_KEY, newValue);
    console.log('项目名称已更新缓存:', newValue);
  }
});

// 组件卸载前清理
onBeforeUnmount(() => {
  if (hoverDebounce.value) {
    clearTimeout(hoverDebounce.value);
  }
});

// 初始化
onMounted(async () => {
  await parseRouteParams();

  await getHistoricalTable(projectName.value, alarmValue.value, pagination.defaultCurrent, pagination.defaultPageSize, 1);
  
  const topologyData = await getNodeDataList(projectName.value);
  if (topologyData) {
    generateTopologyData(topologyData);
  }
  
  if (topologyContainer.value) {
    topologyContainer.value.style.cursor = 'grab';
  }
});
</script>

<style scoped>
/* 样式与第一个组件保持一致，此处省略，请参考第一个组件的样式 */
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

.oms-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.time-cell {
  font-size: 13px;
  color: #1f2d3d;
}

.date-cell {
  font-size: 13px;
  color: #1f2d3d;
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
  height: 3px;
  border-radius: 2px;
}

.legend-line.normal-path {
  background: #d9d9d9;
}

.legend-line.old-path {
  height: 0;
  background: none;
  border-top: 3px dashed #fa541c;
}

.legend-line.new-path {
  background: #1677ff;
}

.legend-line.shared-path {
  height: 0;
  background: none;
  border-top: 3px dashed #722ed1;
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
  stroke-width: 4 !important;
  filter: drop-shadow(0 0 3px rgba(24, 144, 255, 0.5));
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

.operation-buttons {
  display: flex;
  gap: 8px;
}
</style>