<!-- src/pages/ai/agent/MetricsSystem.vue -->
<template>
  <div class="metrics-system">
    <div class="metrics-header">
      <h2>度量系统</h2>
      <div class="metrics-actions">
        <t-input
          v-model="searchText"
          placeholder="搜索度量指标..."
          clearable
          style="width: 300px; margin-right: 16px;"
        >
          <template #prefix-icon>
            <search-icon />
          </template>
        </t-input>
        <t-button @click="refreshData" variant="outline">
          <template #icon><refresh-icon /></template>
          刷新
        </t-button>
        <t-button @click="goBack" theme="primary">
          <template #icon><arrow-left-icon /></template>
          返回聊天
        </t-button>
      </div>
    </div>

    <div class="metrics-content">
      <t-row :gutter="[16, 16]">
        <!-- 统计卡片 -->
        <t-col :span="6">
          <t-card title="总体统计" :bordered="false" hover-shadow>
            <div class="stat-item">
              <div class="stat-number">{{ stats.totalMetrics }}</div>
              <div class="stat-label">度量指标总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ stats.activeMetrics }}</div>
              <div class="stat-label">活跃指标</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ stats.alertMetrics }}</div>
              <div class="stat-label">告警指标</div>
            </div>
          </t-card>
        </t-col>

        <t-col :span="18">
          <t-card title="指标分类" :bordered="false" hover-shadow>
            <div class="category-list">
              <t-tag
                v-for="category in categories"
                :key="category.id"
                :theme="selectedCategory === category.id ? 'primary' : 'default'"
                @click="selectCategory(category.id)"
                style="margin: 4px; cursor: pointer;"
              >
                {{ category.name }} ({{ category.count }})
              </t-tag>
            </div>
          </t-card>
        </t-col>
      </t-row>

      <t-row :gutter="[16, 16]" style="margin-top: 16px;">
        <t-col :span="24">
          <!-- 度量指标表格 -->
          <t-card title="度量指标列表" :bordered="false" hover-shadow>
            <t-table
              :data="filteredMetrics"
              :columns="metricColumns"
              row-key="id"
              :pagination="pagination"
              :loading="loading"
            >
              <template #name="{ row }">
                <span class="metric-name">{{ row.name }}</span>
              </template>
              <template #category="{ row }">
                <t-tag theme="primary" size="small">{{ row.category }}</t-tag>
              </template>
              <template #current_value="{ row }">
                <span class="current-value" :class="getValueClass(row)">{{ row.current_value }}</span>
              </template>
              <template #threshold="{ row }">
                <span class="threshold">{{ row.threshold }}</span>
              </template>
              <template #status="{ row }">
                <t-tag :theme="getStatusTheme(row.status)" size="small">
                  {{ row.status }}
                </t-tag>
              </template>
              <template #last_updated="{ row }">
                <span class="last-updated">{{ row.last_updated }}</span>
              </template>
              <template #actions="{ row }">
                <t-button size="small" variant="text" @click="viewMetricDetail(row)">
                  查看详情
                </t-button>
                <t-button size="small" variant="text" @click="editMetric(row)">
                  编辑
                </t-button>
                <t-popconfirm
                  theme="danger"
                  content="确定要删除这个度量指标吗？"
                  @confirm="deleteMetric(row.id)"
                >
                  <t-button size="small" variant="text" theme="danger">
                    删除
                  </t-button>
                </t-popconfirm>
              </template>
            </t-table>
          </t-card>
        </t-col>
      </t-row>
    </div>

    <!-- 指标详情抽屉 -->
    <t-drawer
      v-model:visible="detailVisible"
      header="度量指标详情"
      size="800px"
      :footer="false"
    >
      <div class="metric-detail">
        <div class="detail-header">
          <h3>{{ selectedMetric.name }}</h3>
          <div class="detail-meta">
            <t-tag theme="primary">{{ selectedMetric.category }}</t-tag>
            <t-tag :theme="getStatusTheme(selectedMetric.status)" size="small">
              {{ selectedMetric.status }}
            </t-tag>
            <span class="detail-date">{{ selectedMetric.last_updated }}</span>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>指标描述</h4>
          <p>{{ selectedMetric.description || '暂无描述' }}</p>
        </div>

        <div class="detail-section">
          <h4>当前值</h4>
          <div class="current-value-display">
            <span class="value">{{ selectedMetric.current_value }}</span>
            <span class="unit">{{ selectedMetric.unit }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>阈值设置</h4>
          <div class="threshold-settings">
            <div class="threshold-item">
              <span class="label">警告阈值:</span>
              <span class="value">{{ selectedMetric.warning_threshold }}</span>
            </div>
            <div class="threshold-item">
              <span class="label">严重阈值:</span>
              <span class="value">{{ selectedMetric.critical_threshold }}</span>
            </div>
            <div class="threshold-item">
              <span class="label">正常范围:</span>
              <span class="value">{{ selectedMetric.normal_range }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>历史趋势</h4>
          <div class="trend-chart">
            <!-- 这里可以集成图表组件 -->
            <div class="chart-placeholder">趋势图表区域</div>
          </div>
        </div>

        <div class="detail-section">
          <h4>告警历史</h4>
          <div class="alert-history">
            <t-table
              :data="selectedMetric.alert_history || []"
              :columns="alertHistoryColumns"
              size="small"
            >
              <template #level="{ row }">
                <t-tag :theme="getAlertLevelTheme(row.level)" size="small">
                  {{ row.level }}
                </t-tag>
              </template>
              <template #time="{ row }">
                <span class="alert-time">{{ row.time }}</span>
              </template>
            </t-table>
          </div>
        </div>
      </div>
    </t-drawer>

    <!-- 编辑对话框 -->
    <t-dialog
      v-model:visible="editVisible"
      :header="isEditing ? '编辑度量指标' : '新增度量指标'"
      :confirm-btn="{
        content: '保存',
        theme: 'primary',
        loading: saving
      }"
      :onConfirm="saveMetric"
      width="800px"
    >
      <t-form :data="metricForm" :rules="formRules" label-width="120px">
        <t-form-item label="指标名称" name="name">
          <t-input v-model="metricForm.name" placeholder="请输入指标名称" />
        </t-form-item>
        <t-form-item label="指标分类" name="category">
          <t-select v-model="metricForm.category" :options="categoryOptions" />
        </t-form-item>
        <t-form-item label="指标描述" name="description">
          <t-textarea
            v-model="metricForm.description"
            placeholder="请输入指标描述"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item label="单位" name="unit">
          <t-input v-model="metricForm.unit" placeholder="请输入单位" />
        </t-form-item>
        <t-form-item label="当前值" name="current_value">
          <t-input v-model="metricForm.current_value" placeholder="请输入当前值" />
        </t-form-item>
        <t-form-item label="警告阈值" name="warning_threshold">
          <t-input v-model="metricForm.warning_threshold" placeholder="请输入警告阈值" />
        </t-form-item>
        <t-form-item label="严重阈值" name="critical_threshold">
          <t-input v-model="metricForm.critical_threshold" placeholder="请输入严重阈值" />
        </t-form-item>
        <t-form-item label="状态" name="status">
          <t-select v-model="metricForm.status" :options="statusOptions" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { MessagePlugin } from 'tdesign-vue-next';
import { SearchIcon, RefreshIcon, ArrowLeftIcon } from 'tdesign-icons-vue-next';
import { useUserStore } from '@/store';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const user = useUserStore();

// 状态管理
const metrics = ref([]);
const categories = ref([]);
const stats = ref({
  totalMetrics: 0,
  activeMetrics: 0,
  alertMetrics: 0
});
const loading = ref(false);
const saving = ref(false);
const isEditing = ref(false);
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
});

