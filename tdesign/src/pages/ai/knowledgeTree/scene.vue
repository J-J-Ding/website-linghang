<template>
  <div class="scene-main">
    <t-space direction="vertical">
      <t-space>
        <t-button @click="onTableRead">读取</t-button>
        <t-button @click="onTableWrite">写入</t-button>
        <t-select v-model="field" :options="fieldOptions" placeholder="请选择领域" clearable> </t-select>
        <t-select v-model="scene" :options="sceneOptions" placeholder="请选择场景" clearable> </t-select>
        <!-- <t-button @click="setLowerHeight">lower height</t-button> -->
        <!-- <t-button @click="setHigherHeight">higher height</t-button> -->
      </t-space>

      <t-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="data"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="850"
        @row-edit="onRowEdit"
      />
    </t-space>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, onMounted, watch } from 'vue';
import { Input, Select, DatePicker, MessagePlugin } from 'tdesign-vue-next';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

const columns = [
  { colKey: 'id', title: '编号', width: '80', edit: { component: Input, showEditIcon: false } },
  { colKey: 'scene', title: '场景', width: '180', edit: { component: Input, showEditIcon: false } },
  { colKey: 'l3svc', title: '业务类型', width: '180', edit: { component: Input, showEditIcon: false } },
  { colKey: 'l2svc', title: '承载类型', edit: { component: Input, showEditIcon: false } },
  { colKey: 'l1svc', title: '管道类型', edit: { component: Input, showEditIcon: false } },
  { colKey: 'uniprotect', title: '客户侧保护', edit: { component: Input, showEditIcon: false } },
  { colKey: 'nnil2protect', title: '网络侧业务保护', edit: { component: Input, showEditIcon: false } },
  { colKey: 'nnil1protect', title: '网络侧管道保护', edit: { component: Input, showEditIcon: false } },
  { colKey: 'qos', title: 'QoS', edit: { component: Input, showEditIcon: false } },
  { colKey: 'oam', title: 'OAM', edit: { component: Input, showEditIcon: false } },
  { colKey: 'domain', title: '跨域', edit: { component: Input, showEditIcon: false } },

  {
    colKey: 'edit',
    title: '操作',
    width: '120',
    cell: (h, { row }) => {
      const editable = editableRowKeys.value.includes(row.id);
      return (
        <div class="table-operations">
          {!editable && (
            <t-link theme="primary" hover="color" data-id={row.id} onClick={onEdit}>
              编辑
            </t-link>
          )}
          {editable && (
            <t-link theme="primary" hover="color" data-id={row.id} onClick={onSave}>
              保存
            </t-link>
          )}
          {editable && (
            <t-link theme="primary" hover="color" data-id={row.id} onClick={onCancel}>
              取消
            </t-link>
          )}
        </div>
      );
    },
  },
];

const data = ref();
const tableRef = ref();
const editableRowKeys = ref([]);
const currentSaveId = ref('');
const editMap = {};
const field = ref('L2');
const fieldOptions = [
  { label: 'L0领域', value: 'L0' },
  { label: 'L1领域', value: 'L1' },
  { label: 'L2领域', value: 'L2' },
  { label: '支撑领域', value: 'OSP' },
  { label: '智控领域', value: 'WASON' },
];

const scene = ref('');
const sceneOptions = ref([]);

// 更新 editableRowKeys
const updateEditState = (id) => {
  const index = editableRowKeys.value.findIndex((t) => t === id);
  editableRowKeys.value.splice(index, 1);
};

const onEdit = (e) => {
  console.log(e);
  console.log('onEdit!');
  const { id } = e.currentTarget.dataset;
  console.log(id);
  console.log(editableRowKeys.value.includes(id));
  if (!editableRowKeys.value.includes(id)) {
    editableRowKeys.value.push(id);
  }
};

const onCancel = (e) => {
  console.log('onCancel!');
  const { id } = e.currentTarget.dataset;
  updateEditState(id);
  tableRef.value.clearValidateData();
};

const onSave = (e) => {
  const { id } = e.currentTarget.dataset;
  currentSaveId.value = id;

  // 直接更新数据，不进行校验
  const current = editMap[currentSaveId.value];
  if (current) {
    data.value.splice(current.rowIndex, 1, current.editedRow);
    MessagePlugin.success('保存成功');
  }
  updateEditState(currentSaveId.value);
};

const onRowEdit = (params) => {
  console.log('onRowEdit');
  const { row, col, value } = params;
  const oldRowData = editMap[row.id]?.editedRow || row;
  const editedRow = { ...oldRowData, [col.colKey]: value };
  editMap[row.id] = {
    ...params,
    editedRow,
  };
};

/**
 * 读取表格数据的函数
 * @returns {Promise<Array>} 返回解析后的表格数据
 * @throws {Error} 当请求失败、数据格式不正确或处理过程中出现错误时抛出异常
 */
