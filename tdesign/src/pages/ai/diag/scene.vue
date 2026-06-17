<template>
  <div class="board-main">

    <t-tooltip content="返回诊断会话" placement="top">
      <t-button class="back-to-chat" size="large" theme="primary" shape="circle" variant="base" @click='jumpToChatPage'>
        <icon name="arrow-left" />
      </t-button>
    </t-tooltip>

    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button shape="circle" variant="base" theme="primary" onClick={onTableAiChat}> AI </t-button>
        <t-select v-model="field" :options="fieldOptions" placeholder="请选择领域"> </t-select>
        <t-button @click='onTableRead'>读取</t-button>
        <t-button @click='onTableCreate'>新建</t-button>
        <!-- 搜索框 -->
        <t-input
          v-model="searchText"
          placeholder="请输入关键词进行搜索..."
          clearable
          style="width: 300px"
          @keyup.enter="onSearch"
        >
          <template #suffixIcon>
            <search-icon @click="onSearch" :style="{ cursor: 'pointer' }" />
          </template>
        </t-input>
      </t-space>

      <t-enhanced-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="filteredTableData"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="650"
        table-layout="fixed"
        resizable
        style="width: 100%"
        @row-edit="onRowEdit"
      />
    </t-space>

    <!-- 编辑对话框 -->
    <t-dialog
      v-model:visible="diagVisible"
      header="新建场景"
      :on-confirm="onSubmitCreate"
      :on-close="onCloseEdit"
      :confirm-loading="loading"
      confirmBtn="保存"
      cancelBtn="关闭"
      destroy-on-close
      width="650"
      placement="top"
      :top="40"
    >
      <!-- 居中容器，限制宽度并居中 -->
      <div style="max-width: 600px; margin: 0 auto; padding: 0 20px">
        <!-- 添加滚动容器，设置固定高度 -->
        <div style="max-height: 70vh; overflow-y: auto; padding-right: 10px">
          <t-form
            v-if="currentEditScene"
            class="edit-form"
            ref="editFormRef"
            label-align="right"
            :data="currentEditScene"
            :rules="editRules"
            :label-width="120"
            :status-icon="false"
          >
            <div style="text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 24px;">
              基本信息
            </div>

            <t-form-item label="领域" name="领域">
              <t-select v-model="field" :disabled="true" />
            </t-form-item>

            <t-form-item label="团队" name="团队">
              <t-select v-model="currentEditScene.团队" :options="teamTypeOptions" placeholder="请选择团队" />
            </t-form-item>

            <t-form-item label="防火墙" name="防火墙">
              <t-input
                v-model="currentEditScene.防火墙"
                placeholder="请输入防火墙姓名工号"
                clearable
              />
            </t-form-item>

            <t-form-item label="支持分析场景" name="支持分析场景">
              <t-select v-model="currentEditScene.支持分析场景" :options="supportTypeOptions" placeholder="请选择支持分析场景" />
            </t-form-item>

            <div style="text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 24px;">
              场景大类
            </div>

