<template>
    <div class="version-main">
        <!-- 查询/筛选区域 -->
        <t-space wrap style="width: 100%;">
            <t-input
                v-model="queryParams.versionName"
                placeholder="版本名称"
                clearable
                style="width: 150px;"
                label="版本名称: "
            />
            <t-date-picker
                v-model="queryParams.releaseTime"
                placeholder="发布时间"
                clearable
                style="width: 150px;"
                format="YYYY-MM-DD"
                label="发布时间: "
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
            <t-select
                v-model="queryParams.targetNetwork"
                placeholder="目标网络"
                clearable
                filterable
                allow-input
                multiple
                style="width: 200px;"
                label="目标网络: "
            >
                <t-option
                    v-for="item in targetNetworkOptions"
                    :key="item"
                    :value="item"
                    :label="item"
                />
            </t-select>
            <t-select
                v-model="queryParams.boards"
                placeholder="单板"
                clearable
                filterable
                allow-input
                multiple
                style="width: 200px;"
                label="单板: "
            >
                <t-option
                    v-for="item in boardOptions"
                    :key="item"
                    :value="item"
                    :label="item"
                />
            </t-select>
            <t-select
                v-model="queryParams.branch"
                placeholder="分支"
                clearable
                filterable
                allow-input
                style="width: 150px;"
                label="分支: "
            >
                <t-option
                    v-for="item in branchOptions"
                    :key="item"
                    :value="item"
                    :label="item"
                />
            </t-select>
        </t-space>

        <!-- 按钮区域 -->
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 16px;">
            <t-space>
                <t-button theme="primary" @click="filterData">
                    <template #icon><SearchIcon /></template>
                    查询
                </t-button>
                <t-button @click="resetFilters">重置</t-button>
            </t-space>
            <t-button theme="primary" @click="openAddDialog">
                <template #icon><AddIcon /></template>
                新建版本
            </t-button>
        </div>

        <!-- 统计信息 -->
        <div style="padding: 16px 0;">
            <span v-if="total > 0">共 {{ total }} 个版本</span>
            <span v-else>暂无数据</span>
        </div>

        <!-- 版本列表表格 -->
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
            <template #targetNetwork="{ row }">
                <span>{{ formatTargetNetwork(row.targetNetwork) }}</span>
            </template>
            <template #involvedBoards="{ row }">
                <span>{{ row.involvedBoards || '-' }}</span>
            </template>
            <template #branch="{ row }">
                <span>{{ row.branch || '-' }}</span>
            </template>
        </t-table>

        <!-- 新建版本对话框 -->
        <t-dialog
            v-model:visible="addDialogVisible"
            :width="800"
            theme="warning">
            <template #header>
                <span>新建版本</span>
            </template>
            <div class="add-form">
                <t-form ref="addFormRef" :data="dialogFormData" layout="vertical">
                    <t-form-item label="* 版本名称" name="versionName">
                        <t-input
                            v-model="dialogFormData.versionName"
                            placeholder="请输入版本名称"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="归属项目" name="belongProject">
                        <t-select
                            v-model="dialogFormData.belongProject"
                            placeholder="请选择归属项目"
                            filterable
                            allow-input
                            clearable
                        >
                            <t-option
                                v-for="item in belongProjectOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 发布时间" name="releaseTime">
                        <t-date-picker
                            v-model="dialogFormData.releaseTime"
                            placeholder="请选择发布时间"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="* 历史版本发布时间" name="historicalReleaseTime">
                        <t-date-picker
                            v-model="dialogFormData.historicalReleaseTime"
                            placeholder="请选择历史版本发布时间"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="目标网络" name="targetNetwork">
                        <t-select
                            v-model="dialogFormData.targetNetwork"
                            placeholder="请选择或输入目标网络（可多选）"
                            filterable
                            creatable
                            clearable
                            multiple
                            @create="handleTargetNetworkCreate"
                        >
                            <t-option
                                v-for="item in targetNetworkOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 涉及单板" name="involvedBoards">
                        <t-select
                            v-model="dialogFormData.involvedBoards"
                            placeholder="请选择或输入涉及单板（可多选）"
                            filterable
                            creatable
                            clearable
                            multiple
                            @create="handleBoardCreate"
                        >
                            <t-option
                                v-for="item in boardOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 版本分支" name="branch">
                        <t-select
                            v-model="dialogFormData.branch"
                            placeholder="请选择或输入版本分支"
                            filterable
                            creatable
                            clearable
                            @create="handleBranchCreate"
                        >
                            <t-option
                                v-for="item in branchOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleAddCancel">取消</t-button>
                <t-button theme="primary" @click="handleAddConfirm">提交</t-button>
            </template>
        </t-dialog>

        <!-- 编辑版本对话框 -->
        <t-dialog
            v-model:visible="editDialogVisible"
            :width="800"
            theme="warning">
            <template #header>
                <span>编辑版本</span>
            </template>
            <div class="edit-form">
                <t-form ref="editFormRef" :data="dialogFormData" layout="vertical">
                    <t-form-item label="* 版本名称" name="versionName">
                        <t-input
                            v-model="dialogFormData.versionName"
                            placeholder="请输入版本名称"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="归属项目" name="belongProject">
                        <t-select
                            v-model="dialogFormData.belongProject"
                            placeholder="请选择归属项目"
                            filterable
                            allow-input
                            clearable
                        >
                            <t-option
                                v-for="item in belongProjectOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 发布时间" name="releaseTime">
                        <t-date-picker
                            v-model="dialogFormData.releaseTime"
                            placeholder="请选择发布时间"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="* 历史版本发布时间" name="historicalReleaseTime">
                        <t-date-picker
                            v-model="dialogFormData.historicalReleaseTime"
                            placeholder="请选择历史版本发布时间"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="目标网络" name="targetNetwork">
                        <t-select
                            v-model="dialogFormData.targetNetwork"
                            placeholder="请选择或输入目标网络（可多选）"
                            filterable
                            creatable
                            clearable
                            multiple
                            @create="handleTargetNetworkCreate"
                        >
                            <t-option
                                v-for="item in targetNetworkOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 涉及单板" name="involvedBoards">
                        <t-select
                            v-model="dialogFormData.involvedBoards"
                            placeholder="请选择或输入涉及单板（可多选）"
                            filterable
                            creatable
                            clearable
                            multiple
                            @create="handleBoardCreate"
                        >
                            <t-option
                                v-for="item in boardOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 版本分支" name="branch">
                        <t-select
                            v-model="dialogFormData.branch"
                            placeholder="请选择或输入版本分支"
                            filterable
                            creatable
                            clearable
                            @create="handleBranchCreate"
                        >
                            <t-option
                                v-for="item in branchOptions"
                                :key="item"
                                :value="item"
                                :label="item"
                            />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleEditCancel">取消</t-button>
                <t-button theme="primary" @click="handleEditConfirm">提交</t-button>
            </template>
        </t-dialog>

        <!-- 删除确认对话框 -->
        <t-dialog
            v-model:visible="deleteDialogVisible"
            :width="500"
            theme="warning">
            <template #header>
                <span>删除版本</span>
            </template>
            <div class="delete-content">
                <p>确定要删除版本 <strong>{{ deleteRowData.versionName }}</strong> 吗？</p>
                <p>该版本关联了 <strong>{{ deleteRowData.caseCount || 0 }}</strong> 个案例。</p>
                <p style="color: #999; font-size: 12px;">删除后关联关系会保留，但版本记录将被删除。</p>
            </div>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" @click="handleDeleteConfirm">确认删除</t-button>
            </template>
        </t-dialog>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';
