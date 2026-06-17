<template>
  <div class="page-container">
    <!-- Tab 切换 -->
    <t-tabs v-model="currentTab" value="trend" @change="handleTabChange">
      <!-- Tab 1：需求预检趋势图 -->
      <t-tab-panel value="trend" label="需求预检趋势图" :lazy="false">
        <div class="trend-page-container">
          <div class="chart-grid">
            <!-- 左侧：曲线图 -->
            <t-card class="chart-card-modern" :bordered="false">
              <div class="card-title-bar">
                <span class="card-title-text">待整改需求变化趋势</span>
              </div>
              <div class="filter-section">
                <div class="filter-group">
                  <span class="filter-label">需求预规划</span>
                  <t-select
                    v-model="selectedTrendPreplanning"
                    placeholder="选择预规划"
                    multiple
                    filterable
                    clearable
                    :min-collapsed-num="1"
                    @change="changeTrendParams"
                    style="flex:1"
                  >
                    <t-option
                      v-for="item in requirementpreplanningOptions"
                      :key="item.value"
                      :value="item.value"
                      :label="item.label"
                    />
                  </t-select>
                </div>
                <div class="filter-group">
                  <span class="filter-label">统计日期</span>
                  <t-date-range-picker
                    v-model="trendDateRange"
                    format="YYYY-MM-DD"
                    value-type="YYYY-MM-DD"
                    :disable-date="disabledTrendDate"
                    @change="changeTrendParams"
                    style="flex:1"
                  />
                </div>
              </div>
              <div class="chart-body">
                <div 
                  ref="trendChart1Ref" 
                  class="chart-instance-modern"
                  style="width: 100%; height: 500px;"
                ></div>
              </div>
            </t-card>

            <!-- 右侧：饼图 -->
            <t-card class="chart-card-modern" :bordered="false">
              <div class="card-title-bar">
                <div class="title-bar-left">
                  <t-icon name="pie-chart" size="20" style="color: #e67c3b;"/>
                </div>
                <span class="card-title-text">待整改需求占比分析</span>
              </div>
              <div class="filter-section">
                <div class="filter-group">
                  <span class="filter-label">需求预规划</span>
                  <t-select
                    v-model="selectedPiePreplanning"
                    placeholder="选择预规划"
                    filterable
                    :options="requirementpreplanningOptions"
                    @change="changePieParams"
                    style="flex:1"
                  />
                </div>
                <div class="filter-group">
                  <span class="filter-label">分析维度</span>
                  <t-select
                    v-model="selectedPieField"
                    placeholder="选择维度"
                    :options="pieFieldOptions"
                    @change="changePieParams"
                    style="flex:1"
                  />
                </div>
              </div>
              <div class="chart-body">
                <div 
                  ref="pieChartRef" 
                  class="chart-instance-modern"
                  style="width: 100%; height: 500px;"
                ></div>
              </div>
            </t-card>
          </div>
        </div>
      </t-tab-panel>

      <!-- Tab 2：需求预检明细表 -->
      <t-tab-panel value="table" label="需求预检明细表" :lazy="false">
        <!-- 筛选器和按钮区域 - 核心优化部分 -->
        <div class="filters-container">
          <div class="filters">
            <!-- 第一行：4列等宽平均分布，右侧无空隙 -->
            <div class="filter-item">
              <span class="filter-label">需求预规划</span>
              <t-select
                v-model="selectedRequirementpreplanning"
                placeholder="请选择（可多选）"
                :options="requirementpreplanningTableOptions"
                filterable
                clearable
                multiple
                :max-collapsed-num="1"
                :min-collapsed-num="1"
                collapse-tags
                style="flex: 1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                @change="handleFilterChange"
              />
            </div>
            <div class="filter-item">
              <span class="filter-label">问题类型</span>
              <t-select
                v-model="selectedProblemType"
                placeholder="请选择（可多选）"
                :options="problemTypeOptions"
                filterable
                clearable
                multiple
                :max-collapsed-num="1"
                :min-collapsed-num="1"
                collapse-tags
                style="flex: 1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                @change="handleFilterChange"
              />
            </div>
            <div class="filter-item">
              <span class="filter-label">团队</span>
              <t-cascader
                v-model="selectedTeam"
                :options="teamOptions"
                placeholder="请选择（可多选）"
                filterable
                clearable
                multiple
                collapse-tags
                :max-collapsed-num="1"
                :min-collapsed-num="1"
                :check-strictly="false"
                :props="{ checkable: true, disabled: 'disabled' }"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                style="flex: 1"
                @change="handleFilterChange"
              />
            </div>
            <div class="filter-item">
              <span class="filter-label">整改责任人</span>
              <t-select
                v-model="selectedCalHandlePerson"
                placeholder="请选择"
                :options="calHandlePersonOptions"
                filterable
                clearable
                style="flex: 1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                @change="handleFilterChange"
              />
            </div>

            <!-- 第二行：精准对齐第一行对应列 -->
            <!-- 问题发现日期 -->
            <div class="filter-item">
              <span class="filter-label">问题发现日期</span>
              <t-date-range-picker
                v-model="checkDateRange"
                format="YYYY-MM-DD"
                value-type="YYYY-MM-DD"
                clearable
                @change="handleFilterChange"
                style="flex: 1"
              />
            </div>
            <div class="filter-item">
              <span class="filter-label">是否需整改</span>
              <t-select
                v-model="selectedCalProblemFlag"
                placeholder="请选择"
                :options="calProblemFlagOptions"
                filterable
                clearable
                style="flex: 1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                @change="handleFilterChange"
              />
            </div>
            <div class="filter-item">
              <span class="filter-label">是否已整改</span>
              <t-select
                v-model="selectedCalHandleFlag"
                placeholder="请选择"
                :options="calHandleFlagOptions"
                filterable
                clearable
                style="flex: 1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                @change="handleFilterChange"
              />
            </div>
            <!-- 按钮组合并，对齐"整改责任人"列，右对齐 -->
            <div class="filter-item filter-item-buttons" style="grid-column: 4 / span 1; justify-content: flex-end;">
              <t-tooltip 
                content="选择多个需求后，一键设置需求的信息，包括是否需整改、是否已整改、整改责任人、整改截止日期"
                placement="top"
                theme="light"
              >
                <t-button 
                  theme="primary" 
                  variant="outline" 
                  @click="handleBatchSet"
                  class="batch-btn"
                >
                  一键设置
                </t-button>
              </t-tooltip>
              <t-button theme="primary" variant="outline" @click="handleExport" class="export-btn">
                导出数据
              </t-button>
            </div>
          </div>
        </div>

        <!-- 表格区域 -->
        <div class="table-wrapper">
          <t-table
            v-if="tableShow"
            v-model:selected-row-keys="selectedRowKeys"
            :data="tableData"
            :columns="tableColumns"
            :scroll="{ x: 'max-content' }"
            :loading="tableLoading"
            :height="tableHeight"
            row-key="row_key"
            bordered
            stripe
            resizable
            hover
            :pagination="pagination"
            :select-on-row-click="true"
            @page-change="onPageChange"
          />
        </div>

        <!-- 批量设置对话框 -->
        <t-dialog
          v-model:visible="batchSetDialogVisible"
          header="一键设置"
          width="600px"
          :close-on-overlay-click="false"
          @confirm="handleBatchSetConfirm"
          @cancel="handleBatchSetCancel"
        >
          <div class="batch-set-info">已选择 {{ selectedRowKeys.length }} 个需求</div>
          <div class="batch-set-form">
            <div class="form-item">
              <div class="form-label-with-tip">
                <span class="form-label">是否需整改</span>
                <t-tooltip content="设置为否后，说明对应需求不需要整改" placement="top" theme="light">
                  <t-icon name="info-circle" size="16" style="color: #999; cursor: pointer; margin-left: 4px;" />
                </t-tooltip>
              </div>
              <t-select
                v-model="batchSetForm.man_problem_flag"
                placeholder="请选择"
                clearable
                :options="[
                  { label: '是', value: '是' },
                  { label: '否', value: '否' }
                ]"
                style="flex: 1;"
              />
            </div>
            <div class="form-item">
              <div class="form-label-with-tip">
                <span class="form-label">是否已整改</span>
                <t-tooltip content="设置为是后，说明对应需求已经整改完成" placement="top" theme="light">
                  <t-icon name="info-circle" size="16" style="color: #999; cursor: pointer; margin-left: 4px;" />
                </t-tooltip>
              </div>
              <t-select
                v-model="batchSetForm.man_handle_flag"
                placeholder="请选择"
                clearable
                :options="[
                  { label: '是', value: '是' },
                  { label: '否', value: '否' }
                ]"
                style="flex: 1;"
              />
            </div>
            <div class="form-item">
              <div class="form-label-with-tip">
                <span class="form-label">整改责任人</span>
                <t-tooltip content="对应需求的整改负责人" placement="top" theme="light">
                  <t-icon name="info-circle" size="16" style="color: #999; cursor: pointer; margin-left: 4px;" />
                </t-tooltip>
              </div>
              <t-select
                v-model="batchSetForm.man_handle_person"
                placeholder="请选择整改责任人"
                :loading="searchLoading"
                loading-text="检索中..."
                filterable
                clearable
                @input-change="getNameOptions"
                @blur="clearList"
                style="flex: 1;"
              >
                <t-option
                  v-for="item in nameOption"
                  :key="item.id"
                  :value="item.value"
                  :label="item.label"
                  :title="item.description"
                />
              </t-select>
            </div>
            <div class="form-item">
              <div class="form-label-with-tip">
                <span class="form-label">整改截止时间</span>
                <t-tooltip content="需要在整改截止日期前完成对应需求的整改" placement="top" theme="light">
                  <t-icon name="info-circle" size="16" style="color: #999; cursor: pointer; margin-left: 4px;" />
                </t-tooltip>
              </div>
              <t-date-picker
                v-model="batchSetForm.man_handle_date"
                format="YYYY-MM-DD"
                value-type="YYYY-MM-DD"
                placeholder="选择日期"
                clearable
                style="flex: 1;"
              />
            </div>
            <div class="form-tip">
              <t-icon name="info-circle" size="14" style="margin-right: 4px;" />
              提示：以上四项至少有一项不为空，如果对应项为空，则不会进行设置。只会将非空项更新到选中的需求上
            </div>
          </div>
        </t-dialog>

        <t-drawer
          v-model:visible="drawerVisible"
          header="影响需求详情"
          placement="top"
          size="90%"
          :close-on-overlay-click="true"
          :footer="false"
        >
          <div class="detail-drawer-content">
            <div v-if="currentRowInfo" class="detail-header-simple">
              <div class="info-row">
                <div class="info-item">
                  <span class="label-text">需求标识：</span>
                  <a 
                    v-if="currentRowInfo.system_id"
                    :href="`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${currentRowInfo.system_id}?teamId=bdv_1047088&tenantId=10001`" 
                    target="_blank" 
                    class="detail-link"
                  >
                    {{ currentRowInfo.system_id }}
                  </a>
                  <span v-else class="text-gray">-</span>
                </div>
              </div>
              <div class="info-row title-row" v-if="currentRowInfo.system_title">
                 <span class="label-text">需求标题：</span>
                 <div class="title-content">{{ currentRowInfo.system_title }}</div>
              </div>
              <div class="info-item" v-if="currentRowInfo.problem_type">
                <span class="label-text">问题类型：</span>
                <t-tag theme="warning" variant="light" size="small">
                  {{ currentRowInfo.problem_type }}
                </t-tag>
              </div>
              <div class="info-row desc-row" v-if="currentRowInfo.problem_description">
                <span class="label-text">问题描述：</span>
                <div class="title-content">{{ currentRowInfo.problem_description }}</div>
              </div>
            </div>
            
            <t-table
              :data="currentDetailList"
              :columns="detailColumns"
              row-key="detail_id"
              bordered
              stripe
              hover
              :max-height="450"
              :loading="drawerLoading"
              resizable
            >
              <template #match_words="{ row }">
                <div v-if="row.match_words && Array.isArray(row.match_words) && row.match_words.length">
                  <t-tag 
                    v-for="(tag, index) in row.match_words" 
                    :key="index" 
                    size="small" 
                    variant="light" 
                    style="margin: 2px"
                  >
                    {{ tag }}
                  </t-tag>
                </div>
                <span v-else style="color: #999">-</span>
              </template>
            </t-table>
            <div class="drawer-footer" v-if="currentDetailList.length > 0">
              <t-tag variant="light" theme="primary">共 {{ currentDetailList.length }} 条影响需求</t-tag>
            </div>
          </div>
        </t-drawer>
      </t-tab-panel>
    </t-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, h, nextTick, watch } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import {
  queryReqManageCheckDict,
  queryReqManageCheckTable,
  queryReqManageCheckSummaryTable
} from '@/api/electric.js'
import { updateReqManageCheckPrInfoTableManFieldsByIdList } from '@/api/electric.js'
import * as XLSX from 'xlsx-js-style'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

