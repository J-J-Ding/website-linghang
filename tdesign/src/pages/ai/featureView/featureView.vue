<template>
  <div class="feature-view-main">
    <t-space direction="vertical" style="width: 100%">
      <!-- 筛选区域 -->
      <t-space :size="16" style="flex-wrap: wrap">
        <t-select
          v-model="queryParams.domain"
          placeholder="请选择领域"
          clearable
          style="width: 300px"
          label="领域: "
          :options="domainOptions"
          filterable
        />
        <t-select
          v-model="queryParams.team"
          placeholder="请选择团队"
          clearable
          multiple
          style="width: 300px"
          label="团队: "
          :options="teamOptions"
          filterable
        />
      </t-space>

      <!-- 按钮区域 -->
      <t-space style="justify-content: flex-start; margin-bottom: 16px">
        <t-button @click="handleQuery">查询</t-button>
        <t-button @click="handleResetFilter">重置</t-button>
        <t-button @click="openAddDialog">新建</t-button>
        <t-button @click="onBatchImport">批量导入</t-button>
        <t-button @click="onBatchExport">批量导出</t-button>
        <t-button theme="primary" :loading="saving" @click="onBatchSave">保存修改</t-button>
        <t-button @click="onExpandAllToggle">{{ expandAll ? '收起全部' : '展开全部' }}</t-button>
        <t-button theme="danger" @click="handleDeleteByDomainTeam">按条件删除</t-button>
      </t-space>
    </t-space>

    <t-enhanced-table
      ref="tableRef"
      row-key="id"
      :columns="tableColumnList"
      :data="tableDataList"
      :bordered="true"
      :hover="true"
      resizable
      :loading="loading"
      :max-height="tableHeight"
      :tree="treeConfig"
      @cell-edit="onCellEdit"
      @expanded-tree-nodes-change="onExpandedTreeNodesChange"
    />

    <!-- 新增/编辑对话框 -->
    <t-dialog v-model:visible="dialogVisible" :width="650" :header="dialogTitle">
      <div class="dialog-form">
        <t-form ref="formRef" :data="formData" layout="vertical">
          <t-form-item label="特性一级分类" name="feature_first_classification">
            <t-select
              v-model="formData.feature_first_classification"
              placeholder="请选择特性一级分类"
              clearable
              filterable
              @change="handleFeatureFirstTypeChange"
            >
              <t-option v-for="opt in allFeatureFirstTypeOptionList" :key="opt" :value="opt" :label="opt" />
            </t-select>
          </t-form-item>
          <t-form-item label="特性二级分类" name="feature_second_classification">
            <t-select
              v-model="formData.feature_second_classification"
              placeholder="请选择特性二级分类"
              clearable
              filterable
              :disabled="!formData.feature_first_classification"
              @change="handleFeatureSecondTypeChange"
            >
              <t-option v-for="opt in allFeatureSecondTypeOptionList" :key="opt" :value="opt" :label="opt" />
            </t-select>
          </t-form-item>
          <t-form-item label="特性" name="feature_name">
            <t-select
              v-model="formData.feature_name"
              placeholder="请选择特性"
              clearable
              filterable
              :disabled="!formData.feature_second_classification"
              @change="handleFeatureChange"
            >
              <t-option v-for="opt in allFeatureOptionList" :key="opt" :value="opt" :label="opt" />
            </t-select>
          </t-form-item>
          <t-form-item label="子特性" name="sub_feature_name">
            <t-select
              v-model="formData.sub_feature_name"
              placeholder="请选择子特性"
              clearable
              filterable
              :disabled="!formData.feature_name"
            >
              <t-option v-for="opt in allSubFeatureOptionList" :key="opt" :value="opt" :label="opt" />
            </t-select>
          </t-form-item>
          <t-form-item label="特性标识" name="feature_identifier">
            <t-input v-model="formData.feature_identifier" placeholder="请输入特性标识" />
          </t-form-item>
          <t-form-item label="领域" name="domain">
            <t-input v-model="formData.domain" placeholder="请输入领域" />
          </t-form-item>
          <t-form-item label="团队" name="team">
            <t-input v-model="formData.team" placeholder="请输入团队" />
          </t-form-item>
          <t-form-item label="验证方式" name="verification_mode">
            <t-input v-model="formData.verification_mode" placeholder="请输入验证方式" />
          </t-form-item>
          <t-form-item label="验证团队" name="verification_team">
            <t-input v-model="formData.verification_team" placeholder="请输入验证团队" />
          </t-form-item>
          <t-form-item label="优先级" name="priority">
            <t-input v-model="formData.priority" placeholder="请输入优先级" />
          </t-form-item>
          <t-form-item label="开发工作量（人天）" name="dev_workload">
            <t-input-number v-model="formData.dev_workload" :min="0" :step="0.5" style="width: 100%" />
          </t-form-item>
          <t-form-item label="详设工作量（人天）" name="detail_workload">
            <t-input-number v-model="formData.detail_workload" :min="0" :step="0.5" style="width: 100%" />
          </t-form-item>
          <t-form-item label="预计开发工作量" name="estimated_dev_workload">
            <t-input-number v-model="formData.estimated_dev_workload" :min="0" :step="0.5" style="width: 100%" />
          </t-form-item>
          <t-form-item label="预计验证工作量" name="estimated_verification_workload">
            <t-input-number v-model="formData.estimated_verification_workload" :min="0" :step="0.5" style="width: 100%" />
          </t-form-item>
          <t-form-item label="预计系统测试工作量" name="estimated_system_test_workload">
            <t-input-number v-model="formData.estimated_system_test_workload" :min="0" :step="0.5" style="width: 100%" />
          </t-form-item>
        </t-form>
      </div>
      <template #footer>
        <t-button @click="handleCancel">取消</t-button>
        <t-button :loading="saving" @click="handleSave">确认</t-button>
      </template>
    </t-dialog>

    <!-- 删除确认对话框 -->
    <t-dialog v-model:visible="deleteDialogVisible" :width="400" header="删除确认">
      <p>确定要删除选中的记录吗？</p>
      <template #footer>
        <t-button @click="deleteDialogVisible = false">取消</t-button>
        <t-button theme="danger" :loading="deleting" @click="handleConfirmDelete">确认删除</t-button>
      </template>
    </t-dialog>

    <!-- 按领域/团队删除确认对话框 -->
    <t-dialog v-model:visible="deleteByDomainTeamDialogVisible" :width="500" header="按条件删除确认">
      <div class="delete-confirm-content">
        <p>删除条件：</p>
        <p v-if="queryParams.domain">领域：{{ queryParams.domain }}</p>
        <p v-if="queryParams.team && queryParams.team.length > 0">团队：{{ queryParams.team.join(', ') }}</p>
        <p class="delete-count">符合条件的记录数量：<strong>{{ deleteByDomainTeamCount }}</strong> 条</p>
        <p class="delete-warning">确定要删除以上数据吗？此操作不可恢复！</p>
      </div>
      <template #footer>
        <t-button @click="deleteByDomainTeamDialogVisible = false">取消</t-button>
        <t-button theme="danger" :loading="deletingByDomainTeam" @click="handleConfirmDeleteByDomainTeam">确认删除</t-button>
      </template>
    </t-dialog>

    <!-- 批量导入对话框 -->
    <t-dialog v-model:visible="importDialogVisible" :width="600" header="批量导入特性视图">
      <div class="import-container">
        <t-upload
          ref="uploadRef"
          :key="uploadKey"
          v-model="fileList"
          :auto-upload="false"
          :max="1"
          accept=".xlsx"
          :on-change="handleFileChange"
        >
          <template #trigger>
            <t-button>
              <t-icon name="upload" />
              选择文件
            </t-button>
          </template>
        </t-upload>
        <div v-if="fileList.length > 0" class="file-info">
          <p>已选择文件: {{ fileList[0].name }}</p>
          <p class="file-size">文件大小: {{ formatFileSize(fileList[0].size) }}</p>
        </div>
        <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
      </div>
      <template #footer>
        <t-button @click="cancelImportSubmit">取消</t-button>
        <t-button :loading="importLoading" @click="handleImportSubmit">确认导入</t-button>
      </template>
    </t-dialog>
  </div>
