<template>
    <div class="scene-main">
        <t-space direction="vertical" style="width: 100%">
            <!-- 筛选区域 -->
            <t-space :size="16" style="flex-wrap: wrap">
                <t-select
                    v-model="queryParams.department"
                    placeholder="请选择部门"
                    clearable
                    style="width: 150px;"
                    label="部门: "
                    :options="departmentOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.domain"
                    placeholder="请选择领域"
                    clearable
                    style="width: 150px;"
                    label="领域: "
                    :options="domainOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.team"
                    placeholder="请选择团队"
                    clearable
                    multiple
                    style="width: 200px;"
                    label="团队: "
                    :options="teamOptions"
                    filterable
                />
                <t-input
                    v-model="queryParams.year"
                    placeholder="年份（如2026）"
                    clearable
                    style="width: 150px;"
                    label="年: "
                />
                <t-input
                    v-model="queryParams.employee_id"
                    placeholder="请输入工号"
                    clearable
                    style="width: 150px;"
                    label="工号: "
                />
                <t-input
                    v-model="queryParams.name"
                    placeholder="请输入姓名"
                    clearable
                    style="width: 150px;"
                    label="姓名: "
                />
            </t-space>
            
            <!-- 按钮区域 -->
            <t-space style="justify-content: flex-start;">
                <t-button @click="handleQuery">查询</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button :loading="exportLoading" @click="handleExport">批量导出</t-button>
                <t-button :loading="syncLoading" @click="handleSync">同步数据</t-button>
                <t-button theme="danger" @click="onBatchDelete">批量删除</t-button>
            </t-space>
        </t-space>
        
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
            @column-resize-end="onColumnResizeEnd">
            <template #demand_human_power_ratio="{ row }">
                {{ formatRatio(row.demand_human_power_ratio) }}
            </template>
        </t-table>

        <!-- 批量导入对话框 -->
        <t-dialog
            v-model:visible="importDialogVisible"
            :width="620"
            theme="warning"
            :header="importPhase === 'select' ? '批量导入数据' : '导入结果'">
            <!-- 选择文件阶段 -->
            <div v-if="importPhase === 'select'" class="import-container">
                <t-upload
                    ref="uploadRef"
                    :key="uploadKey"
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :file-list="fileList"
                    :max-size="10 * 1024 * 1024"
                    :allow-multiple="false"
                    accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    class="upload-component">
                    <t-button variant="outline">选择XLSX文件</t-button>
                </t-upload>

                <div v-if="fileList.length > 0" class="file-info">
                    <p>已选择文件: {{ fileList[0].name }}</p>
                    <p class="file-size">文件大小: {{ formatFileSize(fileList[0].size) }}</p>
                </div>
                <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
                <div class="example-download">
                    <t-space wrap="false" class="example-space">
                        <p>请按照示例文件格式填写数据</p>
                        <t-button
                            variant="text"
                            theme="primary"
                            class="example-btn"
                            @click="downloadExampleFile">
                            <t-icon name="download" size="16" class="mr-1" />
                            下载导入示例文件
                        </t-button>
                    </t-space>
                </div>
                <div class="psm-tip">
                    <t-icon name="info-circle" size="14" />
                    <span>导入时会自动校验工号和技能分类是否存在于<b>01 人员技能地图</b>中，不符合的行将被跳过</span>
                </div>
            </div>

            <!-- 结果展示阶段 -->
            <div v-else class="import-result-container">
                <div class="result-summary">
                    <t-icon name="check-circle" size="20" style="color: #07c160; margin-right: 8px;" />
                    <span>{{ importResultMsg }}</span>
                </div>
                <div v-if="importResult && importResult.failed_rows && importResult.failed_rows.length > 0" class="failed-info">
                    <t-alert
                        theme="warning"
                        :message="`有 ${importResult.failed_rows.length} 行因校验失败被跳过（工号不在人员技能地图中，或技能分类不符）`"
                        style="margin: 12px 0;" />
                    <div class="failed-detail">
                        <p class="failed-tip">请下载失败数据，先在 <b>01 人员技能地图</b> 中补充对应记录后重新导入：</p>
                        <t-button theme="warning" variant="outline" @click="downloadFailedRows">
                            <t-icon name="download" size="16" class="mr-1" />
                            下载失败数据（{{ importResult.failed_rows.length }} 行）
                        </t-button>
                    </div>
                </div>
                <div v-if="importResult && importResult.errors && importResult.errors.length > 0" class="error-list">
                    <p style="color: #e34d59; font-size: 13px; margin-bottom: 4px;">其他错误详情：</p>
                    <ul style="max-height: 120px; overflow-y: auto; font-size: 12px; color: #666; padding-left: 16px;">
                        <li v-for="(err, idx) in importResult.errors.slice(0, 20)" :key="idx">{{ err }}</li>
                    </ul>
                </div>
            </div>

            <template #footer>
                <template v-if="importPhase === 'select'">
                    <t-button @click="cancelImportSubmit">取消</t-button>
                    <t-button :loading="importLoading" @click="handleImportSubmit">确认导入</t-button>
                </template>
                <template v-else>
                    <t-button @click="closeImportDialog">关闭</t-button>
                    <t-button theme="primary" @click="resetImportToSelect">继续导入</t-button>
                </template>
            </template>
        </t-dialog>

        <!-- 删除确认对话框 -->
        <t-dialog
            v-model:visible="deleteDialogVisible"
            :width="420"
            theme="danger"
            header="确认删除">
            <p style="margin: 0;">确定要删除该条记录吗？此操作不可恢复。</p>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" :loading="deleteLoading" @click="handleDeleteSubmit">确认删除</t-button>
            </template>
        </t-dialog>

        <!-- 批量删除确认对话框 -->
        <t-dialog
            v-model:visible="batchDeleteDialogVisible"
            :width="480"
            theme="danger"
            header="批量删除">
            <div style="padding: 8px 0;">
                <p style="margin: 0 0 12px;">将根据筛选条件批量删除记录，此操作不可恢复。</p>
                <t-form layout="inline">
                    <t-form-item label="团队">
                        <t-select
                            v-model="batchDeleteParams.team"
                            placeholder="请选择团队"
                            clearable
                            multiple
                            style="width: 300px;"
                            :options="teamOptions"
                            filterable
                        />
                    </t-form-item>
                    <t-form-item label="工号">
                        <t-select
                            v-model="batchDeleteParams.employee_id"
                            placeholder="请输入工号"
                            clearable
                            multiple
                            style="width: 300px;"
                            filterable
                            creatable
                        />
                    </t-form-item>
                </t-form>
                <t-alert
                    v-if="batchDeleteConditionDesc"
                    :message="batchDeleteConditionDesc"
                    theme="warning"
                    style="margin-top: 12px;"
                />
                <t-alert
                    v-if="!batchDeleteConditionDesc"
                    message="请至少选择一个团队或输入一个工号作为删除条件"
                    theme="error"
                    style="margin-top: 12px;"
                />
            </div>
            <template #footer>
                <t-button @click="batchDeleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" :disabled="!batchDeleteConditionDesc" :loading="batchDeleteLoading" @click="handleBatchDeleteSubmit">确认删除</t-button>
            </template>
        </t-dialog>

        <!-- 编辑对话框 -->
        <t-dialog
            v-model:visible="editDialogVisible"
            :width="500"
            header="编辑需求人力占比">
            <div class="dialog-form">
                <t-form
                    ref="editFormRef"
                    :data="editFormData"
                    :rules="editFormRules"
                    layout="vertical">
                    <t-form-item label="需求人力占比" name="demand_human_power_ratio">
                        <t-input-number
                            v-model="editFormData.demand_human_power_ratio"
                            placeholder="请输入需求人力占比（0~1）"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            :decimal-places="2"
                        />
                        <div class="form-tip">范围：0~1，保留2位小数</div>
                    </t-form-item>
                    <t-form-item label="ZXONE 19700" name="zxone_19700">
                        <t-input-number
                            v-model="editFormData.zxone_19700"
                            placeholder="请输入ZXONE 19700（0~1）"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            :decimal-places="2"
                        />
                        <div class="form-tip">范围：0~1，保留2位小数</div>
                    </t-form-item>
                    <t-form-item label="ZXONE 9700" name="zxone_9700">
                        <t-input-number
                            v-model="editFormData.zxone_9700"
                            placeholder="请输入ZXONE 9700（0~1）"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            :decimal-places="2"
                        />
                        <div class="form-tip">范围：0~1，保留2位小数</div>
                    </t-form-item>
                    <t-form-item label="ZXMP M721" name="zxmp_m721">
                        <t-input-number
                            v-model="editFormData.zxmp_m721"
                            placeholder="请输入ZXMP M21（0~1）"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            :decimal-places="2"
                        />
                        <div class="form-tip">范围：0~1，保留2位小数</div>
                    </t-form-item>
                    <t-form-item label="ZXONE NTON" name="zxone_nton">
                        <t-input-number
                            v-model="editFormData.zxone_nton"
                            placeholder="请输入ZXONE NTON（0~1）"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            :decimal-places="2"
                        />
                        <div class="form-tip">范围：0~1，保留2位小数</div>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleCancelEdit">取消</t-button>
                <t-button :loading="editSaving" @click="handleSaveEdit">确认</t-button>
            </template>
        </t-dialog>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import {
    queryHumanResourceSettingByParams,
    updateHumanResourceSetting,
    deleteHumanResourceSetting,
    batchDeleteHumanResourceSetting,
    getHumanResourceSettingOptions,
    exportHumanResourceSetting,
    importHumanResourceSetting,
    triggerSyncRequirementDevHumanResource
} from '@/api/humanResourceSetting.js';
import * as XLSX from 'xlsx';

