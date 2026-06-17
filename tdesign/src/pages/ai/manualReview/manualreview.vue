<template>
  <div class="approval-list-container">
    <!-- Tab 页签 -->
    <t-tabs v-model="activeTab" @change="handleTabChange">
      <t-tab-panel value="pending" label="待我审批">
        <!-- 待我审批的筛选区域 -->
        <div class="filter-bar">
          <t-button theme="default" variant="outline">
            <template #icon><t-icon name="filter" /></template>
            筛选
          </t-button>
          
          <!-- 批量审核按钮 -->
          <t-button 
            theme="primary" 
            :disabled="selectedRowKeys.length === 0"
            @click="handleBatchApprove"
            style="margin-left: 12px"
          >
            <template #icon><t-icon name="check-circle" /></template>
            批量审核 ({{ selectedRowKeys.length }})
          </t-button>
          
          <t-button 
            theme="danger" 
            variant="outline"
            :disabled="selectedRowKeys.length === 0"
            @click="handleBatchReject"
            style="margin-left: 12px"
          >
            <template #icon><t-icon name="close-circle" /></template>
            批量拒绝
          </t-button>
        </div>
      </t-tab-panel>
      
      <t-tab-panel value="submitted" label="提交记录">
        <!-- 提交记录的筛选区域 -->
        <div class="filter-bar">
          <t-select 
            v-model="submittedStatus" 
            placeholder="请选择审核状态"
            clearable
            style="width: 200px"
            @change="handleSubmittedStatusChange"
          >
            <t-option :value="1" label="待审核" />
            <t-option :value="2" label="审核中" />
            <t-option :value="3" label="已通过" />
            <t-option :value="4" label="已驳回" />
            <t-option :value="5" label="已撤回" />
          </t-select>
        </div>
      </t-tab-panel>
    </t-tabs>

    <!-- 表格区域 -->
    <t-table
      :data="tableData"
      :columns="currentColumns"
      :loading="loading"
      row-key="id"
      stripe
      hover
      :selected-row-keys="activeTab === 'pending' ? selectedRowKeys : []"
      @select-change="handleSelectChange"
      class="approval-table"
    >
      <!-- 审核结果自定义列（展示审核状态标签） -->
      <template #approval_status="{ row }">
        <t-tag :theme="getStatusTheme(row.approval_status)" variant="light">
          {{ getStatusText(row.approval_status) }}
        </t-tag>
      </template>

      <!-- 操作按钮自定义列 -->
      <template #operation="{ row }">
        <t-link theme="primary" hover="color" @click="handleView(row.id)">查看</t-link>
      </template>
    </t-table>

    <!-- 分页组件 -->
    <div class="pagination-wrapper">
      <t-pagination
        v-model="currentPage"
        :page-size="pageSize"
        :total="total"
        :page-size-options="[10, 20, 50]"
        show-jumper
        @change="onPageChange"
        @page-size-change="onPageSizeChange"
      />
    </div>

    <!-- 查看详情抽屉（包含审批操作） -->
    <t-drawer
      v-model:visible="drawerVisible"
      header="变更详情"
      size="large"
      :close-btn="true"
      :footer="false"
    >
      <div class="drawer-content" v-if="detailLoading">
        <div class="loading-wrapper">
          <t-loading text="加载详情中..." />
        </div>
      </div>
      <div class="drawer-content" v-else-if="currentRow">
        <detail-panel :data="currentRow" />
        
        <!-- 待我审批的审批操作区域 - 仅当记录处于待审核(1)或审核中(2)状态时显示 -->
        <div 
          v-if="activeTab === 'pending' && currentRow && (currentRow.approval_status === 1 || currentRow.approval_status === 2)" 
          class="approval-actions"
        >
          <div class="divider"></div>
          <div class="actions-title">审批操作</div>
          <div class="actions-buttons">
            <t-button 
              theme="success" 
              @click="handleDrawerApprove"
              :loading="drawerApproveLoading"
            >
              <template #icon><t-icon name="check-circle" /></template>
              通过
            </t-button>
            <t-button 
              theme="danger" 
              @click="handleDrawerReject"
              :loading="drawerRejectLoading"
            >
              <template #icon><t-icon name="close-circle" /></template>
              拒绝
            </t-button>
            <t-button 
              theme="warning" 
              variant="outline"
              @click="handleDrawerRevoke"
              :loading="drawerRevokeLoading"
            >
              <template #icon><t-icon name="rollback" /></template>
              撤回
            </t-button>
          </div>
        </div>
        
        <!-- 提交记录的撤回操作区域 - 仅当记录处于待审核(1)或审核中(2)状态时显示 -->
        <div 
          v-if="activeTab === 'submitted' && currentRow && (currentRow.approval_status === 1 || currentRow.approval_status === 2)" 
          class="approval-actions"
        >
          <div class="divider"></div>
          <div class="actions-title">操作</div>
          <div class="actions-buttons">
            <t-button 
              theme="warning" 
              variant="outline"
              @click="handleDrawerRevoke"
              :loading="drawerRevokeLoading"
            >
              <template #icon><t-icon name="rollback" /></template>
              撤回
            </t-button>
          </div>
        </div>
        
        <!-- 已完成审批的提示 -->
        <div 
          v-else-if="currentRow && (currentRow.approval_status === 3 || currentRow.approval_status === 4 || currentRow.approval_status === 5)" 
          class="approval-status-info"
        >
          <div class="divider"></div>
          <t-alert 
            :theme="getCompletedAlertTheme(currentRow.approval_status)"
            :message="getCompletedMessage(currentRow.approval_status)"
          />
        </div>
      </div>
    </t-drawer>

    <!-- 单条审核对话框（审批意见表单） -->
    <t-dialog
      v-model:visible="singleApproveDialog.visible"
      :header="singleApproveDialog.title"
      :confirm-btn="{
        content: '确认',
        theme: 'primary',
        loading: singleApproveDialog.loading
      }"
      @confirm="confirmSingleApprove"
      @cancel="cancelSingleApprove"
    >
      <t-form :data="singleApproveDialog.formData" ref="singleApproveFormRef">
        <t-form-item label="审核意见" name="comment">
          <t-textarea 
            v-model="singleApproveDialog.formData.comment" 
            placeholder="请输入审核意见（选填）"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item 
          v-if="singleApproveDialog.action === 'reject'" 
          label="拒绝原因" 
          name="reject_reason"
          :rules="[{ required: true, message: '请填写拒绝原因' }]"
        >
          <t-textarea 
            v-model="singleApproveDialog.formData.reject_reason" 
            placeholder="请填写拒绝原因"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 撤回确认对话框 -->
    <t-dialog
      v-model:visible="revokeDialog.visible"
      header="撤回确认"
      :confirm-btn="{
        content: '确认撤回',
        theme: 'warning',
        loading: revokeDialog.loading
      }"
      @confirm="confirmRevoke"
      @cancel="cancelRevoke"
    >
      <div class="revoke-info">
        <p>确定要撤回该审批申请吗？</p>
        <p class="warning-text">撤回后，该申请将变为已撤回状态，无法再次审批。</p>
      </div>
    </t-dialog>

    <!-- 批量审核对话框 -->
    <t-dialog
      v-model:visible="batchApproveDialog.visible"
      :header="batchApproveDialog.title"
      :confirm-btn="{
        content: '确认',
        theme: 'primary',
        loading: batchApproveDialog.loading
      }"
      @confirm="confirmBatchApprove"
      @cancel="cancelBatchApprove"
    >
      <div class="batch-info">
        <p>已选择 <strong>{{ selectedRowKeys.length }}</strong> 条审批记录</p>
        <t-form :data="batchApproveDialog.formData">
          <t-form-item label="审核意见" name="comment">
            <t-textarea 
              v-model="batchApproveDialog.formData.comment" 
              placeholder="请输入审核意见（选填）"
              :autosize="{ minRows: 3, maxRows: 6 }"
            />
          </t-form-item>
          <t-form-item 
            v-if="batchApproveDialog.action === 'reject'" 
            label="拒绝原因" 
            name="reject_reason"
            :rules="[{ required: true, message: '请填写拒绝原因' }]"
          >
            <t-textarea 
              v-model="batchApproveDialog.formData.reject_reason" 
              placeholder="请填写拒绝原因"
              :autosize="{ minRows: 3, maxRows: 6 }"
            />
          </t-form-item>
        </t-form>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import DetailPanel from './DetailPanel.vue'
