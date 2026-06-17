<template>
  <div class="m-chat">
    <t-drawer
      class="m-chat-drawer"
      v-model:visible="drawVisible"
      size="800px"
      :footer="false"
      :close-btn="true"
      :size-draggable="true"
    >
      <template #header>
        <span class="title">
          Hi，我是
          <span style="color: #1a16fc; font-weight: 600">{{ aiChatTitle }}</span>
          <!-- AI智能体 -->
        </span>
      </template>

      <div class="m-chat-box">
        <t-tooltip content="新建对话" placement="top">
          <t-button
            class="m-chat-new"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="handleNewChat"
          >
            <icon name="plus" />
          </t-button>
        </t-tooltip>
        <t-tooltip content="历史对话" placement="top">
          <t-button
            class="m-chat-history"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="handleHistoryChat"
          >
            <icon name="history" />
          </t-button>
        </t-tooltip>

        <t-tooltip content="常用词模版" placement="top">
          <t-button
            class="m-chat-prompt"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="handlePromptTemplate()"
          >
            <icon name="chat-bubble-error" />
          </t-button>
        </t-tooltip>

        <t-drawer v-model:visible="promptDrawVisible" :footer="false" header="常用词模版" size="330px">
          <t-space direction="vertical" style="width: 100%">
              <div class="prompt-search-container">
                <t-button theme="primary" @click="openCreatePromptDialog">
                  <template #icon><add-icon /></template>
                  新建
                </t-button>
                <t-input v-model="searchText" placeholder="搜索常用词模版..." clearable @change="handlePromptTemplate(searchText)">
                  <template #suffixIcon>
                    <search-icon :style="{ cursor: 'pointer' }" />
                  </template>
                </t-input>
              </div>
              <!-- <div class="prompt-filter-container">
                <t-button theme="default" shape="round" variant="base">全部</t-button>
                <t-button theme="default" shape="round" variant="base">我的</t-button>
                <t-button theme="default" shape="round" variant="base">当前</t-button>
                <t-button theme="default" shape="round" variant="base">热门</t-button>
              </div> -->
            <t-space direction="vertical" style="width: 100%">
              <!-- 插入列表形式的t-card -->
              <div v-for="(template, index) in filteredTemplates" :key="index">
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
                  <t-card class="m-chat-card-main" :title="template.title" :bordered="false" hover-shadow>
                    <div class="m-chat-card-content">
                      {{ template.subtitle }}
                    </div>
                    <template #actions>
                      <a
                        href="javascript:void(0)"
                        @click="() => handleTemplateReference(template)"
                        style="text-decoration: none; color: #409eff; font-size: 14px; margin-right: 10px"
                        >引用</a
                      >
                      <a
                        href="javascript:void(0)"
                        @click="() => handleTemplateEdit(template)"
                        style="text-decoration: none; color: #409eff; font-size: 14px; margin-right: 10px"
                        >修改</a
                      >
                      <t-popconfirm
                        theme="danger"
                        content="确定要删除这个常用词模板吗？"
                        @confirm="() => handleTemplateDelete(template)"
                      >
                        <a href="javascript:void(0)" style="text-decoration: none; color: #ff4d4f; font-size: 14px"
                          >删除</a
                        >
                      </t-popconfirm>
                    </template>
                    <template #footer>
                      <div style="font-size: 12px; color: #666">
                        <span>创建人: {{ template.creator_name + template.creator_id }}</span>
                        <span style="margin-left: 10px">引用次数: {{ template.reference_count || 0 }}</span>
                      </div>
                    </template>
                  </t-card>
                </t-tooltip>
              </div>
            </t-space>
          </t-space>
        </t-drawer>
        <t-drawer v-model:visible="historyChatDrawVisible" placement="right" :footer="false" :z-index="4999">
          <template #header>
            <div style="display: flex; align-items: center">
              <span>历史会话</span>
              <t-loading v-if="historyLoading" text="加载中..." size="small" style="margin-left: 10px" />
            </div>
          </template>

          <div class="history-list">
            <t-tooltip
              v-for="record in recentUserMessages"
              :key="record.session_id"
              placement="left"
              theme="light"
              :show-arrow="false"
              :style="{ width: '100%' }"
            >
              <template #content>
                <t-chat-content
                  style="
                    white-space: pre-line;
                    max-width: 400px;
                    max-height: 400px;
                    overflow-y: auto;
                    font-size: 14px;
                    line-height: 1.5;
                  "
                  :content="getHistoryTooltipContent(record.session_id)"
                />
                <!-- <div
                  style="
                    white-space: pre-line;
                    max-width: 300px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-size: 14px;
                    line-height: 1.5;
                  "
                  v-html="getHistoryTooltipContent(record.session_id)"
                ></div> -->
              </template>
              <div class="history-item" @click="handleSessionClick(record.session_id)">
                <div class="history-content">{{ record.content }}</div>
                <div class="history-time">{{ record.timestamp }}</div>
              </div>
            </t-tooltip>
          </div>
        </t-drawer>

        <t-chat ref="chatRef" layout="both" :clear-history="false" @scroll="handleChatScroll">
          <template v-for="(item, index) in chatList" :key="index">
            <t-chat-item
              :variant="item.role === 'user' ? 'base' : 'base'"
              :avatar="item.avatar"
              :name="item.name"
              :role="item.role"
              :content="item.content"
              :datetime="item.datetime"
              :text-loading="item.textLoading || false"
            >
              <template #content>
                <t-chat-reasoning
                  v-if="item.reasoning?.length > 0 || item.role === 'assistant'"
                  v-model:collapsed="collapsed"
                  expand-icon-placement="right"
                  :collapse-panel-props="{
                    header: renderHeader(index === 0 && isStreamLoad, item),
                  }"
                  @expand-change="handleChange"
                >
                  <template #header v-if="isStreamLoad">
                    <t-chat-loading :text="isMCP ? `思考中...(用时${item.duration}秒)` : `思考中...`" />
                  </template>
                  <t-chat-content :content="item.reasoning" />
                </t-chat-reasoning>
                <t-chat-content v-if="item.content.length > 0" :content="item.content" />
              </template>
              <template #actions v-if="item.showActions !== false">
                <t-chat-action
                  :content="item.content"
                  :operation-btn="['good', 'bad', 'replay', 'copy']"
                  @operation="(type, options) => handleOperation(type, options, index)"
                />
              </template>
            </t-chat-item>
          </template>

          <template #footer>
            <t-chat-sender
              ref="chatSenderRef"
              v-model="inputText"
              :stop-disabled="streamLoading"
              :textarea-props="{ placeholder: '请输入消息...', autosize: { minRows: 2, maxRows: 12 } }"
              :file-props="{ multiple: true }"
              @stop="handleOnStop"
              @send="handleOnSend"
              @file-select="fileSelect"
            >
              <template #prefix>
                <div class="m-chat-select">
                  <t-select class="m-select-model" v-model="selectModelValue" :options="selectModel" value-type="object"></t-select>
                  <t-select class="m-select-function" v-model="selectAgentValue" placeholder="请选择工具" multiple :min-collapsed-num="1" @click="getFunctionList">
                    <t-option label="全选" :check-all="true" />
                    <t-option v-for="item in selectAgent" :key="item.description" :value="item.name" :label="item.name" :title="item.description"></t-option>
                  </t-select>
                  <!-- <t-select v-model="selectknowledgeValue" :options="selectknowledge" value-type="object"></t-select> -->
                </div>
              </template>
            </t-chat-sender>
          </template>
        </t-chat>

        <t-button class="m-chat-bottomBtn" v-if="isShowToBottom" variant="text" @click="handleBackBottom">
          <div class="m-chat-to-bottom">
            <ArrowDownIcon />
          </div>
        </t-button>
      </div>
    </t-drawer>

    <!-- ========== 新增：新建/编辑常用词模板弹窗 ========== -->
    <t-dialog
      v-model:visible="createPromptVisible"
      :header="isEditMode ? '编辑常用词模板' : '新建常用词模板'"
      :confirmBtn="{
        content: '保存',
        theme: 'primary',
        loading: createLoading,
      }"
      :onConfirm="saveNewTemplate"
      :footer="true"
      width="800px"
    >
      <t-form :data="createForm" label-width="80px" style="padding: 20px">
        <t-form-item label="主题" name="title" :rules="[{ required: true, message: '请输入主题' }]">
          <t-input v-model="createForm.title" placeholder="请输入模板主题" />
        </t-form-item>
        <t-form-item label="描述" name="description" :rules="[{ required: true, message: '请输入描述' }]">
          <t-textarea
            v-model="createForm.description"
            placeholder="请输入模板描述"
            :autosize="{ minRows: 4, maxRows: 6 }"
          />
          <!-- <t-input v-model="createForm.description" placeholder="请输入模板描述" /> -->
        </t-form-item>
        <t-form-item label="内容" name="content" :rules="[{ required: true, message: '请输入模板内容' }]">
          <t-textarea
            v-model="createForm.content"
            placeholder="请输入常用词内容"
            :autosize="{ minRows: 4, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item label="MCP工具" name="tool_name_str" :rules="[{ required: false, message: '请选择MCP工具' }]">
          <t-select v-model="createForm.tool_name_str" multiple :min-collapsed-num="1" @click="getFunctionList">
            <t-option label="全选" :check-all="true" />
            <t-option v-for="item in selectAgent" :key="item.description" :value="item.name" :label="item.name" :title="item.description"></t-option>
          </t-select>
        </t-form-item>
        <t-form-item label="创建人" name="creator">
          <t-input v-model="createForm.creator" disabled />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="js">
