<template>
    <t-watermark
        :watermark-content="{
        text: `${headerParams['X-Emp-No']}`,
        }"
        :width="120"
        :height="60"
        :y="120"
        :x="80"
    >
        <div class="scene-main">
            <t-space direction="vertical">
                <t-space>
                    <t-button @click="openAddDialog">新增</t-button>
                    <t-button @click="onBatchDelete">批量删除</t-button>
                    <t-button @click="onBatchImport">批量导入</t-button>
                    <t-button @click="onBatchOutput">批量导出</t-button>
                    <t-dropdown :active="true" :options="divideOptions" :max-column-width="300">    
                        <t-button :loading="loadingBreakdown || loadingAdd || loadingFeature || loadingModify">需求拆分
                            <template #suffix>
                                <t-tooltip
                                    content="勾选对应的单板，点击本按钮，即可进行需求波及和需求拆分（如果单板全局状态页面中对应的单板存在已关联的需求，则无法通过本按钮进行需求拆分）"
                                    placement="right">
                                        <HelpCircleFilledIcon size="1em" />
                                </t-tooltip>
                            </template>
                        </t-button>
                    </t-dropdown> 
                    <t-dropdown :active="true" :options="buttonOptions" :max-column-width="300">
                        <t-button :loading="loadingCreate || loadingUpdate || loadingRefresh">单板方案操作</t-button>
                    </t-dropdown>
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
            active-row-type="multiple"
            :hover="true"
            :max-height="tableHeight"
            bordered
            resizable
            :filter-value.sync="filterValue"
            lazy-load
            @active-change="onActiveChange"
            @select-change="handleSelectChange"
            @filter-change="onFilterChange">
                <template #index="{ rowIndex }">
                    <span>{{ rowIndex + 1 }}</span>
                </template>
            </t-table>

            <t-dialog
            v-model:visible="addDialogVisible"
            :width="800"
            theme="warning"
            :confirmLoading="loadingCreate || saveLoading"
            :on-confirm="handleAddConfirm"
            :on-close="handleAddCancel"
            confirmBtn="提交审核"
            cancelBtn="取消"
            >
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
                    <t-form ref="addFormRef" :data="dialogFormData" :rules="rulesMR" layout="vertical" label-width="250px" :validate-on-rule-change="false">
                        <t-form-item label="单板名称" name="board">
                            <t-input v-model="dialogFormData.board" :disabled="canEdit && false" placeholder="请填写单板名称" @blur="(value) => regularExpressionValidation(value, '单板名称', verifyOption['单板名称']?.input_format, verifyOption['单板名称']?.input_remark)">
                                <template #suffixIcon>
                                    <t-popup destroy-on-close placement="top-left">
                                        <template #content>
                                            <div>{{verifyOption['单板名称']?.input_remark}}</div>
                                        </template>
                                        <t-icon v-if="verifyOption['单板名称'] && verifyOption['单板名称']?.input_remark !== null" name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                    </t-popup>
                                </template>
                            </t-input>
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
                            :multiple="isMultiple(field)"
                            :disabled="(field !== '板卡类型' && canEdit) || (field == '映射关系')"
                            :creatable="isCreatParams(field)"
                            :min-collapsed-num="1"
                            :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                            @change="(value) => selectElement(value, field, 'add')"
                            @create="(value) => regularExpressionValidation(value, field, verifyOption[field]?.input_format, verifyOption[field]?.input_remark)">
                                <template #suffixIcon>
                                    <t-popup destroy-on-close placement="top-left">
                                        <template #content>
                                            <div>{{verifyOption[field]?.input_remark}}</div>
                                        </template>
                                        <t-icon v-if="verifyOption[field] && verifyOption[field]?.input_remark !== null" name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                    </t-popup>
                                </template>
                                <t-option
                                v-for="option in allFactorValueDict[field]"
                                :key="option"
                                :value="option"
                                :label="option"/>
                            </t-select>
                        </t-form-item>

                        <!-- <t-form-item label="客户侧映射关系" name="customerRelation">
                            <t-button
                                variant="text"
                                theme="primary"
                                :disabled="!canShowCustomerRelation"
                                @click="showCustomerRelationDialog"
                            >
                                点击查看
                            </t-button>
                            <div v-if="dialogFormData.customerRelation.length > 0" class="relation-hint">
                                已配置 {{ dialogFormData.customerRelation.length }} 条映射关系
                            </div>
                        </t-form-item> -->

                            <!-- 线路侧映射关系 -->
                        <t-form-item label="线路侧映射关系" name="lineRelation">
                            <t-button
                                variant="text"
                                theme="primary"
                                :disabled="!canShowLineRelation"
                                @click="showLineRelationDialog(dialogFormData?.['线路侧光层业务'], dialogFormData?.['线路侧光模块'], dialogFormData.lineRelation, nowStatus)"
                            >
                                点击查看
                            </t-button>
                            <div class="relation-hint">
                                已配置 {{ lineRelationNum }} 条映射关系
                            </div>
                        </t-form-item>

                        <t-form-item label="是否创建RDC" name="createRdc">
                            <t-checkbox v-model="dialogFormData.createRdc" @change="onChangeRDC">创建RDC</t-checkbox>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="是否创建MR" name="createMR">
                            <t-checkbox v-model="dialogFormData.createMR" @change="onCreateMR">是否创建MR</t-checkbox>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="MR创建人工号" name="createNum">
                            <t-select v-model="dialogFormData.createNum" :loading="searchLoading" loadingText="检索中..." filterable :disabled="!dialogFormData.createRdc" placeholder="请填写MR创建人工号" clearable @input-change="getNameOptions" @blur="clearList">
                                <t-option v-for="item in nameOption" :key="item.id" :value="item.value" :label="item.label" :title="item.description"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="需求来源" name="requirementSource">
                            <t-select v-model="dialogFormData.requirementSource" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择需求来源" clearable @popup-visible-change="getRDCsourceOptions">
                                <t-option v-for="item in sourceOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="期望完成日期" name="expectedFinishDate">
                            <t-date-picker
                                v-model="dialogFormData.expectedFinishDate"
                                placeholder="请选择期望完成日期"
                                clearable
                                allow-input
                                @change="(value) => consoleTime(value)"
                                />
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="需求用途" name="requirementPurpose">
                            <t-select v-model="dialogFormData.requirementPurpose" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择需求用途" clearable @popup-visible-change="getRDCpurposeOptions">
                                <t-option v-for="item in purposeOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="客户" name="customer">
                            <t-select v-model="dialogFormData.customer" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择客户" clearable @popup-visible-change="getRDCcustomerOptions">
                                <t-option v-for="item in customerOption" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="需求预规划" name="requirementPrePlanVersion">
                            <t-select v-model="dialogFormData.requirementPrePlanVersion" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请填写需求预规划" clearable @popup-visible-change="getRDCPlanOptions">
                                <t-option v-for="item in linkOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="需求实例化链接" name="requirementInstantiationLink">
                            <t-input v-model="dialogFormData.requirementInstantiationLink" :disabled="!dialogFormData.createRdc" placeholder="请填写需求实例化链接"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="方案文档链接" name="designSpecificationUrl">
                            <t-input v-model="dialogFormData.designSpecificationUrl" :disabled="!dialogFormData.createRdc" placeholder="请填写方案文档链接"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="高优先级子架" name="subrack">
                            <t-input v-model="dialogFormData.subrack" :disabled="!dialogFormData.createRdc" placeholder="请填写高优先级子架"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="需求类型" name="requirementType">
                            <t-select v-model="dialogFormData.requirementType" :disabled="!dialogFormData.createRdc" filterable placeholder="请选择需求类型" clearable>
                              <template #suffixIcon>
                                <t-popup destroy-on-close placement="top-left">
                                    <template #content>
                                        <div>{{ requirementTypeDes }}</div>
                                    </template>
                                    <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                </t-popup>
                              </template>
                              <t-option v-for="item in requirementTypes" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.requirementType === '交付需求'" label="指派业务团队" name="belongTeam">
                            <t-select v-model="dialogFormData.belongTeam" :disabled="!dialogFormData.createRdc" filterable placeholder="请选择需求类型" clearable>
                              <template #suffixIcon>
                                <t-popup destroy-on-close placement="top-left">
                                    <template #content>
                                        <div>{{ assignTeamDes }}</div>
                                    </template>
                                    <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                </t-popup>
                              </template>
                              <t-option v-for="item in assignTeams" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="目标市场" name="targetMarket">
                            <t-input v-model="dialogFormData.targetMarket" :disabled="!dialogFormData.createRdc" placeholder="请填写目标市场"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.createMR" label="市场目标" name="marketTarget">
                            <t-input v-model="dialogFormData.marketTarget" :disabled="!dialogFormData.createRdc" placeholder="请填写市场目标"/>
                        </t-form-item>
                        <t-form-item label="是否创建单板方案" name="createBoard">
                            <t-checkbox v-model="dialogFormData.createBoard">创建单板方案</t-checkbox>
                        </t-form-item>
                    </t-form>
                </div>
                <!-- <template #footer>
                    <t-button @click="handleAddCancel">取消</t-button>
                    <t-button :loading="loadingCreate" @click="handleAddConfirm">提交审核</t-button>
                </template> -->
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
                        <p>本次删除 {{ selectedRowKeyList.length }} 条数据，是否提交审核？</p>
                    </t-form>
                </t-space>
                <template #footer>
                    <t-button @click="deleteDialogVisible = false">取消</t-button>
                    <t-button :loading="loadingCreate" @click="handleDeleteConfirm">提交审核</t-button>
                </template>
            </t-dialog>

            <t-dialog
            v-model:visible="editDialogVisible"
            :width="800"
            theme="warning"
            :confirmLoading="saveLoading || loadingCreate"
            :on-confirm="handleEditConfirm"
            :on-close="handleEditCancel"
            confirmBtn="提交审核"
            cancelBtn="取消"
            >
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
                    <t-form ref="editForm" :data="dialogFormData" :rules="rules" layout="vertical" label-width="250px" :validate-on-rule-change="false">
                        <t-form-item label="单板名称" name="board">
                            <t-input v-model="dialogFormData.board" :disabled="canEdit" placeholder="请填写单板名称" @blur="(value) => regularExpressionValidation(value, '单板名称', verifyOption['单板名称']?.input_format, verifyOption['单板名称']?.input_remark)">
                                <template #suffixIcon>
                                    <t-popup destroy-on-close placement="top-left">
                                        <template #content>
                                            <div>{{verifyOption['单板名称']?.input_remark}}</div>
                                        </template>
                                        <t-icon v-if="verifyOption['单板名称'] && verifyOption['单板名称']?.input_remark !== null" name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                    </t-popup>
                                </template>
                            </t-input>
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
                            :multiple="isMultiple(field)"
                            :disabled="(field !== '板卡类型' && canEdit) || (field == '映射关系')"
                            :creatable="isCreatParams(field)"
                            :min-collapsed-num="1"
                            :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                            @change="(value) => selectElement(value, field, 'edit')"
                            @create="(value) => regularExpressionValidation(value, field, verifyOption[field]?.input_format, verifyOption[field]?.input_remark)">
                                <template #suffixIcon>
                                    <t-popup destroy-on-close placement="top-left">
                                        <template #content>
                                            <div>{{verifyOption[field]?.input_remark}}</div>
                                        </template>
                                        <t-icon v-if="verifyOption[field] && verifyOption[field]?.input_remark !== null" name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                    </t-popup>
                                </template>
                                <t-option
                                v-for="option in allFactorValueDict[field]"
                                    :key="option"
                                    :value="option"
                                    :label="option"/>
                            </t-select>
                        </t-form-item>
                        <t-form-item label="线路侧映射关系" name="lineRelation">
                            <t-button
                                variant="text"
                                theme="primary"
                                :disabled="!canShowLineRelation"
                                @click="showLineRelationDialog(dialogFormData?.['线路侧光层业务'], dialogFormData?.['线路侧光模块'], dialogFormData.lineRelation, nowStatus)"
                            >
                                点击查看
                            </t-button>
                            <div class="relation-hint">
                                已配置 {{ lineRelationNum }} 条映射关系
                            </div>
                        </t-form-item>
                        <t-form-item label="是否创建RDC" name="createRdc">
                            <t-checkbox v-model="dialogFormData.createRdc" @change="onChangeRDC">创建RDC</t-checkbox>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="关联MR需求标识" name="createRdc">
                            <t-checkbox v-model="dialogFormData.associate_MR" @change="onChangeMR">关联MR需求标识</t-checkbox>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.associate_MR" label="MR需求标识" name="mr_ident">
                            <t-input v-model="dialogFormData.mr_ident" :disabled="!dialogFormData.createRdc" placeholder="请填写MR需求标识" @blur="(value) => searchRDC(value, 'edit')">
                                <template #suffixIcon>
                                    <t-popup destroy-on-close placement="top-left">
                                        <template #content>
                                            <div>{{ popupContent }}</div>
                                        </template>
                                        <t-icon name="link" :style="iconStyle" @click="handleIconClick(dialogFormData.mr_ident)"/>
                                    </t-popup>
                                </template>
                            </t-input>
                            <!-- <t-link theme="primary" underline disabled :href="`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${dialogFormData.mr_ident}?teamId=bdv_106024&tenantId=10001`" target="_self">
                                跳转链接
                            </t-link> -->
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="MR创建人工号" name="createNum">
                            <t-select v-model="dialogFormData.createNum" :loading="searchLoading" loadingText="检索中..." filterable :disabled="!dialogFormData.createRdc" placeholder="请填写MR创建人工号" clearable @input-change="getNameOptions" @blur="clearList">
                                <t-option v-for="item in nameOption" :key="item.id" :value="item.value" :label="item.label" :title="item.description"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="需求来源" name="requirementSource">
                            <t-select v-model="dialogFormData.requirementSource" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择需求来源" clearable @popup-visible-change="getRDCsourceOptions">
                                <t-option v-for="item in sourceOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="期望完成日期" name="expectedFinishDate">
                            <t-date-picker
                                v-model="dialogFormData.expectedFinishDate"
                                placeholder="请选择期望完成日期"
                                clearable
                                allow-input
                                @change="(value) => consoleTime(value)"
                                />
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="需求用途" name="requirementPurpose">
                            <t-select v-model="dialogFormData.requirementPurpose" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择需求用途" clearable @popup-visible-change="getRDCpurposeOptions">
                                <t-option v-for="item in purposeOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="客户" name="customer">
                            <t-select v-model="dialogFormData.customer" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请选择客户" clearable @popup-visible-change="getRDCcustomerOptions">
                                <t-option v-for="item in customerOption" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="需求预规划" name="requirementPrePlanVersion">
                            <t-select v-model="dialogFormData.requirementPrePlanVersion" :disabled="!dialogFormData.createRdc" creatable filterable placeholder="请填写需求预规划" clearable @popup-visible-change="getRDCPlanOptions">
                                <t-option v-for="item in linkOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="需求实例化链接" name="requirementInstantiationLink">
                            <t-input v-model="dialogFormData.requirementInstantiationLink" :disabled="!dialogFormData.createRdc" placeholder="请填写需求实例化链接"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="方案文档链接" name="designSpecificationUrl">
                            <t-input v-model="dialogFormData.designSpecificationUrl" :disabled="!dialogFormData.createRdc" placeholder="请填写方案文档链接"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="高优先级子架" name="subrack">
                            <t-input v-model="dialogFormData.subrack" :disabled="!dialogFormData.createRdc" placeholder="请填写高优先级子架"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc" label="需求类型" name="requirementType">
                            <t-select v-model="dialogFormData.requirementType" :disabled="canEdit" filterable placeholder="请选择需求类型" clearable>
                              <template #suffixIcon>
                                <t-popup destroy-on-close placement="top-left">
                                    <template #content>
                                        <div>{{ requirementTypeDes }}</div>
                                    </template>
                                    <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                </t-popup>
                              </template>  
                              <t-option v-for="item in requirementTypes" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && dialogFormData.requirementType === '交付需求'" label="指派业务团队" name="belongTeam">
                            <t-select v-model="dialogFormData.belongTeam" :disabled="canEdit" filterable placeholder="请选择需求类型" clearable>
                              <template #suffixIcon>
                                <t-popup destroy-on-close placement="top-left">
                                    <template #content>
                                        <div>{{ assignTeamDes }}</div>
                                    </template>
                                    <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                </t-popup>
                              </template> 
                              <t-option v-for="item in assignTeams" :key="item.id" :value="item.value" :label="item.label"></t-option>
                            </t-select>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="目标市场" name="targetMarket">
                            <t-input v-model="dialogFormData.targetMarket" :disabled="!dialogFormData.createRdc" placeholder="请填写目标市场"/>
                        </t-form-item>
                        <t-form-item v-show="dialogFormData.createRdc && !dialogFormData.associate_MR" label="市场目标" name="marketTarget">
                            <t-input v-model="dialogFormData.marketTarget" :disabled="!dialogFormData.createRdc" placeholder="请填写市场目标"/>
                        </t-form-item>
                        <!-- <t-form-item label="是否更新单板方案" name="createBoard">
                            <t-checkbox v-model="dialogFormData.createBoard">更新单板方案</t-checkbox>
                        </t-form-item> -->
                    </t-form>
                </div>
                <!-- <template #footer>
                    <t-button @click="handleEditCancel">取消</t-button>
                    <t-button @click="handleEditConfirm">提交审核</t-button>
                </template> -->
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
                        <t-form-item label="单板名称" name="board">
                            <t-textarea v-model="queryFormData.board" :readonly="true" autosize/>
                        </t-form-item>
                        <t-form-item
                        v-for="field in allFactorOptionList"
                        :key="field"
                        :label="field"
                        :name="field">
                            <t-textarea v-model="queryFormData[field]" :readonly="true" autosize/>
                        </t-form-item>
                        <t-form-item label="线路侧映射关系" name="lineRelation">
                            <t-button
                                variant="text"
                                theme="primary"
                                :disabled="queryFormData.lineRelation === 0"
                                @click="showLineRelationDialog(queryFormData?.['线路侧光层业务'], queryFormData?.['线路侧光模块'], queryFormData.lineRelation, nowStatus)"
                            >
                                点击查看
                            </t-button>
                            <div class="relation-hint">
                                已配置 {{ lineRelationNum }} 条映射关系
                            </div>
                        </t-form-item>
                        <t-form-item label="单板方案链接" name="单板方案链接">
                            <t-link
                            :href="queryFormData['单板方案链接']"
                            target="_blank"
                            theme="primary"
                            :style="{display: 'inline-block', width: '100%', wordBreak: 'break-all', whiteSpace: 'normal',}"
                            :title="queryFormData['单板方案链接']">
                                {{ queryFormData['单板方案链接'] }}
                            </t-link>
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
                    <t-button @click="handleViewCancel">关闭</t-button>
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
                            @click="pubDownloadExampleFile('/templates/electric_hardware_board_tree_example.xlsx', '单板树批量导入示例.xlsx')"
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

            <t-dialog
                placement="center"
                body="是否创建单板方案？"
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
                body="是否批量替换单板方案模板？"
                :visible="visibleUpdateiCenter"
                :on-confirm="confirmUpdateiCenter"
                :on-close="closeUpdateiCenter"
            >
                <template #header>
                    <div>
                        <t-icon name="error-circle-filled" color="orange" />
                        <span style="vertical-align: middle">注意 </span>
                        <t-tooltip
                        content="此操作会删除原页面，更新为新模板创建的页面"
                        placement="top-left">
                            <HelpCircleFilledIcon size="1em" />
                        </t-tooltip>
                    </div>
                </template>
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

            <t-dialog
                placement="center"
                body="是否清空当前表单数据？"
                :visible="visibleClearData"
                :on-confirm="confirmClearData"
                :on-close="closeClearData"
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
                width="600px"
                :visible="visibleRequire"
                :on-confirm="confirmRequire"
                :on-close="closeRequire"
            >
                <template #header>
                    <div>
                        <t-icon name="error-circle-filled" color="orange" />
                        <span style="vertical-align: middle">注意</span>
                    </div>
                </template>
                <template #body>
                    <div>
                        <div>是否创建{{ requireFormData.board }}的拆分需求？</div>
                        <div class="require-form">
                            <t-form ref="requireForm" :data="requireFormData" :rules="splitRules" layout="vertical" label-width="140px">
                                <!-- <t-form-item label="" name="createRdc">
                                    <t-checkbox v-model="requireFormData.createRdc">创建RDC</t-checkbox>
                                </t-form-item> -->
                                <t-form-item label="是否创建MR" name="createMR">
                                    <t-checkbox v-model="requireFormData.createMR" @change="onCreateMR">是否创建MR</t-checkbox>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="MR创建人工号" name="createNum">
                                    <t-select v-model="requireFormData.createNum" :loading="searchLoading" loadingText="检索中..." filterable placeholder="请填写创建人工号" clearable @input-change="getNameOptions" @blur="clearList">
                                        <t-option v-for="item in nameOption" :key="item.id" :value="item.value" :label="item.label" :title="item.description"></t-option>
                                    </t-select>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="需求来源" name="requirementSource">
                                    <t-select v-model="requireFormData.requirementSource" creatable filterable placeholder="请选择需求来源" clearable @popup-visible-change="getRDCsourceOptions">
                                        <t-option v-for="item in sourceOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                                    </t-select>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="期望完成日期" name="expectedFinishDate">
                                    <t-date-picker
                                        v-model="requireFormData.expectedFinishDate"
                                        placeholder="请选择期望完成日期"
                                        clearable
                                        allow-input
                                        @change="(value) => consoleTime(value)"
                                        />
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="需求用途" name="requirementPurpose">
                                    <t-select v-model="requireFormData.requirementPurpose" filterable placeholder="请选择需求用途" creatable clearable @popup-visible-change="getRDCpurposeOptions">
                                        <t-option v-for="item in purposeOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                                    </t-select>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="客户" name="customer">
                                    <t-select v-model="requireFormData.customer"  filterable placeholder="请选择客户" creatable clearable @popup-visible-change="getRDCcustomerOptions">
                                        <t-option v-for="item in customerOption" :key="item.id" :value="item.value" :label="item.label"></t-option>
                                    </t-select>
                                </t-form-item>
                                <t-form-item label="需求预规划" name="requirementPrePlanVersion">
                                    <t-select v-model="requireFormData.requirementPrePlanVersion" creatable filterable placeholder="请填写需求预规划" clearable @popup-visible-change="getRDCPlanOptions">
                                        <t-option v-for="item in linkOption" :key="item.id" :value="item.value" :label="item.id"></t-option>
                                    </t-select>
                                </t-form-item>
                                <t-form-item label="需求实例化链接" name="requirementInstantiationLink">
                                    <t-input v-model="requireFormData.requirementInstantiationLink" placeholder="请填写需求实例化链接"/>
                                </t-form-item>
                                <t-form-item label="方案文档链接" name="designSpecificationUrl">
                                    <t-input v-model="requireFormData.designSpecificationUrl" placeholder="请填写方案文档链接"/>
                                </t-form-item>
                                <t-form-item label="高优先级子架" name="subrack">
                                    <t-input v-model="requireFormData.subrack" placeholder="请填写高优先级子架"/>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="目标市场" name="targetMarket">
                                    <t-input v-model="requireFormData.targetMarket" placeholder="请填写目标市场"/>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.createMR" label="市场目标" name="marketTarget">
                                    <t-input v-model="requireFormData.marketTarget" placeholder="请填写市场目标"/>
                                </t-form-item>
                                <t-form-item label="需求类型" name="requirementType">
                                  <t-select v-model="requireFormData.requirementType" filterable placeholder="请选择需求类型" clearable>
                                    <template #suffixIcon>
                                      <t-popup destroy-on-close placement="top-left">
                                          <template #content>
                                              <div>{{ requirementTypeDes }}</div>
                                          </template>
                                          <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                      </t-popup>
                                    </template>
                                    <t-option v-for="item in requirementTypes" :key="item.id" :value="item.value" :label="item.label"></t-option>
                                  </t-select>
                                </t-form-item>
                                <t-form-item v-show="requireFormData.requirementType === '交付需求'" label="指派业务团队" name="belongTeam">
                                  <t-select v-model="requireFormData.belongTeam" filterable placeholder="请选择需求类型" clearable>
                                    <template #suffixIcon>
                                      <t-popup destroy-on-close placement="top-left">
                                          <template #content>
                                              <div>{{ assignTeamDes }}</div>
                                          </template>
                                          <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                      </t-popup>
                                    </template>  
                                    <t-option v-for="item in assignTeams" :key="item.id" :value="item.value" :label="item.label"></t-option>
                                  </t-select>
                                </t-form-item>
                            </t-form>
                        </div>
                    </div>
                </template>
            </t-dialog>

            <t-dialog
                placement="center"
                width="600px"
                :visible="visibleFeatureRequire"
                :on-confirm="confirmFeatureRequire"
                :on-close="closeFeatureRequire"
            >
                <template #header>
                    <div>
                        <t-icon name="error-circle-filled" color="orange" />
                        <span style="vertical-align: middle">注意</span>
                    </div>
                </template>
                <template #body>
                    <div>
                        <div>是否创建{{ featureFormData.board }}的新特性拆分需求？</div>
                        <div class="require-form">
                            <t-form ref="featureForm" :data="featureFormData" :rules="featureRules" layout="vertical" label-width="140px">
                                <t-form-item label="单板名称" name="board">
                                    <t-input v-model="featureFormData.board" readonly placeholder="请填写单板名称" ></t-input>
                                </t-form-item>
                                <t-form-item label="特性/子特性" name="feature">
                                    <t-cascader
                                        v-model="featureFormData.feature"
                                        :options="featureOptionDict"
                                        :filter="pubFilterTreeOptionFun"
                                        :popupProps="{
                                            overlayClassName: 'custom-cascader-menu'
                                        }"
                                        multiple
                                        filterable
                                        clearable
                                        :min-collapsed-num="1"
                                        value-type="full"
                                        :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                                        placeholder="请选择特性/子特性"
                                        @popup-visible-change="getFeatureOption(featureFormData.board)">
                                        <template #suffixIcon>
                                            <t-popup destroy-on-close placement="top-left">
                                                <template #content>
                                                    <div>1、支持模糊搜索<br/>2、多级搜索用$分隔，如：$一级选项$二级选项</div>
                                                </template>
                                                <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                            </t-popup>
                                        </template>
                                    </t-cascader>
                                </t-form-item>
                                <!-- <t-form-item label="关联MR需求标识" name="associate_MR">
                                    <t-checkbox v-model="featureFormData.associate_MR" @change="onChangeMR">关联MR需求标识</t-checkbox>
                                </t-form-item> -->
                                <t-form-item label="MR需求标识" name="mr_ident">
                                    <t-input v-model="featureFormData.mr_ident" placeholder="请填写MR需求标识" @blur="(value) => searchRDC(value, 'feature')">
                                        <template #suffixIcon>
                                            <t-popup destroy-on-close placement="top-left">
                                                <template #content>
                                                    <div>{{ pupupContent }}</div>
                                                </template>
                                                <t-icon name="link" :style="iconFeatureStyle" @click="handleIconClick(featureFormData.mr_ident)"/>
                                            </t-popup>
                                        </template>
                                    </t-input>
                                    <!-- <t-link theme="primary" underline disabled :href="`https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${dialogFormData.mr_ident}?teamId=bdv_106024&tenantId=10001`" target="_self">
                                        跳转链接
                                    </t-link> -->
                                </t-form-item>
                                <t-form-item label="需求类型" name="requirementType">
                                  <t-select v-model="featureFormData.requirementType" filterable placeholder="请选择需求类型" clearable>
                                    <template #suffixIcon>
                                      <t-popup destroy-on-close placement="top-left">
                                          <template #content>
                                              <div>{{ requirementTypeDes }}</div>
                                          </template>
                                          <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                      </t-popup>
                                    </template>
                                    <t-option v-for="item in requirementTypes" :key="item.id" :value="item.value" :label="item.label"></t-option>
                                  </t-select>
                                </t-form-item>
                                <t-form-item v-show="featureFormData.requirementType === '交付需求'" label="指派业务团队" name="belongTeam">
                                  <t-select v-model="featureFormData.belongTeam" filterable placeholder="请选择需求类型" clearable>
                                    <template #suffixIcon>
                                      <t-popup destroy-on-close placement="top-left">
                                          <template #content>
                                              <div>{{ assignTeamDes }}</div>
                                          </template>
                                          <t-icon name="help-circle" style="cursor: pointer; color: #58606b;"/>
                                      </t-popup>
                                    </template>
                                    <t-option v-for="item in assignTeams" :key="item.id" :value="item.value" :label="item.label"></t-option>
                                  </t-select>
                                </t-form-item>
                            </t-form>
                        </div>
                    </div>
                </template>
            </t-dialog>

            <!-- 客户侧映射关系对话框 -->
            <t-dialog
                v-model:visible="customerRelationDialogVisible"
                :width="800"
                header="客户侧映射关系配置"
                :on-confirm="saveCustomerRelation"
                :on-close="closeCustomerRelationDialog"
                confirmBtn="保存"
                cancelBtn="取消"
            >
                <div class="relation-dialog">
                <t-alert theme="info" class="mb-3">
                    配置光层业务与光模块之间的映射关系。行表示光层业务，列表示光模块，勾选表示建立映射。
                </t-alert>
                
                <div class="relation-table-container">
                    <t-table
                    :data="customerRelationTableData"
                    :columns="customerRelationColumns"
                    row-key="service"
                    bordered
                    :max-height="300"
                    >
                    <template #service="{ row }">
                        <div class="service-cell">{{ row.service }}</div>
                    </template>
                    </t-table>
                </div>
                </div>
            </t-dialog>

            <!-- 线路侧映射关系对话框 -->
            <t-dialog
                v-model:visible="lineRelationDialogVisible"
                :width="1500"
                header="线路侧映射关系配置"
            >
                <div class="relation-dialog">
                <t-alert theme="info" class="mb-3">
                    配置光层业务与光模块之间的映射关系。行表示光层业务，列表示光模块，勾选表示建立映射。
                </t-alert>
                
                <div class="relation-table-container">
                    <t-table
                    :data="lineRelationTableData"
                    :columns="lineRelationColumns"
                    row-key="service"
                    bordered
                    >
                    <template #service="{ row }">
                        <div class="service-cell">{{ row.service }}</div>
                    </template>
                    </t-table>
                </div>
                </div>
                <template #footer>
                    <t-button variant="outline" @click="closeLineRelationDialog">取消</t-button>
                    <t-button v-if="nowStatus !== 'view'" theme="primary" @click="() => saveLineRelation(dialogFormData?.['线路侧光层业务'], dialogFormData?.['线路侧光模块'], nowStatus)">保存</t-button>
                </template>
            </t-dialog>
        </div>
    </t-watermark>
