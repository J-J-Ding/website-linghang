<template>
  <div class="m-table">
    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button shape="circle" variant="base" theme="primary" @click="onTableAiChat"> AI </t-button>
        <t-button @click="onTableCreate">新建</t-button>
        <t-button @click="onTableRead">刷新</t-button>
        <t-button @click="onBatchImport">批量导入</t-button>
        <t-button @click="onBatchExport">批量导出</t-button>
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
        :max-height="tableHeight"
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

    <!-- 批量导入对话框 -->
    <t-dialog v-model:visible="importDialogVisible" :width="600" theme="default" header="批量导入数据">
      <div class="import-container">
        <t-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          :max-size="10 * 1024 * 1024"
          :allow-multiple="false"
          accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          class="upload-component"
        >
          <t-button variant="outline">选择XLSX文件</t-button>
        </t-upload>

        <div v-if="fileList.length > 0" class="file-info">
          <p>已选择文件: {{ fileList[0].name }}</p>
          <p class="file-size">文件大小: {{ formatFileSize(fileList[0].size) }}</p>
        </div>

        <div v-if="uploadError" class="error-message">{{ uploadError }}</div>

        <div class="example-download">
          <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
          <t-space wrap="false" class="example-space">
            <p>请按照当前表格结构填写数据</p>
            <t-button variant="text" theme="primary" @click="downloadExampleFile" class="example-btn">
              <t-icon name="download" size="16" class="mr-1" />
              下载导入示例文件
            </t-button>
          </t-space>
        </div>
      </div>
      <template #footer>
        <t-button @click="importDialogVisible = false">取消</t-button>
        <t-button @click="handleImportSubmit" :loading="importLoading">确认导入</t-button>
      </template>
    </t-dialog>
  </div>
</template>

