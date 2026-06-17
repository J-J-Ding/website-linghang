<template>
  <div class="dashboard-container">
    <!-- 四个下拉框：人工/自动/所有 和 标准/非标准/所有 以独立下拉框形式呈现 -->
    <div class="filter-row">
      <!-- 额外添加一个占位下拉框使布局均匀，也可根据实际需求隐藏或使用 -->
      <t-select 
      class="filter-select-extra" 
      v-model="extraValue"
      label="需求预规划: "
      multiple 
      filterable
      :minCollapsedNum="1" 
      placeholder="请选择需求预规划" 
      @popup-visible-change="getMileStoneOptions"
      @change="changeParams">
        <t-option v-for="item in milestoneOption" :key="item" :value="item" :label="item"></t-option>
      </t-select>
      
      <t-select v-model="manualAutoValue" label="拆分方式: " class="filter-select" placeholder="人工/自动/所有" @change="changeParams">
        <t-option value="man" label="人工" />
        <t-option value="auto" label="自动" />
        <t-option value="all" label="所有" />
      </t-select>

      <t-select v-model="standardNonValue" label="是否标准特性: " class="filter-select" placeholder="标准/非标准/所有" @change="changeParams">
        <t-option value="standard" label="标准特性" />
        <t-option value="special" label="非标准特性" />
        <t-option value="all" label="所有" />
      </t-select>

      <!-- 开始日期和结束日期合并为一个日期范围组件 -->
      <!-- <t-date-range-picker
        v-model="dateRange"
        format="YYYY-MM-DD"
        value-type="YYYY-MM-DD"
        :clearable="false"
        :disabled-date="disabledDate"
        @change="changeParams"
      /> -->
      <t-date-range-picker
        v-model="dateRange"
        format="YYYY-MM-DD"
        value-type="YYYY-MM-DD"
        placeholder="请选择时间"
        :disable-date="disabledDate"
        @change="changeParams"
      />
    </div>

    <!-- 两个曲线图卡片并排 -->
    <div class="charts-row">
      <!-- 需求个数变化曲线图 -->
      <t-card class="chart-card" :bordered="false">
        <template #title>
          <div style="display: flex; align-items: center; padding-left: 16px; margin-top: 10px">
            <span style="font-size: 16px; font-weight: 500; color: #1f2f3d">
              需求个数变化曲线图 
            </span>
            <t-tooltip
              content="以下日数据均为累计数据"
              placement="right">
              <HelpCircleFilledIcon 
                size="1em" 
                style="margin-left: 8px; color: var(--td-brand-color); cursor: help;" 
              />
            </t-tooltip>
          </div>
        </template>
        <template #actions>
          <div class="chart-actions">
            <t-button variant="text" size="small" @click="toggleFullscreen(1)">
              <t-icon :name="fullscreenMap[1] ? 'fullscreen-exit' : 'fullscreen'" />
              {{ fullscreenMap[1] ? '退出全屏' : '全屏' }}
            </t-button>
          </div>
        </template>
        <div class="chart-container" :class="{ 'fullscreen-chart': fullscreenMap[1] }">
          <div ref="chart1Ref" class="chart-instance"></div>
        </div>
      </t-card>

      <!-- 需求特性占比曲线图 -->
      <t-card class="chart-card" :bordered="false">
        <template #title>
          <div style="display: flex; align-items: center; padding-left: 16px; margin-top: 10px">
            <span class="card-title">需求特性占比曲线图</span>
          </div>
        </template>
        <template #actions>
          <div class="chart-actions">
            <t-button variant="text" size="small" @click="toggleFullscreen(2)">
              <t-icon :name="fullscreenMap[2] ? 'fullscreen-exit' : 'fullscreen'" />
              {{ fullscreenMap[2] ? '退出全屏' : '全屏' }}
            </t-button>
          </div>
        </template>
        <div class="chart-container" :class="{ 'fullscreen-chart': fullscreenMap[2] }">
          <div ref="chart2Ref" class="chart-instance"></div>
        </div>
      </t-card>
    </div>

    <!-- 表格标题：各需求预规划在某日期需求拆分情况统计表格 (支持下钻) -->
    <div class="table-header">
      <span class="table-title">需求拆分统计表格</span>
      <span class="table-subtitle">（点击查看明细）</span>
    </div>

    <!-- 统计表格 - 修复pagination属性 -->
    <t-table
      row-key="id"
      :data="milestoneData"
      :columns="columns"
      :pagination="pagination"
      :bordered="true"
      :hover="true"
      style="margin-top: 16px"
    >
      <!-- 需求预规划列 自定义渲染下钻图标 (模拟) -->
      <!-- <template #preplanning="{ row }">
        <span 
          class="drilldown-cell"
    
        >
          {{ row.preplanning }}
        </span>
      </template> -->
      <template #index="{ rowIndex }">
        <span>{{ rowIndex + 1 }}</span>
      </template>

      <template #all_all_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'all', 'all', '所有需求数')"
        >
          {{ row.all_all_num }}
        </span>
      </template>

      <template #all_standard_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'all', 'standard', '标准特性需求数')"
        >
          {{ row.all_standard_num }}
        </span>
      </template>

      <template #all_special_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'all', 'special', '非标准特性需求数')"
        >
          {{ row.all_special_num }}
        </span>
      </template>

      <template #auto_all_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'auto', 'all', '自动拆分需求数')"
        >
          {{ row.auto_all_num }}
        </span>
      </template>

      <template #auto_standard_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'auto', 'standard', '自动拆分标准特性需求数')"
        >
          {{ row.auto_standard_num }}
        </span>
      </template>

      <template #auto_special_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'auto', 'special', '自动拆分非标准特性需求数')"
        >
          {{ row.auto_special_num }}
        </span>
      </template>

      <template #man_all_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'man', 'all', '人工拆分需求数')"
        >
          {{ row.man_all_num }}
        </span>
      </template>

      <template #man_standard_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'man', 'standard', '自动拆分标准特性需求数')"
        >
          {{ row.man_standard_num }}
        </span>
      </template>

      <template #man_special_num="{ row }">
        <span
          class="drilldown-cell"
          style="cursor: pointer; color: #0052d9"
          @click.stop="handleRowClick(row, 'man', 'special', '自动拆分非标准特性需求数')"
        >
          {{ row.man_special_num }}
        </span>
      </template>
    </t-table>

    <!-- 下钻提示消息 -->
    <t-drawer
      :visible.sync="visibleDrawer"
      placement="top"
      size="80%"
      destroyOnClose
      @close="handleClose"
      :confirmBtn="{
        content: '导出CSV',
        theme: 'primary',
        onClick: handleExportExcel
      }"
      cancelBtn="关闭"
      closeOnEscKeydown
    >
      <template #header>
        <div style="display: flex; align-items: center; width: 100%;">
          <span style="font-size: 18px; font-weight: 500; color: #1f2f3d">
            {{ titleHeader + '明细' }}
          </span>
          <t-tooltip :content="dateRange[0] + ' 至 ' + dateRange[1] + ' 之间的数据明细'">
            <HelpCircleFilledIcon 
              size="1.1em" 
              style="margin-left: 8px; color: var(--td-brand-color); cursor: help;" 
            />
          </t-tooltip>
        </div>
      </template>

      <div v-if="requireData.length === 0" class="empty-state">
        <t-icon name="folder-off" size="70px" style="color: var(--td-brand-color-light); margin-bottom: 16px" />
        <p class="empty-title">暂无数据</p>
        <p class="empty-description">{{ dateRange[0] }}至{{ dateRange[1] }}内，{{ titleHeader }}没有明细数据</p>
      </div>

      <div v-else class="checkbox-group">
        <t-table
          ref="tableRef"
          row-key="id"
          :data="requireData"
          :columns="requireColumns"
          :filter-value="filterValue"
          :pagination="pagination"
          :scroll="{ type: 'virtual' }"
          :hover="true"
          bordered
          resizable
          table-layout="fixed"
          max-height="62vh"
          @filter-change="onFilterChange"
        >
          <!-- 需求预规划列 自定义渲染下钻图标 (模拟) -->
          <!-- <template #preplanning="{ row }">
            <span class="drilldown-cell">
              <t-icon name="drill-down" size="16" class="drill-icon" />
              {{ row.preplanning }}
            </span>
          </template> -->
          <template #index="{ rowIndex }">
            <span>{{ rowIndex + 1 }}</span>
          </template>
        </t-table>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount, watch, markRaw, computed } from 'vue';
