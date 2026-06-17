<template>
    <div class="scene-main">
        <t-tabs v-model="tabValue" theme="card">
            <t-tab-panel value="单板原子模型表" label="单板原子模型表">
                <p>&nbsp;</p>
                <t-space direction="vertical">
                <t-space>
                    <t-cascader
                    v-model="selectedAtomBoardBusinessList"
                    :options="atomBoardBusinessTreeList"
                    :filter="pubFilterTreeOptionFun"
                    multiple
                    filterable
                    clearable
                    :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                    :min-collapsed-num="1"
                    value-type="full"
                    style="width: 600px;"
                    placeholder="请选择单板原子模型"
                    label="单板原子模型: ">
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
                    v-model="selectedAtomStatusOptionList"
                    multiple
                    filterable
                    clearable
                    :min-collapsed-num="1"
                    style="width: 300px;"
                    placeholder="请选择数据状态"
                    label="数据状态: ">
                        <t-option v-for="option in atomStatusOptionList" :key="option" :value="option" :label="option" />
                    </t-select>
                    <t-button @click="filterAtomData">筛选</t-button>
                    <t-button @click="resetAtomFilters">重置</t-button>
                    <t-button @click="openAtomAddDialog">新增</t-button>
                    <t-button @click="onAtomBatchDelete">批量删除</t-button>
                    <t-button @click="onAtomBatchImport">批量导入</t-button>
                    <t-button @click="onAtomBatchOutput">批量导出</t-button>
                </t-space>
                <p> </p>
                </t-space>
                <t-table
                ref="atomTableRef"
                row-key="id"
                active-row-type="multiple"
                :columns="atomTableColumnList"
                :data="atomTableDataList"
                :selected-row-keys="selectedAtomRowKeyList"
                :select-on-row-click="false"
                :max-height="tableHeight"
                :bordered="true"
                :hover="true"
                resizable
                @select-change="handleAtomSelectChange">
                    <template #index="{ rowIndex }">
                        <span>{{ rowIndex + 1 }}</span>
                    </template>
                </t-table>

                <t-dialog
                v-model:visible="addAtomDialogVisible"
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
                        <t-form ref="addAtomFormRef" :data="atomDialogFormData" layout="vertical" label-width="120px">
                            <t-form-item label="* 单板分类" name="boardBusinessType">
                                <t-select
                                v-model="atomDialogFormData.boardBusinessType"
                                placeholder="请选择单板分类"
                                creatable
                                filterable
                                :disabled="false"
                                @change="handleAtomBoardBusinessTypeChange">
                                    <t-option v-for="option in allAtomBoardBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="* 单板原子模型" name="boardBusiness">
                                <t-select
                                v-model="atomDialogFormData.boardBusiness"
                                placeholder="请选择单板原子模型"
                                creatable
                                filterable
                                :disabled="!atomDialogFormData.boardBusinessType">
                                    <t-option v-for="option in allAtomBoardBusinessOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="单板模型描述" name="boardBusinessDescribe">
                                <t-input v-model="atomDialogFormData.boardBusinessDescribe" placeholder="请输入单板模型描述"/>
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="handleAtomAddCancel">取消</t-button>
                        <t-button @click="handleAtomAddConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="deleteAtomDialogVisible"
                :width="700"
                @confirm="handleAtomDeleteConfirm"
                @cancel="deleteAtomDialogVisible = false"
                theme="warning">
                    <template #header>
                        <t-space>
                            <span>{{ deleteAtomDialogTitle }}</span>
                            <t-tooltip
                            content="提交后数据将进入审核流程, 审核通过后将正式生效。"
                            placement="top-left">
                                <HelpCircleFilledIcon size="1em" />
                            </t-tooltip>
                        </t-space>
                    </template>
                    <t-space direction="vertical" style="width: 100%">
                        <t-form  layout="vertical">
                            <p>本次删除 {{ selectedAtomRowKeyList.length}} 条数据，是否提交审核？</p>
                        </t-form>
                    </t-space>
                    <template #footer>
                        <t-button @click="deleteAtomDialogVisible = false">取消</t-button>
                        <t-button @click="handleAtomDeleteConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="editAtomDialogVisible"
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
                        <t-form ref="editAtomForm" :data="atomDialogFormData" layout="vertical" label-width="120px">
                            <t-form-item label="* 单板分类" name="boardBusinessType">
                                <t-select
                                v-model="atomDialogFormData.boardBusinessType"
                                creatable
                                filterable
                                placeholder="请选择单板分类"
                                @change="handleAtomBoardBusinessTypeChange">
                                    <t-option v-for="option in allAtomBoardBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="* 单板原子模型" name="boardBusiness">
                                <t-select
                                v-model="atomDialogFormData.boardBusiness"
                                creatable
                                filterable
                                placeholder="请选择单板原子模型"
                                :disabled="!atomDialogFormData.boardBusinessType">
                                    <t-option v-for="option in allAtomBoardBusinessOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="单板模型描述" name="boardBusinessDescribe">
                                <t-input v-model="atomDialogFormData.boardBusinessDescribe" placeholder="请输入单板模型描述" />
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="handleAtomEditCancel">取消</t-button>
                        <t-button @click="handleAtomEditConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="importAtomDialogVisible"
                :width="600"
                theme="warning"
                header="批量导入数据">
                    <div class="import-container">
                        <t-upload
                        ref="atomUploadRef"
                        :key="uploadKey"
                        :auto-upload="false"
                        :on-change="handleAtomFileChange"
                        :file-list="atomFileList"
                        :max-size="10 * 1024 * 1024"
                        :allow-multiple="false"
                        accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        class="upload-component">
                            <t-button variant="outline">选择XLSX文件</t-button>
                        </t-upload>

                        <div v-if="atomFileList.length > 0" class="file-info">
                            <p>已选择文件: {{ atomFileList[0].name }}</p>
                            <p class="file-size">文件大小: {{ formatFileSize(atomFileList[0].size) }}</p>
                        </div>
                        <div v-if="atomUploadError" class="error-message">{{ atomUploadError }}</div>
                        <div class="example-download">
                        <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
                            <t-space wrap="false" class="example-space">
                                <p>请按照示例文件格式填写数据</p>
                                <t-button
                                variant="text"
                                theme="primary"
                                @click="downloadAtomExampleFile"
                                class="example-btn">
                                <t-icon name="download" size="16" class="mr-1" />
                                下载导入示例文件
                                </t-button>
                            </t-space>
                        </div>
                    </div>
                    <template #footer>
                        <t-button @click="cancelAtomImportSubmit">取消</t-button>
                        <t-button @click="handleAtomImportSubmit" :loading="atomImportLoading">确认导入</t-button>
                    </template>
                </t-dialog>
                <t-dialog
                v-model:visible="queryAtomDialogVisible"
                :width="700"
                theme="info">
                    <template #header>
                        <t-space>
                            <span>查看数据</span>
                        </t-space>
                    </template>
                    <div class="query-form">
                        <t-form :data="dialogAtomFormData" layout="vertical" label-width="120px">
                            <t-form-item label="单板分类" name="boardBusinessType">
                                <t-input v-model="dialogAtomFormData.boardBusinessType" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="单板原子模型" name="boardBusiness">
                                <t-input v-model="dialogAtomFormData.boardBusiness" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="单板模型描述" name="boardBusinessDescribe">
                                <t-textarea v-model="dialogAtomFormData.boardBusinessDescribe" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="操作人" name="operator_person">
                                <t-input v-model="dialogAtomFormData.operator_person" :readonly="true"/>
                            </t-form-item>
                            <t-form-item label="更新时间" name="update_time">
                                <t-input v-model="dialogAtomFormData.update_time" :readonly="true"/>
                            </t-form-item>
                            <t-form-item label="数据状态" name="status">
                                <!-- <t-input v-model="dialogAtomFormData.status" :readonly="true"/> -->
                                <t-tag :theme="dialogAtomFormData.status === '正常' ? 'success' : 'danger'" size="small">{{ dialogAtomFormData.status }}</t-tag>
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="queryAtomDialogVisible=false">关闭</t-button>
                    </template>
                </t-dialog>
            </t-tab-panel>
            <t-tab-panel value="单板模型表" label="单板模型表">
                <p>&nbsp;</p>
                <t-space direction="vertical">
                <t-space>
                    <t-cascader
                    v-model="selectedGroupBoardBusinessList"
                    :options="groupBoardBusinessTreeList"
                    :filter="pubFilterTreeOptionFun"
                    multiple
                    filterable
                    clearable
                    :min-collapsed-num="1"
                    value-type="full"
                    style="width: 600px;"
                    placeholder="请选择单板模型"
                    label="单板模型: ">
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
                    v-model="selectedGroupStatusOptionList"
                    multiple
                    filterable
                    clearable
                    :min-collapsed-num="1"
                    style="width: 300px;"
                    placeholder="请选择数据状态"
                    label="数据状态: ">
                        <t-option v-for="option in groupStatusOptionList" :key="option" :value="option" :label="option" />
                    </t-select>
                    <t-button @click="filterGroupData">筛选</t-button>
                    <t-button @click="resetGroupFilters">重置</t-button>
                    <t-button @click="openGroupAddDialog">新增</t-button>
                    <t-button @click="onGroupBatchDelete">批量删除</t-button>
                    <t-button @click="onGroupBatchImport">批量导入</t-button>
                    <t-button @click="onGroupBatchOutput">批量导出</t-button>
                </t-space>
                <p> </p>
                </t-space>
                <t-table
                ref="groupTableRef"
                row-key="id"
                active-row-type="multiple"
                :columns="groupTableColumnList"
                :data="groupTableDataList"
                :selected-row-keys="selectedGroupRowKeyList"
                :select-on-row-click="false"
                :max-height="tableHeight"
                :bordered="true"
                :hover="true"
                @select-change="handleGroupSelectChange">
                    <template #index="{ rowIndex }">
                        <span>{{ rowIndex + 1 }}</span>
                    </template>
                </t-table>

                <t-dialog
                v-model:visible="addGroupDialogVisible"
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
                        <t-form ref="addGroupFormRef" :data="groupDialogFormData" layout="vertical" label-width="140px">
                            <t-form-item label="* 单板分类" name="boardBusinessType">
                                <t-select
                                v-model="groupDialogFormData.boardBusinessType"
                                placeholder="请选择单板分类"
                                creatable
                                filterable
                                :disabled="false"
                                @change="handleGroupBoardBusinessTypeChange">
                                    <t-option v-for="option in allGroupBoardBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="* 单板模型" name="selectedBoardBusinessList">
                                <t-select
                                v-model="groupDialogFormData.selectedBoardBusinessList"
                                placeholder="请选择单板模型"
                                filterable
                                clearable
                                multiple
                                :min-collapsed-num="1"
                                :disabled="!groupDialogFormData.boardBusinessType">
                                    <t-option v-for="option in allGroupBoardBusinessOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="单板模型组合描述" name="boardBusinessDescribe">
                                <t-input v-model="groupDialogFormData.boardBusinessDescribe" placeholder="请输入单板模型组合描述"/>
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="handleGroupAddCancel">取消</t-button>
                        <t-button @click="handleGroupAddConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="deleteGroupDialogVisible"
                :width="700"
                @confirm="handleGroupDeleteConfirm"
                @cancel="deleteGroupDialogVisible = false"
                theme="warning">
                    <template #header>
                        <t-space>
                            <span>{{ deleteGroupDialogTitle }}</span>
                            <t-tooltip
                            content="提交后数据将进入审核流程, 审核通过后将正式生效。"
                            placement="top-left">
                                <HelpCircleFilledIcon size="1em" />
                            </t-tooltip>
                        </t-space>
                    </template>
                    <t-space direction="vertical" style="width: 100%">
                        <t-form  layout="vertical">
                            <p>本次删除 {{ selectedGroupRowKeyList.length}} 条数据，是否提交审核？</p>
                        </t-form>
                    </t-space>
                    <template #footer>
                        <t-button @click="deleteGroupDialogVisible = false">取消</t-button>
                        <t-button @click="handleGroupDeleteConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="editGroupDialogVisible"
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
                        <t-form ref="editGroupForm" :data="groupDialogFormData" layout="vertical" label-width="140px">
                            <t-form-item label="* 单板分类" name="boardBusinessType">
                                <t-select
                                v-model="groupDialogFormData.boardBusinessType"
                                creatable
                                filterable
                                placeholder="请选择单板分类"
                                @change="handleGroupBoardBusinessTypeChange">
                                    <t-option v-for="option in allGroupBoardBusinessTypeOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="* 单板模型" name="selectedBoardBusinessList">
                                <t-select
                                v-model="groupDialogFormData.selectedBoardBusinessList"
                                filterable
                                clearable
                                multiple
                                :min-collapsed-num="1"
                                placeholder="请选择单板模型"
                                :disabled="!groupDialogFormData.boardBusinessType">
                                    <t-option v-for="option in allGroupBoardBusinessOptionList" :key="option" :value="option" :label="option" />
                                </t-select>
                            </t-form-item>
                            <t-form-item label="单板模型组合描述" name="boardBusinessDescribe">
                                <t-input v-model="groupDialogFormData.boardBusinessDescribe" placeholder="请输入单板模型组合描述" />
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="handleGroupEditCancel">取消</t-button>
                        <t-button @click="handleGroupEditConfirm">提交审核</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="importGroupDialogVisible"
                :width="600"
                theme="warning"
                header="批量导入数据">
                    <div class="import-container">
                        <t-upload
                        ref="groupUploadRef"
                        :key="uploadGroupKey"
                        :auto-upload="false"
                        :on-change="handleGroupFileChange"
                        :file-list="groupFileList"
                        :max-size="10 * 1024 * 1024"
                        :allow-multiple="false"
                        accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        class="upload-component">
                            <t-button variant="outline">选择XLSX文件</t-button>
                        </t-upload>

                        <div v-if="groupFileList.length > 0" class="file-info">
                            <p>已选择文件: {{ groupFileList[0].name }}</p>
                            <p class="file-size">文件大小: {{ formatFileSize(groupFileList[0].size) }}</p>
                        </div>
                        <div v-if="groupUploadError" class="error-message">{{ groupUploadError }}</div>
                        <div class="example-download">
                        <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
                            <t-space wrap="false" class="example-space">
                                <p>请按照示例文件格式填写数据</p>
                                <t-button
                                variant="text"
                                theme="primary"
                                @click="downloadGroupExampleFile"
                                class="example-btn">
                                <t-icon name="download" size="16" class="mr-1" />
                                下载导入示例文件
                                </t-button>
                            </t-space>
                        </div>
                    </div>
                    <template #footer>
                        <t-button @click="cancelGroupImportSubmit">取消</t-button>
                        <t-button @click="handleGroupImportSubmit" :loading="groupImportLoading">确认导入</t-button>
                    </template>
                </t-dialog>

                <t-dialog
                v-model:visible="queryAtomDialogVisible"
                :width="700"
                theme="info">
                    <template #header>
                        <t-space>
                            <span>查看数据</span>
                        </t-space>
                    </template>
                    <div class="query-form">
                        <t-form :data="dialogAtomFormData" layout="vertical" label-width="120px">
                            <t-form-item label="单板分类" name="boardBusinessType">
                                <t-input v-model="dialogAtomFormData.boardBusinessType" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="单板模型" name="boardBusiness">
                                <t-input v-model="dialogAtomFormData.boardBusiness" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="单板模型组合描述" name="boardBusinessDescribe">
                                <t-textarea v-model="dialogAtomFormData.boardBusinessDescribe" :readonly="true" autosize/>
                            </t-form-item>
                            <t-form-item label="操作人" name="operator_person">
                                <t-input v-model="dialogAtomFormData.operator_person" :readonly="true"/>
                            </t-form-item>
                            <t-form-item label="更新时间" name="update_time">
                                <t-input v-model="dialogAtomFormData.update_time" :readonly="true"/>
                            </t-form-item>
                            <t-form-item label="数据状态" name="status">
                                <!-- <t-input v-model="dialogAtomFormData.status" :readonly="true"/> -->
                                <t-tag :theme="dialogAtomFormData.status === '正常' ? 'success' : 'danger'" size="small">{{ dialogAtomFormData.status }}</t-tag>
                            </t-form-item>
                        </t-form>
                    </div>
                    <template #footer>
                        <t-button @click="queryAtomDialogVisible=false">关闭</t-button>
                    </template>
                </t-dialog>
            </t-tab-panel>
        </t-tabs>
    </div>