const user = useUserStore();

// 表格配置
const tableRef = ref();
const loading = ref(false);
const tableColumnList = ref([
    { colKey: 'id', title: 'ID', width: 80, align: 'center', resizable: true },
    { colKey: 'department', title: '部门', width: 120, align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, resizable: true },
    { colKey: 'domain', title: '领域', width: 150, align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, resizable: true },
    { colKey: 'team', title: '团队', width: 150, align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, resizable: true },
    { colKey: 'person_belong', title: '人员归属', width: 120, align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, resizable: true },
    { colKey: 'employee_id', title: '工号', width: 120, align: 'center', resizable: true },
    { colKey: 'name', title: '姓名', width: 100, align: 'left', resizable: true },
    { colKey: 'leave_time', title: '离职时间', width: 150, align: 'center', resizable: true },
    { colKey: 'skill_category', title: '技能/特性分类', width: 200, align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, resizable: true },
    { colKey: 'year_month', title: '年月', width: 100, align: 'center', resizable: true },
    { 
        colKey: 'demand_human_power_ratio', 
        title: '需求人力占比', 
        width: 150, 
        align: 'right',
        resizable: true,
        cell: (_, { row }) => formatRatio(row.demand_human_power_ratio)
    },
    { 
        colKey: 'zxone_19700', 
        title: 'ZXONE 19700', 
        width: 150, 
        align: 'right',
        resizable: true,
        cell: (_, { row }) => formatNumber(row.zxone_19700)
    },
    { 
        colKey: 'zxone_9700', 
        title: 'ZXONE 9700', 
        width: 150, 
        align: 'right',
        resizable: true,
        cell: (_, { row }) => formatNumber(row.zxone_9700)
    },
    { 
        colKey: 'zxmp_m721', 
        title: 'ZXMP M721', 
        width: 150, 
        align: 'right',
        resizable: true,
        cell: (_, { row }) => formatNumber(row.zxmp_m721)
    },
    { 
        colKey: 'zxone_nton', 
        title: 'ZXONE NTON', 
        width: 150, 
        align: 'right',
        resizable: true,
        cell: (_, { row }) => formatNumber(row.zxone_nton)
    },
    {
        colKey: 'operation',
        title: '操作',
        width: 140,
        align: 'center',
        fixed: 'right',
        resizable: false,
        cell: (_, { row }) => (
            <t-space size={8}>
                <t-link theme="primary" hover="color" onClick={() => handleEdit(row)}>
                    编辑
                </t-link>
                <t-link theme="danger" hover="color" onClick={() => handleDeleteConfirm(row)}>
                    删除
                </t-link>
            </t-space>
        )
    }
]);