</template>

<script setup lang="jsx">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import {
  queryFeatureViewByParams,
  createFeatureView,
  updateFeatureView,
  deleteFeatureView,
  getFeatureViewOptions,
  importFeatureView,
  exportFeatureView,
  countFeatureViewByDomainTeam,
  deleteFeatureViewByDomainTeam,
  queryFeatureTreeFeatureFirstTypeList,
  queryFeatureTreeFeatureSecondTypeList,
  queryFeatureTreeFeatureList,
  queryFeatureTreeSubFeatureList,
} from '@/api/featureView.js';

const user = useUserStore();

const tableRef = ref();
const loading = ref(false);
const saving = ref(false);
const deleting = ref(false);

const tableHeight = ref(400);
const calculateTableHeight = () => {
  tableHeight.value = pubCalculateTableHeight(240);
};

const queryParams = ref({ domain: '', team: [] });
const domainOptions = ref([]);
const teamOptions = ref([]);

const tableDataList = ref([]);
const editedMap = ref(new Map()); // id -> partial row
const allFeatureFirstTypeOptionList = ref([]);
const allFeatureSecondTypeOptionList = ref([]);
const allFeatureOptionList = ref([]);
const allSubFeatureOptionList = ref([]);

const expandedRowKeys = ref([]);
const expandAll = ref(false);

