<template>
  <div class="component-main">
    <t-tabs v-model="tabValue" theme="card" @change="onTabChange">
      <t-tab-panel value="光层业务特性（O-含L0/智控/支撑）" label="光层业务特性" :destroy-on-hide="false">
      </t-tab-panel>
      <t-tab-panel value="电层业务特性（E-含L1/支撑）" label="电层业务特性" :destroy-on-hide="false">
      </t-tab-panel>
      <t-tab-panel value="分组业务特性（P-含L2/支撑）" label="分组业务特性" :destroy-on-hide="false">
      </t-tab-panel>
      <t-tab-panel value="智控协同业务特性（C）" label="智控协同业务特性" :destroy-on-hide="false">
      </t-tab-panel>
      <t-tab-panel value="产品安全特性（SEC）" label="产品安全特性" :destroy-on-hide="false">
      </t-tab-panel>
    </t-tabs>

    <div class="toolbar">
      <t-popconfirm 
        theme="default" 
        content="确认同步iCenter数据吗?" 
        @confirm="refreshTree">
        <t-button v-show="showButton" theme="primary" variant="outline" size="small" :loading="refreshLoading">
          组件树同步iCenter数据
        </t-button>
      </t-popconfirm>
      <span class="refresh-time">最近刷新时间：{{ lastRefreshTime || '未刷新' }}</span>

      <span v-show="showButton" class="refresh-time">是否拉取新数据：
        <t-switch v-model="forceRefresh"/>
      </span>
      
      <div class="toolbar-right">
        <t-tag theme="primary" variant="light" size="small">包含</t-tag>
        <t-tag theme="warning" variant="light" size="small">依赖</t-tag>
        <t-tag theme="success" variant="light" size="small">关联</t-tag>
        <t-tag theme="danger" variant="light" size="small">连接</t-tag>
      </div>
    </div>

    <div class="main-layout">
      <!-- 左侧树形目录 -->
      <div class="tree-sidebar">
        <div class="tree-header">
          <t-icon name="view-list" />
          <span>路径导航树</span>
          <t-button size="small" variant="text" @click="expandAll" class="tree-action-btn">全部展开</t-button>
          <t-button size="small" variant="text" @click="collapseAll" class="tree-action-btn">全部收起</t-button>
        </div>
        <div class="tree-content">
          <div v-if="treeLoading" class="tree-loading">
            <t-loading size="small" text="加载中..." />
          </div>
          <div v-else-if="treeData.length === 0" class="tree-empty">
            暂无数据
          </div>
          <t-tree
            v-else
            v-model:expanded="expandedKeys"
            :data="treeData"
            :keys="treeKeys"
            hover
            activable
            line
            transition
            @click="onTreeNodeClick"
          />
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="right-content">
        <!-- 上半部分：流程图 -->
        <div class="flowchart-section">
          <div class="section-header">
            <span class="section-title">
              <t-icon name="chart-bubble" />
              组件关系图
            </span>
            <div class="section-actions">
              <t-button size="small" variant="outline" @click="autoLayout">
                <template #icon><t-icon name="refresh" /></template>
                自动布局
              </t-button>
              <t-button size="small" variant="outline" @click="centerGraph">
                <template #icon><t-icon name="zoom-in" /></template>
                适应画布
              </t-button>
              <t-button 
                size="small" 
                variant="text" 
                @click="toggleFullscreen" 
                v-if="hasGraphData"
              >
                <template #icon>
                  <t-icon :name="isFullscreen ? 'fullscreen-exit' : 'fullscreen'" />
                </template>
                {{ isFullscreen ? '退出全屏' : '全屏' }}
              </t-button>
            </div>
          </div>
          <div class="flowchart-container" ref="containerRef" :class="{ 'fullscreen-chart': isFullscreen }">
            <div v-if="graphLoading" class="graph-loading">
              <t-loading size="large" text="加载组件图数据中..." />
            </div>
            <div v-else-if="!hasGraphData && !showDetailOnly" class="graph-empty">
              <t-icon name="chart-bubble" size="48px" style="color: #c0c4cc;" />
              <p>请点击左侧树节点查看组件关系图</p>
            </div>
            <div v-else-if="hasGraphData" class="canvas-wrapper" ref="canvasWrapper">
              <svg 
                class="flowchart-svg" 
                :viewBox="viewBox" 
                :width="svgWidth" 
                :height="svgHeight"
                @mousedown="onSvgMouseDown"
                @mousemove="onSvgMouseMove"
                @mouseup="onSvgMouseUp"
                @wheel="onWheel"
              >
                <!-- 连线层 -->
                <g class="edges-group">
                  <g v-for="edge in categoryEdges" :key="edge.id">
                    <path
                      :d="edge.path"
                      :stroke="edge.highlighted ? edge.strokeColor : '#c4cdd5'"
                      :stroke-width="edge.highlighted ? 2.5 : 1.5"
                      fill="none"
                      :marker-end="getMarkerEnd(edge.arrowType, edge.highlighted)"
                      class="edge-path"
                    />
                    <rect
                      :x="edge.labelX - edge.labelWidth / 2"
                      :y="edge.labelY - 10"
                      :width="edge.labelWidth"
                      height="20"
                      rx="4"
                      :fill="edge.bgColor"
                      :stroke="edge.strokeColor"
                      stroke-width="0.5"
                      opacity="0.95"
                    />
                    <text
                      :x="edge.labelX"
                      :y="edge.labelY + 4"
                      text-anchor="middle"
                      font-size="10"
                      :fill="edge.textColor"
                      font-weight="500"
                    >{{ edge.label }}</text>
                  </g>
                </g>

                <!-- 节点层 -->
                <g class="nodes-group">
                  <g
                    v-for="node in allNodes"
                    :key="node.id"
                    :transform="`translate(${nodePositions[node.id]?.x ?? node.x}, ${nodePositions[node.id]?.y ?? node.y})`"
                    @mouseenter="highlightNode(node.id)"
                    @mouseleave="clearHighlight"
                    @mousedown="onNodeMouseDown($event, node.id)"
                    @click="selectNode(node)"
                    :class="{ 
                      'selected': selectedNodeId === node.id, 
                      'highlight-flash': flashingNodeId === node.id,
                      'dragging': draggingNodeId === node.id
                    }"
                  >
                    <!-- 椭圆节点（中心组件） -->
                    <template v-if="node.shape === 'ellipse'">
                      <ellipse
                        :cx="node.width / 2"
                        :cy="node.height / 2"
                        :rx="node.width / 2"
                        :ry="node.height / 2"
                        :fill="node.bgColor"
                        :stroke="getNodeStroke(node)"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 2"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
                    </template>

                    <!-- 矩形/圆角矩形节点（汇聚框） -->
                    <template v-else>
                      <rect
                        :width="node.width"
                        :height="node.height"
                        :rx="node.shape === 'feature' ? 12 : 6"
                        :fill="node.bgColor"
                        :stroke="getNodeStroke(node)"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 1.5"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
                    </template>

                    <!-- 类型标签 -->
                    <rect 
                      :x="node.typeX" 
                      :y="-10" 
                      :width="node.typeWidth" 
                      height="20" rx="4" 
                      :fill="node.tagColor" 
                    />
                    <text 
                      :x="node.typeX + node.typeWidth / 2" 
                      y="4" 
                      text-anchor="middle" 
                      font-size="11" 
                      fill="white" 
                      font-weight="bold"
                    >{{ node.typeLabel }}</text>

                    <!-- 数量角标（右上角） -->
                    <circle 
                      v-if="node.count > 0 && node.id !== centerComponentId"
                      :cx="node.width - 12" 
                      :cy="12" 
                      r="10" 
                      fill="#e34d59" 
                      stroke="white" 
                      stroke-width="2"
                    />
                    <text 
                      v-if="node.count > 0 && node.id !== centerComponentId"
                      :x="node.width - 12" 
                      :y="16" 
                      text-anchor="middle" 
                      font-size="10" 
                      fill="white" 
                      font-weight="bold"
                    >{{ node.count }}</text>

                    <!-- 节点名称 -->
                    <text 
                      :x="node.width / 2" 
                      :y="node.textY" 
                      text-anchor="middle" 
                      font-size="12" 
                      font-weight="600" 
                      :fill="node.textColor"
                    >
                      {{ node.name.length > 12 ? node.name.substring(0, 12) + '...' : node.name }}
                    </text>

                    <!-- URL 链接图标 -->
                    <g v-if="node.url" class="link-indicator" @click.stop="openUrl(node.url)">
                      <circle :cx="node.width - 14" cy="10" r="8" fill="white" :stroke="node.tagColor" stroke-width="1" />
                      <text :x="node.width - 14" y="14" text-anchor="middle" font-size="10" :fill="node.tagColor">🔗</text>
                    </g>

                    <!-- 拖拽手柄提示 -->
                    <g v-if="draggingNodeId === node.id" class="drag-hint">
                      <circle :cx="node.width / 2" :cy="node.height / 2" r="4" fill="#0052d9" opacity="0.5">
                        <animate attributeName="r" values="4;8;4" dur="1s" repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.5;0.2;0.5" dur="1s" repeatCount="indefinite" />
                      </circle>
                    </g>
                  </g>
                </g>

                <defs>
                  <filter id="shadow" x="-8%" y="-8%" width="120%" height="125%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08" />
                  </filter>
                  <marker id="arrowhead-green" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#2ba471" />
                  </marker>
                  <marker id="arrowhead-green-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#2ba471" />
                  </marker>
                  <marker id="arrowhead-orange" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e37318" />
                  </marker>
                  <marker id="arrowhead-orange-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e37318" />
                  </marker>
                  <marker id="arrowhead-red" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#c5221f" />
                  </marker>
                  <marker id="arrowhead-red-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#c5221f" />
                  </marker>
                  <marker id="arrowhead-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#1967d2" />
                  </marker>
                  <marker id="arrowhead-blue-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#1967d2" />
                  </marker>
                </defs>
              </svg>

              <div class="zoom-controls">
                <t-button size="small" variant="text" @click="zoomOut" shape="circle">
                  <t-icon name="remove" />
                </t-button>
                <span class="zoom-level">{{ Math.round(zoom * 100) }}%</span>
                <t-button size="small" variant="text" @click="zoomIn" shape="circle">
                  <t-icon name="add" />
                </t-button>
              </div>

              <div class="drag-tip" v-if="draggingNodeId">
                <t-tag theme="primary" variant="light" size="small">
                  <template #icon><t-icon name="move" /></template>
                  拖拽中...
                </t-tag>
              </div>
            </div>

            <!-- 仅显示详情时的占位 -->
            <div v-else-if="showDetailOnly" class="graph-empty">
              <t-icon name="chart-bubble" size="48px" style="color: #c0c4cc;" />
              <p>当前节点无关系图数据，仅展示基本信息</p>
            </div>
          </div>
        </div>

        <!-- 下半部分：明细数据 -->
        <div class="detail-section">
          <div class="section-header">
            <span class="section-title">
              <t-icon name="view-module" />
              明细数据
            </span>
          </div>
          <div class="detail-container">
            <t-loading :loading="detailLoading">
              <div class="detail-list">
                <t-descriptions title="基础信息" bordered :column="2" :label-style="{ width: '120px' }">
                  <t-descriptions-item label="组件/模块名称">{{ detail.basicInfo || '-' }}</t-descriptions-item>
                  <t-descriptions-item label="守护人">{{ detail.guardian || '-' }}</t-descriptions-item>
                  <t-descriptions-item label="状态">{{ detail.status || '-' }}</t-descriptions-item>
                  <t-descriptions-item label="组件/模块地址">
                    <t-tooltip :content="detail.url" placement="top" v-if="detail.url">
                      <t-link 
                        theme="primary" 
                        hover="color" 
                        :href="detail.url" 
                        target="_blank"
                        class="url-link"
                      >
                        {{ detail.url }}
                      </t-link>
                    </t-tooltip>
                    <span v-else>-</span>
                  </t-descriptions-item>
                </t-descriptions>
                
                <t-descriptions title="变更日志" bordered :column="2" :label-style="{ width: '120px' }">
                  <t-descriptions-item label="操作人">{{ detail.operator || '-' }}</t-descriptions-item>
                  <t-descriptions-item label="操作时间">{{ detail.operateTime || '-' }}</t-descriptions-item>
                </t-descriptions>
                
                <t-descriptions title="关联关系" bordered :column="1" :label-style="{ width: '120px' }">
                  <t-descriptions-item label="关联组件">
                    <div class="related-link-list" v-if="detail.relatedComponents.length">
                      <template v-for="(item, index) in detail.relatedComponents" :key="`${item.name}-${index}`">
                        <t-link
                          v-if="item.url"
                          theme="primary"
                          :href="item.url"
                          target="_blank"
                          hover="color"
                        >
                          {{ item.name }}
                        </t-link>
                        <span v-else>{{ item.name }}</span>
                        <span v-if="index < detail.relatedComponents.length - 1">，</span>
                      </template>
                    </div>
                    <span v-else>-</span>
                  </t-descriptions-item>
                  <t-descriptions-item label="关联特性">
                    <div class="related-link-list" v-if="detail.relatedFeatures.length">
                      <template v-for="(item, index) in detail.relatedFeatures" :key="`${item.name}-${index}`">
                        <t-link
                          v-if="item.url"
                          theme="primary"
                          :href="item.url"
                          target="_blank"
                          hover="color"
                        >
                          {{ item.name }}
                        </t-link>
                        <span v-else>{{ item.name }}</span>
                        <span v-if="index < detail.relatedFeatures.length - 1">，</span>
                      </template>
                    </div>
                    <span v-else>-</span>
                  </t-descriptions-item>
                </t-descriptions>

                <t-descriptions title="质量评分" bordered :column="2" :label-style="{ width: '120px' }">
                  <t-descriptions-item label="内容完备度">{{ detail.contentCompleteness || '-' }}</t-descriptions-item>
                  <t-descriptions-item label="内容规范性">{{ detail.contentStandardization || '-' }}</t-descriptions-item>
                </t-descriptions>
              </div>
            </t-loading>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情抽屉 -->
    <t-drawer
      v-model:visible="drawerVisible"
      :header="selectedNode?.name"
      size="720px"
      placement="right"
      :footer="false"
      @close="handleDrawerClose"
    >
      <div v-if="selectedNode" class="node-detail">
        <div class="detail-section">
          <div class="detail-label">节点类型</div>
          <span class="type-badge" :style="{ background: getTypeColor(selectedNode.type), color: '#fff' }">
            {{ selectedNode.typeLabel || selectedNode.type }}
          </span>
        </div>
        
        <div class="detail-section">
          <div class="detail-label">描述</div>
          <div class="detail-value" v-if="!isHtmlDescription(selectedNode.desc)">
            {{ selectedNode.desc || '暂无描述' }}
          </div>
          <div v-else class="html-description-container">
            <div class="html-description-toolbar">
              <t-button size="small" variant="outline" @click="openHtmlInNewWindow(selectedNode.desc, selectedNode.name)">
                <template #icon><t-icon name="jump" /></template>
                新窗口打开
              </t-button>
              <t-button size="small" variant="outline" @click="toggleHtmlFullscreen">
                <template #icon><t-icon :name="isHtmlFullscreen ? 'fullscreen-exit' : 'fullscreen'" /></template>
                {{ isHtmlFullscreen ? '退出全屏' : '全屏预览' }}
              </t-button>
            </div>
            <div
              class="html-description-content"
              :class="{ 'html-fullscreen': isHtmlFullscreen }"
              v-html="getProcessedHtmlContent(selectedNode.desc)"
            ></div>
          </div>
        </div>
        
        <div v-if="selectedNode.url" class="detail-section">
          <div class="detail-label">关联文档</div>
          <div class="url-container">
            <div class="url-display">
              <t-icon name="link" size="16px" class="url-icon" />
              <span class="url-text">{{ selectedNode.url }}</span>
            </div>
            <div class="url-actions">
              <t-button theme="primary" size="small" @click="openUrl(selectedNode.url)">
                <template #icon><t-icon name="jump" /></template>
                新窗口打开
              </t-button>
              <t-button theme="default" variant="outline" size="small" @click="copyUrl(selectedNode.url)">
                <template #icon><t-icon name="file-copy" /></template>
                复制链接
              </t-button>
            </div>
          </div>
        </div>
        
        <div class="detail-section">
          <div class="detail-label">关联路径</div>
          <div class="relation-paths">
            <div v-for="(path, idx) in getNodeRelationPaths(selectedNode.id)" :key="idx" class="path-item">
              <t-icon name="link" size="14px" /> {{ path }}
            </div>
            <div v-if="getNodeRelationPaths(selectedNode.id).length === 0" class="no-path">
              暂无关联路径
            </div>
          </div>
        </div>

        <!-- 子组件清单表格（带操作列） -->
        <div class="detail-section">
          <div class="detail-label">子组件清单</div>
          <t-table
            :data="drawerChildComponentList"
            :columns="drawerTableColumnsWithAction"
            row-key="id"
            hover
            stripe
            size="small"
            max-height="300"
            :row-class-name="getRowClassName"
          />
          <div v-if="drawerChildComponentList.length === 0" class="no-data-tip">
            暂无子组件数据
          </div>
        </div>

        <!-- 内容模块 -->
        <div class="detail-section" v-if="selectedChildContent">
          <div class="detail-label">内容</div>
          <div class="content-module">
            <div class="content-header">
              <span class="content-title">{{ selectedChildName }}</span>
              <t-button size="small" variant="outline" @click="openChildHtmlInNewWindow">
                <template #icon><t-icon name="jump" /></template>
                新窗口打开
              </t-button>
              <!-- <t-button size="small" variant="text" @click="clearSelectedContent">
                <t-icon name="close" />
              </t-button> -->
            </div>
            <div class="content-body">
              <div v-if="contentLoading" class="content-loading">
                <t-loading size="small" text="加载内容中..." />
              </div>
              <div v-else-if="isChildHtmlContent" class="html-description-container">
                <!-- <div class="html-description-toolbar">
                  <t-button size="small" variant="outline" @click="openChildHtmlInNewWindow">
                    <template #icon><t-icon name="jump" /></template>
                    新窗口打开
                  </t-button>
                </div> -->
                <div class="html-description-content" v-html="processedChildContent"></div>
              </div>
              <div v-else class="content-text">
                {{ selectedChildContent }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="jsx">
import { onBeforeUnmount, onMounted, ref, computed, reactive, watch, nextTick } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const user = useUserStore();
// ============ 基础状态 ============
const treeLoading = ref(false);
const refreshLoading = ref(false);
const detailLoading = ref(false);
const graphLoading = ref(false);
const treeData = ref([]);
const expandedKeys = ref([]);
const tabValue = ref('L0');
const lastRefreshTime = ref('');
const treeAbortController = ref(null);
const showDetailOnly = ref(false);
const forceRefresh = ref(false);
const centerComponentId = ref(null);
const showButton = ref(false);
// ============ 表格相关 ============
const childComponentList = ref([]);
const drawerChildComponentList = ref([]);
const tableLoading = ref(false);

// 子组件内容相关
const selectedChildContent = ref('');
const selectedChildName = ref('');
const contentLoading = ref(false);
const isChildHtmlContent = ref(false);
const processedChildContent = ref('');

// 表格列定义（带操作列）
const drawerTableColumnsWithAction = computed(() => {
  // 判断当前选中的是否是章节节点
  const isSectionNode = selectedNode.value?.type === 'section' || 
                         selectedNode.value?.originalType === 'section' ||
                         selectedNode.value?.typeLabel === '章节';
  
  const baseColumns = [
    { 
      colKey: 'name', 
      title: '名称', 
      width: 200,
      ellipsis: true,
      cell: (h, { row }) => {
        if (row.url) {
          return h('a', {
            href: row.url,
            target: '_blank',
            style: { color: '#0052d9', textDecoration: 'none', cursor: 'pointer' },
            onMouseenter: (e) => { e.target.style.textDecoration = 'underline'; },
            onMouseleave: (e) => { e.target.style.textDecoration = 'none'; }
          }, row.name);
        }
        return row.name;
      }
    },
    { 
      colKey: 'pageStatus', 
      title: '状态', 
      width: 80,
    }
  ];
  
  // 只有章节节点才显示操作列
  if (isSectionNode) {
    return [
      ...baseColumns,
      {
        colKey: 'action',
        title: '操作',
        width: 100,
        cell: (h, { row }) => {
          return h('t-button', {
            size: 'small',
            variant: 'text',
            theme: 'primary',
            onClick: () => viewChildContent(row)
          }, '点击查看');
        }
      }
    ];
  }
  
  return baseColumns;
});

// 原表格列定义（保留用于其他地方）
const drawerTableColumns = [
  { 
    colKey: 'name', 
    title: '名称', 
    width: 280,
    ellipsis: true,
    cell: (h, { row }) => {
      if (row.url) {
        return h('a', {
          href: row.url,
          target: '_blank',
          style: { color: '#0052d9', textDecoration: 'none', cursor: 'pointer' },
          onMouseenter: (e) => { e.target.style.textDecoration = 'underline'; },
          onMouseleave: (e) => { e.target.style.textDecoration = 'none'; }
        }, row.name);
      }
      return row.name;
    }
  },
  { 
    colKey: 'pageStatus', 
    title: '状态', 
    width: 80,
  }
];

// ============ 汇聚分类常量 ============
const CATEGORY_CONFIG = {
  'module': { label: '模块', typeLabel: '模块', color: '#2ba471', bgColor: '#e6f4ea', textColor: '#0d652d', order: 1 },
  'affected_feature': { label: '特性', typeLabel: '特性', color: '#c5221f', bgColor: '#fce8e6', textColor: '#a50e0e', order: 2 },
  'section': { label: '章节', typeLabel: '章节', color: '#1967d2', bgColor: '#e8f0fe', textColor: '#174ea6', order: 3 },
  'dependent_component': { label: '依赖组件', typeLabel: '依赖组件', color: '#e37318', bgColor: '#fff3e0', textColor: '#8b4a0b', order: 4 }
};

// 获取行类名
const getRowClassName = ({ row }) => {
  if (row.status === 'deprecated') return 'deprecated-row';
  return '';
};

// 查看子组件内容
const viewChildContent = async (row) => {
  console.log('row666', row);
  selectedChildName.value = row.name;
  contentLoading.value = true;
  selectedChildContent.value = '';
  isChildHtmlContent.value = false;
  processedChildContent.value = '';
  
  try {
    // 如果子组件有 desc 字段，直接使用
    if (row.desc) {
      const isHtml = isHtmlDescription(row.desc);
      isChildHtmlContent.value = isHtml;
      
      if (isHtml) {
        // 处理HTML内容
        if (row.desc.match(/\.(html|htm)(\?.*)?$/i) || row.desc.match(/^https?:\/\//i)) {
          await loadChildHtmlContentAsync(row.desc, row.name);
        } else {
          processedChildContent.value = getProcessedHtmlContentForChild(row.desc);
          selectedChildContent.value = row.desc;
        }
      } else {
        selectedChildContent.value = row.desc;
      }
    } 
    // 如果有 URL，尝试从 URL 加载内容
    else if (row.url) {
      await loadChildHtmlContentAsync(row.url, row.name);
    }
    else {
      selectedChildContent.value = '暂无内容';
    }
  } catch (error) {
    console.error('加载子组件内容失败:', error);
    selectedChildContent.value = `加载内容失败: ${error.message}`;
  } finally {
    contentLoading.value = false;
  }
};

// 加载子组件HTML内容
const loadChildHtmlContentAsync = async (url, nodeName) => {
  try {
    let fullUrl = url;
    if (!fullUrl.match(/^https?:\/\//i) && !fullUrl.startsWith('//')) {
      fullUrl = `${SERVER_API_URL}${fullUrl}`;
    }
    
    const response = await fetch(fullUrl);
    if (!response.ok) {
      throw new Error(`加载失败: ${response.status} ${response.statusText}`);
    }
    
    let htmlText = await response.text();
    
    const bodyMatch = htmlText.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) {
      htmlText = bodyMatch[1];
    }
    
    htmlText = htmlText.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    
    processedChildContent.value = `<div class="embedded-html-content">${htmlText}</div>`;
    selectedChildContent.value = htmlText;
    isChildHtmlContent.value = true;
  } catch (error) {
    console.error('加载HTML失败:', error);
    throw error;
  }
};

// 处理子组件HTML内容
const getProcessedHtmlContentForChild = (htmlContent) => {
  if (!htmlContent) return '';
  
  let content = htmlContent;
  
  if (!content.match(/<!DOCTYPE|<\?xml|<html/i)) {
    content = content.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    content = `<div class="embedded-html-content">${content}</div>`;
  }
  
  return content;
};

// 在新窗口打开子组件HTML
const openChildHtmlInNewWindow = () => {
  if (!selectedChildContent.value) return;
  
  const fullHtml = `<!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${selectedChildName.value || 'HTML预览'}</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
        padding: 20px;
        margin: 0;
        line-height: 1.6;
        background: white;
      }
      pre {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
      }
      code {
        font-family: 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
      }
      img {
        max-width: 100%;
        height: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
      }
      th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }
      th {
        background-color: #f5f5f5;
      }
    </style>
  </head>
  <body>
    ${selectedChildContent.value}
  </body>
  </html>`;
  
  const newWindow = window.open();
  if (newWindow) {
    newWindow.document.write(fullHtml);
    newWindow.document.close();
  } else {
    MessagePlugin.warning('请允许弹出窗口以查看完整内容');
  }
};

// 清除选中的内容
const clearSelectedContent = () => {
  selectedChildContent.value = '';
  selectedChildName.value = '';
  isChildHtmlContent.value = false;
  processedChildContent.value = '';
};

// ============ 树相关 ============
const treeKeys = {
  value: 'id',
  label: 'title',
  children: 'children',
};

// ============ 明细数据 ============
const detail = ref({
  basicInfo: '',
  guardian: '',
  status: '',
  changeLog: '',
  operator: '',
  operateTime: '',
  relations: '',
  relatedComponents: [],
  relatedFeatures: [],
  qualityScore: '',
  contentCompleteness: '',
  contentStandardization: '',
  url: '',
});

// ============ 图相关状态 ============
const highlightedNodeId = ref(null);
let highlightTimer = null;
const selectedNodeId = ref(null);
const selectedNode = ref(null);
const drawerVisible = ref(false);
const graphData = ref(null);
const hasGraphData = computed(() => graphData.value && graphData.value.nodes?.length > 0);
const currentSeedNode = ref(null);

// 汇聚框节点
const categoryNodes = ref([]);
// 原始子节点数据（用于表格）
const rawChildNodes = ref([]);
// 中心组件节点
const centerNode = ref(null);

const graphEdges = ref([]);

const zoom = ref(0.7);
const panX = ref(0);
const panY = ref(0);
const svgWidth = ref(2400);
const svgHeight = ref(1600);
const flashingNodeId = ref(null);

const viewBox = computed(() => {
  const width = svgWidth.value / zoom.value;
  const height = svgHeight.value / zoom.value;
  return `${panX.value} ${panY.value} ${width} ${height}`;
});

const draggingNodeId = ref(null);
const dragOffset = reactive({ x: 0, y: 0 });
const isCanvasDragging = ref(false);
const canvasDragStart = reactive({ x: 0, y: 0 });
const nodePositions = reactive({});

// ============ 类型颜色映射 ============
const typeColorMap = {
  'component': { bg: '#fff3e0', tag: '#e37318', text: '#8b4a0b', label: '组件' },
  'dependent_component': { bg: '#fff3e0', tag: '#e37318', text: '#8b4a0b', label: '依赖组件' },
  'module': { bg: '#e6f4ea', tag: '#2ba471', text: '#0d652d', label: '模块' },
  'affected_feature': { bg: '#fce8e6', tag: '#c5221f', text: '#a50e0e', label: '特性' },
  'section': { bg: '#e8f0fe', tag: '#1967d2', text: '#174ea6', label: '章节' },
  'category_module': { bg: '#e6f4ea', tag: '#2ba471', text: '#0d652d', label: '模块' },
  'category_feature': { bg: '#fce8e6', tag: '#c5221f', text: '#a50e0e', label: '特性' },
  'category_section': { bg: '#e8f0fe', tag: '#1967d2', text: '#174ea6', label: '章节' },
  'category_dependency': { bg: '#fff3e0', tag: '#e37318', text: '#8b4a0b', label: '依赖组件' }
};

const NODE_CONFIG = {
  'component': { w: 280, h: 120, shape: 'ellipse' },
  'category_module': { w: 220, h: 80, shape: 'rect' },
  'category_feature': { w: 200, h: 80, shape: 'rect' },
  'category_section': { w: 220, h: 80, shape: 'rect' },
  'category_dependency': { w: 220, h: 80, shape: 'rect' }
};

// ============ 辅助函数 ============
const normalizeRelatedItems = (items, fallbackNames) => {
  if (Array.isArray(items)) {
    return items
      .map((item) => {
        if (typeof item === 'string') {
          return { name: item, url: '' };
        }
        if (item && typeof item === 'object') {
          return {
            name: item.name || '',
            url: item.url || '',
          };
        }
        return { name: '', url: '' };
      })
      .filter((item) => item.name);
  }

  if (Array.isArray(fallbackNames)) {
    return fallbackNames
      .map((name) => (name ? { name, url: '' } : null))
      .filter(Boolean);
  }

  return [];
};

const getTypeDisplay = (type) => {
  const map = {
    'component': '组件',
    'dependent_component': '依赖组件',
    'module': '模块',
    'affected_feature': '特性',
    'section': '章节',
    'category_module': '模块',
    'category_feature': '特性',
    'category_section': '章节',
    'category_dependency': '依赖组件'
  };
  return map[type] || type;
};

const getTypeColor = (type) => {
  const config = typeColorMap[type];
  return config ? config.tag : '#666';
};

const getTypeBgColor = (type) => {
  const config = typeColorMap[type];
  return config ? config.bg : '#f5f5f5';
};

const getTypeTextColor = (type) => {
  const config = typeColorMap[type];
  return config ? config.text : '#333';
};

const getTextWidth = (text, fontSize) => {
  let width = 0;
  for (const char of text) {
    width += /[\u4e00-\u9fa5]/.test(char) ? fontSize * 1.1 : fontSize * 0.6;
  }
  return Math.max(width, 20);
};

const getNodeStroke = (node) => {
  if (selectedNodeId.value === node.id) return '#0052d9';
  if (highlightedNodeId.value === node.id) return node.tagColor;
  return '#d0d5dd';
};

const getScopeByTab = (tab) => {
  const scopeMap = {
    'L0': 'L0',
    'L1': 'L1',
    'L2': 'L2',
    'WASON': 'WASON',
    'OSP': 'OSP'
  };
  return scopeMap[tab] || 'WASON';
};

// ============ 树数据加载 ============
const processTreeData = (nodes) => {
  if (!nodes || !Array.isArray(nodes)) return [];
  return nodes.map(node => ({
    id: node.id,
    title: node.title,
    nodeType: node.nodeType,
    level: node.level,
    url: node.url,
    spaceId: node.spaceId,
    hasChildren: node.hasChildren,
    children: node.children ? processTreeData(node.children) : []
  }));
};

const loadTree = async (scope = tabValue.value) => {
  if (treeAbortController.value) {
    treeAbortController.value.abort();
  }
  treeAbortController.value = new AbortController();

  treeLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_component_tree`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: treeAbortController.value.signal,
      body: JSON.stringify({
        tab: scope,
        domain: scope,
        maxLevel: 4,
      }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200 || !res.data?.root) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }
    const processedTree = processTreeData([res.data.root]);
    treeData.value = processedTree;
    
    if (res.data.root.children) {
      expandedKeys.value = [res.data.root.id];
      res.data.root.children.forEach(child => {
        if (child.children?.length > 0) {
          expandedKeys.value.push(child.id);
        }
      });
    }
  } catch (e) {
    if (e?.name === 'AbortError') {
      return;
    }
    MessagePlugin.error(`读取组件树失败：${e.message || e}`);
    treeData.value = [];
  } finally {
    if (treeAbortController.value?.signal?.aborted) {
      return;
    }
    treeLoading.value = false;
  }
};

const refreshTree = async () => {
  refreshLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_component_tree_refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tab: tabValue.value,
        domain: tabValue.value,
        maxLevel: 4,
      }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }
    lastRefreshTime.value = res.data?.refreshedAt || '';
    MessagePlugin.success('组件树缓存刷新成功');
    await loadTree(tabValue.value);
  } catch (e) {
    MessagePlugin.error(`刷新组件树失败：${e.message || e}`);
  } finally {
    refreshLoading.value = false;
  }
};

// ============ 明细数据加载 ============
const loadDetail = async (node) => {
  detailLoading.value = true;
  tableLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_component_detail`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        spaceId: node.spaceId,
        contentId: node.id,
        title: node.title,
        nodeType: node.nodeType,
        url: node.url,
      }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }
    const data = res.data || {};
    detail.value = {
      basicInfo: data.basicInfo?.name || node.title || '',
      guardian: data.guardian || '',
      status: data.status || '',
      changeLog: data.changeLog || '',
      operator: data.operator || '',
      operateTime: data.operateTime || '',
      relations: data.relations || '',
      relatedComponents: normalizeRelatedItems(data.relatedComponents, data.relatedComponentNames),
      relatedFeatures: normalizeRelatedItems(data.relatedFeatures, data.relatedFeatureNames),
      qualityScore: data.qualityScore || '',
      contentCompleteness: data.contentCompleteness || '',
      contentStandardization: data.contentStandardization || '',
      url: `https://i.zte.com.cn/index/ispace/#/space/${data.basicInfo?.spaceId}/wiki/page/${data.basicInfo?.contentId}/view`
    };

    if (rawChildNodes.value.length > 0) {
      childComponentList.value = rawChildNodes.value.map(child => ({
        id: child.id,
        name: child.name,
        type: child.typeLabel || child.type,
        level: child.level || 1,
        url: child.url,
        pageStatus: child.pageStatus,
        desc: child.desc
      }));
    } else {
      childComponentList.value = [];
    }
  } catch (e) {
    MessagePlugin.error(`读取详情失败：${e.message || e}`);
  } finally {
    detailLoading.value = false;
    tableLoading.value = false;
  }
};

