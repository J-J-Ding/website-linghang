<template>
  <div class="board-main">
    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button shape="circle" variant="base" theme="primary" @click="onTableAiChat"> AI </t-button>
        <t-select v-model="field" :options="fieldOptions" placeholder="请选择领域" clearable> </t-select>
        <t-button @click="onTableRead">读取</t-button>
        <t-button @click="onTableCreate">新建</t-button>
      </t-space>

      <t-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="filteredData"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="650"
        table-layout="fixed"
        :table-content-width="tableContentWidth"
        style="width: 100%"
        :filter-value="filterValue"
        :loading="tableLoading"
        @row-edit="onRowEdit"
        @filter-change="onFilterChange"
      />
    </t-space>

    <!-- 编辑对话框 -->
    <t-dialog
      v-model:visible="diagVisible"
      :header="`编辑单板 - ${currentEditRow ? currentEditRow.单板名称 : ''}`"
      :on-confirm="onSubmitEdit"
      :on-close="onCloseEdit"
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
            :rules="editRules"
            :label-width="120"
            :status-icon="false"
          >
            <!-- 每个 t-form-item 占据一整行 -->
            <t-form-item label="单板编号" name="单板编号">
              <t-input v-model="currentEditRow.单板编号" placeholder="请输入单板编号" />
            </t-form-item>

            <t-form-item label="单板名称" name="单板名称">
              <t-input v-model="currentEditRow.单板名称" :disabled="!isCreateMode" placeholder="请输入单板名称" />
            </t-form-item>

            <t-form-item label="单板类型" name="单板类型">
              <t-input v-model="currentEditRow.单板类型" placeholder="请输入单板类型" />
            </t-form-item>

            <t-form-item label="领域" name="领域">
              <t-input v-model="currentEditRow.领域" placeholder="请输入领域" />
            </t-form-item>

            <t-form-item label="产品" name="产品">
              <t-input v-model="currentEditRow.产品" placeholder="请输入产品" />
            </t-form-item>

            <t-form-item label="子架" name="子架">
              <t-input v-model="currentEditRow.子架" placeholder="请输入子架" />
            </t-form-item>

            <t-form-item label="主控" name="主控">
              <t-input v-model="currentEditRow.主控" placeholder="请输入主控" />
            </t-form-item>

            <t-form-item label="Board ID" name="boardid">
              <t-input v-model="currentEditRow.boardid" placeholder="请输入Board ID" />
            </t-form-item>

            <t-form-item label="Function ID" name="functionid">
              <t-input v-model="currentEditRow.functionid" placeholder="请输入Function ID" />
            </t-form-item>

            <t-form-item label="子卡" name="子卡">
              <t-input v-model="currentEditRow.子卡" placeholder="请输入子卡" />
            </t-form-item>

            <t-form-item label="交换芯片" name="交换芯片">
              <t-input v-model="currentEditRow.交换芯片" placeholder="请输入交换芯片" />
            </t-form-item>

            <t-form-item label="面板端口" name="面板端口">
              <t-input v-model="currentEditRow.面板端口" placeholder="请输入面板端口" />
            </t-form-item>

            <t-form-item label="转发能力" name="转发能力">
              <t-input v-model="currentEditRow.转发能力" placeholder="请输入转发能力" />
            </t-form-item>

            <t-form-item label="软件平台" name="软件平台">
              <t-input v-model="currentEditRow.软件平台" placeholder="请输入软件平台" />
            </t-form-item>

            <t-form-item label="交叉方式" name="交叉方式">
              <t-input v-model="currentEditRow.交叉方式" placeholder="请输入交叉方式" />
            </t-form-item>

            <t-form-item label="PHY芯片" name="PHY芯片">
              <t-input v-model="currentEditRow.PHY芯片" placeholder="请输入PHY芯片" />
            </t-form-item>

            <t-form-item label="时钟芯片" name="时钟芯片">
              <t-input v-model="currentEditRow.时钟芯片" placeholder="请输入时钟芯片" />
            </t-form-item>

            <t-form-item label="内存" name="内存">
              <t-input v-model="currentEditRow.内存" placeholder="请输入内存" />
            </t-form-item>

            <t-form-item label="SDSSD" name="SDSSD">
              <t-input v-model="currentEditRow.SDSSD" placeholder="请输入SDSSD" />
            </t-form-item>

            <t-form-item label="FPGA" name="FPGA">
              <t-input v-model="currentEditRow.FPGA" placeholder="请输入FPGA" />
            </t-form-item>

            <t-form-item label="CPLD" name="CPLD">
              <t-input v-model="currentEditRow.CPLD" placeholder="请输入CPLD" />
            </t-form-item>

            <t-form-item label="FLASH" name="FLASH">
              <t-input v-model="currentEditRow.FLASH" placeholder="请输入FLASH" />
            </t-form-item>

            <t-form-item label="子架EEPROM" name="子架EEPROM">
              <t-input v-model="currentEditRow.子架EEPROM" placeholder="请输入子架EEPROM" />
            </t-form-item>

            <t-form-item label="母板EEPROM" name="母板EEPROM">
              <t-input v-model="currentEditRow.母板EEPROM" placeholder="请输入母板EEPROM" />
            </t-form-item>
          </t-form>
        </div>
      </div>
    </t-dialog>

    <!-- 特性列表弹窗 -->
    <t-dialog
      v-model:visible="featuresDiagVisible"
      header="支持的特性列表"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <div v-if="dialogFeaturesData && dialogFeaturesData.length > 0" class="features-details">
        <t-table
          :data="dialogFeaturesData"
          :columns="featuresDialogColumns"
          row-key="feature_id"
          bordered
          size="small"
          :maxHeight="400"
        />
      </div>
      <t-alert v-else theme="warning" message="未找到该单板的特性信息" />
    </t-dialog>

    <!-- 模块列表弹窗 -->
    <t-dialog
      v-model:visible="modulesDiagVisible"
      :header="modulesDialogTitle"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-loading :loading="modulesLoading">
        <div v-if="dialogModulesData && dialogModulesData.length > 0" class="modules-details">
          <t-table
            :data="dialogModulesData"
            :columns="modulesDialogColumns"
            row-key="PN"
            bordered
            size="small"
            :maxHeight="400"
          />
        </div>
        <t-alert v-else theme="warning" message="未找到该单板的模块信息" />
      </t-loading>
    </t-dialog>

    <!-- SDSSD器件属性弹窗 -->
    <t-dialog
      v-model:visible="sdssdDiagVisible"
      :header="`SDSSD器件属性 - ${currentSDSSD}`"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-loading :loading="sdssdLoading">
        <div v-if="sdssdData && sdssdData.length > 0" class="sdssd-details">
          <t-table
            :data="sdssdData"
            :columns="sdssdDetailColumns"
            row-key="代码"
            bordered
            size="small"
            :maxHeight="400"
          />
        </div>
        <t-alert v-else theme="warning" message="未找到该SDSSD器件的属性信息" />
      </t-loading>
    </t-dialog>

    <!-- PHY芯片属性弹窗 -->
    <t-dialog
      v-model:visible="phyDiagVisible"
      :header="`PHY芯片属性 - ${currentPHY}`"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-loading :loading="phyLoading">
        <div v-if="phyData && phyData.length > 0" class="phy-details">
          <t-table
            :data="phyData"
            :columns="phyDetailColumns"
            row-key="PHY型号"
            bordered
            size="small"
            :maxHeight="400"
          />
        </div>
        <t-alert v-else theme="warning" message="未找到该PHY芯片的属性信息" />
      </t-loading>
    </t-dialog>

    <!-- 交换芯片属性弹窗 -->
    <t-dialog
      v-model:visible="switchDiagVisible"
      :header="`交换芯片属性 - ${currentSwitch}`"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-loading :loading="switchLoading">
        <div v-if="switchData && switchData.length > 0" class="switch-details">
          <t-table
            :data="switchData"
            :columns="switchDetailColumns"
            row-key="型号"
            bordered
            size="small"
            :maxHeight="400"
          />
        </div>
        <t-alert v-else theme="warning" message="未找到该交换芯片的属性信息" />
      </t-loading>
    </t-dialog>

    <!-- 时钟芯片属性弹窗 -->
    <t-dialog
      v-model:visible="clockDiagVisible"
      :header="`时钟芯片属性 - ${currentClock}`"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-loading :loading="clockLoading">
        <div v-if="clockData && clockData.length > 0" class="clock-details">
          <t-table
            :data="clockData"
            :columns="clockDetailColumns"
            row-key="型号"
            bordered
            size="small"
            :maxHeight="400"
          />
        </div>
        <t-alert v-else theme="warning" message="未找到该时钟芯片的属性信息" />
      </t-loading>
    </t-dialog>

    <!-- CPU数据弹窗 -->
    <t-dialog v-model:visible="cpuDiagVisible" header="CPU数据" :footer="false" width="80%" destroy-on-close>
      <div v-if="currentCPUData && currentCPUData.length > 0" class="cpu-details">
        <t-table
          :data="currentCPUData"
          :columns="cpuDetailColumns"
          row-key="子卡型号"
          bordered
          size="small"
          :maxHeight="400"
        />
      </div>
      <t-alert v-else theme="warning" message="未找到该单板的CPU数据" />
    </t-dialog>

    <!-- 全局AI实例 - 原有的AI组件 -->
    <AiChat
      :visible="tableAiVisible"
      :ai-chat-title="tableAiTitle"
      :ai-chat-context="tableAiContext"
      @update:visible="tableAiVisible = $event"
    />

    <!-- 新的行级AI实例 - 响应表格行的AI助手按钮 -->
    <AiChat
      :visible="rowAiVisible"
      :ai-chat-title="rowAiTitle"
      :ai-chat-context="rowAiContext"
      @update:visible="rowAiVisible = $event"
    />
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, onMounted, reactive, computed } from 'vue';
import { Input, Select, MessagePlugin, Tag, Descriptions, DescriptionsItem, Loading, Alert } from 'tdesign-vue-next';
import { useUserStore } from '@/store';

