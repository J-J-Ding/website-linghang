<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
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
                <t-button @click="openAddDialog">新建案例</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
            </t-space>
            <p> </p>
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
            :max-height="tableHeight">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-table>

        <!-- 新增案例对话框 -->
        <t-dialog
            v-model:visible="addDialogVisible"
            :width="800"
            theme="warning">
            <template #header>
                <t-space>
                    <span>新建案例</span>
                    <t-tooltip
                        content="1、带*的为必填项。2、填写工作项ID后点击确认案例源可自动载入相关信息。"
                        placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <div class="add-form">
                <t-form ref="addFormRef" :data="dialogFormData" layout="vertical">
                    <t-form-item label="工作项ID" name="workItemId">
                        <t-input
                            v-model="dialogFormData.workItemId"
                            placeholder="请输入工作项ID"
                            clearable
                        />
                        <t-button
                            style="margin-top: 8px;"
                            @click="confirmCaseSource"
                            :disabled="!dialogFormData.workItemId">
                            确认案例源
                        </t-button>
                    </t-form-item>
                    <t-form-item label="* 案例标题" name="caseTitle">
                        <t-input
                            v-model="dialogFormData.caseTitle"
                            placeholder="请输入案例标题"
                        />
                    </t-form-item>
                    <t-form-item label="* 归属项目" name="belongProject">
                        <t-select
                            v-model="dialogFormData.belongProject"
                            placeholder="请选择或输入归属项目"
                            filterable
                            allow-input
                            clearable
                        >
                            <t-option value="智能OTN" label="智能OTN" />
                            <t-option value="M721" label="M721" />
                            <t-option value="7000" label="7000" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="案例发现局点" name="caseFoundSite">
                        <t-input
                            v-model="dialogFormData.caseFoundSite"
                            placeholder="请输入案例发现局点"
                        />
                    </t-form-item>
                    <t-form-item label="优先级" name="priority">
                        <t-select
                            v-model="dialogFormData.priority"
                            placeholder="请选择优先级"
                        >
                            <t-option value="高" label="高" />
                            <t-option value="中" label="中" />
                            <t-option value="低" label="低" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="关联质量专题" name="qualityTopic">
                        <t-select
                            v-model="dialogFormData.qualityTopic"
                            placeholder="请选择关联质量专题"
                            filterable
                            allow-input
                            clearable
                        >
                            <t-option value="光模块" label="光模块" />
                            <t-option value="流控" label="流控" />
                            <t-option value="业务稳定性" label="业务稳定性" />
                            <t-option value="抖动" label="抖动" />
                            <t-option value="数据设备对接" label="数据设备对接" />
                            <t-option value="SDH" label="SDH" />
                            <t-option value="性能告警" label="性能告警" />
                            <t-option value="编码（软件崩溃、内存泄露、内存越界）" label="编码（软件崩溃、内存泄露、内存越界）" />
                            <t-option value="CPU&内存性能" label="CPU&内存性能" />
                            <t-option value="WASON" label="WASON" />
                            <t-option value="APO" label="APO" />
                            <t-option value="其他" label="其他" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="功能分类" name="functionCategory">
                        <t-input
                            v-model="dialogFormData.functionCategory"
                            placeholder="请输入功能分类"
                        />
                    </t-form-item>
                    <t-form-item label="组件" name="component">
                        <t-input
                            v-model="dialogFormData.component"
                            placeholder="请输入组件"
                        />
                    </t-form-item>
                    <t-form-item label="单板" name="part">
                        <t-input
                            v-model="dialogFormData.part"
                            placeholder="请输入单板"
                        />
                    </t-form-item>
                    <t-form-item label="工作项类型" name="workItemType">
                        <t-select
                            v-model="dialogFormData.workItemType"
                            placeholder="请选择工作项类型"
                        >
                            <t-option value="外场故障" label="外场故障" />
                            <t-option value="内场故障" label="内场故障" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="工作项标题" name="workItemTitle">
                        <t-input
                            v-model="dialogFormData.workItemTitle"
                            placeholder="工作项标题"
                            :disabled="true"
                        />
                    </t-form-item>
                    <t-form-item label="案例发生时间" name="caseOccurTime">
                        <t-date-picker
                            v-model="dialogFormData.caseOccurTime"
                            placeholder="请选择案例发生时间"
                            enable-time-picker
                            format="YYYY-MM-DD HH:mm:ss"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="案例触发局点" name="caseTriggerSite">
                        <t-input
                            v-model="dialogFormData.caseTriggerSite"
                            placeholder="案例触发局点"
                            :disabled="true"
                        />
                    </t-form-item>
                    <t-form-item label="指派给" name="assignTo">
                        <t-input
                            v-model="dialogFormData.assignTo"
                            placeholder="请输入指派给"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="是否影响业务" name="affectBusiness">
                        <t-select
                            v-model="dialogFormData.affectBusiness"
                            placeholder="请选择是否影响业务"
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="修改故障入库记录" name="modifyFaultRecord">
                        <t-input
                            v-model="dialogFormData.modifyFaultRecord"
                            placeholder="请输入修改故障入库记录，按照分支填写"
                        />
                    </t-form-item>
                    <t-form-item label="是否需要横推" name="needHorizontalPush">
                        <t-select
                            v-model="dialogFormData.needHorizontalPush"
                            placeholder="请选择是否需要横推"
                            clearable
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="横推单" name="horizontalPushTicket">
                        <t-input
                            v-model="dialogFormData.horizontalPushTicket"
                            placeholder="请输入横推单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="是否需要通告" name="needNotice">
                        <t-select
                            v-model="dialogFormData.needNotice"
                            placeholder="请选择是否需要通告"
                            clearable
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="RDC通告单" name="rdcNoticeTicket">
                        <t-input
                            v-model="dialogFormData.rdcNoticeTicket"
                            placeholder="请输入RDC通告单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="RDC复盘单" name="rdcReviewTicket">
                        <t-input
                            v-model="dialogFormData.rdcReviewTicket"
                            placeholder="请输入RDC复盘单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="状态" name="status">
                        <t-select
                            v-model="dialogFormData.status"
                            placeholder="请选择状态"
                            :disabled="true"
                        >
                            <t-option value="新建" label="新建" />
                            <t-option value="分析中" label="分析中" />
                            <t-option value="横推中" label="横推中" />
                            <t-option value="审批中" label="审批中" />
                            <t-option value="已完成" label="已完成" />
                            <t-option value="已关闭" label="已关闭" />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleAddCancel">取消</t-button>
                <t-button @click="handleAddConfirm">提交</t-button>
            </template>
        </t-dialog>

        <!-- 编辑案例对话框 -->
        <t-dialog
            v-model:visible="editDialogVisible"
            :width="800"
            theme="warning">
            <template #header>
                <t-space>
                    <span>编辑案例</span>
                    <t-tooltip
                        content="1、带*的为必填项。2、修改后数据将保存。"
                        placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <div class="edit-form">
                <t-form ref="editFormRef" :data="dialogFormData" layout="vertical">
                    <t-form-item label="* 案例标题" name="caseTitle">
                        <t-input
                            v-model="dialogFormData.caseTitle"
                            placeholder="请输入案例标题"
                        />
                    </t-form-item>
                    <t-form-item label="* 归属项目" name="belongProject">
                        <t-select
                            v-model="dialogFormData.belongProject"
                            placeholder="请选择或输入归属项目"
                            filterable
                            allow-input
                            clearable
                        >
                            <t-option value="智能OTN" label="智能OTN" />
                            <t-option value="M721" label="M721" />
                            <t-option value="7000" label="7000" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="案例发现局点" name="caseFoundSite">
                        <t-input
                            v-model="dialogFormData.caseFoundSite"
                            placeholder="请输入案例发现局点"
                        />
                    </t-form-item>
                    <t-form-item label="优先级" name="priority">
                        <t-select
                            v-model="dialogFormData.priority"
                            placeholder="请选择优先级"
                        >
                            <t-option value="高" label="高" />
                            <t-option value="中" label="中" />
                            <t-option value="低" label="低" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="关联质量专题" name="qualityTopic">
                        <t-select
                            v-model="dialogFormData.qualityTopic"
                            placeholder="请选择关联质量专题（可多选）"
                            filterable
                            allow-input
                            clearable
                            multiple
                        >
                            <t-option value="光模块" label="光模块" />
                            <t-option value="流控" label="流控" />
                            <t-option value="业务稳定性" label="业务稳定性" />
                            <t-option value="抖动" label="抖动" />
                            <t-option value="数据设备对接" label="数据设备对接" />
                            <t-option value="SDH" label="SDH" />
                            <t-option value="性能告警" label="性能告警" />
                            <t-option value="编码（软件崩溃、内存泄露、内存越界）" label="编码（软件崩溃、内存泄露、内存越界）" />
                            <t-option value="CPU&内存性能" label="CPU&内存性能" />
                            <t-option value="WASON" label="WASON" />
                            <t-option value="APO" label="APO" />
                            <t-option value="其他" label="其他" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="功能分类" name="functionCategory">
                        <t-input
                            v-model="dialogFormData.functionCategory"
                            placeholder="请输入功能分类"
                        />
                    </t-form-item>
                    <t-form-item label="组件" name="component">
                        <t-input
                            v-model="dialogFormData.component"
                            placeholder="请输入组件"
                        />
                    </t-form-item>
                    <t-form-item label="单板" name="part">
                        <t-input
                            v-model="dialogFormData.part"
                            placeholder="请输入单板"
                        />
                    </t-form-item>
                    <t-form-item label="是否影响业务" name="affectBusiness">
                        <t-select
                            v-model="dialogFormData.affectBusiness"
                            placeholder="请选择是否影响业务"
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="修改故障入库记录" name="modifyFaultRecord">
                        <t-input
                            v-model="dialogFormData.modifyFaultRecord"
                            placeholder="请输入修改故障入库记录，按照分支填写"
                        />
                    </t-form-item>
                    <t-form-item label="工作项ID" name="workItemId">
                        <t-input
                            v-model="dialogFormData.workItemId"
                            placeholder="工作项ID"
                            :disabled="true"
                        />
                    </t-form-item>
                    <t-form-item label="工作项类型" name="workItemType">
                        <t-select
                            v-model="dialogFormData.workItemType"
                            placeholder="请选择工作项类型"
                        >
                            <t-option value="外场故障" label="外场故障" />
                            <t-option value="内场故障" label="内场故障" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="案例发生时间" name="caseOccurTime">
                        <t-date-picker
                            v-model="dialogFormData.caseOccurTime"
                            placeholder="请选择案例发生时间"
                            enable-time-picker
                            format="YYYY-MM-DD HH:mm:ss"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="指派给" name="assignTo">
                        <t-input
                            v-model="dialogFormData.assignTo"
                            placeholder="请输入指派给"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="是否需要横推" name="needHorizontalPush">
                        <t-select
                            v-model="dialogFormData.needHorizontalPush"
                            placeholder="请选择是否需要横推"
                            clearable
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="横推单" name="horizontalPushTicket">
                        <t-input
                            v-model="dialogFormData.horizontalPushTicket"
                            placeholder="请输入横推单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="是否需要通告" name="needNotice">
                        <t-select
                            v-model="dialogFormData.needNotice"
                            placeholder="请选择是否需要通告"
                            clearable
                        >
                            <t-option value="是" label="是" />
                            <t-option value="否" label="否" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="RDC通告单" name="rdcNoticeTicket">
                        <t-input
                            v-model="dialogFormData.rdcNoticeTicket"
                            placeholder="请输入RDC通告单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="RDC复盘单" name="rdcReviewTicket">
                        <t-input
                            v-model="dialogFormData.rdcReviewTicket"
                            placeholder="请输入RDC复盘单ID"
                            clearable
                        />
                    </t-form-item>
                    <t-form-item label="状态" name="status">
                        <t-select
                            v-model="dialogFormData.status"
                            placeholder="请选择状态"
                        >
                            <t-option value="新建" label="新建" />
                            <t-option value="分析中" label="分析中" />
                            <t-option value="横推中" label="横推中" />
                            <t-option value="审批中" label="审批中" />
                            <t-option value="已完成" label="已完成" />
                            <t-option value="已关闭" label="已关闭" />
                        </t-select>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleEditCancel">取消</t-button>
                <t-button @click="handleEditConfirm">提交</t-button>
            </template>
        </t-dialog>

        <!-- 删除确认对话框 -->
        <t-dialog
            v-model:visible="deleteDialogVisible"
            :width="500"
            @confirm="handleDeleteConfirm"
            @cancel="deleteDialogVisible = false"
            theme="warning">
            <template #header>
                <t-space>
                    <span>{{ deleteDialogTitle }}</span>
                    <t-tooltip
                        content="删除后案例状态将置为已删除。"
                        placement="top-left">
                        <HelpCircleFilledIcon size="1em" />
                    </t-tooltip>
                </t-space>
            </template>
            <t-space direction="vertical" style="width: 100%">
                <t-form layout="vertical">
                    <p>确定要删除该案例吗？删除后案例状态将置为"已删除"。</p>
                </t-form>
            </t-space>
            <template #footer>
                <t-button @click="deleteDialogVisible = false">取消</t-button>
                <t-button theme="danger" @click="handleDeleteConfirm">确认删除</t-button>
            </template>
        </t-dialog>

        <!-- 批量导入对话框 -->
        <t-dialog
            v-model:visible="importDialogVisible"
            :width="600"
            theme="warning"
            header="批量导入案例">
            <div class="import-container">
                <t-upload
                    ref="uploadRef"
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
                            @click="downloadExampleFile"
                            class="example-btn">
                            <t-icon name="download" size="16" class="mr-1" />
                            下载导入示例文件
                        </t-button>
                    </t-space>
                </div>
            </div>
            <template #footer>
                <t-button @click="importDialogVisible = false">取消</t-button>
                <t-button @click="handleImportSubmit">确认导入</t-button>
            </template>
        </t-dialog>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { 
    queryIssueImpacte, 
    createIssueImpacte, 
    updateIssueImpacte, 
    deleteIssueImpacte, 
    importIssueImpacte,
    confirmCaseSource as confirmCaseSourceApi
} from '@/api/issueImpacte.js';