// 筛选状态
const searchText = ref('');
const selectedCategory = ref(null);

// 抽屉和对话框状态
const detailVisible = ref(false);
const editVisible = ref(false);

// 表单数据
const metricForm = ref({
  name: '',
  category: '',
  description: '',
  unit: '',
  current_value: '',
  warning_threshold: '',
  critical_threshold: '',
  status: '正常'
});

// 选中的数据
const selectedMetric = ref({});

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入指标名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择指标分类', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
};

// 表格列定义
const metricColumns = [
  { colKey: 'name', title: '指标名称', width: 200 },
  { colKey: 'category', title: '分类', width: 120 },
  { colKey: 'current_value', title: '当前值', width: 120 },
  { colKey: 'threshold', title: '阈值', width: 120 },
  { colKey: 'status', title: '状态', width: 100 },
  { colKey: 'last_updated', title: '最后更新', width: 140 },
  { colKey: 'actions', title: '操作', width: 150, fixed: 'right' }
];

const alertHistoryColumns = [
  { colKey: 'level', title: '告警级别', width: 100 },
  { colKey: 'message', title: '告警信息', width: 200 },
  { colKey: 'time', title: '告警时间', width: 140 }
];

// 选项数据
const categoryOptions = computed(() => 
  categories.value.map(cat => ({
    label: `${cat.name} (${cat.count})`,
    value: cat.name
  }))
);

const statusOptions = [
  { label: '正常', value: '正常' },
  { label: '警告', value: '警告' },
  { label: '严重', value: '严重' },
  { label: '停用', value: '停用' }
];

// 过滤后的数据
const filteredMetrics = computed(() => {
  let result = metrics.value;

  if (searchText.value) {
    const search = searchText.value.toLowerCase();
    result = result.filter(metric => 
      metric.name.toLowerCase().includes(search) ||
      metric.description.toLowerCase().includes(search)
    );
  }

  if (selectedCategory.value) {
    result = result.filter(metric => metric.category === selectedCategory.value);
  }

  return result;
});

