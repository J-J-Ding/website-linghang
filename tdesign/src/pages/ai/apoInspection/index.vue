<template>
  <div class="apo-inspection-page">

    <!-- 顶部功能按钮区 (保留原有图标风格) -->
    <div class="top-action-bar">
      <!-- 新建对话 -->
      <t-tooltip content="新建对话" placement="bottom">
        <t-button
          class="action-btn"
          theme="primary"
          shape="circle"
          @click="handleNewChat"
        >
          <template #icon>
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </template>
        </t-button>
      </t-tooltip>

      <!-- 历史对话 -->
      <t-tooltip content="历史对话" placement="bottom">
        <t-button
          class="action-btn"
          theme="primary"
          shape="circle"
          @click="showHistoryDrawer = true"
        >
          <template #icon>
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
            </svg>
          </template>
        </t-button>
      </t-tooltip>
    </div>

    <!-- Chat Box 对话显示区 -->
    <div class="chat-box" ref="chatBoxRef">
      <!-- 空状态/欢迎页 -->
      <div v-if="chatList.length === 0" class="welcome-container">
        <div class="welcome-content">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" width="64" height="64">
              <path fill="#0052d9" d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7.5 13A2.5 2.5 0 0 0 5 15.5 2.5 2.5 0 0 0 7.5 18 2.5 2.5 0 0 0 10 15.5 2.5 2.5 0 0 0 7.5 13zm9 0a2.5 2.5 0 0 0-2.5 2.5 2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0 2.5-2.5 2.5 2.5 0 0 0-2.5-2.5z"/>
            </svg>
          </div>
          <h2>APO巡检助手</h2>
          <p>选择系统类型和巡检项，开始智能巡检分析</p>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, index) in chatList" :key="index" class="message-row" :class="msg.role">
        <div class="msg-avatar">
          <div v-if="msg.role === 'assistant'" class="avatar-robot">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7.5 13A2.5 2.5 0 0 0 5 15.5 2.5 2.5 0 0 0 7.5 18 2.5 2.5 0 0 0 10 15.5 2.5 2.5 0 0 0 7.5 13zm9 0a2.5 2.5 0 0 0-2.5 2.5 2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0 2.5-2.5 2.5 2.5 0 0 0-2.5-2.5z"/>
            </svg>
          </div>
          <img v-else src="https://tdesign.gtimg.com/site/avatar.jpg" alt="user" />
        </div>
        <div class="msg-body">
<!--          <div class="msg-bubble">{{ msg.content }}</div>-->
          <!-- 使用 v-html 指令来渲染 marked 生成的 HTML 结构 -->
          <div class="msg-bubble" v-html="renderMarkdown(msg.content)"></div>
          <div class="msg-time">{{ msg.time }}</div>
        </div>
      </div>

      <!-- 思考中状态 -->
      <div v-if="isThinking" class="message-row assistant">
        <div class="msg-avatar"><div class="avatar-robot">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7.5 13A2.5 2.5 0 0 0 5 15.5 2.5 2.5 0 0 0 7.5 18 2.5 2.5 0 0 0 10 15.5 2.5 2.5 0 0 0 7.5 13zm9 0a2.5 2.5 0 0 0-2.5 2.5 2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0 2.5-2.5 2.5 2.5 0 0 0-2.5-2.5z"/>
          </svg>
        </div></div>
        <div class="msg-body">
          <div class="msg-bubble thinking">
            <span class="dot-flashing"></span>
            <span class="dot-flashing delay-1"></span>
            <span class="dot-flashing delay-2"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入与配置区 (优化修改版) -->
    <div class="bottom-input-section">
      <div class="input-container">

        <!-- 第一行：系统类型 -->
        <div class="config-row">
          <span class="config-label">系统类型：</span>
          <t-select
            v-model="systemType"
            placeholder="请选择系统类型"
            size="medium"
            style="width: 200px;"
          >
            <t-option label="C/CE" value="C/CE" />
            <t-option label="CPP" value="CPP" />
            <t-option label="C+L" value="C+L" />
          </t-select>
        </div>

        <!-- 第二行：巡检项选择 -->
        <div class="config-row">
          <span class="config-label">巡检项选择：</span>
          <t-checkbox-group v-model="inspectionItems" size="medium">
            <t-checkbox value="OA初始增益检查">OA初始增益检查</t-checkbox>
            <t-checkbox value="OA增益一致性检查">OA增益一致性检查</t-checkbox>
            <t-checkbox value="OA初始斜率检查">OA初始斜率检查</t-checkbox>
            <t-checkbox value="VOA初始衰减检查">VOA初始衰减检查</t-checkbox>
            <t-checkbox value="EDFA端口无光检测">EDFA端口无光检测</t-checkbox>
            <t-checkbox value="OBM端口无光检测">OBM端口无光检测</t-checkbox>
            <!-- 👇 在这里插入一个强制换行的 div -->