<script setup lang="jsx">
import * as XLSX from 'xlsx';
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { Icon, SearchIcon, ChatIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import AiChat from '@/pages/ai/chat/chat.vue';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const userStore = useUserStore();

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
const tableHeight = ref('900px');

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

// 导入相关
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// 计算属性
const filteredData = computed(() => {
  if (!searchValue.value) return data.value;

  // 将搜索值按空格分割成多个关键词，并过滤掉空字符串
  const keywords = searchValue.value
    .toLowerCase()
    .split(' ')
    .filter((keyword) => keyword.trim() !== '');

  // 如果没有有效的关键词，返回所有数据
  if (keywords.length === 0) return data.value;

  // 返回同时匹配所有关键词的记录
  return data.value.filter((item) => {
    // 将行数据的所有值连接成一个字符串用于搜索
    const rowText = Object.values(item)
      .map((value) => String(value))
      .join(' ')
      .toLowerCase();

    // 检查是否所有关键词都在行文本中
    return keywords.every((keyword) => rowText.includes(keyword));
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
  // 序号列
  const indexColumn = {
    colKey: 'index',
    title: '序号',
    width: 60,
    cell: (h, { rowIndex }) => {
      return rowIndex + 1;
    },
  };

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

  return [indexColumn, ...fieldColumns, aiColumn, actionColumn];
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
      // 根据新的参数格式构造请求数据
      // 先创建一个不包含id字段的副本
      const { id, ...conditionsWithoutId } = { ...currentEditRow.value };

      // 从Pinia store中获取当前用户信息
      const currentUser = userStore.userInfo.name || 'guest';

      const requestData = {
        user: currentUser,
        table_name: props.defaultParams.table_name, // 使用table_name作为tale_name
        conditions: conditionsWithoutId,
      };

      // 添加默认参数到conditions
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
    // 传递完整的行数据作为conditions，但排除前端添加的id字段，让后端根据表配置确定主键字段
    // 同时添加user参数

    // 从Pinia store中获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    // 排除前端用于唯一标识的id字段，只传递原始数据字段
    const { id, ...conditionsWithoutId } = { ...row };

    const requestData = {
      user: currentUser,
      table_name: props.defaultParams.table_name,
      conditions: conditionsWithoutId,
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
    // 同时添加user参数

    // 从Pinia store中获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    const requestData = {
      user: currentUser,
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

// 批量导入相关方法
const onBatchImport = () => {
  // 重置状态
  fileList.value = [];
  uploadError.value = '';
  importDialogVisible.value = true;
};

// 处理文件选择变化
const handleFileChange = (files) => {
  uploadError.value = '';
  fileList.value = files;

  // 验证文件格式
  if (files.length > 0) {
    const file = files[0];
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.xlsx')) {
      uploadError.value = '文件格式错误，请选择.xlsx格式的文件';
      fileList.value = []; // 清空错误文件
    }
  }
};

const handleImportSubmit = async () => {
  if (fileList.value.length === 0) {
    uploadError.value = '请先选择文件';
    return;
  }

  if (uploadError.value) {
    return;
  }

  importLoading.value = true;
  uploadError.value = '';

  try {
    const file = fileList.value[0];

    // 读取Excel文件
    const reader = new FileReader();
    const data = await new Promise((resolve, reject) => {
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsArrayBuffer(file.raw);
    });

    // 解析Excel文件
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheetName];

    // 转换为JSON
    const jsonData = XLSX.utils.sheet_to_json(worksheet);

    if (!jsonData || jsonData.length === 0) {
      throw new Error('Excel文件中没有数据');
    }

    // 验证数据结构是否与表单字段匹配
    const expectedHeaders = props.formFields.map((field) => field.label);
    const actualHeaders = Object.keys(jsonData[0]);

    // 检查是否所有Excel列都在表单字段中存在
    const missingHeaders = expectedHeaders.filter((header) => !actualHeaders.includes(header));
    if (missingHeaders.length > 0) {
      throw new Error(`Excel文件缺少以下列: ${missingHeaders.join(', ')}`);
    }

    // 获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    // 逐行处理数据并保存到后端
    let successCount = 0;
    let failCount = 0;

    for (const row of jsonData) {
      try {
        // 将Excel列名转换为字段键名
        const rowData = {};
        props.formFields.forEach((field) => {
          // 查找Excel中匹配的列名
          const excelColumn = Object.keys(row).find((key) => key === field.label);
          if (excelColumn) {
            // 如果是选择类型字段，尝试将标签转换为值
            if (field.type === 'select' && field.options) {
              const option = field.options.find((opt) => opt.label === row[excelColumn]);
              rowData[field.key] = option ? option.value : row[excelColumn];
            } else {
              rowData[field.key] = row[excelColumn];
            }
          }
        });

        // 从Pinia store中获取当前用户信息
        const currentUser = userStore.userInfo.name || 'guest';

        const requestData = {
          user: currentUser,
          table_name: props.defaultParams.table_name,
          conditions: rowData,
        };

        // 添加默认参数到conditions
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

        successCount++;
      } catch (error) {
        console.error('保存单行数据失败:', error);
        failCount++;
      }
    }

    MessagePlugin.success(`批量导入完成: 成功 ${successCount} 条, 失败 ${failCount} 条`);

    await onTableRead(); // 重新加载数据

    importDialogVisible.value = false;
  } catch (error) {
    console.error('批量导入失败', error);
    uploadError.value = error.message || '批量导入失败';
  }

  importLoading.value = false;
};

// 批量导出功能
const onBatchExport = async () => {
  // 判断是否有数据可导出
  if (data.value.length === 0) {
    MessagePlugin.warning('当前没有数据可导出');
    return;
  }

  try {
    // 根据表单字段配置生成导出数据
    const exportData = data.value.map((row) => {
      const exportRow = {};
      props.formFields.forEach((field) => {
        // 根据字段类型和配置处理数据
        if (field.type === 'select' && field.options) {
          // 如果是选择框类型，获取对应的标签而不是值
          const option = field.options.find((opt) => opt.value === row[field.key]);
          exportRow[field.label] = option ? option.label : row[field.key] || '';
        } else {
          // 对于其他类型，直接使用值
          exportRow[field.label] = row[field.key] || '';
        }
      });
      return exportRow;
    });

    // 创建工作簿和工作表
    const worksheet = XLSX.utils.json_to_sheet(exportData);

    // 动态调整列宽（根据内容长度估算）
    const columnWidths = [];
    const firstRow = exportData[0];
    if (firstRow) {
      Object.keys(firstRow).forEach((key) => {
        // 计算列标题的长度
        const headerWidth = key.length;
        // 计算数据中最长值的长度
        const maxWidth = Math.max(headerWidth, ...exportData.map((row) => (row[key] ? String(row[key]).length : 0)));
        // 设置适当的最大宽度，避免过宽
        columnWidths.push({ wch: Math.min(maxWidth + 2, 50) });
      });
    }
    worksheet['!cols'] = columnWidths;

    // 创建工作簿并添加工作表
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, props.tableTitle || '数据导出');

    // 生成文件名（使用表格标题和日期时间）
    const date = new Date();
    const formattedDate =
      `${date.getFullYear().toString().slice(2)}` +
      `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
      `${date.getDate().toString().padStart(2, '0')}` +
      `${date.getHours().toString().padStart(2, '0')}` +
      `${date.getMinutes().toString().padStart(2, '0')}`;
    const fileName = `${props.tableTitle || '数据'}批量导出_${formattedDate}.xlsx`;

    // 导出文件
    XLSX.writeFile(workbook, fileName);

    // 显示成功信息
    MessagePlugin.success('数据导出成功, 请查看下载文件');
  } catch (error) {
    console.error('数据导出失败:', error);
    MessagePlugin.error('数据导出失败，请重试');
  }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 下载示例文件
const downloadExampleFile = () => {
  try {
    // 创建一个示例数据，使用当前表单字段作为列
    const exampleData = [{}];
    props.formFields.forEach((field) => {
      exampleData[0][field.label] = `[${field.label}示例值]`;
    });

    // 创建工作簿和工作表
    const worksheet = XLSX.utils.json_to_sheet(exampleData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '示例');

    // 导出示例文件
    const fileName = `${props.tableTitle || '数据'}导入示例.xlsx`;
    XLSX.writeFile(workbook, fileName);

    MessagePlugin.success('示例文件下载成功');
  } catch (error) {
    console.error('示例文件生成失败:', error);
    MessagePlugin.error('示例文件生成失败');
  }
};

watch(
  () => props.tableConfig,
  () => {
    // 配置变化时可以重新加载数据
  },
  { deep: true },
);

// 监听窗口大小变化
const handleResize = () => {
  tableHeight.value = pubCalculateTableHeight();
};

onMounted(async () => {
  tableHeight.value = pubCalculateTableHeight();
  window.addEventListener('resize', handleResize);
  onTableRead();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
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

/* 编辑表单和导入导出样式 */
.m-table :deep(*) {
  .edit-form .t-form__item {
    margin-bottom: 20px;
  }

  .import-container {
    padding: 16px 0;
  }

  .upload-component {
    margin-bottom: 20px;
  }

  .file-info {
    padding: 12px;
    background-color: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 16px;
  }

  .error-message {
    color: #ff4d4f;
    padding: 8px 0;
    min-height: 24px;
  }

  /* 导入相关样式补充 */
  /* 示例文件说明与下载按钮的容器样式 */
  .example-download {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px dashed #e5e6eb;
  }

  .example-space {
    display: flex; /* 水平布局 */
    align-items: center; /* 垂直居中对齐 */
    gap: 12px; /* 元素间间距，可根据需要调整 */
  }

  .example-space p {
    margin: 0; /* 清除默认外边距 */
    color: #666; /* 可选：调整文字颜色 */
    font-size: 14px; /* 与按钮文字大小保持一致 */
  }

  .example-btn {
    font-size: 14px; /* 与说明文字大小统一 */
    padding-left: 0;
    display: inline-flex;
    align-items: center;
  }

  .mr-1 {
    margin-right: 4px;
  }

  .file-size {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
  }
}
</style>
