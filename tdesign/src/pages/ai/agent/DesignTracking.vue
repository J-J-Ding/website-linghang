<!-- src/pages/ai/agent/DesignTracking.vue -->
<template>
  <div class="design-tracking">
    <div class="tracking-content">
      <!-- 按钮区域，与知识库页面保持一致 -->
      <div class="knowledge-actions" style="margin-bottom: 16px;">
        <!-- 下拉框选择 -->
        <t-select
          v-model="activeTab"
          :options="tabOptions"
          style="width: 200px; margin-right: 16px;"
        />

        <t-input
          v-model="searchText"
          placeholder="搜索详设方案..."
          clearable
          style="width: 300px; margin-right: 16px;"
        >
          <template #prefix-icon>
            <search-icon />
          </template>
        </t-input>

        <!-- 手动导入按钮 -->
        <t-button @click="openImportDialog" variant="outline" theme="primary" style="margin-right: 8px;">
          <template #icon><add-icon /></template>
          手动导入
        </t-button>

        <t-button @click="refreshData" variant="outline">
          <template #icon><refresh-icon /></template>
          刷新
        </t-button>
        <t-button @click="goBack" theme="primary">
          <template #icon><arrow-left-icon /></template>
          返回聊天
        </t-button>
      </div>

      <!-- 统计卡片 -->
      <t-row :gutter="[16, 16]">
        <t-col :span="12">
          <t-card title="详设进展统计" :bordered="false" hover-shadow>
            <div class="stat-cards-container">
              <!-- 详设总数统计卡片 -->
              <div class="stat-card total-card">
                <div class="stat-value">{{ totalDesigns }}</div>
                <div class="stat-label">25H2规划核心详设总数</div>
              </div>
              
              <!-- 详设进展统计卡片 -->
              <div 
                v-for="stat in progressStats" 
                :key="stat.label" 
                class="stat-card"
              >
                <div class="stat-value">{{ stat.count }}</div>
                <div class="stat-label">{{ stat.label }}</div>
                <div class="stat-percent">{{ stat.percentage }}%</div>
              </div>
            </div>
          </t-card>
        </t-col>
      </t-row>

      <!-- 详细设计跟踪表格 -->
      <t-row :gutter="[16, 16]" style="margin-top: 16px;">
        <t-col :span="24">
          <t-card title="详细设计跟踪列表" :bordered="false" hover-shadow>
            <t-table
              :data="filteredDesigns"
              :columns="designColumns"
              row-key="id"
              :pagination="pagination"
              :loading="loading"
              @page-change="handlePageChange"
            >
              <template #team="{ row }">
                <span class="team-name">{{ row.team }}</span>
              </template>
              <template #design_name="{ row }">
                <span class="design-name">{{ row.design_name }}</span>
              </template>
              <template #design_link="{ row }">
                <t-link theme="primary" :href="row.design_link" target="_blank" v-if="row.design_link">
                  查看详设
                </t-link>
                <span v-else>-</span>
              </template>
              <template #progress="{ row }">
                <t-progress
                  :percentage="row.progress"
                  :status="getProgressStatus(row.progress)"
                  :stroke-width="6"
                />
              </template>
              <template #responsible="{ row }">
                <span class="responsible">{{ row.responsible }}</span>
              </template>
              <template #design_progress="{ row }">
                <span class="design-progress">{{ row.design_progress }}</span>
              </template>
              <template #expected_completion_date="{ row }">
                <span class="expected-date" :class="getDeadlineClass(row.expected_completion_date)">{{ row.expected_completion_date }}</span>
              </template>
              <template #review_result="{ row }">
                <t-tag :theme="getReviewResultTheme(row.review_result)" size="small">
                  {{ row.review_result }}
                </t-tag>
              </template>
              <template #review_report="{ row }">
                <t-link theme="primary" @click="viewReviewReport(row)" v-if="row.review_report">
                  查看报告
                </t-link>
                <span v-else>-</span>
              </template>
              <template #actions="{ row }">
                <t-button size="small" variant="text" @click="viewDesignDetail(row)">
                  查看详情
                </t-button>
                <t-button size="small" variant="text" @click="editDesign(row)">
                  编辑
                </t-button>
                <t-popconfirm
                  theme="danger"
                  content="确定要删除这个详设方案吗？"
                  @confirm="deleteDesign(row.design_id)"
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

    <!-- 设计详情抽屉 -->
    <t-drawer
      v-model:visible="detailVisible"
      header="详设方案详情"
      size="800px"
      :footer="false"
    >
      <div class="design-detail">
        <div class="detail-header">
          <h3>{{ selectedDesign.design_name }}</h3>
          <div class="detail-meta">
            <t-tag theme="default">{{ selectedDesign.team }}</t-tag>
            <span class="detail-date">预期定稿: {{ selectedDesign.expected_completion_date }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="basic-info">
            <div class="info-item">
              <span class="label">团队:</span>
              <span class="value">{{ selectedDesign.team }}</span>
            </div>
            <div class="info-item">
              <span class="label">详设名称:</span>
              <span class="value">{{ selectedDesign.design_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">详设链接:</span>
              <t-link theme="primary" :href="selectedDesign.design_link" target="_blank" v-if="selectedDesign.design_link">
                {{ selectedDesign.design_link }}
              </t-link>
              <span v-else>-</span>
            </div>
            <div class="info-item">
              <span class="label">负责人:</span>
              <span class="value">{{ selectedDesign.responsible }}</span>
            </div>
            <div class="info-item">
              <span class="label">预期定稿日期:</span>
              <span class="value" :class="getDeadlineClass(selectedDesign.expected_completion_date)">{{ selectedDesign.expected_completion_date }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>进度信息</h4>
          <div class="progress-info">
            <t-progress
              :percentage="selectedDesign.progress"
              :status="getProgressStatus(selectedDesign.progress)"
              :stroke-width="8"
              :label-inner="true"
            />
            <div class="progress-text">{{ selectedDesign.design_progress }}</div>
          </div>
        </div>

        <div class="detail-section">
          <h4>评审信息</h4>
          <div class="review-info">
            <div class="info-item">
              <span class="label">组件设计评审结果:</span>
              <t-tag :theme="getReviewResultTheme(selectedDesign.review_result)" size="small">
                {{ selectedDesign.review_result }}
              </t-tag>
            </div>
            <div class="info-item">
              <span class="label">组件设计评审报告:</span>
              <t-link theme="primary" @click="viewReviewReport(selectedDesign)" v-if="selectedDesign.review_report">
                查看报告
              </t-link>
              <span v-else>-</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>变更记录</h4>
          <div class="change-history">
            <t-timeline>
              <t-timeline-item
                v-for="change in selectedDesign.change_history"
                :key="change.id"
                :dot-color="getChangeDotColor(change.type)"
              >
                <div class="change-item">
                  <div class="change-header">
                    <span class="change-type">{{ change.type }}</span>
                    <span class="change-time">{{ change.time }}</span>
                  </div>
                  <div class="change-content">{{ change.content }}</div>
                  <div class="change-author">{{ change.author }}</div>
                </div>
              </t-timeline-item>
            </t-timeline>
          </div>
        </div>
      </div>
    </t-drawer>

<!-- 编辑对话框 -->
    <t-dialog
        v-model:visible="editVisible"
        :header="isEditing ? '编辑详设方案' : '新增详设方案'"
        :confirm-btn="{
          content: '保存',
          theme: 'primary',
          loading: saving
        }"
        :onConfirm="saveDesign"
        width="800px"
    >
      <t-form :data="designForm" :rules="formRules" label-width="150px">
        <t-form-item label="团队" name="team">
          <t-select
            v-model="designForm.team"
            :options="teamOptions"
            placeholder="请选择团队"
            filterable
          />
        </t-form-item>

        <t-form-item label="详设名称" name="design_name">
          <t-input
            v-model="designForm.design_name"
            placeholder="请输入详设名称"
          />
        </t-form-item>

        <t-form-item label="详设链接" name="design_link">
          <t-input
            v-model="designForm.design_link"
            placeholder="请输入详设链接"
          />
        </t-form-item>

        <t-form-item label="进度(%)" name="progress">
          <t-slider
            v-model="designForm.progress"
            :min="0"
            :max="100"
            show-tooltip
          />
          <div class="progress-display">{{ designForm.progress }}%</div>
        </t-form-item>

        <t-form-item label="负责人" name="responsible">
          <t-input
            v-model="designForm.responsible"
            placeholder="请输入负责人"
          />
        </t-form-item>

        <t-form-item label="详设进展" name="design_progress">
          <t-select
            v-model="designForm.design_progress"
            :options="progressOptions"
            placeholder="请选择详设进展"
            filterable
          />
        </t-form-item>

        <t-form-item label="预期定稿日期" name="expected_completion_date">
          <t-date-picker
            v-model="designForm.expected_completion_date"
            placeholder="请选择预期定稿日期"
          />
        </t-form-item>

        <t-form-item label="组件设计评审结果" name="review_result">
          <t-select
            v-model="designForm.review_result"
            :options="reviewResultOptions"
            placeholder="请选择评审结果"
          />
        </t-form-item>

        <t-form-item label="组件设计评审报告" name="review_report">
          <t-input
            v-model="designForm.review_report"
            placeholder="请输入评审报告链接"
          />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 手动导入对话框 -->
    <t-dialog
      v-model:visible="importDialogVisible"
      :header="`手动导入详设数据 - ${isBatchImport ? '批量模式' : '单条模式'}`"
      :confirm-btn="{
        content: '导入',
        theme: 'primary',
        loading: importing
      }"
      :onConfirm="importDataManually"
      width="800px"
      @close="resetImportForm"
    >
      <div class="import-mode-toggle">
        <t-radio-group v-model="importMode" @change="toggleImportMode">
          <t-radio value="single">单条导入</t-radio>
          <t-radio value="batch">批量导入</t-radio>
        </t-radio-group>
      </div>

      <!-- 单条导入模式 -->
      <div v-if="importMode === 'single'">
        <t-form :data="singleImportForm" label-width="150px">
          <t-form-item label="团队" name="team">
            <t-select
              v-model="singleImportForm.team"
              :options="teamOptions"
              placeholder="请选择团队"
              filterable
            />
          </t-form-item>

          <t-form-item label="详设名称" name="design_name">
            <t-input
              v-model="singleImportForm.design_name"
              placeholder="请输入详设名称"
            />
          </t-form-item>

          <t-form-item label="详设链接" name="design_link">
            <t-input
              v-model="singleImportForm.design_link"
              placeholder="请输入详设链接"
            />
          </t-form-item>

          <t-form-item label="进度(%)" name="progress">
            <t-slider
              v-model="singleImportForm.progress"
              :min="0"
              :max="100"
              show-tooltip
            />
            <div class="progress-display">{{ singleImportForm.progress }}%</div>
          </t-form-item>

          <t-form-item label="负责人" name="responsible">
            <t-input
              v-model="singleImportForm.responsible"
              placeholder="请输入负责人"
            />
          </t-form-item>

          <t-form-item label="详设进展" name="design_progress">
            <t-select
              v-model="singleImportForm.design_progress"
              :options="progressOptions"
              placeholder="请选择详设进展"
              filterable
            />
          </t-form-item>

          <t-form-item label="预期定稿日期" name="expected_completion_date">
            <t-date-picker
              v-model="singleImportForm.expected_completion_date"
              placeholder="请选择预期定稿日期"
            />
          </t-form-item>

          <t-form-item label="组件设计评审结果" name="review_result">
            <t-select
              v-model="singleImportForm.review_result"
              :options="reviewResultOptions"
              placeholder="请选择评审结果"
            />
          </t-form-item>

          <t-form-item label="组件设计评审报告" name="review_report">
            <t-input
              v-model="singleImportForm.review_report"
              placeholder="请输入评审报告链接"
            />
          </t-form-item>
        </t-form>
      </div>

      <!-- 批量导入模式 -->
      <div v-if="importMode === 'batch'">
        <t-alert theme="info" style="margin-bottom: 16px;">
          <div>
            <p><strong>批量导入说明：</strong></p>
            <p>请按照以下格式每行输入一条记录：</p>
            <p style="font-family: monospace; background: #f5f5f5; padding: 8px; border-radius: 4px;">
              团队,详设名称,详设链接,进度,负责人,详设进展,预期定稿日期,组件设计评审结果,组件设计评审报告
            </p>
            <p>例如：</p>
            <p style="font-family: monospace; background: #f5f5f5; padding: 8px; border-radius: 4px;">
              前端团队,用户登录页面详设,http://example.com/design1,75,张三,需求分析完成,2024-02-01,通过,http://example.com/report1
            </p>
          </div>
        </t-alert>

        <t-form-item label="批量数据">
          <t-textarea
            v-model="batchImportData"
            placeholder="请输入批量数据，每行一条记录"
            :autosize="{ minRows: 6, maxRows: 12 }"
          />
        </t-form-item>
      </div>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { MessagePlugin } from 'tdesign-vue-next';
import { SearchIcon, RefreshIcon, ArrowLeftIcon, AddIcon } from 'tdesign-icons-vue-next';
import { useUserStore } from '@/store';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const user = useUserStore();

// 页面切换状态 - 添加下拉框选项
const activeTab = ref('designTracking'); // 与知识库页面保持一致
const tabOptions = [
  { label: '核心详设进展跟踪', value: 'designTracking' }
];

// 状态管理
const designs = ref([]);
const stages = ref([]);
const stats = ref({
  totalDesigns: 0,
  inProgress: 0,
  completed: 0
});
const loading = ref(false);
const saving = ref(false);
const importing = ref(false);
const isEditing = ref(false);
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showJumper: true,
  showSizer: true,
  pageSizeOptions: [10, 20, 50, 100]
});