<!--            <div class="force-new-line"></div>-->
          <div class="second-row-group">
            <t-checkbox value="EDFA端面脏污反射系数越限检测">EDFA端面脏污反射系数越限检测</t-checkbox>
            <t-checkbox value="EDFA器件异常检测">EDFA器件异常检测</t-checkbox>
            <t-checkbox value="EDFA增益与链路跨损不匹配检测">EDFA增益与链路跨损不匹配检测</t-checkbox>
          </div>
          </t-checkbox-group>
        </div>

        <!-- 第三行：文件上传 (放在巡检项下方) -->
        <div class="config-row">
          <span class="config-label">文件上传：</span>
          <t-upload
            v-model="fileList"
            :auto-upload="false"
            accept=".txt,.log,.zip,.csv,.tar,.gz"
            :before-upload="beforeUpload"
            @change="handleFileChange"
            theme="file"
          >
            <t-button theme="default" variant="outline">
              <template #icon>
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/>
                </svg>
              </template>
              选择文件
            </t-button>
          </t-upload>
          <span v-if="fileList.length > 0" class="file-name">{{ fileList[0].name }}</span>
        </div>

        <!-- 第四行：文本输入框 (增大) -->
        <div class="textarea-area">
          <t-textarea
            v-model="inputMessage"
            placeholder="请输入指令或直接发送执行巡检，支持多行输入..."
            :autosize="{ minRows: 2, maxRows: 4}"
            @keydown.enter.exact.prevent="handleSend"
          />
        </div>

        <!-- 底部操作栏 -->
        <div class="input-footer">
          <div class="footer-left">
            <span class="footer-tip">支持 .xslx 文件</span>
          </div>
          <div class="footer-right">
            <t-button variant="base" theme="default" @click="resetConfig">重置配置</t-button>
            <t-button
              theme="primary"
              @click="handleSend"
              :loading="isThinking"
              :disabled="!canSend"
              size="large"
            >
              <template #icon>
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <path fill="currentColor" d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                </svg>
              </template>
              发送
            </t-button>
          </div>
        </div>

      </div>
    </div>

    <!-- 历史对话抽屉 -->
    <t-drawer
      v-model:visible="showHistoryDrawer"
      placement="right"
      size="320px"
      header="历史会话"
      :footer="false"
    >
      <div class="history-panel">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item"
          @click="loadHistorySession(item)"
        >
          <div class="history-icon">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path fill="currentColor" d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
            </svg>
          </div>
          <div class="history-info">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-time">{{ item.time }}</div>
          </div>
        </div>
      </div>
    </t-drawer>

  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, computed, nextTick, onMounted } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';

import { v4 as uuidv4 } from 'uuid';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { marked } from 'marked'; //渲染表格

const INTELDIGA_API_URL = import.meta.env.VITE_INTELDIGA_API_URL;
const router = useRouter();
const user = useUserStore();
// 为每个聊天单独制定一个唯一id，防止同时提问时冲突
let session_id = uuidv4();

// --- 状态数据 ---
const inputMessage = ref('');
const systemType = ref('');
const inspectionItems = ref([]);
const fileList = ref([]);
const isThinking = ref(false);
const showHistoryDrawer = ref(false);
const chatBoxRef = ref(null);

const loading = ref(false);
// 流式数据加载中
const isStreamLoad = ref(false);

const startTime = ref(null);
const endTime = ref(null);
const dateRange = ref([]);
const uploading = ref(false);
const uploadStatus = ref(null);

// 聊天记录
const chatList = ref([]);

// 历史会话列表
const historyList = ref([
  { id: 1, title: 'APO巡检任务 #202401', time: '2024-05-10 14:30' },
  { id: 2, title: 'OA增益一致性分析', time: '2024-05-11 09:15' },
  { id: 3, title: 'VOA衰减检查报告', time: '2024-05-12 16:45' },
  { id: 4, title: 'C/CE系统全量巡检', time: '2024-05-13 11:20' },
  { id: 5, title: 'CPP斜率检查任务', time: '2024-05-14 10:00' },
]);

// 文件上传相关
async function isLikelyTextFile(file) {
  const buffer = await file.slice(0, 1024).arrayBuffer();
  const view = new Uint8Array(buffer);
  let binary = 0;
  for (const b of view) {
    if (b < 9 || (b > 13 && b < 32) || b > 126) binary++;
  }
  return binary / view.length <= 0.15;
}