// ============ 图数据加载 ============
const loadGraphData = async (componentId, scope) => {
  graphLoading.value = true;
  graphData.value = null;
  showDetailOnly.value = false;
  categoryNodes.value = [];
  rawChildNodes.value = [];
  centerNode.value = null;
  Object.keys(nodePositions).forEach(key => {
    delete nodePositions[key];
  });
  
  try {
    console.log('加载图数据，组件ID:', componentId, '范围:', scope);
    
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_component_graph_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        seedComponentId: componentId,
        scope: scope,
        maxDepth: 2,
        forceRefresh: forceRefresh.value
      }),
    });
    const res = await resp.json();
    
    console.log('图数据响应:', res);
    
    if (resp.ok && res.code === 200 && res.data?.nodes?.length > 0) {
      console.log('节点数据:', res.data.nodes);
      console.log('边数据:', res.data.edges);
      graphData.value = res.data;
      buildGraphFromData(res.data);
    } else {
      console.warn('图数据为空或请求失败:', res);
      graphData.value = null;
      showDetailOnly.value = true;
    }
  } catch (error) {
    console.error('加载图数据失败:', error);
    graphData.value = null;
    showDetailOnly.value = true;
  } finally {
    graphLoading.value = false;
  }
};

// 构建图数据
const buildGraphFromData = (data) => {
  if (!data.nodes || !data.nodes.length) return;
  
  const seedComponentName = data.seedComponentName || '中心组件';
  
  centerComponentId.value = 'center_component';
  centerNode.value = {
    id: 'center_component',
    name: seedComponentName,
    originalType: 'center',
    type: 'component',
    typeLabel: '组件',
    desc: '',
    url: '',
    shape: 'ellipse',
    width: 280,
    height: 120,
    level: 0,
    count: 0
  };
  
  let childNodes = data.nodes;
  
  console.log('子节点数量:', childNodes.length);
  
  if (childNodes.length === 0) {
    console.warn('未找到子节点');
    showDetailOnly.value = true;
    return;
  }
  
  rawChildNodes.value = childNodes.map(child => ({
    id: child.id,
    name: child.name,
    type: child.type,
    typeLabel: getTypeDisplay(child.type),
    desc: child.desc || '',
    url: child.url || '',
    level: child.level,
    parentComponentId: child.parentComponentId,
    pageStatus: child.pageStatus,
  }));
  
  // 按类型汇聚子节点
  const categorizedChildren = {
    'module': [],
    'affected_feature': [],
    'section': [],
    'dependent_component': []
  };
  
  childNodes.forEach(child => {
    let type = child.type;
    let categoryType = null;
    
    if (type === 'module' || type === 'Module') {
      categoryType = 'module';
    } 
    else if (type === 'affected_feature' || type === 'feature' || type === '特性') {
      categoryType = 'affected_feature';
    }
    else if (type === 'section' || type === 'Section' || type === '章节') {
      categoryType = 'section';
    }
    else if (type === 'component') {
      categoryType = 'dependent_component';
    }
    else {
      console.warn('未知类型:', type, '归类为模块');
      categoryType = 'module';
    }
    
    if (categoryType && categorizedChildren[categoryType]) {
      categorizedChildren[categoryType].push({
        id: child.id,
        name: child.name,
        type: child.type,
        typeLabel: categoryType === 'dependent_component' ? '依赖组件' : getTypeDisplay(categoryType),
        desc: child.desc || '',
        url: child.url || '',
        level: child.level,
        parentComponentId: child.parentComponentId,
        pageStatus: child.pageStatus,
      });
    }
  });
  
  // 创建汇聚框节点
  const categories = [];
  Object.entries(categorizedChildren).forEach(([type, children]) => {
    if (children.length > 0) {
      const config = CATEGORY_CONFIG[type];
      if (config) {
        categories.push({
          id: `category_${type}`,
          name: config.label,
          originalType: type,
          type: `category_${type === 'dependent_component' ? 'dependency' : type}`,
          typeLabel: config.label,
          desc: `共 ${children.length} 个${config.label}`,
          url: '',
          shape: 'rect',
          width: NODE_CONFIG[`category_${type === 'dependent_component' ? 'dependency' : type}`]?.w || 220,
          height: NODE_CONFIG[`category_${type === 'dependent_component' ? 'dependency' : type}`]?.h || 80,
          level: 1,
          count: children.length,
          children: children,
          bgColor: config.bgColor,
          tagColor: config.color,
          textColor: config.textColor
        });
      }
    }
  });
  
  categories.sort((a, b) => {
    const orderA = CATEGORY_CONFIG[a.originalType]?.order || 999;
    const orderB = CATEGORY_CONFIG[b.originalType]?.order || 999;
    return orderA - orderB;
  });
  
  categoryNodes.value = categories;
  
  // 创建连线
  const edges = [];
  categories.forEach((cat) => {
    let label = '';
    switch (cat.originalType) {
      case 'module':
        label = '包含模块';
        break;
      case 'affected_feature':
        label = '关联特性';
        break;
      case 'section':
        label = '包含章节';
        break;
      case 'dependent_component':
        label = '依赖组件';
        break;
      default:
        label = '包含模块';
    }
    
    edges.push({
      id: `${centerNode.value.id}_to_${cat.id}`,
      source: centerNode.value.id,
      target: cat.id,
      relationType: 'contains',
      relationLabel: label,
      categoryType: cat.originalType
    });
  });
  
  graphEdges.value = edges;
  initializeGraphPositions();
  
  nextTick(() => {
    centerGraph();
  });
};

