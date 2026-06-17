<template>
  <div class="requirements-main">
    <t-tabs v-model="tabValue" theme="card" @change="onTabChange">
      <t-tab-panel value="智能OTN" label="智能OTN" :destroy-on-hide="false" />
      <t-tab-panel value="M721" label="M721" :destroy-on-hide="false" />
      <t-tab-panel value="NTON" label="NTON" :destroy-on-hide="false" />
      <t-tab-panel value="SRV" label="SRV" :destroy-on-hide="false" />
    </t-tabs>

    <div class="toolbar">
      <t-popconfirm
        theme="default"
        content="确认同步数据吗?"
        @confirm="refreshTree"
      >
        <t-button v-show="showButton" theme="primary" variant="outline" size="small" :loading="refreshLoading">
          需求树同步数据
        </t-button>
      </t-popconfirm>
      <span class="refresh-time">最近刷新时间：{{ lastRefreshTime || '未刷新' }}</span>

      <span v-show="showButton" class="refresh-time">是否拉取新数据：
        <t-switch v-model="forceRefresh"/>
      </span>

      <div class="toolbar-right">
        <t-tag theme="primary" variant="light" size="small">包含关系</t-tag>
        <t-tag theme="warning" variant="light" size="small">波及关系</t-tag>
        <t-tag theme="success" variant="light" size="small">关联关系</t-tag>
        <t-tag theme="danger" variant="light" size="small">校验关系</t-tag>
      </div>
    </div>

    <div class="main-layout" ref="layoutRef">
      <!-- 左侧树形目录 -->
      <div class="tree-sidebar" :style="{ width: sidebarWidth + 'px' }">
        <div class="tree-header">
          <t-icon name="view-list" />
          <span>需求导航树</span>
          <t-button size="small" variant="text" @click="expandAll" class="tree-action-btn">全部展开</t-button>
          <t-button size="small" variant="text" @click="collapseAll" class="tree-action-btn">全部收起</t-button>
        </div>
        <div class="tree-group-tabs">
          <t-radio-group v-model="groupBy" variant="default-filled" size="small" @change="onGroupByChange">
            <t-radio-button value="">原始结构</t-radio-button>
            <t-radio-button value="knowledge_completeness">知识关联类型</t-radio-button>
            <t-radio-button value="main_domain">主交付领域</t-radio-button>
            <t-radio-button value="specific_business" disabled>特定业务类</t-radio-button>
          </t-radio-group>
        </div>
        <div class="tree-search">
          <t-input
            v-model="searchKeyword"
            placeholder="输入RDC单号检索"
            size="small"
            clearable
            :suffix-icon="() => h(TIcon, { name: 'search' })"
          >
            <template #suffixIcon>
              <t-icon name="search" />
            </template>
          </t-input>
        </div>
        <div class="tree-content">
          <div v-if="treeLoading" class="tree-loading">
            <t-loading size="small" text="加载中..." />
          </div>
          <div v-else-if="filteredTreeData.length === 0" class="tree-empty">
            暂无数据
          </div>
          <t-tree
            v-else
            v-model:expanded="expandedKeys"
            v-model:actived="activedKeys"
            :data="filteredTreeData"
            :keys="treeKeys"
            hover
            activable
            line
            transition
            @active="onTreeNodeClick"
          />
        </div>
      </div>

      <!-- 拖拽分隔条 -->
      <div
        class="resize-bar"
        @mousedown="onResizeStart"
      >
        <div class="resize-bar-inner"></div>
      </div>

      <!-- 右侧内容区 -->
      <div class="right-content">
        <!-- 上半部分：图谱区（分组节点时隐藏） -->
        <div class="flowchart-section" v-if="!isGroupNodeSelected">
          <div class="section-header">
            <span class="section-title">
              <t-icon name="chart-bubble" />
              需求关系图
            </span>
            <div class="section-actions">
               <t-button 
                v-if="isFullscreen" 
                size="small" 
                theme="danger" 
                variant="outline" 
                @click="exitFullscreen"
                class="exit-fullscreen-btn"
              >
                <template #icon><t-icon name="close" /></template>
                退出全屏
              </t-button>
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
              <t-button
                size="small"
                variant="outline"
                @click="openAllSkillsDrawer"
                v-if="hasGraphData"
              >
                <template #icon><t-icon name="view-list" /></template>
                查看微范式和配置化PR
              </t-button>
            </div>
          </div>
          <div class="flowchart-container" :class="{ 'fullscreen-chart': isFullscreen }">
            <div v-if="isFullscreen" class="fullscreen-close-btn" @click="exitFullscreen">
              <t-icon name="close" size="20px" />
            </div>
            <div v-if="graphLoading" class="graph-loading">
              <t-loading size="large" text="加载需求图数据中..." />
            </div>
            <div v-else-if="!hasGraphData && !currentSeedNode" class="graph-empty">
              <t-icon name="chart-bubble" size="48px" style="color: #c0c4cc;" />
              <p>请点击左侧树节点查看需求关系图</p>
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
                  <!-- 包含关系连线（蓝色） -->
                  <g v-for="edge in containsEdges" :key="edge.id">
                    <path
                      :d="edge.path"
                      :stroke="edge.highlighted ? '#1967d2' : '#8c9bb0'"
                      :stroke-width="edge.highlighted ? 2.5 : 1.5"
                      fill="none"
                      :marker-end="edge.highlighted ? 'url(#arrowhead-blue-highlight)' : 'url(#arrowhead-blue)'"
                      class="edge-path"
                    />
                    <rect
                      :x="edge.labelX - edge.labelWidth / 2"
                      :y="edge.labelY - 10"
                      :width="edge.labelWidth"
                      height="20"
                      rx="4"
                      fill="#e8f0fe"
                      stroke="#1967d2"
                      stroke-width="0.5"
                      opacity="0.95"
                    />
                    <text
                      :x="edge.labelX"
                      :y="edge.labelY + 4"
                      text-anchor="middle"
                      font-size="10"
                      fill="#174ea6"
                      font-weight="500"
                    >包含</text>
                  </g>

                  <!-- 波及关系连线（黄色/橙色） -->
                  <g v-for="edge in affectsEdges" :key="edge.id">
                    <path
                      :d="edge.path"
                      :stroke="edge.highlighted ? '#e37318' : '#8c9bb0'"
                      :stroke-width="edge.highlighted ? 2.5 : 1.5"
                      fill="none"
                      :marker-end="edge.highlighted ? 'url(#arrowhead-orange-highlight)' : 'url(#arrowhead-orange)'"
                      class="edge-path"
                    />
                    <rect
                      :x="edge.labelX - edge.labelWidth / 2"
                      :y="edge.labelY - 10"
                      :width="edge.labelWidth"
                      height="20"
                      rx="4"
                      fill="#fff3e0"
                      stroke="#e37318"
                      stroke-width="0.5"
                      opacity="0.95"
                    />
                    <text
                      :x="edge.labelX"
                      :y="edge.labelY + 4"
                      text-anchor="middle"
                      font-size="10"
                      fill="#8b4a0b"
                      font-weight="500"
                    >波及</text>
                  </g>

                  <!-- 关联关系连线（绿色） -->
                  <g v-for="edge in relatesEdges" :key="edge.id">
                    <path
                      :d="edge.path"
                      :stroke="edge.highlighted ? '#2ba471' : '#8c9bb0'"
                      :stroke-width="edge.highlighted ? 2.5 : 1.5"
                      fill="none"
                      :marker-end="edge.highlighted ? 'url(#arrowhead-green-highlight)' : 'url(#arrowhead-green)'"
                      class="edge-path"
                    />
                    <rect
                      :x="edge.labelX - edge.labelWidth / 2"
                      :y="edge.labelY - 10"
                      :width="edge.labelWidth"
                      height="20"
                      rx="4"
                      fill="#e6f4ea"
                      stroke="#2ba471"
                      stroke-width="0.5"
                      opacity="0.95"
                    />
                    <text
                      :x="edge.labelX"
                      :y="edge.labelY + 4"
                      text-anchor="middle"
                      font-size="10"
                      fill="#137333"
                      font-weight="500"
                    >关联</text>
                  </g>

                  <!-- 校验关系连线（红色） -->
                  <g v-for="edge in verifiesEdges" :key="edge.id">
                    <path
                      :d="edge.path"
                      :stroke="edge.highlighted ? '#e34d59' : '#8c9bb0'"
                      :stroke-width="edge.highlighted ? 2.5 : 1.5"
                      stroke-dasharray="6,3"
                      fill="none"
                      :marker-end="edge.highlighted ? 'url(#arrowhead-red-highlight)' : 'url(#arrowhead-red)'"
                      class="edge-path"
                    />
                    <rect
                      :x="edge.labelX - edge.labelWidth / 2"
                      :y="edge.labelY - 10"
                      :width="edge.labelWidth"
                      height="20"
                      rx="4"
                      :fill="edge.isMatch ? '#e6f4ea' : '#fdecee'"
                      :stroke="edge.isMatch ? '#2ba471' : '#e34d59'"
                      stroke-width="0.5"
                      opacity="0.95"
                      class="edge-clickable"
                      @click.stop="openEdgeDrawer(edge)"
                    />
                    <text
                      :x="edge.labelX"
                      :y="edge.labelY + 4"
                      text-anchor="middle"
                      font-size="10"
                      :fill="edge.isMatch ? '#137333' : '#c62828'"
                      font-weight="500"
                      class="edge-clickable"
                      @click.stop="openEdgeDrawer(edge)"
                    >{{ edge.labelText }}</text>
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
                    @click.stop="selectNode(node)"
                    :class="{
                      'selected': selectedNodeId === node.id,
                      'dragging': draggingNodeId === node.id
                    }"
                  >
                    <title>{{ node.name }}</title>

                    <!-- PR 聚合节点特殊渲染 -->
                    <template v-if="node.type === 'product_requirement'">
                      <rect
                        :width="node.width"
                        :height="node.height"
                        rx="8"
                        :fill="node.bgColor"
                        :stroke="getNodeStroke(node)"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 2"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
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

                      <template v-if="node.prSummary">
                        <g v-for="(cat, ci) in prCategories" :key="cat.key">
                          <rect
                            :x="6 + ci * 74"
                            :y="24"
                            width="70"
                            height="28"
                            rx="4"
                            fill="white"
                            opacity="0.75"
                          />
                          <rect
                            :x="6 + ci * 74"
                            :y="24"
                            width="70"
                            height="28"
                            rx="4"
                            fill="none"
                            :stroke="cat.color"
                            stroke-width="1"
                          />
                          <text
                            :x="28 + ci * 74"
                            :y="42"
                            text-anchor="middle"
                            font-size="9"
                            :fill="cat.color"
                            font-weight="600"
                          >{{ cat.label }}</text>
                          <text
                            :x="58 + ci * 74"
                            :y="42"
                            text-anchor="middle"
                            font-size="11"
                            :fill="cat.color"
                            font-weight="bold"
                          >{{ node.prSummary.counts[cat.key] || 0 }}</text>
                        </g>
                      </template>
                    </template>

                    <!-- 需求分析技能库节点（紫色边框） -->
                    <template v-else-if="node.type === 'requirement_analysis_skill'">
                      <rect
                        :width="node.width"
                        :height="node.height"
                        rx="12"
                        fill="#faf5ff"
                        stroke="#9333ea"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 2"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
                      <rect
                        :x="node.typeX"
                        :y="-10"
                        :width="node.typeWidth"
                        height="20" rx="4"
                        fill="#9333ea"
                      />
                      <text
                        :x="node.typeX + node.typeWidth / 2"
                        y="4"
                        text-anchor="middle"
                        font-size="11"
                        fill="white"
                        font-weight="bold"
                      >{{ node.typeLabel }}</text>
                      <text
                        :x="node.width / 2"
                        :y="node.textY"
                        text-anchor="middle"
                        font-size="12"
                        font-weight="600"
                        fill="#6b21a8"
                      >
                        {{ node.name.length > 12 ? node.name.substring(0, 12) + '...' : node.name }}
                      </text>
                      <text
                        :x="node.width - 8"
                        :y="node.height - 8"
                        text-anchor="end"
                        font-size="10"
                        font-weight="500"
                        fill="#9333ea"
                      >
                        {{ node.skillCount || 0 }}条
                      </text>
                    </template>

                    <!-- 方案设计技能库节点（蓝色边框） -->
                    <template v-else-if="node.type === 'solution_design_skill'">
                      <rect
                        :width="node.width"
                        :height="node.height"
                        rx="12"
                        fill="#eff6ff"
                        stroke="#3b82f6"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 2"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
                      <rect
                        :x="node.typeX"
                        :y="-10"
                        :width="node.typeWidth"
                        height="20" rx="4"
                        fill="#3b82f6"
                      />
                      <text
                        :x="node.typeX + node.typeWidth / 2"
                        y="4"
                        text-anchor="middle"
                        font-size="11"
                        fill="white"
                        font-weight="bold"
                      >{{ node.typeLabel }}</text>
                      <text
                        :x="node.width / 2"
                        :y="node.textY"
                        text-anchor="middle"
                        font-size="12"
                        font-weight="600"
                        fill="#1e40af"
                      >
                        {{ node.name.length > 12 ? node.name.substring(0, 12) + '...' : node.name }}
                      </text>
                      <text
                        :x="node.width - 8"
                        :y="node.height - 8"
                        text-anchor="end"
                        font-size="10"
                        font-weight="500"
                        fill="#3b82f6"
                      >
                        {{ node.skillCount || 0 }}条
                      </text>
                    </template>

                    <!-- 技能库聚合节点（红色边框） -->
                    <template v-else-if="node.type === 'skill_library'">
                      <rect
                        :width="node.width"
                        :height="node.height"
                        rx="12"
                        fill="#fff5f5"
                        stroke="#e34d59"
                        :stroke-width="selectedNodeId === node.id ? 2.5 : 2"
                        filter="url(#shadow)"
                        class="node-shape"
                      />
                      <rect
                        :x="node.typeX"
                        :y="-10"
                        :width="node.typeWidth"
                        height="20" rx="4"
                        fill="#e34d59"
                      />
                      <text
                        :x="node.typeX + node.typeWidth / 2"
                        y="4"
                        text-anchor="middle"
                        font-size="11"
                        fill="white"
                        font-weight="bold"
                      >{{ node.typeLabel }}</text>
                      <text
                        :x="node.width / 2"
                        :y="node.textY"
                        text-anchor="middle"
                        font-size="12"
                        font-weight="600"
                        fill="#c62828"
                      >
                        {{ node.name.length > 12 ? node.name.substring(0, 12) + '...' : node.name }}
                      </text>
                      <text
                        :x="node.width - 8"
                        :y="node.height - 8"
                        text-anchor="end"
                        font-size="10"
                        font-weight="500"
                        fill="#e34d59"
                      >
                        {{ node.skillCount || 0 }}条
                      </text>
                    </template>

                    <!-- 普通节点渲染 -->
                    <template v-else>
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

                      <template v-else>
                        <rect
                          :width="node.width"
                          :height="node.height"
                          :rx="node.shape === 'feature' ? 12 : 2"
                          :fill="node.bgColor"
                          :stroke="getNodeStroke(node)"
                          :stroke-width="selectedNodeId === node.id ? 2.5 : 1.5"
                          filter="url(#shadow)"
                          class="node-shape"
                        />
                      </template>

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

                      <text
                        :x="node.width / 2"
                        :y="node.textY"
                        text-anchor="middle"
                        font-size="12"
                        font-weight="600"
                        :fill="node.textColor"
                      >
                        {{ node.name.length > 10 ? node.name.substring(0, 10) + '...' : node.name }}
                      </text>

                      <text
                        v-if="getChildBadgeText(node) !== ''"
                        :x="node.width - 8"
                        :y="node.height - 8"
                        text-anchor="end"
                        font-size="9"
                        font-weight="500"
                        :fill="node.tagColor"
                      >
                        {{ getChildBadgeText(node) }}
                      </text>

                      <!-- 关联技能数量徽章 -->
                      <text
                        v-if="node.relatedSkillIds && node.relatedSkillIds.length > 0"
                        :x="node.width - 8"
                        :y="node.height - 8"
                        text-anchor="end"
                        font-size="10"
                        font-weight="500"
                        fill="#e34d59"
                      >
                        🔗{{ node.relatedSkillIds.length }}
                      </text>

                      <g v-if="node.url" class="link-indicator" @click.stop="openUrl(node.url)">
                        <circle :cx="node.width - 14" cy="10" r="8" fill="white" :stroke="node.tagColor" stroke-width="1" />
                        <text :x="node.width - 14" y="14" text-anchor="middle" font-size="10" :fill="node.tagColor">🔗</text>
                      </g>
                    </template>
                  </g>
                </g>

                <defs>
                  <filter id="shadow" x="-8%" y="-8%" width="120%" height="125%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08" />
                  </filter>
                  <marker id="arrowhead-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#1967d2" />
                  </marker>
                  <marker id="arrowhead-blue-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#1967d2" />
                  </marker>
                  <marker id="arrowhead-orange" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e37318" />
                  </marker>
                  <marker id="arrowhead-orange-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e37318" />
                  </marker>
                  <marker id="arrowhead-green" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#2ba471" />
                  </marker>
                  <marker id="arrowhead-green-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#2ba471" />
                  </marker>
                  <marker id="arrowhead-red" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e34d59" />
                  </marker>
                  <marker id="arrowhead-red-highlight" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
                    <path d="M0,0 L8,3 L0,6 Z" fill="#e34d59" />
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
            </div>

            <div v-else class="graph-empty">
              <t-icon name="chart-bubble" size="48px" style="color: #c0c4cc;" />
              <p>当前节点无关系图数据</p>
            </div>
          </div>
        </div>

        <!-- 上半部分：分组详情表格（分组节点时显示） -->
        <div class="flowchart-section" v-else>
          <div class="section-header">
            <span class="section-title">
              <t-icon name="table" />
              分组详情 - {{ currentGroupCategory }}
            </span>
            <div class="section-actions">
              <t-button size="small" variant="outline" @click="refreshGroupDetail">
                <template #icon><t-icon name="refresh" /></template>
                刷新
              </t-button>
              <t-button size="small" variant="outline" theme="primary" @click="exportGroupDetail">
                <template #icon><t-icon name="download" /></template>
                导出
              </t-button>
            </div>
          </div>
          <div class="detail-table-container">
            <div v-if="groupDetailLoading" class="graph-loading">
              <t-loading size="large" text="加载分组数据中..." />
            </div>
            <div v-else-if="groupDetailItems.length === 0" class="graph-empty">
              <t-icon name="file" size="48px" style="color: #c0c4cc;" />
              <p>暂无数据</p>
            </div>
            <t-table
              v-else
              :data="groupDetailItems"
              :columns="groupDetailColumns"
              row-key="rdc_id"
              bordered
              hover
              stripe
              size="medium"
              max-height="calc(100% - 60px)"
            >
              <template #access_check="{ row }">
                <t-tag :theme="row.access_check === '通过' ? 'success' : 'default'" variant="light">
                  {{ row.access_check || '-' }}
                </t-tag>
              </template>
              <template #instance_url="{ row }">
                <t-link v-if="row.instance_url" theme="primary" hover="color" :href="row.instance_url" target="_blank">
                  点击查看
                </t-link>
                <span v-else>-</span>
              </template>
              <template #solution_doc_url="{ row }">
                <t-link v-if="row.solution_doc_url" theme="primary" hover="color" :href="row.solution_doc_url" target="_blank">
                  点击查看
                </t-link>
                <span v-else>-</span>
              </template>
            </t-table>
          </div>
        </div>

        <!-- 下半部分：明细数据（分组节点时隐藏） -->
        <div class="detail-section" v-if="!isGroupNodeSelected">
          <div class="section-header">
            <span class="section-title">
              <t-icon name="view-module" />
              明细数据
            </span>
          </div>
          <div class="detail-container">
            <div class="detail-list">
              <t-descriptions title="基础信息" bordered :column="2" :label-style="{ width: '120px' }">
                <t-descriptions-item label="需求名称">{{ detail.basicInfo || '-' }}</t-descriptions-item>
                <t-descriptions-item label="RDC ID">{{ detail.rdcId || '-' }}</t-descriptions-item>
                <t-descriptions-item label="状态">{{ detail.status || '-' }}</t-descriptions-item>
                <t-descriptions-item label="主领域">{{ detail.mainDomain || '-' }}</t-descriptions-item>
                <t-descriptions-item label="需求实例化链接">
                  <t-link v-if="detail.instanceUrl" theme="primary" hover="color" :href="detail.instanceUrl" target="_blank" class="url-link">
                    {{ detail.instanceUrl }}
                  </t-link>
                  <span v-else>-</span>
                </t-descriptions-item>
                <t-descriptions-item label="方案状态">{{ detail.solutionStatus || '-' }}</t-descriptions-item>
              </t-descriptions>

              <t-descriptions title="方案文档" bordered :column="1" :label-style="{ width: '120px' }">
                <t-descriptions-item label="方案文档链接">
                  <t-link v-if="detail.solutionDocUrl" theme="primary" hover="color" :href="detail.solutionDocUrl" target="_blank" class="url-link">
                    {{ detail.solutionDocUrl }}
                  </t-link>
                  <span v-else>-</span>
                </t-descriptions-item>
              </t-descriptions>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Drawer 组件 -->
    <t-drawer
      v-model:visible="drawerVisible"
      :header="selectedNode?.fullName || selectedNode?.name"
      size="720px"
      placement="right"
      :footer="false"
      @close="handleDrawerClose"
    >
      <div v-if="selectedNode" class="node-detail">
        <div class="detail-section">
          <div class="detail-label">节点类型</div>
          <span class="type-badge" :style="{ background: getTypeColor(selectedNode.type), color: '#fff' }">
            {{ selectedNode.typeLabel }}
          </span>
        </div>

        <div v-if="selectedNode.rawData?.urls?.length || selectedNode.url" class="detail-section">
          <div class="detail-label">链接</div>
          <div v-if="selectedNode.rawData?.urls?.length" class="url-list">
            <div v-for="(url, index) in selectedNode.rawData.urls" :key="url" class="url-container">
              <t-link theme="primary" hover="color" :href="url" target="_blank">
                {{ getLinkDisplayText(url, selectedNode.typeLabel, selectedNode.name, selectedNode.rawData?.linkNames?.[index]) }}
              </t-link>
            </div>
          </div>
          <div v-else class="url-container">
            <t-link theme="primary" hover="color" :href="selectedNode.url" target="_blank">
              {{ getLinkDisplayText(selectedNode.url, selectedNode.typeLabel, selectedNode.name) }}
            </t-link>
          </div>
        </div>

        <!-- 需求分析技能库内容 - 修改后的样式 -->
        <div v-if="selectedNode.type === 'requirement_analysis_skill'" class="detail-section">
          <div class="detail-label">技能库内容（共 {{ selectedNode.skillRecords?.length || 0 }} 条记录）</div>
          <div class="skill-library-content">
            <div v-if="selectedNode.skillRecords && selectedNode.skillRecords.length > 0" class="skill-records-container">
              <div 
                v-for="(record, idx) in selectedNode.skillRecords" 
                :key="idx" 
                class="skill-record-card"
              >
                <!-- 章节名称 -->
                <div class="record-chapter">
                  <t-icon name="book" size="16px" />
                  <span class="chapter-name">{{ record.chapterName || '未命名章节' }}</span>
                </div>

                <!-- 使用技能 -->
                <div class="record-section">
                  <div class="section-label">
                    <t-icon name="code" size="14px" />
                    <span>使用技能</span>
                  </div>
                  <div class="skill-links">
                    <div 
                      v-for="(skillUrl, skillName) in record.useSkill" 
                      :key="skillName"
                      class="skill-link-item"
                    >
                      <t-link 
                        theme="primary" 
                        hover="color" 
                        :href="skillUrl"
                        target="_blank"
                      >
                        {{ skillName }}
                      </t-link>
                    </div>
                    <span v-if="Object.keys(record.useSkill || {}).length === 0" class="empty-tip">无</span>
                  </div>
                </div>

                <!-- 输入知识 -->
                <div class="record-section">
                <div class="section-label">
                  <t-icon name="enter" size="14px" />
                  <span>使用业务知识</span>
                </div>
                <div class="knowledge-links">
                  <div 
                    v-for="(knowledgeUrl, knowledgeTitle) in record.inputKnowledge" 
                    :key="knowledgeTitle"
                    class="knowledge-link-item"
                  >
                    <t-link 
                      theme="primary" 
                      hover="color" 
                      :href="knowledgeUrl"
                      target="_blank"
                    >
                      {{ knowledgeTitle }}
                    </t-link>
                  </div>
                  <span v-if="Object.keys(record.inputKnowledge || {}).length === 0" class="empty-tip">无</span>
                </div>
              </div>

              <!-- 沉淀业务知识 -->
              <div class="record-section">
                <div class="section-label">
                  <t-icon name="rollback" size="14px" />
                  <span>沉淀业务知识</span>
                </div>
                <div class="knowledge-links">
                  <div 
                    v-for="(feedbackUrl, feedbackTitle) in record.feedbackKnowledge" 
                    :key="feedbackTitle"
                    class="knowledge-link-item"
                  >
                    <t-link 
                      theme="primary" 
                      hover="color" 
                      :href="feedbackUrl"
                      target="_blank"
                    >
                      {{ feedbackTitle }}
                    </t-link>
                  </div>
                  <span v-if="Object.keys(record.feedbackKnowledge || {}).length === 0" class="empty-tip">无</span>
                </div>
              </div>
              </div>
            </div>
            <div v-else class="no-data-tip">
              暂无技能库数据
            </div>
          </div>
        </div>

        <!-- 方案设计技能库内容 - 同样修改 -->
        <div v-if="selectedNode.type === 'solution_design_skill'" class="detail-section">
          <div class="detail-label">技能库内容（共 {{ selectedNode.skillRecords?.length || 0 }} 条记录）</div>
          <div class="skill-library-content">
            <div v-if="selectedNode.skillRecords && selectedNode.skillRecords.length > 0" class="skill-records-container">
              <div 
                v-for="(record, idx) in selectedNode.skillRecords" 
                :key="idx" 
                class="skill-record-card"
              >
                <!-- 章节名称 -->
                <div class="record-chapter">
                  <t-icon name="book" size="16px" />
                  <span class="chapter-name">{{ record.chapterName || '未命名章节' }}</span>
                </div>

                <!-- 使用技能 -->
                <div class="record-section">
                  <div class="section-label">
                    <t-icon name="code" size="14px" />
                    <span>使用技能</span>
                  </div>
                  <div class="skill-links">
                    <div 
                      v-for="(skillUrl, skillName) in record.useSkill" 
                      :key="skillName"
                      class="skill-link-item"
                    >
                      <t-link 
                        theme="primary" 
                        hover="color" 
                        :href="skillUrl"
                        target="_blank"
                      >
                        {{ skillName }}
                      </t-link>
                    </div>
                    <span v-if="Object.keys(record.useSkill || {}).length === 0" class="empty-tip">无</span>
                  </div>
                </div>

                <!-- 使用业务知识 -->
                <div class="record-section">
                  <div class="section-label">
                    <t-icon name="enter" size="14px" />
                    <span>使用业务知识</span>
                  </div>
                  <div class="knowledge-links">
                    <div 
                      v-for="(knowledgeUrl, knowledgeTitle) in record.inputKnowledge" 
                      :key="knowledgeTitle"
                      class="knowledge-link-item"
                    >
                      <t-link 
                        theme="primary" 
                        hover="color" 
                        :href="knowledgeUrl"
                        target="_blank"
                      >
                        {{ knowledgeTitle }}
                      </t-link>
                    </div>
                    <span v-if="Object.keys(record.inputKnowledge || {}).length === 0" class="empty-tip">无</span>
                  </div>
                </div>

                <!-- 回馈知识 -->
                <div class="record-section">
                  <div class="section-label">
                    <t-icon name="rollback" size="14px" />
                    <span>沉淀业务知识</span>
                  </div>
                  <div class="knowledge-links">
                    <div 
                      v-for="(feedbackUrl, feedbackTitle) in record.feedbackKnowledge" 
                      :key="feedbackTitle"
                      class="knowledge-link-item"
                    >
                      <t-link 
                        theme="primary" 
                        hover="color" 
                        :href="feedbackUrl"
                        target="_blank"
                      >
                        {{ feedbackTitle }}
                      </t-link>
                    </div>
                    <span v-if="Object.keys(record.feedbackKnowledge || {}).length === 0" class="empty-tip">无</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data-tip">
              暂无技能库数据
            </div>
          </div>
        </div>

        <!-- 技能库聚合节点内容 -->
        <div v-if="selectedNode.type === 'skill_library'" class="detail-section">
          <div class="detail-label">技能库内容（共 {{ selectedNode.skillList?.length || 0 }} 条）</div>
          <div class="skill-library-content">
            <t-table
              v-if="selectedNode.skillList && selectedNode.skillList.length > 0"
              :data="selectedNode.skillList"
              :columns="skillLibraryColumns"
              row-key="id"
              hover
              size="small"
              style="margin-top: 10px; width: 100%"
              max-height="400"
            >
              <template #skill_name="{ row }">
                <t-link 
                  v-if="row.skill_url" 
                  theme="primary" 
                  hover="color" 
                  :href="row.skill_url"
                  target="_blank"
                >
                  {{ row.skill_name || '查看技能' }}
                </t-link>
                <span v-else>{{ row.skill_name || '-' }}</span>
              </template>
            </t-table>
            <div v-else class="no-data-tip">
              暂无技能库数据
            </div>
          </div>
        </div>

        <div v-if="selectedNode.childFeatures?.length" class="detail-section">
          <div class="detail-label">波及特性（{{ selectedNode.childFeatures.length }}个）</div>
          <div class="child-list">
            <t-tag
              v-for="f in selectedNode.childFeatures"
              :key="f.id"
              theme="warning"
              variant="light"
              class="child-tag"
            >{{ f.name }}</t-tag>
          </div>
        </div>

        <div v-if="selectedNode.childComponents?.length" class="detail-section">
          <div class="detail-label">波及组件（{{ selectedNode.childComponents.length }}个）</div>
          <div class="child-list">
            <t-tag
              v-for="c in selectedNode.childComponents"
              :key="c.id"
              theme="primary"
              variant="light"
              class="child-tag"
              @click="c.url && openUrl(c.url)"
            >{{ c.name }}</t-tag>
          </div>
        </div>

        <div v-if="selectedNode.childSections?.length" class="detail-section">
          <div class="detail-label">包含章节（{{ selectedNode.childSections.length }}个）</div>
          <div class="section-list">
            <div v-for="s in selectedNode.childSections" :key="s.id" class="section-item" @click="viewSectionContent(s)">
              <t-icon name="folder" size="16px" />
              <span class="section-title">{{ s.name }}</span>
              <t-icon name="chevron-right" size="16px" class="section-arrow" />
            </div>
          </div>
        </div>

        <div v-if="selectedSectionContent" class="detail-section">
          <div class="detail-label">{{ selectedSectionName }}</div>
          <div class="section-content">
            <div v-if="isSectionHtml" class="html-description-content" v-html="selectedSectionContent"></div>
            <div v-else class="content-text">{{ selectedSectionContent }}</div>
          </div>
        </div>

        <div v-if="!selectedNode.childFeatures?.length && !selectedNode.childComponents?.length && !selectedNode.childSections?.length && !selectedNode.url && !selectedNode.rawData?.urls?.length && !selectedNode.prSummary && selectedNode.type !== 'requirement_analysis_skill' && selectedNode.type !== 'solution_design_skill' && selectedNode.type !== 'skill_library'" class="no-data-tip">
          暂无附属数据
        </div>

        <div v-if="selectedNode.prSummary" class="detail-section">
          <div class="detail-label">产品需求列表</div>
          <div v-for="cat in prCategories" :key="cat.key" class="pr-category-group">
            <div class="pr-category-header" :style="{ borderLeft: `3px solid ${cat.color}` }">
              <span :style="{ color: cat.color }" class="pr-category-name">{{ cat.label }}</span>
              <span class="pr-category-count">{{ selectedNode.prSummary.counts[cat.key] || 0 }}个</span>
            </div>
            <div v-if="selectedNode.prSummary.items.filter(i => (prCategories.map(c=>c.key).includes(i.reuse_degree) ? i.reuse_degree : '无标识') === cat.key).length" class="pr-id-list">
              <t-tag
                v-for="item in selectedNode.prSummary.items.filter(i => (prCategories.map(c=>c.key).includes(i.reuse_degree) ? i.reuse_degree : '无标识') === cat.key)"
                :key="item.id"
                variant="outline"
                class="pr-id-tag"
                @click="item.id && openUrl(`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${item.id}`)"
              >{{ item.id }} {{ item.title }}</t-tag>
            </div>
          </div>
        </div>
      </div>
    </t-drawer>

    <t-drawer
      v-model:visible="edgeDrawerVisible"
      header="校验详情"
      size="520px"
      placement="right"
      :footer="false"
    >
      <div v-if="selectedEdge" class="node-detail">
        <div class="detail-section">
          <div class="detail-label">校验结果</div>
          <span class="type-badge" :style="{ background: selectedEdge.isMatch ? '#2ba471' : '#e34d59', color: '#fff' }">
            {{ selectedEdge.labelText }}
          </span>
        </div>

        <div class="detail-section">
          <div class="detail-label">RDC 需求方案 URL</div>
          <div v-if="selectedEdge.rawData?.solution_doc_url" class="url-container">
            <t-link theme="primary" hover="color" :href="selectedEdge.rawData.solution_doc_url" target="_blank">
              {{ selectedEdge.rawData.solution_doc_url }}
            </t-link>
          </div>
          <div v-else class="url-container" style="color: #98a2b3;">无</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">iCenter 抽取方案 URLs</div>
          <div v-if="selectedEdge.rawData?.icenter_solution_urls?.length" class="url-list">
            <div v-for="url in selectedEdge.rawData.icenter_solution_urls" :key="url" class="url-container">
              <t-link theme="primary" hover="color" :href="url" target="_blank">
                {{ url }}
              </t-link>
            </div>
          </div>
          <div v-else class="url-container" style="color: #98a2b3;">无</div>
        </div>
      </div>
    </t-drawer>

    <!-- 技能表格抽屉 - 三列布局 -->
    <t-drawer
      v-model:visible="skillDrawerVisible"
      :header="selectedEdge ? '关联的微范式和配置化 PR' : '画布中所有微范式和配置化 PR'"
      size="1000px"
      placement="right"
      :footer="false"
    >
      <div v-if="skillTableData.length > 0" class="skill-table-container">
        <!-- 三列布局：PR 列表、类型选择、SKILL 链接 -->
        <div class="three-column-layout">
          <!-- 第一列：所有的配置化和微范式 PR -->
          <div class="column-left">
            <div class="column-header">
              <t-icon name="view-list" />
              <span>PR 列表</span>
              <span class="column-count">{{ skillTableData.length }}个</span>
            </div>
            <div class="column-content">
              <div 
                v-for="(item, index) in skillTableData" 
                :key="index"
                class="pr-item"
                :class="{ 'active': currentSelectedIndex === index }"
                @click="currentSelectedIndex = index"
              >
                <div class="pr-id">
                  <t-link 
                    v-if="item.prRdcId" 
                    theme="primary" 
                    hover="color" 
                    :href="`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${item.prRdcId}`"
                    target="_blank"
                    @click.stop
                  >
                    {{ item.prRdcId }}
                  </t-link>
                  <span v-else class="no-id">无 ID</span>
                </div>
                <div class="pr-title">{{ item.prTitle || '无标题' }}</div>
              </div>
            </div>
          </div>
          
          <!-- 第二列：填写 PR 类型（微范式/配置化） -->
          <div class="column-middle">
            <div class="column-header">
              <t-icon name="edit" />
              <span>PR 类型</span>
            </div>
            <div class="column-content">
              <div v-if="currentSelectedIndex !== null" class="type-editor">
                <div class="editor-label">当前 PR：</div>
                <div class="current-pr-info">
                  {{ skillTableData[currentSelectedIndex]?.prRdcId || '无 ID' }}
                </div>
                <div class="editor-label" style="margin-top: 16px;">选择类型：</div>
                <t-radio-group 
                  v-model="skillTableData[currentSelectedIndex].type" 
                  variant="default-filled"
                  class="type-selector"
                >
                  <t-radio-button value="微范式">
                    <t-icon name="code" />
                    微范式
                  </t-radio-button>
                  <t-radio-button value="配置化">
                    <t-icon name="setting" />
                    配置化
                  </t-radio-button>
                  <t-radio-button value="无标识">
                    <t-icon name="question" />
                    无标识
                  </t-radio-button>
                </t-radio-group>
                <div class="type-description">
                  <t-alert v-if="skillTableData[currentSelectedIndex]?.type === '微范式'" theme="warning" title="微范式说明" close>
                    基于微架构范式的实现方式
                  </t-alert>
                  <t-alert v-else-if="skillTableData[currentSelectedIndex]?.type === '配置化'" theme="info" title="配置化说明" close>
                    通过配置参数实现不同场景
                  </t-alert>
                  <t-alert v-else theme="default" title="无标识说明" close>
                    未明确标识类型
                  </t-alert>
                </div>
              </div>
              <div v-else class="no-selection-tip">
                <t-icon name="info-circle" size="24px" style="color: #98a2b3;" />
                <p>请点击左侧 PR 进行类型设置</p>
              </div>
            </div>
          </div>
          
          <!-- 第三列：PR 关联的 SKILL 链接 -->
          <div class="column-right">
            <div class="column-header">
              <t-icon name="link" />
              <span>SKILL 链接</span>
            </div>
            <div class="column-content">
              <div v-if="currentSelectedIndex !== null && skillTableData[currentSelectedIndex]?.skillUrl" class="skill-link-section">
                <div class="skill-name">
                  {{ skillTableData[currentSelectedIndex]?.skillName || '技能' }}
                </div>
                <t-button 
                  theme="success" 
                  variant="outline"
                  block
                  @click="openUrl(skillTableData[currentSelectedIndex].skillUrl)"
                >
                  <template #icon><t-icon name="link" /></template>
                  打开技能链接
                </t-button>
                <div class="skill-url-display">
                  <span class="url-label">URL:</span>
                  <a :href="skillTableData[currentSelectedIndex].skillUrl" target="_blank" class="url-text">
                    {{ skillTableData[currentSelectedIndex].skillUrl }}
                  </a>
                </div>
              </div>
              <div v-else class="no-skill-tip">
                <t-icon name="link-off" size="24px" style="color: #98a2b3;" />
                <p>{{ currentSelectedIndex !== null ? '该 PR 暂无关联技能' : '请先选择 PR' }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 底部操作栏 -->
        <div class="bottom-action-bar">
          <t-button theme="primary" @click="saveSkillData">
            <t-icon name="check" />
            保存修改
          </t-button>
          <t-button variant="outline" @click="exportSkillData">
            <t-icon name="download" />
            导出数据
          </t-button>
          <span class="action-tip">提示：点击左侧 PR 项可在中间列设置类型</span>
        </div>
      </div>
      <div v-else class="no-skills-tip">
        <t-icon name="info-circle" size="24px" style="color: #98a2b3;" />
        <p>{{ selectedEdge ? '该边没有关联的微范式和配置化 PR' : '画布中没有微范式和配置化 PR' }}</p>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="jsx">
import { onMounted, onUnmounted, ref, computed, reactive, watch, nextTick, h } from 'vue';
import { MessagePlugin, Link } from 'tdesign-vue-next';
import * as XLSX from 'xlsx';
import { useUserStore } from '@/store';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const user = useUserStore();
// ============ 基础状态 ============
const treeLoading = ref(false);
const refreshLoading = ref(false);
const treeData = ref([]);
const groupBy = ref('');
const expandedKeys = ref([]);
const activedKeys = ref([]);
const tabValue = ref('智能OTN');
const treeAbortController = ref(null);
const lastRefreshTime = ref('');
const forceRefresh = ref(false);
const showButton = ref(false);
const searchKeyword = ref('');

// ============ 基于RDC单号的树过滤 ============
const filterTreeByKeyword = (nodes, keyword) => {
  if (!keyword || !keyword.trim()) return nodes;
  const kw = keyword.trim().toLowerCase();

  const filter = (nodeList) => {
    return nodeList.reduce((acc, node) => {
      const rdcId = (node.rdc_id || '').toLowerCase();
      const matched = rdcId.includes(kw);
      const filteredChildren = node.children?.length ? filter(node.children) : [];

      if (matched || filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren,
        });
      }
      return acc;
    }, []);
  };

  return filter(nodes);
};

