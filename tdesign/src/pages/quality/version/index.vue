<template>
  <div class="qualityversion-main">
    <t-space direction="vertical">
      <t-space>
        <t-button shape="circle" variant="base" theme="primary" @click="drawVisible = true"> AI </t-button>
        <t-button @click="onTableRead">读取</t-button>
        <t-button @click="onTableWrite">写入</t-button>
      </t-space>

      <t-drawer
        class="component-drawer"
        v-model:visible="drawVisible"
        size="1000px"
        :footer="false"
        :close-btn="true"
        :size-draggable="true"
      >
        <t-tooltip content="新建对话" placement="top-left">
          <t-button
            class="component-new-chat"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="newChat"
          >
            <icon name="plus" />
          </t-button>
        </t-tooltip>
        <template #header>
          <span class="title">
            Hi,&nbsp;我是
            <span style="color: #1a16fc; font-weight: 600">
              {{ componentSelect || '' }}
            </span>
            AI智能体
          </span>
        </template>
        <div class="component-chat-box">
          <t-chat ref="chatRef" layout="both" :clear-history="false" @scroll="handleChatScroll">
            <template v-for="(item, index) in chatList" :key="index">
              <t-chat-item
                :variant="item.role === 'user' ? 'base' : 'base'"
                :avatar="item.avatar"
                :name="item.name"
                :role="item.role"
                :datetime="item.datetime"
                :text-loading="index === 0 && loading"
                :content="item.content"
              >
                <template #actions>
                  <t-chat-action
                    :content="item.content"
                    :operation-btn="['good', 'bad', 'replay', 'copy']"
                    @operation="handleOperation"
                  />
                </template>
              </t-chat-item>
            </template>
            <template #footer>
              <t-chat-sender
                v-model="inputText"
                :stop-disabled="loading"
                :textarea-props="{ placeholder: '请输入消息...' }"
                @send="inputEnter"
              >
              </t-chat-sender>
            </template>
          </t-chat>
          <t-button v-show="isShowToBottom" variant="text" class="bottomBtn" @click="backBottom">
            <div class="to-bottom">
              <ArrowDownIcon />
            </div>
          </t-button>
        </div>
      </t-drawer>

      <t-table
        ref="tableRef"
        row-key="version"
        bordered
        lazy-load
        :columns="columns"
        :data="data"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="750"
        @row-edit="onRowEdit"
      />
    </t-space>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, onMounted, watch, nextTick } from 'vue';
import { Input, Select, DatePicker, MessagePlugin } from 'tdesign-vue-next';
import { SystemSumIcon, Icon, ArrowDownIcon } from 'tdesign-icons-vue-next';
import { useUserStore } from '@/store';
import { v4 as uuidv4 } from 'uuid';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

const drawVisible = ref(false);

const columns = [
  {
    colKey: 'index',
    title: '序号',
    width: '60',
    cell: (h, { rowIndex }) => rowIndex + 1,
  },
  {
    colKey: 'version',
    title: '版本',
    width: '180',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'version'),
  },
  {
    colKey: 'product',
    title: '产品项目',
    width: '180',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'product'),
  },
  {
    colKey: 'time',
    title: '发布时间',
    width: '180',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'time'),
  },
  {
    colKey: 'branch',
    title: '分支信息',
    width: '180',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'branch'),
  },
  {
    colKey: 'plan',
    title: '版本计划',
    width: '180',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'plan'),
  },
  {
    colKey: 'feature',
    title: '功能范围',
    width: '300',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'feature'),
  },
  {
    colKey: 'board',
    title: '单板范围',
    width: '300',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'board'),
  },
  {
    colKey: 'versionSupport',
    title: '版本重保',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'versionSupport'),
  },
  {
    colKey: 'upgradeSupport',
    title: '升级重保',
    ellipsis: true,
    cell: (h, { row }) => renderCell(h, row, 'upgradeSupport'),
  },
];

const renderCell = (h, row, colKey) => {
  const content = row[colKey] || '';
  return (
    <t-tooltip content={content} placement="top" showArrow theme="light" destroyOnClose>
      <div class="cell-content" style="width: 100%; overflow: hidden; text-overflow: ellipsis;">
        {content}
      </div>
    </t-tooltip>
  );
};

const data = ref();
const tableRef = ref();
const editableRowKeys = ref([]);
const currentSaveId = ref('');
const editMap = {};
const field = ref('L2');
const fieldOptions = [
  { label: '全部', value: 'all' },
  { label: 'L0领域', value: 'L0' },
  { label: 'L1领域', value: 'L1' },
  { label: 'L2领域', value: 'L2' },
  { label: '支撑领域', value: 'OSP' },
  { label: '智控领域', value: 'WASON' },
];

