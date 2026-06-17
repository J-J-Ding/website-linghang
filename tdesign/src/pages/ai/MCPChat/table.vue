<template>
  <div class="m-table">
    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button shape="circle" variant="base" theme="primary" @click="onTableAiChat">
          <icon name="chat" />
        </t-button>
        <t-button @click="onTableCreate">新建</t-button>
        <t-button @click="onTableRead">刷新</t-button>
        <t-input v-model="searchValue" placeholder="搜索..." clearable>
          <template #suffix-icon>
            <search-icon />
          </template>
        </t-input>
      </t-space>

      <t-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="filteredData"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="650"
        table-layout="fixed"
        :loading="loading"
        style="width: 100%"
        @row-edit="onRowEdit"
      />
    </t-space>

    <!-- 编辑对话框 -->
    <t-dialog
      v-model:visible="diagVisible"
      :header="`${isCreateMode ? '新建' : '编辑'} - ${dialogTitle}`"
      :on-confirm="onSubmitEdit"
      :on-close="onCloseEdit"
      confirmBtn="保存"
      cancelBtn="取消"
      destroy-on-close
      width="650"
      placement="top"
      :top="40"
    >
      <div style="max-width: 600px; margin: 0 auto; padding: 0 20px">
        <div style="max-height: 70vh; overflow-y: auto; padding-right: 10px">
          <t-form
            class="edit-form"
            ref="editFormRef"
            label-align="right"
            :data="currentEditRow"
            :rules="editRules"
            :label-width="120"
            :status-icon="false"
          >
            <t-form-item
              v-for="field in formFields"
              :key="field.key"
              :label="field.label"
              :name="field.key"
              v-show="isCreateMode || field.editable !== false"
            >
              <t-input
                v-if="field.type === 'input'"
                v-model="currentEditRow[field.key]"
                :placeholder="`请输入${field.label}`"
                :disabled="!isCreateMode && field.editable === false"
              />
              <t-select
                v-else-if="field.type === 'select'"
                v-model="currentEditRow[field.key]"
                :options="field.options"
                :placeholder="`请选择${field.label}`"
                :disabled="!isCreateMode && field.editable === false"
              />
              <t-textarea
                v-else-if="field.type === 'textarea'"
                v-model="currentEditRow[field.key]"
                :placeholder="`请输入${field.label}`"
                :disabled="!isCreateMode && field.editable === false"
              />
              <t-input-number
                v-else-if="field.type === 'number'"
                v-model="currentEditRow[field.key]"
                :placeholder="`请输入${field.label}`"
                :disabled="!isCreateMode && field.editable === false"
              />
            </t-form-item>
          </t-form>
        </div>
      </div>
    </t-dialog>

    <!-- 全局AI实例 -->
    <AiChat
      :visible="tableAiVisible"
      :ai-chat-title="tableAiTitle"
      :ai-chat-context="tableAiContext"
      @update:visible="tableAiVisible = $event"
    />

    <!-- 行级AI实例 -->
    <AiChat
      :visible="rowAiVisible"
      :ai-chat-title="rowAiTitle"
      :ai-chat-context="rowAiContext"
      @update:visible="rowAiVisible = $event"
    />
  </div>
</template>