const filteredTreeData = computed(() => filterTreeByKeyword(treeData.value, searchKeyword.value));

// 搜索时自动展开匹配结果
watch(searchKeyword, (val) => {
  if (val && val.trim()) {
    const allIds = [];
    const collectIds = (nodes) => {
      nodes.forEach(n => {
        allIds.push(n.node_id);
        if (n.children?.length) collectIds(n.children);
      });
    };
    collectIds(filteredTreeData.value);
    expandedKeys.value = allIds;
  }
});
// ============ 分组详情状态 ============
const isGroupNodeSelected = ref(false);
const currentGroupNode = ref(null);
const groupDetailLoading = ref(false);
const groupDetailItems = ref([]);
const currentGroupCategory = ref('');
const groupDetailColumns = [
  { 
    colKey: 'rdc_id', 
    title: '标识', 
    width: 150,
    cell: (_, { row }) => {
      const getRdcHref = (relatedRdcIdent) => {
        if (!relatedRdcIdent) return '';
        
        const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
        const appPath = '/apps/wim/allWorkItems';
        
        const configs = {
          OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
          OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
        };
        
        const config = Object.entries(configs).find(([key]) => 
          relatedRdcIdent.includes(key)
        )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };

        return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
      };

      const href = getRdcHref(row.rdc_id);

      return (
        <t-link
          theme="primary"
          href={href}
          target="_blank"
          hover="underline"
        >
          {row.rdc_id}
        </t-link>
      );
    },    
  },
  { colKey: 'title', title: '标题', ellipsis: true },
  { colKey: 'main_domain', title: '主交付领域', width: 150 },
  { colKey: 'access_check', title: '准入检查', width: 100, cell: 'access_check' },
  { colKey: 'instance_url', title: '需求实例化链接', width: 150, cell: 'instance_url' },
  { colKey: 'instance_status', title: '需求实例化状态', width: 150 },
  { colKey: 'solution_doc_url', title: '方案文档链接', width: 150, cell: 'solution_doc_url' },
  { colKey: 'solution_status', title: '方案状态', width: 120 },
];

