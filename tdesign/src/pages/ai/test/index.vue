<template>
  <div class="test">
    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button variant="outline" theme="primary" @click="openAiChat"> 打开AI对话 </t-button>
      </t-space>

      <!-- AI对话框 -->
      <AiChat
        :visible="tableAiVisible"
        :ai-chat-title="tableAiTitle"
        :ai-chat-context="tableAiContext"
        @update:visible="tableAiVisible = $event"
      />

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
    </t-space>
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
const tableTitle = ref('SD器件表');

// 表单字段配置
const formFields = ref([
  {
    key: 'SD类型',
    label: 'SD类型',
    type: 'input',
    width: 150,
    isTitle: true,
  },
  {
    key: '厂家',
    label: '厂家',
    type: 'input',
    width: 120,
  },
  {
    key: '容量',
    label: '容量',
    type: 'input',
    width: 120,
  },
  {
    key: '材质',
    label: '材质',
    type: 'input',
    width: 120,
  },
  {
    key: '接口类型',
    label: '接口类型',
    type: 'input',
    width: 120,
  },
  {
    key: '代码',
    label: '代码',
    type: 'input',
    width: 120,
  },
  {
    key: '支持主控',
    label: '支持主控',
    type: 'input',
    width: 120,
  },
  {
    key: '总写入次数',
    label: '总写入次数',
    type: 'input',
    width: 120,
  },
  {
    key: '单block大小',
    label: '单block大小',
    type: 'input',
    width: 120,
  },
  {
    key: '理论TBW',
    label: '理论TBW',
    type: 'input',
    width: 120,
  },
  {
    key: '每日写入上限',
    label: '每日写入上限',
    type: 'input',
    width: 120,
  },
]);

// 表单验证规则
const editRules = ref({
  SD类型: [{ required: true, message: '请输入SD类型', type: 'error' }],
  厂家: [{ required: true, message: '请输入厂家', type: 'error' }],
  容量: [{ required: true, message: '请输入容量', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: 'SD器件', // 使用SD器件表
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
