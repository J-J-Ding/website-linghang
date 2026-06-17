<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-cascader
                v-model="selectedFeatureTreeList"
                :options="featureTreeList"
                :filter="pubFilterTreeOptionFun"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                value-type="full"
                style="width: 500px;"
                placeholder="请选择特性"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                label="特性: ">
                    /* Started by AICoder, pid:j2087u1ae2k0f8414a8209ca70e93a0c6618e971 */
                    <template #suffixIcon>
                        <t-popup destroy-on-close placement="top-left">
                            <template #content>
                                <div>1、支持模糊搜索<br/>2、多级搜索用$分隔，如：$一级选项$二级选项</div>
                            </template>
                            <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                        </t-popup>
                    </template>
                    /* Ended by AICoder, pid:j2087u1ae2k0f8414a8209ca70e93a0c6618e971 */
                </t-cascader>
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
                <t-button @click="onExpandAllToggle">{{
                    expandAll ? '收起全部' : '展开全部'
                }}</t-button>
                <t-button @click="onBatchDelete">批量删除</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button @click="onBatchOutput">批量导出</t-button>
                <t-dropdown :active="true" :options="buttonOptions" :max-column-width="300">
                    <t-button :loading="loadingCreate || loadingUpdate || loadingDelete || loadingRefresh">特性树操作</t-button>
                </t-dropdown>
            </t-space>
            <p> </p>
        </t-space>
        <t-enhanced-table
        ref="tableRef"
        row-key="id"
        :columns="tableColumnList"
        :data="tableDataList"
        :tree="{
            childrenKey: 'childrenList',
            checkStrictly: true,
            treeNodeColumnIndex: 4, 
            expandedRowKeys: expandedKeys
        }"
        :selected-row-keys="selectedRowKeyList"
        :select-on-row-click="false"
        :bordered="true"
        active-row-type="multiple"
        :hover="true"
        resizable
        @select-change="handleSelectChange"
        @expanded-tree-nodes-change="onExpandedTreeNodesChange"
        :max-height="tableHeight">
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>
        </t-enhanced-table>

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
                <t-form ref="addFormRef" :data="dialogFormData" :rules="rulesFormData" layout="vertical" label-width="160px">
                     <t-form-item label="特性一级分类" name="featureFirstType">
                        <t-select
                        v-model="dialogFormData.featureFirstType"
                        placeholder="请选择特性一级分类"
                        creatable
                        filterable
                        :disabled="false"
                        @change="handleFeatureFirstTypeChange(true)">
                            <t-option v-for="option in allFeatureFirstTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="特性二级分类" name="featureSecondType">
                        <t-select
                        v-model="dialogFormData.featureSecondType"
                        placeholder="请选择特性二级分类"
                        creatable
                        filterable
                        :disabled="!dialogFormData.featureFirstType"
                        @change="handleFeatureSecondTypeChange(true)">
                            <t-option v-for="option in allFeatureSecondTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="特性" name="feature">
                        <t-select
                        v-model="dialogFormData.feature"
                        placeholder="请选择特性"
                        creatable
                        filterable
                        :disabled="!dialogFormData.featureSecondType"
                        @change="handleFeatureChange(true)">
                            <t-option v-for="option in allSubFeatureOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="子特性" name="subFeature">
                        <t-select
                        v-model="dialogFormData.subFeature"
                        placeholder="请选择子特性"
                        creatable
                        filterable
                        :disabled="!dialogFormData.feature">
                            <t-option v-for="option in allSubFeatureOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="描述" name="description">
                        <t-textarea
                            v-model="dialogFormData.description"
                            placeholder="请输入描述"
                            name="description"
                            :disabled="!dialogFormData.feature"
                            :autosize="{ minRows: 3, maxRows: 5 }"
                        />
                    </t-form-item>
                     <t-form-item label="验收准则" name="acceptanceCriteria">
                        <t-textarea v-model="dialogFormData.acceptanceCriteria" autosize placeholder="请输入验收准则" :disabled="!dialogFormData.feature"/>
                    </t-form-item>
                    <!-- <t-form-item label="特性内容链接" name="featureContentLink">
                        <t-input v-model="dialogFormData.featureContentLink" clearable placeholder="请输入特性内容链接" :disabled="!dialogFormData.feature"/>
                    </t-form-item> -->
                    <t-form-item label="团队" name="belongTeam">
                        <t-select
                            v-model="dialogFormData.belongTeam"
                            placeholder="请选择团队"
                            filterable
                            :disabled="!dialogFormData.feature">
                            <t-option v-for="option in teamOption" :key="option.id" :value="option.value" :label="option.label" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="预计开发工作量(人天)" name="estimatedDevWorkload">
                        <t-input-number 
                        v-model="dialogFormData.estimatedDevWorkload" 
                        :step="0.1"
                        :min="0"
                        placeholder="请输入预计开发工作量(人天)" 
                        :disabled="!dialogFormData.feature"
                        auto-width
                        />
                    </t-form-item>
                    <t-form-item label="需求优先级" name="requirementSort">
                        <t-input-number 
                        v-model="dialogFormData.requirementSort" 
                        :step="1"
                        :min="1"
                        :max="5"
                        placeholder="请选择需求优先级" 
                        :disabled="!dialogFormData.feature"
                        auto-width
                        />
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleAddCancel">取消</t-button>
                <t-button :loading="loadingCreate" @click="handleAddConfirm(true)">提交审核</t-button>
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
                <t-button :loading="loadingCreate" @click="handleDeleteConfirm">提交审核</t-button>
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
                <t-form ref="editForm" :data="dialogFormData" :rules="rulesFormData" layout="vertical" label-width="150px">
                    <t-form-item label="特性一级分类" name="featureFirstType">
                        <t-select
                        v-model="dialogFormData.featureFirstType"
                        creatable
                        filterable
                        placeholder="请选择特性一级分类"
                        @change="handleFeatureFirstTypeChange(ifNotParent)">
                            <t-option v-for="option in allFeatureFirstTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="特性二级分类" name="featureSecondType">
                        <t-select
                        v-model="dialogFormData.featureSecondType"
                        creatable
                        filterable
                        placeholder="请选择特性二级分类"
                        :disabled="!dialogFormData.featureFirstType"
                        @change="handleFeatureSecondTypeChange(ifNotParent)">
                            <t-option v-for="option in allFeatureSecondTypeOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="特性" name="feature">
                        <t-select
                        v-model="dialogFormData.feature"
                        creatable
                        filterable
                        placeholder="请选择特性"
                        :disabled="!dialogFormData.featureSecondType"
                        @change="handleFeatureChange(ifNotParent)">
                            <t-option v-for="option in allFeatureOptionList" :key="option" :value="option" :label="option" />
                        </t-select>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="子特性" name="subFeature">
                        <t-select
                        v-model="dialogFormData.subFeature"
                        placeholder="请选择子特性"
                        creatable
                        filterable
                        :disabled="!dialogFormData.feature">
                            <t-option v-for="option in allSubFeatureOptionList" :key="option"  :value="option"  :label="option"/>
                        </t-select>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="描述" name="description">
                        <t-textarea
                            v-model="dialogFormData.description"
                            placeholder="请输入描述"
                            name="description"
                            :disabled="!dialogFormData.feature"
                            :autosize="{ minRows: 3, maxRows: 5 }"
                        />
                    </t-form-item>
                     <t-form-item v-if="ifNotParent" label="验收准则" name="acceptanceCriteria">
                        <t-textarea v-model="dialogFormData.acceptanceCriteria" autosize placeholder="请输入验收准则" :disabled="!dialogFormData.feature"/>
                    </t-form-item>
                    <t-form-item label="特性内容链接" name="featureContentLink">
                        <t-input v-model="dialogFormData.featureContentLink" clearable placeholder="请输入特性内容链接" :disabled="!dialogFormData.feature"/>
                    </t-form-item>
                    <t-form-item label="团队" name="belongTeam">
                        <t-select
                            v-model="dialogFormData.belongTeam"
                            placeholder="请选择团队"
                            filterable
                            :disabled="!dialogFormData.feature">
                            <t-option v-for="option in teamOption" :key="option.id" :value="option.value" :label="option.label" />
                        </t-select>
                    </t-form-item>
                    <t-form-item label="预计开发工作量(人天)" name="estimatedDevWorkload">
                        <t-input-number 
                            v-model="dialogFormData.estimatedDevWorkload" 
                            :step="0.1"
                            :min="0"
                            placeholder="请输入预计开发工作量(人天)" 
                            :disabled="!dialogFormData.feature"
                            auto-width
                        />
                    </t-form-item>
                    <t-form-item label="需求优先级" name="requirementSort">
                        <t-input-number 
                            v-model="dialogFormData.requirementSort" 
                            :step="1"
                            :min="1"
                            :max="5"
                            placeholder="请选择需求优先级" 
                            :disabled="!dialogFormData.feature"
                            auto-width
                        />
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="handleEditCancel">取消</t-button>
                <t-button :loading="loadingCreate" :disabled="!hasFormChanged" @click="handleEditConfirm(ifNotParent)">提交审核</t-button>
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
                    <p class="file-size">文件大小: {{ formatFileSize(fileList[0].size) }}</p>
                </div>
                <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
                <div class="example-download">
                <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
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
                <t-button @click="cancelImportSubmit">取消</t-button>
                <t-button :loading="loadingImport" @click="handleImportSubmit">确认导入</t-button>
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
                <t-form :data="dialogFormData" layout="vertical" label-width="150px">
                    <t-form-item label="特性一级分类" name="featureFirstType">
                        <t-input v-model="dialogFormData.featureFirstType" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="特性二级分类" name="featureSecondType">
                        <t-input v-model="dialogFormData.featureSecondType" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="特性" name="feature">
                        <t-input v-model="dialogFormData.feature" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="子特性" name="subFeature">
                        <t-input v-model="dialogFormData.subFeature" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="描述" name="description">
                        <t-textarea v-model="dialogFormData.description" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="验收准则" name="acceptanceCriteria">
                        <t-textarea v-model="dialogFormData.acceptanceCriteria" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="特性内容链接" name="featureContentLink">
                        <t-link
                        :href="dialogFormData.featureContentLink"
                        target="_blank"
                        theme="primary"
                        :style="{display: 'inline-block', width: '100%', wordBreak: 'break-all', whiteSpace: 'normal',}"
                        :title="dialogFormData.featureContentLink">
                            {{ dialogFormData.featureContentLink }}
                        </t-link>
                    </t-form-item>
                    <t-form-item label="团队" name="belongTeam">
                        <t-input v-model="dialogFormData.belongTeam" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="预计开发工作量(人天)" name="estimatedDevWorkload">
                        <t-input v-model="dialogFormData.estimatedDevWorkload" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item label="需求优先级" name="requirementSort">
                        <t-input v-model="dialogFormData.requirementSort" :readonly="true" autosize/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="操作人" name="operator_person">
                        <t-input v-model="dialogFormData.operator_person" :readonly="true"/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="更新时间" name="update_time">
                        <t-input v-model="dialogFormData.update_time" :readonly="true"/>
                    </t-form-item>
                    <t-form-item v-if="ifNotParent" label="状态" name="status">
                        <!-- <t-input v-model="dialogFormData.status" :readonly="true"/> -->
                        <t-tag :theme="dialogFormData.status === '正常' ? 'success' : 'danger'" size="small">{{ dialogFormData.status }}</t-tag>
                    </t-form-item>
                </t-form>
            </div>
            <template #footer>
                <t-button @click="queryDialogVisible=false">关闭</t-button>
            </template>
        </t-dialog>

        <t-dialog
            placement="center"
            body="是否批量创建iCenter页面？"
            :visible="visibleCreatiCenter"
            :on-confirm="confirmCreatiCenter"
            :on-close="closeCreatiCenter"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="orange" />
                    <span style="vertical-align: middle">注意</span>
                </div>
            </template>
        </t-dialog>
        <t-dialog
            placement="center"
            :visible="visibleUpdateiCenter"
            :on-confirm="confirmUpdateiCenter"
            :on-close="closeUpdateiCenter"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="orange" />
                    <span style="vertical-align: middle">注意</span>
                </div>
            </template>
            <template #body>
                <div>
                    <div>是否批量更新 iCenter 页面？</div>
                    <div class="add-switch">
                        <t-space>
                            <span style="vertical-align: middle">是否添加标签</span>
                            <t-switch
                                v-model="ifAddLabel"
                                size="medium"
                                :label="[renderActiveContent, renderInactiveContent]"
                            />
                        </t-space>
                    </div>
                </div>
            </template>
        </t-dialog>
        <t-dialog
            placement="center"
            body="是否批量删除iCenter页面？"
            :visible="visibleDeleteiCenter"
            :on-confirm="confirmDeleteiCenter"
            :on-close="closeDeleteiCenter"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="red" />
                    <span style="vertical-align: middle">警告</span>
                </div>
            </template>
        </t-dialog>
        <t-dialog
            placement="center"
            body="是否更新当前数据？"
            :visible="visibleIcenterPage"
            :on-confirm="confirmIcenterPage"
            :on-close="closeIcenterPage"
        >
            <template #header>
                <div>
                    <t-icon name="error-circle-filled" color="orange" />
                    <span style="vertical-align: middle">警告</span>
                </div>
            </template>
        </t-dialog>
    </div>
