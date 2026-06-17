<!-- src/pages/ai/agent/DesignKnowledgeBase.vue -->
<template>
  <div class="design-knowledge-base">
    <div class="knowledge-content">
      <!-- 按钮区域 -->
      <div class="knowledge-actions" style="margin-bottom: 16px;">
        <!-- 添加下拉框选择 -->
        <t-select
          v-model="activeTab"
          :options="tabOptions"
          style="width: 200px; margin-right: 16px;"
        />

        <t-input
          v-model="searchText"
          :placeholder="`搜索${getSearchPlaceholder()}...`"
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

      <!-- 场景库表格 -->
      <t-card
        v-if="activeTab === 'scene'"
        title="组件设计场景库"
        :bordered="false"
        hover-shadow
      >
        <t-table
          :data="filteredScenes"
          :columns="sceneColumns"
          row-key="id"
          :pagination="scenePagination"
          :loading="sceneLoading"
        >
          <template #component="{ row }">
            <span class="component-name">{{ row.component }}</span>
          </template>
          <template #function_module="{ row }">
            <span class="function-module">{{ row.function_module }}</span>
          </template>
          <template #business_scenario="{ row }">
            <span class="business-scenario">{{ row.business_scenario }}</span>
          </template>
          <template #related_scenarios="{ row }">
            <div class="related-scenarios">
              <t-tag
                v-for="scenario in row.related_scenarios"
                :key="scenario"
                theme="default"
                size="small"
                style="margin: 2px;"
              >
                {{ scenario }}
              </t-tag>
            </div>
          </template>
          <template #maintenance_team="{ row }">
            <span class="maintenance-team">{{ row.maintenance_team }}</span>
          </template>
          <template #detail_link="{ row }">
            <t-link theme="primary" :href="row.detail_link" target="_blank" v-if="row.detail_link">
              查看详设
            </t-link>
            <span v-else>-</span>
          </template>
          <template #create_time="{ row }">
            <span class="create-time">{{ row.create_time }}</span>
          </template>
          <template #actions="{ row }">
            <t-button size="small" variant="text" @click="editScene(row)">
              编辑
            </t-button>
            <t-popconfirm
              theme="danger"
              content="确定要删除这个场景记录吗？"
              @confirm="deleteScene(row.scene_id)"
            >
              <t-button size="small" variant="text" theme="danger">
                删除
              </t-button>
            </t-popconfirm>
          </template>
        </t-table>
      </t-card>

      <!-- 性能库表格 -->
      <t-card
        v-if="activeTab === 'performance'"
        title="组件设计性能库"
        :bordered="false"
        hover-shadow
      >
        <t-table
          :data="filteredPerformance"
          :columns="performanceColumns"
          row-key="id"
          :pagination="performancePagination"
          :loading="performanceLoading"
        >
          <template #component="{ row }">
            <span class="component-name">{{ row.component }}</span>
          </template>
          <template #performance_type="{ row }">
            <t-tag :theme="getPerformanceTypeTheme(row.performance_type)" size="small">
              {{ row.performance_type }}
            </t-tag>
          </template>
          <template #performance_metrics="{ row }">
            <div class="performance-metrics">{{ row.performance_metrics }}</div>
          </template>
          <template #performance_boundary="{ row }">
            <span class="performance-boundary">{{ row.performance_boundary }}</span>
          </template>
          <template #create_time="{ row }">
            <span class="create-time">{{ row.create_time }}</span>
          </template>
        </t-table>
      </t-card>

      <!-- 故障库表格 -->
      <t-card
        v-if="activeTab === 'fault'"
        title="组件设计故障库"
        :bordered="false"
        hover-shadow
      >
        <t-table
          :data="filteredFaults"
          :columns="faultColumns"
          row-key="id"
          :pagination="faultPagination"
          :loading="faultLoading"
        >
          <template #identifier="{ row }">
            <span class="identifier">{{ row.identifier }}</span>
          </template>
          <template #title="{ row }">
            <span class="fault-title">{{ row.title }}</span>
          </template>
          <template #replay_status="{ row }">
            <t-tag
              :theme="getStatusTheme(row.replay_status)"
              size="small"
            >
              {{ row.replay_status }}
            </t-tag>
          </template>
          <template #team="{ row }">
            <span class="team-name">{{ row.team }}</span>
          </template>
          <template #source="{ row }">
            <span class="source">{{ row.source }}</span>
          </template>
          <template #create_time="{ row }">
            <span class="create-time">{{ row.create_time }}</span>
          </template>
          <template #detail_link="{ row }">
            <t-link theme="primary" @click="viewFaultDetail(row)">
              查看详情
            </t-link>
          </template>
          <template #reason_category="{ row }">
            <span class="reason-category">{{ row.reason_category }}</span>
          </template>
          <template #improvement_measures="{ row }">
            <span class="improvement-measures">{{ row.improvement_measures }}</span>
          </template>
          <template #interception_measures="{ row }">
            <span class="interception-measures">{{ row.interception_measures }}</span>
          </template>
          <template #actions="{ row }">
            <t-button size="small" variant="text" @click="editFault(row)">
              编辑
            </t-button>
            <t-popconfirm
              theme="danger"
              content="确定要删除这个故障记录吗？"
              @confirm="deleteFault(row.id)"
            >
              <t-button size="small" variant="text" theme="danger">
                删除
              </t-button>
            </t-popconfirm>
          </template>
        </t-table>
      </t-card>
    </div>

    <!-- 场景库编辑对话框 -->
    <t-dialog
      v-model:visible="editSceneVisible"
      :header="isSceneEditing ? '编辑场景' : '新增场景'"
      :confirm-btn="{
        content: '保存',
        theme: 'primary',
        loading: saving
      }"
      :onConfirm="saveScene"
      width="800px"
    >
      <t-form :data="sceneForm" :rules="sceneFormRules" label-width="150px">
        <t-form-item label="组件" name="component">
          <t-select v-model="sceneForm.component" :options="componentOptions" />
        </t-form-item>
        <t-form-item label="功能模块" name="function_module">
          <t-input v-model="sceneForm.function_module" placeholder="请输入功能模块" />
        </t-form-item>
        <t-form-item label="业务场景" name="business_scenario">
          <t-textarea
            v-model="sceneForm.business_scenario"
            placeholder="请输入业务场景"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item label="关联场景" name="related_scenarios">
            <t-input
              v-model="sceneForm.related_scenarios"
              placeholder="请输入关联场景，多个场景用英文分号分隔，例如：场景A; 场景B; 场景C"
            />
          </t-form-item>
        <t-form-item label="维护团队" name="maintenance_team">
          <t-select v-model="sceneForm.maintenance_team" :options="teamOptions" />
        </t-form-item>
        <t-form-item label="场景对应详设链接" name="detail_link">
          <t-input v-model="sceneForm.detail_link" placeholder="请输入详设链接" />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 性能库编辑对话框 -->
    <t-dialog
      v-model:visible="editPerformanceVisible"
      :header="isPerformanceEditing ? '编辑性能' : '新增性能'"
      :confirm-btn="{
        content: '保存',
        theme: 'primary',
        loading: saving
      }"
      :onConfirm="savePerformance"
      width="800px"
    >
      <t-form :data="performanceForm" :rules="performanceFormRules" label-width="120px">
        <t-form-item label="组件" name="component">
          <t-select v-model="performanceForm.component" :options="componentOptions" />
        </t-form-item>
        <t-form-item label="性能类型" name="performance_type">
          <t-select v-model="performanceForm.performance_type" :options="performanceTypeOptions" />
        </t-form-item>
        <t-form-item label="性能指标" name="performance_metrics">
          <t-textarea
            v-model="performanceForm.performance_metrics"
            placeholder="请输入性能指标"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </t-form-item>
        <t-form-item label="性能边界值" name="performance_boundary">
          <t-input v-model="performanceForm.performance_boundary" placeholder="请输入性能边界值" />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 故障库编辑对话框 -->
    <t-dialog
      v-model:visible="editFaultVisible"
      :header="isFaultEditing ? '编辑故障' : '新增故障'"
      :confirm-btn="{
        content: '保存',
        theme: 'primary',
        loading: saving
      }"
      :onConfirm="saveFault"
      width="800px"
    >
      <t-form v-if="activeTab === 'fault'" :data="faultForm" :rules="faultFormRules" label-width="120px">
        <t-form-item label="组件" name="component">
          <t-select v-model="faultForm.component" :options="componentOptions" placeholder="请选择组件" filterable />
        </t-form-item>
        <t-form-item label="标识" name="identifier">
          <t-input v-model="faultForm.identifier" placeholder="请输入故障标识" />
        </t-form-item>
        <t-form-item label="标题" name="title">
          <t-input v-model="faultForm.title" placeholder="请输入故障标题" />
        </t-form-item>
        <t-form-item label="引入来源" name="source">
          <t-select v-model="faultForm.source" :options="sourceOptions" placeholder="请选择引入来源" filterable />
        </t-form-item>
        <t-form-item label="故障原因二级分类" name="reason_category">
          <t-select v-model="faultForm.reason_category" :options="reasonCategoryOptions" placeholder="请选择分类" filterable />
        </t-form-item>
        <t-form-item label="故障详设链接" name="detail_link">
          <t-input v-model="faultForm.detail_link" placeholder="请输入链接" />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- 手动导入对话框 -->
    <t-dialog
      v-model:visible="importDialogVisible"
      :header="`手动导入${getImportTitle()}数据`"
      :confirm-btn="{
        content: '导入',
        theme: 'primary',
        loading: importing
      }"
      :onConfirm="importDataManually"
      width="800px"
      @close="resetImportForm"
    >
      <t-form :data="importForm" label-width="120px">
        <t-form-item label="导入类型">
          <t-radio-group v-model="importForm.importType">
            <t-radio value="single">单条导入</t-radio>
            <t-radio value="batch">批量导入</t-radio>
          </t-radio-group>
        </t-form-item>
      </t-form>

        <div v-if="importForm.importType === 'single'">
          <!---
          <t-textarea
            v-model="importForm.singleData"
            :placeholder="getImportPlaceholder()"
            :autosize="{ minRows: 4, maxRows: 8 }"
          />
        </t-form-item>

        <t-form-item v-if="importForm.importType === 'batch'" label="批量数据">
          <t-textarea
            v-model="importForm.batchData"
            :placeholder="getBatchImportPlaceholder()"
            :autosize="{ minRows: 6, maxRows: 12 }"
          />
 -->
          <!-- 场景库导入表单 -->
          <t-form v-if="activeTab === 'scene'"
          :data="sceneForm" label-width="150px">
            <t-form-item label="组件" name="component">
              <t-select
                v-model="sceneForm.component"
                :options="componentOptions"
                placeholder="请选择组件"
                filterable
              />
            </t-form-item>

            <!-- 功能模块 - 手动填写 -->
            <t-form-item label="功能模块" name="function_module">
              <t-input
                v-model="sceneForm.function_module"
                placeholder="请输入功能模块"
              />
            </t-form-item>

          <!-- 业务场景 - 手动填写 -->
          <t-form-item label="业务场景" name="business_scenario">
            <t-textarea
              v-model="sceneForm.business_scenario"
              placeholder="请输入业务场景"
              :autosize="{ minRows: 3, maxRows: 6 }"
            />
          </t-form-item>

          <!-- 关联场景 - 手动填写 -->
          <t-form-item label="关联场景" name="related_scenarios">
            <t-input
              v-model="sceneForm.related_scenarios"
              placeholder="请输入关联场景，多个场景用英文分号分隔，例如：场景A;场景B;场景C"
            />
          </t-form-item>

          <!-- 维护团队 - 下拉框 -->
          <t-form-item label="维护团队" name="maintenance_team">
            <t-select
              v-model="sceneForm.maintenance_team"
              :options="teamOptions"
              placeholder="请选择维护团队"
              filterable
            />
          </t-form-item>

          <t-form-item label="场景对应详设链接" name="detail_link">
          <t-input
            v-model="sceneForm.detail_link"
            placeholder="请输入详设链接"
          />
          </t-form-item>

        </t-form>

        <!-- 性能库导入表单 -->
        <t-form
          v-if="activeTab === 'performance'"
          :data="performanceForm"
          :rules="performanceFormRules" 
          label-width="120px"
        >
          <t-form-item label="组件" name="component">
            <t-select
              v-model="performanceForm.component"
              :options="componentOptions"
              placeholder="请选择组件"
              filterable
            />
          </t-form-item>
          <t-form-item label="性能类型" name="performance_type">
            <t-select
              v-model="performanceForm.performance_type"
              :options="performanceTypeOptions"
              placeholder="请选择性能类型"
              filterable
            />
          </t-form-item>
          <t-form-item label="性能指标" name="performance_metrics">
            <t-textarea
              v-model="performanceForm.performance_metrics"
              placeholder="请输入性能指标"
              :autosize="{ minRows: 3, maxRows: 6 }"
            />
          </t-form-item>
          <t-form-item label="性能边界值" name="performance_boundary">
            <t-input
              v-model="performanceForm.performance_boundary"
              placeholder="请输入性能边界值"
            />
          </t-form-item>
        </t-form>

        <!-- 故障库导入表单 -->
        <t-form
          v-if="activeTab === 'fault'"
          :data="faultForm"
          :rules="faultImportFormRules"
          label-width="120px"
        >
          <t-form-item label="组件" name="component">
            <t-select
              v-model="faultForm.component"
              :options="componentOptions"
              placeholder="请选择组件"
              filterable
            />
          </t-form-item>
          <t-form-item label="标识" name="identifier">
            <t-input
              v-model="faultForm.identifier"
              placeholder="请输入故障标识"
            />
          </t-form-item>
          <t-form-item label="标题" name="title">
            <t-input
              v-model="faultForm.title"
              placeholder="请输入故障标题"
            />
          </t-form-item>
          <t-form-item label="引入来源" name="source">
            <t-select
              v-model="faultForm.source"
              :options="sourceOptions"
              placeholder="请选择引入来源"
              filterable
            />
          </t-form-item>
          <t-form-item label="故障原因二级分类" name="reason_category">
            <t-select
              v-model="faultForm.reason_category"
              :options="reasonCategoryOptions"
              placeholder="请选择故障原因分类"
              filterable
            />
          </t-form-item>
          <t-form-item label="故障详设链接" name="detail_link">
            <t-input
              v-model="faultForm.detail_link"
              placeholder="请输入故障详设链接"
            />
          </t-form-item>
        </t-form>

      </div>
    </t-dialog>

    <!-- 故障详情抽屉 -->
    <t-drawer
      v-model:visible="faultDetailVisible"
      header="故障详情"
      size="800px"
      :footer="false"
    >
      <div class="fault-detail">
        <div class="detail-header">
          <h3>{{ selectedFault.title }}</h3>
          <div class="detail-meta">
            <t-tag :theme="getStatusTheme(selectedFault.replay_status)" size="small">
              {{ selectedFault.replay_status }}
            </t-tag>
            <span class="detail-date">{{ selectedFault.create_time }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>故障标识</h4>
          <p>{{ selectedFault.identifier }}</p>
        </div>

        <div class="detail-section">
          <h4>故障描述</h4>
          <p>{{ selectedFault.description || '暂无故障描述' }}</p>
        </div>

        <div class="detail-section">
          <h4>引入点复盘状态</h4>
          <p>{{ selectedFault.replay_status }}</p>
        </div>

        <div class="detail-section">
          <h4>团队</h4>
          <p>{{ selectedFault.team }}</p>
        </div>

        <div class="detail-section">
          <h4>引入来源</h4>
          <p>{{ selectedFault.source }}</p>
        </div>

        <div class="detail-section">
          <h4>故障原因二级分类</h4>
          <p>{{ selectedFault.reason_category }}</p>
        </div>

        <div class="detail-section">
          <h4>改进点举措</h4>
          <div class="improvement-measures">{{ selectedFault.improvement_measures }}</div>
        </div>

        <div class="detail-section">
          <h4>拦截点举措</h4>
          <div class="interception-measures">{{ selectedFault.interception_measures }}</div>
        </div>

        <div class="detail-section">
          <h4>故障详设链接</h4>
          <t-link theme="primary" :href="selectedFault.detail_link" target="_blank">
            {{ selectedFault.detail_link }}
          </t-link>
        </div>
      </div>
    </t-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { MessagePlugin } from 'tdesign-vue-next';
import { SearchIcon, RefreshIcon, ArrowLeftIcon, Icon, AddIcon } from 'tdesign-icons-vue-next';
import { useUserStore } from '@/store';
// import { knowledgeApi, faultApi } from '@/api/chatKnowledge';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const user = useUserStore();

// 页面切换状态 - 默认显示场景库
const activeTab = ref('scene'); // 'scene', 'performance', 'fault'

// 添加下拉框选项
const tabOptions = [
  { label: '组件设计场景库', value: 'scene' },
  { label: '组件设计性能库', value: 'performance' },
  { label: '组件设计故障库', value: 'fault' }
];

// 通用筛选状态
const searchText = ref('');

// 场景库相关状态
const scenes = ref([]);
const sceneLoading = ref(false);
const scenePagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
});

