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
import AiTable from '@/pages/ai/chat/tablepro4version.vue';

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('版本库');

// 子表单字段配置
const dialogColumns = ref([
  {
    key: '标识',
    label: '标识',
    type: 'link',
    width: 160,
    isTitle: true, // 关键字段高亮
  },
  {
    key: '标题',
    label: '标题',
    type: 'input',
    width: 400,
  },
  {
    key: '状态',
    label: '状态',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '发现版本',
    label: '发现版本',
    type: 'input',
    width: 120,
    filterable: true,
  },
  {
    key: '发现活动',
    label: '发现活动',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '缺陷等级',
    label: '缺陷等级',
    type: 'input',
    width: 100,
    filterable: true,
  },
  {
    key: '领域',
    label: '领域',
    type: 'input',
    width: 120,
    filterable: true,
  },
  {
    key: '团队',
    label: '团队',
    type: 'input',
    width: 140,
    filterable: true,
  },
  {
    key: '创建时间',
    label: '创建时间',
    type: 'input',
    width: 150,
    editable: false,
    sort: true,
  },
]);

// 表单字段配置
const formFields = ref([
  {
    key: '版本',
    label: '版本',
    type: 'input',
    width: 240,
    isTitle: true, // 关键字段高亮
  },
  {
    key: '版本号',
    label: '版本号',
    type: 'input',
    width: 120,
  },
  {
    key: '目标',
    label: '目标',
    type: 'input',
    width: 160,
  },
  {
    key: '分支',
    label: '分支',
    type: 'input',
    width: 150,
  },
  {
    key: '主控',
    label: '主控/单板',
    type: 'input',
    width: 120,
  },
  {
    key: '需求情况',
    label: '需求情况',
    type: 'textarea',
    width: 200,
  },
  {
    key: '故障情况',
    label: '故障情况',
    type: 'textarea',
    width: 200,
  },
  {
    key: '关联故障',
    label: '关联故障',
    type: 'table',
    width: 150,
    tableTitle: '关联故障',
    apiPath: '/api_data/API_Table_get',
    table: '故障库',
    table_key: [{'版本号': '发现版本'}],
    dialogColumns: dialogColumns,
    displayText: '关联故障详细',
  },
  {
    key: '版本风险情况',
    label: '版本风险情况',
    type: 'textarea',
    width: 120,
  },
  {
    key: '团队风险情况',
    label: '团队风险情况',
    type: 'textarea',
    width: 120,
  },
  {
    key: '版本状态',
    label: '版本状态',
    type: 'input',
    width: 120,
  },
  {
    key: '版本发布时间',
    label: '版本发布时间',
    type: 'date',
    width: 150,
  },
  {
    key: '编译构建时间',
    label: '编译构建时间',
    type: 'date',
    width: 150,
  },
  {
    key: '主控系统类型',
    label: '主控系统类型',
    type: 'input',
    width: 120,
  },
  {
    key: '版本链接',
    label: '版本链接',
    type: 'link',
    width: 200,
  },
  {
    key: '关联故障横推通告',
    label: '关联故障横推通告',
    type: 'textarea',
    width: 200,
  },
]);

// 表单验证规则
const editRules = ref({
  版本: [{ required: true, message: '请输入版本', type: 'error' }],
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
