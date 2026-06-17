
<template>
  <div class="chat-box">
    <t-drawer v-model:visible="historyChatDrawVisible" placement="right" :footer="false" :z-index="4999">
      <template #header>历史会话</template>

      <div class="history-list">
        <div
          v-for="record in historySessionRecord"
          :key="record.session_id"
          class="history-item"
          @click="handleSessionClick(record.session_id)"
        >
          <div class="history-content">{{ record.title }}</div>
          <div class="history-time">{{ record.time }}</div>
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
    <t-tooltip content="语料新增" placement="top">
      <t-button class="corpusadd" size="large" theme="primary" shape="circle" variant="base" @click="jumpToScenePage">
        <icon name="creditcard-add" />
      </t-button>
    </t-tooltip>
    <t-tooltip content="度量看板" placement="top">
      <t-button class="metricsBoard" size="large" theme="primary" shape="circle" variant="base" @click="jumpToTablePage">
        <icon name="chart-area-multi-filled" />
      </t-button>
    </t-tooltip>

    <t-tooltip v-if="['10345712', '10276640'].includes(user.userInfo.name)" content="对话数据导出" placement="top">
      <!-- 时间选择器 + 按钮 -->
      <div class="qaExport">
        <button
          class="export-btn"
          @click="exportQaDetailsData"
        >
          对话数据导出
        </button>
        <t-date-range-picker
          v-model="dateRange"
          value-type="YYYY-MM-DD"
          style="flex: 1; min-width: 140px;"
        />
      </div>
    </t-tooltip>

    <!-- 清空历史记录配置 -->
    <!-- :clear-history="chatList.length > 0 && !isStreamLoad" -->

    <t-chat ref="chatRef" layout="both" :clear-history="false" @scroll="handleChatScroll" @clear="clearConfirm">
      <template v-for="(item, index) in chatList" :key="item.message_id">
        <!-- 对话信息显示 -->
        <t-chat-item
          :variant="item.role === 'user' ? 'base' : 'base'"
          :avatar="item.avatar"
          :name="item.name"
          :role="item.role"
          :datetime="item.datetime"
          :text-loading="index === 0 && loading"
          :content="item.content"
          :reasoning="item.reasoning ? {
            collapsed: index === chatList.length - 1 && !isStreamLoad,
            expandIconPlacement: 'right',
            collapsePanelProps: {
              header: renderHeader(index === chatList.length - 1 && isStreamLoad && !item.content, item),
              content: renderReasoningContent(item.reasoning),
            },
          }:null"
        >
          <!-- 操作按钮直接放在 t-chat-item 内部 -->
          <template #actions>
            <!-- 日志诊断消息：显示进度条 -->
            <div v-if="item.progress !== null">
              <t-progress
                class="log-download-progress"
                style="width: 300px; height: 10px;"
                :percentage="Math.max(0, Math.min(100, item.progress))"
                :status="getProgressStatus(item)"
                theme="line"
                :stroke-width="10"
              />
            </div>
            <div v-if="item.logDownloadConfig" >
              <!-- 外层包裹，用于 :deep() 穿透 -->
              <div class="system-log-diagnosis-filters" style="width: 100%; max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
                <!-- 跳板机 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">跳板机</label>
                  <select
                    v-model="item.logDownloadConfig.jumpName"
                    placeholder="请选择跳板机"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="">请选择跳板机</option>
                    <option v-for="opt in systemJumpNameOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>

                <!-- 网元ip -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">网元ip</label>
                  <input
                    v-model="item.logDownloadConfig.targetIp"
                    placeholder="请输入网元ip"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                </div>

                <!-- 子架 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">子架</label>
                  <input
                    v-model="item.logDownloadConfig.shelf"
                    placeholder="请输入子架号"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                </div>

                <!-- 槽位 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">槽位</label>
                  <input
                    v-model="item.logDownloadConfig.slot"
                    placeholder="请输入槽位号"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                </div>
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">只取今天日志</label>
                  <select
                    v-model="item.logDownloadConfig.todayOnly"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="是">是</option>
                    <option value="否">否</option>
                  </select>
                </div>

                <div class="action-row" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                  <button
                    style="
                      background-color: #0052d9 !important;
                      color: #ffffff !important;
                      border: none !important;
                      padding: 10px 20px !important;
                      font-size: 14px !important;
                      font-weight: 500;
                      cursor: pointer !important;
                      border-radius: 6px !important;
                      white-space: nowrap;
                      box-shadow: 0 2px 4px rgba(0,82,217,0.2);
                    "
                    @click="triggerLogDownloadTask(item.logDownloadConfig)"
                  >
                    拉取日志
                  </button>
                </div>
              </div>
            </div>
            <div v-if="item.logDiag" >
              <!-- 外层包裹，用于 :deep() 穿透 -->
              <div class="system-log-diagnosis-filters" style="width: 100%; max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
                <!-- 领域 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">领域</label>
                  <select
                    v-model="item.selectLogFieldValue"
                    placeholder="请选择领域"
                    @change="item.selectLogMainSceneValue='';item.selectLogSubSceneValue=''"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="">请选择领域</option>
                    <option v-for="opt in systemLogFieldOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>

                <!-- 主场景 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">主场景</label>
                  <select
                    v-model="item.selectLogMainSceneValue"
                    placeholder="请选择主场景"
                    @change="item.selectLogSubSceneValue=''"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="">请选择主场景</option>
                    <option v-for="opt in getMainSceneOptions(item.selectLogFieldValue)" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>

                <!-- 子场景 -->
                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">子场景</label>
                  <select
                    v-model="item.selectLogSubSceneValue"
                    placeholder="请选择子场景"
                    @change="() => handleSubSceneChange(item)"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="">请选择子场景</option>
                    <option v-for="opt in getSubSceneOptions(item.selectLogFieldValue, item.selectLogMainSceneValue)" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>

                <!-- 时间选择器 + 按钮 -->
                <div class="action-row" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                  <t-date-range-picker
                    enableTimePicker
                    v-model="item.dateRange"
                    value-type="YYYY-MM-DD HH:mm:ss"
                    style="flex: 1; min-width: 280px;"
                  />

                  <button
                    style="
                      background-color: #0052d9 !important;
                      color: #ffffff !important;
                      border: none !important;
                      padding: 10px 20px !important;
                      font-size: 14px !important;
                      font-weight: 500;
                      cursor: pointer !important;
                      border-radius: 6px !important;
                      white-space: nowrap;
                      box-shadow: 0 2px 4px rgba(0,82,217,0.2);
                    "
                    @click="handleSystemButtonClick(item)"
                  >
                    开始诊断
                  </button>
                </div>
              </div>
            </div>
            <!-- RDC诊断：在完成流式输出后追加“是/否”按钮 -->
            <div v-if="item.showRdcButtons" style="display:flex; gap: 8px; margin-top: 8px;">
              <t-button
                @click="onRdcYes(item)"
                style="
                  background-color: #0052d9 !important; /* 蓝色背景 */
                  color: #ffffff !important;           /* 白色文字 */
                  font-size: 14px;                     /* 字体 */
                  border: 1px solid #0052d9 !important; /* 蓝色边框 */
                "
              >
                是
              </t-button>
              <!-- <t-button
                @click="onRdcNo(item)"
                style="
                  background-color: #0052d9 !important; /* 蓝色背景 */
                  color: #ffffff !important;           /* 白色文字 */
                  font-size: 14px;                     /* 字体 */
                  border: 1px solid #0052d9 !important; /* 蓝色边框 */
                "
              >
                否
              </t-button> -->
            </div>
            <!-- 故障单提交：在完成输出后追加新弹窗“是/否”按钮 -->
            <div v-if="item.showSubmitRdcButtons" style="display: flex; gap: 8px; margin-top: 8px">
              <t-button theme="primary" @click="onSubmitRdcYes(item)"> 是 </t-button>
              <t-button theme="primary" @click="onSubmitRdcNo(item)"> 否 </t-button>
            </div>

            <!-- 点赞点踩组件 -->
            <div v-if="item.role === 'assistant' && item.rating !== -1" class="rating-container">
              <div class="feedback-actions" style="display: flex; gap: 8px; align-items: center">
                <!-- 点赞按钮 -->
                <t-button
                  :theme="item.rating === 5 ? 'primary' : 'default'"
                  variant="text"
                  size="small"
                  @click="handleLikeClick(item)"
                >
                  <template #icon>
                    <icon name="thumb-up" size="16" />
                  </template>
                  {{ item.rating === 5 ? '已赞' : '赞' }}
                </t-button>

                <!-- 点踩按钮 -->
                <t-button
                  :theme="item.rating === 1 ? 'warning' : 'default'"
                  variant="text"
                  size="small"
                  @click="handleDislikeClick(item)"
                >
                  <template #icon>
                    <icon name="thumb-down" size="16" />
                  </template>
                  {{ item.rating === 1 ? '已踩' : '踩' }}
                </t-button>

                <!-- 点赞理由对话框 -->
                <t-dialog
                  v-model:visible="likeDialogVisible"
                  header="点赞理由"
                  :width="400"
                  placement="center"
                  :close-on-overlay-click="false"
                  :close-on-esc-keypress="false"
                >
                  <template #default>
                    <div class="dislike-reasons" style="background-color: #ffffff; min-height: 200px">
                      <p style="margin-bottom: 16px; color: #666">请选择点赞的主要原因：</p>

                      <div class="reason-buttons" style="display: flex; flex-wrap: wrap; gap: 8px">
                        <t-button
                          v-for="reason in likeReasons"
                          :key="reason.value"
                          :theme="selectedDislikeReason === reason.value ? 'primary' : 'default'"
                          variant="outline"
                          size="small"
                          @click="selectDislikeReason(reason.value)"
                        >
                          {{ reason.label }}
                        </t-button>
                      </div>

                      <div style="margin-top: 16px">
                        <t-textarea
                          v-model="dislikeComment"
                          placeholder="请补充具体原因（选填）"
                          :autosize="{ minRows: 3, maxRows: 6 }"
                          style="width: 100%; background-color: #ffffff"
                        />
                      </div>
                    </div>
                  </template>
                  <template #footer>
                    <div class="dialog-footer">
                      <t-button theme="default" @click="submitLikeFeedback"> 提交 </t-button>
                      <t-button theme="default" @click="cancelLikeFeedback"> 撤回 </t-button>
                    </div>
                  </template>
                </t-dialog>

                <!-- 点踩理由对话框 -->
                <t-dialog
                  v-model:visible="dislikeDialogVisible"
                  header="点踩理由"
                  :width="400"
                  placement="center"
                  :close-on-overlay-click="false"
                  :close-on-esc-keypress="false"
                >
                  <template #default>
                    <div class="dislike-reasons" style="background-color: #ffffff; min-height: 200px">
                      <p style="margin-bottom: 16px; color: #666">请选择点踩的主要原因：</p>

                      <div class="reason-buttons" style="display: flex; flex-wrap: wrap; gap: 8px">
                        <t-button
                          v-for="reason in dislikeReasons"
                          :key="reason.value"
                          :theme="selectedDislikeReason === reason.value ? 'primary' : 'default'"
                          variant="outline"
                          size="small"
                          @click="selectDislikeReason(reason.value)"
                        >
                          {{ reason.label }}
                        </t-button>
                      </div>

                      <div style="margin-top: 16px">
                        <t-textarea
                          v-model="dislikeComment"
                          placeholder="请补充具体原因（选填）"
                          :autosize="{ minRows: 3, maxRows: 6 }"
                          style="width: 100%; background-color: #ffffff"
                        />
                      </div>
                    </div>
                  </template>
                  <template #footer>
                    <div class="dialog-footer">
                      <t-button theme="default" @click="submitDislikeFeedback"> 提交 </t-button>
                      <t-button theme="default" @click="cancelDislikeFeedback"> 撤回 </t-button>
                    </div>
                  </template>
                </t-dialog>

                <t-chat-action
                  :content="item.content"
                  :operation-btn="['replay', 'copy']"
                  @operation="handleOperation"
                />
              </div>
            </div>
            <!-- <div v-if="item.rdcCheck" class="rating-container">
              <div class="system-log-diagnosis-filters" style="width: 100%; max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">

                <div class="filter-item" style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
                  <label style="flex: 0 0 90px; font-size: 14px; color: #333;">AI模型</label>
                  <select
                    v-model="item.rdcCheckModel"
                    placeholder="请选择大模型"
                    style="flex: 1; min-width: 200px; padding: 10px; border: 1px solid #000; border-radius: 4px; background-color: #fff; font-size: 14px; color: #333;"
                  >
                    <option value="nebula">星云大模型</option>
                    <option value="qwen3-zte">通义千问-中兴</option>
                  </select>
                </div>
                <div class="action-row" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                  <t-date-range-picker
                    v-model="item.dateRange"
                    value-type="YYYY-MM-DD"
                    style="flex: 1; min-width: 280px;"
                  />

                  <button
                    style="
                      background-color: #0052d9 !important;
                      color: #ffffff !important;
                      border: none !important;
                      padding: 10px 20px !important;
                      font-size: 14px !important;
                      font-weight: 500;
                      cursor: pointer !important;
                      border-radius: 6px !important;
                      white-space: nowrap;
                      box-shadow: 0 2px 4px rgba(0,82,217,0.2);
                    "
                    @click="handleRdcCheckButtonClick(item)"
                  >
                    开始检查
                  </button>
                </div>
              </div>
            </div> -->
          </template>
        </t-chat-item>
      </template>
      <template #footer>
        <!-- 输入信息显示 -->
        <t-chat-sender
          v-model="inputText"
          :stop-disabled="isStreamLoad"
          :disabled="isStreamLoad"
          :textarea-props="{
            placeholder: inputPlaceholder,
            autosize: { minRows: 2, maxRows: 12 }
          }"
          @stop="onStop"
          @send="inputEnter"
        >
          <template #prefix>
            <div class="model-select">
              <t-select v-model="selectModelValue" :options="selectModel" value-type="object"></t-select>
              <t-select v-if="shouldShowLogAnalyseSelect" v-model="selectLogAnalyseValue" :options="selectLogAnalyse" value-type="object"></t-select>
              <t-select v-if="shouldShowReproduceSelect" v-model="selectReproduceValue" :options="selectReproduce" value-type="object"></t-select>
              <t-select v-if="shouldShowJumpSelect"
                v-model="selectJumpValue"
                placeholder="请选择跳板机"
                :options="systemJumpNameOptions" value-type="object"
              >
              </t-select>

              <!上站定位的文件上传按钮 -->
              <t-upload
                v-if="shouldShowUploadForLocation"
                v-model="locationFileList"
                :auto-upload="false"
                :size-limit="{ size: 500, unit: 'MB' }"
                :before-upload="beforeUploadLocation"
                @change="onLocationFileChange"
                :disabled="locationUploading"
                theme="custom"
              >
                <t-button :disabled="locationUploading">上传文件到设备</t-button>
              </t-upload>

              <t-upload
                v-if="shouldShowLogAnalyseSelect"
                v-model="fileList"
                :auto-upload="false"
                :size-limit="{ size: 150, unit: 'MB' }"
                :before-upload="beforeUpload"
                @change="onFileChange"
                :disabled="uploading"
                theme="custom"
              >
                <t-button :disabled="uploading">文件上传</t-button>
                <button onclick="window.open('http://10.239.69.183:8080/experience/', '_blank')">
                    浏览agent经验
                </button>
              </t-upload>
              <!-- 新增：图片上传按钮（用于故障确认/直接定位） -->
              <t-upload
                v-if="shouldShowImageUpload"
                v-model="imageFileList"
                :auto-upload="false"
                accept="image/*"
                :size-limit="{ size: 10, unit: 'MB' }"
                :before-upload="beforeImageUpload"
                @change="onImageChange"
                :disabled="imageUploading"
                theme="custom"
              >
                <t-button :disabled="imageUploading">📷 图片上传</t-button>
              </t-upload>
            </div>
          </template>
        </t-chat-sender>
        <!-- 新增上传状态显示 -->
        <div v-if="uploadStatus" class="upload-status" :class="uploadStatus.type === 'success' ? 'upload-success' : 'upload-error'">
          {{ uploadStatus.message }}
        </div>

        <!-- 新增上传中提示 -->
        <div v-if="uploading" class="uploading-indicator">
          文件上传中...
        </div>
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
import { watch } from 'vue';
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