const initializeGraphPositions = () => {
  Object.keys(nodePositions).forEach(key => {
    delete nodePositions[key];
  });
  
  if (!centerNode.value) return;
  
  const centerX = 900;
  const centerY = 350;
  nodePositions[centerNode.value.id] = { x: centerX, y: centerY };
  
  const categories = categoryNodes.value;
  if (categories.length === 0) return;
  
  const radius = 350;
  const angleStep = (Math.PI * 2) / categories.length;
  let startAngle = -Math.PI / 2;
  
  if (categories.length === 2) {
    startAngle = 0;
  } else if (categories.length === 3) {
    startAngle = -Math.PI / 2;
  } else if (categories.length === 4) {
    startAngle = -Math.PI / 4;
  } else {
    startAngle = -Math.PI / 2;
  }
  
  categories.forEach((cat, idx) => {
    let angle;
    if (categories.length === 2) {
      angle = idx === 0 ? -Math.PI / 2 : Math.PI / 2;
    } else if (categories.length === 3) {
      if (idx === 0) angle = -Math.PI / 2;
      else if (idx === 1) angle = Math.PI / 6;
      else angle = -Math.PI * 5 / 6;
    } else {
      angle = startAngle + angleStep * idx;
    }
    
    const x = centerX + radius * Math.cos(angle) - cat.width / 2;
    const y = centerY + radius * Math.sin(angle) - cat.height / 2;
    nodePositions[cat.id] = { x, y };
  });
};