const normalizeTreeData = (rows) => {
  if (!Array.isArray(rows) || rows.length === 0) return [];
  const hasTree = rows.some((item) => Array.isArray(item?.childrenList) && item.childrenList.length > 0);
  if (hasTree) return rows;

  const parentMap = new Map();
  const orphans = [];
  const latestFeatureByClass = new Map();

  rows.forEach((row) => {
    const f1 = row.feature_first_classification || '';
    const f2 = row.feature_second_classification || '';
    const feature = row.feature_name || '';
    const sub = row.sub_feature_name || '';
    if (!sub && feature) {
      parentMap.set(`${f1}__${f2}__${feature}`, { ...row, parent: true, childrenList: [] });
      latestFeatureByClass.set(`${f1}__${f2}`, feature);
    }
  });

  rows.forEach((row) => {
    const f1 = row.feature_first_classification || '';
    const f2 = row.feature_second_classification || '';
    const feature = row.feature_name || '';
    const sub = row.sub_feature_name || '';
    if (feature) latestFeatureByClass.set(`${f1}__${f2}`, feature);
    if (!sub) return;

    const inferredFeature = feature || latestFeatureByClass.get(`${f1}__${f2}`) || '';
    if (!inferredFeature) {
      orphans.push({ ...row, parent: false, childrenList: [] });
      return;
    }
    const parentKey = `${f1}__${f2}__${inferredFeature}`;
    if (!parentMap.has(parentKey)) {
      parentMap.set(parentKey, {
        id: null,
        feature_first_classification: f1,
        feature_second_classification: f2,
        feature_name: inferredFeature,
        sub_feature_name: '',
        parent: true,
        childrenList: [],
      });
    }
    parentMap.get(parentKey).childrenList.push({
      ...row,
      parent: false,
      feature_first_classification: f1,
      feature_second_classification: f2,
      feature_name: inferredFeature,
      feature_first_classification_bak: f1,
      feature_second_classification_bak: f2,
      feature_name_bak: inferredFeature,
    });
  });

  return [...parentMap.values(), ...orphans];
};

