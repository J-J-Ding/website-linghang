<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-select
                v-model="selectedBoardNameOption"
                filterable=""
                style="width: 300px;"
                label="单板: ">
                @change="handleBoardChange"> <!-- 添加change事件 -->
                    <t-option v-for="option in boardNameOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-button @click="openBoardChatDialog">单板智能助手</t-button>
                <!-- <t-button @click="openAddDialog">新增</t-button>
                <t-button @click="onBatchDelete">批量删除</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button @click="onBatchOutput">批量导出</t-button> -->
                <!-- 新增通用智能助手按钮 -->
                <t-button 
                  class="general-assistant-btn precise-spacing"
                  theme="primary" 
                  @click="openGeneralAssistantDialog">
                  通用智能助手
                </t-button>

                <!-- 新增代码守护助手测试按钮 -->
                <t-button
                  class="codelens-assistant-btn precise-spacing"
                  theme="primary"
                  @click="openCodelensAssistantDialog">
                  代码守护助手测试
                </t-button>

                <t-button
                  class="data-board-btn precise-spacing"
                  theme="primary" 
                  @click="jumpToBoardChatTablePage">
                  数据看板
                </t-button>
            </t-space>
            <p> </p>
        </t-space>
        <t-table
        ref="tableRef"
        row-key="id"
        :columns="updateColumnList"
        :data="filterDataList"
        :selected-row-keys="selectedRowKeyList"
        :select-on-row-click="false"
        :max-height="tableHeight"
        bordered
        resizable
        :filter-value="filterValue"
        @select-change="handleSelectChange"
        @filter-change="onFilterChange">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-table>

        <t-drawer
        v-model:visible="drawVisible"
        size="1000px"
        :footer="false"
        :close-btn="true"
        :size-draggable="true">
            <t-tooltip content="新建对话" placement="top-left">
                <t-button
                size="large"
                theme="primary"
                shape="circle"
                variant="base"
                @click="newChat">
                <icon name="plus" />
                </t-button>
            </t-tooltip>
            <template #header>
                <span class="title">
                Hi,&nbsp;我是
                <span style="color: #1a16fc; font-weight: 600">
                    {{ selectedBoardNameOption || '' }}
                </span>
                单板智能助手
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
                    >
                    <template #content>
                        <t-chat-reasoning
                        v-if="item.reasoning?.length > 0"
                        expand-icon-placement="right"
                        :collapse-panel-props="{
                            header: renderHeader(index === 0 && isStreamLoad, item),
                            content: renderReasoningContent(item.reasoning),
                        }"
                        @expand-change="handleChange"
                        >
                        </t-chat-reasoning>
                        <t-chat-content v-if="item.content.length > 0" :content="item.content" />
                        <!-- 反馈状态提示 -->
                        <div v-if="item.feedbackStatus" class="feedback-status-tip">
                          <t-tag 
                            :theme="item.feedbackStatus === '已点赞' ? 'success' : 
                                    item.feedbackStatus === '已点踩' ? 'warning' : 'danger'"
                            size="small"
                          >
                            {{ item.feedbackStatus }}
                          </t-tag>
                        </div>
                        <!-- 显示反馈状态 -->
                        <div v-if="item.feedback" class="feedback-status">
                            <t-tag v-if="item.feedback === 'good'" theme="success" variant="light">
                                <template #icon><icon name="thumb-up" /></template>
                                已点赞
                            </t-tag>
                            <t-tag v-else-if="item.feedback === 'bad'" theme="warning" variant="light">
                                <template #icon><icon name="thumb-down" /></template>
                                已点踩
                            </t-tag>
                            <span v-if="item.feedbackTime" class="feedback-time">({{ item.feedbackTime }})</span>
                        </div>
                    </template>
                    <template #actions>
                        <t-chat-action
                          :content="item.content"
                          :operation-btn="['good', 'bad', 'replay', 'copy']"
                          :disabled="getDisabledButtons(item.feedback)"
                          @operation="(type, options) => handleOperation(type, { ...options, index })"
                        />
                        <!-- 添加反馈输入框 -->
                        <div v-if="showFeedbackInput === index" class="feedback-input-container">
                            <div class="feedback-input-wrapper">
                                <t-textarea
                                    v-model="feedbackInputText"
                                    placeholder="请输入您的反馈意见..."
                                    :autosize="{ minRows: 2, maxRows: 4 }"
                                    class="feedback-textarea"
                                />
                                <div class="feedback-actions">
                                    <t-button size="small" @click="submitFeedback(index)">提交反馈</t-button>
                                    <t-button size="small" variant="outline" @click="cancelFeedback">取消</t-button>
                                </div>
                            </div>
                            <!-- 反馈状态提示显示在反馈框右边 -->
                            <div v-if="showFeedbackSuccess === index" class="feedback-success-tip">
                                <t-tag theme="success" size="small">
                                    反馈提交成功
                                </t-tag>
                            </div>
                        </div>
                    </template>
                    </t-chat-item>
                </template>
                <template #footer>
                    <t-chat-sender
                    v-model="inputText"
                    :stop-disabled="loading"
                    :textarea-props="{ placeholder: '请输入消息...' }"
                    @send="inputEnter">
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

        <!-- 新增通用智能助手抽屉 -->
        <t-drawer
        v-model:visible="generalDrawVisible"
        size="1000px"
        :footer="false"
        :close-btn="true"
        :size-draggable="true">
            <t-tooltip content="新建对话" placement="top-left">
                <t-button
                size="large"
                theme="primary"
                shape="circle"
                variant="base"
                @click="newGeneralChat">
                <icon name="plus" />
                </t-button>
            </t-tooltip>
            <template #header>
                <span class="title">
                Hi,&nbsp;我是
                <span style="color: #1a16fc; font-weight: 600">
                    通用智能助手
                </span>
                </span>
            </template>
            <div class="component-chat-box">
                <t-chat ref="generalChatRef" layout="both" :clear-history="false" @scroll="handleGeneralChatScroll">
                <template v-for="(item, index) in generalChatList" :key="index">
                    <t-chat-item
                    :variant="item.role === 'user' ? 'base' : 'base'"
                    :avatar="item.avatar"
                    :name="item.name"
                    :role="item.role"
                    :datetime="item.datetime"
                    :text-loading="index === 0 && generalLoading"
                    >
                    <template #content>
                        <t-chat-reasoning
                        v-if="item.reasoning?.length > 0"
                        expand-icon-placement="right"
                        :collapse-panel-props="{
                            header: renderHeader(index === 0 && generalIsStreamLoad, item),
                            content: renderReasoningContent(item.reasoning),
                        }"
                        @expand-change="handleChange"
                        >
                        </t-chat-reasoning>
                        <t-chat-content v-if="item.content.length > 0" :content="item.content" />
                        <!-- 反馈状态提示 -->
                        <div v-if="item.feedbackStatus" class="feedback-status-tip">
                          <t-tag 
                            :theme="item.feedbackStatus === '已点赞' ? 'success' : 
                                    item.feedbackStatus === '已点踩' ? 'warning' : 'danger'"
                            size="small"
                          >
                            {{ item.feedbackStatus }}
                          </t-tag>
                        </div>
                        <!-- 显示反馈状态 -->
                        <div v-if="item.feedback" class="feedback-status">
                            <t-tag v-if="item.feedback === 'good'" theme="success" variant="light">
                                <template #icon><icon name="thumb-up" /></template>
                                已点赞
                            </t-tag>
                            <t-tag v-else-if="item.feedback === 'bad'" theme="warning" variant="light">
                                <template #icon><icon name="thumb-down" /></template>
                                已点踩
                            </t-tag>
                            <span v-if="item.feedbackTime" class="feedback-time">({{ item.feedbackTime }})</span>
                        </div>
                    </template>
                    <template #actions>
                        <t-chat-action
                        :content="item.content"
                        :operation-btn="['good', 'bad', 'replay', 'copy']"
                        :disabled="getDisabledButtons(item.feedback)"
                        @operation="(type, options) => handleGeneralOperation(type, { ...options, index })"
                        />
                        <!-- 添加反馈输入框 -->
                        <div v-if="generalShowFeedbackInput === index" class="feedback-input-container">
                            <div class="feedback-input-wrapper">
                                <t-textarea
                                    v-model="generalFeedbackInputText"
                                    placeholder="请输入您的反馈意见..."
                                    :autosize="{ minRows: 2, maxRows: 4 }"
                                    class="feedback-textarea"
                                />
                                <div class="feedback-actions">
                                    <t-button size="small" @click="submitGeneralFeedback(index)">提交反馈</t-button>
                                    <t-button size="small" variant="outline" @click="cancelGeneralFeedback">取消</t-button>
                                </div>
                            </div>
                            <!-- 反馈状态提示显示在反馈框右边 -->
                            <div v-if="generalShowFeedbackSuccess === index" class="feedback-success-tip">
                                <t-tag theme="success" size="small">
                                    反馈提交成功
                                </t-tag>
                            </div>
                        </div>
                    </template>
                    </t-chat-item>
                </template>
                <template #footer>
                    <t-chat-sender
                    v-model="generalInputText"
                    :stop-disabled="generalLoading"
                    :textarea-props="{ placeholder: '请输入消息...' }"
                    @send="generalInputEnter">
                    </t-chat-sender>
                </template>
                </t-chat>
                <t-button v-show="generalIsShowToBottom" variant="text" class="bottomBtn" @click="generalBackBottom">
                <div class="to-bottom">
                    <ArrowDownIcon />
                </div>
                </t-button>
            </div>
        </t-drawer>

        <!-- 新增代码守护助手测试抽屉 -->
        <t-drawer
        v-model:visible="codelensDrawVisible"
        size="1000px"
        :footer="false"
        :close-btn="true"
        :size-draggable="true">
            <t-tooltip content="新建对话" placement="top-left">
                <t-button
                size="large"
                theme="primary"
                shape="circle"
                variant="base"
                @click="newCodelensChat">
                <icon name="plus" />
                </t-button>
            </t-tooltip>
            <template #header>
                <span class="title">
                Hi,&nbsp;我是
                <span style="color: #1a16fc; font-weight: 600">
                    代码守护助手测试
                </span>
                </span>
            </template>
            <div class="component-chat-box">
                <t-chat ref="codelensChatRef" layout="both" :clear-history="false" @scroll="handleCodelensChatScroll">
                <template v-for="(item, index) in codelensChatList" :key="index">
                    <t-chat-item
                    :variant="item.role === 'user' ? 'base' : 'base'"
                    :avatar="item.avatar"
                    :name="item.name"
                    :role="item.role"
                    :datetime="item.datetime"
                    :text-loading="index === 0 && codelensLoading"
                    >
                    <template #content>
                        <t-chat-reasoning
                        v-if="item.reasoning?.length > 0"
                        expand-icon-placement="right"
                        :collapse-panel-props="{
                            header: renderHeader(index === 0 && codelensIsStreamLoad, item),
                            content: renderReasoningContent(item.reasoning),
                        }"
                        @expand-change="handleChange"
                        >
                        </t-chat-reasoning>
                        <t-chat-content v-if="item.content.length > 0" :content="item.content" />
                        <!-- 反馈状态提示 -->
                        <div v-if="item.feedbackStatus" class="feedback-status-tip">
                          <t-tag
                            :theme="item.feedbackStatus === '已点赞' ? 'success' :
                                    item.feedbackStatus === '已点踩' ? 'warning' : 'danger'"
                            size="small"
                          >
                            {{ item.feedbackStatus }}
                          </t-tag>
                        </div>
                        <!-- 显示反馈状态 -->
                        <div v-if="item.feedback" class="feedback-status">
                            <t-tag v-if="item.feedback === 'good'" theme="success" variant="light">
                                <template #icon><icon name="thumb-up" /></template>
                                已点赞
                            </t-tag>
                            <t-tag v-else-if="item.feedback === 'bad'" theme="warning" variant="light">
                                <template #icon><icon name="thumb-down" /></template>
                                已点踩
                            </t-tag>
                            <span v-if="item.feedbackTime" class="feedback-time">({{ item.feedbackTime }})</span>
                        </div>
                    </template>
                    <template #actions>
                        <t-chat-action
                        :content="item.content"
                        :operation-btn="['good', 'bad', 'replay', 'copy']"
                        :disabled="getDisabledButtons(item.feedback)"
                        @operation="(type, options) => handleCodelensOperation(type, { ...options, index })"
                        />
                        <!-- 添加反馈输入框 -->
                        <div v-if="codelensShowFeedbackInput === index" class="feedback-input-container">
                            <div class="feedback-input-wrapper">
                                <t-textarea
                                    v-model="codelensFeedbackInputText"
                                    placeholder="请输入您的反馈意见..."
                                    :autosize="{ minRows: 2, maxRows: 4 }"
                                    class="feedback-textarea"
                                />
                                <div class="feedback-actions">
                                    <t-button size="small" @click="submitCodelensFeedback(index)">提交反馈</t-button>
                                    <t-button size="small" variant="outline" @click="cancelCodelensFeedback">取消</t-button>
                                </div>
                            </div>
                            <!-- 反馈状态提示显示在反馈框右边 -->
                            <div v-if="codelensShowFeedbackSuccess === index" class="feedback-success-tip">
                                <t-tag theme="success" size="small">
                                    反馈提交成功
                                </t-tag>
                            </div>
                        </div>
                    </template>
                    </t-chat-item>
                </template>
                <template #footer>
                    <t-chat-sender
                    v-model="codelensInputText"
                    :stop-disabled="codelensLoading"
                    :textarea-props="{ placeholder: '请输入消息...' }"
                    @send="codelensInputEnter">
                    </t-chat-sender>
                </template>
                </t-chat>
                <t-button v-show="codelensIsShowToBottom" variant="text" class="bottomBtn" @click="codelensBackBottom">
                <div class="to-bottom">
                    <ArrowDownIcon />
                </div>
                </t-button>
            </div>
        </t-drawer>

        <t-dialog
        v-model:visible="queryDialogVisible"
        :width="800"
        theme="info">
            <template #header>
                <t-space>
                    <span>查看数据</span>
                </t-space>
            </template>
            <div class="query-form">
                <t-form :data="queryFormData" layout="vertical" label-width="250px">
                    <t-form-item label="单板名称" name="board">
                        <t-textarea v-model="queryFormData.board" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item
                    v-for="field in allFactorOptionList"
                    :key="field"
                    :label="field"
                    :name="field">
                        <t-textarea v-model="queryFormData[field]" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="操作人" name="operator_person">
                        <t-input v-model="queryFormData.operator_person" :readonly="true"/>
                    </t-form-item>
                    <t-form-item label="更新时间" name="update_time">
                        <t-input v-model="queryFormData.update_time" :readonly="true"/>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="queryDialogVisible=false">关闭</t-button>
            </template>
        </t-dialog>
    </div>