const allNodes = computed(() => {
  const nodes = [];
  if (centerNode.value) {
    nodes.push({
      ...centerNode.value,
      typeX: centerNode.value.width / 2 - getTextWidth(centerNode.value.typeLabel, 11) / 2 - 8,
      typeWidth: getTextWidth(centerNode.value.typeLabel, 11) + 16,
      textY: centerNode.value.height / 2 + 5,
      bgColor: getTypeBgColor(centerNode.value.type),
      tagColor: getTypeColor(centerNode.value.type),
      textColor: getTypeTextColor(centerNode.value.type)
    });
  }
  
  categoryNodes.value.forEach(cat => {
    nodes.push({
      ...cat,
      typeX: cat.width / 2 - getTextWidth(cat.typeLabel, 11) / 2 - 8,
      typeWidth: getTextWidth(cat.typeLabel, 11) + 16,
      textY: cat.height / 2 + 5,
    });
  });
  
  return nodes;
});

const calcEdge = (fromId, toId, labelText, curveOffsetX = 0, curveOffsetY = 0) => {
  const from = allNodes.value.find(n => n.id === fromId);
  const to = allNodes.value.find(n => n.id === toId);
  if (!from || !to) return null;

  const fromPos = nodePositions[fromId] || { x: from.x, y: from.y };
  const toPos = nodePositions[toId] || { x: to.x, y: to.y };

  const fx = fromPos.x + from.width / 2;
  const fy = fromPos.y + from.height / 2;
  const tx = toPos.x + to.width / 2;
  const ty = toPos.y + to.height / 2;

  const dx = tx - fx;
  const dy = ty - fy;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const nx = dx / dist;
  const ny = dy / dist;

  const fromRx = from.shape === 'ellipse' ? from.width / 2 * 0.85 : from.width / 2 * 0.9;
  const fromRy = from.shape === 'ellipse' ? from.height / 2 * 0.85 : from.height / 2 * 0.9;
  const toRx = to.shape === 'ellipse' ? to.width / 2 * 0.9 : to.width / 2;
  const toRy = to.shape === 'ellipse' ? to.height / 2 * 0.9 : to.height / 2;

  const startX = fx + nx * fromRx;
  const startY = fy + ny * fromRy;
  const endX = tx - nx * toRx * 1.1;
  const endY = ty - ny * toRy * 1.1;

  const midX = (startX + endX) / 2 + curveOffsetX;
  const midY = (startY + endY) / 2 + curveOffsetY;

  return {
    path: `M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`,
    labelX: midX,
    labelY: midY,
    labelWidth: getTextWidth(labelText, 10) + 16,
    highlighted: highlightedNodeId.value === fromId || highlightedNodeId.value === toId
  };
};