import { ref, nextTick, computed, onUnmounted, watch, markRaw, h } from 'vue';
import { Icon, ArrowDownIcon, SearchIcon, AddIcon, CheckCircleIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
// import { TdAttachmentItem } from '@tdesign-vue-next/chat';
import { useUserStore } from '@/store';
import { v4 as uuidv4 } from 'uuid';
import { Utils } from "@/utils/utils";
import { askReqManageAgent, getHistoryChatRecordList, getPromptListBySearchStr, updateSinglePromptCcontent, updateSinglePromptReferenceCount, delSinglePrompt, getToolNameList } from "@/api/mcp.js";
const headerParams = Utils.getHeader();
const imageUrl = `https://icenterapi.zte.com.cn/zte-km-icenter-user/user/avatar/${headerParams?.['X-Emp-No'] ?? ''}`;
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const REQUIRE_API_URL = import.meta.env.VITE_REQUIRE_API_URL;
const user = useUserStore();

// 使用 defineModel
const drawVisible = defineModel('visible', { type: Boolean, default: false });

const props = defineProps({
  aiChatTitle: {
    type: [String],
    default: '您的专属',
  },
  aiChatContext: {
    type: [String],
    default: '',
  },
  aiChatAgent: {
    type: [String],
    default: 'chat',
  },
});

// 内部状态
const chatRef = ref(null);
const chatList = ref([]);
const inputText = ref('');
const streamLoading = ref(false); //是否显示onStop按钮
const isShowToBottom = ref(false);
const fetchCancel = ref(null);
const eventSourceRef = ref(null);
const chatSenderRef = ref(null);
const isStreamLoad = ref(false);
const isMCP = ref(false);
let session_id = uuidv4();
let fileContent = null;

const collapsed = ref(true);

const gFile = ref(''); // 如果想存 File 对象
const gContent = ref([]);

const selectModel = [
  {
    label: '星云大模型',
    value: 'nebula',
  },
  {
    label: '通义千问-中兴',
    value: 'qwen3-zte',
  }
];
const selectModelValue = ref({
    label: '星云大模型',
    value: 'nebula',
  });

const selectAgent = ref([]);
const selectAgentValue = ref();

const focusInput = () => {
  nextTick(() => {
    // 触发输入框聚焦（根据组件内部结构调整选择器）
    if (chatSenderRef.value) {
      const textarea = chatSenderRef.value.$el.querySelector('textarea');
      if (textarea) {
        textarea.focus();
      }
    }
  });
};

// ========== 新增：新建常用词模板相关状态 ==========
const createPromptVisible = ref(false); // 控制新建弹窗显示
const createLoading = ref(false); // 保存按钮的加载状态
const isEditMode = ref(false); // 是否为编辑模式
const createForm = ref({
  // 表单数据
  title: '',
  subtitle: '',
  content: '',
  scene: '',
  description: '',
  tool_name_str: [],
  creator: user.userInfo.name || '', // 默认为当前用户
});

// ========== 新增：打开新建弹窗 ==========
const openCreatePromptDialog = () => {
  // 设置为新建模式
  isEditMode.value = false;
  createForm.value = {
    // 重置表单
    title: '',
    subtitle: '',
    content: '',
    description: '',
    tool_name_str: [],
    scene: props.aiChatTitle || '', // 场景字段默认取aiChatTitle的值
    creator: user.userInfo.name || '',
  };
  createPromptVisible.value = true;
};

const handleChange = (value) => {
    console.log('handleChange', chatList);
};

/**
 * 渲染推理模块的头部自定义内容
 * @param {boolean} flag - 思维链内容是否加载中
 * @param {string} endText - 思维链加载完成时显示的文本
 * @returns {JSX.Element} 返回对应的头部组件
 */
const renderHeader = (flag, item) => {
  if (flag) {
    return null;
    // 返回 VNode，等价于 <t-chat-loading text="思考中..." />
    // return h('t-chat-loading', { text: '思考中...' });
  }
  const endText = item.duration
    ? `已总结(用时${item.duration}秒)`
    : '已完成思考';

  return h('div', { style: 'display:flex;align-items:center' }, [
    h(CheckCircleIcon, {
      style: {
        color: 'var(--td-success-color-5)',
        fontSize: '20px',
        marginRight: '8px',
      },
    }),
    h('span', endText),
  ])
};

const fileSelect = (data) => {
  const files = data.files;
  if (!files || files.length === 0) return alert('未选择文件');

  /* ==========  批量处理：逐个校验 & 收集  ========== */
  const allowedExtensions = [
    '.txt', '.json', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.less',
    '.html', '.htm', '.py', '.java', '.cpp', '.c', '.h', '.hpp', '.cs',
    '.php', '.rb', '.go', '.swift', '.md', '.markdown', '.xml', '.csv',
    '.log', '.config', '.yml', '.yaml', '.ini',
    '.xlsx', '.xls', '.pdf', // 电子表格
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp'  // ← 新增图片
  ];
  const MAX_SIZE = 15_000 * 1024 * 1024; // 15 MB

  const validFiles = []; // 通过校验的文件
  const failMsgs = []; // 失败原因

  [...files].forEach((file) => {
    const { name: fileName, size } = file;
    const ext = '.' + fileName.toLowerCase().split('.').pop();

    // 1. 大小
    if (size > MAX_SIZE) {
      failMsgs.push(`【${fileName}】超过 15 MB`);
      return null;
    }
    // 2. 扩展名
    if (!allowedExtensions.includes(ext)) {
      failMsgs.push(`【${fileName}】后缀不支持`);
      return null;
    }

    // 3. 内容预判（异步→先同步拦一道）
    validFiles.push(file);
  });

  if (failMsgs.length) {
    alert(`以下文件未通过校验：\n${failMsgs.join('\n')}`);
    if (!validFiles.length) return null; // 全部失败
  }

  /* ==========  批量读取 & 展示  ========== */
  Promise.all(
    validFiles.map((file) =>
      new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const uint8 = new Uint8Array(e.target.result);
          const text = new TextDecoder('utf-8', { fatal: false }).decode(uint8);
          const nonPrint = [...text.slice(0, 1000)].filter(
            (c) => (c.charCodeAt(0) < 32 && ![9, 10, 13].includes(c.charCodeAt(0))) || c.charCodeAt(0) === 127
          ).length;
          resolve({ file, isText: nonPrint / Math.min(1000, text.length) < 0.5 });
        };
        reader.onerror = () => resolve({ file, isText: false });
        reader.readAsArrayBuffer(file.slice(0, 1024));
      })
    )
  ).then((results) => {
    const reallyValid = [];
    results.forEach(({ file, isText }) => {
      if (isText) reallyValid.push(file);
      else failMsgs.push(`【${file.name}】内容不是可读文本`);
    });

    if (failMsgs.length) alert(failMsgs.join('\n'));

    // 4. 真正有效的文件 → 统一挂到全局 & 聊天列表
    if (reallyValid.length) {
      // 多个文件拼成一条用户消息，避免刷屏
      const nameList = reallyValid.map((f) => f.name).join('、');
      chatList.value.unshift({
        avatar: '/src/assets/white.png',
        datetime: new Date().toLocaleString(),
        content: `${nameList} 导入成功`,
        file: reallyValid, // 这里变成数组
        role: 'model-change',
        showActions: false,
      });
      // 把文件数组挂到全局，供 handleData 上传时循环 FormData.append
      gContent.value.push(reallyValid[0]); // 原来是单个 File，现在 File[]
      gFile.value = nameList;
    }
  });
};