import AiChat from '@/pages/ai/chat/chat.vue';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const user = useUserStore();

// 全局AI相关变量
const tableAiVisible = ref(false);
const tableAiTitle = ref('全局');
const tableAiContext = ref('');

// 行级AI相关变量（新的AI实例）
const rowAiVisible = ref(false);
const rowAiTitle = ref('单板');
const rowAiContext = ref('');

// 打开全局AI
const onTableAiChat = () => {
  tableAiVisible.value = true;
};

// 打开行级AI并传递当前行数据
const onRowAiChat = (rowData) => {
  // 直接使用包含SDSSD、PHY和交换芯片数据的行数据
  const rowDataWithComponents = {
    ...rowData,
    // 确保包含所有组件的详细数据
    SDSSD数据: rowData.SDSSD数据 || [],
    PHY数据: rowData.PHY数据 || [],
    交换芯片数据: rowData.交换芯片数据 || [],
    时钟芯片数据: rowData.时钟芯片数据 || [],
    CPU数据: rowData.CPU数据 || [],
    支持模块: rowData.支持模块 || [],
  };

  // 将当前行数据（包含所有组件详情）转换为JSON格式作为上下文
  rowAiTitle.value = rowData.单板名称 + '单板';
  rowAiContext.value = JSON.stringify(rowDataWithComponents, null, 2);
  rowAiVisible.value = true;
};

const diagVisible = ref(false);
const currentEditRow = ref(null);
const editFormRef = ref(null);
const isCreateMode = ref(false); // 标识是否是新建模式

// 表单验证规则
const editRules = {
  单板编号: [{ required: true, message: '请输入单板编号', type: 'error' }],
  单板名称: [
    {
      required: true,
      message: '请输入单板名称',
      type: 'error',
      validator: (val) => (isCreateMode.value ? !!val : true),
    },
  ],
  单板类型: [{ required: true, message: '请输入单板类型', type: 'error' }],
  领域: [{ required: true, message: '请输入领域', type: 'error' }],
  产品: [{ required: true, message: '请输入产品', type: 'error' }],
};

