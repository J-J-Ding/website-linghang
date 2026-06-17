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
const tableTitle = ref('EEPROM库');

// 表单字段配置
const formFields = ref([
  {
    key: '主控类型',
    label: '主控类型',
    type: 'input',
    width: 120,
    isTitle: true,
    required: true,
  },
  {
    key: '访问通道',
    label: '访问通道',
    type: 'input',
    width: 120,
    isTitle: true,
    required: true,
  },
  {
    key: '接口',
    label: '接口',
    type: 'input',
    width: 100,
  },
  {
    key: '母板eeprom个数',
    label: '母板eeprom个数',
    type: 'input',
    width: 140,
  },
  {
    key: '母板eeprom位置',
    label: '母板eeprom位置',
    type: 'input',
    width: 140,
  },
  {
    key: '母板eeprom支持备份',
    label: '母板eeprom支持备份',
    type: 'input',
    width: 160,
  },
  {
    key: '母板eeprom失效检测',
    label: '母板eeprom失效检测',
    type: 'input',
    width: 160,
  },
  {
    key: '单板eeprom1',
    label: '单板eeprom1',
    type: 'input',
    width: 120,
  },
  {
    key: '单板eeprom2',
    label: '单板eeprom2',
    type: 'input',
    width: 120,
  },
  {
    key: '背板eeprom个数',
    label: '背板eeprom个数',
    type: 'input',
    width: 140,
  },
  {
    key: '背板eeprom互斥锁',
    label: '背板eeprom互斥锁',
    type: 'input',
    width: 150,
  },
  {
    key: '主备互斥访问寄存器',
    label: '主备互斥访问寄存器',
    type: 'input',
    width: 160,
  },
  {
    key: '背板eeprom支持备份',
    label: '背板eeprom支持备份',
    type: 'input',
    width: 160,
  },
  {
    key: '背板eeprom失效检测',
    label: '背板eeprom失效检测',
    type: 'input',
    width: 160,
  },
]);

// 表单验证规则
const editRules = ref({
  '主控类型': [{ required: true, message: '请输入主控类型', type: 'error' }],
});

// API路径配置
const readApiPath = ref('/api_data/API_Table_get');
const saveApiPath = ref('/api_data/API_Table_set');
const deleteApiPath = ref('/api_data/API_Table_del');

// 默认参数
const defaultParams = ref({
  table_name: 'EEPROM库',
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