// 获取度量数据
const getMetrics = async () => {
  loading.value = true;
  try {
    // 这里需要调用后端API获取度量数据
    // 暂时使用模拟数据
    metrics.value = [
      {
        id: 1,
        name: 'CPU使用率',
        category: '系统性能',
        current_value: '65%',
        threshold: '<80%',
        status: '正常',
        last_updated: '2024-01-01 10:00:00',
        unit: '%',
        warning_threshold: '70%',
        critical_threshold: '85%',
        description: 'CPU使用率监控指标'
      },
      {
        id: 2,
        name: '内存使用率',
        category: '系统性能',
        current_value: '82%',
        threshold: '<85%',
        status: '警告',
        last_updated: '2024-01-01 10:05:00',
        unit: '%',
        warning_threshold: '75%',
        critical_threshold: '90%',
        description: '内存使用率监控指标'
      }
    ];
    
    stats.value = {
      totalMetrics: metrics.value.length,
      activeMetrics: metrics.value.filter(m => m.status !== '停用').length,
      alertMetrics: metrics.value.filter(m => m.status === '警告' || m.status === '严重').length
    };
    
    categories.value = [
      { id: 1, name: '系统性能', count: 2 },
      { id: 2, name: '业务指标', count: 0 }
    ];
  } catch (error) {
    console.error('获取度量数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 根据值获取样式类
const getValueClass = (row) => {
  if (row.status === '严重') return 'value-critical';
  if (row.status === '警告') return 'value-warning';
  return 'value-normal';
};

// 根据状态获取主题
const getStatusTheme = (status) => {
  const themeMap = {
    '正常': 'success',
    '警告': 'warning',
    '严重': 'danger',
    '停用': 'default'
  };
  return themeMap[status] || 'default';
};

const getAlertLevelTheme = (level) => {
  const themeMap = {
    '信息': 'default',
    '警告': 'warning',
    '严重': 'danger'
  };
  return themeMap[level] || 'default';
};

// 操作函数
const selectCategory = (categoryId) => {
  selectedCategory.value = selectedCategory.value === categoryId ? null : categoryId;
};

const viewMetricDetail = (metric) => {
  selectedMetric.value = metric;
  detailVisible.value = true;
};

const editMetric = (metric) => {
  isEditing.value = true;
  metricForm.value = { ...metric };
  editVisible.value = true;
};

const addMetric = () => {
  isEditing.value = false;
  metricForm.value = {
    name: '',
    category: '',
    description: '',
    unit: '',
    current_value: '',
    warning_threshold: '',
    critical_threshold: '',
    status: '正常'
  };
  editVisible.value = true;
};

const saveMetric = async () => {
  saving.value = true;
  try {
    // 这里需要调用后端API保存度量数据
    MessagePlugin.success(isEditing.value ? '指标更新成功' : '指标创建成功');
    editVisible.value = false;
    getMetrics();
  } catch (error) {
    console.error('保存度量指标失败:', error);
  } finally {
    saving.value = false;
  }
};

const deleteMetric = async (metricId) => {
  try {
    // 这里需要调用后端API删除度量数据
    MessagePlugin.success('指标删除成功');
    getMetrics();
  } catch (error) {
    console.error('删除度量指标失败:', error);
  }
};

const refreshData = () => {
  getMetrics();
};

const goBack = () => {
  router.go(-1);
};

onMounted(() => {
  getMetrics();
});
</script>

<style scoped>
.metrics-system {
  padding: 24px;
  height: 100%;
  background-color: #f5f5f5;
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e4e4;
}

.metrics-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
}

.stat-item {
  margin-bottom: 16px;
  text-align: center;
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: #0052d9;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.category-list {
  display: flex;
  flex-wrap: wrap;
}

.detail-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e4e4;
}

.detail-header h3 {
  margin: 0 0 8px 0;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-date {
  color: #999;
  font-size: 12px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 14px;
}

.current-value-display {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.current-value-display .value {
  font-size: 24px;
  font-weight: bold;
  color: #0052d9;
}

.current-value-display .unit {
  font-size: 14px;
  color: #666;
}

.threshold-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.threshold-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-item .label {
  font-weight: 500;
  color: #333;
  min-width: 80px;
}

.threshold-item .value {
  color: #666;
}

.trend-chart {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.chart-placeholder {
  color: #999;
  font-size: 14px;
}

.alert-history {
  max-height: 300px;
  overflow-y: auto;
}

.value-normal {
  color: #00a870;
}

.value-warning {
  color: #ff7a00;
}

.value-critical {
  color: #e34d59;
}

.alert-time {
  color: #999;
  font-size: 12px;
}
</style>