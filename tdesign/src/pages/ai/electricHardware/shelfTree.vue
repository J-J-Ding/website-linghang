<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
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
        :columns="updateColumnList"
        :data="filterDataList"
        :selected-row-keys="selectedRowKeyList"
        :select-on-row-click="false"
        :max-height="tableHeight"
        active-row-type="multiple"
        :hover="true"
        bordered
        resizable
        :filter-value="filterValue"
        @select-change="handleSelectChange"
        @filter-change="onFilterChange">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-table>

        <t-dialog
        v-model:visible="addDialogVisible"
        :width="800"
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
                <t-form ref="addFormRef" :data="dialogFormData" layout="vertical" label-width="250px">
                    <t-form-item label="* 子架名称" name="shelf">
                        <t-input v-model="dialogFormData.shelf" placeholder="请填写子架名称"/>
                    </t-form-item>
                    <t-form-item
                    v-for="field in allFactorOptionList"
                    :key="field"
                    :label="`${field}`"
                    :name="field">
                        <t-select
                        v-model="dialogFormData[field]"
                        :placeholder="`请选择${field}`"
                        filterable
                        multiple
                        :min-collapsed-num="1"
                        :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }">
                            <t-option
                            v-for="option in allFactorValueDict[field]"
                            :key="option"
                            :value="option"
                            :label="option"/>
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
        :width="800"
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
                <t-form ref="editForm" :data="dialogFormData" layout="vertical" label-width="250px">
                    <t-form-item label="* 子架名称" name="shelf">
                        <t-input v-model="dialogFormData.shelf" placeholder="请填写子架名称" />
                    </t-form-item>
                    <t-form-item
                    v-for="field in allFactorOptionList"
                    :key="field"
                    :label="`${field}`"
                    :name="field">
                        <t-select
                        v-model="dialogFormData[field]"
                        :placeholder="`请选择${field}`"
                        filterable
                        multiple
                        :min-collapsed-num="1"
                        :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }">>
                            <t-option
                            v-for="option in allFactorValueDict[field]"
                            :key="option"
                            :value="option"
                            :label="option"/>
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
        :width="800"
        theme="info">
            <template #header>
                <t-space>
                    <span>查看数据</span>
                </t-space>
            </template>
            <div class="query-form">
                <t-form :data="queryFormData" layout="vertical" label-width="250px">
                    <t-form-item label="子架名称" name="shelf">
                        <t-textarea v-model="queryFormData.shelf" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item
                    v-for="field in allFactorOptionList"
                    :key="field"
                    :label="field"
                    :name="field">
                        <t-textarea v-model="queryFormData[field]" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="操作人" name="operator_person">
                        <t-input v-model="queryFormData.operator_person" :readonly="true"/>
                    </t-form-item>
                    <t-form-item label="更新时间" name="update_time">
                        <t-input v-model="queryFormData.update_time" :readonly="true"/>
                    </t-form-item>
                    <t-form-item label="状态" name="status">
                        <t-tag :theme="queryFormData.status === '正常' ? 'success' : 'danger'" size="small">{{ queryFormData.status }}</t-tag>
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
                        @click="pubDownloadExampleFile('/templates/electric_hardware_shelf_tree_example.xlsx', '子架树批量导入示例.xlsx')"
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
import { ref, onMounted, nextTick, markRaw } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin, Select } from 'tdesign-vue-next';
import { pubFormatFileSize, pubDownloadExampleFile, pubCalculateTableHeight } from '@/utils/pub';
import { queryShelfTreeByParams, queryShelfTreeFactorList, queryShelfTreeFactorValueDict, queryShelfTreeAllFactorValueDict, addShelfTreeData,
         updateShelfTreeData, deleteShelfTreeData, importExcelShelfTreeData } from '@/api/electric.js';


const router = useRouter();
const user = useUserStore();

