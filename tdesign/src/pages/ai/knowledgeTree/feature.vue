<template>
  <div class="feature-main">
    <t-space direction="vertical" style="width: 100%">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <t-space>
          <t-button shape="circle" variant="base" theme="primary" @click="onTableAiChat"> AI </t-button>
          <t-select v-model="field" :options="fieldOptions" placeholder="请选择领域" clearable> </t-select>
          <t-select v-model="board" :options="boardOptions" placeholder="请选择单板" clearable> </t-select>
          <t-button @click="onTableRead">读取</t-button>
          <t-button @click="toggleAllExpanded">{{ allExpanded ? '收起所有' : '展开所有' }}</t-button>
          <!-- <t-button @click="onTableWrite">写入</t-button -->

          <!-- <t-button @click="setLowerHeight">lower height</t-button> -->
          <!-- <t-button @click="setHigherHeight">higher height</t-button> -->
        </t-space>
        <t-tooltip content="特性方案完成度(%) = 特性方案页面链接数 / 总特性数" placement="left">
          <t-tag size="large" :theme="getCompletionTheme(featureDesignCompletionRate.rate)" variant="light-outline">
            特性设计完成度: {{ featureDesignCompletionRate.completed }}/{{ featureDesignCompletionRate.total }} ({{
              featureDesignCompletionRate.rate
            }}%)
          </t-tag>
        </t-tooltip>
      </div>

      <t-enhanced-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="treeData"
        :editable-row-keys="editableRowKeys"
        :fixed-rows="[0, 0]"
        :maxHeight="650"
        :loading="tableLoading"
        :tree="{
          childrenKey: 'children',
          treeNodeColumnIndex: 1,
          expandTreeNodeOnClick: false,
          defaultExpandAll: false,
        }"
        @row-edit="onRowEdit"
      />
    </t-space>

    <AiChat
      :visible="drawVisible"
      :ai-chat-title="tableAiTitle"
      :ai-chat-context="tableAiContext"
      @update:visible="drawVisible = $event"
    />

    <!-- 新的行级AI实例 - 响应表格行的AI助手按钮 -->
    <AiChat
      :visible="rowAiVisible"
      :ai-chat-title="rowAiTitle"
      :ai-chat-context="rowAiContext"
      @update:visible="rowAiVisible = $event"
    />

    <!-- 编辑对话框 -->
    <t-dialog v-model:visible="diagVisible" header="编辑特性信息" :footer="false" width="30%" destroy-on-close>
      <t-form
        v-if="currentEditRow"
        :data="currentEditRow"
        :label-width="120"
        reset-type="empty"
        layout="vertical"
        @submit="onEditSubmit"
      >
        <t-form-item label="特性编号" name="feature_id">
          <t-input v-model="currentEditRow.feature_id" placeholder="请输入特性编号" />
        </t-form-item>
        <t-form-item label="特性名称" name="feature_name">
          <t-input v-model="currentEditRow.feature_name" placeholder="请输入特性名称" />
        </t-form-item>
        <t-form-item label="特性功能" name="feature_function">
          <t-input v-model="currentEditRow.feature_function" placeholder="请输入特性功能" />
        </t-form-item>
        <t-form-item label="特性设计" name="feature_page">
          <t-input v-model="currentEditRow.feature_page" placeholder="请输入特性设计链接" />
        </t-form-item>
        <t-form-item label="特性等级" name="feature_level">
          <t-select v-model="currentEditRow.feature_level" placeholder="请选择特性等级">
            <t-option value="一级特性">一级特性</t-option>
            <t-option value="二级特性">二级特性</t-option>
            <t-option value="三级特性">三级特性</t-option>
          </t-select>
        </t-form-item>
        <t-form-item label="组件" name="component">
          <t-input v-model="currentEditRow.component" placeholder="请输入组件" />
        </t-form-item>
        <t-form-item label="单板" name="board">
          <t-input v-model="currentEditRow.board" placeholder="请输入单板" />
        </t-form-item>
        <t-form-item label="需求" name="requirement">
          <t-input v-model="currentEditRow.requirement" placeholder="请输入需求" />
        </t-form-item>
        <t-form-item label="用例" name="testcase">
          <t-input v-model="currentEditRow.testcase" placeholder="请输入用例" />
        </t-form-item>
        <t-form-item label="接口" name="api">
          <t-input v-model="currentEditRow.api" placeholder="请输入接口" />
        </t-form-item>
        <t-form-item label="评审状态" name="review_status">
          <t-select v-model="currentEditRow.review_status" placeholder="请选择评审状态">
            <t-option value="通过">通过</t-option>
            <t-option value="不通过">不通过</t-option>
          </t-select>
        </t-form-item>
        <div class="dialog-footer">
          <t-button variant="outline" @click="diagVisible = false">取消</t-button>
          <t-button theme="primary" type="submit">保存</t-button>
        </div>
      </t-form>
    </t-dialog>

    <t-dialog
      v-model:visible="issueDiagVisible"
      header="关联的故障复盘列表"
      :footer="false"
      width="80%"
      destroy-on-close
    >
      <t-table :data="dialogReviewData" :columns="diagReviewColumns" max-height="500" row-key="标识" bordered />
    </t-dialog>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import { ref, onMounted, watch, computed } from 'vue';