const router = useRouter();
const user = useUserStore();

// 表格配置
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
    { colKey: 'part', title: '部件', width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
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
    },
    {
        colKey: 'edit',
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
    caseId: '',
    caseTitle: '',
    belongProject: '',
    caseFoundSite: '',
    priority: '',
    qualityTopic: '',
    functionCategory: '',
    component: ''
});

// 对话框相关
const addDialogVisible = ref(false);
const editDialogVisible = ref(false);
const deleteDialogVisible = ref(false);
const importDialogVisible = ref(false);
const addFormRef = ref(null);
const editFormRef = ref(null);
const deleteDialogTitle = ref('删除案例');
const currentEditId = ref(null);
const deleteRowId = ref(null);

// 表单数据
const dialogFormData = ref({
    caseId: '',
    caseTitle: '',
    belongProject: '',
    caseFoundSite: '',
    priority: '',
    qualityTopic: '',
    functionCategory: '',
    component: '',
    part: '',
    workItemId: '',
    workItemType: '',
    workItemTitle: '',
    caseOccurTime: '',
    caseTriggerSite: '',
    affectBusiness: '',
    modifyFaultRecord: '',
    faultCode: '',
    modifiedCode: '',
    introduceFaultRecord: '',
    status: '新建',
    needHorizontalPush: '',
    horizontalPushTicket: '',
    needNotice: '',
    rdcNoticeTicket: '',
    rdcReviewTicket: '',
    assignTo: ''
});

