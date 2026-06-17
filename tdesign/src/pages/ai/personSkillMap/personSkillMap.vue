<template>
    <div class="scene-main">
        <t-space direction="vertical" style="width: 100%">
            <!-- 筛选区域 -->
            <t-space :size="16" style="flex-wrap: wrap">
                <t-input
                    v-model="queryParams.department"
                    placeholder="部门"
                    clearable
                    style="width: 180px;"
                    label="部门: "
                />
                <t-input
                    v-model="queryParams.domain"
                    placeholder="领域"
                    clearable
                    style="width: 180px;"
                    label="领域: "
                />
                <t-input
                    v-model="queryParams.team"
                    placeholder="团队"
                    clearable
                    style="width: 180px;"
                    label="团队: "
                />
                <t-select
                    v-model="queryParams.person_belong"
                    placeholder="人员归属"
                    clearable
                    style="width: 180px;"
                    label="人员归属: "
                    :options="personBelongOptions"
                />
                <t-input
                    v-model="queryParams.employee_id"
                    placeholder="工号"
                    clearable
                    style="width: 180px;"
                    label="工号: "
                />
                <t-input
                    v-model="queryParams.name"
                    placeholder="姓名"
                    clearable
                    style="width: 180px;"
                    label="姓名: "
                />
                <t-select
                    v-model="queryParams.leave_time"
                    placeholder="在职状态"
                    clearable
                    style="width: 180px;"
                    label="在职状态: "
                >
                    <t-option value="" label="在职" />
                    <t-option value="has_leave" label="已离职" />
                </t-select>
            </t-space>
            
            <!-- 按钮区域 -->
            <t-space style="justify-content: flex-start;margin-bottom: 16px;">
                <t-button @click="filterData">查询</t-button>
                <!-- 隐藏重置按钮，保留代码 -->
                <!-- <t-button @click="resetFilters">重置</t-button> -->
                <!-- 隐藏新建按钮，保留代码 -->
                <!-- <t-button @click="openAddDialog">新建</t-button> -->
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button :loading="exportLoading" @click="onBatchExport">批量导出</t-button>
            </t-space>
        </t-space>
        <t-table
            ref="tableRef"
            row-key="id"
            :columns="tableColumnList"
            :data="tableDataList"
            :bordered="true"
            :hover="true"
            :scroll="{ type: 'virtual' }"
            resizable
            :loading="loading"
            :max-height="tableHeight">
        </t-table>

        <!-- 新增/编辑对话框 -->
        <t-dialog
            v-model:visible="dialogVisible"
            :width="800"
            :header="dialogTitle">
            <div class="dialog-form">
                <t-form
                    ref="formRef"
                    :data="formData"
                    :rules="formRules"
                    layout="vertical">
                    <t-form-item label="部门" name="department">
                        <t-input
                            v-model="formData.department"
                            placeholder="请输入部门"
                        />
                    </t-form-item>
                    <t-form-item label="项目组" name="project_group">
                        <t-input
                            v-model="formData.project_group"
                            placeholder="请输入项目组"
                        />
                    </t-form-item>
                    <t-form-item label="领域" name="domain">
                        <t-input
                            v-model="formData.domain"
                            placeholder="请输入领域"
                        />
                    </t-form-item>
                    <t-form-item label="团队" name="team">
                        <t-input
                            v-model="formData.team"
                            placeholder="请输入团队"
                        />
                    </t-form-item>
                    <t-form-item label="人员归属" name="person_belong">
                        <t-select
                            v-model="formData.person_belong"
                            placeholder="请选择人员归属"
                            :options="personBelongOptions"
                        />
                    </t-form-item>
                    <t-form-item label="工号" name="employee_id">
                        <t-input
                            v-model="formData.employee_id"
                            placeholder="请输入工号"
                            :disabled="isEdit"
                        />
                    </t-form-item>
                    <t-form-item label="姓名" name="name">
                        <t-input
                            v-model="formData.name"
                            placeholder="请输入姓名"
                        />
                    </t-form-item>
                    <t-form-item label="离职时间" name="leave_time">
                        <t-date-picker
                            v-model="formData.leave_time"
                            placeholder="请选择离职时间（在职则不填）"
                            format="YYYY-MM-DD"
                            clearable
                            style="width: 100%" />
                    </t-form-item>
                    <t-form-item label="技能/特性分类" name="skill_category">
                        <t-input
                            v-model="formData.skill_category"
                            placeholder="请输入技能/特性分类（多个用逗号分隔）"
                        />
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleCancel">取消</t-button>
                <t-button @click="handleConfirm" :loading="saving">确认</t-button>
            </template>
        </t-dialog>

        <!-- 删除确认对话框 -->
        <t-dialog
            v-model:visible="deleteDialogVisible"
            :width="500"
            header="删除确认">
            <p>确定要删除选中的记录吗？</p>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" @click="handleDeleteConfirm" :loading="deleting">确认删除</t-button>
            </template>
        </t-dialog>

        <!-- 批量导入对话框 -->
        <t-dialog
            v-model:visible="importDialogVisible"
            :width="600"
            theme="warning"
            header="批量导入数据">
            <div class="import-container">
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
import { 
    queryPersonSkillMapByParams, 
    createPersonSkillMap, 
    updatePersonSkillMap, 
    deletePersonSkillMap,
    getPersonSkillMapOptions,
    importPersonSkillMap,
    exportPersonSkillMap
} from '@/api/personSkillMap.js';
import * as XLSX from 'xlsx';

