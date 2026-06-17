<template>
    <div class="requirement-list-main">
        <!-- HAI 加载遮罩 -->
        <div id="hai-loader-mask" style="display: none;">
            <div class="hai-spinner"></div>
            <div id="hai-loader-text">正在准备需求列表...</div>
        </div>

        <t-space direction="vertical" style="width: 100%">
            <!-- 筛选区域 -->
            <t-space direction="vertical" style="width: 100%">
                <t-space :size="16" style="flex-wrap: wrap">
                    <t-select
                        v-model="filterForm.belong_product"
                        placeholder="所属产品"
                        clearable
                        style="width: 200px"
                        label="所属产品: "
                        @change="handleFilterChange">
                        <t-option v-for="option in productOptions" :key="option" :value="option" :label="option" />
                    </t-select>
                    <t-select
                        v-model="filterForm.product_roadmap"
                        placeholder="产品路标"
                        clearable
                        filterable
                        creatable
                        style="width: 200px"
                        label="产品路标: "
                        :options="productRoadmapOptions"
                        @change="handleFilterChange"
                        @create="handleCreateProductRoadmap">
                    </t-select>
                    <t-select
                        v-model="filterForm.requirement_preplanning"
                        placeholder="需求预规划"
                        clearable
                        filterable
                        creatable
                        style="width: 200px"
                        label="需求预规划: "
                        :options="requirementPreplanningOptions"
                        @change="handleFilterChange"
                        @create="handleCreateRequirementPreplanning">
                    </t-select>
                    <t-select
                        v-model="filterForm.domain"
                        placeholder="领域"
                        clearable
                        filterable
                        creatable
                        style="width: 200px"
                        label="领域: "
                        :options="domainOptions"
                        @change="handleFilterChange"
                        @create="handleCreateDomain">
                    </t-select>
                    <t-select
                        v-model="filterForm.team"
                        placeholder="团队"
                        clearable
                        filterable
                        creatable
                        style="width: 200px"
                        label="团队: "
                        :options="teamOptions"
                        @change="handleFilterChange"
                        @create="handleCreateTeam">
                    </t-select>
                    <t-select
                        v-model="filterForm.work_item_type"
                        placeholder="工作项类型"
                        clearable
                        style="width: 200px"
                        label="工作项类型: "
                        @change="handleFilterChange">
                        <t-option v-for="option in workItemTypeOptions" :key="option" :value="option" :label="option" />
                    </t-select>
                    <t-button @click="handleFilter">查询</t-button>
                    <t-button theme="primary" @click="openSyncDialog">从RDC同步数据</t-button>
                    <t-button theme="primary" @click="openScheduleDialog">需求自动排期</t-button>
                    <t-button theme="primary" @click="openBackfillDialog">数据回填到RDC</t-button>
                </t-space>
            </t-space>

            <!-- 表格区域 -->
            <t-table
                ref="tableRef"
                row-key="id"
                :columns="tableColumns"
                :data="tableData"
                :selected-row-keys="selectedRowKeys"
                :select-on-row-click="false"
                :max-height="tableHeight"
                :filter-value="filterValue"
                :hover="true"
                bordered
                resizable
                :loading="loading"
                :scroll="{ type: 'virtual' }"
                @select-change="handleSelectChange"
                @row-edit="handleRowEdit"
                @filter-change="onFilterChange">
            </t-table>

            <!-- 编辑弹窗 -->
            <t-dialog
                v-model:visible="editDialogVisible"
                header="编辑需求排期"
                width="900px"
                :confirm-btn="{ loading: editSaving }"
                @confirm="handleSaveEdit"
                @cancel="handleCancelEdit">
                <div class="add-form">
                    <t-form
                        ref="editFormRef"
                        :data="editFormData"
                        :rules="editFormRules"
                        label-width="180px"
                        layout="vertical">
                        <t-form-item label="评估结论（第一次）" name="first_evaluation_conclusion">
                            <t-textarea
                                v-model="editFormData.first_evaluation_conclusion"
                                placeholder="请输入评估结论（第一次）"
                                :autosize="{ minRows: 3, maxRows: 6 }"
                                :maxlength="5000" />
                        </t-form-item>
                        <t-form-item label="预计开发工作量（人天）" name="estimated_dev_workload">
                            <t-input-number
                                v-model="editFormData.estimated_dev_workload"
                                placeholder="请输入预计开发工作量"
                                :precision="2"
                                :min="0"
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="预计验证工作量（人天）" name="estimated_verification_workload">
                            <t-input-number
                                v-model="editFormData.estimated_verification_workload"
                                placeholder="请输入预计验证工作量"
                                :precision="2"
                                :min="0"
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="预计系统测试工作量（人天）" name="estimated_system_test_workload">
                            <t-input-number
                                v-model="editFormData.estimated_system_test_workload"
                                placeholder="请输入预计系统测试工作量"
                                :precision="2"
                                :min="0"
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划开始开发日期" name="plan_start_dev_date">
                            <t-date-picker
                                v-model="editFormData.plan_start_dev_date"
                                placeholder="请选择计划开始开发日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划完成开发日期" name="plan_finish_dev_date">
                            <t-date-picker
                                v-model="editFormData.plan_finish_dev_date"
                                placeholder="请选择计划完成开发日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划开始集成测试日期" name="plan_start_integration_test_date">
                            <t-date-picker
                                v-model="editFormData.plan_start_integration_test_date"
                                placeholder="请选择计划开始集成测试日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划完成集成测试日期" name="plan_finish_integration_test_date">
                            <t-date-picker
                                v-model="editFormData.plan_finish_integration_test_date"
                                placeholder="请选择计划完成集成测试日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划开始系统测试日期" name="plan_start_system_test_date">
                            <t-date-picker
                                v-model="editFormData.plan_start_system_test_date"
                                placeholder="请选择计划开始系统测试日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划完成系统测试日期" name="plan_finish_system_test_date">
                            <t-date-picker
                                v-model="editFormData.plan_finish_system_test_date"
                                placeholder="请选择计划完成系统测试日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="计划交付日期" name="plan_delivery_date">
                            <t-date-picker
                                v-model="editFormData.plan_delivery_date"
                                placeholder="请选择计划交付日期"
                                format="YYYY-MM-DD"
                                clearable
                                style="width: 100%" />
                        </t-form-item>
                    </t-form>
                </div>
            </t-dialog>

            <!-- RDC 数据同步对话框 -->
            <t-dialog
                v-model:visible="syncDialogVisible"
                :width="500"
                header="从RDC同步数据"
                :confirm-btn="{ loading: syncLoading, content: '开始同步' }"
                @confirm="handleSyncConfirm"
                @cancel="handleSyncCancel">
                <t-space direction="vertical" style="width: 100%">
                    <t-alert
                        theme="warning"
                        message="此操作将清空现有需求清单数据，并从RDC平台重新拉取。请确认后再操作。"
                        style="margin-bottom: 8px" />
                    <t-form
                        ref="syncFormRef"
                        :data="syncFormData"
                        label-width="100px"
                        layout="vertical">
                        <t-form-item label="工作项类型" name="work_type">
                            <t-select v-model="syncFormData.work_type" style="width: 100%">
                                <t-option value="产品需求" label="产品需求" />
                                <t-option value="市场需求" label="市场需求" />
                                <t-option value="用户故事" label="用户故事" />
                            </t-select>
                        </t-form-item>
                        <t-form-item label="团队" name="team">
                            <t-select
                                v-model="syncFormData.team"
                                filterable
                                style="width: 100%"
                                :options="rdcTeamOptions" />
                        </t-form-item>
                        <t-form-item label="工号" name="username">
                            <t-input v-model="syncFormData.username" placeholder="请输入工号" style="width: 100%" />
                        </t-form-item>
                        <t-form-item label="密码" name="password">
                            <t-input
                                v-model="syncFormData.password"
                                type="password"
                                placeholder="请输入密码"
                                style="width: 100%" />
                        </t-form-item>
                    </t-form>
                </t-space>
            </t-dialog>

            <!-- 需求自动排期对话框 -->
            <t-dialog
                v-model:visible="scheduleDialogVisible"
                :width="500"
                header="需求自动排期"
                :confirm-btn="{ loading: scheduleLoading, content: '开始排期' }"
                @confirm="handleScheduleConfirm"
                @cancel="scheduleDialogVisible = false">
                <t-space direction="vertical" style="width: 100%">
                    <t-alert
                        theme="info"
                        message="根据需求预规划和工作项类型，对符合条件的PR进行优先级自动排序。"
                        style="margin-bottom: 8px" />
                    <t-form
                        ref="scheduleFormRef"
                        :data="scheduleFormData"
                        label-width="110px"
                        layout="vertical">
                        <t-form-item label="需求预规划" name="requirement_preplanning">
                            <t-select
                                v-model="scheduleFormData.requirement_preplanning"
                                filterable
                                clearable
                                placeholder="请选择需求预规划（必填）"
                                style="width: 100%"
                                :options="requirementPreplanningOptions" />
                        </t-form-item>
                        <t-form-item label="工作项类型" name="work_type">
                            <t-select v-model="scheduleFormData.work_type" style="width: 100%">
                                <t-option value="产品需求" label="产品需求" />
                                <t-option value="市场需求" label="市场需求" />
                                <t-option value="用户故事" label="用户故事" />
                            </t-select>
                        </t-form-item>
                        <t-form-item label="领域" name="domain">
                            <t-select
                                v-model="scheduleFormData.domain"
                                multiple
                                filterable
                                clearable
                                placeholder="请选择领域（可多选，不选则全部）"
                                style="width: 100%"
                                :options="domainOptions" />
                        </t-form-item>
                        <t-form-item label="团队" name="team">
                            <t-select
                                v-model="scheduleFormData.team"
                                multiple
                                filterable
                                clearable
                                placeholder="请选择团队（可多选，不选则全部）"
                                style="width: 100%"
                                :options="teamOptions" />
                        </t-form-item>
                        <t-form-item label="用户名" name="username">
                            <t-input
                                v-model="scheduleFormData.username"
                                placeholder="请输入工号（必填）"
                                clearable />
                        </t-form-item>
                        <t-form-item label="密码" name="password">
                            <t-input
                                v-model="scheduleFormData.password"
                                type="password"
                                placeholder="请输入密码（必填）"
                                clearable />
                        </t-form-item>
                    </t-form>
                </t-space>
            </t-dialog>

            <!-- RDC 数据回填对话框 -->
            <t-dialog
                v-model:visible="backfillDialogVisible"
                :width="500"
                header="数据回填到RDC"
                :confirm-btn="{ loading: backfillLoading, content: '开始回填', disabled: !backfillPreviewed }"
                @confirm="handleBackfillRdc"
                @cancel="handleBackfillCancel">
                <t-space direction="vertical" style="width: 100%">
                    <t-alert
                        theme="warning"
                        message="将当前筛选条件下、已排期的数据回填到 RDC。请先查询统计，确认后再操作。"
                        style="margin-bottom: 8px" />
                    <t-form ref="backfillFormRef" :data="backfillFormData" label-width="100px" layout="vertical">
                        <t-form-item label="工号" name="username">
                            <t-select
                                v-model="backfillFormData.username"
                                filterable
                                creatable
                                placeholder="请选择或输入工号"
                                style="width: 100%"
                                :options="usernameOptions"
                                @create="handleCreateUsername" />
                        </t-form-item>
                        <t-form-item label="密码" name="password">
                            <t-input
                                v-model="backfillFormData.password"
                                type="password"
                                placeholder="请输入密码"
                                style="width: 100%" />
                        </t-form-item>
                    </t-form>
                    <t-button
                        theme="primary"
                        variant="outline"
                        block
                        :loading="previewLoading"
                        @click="handlePreviewBackfill">
                        查询统计
                    </t-button>
                    <t-alert
                        v-if="backfillPreviewed"
                        :theme="backfillCount > 0 ? 'info' : 'warning'"
                        :message="backfillPreviewMessage"
                        style="margin-top: 8px" />
                </t-space>
            </t-dialog>
        </t-space>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, computed, h } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import {
    queryRequirementScheduleByParams,
    updateRequirementSchedule,
    saveFilterHistory,
    syncRdcData,
    autoScheduling,
    previewBackfillRdcData,
    backfillRdcData,
} from '@/api/requireSchedule.js';
import { pubCalculateTableHeight } from '@/utils/pub';

