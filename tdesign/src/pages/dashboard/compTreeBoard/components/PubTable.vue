<!-- src/pages/dashboard/compTreeBoard/PubTable.vue -->
<template>
    <div class="simple-table-wrapper">
        <div class="table-container">
            <div class="table-header">
                <div class="table-title">{{ title }}</div>
                <div class="table-actions" v-if="props.enableExport">
                    <t-button 
                        theme="primary" 
                        variant="outline"
                        @click="handleExport"
                        :loading="isExporting"
                        :disabled="filteredData.length === 0"
                    >
                        <template #icon><t-icon name="download" /></template>
                        导出数据
                    </t-button>
                </div>
            </div>
            <t-table
                ref="tableRef"
                :data="pagedData"
                :columns="tableColumns"
                :border="border"
                :stripe="stripe"
                :height="maxHeight || height"
                :empty="emptyText"
                row-key="index"
                resizable
                :filter-value="filterValues"
                :virtual-scroll="true"
                :scroll="scrollConfig"
                style="width: 100%;"
                @sort-change="handleSortChange"
                @resize="handleColumnResize"
                @filter-change="handleFilterChange"
                @mounted="onTableMounted"
            >
                <!-- 序号列 -->
                <template #serial="{ rowIndex }">
                    {{ (currentPage - 1) * pageSize + rowIndex + 1 }}
                </template>

                <!-- 动态列插槽 -->
                <template v-for="col in columns" :key="col.prop" #[`${col.prop}`]="{ row, rowIndex }">
                    <slot :name="`cell-${col.prop}`" :row="row" :$index="rowIndex">
                        <span>{{ row[col.prop] || '-' }}</span>
                    </slot>
                </template>
            </t-table>
        </div>

        <!-- 分页器 -->
        <div class="pagination-wrapper" v-if="showPagination && total > 0">
            <t-pagination
                v-model:current="currentPage"
                v-model:pageSize="pageSize"
                :total="total"
                :page-size-options="[10, 20, 50, 100]"
                show-jumper
                show-page-number
                show-page-size
                show-total
                @change="handlePageChange"
                @page-size-change="handleSizeChange"
            />
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, shallowRef } from 'vue'
import * as XLSX from 'xlsx-js-style'
import { MessagePlugin } from 'tdesign-vue-next'

// 筛选相关状态
const filterValues = ref({})
// 存储全局点击监听器移除函数
let removeGlobalClickListener = null
// 存储筛选器选项（缓存，避免每次重新计算）
const filterOptions = ref({})
// 记录表格渲染开始时间
let tableRenderStartTime = null
// 虚拟滚动配置
const scrollConfig = {
    type: 'virtual',
    threshold: 100, // 超过 100 条数据启用虚拟滚动
    rowHeight: 40, // 每行高度（像素）
    bufferSize: 10 // 缓冲区行数
}

const props = defineProps({
    title: {
        type: String,
        default: ""
    },
    columns: {
        type: Array,
        required: true,
        default: () => []
    },
    data: {
        type: Array,
        required: true,
        default: () => []
    },
    border: {
        type: Boolean,
        default: true
    },
    stripe: {
        type: Boolean,
        default: true
    },
    height: {
        type: [Number, String],
        default: null
    },
    maxHeight: {
        type: [Number, String],
        default: null
    },
    tableClass: {
        type: String,
        default: ""
    },
    emptyText: {
        type: String,
        default: "暂无数据"
    },
    showPagination: {
        type: Boolean,
        default: true
    },
    defaultPageSize: {
        type: Number,
        default: 10
    },
    // 是否启用筛选功能
    enableFilter: {
        type: Boolean,
        default: false
    },
    // 是否启用导出功能
    enableExport: {
        type: Boolean,
        default: false
    },
    // 新增：是否启用列宽持久化（刷新页面后保持）
    persistColumnWidth: {
        type: Boolean,
        default: true
    },
    // 新增：用于区分不同表格的存储键前缀
    storageKey: {
        type: String,
        default: "pub-table"
    },
    // 导出时包含链接的列配置 [{ prop: 'page_title', urlProp: 'page_url' }]
    linkColumns: {
        type: Array,
        default: () => []
    }
})

const tableRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(props.defaultPageSize)
const sortProp = ref(null)
const sortOrder = ref(null)
// 新增：存储调整后的列宽
const columnWidths = ref({})
// 新增：存储原始数据用于筛选
const originalData = ref([])
// 新增：导出按钮显示状态
const isExporting = ref(false)

// 构建表格列配置（添加序号列和调整后的宽度）
let lastColumnsBuildTime = 0
const tableColumns = computed(() => {
    const buildStartTime = performance.now()
    const cols = [
        {
            colKey: 'serial',
            title: '序号',
            width: columnWidths.value.serial || 60,
            align: 'center',
            fixed: 'left'
        }
    ]
    
    props.columns.forEach(col => {
        const colConfig = {
            colKey: col.prop,
            title: col.label,
            width: columnWidths.value[col.prop] || col.width,
            minWidth: col.minWidth,
            align: col.align || 'center',
            fixed: col.fixed,
            sortable: col.sortable || false,
            ellipsis: col.tooltip !== false,
            resizable: true
        }
        
        // 如果启用了筛选且列配置允许筛选，添加筛选配置
        if (props.enableFilter && col.filterable !== false) {
            const filterType = col.filterable === 'multiple' ? 'multiple' : 'input'
            const options = filterOptions.value[col.prop] || []
            
            colConfig.filter = {
                type: filterType,
                list: filterType === 'multiple' ? options : [],
                placeholder: filterType === 'multiple' ? `请选择${col.label}` : `搜索${col.label}`,
                confirmText: '确定',
                resetText: '重置',
                // 限制下拉面板最大高度，避免选项过多时无法关闭
                maxHeight: 300,
                // 点击外部关闭下拉框
                popupProps: {
                    overlayInnerStyle: { maxHeight: '300px', overflowY: 'auto' },
                    // 点击遮罩层关闭下拉框
                    closeOnOverlayClick: true,
                    // 按 ESC 键关闭
                    closeOnEscKeydown: true,
                    // 点击外部关闭
                    destroyOnClose: true,
                    // 设置下拉框位置为底部，确保点击检测正确工作
                    placement: 'bottom-left',
                    // 扩大点击检测区域
                    attach: 'body'
                },
                // 自定义确认和重置按钮，点击后关闭下拉框
                onConfirm: ({ value }) => {
                    filterValues.value = { ...filterValues.value, [col.prop]: value }
                    // 点击确认后关闭下拉框
                    setTimeout(() => {
                        const activeElement = document.activeElement
                        if (activeElement && activeElement.blur) {
                            activeElement.blur()
                        }
                    }, 0)
                },
                onReset: () => {
                    filterValues.value = { ...filterValues.value, [col.prop]: undefined }
                }
            }
        }
        
        cols.push(colConfig)
            })
            
            const buildEndTime = performance.now()
            const buildTime = buildEndTime - buildStartTime
            if (buildTime > 10) {
                console.warn(`[PubTable] ⚠️ 表格列配置构建耗时 ${buildTime.toFixed(2)}ms (超过 10ms)`)
            }
            lastColumnsBuildTime = buildEndTime
            return cols
        })

// 监听数据变化，更新筛选器选项
const dataChangeTime = ref(0)
let isProcessingDataChange = false