// 详设总数
const totalDesigns = computed(() => {
  return designs.value.length;
});

// 详设进展统计
const progressStats = computed(() => {
  const total = designs.value.length;
  const progressCount = {};
  
  // 统计各个进展的数量
  designs.value.forEach(design => {
    const progress = design.design_progress;
    progressCount[progress] = (progressCount[progress] || 0) + 1;
  });

  // 返回统计结果
  return progressOptions.value.map(option => {
    const count = progressCount[option.value] || 0;
    const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
    return {
      label: option.label,
      value: option.value,
      count: count,
      percentage: percentage
    };
  });
});

// 筛选状态
const searchText = ref('');
const selectedStage = ref(null);

// 抽屉和对话框状态
const detailVisible = ref(false);
const editVisible = ref(false);
const importDialogVisible = ref(false);

// 导入模式状态
const importMode = ref('single'); // 'single' 或 'batch'
const isBatchImport = computed(() => importMode.value === 'batch');

// 表单数据
const designForm = ref({
  team: '',
  design_name: '',
  design_link: '',
  progress: 0,
  responsible: '',
  design_progress: '',
  expected_completion_date: '',
  review_result: '未评审',
  review_report: ''
});

// 单条导入表单数据
const singleImportForm = ref({
  team: '',
  design_name: '',
  design_link: '',
  progress: 0,
  responsible: '',
  design_progress: '',
  expected_completion_date: '',
  review_result: '未评审',
  review_report: ''
});