</template>


<script setup lang="jsx">
import { ref, onMounted, markRaw, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { MessagePlugin, DatePicker, Input, Select } from 'tdesign-vue-next';
import { pubCalculateTableHeight } from '@/utils/pub';
import { queryBoardTreeByParams, queryBoardTreeFactorList, queryBoardTreeFactorValueDict, queryBoardTreeAllFactorValueDict} from '@/api/electric.js';
import { boardChatChatRequest, boardChatCreateChatEventSource, get_support_list, BoardChatDashboardRequest, boardChatFeedbackRequest, 
         generalChatRequest, generalChatCreateChatEventSource, generalChatFeedbackRequest, generalChatDashboardRequest} from '@/api/boardChat.js';
import axios from 'axios';
import { SystemSumIcon, Icon, ArrowDownIcon, CheckCircleIcon } from 'tdesign-icons-vue-next';
import { v4 as uuidv4 } from 'uuid';

const jumpToBoardChatTablePage = () => {
  router.push('/ai/boardChat/BoardChatTable');
};

const router = useRouter();
const user = useUserStore();

// 单板智能助手反馈相关
const showFeedbackInput = ref(-1); // 显示反馈输入框的索引
const feedbackInputText = ref(''); // 反馈输入内容
const pendingFeedbackType = ref(''); // 待提交的反馈类型
const pendingFeedbackIndex = ref(-1); // 待提交的反馈索引
const showFeedbackSuccess = ref(-1); // 显示反馈成功提示的索引

// 通用智能助手反馈相关
const generalShowFeedbackInput = ref(-1); // 通用助手反馈输入框索引
const generalFeedbackInputText = ref(''); // 通用助手反馈输入内容
const generalPendingFeedbackType = ref(''); // 通用助手待提交反馈类型
const generalPendingFeedbackIndex = ref(-1); // 通用助手待提交反馈索引
const generalShowFeedbackSuccess = ref(-1); // 通用助手显示反馈成功提示的索引

// 通用智能助手相关
const generalDrawVisible = ref(false);
const generalIsShowToBottom = ref(false);
const generalChatList = ref([]);
let generalSessionId = uuidv4();
const generalChatRef = ref(null);
const generalInputText = ref('');
const generalLoading = ref(false);
const generalIsStreamLoad = ref(false);

// 代码守护助手测试相关
const codelensDrawVisible = ref(false);
const codelensIsShowToBottom = ref(false);
const codelensChatList = ref([]);
let codelensSessionId = uuidv4();
const codelensChatRef = ref(null);
const codelensInputText = ref('');
const codelensLoading = ref(false);
const codelensIsStreamLoad = ref(false);

// 代码守护助手测试反馈相关
const codelensShowFeedbackInput = ref(-1);
const codelensFeedbackInputText = ref('');
const codelensPendingFeedbackType = ref('');
const codelensPendingFeedbackIndex = ref(-1);
const codelensShowFeedbackSuccess = ref(-1);

// 打开通用智能助手对话框
const openGeneralAssistantDialog = () => {
    generalDrawVisible.value = true;
    console.log('打开通用智能助手');
    GeneralChatRequest();
};

const GeneralChatRequest = async () => {
    try {
        const requestParams = {
            user_id: user.userInfo.name,
            board_name: 'all', // 标识为通用助手
        };
        await generalChatDashboardRequest(requestParams);
        console.log('通用智能助手访问记录成功');
    } catch (error) {
        console.log('通用智能助手信息记录失败，请重试', error);
    }
};

// 通用助手新建对话
const newGeneralChat = () => {
    generalSessionId = uuidv4();
    generalChatList.value = [];
    generalInputText.value = '';
    generalLoading.value = false;
    generalIsStreamLoad.value = false;
    MessagePlugin.info('创建对话成功');
};

// 通用助手滚动处理
const handleGeneralChatScroll = function ({ e }) {
    const scrollTop = e.target.scrollTop;
    generalIsShowToBottom.value = scrollTop < 0;
};

// 通用助手回到底部
const generalBackBottom = () => {
    generalChatRef.value.scrollToBottom({
        behavior: 'smooth',
    });
};

// 获取需要禁用的按钮列表
const getDisabledButtons = (feedback) => {
  if (!feedback) return [];

  // 如果已经有反馈，只禁用点赞和点踩按钮
  return ['good', 'bad'];
};

// 通用智能助手操作处理
const handleGeneralOperation = async (type, options) => {
  const { content, index } = options;

  // 如果是点赞或点踩，显示反馈输入框
  if (type === 'good' || type === 'bad') {
    console.log('通用助手点击了反馈按钮:', type, '索引:', index);
    
    // 确保重置其他可能打开的反馈框
    generalShowFeedbackInput.value = -1;
    generalFeedbackInputText.value = '';
    
    // 使用setTimeout确保DOM更新
    setTimeout(() => {
      generalShowFeedbackInput.value = index;
      generalPendingFeedbackType.value = type;
      generalPendingFeedbackIndex.value = index;
      generalFeedbackInputText.value = ''; // 清空之前的输入
      
      console.log('设置通用助手反馈框显示，索引:', generalShowFeedbackInput.value);
    }, 0 );
    return;
  }

  // 其他操作（复制、重播）保持原有逻辑
  if (type === 'copy') {
    try {
      await navigator.clipboard.writeText(content);
      MessagePlugin.success('已复制到剪贴板');
    } catch (err) {
      console.error('复制失败:', err);
      MessagePlugin.error('复制失败');
    }
  } else if (type === 'replay') {
    // 重播逻辑
    generalInputText.value = content;
    generalInputEnter(content);
  }
};

// 提交通用智能助手反馈
const submitGeneralFeedback = async (index) => {
  if (generalLoading.value) return;

  const feedbackItem = generalChatList.value[index];
  if (!feedbackItem) return;

  try {
    generalLoading.value = true;
    const messageIdToSend = feedbackItem.message_id || uuidv4();
    // 构建完整的反馈数据
    const feedback_data = {
      user_id: user.userInfo.name,
      session_id: generalSessionId,
      board_name: 'all', // 通用助手标识
      message_id: messageIdToSend,
      user_question: generalChatList.value[index + 1]?.content || '', // 用户的问题
      ai_answer: feedbackItem.content, // AI的回答
      feedback_type: generalPendingFeedbackType.value,
      feedback_content: generalFeedbackInputText.value, // 用户输入的反馈内容
      timestamp: new Date().toISOString()
    };

    console.log('发送通用助手完整反馈数据:', feedback_data);
    
    // 发送反馈到后端
    const response = await generalChatFeedbackRequest(feedback_data);
    
    if (response.status === 'success') {
      // 更新UI状态
      feedbackItem.feedback = generalPendingFeedbackType.value;
      feedbackItem.feedbackTime = new Date().toLocaleString();
      feedbackItem.feedbackContent = generalFeedbackInputText.value; // 保存反馈内容
      // 显示反馈成功提示
      generalShowFeedbackSuccess.value = index;
   
      // 3秒后清除状态提示
      setTimeout(() => {
        generalShowFeedbackSuccess.value = -1;
        // 关闭反馈输入框
        generalShowFeedbackInput.value = -1;
        generalFeedbackInputText.value = '';
        generalPendingFeedbackType.value = '';
        generalPendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } catch (error) {
    console.error('通用助手反馈提交错误:', error);
    MessagePlugin.error('反馈提交失败，请重试');
    
    // 错误提示
    if (generalChatList.value[index]) {
      generalChatList.value[index].feedbackStatus = '反馈失败';
      setTimeout(() => {
        if (generalChatList.value[index]) {
          generalChatList.value[index].feedbackStatus = '';
        }
        // 关闭反馈输入框
        generalShowFeedbackInput.value = -1;
        generalFeedbackInputText.value = '';
        generalPendingFeedbackType.value = '';
        generalPendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } finally {
    generalLoading.value = false;
  }
};

// 取消通用智能助手反馈
const cancelGeneralFeedback = () => {
  generalShowFeedbackInput.value = -1;
  generalFeedbackInputText.value = '';
  generalPendingFeedbackType.value = '';
  generalPendingFeedbackIndex.value = -1;
};

// 通用助手输入处理
const generalInputEnter = function (inputValue) {
    if (generalIsStreamLoad.value) {
        return;
    }

    if (!inputValue) {
        return;
    }

    const params = {
        avatar: '/src/assets/assets-user3.png',
        datetime: new Date().toLocaleString(),
        content: inputValue,
        reasoning: '',
        role: 'user',
    };

    generalChatList.value.unshift(params);

    const params2 = {
        avatar: '/src/assets/assets-ai2.png',
        content: '',
        reasoning: '',
        role: 'assistant',
    };

    generalChatList.value.unshift(params2);

    handleGeneralData(inputValue);
    generalInputText.value = '';
};

// 通用助手数据处理
const handleGeneralData = async (inputValue) => {
    generalLoading.value = true;
    generalIsStreamLoad.value = true;

    const lastItem = generalChatList.value[0];
    // 存储接收到的message_id
    let receivedMessageId = '';
    // 通用助手传入空board_name或特定标识
    const contextObj = {board_name: 'all', answer: inputValue};
    const context = JSON.stringify(contextObj);

    let buffer = '';
    let reasoningBuffer = '';
    let isFlushing = false;
    let isInThinkTag = false;
    let tempBuffer = '';
    let eventSource = null;
    let startTime = Date.now();

    function flushBuffer() {
        if (buffer && lastItem) {
            lastItem.content += buffer;
            buffer = '';
        }
        if (reasoningBuffer && lastItem) {
            lastItem.reasoning += reasoningBuffer;
            reasoningBuffer = '';
        }
        isFlushing = false;
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);

        const data = await generalChatRequest(
            {
                user: user.userInfo.name,
                session_id: generalSessionId,
                board_name: 'all', // all值表示通用助手
                content: context,
            },
            { signal: controller.signal }
        );

        clearTimeout(timeoutId);

        if (data.status === 'success') {
            eventSource = generalChatCreateChatEventSource(generalSessionId, {
                board_name: 'all' // all值表示通用助手
            });

            const cleanUp = () => {
                generalLoading.value = false;
                generalIsStreamLoad.value = false;

                if (eventSource) eventSource.close();

                nextTick().then(() => {
                    const textareaEl = document.querySelector('.t-textarea__inner');
                    if (textareaEl) textareaEl.focus();
                });
            };

            eventSource.onmessage = (event) => {
                if (event.data === '[DONE]') {
                    if (tempBuffer) {
                        if (isInThinkTag) {
                            reasoningBuffer += tempBuffer;
                        } else {
                            buffer += tempBuffer;
                        }
                        tempBuffer = '';
                    }

                    if (buffer && lastItem) {
                        lastItem.content += buffer;
                        buffer = '';
                    }
                    if (reasoningBuffer && lastItem) {
                        lastItem.reasoning += reasoningBuffer;
                        reasoningBuffer = '';
                    }
                    // 将message_id存储到聊天项中
                    if (receivedMessageId && lastItem) {
                        lastItem.message_id = receivedMessageId;
                    }
                    cleanUp();
                    return;
                }

                try {
                    const data = JSON.parse(event.data);
                    if (data.message_id) {
                        // 接收并存储message_id
                        receivedMessageId = data.message_id;
                        if (lastItem) {
                            lastItem.message_id = receivedMessageId;
                        }
                        console.log('通用助手接收到message_id:', receivedMessageId);
                    }
                    if (data.error) {
                        lastItem.role = 'error';
                        lastItem.content = `服务器错误: ${data.error}`;
                        cleanUp();
                    } else if (data.text) {
                        tempBuffer += data.text;
                        while (tempBuffer.length > 0) {
                            if (!isInThinkTag) {
                                const thinkStartIndex = tempBuffer.indexOf("<think>");
                                if (thinkStartIndex !== -1) {
                                    buffer += tempBuffer.substring(0, thinkStartIndex);
                                    tempBuffer = tempBuffer.substring(thinkStartIndex + 7);
                                    isInThinkTag = true;
                                    generalIsStreamLoad.value = true;
                                } else {
                                    buffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            } else {
                                const thinkEndIndex = tempBuffer.indexOf("</think>");
                                if (thinkEndIndex !== -1) {
                                    reasoningBuffer += tempBuffer.substring(0, thinkEndIndex);
                                    tempBuffer = tempBuffer.substring(thinkEndIndex + 8);
                                    isInThinkTag = false;
                                    generalIsStreamLoad.value = false;
                                    const endTime = Date.now();
                                    lastItem.duration = ((endTime - startTime) / 1000).toFixed(2);
                                } else {
                                    reasoningBuffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            }
                        }

                        if (!isFlushing) {
                            isFlushing = true;
                            setTimeout(flushBuffer, 50);
                        }
                    }
                } catch (e) {
                    console.error('解析通用助手SSE数据失败:', e);
                    lastItem.role = 'error';
                    lastItem.content = '数据解析失败';
                    cleanUp();
                }
            };

            eventSource.onerror = (err) => {
                console.error('通用助手SSE连接错误:', err);
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
        console.error('通用助手请求异常:', error);

        if (error.name === 'AbortError') {
            lastItem.content = '请求超时，请重试';
        } else {
            lastItem.content = `网络错误: ${error.message || '未知错误'}`;
        }

        lastItem.role = 'error';
        lastItem.datetime = new Date().toLocaleString();

        if (eventSource) eventSource.close();
    } finally {
        generalLoading.value = false;
        generalIsStreamLoad.value = false;
    }
};

// 打开代码守护助手测试对话框
const openCodelensAssistantDialog = () => {
    codelensDrawVisible.value = true;
    console.log('打开代码守护助手测试');
    CodelensChatRequest();
};

const CodelensChatRequest = async () => {
    try {
        const requestParams = {
            user_id: user.userInfo.name,
            board_name: 'codelens',
        };
        await generalChatDashboardRequest(requestParams);
        console.log('代码守护助手测试访问记录成功');
    } catch (error) {
        console.log('代码守护助手测试信息记录失败，请重试', error);
    }
};

// 代码守护助手测试新建对话
const newCodelensChat = () => {
    codelensSessionId = uuidv4();
    codelensChatList.value = [];
    codelensInputText.value = '';
    codelensLoading.value = false;
    codelensIsStreamLoad.value = false;
    MessagePlugin.info('创建对话成功');
};

// 代码守护助手测试滚动处理
const handleCodelensChatScroll = function ({ e }) {
    const scrollTop = e.target.scrollTop;
    codelensIsShowToBottom.value = scrollTop < 0;
};

// 代码守护助手测试回到底部
const codelensBackBottom = () => {
    codelensChatRef.value.scrollToBottom({
        behavior: 'smooth',
    });
};

// 代码守护助手测试操作处理
const handleCodelensOperation = async (type, options) => {
  const { content, index } = options;

  if (type === 'good' || type === 'bad') {
    console.log('代码守护助手测试点击了反馈按钮:', type, '索引:', index);

    codelensShowFeedbackInput.value = -1;
    codelensFeedbackInputText.value = '';

    setTimeout(() => {
      codelensShowFeedbackInput.value = index;
      codelensPendingFeedbackType.value = type;
      codelensPendingFeedbackIndex.value = index;
      codelensFeedbackInputText.value = '';
    }, 0);
    return;
  }

  if (type === 'copy') {
    try {
      await navigator.clipboard.writeText(content);
      MessagePlugin.success('已复制到剪贴板');
    } catch (err) {
      console.error('复制失败:', err);
      MessagePlugin.error('复制失败');
    }
  } else if (type === 'replay') {
    codelensInputText.value = content;
    codelensInputEnter(content);
  }
};

// 提交代码守护助手测试反馈
const submitCodelensFeedback = async (index) => {
  if (codelensLoading.value) return;

  const feedbackItem = codelensChatList.value[index];
  if (!feedbackItem) return;

  try {
    codelensLoading.value = true;
    const messageIdToSend = feedbackItem.message_id || uuidv4();
    const feedback_data = {
      user_id: user.userInfo.name,
      session_id: codelensSessionId,
      board_name: 'codelens',
      message_id: messageIdToSend,
      user_question: codelensChatList.value[index + 1]?.content || '',
      ai_answer: feedbackItem.content,
      feedback_type: codelensPendingFeedbackType.value,
      feedback_content: codelensFeedbackInputText.value,
      timestamp: new Date().toISOString()
    };

    console.log('发送代码守护助手测试完整反馈数据:', feedback_data);

    const response = await generalChatFeedbackRequest(feedback_data);

    if (response.status === 'success') {
      feedbackItem.feedback = codelensPendingFeedbackType.value;
      feedbackItem.feedbackTime = new Date().toLocaleString();
      feedbackItem.feedbackContent = codelensFeedbackInputText.value;
      codelensShowFeedbackSuccess.value = index;

      setTimeout(() => {
        codelensShowFeedbackSuccess.value = -1;
        codelensShowFeedbackInput.value = -1;
        codelensFeedbackInputText.value = '';
        codelensPendingFeedbackType.value = '';
        codelensPendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } catch (error) {
    console.error('代码守护助手测试反馈提交错误:', error);
    MessagePlugin.error('反馈提交失败，请重试');

    if (codelensChatList.value[index]) {
      codelensChatList.value[index].feedbackStatus = '反馈失败';
      setTimeout(() => {
        if (codelensChatList.value[index]) {
          codelensChatList.value[index].feedbackStatus = '';
        }
        codelensShowFeedbackInput.value = -1;
        codelensFeedbackInputText.value = '';
        codelensPendingFeedbackType.value = '';
        codelensPendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } finally {
    codelensLoading.value = false;
  }
};

// 取消代码守护助手测试反馈
const cancelCodelensFeedback = () => {
  codelensShowFeedbackInput.value = -1;
  codelensFeedbackInputText.value = '';
  codelensPendingFeedbackType.value = '';
  codelensPendingFeedbackIndex.value = -1;
};

// 代码守护助手测试输入处理
const codelensInputEnter = function (inputValue) {
    if (codelensIsStreamLoad.value) {
        return;
    }

    if (!inputValue) {
        return;
    }

    const params = {
        avatar: '/src/assets/assets-user3.png',
        datetime: new Date().toLocaleString(),
        content: inputValue,
        reasoning: '',
        role: 'user',
    };

    codelensChatList.value.unshift(params);

    const params2 = {
        avatar: '/src/assets/assets-ai2.png',
        content: '',
        reasoning: '',
        role: 'assistant',
    };

    codelensChatList.value.unshift(params2);

    handleCodelensData(inputValue);
    codelensInputText.value = '';
};

// 代码守护助手测试数据处理
const handleCodelensData = async (inputValue) => {
    codelensLoading.value = true;
    codelensIsStreamLoad.value = true;

    const lastItem = codelensChatList.value[0];
    let receivedMessageId = '';
    const contextObj = {board_name: 'codelens', answer: inputValue};
    const context = JSON.stringify(contextObj);

    let buffer = '';
    let reasoningBuffer = '';
    let isFlushing = false;
    let isInThinkTag = false;
    let tempBuffer = '';
    let eventSource = null;
    let startTime = Date.now();

    function flushBuffer() {
        if (buffer && lastItem) {
            lastItem.content += buffer;
            buffer = '';
        }
        if (reasoningBuffer && lastItem) {
            lastItem.reasoning += reasoningBuffer;
            reasoningBuffer = '';
        }
        isFlushing = false;
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);

        const data = await generalChatRequest(
            {
                user: user.userInfo.name,
                session_id: codelensSessionId,
                board_name: 'codelens',
                content: context,
            },
            { signal: controller.signal }
        );

        clearTimeout(timeoutId);

        if (data.status === 'success') {
            eventSource = generalChatCreateChatEventSource(codelensSessionId, {
                board_name: 'codelens'
            });

            const cleanUp = () => {
                codelensLoading.value = false;
                codelensIsStreamLoad.value = false;

                if (eventSource) eventSource.close();

                nextTick().then(() => {
                    const textareaEl = document.querySelector('.t-textarea__inner');
                    if (textareaEl) textareaEl.focus();
                });
            };

            eventSource.onmessage = (event) => {
                if (event.data === '[DONE]') {
                    if (tempBuffer) {
                        if (isInThinkTag) {
                            reasoningBuffer += tempBuffer;
                        } else {
                            buffer += tempBuffer;
                        }
                        tempBuffer = '';
                    }

                    if (buffer && lastItem) {
                        lastItem.content += buffer;
                        buffer = '';
                    }
                    if (reasoningBuffer && lastItem) {
                        lastItem.reasoning += reasoningBuffer;
                        reasoningBuffer = '';
                    }
                    if (receivedMessageId && lastItem) {
                        lastItem.message_id = receivedMessageId;
                    }
                    cleanUp();
                    return;
                }

                try {
                    const data = JSON.parse(event.data);
                    if (data.message_id) {
                        receivedMessageId = data.message_id;
                        if (lastItem) {
                            lastItem.message_id = receivedMessageId;
                        }
                        console.log('代码守护助手测试接收到message_id:', receivedMessageId);
                    }
                    if (data.error) {
                        lastItem.role = 'error';
                        lastItem.content = `服务器错误: ${data.error}`;
                        cleanUp();
                    } else if (data.text) {
                        tempBuffer += data.text;
                        while (tempBuffer.length > 0) {
                            if (!isInThinkTag) {
                                const thinkStartIndex = tempBuffer.indexOf("<think>");
                                if (thinkStartIndex !== -1) {
                                    buffer += tempBuffer.substring(0, thinkStartIndex);
                                    tempBuffer = tempBuffer.substring(thinkStartIndex + 7);
                                    isInThinkTag = true;
                                    codelensIsStreamLoad.value = true;
                                } else {
                                    buffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            } else {
                                const thinkEndIndex = tempBuffer.indexOf("</think>");
                                if (thinkEndIndex !== -1) {
                                    reasoningBuffer += tempBuffer.substring(0, thinkEndIndex);
                                    tempBuffer = tempBuffer.substring(thinkEndIndex + 8);
                                    isInThinkTag = false;
                                    codelensIsStreamLoad.value = false;
                                    const endTime = Date.now();
                                    lastItem.duration = ((endTime - startTime) / 1000).toFixed(2);
                                } else {
                                    reasoningBuffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            }
                        }

                        if (!isFlushing) {
                            isFlushing = true;
                            setTimeout(flushBuffer, 50);
                        }
                    }
                } catch (e) {
                    console.error('解析代码守护助手测试SSE数据失败:', e);
                    lastItem.role = 'error';
                    lastItem.content = '数据解析失败';
                    cleanUp();
                }
            };

            eventSource.onerror = (err) => {
                console.error('代码守护助手测试SSE连接错误:', err);
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
        console.error('代码守护助手测试请求异常:', error);

        if (error.name === 'AbortError') {
            lastItem.content = '请求超时，请重试';
        } else {
            lastItem.content = `网络错误: ${error.message || '未知错误'}`;
        }

        lastItem.role = 'error';
        lastItem.datetime = new Date().toLocaleString();

        if (eventSource) eventSource.close();
    } finally {
        codelensLoading.value = false;
        codelensIsStreamLoad.value = false;
    }
};

// 表格配置
const tableRef = ref();
const tableColumnList = ref([
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'board', title: () => (<div style={{ textAlign: 'center' }}>单板名称</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'operator_person', title: '操作人', width: '200', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },
    {
        colKey: 'edit',
        title: '操作',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (
            <>
            <t-link theme="primary" hover="color" onClick={() => openQueryDialog(row)} style={{ marginRight: '8px' }}>查看</t-link>
            </>
        )
    }
]);
const updateColumnList = ref([])

// 原始数据和筛选后数据
const tableDataList = ref([]);
const filterDataList = ref([]);

// 表格选择相关
const selectedRowKeyList = ref([]);

// 后端查询的选择器选项
const allFactorOptionList = ref([]);
const factorValueDict = ref({});
const allFactorValueDict = ref({});

const filterValue = ref({});

// 查询相关
const queryDialogVisible = ref(false);
const queryFormData = ref({});

const tableHeight = ref('900px');

// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('请先登录...');
        router.push('/login');
    }
    try {
        await refreshData();

        tableHeight.value = pubCalculateTableHeight();

        // 初始化当前对话单板
        if (boardNameOptionList.value.length > 0) {
            currentChatBoard.value = selectedBoardNameOption.value;
        }
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
});

// 选中事件处理
const handleSelectChange = (keys) => {
    selectedRowKeyList.value = keys;
};

const refreshData = async () => {
    selectedRowKeyList.value = [];

    const [
        queryBoardTreeByParamsResponse,
        queryBoardTreeFactorListResponse,
        queryBoardTreeFactorValueDictResponse,
        queryBoardTreeAllFactorValueDictResponse,
        supportedBoardsResponse,
    ] = await Promise.all([
        queryBoardTreeByParams(),
        queryBoardTreeFactorList(),
        queryBoardTreeFactorValueDict(),
        queryBoardTreeAllFactorValueDict(),
        get_support_list(),
    ]);

    tableDataList.value = queryBoardTreeByParamsResponse.data || [];
    allFactorOptionList.value = queryBoardTreeFactorListResponse.data || [];
    factorValueDict.value = queryBoardTreeFactorValueDictResponse.data || {};
    allFactorValueDict.value = queryBoardTreeAllFactorValueDictResponse.data || {};
    supportedBoards.value = supportedBoardsResponse.data || [];
    filterDataList.value = tableDataList.value
    const allBoardNames = tableDataList.value.map(item => item["board"]);
    boardNameOptionList.value = allBoardNames.filter(board => supportedBoards.value.includes(board));
    if (boardNameOptionList.value.length > 0) {
        const defaultBoard = supportedBoards.value.includes(selectedBoardNameOption.value) 
            ? selectedBoardNameOption.value 
            : boardNameOptionList.value[0];
        selectedBoardNameOption.value = defaultBoard;
        currentChatBoard.value = selectedBoardNameOption.value;
    } else {
        // 无支持的单板时清空选中值
        selectedBoardNameOption.value = "";
        currentChatBoard.value = "";
    }

    dynamicUpdateColumn();
}

const dynamicUpdateColumn = () => {
    updateColumnList.value = tableColumnList.value
    const boardIndex = updateColumnList.value.findIndex(col => col.colKey === 'board');
    if (boardIndex === -1) {
        return null;
    }

    const supportedBoardOptions = factorValueDict.value.board 
        ? factorValueDict.value.board.filter(board => supportedBoards.value.includes(board))
        : [];

    // 更新单板筛选
    updateColumnList.value[boardIndex]['filter'] = {
        component: markRaw(Select),
        props: {
            options: [
                { label: '全选', checkAll: true },
                ...supportedBoardOptions.map(value => ({
                    label: value,
                    value: value,
                }))
            ],
            placeholder: '请选择单板',
            multiple: true,
            filterable: true,
            clearable: true,
        },
        showConfirmAndReset: true,
    }

    // 插入因子列
    const newColumns = allFactorOptionList.value.map((item) => {
        const filterOptionList = factorValueDict.value[item] || [];
        const filterList = [
            { label: '全选', checkAll: true },
            ...filterOptionList.map(value => ({
                label: value,
                value: value,
            })),
        ];
        return {
            colKey: item,
            title: () => (<div style={{ textAlign: 'center' }}>{item}</div>),
            width: '200',
            align: 'left',
            ellipsis: { theme: 'light', placement: 'bottom' },
            filter: {
                component: markRaw(Select),
                props: {
                    options: filterList,
                    placeholder: `请选择${item}`,
                    multiple: true,
                    filterable: true,
                    clearable: true,
                },
                showConfirmAndReset: true,
            },
        };
    });
    const newTableColumns = [...updateColumnList.value];
    newTableColumns.splice(boardIndex + 1, 0, ...newColumns);
    updateColumnList.value = newTableColumns;
    return null;
};

const onFilterChange = (filters, ctx) => {
    const cleanedFilters = Object.fromEntries(
        Object.entries(filters).filter(([key, value]) =>
            !Array.isArray(value) || value.length > 0
        )
    );
    filterValue.value = {
        ...cleanedFilters,
    };
    filterData(cleanedFilters);
};

const filterData = (filters) => {
    const timer = setTimeout(() => {
        clearTimeout(timer);
        const newData = tableDataList.value.filter((item) => {
            let result = true;
            // 根据单板名称过滤
            if (result && filters["board"] && filters["board"].length > 0) {
                result = filters["board"].some(selectedValue => item['board']===selectedValue);
            }
            // 如果已经不匹配，可以提前退出循环
            if (!result) {
                return result;
            }
            // 如果已经不匹配，可以提前退出循环
            if (!result) {
                return result;
            }
            // 遍历所有因子选项进行过滤
            for (let i = 0; i < allFactorOptionList.value.length; i++) {
                const factorKey = allFactorOptionList.value[i];
                // 检查该因子是否在filters中存在且有选中值
                if (result && filters[factorKey] && filters[factorKey].length > 0) {
                    // 获取当前行的该因子值
                    const itemValues = item[factorKey] ? item[factorKey].split(',') : [''];
                    // 检查是否有任意一个选中的值包含在当前行中
                    result = filters[factorKey].some(selectedValue => itemValues.includes(selectedValue));
                }
                // 如果已经不匹配，可以提前退出循环
                if (!result) {
                    break;
                }
            }
            return result;
        });
        filterDataList.value = newData;
    }, 100);
};

// 查看相关方法
const openQueryDialog = async (row) => {
    queryFormData.value = {
        ...row
    };

    allFactorOptionList.value.forEach(field => {
        queryFormData.value[field] = row[field]
    });

    queryDialogVisible.value = true;
};

// 单板智能助手相关
const boardNameOptionList = ref([]);
const selectedBoardNameOption = ref("")
const drawVisible = ref(false);
const isShowToBottom = ref(false);
const chatList = ref([]);
let session_id = uuidv4();
const chatRef = ref(null);
const inputText = ref('');
const loading = ref(false);
const isStreamLoad = ref(false);
const supportedBoards = ref([]);

// 存储当前对话对应的单板名称
const currentChatBoard = ref("");

// 单板切换处理函数
const handleBoardChange = (newBoardName) => {
    console.log(`单板切换: ${currentChatBoard.value} -> ${newBoardName}`);
    // 只有当单板确实发生变化时才清理数据
    if (newBoardName !== currentChatBoard.value) {
        clearPreviousBoardData();
        currentChatBoard.value = newBoardName;
    }
};

// 清除上个单板的数据
const clearPreviousBoardData = () => {
    chatList.value = [];
    inputText.value = '';
    loading.value = false;
    isStreamLoad.value = false;
    session_id = uuidv4(); // 生成新的会话ID

    console.log(`已清理上一个单板的对话数据，当前单板: ${selectedBoardNameOption.value}`);
};

const openBoardChatDialog = () => {
    if (supportedBoards.value.length === 0) {
        MessagePlugin.warning('暂无支持智能助手的单板');
        return;
    }

    // 检查是否切换了单板
    if (selectedBoardNameOption.value !== currentChatBoard.value) {
        clearPreviousBoardData();
        currentChatBoard.value = selectedBoardNameOption.value;
        console.log(`已打开单板 ${selectedBoardNameOption.value} 的智能助手`);
    }
    else{
        console.log(`继续当前单板 ${selectedBoardNameOption.value} 的对话`);

    }

    RequestBoradChart();
    drawVisible.value = true;
}

const RequestBoradChart = async () => {
    try {
        const extractBoardName = (fullName) => {
            const match = fullName.match(/^([^(]+)/);
            return match ? match[1].trim() : fullName;
        };

        const pureBoardName = extractBoardName(selectedBoardNameOption.value);
        const requestParams = {
            user_id: user.userInfo.name,
            board_name: pureBoardName,
        };
        await BoardChatDashboardRequest(requestParams);
    } catch (error) {
        console.log('信息记录失败，请重试', error);
    }
};

const newChat = () => {
    session_id = uuidv4(); // 重置聊天id
    chatList.value = []; // 清空聊天列表
    inputText.value = ''; // 清空输入框
    loading.value = false;
    isStreamLoad.value = false;
    MessagePlugin.info('创建对话成功');
};

const handleChatScroll = function ({ e }) {
    const scrollTop = e.target.scrollTop;
    isShowToBottom.value = scrollTop < 0;
};

const backBottom = () => {
    chatRef.value.scrollToBottom({
        behavior: 'smooth',
    });
};

const handleOperation = async (type, options) => {
  const { content, index } = options;

  // 如果是点赞或点踩，显示反馈输入框
  if (type === 'good' || type === 'bad') {
    console.log('点击了反馈按钮:', type, '索引:', index)
    // 确保重置其他可能打开的反馈框
    showFeedbackInput.value = -1;
    feedbackInputText.value = '';
    
    // 使用 nextTick 确保 DOM 更新
    setTimeout(() => {
    showFeedbackInput.value = index;
    pendingFeedbackType.value = type;
    pendingFeedbackIndex.value = index;
    feedbackInputText.value = ''; // 清空之前的输入
    console.log('设置反馈框显示，索引:', showFeedbackInput.value);
    }, 0);
    return;
  }

  // 其他操作（复制、重播）保持原有逻辑
  if (type === 'copy') {
    try {
      await navigator.clipboard.writeText(content);
      MessagePlugin.success('已复制到剪贴板');
    } catch (err) {
      console.error('复制失败:', err);
      MessagePlugin.error('复制失败');
    }
  } else if (type === 'replay') {
    // 重播逻辑
    inputText.value = content;
    inputEnter(content);
  }
};

// 提交单板智能助手反馈
const submitFeedback = async (index) => {
  // 防止重复提交
  if (loading.value) return;

  const feedbackItem = chatList.value[index];
  if (!feedbackItem) return;

  try {
    loading.value = true;
    const messageIdToSend = feedbackItem.message_id || uuidv4();
    // 构建反馈数据
    const feedback_data = {
      user_id: user.userInfo.name,
      session_id: session_id,
      board_name: selectedBoardNameOption.value,
      message_id: messageIdToSend,
      user_question: chatList.value[index + 1]?.content || '', // 用户的问题（上一条消息）
      ai_answer: feedbackItem.content, // AI的回答
      feedback_type: pendingFeedbackType.value,
      feedback_content: feedbackInputText.value, // 用户输入的反馈内容
      timestamp: new Date().toISOString()
    };

    console.log('发送反馈数据:', feedback_data);
    
    // 发送反馈到后端
    const response = await boardChatFeedbackRequest(feedback_data);
    
    if (response.status === 'success') {
      feedbackItem.feedback = pendingFeedbackType.value;
      feedbackItem.feedbackTime = new Date().toLocaleString();
      feedbackItem.feedbackContent = feedbackInputText.value; // 保存反馈内容
      // 显示反馈成功提示
      showFeedbackSuccess.value = index;
      // 3秒后清除状态提示
      setTimeout(() => {
        showFeedbackSuccess.value = -1;
        // 关闭反馈输入框
        showFeedbackInput.value = -1;
        feedbackInputText.value = '';
        pendingFeedbackType.value = '';
        pendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } catch (error) {
    console.error('反馈提交错误:', error);
    // 错误提示
    if (index !== undefined && chatList.value[index]) {
      chatList.value[index].feedbackStatus = '反馈失败';
      setTimeout(() => {
        if (chatList.value[index]) {
          chatList.value[index].feedbackStatus = '';
        }
        // 关闭反馈输入框
        showFeedbackInput.value = -1;
        feedbackInputText.value = '';
        pendingFeedbackType.value = '';
        pendingFeedbackIndex.value = -1;
      }, 3000);
    }
  } finally {
    loading.value = false;
  }
};

// 取消单板智能助手反馈
const cancelFeedback = () => {
  showFeedbackInput.value = -1;
  feedbackInputText.value = '';
  pendingFeedbackType.value = '';
  pendingFeedbackIndex.value = -1;
};

const handleChange = (value) => {
    console.log('handleChange', value);
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

/**
 * 渲染推理内容组件
 * @param {string} reasoningContent - 需要渲染的推理内容
 * @returns {JSX.Element} 返回 markdown渲染内容，用于展示推理内容, 不用markdown渲染组件原文返回
 */
const renderReasoningContent = (reasoningContent) => <t-chat-content content={reasoningContent} role="assistant" />;

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
        content: inputValue,
        reasoning: '',
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


const handleData = async (inputValue) => {
    loading.value = true;
    isStreamLoad.value = true;

    const lastItem = chatList.value[0];
    let receivedMessageId = '';

    // 构建context对象并转换为字符串
    const contextObj = selectedBoardNameOption.value? {board_name: selectedBoardNameOption.value || '', answer: inputValue} : {};
    // 将JSON对象转换为字符串
    const context = JSON.stringify(contextObj);

    let buffer = '';
    let reasoningBuffer = '';
    let isFlushing = false;
    let isInThinkTag = false; // 标记是否在<think>标签内
    let tempBuffer = ''; // 临时缓冲区，用于处理不完整的标签
    let eventSource = null; // 用于在外部访问EventSource
    let startTime = Date.now(); // 记录开始时间

    function flushBuffer() {
        if (buffer && lastItem) {
            lastItem.content += buffer;
            buffer = '';
        }
        if (reasoningBuffer && lastItem) {
            lastItem.reasoning += reasoningBuffer;
            reasoningBuffer = '';
        }
        isFlushing = false;
    }

    try {
        // 增加fetch超时处理
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 30秒超时

        const data = await boardChatChatRequest(
            {
                user: user.userInfo.name,
                session_id,
                board_name: selectedBoardNameOption.value,
                content: context,
            },
            { signal: controller.signal }
        );

        clearTimeout(timeoutId);

        if (data.status === 'success') {
            eventSource = boardChatCreateChatEventSource(session_id, {
                // 可扩展其他参数
                board_name: selectedBoardNameOption.value
            });

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
                    // 处理剩余的临时缓冲区内容
                    if (tempBuffer) {
                        if (isInThinkTag) {
                            reasoningBuffer += tempBuffer;
                        } else {
                            buffer += tempBuffer;
                        }
                        tempBuffer = '';
                    }

                    if (buffer && lastItem) {
                        lastItem.content += buffer;
                        buffer = '';
                    }
                    if (reasoningBuffer && lastItem) {
                        lastItem.reasoning += reasoningBuffer;
                        reasoningBuffer = '';
                    }
                    // 将message_id存储到聊天项中
                    if (receivedMessageId && lastItem) {
                        lastItem.message_id = receivedMessageId;
                    }
                    cleanUp();
                    return;
                }

                try {
                    const data = JSON.parse(event.data);
                    // 检查是否包含message_id
                    if (data.message_id) {
                        // 接收并存储message_id
                        receivedMessageId = data.message_id;
                        if (lastItem) {
                            lastItem.message_id = receivedMessageId;
                        }
                        console.log('接收到message_id:', receivedMessageId);
                    }
                    if (data.error) {
                        lastItem.role = 'error';
                        lastItem.content = `服务器错误: ${data.error}`;
                        cleanUp();
                    } else if (data.text) {
                        // 将新数据添加到临时缓冲区
                        tempBuffer += data.text;
                        // 处理临时缓冲区中的内容
                        while (tempBuffer.length > 0) {
                            if (!isInThinkTag) {
                                // 查找<think>标签开始
                                const thinkStartIndex = tempBuffer.indexOf("<think>");
                                if (thinkStartIndex !== -1) {
                                    // 将<think>之前的内容添加到主缓冲区
                                    buffer += tempBuffer.substring(0, thinkStartIndex);
                                    // 更新临时缓冲区，移除已处理的部分
                                    tempBuffer = tempBuffer.substring(thinkStartIndex + 7); // 7是"<think>"的长度
                                    isInThinkTag = true;
                                    // 当开始思考时，设置流加载状态
                                    isStreamLoad.value = true;
                                } else {
                                    // 没有找到<think>标签，将所有内容添加到主缓冲区
                                    buffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            } else {
                                // 查找</think>标签结束
                                const thinkEndIndex = tempBuffer.indexOf("</think>");
                                if (thinkEndIndex !== -1) {
                                    // 将</think>之前的内容添加到推理缓冲区
                                    reasoningBuffer += tempBuffer.substring(0, thinkEndIndex);
                                    // 更新临时缓冲区，移除已处理的部分
                                    tempBuffer = tempBuffer.substring(thinkEndIndex + 8); // 8是"</think>"的长度
                                    isInThinkTag = false;
                                    // 当思考结束时，设置流加载状态为false，并计算耗时
                                    isStreamLoad.value = false;
                                    const endTime = Date.now();
                                    lastItem.duration = ((endTime - startTime) / 1000).toFixed(2);
                                } else {
                                    // 没有找到</think>标签，将所有内容添加到推理缓冲区
                                    reasoningBuffer += tempBuffer;
                                    tempBuffer = '';
                                }
                            }
                        }

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
        isStreamLoad.value = false;
    }
};
</script>


<style scoped>
.dialog-content {
    padding: 16px;
    line-height: 1.5;
    min-height: 40px;
}

.dialog-content p {
    white-space: pre-line;
    margin: 0;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid #e0e0e0;
}

.query-form,
.edit-form,
.add-form {
    padding: 16px 0;
    height: 500px;
    overflow-y: auto;
}

.scene-main {
/* 基础表格样式 */
table {
    border-collapse: collapse;
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

    .data-board-btn {
      background-color: #1a16fc; /* 蓝色背景 */
      color: white; /* 白色文字 */
      border: none;
      border-radius: 4px; /* 方框圆角 */
      padding: 8px 16px;
      font-weight: 600;
      font-size: 14px;
      box-shadow: 
          0px 4px 12px rgba(0, 0, 0, 0.15),
          0px 16px 32px rgba(0, 0, 0, 0.2),
          0px 32px 48px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;
      white-space: nowrap;
    }

    .precise-spacing {
      margin-left: 50px !important;
    }

    .data-board-btn:hover {
      background-color: #0d0bc2;
      transform: translateY(-1px);
      box-shadow: 
          0px 6px 16px rgba(0, 0, 0, 0.2),
          0px 20px 40px rgba(0, 0, 0, 0.25),
          0px 36px 56px rgba(0, 0, 0, 0.2);
    }

    .feedback-status {
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .feedback-time {
      font-size: 12px;
      color: #999;
    }

    /* 禁用状态的反馈按钮样式 */
    :deep(.t-chat-action__btn[disabled]) {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* 已反馈按钮的高亮样式 */
    :deep(.t-chat-action__btn.active) {
      color: var(--td-brand-color);
      background-color: var(--td-brand-color-1);
    }

    .feedback-status-tip {
      margin-top: 8px;
      animation: fadeInOut 3s ease-in-out;
    }

    @keyframes fadeInOut {
      0% { opacity: 0; }
      20% { opacity: 1; }
      80% { opacity: 1; }
      100% { opacity: 0; }
    }

    .general-assistant-btn {
        background-color: #1a16fc; /* 蓝色背景 */
      color: white;
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      font-weight: 600;
      font-size: 14px;
      box-shadow: 
          0px 4px 12px rgba(0, 0, 0, 0.15),
          0px 16px 32px rgba(0, 0, 0, 0.2),
          0px 32px 48px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;
      white-space: nowrap;
    }

    .general-assistant-btn:hover {
      background-color: #0d0bc2;
      transform: translateY(-1px);
      box-shadow:
          0px 6px 16px rgba(0, 0, 0, 0.2),
          0px 20px 40px rgba(0, 0, 0, 0.25),
          0px 36px 56px rgba(0, 0, 0, 0.2);
    }

    .codelens-assistant-btn {
        background-color: #1a16fc;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      font-weight: 600;
      font-size: 14px;
      box-shadow:
          0px 4px 12px rgba(0, 0, 0, 0.15),
          0px 16px 32px rgba(0, 0, 0, 0.2),
          0px 32px 48px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;
      white-space: nowrap;
    }

    .codelens-assistant-btn:hover {
      background-color: #0d0bc2;
      transform: translateY(-1px);
      box-shadow:
          0px 6px 16px rgba(0, 0, 0, 0.2),
          0px 20px 40px rgba(0, 0, 0, 0.25),
          0px 36px 56px rgba(0, 0, 0, 0.2);
    }

    .wide-spacing {
      margin-left: 100px !important;
    }

    .precise-spacing {
      margin-left: 50px !important;
    }

    /* 添加反馈输入框样式 */
    .feedback-input-container {
        margin-top: 12px;
        padding: 12px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e5e5e5;
        position: relative;
        display: flex;
        align-items: flex-start;
        gap: 16px;
    }

    .feedback-input-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .feedback-textarea {
        margin-bottom: 8px;
    }

    .feedback-actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
    }

    /* 反馈成功提示在反馈框右边的样式 */
    .feedback-success-tip {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 100px;
        animation: slideInFromRight 0.3s ease-out;
    }

    /* 原有的反馈状态提示 */
    .feedback-status-tip {
        margin-top: 8px;
        animation: fadeInOut 3s ease-in-out;
    }

    /* 动画效果 */
    @keyframes slideInFromRight {
        0% {
            opacity: 0;
            transform: translateX(20px);
        }
        100% {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeInOut {
        0% { opacity: 0; }
        20% { opacity: 1; }
        80% { opacity: 1; }
        100% { opacity: 0; }
    }

    /* 调整操作区域的位置，为状态提示留出空间 */
    :deep(.t-chat__actions) {
        position: relative;
        min-height: 40px;
    }

    /* 确保操作按钮区域有足够的空间显示状态提示 */
    :deep(.t-chat-action) {
        position: relative;
    }

    /* 原有的反馈状态样式保留 */
    .feedback-status {
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }

    .feedback-time {
        font-size: 12px;
        color: #999;
    }

    .feedback-content {
        font-size: 12px;
        color: #666;
        background-color: #f5f5f5;
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 4px;
        width: 100%;
    }
  }
</style>