/**
 * 渲染推理内容组件
 * @param {string} reasoningContent - 需要渲染的推理内容
 * @returns {JSX.Element} 返回 markdown渲染内容，用于展示推理内容, 不用markdown渲染组件原文返回
 */
const renderReasoningContent = (reasoningContent) => {
  return h('t-chat-content', { content: reasoningContent, role: 'assistant' });
};

// ========== 新增：保存新建/编辑的模板 ==========
const saveNewTemplate = async () => {
  createLoading.value = true;
  
  try {
    const params = {
        title: createForm.value.title,
        // subtitle: createForm.value.subtitle,
        content: createForm.value.content,
        // scene: createForm.value.scene,
        creator: createForm.value.creator,
        description: createForm.value.description,
        tool_name_str: createForm.value.tool_name_str.join(','),
        reference_count: createForm.value.reference_count, // 保留引用次数
        // 根据你的后端接口，可能还需要其他字段
      }
    const response = await updateSinglePromptCcontent(params);

    if (response.status === 'success') {
      MessagePlugin.success(isEditMode.value ? '模板保存成功' : '模板创建成功');
      // 可选：刷新模板列表
      TemplatesGet();
      createPromptVisible.value = false; // 关闭弹窗
    } else {
      MessagePlugin.error(response.message || '保存模板失败');
    }
  } catch (err) {
    MessagePlugin.error('无法保存模板，请稍后再试');
  } finally {
    createLoading.value = false;
  }
};