import { Input, Select, DatePicker, MessagePlugin } from 'tdesign-vue-next';

import AiChat from '@/pages/ai/chat/chat.vue';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

const aiChatRef = ref(null);
const drawVisible = ref(false);
const tableAiTitle = ref('全局');
const tableAiContext = ref('这是我要传给子组件的额外信息');
const allExpanded = ref(false); // 控制是否展开所有节点

// 行级AI相关变量（新的AI实例）
const rowAiVisible = ref(false);
const rowAiTitle = ref('特性');
const rowAiContext = ref('');

// 计算特性设计列完成度
const featureDesignCompletionRate = computed(() => {
  if (!data.value || data.value.length === 0) {
    return { completed: 0, total: 0, rate: 0 };
  }

  // 遍历所有的行数据（包括子节点）
  const allRows = [];

  const collectRows = (items) => {
    items.forEach((item) => {
      allRows.push(item);
      if (item.children && item.children.length > 0) {
        collectRows(item.children);
      }
    });
  };

  collectRows(treeData.value);

  // 总行数（包括feature_page为空的行）
  const total = allRows.length;
  let completed = 0;

  // 计算完成数（包含指定域名链接的行数）
  allRows.forEach((row) => {
    if (row.feature_page) {
      // 检查是否包含指定域名的链接
      if (
        typeof row.feature_page === 'string' &&
        (row.feature_page.includes('http://i.zte.com.cn/') || row.feature_page.includes('https://i.zte.com.cn/'))
      ) {
        completed++;
      }
    }
  });

  const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

  return {
    completed,
    total,
    rate,
  };
});

// 根据完成度返回相应的主题颜色
const getCompletionTheme = (rate) => {
  if (rate > 70) {
    return 'success';
  } else if (rate > 30) {
    return 'warning';
  } else {
    return 'danger';
  }
};

const onTableAiChat = () => {
  drawVisible.value = true;
};

const onRowAiChat = (rowData) => {
  // 将当前行数据转换为JSON格式作为上下文
  rowAiTitle.value = rowData.feature_name + ' 特性';
  rowAiContext.value = JSON.stringify(rowData, null, 2);
  rowAiVisible.value = true;
};