// 批量导入数据
const batchImportData = ref('');

// 选中的数据
const selectedDesign = ref({});

// 表单验证规则
const formRules = {
  team: [{ required: true, message: '请输入团队名称', trigger: 'blur' }],
  design_name: [{ required: true, message: '请输入详设名称', trigger: 'blur' }],
  responsible: [{ required: true, message: '请输入负责人', trigger: 'blur' }],
  expected_completion_date: [{ required: true, message: '请选择预期定稿日期', trigger: 'change' }]
};

// 表格列定义
const designColumns = [
  { colKey: 'team', title: '团队', width: 120 },
  { colKey: 'design_name', title: '详设名称', width: 200 },
  { colKey: 'design_link', title: '详设链接', width: 120 },
  { colKey: 'progress', title: '进度', width: 150 },
  { colKey: 'responsible', title: '负责人', width: 100 },
  { colKey: 'design_progress', title: '详设进展', width: 200 },
  { colKey: 'expected_completion_date', title: '预期定稿日期', width: 120 },
  { colKey: 'review_result', title: '组件设计评审结果', width: 150 },
  { colKey: 'review_report', title: '组件设计评审报告', width: 150 },
  { colKey: 'actions', title: '操作', width: 150, fixed: 'right' }
];

// 选项数据
const teamOptions = ref([
  { label: 'L0-极光', value: 'L0-极光' },
  { label: 'L0-光速', value: 'L0-光速' },
  { label: 'L0-疾电之光', value: 'L0-疾电之光' },
  { label: 'L2-超能', value: 'L2-超能' },
  { label: 'L2-集结号', value: 'L2-集结号' },
  { label: '支撑-Baseman守垒员', value: '支撑-Baseman守垒员' },
  { label: '支撑-猿宇宙', value: '支撑-猿宇宙' },
  { label: '支撑-北极星', value: '支撑-北极星' },
  { label: '支撑-Starwar', value: '支撑-Starwar' },
  { label: '支撑-茅店神', value: '支撑-茅店神' },
  { label: '支撑-破冰号', value: '支撑-破冰号' },
  { label: '支撑-乘风破浪', value: '支撑-乘风破浪' }
]);