const categoryEdges = computed(() => {
  const edges = [];
  graphEdges.value.forEach((edge, idx) => {
    const targetCat = categoryNodes.value.find(c => c.id === edge.target);
    if (targetCat) {
      let label = '';
      let bgColor = '#e6f4ea';
      let strokeColor = '#2ba471';
      let textColor = '#137333';
      let arrowType = 'green';
      
      switch (targetCat.originalType) {
        case 'module':
          label = '包含模块';
          bgColor = '#e6f4ea';
          strokeColor = '#2ba471';
          textColor = '#137333';
          arrowType = 'green';
          break;
        case 'affected_feature':
          label = '关联特性';
          bgColor = '#fce8e6';
          strokeColor = '#c5221f';
          textColor = '#a50e0e';
          arrowType = 'red';
          break;
        case 'section':
          label = '包含章节';
          bgColor = '#e8f0fe';
          strokeColor = '#1967d2';
          textColor = '#174ea6';
          arrowType = 'blue';
          break;
        case 'dependent_component':
          label = '依赖组件';
          bgColor = '#fff3e0';
          strokeColor = '#e37318';
          textColor = '#8b4a0b';
          arrowType = 'orange';
          break;
        default:
          label = '包含模块';
      }
      
      const offsetX = idx * 10 - 15;
      const offsetY = -15 + idx * 5;
      const edgeCalc = calcEdge(edge.source, edge.target, label, offsetX, offsetY);
      if (edgeCalc) {
        edges.push({ 
          id: edge.id, 
          ...edgeCalc,
          label,
          bgColor,
          strokeColor,
          textColor,
          arrowType
        });
      }
    }
  });
  return edges;
});

