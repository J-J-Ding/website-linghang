<!-- src/views/knowledge-board/KnowledgeBoard.vue -->
<template>
    <div class="knowledge-board-container">
        <!-- 看板切换标签 -->
        <t-tabs v-model="activeBoardTab" @change="handleBoardChange">
            <t-tab-panel value="comp" label="组件看板" />
            <t-tab-panel value="feature" label="特性看板" />
        </t-tabs>

        <!-- 组件看板内容 -->
        <div v-show="activeBoardTab === 'comp'" class="board-content">
            <!-- 图表区域筛选栏 -->
            <t-row :gutter="16" justify="end" style="margin-bottom: 20px;">
                <t-col>
                    <t-select
                        v-model="compEchartSelectedPageType"
                        style="width: 200px"
                        placeholder="请选择节点类型"
                        clearable
                        filterable
                    >
                        <t-option
                            v-for="item in compPageTypeOptionList"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        />
                    </t-select>
                </t-col>
                <t-col>
                    <t-select
                        v-model="compEchartSelectedDataType"
                        style="width: 200px"
                        placeholder="请选择展示数据"
                        clearable
                        filterable
                    >
                        <t-option
                            v-for="item in dataTypeOptionList"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        />
                    </t-select>
                </t-col>
                <t-col>
                    <t-date-range-picker
                        v-model="dateRange"
                        :disable-date="disabledDate"
                        format="YYYY-MM-DD"
                        value-type="YYYY-MM-DD"
                        class="date-range-picker-center"
                        style="width: 300px"
                        clearable
                    />
                </t-col>
                <t-col>
                    <t-button theme="primary" variant="outline" @click="refreshData">
                        <template #icon><t-icon name="search" /></template>
                        查询
                    </t-button>
                </t-col>
            </t-row>

            <!-- 图表区域 -->
            <t-row :gutter="20" style="margin-bottom: 20px;">
                <t-col :span="6">
                    <pub-line-chart
                        ref="compCumulativeChartRef"
                        :chart-data="compEchartDataList"
                        :title="compChartTitle"
                        yAxisName="累计值"
                        height="360px"
                    />
                </t-col>
                <t-col :span="6">
                    <pub-line-chart
                        ref="compDailyChartRef"
                        :chart-data="compDailyIncrementData"
                        :title="compDailyChartTitle"
                        yAxisName="日增量"
                        height="360px"
                    />
                </t-col>
            </t-row>

            <!-- 表格 -->
            <t-table
                ref="compTableRef"
                row-key="serial"
                :data="compTableList"
                :columns="compTableColumns"
                hover
                size="small"
                style="margin-top: 10px; width: 100%"
            >
                <template #serial="{ rowIndex }">
                    <span>{{ rowIndex + 1 }}</span>
                </template>
            </t-table>
        </div>

        <!-- 特性看板内容 -->
        <div v-show="activeBoardTab === 'feature'" class="board-content">
            <!-- 图表区域筛选栏 -->
            <t-row :gutter="16" justify="end" style="margin-bottom: 20px;">
                <t-col>
                    <t-select
                        v-model="featureEchartSelectedPageType"
                        style="width: 200px"
                        placeholder="请选择页面类型"
                        clearable
                        filterable
                    >
                        <t-option
                            v-for="item in featurePageTypeOptionList"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        />
                    </t-select>
                </t-col>
                <t-col>
                    <t-select
                        v-model="featureEchartSelectedDataType"
                        style="width: 200px"
                        placeholder="请选择展示数据"
                        clearable
                        filterable
                    >
                        <t-option
                            v-for="item in dataTypeOptionList"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        />
                    </t-select>
                </t-col>
                <t-col>
                    <t-date-range-picker
                        v-model="dateRange"
                        :disable-date="disabledDate"
                        format="YYYY-MM-DD"
                        value-type="YYYY-MM-DD"
                        class="date-range-picker-center"
                        style="width: 300px"
                        clearable
                    />
                </t-col>
                <t-col>
                    <t-button theme="primary" variant="outline" @click="refreshData">
                        <template #icon><t-icon name="search" /></template>
                        查询
                    </t-button>
                </t-col>
            </t-row>

            <!-- 图表区域 -->
            <t-row :gutter="20" style="margin-bottom: 20px;">
                <t-col :span="6">
                    <pub-line-chart
                        ref="featureCumulativeChartRef"
                        :chart-data="featureEchartDataList"
                        :title="featureChartTitle"
                        yAxisName="累计值"
                        height="360px"
                    />
                </t-col>
                <t-col :span="6">
                    <pub-line-chart
                        ref="featureDailyChartRef"
                        :chart-data="featureDailyIncrementData"
                        :title="featureDailyChartTitle"
                        yAxisName="日增量"
                        height="360px"
                    />
                </t-col>
            </t-row>

            <!-- 表格 -->
            <t-table
                ref="featureTableRef"
                row-key="serial"
                :data="featureTableList"
                :columns="featureTableColumns"
                hover
                size="small"
                style="margin-top: 10px; width: 100%"
            >
                <template #serial="{ rowIndex }">
                    <span>{{ rowIndex + 1 }}</span>
                </template>
            </t-table>
        </div>

        <!-- 明细数据抽屉（共用） -->
        <t-drawer
            v-model:visible="drawerVisible"
            :header="drawerHeader"
            placement="top"
            :footer="false"
            size="85%"
            :close-on-overlay-click="true"
            @close="handleCloseDrawer"
            @opened="onDrawerOpened"
        >
            <div v-show="drawerData.length === 0" class="empty-state">
                <t-icon name="folder-off" size="70px" style="color: var(--td-brand-color-light); margin-bottom: 16px" />
                <p class="empty-title">暂无数据</p>
                <p class="empty-description">{{ drawerEmptyDescription }}</p>
            </div>

            <div v-show="drawerData.length !== 0" class="checkbox-group">
                <pub-table
                    ref="pubTableRef"
                    :key="drawerTableKey"
                    :columns="currentDrawerColumns"
                    :data="drawerData"
                    :border="true"
                    :max-height="600"
                    :stripe="true"
                    :enableFilter="true"
                    :enableExport="true"
                    :link-columns="linkColumnsConfig"
                    style="width: 100%; max-width: calc(100% - 20px); overflow-x: auto;"
                >
                    <template #cell-page_title="{ row }">
                        <t-button theme="primary" variant="text" @click="openPage(row.page_url)">
                            {{ row.page_title }}
                        </t-button>
                    </template>
                    <template #cell-is_sub_feature="{ row }" v-if="activeBoardTab === 'feature'">
                        <t-tag :theme="row.is_sub_feature === 1 ? 'warning' : 'default'" size="small">
                            {{ row.is_sub_feature === 1 ? '是' : '否' }}
                        </t-tag>
                    </template>
                    <template #cell-type_flag="{ row }" v-if="activeBoardTab === 'feature'">
                        <t-tag size="small">{{ row.type_flag }}</t-tag>
                    </template>
                    <template v-if="isChangeDetail" #cell-change_type="{ row }">
                        <t-tag :theme="row.change_type === 'add' ? 'success' : 'danger'" size="small">
                            {{ row.change_type === 'add' ? '新增' : '删除' }}
                        </t-tag>
                    </template>
                </pub-table>
            </div>
        </t-drawer>
    </div>