</template>


<script setup lang="jsx">
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { pubBuildTreeWithText, pubFilterTreeOptionFun } from '@/utils/pub';
import { queryBoardBusinessAtomByParams, queryBoardBusinessAtomTree, queryBoardBusinessAtomStatusList, queryBoardBusinessAtomBoardBusinessTypeList,
         queryBoardBusinessAtomBoardBusinessList, addBoardBusinessAtomData, updateBoardBusinessAtomData, deleteBoardBusinessAtomData, importExcelData,
         queryBoardBusinessGroupByParams, queryBoardBusinessGroupTree, queryBoardBusinessGroupStatusList, queryBoardBusinessGroupBoardBusinessTypeList,
         queryBoardBusinessGroupBoardBusinessList, addBoardBusinessGroupData, updateBoardBusinessGroupData, deleteBoardBusinessGroupData, importExcelBoardAtomModelData, importExcelBoardGroupModelData } from '@/api/electric.js';


const router = useRouter();
const user = useUserStore();

// 固定数据
const tabValue = ref("单板原子模型表")
const uploadKey = ref(0);
const uploadGroupKey = ref(0);
// 表格配置
const atomTableRef = ref();
const atomTableColumnList = [
    {
        colKey: 'row-select',
        type: 'multiple',
        width: '50',
        checkProps: ({row}) => ({ disabled: row.status !== '正常', title: row.status !== '正常' ? '不可选' : null }),
    },
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'boardBusinessType', title: () => (<div style={{ textAlign: 'center' }}>单板分类</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardBusiness', title: () => (<div style={{ textAlign: 'center' }}>单板原子模型</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardBusinessDescribe', title: () => (<div style={{ textAlign: 'center' }}>单板模型描述</div>), width: '600', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
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
            <t-link theme="primary" hover="color" onClick={() => openAtomQueryDialog(row)} style={{ marginRight: '8px' }}>查看</t-link>
            {row.status === '正常' ? (<t-link theme="primary" hover="color" onClick={() => openAtomEditDialog(row)}>修改</t-link>):null}
            </>
        )
    }
];

