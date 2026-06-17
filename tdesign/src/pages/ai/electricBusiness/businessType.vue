<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-select
                v-model="selectedBusinessSpeedOptionList"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 600px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择光口业务速率"
                label="光口业务速率: ">
                    <t-option v-for="option in allBusinessSpeedOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="selectedStatusOptionList"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 300px;"
                placeholder="请选择数据状态"
                label="数据状态: ">
                    <t-option v-for="option in statusOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-button @click="filterData">筛选</t-button>
                <t-button @click="resetFilters">重置</t-button>
                <t-button @click="openAddDialog">新增</t-button>
                <t-button @click="onBatchDelete">批量删除</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button @click="onBatchOutput">批量导出</t-button>
            </t-space>
            <p> </p>
        </t-space>
        <t-table
        ref="tableRef"
        row-key="id"
        :columns="tableColumnList"
        :data="tableDataList"
        :selected-row-keys="selectedRowKeyList"
        :select-on-row-click="false"
        active-row-type="multiple"
        :hover="true"
        :max-height="tableHeight"
        bordered
        resizable
        @select-change="handleSelectChange">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-table>

        <t-dialog
        v-model:visible="addDialogVisible"
        :width="700"
        theme="warning">
            <template #header>
                <t-space>
                    <span>新增数据</span>
                    <t-tooltip
                    content="1、带*的为必填项。2、提交后数据将进入审核流程, 审核通过后将正式生效。"
                    placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <div class="add-form">
                <t-form ref="addFormRef" :data="dialogFormData" layout="vertical">
                     <t-form-item label="* 光口业务速率" name="businessSpeed">
                        <t-select
                        v-model="dialogFormData.businessSpeed"
                        placeholder="请选择光口业务速率"
                        creatable
                        filterable
                        :disabled="false"
                        @change="handleBusinessSpeedChange"
                        :onCreate="handleCreateBusinessSpeedOption">>
                            <t-option v-for="option in allBusinessSpeedOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 业务类型" name="selectedBusinessTypeList">
                        <t-select
                        v-model="dialogFormData.selectedBusinessTypeList"
                        placeholder="请选择业务类型"
                        creatable
                        multiple
                        filterable
                        clearable
                        :min-collapsed-num="1"
                        :disabled="!dialogFormData.businessSpeed"
                        :onCreate="handleCreateBusinessTypeOption">>
                            <t-option v-for="option in allBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleAddCancel">取消</t-button>
                <t-button @click="handleAddConfirm">提交审核</t-button>
            </template>
        </t-dialog>

        <t-dialog
        v-model:visible="deleteDialogVisible"
        :width="700"
        @confirm="handleDeleteConfirm"
        @cancel="deleteDialogVisible = false"
        theme="warning">
            <template #header>
                <t-space>
                    <span>{{ deleteDialogTitle }}</span>
                    <t-tooltip
                    content="提交后数据将进入审核流程, 审核通过后将正式生效。"
                    placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <t-space direction="vertical" style="width: 100%">
                <t-form  layout="vertical">
                    <p>本次删除 {{ selectedRowKeyList.length}} 条数据，是否提交审核？</p>
                </t-form>
            </t-space>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button @click="handleDeleteConfirm">提交审核</t-button>
            </template>
        </t-dialog>

        <t-dialog
        v-model:visible="editDialogVisible"
        :width="700"
        theme="warning">
            <template #header>
                <t-space>
                    <span>修改数据</span>
                    <t-tooltip
                    content="1、带*的为必填项。2、提交后数据将进入审核流程, 审核通过后将正式生效。"
                    placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <div class="edit-form">
                <t-form ref="editForm" :data="dialogFormData" layout="vertical">
                    <t-form-item label="* 光口业务速率" name="businessSpeed">
                        <t-select
                        v-model="dialogFormData.businessSpeed"
                        creatable
                        filterable
                        placeholder="请选择光口业务速率"
                        @change="handleBusinessSpeedChange"
                        :onCreate="handleCreateBusinessSpeedOption">
                            <t-option v-for="option in allBusinessSpeedOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 业务类型" name="selectedBusinessTypeList">
                        <t-select
                        v-model="dialogFormData.selectedBusinessTypeList"
                        creatable
                        multiple
                        filterable
                        clearable
                        :min-collapsed-num="1"
                        placeholder="请选择业务类型"
                        :onCreate="handleCreateBusinessTypeOption"
                        :disabled="!dialogFormData.businessSpeed">
                            <t-option v-for="option in allBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleEditCancel">取消</t-button>
                <t-button @click="handleEditConfirm">提交审核</t-button>
            </template>
        </t-dialog>

        <t-dialog
        v-model:visible="queryDialogVisible"
        :width="700"
        theme="info">
            <template #header>
                <t-space>
                    <span>查看数据</span>
                </t-space>
            </template>
            <div class="query-form">
                <t-form :data="dialogFormData" layout="vertical">
                    <t-form-item label="光口业务速率" name="businessSpeed">
                        <t-textarea v-model="dialogFormData.businessSpeed" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="业务类型" name="businessType">
                        <t-textarea v-model="dialogFormData.businessType" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="操作人" name="operator_person">
                        <t-input v-model="dialogFormData.operator_person" :readonly="true"/>
                    </t-form-item>
                    <t-form-item label="更新时间" name="update_time">
                        <t-input v-model="dialogFormData.update_time" :readonly="true"/>
                    </t-form-item>
                    <t-form-item label="状态" name="status">
                        <t-tag :theme="dialogFormData.status === '正常' ? 'success' : 'danger'" size="small">{{ dialogFormData.status }}</t-tag>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="queryDialogVisible=false">关闭</t-button>
            </template>
        </t-dialog>

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
                    <p class="file-size">文件大小: {{ pubFormatFileSize(fileList[0].size) }}</p>
                </div>
                <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
                <div class="example-download">
                <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
                    <t-space wrap="false" class="example-space">
                        <p>请按照示例文件格式填写数据</p>
                        <t-button
                        variant="text"
                        theme="primary"
                        @click="pubDownloadExampleFile('/templates/electric_business_business_type_example.xlsx', '光口业务速率&业务类型批量导入示例.xlsx')"
                        class="example-btn">
                        <t-icon name="download" size="16" class="mr-1" />
                        下载导入示例文件
                        </t-button>
                    </t-space>
                </div>
            </div>
            <template #footer>
                <t-button @click="cancelImportSubmit">取消</t-button>
                <t-button @click="handleImportSubmit" :loading="importLoading">确认导入</t-button>
            </template>
        </t-dialog>
    </div>