<t-form-item label="故障类型" name="故障类型">
              <t-select v-model="currentEditScene.故障类型"
              :options="faultTypeOptions"
              @change="currentEditScene.大类名称='';currentEditScene.来源='';currentEditScene.层次='';currentEditScene.功能='';currentEditScene.板卡类型='';currentEditScene.框架组件='';currentEditScene.指令名称='';currentEditScene.业务类型='';currentEditScene.故障现象='';"
              placeholder="请选择故障类型" />
            </t-form-item>

            <t-form-item label="大类名称" name="大类名称">
              <t-select v-model="currentEditScene.大类名称"
              :options="sceneCategoryOptions"
              @change="currentEditScene.来源='';currentEditScene.层次='';currentEditScene.功能='';currentEditScene.板卡类型='';currentEditScene.框架组件='';currentEditScene.指令名称='';currentEditScene.业务类型='';currentEditScene.故障现象='';"
              placeholder="请选择大类名称" />
            </t-form-item>

            <!-- Started by AICoder, pid:k8147j9ef6hbbac14574090f70625d14e5f4c79c -->
            <!-- 来源选择 -->
            <t-form-item v-if="sourceOptions.length > 0" label="来源" name="来源">
              <t-select v-model="currentEditScene.来源" :options="sourceOptions" placeholder="请选择来源" />
            </t-form-item>

            <!-- 层次选择 -->
            <t-form-item v-if="levelOptions.length > 0" label="层次" name="层次">
              <t-select v-model="currentEditScene.层次" :options="levelOptions" placeholder="请选择层次" />
            </t-form-item>

            <!-- 功能选择 -->
            <t-form-item v-if="functionOptions.length > 0" label="功能" name="功能">
              <t-select v-model="currentEditScene.功能"
              :options="functionOptions"
              @change="currentEditScene.板卡类型='';currentEditScene.框架组件='';currentEditScene.指令名称='';currentEditScene.业务类型='';currentEditScene.故障现象='';"
              placeholder="请选择功能" />
            </t-form-item>
            <!-- Ended by AICoder, pid:k8147j9ef6hbbac14574090f70625d14e5f4c79c -->

            <div style="text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 24px;">
              场景小类
            </div>

            <!-- Started by AICoder, pid:8161b6d62ar44c2143ef092de0261f1a70a91eca -->
            <!-- Started by AICoder, pid:ze272a887bb934414b5d0959a074a874da24e95a -->
            <!-- 动态 textarea 字段（根据配置决定是否显示） -->
            <template v-for="(faultObjectField, _) in faultObjectFieldList" :key="faultObjectField.key">
              <t-form-item
                v-if="shouldShowFaultObjectField(faultObjectField.key)"
                :label="faultObjectField.label"
                :name="faultObjectField.key"
              >
                <!-- 动态判断使用 input 还是 select -->
                <template v-if="getFaultObjectFieldOption(faultObjectField.key).length === 0">
                  <t-input
                    v-model="currentEditScene[faultObjectField.key]"
                    :placeholder="`请输入${faultObjectField.label}`"
                    clearable
                  />
                </template>
                <template v-else>
                  <t-select
                    v-model="currentEditScene[faultObjectField.key]"
                    :options="getFaultObjectFieldOption(faultObjectField.key)"
                    :placeholder="`请选择${faultObjectField.label}`"
                    clearable
                  />
                </template>
              </t-form-item>
            </template>
            <!-- Ended by AICoder, pid:ze272a887bb934414b5d0959a074a874da24e95a -->
            <!-- 故障现象选择 -->
            <t-form-item label="故障现象" name="故障现象">
              <t-select v-model="currentEditScene.故障现象" :options="faultPhenomenonOptions" placeholder="请选择故障现象" />
            </t-form-item>
            <!-- Ended by AICoder, pid:8161b6d62ar44c2143ef092de0261f1a70a91eca -->

            <t-form-item label="故障描述" name="故障描述">
              <t-textarea
                v-model="currentEditScene.故障描述"
                placeholder="请输入故障描述"
                :autosize="{ minRows: 3, maxRows: 6 }"
              />
            </t-form-item>
          </t-form>
        </div>
      </div>
    </t-dialog>

    <!-- 编辑对话框 -->
    <t-dialog
      v-model:visible="diagEditVisible"
      :header="`编辑场景 ${currentEditRow ? ('-' + currentEditRow.场景) : ''}`"
      :on-confirm="onSubmitEdit"
      :on-close="onCloseEdit"
      :confirm-loading="loading"
      confirmBtn="保存"
      cancelBtn="关闭"
      destroy-on-close
      width="650"
      placement="top"
      :top="40"
    >
      <!-- 居中容器，限制宽度并居中 -->
      <div style="max-width: 600px; margin: 0 auto; padding: 0 20px">
        <!-- 添加滚动容器，设置固定高度 -->
        <div style="max-height: 70vh; overflow-y: auto; padding-right: 10px">
          <t-form
            v-if="currentEditRow"
            class="edit-form"
            ref="editFormRef"
            label-align="right"
            :data="currentEditRow"
            :rules="editRowRules"
            :label-width="120"
            :status-icon="false"
          >
            <t-form-item label="领域" name="领域">
              <t-select v-model="currentEditRow.领域" :disabled="true" />
            </t-form-item>

            <t-form-item label="团队" name="团队">
              <t-select v-model="currentEditRow.团队" :options="teamTypeOptions" placeholder="请选择团队" />
            </t-form-item>

            <t-form-item label="防火墙" name="防火墙">
              <t-input
                v-model="currentEditRow.防火墙"
                placeholder="请输入防火墙姓名工号"
                clearable
              />
            </t-form-item>

            <t-form-item label="支持分析场景" name="支持分析场景">
              <t-select v-model="currentEditRow.支持分析场景" :disabled="true" />
            </t-form-item>

            <t-form-item label="场景" name="场景">
              <t-input v-model="currentEditRow.场景"/>
            </t-form-item>

            <t-form-item label="子场景" name="子场景">
              <t-input v-model="currentEditRow.子场景"/>
            </t-form-item>

            <t-form-item label="场景描述" name="场景描述">
              <t-textarea
                v-model="currentEditRow.场景描述"
                placeholder="请输入场景描述"
                :autosize="{ minRows: 3, maxRows: 6 }"
              />
            </t-form-item>

            <t-form-item label="用户引导" name="用户引导">
              <t-textarea
                v-model="currentEditRow.用户引导"
                placeholder="请输入用户引导"
                :autosize="{ minRows: 3, maxRows: 6 }"
              />
            </t-form-item>
          </t-form>
        </div>
      </div>
    </t-dialog>

    <!-- 状态列表弹窗 -->
    <t-dialog
      v-model:visible="statusDiagVisible"
      header="上线状态"
      :footer="false"
      width="60%"
      destroy-on-close
    >
      <t-table
        :data="statusData"
        :columns="statusDialogColumns"
        max-height="500"
        row-key="sub_scene_name"
        bordered
        resizable
      />
    </t-dialog>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, onMounted, computed, reactive } from 'vue';