// 原始数据和筛选后数据
const atomTableDataList = ref([]);

// 表格选择相关
const selectedAtomRowKeyList = ref([]);

// 级联选择器相关
const selectedAtomBoardBusinessList = ref([]);
const atomBoardBusinessTreeList = ref([]);

// 数据状态选择相关
const selectedAtomStatusOptionList = ref([]);
const atomStatusOptionList = ref([]);

// 后端查询的选择器选项
const allAtomBoardBusinessTypeOptionList = ref([]);
const allAtomBoardBusinessOptionList = ref([]);

// 修改相关
const currentAtomEditId = ref(null);
const editAtomDialogVisible = ref(false);
const editAtomForm = ref();
const atomDialogFormData = ref({
    boardBusinessType: '',
    boardBusiness: '',
    boardBusinessDescribe: '',
});

const dialogAtomFormData = ref({
    boardBusinessType: '',
    boardBusiness: '',
    boardBusinessDescribe: '',
    operator_person: '',
    update_time: '',
    status: ''
});

const queryAtomDialogVisible = ref(false);

// 新增相关
const addAtomDialogVisible = ref(false);
const addAtomFormRef = ref(null);

// 删除相关
const deleteAtomDialogTitle = ref('删除数据');
const deleteAtomDialogVisible = ref(false);
const deleteAtomRowIds = ref([]);

