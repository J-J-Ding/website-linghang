<template>
  <div class="test">
    <!-- 通用表格组件示例 -->
    <AiTable
      :table-config="tableConfig"
      :form-fields="formFields"
      :edit-rules="editRules"
      :read-api-path="readApiPath"
      :save-api-path="saveApiPath"
      :delete-api-path="deleteApiPath"
      :table-title="tableTitle"
      :default-params="defaultParams"
      @data-loaded="onDataLoaded"
      @row-created="onRowCreated"
      @row-updated="onRowUpdated"
      @row-deleted="onRowDeleted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import AiTable from '@/pages/ai/chat/tablepro.vue';

/*
表配置：
{
  // 表格基本配置
  bordered: true,           // 是否显示边框
  striped: true,            // 是否显示斑马纹
  hover: true,              // 是否开启鼠标悬停效果
  loading: false,           // 是否显示加载状态
  size: 'medium',           // 表格尺寸 'small' | 'medium' | 'large'
  tableLayout: 'fixed',     // 表格布局 'fixed' | 'auto'
  verticalAlign: 'middle',  // 垂直对齐方式
  // 更多表格配置...
}

行配置：
[
  {
    key: '字段名',           // 字段标识符，对应数据中的属性名
    label: '字段标签',       // 显示的标题文本
    type: 'input',          // 字段类型: 'input', 'select', 'textarea', 'html', 'link', 'number' 等
    width: 120,             // 列宽度
    isTitle: false,         // 是否为关键字段(标题字段)，影响列的固定显示
    editable: true,         // 是否可编辑(默认true)
    defaultValue: '',       // 新建记录时的默认值
    filterable: false,      // 是否可筛选
    filterType: 'single',   // 筛选类型: 'single' | 'multiple' (默认'multiple')
    options: [],            // 选择类型字段的选项列表
    aiTableFilter: false,   // 是否在AI表格上下文中过滤掉此字段
    sort: false,            // 是否使用此字段进行排序
  },
]
*/

// 表格配置
const tableConfig = ref({
  bordered: true,
  striped: true,
  hover: true,
  loading: false,
  size: 'medium',
  tableLayout: 'fixed',
  verticalAlign: 'middle',
});
const tableTitle = ref('单板温度检测库');

// 表单字段配置
const formFields = ref([
  {
    key: '单板名称',
    label: '单板名称',
    type: 'input',
    width: 150,
    isTitle: true,
    editable: true,
  },
  {
    key: '是否带有IPMC',
    label: '是否带有IPMC',
    type: 'select',
    width: 120,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
  },
  {
    key: 'FRU中的温度检测点',
    label: 'FRU中的温度检测点',
    type: 'input',
    width: 150,
  },
  {
    key: 'FRU中的温度检测点id',
    label: 'FRU中的温度检测点id',
    type: 'input',
    width: 150,
  },
  {
    key: 'FRU中的温度检测点定标温度',
    label: 'FRU中的温度检测点定标温度',
    type: 'input',
    width: 180,
  },
  {
    key: '软件是否上报检测点温度参与风扇调速',
    label: '软件是否上报检测点温度参与风扇调速',
    type: 'select',
    width: 220,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
  },
  {
    key: '软件上报温度是否有归一化处理',
    label: '软件上报温度是否有归一化处理',
    type: 'select',
    width: 180,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
  },
  {
    key: '单板是否支持关键器件超温告警上报以及告警上报条件',
    label: '单板是否支持关键器件超温告警上报以及告警上报条件',
    type: 'input',
    width: 280,
  },
  {
    key: '备注',
    label: '备注',
    type: 'textarea',
    width: 150,
  },
]);

// 表单验证规则
const editRules = ref({
  单板名称: [{ required: true, message: '请输入单板名称', type: 'error' }],
  'FRU中的温度检测点': [{ required: true, message: '请输入FRU中的温度检测点', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: tableTitle,
});

// 事件处理函数
const onDataLoaded = (data: any[]) => {
  console.log('数据加载完成:', data);
  MessagePlugin.success(`成功加载 ${data.length} 条数据`);
};

const onRowCreated = (row: any) => {
  console.log('新增行:', row);
  MessagePlugin.success('新增记录成功');
};

const onRowUpdated = (row: any) => {
  console.log('更新行:', row);
  MessagePlugin.success('更新记录成功');
};

const onRowDeleted = (row: any) => {
  console.log('删除行:', row);
  MessagePlugin.success('删除记录成功');
};
</script>
