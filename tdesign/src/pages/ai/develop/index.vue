<template>
  <div class="devolop-main">
    <t-steps :default-current="current" @change="handleStepChange">
      <t-step-item title="需求分析" content="提示文字">
        <div>①需求意图识别</div>
        <div>②场景切片提取</div>
        <div>③功能特性提取</div>
        <div>④特性变更点识别</div>
      </t-step-item>
      <t-step-item title="方案设计" content="提示文字">
        <div>①组件提取</div>
        <div>②组件接口设计</div>
        <div>②组件协作流程设计</div>
      </t-step-item>
      <t-step-item title="详细设计" content="提示文字">
        <div>①组件变更点分析</div>
        <div>②模块变更点分析</div>
      </t-step-item>
      <t-step-item title="开发编码" content="提示文字">
        <div>①详设功能组件获取</div>
        <div>②识别变更点和变更值</div>
        <div>③编写业务代码</div>
        <div>④编写FT用例</div>
        <div>⑤代码提交</div>
      </t-step-item>
      <t-step-item title="测试构建" content="提示文字" />
    </t-steps>

    <t-space class="develop-toolbar">
      <t-tooltip content="新建对话" placement="top-left">
        <t-button class="develop-new-chat" size="large" theme="primary" shape="circle" variant="base" @click="newChat">
          <icon name="plus" />
        </t-button>
      </t-tooltip>
      <t-button size="large" shape="round">
        {{ buttonText }}
      </t-button>
      <t-input v-model="inputContent" size="large" :placeholder="inputPlaceholder"> </t-input>
    </t-space>

    <div class="develop-container">
      <div class="develop-chat-box">
        <t-chat ref="chatRef" layout="both" :clear-history="false">
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
      </div>
      <div class="develop-log-box">
        <div class="develop-log-header">
          <t-collapse>
            <t-collapse-panel header="相关信息">
              <t-chat-content :content="AllContent" variant="text"> </t-chat-content>
            </t-collapse-panel>
            <t-collapse-panel header="需求分析">
              <template #headerRightContent>
                <t-button size="small" @click="toggleEdit('BA')">
                  {{ editStatus.BA ? '保存' : '编辑' }}
                </t-button>
                <t-button size="small" @click="writeBack('BA')" :disabled="editStatus.BA"> 回填 </t-button>
              </template>
              <!-- 需求分析内容区域，根据编辑状态切换 -->
              <div v-if="editStatus.BA">
                <t-textarea
                  v-model="BAContent"
                  rows="10"
                  placeholder="请输入需求分析变更内容"
                  class="edit-textarea"
                ></t-textarea>
              </div>
              <div v-else>
                <t-chat-content :content="BAContent" variant="text"> </t-chat-content>
              </div>
            </t-collapse-panel>
            <t-collapse-panel header="方案设计">
              <template #headerRightContent>
                <t-button size="small" @click="toggleEdit('SE')">
                  {{ editStatus.SE ? '保存' : '编辑' }}
                </t-button>
                <t-button size="small" @click="writeBack('SE')" :disabled="editStatus.SE"> 回填 </t-button>
              </template>
              <!-- 方案设计内容区域，根据编辑状态切换 -->
              <div v-if="editStatus.SE">
                <t-textarea
                  v-model="SEContent"
                  rows="10"
                  placeholder="请输入方案设计变更内容"
                  class="edit-textarea"
                ></t-textarea>
              </div>
              <div v-else>
                <t-chat-content :content="SEContent" variant="text"> </t-chat-content>
              </div>
            </t-collapse-panel>
            <t-collapse-panel header="详细设计">
              <template #headerRightContent>
                <t-button size="small" @click="toggleEdit('TL')">
                  {{ editStatus.TL ? '保存' : '编辑' }}
                </t-button>
                <t-button size="small" @click="writeBack('TL')" :disabled="editStatus.TL"> 回填 </t-button>
              </template>
              <!-- 详细设计内容区域，根据编辑状态切换 -->
              <div v-if="editStatus.TL">
                <t-textarea
                  v-model="TLContent"
                  rows="10"
                  placeholder="请输入详细设计变更内容"
                  class="edit-textarea"
                ></t-textarea>
              </div>
              <div v-else>
                <t-chat-content :content="TLContent" variant="text"> </t-chat-content>
              </div>
            </t-collapse-panel>
            <t-collapse-panel header="开发编码">
              <template #headerRightContent>
                <t-button size="small" @click="toggleEdit('DEV')">
                  {{ editStatus.DEV ? '保存' : '编辑' }}
                </t-button>
                <t-button size="small" @click="writeBack('DEV')" :disabled="editStatus.DEV"> 回填 </t-button>
              </template>
              <!-- 开发编码内容区域，根据编辑状态切换 -->
              <div v-if="editStatus.DEV">
                <t-textarea
                  v-model="DEVContent"
                  rows="10"
                  placeholder="请输入开发编码变更内容"
                  class="edit-textarea"
                ></t-textarea>
              </div>
              <div v-else>
                <t-chat-content :content="DEVContent" variant="text"> </t-chat-content>
              </div>
            </t-collapse-panel>
          </t-collapse>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, nextTick } from 'vue';
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
import { useUserStore } from '@/store';
import axios from 'axios';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

