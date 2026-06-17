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
const tableTitle = ref('分支漏合库');


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
    key: '提交链接',
    label: '提交链接',
    type: 'input',
    width: 160,
    editable: false,
  },
  {
    key: '首次合入时间',
    label: '首次合入时间',
    type: 'data',
    width: 100,
    editable: false,
    filterable: true,
  },
  {
    key: '提交人',
    label: '提交人',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '所属部门',
    label: '所属部门',
    type: 'input',
    width: 100,
    editable: false,
    filterable: true,
  },
  {
    key: '所属团队',
    label: '所属团队',
    type: 'input',
    width: 120,
    editable: false,
    filterable: true,
  },
  {
    key: '实际合入分支',
    label: '实际合入分支',
    type: 'input',
    width: 140,
    editable: false,
  },
  {
    key: '应波及分支',
    label: '应波及分支',
    type: 'input',
    width: 120,
    editable: false,
  },
  {
    key: '遗漏分支',
    label: '遗漏分支',
    type: 'input',
    width: 120,
    editable: false,
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
  table_name: '分支漏合库',
});

// 场景配置
const sceneConfig = ref([
  {
    key: 'tracking',
    label: '增量遗漏问题',
    columns: [ "标识", "提交链接", "首次合入时间", "提交人", "所属部门", "所属团队", "实际合入分支", "应波及分支", "遗漏分支"],
    filters: {
      是否增量: ['是'],
    },
  },
  {
    key: 'viewing',
    label: '全量遗漏问题',
    columns: [ "标识", "提交链接", "首次合入时间", "提交人", "所属部门", "所属团队", "实际合入分支", "应波及分支", "遗漏分支"],
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
