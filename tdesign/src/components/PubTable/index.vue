<!-- src/components/PubTable/index.vue -->
<template>
    <div class="simple-table-wrapper">
        <div class="table-container">
            <div class="table-title">{{ title }}</div>
            <t-table
                ref="tableRef"
                :data="pagedData"
                :columns="tableColumns"
                :border="border"
                :stripe="stripe"
                :height="maxHeight || height"
                :empty="emptyText"
                row-key="index"
                style="width: 100%; table-layout: fixed;"
                @sort-change="handleSortChange"
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
import { ref, computed, watch, nextTick } from 'vue'

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
    }
})

const tableRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(props.defaultPageSize)
const sortProp = ref(null)
const sortOrder = ref(null)

// 构建表格列配置（添加序号列）
const tableColumns = computed(() => {
    const cols = [
        {
            colKey: 'serial',
            title: '序号',
            width: 60,
            align: 'center',
            fixed: 'left'
        }
    ]
    
    props.columns.forEach(col => {
        cols.push({
            colKey: col.prop,
            title: col.label,
            width: col.width,
            minWidth: col.minWidth,
            align: col.align || 'center',
            fixed: col.fixed,
            sortable: col.sortable || false,
            ellipsis: col.tooltip !== false
        })
    })
    
    return cols
})

const total = computed(() => props.data.length)

const pagedData = computed(() => {
    let sortedData = [...props.data]

    if (sortProp.value && sortOrder.value) {
        sortedData.sort((a, b) => {
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

    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return sortedData.slice(start, end)
})

watch(pagedData, () => {
    nextTick(() => {
        // 滚动到顶部
        const tableBody = tableRef.value?.$el?.querySelector('.t-table__body')
        if (tableBody) {
            tableBody.scrollTop = 0
        }
    })
}, { immediate: true })

const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
}

const handlePageChange = (pageInfo) => {
    currentPage.value = pageInfo.current
}

const handleSortChange = (sort) => {
    sortProp.value = sort.sortBy
    sortOrder.value = sort.descending ? 'descending' : sort.descending === false ? 'ascending' : null
    currentPage.value = 1
}

// 暴露方法给父组件
defineExpose({
    tableRef,
    refresh: () => {
        currentPage.value = 1
    }
})
</script>

<style scoped>
.simple-table-wrapper {
    margin: 0px auto;
    width: 99%;
    overflow-x: auto;
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

.table-title {
    font-size: 16px;
    font-weight: bold;
    color: #838282;
    margin-top: 0px;
    margin-bottom: 10px;
    text-align: left;
}

:deep(.t-table__header th) {
    background-color: #f8f9fa;
    color: #3c4858;
    font-weight: 600;
}
</style>