// ==================== 工具函数 ====================
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  if (typeof dateStr === 'string') {
    return dateStr.length >= 10 ? dateStr.substring(0, 10) : dateStr
  }
  return String(dateStr)
}

const convertTeamToCascader = (teamList) => {
  const treeMap = { '支撑': [], 'L0': [], 'L1': [], 'L2': [], '智控': [], '其它': [] }
  teamList.forEach(item => {
    const label = item.label || item
    const value = item.value || item
    let parentLabel = '其它'
    if (label.startsWith('支撑-')) parentLabel = '支撑'
    else if (label.startsWith('L0-')) parentLabel = 'L0'
    else if (label.startsWith('L1-')) parentLabel = 'L1'
    else if (label.startsWith('L2-')) parentLabel = 'L2'
    else if (label.startsWith('智控-')) parentLabel = '智控'
    treeMap[parentLabel].push({ label, value, checkable: true, leaf: true })
  })
  const result = []
  Object.entries(treeMap).forEach(([parentLabel, children]) => {
    if (children.length > 0) {
      const parentValue = parentLabel === '支撑' ? 'support' : parentLabel === 'L0' ? 'l0' : parentLabel === 'L1' ? 'l1' : parentLabel === 'L2' ? 'l2' : parentLabel === '智控' ? 'smart' : 'other'
      result.push({ label: parentLabel, value: parentValue, children })
    }
  })
  return result
}