/* ==================== HAI 工具集成 ==================== */
let currentToolCall = null
const _haiInIframe = window.parent !== window
const _haiHasIdParam = window.location.search.includes('id=')

// 发送消息到 HAI
const sendHAIMessage = (message) => {
    if (window.parent !== window) {
        console.log('[HAI] Sending message:', message)
        window.parent.postMessage(message, '*')
    } else {
        console.log('[HAI] Not in iframe, skipping message send')
    }
}

// 发送执行结果
const sendHAIResult = (code, message, data = {}) => {
    const resultMessage = {
        type: 'HAI_TOOL_CALL_RESULT',
        toolCallId: currentToolCall ? currentToolCall.toolCallId : 'requirement_list_ready_id',
        toolCallName: currentToolCall ? currentToolCall.toolCallName : 'WA_Dispatcher',
        code: code,
        message: message,
        rawEvent: currentToolCall ? currentToolCall.rawEvent : null,
        timestamp: new Date().getTime(),
        data: JSON.stringify(data)
    }
    sendHAIMessage(resultMessage)
}

// 从URL获取ID参数
const getIdFromUrl = () => {
    const params = new URLSearchParams(window.location.search)
    return params.get('id')
}

const user = useUserStore();

// 权限控制
const canEdit = ref(false);
const filterValue = ref({});
// 筛选表单
const filterForm = ref({
    belong_product: '',
    product_roadmap: '',
    requirement_preplanning: '',
    domain: '',
    team: '',
    work_item_type: ''
});