const progressOptions = ref([
  { label: '未开始', value: '未开始' },
  { label: '编写中', value: '编写中' },
  { label: '拟定初稿', value: '拟定初稿' },
  { label: '完成内部评审', value: '完成内部评审' },
  { label: '完成部门评审', value: '完成部门评审' },
  { label: '用例和评审意见闭环中', value: '用例和评审意见闭环中' },
  { label: '已定稿', value: '已定稿' }
]);

const reviewResultOptions = [
  { label: '评审通过', value: '评审通过' },
  { label: '评审不通过', value: '评审不通过' }
];

// 监听分页变化
watch(
  () => [pagination.value.current, pagination.value.pageSize],
  () => {
    // 当分页参数变化时，filteredDesigns 会自动重新计算
  },
  { deep: true }
);

// 添加分页变化事件处理
const handlePageChange = (pageInfo) => {
  pagination.value.current = pageInfo.current;
  pagination.value.pageSize = pageInfo.pageSize;
};

// 过滤后的数据
const filteredDesigns = computed(() => {
  let result = designs.value;

  if (searchText.value) {
    const search = searchText.value.toLowerCase();
    result = result.filter(design =>
      design.team.toLowerCase().includes(search) ||
      design.design_name.toLowerCase().includes(search) ||
      design.responsible.toLowerCase().includes(search)
    );
  }

  if (selectedStage.value) {
    result = result.filter(design => design.stage === selectedStage.value);
  }

  // 更新总数量
  pagination.value.total = result.length;

  // 计算当前页的数据
  const start = (pagination.value.current - 1) * pagination.value.pageSize;
  const end = start + pagination.value.pageSize;
  return result.slice(start, end);
});

