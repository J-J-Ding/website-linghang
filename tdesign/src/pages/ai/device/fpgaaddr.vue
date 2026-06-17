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
const tableTitle = ref('FPGA地址库');

// 表单字段配置
const formFields = ref([
  {
    key: '板类型',
    label: '板类型',
    type: 'input',
    width: 180,
    isTitle: true,
    required: true,
    filterable: true,
  },
  {
    key: 'BOM ID',
    label: 'BOMID',
    type: 'input',
    width: 120,
  },
  {
    key: '基地址名称',
    label: '基地址名称',
    type: 'input',
    width: 150,
    isTitle: true,
    required: true,
    filterable: true,
  },
  {
    key: 'FPGA ID',
    label: 'FPGAID',
    type: 'input',
    width: 120,
  },
  {
    key: '基地址',
    label: '基地址',
    type: 'input',
    width: 180,
  },
]);

// 表单验证规则
const editRules = ref({
  板类型: [{ required: true, message: '请输入板类型', type: 'error' }],
  基地址名称: [{ required: true, message: '请输入基地址名称', type: 'error' }],
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
