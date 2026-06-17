<template>
  <div class="m-chat">
    <t-drawer
      class="m-chat-drawer"
      v-model:visible="drawVisible"
      size="1200px"
      :footer="false"
      :close-btn="true"
      :size-draggable="true"
    >
      <template #header>
        <span class="title">
          Hi，我是
          <span style="color: #1a16fc; font-weight: 600">{{ aiChatTitle }}</span>
          AI智能体
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

        <t-tooltip content="提示词模版" placement="top">
          <t-button
            class="m-chat-prompt"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="handlePromptTemplate"
          >
            <icon name="chat-bubble-error" />
          </t-button>
        </t-tooltip>

        <t-drawer v-model:visible="promptDrawVisible" :footer="false" header="提示词模版" size="330px">
          <t-space direction="vertical" style="width: 100%">
            <div class="prompt-search-container">
              <t-button theme="primary" @click="openCreatePromptDialog">
                <template #icon><add-icon /></template>
                新建
              </t-button>
              <t-input v-model="searchText" placeholder="搜索提示词模版..." clearable>
                <template #suffixIcon>
                  <search-icon :style="{ cursor: 'pointer' }" />
                </template>
              </t-input>
            </div>
            <t-space direction="vertical" style="width: 100%">
              <!-- 插入列表形式的t-card -->
              <div v-for="(template, index) in filteredTemplates" :key="index">
                <t-tooltip placement="left" theme="light" :show-arrow="false">
                  <template #content>
                    <div style="white-space: pre-line; max-height: 400px; overflow-y: auto">
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
                        content="确定要删除这个提示词模板吗？"
                        @confirm="() => handleTemplateDelete(template)"
                      >
                        <a href="javascript:void(0)" style="text-decoration: none; color: #ff4d4f; font-size: 14px"
                          >删除</a
                        >
                      </t-popconfirm>
                    </template>
                    <template #footer>
                      <div style="font-size: 12px; color: #666">
                        <span>创建人: {{ template.creator }}</span>
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
                <div
                  style="
                    white-space: pre-line;
                    max-width: 300px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-size: 14px;
                    line-height: 1.5;
                  "
                  v-html="getHistoryTooltipContent(record.session_id)"
                ></div>
              </template>
              <div class="history-item" @click="handleSessionClick(record.session_id)">
                <div class="history-content">{{ record.origin }}</div>
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
              <template #actions v-if="item.showActions !== false">
                <t-space><t-chat-action
                  :content="item.content"
                  :is-good="item.isGood"
                  :operation-btn="['good', 'bad', 'replay', 'copy']"
                  @operation="(type, options) => handleOperation(type, options, index)"
                />
               </t-space>
              </template>
            </t-chat-item>
          </template>

          <template #footer>
            <t-chat-sender
              ref="chatSenderRef"
              v-model="inputText"
              :stop-disabled="streamLoading"
              :textarea-props="{ placeholder: '请输入消息...', autosize: { minRows: 2, maxRows: 12 } }"
              @stop="handleOnStop"
              @send="handleOnSend"
            >
              <template #prefix>
                <div class="m-chat-select">
                  <t-select v-model="selectModelValue" :options="selectModel" value-type="object"></t-select>
                  <t-select v-model="selectAgentValue" :options="selectAgent" value-type="object"></t-select>
                  <t-select v-model="selectFieldValue" :options="selectField" value-type="object"></t-select>
                  <t-select v-model="selectComponentValue" :options="selectComponent" value-type="object" :min-collapsed-num="1" multiple></t-select>
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

    <!-- ========== 新增：新建/编辑提示词模板弹窗 ========== -->
    <t-dialog
      v-model:visible="createPromptVisible"
      :header="isEditMode ? '编辑提示词模板' : '新建提示词模板'"
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
        <t-form-item label="摘要" name="subtitle" :rules="[{ required: true, message: '请输入模板摘要' }]">
          <t-input v-model="createForm.subtitle" placeholder="请输入模板摘要" />
        </t-form-item>
        <t-form-item label="内容" name="content" :rules="[{ required: true, message: '请输入模板内容' }]">
          <t-textarea
            v-model="createForm.content"
            placeholder="请输入提示词内容"
            :autosize="{ minRows: 5, maxRows: 10 }"
          />
        </t-form-item>
        <t-form-item label="场景" name="scene" :rules="[{ required: true, message: '请输入使用场景' }]">
          <t-input v-model="createForm.scene" placeholder="请输入通用场景，或组件/模块名称" />
        </t-form-item>
        <t-form-item label="创建人" name="creator">
          <t-input v-model="createForm.creator" disabled />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import numeral from 'numeral';