</template>

<script setup lang="jsx">
import { ref, onMounted, nextTick, markRaw, onBeforeUnmount, watch, computed, reactive } from 'vue';
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { HelpCircleFilledIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin, Select, DialogPlugin, Checkbox } from 'tdesign-vue-next';
import { pubFormatFileSize, pubDownloadExampleFile, pubCalculateTableHeight } from '@/utils/pub';
import { queryBoardTreeByParams, queryBoardTreeFactorList, queryBoardTreeAllFactorValueDict, addBoardTreeData,
         updateBoardTreeData, deleteBoardTreeData, importExcelBoardTreeData, addBoardGlobalStatusBoardData, addNewPartUpdateChangeAnalysisData, addBoardIcenterPage, syncBoardIcenterPage, updateBoardIcenterPage, queryHardwareTreeRuleDictBySituation, queryBoardOptBizByParams, getRdcSplitTaskResultDict, getTaskResult, queryBoardNewFeatures, addNewFeatureUpdateChangeAnalysisData} from '@/api/electric.js';
import { RDC } from "@/utils/rdc.js";
import { Utils } from "@/utils/utils";
import { pubFilterTreeOptionFun } from '@/utils/pub';
import { h } from 'vue'; 
const router = useRouter();
const user = useUserStore();
const rdcParams = RDC.getRDCParams('PR', 'RequirementPrePlanning');
const sourceParams = RDC.getRDCParams('MR', 'RequirementSource');
const purposeParams = RDC.getRDCParams('MR', 'RequirementPurpose');
const customerParams = RDC.getRDCCustomers('MR', 'Customer');
const headerParams = Utils.getRDCHeader();
const TCheckbox = Checkbox;
const RDCurl = 'https://wsit.zx.zte.com.cn/rdcapi/ZXRDCloud/RDCloud/zte-plm-wic-api/api/workspaces/OTNSW/fields/candidate';
const CUSurl = 'https://wsit.zx.zte.com.cn/rdcapi/ZXRDCloud/RDCloud/zte-plm-wic-api/api/workspaces/OTNSW/remoteDataSource/realTime'
// 固定数据
const showDetails = ref(false);
const canEdit = ref(true);
const customerRelationDialogVisible = ref(false);
const lineRelationDialogVisible = ref(false);
const visibleFeatureRequire = ref(false);
const lineRelationNum = ref(0);
const turnUrl = ref(false);
const verifyOption = ref({
    '单板名称': {
        required_flag: false,
        input_format: null,
        input_remark: null
    }
});
const divideOptions = [
    // {
    //     content: '新增单板拆分',
    //     theme: 'default',
    //     value: 1,
    //     onClick: () => openAddDialog(),
    // },
    {
        content: '新增特性拆分',
        theme: 'default',
        value: 2,
        onClick: () => openFeatureDialog(),
    },
    {
        content: '存量单板拆分',
        theme: 'default',
        value: 3,
        onClick: () => onBatchBreakdownRDC(),
    },
    // {
    //     content: '修改单板拆分',
    //     theme: 'default',
    //     value: 4,
    //     onClick: () => modifyBoardData(),
    // }
]
const buttonOptions = [
  {
    content: '创建单板方案',
    theme: 'default',
    value: 1,
    prefixIcon: () => <t-tooltip
                        content="勾选对应单板，点击本按钮，即可将所选单板，按照预设的单板方案模板在iCenter空间中创建对应的单板方案页面，并将单板方案链接回填到本页面的单板方案链接栏"
                        placement="top-left">
                          <HelpCircleFilledIcon size="1em" />
                      </t-tooltip>,
    onClick: () => onBatchCreateICenter(),
  },
  {
    content: '批量替换单板方案模板',
    value: 2,
    theme: 'default',
    prefixIcon: () => <t-tooltip
                        content="勾选一行或多行单板，点击本按钮，即可将iCenter空间中对应的单板方案页面替换为最新的单板方案模板"
                        placement="top-left">
                          <HelpCircleFilledIcon size="1em" />
                      </t-tooltip>,
    onClick: () => onBatchUpdateICenter(),
  },
  {
    content: '爬取并更新单板方案链接',
    value: 3,
    theme: 'default',
    prefixIcon: () => <t-tooltip
                        content="点击本按钮，即可爬取iCenter空间中所有的单板方案链接，并更新回填到本页面的单板方案链接栏"
                        placement="top-left">
                          <HelpCircleFilledIcon size="1em" />
                      </t-tooltip>,
    onClick: () => onBatchIcenterPage(),
  },
];