const fetchCancel = ref(null);
const isStreamLoad = ref(false);

// 响应式数据：聊天输入框内容和加载状态
const query = ref('');
const inputText = ref('');

const loading = ref(false);
const chatRef = ref(null);
const chatList = ref([]);
const buttonText = ref('需求分析智能体');

const AllContent = ref('**需求编号**，需求实例化链接，需求方案链接，详细设计链接，代码库');
const BAContent = ref('需求分析变更内容');
const SEContent = ref('方案设计变更内容');
const TLContent = ref('详细设计变更内容');
const DEVContent = ref('开发编码变更内容');

// 编辑状态管理
const editStatus = ref({
  BA: false, // 需求分析编辑状态
  SE: false, // 方案设计编辑状态
  TL: false, // 详细设计编辑状态
  DEV: false, // 开发编码编辑状态
});

// 定义 agent 到 content ref 的映射
const logContentMap = {
  BaAgent: BAContent,
  SeAgent: SEContent,
  TlAgent: TLContent,
  L2MvpAgent: DEVContent,
  CustomerAgent: SEContent,
};

// 定义 agent 到提取内容规则的映射（策略模式）
const logContentRulesMap = {
  BaAgent: '### 需求变更内容总结',
  SeAgent: '### 📝方案变更内容总结',
  TlAgent: '### 📝详设变更内容总结',
  L2MvpAgent: '### 📝代码变更内容总结',
};

const inputContent = ref('OTNSW-687638');
const inputPlaceholder = ref('请输入需求编号');

// 当前步骤
const current = ref(0);
const agent = ref('BaAgent');

const result = ref('');
const logContent = ref('');

// 处理步骤变化
const handleStepChange = (currentStep, previousStep, context) => {
  session_id = uuidv4(); // 重置聊天id

  switch (currentStep) {
    case 0:
      buttonText.value = '需求分析智能体';
      agent.value = 'BaAgent';
      inputPlaceholder.value = '请输入需求编号';
      break;
    case 1:
      buttonText.value = '方案设计智能体';
      agent.value = 'SeAgent';
      inputPlaceholder.value = '请输入方案设计链接';
      break;
    case 2:
      buttonText.value = '详细设计智能体';
      agent.value = 'TlAgent';
      inputPlaceholder.value = '请输入详细设计链接';
      break;
    case 3:
      buttonText.value = '开发编码智能体';
      agent.value = 'L2MvpAgent';
      inputPlaceholder.value = '请输入代码路径';
      break;
    case 4:
      buttonText.value = '测试智能体';
      agent.value = 'CustomerAgent';
      break;
    default:
      console.warn('未知的步骤:', currentStep);
  }
};

// 切换编辑状态
const toggleEdit = (type) => {
  editStatus.value[type] = !editStatus.value[type];

  // 如果切换到编辑状态，自动聚焦到文本框
  if (editStatus.value[type]) {
    nextTick(() => {
      const textarea = document.querySelector(`.edit-textarea`);
      if (textarea) {
        textarea.focus();
      }
    });
  } else {
    // 切换到非编辑状态时，显示保存成功提示
    MessagePlugin.success(`${getTypeName(type)}内容已保存`);
  }
};