const user = useUserStore();

// 表格配置
const tableRef = ref();
const loading = ref(false);
const tableColumnList = [
    { colKey: 'id', title: 'ID', width: '80', align: 'center' },
    { colKey: 'department', title: '部门', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'domain', title: '领域', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'team', title: '团队', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'person_belong', title: '人员归属', width: '120', align: 'center' },
    { colKey: 'employee_id', title: '工号', width: '120', align: 'center' },
    { colKey: 'name', title: '姓名', width: '100', align: 'left' },
    { colKey: 'leave_time', title: '离职时间', width: '150', align: 'center' },
    { colKey: 'skill_category', title: '技能/特性分类', width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
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
    department: '',
    domain: '',
    team: '',
    person_belong: '',
    employee_id: '',
    name: '',
    leave_time: ''
});

// 对话框相关
const dialogVisible = ref(false);
const dialogTitle = ref('新建人员');
const isEdit = ref(false);
const formRef = ref(null);
const saving = ref(false);
const formData = ref({
    id: null,
    department: '',
    project_group: '',
    domain: '',
    team: '',
    person_belong: '',
    employee_id: '',
    name: '',
    leave_time: '',
    skill_category: ''
});

// 表单验证规则
const formRules = {
    department: [{ required: true, message: '部门不能为空' }],
    project_group: [{ required: true, message: '项目组不能为空' }],
    domain: [{ required: true, message: '领域不能为空' }],
    team: [{ required: true, message: '团队不能为空' }],
    person_belong: [{ required: true, message: '人员归属不能为空' }],
    employee_id: [{ required: true, message: '工号不能为空' }],
    name: [{ required: true, message: '姓名不能为空' }]
};

// 删除对话框
const deleteDialogVisible = ref(false);
const deleting = ref(false);
const deleteRowId = ref(null);

// 批量导出相关
const exportLoading = ref(false);

// 批量导入相关
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const uploadKey = ref(0);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// 选项数据
const personBelongOptions = ref([
    { label: '中兴', value: '中兴' },
    { label: '外协', value: '外协' }
]);

// 表格高度
const tableHeight = ref('900px');

// 计算表格高度
const calculateTableHeight = () => {
    const offset = 200;
    tableHeight.value = `${window.innerHeight - offset}px`;
};