// ==================== 状态变量 ====================
const problemTypeOptions = ref([])
const teamOptions = ref([])
const selectedProblemType = ref([])
const selectedTeam = ref([])
const selectedRequirementpreplanning = ref(['M721 V5.50R1'])
const requirementpreplanningOptions = ref([])
const requirementpreplanningTableOptions = ref([])
const selectedCalHandleFlag = ref('否')
const calHandleFlagOptions = ref([])
const selectedCalProblemFlag = ref('是')
const calProblemFlagOptions = ref([])
const selectedCalHandlePerson = ref('')
const calHandlePersonOptions = ref([])
const checkDateRange = ref([]) // 问题发现日期范围
const tableData = ref([])
const tableLoading = ref(false)
const tableHeight = ref('100px')
const tableShow = ref(true) // 新增：用于强制表格重新渲染
const pagination = reactive({ 
  current: 1, 
  pageSize: 100, 
  total: 0, 
  showJumper: true, 
  showPageSize: true, 
  pageSizeOptions: [10, 20, 50, 100],
  showZeroPage: true,
  whenPageEmpty: 'show'
})
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const currentDetailList = ref([])
const currentRowInfo = ref(null)
const currentTab = ref('trend')
const selectedRowKeys = ref([])
const batchSetDialogVisible = ref(false)
const batchSetForm = reactive({
  man_problem_flag: '',
  man_handle_flag: '',
  man_handle_person: '',
  man_handle_date: ''
})
// 整改责任人选项相关
const nameOption = ref([])
const searchLoading = ref(false)

// 图表相关
const selectedTrendPreplanning = ref([])
const trendDateRange = ref([])
const trendChart1Ref = ref(null)
let trendChart1 = null
const selectedPiePreplanning = ref('')
const selectedPieField = ref('team')
const pieFieldOptions = ref([])
const pieChartRef = ref(null)
let pieChart = null