// 需求分析技能库表格列配置（保留用于兼容，但不再使用表格展示）
const requirementSkillColumns = [
  { 
    colKey: 'skill_name', 
    title: 'SKILL名称', 
    width: 250,
    ellipsis: true,
  },
  { 
    colKey: 'skill_url', 
    title: 'SKILL链接', 
    width: 200,
  },
  { 
    colKey: 'source_page', 
    title: '来源页面', 
    width: 200,
    ellipsis: true,
  },
];

// 方案设计技能库表格列配置
const solutionSkillColumns = [
  { 
    colKey: 'skill_name', 
    title: 'SKILL名称', 
    width: 250,
    ellipsis: true,
  },
  { 
    colKey: 'skill_url', 
    title: 'SKILL链接', 
    width: 200,
  },
  { 
    colKey: 'source_page', 
    title: '来源页面', 
    width: 200,
    ellipsis: true,
  },
];

// 技能库表格列配置
const skillLibraryColumns = [
  { 
    colKey: 'skill_name', 
    title: 'SKILL名称', 
    width: 250,
    ellipsis: true,
  },
  { 
    colKey: 'skill_url', 
    title: 'SKILL链接', 
    width: 200,
  },
  { 
    colKey: 'source_page', 
    title: '来源页面', 
    width: 200,
    ellipsis: true,
  },
];