import dayjs from 'dayjs';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import * as echarts from 'echarts';
import { queryChartData, queryPreplan, queryTableData, queryManageBoard } from '@/api/chart';
import { DateRangePickerPanel, Select } from 'tdesign-vue-next';
import * as XLSX from 'xlsx'; // 需要安装 xlsx 库

const tableRef = ref(null);
// 下拉框绑定值
const manualAutoValue = ref('auto');
const standardNonValue = ref('all');
const extraValue = ref(['所有']);
// 日期范围绑定 [开始, 结束]
const dateRange = ref([]);
const dataArray = ref([]);
// 图表实例引用
const chart1Ref = ref(null);
const chart2Ref = ref(null);
let chart1 = null;
let chart2 = null;
const filterValue = ref({});
// 保存原始配置以便重置缩放
const chart1Option = ref(null);
const chart2Option = ref(null);
const titleHeader = ref(''); // 标题头
// 曲线选择
const selectedSeries = ref('all');
const visibleDrawer = ref(false);
const disableTime = ref(null);
const dateList = ref([]); // 日期列表
const allNumList = ref([]); // 数组列表
const numList = ref([]); // 数组列表
const rateList = ref([]); // 数组列表
// 全屏状态管理
const fullscreenMap = ref({
  1: false,
  2: false,
});
const milestoneOption = ref([]);