// 性能库相关状态
const performance = ref([]);
const performanceLoading = ref(false);
const performancePagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
});

// 故障库相关状态
const faults = ref([]);
const faultLoading = ref(false);
const faultPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
});

// 抽屉和对话框状态
const faultDetailVisible = ref(false);
const editSceneVisible = ref(false);
const editPerformanceVisible = ref(false);
const editFaultVisible = ref(false);
const importDialogVisible = ref(false);
const saving = ref(false);
const importing = ref(false);
const isSceneEditing = ref(false);
const isPerformanceEditing = ref(false);
const isFaultEditing = ref(false);

// 表单数据
const sceneForm = ref({
  component: '',
  function_module: '',
  business_scenario: '',
  related_scenarios: '',
  maintenance_team: '',
  detail_link: ''
});

// 批量导入数据
const batchImportData = ref('');

// 重置导入表单 - 修改为场景库字段
const resetImportForm = () => {
  sceneForm.value = {
    component: '',
    function_module: '',
    business_scenario: '',
    related_scenarios: '',
    maintenance_team: '',
    detail_link: ''
  };
  batchImportData.value = '';
  importForm.value.importType = 'single';
};

const performanceForm = ref({
  component: '',
  performance_type: '',
  performance_metrics: '',
  performance_boundary: '',
});