// AI评审功能的桩函数，调用后端API
const onRowAiReview = async (rowData) => {
  try {
    // 显示加载状态或提示
    MessagePlugin.info('正在启动AI评审...');

    // 准备发送到后端的数据
    const reviewData = {
      feature_id: rowData.feature_id,
      feature_name: rowData.feature_name,
      feature_function: rowData.feature_function,
      feature_level: rowData.feature_level,
      feature_page: rowData.feature_page,
      component: rowData.component,
      board: rowData.board,
      requirement: rowData.requirement,
      testcase: rowData.testcase,
      // 添加评审状态，未评审时为空字符串
      review_status: rowData.review_status || '',
    };

    // 调用后端AI评审API
    const response = await fetch(`${SERVER_API_URL}/api_data/ai_review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(reviewData),
    });

    const result = await response.json();

    if (result.status === 'success') {
      MessagePlugin.success('AI评审已启动');

      // 可以选择更新本地数据或重新加载表格
      // 根据API返回的结果更新当前行的评审状态
      if (result.review_status) {
        rowData.review_status = result.review_status;
      }

      // 可选：打开AI评审结果对话框或显示评审结果
      rowAiTitle.value = rowData.feature_name + ' AI评审结果';
      rowAiContext.value = JSON.stringify(result, null, 2);
      rowAiVisible.value = true;
    } else {
      MessagePlugin.error(result.message || 'AI评审启动失败');
    }
  } catch (error) {
    console.error('AI评审调用失败:', error);
    MessagePlugin.error('AI评审调用失败: ' + error.message);
  }
};

const diagVisible = ref(false); // 控制对话框显示与隐藏
const currentEditRow = ref(null); // 存储当前编辑行的数据

const diagReviewColumns = [
  {
    colKey: '标识',
    title: '标识',
    width: 100,
    cell: (h, { row }) => {
      const value = row.标识; // 假设数据中字段名为 '标识'
      if (!value) return '';

      const link = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${value}?teamId=bdv_106024`;

      return (
        <t-link theme="primary" href={link} target="_blank">
          {value}
        </t-link>
      );
    },
    ellipsis: true,
  },
  { colKey: '主题', title: '主题', width: 200, ellipsis: true },
  { colKey: '提交日期', title: '提交日期', width: 80 },
  { colKey: '一级特性', title: '一级特性', width: 80, ellipsis: true },
  { colKey: '二级特性', title: '二级特性', width: 120, ellipsis: true },
  { colKey: '故障引入点根因一级分类', title: '引入一级根因', width: 80, ellipsis: true },
  { colKey: '故障引入点根因二级分类', title: '引入二级根因', width: 120, ellipsis: true },
  { colKey: '故障控制点根因一级分类IT', title: '控制一级根因IT', width: 80, ellipsis: true },
  { colKey: '故障控制点根因二级分类IT', title: '控制二级根因IT', width: 120, ellipsis: true },
];