import { Input, Select, MessagePlugin, Tag } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { Icon } from 'tdesign-icons-vue-next';
import { useRouter } from 'vue-router';

import AiChat from '@/pages/ai/chat/chat.vue';

const INTELDIGA_API_URL = import.meta.env.VITE_INTELDIGA_API_URL;
const user = useUserStore();
const router = useRouter();

const diagVisible = ref(false);
const diagEditVisible = ref(false);
const currentEditScene = ref(null); // 当前正在编辑的场景
const currentEditRow = ref(null); // 当前正在编辑的行的数据
const editFormRef = ref(null);
const loading = ref(false); // 加载状态

// 搜索相关
const searchText = ref('');
const mainSceneOptionsMap = ref({});
const cfgSubSceneOptionsMap = ref({});
const oprSubSceneOptionsMap = ref({});
const funcSubSceneOptionsMap = ref({});


// 团队类型选项映射，根据领域(field)确定可用团队
const teamTypeOptionsMap = {};

// 基于当前 field 值计算可用的团队选项
const teamTypeOptions = computed(() => {
  const sceneField = field.value;
  if (!sceneField) return [];
  return teamTypeOptionsMap[sceneField] || [];
});

// 支持分析场景类型选项
const supportTypeOptions = [
  { label: '日志分析', value: '日志分析' },
];

// 故障类型选项
const faultTypeOptions = [
  { label: '功能类', value: '功能类' },
  { label: '发放类', value: '发放类' },
  { label: '运行类', value: '运行类' },
];

// 计算属性：根据故障类型返回大类名称选项
const sceneCategoryOptions = computed(() => {
  const faultType = currentEditScene.value.故障类型;
  if (!faultType) return [];

  // 获取对应故障类型下的所有大类名称
  const categories = Object.keys(mainSceneOptionsMap.value[faultType] || {});
  return categories.map(category => ({
    label: category,
    value: category
  }));
});

/* Started by AICoder, pid:g8147j9ef6ybbac14574090f70625d34e5f8c79c */
// 计算属性：根据故障类型和大类名称返回来源选项
const sourceOptions = computed(() => {
  const faultType = currentEditScene.value.故障类型;
  const category = currentEditScene.value.大类名称;
  if (!faultType || !category) return [];

  const sources = mainSceneOptionsMap.value[faultType]?.[category]?.['来源'] || [];
  return sources.map(source => ({
    label: source,
    value: source
  }));
});

// 计算属性：根据故障类型和大类名称返回层次选项
const levelOptions = computed(() => {
  const faultType = currentEditScene.value.故障类型;
  const category = currentEditScene.value.大类名称;
  if (!faultType || !category) return [];

  const levels = mainSceneOptionsMap.value[faultType]?.[category]?.['层次'] || [];
  return levels.map(level => ({
    label: level,
    value: level
  }));
});

// 计算属性：根据故障类型和大类名称返回功能选项
const functionOptions = computed(() => {
  const faultType = currentEditScene.value.故障类型;
  const category = currentEditScene.value.大类名称;
  if (!faultType || !category) return [];

  const functions = mainSceneOptionsMap.value[faultType]?.[category]?.['功能'] || [];
  return functions.map(func => ({
    label: func,
    value: func
  }));
});
/* Ended by AICoder, pid:g8147j9ef6ybbac14574090f70625d34e5f8c79c */

/* Started by AICoder, pid:z161bsd62a244c2143ef092de1261f2a70a71eca */