// ==================== 列定义：最终修复选择列 ====================
const detailColumns = [
  { colKey: 'row_index', title: '序号', width: 70, align: 'center', fixed: 'left', cell: (h, { rowIndex }) => h('span', { style: 'font-weight: 500; color: #333' }, rowIndex + 1) },
  { 
    colKey: 'pr_id', 
    title: () => h('div', { style: { textAlign: 'center' } }, '需求标识'),
    width: 160, minWidth: 120, ellipsis: true, fixed: 'left', resizable: true, align: 'left',
    cell: (h, { row }) => {
      const prId = row.pr_id
      if (!prId) return h('span', { style: 'color: #999' }, '—')
      const jumpUrl = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${prId}?teamId=bdv_1047088&tenantId=10001`
      return h('a', { href: jumpUrl, target: '_blank', style: 'color: #0052d9; text-decoration: none; font-weight: 500; font-size: 13px;', onMouseenter: (e) => { e.target.style.textDecoration = 'underline' }, onMouseleave: (e) => { e.target.style.textDecoration = 'none' } }, prId)
    }
  },
  { colKey: 'system_title', title: () => h('div', { style: { textAlign: 'center' } }, '需求标题'), ellipsis: true, tooltip: true, resizable: true, align: 'left' },
  { colKey: 'team', title: () => h('div', { style: { textAlign: 'center' } }, '团队'), width: 160, minWidth: 100, ellipsis: true, resizable: true, align: 'left' },
  { colKey: 'planstartdateofdevelopment', title: () => h('div', { style: { textAlign: 'center' } }, '计划开始开发时间'), width: 160, minWidth: 140, ellipsis: true, resizable: true, align: 'left', cell: (h, { row }) => h('span', { title: row.planstartdateofdevelopment }, formatDate(row.planstartdateofdevelopment)) },
  { colKey: 'planfinishdateofdevelopment', title: () => h('div', { style: { textAlign: 'center' } }, '计划结束开发时间'), width: 160, minWidth: 140, ellipsis: true, resizable: true, align: 'left', cell: (h, { row }) => h('span', { title: row.planfinishdateofdevelopment }, formatDate(row.planfinishdateofdevelopment)) },
  { colKey: 'assessresult_first', title: () => h('div', { style: { textAlign: 'center' } }, '初评结论'), width: 120, minWidth: 100, ellipsis: true, resizable: true, align: 'left' },
  { colKey: 'match_words', title: () => h('div', { style: { textAlign: 'center' } }, '共同关键词'), width: 160, minWidth: 180, ellipsis: true, slot: 'match_words', resizable: true, align: 'left' }
]
const tableColumns = [
  // ✅ 最终修复：必须显式指定 colKey="row-select"，这是 TDesign 选择列的强制要求
  { 
    colKey: 'row-select',
    type: 'multiple', 
    width: 60, 
    align: 'center', 
    fixed: 'left'
  },
  { 
    colKey: 'row_index', 
    title: '序号', 
    exportTitle: '序号',
    width: 70, 
    align: 'center', 
    fixed: 'left', 
    cell: (h, { rowIndex }) => h('span', { style: 'font-weight: 500; color: #333' }, rowIndex + 1) 
  },
  { 
    colKey: 'problem_type', 
    title: () => h('div', { style: { textAlign: 'center' } }, '问题类型'), 
    exportTitle: '问题类型',
    width: 160, 
    ellipsis: true, 
    align: 'left' 
  },
  { 
    colKey: 'problem_description', 
    title: () => h('div', { style: { textAlign: 'center' } }, '问题描述'), 
    exportTitle: '问题描述',
    width: 200, 
    ellipsis: true, 
    tooltip: true, 
    align: 'left' 
  },
  { 
    colKey: 'system_id', 
    title: () => h('div', { style: { textAlign: 'center' } }, '需求标识'), 
    exportTitle: '需求标识',
    width: 140, 
    ellipsis: true, 
    fixed: 'left', 
    align: 'left',
    cell: (h, { row }) => {
      const systemId = row.system_id
      if (!systemId) return h('span', { style: 'color: #999' }, '—')
      const jumpUrl = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${systemId}?teamId=bdv_1047088&tenantId=10001`
      return h('a', { href: jumpUrl, target: '_blank', style: 'color: #0052d9; text-decoration: none; font-weight: 500; font-size: 13px;', onMouseenter: (e) => { e.target.style.textDecoration = 'underline' }, onMouseleave: (e) => { e.target.style.textDecoration = 'none' } }, systemId)
    }
  },
  { colKey: 'system_title', title: () => h('div', { style: { textAlign: 'center' } }, '需求标题'), exportTitle: '需求标题', width: 600, ellipsis: true, tooltip: true, align: 'left' },
  { 
    colKey: 'cal_problem_flag', 
    title: () => h('div', { style: { textAlign: 'center' } }, '是否需整改'), 
    exportTitle: '是否需整改',
    width: 105, 
    ellipsis: true, 
    align: 'center' 
  },
  { 
    colKey: 'cal_handle_flag', 
    title: () => h('div', { style: { textAlign: 'center' } }, '是否已整改'), 
    exportTitle: '是否已整改',
    width: 105, 
    ellipsis: true, 
    align: 'center' 
  },
  { 
    colKey: 'cal_handle_person', 
    title: () => h('div', { style: { textAlign: 'center' } }, '整改责任人'), 
    exportTitle: '整改责任人',
    width: 105, 
    ellipsis: true, 
    align: 'left' 
  },
  { colKey: 'team', title: () => h('div', { style: { textAlign: 'center' } }, '团队'), exportTitle: '团队', width: 150, ellipsis: true, align: 'left' },
  { colKey: 'requirementanalysisowner', title: () => h('div', { style: { textAlign: 'center' } }, '分析负责人'), exportTitle: '分析负责人', width: 130, ellipsis: true, align: 'left' },
  { colKey: 'assessresult_first', title: () => h('div', { style: { textAlign: 'center' } }, '初评结论'), exportTitle: '初评结论', width: 100, ellipsis: true, align: 'left' },
  { colKey: 'system_state', title: () => h('div', { style: { textAlign: 'center' } }, '状态'), exportTitle: '状态', width: 90, ellipsis: true, align: 'left' },
  { colKey: 'requirementpreplanning', title: () => h('div', { style: { textAlign: 'center' } }, '需求预规划'), exportTitle: '需求预规划', width: 150, ellipsis: true, align: 'left' },
  { colKey: 'belongreleaseversion', title: () => h('div', { style: { textAlign: 'center' } }, '发布版本'), exportTitle: '发布版本', width: 140, ellipsis: true, align: 'left' },
  { colKey: 'planstartdateofdevelopment', title: () => h('div', { style: { textAlign: 'center' } }, '计划开始开发时间'), exportTitle: '计划开始开发时间', width: 150, ellipsis: true, align: 'left', cell: (h, { row }) => h('span', { title: row.planstartdateofdevelopment }, formatDate(row.planstartdateofdevelopment)) },
  { colKey: 'planfinishdateofdevelopment', title: () => h('div', { style: { textAlign: 'center' } }, '计划结束开发时间'), exportTitle: '计划结束开发时间', width: 150, ellipsis: true, align: 'left', cell: (h, { row }) => h('span', { title: row.planfinishdateofdevelopment }, formatDate(row.planfinishdateofdevelopment)) },
  { colKey: 'system_createddate', title: () => h('div', { style: { textAlign: 'center' } }, '需求创建时间'), exportTitle: '需求创建时间', width: 150, ellipsis: true, align: 'left', cell: (h, { row }) => h('span', { title: row.system_createddate }, formatDate(row.system_createddate)) },
  { 
    colKey: 'check_date', 
    title: () => h('div', { style: { textAlign: 'center' } }, '问题发现日期'), 
    exportTitle: '问题发现日期',
    width: 120, 
    ellipsis: true, 
    align: 'center',
    cell: (h, { row }) => h('span', { title: row.check_date }, formatDate(row.check_date))
  },
  { 
    colKey: 'cal_handle_date', 
    title: () => h('div', { style: { textAlign: 'center' } }, '整改截止日期'), 
    exportTitle: '整改截止日期',
    width: 120, 
    ellipsis: true, 
    align: 'center',
    cell: (h, { row }) => h('span', { title: row.cal_handle_date }, formatDate(row.cal_handle_date))
  },
  { 
    colKey: 'handle_delay_flag', 
    title: () => h('div', { style: { textAlign: 'center' } }, '是否已过整改日期'), 
    exportTitle: '是否已过整改日期',
    width: 150, 
    ellipsis: true, 
    align: 'center' 
  },
  { 
    colKey: 'man_update_person', 
    title: () => h('div', { style: { textAlign: 'center' } }, '一键设置人'), 
    exportTitle: '一键设置人',
    width: 105, 
    ellipsis: true, 
    align: 'left' 
  },
  { 
    colKey: 'man_update_date', 
    title: () => h('div', { style: { textAlign: 'center' } }, '一键设置时间'), 
    exportTitle: '一键设置时间',
    width: 150, 
    ellipsis: true, 
    align: 'center',
    cell: (h, { row }) => h('span', { title: row.man_update_date }, formatDate(row.man_update_date))
  },
  { 
    colKey: 'detail_list', 
    title: () => h('div', { style: { textAlign: 'center' } }, '影响需求详情'), 
    exportTitle: '影响需求详情',
    width: 130, 
    align: 'center', 
    fixed: 'right',
    cell: (h, { row }) => {
      const list = row.detail_list
      const count = Array.isArray(list) ? list.length : 0
      if (count === 0) return h('span', { style: 'color: #999; font-size: 13px' }, '—')
      return h('span', {
        style: 'color: #0052d9; font-weight: 500; cursor: pointer; padding: 4px 12px; border-radius: 12px; background: #ebf1ff; font-size: 13px; transition: all 0.2s; display: inline-block;',
        onClick: (e) => { e.stopPropagation(); handleShowDetail(row) },
        onMouseenter: (e) => { e.currentTarget.style.background = '#d4e1ff' },
        onMouseleave: (e) => { e.currentTarget.style.background = '#ebf1ff' }
      }, `${count}条`)
    }
  }
]

