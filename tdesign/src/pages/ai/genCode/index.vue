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
import AiChat from '@/pages/ai/genCode/chat.vue';
import AiTable from '@/pages/ai/genCode/tablepro.vue';

defineOptions({ name: 'AiGenCode' });

// AI对话相关
const tableAiVisible = ref(false);
const tableAiTitle = ref('这是我要传给子组件的标题');
const tableAiContext = ref('{"主题":"这是我要传给子组件的上下文"}');

const openAiChat = () => {
  tableAiVisible.value = true;
};

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('任务库表');


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
    width: 200,
    editable: false,
  },
  {
    key: '描述',
    label: '描述',
    type: 'html',
    width: 400,
    editable: false,
  },
  {
    key: '状态',
    label: '状态',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '指派给',
    label: '指派给',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
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
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '迭代',
    label: '迭代',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  }
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
  table_name: '任务库',
});

// 场景配置
const sceneConfig = ref([
  {
    key: 'tracking',
    label: '任务未关闭',
    columns: ['标识', '标题', '描述', '状态', '指派给', '领域', '团队', '迭代', '智能体'],
    filters: {
      状态: ['Active', 'New'],
    },
  },
  {
    key: 'viewing',
    label: '任务全集',
    columns: ['标识', '标题', '描述', '状态', '指派给', '领域', '团队', '迭代','智能体'],
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