const INTELDIGA_API_URL = import.meta.env.VITE_INTELDIGA_API_URL;
const router = useRouter();
const user = useUserStore();
// RDC 按钮显示的严格结尾校验文本（包含末尾换行）
const RDC_SUFFIX = '**接受场景请点击“是”**\n';

const STATUS_ERROR = 0
const STATUS_LOG_MATCH_SUCCESS = 1
const STATUS_LOG_MATCH_FAIL = 2

const jumpToScenePage = () => {
  router.push('/ai/diag/diagSceneBoard');
};
const jumpToTablePage = () => {
  router.push('/ai/diag/diagTable');
};


// 为每个聊天单独制定一个唯一id，防止同时提问时冲突
let session_id = uuidv4();
let fileContent = null;

const fetchCancel = ref(null);
const loading = ref(false);
// 流式数据加载中
const isStreamLoad = ref(false);

const chatRef = ref(null);
const isShowToBottom = ref(false);

// 保存最近一次用户输入（RDC诊断重触发用）
const lastUserInput = ref('');

const local_jumpName = ref('');
const local_targetIp = ref('');
const local_shelf = ref('');
const local_slot = ref('');

// 滚动到底部
const backBottom = () => {
  chatRef.value.scrollToBottom({
    behavior: 'smooth',
  });
};
const fileList = ref([]);
const guidance = ref(null)
const startTime = ref(null);
const endTime = ref(null);
const dateRange = ref([]);
const uploading = ref(false);
const uploadStatus = ref(null);
// 新增：图片上传相关状态
const imageFileList = ref([]);
const imageUploading = ref(false);
const uploadedImageName = ref(null); // 保存已上传的图片文件名

// 点赞点踩相关状态
const likeDialogVisible = ref(false); // 点赞对话框显示状态
const dislikeDialogVisible = ref(false); // 点踩对话框显示状态
const selectedDislikeReason = ref(''); // 选中的点踩理由
const dislikeComment = ref(''); // 点踩补充评论
const currentDislikeItem = ref(null); // 当前要点踩的消息项

// 点赞理由选项
const likeReasons = [
  { label: '响应迅速', value: '响应迅速' },
  { label: '回答准确', value: '回答准确' },
  { label: '指引明晰', value: '指引明晰' },
  { label: '定位无误', value: '定位无误' },
  { label: '操作简便', value: '操作简便' },
  { label: '研判精准', value: '研判精准' },
  { label: '其他', value: '其他' },
];

// 点踩理由选项
const dislikeReasons = [
  { label: '易用性差', value: '易用性差' },
  { label: '知识不够', value: '知识不够' },
  { label: '准确度不高', value: '准确度不高' },
  { label: '工具调用', value: '工具调用' },
  { label: '其他', value: '其他' },
];

const selectModel = [
  {
    label: '请选择业务子活动',
    value: '',
  },
  {
    label: '故障确认',
    value: '故障确认',
  },
  {
    label: '直接定位',
    value: '直接定位',
  },
  {
    label: '日志分析',
    value: '日志分析',
  },
  {
    label: '上站定位',
    value: '上站定位',
  },
  {
    label: '复现定位',
    value: '复现定位',
  }
];

const selectLogAnalyse = [
  {
    label: '通用分析',
    value: '日志分析',
  },
  {
    label: '数据一致性比较分析',
    value: '数据一致性比较分析',
  },
  {
    label: '内存分析',
    value: '内存分析',
  },
];

const selectReproduce = [
  {
    label: '工程故障横推',
    value: '工程故障横推',
  }
];

const selectLogAnalyseValue = ref({
  label: '通用分析',
  value: '日志分析',
});