</template>

<script setup lang="jsx">
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import PubTable from './components/PubTable.vue'
import PubLineChart from './components/PubLineChart.vue'
// 组件看板接口
import {
    knowQueryCompTreeBoardGraphSumDataDict,
    knowQueryCompTreeBoardTableSumDataDict,
    knowQueryCompTreeBoardTableCumulativeDetailList,
    knowQueryCompTreeBoardTableChangeDetailList
} from '@/api/comp.js'
// 特性看板接口
import {
    knowQueryFeatureTreeBoardGraphSumDataDict,
    knowQueryFeatureTreeBoardTableSumDataDict,
    knowQueryFeatureTreeBoardTableCumulativeDetailList,
    knowQueryFeatureTreeBoardTableChangeDetailList
} from '@/api/feature.js'

// ==================== 公共状态 ====================

// const compCumulativeChartRef = ref(null)
// const compDailyChartRef = ref(null)
// const featureCumulativeChartRef = ref(null)
// const featureDailyChartRef = ref(null)

const activeBoardTab = ref('comp')
const dateRange = ref([])
const drawerVisible = ref(false)
const drawerData = ref([])
const currentFieldName = ref('')
const currentStatus = ref('')
const currentStatusLabel = ref('')
const isChangeDetail = ref(false)
const dateRangeForChange = ref([])
const pubTableRef = ref(null)
const linkColumnsConfig = [{ prop: 'page_title', urlProp: 'page_url' }]

// 公共常量
const minSelectableDate = '2026-05-27'
const dataTypeOptionList = [
    { label: '节点总数', value: 'sum_num' },
    { label: '初始', value: 'initial_num' },
    { label: '已初审', value: 'reviewed_num' },
    { label: '修订中', value: 'revision_num' },
    { label: '空页面', value: 'blank_num' },
    { label: '已定稿', value: 'finish_num' },
    { label: '定稿率', value: 'finish_rate' },
    { label: '编辑总人数', value: 'sum_editor_num' },
    { label: '编辑总人次', value: 'sum_edit_num' },
    { label: '浏览总人数', value: 'sum_view_visitor_num' },
    { label: '浏览总人次', value: 'sum_view_visit_num' },
]

// ==================== 组件看板状态 ====================
const compEchartSelectedPageType = ref('comp')
const compEchartSelectedDataType = ref('finish_num')
const compEchartDataList = ref([])
const compDailyIncrementData = ref([])
const compTableList = ref([])
const compTableSelectedPageType = ref('comp')
const compCumulativeChartRef = ref(null)
const compDailyChartRef = ref(null)
const compTableRef = ref(null)

const compPageTypeOptionList = [
    { label: '组件设计', value: 'comp' },
    { label: '模块设计', value: 'module' },
]

