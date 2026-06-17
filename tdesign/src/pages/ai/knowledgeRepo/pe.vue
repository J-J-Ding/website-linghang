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
const tableTitle = ref('PE模版库');

// 表单字段配置
const formFields = ref([
  {
    key: '主题',
    label: '主题',
    type: 'input',
    width: 200,
    isTitle: true,
  },
  {
    key: '摘要',
    label: '摘要',
    type: 'textarea',
    width: 200,
  },
  {
    key: '内容',
    label: '内容',
    type: 'textarea',
    width: 300,
  },
  {
    key: '场景',
    label: '场景',
    type: 'input',
    width: 120,
  },
  {
    key: '创建人',
    label: '创建人',
    type: 'input',
    width: 120,
  },
  {
    key: '创建时间',
    label: '创建时间',
    type: 'date',
    width: 180,
    editable: false,
  },
  {
    key: '引用次数',
    label: '引用次数',
    type: 'number',
    width: 120,
    editable: false,
  },
]);

// 表单验证规则
const editRules = ref({
  主题: [{ required: true, message: '请输入主题', type: 'error' }],
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