const columns = [
  {
    colKey: 'feature_id',
    title: '特性编号',
    width: '120',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'feature_name',
    title: '特性名称',
    width: '240',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'feature_function',
    title: '特性功能',
    width: '240',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'feature_page',
    title: '特性设计',
    width: '120',
    ellipsis: true,
    cell: (h, { row }) => {
      const value = row.feature_page;
      if (!value) return '';

      // 判断是否是链接（以 http:// 或 https:// 开头的字符串）
      if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
        return (
          <t-link theme="primary" href={value} target="_blank">
            {value}
          </t-link>
        );
      }

      // 非链接内容直接显示
      return <span>{value}</span>;
    },
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'feature_level',
    title: '特性等级',
    width: '120',
    ellipsis: true, // 新增：超出一行显示省略号
    cell: (h, { row }) => {
      // 根据特性等级显示不同样式的标签
      if (row.feature_level === '一级特性') {
        return (
          <t-tag theme="primary" variant="light-outline">
            一级特性
          </t-tag>
        );
      } else if (row.feature_level === '二级特性') {
        return (
          <t-tag theme="primary" variant="light">
            二级特性
          </t-tag>
        );
      }
      // 可以添加更多等级的标签样式
      return <t-tag>{row.feature_level}</t-tag>;
    },
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'component',
    title: '组件',
    width: '120',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'board',
    title: '单板',
    width: '120',
    ellipsis: true, // 新增：超出一行显示省略号
    cell: (h, { row }) => {
      // 严格判断是否与board相等
      if (row.board && row.board === board.value) {
        return <t-tag theme="success">{row.board}</t-tag>; // 相等时显示绿色标签
      } else {
        return row.board; // 不相等时直接显示文本，不打标签
      }
    },
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'requirement',
    title: '需求',
    width: '120',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'issue',
    title: '故障',
    width: '120',
    ellipsis: true,
    edit: { component: Input, showEditIcon: false },
    // ✅ 使用 cell 自定义渲染
    cell: (h, { row }) => {
      const issue = row.issue;
      if (!issue || typeof issue !== 'object' || issue.count === 0) {
        return '引入  0 个故障';
      }
      return (
        <t-link theme="primary" hover="color" onClick={() => openReviewDialog(issue.data)}>
          引入 {issue.count} 个故障
        </t-link>
      );
    },
  },
  {
    colKey: 'testcase',
    title: '用例',
    width: '80',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'api',
    title: '接口',
    width: '80',
    ellipsis: true, // 新增：超出一行显示省略号
    edit: { component: Input, showEditIcon: false },
  },
  {
    colKey: 'review_status',
    title: '评审状态',
    width: '100',
    ellipsis: true,
    cell: (h, { row }) => {
      if (row.review_status === '通过') {
        return (
          <t-tag theme="success" variant="light-outline">
            通过
          </t-tag>
        );
      } else if (row.review_status === '不通过') {
        return (
          <t-tag theme="danger" variant="light-outline">
            不通过
          </t-tag>
        );
      }
      return <t-tag variant="default">未评审</t-tag>; // 显示"未评审"而不是空标签
    },
    edit: {
      component: Select,
      showEditIcon: false,
      props: {
        options: [
          { label: '未评审', value: '' },
          { label: '通过', value: '通过' },
          { label: '不通过', value: '不通过' },
        ],
      },
    },
  },
  {
    colKey: 'ai_review',
    title: 'AI评审',
    width: '90',
    ellipsis: true, // 超出一行显示省略号
    cell: (h, { row }) => {
      // 移除判断条件，所有按钮都默认可点击
      return (
        <t-button
          theme="primary"
          size="small"
          onClick={() => onRowAiReview(row)} // 点击时打开行级AI并传递当前行数据用于AI评审
        >
          AI评审
        </t-button>
      );
    },
  },
  {
    colKey: 'ai',
    title: '智能体',
    width: '90',
    ellipsis: true, // 超出一行显示省略号
    cell: (h, { row }) => {
      // 移除判断条件，所有按钮都默认可点击
      return (
        <t-button
          theme="primary"
          size="small"
          onClick={() => onRowAiChat(row)} // 点击时打开行级AI并传递当前行数据
        >
          AI助手
        </t-button>
      );
    },
  },
  {
    colKey: 'edit',
    title: '操作',
    width: '80',
    ellipsis: true,
    cell: (h, { row }) => {
      return (
        <div class="table-operations">
          <t-link
            theme="primary"
            hover="color"
            data-id={row.id}
            onClick={() => openEditModal(row)} // 点击打开编辑弹窗
          >
            编辑
          </t-link>
        </div>
      );
    },
  },
];

// 新增：编辑弹窗函数，用于打开编辑窗口
function openEditModal(row) {
  // 这里可以实现打开弹窗的逻辑
  console.log('打开编辑窗口，当前行数据：', row);

  // 点击编辑时，记录当前行数据并显示对话框
  currentEditRow.value = { ...row }; // 深拷贝当前行数据，避免直接修改表格数据
  diagVisible.value = true; // 显示对话框

  // 示例：如果使用的是TDesign的弹窗组件
  // editModalVisible.value = true;
  // currentEditRow.value = { ...row };
}