// 获取设计数据
const getDesigns = async () => {
  loading.value = true;
  try {
      MessagePlugin.success('开始刷新...');
      // 刷新一次表格
      const response = await fetch(`${SERVER_API_URL}/api_data/API_Design_get`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok)
      {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      const response_data = await response.json();
      if (response_data.status === 'success')
      {
          MessagePlugin.success('数据更新成功');
      }
      else
      {
          MessagePlugin.error(data.message || '数据更新失败');
      }
      // designs.value = response_data.core_design_data;
      designs.value = response_data.core_design_data.map(design => ({  // 获取返回的核心详设数据
        ...design,
        progress: typeof design.progress === 'string' ? parseInt(design.progress, 10) : design.progress
      }));

      stats.value = {
        totalDesigns: designs.value.length,
        inProgress: designs.value.filter(d => d.progress > 0 && d.progress < 100).length,
        completed: designs.value.filter(d => d.progress === 100).length
      };

      stages.value = [
          { id: '需求分析', name: '需求分析', count: 0 },
          { id: '方案设计', name: '方案设计', count: 0 },
          { id: '详细设计', name: '详细设计', count: 0 },
          { id: '开发实施', name: '开发实施', count: 0 },
          { id: '测试验证', name: '测试验证', count: 0 },
          { id: '上线部署', name: '上线部署', count: 0 }
      ];
  } catch (error) {
    console.error('获取设计数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 根据进度获取状态
const getProgressStatus = (progress) => {
  if (progress === 100) return 'success';
  if (progress >= 80) return 'warning';
  return 'default';
};

// 获取评审结果主题
const getReviewResultTheme = (result) => {
  const themeMap = {
    '未评审': 'default',
    '通过': 'success',
    '有条件通过': 'warning',
    '不通过': 'danger'
  };
  return themeMap[result] || 'default';
};

// 获取截止日期样式类
const getDeadlineClass = (deadline) => {
  const deadlineDate = new Date(deadline);
  const today = new Date();
  const diffTime = deadlineDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return 'deadline-overdue';
  if (diffDays <= 3) return 'deadline-near';
  return 'deadline-normal';
};

// 获取变更点颜色
const getChangeDotColor = (type) => {
  if (type === '创建') return '#0052d9';
  if (type === '修改') return '#ff7a00';
  return '#666';
};

// 操作函数
const selectStage = (stageId) => {
  selectedStage.value = selectedStage.value === stageId ? null : stageId;
};

const viewDesignDetail = (design) => {
  selectedDesign.value = design;
  detailVisible.value = true;
};

const viewReviewReport = (design) => {
  if (design.review_report) {
    window.open(design.review_report, '_blank');
  } else {
    MessagePlugin.warning('暂无评审报告');
  }
};

const editDesign = (design) => {
  isEditing.value = true;
  designForm.value = { ...design };
  editVisible.value = true;
};

const addDesign = () => {
  isEditing.value = false;
  designForm.value = {
    team: '',
    design_name: '',
    design_link: '',
    progress: 0,
    responsible: '',
    design_progress: '',
    expected_completion_date: '',
    review_result: '未评审',
    review_report: ''
  };
  editVisible.value = true;
};

const saveDesign = async () => {
    saving.value = true;
    try {
        // 这里需要调用后端API保存设计数据
        const response = await fetch(`${SERVER_API_URL}/api_data/API_Design_set`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  team: designForm.value.team,
                  design_name: designForm.value.design_name,
                  design_link: designForm.value.design_link,
                  progress: designForm.value.progress,
                  responsible: designForm.value.responsible,
                  design_progress: designForm.value.design_progress,
                  expected_completion_date: designForm.value.expected_completion_date,
                  review_result: designForm.value.review_result,
                  review_report: designForm.value.review_report
              }),
            });

            if (!response.ok)
            {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.status === 'success')
            {
                MessagePlugin.success(isEditing.value ? '详设方案更新成功' : '详设方案创建成功');
            }
            else
            {
                MessagePlugin.error(isEditing.value ? (data.message || '详设方案更新失败') : (data.message || '详设方案创建失败'));
            }
        // MessagePlugin.success(isEditing.value ? '详设方案更新成功' : '详设方案创建成功');
            editVisible.value = false;
            getDesigns();
    } catch (error) {
        console.error('保存详设方案失败:', error);
    } finally {
        saving.value = false;
    }
};

const deleteDesign = async (designId) => {
    try {
        console.log('要删除的设计ID:', designId);

        const response = await fetch(`${SERVER_API_URL}/api_data/API_Design_delete`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                design_id: designId
            }),
          });

        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success')
        {
            MessagePlugin.success('单条详设数据删除成功');
        }
        else
        {
            MessagePlugin.error(data.message || '单条详设数据删除失败');
        }
        getDesigns();
    }
    catch (error)
    {
        MessagePlugin.error('删除过程异常，请稍后再试');
    }
};