// 假设这是你的模板数据源
const templates = ref(null);
const TemplatesGet = async (searchKeyword = '') => {
  try {
    const params = {
        search_str: searchKeyword, // 支持传入搜索词，空字符串表示获取全部
      }
    const response = await getPromptListBySearchStr(params)
    if (response.status === 'success') {
      templates.value = response.data;
      // MessagePlugin.success(`${response.message}`);
    } else {
      MessagePlugin.error('获取模板失败，请稍后再试。');
    }
  } catch (err) {
    MessagePlugin.error('无法加载模板数据，请稍后再试。');
    console.error('Fetch templates error:', err);
  } finally {
    console.log('请求 Templates 完成');
  }
};

// 过滤后的模板列表
const searchText = ref(''); // 搜索文本
const filteredTemplates = computed(() => {
  if (!templates.value || !Array.isArray(templates.value) || !searchText.value) {
    return Array.isArray(templates.value) ? templates.value : [];
  }

  // 确保searchText.value是字符串类型
  const search = String(searchText.value).toLowerCase();

  return templates.value.filter((template) => {
    // 确保template是一个对象
    if (!template || typeof template !== 'object') {
      return false;
    }

    // 安全地检查各个字段
    const title = template.title ? String(template.title).toLowerCase() : '';
    const subtitle = template.subtitle ? String(template.subtitle).toLowerCase() : '';
    const content = template.content ? String(template.content).toLowerCase() : '';
    const scene = template.scene ? String(template.scene).toLowerCase() : '';
    const creator = template.creator ? String(template.creator).toLowerCase() : '';

    return (
      title.includes(search) ||
      subtitle.includes(search) ||
      content.includes(search) ||
      scene.includes(search) ||
      creator.includes(search)
    );
  });
});

/**
 * 创建新的对话
 * 清空当前对话记录并生成新的会话ID
 */
const handleNewChat = () => {
  session_id = uuidv4();
  chatList.value = [];
  gContent.value = [];
  gFile.value = '';
  MessagePlugin.info('创建对话成功');
};

const historyChatDrawVisible = ref(false);
const historyLoading = ref(false); // 历史会话加载状态
const handleHistoryChat = () => {
  historyChatDrawVisible.value = true;
  historyLoading.value = true; // 开始加载
  HistoryGet(); // 获取聊天记录
};