const selectReproduceValue = ref({
  label: '工程故障横推',
  value: '工程故障横推',
});

const selectJumpValue = ref({
  label: '请选择跳板机',
  value: '',
});

const selectModelValue = ref({
  label: '请选择业务子活动',
  value: '',
});


const locationFileList = ref([]);
const locationUploading = ref(false);
const locationUploadStatus = ref(null);

//加上站定位文件上传相关方法
const beforeUploadLocation = async (fileObject) => {
  const file = fileObject.raw;
  const name = file.name.toLowerCase();

  // 支持常见日志文件格式
  const allowedExtensions = ['.tar', '.zip', '.log', '.txt', '.gz', '.tar.gz'];
  const isValid = allowedExtensions.some(ext => name.endsWith(ext));

  if (!isValid) {
    MessagePlugin.error('不支持的文件类型，请上传 .tar, .zip, .log, .txt, .gz 格式的文件');
    return false;
  }

  return true;
};

const onLocationFileChange = (data) => {
  const file = data[0]?.raw;
  if (file) uploadFileToDevice(file);
};

const uploadFileToDevice = async (file) => {
  // 检查是否选择了跳板机
  if (!selectJumpValue.value?.value) {
    MessagePlugin.warning('请先选择跳板机');
    locationFileList.value = [];
    return;
  }

  // 检查是否填写了目标IP
  let targetIp = await prompt('请输入目标设备IP地址：');
  if (!targetIp || !targetIp.trim()) {
    MessagePlugin.warning('请输入目标设备IP地址');
    locationFileList.value = [];
    return;
  }

  // 检查是否填写了目标路径
  let targetPath = '/';


  // 确保目标路径以 / 结尾
  if (!targetPath.endsWith('/')) {
    targetPath += '/';
  }

  locationUploading.value = true;
  locationUploadStatus.value = null;

  // 添加用户消息
  const userMsgId = uuidv4();
  const userMsg = {
    avatar: '/src/assets/assets-user3.png',
    datetime: new Date().toLocaleString(),
    content: `上传文件 "${file.name}" 到设备 ${targetIp}`,
    message_id: userMsgId,
    role: 'user',
  };
  chatList.value.unshift(userMsg);

  // 添加AI占位消息 - 保存message_id以便后续更新
  const assistantMsgId = uuidv4();
  const assistantMsg = {
    avatar: '/src/assets/assets-ai2.png',
    role: 'assistant',
    content: '🚀 正在上传文件...',
    reasoning: '',
    logDiag: false,
    rating: -1,
    session_id: session_id,
    message_id: assistantMsgId,
    progress: 0,
    datetime: new Date().toLocaleString(),
  };
  chatList.value.unshift(assistantMsg);

  // 保存当前消息的ID，用于后续查找更新
  const currentAssistantMsgId = assistantMsgId;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('jump_name', selectJumpValue.value.value);
  formData.append('target_ip', targetIp.trim());
  formData.append('target_path', targetPath);
  formData.append('session_id', session_id);
  formData.append('account', user.userInfo.name);

  try {
    const response = await fetch(`${INTELDIGA_API_URL}/api/upload-to-device`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || '上传失败');
    }

    const result = await response.json();

    if (result.status === 'success') {
      // 通过message_id找到对应的消息并更新
      const targetMsg = chatList.value.find(msg => msg.message_id === currentAssistantMsgId);
      if (targetMsg) {
        targetMsg.content = `✅ 文件上传成功！\n\n**文件名:** ${file.name}\n**目标设备**: ${targetIp}\n\n\n${result.message || ''}`;
        targetMsg.progress = 100;
      } else {
        // 如果找不到，添加一条新消息
        const successMsg = {
          avatar: '/src/assets/assets-ai2.png',
          role: 'assistant',
          content: `✅ 文件上传成功！\n\n**文件名:** ${file.name}\n**目标设备**: ${targetIp}\n\n\n${result.message || ''}`,
          reasoning: '',
          logDiag: false,
          rating: -1,
          session_id: session_id,
          message_id: uuidv4(),
          progress: 100,
          datetime: new Date().toLocaleString(),
        };
        chatList.value.unshift(successMsg);
      }
      MessagePlugin.success('文件上传成功');
    } else {
      throw new Error(result.message || '上传失败');
    }
  } catch (error) {
    console.error('文件上传失败:', error);
    // 通过message_id找到对应的消息并更新为错误状态
    const targetMsg = chatList.value.find(msg => msg.message_id === currentAssistantMsgId);
    if (targetMsg) {
      targetMsg.content = `❌ 文件上传失败: ${error.message}`;
      targetMsg.progress = -1;
    } else {
      // 如果找不到，添加一条错误消息
      const errorMsg = {
        avatar: '/src/assets/assets-ai2.png',
        role: 'assistant',
        content: `❌ 文件上传失败: ${error.message}`,
        reasoning: '',
        logDiag: false,
        rating: -1,
        session_id: session_id,
        message_id: uuidv4(),
        progress: -1,
        datetime: new Date().toLocaleString(),
      };
      chatList.value.unshift(errorMsg);
    }
    MessagePlugin.error(`文件上传失败: ${error.message}`);
  } finally {
    locationUploading.value = false;
    locationFileList.value = [];

    // 触发视图更新
    await nextTick();
  }
};


const systemLogSceneList = [];

// 定义系统消息下拉框选项
const systemLogFieldOptions = ref([]);

// 定义跳板机下拉框选项
const systemJumpNameOptions = ref([]);

const fetchJumpServers = async () => {
  try {
    const response = await axios.get(`${INTELDIGA_API_URL}/api/get-jump-servers`);
    if (response.data.status === 'success') {
      systemJumpNameOptions.value = response.data.data;
      console.log('跳板机列表:', systemJumpNameOptions.value);
    } else {
      MessagePlugin.error('获取跳板机列表失败');
    }
  } catch (error) {
    console.error('获取跳板机列表失败:', error);
    MessagePlugin.error('获取跳板机列表失败');
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
      // 转换数据格式以适应图表
      const local = result.data.local;
      local_jumpName.value = local.jump_name;
      local_targetIp.value = local.target_ip;
      local_shelf.value = local.shelf_number;
      local_slot.value = local.slot_number;
    } else {
      console.error('获取用户常用网元信息失败:', result.message);
    }
  } catch (err) {
    console.error('获取用户常用网元信息失败:', error);
  }
};

const getMainSceneOptions = (field) => {
  if (!field || !systemLogSceneList[field]) return [];
  return Object.keys(systemLogSceneList[field]).map(mainscene => ({
    label: mainscene,
    value: mainscene
  }));
};

const getSubSceneOptions = (field, mainscene) => {
  if (!field || !mainscene || !systemLogSceneList[field]?.[mainscene]) return [];
  return Object.entries(systemLogSceneList[field][mainscene]).map(([subscene, url]) => ({
    label: subscene,
    value: subscene
  }));
};

const handleSubSceneChange = (item) => {
  const { selectLogFieldValue, selectLogMainSceneValue, selectLogSubSceneValue } = item.value || item;

  // 安全访问嵌套属性
  const sceneConfig =
    systemLogSceneList?.[selectLogFieldValue]?.[selectLogMainSceneValue]?.[selectLogSubSceneValue];

  // 如果存在 .guidance 字段，则取值；否则设为 null（或空字符串）
  guidance.value = sceneConfig?.guidance ?? null; // 或 ?? ''

   if (sceneConfig?.guidance) {
   const guidanceText = sceneConfig.guidance;
   const moduleMatch = guidanceText.match(/【模块】\s*(\w+)/);
   if (moduleMatch && moduleMatch[1]) {
      // 将模块参数存储到当前日志下载配置中
      if (item.logDownloadConfig) {
        item.logDownloadConfig.module = moduleMatch[1];
      }
    }
  }
};

// 工具函数：格式化日期为 "YYYY-MM-DD HH:mm:ss"
function formatDateTime(date) {
  const pad = (n) => n.toString().padStart(2, '0');
  return (
    date.getFullYear() +
    '-' +
    pad(date.getMonth() + 1) +
    '-' +
    pad(date.getDate()) +
    ' ' +
    pad(date.getHours()) +
    ':' +
    pad(date.getMinutes()) +
    ':' +
    pad(date.getSeconds())
  );
}

// 构造默认时间范围
const now = new Date();
const eightHoursAgo = new Date(now.getTime() - 8 * 60 * 60 * 1000);

// 当模型选择变化时，如果是日志分析，则添加提示消息
// watch(selectModelValue, (newValue) => {
//   if (newValue?.value === '日志分析') {
//     // 新流程：不再自动显示配置窗口，而是让用户通过输入框触发RDC识别
//     const newItem = {
//       role: 'assistant',
//       logDiag: true,
//       showBothConfigs: true,
//       logDownloadConfig: {  // 包含跳板机配置对象
//         jumpName: local_jumpName,
//         targetIp: local_targetIp,
//         shelf: local_shelf,
//         slot: local_slot,
//         todayOnly: '是'
//       },
//       content: '**请手动上传或自动化拉取日志文件，然后点击开始诊断进行日志分析；在下方输入框中输入故障描述可以自动匹配场景**',
//       datetime: new Date().toLocaleString(),
//       avatar: '/src/assets/assets-ai2.png',
//       selectLogFieldValue: '',
//       selectLogMainSceneValue: '',
//       selectLogSubSceneValue: '',
//       dateRange: [
//         formatDateTime(eightHoursAgo), // "2025-01-01 00:00:00"
//         formatDateTime(now),         // 当前时间
//       ],
//       rating: -1,
//       progress: null,
//       session_id: session_id,
//       message_id: uuidv4(),
//     };
//     chatList.value.unshift(newItem);
//   }
//   if (newValue?.value === '故障单规范检查') {
//     const newItem = {
//       role: 'assistant',
//       logDiag: false,
//       rdcCheck: true,
//       rdcCheckModel: 'nebula',
//       content: '请选择时间范围',
//       datetime: new Date().toLocaleString(),
//       avatar: '/src/assets/assets-ai2.png',
//       dateRange: [
//         formatDateTime(eightHoursAgo), // "2025-01-01 00:00:00"
//         formatDateTime(now),         // 当前时间
//       ],
//       rating: -1,
//       progress: null,
//       session_id: session_id,
//       message_id: uuidv4(),
//     };
//     chatList.value.unshift(newItem);
//   }
// }, { immediate: false });

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

