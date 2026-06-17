<template>
  <div class="chat-box">
    <t-drawer v-model:visible="promptDrawVisible" :footer="false" header="提示词模版" size="330px">
      <t-space direction="vertical" style="width: 100%">
        <t-space style="width: 100%">
          <t-button theme="primary">
            <template #icon><add-icon /></template>
            新建
          </t-button>
          <t-input placeholder="Search Input" clearable>
            <template #suffixIcon>
              <search-icon :style="{ cursor: 'pointer' }" @search="search" />
            </template>
          </t-input>
        </t-space>
        <t-space direction="vertical" style="width: 100%">
          <!-- 插入列表形式的t-card -->
          <div v-for="(template, index) in templates" :key="index">
            <t-tooltip placement="left" theme="light" :show-arrow="false">
              <template #content>
                <div style="white-space: pre-line">
                  <strong>{{ template.title }}</strong
                  ><br />
                  <span style="color: #616161">{{ template.subtitle }}</span
                  ><br />
                  {{ template.content }}
                </div>
              </template>
              <t-card class="card-main" :title="template.title" :bordered="false" hover-shadow>
                <div class="card-content">
                  {{ template.subtitle }}
                </div>
                <template #actions>
                  <a
                    href="javascript:void(0)"
                    @click="() => templateReference(template)"
                    style="text-decoration: none; color: #409eff; font-size: 14px"
                    >引用</a
                  >
                </template>
              </t-card>
            </t-tooltip>
          </div>
        </t-space>
      </t-space>
    </t-drawer>

    <t-drawer v-model:visible="historyChatDrawVisible" placement="right" :footer="false" :z-index="4999">
      <template #header>历史会话</template>

      <div class="history-list">
        <div
          v-for="record in recentUserMessages"
          :key="record.session_id"
          class="history-item"
          @click="handleSessionClick(record.session_id)"
        >
          <div class="history-content">{{ record.origin }}</div>
          <div class="history-time">{{ record.timestamp }}</div>
        </div>
      </div>
    </t-drawer>

    <t-tooltip content="新建对话" placement="top">
      <t-button class="new-chat" size="large" theme="primary" shape="circle" variant="base" @click="newChat">
        <icon name="plus" />
      </t-button>
    </t-tooltip>
    <t-tooltip content="历史对话" placement="top">
      <t-button class="history-chat" size="large" theme="primary" shape="circle" variant="base" @click="historyChat">
        <icon name="history" />
      </t-button>
    </t-tooltip>
    <t-tooltip content="提示词模版" placement="top">
      <t-button class="prompt" size="large" theme="primary" shape="circle" variant="base" @click="promptTemplate">
        <icon name="chat-bubble-error" />
      </t-button>
    </t-tooltip>

    <!-- 清空历史记录配置 -->
    <!-- :clear-history="chatList.length > 0 && !isStreamLoad" -->

    <t-chat ref="chatRef" layout="both" :clear-history="false" @scroll="handleChatScroll" @clear="clearConfirm">
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
          <!-- 操作按钮直接放在 t-chat-item 内部 -->
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
          :stop-disabled="isStreamLoad"
          :textarea-props="{
            placeholder: '请输入消息...',
            autosize: { minRows: 2, maxRows: 12 },
          }"
          @stop="onStop"
          @send="inputEnter"
          @file-select="fileSelect"
        >
          <template #prefix>
            <div class="model-select">
              <t-select v-model="selectModelValue" :options="selectModel" value-type="object"></t-select>
              <t-select v-model="selectAgentValue" :options="selectAgent" value-type="object"></t-select>
              <t-select v-model="selectknowledgeValue" :options="selectknowledge" value-type="object"></t-select>
              <!-- <t-button class="check-box" :class="{ 'is-active': isChecked }" variant="text" @click="checkClick">
                  <SystemSumIcon />
                  <span>深度思考</span>
                </t-button> -->
              <t-button
                class="check-box"
                :class="{ 'is-active': isCheckedIcenter }"
                variant="text"
                @click="checkClickIcenter"
              >
                <icon name="file-code-1" />
                <span>引用Icenter</span>
              </t-button>
              <t-button class="check-box" :class="{ 'is-active': isCheckedRdc }" variant="text" @click="checkClickRdc">
                <icon name="file-code" />
                <span>引用RDC</span>
              </t-button>
            </div>
          </template>
        </t-chat-sender>
      </template>
    </t-chat>

    <t-button v-show="isShowToBottom" variant="text" class="bottomBtn" @click="backBottom">
      <div class="to-bottom">
        <ArrowDownIcon />
      </div>
    </t-button>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';

