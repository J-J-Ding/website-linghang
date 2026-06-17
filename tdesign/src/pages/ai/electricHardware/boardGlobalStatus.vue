<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-select
                v-model="boardFilterSelectedOptionDict.product"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择产品"
                label="产品: "
                @change="() => updateDownstreamFilters('product')">
                    <t-option v-for="option in boardFilterAllOptionDict.product" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="boardFilterSelectedOptionDict.boardType"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择板卡类型"
                label="板卡类型: "
                @change="() => updateDownstreamFilters('boardType')">
                    <t-option v-for="option in boardFilterAllOptionDict.boardType" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="boardFilterSelectedOptionDict.boardBusinessModel"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择单板业务模型"
                label="单板业务模型: "
                @change="() => updateDownstreamFilters('boardBusinessModel')">
                    <t-option v-for="option in boardFilterAllOptionDict.boardBusinessModel" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="boardFilterSelectedOptionDict.boardIdent"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                :max="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择单板名称"
                label="单板名称: "
                @change="() => updateBoardIdent()">
                    <t-option v-for="option in boardFilterAllOptionDict.boardIdent" :key="option" :value="option" :label="option" />
                </t-select>
            </t-space>
            <t-space>
                <t-cascader
                v-model="rdcFilterSelectedOptionDict.feature"
                :options="rdcFilterAllOptionDict.feature"
                :filter="pubFilterTreeOptionFun"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                value-type="full"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择特性/子特性"
                label="特性/子特性: ">
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
                v-model="rdcFilterSelectedOptionDict.rdcIdent"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择RDC标识"
                label="RDC标识: ">
                    <t-option v-for="option in rdcFilterAllOptionDict.rdcIdent" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="rdcFilterSelectedOptionDict.requirementPreplanningVersion"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择预规划版本"
                label="预规划版本: ">
                    <t-option v-for="option in rdcFilterAllOptionDict.requirementPreplanningVersion" :key="option" :value="option" :label="option" />
                </t-select>
                <t-select
                v-model="rdcFilterSelectedOptionDict.requirementStatus"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                style="width: 375px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择需求状态"
                label="需求状态: ">
                    <t-option v-for="option in rdcFilterAllOptionDict.requirementStatus" :key="option" :value="option" :label="option" />
                </t-select>
            </t-space>
            <t-space>
                <t-button shape="circle" variant="base" theme="primary" @click="onTableAiChat"> AI </t-button>
                <t-button style="width: 80px;" @click="filterData">筛选</t-button>
                <t-button style="width: 80px;" @click="resetFilters">重置</t-button>
                <t-button style="width: 111px;" @click="toggleExpandAll">
                    {{ isAllExpanded ? '收起全部' : '展开全部' }}
                </t-button>
                <t-button :icon="renderIcon" theme="primary" :loading="loadingFresh" @click="clickUpdateData">更新当前数据</t-button>
                <t-button style="width: 111px;" @click="onBatchImport">批量导入</t-button>
                <t-button style="width: 111px;" @click="onBatchOutput">批量导出</t-button>
                <t-button :icon="renderIcon" theme="primary" :loading="loadingUpdate" @click="updateChangeAnalysis">
                    更新变更分析
                </t-button>
                <t-button :icon="EditFilledIcon" theme="primary" :loading="loadingEditRDC" @click="batchEdit">批量更新RDC字段</t-button>
            </t-space>
            <p> </p>
        </t-space>
        <t-enhanced-table
        ref="tableRef"
        row-key="id"
        :columns="tableColumnList"
        :data="tableDataList"
        :select-on-row-click="false"
        active-row-type="multiple"
        :hover="true"
        :tree="{
            childrenKey: 'childrenList',
            treeNodeColumnIndex: 5,
            expandTreeNodeOnClick: false,
        }"
        :max-height="tableHeight"
        bordered
        resizable
        v-model:expandedTreeNodes="expandedTreeNodes"
         @active-change="onActiveChange">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-enhanced-table>

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
                    <t-form-item label="* 变更分析" name="changeAnalysis">
                        <t-textarea
                        v-model="dialogFormData.changeAnalysis"
                        :autosize="{ minRows: 3, maxRows: 10 }"
                        placeholder="请输入变更分析"/>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleEditCancel">取消</t-button>
                <t-button @click="handleEditConfirm">提交审核</t-button>
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
                        class="example-btn"
                        @click="pubDownloadExampleFile('/templates/board_global_status_example.xlsx', '单板全局状态批量导入示例.xlsx')"
                        >
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

        <t-dialog
        v-model:visible="rdcProblemDialogVisible"
        :width="1700"
        theme="info">
            <template #header>
                <t-space>
                    <span>RDC关联故障详情</span>
                </t-space>
            </template>
            <div class="problem-form">
                <t-table
                row-key="id"
                :columns="rdcProblemTableColumnList"
                :data="rdcProblemList"
                bordered
                active-row-type="multiple"
                :hover="true"
                resizable>
                    <template #index="{ rowIndex }">
                        <span>{{ rowIndex + 1 }}</span>
                    </template>
                </t-table>
            </div>
            <template #footer>
                <t-button @click="handleRdcProblemClose">关闭</t-button>
            </template>
        </t-dialog>

        <t-dialog
            placement="center"
            body="是否更新变更分析？"
            :visible="visibleUpdate"
            :on-confirm="confirmUpdate"
            :on-close="closeUpdate"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="orange" />
                    <span style="vertical-align: middle">注意</span>
                </div>
            </template>
        </t-dialog>

        <t-dialog
            v-model:visible="showDialog"
            header="批量更新RDC字段"
            :on-confirm="handleConfirm"
            :on-close="handleClose"
            :on-cancel="handleClose"
            confirm-btn="确定"
            cancel-btn="取消"
            width="700px"
            >
            <div class="batch-edit-dialog">
                <!-- 表头 -->
                <div class="dialog-header">
                <div class="header-field">字段</div>
                <div class="header-value">值</div>
                </div>
                
                <!-- 动态字段列表 -->
                <div class="fields-container">
                <div v-for="(field, index) in fields" :key="field.id" class="field-row">
                    <t-select
                    v-model="field.key"
                    :options="fieldOptions"
                    placeholder="请选择"
                    class="field-select"
                    clearable
                    @change="handleFieldChange(field.key, index)"
                    />

                    <!-- <t-select
                    v-show="field.kind"
                    v-model="field.value"
                    :options="field.option"
                    placeholder="请选择"
                    class="value-input"
                    clearable
                    /> -->
                    <t-input
                    v-model="field.value"
                    placeholder="请输入值"
                    :readonly="field.kind"
                    class="value-input"
                    clearable
                    />
                    <t-button 
                    variant="text" 
                    @click="removeField(index)"
                    class="remove-btn"
                    >
                    <t-icon name="delete-1" />
                    </t-button>
                </div>
                </div>
                
                <!-- 添加字段按钮 -->
                <div class="add-field-section">
                <t-button variant="dashed" block @click="addField">
                    <template #icon><t-icon name="add" /></template>
                    添加字段
                </t-button>
                </div>
            </div>
        </t-dialog>

        <t-dialog
            placement="center"
            body="是否更新当前数据？"
            :visible="visibleUpdateData"
            :on-confirm="confirmUpdateData"
            :on-close="closeUpdateData"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="orange" />
                    <span style="vertical-align: middle">注意</span>
                </div>
            </template>
        </t-dialog>

        <AiChat
        :visible="tableAiVisible"
        :ai-chat-title="tableAiTitle"
        :ai-chat-context="tableAiContext"
        @update:visible="tableAiVisible = $event"
        />
    </div>