// 特性弹窗相关
const featuresDiagVisible = ref(false);
const dialogFeaturesData = ref([]);

// 模块弹窗相关
const modulesDiagVisible = ref(false);
const dialogModulesData = ref([]);
const modulesLoading = ref(false);

const modulesDialogTitle = computed(() => {
  return `支持的模块列表 - 共 ${dialogModulesData.value.length} 个`;
});

// SDSSD弹窗相关
const sdssdDiagVisible = ref(false);
const currentSDSSD = ref('');
const sdssdData = ref([]);
const sdssdLoading = ref(false);

// PHY芯片弹窗相关
const phyDiagVisible = ref(false);
const currentPHY = ref('');
const phyData = ref([]);
const phyLoading = ref(false);

// 交换芯片弹窗相关
const switchDiagVisible = ref(false);
const currentSwitch = ref('');
const switchData = ref([]);
const switchLoading = ref(false);

// 时钟芯片弹窗相关
const clockDiagVisible = ref(false);
const currentClock = ref('');
const clockData = ref([]);
const clockLoading = ref(false);

// CPU数据弹窗相关
const cpuDiagVisible = ref(false);
const currentCPUData = ref([]);

// SDSSD详情列定义（用于表格显示多个条目）
const sdssdDetailColumns = [
  { colKey: 'SD类型', title: 'SD类型', width: 120, ellipsis: true },
  { colKey: '厂家', title: '厂家', width: 120, ellipsis: true },
  { colKey: '容量', title: '容量', width: 100, ellipsis: true },
  { colKey: '材质', title: '材质', width: 100, ellipsis: true },
  { colKey: '接口类型', title: '接口类型', width: 120, ellipsis: true },
  { colKey: '代码', title: '代码', width: 120, ellipsis: true },
  { colKey: '支持主控', title: '支持主控', width: 120, ellipsis: true },
  { colKey: '总写入次数', title: '总写入次数', width: 120, ellipsis: true },
  { colKey: '单block大小', title: '单block大小', width: 120, ellipsis: true },
  { colKey: '理论TBW', title: '理论TBW', width: 120, ellipsis: true },
  { colKey: '每日写入上限', title: '每日写入上限', width: 140, ellipsis: true },
];

// PHY芯片详情列定义（用于表格显示多个条目）
const phyDetailColumns = [
  { colKey: 'PHY型号', title: 'PHY型号', width: 150, ellipsis: true },
  { colKey: '厂家', title: '厂家', width: 120, ellipsis: true },
  { colKey: '端口配置', title: '端口配置', width: 120, ellipsis: true },
  { colKey: '端口类型', title: '端口类型', width: 120, ellipsis: true },
  { colKey: '封装类型', title: '封装类型', width: 120, ellipsis: true },
  { colKey: '速率支持', title: '速率支持', width: 120, ellipsis: true },
  { colKey: '典型特性', title: '典型特性', width: 150, ellipsis: true },
];

// 交换芯片详情列定义（用于表格显示多个条目）
const switchDetailColumns = [
  { colKey: '型号', title: '型号', width: 120, ellipsis: true },
  { colKey: '厂家', title: '厂家', width: 120, ellipsis: true },
  { colKey: '交换容量', title: '交换容量', width: 120, ellipsis: true },
  { colKey: '端口配置', title: '端口配置', width: 120, ellipsis: true },
  { colKey: '端口容量', title: '端口容量', width: 120, ellipsis: true },
  { colKey: '路由表容量', title: '路由表容量', width: 140, ellipsis: true },
];

// 时钟芯片详情列定义（用于表格显示多个条目）
const clockDetailColumns = [
  { colKey: '型号', title: '型号', width: 150, ellipsis: true },
  { colKey: '厂家', title: '厂家', width: 120, ellipsis: true },
];

// CPU数据详情列定义（用于表格显示多个条目）
const cpuDetailColumns = [
  { colKey: '子卡型号', title: '子卡型号', width: 120, ellipsis: true },
  { colKey: '子卡ID', title: '子卡ID', width: 100, ellipsis: true },
  { colKey: 'CPU架构', title: 'CPU架构', width: 100, ellipsis: true },
  { colKey: 'DRAM容量', title: 'DRAM容量', width: 100, ellipsis: true },
];

// 特性弹窗表格列定义
const featuresDialogColumns = [
  { colKey: 'feature_id', title: '特性编号', width: 100 },
  { colKey: 'feature_name', title: '特性名称', width: 200, ellipsis: true },
  {
    colKey: 'feature_level',
    title: '特性等级',
    width: '120',
    ellipsis: true,
    cell: (h, { row }) => {
      // 根据特性等级显示不同样式的标签
      if (row.feature_level === '一级特性') {
        return (
          <t-tag theme="primary" variant="light-outline">
            一级特性
          </t-tag>
        );
      } else if (row.feature_level === '二级特性') {
        return (
          <t-tag theme="primary" variant="light">
            二级特性
          </t-tag>
        );
      }
      // 可以添加更多等级的标签样式
      return <t-tag>{row.feature_level}</t-tag>;
    },
  },
  {
    colKey: 'feature_support',
    title: '支持情况',
    width: 100,
    cell: (h, { row }) => {
      const supportStatus = row.feature_support;
      if (supportStatus === '已支持') {
        return <t-tag theme="success">{supportStatus}</t-tag>;
      } else if (supportStatus === '不支持') {
        return <t-tag theme="danger">{supportStatus}</t-tag>;
      }
      // 处理其他未定义的状态
      return supportStatus || '';
    },
  },
];