import { ref, onMounted, computed, nextTick } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import {
  ArrowDownIcon,
  SystemSumIcon,
  LettersTIcon,
  CheckCircleIcon,
  Icon,
  SearchIcon,
  AddIcon,
} from 'tdesign-icons-vue-next';
import { v4 as uuidv4 } from 'uuid';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const user = useUserStore();

const fetchCancel = ref(null);
const loading = ref(false);
// 流式数据加载中
const isStreamLoad = ref(false);

const chatRef = ref(null);
const isShowToBottom = ref(false);
// 滚动到底部
const backBottom = () => {
  chatRef.value.scrollToBottom({
    behavior: 'smooth',
  });
};
const selectModel = [
  {
    label: '星云大模型',
    value: 'nebula',
  },
  {
    label: '通义千问-中兴',
    value: 'qwen3-zte',
  },
  // {
  //   label: '通义千问-阿里',
  //   value: 'qwen',
  // },
  // {
  //   label: 'Qwen3-coder',
  //   value: 'qwen3-coder',
  // },
  // {
  //   label: 'Deepseek-V3',
  //   value: 'deepseek-V3',
  // },
  // {
  //   label: 'Kimi-K2',
  //   value: 'kimi-K2',
  // },
];
const selectModelValue = ref({
  label: '星云大模型',
  value: 'nebula',
});

const selectAgent = [
  {
    label: '✔️问答模式',
    value: 'chat',
  },
  {
    label: '✔️批量任务智能体',
    value: 'DoTaskListAgent',
  },
  {
    label: '✔️故障分析智能体',
    value: 'BugAnalysisAgent',
  },
  {
    label: '✔️故障检索智能体',
    value: 'BugDiagAgent',
  },
  // {
  //   label: '✔️L2MVP智能体',
  //   value: 'L2MvpAgent',
  // },
  {
    label: '✔️深度研究智能体',
    value: 'DeepResearchAgent',
  },
  // {
  //   label: '✔️BA智能体',
  //   value: 'BaAgent',
  // },
  // {
  //   label: '✔️组件智能体',
  //   value: 'Coder',
  // },
  {
    label: '✔️空间搜索智能体',
    value: 'iCenterSearchAgent',
  },
  // {
  //   label: '✔️DN通用智能体',
  //   value: 'DNstdioBasicAgent',
  // },
  {
    label: '✔️DN光层仿真单板模型生成',
    value: 'DNstdioFzAgent',
  },
  {
    label: '✔️DN光层仿真Modeldata生成',
    value: 'DNstdioMdAgent',
  },
  {
    label: '✔️详设评审智能体',
    value: 'TlCheckAgent',
  },
  {
    label: '✔️内容域测评智能体',
    value: 'DNstdioCntEvalAgent',
  },
  // {
  //   label: '波及分析智能体',
  //   value: 'ModifyAnalysisAgent',
  // },
  // {
  //   label: '故障横推智能体',
  //   value: 'BugShareAgent',
  // },
  // {
  //   label: '接口文档智能体',
  //   value: 'ApiAgent',
  // },
  // {
  //   label: '自定义智能体',
  //   value: 'CustomerAgent',
  // },
];
const selectAgentValue = ref({
  label: '智能体',
  value: 'chat',
});

