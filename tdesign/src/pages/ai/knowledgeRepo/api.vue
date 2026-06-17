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
const tableTitle = ref('命令库');

// 表单字段配置
const formFields = ref([
  {
    key: '命令类型',
    label: '命令类型',
    type: 'input',
    width: 120,
    isTitle: true,
    filterable: true,
  },
  {
    key: '命令码',
    label: '命令码',
    type: 'input',
    width: 120,
    isTitle: true,
  },
  {
    key: '命令名称',
    label: '命令名称',
    type: 'input',
    width: 160,
  },
  {
    key: '命令来源',
    label: '命令来源',
    type: 'input',
    width: 120,
    filterable: true,
  },
  {
    key: '关联特性',
    label: '关联特性',
    type: 'input',
    width: 120,
  },
  {
    key: '关联命令',
    label: '关联命令',
    type: 'input',
    width: 120,
  },
  {
    key: '关联组件',
    label: '关联组件',
    type: 'input',
    width: 120,
  },
  {
    key: '数据存储',
    label: '数据存储',
    type: 'input',
    width: 120,
  },
  {
    key: '处理流程',
    label: '处理流程',
    type: 'input',
    width: 120,
  },
  {
    key: '白盒梳理',
    label: '白盒梳理',
    type: 'link',
    width: 120,
  },
  {
    key: '处理规则',
    label: '处理规则',
    type: 'input',
    width: 120,
  },
]);

// 表单验证规则
const editRules = ref({
  命令类型: [{ required: true, message: '请输入命令类型', type: 'error' }],
  命令码: [{ required: true, message: '请输入命令码', type: 'error' }],
  命令名称: [{ required: true, message: '请输入命令名称', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: '命令库',
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
