<template>
    <div class="version-cases-main">
        <!-- 返回按钮和版本信息 -->
        <t-space direction="vertical" style="width: 100%; margin-bottom: 16px;">
            <t-button variant="text" theme="primary" @click="goBack">
                <template #icon><ChevronLeftIcon /></template>
                返回版本列表
            </t-button>
            <t-card v-if="versionInfo" :bordered="false">
                <template #header>
                    <span style="font-weight: 600;">版本基本信息</span>
                </template>
                <t-descriptions :column="4" :items="versionInfoItems" />
            </t-card>
            <div style="padding: 8px 0;">
                <span style="font-weight: 600;">该版本包含 <strong style="color: #0052d9;">{{ total }}</strong> 个案例</span>
            </div>
        </t-space>

        <!-- 查询/筛选区域 -->
        <t-space direction="vertical" style="width: 100%;">
            <t-space wrap>
                <t-input
                    v-model="queryParams.caseId"
                    placeholder="案例ID"
                    clearable
                    style="width: 150px;"
                    label="案例ID: "
                />
                <t-input
                    v-model="queryParams.caseTitle"
                    placeholder="案例标题"
                    clearable
                    style="width: 200px;"
                    label="案例标题: "
                />
                <t-select
                    v-model="queryParams.belongProject"
                    placeholder="归属项目"
                    clearable
                    filterable
                    allow-input
                    style="width: 150px;"
                    label="归属项目: "
                >
                    <t-option value="智能OTN" label="智能OTN" />
                    <t-option value="M721" label="M721" />
                    <t-option value="7000" label="7000" />
                </t-select>
                <t-input
                    v-model="queryParams.caseFoundSite"
                    placeholder="案例发现局点"
                    clearable
                    style="width: 150px;"
                    label="案例发现局点: "
                />
                <t-select
                    v-model="queryParams.priority"
                    placeholder="优先级"
                    clearable
                    style="width: 120px;"
                    label="优先级: "
                >
                    <t-option value="高" label="高" />
                    <t-option value="中" label="中" />
                    <t-option value="低" label="低" />
                </t-select>
                <t-input
                    v-model="queryParams.qualityTopic"
                    placeholder="关联质量专题"
                    clearable
                    style="width: 150px;"
                    label="关联质量专题: "
                />
                <t-input
                    v-model="queryParams.functionCategory"
                    placeholder="功能分类"
                    clearable
                    style="width: 150px;"
                    label="功能分类: "
                />
                <t-input
                    v-model="queryParams.component"
                    placeholder="单板"
                    clearable
                    style="width: 120px;"
                    label="单板: "
                />
                <t-button @click="filterData">查询</t-button>
                <t-button @click="resetFilters">重置</t-button>
            </t-space>
        </t-space>

        <!-- 案例清单表格 -->
        <t-table
            ref="tableRef"
            row-key="id"
            :columns="tableColumnList"
            :data="tableDataList"
            :bordered="true"
            :hover="true"
            resizable
            :loading="loading"
            :max-height="tableHeight"
            :pagination="paginationConfig"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
            @sort-change="handleSortChange"
        >
            <template #index="{ rowIndex }">
                <span>{{ (paginationConfig.current - 1) * paginationConfig.pageSize + rowIndex + 1 }}</span>
            </template>
        </t-table>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';
import { ChevronLeftIcon } from 'tdesign-icons-vue-next';
import { queryVersionCases, getVersionDetail } from '@/api/issueImpacte/version.js';

const router = useRouter();
const route = useRoute();
const user = useUserStore();

// 版本信息
const versionInfo = ref(null);
const versionId = computed(() => route.params.versionId);

// 版本信息描述项
const versionInfoItems = computed(() => {
    if (!versionInfo.value) return [];
    return [
        { label: '版本名称', content: versionInfo.value.versionName || '-' },
        { label: '归属项目', content: versionInfo.value.belongProject || '-' },
        { label: '发布时间', content: versionInfo.value.releaseTime || '-' },
        { label: '历史版本发布时间', content: versionInfo.value.historicalReleaseTime || '-' },
        { label: '目标网络', content: formatTargetNetwork(versionInfo.value.targetNetwork) },
        { label: '涉及单板', content: versionInfo.value.involvedBoards || '-' },
        { label: '版本分支', content: versionInfo.value.branch || '-' }
    ];
});

// 格式化目标网络显示
const formatTargetNetwork = (value) => {
    if (!value) return '-';
    if (Array.isArray(value)) {
        return value.join(',');
    }
    if (typeof value === 'string') {
        return value;
    }
    return '-';
};

