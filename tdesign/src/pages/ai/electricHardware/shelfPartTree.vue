<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-select
                v-model="selectedProductList"
                filterable
                clearable
                multiple
                :min-collapsed-num="1"
                style="width: 250px;"
                placeholder="请选择产品"
                label="产品: "
                @change="() => updateProductShelfType()">
                    <t-option v-for="option in allProductOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="selectedShelfTypeList"
                filterable
                clearable
                multiple
                :min-collapsed-num="1"
                style="width: 300px;"
                placeholder="请选择子架类型"
                label="子架类型: "
                @change="() => updateProductShelfType()">
                    <t-option v-for="option in allShelfTypeOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-cascader
                v-model="selectedPartBusinessSchemeList"
                :options="partBusinessSchemeTreeList"
                :filter="pubFilterTreeOptionFun"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                value-type="full"
                style="width: 300px;"
                placeholder="请选择部件业务方案"
                label="部件业务方案: ">
                    <template #suffixIcon>
                        <t-popup destroy-on-close placement="top-left">
                            <template #content>
                                <div>1、支持模糊搜索<br/>2、多级搜索用$分隔，如：$一级选项$二级选项</div>
                            </template>
                            <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                        </t-popup>
                    </template>
                </t-cascader>
                <t-select
                v-model="selectedStatusOptionList"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                style="width: 200px;"
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
        :max-height="tableHeight"
        active-row-type="multiple"
        :hover="true"
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
                    <t-form-item label="* 所属产品" name="product">
                        <t-select
                        v-model="dialogFormData.product"
                        placeholder="请选择所属产品"
                        filterable>
                            <t-option v-for="option in allProductOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 子架类型" name="shelfType">
                        <t-select
                        v-model="dialogFormData.shelfType"
                        placeholder="请选择子架类型"
                        filterable>
                            <t-option v-for="option in allShelfTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 部件" name="part">
                        <t-select
                        v-model="dialogFormData.part"
                        placeholder="请选择或创建部件"
                        creatable
                        filterable
                        :disabled="false"
                        @change="handlePartChange"
                        :onCreate="handleCreatePartOption">
                            <t-option v-for="option in allPartOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 部件业务方案" name="businessScheme">
                        <t-select
                        v-model="dialogFormData.businessScheme"
                        placeholder="请选择或创建部件业务方案"
                        creatable
                        filterable
                        :disabled="!dialogFormData.part"
                        @change="handleBusinessSchemeChange"
                        :onCreate="handleCreateBusinessSchemeOption">
                            <t-option v-for="option in allBusinessSchemeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 业务方案切片" name="schemeSlice">
                        <t-select
                        v-model="dialogFormData.schemeSlice"
                        placeholder="请选择或创建业务方案切片"
                        creatable
                        filterable
                        :disabled="!dialogFormData.businessScheme">
                            <t-option v-for="option in allSchemeSliceOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="切片详情链接" name="schemeSliceDetailLink">
                        <t-input v-model="dialogFormData.schemeSliceDetailLink" placeholder="请输入业务方案切片详情链接" :disabled="!dialogFormData.businessScheme"/>
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
                <t-form ref="editForm" :data="dialogFormData" layout="vertical" >
                    <t-form-item label="* 所属产品" name="product">
                        <t-select
                        v-model="dialogFormData.product"
                        placeholder="请选择所属产品"
                        filterable>
                            <t-option v-for="option in allProductOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 子架类型" name="shelfType">
                        <t-select
                        v-model="dialogFormData.shelfType"
                        placeholder="请选择子架类型"
                        filterable>
                            <t-option v-for="option in allShelfTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 部件" name="part">
                        <t-select
                        v-model="dialogFormData.part"
                        creatable
                        filterable
                        placeholder="请选择或创建部件"
                        @change="handlePartChange"
                        :onCreate="handleCreatePartOption">
                            <t-option v-for="option in allPartOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 部件业务方案" name="businessScheme">
                        <t-select
                        v-model="dialogFormData.businessScheme"
                        creatable
                        filterable
                        placeholder="请选择或创建部件业务方案"
                        :disabled="!dialogFormData.part"
                        @change="handleBusinessSchemeChange"
                        :onCreate="handleCreateBusinessSchemeOption">
                            <t-option v-for="option in allBusinessSchemeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="* 业务方案切片" name="schemeSlice">
                        <t-select
                        v-model="dialogFormData.schemeSlice"
                        placeholder="请选择或创建业务方案切片"
                        creatable
                        filterable
                        :disabled="!dialogFormData.businessScheme">
                            <t-option v-for="item in allSchemeSliceOptionList" :key="item"  :value="item"  :label="item"/>
                        </t-select>
                    </t-form-item>
                    <t-form-item label="切片详情链接" name="schemeSliceDetailLink">
                        <t-input v-model="dialogFormData.schemeSliceDetailLink" placeholder="请输入业务方案切片详情链接" :disabled="!dialogFormData.businessScheme" />
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
                    <t-form-item label="部件" name="part">
                        <t-textarea v-model="dialogFormData.part" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="部件业务方案" name="businessScheme">
                        <t-textarea v-model="dialogFormData.businessScheme" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="业务方案切片" name="schemeSlice">
                        <t-textarea v-model="dialogFormData.schemeSlice" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="切片详情链接" name="schemeSliceDetailLink">
                        <t-link
                        :href="dialogFormData.schemeSliceDetailLink"
                        target="_blank"
                        theme="primary"
                        :style="{display: 'inline-block', width: '100%', wordBreak: 'break-all', whiteSpace: 'normal',}"
                        :title="dialogFormData.schemeSliceDetailLink">
                            {{ dialogFormData.schemeSliceDetailLink }}
                        </t-link>
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
                        @click="pubDownloadExampleFile('/templates/electric_hardware_shelf_part_tree_example.xlsx', '子架部件树批量导入示例.xlsx')"
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
import { pubFormatFileSize, pubDownloadExampleFile, pubCalculateTableHeight, pubBuildTreeWithText, pubFilterTreeOptionFun } from '@/utils/pub';
import { queryShelfPartTreeByParams, queryShelfPartTreeTree, queryShelfPartTreeStatusList, queryShelfPartTreeProductList, queryShelfPartTreeShelfTypeList,
         queryShelfPartTreePartList, queryShelfPartTreeBusinessSchemeList, queryShelfPartTreeSchemeSliceList, addShelfPartTreeData, updateShelfPartTreeData,
         deleteShelfPartTreeData, importExcelShelfPartTreeData} from '@/api/electric.js';


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
    { colKey: 'product', title: () => (<div style={{ textAlign: 'center' }}>所属产品</div>),  width: '150', align: 'left' },
    { colKey: 'shelfType', title: () => (<div style={{ textAlign: 'center' }}>子架类型</div>), width: '150', align: 'left' },
    { colKey: 'part', title: () => (<div style={{ textAlign: 'center' }}>部件</div>), width: '150', align: 'left' },
    { colKey: 'businessScheme', title: () => (<div style={{ textAlign: 'center' }}>部件业务方案</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'schemeSlice', title: () => (<div style={{ textAlign: 'center' }}>业务方案切片</div>), minWidth: '600', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: 'schemeSliceDetailLink',
        title: () => (<div style={{ textAlign: 'center' }}>业务方案切片详情链接</div>),
        width: '200',
        align: 'center',
        ellipsis: { theme: 'light', placement: 'bottom',},
        cell: (_, { row }) => (<t-link theme="primary" href={row.schemeSliceDetailLink} target="_blank" hover="underline">{row.schemeSliceDetailLink}</t-link>)
    },
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
const selectedProductList = ref([]);
const selectedShelfTypeList = ref([]);
const selectedPartBusinessSchemeList = ref([]);
const partBusinessSchemeTreeList = ref([]);

// 数据状态选择相关
const selectedStatusOptionList = ref([]);
const statusOptionList = ref([]);

// 后端查询的选择器选项
const allProductOptionList = ref([]);
const allShelfTypeOptionList = ref([]);
const allPartOptionList = ref([]);
const allBusinessSchemeOptionList = ref([]);
const allSchemeSliceOptionList = ref([]);

// 修改相关
const currentEditId = ref(null);
const editDialogVisible = ref(false);
const editForm = ref();
const dialogFormData = ref({
    part: '',
    businessScheme: '',
    schemeSlice: '',
    schemeSliceDetailLink: '',
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
        // 提取和处理参数
        const partList = selectedPartBusinessSchemeList.value.map(item => item[0]);
        const businessSchemeList = selectedPartBusinessSchemeList.value.map(item => item[1]);

        const product = selectedProductList.value.join(',');
        const shelfType = selectedShelfTypeList.value.join(',');
        const part = [...new Set(partList)].join(',');
        const businessScheme = [...new Set(businessSchemeList)].join(',');
        const status = selectedStatusOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (product) requestParams.product = product;
        if (shelfType) requestParams.shelfType = shelfType;
        if (part) requestParams.part = part;
        if (businessScheme) requestParams.businessScheme = businessScheme;
        if (status) requestParams.status = status;

        // 发送请求
        const queryShelfPartTreeByParamsResponse = await queryShelfPartTreeByParams(requestParams);
        tableDataList.value = queryShelfPartTreeByParamsResponse.data || [];

        // 处理结果提示
        const message = tableDataList.value.length > 0 ? `共找到 ${tableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[tableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选
const resetFilters = () => {
    selectedProductList.value = [];
    selectedShelfTypeList.value = [];
    selectedPartBusinessSchemeList.value = [];
    selectedStatusOptionList.value = [];
    filterData();
    MessagePlugin.info('已重置筛选条件');
};

// 选中事件处理
const handleSelectChange = (keys) => {
    selectedRowKeyList.value = keys;
};


const refreshData = async () => {
    selectedProductList.value = [];
    selectedShelfTypeList.value = [];
    selectedPartBusinessSchemeList.value = [];
    selectedStatusOptionList.value = [];
    selectedRowKeyList.value = [];

    const [
        queryShelfPartTreeTreeResponse,
        queryShelfPartTreeByParamsResponse,
        queryShelfPartTreeStatusListResponse,
        queryShelfPartTreeProductListResponse,
        queryShelfPartTreeShelfTypeListResponse,
        queryShelfPartTreePartListResponse,
    ] = await Promise.all([
        queryShelfPartTreeTree({"product": selectedProductList.value.join(','), "shelfType": selectedShelfTypeList.value.join(',')}),
        queryShelfPartTreeByParams(),
        queryShelfPartTreeStatusList(),
        queryShelfPartTreeProductList(),
        queryShelfPartTreeShelfTypeList(),
        queryShelfPartTreePartList(),
    ]);

    partBusinessSchemeTreeList.value = pubBuildTreeWithText(queryShelfPartTreeTreeResponse.data || []);
    tableDataList.value = queryShelfPartTreeByParamsResponse.data || [];
    statusOptionList.value = queryShelfPartTreeStatusListResponse.data || [];
    allProductOptionList.value = queryShelfPartTreeProductListResponse.data || [];
    allShelfTypeOptionList.value = queryShelfPartTreeShelfTypeListResponse.data || [];
    allPartOptionList.value = queryShelfPartTreePartListResponse.data || [];
}


const updateProductShelfType = async () => {
    try {
        const response = await queryShelfPartTreeTree({"product": selectedProductList.value.join(','), "shelfType": selectedShelfTypeList.value.join(',')});
        const dataList = response?.data || [];
        partBusinessSchemeTreeList.value = pubBuildTreeWithText(dataList);
    } catch (error) {
        console.error(error);
        partBusinessSchemeTreeList.value = [];
    }
};


// 修改相关方法
const openEditDialog = async (row) => {
    currentEditId.value = row.id;
    dialogFormData.value = {
        id: row.id,
        product: row.product,
        shelfType: row.shelfType,
        part: row.part,
        businessScheme: row.businessScheme,
        schemeSlice: row.schemeSlice,
        schemeSliceDetailLink: row.schemeSliceDetailLink,
    };

    let queryShelfPartTreeBusinessSchemeListResponse = await queryShelfPartTreeBusinessSchemeList({"part": row.part});
    allBusinessSchemeOptionList.value = queryShelfPartTreeBusinessSchemeListResponse.data || [];

    // 查询业务方案切片列表
    let queryShelfPartTreeSchemeSliceListResponse = await queryShelfPartTreeSchemeSliceList({"businessScheme": dialogFormData.value.businessScheme});
    allSchemeSliceOptionList.value = queryShelfPartTreeSchemeSliceListResponse.data || [];

    editDialogVisible.value = true;
};

const handleEditConfirm = async () => {
    if (!dialogFormData.value.product) {
        MessagePlugin.warning('请选择所属产品');
        return;
    }
    if (!dialogFormData.value.shelfType) {
        MessagePlugin.warning('请选择子架类型');
        return;
    }
    if (!dialogFormData.value.part) {
        MessagePlugin.warning('请选择或创建部件');
        return;
    }
    if (!dialogFormData.value.businessScheme) {
        MessagePlugin.warning('请选择选择或创建部件业务方案');
        return;
    }
    if (!dialogFormData.value.schemeSlice) {
        MessagePlugin.warning('请选择或创建业务方案切片');
        return;
    }

    let updatedData = {
        ...dialogFormData.value,
        id: String(dialogFormData.value.id),
    };

    try {
        let updateShelfPartTreeDataResponse = await updateShelfPartTreeData(updatedData);

        await refreshData();

        editDialogVisible.value = false;
        MessagePlugin.success(updateShelfPartTreeDataResponse.message);
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
        product: '',
        shelfType: '',
        part: '',
        businessScheme: '',
        schemeSlice: '',
        schemeSliceDetailLink: '',
    };
    addDialogVisible.value = true;
};

const handleAddConfirm = async () => {
    // 新增表单校验（必填项）
    if (!dialogFormData.value.product) {
        MessagePlugin.warning('请选择所属产品');
        return;
    }
    if (!dialogFormData.value.shelfType) {
        MessagePlugin.warning('请选择子架类型');
        return;
    }
    if (!dialogFormData.value.part) {
        MessagePlugin.warning('请选择或创建部件');
        return;
    }
    if (!dialogFormData.value.businessScheme) {
        MessagePlugin.warning('请选择或创建部件业务方案');
        return;
    }
    if (!dialogFormData.value.schemeSlice) {
        MessagePlugin.warning('请选择或创建业务方案切片');
        return;
    }

    // 处理新增数据
    const newRow = {
        ...dialogFormData.value,
    };

    try {
        let addShelfPartTreeDataResponse = await addShelfPartTreeData(newRow);

        await refreshData();

        addDialogVisible.value = false;
        MessagePlugin.success(addShelfPartTreeDataResponse.message);
    } catch (error) {
        console.log('新增失败，请重试', error);
    }
};

const handleAddCancel = () => {
    addDialogVisible.value = false;
};

const handleCreatePartOption = (value) => {
    if (!allPartOptionList.value.includes(value)) {
        allPartOptionList.value.push(value);
    }
}

const handleCreateBusinessSchemeOption = (value) => {
    if (!allBusinessSchemeOptionList.value.includes(value)) {
        allBusinessSchemeOptionList.value.push(value);
    }
}

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
        await deleteShelfPartTreeData({"id": deleteRowIds.value.join(',')});

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
        const response = await importExcelShelfPartTreeData(formData);

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
            '部件': row.part || '',
            '部件业务方案': row.businessScheme || '',
            '业务方案切片': row.schemeSlice || '',
            '业务方案切片详情链接': row.schemeSliceDetailLink || '',
            '操作人': row.operator_person || '',
            '更新时间': row.update_time || '',
            '数据状态': row.status || ''
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },  // 编号
            { wch: 15 }, // 部件
            { wch: 20 }, // 部件业务方案
            { wch: 30 }, // 业务方案切片
            { wch: 25 }, // 业务方案切片详情链接
            { wch: 12 }, // 关联版本号
            { wch: 15 }, // 操作人
            { wch: 20 }, // 更新时间
            { wch: 10 }  // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '子架部件树批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate = 
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `子架部件树批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

const handlePartChange = async (value) => {
    dialogFormData.value.businessScheme = ""
    dialogFormData.value.schemeSlice = ""
    dialogFormData.value.schemeSliceDetailLink = ""
    let queryShelfPartTreeBusinessSchemeListResponse = await queryShelfPartTreeBusinessSchemeList({"part": value});
    allBusinessSchemeOptionList.value = queryShelfPartTreeBusinessSchemeListResponse.data || [];
    if (allBusinessSchemeOptionList.value.length > 0) {
        dialogFormData.value.businessScheme = allBusinessSchemeOptionList.value[0];
    }
    let queryShelfPartTreeSchemeSliceListResponse = await queryShelfPartTreeSchemeSliceList({"businessScheme": dialogFormData.value.businessScheme});
    allSchemeSliceOptionList.value = queryShelfPartTreeSchemeSliceListResponse.data || [];
    if (allSchemeSliceOptionList.value.length > 0) {
        dialogFormData.value.schemeSlice = allSchemeSliceOptionList.value[0];
    }
}

const handleBusinessSchemeChange = async (value) => {
    dialogFormData.value.schemeSlice = ""
    dialogFormData.value.schemeSliceDetailLink = ""
    let queryShelfPartTreeSchemeSliceListResponse = await queryShelfPartTreeSchemeSliceList({"businessScheme": dialogFormData.value.businessScheme});
    allSchemeSliceOptionList.value = queryShelfPartTreeSchemeSliceListResponse.data || [];
    if (allSchemeSliceOptionList.value.length > 0) {
        dialogFormData.value.schemeSlice = allSchemeSliceOptionList.value[0];
    }
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