// 导入相关变量
const importAtomDialogVisible = ref(false);
const atomUploadRef = ref(null);
const atomFileList = ref([]);
const atomUploadError = ref('');
const atomImportLoading = ref(false);

const tableHeight = ref('900px');

const calculateTableHeight = () => {
  // 减去顶部筛选区域、页脚和其他元素的预估高度
  const offset = 270; // 根据实际情况调整这个值
  tableHeight.value = `${window.innerHeight - offset}px`;
};


// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('请先登录...');
        router.push('/login');
    }
    try {
        const [
            queryBoardBusinessAtomTreeResponse,
            queryBoardBusinessAtomByParamsResponse,
            queryBoardBusinessAtomStatusListResponse,
            queryBoardBusinessAtomBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessAtomTree(),
            queryBoardBusinessAtomByParams(),
            queryBoardBusinessAtomStatusList(),
            queryBoardBusinessAtomBoardBusinessTypeList(),
        ]);

        atomBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessAtomTreeResponse.data || []);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];
        atomStatusOptionList.value = queryBoardBusinessAtomStatusListResponse.data || [];
        allAtomBoardBusinessTypeOptionList.value = queryBoardBusinessAtomBoardBusinessTypeListResponse.data || [];

        const [
            queryBoardBusinessGroupTreeResponse,
            queryBoardBusinessGroupByParamsResponse,
            queryBoardBusinessGroupStatusListResponse,
            queryBoardBusinessGroupBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessGroupTree(),
            queryBoardBusinessGroupByParams(),
            queryBoardBusinessGroupStatusList(),
            queryBoardBusinessGroupBoardBusinessTypeList(),
        ]);

        groupBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessGroupTreeResponse.data || []);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];
        groupStatusOptionList.value = queryBoardBusinessGroupStatusListResponse.data || [];
        allGroupBoardBusinessTypeOptionList.value = queryBoardBusinessGroupBoardBusinessTypeListResponse.data || [];

        calculateTableHeight();
        window.addEventListener('resize', calculateTableHeight);
        

    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', calculateTableHeight);
});

const openAtomQueryDialog = async (row) => {
    queryAtomDialogVisible.value = true;
    dialogAtomFormData.value = {
        boardBusinessType: row.boardBusinessType,
        boardBusiness: row.boardBusiness,
        boardBusinessDescribe: row.boardBusinessDescribe,
        operator_person: row.operator_person,
        update_time: row.update_time,
        status: row.status
    };
};