</template>


<script setup lang="jsx">
import { ref, onMounted, nextTick, onBeforeUnmount, computed, watch } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { pubBuildTreeWithText, pubFilterTreeOptionFun } from '@/utils/pub';
import { HelpCircleFilledIcon, CloseIcon, CheckIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin, NotifyPlugin } from 'tdesign-vue-next';
import { queryFeatureTreeByParams, queryFeatureTreeTree, queryFeatureTreeStatusList, queryFeatureTreeFeatureFirstTypeList,
         queryFeatureTreeFeatureSecondTypeList, queryFeatureTreeFeatureList, queryFeatureTreeSubFeatureList, addFeatureTreeData, updateFeatureTreeData,
         deleteFeatureTreeData, addFeatureIcenterPage, updateFeatureIcenterPage, deleteFeatureIcenterPage, syncFeatureIcenterPage, importExcelFeatureRelationData, submitChange} from '@/api/electric.js';
import tokenManager from '@/utils/tokenManager';
import globalUserInfo from '@/utils/globalUserInfo';
const router = useRouter();
const user = useUserStore();

// 固定数据
const canDelete = ref(false);
const loadingImport = ref(false);
const uploadKey = ref(0);
const buttonOptions = ref([
    {
        content: '批量创建特性树',
        theme: 'default',
        value: 1,
        prefixIcon: () => <t-tooltip
                            content="勾选一行或多行特性/子特性，点击本按钮，即可将所选特性/子特性，按照预设的特性树模板在iCenter空间中批量创建对应的特性树页面，并将特性树链接回填到本页面的特性内容链接栏"
                            placement="top-left">
                            <HelpCircleFilledIcon size="1em" />
                        </t-tooltip>,
        onClick: () => onBatchCreateICenter(),
    },
    {
        content: '批量替换特性树模板',
        value: 2,
        theme: 'default',
        disabled: !canDelete.value,
        prefixIcon: () => <t-tooltip
                            content="勾选一行或多行特性/子特性，点击本按钮，即可将iCenter空间特性树中对应的特性/子特性页面替换为最新的特性树模板"
                            placement="top-left">
                            <HelpCircleFilledIcon size="1em" />
                        </t-tooltip>,
        onClick: () => onBatchUpdateICenter(),
    },
    {
        content: '批量删除特性树',
        value: 3,
        theme: 'default',
        disabled: !canDelete.value,
        prefixIcon: () => <t-tooltip
                            content="勾选一行或多行特性/子特性，点击本按钮，即可将iCenter空间特性树中对应的特性/子特性页面删除"
                            placement="top-left">
                            <HelpCircleFilledIcon size="1em" />
                        </t-tooltip>,
        onClick: () => onBatchDeleteICenter(),
    },
    {
        content: '爬取并更新特性树链接',
        value: 4,
        theme: 'default',
        prefixIcon: () => <t-tooltip
                            content="点击本按钮，即可爬取iCenter空间特性树中所有的特性/子特性链接，并更新回填到本页面的特性内容链接栏"
                            placement="top-left">
                            <HelpCircleFilledIcon size="1em" />
                        </t-tooltip>,
        onClick: () => onBatchIcenterPage(),
    },
]);