// 导入相关函数
const toggleImportMode = (mode) => {
  importMode.value = mode;
};

const resetImportForm = () => {
  singleImportForm.value = {
    team: '',
    design_name: '',
    design_link: '',
    progress: 0,
    responsible: '',
    design_progress: '',
    expected_completion_date: '',
    review_result: '未评审',
    review_report: ''
  };
  batchImportData.value = '';
  importMode.value = 'single';
};

const openImportDialog = () => {
  importDialogVisible.value = true;
  resetImportForm();
};

const importDataManually = async () => {
  importing.value = true;
  try {
    if (importMode.value === 'single') {
      // 单条导入 - 验证必填字段
      if (!singleImportForm.value.team || !singleImportForm.value.design_name || !singleImportForm.value.responsible) {
        MessagePlugin.error('请填写必填字段：团队、详设名称、负责人');
        importing.value = false;
        return;
      }
      MessagePlugin.loading('正在导入...');
      try {
        const response = await fetch(`${SERVER_API_URL}/api_data/API_Design_set`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            team: singleImportForm.value.team,
            design_name: singleImportForm.value.design_name,
            design_link: singleImportForm.value.design_link,
            progress: singleImportForm.value.progress,
            responsible: singleImportForm.value.responsible,
            design_progress: singleImportForm.value.design_progress,
            expected_completion_date: singleImportForm.value.expected_completion_date,
            review_result: singleImportForm.value.review_result,
            review_report: singleImportForm.value.review_report
            // 根据你的后端接口，可能还需要其他字段
          }),
        });

        if (!response.ok)
        {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success')
        {
          MessagePlugin.success('单条详设数据导入成功');
        }
        else
        {
          MessagePlugin.error(data.message || '单条详设数据导入失败');
        }
      }
      catch (err)
      {
        MessagePlugin.error('导入过程异常，请稍后再试');
      }
    }
    else
    {
      // 批量导入
      if (!batchImportData.value.trim()) {
        importing.value = false;
        return;
      }

      const lines = batchImportData.value.split('\n').filter(line => line.trim());
      const designsToImport = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const designData = parseBatchDesignData(line);
        if (designData) {
          designsToImport.push(designData);
        } else {
          MessagePlugin.warning(`第 ${i + 1} 行数据格式错误，已跳过: ${line}`);
        }
      }

      if (designsToImport.length === 0) {
        MessagePlugin.error('没有有效的数据可以导入');
        importing.value = false;
        return;
      }

      // 批量导入到后端
      MessagePlugin.loading(`正在批量导入 ${designsToImport.length} 条数据...`);
      try {
        const response = await fetch(`${SERVER_API_URL}/api_data/API_Design_batch_set`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            designs: designsToImport
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
          MessagePlugin.success(`批量导入成功，共导入 ${designsToImport.length} 条记录`);
        } else {
          MessagePlugin.error(data.message || `批量导入失败，成功 ${data.success_count || 0} 条，失败 ${data.failed_count || 0} 条`);
        }
      } catch (err) {
        MessagePlugin.error('批量导入过程异常，请稍后再试');
      }
    }

    importDialogVisible.value = false;
    refreshData();
  } catch (error) {
    console.error('手动导入失败:', error);
    MessagePlugin.error('导入失败: ' + error.message);
  } finally {
    importing.value = false;
  }
};