import { getMyPending, batchApprove, singleApprove, revokeApprove, getMySubmitted, getDetail } from '@/api/electric.js'

// 当前激活的Tab
const activeTab = ref('pending')

// 提交记录的状态筛选
const submittedStatus = ref(null)

// 待我审批的表格列配置
const pendingColumns = [
  { colKey: 'row-select', type: 'multiple', width: 50, fixed: 'left' },
  { colKey: 'serial-number', title: '序号', width: 70, align: 'center' },
  { colKey: 'submitter_person', title: '变更人', width: 150, ellipsis: true },
  { colKey: 'create_time', title: '创建时间', width: 180 },
  { 
    colKey: 'change_type', 
    title: '变更类型', 
    width: 100,
    cell: (h, { row }) => {
      const typeMap = { add: '新增', update: '修改', delete: '删除' }
      return typeMap[row.change_type] || row.change_type
    }
  },
  { colKey: 'biz_type', title: '变更知识', width: 150, ellipsis: true },
  { colKey: 'change_reason', title: '变更理由', width: 150, ellipsis: true },
  { colKey: 'assigned_persons', title: '审核人', width: 180, ellipsis: true },
  { colKey: 'approval_status', title: '审核状态', width: 120, cell: 'approval_status' },
  { colKey: 'reject_reason', title: '拒绝原因', width: 200, ellipsis: true },
  { colKey: 'update_time', title: '更新时间', width: 180 },
  { colKey: 'operation', title: '操作', width: 100, fixed: 'right', cell: 'operation' }
]

