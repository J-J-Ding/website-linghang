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
      :support-create="true"
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
import AiTable from '@/pages/ai/chat/tablepro.vue';

// AI对话相关
const tableAiVisible = ref(false);

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('单板库');

// 表单字段配置
const formFields = ref([
  {
    key: 'board_id',
    label: '单板编号',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: 'board_name',
    label: '单板名称',
    type: 'input',
    width: 120,
    isTitle: true,
    editable: true, // 主键字段在新增时可编辑
    required: true,
  },
  {
    key: '单板类型',
    label: '单板类型',
    type: 'input',
    width: 120,
    editable: true,
    filterable: true,
  },
  {
    key: 'domain',
    label: '领域',
    type: 'input',
    width: 100,
    editable: true,
    filterable: true,
  },
  {
    key: '产品',
    label: '产品',
    type: 'input',
    width: 100,
    editable: true,
    filterable: true,
  },
  {
    key: '子架',
    label: '子架',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '主控',
    label: '主控',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '子卡',
    label: '子卡',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '交换芯片',
    label: '交换芯片',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: '面板端口',
    label: '面板端口',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: '转发能力',
    label: '转发能力',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: '软件平台',
    label: '软件平台',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: '交叉方式',
    label: '交叉方式',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: 'update_time',
    label: '更新时间',
    type: 'input',
    width: 150,
    editable: false, // 更新时间由后端自动管理
    sort: true,
  },
  {
    key: 'update_user',
    label: '更新人',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'PHY芯片',
    label: 'PHY芯片',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '时钟芯片',
    label: '时钟芯片',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '内存',
    label: '内存',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'SDSSD',
    label: 'SDSSD',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'FPGA',
    label: 'FPGA',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'CPLD',
    label: 'CPLD',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'FLASH',
    label: 'FLASH',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: '子架EEPROM',
    label: '子架EEPROM',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: '母板EEPROM',
    label: '母板EEPROM',
    type: 'input',
    width: 120,
    editable: true,
  },
  {
    key: 'boardid',
    label: 'Board ID',
    type: 'input',
    width: 100,
    editable: true,
  },
  {
    key: 'functionid',
    label: 'Function ID',
    type: 'input',
    width: 100,
    editable: true,
  },
]);

// 表单验证规则
const editRules = ref({
  board_name: [{ required: true, message: '请输入单板名称', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: '单板库',
});

// 场景配置
const sceneConfig = ref([
  {
    key: 'all_info',
    label: '完整信息',
    columns: [
      'board_name',
      'board_id',
      '单板类型',
      '产品',
      '子架',
      '主控',
      '子卡',
      '交换芯片',
      '面板端口',
      '转发能力',
      '软件平台',
      '交叉方式',
      'domain',
      'update_time',
      'update_user',
      'PHY芯片',
      '时钟芯片',
      '内存',
      'SDSSD',
      'FPGA',
      'CPLD',
      'FLASH',
      '子架EEPROM',
      '母板EEPROM',
      'boardid',
      'functionid',
    ],
  },
  {
    key: 'basic_info',
    label: '基本信息',
    columns: ['board_name', 'board_id', '单板类型', '产品', 'domain', '主控', '子卡'],
  },
  {
    key: 'hardware_details',
    label: '硬件详情',
    columns: ['board_name', '交换芯片', 'PHY芯片', '时钟芯片', '内存', 'FPGA', 'CPLD', 'FLASH'],
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