const historyChatRecord = ref([]); // 用于保存聊天记录
const HistoryGet = async () => {
  try {
    const params = {
        user: user.userInfo.name,
      }
    const response = await getHistoryChatRecordList(params)

    if (response.status === 'success') {
      historyChatRecord.value = response.data;
      MessagePlugin.success(`${response.message}`);
    } else {
      MessagePlugin.error('获取聊天记录失败，请稍后再试。');
    }
  } catch (err) {
    MessagePlugin.error('无法加载聊天记录，请稍后再试。');
  } finally {
    historyLoading.value = false; // 关闭加载状态
    console.log('请求 History 完成（无论成功/失败）');
  }
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

// 获取历史记录tooltip显示内容
const getHistoryTooltipContent = (id) => {
  // 1. 只筛选 user 和 assistant 的记录
  const sessionRecords = historyChatRecord.value
    .filter((record) => record.session_id === id && (record.role === 'user' || record.role === 'assistant'))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  if (!sessionRecords.length) {
    return '该会话没有聊天记录';
  }

  // 2. 构建显示内容（显示所有记录）
  let tooltipContent = '';

  sessionRecords.forEach((record, index) => {
    const roleLabel = record.role === 'user' ? `${record.user_name + record.user_id}` : 'AI';
    // 格式化时间，只显示月/日 时:分
    const date = new Date(record.timestamp);
    const time = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    // 使用HTML标签加粗时间和角色（不加maxLength限制）
    tooltipContent += `<strong>${time} ${roleLabel}:</strong>
    ${record.content}
`;

    // 不在最后一条记录后添加换行
    if (index < sessionRecords.length - 1) {
      tooltipContent += `
`;
    }
  });

  return tooltipContent;
};

// 将历史聊天记录拷贝到剪切板中
const handleSessionClick = async (id) => {
  // 1. 只筛选 user 和 assistant 的记录
  const sessionRecords = historyChatRecord.value
    .filter((record) => record.session_id === id && (record.role === 'user' || record.role === 'assistant'))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  if (!sessionRecords.length) {
    MessagePlugin.warning('该会话没有聊天记录');
    return;
  }

  // 2. 构建复制内容
  let clipboardText = '';

  sessionRecords.forEach((record) => {
    const roleLabel = record.role === 'user' ? `${record.user_name + record.user_id}` : 'AI';
    const time = record.timestamp;

    clipboardText += `${time} ${roleLabel}：\n${record.content}\n\n`;
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

const promptDrawVisible = ref(false);
const handlePromptTemplate = (text) => {
  promptDrawVisible.value = true;
  // searchText.value = props.aiChatTitle; // 设置默认搜索词为aiChatTitle
  TemplatesGet(text); // 获取模板数据
};

// 引用常用词模版 —— 替换模式（清空后设置）
const handleTemplateReference = async (template) => {
  inputText.value = template.content?.trimStart();
  selectAgentValue.value = template.tool_name_str?.split(',') || [];
  // 等待 DOM 更新后再聚焦
  await nextTick();
  const textareaEl = document.querySelector('.t-textarea__inner');
  if (textareaEl) {
    textareaEl.focus();
    // 可选：将光标定位到内容末尾
    textareaEl.setSelectionRange(template.content.length, template.content.length);
  }

  // 增加引用计数
  await incrementReferenceCount(template);
};

// 增加模板引用计数
const incrementReferenceCount = async (template) => {
  try {
    const params = {
        title: template.title,
        subtitle: template.subtitle,
        content: template.content,
        scene: template.scene,
        creator: template.creator,
        description: template.description,
        tool_name_str: template.tool_name_str?.split(','),
        reference_count: (template.reference_count || 0) + 1, // 增加引用计数
      }
    const response = await updateSinglePromptReferenceCount(params);

    if (response.status === 'success') {
      console.log('引用计数更新成功');
      // 可选：刷新模板列表
      TemplatesGet();
    } else {
      console.error('引用计数更新失败:', response.message || '未知错误');
    }
  } catch (err) {
    console.error('无法更新引用计数:', err);
  }
};

// 修改常用词模板
const handleTemplateEdit = (template) => {
  // 设置为编辑模式
  isEditMode.value = true;
  // 填充表单数据
  createForm.value = {
    title: template.title || '',
    subtitle: template.subtitle || '',
    content: template.content || '',
    scene: template.scene || props.aiChatTitle || '', // 如果模板中没有场景，则使用aiChatTitle
    creator: template.creator || user.userInfo.name || '',
    reference_count: template.reference_count || 0, // 保留引用次数
    description: template.description || '',
    tool_name_str: template.tool_name_str?.split(',') || [],
  };
  // 显示新建/编辑弹窗
  createPromptVisible.value = true;
};

// 删除常用词模板
const handleTemplateDelete = async (template) => {
  try {
     const params = {
        user: user.userInfo.name,
        creator: template.creator,
        title: template.title,
      }
    const response = await delSinglePrompt(params)

    if (response.status === 'success') {
      MessagePlugin.success('模板删除成功');
      // 刷新模板列表
      TemplatesGet();
    } else {
      // 显示后端返回的具体错误信息
      MessagePlugin.error(response.message || '删除失败：未知错误');
    }
  } catch (err) {
    // 网络错误、请求失败、解析失败等都会进入这里
    MessagePlugin.error(`无法删除模板：${err.message}`);
  }
};

/**
 * 处理聊天操作（点赞、点踩、重发、复制等）
 */
const handleOperation = (type, options, index) => {
  console.log('handleOperation', type, options, index);
  // if (type === 'replay') {
  //   handleOnSend(chatList[index].content);
  // }
};

const getFunctionList = async () => {
  try {
    const response = await getToolNameList()

    if (response.status === 'success') {
      selectAgent.value = response.data
    } else {
      // 显示后端返回的具体错误信息
      MessagePlugin.error(response.message);
    }

  } catch (err) {
    // 网络错误、请求失败、解析失败等都会进入这里
    MessagePlugin.error(`${err.message}`);
  }


};

/**
 * 滚动到底部
 * 将聊天内容滚动到最新消息位置
 */
const handleBackBottom = () => {
  chatRef.value.scrollToBottom({ behavior: 'smooth' });
};

/**
 * 处理聊天区域滚动事件
 */
const handleChatScroll = ({ e }) => {
  const scrollTop = e.target.scrollTop;
  isShowToBottom.value = scrollTop < 0;
};

const handleOnStop = () => {
  console.log('handleOnStop');

  // 关闭EventSource连接
  if (eventSourceRef.value) {
    eventSourceRef.value.close();
    eventSourceRef.value = null;
  }

  // 取消fetch请求
  if (fetchCancel.value) {
    fetchCancel.value.abort();
    fetchCancel.value = null;
  }

  // 恢复当前回答项的点赞按钮显示
  if (chatList.value.length > 0 && chatList.value[0].role === 'assistant') {
    chatList.value[0].showActions = true;
    chatList.value[0].textLoading = false;
  }

  streamLoading.value = false;
  gContent.value = [];
  gFile.value = '';

  focusInput();
};

/**
 * 处理用户输入消息
 * 将用户消息添加到聊天列表并调用AI处理
 * @param {string} inputValue - 用户输入的内容
 */
const handleOnSend = (inputValue) => {
  if (streamLoading.value || !inputValue) return;

  // 添加用户消息
  chatList.value.unshift({
    avatar: imageUrl,
    datetime: new Date().toLocaleString(),
    content: inputValue,
    role: 'user',
    showActions: true, // 用户消息始终显示操作按钮
    textLoading: false,
  });

  // 添加AI回答占位项
  chatList.value.unshift({
    avatar: '/src/assets/assets-ai2.png',
    content: '',
    reasoning: '',
    duration: 0,
    role: 'assistant',
    showActions: false, // 初始时不显示操作按钮
    textLoading: false, // 显示加载状态
  });

  handleData(inputValue);
  inputText.value = '';
};

const buildFormData = (inputValue, selectAgentStr) => {
  const fd = new FormData();
  /* 1. 普通字段 ...... */
  fd.append('user', user.userInfo.name);
  fd.append('session_id', session_id);
  fd.append('request_id', uuidv4());
  fd.append('model', selectModelValue.value.value);
  fd.append('agent', selectAgentValue.value);
  fd.append('icenter', true);
  fd.append('rdc', true);
  fd.append('think', false);
  fd.append('content', inputValue);
  fd.append('context', JSON.stringify(props.aiChatContext));
  fd.append('component', props.aiChatTitle);
  fd.append('knowledge', 'NoneKnowledge');
  fd.append('tool_name_str', selectAgentStr);

  /* 2. 文件字段（多文件） */
  if (gContent.value) {
    // gContent 现在是 File[]
    const fileArray = Array.isArray(gContent.value) ? gContent.value : [...gContent.value];
    fileArray.forEach((file) => fd.append('file', file, file.name));
  }

  return fd;
};

/**
 * 处理AI数据请求和响应
 * 向服务器发送用户消息并处理流式响应
 * @param {string} inputValue - 用户输入的内容
 */
const handleData = async (inputValue) => {
  streamLoading.value = true;
  isStreamLoad.value = true;
  if (selectAgentValue.value.length > 0) {
    isMCP.value = true;
  }
  // 创建 AbortController
  const controller = new AbortController();
  fetchCancel.value = controller;

  // 获取当前回答项的引用
  const currentResponse = chatList.value[0];
  // 初始化 reasoning 字段
  currentResponse.reasoning = '';

  const selectAgentStr = [...new Set(selectAgentValue.value)].join(',');
  const fd = buildFormData(inputValue, selectAgentStr);


  try {
    const response = await fetch(`https://wsit.zx.zte.com.cn/api/electric_knowledge/req_manage_agent/ask_req_manage_agent`, {
      method: 'POST',
      headers: { 
        'X-Emp-No': headerParams?.['X-Emp-No'] ?? '',
        'X-Auth-Value': headerParams?.['X-Auth-Value'] ?? ''
      },
      body: fd,
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || 'Network response was not ok');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let rawBuffer = '';
    let textBuffer = '';
    let updateTimer = null;
    
    // 新增：状态变量
    let isInToolName = false;      // 是否在 tool_name 标签中
    let isInToolResult = false;    // 是否在 tool_result 标签中
    let toolReasoningBuffer = '';  // 存储 reasoning 内容（仅标签内的内容）
    const startTime = Date.now();

    const processStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // 处理剩余的任何数据
            if (textBuffer) {
              currentResponse.content += textBuffer;
              textBuffer = '';
            }
            // 如果还有未处理的 reasoning 内容
            if (toolReasoningBuffer) {
              currentResponse.reasoning += toolReasoningBuffer;
              toolReasoningBuffer = '';
            }
            
            currentResponse.showActions = true;
            currentResponse.textLoading = false;
            streamLoading.value = false;
            focusInput();
            return;
          }

          const chunk = decoder.decode(value, { stream: true });
          rawBuffer += chunk;

          const lines = rawBuffer.split('\n');
          rawBuffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === '') continue;

            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6);

              if (dataStr === '[DONE]') {
                // 立即更新任何剩余的文本
                if (textBuffer) {
                  currentResponse.content += textBuffer;
                  textBuffer = '';
                }
                // 处理剩余的 reasoning 内容
                if (toolReasoningBuffer) {
                  currentResponse.reasoning += toolReasoningBuffer;
                  toolReasoningBuffer = '';
                }
                
                currentResponse.showActions = true;
                currentResponse.textLoading = false;
                streamLoading.value = false;
                isStreamLoad.value = false;
                isMCP.value = false;
                focusInput();
                return;
              }

              try {
                const data = JSON.parse(dataStr);
                let textContent = '';
                
                // 检查是 text 字段还是 tool_result 字段
                if (data.text !== undefined) {
                  textContent = data.text;
                }
                
                if (textContent) {
                  // 处理 tool_name 开始标签
                  if (textContent.includes('<tool_name>')) {
                    isInToolName = true;
                    // 只提取开始标签后的内容，不包含标签本身
                    const startIndex = textContent.indexOf('<tool_name>');
                    const afterTag = textContent.substring(startIndex + '<tool_name>'.length);
                    if (afterTag) {
                      toolReasoningBuffer += afterTag;
                    }
                    // 如果标签中有完整的结束标签（处理边界情况）
                    // if (textContent.includes('</tool_name>')) {
                    //   const endIndex = textContent.indexOf('</tool_name>');
                    //   const beforeEnd = textContent.substring(0, endIndex);
                    //   if (beforeEnd.includes('<tool_name>')) {
                    //     const actualContent = beforeEnd.substring(beforeEnd.indexOf('<tool_name>') + '<tool_name>'.length);
                    //     toolReasoningBuffer += actualContent;
                    //   }
                    //   // 提取结束标签后的内容到普通内容
                    //   const afterEndTag = textContent.substring(endIndex + '</tool_name>'.length);
                    //   if (afterEndTag) {
                    //     textBuffer += afterEndTag;
                    //   }
                    //   isInToolName = false;
                    //   // 将积累的 reasoning 内容保存（不包含标签）
                    //   if (toolReasoningBuffer) {
                    //     currentResponse.reasoning += toolReasoningBuffer;
                    //     toolReasoningBuffer = '';
                    //   }
                    // }
                  }
                  // 处理 tool_name 结束标签
                  else if (textContent.includes('</tool_name>')) {
                    // const endIndex = textContent.indexOf('</tool_name>');
                    // // 结束标签前的内容加入 reasoning（不包含标签本身）
                    // const beforeEnd = textContent.substring(0, endIndex);
                    // if (beforeEnd) {
                    //   toolReasoningBuffer += beforeEnd;
                    // }
                    // // 保存 reasoning 内容（不包含标签）
                    // if (toolReasoningBuffer) {
                    //   currentResponse.reasoning += toolReasoningBuffer;
                    //   toolReasoningBuffer = '';
                    // }
                    // // 结束标签后的内容加入普通内容
                    // const afterEndTag = textContent.substring(endIndex + '</tool_name>'.length);
                    // if (afterEndTag) {
                    //   textBuffer += afterEndTag;
                    // }
                    isInToolName = false;
                  }
                  // 处理 tool_result 开始标签
                  else if (textContent.includes('<tool_result>')) {
                    isInToolResult = true;
                    const startIndex = textContent.indexOf('<tool_result>');
                    const afterTag = textContent.substring(startIndex + '<tool_result>'.length);
                    if (afterTag) {
                      toolReasoningBuffer += afterTag;
                    }
                    // 如果标签中有完整的结束标签
                    if (textContent.includes('</tool_result>')) {
                    //   const endIndex = textContent.indexOf('</tool_result>');
                    //   const beforeEnd = textContent.substring(0, endIndex);
                    //   if (beforeEnd.includes('<tool_result>')) {
                    //     const actualContent = beforeEnd.substring(beforeEnd.indexOf('<tool_result>') + '<tool_result>'.length);
                    //     toolReasoningBuffer += actualContent;
                    //   }
                    //   const afterEndTag = textContent.substring(endIndex + '</tool_result>'.length);
                    //   if (afterEndTag) {
                    //     textBuffer += afterEndTag;
                    //   }
                      isInToolResult = false;
                    //   // 将积累的 reasoning 内容保存（不包含标签）
                    //   if (toolReasoningBuffer) {
                    //     currentResponse.reasoning += toolReasoningBuffer;
                    //     toolReasoningBuffer = '';
                    //   }
                    }
                  }
                  // 处理 tool_result 结束标签
                  // else if (textContent.includes('</tool_result>')) {
                    // const endIndex = textContent.indexOf('</tool_result>');
                    // const beforeEnd = textContent.substring(0, endIndex);
                    // if (beforeEnd) {
                    //   toolReasoningBuffer += beforeEnd;
                    // }
                    // // 保存 reasoning 内容（不包含标签）
                    // if (toolReasoningBuffer) {
                    //   currentResponse.reasoning += toolReasoningBuffer;
                    //   toolReasoningBuffer = '';
                    // }
                    // const afterEndTag = textContent.substring(endIndex + '</tool_result>'.length);
                    // if (afterEndTag) {
                    //   textBuffer += afterEndTag;
                    // }
                    // isInToolResult = false;
                  // }
                  // 处理标签内的内容（不包含标签本身）
                  else if (isInToolName || isInToolResult) {
                    // 当前在标签内，内容放入 reasoning 缓冲区
                    toolReasoningBuffer += textContent;
                    const endTime = Date.now();
                    currentResponse.duration = ((endTime - startTime) / 1000).toFixed(2);
                  }
                  // 普通内容
                  else {
                    isStreamLoad.value = false;
                    textBuffer += textContent;
                  }

                  // 使用缓冲机制优化性能
                  if (updateTimer) clearTimeout(updateTimer);
                  updateTimer = setTimeout(() => {
                    if (textBuffer) {
                      currentResponse.content += textBuffer;
                      currentResponse.textLoading = false;
                      textBuffer = '';
                    }
                    // 如果 reasoning 缓冲区有内容但不在标签中（边界情况）
                    if (toolReasoningBuffer && !isInToolName && !isInToolResult) {
                      currentResponse.reasoning += toolReasoningBuffer;
                      toolReasoningBuffer = '';
                    }
                  }, 20);
                }
              } catch (e) {
                console.error('解析JSON出错:', e, '原始数据:', dataStr);
              }
            }
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('流读取已被中止');
        } else {
          console.error('流读取错误:', error);
          if (textBuffer) {
            currentResponse.content += textBuffer;
            textBuffer = '';
          }
          if (toolReasoningBuffer) {
            currentResponse.reasoning += toolReasoningBuffer;
            toolReasoningBuffer = '';
          }
          currentResponse.content += `\n流处理错误: ${error.message || 'Unknown error occurred'}`;
          currentResponse.showActions = true;
          currentResponse.textLoading = false;
          streamLoading.value = false;
          isStreamLoad.value = false;
          isMCP.value = false;
        }
      }
    };
    processStream();
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求已被中止');
      currentResponse.content = '请求已被中止';
    } else {
      console.error('请求出错:', error);
      currentResponse.content = `请求出错: ${error.message || 'Unknown error occurred'}`;
    }
    currentResponse.showActions = true;
    currentResponse.textLoading = false;
    streamLoading.value = false;
    isStreamLoad.value = false;
    isMCP.value = false;
  } finally {
    gContent.value = [];
    gFile.value = '';
  }
};