// 回填处理
const writeBack = async (type) => {
  // 获取对应类型的内容
  let content = '';
  switch (type) {
    case 'BA':
      content = BAContent.value;
      break;
    case 'SE':
      content = SEContent.value;
      break;
    case 'TL':
      content = TLContent.value;
      break;
    case 'DEV':
      content = DEVContent.value;
      break;
    default:
      MessagePlugin.error('未知的回写类型');
      return;
  }

  // 显示加载状态
  MessagePlugin.loading(`${getTypeName(type)}内容回写中...`, 0);

  try {
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Icenter_block_set`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: user.userInfo.name,
        workflow: type,
        content: content, // 发送实际的 content
      }),
    });

    const data = await response.json();

    // 关闭加载提示
    MessagePlugin.closeAll();

    if (data.status === 'success') {
      MessagePlugin.success(`${getTypeName(type)}内容回写成功`);
      console.log(`回写${getTypeName(type)}内容:`, content);
    } else {
      // 可根据后端返回的具体错误信息调整提示
      MessagePlugin.error(`${getTypeName(type)}内容回写失败: ${data.message || '未知错误'}`);
      console.error('回写失败:', data);
    }
  } catch (error) {
    // 网络错误或请求异常
    MessagePlugin.closeAll();
    MessagePlugin.error(`${getTypeName(type)}内容回写请求失败，请检查网络或服务状态`);
    console.error('回写请求出错:', error);
  }
};

// 获取类型名称用于提示信息
const getTypeName = (type) => {
  const typeMap = {
    BA: '需求分析',
    SE: '方案设计',
    TL: '详细设计',
    DEV: '开发编码',
  };
  return typeMap[type] || type;
};

const onStop = function () {
  if (fetchCancel.value) {
    fetchCancel.value.controller.close();
    loading.value = false;
    isStreamLoad.value = false;
  }
};

const newChat = function () {
  session_id = uuidv4(); // 重置聊天id
  chatList.value = []; // 清空聊天列表
  MessagePlugin.info('创建对话成功');
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
    datetime: new Date().toLocaleString(),
    content: inputContent.value + '\n' + inputValue,
    role: 'user',
  };

  chatList.value.unshift(params);

  // 空消息占位
  const params2 = {
    avatar: '/src/assets/assets-ai2.png',
    content: '',
    reasoning: '',
    role: 'assistant',
  };

  chatList.value.unshift(params2);

  handleData(inputValue);
  inputText.value = ''; // 清空输入框
};

const user = useUserStore();

// 为每个聊天单独制定一个唯一id，防止同时提问时冲突
let session_id = uuidv4();

let mr = '';
let requirementLink = '';
let solutionLink = '';
let xiangshe = '';

const handleData = async (inputValue) => {
  loading.value = true;
  isStreamLoad.value = true;
  const request_id = uuidv4();
  const lastItem = chatList.value[0];

  let buffer = '';
  let isFlushing = false;
  let fullText = '';
  let outputContent = '';

  inputValue = inputContent.value + '\n' + inputValue;

  function flushBuffer() {
    if (buffer && lastItem) {
      lastItem.content += buffer; // 只有在 Vue 中才会触发响应式更新
      buffer = '';
    }
    isFlushing = false;
  }

  try {
    const response = await fetch(`${SERVER_API_URL}/api_chat/Chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: user.userInfo.name,
        session_id: session_id,
        model: 'nebula',
        agent: agent.value,
        icenter: true,
        rdc: true,
        think: false,
        content: inputValue,
      }),
    });

    const data = await response.json();

    if (data.status === 'success') {
      const eventSource = new EventSource(
        `${SERVER_API_URL}/api_chat/Sse?session_id=${encodeURIComponent(session_id)}`,
      );

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close();
          if (buffer) {
            lastItem.content += buffer;
            buffer = '';
          }

          if (fullText) {
            const extractMarker = logContentRulesMap[agent.value];
            const targetContentRef = logContentMap[agent.value];

            if (targetContentRef && extractMarker) {
              targetContentRef.value = extractOutputContent(fullText, extractMarker);
            }

            const inputString = targetContentRef.value;

            // 正则表达式用于匹配链接
            const requirementPattern = /需求实例化链接：\s*(https?:\/\/[^\s]+)/;
            const solutionPattern = /需求方案链接：\s*(https?:\/\/[^\s]+)/;

            // 安全提取链接
            const requirementMatch = inputString.match(requirementPattern);
            const solutionMatch = inputString.match(solutionPattern);

            if (requirementMatch) {
              requirementLink = requirementMatch[1];
            }

            if (solutionMatch) {
              solutionLink = solutionMatch[1];
            }

            AllContent.value = `**需求编号**：${inputContent.value}\n\n**需求实例化链接**：${requirementLink}\n\n**需求方案链接**：${solutionLink}`;
          }

          isStreamLoad.value = false;

          // 等待 DOM 更新后再聚焦
          nextTick().then(() => {
            const textareaEl = document.querySelector('.t-textarea__inner');
            if (textareaEl) {
              textareaEl.focus();
            }
          });

          return;
        }

        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            answer.value = `错误: ${data.error}`;
            eventSource.close();
          } else if (data.text) {
            buffer += data.text;

            if (!isFlushing) {
              isFlushing = true;
              setTimeout(() => {
                flushBuffer();
              }, 50); // 控制更新频率，避免高频渲染
            }
            // 【新增】实时更新 result 内容
            fullText += data.text;
          }
        } catch (e) {
          console.error('解析SSE数据失败:', e);
        }
      };
    } else {
      lastItem.role = 'error';
      lastItem.content = 'Error occurred while fetching data.';
    }

    lastItem.datetime = new Date().toLocaleString();
  } catch (error) {
    lastItem.role = 'error';
    lastItem.content = 'Error occurred while sending the message.';
  } finally {
    // 显示用时xx秒，业务侧需要自行处理
    lastItem.duration = 5;
    // 骨架屏蒙版设置
    loading.value = false;
  }
};