// 表格列定义 —— 按照图片描述，列名与需求一致
const columns = [
  { colKey: 'index', title: '编号', width: '70', align: 'center' },
  { colKey: 'preplanning', title: '需求预规划', width: '160', cell: 'preplanning', align: 'center' },
  { colKey: 'all_all_num', title: '所有需求数', width: '110', align: 'center' },
  { colKey: 'all_standard_num', title: '标准特性需求数', width: '140', align: 'center' },
  { colKey: 'all_special_num', title: '非标准特性需求数', width: '160', align: 'center' },
  { colKey: 'auto_all_num', title: '自动拆分需求数', width: '140', align: 'center' },
  { colKey: 'auto_standard_num', title: '自动拆分标准特性需求数', width: '200', align: 'center' },
  { colKey: 'auto_special_num', title: '自动拆分非标准特性需求数', width: '210', align: 'center' },
  { colKey: 'man_all_num', title: '人工拆分需求数', width: '140', align: 'center' },
  { colKey: 'man_standard_num', title: '人工拆分标准特性需求数', width: '200', align: 'center' },
  { colKey: 'man_special_num', title: '人工拆分非标准特性需求数', width: '210', align: 'center' },
];
const requireColumns = [
  { colKey: 'index', title: '编号', width: '70', align: 'center' },
  {
    colKey: 'system_id',
    title: () => (<div style={{ textAlign: 'center' }}>需求标识</div>),
    width: '150',
    align: 'center',
    //cell: (_, { row }) => (<t-link theme="primary" href={`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${row.rdc_ident}?teamId=bdv_106024`} target="_blank" hover="underline">{row.rdc_ident}</t-link>)
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

      // 使用
      const href = getRdcHref(row.system_id);

      return (
        <t-link
          theme="primary"
          href={href}
          target="_blank"
          hover="underline"
        >
          {row.system_id}
        </t-link>
      );
    },
  },
  {
    colKey: 'system_title',
    title: '需求标题',
    width: '300',
    ellipsis: { theme: 'light', placement: 'bottom' },
    filter: {
      type: 'input',

      // 文本域搜索
      // component: Textarea,

      resetValue: '',
      // 按下 Enter 键时也触发确认搜索
      confirmEvents: ['onEnter'],
      props: {
        placeholder: '输入需求标题过滤',
      },
      // 是否显示重置取消按钮，一般情况不需要显示
      showConfirmAndReset: true,
    },
  },
  {
    colKey: 'requirementpreplanning',
    title: '需求预规划',
    width: '160',
    align: 'center'
  },
  {
    colKey: 'system_createddate',
    title: '需求创建时间',
    width: '180',
    align: 'center'
  },
  { colKey: 'system_createdby', title: '需求创建人', width: '160', align: 'center' },
  { colKey: 'system_changeddate', title: '需求更新时间', width: '180', align: 'center' },
  { colKey: 'system_changedby', title: '需求更新人', width: '160', align: 'center' },
  { colKey: 'system_appointedto', title: '指派给', width: '160', align: 'center' },
  { colKey: 'system_areapath', title: '领域', width: '150', align: 'center' },
  { colKey: 'team', title: '团队', width: '160', align: 'center' },
  { 
    colKey: 'belongproduct',
    title: '所属产品',
    width: '120',
    align: 'center',
    filter: {
      type: 'input',

      // 文本域搜索
      // component: Textarea,

      resetValue: '',
      // 按下 Enter 键时也触发确认搜索
      confirmEvents: ['onEnter'],
      props: {
        placeholder: '输入所属产品过滤',
      },
      // 是否显示重置取消按钮，一般情况不需要显示
      showConfirmAndReset: true,
    },
  },
  { colKey: 'system_description_html', title: '描述', width: '200', align: 'center' },
  { colKey: 'acceptancecriteria_html', title: '验收准则', width: '200', align: 'center' },
  { colKey: 'requirementanalysisowner', title: '需求分析负责人', width: '160', align: 'center' },
  {
    colKey: 'specificationbyexampleurl',
    title: 'iCenter实例化链接',
    width: '200',
    ellipsis: { theme: 'light', placement: 'bottom' },
    cell: (_, { row }) => (<t-link theme="primary" href={row.specificationbyexampleurl} target="_blank" hover="underline">{row.specificationbyexampleurl}</t-link>)
  },
  // { colKey: 'specificationbyexampleurl', title: 'iCenter实例化链接', width: '160' },
  { colKey: 'specificationbyexamplestate', title: '需求实例化状态', width: '140', align: 'center' },
  {
    colKey: 'designspecificationurl',
    title: '方案文档链接',
    width: '200',
    ellipsis: { theme: 'light', placement: 'bottom' },
    cell: (_, { row }) => (<t-link theme="primary" href={row.designspecificationurl} target="_blank" hover="underline">{row.designspecificationurl}</t-link>)
  },
  // { colKey: 'designspecificationurl', title: '方案文档链接', width: '140' },
  { colKey: 'designstate', title: '方案状态', width: '120' },
  {
    colKey: 'featureurl',
    title: '特性内容链接',
    width: '200',
    ellipsis: { theme: 'light', placement: 'bottom' },
    cell: (_, { row }) => (<t-link theme="primary" href={row.featureurl} target="_blank" hover="underline">{row.featureurl}</t-link>)
  },
  // { colKey: 'featureurl', title: '特性内容链接', width: '140' },
  { colKey: 'belongfeaturecatalog', title: '所属特性分类', width: '140', align: 'center' },
  { colKey: 'featureid', title: '特性标识', width: '140', align: 'center' },
  { colKey: 'featurename_cn', title: '特性名称', width: '140', align: 'center' },
  { colKey: 'checkresultofchipscheme', title: '特性链接检查结论', width: '160', align: 'center' },
  { colKey: 'isautocreated', title: '是否自动拆分', width: '120', align: 'center' },
  { colKey: 'assessresult_first', title: '初评结论', width: '120', align: 'center' },
  { colKey: 'reusedegree', title: '复用程度', width: '120', align: 'center' },
  { colKey: 'script_update_date', title: '脚本更新日期', width: '160', align: 'center' },
  {
    colKey: 'system_state',
    title: '状态',
    width: '120',
    align: 'center',
    fixed: 'right',
    cell: (_, { row }) => (<t-tag theme={row.system_state === '新建' ? 'primary':row.system_state === '已分析' ? 'success': 'warning'} size="small">{row.system_state}</t-tag>),
    filter: {
      // 过滤行中的列标题别名
      // label: '申请状态 A',
      type: 'single',
      list: [
        { label: '新建', value: '新建' },
        { label: '分析中', value: '分析中' },
        { label: '已分析', value: '已分析' },
      ],
      // confirm to search and hide filter popup
      confirmEvents: ['onChange'],
      // 支持透传全部 Popup 组件属性
      // popupProps: {
      //   attach: () => document.body,
      // },
    },
  },
];
// 模拟表格数据（各需求预规划统计数据）
const milestoneData = ref([]);
const requireData = ref([]);
// 分页配置 - 修复pagination属性错误，设置为null表示不显示分页
const pagination = null;