// 表格配置（复用父页面的列配置，但不包含操作列）
const tableRef = ref();
const loading = ref(false);
const tableColumnList = [
    { colKey: 'index', title: '序号', width: '70', align: 'center' },
    { colKey: 'caseId', title: '案例ID', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'caseTitle', title: '案例标题', width: '250', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'belongProject', title: '归属项目', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'caseFoundSite', title: '案例发现局点', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'priority', title: '优先级', width: '100', align: 'center' },
    { colKey: 'qualityTopic', title: '关联质量专题', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'functionCategory', title: '功能分类', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'part', title: '单板', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'workItemId', title: '工作项ID', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'workItemType', title: '工作项类型', width: '120', align: 'center', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'caseOccurTime', title: '案例发生时间', width: '180', align: 'center', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'assignTo', title: '指派给', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'affectBusiness', title: '是否影响业务', width: '120', align: 'center', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'modifyFaultRecord', title: '修改故障入库记录', width: '180', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'needHorizontalPush', title: '是否需要横推', width: '120', align: 'center', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'horizontalPushTicket', title: '横推单', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'needNotice', title: '是否需要通告', width: '120', align: 'center', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'rdcNoticeTicket', title: 'RDC通告单', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'rdcReviewTicket', title: 'RDC复盘单', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    {
        colKey: 'status',
        title: '状态',
        width: '120',
        align: 'center',
        cell: (_, { row }) => {
            const statusMap = {
                '新建': 'default',
                '分析中': 'warning',
                '横推中': 'primary',
                '审批中': 'warning',
                '已完成': 'success',
                '已关闭': 'default'
            };
            return (<t-tag theme={statusMap[row.status] || 'default'} size="small">{row.status}</t-tag>);
        }
    }
];

// 数据
const tableDataList = ref([]);
const total = ref(0);

// 查询参数
const queryParams = ref({
    caseId: '',
    caseTitle: '',
    belongProject: '',
    caseFoundSite: '',
    priority: '',
    qualityTopic: '',
    functionCategory: '',
    component: ''
});

// 分页配置
const paginationConfig = ref({
    current: 1,
    pageSize: 20,
    total: 0,
    showJumper: true,
    showSizer: true,
    pageSizeOptions: [10, 20, 50, 100]
});

// 排序配置
const sortConfig = ref({
    sortBy: 'caseOccurTime',
    descending: true
});

// 表格高度
const tableHeight = ref('600px');

// 计算表格高度
const calculateTableHeight = () => {
    const offset = 400;
    tableHeight.value = `${window.innerHeight - offset}px`;
};

// 生命周期
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('用户信息缺失，请重新登录...');
        router.push('/login');
        return;
    }

    if (!versionId.value) {
        MessagePlugin.error('版本ID缺失');
        router.push('/ai/issueImpacte/version');
        return;
    }

    calculateTableHeight();
    window.addEventListener('resize', calculateTableHeight);
    
    // 加载版本信息和案例列表
    await loadVersionInfo();
    await loadData();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载版本信息
const loadVersionInfo = async () => {
    try {
        const responseData = await getVersionDetail(versionId.value);
        if (responseData.status === 'success' || responseData.code === 200) {
            versionInfo.value = responseData.data || {};
        } else {
            MessagePlugin.error(responseData.message || '获取版本信息失败');
        }
    } catch (error) {
        console.error('加载版本信息失败:', error);
        MessagePlugin.error('加载版本信息失败');
    }
};

// 加载数据
const loadData = async () => {
    try {
        loading.value = true;
        const requestData = {
            user: user.userInfo.name || 'guest',
            page: paginationConfig.value.current,
            pageSize: paginationConfig.value.pageSize,
            sortBy: sortConfig.value.sortBy,
            descending: sortConfig.value.descending,
            conditions: {
                ...queryParams.value
            }
        };

        const responseData = await queryVersionCases(versionId.value, requestData);
        
        if (responseData.status !== 'success' && responseData.code !== 200) {
            throw new Error(responseData.message || '读取数据失败');
        }

        tableDataList.value = (responseData.data || []).map((item, index) => ({
            id: item.caseId || `case_${index}`,
            ...item
        }));

        total.value = responseData.total || 0;
        paginationConfig.value.total = total.value;

        MessagePlugin.success('数据加载成功');
    } catch (error) {
        console.error('数据加载失败:', error);
        MessagePlugin.error(error.message || '数据加载失败');
    } finally {
        loading.value = false;
    }
};

// 筛选数据
const filterData = async () => {
    paginationConfig.value.current = 1;
    await loadData();
};

// 重置筛选
const resetFilters = () => {
    queryParams.value = {
        caseId: '',
        caseTitle: '',
        belongProject: '',
        caseFoundSite: '',
        priority: '',
        qualityTopic: '',
        functionCategory: '',
        component: ''
    };
    filterData();
    MessagePlugin.info('已重置筛选条件');
};

// 分页变化
const handlePageChange = (pageInfo) => {
    paginationConfig.value.current = pageInfo.current;
    loadData();
};

// 每页条数变化
const handlePageSizeChange = (pageInfo) => {
    paginationConfig.value.pageSize = pageInfo.pageSize;
    paginationConfig.value.current = 1;
    loadData();
};

// 排序变化
const handleSortChange = (sortInfo) => {
    if (sortInfo.length > 0) {
        sortConfig.value.sortBy = sortInfo[0].sortBy;
        sortConfig.value.descending = sortInfo[0].descending;
    }
    loadData();
};

// 返回版本列表
const goBack = () => {
    router.push('/ai/issueImpacte/version');
};
</script>

<style scoped>
.version-cases-main {
    padding: 16px;
}

.version-cases-main :deep(.t-descriptions__label) {
    font-weight: 600;
}
</style>