import { ref, nextTick, computed, onUnmounted, watch, onMounted, onBeforeMount, toRaw } from 'vue';
import { Icon, ArrowDownIcon, SearchIcon, AddIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { getChartListColor } from '@/utils/color';
import { v4 as uuidv4 } from 'uuid';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
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

let session_id = uuidv4();

const selectModel = [
  {
    label: '星云大模型',
    value: 'nebula',
  },
  {
    label: '通义千问-中兴',
    value: 'qwen3-zte',
  },
  {
    label: '通义千问-阿里',
    value: 'qwen',
  },
  {
    label: 'Qwen3-coder',
    value: 'qwen3-coder',
  },
  {
    label: 'Deepseek-V3',
    value: 'deepseek-V3',
  },
  {
    label: 'Kimi-K2',
    value: 'kimi-K2',
  },
];

const selectModelValue = ref({
    label: '通义千问-中兴',
    value: 'qwen3-zte',
});

const selectAgent = [
  { label: '组件智能体',value: 'ComponentAgentNew' },
  { label: '业务代码生成', value: 'BusinessCodeGen' },
  { label: 'UT生成', value: 'UTGen' },
  { label: 'FT生成', value: 'FTGen' },
  { label: '巡检工具代码生成', value: 'ZxsemCodeGen' },
];
const selectAgentValue = ref({});

const selectField = [
  { label: 'L0', value: 'L0' },
  { label: 'L1', value: 'L1' },
  { label: 'L2', value: 'L2' },
  { label: '支撑', value: 'OSP' },
  { label: '仿真', value: 'SIMU' },
  { label: '智控', value: 'WASON' },
  { label: '数据', value: 'DATA' },
];

const selectFieldValue = ref({});


const selectComponent = ref([]); // 动态加载的组件选项
const selectComponentValue = ref([])

const componentOptionsMap = ref({});
const aiApplicationMap = ref({});

const isSettingDefaultFromTitle = ref(false);

const loadComponentData = async () => {
  const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络请求失败',
    SERVER_ERROR: '服务器错误',
    INVALID_JSON: '返回数据不是 JSON',
    INVALID_FORMAT: '返回数据不是数组',
    UNKNOWN_ERROR: '未知错误',
  };
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  try {
    const fetchPromises = selectField.map(async (field) => {
      const domain = field.value;
      if (domain == 'SIMU'){
        const componentData = [];
        return { domain, componentData };
      }else{
        const response = await fetch(`${SERVER_API_URL}/api_data/Table_read`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ table: 'Component', domain: domain }),
          signal: controller.signal, // 如果有 AbortController 逻辑可以保留
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const responseData = await response.json();
        if (responseData.status !== 'success') {
          throw new Error(responseData.message || '获取组件数据失败');
        }
        const componentData = responseData.tableData || [];
        if (!Array.isArray(componentData)) {
          throw new Error(ERROR_MESSAGES.INVALID_FORMAT);
        }
        return { domain, componentData };
      }
    });
    // 并发执行所有请求
    const results = await Promise.all(fetchPromises);
    for (const { domain, componentData } of results) {
      componentOptionsMap.value[domain] = componentData;
    }
  } catch (error) {
    console.error('加载组件选项失败:', error);
    if (error.name !== 'AbortError') {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    return [];
  } finally {
    clearTimeout(timeoutId);
  }
};