// 筛选选项
const productOptions = ref(['ZXONE 19700', 'ZXONE 9700', 'ZXMP M721', 'ZXONE 7000', 'ZXONE NTON']);
const productRoadmapOptions = ref([]);
const requirementPreplanningOptions = ref([]);
const domainOptions = ref([]);
const teamOptions = ref([]);
const workItemTypeOptions = ref(['市场需求', '产品需求', '用户故事']);

// 表格相关
const tableRef = ref();
const tableData = ref([]);
const allTableData = ref([]);
const selectedRowKeys = ref([]);
const loading = ref(false);
const saving = ref(false);
const exporting = ref(false);
const tableHeight = ref('900px');

// 需求自动排期对话框相关
const scheduleDialogVisible = ref(false);
const scheduleLoading = ref(false);
const scheduleFormRef = ref();
const scheduleFormData = ref({
    requirement_preplanning: '',
    work_type: '产品需求',
    domain: [],
    team: [],
    username: '',
    password: '',
});

// RDC 同步对话框相关
const syncDialogVisible = ref(false);
const syncLoading = ref(false);
const syncFormRef = ref();
const syncFormData = ref({
    work_type: '产品需求',
    team: '',
    username: '',
    password: '',
});
const rdcTeamOptions = ref([
    'L1-保护团队', 'L1-大师业务团队', 'L1-功能团队', 'L1-功能一组', 'L1-功能三组',
    'L1-管理团队', 'L1-集测团队', 'L1-疾风业务团队', 'L1-开心果', 'L1-雷神业务团队',
    'L1-领域测试', 'L1-平台团队', 'L1-神盾业务团队', 'L1-性能团队', 'L1-星火业务团队',
    'L1-专家团队', 'L1-量子业务团队',
    'L2-超能', 'L2-阳光部落', 'L2-追风', 'L2-集结号', 'L2-全能', 'L2-领域系统测试',
    'L0-管理团队', 'L0-光速', 'L0-极光', 'L0-疾电之光', 'L0-领域测试', 'L0-磐石',
    'BSP-FTD舰队', 'BSP-银河舰队', '仿真-天问', '工具支撑团队',
    '06-逻辑北京', '06-硬件北京', '07-逻辑武汉', '13-智能控制',
    '智控-APO团队', '智控-集测团队', '智控-WASON团队', '智能控制-管理团队',
    '支撑-BaseMan守垒员', '支撑-北极星', '支撑-乘风破浪', '支撑-管理团队',
    '支撑-混沌Chaos', '支撑-领域测试', '支撑-茅店神', '支撑-破冰号',
    '支撑-StarWar', '支撑-猿宇宙', '支撑-原点',
    '硬件武汉-光机', '硬件武汉-可靠性', '硬件武汉-硬测', '硬件武汉-硬开',
    '00-L0外购非相干光模块', '00-L0外购相干光模块',
].map((t) => ({ label: t, value: t })));

// RDC 回填
const backfillDialogVisible = ref(false);
const backfillLoading = ref(false);
const backfillFormRef = ref();
const backfillFormData = ref({ username: '', password: '' });
const usernameOptions = ref([]);
const previewLoading = ref(false);
const backfillPreviewed = ref(false);
const backfillCount = ref(0);

const backfillPreviewMessage = computed(() => {
    if (backfillCount.value > 0) {
        return `预计回填 ${backfillCount.value} 条需求，请确认后点击「开始回填」`;
    }
    return '当前筛选条件下无待回填的需求';
});

const openBackfillDialog = async () => {
    await loadUsernameHistory();
    backfillFormData.value = { 
        username: user.userInfo?.employNo || '', 
        password: '' 
    };
    backfillPreviewed.value = false;
    backfillCount.value = 0;
    backfillDialogVisible.value = true;
};

const loadUsernameHistory = async () => {
    try {
        const response = await getFilterHistory({ filter_type: 'username' });
        if (response.code === 200) {
            usernameOptions.value = (response.data || []).map(item => ({ 
                label: item, 
                value: item 
            }));
        }
    } catch (error) {
        console.error('加载工号历史失败:', error);
    }
};

const handleCreateUsername = async (value) => {
    if (!value) return;
    try {
        await saveFilterHistory({
            filter_type: 'username',
            filter_value: value
        });
        const exists = usernameOptions.value.some(opt => opt.value === value);
        if (!exists) {
            usernameOptions.value.push({ label: value, value: value });
            usernameOptions.value.sort((a, b) => a.value.localeCompare(b.value));
        }
        backfillFormData.value.username = value;
        MessagePlugin.success('保存成功');
    } catch (error) {
        MessagePlugin.error('保存失败');
    }
};