// 数据
const tableDataList = ref([]);

// 查询参数
const queryParams = ref({
    // 默认筛选条件
    department: '波分软件开发二部',
    domain: '13-智能控制',
    team: [], // 改为数组，支持多选
    year: '2026',
    employee_id: '',
    name: ''
});

// 选项数据
const departmentOptions = ref([]);
const domainOptions = ref([]);
const teamOptions = ref([]);

// 导出相关
const exportLoading = ref(false);

// 同步相关
const syncLoading = ref(false);

// 导入相关
const importDialogVisible = ref(false);
const importPhase = ref('select');  // 'select' | 'result'
const importResult = ref(null);     // 后端返回的导入结果
const importResultMsg = ref('');    // 导入结果摘要文本
const uploadRef = ref(null);
const uploadKey = ref(0);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// 编辑对话框相关
const editDialogVisible = ref(false);
const editFormRef = ref(null);
const editSaving = ref(false);
const editFormData = ref({
    id: null,
    demand_human_power_ratio: 1.00,
    zxone_19700: 0.00,
    zxone_9700: 0.00,
    zxmp_m721: 0.00,
    zxone_nton: 0.00
});

// 表单验证规则
const editFormRules = {
    demand_human_power_ratio: [
        { required: true, message: '需求人力占比不能为空' },
        { 
            validator: (val) => {
                if (val === null || val === undefined || val === '') {
                    return { result: false, message: '需求人力占比不能为空' };
                }
                const num = Number(val);
                if (isNaN(num) || num < 0 || num > 1) {
                    return { result: false, message: '需求人力占比必须在0~1之间' };
                }
                return { result: true };
            }
        }
    ],
    zxone_19700: [
        {
            validator: (val) => {
                if (val === null || val === undefined || val === '') {
                    return { result: true }; // 允许为空，使用默认值0
                }
                const num = Number(val);
                if (isNaN(num) || num < 0 || num > 1) {
                    return { result: false, message: 'ZXONE 19700必须在0~1之间' };
                }
                return { result: true };
            }
        }
    ],
    zxone_9700: [
        {
            validator: (val) => {
                if (val === null || val === undefined || val === '') {
                    return { result: true }; // 允许为空，使用默认值0
                }
                const num = Number(val);
                if (isNaN(num) || num < 0 || num > 1) {
                    return { result: false, message: 'ZXONE 9700必须在0~1之间' };
                }
                return { result: true };
            }
        }
    ],
    zxmp_m721: [
        {
            validator: (val) => {
                if (val === null || val === undefined || val === '') {
                    return { result: true }; // 允许为空，使用默认值0
                }
                const num = Number(val);
                if (isNaN(num) || num < 0 || num > 1) {
                    return { result: false, message: 'ZXMP M21必须在0~1之间' };
                }
                return { result: true };
            }
        }
    ],
    zxone_nton: [
        {
            validator: (val) => {
                if (val === null || val === undefined || val === '') {
                    return { result: true }; // 允许为空，使用默认值0
                }
                const num = Number(val);
                if (isNaN(num) || num < 0 || num > 1) {
                    return { result: false, message: 'ZXONE NTON必须在0~1之间' };
                }
                return { result: true };
            }
        }
    ]
};

