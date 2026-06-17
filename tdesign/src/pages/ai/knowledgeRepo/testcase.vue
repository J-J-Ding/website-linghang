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
      :scene-config="sceneConfig"
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

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('用例库');

// 表单字段配置
const formFields = ref([
  {
    key: '用例编号',
    label: '用例编号',
    type: 'input',
    width: 120,
    isTitle: true,
  },
  {
    key: '用例名称',
    label: '用例名称',
    type: 'input',
    width: 240,
    isTitle: true,
  },
  {
    key: '领域',
    label: '领域',
    type: 'select',
    options: [
      { label: 'L0', value: 'L0' },
      { label: 'L1', value: 'L1' },
      { label: 'L2', value: 'L2' },
      { label: '支撑', value: '支撑' },
      { label: '智控', value: '智控' },
    ],
    width: 100,
    filterable: true,
  },
  {
    key: '特性',
    label: '特性',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '功能点',
    label: '功能点',
    type: 'input',
    width: 120,
    filterable: true,
  },
  {
    key: '测试点',
    label: '测试点',
    type: 'input',
    width: 120,
  },
  {
    key: '预置条件(G)',
    label: '预置条件(G)',
    type: 'textarea',
    width: 200,
  },
  {
    key: '测试步骤(W)',
    label: '测试步骤(W)',
    type: 'textarea',
    width: 200,
  },
  {
    key: '预期结果(T)',
    label: '预期结果(T)',
    type: 'textarea',
    width: 200,
  },
  {
    key: '标签',
    label: '标签',
    type: 'input',
    width: 120,
  },
  {
    key: '优先级',
    label: '优先级',
    type: 'select',
    width: 80,
    options: [
      { label: '5', value: '5' },
      { label: '4', value: '4' },
      { label: '3', value: '3' },
      { label: '2', value: '2' },
      { label: '1', value: '1' },
    ],
  },
  {
    key: '测试类型',
    label: '测试类型',
    type: 'select',
    width: 100,
    options: [
      { label: '功能测试', value: '功能测试' },
      { label: '性能测试', value: '性能测试' },
      { label: '兼容性测试', value: '兼容性测试' },
      { label: '安全测试', value: '安全测试' },
      { label: '其他', value: '其他' },
    ],
    filterable: true,
  },
  {
    key: '测试分层',
    label: '测试分层',
    type: 'select',
    width: 100,
    options: [
      { label: 'FT', value: 'FT' },
      { label: 'IT', value: 'IT' },
      { label: 'ST', value: 'ST' },
    ],
    filterable: true,
  },
  {
    key: '是否通用用例',
    label: '是否通用用例',
    type: 'select',
    width: 120,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
    filterable: true,
  },
  {
    key: '是否异常测试',
    label: '是否异常测试',
    type: 'select',
    width: 120,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
    filterable: true,
  },
  {
    key: '是否可自动化',
    label: '是否可自动化',
    type: 'select',
    width: 120,
    options: [
      { label: '是', value: '是' },
      { label: '否', value: '否' },
    ],
    filterable: true,
  },
  {
    key: '用例来源',
    label: '用例来源',
    type: 'select',
    width: 120,
    options: [
      { label: '借鉴对外测试', value: '借鉴对外测试' },
      { label: '工程/生产反向补充', value: '工程/生产反向补充' },
      { label: '故障反向补充', value: '故障反向补充' },
      { label: '根据需求方案正向设计', value: '根据需求方案正向设计' },
    ],

    filterable: true,
  },
  {
    key: '编写人',
    label: '编写人',
    type: 'input',
    width: 100,
  },
  {
    key: '维护人',
    label: '维护人',
    type: 'input',
    width: 100,
  },
  {
    key: '导入路径',
    label: '导入路径',
    type: 'input',
    width: 200,
  },
]);

// 表单验证规则
const editRules = ref({
  用例编号: [{ required: true, message: '请输入用例编号', type: 'error' }],
  用例名称: [{ required: true, message: '请输入用例名称', type: 'error' }],
});

// 场景配置
const sceneConfig = ref([
  {
    key: 'summary',
    label: '摘要信息',
    columns: [
      '用例编号',
      '用例名称',
      '领域',
      '特性',
      '功能点',
      '测试点',
      '预置条件(G)',
      '测试步骤(W)',
      '预期结果(T)',
      '测试分层',
    ],
  },
  {
    key: 'verbose',
    label: '全量信息',
    columns: [
      '用例编号',
      '用例名称',
      '领域',
      '特性',
      '功能点',
      '测试点',
      '预置条件(G)',
      '测试步骤(W)',
      '预期结果(T)',
      '标签',
      '优先级',
      '测试类型',
      '测试分层',
      '是否通用用例',
      '是否异常测试',
      '是否可自动化',
      '编写人',
      '维护人',
      '用例来源',
      '导入路径',
    ],
  },
]);

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: '用例库',
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