const handlePreviewBackfill = async () => {
    previewLoading.value = true;
    try {
        const response = await previewBackfillRdcData({
            requirement_preplanning: filterForm.value.requirement_preplanning || '',
            work_type: filterForm.value.work_item_type || '',
            domain: filterForm.value.domain || '',
            team: filterForm.value.team || '',
        });
        if (response.code === 200) {
            backfillCount.value = response.data?.count || 0;
            backfillPreviewed.value = true;
        } else {
            MessagePlugin.error(response.message || '查询统计失败');
            backfillPreviewed.value = false;
        }
    } catch (error) {
        MessagePlugin.error(error?.message || '查询统计失败');
        console.error('查询统计失败:', error);
        backfillPreviewed.value = false;
    } finally {
        previewLoading.value = false;
    }
};

const handleBackfillRdc = async () => {
    if (!backfillPreviewed.value) {
        MessagePlugin.warning('请先查询统计');
        return;
    }

    const username = (backfillFormData.value.username || '').trim();
    const password = (backfillFormData.value.password || '').trim();
    
    if (!username) {
        MessagePlugin.warning('请输入工号');
        return;
    }
    if (!password) {
        MessagePlugin.warning('请输入密码');
        return;
    }
    
    backfillLoading.value = true;
    try {
        const response = await backfillRdcData({
            username,
            password,
            requirement_preplanning: filterForm.value.requirement_preplanning || '',
            work_type: filterForm.value.work_item_type || '',
            domain: filterForm.value.domain || '',
            team: filterForm.value.team || '',
        });
        if (response.code === 200) {
            MessagePlugin.success(response.message || 'RDC 数据回填成功');
            backfillDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || 'RDC 数据回填失败');
        }
    } catch (error) {
        MessagePlugin.error(error?.message || 'RDC 数据回填失败');
        console.error('RDC 数据回填失败:', error);
    } finally {
        backfillLoading.value = false;
    }
};

const handleBackfillCancel = () => {
    backfillPreviewed.value = false;
    backfillCount.value = 0;
    backfillDialogVisible.value = false;
};

// 编辑弹窗相关
const editDialogVisible = ref(false);
const editFormRef = ref();
const editSaving = ref(false);
const editFormData = ref({
    id: null,
    first_evaluation_conclusion: '',
    estimated_dev_workload: null,
    estimated_verification_workload: null,
    estimated_system_test_workload: null,
    plan_start_dev_date: '',
    plan_finish_dev_date: '',
    plan_start_integration_test_date: '',
    plan_finish_integration_test_date: '',
    plan_start_system_test_date: '',
    plan_finish_system_test_date: '',
    plan_delivery_date: ''
});

// 编辑表单验证规则
const editFormRules = {
    estimated_dev_workload: [
        { type: 'number', min: 0, message: '预计开发工作量不能小于0' }
    ],
    estimated_verification_workload: [
        { type: 'number', min: 0, message: '预计验证工作量不能小于0' }
    ],
    estimated_system_test_workload: [
        { type: 'number', min: 0, message: '预计系统测试工作量不能小于0' }
    ]
};

const onFilterChange = (filters, ctx) => {
  filterValue.value = {
    ...filters,
  };
  request(filters);
};

// 表格列定义
const tableColumns = computed(() => [
    {
        colKey: 'row-select',
        type: 'multiple',
        width: 50,
    },
    { colKey: 'id', title: 'ID', width: 80, align: 'center' },
    { 
        colKey: 'work_item_type', 
        title: '工作项类型', 
        width: 120, 
        align: 'center',
        ellipsis: true,
        filter: {
            type: 'multiple',
            resetValue: [],
            list: [
                { label: 'All', checkAll: true },
                { label: '市场需求', value: '市场需求' },
                { label: '产品需求', value: '产品需求' },
                { label: '用户故事', value: '用户故事' },
            ],
            showConfirmAndReset: true,
        }
    },
    {
        colKey: 'identifier',
        title: () => (<div style={{ textAlign: 'center' }}>标识</div>),
        width: 150,
        align: 'center',
        cell: (_, { row }) => {
        const getRdcHref = (relatedRdcIdent) => {
            if (!relatedRdcIdent) return '';
            const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
            const appPath = '/apps/wim/allWorkItems';
            const configs = {
            OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
            OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
            };
            const config = Object.entries(configs).find(([key]) =>
            relatedRdcIdent.includes(key)
            )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };
            return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
        };
        const href = getRdcHref(row.identifier);
        return (
            <t-link
            theme="primary"
            href={href}
            target="_blank"
            hover="underline"
            >
            {row.identifier}
            </t-link>
        );
        },
    },
    { 
        colKey: 'belong_product', 
        title: '所属产品', 
        width: 150, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'product_roadmap', 
        title: '产品路标', 
        width: 150, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'requirement_preplanning', 
        title: '需求预规划', 
        width: 150, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'title', 
        title: '标题', 
        width: 200, 
        align: 'left',
        ellipsis: true
    },
    { 
        colKey: 'reuse_degree', 
        title: '复用程度', 
        width: 100, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'feature_identifier', 
        title: '特性标识', 
        width: 150, 
        align: 'left',
        ellipsis: true
    },
    { 
        colKey: 'feature_attribute', 
        title: '特性属性', 
        width: 150, 
        align: 'left',
        ellipsis: true
    },
    { 
        colKey: 'verification_mode', 
        title: '验证方式', 
        width: 120, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'verification_team', 
        title: '验证团队', 
        width: 120, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'requirement_sort', 
        title: '需求排序', 
        width: 100, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'priority', 
        title: '优先级', 
        width: 100, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'domain', 
        title: '领域', 
        width: 120, 
        align: 'center',
        ellipsis: true
    },
    { 
        colKey: 'team', 
        title: '团队', 
        width: 120, 
        align: 'center',
        ellipsis: true
    },
    {
        colKey: 'first_evaluation_conclusion',
        title: '评估结论（第一次）',
        width: 200,
        align: 'left',
        ellipsis: true
    },
    {
        colKey: 'second_evaluation_conclusion',
        title: '评估结论（第二次）',
        width: 200,
        align: 'left',
        ellipsis: true
    },
    {
        colKey: 'estimated_workload',
        title: '预计工作量',
        width: 120,
        align: 'right',
        ellipsis: true
    },
    {
        colKey: 'estimated_dev_workload',
        title: '预计开发工作量',
        width: 150,
        align: 'right'
    },
    {
        colKey: 'estimated_verification_workload',
        title: '预计验证工作量',
        width: 150,
        align: 'right'
    },
    {
        colKey: 'estimated_system_test_workload',
        title: '预计系统测试工作量',
        width: 180,
        align: 'right'
    },
    {
        colKey: 'plan_start_dev_date',
        title: '计划开始开发日期',
        width: 160,
        align: 'center'
    },
    {
        colKey: 'plan_finish_dev_date',
        title: '计划完成开发日期',
        width: 160,
        align: 'center'
    },
    {
        colKey: 'plan_start_integration_test_date',
        title: '计划开始集成测试日期',
        width: 180,
        align: 'center'
    },
    {
        colKey: 'plan_finish_integration_test_date',
        title: '计划完成集成测试日期',
        width: 180,
        align: 'center'
    },
    {
        colKey: 'plan_start_system_test_date',
        title: '计划开始系统测试日期',
        width: 180,
        align: 'center'
    },
    {
        colKey: 'plan_finish_system_test_date',
        title: '计划完成系统测试日期',
        width: 180,
        align: 'center'
    },
    {
        colKey: 'plan_delivery_date',
        title: '计划交付日期',
        width: 160,
        align: 'center'
    },
    {
        colKey: 'operation',
        title: '操作',
        width: 100,
        align: 'center',
        fixed: 'right',
        cell: (h, { row }) => {
            return (
                <t-link theme="primary" hover="color" onClick={() => handleEdit(row)}>
                    编辑
                </t-link>
            );
        }
    }
]);