const getPrUrl = (rdcId) => {
  if (!rdcId) return '';
  
  const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
  const appPath = '/apps/wim/allWorkItems';
  
  const configs = {
    OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
    OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
  };
  
  const config = Object.entries(configs).find(([key]) => 
    rdcId.includes(key)
  )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };

  return `${baseUrl}/${config.workspace}${appPath}/${rdcId}?teamId=${config.teamId}`;
};

// ============ 导出分组详情表格 ============
const exportGroupDetail = () => {
  if (!groupDetailItems.value || groupDetailItems.value.length === 0) {
    MessagePlugin.warning('暂无数据可导出');
    return;
  }

  try {
    const exportData = groupDetailItems.value.map((row) => {
      const exportRow = {};
      
      groupDetailColumns.forEach((col) => {
        if (col.colKey === 'operation') return;
        
        let value = row[col.colKey];
        
        if (col.colKey === 'rdc_id') {
          value = value || '';
        } else if (col.colKey === 'access_check') {
          value = value || '-';
        } else if (col.colKey === 'instance_url') {
          value = value || '-';
        } else if (col.colKey === 'solution_doc_url') {
          value = value || '-';
        } else {
          value = value !== null && value !== undefined ? String(value) : '-';
        }
        
        exportRow[col.title] = value;
      });
      
      return exportRow;
    });

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    
    const columnWidths = [];
    const firstRow = exportData[0];
    if (firstRow) {
      Object.keys(firstRow).forEach((key) => {
        const headerWidth = key.length;
        const maxWidth = Math.max(
          headerWidth,
          ...exportData.map((row) => (row[key] ? String(row[key]).length : 0))
        );
        columnWidths.push({ wch: Math.min(maxWidth + 2, 60) });
      });
    }
    worksheet['!cols'] = columnWidths;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, currentGroupCategory.value || '分组详情');

    const date = new Date();
    const formattedDate = `${date.getFullYear()}${(date.getMonth() + 1).toString().padStart(2, '0')}${date.getDate().toString().padStart(2, '0')}_${date.getHours().toString().padStart(2, '0')}${date.getMinutes().toString().padStart(2, '0')}`;
    const fileName = `${currentGroupCategory.value || '分组详情'}_${formattedDate}.xlsx`;

    XLSX.writeFile(workbook, fileName);
    MessagePlugin.success(`导出成功，共 ${exportData.length} 条数据`);
  } catch (error) {
    console.error('导出失败:', error);
    MessagePlugin.error('导出失败，请重试');
  }
};

// ============ 拖拽调整宽度 ============
const layoutRef = ref(null);
const sidebarWidth = ref(360);
const MIN_SIDEBAR = 200;
const MAX_SIDEBAR = 800;
let resizing = false;
let startX = 0;
let startWidth = 0;

const onResizeStart = (e) => {
  resizing = true;
  startX = e.clientX;
  startWidth = sidebarWidth.value;
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
  document.addEventListener('mousemove', onResizeMove);
  document.addEventListener('mouseup', onResizeEnd);
};

const onResizeMove = (e) => {
  if (!resizing) return;
  const dx = e.clientX - startX;
  const newWidth = Math.min(MAX_SIDEBAR, Math.max(MIN_SIDEBAR, startWidth + dx));
  sidebarWidth.value = newWidth;
};

const onResizeEnd = () => {
  resizing = false;
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
  document.removeEventListener('mousemove', onResizeMove);
  document.removeEventListener('mouseup', onResizeEnd);
};

// ============ 树配置 ============
const treeKeys = {
  value: 'node_id',
  label: 'display_name',
  children: 'children',
};

// ============ 节点显示名映射 ============
const getDisplayName = (node) => {
  if (node.node_type === 'project') return node.project_name || '';
  if (node.node_type === 'milestone') return node.milestone_name || '';
  if (node.node_type === 'group') return node.group_value || node.display_name || '';
  if (node.node_type === 'market_requirement') {
    const rdc = node.rdc_id ? `${node.rdc_id} | ` : '';
    return `${rdc}${node.title || ''}`;
  }
  return '';
};

// ============ 树数据处理 ============
const processTreeData = (nodes) => {
  if (!nodes || !Array.isArray(nodes)) return [];
  return nodes.map((node) => ({
    ...node,
    display_name: getDisplayName(node),
    children: node.children ? processTreeData(node.children) : [],
  }));
};