// 提交记录的表格列配置（没有多选框）
const submittedColumns = [
  { colKey: 'serial-number', title: '序号', width: 70, align: 'center' },
  { colKey: 'submitter_person', title: '变更人', width: 150, ellipsis: true },
  { colKey: 'create_time', title: '创建时间', width: 180 },
  { 
    colKey: 'change_type', 
    title: '变更类型', 
    width: 100,
    cell: (h, { row }) => {
      const typeMap = { add: '新增', update: '修改', delete: '删除' }
      return typeMap[row.change_type] || row.change_type
    }
  },
  { colKey: 'biz_type', title: '变更知识', width: 150, ellipsis: true },
  { colKey: 'change_reason', title: '变更理由', width: 150, ellipsis: true },
  { colKey: 'assigned_persons', title: '审核人', width: 180, ellipsis: true },
  { colKey: 'approval_status', title: '审核状态', width: 120, cell: 'approval_status' },
  { colKey: 'reject_reason', title: '驳回原因', width: 200, ellipsis: true },
  { colKey: 'update_time', title: '更新时间', width: 180 },
  { colKey: 'operation', title: '操作', width: 100, fixed: 'right', cell: 'operation' }
]

// 根据当前Tab动态切换列配置
const currentColumns = computed(() => {
  return activeTab.value === 'pending' ? pendingColumns : submittedColumns
})

// 响应式数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 多选相关（仅待我审批使用）
const selectedRowKeys = ref([])

// 抽屉相关
const drawerVisible = ref(false)
const currentRow = ref(null)
const detailLoading = ref(false)