// ======================
// 字段配置（要动态显示的 textarea 字段）
// ======================
const faultObjectFieldList = ref([
  { key: '板卡类型', label: '板卡类型' },
  { key: '框架组件', label: '框架组件' },
  { key: '指令名称', label: '指令名称' },
  { key: '功能名称', label: '功能名称' },
  { key: '业务类型', label: '业务类型' },
  { key: '业务层次', label: '业务层次' },
  { key: '模块类型', label: '模块类型' },
  { key: '监控功能', label: '监控功能' },
  { key: '同步功能', label: '同步功能' },
  { key: '告警框架', label: '告警框架' },
  { key: 'APO功能', label: 'APO功能' },
  { key: 'P端口类型', label: 'P端口类型' },
  { key: 'OAM类型', label: 'OAM类型' },
  { key: 'OPM功能', label: 'OPM功能' },
  { key: 'OTDR功能', label: 'OTDR功能' },
  { key: 'APR功能', label: 'APR功能' },
  { key: 'EDFA功能', label: 'EDFA功能' }
]);

// ======================
// 核心：判断字段是否应在当前场景下显示
// ======================
function shouldShowFaultObjectField(name) {
  const { 故障类型: faultType, 大类名称: category, 功能: functionValue } = currentEditScene.value;

  if (!faultType || !category) return false;

  let subSceneOptions = null;
  switch (faultType) {
    case '发放类':
      subSceneOptions = cfgSubSceneOptionsMap.value;
      break;
    case '运行类':
      subSceneOptions = oprSubSceneOptionsMap.value;
      break;
    case '功能类':
      subSceneOptions = funcSubSceneOptionsMap.value;
      break;
    default:
      return false;
  }

  if (!subSceneOptions) return false;

  const key = functionValue === '' ? category : `${category}[${functionValue}]`;
  const faultObject = subSceneOptions[key]?.['故障对象'];
  return !!faultObject && name in faultObject;
}

// ======================
// 核心：判断字段的选项
// ======================
function getFaultObjectFieldOption(name) {
  const { 故障类型: faultType, 大类名称: category, 功能: functionValue } = currentEditScene.value;

  if (!faultType || !category) return false;

  let subSceneOptions = null;
  switch (faultType) {
    case '发放类':
      subSceneOptions = cfgSubSceneOptionsMap.value;
      break;
    case '运行类':
      subSceneOptions = oprSubSceneOptionsMap.value;
      break;
    case '功能类':
      subSceneOptions = funcSubSceneOptionsMap.value;
      break;
    default:
      return false;
  }

  if (!subSceneOptions) return false;

  const key = functionValue === '' ? category : `${category}[${functionValue}]`;
  const options = subSceneOptions[key]?.['故障对象']?.[name] || [];
  return options.map(option => ({
    label: option,
    value: option
  }));
}

// 计算属性：根据故障类型、大类名称和功能返回故障现象选项
const faultPhenomenonOptions = computed(() => {
  const faultType = currentEditScene.value.故障类型;
  const category = currentEditScene.value.大类名称;
  const functionValue = currentEditScene.value.功能;
  if (!faultType || !category) return [];

  let subSceneOptions = null;
  switch (faultType) {
    case '发放类':
      subSceneOptions = cfgSubSceneOptionsMap.value;
      break;
    case '运行类':
      subSceneOptions = oprSubSceneOptionsMap.value;
      break;
    case '功能类':
      subSceneOptions = funcSubSceneOptionsMap.value;
      break;
    default:
      subSceneOptions = null;
  }

  if (!subSceneOptions) return [];

  const key = functionValue === '' ? category : `${category}[${functionValue}]`;
  const faultPhenomenons = subSceneOptions[key]?.['故障现象'] || [];
  return faultPhenomenons.map(faultPhenomenon => ({
    label: faultPhenomenon,
    value: faultPhenomenon
  }));
});
/* Ended by AICoder, pid:z161bsd62a244c2143ef092de1261f2a70a71eca */