</template>


<script setup lang="jsx">
import { ref, onMounted, reactive } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon, RefreshIcon, Edit1FilledIcon, ChatMessageIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin } from 'tdesign-vue-next';
import { pubFormatFileSize, pubDownloadExampleFile, pubCalculateTableHeight, pubBuildTreeWithText, pubFilterTreeOptionFun } from '@/utils/pub';
import { queryBoardGlobalStatusByParams, queryBoardGlobalStatusFilterDataDict, queryBoardGlobalStatusRdcFilterDataDict, updateBoardGlobalStatusData,
         queryBoardGlobalStatusProblemListByRdc, updateBoardGlobalStatusBoardData, updateChangeAnalysisData, syncBoardWholeStatusDataRDC, importExcelBoardGlobalStatusData } from '@/api/electric.js';
import AiChat from '@/pages/ai/MCPChat/chat.vue';
const router = useRouter();
const user = useUserStore();
const tableAiTitle = ref('需求管理助手');
const tableAiContext = ref('');
const renderIcon = () => {
  return <RefreshIcon />;
};

const EditFilledIcon = () => {
  return <Edit1FilledIcon />;
};

const EditAIIcon = () => {
  return <ChatMessageIcon />;
};

// 表格配置
const tableRef = ref();
const tableColumnList = [
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'product', title: () => (<div style={{ textAlign: 'center' }}>产品因子取值</div>), width: '120', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardType', title: () => (<div style={{ textAlign: 'center' }}>板卡类型因子取值</div>),  width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'boardBusinessModel', title: () => (<div style={{ textAlign: 'center' }}>单板业务模型因子取值</div>), width: '180', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'board', title: () => (<div style={{ textAlign: 'center' }}>单板名称</div>), width: '180', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'feature', title: () => (<div style={{ textAlign: 'center' }}>特性/子特性</div>), width: '500', align: 'left' },
    {
        colKey: 'changeAnalysis',
        title: () => (<div style={{ textAlign: 'center' }}>变更分析</div>),
        width: '500',
        align: 'left',
        ellipsis: false, // 必须关闭，否则内容被截断
        cell: (_, { row }) => (
            <div
                style={{
                    whiteSpace: 'pre-line',
                    wordWrap: 'break-word',
                    wordBreak: 'break-all',
                    fontSize: '14px',
                    lineHeight: '1.5',
                    maxHeight: '200px',
                    overflowY: 'auto'
                }}
            >
                {row.changeAnalysis || ''}
            </div>
        )
    },
    // { colKey: 'mileStone', title: () => (<div style={{ textAlign: 'center' }}>里程碑</div>), width: '100', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    // { colKey: 'rdcIdent', title: () => (<div style={{ textAlign: 'center' }}>关联RDC标识</div>), width: '140', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: 'rdcIdent',
        title: () => (<div style={{ textAlign: 'center' }}>关联RDC标识</div>),
        width: '150',
        align: 'center',
        //cell: (_, { row }) => (<t-link theme="primary" href={`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${row.rdc_ident}?teamId=bdv_106024`} target="_blank" hover="underline">{row.rdc_ident}</t-link>)
        cell: (_, { row }) => {
            const getRdcHref = (relatedRdcIdent) => {
                if (!relatedRdcIdent) return '';
                
                const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
                const appPath = '/apps/wim/allWorkItems';
                
                const configs = {
                    OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
                    OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
                };
                
                const config = Object.entries(configs).find(([key]) => 
                    relatedRdcIdent.includes(key)
                )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };
        
                return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
            };

            // 使用
            const href = getRdcHref(row.rdcIdent);

            return (
                <t-link
                    theme="primary"
                    href={href}
                    target="_blank"
                    hover="underline"
                >
                    {row.rdcIdent}
                </t-link>
            );
        },    
    },
    { colKey: 'rdcTitle', title: () => (<div style={{ textAlign: 'center' }}>关联RDC标题</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'requirementPrePlanVersion', title: () => (<div style={{ textAlign: 'center' }}>关联需求预规划版本</div>), width: '160', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'requirementStatus', title: () => (<div style={{ textAlign: 'center' }}>关联需求状态</div>), width: '140', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: 'related_fault_num',
        title: () => (<div style={{ textAlign: 'center' }}>关联故障数</div>),
        width: '110',
        align: 'left',
        cell: (_, { row }) => (row.related_fault_num != null ? (<t-link theme="primary" hover="color" onClick={() => openRdcProblemDialog(row)}>{row.related_fault_num}</t-link>) : null),
        ellipsis: { theme: 'light', placement: 'bottom',}
    },
    // { colKey: 'parentNodeRdc', title: () => (<div style={{ textAlign: 'center' }}>关联父节点RDC</div>), width: '160', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: 'parentNodeRdc',
        title: () => (<div style={{ textAlign: 'center' }}>关联父节点RDC</div>),
        width: '150',
        align: 'center',
        //cell: (_, { row }) => (<t-link theme="primary" href={`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${row.rdc_ident}?teamId=bdv_106024`} target="_blank" hover="underline">{row.rdc_ident}</t-link>)
        cell: (_, { row }) => {
            const getRdcHref = (relatedRdcIdent) => {
                if (!relatedRdcIdent) return '';
                
                const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
                const appPath = '/apps/wim/allWorkItems';
                
                const configs = {
                    OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
                    OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
                };
                
                const config = Object.entries(configs).find(([key]) => 
                    relatedRdcIdent.includes(key)
                )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };
        
                return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
            };

            // 使用
            const href = getRdcHref(row.parentNodeRdc);

            return (
                <t-link
                    theme="primary"
                    href={href}
                    target="_blank"
                    hover="underline"
                >
                    {row.parentNodeRdc}
                </t-link>
            );
        },    
    },
    { colKey: 'operator_person', title: '操作人', width: '200', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },{
        colKey: 'status',
        title: '数据状态',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => row.status === '' ? '' : (<t-tag theme={row.status === '正常' ? 'success' : 'danger'} size="small">{row.status}</t-tag>)
    },
    {
        colKey: 'edit',
        title: '操作',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (row.status === '正常' ? (<t-link theme="primary" hover="color" onClick={() => openEditDialog(row)}>修改</t-link>) : null)
    }
];