// 固定数据
const uploadKey = ref(0);
// 表格配置
const tableRef = ref();
const tableColumnList = ref([
    {
        colKey: 'row-select',
        type: 'multiple',
        width: '50',
        checkProps: ({row}) => ({ disabled: row.status !== '正常', title: row.status !== '正常' ? '不可选' : null }),
    },
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'shelf', title: () => (<div style={{ textAlign: 'center' }}>子架名称</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
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
]);
const updateColumnList = ref([])

// 原始数据和筛选后数据
const tableDataList = ref([]);
const filterDataList = ref([]);

// 表格选择相关
const selectedRowKeyList = ref([]);

// 后端查询的选择器选项
const allFactorOptionList = ref([]);
const allFactorValueDict = ref({});

const filterValue = ref({});

// 修改相关
const currentEditId = ref(null);
const editDialogVisible = ref(false);
const editForm = ref();
const dialogFormData = ref({
    shelf: '',
});

// 查询相关
const queryDialogVisible = ref(false);
const queryFormData = ref({});

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
        MessagePlugin.error(`数据加载失败，请重试`);
    }
});

// 选中事件处理
const handleSelectChange = (keys) => {
    selectedRowKeyList.value = keys;
};

const refreshData = async () => {
    selectedRowKeyList.value = [];

    const [
        queryShelfTreeByParamsResponse,
        queryShelfTreeFactorListResponse,
        queryShelfTreeAllFactorValueDictResponse,
    ] = await Promise.all([
        queryShelfTreeByParams(),
        queryShelfTreeFactorList(),
        queryShelfTreeAllFactorValueDict(),
    ]);

    tableDataList.value = queryShelfTreeByParamsResponse.data || [];
    allFactorOptionList.value = queryShelfTreeFactorListResponse.data || [];
    allFactorValueDict.value = queryShelfTreeAllFactorValueDictResponse.data || {};
    filterDataList.value = tableDataList.value

    dynamicUpdateColumn();
}