/* Started by AICoder, pid:46ea8354ff6789f14c700b2330547f27b7e8cda6 */
// 验证规则
const editRules = computed(() => ({
  领域: [{ required: true, message: '请选择领域' }],
  团队: [{ required: true, message: '请选择团队' }],
  防火墙: [{ required: true, message: '请输入防火墙' }],
  支持分析场景: [{ required: true, message: '请选择支持分析场景' }],
  故障类型: [{ required: true, message: '请选择故障类型' }],
  大类名称: [{ required: true, message: '请选择大类名称' }],
  故障现象: [{ required: true, message: '请输入故障现象' }],
  故障描述: [{ required: true, message: '请输入故障描述' }],
  来源: [{ required: true, message: '请选择来源' }],
  层次: [{ required: true, message: '请选择层次' }],
  功能: [{ required: true, message: '请选择功能' }],
  板卡类型: [{ required: true, message: '请选择板卡类型' }],
  框架组件: [{ required: true, message: '请选择框架组件' }],
  指令名称: [{ required: true, message: '请选择指令名称' }],
  功能名称: [{ required: true, message: '请选择功能名称' }],
  业务类型: [{ required: true, message: '请选择业务类型' }],
  业务层次: [{ required: true, message: '请选择业务层次' }],
  模块类型: [{ required: true, message: '请选择模块类型' }],
  监控功能: [{ required: true, message: '请选择监控功能' }],
  同步功能: [{ required: true, message: '请选择同步功能' }],
  告警框架: [{ required: true, message: '请选择告警框架' }],
  APO功能: [{ required: true, message: '请选择APO功能' }],
  P端口类型: [{ required: true, message: '请选择P端口类型' }],
  OAM类型: [{ required: true, message: '请选择OAM类型' }],
  OPM功能: [{ required: true, message: '请选择OPM功能' }],
  OTDR功能: [{ required: true, message: '请选择OTDR功能' }],
  APR功能: [{ required: true, message: '请选择APR功能' }],
  EDFA功能: [{ required: true, message: '请选择EDFA功能' }]
}));
/* Ended by AICoder, pid:46ea8354ff6789f14c700b2330547f27b7e8cda6 */

const editRowRules = computed(() => ({
  领域: [{ required: true, message: '请选择领域' }],
  团队: [{ required: true, message: '请选择团队' }],
  防火墙: [{ required: true, message: '请输入防火墙' }],
  支持分析场景: [{ required: true, message: '请选择支持分析场景' }],
  场景: [{ required: true, message: '请输入场景' }],
  子场景: [{ required: true, message: '请输入子场景' }],
  场景描述: [{ required: true, message: '请输入场景描述' }],
  用户引导: [{ required: true, message: '请输入用户引导' }]
}));

// 用户验证
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

// 状态弹窗相关
const statusDiagVisible = ref(false);
const statusData = ref([]);

// 状态弹窗表格列定义
const statusDialogColumns = [
  { colKey: '子场景', title: '子场景', width: 100 },
  { colKey: '团队', title: '团队', width: 100 },
  { colKey: '更新人', title: '更新人', width: 100 },
  { colKey: '更新时间', title: '更新时间', width: 200 },
  {
    colKey: '状态',
    title: '状态',
    width: 100,
    cell: (h, { row }) => {
      const supportStatus = row.状态;
      if (supportStatus.includes('成功')) {
        return <t-tag theme="success">{supportStatus}</t-tag>;
      } else if (supportStatus === '发布中') {
        return <t-tag theme="warning">{supportStatus}</t-tag>;
      } else {
        return <t-tag theme="danger">{supportStatus}</t-tag>;
      }
    },
  },
  { colKey: '详细信息', title: '详细信息', width: 100 },
];

