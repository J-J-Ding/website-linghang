<template>
    <div class="scene-main">
        <t-space direction="vertical" style="width: 100%">
            <!-- ===================== 筛选区域 ===================== -->
            <div class="filter-area">
                <!-- 第一行：时间 + 部门 -->
                <div class="filter-row">
                    <!-- 起止月份（必填） -->
                    <div class="filter-item">
                        <span class="filter-label">时间范围: <span class="required">*</span></span>
                        <t-date-picker
                            v-model="queryParams.start_month"
                            mode="month"
                            placeholder="起始月份"
                            clearable
                            style="width: 140px;"
                            value-format="YYYY-MM"
                            format="YYYY-MM"
                        />
                        <span class="range-sep">~</span>
                        <t-date-picker
                            v-model="queryParams.end_month"
                            mode="month"
                            placeholder="截止月份"
                            clearable
                            style="width: 140px;"
                            value-format="YYYY-MM"
                            format="YYYY-MM"
                        />
                    </div>

                    <!-- 部门 -->
                    <div class="filter-item">
                        <span class="filter-label">部门:</span>
                        <t-select
                            v-model="queryParams.department"
                            placeholder="请选择部门"
                            clearable
                            style="width: 160px;"
                            :options="departmentOptions"
                            filterable
                        />
                    </div>
                </div>

                <!-- 第二行：领域 + 团队 + 技能分类 -->
                <div class="filter-row">
                    <!-- 领域（多选） -->
                    <div class="filter-item">
                        <span class="filter-label">领域:</span>
                        <t-select
                            v-model="queryParams.domain"
                            placeholder="请选择领域"
                            clearable
                            multiple
                            style="width: 300px;"
                            :options="domainOptions"
                            filterable
                            :min-collapsed-num="2"
                        />
                    </div>

                    <!-- 团队（多选） -->
                    <div class="filter-item">
                        <span class="filter-label">团队:</span>
                        <t-select
                            v-model="queryParams.team"
                            placeholder="请选择团队"
                            clearable
                            multiple
                            style="width: 300px;"
                            :options="teamOptions"
                            filterable
                            :min-collapsed-num="2"
                        />
                    </div>

                    <!-- 技能/特性分类 -->
                    <div class="filter-item">
                        <span class="filter-label">技能分类:</span>
                        <t-select
                            v-model="queryParams.skill_category"
                            placeholder="请选择技能分类"
                            clearable
                            style="width: 180px;"
                            :options="skillCategoryOptions"
                            filterable
                        />
                    </div>
                </div>

                <!-- 按钮行 -->
                <div class="filter-row filter-btns">
                    <t-button theme="primary" @click="handleQuery">
                        <template #icon><t-icon name="search" /></template>
                        查询
                    </t-button>
                    <t-button theme="default" variant="outline" @click="handleReset">
                        <template #icon><t-icon name="refresh" /></template>
                        重置
                    </t-button>
                </div>
            </div>

            <!-- ===================== 说明提示 ===================== -->
            <t-alert v-if="showTip" theme="info" close message="" style="margin-bottom: 4px;">
                <template #message>
                    <span>
                        剩余可用人力计算：需求交付可用人力 - 已用人力。
                        <span style="color: #e34d59; font-weight: 600;">红色</span> 表示剩余 &lt; 0（超用），
                        <span style="color: #00a870; font-weight: 600;">绿色</span> 表示剩余 &gt; 1（充裕）。
                        数据来源于 domain_team_available_human_resource 表，已按所选时间范围聚合。
                    </span>
                </template>
            </t-alert>
        </t-space>

        <!-- ===================== 数据表格 ===================== -->
        <t-table
            ref="tableRef"
            row-key="rowKey"
            :columns="tableColumnList"
            :data="tableDataList"
            :bordered="true"
            :hover="true"
            resizable
            :loading="loading"
            :max-height="tableHeight"
            size="small"
            stripe
        >
            <!-- 空状态 -->
            <template #empty>
                <div style="padding: 40px 0; color: #888; text-align: center;">
                    <t-icon name="search" size="32" style="display: block; margin: 0 auto 8px;" />
                    请设置筛选条件后点击"查询"
                </div>
            </template>
        </t-table>
    </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { pubCalculateTableHeight } from '@/utils/pub';
import {
    queryAvailableHumanResourceByParams,
    getAvailableHumanResourceOptions
} from '@/api/availableHumanResource.js';

// ----------------------------------------------------------------
// 常量：每月工作天数（与后端保持一致）
// ----------------------------------------------------------------
const WORKING_DAYS_PER_MONTH = 20;

