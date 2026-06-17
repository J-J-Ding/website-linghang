<template>
  <div class="detail-panel">
    <!-- 基础信息 -->
    <t-descriptions :column="2" bordered label-width="100px" title="基本信息">
      <t-descriptions-item label="变更ID">{{ data?.id }}</t-descriptions-item>
      <t-descriptions-item label="变更类型">
        <t-tag :theme="getChangeTypeTheme(data?.change_type)" variant="light">
          {{ getChangeTypeText(data?.change_type) }}
        </t-tag>
      </t-descriptions-item>
      <t-descriptions-item label="变更人">{{ data?.submitter_person }}</t-descriptions-item>
      <t-descriptions-item label="变更时间">{{ formatTime(data?.create_time) }}</t-descriptions-item>
      <t-descriptions-item label="变更知识">{{ data?.biz_type }}</t-descriptions-item>
      <t-descriptions-item label="变更理由">{{ data?.change_reason || '--' }}</t-descriptions-item>
      <t-descriptions-item label="审核人">{{ data?.assigned_persons }}</t-descriptions-item>
      <t-descriptions-item label="审核状态">
        <t-tag :theme="getStatusTheme(data?.approval_status)" variant="light">
          {{ getStatusText(data?.approval_status) }}
        </t-tag>
      </t-descriptions-item>
      <t-descriptions-item label="审核结果">{{ data?.approval_result || '--' }}</t-descriptions-item>
      <t-descriptions-item label="拒绝原因">{{ data?.reject_reason || '--' }}</t-descriptions-item>
      <t-descriptions-item label="当前审批人">{{ data?.current_approver || '--' }}</t-descriptions-item>
      <t-descriptions-item label="审核结束时间">{{ formatTime(data?.update_time) }}</t-descriptions-item>
    </t-descriptions>

    <!-- 变更内容详情 -->
    <div class="diff-section" v-if="hasDiffData">
      <h4>变更内容详情</h4>
      
      <!-- 新增类型 - 标绿展示 -->
      <div v-if="data?.change_type === 'add'" class="change-content add-content">
        <div class="section-title">
          <t-icon name="add" />
          新增内容
        </div>
        <div class="content-wrapper">
          <div 
            v-for="(value, key) in formatDataForDisplay(data?.new_data)" 
            :key="key" 
            class="diff-item diff-add"
          >
            <div class="diff-label">{{ getFieldLabel(key) }}：</div>
            <div class="diff-value">
              <template v-if="isLinkField(key, value)">
                <t-link :href="value" target="_blank" hover="color">
                  {{ value }}
                  <template #suffix><t-icon name="link" /></template>
                </t-link>
              </template>
              <template v-else>
                {{ formatValue(value) }}
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 删除类型 - 标红展示 -->
      <div v-else-if="data?.change_type === 'delete'" class="change-content delete-content">
        <div class="section-title">
          <t-icon name="delete" />
          删除内容
        </div>
        <div class="content-wrapper">
          <div 
            v-for="(value, key) in formatDataForDisplay(data?.old_data)" 
            :key="key" 
            class="diff-item diff-delete"
          >
            <div class="diff-label">{{ getFieldLabel(key) }}：</div>
            <div class="diff-value">
              <template v-if="isLinkField(key, value)">
                <t-link :href="value" target="_blank" hover="color">
                  {{ value }}
                  <template #suffix><t-icon name="link" /></template>
                </t-link>
              </template>
              <template v-else>
                {{ formatValue(value) }}
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 修改类型 - 对比展示差异项 -->
      <div v-else-if="data?.change_type === 'update'" class="change-content update-content">
        <div class="section-title">
          <t-icon name="edit" />
          修改内容对比
        </div>
        <div class="compare-wrapper">
          <div class="compare-header">
            <div class="compare-col">字段名</div>
            <div class="compare-col">原值</div>
            <div class="compare-col">新值</div>
          </div>
          <div 
            v-for="item in diffFieldsList" 
            :key="item.field" 
            class="compare-row"
          >
            <div class="compare-col diff-label">{{ item.field }}</div>
            <div class="compare-col diff-old-value">
              <template v-if="isLinkFieldByLabel(item.field, item.oldValue)">
                <t-link :href="item.oldValue" target="_blank" hover="color">
                  {{ item.oldValue || '--' }}
                  <template #suffix><t-icon name="link" /></template>
                </t-link>
              </template>
              <template v-else>
                {{ item.oldValue || '--' }}
              </template>
            </div>
            <div class="compare-col diff-new-value">
              <template v-if="isLinkFieldByLabel(item.field, item.newValue)">
                <t-link :href="item.newValue" target="_blank" hover="color">
                  {{ item.newValue || '--' }}
                  <template #suffix><t-icon name="link" /></template>
                </t-link>
              </template>
              <template v-else>
                {{ item.newValue || '--' }}
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 完整JSON数据（折叠面板） -->
    <t-collapse class="json-collapse" :default-expand-all="false">
      <t-collapse-panel header="查看完整JSON数据" value="json">
        <pre class="json-content">{{ formatJson(filterBakFields(data)) }}</pre>
      </t-collapse-panel>
    </t-collapse>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: null
  }
})