const request = (filters) => {
  const timer = setTimeout(() => {
    clearTimeout(timer);
    const newData = allTableData.value.filter((item) => {
      let result = true;
      if (result && filters.work_item_type && filters.work_item_type.length) {
        result = filters.work_item_type.includes(item.work_item_type);
      }
      return result;
    });
    tableData.value = newData;
  }, 100);
};

// 生命周期
onMounted(async () => {
    tableHeight.value = pubCalculateTableHeight();
    await loadData();

    // HAI 初始化
    sendReadyAndHandleLoad()
    window.addEventListener('message', handleHAIMessage)
});

// 从主表数据中提取唯一值，填充下拉选项
const extractUniqueValuesFromData = (data) => {
    if (!data || data.length === 0) return;
    
    const productRoadmapSet = new Set();
    const requirementPreplanningSet = new Set();
    const domainSet = new Set();
    const teamSet = new Set();
    
    data.forEach(item => {
        if (item.product_roadmap && item.product_roadmap.trim()) {
            productRoadmapSet.add(item.product_roadmap.trim());
        }
        if (item.requirement_preplanning && item.requirement_preplanning.trim()) {
            requirementPreplanningSet.add(item.requirement_preplanning.trim());
        }
        if (item.domain && item.domain.trim()) {
            domainSet.add(item.domain.trim());
        }
        if (item.team && item.team.trim()) {
            teamSet.add(item.team.trim());
        }
    });
    
    const toOptions = (arr) => arr.map(item => ({ label: item, value: item }));
    
    productRoadmapOptions.value = toOptions(Array.from(productRoadmapSet).sort());
    requirementPreplanningOptions.value = toOptions(Array.from(requirementPreplanningSet).sort());
    domainOptions.value = toOptions(Array.from(domainSet).sort());
    teamOptions.value = toOptions(Array.from(teamSet).sort());
};

// 加载数据
const loadData = async () => {
    loading.value = true;
    try {
        const params = {};
        Object.keys(filterForm.value).forEach(key => {
            if (filterForm.value[key]) {
                params[key] = filterForm.value[key];
            }
        });
        const response = await queryRequirementScheduleByParams(params);
        if (response.code === 200) {
            tableData.value = response.data || [];
            allTableData.value = response.data || [];
            extractUniqueValuesFromData(response.data || []);
        } else {
            MessagePlugin.error(response.message || '加载数据失败');
        }
    } catch (error) {
        MessagePlugin.error('加载数据失败');
        console.error(error);
    } finally {
        loading.value = false;
    }
};

// 筛选
const handleFilter = () => {
    loadData();
};

// 重置筛选
const handleResetFilter = () => {
    filterForm.value = {
        belong_product: '',
        product_roadmap: '',
        requirement_preplanning: '',
        domain: '',
        team: '',
        work_item_type: ''
    };
    loadData();
};

// 筛选变化
const handleFilterChange = () => {};

// 创建新产品路标
const handleCreateProductRoadmap = async (value) => {
    if (!value) return;
    try {
        await saveFilterHistory({
            filter_type: 'product_roadmap',
            filter_value: value
        });
        const exists = productRoadmapOptions.value.some(opt => opt.value === value);
        if (!exists) {
            productRoadmapOptions.value.push({ label: value, value: value });
            productRoadmapOptions.value.sort((a, b) => a.value.localeCompare(b.value));
        }
        filterForm.value.product_roadmap = value;
        MessagePlugin.success('保存成功');
    } catch (error) {
        MessagePlugin.error('保存失败');
    }
};

// 创建新需求预规划
const handleCreateRequirementPreplanning = async (value) => {
    if (!value) return;
    try {
        await saveFilterHistory({
            filter_type: 'requirement_preplanning',
            filter_value: value
        });
        const exists = requirementPreplanningOptions.value.some(opt => opt.value === value);
        if (!exists) {
            requirementPreplanningOptions.value.push({ label: value, value: value });
            requirementPreplanningOptions.value.sort((a, b) => a.value.localeCompare(b.value));
        }
        filterForm.value.requirement_preplanning = value;
        MessagePlugin.success('保存成功');
    } catch (error) {
        MessagePlugin.error('保存失败');
    }
};

// 创建新领域
const handleCreateDomain = async (value) => {
    if (!value) return;
    try {
        await saveFilterHistory({
            filter_type: 'domain',
            filter_value: value
        });
        const exists = domainOptions.value.some(opt => opt.value === value);
        if (!exists) {
            domainOptions.value.push({ label: value, value: value });
            domainOptions.value.sort((a, b) => a.value.localeCompare(b.value));
        }
        filterForm.value.domain = value;
        MessagePlugin.success('保存成功');
    } catch (error) {
        MessagePlugin.error('保存失败');
    }
};