const onTableRead = async () => {
  console.log('开始读取数据...');

  // 定义默认错误消息
  const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络请求失败，请检查网络连接',
    TIMEOUT_ERROR: '请求超时，请稍后重试',
    SERVER_ERROR: '服务器返回错误',
    INVALID_JSON: '返回的数据不是有效的JSON格式',
    INVALID_DATA_FORMAT: '返回的数据格式不正确，预期是数组',
    UNKNOWN_ERROR: '发生未知错误',
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

  try {
    // 1. 发起请求
    let response;
    try {
      response = await fetch(`${SERVER_API_URL}/api_data/Table_read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table: 'Scene',
          domain: field.value,
        }),
        signal: controller.signal,
      });
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('请求超时:', error);
        MessagePlugin.error(ERROR_MESSAGES.TIMEOUT_ERROR);
        throw new Error(ERROR_MESSAGES.TIMEOUT_ERROR);
      }
      console.error('网络请求失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.NETWORK_ERROR);
      throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
    }

    // 2. 检查响应状态
    if (!response.ok) {
      const errorMsg = `HTTP错误! 状态码: ${response.status}`;
      console.error(errorMsg);
      MessagePlugin.error(ERROR_MESSAGES.SERVER_ERROR);
      throw new Error(errorMsg);
    }

    // 3. 解析响应数据
    let responseData;
    try {
      responseData = await response.json();
    } catch (error) {
      console.error('解析响应JSON失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
      throw new Error(ERROR_MESSAGES.INVALID_JSON);
    }

    // 4. 检查响应数据状态
    if (responseData.status !== 'success') {
      const errorMsg = responseData.message || '读取表格失败';
      console.error('服务器返回错误:', errorMsg);
      MessagePlugin.error(errorMsg);
      throw new Error(errorMsg);
    }

    console.log('数据读取成功，开始处理数据...');

    // 5. 处理表格数据
    let tableData = responseData.tableData;

    // 如果是字符串，尝试解析为JSON
    if (typeof tableData === 'string') {
      try {
        tableData = JSON.parse(tableData);
      } catch (error) {
        console.error('解析表格数据JSON失败:', error);
        MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
        throw new Error(ERROR_MESSAGES.INVALID_JSON);
      }
    }

    // 确保数据是数组
    if (!Array.isArray(tableData)) {
      console.error('表格数据格式不正确:', tableData);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
      throw new Error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
    }

    // 6. 更新应用状态
    try {
      // 映射数据到表格显示格式
      data.value = tableData.map((item) => ({
        id: item['编号']?.toString() || '',
        scene: item['场景']?.toString() || '',
        l3svc: item['业务类型']?.toString() || '',
        l2svc: item['承载类型']?.toString() || '',
        l1svc: item['管道类型']?.toString() || '',
        uniprotect: item['客户侧保护']?.toString() || '',
        nnil2protect: item['网络侧业务保护']?.toString() || '',
        nnil1protect: item['网络侧管道保护']?.toString() || '',
        qos: item['QoS']?.toString() || '',
        oam: item['OAM']?.toString() || '',
        domain: item['跨域']?.toString() || '',
      }));
      console.log(tableData);
      MessagePlugin.success('数据加载成功');
      console.log('数据处理完成，成功加载数据');
      return tableData;
    } catch (error) {
      console.error('数据处理过程中出错:', error);
      MessagePlugin.error('数据处理失败');
      throw new Error('数据处理失败');
    }
  } catch (error) {
    console.error('数据读取和处理过程中出错:', error);
    // 如果错误还没有被处理过，显示通用错误消息
    if (!error.message || Object.values(ERROR_MESSAGES).indexOf(error.message) === -1) {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
      throw new Error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    throw error; // 重新抛出已处理的错误
  } finally {
    clearTimeout(timeoutId); // 清除超时定时器
  }
};

// 写入表格数据
const onTableWrite = async () => {
  console.log('Write data to backend');
};

const onMenuRead = async () => {
  console.log('Menu read!');

  try {
    // 使用 query 参数传递 domain 值
    const response = await axios.get(`${SERVER_API_URL}/api_data/Menu_read`, {
      params: {
        domain: 'L2', // 可根据需要动态设置
      },
    });

    console.log(response.data.menuData);

    // 将字符串数组转换为 { label: '', value: '' } 数组
    sceneOptions.value = response.data.menuData.map((item) => ({
      label: item,
      value: item,
    }));
  } catch (error) {
    console.error('接收失败:', error);
  }
};

onMounted(() => {
  onTableRead();
  onMenuRead();
});

// 监听 field 变化，自动读取数据
watch(field, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    onTableRead();
  }
});
</script>

<style>
.table-operations .t-link {
  margin-right: 8px;
}

.scene-main {
  /* 基础表格样式 */
  table {
    /* max-width: 100%; */
    border-collapse: collapse;
    /* border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      margin-top: 1em;
      margin-bottom: 1em; */
    white-space: pre-line;
  }

  /* 表头样式 */
  th {
    background-color: #e7e7e7;
    color: #333;
    white-space: nowrap; /* 防止表头换行 */
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    border-left: none;
    border-right: none;
    line-height: 1.4; /* 紧凑行高 */
  }

  /* 单元格样式 */
  td {
    background-color: #fefefe;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4;
    border-left: none;
    border-right: none;
  }

  /* 奇偶行颜色区分 */
  tr:nth-child(even) td {
    background-color: #f8f8f8;
  }

  /* 悬停效果 */
  tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
  }

  /* 响应式优化 */
  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }
}
</style>