const loadApplicationData = async () => {
  const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络请求失败',
    SERVER_ERROR: '服务器错误',
    INVALID_JSON: '返回数据不是 JSON',
    INVALID_FORMAT: '返回数据不是数组',
    UNKNOWN_ERROR: '未知错误',
  };
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  try {
    const requestData = {
      table_name: 'AI应用库',
      conditions: {},
    };
    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });
    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }
    const responseData = await response.json();
    const dataList = responseData.data;
    const allowedAiTypes = ['BusinessCodeGen', 'UTGen', 'FTGen', 'ZxsemCodeGen'];
    const allowedDomains = ["L0", "L1", "L2", "OSP", "WASON", "DATA", "SIMU"];
    for (const aiType of allowedAiTypes) {
      for (const domain of allowedDomains) {
        const matched = dataList.filter(
          (item) => item["AI应用类型"] === aiType && item["领域"] === domain
        );
        const key = `${aiType},${domain}`;
        aiApplicationMap.value[key] = matched;
      }
    }
  } catch (error) {
    console.error('加载组件选项失败:', error);
    if (error.name !== 'AbortError') {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  } finally {
    clearTimeout(timeoutId);
  }
};

const getRdcComponent = (htmlString, head_str) => {
  const hasTable = /<table/i.test(htmlString);
  if (!hasTable) {
    if(head_str === '需求描述'){
      const target = '<strong>AI输出:</strong>';
      var formerPart = '';
      if (htmlString.includes(target)) {
        const index = htmlString.indexOf(target);
        formerPart = htmlString.substring(0, index);
      }else{
        formerPart = htmlString;
      }
      const tmp = document.createElement('div');
      tmp.innerHTML = formerPart;
      const all_description = tmp.textContent || tmp.innerText || '';
      return all_description;
    }
    return '';
  }
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, 'text/html');
  const rows = doc.querySelectorAll('tr');
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const cells = row.querySelectorAll('td, th');
    for (let j = 0; j < cells.length; j++) {
      const cell = cells[j];
      const cellText = cell.textContent?.trim() || '';
      if (cellText === head_str) {
        if (j + 1 < cells.length) {
          const rightCell = cells[j + 1];
          const rightCellText = rightCell.textContent?.trim() || '';
          return rightCellText;
        }
        return "";
      }
    }
  }
  return '';
}