// 消息提示
const messageVisible = ref(false);
const messageContent = ref('');

// 行点击下钻模拟
const handleRowClick = async (row, manualAutoValue, standardNonValue, headStr) => {
  messageVisible.value = true;
  visibleDrawer.value = true;
  titleHeader.value = headStr;
  await queryTableDetail(row.preplanning, manualAutoValue, standardNonValue, dateRange.value);
};

const request = (filters) => {
  const timer = setTimeout(() => {
    clearTimeout(timer);
    const newData = dataArray.value.filter((item) => {
      let result = true;
      if (result && filters.system_title) {
        result = item.system_title.indexOf(filters.system_title) !== -1;
      }
      if (result && filters.system_state) {
        result = item.system_state === filters.system_state;
      }
      if (result && filters.belongproduct) {
        result = item.belongproduct.indexOf(filters.belongproduct) !== -1;
      }
      return result;
    });
    requireData.value = newData;
  }, 100);
};

const onFilterChange = (filters, ctx) => {
  filterValue.value = {
    ...filters,
  };
  console.log(filters);
  request(filters);
};

const setVisible = (state) => {
  visibleDrawer.value = state;
};

const handleClose = () => {
  setFilters();
  setVisible(false);
  requireData.value = [];
  dataArray.value = [];
};