// 抽屉中按钮的loading状态
const drawerApproveLoading = ref(false)
const drawerRejectLoading = ref(false)
const drawerRevokeLoading = ref(false)

// 单条审核对话框
const singleApproveDialog = ref({
  visible: false,
  title: '',
  action: 'approve',
  loading: false,
  formData: {
    record_id: null,
    comment: '',
    reject_reason: ''
  }
})

// 撤回对话框
const revokeDialog = ref({
  visible: false,
  loading: false,
  record_id: null
})

// 批量审核对话框
const batchApproveDialog = ref({
  visible: false,
  title: '',
  action: 'approve',
  loading: false,
  formData: {
    comment: '',
    reject_reason: ''
  }
})

// 获取审核状态对应的主题色
const getStatusTheme = (status) => {
  switch (status) {
    case 1: return 'warning'
    case 2: return 'primary'
    case 3: return 'success'
    case 4: return 'danger'
    case 5: return 'default'
    default: return 'default'
  }
}

// 获取审核状态文本
const getStatusText = (status) => {
  switch (status) {
    case 1: return '待审核'
    case 2: return '审核中'
    case 3: return '已通过'
    case 4: return '已驳回'
    case 5: return '已撤回'
    default: return '未知'
  }
}

// 获取已完成审批的提示主题
const getCompletedAlertTheme = (status) => {
  switch (status) {
    case 3: return 'success'
    case 4: return 'error'
    case 5: return 'warning'
    default: return 'info'
  }
}

// 获取已完成审批的提示消息
const getCompletedMessage = (status) => {
  switch (status) {
    case 3: return '该申请已通过审批'
    case 4: return '该申请已被驳回'
    case 5: return '该申请已被撤回'
    default: return '该申请已完成审批'
  }
}

// 表格多选变化
const handleSelectChange = (value, { selectedRowData }) => {
  selectedRowKeys.value = value
}