// ==================== 业务方法 ====================
const updatePieFieldOptions = () => {
  const baseOptions = [
    { value: 'team', label: '团队' },
    { value: 'problem_type', label: '问题类型' },
    { value: 'requirementanalysisowner', label: '分析责任人' }
  ]
  if (selectedPiePreplanning.value === '所有') {
    pieFieldOptions.value = [
     ...baseOptions,
      { value: 'requirementpreplanning', label: '需求预规划' }
    ]
  } else {
    pieFieldOptions.value = baseOptions
    if (selectedPieField.value === 'requirementpreplanning') {
      selectedPieField.value = 'team'
    }
  }
}

const fetchDictData = async () => {
  try {
    const param = { field_list: ['problem_type', 'team', 'requirementpreplanning', 'cal_handle_flag', 'cal_problem_flag', 'cal_handle_person'] }
    const result = await queryReqManageCheckDict(param);
    if (result.code === 200 && result.data && result.data.value_dict) {
      const { problem_type, team, requirementpreplanning, cal_handle_flag, cal_problem_flag, cal_handle_person } = result.data.value_dict
      problemTypeOptions.value = problem_type.map(item => ({ label: item, value: item }))
      const teamFlatList = team.map(item => ({ label: item, value: item }))
      teamOptions.value = convertTeamToCascader(teamFlatList)
      
      requirementpreplanningOptions.value = [
        { label: '所有', value: '所有' },
       ...requirementpreplanning.map(item => ({ label: item, value: item }))
      ]
      requirementpreplanningTableOptions.value = requirementpreplanning.map(item => ({ label: item, value: item }))
      
      calHandleFlagOptions.value = cal_handle_flag.map(item => ({ label: item, value: item }))
      calProblemFlagOptions.value = cal_problem_flag.map(item => ({ label: item, value: item }))
      calHandlePersonOptions.value = cal_handle_person.map(item => ({ label: item, value: item }))
      
      updatePieFieldOptions()
      
      if (requirementpreplanning.length > 0) {
        const defaultVal = "M721 V5.50R1"
        selectedRequirementpreplanning.value = [defaultVal]
        selectedTrendPreplanning.value = [defaultVal]
        selectedPiePreplanning.value = defaultVal
        setTrendDateRangeToLast7Days()
        await nextTick()
        fetchTableData()
        setTimeout(async () => {
          await changeTrendParams()
          await changePieParams()
        }, 200)
      }
    } else {
      MessagePlugin.error('获取筛选数据失败')
    }
  } catch (error) {
    console.error('获取字典数据失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  }
}

const fetchTableData = async () => {
  tableLoading.value = true
  // 强制表格销毁重建，清除之前的渲染缓存
  tableShow.value = false
  
  try {
    const filterDict = {}
    if (selectedRequirementpreplanning.value?.length > 0) filterDict.requirementpreplanning = selectedRequirementpreplanning.value
    if (selectedProblemType.value?.length > 0) filterDict.problem_type = selectedProblemType.value
    if (selectedTeam.value?.length > 0) filterDict.team = selectedTeam.value
    if (selectedCalHandleFlag.value) filterDict.cal_handle_flag = [selectedCalHandleFlag.value]
    if (selectedCalProblemFlag.value) filterDict.cal_problem_flag = [selectedCalProblemFlag.value]
    if (selectedCalHandlePerson.value) filterDict.cal_handle_person = [selectedCalHandlePerson.value]

    const param = { filter_dict: filterDict }
    
    // 添加日期范围参数
    if (checkDateRange.value?.length === 2) {
      param.date_range_dict = {
        check_date: {
          start: checkDateRange.value[0],
          end: checkDateRange.value[1]
        }
      }
    }
    
    const result = await queryReqManageCheckTable(param);
    if (result.code === 200 && result.data) {
      tableData.value = (result.data.pr_info_list || []).map((item, index) => ({
       ...item,
        // 确保 row_key 绝对唯一，优先使用后端返回的 id
        row_key: item.id || item.system_id || `row_${index}_${Math.random().toString(36).slice(2, 10)}`
      }))
      pagination.total = tableData.value.length
      
      // 调试信息：确认数据和选中状态
      console.log('✅ 表格数据加载成功，共', tableData.value.length, '条')
      console.log('✅ 选择列配置:', tableColumns[0])
    } else {
      MessagePlugin.error('获取表格数据失败')
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取表格数据失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
    tableData.value = []
    pagination.total = 0
  } finally {
    // 数据加载完成后，重新渲染表格
    await nextTick()
    tableShow.value = true
    tableLoading.value = false
  }
}

const handleFilterChange = () => {
  pagination.current = 1
  fetchTableData()
}

const handleShowDetail = (row) => {
  try {
    const list = row.detail_list
    if (!list || !Array.isArray(list) || list.length === 0) {
      MessagePlugin.warning('暂无详情数据')
      return
    }
    currentRowInfo.value = {
      system_id: row.system_id,
      system_title: row.system_title,
      problem_type: row.problem_type,
      problem_description: row.problem_description
    }
    currentDetailList.value = list.map((item, index) => ({
     ...item,
      detail_id: `${row.row_key}_detail_${index}_${item.pr_id || index}`
    }))
    drawerVisible.value = true
    MessagePlugin.success(`已加载 ${list.length} 条影响需求`)
  } catch (error) {
    console.error('打开详情失败:', error)
    MessagePlugin.error('加载详情失败，请重试')
  }
}

const handleExport = () => {
  try {
    if (tableData.value.length === 0) {
      MessagePlugin.warning('暂无数据可导出')
      return
    }

    const exportColConfig = tableColumns.filter(col => !['row-select', 'row_index', 'detail_list'].includes(col.colKey))
    const headerOrder = ['序号', ...exportColConfig.map(c => c.exportTitle)]
    let linkColIndex = -1
    const linkColName = '需求标识'

    const exportData = tableData.value.map((row, index) => {
      const rowItem = {}
      rowItem['序号'] = index + 1

      exportColConfig.forEach(col => {
        let cellValue = row[col.colKey]
        
        if (['planstartdateofdevelopment', 'planfinishdateofdevelopment', 'system_createddate'].includes(col.colKey)) {
          cellValue = formatDate(cellValue)
        }

        if (col.colKey === 'system_id' && cellValue) {
          linkColIndex = headerOrder.findIndex(name => name === col.exportTitle)
          const url = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNSW/apps/wim/allWorkItems/${cellValue}?teamId=bdv_1047088&tenantId=10001`
          rowItem[col.exportTitle] = {
            t: 's',
            v: String(cellValue),
            l: { Target: url },
            s: {
              font: {
                color: { rgb: "FF0052d9" },
                underline: true,
                sz: 11
              }
            }
          }
        } else {
          rowItem[col.exportTitle] = cellValue !== null && cellValue !== undefined ? String(cellValue) : ''
        }
      })
      return rowItem
    })

    const worksheet = XLSX.utils.json_to_sheet(exportData, { header: headerOrder })

    const headerRange = XLSX.utils.decode_range(worksheet['!ref'])
    for (let col = headerRange.s.c; col <= headerRange.e.c; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col })
      if (!worksheet[cellAddress]) continue
      worksheet[cellAddress].s = {
        font: { bold: true, sz: 12 },
        alignment: { horizontal: 'center', vertical: 'center' }
      }
    }
worksheet['!cols'] = [
  { wch: 6 },   // 序号
  { wch: 12 },  // 问题类型
  { wch: 20 },  // 问题描述
  { wch: 15 },  // 需求标识
  { wch: 30 },  // 需求标题
  { wch: 15 },  // 团队
  { wch: 12 },  // 是否需整改
  { wch: 12 },  // 是否已整改
  { wch: 12 },  // 整改责任人
  { wch: 15 },  // 分析负责人
  { wch: 10 },  // 初评结论
  { wch: 8 },   // 状态
  { wch: 15 },  // 需求预规划
  { wch: 15 },  // 发布版本
  { wch: 15 },  // 计划开始开发时间
  { wch: 15 },  // 计划结束开发时间
  { wch: 15 },  // 需求创建时间
  { wch: 15 },  // 问题发现日期
  { wch: 15 },  // 整改截止日期
  { wch: 15 },  // 是否已过整改日期
  { wch: 12 },  // 一键设置人
  { wch: 15 }   // 一键设置时间
]

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '需求管理检查数据')
    
    const date = new Date()
    const formattedDate = `${date.getFullYear().toString().slice(2)}${(date.getMonth() + 1).toString().padStart(2, '0')}${date.getDate().toString().padStart(2, '0')}${date.getHours().toString().padStart(2, '0')}${date.getMinutes().toString().padStart(2, '0')}`
    
    XLSX.writeFile(workbook, `需求管理检查数据_${formattedDate}.xlsx`)
    MessagePlugin.success('导出成功，请查看下载文件')
  } catch (error) {
    console.error('数据导出失败:', error)
    MessagePlugin.error('导出失败，请重试')
  }
}

const onPageChange = (pageInfo) => {
  pagination.current = pageInfo.current
  pagination.pageSize = pageInfo.pageSize
}

// ==================== 批量设置相关方法 ====================
const handleBatchSet = () => {
  if (selectedRowKeys.value.length === 0) {
    MessagePlugin.warning('请先选择要设置的行')
    return
  }
  batchSetForm.man_problem_flag = ''
  batchSetForm.man_handle_flag = ''
  batchSetForm.man_handle_person = ''
  batchSetForm.man_handle_date = ''
  batchSetDialogVisible.value = true
}

const handleBatchSetCancel = () => {
  batchSetDialogVisible.value = false
}

// 获取整改责任人选项
const getNameOptions = async (searchValue, context) => {
    try {
        searchLoading.value = true;
        const response = await fetch(`https://wdmpi.zx.zte.com.cn/baseapi/userinfo/getuser?user=${searchValue}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();
        console.log(responseData)
        nameOption.value = extractEmployeeData(responseData.body.data);
        searchLoading.value = false;
    } catch (error) {
        console.error('请求出错:', error);
        MessagePlugin.error(response.message);
        searchLoading.value = false;
    }

};

// 提取员工数据并转换为选项格式
const extractEmployeeData = (data) => {
  return Object.keys(data).map((key, index) => {
    // 从键名中提取工号（假设工号是末尾的数字）
    const match = key.match(/(\d+)$/);
    const employeeId = match ? match[1] : '';
    return {
      id: index + 1,
      label: key,
      value: employeeId,
      description: data[key],
    };
  });
};

// 清空列表
const clearList = () => {
  nameOption.value = []
}

const handleBatchSetConfirm = async () => {
  const { man_problem_flag, man_handle_flag, man_handle_person, man_handle_date } = batchSetForm
  if (!man_problem_flag && !man_handle_flag && !man_handle_person && !man_handle_date) {
    MessagePlugin.warning('请至少填写一项内容')
    return
  }

  try {
    const updateData = {
      id_list: selectedRowKeys.value
    }
    
    if (man_problem_flag) updateData.man_problem_flag = man_problem_flag
    if (man_handle_flag) updateData.man_handle_flag = man_handle_flag
    if (man_handle_person) updateData.man_handle_person = man_handle_person
    if (man_handle_date) updateData.man_handle_date = man_handle_date

    const result = await updateReqManageCheckPrInfoTableManFieldsByIdList(updateData)
    
    if (result.code === 200) {
      MessagePlugin.success('批量设置成功')
      batchSetDialogVisible.value = false
      fetchTableData()
    } else {
      MessagePlugin.error('批量设置失败')
    }
  } catch (error) {
    console.error('批量设置失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  }
}

// ==================== 图表核心逻辑 ====================
const setTrendDateRangeToLast7Days = () => {
  trendDateRange.value = [dayjs().subtract(7, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
}

const disabledTrendDate = (date) => {
  const d = dayjs(date).startOf('day')
  return d.isBefore(dayjs('2026-01-01')) || d.isAfter(dayjs())
}

const handleTabChange = async (tabValue) => {
  if (tabValue === 'trend') {
    await nextTick()
    changeTrendParams()
    changePieParams()
  }
}

const changeTrendParams = async () => {
  if (!trendDateRange.value?.length || !selectedTrendPreplanning.value?.length) return
  await nextTick()
  
  try {
    const data = {
      start_date: trendDateRange.value[0],
      end_date: trendDateRange.value[1],
      requirementpreplanning_list: selectedTrendPreplanning.value
    }
    const res = await queryReqManageCheckSummaryTable(data)
    if (res.code === 200) {
      initTrendChart(res.data)
    }
  } catch (e) { 
    console.error('曲线图数据加载失败:', e) 
  }
}


const initTrendChart = (data) => {
  if (!trendChart1Ref.value) {
    console.warn('曲线图 DOM 未找到，重试中...')
    setTimeout(() => initTrendChart(data), 200)
    return
  }

  if (trendChart1) {
    trendChart1.dispose()
    trendChart1 = null
  }

  trendChart1 = echarts.init(trendChart1Ref.value)
  const dateList = data[0]?.date_list || []
  
  let maxVal = 0
  let minVal = Infinity
  data.forEach(item => {
    const numList = item.not_handle_num_list || []
    numList.forEach(num => {
      if (num > maxVal) maxVal = num
      if (num < minVal) minVal = num
    })
  })
  const yAxisMax = maxVal === 0 ? 10 : Math.ceil(maxVal * 1.2)
  const yAxisMin = minVal === Infinity ? 0 : Math.max(0, Math.floor(minVal * 0.8))
  
  const series = data.map(item => ({
    name: item.requirementpreplanning,
    type: 'line',
    data: item.not_handle_num_list,
    smooth: true,
    lineStyle: { width: 3 },
    symbol: 'circle',
    symbolSize: 6,
    label: { show: true, position: 'top', color: '#e67c3b' }
  }))

  trendChart1.setOption({
    tooltip: { trigger: 'axis' },
    legend: { 
      orient: 'horizontal', 
      left: 'center',
      bottom: 5,
      itemGap: 12,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 12 },
      width: '95%',
      maxRows: 2,
      type: 'scroll',
      pageIconSize: 10,
      pageTextStyle: { fontSize: 12 },
      pageButtonPosition: 'end'
    },
    grid: { 
      left: '3%', 
      right: '4%', 
      top: '10%', 
      bottom: '12%',
      containLabel: true 
    },
    xAxis: { 
      type: 'category', 
      data: dateList,
      axisTick: {
        show: true,
        inside: true,
        alignWithLabel: true,
        length: 6,
        lineStyle: { color: '#666' }
      },
      axisLabel: {
        interval: 'auto',
        hideOverlap: true,
        align: 'center',
        fontSize: 12,
        color: '#666',
        margin: 8
      },
    },
    yAxis: { 
      type: 'value', 
      name: '待整改需求数',
      nameGap: 15,
      nameTextStyle: { fontSize: 12, color: '#666' },
      min: yAxisMin,
      max: yAxisMax,
      axisLine: {
        show: true,
        lineStyle: { color: '#666' }
      },
      axisTick: {
        show: true,
        inside: true,
        length: 6,
        lineStyle: { color: '#666' }
      },
      axisLabel: {
        fontSize: 12,
        color: '#666',
        margin: 8
      }
    },
    series,
    color: [
        '#0052d9', '#e67c3b', '#2ecc71', '#e74c3c', '#9b59b6',
        '#3498db', '#1abc9c', '#f39c12', '#d35400', '#8e44ad',
        '#27ae60', '#c0392b', '#16a085', '#f1c40f', '#2980b9'
      ],
  })
}

const changePieParams = async () => {
  await nextTick()
  
  try {
    const filterDict = {
      cal_handle_flag: ['否']
    }
    if (selectedPiePreplanning.value && selectedPiePreplanning.value !== '所有') {
      filterDict.requirementpreplanning = [selectedPiePreplanning.value]
    }
    
    const res = await queryReqManageCheckTable({ filter_dict: filterDict })
    if (res.code === 200) {
      const list = res.data?.pr_info_list || []
      const map = {}
      list.forEach(item => {
        const k = item[selectedPieField.value] || '未知'
        map[k] = (map[k] || 0) + 1
      })
      initPieChart(Object.keys(map).map(k => ({ name: k, value: map[k] })))
    }
  } catch (e) { 
    console.error('饼图数据加载失败:', e) 
  }
}



const initPieChart = (data) => {
  if (!pieChartRef.value) {
    console.warn('饼图DOM未找到，重试中...')
    setTimeout(() => initPieChart(data), 200)
    return
  }

  if (pieChart) {
    pieChart.dispose()
    pieChart = null
  }

  const sortedData = [...data].sort((a, b) => b.value - a.value)

  pieChart = echarts.init(pieChartRef.value)
  
  const total = sortedData.reduce((sum, item) => sum + item.value, 0)

  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { 
      bottom: 10,
      left: 'center',
      orient: 'horizontal',
      itemGap: 15,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 12 },
      width: '90%',
      maxRows: 2,
      type: 'scroll',
      pageIconSize: 10,
      pageTextStyle: { fontSize: 12 }
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '40%',
        style: {
          text: `总数\n${total}`,
          textAlign: 'center',
          fill: '#1d2129',
          fontSize: 18,
          fontWeight: 600,
          lineHeight: 24
        }
      }
    ],
    series: [{
      name: '占比',
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '45%'], 
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      label: {
        show: true,
        formatter: '{b|{b}}\n{c|{c}个}',
        position: 'outer',
        alignTo: 'labelLine',
        edgeDistance: '15%',
        overflow: 'truncate',
        minMargin: 3,
        lineHeight: 16,
        rich: {
          b: {
            fontSize: 11,
            color: '#333',
            fontWeight: 400,
            lineHeight: 16,
            width: 80,
            overflow: 'truncate'
          },
          c: {
            fontSize: 10,
            color: '#666',
            lineHeight: 14
          }
        },
      },
      data: sortedData,
      labelLine: {
        show: true,
        length: 2,
        length2: 10,
        maxSurfaceAngle: 80,
        smooth: 0.2,
        lineStyle: { width: 1 }
      },
      color: [
        '#0052d9', '#e67c3b', '#2ecc71', '#e74c3c', '#9b59b6',
        '#3498db', '#1abc9c', '#f39c12', '#d35400', '#8e44ad',
        '#27ae60', '#c0392b', '#16a085', '#f1c40f', '#2980b9'
      ],
    }],
  })
}


const handleResize = () => {
  trendChart1?.resize()
  pieChart?.resize()
}

// ==================== 生命周期 ====================
onMounted(() => {
  const calculateHeight = () => {
    const pageHeight = document.documentElement.clientHeight
    return `${pageHeight * 0.83 - 225}px`
  }
  
  tableHeight.value = calculateHeight()
  fetchDictData()
  window.addEventListener('resize', () => {
    handleResize()
    tableHeight.value = calculateHeight()
  })
})

watch(selectedPiePreplanning, () => {
  updatePieFieldOptions()
  changePieParams()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart1?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.page-container {
  padding: 0;
  height: 83vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background: #f2f3f5;
}

:deep(.t-tabs__content) {
  height: calc(100%);
  overflow-y: auto;
  overflow-x: auto;
}

.trend-page-container {
  padding: 24px;
  height: 100%;
  box-sizing: border-box;
}
.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: 100%;
  min-height: 700px;
}
.chart-card-modern {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 680px;
  overflow: hidden;
}

.card-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.title-bar-left, .title-bar-right {
  display: flex;
  align-items: center;
  min-width: 60px;
}
.title-bar-right {
  justify-content: flex-end;
}
.card-title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  text-align: center;
  flex: 1;
}

.filter-section {
  display: flex;
  gap: 20px;
  padding: 20px;
  background: #f7f8fa;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.filter-group {
  flex: 1;
  min-width: 280px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
}
.filter-label {
  font-size: 13px;
  color: #4e5969;
  font-weight: 500;
  min-width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.chart-body {
  flex: 1;
  padding: 20px;
  flex-shrink: 0;
  min-height: 500px;
}
.chart-instance-modern {
  display: block;
}

/* ==================== 核心优化：筛选器Grid布局 ==================== */
.filters-container {
  background: #fff;
  padding: 16px 24px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4列等宽，实现第一行平均分布 */
  gap: 16px 24px; /* 行间距16px，列间距24px */
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%; /* 占满Grid单元格 */
}

/* 按钮组特殊样式：两个按钮并排，左对齐 */
.filter-item-buttons {
  gap: 12px;
  justify-content: flex-start;
}

.filter-item .batch-btn,
.filter-item .export-btn {
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 14px;
  white-space: nowrap; /* 防止按钮文字换行 */
}

.filter-item .batch-btn:hover:not(:disabled) {
  background: #e8f3ff;
}

.filter-item .export-btn:hover {
  background: #e8f3ff;
}

.filter-item .filter-label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
  min-width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.filter-item :deep(.t-select, .t-cascader) {
  border-radius: 6px;
}

.filter-item :deep(.t-input__inner) {
  border-radius: 6px;
}

.table-wrapper {
  flex: 1;
  border: 1px solid #e7e7e7;
  border-radius: 4px;
  margin: 0 24px 24px 24px;
  background: #fff;
  overflow: auto;
}

.batch-set-info {
  padding: 12px 16px;
  background: #f0f5ff;
  border-radius: 4px;
  font-size: 14px;
  color: #0052d9;
  margin-bottom: 16px;
  font-weight: 500;
}

.batch-set-form {
  padding: 8px 0;
}

.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
}

.form-label-with-tip {
  display: flex;
  align-items: center;
  min-width: 100px;
}

.form-label-with-tip .form-label {
  text-align: right;
  white-space: nowrap;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  min-width: 100px;
  text-align: right;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-tip {
  margin-top: 16px;
  padding: 8px 12px;
  background: #f7f8fa;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.detail-drawer-content { padding: 0; }
.detail-header-simple {
  background: #fff;
  border-bottom: 1px solid #e7e7e7;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.label-text {
  color: #000;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
}
.detail-link {
  color: #0052d9;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
}
.detail-link:hover {
  text-decoration: underline;
  color: #003bb3;
}
.title-row { margin-top: 8px; align-items: flex-start; }
.title-content { font-size: 15px; color: #000; flex: 1; }
.desc-row { margin-top: 8px; align-items: flex-start; }
.drawer-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  padding-right: 24px;
}
/* 仅问题发现日期输入框居中 */
.filters-container .filter-item:nth-child(5) :deep(.t-input__inner) {
  text-align: center !important;
}

.filters-container .filter-item:nth-child(5) :deep(.t-date-range-picker__separator) {
  text-align: center;
}
</style>