const setDefaultCompOptions = (async () => {
  const requestData = { "rdc_id": props.aiChatTitle };
  //实时获取组件名称和领域，能获取到的话，不然保持默认
  const response = await fetch(`${SERVER_API_URL}/api_data/get_rdc_component`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData),
  });
  if (!response.ok) {
    throw new Error(`HTTP错误! 状态码: ${response.status}`);
  }
  const responseData = await response.json();
  const description_html = responseData.tableData;
  const rdc_description = getRdcComponent(description_html, '需求描述');
  if(rdc_description != "") {
    inputText.value = rdc_description;
  }
  const agent_type = getRdcComponent(description_html, '智能体类型');
  let rdc_component_name = getRdcComponent(description_html, '智能体名称');
  const exists = selectAgent.some(item => item.label === agent_type);
  if(exists) {
    const matchedItem = selectAgent.find(item => item.label === agent_type);
    const agent_type_value = matchedItem.value;
    let rdc_select_field = "";
    let rdc_select_component = [];
    let rdc_select_name = [];
    let important_key = "";
    // 分割逗号分隔的字符串
    rdc_component_name = rdc_component_name.split(',').map(name =>
      name.trim().replace(/[\r\n\s]+/g, '')
    );
    if (agent_type_value === "ComponentAgentNew"){
      let flag = true;
      outerLoop:
      for (const dictKey in componentOptionsMap.value) {
        const list = componentOptionsMap.value[dictKey]; // 当前键对应的数组
        if (flag) {
          for (const obj of list) {
            const temp_name = obj["组件名称"].trim().replace(/[\r\n\s]+/g, '');
            // 检查是否在目标组件名称列表中
            if (rdc_component_name.includes(temp_name)) {
              rdc_select_field = dictKey;
              rdc_select_component.push(JSON.stringify(obj));
              rdc_select_name.push(temp_name);
              flag = false;
              // 如果找到了所有组件，就跳出外层循环
              if (rdc_select_component.length === rdc_component_name.length) {
                break outerLoop;
              }
            }
          }
        }
      }
      important_key = "组件名称";
    }else{
      let flag = true;
      outerLoop:
      for (const field of selectField) {
        const type_key = `${agent_type_value},${field.value}`;
        const arr_list = aiApplicationMap.value[type_key]; // 当前键对应的数组
        if (flag) {
          for (const obj of arr_list) {
            // 取第一个,后面直接跳出
            const temp_name = obj["AI应用名称"].trim().replace(/[\r\n\s]+/g, '');
            if (rdc_component_name.includes(temp_name)) {
              rdc_select_field = field.value;
              rdc_select_component.push(JSON.stringify(obj));
              rdc_select_name.push(temp_name);
              flag = false;
              break outerLoop;
            }
          }
        }
      }
      important_key = "AI应用名称";
    }
    selectAgentValue.value = {label: agent_type, value: agent_type_value};
    if (rdc_select_field && rdc_select_component){
      selectFieldValue.value = selectField.find((item) => item.value === rdc_select_field);
    }else{
      selectFieldValue.value = { label: 'L0', value: 'L0' };
    }
    const defaultDomain = selectFieldValue.value?.value;
    let rawData = [];
    if(important_key == "组件名称"){
      rawData = componentOptionsMap.value[defaultDomain];
    }else{
      rawData = aiApplicationMap.value[`${agent_type_value},${defaultDomain}`];
    }
    const uniqueComponents = new Set();
    const options = [];
    for (const item of rawData) {
      const componentName = item[important_key];
      if (componentName && !uniqueComponents.has(componentName)) {
        uniqueComponents.add(componentName);
        options.push({
          label: componentName,
          value: JSON.stringify(item),
        });
      }
    }
    selectComponent.value = options;
    if (options.length > 0) {
      if(rdc_select_field && rdc_select_component && rdc_component_name){
        // selectComponentValue.value =  {label:rdc_component_name, value:rdc_select_component};
        selectComponentValue.value = rdc_select_component.map((field, index) => ({
          label: rdc_component_name[index] || '',
          value: rdc_select_component[index],
        }))
      }else{
        selectComponentValue.value = [];
      }
    } else {
      selectComponentValue.value = [];
    }
  }else{
    isSettingDefaultFromTitle.value = false;
    selectAgentValue.value = { label: '组件智能体', value: 'ComponentAgentNew'}
    selectFieldValue.value = { label: 'L0', value: 'L0' };
    selectComponentValue.value = [];
  }
})


watch(
  () => props.aiChatTitle,
  async (newValue) => {
    isSettingDefaultFromTitle.value = true;
    await setDefaultCompOptions();
    isSettingDefaultFromTitle.value = false;
  }
);