const rulesFormData = computed(() => {
    return {
        featureFirstType: [
            { 
                required: true,
                message: '特性一级分类不能为空',
                validator: (value) => {
                    return !!value?.trim();
                },
                trigger: 'change',
            }
        ],
        featureSecondType: [
            { 
                required: true,
                message: '特性二级分类不能为空',
                validator: (value) => {
                    return !!value?.trim();
                },
                trigger: 'change',
            }
        ],
        feature: [
            { 
                required: true,
                message: '特性不能为空',
                validator: (value) => {
                    return !!value?.trim();
                },
                trigger: 'change',
            }
        ],
        subFeature: [
            { 
                required: true,
                message: '子特性不能为空',
                validator: (value) => {
                    return !!value?.trim();
                },
                trigger: 'change',
            }
        ],
        feature: [
            { 
                required: true,
                message: '特性/子特性不能为空',
                validator: (value) => {
                    if (Array.isArray(value)) {
                        return value.length > 0;
                    }               
                    return true;
                },
                trigger: 'change',
            }
        ],
        estimatedDevWorkload: [
            { 
                required: true,
                message: '预计开发工作量(人天)不能为空',
                validator: (value) => {
                    if (Array.isArray(value)) {
                        return value.length > 0;
                    }               
                    return true;
                },
                trigger: 'blur',
            }
        ],
        belongTeam: [
            { 
                required: true,
                message: '团队不能为空',
                validator: (value) => {
                    if (Array.isArray(value)) {
                        return value.length > 0;
                    }               
                    return true;
                },
                trigger: 'change',
            }
        ],
        requirementSort: [
            { 
                required: true,
                message: '需求优先级不能为空',
                validator: (value) => {
                    if (Array.isArray(value)) {
                        return value.length > 0;
                    }               
                    return true;
                },
                trigger: 'blur',
            }
        ],
    }
});
// 表格配置
const tableRef = ref();
const expandedKeys = ref([]);
const originalFormData = ref({}); // 保存初始数据副本
const hasFormChanged = ref(false); // 标记表单是否有修改
const tableColumnList = [
    {
      colKey: 'row-select',
      type: 'multiple',
      width: '50',
      checkProps: ({row}) => ({ disabled: row.status !== '正常' && row.status !== '', title: row.status !== '正常' && row.status !== '' ? '不可选' : null }),
    },
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'featureFirstType', title: () => (<div style={{ textAlign: 'center' }}>特性一级分类</div>), width: '150', align: 'left',ellipsis: { theme: 'light', placement: 'bottom',}  },
    { colKey: 'featureSecondType', title: () => (<div style={{ textAlign: 'center' }}>特性二级分类</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { 
      colKey: 'feature', 
      title: () => (<div style={{ textAlign: 'center' }}>特性</div>), 
      width: '300', align: 'left', 
      cell: (_, { row }) => (
            <div style={{ whiteSpace: 'normal' }}>  {/* 允许换行 */}
                {row.feature}
            </div>
        )
    },
    { colKey: 'subFeature', title: () => (<div style={{ textAlign: 'center' }}>子特性</div>), width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { colKey: 'description', title: () => (<div style={{ textAlign: 'center' }}>描述</div>), width: '300', align: 'left',ellipsis: { theme: 'light', placement: 'bottom',}  },
    { colKey: 'acceptanceCriteria', title: () => (<div style={{ textAlign: 'center' }}>验收准则</div>), width: '200', align: 'left',ellipsis: { theme: 'light', placement: 'bottom',}  },
    { colKey: 'belongTeam', title: '团队', width: '180', align: 'center', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'estimatedDevWorkload', title: '预计开发工作量(人天)', width: '200', align: 'center' },
    { colKey: 'requirementSort', title: '需求优先级', width: '150', align: 'center' },
    {
        colKey: 'featureContentLink',
        title: '特性内容链接',
        width: '200',
        align: 'center',
        ellipsis: { theme: 'light', placement: 'bottom',},
        cell: (_, { row }) => (<t-link theme="primary" href={row.featureContentLink} target="_blank" hover="underline">{row.featureContentLink}</t-link>)
    },
    { colKey: 'operator_person', title: '操作人', width: '200', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },
    {
        colKey: 'status',
        title: '数据状态',
        width: '120',
        align: 'center',
        fixed: 'right',
        cell: (_, { row }) => ((<t-tag theme={row.status === '正常' ? 'success' : 'danger'} size="small">{row.status}</t-tag>))
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
            {(row.status === '正常' || row.status === '') ? (<t-link theme="primary" hover="color" onClick={() => openEditDialog(row)}>修改</t-link>):null}
            </>
        )
    }
];

const teamOption = ref([
    {
        id: 1,
        label: 'L1-保护团队',
        value: 'L1-保护团队',
    },
    {
        id: 2,
        label: 'L1-大师业务团队',
        value: 'L1-大师业务团队',
    },
    {
        id: 3,
        label: 'L1-功能团队',
        value: 'L1-功能团队',
    },
    {
        id: 4,
        label: 'L1-性能团队',
        value: 'L1-性能团队',
    },
    {
        id: 5,
        label: 'L1-量子业务团队',
        value: 'L1-量子业务团队',
    },
    {
        id: 6,
        label: 'L1-雷神业务团队',
        value: 'L1-雷神业务团队',
    },
    {
        id: 7,
        label: 'L1-神盾业务团队',
        value: 'L1-神盾业务团队',
    },
    {
        id: 8,
        label: 'L1-疾风业务团队',
        value: 'L1-疾风业务团队',
    },
    {
        id: 9,
        label: 'L1-平台团队',
        value: 'L1-平台团队',
    }
]);

const priorityOption = ref([
    {
        id: 55,
        label: '5',
        value: 5,
    },
    {
        id: 44,
        label: '4',
        value: 4,
    },
    {
        id: 33,
        label: '3',
        value: 3,
    },
    {
        id: 22,
        label: '2',
        value: 2,
    },
    {
        id: 11,
        label: '1',
        value: 1,
    },
]);

const correspondence =  ref(
    {
        featureFirstType: '特性一级分类',
        featureSecondType: '特性二级分类',
        feature: '特性',
        subFeature: '子特性',
        description: '描述',
        acceptanceCriteria: '验收准则',
        featureContentLink: '特性内容链接',
        belongTeam: '团队',
        estimatedDevWorkload: '预计开发工作量(人天)',
        requirementSort: '需求优先级'
    }
);

// 原始数据和筛选后数据
const tableDataList = ref([]);

// 表格选择相关
const selectedRowKeyList = ref([]);

// 级联选择器相关
const selectedFeatureTreeList = ref([]);
const featureTreeList = ref([]);

// 数据状态选择相关
const selectedStatusOptionList = ref([]);
const statusOptionList = ref([]);

const loadingCreate = ref(false);
const loadingUpdate = ref(false);
const loadingDelete = ref(false);
const loadingRefresh = ref(false);

const ifAddLabel = ref(false);
// 后端查询的选择器选项
const allFeatureFirstTypeOptionList = ref([]);
const allFeatureSecondTypeOptionList = ref([]);
const allFeatureOptionList = ref([]);
const allSubFeatureOptionList = ref([]);
// 修改相关
const currentEditId = ref(null);
const ifNotParent = ref(true);
const editDialogVisible = ref(false);
const editForm = ref();
const dialogFormData = ref({
    featureFirstType: '',
    featureSecondType: '',
    feature: '',
    subFeature: '',
    description: '',
    acceptanceCriteria: '',
    featureContentLink: '',
    operator_person: '',
    update_time: '',
    belongTeam: '',
    estimatedDevWorkload: '',
    requirementSort: '',
    status: ''
});

const queryDialogVisible = ref(false);
// 新增相关
const addDialogVisible = ref(false);
const addFormRef = ref(null);
const visibleCreatiCenter = ref(false);
const visibleUpdateiCenter = ref(false);
const visibleDeleteiCenter = ref(false);
const visibleIcenterPage = ref(false);
// 删除相关
const deleteDialogTitle = ref('删除数据');
const deleteDialogVisible = ref(false);
const deleteRowIds = ref([]);

// 导入相关变量
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const expandAll = ref(false);
const tableHeight = ref('900px');

const renderActiveContent = () => {
  return <CheckIcon />;
};
const renderInactiveContent = () => {
  return <CloseIcon />;
};

const calculateTableHeight = () => {
  // 减去顶部筛选区域、页脚和其他元素的预估高度
  const offset = 245; // 根据实际情况调整这个值
  tableHeight.value = `${window.innerHeight - offset}px`;
};

// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name || !globalUserInfo.hasUserInfo()) {
        MessagePlugin.error('用户信息缺失，请重新登录...');
        router.push('/login');
    }

    if(user.userInfo.name === '10132282' || user.userInfo.name === '10251481' || user.userInfo.name === '10164361' || user.userInfo.name === '10329743' || user.userInfo.name === '10305454' || user.userInfo.name === '10336606'){
        canDelete.value = true

        buttonOptions.value = [
            {
                content: '批量创建特性树',
                theme: 'default',
                value: 1,
                prefixIcon: () => <t-tooltip
                                    content="勾选一行或多行特性/子特性，点击本按钮，即可将所选特性/子特性，按照预设的特性树模板在iCenter空间中批量创建对应的特性树页面，并将特性树链接回填到本页面的特性内容链接栏"
                                    placement="top-left">
                                    <HelpCircleFilledIcon size="1em" />
                                  </t-tooltip>,
                onClick: () => onBatchCreateICenter(),
            },
            {
                content: '批量替换特性树模板',
                value: 2,
                theme: 'default',
                disabled: !canDelete.value,
                prefixIcon: () => <t-tooltip
                                    content="勾选一行或多行特性/子特性，点击本按钮，即可将iCenter空间特性树中对应的特性/子特性页面替换为最新的特性树模板"
                                    placement="top-left">
                                    <HelpCircleFilledIcon size="1em" />
                                  </t-tooltip>,
                onClick: () => onBatchUpdateICenter(),
            },
            {
                content: '批量删除特性树',
                value: 3,
                theme: 'default',
                disabled: !canDelete.value,
                prefixIcon: () => <t-tooltip
                                    content="勾选一行或多行特性/子特性，点击本按钮，即可将iCenter空间特性树中对应的特性/子特性页面删除"
                                    placement="top-left">
                                    <HelpCircleFilledIcon size="1em" />
                                  </t-tooltip>,
                onClick: () => onBatchDeleteICenter(),
            },
            {
                content: '爬取并更新特性树链接',
                value: 4,
                theme: 'default',
                prefixIcon: () => <t-tooltip
                                    content="点击本按钮，即可爬取iCenter空间特性树中所有的特性/子特性链接，并更新回填到本页面的特性内容链接栏"
                                    placement="top-left">
                                    <HelpCircleFilledIcon size="1em" />
                                  </t-tooltip>,
                onClick: () => onBatchIcenterPage(),
            },
        ]
    }
    // await tokenManager.getTokenAutoRefresh(); // 页面主动刷新token值
    try {
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeStatusListResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeStatusList(),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);
        featureTreeList.value = pubBuildTreeWithText(queryFeatureTreeTreeResponse.data || []);
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        statusOptionList.value = queryFeatureTreeStatusListResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];

        calculateTableHeight();
        window.addEventListener('resize', calculateTableHeight);
        
        nextTick(() => {
            if (tableDataList.value.length > 0) {
                expandedKeys.value = [tableDataList.value[0].index];
            }
        });
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', calculateTableHeight);
});