// ============ 加载树 ============
const loadTree = async (scope = tabValue.value) => {
  if (treeAbortController.value) {
    treeAbortController.value.abort();
  }
  treeAbortController.value = new AbortController();

  treeLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_requirement_tree`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: treeAbortController.value.signal,
      body: JSON.stringify({ scope, forceRefresh: forceRefresh.value, groupBy: groupBy.value || undefined }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }

    const tree = res.data?.tree || [];
    treeData.value = processTreeData(tree);

    expandedKeys.value = treeData.value.map((n) => n.node_id);
  } catch (e) {
    if (e?.name === 'AbortError') return;
    MessagePlugin.error(`读取需求树失败：${e.message || e}`);
    treeData.value = [];
  } finally {
    if (treeAbortController.value?.signal?.aborted) return;
    treeLoading.value = false;
  }
};

// ============ 分组切换 ============
const onGroupByChange = () => {
  isGroupNodeSelected.value = false;
  currentGroupNode.value = null;
  groupDetailItems.value = [];
  currentGroupCategory.value = '';
  loadTree();
};

// ============ 刷新树 ============
const refreshTree = async () => {
  refreshLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_requirement_tree_refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope: tabValue.value }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }
    lastRefreshTime.value = res.data?.refreshedAt || '';
    MessagePlugin.success('需求树缓存刷新成功');
    await loadTree(tabValue.value);
  } catch (e) {
    MessagePlugin.error(`刷新需求树失败：${e.message || e}`);
  } finally {
    refreshLoading.value = false;
  }
};

// ============ Tab 切换 ============
const onTabChange = (value) => {
  tabValue.value = value;
  treeData.value = [];
  expandedKeys.value = [];
  activedKeys.value = [];
  isGroupNodeSelected.value = false;
  currentGroupNode.value = null;
  groupDetailItems.value = [];
  currentGroupCategory.value = '';
  graphNodes.value = [];
  graphEdges.value = [];
  currentSeedNode.value = null;
  Object.keys(nodePositions).forEach(key => { delete nodePositions[key]; });
  loadTree(value);
};

// 获取链接显示文字
const getLinkDisplayText = (url, typeLabel, nodeName, customName) => {
  if (typeLabel === '需求实例化') {
    const displayName = customName || nodeName;
    if (displayName && displayName.trim()) {
      return displayName;
    }
  }
  return url || '查看详情';
};

// 退出全屏
const exitFullscreen = () => {
  isFullscreen.value = false;
  nextTick(() => {
    setTimeout(() => {
      centerGraph();
    }, 100);
  });
};

// ============ 加载分组详情 ============
const loadGroupDetail = async (groupNode) => {
  let milestoneName = null;
  let currentNode = groupNode;
  
  const findParentMilestone = (nodes, parentId) => {
    for (const node of nodes) {
      if (node.node_id === parentId) {
        if (node.node_type === 'milestone') {
          return node.milestone_name;
        }
        return null;
      }
      if (node.children && node.children.length) {
        const found = findParentMilestone(node.children, parentId);
        if (found) return found;
      }
    }
    return null;
  };
  
  milestoneName = findParentMilestone(treeData.value, groupNode.parent_id);
  
  let categoryValue = groupNode.group_value || '';
  categoryValue = categoryValue.replace(/[（(]\d+[）)]$/, '');
  
  groupDetailLoading.value = true;
  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_requirement_tree_group_detail`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scope: tabValue.value,
        groupBy: groupNode.group_field || 'knowledge_completeness',
        category: categoryValue,
        milestoneName: milestoneName || undefined,
      }),
    });
    const res = await resp.json();
    if (!resp.ok || res.code !== 200) {
      throw new Error(res.message || `请求失败(${resp.status})`);
    }
    groupDetailItems.value = res.data?.items || [];
    currentGroupCategory.value = res.data?.category || categoryValue;
    MessagePlugin.success(`加载分组详情成功，共 ${groupDetailItems.value.length} 条数据`);
  } catch (e) {
    MessagePlugin.error(`加载分组详情失败：${e.message || e}`);
    groupDetailItems.value = [];
    currentGroupCategory.value = categoryValue;
  } finally {
    groupDetailLoading.value = false;
  }
};

// 刷新分组详情
const refreshGroupDetail = () => {
  if (currentGroupNode.value) {
    loadGroupDetail(currentGroupNode.value);
  }
};

// ============ 解析 knowledgeContent JSON 字符串 ============
const parseKnowledgeContent = (knowledgeContent) => {
  if (!knowledgeContent) return {};
  try {
    if (typeof knowledgeContent === 'string') {
      return JSON.parse(knowledgeContent);
    }
    if (typeof knowledgeContent === 'object') {
      return knowledgeContent;
    }
    return {};
  } catch (e) {
    console.warn('Failed to parse knowledgeContent:', e);
    return {};
  }
};

// ============ 树节点点击 ============
const onTreeNodeClick = (value, context) => {
  const node = context?.node?.data;
  if (!node) return;

  if (node.node_type === 'group') {
    isGroupNodeSelected.value = true;
    currentGroupNode.value = node;
    loadGroupDetail(node);
  } else {
    isGroupNodeSelected.value = false;
    currentGroupNode.value = null;
    groupDetailItems.value = [];
    currentGroupCategory.value = '';

    loadDetail(node);
    currentSeedNode.value = node;
    loadGraphData(node.node_id, tabValue.value);
  }
};

// ============ 展开/收起 ============
const getAllNodeIds = (nodes) => {
  let ids = [];
  nodes.forEach((node) => {
    ids.push(node.node_id);
    if (node.children?.length) {
      ids = ids.concat(getAllNodeIds(node.children));
    }
  });
  return ids;
};

const expandAll = () => {
  expandedKeys.value = getAllNodeIds(treeData.value);
};

const collapseAll = () => {
  expandedKeys.value = [];
};

// ============ 明细数据 ============
const detail = ref({
  basicInfo: '',
  rdcId: '',
  status: '',
  mainDomain: '',
  instanceUrl: '',
  solutionStatus: '',
  solutionDocUrl: '',
});

const loadDetail = (node) => {
  const nodeType = node.node_type;
  detail.value = {
    basicInfo: nodeType === 'project' ? node.project_name
      : nodeType === 'milestone' ? node.milestone_name
      : node.title || '',
    rdcId: node.rdc_id || '',
    status: node.status || '',
    mainDomain: node.main_domain || '',
    instanceUrl: node.instance_url || '',
    solutionStatus: node.solution_status || '',
    solutionDocUrl: node.solution_doc_url || '',
  };
};

// ============ 图相关状态 ============
const graphLoading = ref(false);
const graphNodes = ref([]);
const graphEdges = ref([]);
const currentSeedNode = ref(null);
const highlightedNodeId = ref(null);
const selectedNodeId = ref(null);

// 保存原始图数据
const allRawNodes = ref([]);
const allRawEdges = ref([]);

const zoom = ref(0.7);
const panX = ref(0);
const panY = ref(0);
const svgWidth = ref(2400);
const svgHeight = ref(1600);

const draggingNodeId = ref(null);
const dragOffset = reactive({ x: 0, y: 0 });
let dragStartPos = { x: 0, y: 0 };
let wasDragged = false;
const isCanvasDragging = ref(false);
const canvasDragStart = reactive({ x: 0, y: 0 });
const nodePositions = reactive({});

const isFullscreen = ref(false);

// Drawer 相关
const selectedNode = ref(null);
const drawerVisible = ref(false);
const selectedSectionContent = ref(null);
const selectedSectionName = ref('');
const isSectionHtml = ref(false);
const selectedEdge = ref(null);
const edgeDrawerVisible = ref(false);
const skillDrawerVisible = ref(false);
const skillTableData = ref([]);
const currentSelectedIndex = ref(null);

const hasGraphData = computed(() => graphNodes.value.length > 0);

const viewBox = computed(() => {
  const width = svgWidth.value / zoom.value;
  const height = svgHeight.value / zoom.value;
  return `${panX.value} ${panY.value} ${width} ${height}`;
});

// ============ PR 复用程度分类 ============
const prCategories = [
  { key: '全代码', label: '全代码', color: '#7c4dff' },
  { key: '微范式', label: '微范式', color: '#e65100' },
  { key: '配置化', label: '配置化', color: '#1565c0' },
  { key: '零代码', label: '零代码', color: '#2e7d32' },
  { key: '无标识', label: '无标识', color: '#757575' },
];

// ============ 节点类型配置 ============
const typeColorMap = {
  'project': { bg: '#e8f0fe', tag: '#1967d2', text: '#174ea6', label: '项目' },
  'milestone': { bg: '#e8f0fe', tag: '#1967d2', text: '#174ea6', label: '里程碑' },
  'product_requirement': { bg: '#ede7f6', tag: '#5e35b1', text: '#311b92', label: '产品需求' },
  'market_requirement': { bg: '#f3e8fd', tag: '#7b2fa0', text: '#4a148c', label: '市场需求' },
  'requirement_instance': { bg: '#fce4ec', tag: '#c62828', text: '#b71c1c', label: '需求实例化' },
  'requirement_solution': { bg: '#e8f5e9', tag: '#2e7d32', text: '#1b5e20', label: '需求方案' },
  'component_design': { bg: '#fff3e0', tag: '#e65100', text: '#bf360c', label: '组件功能设计' },
  'feature': { bg: '#fff8e1', tag: '#ff8f00', text: '#e65100', label: '特性' },
  'section': { bg: '#f1f8e9', tag: '#558b2f', text: '#33691e', label: '章节' },
  'component': { bg: '#e3f2fd', tag: '#1565c0', text: '#0d47a1', label: '组件' },
  'skill': { bg: '#f3e5f5', tag: '#7b1fa2', text: '#4a148c', label: '技能' },
  'skill_library': { bg: '#fff5f5', tag: '#e34d59', text: '#c62828', label: '技能库' },
  'requirement_analysis_skill': { bg: '#faf5ff', tag: '#9333ea', text: '#6b21a8', label: '需求分析技能库' },
  'solution_design_skill': { bg: '#eff6ff', tag: '#3b82f6', text: '#1e40af', label: '方案设计技能库' },
};

const NODE_CONFIG = {
  'project': { w: 260, h: 110, shape: 'ellipse' },
  'milestone': { w: 200, h: 70, shape: 'rect' },
  'product_requirement': { w: 380, h: 65, shape: 'rect' },
  'market_requirement': { w: 180, h: 65, shape: 'feature' },
  'requirement_instance': { w: 180, h: 65, shape: 'rect' },
  'requirement_solution': { w: 180, h: 65, shape: 'rect' },
  'component_design': { w: 200, h: 65, shape: 'feature' },
  'feature': { w: 200, h: 65, shape: 'feature' },
  'section': { w: 200, h: 65, shape: 'rect' },
  'component': { w: 200, h: 65, shape: 'feature' },
  'skill': { w: 220, h: 75, shape: 'rect' },
  'skill_library': { w: 200, h: 75, shape: 'rect' },
  'requirement_analysis_skill': { w: 200, h: 75, shape: 'rect' },
  'solution_design_skill': { w: 200, h: 75, shape: 'rect' },
};