// 新增：处理编辑表单提交
async function onEditSubmit() {
  // 在这里可以添加验证逻辑

  try {
    // 准备要发送到后端的数据，排除可能不适用于feature表的字段
    const featureData = {
      feature_id: currentEditRow.value.feature_id,
      feature_name: currentEditRow.value.feature_name,
      feature_function: currentEditRow.value.feature_function,
      feature_level: currentEditRow.value.feature_level,
      feature_page: currentEditRow.value.feature_page,
      domain: field.value, // 使用当前选择的领域
      component: currentEditRow.value.component,
      review_status: currentEditRow.value.review_status, // 评审状态
    };

    // 调用后端API更新数据库
    const response = await fetch(`${SERVER_API_URL}/api_data/feature_set`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(featureData),
    });

    const result = await response.json();

    if (result.status === 'success') {
      // 更新data.value中的对应行数据
      const index = data.value.findIndex((item) => item.id === currentEditRow.value.id);
      if (index !== -1) {
        // 直接更新data.value中的数据
        data.value[index] = { ...currentEditRow.value };

        // 由于data是响应式的，更新后会自动反映在表格中
        MessagePlugin.success(result.message || '编辑成功');
      } else {
        MessagePlugin.error('更新本地数据失败：未找到对应的行');
      }

      // 关闭对话框
      diagVisible.value = false;
    } else {
      MessagePlugin.error(result.message || '更新数据库失败');
    }
  } catch (error) {
    console.error('保存数据到数据库时出错:', error);
    MessagePlugin.error('保存失败：' + error.message);
  }
}

// 展开/收起所有节点的函数
const toggleAllExpanded = () => {
  if (!tableRef.value) return;

  if (allExpanded.value) {
    // 当前是展开状态，需要收起所有
    tableRef.value.foldAll();
  } else {
    // 当前是收起状态，需要展开所有
    tableRef.value.expandAll();
  }

  // 切换状态
  allExpanded.value = !allExpanded.value;
};

// 递归获取所有节点的key
const getAllRowKeys = (data) => {
  const keys = [];
  data.forEach((item) => {
    keys.push(item.id);
    if (item.children && item.children.length > 0) {
      keys.push(...getAllRowKeys(item.children));
    }
  });
  return keys;
};

// ✅ 新增：控制故障列表弹窗
const issueDiagVisible = ref(false);
const dialogReviewData = ref([]); // 弹窗中表格的数据

// ✅ 新增：打开故障列表弹窗
const openReviewDialog = (reviewData) => {
  dialogReviewData.value = reviewData;
  issueDiagVisible.value = true;
};

// 计算属性：将扁平数据转换为树形结构
const treeData = computed(() => {
  if (!data.value || data.value.length === 0) return [];

  // 创建映射表
  const dataMap = {};
  const result = [];

  // 初始化所有数据项，添加children字段
  data.value.forEach((item) => {
    dataMap[item.id] = { ...item, children: [] };
  });

  // 构建树形结构
  data.value.forEach((item) => {
    const currentItem = dataMap[item.id];

    // 根据feature_level确定层级关系
    if (item.feature_level === '一级特性') {
      // 一级特性作为根节点
      result.push(currentItem);
    } else if (item.feature_level === '二级特性') {
      // 二级特性查找对应的一级特性父节点
      const parent = findParentFeature(dataMap, item.feature_id, '一级特性');
      if (parent) {
        parent.children.push(currentItem);
      } else {
        // 找不到父节点时作为根节点
        result.push(currentItem);
      }
    } else if (item.feature_level === '三级特性') {
      // 三级特性查找对应的二级特性父节点
      const parent = findParentFeature(dataMap, item.feature_id, '二级特性');
      if (parent) {
        parent.children.push(currentItem);
      } else {
        // 找不到父节点时作为根节点
        result.push(currentItem);
      }
    } else {
      // 其他情况作为根节点
      result.push(currentItem);
    }
  });

  return result;
});