// 创建新团队
const handleCreateTeam = async (value) => {
    if (!value) return;
    try {
        await saveFilterHistory({
            filter_type: 'team',
            filter_value: value
        });
        const exists = teamOptions.value.some(opt => opt.value === value);
        if (!exists) {
            teamOptions.value.push({ label: value, value: value });
            teamOptions.value.sort((a, b) => a.value.localeCompare(b.value));
        }
        filterForm.value.team = value;
        MessagePlugin.success('保存成功');
    } catch (error) {
        MessagePlugin.error('保存失败');
    }
};

// 选择变化
const handleSelectChange = (value) => {
    selectedRowKeys.value = value;
};

// 行编辑
const handleRowEdit = ({ row, col, value }) => {
    row[col.colKey] = value;
};

// 打开编辑弹窗
const handleEdit = (row) => {
    editFormData.value = {
        id: row.id,
        first_evaluation_conclusion: row.first_evaluation_conclusion || '',
        estimated_dev_workload: row.estimated_dev_workload || null,
        estimated_verification_workload: row.estimated_verification_workload || null,
        estimated_system_test_workload: row.estimated_system_test_workload || null,
        plan_start_dev_date: row.plan_start_dev_date || '',
        plan_finish_dev_date: row.plan_finish_dev_date || '',
        plan_start_integration_test_date: row.plan_start_integration_test_date || '',
        plan_finish_integration_test_date: row.plan_finish_integration_test_date || '',
        plan_start_system_test_date: row.plan_start_system_test_date || '',
        plan_finish_system_test_date: row.plan_finish_system_test_date || '',
        plan_delivery_date: row.plan_delivery_date || ''
    };
    editDialogVisible.value = true;
};

// 格式化日期
const formatDate = (date) => {
    if (!date) return '';
    if (typeof date === 'string') return date;
    if (date instanceof Date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    return '';
};

// 保存编辑
const handleSaveEdit = async () => {
    const valid = await editFormRef.value?.validate();
    if (!valid) {
        return;
    }
    
    editSaving.value = true;
    try {
        const submitData = {
            ...editFormData.value,
            plan_start_dev_date: formatDate(editFormData.value.plan_start_dev_date),
            plan_finish_dev_date: formatDate(editFormData.value.plan_finish_dev_date),
            plan_start_integration_test_date: formatDate(editFormData.value.plan_start_integration_test_date),
            plan_finish_integration_test_date: formatDate(editFormData.value.plan_finish_integration_test_date),
            plan_start_system_test_date: formatDate(editFormData.value.plan_start_system_test_date),
            plan_finish_system_test_date: formatDate(editFormData.value.plan_finish_system_test_date),
            plan_delivery_date: formatDate(editFormData.value.plan_delivery_date)
        };
        
        const response = await updateRequirementSchedule({ data: [submitData] });
        if (response.code === 200) {
            MessagePlugin.success('保存成功');
            editDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '保存失败');
        }
    } catch (error) {
        MessagePlugin.error('保存失败');
        console.error(error);
    } finally {
        editSaving.value = false;
    }
};

// 取消编辑
const handleCancelEdit = () => {
    editFormData.value = {
        id: null,
        first_evaluation_conclusion: '',
        estimated_dev_workload: null,
        estimated_verification_workload: null,
        estimated_system_test_workload: null,
        plan_start_dev_date: '',
        plan_finish_dev_date: '',
        plan_start_integration_test_date: '',
        plan_finish_integration_test_date: '',
        plan_start_system_test_date: '',
        plan_finish_system_test_date: '',
        plan_delivery_date: ''
    };
};

// 批量保存
const handleBatchSave = async () => {
    if (selectedRowKeys.value.length === 0) {
        MessagePlugin.warning('请选择要保存的数据');
        return;
    }
    
    saving.value = true;
    try {
        const updateData = tableData.value
            .filter(item => selectedRowKeys.value.includes(item.id))
            .map(item => ({
                id: item.id,
                first_evaluation_conclusion: item.first_evaluation_conclusion,
                estimated_dev_workload: item.estimated_dev_workload,
                estimated_verification_workload: item.estimated_verification_workload,
                estimated_system_test_workload: item.estimated_system_test_workload,
                plan_start_dev_date: item.plan_start_dev_date,
                plan_finish_dev_date: item.plan_finish_dev_date,
                plan_start_integration_test_date: item.plan_start_integration_test_date,
                plan_finish_integration_test_date: item.plan_finish_integration_test_date,
                plan_start_system_test_date: item.plan_start_system_test_date,
                plan_finish_system_test_date: item.plan_finish_system_test_date,
                plan_delivery_date: item.plan_delivery_date
            }));
        
        const response = await updateRequirementSchedule({ data: updateData });
        if (response.code === 200) {
            MessagePlugin.success(response.message || '保存成功');
            await loadData();
            selectedRowKeys.value = [];
        } else {
            MessagePlugin.error(response.message || '保存失败');
        }
    } catch (error) {
        MessagePlugin.error('保存失败');
        console.error(error);
    } finally {
        saving.value = false;
    }
};

// 导出
const handleExport = async () => {
    exporting.value = true;
    try {
        MessagePlugin.info('导出功能开发中');
    } catch (error) {
        MessagePlugin.error('导出失败');
    } finally {
        exporting.value = false;
    }
};

// ===================== 需求自动排期 =====================

const openScheduleDialog = () => {
    scheduleFormData.value = {
        requirement_preplanning: filterForm.value.requirement_preplanning || '',
        work_type: filterForm.value.work_item_type || '产品需求',
        domain: filterForm.value.domain ? [filterForm.value.domain] : [],
        team: filterForm.value.team ? [filterForm.value.team] : [],
        username: '',
        password: '',
    };
    scheduleDialogVisible.value = true;
};