const dynamicUpdateColumn = () => {
    const factorValueDict = ref({});

    // 辅助函数：统计字段中各值的出现次数（包括空字符串）
    function countValues(dataList, field) {
        const countMap = new Map();
        dataList.forEach(item => {
            let values = item[field];
            let valueArray = [];

            if (values === null || values === undefined) {
                return;
            }

            if (typeof values === 'string') {
                valueArray = values.split(',');
            } else if (Array.isArray(values)) {
                valueArray = values;
            } else {
                valueArray = [String(values)];
            }

            valueArray.forEach(val => {
                const countKey = val;
                countMap.set(countKey, (countMap.get(countKey) || 0) + 1);
            });
        });
        return countMap;
    }

    // 1. 处理 shelf 字段
    const shelfCountMap = countValues(filterDataList.value, 'shelf');
    factorValueDict.value["shelf"] = Array.from(shelfCountMap.entries()).map(([value, count]) => {
        const displayLabel = value === '' ? `(空) (${count})` : `${value} (${count})`;
        return {
            label: displayLabel,
            value: value
        };
    });

    // 2. 处理 status 字段
    const statusCountMap = countValues(filterDataList.value, 'status');
    factorValueDict.value["status"] = Array.from(statusCountMap.entries()).map(([value, count]) => {
        const displayLabel = value === '' ? `(空) (${count})` : `${value} (${count})`;
        return {
            label: displayLabel,
            value: value
        };
    });

    // 3. 处理每个 factor 字段
    allFactorOptionList.value.forEach(factor => {
        const valueCountMap = countValues(filterDataList.value, factor);
        factorValueDict.value[factor] = Array.from(valueCountMap.entries()).map(([value, count]) => {
            const displayLabel = value === '' ? `(空) (${count})` : `${value} (${count})`;
            return {
                label: displayLabel,
                value: value
            };
        });
    });

    updateColumnList.value = tableColumnList.value
    const shelfIndex = updateColumnList.value.findIndex(col => col.colKey === 'shelf');
    const statusIndex = updateColumnList.value.findIndex(col => col.colKey === 'status');
    if (shelfIndex === -1 || statusIndex === -1) {
        return null;
    }
    // 更新子架筛选
    updateColumnList.value[shelfIndex]['filter'] = {
        component: markRaw(Select),
        props: {
            options: [
                { label: '全选', checkAll: true },
                ...factorValueDict.value.shelf.map(item => ({
                    label: item['label'],
                    value: item['value'],
                }))
            ],
            placeholder: '请选择子架',
            multiple: true,
            filterable: true,
            clearable: true,
        },
        showConfirmAndReset: true,
    }

    // 增加数据状态筛选
    updateColumnList.value[statusIndex]['filter'] = {
        component: markRaw(Select),
        props: {
            options: [
                { label: '全选', checkAll: true },
                ...factorValueDict.value.status.map(item => ({
                    label: item['label'],
                    value: item['value'],
                }))
            ],
            placeholder: '请选择数据状态',
            multiple: true,
            filterable: true,
            clearable: true,
        },
        showConfirmAndReset: true,
    }
    // 插入因子列
    const newColumns = allFactorOptionList.value.map((item) => {
        const filterOptionList = factorValueDict.value[item] || [];
        const filterList = [
            { label: '全选', checkAll: true },
            ...filterOptionList.map(optionItem => ({
                label: optionItem['label'],
                value: optionItem['value'],
            })),
        ];
        return {
            colKey: item,
            title: () => (<div style={{ textAlign: 'center' }}>{item}</div>),
            width: '200',
            align: 'left',
            ellipsis: { theme: 'light', placement: 'bottom' },
            filter: {
                component: markRaw(Select),
                props: {
                    options: filterList,
                    placeholder: `请选择${item}`,
                    multiple: true,
                    filterable: true,
                    clearable: true,
                },
                showConfirmAndReset: true,
            },
        };
    });
    const newTableColumns = [...updateColumnList.value];
    newTableColumns.splice(shelfIndex + 1, 0, ...newColumns);
    updateColumnList.value = newTableColumns;
    return null;
};

const onFilterChange = (filters, ctx) => {
    const cleanedFilters = Object.fromEntries(
        Object.entries(filters).filter(([key, value]) =>
            !Array.isArray(value) || value.length > 0
        )
    );
    filterValue.value = {
        ...cleanedFilters,
    };
    filterData(cleanedFilters);
};

const filterData = (filters) => {
    const timer = setTimeout(() => {
        clearTimeout(timer);
        const newData = tableDataList.value.filter((item) => {
            let result = true;
            // 根据子架名称过滤
            if (result && filters["shelf"] && filters["shelf"].length > 0) {
                result = filters["shelf"].some(selectedValue => item['shelf']===selectedValue);
            }
            // 如果已经不匹配，可以提前退出循环
            if (!result) {
                return result;
            }
            // 根据数据状态过滤
            if (result && filters["status"] && filters["status"].length > 0) {
                result = filters["status"].some(selectedValue => item['status']===selectedValue);
            }
            // 如果已经不匹配，可以提前退出循环
            if (!result) {
                return result;
            }
            // 遍历所有因子选项进行过滤
            for (let i = 0; i < allFactorOptionList.value.length; i++) {
                const factorKey = allFactorOptionList.value[i];
                // 检查该因子是否在filters中存在且有选中值
                if (result && filters[factorKey] && filters[factorKey].length > 0) {
                    // 获取当前行的该因子值
                    const itemValues = item[factorKey] ? item[factorKey].split(',') : [''];
                    // 检查是否有任意一个选中的值包含在当前行中
                    result = filters[factorKey].some(selectedValue => itemValues.includes(selectedValue));
                }
                // 如果已经不匹配，可以提前退出循环
                if (!result) {
                    break;
                }
            }
            return result;
        });
        filterDataList.value = newData;
        dynamicUpdateColumn();
    }, 100);
};