const selectknowledge = [
  {
    label: '✔️无知识库',
    value: 'NoneKnowledge',
  },
  {
    label: '✔️编码规范知识库',
    value: 'CodingStandards',
  },
  {
    label: '✔️星载编码规范知识库',
    value: 'CodingStandardsNasa',
  },
  {
    label: '✔️典型编码故障知识库',
    value: 'CodingBugCases',
  },
  {
    label: '接口文档知识库',
    value: 'ApiKnowledge',
  },
  {
    label: '故障定位知识库',
    value: 'BugReviewKnowledge',
  },
  {
    label: '场景树知识库',
    value: 'SceneKnowledge',
  },
  {
    label: '特性树知识库',
    value: 'FeatureKnowledge',
  },
  {
    label: '单板树知识库',
    value: 'BoardKnowledge',
  },
  {
    label: '组件树知识库',
    value: 'ModuleKnowledge',
  },
  {
    label: '器件树知识库',
    value: 'DeviceKnowledge',
  },
];
const selectknowledgeValue = ref({
  label: '未引用知识库',
  value: 'NoneKnowledge',
});

const allowToolTip = ref(false);

const isChecked = ref(false);
const checkClick = () => {
  isChecked.value = !isChecked.value;
};

const isCheckedIcenter = ref(true);
const checkClickIcenter = () => {
  isCheckedIcenter.value = !isCheckedIcenter.value;
};

const isCheckedRdc = ref(true);
const checkClickRdc = () => {
  isCheckedRdc.value = !isCheckedRdc.value;
};

const handleOperation = function (type, options) {
  console.log('handleOperation', type, options);
};

const handleChange = (value, { index }) => {
  console.log('handleChange', value, index);
};
/**
 * 渲染推理模块的头部自定义内容
 * @param {boolean} flag - 思维链内容是否加载中
 * @param {string} endText - 思维链加载完成时显示的文本
 * @returns {JSX.Element} 返回对应的头部组件
 */
const renderHeader = (flag, item) => {
  if (flag) {
    return <t-chat-loading text="思考中..." />;
  }
  const endText = item.duration ? `已深度思考(用时${item.duration}秒)` : '已深度思考';
  return (
    <div style="display:flex;align-items:center">
      <CheckCircleIcon
        style={{
          color: 'var(--td-success-color-5)',
          fontSize: '20px',
          marginRight: '8px',
        }}
      />
      <span>{endText}</span>
    </div>
  );
};
const renderReasoningContent = (reasoningContent) => <t-chat-content content={reasoningContent} role="assistant" />;
// 倒序渲染
const chatList = ref([]);
const clearConfirm = function () {
  chatList.value = [];
};
// 是否显示回到底部按钮
const handleChatScroll = function ({ e }) {
  const scrollTop = e.target.scrollTop;
  isShowToBottom.value = scrollTop < 0;
};