const getMarkerEnd = (arrowType, highlighted) => {
  const suffix = highlighted ? '-highlight' : '';
  switch (arrowType) {
    case 'green':
      return `url(#arrowhead-green${suffix})`;
    case 'orange':
      return `url(#arrowhead-orange${suffix})`;
    case 'red':
      return `url(#arrowhead-red${suffix})`;
    case 'blue':
      return `url(#arrowhead-blue${suffix})`;
    default:
      return `url(#arrowhead-green${suffix})`;
  }
};

// ============ 事件处理 ============
const onTabChange = (value) => {
  tabValue.value = value;
  graphData.value = null;
  categoryNodes.value = [];
  centerNode.value = null;
  showDetailOnly.value = false;
  Object.keys(nodePositions).forEach(key => {
    delete nodePositions[key];
  });
  currentSeedNode.value = null;
  loadTree(value);
};

const onTreeNodeClick = async(context) => {
  const node = context?.node?.data;
  if (!node) return;
  
  loadDetail(node);
  
  const shouldLoadGraph = (
    (tabValue.value === 'WASON') && 
    (node.level === 2 || node.level === 3)
  ) || (node.level === 2 && tabValue.value !== 'WASON' && tabValue.value !== 'OSP');
  
  if (shouldLoadGraph) {
    currentSeedNode.value = node;
    const scope = getScopeByTab(tabValue.value);
    loadGraphData(node.id, scope);
  } else {
    graphData.value = null;
    categoryNodes.value = [];
    centerNode.value = null;
    showDetailOnly.value = true;
  }
};

const highlightNode = (nodeId) => {
  if (highlightTimer) clearTimeout(highlightTimer);
  highlightTimer = setTimeout(() => {
    highlightedNodeId.value = nodeId;
  }, 50);
};

const clearHighlight = () => {
  if (highlightTimer) clearTimeout(highlightTimer);
  highlightTimer = setTimeout(() => {
    highlightedNodeId.value = null;
  }, 50);
};