// ----------------------------------------------------------------
// 筛选参数
// ----------------------------------------------------------------
const queryParams = ref({
    start_month: '',      // 起始年月 YYYY-MM
    end_month: '',        // 截止年月 YYYY-MM
    department: '',
    domain: [],           // 多选
    team: [],             // 多选
    skill_category: '',
});

// ----------------------------------------------------------------
// 下拉选项
// ----------------------------------------------------------------
const departmentOptions = ref([]);
const domainOptions = ref([]);
const teamOptions = ref([]);
const skillCategoryOptions = ref([]);
// 注：belong_product 选项已移除，因为新数据源不支持按产品筛选

// 表格
// ----------------------------------------------------------------
const loading = ref(false);
const tableDataList = ref([]);
const tableRef = ref(null);
const tableHeight = ref(600);
const showTip = ref(false);

const getCurrentYearMonth = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    return `${year}-${month}`;
};

// 获取N个月前的年月
const getYearMonthMonthsAgo = (months) => {
    const date = new Date();
    date.setMonth(date.getMonth() - months);
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${year}-${month}`;
};

const getMonthDate = () => {
    queryParams.value.start_month = getYearMonthMonthsAgo(2);
    queryParams.value.end_month = getCurrentYearMonth();
};

// ----------------------------------------------------------------
// 表格列定义
// ----------------------------------------------------------------
/**
 * 剩余可用人力的单元格渲染：
 *   < 0  → 红色（超用）
 *   > 1  → 绿色（充裕）
 *   其他 → 默认
 */
function remainingCell(_, { row }) {
    const val = row.remaining_available_power;
    if (val === null || val === undefined) return '-';
    let color = '';
    if (val < 0) color = '#e34d59';
    else if (val > 1) color = '#00a870';
    return (
        <span style={{ color, fontWeight: color ? '600' : 'normal' }}>
            {formatNum(val)}
        </span>
    );
}

const tableColumnList = ref([
    {
        colKey: 'department',
        title: '部门',
        width: 120,
        align: 'left',
        fixed: 'left',
        ellipsis: { theme: 'light', placement: 'bottom' },
    },
    {
        colKey: 'domain',
        title: '领域',
        width: 150,
        align: 'left',
        fixed: 'left',
        ellipsis: { theme: 'light', placement: 'bottom' },
    },
    {
        colKey: 'team',
        title: '团队',
        width: 160,
        align: 'left',
        fixed: 'left',
        ellipsis: { theme: 'light', placement: 'bottom' },
    },
    {
        colKey: 'team_type',
        title: '团队类型',
        width: 120,
        align: 'center',
        fixed: 'left',
        ellipsis: { theme: 'light', placement: 'bottom' },
    },
    {
        colKey: 'skill_category',
        title: '技能/特性分类',
        width: 180,
        align: 'left',
        fixed: 'left',
        ellipsis: { theme: 'light', placement: 'bottom' },
    },

    // ---- 人力统计列 ----
    {
        colKey: 'total_human_power',
        title: '总人力',
        width: 90,
        align: 'right',
        cell: (_, { row }) => formatNum(row.total_human_power),
        attrs: () => ({ style: 'background: #f0f4ff;' }),
    },
    {
        colKey: 'zte_human_power',
        title: '中兴人力',
        width: 90,
        align: 'right',
        cell: (_, { row }) => formatNum(row.zte_human_power),
        attrs: () => ({ style: 'background: #f0f4ff;' }),
    },
    {
        colKey: 'outsource_human_power',
        title: '外包人力',
        width: 90,
        align: 'right',
        cell: (_, { row }) => formatNum(row.outsource_human_power),
        attrs: () => ({ style: 'background: #f0f4ff;' }),
    },

    // ---- 需求交付列 ----
    {
        colKey: 'demand_delivery_available_power',
        title: '需求交付可用人力',
        width: 150,
        align: 'right',
        cell: (_, { row }) => formatNum(row.demand_delivery_available_power),
        attrs: () => ({ style: 'background: #e8f7e8;' }),
    },

    // ---- 剩余列（带颜色） ----
    {
        colKey: 'remaining_available_power',
        title: '剩余可用人力',
        width: 130,
        align: 'right',
        cell: remainingCell,
    },

    // ---- 已用人力列 ----
    {
        colKey: 'used_human_power',
        title: '已用人力',
        width: 100,
        align: 'right',
        cell: (_, { row }) => formatNum(row.used_human_power),
        attrs: () => ({ style: 'background: #fff7e6;' }),
    },
    {
        colKey: 'used_human_power_1',
        title: '已用人力1（主交付PR）',
        width: 180,
        align: 'right',
        cell: (_, { row }) => formatNum(row.used_human_power_1),
        attrs: () => ({ style: 'background: #fff7e6;' }),
    },
    {
        colKey: 'used_human_power_2',
        title: '已用人力2（非本团队主交付PR关联US）',
        width: 260,
        align: 'right',
        cell: (_, { row }) => formatNum(row.used_human_power_2),
        attrs: () => ({ style: 'background: #fff7e6;' }),
    },
]);

// ----------------------------------------------------------------
// 工具函数
// ----------------------------------------------------------------
function formatNum(val) {
    if (val === null || val === undefined) return '-';
    if (typeof val === 'number') return val;
    return val;
}

// ----------------------------------------------------------------
// 查询
// ----------------------------------------------------------------
async function handleQuery() {
    if (!queryParams.value.start_month) {
        MessagePlugin.warning('请选择起始月份');
        return;
    }
    if (!queryParams.value.end_month) {
        MessagePlugin.warning('请选择截止月份');
        return;
    }
    if (queryParams.value.start_month > queryParams.value.end_month) {
        MessagePlugin.warning('起始月份不能大于截止月份');
        return;
    }

    loading.value = true;
    showTip.value = true;
    try {
        const res = await queryAvailableHumanResourceByParams(queryParams.value);
        // 响应拦截器已返回 response.data，所以 res 就是 { code, data, message }
        if (res && res.code === 200) {
            tableDataList.value = (res.data || []).map((row, idx) => ({
                ...row,
                rowKey: `${row.domain}_${row.team}_${row.skill_category}_${idx}`,
            }));
            if (tableDataList.value.length === 0) {
                MessagePlugin.info('未查询到匹配的数据');
            } else {
                MessagePlugin.success(`查询成功，共 ${tableDataList.value.length} 条`);
            }
        } else {
            MessagePlugin.error(res?.message || '查询失败');
        }
    } catch (e) {
        MessagePlugin.error('请求异常：' + e.message);
    } finally {
        loading.value = false;
    }
}

// ----------------------------------------------------------------
// 重置
// ----------------------------------------------------------------
function handleReset() {
    queryParams.value = {
        start_month: '',
        end_month: '',
        department: '',
        domain: [],
        team: [],
        skill_category: '',
    };
    tableDataList.value = [];
    showTip.value = false;
}

// ----------------------------------------------------------------
// 加载筛选选项
// ----------------------------------------------------------------
async function loadOptions() {
    try {
        const res = await getAvailableHumanResourceOptions();
        console.log('获取选项API响应:', res);
        
        // 响应拦截器已返回 response.data，所以 res 就是 { code, data, message }
        if (res && res.code === 200) {
            const data = res.data || {};
            console.log('选项数据:', data);
            
            departmentOptions.value = (data.department || []).map(v => ({ label: v, value: v }));
            domainOptions.value = (data.domain || []).map(v => ({ label: v, value: v }));
            teamOptions.value = (data.team || []).map(v => ({ label: v, value: v }));
            skillCategoryOptions.value = (data.skill_category || []).map(v => ({ label: v, value: v }));
            
            console.log('加载选项完成:', {
                department: departmentOptions.value.length,
                domain: domainOptions.value.length,
                team: teamOptions.value.length,
                skillCategory: skillCategoryOptions.value.length
            });
        } else {
            console.warn('获取选项失败，响应码:', res?.code, '消息:', res?.message);
            MessagePlugin.warning('加载筛选选项失败: ' + (res?.message || '未知错误'));
        }
    } catch (e) {
        console.error('加载可用人力选项失败', e);
        MessagePlugin.error('加载筛选选项异常: ' + (e.message || '未知错误'));
    }
}

// ----------------------------------------------------------------
// 表格高度自适应
// ----------------------------------------------------------------
function updateTableHeight() {
    tableHeight.value = pubCalculateTableHeight(tableRef.value, 300);
}

onMounted(() => {
    loadOptions();
    updateTableHeight();
    window.addEventListener('resize', updateTableHeight);
    getMonthDate();
    handleQuery();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', updateTableHeight);
});
</script>

<style scoped>
.scene-main {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    box-sizing: border-box;
}

.filter-area {
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: #fafafa;
    border: 1px solid #e7e7e7;
    border-radius: 6px;
    padding: 14px 16px 10px;
}

.filter-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.filter-label {
    font-size: 13px;
    color: #4a4a4a;
    white-space: nowrap;
    flex-shrink: 0;
}

.required {
    color: #e34d59;
}

.range-sep {
    font-size: 14px;
    color: #888;
    padding: 0 2px;
}

.filter-btns {
    padding-top: 4px;
}
</style>