const parseBatchDesignData = (line) => {
  try {
    const parts = line.split(',').map(part => part.trim());
    // 数据格式应为：团队,详设名称,详设链接,进度,负责人,详设进展,预期定稿日期,组件设计评审结果,组件设计评审报告
    // 对应数据库字段：team, design_name, design_link, progress, responsible, design_progress, expected_completion_date, review_result, review_report
    if (parts.length < 9) {
      console.warn('数据格式不完整，缺少必要字段:', line);
      return null; // 数据不完整
    }

    return {
      team: parts[0] || '', // 数据库字段 team
      design_name: parts[1] || '', // 数据库字段 design_name
      design_link: parts[2] || '', // 数据库字段 design_link
      progress: parseInt(parts[3]) || 0, // 数据库字段 progress
      responsible: parts[4] || '', // 数据库字段 responsible (注意：数据库里是'responsible'，不是'responsibility')
      design_progress: parts[5] || '', // 数据库字段 design_progress
      expected_completion_date: parts[6] || '', // 数据库字段 expected_completion_date
      review_result: parts[7] || '未评审', // 数据库字段 review_result
      review_report: parts[8] || '' // 数据库字段 review_report
    };
  } catch (error) {
    console.error('解析批量导入数据失败:', error);
    return null;
  }
};