const beforeUpload = async (fileObject) => {
  const file = fileObject.raw;
  const name = file.name.toLowerCase();
  console.log(name);
  // 放行 .tar.gz（accept 无法识别）
  if (name.endsWith('.tar.gz') || name.endsWith('.csv') || name.endsWith('.xlsx')) {
    return true;
  }

  // 对 .txt / .log 做内容检测
  if (/\.(txt|log)$/i.test(name)) {
    const isText = await isLikelyTextFile(file);
    if (!isText) {
      MessagePlugin.error(`文件 "${file.name}" 不是有效文本文件`);
      return false; // 阻止上传
    }
  }
  return true; // 允许上传
};

// 3. 创建一个全局的渲染函数，供模板使用
// 注意：在 script setup 中，需要将其挂载到组件实例或作为全局函数（在 Vue3 <script setup> 中，直接定义的函数默认不可在模板中作为过滤器使用，所以我们通过一个 computed 或直接在 setup 顶层定义，然后在模板中调用）
// 这里我们直接定义一个函数
const renderMarkdown = (text) => {
  if (!text) return '';
  // 只需确保使用 .parse 方法
  return marked.parse(text);
};

// --- 计算属性 ---
const canSend = computed(() => {
  return inputMessage.value.trim() ||
         systemType.value ||
         inspectionItems.value.length > 0 ||
         fileList.value.length > 0;
});

// --- 方法 ---
const verifyToken = async () => {
  try {
    const response = await fetch(`${INTELDIGA_API_URL}/api/verifyToken`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name,
        token: user.uacToken})
    });

    let responseData = await response.json();

    // 如果后端返回 status === 'success'，说明验证通过
    if (responseData.status === 'success') {
      return true;
    } else {
      return false;
    }
  } catch (error) {
    console.error('Token verification failed:', error);
    // 网络错误或 401/500 等都会进这里
    return false;
  }
};