const preprocessTree = (nodes) => {
  let counter = 0;
  const walk = (list) => {
    list.forEach((node) => {
      if (node.id == null) node.id = `vp_${counter++}_${node.feature_name || ''}`;
      if (Array.isArray(node.childrenList) && node.childrenList.length > 0) {
        walk(node.childrenList);
      }
    });
  };
  walk(nodes);
};

const treeConfig = computed(() => ({
  childrenKey: 'childrenList',
  treeNodeColumnIndex: 2,
  checkStrictly: true,
  expandedRowKeys: expandedRowKeys.value,
}));

const onExpandAllToggle = () => {
  expandAll.value = !expandAll.value;
  if (expandAll.value) {
    tableRef.value?.expandAll();
  } else {
    tableRef.value?.foldAll();
  }
};

const onExpandedTreeNodesChange = (expandedTreeNodes) => {
  const uniqueKeys = Array.from(new Set(expandedTreeNodes || []));
  expandedRowKeys.value = uniqueKeys;
  expandAll.value = uniqueKeys.length > 0;
};

const tableColumnList = [
  { colKey: 'feature_first_classification', title: '特性一级分类', width: '140', align: 'left' },
  { colKey: 'feature_second_classification', title: '特性二级分类', width: '140', align: 'left' },
  { colKey: 'feature_name', title: '特性', width: '200', align: 'left' },
  { colKey: 'sub_feature_name', title: '子特性', width: '200', align: 'left' },
  { colKey: 'feature_identifier', title: '特性标识', width: '120', align: 'left' },
  { colKey: 'domain', title: '领域', width: '120', align: 'left' },
  { colKey: 'team', title: '团队', width: '120', align: 'left' },
  { colKey: 'verification_mode', title: '验证方式', width: '120', align: 'left' },
  { colKey: 'verification_team', title: '验证团队', width: '120', align: 'left' },
  { colKey: 'priority', title: '优先级', width: '80', align: 'left' },
  { colKey: 'dev_workload', title: '开发工作量（人天）', width: '140', align: 'right' },
  { colKey: 'detail_workload', title: '详设工作量（人天）', width: '140', align: 'right' },
  { colKey: 'estimated_dev_workload', title: '预计开发工作量', width: '140', align: 'right' },
  { colKey: 'estimated_verification_workload', title: '预计验证工作量', width: '140', align: 'right' },
  { colKey: 'estimated_system_test_workload', title: '预计系统测试工作量', width: '160', align: 'right' },
  {
    colKey: 'operation',
    title: '操作',
    width: '110',
    align: 'center',
    fixed: 'right',
    cell: (_, { row }) => (
      <t-space>
        <t-link theme="primary" hover="color" onClick={() => handleEdit(row)}>
          编辑
        </t-link>
        <t-link theme="danger" hover="color" onClick={() => handleDelete(row)}>
          删除
        </t-link>
      </t-space>
    ),
  },
];

const loadOptions = async () => {
  const d = await getFeatureViewOptions({ option_type: 'domain' });
  if (d.code === 200) domainOptions.value = (d.data || []).map((x) => ({ label: x, value: x }));
  const t = await getFeatureViewOptions({ option_type: 'team' });
  if (t.code === 200) teamOptions.value = (t.data || []).map((x) => ({ label: x, value: x }));
};