const faultForm = ref({
  component: '',              // ← 新增
  identifier: '',
  title: '',
  source: '',
  reason_category: '',
  detail_link: ''
});

// 导入表单数据
const importForm = ref({
  importType: 'single', // 'single' 或 'batch'
  singleData: '',
  batchData: ''
});

// 选中的数据
const selectedFault = ref({});

// 表单验证规则
const sceneFormRules = {
  component: [{ required: true, message: '请选择组件', trigger: 'change' }],
  function_module: [{ required: true, message: '请输入功能模块', trigger: 'blur' }],
  business_scenario: [{ required: true, message: '请输入业务场景', trigger: 'blur' }],
  maintenance_team: [{ required: true, message: '请选择维护团队', trigger: 'change' }]
};

const performanceFormRules = {
  component: [{ required: true, message: '请选择组件', trigger: 'change' }],
  performance_type: [{ required: true, message: '请选择性能类型', trigger: 'change' }],
  performance_metrics: [{ required: true, message: '请输入性能指标', trigger: 'blur' }],
  performance_boundary: [{ required: true, message: '请输入性能边界值', trigger: 'blur' }]
};

const faultFormRules = {
  component: [{ required: true, message: '请选择组件', trigger: 'change' }],
  identifier: [{ required: true, message: '请输入标识', trigger: 'blur' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  source: [{ required: true, message: '请选择引入来源', trigger: 'change' }],
  reason_category: [{ required: true, message: '请选择故障原因分类', trigger: 'change' }]
};

// 场景库表格列定义
const sceneColumns = [
  { colKey: 'component', title: '组件', width: 150 },
  { colKey: 'function_module', title: '功能模块', width: 150 },
  { colKey: 'business_scenario', title: '业务场景', width: 200 },
  { colKey: 'related_scenarios', title: '关联场景', width: 150 },
  { colKey: 'maintenance_team', title: '维护团队', width: 120 },
  { colKey: 'detail_link', title: '场景对应详设链接', width: 150 },
  { colKey: 'create_time', title: '创建时间', width: 140 },
  { colKey: 'actions', title: '操作', width: 120, fixed: 'right' }
];

// 性能库表格列定义
const performanceColumns = [
  { colKey: 'component', title: '组件', width: 150 },
  { colKey: 'performance_type', title: '性能类型', width: 120 },
  { colKey: 'performance_metrics', title: '性能指标', width: 200 },
  { colKey: 'performance_boundary', title: '性能边界值', width: 150 },
  { colKey: 'create_time', title: '创建时间', width: 140 },
  { colKey: 'actions', title: '操作', width: 120, fixed: 'right' }
];

// 故障库表格列定义
const faultColumns = [
  { colKey: 'component', title: '组件', width: 150 },
  { colKey: 'identifier', title: '标识', width: 120 },
  { colKey: 'title', title: '标题', width: 200 },
  { colKey: 'source', title: '引入来源', width: 120 },
  { colKey: 'reason_category', title: '故障原因二级分类', width: 180 },
  { colKey: 'detail_link', title: '故障详设链接', width: 180 },
  { colKey: 'create_time', title: '创建时间', width: 140 },
  { colKey: 'actions', title: '操作', width: 120, fixed: 'right' }
];

// 选项数据
const componentOptions = [
  { label: 'L0-WSS', value: 'L0-WSS' },
  { label: 'L0-EDFA', value: 'L0-EDFA' },
  { label: 'L0-DUMMY', value: 'L0-DUMMY' },
  { label: 'L0-OP', value: 'L0-OP' },
  { label: 'L0-OPM', value: 'L0-OPM' },
  { label: '支撑-CPL', value: '支撑-CPL' },
];

const scenarioOptions = [
  { label: '用户登录', value: '用户登录' },
  { label: '数据查询', value: '数据查询' },
  { label: '表单提交', value: '表单提交' },
  { label: '文件上传', value: '文件上传' },
  { label: '权限校验', value: '权限校验' }
];

const teamOptions = [
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
];

const performanceTypeOptions = [
  { label: '时效性', value: '时效性' },
  { label: '吞吐量', value: '吞吐量' },
  { label: '资源利用率', value: '资源利用率' },
  { label: '并发能力', value: '并发能力' }
];

const sourceOptions = [
  { label: '新需求首次发现', value: '新需求首次发现' },
  { label: '老需求首次发现', value: '老需求首次发现' },
  { label: '修改引入', value: '修改引入' },
  { label: '需求未交付', value: '需求未交付' }
];

const replayStatusOptions = [
  { label: '已完成', value: '已完成' },
  { label: '进行中', value: '进行中' },
  { label: '未开始', value: '未开始' }
];

const reasonCategoryOptions = [
  { label: '详细设计-缺少详设', value: '详细设计-缺少详设' },
  { label: '详细设计-详细设计与需求理解不一致', value: '详细设计-详细设计与需求理解不一致' },
  { label: '详细设计-芯片/光模块手册错误', value: '详细设计-芯片/光模块手册错误' },
  { label: '详细设计-详设场景遗漏', value: '详细设计-详设场景遗漏' },
  { label: '详细设计-波及单板遗漏', value: '详细设计-波及单板遗漏' },
  { label: '详细设计-波及场景遗漏', value: '详细设计-波及场景遗漏' },
  { label: '详细设计-业务逻辑问题', value: '详细设计-业务逻辑问题' },
  { label: '详细设计-异常处理问题', value: '详细设计-异常处理问题' },
  { label: '详细设计-消息设计问题', value: '详细设计-消息设计问题' },
  { label: '详细设计-并发设计问题', value: '详细设计-并发设计问题' },
  { label: '详细设计-时序设计问题', value: '详细设计-时序设计问题' },
  { label: '详细设计-兼容性设计问题', value: '详细设计-兼容性设计问题' },
  { label: '详细设计-数据接口设计问题', value: '详细设计-数据接口设计问题' },
  { label: '详细设计-性能设计问题', value: '详细设计-性能设计问题' },
  { label: '详细设计-外部接口调用问题', value: '详细设计-外部接口调用问题' },
  { label: '详细设计-可靠性设计问题', value: '详细设计-可靠性设计问题' },
  { label: '详细设计-其他', value: '详细设计-其他' },
];

// 过滤后的数据
const filteredScenes = computed(() => {
  if (!searchText.value || activeTab.value !== 'scene') {
    return scenes.value;
  }
  const search = searchText.value.toLowerCase();
  return scenes.value.filter(scene =>
    scene.component.toLowerCase().includes(search) ||
    scene.function_module.toLowerCase().includes(search) ||
    scene.business_scenario.toLowerCase().includes(search) ||
    scene.maintenance_team.toLowerCase().includes(search)
  );
});

const filteredPerformance = computed(() => {
  if (!searchText.value || activeTab.value !== 'performance') {
    return performance.value;
  }
  const search = searchText.value.toLowerCase();
  return performance.value.filter(perf =>
    perf.component_name.toLowerCase().includes(search)
  );
});

const filteredFaults = computed(() => {
  if (!searchText.value || activeTab.value !== 'fault') {
    return faults.value;
  }
  const search = searchText.value.toLowerCase();
  return faults.value.filter(fault =>
    fault.identifier.toLowerCase().includes(search) ||
    fault.title.toLowerCase().includes(search) ||
    fault.description.toLowerCase().includes(search)
  );
});

// 获取搜索占位符
const getSearchPlaceholder = () => {
  const placeholders = {
    'scene': '组件、功能模块、业务场景、维护团队',
    'performance': '组件名称',
    'fault': '标识、标题、故障描述'
  };
  return placeholders[activeTab.value] || '搜索内容';
};

// 获取导入标题
const getImportTitle = () => {
  const titles = {
    'scene': '场景',
    'performance': '性能',
    'fault': '故障'
  };
  return titles[activeTab.value] || '场景';
};

// 获取导入占位符
const getImportPlaceholder = () => {
  const placeholders = {
    'scene': '请输入单条场景数据，格式：组件,功能模块,业务场景,关联场景(多个用;分隔),维护团队,详设链接',
    'performance': '请输入单条性能数据，格式：组件,性能类型,性能指标,性能边界值',
    'fault': '请输入单条故障数据，格式：标识,标题,复盘状态,团队,来源,链接,原因分类,改进措施,拦截措施,描述'
  };
  return placeholders[activeTab.value] || '请输入数据内容';
};

// 获取批量导入占位符
const getBatchImportPlaceholder = () => {
  const placeholders = {
    'scene': '请输入批量场景数据，每行一条记录，格式：组件,功能模块,业务场景,关联场景(多个用;分隔),维护团队,详设链接',
    'performance': '请输入批量性能数据，每行一条记录，格式：组件,性能类型,性能指标,性能边界值',
    'fault': '请输入批量故障数据，每行一条记录，格式：标识,标题,复盘状态,团队,来源,链接,原因分类,改进措施,拦截措施,描述'
  };
  return placeholders[activeTab.value] || '请输入批量数据';
};

// 根据标签获取状态主题
const getStatusTheme = (status) => {
  const statusMap = {
    '已完成': 'success',
    '进行中': 'warning',
    '未开始': 'default',
    '已关闭': 'primary'
  };
  return statusMap[status] || 'default';
};

const getPerformanceTypeTheme = (type) => {
  const themeMap = {
    '性能测试': 'primary',
    '压力测试': 'success',
    '负载测试': 'warning'
  };
  return themeMap[type] || 'default';
};

// 获取数据
const getScenes = async () => {
  sceneLoading.value = true;
  try {
        // 这里需要调用后端API获取场景数据
        MessagePlugin.success('开始刷新...');
        // 刷新一次表格
        const response = await fetch(`${SERVER_API_URL}/api_data/API_Scene_get`, {
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
        // 处理关联场景数据
        const scenes_data = response_data.scenes_data || [];
        scenes.value = scenes_data.map(scene => ({
            ...scene,
            related_scenarios: JSON.parse(scene.related_scenarios),
            // 确保 create_time 存在且有值
            create_time: scene.create_time || '未知时间'
        }));
        scenePagination.value.total = scenes.value.length;
  } catch (error) {
    console.error('获取场景数据失败:', error);
  } finally {
    sceneLoading.value = false;
  }
};

const getPerformance = async () => {
  performanceLoading.value = true;
  try {
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Performance_get`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const response_data = await response.json();
    if (response_data.status === 'success') {
      MessagePlugin.success('性能数据加载成功');
      const perfData = response_data.performance_data || [];
      // 注意：后端字段是 component, 不是 component_name
      performance.value = perfData.map(p => ({
        ...p,
        id: p.performance_id, // 用于 row-key
        component: p.component, // 确保字段名一致
      }));
      performancePagination.value.total = performance.value.length;
    } else {
      MessagePlugin.error(response_data.message || '性能数据加载失败');
      performance.value = [];
    }
  } catch (error) {
    console.error('获取性能数据失败:', error);
    MessagePlugin.error('获取性能数据失败');
    performance.value = [];
  } finally {
    performanceLoading.value = false;
  }
};

const getFaults = async () => {
  faultLoading.value = true;
  try {
    const response = await fetch(`${SERVER_API_URL}/api_data/API_Fault_get`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data.status === 'success') {
      MessagePlugin.success('故障数据加载成功');
      faults.value = (data.faults_data || []).map(f => ({
        ...f,
        id: f.fault_id, // 用于 row-key
        // 注意：你新表头需要 component，但当前 API 返回中没有？见下方⚠️说明
      }));
      faultPagination.value.total = faults.value.length;
    } else {
      MessagePlugin.error(data.message || '故障数据加载失败');
      faults.value = [];
    }
  } catch (error) {
    console.error('获取故障数据失败:', error);
    MessagePlugin.error('获取故障数据失败');
    faults.value = [];
  } finally {
    faultLoading.value = false;
  }
};

// 场景库相关操作
const editScene = (scene) => {
  isSceneEditing.value = true;
  sceneForm.value = {
    ...scene,
    // 如果关联场景是数组格式，转换为分号分隔的字符串
    related_scenarios: Array.isArray(scene.related_scenarios)
      ? scene.related_scenarios.join(';')
      : scene.related_scenarios || ''
  };
  editSceneVisible.value = true;
};

const addScene = () => {
  isSceneEditing.value = false;
  sceneForm.value = {
    component: '',
    function_module: '',
    business_scenario: '',
    related_scenarios: '',
    maintenance_team: '',
    detail_link: ''
  };
  editSceneVisible.value = true;
};

const saveScene = async () => {
  saving.value = true;
  try {
        const single_data = sceneForm.value
        console.log("id:" + single_data.scene_id);
        // 单条导入 - 验证必填字段
        if (!single_data.component || !single_data.function_module || !single_data.business_scenario || !single_data.maintenance_team) {
            MessagePlugin.error('请填写必填字段：组件、功能模块、业务场景、维护团队');
            return;
        }
        if(single_data.related_scenarios.includes('；'))
        {
            single_data.related_scenarios = single_data.related_scenarios.replace(/；/g, ';');
        }
        // 处理关联场景数据 - 将英文分号分隔的字符串转换为数组
        const relatedScenariosArray = single_data.related_scenarios
          ? single_data.related_scenarios.split(';').map(s => s.trim()).filter(s => s) : [];
        const response = await fetch(`${SERVER_API_URL}/api_data/API_Scene_update`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  scene_id: single_data.scene_id,
                  component: single_data.component,
                  function_module: single_data.function_module,
                  business_scenario: single_data.business_scenario,
                  related_scenarios: JSON.stringify(relatedScenariosArray), // 传递转换后的数组
                  maintenance_team: single_data.maintenance_team,
                  detail_link: single_data.detail_link
              }),
            });

        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success')
        {
            MessagePlugin.success(isSceneEditing.value ? '场景更新成功' : '场景创建成功');
        }
        else
        {
            MessagePlugin.error(isEditing.value ? (data.message || '场景更新失败') : (data.message || '场景创建失败'));
        }
        editSceneVisible.value = false;
        getScenes();
    } catch (error) {
        console.error('保存场景失败:', error);
    } finally {
        saving.value = false;
    }
};

const deleteScene = async (sceneId) => {
    try {
        console.log('要删除的场景ID:', sceneId);

        const response = await fetch(`${SERVER_API_URL}/api_data/API_Scene_delete`, {
            method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  scene_id: sceneId
              }),
            });

        if (!response.ok)
        {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success')
        {
            MessagePlugin.success('场景删除成功');
        }
        else
        {
            MessagePlugin.error(data.message || '单条场景数据删除失败');
        }
        getScenes();
    }
    catch (error)
    {
        MessagePlugin.error('删除过程异常，请稍后再试');
    }
};

// 性能库相关操作
const editPerformance = (perf) => {
  isPerformanceEditing.value = true;
  performanceForm.value = { ...perf };
  editPerformanceVisible.value = true;
};

const addPerformance = () => {
  isPerformanceEditing.value = false;
  performanceForm.value = {
    component_name: '',
    performance_type: '',
    metrics: {
      response_time: '',
      throughput: '',
      concurrency: '',
      memory_usage: ''
    },
    performance_explanation: ''
  };
  editPerformanceVisible.value = true;
};

const savePerformance = async () => {
  saving.value = true;
  try {
    const dataToSend = {
      component: performanceForm.value.component,
      performance_type: performanceForm.value.performance_type,
      performance_metrics: performanceForm.value.performance_metrics,
      performance_boundary: performanceForm.value.performance_boundary,
      //description: performanceForm.value.description || ''
    };

    // 必填校验（可选，但建议保留）
    if (!dataToSend.component || !dataToSend.performance_type || !dataToSend.performance_metrics || !dataToSend.performance_boundary) {
      MessagePlugin.error('请填写必填字段：组件、性能类型、性能指标、性能边界值');
      saving.value = false;
      return;
    }

    const response = await fetch(`${SERVER_API_URL}/api_data/API_Performance_set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dataToSend)
    });

    const result = await response.json();
    if (result.status === 'success') {
      MessagePlugin.success(isPerformanceEditing.value ? '性能记录更新成功' : '性能记录创建成功');
      editPerformanceVisible.value = false;
      getPerformance(); // 刷新数据
    } else {
      MessagePlugin.error(result.message || '保存失败');
    }
  } catch (error) {
    console.error('保存性能记录失败:', error);
    MessagePlugin.error('保存失败，请稍后重试');
  } finally {
    saving.value = false;
  }
};

const deletePerformance = async (perfId) => {
  try {
    // 这里需要调用后端API删除性能数据
    MessagePlugin.success('性能记录删除成功');
    getPerformance();
  } catch (error) {
    console.error('删除性能记录失败:', error);
  }
};

// 故障库相关操作
const viewFaultDetail = (fault) => {
  selectedFault.value = fault;
  faultDetailVisible.value = true;
};

const editFault = (fault) => {
  isFaultEditing.value = true;
  faultForm.value = { ...fault };
  editFaultVisible.value = true;
};

const addFault = () => {
  isFaultEditing.value = false;
  faultForm.value = {
    identifier: '',
    title: '',
    replay_status: '',
    team: '',
    source: '',
    detail_link: '',
    reason_category: '',
    improvement_measures: '',
    interception_measures: '',
    description: ''
  };
  editFaultVisible.value = true;
};

const saveFault = async () => {
  saving.value = true;
  try {
    const res = await fetch(`${SERVER_API_URL}/api_data/API_Fault_set`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(faultForm.value)
    });
    const data = await res.json();
    if (data.status === 'success') {
      MessagePlugin.success('保存成功');
      editFaultVisible.value = false;
      getFaults();
    }
  } finally {
    saving.value = false;
  }
};