// 生命周期
onMounted(async () => {
    calculateTableHeight();
    window.addEventListener('resize', calculateTableHeight);
    await loadData();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载数据
const loadData = async () => {
    try {
        loading.value = true;
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            if (queryParams.value[key] !== '' && queryParams.value[key] !== null) {
                if (key === 'leave_time' && queryParams.value[key] === 'has_leave') {
                    // 查询已离职人员，传递一个特殊标记
                    params[key] = 'has_leave';
                } else {
                    params[key] = queryParams.value[key];
                }
            }
        });
        
        const response = await queryPersonSkillMapByParams(params);
        if (response.code === 200) {
            tableDataList.value = response.data || [];
            // 处理离职时间显示
            tableDataList.value = tableDataList.value.map(item => {
                if (!item.leave_time || item.leave_time === '') {
                    return { ...item, leave_time: '在职' };
                }
                return item;
            });
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

// 筛选数据
const filterData = () => {
    loadData();
};

// 重置筛选
const resetFilters = () => {
    queryParams.value = {
        department: '',
        domain: '',
        team: '',
        person_belong: '',
        employee_id: '',
        name: '',
        leave_time: ''
    };
    loadData();
};

// 打开新增对话框
const openAddDialog = () => {
    isEdit.value = false;
    dialogTitle.value = '新建人员';
    formData.value = {
        id: null,
        department: '',
        project_group: '',
        domain: '',
        team: '',
        person_belong: '',
        employee_id: '',
        name: '',
        leave_time: '',
        skill_category: ''
    };
    dialogVisible.value = true;
};

// 打开编辑对话框
const openEditDialog = (row) => {
    isEdit.value = true;
    dialogTitle.value = '编辑人员';
    formData.value = {
        id: row.id,
        department: row.department || '',
        project_group: row.project_group || '',
        domain: row.domain || '',
        team: row.team || '',
        person_belong: row.person_belong || '',
        employee_id: row.employee_id || '',
        name: row.name || '',
        leave_time: row.leave_time && row.leave_time !== '在职' ? row.leave_time : '',
        skill_category: row.skill_category || ''
    };
    dialogVisible.value = true;
};

// 确认保存
const handleConfirm = async () => {
    const valid = await formRef.value?.validate();
    if (!valid) {
        return;
    }
    
    saving.value = true;
    try {
        const submitData = { ...formData.value };
        
        if (isEdit.value) {
            // 更新
            const response = await updatePersonSkillMap({ data: [submitData] });
            if (response.code === 200) {
                MessagePlugin.success('更新成功');
                dialogVisible.value = false;
                await loadData();
            } else {
                MessagePlugin.error(response.message || '更新失败');
            }
        } else {
            // 新增
            const response = await createPersonSkillMap(submitData);
            if (response.code === 200) {
                MessagePlugin.success('创建成功');
                dialogVisible.value = false;
                await loadData();
            } else {
                MessagePlugin.error(response.message || '创建失败');
            }
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
    formRef.value?.resetValidate();
};

// 打开删除对话框
const openDeleteDialog = (row) => {
    deleteRowId.value = row.id;
    deleteDialogVisible.value = true;
};

// 确认删除
const handleDeleteConfirm = async () => {
    if (!deleteRowId.value) {
        return;
    }
    
    deleting.value = true;
    try {
        const response = await deletePersonSkillMap({ ids: [deleteRowId.value] });
        if (response.code === 200) {
            MessagePlugin.success('删除成功');
            deleteDialogVisible.value = false;
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

// 批量导出
const onBatchExport = async () => {
    exportLoading.value = true;
    try {
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            if (queryParams.value[key] !== '' && queryParams.value[key] !== null) {
                params[key] = queryParams.value[key];
            }
        });

        const blob = await exportPersonSkillMap(params);
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.download = '人员技能地图.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        MessagePlugin.success('导出成功');
    } catch (error) {
        console.error('导出失败:', error);
        MessagePlugin.error('导出失败: ' + (error.message || '未知错误'));
    } finally {
        exportLoading.value = false;
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
            '部门': '示例部门',
            '项目组': '示例项目组',
            '领域': '示例领域',
            '团队': '示例团队',
            '人员归属': '中兴',
            '工号': '12345678',
            '姓名': '示例姓名',
            '离职时间': '',
            '技能/特性分类': '技能1,技能2'
        }];

        const worksheet = XLSX.utils.json_to_sheet(exampleData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '人员技能地图批量导入示例');

        const fileName = '人员技能地图批量导入示例.xlsx';
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
        const response = await importPersonSkillMap(formData);

        if (response.code === 200) {
            MessagePlugin.success(response.message || '批量导入成功');
            importDialogVisible.value = false;
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
</script>

<style scoped>

.scene-main {
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

.dialog-form {
    padding: 16px 0;
    max-height: 500px;
    overflow-y: auto;
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
