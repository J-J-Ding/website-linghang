<template>
    <div class="scene-main">
        <t-space direction="vertical" style="width: 100%">
            <!-- 筛选区域 -->
            <t-space :size="16" style="flex-wrap: wrap">
                <t-select
                    v-model="queryParams.department"
                    placeholder="请选择部门"
                    clearable
                    style="width: 200px;"
                    label="部门: "
                    :options="departmentOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.domain"
                    placeholder="请选择领域"
                    clearable
                    style="width: 200px;"
                    label="领域: "
                    :options="domainOptions"
                    filterable
                />
                <t-select
                    v-model="queryParams.team"
                    placeholder="请选择团队"
                    clearable
                    multiple
                    style="width: 200px;"
                    label="团队: "
                    :options="teamOptions"
                    filterable
                />
                <!-- <t-input
                    v-model="queryParams.year"
                    placeholder="年份（如2026）"
                    clearable
                    style="width: 200px;"
                    label="年: "
                /> -->
                <t-date-picker 
                    v-model="queryParams.year"
                    placeholder="年份（如2026）"
                    style="width: 200px;"
                    mode="year" 
                    allow-input
                    label="年: "/>
                <t-input
                    v-model="queryParams.employee_id"
                    placeholder="请输入工号"
                    clearable
                    style="width: 200px;"
                    label="工号: "
                />
                <t-input
                    v-model="queryParams.name"
                    placeholder="请输入姓名"
                    clearable
                    style="width: 200px;"
                    label="姓名: "
                />
            </t-space>
            
            <!-- 按钮区域 -->
            <t-space style="justify-content: flex-start;margin-bottom: 16px;">
                <t-button @click="handleQuery">查询</t-button>
            </t-space>
        </t-space>
        
        <t-table
            ref="tableRef"
            row-key="rowKey"
            :columns="tableColumnList"
            :data="tableDataList"
            :hover="true"
            bordered
            resizable
            :loading="loading"
            :scroll="{ type: 'virtual' }"
            :max-height="tableHeight">
        </t-table>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import {
    queryHumanResourcePivotByParams,
    getHumanResourcePivotOptions
} from '@/api/humanResourcePivot.js';

const user = useUserStore();

// 表格配置
const tableRef = ref();
const loading = ref(false);
const tableColumnList = ref([]);

// 数据
const tableDataList = ref([]);
const yearMonths = ref([]); // 年月列表，用于动态生成列

// 查询参数
const queryParams = ref({
    department: '',
    domain: '',
    team: [], // 数组，支持多选
    year: '2026',
    employee_id: '',
    name: ''
});

// 选项数据
const departmentOptions = ref([]);
const domainOptions = ref([]);
const teamOptions = ref([]);

// 表格高度
const tableHeight = ref('900px');

// 计算表格高度
const calculateTableHeight = () => {
    tableHeight.value = pubCalculateTableHeight(200);
};

// 格式化数字显示
const formatNumber = (num) => {
    if (num === null || num === undefined) return '';
    const number = Number(num);
    if (isNaN(number)) return '';
    return number.toFixed(2);
};

