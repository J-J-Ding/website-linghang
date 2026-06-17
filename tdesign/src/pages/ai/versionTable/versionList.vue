<template>
    <div class="scene-main">
        <t-space direction="vertical" style="width: 100%">
            <!-- 筛选区域 -->
            <t-space :size="16" style="flex-wrap: wrap">
                <t-select
                    v-model="queryParams.belong_product"
                    placeholder="请选择所属产品"
                    clearable
                    style="width: 300px;"
                    label="所属产品: "
                    :options="belongProductOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.product_roadmap"
                    placeholder="请选择所属项目"
                    clearable
                    style="width: 300px;"
                    label="所属项目: "
                    :options="productRoadmapOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.requirement_preplanning"
                    placeholder="请选择需求预规划"
                    clearable
                    style="width: 300px;"
                    label="需求预规划: "
                    :options="requirementPreplanningOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.version_status"
                    placeholder="请选择版本状态"
                    clearable
                    style="width: 300px;"
                    label="版本状态: "
                    :options="versionStatusOptions"
                    filterable
                />
            </t-space>
            
            <!-- 按钮区域 -->
            <t-space style="justify-content: flex-start;margin-bottom: 16px">
                <t-button @click="handleQuery">查询</t-button>
                <t-button @click="handleResetFilter">重置</t-button>
                <t-button @click="openAddDialog">新建</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button @click="onBatchExport">批量导出</t-button>
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
            :scroll="{ type: 'virtual' }"
            :max-height="tableHeight">
        </t-table>

        <!-- 新增/编辑对话框 -->
        <t-dialog
            v-model:visible="dialogVisible"
            :width="600"
            :header="dialogTitle">
            <div class="dialog-form">
                <t-form
                    ref="formRef"
                    :data="formData"
                    :rules="formRules"
                    layout="vertical">
                    <t-form-item label="* 所属产品" name="belong_product">
                        <t-input
                            v-model="formData.belong_product"
                            placeholder="请输入所属产品"
                        />
                    </t-form-item>
                    <t-form-item label="* 所属项目" name="product_roadmap">
                        <t-input
                            v-model="formData.product_roadmap"
                            placeholder="请输入所属项目"
                        />
                    </t-form-item>
                    <t-form-item label="* 需求预规划" name="requirement_preplanning">
                        <t-input
                            v-model="formData.requirement_preplanning"
                            placeholder="请输入需求预规划"
                        />
                    </t-form-item>
                    <t-form-item label="启动开发日期" name="start_dev_date">
                        <t-date-picker
                            v-model="formData.start_dev_date"
                            placeholder="请选择启动开发日期"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="完成开发日期" name="finish_dev_date">
                        <t-date-picker
                            v-model="formData.finish_dev_date"
                            placeholder="请选择完成开发日期"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="成果鉴定日期" name="achievement_appraisal_date">
                        <t-date-picker
                            v-model="formData.achievement_appraisal_date"
                            placeholder="请选择成果鉴定日期"
                            format="YYYY-MM-DD"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="版本状态" name="version_status">
                        <t-input
                            v-model="formData.version_status"
                            placeholder="请输入版本状态"
                            clearable
                        />
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleCancel">取消</t-button>
                <t-button :loading="saving" @click="handleSave">确认</t-button>
            </template>
        </t-dialog>

        <!-- 删除确认对话框 -->
        <t-dialog
            v-model:visible="deleteDialogVisible"
            :width="400"
            header="删除确认">
            <p>确定要删除选中的记录吗？</p>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" :loading="deleting" @click="handleConfirmDelete">确认删除</t-button>
            </template>
        </t-dialog>

        <!-- 批量导入对话框 -->
        <t-dialog
            v-model:visible="importDialogVisible"
            :width="600"
            header="批量导入版本视图">
            <div class="import-container">
                <t-upload
                    ref="uploadRef"
                    :key="uploadKey"
                    v-model="fileList"
                    :auto-upload="false"
                    :max="1"
                    accept=".xlsx"
                    :on-change="handleFileChange">
                    <template #trigger>
                        <t-button>
                            <t-icon name="upload" />
                            选择文件
                        </t-button>
                    </template>
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
            </div>
            <template #footer>
                <t-button @click="cancelImportSubmit">取消</t-button>
                <t-button :loading="importLoading" @click="handleImportSubmit">确认导入</t-button>
            </template>
        </t-dialog>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import {
    queryVersionTableByParams,
    createVersionTable,
    updateVersionTable,
    deleteVersionTable,
    getVersionTableOptions,
    importVersionTable,
    exportVersionTable
} from '@/api/versionTable.js';
import * as XLSX from 'xlsx';