// 生成筛选器选项的函数
const generateFilterOptions = async (newData) => {
    const newOptions = {}
    const columnsWithFilter = props.columns.filter(col => props.enableFilter && col.filterable !== false)
    
    if (columnsWithFilter.length === 0 || newData.length === 0) {
        filterOptions.value = newOptions
        return
    }
    
    // 并行处理各列的筛选器选项提取
    const extractPromises = columnsWithFilter.map(async (col) => {
        const extractStartTime = performance.now()
        // 从数据中提取该列的唯一值作为筛选选项
        // 从数据中提取该列的唯一值作为筛选选项，保留空值（显示为"-"）
        const columnValues = newData.map(row => {
            const val = row[col.prop]
            // 空值统一标记为特殊标识符 "__EMPTY__"
            return (val == null || val === '') ? '__EMPTY__' : val
        })
        const uniqueValues = [...new Set(columnValues)]
        const filterType = col.filterable === 'multiple' ? 'multiple' : 'input'
        
        // 为筛选选项设置显示标签，空值显示为"-"
        let options = filterType === 'multiple' 
            ? uniqueValues.map(val => ({ 
                label: val === '__EMPTY__' ? '-' : val, 
                value: val 
            })) 
            : []
        
        // 对选项进行排序：空值（"-"）排在前面，其他按字母/数字顺序排序
        if (options.length > 0) {
            options.sort((a, b) => {
                // 空值排在最前面
                if (a.value === '__EMPTY__') return -1
                if (b.value === '__EMPTY__') return 1
                
                // 其他值按字典序排序
                const labelA = String(a.label)
                const labelB = String(b.label)
                return labelA.localeCompare(labelB, 'zh-CN')
            })
        }
        
        newOptions[col.prop] = options
        
        const extractEndTime = performance.now()
        console.log(`[PubTable] 列 "${col.label}" 提取唯一值耗时：${(extractEndTime - extractStartTime).toFixed(2)}ms, 唯一值数量：${uniqueValues.length}`)
    })
    
    await Promise.all(extractPromises)
    filterOptions.value = newOptions
}

// 监听数据变化
watch(() => props.data, async (newData) => {
    // 避免重复处理
    if (isProcessingDataChange) return
    isProcessingDataChange = true
    
    const perfStartTime = performance.now()
    dataChangeTime.value = perfStartTime
    
    console.log(`[PubTable] ========== 检测到数据变化，开始处理 ==========`)
    console.log(`[PubTable] 数据量：${newData.length}条`)
    console.log(`[PubTable] 数据变化时间戳：${new Date().toLocaleTimeString()}.${Math.floor(perfStartTime % 1000)}`)
    
    try {
        // 每次都重新生成筛选器选项（确保切换领域/状态时正确更新）
        if (newData.length > 0) {
            await generateFilterOptions(newData)
            const filterUpdateTime = performance.now() - perfStartTime
            console.log(`[PubTable] 筛选器选项更新完成，耗时：${filterUpdateTime.toFixed(2)}ms`)
        } else {
            filterOptions.value = {}
            console.log('[PubTable] 数据为空，清空筛选器选项')
        }
        
        // 记录表格渲染开始时间
        tableRenderStartTime = performance.now()
        const delayFromDataChange = tableRenderStartTime - dataChangeTime.value
        console.log(`[PubTable] 开始渲染表格... (距离数据变化延迟：${delayFromDataChange.toFixed(2)}ms)`)
        
        // 等待表格完全渲染后记录总耗时
        nextTick(() => {
            nextTick(() => {
                const renderCompleteTime = performance.now()
                const totalRenderTime = renderCompleteTime - tableRenderStartTime
                const totalTimeFromDataChange = renderCompleteTime - dataChangeTime.value
                console.log(`[PubTable] ========== 表格渲染完成 ==========`)
                console.log(`[PubTable] 表格渲染耗时：${totalRenderTime.toFixed(2)}ms`)
                console.log(`[PubTable] 从数据变化到渲染完成总耗时：${totalTimeFromDataChange.toFixed(2)}ms`)
                console.log(`[PubTable] 其中延迟时间：${delayFromDataChange.toFixed(2)}ms`)
            })
        })
    } finally {
        isProcessingDataChange = false
    }
}, { immediate: true, deep: false })

const total = computed(() => {
    const startTime = performance.now()
    const len = filteredData.value.length
    const elapsed = performance.now() - startTime
    if (elapsed > 50) {
        console.warn(`[PubTable] ⚠️ filteredData 计算耗时 ${elapsed.toFixed(2)}ms`)
    }
    return len
})