const rdcProblemTableColumnList = [
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    {
        colKey: 'rdc_ident',
        title: () => (<div style={{ textAlign: 'center' }}>RDC标识</div>),
        width: '150',
        align: 'center',
        //cell: (_, { row }) => (<t-link theme="primary" href={`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${row.rdc_ident}?teamId=bdv_106024`} target="_blank" hover="underline">{row.rdc_ident}</t-link>)
        cell: (_, { row }) => {
            const getRdcHref = (relatedRdcIdent) => {
                if (!relatedRdcIdent) return '';
                
                const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
                const appPath = '/apps/wim/allWorkItems';

                const configs = {
                    OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
                    OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
                };

                const config = Object.entries(configs).find(([key]) => 
                    relatedRdcIdent.includes(key)
                )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };

                return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
            };

            // 使用
            const href = getRdcHref(row.related_rdc_ident);

            return (
                <t-link
                    theme="primary"
                    href={href}
                    target="_blank"
                    hover="underline"
                >
                    {row.rdc_ident}
                </t-link>
            );
        },    
    },
    { colKey: 'rdc_title', title: () => (<div style={{ textAlign: 'center' }}>RDC标题</div>), width: '300', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'rdc_field', title: () => (<div style={{ textAlign: 'center' }}>归属领域</div>), width: '150', align: 'center', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'rdc_team', title: () => (<div style={{ textAlign: 'center' }}>归属团队</div>), width: '150', align: 'center', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'rdc_changed_by', title: '变更人', width: '150', align: 'center' },
    { colKey: 'rdc_changed_time', title: '变更时间', width: '220', align: 'center' },
    { colKey: 'related_board_name', title: () => (<div style={{ textAlign: 'center' }}>关联单板</div>), width: '200', align: 'center', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: 'related_rdc_ident',
        title: () => (<div style={{ textAlign: 'center' }}>关联RDC标识</div>),
        width: '150',
        align: 'center',
        //cell: (_, { row }) => (<t-link theme="primary" href={`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${row.rdc_ident}?teamId=bdv_106024`} target="_blank" hover="underline">{row.rdc_ident}</t-link>)
        cell: (_, { row }) => {
            // 工具函数
            const getRdcHref = (relatedRdcIdent) => {
                if (!relatedRdcIdent) return '';
                
                const baseUrl = 'https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces';
                const appPath = '/apps/wim/allWorkItems';
                
                const configs = {
                    OTNAG: { workspace: 'OTNAG', teamId: 'bdv_106024' },
                    OTNSW: { workspace: 'OTNSW', teamId: 'bdv_105441' },
                };
                
                const config = Object.entries(configs).find(([key]) => 
                    relatedRdcIdent.includes(key)
                )?.[1] || { workspace: 'OTNTest', teamId: 'bdv_1014533' };
                
                return `${baseUrl}/${config.workspace}${appPath}/${relatedRdcIdent}?teamId=${config.teamId}`;
            };

            // 使用
            const href = getRdcHref(row.related_rdc_ident);
            
            return (
                <t-link
                    theme="primary"
                    href={href}
                    target="_blank"
                    hover="underline"
                >
                    {row.related_rdc_ident}
                </t-link>
            );
        },    
    },
    { colKey: 'rdc_created_by', title: '创建人', width: '150', align: 'center' },
    { colKey: 'rdc_created_time', title: '创建时间', width: '220', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },
    {
        colKey: 'requirement_status',
        title: '状态',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => (<t-tag theme={row.status === '已完成' ? 'success' : 'danger'} size="small">{row.requirement_status}</t-tag>)
    },
];