</template>


<script setup lang="jsx">
import { ref, onMounted, nextTick } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { pubFormatFileSize, pubDownloadExampleFile, pubCalculateTableHeight } from '@/utils/pub';
import { queryBusinessSpeedTypeByParams, queryBusinessSpeedTypeStatusList, queryBusinessSpeedTypeBusinessSpeedList, queryBusinessSpeedTypeBusinessTypeList,
         addBusinessSpeedTypeData, updateBusinessSpeedTypeData, deleteBusinessSpeedTypeData, importExcelbaseBusinessSpeedTypeData} from '@/api/electric.js';


const router = useRouter();
const user = useUserStore();

// 固定数据
const uploadKey = ref(0);
// 表格配置
const tableRef = ref();
const tableColumnList = [
    {
        colKey: 'row-select',
        type: 'multiple',
        width: '50',
        checkProps: ({row}) => ({ disabled: row.status !== '正常', title: row.status !== '正常' ? '不可选' : null }),
    },
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'businessSpeed', title: () => (<div style={{ textAlign: 'center' }}>光口业务速率</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'businessType', title: () => (<div style={{ textAlign: 'center' }}>业务类型</div>), minWidth: '800', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'operator_person', title: '操作人', width: '200', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },
    {
        colKey: 'status',
        title: '数据状态',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (<t-tag theme={row.status === '正常' ? 'success' : 'danger'} size="small">{row.status}</t-tag>)
    },
    {
        colKey: 'edit',
        title: '操作',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (
            <>
            <t-link theme="primary" hover="color" onClick={() => openQueryDialog(row)} style={{ marginRight: '8px' }}>查看</t-link>
            {row.status === '正常' && (<t-link theme="primary" hover="color" onClick={() => openEditDialog(row)}>修改</t-link>)}
            </>
        )
    }
];

// 原始数据和筛选后数据
const tableDataList = ref([]);

// 表格选择相关
const selectedRowKeyList = ref([]);

// 级联选择器相关
const selectedBusinessSpeedOptionList = ref([]);

// 数据状态选择相关
const selectedStatusOptionList = ref([]);
const statusOptionList = ref([]);

// 后端查询的选择器选项
const allBusinessSpeedOptionList = ref([]);
const allBusinessTypeOptionList = ref([]);

// 修改相关
const editDialogVisible = ref(false);
const editForm = ref();
const dialogFormData = ref({
    businessSpeed: '',
    selectedBusinessTypeList: [],
});

// 查询相关
const queryDialogVisible = ref(false);

// 新增相关
const addDialogVisible = ref(false);
const addFormRef = ref(null);

// 删除相关
const deleteDialogTitle = ref('删除数据');
const deleteDialogVisible = ref(false);
const deleteRowIds = ref([]);

// 导入相关变量
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

const tableHeight = ref('900px');


// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('请先登录...');
        router.push('/login');
    }
    try {
        await refreshData();

        tableHeight.value = pubCalculateTableHeight();

    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
});