defineExpose({
  chatRef,
});

watch(
  () => props.aiChatAgent,
  (newAgent) => {
    // 根据传入的 agent 设置下拉框默认值
    // const agentOption = selectAgent.find((opt) => opt.value === newAgent);
    // if (agentOption) {
    //   selectAgentValue.value.find((opt) => opt.value === agentOption);
    // }
  },
  { immediate: true },
);

onUnmounted(() => {
  handleOnStop(); // 清理所有资源
});
</script>

<style scoped>
.m-chat :deep(*) {
  .m-chat-box {
    display: flex;
    height: 95%;

    .m-chat-bottomBtn {
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

    .m-chat-to-bottom {
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

    .m-chat-select {
      display: flex;
      align-items: center;

      .m-select-model {
        width: 200px;
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

      .m-select-function {
        width: 380px;
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

    .t-chat__detail {
      max-width: 90% !important;
    }

    .t-chat__inner.user {
      margin-right: 10px;

      .t-chat__text {
        background-color: #f5f5f5 !important;
      }
    }

    .t-chat__text {
      background-color: transparent !important;
      font-size: 14px !important;
      line-height: 2 !important;
    }

    .t-chat__actions-margin * {
      background-color: transparent !important;
      border: none !important;
    }

    .m-chat-new {
      position: absolute;
      z-index: 4000;
      top: 80px;
      left: 20px;
      margin-left: 0px;
      box-shadow:
        0px 4px 12px rgba(0, 0, 0, 0.15),
        0px 16px 32px rgba(0, 0, 0, 0.2),
        0px 32px 48px rgba(0, 0, 0, 0.15);
    }
    .m-chat-history {
      position: absolute;
      z-index: 4000;
      top: 80px;
      left: 80px;
      margin-left: 0px;
      box-shadow:
        0px 4px 12px rgba(0, 0, 0, 0.15),
        0px 16px 32px rgba(0, 0, 0, 0.2),
        0px 32px 48px rgba(0, 0, 0, 0.15);
    }
    .m-chat-prompt {
      position: absolute;
      z-index: 4000;
      top: 80px;
      left: 140px;
      margin-left: 0px;
      box-shadow:
        0px 4px 12px rgba(0, 0, 0, 0.15),
        0px 16px 32px rgba(0, 0, 0, 0.2),
        0px 32px 48px rgba(0, 0, 0, 0.15);
    }

    .m-chat-card-main {
      width: 100%;
      background-color: #f3f3f3;
    }

    .m-chat-card-content {
      flex: 1;
      font-size: 14px;
      color: #333;

      /* 多行文本截断 */
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2; /* 控制最多显示几行 */
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .t-card__title {
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 1; /* 控制最多显示几行 */
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .t-card__subtitle {
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 1; /* 控制最多显示几行 */
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .t-card__header {
      padding-top: 5px;
      padding-bottom: 5px;
    }

    .t-card__body {
      padding-top: 0px;
      padding-bottom: 0px; /* 修复 typo: 原为 padding-top: 5px 两次 */
    }

    .t-card__footer {
      padding-top: 5px;
      padding-bottom: 5px; /* 修复 typo: 原为 padding-top: 5px 两次 */
    }
    .t-card__actions {
      display: flex;
      align-items: flex-start; /* 向上对齐 */
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
    }

    .history-time {
      font-size: 12px;
      color: #999;
      margin-top: 4px;
    }

    /* 常用词模板搜索框布局 */
    .prompt-search-container {
      width: 100%;
      display: flex;
      gap: 10px;
    }

    .prompt-filter-container {
      display: flex;
      width: 100%;
      overflow-x: auto;
    }

    .prompt-search-container .t-button {
      flex-shrink: 0;
    }

    .prompt-search-container .t-input {
      flex: 1;
    }
  }

  /* 表格样式 */
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

  th {
    background-color: #f3f3f3;
    color: #333;
    white-space: nowrap;
    padding: 12px 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    line-height: 1.4;
  }

  td {
    background-color: #fefefe;
    padding: 8px 10px;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4;
  }

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
    line-height: 1.5;
  }
}
</style>
