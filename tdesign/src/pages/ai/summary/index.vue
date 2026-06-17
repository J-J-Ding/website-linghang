<template>
  <t-space direction="vertical">
    <t-space align="center">
      <t-button @click="tableUpdate">更新</t-button>
      <t-dropdown :options="options" :min-column-width="88">
        <t-button variant="text">显示内容</t-button>
      </t-dropdown>
      <!-- <t-button @click="setLowerHeight">lower height</t-button> -->
      <!-- <t-button @click="setHigherHeight">higher height</t-button> -->
    </t-space>
    <!-- 
        1. rowHeight 接近平均高度即可
        2. bufferSize 别太大，5 ～ 30 之间合适
        3. 如果是固定行高请设置 isFixedRowHeight: true。rowHeight 设置精确值
        4. 当数据量小于 `scroll.threshold` 时，无论虚拟滚动的配置是否存在，组件内部都不会开启虚拟滚动，默认值 100
      -->
    <t-table
      ref="tableRef"
      row-key="id"
      :columns="columns"
      :data="data"
      :height="height"
      :scroll="{ type: 'virtual', rowHeight: 48, bufferSize: 10 }"
      lazy-load
    >
    </t-table>
  </t-space>
</template>

<script setup lang="jsx">
import { ref } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { ErrorCircleFilledIcon, CheckCircleFilledIcon, CloseCircleFilledIcon } from 'tdesign-icons-vue-next';

const options = [
  {
    content: '特性参数',
    value: 1,
    onClick: () => MessagePlugin.success('特性参数'),
  },
  {
    content: '需求',
    value: 2,
    onClick: () => MessagePlugin.success('需求'),
  },
  {
    content: '故障',
    value: 3,
    onClick: () => MessagePlugin.success('故障'),
  },
  {
    content: '用例',
    value: 4,
    onClick: () => MessagePlugin.success('用例'),
  },
];



const statusNameListMap = {
  0: { label: '审批通过', theme: 'success', icon: <CheckCircleFilledIcon /> },
  1: { label: '审批失败', theme: 'danger', icon: <CloseCircleFilledIcon /> },
  2: { label: '审批过期', theme: 'warning', icon: <ErrorCircleFilledIcon /> },
};

const columns = [
  // { colKey: 'uuid', title: 'uuid', width: 80, },
  { colKey: 'number', title: '编号', width: '140' },
  // {
  //   colKey: 'status',
  //   title: '申请状态',
  //   width: '150',
  //   cell: (h, { rowIndex }) => {
  //     const status = rowIndex % 3;
  //     return (
  //       <t-tag shape="round" theme={statusNameListMap[status].theme} variant="light-outline">
  //         {statusNameListMap[status].icon}
  //         {statusNameListMap[status].label}
  //       </t-tag>
  //     );
  //   },
  // },
  { colKey: 'level1', title: '一级特性', width: '180' },
  { colKey: 'level2', title: '二级特性', width: '180' },
  { colKey: 'level3', title: '三级特性', width: '180' },
  { colKey: 'F1K', title: 'F1K', width: '180' },
  { colKey: 'F2K', title: 'F2K' }
];

const jsonData = {
  "summary_feature": [
    {
      "uuid": "",
      "编号": "TX:001-001-001",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "端口别名",
      "F1K": "M1F1K",
      "F2K": "M1F2K"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-002",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "光电类型",
      "F1K": "✅[光口, 电口]",
      "F2K": "✅[光口, 电口]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-003",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "SD使能",
      "F1K": "✅[True, False]",
      "F2K": "✅[True, False]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-004",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "端口上电延时",
      "F1K": "✅[0, 360]",
      "F2K": "✅[0, 360]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-005",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "MTU",
      "F1K": "✅[1588, 9600]",
      "F2K": "✅[1588, 9600]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-006",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "IPG参数配置",
      "F1K": "✅[True, False]",
      "F2K": "✅[True, False]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-007",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "速率选择",
      "F1K": "✅[100M, 1000M, 1G, 10G]",
      "F2K": "✅[100M, 1000M, 1G, 10G]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-008",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "启用配置",
      "F1K": "✅[True, False]",
      "F2K": "✅[True, False]"
    },
    {
      "uuid": "",
      "编号": "TX:001-001-009",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网物理端口管理",
      "三级特性": "基础数据免配",
      "F1K": "✅[True, False]",
      "F2K": "✅[True, False]"
    },
    {
      "uuid": "",
      "编号": "TX:001-002-001",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网业务端口管理",
      "三级特性": "创建删除",
      "F1K": "✅",
      "F2K": "❌"
    },
    {
      "uuid": "",
      "编号": "TX:001-002-002",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网业务端口管理",
      "三级特性": "启用配置",
      "F1K": "✅",
      "F2K": "❌"
    },
    {
      "uuid": "",
      "编号": "TX:001-002-003",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网业务端口管理",
      "三级特性": "TPID",
      "F1K": "✅",
      "F2K": "❌"
    },
    {
      "uuid": "",
      "编号": "TX:001-002-004",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网业务端口管理",
      "三级特性": "封装类型",
      "F1K": "✅",
      "F2K": "❌"
    },
    {
      "uuid": "",
      "编号": "TX:001-002-005",
      "一级特性": "L2-接口管理",
      "二级特性": "以太网业务端口管理",
      "三级特性": "绑定端口",
      "F1K": "✅",
      "F2K": "❌"
    }
  ]
};

// 将JSON数据转换为表格需要的数据格式
const initialData = jsonData.summary_feature.map(item => ({
  number: item['编号'],
  level1: item['一级特性'],
  level2: item['二级特性'],
  level3: item['三级特性'],
  F1K: item['F1K'],
  F2K: item['F2K']
}));


const data = ref([...initialData]);
const bordered = ref(true);
const tableRef = ref(null);
const height = ref(500);

// const setLowerHeight = () => {
//   height.value = 150;
// };

// const setHigherHeight = () => {
//   height.value = 600;
// };
</script>