// 原始数据和筛选后数据
const tableDataList = ref([]);

// 后端查询的选择器选项
const boardFilterDataDict = ref({});
const boardFilterAllOptionDict = ref({
    product: [],
    // mileStone: [],
    boardType: [],
    boardBusinessModel: [],
    boardIdent: [],
});
const boardFilterSelectedOptionDict = ref({
    product: [],
    // mileStone: [],
    boardType: [],
    boardBusinessModel: [],
    boardIdent: [],
});

const rdcFilterAllOptionDict = ref({
    feature: [],
    rdcIdent: [],
    requirementPreplanningVersion: [],
    requirementStatus: [],
});
const rdcFilterSelectedOptionDict = ref({
    feature: [],
    rdcIdent: [],
    requirementPreplanningVersion: [],
    requirementStatus: [],
});
const uploadKey = ref(0);
// 控制展开/折叠状态
const isAllExpanded = ref(false);
const expandedTreeNodes = ref([]);

// 修改相关
const editDialogVisible = ref(false);
const editForm = ref();
const dialogFormData = ref({
    changeAnalysis: '',
});
const visibleUpdateData = ref(false);
// 导入相关变量
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// RDC故障相关
const rdcProblemDialogVisible = ref(false);
const rdcProblemList = ref([]);
const loadingUpdate = ref(false);
const loadingFresh = ref(false);
const loadingEditRDC = ref(false);
const tableHeight = ref('900px');

const visibleUpdate = ref(false);
const tableAiVisible = ref(false);
// 对话框显示状态
const showDialog = ref(false);

// 动态字段ID计数器
let fieldIdCounter = 0;

// 字段列表
const fields = ref([
  {
    id: fieldIdCounter++,
    key: '',
    kind: false,
    value: '',
    label: '',
  },
]);

// 可选择的字段选项
const fieldOptions = ref([]);

const getOptionData = () => {
  fieldOptions.value = [
    { label: '描述', value: 'description', type: 'readonly', description: '来源于领航特性&子特性中的"描述"列' },
    { label: '验收准则', value: 'acceptance_criteria', type: 'readonly', description: '来源于领航特性&子特性中的"验收准则"列' },
    { label: '需求预规划', value: 'requirementPrePlanning', type: 'input', description: '' },
    { label: '需求实例化链接', value: 'specificationByExampleUrl', type: 'input', description: '' },
    { label: '方案文档链接', value: 'designSpecificationUrl', type: 'input', description: '' },
    {
      label: '特性内容链接',
      value: 'featureContentLink',
      type: 'readonly',
      description: '来源于领航特性&子特性中的子特性的"特性详情"链接',
    },
    // { label: '需求用途', value: 'requirementPurpose', type: 'input', description: '' },
    {
      label: '分析说明',
      value: 'analysisReport',
      type: 'readonly',
      description: '来源于全局状态表中对应特性的"变更分析内容"',
    },
    { label: '部件名称', value: 'partName', type: 'readonly', description: '来源于全局状态表中的单板名称' },
  ];
};

// 添加字段
const addField = () => {
  fields.value.push({
    id: fieldIdCounter++,
    key: '',
    kind: false,
    value: '',
    label: ''
  });
};

// 移除字段
const removeField = (index) => {
  if (fields.value.length > 1) {
    fields.value.splice(index, 1);
  }
};

// 字段选择变化
const handleFieldChange = (key, index) => {
  const field = fields.value[index];
  const opt = fieldOptions.value.find(o => o.value === key);
  field.kind = opt?.type === 'readonly';   // 用你自己的判断逻辑
  field.value = field.kind ? opt?.description : ''; // 关键：清空旧值
  //  field.option = opt?.option
};

