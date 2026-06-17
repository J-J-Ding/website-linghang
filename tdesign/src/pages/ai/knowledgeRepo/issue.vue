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
      :support-create="false"
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
import AiChat from '@/pages/ai/chat/chat.vue';
import AiTable from '@/pages/ai/chat/tablepro.vue';

// AI对话相关
const tableAiVisible = ref(false);
const tableAiTitle = ref('这是我要传给子组件的标题');
const tableAiContext = ref('{"主题":"这是我要传给子组件的上下文"}');

const openAiChat = () => {
  tableAiVisible.value = true;
};

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('故障库表');

// 表单字段配置
const formFields = ref([
  {
    key: '标识',
    label: '标识',
    type: 'link',
    width: 160,
    isTitle: true,
    editable: false, // 标识字段不可编辑
  },
  {
    key: '标题',
    label: '标题',
    type: 'input',
    width: 400,
    editable: false,
  },
  {
    key: '状态',
    label: '状态',
    type: 'input',
    width: 100,
    editable: false,
    filterable: true,
  },
  {
    key: '变更大类',
    label: '变更大类',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '缺陷等级',
    label: '缺陷等级',
    type: 'input',
    width: 100,
    editable: false,
  },
  {
    key: '领域',
    label: '领域',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '团队',
    label: '团队',
    type: 'input',
    width: 140,
    editable: false,
    filterable: true,
  },
  {
    key: '描述',
    label: '描述',
    type: 'html',
    width: 120,
    editable: false,
    aiTableFilter: true, // AI上下文中过滤此字段
  },
  {
    key: '缺陷来源',
    label: '缺陷来源',
    type: 'input',
    width: 120,
    editable: false,
  },
  {
    key: '发现活动',
    label: '发现活动',
    type: 'input',
    width: 100,
    editable: false,
    filterable: true,
  },
  {
    key: '发现方法',
    label: '发现方法',
    type: 'input',
    width: 100,
    editable: false,
    filterable: true,
  },
  {
    key: '发现版本',
    label: '发现版本',
    type: 'input',
    width: 120,
    editable: false,
  },
  {
    key: '创建时间',
    label: '创建时间',
    type: 'input',
    width: 150,
    editable: false,
    sort: true,
  },
  {
    key: '关闭时间',
    label: '关闭时间',
    type: 'input',
    width: 150,
    editable: false,
  },
  {
    key: '所属产品',
    label: '所属产品',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '所属项目',
    label: '所属项目',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '引入人',
    label: '引入人',
    type: 'input',
    width: 120,
    editable: false,
  },
  {
    key: '引入人部门',
    label: '引入人部门',
    type: 'input',
    width: 150,
    editable: false,
  },
  {
    key: '发现人',
    label: '发现人',
    type: 'input',
    width: 120,
    editable: false,
  },
  {
    key: '发现人部门',
    label: '发现人部门',
    type: 'input',
    width: 150,
    editable: false,
  },
  {
    key: '进展',
    label: '进展',
    type: 'textarea',
    width: 160,
    editable: true,
  },
  {
    key: '备注',
    label: '备注',
    type: 'textarea',
    width: 160,
    editable: true,
  },
  {
    key: '计划解决日期',
    label: '计划解决日期',
    type: 'date',
    width: 160,
    editable: true,
  },
  {
    key: '自测报告链接',
    label: '自测报告链接',
    type: 'input',
    width: 160,
    editable: true,
  },
]);

// 表单验证规则
const editRules = ref({
  标题: [{ required: false, message: '请输入标题', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: '故障库',
});

// 场景配置
const sceneConfig = ref([
  {
    key: 'tracking',
    label: '故障未关闭',
    columns: [
      '标识',
      '标题',
      '状态',
      '变更大类',
      '领域',
      '团队',
      '发现活动',
      '进展',
      '备注',
      '创建时间',
      '计划解决日期',
      '自测报告链接',
    ],
    filters: {
      状态: ['待确认拒绝', '待确认重复', '待审核', '待验证', '待转需求', '拟制中', '实施中', '研究中'],
    },
  },
  {
    key: 'viewing',
    label: '故障全集',
    columns: ['标识', '标题', '描述', '状态', '团队', '创建时间'],
  },
]);

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