const user = useUserStore();

// 表格配置
const tableRef = ref();
const loading = ref(false);
const tableColumnList = [
    { colKey: 'id', title: 'ID', width: '80', align: 'center' },
    { colKey: 'belong_product', title: '所属产品', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'product_roadmap', title: '所属项目', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'requirement_preplanning', title: '需求预规划', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'start_dev_date', title: '启动开发日期', width: '150', align: 'center' },
    { colKey: 'finish_dev_date', title: '完成开发日期', width: '150', align: 'center' },
    { colKey: 'achievement_appraisal_date', title: '成果鉴定日期', width: '150', align: 'center' },
    { 
        colKey: 'cycle_days', 
        title: '周期 (天)', 
        width: '120', 
        align: 'right',
        cell: (_, { row }) => {
            // 如果周期天数为空，尝试计算：周期 = 成果鉴定日期 - 启动开发日期
            if (!row.cycle_days && row.start_dev_date && row.achievement_appraisal_date) {
                const days = calculateCycleDays(row.start_dev_date, row.achievement_appraisal_date);
                return days !== null ? days : '-';
            }
            return row.cycle_days !== null ? row.cycle_days : '-';
        }
    },
    { colKey: 'version_status', title: '版本状态', width: '120', align: 'center' },
    {
        colKey: 'operation',
        title: '操作',
        width: '150',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (
            <>
                <t-link theme="primary" hover="color" onClick={() => openEditDialog(row)} style={{ marginRight: '8px' }}>编辑</t-link>
                <t-link theme="danger" hover="color" onClick={() => openDeleteDialog(row)}>删除</t-link>
            </>
        )
    }
];

// 数据
const tableDataList = ref([]);

// 查询参数
const queryParams = ref({
    belong_product: '',
    product_roadmap: '',
    requirement_preplanning: '',
    version_status: ''
});

// 选项数据
const belongProductOptions = ref([]);
const productRoadmapOptions = ref([]);
const requirementPreplanningOptions = ref([]);
const versionStatusOptions = ref([]);

// 对话框相关
const dialogVisible = ref(false);
const dialogTitle = ref('新建版本');
const isEdit = ref(false);
const formRef = ref(null);
const saving = ref(false);
const formData = ref({
    id: null,
    belong_product: '',
    product_roadmap: '',
    requirement_preplanning: '',
    start_dev_date: '',
    finish_dev_date: '',
    achievement_appraisal_date: '',
    version_status: ''
});

// 表单验证规则
const formRules = {
    belong_product: [{ required: true, message: '所属产品不能为空' }],
    product_roadmap: [{ required: true, message: '所属项目不能为空' }],
    requirement_preplanning: [{ required: true, message: '需求预规划不能为空' }]
};

// 删除对话框
const deleteDialogVisible = ref(false);
const deleting = ref(false);
const deleteRowId = ref(null);

// 批量导入相关
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const uploadKey = ref(0);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// 表格高度
const tableHeight = ref('900px');

// 计算表格高度
const calculateTableHeight = () => {
    tableHeight.value = pubCalculateTableHeight(200);
};