// 动态生成表格列
const generateTableColumns = () => {
    const fixedColumns = [
        { colKey: 'department', title: '部门', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, fixed: 'left' },
        { colKey: 'domain', title: '领域', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, fixed: 'left' },
        { colKey: 'team', title: '团队', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, fixed: 'left' },
        { colKey: 'team_type', title: '团队类型', width: '150', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, fixed: 'left' },
        { colKey: 'skill_category', title: '技能/特性分类', width: '200', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' }, fixed: 'left' }
    ];

    // 动态生成年月列
    const yearMonthColumns = yearMonths.value.map(ym => ({
        colKey: ym,
        title: ym,
        width: '100',
        align: 'right',
        cell: (_, { row }) => formatNumber(row[ym])
    }));

    tableColumnList.value = [...fixedColumns, ...yearMonthColumns];
};

// 生命周期
onMounted(async () => {
    try {
        calculateTableHeight();
        window.addEventListener('resize', calculateTableHeight);
        // 先加载选项，如果失败也不阻塞页面
        loadOptions().catch(error => {
            console.error('加载选项失败:', error);
            MessagePlugin.warning('加载筛选选项失败，请刷新页面重试');
        });
        await handleQuery();
    } catch (error) {
        console.error('页面初始化失败:', error);
        MessagePlugin.error('页面初始化失败');
    }
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', calculateTableHeight);
});

// 加载选项数据
const loadOptions = async () => {
    try {
        // 加载部门选项
        const deptResponse = await getHumanResourcePivotOptions({ option_type: 'department' });
        if (deptResponse && deptResponse.code === 200) {
            departmentOptions.value = (deptResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        } else {
            console.warn('加载部门选项失败:', deptResponse?.message || '未知错误');
        }

        // 加载领域选项
        const domainResponse = await getHumanResourcePivotOptions({ option_type: 'domain' });
        if (domainResponse && domainResponse.code === 200) {
            domainOptions.value = (domainResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        } else {
            console.warn('加载领域选项失败:', domainResponse?.message || '未知错误');
        }

        // 加载团队选项
        const teamResponse = await getHumanResourcePivotOptions({ option_type: 'team' });
        if (teamResponse && teamResponse.code === 200) {
            teamOptions.value = (teamResponse.data || []).map(item => ({
                label: item,
                value: item
            }));
        } else {
            console.warn('加载团队选项失败:', teamResponse?.message || '未知错误');
        }
    } catch (error) {
        console.error('加载选项数据失败:', error);
    }
};

// 加载数据
const loadData = async () => {
    try {
        loading.value = true;
        const params = {};
        Object.keys(queryParams.value).forEach(key => {
            const value = queryParams.value[key];
            // 处理数组类型（团队多选）
            if (Array.isArray(value)) {
                if (value.length > 0) {
                    params[key] = value;
                }
            } else if (value !== '' && value !== null) {
                params[key] = value;
            }
        });
        
        const response = await queryHumanResourcePivotByParams(params);
        if (response && response.code === 200) {
            tableDataList.value = (response.data || []).map((item, index) => ({
                ...item,
                rowKey: `${item.department}_${item.domain}_${item.team}_${item.team_type}_${item.skill_category}_${index}`
            }));
            // 更新年月列表
            if (response.year_months && response.year_months.length > 0) {
                yearMonths.value = response.year_months;
            } else {
                // 如果没有返回年月列表，从数据中提取
                const yms = new Set();
                tableDataList.value.forEach(row => {
                    Object.keys(row).forEach(key => {
                        if (/^\d{4}-\d{2}$/.test(key)) {
                            yms.add(key);
                        }
                    });
                });
                yearMonths.value = Array.from(yms).sort();
            }
            // 重新生成表格列
            generateTableColumns();
        } else {
            MessagePlugin.error(response?.message || '加载数据失败');
            tableDataList.value = [];
            yearMonths.value = [];
            generateTableColumns();
        }
    } catch (error) {
        console.error('数据加载失败:', error);
        MessagePlugin.error('数据加载失败: ' + (error.message || '网络错误'));
        tableDataList.value = [];
        yearMonths.value = [];
        generateTableColumns();
    } finally {
        loading.value = false;
    }
};

// 查询按钮
const handleQuery = async () => {
    await loadData();
};
</script>

<style scoped>
.scene-main {
    padding: 16px;
}

/* 表格数据单元格样式 */
:deep(.t-table__body) td {
    color: #555 !important;
    font-weight: normal !important;
    background-color: #fefefe !important;
    border-bottom: 1px solid #d6d6d6 !important;
    line-height: 1.4;
    border-left: none !important;
    border-right: none !important;
}

/* 表格头样式 */
:deep(.t-table__header) th {
    background-color: #e7e7e7 !important;
    color: #333 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #e0e0e0 !important;
    border-left: none !important;
    border-right: none !important;
    line-height: 1.4;
}

/* 奇偶行颜色区分 */
:deep(.t-table__body) tr:nth-child(even) td {
    background-color: #f8f8f8 !important;
}

/* 悬停效果 */
:deep(.t-table__body) tr:hover td {
    background-color: #dbeafe !important;
    transition: background-color 0.3s ease;
}
</style>