const component = ref('');
const componentOption = ref([]);
const componentSelect = ref('');

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
          table: 'Quality',
          domain: 'version',
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
        version: item['版本']?.toString() || '',
        product: item['产品项目']?.toString() || '',
        time: item['发布时间']?.toString() || '',
        branch: item['分支信息']?.toString() || '',
        plan: item['版本计划']?.toString() || '',
        feature: item['功能范围']?.toString() || '',
        board: item['单板范围']?.toString() || '',
        versionSupport: item['版本重保']?.toString() || '',
        upgradeSupport: item['升级重保']?.toString() || '',
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
        table: 'Component',
        domain: 'L2',
      },
    });

    console.log(response.data.menuData);

    // 将字符串数组转换为 { label: '', value: '' } 数组
    componentOption.value = response.data.menuData.map((item) => ({
      label: item,
      value: item,
    }));
  } catch (error) {
    console.error('接收失败:', error);
  }
};

// 模块：AI对话
const fetchCancel = ref(null);
const isStreamLoad = ref(false);
const inputText = ref('');
const loading = ref(false);
const chatRef = ref(null);
const chatList = ref([]);
const user = useUserStore();
let session_id = uuidv4();

const onStop = function () {
  if (fetchCancel.value) {
    fetchCancel.value.controller.close();
    loading.value = false;
    isStreamLoad.value = false;
  }
};

const newChat = () => {
  session_id = uuidv4(); // 重置聊天id
  chatList.value = []; // 清空聊天列表
  MessagePlugin.info('创建对话成功');
};

const handleOperation = function (type, options) {
  console.log('handleOperation', type, options);
};

const isShowToBottom = ref(false);
const backBottom = () => {
  chatRef.value.scrollToBottom({
    behavior: 'smooth',
  });
};

const handleChatScroll = function ({ e }) {
  const scrollTop = e.target.scrollTop;
  isShowToBottom.value = scrollTop < 0;
};

const inputEnter = function (inputValue) {
  if (isStreamLoad.value) {
    return;
  }

  if (!inputValue) {
    return;
  }

  const params = {
    avatar: '/src/assets/assets-user3.png',
    // name: 'You：',
    datetime: new Date().toLocaleString(),
    content: inputValue,
    role: 'user',
  };

  chatList.value.unshift(params);

  // 空消息占位
  const params2 = {
    avatar: '/src/assets/assets-ai2.png',
    // name: 'AI：',
    // datetime: new Date().toLocaleString(),
    content: '',
    reasoning: '',
    role: 'assistant',
  };

  chatList.value.unshift(params2);

  handleData(inputValue);
  inputText.value = ''; // 清空输入框
};