const RDC1 = ref('');
const RDC2 = ref('');
const RDC3 = ref('');

const TIP1 = ref('');
const TIP2 = ref('');
const TIP3 = ref('');
const saveLoading = ref(false);
const featureOptionDict = ref([]);
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
    { colKey: 'board', title: () => (<div style={{ textAlign: 'center' }}>单板名称</div>), width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    {
        colKey: '单板方案链接',
        title: '单板方案链接',
        width: '200',
        align: 'center',
        ellipsis: { theme: 'light', placement: 'bottom',},
        cell: (_, { row }) => (<t-link theme="primary" href={row['单板方案链接']} target="_blank" hover="underline">{row['单板方案链接']}</t-link>)
    },
    { colKey: 'operator_person', title: '操作人', width: '200', align: 'center' },
    { colKey: 'update_time', title: '更新时间', width: '200', align: 'center' },
    // { colKey: 'map_relation', title: '映射关系', width: '200', align: 'center' },
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
const updateColumnList = ref([]);
// 原始数据和筛选后数据
const tableDataList = ref([]);
const filterDataList = ref([]);
// 表格选择相关
const selectedRowKeyList = ref([]);
const linkOption = ref([]);
const sourceOption = ref([]);
const purposeOption = ref([]);
const customerOption = ref([]);
const nameOption = ref([]);

const requirementTypes = ref([
  {
    id: 1,
    label: '交付需求',
    value: '交付需求'
  },
  {
    id: 2,
    label: '平台团队需求',
    value: '平台团队需求'
  }
]);
const assignTeams = ref([
  {
    id: 1,
    label: 'L1-神盾业务团队',
    value: 'L1-神盾业务团队' 
  },
  {
    id: 2,
    label: 'L1-雷神业务团队',
    value: 'L1-雷神业务团队' 
  },
  {
    id: 3,
    label: 'L1-星火业务团队',
    value: 'L1-星火业务团队' 
  },
]);
const requirementTypeDes = ref('如果是平台团队需求，那么所有自动拆分出的PR都会被指派至L1-平台团队；如果是交付需求，将按照团队负责的特性进行指派（团队负责特性在特性树-特性&子特性页面查询），其中某些特性可能由多个业务团队负责，这些特性将按照用户选择的默认业务团队进行指派。');
const assignTeamDes = ref('默认业务团队：如果用户的需求类型选择为交付需求，那么展示本选择器，且必填。如果用户的需求类型选择为平台团队需求，那么本选择器不展示。');
const nowStatus = ref('add');
// 后端查询的选择器选项
const allFactorOptionList = ref([]);
const allFactorValueDict = ref({});

const businessFRM = ref([]);
const costLogic = ref([]);
const controlLogic = ref([]);
const subrackSup = ref([]);
const filterValue = ref({});
const loadingCreate = ref(false);
const loadingUpdate = ref(false);
const loadingRefresh = ref(false);
const searchLoading = ref(false);
const loadingBreakdown = ref(false);
const loadingAdd = ref(false); 
const loadingFeature = ref(false); 
const loadingModify = ref(false);
const visibleCreatiCenter = ref(false);
const visibleUpdateiCenter = ref(false);
const visibleUpdateData = ref(false);
const visibleClearData = ref(false);
const visibleRequire = ref(false);
const ifDialog = ref(false);
// 修改相关
const currentEditId = ref(null);
const editDialogVisible = ref(false);
const editForm = ref();
const requireForm = ref();
const featureForm = ref();
const elementTypeMap = ref({
  "FPGA部件承载_电层业务": '纯电_业务FPGA',
  "FRM部件承载_电层业务": '纯电_业务FRM',
  "光模块部件承载_电层业务": '光电_业务FRM',
  // 可以继续添加其他映射...
});
const dialogFormData = ref({
    board: '',
    createRdc: false,
    createBoard: false,
    createMR: false,
    createNum:  '',
    requirementPrePlanVersion: '',
    requirementInstantiationLink: '',
    associate_MR: false,
    mr_ident: '',
    requirementSource: '',
    expectedFinishDate: '',
    requirementPurpose: '',
    targetMarket: '',
    marketTarget: '',
    customer: '',
    subrack: '',
    designSpecificationUrl: '',
    // customerRelation: [],
    lineRelation: [],
    requirementType: '', 
    belongTeam: '',
});

const requireFormData = ref({
    board: '',
    createRdc: false,
    createBoard: false,
    createMR: false,
    createNum:  '',
    requirementPrePlanVersion: '',
    requirementInstantiationLink: '',
    requirementSource: '',
    expectedFinishDate: '',
    requirementPurpose: '',
    targetMarket: '',
    marketTarget: '',
    customer: '',
    subrack: '',
    designSpecificationUrl: '',
    requirementType: '',
    belongTeam: '',
});

const featureFormData = ref({
    board: '',
    associate_MR: false,
    feature: [],
    mr_ident: '',
    requirementType: '',
    belongTeam: ''
});

// 客户侧表格数据
const customerRelationTableData = ref([])
// 线路侧表格数据
const lineRelationTableData = ref([])

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
const isMapped = ref(false);
// 导入相关变量
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);
const turnMR = ref(false);

const tableHeight = ref('900px');

const featureRules = computed(() => {
    // const isMRRequired = featureFormData.value.associate_MR;
    const isMR = turnMR.value;
    const isRequie = featureFormData.value.requirementType === '交付需求'? true:false
    return {
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
        // associate_MR: [
        //     { 
        //         validator: (value) => {
        //             // value 已经是 boolean 类型 true/false
        //             return value === true;  // 直接返回 value 或 value === true
        //         },
        //         message: '请勾选关联MR需求标识',
        //         trigger: 'change',
        //     }
        // ],
        mr_ident: [
            { 
                required: true,
                validator: (value) => {
                if (value) {
                    return !!value?.trim();
                }
                return true;
                },
                message: 'MR需求标识不能为空',
                trigger: 'blur',
            },
            {
                validator: (value) => {
                if (value) {
                    return isMR === true;
                }
                return true;
                },
                message: '请输入有效的MR需求标识',
                trigger: 'blur',
            }
        ],

        requirementType: [
          { 
            required: true, 
            message: '需求类型不能为空', 
            trigger: 'change',
            validator: (value) => {
              return !!value?.trim();
            }
          }
        ],
        belongTeam: [
          { 
            required: isRequie,
            validator: (value) => {
              if(isRequie) {
                return !!value?.trim();
              }
              return true;
            },
            message: '指派业务团队不能为空', 
            trigger: 'change' 
          }
        ],
    }
});