const onStatusRead = async () => {
  console.log('开始读取更新状态数据...');

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
      response = await fetch(`${INTELDIGA_API_URL}/api/getScenarioUpdates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: currentEditRow.value.id
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

    if (!response.ok) {
      const errorMsg = `HTTP错误! 状态码: ${response.status}`;
      console.error(errorMsg);
      MessagePlugin.error(ERROR_MESSAGES.SERVER_ERROR);
      throw new Error(errorMsg);
    }

    let responseData;
    try {
      responseData = await response.json();
      console.log(responseData);

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

    console.log('场景数据读取成功，服务器消息');

    let updateData = responseData.updateData || [];

    if (typeof updateData === 'string') {
      try {
        updateData = JSON.parse(updateData);
      } catch (error) {
        console.error('解析场景数据JSON失败:', error);
        MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
        throw new Error(ERROR_MESSAGES.INVALID_JSON);
      }
    }

    if (!Array.isArray(updateData)) {
      console.error('场景数据格式不正确:', updateData);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
      throw new Error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
    }

    statusData.value = updateData.map((item, index) => {
      return {
        子场景: item.subscene || '',
        团队: item.team || '',
        更新人: item.account || '',
        更新时间: item.updatetime || '',
        状态: item.status || '',
        详细信息: item.message || '',
      };
    });
    console.log(statusData);
    MessagePlugin.success(responseData.message || '场景数据加载成功');
    console.log('场景数据处理完成，共加载', statusData.value.length, '条记录');
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

const openStatusDialog = (row) => {
  // 构建状态数据
  currentEditRow.value = { ...row };
  onStatusRead();
  statusDiagVisible.value = true;
};

const columns = [
  {
    colKey: '场景',
    title: '场景',
    width: 80,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '子场景',
    title: '子场景',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '团队',
    title: '团队',
    width: 80,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '防火墙',
    title: '防火墙',
    width: 80,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '支持分析场景',
    title: '支持分析场景',
    width: 80,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '页面链接',
    title: '页面链接',
    width: 200,
    ellipsis: true,
    cell: (h, { row }) => {
      const url = row.页面链接;
      if (url) {
        return <t-link theme="primary" hover="color" onClick={(e) => {
          e.stopPropagation();
          window.open(url, '_blank');
        }}>{url}</t-link>;
      }
      return url;
    },
  },
  {
    colKey: '上线状态',
    title: '上线状态',
    width: 80,
    ellipsis: true,
    cell: (h, { row }) => {
      // 根据上线状态类型显示不同样式的标签
      const status = row.上线状态;
      if (status === '已上线') {
        return <t-tag theme="success" onClick={() => openStatusDialog(row)} style={{ cursor: 'pointer' }}>{status}</t-tag>;
      } else if (status === '上线中') {
        return <t-tag theme="warning" onClick={() => openStatusDialog(row)} style={{ cursor: 'pointer' }}>{status}</t-tag>;
      } else{
        return <t-tag theme="danger" onClick={() => openStatusDialog(row)} style={{ cursor: 'pointer' }}>{status}</t-tag>;
      }
    },
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '场景描述',
    title: '场景描述',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '用户引导',
    title: '用户引导',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'edit',
    title: '操作',
    width: 100,
    fixed: 'right',
    ellipsis: true,
    cell: (h, { row }) => {
      return (
        <div class="table-operations">
          <t-link theme="primary" hover="color" data-id={row.id} onClick={() => releaseScene(row)}>
            发布
          </t-link>
          <t-link theme="primary" hover="color" data-id={row.id} onClick={() => openEditModal(row)}>
            编辑
          </t-link>
          <t-popconfirm theme="danger" content="确定要删除这个场景吗？" onConfirm={() => onDeleteRow(row)}>
            <t-link theme="danger" hover="color">
              删除
            </t-link>
          </t-popconfirm>
        </div>
      );
    },
  },
];

function openEditModal(row) {
  console.log('打开编辑窗口，当前行数据：', row);
  currentEditRow.value = { ...row };
  currentEditRow.value.领域 = field.value;
  diagEditVisible.value = true;
}

// 新建按钮点击事件
const onTableCreate = () => {
  const newRow = {
    id: '', // 新建时id为空，保存时由后端生成
    领域: field.value,
    团队: '',
    防火墙: '',
    支持分析场景: '',
    故障类型: '',
    大类名称: '',
    来源: '',
    层次: '',
    功能: '',
    板卡类型: '',
    框架组件: '',
    指令名称: '',
    功能名称: '',
    业务类型: '',
    业务层次: '',
    模块类型: '',
    监控功能: '',
    同步功能: '',
    告警框架: '',
    APO功能: '',
    P端口类型: '',
    OAM类型: '',
    OPM功能: '',
    OTDR功能: '',
    APR功能: '',
    EDFA功能: '',
    故障现象: '',
    故障描述: '',
  };

  // 设置当前编辑行为新行数据
  currentEditScene.value = newRow;
  diagVisible.value = true;
};

// 提交新建表单
const onSubmitCreate = async () => {
  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    const validateResult = await editFormRef.value.validate();
    if (validateResult === true) {
      // 表单验证通过，执行保存操作
      console.log('表单验证通过，提交数据：', currentEditScene.value);

      // 准备发送给后端的数据
      const requestData = {
        sceneInfo: currentEditScene.value,
        account: user.userInfo.name,
        token: user.uacToken,
      };

      // 设置加载状态
      loading.value = true;

      // 调用后端API保存数据
      const response = await fetch(`${INTELDIGA_API_URL}/api/createScenarios`, {
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

      // 新建记录，添加到表格数据中
      const newRowData = {
        id: responseData.sceneData.id,
        场景: responseData.sceneData.mainScene,
        子场景: responseData.sceneData.subScene,
        团队: currentEditScene.value.团队,
        用户引导: '',
        场景描述: responseData.sceneData.description,
        支持分析场景: currentEditScene.value.支持分析场景,
        上线状态: responseData.sceneData.status,
        页面链接: responseData.sceneData.url,
      };
      data.value.push(newRowData);
      MessagePlugin.success(responseData.message || '新建成功');
     
      diagVisible.value = false;
      return true;
    }
    return false;
  } catch (error) {
    console.error('保存失败:', error);
    MessagePlugin.error(error.message || '保存失败');
    return false;
  } finally{
    loading.value = false;
  }
};

// 提交编辑表单
const onSubmitEdit = async () => {
  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    const validateResult = await editFormRef.value.validate();
    
    if (validateResult === true) {
      // 表单验证通过，执行保存操作
      console.log('表单验证通过，提交数据：', currentEditRow.value);

      // 准备发送给后端的数据
      const requestData = {
        sceneInfo: currentEditRow.value,
        account: user.userInfo.name,
        token: user.uacToken,
      };

      // 设置加载状态
      loading.value = true;

      // 调用后端API保存数据
      const response = await fetch(`${INTELDIGA_API_URL}/api/updateScenarios`, {
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

      // 编辑记录，更新表格数据
      const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
      if (index !== -1) {
        data.value[index] = {
          id: currentEditRow.value.id,
          场景: currentEditRow.value.场景,
          子场景: currentEditRow.value.子场景,
          团队: currentEditRow.value.团队,
          用户引导: currentEditRow.value.用户引导,
          场景描述: currentEditRow.value.场景描述,
          支持分析场景: currentEditRow.value.支持分析场景,
          页面链接: currentEditRow.value.页面链接,
          上线状态: currentEditRow.value.上线状态,
        };
      }
      MessagePlugin.success(responseData.message || '保存成功');

      diagEditVisible.value = false;
      return true;
    }
    return false;
  } catch (error) {
    console.error('保存失败:', error);
    MessagePlugin.error(error.message || '保存失败');
    return false;
  } finally{
    loading.value = false;
  }
};

// 关闭编辑对话框
const onCloseEdit = () => {
  editFormRef.value.reset();
  diagVisible.value = false;
  diagEditVisible.value = false;
};

const data = ref();
const tableRef = ref();
const editableRowKeys = ref([]);
const editMap = {};
const field = ref('L2');
const tableContentWidth = ref('2500px');
const fieldOptions = [
  { label: 'L0领域', value: 'L0' },
  { label: 'L1领域', value: 'L1' },
  { label: 'L2领域', value: 'L2' },
  { label: '支撑领域', value: '支撑' },
  { label: '智控领域', value: '智控' },
];

// 删除行数据
const onDeleteRow = async (row) => {
  try {
    currentEditRow.value = { ...row };
    const response = await fetch(`${INTELDIGA_API_URL}/api/deleteScenarios`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: currentEditRow.value.id
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '删除场景数据失败');
    }

    // 从表格数据中移除该行
    const index = data.value.findIndex((item) => item.id === row.id);
    if (index !== -1) {
      data.value.splice(index, 1);
    }

    MessagePlugin.success(responseData.message || '删除成功');
  } catch (error) {
    console.error('删除失败:', error);
    MessagePlugin.error(error.message || '删除失败');
  }
};

// 发布场景
const releaseScene = async (row) => {
  try {
    const isValid = await verifyToken();
    if (!isValid) {
      router.push('/login');
    }

    currentEditRow.value = { ...row };
    // 准备发送给后端的数据
    const requestData = {
      scenario_id: currentEditRow.value.id,
      field: field.value,
      main_scene: currentEditRow.value.场景,
      sub_scene: currentEditRow.value.子场景,
      team: currentEditRow.value.团队,
      support_scenario: currentEditRow.value.支持分析场景,
      url: currentEditRow.value.页面链接,
      status: currentEditRow.value.上线状态,
      description: currentEditRow.value.场景描述,
      account: user.userInfo.name,
      token: user.uacToken,
    };

    // 编辑记录，更新表格数据
    const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
    if (index !== -1) {
      data.value[index] = {
        id: currentEditRow.value.id,
        场景: currentEditRow.value.场景,
        子场景: currentEditRow.value.子场景,
        团队: currentEditRow.value.团队,
        支持分析场景: currentEditRow.value.支持分析场景,
        页面链接: currentEditRow.value.页面链接,
        场景描述: currentEditRow.value.场景描述,
        上线状态: "上线中",
      };
    }

    // 调用后端API保存数据
    const response = await fetch(`${INTELDIGA_API_URL}/api/releaseScenario`, {
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
      throw new Error(responseData.message || '发布场景失败');
    }
    if (index !== -1) {
      data.value[index] = {
        id: currentEditRow.value.id,
        场景: currentEditRow.value.场景,
        子场景: currentEditRow.value.子场景,
        团队: currentEditRow.value.团队,
        支持分析场景: currentEditRow.value.支持分析场景,
        页面链接: currentEditRow.value.页面链接,
        场景描述: currentEditRow.value.场景描述,
        上线状态: "已上线",
      };
    }
    MessagePlugin.success(responseData.message || '发布成功');
    return true;
  } catch (error) {
    console.error('保存失败:', error);
    const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
    if (index !== -1) {
      data.value[index] = {
        id: currentEditRow.value.id,
        场景: currentEditRow.value.场景,
        子场景: currentEditRow.value.子场景,
        团队: currentEditRow.value.团队,
        支持分析场景: currentEditRow.value.支持分析场景,
        页面链接: currentEditRow.value.页面链接,
        场景描述: currentEditRow.value.场景描述,
        上线状态: "上线失败",
      };
    }
    MessagePlugin.error(error.message || '发布失败');
    return false;
  }
};

const onRowEdit = (params) => {
  const { row, col, value } = params;
  const oldRowData = editMap[row.id]?.editedRow || row;
  const editedRow = { ...oldRowData, [col.colKey]: value };
  editMap[row.id] = {
    ...params,
    editedRow,
  };
};

const onTableRead = async () => {
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
        body: JSON.stringify({ field: field.value || '' }),
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
      console.log('服务器响应', responseData);
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

    data.value = sceneData.map((item, index) => {
      return {
        id: item.id,
        场景: item.mainscene || '',
        子场景: item.subscene || '',
        团队: item.team || '',
        防火墙: item.PersonInCharge || '',
        场景描述: item.Description || '',
        用户引导: item.UserGuidance || '',
        支持分析场景: item.supportscenario || '',
        页面链接: item.url || '',
        上线状态: item.status || '',
      };
    });

    MessagePlugin.success(responseData.message || '场景数据加载成功');
    console.log('场景数据处理完成，共加载', data.value.length, '条记录');
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

/* Started by AICoder, pid:v4f7bt7fcamcfa91488808c8f00e38738c3636dd */
const onSceneMapRead = async () => {
  console.log('开始读取场景Map...');

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
      response = await fetch(`${INTELDIGA_API_URL}/api/getSceneMap`, {
        method: 'GET',
        headers: {'Content-Type': 'application/json' },
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
      console.log('服务器响应', responseData);
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

    // 将获取的场景map数据赋值给响应式变量
    mainSceneOptionsMap.value = responseData.info.main_scene_options_map;
    cfgSubSceneOptionsMap.value = responseData.info.cfg_sub_scene_options_map;
    oprSubSceneOptionsMap.value = responseData.info.opr_sub_scene_options_map;
    funcSubSceneOptionsMap.value = responseData.info.func_sub_scene_options_map;

    for (const [key, values] of Object.entries(responseData.info.field_team_options_map)) {
      teamTypeOptionsMap[key] = values.map(value => ({
        label: value,
        value: value
      }));
    }

    console.log('场景Map处理完成');
  } catch (error) {
    console.error('场景Map读取过程中出错:', error);
    if (!Object.values(ERROR_MESSAGES).includes(error.message)) {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};

/* Ended by AICoder, pid:v4f7bt7fcamcfa91488808c8f00e38738c3636dd */

// 过滤后的表格数据
const filteredTableData = computed(() => {
  if (!data.value || !searchText.value) {
    return data.value || [];
  }

  const search = String(searchText.value).toLowerCase();
  return data.value.filter(
    (row) =>
      (row.场景 && row.场景.toLowerCase().includes(search)) ||
      (row.子场景 && row.子场景.toLowerCase().includes(search)) ||
      (row.团队 && row.团队.toLowerCase().includes(search)) ||
      (row.支持分析场景 && row.支持分析场景.toLowerCase().includes(search)) ||
      (row.上线状态 && row.上线状态.toLowerCase().includes(search)),
  );
});

// 搜索处理函数
const onSearch = () => {
  // 搜索会在 computed 属性中自动处理
  console.log('搜索内容:', String(searchText.value));
};

onMounted(async () => {
  const isValid = await verifyToken();
  if (!isValid) {
    router.push('/login');
  }
  onSceneMapRead();
  onTableRead();
});

const jumpToChatPage = () => {
  router.push('/ai/diag'); // 根据实际路由路径调整
};

</script>

<style>
.table-operations .t-link {
  margin-right: 8px;
}

.board-main {
  padding-top: 50px;

  width: 100%;
  table {
    border-collapse: collapse;
  }

  th {
    background-color: #e7e7e7;
    color: #333;
    white-space: nowrap;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    border-left: none;               /* 左侧无边框 */
    border-right: 1px solid #d0d0d0; /* 列之间有分隔线 */
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

  .back-to-chat {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 70px; /* 距离页面顶部的距离为0 */
    left: 250px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      0px 16px 32px rgba(0, 0, 0, 0.2),
      0px 32px 48px rgba(0, 0, 0, 0.15);
  }
}

/* 编辑表单样式 */
.edit-form .t-form__item {
  margin-bottom: 20px;
}
</style>