// 处理筛选后的数据 - 添加性能监控
let lastFilterBuildTime = 0
const filteredData = computed(() => {
    const filterStartTime = performance.now()
    let result = [...props.data]
    
    // 如果有筛选条件，先进行筛选
    if (Object.keys(filterValues.value).length > 0) {
        result = result.filter(row => {
            return Object.entries(filterValues.value).every(([key, value]) => {
                // 处理多选情况（value 是数组）
                if (Array.isArray(value)) {
                    if (value.length === 0) return true
                    const rowValue = row[key]
                    // 将行中的空值转换为__EMPTY__标识符进行匹配
                    const normalizedRowValue = (rowValue == null || rowValue === '') ? '__EMPTY__' : rowValue
                    return value.includes(normalizedRowValue)
                }
                // 处理单选/输入框情况
                if (!value || value === '') return true
                const rowValue = row[key]
                if (rowValue == null) return false
                return String(rowValue).toLowerCase().includes(String(value).toLowerCase())
            })
        })
    }
    
    // 再进行排序
    if (sortProp.value && sortOrder.value) {
        result.sort((a, b) => {
            let valA = a[sortProp.value]
            let valB = b[sortProp.value]

            if (valA == null) valA = ''
            if (valB == null) valB = ''

            const isNum = !isNaN(Number(valA)) && !isNaN(Number(valB))
            if (isNum) {
                valA = Number(valA)
                valB = Number(valB)
            }

            let result = 0
            if (valA < valB) result = -1
            if (valA > valB) result = 1

            return sortOrder.value === 'ascending' ? result : -result
        })
    }
    
    return result
        const filterEndTime = performance.now()
        const filterElapsed = filterEndTime - filterStartTime
        lastFilterBuildTime = filterEndTime
        if (filterElapsed > 50) {
            console.warn(`[PubTable] ⚠️ filteredData 计算耗时 ${filterElapsed.toFixed(2)}ms (数据量：${result.length}条)`)
        }
        return result
    })

const pagedData = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredData.value.slice(start, end)
})

// 移除 pagedData 的 watch，避免每次分页都触发日志

const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
}

const handlePageChange = (pageInfo) => {
    currentPage.value = pageInfo.current
}

// 处理筛选变化
const handleFilterChange = (filterValue) => {
    filterValues.value = filterValue
    currentPage.value = 1 // 重置到第一页
}

const handleSortChange = (sort) => {
    sortProp.value = sort.sortBy
    sortOrder.value = sort.descending ? 'descending' : sort.descending === false ? 'ascending' : null
    currentPage.value = 1
}

// 新增：处理列宽调整事件
// TDesign resize 事件参数：(trigger, data)
// trigger = { colKey }, data = { width }
const handleColumnResize = (trigger, data) => {
    const { colKey } = trigger
    const { width } = data
    
    // 保存调整后的宽度
    columnWidths.value[colKey] = width
    
    // 如果启用了持久化，保存到本地存储
    if (props.persistColumnWidth) {
        const storageKey = `${props.storageKey}-column-widths`
        localStorage.setItem(storageKey, JSON.stringify(columnWidths.value))
    }
}

// 新增：组件挂载时从本地存储加载列宽
onMounted(() => {
    if (props.persistColumnWidth) {
        const storageKey = `${props.storageKey}-column-widths`
        const savedWidths = localStorage.getItem(storageKey)
        if (savedWidths) {
            try {
                columnWidths.value = JSON.parse(savedWidths)
            } catch (e) {
                console.error('Failed to parse saved column widths:', e)
            }
        }
    }
})

// 监听 filteredData 变化，记录分页数据计算时间（替代 pagedData 监听）
watch(filteredData, (newData) => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    const displayCount = Math.min(end, newData.length) - start
    console.log(`[PubTable] pagedData 更新：显示 ${Math.max(0, displayCount)}/${newData.length} 条数据`)
}, { immediate: true })