<script setup lang="jsx">
import { ref, computed, onMounted, watch } from 'vue';
import { Icon, SearchIcon, ChatIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import AiChat from '@/pages/ai/chat/chat.vue';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

// 对外提供的属性
const props = defineProps({
  // 表格配置
  tableConfig: {
    type: Object,
    required: true,
    default: () => ({}),
  },
  // 表单字段配置
  formFields: {
    type: Array,
    required: true,
    default: () => [],
  },
  // 表单验证规则
  editRules: {
    type: Object,
    default: () => ({}),
  },
  // 读取数据的API路径
  readApiPath: {
    type: String,
    required: true,
  },
  // 保存数据的API路径
  saveApiPath: {
    type: String,
    required: true,
  },
  // 删除数据的API路径
  deleteApiPath: {
    type: String,
    required: true,
  },
  // 表格标题（用于AI上下文）
  tableTitle: {
    type: String,
    default: '表格',
  },
  // 默认查询参数
  defaultParams: {
    type: Object,
    default: () => ({}),
  },
});

// 对外提供的事件
const emit = defineEmits(['data-loaded', 'row-created', 'row-updated', 'row-deleted']);

// 响应式数据
const data = ref([]);
const loading = ref(false);
const searchValue = ref('');
const tableRef = ref(null);

// AI相关
const tableAiVisible = ref(false);
const tableAiTitle = ref('全局');
const tableAiContext = ref('');

const rowAiVisible = ref(false);
const rowAiTitle = ref('');
const rowAiContext = ref('');

// 编辑相关
const diagVisible = ref(false);
const currentEditRow = ref(null);
const editFormRef = ref(null);
const isCreateMode = ref(false);
const editableRowKeys = ref([]);

// 计算属性
const filteredData = computed(() => {
  if (!searchValue.value) return data.value;

  const search = searchValue.value.toLowerCase();
  return data.value.filter((item) => {
    return Object.values(item).some((value) => String(value).toLowerCase().includes(search));
  });
});

// 监听搜索值变化，更新AI上下文
watch(searchValue, (newSearchValue) => {
  if (newSearchValue) {
    // 如果有搜索值，将搜索结果作为AI上下文
    tableAiContext.value = JSON.stringify(filteredData.value, null, 2);
  } else {
    // 如果没有搜索值，将所有数据作为AI上下文
    tableAiContext.value = JSON.stringify(data.value, null, 2);
  }
});

const columns = computed(() => {
  // 基础字段列
  const fieldColumns = props.formFields.map((field) => ({
    colKey: field.key,
    title: field.label,
    width: field.width || 120,
    ellipsis: true,
    ...(field.type === 'select' && field.options
      ? {
          cell: (h, { row }) => {
            const option = field.options.find((opt) => opt.value === row[field.key]);
            return option ? option.label : row[field.key] || '';
          },
        }
      : {}),
    edit: {
      component: field.type === 'select' ? 'Select' : 'Input',
      showEditIcon: false,
      props: field.type === 'select' ? { options: field.options } : {},
    },
  }));

  // AI列
  const aiColumn = {
    colKey: 'ai',
    title: '智能体',
    width: 100,
    fixed: 'right',
    cell: (h, { row }) => {
      return (
        <t-button theme="primary" size="small" onClick={() => onRowAiChat(row)}>
          AI助手
        </t-button>
      );
    },
  };

  // 操作列
  const actionColumn = {
    colKey: 'edit',
    title: '操作',
    width: 120,
    fixed: 'right',
    cell: (h, { row }) => {
      return (
        <div class="table-operations">
          <t-link theme="primary" hover="color" onClick={() => openEditModal(row)}>
            编辑
          </t-link>
          <t-popconfirm theme="danger" content="确定要删除这条记录吗？" onConfirm={() => onDeleteRow(row)}>
            <t-link theme="danger" hover="color">
              删除
            </t-link>
          </t-popconfirm>
        </div>
      );
    },
  };

  return [...fieldColumns, aiColumn, actionColumn];
});

const dialogTitle = computed(() => {
  if (!currentEditRow.value) return '';
  const titleField = props.formFields.find((field) => field.isTitle) || props.formFields[0];
  return (titleField && currentEditRow.value[titleField.key]) || '';
});

// 方法
const onTableAiChat = () => {
  tableAiTitle.value = props.tableTitle;
  // 如果有搜索结果，使用搜索结果作为上下文，否则使用所有数据
  tableAiContext.value = JSON.stringify(searchValue.value ? filteredData.value : data.value, null, 2);
  tableAiVisible.value = true;
};

const onRowAiChat = (rowData) => {
  const titleField = props.formFields.find((field) => field.isTitle) || props.formFields[0];
  const titleValue = titleField && rowData[titleField.key] ? rowData[titleField.key] : '记录';
  rowAiTitle.value = titleValue;
  rowAiContext.value = JSON.stringify(rowData, null, 2);
  rowAiVisible.value = true;
};

const openEditModal = (row) => {
  currentEditRow.value = { ...row };
  isCreateMode.value = false;
  diagVisible.value = true;
};

const onTableCreate = () => {
  // 创建一个空的新行数据对象
  const newRow = {
    id: '', // 新建时id为空
  };
  props.formFields.forEach((field) => {
    // 对于新建记录，使用字段的默认值或空字符串
    newRow[field.key] = field.defaultValue !== undefined ? field.defaultValue : '';
  });

  currentEditRow.value = newRow;
  isCreateMode.value = true;
  diagVisible.value = true;
};

const onSubmitEdit = async () => {
  try {
    const validateResult = await editFormRef.value.validate();
    if (validateResult === true) {
      loading.value = true;

      // 准备发送给后端的数据
      // 根据后端API_Table_set的期望格式构造请求数据
      // 先创建一个不包含id字段的副本
      const { id, ...conditionsWithoutId } = { ...currentEditRow.value };

      const requestData = {
        table_name: props.defaultParams.table_name,
        conditions: conditionsWithoutId,
      };

      // 添加默认参数（除了table_name）
      Object.keys(props.defaultParams).forEach((key) => {
        if (key !== 'table_name' && requestData.conditions[key] === undefined) {
          requestData.conditions[key] = props.defaultParams[key];
        }
      });

      // 调用后端API保存数据
      const response = await fetch(`${SERVER_API_URL}${props.saveApiPath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '保存数据失败');
      }

      // 根据是否有id判断是新建还是编辑
      const isNewRecord = !currentEditRow.value.id;

      if (isNewRecord) {
        // 新建记录
        const newRowData = { ...currentEditRow.value };
        newRowData.id = responseData.id || Date.now().toString(); // 如果后端没有返回id，生成一个临时id
        data.value.push(newRowData);
        MessagePlugin.success(responseData.message || '新建成功');
        emit('row-created', newRowData);
      } else {
        // 编辑记录
        const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
        if (index !== -1) {
          data.value[index] = { ...currentEditRow.value };
          MessagePlugin.success(responseData.message || '保存成功');
          emit('row-updated', data.value[index]);
        }
      }

      diagVisible.value = false;
      return true;
    }
    return false;
  } catch (error) {
    console.error('保存失败:', error);
    MessagePlugin.error(error.message || '保存失败');
    return false;
  } finally {
    loading.value = false;
  }
};

const onCloseEdit = () => {
  editFormRef.value?.reset();
  diagVisible.value = false;
};

const onDeleteRow = async (row) => {
  try {
    loading.value = true;

    // 根据后端API_Table_del的期望格式构造请求数据
    // 传递完整的行数据作为conditions，让后端根据表配置确定主键字段
    const requestData = {
      table_name: props.defaultParams.table_name,
      conditions: { ...row },
    };

    // 调用后端API删除数据
    const response = await fetch(`${SERVER_API_URL}${props.deleteApiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '删除数据失败');
    }

    // 从表格数据中移除该行
    const index = data.value.findIndex((item) => item.id === row.id);
    if (index !== -1) {
      data.value.splice(index, 1);
    }

    MessagePlugin.success(responseData.message || '删除成功');
    emit('row-deleted', row);
  } catch (error) {
    console.error('删除失败:', error);
    MessagePlugin.error(error.message || '删除失败');
  } finally {
    loading.value = false;
  }
};

const onRowEdit = (params) => {
  const { row, col, value } = params;
  const index = data.value.findIndex((item) => item.id === row.id);
  if (index !== -1) {
    // 创建一个新的对象而不是直接修改现有对象
    data.value[index] = { ...data.value[index], [col.colKey]: value };
  }
};

const onTableRead = async () => {
  try {
    loading.value = true;

    // 根据后端API_Table_get的期望格式构造请求数据
    const requestData = {
      table_name: props.defaultParams.table_name,
      ...props.defaultParams,
    };

    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}${props.readApiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '读取数据失败');
    }

    // 处理数据 - 支持 data 或 boardData 字段
    let tableData = responseData.data || responseData.boardData || [];

    if (typeof tableData === 'string') {
      try {
        tableData = JSON.parse(tableData);
      } catch (error) {
        console.error('解析数据JSON失败:', error);
        throw new Error('返回的数据格式不正确');
      }
    }

    if (!Array.isArray(tableData)) {
      throw new Error('返回的数据格式不正确，预期是数组');
    }

    data.value = tableData.map((item, index) => {
      // 使用已有的唯一标识符，如果没有则生成一个
      const id = item.id || item.board_name || item.SD类型 || index.toString();
      return {
        id,
        ...item,
      };
    });

    // 更新全局AI的上下文
    tableAiContext.value = JSON.stringify(data.value, null, 2);

    MessagePlugin.success(responseData.message || '数据加载成功');
    emit('data-loaded', data.value);
  } catch (error) {
    console.error('数据读取过程中出错:', error);
    MessagePlugin.error(error.message || '数据加载失败');
  } finally {
    loading.value = false;
  }
};

// 生命周期
onMounted(() => {
  onTableRead();
});

// 监听配置变化
watch(
  () => props.tableConfig,
  () => {
    // 配置变化时可以重新加载数据
  },
  { deep: true },
);
</script>

<style scoped>
.m-table :deep(.table-operations .t-link) {
  margin-right: 8px;
}

.m-table :deep(*) {
  th {
    background-color: #e7e7e7;
    color: #333;
    white-space: nowrap;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    border-left: none;
    border-right: none;
    line-height: 1.4;
  }

  td {
    background-color: #fefefe;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4;
    border-left: none;
    border-right: none;
  }

  tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
  }

  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }
}

/* 编辑表单样式 */
.edit-form :deep(.t-form__item) {
  margin-bottom: 20px;
}
</style>