const openQueryDialog = async (row) => {
    ifNotParent.value = !row.parent; // 修改值
    dialogFormData.value = {
        id: row.id,
        featureFirstType: row.parent? row.featureFirstType:row.featureFirstType_bak,
        featureSecondType: row.parent? row.featureSecondType:row.featureSecondType_bak,
        feature: row.parent? row.feature:row.feature_bak,
        subFeature: row.subFeature,
        description: row.description,
        acceptanceCriteria: row.acceptanceCriteria,
        featureContentLink: row.featureContentLink,
        operator_person: row.operator_person,
        update_time: row.update_time,
        belongTeam: row.belongTeam,
        estimatedDevWorkload: row.estimatedDevWorkload,
        requirementSort: row.requirementSort,
        status: row.status
    };
    queryDialogVisible.value = true;
};

const onExpandAllToggle = () => {
  expandAll.value = !expandAll.value;
  expandAll.value ? tableRef.value.expandAll() : tableRef.value.foldAll();
};

const onExpandedTreeNodesChange = (expandedTreeNodes) => {
    const uniqueNumbers = Array.from(new Set(expandedTreeNodes)); 
    if(uniqueNumbers.length > 0) {
        expandAll.value = true;
    } else {
        expandAll.value = false;
    }
    expandedKeys.value = uniqueNumbers;
};