// 筛选数据
const filterAtomData = async () => {
    try {
        // 提取和处理参数
        const elementList = selectedAtomBoardBusinessList.value.map(item => item[0]);
        const factorTypeList = selectedAtomBoardBusinessList.value.map(item => item[1]);

        const boardBusinessType = [...new Set(elementList)].join(',');
        const boardBusiness = [...new Set(factorTypeList)].join(',');
        const status = selectedAtomStatusOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (boardBusinessType) requestParams.boardBusinessType = boardBusinessType;
        if (boardBusiness) requestParams.boardBusiness = boardBusiness;
        if (status) requestParams.status = status;

        // 发送请求
        const queryBoardBusinessAtomByParamsResponse = await queryBoardBusinessAtomByParams(requestParams);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];

        // 处理结果提示
        const message = atomTableDataList.value.length > 0 ? `共找到 ${atomTableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[atomTableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选
const resetAtomFilters = () => {
    selectedAtomBoardBusinessList.value = [];
    selectedAtomStatusOptionList.value = [];
    filterAtomData();
    MessagePlugin.info('已重置筛选条件');
};

// 选中事件处理
const handleAtomSelectChange = (keys) => {
    selectedAtomRowKeyList.value = keys;
};


// 修改相关方法
const openAtomEditDialog = async (row) => {
    currentAtomEditId.value = row.id;
    atomDialogFormData.value = {
        id: row.id,
        boardBusinessType: row.boardBusinessType,
        boardBusiness: row.boardBusiness,
        boardBusinessDescribe: row.boardBusinessDescribe,
    };

    let queryBoardBusinessAtomBoardBusinessListResponse = await queryBoardBusinessAtomBoardBusinessList();
    allAtomBoardBusinessOptionList.value = queryBoardBusinessAtomBoardBusinessListResponse.data || [];

    editAtomDialogVisible.value = true;
};

const handleAtomEditConfirm = async () => {
    if (!atomDialogFormData.value.boardBusinessType) {
        MessagePlugin.warning('请选择或创建单板分类');
        return;
    }
    if (!atomDialogFormData.value.boardBusiness) {
        MessagePlugin.warning('请选择选择或创建单板原子模型');
        return;
    }

    let updatedData = {
        ...atomDialogFormData.value,
        id: String(atomDialogFormData.value.id),
    };

    try {
        let updateBoardBusinessAtomDataResponse = await updateBoardBusinessAtomData(updatedData);

        selectedAtomBoardBusinessList.value = [];
        selectedAtomStatusOptionList.value = [];
        selectedAtomRowKeyList.value = [];

        const [
            queryBoardBusinessAtomTreeResponse,
            queryBoardBusinessAtomByParamsResponse,
            queryBoardBusinessAtomBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessAtomTree(),
            queryBoardBusinessAtomByParams(),
            queryBoardBusinessAtomBoardBusinessTypeList(),
        ]);

        atomBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessAtomTreeResponse.data || []);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];
        allAtomBoardBusinessTypeOptionList.value = queryBoardBusinessAtomBoardBusinessTypeListResponse.data || [];

        editAtomDialogVisible.value = false;
        MessagePlugin.success(updateBoardBusinessAtomDataResponse.message);
    } catch (error) {
        console.log('修改失败，请重试', error);
    }
};

const handleAtomEditCancel = () => {
    editAtomDialogVisible.value = false;
};

// 新增相关方法
const openAtomAddDialog = async () => {
    atomDialogFormData.value = {
        boardBusinessType: '',
        boardBusiness: '',
        boardBusinessDescribe: '',
    };
    addAtomDialogVisible.value = true;
};

const handleAtomAddConfirm = async () => {
    // 新增表单校验（必填项）
    if (!atomDialogFormData.value.boardBusinessType) {
        MessagePlugin.warning('请选择或创建单板分类');
        return;
    }
    if (!atomDialogFormData.value.boardBusiness) {
        MessagePlugin.warning('请选择或创建单板原子模型');
        return;
    }

    // 处理新增数据
    const newRow = {
        ...atomDialogFormData.value,
    };

    try {
        let addBoardBusinessAtomDataResponse = await addBoardBusinessAtomData(newRow);

        selectedAtomBoardBusinessList.value = [];
        selectedAtomStatusOptionList.value = [];
        selectedAtomRowKeyList.value = [];

        const [
            queryBoardBusinessAtomTreeResponse,
            queryBoardBusinessAtomByParamsResponse,
            queryBoardBusinessAtomBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessAtomTree(),
            queryBoardBusinessAtomByParams(),
            queryBoardBusinessAtomBoardBusinessTypeList(),
        ]);

        atomBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessAtomTreeResponse.data || []);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];
        allAtomBoardBusinessTypeOptionList.value = queryBoardBusinessAtomBoardBusinessTypeListResponse.data || [];

        addAtomDialogVisible.value = false;
        MessagePlugin.success(addBoardBusinessAtomDataResponse.message);
    } catch (error) {
        console.log('新增失败，请重试', error);
    }
};

const handleAtomAddCancel = () => {
    addAtomDialogVisible.value = false;
};

// 删除相关方法
const onAtomBatchDelete = () => {
    const selectCount = selectedAtomRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要删除的行');
        return;
    }

    deleteAtomRowIds.value = selectedAtomRowKeyList.value;
    deleteAtomDialogTitle.value = `删除 ${selectCount} 条数据`;

    nextTick(() => deleteAtomDialogVisible.value = true);
};

const handleAtomDeleteConfirm = async () => {
    try {
        const deletedCount = deleteAtomRowIds.value.length;
        await deleteBoardBusinessAtomData({"id": deleteAtomRowIds.value.join(',')});

        selectedAtomBoardBusinessList.value = [];
        selectedAtomStatusOptionList.value = [];
        selectedAtomRowKeyList.value = [];

        const [
            queryBoardBusinessAtomTreeResponse,
            queryBoardBusinessAtomByParamsResponse,
            queryBoardBusinessAtomBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessAtomTree(),
            queryBoardBusinessAtomByParams(),
            queryBoardBusinessAtomBoardBusinessTypeList(),
        ]);

        atomBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessAtomTreeResponse.data || []);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];
        allAtomBoardBusinessTypeOptionList.value = queryBoardBusinessAtomBoardBusinessTypeListResponse.data || [];

        deleteAtomDialogVisible.value = false;
        MessagePlugin.success(`成功删除 ${deletedCount} 条数据`);
    } catch (error) {
        console.log('删除失败，请重试', error);
    }
};

// 修改原有批量导入方法
const onAtomBatchImport = () => {
    // 重置状态
    atomFileList.value = [];
    atomUploadError.value = '';
    importAtomDialogVisible.value = true;
};

// 处理文件选择变化
const handleAtomFileChange = (files) => {
    atomUploadError.value = '';
    atomFileList.value = files;

    // 验证文件格式
    if (files.length > 0) {
        const file = files[0];
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xlsx')) {
            atomUploadError.value = '文件格式错误，请选择.xlsx格式的文件';
            atomFileList.value = []; // 清空错误文件
        }
    }
};

// 格式化文件大小显示
const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};


const downloadAtomExampleFile = () => {
    try {
        /* Started by AICoder, pid:t904df8438jc0a214173098a500c7a0cf9e17880 */
        const exampleFilePath = '/templates/single_board_atomic_model.xlsx';
        /* Ended by AICoder, pid:t904df8438jc0a214173098a500c7a0cf9e17880 */
        // 创建下载链接
        const link = document.createElement('a');
        link.href = exampleFilePath;
        link.download = '单板原子模型表批量导入示例.xlsx'; // 指定下载文件名
        document.body.appendChild(link);
        link.click();
        // 清理
        document.body.removeChild(link);
        MessagePlugin.success('单板原子模型表批量导入示例文件下载成功，请查看下载文件');
    } catch (error) {
        console.error('单板原子模型表批量导入示例文件下载失败', error);
        MessagePlugin.error('单板原子模型表批量导入示例文件失败，请联系管理员');
    }
};

const resetAtomImportSubmit = () => {
    // 1. 清空文件列表
    atomFileList.value = []
    // 2. 重置上传组件（如果已挂载）
    uploadKey.value++
};

const cancelAtomImportSubmit = () => {
    resetAtomImportSubmit()
    importAtomDialogVisible.value = false
};


const handleAtomImportSubmit = async () => {
    if (atomFileList.value.length === 0) {
        atomUploadError.value = '请先选择文件';
        return;
    }

    if (atomUploadError.value) {
        return;
    }

    atomImportLoading.value = true;
    atomUploadError.value = '';

    try {
        const file = atomFileList.value[0];
        const formData = new FormData();

        // 构造表单数据
        formData.append('file', file.raw);

        // 调用后端批量导入接口
        const response = await importExcelBoardAtomModelData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        // 刷新表格数据
        const [
            queryBoardBusinessAtomTreeResponse,
            queryBoardBusinessAtomByParamsResponse,
            queryBoardBusinessAtomStatusListResponse,
            queryBoardBusinessAtomBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessAtomTree(),
            queryBoardBusinessAtomByParams(),
            queryBoardBusinessAtomStatusList(),
            queryBoardBusinessAtomBoardBusinessTypeList(),
        ]);

        atomBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessAtomTreeResponse.data || []);
        atomTableDataList.value = queryBoardBusinessAtomByParamsResponse.data || [];
        atomStatusOptionList.value = queryBoardBusinessAtomStatusListResponse.data || [];
        allAtomBoardBusinessTypeOptionList.value = queryBoardBusinessAtomBoardBusinessTypeListResponse.data || [];
        importAtomDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        atomUploadError.value = '批量导入失败';
    }
    uploadKey.value++
};


// 批量导出实现
const onAtomBatchOutput = async () => {
    // 判断是否有数据可导出
    if (atomTableDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }
    try {
        // 处理导出数据（映射表格列与数据）
        const exportData = atomTableDataList.value.map((row, index) => ({
            '编号': index + 1,
            '单板分类': row.boardBusinessType || '',
            '单板原子模型': row.boardBusiness || '',
            '单板模型描述': row.boardBusinessDescribe || '',
            '操作人': row.operator_person || '',
            '更新时间': row.update_time || '',
            '数据状态': row.status || ''
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },  // 编号
            { wch: 15 }, // 单板分类
            { wch: 20 }, // 单板原子模型
            { wch: 25 }, // 单板模型描述
            { wch: 12 }, // 关联版本号
            { wch: 15 }, // 操作人
            { wch: 20 }, // 更新时间
            { wch: 10 }  // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '单板原子模型批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate = 
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `单板业务模型批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

const handleAtomBoardBusinessTypeChange = async (value) => {
    atomDialogFormData.value.boardBusiness = ""
    atomDialogFormData.value.boardBusinessDescribe = ""
    let queryBoardBusinessAtomBoardBusinessListResponse = await queryBoardBusinessAtomBoardBusinessList({"boardBusinessType": value});
    allAtomBoardBusinessOptionList.value = queryBoardBusinessAtomBoardBusinessListResponse.data || [];
    if (allAtomBoardBusinessOptionList.value.length > 0) {
        atomDialogFormData.value.boardBusiness = allAtomBoardBusinessOptionList.value[0];
    }
}

// 表格配置
const groupTableRef = ref();
const groupTableColumnList = [
    {
        colKey: 'row-select',
        type: 'multiple',
        width: '50',
        checkProps: ({row}) => ({ disabled: row.status !== '正常', title: row.status !== '正常' ? '不可选' : null }),
    },
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'boardBusinessType', title: () => (<div style={{ textAlign: 'center' }}>单板分类</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardBusiness', title: () => (<div style={{ textAlign: 'center' }}>单板模型</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardBusinessDescribe', title: () => (<div style={{ textAlign: 'center' }}>单板模型组合描述</div>), width: '600', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
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
            <t-link theme="primary" hover="color" onClick={() => openAtomQueryDialog(row)} style={{ marginRight: '8px' }}>查看</t-link>
            {row.status === '正常' ? (<t-link theme="primary" hover="color" onClick={() => openGroupEditDialog(row)}>修改</t-link>):null}
            </>
        )
    }
];

