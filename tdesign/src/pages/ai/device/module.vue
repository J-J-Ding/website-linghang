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

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('光模块库');

// 表单字段配置
const formFields = ref([
  {
    key: 'PN',
    label: 'PN',
    type: 'input',
    width: 150,
    isTitle: true,
  },
  {
    key: '模块类型',
    label: '模块类型',
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
    key: '速率Mbps',
    label: '速率(Mbps)',
    type: 'input',
    width: 120,
  },
  {
    key: '距离',
    label: '距离',
    type: 'input',
    width: 120,
  },
  {
    key: '制造厂商',
    label: '制造厂商',
    type: 'input',
    width: 120,
  },
  {
    key: '应用代码',
    label: '应用代码',
    type: 'input',
    width: 120,
  },
  {
    key: '波长类型',
    label: '波长类型',
    type: 'input',
    width: 120,
  },
  {
    key: '物料代码',
    label: '物料代码',
    type: 'input',
    width: 120,
  },
  {
    key: '支持单板',
    label: '支持单板',
    type: 'input',
    width: 150,
  },
]);

// 表单验证规则
const editRules = ref({
  PN: [{ required: true, message: '请输入PN', type: 'error' }],
  模块类型: [{ required: true, message: '请输入模块类型', type: 'error' }],
  接口类型: [{ required: true, message: '请输入接口类型', type: 'error' }],
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