const processString = (str) => {
    // 将字符串按逗号分割成数组
    const items = str.split(',');
    // 对每个元素进行处理，去掉最后一个 - 及其后面的字符
    const processedItems = items.map(item => {
        // 使用正则表达式去掉最后一个 - 及其后面的字符
        return item.replace(/-[^-]*$/, '');
    });
    // 将处理后的数组重新拼接成字符串
    return processedItems.join(',');
};

// 筛选数据
const filterData = async () => {
    try {
        // 提取和处理参数
        const featureFirstTypeList = selectedFeatureTreeList.value.map(item => item[0]);
        const featureSecondTypeList = selectedFeatureTreeList.value.map(item => item[1]);
        const featureList = selectedFeatureTreeList.value.map(item => item[2]);
        const subFeatureList = selectedFeatureTreeList.value.map(item => item[3]);

        const featureFirstType = [...new Set(featureFirstTypeList)].join(',');
        const featureSecondType = [...new Set(featureSecondTypeList)].join(',');
        const feature = [...new Set(featureList)].join(',');
        const subFeature = [...new Set(subFeatureList)].join(',');
        const status = selectedStatusOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (featureFirstType) requestParams.featureFirstType = processString(featureFirstType);
        if (featureSecondType) requestParams.featureSecondType = processString(featureSecondType);
        if (feature) requestParams.feature = processString(feature);
        if (subFeature) requestParams.subFeature = processString(subFeature);
        if (status) requestParams.status = status;

        // 发送请求
        const queryFeatureTreeByParamsResponse = await queryFeatureTreeByParams(requestParams);
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        
        expandAll.value = false;

        // 处理结果提示
        const message = tableDataList.value.length > 0 ? `共找到 ${tableDataList.value.length} 条数据` : `未找到匹配数据`;
        MessagePlugin[tableDataList.value.length > 0 ? 'success' : 'warning'](message);
    } catch (error) {
        MessagePlugin.error('筛选失败，请重试');
    }
};

// 重置筛选
const resetFilters = () => {
    selectedFeatureTreeList.value = [];
    selectedStatusOptionList.value = [];
    filterData();
    MessagePlugin.info('已重置筛选条件');
};

const handleSelectChange = (value, { selectedRowData }) => {
  // 将选中的ID从小到大排序
  selectedRowKeyList.value = [...value].sort((a, b) => a - b)
}


// 修改相关方法
const openEditDialog = async (row) => {
    ifNotParent.value = !row.parent; // 修改值
    editDialogVisible.value = true;
    currentEditId.value = row.id;
    const formData = {
        id: row.id,
        featureFirstType: row.parent? row.featureFirstType:row.featureFirstType_bak,
        featureSecondType: row.parent? row.featureSecondType:row.featureSecondType_bak,
        feature: row.parent? row.feature:row.feature_bak,
        subFeature: row.subFeature,
        description: row.description,
        acceptanceCriteria: row.acceptanceCriteria,
        featureContentLink: row.featureContentLink,
        belongTeam: row.belongTeam,
        estimatedDevWorkload: row.estimatedDevWorkload,
        requirementSort: row.requirementSort
    };

    // 保存到表单数据
    dialogFormData.value = { ...formData };
    
    // 保存原始数据副本（深拷贝）
    originalFormData.value = JSON.parse(JSON.stringify(formData));
    
    // 重置修改标记
    hasFormChanged.value = false;

    // 查询特性二级分类
    let queryFeatureTreeFeatureSecondTypeListResponse = await queryFeatureTreeFeatureSecondTypeList();
    allFeatureSecondTypeOptionList.value = queryFeatureTreeFeatureSecondTypeListResponse.data || [];

    // 查询特性
    let queryFeatureTreeFeatureListResponse = await queryFeatureTreeFeatureList();
    allFeatureOptionList.value = queryFeatureTreeFeatureListResponse.data || [];

    // 查询子特性
    let queryFeatureTreeSubFeatureListResponse = await queryFeatureTreeSubFeatureList();
    allSubFeatureOptionList.value = queryFeatureTreeSubFeatureListResponse.data || [];

    await nextTick(); 
};