// 处理确认
const handleConfirm = async () => {
  // 验证表单
  const validFields = fields.value.filter(field => field.key && field.value);
  const boardIdentList = [...new Set(boardFilterSelectedOptionDict.value.boardIdent)];
  const requestParams = {};
  if (validFields.length === 0) {
    MessagePlugin.warning('请至少填写一个完整的字段');
    return;
  }

  const submitData = validFields.reduce((acc, item) => {
        acc[item.key] = item.value;
        return acc;
    }, {});

  if (boardIdentList) requestParams.board = boardIdentList.join(',');
  if (submitData)requestParams.rdc_fields = submitData;
 
  console.log('提交的数据:', submitData);
  loadingEditRDC.value = true;
  showDialog.value = false;

  await updateBoardWholeStatusDataRDC(requestParams);

  resetForm();
};

const updateBoardWholeStatusDataRDC = async (requestParams) => {
    try {
        const comfirmResponse = await syncBoardWholeStatusDataRDC(requestParams);

        MessagePlugin.success(comfirmResponse.message);

        await resetFilters();
        loadingEditRDC.value = false;
    } catch (error) {
        console.log('更新变更分析失败，请重试', error);
        loadingEditRDC.value = false;
    }
};

// 处理对话框关闭
const handleClose = () => {
  showDialog.value = false;
  resetForm();
};

// 重置表单
const resetForm = () => {
  fields.value = [{
    id: fieldIdCounter++,
    key: '',
    kind: false,
    value: '',
    label: ''
  }];
};

// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('请先登录...');
        router.push('/login');
    }
    try {
        const queryBoardGlobalStatusFilterDataDictResponse = await queryBoardGlobalStatusFilterDataDict();
        boardFilterDataDict.value = queryBoardGlobalStatusFilterDataDictResponse.data || {};

        initFilterAllOptionDict();

        boardFilterSelectedOptionDict.value = {
            product: [],
            // mileStone: [],
            boardType: [],
            boardBusinessModel: [],
            boardIdent: boardFilterAllOptionDict.value.boardIdent.length>0?[boardFilterAllOptionDict.value.boardIdent[0]]:[]
        };

        const queryBoardGlobalStatusRdcFilterDataDictResponse = await queryBoardGlobalStatusRdcFilterDataDict({"board": boardFilterSelectedOptionDict.value.boardIdent.join(',')});
        const optionDict = queryBoardGlobalStatusRdcFilterDataDictResponse.data || {};

        rdcFilterAllOptionDict.value.feature = optionDict.feature;
        rdcFilterAllOptionDict.value.requirementStatus = optionDict.requirementStatus;
        rdcFilterAllOptionDict.value.rdcIdent = optionDict.rdcIdent.sort();
        rdcFilterAllOptionDict.value.requirementPreplanningVersion = optionDict.requirementPreplanningVersion.sort();
        await filterData();
        tableHeight.value = pubCalculateTableHeight(290);
        // await nextTick();
        // expandAll();
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
});

const onTableAiChat = () => {
  tableAiVisible.value = true;
};

const updateChangeAnalysis = () => {
    if(boardFilterSelectedOptionDict.value.boardIdent.length > 0) {
        // loadingUpdate.value = true;
        visibleUpdate.value = true;
    } else {
        MessagePlugin.warning('请选择单板！');
    }
    console.log('正在更新变更分析！');
};

const batchEdit = () => {
    if(boardFilterSelectedOptionDict.value.boardIdent.length > 0) {
        getOptionData();
        showDialog.value = true;
    } else {
        MessagePlugin.warning('请选择单板！');
    }
};

const confirmUpdate = async () => {
    const boardIdentList = [...new Set(boardFilterSelectedOptionDict.value.boardIdent)];
    // 构建参数对象，过滤掉空值
    const requestParams = {};
    if (boardIdentList) requestParams.board = boardIdentList.join(',');
    loadingUpdate.value = true;
    visibleUpdate.value = false;
    await updateAnalysis(requestParams);
};

const updateAnalysis = async (requestParams) => {
    try {
        const comfirmResponse = await updateChangeAnalysisData(requestParams);

        MessagePlugin.success(comfirmResponse.message);

        await resetFilters();
        loadingUpdate.value = false;
    } catch (error) {
        console.log('更新变更分析失败，请重试', error);
        loadingUpdate.value = false;
    }
};

const closeUpdate = () => {
    visibleUpdate.value = false;
    loadingUpdate.value = false;
};