// ============ 辅助函数 ============
const getTypeDisplay = (type) => {
  const map = {
    'project': '项目',
    'product_requirement': '产品需求',
    'milestone': '里程碑',
    'market_requirement': '市场需求',
    'requirement_instance': '需求实例化',
    'requirement_solution': '需求方案',
    'component_design': '组件功能设计',
    'feature': '特性',
    'section': '章节',
    'component': '组件',
    'skill': '技能',
    'skill_library': '技能库',
    'requirement_analysis_skill': '需求分析技能库',
    'solution_design_skill': '方案设计技能库',
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

const openUrl = (url) => {
  if (!url) {
    MessagePlugin.warning('该节点暂无关联链接');
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
};

const selectNode = (node) => {
  if (wasDragged) return;
  const fullNode = graphNodes.value.find(n => n.id === node.id);
  if (!fullNode) return;
  
  selectedNode.value = fullNode;
  selectedSectionContent.value = null;
  selectedSectionName.value = '';
  isSectionHtml.value = false;
  drawerVisible.value = true;
};

const openEdgeDrawer = (edge) => {
  selectedEdge.value = edge;
  
  if (edge.relationType === 'verifies') {
    edgeDrawerVisible.value = true;
  } else if (edge.relationType === 'relates_to') {
    // 关联边打开技能抽屉
    openSkillDrawerForEdge(edge);
  }
};

// 为特定边打开技能抽屉
const openSkillDrawerForEdge = (edge) => {
  selectedEdge.value = edge;
  skillTableData.value = [];
  
  const sourceNode = graphNodes.value.find(n => n.id === edge.source);
  if (!sourceNode) {
    skillDrawerVisible.value = true;
    return;
  }
  
  const sourceRawNode = allRawNodes.value?.find(n => n.id === edge.source);
  
  if (sourceRawNode) {
    const skillEdges = allRawEdges.value.filter(e => 
      e.source === edge.source && 
      e.relationType === 'relates_to'
    );
    
    skillEdges.forEach(skillEdge => {
      const skillNode = allRawNodes.value.find(n => n.id === skillEdge.target && n.type === 'skill');
      if (skillNode) {
        const prRdcId = sourceRawNode.rawData?.rdc_id || sourceRawNode.id;
        const prTitle = sourceRawNode.name || '';
        const reuseDegree = sourceRawNode.rawData?.reuse_degree || '';
        const skillUrl = skillNode.rawData?.urls?.[0] || skillNode.url || '';
        
        let type = '无标识';
        if (reuseDegree === '微范式') {
          type = '微范式';
        } else if (reuseDegree === '配置化') {
          type = '配置化';
        }
        
        skillTableData.value.push({
          prRdcId,
          prTitle,
          type,
          skillUrl,
          skillName: skillNode.name,
        });
      }
    });
  }
  
  skillDrawerVisible.value = true;
};

// 打开所有微范式和配置化 PR 抽屉
const openAllSkillsDrawer = () => {
  selectedEdge.value = null;
  skillTableData.value = [];
  
  const allPrNodes = allRawNodes.value?.filter(n => n.type === 'product_requirement') || [];
  
  allPrNodes.forEach(prNode => {
    const rawData = prNode.rawData || {};
    const reuseDegree = rawData.reuse_degree || '';
    
    if (reuseDegree !== '微范式' && reuseDegree !== '配置化') {
      return;
    }
    
    const prRdcId = rawData.rdc_id || prNode.id;
    const prTitle = prNode.name || '';
    
    const skillEdge = allRawEdges.value.find(e => 
      e.source === prNode.id && 
      e.relationType === 'relates_to'
    );
    
    let skillUrl = '';
    let skillName = '';
    
    if (skillEdge) {
      const skillNode = allRawNodes.value.find(n => n.id === skillEdge.target && n.type === 'skill');
      if (skillNode) {
        skillUrl = skillNode.rawData?.urls?.[0] || skillNode.url || '';
        skillName = skillNode.name;
      }
    }
    
    skillTableData.value.push({
      prRdcId,
      prTitle,
      type: reuseDegree,
      skillUrl,
      skillName,
    });
  });
  
  skillDrawerVisible.value = true;
};

// 保存技能数据修改
const saveSkillData = () => {
  MessagePlugin.success('修改已保存');
};

// 导出技能数据
const exportSkillData = () => {
  const dataStr = JSON.stringify(skillTableData.value, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'skill-data.json';
  a.click();
  URL.revokeObjectURL(url);
  MessagePlugin.success('数据已导出');
};

const handleDrawerClose = () => {
  selectedSectionContent.value = null;
  selectedSectionName.value = '';
};

const viewSectionContent = (section) => {
  const rawHtml = section.rawData?.raw_html || '';
  const sectionType = section.rawData?.section_type || section.name;
  selectedSectionName.value = sectionType;
  if (rawHtml && isHtmlDescription(rawHtml)) {
    isSectionHtml.value = true;
    selectedSectionContent.value = getProcessedHtmlContent(rawHtml);
  } else {
    isSectionHtml.value = false;
    selectedSectionContent.value = rawHtml || '暂无内容';
  }
};

const isHtmlDescription = (desc) => {
  if (!desc || typeof desc !== 'string') return false;
  return /<(html|body|div|span|p|a|img|table|ul|ol|li|h[1-6]|br|hr)[^>]*>/i.test(desc)
    || /<!DOCTYPE\s+html|<\?xml|<html/i.test(desc);
};

const getProcessedHtmlContent = (html) => {
  if (!html) return '';
  let processed = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  if (!/<html/i.test(processed) && !/<!DOCTYPE/i.test(processed)) {
    processed = `<div class="embedded-html-content">${processed}</div>`;
  }
  return processed;
};

const getChildBadgeText = (node) => {
  const parts = [];
  if (node.childFeatures?.length) parts.push(`特性${node.childFeatures.length}`);
  if (node.childComponents?.length) parts.push(`组件${node.childComponents.length}`);
  if (node.childSections?.length) parts.push(`章节${node.childSections.length}`);
  return parts.length ? `+ ${parts.join(' ')}` : '';
};

// ============ 图数据加载 ============
const loadGraphData = async (seedNodeId, scope) => {
  graphLoading.value = true;
  graphNodes.value = [];
  graphEdges.value = [];
  Object.keys(nodePositions).forEach(key => { delete nodePositions[key]; });

  try {
    const resp = await fetch(`${SERVER_API_URL}/api_data/API_Knowledge_requirement_graph_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        seedNodeId,
        scope,
        forceRefresh: forceRefresh.value,
      }),
    });
    const res = await resp.json();
    if (resp.ok && res.code === 200 && res.data) {
      buildGraphFromData(res.data);
      nextTick(() => {
        setTimeout(() => centerGraph(), 100);
      });
    } else {
      graphNodes.value = [];
      graphEdges.value = [];
    }
  } catch (error) {
    console.error('加载图数据失败:', error);
    graphNodes.value = [];
    graphEdges.value = [];
  } finally {
    graphLoading.value = false;
  }
};

const buildGraphFromData = (data) => {
  const processedNodes = [];
  allRawNodes.value = data.nodes || [];
  allRawEdges.value = data.edges || [];

  const mainTypes = ['market_requirement', 'product_requirement', 'requirement_instance', 'requirement_solution', 'component_design'];

  // 收集所有 skill 节点用于聚合
  const allSkillNodes = [];
  const skillNodeIds = new Set();

  // 按源节点分组 skill
  const skillsBySourceId = new Map();

  allRawNodes.value.forEach(node => {
    if (node.type === 'skill') {
      skillNodeIds.add(node.id);
      allSkillNodes.push(node);
    }
  });

  // 建立源节点到 skill 节点的映射
  allRawEdges.value.forEach(edge => {
    if (edge.relationType === 'relates_to' && skillNodeIds.has(edge.target)) {
      const skillNode = allRawNodes.value.find(n => n.id === edge.target);
      if (skillNode) {
        if (!skillsBySourceId.has(edge.source)) {
          skillsBySourceId.set(edge.source, []);
        }
        skillsBySourceId.get(edge.source).push(skillNode);
      }
    }
  });

  // 处理主要类型的节点
  allRawNodes.value.forEach(node => {
    const cfg = NODE_CONFIG[node.type] || { w: 200, h: 80, shape: 'rect' };
    
    if (node.type === 'product_requirement') {
      return;
    }
    
    if (node.type === 'skill') {
      return;
    }
    
    if (node.type === 'requirement_analysis_skill') {
      const rawData = node.rawData || {};
      const skillRecords = [];
      
      if (rawData.records && Array.isArray(rawData.records)) {
        rawData.records.forEach(record => {
          const chapterName = record.chapterName || '';
          const useSkill = record.useSkill || {};
          // 输入知识：knowledgeContent 中的所有内容
          const inputKnowledge = parseKnowledgeContent(record.knowledgeContent);
          // 回馈/沉淀知识：accumulateBusinessKnowledge 中的所有内容
          const feedbackKnowledge = record.accumulateBusinessKnowledge || {};
          
          skillRecords.push({
            chapterName: chapterName,
            useSkill: useSkill,
            inputKnowledge: inputKnowledge,
            feedbackKnowledge: feedbackKnowledge,
          });
        });
      }
      
      processedNodes.push({
        id: node.id,
        name: node.name.length > 30 ? node.name.substring(0, 27) + '...' : node.name,
        fullName: node.name,
        type: node.type,
        typeLabel: node.typeLabel || getTypeDisplay(node.type),
        url: node.url || '',
        shape: cfg.shape,
        width: cfg.w,
        height: cfg.h,
        level: node.level || 0,
        parentNodeId: node.parentNodeId || '',
        childCount: 0,
        childFeatures: [],
        childSections: [],
        childComponents: [],
        rawData: node.rawData || {},
        skillRecords: skillRecords,
        skillCount: skillRecords.length,
      });
      return;
    }
    
    if (node.type === 'solution_design_skill') {
      const rawData = node.rawData || {};
      const skillRecords = [];
      
      if (rawData.records && Array.isArray(rawData.records)) {
        rawData.records.forEach(record => {
          const chapterName = record.chapterName || '';
          const useSkill = record.useSkill || {};
          // 输入知识：knowledgeContent 中的所有内容
          const inputKnowledge = parseKnowledgeContent(record.knowledgeContent);
          // 回馈/沉淀知识：accumulateBusinessKnowledge 中的所有内容
          const feedbackKnowledge = record.accumulateBusinessKnowledge || {};
          
          skillRecords.push({
            chapterName: chapterName,
            useSkill: useSkill,
            inputKnowledge: inputKnowledge,
            feedbackKnowledge: feedbackKnowledge,
          });
        });
      }
      
      processedNodes.push({
        id: node.id,
        name: node.name.length > 30 ? node.name.substring(0, 27) + '...' : node.name,
        fullName: node.name,
        type: node.type,
        typeLabel: node.typeLabel || getTypeDisplay(node.type),
        url: node.url || '',
        shape: cfg.shape,
        width: cfg.w,
        height: cfg.h,
        level: node.level || 0,
        parentNodeId: node.parentNodeId || '',
        childCount: 0,
        childFeatures: [],
        childSections: [],
        childComponents: [],
        rawData: node.rawData || {},
        skillRecords: skillRecords,
        skillCount: skillRecords.length,
      });
      return;
    }
    
    if (mainTypes.includes(node.type)) {
      const childNodes = allRawNodes.value.filter(n =>
        allRawEdges.value.some(e => e.source === node.id && e.target === n.id && !mainTypes.includes(n.type) && n.type !== 'skill')
      );
      const childFeatures = childNodes.filter(n => n.type === 'feature');
      const childSections = childNodes.filter(n => n.type === 'section');
      const childComponents = childNodes.filter(n => n.type === 'component');
      const childCount = childNodes.length;

      // 收集关联的 skill 节点 ID（用于显示徽章）
      const relatedSkillNodes = skillsBySourceId.get(node.id) || [];
      const relatedSkillIds = relatedSkillNodes.map(s => s.id);

      processedNodes.push({
        id: node.id,
        name: node.name.length > 30 ? node.name.substring(0, 27) + '...' : node.name,
        fullName: node.name,
        type: node.type,
        typeLabel: node.typeLabel || getTypeDisplay(node.type),
        url: node.url || '',
        shape: cfg.shape,
        width: cfg.w,
        height: cfg.h,
        level: node.level || 0,
        parentNodeId: node.parentNodeId || '',
        childCount,
        childFeatures,
        childSections,
        childComponents,
        relatedSkillIds,
        rawData: node.rawData || {},
      });
    }
  });
  
  // 处理 PR 节点聚合
  const prNodes = allRawNodes.value.filter(n => n.type === 'product_requirement');
  if (prNodes.length > 0) {
    const categories = ['全代码', '微范式', '配置化', '零代码'];
    const counts = {};
    categories.forEach(c => counts[c] = 0);
    counts['无标识'] = 0;
    const items = [];

    prNodes.forEach(pr => {
      const rd = pr.rawData || {};
      const degree = rd.reuse_degree || '';
      const cat = categories.includes(degree) ? degree : '无标识';
      counts[cat]++;
      items.push({
        id: rd.rdc_id || pr.id,
        title: pr.name,
        reuse_degree: degree,
        detail_design_url: rd.detail_design_url || '',
        development_type: rd.development_type || '',
        detail_category: rd.detail_category || '',
      });
    });

    const seedNode = allRawNodes.value.find(n => n.type === 'market_requirement');
    const seedId = seedNode ? seedNode.id : '';

    processedNodes.push({
      id: 'pr_aggregated',
      name: `产品需求(${prNodes.length})`,
      fullName: `产品需求(${prNodes.length})`,
      type: 'product_requirement',
      typeLabel: '产品需求',
      url: '',
      shape: 'rect',
      width: 360,
      height: 160,
      level: 1,
      parentNodeId: seedId,
      childCount: 0,
      childFeatures: [],
      childSections: [],
      childComponents: [],
      rawData: {},
      prSummary: { counts, items },
    });
  }

  // 聚合所有 skill 节点为一个技能库节点
  if (allSkillNodes.length > 0) {
    const skillList = allSkillNodes.map(skill => ({
      id: skill.id,
      skill_name: skill.name,
      skill_url: skill.url || skill.rawData?.urls?.[0] || '',
      source_page: '技能库',
    }));
    
    processedNodes.push({
      id: 'skill_library_aggregated',
      name: `技能 (${allSkillNodes.length})`,
      fullName: `技能库 (${allSkillNodes.length}个技能)`,
      type: 'skill_library',
      typeLabel: '技能',
      url: '',
      shape: 'rect',
      width: 200,
      height: 75,
      level: 2,
      parentNodeId: '',
      childCount: 0,
      childFeatures: [],
      childSections: [],
      childComponents: [],
      rawData: {},
      skillList: skillList,
      skillCount: skillList.length,
    });
  }

  graphNodes.value = processedNodes;

  // 处理边
  const prNodeIds = new Set(prNodes.map(n => n.id));
  const processedEdges = [];
  
  allRawEdges.value.forEach(edge => {
    let source = edge.source;
    let target = edge.target;
    
    if (prNodeIds.has(target)) target = 'pr_aggregated';
    if (prNodeIds.has(source)) source = 'pr_aggregated';
    
    // 将指向 skill 节点的边重定向到技能库聚合节点
    if (skillNodeIds.has(target)) target = 'skill_library_aggregated';
    if (skillNodeIds.has(source)) source = 'skill_library_aggregated';

    const sourceExists = processedNodes.find(n => n.id === source);
    const targetExists = processedNodes.find(n => n.id === target);
    if (sourceExists && targetExists) {
      const edgeKey = `${source}-${target}-${edge.relationType}`;
      const existingEdge = processedEdges.find(e => 
        e.source === source && e.target === target && e.relationType === edge.relationType
      );
      if (!existingEdge) {
        processedEdges.push({
          id: edge.id,
          source,
          target,
          relationType: edge.relationType,
          relationLabel: edge.relationLabel,
          rawData: edge.rawData || {},
        });
      }
    }
  });
  
  const edgeKeys = new Set();
  graphEdges.value = [...processedEdges.filter(e => {
    const key = `${e.source}-${e.target}-${e.relationType}`;
    if (edgeKeys.has(key)) return false;
    edgeKeys.add(key);
    return true;
  })];

  initializeGraphPositions();

  processedNodes.forEach(node => {
    if (!nodePositions[node.id]) {
      nodePositions[node.id] = { x: 0, y: 0 };
    }
  });
};

// ============ 图布局 ============
const layoutColumn = (nodes, x, startY, verticalSpacing = 120) => {
  if (!nodes || nodes.length === 0) return;
  nodes.forEach((node, i) => {
    const cfg = NODE_CONFIG[node.type];
    if (cfg) {
      nodePositions[node.id] = { 
        x: x, 
        y: startY + i * verticalSpacing 
      };
    }
  });
};

const initializeGraphPositions = () => {
  Object.keys(nodePositions).forEach(key => { delete nodePositions[key]; });

  const centerNodes = graphNodes.value.filter(n => n.level === 0);
  if (centerNodes.length === 0) return;

  const centerNode = centerNodes[0];
  const startX = 80;
  const cy = 400;
  const colGap = 350;
  const verticalSpacing = 120;

  const childrenByType = {
    'milestone': graphNodes.value.filter(n => n.level === 1 && n.type === 'milestone'),
    'market_requirement': graphNodes.value.filter(n => n.level === 2 && n.type === 'market_requirement'),
    'requirement_instance': graphNodes.value.filter(n => n.level === 1 && n.type === 'requirement_instance'),
    'requirement_solution': graphNodes.value.filter(n => n.level === 1 && n.type === 'requirement_solution'),
    'component_design': graphNodes.value.filter(n => n.level === 2 && n.type === 'component_design'),
    'skill_library': graphNodes.value.filter(n => n.type === 'skill_library'),
    'requirement_analysis_skill': graphNodes.value.filter(n => n.type === 'requirement_analysis_skill'),
    'solution_design_skill': graphNodes.value.filter(n => n.type === 'solution_design_skill'),
  };

  const isRequirementGraph = childrenByType['requirement_instance'].length > 0
    || childrenByType['requirement_solution'].length > 0
    || childrenByType['component_design'].length > 0;

  if (isRequirementGraph) {
    const instNodes = childrenByType['requirement_instance'];
    const instY = cy;
    layoutColumn(instNodes, startX, instY);

    const rootCfg = NODE_CONFIG[centerNode.type];
    const firstInst = instNodes[0];
    const rootX = firstInst ? (nodePositions[firstInst.id]?.x ?? startX) : startX;
    const rootY = firstInst
      ? (nodePositions[firstInst.id]?.y ?? cy) - rootCfg.h - 80
      : cy - rootCfg.h / 2;
    nodePositions[centerNode.id] = { x: rootX, y: rootY };

    layoutColumn(childrenByType['requirement_solution'], startX + colGap, cy);
    layoutColumn(childrenByType['component_design'], startX + colGap * 2, cy);
    
    const reqAnalysisSkills = childrenByType['requirement_analysis_skill'];
    if (reqAnalysisSkills.length > 0 && instNodes.length > 0) {
      const firstInstNode = instNodes[0];
      const instPos = nodePositions[firstInstNode.id];
      if (instPos) {
        const instCfg = NODE_CONFIG[firstInstNode.type];
        const skillX = instPos.x;
        const skillY = instPos.y + (instCfg?.h || 65) + verticalSpacing;
        reqAnalysisSkills.forEach((skill, idx) => {
          nodePositions[skill.id] = {
            x: skillX,
            y: skillY + idx * verticalSpacing
          };
        });
      }
    }
    
    const solDesignSkills = childrenByType['solution_design_skill'];
    if (solDesignSkills.length > 0) {
      const solutionNodes = childrenByType['requirement_solution'];
      if (solutionNodes.length > 0) {
        const firstSolutionNode = solutionNodes[0];
        const solPos = nodePositions[firstSolutionNode.id];
        if (solPos) {
          const solCfg = NODE_CONFIG[firstSolutionNode.type];
          const skillX = solPos.x;
          const skillY = solPos.y + (solCfg?.h || 65) + verticalSpacing;
          solDesignSkills.forEach((skill, idx) => {
            nodePositions[skill.id] = {
              x: skillX,
              y: skillY + idx * verticalSpacing
            };
          });
        }
      } else {
        layoutColumn(solDesignSkills, startX + colGap, cy + 150, verticalSpacing);
      }
    }

    const prNode = graphNodes.value.find(n => n.type === 'product_requirement');
    if (prNode) {
      const compDesNodes = childrenByType['component_design'];
      const compDesX = compDesNodes.length > 0 ? (nodePositions[compDesNodes[0].id]?.x ?? startX + colGap * 2) : startX + colGap * 2;
      const prY = nodePositions[centerNode.id]?.y ?? (cy - rootCfg.h / 2);
      nodePositions[prNode.id] = { x: compDesX, y: prY };
    }
    
    const skillLibNode = graphNodes.value.find(n => n.type === 'skill_library');
    if (skillLibNode && prNode) {
      const prPos = nodePositions[prNode.id];
      const prHeight = NODE_CONFIG[prNode.type]?.h || 65;
      const libCfg = NODE_CONFIG[skillLibNode.type];
      nodePositions[skillLibNode.id] = { 
        x: prPos.x + (prNode.width - libCfg.w)/2 + 160, 
        y: prPos.y + prHeight + 190
      };
    }
  } else {
    const cx = 600;
    const rootCfg = NODE_CONFIG[centerNode.type];
    nodePositions[centerNode.id] = { x: cx - rootCfg.w / 2, y: cy - rootCfg.h / 2 };

    const milestones = childrenByType['milestone'];
    const msRadius = 420;
    const msStartAngle = 70;
    const msEndAngle = 110;
    milestones.forEach((node, i) => {
      const cfg = NODE_CONFIG[node.type];
      const angleSpan = milestones.length === 1 ? 0 : msEndAngle - msStartAngle;
      const angle = milestones.length === 1
        ? (msStartAngle + msEndAngle) / 2
        : msStartAngle + angleSpan * (i / (milestones.length - 1));
      const radius = msRadius + (i % 2) * 50;
      const rad = (angle * Math.PI) / 180;
      nodePositions[node.id] = {
        x: cx + radius * Math.cos(rad) - cfg.w / 2,
        y: cy - radius * Math.sin(rad) - cfg.h / 2,
      };
    });

    const requirements = childrenByType['market_requirement'];
    const reqRadius = 800;
    const reqStartAngle = 330;
    const reqEndAngle = 30;
    requirements.forEach((node, i) => {
      const cfg = NODE_CONFIG[node.type];
      let angle;
      if (requirements.length === 1) {
        angle = 0;
      } else {
        const totalSpan = 360 - (reqStartAngle - reqEndAngle);
        const step = totalSpan / requirements.length;
        angle = reqStartAngle + step * i;
        if (angle >= 360) angle -= 360;
      }
      const radius = reqRadius + (i % 3) * 60;
      const rad = (angle * Math.PI) / 180;
      nodePositions[node.id] = {
        x: cx + radius * Math.cos(rad) - cfg.w / 2,
        y: cy - radius * Math.sin(rad) - cfg.h / 2,
      };
    });
    
    const reqAnalysisSkills = childrenByType['requirement_analysis_skill'];
    if (reqAnalysisSkills.length > 0) {
      const instNode = graphNodes.value.find(n => n.type === 'requirement_instance');
      if (instNode && nodePositions[instNode.id]) {
        const instPos = nodePositions[instNode.id];
        const instCfg = NODE_CONFIG[instNode.type];
        reqAnalysisSkills.forEach((skill, idx) => {
          nodePositions[skill.id] = {
            x: instPos.x,
            y: instPos.y + (instCfg?.h || 65) + verticalSpacing + idx * verticalSpacing
          };
        });
      }
    }
    
    const solDesignSkills = childrenByType['solution_design_skill'];
    if (solDesignSkills.length > 0) {
      const solNode = graphNodes.value.find(n => n.type === 'requirement_solution');
      if (solNode && nodePositions[solNode.id]) {
        const solPos = nodePositions[solNode.id];
        const solCfg = NODE_CONFIG[solNode.type];
        solDesignSkills.forEach((skill, idx) => {
          nodePositions[skill.id] = {
            x: solPos.x,
            y: solPos.y + (solCfg?.h || 65) + verticalSpacing + idx * verticalSpacing
          };
        });
      }
    }
    
    const skillLibNode = graphNodes.value.find(n => n.type === 'skill_library');
    if (skillLibNode) {
      const skillX = startX + colGap * 3;
      const skillY = cy + 200;
      nodePositions[skillLibNode.id] = { x: skillX, y: skillY };
    }
  }

  let orphanIdx = 0;
  graphNodes.value.forEach(node => {
    if (!nodePositions[node.id]) {
      const angle = (orphanIdx * 30) * Math.PI / 180;
      const radius = 500 + (orphanIdx % 3) * 80;
      const cx = 600;
      const cfg = NODE_CONFIG[node.type] || { w: 200, h: 80 };
      nodePositions[node.id] = {
        x: cx + radius * Math.cos(angle) - cfg.w / 2,
        y: cy + radius * Math.sin(angle) - cfg.h / 2,
      };
      orphanIdx++;
    }
  });
};

// ============ 计算属性 ============
const allNodes = computed(() => {
  if (!graphNodes.value.length) return [];

  return graphNodes.value.map(node => {
    const cfg = NODE_CONFIG[node.type] || { w: 200, h: 80, shape: 'rect' };
    const pos = nodePositions[node.id] || { x: 0, y: 0 };
    const typeWidth = getTextWidth(node.typeLabel, 11) + 16;
    
    return {
      id: node.id,
      name: node.name,
      fullName: node.fullName,
      type: node.type,
      typeLabel: node.typeLabel,
      desc: node.desc,
      url: node.url,
      shape: node.shape || cfg.shape,
      x: pos.x,
      y: pos.y,
      width: cfg.w,
      height: cfg.h,
      typeX: cfg.w / 2 - typeWidth / 2,
      typeWidth: typeWidth,
      textY: cfg.h / 2 + 5,
      bgColor: getTypeBgColor(node.type),
      tagColor: getTypeColor(node.type),
      textColor: getTypeTextColor(node.type),
      childCount: node.childCount,
      childFeatures: node.childFeatures,
      childSections: node.childSections,
      childComponents: node.childComponents,
      relatedSkillIds: node.relatedSkillIds || [],
      rawData: node.rawData || {},
      prSummary: node.prSummary,
      skillList: node.skillList || [],
      skillCount: node.skillCount || 0,
      skillRecords: node.skillRecords || [],
    };
  });
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

  const curveMidX = 0.25 * startX + 0.5 * midX + 0.25 * endX;
  const curveMidY = 0.25 * startY + 0.5 * midY + 0.25 * endY;

  return {
    path: `M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`,
    labelX: curveMidX,
    labelY: curveMidY,
    labelWidth: getTextWidth(labelText, 10) + 16,
    highlighted: highlightedNodeId.value === fromId || highlightedNodeId.value === toId,
  };
};

const containsEdges = computed(() => {
  const edges = [];
  graphEdges.value.forEach((edge, idx) => {
    if (edge.relationType === 'contains') {
      const offsetX = (idx % 2 === 0 ? 15 : -15);
      const offsetY = idx * 8 - 12;
      const edgeCalc = calcEdge(edge.source, edge.target, '包含', offsetX, offsetY);
      if (edgeCalc) edges.push({ id: edge.id, ...edgeCalc });
    }
  });
  return edges;
});

const affectsEdges = computed(() => {
  const edges = [];
  graphEdges.value.forEach((edge, idx) => {
    if (edge.relationType === 'affects') {
      const offsetX = idx * 12 - 12;
      const offsetY = idx * 8 - 8;
      const edgeCalc = calcEdge(edge.source, edge.target, '波及', offsetX, offsetY);
      if (edgeCalc) edges.push({ id: edge.id, ...edgeCalc });
    }
  });
  return edges;
});

const relatesEdges = computed(() => {
  const edges = [];
  graphEdges.value.forEach((edge, idx) => {
    if (edge.relationType === 'relates_to') {
      const offsetX = idx * 15 - 15;
      const offsetY = 20 + idx * 5;
      const edgeCalc = calcEdge(edge.source, edge.target, '关联', offsetX, offsetY);
      if (edgeCalc) edges.push({ id: edge.id, ...edgeCalc, rawData: edge.rawData || {} });
    }
  });
  return edges;
});

const verifiesEdges = computed(() => {
  const edges = [];
  graphEdges.value.forEach((edge, idx) => {
    if (edge.relationType === 'verifies') {
      const labelText = edge.relationLabel || '校验';
      const isMatch = labelText === '匹配';
      const offsetX = idx * 12 - 12;
      const offsetY = 25 + idx * 5;
      const edgeCalc = calcEdge(edge.source, edge.target, labelText, offsetX, offsetY);
      if (edgeCalc) edges.push({ 
        id: edge.id, 
        ...edgeCalc, 
        labelText, 
        isMatch, 
        rawData: edge.rawData || {},
        relationType: 'verifies'
      });
    }
  });
  return edges;
});

// ============ 交互事件 ============
const highlightNode = (nodeId) => {
  highlightedNodeId.value = nodeId;
};

const clearHighlight = () => {
  highlightedNodeId.value = null;
};

const onSvgMouseDown = (e) => {
  if (e.target.closest('.nodes-group g')) return;
  isCanvasDragging.value = true;
  canvasDragStart.x = e.clientX;
  canvasDragStart.y = e.clientY;
};

const onSvgMouseMove = (e) => {
  if (draggingNodeId.value) {
    const dx = e.clientX - dragStartPos.x;
    const dy = e.clientY - dragStartPos.y;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) wasDragged = true;

    const rect = e.currentTarget.getBoundingClientRect();
    const svgX = (e.clientX - rect.left) / zoom.value + panX.value;
    const svgY = (e.clientY - rect.top) / zoom.value + panY.value;

    const node = allNodes.value.find(n => n.id === draggingNodeId.value);
    if (node) {
      nodePositions[draggingNodeId.value] = {
        x: svgX - dragOffset.x,
        y: svgY - dragOffset.y,
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

  wasDragged = false;
  dragStartPos = { x: e.clientX, y: e.clientY };

  const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect();
  const svgX = (e.clientX - rect.left) / zoom.value + panX.value;
  const svgY = (e.clientY - rect.top) / zoom.value + panY.value;

  const pos = nodePositions[nodeId];
  if (pos) {
    dragOffset.x = svgX - pos.x;
    dragOffset.y = svgY - pos.y;
  }
  draggingNodeId.value = nodeId;
  selectedNodeId.value = nodeId;
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
    svgHeight.value / (contentHeight + padding * 2),
  ));
  zoom.value = targetZoom * 0.9;
  panX.value = minX - padding;
  panY.value = minY - padding;
};

const autoLayout = () => {
  if (graphNodes.value.length > 0) {
    initializeGraphPositions();
    MessagePlugin.success('已恢复自动布局');
  } else {
    MessagePlugin.warning('暂无图数据');
  }
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  nextTick(() => {
    setTimeout(() => {
      if (isFullscreen.value) centerGraph();
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

onUnmounted(() => {
  document.removeEventListener('mousemove', onResizeMove);
  document.removeEventListener('mouseup', onResizeEnd);
  if (treeAbortController.value) {
    treeAbortController.value.abort();
  }
  window.removeEventListener('keydown', onKeyDown);
  document.body.style.overflow = '';
});
</script>

<style scoped>
/* 保持原有样式不变 */
.requirements-main {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
}

.toolbar {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
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
  display: flex;
  align-items: center;
  gap: 4px;
}

.main-layout {
  flex: 1;
  display: flex;
  padding: 0 16px 16px;
  overflow: hidden;
}

.tree-sidebar {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
}

.resize-bar {
  width: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: col-resize;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.resize-bar-inner {
  width: 4px;
  height: 32px;
  border-radius: 2px;
  background: #d0d5dd;
  transition: background 0.2s, height 0.2s;
}

.resize-bar:hover .resize-bar-inner {
  background: #0052d9;
  height: 48px;
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

.tree-group-tabs {
  padding: 8px 16px;
  border-bottom: 1px solid #eef2f6;
  display: flex;
  justify-content: center;
}

.tree-search {
  padding: 8px 12px 4px;
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

.tree-loading,
.tree-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #98a2b3;
}

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

.flowchart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
  max-height: 700px;
  overflow: hidden;
  position: relative;
}

.flowchart-container {
  flex: 1;
  background: white;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 12px 12px;
  overflow: hidden;
  min-height: 300px;
}

.flowchart-container.fullscreen-chart {
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

.detail-table-container {
  flex: 1;
  background: white;
  border: 1px solid #e5e7eb;
  border-top: none;
  border-radius: 0 0 12px 12px;
  overflow: auto;
  padding: 0;
  min-height: 300px;
}

.detail-table-container :deep(.t-table) {
  height: 100%;
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

.edge-clickable {
  cursor: pointer;
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

.nodes-group g.dragging {
  filter: drop-shadow(0 8px 24px rgba(0, 82, 217, 0.3));
}

.nodes-group g.dragging .node-shape {
  stroke: #0052d9 !important;
  stroke-width: 2.5 !important;
}

.link-indicator {
  cursor: pointer;
}

.link-indicator:hover circle {
  fill: #e8f0fe;
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

.graph-loading,
.graph-empty {
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

.detail-section {
  display: flex;
  flex-direction: column;
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
  min-height: 200px;
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

.node-detail .detail-section {
  margin-bottom: 24px;
}

.pr-category-group {
  margin-bottom: 12px;
}

.pr-category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #f8f9fb;
  border-radius: 6px;
  margin-bottom: 6px;
}

.pr-category-name {
  font-size: 13px;
  font-weight: 600;
}

.pr-category-count {
  font-size: 12px;
  color: #98a2b3;
}

.pr-id-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 12px;
}

.pr-id-tag {
  cursor: pointer;
  font-size: 12px;
}

.node-detail .detail-label {
  font-size: 12px;
  font-weight: 500;
  color: #98a2b3;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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

.child-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.child-tag {
  cursor: pointer;
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8f9fb;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.section-item:hover {
  background: #e8f0fe;
}

.section-title {
  flex: 1;
  font-size: 13px;
  color: #344054;
}

.section-arrow {
  color: #98a2b3;
}

.section-content {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.html-description-content {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  line-height: 1.6;
  font-size: 13px;
  color: #344054;
}

.content-text {
  padding: 16px;
  font-size: 13px;
  color: #344054;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.url-container {
  background: #f8f9fb;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e5e7eb;
}

.no-data-tip {
  padding: 20px;
  text-align: center;
  color: #98a2b3;
  font-size: 13px;
}

.skill-library-content {
  margin-top: 8px;
}

.skill-table-container {
  padding: 16px;
}

.no-skills-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #98a2b3;
  gap: 12px;
}

.no-skills-tip p {
  margin: 0;
  font-size: 14px;
}

.three-column-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 180px);
  min-height: 400px;
}

.column-left,
.column-middle,
.column-right {
  display: flex;
  flex-direction: column;
  background: #f8f9fb;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.column-left {
  width: 320px;
  flex-shrink: 0;
}

.column-middle {
  width: 280px;
  flex-shrink: 0;
}

.column-right {
  flex: 1;
  min-width: 200px;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 14px;
  color: #1f2d3d;
}

.column-count {
  margin-left: auto;
  font-size: 12px;
  color: #98a2b3;
  font-weight: normal;
}

.column-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.column-content::-webkit-scrollbar {
  width: 4px;
}

.column-content::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}

.pr-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.pr-item:hover {
  border-color: #0052d9;
  box-shadow: 0 2px 8px rgba(0, 82, 217, 0.1);
}

.pr-item.active {
  border-color: #0052d9;
  background: #e8f0fe;
  box-shadow: 0 2px 8px rgba(0, 82, 217, 0.15);
}

.pr-id {
  font-size: 13px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 4px;
}

.pr-id .no-id {
  color: #98a2b3;
}

.pr-title {
  font-size: 12px;
  color: #667085;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.type-editor {
  padding: 12px;
}

.editor-label {
  font-size: 12px;
  color: #98a2b3;
  margin-bottom: 8px;
}

.current-pr-info {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.type-selector {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}

.type-selector .t-radio-button {
  width: 100%;
}

.type-description {
  margin-top: 16px;
}

.no-selection-tip,
.no-skill-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  color: #98a2b3;
  gap: 12px;
}

.no-selection-tip p,
.no-skill-tip p {
  margin: 0;
  font-size: 14px;
}

.skill-link-section {
  padding: 12px;
}

.skill-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12px;
}

.skill-url-display {
  margin-top: 16px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.skill-url-display .url-label {
  font-size: 12px;
  color: #98a2b3;
  display: block;
  margin-bottom: 8px;
}

.skill-url-display .url-text {
  font-size: 12px;
  color: #0052d9;
  word-break: break-all;
  line-height: 1.5;
}

.skill-url-display .url-text:hover {
  text-decoration: underline;
}

.bottom-action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-top: 1px solid #e5e7eb;
  margin-top: 16px;
}

.action-tip {
  margin-left: auto;
  font-size: 12px;
  color: #98a2b3;
}

/* 全屏模式下的浮动关闭按钮 */
.fullscreen-close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1002;
  transition: all 0.2s;
  color: white;
}

.fullscreen-close-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: scale(1.05);
}

/* ============ 新增技能库卡片样式 ============ */
.skill-records-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skill-record-card {
  background: #f8f9fb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.skill-record-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.record-chapter {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #e8f0fe;
  border-bottom: 1px solid #d0d5dd;
}

.chapter-name {
  font-size: 14px;
  font-weight: 600;
  color: #174ea6;
}

.record-section {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.record-section:last-child {
  border-bottom: none;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #344054;
  margin-bottom: 10px;
}

.section-label .t-icon {
  color: #667085;
}

.skill-links,
.knowledge-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 20px;
}

.skill-link-item,
.knowledge-link-item {
  font-size: 13px;
}

.empty-tip {
  color: #98a2b3;
  font-size: 12px;
  padding: 4px 0;
  padding-left: 20px;
}
</style>