const handleScheduleConfirm = async () => {
    if (!scheduleFormData.value.requirement_preplanning) {
        MessagePlugin.warning('请选择需求预规划');
        return;
    }
    if (!scheduleFormData.value.work_type) {
        MessagePlugin.warning('请选择工作项类型');
        return;
    }
    if (!scheduleFormData.value.username) {
        MessagePlugin.warning('请输入用户名');
        return;
    }
    if (!scheduleFormData.value.password) {
        MessagePlugin.warning('请输入密码');
        return;
    }

    scheduleLoading.value = true;
    try {
        const response = await autoScheduling({
            requirement_preplanning: scheduleFormData.value.requirement_preplanning,
            work_type: scheduleFormData.value.work_type,
            domain: scheduleFormData.value.domain,
            team: scheduleFormData.value.team,
            username: scheduleFormData.value.username,
            password: scheduleFormData.value.password,
        });

        if (response.code === 200) {
            MessagePlugin.success(response.message || '需求自动排期执行成功');
            scheduleDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '需求自动排期执行失败');
        }
    } catch (error) {
        console.error('需求自动排期失败:', error);
        MessagePlugin.error(error.message || '需求自动排期失败');
    } finally {
        scheduleLoading.value = false;
    }
};

// ===================== RDC 数据同步 =====================

const openSyncDialog = () => {
    syncFormData.value = {
        work_type: '产品需求',
        team: '',
        username: '',
        password: '',
    };
    syncDialogVisible.value = true;
};

const handleSyncCancel = () => {
    syncDialogVisible.value = false;
};

const handleSyncConfirm = async () => {
    const { username, password } = syncFormData.value;
    if (!username.trim() || !password.trim()) {
        MessagePlugin.warning('请填写工号和密码');
        return;
    }

    syncLoading.value = true;
    try {
        const response = await syncRdcData({
            work_type: syncFormData.value.work_type,
            username: syncFormData.value.username.trim(),
            password: syncFormData.value.password.trim(),
        });

        if (response.code === 200) {
            MessagePlugin.success(response.message || 'RDC 数据同步成功');
            syncDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || 'RDC 数据同步失败');
        }
    } catch (error) {
        console.error('RDC 数据同步失败:', error);
        MessagePlugin.error(error.message || 'RDC 数据同步失败');
    } finally {
        syncLoading.value = false;
    }
};

/* ==================== HAI 动作执行器 ==================== */

// 执行 HAI 传入的动作
const executeActions = async (actions) => {
    console.log('[HAI] Executing actions:', JSON.stringify(actions, null, 2))

    for (const action of actions) {
        console.log('[HAI] 当前动作:', JSON.stringify(action, null, 2))
        
        if (!action.name) {
            document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
            sendHAIResult('9999', '动作名称不能为空')
            return
        }

        switch (action.name) {
            case 'filter':
                await handleHAIFilter(action.args)
                break
            case 'editRequirement':
                await handleHAIEdit(action.args)
                break
            case 'syncFromRDC':
                await handleHAISync(action.args)
                break
            case 'autoSchedule':
                await handleHAIAutoSchedule(action.args)
                break
            case 'backfillToRDC':
                await handleHAIBackfill(action.args)
                break
            case 'exportData':
                await handleHAIExport(action.args)
                break
            default:
                document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
                sendHAIResult('9999', `不支持的动作: ${action.name}，支持的动作: filter, editRequirement, syncFromRDC, autoSchedule, backfillToRDC, exportData`)
                return
        }
    }
}

// HAI 动作：筛选
const handleHAIFilter = async (args) => {
    try {
        if (args.belong_product) filterForm.value.belong_product = args.belong_product
        if (args.product_roadmap) filterForm.value.product_roadmap = args.product_roadmap
        if (args.requirement_preplanning) filterForm.value.requirement_preplanning = args.requirement_preplanning
        if (args.domain) filterForm.value.domain = args.domain
        if (args.team) filterForm.value.team = args.team
        if (args.work_item_type) filterForm.value.work_item_type = args.work_item_type
        
        await loadData()
        
        document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
        sendHAIResult('0000', '筛选成功', {
            filter: filterForm.value,
            resultCount: tableData.value.length
        })
    } catch (error) {
        sendHAIResult('9999', `筛选失败: ${error.message}`)
    }
}

// HAI 动作：编辑需求
const handleHAIEdit = async (args) => {
    try {
        if (!args.id) {
            sendHAIResult('9999', '请提供需求ID')
            return
        }
        
        const targetRow = tableData.value.find(item => item.id == args.id)
        if (!targetRow) {
            sendHAIResult('9999', `未找到ID为 ${args.id} 的需求`)
            return
        }
        
        handleEdit(targetRow)
        
        if (args.fields && editDialogVisible.value) {
            if (args.fields.first_evaluation_conclusion !== undefined)
                editFormData.value.first_evaluation_conclusion = args.fields.first_evaluation_conclusion
            if (args.fields.estimated_dev_workload !== undefined)
                editFormData.value.estimated_dev_workload = args.fields.estimated_dev_workload
            if (args.fields.estimated_verification_workload !== undefined)
                editFormData.value.estimated_verification_workload = args.fields.estimated_verification_workload
            if (args.fields.estimated_system_test_workload !== undefined)
                editFormData.value.estimated_system_test_workload = args.fields.estimated_system_test_workload
            if (args.fields.plan_start_dev_date)
                editFormData.value.plan_start_dev_date = args.fields.plan_start_dev_date
            if (args.fields.plan_finish_dev_date)
                editFormData.value.plan_finish_dev_date = args.fields.plan_finish_dev_date
            if (args.fields.plan_delivery_date)
                editFormData.value.plan_delivery_date = args.fields.plan_delivery_date
        }
        
        if (args.autoSave) {
            await handleSaveEdit()
            sendHAIResult('0000', '编辑并保存成功', { id: targetRow.id })
        } else {
            document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
            sendHAIResult('0000', '编辑弹窗已打开', { id: targetRow.id })
        }
    } catch (error) {
        sendHAIResult('9999', `编辑失败: ${error.message}`)
    }
}

// HAI 动作：从RDC同步
const handleHAISync = async (args) => {
    try {
        syncFormData.value = {
            work_type: args.work_type || '产品需求',
            team: args.team || '',
            username: args.username || '',
            password: args.password || '',
        }
        
        if (!syncFormData.value.username || !syncFormData.value.password) {
            sendHAIResult('9999', '同步需要提供 username 和 password 参数')
            return
        }
        
        syncLoading.value = true
        const response = await syncRdcData({
            work_type: syncFormData.value.work_type,
            username: syncFormData.value.username,
            password: syncFormData.value.password,
        })
        
        if (response.code === 200) {
            await loadData()
            document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
            sendHAIResult('0000', 'RDC数据同步成功', { 
                work_type: syncFormData.value.work_type,
                syncedCount: response.data?.count || 0 
            })
        } else {
            sendHAIResult('9999', response.message || '同步失败')
        }
    } catch (error) {
        sendHAIResult('9999', `同步失败: ${error.message}`)
    } finally {
        syncLoading.value = false
    }
}