const splitRules = computed(() => {
  const isRequired = requireFormData.value.createMR;
  const isRequie = requireFormData.value.requirementType === '交付需求'? true:false;
  return {

    createNum: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: 'MR创建人工号不能为空',
        trigger: 'change',
      }
    ],

    requirementSource: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求来源不能为空',
        trigger: 'change',
      }
    ],

    requirementPurpose: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求用途不能为空',
        trigger: 'change',
      }
    ],

    customer: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '客户不能为空',
        trigger: 'change',
      }
    ],

    expectedFinishDate: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '期望完成日期不能为空',
        trigger: 'change',
      }
    ],
    
    requirementPrePlanVersion: [
      { 
        required: isRequired || true,
        validator: (value) => {
          if (isRequired || true) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求预规划不能为空',
        trigger: 'change',
      }
    ],
    
    requirementInstantiationLink: [
      { 
        required: isRequired || true,
        validator: (value) => {
          if (isRequired || true) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求实例化链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if ((isRequired || true) && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    designSpecificationUrl: [
      { 
        required: isRequired || true,
        validator: (value) => {
          if (isRequired || true) {
            return !!value?.trim();
          }
          return true;
        },
        message: '方案文档链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if ((isRequired || true) && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    subrack: [
      { 
        required: isRequired && false,
        validator: (value) => {
          if (isRequired && false) {
            return !!value?.trim();
          }
          return true;
        },
        message: '高优先级子架不能为空',
        trigger: 'blur',
      },
    ],

    requirementType: [
      { 
        required: true, 
        message: '需求类型不能为空', 
        trigger: 'change',
        validator: (value) => {
          return !!value?.trim();
        }
      }
    ],
    belongTeam: [
      { 
        required: isRequie,
        validator: (value) => {
          if(isRequie) {
            return !!value?.trim();
          }
          return true;
        },
        message: '指派业务团队不能为空', 
        trigger: 'change' 
      }
    ],
  };
});

const rdcRules = computed(() => {
  const isRDCRequired = dialogFormData.value.createRdc
  const isRequired = dialogFormData.value.createRdc && !dialogFormData.value.associate_MR;
  const isMRRequired = dialogFormData.value.associate_MR;
  const isRequie = dialogFormData.value.requirementType === '交付需求'? true:false;
  const isMR = turnUrl.value;
  return {
    // customerRelation: [
    //   { 
    //     required: true,
    //     validator: (value) => {
    //       return value.length > 0;
    //     },
    //     message: '客户侧映射关系不能为空',
    //     trigger: 'change',
    //   }
    // ],
    requirementType: [
      { 
        required: isRDCRequired, 
        message: '需求类型不能为空', 
        trigger: 'change',
        validator: (value) => {
          if (isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
      }
    ],
    belongTeam: [
      { 
        required: isRDCRequired && isRequie,
        validator: (value) => {
          if(isRDCRequired && isRequie) {
            return !!value?.trim();
          }
          return true;
        },
        message: '指派业务团队不能为空', 
        trigger: 'change' 
      }
    ],

    mr_ident: [
      { 
        required: isMRRequired,
        validator: (value) => {
          if (isMRRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: 'MR需求标识不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if (value && isMRRequired) {
            return isMR === true;
          }
          return true;
        },
        message: '请输入有效的MR需求标识',
        trigger: 'blur',
      }
    ],

    createNum: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: 'MR创建人工号不能为空',
        trigger: 'change',
      }
    ],

    requirementSource: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求来源不能为空',
        trigger: 'change',
      }
    ],

    requirementPurpose: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求用途不能为空',
        trigger: 'change',
      }
    ],

    customer: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '客户不能为空',
        trigger: 'change',
      }
    ],

    expectedFinishDate: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '期望完成日期不能为空',
        trigger: 'change',
      }
    ],
    
    requirementPrePlanVersion: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求预规划不能为空',
        trigger: 'change',
      }
    ],
    
    requirementInstantiationLink: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求实例化链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if (isRDCRequired && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    designSpecificationUrl: [
      { 
        required: isRDCRequired,
        validator: (value) => {
          if (isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '方案文档链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if (isRDCRequired && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    subrack: [
      { 
        required: isRequired && false,
        validator: (value) => {
          if (isRequired && false) {
            return !!value?.trim();
          }
          return true;
        },
        message: '高优先级子架不能为空',
        trigger: 'blur',
      },
    ]
  };
});

const mrRules = computed(() => {
  const isRDCRequired = dialogFormData.value.createRdc
  const isRequired = dialogFormData.value.createRdc && dialogFormData.value.createMR;
  const isRequie = dialogFormData.value.requirementType === '交付需求'? true:false
  return {
    requirementType: [
      { 
        required: isRDCRequired, 
        message: '需求类型不能为空', 
        trigger: 'change',
        validator: (value) => {
        if(isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
      }
    ],
    belongTeam: [
      { 
        required: isRDCRequired && isRequie,
        validator: (value) => {
          if(isRDCRequired && isRequie) {
            return !!value?.trim();
          }
          return true;
        },
        message: '指派业务团队不能为空', 
        trigger: 'change' 
      }
    ],
    createNum: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: 'MR创建人工号不能为空',
        trigger: 'change',
      }
    ],

    requirementSource: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求来源不能为空',
        trigger: 'change',
      }
    ],

    requirementPurpose: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求用途不能为空',
        trigger: 'change',
      }
    ],

    customer: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '客户不能为空',
        trigger: 'change',
      }
    ],

    expectedFinishDate: [
      { 
        required: isRequired,
        validator: (value) => {
          if (isRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '期望完成日期不能为空',
        trigger: 'change',
      }
    ],
    
    requirementPrePlanVersion: [
      { 
        required: isRDCRequired,
        validator: (value) => {
          if (isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求预规划不能为空',
        trigger: 'change',
      }
    ],
    
    requirementInstantiationLink: [
      { 
        required: isRDCRequired,
        validator: (value) => {
          if (isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '需求实例化链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if (isRDCRequired && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    designSpecificationUrl: [
      { 
        required: isRDCRequired,
        validator: (value) => {
          if (isRDCRequired) {
            return !!value?.trim();
          }
          return true;
        },
        message: '方案文档链接不能为空',
        trigger: 'blur',
      },
      {
        validator: (value) => {
          if (isRDCRequired && value) {
            return /^https?:\/\//.test(value) || /^http?:\/\//.test(value);
          }
          return true;
        },
        message: '请输入有效的链接地址',
        trigger: 'blur',
      }
    ],

    subrack: [
      { 
        required: isRequired && false,
        validator: (value) => {
          if (isRequired && false) {
            return !!value?.trim();
          }
          return true;
        },
        message: '高优先级子架不能为空',
        trigger: 'blur',
      },
    ]
  };
});

const rulesMR = computed(() => {
  return {
    board: [
      { required: true, message: '单板名称不能为空', trigger: 'blur' },
      { validator: (value) => { return !!value?.trim(); } }
    ],
    
    // 动态字段的验证规则（根据您的需求添加）
    ...Object.fromEntries(
      allFactorOptionList.value.map((field) => [
        field,
        [
          { 
            required: verifyOption.value[field]?.required_flag || false,
            message: `${field}不能为空`,
            trigger: 'change',
            validator: (value) => {
              const isRequired = verifyOption.value[field]?.required_flag;
              if (isRequired) {
                if (Array.isArray(value)) {
                  return value.length > 0;
                }
                return !!value?.trim();
              }
              return true;
            }
          }
        ]
      ])
    ),
    
    lineRelation: [
        { 
          required: verifyOption.value['线路侧光层业务']?.required_flag && verifyOption.value['线路侧光模块']?.required_flag || isMapped.value,
          validator: (value) => {
            if (verifyOption.value['线路侧光层业务']?.required_flag && verifyOption.value['线路侧光模块']?.required_flag || isMapped.value) {
              return !!value?.trim();
            }
            return true;
          },
          message: '线路侧映射关系不能为空',
          trigger: 'blur',
        }
      ],
    // 合并 RDC 规则
    ...mrRules.value,
  };
}
);

const rules = computed(() => {
  return {
    board: [
      { required: true, message: '单板名称不能为空', trigger: 'blur' },
      { validator: (value) => { return !!value?.trim(); } }
    ],
    
    // 动态字段的验证规则（根据您的需求添加）
    ...Object.fromEntries(
      allFactorOptionList.value.map((field) => [
        field,
        [
          { 
            required: verifyOption.value[field]?.required_flag || false,
            message: `${field}不能为空`,
            trigger: 'change',
            validator: (value) => {
              const isRequired = verifyOption.value[field]?.required_flag;
              if (isRequired) {
                if (Array.isArray(value)) {
                  return value.length > 0;
                }
                return !!value?.trim();
              }
              return true;
            }
          }
        ]
      ])
    ),
    
    lineRelation: [
        { 
          required: verifyOption.value['线路侧光层业务']?.required_flag && verifyOption.value['线路侧光模块']?.required_flag || isMapped.value,
          validator: (value) => {
            if (verifyOption.value['线路侧光层业务']?.required_flag && verifyOption.value['线路侧光模块']?.required_flag || isMapped.value) {
              return !!value?.trim();
            }
            return true;
          },
          message: '线路侧映射关系不能为空',
          trigger: 'blur',
        }
      ],
    // 合并 RDC 规则
    ...rdcRules.value,
    }
  }
);

const popupContent = computed(() => {
  return dialogFormData.value.mr_ident && turnUrl.value ? '点击跳转链接' : '请先填写有效MR标识'
})

const pupupContent = computed(() => {
  return featureFormData.value.mr_ident && turnMR.value ? '点击跳转链接' : '请先填写有效MR标识'
})

const iconStyle = computed(() => {
  const baseStyle = 'cursor: pointer;'
  if (dialogFormData.value.mr_ident && turnUrl.value) {
    return baseStyle + 'color: #0052D9;'
  } else {
    return baseStyle + 'color: #c5c5c5;'
  }
})

const iconFeatureStyle = computed(() => {
  const baseStyle = 'cursor: pointer;'
  if (featureFormData.value.mr_ident && turnMR.value) {
    return baseStyle + 'color: #0052D9;'
  } else {
    return baseStyle + 'color: #c5c5c5;'
  }
})

watch(() => turnUrl.value, (newValue) => {
  // 延迟执行，确保表单已更新
  setTimeout(() => {
    if (editForm.value) {
      editForm.value.clearValidate?.('mr_ident');
      // 或者触发重新验证
      editForm.value.validate?.('mr_ident');
    }
  }, 100);
}, { immediate: true });

watch(() => turnMR.value, (newValue) => {
  // 延迟执行，确保表单已更新
  setTimeout(() => {
    if (featureForm.value) {
      featureForm.value.clearValidate?.('mr_ident');
      // 或者触发重新验证
      featureForm.value.validate?.('mr_ident');
    }
  }, 100);
}, { immediate: true });

const updateRulesBasedOnVerifyOption = () => {
  const newRules = { ...rules.value };
  
  allFactorOptionList.value.forEach((field) => {
    const isRequired = verifyOption.value[field]?.required_flag;
    
    if (isRequired) {
      // 必填字段
      newRules[field] = [
        {
          required: true,
          message: `${field}不能为空`,
          trigger: 'change',
          validator: (value) => {
            // 处理数组类型的值（多选框）
            if (Array.isArray(value)) {
              return value.length > 0;
            }
            return !!value?.trim();
          }
        }
      ];
    } else {
      // 非必填字段 - 可以设置为空数组或只包含非必填规则
      newRules[field] = [];
      // 或者保持简单验证
      // newRules[field] = [
      //   { required: false, trigger: 'change' }
      // ];
    }
  });
  
  rules.value = newRules;
};

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

onBeforeUnmount(() => {
  // 组件销毁前清理
  resetUploadData();
});

// 选中事件处理
const handleSelectChange = (keys) => {
    selectedRowKeyList.value = keys;
};

const onActiveChange = (highlightRowKeys, ctx) => {
  console.log(highlightRowKeys, ctx);
};

const handleIconClick = (val) => {
  if (!val || !turnUrl.value || !turnMR.value) {
    // MessagePlugin.warning('请先填写MR需求标识')
    return;
  }
  
  const url = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${val}?teamId=bdv_106024&tenantId=10001`
  window.open(url, '_blank')
};

const searchRDC = async (val, type) => {
    try {
        const response = await fetch('https://wsit.zx.zte.com.cn/rdcapi/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1/work_items/query_workitems', {
            method: 'POST',
            headers: headerParams,
            body: JSON.stringify([val]),
        });
        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();

        if(responseData.bo?.items[0]?.workItemTypeKey === 'MR' && type === 'edit') {
            turnUrl.value = true
            // editForm.value.clearValidate(['mr_ident']);
        } else if (responseData.bo?.items[0]?.workItemTypeKey === 'MR' && type === 'feature') {
            turnMR.value = true
        } else {
            // MessagePlugin.warning('非MR需求标识，请重新填写')
            turnUrl.value = false
            turnMR.value = false
        }
    } catch (error) {
        console.error('请求出错:', error);
        MessagePlugin.error(response.code.msgId);
        turnUrl.value = false
        turnMR.value = false
    }
};

const onChangeMR = (val) => {
  // 只需要更新值，验证规则会自动更新
  dialogFormData.value.associate_MR = val;
  if(!val) {
    dialogFormData.value.createNum =  '';
    dialogFormData.value.requirementPrePlanVersion = '';
    dialogFormData.value.requirementInstantiationLink = '';
    dialogFormData.value.mr_ident = '';
    dialogFormData.value.requirementSource = '';
    dialogFormData.value.expectedFinishDate = '';
    dialogFormData.value.requirementPurpose = '';
    dialogFormData.value.targetMarket = '';
    dialogFormData.value.marketTarget = '';
    dialogFormData.value.customer = '';
    dialogFormData.value.subrack ='';
  }
  turnUrl.value = false;
  // 可选：清除相关字段的验证状态
  nextTick(() => {
    if (editForm.value) {
      editForm.value.clearValidate(['createNum', 'requirementPrePlanVersion', 'requirementInstantiationLink', 'requirementSource', 'expectedFinishDate', 'requirementPurpose', 'customer', 'mr_ident', 'designSpecificationUrl']);
      //editForm.value.reset();
    }
  });
};

const onCreateMR = (val) => {
    dialogFormData.value.createMR = val;
    if(!val) {
        dialogFormData.value.associate_MR = false;
        dialogFormData.value.createNum = '';
        dialogFormData.value.requirementPrePlanVersion = '';
        dialogFormData.value.requirementInstantiationLink = '';
        dialogFormData.value.mr_ident = '';
        dialogFormData.value.requirementSource = '';
        dialogFormData.value.expectedFinishDate = '';
        dialogFormData.value.requirementPurpose = '';
        dialogFormData.value.targetMarket = '';
        dialogFormData.value.marketTarget = '';
        dialogFormData.value.customer = '';
        dialogFormData.value.subrack ='';
    }
    nextTick(() => {
        if (addFormRef.value) {
            addFormRef.value.clearValidate(['createNum', 'requirementPrePlanVersion', 'requirementInstantiationLink', 'requirementSource', 'expectedFinishDate', 'requirementPurpose', 'customer', 'mr_ident', 'designSpecificationUrl']);
            //   addFormRef.value.reset();
        }
        if (requireForm.value) {
            requireForm.value.clearValidate(['createNum', 'requirementPrePlanVersion', 'requirementInstantiationLink', 'requirementSource', 'expectedFinishDate', 'requirementPurpose', 'customer', 'mr_ident', 'designSpecificationUrl']);
            //   addFormRef.value.reset();
        }
    });
};

const onChangeRDC = (val) => {
  // 只需要更新值，验证规则会自动更新
  dialogFormData.value.createRdc = val;
  if(!val) {
    dialogFormData.value.associate_MR = false;
    dialogFormData.value.createNum = '';
    dialogFormData.value.requirementPrePlanVersion = '';
    dialogFormData.value.requirementInstantiationLink = '';
    dialogFormData.value.mr_ident = '';
    dialogFormData.value.requirementSource = '';
    dialogFormData.value.expectedFinishDate = '';
    dialogFormData.value.requirementPurpose = '';
    dialogFormData.value.targetMarket = '';
    dialogFormData.value.marketTarget = '';
    dialogFormData.value.customer = '';
    dialogFormData.value.subrack ='';
  }
  turnUrl.value = false;
  // 可选：清除相关字段的验证状态
  nextTick(() => {
    if (addFormRef.value && !val) {
      addFormRef.value.clearValidate(['createNum', 'requirementPrePlanVersion', 'requirementInstantiationLink', 'requirementSource', 'expectedFinishDate', 'requirementPurpose', 'customer', 'mr_ident', 'designSpecificationUrl']);
    //   addFormRef.value.reset();
    }
    if (editForm.value && !val) {
      editForm.value.clearValidate(['createNum', 'requirementPrePlanVersion', 'requirementInstantiationLink', 'requirementSource', 'expectedFinishDate', 'requirementPurpose', 'customer', 'mr_ident', 'designSpecificationUrl']);
    //   editForm.value.reset();
    }
  });
};

const refreshData = async () => {
    selectedRowKeyList.value = [];

    const [
        queryBoardTreeByParamsResponse,
        queryBoardTreeFactorListResponse,
        queryBoardTreeAllFactorValueDictResponse,
    ] = await Promise.all([
        queryBoardTreeByParams(),
        queryBoardTreeFactorList(),
        queryBoardTreeAllFactorValueDict(),
    ]);

    // const map_relation = `C04M4-A01<->100G_SD-FEC1-NONDIFF-20%_QPSK,C04M4-A01<->400G_SD-FEC2-NODIFF-20%_DP_QPSK`

    // tableDataList.value = (queryBoardTreeByParamsResponse.data || []).map(item => ({
    //     ...item,
    //     map_relation: map_relation
    // }));
    tableDataList.value = queryBoardTreeByParamsResponse.data || [];
    allFactorOptionList.value = queryBoardTreeFactorListResponse.data || [];
    allFactorValueDict.value = queryBoardTreeAllFactorValueDictResponse.data || {};
    filterDataList.value = tableDataList.value

    subrackSup.value = allFactorValueDict.value['单板支持的子架'];
    businessFRM.value = allFactorValueDict.value['业务FRM芯片'];
    costLogic.value = allFactorValueDict.value['开销逻辑'];
    controlLogic.value = allFactorValueDict.value['控制逻辑'];

    getClearString(allFactorValueDict.value);

    await refactorVerifyOption(allFactorOptionList.value);
    dynamicUpdateColumn();
};

const refactorVerifyOption = async (arrayData) => {
    arrayData.forEach(key => {
    if (!verifyOption.value[key]) {
        // 防止覆盖已存在的属性
        verifyOption.value[key] = {
            required_flag: false,
            input_format: null,
            input_remark: null
        };
    }
    // else if (!verifyOption.value[key] && key === '板卡类型') {
    //     verifyOption.value[key] = {
    //         required_flag: true,
    //         input_format: null,
    //         input_remark: null
    //     };
    // }
});
};

const resetOption = async () => {
    const queryBoardTreeAllFactorValueDictResponse = await queryBoardTreeAllFactorValueDict();
    allFactorValueDict.value = queryBoardTreeAllFactorValueDictResponse.data || {};
};

const isCreatParams = (field) => {
    const fieldArray = ['单板硬件PCB', '单板配置类型', '线路侧光层业务', '客户侧光模块', '线路侧光模块']
    if (fieldArray.includes(field)) {
        return true;
    } else {
        return false;
    }
};

const isMultiple = (field) => {
    return field !== '单板业务模型';
};

const insertOption = (value, field) => {
    // 可能的问题：某个数组变量没有初始化
    // 例如：
    // if (!someArray) {  // 如果没有判断undefined
    //     someArray.push(value);  // 这里会报错
    // }
    
    // 解决方案：确保数组已初始化
    if (!allFactorValueDict.value[field]) {
        allFactorValueDict.value[field] = []; // 初始化数组
    }
    allFactorValueDict.value[field].push(value);
    
    // 或者如果是响应式数据
    // if (!dialogFormData.value[field]) {
    //     dialogFormData.value[field] = []; // 初始化数组
    // }
    // dialogFormData.value[field].push(value);
};

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

    // 1. 处理 board 字段
    const boardCountMap = countValues(filterDataList.value, 'board');
    factorValueDict.value["board"] = Array.from(boardCountMap.entries()).map(([value, count]) => {
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

    updateColumnList.value = tableColumnList.value;
    const boardIndex = updateColumnList.value.findIndex(col => col.colKey === 'board');
    const statusIndex = updateColumnList.value.findIndex(col => col.colKey === 'status');
    if (boardIndex === -1 || statusIndex === -1) {
        return null;
    }

    // 更新单板筛选
    updateColumnList.value[boardIndex]['filter'] = {
        component: markRaw(Select),
        props: {
            options: [
                { label: '全选', checkAll: true },
                ...factorValueDict.value.board.map(item => ({
                    label: item['label'],
                    value: item['value'],
                }))
            ],
            placeholder: '请选择单板',
            multiple: true,
            filterable: true,
            clearable: true,
        },
        showConfirmAndReset: true,
    };

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
    };

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
    newTableColumns.splice(boardIndex + 1, 0, ...newColumns);
    updateColumnList.value = newTableColumns;

    return null;
};

const getFeatureOption = async (boardName) => {
    try {
        const param = {
            board: boardName,
        }
        const dictResponse = await queryBoardNewFeatures(param);
        featureOptionDict.value = dictResponse.data || [];
    } catch (error) {
        MessagePlugin.error('数据加载失败，请重试');
    }
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

const openFeatureDialog = async () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要拆分的行');
        return;
    }
    if (selectCount > 1) {
        MessagePlugin.warning('最多只能选一块单板');
        return;
    }
    const itemObject = filterDataList.value.find(
        item => item.id === selectedRowKeyList.value[0]
    ) ?? {};
    featureFormData.value.board = itemObject.board
    visibleFeatureRequire.value = true;
    featureForm.value.clearValidate();
};

const modifyBoardData = async () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要拆分的行');
        return;
    }
    if (selectCount > 1) {
        MessagePlugin.warning('最多只能选一块单板');
        return;
    }
    const itemObject = filterDataList.value.find(
        item => item.id === selectedRowKeyList.value[0]
    ) ?? {};
    openEditDialog(itemObject);
};

const filterData = (filters) => {
    const timer = setTimeout(() => {
        clearTimeout(timer);
        const newData = tableDataList.value.filter((item) => {
            let result = true;
            // 根据单板名称过滤
            if (result && filters["board"] && filters["board"].length > 0) {
                result = filters["board"].some(selectedValue => item['board']===selectedValue);
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

const extractEmployeeData = (data) => {
  return Object.keys(data).map((key, index) => {
    // 从键名中提取工号（假设工号是末尾的数字）
    const match = key.match(/(\d+)$/);
    const employeeId = match ? match[1] : '';
    return {
      id: index + 1,
      label: key,
      value: employeeId,
      description: data[key],
    };
  });
};

const clearList = () => {
    nameOption.value = []
};

const regularExpressionValidation = async (value, field, format, remark) => {
    if (value === null || value === '' && field === '单板名称') {
        // MessagePlugin.warning(`请填写${field}`);
        return true;
    }
    // 如果format为空，直接通过校验
    if (!verifyOption.value[field] || format === null || format === undefined) {
        insertOption(value, field);
        return true;
    }

    try {
        // 如果format是字符串，需要转换成正则表达式
        let regex;
        
        if (typeof format === 'string') {
            // 假设format是类似 "/^[a-zA-Z0-9]+$/" 的字符串
            if (format.startsWith('/') && format.endsWith('/')) {
                // 提取正则表达式和标志
                const lastSlashIndex = format.lastIndexOf('/');
                const pattern = format.substring(1, lastSlashIndex);
                const flags = format.substring(lastSlashIndex + 1);
                regex = new RegExp(pattern, flags);
            } else {
                // 如果不是以/开头结尾，直接作为普通字符串模式
                regex = new RegExp(format);
            }
        } else if (format instanceof RegExp) {
            // 如果已经是正则对象，直接使用
            regex = format;
        } else {
            MessagePlugin.error(`字段"${field}"的format参数必须是字符串或正则表达式`);
            // 校验不通过，直接返回，不会执行insertOption
            return false;
        }
        
        // 执行正则测试
        const testResult = regex.test(value);
        
        if (!testResult) {
            MessagePlugin.error(`${field}中"${value}"填写格式有误，请修改！${remark}`);
            return false;
        }
        
        // 校验通过，执行插入操作
        insertOption(value, field);
        return true;
    } catch (error) {
        MessagePlugin.error(`字段"${field}"的正则表达式错误: ${error.message}`);
        // 正则表达式本身有错误，不执行插入操作
        return false;
    }
};

const selectElement = async (val, field, operation) => {
    if (val && val.length > 0 && field === '板卡类型') {
        canEdit.value = false;
        const boardList = val.join(',');
        verifyOption.value = await getVerfyOptionData('单板', boardList);
        regularExpressionValidation(dialogFormData.value.board, '单板名称', verifyOption.value['单板名称']?.input_format, verifyOption.value['单板名称']?.input_remark)
    } else if (val && val.length === 0 && field === '板卡类型' && operation === 'add' && ifDialog.value) {
        visibleClearData.value = true;
    } else if (val && val.length === 0 && field === '板卡类型' && operation === 'edit') {
        resetDialog('clearNotAll');
    } else if (val && val.length > 0 && (field === '线路侧光层业务' || field === '线路侧光模块')) {
        if (field === '线路侧光层业务' && dialogFormData.value['线路侧光模块'].length > 0) {
            const newValue = val[val.length - 1]
            generateLineRelationTable(val, dialogFormData.value['线路侧光模块'], dialogFormData.value.lineRelation, nowStatus.value, newValue, null);
        } else if (field === '线路侧光模块' && dialogFormData.value['线路侧光层业务'].length > 0) {
            const newValue = val[val.length - 1]
            generateLineRelationTable(dialogFormData.value['线路侧光层业务'], val, dialogFormData.value.lineRelation, nowStatus.value, null, newValue);
        } else {
            lineRelationTableData.value = [];
            return;
        }
    } else if (val && val.length === 0 && (field === '线路侧光层业务' || field === '线路侧光模块')) {
        lineRelationTableData.value = [];
        return;
    } else if (val && val.length > 0 && field === '部件承载电层业务模式') {
        allFactorValueDict.value['业务FRM芯片'] = [];
        allFactorValueDict.value['开销逻辑'] = [];
        allFactorValueDict.value['控制逻辑'] = [];
        filterBoardData(val);
        return;
    } else if (val && val.length > 0 && field === '产品') {
        allFactorValueDict.value['单板支持的子架'] = [];
        filterSubrackData(val);
        return;
    }
};

const transformMappingData = (originalData) => {
    return originalData.map(item => ({
        module: item.opt,
        service: item.biz,
        checked: true
    }));
};

const getMappingRelationship = async (Board, type, Opt, Biz, Flag, Status) => {
    try {

        const formParams = {
            board: Board,
            l_c_type: type,
            opt: Opt,
            biz: Biz,
            part_match_flag: Flag,
        }

        const response = await queryBoardOptBizByParams(formParams);
        const relationData = transformMappingData(response.data);

        return relationData;
    
    } catch (error) {
        MessagePlugin.error('光模块-光层业务映射关系获取失败！');
    }
};

const getVerfyOptionData = async (HardwareType, Situation) => {
    try {

        const formData = new FormData();
        formData.append('hardware_type', HardwareType);
        formData.append('situation', Situation);

        const response = await queryHardwareTreeRuleDictBySituation(formData);

        return response.data;
    
    } catch (error) {
        MessagePlugin.error('校验规则获取失败！');
    }
};

const getNameOptions = async (searchValue, context) => {
    try {
        searchLoading.value = true;
        const response = await fetch(`https://wdmpi.zx.zte.com.cn/baseapi/userinfo/getuser?user=${searchValue}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();
        nameOption.value = extractEmployeeData(responseData.body.data);
        searchLoading.value = false;
    } catch (error) {
        console.error('请求出错:', error);
        MessagePlugin.error(response.message);
        searchLoading.value = false;
    }

};

const getRDCPlanOptions = async () => {
    linkOption.value = await getRDCLinkOptions(RDCurl, headerParams, rdcParams, 'RDC');
};

const getRDCsourceOptions = async () => {
    sourceOption.value = await getRDCLinkOptions(RDCurl, headerParams, sourceParams, 'RDC');
};

const getRDCpurposeOptions = async () => {
    purposeOption.value = await getRDCLinkOptions(RDCurl, headerParams, purposeParams, 'RDC');
};

const getRDCcustomerOptions = async () => {
    customerOption.value = await getRDCLinkOptions(CUSurl, headerParams, customerParams, 'OTH');
};

const getRDCLinkOptions = async (url, headers, body, type) => {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body),
        });
        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();

        const paramOption = type === 'RDC'?responseData.bo.textPickList:responseData.bo;

        return paramOption;

    } catch (error) {
        console.error('请求出错:', error);
        MessagePlugin.error(response.message);
    }

};