// 模块弹窗表格列定义
const modulesDialogColumns = [
  { colKey: 'PN', title: 'PN', width: 120, ellipsis: true },
  { colKey: '模块类型', title: '模块类型', width: 100, ellipsis: true },
  { colKey: '接口类型', title: '接口类型', width: 100, ellipsis: true },
  { colKey: '速率Mbps', title: '速率(Mbps)', width: 100, ellipsis: true },
  { colKey: '距离', title: '距离', width: 80, ellipsis: true },
  { colKey: '制造厂商', title: '制造厂商', width: 120, ellipsis: true },
  { colKey: '应用代码', title: '应用代码', width: 120, ellipsis: true },
  { colKey: '波长类型', title: '波长类型', width: 100, ellipsis: true },
  { colKey: '物料代码', title: '物料代码', width: 120, ellipsis: true },
];

const openFeaturesDialog = (features) => {
  // 从参数获取特性数据
  dialogFeaturesData.value = Array.isArray(features) ? features : [];

  if (dialogFeaturesData.value.length === 0) {
    MessagePlugin.warning('未找到该单板的特性信息');
  } else {
    MessagePlugin.success(`获取到 ${dialogFeaturesData.value.length} 条特性信息`);
  }

  featuresDiagVisible.value = true;
};

const openModulesDialog = (modules) => {
  modulesLoading.value = true;
  modulesDiagVisible.value = true;

  // 模拟数据加载，实际应用中如果是异步获取数据，这里应该是异步操作
  try {
    // 从参数获取模块数据
    dialogModulesData.value = Array.isArray(modules) ? modules : [];

    if (dialogModulesData.value.length === 0) {
      MessagePlugin.warning('未找到该单板的模块信息');
    } else {
      MessagePlugin.success(`获取到 ${dialogModulesData.value.length} 条模块信息`);
    }
  } catch (error) {
    console.error('获取模块数据失败:', error);
    MessagePlugin.error(error.message || '获取模块数据失败');
    dialogModulesData.value = [];
  } finally {
    modulesLoading.value = false;
  }
};

// 打开SDSSD弹窗并获取数据
const openSDSSDDialog = async (sdssdValue) => {
  if (!sdssdValue) {
    MessagePlugin.warning('SDSSD值为空');
    return;
  }

  currentSDSSD.value = sdssdValue;
  sdssdData.value = [];
  sdssdLoading.value = true;
  sdssdDiagVisible.value = true;

  try {
    // 从当前行获取SDSSD数据
    const currentRow = data.value.find((row) => row.SDSSD === sdssdValue);
    if (currentRow && currentRow.SDSSD数据 && currentRow.SDSSD数据.length > 0) {
      sdssdData.value = currentRow.SDSSD数据;
    } else {
      // 如果当前行没有详细数据，再请求后端
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: user.userInfo.name,
          table_name: 'SD器件库',
          conditions: { SD类型: sdssdValue },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '获取SDSSD数据失败');
      }

      sdssdData.value = responseData.data || [];

      if (sdssdData.value.length === 0) {
        MessagePlugin.warning('未找到该SDSSD器件的属性信息');
      } else {
        MessagePlugin.success('SDSSD器件属性获取成功');
      }
    }
  } catch (error) {
    console.error('获取SDSSD数据失败:', error);
    MessagePlugin.error(error.message || '获取SDSSD数据失败');
    sdssdData.value = [];
  } finally {
    sdssdLoading.value = false;
  }
};

// 打开PHY芯片弹窗并获取数据
const openPHYDialog = async (phyValue) => {
  if (!phyValue) {
    MessagePlugin.warning('PHY芯片值为空');
    return;
  }

  currentPHY.value = phyValue;
  phyData.value = [];
  phyLoading.value = true;
  phyDiagVisible.value = true;

  try {
    // 从当前行获取PHY数据
    const currentRow = data.value.find((row) => row.PHY芯片 === phyValue);
    if (currentRow && currentRow.PHY数据 && currentRow.PHY数据.length > 0) {
      phyData.value = currentRow.PHY数据;
    } else {
      // 如果当前行没有详细数据，再请求后端
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: user.userInfo.name,
          table_name: 'PHY库',
          conditions: { PHY型号: phyValue },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '获取PHY芯片数据失败');
      }

      phyData.value = responseData.data || [];

      if (phyData.value.length === 0) {
        MessagePlugin.warning('未找到该PHY芯片的属性信息');
      } else {
        MessagePlugin.success('PHY芯片属性获取成功');
      }
    }
  } catch (error) {
    console.error('获取PHY芯片数据失败:', error);
    MessagePlugin.error(error.message || '获取PHY芯片数据失败');
    phyData.value = [];
  } finally {
    phyLoading.value = false;
  }
};

// 打开交换芯片弹窗并获取数据
const openSwitchDialog = async (switchValue) => {
  if (!switchValue) {
    MessagePlugin.warning('交换芯片值为空');
    return;
  }

  currentSwitch.value = switchValue;
  switchData.value = [];
  switchLoading.value = true;
  switchDiagVisible.value = true;

  try {
    // 从当前行获取交换芯片数据
    const currentRow = data.value.find((row) => row.交换芯片 === switchValue);
    if (currentRow && currentRow.交换芯片数据 && currentRow.交换芯片数据.length > 0) {
      switchData.value = currentRow.交换芯片数据;
    } else {
      // 如果当前行没有详细数据，再请求后端
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: user.userInfo.name,
          table_name: '交换芯片库',
          conditions: { 型号: switchValue },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '获取交换芯片数据失败');
      }

      switchData.value = responseData.data || [];

      if (switchData.value.length === 0) {
        MessagePlugin.warning('未找到该交换芯片的属性信息');
      } else {
        MessagePlugin.success('交换芯片属性获取成功');
      }
    }
  } catch (error) {
    console.error('获取交换芯片数据失败:', error);
    MessagePlugin.error(error.message || '获取交换芯片数据失败');
    switchData.value = [];
  } finally {
    switchLoading.value = false;
  }
};