// 处理点赞点击
const handleLikeClick = (item) => {
  if (item.rating === 5) {
    // 已点赞，显示对话框让用户确认或取消
    currentDislikeItem.value = item;
    selectedDislikeReason.value = item.dislikeReason || '';
    dislikeComment.value = item.dislikeComment || '';
    likeDialogVisible.value = true;
  } else {
    // 未评价，显示对话框进行点赞
    currentDislikeItem.value = item;
    selectedDislikeReason.value = '';
    dislikeComment.value = '';
    likeDialogVisible.value = true;
  }
};

// 处理点踩点击
const handleDislikeClick = (item) => {
  if (item.rating === 1) {
    // 已点踩，显示对话框让用户确认或取消
    currentDislikeItem.value = item;
    selectedDislikeReason.value = item.dislikeReason || '';
    dislikeComment.value = item.dislikeComment || '';
    dislikeDialogVisible.value = true;
  } else {
    // 未评价，显示对话框进行点踩
    currentDislikeItem.value = item;
    selectedDislikeReason.value = '';
    dislikeComment.value = '';
    dislikeDialogVisible.value = true;
  }
  // rating === -1 时禁用，不处理
};

// 选择点踩理由
const selectDislikeReason = (reason) => {
  selectedDislikeReason.value = reason;
};

// 取消点踩反馈
const cancelDislikeFeedback = () => {
  if (currentDislikeItem.value && currentDislikeItem.value.rating === 1) {
    // 如果原来是点踩状态，点击取消则取消点踩
    currentDislikeItem.value.rating = 0;
    currentDislikeItem.value.dislikeReason = '';
    currentDislikeItem.value.dislikeComment = '';
    submitFeedback(currentDislikeItem.value.session_id, currentDislikeItem.value.message_id, 0);
  }
  dislikeDialogVisible.value = false;
  currentDislikeItem.value = null;
  selectedDislikeReason.value = '';
  dislikeComment.value = '';
};

// 提交点赞反馈
const submitLikeFeedback = () => {
  if (!currentDislikeItem.value) return;

  const item = currentDislikeItem.value;
  item.rating = 5; // 设置为点踩
  item.dislikeReason = selectedDislikeReason.value;
  item.dislikeComment = dislikeComment.value.trim();

  // 构建反馈数据
  const feedbackData = {
    session_id: item.session_id,
    message_id: item.message_id,
    feedback: item.rating, // 1表示点踩
    dislike_comment: dislikeComment.value.trim(),
    dislike_reason: item.dislikeReason
  };

  submitFeedbackToBackend(feedbackData);

  // 关闭对话框
  likeDialogVisible.value = false;
  currentDislikeItem.value = null;
  selectedDislikeReason.value = '';
  dislikeComment.value = '';
};

// 取消点踩反馈
const cancelLikeFeedback = () => {
  if (currentDislikeItem.value && currentDislikeItem.value.rating === 5) {
    // 如果原来是点赞状态，点击取消则取消点踩
    currentDislikeItem.value.rating = 0;
    currentDislikeItem.value.dislikeReason = '';
    currentDislikeItem.value.dislikeComment = '';
    submitFeedback(currentDislikeItem.value.session_id, currentDislikeItem.value.message_id, 0);
  }
  likeDialogVisible.value = false;
  currentDislikeItem.value = null;
  selectedDislikeReason.value = '';
  dislikeComment.value = '';
};

// 提交点踩反馈
const submitDislikeFeedback = () => {
  if (!currentDislikeItem.value) return;

  // 检查是否选择了reason
  if (!selectedDislikeReason.value) {
    MessagePlugin.warning('请选择点踩理由');
    return;
  }

  const item = currentDislikeItem.value;
  item.rating = 1; // 设置为点踩
  item.dislikeReason = selectedDislikeReason.value;
  item.dislikeComment = dislikeComment.value.trim();

  // 构建反馈数据
  const feedbackData = {
    session_id: item.session_id,
    message_id: item.message_id,
    feedback: item.rating = 1, // 1表示点踩
    dislike_comment: item.dislikeComment,
    dislike_reason:item.dislikeReason
  };

  submitFeedbackToBackend(feedbackData);

  // 关闭对话框
  dislikeDialogVisible.value = false;
  currentDislikeItem.value = null;
  selectedDislikeReason.value = '';
  dislikeComment.value = '';
};

// 提交反馈到后端
const submitFeedback = (session_id, message_id, rating) => {
  const feedbackData = {
    session_id: session_id,
    message_id: message_id,
    feedback: rating, // 1表示点赞，0表示点踩，-1表示无评价
  };

  submitFeedbackToBackend(feedbackData);
};

