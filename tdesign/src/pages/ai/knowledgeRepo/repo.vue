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
const tableTitle = ref('代码库表');

// 表单字段配置
const formFields = ref([
  {
    key: '代码库',
    label: '代码库',
    type: 'input',
    width: 200,
    isTitle: true,
  },
  {
    key: '分支',
    label: '分支',
    type: 'input',
    width: 160,
  },
  {
    key: '变更次数',
    label: '变更次数',
    type: 'input',
    width: 120,
  },
  {
    key: '新增行',
    label: '新增行',
    type: 'input',
    width: 120,
  },
  {
    key: '删除行',
    label: '删除行',
    type: 'input',
    width: 120,
  },
  {
    key: '领域',
    label: '领域',
    type: 'input',
    width: 120,
  },
  {
    key: '关联故障',
    label: '关联故障',
    type: 'input',
    width: 120,
  },
  {
    key: '关联组件',
    label: '关联组件',
    type: 'input',
    width: 120,
  },
]);

// 表单验证规则
const editRules = ref({
  代码库: [{ required: true, message: '请输入代码库', type: 'error' }],
  分支: [{ required: true, message: '请输入分支', type: 'error' }],
  变更次数: [{ required: true, message: '请输入变更次数', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: '代码库',
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