const deleteFault = async (faultId) => {
  try {
    await faultApi.deleteFault({
      id: faultId,
      user: user.userInfo.name
    });

    MessagePlugin.success('故障记录删除成功');
    getFaults();
  } catch (error) {
    console.error('删除故障记录失败:', error);
  }
};

// 手动导入相关操作
const openImportDialog = () => {
  importDialogVisible.value = true;
  resetImportForm();
  importForm.value = {
    importType: 'single',
    singleData: '',
    batchData: ''
  };
};

const importDataManually = async () => {
    importing.value = true;
    try {
        // 根据当前tab进行不同的导入操作
        if (activeTab.value === 'scene') {
            // 场景导入逻辑
            if (importForm.value.importType === 'single') {
                const single_data = sceneForm.value
                 // 单条导入 - 验证必填字段
                if (!single_data.component || !single_data.function_module || !single_data.business_scenario || !single_data.maintenance_team) {
                    MessagePlugin.error('请填写必填字段：组件、功能模块、业务场景、维护团队');
                    importing.value = false;
                    return;
                }
                if(single_data.related_scenarios.includes('；'))
                {
                    single_data.related_scenarios = single_data.related_scenarios.replace(/；/g, ';');
                }
                // 处理关联场景数据 - 将英文分号分隔的字符串转换为数组
                const relatedScenariosArray = single_data.related_scenarios
                  ? single_data.related_scenarios.split(';').map(s => s.trim()).filter(s => s) : [];
                MessagePlugin.loading('正在导入场景数据...');
                try {
                    // 调用场景库的API
                    const response = await fetch(`${SERVER_API_URL}/api_data/API_Scene_set`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            component: single_data.component,
                            function_module: single_data.function_module,
                            business_scenario: single_data.business_scenario,
                            related_scenarios: JSON.stringify(relatedScenariosArray), // 传递转换后的数组
                            maintenance_team: single_data.maintenance_team,
                            detail_link: single_data.detail_link
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    if (data.status === 'success') {
                        MessagePlugin.success('单条场景数据导入成功');
                    } else {
                        MessagePlugin.error(data.message || '单条场景数据导入失败');
                    }
                }
                catch (err) {
                    MessagePlugin.error('导入过程异常，请稍后再试');
                }
            }
            else {
                const lines = importForm.value.batchData.split('\n').filter(line => line.trim());
                const scenesToImport = [];

                for (const line of lines) {
                  // const sceneData = parseSceneData(line);
                  if (sceneData) {
                    scenesToImport.push(sceneData);
                  }
                }

                if (scenesToImport.length > 0) {
                  // 这里需要调用后端API批量保存场景数据
                  MessagePlugin.success(`批量导入成功，共导入 ${scenesToImport.length} 条记录`);
                } else {
                  MessagePlugin.error('没有有效的数据');
                  return;
                }
            }
        }
        else if (activeTab.value === 'performance') {
          // 性能库导入逻辑（单条）
          if (importForm.value.importType === 'single') {
            const perfData = performanceForm.value;
            // 必填字段校验
            if (!perfData.component || !perfData.performance_type || !perfData.performance_metrics) {
              MessagePlugin.error('请填写必填字段：组件、性能类型、性能指标');
              importing.value = false;
              return;
            }

            MessagePlugin.loading('正在导入性能数据...');
            try {
              const response = await fetch(`${SERVER_API_URL}/api_data/API_Performance_set`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  component: perfData.component,
                  performance_type: perfData.performance_type,
                  performance_metrics: perfData.performance_metrics,
                  performance_boundary: perfData.performance_boundary,
                  //description: perfData.description || ''
                })
              });

              const result = await response.json();
              if (result.status === 'success') {
                MessagePlugin.success('单条性能数据导入成功');
              } else {
                MessagePlugin.error(result.message || '性能数据导入失败');
              }
            } catch (err) {
              console.error('性能导入异常:', err);
              MessagePlugin.error('导入过程异常，请稍后再试');
            }
          } else {
            // 批量导入（暂未实现，保留提示或后续扩展）
            MessagePlugin.info('批量导入性能数据功能暂未开放');
            importing.value = false;
            return;
          }
        }
        else if (activeTab.value === 'fault') {
          // 故障库导入逻辑（单条）
          if (importForm.value.importType === 'single') {
            const faultData = faultForm.value;
            if (!faultData.component || !faultData.identifier || !faultData.title ||
                !faultData.source || !faultData.reason_category) {
              MessagePlugin.error('请填写必填字段：组件、标识、标题、引入来源、故障原因二级分类');
              importing.value = false;
              return;
            }

            MessagePlugin.loading('正在导入故障数据...');
            try {
              const response = await fetch(`${SERVER_API_URL}/api_data/API_Fault_set`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  component: faultData.component,
                  identifier: faultData.identifier,
                  title: faultData.title,
                  replay_status: faultData.replay_status,
                  team: faultData.team,
                  source: faultData.source,
                  detail_link: faultData.detail_link,
                  reason_category: faultData.reason_category,
                  improvement_measures: faultData.improvement_measures,
                  interception_measures: faultData.interception_measures,
                  //description: faultData.description
                })
              });
              const result = await response.json();
              if (result.status === 'success') {
                MessagePlugin.success('单条故障数据导入成功');
              } else {
                MessagePlugin.error(result.message || '导入失败');
              }
            } catch (err) {
              console.error('故障导入异常:', err);
              MessagePlugin.error('导入过程异常');
            }
          } else {
            MessagePlugin.info('批量导入功能暂未开放');
            importing.value = false;
            return;
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

// 解析故障数据
const parseFaultData = (line) => {
  try {
    const parts = line.split(',').map(part => part.trim());
    if (parts.length < 10) {
      return null; // 数据不完整
    }

    return {
      identifier: parts[0],
      title: parts[1],
      replay_status: parts[2],
      team: parts[3],
      source: parts[4],
      detail_link: parts[5],
      reason_category: parts[6],
      improvement_measures: parts[7],
      interception_measures: parts[8],
      description: parts[9]
    };
  } catch (error) {
    console.error('解析故障数据失败:', error);
    return null;
  }
};

// 刷新数据
const refreshData = () => {
  if (activeTab.value === 'scene') {
    getScenes();
  } else if (activeTab.value === 'performance') {
    getPerformance();
  } else {
    getFaults();
  }
};

// 返回聊天页面
const goBack = () => {
  router.go(-1);
};

onMounted(() => {
  // 初始加载场景库数据
  getScenes();
});
</script>

<style scoped>
.design-knowledge-base {
  padding: 24px;
  height: 100%;
  background-color: #f5f5f5;
}

.knowledge-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
}

.knowledge-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.component-name {
  font-weight: 500;
  color: #333;
}

.function-module {
  color: #666;
}

.business-scenario {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.related-scenarios {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.maintenance-team {
  color: #0052d9;
  font-weight: 500;
}

.create-time {
  color: #999;
  font-size: 12px;
}

.identifier {
  font-weight: bold;
  color: #0052d9;
}

.fault-title {
  font-weight: 500;
  color: #333;
}

.team-name {
  color: #666;
}

.source {
  color: #666;
}

.reason-category {
  color: #666;
  font-size: 12px;
}

.improvement-measures,
.interception-measures {
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.performance-metrics {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.performance-boundary {
  font-weight: 500;
  color: #0052d9;
}
.metric-item {
  margin-bottom: 4px;
}

.metric-label {
  font-weight: bold;
  margin-right: 8px;
}

.metric-value {
  color: #0052d9;
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

.fault-detail {
  height: 100%;
  overflow-y: auto;
}

.improvement-measures,
.interception-measures {
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>