watch(
  [selectAgentValue, selectFieldValue],
  ([agentRef, fieldRef]) => {
    const new_agent = agentRef.value;
    const new_field = fieldRef.value;
    if (isSettingDefaultFromTitle.value) {
      return;
    }
    if(new_agent == "ComponentAgentNew") {
      const rawData = componentOptionsMap.value[new_field];
      const uniqueComponents = new Set();
      const options = [];
      for (const item of rawData) {
        const componentName = item['组件名称'];
        if (componentName && !uniqueComponents.has(componentName)) {
          uniqueComponents.add(componentName);
          options.push({
            label: componentName,
            value: JSON.stringify(item),
          });
        }
      }
      selectComponent.value = options;
      if (options.length > 0) {
        selectComponentValue.value = [options[0]];
      }else{
        selectComponentValue.value = [];
      }
    }else{
      const rawData = aiApplicationMap.value[`${new_agent},${new_field}`];
      const uniqueComponents = new Set();
      const options = [];
      for (const item of rawData) {
        const componentName = item['AI应用名称'];
        if (componentName && !uniqueComponents.has(componentName)) {
          uniqueComponents.add(componentName);
          options.push({
            label: componentName,
            value: JSON.stringify(item),
          });
        }
      }
      selectComponent.value = options;
      if (options.length > 0) {
        selectComponentValue.value = [options[0]];
      } else {
        selectComponentValue.value = [];
      }
    }
  }
)

onMounted(async () => {
  await loadComponentData(); // 加载所有领域组件数据到 componentOptionsMap.value
  console.log("组件选项:");
  console.log(componentOptionsMap);
  await loadApplicationData();
  console.log("DN应用库选项:");
  console.log(aiApplicationMap);
});



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


// ========== 新增：新建提示词模板相关状态 ==========
const createPromptVisible = ref(false); // 控制新建弹窗显示
const createLoading = ref(false); // 保存按钮的加载状态
const isEditMode = ref(false); // 是否为编辑模式
const createForm = ref({
  // 表单数据
  title: '',
  subtitle: '',
  content: '',
  scene: '',
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
    scene: props.aiChatTitle || '', // 场景字段默认取aiChatTitle的值
    creator: user.userInfo.name || '',
  };
  createPromptVisible.value = true;
};