const selectNode = (node) => {
  let fullNode = { ...node };
  if (!fullNode.url) fullNode.url = '';
  
  // 清除之前选中的子组件内容
  clearSelectedContent();
  
  if (node.id.startsWith('category_')) {
    drawerChildComponentList.value = (node.children || []).map(child => ({
      ...child,
    }));
  } else {
    drawerChildComponentList.value = [];
  }
  
  selectedNode.value = fullNode;
  selectedNodeId.value = node.id;
  
  isHtmlFullscreen.value = false;
  drawerVisible.value = true;
  
  if (node.desc && isHtmlDescription(node.desc)) {
    if (node.desc.match(/\.(html|htm)(\?.*)?$/i) || node.desc.match(/^https?:\/\//i)) {
      setTimeout(() => {
        loadHtmlContentAsync(node.desc, node.name);
      }, 100);
    }
  }
};

const handleDrawerClose = () => {
  clearSelectedContent();
  // 不需要重置 drawerChildComponentList，因为下次打开时会重新设置
};

const onSvgMouseDown = (e) => {
  if (e.target.closest('.nodes-group g')) return;
  isCanvasDragging.value = true;
  canvasDragStart.x = e.clientX;
  canvasDragStart.y = e.clientY;
};

const onSvgMouseMove = (e) => {
  if (draggingNodeId.value) {
    const rect = e.currentTarget.getBoundingClientRect();
    const svgX = (e.clientX - rect.left) / zoom.value + panX.value;
    const svgY = (e.clientY - rect.top) / zoom.value + panY.value;
    
    const node = allNodes.value.find(n => n.id === draggingNodeId.value);
    if (node) {
      nodePositions[draggingNodeId.value] = {
        x: svgX - dragOffset.x,
        y: svgY - dragOffset.y
      };
    }
    return;
  }
  
  if (isCanvasDragging.value) {
    const dx = e.clientX - canvasDragStart.x;
    const dy = e.clientY - canvasDragStart.y;
    panX.value -= dx * (1 / zoom.value);
    panY.value -= dy * (1 / zoom.value);
    canvasDragStart.x = e.clientX;
    canvasDragStart.y = e.clientY;
  }
};

const onSvgMouseUp = () => {
  draggingNodeId.value = null;
  isCanvasDragging.value = false;
};

const onNodeMouseDown = (e, nodeId) => {
  e.stopPropagation();
  if (e.target.closest('.link-indicator')) return;
  
  const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect();
  const svgX = (e.clientX - rect.left) / zoom.value + panX.value;
  const svgY = (e.clientY - rect.top) / zoom.value + panY.value;
  
  const pos = nodePositions[nodeId];
  if (pos) {
    dragOffset.x = svgX - pos.x;
    dragOffset.y = svgY - pos.y;
  }
  draggingNodeId.value = nodeId;
};

const onWheel = (e) => {
  e.preventDefault();
  const delta = e.deltaY > 0 ? -0.05 : 0.05;
  const newZoom = Math.min(2, Math.max(0.3, zoom.value + delta));
  
  const rect = e.currentTarget.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  const scale = newZoom / zoom.value;
  panX.value = mouseX - scale * (mouseX - panX.value);
  panY.value = mouseY - scale * (mouseY - panY.value);
  zoom.value = newZoom;
};

const zoomIn = () => {
  zoom.value = Math.min(2, zoom.value + 0.1);
};

const zoomOut = () => {
  zoom.value = Math.max(0.3, zoom.value - 0.1);
};

const centerGraph = () => {
  if (allNodes.value.length === 0) return;
  
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  allNodes.value.forEach(node => {
    const pos = nodePositions[node.id] || { x: node.x, y: node.y };
    minX = Math.min(minX, pos.x);
    minY = Math.min(minY, pos.y);
    maxX = Math.max(maxX, pos.x + node.width);
    maxY = Math.max(maxY, pos.y + node.height);
  });
  const contentWidth = maxX - minX;
  const contentHeight = maxY - minY;
  const padding = 80;
  const targetZoom = Math.min(1.2, Math.min(
    svgWidth.value / (contentWidth + padding * 2),
    svgHeight.value / (contentHeight + padding * 2)
  ));
  zoom.value = targetZoom * 0.9;
  panX.value = minX - padding;
  panY.value = minY - padding;
};

const autoLayout = () => {
  if (centerNode.value) {
    initializeGraphPositions();
    MessagePlugin.success('已恢复自动布局');
  } else {
    MessagePlugin.warning('暂无图数据');
  }
};

const expandAll = () => {
  const getAllNodeIds = (nodes) => {
    let ids = [];
    nodes.forEach(node => {
      ids.push(node.id);
      if (node.children) {
        ids = ids.concat(getAllNodeIds(node.children));
      }
    });
    return ids;
  };
  expandedKeys.value = getAllNodeIds(treeData.value);
};

const collapseAll = () => {
  expandedKeys.value = [];
};

const getNodeRelationPaths = (nodeId) => {
  const paths = [];
  graphEdges.value.forEach(edge => {
    if (edge.source === nodeId) {
      const targetNode = allNodes.value.find(n => n.id === edge.target);
      if (targetNode) {
        paths.push(`${edge.relationLabel || '关联'} → ${targetNode.name}`);
      }
    }
    if (edge.target === nodeId) {
      const sourceNode = allNodes.value.find(n => n.id === edge.source);
      if (sourceNode) {
        paths.push(`${sourceNode.name} → ${edge.relationLabel || '关联'}`);
      }
    }
  });
  return paths;
};

const openUrl = (url) => {
  if (!url) {
    MessagePlugin.warning('该节点暂无关联链接');
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
};

const copyUrl = async (url) => {
  if (!url) {
    MessagePlugin.warning('该节点暂无关联链接');
    return;
  }
  try {
    await navigator.clipboard.writeText(url);
    MessagePlugin.success('链接已复制到剪贴板');
  } catch (err) {
    const textarea = document.createElement('textarea');
    textarea.value = url;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    MessagePlugin.success('链接已复制到剪贴板');
  }
};

// ============ 全屏相关 ============
const isFullscreen = ref(false);

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  
  nextTick(() => {
    setTimeout(() => {
      if (isFullscreen.value) {
        centerGraph();
      }
    }, 100);
  });
};

watch(isFullscreen, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});

const onKeyDown = (e) => {
  if (e.key === 'Escape' && isFullscreen.value) {
    isFullscreen.value = false;
  }
};

// ============ 生命周期 ============
onMounted(() => {
  if(user.userInfo.name === '10210415' || user.userInfo.name === '10336097' || user.userInfo.name === '10305454' || user.userInfo.name === '10336606'){
    showButton.value = true;
  }
  loadTree();
  window.addEventListener('keydown', onKeyDown);
});

onBeforeUnmount(() => {
  if (treeAbortController.value) {
    treeAbortController.value.abort();
  }
  window.removeEventListener('keydown', onKeyDown);
  document.body.style.overflow = '';
  if (highlightTimer) clearTimeout(highlightTimer);
});

// ============ HTML预览相关 ============
const isHtmlFullscreen = ref(false);

const isHtmlDescription = (desc) => {
  if (!desc || typeof desc !== 'string') return false;
  
  const htmlPathPattern = /\.(html|htm)(\?.*)?$/i;
  if (htmlPathPattern.test(desc)) {
    return true;
  }
  
  const htmlTagPattern = /<(html|body|div|span|p|a|img|table|ul|ol|li|h[1-6]|br|hr|script|style|link|meta|iframe)[^>]*>/i;
  if (htmlTagPattern.test(desc)) {
    return true;
  }
  
  const htmlDocPattern = /<!DOCTYPE\s+html|<\?xml|<html/i;
  if (htmlDocPattern.test(desc)) {
    return true;
  }
  
  const htmlStylePattern = /style\s*=|class\s*=|font-family|background-color|margin|padding/i;
  if (htmlStylePattern.test(desc) && desc.length > 50) {
    return true;
  }
  
  return false;
};