// 获取待审批列表数据
const fetchMyPending = async () => {
  loading.value = true
  try {
    const params = {
      size: pageSize.value,
      page: currentPage.value,
    }
    const response = await getMyPending(params);
    
    if (response.code === 200) {
      tableData.value = response.data.list
      total.value = response.data.total
      selectedRowKeys.value = []
    } else {
      MessagePlugin.error(response.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取待审批列表失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取提交记录列表数据
const fetchMySubmitted = async () => {
  loading.value = true
  try {
    const params = {
      size: pageSize.value,
      page: currentPage.value,
    }
    // 如果有状态筛选，添加status参数
    if (submittedStatus.value) {
      params.status = submittedStatus.value
    }
    const response = await getMySubmitted(params);
    
    if (response.code === 200) {
      tableData.value = response.data.list
      total.value = response.data.total
    } else {
      MessagePlugin.error(response.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取提交记录失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取详情数据
const fetchDetail = async (recordId) => {
  detailLoading.value = true
  try {
    const params = {
      record_id: recordId
    }
    const response = await getDetail(params)
    
    if (response.code === 200) {
      currentRow.value = response.data.record
    } else {
      MessagePlugin.error(response.message || '获取详情失败')
      drawerVisible.value = false
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
    drawerVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

// Tab切换处理
const handleTabChange = (value) => {
  activeTab.value = value
  currentPage.value = 1
  selectedRowKeys.value = []
  submittedStatus.value = null
  
  if (value === 'pending') {
    fetchMyPending()
  } else {
    fetchMySubmitted()
  }
}

// 提交记录状态筛选变化
const handleSubmittedStatusChange = () => {
  currentPage.value = 1
  fetchMySubmitted()
}

// 查看详情
const handleView = (recordId) => {
  drawerVisible.value = true
  fetchDetail(recordId)
}

// 抽屉中的通过操作
const handleDrawerApprove = () => {
  singleApproveDialog.value = {
    visible: true,
    title: '审批通过',
    action: 'approve',
    loading: false,
    formData: {
      record_id: currentRow.value.id,
      comment: '',
      reject_reason: ''
    }
  }
}

// 抽屉中的拒绝操作
const handleDrawerReject = () => {
  singleApproveDialog.value = {
    visible: true,
    title: '审批驳回',
    action: 'reject',
    loading: false,
    formData: {
      record_id: currentRow.value.id,
      comment: '',
      reject_reason: ''
    }
  }
}

// 抽屉中的撤回操作
const handleDrawerRevoke = () => {
  revokeDialog.value = {
    visible: true,
    loading: false,
    record_id: currentRow.value.id
  }
}

// 确认撤回
const confirmRevoke = async () => {
  revokeDialog.value.loading = true
  drawerRevokeLoading.value = true
  
  try {
    const params = {
      record_id: revokeDialog.value.record_id
    }
    
    const response = await revokeApprove(params)
    
    if (response.code === 200) {
      MessagePlugin.success(response.message || '撤回成功')
      revokeDialog.value.visible = false
      drawerVisible.value = false
      // 刷新当前列表
      if (activeTab.value === 'pending') {
        await fetchMyPending()
      } else {
        await fetchMySubmitted()
      }
    } else {
      MessagePlugin.error(response.message || '撤回失败')
    }
  } catch (error) {
    console.error('撤回失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  } finally {
    revokeDialog.value.loading = false
    drawerRevokeLoading.value = false
  }
}

// 取消撤回
const cancelRevoke = () => {
  revokeDialog.value.visible = false
}

// 确认单条审批
const confirmSingleApprove = async () => {
  if (singleApproveDialog.value.action === 'reject' && !singleApproveDialog.value.formData.reject_reason) {
    MessagePlugin.warning('请填写驳回原因')
    return
  }

  singleApproveDialog.value.loading = true
  
  if (singleApproveDialog.value.action === 'approve') {
    drawerApproveLoading.value = true
  } else {
    drawerRejectLoading.value = true
  }
  
  try {
    const params = {
      record_id: singleApproveDialog.value.formData.record_id,
      action: singleApproveDialog.value.action,
      comment: singleApproveDialog.value.formData.comment || 
               (singleApproveDialog.value.action === 'approve' ? '审批通过' : '审批驳回'),
      reject_reason: singleApproveDialog.value.action === 'reject' 
                     ? singleApproveDialog.value.formData.reject_reason 
                     : ''
    }
    
    const response = await singleApprove(params)
    
    if (response.code === 200) {
      MessagePlugin.success(response.message || '操作成功')
      singleApproveDialog.value.visible = false
      drawerVisible.value = false
      await fetchMyPending()
    } else {
      MessagePlugin.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('审批失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  } finally {
    singleApproveDialog.value.loading = false
    drawerApproveLoading.value = false
    drawerRejectLoading.value = false
  }
}

// 取消单条审批
const cancelSingleApprove = () => {
  singleApproveDialog.value.visible = false
}

// 批量审批通过
const handleBatchApprove = () => {
  if (selectedRowKeys.value.length === 0) {
    MessagePlugin.warning('请选择要审核的记录')
    return
  }
  
  batchApproveDialog.value = {
    visible: true,
    title: `批量审批通过 (${selectedRowKeys.value.length}条)`,
    action: 'approve',
    loading: false,
    formData: {
      comment: '',
      reject_reason: ''
    }
  }
}

// 批量驳回
const handleBatchReject = () => {
  if (selectedRowKeys.value.length === 0) {
    MessagePlugin.warning('请选择要审核的记录')
    return
  }
  
  batchApproveDialog.value = {
    visible: true,
    title: `批量驳回 (${selectedRowKeys.value.length}条)`,
    action: 'reject',
    loading: false,
    formData: {
      comment: '',
      reject_reason: ''
    }
  }
}

// 确认批量审批
const confirmBatchApprove = async () => {
  if (batchApproveDialog.value.action === 'reject' && !batchApproveDialog.value.formData.reject_reason) {
    MessagePlugin.warning('请填写驳回原因')
    return
  }

  batchApproveDialog.value.loading = true
  try {
    const sortedRecordIds = [...selectedRowKeys.value].sort((a, b) => a - b)
    
    const params = {
      record_ids: sortedRecordIds,
      action: batchApproveDialog.value.action,
      comment: batchApproveDialog.value.formData.comment || 
               (batchApproveDialog.value.action === 'approve' ? '批量审批通过' : '批量驳回'),
      reject_reason: batchApproveDialog.value.action === 'reject' 
                     ? batchApproveDialog.value.formData.reject_reason 
                     : ''
    }
    
    const response = await batchApprove(params)
    
    if (response.code === 200) {
      MessagePlugin.success(response.message || '批量操作成功')
      batchApproveDialog.value.visible = false
      await fetchMyPending()
    } else {
      MessagePlugin.error(response.message || '批量操作失败')
    }
  } catch (error) {
    console.error('批量审批失败:', error)
    MessagePlugin.error('网络请求失败，请稍后重试')
  } finally {
    batchApproveDialog.value.loading = false
  }
}

// 取消批量审批
const cancelBatchApprove = () => {
  batchApproveDialog.value.visible = false
}

// 分页页码变化
const onPageChange = (page, pageInfo) => {
  if (typeof page === 'number') {
    currentPage.value = page
  } else if (page?.current) {
    currentPage.value = page.current
  } else if (pageInfo?.current) {
    currentPage.value = pageInfo.current
  }
  
  if (activeTab.value === 'pending') {
    fetchMyPending()
  } else {
    fetchMySubmitted()
  }
}

// 分页每页条数变化
const onPageSizeChange = (size, pageInfo) => {
  let newSize = size
  if (typeof size === 'object') {
    newSize = size.pageSize || size.size || 20
  } else if (pageInfo?.pageSize) {
    newSize = pageInfo.pageSize
  }
  
  pageSize.value = newSize
  currentPage.value = 1
  
  if (activeTab.value === 'pending') {
    fetchMyPending()
  } else {
    fetchMySubmitted()
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchMyPending()
})
</script>

<style scoped lang="less">
.approval-list-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.filter-bar { 
  margin-top: 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-start;
  gap: 12px;
}

.approval-table {
  background-color: #fff;
  border-radius: 6px;
  overflow: hidden;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  background-color: #fff;
  padding: 16px;
  border-radius: 6px;
}

.batch-info {
  margin-bottom: 16px;
  
  p {
    margin-bottom: 16px;
    color: #666;
    
    strong {
      color: #0052d9;
      font-size: 16px;
    }
  }
}

.revoke-info {
  p {
    margin-bottom: 12px;
    font-size: 14px;
    
    &.warning-text {
      color: #e34d59;
      font-size: 12px;
    }
  }
}

.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  .loading-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    min-height: 300px;
  }
  
  .approval-actions {
    margin-top: auto;
    padding: 16px 0;
    
    .divider {
      height: 1px;
      background-color: #e7e7e7;
      margin: 16px 0;
    }
    
    .actions-title {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 16px;
      color: #1f2d3d;
    }
    
    .actions-buttons {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
    }
  }
  
  .approval-status-info {
    margin-top: auto;
    padding: 16px 0;
    
    .divider {
      height: 1px;
      background-color: #e7e7e7;
      margin: 16px 0;
    }
  }
}

:deep(.t-table__header th) {
  background-color: #f5f7fa;
  color: #1f2d3d;
  font-weight: 500;
}

:deep(.t-link) {
  cursor: pointer;
}

:deep(.t-drawer__body) {
  display: flex;
  flex-direction: column;
}
</style>