const setFilters = () => {
  filterValue.value = {};
};

const getMileStoneOptions = async () => {
  const response = await queryPreplan();
  milestoneOption.value = response.data;
};

const setDateRangeToLast7Days = () => {
  dateRange.value = [
    dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  ]
};

const queryTableList = async (extraValue, manualAutoValue, standardNonValue, dateRange) => {
  try {
    const data = {
      preplanning_list: extraValue,
      start_date: dateRange[0],
      end_date: dateRange[1],
      auto_field: manualAutoValue,
      standard_field: standardNonValue,
    };
    const responseChart = await queryTableData(data);
    milestoneData.value = responseChart.data;
  } catch (error) {
    console.log('获取图表数据失败，请重试', error);
  }
};

const queryTableDetail = async (extraValue, manualAutoValue, standardNonValue, dateRange) => {
  try {
    const data = {
      preplanning: extraValue,
      start_date: dateRange[0],
      end_date: dateRange[1],
      auto_field: manualAutoValue,
      standard_field: standardNonValue,
    };
    const responseChart = await queryManageBoard(data);
    dataArray.value = responseChart.data;
    requireData.value = dataArray.value;
  } catch (error) {
    console.log('获取图表数据失败，请重试', error);
  }
};

const queryChartList = async (extraValue, manualAutoValue, standardNonValue, dateRange) => {
  try {
    const data = {
      preplanning_list: extraValue,
      start_date: dateRange[0],
      end_date: dateRange[1],
      auto_field: manualAutoValue,
      standard_field: standardNonValue,
    };
    const responseChart = await queryChartData(data);
    //dateList.value = responseChart.data[0].date_list; // 日期列表
    allNumList.value = responseChart.data; // 数组列表
    //numList.value = responseChart.data[0].obj_num_list; // 数组列表
    //rateList.value = responseChart.data[0].obj_rate_list; // 数组列表
  } catch (error) {
    console.log('获取图表数据失败，请重试', error);
  }
};