// 表格组件挂载时的回调
const onTableMounted = () => {
    console.log('[PubTable] TDesign 表格组件已挂载')
    console.log(`[PubTable] 最后表格列配置构建耗时：${lastColumnsBuildTime.toFixed(2)}ms`)
    console.log(`[PubTable] 最后 filteredData 计算耗时：${lastFilterBuildTime.toFixed(2)}ms`)
    if (tableRenderStartTime) {
        const endTime = performance.now()
        console.log(`[PubTable] TDesign 表格组件渲染耗时：${(endTime - tableRenderStartTime).toFixed(2)}ms`)
        
        // 额外记录从数据变化到现在的总时间
        console.log(`[PubTable] 从数据变化到组件挂载总耗时：${(endTime - tableRenderStartTime).toFixed(2)}ms`)
        tableRenderStartTime = null
    }
    
    // 添加全局点击监听器，处理筛选下拉框的关闭问题
    // 当点击页面任何地方（包括下拉框外部）时，关闭所有筛选下拉框
    if (!removeGlobalClickListener) {
        const handleGlobalMousedown = (e) => {
            // 检查点击是否在下拉框内部
            const popupElement = e.target.closest('.t-popup, .t-dialog, .t-dropdown, .t-select__panel')
            if (!popupElement) {
                // 点击不在下拉框内，清除筛选焦点以关闭下拉框
                if (document.activeElement && document.activeElement.blur) {
                    document.activeElement.blur()
                }
            }
        }
        
        // 使用 mousedown 事件，比 click 更早触发
        document.addEventListener('mousedown', handleGlobalMousedown, true)
        removeGlobalClickListener = () => {
            document.removeEventListener('mousedown', handleGlobalMousedown, true)
        }
    }
}