const initFilterAllOptionDict = () => {
    // 1. product 层直接取顶层 keys
    boardFilterAllOptionDict.value.product = Object.keys(boardFilterDataDict.value).sort();

    // 2. mileStone 层：遍历每个 product 下的所有第一层子项
    const mileStoneSet = new Set();
    for (const product in boardFilterDataDict.value) {
        const productData = boardFilterDataDict.value[product];
        Object.keys(productData).forEach(key => mileStoneSet.add(key));
    }
    boardFilterAllOptionDict.value.boardType = Array.from(mileStoneSet).sort();

    // 3. boardType 层：遍历 product -> mileStone -> 下一层
    const boardTypeSet = new Set();
    for (const product in boardFilterDataDict.value) {
        const productData = boardFilterDataDict.value[product];
        for (const mileStone in productData) {
            const mileStoneData = productData[mileStone];
            Object.keys(mileStoneData).forEach(key => boardTypeSet.add(key));
        }
    }
    boardFilterAllOptionDict.value.boardBusinessModel = Array.from(boardTypeSet).sort();

    // 4. boardBusinessModel 层：继续深入
    const boardBusinessModelSet = new Set();
    for (const product in boardFilterDataDict.value) {
        const productData = boardFilterDataDict.value[product];
        for (const mileStone in productData) {
            const mileStoneData = productData[mileStone];
            for (const boardType in mileStoneData) {
                const boardTypeData = mileStoneData[boardType];
                boardTypeData.forEach(id => boardBusinessModelSet.add(id));
            }
        }
    }
    boardFilterAllOptionDict.value.boardIdent = Array.from(boardBusinessModelSet).sort();

    // 5. boardIdent 层：最深层的数组元素
    // const boardIdentSet = new Set();
    // for (const product in boardFilterDataDict.value) {
    //     const productData = boardFilterDataDict.value[product];
    //     for (const mileStone in productData) {
    //         const mileStoneData = productData[mileStone];
    //         for (const boardType in mileStoneData) {
    //             const boardTypeData = mileStoneData[boardType];
    //             for (const boardBusinessModel in boardTypeData) {
    //                 const boardIdentList = boardTypeData[boardBusinessModel];
    //                 boardIdentList.forEach(id => boardIdentSet.add(id));
    //             }
    //         }
    //     }
    // }
    // boardFilterAllOptionDict.value.boardIdent = Array.from(boardIdentSet);
}


const updateDownstreamFilters = (level) => {
    const levels = ['product', 'boardType', 'boardBusinessModel', 'boardIdent'];
    const levelIndex = levels.indexOf(level);

    if (levelIndex === -1) {
        console.warn('Invalid level:', level);
        return;
    }
    // ===== 第一步：清空下游层级的 boardFilterAllOptionDict.value =====
    for (let i = levelIndex + 1; i < levels.length; i++) {
        boardFilterAllOptionDict.value[levels[i]] = [];
    }

    // ===== 第二步：获取当前及上游所有已选值 =====
    const selected = {};
    for (let i = 0; i <= levelIndex; i++) {
        const lvl = levels[i];
        selected[lvl] = boardFilterSelectedOptionDict.value[lvl] || [];
    }
    // ===== 第三步：从顶层开始逐级向下构建数据流 =====
    let currentDataList = [boardFilterDataDict.value]; // 从根开始
    for (let i = 0; i <= levelIndex; i++) {
        const lvl = levels[i];
        const selectedList = selected[lvl];
        // 如果当前层无选择，视为“全选” → 取所有 key
        let keysToUse = selectedList.length > 0 ? selectedList : Object.keys(i === 0 ? boardFilterDataDict.value : currentDataList.reduce((acc, obj) => {Object.keys(obj).forEach(key => { acc[key] = true; });  return acc; }, {}));
        const nextLevelData = [];
        for (const data of currentDataList) {
            for (const key of keysToUse) {
                if (data && data[key]) {
                    nextLevelData.push(data[key]);
                }
            }
        }
        currentDataList = nextLevelData;
        // 如果当前是最后一级（即 level），停止向下构建，准备生成下游选项
        if (i === levelIndex) break;
    }

    // ===== 第四步：从 levelIndex+1 开始，逐级生成 boardFilterAllOptionDict =====
    let currentLevelData = currentDataList;

    for (let i = levelIndex + 1; i < levels.length; i++) {
        const nextLevel = levels[i];
        const nextLevelSet = new Set();

        if (nextLevel === 'boardType') {
            for (const data of currentLevelData) {
                Object.keys(data).forEach(k => nextLevelSet.add(k));
            }
        } else if (nextLevel === 'boardBusinessModel') {
            for (const data of currentLevelData) {
                Object.keys(data).forEach(k => nextLevelSet.add(k));
            }
        } else if (nextLevel === 'boardIdent') {
            for (const data of currentLevelData) {
                if (Array.isArray(data)) {
                    data.forEach(id => nextLevelSet.add(id));
                }
            }
        }

        const options = Array.from(nextLevelSet);
        boardFilterAllOptionDict.value[nextLevel] = options.sort();
        
        // ===== 清理 boardFilterSelectedOptionDict.value[nextLevel] 中无效项 =====
        const selectedOptions = boardFilterSelectedOptionDict.value[nextLevel] || [];
        const validSelected = selectedOptions.filter(opt => options.includes(opt));
        if (validSelected.length !== selectedOptions.length) {
            boardFilterSelectedOptionDict.value[nextLevel] = validSelected;
        }

        // 为下一层准备数据源（非最后一层）
        if (i < levels.length - 1) {
            const newNextLevelData = [];
            for (const data of currentLevelData) {
                for (const key of options) {
                    if (data && data[key]) {
                        newNextLevelData.push(data[key]);
                    }
                }
            }
            currentLevelData = newNextLevelData;
        }
    }

    rdcFilterAllOptionDict.value = {
        feature: [],
        rdcIdent: [],
        requirementPreplanningVersion: [],
        requirementStatus: [],
    }
}