// 重置图表缩放
const resetZoom = (chartIndex) => {
  console.log('chartIndex', chartIndex);
  if (chartIndex === 1 && chart1 && chart1Option.value) {
    chart1.setOption({
      dataZoom: null, // 清除缩放
    });
    // 重新设置原始数据范围
    chart1.setOption({
      xAxis: {
        data: dateList.value,
      },
      yAxis: {
        min: null,
        max: null,
      },
    });
  } else if (chartIndex === 2 && chart2 && chart2Option.value) {
    chart2.setOption({
      dataZoom: null,
    });
    chart2.setOption({
      xAxis: {
        data: dateList.value,
      },
      yAxis: {
        min: null,
        max: null,
      },
    });
  }
};

// 切换全屏
const toggleFullscreen = (chartIndex) => {
  fullscreenMap.value[chartIndex] = !fullscreenMap.value[chartIndex];
  // 延迟执行resize，等待DOM更新完成
  setTimeout(() => {
    if (chartIndex === 1 && chart1) {
      chart1.resize();
    } else if (chartIndex === 2 && chart2) {
      chart2.resize();
    }
  }, 100);
};

const initCharts = (data) => {
  // 从allNumList.value获取数据
  const allData = data;
  
  // 提取日期数据（所有子数组的日期相同，取第一个）
  dateList.value = allData[0]?.date_list || [];

  // 销毁现有的图表实例
  if (chart1) {
    chart1.dispose();
    chart1 = null;
  }
  
  if (chart2) {
    chart2.dispose();
    chart2 = null;
  }

  if (chart1Ref.value) {
    chart1 = echarts.init(chart1Ref.value);
    
    // 构建系列数据 - 已完成需求数图
    const series1 = allData.map((item) => ({
      name: item.preplanning,
      type: 'line',
      data: item.obj_num_list,
      smooth: true,
      lineStyle: { width: 3 },
      symbol: 'circle',
      symbolSize: 8,
      emphasis: {
        focus: 'series',
        itemStyle: {
          symbolSize: 12,
        },
      },
      label: {
        show: true,
        position: 'top',
        formatter: function(params) {
          return params.value;
        },
        fontSize: 11,
        color: '#e67c3b',
      },
    }));

    // 计算所有数据的最小值用于Y轴
    const allNumValues = allData.flatMap((item) => item.obj_num_list);
    const minNum = allNumValues.length > 0 ? Math.min(...allNumValues) : 0;

    const option1 = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        type: 'scroll',
        orient: 'horizontal',
        top: 0,
        left: 'center',
        itemWidth: 20,
        itemHeight: 10,
        pageIconColor: '#2468f2',
        pageTextStyle: {
          color: '#666',
        },
      },
      grid: {
        left: '8%',
        right: '8%',
        top: 50,
        bottom: 25,
        containLabel: true,
        backgroundColor: '#fafafa',
      },
      xAxis: {
        type: 'category',
        data: dateList.value,
        axisLine: { lineStyle: { color: '#999' } },
        axisLabel: {
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        name: '需求个数',
        nameTextStyle: { color: '#666', fontSize: 12 },
        splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
        axisLabel: {
          fontSize: 12,
        },
        min: allNumValues.length > 0 ? Math.max(0, minNum - 10) : 0,
      },
      series: series1,
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          moveOnMouseWheel: true,
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          width: '80%',
          height: 20,
          left: '10%',
          right: '10%',
          bottom: 0,
          borderColor: '#ddd',
          fillerColor: 'rgba(36,104,242,0.2)',
          handleStyle: {
            color: '#2468f2',
          },
          backgroundColor: '#f5f5f5',
          showDetail: false,
          brushSelect: false,
        },
      ],
      color: ['#2468f2', '#e67c3b', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f'],
    };
    
    chart1.setOption(option1);
    chart1Option.value = option1;

    chart1.on('datazoom', (params) => {
      console.log('图表1缩放:', params);
    });
  }

  if (chart2Ref.value) {
    chart2 = echarts.init(chart2Ref.value);
    
    // 构建系列数据 - 需求占比图
    const series2 = allData.map((item) => ({
      name: item.preplanning,
      type: 'line',
      data: item.obj_rate_list,
      smooth: true,
      lineStyle: { width: 3 },
      symbol: 'circle',
      symbolSize: 8,
      emphasis: {
        focus: 'series',
        itemStyle: {
          symbolSize: 12,
        },
      },
      label: {
        show: true,
        position: 'top',
        formatter: function(params) {
          return params.value + '%';
        },
        fontSize: 11,
      },
    }));

    // 计算所有占比的最小值
    const allRateValues = allData.flatMap((item) => item.obj_rate_list);
    const minRate = allRateValues.length > 0 ? Math.min(...allRateValues) : 0;

    const option2 = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: function(params) {
          return params.map(p => {
            return `${p.marker} ${p.seriesName}: ${p.value}%`;
          }).join('<br/>');
        },
      },
      legend: {
        type: 'scroll',
        orient: 'horizontal',
        top: 0,
        left: 'center',
        itemWidth: 20,
        itemHeight: 10,
        pageIconColor: '#2468f2',
        pageTextStyle: {
          color: '#666',
        },
      },
      grid: {
        left: '8%',
        right: '8%',
        top: 50,
        bottom: 25,
        containLabel: true,
        backgroundColor: '#fafafa',
      },
      xAxis: {
        type: 'category',
        data: dateList.value,
        axisLine: { lineStyle: { color: '#999' } },
        axisLabel: {
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        name: '需求占比 (%)',
        nameTextStyle: { color: '#666', fontSize: 12 },
        splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
        axisLabel: {
          fontSize: 12,
          formatter: function(value) {
            return value + '%';
          },
        },
        min: allRateValues.length > 0 ? Math.max(0, minRate - 0.05).toFixed(2) : 0,
      },
      series: series2,
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          moveOnMouseWheel: true,
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          width: '80%',
        height: 20,
          left: '10%',
          right: '10%',
          bottom: 0,
          borderColor: '#ddd',
          fillerColor: 'rgba(36,104,242,0.2)',
          handleStyle: {
            color: '#2468f2',
          },
          backgroundColor: '#f5f5f5',
          showDetail: false,
          brushSelect: false,
        },
      ],
      color: ['#2468f2', '#e67c3b', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f'],
    };
    
    chart2.setOption(option2);
    chart2Option.value = option2;
    
    chart2.on('datazoom', (params) => {
      console.log('图表2缩放:', params);
    });
  }

  // 窗口大小变化时自适应图表
  const handleResize = () => {
    chart1?.resize();
    chart2?.resize();
  };
  
  // 先移除旧的监听器再添加新的，避免重复
  window.removeEventListener('resize', handleResize);
  window.addEventListener('resize', handleResize);
  
  // 返回清理函数（可选，用于组件卸载时）
  return () => {
    window.removeEventListener('resize', handleResize);
    if (chart1) {
      chart1.dispose();
      chart1 = null;
    }
    if (chart2) {
      chart2.dispose();
      chart2 = null;
    }
  };
};