// 表格高度
const tableHeight = ref('900px');

// 计算表格高度
const calculateTableHeight = () => {
    tableHeight.value = pubCalculateTableHeight(200);
};

// 格式化占比显示
const formatRatio = (ratio) => {
    if (ratio === null || ratio === undefined) return '1.00';
    const num = Number(ratio);
    if (isNaN(num)) return '1.00';
    return num.toFixed(2);
};

// 格式化数字显示（用于产品投入占比）
const formatNumber = (num) => {
    if (num === null || num === undefined) return '0.00';
    const number = Number(num);
    if (isNaN(number)) return '0.00';
    return number.toFixed(2);
};

// 生命周期
onMounted(async () => {
    try {
        calculateTableHeight();
        window.addEventListener('resize', calculateTableHeight);
        // 先加载选项（不阻塞页面初始化），再按默认条件自动查询一次
        try {
            await loadOptions();
        } catch (error) {
            console.error('加载选项失败:', error);
            MessagePlugin.warning('加载筛选选项失败，请刷新页面重试');
        }
        await loadData();
    } catch (error) {
        console.error('页面初始化失败:', error);
        MessagePlugin.error('页面初始化失败');
    }
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载选项数据
const loadOptions = async () => {
    try {
        // 加载部门选项
        const deptResponse = await getHumanResourceSettingOptions({ option_type: 'department' });
        if (deptResponse.code === 200) {
            departmentOptions.value = (deptResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }

        // 加载领域选项
        const domainResponse = await getHumanResourceSettingOptions({ option_type: 'domain' });
        if (domainResponse.code === 200) {
            domainOptions.value = (domainResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }

        // 加载团队选项
        const teamResponse = await getHumanResourceSettingOptions({ option_type: 'team' });
        if (teamResponse.code === 200) {
            teamOptions.value = (teamResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }
    } catch (error) {
        console.error('加载选项数据失败:', error);
    }
};

// 加载数据
const loadData = async () => {
    try {
        loading.value = true;
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            if (queryParams.value[key] !== '' && queryParams.value[key] !== null) {
                params[key] = queryParams.value[key];
            }
        });
        
        const response = await queryHumanResourceSettingByParams(params);
        if (response.code === 200) {
            tableDataList.value = response.data || [];
        } else {
            MessagePlugin.error(response.message || '加载数据失败');
        }
    } catch (error) {
        console.error('数据加载失败:', error);
        MessagePlugin.error('数据加载失败');
    } finally {
        loading.value = false;
    }
};

// 查询按钮（仅执行查询，不触发聚合）
const handleQuery = async () => {
    try {
        loading.value = true;
        await loadData();
    } catch (error) {
        console.error('查询失败:', error);
        MessagePlugin.error('查询失败: ' + (error.message || '网络错误'));
    } finally {
        loading.value = false;
    }
};

// 批量导出
const handleExport = async () => {
    exportLoading.value = true;
    try {
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            const value = queryParams.value[key];
            if (Array.isArray(value)) {
                if (value.length > 0) params[key] = value;
            } else if (value !== '' && value !== null) {
                params[key] = value;
            }
        });

        const blob = await exportHumanResourceSetting(params);
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.download = '开发人力投入.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        MessagePlugin.success('导出成功');
    } catch (error) {
        console.error('导出失败:', error);
        MessagePlugin.error('导出失败：' + (error.message || '未知错误'));
    } finally {
        exportLoading.value = false;
    }
};

// 同步数据
const handleSync = async () => {
    // 检查是否有领域和团队的筛选条件
    const domain = queryParams.value.domain;
    const teams = queryParams.value.team;
    const year = queryParams.value.year;

    if (!domain) {
        MessagePlugin.warning('请先选择领域');
        return;
    }
    if (!teams || teams.length === 0) {
        MessagePlugin.warning('请先选择团队');
        return;
    }

    syncLoading.value = true;
    try {
        // 对每个团队进行同步
        for (const team of teams) {
            const syncParams = {
                domain: domain,
                team: team,
                year: year || ''
            };
            const response = await triggerSyncRequirementDevHumanResource(syncParams);
            if (response.code === 200) {
                console.log(`团队 ${team} 同步成功`);
            } else {
                console.warn(`团队 ${team} 同步失败:`, response?.message || '未知错误');
            }
        }
        MessagePlugin.success('同步完成');
        // 同步后刷新表格数据
        await loadData();
    } catch (error) {
        console.error('同步失败:', error);
        MessagePlugin.error('同步失败：' + (error.message || '网络错误'));
    } finally {
        syncLoading.value = false;
    }
};

// 批量导入 - 打开弹框
const onBatchImport = () => {
    fileList.value = [];
    uploadError.value = '';
    importPhase.value = 'select';
    importResult.value = null;
    importResultMsg.value = '';
    importDialogVisible.value = true;
};

// 处理文件选择变化
const handleFileChange = (files) => {
    uploadError.value = '';
    fileList.value = files;
    if (files.length > 0) {
        const file = files[0];
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xlsx')) {
            uploadError.value = '文件格式错误，请选择.xlsx格式的文件';
            fileList.value = [];
        }
    }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 重置上传数据
const resetUploadData = () => {
    fileList.value = [];
    uploadKey.value++;
};

// 取消导入
const cancelImportSubmit = () => {
    resetUploadData();
    importDialogVisible.value = false;
};

// 下载示例文件
const downloadExampleFile = () => {
    try {
        const exampleData = [{
            '部门': '示例部门',
            '领域': '示例领域',
            '团队': '示例团队',
            '人员归属': '中兴',
            '工号': '12345678',
            '姓名': '示例姓名',
            '离职时间': '',
            '技能/特性分类': '示例技能',
            '年月': '2026-01',
            '需求人力占比': 1.00,
            'ZXONE 19700': 0.25,
            'ZXONE 9700': 0.25,
            'ZXMP M721': 0.25,
            'ZXONE NTON': 0.25
        }];
        const worksheet = XLSX.utils.json_to_sheet(exampleData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '开发人力投入批量导入示例');
        XLSX.writeFile(workbook, '开发人力投入批量导入示例.xlsx');
        MessagePlugin.success('示例文件下载成功');
    } catch (error) {
        console.error('示例文件生成失败:', error);
        MessagePlugin.error('示例文件生成失败');
    }
};

// 提交导入
const handleImportSubmit = async () => {
    if (fileList.value.length === 0) {
        uploadError.value = '请先选择文件';
        return;
    }
    if (uploadError.value) {
        return;
    }
    importLoading.value = true;
    uploadError.value = '';
    try {
        const file = fileList.value[0];
        const formData = new FormData();
        formData.append('file', file.raw);
        const response = await importHumanResourceSetting(formData);
        if (response.code === 200) {
            const result = response.data || {};
            importResult.value = result;
            importResultMsg.value = response.message || '批量导入成功';
            importPhase.value = 'result';
            // 立即刷新表格
            await loadData();
        } else {
            uploadError.value = response.message || '批量导入失败';
        }
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = error.message || '批量导入失败';
    } finally {
        uploadKey.value++;
        importLoading.value = false;
    }
};

// 关闭导入对话框
const closeImportDialog = () => {
    importDialogVisible.value = false;
    importPhase.value = 'select';
    importResult.value = null;
    importResultMsg.value = '';
};

// 继续导入（返回选择文件阶段）
const resetImportToSelect = () => {
    fileList.value = [];
    uploadError.value = '';
    uploadKey.value++;
    importPhase.value = 'select';
    importResult.value = null;
    importResultMsg.value = '';
};

// 下载失败数据
const downloadFailedRows = () => {
    const rows = importResult.value?.failed_rows;
    if (!rows || rows.length === 0) {
        MessagePlugin.warning('没有失败数据');
        return;
    }
    try {
        const worksheet = XLSX.utils.json_to_sheet(rows);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '导入失败数据');
        XLSX.writeFile(workbook, '开发人力投入_导入失败数据.xlsx');
        MessagePlugin.success('下载成功');
    } catch (error) {
        console.error('下载失败数据失败:', error);
        MessagePlugin.error('下载失败: ' + error.message);
    }
};