const onBatchBreakdownRDC = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要拆分的行');
        return;
    }
    if (selectCount > 1) {
        MessagePlugin.warning('最多只能选一块单板');
        return;
    }
    const urlLink = filterDataList.value.find(item => item.id === selectedRowKeyList.value[0])?.['单板方案链接'];
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    requireFormData.value.board = selectCountData[0].board
    requireFormData.value.designSpecificationUrl = urlLink
    visibleRequire.value = true
};

const onBatchCreateICenter = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要创建的行');
        return;
    }
    if (selectCount > 1) {
        MessagePlugin.warning('最多只能选一块单板');
        return;
    }
    visibleCreatiCenter.value = true;
}

const onBatchUpdateICenter  = () => {
    const selectCount = selectedRowKeyList.value.length;
    if (selectCount === 0) {
        MessagePlugin.warning('请先选择要创建的行');
        return;
    }
    visibleUpdateiCenter.value = true;
}

const onBatchIcenterPage = () => {
    visibleUpdateData.value = true;
}

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

const confirmUpdateiCenter = async () => {
    loadingUpdate.value = true 
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    const resultData = transformData(selectCountData);
    visibleUpdateiCenter.value = false
    const postData = {
        board: resultData
    }
    await RefreshICenter(postData);
}

const RefreshICenterData = async (data) => {
    try {
      const refreshICenterResponse = await syncBoardIcenterPage(data);
      loadingRefresh.value = false;
      MessagePlugin.success(refreshICenterResponse.message);
      await refreshData();
    } catch (error) {
        console.log('更新数据失败，请重试', error);
        loadingRefresh.value = false;
    }
};