// 计算周期天数：周期 = 成果鉴定日期 - 启动开发日期
const calculateCycleDays = (startDate, achievementAppraisalDate) => {
    if (!startDate || !achievementAppraisalDate) return null;
    try {
        const start = new Date(startDate);
        const achievement = new Date(achievementAppraisalDate);
        const diffTime = achievement - start;
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        return diffDays >= 0 ? diffDays : null;
    } catch (error) {
        return null;
    }
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

// 生命周期
onMounted(async () => {
    calculateTableHeight();
    window.addEventListener('resize', calculateTableHeight);
    await loadOptions();
    await loadData();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载选项数据
const loadOptions = async () => {
    try {
        // 加载所属产品选项
        const belongProductResponse = await getVersionTableOptions({ option_type: 'belong_product' });
        if (belongProductResponse.code === 200) {
            belongProductOptions.value = (belongProductResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }

        // 加载所属项目选项
        const productRoadmapResponse = await getVersionTableOptions({ option_type: 'product_roadmap' });
        if (productRoadmapResponse.code === 200) {
            productRoadmapOptions.value = (productRoadmapResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }

        // 加载需求预规划选项
        const requirementPreplanningResponse = await getVersionTableOptions({ option_type: 'requirement_preplanning' });
        if (requirementPreplanningResponse.code === 200) {
            requirementPreplanningOptions.value = (requirementPreplanningResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        }

        // 加载版本状态选项
        const versionStatusResponse = await getVersionTableOptions({ option_type: 'version_status' });
        if (versionStatusResponse.code === 200) {
            versionStatusOptions.value = (versionStatusResponse.data || []).map(item => ({
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
        
        const response = await queryVersionTableByParams(params);
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

// 查询
const handleQuery = () => {
    loadData();
};

// 重置筛选
const handleResetFilter = () => {
    queryParams.value = {
        belong_product: '',
        product_roadmap: '',
        requirement_preplanning: '',
        version_status: ''
    };
    loadData();
};

// 打开新增对话框
const openAddDialog = () => {
    isEdit.value = false;
    dialogTitle.value = '新建版本';
    formData.value = {
        id: null,
        belong_product: '',
        product_roadmap: '',
        requirement_preplanning: '',
        start_dev_date: '',
        finish_dev_date: '',
        achievement_appraisal_date: '',
        version_status: ''
    };
    dialogVisible.value = true;
};

// 打开编辑对话框
const openEditDialog = (row) => {
    isEdit.value = true;
    dialogTitle.value = '编辑版本';
    formData.value = {
        id: row.id,
        belong_product: row.belong_product,
        product_roadmap: row.product_roadmap,
        requirement_preplanning: row.requirement_preplanning,
        start_dev_date: row.start_dev_date || '',
        finish_dev_date: row.finish_dev_date || '',
        achievement_appraisal_date: row.achievement_appraisal_date || '',
        version_status: row.version_status || ''
    };
    dialogVisible.value = true;
};

// 保存
const handleSave = async () => {
    const valid = await formRef.value?.validate();
    if (!valid) {
        return;
    }

    saving.value = true;
    try {
        const submitData = {
            ...formData.value,
            start_dev_date: formatDate(formData.value.start_dev_date),
            finish_dev_date: formatDate(formData.value.finish_dev_date),
            achievement_appraisal_date: formatDate(formData.value.achievement_appraisal_date)
        };

        let response;
        if (isEdit.value) {
            response = await updateVersionTable({ data: [submitData] });
        } else {
            response = await createVersionTable(submitData);
        }

        if (response.code === 200) {
            MessagePlugin.success(response.message || '保存成功');
            dialogVisible.value = false;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        MessagePlugin.error('保存失败');
    } finally {
        saving.value = false;
    }
};

// 取消
const handleCancel = () => {
    dialogVisible.value = false;
    formData.value = {
        id: null,
        belong_product: '',
        product_roadmap: '',
        requirement_preplanning: '',
        start_dev_date: '',
        finish_dev_date: '',
        achievement_appraisal_date: '',
        version_status: ''
    };
};

// 打开删除对话框
const openDeleteDialog = (row) => {
    deleteRowId.value = row.id;
    deleteDialogVisible.value = true;
};

// 确认删除
const handleConfirmDelete = async () => {
    if (!deleteRowId.value) {
        return;
    }

    deleting.value = true;
    try {
        const response = await deleteVersionTable({ ids: [deleteRowId.value] });
        if (response.code === 200) {
            MessagePlugin.success(response.message || '删除成功');
            deleteDialogVisible.value = false;
            deleteRowId.value = null;
            await loadData();
        } else {
            MessagePlugin.error(response.message || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        MessagePlugin.error('删除失败');
    } finally {
        deleting.value = false;
    }
};

// 批量导入
const onBatchImport = () => {
    // 重置状态
    fileList.value = [];
    uploadError.value = '';
    importDialogVisible.value = true;
};

// 处理文件选择变化
const handleFileChange = (files) => {
    uploadError.value = '';
    fileList.value = files;

    // 验证文件格式
    if (files.length > 0) {
        const file = files[0];
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xlsx')) {
            uploadError.value = '文件格式错误，请选择.xlsx格式的文件';
            fileList.value = []; // 清空错误文件
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
            '所属产品': '示例产品',
            '所属项目': '示例项目',
            '需求预规划': '示例需求预规划',
            '启动开发日期': '2026-01-01',
            '完成开发日期': '2026-06-30',
            '成果鉴定日期': '2026-07-15',
            '版本状态': '开发中'
        }];

        const worksheet = XLSX.utils.json_to_sheet(exampleData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '版本视图批量导入示例');

        const fileName = '版本视图批量导入示例.xlsx';
        XLSX.writeFile(workbook, fileName);
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

        // 构造表单数据
        formData.append('file', file.raw);

        // 调用后端批量导入接口
        const response = await importVersionTable(formData);

        if (response.code === 200) {
            MessagePlugin.success(response.message || '批量导入成功');
            importDialogVisible.value = false;
            resetUploadData();
            await loadData();
        } else {
            uploadError.value = response.message || '批量导入失败';
        }
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = error.message || '批量导入失败';
    } finally {
        importLoading.value = false;
    }
};

// 批量导出
const onBatchExport = async () => {
    try {
        loading.value = true;
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            if (queryParams.value[key] !== '' && queryParams.value[key] !== null) {
                params[key] = queryParams.value[key];
            }
        });

        const response = await exportVersionTable(params);
        
        // 处理blob响应
        if (response instanceof Blob) {
            const url = window.URL.createObjectURL(response);
            const link = document.createElement('a');
            link.href = url;
            link.download = `版本视图导出_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            MessagePlugin.success('导出成功');
        } else {
            // 如果不是blob，可能是错误响应
            const reader = new FileReader();
            reader.onload = () => {
                try {
                    const result = JSON.parse(reader.result);
                    MessagePlugin.error(result.message || '导出失败');
                } catch (e) {
                    MessagePlugin.error('导出失败');
                }
            };
            reader.readAsText(response);
        }
    } catch (error) {
        console.error('导出失败:', error);
        MessagePlugin.error('导出失败');
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
.scene-main {
    padding: 16px;
}

.dialog-form {
    padding: 16px 0;
}

/* 表格数据单元格样式 */
:deep(.t-table__body) td {
    color: #555 !important;
    font-weight: normal !important;
    background-color: #fefefe !important;
    border-bottom: 1px solid #d6d6d6 !important;
    line-height: 1.4;
    border-left: none !important;
    border-right: none !important;
}

/* 表格头样式 */
:deep(.t-table__header) th {
    background-color: #e7e7e7 !important;
    color: #333 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #e0e0e0 !important;
    border-left: none !important;
    border-right: none !important;
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
</style>
