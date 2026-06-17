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

/*
表配置：
{
  // 表格基本配置
  bordered: true,           // 是否显示边框
  striped: true,            // 是否显示斑马纹
  hover: true,              // 是否开启鼠标悬停效果
  loading: false,           // 是否显示加载状态
  size: 'medium',           // 表格尺寸 'small' | 'medium' | 'large'
  tableLayout: 'fixed',     // 表格布局 'fixed' | 'auto'
  verticalAlign: 'middle',  // 垂直对齐方式
  // 更多表格配置...
}

行配置：
[
  {
    key: '字段名',           // 字段标识符，对应数据中的属性名
    label: '字段标签',       // 显示的标题文本
    type: 'input',          // 字段类型: 'input', 'select', 'textarea', 'html', 'link', 'number' 等
    width: 120,             // 列宽度
    isTitle: false,         // 是否为关键字段(标题字段)，影响列的固定显示
    editable: true,         // 是否可编辑(默认true)
    defaultValue: '',       // 新建记录时的默认值
    filterable: false,      // 是否可筛选
    filterType: 'single',   // 筛选类型: 'single' | 'multiple' (默认'multiple')
    options: [],            // 选择类型字段的选项列表
    aiTableFilter: false,   // 是否在AI表格上下文中过滤掉此字段
    sort: false,            // 是否使用此字段进行排序
  },
]
*/

// 表格配置
const tableConfig = ref({});
const tableTitle = ref('硬件检查库');

// 表单字段配置
const formFields = ref([
  {
    key: '器件类型',
    label: '器件类型',
    type: 'input',
    width: 100,
    filterable: true,
    editable: true, // 可编辑
    isTitle: true,
  },
  {
    key: '功能大类',
    label: '功能大类',
    type: 'input',
    width: 100,
    filterable: true,
    editable: true, // 可编辑
    isTitle: true,
  },
  {
    key: '功能细分',
    label: '功能细分',
    type: 'input',
    width: 100,
    filterable: true,
    editable: true, // 可编辑
    isTitle: true,
  },
  {
    key: '功能细分内容',
    label: '功能细分内容',
    type: 'textarea',
    width: 600,
  },
]);

// 表单验证规则
const editRules = ref({
  器件类型: [{ required: true, message: '器件类型必填', type: 'error' }],
  功能大类: [{ required: true, message: '功能大类必填', type: 'error' }],
  功能细分: [{ required: true, message: '功能细分必填', type: 'error' }],
});

// 场景配置
const sceneConfig = ref([]);

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