const closeUpdateiCenter = () => {
    visibleUpdateiCenter.value = false
}

const confirmUpdateData = async () => {
    loadingRefresh.value = true;
    visibleUpdateData.value = false;
    const postData = {
        data_type: "board"
    }
    await RefreshICenterData(postData);
}

const transformData = (data) => {
    return data.map(item => item.board).join(',');
}

const RefreshICenter = async (data) => {
    try {
        const refreshICenterResponse = await updateBoardIcenterPage(data);
        loadingUpdate.value = false;
        MessagePlugin.success(refreshICenterResponse.message);
        await refreshData();
    } catch (error) {
        console.log('更新数据失败，请重试', error);
        loadingUpdate.value = false;
    }
};

const confirmClearData = () => {
    resetDialog('clearAll');
    visibleClearData.value = false
}

const closeClearData = () => {
    visibleClearData.value = false
}

const closeUpdateData = () => {
    visibleUpdateData.value = false
}

const consoleTime = (time) => {
    console.log('Expected Completion Date:', time);
}

const confirmCreatiCenter = async () => {
    loadingCreate.value = true;
    visibleCreatiCenter.value = false; 
    const selectCountData = extractNodesByIds(tableDataList.value, selectedRowKeyList.value);
    await comfirmICenter(selectCountData[0].board);
    await refreshData();
}

const comfirmICenter = async (data) => {
    try {
        const requestParams = {
            board: data,
        };
        const comfirmICenterResponse = await addBoardIcenterPage(requestParams);

        if(comfirmICenterResponse.data && comfirmICenterResponse.data.length === 0) {
            MessagePlugin.success(comfirmICenterResponse.message);
        } else {
            comfirmICenterResponse.data.map((item, index) => {
                NotifyPlugin.warning({
                    title: '警告',
                    content: `${item} 单板方案页面已存在！`,
                    duration: 10000,
                })
            })
        }
        loadingCreate.value = false;
    } catch (error) {
        console.log('批量创建失败，请重试', error);
        loadingCreate.value = false;
    }
}

const closeCreatiCenter = () => {
    visibleCreatiCenter.value = false;
}

// 修改相关方法
const openEditDialog = async (row) => {
    currentEditId.value = row.id;
    const services = row['线路侧光层业务'];
    const modules = row['线路侧光模块'];
    const lineRelationData = await getMappingRelationship(row.board, '线路侧', modules, services, false, row.status)
    lineRelationNum.value = lineRelationData.length;
    dialogFormData.value = {
        id: row.id,
        board: row.board,
        createRdc: false,
        createBoard: false,
        createMR: false,
        createNum: '',
        requirementPrePlanVersion: '',
        requirementInstantiationLink: '',
        designSpecificationUrl: row['单板方案链接'],
        lineRelation: lineRelationData
    };
    nowStatus.value = "edit";
    // allFactorOptionList.value.forEach(field => {
    //     dialogFormData.value[field] = row[field]?row[field].split(','):[]
    // });
    allFactorOptionList.value.forEach(field => {
        // 转换字符串为数组
        let newArray = [];

        if (field === '单板业务模型') {
            dialogFormData.value[field] = row[field].trim();
        } else {
            newArray = (row[field] || '').split(',').filter(item => item.trim() !== '');
            dialogFormData.value[field] = newArray;
        }

        if (field === '业务FRM芯片' || field === '单板支持的子架' || field === '开销逻辑' || field === '控制逻辑') {
          if (Array.isArray(dialogFormData.value[field])) {
           allFactorValueDict.value[field] = allFactorValueDict.value[field].map(item => {
              return typeof item === 'string' ? item.replace(/^.*?->/, '') : item;
            });
          }
        }

        // if (field === '产品' && Array.isArray(dialogFormData.value[field])) {
        //   const fieldArray = dialogFormData.value[field]
        //   filterSubrackData(fieldArray);
        //   console.log("allFactorValueDict.value", allFactorValueDict.value['单板支持的子架']);
        // }
        
        // if (field === '部件承载电层业务模式' && Array.isArray(dialogFormData.value[field])) {
        //   const fieldArrays = dialogFormData.value[field]
        //   filterBoardData(fieldArrays);
        // }
        // 赋值给dialogFormData
        
        // 合并去重并赋值给allFactorValueDict
        const existing = allFactorValueDict.value[field] || [];
        allFactorValueDict.value[field] = [...new Set([...existing, ...newArray])];
    });

    // if (dialogFormData.value['线路侧光层业务'].length > 0 && dialogFormData.value['线路侧光模块'].length > 0) {
    //     generateLineRelationTable(dialogFormData.value['线路侧光层业务'].length, dialogFormData.value['线路侧光模块'], dialogFormData.value.lineRelation, nowStatus.value, null, null);
    // } 

    if (dialogFormData.value['板卡类型'].length > 0) {
        selectElement(dialogFormData.value['板卡类型'], '板卡类型', 'edit')
    } else {
        MessagePlugin.warning('请先选择"板卡类型"后，再修改其他项。');
        canEdit.value = true;
    }

    editDialogVisible.value = true;
};

const handleEditConfirm = async () => {
    const validateResult = await editForm.value.validate();
    
    if (validateResult === true) {

        if (dialogFormData.value['板卡类型'].length === 0) {
            MessagePlugin.warning('板卡类型不能为空，请选择后提交。')
            return;
        }
        loadingModify.value = true;
        saveLoading.value = true;
        let updatedData = {
            ...dialogFormData.value,
            id: String(dialogFormData.value.id),
        };

        allFactorOptionList.value.forEach(field => {
            if (field === '单板业务模型') {
                updatedData[field] = dialogFormData.value[field];
            } else {
                updatedData[field] = dialogFormData.value[field].join(',');
            }
        });

        try {
            let updateBoardTreeDataResponse = await updateBoardTreeData(updatedData);
            saveLoading.value = false;
            editDialogVisible.value = false;
            // if(updatedData.createBoard) {
            //     loadingCreate.value = true;
            //     await comfirmICenter(updatedData.board);
            // }
            
            await refreshData();
            MessagePlugin.success(updateBoardTreeDataResponse.message);

            // 提取公共参数
            const params = {
                "board": updatedData["board"],
                "employ_no": updatedData.createNum,
                "requirementPrePlanning": updatedData.requirementPrePlanVersion,
                "specificationByExampleUrl": updatedData.requirementInstantiationLink,
                "split_rdc_flag": updatedData.createRdc ? 'Y' : 'N',
                "data": updateBoardTreeDataResponse.data,
                ...updatedData
            };

            let messageKey;
            if (updatedData.createRdc) {
                messageKey = MessagePlugin.loading('需求管理助手正在努力拆分需求, 大约需要1分钟, 请稍等...', 0);
            } else {
                messageKey = MessagePlugin.loading('波及分析助手正在努力波及分析, 大约需要30秒, 请稍等...', 0);
            }

            try {
                let response = await addNewPartUpdateChangeAnalysisData(params);
                const taskId = response.data[0];
                const resultPoll = await pollForResult(taskId);
                if (messageKey && resultPoll === 'success') {
                // if (messageKey) {
                    MessagePlugin.close(messageKey);
                    MessagePlugin.success(`拆分成功, 请在单板全局状态界面查询${updatedData['board']}`);
                } else {
                    MessagePlugin.close(messageKey);
                    MessagePlugin.success(`分析成功, ${response.message}`);
                }
            } catch (error) {
                if (messageKey) {
                    MessagePlugin.close(messageKey);
                }
                const errorMsg = updatedData.createRdc ? '拆分失败，请重试' : '分析失败，请重试';
                MessagePlugin.error(errorMsg);
                console.error(errorMsg + ':', error);
            }
        } catch (error) {
            console.error('修改失败，请重试', error);
            MessagePlugin.error('修改失败，请重试');
        } finally {
            resetOption();
            resetDialog('clearAll');
            loadingCreate.value = false;
            loadingModify.value = false;
            saveLoading.value = false;
        }
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }
};

const handleEditCancel = () => {
    resetOption();
    resetDialog('clearAll');
    editDialogVisible.value = false;
};

const handleViewCancel = () => {
    resetDialog('clearView');
    queryDialogVisible.value = false;
};

const resetFeature = () => {
    featureFormData.value = {
        board: '',
        associate_MR: false,
        mr_ident: '',
        feature: []
    }
};

const closeFeatureRequire = () => {
    if (featureForm.value) {
        // 清除所有字段的验证状态
        featureForm.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (featureForm.value.reset) {
            featureForm.value.reset();
        }
    }
    turnMR.value = false;
    visibleFeatureRequire.value = false;
    resetFeature();
};

const closeRequire = () => {
    if (requireForm.value) {
        // 清除所有字段的验证状态
        requireForm.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (requireForm.value.reset) {
            requireForm.value.reset();
        }
    }
    visibleRequire.value = false;
};

// 查看相关方法
const openQueryDialog = async (row) => {

    const services = row['线路侧光层业务'];
    const modules = row['线路侧光模块'];
    const lineRelationData = await getMappingRelationship(row.board, '线路侧', modules, services, false, row.status)

    lineRelationNum.value = lineRelationData.length;


    queryFormData.value = {
        ...row,
        lineRelation: lineRelationData
    };

    nowStatus.value = 'view';
    allFactorOptionList.value.forEach(field => {
        queryFormData.value[field] = row[field]
    });

    queryDialogVisible.value = true;
};

// 新增相关方法
const openAddDialog = async () => {
    dialogFormData.value = {
        board: '',
        createRdc: false,
        createBoard: false,
        createMR: false,
        createNum: '',
        requirementPrePlanVersion: '',
        requirementInstantiationLink: '',
        requirementSource: '',
        associate_MR: false,
        mr_ident: '',
        expectedFinishDate: '',
        requirementPurpose: '',
        targetMarket: '',
        marketTarget: '',
        customer: '',
        subrack: '',
        designSpecificationUrl: '',
        // customerRelation: [],
        lineRelation: []
    };
    nowStatus.value = 'add';
    allFactorOptionList.value.forEach(field => {
        dialogFormData.value[field] = [];
    });
    ifDialog.value = true;
    addDialogVisible.value = true;
};

const confirmFeatureRequire = async () => {
    const validateResult = await featureForm.value.validate();

    if (validateResult === true) {
        loadingFeature.value = true;
        visibleFeatureRequire.value = false;
        const requestParams = {
          board: "",
          feature: "",
          subFeature: "",
          mr_ident: "",
          associate_MR: false,
          belongTeam: ""
        };

        const featureList = [...new Set(featureFormData.value.feature.map(item => item[0]))];
        const subFeatureList = [...new Set(featureFormData.value.feature.map(item => item[1]))];
        if (featureList) requestParams.feature = featureList.join(',');
        if (subFeatureList) requestParams.subFeature = subFeatureList.join(',');
        requestParams.board = featureFormData.value.board;
        requestParams.associate_MR = featureFormData.value.associate_MR;
        requestParams.mr_ident = featureFormData.value.mr_ident;
        requestParams.belongTeam = featureFormData.value.requirementType === '交付需求'? featureFormData.value.belongTeam : "";

        try {
            let response = await addNewFeatureUpdateChangeAnalysisData(requestParams);
            if (response.status === 'success') {
                MessagePlugin.success(`${response.message}`);
                const taskId = response.data[0];
                await pollForResult(taskId);
            } else {
                MessagePlugin.error(`${response.message}`);
            }
            loadingFeature.value = false;
        } catch (error) {
            const errorMsg = '拆分失败，请重试';
            MessagePlugin.error(errorMsg);
            console.error(errorMsg + ':', error);
            loadingFeature.value = false;
        }  
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }
};

const confirmRequire = async () => {
    const validateResult = await requireForm.value.validate();
    
    if (validateResult === true) {
        loadingBreakdown.value = true;
        visibleRequire.value = false;
        const params = {
                "board": requireFormData.value.board,
                "employ_no": requireFormData.value.createNum,
                "requirementPrePlanning": requireFormData.value.requirementPrePlanVersion,
                "specificationByExampleUrl": requireFormData.value.requirementInstantiationLink,
                "split_rdc_flag": 'Y',
                "stock_flag": 'Y',
                ...requireFormData.value
              };

        try {
            let response = await addBoardGlobalStatusBoardData(params);
            if (response.status === 'success') {
                MessagePlugin.success(`${response.message}`);
                const taskId = response.data[0];
                await pollForResult(taskId);
            } else {
                MessagePlugin.error(`${response.message}`);
            }
            loadingBreakdown.value = false;
        } catch (error) {
            const errorMsg = '拆分失败，请重试';
            MessagePlugin.error(errorMsg);
            console.error(errorMsg + ':', error);
            loadingBreakdown.value = false;
        }
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }
};

/**
 * 辅助函数：处理字符串，去掉"->"及其前面的内容
 * @param {string} str - 原始字符串
 * @returns {string} 处理后的字符串
 */
const removeArrowAndPrefix = (str) => {
  if (!str) return str;
  const index = str.indexOf("->");
  return index !== -1 ? str.slice(index + 2) : str;
};