const inputEnter = function (inputValue) {
  if (isStreamLoad.value) {
    return;
  }

  if (!inputValue) return;
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

// 为每个聊天单独制定一个唯一id，防止同时提问时冲突
let session_id = uuidv4();
let fileContent = null;

const newChat = () => {
  session_id = uuidv4(); // 重置聊天id
  chatList.value = []; // 清空聊天列表
  MessagePlugin.info('创建对话成功');
};

const historyChatDrawVisible = ref(false);
const historyChat = () => {
  historyChatDrawVisible.value = true;
  HistoryGet(); // 获取聊天记录
};

const promptDrawVisible = ref(false);
const promptTemplate = () => {
  promptDrawVisible.value = true;
  TemplatesGet(); // 获取模板数据
};

const recentUserMessages = computed(() => {
  const sessions = {};

  // 遍历聊天记录
  historyChatRecord.value.forEach((record) => {
    if (record.role === 'user') {
      // 如果是用户消息
      if (
        !sessions[record.session_id] ||
        new Date(record.timestamp) > new Date(sessions[record.session_id].timestamp)
      ) {
        sessions[record.session_id] = record;
      }
    }
  });

  // 转成数组并按时间倒序排列（最新的在最上面）
  return Object.values(sessions).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
});

const handleSessionClick = async (session_id) => {
  // 1. 只筛选 user 和 assistant 的记录
  const sessionRecords = historyChatRecord.value
    .filter((record) => record.session_id === session_id && (record.role === 'user' || record.role === 'assistant'))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  if (!sessionRecords.length) {
    MessagePlugin.warning('该会话没有聊天记录');
    return;
  }

  // 2. 构建复制内容
  let clipboardText = '';

  sessionRecords.forEach((record) => {
    const roleLabel = record.role === 'user' ? `${user.userInfo.name}` : 'AI';
    const time = record.timestamp;

    clipboardText += `${time} ${roleLabel}：\n${record.origin}\n\n`;
  });

  // 3. 使用 Clipboard API 复制到剪贴板
  try {
    // Fallback for older browsers or insecure contexts
    if (!navigator.clipboard) {
      // Create a temporary textarea element
      const textarea = document.createElement('textarea');
      textarea.value = clipboardText.trim();
      textarea.style.position = 'fixed'; // Prevent scrolling to bottom
      document.body.appendChild(textarea);
      textarea.select();

      try {
        const successful = document.execCommand('copy');
        if (successful) {
          MessagePlugin.success('会话记录已复制到剪贴板');
        } else {
          throw new Error('Copy command failed');
        }
      } catch (err) {
        MessagePlugin.error('无法复制到剪贴板，请手动复制');
      } finally {
        document.body.removeChild(textarea);
      }
    } else {
      await navigator.clipboard.writeText(clipboardText.trim());
      MessagePlugin.success('会话记录已复制到剪贴板');
    }
  } catch (err) {
    MessagePlugin.error('复制到剪贴板失败');
  }
};

const search = () => {
  console.log('search');
};

const onStop = function () {
  if (fetchCancel.value) {
    fetchCancel.value.controller.close();
    loading.value = false;
    isStreamLoad.value = false;
  }
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
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 30秒超时

    const response = await fetch(`${SERVER_API_URL}/api_chat/Chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Name': user.userInfo.name,
        Authorization: `Bearer ${user.uacToken}`,
      },
      body: JSON.stringify({
        user: user.userInfo.name,
        session_id: session_id,
        model: selectModelValue.value.value,
        agent: selectAgentValue.value.value,
        knowledge: selectknowledgeValue.value.value,
        icenter: isCheckedIcenter.value,
        rdc: isCheckedRdc.value,
        think: isChecked.value,
        content: inputValue,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const data = await response.json();

    if (data.status === 'success') {
      // 构建包含认证信息的查询参数
      const params = new URLSearchParams({
        user: encodeURIComponent(user.userInfo.name),
        user_token: encodeURIComponent(user.uacToken),
        session_id: encodeURIComponent(session_id),
      });

      eventSource = new EventSource(`${SERVER_API_URL}/api_chat/Sse?${params.toString()}`);

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
              setTimeout(flushBuffer, 0);
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

// 假设这是你的模板数据源
const templates = ref(null);

const TemplatesGet = async () => {
  try {
    const res = await axios.get(`${SERVER_API_URL}/api_chat/Template`);

    if (res.data.status === 'success') {
      templates.value = res.data.templates; // ✅ 只取 templates 数组
    } else {
      error.value = '获取模板失败，请稍后再试。';
    }
  } catch (err) {
    console.error('请求失败:', err);
    error.value = '无法加载模板数据，请稍后再试。';
  } finally {
    console.log('请求 Template 成功');
  }
};

const historyChatRecord = ref([]); // 用于保存聊天记录
const HistoryGet = async () => {
  try {
    const res = await axios.get(`${SERVER_API_URL}/api_chat/History`, {
      params: {
        user: user.userInfo.name,
      },
    });

    if (res.data.status === 'success') {
      historyChatRecord.value = res.data.chat_records;
      // console.log('获取到的聊天记录:', res.data.chat_records);
    } else {
      error.value = '获取聊天记录失败，请稍后再试。';
    }
  } catch (err) {
    console.error('请求失败:', err);
    error.value = '无法加载聊天记录，请稍后再试。';
  } finally {
    console.log('请求 History 成功');
  }
};

// 检查用户登录状态的函数
const checkAuth = async () => {
  // 如果store中没有用户信息，尝试从本地存储或其他地方获取
  if (!user.userInfo || !user.userInfo.name) {
    try {
      // 这里假设你的user store有方法来刷新用户信息
      await user.refreshUserInfo();

      // 如果刷新后仍然没有用户信息，则跳转到登录页
      if (!user.userInfo || !user.userInfo.name) {
        router.push('/login');
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      router.push('/login');
    }
  }
};

// 在onMounted中添加检查
onMounted(async () => {
  await checkAuth(); // 先检查登录状态
});
const inputText = ref('');

const templateReference = async (template) => {
  if (inputText.value.trim()) {
    inputText.value += '\n' + template.content;
  } else {
    inputText.value += template.content;
  }
  // 等待 DOM 更新后再聚焦
  await nextTick();
  const textareaEl = document.querySelector('.t-textarea__inner');
  if (textareaEl) {
    textareaEl.focus();
  }
};

const fileSelect = (data) => {
  const files = data.files;

  if (!files || files.length === 0) {
    alert('未选择文件');
    return;
  }

  // 支持的文本文件扩展名（小写）- 作为初步筛选和用户提示
  const allowedExtensions = [
    '.txt',
    '.json',
    '.js',
    '.jsx',
    '.ts',
    '.tsx',
    '.css',
    '.scss',
    '.less',
    '.html',
    '.htm',
    '.py',
    '.java',
    '.cpp',
    '.c',
    '.h',
    '.hpp',
    '.cs',
    '.php',
    '.rb',
    '.go',
    '.swift',
    '.md',
    '.markdown',
    '.xml',
    '.csv',
    '.log',
    '.config',
    '.yml',
    '.yaml',
    '.ini',
  ];

  // 支持的 MIME 类型前缀 - 用于检查浏览器提供的类型
  const allowedMimeTypes = [
    'text/', // 通用文本
    'application/json',
    'application/xml',
    'text/markdown', // 明确的 markdown MIME
    // 注意：像 .js, .css 等可能被报告为 text/javascript, text/css, text/plain 等，用 'text/' 覆盖
  ];

  // 最大文件大小：10MB
  const MAX_SIZE = 10 * 1024 * 1024; // 10MB in bytes

  const file = files[0];
  const fileName = file.name;
  const fileExtension = '.' + fileName.toLowerCase().split('.').pop();
  const fileSize = file.size;
  const mimeType = file.type.toLowerCase(); // 浏览器推测的 MIME 类型

  // 1. 检查文件大小
  if (fileSize > MAX_SIZE) {
    alert(`文件 "${fileName}" 超过 10MB 限制，无法上传。`);
    console.warn(`文件过大: ${fileName}, ${fileSize} bytes`);
    return;
  }

  // 2. 检查扩展名（初步筛选和友好提示）
  const hasAllowedExtension = allowedExtensions.includes(fileExtension);
  if (!hasAllowedExtension) {
    alert(`文件 "${fileName}" 类型不支持。只允许上传文本类文件（如 .txt, .json, .js, .py, .md 等）`);
    console.warn(`不支持的文件扩展名: ${fileName}`);
    return;
  }

  // 3. 检查 MIME 类型 (更可靠的前端类型指示)
  const hasAllowedMimeType = allowedMimeTypes.some(
    (type) => mimeType === type || (type.endsWith('/') && mimeType.startsWith(type)),
  );
  if (!hasAllowedMimeType) {
    // MIME 类型不匹配，但扩展名匹配，可能是浏览器无法识别或错误。进行内容检查。
    console.log(`文件 "${fileName}" 的 MIME 类型 '${mimeType}' 不在明确允许列表中，将进行内容检查...`);
  }
  // 注意：我们不在此处直接返回失败，因为 mimeType 可能不准确（如某些 .md 文件可能是 text/plain）

  // 4. 关键：检查文件内容是否为可读文本 (最可靠的判断)
  // 创建一个 Promise 来执行内容检查
  const checkTextContent = new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = function (e) {
      const buffer = e.target.result;
      const uint8Array = new Uint8Array(buffer);

      // 尝试将前1024字节解码为UTF-8
      let decoder = new TextDecoder('utf-8', { fatal: false }); // fatal: false 表示解码错误时不抛出异常
      let text;
      try {
        text = decoder.decode(uint8Array);
      } catch (decodeError) {
        resolve(false); // 解码失败，很可能不是文本
        return;
      }

      // 检查文本中是否包含过多的非打印字符（启发式判断二进制文件）
      let nonPrintableCount = 0;
      const checkLength = Math.min(1000, text.length); // 检查前1000字符或文件长度
      for (let i = 0; i < checkLength; i++) {
        const code = text.charCodeAt(i);
        // 可打印ASCII: 32-126, 允许的控制符: \t(9), \n(10), \r(13)
        if ((code < 32 && ![9, 10, 13].includes(code)) || code === 127) {
          nonPrintableCount++;
        }
      }

      const ratio = checkLength > 0 ? nonPrintableCount / checkLength : 1;
      // 如果非打印字符比例过高（例如 > 15%），则认为是二进制文件
      const isLikelyText = ratio < 0.15;
      resolve(isLikelyText);
    };
    reader.onerror = () => reject(new Error('文件读取失败'));
    // 只读取文件开头一小部分进行检查
    reader.readAsArrayBuffer(file.slice(0, 1024));
  });

  // 5. 执行内容检查并根据结果决定是否继续
  checkTextContent
    .then((isText) => {
      if (!isText) {
        alert(`文件 "${fileName}" 的内容检查表明它可能不是有效的文本文件，无法上传。`);
        console.warn(`文件内容检查失败 (非文本): ${fileName}`);
        return;
      }

      // ✅ 所有检查通过！现在可以安全地读取整个文件内容了
      console.log(`文件 "${fileName}" 通过类型和内容检查，开始读取...`);

      const contentReader = new FileReader();
      contentReader.onload = function (e) {
        fileContent = e.target.result;
        console.log('文件内容读取成功');

        // 显示内容到页面
        displayFileContent(file.name);
      };

      contentReader.onerror = function () {
        console.error(`文件 "${fileName}" 读取失败`);
        alert(`文件 "${fileName}" 读取失败，请重试。`);
      };

      // 以文本方式读取整个文件
      contentReader.readAsText(file);
    })
    .catch((error) => {
      console.error(`检查文件 "${fileName}" 时发生错误:`, error);
      alert(`检查文件时发生错误，请重试。`);
    });
};

// 将文件名显示在前端页面上
function displayFileContent(fileName) {
  const params = {
    avatar: '/src/assets/assets-user3.png',
    // name: 'You：',
    datetime: new Date().toLocaleString(),
    content: `文件 "${fileName}" 已上传。`,
    role: 'user',
  };
  chatList.value.unshift(params);
}
</script>

<style lang="less">
/* 应用滚动条样式 */
::-webkit-scrollbar-thumb {
  background-color: var(--td-scrollbar-color);
  // display: none;
}
::-webkit-scrollbar-thumb:horizontal:hover {
  background-color: var(--td-scrollbar-hover-color);
  // display: none;
}
::-webkit-scrollbar-track {
  // background-color: var(--td-scroll-track-color);
  background-color: transparent;
}

.t-chat__detail {
  max-width: 98% !important;
}

.t-chat__inner.user {
  margin-right: 10px;

  .t-chat__text {
    background-color: #e6e6e6 !important;
    /* 添加阴影 */
    // box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2); /* 轻柔阴影 */
    // border-radius: 8px; /* 可选：圆角更现代 */
    // padding: 10px 15px; /* 可选：增加内边距让内容不贴边 */
    // transition: box-shadow 0.3s ease; /* 平滑过渡 */
  }
}

.t-chat__text {
  // background-color: #eff6ff !important;
  background-color: transparent !important;
  font-size: 14px;
  line-height: 1.6;

  /* 添加阴影 */
  // box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2); /* 轻柔阴影 */
  // border-radius: 8px; /* 可选：圆角更现代 */
  // padding: 10px 15px; /* 可选：增加内边距让内容不贴边 */
  // transition: box-shadow 0.3s ease; /* 平滑过渡 */
}

// .t-chat__text p {
//   margin-bottom: 1em; /* 段落底部间距 */
// }

.t-chat__actions-margin * {
  background-color: transparent !important;
  border: none !important; /* 无边框 */
}

.chat-box {
  position: relative;
  height: 84vh;
  // background-color: yellow;

  /* 基础表格样式 */
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
  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }

  /* 代码块样式 */
  .hljs {
    font-size: 14px;
    line-height: 1.5; /* 紧凑行高 */
  }

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
    border: 1px solid #f0f0f0;
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

  .new-chat {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 0px; /* 距离页面顶部的距离为0 */
    left: 0px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      // 浅层阴影
      0px 16px 32px rgba(0, 0, 0, 0.2),
      // 中层主阴影（更明显）
      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
  }

  .history-chat {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 0px; /* 距离页面顶部的距离为0 */
    left: 60px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      // 浅层阴影
      0px 16px 32px rgba(0, 0, 0, 0.2),
      // 中层主阴影（更明显）
      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
  }

  .prompt {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 0px; /* 距离页面顶部的距离为0 */
    left: 120px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      // 浅层阴影
      0px 16px 32px rgba(0, 0, 0, 0.2),
      // 中层主阴影（更明显）
      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
  }
}

.model-select {
  display: flex;
  align-items: center;
  .t-select {
    width: 140px;
    height: var(--td-comp-size-m);
    margin-right: var(--td-comp-margin-s);
    .t-input {
      border-radius: 32px;
      padding: 0 15px;
    }
    .t-input.t-is-focused {
      box-shadow: none;
    }
  }
  .check-box {
    width: 140px;
    height: var(--td-comp-size-m);
    border-radius: 32px;
    border: 0;
    background: var(--td-bg-color-component);
    color: var(--td-text-color-primary);
    box-sizing: border-box;
    flex: 0 0 auto;
    .t-button__text {
      display: flex;
      align-items: center;
      justify-content: center;
      span {
        margin-left: var(--td-comp-margin-xs);
      }
    }
  }
  .check-box.is-active {
    border: 1px solid var(--td-brand-color-focus);
    background: var(--td-brand-color-light);
    color: var(--td-text-color-brand);
  }
}

.history-item {
  padding: 0.5rem;
  border-bottom: 1px solid #e4e4e4;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.history-item:hover {
  background-color: #f5f5f5;
}

.history-content {
  font-size: 14px;
  color: #333333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.history-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.card-main {
  width: 100%;
  background-color: #eff6ff;
  // borderRadius: 8px;
  // height: 130px;           // 固定最大高度
  // // display: flex;
  // // flexDirection: column;
  // overflow: hidden;
  // position: relative;
}

.card-content {
  flex: 1;
  font-size: 14px;
  color: #333;

  /* 多行文本截断 */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
}

.t-card__title {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  line-clamp: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.t-card__subtitle {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  line-clamp: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.t-card__header {
  padding-top: 5px;
  padding-bottom: 0px;
}

.t-card__body {
  padding-top: 0px;
  padding-top: 5px;
}

.t-card__actions {
  display: flex;
  align-items: flex-start; /* 向上对齐 */
}
</style>