const checkFormChanged = () => {
    if (!originalFormData.value || !dialogFormData.value) {
        hasFormChanged.value = false;
        return;
    }
    
    // 需要比较的字段列表
    const fieldsToCompare = [
        'featureFirstType',
        'featureSecondType', 
        'feature',
        'subFeature',
        'description',
        'acceptanceCriteria',
        'featureContentLink',
        'belongTeam',
        'estimatedDevWorkload',
        'requirementSort'
    ];
    
    // 逐字段比较
    hasFormChanged.value = fieldsToCompare.some(field => {
        const originalValue = originalFormData.value[field];
        const currentValue = dialogFormData.value[field];
        
        // 处理数字类型比较
        if (typeof originalValue === 'number' && typeof currentValue === 'number') {
            return originalValue !== currentValue;
        }
        
        // 处理字符串类型比较（包括空字符串和undefined的情况）
        return (originalValue || '') !== (currentValue || '');
    });
    
    console.log('表单是否修改:', hasFormChanged.value);
};

const handleEditConfirm = async (value) => {
    const validateResult = await editForm.value.validate();

    if (validateResult === true) {

        loadingCreate.value = true;
        let updatedData = {
            ...dialogFormData.value,
            id: String(dialogFormData.value.id),
        };

        const modifyData = {
            biz_type: "特性-子特性",
            biz_ids: [dialogFormData.value.id],
            change_type: "update",
            new_datas: [dialogFormData.value],
            old_datas: [originalFormData.value],
            zh_en_name_relation: correspondence.value,
            change_reason: "数据更新",
            assigned_persons: "张进朋10305454,罗峰10164361"
        }

        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };

        try {
            // let updateFeatureTreeDataResponse = await updateFeatureTreeData(updatedData);
            selectedFeatureTreeList.value = [];
            selectedStatusOptionList.value = [];
            selectedRowKeyList.value = [];

            const [
                queryFeatureTreeTreeResponse,
                queryFeatureTreeByParamsResponse,
                queryFeatureTreeFeatureFirstTypeListResponse,
                queryModifyData,
            ] = await Promise.all([
                queryFeatureTreeTree(),
                queryFeatureTreeByParams(requestParams),
                queryFeatureTreeFeatureFirstTypeList(),
                submitChange(modifyData),
            ]);

            featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
            tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
            allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
            editDialogVisible.value = false;

            // 重置修改状态
            hasFormChanged.value = false;
            originalFormData.value = {};

            MessagePlugin.success(queryModifyData.message);
        } catch (error) {
            console.log('修改失败，请重试', error);
        } finally {
            loadingCreate.value = false;
        }
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }
};

const handleEditCancel = () => {
    if (editForm.value) {
        // 清除所有字段的验证状态
        editForm.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (editForm.value.reset) {
            editForm.value.reset();
        }
    }
    // 重置修改状态
    hasFormChanged.value = false;
    originalFormData.value = {};
    editDialogVisible.value = false;
};

// 新增相关方法
const openAddDialog = async () => {
    dialogFormData.value = {
        featureFirstType: '',
        featureSecondType: '',
        feature: '',
        subFeature: '',
        description: '',
        acceptanceCriteria: '',
        featureContentLink: '',
        belongTeam: '',
        estimatedDevWorkload: '',
        requirementSort: ''
    };
    addDialogVisible.value = true;
};

const handleAddConfirm = async () => {
    const validateResult = await addFormRef.value.validate();
    if (validateResult === true) {
        loadingCreate.value = true;
        // 处理新增数据
        const newRow = {
            ...dialogFormData.value,
        };
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const modifyData = {
            biz_type: "特性-子特性",
            biz_ids: [''],
            change_type: "add",
            new_datas: [dialogFormData.value],
            old_datas: [originalFormData.value],
            zh_en_name_relation: correspondence.value,
            change_reason: "数据新增",
            assigned_persons: "张进朋10305454,罗峰10164361"
        }
        try {
            // let addFeatureTreeDataResponse = await addFeatureTreeData(newRow);

            // if(addFeatureTreeDataResponse.data) {
            //     MessagePlugin.success(addFeatureTreeDataResponse.message);
            // } else {
            //     MessagePlugin.warning(addFeatureTreeDataResponse.message + '，特性链接已存在！');
            // }

            selectedFeatureTreeList.value = [];
            selectedStatusOptionList.value = [];
            selectedRowKeyList.value = [];

            const [
                queryFeatureTreeTreeResponse,
                queryFeatureTreeByParamsResponse,
                queryFeatureTreeFeatureFirstTypeListResponse,
                queryModifyData,
            ] = await Promise.all([
                queryFeatureTreeTree(),
                queryFeatureTreeByParams(requestParams),
                queryFeatureTreeFeatureFirstTypeList(),
                submitChange(modifyData),
            ]);

            featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
            tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
            allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];

            addDialogVisible.value = false;
            MessagePlugin.success(queryModifyData.message);
        } catch (error) {
            console.log('新增失败，请重试', error);
        } finally {
            loadingCreate.value = false;
        }
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }    
};

const handleAddCancel = () => {
    if (addFormRef.value) {
        // 清除所有字段的验证状态
        addFormRef.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (addFormRef.value.reset) {
            addFormRef.value.reset();
        }
    }
    addDialogVisible.value = false;
};

const extractNodesByIds = (data, ids) => {
    const result = [];
    const idSet = new Set(ids);
    
    function traverse(nodes) {
        nodes.forEach(node => {
            if (idSet.has(node.id)) {
                result.push({ ...node });
            }
            if (node.childrenList) {
                traverse(node.childrenList);
            }
        });
    }
    
    traverse(data);
    return result;
}

const transformData = (data, ifAddLabel) => {
    const result = {
        featureFirstType: [],
        featureSecondType: [],
        feature: [],
        subFeature: [],
        tag_flag: ifAddLabel,
    };

    data.forEach(item => {
        // 根据 parent 字段决定使用哪个字段
        const featureFirstTypeValue = item.parent ? 
            item.featureFirstType : item.featureFirstType_bak;
        
        const featureSecondTypeValue = item.parent ? 
            item.featureSecondType : item.featureSecondType_bak;
        
        const featureValue = item.parent ? 
            item.feature : item.feature_bak;

        // 添加到对应的数组中
        if (featureFirstTypeValue) {
            result.featureFirstType.push(featureFirstTypeValue);
        }
        
        if (featureSecondTypeValue) {
            result.featureSecondType.push(featureSecondTypeValue);
        }
        
        if (featureValue) {
            result.feature.push(featureValue);
        }
        
        result.subFeature.push(item.subFeature);
        
    });

    // 将数组转换为逗号分隔的字符串
    result.featureFirstType = result.featureFirstType.join(',');
    result.featureSecondType = result.featureSecondType.join(',');
    result.feature = result.feature.join(',');
    result.subFeature = result.subFeature.join(',');

    return result;
}