const filterSubrackData  = (data) => {
  if (!Array.isArray(data) || data.length === 0) return;
  const processElement = (element) => {
    // 如果是数组，递归处理每个元素
    if (Array.isArray(element)) {
      element.forEach(processElement);
      return;
    }
    
    // 如果是字符串且包含"+"
    if (typeof element === 'string' && element.includes('+')) {
      element.split('+').forEach(part => {
        const trimmedPart = part.trim();
        if (trimmedPart) processElement(trimmedPart);
      });
      return;
    }

    handleSubCase(String(element).trim());
  };
  
  // 开始处理
  data.forEach(processElement);
};

/**
 * 筛选和处理板卡数据
 * @param {Array} data - 板卡类型数组
 */
const filterBoardData = (data) => {
  if (!Array.isArray(data) || data.length === 0) return;
  
  // 递归函数：处理所有可能的嵌套
  const processElement = (element) => {
    // 如果是数组，递归处理每个元素
    if (Array.isArray(element)) {
      element.forEach(processElement);
      return;
    }
    
    // 如果是字符串且包含"+"
    if (typeof element === 'string' && element.includes('+')) {
      element.split('+').forEach(part => {
        const trimmedPart = part.trim();
        if (trimmedPart) processElement(trimmedPart);
      });
      return;
    }
    
    // 处理单个字符串
    switch(String(element).trim()) {
      case "FPGA部件_承载电层业务":
        handleCase('纯电_业务FPGA');
        break;
        
      case "FRM部件_承载电层业务":
        handleCase('纯电_业务FRM');
        break;
        
      case "光模块部件_承载电层业务":
        handleCase('光电_业务FRM');
        break;
        
      default:
        console.log(`未处理的元素类型: ${element}`);
        break;
    }
  };
  
  // 开始处理
  data.forEach(processElement);
};

const handleSubCase = (keyword) => {
  if (!subrackSup.value || !Array.isArray(subrackSup.value)) {
    allFactorValueDict.value['单板支持的子架'] = [];
    return;
  } 

  const filteredsubrack = subrackSup.value
    .filter(item => item && typeof item === 'string' && item.includes(keyword))
    .map(removeArrowAndPrefix);

  allFactorValueDict.value['单板支持的子架'] = allFactorValueDict.value['单板支持的子架'].concat(filteredsubrack);
};

/**
 * 处理FPGA部件的情况
 */
const handleCase = (keyword) => {
  if (!businessFRM.value || !Array.isArray(businessFRM.value)) {
    allFactorValueDict.value['业务FRM芯片'] = [];
    return;
  } else if (!costLogic.value || !Array.isArray(costLogic.value)) {
    allFactorValueDict.value['开销逻辑'] = [];
    return;
  } else if (!controlLogic.value || !Array.isArray(controlLogic.value)) {
    allFactorValueDict.value['控制逻辑'] = [];
    return;
  }
  
  const filteredFPGA = businessFRM.value
    .filter(item => item && typeof item === 'string' && item.includes(keyword))
    .map(removeArrowAndPrefix);
  const filteredFRM = costLogic.value
    .filter(item => item && typeof item === 'string' && item.includes(keyword))
    .map(removeArrowAndPrefix);
  const filtered = controlLogic.value
    .filter(item => item && typeof item === 'string' && item.includes(keyword))
    .map(removeArrowAndPrefix);
  
  allFactorValueDict.value['业务FRM芯片'] = allFactorValueDict.value['业务FRM芯片'].concat(filteredFPGA);
  allFactorValueDict.value['开销逻辑'] = allFactorValueDict.value['开销逻辑'].concat(filteredFRM);
  allFactorValueDict.value['控制逻辑'] = allFactorValueDict.value['控制逻辑'].concat(filtered);
};

const getClearString = (paramsArray) => {
    const processKeys = ["单板支持的子架", "业务FRM芯片", "开销逻辑", "控制逻辑"];

    // 处理方法1：直接修改原对象
    processKeys.forEach(key => {
        if (paramsArray[key]) {
            paramsArray[key] = paramsArray[key].map(item => {
            // 分割字符串，取"->"后面的部分
            const parts = item.split("->");
            // 如果有"->"，返回第二部分，否则返回原字符串
            return parts.length > 1 ? parts[1] : item;
            });
        }
    });
};

const handleAddConfirm = async () => {
    // 先进行表单验证
    const validateResult = await addFormRef.value.validate();
    
    if (validateResult === true) {
        loadingAdd.value = true;
        saveLoading.value = true;
        // 验证通过，继续原有逻辑
        // 构造提交数据，动态处理 allFactorOptionList 字段
        const newRow = {
            ...dialogFormData.value,
        };

        allFactorOptionList.value.forEach(field => {
            if (field === '单板业务模型') {
                newRow[field] = dialogFormData.value[field];
            } else {
                newRow[field] = dialogFormData.value[field].join(',');
            }
        });

        try {
            let addBoardTreeDataResponse = await addBoardTreeData(newRow);
            saveLoading.value = false;
            addDialogVisible.value = false;
            if(dialogFormData.value.createBoard) {
                loadingCreate.value = true;
                await comfirmICenter(dialogFormData.value.board);
            }

            await refreshData();
            MessagePlugin.success(addBoardTreeDataResponse.message);

            // 提取公共参数
            const params = {
                "board": newRow["board"],
                "employ_no": newRow.createNum,
                "requirementPrePlanning": newRow.requirementPrePlanVersion,
                "specificationByExampleUrl": newRow.requirementInstantiationLink,
                "split_rdc_flag": newRow.createRdc ? 'Y' : 'N',
                "stock_flag": 'N',
                "data": addBoardTreeDataResponse.data,
                ...newRow
            };

            let messageKey;
            if (newRow.createRdc) {
              messageKey = MessagePlugin.loading('需求管理助手正在努力拆分需求, 大约需要1分钟, 请稍等...', 0);
            } else {
              messageKey = MessagePlugin.loading('波及分析助手正在努力波及分析, 大约需要30秒, 请稍等...', 0);
            }

            try {
                let response = await addBoardGlobalStatusBoardData(params);
                const taskId = response.data[0];
                const resultPoll = await pollForResult(taskId);
                if (messageKey && newRow.createRdc && resultPoll === 'success') {
                    MessagePlugin.close(messageKey);
                    MessagePlugin.success(`拆分成功, 请在单板全局状态界面查询${newRow['board']}`);
                } else {
                    MessagePlugin.close(messageKey);
                    MessagePlugin.success(`分析成功, ${response.message}`);
                }
            } catch (error) {
                if (messageKey) {
                    MessagePlugin.close(messageKey);
                }
                const errorMsg = newRow.createRdc ? '拆分失败，请重试' : '分析失败，请重试';
                MessagePlugin.error(errorMsg);
                console.error(errorMsg + ':', error);
            }
        } catch (error) {
            console.error('新增失败，请重试', error);
            MessagePlugin.error('新增失败，请重试');
        } finally {
            loadingCreate.value = false;
            canEdit.value = true;
            ifDialog.value = false;
            loadingAdd.value = false;
            saveLoading.value = false;
        }
    } else {
        // 验证失败，TDesign 会自动显示错误信息
        console.log('表单验证失败:', validateResult);
        // MessagePlugin.warning('请检查表单填写是否正确');
    }
};

const pollForResult = async (taskId, maxAttempts = 100, interval = 7000) => {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        
        const poll = async () => {
            attempts++;
            
            try {
                const response = await getRdcSplitTaskResultDict(taskId);
                const status = response.data.task_status
                const result = response.data.task_result
                const message = response.data.task_err_reason
                if (status === 'completed') {
                    if (result === 'success') {
                      resolve(result); // 成功获取结果
                    } else {
                      // MessagePlugin.error(message);
                      MessagePlugin.error({
                        content: message,
                        duration: 0, // duration 为 0 时不会自动关闭
                        closeBtn: true,     // 显示关闭按钮
                      });
                      reject(new Error(`Task failed: ${message}`));
                    }
                } else if (status === 'pending') {
                    // 任务仍在运行，继续轮询
                    if (attempts < maxAttempts) {
                        setTimeout(poll, interval);
                    } else {
                        MessagePlugin.error('查询超时');
                        reject(new Error('Task timeout'));
                    }
                } else {
                    MessagePlugin.error('未找到当前任务');
                    reject(new Error('Task not found'));
                }
            } catch (error) {
                MessagePlugin.error(`${error}`);
                reject(error);
            }
        };
        
        poll(); // 开始第一次轮询
    });
};

const resetDialog = (status) => {
    // 1. 重置表单数据
    if (status === 'clearAll') {
        dialogFormData.value = {
            board: '',
            createRdc: false,
            createBoard: false,
            createMR: false,
            createNum: '',
            requirementPrePlanVersion: '',
            requirementInstantiationLink: '',
            requirementSource: '',
            associate_MR: false,
            mr_ident: '',
            expectedFinishDate: '',
            requirementPurpose: '',
            targetMarket: '',
            marketTarget: '',
            customer: '',
            subrack: '',
            designSpecificationUrl: '',
            // customerRelation: [],
            lineRelation: [],
            requirementType: '',
            belongTeam: '',
        };
        lineRelationNum.value = 0;
        allFactorOptionList.value.forEach(field => {
            if (field === '单板业务模型') {
                dialogFormData.value[field] = '';
            } else {
                dialogFormData.value[field] = [];
            }
        });
    } else if (status === 'clearView') {
        queryFormData.value = {};
        lineRelationNum.value = 0;
        return;
    }
    

    
    // 3. 重置验证状态
    if (addFormRef.value) {
        // 清除所有字段的验证状态
        addFormRef.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (addFormRef.value.reset && status === 'clearAll') {
            addFormRef.value.reset();
        }
    }

    if (editForm.value) {
        // 清除所有字段的验证状态
        editForm.value.clearValidate();
        // 重置表单（如果有reset方法）
        if (editForm.value.reset && status === 'clearAll') {
            editForm.value.reset();
        }
    }
    
    // 4. 重置其他状态
    canEdit.value = true;
    turnUrl.value = false;
    
    // 5. 重置 verifyOption 为初始状态
    verifyOption.value = {
        '单板名称': {
            required_flag: false,
            input_format: null,
            input_remark: null
        }
    };
};

const handleAddCancel = () => {
    resetDialog('clearAll');
    addDialogVisible.value = false;
    ifDialog.value = false
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
        let deleteRowboards = [];

        for (const item of filterDataList.value) {
            if (deleteIdSet.has(item.id)) {
                deleteRowboards.push(item.board);
            }
        }
        await deleteBoardTreeData({"board": deleteRowboards.join(',')});
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
        const response = await importExcelBoardTreeData(formData);
        MessagePlugin.success(`${response.message || ''}`);
        await refreshData();
        importDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = '批量导入失败';
        importDialogVisible.value = false;
        const result = await extractAllParts(error.data);
        showImportFailureReason(result, error.message);
    } finally {
      importLoading.value = false;
    }
    uploadKey.value++
};

const extractAllParts = async (items) => {
  return items.map(text => {
    // 使用正则表达式一次性匹配三个部分
    const match = text.match(/^(.*?)(?:格式\d*：)(.*?)(?:注意：(.*))?$/s);
    
    if (match) {
      const beforeFormat = match[1].trim() || "无";
      const formatContent = match[2].trim() || "无";
      const noteContent = (match[3] || "无").trim();
      
      return {
        beforeFormat,
        formatContent,
        noteContent
      };
    } else {
      // 如果没有匹配到任何格式标记
      return {
        beforeFormat: text.trim(),
        formatContent: "无",
        noteContent: "无"
      };
    }
  });
};

const showImportFailureReason = (importData, status) => {
    const contentElements = importData.map((importItem, itemIndex) => 
        h('div', { 
            key: itemIndex,
            style: { 
                marginBottom: '8px',
                padding: '8px',
                borderLeft: '3px solid #e34d59',
                backgroundColor: '#fff2f0',
                borderRadius: '2px'
            } 
        }, [
            h('div', { style: { fontWeight: 'bold', fontSize: '13px' } }, `失败原因${itemIndex + 1}: ${importItem?.beforeFormat}`),
            // h('div', { style: { fontWeight: 'bold',fontSize: '13px' } }, `${importItem?.beforeFormat}`),
            h('div', { style: { color: '#00000099', fontSize: '12px', marginTop: '4px' } }, `注意: ${importItem?.noteContent}`),
            h('div', { style: { color: '#e34d59', fontSize: '12px', marginTop: '4px' } }, `格式: ${importItem?.formatContent}`)
        ])
    );

    DialogPlugin.confirm({
        header: `单板树数据${status}`,
        body: () => h('div', [
            h('div', { style: { marginBottom: '10px', fontWeight: 'bold' } }, [
                    `共 ${importData.length} 条${status}信息`
                ]
            ),
            // 展开/收起按钮
            h('div', {
                style: { 
                    color: '#0052d9', 
                    cursor: 'pointer', 
                    fontWeight: 'bold',
                    marginBottom: '10px',
                    fontSize: '13px'
                },
                onClick: (e) => {
                    e.stopPropagation();
                    showDetails.value = !showDetails.value;
                }
            }, showDetails.value ? '▼ 收起详细失败信息' : '► 展开详细失败信息'),
            
            // 详情内容
            showDetails.value ? h('div', { 
                style: { 
                    maxHeight: '400px', 
                    overflowY: 'auto',
                    border: '1px solid #dcdcdc',
                    borderRadius: '4px',
                    padding: '10px',
                    backgroundColor: '#fafafa'
                } 
            }, contentElements) : null
        ]),
        duration: 30000,
        confirmBtn: null,
        cancelBtn: null,
        width: '700px',
    });
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
            '单板名称': row.board || '',
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
            { wch: 15 },  // 单板名称
            ...allFactorOptionList.value.map(field => ({ wch: 20 })), // 动态字段
            { wch: 12 },  // 关联版本号
            { wch: 15 },  // 操作人
            { wch: 20 },  // 更新时间
            { wch: 10 }   // 数据状态
        ];
        worksheet['!cols'] = wscols;
        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '单板树批量导出');
        // 生成文件名（使用YYMMDDHHMM格式）
        const date = new Date();
        const formattedDate =
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `单板树批量导出_${formattedDate}.xlsx`;
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        // 显示成功信息
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};

watch(allFactorOptionList, (newFields) => {
  // 清空现有动态字段的规则，避免旧规则残留
  newFields.forEach(field => {
    delete rules.value[field];
  });
  
  // 根据 verifyOption 重新创建规则
  updateRulesBasedOnVerifyOption();
}, { immediate: true });