// HAI 动作：自动排期
const handleHAIAutoSchedule = async (args) => {
    try {
        if (!args.requirement_preplanning) {
            sendHAIResult('9999', '自动排期需要提供 requirement_preplanning 参数')
            return
        }
        if (!args.username || !args.password) {
            sendHAIResult('9999', '自动排期需要提供 username 和 password 参数')
            return
        }
        
        const scheduleParams = {
            requirement_preplanning: args.requirement_preplanning,
            work_type: args.work_type || '产品需求',
            domain: args.domain ? (Array.isArray(args.domain) ? args.domain : [args.domain]) : [],
            team: args.team ? (Array.isArray(args.team) ? args.team : [args.team]) : [],
            username: args.username,
            password: args.password,
        }
        
        scheduleLoading.value = true
        const response = await autoScheduling(scheduleParams)
        
        if (response.code === 200) {
            await loadData()
            document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
            sendHAIResult('0000', response.message || '需求自动排期执行成功', scheduleParams)
        } else {
            sendHAIResult('9999', response.message || '自动排期失败')
        }
    } catch (error) {
        sendHAIResult('9999', `自动排期失败: ${error.message}`)
    } finally {
        scheduleLoading.value = false
    }
}

// HAI 动作：回填到RDC
const handleHAIBackfill = async (args) => {
    try {
        if (!args.username || !args.password) {
            sendHAIResult('9999', '回填需要提供 username 和 password 参数')
            return
        }
        
        const backfillParams = {
            username: args.username,
            password: args.password,
            requirement_preplanning: args.requirement_preplanning || filterForm.value.requirement_preplanning || '',
            work_type: args.work_type || filterForm.value.work_item_type || '',
            domain: args.domain || filterForm.value.domain || '',
            team: args.team || filterForm.value.team || '',
        }
        
        backfillLoading.value = true
        const response = await backfillRdcData(backfillParams)
        
        if (response.code === 200) {
            document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
            sendHAIResult('0000', response.message || 'RDC数据回填成功', backfillParams)
        } else {
            sendHAIResult('9999', response.message || '回填失败')
        }
    } catch (error) {
        sendHAIResult('9999', `回填失败: ${error.message}`)
    } finally {
        backfillLoading.value = false
    }
}

// HAI 动作：导出数据
const handleHAIExport = async (args) => {
    try {
        await handleExport()
        document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
        sendHAIResult('0000', '导出成功', { 
            format: args.format || 'excel',
            dataCount: tableData.value.length 
        })
    } catch (error) {
        sendHAIResult('9999', `导出失败: ${error.message}`)
    }
}

// 处理 HAI 发来的消息
const handleHAIMessage = (event) => {
    console.log('[HAI] Received message:', JSON.stringify(event.data, null, 2))

    if (!event.data || !event.data.type) {
        return
    }

    if (event.data.type === 'HAI_TOOL_CALL_ARGS') {
        console.log('[HAI] 收到 HAI_TOOL_CALL_ARGS 消息')
        currentToolCall = event.data
        
        if (!event.data.delta) {
            sendHAIResult('9999', '缺少必要参数')
            return
        }

        try {
            const delta = JSON.parse(event.data.delta) || {}
            
            if (!delta.actions || !Array.isArray(delta.actions)) {
                sendHAIResult('9999', '缺少 actions 参数')
                return
            }

            if (delta.actions.length === 0) {
                sendHAIResult('9999', 'actions 不能为空')
                return
            }

            executeActions(delta.actions)
        } catch (e) {
            console.log('[HAI] 解析 delta 失败:', e)
            sendHAIResult('9999', '参数解析失败')
        }
    }
}

// 发送就绪信号并处理URL参数
const sendReadyAndHandleLoad = () => {
    if (_haiInIframe && !_haiHasIdParam) {
        document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: flex')
    }

    const urlId = getIdFromUrl()
    if (urlId) {
        document.getElementById('hai-loader-mask')?.setAttribute('style', 'display: none')
        setTimeout(() => {
            const targetRow = tableData.value.find(item => item.id == urlId)
            if (targetRow) {
                handleEdit(targetRow)
            }
        }, 500)
        return
    }

    if (_haiInIframe && !_haiHasIdParam) {
        const loaderText = document.getElementById('hai-loader-text')
        if (loaderText) {
            loaderText.innerText = '等待 HAI 连接...'
        }
        
        const readyMessage = {
            type: 'HAI_TOOL_CALL_READY',
            toolCallId: 'requirement_list_ready_id',
            toolCallName: 'WA_Dispatcher',
            timestamp: new Date().getTime(),
            rawEvent: null,
            data: null
        }
        sendHAIMessage(readyMessage)
    }
}
</script>

<style scoped>
.requirement-list-main {
    padding: 16px;
    background-color: #f5f5f9;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.add-form {
    padding: 16px 0;
    height: 500px;
    overflow-y: auto;
}

.requirement-list-main {
    table {
        border-collapse: collapse;
        white-space: pre-line;
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

    tr:nth-child(even) td {
        background-color: #f8f8f8;
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

:deep(.t-table__body) td {
    color: #555 !important;
}

:deep(.t-table__body) .t-table__cell {
    color: #555 !important;
}

:deep(.t-table__body) .t-table__cell-inner {
    color: #555 !important;
}

:deep(.t-table__body) .t-table__cell-inner * {
    color: #555 !important;
}

:deep(.t-table__body) .t-table__row .t-table__cell {
    color: #555 !important;
}

/* HAI 加载遮罩样式 */
#hai-loader-mask {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.95);
    z-index: 99999;
    display: none;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.hai-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #f0f0f0;
    border-top: 4px solid #1890ff;
    border-radius: 50%;
    animation: hai-spin 1s linear infinite;
    margin-bottom: 20px;
}

@keyframes hai-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