// 实际的后端请求函数
const submitFeedbackToBackend = async (feedbackData) => {
  try {
    const controller = new AbortController();

    const response = await fetch(`${INTELDIGA_API_URL}/api/submit-feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedbackData),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    if (result.status !== 'success') {
      console.error('提交反馈失败:', result.message);
    }
  } catch (error) {
    console.error('提交反馈请求异常:', error);
  }
};

const handleOperation = function (type, options) {
  console.log('handleOperation', type, options);
};

// 倒序渲染
const chatList = ref([]);
// 记录最近一次解析出来的领域、团队，后续提单时回传
const lastSelectedField = ref('');
const lastSelectedTeam = ref('');
// 保存日志下载任务配置信息（跳板机名称、目标网元IP、子架、槽位等）
const lastLogDownloadData = ref(null);
const clearConfirm = function () {
  chatList.value = [];
};
// 是否显示回到底部按钮
const handleChatScroll = function ({ e }) {
  const scrollTop = e.target.scrollTop;
  isShowToBottom.value = scrollTop < 0;
};

const handleRdcCheckButtonClick = (item) => {
  if (isStreamLoad.value) {
    return;
  }

  if (!item) return;

  if (!item.dateRange || item.dateRange.length < 2) {
    MessagePlugin.warning('请选择完整的日期范围');
    return;
  }

  // 空消息占位
  const params = {
    avatar: '/src/assets/assets-ai2.png',
    // name: 'AI：',
    // datetime: new Date().toLocaleString(),
    content: '',
    reasoning: '',
    role: 'assistant',
    logDiag: false,
    rating: 0,
    progress: null,
    session_id: session_id,
    message_id: uuidv4(),
  };
  chatList.value.unshift(params);

  handleRdcCheckData(item);
};

// 处理系统消息按钮点击
const handleSystemButtonClick = (item) => {
  console.log('系统按钮点击', item.selectLogSubSceneValue);
  // 可在此添加具体业务逻辑，如触发诊断流程

  if (isStreamLoad.value) {
    return;
  }

  if (!item) return;

  if (!item.selectLogSubSceneValue) {
    MessagePlugin.warning('请选择日志场景');
    return;
  }

  if (!item.dateRange || item.dateRange.length < 2) {
    MessagePlugin.warning('请选择完整的日期范围');
    return;
  }

  const paramsScene = {
    avatar: '/src/assets/assets-user3.png',
    // name: 'You：',
    datetime: new Date().toLocaleString(),
    content: item.selectLogSubSceneValue,
    role: 'user',
    message_id: uuidv4(),
  };
  chatList.value.unshift(paramsScene);

  // 空消息占位
  const params = {
    avatar: '/src/assets/assets-ai2.png',
    // name: 'AI：',
    datetime: new Date().toLocaleString(),
    content: '',
    reasoning: '',
    role: 'assistant',
    logDiag: false,
    rating: 0,
    progress: null,
    session_id: session_id,
    message_id: uuidv4(),
  };
  chatList.value.unshift(params);

  handleLogData(item);
  inputText.value = ''; // 清空输入框
};

const inputEnter = function (inputValue) {
  if (isStreamLoad.value) {
    return;
  }

  if (!selectModelValue.value.value) {
    return;
  }

  if (!inputValue) return;

  // 新增：如果已上传图片，拼接图片文件名到消息开头
  let finalMessage = inputValue;
  if (uploadedImageName.value &&
      (selectModelValue.value.value === '故障确认' ||
       selectModelValue.value.value === '直接定位')) {
    finalMessage = `${uploadedImageName.value}\n${inputValue}`;
    uploadedImageName.value = null; // 清空，避免重复使用
  }

  const params = {
    avatar: '/src/assets/assets-user3.png',
    // name: 'You：',
    datetime: new Date().toLocaleString(),
    content: inputValue, // 显示原始问题（不含图片名）
    message_id: uuidv4(),
    role: 'user',
  };
  chatList.value.unshift(params);
  // 空消息占位
  const params2 = {
    avatar: '/src/assets/assets-ai2.png',
    content: '',
    reasoning: '',
    role: 'assistant',
    logDiag: false,
    progress: null,
    session_id: session_id,
    message_id: uuidv4(),
    rating: 0,
    dislikeReason: '',
    dislikeComment: '',
  };
  chatList.value.unshift(params2);

  handleData(finalMessage); // 发送拼接后的消息
  // 记录最近一次用户输入
  inputText.value = ''; // 清空输入框
};

const isValidIPv4 = (ip) => {
  if (typeof ip !== 'string') return false;
  const parts = ip.split('.');
  if (parts.length !== 4) return false;
  return parts.every(part => {
    // 不能有前导零（除非就是 "0"）
    if (part.length > 1 && part.startsWith('0')) return false;
    const num = Number(part);
    return !isNaN(num) && Number.isInteger(num) && num >= 0 && num <= 255;
  });
};

const isValidPositiveIntegerString = (str) => {
  if (typeof str !== 'string') return false;
  // 必须是非空、全数字、且不能以 0 开头（除非就是 "0"，但通常子架/槽位 ≥1）
  // 假设子架/槽位从 1 开始，不允许 "0"
  if (!/^[1-9]\d*$/.test(str)) return false;
  const num = Number(str);
  return Number.isInteger(num) && num > 0 && num <= 65535; // 可按需调整上限
};

// ==============================
// 新增：触发日志下载任务（带进度条）
// ==============================
const triggerLogDownloadTask = (data) => {
  if (isStreamLoad.value) {
    MessagePlugin.warning('任务正在进行中，请稍后...');
    return;
  }

  if (!data.jumpName) {
    MessagePlugin.warning('请选择跳板机');
    return;
  }

  if (!data.targetIp || !isValidIPv4(data.targetIp.trim())) {
    MessagePlugin.warning('请输入有效的网元IP地址（如 192.168.1.1）');
    return;
  }

  if (!data.shelf || !isValidPositiveIntegerString(data.shelf.trim())) {
    MessagePlugin.warning('子架必须为正整数');
    return;
  }

  if (!data.slot || !isValidPositiveIntegerString(data.slot.trim())) {
    MessagePlugin.warning('槽位必须为正整数');
    return;
  }

  // 保存日志下载配置信息，供后续使用
  lastLogDownloadData.value = {
    jumpName: data.jumpName,
    targetIp: data.targetIp.trim(),
    shelf: data.shelf.trim(),
    slot: data.slot.trim(),
    todayOnly: data.todayOnly || '是',
    module: data.module || ''
  };

  const userMsg = {
    avatar: '/src/assets/assets-user3.png',
    // name: 'You：',
    datetime: new Date().toLocaleString(),
    content: `下载${data.jumpName}${data.targetIp}网元${data.shelf}子架${data.slot}槽位单板日志文件`,
    message_id: uuidv4(),
    role: 'user',
  };
  chatList.value.unshift(userMsg);

  // 2. 添加 AI 占位消息（关键：logDiag=true + progress=0）
  const assistantMsg = {
    avatar: '/src/assets/assets-ai2.png',
    role: 'assistant',
    content: '🚀 正在启动日志下载任务...', // 初始描述
    reasoning: '',
    logDiag: false,           // 标记为日志诊断消息 → 触发进度条
    rating: -1,
    session_id: session_id,
    message_id: uuidv4(),
    progress: 0,             // 初始进度为 0（显示进度条）
    datetime: new Date().toLocaleString(),
  };
  chatList.value.unshift(assistantMsg);

  // 3. 启动后台任务（异步流式更新 assistantMsg）
  startLogDownloadWithProgress(data, assistantMsg.message_id);
};

// ==============================
// 执行下载并流式更新进度
// ==============================
const startLogDownloadWithProgress = async (data, messageId) => {
  isStreamLoad.value = true;
  const lastItem = chatList.value[0];

  try {
    const response = await fetch(`${INTELDIGA_API_URL}/api/download-log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name,
        jump_name: data.jumpName,
        target_ip: data.targetIp,
        shelf_number: data.shelf,
        slot_number: data.slot,
        today_only: data.todayOnly === '是' ? true : false,
        module: data.module || '',
        session_id: session_id,
      }),
    });

    if (!response.ok) {
      throw new Error(`服务器返回错误: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            // 更新 content 和 progress
            if (data.status === 'completed') {
              const baseUrl = INTELDIGA_API_URL.replace(/\/$/, '');
              const downloadUrl = `${baseUrl}/download?filename=${encodeURIComponent(data.filename)}&dir_type=${encodeURIComponent("在线诊断用户下载目录")}&session_id=${encodeURIComponent(session_id)}`;
              const markdownLink = `[📥 点击下载日志文件 \`${data.filename}\`](${downloadUrl})`;
              lastItem.content = data.message + '\n\n' + markdownLink +
              '<div style="margin-top: 16px; padding: 8px; background-color: #f0f7ff; border-left: 4px solid #0052d9; border-radius: 4px;">' +
              '<span style="color: #0052d9; font-weight: bold;">💡 日志下载完成，请点击开始诊断</span>' +
              '</div>';
              lastItem.progress = 100;
            } else if (data.status === 'error') {
              lastItem.content = `❌ 下载失败: ${data.message}`;
              lastItem.progress = -1; // 触发 error 状态
            } else {
              // 进度中
              lastItem.content = data.message || '处理中...';
              lastItem.progress = typeof data.progress === 'number' ? data.progress : 0;
            }
          } catch (e) {
            console.error('SSE 数据解析失败:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('下载任务异常:', error);
    const msg = chatList.value.find(m => m.message_id === messageId);
    if (msg) {
      msg.content = `❌ 网络错误: ${error.message}`;
      msg.progress = -1;
    }
  } finally {
    isStreamLoad.value = false;
  }
};

const getProgressStatus = (item) => {
  if (item.progress === -1) return 'error';
  if (item.progress >= 100) return 'success';
  return 'default';
};

const addSubmitRdc = function (message) {
  // 空消息占位
  const params = {
    avatar: '/src/assets/assets-ai2.png',
    // name: 'AI：',
    // datetime: new Date().toLocaleString(),
    content: '是否需要提单',
    reasoning: '',
    role: 'assistant',
    logDiag: false,
    rdcCheck: false,
    session_id: session_id,
    message_id: uuidv4(),
    submit_message: message,
    progress: null,
    rating: -1,
    showSubmitRdcButtons: true
  };
  chatList.value.unshift(params);
};

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
  const endText = '思考过程';
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

/* Started by AICoder, pid:44999974ffe8577142f308a92037f6766f5306f7 */
/**
 * 处理历史会话点击事件，加载指定会话的聊天记录
 * @param {string} history_session - 要加载的历史会话ID
 */
const handleSessionClick = async (history_session) => {
  try {
    // 设置当前会话ID（注意：应使用let/const声明变量）
    session_id = history_session;

    // 向后端API请求消息数据
    const response = await axios.post(`${INTELDIGA_API_URL}/api/getMessages`, {
      account: user.userInfo.name, // 当前用户账号
      session_id: history_session, // 请求的目标会话ID
    });

    if (response.data.status === 'success') {
      let historyMessages = response.data.messages;
      console.log('获取到的聊天记录:', response.data.messages);

      // 清空现有聊天列表准备加载新数据
      chatList.value = [];

      // 倒序处理消息（保证时间顺序正确）
      for (const message of historyMessages) {
        const role = message.role;

        // 用户消息处理
        if (role === 'user') {
          const params = {
            avatar: '/src/assets/assets-user3.png', // 用户头像路径
            datetime: message.create_time, // 消息创建时间
            content: message.content, // 消息内容
            message_id: message.message_id, // 消息唯一标识
            role: 'user', // 角色标识
          };
          chatList.value.unshift(params); // 添加到列表开头保持时间顺序
        }

        // AI回复处理
        else if (role === 'assistant') {
          const params2 = {
            avatar: '/src/assets/assets-ai2.png', // AI头像路径
            datetime: message.create_time, // 消息创建时间
            content: message.content, // 回复内容
            reasoning: message.reason, // 推理过程（预留字段）
            role: 'assistant', // 角色标识
            logDiag: false, // 日志诊断状态
            progress: null, // 进度信息（预留）
            session_id: session_id, // 关联会话ID
            message_id: message.message_id, // 消息唯一标识
            rating: message.feedback, // 评分（预留）
            dislikeReason: message.dislike_reason,
            dislikeComment: message.comment,
          };
          chatList.value.unshift(params2); // 添加到列表开头保持时间顺序
        }

        // 未知角色类型处理
        else {
          console.log('未定义角色类型', role);
        }
      }
    } else {
      // API返回非成功状态时设置错误提示
      error.value = '获取聊天记录失败，请稍后再试。';
    }
  } catch (err) {
    // 网络请求异常处理
    console.error('请求失败:', err);
    error.value = '无法加载聊天记录，请稍后再试。';
  } finally {
    // 无论成功与否都会执行的日志记录
    console.log('请求聊天历史完成');
  }
};

/* Ended by AICoder, pid:44999974ffe8577142f308a92037f6766f5306f7 */

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

  const lastItem = chatList.value[0];

  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    // 直接使用流式接口
    const controller = new AbortController();
    fetchCancel.value = { controller }; // 将 controller 存储起来，以便 onStop 可以访问
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
          mode: selectModelValue.value.value,
          log_mode: selectLogAnalyseValue.value.value,
          reproduce_mode: selectReproduceValue.value.value,
          jump: selectJumpValue.value.value
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
            // 循环结束后，确保最后一次更新被应用
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
                // try {
                //   if (
                //     (selectModelValue.value?.value === 'RDC诊断' ||
                //     selectModelValue.value?.value === '日志分析') &&
                //     lastItem &&
                //     lastItem.dict &&
                //     typeof lastItem.dict === 'object' &&
                //     lastItem.dict.status &&
                //     (lastItem.dict.status === 1 ||
                //     lastItem.dict.status === 2)
                //   ) {
                //     lastItem.showRdcButtons = true;
                //   }
                // } catch (e) {}
                return;
              }

              try {
                const json = JSON.parse(data);
                if (!lastItem) continue; // 防御性编程

                let hasUpdate = false;

                if (json.info_type === 'answer' && json.text) {
                  if (lastItem) {
                    lastItem.content += json.text;
                    if (json.message_id) lastItem.message_id = json.message_id;
                    hasUpdate = true;
                  }
                } else if (json.info_type === 'rdc' && json.text && json.dict) {
                  lastItem.content += json.text;
                  lastItem.dict = json.dict;
                  if (json.message_id) lastItem.message_id = json.message_id;
                  hasUpdate = true;
                } else if (['thought'].includes(json.info_type) && json.text) {
                  lastItem.reasoning += json.text;
                  lastItem.reasoning = lastItem.reasoning.replace(/\\n/g, '\n\n');
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
          if (updatePending) {
              // 方案 A: 简单移除 await，依赖 Vue 批量更新 (推荐先试这个)
              // updatePending = false; 
              
              // 方案 B: 如果还是卡，每处理完一个 read() 包后，让出主线程
              await new Promise(resolve => setTimeout(resolve, 0)); 
              updatePending = false;
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          console.error('读取流时发生错误:', error);
          if (lastItem) {
            lastItem.role = 'error';
            lastItem.content = `流读取错误: ${error.message}`;
          }
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

    if (error.name === 'AbortError') {
      lastItem.content = '请求超时，请重试';
    } else {
      lastItem.content = `网络错误: ${error.message || '未知错误'}`;
    }

    lastItem.role = 'error';
    lastItem.datetime = new Date().toLocaleString();

  } finally {
    // 注意：isStreamLoad 的状态由 processStream 内部的 cleanUp 函数管理
    // 这里不设置 isStreamLoad.value = false，避免过早恢复输入框
    loading.value = false;
    fetchCancel.value = null; // 清理 controller 引用，避免内存泄漏

    // 显示用时xx秒
    lastItem.duration = 5;
  }
};

// RDC按钮交互：是/否
const onRdcYes = (item) => {
  // 1. 检查传入的 item 是否有效及其 content 是否存在
  if (!item || typeof item.content !== 'string' || typeof item.dict !== 'string' && item.dict == null) {
    item.showRdcButtons = false;
    return; // 提前退出
  }

  // 2. 获取当前 assistant 消息的 content、dict
  const content = item.content;
  const dictRaw = item.dict;
  let dict = {};
  dict = dictRaw;

  // 3. 获取dict信息
  const status = dict.status !== undefined ? dict.status : STATUS_ERROR;
  const rdcNumber = dict.rdc !== undefined ? dict.rdc : '';
  const rdcTopic = dict.rdc_topic !== undefined ? dict.rdc_topic : '';
  const rdcDescription = dict.rdc_description !== undefined ? dict.rdc_description : '';
  const field = dict.field !== undefined ? dict.field : '';
  const team = dict.team !== undefined ? dict.team : '';
  const mainscene = dict.mainscene !== undefined ? dict.mainscene : '';
  const subscene = dict.subscene !== undefined ? dict.subscene : '';
  const fault = dict.fault !== undefined ? dict.fault : '';
  console.log(`dict.fault: ${fault}`);

  lastSelectedField.value = field;
  lastSelectedTeam.value = team;

  // 4. 选择日志分析场景
  let matchedOption = null;
  if (String(status) === '1') {
    matchedOption = selectModel.find(opt => opt.value === '日志分析') || null;
  } else if (String(status) === '2') {
    matchedOption = selectModel.find(opt => opt.value === '故障问答') || null;
  }

  // 5. 如果找到匹配项，则更新 selectModelValue
  if (matchedOption) {
    selectModelValue.value = matchedOption;
    console.log(`已将模型选择框更新为: ${matchedOption.label}`);
    if (matchedOption.value=='故障问答') {
      let fillText = fault;
      inputText.value = fillText.trim();
      console.log('已将RDC信息回填到输入框:', fillText.trim());
    } else if (matchedOption.value=='日志分析') {
      // 进入“日志分析”时，按顺序为 领域、团队、主场景、子场景 预填值（优先使用解析值，否则取第一个可选项）
      nextTick(() => {
        // 最新插入的系统过滤项一般位于列表顶部
        const logItem = chatList.value.find((m) => m && m.logDiag === true);
        if (!logItem) return;

        // 1) 领域：仅在解析值存在且匹配到时赋值
        const fieldOpts = systemLogFieldOptions.value || [];
        if (!field) return;
        const foundField = fieldOpts.find((o) => o.value === field || o.label === field);
        if (!foundField) return;
        logItem.selectLogFieldValue = foundField.value;

        // 3) 主场景
        const mainSceneOpts = getMainSceneOptions(logItem.selectLogFieldValue);
        if (!mainscene) return;
        const foundMain = mainSceneOpts.find((o) => o.value === mainscene || o.label === mainscene);
        if (!foundMain) return;
        logItem.selectLogMainSceneValue = foundMain.value;

        // 4) 子场景
        const subSceneOpts = getSubSceneOptions(
          logItem.selectLogFieldValue,
          logItem.selectLogMainSceneValue,
        );
        if (!subscene) return;
        const foundSub = subSceneOpts.find((o) => o.value === subscene || o.label === subscene);
        if (!foundSub) return;
        logItem.selectLogSubSceneValue = foundSub.value;

        // 5) 更新输入框占位符
        handleSubSceneChange(logItem);
      });
    }
  } else {
    console.log('内容中未找到预设的智能体类型，保持当前选择不变。');
    selectModelValue.value = selectModel.find(opt => opt.value === '功能选择');
  }

  // 6. 写入标签（即发即弃）：解析到 RDC 号后触发请求，不等待结果
  if (rdcNumber) {
    axios.post(`${INTELDIGA_API_URL}/api/addTag`, {
      rdc_id: rdcNumber,
      tag: '智能诊断'
    }).catch(() => {});
  }

  // 7. 隐藏按钮
  item.showRdcButtons = false;

  // triggerLogDownloadTask();
};

const onRdcNo = (item) => {
  // item.rdcBtnsDisabled = true;
  item.showRdcButtons = false;
  // 插入占位消息承接新一轮输出
  chatList.value.unshift({
    avatar: '/src/assets/assets-ai2.png',
    content: '',
    reasoning: '',
    role: 'assistant',
  });
  handleData('匹配的不对');
};

// RDC按钮交互：是/否
const onSubmitRdcYes = async (item) => {
  // 1. 检查传入的 item 是否有效及其 message_id 是否存在
  if (!item || typeof item.submit_message !== 'string') {
    console.warn('onSubmitRdcYes: item 或 message 无效', item);
    item.showSubmitRdcButtons = false;
    return; // 提前退出
  }

  // 2. 获取当前 assistant 消息的 content
  const submit_message = item.submit_message;
  
  /* Started by AICoder, pid:l33b758b213ce6e14ec10aaf80d81963141325d1 */
  // 3. 获取日志下载配置信息（跳板机名称、目标网元IP、子架、槽位等）
  const logDownloadData = lastLogDownloadData.value;

  // 检查日志下载配置信息是否为空
  if (!logDownloadData) {
    console.warn('日志下载配置信息为空，请先执行日志下载任务');
    MessagePlugin.warning('日志下载配置信息为空，请先执行日志下载任务');
    // 可以选择是否继续执行，这里选择继续但记录警告
  } else {
    // 检查各个字段是否为空
    const missingFields = [];
    if (!logDownloadData.jumpName) missingFields.push('跳板机名称');
    if (!logDownloadData.targetIp) missingFields.push('目标网元IP');
    if (!logDownloadData.shelf) missingFields.push('子架');
    if (!logDownloadData.slot) missingFields.push('槽位');
    
    if (missingFields.length > 0) {
      console.warn('日志下载配置信息不完整，缺少字段:', missingFields.join(', '));
      MessagePlugin.warning(`日志下载配置信息不完整，缺少字段: ${missingFields.join(', ')}`);
    } else {
      console.log('日志下载配置信息:', {
        jumpName: logDownloadData.jumpName,
        targetIp: logDownloadData.targetIp,
        shelf: logDownloadData.shelf,
        slot: logDownloadData.slot,
        todayOnly: logDownloadData.todayOnly
      });
    }
  }

  // 4. 调用后端接口获取版本信息（仅需跳板机名称与目标IP）
  let versionInfo = null; // 保存查询结果，便于后续传给后端
  if (logDownloadData && logDownloadData.jumpName && logDownloadData.targetIp) {
    try {
      const versionResp = await fetch(`${INTELDIGA_API_URL}/api/show_version`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jump_name: logDownloadData.jumpName,
          target_ip: logDownloadData.targetIp,
        }),
      });

      if (!versionResp.ok) {
        throw new Error(`版本查询接口返回错误: ${versionResp.status}`);
      }

      const versionData = await versionResp.json();
      if (versionData.status === 'success') {
        console.log('版本查询成功', versionData);
        versionInfo = versionData.info || null;
        MessagePlugin.success('版本信息查询成功');
      } else {
        console.warn('版本查询失败', versionData);
        MessagePlugin.warning(versionData.message || '版本信息查询失败');
      }
    } catch (error) {
      console.error('调用版本查询接口失败:', error);
      MessagePlugin.error(`版本信息查询失败: ${error.message}`);
    }
  } else {
    console.warn('缺少跳板机名称或目标IP，无法调用版本查询接口');
  }
  /* Ended by AICoder, pid:l33b758b213ce6e14ec10aaf80d81963141325d1 */

  // 准备发送给后端的数据
  const requestData = {
    description: submit_message,
    title: "草稿",
    user_id: user.userInfo.name,
    field: lastSelectedField.value || '',
    team: lastSelectedTeam.value || '',
    version_data: versionInfo || '',
  };

  // 调用后端API保存数据
  const response = await fetch(`${INTELDIGA_API_URL}/api/saveChgDraft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData),
  });

  if (!response.ok) {
    const responseData = await response.json();
    throw new Error(`HTTP错误! 状态码: ${response.status} 错误原因: ${responseData.message || '未知错误'}`);
  }

  const responseData = await response.json();

  if (responseData.status !== 'success') {
    throw new Error(responseData.message || '保存场景数据失败');
  }

  // 4. 执行原来的操作：禁用按钮并隐藏它们
  item.showSubmitRdcButtons = false;
  item.content = `草稿已创建 [草稿](${responseData.url})`;
};

const onSubmitRdcNo = (item) => {
  item.showSubmitRdcButtons = false;
  item.content = "用户不需要提单";
};

const handleLogData = async (item) => {
  loading.value = true;
  isStreamLoad.value = true;
  const lastItem = chatList.value[0];

  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    // 直接使用流式接口
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 480000); // 480秒超时

    const url = systemLogSceneList[item.selectLogFieldValue][item.selectLogMainSceneValue][item.selectLogSubSceneValue]["url"];
    lastSelectedField.value = systemLogSceneList[item.selectLogFieldValue][item.selectLogMainSceneValue][item.selectLogSubSceneValue]["field"];
    lastSelectedTeam.value = systemLogSceneList[item.selectLogFieldValue][item.selectLogMainSceneValue][item.selectLogSubSceneValue]["team"];

    const response = await fetch(`${INTELDIGA_API_URL}/api/tryChat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name,
        session_id: session_id,
        token: user.uacToken,
        message: {
          input: url,
          starttime: item.dateRange[0],
          endtime: item.dateRange[1],
          mode: "日志分析",
          knowledge: "",
          logmessage: inputText.value
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

      nextTick().then(() => {
        const textareaEl = document.querySelector('.t-textarea__inner');
        if (textareaEl) textareaEl.focus();
      });
    };

    // 处理读取到的数据
    const processStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          console.log(value);
          if (done) {
            cleanUp();
            addSubmitRdc(lastItem.content);
            break;
          }

          // 解码并添加到缓冲区
          buffer += decoder.decode(value, { stream: true });

          // 按行处理数据
          const lines = buffer.split('\n');
          // 保留最后一行不完整的数据
          buffer = lines.pop();

          let rdc_flag = true;

          for (const line of lines) {
            if (line.startsWith('data:')) {
              const data = line.slice(5).trim(); // 移除 'data:' 前缀

              if (data === '[DONE]') {
                cleanUp();
                if(rdc_flag)
                {
                  addSubmitRdc(lastItem.content);
                }
                return;
              }

              try {
              const json = JSON.parse(data);
              if (json.info_type === 'answer' && json.text) {
                if (lastItem) {
                  lastItem.content += json.text;
                  // 保存 message_id 用于评分
                  if (json.message_id) {
                    lastItem.message_id = json.message_id;
                  }
                  // 强制触发视图更新
                  await nextTick();
                }
              }
              else if(json.info_type === 'error'){
                if (lastItem) {
                  lastItem.content += json.text;
                  lastItem.rating = -1;
                  // 保存 message_id 用于评分
                  if (json.message_id) {
                    lastItem.message_id = json.message_id;
                  }
                  // 强制触发视图更新
                  await nextTick();
                  rdc_flag = false;
                }
              }
            } catch (e) {
              console.error('解析JSON失败:', e);
            }
            }
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          console.error('读取流时发生错误:', error);
          if (lastItem) {
            lastItem.role = 'error';
            lastItem.content = `流读取错误: ${error.message}`;
          }
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

    if (error.name === 'AbortError') {
      lastItem.content = '请求超时，请重试';
    } else {
      lastItem.content = `网络错误: ${error.message || '未知错误'}`;
    }

    lastItem.role = 'error';
    lastItem.datetime = new Date().toLocaleString();

  } finally {
    // 注意：isStreamLoad 的状态由 processStream 内部的 cleanUp 函数管理
    loading.value = false;

    // 显示用时xx秒
    lastItem.duration = 5;
  }
};