const updateBoardIdent = async () => {
    try {
        const queryBoardGlobalStatusRdcFilterDataDictResponse = await queryBoardGlobalStatusRdcFilterDataDict({"board": boardFilterSelectedOptionDict.value.boardIdent.join(',')});
        const optionDict = queryBoardGlobalStatusRdcFilterDataDictResponse.data || {};
        rdcFilterAllOptionDict.value.feature = optionDict.feature;
        rdcFilterAllOptionDict.value.requirementStatus = optionDict.requirementStatus;
        rdcFilterAllOptionDict.value.rdcIdent = optionDict.rdcIdent.sort();
        rdcFilterAllOptionDict.value.requirementPreplanningVersion = optionDict.requirementPreplanningVersion.sort();

        const feature = rdcFilterAllOptionDict.value.feature;
        rdcFilterAllOptionDict.value.feature = pubBuildTreeWithText(feature);
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
}

// 筛选数据
const filterData = async () => {
    try {
        // 提取和处理参数
        const boardIdentList = [...new Set(boardFilterSelectedOptionDict.value.boardIdent)];
        const featureList = [...new Set(rdcFilterSelectedOptionDict.value.feature.map(item => item[0]))];
        const subFeatureList = [...new Set(rdcFilterSelectedOptionDict.value.feature.map(item => item[1]))];
        const rdcIdentList = [...new Set(rdcFilterSelectedOptionDict.value.rdcIdent)];
        const requirementStatusList = [...new Set(rdcFilterSelectedOptionDict.value.requirementStatus)];
        const requirementPrePlanVersion = [...new Set(rdcFilterSelectedOptionDict.value.requirementPreplanningVersion)];

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (boardIdentList) requestParams.board = boardIdentList.join(',');
        if (featureList) requestParams.feature = featureList.join(',');
        if (subFeatureList) requestParams.subFeature = subFeatureList.join(',');
        if (rdcIdentList) requestParams.rdcIdent = rdcIdentList.join(',');
        if (requirementStatusList) requestParams.requirementStatus = requirementStatusList.join(',');
        if (requirementPrePlanVersion) requestParams.requirementPrePlanVersion = requirementPrePlanVersion.join(',');
        // 发送请求
        const queryBoardGlobalStatusByParamsResponse = await queryBoardGlobalStatusByParams(requestParams);
        tableDataList.value = queryBoardGlobalStatusByParamsResponse.data || [];

        // 处理结果提示
        const message = tableDataList.value.length > 0 ? `共找到 ${tableDataList.value.length} 块单板` : `未找到匹配单板`;
        MessagePlugin[tableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选条件
const resetFilters = async () => {
    initFilterAllOptionDict();
    boardFilterSelectedOptionDict.value = {
        product: [],
        // mileStone: [],
        boardType: [],
        boardBusinessModel: [],
        boardIdent: boardFilterAllOptionDict.value.boardIdent.length>1?[boardFilterAllOptionDict.value.boardIdent[0]]:[]
    };
    rdcFilterSelectedOptionDict.value = {
        feature: [],
        rdcIdent: [],
        requirementPreplanningVersion: [],
        requirementStatus: [],
    };
    try {
        const queryBoardGlobalStatusRdcFilterDataDictResponse = await queryBoardGlobalStatusRdcFilterDataDict({"board": boardFilterSelectedOptionDict.value.boardIdent.join(',')});
        const optionDict = queryBoardGlobalStatusRdcFilterDataDictResponse.data || {};
        rdcFilterAllOptionDict.value.feature = optionDict.feature;
        rdcFilterAllOptionDict.value.requirementStatus = optionDict.requirementStatus;
        rdcFilterAllOptionDict.value.rdcIdent = optionDict.rdcIdent.sort();
        rdcFilterAllOptionDict.value.requirementPreplanningVersion = optionDict.requirementPreplanningVersion.sort();
        rdcFilterAllOptionDict.value.feature = pubBuildTreeWithText(rdcFilterAllOptionDict.value.feature);
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
    filterData();
};

// 获取所有行的 rowKey（递归）
function getAllRowKeys(data, keys = []) {
    data.forEach(item => {
        keys.push(item.id);
        if (item.childrenList && item.childrenList.length) {
            getAllRowKeys(item.childrenList, keys);
        }
    });
    return keys;
}

// 切换全部展开/折叠
const toggleExpandAll = () => {
    if (isAllExpanded.value) {
        collapseAll();
    } else {
        expandAll();
    }
};

// 全部展开
const expandAll = () => {
    const allKeys = getAllRowKeys(tableDataList.value);
    expandedTreeNodes.value = allKeys;
    isAllExpanded.value = true;
};

// 全部折叠
const collapseAll = () => {
    expandedTreeNodes.value = [];
    isAllExpanded.value = false;
};

// 修改相关方法
const openEditDialog = async (row) => {
    dialogFormData.value = {
        id: row.id,
        changeAnalysis: row.changeAnalysis,
    };

    editDialogVisible.value = true;
};

const handleEditConfirm = async () => {
    if (!dialogFormData.value.changeAnalysis) {
        MessagePlugin.warning('请填写变更分析');
        return;
    }

    let updatedData = {
        ...dialogFormData.value,
        id: String(dialogFormData.value.id),
    };

    try {
        let updateBoardGlobalStatusDataResponse = await updateBoardGlobalStatusData(updatedData);

        editDialogVisible.value = false;
        MessagePlugin.success(updateBoardGlobalStatusDataResponse.message);
    } catch (error) {
        console.log('修改失败，请重试', error);
    }
};

const handleEditCancel = () => {
    editDialogVisible.value = false;
};

const onActiveChange = (highlightRowKeys, ctx) => {
  console.log(highlightRowKeys, ctx);
};

// RDC故障相关
const openRdcProblemDialog = async (row) => {
    try {
        let queryBoardGlobalStatusProblemListByRdcResponse = await queryBoardGlobalStatusProblemListByRdc({ rdc_ident: row.rdcIdent });
        rdcProblemList.value = queryBoardGlobalStatusProblemListByRdcResponse.data || []
        MessagePlugin.success(queryBoardGlobalStatusProblemListByRdcResponse.message);
    } catch (error) {
        console.log('查询失败，请重试', error);
    }

    rdcProblemDialogVisible.value = true;
};

const handleRdcProblemClose = async () => {
    rdcProblemList.value = []
    rdcProblemDialogVisible.value = false;
};

const confirmUpdateData = async () => {
    loadingFresh.value = true;
    visibleUpdateData.value = false;
    await onUpdateData();
}

const closeUpdateData = () => {
    visibleUpdateData.value = false
}

const clickUpdateData  = async () => {
    visibleUpdateData.value = true;
}

// 更新当前数据
const onUpdateData = async () => {
    try {
        await updateBoardGlobalStatusBoardData({ board: boardFilterSelectedOptionDict.value.boardIdent.join(',') });
        await filterData();
    } catch (error) {
        console.log('更新失败，请重试', error);
    } finally {
        loadingFresh.value = false;
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
        const response = await importExcelBoardGlobalStatusData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        importDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = '批量导入失败';
    }
    uploadKey.value++
    importLoading.value = false;
};

// 批量导出
const onBatchOutput = async () => {
    // 判断是否有数据可导出
    if (tableDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }

    try {
        // 用于存储所有需要导出的扁平化行数据
        const flattenedExportData = [];

        // 递归函数：将树形数据扁平化并添加到 exportData 数组中
        const flattenData = (data, level = 0) => {
            data.forEach((row) => {
                // 将树形结构的数据转换为扁平化的对象，键为表格列的标题
                const flatRow = {
                    '产品因子取值': row.product || '',
                    '板卡类型因子取值': row.boardType || '',
                    '单板业务模型因子取值': row.boardBusinessModel || '',
                    '单板名称': row.board || '',
                    '特性/子特性': row.feature || '',
                    '变更分析': row.changeAnalysis || '',
                    // '里程碑': row.mileStone || '',
                    '关联RDC标识': row.rdcIdent || '',
                    '关联RDC标题': row.rdcTitle || '',
                    '关联需求预规划版本': row.requirementPrePlanVersion || '',
                    '关联需求状态': row.requirementStatus || '',
                    '关联父节点RDC': row.parentNodeRdc || '',
                    '关联故障数': row.related_fault_num || '',
                    '操作人': row.operator_person || '',
                    '更新时间': row.update_time || '',
                    '数据状态': row.status || ''
                };
                flattenedExportData.push(flatRow);

                // 如果当前行有子节点，则递归处理子节点
                if (row.childrenList && row.childrenList.length > 0) {
                    flattenData(row.childrenList, level + 1);
                }
            });
        };

        // 从根节点开始扁平化整个表格数据
        flattenData(tableDataList.value);

        // 为扁平化后的数据添加行号
        const exportDataWithIndex = flattenedExportData.map((row, index) => ({
            '编号': index + 1,
            ...row
        }));

        // 创建工作表
        const worksheet = XLSX.utils.json_to_sheet(exportDataWithIndex, { skipHeader: false });

        // --- 修改部分：设置所有列宽度为相同的默认值 ---
        const DEFAULT_COLUMN_WIDTH = 25; // 设置您想要的默认宽度
        // 获取导出数据中的所有唯一键（列名）
        const uniqueKeys = new Set();
        exportDataWithIndex.forEach(row => {
            Object.keys(row).forEach(key => uniqueKeys.add(key));
        });
        const columnKeys = Array.from(uniqueKeys);
        // 为每一列创建相同宽度的配置
        const wscols = columnKeys.map(() => ({ wch: DEFAULT_COLUMN_WIDTH }));
        worksheet['!cols'] = wscols;
        // --- 修改部分结束 ---

        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '单板全局状态');

        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate =
            `${date.getFullYear().toString().slice(2)}` +
            `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
            `${date.getDate().toString().padStart(2, '0')}` +
            `${date.getHours().toString().padStart(2, '0')}` +
            `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `单板全局状态_${formattedDate}.xlsx`;

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

.edit-form,
.add-form {
    padding: 16px 0;
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

.batch-edit-dialog {
  padding: 8px 0;
  max-height: 500px;
}

.dialog-header {
  display: flex;
  margin-bottom: 16px;
  font-weight: bold;
  color: var(--td-text-color-primary);
  border-bottom: 1px solid var(--td-border-level-1-color);
  padding-bottom: 8px;
}

.header-field {
  flex: 1.3;
  padding-right: 12px;
}

.header-value {
  flex: 2;
  padding-left: 12px;
}

.fields-container {
  margin-bottom: 16px;
}

.field-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.field-select {
  flex: 1.3;
}

.value-input {
  flex: 1.6;
}

.remove-btn {
  flex-shrink: 0;
  color: var(--td-error-color);
}

.add-field-section {
  margin-top: 8px;
}
</style>