// 监听全屏状态变化，处理样式和布局
watch(fullscreenMap, (newVal) => {
  if (newVal[1] || newVal[2]) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
}, { deep: true });

// 窗口大小自适应
const handleResize = () => {
  chart1?.resize();
  chart2?.resize();
};

const changeParams = async () => {
  await queryChartList(extraValue.value, manualAutoValue.value, standardNonValue.value, dateRange.value);
  await queryTableList(extraValue.value, manualAutoValue.value, standardNonValue.value, dateRange.value);
  initCharts(allNumList.value);
};

const disabledDate = (date) => {
  // 使用 startOf('day') 忽略时间部分
  const currentDate = dayjs(date).startOf('day');
  const minDate = dayjs('2026-01-01').startOf('day');
  const maxDate = dayjs().startOf('day');

  // 检查日期是否有效
  if (!currentDate.isValid()) return true;

  return currentDate.isBefore(minDate) || currentDate.isAfter(maxDate);
};

// 简单的CSV导出函数
const handleExportExcel = () => {
  if (!requireData.value || requireData.value.length === 0) {
    alert('暂无数据可导出');
    return;
  }

  try {
    // 准备表头 - 直接使用列标题
    const headers = requireColumns.map(col => {
      // 如果title是函数，简单处理
      if (typeof col.title === 'function') {
        // 需求标识列特殊处理
        if (col.colKey === 'system_id') {
          return '需求标识';
        }
        return col.colKey; // 其他函数式标题用colKey代替
      }
      return col.title || col.colKey;
    });

    // 准备数据行 - 保持原样，不做任何格式化
    const rows = requireData.value.map((item, index) => {
      return requireColumns.map(col => {
        // 索引列特殊处理
        if (col.colKey === 'index') {
          return index + 1;
        }
        
        // 直接返回原始数据，不做任何处理
        return item[col.colKey] !== undefined ? item[col.colKey] : '';
      });
    });

    // 组合CSV内容
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        // 只处理CSV中的逗号和引号，保持数据原样
        if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
          return `"${cell.replace(/"/g, '""')}"`;
        }
        return cell;
      }).join(','))
    ].join('\n');

    // 生成文件名
    const startDate = dateRange.value?.[0]?.replace(/-/g, '') || '';
    const endDate = dateRange.value?.[1]?.replace(/-/g, '') || '';
    const timestamp = new Date().getTime();
    const fileName = `${titleHeader.value || '需求明细'}_${startDate}_${endDate}_${timestamp}.csv`;

    // 创建Blob并下载
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);

  } catch (error) {
    console.error('导出CSV失败:', error);
    alert('导出失败，请重试');
  }
};