// 筛选数据
const filterData = async () => {
    try {
        const businessSpeed = [...new Set(selectedBusinessSpeedOptionList.value)].join(',');
        const status = selectedStatusOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (businessSpeed) requestParams.businessSpeed = businessSpeed;
        if (status) requestParams.status = status;

        // 发送请求
        const queryBusinessSpeedTypeByParamsResponse = await queryBusinessSpeedTypeByParams(requestParams);
        tableDataList.value = queryBusinessSpeedTypeByParamsResponse.data || [];

        // 处理结果提示
        const message = tableDataList.value.length > 0 ? `共找到 ${tableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[tableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选
const resetFilters = () => {
    selectedBusinessSpeedOptionList.value = [];
    selectedStatusOptionList.value = [];
    filterData();
    MessagePlugin.info('已重置筛选条件');
};

// 选中事件处理
const handleSelectChange = (keys) => {
    selectedRowKeyList.value = keys;
};

const refreshData = async () => {
    selectedBusinessSpeedOptionList.value = [];
    selectedStatusOptionList.value = [];
    selectedRowKeyList.value = [];

    const [
        queryBusinessSpeedTypeByParamsResponse,
        queryBusinessSpeedTypeStatusListResponse,
        queryBusinessSpeedTypeBusinessSpeedListResponse,
    ] = await Promise.all([
        queryBusinessSpeedTypeByParams(),
        queryBusinessSpeedTypeStatusList(),
        queryBusinessSpeedTypeBusinessSpeedList(),
    ]);

    tableDataList.value = queryBusinessSpeedTypeByParamsResponse.data || [];
    statusOptionList.value = queryBusinessSpeedTypeStatusListResponse.data || [];
    allBusinessSpeedOptionList.value = queryBusinessSpeedTypeBusinessSpeedListResponse.data || [];
}


// 修改相关方法
const openEditDialog = async (row) => {
    let selectedBusinessTypeList = row.businessType.split(',')

    dialogFormData.value = {
        id: row.id,
        businessSpeed: row.businessSpeed,
        selectedBusinessTypeList: selectedBusinessTypeList,
    };

    let queryBusinessSpeedTypeBusinessTypeListResponse = await queryBusinessSpeedTypeBusinessTypeList({"businessSpeed": row.businessSpeed});
    allBusinessTypeOptionList.value = queryBusinessSpeedTypeBusinessTypeListResponse.data || [];

    editDialogVisible.value = true;
};

const handleEditConfirm = async () => {
    if (!dialogFormData.value.businessSpeed) {
        MessagePlugin.warning('请选择或创建光口业务速率');
        return;
    }
    if (!dialogFormData.value.selectedBusinessTypeList || dialogFormData.value.selectedBusinessTypeList.length === 0) {
        MessagePlugin.warning('请选择选择或创建业务类型');
        return;
    }

    let updatedData = {
        ...dialogFormData.value,
        id: String(dialogFormData.value.id),
        businessType: dialogFormData.value.selectedBusinessTypeList.join(',')
    };

    try {
        let updateBusinessSpeedTypeDataResponse = await updateBusinessSpeedTypeData(updatedData);

        await refreshData();

        editDialogVisible.value = false;
        MessagePlugin.success(updateBusinessSpeedTypeDataResponse.message);
    } catch (error) {
        console.log('修改失败，请重试', error);
    }
};

const handleEditCancel = () => {
    editDialogVisible.value = false;
};

// 查看相关方法
const openQueryDialog = async (row) => {
    dialogFormData.value = {
        ...row
    };
    queryDialogVisible.value = true;
};

// 新增相关方法
const openAddDialog = async () => {
    dialogFormData.value = {
        businessSpeed: '',
        selectedBusinessTypeList: []
    };
    addDialogVisible.value = true;
};

const handleAddConfirm = async () => {
    // 新增表单校验（必填项）
    if (!dialogFormData.value.businessSpeed) {
        MessagePlugin.warning('请选择或创建光口业务速率');
        return;
    }
    if (!dialogFormData.value.selectedBusinessTypeList || dialogFormData.value.selectedBusinessTypeList.length === 0) {
        MessagePlugin.warning('请选择或创建业务类型');
        return;
    }

    // 处理新增数据
    const newRow = {
        ...dialogFormData.value,
        businessType: dialogFormData.value.selectedBusinessTypeList.join(',')
    };

    try {
        let addBusinessSpeedTypeDataResponse = await addBusinessSpeedTypeData(newRow);

        await refreshData();

        addDialogVisible.value = false;
        MessagePlugin.success(addBusinessSpeedTypeDataResponse.message);
    } catch (error) {
        console.log('新增失败，请重试', error);
    }
};

const handleAddCancel = () => {
    addDialogVisible.value = false;
};

// 删除相关方法
const onBatchDelete = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要删除的行');
        return;
    }

    deleteRowIds.value = selectedRowKeyList.value;
    deleteDialogTitle.value = `删除 ${selectCount} 条数据`;

    nextTick(() => deleteDialogVisible.value = true);
};

const handleDeleteConfirm = async () => {
    try {
        const deletedCount = deleteRowIds.value.length;
        await deleteBusinessSpeedTypeData({"id": deleteRowIds.value.join(',')});

        await refreshData();

        deleteDialogVisible.value = false;
        MessagePlugin.success(`成功删除 ${deletedCount} 条数据`);
    } catch (error) {
        console.log('删除失败，请重试', error);
    }
};

const handleCreateBusinessSpeedOption = (value) => {
    if (!allBusinessSpeedOptionList.value.includes(value)) {
        allBusinessSpeedOptionList.value.push(value);
    }
}

const handleCreateBusinessTypeOption = (value) => {
    if (!allBusinessTypeOptionList.value.includes(value)) {
        allBusinessTypeOptionList.value.push(value);
    }
}


// 修改原有批量导入方法
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

const resetUploadData = () => {
    // 1. 清空文件列表
    fileList.value = []
    // 2. 重置上传组件（如果已挂载）
    uploadKey.value++
};

const cancelImportSubmit = () => {
    resetUploadData()
    importDialogVisible.value = false
};

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
        const response = await importExcelbaseBusinessSpeedTypeData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        await refreshData();

        importDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = '批量导入失败';
    }
    uploadKey.value++
    importLoading.value = false;
};


// 批量导出实现
const onBatchOutput = async () => {
    // 判断是否有数据可导出
    if (tableDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }
    try {
        // 处理导出数据（映射表格列与数据）
        const exportData = tableDataList.value.map((row, index) => ({
            '编号': index + 1,
            '光口业务速率': row.businessSpeed || '',
            '业务类型': row.businessType || '',
            '操作人': row.operator_person || '',
            '更新时间': row.update_time || '',
            '数据状态': row.status || ''
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },  // 编号
            { wch: 15 }, // 光口业务速率
            { wch: 20 }, // 业务类型
            { wch: 12 }, // 关联版本号
            { wch: 15 }, // 操作人
            { wch: 20 }, // 更新时间
            { wch: 10 }  // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '光口业务速率&业务类型批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate =
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `光口业务速率&业务类型批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

const handleBusinessSpeedChange = async (value) => {
    dialogFormData.value.selectedBusinessTypeList = []
    let queryBusinessSpeedTypeBusinessTypeListResponse = await queryBusinessSpeedTypeBusinessTypeList({"businessSpeed": value});
    allBusinessTypeOptionList.value = queryBusinessSpeedTypeBusinessTypeListResponse.data || [];
}
</script>


<style scoped>
.dialog-content {
    padding: 16px;
    line-height: 1.5;
    min-height: 40px;
}

.dialog-content p {
    white-space: pre-line;
    margin: 0;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid #e0e0e0;
}

.query-form,
.edit-form,
.add-form {
    padding: 16px 0;
    max-height: 500px;
    overflow-y: auto;
}

.scene-main {
    /* 基础表格样式 */
    table {
        border-collapse: collapse;
        white-space: pre-line;
    }

    /* 表头样式 */
    th {
        background-color: #e7e7e7;
        color: #333;
        white-space: nowrap; /* 防止表头换行 */
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e0e0e0;
        border-left: none;
        border-right: none;
        line-height: 1.4; /* 紧凑行高 */
    }

    /* 单元格样式 */
    td {
        background-color: #fefefe;
        border-bottom: 1px solid #d6d6d6;
        color: #555;
        line-height: 1.4;
        border-left: none;
        border-right: none;
    }

    /* 奇偶行颜色区分 */
    tr:nth-child(even) td {
        background-color: #f8f8f8;
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

.error-message {
    color: #ff4d4f;
    padding: 8px 0;
    min-height: 24px;
}

/* 导入相关样式补充 */
/* 示例文件说明与下载按钮的容器样式 */
.example-download {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed #e5e6eb;
}

.example-space {
  display: flex; /* 水平布局 */
  align-items: center; /* 垂直居中对齐 */
  gap: 12px; /* 元素间间距，可根据需要调整 */
}

.example-space p {
  margin: 0; /* 清除默认外边距 */
  color: #666; /* 可选：调整文字颜色 */
  font-size: 14px; /* 与按钮文字大小保持一致 */
}

.example-btn {
  font-size: 14px; /* 与说明文字大小统一 */
}

.example-btn {
    padding-left: 0;
    display: inline-flex;
    align-items: center;
}

.mr-1 {
    margin-right: 4px;
}

.file-size {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
}
</style>