const handleData = async (inputValue) => {
  loading.value = true;
  isStreamLoad.value = true;

  const request_id = uuidv4();
  const lastItem = chatList.value[0];

  let buffer = '';
  let isFlushing = false;
  let eventSource = null; // 用于在外部访问EventSource

  function flushBuffer() {
    if (buffer && lastItem) {
      lastItem.content += buffer;
      buffer = '';
    }
    isFlushing = false;
  }

  try {
    // 增加fetch超时处理
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

    const response = await fetch(`${SERVER_API_URL}/api_chat/Chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: user.userInfo.name,
        session_id: session_id,
        model: 'nebula',
        agent: 'ComponentAgent',
        icenter: true,
        rdc: true,
        think: false,
        content: inputValue,
        component: componentSelect.value,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const data = await response.json();

    if (data.status === 'success') {
      eventSource = new EventSource(`${SERVER_API_URL}/api_chat/Sse?session_id=${encodeURIComponent(session_id)}`);

      // 统一的清理函数
      const cleanUp = () => {
        loading.value = false;
        isStreamLoad.value = false;

        if (eventSource) eventSource.close();

        nextTick().then(() => {
          const textareaEl = document.querySelector('.t-textarea__inner');
          if (textareaEl) textareaEl.focus();
        });
      };

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          if (buffer && lastItem) {
            lastItem.content += buffer;
            buffer = '';
          }
          cleanUp();
          return;
        }

        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            lastItem.role = 'error';
            lastItem.content = `服务器错误: ${data.error}`;
            cleanUp();
          } else if (data.text) {
            buffer += data.text;
            if (!isFlushing) {
              isFlushing = true;
              setTimeout(flushBuffer, 50);
            }
          }
        } catch (e) {
          console.error('解析SSE数据失败:', e);
          lastItem.role = 'error';
          lastItem.content = '数据解析失败';
          cleanUp();
        }
      };

      // 增加EventSource错误处理
      eventSource.onerror = (err) => {
        console.error('SSE连接错误:', err);
        lastItem.role = 'error';
        lastItem.content = '与服务器的连接已断开';
        cleanUp();
      };
    } else {
      lastItem.role = 'error';
      lastItem.content = `请求失败: ${data.message || '未知错误'}`;
    }

    lastItem.datetime = new Date().toLocaleString();
  } catch (error) {
    console.error('请求异常:', error);

    if (error.name === 'AbortError') {
      lastItem.content = '请求超时，请重试';
    } else {
      lastItem.content = `网络错误: ${error.message || '未知错误'}`;
    }

    lastItem.role = 'error';
    lastItem.datetime = new Date().toLocaleString();

    // 确保关闭可能存在的EventSource
    if (eventSource) eventSource.close();
  } finally {
    // 确保最终关闭加载状态
    loading.value = false;

    // 显示用时xx秒
    lastItem.duration = 5;
  }
};

// 模块：页面整体配置
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

.qualityversion-main {
  /* 添加以下样式 */
  .cell-content {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* 确保表格单元格有足够的空间显示Tooltip */
  .t-table td {
    position: relative;
  }

  /* Tooltip样式调整 */
  .t-tooltip__content {
    max-width: 400px;
    word-break: break-word;
    white-space: normal;
  }
  /* 基础表格样式 */
  .t-table {
    table-layout: fixed;
    width: 100%;
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
    vertical-align: top !important;
    text-overflow: ellipsis !important;
  }

  /* 悬停效果 */
  tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
    height: 40px !important;
  }

  /* 响应式优化 */
  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }

  .component-chat-box {
    display: flex;
    height: 95%;

    .bottomBtn {
      position: absolute;
      left: 50%;
      margin-left: -20px;
      bottom: 210px;
      padding: 0;
      border: 0;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      box-shadow:
        0px 8px 10px -5px rgba(0, 0, 0, 0.08),
        0px 16px 24px 2px rgba(0, 0, 0, 0.04),
        0px 6px 30px 5px rgba(0, 0, 0, 0.05);
    }

    .to-bottom {
      width: 40px;
      height: 40px;
      border: 1px solid #dcdcdc;
      box-sizing: border-box;
      background: var(--td-bg-color-container);
      border-radius: 50%;
      font-size: 24px;
      line-height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      .t-icon {
        font-size: 24px;
      }
    }

    .t-chat__detail {
      max-width: 98% !important;
    }

    .t-chat__inner.user {
      margin-right: 10px;

      .t-chat__text {
        background-color: #f5f5f5 !important;
      }
    }

    .t-chat__text {
      background-color: transparent !important;
      font-size: 14px;
      line-height: 1.6;
    }

    .t-chat__actions-margin * {
      background-color: transparent !important;
      border: none !important; /* 无边框 */
    }

    .component.new-chat {
      position: absolute;
      z-index: 9999;
      top: 0px;
      left: 0px;
      margin-left: 0px;
      box-shadow:
        0px 4px 12px rgba(0, 0, 0, 0.15),
        0px 16px 32px rgba(0, 0, 0, 0.2),
        0px 32px 48px rgba(0, 0, 0, 0.15);
    }

    table {
      max-width: 100%;
      border-collapse: collapse;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      margin-top: 1em;
      margin-bottom: 1em;
    }

    /* 表头样式 */
    th {
      background-color: #f3f3f3;
      color: #333;
      white-space: nowrap; /* 防止表头换行 */
      padding: 12px 10px; /* 降低内边距 */
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid #e0e0e0;
      line-height: 1.4; /* 紧凑行高 */
    }

    /* 单元格样式 */
    td {
      background-color: #fefefe;
      padding: 8px 10px; /* 显著降低内边距 */
      border-bottom: 1px solid #d6d6d6;
      color: #555;
      line-height: 1.4; /* 紧凑行高 */
    }

    /* 悬停效果 */
    tr:hover td {
      background-color: #dbeafe;
      transition: background-color 0.3s ease;
    }

    /* 响应式优化 */
    @media (max-width: 100%) {
      th,
      td {
        padding: 10px 8px;
        font-size: 14px;
      }
    }

    /* 代码块样式 */
    .hljs {
      max-width: 100%;
      font-size: 13px;
      line-height: 1.5; /* 紧凑行高 */
    }
  }
}
</style>