watch(verifyOption, () => {
  updateRulesBasedOnVerifyOption();
}, { deep: true });

// 计算属性：是否可以显示客户侧映射关系
const canShowCustomerRelation = computed(() => {
  const opticalServices = dialogFormData.value['客户侧光层业务'] || []
  const opticalModules = dialogFormData.value['客户侧光模块'] || []
  return opticalServices.length > 0 && opticalModules.length > 0
})

// 计算属性：是否可以显示线路侧映射关系
const canShowLineRelation = computed(() => {
  const opticalServices = dialogFormData.value['线路侧光层业务'] || []
  const opticalModules = dialogFormData.value['线路侧光模块'] || []
  return opticalServices.length > 0 && opticalModules.length > 0
})

// 监听客户侧光层业务和光模块变化
/*
watch(
  () => [dialogFormData.value['客户侧光层业务'], dialogFormData.value['客户侧光模块']],
  async ([newServices, newModules]) => {
    // 当光层业务或光模块发生变化时，重新生成表格数据
    if (newServices.length > 0 && newModules.length > 0) {
      try {
        const customerRelationData = await generateDefaultSelectData(
          dialogFormData.value['客户侧光层业务'], 
          dialogFormData.value['客户侧光模块'], 
          nowStatus.value
        );
        
        // 确保赋值的是数组
        dialogFormData.value.customerRelation = Array.isArray(customerRelationData) 
          ? customerRelationData 
          : [];

        generateCustomerRelationTable(nowStatus.value);
      } catch (error) {
        console.error('生成客户侧数据失败:', error);
        dialogFormData.value.customerRelation = [];
        customerRelationTableData.value = [];
      }
    } else {
      customerRelationTableData.value = [];
    }
  },
  { deep: true }
)*/


// 监听线路侧光层业务和光模块变化
// watch(
//   () => [dialogFormData.value['线路侧光层业务'], dialogFormData.value['线路侧光模块']],
//   async ([newServices, newModules]) => {

//     // 当光层业务或光模块发生变化时，重新生成表格数据
//     if (newServices.length > 0 && newModules.length > 0) {
//       try {
//         // const lineRelationData = await generateDefaultSelectData(
//         //   dialogFormData.value['线路侧光层业务'], 
//         //   dialogFormData.value['线路侧光模块'], 
//         //   nowStatus.value
//         // );
        
//         // /*=== 确保赋值的是数组 ===*/
//         // dialogFormData.value.lineRelation = Array.isArray(lineRelationData) 
//         //   ? lineRelationData 
//         //   : [];

//         generateLineRelationTable(newServices, newModules, dialogFormData.value.lineRelation, nowStatus.value);
//       } catch (error) {
//         console.error('生成线路侧数据失败:', error);
//         dialogFormData.value.customerRelation = [];
//         lineRelationTableData.value = [];
//       }
//     } else {
//       lineRelationTableData.value = [];
//     }
//   },
//   { deep: true }
// )

// watch(
//   () => [queryFormData.value['线路侧光层业务'], queryFormData.value['线路侧光模块']],
//   async ([newServices, newModules]) => {
//     // 当光层业务或光模块发生变化时，重新生成表格数据
//     if (newServices.length > 0 && newModules.length > 0) {
//       try {
//         // const lineRelationData = await generateDefaultSelectData(
//         //   dialogFormData.value['线路侧光层业务'], 
//         //   dialogFormData.value['线路侧光模块'], 
//         //   nowStatus.value
//         // );
        
//         // /*=== 确保赋值的是数组 ===*/
//         // dialogFormData.value.lineRelation = Array.isArray(lineRelationData) 
//         //   ? lineRelationData 
//         //   : [];

//         const arraynewServices = newServices.split(',');
//         const arrayModules = newModules.split(',');

//         generateLineRelationTable(arraynewServices, arrayModules, queryFormData.value.lineRelation, nowStatus.value);
//       } catch (error) {
//         console.error('生成线路侧数据失败:', error);
//         queryFormData.value.customerRelation = [];
//         lineRelationTableData.value = [];
//       }
//     } else {
//       lineRelationTableData.value = [];
//     }
//   },
//   { deep: true }
// )

/**
 * 生成客户侧映射关系数据
 * @param {Array} businessArray - 业务数组，如 ["SFP_SR-550", "SFP_LR-10K", "SFP_ER-40K"]
 * @param {Array} moduleArray - 模块数组，如 ["新易盛_QSFP28(4*28)_物料代码1_PN1", "新易盛_QSFP28(4*28)_物料代码2_PN2"]
 * @param {string} status - 状态，如 "add" 表示新增时默认全选
 * @returns {Promise<Array>} 返回映射关系数组
 */
const generateDefaultSelectData = async (businessArray, moduleArray, status) => {
  try {
    // 验证输入参数
    if (!Array.isArray(businessArray) || !Array.isArray(moduleArray)) {
      throw new Error('businessArray 和 moduleArray 必须是数组')
    }
    
    if (businessArray.length === 0 || moduleArray.length === 0) {
      return [];
    }
    
    const result = []
    
    // 生成所有可能的组合
    moduleArray.forEach(module => {
      businessArray.forEach(service => {
        result.push({
          module,
          service,
          checked: true // 如果是新增状态，默认勾选
        })
      })
    })
    
    return result;
    
  } catch (error) {
    console.error('生成客户侧数据失败:', error)
    return [];
  }
}

// 生成客户侧关系表格数据
const generateCustomerRelationTable = (status) => {
  const services = dialogFormData.value['客户侧光层业务'] || []
  const modules = dialogFormData.value['客户侧光模块'] || []
  
  // 从已保存的映射关系中获取勾选状态
  const savedRelations = dialogFormData.value.customerRelation || []
  
  // 检查是否所有可能的映射关系都已经保存了
  const totalPossibleRelations = services.length * modules.length
  const hasSavedAllRelations = savedRelations.length === totalPossibleRelations
  
  const tableData = services.map(service => {
    const row = { service }
    
    // 为每个光模块添加复选框列
    modules.forEach(module => {
      if (savedRelations.length === 0) {
        // 如果完全没有保存过任何映射，默认全部勾选
        row[module] = true
      } else if (hasSavedAllRelations) {
        // 如果保存的映射数量等于所有可能的映射数量，说明之前是全选的
        row[module] = true
      } else {
        // 检查是否已存在映射关系
        const isChecked = savedRelations.some(
          relation => relation.service === service && relation.module === module
        )
        row[module] = isChecked
      }
    })
    
    return row
  })
  
  customerRelationTableData.value = tableData
}

// 生成线路侧关系表格数据
const generateLineRelationTable = (newServices, newModules, FormData, status, serviceValue, moduleValue) => {
  const services = newServices || [];
  const modules = newModules || [];

  const isService = serviceValue !== null && serviceValue !== undefined;
  const isModule = moduleValue !== null && moduleValue !== undefined;
  
  // 从已保存的映射关系中获取勾选状态
  const savedRelations = FormData || [];

  // 检查是否所有可能的映射关系都已经保存了
  const totalPossibleRelations = services.length * modules.length
  const hasSavedAllRelations = savedRelations.length === totalPossibleRelations
  let Num = 0
  const tableData = modules.map(module => {
    const row = { module }
    const moduleCheck = isModule? module === moduleValue? true:false:false
    // 为每个光模块添加复选框列
    services.forEach(service => {
    const serviceCheck = isService? service === serviceValue? true:false:false
    //   if (savedRelations.length === 0 && status === 'add') {
    //     // 如果完全没有保存过任何映射，默认全部勾选
    //     row[service] = true
    //     Num++
    //   } else {
    // 检查是否已存在映射关系
    // const isChecked = savedRelations.some(
    //   relation => relation.module === module && relation.service === service? relation.checked:true
    // )
        const existingRelation = savedRelations.find(
          relation => relation.module === module && relation.service === service
        )
        row[service] = existingRelation ? existingRelation.checked : moduleCheck || serviceCheck || false;

        if(row[service]) Num++
      //}
    })
    
    return row
  })
   lineRelationNum.value = Num

   lineRelationTableData.value = tableData

   saveLineRelation(newServices, newModules, status);
}

// 动态生成表格列配置（客户侧）
const customerRelationColumns = computed(() => {
  const modules = dialogFormData.value['客户侧光层业务'] || []
  
  const columns = [
    {
      title: '光模块 / 光层业务',
      colKey: 'module',
      width: 150,
      fixed: 'left'
    }
  ]
  
  modules.forEach(module => {
    columns.push({
        title: module,
        colKey: module,
        width: 100,
        align: 'center',
        cell: (h, { row }) => {
        return h(TCheckbox, {
            checked: row[module],
            onChange: (checked) => {
                // 使用 Vue.set 或直接修改 ref 值
                const index = customerRelationTableData.value.findIndex(r => r.service === row.service)
                if (index !== -1) {
                    // 创建新对象确保响应式更新
                    customerRelationTableData.value[index] = {
                        ...customerRelationTableData.value[index],
                        [module]: checked
                    }
                }
            }
        })
        }
    })
  })
  
  return columns
})

// 动态生成表格列配置（线路侧）
const lineRelationColumns = computed(() => {
  const service = nowStatus.value === 'view'? queryFormData.value['线路侧光层业务'].split(',') || []:dialogFormData.value['线路侧光层业务'] || []

  const columns = [
    {
      title: `光模块 / 光层业务`,
      colKey: 'module',
      width: 120,
      fixed: 'left'
    }
  ]
  
  service.forEach(service => {
    columns.push({
        title: service,
        colKey: service,
        width: 200,
        align: 'center',
        cell: (h, { row }) => {
        return h(TCheckbox, {
            modelValue: row[service],
            onChange: (checked) => {
                // 使用 Vue.set 或直接修改 ref 值
                const index = lineRelationTableData.value.findIndex(r => r.module === row.module)
                if (index !== -1) {
                    // 创建新对象确保响应式更新
                    lineRelationTableData.value[index] = {
                        ...lineRelationTableData.value[index],
                        [service]: checked
                    }
                }
            }
        })
        }
    })
  })
  return columns
})

// 显示客户侧映射关系对话框
const showCustomerRelationDialog = () => {
  if (!canShowCustomerRelation.value) {
    MessagePlugin.warning('请先选择客户侧光层业务和光模块')
    return
  }
  
  // 重新生成表格数据（确保数据最新）
  generateCustomerRelationTable(nowStatus.value)
  customerRelationDialogVisible.value = true
}

// 显示线路侧映射关系对话框
const showLineRelationDialog = (newServices, newModules, lineRelation, nowStatus) => {
  if (!canShowLineRelation.value && nowStatus !== 'view') {
    MessagePlugin.warning('请先选择线路侧光层业务和光模块')
    return
  }

  let arraynewServices = [];
  let arrayModules = [];
  if (nowStatus === 'view') {
    arraynewServices = newServices.split(',');
    arrayModules = newModules.split(',');
  } else {
    arraynewServices = newServices;
    arrayModules = newModules;
  }

  // 重新生成表格数据（确保数据最新）
  generateLineRelationTable(arraynewServices, arrayModules, lineRelation, nowStatus, null, null)
  lineRelationDialogVisible.value = true
}

// 保存客户侧映射关系
const saveCustomerRelation = () => {
  const services = dialogFormData.value['客户侧光层业务'] || []
  const modules = dialogFormData.value['客户侧光模块'] || []
  const relations = []
  
  // 遍历表格数据，收集所有勾选的映射关系
  customerRelationTableData.value.forEach(row => {
    const service = row.service
    modules.forEach(module => {
      if (row[module]) {
        relations.push({
          service,
          module,
          checked: true
        })
      }
    })
  })
  
  // 保存到表单数据
  dialogFormData.value.customerRelation = relations
  customerRelationDialogVisible.value = false
}

// 保存线路侧映射关系
const saveLineRelation = (newServices, newModules, nowStatus) => {
    if (nowStatus !== 'view') {
        const services = newServices || []
        const modules = newModules || []
        //   if(nowStatus === 'view'){
        //     services = queryFormData.value['线路侧光层业务'] || []
        //     modules = queryFormData.value['线路侧光模块'] || []
        //   } else {
        //     services = dialogFormData.value['线路侧光层业务'] || []
        //     modules = dialogFormData.value['线路侧光模块'] || []
        //   }
        const relations = []
        let Num = 0

        // 遍历表格数据，收集所有勾选的映射关系
        lineRelationTableData.value.forEach(row => {
            const module = row.module
            services.forEach(service => {
            if (row[service]) {
                relations.push({
                module,
                service,
                checked: true
                })
                Num++
            } else {
                relations.push({
                module,
                service,
                checked: false
                })
            }
            })
        })
        lineRelationNum.value = Num
        // 保存到表单数据
        dialogFormData.value.lineRelation = relations
    }
  lineRelationDialogVisible.value = false
}

// 关闭客户侧映射关系对话框
const closeCustomerRelationDialog = () => {
  customerRelationDialogVisible.value = false
}

// 关闭线路侧映射关系对话框
const closeLineRelationDialog = () => {
  lineRelationDialogVisible.value = false
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

.require-form {
    padding: 16px 0;
    height: auto;
    overflow-y: auto;
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

.mb-3 {
  margin-bottom: 16px;
}

.relation-hint {
  font-size: 14px;
  color: var(--td-text-color-secondary);
  margin-top: 0px;
}

.relation-dialog {
  max-height: 60vh;
  overflow-y: auto;
}

.relation-table-container {
  overflow-x: auto;
}

.service-cell {
  font-weight: 500;
  color: var(--td-text-color-primary);
}

/* 自定义复选框样式 */
/* :deep(.add-checkbox) {
  margin: 0 auto;
} */

:deep(.t-table__cell) {
  padding: 8px 12px;
}

/* 在全局样式或组件样式中 */
.custom-cascader-menu .t-cascader__menu {
  width: 300px !important;
  min-width: 300px !important;
}

/* 如果有多级菜单，确保所有菜单都设置宽度 */
.custom-cascader-menu .t-cascader__menu + .t-cascader__menu {
  width: 300px !important;
}
</style>

<style>
/* 在全局样式或组件样式中 */
.custom-cascader-menu .t-cascader__menu {
  width: 400px !important;
  min-width: 400px !important;
}
.custom-cascader-menu .t-cascader__menu + .t-cascader__menu {
  width: 400px !important;
}
</style>