// 打开编辑对话框
const handleEdit = (row) => {
    editFormData.value = {
        id: row.id,
        demand_human_power_ratio: (row.demand_human_power_ratio !== null && row.demand_human_power_ratio !== undefined) ? row.demand_human_power_ratio : 1.00,
        zxone_19700: (row.zxone_19700 !== null && row.zxone_19700 !== undefined) ? row.zxone_19700 : 0.00,
        zxone_9700: (row.zxone_9700 !== null && row.zxone_9700 !== undefined) ? row.zxone_9700 : 0.00,
        zxmp_m721: (row.zxmp_m721 !== null && row.zxmp_m721 !== undefined) ? row.zxmp_m721 : 0.00,
        zxone_nton: (row.zxone_nton !== null && row.zxone_nton !== undefined) ? row.zxone_nton : 0.00
    };
    editDialogVisible.value = true;
};

// 保存编辑
const handleSaveEdit = async () => {
    const valid = await editFormRef.value?.validate();
    if (!valid) {
        return;
    }

    // 前端校验 4 个产品投入占比之和
    // 当需求人力占比为 0 时，产品占比之和应为 0；否则应为 1
    const p1 = Number(editFormData.value.zxone_19700) || 0;
    const p2 = Number(editFormData.value.zxone_9700) || 0;
    const p3 = Number(editFormData.value.zxmp_m721) || 0;
    const p4 = Number(editFormData.value.zxone_nton) || 0;
    const total = p1 + p2 + p3 + p4;
    const demandRatio = Number(editFormData.value.demand_human_power_ratio) || 0;
    
    // 根据需求人力占比判断期望的产品占比总和
    const expectedTotal = (demandRatio === 0) ? 0 : 1;
    const errorMessage = (demandRatio === 0) 
        ? '需求人力占比为 0 时，产品投入占比之和必须为 0'
        : '4 个产品投入占比之和必须为 1.00';
    
    if (Math.abs(total - expectedTotal) > 0.000001) {
        MessagePlugin.error(errorMessage);
        return;
    }

    editSaving.value = true;
    try {
        const submitData = {
            data: [{
                id: editFormData.value.id,
                demand_human_power_ratio: Number(editFormData.value.demand_human_power_ratio),
                zxone_19700: p1,
                zxone_9700: p2,
                zxmp_m721: p3,
                zxone_nton: p4
            }]
        };

        const response = await updateHumanResourceSetting(submitData);
        if (response.code === 200) {
            MessagePlugin.success(response.message || '保存成功');
            editDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        MessagePlugin.error('保存失败');
    } finally {
        editSaving.value = false;
    }
};

// 删除相关
const deleteDialogVisible = ref(false);
const deleteLoading = ref(false);
const deleteTargetRow = ref(null);

const handleDeleteConfirm = (row) => {
    deleteTargetRow.value = row;
    deleteDialogVisible.value = true;
};

const handleDeleteSubmit = async () => {
    if (!deleteTargetRow.value) return;
    deleteLoading.value = true;
    try {
        const response = await deleteHumanResourceSetting({ ids: [deleteTargetRow.value.id] });
        if (response.code === 200) {
            MessagePlugin.success(response.message || '删除成功');
            deleteDialogVisible.value = false;
            deleteTargetRow.value = null;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        MessagePlugin.error('删除失败: ' + (error.message || '未知错误'));
    } finally {
        deleteLoading.value = false;
    }
};

// 批量删除相关
const batchDeleteDialogVisible = ref(false);
const batchDeleteLoading = ref(false);
const batchDeleteParams = ref({
    team: [],
    employee_id: []
});

// 批量删除条件描述（computed）
const batchDeleteConditionDesc = computed(() => {
    const teams = batchDeleteParams.value.team;
    const employeeIds = batchDeleteParams.value.employee_id;
    if (employeeIds.length > 0) {
        return `将按工号删除：${employeeIds.join(', ')}（工号优先，团队条件不生效）`;
    }
    if (teams.length > 0) {
        return `将按团队删除：${teams.join(', ')}`;
    }
    return '';
});

// 打开批量删除对话框，预填当前筛选条件
const onBatchDelete = () => {
    batchDeleteParams.value = {
        team: [...(queryParams.value.team || [])],
        employee_id: queryParams.value.employee_id ? [queryParams.value.employee_id] : []
    };
    batchDeleteDialogVisible.value = true;
};

// 提交批量删除
const handleBatchDeleteSubmit = async () => {
    const teams = batchDeleteParams.value.team.filter(t => t && String(t).trim());
    const employeeIds = batchDeleteParams.value.employee_id.filter(e => e && String(e).trim());
    if (!teams.length && !employeeIds.length) {
        MessagePlugin.warning('至少需要提供团队或工号作为删除条件');
        return;
    }

    const requestData = {
        team: teams,
        employee_id: employeeIds
    };
    console.log('===== 批量删除请求参数 =====');
    console.log('teams:', teams);
    console.log('employeeIds:', employeeIds);
    console.log('完整请求体:', JSON.stringify(requestData, null, 2));

    batchDeleteLoading.value = true;
    try {
        const response = await batchDeleteHumanResourceSetting(requestData);
        console.log('批量删除响应:', response);
        if (response.code === 200) {
            MessagePlugin.success(response.message || '批量删除成功');
            batchDeleteDialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '批量删除失败');
        }
    } catch (error) {
        console.error('批量删除失败 - 完整错误对象:', error);
        console.error('错误名称:', error?.name);
        console.error('错误消息:', error?.message);
        console.error('错误堆栈:', error?.stack);
        if (error?.response) {
            console.error('响应状态:', error.response.status);
            console.error('响应数据:', error.response.data);
            console.error('响应头:', error.response.headers);
        }
        if (error?.request) {
            console.error('请求已发出但无响应 - request 对象:', error.request);
            console.error('请求URL:', error.config?.url);
            console.error('请求方法:', error.config?.method);
        }
        MessagePlugin.error('批量删除失败: ' + (error.message || '未知错误'));
    } finally {
        batchDeleteLoading.value = false;
    }
};

// 列宽调整结束回调，更新列宽配置
const onColumnResizeEnd = ({ col, resizeWidth }) => {
    const target = tableColumnList.value.find(c => c.colKey === col.colKey);
    if (target) {
        target.width = resizeWidth;
    }
};

// 取消编辑
const handleCancelEdit = () => {
    editDialogVisible.value = false;
    editFormData.value = {
        id: null,
        demand_human_power_ratio: 1.00,
        zxone_19700: 0.00,
        zxone_9700: 0.00,
        zxmp_m721: 0.00,
        zxone_nton: 0.00
    };
};
</script>

<style scoped>
.scene-main {
    padding: 16px;
}

.dialog-form {
    padding: 16px 0;
}

.form-tip {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
}

/* 表格数据单元格样式 */
:deep(.t-table__body) td {
    color: #555 !important;
    font-weight: normal !important;
    background-color: #fefefe !important;
    border-bottom: 1px solid #d6d6d6 !important;
    border-right: 1px solid #e8e8e8 !important;
    border-left: none !important;
    line-height: 1.4;
}

/* 表格头样式 */
:deep(.t-table__header) th {
    background-color: #e7e7e7 !important;
    color: #333 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #e0e0e0 !important;
    border-right: 1px solid #d0d0d0 !important;
    border-left: none !important;
    line-height: 1.4;
}

/* 奇偶行颜色区分 */
:deep(.t-table__body) tr:nth-child(even) td {
    background-color: #f8f8f8 !important;
}

/* 悬停效果 */
:deep(.t-table__body) tr:hover td {
    background-color: #dbeafe !important;
    transition: background-color 0.3s ease;
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

.file-size {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
}

.error-message {
    color: #ff4d4f;
    padding: 8px 0;
    min-height: 24px;
}

.example-download {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px dashed #e5e6eb;
}

.example-space {
    display: flex;
    align-items: center;
    gap: 12px;
}

.example-space p {
    margin: 0;
    color: #666;
    font-size: 14px;
}

.example-btn {
    font-size: 14px;
    padding-left: 0;
    display: inline-flex;
    align-items: center;
}

.mr-1 {
    margin-right: 4px;
}

/* 导入提示 */
.psm-tip {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin-top: 12px;
    padding: 8px 12px;
    background: #fffbe6;
    border: 1px solid #ffe58f;
    border-radius: 4px;
    font-size: 13px;
    color: #614700;
    line-height: 1.5;
}

/* 导入结果 */
.import-result-container {
    padding: 16px 0;
}

.result-summary {
    display: flex;
    align-items: center;
    font-size: 15px;
    font-weight: 500;
    color: #333;
    margin-bottom: 12px;
}

.failed-info {
    margin-top: 4px;
}

.failed-detail {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.failed-tip {
    font-size: 13px;
    color: #666;
    margin: 0;
}

.error-list {
    margin-top: 12px;
    padding: 8px 12px;
    background: #fff2f0;
    border: 1px solid #ffccc7;
    border-radius: 4px;
}
</style>