// 修改相关方法
const openEditDialog = async (row) => {
    currentEditId.value = row.id;
    dialogFormData.value = {
        id: row.id,
        shelf: row.shelf,
    };

    allFactorOptionList.value.forEach(field => {
        dialogFormData.value[field] = row[field]?row[field].split(','):[]
    });

    editDialogVisible.value = true;
};

const handleEditConfirm = async () => {
    if (!dialogFormData.value.shelf) {
        MessagePlugin.warning('请填写子架');
        return;
    }

    let updatedData = {
        ...dialogFormData.value,
        id: String(dialogFormData.value.id),
    };

    allFactorOptionList.value.forEach(field => {
        updatedData[field] = dialogFormData.value[field].join(',');
    });

    try {
        let updateShelfTreeDataResponse = await updateShelfTreeData(updatedData);
        MessagePlugin.success(updateShelfTreeDataResponse.message);
        await refreshData();
        editDialogVisible.value = false;
    } catch (error) {
        console.log('修改失败，请重试', error);
    }
};

const handleEditCancel = () => {
    editDialogVisible.value = false;
};

// 查看相关方法
const openQueryDialog = async (row) => {
    queryFormData.value = {
        ...row
    };

    allFactorOptionList.value.forEach(field => {
        queryFormData.value[field] = row[field]
    });

    queryDialogVisible.value = true;
};

// 新增相关方法
const openAddDialog = async () => {
    dialogFormData.value = {
        shelf: '',
    };

    allFactorOptionList.value.forEach(field => {
        dialogFormData.value[field] = [];
    });

    addDialogVisible.value = true;
};

const handleAddConfirm = async () => {
    // 必填校验 - 子架名称
    if (!dialogFormData.value.shelf) {
        MessagePlugin.warning('请填写子架名称');
        return;
    }

    // 构造提交数据，动态处理 allFactorOptionList 字段
    const newRow = {
        ...dialogFormData.value,
    };

    allFactorOptionList.value.forEach(field => {
        newRow[field] = dialogFormData.value[field].join(',');
    });

    try {
        let addShelfTreeDataResponse = await addShelfTreeData(newRow);

        await refreshData();

        addDialogVisible.value = false;
        MessagePlugin.success(addShelfTreeDataResponse.message);
    } catch (error) {
        console.error('新增失败，请重试', error);
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
        const deleteIdSet = new Set(deleteRowIds.value);
        let deleteRowshelfs = [];

        for (const item of filterDataList.value) {
            if (deleteIdSet.has(item.id)) {
                deleteRowshelfs.push(item.shelf);
            }
        }
        await deleteShelfTreeData({"shelf": deleteRowshelfs.join(',')});
        await refreshData();

        deleteDialogVisible.value = false;
        MessagePlugin.success(`成功删除 ${deletedCount} 条数据`);
    } catch (error) {
        console.log('删除失败，请重试', error);
    }
};

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
        const response = await importExcelShelfTreeData(formData);

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
    if (filterDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }
    try {
        // 处理导出数据（映射表格列与数据）
        const exportData = filterDataList.value.map((row, index) => ({
            '编号': index + 1,
            '子架名称': row.shelf || '',
            ...Object.fromEntries(allFactorOptionList.value.map(field => [
                field, row[field] || ''
            ])),
            '操作人': row.operator_person || '',
            '更新时间': row.update_time || '',
            '数据状态': row.status || ''
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },   // 编号
            { wch: 15 },  // 子架名称
            ...allFactorOptionList.value.map(field => ({ wch: 20 })), // 动态字段
            { wch: 12 },  // 关联版本号
            { wch: 15 },  // 操作人
            { wch: 20 },  // 更新时间
            { wch: 10 }   // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '子架树批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate =
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `子架树批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};
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
    height: 500px;
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