import { SearchIcon, AddIcon } from 'tdesign-icons-vue-next';
import { 
    queryVersion,
    createVersion,
    updateVersion,
    deleteVersion,
    getTargetNetworkOptions,
    getBoardOptions,
    getBranchOptions
} from '@/api/issueImpacte/version.js';

const router = useRouter();
const user = useUserStore();

// 表格配置
const tableRef = ref();
const loading = ref(false);
const tableColumnList = [
    { colKey: 'index', title: '#', width: '70', align: 'center' },
    { colKey: 'versionName', title: '版本名称', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, sorter: true },
    { colKey: 'belongProject', title: '归属项目', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'releaseTime', title: '发布时间', width: '150', align: 'center', sorter: true },
    { colKey: 'historicalReleaseTime', title: '历史版本发布时间', width: '180', align: 'center', sorter: true },
    { colKey: 'targetNetwork', title: '目标网络', width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'involvedBoards', title: '涉及单板', width: '250', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'branch', title: '版本分支', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    {
        colKey: 'operation',
        title: '操作',
        width: '200',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (
            <>
                <t-link theme="primary" hover="color" onClick={() => viewVersionCases(row)} style={{ marginRight: '8px' }}>版本清单</t-link>
                <t-link theme="primary" hover="color" onClick={() => openEditDialog(row)} style={{ marginRight: '8px' }}>编辑</t-link>
                <t-link theme="danger" hover="color" onClick={() => openDeleteDialog(row)}>删除</t-link>
            </>
        )
    }
];

// 数据
const tableDataList = ref([]);
const total = ref(0);

// 查询参数
const queryParams = ref({
    versionName: '',
    releaseTime: '',
    belongProject: '',
    targetNetwork: [],
    boards: [],
    branch: ''
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
    sortBy: 'releaseTime',
    descending: true
});

// 对话框相关
const addDialogVisible = ref(false);
const editDialogVisible = ref(false);
const deleteDialogVisible = ref(false);
const addFormRef = ref(null);
const editFormRef = ref(null);
const currentEditId = ref(null);
const deleteRowData = ref({});

// 表单数据
const dialogFormData = ref({
    versionName: '',
    belongProject: '',
    releaseTime: '',
    historicalReleaseTime: '',
    targetNetwork: [],
    involvedBoards: [],
    branch: ''
});

// 下拉选项
const targetNetworkOptions = ref([]);
const boardOptions = ref([]);
const branchOptions = ref([]);
// 归属项目固定选项
const belongProjectOptions = ['智能OTN', 'M721', '7000'];

// 表格高度
const tableHeight = ref('600px');

// 格式化目标网络显示（数组转逗号分隔字符串）
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

// 计算表格高度
const calculateTableHeight = () => {
    const offset = 280;
    tableHeight.value = `${window.innerHeight - offset}px`;
};

// 生命周期
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('用户信息缺失，请重新登录...');
        router.push('/login');
        return;
    }

    calculateTableHeight();
    window.addEventListener('resize', calculateTableHeight);
    
    // 加载下拉选项
    await loadOptions();
    await loadData();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载下拉选项