// ========== 新增：保存新建/编辑的模板 ==========
const saveNewTemplate = async () => {
  createLoading.value = true;

  try {
    const response = await fetch(`${SERVER_API_URL}/api_chat/API_Prompt_set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: createForm.value.title,
        subtitle: createForm.value.subtitle,
        content: createForm.value.content,
        scene: createForm.value.scene,
        creator: createForm.value.creator,
        reference_count: createForm.value.reference_count, // 保留引用次数
        // 根据你的后端接口，可能还需要其他字段
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === 'success') {
      MessagePlugin.success(isEditMode.value ? '模板保存成功' : '模板创建成功');
      // 可选：刷新模板列表
      TemplatesGet();
      createPromptVisible.value = false; // 关闭弹窗
    } else {
      MessagePlugin.error(data.message || '保存模板失败');
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
    const response = await fetch(`${SERVER_API_URL}/api_chat/API_Prompt_get`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        search: searchKeyword, // 支持传入搜索词，空字符串表示获取全部
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === 'success') {
      templates.value = data.prompts; // ✅ 正确字段名：prompts
    } else {
      error.value = data.message || '获取模板失败，请稍后再试。';
    }
  } catch (err) {
    error.value = '无法加载模板数据，请稍后再试。';
    console.error('Fetch templates error:', err); // 建议加上错误日志
  } finally {
    console.log('请求 Templates 完成'); // 修正拼写：Template -> Templates
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
    const response = await fetch(`${SERVER_API_URL}/api_chat/API_History_chat_get`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // 可根据需要添加认证头，例如：
        // 'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        user: user.userInfo.name,
      }),
      // 如需取消请求，可保留 signal：
      // signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === 'success') {
      historyChatRecord.value = data.chat_records;
    } else {
      error.value = '获取聊天记录失败，请稍后再试。';
    }
  } catch (err) {
    error.value = '无法加载聊天记录，请稍后再试。';
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
const getHistoryTooltipContent = (session_id) => {
  // 1. 只筛选 user 和 assistant 的记录
  const sessionRecords = historyChatRecord.value
    .filter((record) => record.session_id === session_id && (record.role === 'user' || record.role === 'assistant'))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  if (!sessionRecords.length) {
    return '该会话没有聊天记录';
  }

  // 2. 构建显示内容（显示所有记录）
  let tooltipContent = '';

  sessionRecords.forEach((record, index) => {
    const roleLabel = record.role === 'user' ? `${user.userInfo.name}` : 'AI';
    // 格式化时间，只显示月/日 时:分
    const date = new Date(record.timestamp);
    const time = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    // 使用HTML标签加粗时间和角色（不加maxLength限制）
    tooltipContent += `<strong>${time} ${roleLabel}:</strong>
${record.origin}
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

const promptDrawVisible = ref(false);
const handlePromptTemplate = () => {
  promptDrawVisible.value = true;
  // searchText.value = props.aiChatTitle; // 设置默认搜索词为aiChatTitle
  TemplatesGet(); // 获取模板数据
};

// 引用提示词模版 —— 替换模式（清空后设置）
const handleTemplateReference = async (template) => {
  inputText.value = template.content?.trimStart();

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
    const response = await fetch(`${SERVER_API_URL}/api_chat/API_Prompt_set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: template.title,
        subtitle: template.subtitle,
        content: template.content,
        scene: template.scene,
        creator: template.creator,
        reference_count: (template.reference_count || 0) + 1, // 增加引用计数
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === 'success') {
      console.log('引用计数更新成功');
      // 可选：刷新模板列表
      TemplatesGet();
    } else {
      console.error('引用计数更新失败:', data.message || '未知错误');
    }
  } catch (err) {
    console.error('无法更新引用计数:', err);
  }
};

// 修改提示词模板
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
  };
  // 显示新建/编辑弹窗
  createPromptVisible.value = true;
};

// 删除提示词模板
const handleTemplateDelete = async (template) => {
  try {
    const response = await fetch(`${SERVER_API_URL}/api_chat/API_Prompt_del`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: user.userInfo.name,
        creator: template.creator,
        title: template.title,
      }),
    });

    let data;
    try {
      data = await response.json(); // 尝试解析 JSON
    } catch (parseError) {
      // 如果解析失败（比如后端返回非 JSON），使用默认错误信息
      throw new Error('服务器返回了无效数据');
    }

    if (data.status === 'success') {
      MessagePlugin.success('模板删除成功');
      // 刷新模板列表
      TemplatesGet();
    } else {
      // 显示后端返回的具体错误信息
      MessagePlugin.error(data.message || '删除失败：未知错误');
    }
  } catch (err) {
    // 网络错误、请求失败、解析失败等都会进入这里
    MessagePlugin.error(`无法删除模板：${err.message}`);
  }
};

/**
 * 处理聊天操作（点赞、点踩、重发、复制等）
 */
const handleOperation = async (type, options, index) => {
  console.log('handleOperation', type, options, index);
  if(type === "good") {
    const char_dict = chatList.value[index];
    chatList.value[index].isGood = !chatList.value[index].isGood;
    if (chatList.value[index].isGood === true){
      const requestData = {
        "rdc_id": props.aiChatTitle,
        "content": char_dict["content"]
      }
      //实时获取组件名称和领域，能获取到的话，不然保持默认
      const response = await fetch(`${SERVER_API_URL}/api_data/write_rdc_component`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }
      const responseData = await response.json();
      MessagePlugin.success("AI输出同步RDC成功!");
    }
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
    avatar: '/src/assets/assets-user3.png',
    datetime: new Date().toLocaleString(),
    content: inputValue,
    role: 'user',
    showActions: true, // 用户消息始终显示操作按钮
    isGood: false,    //控制点赞点踩
  });

  // 添加AI回答占位项
  chatList.value.unshift({
    avatar: '/src/assets/assets-ai2.png',
    datetime: new Date().toLocaleString(),
    content: '',
    reasoning: '',
    role: 'assistant',
    showActions: false, // 初始时不显示操作按钮
    textLoading: true, // 显示加载状态
    isGood: false,    //控制点赞点踩
  });

  handleData(inputValue);
  inputText.value = '';
};

// const onComponentStatusUpdate = async (load_data) => {
//     try {
//       const payload = {
//         domain: selectFieldValue.value.value || '',
//         component: load_data.组件名称 || '',
//         description: load_data.组件描述 || '',
//         code_server: load_data.代码服务器 || '',
//         file_list: load_data.相关文件 || '',
//       };

//       console.log("payload", payload);
//       const response = await fetch(`${SERVER_API_URL}/agent_component/API_Component_status_get`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(payload),
//       });
//       if (!response.ok) {
//         throw new Error(`HTTP ${response.status}`);
//       }
//       const result = await response.json();
//       if (result.status !== 'success') {
//         throw new Error(result.message || '后端返回失败');
//       }
//       const { code_size, agent_status } = result.data;
//       load_data.代码规模 = numeral(code_size / 3).format('0.0a');
//       load_data.智能体状态 = agent_status || '未支持'; // 防止 undefined
//       load_data.代码目录 = load_data.相关文件;
//       delete load_data.相关文件;
//       return load_data
//     } catch (error) {
//       console.warn(`组件 ${load_data.组件名称} 状态更新失败:`, error.message);
//     }
// };


const onComponentStatusUpdate = async (load_data_array) => {
  // 并行处理所有组件
  const updatePromises = load_data_array.map(async (load_data) => {
    const payload = {
      domain: selectFieldValue.value.value || '',
      component: load_data.组件名称 || '',
      description: load_data.组件描述 || '',
      code_server: load_data.代码服务器 || '',
      file_list: load_data.相关文件 || '',
    };
    const response = await fetch(`${SERVER_API_URL}/agent_component/API_Component_status_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const result = await response.json();
    if (result.status !== 'success') {
      throw new Error(result.message || '后端返回失败');
    }
    const { code_size, agent_status } = result.data;
    // 更新组件数据
    load_data.代码规模 = numeral(code_size / 3).format('0.0a');
    load_data.智能体状态 = agent_status || '未支持';
    load_data.代码目录 = load_data.相关文件;
    delete load_data.相关文件;
    console.log(`组件 "${load_data.组件名称}" 状态更新成功`);
    return load_data;
  });
  // 等待所有更新完成
  const results = await Promise.all(updatePromises);
  const successCount = results.filter(item => !item._updateFailed).length;
  const failCount = results.length - successCount;
  console.log(`批量更新完成: 成功 ${successCount} 个, 失败 ${failCount} 个`);
  return results;
}


/**
 * 处理AI数据请求和响应
 * 向服务器发送用户消息并处理流式响应
 * @param {string} inputValue - 用户输入的内容
 */
const handleData = async (inputValue) => {
  streamLoading.value = true;

  // 创建 AbortController
  const controller = new AbortController();
  fetchCancel.value = controller;

  // 获取当前回答项的引用
  const currentResponse = chatList.value[0];

  try {
    const send_data = {
      user: user.userInfo.name,
      session_id,
      request_id: uuidv4(),
      model: selectModelValue.value.value,
      agent: selectAgentValue.value.value,
      icenter: true,
      rdc: true,
      think: false,
      content: inputValue,
      context: props.aiChatContext,
      component: props.aiChatTitle,
      knowledge: 'NoneKnowledge',
    }
    console.log("send_data", send_data);

    if (selectAgentValue.value.value == "ComponentAgentNew"){
      if (selectComponentValue.value && Object.keys(selectComponentValue.value).length > 0) {
        var load_data = selectComponentValue.value.map(item => JSON.parse(item.value));
        console.log("load_data", load_data);
        var new_load_data = await onComponentStatusUpdate(load_data);
        console.log("new_load_data", new_load_data);
        send_data.context =  JSON.stringify(new_load_data);
        send_data.component = selectComponentValue.value.map(item => item.label).join(',');
      }else{
        send_data.context = props.aiChatContext;
        send_data.component = props.aiChatTitle;
        send_data.agent = "chat";
      }
    }else{
      // 非DN场景现在都暂时调用通用问答
      const content = selectComponentValue.value[0].value;
      const new_content = JSON.parse(content);
      send_data.context =  content;
      if(new_content["AI应用平台"] === "DN"){
        send_data.agent = "DN";
      }else{
        send_data.agent = "chat";
      }
    }
    // 使用新的agent接口
    const response = await fetch(`${SERVER_API_URL}/api_chat/Agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(send_data),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || 'Network response was not ok');
    }

    // 直接处理流式响应，不再需要额外的EventSource连接
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let rawBuffer = ''; // 存储原始SSE数据
    let textBuffer = ''; // 存储解析后的文本内容
    let updateTimer = null;

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
            // 回答完成，显示操作按钮
            currentResponse.showActions = true;
            currentResponse.textLoading = false;
            streamLoading.value = false;
            focusInput();
            return;
          }

          // 解码并处理数据
          const chunk = decoder.decode(value, { stream: true });
          rawBuffer += chunk;

          // 处理SSE格式的数据 (每行以"data: "开头)
          const lines = rawBuffer.split('\n');
          rawBuffer = lines.pop() || ''; // 最后一行可能是不完整的，保留在缓冲区

          for (const line of lines) {
            if (line.trim() === '') continue;

            // 检查是否是SSE格式的数据行
            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6); // 移除"data: "前缀

              if (dataStr === '[DONE]') {
                // 立即更新任何剩余的文本
                if (textBuffer) {
                  currentResponse.content += textBuffer;
                  textBuffer = '';
                }
                currentResponse.showActions = true;
                currentResponse.textLoading = false;
                streamLoading.value = false;
                focusInput();
                return;
              }

              try {
                const data = JSON.parse(dataStr);
                if (data.text) {
                  // 将文本添加到缓冲区
                  textBuffer += data.text;

                  // 使用缓冲机制优化性能
                  if (updateTimer) clearTimeout(updateTimer);
                  updateTimer = setTimeout(() => {
                    currentResponse.content += textBuffer;
                    currentResponse.textLoading = false;
                    textBuffer = '';
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
          // 确保在出错时也显示所有已接收的文本
          if (textBuffer) {
            currentResponse.content += textBuffer;
            textBuffer = '';
          }
          currentResponse.content += `\n流处理错误: ${error.message || 'Unknown error occurred'}`;
          currentResponse.showActions = true;
          currentResponse.textLoading = false;
          streamLoading.value = false;
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
    currentResponse.showActions = true; // 显示操作按钮
    currentResponse.textLoading = false; // 停止加载
    streamLoading.value = false;
  }
};

defineExpose({
  chatRef,
});

watch(
  () => props.aiChatAgent,
  (newAgent) => {
    // 根据传入的 agent 设置下拉框默认值
    const agentOption = selectAgent.find((opt) => opt.value === newAgent);
    if (agentOption) {
      selectAgentValue.value = agentOption;
    }
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

      .t-select {
        width: 240px;
        height: var(--td-comp-size-m);
        margin-right: var(--td-comp-margin-s);

        .t-input {
          border-radius: 32px;
          padding: 0 15px;
        }

        .t-input.t-is-focused {
          box-shadow: none;
        }

        .t-tag {
          max-width: 200px; /* 设置最大宽度 */
          overflow: hidden;
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
      max-width: 100% !important;
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

    /* 提示词模板搜索框布局 */
    .prompt-search-container {
      width: 100%;
      display: flex;
      gap: 10px;
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