// 辅助函数：查找父级特性
function findParentFeature(dataMap, featureId, parentLevel) {
  // 根据特性编号规则匹配父子关系
  // 一级特性格式：D001, D002...
  // 二级特性格式：D001-001, D001-002...
  // 三级特性格式：D001-001-001, D001-001-002...

  if (parentLevel === '一级特性') {
    // 二级特性查找一级特性父节点
    // 从D001-001中提取D001
    const parentId = featureId.split('-')[0];
    for (const id in dataMap) {
      const item = dataMap[id];
      if (item.feature_level === '一级特性' && item.feature_id === parentId) {
        return item;
      }
    }
  } else if (parentLevel === '二级特性') {
    // 三级特性查找二级特性父节点
    // 从D001-001-001中提取D001-001
    const parts = featureId.split('-');
    if (parts.length >= 2) {
      const parentId = parts[0] + '-' + parts[1];
      for (const id in dataMap) {
        const item = dataMap[id];
        if (item.feature_level === '二级特性' && item.feature_id === parentId) {
          return item;
        }
      }
    }
  }

  return null;
}

const data = ref();
const tableRef = ref();
const editableRowKeys = ref([]);
const tableLoading = ref(false);
const currentSaveId = ref('');
const editMap = {};
const field = ref('L2');
const fieldOptions = [
  { label: 'L0领域', value: 'L0' },
  { label: 'L1领域', value: 'L1' },
  { label: 'L2领域', value: 'L2' },
  { label: '支撑领域', value: '支撑' },
  { label: '智控领域', value: '智控' },
];
const board = ref();
const boardOptions = [
  { label: 'M1SGEP', value: 'M1SGEP' },
  { label: 'M3SGEP', value: 'M3SGEP' },
  { label: 'EGEP', value: 'EGEP' },
  { label: 'EXGP', value: 'EXGP' },
  { label: 'SOG2', value: 'SOG2' },
  { label: 'E2K', value: 'E2K' },
  { label: 'E4K', value: 'E4K' },
  { label: 'PGEL', value: 'PGEL' },
  { label: 'PXGK', value: 'PXGK' },
  { label: 'PCGL', value: 'PCGL' },
  { label: 'M2H2K', value: 'M2H2K' },
  { label: 'M3H2K', value: 'M3H2K' },
  { label: 'M2H4K', value: 'M2H4K' },
  { label: 'M3H4K', value: 'M3H4K' },
  { label: 'M2H4L', value: 'M2H4L' },
];

// 更新 editableRowKeys
const updateEditState = (id) => {
  const index = editableRowKeys.value.findIndex((t) => t === id);
  editableRowKeys.value.splice(index, 1);
};

const onEdit = (e) => {
  console.log('onEdit');

  const { id } = e.currentTarget.dataset;
  if (!editableRowKeys.value.includes(id)) {
    editableRowKeys.value.push(id);
  }
};

const onCancel = (e) => {
  console.log('onCancel');

  const { id } = e.currentTarget.dataset;
  updateEditState(id);
  tableRef.value.clearValidateData();
};

const onSave = (e) => {
  console.log('onSave');

  const { id } = e.currentTarget.dataset;
  currentSaveId.value = id;

  // 直接更新数据，不进行校验
  const current = editMap[currentSaveId.value];
  if (current) {
    data.value.splice(current.rowIndex, 1, current.editedRow);
    MessagePlugin.success('保存成功');
  }
  updateEditState(currentSaveId.value);
};

const onRowEdit = (params) => {
  const { row, col, value } = params;
  const oldRowData = editMap[row.id]?.editedRow || row;
  const editedRow = { ...oldRowData, [col.colKey]: value };
  editMap[row.id] = {
    ...params,
    editedRow,
  };
};