const handleData = async (inputValue, messageIndex) => {
  loading.value = true;
  isStreamLoad.value = true;

  const request_id = uuidv4();
  // 注意：这里不需要 lastItem 了，因为我们通过索引动态获取
  // const lastItem = chatList.value[0]; // 删除这行

  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    // 准备时间参数
    const timeParams = {};
    // if (selectModelValue.value?.value === '日志分析' && startTime.value && endTime.value) {
    //   timeParams.start_time = new Date(startTime.value).toISOString().replace('T', ' ').substring(0, 19);
    //   timeParams.end_time = new Date(endTime.value).toISOString().replace('T', ' ').substring(0, 19);
    // }
    // 直接使用流式接口
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 480000); // 480秒超时

    const response = await fetch(`${INTELDIGA_API_URL}/api/tryChat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name,
        session_id: session_id,
        token: user.uacToken,
        message: {
          input: inputValue,
          starttime: dateRange.value[0],
          endtime: dateRange.value[1],
          mode: 'APO升级巡检',
          knowledge: "rdc",
          jump: ""
        }
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported in this browser');
    }

    // 使用 ReadableStream 处理 SSE
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    // 统一的清理函数
    const cleanUp = () => {
      loading.value = false;
      isStreamLoad.value = false;
      isThinking.value = false;

      nextTick().then(() => {
        const textareaEl = document.querySelector('.t-textarea__inner');
        if (textareaEl) textareaEl.focus();
      });
    };

    // 处理读取到的数据
    const processStream = async () => {
      let updatePending = false; // 标记是否需要更新视图
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            if (updatePending) {
                await nextTick();
            }
            cleanUp();
            break;
          }

          // 解码并添加到缓冲区
          // 注意：如果 value 很大，这里依然会有压力，但这是 Stream API 的限制
          const textChunk = decoder.decode(value, { stream: true });

          // 优化：如果 buffer 已经非常大，可能需要警惕，但通常 split 是瓶颈
          buffer += textChunk;

          // 按行处理数据
          const lines = buffer.split('\n');
          // 保留最后一行不完整的数据
          buffer = lines.pop() || ''; // 处理最后一行可能为空的情况

          // 标记本轮有数据需要处理
          if (lines.length > 0) {
              updatePending = true;
          }

          for (const line of lines) {
            if (line.startsWith('data:')) {
              const data = line.slice(5).trim(); // 移除 'data:' 前缀

              if (data === '[DONE]') {
                cleanUp();
                // 流式完成：若当前模式为RDC诊断，并且内容以指定文案严格结尾，则展示按钮
                return;
              }

              try {
                const json = JSON.parse(data);
                // 4. 核心修改：通过传入的索引找到对应的消息
                // 检查索引是否有效
                if (messageIndex === undefined || !chatList.value[messageIndex]) {
                  continue; // 防御性编程
                }
                // if (!lastItem) continue; // 防御性编程

                let hasUpdate = false;
                let targetMessage = chatList.value[messageIndex]; // 获取目标消息

                if (json.info_type === 'answer' && json.text) {
                  // 关键：等待 Vue 更新 DOM，确保 marked 解析的新内容能立即显示
                  // 这对于表格一行行出现的效果至关重要
                  // await nextTick();
                  // scrollToBottom();
                  // 5. 核心修改：拼接内容到指定的消息上
                  targetMessage.content += json.text;
                  if (json.message_id) targetMessage.message_id = json.message_id;
                  hasUpdate = true;
                }else if (['thought'].includes(json.info_type) && json.text) {
                  // await nextTick();
                  // scrollToBottom();
                  // 5. 核心修改：拼接内容到指定的消息上
                  targetMessage.content += json.text;
                  if (json.message_id) targetMessage.message_id = json.message_id;
                  hasUpdate = true;
                }

                // 如果有更新，标记需要刷新，但不要在这里 await
                if (hasUpdate) {
                    updatePending = true;
                }
              } catch (e) {
                console.error('解析JSON失败:', e);
              }
            }
          }
          // 【重要优化】：不要在每个 packet 里都 await nextTick()
          // 让事件循环有机会去渲染。如果数据量极大，可以每隔 N 行 yield 一次，
          // 但通常去掉循环内的 await，利用 Vue 的 batch update 机制即可解决大部分卡顿。
          // 如果依然卡，可以使用 requestAnimationFrame 或 setTimeout 让出主线程
          if (updatePending && isStreamLoad.value) {
              // 方案 A: 简单移除 await，依赖 Vue 批量更新 (推荐先试这个)
              // updatePending = false;

              // 方案 B: 如果还是卡，每处理完一个 read() 包后，让出主线程
              await new Promise(resolve => setTimeout(resolve, 0));
              scrollToBottom();
              updatePending = false;
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          console.error('读取流时发生错误:', error);
          // if (lastItem) {
          //   lastItem.role = 'error';
          //   lastItem.content = `流读取错误: ${error.message}`;
          // }
        }
        cleanUp();
      } finally {
        reader.releaseLock();
      }
    };

    // 开始处理流
    processStream();
  } catch (error) {
    console.error('请求异常:', error);

    // if (error.name === 'AbortError') {
    //   lastItem.content = '请求超时，请重试';
    // } else {
    //   lastItem.content = `网络错误: ${error.message || '未知错误'}`;
    // }
    //
    // lastItem.role = 'error';
    // lastItem.datetime = new Date().toLocaleString();
    if (chatList.value[messageIndex]) {
      chatList.value[messageIndex].role = 'error';
      chatList.value[messageIndex].content = `请求失败: ${error.message}`;
    }
    cleanUp();
  } finally {
    // 确保最终关闭加载状态
    loading.value = false;
    isStreamLoad.value = false;

    // // 显示用时xx秒
    // lastItem.duration = 5;
  }
};


// 发送消息
const handleSend = async () => {
  if (!canSend.value) return;

  let content = inputMessage.value.trim() || '任务：APO巡检';

  const configParts = [];
  if (systemType.value) {
    configParts.push(`系统类型：${systemType.value}\n`);
  }
  if (inspectionItems.value.length > 0) {
    configParts.push(`巡检项：${inspectionItems.value.join('和')}`);
  }
  if (fileList.value.length > 0) {
    configParts.push(`文件：${fileList.value[0].name}`);
  }

  const fullContent = configParts.length > 0
    ? `${content}\n\n${configParts.join('\n')}`
    : content;
  console.log(fullContent)
  addMessage('user', fullContent);

  // 2. 添加一条 AI 的初始消息，并获取它的索引
  // 注意：这里我们先发一个空的或“思考中”的消息，后续会被流式数据覆盖
  const aiMessageIndex = chatList.value.length;
  let waiting_msg = '✅ 巡检任务已接收\n\n';
  if (systemType.value) {
    waiting_msg += `📌 系统类型：${systemType.value}\n`;
  }
  if (inspectionItems.value.length > 0) {
    waiting_msg += `📋 巡检项目:\n`;
    inspectionItems.value.forEach(item => {
      waiting_msg += `   • ${item}\n`;
    });
  }
  if (fileList.value.length > 0) {
    waiting_msg += `📎 附件：${fileList.value[0].name} 已解析\n`;
  }
  waiting_msg += `\n正在执行分析，请稍候...`;
  addMessage('assistant', waiting_msg); // 先放一个空内容，或者放 "AI正在输入..."

  inputMessage.value = '';
  // addMessage('assistant', '');
  // fileList.value = [];  // 保留文件列表，方便重复使用

  isThinking.value = true;
  scrollToBottom();

  // 3. 关键修改：将索引传给 handleData
  // 注意：这里去掉了原来的 setTimeout 模拟，直接调用
  // 原来的 setTimeout 是为了模拟 AI 延迟，现在流式接口自己有延迟，可以去掉
  handleData(fullContent, aiMessageIndex); // 传入索引
};

// 添加消息
const addMessage = (role, content) => {
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  chatList.value.push({ role, content, time });
  nextTick(() => scrollToBottom());
};

// 滚动到底部
const scrollToBottom = () => {
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
  }
};

// 新建对话
const handleNewChat = () => {
  session_id = uuidv4(); // 重置聊天id
  chatList.value = [];
  resetConfig();
  MessagePlugin.success('已新建对话');
};

// 重置配置
const resetConfig = () => {
  systemType.value = '';
  inspectionItems.value = [];
  inputMessage.value = '';
  fileList.value = [];
};

// 文件上传
// --- 上传逻辑 ---
async function uploadFile(file) {
  uploading.value = true;
  uploadStatus.value = null;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', 'APO升级巡检');
  formData.append('session_id', session_id);

  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (res.data.success) {
      MessagePlugin.success('文件上传成功');
      uploadStatus.value = { type: 'success', message: `文件 "${file.name}" 上传成功` };
    } else {
      throw new Error(res.data.error || '上传失败');
    }
  } catch (error) {
    const msg = error.response?.data?.error || error.message || '上传失败';
    MessagePlugin.error(`文件上传失败: ${msg}`);
    uploadStatus.value = { type: 'error', message: `文件上传失败: ${msg}` };
  } finally {
    uploading.value = false;
    fileList.value = [];
    displayFileContent(file.name, uploadStatus.value?.type);
  }
}

function displayFileContent(fileName, status) {
  let contentText = '';

  if (status === 'success') {
    contentText = `✅ 文件 "${fileName}" 已成功上传。`;
  } else {
    contentText = `❌ 文件 "${fileName}" 上传失败。`;
  }

  const params = {
    avatar: '/src/assets/assets-user3.png',
    datetime: new Date().toLocaleString(),
    content: contentText,
    role: 'user',
    isFile: true // 标识为文件消息
  };
  chatList.value.unshift(params);
}

const handleFileChange = (files) => {
  if (files.length > 0) {
    MessagePlugin.success(`文件 "${files[0].name}" 已添加`);
    const file = files[0].raw;
    uploadFile(file);
  }
};

// 加载历史会话
const loadHistorySession = (item) => {
  showHistoryDrawer.value = false;
  MessagePlugin.info(`加载：${item.title}`);
  // 实际项目中调用 API 加载历史消息
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

const fetchNetInformation = async () => {
  try {
    const response = await fetch(`${INTELDIGA_API_URL}/api/get-net-information`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === 'success') {
      console.log("success");
    } else {
      console.error('获取信息失败:', result.message);
    }
  } catch (err) {
    console.error('获取信息失败:', error);
  }
};

onMounted(async() => {
  await checkAuth(); // 先检查登录状态
  const isValid = await verifyToken();
  if (!isValid) {
    router.push('/login');
  }
  fetchNetInformation();
  scrollToBottom();
});
</script>

<style lang="less" scoped>
.apo-inspection-page {
  display: flex;
  flex-direction: column;
  height: 90vh;
  background-color: #f5f5f5;
  position: relative;
}

/* 顶部功能按钮区 */
.top-action-bar {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
  display: flex;
  gap: 12px;

  .action-btn {
    width: 48px;
    height: 48px;
    box-shadow: 0 4px 12px rgba(0, 82, 217, 0.25);
    background-color: #0052d9;
    border: none;

    &:hover {
      background-color: #0040b0;
      box-shadow: 0 6px 16px rgba(0, 82, 217, 0.35);
    }

    :deep(svg) {
      fill: #ffffff;
    }
  }
}

//.chat-box {
//  position: relative;
//  height: 84vh;
//  // background-color: yellow;
//
//  /* 基础表格样式 */
//  table {
//    max-width: 100%;
//    border-collapse: collapse;
//    border-radius: 8px;
//    overflow: hidden;
//    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
//    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
//    font-size: 14px;
//    margin-top: 1em;
//    margin-bottom: 1em;
//  }
//
//  /* 表头样式 */
//  th {
//    background-color: #f3f3f3;
//    color: #333;
//    white-space: nowrap; /* 防止表头换行 */
//    padding: 12px 10px; /* 降低内边距 */
//    text-align: left;
//    font-weight: 600;
//    border-bottom: 2px solid #e0e0e0;
//    line-height: 1.4; /* 紧凑行高 */
//  }
//
//  /* 单元格样式 */
//  td {
//    background-color: #fefefe;
//    padding: 8px 10px; /* 显著降低内边距 */
//    border-bottom: 1px solid #d6d6d6;
//    color: #555;
//    line-height: 1.4; /* 紧凑行高 */
//  }
//
//  /* 悬停效果 */
//  tr:hover td {
//    background-color: #dbeafe;
//    transition: background-color 0.3s ease;
//  }
//
//  /* 响应式优化 */
//  @media (max-width: 600px) {
//    th,
//    td {
//      padding: 10px 8px;
//      font-size: 14px;
//    }
//  }
//
//  /* 代码块样式 */
//  .hljs {
//    font-size: 14px;
//    line-height: 1.5; /* 紧凑行高 */
//  }
//
//  .bottomBtn {
//    position: absolute;
//    left: 50%;
//    margin-left: -20px;
//    bottom: 210px;
//    padding: 0;
//    border: 0;
//    width: 40px;
//    height: 40px;
//    border-radius: 50%;
//    box-shadow:
//      0px 8px 10px -5px rgba(0, 0, 0, 0.08),
//      0px 16px 24px 2px rgba(0, 0, 0, 0.04),
//      0px 6px 30px 5px rgba(0, 0, 0, 0.05);
//  }
//  .to-bottom {
//    width: 40px;
//    height: 40px;
//    border: 1px solid #f0f0f0;
//    box-sizing: border-box;
//    background: var(--td-bg-color-container);
//    border-radius: 50%;
//    font-size: 24px;
//    line-height: 40px;
//    display: flex;
//    align-items: center;
//    justify-content: center;
//    .t-icon {
//      font-size: 24px;
//    }
//  }
//
//  .new-chat {
//    position: absolute; /* 或 absolute，视你的布局而定 */
//    z-index: 4000; /* 确保浮在最上层 */
//    top: 0px; /* 距离页面顶部的距离为0 */
//    left: 0px; /* 距离页面左边的距离为0 */
//    margin-left: 0px;
//    box-shadow:
//      0px 4px 12px rgba(0, 0, 0, 0.15),
//      // 浅层阴影
//      0px 16px 32px rgba(0, 0, 0, 0.2),
//      // 中层主阴影（更明显）
//      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
//  }
//
//  .new-chat-wrapper {
//    position: absolute;
//    z-index: 4000;
//    top: 0px;
//    left: 0px;
//  }
//
//  .history-chat {
//    position: absolute; /* 或 absolute，视你的布局而定 */
//    z-index: 4000; /* 确保浮在最上层 */
//    top: 0px; /* 距离页面顶部的距离为0 */
//    left: 60px; /* 距离页面左边的距离为0 */
//    margin-left: 0px;
//    box-shadow:
//      0px 4px 12px rgba(0, 0, 0, 0.15),
//      // 浅层阴影
//      0px 16px 32px rgba(0, 0, 0, 0.2),
//      // 中层主阴影（更明显）
//      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
//  }
//
//  .history-chat-wrapper {
//    position: absolute;
//    z-index: 4000;
//    top: 0px;
//    left: 60px;
//  }
//
//  .corpusadd {
//    position: absolute; /* 或 absolute，视你的布局而定 */
//    z-index: 4000; /* 确保浮在最上层 */
//    top: 0px; /* 距离页面顶部的距离为0 */
//    left: 120px; /* 距离页面左边的距离为0 */
//    margin-left: 0px;
//    box-shadow:
//      0px 4px 12px rgba(0, 0, 0, 0.15),
//      // 浅层阴影
//      0px 16px 32px rgba(0, 0, 0, 0.2),
//      // 中层主阴影（更明显）
//      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
//  }
//
//  .metricsBoard {
//  position: absolute; /* 或 absolute，视你的布局而定 */
//  z-index: 4000; /* 确保浮在最上层 */
//  top: 0px; /* 距离页面顶部的距离为0 */
//  left: 180px; /* 距离页面左边的距离为0 */
//  margin-left: 0px;
//  box-shadow:
//    0px 4px 12px rgba(0, 0, 0, 0.15),
//    // 浅层阴影
//    0px 16px 32px rgba(0, 0, 0, 0.2),
//    // 中层主阴影（更明显）
//    0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
//  }
//
//  .qaExport{
//  position: absolute; /* 或 absolute，视你的布局而定 */
//  z-index: 4000; /* 确保浮在最上层 */
//  top: 0px; /* 距离页面顶部的距离为0 */
//  left: 240px; /* 距离页面左边的距离为0 */
//  margin-left: 0px;
//  box-shadow:
//    0px 4px 12px rgba(0, 0, 0, 0.15),
//    // 浅层阴影
//    0px 16px 32px rgba(0, 0, 0, 0.2),
//    // 中层主阴影（更明显）
//    0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
//  }
//
//}

/* Chat Box 对话区 */
.chat-box {
  position: relative;
  flex: 1;
  overflow-y: auto;
  padding: 100px 24px 24px;
  scroll-behavior: smooth;

  .welcome-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    min-height: 400px;

    .welcome-content {
      text-align: center;
      color: #666;

      .welcome-icon {
        margin-bottom: 24px;
        opacity: 0.9;
      }

      h2 {
        color: #333;
        margin-bottom: 12px;
        font-size: 22px;
        font-weight: 600;
      }

      p {
        font-size: 14px;
        color: #999;
      }
    }
  }

  .message-row {
    display: flex;
    margin-bottom: 24px;
    max-width: 80%;

    &.user {
      flex-direction: row-reverse;
      margin-left: auto;

      .msg-avatar img {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        border: 2px solid #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }

      //.msg-bubble {
      //  background: linear-gradient(135deg, #0052d9 0%, #266fe8 100%);
      //  color: #ffffff;
      //}

      .msg-time {
        text-align: right;
        color: rgba(255,255,255,0.6);
      }
    }

    &.assistant {
      .avatar-robot {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #e3f0ff 0%, #c9dcff 100%);
        color: #0052d9;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);

        svg {
          fill: #0052d9;
        }
      }

      .msg-time {
        color: #999999;
      }
    }

    .msg-avatar {
      flex-shrink: 0;
    }

    .msg-body {
      margin: 0 12px;
      max-width: 100%;

      :deep(.msg-bubble) {
        padding: 14px 18px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.7;
        white-space: normal;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        word-break: break-word; /* 关键：防止长文本（包括表格代码）撑破容器 */

        &.thinking {
          background: #f5f5f5;
          padding: 12px 18px;
          display: flex;
          gap: 6px;
          align-items: center;

          .dot-flashing {
            width: 8px;
            height: 8px;
            background: #0052d9;
            border-radius: 50%;
            animation: flashing 1.4s infinite both;
          }

          .delay-1 { animation-delay: 0.2s; }
          .delay-2 { animation-delay: 0.4s; }
        }
      }

      /* 表格基础样式 */
      :deep(.msg-bubble table) {
        //width: 100%;
        //border-collapse: separate;
        //margin: 12px 0;
        //font-size: 14px;
        //background-color: #ffffff;
        //table-layout: auto; /* 允许列宽自适应内容 */
        //overflow-x: auto;
        //border: 1px solid #e0e0e0;
        //border-radius: 4px;
        //overflow: hidden; /* 让内部的 border-radius 生效 */
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
      :deep(.msg-bubble th) {
        //background-color: #f2f4f7 !important;
        //color: #1f2d3d;
        //font-weight: 600;
        //padding: 10px 12px;
        //text-align: left;
        //border-bottom: 2px solid #dcdfe6; /* 底部加深，分割表头和内容 */
        background-color: #f3f3f3;
        color: #333;
        white-space: nowrap; /* 防止表头换行 */
        padding: 12px 10px; /* 降低内边距 */
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e0e0e0;
        line-height: 1.4; /* 紧凑行高 */
      }
      /* 鼠标悬停高亮 */
      :deep(.msg-bubble tbody tr:hover) {
        background-color: #798863;
      }

      /* 表格单元格 */
      :deep(.msg-bubble th),
      :deep(.msg-bubble td) {
        //border: 1px solid #dcdfe6; /* 关键：添加灰色边框 */
        //padding: 10px 12px;
        //text-align: left;          /* 默认左对齐 */
        //border-bottom: 1px solid #e0e0e0;
        //color: #4e5969;
        background-color: #fefefe;
        padding: 8px 10px; /* 显著降低内边距 */
        border-bottom: 1px solid #d6d6d6;
        color: #555;
        line-height: 1.4; /* 紧凑行高 */
      }

      /* 6. 针对 Markdown 解析出的标题（如“五、巡检结果统计”） */
      :deep(.msg-bubble h5) {
        border-left: 4px solid #409eff; /* 左侧蓝色条，强调标题 */
        padding-left: 10px;
        color: #303133;
        margin-top: 20px;
      }
      /* 隔行变色，增加可读性 */
      :deep(.msg-bubble tbody tr:nth-child(even)) {
        background-color: #fafafa;
      }

      /* 最后一行去除下边框（可选） */
      :deep(.msg-bubble tbody tr:last-child td) {
        border-bottom: none;
      }

      /* 代码块样式（如果 marked 渲染了代码块） */
      :deep(.msg-bubble pre) {
        background-color: #f6f6f6;
        padding: 12px;
        border-radius: 4px;
        overflow: auto;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        border: 1px solid #e0e0e0;
      }
        /* 响应式优化 */
      @media (max-width: 600px) {
        th,
        td {
          padding: 10px 8px;
          font-size: 14px;
        }
      }
      :deep(.msg-bubble code) {
        background-color: #eee;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        font-weight: bold;               /* 加粗 */
        color: #d71446;
      }

      :deep(.msg-time) {
        font-size: 12px;
        margin-top: 6px;
      }
    }
  }
}


:deep(.t-chat__detail) {
  max-width: 98% !important;
}

:deep(.t-chat__inner.user) {
  margin-right: 10px;
  .t-chat__text {
    background-color: #e6e6e6 !important;
  }
}

:deep(.t-chat__text) {
  background-color: transparent !important;
  font-size: 14px;
  line-height: 1.6;
}

:deep(.t-chat__actions-margin *) {
  background-color: transparent !important;
  border: none !important; /* 无边框 */
}

/* ========== 底部输入区 (优化修改重点) ========== */
.bottom-input-section {
  padding: 8px 8px 6px;  /* 增大底部区域整体padding */
  background: transparent;

  .input-container {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border: 1px solid #e7e7e7;
    overflow: hidden;
    padding: 16px 20px;  /* 增大容器内边距 */

    .second-row-group {
      width: 100%;        /* 强制占满一行，从而挤到下一行 */
      display: flex;      /* 内部依然保持横向排列 */
      gap: 16px;          /* 内部间距 */
      margin-top: -2px;    /* 可选：与上一行保持一点距离 */
    }
    /* 配置行 - 上下分布，每行独立 */
    .config-row {
      display: flex;
      //flex-wrap: wrap;     /* 允许换行：这是关键 */
      align-items: center;
      gap: 8px 16px;
      padding: 4px 0;  /* 增大行间距 */
      border-bottom: 1px dashed #e8e8e8;

      &:last-of-type {
        border-bottom: none;
        padding-bottom: 4px;
      }

      &:first-of-type {
        padding-top: 2px;
      }

      .config-label {
        font-size: 13px;
        color: #555555;
        font-weight: 600;
        white-space: nowrap;
        min-width: 76px;  /* 标签宽度统一 */
      }

      :deep(.t-checkbox) {
        margin-right: 14px;
        font-size: 14px;
        color: #555555;

        .t-checkbox__label {
          padding-left: 8px;
        }
      }

      :deep(.t-select) {
        font-size: 14px;
      }

      :deep(.t-button) {
        height: 36px;
        padding: 0 18px;
      }

      .file-name {
        font-size: 13px;
        color: #0052d9;
        margin-left: 10px;
        padding: 5px 12px;
        background: #ebf1fb;
        border-radius: 4px;
        font-weight: 500;
      }
    }

    /* 输入框区域 (增大) */
    .textarea-area {
      padding: 12px 0 10px;  /* 增大输入框上下间距 */
      margin-top: 8px;

      :deep(.t-textarea) {
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        box-shadow: none;
        resize: none;
        background: #fafafa;
        transition: all 0.25s;

        &:focus-within {
          border-color: #0052d9;
          background: #ffffff;
          box-shadow: 0 0 0 1px rgba(0, 82, 217, 0.1);
        }

        textarea {
          padding: 10px 12px !important;  /* 增大内边距 */
          font-size: 13px;
          color: #333333;
          line-height: 1.6;
          min-height: 60px;  /* 增大最小高度 */

          &::placeholder {
            color: #bbbbbb;
          }
        }
      }
    }

    /* 底部操作栏 */
    .input-footer {
      padding: 8px 0 2px;  /* 增大底部栏间距 */
      margin-top: 8px;
      border-top: 1px solid #e8e8e8;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .footer-left {
        .footer-tip {
          font-size: 12px;
          color: #999999;
        }
      }

      .footer-right {
        display: flex;
        gap: 8px;

        :deep(.t-button) {
          padding: 0 10px;
          height: 28px;  /* 增大按钮高度 */
          font-size: 13px;
          font-weight: 500;
        }
      }
    }
  }
}

/* 历史对话面板 */
.history-panel {
  .history-item {
    display: flex;
    align-items: flex-start;
    padding: 16px 14px;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: #f5f6f7;
    }

    .history-icon {
      width: 40px;
      height: 40px;
      background: #ebf1fb;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 14px;
      flex-shrink: 0;

      svg {
        fill: #0052d9;
      }
    }

    .history-info {
      flex: 1;
      min-width: 0;

      .history-title {
        font-size: 14px;
        color: #333333;
        margin-bottom: 6px;
        font-weight: 500;
      }

      .history-time {
        font-size: 12px;
        color: #999999;
      }
    }
  }
}

/* 动画 */
@keyframes flashing {
  0%, 80%, 100% { opacity: 0.4; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
</style>