// 原始数据和筛选后数据
const groupTableDataList = ref([]);

// 表格选择相关
const selectedGroupRowKeyList = ref([]);

// 级联选择器相关
const selectedGroupBoardBusinessList = ref([]);
const groupBoardBusinessTreeList = ref([]);

// 数据状态选择相关
const selectedGroupStatusOptionList = ref([]);
const groupStatusOptionList = ref([]);

// 后端查询的选择器选项
const allGroupBoardBusinessTypeOptionList = ref([]);
const allGroupBoardBusinessOptionList = ref([]);

// 修改相关
const currentGroupEditId = ref(null);
const editGroupDialogVisible = ref(false);
const editGroupForm = ref();
const groupDialogFormData = ref({
    boardBusinessType: '',
    selectedBoardBusinessList: [],
    boardBusinessDescribe: '',
});


// 新增相关
const addGroupDialogVisible = ref(false);
const addGroupFormRef = ref(null);

// 删除相关
const deleteGroupDialogTitle = ref('删除数据');
const deleteGroupDialogVisible = ref(false);
const deleteGroupRowIds = ref([]);

// 导入相关变量
const importGroupDialogVisible = ref(false);
const groupUploadRef = ref(null);
const groupFileList = ref([]);
const groupUploadError = ref('');
const groupImportLoading = ref(false);