const loadData = async () => {
  loading.value = true;
  try {
    const params = {};
    if (queryParams.value.domain) params.domain = queryParams.value.domain;
    if (queryParams.value.team && queryParams.value.team.length > 0) params.team = queryParams.value.team;
    const res = await queryFeatureViewByParams(params);
    if (res.code === 200) {
      const treeRows = normalizeTreeData(res.data || []);
      preprocessTree(treeRows);
      tableDataList.value = treeRows;
      expandedRowKeys.value = [];
      expandAll.value = false;
      editedMap.value = new Map();
    } else {
      MessagePlugin.error(res.message || '查询失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('查询失败');
  } finally {
    loading.value = false;
  }
};

const handleQuery = async () => {
  await loadData();
};
const handleResetFilter = async () => {
  queryParams.value = { domain: '', team: [] };
  await loadData();
};

// cell edit (记录修改)
const onCellEdit = (context) => {
  const { row, col, value } = context;
  if (!row || !row.id) return;
  const key = col.colKey;
  const patch = editedMap.value.get(row.id) || {};
  patch[key] = value;
  editedMap.value.set(row.id, patch);
};

const onBatchSave = async () => {
  if (editedMap.value.size === 0) {
    MessagePlugin.info('没有需要保存的修改');
    return;
  }
  saving.value = true;
  try {
    const payload = [];
    editedMap.value.forEach((patch, id) => payload.push({ id, ...patch }));
    const res = await updateFeatureView({ data: payload, operator_person: user?.userInfo?.employNo || '' });
    if (res.code === 200) {
      MessagePlugin.success(res.message || '保存成功');
      await loadOptions();
      await loadData();
    } else {
      MessagePlugin.error(res.message || '保存失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// dialog add/edit
const dialogVisible = ref(false);
const dialogTitle = ref('新建');
const formRef = ref();
const formData = ref({
  id: null,
  feature_first_classification: '',
  feature_second_classification: '',
  feature_name: '',
  sub_feature_name: '',
  feature_identifier: '',
  domain: '',
  team: '',
  verification_mode: '',
  verification_team: '',
  priority: '',
  dev_workload: null,
  detail_workload: null,
  estimated_dev_workload: null,
  estimated_verification_workload: null,
  estimated_system_test_workload: null,
});

const openAddDialog = () => {
  dialogTitle.value = '新建';
  formData.value = {
    id: null,
    feature_first_classification: '',
    feature_second_classification: '',
    feature_name: '',
    sub_feature_name: '',
    feature_identifier: '',
    domain: '',
    team: '',
    verification_mode: '',
    verification_team: '',
    priority: '',
    dev_workload: null,
    detail_workload: null,
    estimated_dev_workload: null,
    estimated_verification_workload: null,
    estimated_system_test_workload: null,
  };
  allFeatureSecondTypeOptionList.value = [];
  allFeatureOptionList.value = [];
  allSubFeatureOptionList.value = [];
  queryFeatureTreeFeatureFirstTypeList()
    .then((res) => {
      allFeatureFirstTypeOptionList.value = res.data || [];
    })
    .catch(() => {
      allFeatureFirstTypeOptionList.value = [];
    });
  dialogVisible.value = true;
};

const handleEdit = async (row) => {
  dialogTitle.value = '编辑';
  formData.value = { ...row };
  try {
    const r1 = await queryFeatureTreeFeatureFirstTypeList();
    allFeatureFirstTypeOptionList.value = r1.data || [];
    if (row.feature_first_classification) {
      const r2 = await queryFeatureTreeFeatureSecondTypeList({ featureFirstType: row.feature_first_classification });
      allFeatureSecondTypeOptionList.value = r2.data || [];
    } else {
      allFeatureSecondTypeOptionList.value = [];
    }
    if (row.feature_second_classification) {
      const r3 = await queryFeatureTreeFeatureList({
        featureFirstType: row.feature_first_classification,
        featureSecondType: row.feature_second_classification,
      });
      allFeatureOptionList.value = r3.data || [];
    } else {
      allFeatureOptionList.value = [];
    }
    if (row.feature_name) {
      const r4 = await queryFeatureTreeSubFeatureList({
        featureFirstType: row.feature_first_classification,
        featureSecondType: row.feature_second_classification,
        feature: row.feature_name,
      });
      allSubFeatureOptionList.value = r4.data || [];
    } else {
      allSubFeatureOptionList.value = [];
    }
  } catch (e) {
    allFeatureFirstTypeOptionList.value = [];
    allFeatureSecondTypeOptionList.value = [];
    allFeatureOptionList.value = [];
    allSubFeatureOptionList.value = [];
  }
  dialogVisible.value = true;
};

const handleFeatureFirstTypeChange = async () => {
  formData.value.feature_second_classification = '';
  formData.value.feature_name = '';
  formData.value.sub_feature_name = '';
  allFeatureSecondTypeOptionList.value = [];
  allFeatureOptionList.value = [];
  allSubFeatureOptionList.value = [];
  if (!formData.value.feature_first_classification) return;
  try {
    const res = await queryFeatureTreeFeatureSecondTypeList({
      featureFirstType: formData.value.feature_first_classification,
    });
    allFeatureSecondTypeOptionList.value = res.data || [];
  } catch (e) {
    allFeatureSecondTypeOptionList.value = [];
  }
};

const handleFeatureSecondTypeChange = async () => {
  formData.value.feature_name = '';
  formData.value.sub_feature_name = '';
  allFeatureOptionList.value = [];
  allSubFeatureOptionList.value = [];
  if (!formData.value.feature_second_classification) return;
  try {
    const res = await queryFeatureTreeFeatureList({
      featureFirstType: formData.value.feature_first_classification,
      featureSecondType: formData.value.feature_second_classification,
    });
    allFeatureOptionList.value = res.data || [];
  } catch (e) {
    allFeatureOptionList.value = [];
  }
};

const handleFeatureChange = async () => {
  formData.value.sub_feature_name = '';
  allSubFeatureOptionList.value = [];
  if (!formData.value.feature_name) return;
  try {
    const res = await queryFeatureTreeSubFeatureList({
      featureFirstType: formData.value.feature_first_classification,
      featureSecondType: formData.value.feature_second_classification,
      feature: formData.value.feature_name,
    });
    allSubFeatureOptionList.value = res.data || [];
  } catch (e) {
    allSubFeatureOptionList.value = [];
  }
};

const handleCancel = () => {
  dialogVisible.value = false;
};

const handleSave = async () => {
  saving.value = true;
  try {
    const payload = { ...formData.value, operator_person: user?.userInfo?.employNo || '' };
    const res = payload.id ? await updateFeatureView({ data: [payload] }) : await createFeatureView(payload);
    if (res.code === 200) {
      MessagePlugin.success(res.message || '保存成功');
      dialogVisible.value = false;
      await loadOptions();
      await loadData();
    } else {
      MessagePlugin.error(res.message || '保存失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// delete
const deleteDialogVisible = ref(false);
const deleteTargetId = ref(null);
const handleDelete = (row) => {
  deleteTargetId.value = row.id;
  deleteDialogVisible.value = true;
};
const handleConfirmDelete = async () => {
  deleting.value = true;
  try {
    const res = await deleteFeatureView({ ids: [deleteTargetId.value] });
    if (res.code === 200) {
      MessagePlugin.success(res.message || '删除成功');
      deleteDialogVisible.value = false;
      await loadOptions();
      await loadData();
    } else {
      MessagePlugin.error(res.message || '删除失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('删除失败');
  } finally {
    deleting.value = false;
  }
};

// 按领域/团队删除
const deleteByDomainTeamDialogVisible = ref(false);
const deleteByDomainTeamCount = ref(0);
const deletingByDomainTeam = ref(false);

const handleDeleteByDomainTeam = async () => {
  const { domain } = queryParams.value;
  const team = queryParams.value.team;
  if (!domain && (!team || team.length === 0)) {
    MessagePlugin.warning('请先选择领域或团队作为删除条件');
    return;
  }
  try {
    const params = {};
    if (domain) params.domain = domain;
    if (team && team.length === 1) params.team = team[0];
    const res = await countFeatureViewByDomainTeam(params);
    if (res.code === 200) {
      deleteByDomainTeamCount.value = res.data?.count || 0;
      if (deleteByDomainTeamCount.value === 0) {
        MessagePlugin.info('没有符合条件的数据');
        return;
      }
      deleteByDomainTeamDialogVisible.value = true;
    } else {
      MessagePlugin.error(res.message || '查询失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('查询失败');
  }
};

const handleConfirmDeleteByDomainTeam = async () => {
  deletingByDomainTeam.value = true;
  try {
    const { domain } = queryParams.value;
    const team = queryParams.value.team;
    const payload = {};
    if (domain) payload.domain = domain;
    if (team && team.length === 1) payload.team = team[0];
    const res = await deleteFeatureViewByDomainTeam(payload);
    if (res.code === 200) {
      MessagePlugin.success(res.message || '删除成功');
      deleteByDomainTeamDialogVisible.value = false;
      await loadOptions();
      await loadData();
    } else {
      MessagePlugin.error(res.message || '删除失败');
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('删除失败');
  } finally {
    deletingByDomainTeam.value = false;
  }
};

// import/export
const importDialogVisible = ref(false);
const uploadRef = ref();
const uploadKey = ref(0);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

const onBatchImport = () => {
  fileList.value = [];
  uploadError.value = '';
  importDialogVisible.value = true;
};

const handleFileChange = (files) => {
  uploadError.value = '';
  fileList.value = files;
  if (files.length > 0) {
    const name = (files[0].name || '').toLowerCase();
    if (!name.endsWith('.xlsx')) {
      uploadError.value = '文件格式错误，请选择.xlsx文件';
      fileList.value = [];
    }
  }
};

const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const cancelImportSubmit = () => {
  uploadKey.value += 1;
  importDialogVisible.value = false;
};

const handleImportSubmit = async () => {
  if (fileList.value.length === 0) {
    uploadError.value = '请先选择文件';
    return;
  }
  importLoading.value = true;
  try {
    const form = new FormData();
    form.append('file', fileList.value[0].raw);
    const res = await importFeatureView(form);
    if (res.code === 200) {
      MessagePlugin.success(res.message || '导入成功');
      importDialogVisible.value = false;
      await loadOptions();
      await loadData();
    } else {
      uploadError.value = res.message || '导入失败';
    }
  } catch (e) {
    console.error(e);
    uploadError.value = e.message || '导入失败';
  } finally {
    importLoading.value = false;
    uploadKey.value += 1;
  }
};

const onBatchExport = async () => {
  try {
    const params = {};
    if (queryParams.value.domain) params.domain = queryParams.value.domain;
    if (queryParams.value.team && queryParams.value.team.length > 0) params.team = queryParams.value.team;
    const res = await exportFeatureView(params);
    if (res instanceof Blob) {
      const url = window.URL.createObjectURL(res);
      const link = document.createElement('a');
      link.href = url;
      link.download = `特性视图导出_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      MessagePlugin.success('导出成功');
    } else {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const result = JSON.parse(reader.result);
          MessagePlugin.error(result.message || '导出失败');
        } catch (e) {
          MessagePlugin.error('导出失败');
        }
      };
      reader.readAsText(res);
    }
  } catch (e) {
    console.error(e);
    MessagePlugin.error('导出失败');
  }
};

onMounted(async () => {
  calculateTableHeight();
  window.addEventListener('resize', calculateTableHeight);
  await loadOptions();
  await loadData();
});
onBeforeUnmount(() => {
  window.removeEventListener('resize', calculateTableHeight);
});
</script>

<style scoped>
.feature-view-main {
  padding: 16px;
}
.dialog-form {
  padding: 12px 0;
}
.import-container {
  padding: 16px 0;
}
.file-info {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-top: 12px;
}
.file-size {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}
.error-message {
  color: #ff4d4f;
  padding: 8px 0;
  min-height: 24px;
}
.delete-confirm-content {
  padding: 8px 0;
}
.delete-confirm-content p {
  margin: 8px 0;
}
.delete-count {
  font-size: 16px;
  color: #333;
}
.delete-count strong {
  color: #ff4d4f;
  font-size: 18px;
}
.delete-warning {
  color: #ff4d4f;
  font-weight: 500;
  margin-top: 16px !important;
}
</style>