/* Started by AICoder, pid:3452fy26014932914b8a081f20ff5639ef43ee2e */
const onBatchCreateICenter = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要创建的行');
        return;
    }
    visibleCreatiCenter.value = true;
}

const onBatchUpdateICenter = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要更新的行');
        return;
    }
    visibleUpdateiCenter.value = true;
}

const onBatchDeleteICenter = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要删除的行');
        return;
    }
     visibleDeleteiCenter.value = true;
}

const onBatchIcenterPage = () => {
     visibleIcenterPage.value = true;
}

const confirmCreatiCenter = async () => {
    loadingCreate.value = true;
    visibleCreatiCenter.value = false;
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    const resultData = transformData(selectCountData, false);
    await comfirmICenter(resultData);
}

const confirmUpdateiCenter = async () => {
    loadingUpdate.value = true;
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    const resultData = transformData(selectCountData, ifAddLabel.value);
    visibleUpdateiCenter.value = false;
    ifAddLabel.value = false;
    await updateICenter(resultData);
}

const confirmDeleteiCenter = async () => {
    loadingDelete.value = true;
    visibleDeleteiCenter.value = false;
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    const resultData = transformData(selectCountData, false);
    await DeleteICenter(resultData);
}
/* Ended by AICoder, pid:3452fy26014932914b8a081f20ff5639ef43ee2e */

const confirmIcenterPage = async () => {
    loadingRefresh.value = true;
    visibleIcenterPage.value = false;
    const postData = {
        data_type: "feature"
    }
    await RefreshICenter(postData);
}

const closeCreatiCenter = () => {
    visibleCreatiCenter.value = false;
}

const closeUpdateiCenter = () => {
    ifAddLabel.value = false;
    visibleUpdateiCenter.value = false;
}

const closeDeleteiCenter = () => {
    visibleDeleteiCenter.value = false;
}

const closeIcenterPage = () => {
    visibleIcenterPage.value = false;
}

const updateICenter = async (data) => {
    try {
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const updateICenterResponse = await updateFeatureIcenterPage(data);

        MessagePlugin.success(updateICenterResponse.message);
        
        // else {
        //     updateICenterResponse.data.map((item, index) => {
        //         NotifyPlugin.warning({
        //             title: '警告',
        //             content: `${item} 特性链接页面已存在！`,
        //             duration: 10000,
        //         })
        //     })
        // }

        selectedFeatureTreeList.value = [];
        selectedStatusOptionList.value = [];
        selectedRowKeyList.value = [];

        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
        loadingUpdate.value = false;
    } catch (error) {
        console.log('批量更新失败，请重试', error);
        loadingUpdate.value = false;
    }
}

const comfirmICenter = async (data) => {
    try {
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const comfirmICenterResponse = await addFeatureIcenterPage(data);

        if(comfirmICenterResponse.data && comfirmICenterResponse.data.length === 0) {
            MessagePlugin.success(comfirmICenterResponse.message);
        } else {
            comfirmICenterResponse.data.map((item, index) => {
                NotifyPlugin.warning({
                    title: '警告',
                    content: `${item} 特性链接页面已存在！`,
                    duration: 10000,
                })
            })
        }

        selectedFeatureTreeList.value = [];
        selectedStatusOptionList.value = [];
        selectedRowKeyList.value = [];

        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
        loadingCreate.value = false;
    } catch (error) {
        console.log('批量创建失败，请重试', error);
        loadingCreate.value = false;
    }
}

const DeleteICenter = async (data) => {
    try {
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const deleteICenterResponse = await deleteFeatureIcenterPage(data);

        selectedFeatureTreeList.value = [];
        selectedStatusOptionList.value = [];
        selectedRowKeyList.value = [];

        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
        loadingDelete.value = false;
        MessagePlugin.success(deleteICenterResponse.message);
    } catch (error) {
        console.log('批量删除失败，请重试', error);
        loadingDelete.value = false;
    }
}

const RefreshICenter = async (data) => {
    try {
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        const refreshICenterResponse = await syncFeatureIcenterPage(data);

        selectedFeatureTreeList.value = [];
        selectedStatusOptionList.value = [];
        selectedRowKeyList.value = [];

        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
        loadingRefresh.value = false;
        MessagePlugin.success(refreshICenterResponse.message);
    } catch (error) {
        console.log('批量删除失败，请重试', error);
        loadingRefresh.value = false;
    }
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

const flattenFilteredTree = (treeData, deleteIds) => {
    let result = [];
    
    for (const item of treeData) {
        if (deleteIds.includes(item.id)) {
            result.push(item);
        }
        
        if (item.childrenList && item.childrenList.length > 0) {
            result = result.concat(flattenFilteredTree(item.childrenList, deleteIds));
        }
    }
    
    return result;
};

const handleDeleteConfirm = async () => {
    try {
        loadingCreate.value = true;
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };
        
        const deletedCount = deleteRowIds.value.length;
        const emptyData = Array.from({ length: deletedCount }, () => ({}));
        const newDeleteData = flattenFilteredTree(tableDataList.value, deleteRowIds.value);
        // console.log('tableDataList.value', tableDataList.value);
        // console.log('deleteRowIds.value', deleteRowIds.value);
        // console.log('newDeleteData', newDeleteData);

        const modifyData = {
            biz_type: "特性-子特性",
            biz_ids: deleteRowIds.value,
            change_type: "delete",
            new_datas: emptyData,
            old_datas: newDeleteData,
            zh_en_name_relation: correspondence.value,
            change_reason: "数据删除",
            assigned_persons: "张进朋10305454,罗峰10164361"
        }

        const queryModifyData = await submitChange(modifyData);

        selectedFeatureTreeList.value = [];
        selectedStatusOptionList.value = [];
        selectedRowKeyList.value = [];

        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];

        deleteDialogVisible.value = false;
        MessagePlugin.success(queryModifyData.message);
    } catch (error) {
        console.log('删除失败，请重试', error);
    } finally {
        loadingCreate.value = false;
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

// 格式化文件大小显示
const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};