// 筛选数据
const filterGroupData = async () => {
    try {
        // 提取和处理参数
        const elementList = selectedGroupBoardBusinessList.value.map(item => item[0]);
        const factorTypeList = selectedGroupBoardBusinessList.value.map(item => item[1]);

        const boardBusinessType = [...new Set(elementList)].join(',');
        const boardBusiness = [...new Set(factorTypeList)].join(',');
        const status = selectedGroupStatusOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (boardBusinessType) requestParams.boardBusinessType = boardBusinessType;
        if (boardBusiness) requestParams.boardBusiness = boardBusiness;
        if (status) requestParams.status = status;

        // 发送请求
        const queryBoardBusinessGroupByParamsResponse = await queryBoardBusinessGroupByParams(requestParams);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];

        // 处理结果提示
        const message = groupTableDataList.value.length > 0 ? `共找到 ${groupTableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[groupTableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选
const resetGroupFilters = () => {
    selectedGroupBoardBusinessList.value = [];
    selectedGroupStatusOptionList.value = [];
    filterGroupData();
    MessagePlugin.info('已重置筛选条件');
};

// 选中事件处理
const handleGroupSelectChange = (keys) => {
    selectedGroupRowKeyList.value = keys;
};


// 修改相关方法
const openGroupEditDialog = async (row) => {
    let selectedBoardBusinessList = row.boardBusiness.split('/')

    currentGroupEditId.value = row.id;
    groupDialogFormData.value = {
        id: row.id,
        boardBusinessType: row.boardBusinessType,
        selectedBoardBusinessList: selectedBoardBusinessList,
        boardBusinessDescribe: row.boardBusinessDescribe,
    };

    // let queryBoardBusinessGroupBoardBusinessListResponse = await queryBoardBusinessGroupBoardBusinessList();
    let queryBoardBusinessGroupBoardBusinessListResponse = await queryBoardBusinessAtomBoardBusinessList();
    allGroupBoardBusinessOptionList.value = queryBoardBusinessGroupBoardBusinessListResponse.data || [];

    editGroupDialogVisible.value = true;
};

const handleGroupEditConfirm = async () => {
    if (!groupDialogFormData.value.boardBusinessType) {
        MessagePlugin.warning('请选择或创建单板分类');
        return;
    }
    if (!groupDialogFormData.value.selectedBoardBusinessList || groupDialogFormData.value.selectedBoardBusinessList.length === 0) {
        MessagePlugin.warning('请选择选择或创建单板组合模型');
        return;
    }

    let updatedData = {
        ...groupDialogFormData.value,
        id: String(groupDialogFormData.value.id),
        boardBusiness: groupDialogFormData.value.selectedBoardBusinessList.join('|'),
    };

    try {
        let updateBoardBusinessGroupDataResponse = await updateBoardBusinessGroupData(updatedData);

        selectedGroupBoardBusinessList.value = [];
        selectedGroupStatusOptionList.value = [];
        selectedGroupRowKeyList.value = [];

        const [
            queryBoardBusinessGroupTreeResponse,
            queryBoardBusinessGroupByParamsResponse,
            queryBoardBusinessGroupBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessGroupTree(),
            queryBoardBusinessGroupByParams(),
            queryBoardBusinessGroupBoardBusinessTypeList(),
        ]);

        groupBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessGroupTreeResponse.data || []);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];
        allGroupBoardBusinessTypeOptionList.value = queryBoardBusinessGroupBoardBusinessTypeListResponse.data || [];

        editGroupDialogVisible.value = false;
        MessagePlugin.success(updateBoardBusinessGroupDataResponse.message);
    } catch (error) {
        console.log('修改失败，请重试', error);
    }
};

const handleGroupEditCancel = () => {
    editGroupDialogVisible.value = false;
};

// 新增相关方法
const openGroupAddDialog = async () => {
    groupDialogFormData.value = {
        boardBusinessType: '',
        boardBusiness: '',
        boardBusinessDescribe: '',
    };
    addGroupDialogVisible.value = true;
};

const handleGroupAddConfirm = async () => {
    // 新增表单校验（必填项）
    if (!groupDialogFormData.value.boardBusinessType) {
        MessagePlugin.warning('请选择或创建单板分类');
        return;
    }
    if (!groupDialogFormData.value.boardBusiness) {
        MessagePlugin.warning('请选择或创建单板组合模型');
        return;
    }

    // 处理新增数据
    const newRow = {
        ...groupDialogFormData.value,
        boardBusiness: groupDialogFormData.value.selectedBoardBusinessList.join('|'),
    };

    try {
        let addBoardBusinessGroupDataResponse = await addBoardBusinessGroupData(newRow);

        selectedGroupBoardBusinessList.value = [];
        selectedGroupStatusOptionList.value = [];
        selectedGroupRowKeyList.value = [];

        const [
            queryBoardBusinessGroupTreeResponse,
            queryBoardBusinessGroupByParamsResponse,
            queryBoardBusinessGroupBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessGroupTree(),
            queryBoardBusinessGroupByParams(),
            queryBoardBusinessGroupBoardBusinessTypeList(),
        ]);

        groupBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessGroupTreeResponse.data || []);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];
        allGroupBoardBusinessTypeOptionList.value = queryBoardBusinessGroupBoardBusinessTypeListResponse.data || [];

        addGroupDialogVisible.value = false;
        MessagePlugin.success(addBoardBusinessGroupDataResponse.message);
    } catch (error) {
        console.log('新增失败，请重试', error);
    }
};

const handleGroupAddCancel = () => {
    addGroupDialogVisible.value = false;
};

// 删除相关方法
const onGroupBatchDelete = () => {
    const selectCount = selectedGroupRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要删除的行');
        return;
    }

    deleteGroupRowIds.value = selectedGroupRowKeyList.value;
    deleteGroupDialogTitle.value = `删除 ${selectCount} 条数据`;

    nextTick(() => deleteGroupDialogVisible.value = true);
};

const handleGroupDeleteConfirm = async () => {
    try {
        const deletedCount = deleteGroupRowIds.value.length;
        await deleteBoardBusinessGroupData({"id": deleteGroupRowIds.value.join(',')});

        selectedGroupBoardBusinessList.value = [];
        selectedGroupStatusOptionList.value = [];
        selectedGroupRowKeyList.value = [];

        const [
            queryBoardBusinessGroupTreeResponse,
            queryBoardBusinessGroupByParamsResponse,
            queryBoardBusinessGroupBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessGroupTree(),
            queryBoardBusinessGroupByParams(),
            queryBoardBusinessGroupBoardBusinessTypeList(),
        ]);

        groupBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessGroupTreeResponse.data || []);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];
        allGroupBoardBusinessTypeOptionList.value = queryBoardBusinessGroupBoardBusinessTypeListResponse.data || [];

        deleteGroupDialogVisible.value = false;
        MessagePlugin.success(`成功删除 ${deletedCount} 条数据`);
    } catch (error) {
        console.log('删除失败，请重试', error);
    }
};

// 修改原有批量导入方法
const onGroupBatchImport = () => {
    // 重置状态
    groupFileList.value = [];
    groupUploadError.value = '';
    importGroupDialogVisible.value = true;
};

// 处理文件选择变化
const handleGroupFileChange = (files) => {
    groupUploadError.value = '';
    groupFileList.value = files;

    // 验证文件格式
    if (files.length > 0) {
        const file = files[0];
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xlsx')) {
            groupUploadError.value = '文件格式错误，请选择.xlsx格式的文件';
            groupFileList.value = []; // 清空错误文件
        }
    }
};


const downloadGroupExampleFile = () => {
    try {
        const exampleFilePath = '/templates/single_board_effective_model.xlsx';
        // 创建下载链接
        const link = document.createElement('a');
        link.href = exampleFilePath;
        link.download = '单板模型表批量导入示例.xlsx'; // 指定下载文件名
        document.body.appendChild(link);
        link.click();
        // 清理
        document.body.removeChild(link);
        MessagePlugin.success('单板模型表批量导入示例文件下载成功，请查看下载文件');
    } catch (error) {
        console.error('单板模型表批量导入示例文件下载失败', error);
        MessagePlugin.error('单板模型表批量导入示例文件失败，请联系管理员');
    }
};

const resetGroupImportSubmit = () => {
    // 1. 清空文件列表
    groupFileList.value = []
    // 2. 重置上传组件（如果已挂载）
    uploadGroupKey.value++
};

const cancelGroupImportSubmit = () => {
    resetGroupImportSubmit()
    importGroupDialogVisible.value = false
};

const handleGroupImportSubmit = async () => {
    if (groupFileList.value.length === 0) {
        groupUploadError.value = '请先选择文件';
        return;
    }

    if (groupUploadError.value) {
        return;
    }

    groupImportLoading.value = true;
    groupUploadError.value = '';

    try {
        const file = groupFileList.value[0];
        const formData = new FormData();

        // 构造表单数据
        formData.append('file', file.raw);

        // 调用后端批量导入接口
        const response = await importExcelBoardGroupModelData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        // 刷新表格数据
        const [
            queryBoardBusinessGroupTreeResponse,
            queryBoardBusinessGroupByParamsResponse,
            queryBoardBusinessGroupStatusListResponse,
            queryBoardBusinessGroupBoardBusinessTypeListResponse,
        ] = await Promise.all([
            queryBoardBusinessGroupTree(),
            queryBoardBusinessGroupByParams(),
            queryBoardBusinessGroupStatusList(),
            queryBoardBusinessGroupBoardBusinessTypeList(),
        ]);

        groupBoardBusinessTreeList.value = pubBuildTreeWithText(queryBoardBusinessGroupTreeResponse.data || []);
        groupTableDataList.value = queryBoardBusinessGroupByParamsResponse.data || [];
        groupStatusOptionList.value = queryBoardBusinessGroupStatusListResponse.data || [];
        allGroupBoardBusinessTypeOptionList.value = queryBoardBusinessGroupBoardBusinessTypeListResponse.data || [];
        importGroupDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        groupUploadError.value = '批量导入失败';
    }
    uploadGroupKey.value++
};


// 批量导出实现
const onGroupBatchOutput = async () => {
    // 判断是否有数据可导出
    if (groupTableDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }
    try {
        // 处理导出数据（映射表格列与数据）
        const exportData = groupTableDataList.value.map((row, index) => ({
            '编号': index + 1,
            '单板分类': row.boardBusinessType || '',
            '单板模型': row.boardBusiness || '',
            '单板模型组合描述': row.boardBusinessDescribe || '',
            '操作人': row.operator_person || '',
            '更新时间': row.update_time || '',
            '数据状态': row.status || ''
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },  // 编号
            { wch: 15 }, // 单板分类
            { wch: 20 }, // 单板模型
            { wch: 25 }, // 单板模型描述
            { wch: 12 }, // 关联版本号
            { wch: 15 }, // 操作人
            { wch: 20 }, // 更新时间
            { wch: 10 }  // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '单板模型批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate = 
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `单板业务模型批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

const handleGroupBoardBusinessTypeChange = async (value) => {
    groupDialogFormData.value.boardBusiness = ""
    groupDialogFormData.value.boardBusinessDescribe = ""
    // let queryBoardBusinessGroupBoardBusinessListResponse = await queryBoardBusinessGroupBoardBusinessList({"boardBusinessType": value});
    /* Started by AICoder, pid:p781ci132ac6b84149580936b05aa50e06f16953 */
    let queryBoardBusinessGroupBoardBusinessListResponse = await queryBoardBusinessAtomBoardBusinessList({"boardBusinessType": value});
    /* Ended by AICoder, pid:p781ci132ac6b84149580936b05aa50e06f16953 */
    allGroupBoardBusinessOptionList.value = queryBoardBusinessGroupBoardBusinessListResponse.data || [];
    if (allGroupBoardBusinessOptionList.value.length > 0) {
        groupDialogFormData.value.boardBusiness = allGroupBoardBusinessOptionList.value[0];
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

.query-form
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