// 需要显示为链接的字段列表
const LINK_FIELDS = ['featureContentLink', 'feature_content_link', 'link', 'url', 'document_url', 'wiki_link']

// 判断字段是否为链接类型
const isLinkField = (fieldKey, value) => {
  if (!value || typeof value !== 'string') return false
  // 检查字段名是否在链接字段列表中
  const isLinkFieldName = LINK_FIELDS.some(linkField => 
    fieldKey === linkField || fieldKey.toLowerCase().includes(linkField.toLowerCase())
  )
  // 检查值是否为有效的URL格式
  const isValidUrl = value.startsWith('http://') || value.startsWith('https://') || value.startsWith('/')
  return isLinkFieldName && isValidUrl
}

// 根据字段标签判断是否为链接字段（用于对比列表）
const isLinkFieldByLabel = (fieldLabel, value) => {
  if (!value || typeof value !== 'string') return false
  // 检查字段标签是否包含链接相关关键词
  const linkKeywords = ['链接', '地址', 'URL', 'link', 'url', '特性内容链接']
  const isLinkLabel = linkKeywords.some(keyword => 
    fieldLabel?.includes(keyword)
  )
  const isValidUrl = value.startsWith('http://') || value.startsWith('https://') || value.startsWith('/')
  return isLinkLabel && isValidUrl
}

// 过滤掉 _bak 后缀的字段
const filterBakFields = (obj) => {
  if (!obj) return obj
  if (typeof obj !== 'object') return obj
  
  const filtered = {}
  for (const key in obj) {
    // 跳过所有带 _bak 后缀的字段
    if (!key.endsWith('_bak')) {
      if (obj[key] && typeof obj[key] === 'object') {
        filtered[key] = filterBakFields(obj[key])
      } else {
        filtered[key] = obj[key]
      }
    }
  }
  return filtered
}

// 字段名映射（根据 zh_en_name_relation）
const getFieldLabel = (fieldKey) => {
  // 跳过 _bak 字段
  if (fieldKey.endsWith('_bak')) return null
  
  if (props.data?.zh_en_name_relation && props.data.zh_en_name_relation[fieldKey]) {
    return props.data.zh_en_name_relation[fieldKey]
  }
  
  // 常见字段的中文映射
  const commonMap = {
    feature: '特性',
    belongTeam: '团队',
    subFeature: '子特性',
    description: '描述',
    requirementSort: '需求优先级',
    featureFirstType: '特性一级分类',
    featureSecondType: '特性二级分类',
    acceptanceCriteria: '验收准则',
    featureContentLink: '特性内容链接',
    estimatedDevWorkload: '预计开发工作量(人天)',
    id: 'ID',
    status: '状态',
    create_time: '创建时间',
    update_time: '更新时间',
    effective_flag: '生效标志',
    operator_person: '操作人',
    childrenList: '子特性列表'
  }
  
  return commonMap[fieldKey] || fieldKey
}

// 格式化数据用于展示（排除空值、元数据和_bak字段）
const formatDataForDisplay = (data) => {
  if (!data) return {}
  
  // 排除不需要展示的字段
  const excludeKeys = ['id', 'create_time', 'update_time', 'effective_flag', 'operator_person',  'parent', 'childrenList']
  
  return Object.keys(data)
    .filter(key => {
      // 排除 excludeKeys 中的字段
      if (excludeKeys.includes(key)) return false
      // 排除所有 _bak 后缀的字段
      if (key.endsWith('_bak')) return false
      // 排除空值
      if (data[key] === null || data[key] === undefined || data[key] === '') return false
      return true
    })
    .reduce((obj, key) => {
      obj[key] = data[key]
      return obj
    }, {})
}

// 格式化值
const formatValue = (value) => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.join(', ')
    }
    // 递归过滤对象中的 _bak 字段
    const filtered = filterBakFields(value)
    if (Object.keys(filtered).length === 0) return '--'
    return JSON.stringify(filtered, null, 2)
  }
  if (typeof value === 'boolean') return value ? '是' : '否'
  return String(value)
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '--'
  return time.replace('T', ' ')
}

// 格式化JSON
const formatJson = (obj) => {
  if (!obj) return '--'
  try {
    const filtered = filterBakFields(obj)
    return JSON.stringify(filtered, null, 2)
  } catch (e) {
    return String(obj)
  }
}

// 判断是否有变更数据
const hasDiffData = computed(() => {
  if (!props.data) return false
  return props.data.diff_data || 
         (props.data.change_type === 'add' && props.data.new_data && Object.keys(formatDataForDisplay(props.data.new_data)).length > 0) ||
         (props.data.change_type === 'delete' && props.data.old_data && Object.keys(formatDataForDisplay(props.data.old_data)).length > 0)
})

