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
import AiTable from '@/pages/ai/generalApplication/tablepro.vue';


// 表格配置
const tableConfig = ref({});
const tableTitle = ref('AI应用库');


// 表单字段配置
const formFields = ref([
  {
    key: 'AI应用名称',
    label: 'AI应用名称',
    isTitle: true,
    type: 'input',
    width: 120,
  },
  {
    key: 'AI应用描述',
    label: 'AI应用描述',
    type: 'input',
    width: 120,
  },
  {
    key: 'AI应用场景',
    label: 'AI应用场景',
    type: 'input',
    width: 120,
  },
  {
    key: 'AI应用类型',
    label: 'AI应用类型',
    type: 'select',
    width: 120,
    options: [
      { label: '业务代码生成', value: 'BusinessCodeGen' },
      { label: 'UT生成', value: 'UTGen' },
      { label: 'FT生成', value: 'FTGen' },
      { label: '巡检工具代码生成', value: 'ZxsemCodeGen' },
      { label: 'NA', value: 'NA' },
    ]
  },
  {
    key: 'AI应用平台',
    label: 'AI应用平台',
    type: 'select',
    width: 120,
    options: [
      { label: 'DN Studio', value: 'DN' },
      { label: '个人自建', value: 'SelfBuilt' },
      { label: 'NA', value: 'NA' },
    ]
  },
  {
    key: '领域',
    label: '领域',
    type: 'select',
    width: 120,
    options: [
      { label: 'L0', value: 'L0' },
      { label: 'L1', value: 'L1' },
      { label: 'L2', value: 'L2' },
      { label: '支撑', value: 'OSP' },
      { label: '仿真', value: 'SIMU' },
      { label: '智控', value: 'WASON' },
      { label: '数据', value: 'DATA' },
    ]
  },
  {
    key: '团队',
    label: '团队',
    type: 'input',
    width: 120,
  },
  {
    key: '组件',
    label: '组件',
    type: 'input',
    width: 120,
  },
  {
    key: '是否范式',
    label: '是否范式',
    type: 'select',
    width: 120,
    options: [
      { label: '是', value: 'Yes' },
      { label: '否', value: 'No' },
    ]
  },
  {
    key: 'key',
    label: 'key',
    type: 'input',
    width: 120,
  },
  {
    key: 'appid',
    label: 'appid',
    type: 'input',
    width: 120,
  },
  {
    key: '使用指导',
    label: '使用指导',
    type: 'textarea',
    width: 120,
  },
]);

// 表单验证规则
const editRules = ref({
  AI应用名称: [{ required: true, message: '请输入AI应用名称', type: 'error' }],
  AI应用类型: [{ required: true, message: '请选择AI应用类型', type: 'error' }],
  AI应用平台: [{ required: true, message: '请选择AI应用平台', type: 'error' }],
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