onMounted(async () => {
  getMileStoneOptions();
  setDateRangeToLast7Days();
  changeParams();
  window.addEventListener('resize', handleResize);
});

// 组件卸载前清除监听
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chart1?.dispose();
  chart2?.dispose();
  document.body.style.overflow = '';
});
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f5f9;
  min-height: 85vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 四个下拉框一行 */
.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  background-color: #fff;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.filter-select-extra {
  width: 350px;
}

.filter-select {
  width: 180px;
}

.date-range-picker {
  width: 180px;
}

/* 两个图表并排 */
.charts-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  flex: 1;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  position: relative;
  transition: all 0.3s ease;
}

.chart-card:has(.fullscreen-chart) {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  margin: 0;
  border-radius: 0;
  box-shadow: none;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: #1f2f3d;
  padding-left: 16px;
}

.chart-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 16px;
}

.series-select {
  width: 120px;
}

.chart-container {
  width: 100%;
  height: 280px;
  padding: 8px 0 0 0;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.fullscreen-chart {
  position: fixed;
  top: 50px;
  left: 50px;
  right: 50px;
  bottom: 50px;
  width: auto;
  height: auto;
  z-index: 1001;
  background-color: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  padding: 20px;
}

.chart-instance {
  width: 100%;
  height: 100%;
}

/* 表格标题区域 */
.table-header {
  margin: 16px 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: #1f2f3d;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.table-subtitle {
  font-size: 13px;
  color: #8d9aa8;
  font-weight: 400;
}

/* 表格内部下钻图标样式 */
.drilldown-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #2468f2;
  cursor: pointer;
}

.drill-icon {
  font-size: 16px;
  color: #2468f2;
}

/* t-table 覆写边距等 */
:deep(.t-table__th) {
  background-color: #f7f8fa;
  font-weight: 500;
  color: #1f2f3d;
  white-space: nowrap;
}

:deep(.t-table__row:hover) {
  background-color: #f2f6fc;
  cursor: pointer;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .charts-row {
    flex-direction: column;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .fullscreen-chart {
    left: 20px;
    right: 20px;
    top: 20px;
    bottom: 20px;
  }
}

.checkbox-group {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 600px;
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
  max-width: 300px;
}

/* 缩放工具栏样式 */
:deep(.t-button--variant-text) {
  color: #2468f2;
}

:deep(.t-button--variant-text:hover) {
  background-color: rgba(36, 104, 242, 0.1);
}

/* 下拉框样式优化 */
:deep(.t-select__wrap) {
  min-width: 100px;
}
</style>