// 变更字段对比列表（用于update类型）
const diffFieldsList = computed(() => {
  if (!props.data?.diff_data?.diff) {
    // 如果没有diff_data，尝试从old_data和new_data对比生成
    if (props.data?.old_data && props.data?.new_data) {
      return generateDiffFromData(
        filterBakFields(props.data.old_data), 
        filterBakFields(props.data.new_data)
      )
    }
    return []
  }
  
  const diff = props.data.diff_data.diff
  return Object.keys(diff)
    .filter(field => !field.endsWith('_bak')) // 过滤 _bak 字段
    .map(field => ({
      field: getFieldLabel(field),
      oldValue: formatValue(diff[field].old),
      newValue: formatValue(diff[field].new)
    }))
})

// 从old_data和new_data生成对比列表
const generateDiffFromData = (oldData, newData) => {
  const allKeys = new Set([...Object.keys(oldData || {}), ...Object.keys(newData || {})])
  const diffs = []
  
  allKeys.forEach(key => {
    // 跳过 _bak 字段
    if (key.endsWith('_bak')) return
    
    const oldValue = oldData?.[key]
    const newValue = newData?.[key]
    
    // 排除不需要对比的字段
    const excludeKeys = ['id', 'create_time', 'update_time', 'effective_flag', 'operator_person', 'parent', 'childrenList']
    if (excludeKeys.includes(key)) return
    
    // 只有当值不同时才显示
    if (JSON.stringify(oldValue) !== JSON.stringify(newValue)) {
      diffs.push({
        field: getFieldLabel(key),
        oldValue: formatValue(oldValue),
        newValue: formatValue(newValue)
      })
    }
  })
  
  return diffs
}

// 变更类型相关
const getChangeTypeText = (type) => {
  const map = { add: '新增', update: '修改', delete: '删除' }
  return map[type] || type
}

const getChangeTypeTheme = (type) => {
  const map = { add: 'success', update: 'warning', delete: 'danger' }
  return map[type] || 'default'
}

// 审核状态相关
// 在 DetailPanel.vue 的 script 中，替换审核状态相关函数

// 审核状态相关
const getStatusTheme = (status) => {
  switch (status) {
    case 1: return 'warning'     // 待审核
    case 2: return 'primary'     // 审核中
    case 3: return 'success'     // 审核结束-通过
    case 4: return 'danger'      // 审核结束-驳回
    case 5: return 'default'     // 撤回
    default: return 'default'
  }
}

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
</script>

<style scoped lang="less">
.detail-panel {
  padding: 16px;
  
  .diff-section {
    margin-top: 24px;
    
    h4 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 500;
      padding-left: 8px;
      border-left: 3px solid #0052d9;
    }
    
    .change-content {
      background-color: #f5f7fa;
      border-radius: 6px;
      padding: 16px;
      
      .section-title {
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        
        .t-icon {
          font-size: 16px;
        }
      }
      
      .content-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .diff-item {
        display: flex;
        padding: 8px 12px;
        background-color: #fff;
        border-radius: 4px;
        border-left: 3px solid;
        
        .diff-label {
          width: 180px;
          flex-shrink: 0;
          font-weight: 500;
          color: #1f2d3d;
        }
        
        .diff-value {
          flex: 1;
          color: #606266;
          word-break: break-all;
          white-space: pre-wrap;
          
          :deep(.t-link) {
            word-break: break-all;
            display: inline-flex;
            align-items: center;
            gap: 4px;
          }
        }
      }
      
      &.add-content {
        .diff-item {
          border-left-color: #00a870;
          background-color: #f0f9f4;
          
          .diff-label {
            color: #00a870;
          }
        }
      }
      
      &.delete-content {
        .diff-item {
          border-left-color: #e34d59;
          background-color: #fef0f0;
          
          .diff-label {
            color: #e34d59;
          }
        }
      }
      
      .compare-wrapper {
        background-color: #fff;
        border-radius: 4px;
        overflow: hidden;
        
        .compare-header {
          display: flex;
          background-color: #f5f7fa;
          font-weight: 500;
          border-bottom: 1px solid #e7e7e7;
        }
        
        .compare-row {
          display: flex;
          border-bottom: 1px solid #f0f0f0;
          
          &:last-child {
            border-bottom: none;
          }
        }
        
        .compare-col {
          flex: 1;
          padding: 12px;
          word-break: break-all;
          
          &:first-child {
            width: 200px;
            flex-shrink: 0;
            background-color: #fafafa;
            font-weight: 500;
          }
        }
        
        .diff-old-value {
          color: #e34d59;
          background-color: #fef0f0;
          
          :deep(.t-link) {
            color: #e34d59;
          }
        }
        
        .diff-new-value {
          color: #00a870;
          background-color: #f0f9f4;
          
          :deep(.t-link) {
            color: #00a870;
          }
        }
      }
    }
  }
  
  .json-collapse {
    margin-top: 24px;
    
    .json-content {
      background-color: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
      font-size: 12px;
      line-height: 1.5;
      margin: 0;
      max-height: 300px;
      overflow-y: auto;
    }
  }
}
</style>