// 打开时钟芯片弹窗并获取数据
const openClockDialog = async (clockValue) => {
  if (!clockValue) {
    MessagePlugin.warning('时钟芯片值为空');
    return;
  }

  currentClock.value = clockValue;
  clockData.value = [];
  clockLoading.value = true;
  clockDiagVisible.value = true;

  try {
    // 从当前行获取时钟芯片数据
    const currentRow = data.value.find((row) => row.时钟芯片 === clockValue);
    if (currentRow && currentRow.时钟芯片数据 && currentRow.时钟芯片数据.length > 0) {
      clockData.value = currentRow.时钟芯片数据;
    } else {
      // 如果当前行没有详细数据，再请求后端
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Table_get`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: user.userInfo.name,
          table_name: '时钟芯片库', // 请根据您的实际表名调整
          conditions: { 型号: clockValue },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '获取时钟芯片数据失败');
      }

      clockData.value = responseData.data || [];

      if (clockData.value.length === 0) {
        MessagePlugin.warning('未找到该时钟芯片的属性信息');
      } else {
        MessagePlugin.success('时钟芯片属性获取成功');
      }
    }
  } catch (error) {
    console.error('获取时钟芯片数据失败:', error);
    MessagePlugin.error(error.message || '获取时钟芯片数据失败');
    clockData.value = [];
  } finally {
    clockLoading.value = false;
  }
};

// 打开CPU数据弹窗
const openCPUDialog = (cpuData) => {
  if (!cpuData || cpuData.length === 0) {
    MessagePlugin.warning('无CPU数据');
    return;
  }

  currentCPUData.value = cpuData;
  cpuDiagVisible.value = true;
  MessagePlugin.success(`获取到 ${cpuData.length} 条CPU数据`);
};

const columns = [
  {
    colKey: '单板编号',
    title: '单板编号',
    width: 100,
    ellipsis: true,
    fixed: 'left',
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '单板名称',
    title: '单板名称',
    width: 120,
    ellipsis: true,
    fixed: 'left',
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '单板类型',
    title: '单板类型',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    filter: {
      type: 'multiple',
      resetValue: [],
      props: {
        options: [], // 动态选项将在onTableRead中填充
      },
      showConfirmAndReset: true,
    },
  },
  {
    colKey: '领域',
    title: '领域',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    filter: {
      type: 'multiple',
      resetValue: [],
      props: {
        options: [], // 动态选项将在onTableRead中填充
      },
      showConfirmAndReset: true,
    },
  },
  {
    colKey: '产品',
    title: '产品',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    filter: {
      type: 'multiple',
      resetValue: [],
      props: {
        options: [], // 动态选项将在onTableRead中填充
      },
      showConfirmAndReset: true,
    },
  },
  {
    colKey: '支持特性',
    title: '支持特性',
    width: 150,
    ellipsis: true,
    cell: (h, { row }) => {
      const features = row.支持特性 || [];
      // 筛选出状态为"已支持"的特性并计算数量
      const supportedFeatures = Array.isArray(features)
        ? features.filter((feature) => feature.feature_support === '已支持')
        : [];
      const supportedCount = supportedFeatures.length;
      const totalCount = Array.isArray(features) ? features.length : 0;

      if (totalCount === 0) {
        return '支持 0 个特性';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openFeaturesDialog(features)}>
          支持 {supportedCount} 个特性
        </t-link>
      );
    },
  },
  {
    colKey: '支持模块',
    title: '支持模块',
    width: 150,
    ellipsis: true,
    cell: (h, { row }) => {
      const modules = row.支持模块 || [];
      const moduleCount = Array.isArray(modules) ? modules.length : 0;

      if (moduleCount === 0) {
        return '支持 0 类模块';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openModulesDialog(modules)}>
          支持 {moduleCount} 类模块
        </t-link>
      );
    },
  },
  {
    colKey: '子架',
    title: '子架',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '主控',
    title: '主控',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'boardid',
    title: 'Board ID',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'functionid',
    title: 'Function ID',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '子卡',
    title: '子卡',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const subcardValue = row.子卡;
      const cpuData = row.CPU数据 || [];

      if (cpuData.length === 0) {
        return subcardValue || '无数据';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openCPUDialog(cpuData)}>
          {subcardValue}
        </t-link>
      );
    },
  },
  {
    colKey: '交换芯片',
    title: '交换芯片',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const switchValue = row.交换芯片;
      const switchData = row.交换芯片数据 || [];
      const switchCount = switchData.length;

      if (switchCount === 0) {
        return switchValue || '无数据';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openSwitchDialog(switchValue)}>
          {switchValue}
        </t-link>
      );
    },
  },
  {
    colKey: '面板端口',
    title: '面板端口',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '转发能力',
    title: '转发能力',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '软件平台',
    title: '软件平台',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '交叉方式',
    title: '交叉方式',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'PHY芯片',
    title: 'PHY芯片',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const phyValue = row.PHY芯片;
      const phyData = row.PHY数据 || [];
      const phyCount = phyData.length;

      if (phyCount === 0) {
        return phyValue || '无数据';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openPHYDialog(phyValue)}>
          {phyValue}
        </t-link>
      );
    },
  },
  {
    colKey: '时钟芯片',
    title: '时钟芯片',
    width: 120,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const clockValue = row.时钟芯片;
      const clockData = row.时钟芯片数据 || [];
      const clockCount = clockData.length;

      if (clockCount === 0) {
        return clockValue || '无数据';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openClockDialog(clockValue)}>
          {clockValue}
        </t-link>
      );
    },
  },
  {
    colKey: '内存',
    title: '内存',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'SDSSD',
    title: 'SDSSD',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const sdssdValue = row.SDSSD;
      const sdssdData = row.SDSSD数据 || [];
      const sdssdCount = sdssdData.length;

      if (sdssdCount === 0) {
        return sdssdValue || '无数据';
      }

      return (
        <t-link theme="primary" hover="color" onClick={() => openSDSSDDialog(sdssdValue)}>
          {sdssdValue}
        </t-link>
      );
    },
  },
  /* Started by AICoder, pid:s6f51wad99x82321493d0830105c81201309e47e */
  {
    colKey: 'FPGA',
    title: 'FPGA',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    cell: (h, { row }) => {
      const fpgaValue = row.FPGA || '';

      // 匹配Markdown格式的超链接
      const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/;
      const match = fpgaValue.match(linkPattern);

      if (match) {
        const [fullMatch, title, url] = match;
        return (
          <t-link theme="primary" hover="color" onClick={() => window.open(url, '_blank')}>
            {title}
          </t-link>
        );
      }

      // 默认显示原始文本
      return fpgaValue;
    },
  },
  /* Ended by AICoder, pid:s6f51wad99x82321493d0830105c81201309e47e */
  {
    colKey: 'CPLD',
    title: 'CPLD',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'FLASH',
    title: 'FLASH',
    width: 100,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '子架EEPROM',
    title: '子架EEPROM',
    width: 130,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: '母板EEPROM',
    title: '母板EEPROM',
    width: 130,
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'ai',
    title: '智能体',
    width: 80,
    fixed: 'right',
    cell: (h, { row }) => {
      return (
        <t-button
          theme="primary"
          size="small"
          disabled={row.agent !== '支持'}
          onClick={() => onRowAiChat(row)} // 点击时打开行级AI并传递当前行数据
        >
          AI助手
        </t-button>
      );
    },
  },
  {
    colKey: 'edit',
    title: '操作',
    width: 120,
    fixed: 'right',
    cell: (h, { row }) => {
      return (
        <div class="table-operations">
          <t-link theme="primary" hover="color" data-id={row.id} onClick={() => openEditModal(row)}>
            编辑
          </t-link>
          <t-popconfirm theme="danger" content="确定要删除这个单板吗？" onConfirm={() => onDeleteRow(row)}>
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
  isCreateMode.value = false; // 编辑模式
  diagVisible.value = true;
}

// 新建按钮点击事件
const onTableCreate = () => {
  // 创建一个空的新行数据对象
  const newRow = {
    id: '', // 新建时id为空，保存时由后端生成
    单板编号: '',
    单板名称: '',
    单板类型: '',
    领域: '',
    产品: '',
    子架: '',
    主控: '',
    boardid: '',
    functionid: '',
    子卡: '',
    交换芯片: '',
    面板端口: '',
    转发能力: '',
    软件平台: '',
    交叉方式: '',
    PHY芯片: '',
    时钟芯片: '',
    内存: '',
    SDSSD: '',
    FPGA: '',
    CPLD: '',
    FLASH: '',
    子架EEPROM: '',
    母板EEPROM: '',
    支持特性: [],
    支持模块: [],
    agent: '支持',
  };

  // 设置当前编辑行为新行数据
  currentEditRow.value = newRow;
  isCreateMode.value = true; // 新建模式
  diagVisible.value = true;
};

/* Started by AICoder, pid:s0538h3f69lb28714e690a7790289d507ac71d7e */
// 工具函数：检查是否为指定格式的链接
const isWikiLink = (url) => {
  // 支持相对路径和绝对路径
  const pattern = /\/space\/[a-zA-Z0-9]{32}\/wiki\/page\/[a-zA-Z0-9]{32}\/view/;
  return pattern.test(url);
};

// 提取参数并生成Markdown链接
const processWikiLink = async (originalUrl) => {
  // 提取参数
  const match = originalUrl.match(/\/space\/([a-zA-Z0-9]{32})\/wiki\/page\/([a-zA-Z0-9]{32})\/view/);
  if (!match) return originalUrl;

  const [urlId, spaceId, pageId] = match;
  const fullUrl = `https://i.zte.com.cn/index/ispace/#${urlId}`;

  try {
    const response = await fetch(
      `https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/${pageId}?spaceId=${spaceId}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', 'X-Emp-No': user.userInfo.name, 'X-Auth-Value': user.uacToken },
      },
    );

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const data = await response.json();
    const title = data.bo?.title || '未找到标题';
    return `[${title}](${fullUrl})`;
  } catch (error) {
    console.error('获取页面标题失败:', error);
    return originalUrl;
  }
};

// 主处理函数
const prepareFPGAData = async () => {
  const currentFPGA = currentEditRow.value.FPGA;

  // 如果FPGA字段是空值或非链接格式，直接返回原始数据
  if (!currentFPGA || !isWikiLink(currentFPGA)) {
    return currentFPGA;
  }

  try {
    return await processWikiLink(currentFPGA);
  } catch (error) {
    console.warn('跳过FPGA字段更新:', error);
    return currentFPGA;
  }
};
/* Ended by AICoder, pid:s0538h3f69lb28714e690a7790289d507ac71d7e */

// 提交编辑表单
const onSubmitEdit = async () => {
  try {
    const validateResult = await editFormRef.value.validate();
    if (validateResult === true) {
      // 表单验证通过，执行保存操作
      console.log('表单验证通过，提交数据：', currentEditRow.value);

      const FPGA = await prepareFPGAData();

      // 准备发送给后端的数据
      const requestData = {
        board_id: currentEditRow.value.单板编号,
        board_name: currentEditRow.value.单板名称,
        单板类型: currentEditRow.value.单板类型,
        领域: currentEditRow.value.领域,
        产品: currentEditRow.value.产品,
        子架: currentEditRow.value.子架,
        主控: currentEditRow.value.主控,
        boardid: currentEditRow.value.boardid,
        functionid: currentEditRow.value.functionid,
        子卡: currentEditRow.value.子卡,
        交换芯片: currentEditRow.value.交换芯片,
        面板端口: currentEditRow.value.面板端口,
        转发能力: currentEditRow.value.转发能力,
        软件平台: currentEditRow.value.软件平台,
        交叉方式: currentEditRow.value.交叉方式,
        PHY芯片: currentEditRow.value.PHY芯片,
        时钟芯片: currentEditRow.value.时钟芯片,
        内存: currentEditRow.value.内存,
        SDSSD: currentEditRow.value.SDSSD,
        FPGA: FPGA,
        CPLD: currentEditRow.value.CPLD,
        FLASH: currentEditRow.value.FLASH,
        子架EEPROM: currentEditRow.value.子架EEPROM,
        母板EEPROM: currentEditRow.value.母板EEPROM,
        domain: field.value,
        update_user: user.userInfo.name,
      };

      // 调用后端API保存数据
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Board_set`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP错误! 状态码: ${response.status}`);
      }

      const responseData = await response.json();

      if (responseData.status !== 'success') {
        throw new Error(responseData.message || '保存单板数据失败');
      }
      currentEditRow.value.FPGA = FPGA;
      // 根据是否有id判断是新建还是编辑
      const isNewRecord = !currentEditRow.value.id;

      if (isNewRecord) {
        // 新建记录，添加到表格数据中
        const newRowData = {
          id: currentEditRow.value.单板名称,
          单板编号: currentEditRow.value.单板编号,
          单板名称: currentEditRow.value.单板名称,
          单板类型: currentEditRow.value.单板类型,
          领域: currentEditRow.value.领域,
          产品: currentEditRow.value.产品,
          子架: currentEditRow.value.子架,
          主控: currentEditRow.value.主控,
          boardid: currentEditRow.value.boardid,
          functionid: currentEditRow.value.functionid,
          子卡: currentEditRow.value.子卡,
          交换芯片: currentEditRow.value.交换芯片,
          面板端口: currentEditRow.value.面板端口,
          转发能力: currentEditRow.value.转发能力,
          软件平台: currentEditRow.value.软件平台,
          交叉方式: currentEditRow.value.交叉方式,
          PHY芯片: currentEditRow.value.PHY芯片,
          时钟芯片: currentEditRow.value.时钟芯片,
          内存: currentEditRow.value.内存,
          SDSSD: currentEditRow.value.SDSSD,
          FPGA: currentEditRow.value.FPGA,
          CPLD: currentEditRow.value.CPLD,
          FLASH: currentEditRow.value.FLASH,
          子架EEPROM: currentEditRow.value.子架EEPROM,
          母板EEPROM: currentEditRow.value.母板EEPROM,
          支持特性: [],
          支持模块: [],
          agent: '支持',
        };
        data.value.push(newRowData);
        MessagePlugin.success(responseData.message || '新建成功');
      } else {
        // 编辑记录，更新表格数据
        const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
        if (index !== -1) {
          data.value[index] = {
            ...currentEditRow.value,
            支持特性: Array.isArray(currentEditRow.value.支持特性) ? currentEditRow.value.支持特性 : [],
            支持模块: Array.isArray(currentEditRow.value.支持模块) ? currentEditRow.value.支持模块 : [],
          };
        }
        MessagePlugin.success(responseData.message || '保存成功');
      }

      diagVisible.value = false;
      return true;
    }
    return false;
  } catch (error) {
    console.error('保存失败:', error);
    MessagePlugin.error(error.message || '保存失败');
    return false;
  }
};

// 关闭编辑对话框
const onCloseEdit = () => {
  editFormRef.value.reset();
  diagVisible.value = false;
};

const data = ref();
const tableRef = ref();
const editableRowKeys = ref([]);
const tableLoading = ref(false);
const currentSaveId = ref('');
const editMap = {};
const field = ref('支撑');
const tableContentWidth = ref('2500px');
const fieldOptions = [
  { label: 'L0领域', value: 'L0' },
  { label: 'L1领域', value: 'L1' },
  { label: 'L2领域', value: 'L2' },
  { label: '支撑领域', value: '支撑' },
  { label: '智控领域', value: '智控' },
];

// 筛选相关变量
const filterValue = ref({});
const filteredData = computed(() => {
  if (!data.value || data.value.length === 0) {
    return [];
  }

  // 如果没有筛选条件，返回原始数据
  if (!filterValue.value || Object.keys(filterValue.value).length === 0) {
    return data.value;
  }

  // 根据筛选条件过滤数据
  return data.value.filter((row) => {
    // 检查单板类型筛选
    if (filterValue.value['单板类型'] && filterValue.value['单板类型'].length > 0) {
      const selectedTypes = filterValue.value['单板类型'];
      if (!selectedTypes.includes(row.单板类型)) {
        return false;
      }
    }

    // 检查领域筛选
    if (filterValue.value['领域'] && filterValue.value['领域'].length > 0) {
      const selectedDomains = filterValue.value['领域'];
      if (!selectedDomains.includes(row.领域)) {
        return false;
      }
    }

    return true;
  });
});

const updateEditState = (id) => {
  const index = editableRowKeys.value.findIndex((t) => t === id);
  editableRowKeys.value.splice(index, 1);
};

const onEdit = (e) => {
  console.log('onEdit');
  const { id } = e.currentTarget.dataset;
  if (!editableRowKeys.value.includes(id)) {
    editableRowKeys.value.push(id);
  }
};

const onCancel = (e) => {
  console.log('onCancel');
  const { id } = e.currentTarget.dataset;
  updateEditState(id);
  tableRef.value.clearValidateData();
};

const onSave = (e) => {
  console.log('onSave');
  const { id } = e.currentTarget.dataset;
  currentSaveId.value = id;

  const current = editMap[currentSaveId.value];
  if (current) {
    data.value.splice(current.rowIndex, 1, current.editedRow);
    MessagePlugin.success('保存成功');
  }
  updateEditState(currentSaveId.value);
};

// 删除行数据
const onDeleteRow = async (row) => {
  try {
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Board_del`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        board_name: row.单板名称,
        update_user: user.userInfo.name,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '删除单板数据失败');
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
  tableLoading.value = true; // 开始加载时显示加载状态
  console.log('开始读取单板数据...');

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
      response = await fetch(`${SERVER_API_URL}/api_data/API_Board_read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: field.value || '' }),
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
    } catch (error) {
      console.error('解析响应JSON失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
      throw new Error(ERROR_MESSAGES.INVALID_JSON);
    }

    if (responseData.status !== 'success') {
      const errorMsg = responseData.message || '读取单板数据失败';
      console.error('服务器返回错误:', errorMsg);
      MessagePlugin.error(errorMsg);
      throw new Error(errorMsg);
    }

    console.log('单板数据读取成功，服务器消息：', responseData.message);

    let boardData = responseData.boardData || [];

    if (typeof boardData === 'string') {
      try {
        boardData = JSON.parse(boardData);
      } catch (error) {
        console.error('解析单板数据JSON失败:', error);
        MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
        throw new Error(ERROR_MESSAGES.INVALID_JSON);
      }
    }

    if (!Array.isArray(boardData)) {
      console.error('单板数据格式不正确:', boardData);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
      throw new Error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
    }

    data.value = boardData.map((item, index) => {
      const features = Array.isArray(item.支持特性) ? item.支持特性 : [];
      const featureCount = features.length;

      const modules = Array.isArray(item.支持模块) ? item.支持模块 : [];
      const moduleCount = modules.length;

      // 处理SDSSD数据，将其转换为子表格格式
      const sdssdData = Array.isArray(item.SDSSD数据) ? item.SDSSD数据 : [];

      // 处理PHY芯片数据，将其转换为子表格格式
      const phyData = Array.isArray(item.PHY数据) ? item.PHY数据 : [];

      // 处理交换芯片数据，将其转换为子表格格式
      const switchData = Array.isArray(item.交换芯片数据) ? item.交换芯片数据 : [];

      // 处理时钟芯片数据，将其转换为子表格格式
      const clockData = Array.isArray(item.时钟芯片数据) ? item.时钟芯片数据 : [];

      // 处理CPU数据，将其转换为子表格格式
      const cpuData = Array.isArray(item.CPU数据) ? item.CPU数据 : [];

      return {
        id: item.单板名称 || index.toString(),
        单板编号: item.单板编号 || '',
        单板名称: item.单板名称 || '',
        单板类型: item.单板类型 || '',
        领域: item.领域 || '',
        产品: item.产品 || '',
        子架: item.子架 || '',
        主控: item.主控 || '',
        boardid: item.boardid || '',
        functionid: item.functionid || '',
        子卡: item.子卡 || '',
        交换芯片: item.交换芯片 || '',
        面板端口: item.面板端口 || '',
        转发能力: item.转发能力 || '',
        软件平台: item.软件平台 || '',
        交叉方式: item.交叉方式 || '',
        PHY芯片: item.PHY芯片 || '',
        时钟芯片: item.时钟芯片 || '',
        内存: item.内存 || '',
        SDSSD: item.SDSSD || '',
        FPGA: item.FPGA || '',
        CPLD: item.CPLD || '',
        FLASH: item.FLASH || '',
        子架EEPROM: item.子架EEPROM || '',
        母板EEPROM: item.母板EEPROM || '',
        支持特性: features.map((feature) => ({
          feature_id: feature.feature_id || '',
          feature_name: feature.feature_name || '',
          feature_level: feature.feature_level || '',
          feature_support: feature.feature_support || '',
        })),
        支持模块: modules,
        SDSSD数据: sdssdData,
        PHY数据: phyData,
        交换芯片数据: switchData,
        时钟芯片数据: clockData,
        CPU数据: cpuData,
        issue: {
          count: featureCount,
          data: [],
        },
        agent: '支持',
      };
    });

    // 填充筛选选项
    // 获取所有唯一的单板类型
    const uniqueTypes = [...new Set(data.value.map((item) => item.单板类型).filter((item) => item))];
    // 更新单板类型列的筛选选项
    const typeColumnIndex = columns.findIndex((col) => col.colKey === '单板类型');
    if (typeColumnIndex !== -1) {
      columns[typeColumnIndex].filter.props.options = uniqueTypes.map((type) => ({ label: type, value: type }));
    }

    // 获取所有唯一的领域
    const uniqueDomains = [...new Set(data.value.map((item) => item.领域).filter((item) => item))];
    // 更新领域列的筛选选项
    const domainColumnIndex = columns.findIndex((col) => col.colKey === '领域');
    if (domainColumnIndex !== -1) {
      columns[domainColumnIndex].filter.props.options = uniqueDomains.map((domain) => ({
        label: domain,
        value: domain,
      }));
    }

    // 获取所有唯一的产品
    const uniqueProducts = [...new Set(data.value.map((item) => item.产品).filter((item) => item))];
    // 更新产品列的筛选选项
    const productColumnIndex = columns.findIndex((col) => col.colKey === '产品');
    if (productColumnIndex !== -1) {
      columns[productColumnIndex].filter.props.options = uniqueProducts.map((product) => ({
        label: product,
        value: product,
      }));
    }

    // 更新全局AI的上下文
    tableAiContext.value = JSON.stringify(
      data.value.map((item) => {
        // 由于支持特性字段内容过多，这里需要屏蔽掉
        const { 支持特性, ...rest } = item;
        return rest;
      }),
      null,
      2,
    );

    MessagePlugin.success(responseData.message || '单板数据加载成功');
    console.log('单板数据处理完成，共加载', data.value.length, '条记录');
    return boardData;
  } catch (error) {
    console.error('单板数据读取过程中出错:', error);
    if (!Object.values(ERROR_MESSAGES).includes(error.message)) {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    tableLoading.value = false; // 数据加载完成后关闭加载状态
  }
};

// 筛选变化处理函数
const onFilterChange = (filterParams) => {
  console.log('筛选条件变化:', filterParams);
  // 更新筛选值
  filterValue.value = { ...filterParams };
  MessagePlugin.success('筛选条件已更新');
};

onMounted(() => {
  onTableRead();
});
</script>

<style>
.table-operations .t-link {
  margin-right: 8px;
}

.board-main {
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
    border-left: none;
    border-right: none;
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
}

/* 编辑表单样式 */
.edit-form .t-form__item {
  margin-bottom: 20px;
}

/* SDSSD详情样式 */
.sdssd-details {
  padding: 20px;
}

.sdssd-details .t-descriptions__body {
  border-radius: 6px;
}
</style>