// 导出功能实现
const handleExport = async () => {
    // 直接使用 filteredData.value 获取筛选后的数据
    const dataToExport = filteredData.value
    
    if (dataToExport.length === 0) {
        MessagePlugin.warning('当前没有数据可导出')
        return
    }

    console.log('[PubTable] 开始导出，筛选后数据量:', dataToExport.length)

    try {
        isExporting.value = true

        // 获取所有列（排除序号列）
        const exportColumns = props.columns.filter(col => col.prop)
        
        // 先生成纯数据用于创建基础工作表
        const plainExportData = dataToExport.map((row, index) => {
            const exportRow = {}
            exportRow['序号'] = index + 1
            
            exportColumns.forEach(col => {
                const value = row[col.prop]
                const displayValue = (value == null || value === '') ? '-' : value
                exportRow[col.label] = displayValue
            })
            
            return exportRow
        })

        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(plainExportData)
        
        // 动态调整列宽 - 优化版：确保列标题完整显示
        const columnWidths = []
        const headerKeys = Object.keys(plainExportData[0] || {})
        
        headerKeys.forEach((key, index) => {
            const headerWidth = key.length
            let maxValue = 0
            
            plainExportData.forEach((row) => {
                const cellValue = row[key]
                const strValue = cellValue ? String(cellValue) : ''
                maxValue = Math.max(maxValue, strValue.length)
            })
            
            // 计算列宽：优先保证列标题能完整显示
            // 列标题宽度至少为标题长度 + 2（留有余量）
            // 数据宽度为最大数据长度 + 1
            // 最终宽度取两者较大值，但不少于 8（避免太窄），不超过 80（避免太宽）
            const minHeaderWidth = headerWidth + 2
            const minDataWidth = maxValue > 0 ? maxValue + 1 : 0
            const optimalWidth = Math.max(minHeaderWidth, minDataWidth, 8)
            
            columnWidths.push({ 
                wch: Math.min(optimalWidth, 80),
                customWidth: true
            })
        })
        worksheet['!cols'] = columnWidths
        
        // 设置表头样式（加粗、居中）
        const headerRange = XLSX.utils.decode_range(worksheet['!ref'])
        for (let col = headerRange.s.c; col <= headerRange.e.c; col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col })
            if (!worksheet[cellAddress]) continue
            worksheet[cellAddress].s = {
                font: { bold: true, sz: 11 },
                alignment: { horizontal: 'center', vertical: 'center' }
            }
        }

        // 为链接列添加超链接和样式
        
        for (let colIndex = 0; colIndex < exportColumns.length; colIndex++) {
            const col = exportColumns[colIndex]
            const linkConfig = props.linkColumns.find(link => link.prop === col.prop)
            
            if (linkConfig && linkConfig.urlProp) {
                const colLetter = String.fromCharCode(65 + colIndex + 1)
                const urlValue = linkConfig.urlProp
                
                // 遍历每一行数据
                for (let rowIndex = 0; rowIndex < dataToExport.length; rowIndex++) {
                    const rowNum = rowIndex + 2 // Excel 行号从 1 开始，第 1 行是表头
                    const cellAddress = `${colLetter}${rowNum}`
                    
                    const rowData = dataToExport[rowIndex]
                    const titleValue = rowData[col.prop] || '-'
                    const url = rowData[urlValue]
                    
                    if (url && url !== '-' && url !== '') {
                        // 创建超链接单元格 - 参考 requirementDetailTable.vue 的实现
                        worksheet[cellAddress] = {
                            t: 's',
                            v: String(titleValue),
                            l: { Target: url },
                            s: {
                                font: {
                                    color: { rgb: 'FF0052d9' },
                                    underline: true,
                                    sz: 11
                                }
                            }
                        }
                    }
                }
            }
        }

        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, props.title || '数据导出')

        // 生成文件名
        const date = new Date()
        const formattedDate =
            `${date.getFullYear().toString().slice(2)}` +
            `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
            `${date.getDate().toString().padStart(2, '0')}` +
            `${date.getHours().toString().padStart(2, '0')}` +
            `${date.getMinutes().toString().padStart(2, '0')}`
        const fileName = `${props.title || '数据'}导出_${formattedDate}.xlsx`

        // 导出文件
        XLSX.writeFile(workbook, fileName)

        // 显示成功信息
        MessagePlugin.success(`数据导出成功，共 ${dataToExport.length} 条记录`)
    } catch (error) {
        console.error('数据导出失败:', error)
        MessagePlugin.error('数据导出失败，请重试')
    } finally {
        isExporting.value = false
    }
}

// 暴露方法给父组件
defineExpose({
    tableRef,
    refresh: () => {
        currentPage.value = 1
    },
    // 新增：重置列宽为默认值
    resetColumnWidths: () => {
        columnWidths.value = {}
        if (props.persistColumnWidth) {
            const storageKey = `${props.storageKey}-column-widths`
            localStorage.removeItem(storageKey)
        }
    },
    // 新增：重置筛选条件
    resetFilters: () => {
        filterValues.value = {}
        currentPage.value = 1
    },
    // 新增：获取当前筛选条件
    getFilters: () => {
        return { ...filterValues.value }
    },
    // 新增：导出功能
    handleExport
})

// 组件卸载时清理全局监听器
import { onUnmounted } from 'vue'
onUnmounted(() => {
    if (removeGlobalClickListener) {
        removeGlobalClickListener()
        removeGlobalClickListener = null
    }
})
</script>

<style scoped>
.simple-table-wrapper {
    margin: 0px auto;
    width: 99%;
    overflow-x: auto;
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.table-title {
    font-size: 16px;
    font-weight: bold;
    color: #838282;
}

.table-actions {
    display: flex;
    gap: 8px;
}

.table-container {
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    max-width: 100%;
    overflow-x: auto;
}

.pagination-wrapper {
    margin-top: 16px;
    text-align: left;
    display: flex;
    justify-content: center;
}


:deep(.t-table__header th) {
    background-color: #f8f9fa;
    color: #3c4858;
    font-weight: 600;
}

/* 优化列宽调整手柄的样式 */
:deep(.t-table__resize-line) {
    background-color: #0052d9;
}

:deep(.t-table__resize-trigger:hover) {
    background-color: rgba(0, 82, 217, 0.1);
}
</style>
