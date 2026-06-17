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
const tableTitle = ref('CPU库');

// 表单字段配置
const formFields = ref([
  {
    key: '子卡型号',
    label: '子卡型号',
    type: 'input',
    width: 120,
    isTitle: true,
    required: true,
  },
  {
    key: '子卡ID',
    label: '子卡ID',
    type: 'input',
    width: 100,
  },
  {
    key: 'CPU架构',
    label: 'CPU架构',
    type: 'input',
    width: 100,
  },
  {
    key: 'DRAM容量',
    label: 'DRAM容量',
    type: 'input',
    width: 100,
  },
  {
    key: '支持主控',
    label: '支持主控',
    type: 'input',
    width: 120,
  },
]);

// 表单验证规则
const editRules = ref({
  子卡型号: [{ required: true, message: '请输入子卡型号', type: 'error' }],
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