const getProcessedHtmlContent = (htmlContent) => {
  if (!htmlContent) return '';
  
  if (htmlContent.match(/\.(html|htm)(\?.*)?$/i) || htmlContent.match(/^https?:\/\//i)) {
    loadHtmlContentAsync(htmlContent);
    return '<div class="html-loading">加载HTML内容中...</div>';
  }
  
  let content = htmlContent;
  
  if (!content.match(/<!DOCTYPE|<\?xml|<html/i)) {
    content = content.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    content = `<div class="embedded-html-content">${content}</div>`;
  }
  
  return content;
};

const loadHtmlContentAsync = async (url, nodeName) => {
  try {
    let fullUrl = url;
    if (!fullUrl.match(/^https?:\/\//i) && !fullUrl.startsWith('//')) {
      fullUrl = `${SERVER_API_URL}${fullUrl}`;
    }
    
    const response = await fetch(fullUrl);
    if (!response.ok) {
      throw new Error(`加载失败: ${response.status} ${response.statusText}`);
    }
    
    let htmlText = await response.text();
    
    const bodyMatch = htmlText.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) {
      htmlText = bodyMatch[1];
    }
    
    htmlText = htmlText.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    
    if (selectedNode.value && selectedNode.value.desc === url) {
      const htmlContainer = document.querySelector('.html-description-content');
      if (htmlContainer) {
        htmlContainer.innerHTML = `<div class="embedded-html-content">${htmlText}</div>`;
      }
    }
  } catch (error) {
    console.error('加载HTML失败:', error);
    const errorHtml = `<div class="html-error">加载HTML失败: ${error.message}<br>原始路径: ${url}</div>`;
    
    if (selectedNode.value && selectedNode.value.desc === url) {
      const htmlContainer = document.querySelector('.html-description-content');
      if (htmlContainer) {
        htmlContainer.innerHTML = errorHtml;
      }
    }
  }
};

const openHtmlInNewWindow = (htmlContent, title) => {
  if (!htmlContent) return;
  
  if (htmlContent.match(/\.(html|htm)(\?.*)?$/i) || htmlContent.match(/^https?:\/\//i)) {
    let url = htmlContent;
    if (!url.match(/^https?:\/\//i) && !url.startsWith('//')) {
      url = `${SERVER_API_URL}${url}`;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
    return;
  }
  
  const fullHtml = `<!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title || 'HTML预览'}</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
        padding: 20px;
        margin: 0;
        line-height: 1.6;
        background: white;
      }
      pre {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
      }
      code {
        font-family: 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
      }
      img {
        max-width: 100%;
        height: auto;
      }
      table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
      }
      th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }
      th {
        background-color: #f5f5f5;
      }
    </style>
  </head>
  <body>
    ${htmlContent}
  </body>
  </html>`;
  
  const newWindow = window.open();
  if (newWindow) {
    newWindow.document.write(fullHtml);
    newWindow.document.close();
  } else {
    MessagePlugin.warning('请允许弹出窗口以查看完整内容');
  }
};

const toggleHtmlFullscreen = () => {
  isHtmlFullscreen.value = !isHtmlFullscreen.value;
  
  if (isHtmlFullscreen.value) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
};
</script>

<style scoped>
/* 样式保持与原代码相同，新增内容模块样式 */
.component-main {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F5F5F5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
}

.toolbar {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-right {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.refresh-time {
  color: #666;
  font-size: 13px;
}

.main-layout {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 0 16px 16px;
  overflow: hidden;
}

/* ============ 左侧树 ============ */
.tree-sidebar {
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
}

.tree-header {
  padding: 12px 16px;
  border-bottom: 1px solid #eef2f6;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #1f2d3d;
}

.tree-action-btn {
  font-size: 12px;
}

.tree-action-btn:first-of-type {
  margin-left: auto;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-content::-webkit-scrollbar {
  width: 4px;
}

.tree-content::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}

.tree-loading, .tree-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #98a2b3;
}

/* ============ 右侧内容区 ============ */
.right-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: white;
  border-radius: 12px 12px 0 0;
  border: 1px solid #e5e7eb;
  border-bottom: 1px solid #eef2f6;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #1f2d3d;
}

.section-actions {
  display: flex;
  gap: 8px;
}

/* ============ 流程图区域 ============ */
.flowchart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  max-height: 700px;
  overflow: hidden;
}

.flowchart-container {
  flex: 1;
  background: white;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.canvas-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #fafbfc;
  background-image: radial-gradient(#e5e7eb 0.5px, transparent 0.5px);
  background-size: 32px 32px;
}

.flowchart-svg {
  display: block;
  cursor: grab;
}

.flowchart-svg:active {
  cursor: grabbing;
}

.edge-path {
  transition: stroke 0.3s, stroke-width 0.3s;
}

.nodes-group g {
  cursor: grab;
  transition: filter 0.2s ease;
}

.nodes-group g:hover {
  filter: drop-shadow(0 4px 12px rgba(0, 82, 217, 0.18));
}

.nodes-group g:active {
  cursor: grabbing;
}

.nodes-group g.selected .node-shape {
  stroke: #0052d9 !important;
  stroke-width: 2.5 !important;
  filter: drop-shadow(0 4px 16px rgba(0, 82, 217, 0.25));
}

.nodes-group g.highlight-flash {
  animation: flash 0.8s ease-in-out;
}

.nodes-group g.dragging {
  filter: drop-shadow(0 8px 24px rgba(0, 82, 217, 0.3));
}

.nodes-group g.dragging .node-shape {
  stroke: #0052d9 !important;
  stroke-width: 2.5 !important;
}

@keyframes flash {
  0%, 100% { filter: drop-shadow(0 0 0 rgba(0, 82, 217, 0)); }
  50% { filter: drop-shadow(0 0 20px rgba(0, 82, 217, 0.5)); }
}

.link-indicator {
  cursor: pointer;
}

.link-indicator:hover circle {
  fill: #e8f0fe;
}

.drag-hint {
  pointer-events: none;
}

.zoom-controls {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: white;
  padding: 6px 8px;
  border-radius: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
}

.zoom-level {
  font-size: 13px;
  min-width: 46px;
  text-align: center;
  color: #667085;
  font-variant-numeric: tabular-nums;
}

.drag-tip {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.graph-loading, .graph-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #98a2b3;
}

.graph-empty p {
  margin-top: 12px;
  font-size: 14px;
}

/* ============ 明细数据区域 ============ */
.detail-section {
  display: flex;
  flex-direction: column;
  min-height: 20px;
  max-height: 1000px;
  overflow: hidden;
}

.detail-container {
  flex: 1;
  background: white;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 12px 12px;
  overflow-y: auto;
  padding: 16px;
}

.detail-container::-webkit-scrollbar {
  width: 4px;
}

.detail-container::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.url-link {
  word-wrap: break-word;
  word-break: break-all;
  display: inline-block;
  max-width: 100%;
}

.related-link-list {
  line-height: 1.8;
  word-break: break-all;
}

.no-data-tip {
  padding: 20px;
  text-align: center;
  color: #98a2b3;
  font-size: 13px;
}

/* ============ 抽屉内容 ============ */
.node-detail .detail-section {
  margin-bottom: 24px;
  max-height: none;
  overflow: visible;
}

.node-detail .detail-label {
  font-size: 12px;
  font-weight: 500;
  color: #98a2b3;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.node-detail .detail-value {
  font-size: 13px;
  color: #344054;
  line-height: 1.5;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.url-container {
  background: #f8f9fb;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.url-display {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.url-icon {
  color: #0052d9;
  flex-shrink: 0;
}

.url-text {
  font-size: 12px;
  color: #0052d9;
  word-break: break-all;
  line-height: 1.5;
}

.url-actions {
  display: flex;
  gap: 8px;
}

.relation-paths .path-item {
  font-size: 13px;
  color: #344054;
  padding: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #f0f1f3;
}

.relation-paths .path-item:last-child {
  border-bottom: none;
}

.relation-paths .no-path {
  font-size: 13px;
  color: #98a2b3;
  padding: 8px 0;
  font-style: italic;
}

/* ============ 内容模块样式 ============ */
.content-module {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f8f9fb;
  border-bottom: 1px solid #e5e7eb;
}

.content-title {
  font-weight: 600;
  font-size: 13px;
  color: #1f2d3d;
}

.content-body {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.content-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
}

.content-text {
  font-size: 13px;
  color: #344054;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ============ 全屏样式 ============ */
.flowchart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: 700px;
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
}

.fullscreen-chart {
  position: fixed;
  top: 70px;
  left: 30px;
  right: 30px;
  bottom: 30px;
  width: auto;
  height: auto;
  z-index: 1001;
  background-color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.fullscreen-chart .zoom-controls {
  bottom: 20px;
  right: 20px;
}

/* ============ HTML描述样式 ============ */
.html-description-container {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.html-description-toolbar {
  padding: 8px 12px;
  background: #f8f9fb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.html-description-content {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  line-height: 1.6;
  font-size: 13px;
  color: #344054;
}

.html-description-content.html-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  max-height: none;
  padding: 20px;
  background: white;
  overflow-y: auto;
}

.embedded-html-content {
  font-family: inherit;
}

.embedded-html-content h1,
.embedded-html-content h2,
.embedded-html-content h3,
.embedded-html-content h4,
.embedded-html-content h5,
.embedded-html-content h6 {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.embedded-html-content p {
  margin-bottom: 12px;
}

.embedded-html-content ul,
.embedded-html-content ol {
  margin: 8px 0;
  padding-left: 24px;
}

.embedded-html-content li {
  margin: 4px 0;
}

.embedded-html-content a {
  color: #0052d9;
  text-decoration: none;
}

.embedded-html-content a:hover {
  text-decoration: underline;
}

.embedded-html-content img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.embedded-html-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.embedded-html-content th,
.embedded-html-content td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.embedded-html-content th {
  background: #f8f9fb;
  font-weight: 600;
}

.embedded-html-content code {
  font-family: 'Courier New', monospace;
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.embedded-html-content pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.embedded-html-content pre code {
  background: none;
  padding: 0;
}

.embedded-html-content blockquote {
  margin: 12px 0;
  padding: 8px 16px;
  border-left: 4px solid #0052d9;
  background: #f8f9fb;
  color: #666;
}

.html-loading,
.html-error {
  padding: 40px;
  text-align: center;
  color: #98a2b3;
}

.html-error {
  color: #d32f2f;
}

.html-description-content::-webkit-scrollbar {
  width: 6px;
}

.html-description-content::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 3px;
}

.html-description-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

/* 抽屉表格样式 */
.detail-section .t-table {
  font-size: 12px;
}

.detail-section .t-table a {
  color: #0052d9;
  text-decoration: none;
}

.detail-section .t-table a:hover {
  text-decoration: underline;
}

.deprecated-row {
  opacity: 0.7;
  background-color: #fce8e6 !important;
}

@media (max-width: 1200px) {
  .fullscreen-chart {
    left: 20px;
    right: 20px;
    top: 20px;
    bottom: 20px;
  }

  .html-description-content {
    max-height: 300px;
  }
  
  .html-description-toolbar {
    flex-wrap: wrap;
  }
}
</style>