const handleRdcCheckData = async (item) => {
  loading.value = true;
  isStreamLoad.value = true;
  const lastItem = chatList.value[0];

  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }
    
    // 直接使用流式接口
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时

    const response = await fetch(`${INTELDIGA_API_URL}/api/rdc-list-check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: user.userInfo.name,
        token: user.uacToken,
        session_id: lastItem.session_id,
        message_id: lastItem.message_id,
        starttime: item.dateRange[0],
        endtime: item.dateRange[1],
        modelname: item.rdcCheckModel,
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

      nextTick().then(() => {
        const textareaEl = document.querySelector('.t-textarea__inner');
        if (textareaEl) textareaEl.focus();
      });
    };

    // 处理读取到的数据
    const processStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            cleanUp();
            break;
          }

          // 解码并添加到缓冲区
          buffer += decoder.decode(value, { stream: true });

          // 按行处理数据
          const lines = buffer.split('\n');
          // 保留最后一行不完整的数据
          buffer = lines.pop();

          for (const line of lines) {
            if (line.startsWith('data:')) {
              const data = line.slice(5).trim(); // 移除 'data:' 前缀

              if (data === '[DONE]') {
                cleanUp();
                return;
              }

              try {
                const json = JSON.parse(data);
                if (json.info_type === 'answer' && json.text) {
                  if (lastItem) {
                    lastItem.content += json.text;
                    // 强制触发视图更新
                    await nextTick();
                  }
                }
                if(json.info_type === 'download'){
                  const downloadUrl = `${INTELDIGA_API_URL}/api/export-rdc-check-records?session_id=${encodeURIComponent(lastItem.session_id)}&message_id=${encodeURIComponent(lastItem.message_id)}`;
                  const markdownLink = `[📥 点击下载检查结果 ](${downloadUrl})`;
                  lastItem.content += markdownLink || '✅ 日志文件已准备就绪';
                  // 强制触发视图更新
                  await nextTick();
                }
              } catch (e) {
                console.error('解析JSON失败:', e);
              }
            }
          }
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          console.error('读取流时发生错误:', error);
          if (lastItem) {
            lastItem.role = 'error';
            lastItem.content = `流读取错误: ${error.message}`;
          }
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

    if (error.name === 'AbortError') {
      lastItem.content = '请求超时，请重试';
    } else {
      lastItem.content = `网络错误: ${error.message || '未知错误'}`;
    }

    lastItem.role = 'error';
    lastItem.datetime = new Date().toLocaleString();

  } finally {
    // 注意：isStreamLoad 的状态由 processStream 内部的 cleanUp 函数管理
    loading.value = false;

    // 显示用时xx秒
    lastItem.duration = 5;
  }
};

const historySessionRecord = ref([]); // 用于保存聊天记录
const HistoryGet = async () => {
  try {
    const response = await axios.post(`${INTELDIGA_API_URL}/api/getSessions`, {
      account: user.userInfo.name
    });

    if (response.data.status === 'success') {
      historySessionRecord.value = response.data.sessions;
      //console.log('获取到的会话记录:', response.data.sessions);
    } else {
      error.value = '获取会话记录失败，请稍后再试。';
    }
  } catch (err) {
    console.error('请求失败:', err);
    error.value = '无法加载会话记录，请稍后再试。';
  } finally {
    console.log('请求历史会话成功');
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

const onSceneRead = async () => {
  console.log('开始读取场景数据...');

  const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络请求失败，请检查网络连接',
    TIMEOUT_ERROR: '请求超时，请稍后重试',
    SERVER_ERROR: '服务器返回错误',
    INVALID_JSON: '返回的数据不是有效的JSON格式',
    INVALID_DATA_FORMAT: '返回的数据格式不正确，预期是数组',
    UNKNOWN_ERROR: '发生未知错误',
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    let response;
    try {
      response = await fetch(`${INTELDIGA_API_URL}/api/getScenarios`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json' },
        body: JSON.stringify({ status: '已上线' }),
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

    if (!response.ok) {
      const errorMsg = `HTTP错误! 状态码: ${response.status}`;
      console.error(errorMsg);
      MessagePlugin.error(ERROR_MESSAGES.SERVER_ERROR);
      throw new Error(errorMsg);
    }

    let responseData;
    try {
      responseData = await response.json();
      console.log('服务器响应：', responseData);

    } catch (error) {
      console.error('解析响应JSON失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
      throw new Error(ERROR_MESSAGES.INVALID_JSON);
    }

    if (responseData.status !== 'success') {
      const errorMsg = responseData.message || '读取场景数据失败';
      console.error('服务器返回错误:', errorMsg);
      MessagePlugin.error(errorMsg);
      throw new Error(errorMsg);
    }

    let sceneData = responseData.sceneData || [];

    if (typeof sceneData === 'string') {
      try {
        sceneData = JSON.parse(sceneData);
      } catch (error) {
        console.error('解析场景数据JSON失败:', error);
        MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
        throw new Error(ERROR_MESSAGES.INVALID_JSON);
      }
    }

    if (!Array.isArray(sceneData)) {
      console.error('场景数据格式不正确:', sceneData);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
      throw new Error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
    }

    sceneData.forEach(item => {
      const field = item.field;
      const team = item.team;
      const mainscene = item.mainscene;
      const subscene = item.subscene;
      const url = item.url;
      const userGuidance = item.UserGuidance;

      if (!systemLogSceneList[field]) {
        systemLogSceneList[field] = {};
      }

      // 避免重复场景
      if (!systemLogSceneList[field][mainscene]) {
        systemLogSceneList[field][mainscene] = [];
      }

      // 避免重复场景
      if (!systemLogSceneList[field][mainscene][subscene]) {
        systemLogSceneList[field][mainscene][subscene] = {url:url, guidance:userGuidance, field:field, team:team};
      }
    });

    console.log(systemLogSceneList);
    // 生成领域选项
    systemLogFieldOptions.value = Object.keys(systemLogSceneList).map(key => ({
      label: key,
      value: key
    }));

    console.log('场景数据处理完成');
  } catch (error) {
    console.error('场景数据读取过程中出错:', error);
    if (!Object.values(ERROR_MESSAGES).includes(error.message)) {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};

// 在onMounted中添加检查
onMounted(async () => {
  await checkAuth(); // 先检查登录状态
  const isValid = await verifyToken();
  if (!isValid) {
    router.push('/login');
  }
  // onSceneRead();
  fetchJumpServers(); // 获取跳板机列表
  // fetchNetInformation();
});
const inputText = ref('');

// 文件上传相关
const beforeUpload = async (fileObject) => {
  const file = fileObject.raw;
  const name = file.name.toLowerCase();

  // 放行 .tar.gz（accept 无法识别）
  if (name.endsWith('.tar.gz')) {
    return true;
  }

  return true; // 允许上传
};

// 文件选择后触发上传（TDesign 已校验通过）
const onFileChange = (data) => {
  const file = data[0].raw;
  if (file) uploadFile(file);
};

// --- 工具函数（保持简洁）---
async function isLikelyTextFile(file) {
  const buffer = await file.slice(0, 1024).arrayBuffer();
  const view = new Uint8Array(buffer);
  let binary = 0;
  for (const b of view) {
    if (b < 9 || (b > 13 && b < 32) || b > 126) binary++;
  }
  return binary / view.length <= 0.15;
}

const exportQaDetailsData = async () => {
  let loadingInstance;
  try {
    loadingInstance = MessagePlugin.loading('正在导出文件...', { duration: 0 });

    const [startTime, endTime] = dateRange.value;
    if (!startTime || !endTime) {
      throw new Error('请选择完整的时间范围');
    }

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-qa-details`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        start_time: startTime,  // ✅ 修正字段名
        end_time: endTime      // ✅ 修正字段名
      })
    });

    if (!response.ok) {
      // 尝试解析 JSON 错误，否则用文本
      let errorMsg = `导出失败：HTTP ${response.status}`;
      try {
        const errorJson = await response.json();
        errorMsg = errorJson.details || errorJson.error || errorMsg;
      } catch {
        const errorText = await response.text();
        if (errorText) errorMsg += ` - ${errorText}`;
      }
      throw new Error(errorMsg);
    }

    const blob = await response.blob();
    if (blob.size === 0) {
      throw new Error('服务器返回空文件，请检查时间范围是否有数据');
    }

    // 获取文件名
    let filename = `qa-details_${new Date().toISOString().split('T')[0]}.xlsx`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename\*?=['"]?(?:UTF-8'')?([^'"]+)['"]?/i);
      if (matches && matches[1]) {
        // 处理 RFC 5987 编码（如 filename*=UTF-8''xxx）
        try {
          filename = decodeURIComponent(matches[1].replace(/['"]/g, ''));
        } catch (e) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }
    }

    // 触发下载
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    MessagePlugin.success(`导出成功：${filename}`);

  } catch (err) {
    console.error('场景活跃度数据导出失败:', err);
    MessagePlugin.error(err.message || '未知错误，请联系管理员');
  } finally {
    if (loadingInstance?.close) {
      loadingInstance.close();
    }
  }
};