const loadOptions = async () => {
    try {
        const [targetNetworkRes, boardRes, branchRes] = await Promise.all([
            getTargetNetworkOptions(),
            getBoardOptions(),
            getBranchOptions()
        ]);

        if (targetNetworkRes.status === 'success' || targetNetworkRes.code === 200) {
            const backendOptions = targetNetworkRes.data || [];
            // 从 localStorage 读取自定义输入的值
            const savedOptions = JSON.parse(localStorage.getItem('targetNetworkOptions') || '[]');
            // 合并后端选项和本地保存的选项，去重
            targetNetworkOptions.value = [...new Set([...backendOptions, ...savedOptions])];
        }
        if (boardRes.status === 'success' || boardRes.code === 200) {
            const backendOptions = boardRes.data || [];
            // 从 localStorage 读取自定义输入的值
            const savedOptions = JSON.parse(localStorage.getItem('boardOptions') || '[]');
            // 合并后端选项和本地保存的选项，去重
            boardOptions.value = [...new Set([...backendOptions, ...savedOptions])];
        }
        if (branchRes.status === 'success' || branchRes.code === 200) {
            branchOptions.value = branchRes.data || [];
        }
    } catch (error) {
        console.error('加载下拉选项失败:', error);
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

        // 处理数组字段
        if (Array.isArray(requestData.conditions.targetNetwork) && requestData.conditions.targetNetwork.length > 0) {
            requestData.conditions.targetNetwork = requestData.conditions.targetNetwork.join(',');
        }
        if (Array.isArray(requestData.conditions.boards) && requestData.conditions.boards.length > 0) {
            requestData.conditions.boards = requestData.conditions.boards.join(',');
        }

        const responseData = await queryVersion(requestData);
        
        if (responseData.status !== 'success' && responseData.code !== 200) {
            throw new Error(responseData.message || '读取数据失败');
        }

        tableDataList.value = (responseData.data || []).map((item, index) => ({
            id: item.versionId || item.id || `version_${index}`,
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
        versionName: '',
        releaseTime: '',
        belongProject: '',
        targetNetwork: [],
        boards: [],
        branch: ''
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

// 打开新增对话框
const openAddDialog = async () => {
    // 重新加载分支选项（获取最新历史输入）
    try {
        const branchRes = await getBranchOptions();
        if (branchRes.status === 'success' || branchRes.code === 200) {
            branchOptions.value = branchRes.data || [];
        }
    } catch (error) {
        console.error('加载分支选项失败:', error);
    }

    dialogFormData.value = {
        versionName: '',
        belongProject: '',
        releaseTime: '',
        historicalReleaseTime: '',
        targetNetwork: [],
        involvedBoards: [],
        branch: ''
    };
    addDialogVisible.value = true;
};

// 确认新增
const handleAddConfirm = async () => {
    // 验证必填项
    if (!dialogFormData.value.versionName) {
        MessagePlugin.warning('请输入版本名称');
        return;
    }
    if (!dialogFormData.value.releaseTime) {
        MessagePlugin.warning('请选择发布时间');
        return;
    }
    if (!dialogFormData.value.historicalReleaseTime) {
        MessagePlugin.warning('请选择历史版本发布时间');
        return;
    }
    if (!dialogFormData.value.involvedBoards || (Array.isArray(dialogFormData.value.involvedBoards) && dialogFormData.value.involvedBoards.length === 0)) {
        MessagePlugin.warning('请选择涉及单板');
        return;
    }
    if (!dialogFormData.value.branch) {
        MessagePlugin.warning('请输入版本分支');
        return;
    }

    try {
        loading.value = true;
        const submitData = { ...dialogFormData.value };
        
        // 将数组转换为逗号分隔的字符串
        if (Array.isArray(submitData.targetNetwork)) {
            submitData.targetNetwork = submitData.targetNetwork.join(',');
        }
        if (Array.isArray(submitData.involvedBoards)) {
            submitData.involvedBoards = submitData.involvedBoards.join(',');
        }

        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: submitData
        };

        const responseData = await createVersion(requestData);
        
        if (responseData.status !== 'success' && responseData.code !== 200) {
            throw new Error(responseData.message || '新增失败');
        }
        
        // 如果手动输入了新的版本分支，将其添加到选项列表中
        if (submitData.branch && !branchOptions.value.includes(submitData.branch)) {
            branchOptions.value.push(submitData.branch);
        }
        
        MessagePlugin.success('新增版本成功');
        addDialogVisible.value = false;
        await loadData();
    } catch (error) {
        console.error('新增失败:', error);
        MessagePlugin.error(error.message || '新增失败');
    } finally {
        loading.value = false;
    }
};

// 取消新增
const handleAddCancel = () => {
    addDialogVisible.value = false;
};

// 打开编辑对话框
const openEditDialog = async (row) => {
    // 重新加载分支选项（获取最新历史输入）
    try {
        const branchRes = await getBranchOptions();
        if (branchRes.status === 'success' || branchRes.code === 200) {
            branchOptions.value = branchRes.data || [];
        }
    } catch (error) {
        console.error('加载分支选项失败:', error);
    }

    currentEditId.value = row.id;
    dialogFormData.value = { ...row };
    
    // 将字符串转换为数组
    if (typeof dialogFormData.value.targetNetwork === 'string') {
        dialogFormData.value.targetNetwork = dialogFormData.value.targetNetwork.split(',').map(item => item.trim()).filter(item => item);
    } else if (!Array.isArray(dialogFormData.value.targetNetwork)) {
        dialogFormData.value.targetNetwork = [];
    }
    
    if (typeof dialogFormData.value.involvedBoards === 'string') {
        dialogFormData.value.involvedBoards = dialogFormData.value.involvedBoards.split(',').map(item => item.trim()).filter(item => item);
    } else if (!Array.isArray(dialogFormData.value.involvedBoards)) {
        dialogFormData.value.involvedBoards = [];
    }
    
    editDialogVisible.value = true;
};

// 确认编辑
const handleEditConfirm = async () => {
    // 验证必填项
    if (!dialogFormData.value.versionName) {
        MessagePlugin.warning('请输入版本名称');
        return;
    }
    if (!dialogFormData.value.releaseTime) {
        MessagePlugin.warning('请选择发布时间');
        return;
    }
    if (!dialogFormData.value.historicalReleaseTime) {
        MessagePlugin.warning('请选择历史版本发布时间');
        return;
    }
    if (!dialogFormData.value.involvedBoards || (Array.isArray(dialogFormData.value.involvedBoards) && dialogFormData.value.involvedBoards.length === 0)) {
        MessagePlugin.warning('请选择涉及单板');
        return;
    }
    if (!dialogFormData.value.branch) {
        MessagePlugin.warning('请输入版本分支');
        return;
    }

    try {
        loading.value = true;
        const submitData = { ...dialogFormData.value };
        
        // 将数组转换为逗号分隔的字符串
        if (Array.isArray(submitData.targetNetwork)) {
            submitData.targetNetwork = submitData.targetNetwork.join(',');
        }
        if (Array.isArray(submitData.involvedBoards)) {
            submitData.involvedBoards = submitData.involvedBoards.join(',');
        }

        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: {
                versionId: dialogFormData.value.versionId || dialogFormData.value.id,
                ...submitData
            }
        };

        const responseData = await updateVersion(requestData);
        
        if (responseData.status !== 'success' && responseData.code !== 200) {
            throw new Error(responseData.message || '更新失败');
        }

        // 如果手动输入了新的版本分支，将其添加到选项列表中
        if (submitData.branch && !branchOptions.value.includes(submitData.branch)) {
            branchOptions.value.push(submitData.branch);
        }

        MessagePlugin.success('更新版本成功');
        editDialogVisible.value = false;
        await loadData();
    } catch (error) {
        console.error('更新失败:', error);
        MessagePlugin.error(error.message || '更新失败');
    } finally {
        loading.value = false;
    }
};

// 取消编辑
const handleEditCancel = () => {
    editDialogVisible.value = false;
};

// 打开删除对话框
const openDeleteDialog = (row) => {
    deleteRowData.value = { ...row };
    deleteDialogVisible.value = true;
};

// 确认删除
const handleDeleteConfirm = async () => {
    try {
        loading.value = true;
        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: {
                versionId: deleteRowData.value.versionId || deleteRowData.value.id
            }
        };

        const responseData = await deleteVersion(requestData);
        
        if (responseData.status !== 'success' && responseData.code !== 200) {
            throw new Error(responseData.message || '删除失败');
        }

        MessagePlugin.success('删除成功');
        deleteDialogVisible.value = false;
        await loadData();
    } catch (error) {
        console.error('删除失败:', error);
        MessagePlugin.error(error.message || '删除失败');
    } finally {
        loading.value = false;
    }
};

// 处理版本分支创建（手动输入新值）
const handleBranchCreate = (value) => {
    // 将新输入的值添加到选项列表中
    if (value && !branchOptions.value.includes(value)) {
        branchOptions.value.push(value);
    }
};

// 处理目标网络创建（手动输入新值）
const handleTargetNetworkCreate = (value) => {
    // 将新输入的值添加到选项列表中
    if (value && !targetNetworkOptions.value.includes(value)) {
        targetNetworkOptions.value.push(value);
        // 保存到 localStorage
        const savedOptions = JSON.parse(localStorage.getItem('targetNetworkOptions') || '[]');
        if (!savedOptions.includes(value)) {
            savedOptions.push(value);
            localStorage.setItem('targetNetworkOptions', JSON.stringify(savedOptions));
        }
    }
};

// 处理涉及单板创建（手动输入新值）
const handleBoardCreate = (value) => {
    // 将新输入的值添加到选项列表中
    if (value && !boardOptions.value.includes(value)) {
        boardOptions.value.push(value);
        // 保存到 localStorage
        const savedOptions = JSON.parse(localStorage.getItem('boardOptions') || '[]');
        if (!savedOptions.includes(value)) {
            savedOptions.push(value);
            localStorage.setItem('boardOptions', JSON.stringify(savedOptions));
        }
    }
};

// 查看版本案例详情
const viewVersionCases = (row) => {
    const versionId = row.versionId || row.id;
    router.push(`/ai/issueImpacte/version/${versionId}/cases`);
};
</script>

<style scoped>
.version-main {
    padding: 16px;
}

.add-form,
.edit-form {
    padding: 16px 0;
    max-height: 500px;
    overflow-y: auto;
}

.delete-content {
    padding: 16px 0;
}

.delete-content p {
    margin: 8px 0;
}

.delete-content strong {
    color: #0052d9;
}
</style>