// 组件看板表格列配置
const compTableColumns = computed(() => [
    { colKey: 'serial', title: '序号', width: 70, align: 'center', fixed: 'left' },
    { colKey: 'field_name', title: '领域名称', width: 100, align: 'center', fixed: 'left' },
    {
        colKey: 'sum_num_end',
        title: '节点总数',
        width: 100,
        align: 'center',
        cell: (_, { row }) => (
            <t-link theme="primary" hover="color" onClick={() => showTableSumDetail(row)}>
                {row.sum_num_end}
            </t-link>
        )
    },
    {
        title: '已定稿',
        align: 'center',
        children: [
            {
                colKey: 'finish_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '已定稿')}>
                        {row.finish_end}
                    </t-link>
                )
            },
            {
                colKey: 'finish_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '已定稿')}
                        style={{ color: row.finish_change > 0 ? '#f56c6c' : row.finish_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.finish_change > 0 ? '+' : ''}{row.finish_change}
                    </t-link>
                )
            },
            { colKey: 'finish_rate', title: '定稿率', width: 90, align: 'center' }
        ]
    },
    {
        title: '初始',
        align: 'center',
        children: [
            {
                colKey: 'initial_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '初始')}>
                        {row.initial_end}
                    </t-link>
                )
            },
            {
                colKey: 'initial_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '初始')}
                        style={{ color: row.initial_change > 0 ? '#f56c6c' : row.initial_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.initial_change > 0 ? '+' : ''}{row.initial_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '已初审',
        align: 'center',
        children: [
            {
                colKey: 'reviewed_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '已初审')}>
                        {row.reviewed_end}
                    </t-link>
                )
            },
            {
                colKey: 'reviewed_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '已初审')}
                        style={{ color: row.reviewed_change > 0 ? '#f56c6c' : row.reviewed_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.reviewed_change > 0 ? '+' : ''}{row.reviewed_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '修订中',
        align: 'center',
        children: [
            {
                colKey: 'revision_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '修订中')}>
                        {row.revision_end}
                    </t-link>
                )
            },
            {
                colKey: 'revision_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '修订中')}
                        style={{ color: row.revision_change > 0 ? '#f56c6c' : row.revision_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.revision_change > 0 ? '+' : ''}{row.revision_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '空页面',
        align: 'center',
        children: [
            {
                colKey: 'blank_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '空页面')}>
                        {row.blank_end}
                    </t-link>
                )
            },
            {
                colKey: 'blank_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '空页面')}
                        style={{ color: row.blank_change > 0 ? '#f56c6c' : row.blank_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.blank_change > 0 ? '+' : ''}{row.blank_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '浏览',
        align: 'center',
        children: [
            { colKey: 'sum_view_visitor_num', title: '总人数', width: 100, align: 'center' },
            { colKey: 'sum_view_visit_num', title: '总人次', width: 100, align: 'center' }
        ]
    },
    {
        title: '编辑',
        align: 'center',
        children: [
            { colKey: 'sum_editor_num', title: '总人数', width: 100, align: 'center' },
            { colKey: 'sum_edit_num', title: '总人次', width: 100, align: 'center' }
        ]
    },
])

// 组件看板抽屉列配置 - 累计明细
const compDrawerColumnDictCumulative = {
    comp: [
        { prop: 'field_name', label: '领域名称', width: '100', fixed: 'left', filterable: false },
        { prop: 'page_title', label: '节点标题', width: '250', fixed: 'left', filterable: false },
        { prop: 'comp_name', label: '组件名称', width: '200', filterable: false },
        { prop: 'module_num', label: '模块数', width: '70', filterable: false },
        { prop: 'page_status', label: '节点状态', width: '100', filterable: false },
        { prop: 'page_person', label: '页面守护人', width: '150', filterable: 'multiple' },
        { prop: 'page_tl', label: 'TL', width: '150', filterable: false },
        { prop: 'page_se', label: 'SE', width: '150', filterable: false },
        { prop: 'page_tse', label: 'TSE', width: '150', filterable: false },
        { prop: 'update_by', label: '更新人', width: '150', filterable: false },
        { prop: 'update_date', label: '更新时间', width: '200', sortable: true, filterable: false },
        { prop: 'editor_num', label: '编辑人数', width: '100', sortable: true, filterable: false },
        { prop: 'edit_num', label: '编辑人次', width: '100', sortable: true, filterable: false },
        { prop: 'view_visitor_num', label: '浏览人数', width: '100', sortable: true, filterable: false },
        { prop: 'view_visit_num', label: '浏览人次', width: '100', sortable: true, filterable: false },
    ],
    module: [
        { prop: 'field_name', label: '领域名称', width: '100', fixed: 'left', filterable: false },
        { prop: 'page_title', label: '节点标题', width: '250', fixed: 'left', filterable: false },
        { prop: 'module_name', label: '模块名称', width: '200', filterable: false },
        { prop: 'comp_name', label: '所属组件', width: '200', filterable: 'multiple' },
        { prop: 'page_status', label: '节点状态', width: '100', filterable: false },
        { prop: 'page_person', label: '页面守护人', width: '150', filterable: 'multiple' },
        { prop: 'page_tl', label: 'TL', width: '150', filterable: false },
        { prop: 'page_se', label: 'SE', width: '150', filterable: false },
        { prop: 'page_tse', label: 'TSE', width: '150', filterable: false },
        { prop: 'update_by', label: '更新人', width: '150', filterable: false },
        { prop: 'update_date', label: '更新时间', width: '200', sortable: true, filterable: false },
        { prop: 'editor_num', label: '编辑人数', width: '100', sortable: true, filterable: false },
        { prop: 'edit_num', label: '编辑人次', width: '100', sortable: true, filterable: false },
        { prop: 'view_visitor_num', label: '浏览人数', width: '100', sortable: true, filterable: false },
        { prop: 'view_visit_num', label: '浏览人次', width: '100', sortable: true, filterable: false },
    ]
}

// 组件看板抽屉列配置 - 变更详情
const compDrawerColumnDictChange = {
    comp: [
        ...compDrawerColumnDictCumulative.comp,
        { prop: 'change_type', label: '变更类型', width: '100', sortable: true, fixed: 'right', filterable: false },
        { prop: 'change_detail', label: '变更原因', width: '150', fixed: 'right', filterable: false },
    ],
    module: [
        ...compDrawerColumnDictCumulative.module,
        { prop: 'change_type', label: '变更类型', width: '100', sortable: true, fixed: 'right', filterable: false },
        { prop: 'change_detail', label: '变更原因', width: '150', fixed: 'right', filterable: false },
    ]
}

// ==================== 特性看板状态 ====================
const featureEchartSelectedPageType = ref('analysis')
const featureEchartSelectedDataType = ref('finish_num')
const featureEchartDataList = ref([])
const featureDailyIncrementData = ref([])
const featureTableList = ref([])
const featureTableSelectedPageType = ref('analysis')
const featureCumulativeChartRef = ref(null)
const featureDailyChartRef = ref(null)
const featureTableRef = ref(null)

const featurePageTypeOptionList = [
    { label: '特性分析', value: 'analysis' },
    { label: '特性方案', value: 'scheme' },
]

// 特性看板特有数据类型
const featureDataTypeOptionList = [
    ...dataTypeOptionList,
    { label: 'AI适配数', value: 'sum_ai_adapt_num' },
    { label: 'AI生成数', value: 'sum_ai_gene_num' },
]

// 特性看板表格列配置
const featureTableColumns = computed(() => [
    { colKey: 'serial', title: '序号', width: 70, align: 'center', fixed: 'left' },
    { colKey: 'field_name', title: '领域名称', width: 100, align: 'center', fixed: 'left' },
    {
        colKey: 'sum_num_end',
        title: '节点总数',
        width: 100,
        align: 'center',
        cell: (_, { row }) => (
            <t-link theme="primary" hover="color" onClick={() => showTableSumDetail(row)}>
                {row.sum_num_end}
            </t-link>
        )
    },
    {
        title: '已定稿',
        align: 'center',
        children: [
            {
                colKey: 'finish_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '已定稿')}>
                        {row.finish_end}
                    </t-link>
                )
            },
            {
                colKey: 'finish_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '已定稿')}
                        style={{ color: row.finish_change > 0 ? '#f56c6c' : row.finish_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.finish_change > 0 ? '+' : ''}{row.finish_change}
                    </t-link>
                )
            },
            { colKey: 'finish_rate', title: '定稿率', width: 90, align: 'center' }
        ]
    },
    {
        title: '初始',
        align: 'center',
        children: [
            {
                colKey: 'initial_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '初始')}>
                        {row.initial_end}
                    </t-link>
                )
            },
            {
                colKey: 'initial_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '初始')}
                        style={{ color: row.initial_change > 0 ? '#f56c6c' : row.initial_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.initial_change > 0 ? '+' : ''}{row.initial_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '已初审',
        align: 'center',
        children: [
            {
                colKey: 'reviewed_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '已初审')}>
                        {row.reviewed_end}
                    </t-link>
                )
            },
            {
                colKey: 'reviewed_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '已初审')}
                        style={{ color: row.reviewed_change > 0 ? '#f56c6c' : row.reviewed_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.reviewed_change > 0 ? '+' : ''}{row.reviewed_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '修订中',
        align: 'center',
        children: [
            {
                colKey: 'revision_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '修订中')}>
                        {row.revision_end}
                    </t-link>
                )
            },
            {
                colKey: 'revision_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '修订中')}
                        style={{ color: row.revision_change > 0 ? '#f56c6c' : row.revision_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.revision_change > 0 ? '+' : ''}{row.revision_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '空页面',
        align: 'center',
        children: [
            {
                colKey: 'blank_end',
                title: '累计',
                width: 100,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link theme="primary" hover="color" onClick={() => showTableNumDetail(row, '空页面')}>
                        {row.blank_end}
                    </t-link>
                )
            },
            {
                colKey: 'blank_change',
                title: '新增',
                width: 90,
                align: 'center',
                cell: (_, { row }) => (
                    <t-link
                        theme="primary"
                        hover="color"
                        onClick={() => showTableChangeDetail(row, '空页面')}
                        style={{ color: row.blank_change > 0 ? '#f56c6c' : row.blank_change < 0 ? '#67c23a' : '#909399' }}
                    >
                        {row.blank_change > 0 ? '+' : ''}{row.blank_change}
                    </t-link>
                )
            },
        ]
    },
    {
        title: '浏览',
        align: 'center',
        children: [
            { colKey: 'sum_view_visitor_num', title: '总人数', width: 100, align: 'center' },
            { colKey: 'sum_view_visit_num', title: '总人次', width: 100, align: 'center' }
        ]
    },
    {
        title: '编辑',
        align: 'center',
        children: [
            { colKey: 'sum_editor_num', title: '总人数', width: 100, align: 'center' },
            { colKey: 'sum_edit_num', title: '总人次', width: 100, align: 'center' }
        ]
    },
])

// 特性看板抽屉列配置 - 累计明细
const featureDrawerColumnDictCumulative = {
    analysis: [
        { prop: 'field_name', label: '领域名称', width: '100', fixed: 'left', filterable: false },
        { prop: 'page_title', label: '节点标题', width: '250', fixed: 'left', filterable: false },
        { prop: 'feature_num', label: '特性编号', width: '120', filterable: false },
        { prop: 'feature_name', label: '特性名称', width: '200', filterable: false },
        { prop: 'type_flag', label: '业务标识', width: '80', filterable: 'multiple' },
        { prop: 'is_sub_feature', label: '子特性', width: '70', filterable: 'multiple' },
        { prop: 'scheme_num', label: '关联方案数', width: '100', sortable: true, filterable: false },
        { prop: 'page_status', label: '节点状态', width: '100', filterable: false },
        { prop: 'page_person', label: '页面守护人', width: '150', filterable: 'multiple' },
        { prop: 'page_tl', label: 'TL', width: '150', filterable: false },
        { prop: 'page_se', label: 'SE', width: '150', filterable: false },
        { prop: 'page_tse', label: 'TSE', width: '150', filterable: false },
        { prop: 'update_by', label: '更新人', width: '150', filterable: false },
        { prop: 'update_date', label: '更新时间', width: '200', sortable: true, filterable: false },
        { prop: 'editor_num', label: '编辑人数', width: '100', sortable: true, filterable: false },
        { prop: 'edit_num', label: '编辑人次', width: '100', sortable: true, filterable: false },
        { prop: 'view_visitor_num', label: '浏览人数', width: '100', sortable: true, filterable: false },
        { prop: 'view_visit_num', label: '浏览人次', width: '100', sortable: true, filterable: false },
    ],
    scheme: [
        { prop: 'field_name', label: '领域名称', width: '100', fixed: 'left', filterable: false },
        { prop: 'page_title', label: '节点标题', width: '250', fixed: 'left', filterable: false },
        { prop: 'feature_num', label: '特性编号', width: '120', filterable: false },
        { prop: 'feature_name', label: '特性名称', width: '200', filterable: false },
        { prop: 'type_flag', label: '业务标识', width: '80', filterable: 'multiple' },
        { prop: 'is_sub_feature', label: '子特性', width: '70', filterable: 'multiple' },
        { prop: 'scheme_num', label: '关联方案数', width: '100', sortable: true, filterable: false },
        { prop: 'page_status', label: '节点状态', width: '100', filterable: false },
        { prop: 'page_person', label: '页面守护人', width: '150', filterable: 'multiple' },
        { prop: 'page_tl', label: 'TL', width: '150', filterable: false },
        { prop: 'page_se', label: 'SE', width: '150', filterable: false },
        { prop: 'page_tse', label: 'TSE', width: '150', filterable: false },
        { prop: 'update_by', label: '更新人', width: '150', filterable: false },
        { prop: 'update_date', label: '更新时间', width: '200', sortable: true, filterable: false },
        { prop: 'editor_num', label: '编辑人数', width: '100', sortable: true, filterable: false },
        { prop: 'edit_num', label: '编辑人次', width: '100', sortable: true, filterable: false },
        { prop: 'view_visitor_num', label: '浏览人数', width: '100', sortable: true, filterable: false },
        { prop: 'view_visit_num', label: '浏览人次', width: '100', sortable: true, filterable: false },
    ]
}

// 特性看板抽屉列配置 - 变更详情
const featureDrawerColumnDictChange = {
    analysis: [
        ...featureDrawerColumnDictCumulative.analysis,
        { prop: 'change_type', label: '变更类型', width: '100', sortable: true, fixed: 'right', filterable: false },
        { prop: 'change_detail', label: '变更原因', width: '150', fixed: 'right', filterable: false },
    ],
    scheme: [
        ...featureDrawerColumnDictCumulative.scheme,
        { prop: 'change_type', label: '变更类型', width: '100', sortable: true, fixed: 'right', filterable: false },
        { prop: 'change_detail', label: '变更原因', width: '150', fixed: 'right', filterable: false },
    ]
}

// ==================== 计算属性（动态根据当前看板切换） ====================
// 图表标题
const compChartTitle = computed(() => `各领域${getDataTypeLabel(compEchartSelectedDataType.value)}累计趋势`)
const compDailyChartTitle = computed(() => `各领域每日新增${getDataTypeLabel(compEchartSelectedDataType.value)}`)
const featureChartTitle = computed(() => `各领域${getDataTypeLabel(featureEchartSelectedDataType.value)}累计趋势`)
const featureDailyChartTitle = computed(() => `各领域每日新增${getDataTypeLabel(featureEchartSelectedDataType.value)}`)

// 抽屉相关计算属性
const drawerTableKey = computed(() => `${activeBoardTab.value}-${activeBoardTab.value === 'comp' ? compTableSelectedPageType.value : featureTableSelectedPageType.value}-${currentStatus.value}`)

const currentDrawerColumns = computed(() => {
    if (activeBoardTab.value === 'comp') {
        const dict = isChangeDetail.value ? compDrawerColumnDictChange : compDrawerColumnDictCumulative
        return dict[compTableSelectedPageType.value] || dict.comp
    } else {
        const dict = isChangeDetail.value ? featureDrawerColumnDictChange : featureDrawerColumnDictCumulative
        return dict[featureTableSelectedPageType.value] || dict.analysis
    }
})

const drawerHeader = computed(() => {
    if (isChangeDetail.value) {
        return `${currentFieldName.value}${currentStatusLabel.value}变更详情 (${dateRangeForChange.value[0]} 至 ${dateRangeForChange.value[1]})`
    }
    return `${currentFieldName.value}${currentStatusLabel.value}明细数据`
})

const drawerEmptyDescription = computed(() => {
    if (isChangeDetail.value) {
        return `${dateRangeForChange.value[0]} 至 ${dateRangeForChange.value[1]} 内，没有${currentStatusLabel.value}变更数据`
    }
    return `${dateRange.value[0]} 至 ${dateRange.value[1]} 内，没有明细数据`
})

// 监听组件看板节点类型变化，同步更新表格的页面类型
watch(compEchartSelectedPageType, (newVal) => {
    if (newVal) {
        compTableSelectedPageType.value = newVal
    }
})

// 监听特性看板页面类型变化，同步更新表格的页面类型
watch(featureEchartSelectedPageType, (newVal) => {
    if (newVal) {
        featureTableSelectedPageType.value = newVal
    }
})

// ==================== 公共方法 ====================
const formatDate = (date) => {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
}

const setDefaultDateRange = () => {
    const now = new Date()
    const minDate = new Date(minSelectableDate)
    const start = new Date(Math.max(now.getTime() - 6 * 24 * 60 * 60 * 1000, minDate.getTime()))
    dateRange.value = [formatDate(start), formatDate(now)]
}

const disabledDate = (date) => {
    const minDate = new Date(minSelectableDate)
    minDate.setHours(0, 0, 0, 0)
    return date < minDate
}

const getDataTypeLabel = (value) => {
    const allOptions = activeBoardTab.value === 'feature' ? featureDataTypeOptionList : dataTypeOptionList
    const item = allOptions.find(i => i.value === value)
    return item ? item.label : '数据'
}

const openPage = (url) => {
    if (typeof window !== 'undefined' && url) {
        window.open(url, '_blank')
    } else {
        MessagePlugin.warning('URL无效，无法跳转')
    }
}

// ==================== 数据刷新方法 ====================
// 刷新组件看板数据
const refreshCompData = async () => {
    let [start, end] = dateRange.value || []
    if (!start || !end) {
        MessagePlugin.warning('请选择完整日期范围')
        return
    }

    const params = {
        start_date: start,
        end_date: end,
        page_type: compEchartSelectedPageType.value,
        data_type: compEchartSelectedDataType.value
    }

    try {
        const [chartRes, tableRes] = await Promise.all([
            knowQueryCompTreeBoardGraphSumDataDict(params),
            knowQueryCompTreeBoardTableSumDataDict(params)
        ])

        // 处理图表数据 - 累计趋势
        const cumulativeData = chartRes.body.data?.cumulative_data
        if (cumulativeData) {
            const dateList = cumulativeData.date_list || []
            const dataList = cumulativeData.data_list || []
            const formattedData = []
            dataList.forEach(item => {
                const fieldName = item.name
                const values = item.data || []
                values.forEach((value, index) => {
                    if (dateList[index]) {
                        formattedData.push({ date: dateList[index], field_name: fieldName, value })
                    }
                })
            })
            compEchartDataList.value = formattedData
        }

        // 处理图表数据 - 日增量
        const dailyData = chartRes.body.data?.daily_data
        if (dailyData) {
            const dateList = dailyData.date_list || []
            const dataList = dailyData.data_list || []
            const formattedDailyData = []
            dataList.forEach(item => {
                const fieldName = item.name
                const values = item.data || []
                values.forEach((value, index) => {
                    if (dateList[index]) {
                        formattedDailyData.push({ date: dateList[index], field_name: fieldName, value })
                    }
                })
            })
            compDailyIncrementData.value = formattedDailyData
        }

        // 处理表格数据
        const tableData = tableRes.body.data || {}
        const tableList = []
        Object.keys(tableData).forEach(fieldName => {
            const fieldItem = tableData[fieldName]
            const endData = fieldItem.end_data || {}
            const diffMetrics = fieldItem.diff_metrics || {}
            const finishRate = endData.sum_num > 0
                ? ((endData.finish_num / endData.sum_num) * 100).toFixed(2) + '%'
                : '0%'

            tableList.push({
                field_name: fieldName,
                sum_num_end: endData.sum_num || 0,
                initial_end: endData.initial_num || 0,
                reviewed_end: endData.reviewed_num || 0,
                revision_end: endData.revision_num || 0,
                blank_end: endData.blank_num || 0,
                finish_end: endData.finish_num || 0,
                initial_change: diffMetrics.initial_num || 0,
                reviewed_change: diffMetrics.reviewed_num || 0,
                revision_change: diffMetrics.revision_num || 0,
                blank_change: diffMetrics.blank_num || 0,
                finish_change: diffMetrics.finish_num || 0,
                finish_rate: finishRate,
                sum_editor_num: endData.sum_editor_num || 0,
                sum_edit_num: endData.sum_edit_num || 0,
                sum_view_visitor_num: endData.sum_view_visitor_num || 0,
                sum_view_visit_num: endData.sum_view_visit_num || 0,
                actual_start_date: fieldItem.actual_start_date || start,
                actual_end_date: fieldItem.actual_end_date || end
            })
        })
        compTableList.value = tableList
        MessagePlugin.success('数据加载成功')
    } catch (error) {
        console.error('组件看板数据加载失败:', error)
        MessagePlugin.error('获取数据失败')
    }
}

// 刷新特性看板数据
const refreshFeatureData = async () => {
    let [start, end] = dateRange.value || []
    if (!start || !end) {
        MessagePlugin.warning('请选择完整日期范围')
        return
    }

    const params = {
        start_date: start,
        end_date: end,
        page_type: featureEchartSelectedPageType.value,
        data_type: featureEchartSelectedDataType.value
    }

    try {
        const [chartRes, tableRes] = await Promise.all([
            knowQueryFeatureTreeBoardGraphSumDataDict(params),
            knowQueryFeatureTreeBoardTableSumDataDict(params)
        ])

        // 处理图表数据 - 累计趋势
        const cumulativeData = chartRes.body.data?.cumulative_data
        if (cumulativeData) {
            const dateList = cumulativeData.date_list || []
            const dataList = cumulativeData.data_list || []
            const formattedData = []
            dataList.forEach(item => {
                const fieldName = item.name
                const values = item.data || []
                values.forEach((value, index) => {
                    if (dateList[index]) {
                        formattedData.push({ date: dateList[index], field_name: fieldName, value })
                    }
                })
            })
            featureEchartDataList.value = formattedData
        }

        // 处理图表数据 - 日增量
        const dailyData = chartRes.body.data?.daily_data
        if (dailyData) {
            const dateList = dailyData.date_list || []
            const dataList = dailyData.data_list || []
            const formattedDailyData = []
            dataList.forEach(item => {
                const fieldName = item.name
                const values = item.data || []
                values.forEach((value, index) => {
                    if (dateList[index]) {
                        formattedDailyData.push({ date: dateList[index], field_name: fieldName, value })
                    }
                })
            })
            featureDailyIncrementData.value = formattedDailyData
        }

        // 处理表格数据
        const tableData = tableRes.body.data || {}
        const tableList = []
        Object.keys(tableData).forEach(fieldName => {
            const fieldItem = tableData[fieldName]
            const endData = fieldItem.end_data || {}
            const diffMetrics = fieldItem.diff_metrics || {}
            const finishRate = endData.sum_num > 0
                ? ((endData.finish_num / endData.sum_num) * 100).toFixed(2) + '%'
                : '0%'

            tableList.push({
                field_name: fieldName,
                sum_num_end: endData.sum_num || 0,
                initial_end: endData.initial_num || 0,
                reviewed_end: endData.reviewed_num || 0,
                revision_end: endData.revision_num || 0,
                blank_end: endData.blank_num || 0,
                finish_end: endData.finish_num || 0,
                initial_change: diffMetrics.initial_num || 0,
                reviewed_change: diffMetrics.reviewed_num || 0,
                revision_change: diffMetrics.revision_num || 0,
                blank_change: diffMetrics.blank_num || 0,
                finish_change: diffMetrics.finish_num || 0,
                finish_rate: finishRate,
                sum_editor_num: endData.sum_editor_num || 0,
                sum_edit_num: endData.sum_edit_num || 0,
                sum_view_visitor_num: endData.sum_view_visitor_num || 0,
                sum_view_visit_num: endData.sum_view_visit_num || 0,
                actual_end_date: fieldItem.actual_end_date || end
            })
        })
        featureTableList.value = tableList
        MessagePlugin.success('数据加载成功')
    } catch (error) {
        console.error('特性看板数据加载失败:', error)
        MessagePlugin.error('获取数据失败')
    }
}

// 统一刷新数据入口
const refreshData = () => {
    if (activeBoardTab.value === 'comp') {
        refreshCompData()
    } else {
        refreshFeatureData()
    }
}

// ==================== 明细数据方法 ====================
// 显示节点总数明细
const showTableSumDetail = async (row) => {
    currentFieldName.value = row.field_name
    currentStatus.value = '节点总数'
    currentStatusLabel.value = '节点总数'
    isChangeDetail.value = false

    try {
        let response
        if (activeBoardTab.value === 'comp') {
            response = await knowQueryCompTreeBoardTableCumulativeDetailList({
                script_date: row.actual_end_date,
                page_type: compTableSelectedPageType.value,
                page_status: '节点总数',
                field_name: row.field_name,
            })
        } else {
            response = await knowQueryFeatureTreeBoardTableCumulativeDetailList({
                script_date: row.actual_end_date,
                page_type: featureTableSelectedPageType.value,
                page_status: '节点总数',
                field_name: row.field_name,
            })
        }
        drawerData.value = response.body.data || []
        if (pubTableRef.value) {
            pubTableRef.value.refresh()
        }
        drawerVisible.value = true
    } catch (error) {
        console.error(error)
        MessagePlugin.error('获取节点总数明细失败')
    }
}

// 显示指定状态累计明细
const showTableNumDetail = async (row, pageStatus) => {
    currentFieldName.value = row.field_name
    currentStatus.value = pageStatus
    currentStatusLabel.value = pageStatus
    isChangeDetail.value = false

    try {
        let response
        if (activeBoardTab.value === 'comp') {
            response = await knowQueryCompTreeBoardTableCumulativeDetailList({
                script_date: row.actual_end_date,
                page_type: compTableSelectedPageType.value,
                page_status: pageStatus,
                field_name: row.field_name,
            })
        } else {
            response = await knowQueryFeatureTreeBoardTableCumulativeDetailList({
                script_date: row.actual_end_date,
                page_type: featureTableSelectedPageType.value,
                page_status: pageStatus,
                field_name: row.field_name,
            })
        }
        drawerData.value = response.body.data || []
        if (pubTableRef.value) {
            pubTableRef.value.refresh()
        }
        drawerVisible.value = true
    } catch (error) {
        console.error(error)
        MessagePlugin.error('获取明细数据失败')
    }
}

// 显示变更详情
const showTableChangeDetail = async (row, pageStatus) => {
    currentFieldName.value = row.field_name
    currentStatus.value = pageStatus
    currentStatusLabel.value = pageStatus
    isChangeDetail.value = true

    const [start, end] = dateRange.value || []
    if (!start || !end) {
        MessagePlugin.warning('请选择完整日期范围')
        return
    }
    dateRangeForChange.value = [start, end]

    try {
        let response
        if (activeBoardTab.value === 'comp') {
            response = await knowQueryCompTreeBoardTableChangeDetailList({
                field_name: row.field_name,
                page_type: compTableSelectedPageType.value,
                page_status: pageStatus,
                start_date: start,
                end_date: end,
            })
        } else {
            response = await knowQueryFeatureTreeBoardTableChangeDetailList({
                field_name: row.field_name,
                page_type: featureTableSelectedPageType.value,
                page_status: pageStatus,
                start_date: start,
                end_date: end,
            })
        }
        drawerData.value = response.body.data || []
        if (pubTableRef.value) {
            pubTableRef.value.refresh()
        }
        drawerVisible.value = true
    } catch (error) {
        console.error(error)
        MessagePlugin.error('获取变更详情失败')
    }
}

// 抽屉关闭处理
const handleCloseDrawer = () => {
    drawerVisible.value = false
    isChangeDetail.value = false
    dateRangeForChange.value = []
}

const onDrawerOpened = () => {
    console.log('[知识看板] 抽屉打开动画完成')
}

// 看板切换处理
// 看板切换处理
const handleBoardChange = async (value) => {
    if (value === 'comp') {
        await refreshCompData()
        // 等待 DOM 更新后调整图表尺寸
        await nextTick()
        // 多次调用 resize 确保图表正确渲染
        setTimeout(() => {
            if (compCumulativeChartRef.value) {
                compCumulativeChartRef.value.resize?.()
            }
            if (compDailyChartRef.value) {
                compDailyChartRef.value.resize?.()
            }
        }, 100)
    } else {
        await refreshFeatureData()
        await nextTick()
        setTimeout(() => {
            if (featureCumulativeChartRef.value) {
                featureCumulativeChartRef.value.resize?.()
            }
            if (featureDailyChartRef.value) {
                featureDailyChartRef.value.resize?.()
            }
        }, 100)
    }
}

let resizeObserver = null

onMounted(() => {
    setDefaultDateRange()
    refreshCompData()
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
})

const handleResize = () => {
    if (activeBoardTab.value === 'comp') {
        compCumulativeChartRef.value?.resize?.()
        compDailyChartRef.value?.resize?.()
    } else {
        featureCumulativeChartRef.value?.resize?.()
        featureDailyChartRef.value?.resize?.()
    }
}

// ==================== 生命周期 ====================
onMounted(() => {
    setDefaultDateRange()
    refreshCompData()
})

// 暴露方法
defineExpose({
    refreshData,
    showTableSumDetail,
    showTableNumDetail,
    showTableChangeDetail,
    openPage
})
</script>

<style scoped>
.knowledge-board-container {
    background-color: #ffffff;
    margin-top: -10px;
    padding: 11px;
}

.board-content {
    margin-top: 20px;
}

/* 表头边框 - 显示所有表格线 */
:deep(.t-table__header th) {
    background-color: #f5f7fa;
    border: 1px solid #e0e0e0;
    padding: 8px 8px !important;
}

/* 数据单元格边框 */
:deep(.t-table__body td) {
    border: 1px solid #e0e0e0;
    padding: 8px 8px !important;
}

/* 悬停效果 */
:deep(.t-table__row:hover) {
    background-color: #f5f5f5;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 400px;
    padding: 20px;
    text-align: center;
}

.empty-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2d3d;
    margin-bottom: 8px;
}

.empty-description {
    font-size: 14px;
    color: #8492a6;
    margin-bottom: 20px;
    max-width: 400px;
}

.loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 300px;
}

.checkbox-group {
    width: 100%;
}

/* 时间选择器输入框文本居中 */
:deep(.date-range-picker-center .t-input) {
    text-align: center !important;
}

:deep(.date-range-picker-center .t-input__inner) {
    text-align: center !important;
    justify-content: center !important;
}

:deep(.date-range-picker-center .t-input--focused) {
    text-align: center !important;
}

/* Tabs 样式微调 */
:deep(.t-tabs__nav-wrap) {
    padding: 0 16px;
}

:deep(.t-tabs__nav-item) {
    font-size: 16px;
    font-weight: 500;
}
</style>