function typeWriterEffect(text, elementValueRef, speed = 100) {
  return new Promise((resolve) => {
    let index = 0;
    const timer = setInterval(() => {
      if (index < text.length) {
        elementValueRef.value += text[index];
        index++;
      } else {
        clearInterval(timer);
        resolve();
      }
    }, speed);
  });
}

function extractOutputContent(text, StartMarker) {
  const startMarker = StartMarker;

  // 查找起始位置
  const startIndex = text.indexOf(startMarker);

  if (startIndex === -1) {
    return '提取内容失败！'; // 没有找到标记，返回空字符串
  }

  // 截取从起始标记到末尾的所有内容
  return text.slice(startIndex);
}
</script>

<style lang="less">
.develop-toolbar {
  margin-bottom: 10px !important;
  margin-top: 10px !important;
}

.develop-container {
  width: 100%; /* 占据整个视口宽度 */
  display: flex;
  gap: 8px;

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
    background-color: #e7e7e7;
    color: #333;
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

  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }

  .hljs {
    line-height: 1.5;
  }

  .develop-chat-box {
    width: 35%;
    min-width: 400px;
    height: 65vh;
    padding: 20px;
    border: 1px solid #e4e4e4;
    box-sizing: border-box;
    background-color: #f9f9f9;
    border-radius: 8px;
  }

  .develop-log-box {
    flex: 1;
    min-width: 400px;
    height: 65vh;
    padding: 20px;
    border: 1px solid #e4e4e4;
    box-sizing: border-box;
    background-color: #f9f9f9;
    border-radius: 8px;
    overflow-y: auto;
  }

  .develop-log-header .develop-log-content {
    max-height: 100%;
    overflow: auto;
    padding: 10px;
  }

  .t-chat__detail {
    max-width: 86% !important;
  }

  .t-chat__inner.user {
    margin-right: 10px;
  }

  .t-chat__text {
    background-color: #eff6ff !important;
    font-size: 14px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 10px 15px;
    transition: box-shadow 0.3s ease;
  }

  .develop-log-box .t-chat__text {
    background-color: transparent !important;
    line-height: 1.4;
  }
}

/* 编辑框样式 */
.edit-textarea {
  width: 100%;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 12px 16px; /* 稍微增加内边距提升舒适度 */
  font-size: 14px;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  resize: vertical; /* 允许用户垂直调整大小 */

  &:focus {
    outline: none;
    border-color: #4096ff;
    box-shadow: 0 0 0 2px rgba(64, 150, 255, 0.2);
  }

  .t-textarea__inner {
    min-height: 400px !important; /* 增加最小高度作为后备 */
  }
}
</style>