/**
 * 读取表格数据的函数
 * 适配后端返回的 {status, message, tableData} 结构
 */
const onTableRead = async () => {
  tableLoading.value = true; // 开始加载时显示加载状态
  console.log('开始读取数据...');

  const ERROR_MESSAGES = {
    NETWORK_ERROR: '网络请求失败，请检查网络连接',
    TIMEOUT_ERROR: '请求超时，请稍后重试',
    SERVER_ERROR: '服务器返回错误',
    INVALID_JSON: '返回的数据不是有效的JSON格式',
    INVALID_DATA_FORMAT: '返回的数据格式不正确，预期是数组',
    UNKNOWN_ERROR: '发生未知错误',
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    let response;
    try {
      // 使用新的API_Feature_read接口
      response = await fetch(`${SERVER_API_URL}/api_data/API_Feature_read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: field.value || '',
          board: board.value || '',
        }),
        signal: controller.signal,
      });
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('请求超时:', error);
        MessagePlugin.error(ERROR_MESSAGES.TIMEOUT_ERROR);
        throw new Error(ERROR_MESSAGES.TIMEOUT_ERROR);
      }
      console.error('网络请求失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.NETWORK_ERROR);
      throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
    }

    if (!response.ok) {
      const errorMsg = `HTTP错误! 状态码: ${response.status}`;
      console.error(errorMsg);
      MessagePlugin.error(ERROR_MESSAGES.SERVER_ERROR);
      throw new Error(errorMsg);
    }

    let responseData;
    try {
      responseData = await response.json();
    } catch (error) {
      console.error('解析响应JSON失败:', error);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
      throw new Error(ERROR_MESSAGES.INVALID_JSON);
    }

    if (responseData.status !== 'success') {
      const errorMsg = responseData.message || '读取表格失败';
      console.error('服务器返回错误:', errorMsg);
      MessagePlugin.error(errorMsg);
      throw new Error(errorMsg);
    }

    console.log('数据读取成功，服务器消息：', responseData.message);

    // 从tableData字段获取数据（关键修改点）
    let tableData = responseData.tableData || [];

    // 如果是字符串，尝试解析为JSON
    if (typeof tableData === 'string') {
      try {
        tableData = JSON.parse(tableData);
      } catch (error) {
        console.error('解析表格数据JSON失败:', error);
        MessagePlugin.error(ERROR_MESSAGES.INVALID_JSON);
        throw new Error(ERROR_MESSAGES.INVALID_JSON);
      }
    }

    // 确保数据是数组
    if (!Array.isArray(tableData)) {
      console.error('表格数据格式不正确:', tableData);
      MessagePlugin.error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
      throw new Error(ERROR_MESSAGES.INVALID_DATA_FORMAT);
    }

    // --- ✅ 映射数据到表格列结构，并将 review 显示在 issue 列 ---
    // --- ✅ 修改：映射数据，issue 存数量和数据 ---
    data.value = tableData.map((item, index) => {
      const reviewList = Array.isArray(item.review) ? item.review : [];
      const issueCount = reviewList.length;
      // ✅ 日期格式化函数
      const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? dateStr : date.toISOString().split('T')[0];
      };

      return {
        id: item.id || index.toString(),
        feature_id: item.feature_id || '',
        feature_name: item.feature_name || '',
        feature_function: item.feature_function || '',
        feature_level: item.feature_level || '',
        component: item.component || '',
        board: Array.isArray(item.board) ? item.board.join(', ') : '',
        requirement: item.requirement || '',
        review_status: item.review_status || '', // 评审状态，空字符串表示未评审
        ai_review: item.ai_review || '', // AI评审
        // ✅ issue 现在是一个对象，包含 count 和 data
        issue: {
          count: issueCount,
          data: reviewList.map((reviewItem) => ({
            标识: reviewItem.标识 || '',
            主题: reviewItem.主题 || '',
            提交日期: formatDate(reviewItem.提交日期),
            一级特性: reviewItem.一级特性 || '',
            二级特性: reviewItem.二级特性 || '',
            故障引入点根因一级分类: reviewItem.故障引入点根因一级分类 || '',
            故障引入点根因二级分类: reviewItem.故障引入点根因二级分类 || '',
            故障控制点根因一级分类IT: reviewItem.故障控制点根因一级分类IT || '',
            故障控制点根因二级分类IT: reviewItem.故障控制点根因二级分类IT || '',
          })),
        },
        testcase: item.testcase || '',
        feature_page: item.feature_page || '',
        agent: item.agent || '不支持',
      };
    });

    tableAiContext.value = JSON.stringify(
      data.value.map(({ issue, ...rest }) => rest), // 剔除每行的 issue 字段
      null,
      2,
    );

    MessagePlugin.success(responseData.message || '数据加载成功');
    console.log('数据处理完成，共加载', data.value.length, '条记录');
    return tableData;
  } catch (error) {
    console.error('数据读取过程中出错:', error);
    if (!Object.values(ERROR_MESSAGES).includes(error.message)) {
      MessagePlugin.error(ERROR_MESSAGES.UNKNOWN_ERROR);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    tableLoading.value = false; // 数据加载完成后关闭加载状态
  }
};

// 写入表格数据
const onTableWrite = async () => {
  console.log('开始写入数据...');

  if (!data.value || data.value.length === 0) {
    MessagePlugin.warning('没有数据可保存');
    return;
  }

  try {
    // 转换数据为后端需要的格式
    const payload = {
      table: 'Feature',
      domain: field.value,
      tableData: data.value.map((item) => ({
        编号: item.id,
        一级特性: item.level1,
        二级特性: item.level2,
        特性描述: item.feature_description,
        特性文档: item.feature_documentation,
      })),
    };

    // 发送请求
    const response = await axios.post(`${SERVER_API_URL}/api_data/Table_write`, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
    });

    if (response.data.status === 'success') {
      MessagePlugin.success('数据保存成功');
      console.log('数据写入成功');
    } else {
      MessagePlugin.error(response.data.message || '保存失败');
      throw new Error(response.data.message || '保存失败');
    }
  } catch (error) {
    console.error('保存数据时出错:', error);

    let errorMessage = '保存失败';
    if (error.response) {
      // 服务器返回了错误响应
      errorMessage = error.response.data.message || errorMessage;
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = '服务器无响应，请检查网络连接';
    } else {
      // 请求设置出错
      errorMessage = error.message || errorMessage;
    }

    MessagePlugin.error(errorMessage);
    throw error;
  }
};

onMounted(() => {
  onTableRead();
});

// 监听 field 变化，自动读取数据
// watch(field, (newValue, oldValue) => {
//   if (newValue !== oldValue) {
//     onTableRead();
//   }
// });
</script>

<style>
.table-operations .t-link {
  margin-right: 8px;
}

.feature-main {
  /* 基础表格样式 */
  table {
    /* max-width: 100%; */
    border-collapse: collapse;
    /* border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      margin-top: 1em;
      margin-bottom: 1em; */
  }

  /* 表头样式 */
  th {
    background-color: #e7e7e7;
    color: #333;
    white-space: nowrap; /* 防止表头换行 */
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    border-left: none;
    border-right: none;
    line-height: 1.4; /* 紧凑行高 */
  }

  /* 单元格样式 */
  td {
    background-color: #fefefe;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4; /* 紧凑行高 */
    border-left: none;
    border-right: none;
  }

  /* 奇偶行颜色区分 */
  /* tr:nth-child(even) td {
      background-color: #f8f8f8;
    } */

  /* 悬停效果 */
  tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
  }

  /* 响应式优化 */
  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
</style>
