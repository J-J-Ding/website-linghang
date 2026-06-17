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
const tableTitle = ref('FT用例库');

// 表单字段配置 - 对应后端FT用例库数据库字段
const formFields = ref([
  {
    key: '用例编号',
    label: '用例编号',
    type: 'input',
    width: 100,
    isTitle: true,
  },
  {
    key: '用例名称',
    label: '用例名称',
    type: 'input',
    width: 200,
    isTitle: true,
  },
  {
    key: '用例描述',
    label: '用例描述',
    type: 'textarea',
    width: 300,
  },
  {
    key: '领域',
    label: '领域',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '团队',
    label: '团队',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '组件',
    label: '组件',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '特性',
    label: '特性',
    type: 'input',
    width: 120,
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
    width: 150,
  },
  {
    key: '创建人',
    label: '创建人',
    type: 'input',
    width: 100,
  },
  {
    key: '更新时间',
    label: '更新时间',
    type: 'input',
    width: 150,
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
      '团队',
      '组件',
      '特性',
      '功能点',
      '预置条件(G)',
      '测试步骤(W)',
      '预期结果(T)',
    ],
  },
  {
    key: 'verbose',
    label: '全量信息',
    columns: [
      '用例编号',
      '用例名称',
      '用例描述',
      '领域',
      '团队',
      '组件',
      '特性',
      '功能点',
      '预置条件(G)',
      '测试步骤(W)',
      '预期结果(T)',
      '标签',
      '创建人',
      '更新时间',
    ],
  },
]);

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: 'FT用例库',
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