// --- 上传逻辑 ---
async function uploadFile(file) {
  uploading.value = true;
  uploadStatus.value = null;

  const formData = new FormData();
  formData.append('file', file);
  // formData.append('mode', selectModelValue.value?.value || '');
  formData.append('mode', selectLogAnalyseValue.value?.value || '');
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

// 新增：图片上传前校验
const beforeImageUpload = async (fileObject) => {
  const file = fileObject.raw;
  const name = file.name.toLowerCase();

  // 只允许图片格式
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp'];
  if (!allowedTypes.includes(file.type)) {
    MessagePlugin.warning('只支持上传图片文件（PNG、JPG、JPEG、GIF、BMP）');
    return false;
  }

  return true;
};

// 新增：图片选择后触发上传
const onImageChange = (data) => {
  const file = data[0].raw;
  if (file) uploadImageToXingxiaomi(file);
};

// 新增：上传图片到兴小秘
async function uploadImageToXingxiaomi(file) {
  imageUploading.value = true;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', session_id);
  formData.append('account', user.userInfo.name);

  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/uploadImage`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (res.data.success) {
      MessagePlugin.success('图片上传成功');
      uploadedImageName.value = file.name; // 保存文件名

      // 在聊天界面显示上传成功提示（不显示图片）
      const params = {
        avatar: '/src/assets/assets-user3.png',
        datetime: new Date().toLocaleString(),
        content: `📷 图片 "${file.name}" 已上传成功，请在输入框中描述问题`,
        role: 'user',
        isImage: true
      };
      chatList.value.unshift(params);
    } else {
      throw new Error(res.data.error || '上传失败');
    }
  } catch (error) {
    const msg = error.response?.data?.error || error.message || '上传失败';
    MessagePlugin.error(`图片上传失败: ${msg}`);
  } finally {
    imageUploading.value = false;
    imageFileList.value = [];
  }
}

const shouldShowLogAnalyseSelect = computed(() => {
  // 只有当选择的模型是"日志分析"时才显示日志分析下拉框
  return selectModelValue.value?.value === '日志分析';
});

const shouldShowUploadForLocation = computed(() => {
  // 只有当选择的模型是"上站定位"时才显示文件上传按钮
  return selectModelValue.value?.value === '上站定位';
});

const shouldShowReproduceSelect = computed(() => {
  // 只有当选择的模型是"复现定位"时才显示复现定位下拉框
  return selectModelValue.value?.value === '复现定位';
});

const shouldShowJumpSelect = computed(() => {
  // 只有当选择的模型是"在线诊断"时才显示选择下拉框
  return selectModelValue.value?.value === '上站定位';
});

// 新增：控制图片上传按钮显示条件
const shouldShowImageUpload = computed(() => {
  return selectModelValue.value?.value === '故障确认' ||
         selectModelValue.value?.value === '直接定位';
});

const inputPlaceholder = computed(() => {
  // 获取当前选中的模型值（默认空字符串避免报错）
  const modelValue = selectModelValue.value?.value || '';

  // 根据不同模型返回对应提示语
  switch (modelValue) {
    case '故障确认':
      return '麻烦您描述一下具体故障现象，我会调取现有特性案例、历史实例、整改方案及 CCB 决策库，为您判断是否属于已知问题';
    case '直接定位':
      return '麻烦您描述一下具体故障现象，我将调取故障定位一页纸及故障定位指导手册，为您梳理排查思路、匹配标准排查流程，快速检索定位方法，并确认专属排查定位方案';
    case '日志分析':
      return '请您上传需要分析的日志，同时输入 具体故障现象和现场背景，我会结合日志内容精准分析、定位问题根因';
    case '上站定位':
      return '请根据网元所属位置选择对应实验室跳板机，并描述具体故障现象及现场背景。我将远程登录设备、采集相关信息，精准分析并定位问题根因';
    case '复现定位':
      return '请输入提问';
    default:
      return '请选择要进行的业务子活动';
  }
});

</script>

<style lang="less">
.t-rate__item .t-icon {
  stroke: #000 !important;
  fill: none !important;
}

.t-rate__item--active .t-icon {
  stroke: #000 !important;
  fill: #000 !important;
}

/* 使用 Flex 布局让评分和操作按钮在同一行 */
.rating-container {
  display: flex;
  align-items: center; /* 垂直居中对齐 */
  gap: 8px; /* 按钮之间的间距，可选 */
}

/* 新增样式 */
.upload-status {
  padding: 8px 12px;
  border-radius: 6px;
  margin: 8px 0;
  font-size: 14px;
}

.upload-success {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.upload-error {
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

.uploading-indicator {
  padding: 8px 12px;
  color: #1890ff;
  font-size: 14px;
}
.time-range-picker {
  display: flex;
  align-items: center;
  margin-top: 10px;
  padding: 8px 12px;
  background-color: var(--td-bg-color-container);
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.time-range-picker .t-date-picker {
  flex: 1;
  margin: 0 8px;
}
.time-range-divider {
  margin: 0 8px;
  color: var(--td-text-color-placeholder);
}
.time-range-label {
  font-size: 12px;
  color: var(--td-text-color-secondary);
  white-space: nowrap;
}
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

  .new-chat-wrapper {
    position: absolute;
    z-index: 4000;
    top: 0px;
    left: 0px;
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

  .history-chat-wrapper {
    position: absolute;
    z-index: 4000;
    top: 0px;
    left: 60px;
  }

  .corpusadd {
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

  .metricsBoard {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 0px; /* 距离页面顶部的距离为0 */
    left: 180px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      // 浅层阴影
      0px 16px 32px rgba(0, 0, 0, 0.2),
      // 中层主阴影（更明显）
      0px 32px 48px rgba(0, 0, 0, 0.15); // 深层长投影（营造悬浮感）
  }

  .qaExport {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 0px; /* 距离页面顶部的距离为0 */
    left: 240px; /* 距离页面左边的距离为0 */
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

.log-download-progress {
  width: 300px;
  height: 10px;
}

/* .t-progress__bar：轨道（背景容器）—— 无色 + 边框 */
.log-download-progress .t-progress__bar {
  background-color: #fff; /* 背景白色 */
  border: 1px solid #000; /* 黑色边框 */
  border-radius: 6px;
  height: 10px !important;
  position: relative;
  overflow: hidden; /* 防止圆角内层溢出 */
}

/* .t-progress__inner：进度填充 —— 蓝色 */
.log-download-progress .t-progress__inner {
  background-color: #0052d9 !important;
  border-radius: 5px;
  height: 100%;
}

.log-download-progress .t-progress__info {
  color: #000;
  font-size: 14px;
  margin-left: 8px;
}

.t-chat-sender__upload {
  display: none !important;
}

// 点赞点踩组件样式
.rating-container {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.feedback-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dislike-reasons {
  padding: 8px 0;

  .reason-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }
}

// 确保对话框背景完全不透明 - 使用最高优先级
.t-dialog {
  background-color: #ffffff !important;
  background: #ffffff !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  opacity: 1 !important;
  border-radius: 4px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
}

.t-dialog__header {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border-bottom: 1px solid #e7e7e7 !important;
}

.t-dialog__body {
  background-color: #ffffff !important;
  background: #ffffff !important;
  opacity: 1 !important;
  color: #333333 !important;
  min-height: 200px !important;
}

.t-dialog__footer {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border-top: 1px solid #e7e7e7 !important;
}

.t-dialog__ctx {
  background-color: rgba(0, 0, 0, 0.5) !important; // 遮罩层保持半透明
}

// 确保对话框内部元素背景为白色
.dislike-reasons {
  background-color: #ffffff !important;
  min-height: 200px;
  padding: 16px;
}

.dislike-reasons p {
  color: #666666 !important;
}

// 强制覆盖所有可能的透明度
.t-dialog,
.t-dialog *,
.t-dialog__header,
.t-dialog__body,
.t-dialog__footer,
.t-dialog__content {
  background-color: #ffffff !important;
  background-image: none !important;
  opacity: 1 !important;
}

// 对话框footer样式
.dialog-footer {
  display: flex;
  justify-content: flex-start;
  gap: 12px;
  width: 100%;
  padding: 16px 0 0 0;
}
</style>