const refreshData = () => {
  getDesigns();
};

const goBack = () => {
  router.go(-1);
};

onMounted(() => {
  getDesigns();
});
</script>

<style scoped>
.design-tracking {
  padding: 24px;
  height: 100%;
  background-color: #f5f5f5;
}

.tracking-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
}

/* 与知识库页面保持一致的按钮区域样式 */
.knowledge-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
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

.stage-list {
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

.basic-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.info-item .value {
  color: #666;
}

.progress-info {
  margin-top: 16px;
}

.progress-text {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.review-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.change-history {
  max-height: 300px;
  overflow-y: auto;
}

.change-item {
  padding: 8px 0;
}

.change-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.change-type {
  font-weight: 500;
  color: #333;
}

.change-time {
  color: #999;
  font-size: 12px;
}

.change-content {
  color: #666;
  font-size: 14px;
  margin-bottom: 4px;
}

.change-author {
  color: #999;
  font-size: 12px;
}

.team-name {
  font-weight: 500;
  color: #333;
}

.design-name {
  font-weight: 500;
  color: #0052d9;
}

.responsible {
  color: #666;
}

.design-progress {
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.expected-date {
  color: #999;
  font-size: 12px;
}

.deadline-overdue {
  color: #e34d59;
  font-weight: bold;
}

.deadline-near {
  color: #ff7a00;
  font-weight: 500;
}

.deadline-normal {
  color: #666;
}

.import-mode-toggle {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e4e4;
}

.progress-display {
  margin-top: 8px;
  text-align: center;
  font-weight: bold;
  color: #0052d9;
  font-size: 16px;
}

.stat-cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat-card {
  flex: 1;
  min-width: 120px; /* 设置最小宽度 */
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e4e4e4;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #68c6d6;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-percent {
  font-size: 14px;
  color: #999;
}

/* 如果卡片数量较少，确保它们能平均分布 */
.stat-cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  max-width: 200px; /* 限制最大宽度，防止卡片过宽 */
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e4e4e4;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  max-width: 200px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e4e4e4;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.total-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.total-card .stat-value,
.total-card .stat-label,
.total-card .stat-percent {
  color: white !important;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #0052d9;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-percent {
  font-size: 14px;
  color: #999;
}
</style>