// 导入相关
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const tableHeight = ref('900px');

// 计算表格高度
const calculateTableHeight = () => {
    const offset = 245;
    tableHeight.value = `${window.innerHeight - offset}px`;
};

// 生命周期
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('用户信息缺失，请重新登录...');
        router.push('/login');
    }

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
        const requestData = {
            user: user.userInfo.name || 'guest',
            onlyOpen: true,
            conditions: {
                status: ['新建', '分析中', '横推中', '审批中']
            }
        };

        const responseData = await queryIssueImpacte(requestData);
        
        if (responseData.status !== 'success') {
            throw new Error(responseData.message || '读取数据失败');
        }

        tableDataList.value = (responseData.data || []).map((item, index) => ({
            id: item.caseId || `case_${index}`,
            ...item
        }));

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
    try {
        loading.value = true;
        const conditions = {};
        
        if (queryParams.value.caseId) conditions.caseId = queryParams.value.caseId;
        if (queryParams.value.caseTitle) conditions.caseTitle = queryParams.value.caseTitle;
        if (queryParams.value.belongProject) conditions.belongProject = queryParams.value.belongProject;
        if (queryParams.value.caseFoundSite) conditions.caseFoundSite = queryParams.value.caseFoundSite;
        if (queryParams.value.priority) conditions.priority = queryParams.value.priority;
        if (queryParams.value.qualityTopic) conditions.qualityTopic = queryParams.value.qualityTopic;
        if (queryParams.value.functionCategory) conditions.functionCategory = queryParams.value.functionCategory;
        if (queryParams.value.component) conditions.component = queryParams.value.component;
        
        conditions.status = ['新建', '分析中', '横推中', '审批中'];

        const requestData = {
            user: user.userInfo.name || 'guest',
            onlyOpen: true,
            conditions: conditions
        };

        const responseData = await queryIssueImpacte(requestData);
        
        if (responseData.status !== 'success') {
            throw new Error(responseData.message || '查询失败');
        }

        tableDataList.value = (responseData.data || []).map((item, index) => ({
            id: item.caseId || `case_${index}`,
            ...item
        }));

        const message = tableDataList.value.length > 0 ? `共找到 ${tableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[tableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        console.error('筛选失败:', error);
        MessagePlugin.error(error.message || '筛选失败');
    } finally {
        loading.value = false;
    }
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

// 打开新增对话框
const openAddDialog = () => {
    dialogFormData.value = {
        caseId: '',
        caseTitle: '',
        belongProject: '',
        caseFoundSite: '',
        priority: '',
        qualityTopic: '',
        functionCategory: '',
        component: '',
        part: '',
        workItemId: '',
        workItemType: '',
        workItemTitle: '',
        caseOccurTime: '',
        caseTriggerSite: '',
        affectBusiness: '',
        modifyFaultRecord: '',
        faultCode: '',
        modifiedCode: '',
        introduceFaultRecord: '',
        status: '新建',
        needHorizontalPush: '',
        horizontalPushTicket: '',
        needNotice: '',
        rdcNoticeTicket: '',
        rdcReviewTicket: '',
        assignTo: ''
    };
    addDialogVisible.value = true;
};

// 确认案例源（从工作项加载信息）
const confirmCaseSource = async () => {
    if (!dialogFormData.value.workItemId) {
        MessagePlugin.warning('请输入工作项ID');
        return;
    }

    try {
        loading.value = true;
        const requestData = {
            workItemId: dialogFormData.value.workItemId,
            workItemType: dialogFormData.value.workItemType || '内场故障',
            belongProject: dialogFormData.value.belongProject,
            caseTriggerSite: dialogFormData.value.caseTriggerSite,
            affectBusiness: dialogFormData.value.affectBusiness,
            functionCategory: dialogFormData.value.functionCategory,
            component: dialogFormData.value.component,
            part: dialogFormData.value.part,
        };

        const responseData = await confirmCaseSourceApi(requestData);
        
        if (responseData.status === 'success') {
            if (responseData.data && responseData.data.caseId) {
                Object.assign(dialogFormData.value, responseData.data);
                MessagePlugin.warning('该工作项已存在案例单，已加载现有数据');
            } else {
                Object.assign(dialogFormData.value, responseData.data);
                MessagePlugin.success('已根据工作项生成推荐信息');
            }
        } else {
            throw new Error(responseData.message || '获取案例源信息失败');
        }
    } catch (error) {
        console.error('加载案例源信息失败:', error);
        MessagePlugin.error(error.message || '加载案例源信息失败');
    } finally {
        loading.value = false;
    }
};

// 确认新增
const handleAddConfirm = async () => {
    if (!dialogFormData.value.caseTitle) {
        MessagePlugin.warning('请输入案例标题');
        return;
    }
    if (!dialogFormData.value.belongProject) {
        MessagePlugin.warning('请输入归属项目');
        return;
    }

    try {
        loading.value = true;
        const formData = { ...dialogFormData.value };
        if (!('assignTo' in formData)) {
            formData.assignTo = '';
        }
        
        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: formData
        };

        try {
            const responseData = await createIssueImpacte(requestData);
            
            if (responseData.status !== 'success') {
                throw new Error(responseData.message || '新增失败');
            }
            
            MessagePlugin.success('新增案例成功');
            addDialogVisible.value = false;
            await loadData();
        } catch (error) {
            if (error.status === 409 && error.data) {
                Object.assign(dialogFormData.value, error.data);
                MessagePlugin.warning(error.message || '该工作项已存在案例单，请直接编辑');
                addDialogVisible.value = false;
                editDialogVisible.value = true;
                currentEditId.value = error.data.caseId;
            } else {
                throw error;
            }
        }
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
const openEditDialog = (row) => {
    currentEditId.value = row.id;
    dialogFormData.value = { ...row };
    if (dialogFormData.value.qualityTopic) {
        if (typeof dialogFormData.value.qualityTopic === 'string') {
            dialogFormData.value.qualityTopic = dialogFormData.value.qualityTopic.split(',').map(item => item.trim()).filter(item => item);
        } else if (!Array.isArray(dialogFormData.value.qualityTopic)) {
            dialogFormData.value.qualityTopic = [];
        }
    } else {
        dialogFormData.value.qualityTopic = [];
    }
    editDialogVisible.value = true;
};

// 确认编辑
const handleEditConfirm = async () => {
    if (!dialogFormData.value.caseTitle) {
        MessagePlugin.warning('请输入案例标题');
        return;
    }
    if (!dialogFormData.value.belongProject) {
        MessagePlugin.warning('请输入归属项目');
        return;
    }

    try {
        loading.value = true;
        const submitData = { ...dialogFormData.value };
        if (Array.isArray(submitData.qualityTopic)) {
            submitData.qualityTopic = submitData.qualityTopic.join(',');
        }
        
        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: {
                caseId: dialogFormData.value.caseId,
                ...submitData
            }
        };

        const responseData = await updateIssueImpacte(requestData);
        
        if (responseData.status !== 'success') {
            throw new Error(responseData.message || '更新失败');
        }

        MessagePlugin.success('更新案例成功');
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
    deleteRowId.value = row.id;
    deleteDialogTitle.value = `删除案例: ${row.caseTitle || row.caseId}`;
    deleteDialogVisible.value = true;
};

// 确认删除
const handleDeleteConfirm = async () => {
    try {
        loading.value = true;
        const row = tableDataList.value.find(item => item.id === deleteRowId.value);
        if (!row) {
            MessagePlugin.error('未找到要删除的案例');
            return;
        }

        const requestData = {
            user: user.userInfo.name || 'guest',
            conditions: {
                caseId: row.caseId
            }
        };

        const responseData = await deleteIssueImpacte(requestData);
        
        if (responseData.status !== 'success') {
            throw new Error(responseData.message || '删除失败');
        }

        MessagePlugin.success('删除成功（案例状态已置为已删除）');
        deleteDialogVisible.value = false;
        await loadData();
    } catch (error) {
        console.error('删除失败:', error);
        MessagePlugin.error(error.message || '删除失败');
    } finally {
        loading.value = false;
    }
};

// 批量导入
const onBatchImport = () => {
    fileList.value = [];
    uploadError.value = '';
    importDialogVisible.value = true;
};

// 处理文件选择
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

// 下载示例文件
const downloadExampleFile = () => {
    try {
        const exampleData = [{
            '案例ID': 'CASE_001',
            '案例标题': '示例案例标题',
            '归属项目': '智能OTN',
            '案例发现局点': '示例局点',
            '优先级': '高',
            '关联质量专题': '示例专题',
            '功能分类': '示例分类',
            '部件': '示例单板',
            '工作项ID': 'WORK_001',
            '工作项类型': '外场故障',
            '案例发生时间': '2024-01-01 10:00:00',
            '指派给': '示例人员',
            '状态': '新建'
        }];

        const worksheet = XLSX.utils.json_to_sheet(exampleData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '案例批量导入示例');

        const fileName = '案例批量导入示例.xlsx';
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

    try {
        loading.value = true;
        const file = fileList.value[0];
        const reader = new FileReader();
        const data = await new Promise((resolve, reject) => {
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsArrayBuffer(file.raw);
        });

        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);

        if (!jsonData || jsonData.length === 0) {
            throw new Error('Excel文件中没有数据');
        }

        const formData = new FormData();
        formData.append('file', file.raw);

        const responseData = await importIssueImpacte(formData);
        
        if (responseData.status !== 'success') {
            throw new Error(responseData.message || '批量导入失败');
        }

        MessagePlugin.success(responseData.message || `批量导入完成: 成功 ${responseData.data?.inserted || 0} 条, 跳过 ${responseData.data?.skipped || 0} 条`);
        importDialogVisible.value = false;
        await loadData();
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = error.message || '批量导入失败';
    } finally {
        loading.value = false;
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

.query-form,
.edit-form,
.add-form {
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

.file-size {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
}
</style>