const downloadExampleFile = () => {
    try {
        const exampleFilePath = '/templates/characteristics_sub_characteristics.xlsx';
        // 创建下载链接
        const link = document.createElement('a');
        link.href = exampleFilePath;
        link.download = '特性&子特性批量导入示例.xlsx'; // 指定下载文件名
        document.body.appendChild(link);
        link.click();
        // 清理
        document.body.removeChild(link);
        MessagePlugin.success('特性&子特性批量导入示例文件下载成功，请查看下载文件');
    } catch (error) {
        console.error('特性&子特性批量导入示例文件下载失败', error);
        MessagePlugin.error('特性&子特性批量导入示例文件失败，请联系管理员');
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
    loadingImport.value = true;
    uploadError.value = '';

    try {
        const file = fileList.value[0];
        const formData = new FormData();
        const requestParams = {
            featureFirstType: '',
            featureSecondType: '',
            feature: '',
            subFeature: '',
            status: '',
        };

        // 构造表单数据
        formData.append('file', file.raw);

        // 调用后端批量导入接口
        const response = await importExcelFeatureRelationData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        // 刷新表格数据
        const [
            queryFeatureTreeTreeResponse,
            queryFeatureTreeByParamsResponse,
            queryFeatureTreeStatusListResponse,
            queryFeatureTreeFeatureFirstTypeListResponse,
        ] = await Promise.all([
            queryFeatureTreeTree(),
            queryFeatureTreeByParams(requestParams),
            queryFeatureTreeStatusList(),
            queryFeatureTreeFeatureFirstTypeList(),
        ]);

        featureTreeList.value = queryFeatureTreeTreeResponse.data || [];
        tableDataList.value = queryFeatureTreeByParamsResponse.data || [];
        statusOptionList.value = queryFeatureTreeStatusListResponse.data || [];
        allFeatureFirstTypeOptionList.value = queryFeatureTreeFeatureFirstTypeListResponse.data || [];
        importDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = '批量导入失败';
    } finally {
        loadingImport.value = false;   
        resetUploadData();
    }
    uploadKey.value++
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
        const flattenData = (data) => {
            let result = [];
            
            data.forEach(item => {
                // 添加父节点数据
                result.push({
                    '编号': item.index,
                    '特性一级分类': item.featureFirstType || '',
                    '特性二级分类': item.featureSecondType || '',
                    '特性': item.feature || '',
                    '子特性': item.subFeature || '',
                    '描述': item.description || '',
                    '验收准则': item.acceptanceCriteria || '',
                    '团队': item.belongTeam || '',
                    '预计开发工作量(人天)': item.estimatedDevWorkload || '',
                    '需求优先级': item.requirementSort || '',
                    '特性内容链接': item.featureContentLink || '',
                    '操作人': item.operator_person || '',
                    '更新时间': item.update_time || '',
                    '数据状态': item.status || ''
                });

                // 递归处理子节点
                if (item.childrenList && item.childrenList.length > 0) {
                    result = result.concat(flattenData(item.childrenList));
                }
            });

            return result;
        };

        const exportData = flattenData(tableDataList.value).map((item, index) => ({
            ...item,
            '编号': index + 1  // 重新生成连续编号
        }));

        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        // 调整列宽（根据内容长度估算）
        const wscols = [
            { wch: 8 },  // 编号
            { wch: 30 }, // 特性一级分类
            { wch: 30 }, // 特性二级分类
            { wch: 30 }, // 特性
            { wch: 30 }, // 子特性
            { wch: 30 }, // 描述
            { wch: 30 }, // 验收准则
            { wch: 30 }, // 领域
            { wch: 30 }, // 特性内容链接
            { wch: 12 }, // 关联版本号
            { wch: 15 }, // 操作人
            { wch: 20 }, // 更新时间
            { wch: 10 }  // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '特性树批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate = 
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `特性树批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

const handleFeatureFirstTypeChange = async (value) => {
    dialogFormData.value.featureSecondType = ""
    dialogFormData.value.feature = ""
    dialogFormData.value.subFeature = ""

    let queryFeatureTreeFeatureSecondTypeListResponse = await queryFeatureTreeFeatureSecondTypeList();
    allFeatureSecondTypeOptionList.value = queryFeatureTreeFeatureSecondTypeListResponse.data || [];
    if (allFeatureSecondTypeOptionList.value.length > 0) {
        dialogFormData.value.featureSecondType = allFeatureSecondTypeOptionList.value[0];
    }

    let queryFeatureTreeFeatureListResponse = await queryFeatureTreeFeatureList();
    allFeatureOptionList.value = queryFeatureTreeFeatureListResponse.data || [];
    if (allFeatureOptionList.value.length > 0) {
        dialogFormData.value.feature = allFeatureOptionList.value[0];
    }

    let queryFeatureTreeSubFeatureListResponse = await queryFeatureTreeSubFeatureList();
    allSubFeatureOptionList.value = queryFeatureTreeSubFeatureListResponse.data || [];
    if (allSubFeatureOptionList.value.length > 0) {
        dialogFormData.value.subFeature = value ? allSubFeatureOptionList.value[0] : '';
    }

    // 检查表单变化
    checkFormChanged();
}

const handleFeatureSecondTypeChange = async (value) => {
    dialogFormData.value.feature = ""
    dialogFormData.value.subFeature = ""

    let queryFeatureTreeFeatureListResponse = await queryFeatureTreeFeatureList();
    allFeatureOptionList.value = queryFeatureTreeFeatureListResponse.data || [];
    if (allFeatureOptionList.value.length > 0) {
        dialogFormData.value.feature = allFeatureOptionList.value[0];
    }

    let queryFeatureTreeSubFeatureListResponse = await queryFeatureTreeSubFeatureList();
    allSubFeatureOptionList.value = queryFeatureTreeSubFeatureListResponse.data || [];
    if (allSubFeatureOptionList.value.length > 0) {
        dialogFormData.value.subFeature = value ? allSubFeatureOptionList.value[0] : '';
    }

     // 检查表单变化
    checkFormChanged();
}

const handleFeatureChange = async (value) => {
    dialogFormData.value.subFeature = ""

    let queryFeatureTreeSubFeatureListResponse = await queryFeatureTreeSubFeatureList();
    allSubFeatureOptionList.value = queryFeatureTreeSubFeatureListResponse.data || [];
    if (allSubFeatureOptionList.value.length > 0) {
        dialogFormData.value.subFeature = value ? allSubFeatureOptionList.value[0] : '';
    }

    // 检查表单变化
    checkFormChanged();
}

// 监听表单数据变化
watch(
    () => dialogFormData.value,
    (newVal) => {
        if (editDialogVisible.value && originalFormData.value) {
            checkFormChanged();
        }
    },
    { deep: true }
);
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

.add-switch {
    margin-top: 10px;
}
</style>

<!-- <style>
/* 在全局样式或组件样式中 */
.custom-cascader-menu .t-cascader__menu {
  width: 400px !important;
  min-width: 400px !important;
}
.custom-cascader-menu .t-cascader__menu + .t-cascader__menu {
  width: 400px !important;
}
</style> -->
