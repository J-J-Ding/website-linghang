<template>
  <div class="m-table">
    <t-space direction="vertical" style="width: 100%">
      <t-space>
        <t-button @click="onTableReadFresh">刷新</t-button>
        <t-button @click="onBatchExport">批量导出</t-button>

        <t-input v-model="searchValue" placeholder="搜索..." clearable>
          <template #suffix-icon>
            <search-icon />
          </template>
        </t-input>
        <t-select
          v-model="selectedColumns"
          :options="columnOptions"
          multiple
          placeholder="选择显示列"
          :min-collapsed-num="1"
          style="width: 200px"
        >
          <template #prefix-icon>
            <icon name="menu" />
          </template>
        </t-select>

        <!-- 场景选择控件 -->
        <t-radio-group
          v-if="props.sceneConfig && props.sceneConfig.length > 0"
          variant="default-filled"
          :value="currentSceneKey"
          @change="handleSceneChange"
        >
          <t-radio-button v-for="scene in props.sceneConfig" :key="scene.key" :value="scene.key">
            {{ scene.label }}
          </t-radio-button>
        </t-radio-group>
        <t-button @click="jumpToTablePage">度量看板</t-button>
      </t-space>

      <t-table
        ref="tableRef"
        row-key="id"
        bordered
        lazy-load
        :columns="columns"
        :data="paginatedData"
        :editable-row-keys="editableRowKeys"
        :max-height="tableHeight"
        :loading="loading"
        :pagination="pagination"
        :filter-value="filterValue"
        :filterRow="null"
        style="width: 100%"
        @row-edit="onRowEdit"
        @page-change="onPageChange"
        @filter-change="onFilterChange"
      />
    </t-space>

    <!-- 行级AI实例 -->
    <AiChat
      :visible="rowAiVisible"
      :ai-chat-title="rowAiTitle"
      :ai-chat-context="rowAiContext"
      @update:visible="rowAiVisible = $event"
    />
  </div>
</template>

<script setup lang="jsx">
import * as XLSX from 'xlsx';
import { ref, computed, onMounted, onUnmounted, watch, reactive, h } from 'vue';
import { Icon, SearchIcon, ChatIcon } from 'tdesign-icons-vue-next';
import { MessagePlugin, Tooltip as TTooltip } from 'tdesign-vue-next';
import { useUserStore } from '@/store';
import { pubCalculateTableHeight } from '@/utils/pub';
import AiChat from '@/pages/ai/genCode/chat.vue';
import { LoadingPlugin } from 'tdesign-vue-next';
import { useRouter } from 'vue-router';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const userStore = useUserStore();
const router = useRouter();

// 对外提供的属性
const props = defineProps({
  // 表格配置
  tableConfig: {
    type: Object,
    required: true,
    default: () => ({}),
  },
  // 表单字段配置
  formFields: {
    type: Array,
    required: true,
    default: () => [],
  },
  // 表单验证规则
  editRules: {
    type: Object,
    default: () => ({}),
  },
  // 读取数据的API路径
  readApiPath: {
    type: String,
    required: true,
  },
  // 保存数据的API路径
  saveApiPath: {
    type: String,
    required: true,
  },
  // 删除数据的API路径
  deleteApiPath: {
    type: String,
    required: true,
  },
  // 表格标题（用于AI上下文）
  tableTitle: {
    type: String,
    default: '表格',
  },
  // 默认查询参数
  defaultParams: {
    type: Object,
    default: () => ({}),
  },
  // 是否支持新建功能
  supportCreate: {
    type: Boolean,
    default: true,
  },
  // 场景配置，用于列显示和筛选控制
  sceneConfig: {
    type: Array,
    default: () => [],
  },
});

const jumpToTablePage = () => {
  router.push('/ai/code/genCodeTable');
};

// 对外提供的事件
const emit = defineEmits(['data-loaded', 'row-created', 'row-updated', 'row-deleted']);

// 响应式数据
const data = ref([]);
const loading = ref(false);
const searchValue = ref('');
const tableRef = ref(null);
const tableHeight = ref('900px');
const filterValue = ref({}); // 添加筛选值
const selectedColumns = ref([]); // 选中的列
const currentSceneKey = ref(''); // 默认为空，表示未选择特定场景

// 分页相关数据
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showJumper: false,
});

// 限制最大分页大小
const MAX_PAGE_SIZE = 100;

// AI相关
const tableAiContext = ref('');

const rowAiVisible = ref(false);
const rowAiTitle = ref('行内');
const rowAiContext = ref('');

// 编辑相关
const diagVisible = ref(false);
const currentEditRow = ref(null);
const isCreateMode = ref(false);
const editableRowKeys = ref([]);

// 导入相关
const importDialogVisible = ref(false);
const fileList = ref([]);
const uploadError = ref('');
const importLoading = ref(false);

// 为动态筛选列缓存唯一值
const dynamicFilterCache = new Map();


// 获取指定列的唯一值（带缓存优化和数量限制）
const getColumnUniqueValues = (data, colKey, limit = 100) => {
  // 创建缓存键
  const cacheKey = `${colKey}_${data.length}_${limit}`;

  // 检查缓存
  if (dynamicFilterCache.has(cacheKey)) {
    return dynamicFilterCache.get(cacheKey);
  }

  // 处理嵌套属性
  const values = data
    .map((item) => {
      if (colKey.includes('.')) {
        const keys = colKey.split('.');
        let value = item;
        for (const key of keys) {
          value = value ? value[key] : '';
        }
        return value;
      }
      return item[colKey];
    })
    .filter((value) => value !== undefined && value !== null);

  // 去重
  let uniqueValues = [...new Set(values)];

  // 按字符串排序
  uniqueValues.sort((a, b) => String(a).localeCompare(String(b)));

  // 限制数量
  if (uniqueValues.length > limit) {
    uniqueValues = uniqueValues.slice(0, limit);
  }

  // 存入缓存
  dynamicFilterCache.set(cacheKey, uniqueValues);

  return uniqueValues;
};

// 监听数据变化，清除缓存
watch(data, () => {
  dynamicFilterCache.clear();
});

// 列选项
const columnOptions = computed(() => {
  return props.formFields.map((field) => {
    // 根据isTitle属性判断是否为关键字段，需要默认选中且不可更改
    const isKeyField = field.isTitle === true;
    return {
      label: field.label,
      value: field.key,
      disabled: isKeyField, // key列不可更改
    };
  });
});

// 计算属性
const filteredData = computed(() => {
  let result = data.value;

  // 应用筛选条件
  if (filterValue.value && Object.keys(filterValue.value).length > 0) {
    result = result.filter((item) => {
      return Object.entries(filterValue.value).every(([colKey, filterValues]) => {
        // 空数组或未设置筛选条件时，不过滤
        if (!filterValues || (Array.isArray(filterValues) && filterValues.length === 0)) {
          return true;
        }

        // 获取字段值
        let value = item[colKey];

        // 处理数组类型的筛选值
        if (Array.isArray(filterValues)) {
          // 检查是否包含"全选"选项
          const hasCheckAll = filterValues.some((v) => {
            // 检查是否是全选选项对象
            if (typeof v === 'object' && v !== null) {
              return v.checkAll === true;
            }
            // 检查是否是"全选"字符串
            return v === '全选';
          });

          // 如果有全选选项，则不过滤
          if (hasCheckAll) {
            return true;
          }

          // 检查值是否在筛选列表中
          return filterValues.includes(value);
        } else {
          // 单值筛选
          return filterValues === value;
        }
      });
    });
  }

  // 应用搜索过滤
  if (searchValue.value) {
    // 将搜索值按空格分割成多个关键词，并过滤掉空字符串
    const keywords = searchValue.value
      .toLowerCase()
      .split(' ')
      .filter((keyword) => keyword.trim() !== '');

    // 如果没有有效的关键词，返回所有数据
    if (keywords.length > 0) {
      result = result.filter((item) => {
        // 将行数据的所有值连接成一个字符串用于搜索
        const rowText = Object.values(item)
          .map((value) => String(value))
          .join(' ')
          .toLowerCase();

        // 检查是否所有关键词都在行文本中
        return keywords.every((keyword) => rowText.includes(keyword));
      });
    }
  }

  // 按指定排序字段排序（查找设置了 sort 为 true 的字段）
  const sortField = props.formFields.find((field) => field.sort === true);
  if (sortField) {
    result = result.sort((a, b) => {
      const valueA = a[sortField.key];
      const valueB = b[sortField.key];

      // 处理数字类型排序（倒序）
      if (!isNaN(Number(valueA)) && !isNaN(Number(valueB))) {
        return Number(valueB) - Number(valueA);
      }

      // 字符串排序（倒序）
      return String(valueB).localeCompare(String(valueA));
    });
  }

  return result;
});

// 分页数据计算属性
const paginatedData = computed(() => {
  // 使用filteredData作为源数据
  const sourceData = filteredData.value;

  // 更新总数据量
  pagination.total = sourceData.length;

  // 计算当前页的数据
  const start = (pagination.current - 1) * pagination.pageSize;
  const end = start + pagination.pageSize;

  return sourceData.slice(start, end);
});

// 监听搜索值变化，更新AI上下文
watch(searchValue, (newSearchValue) => {
  // 使用经过筛选和搜索后的最终结果（只包含显示的列）
  tableAiContext.value = JSON.stringify(getDisplayData(filteredData.value), null, 2);
});

const columns = computed(() => {
  // 序号列
  const indexColumn = {
    colKey: 'index',
    title: '序号',
    width: 60,
    cell: (h, { rowIndex }) => {
      return rowIndex + 1;
    },
  };

  // 基础字段列
  const fieldColumns = props.formFields
    // 只显示选中的列（如果selectedColumns为空，则显示所有列）
    // 但始终显示key列（根据isTitle属性判断）
    .filter(
      (field) =>
        field.isTitle === true || selectedColumns.value.length === 0 || selectedColumns.value.includes(field.key),
    )
    .map((field) => {
      // 构造基础列配置
      const columnConfig = {
        colKey: field.key,
        title: field.label,
        width: field.width || 120,
        ellipsis: true,
        ...(field.filterable
          ? {
              // 添加筛选配置
              filter: {
                type: field.filterType || 'multiple',
                resetValue: field.filterResetValue || [],
                list: field.filterList || [
                  { label: '全选', checkAll: true },
                  ...getColumnUniqueValues(data.value, field.key, 100).map((value) => ({
                    label: String(value),
                    value: value,
                  })),
                ],
                showConfirmAndReset: false, // 不显示确认和重置按钮，选中即生效
                popupProps: {
                  overlayInnerStyle: {
                    maxHeight: '400px',
                    overflowY: 'auto',
                  },
                  ...(field.filterPopupProps || {}),
                },
              },
            }
          : {}),
        ...(field.type === 'select' && field.options
          ? {
              cell: (h, { row }) => {
                const option = field.options.find((opt) => opt.value === row[field.key]);
                return option ? option.label : row[field.key] || '';
              },
            }
          : field.type === 'link'
            ? {
                cell: (h, { row }) => {
                  const linkValue = row[field.key] || '';
                  if (!linkValue) return '';

                  // 根据字段名构造链接地址
                  let link = '';
                  if (field.key === '标识') {
                    // 对于标识字段，构造特定的 RDCloud 链接
                    link = `https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/OTNAG/apps/wim/allWorkItems/${linkValue}?teamId=bdv_106024`;
                  } else {
                    // 对于其他链接字段，直接使用字段值作为链接
                    link = linkValue;
                  }

                  // 使用 JSX 语法创建 TLink 组件
                  return (
                    <t-link theme="primary" href={link} target="_blank">
                      {linkValue}
                    </t-link>
                  );
                },
              }
            : field.type === 'html' || field.type === 'textarea'
              ? {
                  cell: (h, { row }) => {
                    try {
                      // 显示纯文本内容，保留换行符
                      const fieldValue = row[field.key] || '';
                      // 对于HTML类型，需要处理HTML标签；对于textarea类型直接使用
                      let textContent = fieldValue;
                      if (field.type === 'html') {
                        // 将HTML标签转换为换行符，然后清理多余的空白字符
                        textContent = fieldValue
                          .replace(/<br\s*\/?>/gi, '\n')
                          .replace(/<p\s*>/gi, '\n')
                          .replace(/<\/p>/gi, '\n')
                          .replace(/<div\s*>/gi, '\n')
                          .replace(/<\/div>/gi, '\n')
                          .replace(/<[^>]*>/g, '') // 移除其他HTML标签
                          .replace(/&nbsp;/g, ' ') // 处理HTML实体
                          .replace(/&lt;/g, '<')
                          .replace(/&gt;/g, '>')
                          .replace(/&amp;/g, '&');
                      }

                      // 清理多余的换行和空白字符
                      textContent = textContent
                        .replace(/^\s+|\s+$/g, '') // 去除首尾空白字符
                        .replace(/\n{3,}/g, '\n\n') // 将3个或更多连续换行替换为2个换行
                        .trim();

                      // 单行显示，溢出显示省略号
                      const displayText = h(
                        'div',
                        {
                          style: {
                            'white-space': 'nowrap',
                            overflow: 'hidden',
                            'text-overflow': 'ellipsis',
                          },
                        },
                        textContent,
                      );

                      // 使用TTooltip组件显示完整内容
                      return h(
                        TTooltip,
                        {
                          content: () =>
                            h(
                              'div',
                              {
                                style: {
                                  'max-width': '900px',
                                  'max-height': '200px',
                                  'overflow-y': 'auto',
                                  'white-space': 'pre-wrap',
                                  'word-break': 'break-word',
                                  'line-height': '1.5',
                                  'font-family': 'inherit',
                                  'font-size': 'inherit',
                                  'whiteSpace': 'pre-wrap',
                                },
                              },
                              textContent,
                            ),
                          placement: 'top-left',
                          showArrow: true,
                          destroyOnClose: true,
                          overlayInnerStyle: {
                            'white-space': 'pre-wrap',
                            'word-break': 'break-word',
                            'line-height': '1.5',
                            'max-width': '900px'
                          },
                        },
                        {
                          default: () => displayText,
                        },
                      );
                    } catch (error) {
                      console.error('Error processing HTML/textarea field:', error);
                      return '';
                    }
                  },
                }
              : {}),
        edit: {
          component: field.type === 'select' ? 'Select' : 'Input',
          showEditIcon: false,
          props: field.type === 'select' ? { options: field.options } : {},
        },
      };

      return columnConfig;
    });

  // AI列
  const aiColumn = {
    colKey: 'ai',
    title: '智能体',
    width: 100,
    fixed: 'right',
    cell: (h, { row }) => {
      return (
        <t-button theme="primary" size="small" onClick={() => onRowAiChat(row)}>
          AI助手
        </t-button>
      );
    },
  };

  return [indexColumn, ...fieldColumns, aiColumn];
});

// 方法
// 处理场景切换
function handleSceneChange(sceneKey) {
  currentSceneKey.value = sceneKey;

  // 查找对应的场景配置
  const selectedScene = props.sceneConfig.find((scene) => scene.key === sceneKey);
  if (selectedScene) {
    // 更新选中的列
    if (selectedScene.columns) {
      selectedColumns.value = [...selectedScene.columns];
    } else {
      // 如果没有指定列或场景不存在，清空选择（将显示所有列）
      selectedColumns.value = [];
    }

    // 更新筛选条件
    if (selectedScene.filters) {
      // 将场景中的筛选条件应用到filterValue
      filterValue.value = { ...selectedScene.filters };
    } else {
      // 如果没有指定筛选条件，清空筛选
      filterValue.value = {};
    }
  } else {
    // 如果场景不存在，清空列选择和筛选
    selectedColumns.value = [];
    filterValue.value = {};
  }

  // 切换场景后重新加载数据
  onTableRead();
}

const onRowAiChat = async (rowData) => {
  const titleField = props.formFields.find((field) => field.isTitle) || props.formFields[0];
  const titleValue = titleField && rowData[titleField.key] ? rowData[titleField.key] : '记录';
  rowAiTitle.value = titleValue;
  rowAiContext.value = JSON.stringify(rowData, null, 2);
  rowAiVisible.value = true;
};

const openEditModal = (row) => {
  currentEditRow.value = { ...row };
  isCreateMode.value = false;
  diagVisible.value = true;
};

const onDeleteRow = async (row) => {
  try {
    loading.value = true;

    // 根据后端API_Table_del的期望格式构造请求数据
    // 传递完整的行数据作为conditions，但排除前端添加的id字段，让后端根据表配置确定主键字段
    // 同时添加user参数

    // 从Pinia store中获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    // 排除前端用于唯一标识的id字段，只传递原始数据字段
    const { id, ...conditionsWithoutId } = { ...row };

    const requestData = {
      user: currentUser,
      table_name: props.defaultParams.table_name,
      conditions: conditionsWithoutId,
    };

    // 调用后端API删除数据
    const response = await fetch(`${SERVER_API_URL}${props.deleteApiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '删除数据失败');
    }

    // 从表格数据中移除该行
    const index = data.value.findIndex((item) => item.id === row.id);
    if (index !== -1) {
      data.value.splice(index, 1);
    }

    MessagePlugin.success(responseData.message || '删除成功');
    emit('row-deleted', row);
  } catch (error) {
    console.error('删除失败:', error);
    MessagePlugin.error(error.message || '删除失败');
  } finally {
    loading.value = false;
  }
};

const onRowEdit = (params) => {
  const { row, col, value } = params;
  const index = data.value.findIndex((item) => item.id === row.id);
  if (index !== -1) {
    // 创建一个新的对象而不是直接修改现有对象
    data.value[index] = { ...data.value[index], [col.colKey]: value };
  }
};

// 防抖函数
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// 使用防抖优化的筛选处理函数
const debouncedFilterChange = debounce((filters) => {
  filterValue.value = { ...filters };
}, 300);

const onFilterChange = (filters, ctx) => {
  console.log('filter-change', filters, ctx);
  debouncedFilterChange(filters);
};

// 分页事件处理方法
const onPageChange = (pageInfo, context) => {
  console.log('page-change', pageInfo, context);
  // 受控用法需要更新pagination的current和pageSize
  pagination.current = pageInfo.current;
  // 限制分页大小
  pagination.pageSize = Math.min(pageInfo.pageSize, MAX_PAGE_SIZE);
};

const onTableRead = async () => {
  try {
    loading.value = true;

    // 根据后端API_Table_get的期望格式构造请求数据
    // 同时添加user参数

    // 从Pinia store中获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    // 获取当前场景的过滤条件
    let sceneFilters = {};
    if (currentSceneKey.value && props.sceneConfig) {
      const currentScene = props.sceneConfig.find((scene) => scene.key === currentSceneKey.value);
      if (currentScene && currentScene.filters) {
        sceneFilters = currentScene.filters;
      }
    }

    const requestData = {
      user: currentUser,
      table_name: props.defaultParams.table_name,
      ...props.defaultParams,
      conditions: sceneFilters, // 使用场景配置中的过滤条件
    };

    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}${props.readApiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '读取数据失败');
    }

    // 处理数据 - 支持 data 或 boardData 字段
    let tableData = responseData.data || responseData.boardData || [];

    if (typeof tableData === 'string') {
      try {
        tableData = JSON.parse(tableData);
      } catch (error) {
        console.error('解析数据JSON失败:', error);
        throw new Error('返回的数据格式不正确');
      }
    }

    if (!Array.isArray(tableData)) {
      throw new Error('返回的数据格式不正确，预期是数组');
    }

    // 限制数据量以避免性能问题
    const MAX_DATA_SIZE = 50000;
    if (tableData.length > MAX_DATA_SIZE) {
      console.warn(`数据量过大(${tableData.length})，已限制为${MAX_DATA_SIZE}条`);
      tableData = tableData.slice(0, MAX_DATA_SIZE);
    }

    data.value = tableData.map((item, index) => {
      // 使用已有的唯一标识符，如果没有则生成一个
      const id = item.id || item.board_name || item.SD类型 || index.toString();
      return {
        id,
        ...item,
      };
    });

    // 清除筛选缓存
    dynamicFilterCache.clear();

    // 更新全局AI的上下文（只包含显示的列，并使用经过筛选和搜索后的最终结果）
    tableAiContext.value = JSON.stringify(getDisplayData(filteredData.value), null, 2);

    MessagePlugin.success(responseData.message || '数据加载成功');
    emit('data-loaded', data.value);
  } catch (error) {
    console.error('数据读取过程中出错:', error);
    MessagePlugin.error(error.message || '数据加载失败');
  } finally {
    loading.value = false;
  }
};

const onTableReadFresh = async () => {
  try {
    loading.value = true;

    // 根据后端API_Table_get的期望格式构造请求数据
    // 同时添加user参数

    // 刷新一次表格
    const refreshData = await fetch(`${SERVER_API_URL}/api_data/refresh_task`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 从Pinia store中获取当前用户信息
    const currentUser = userStore.userInfo.name || 'guest';

    // 获取当前场景的过滤条件
    let sceneFilters = {};
    if (currentSceneKey.value && props.sceneConfig) {
      const currentScene = props.sceneConfig.find((scene) => scene.key === currentSceneKey.value);
      if (currentScene && currentScene.filters) {
        sceneFilters = currentScene.filters;
      }
    }

    const requestData = {
      user: currentUser,
      table_name: props.defaultParams.table_name,
      ...props.defaultParams,
      conditions: sceneFilters, // 使用场景配置中的过滤条件
    };

    // 调用后端API读取数据
    const response = await fetch(`${SERVER_API_URL}${props.readApiPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData),
    });

    if (!response.ok) {
      throw new Error(`HTTP错误! 状态码: ${response.status}`);
    }

    const responseData = await response.json();

    if (responseData.status !== 'success') {
      throw new Error(responseData.message || '读取数据失败');
    }

    // 处理数据 - 支持 data 或 boardData 字段
    let tableData = responseData.data || responseData.boardData || [];

    if (typeof tableData === 'string') {
      try {
        tableData = JSON.parse(tableData);
      } catch (error) {
        console.error('解析数据JSON失败:', error);
        throw new Error('返回的数据格式不正确');
      }
    }

    if (!Array.isArray(tableData)) {
      throw new Error('返回的数据格式不正确，预期是数组');
    }

    // 限制数据量以避免性能问题
    const MAX_DATA_SIZE = 50000;
    if (tableData.length > MAX_DATA_SIZE) {
      console.warn(`数据量过大(${tableData.length})，已限制为${MAX_DATA_SIZE}条`);
      tableData = tableData.slice(0, MAX_DATA_SIZE);
    }

    data.value = tableData.map((item, index) => {
      // 使用已有的唯一标识符，如果没有则生成一个
      const id = item.id || item.board_name || item.SD类型 || index.toString();
      return {
        id,
        ...item,
      };
    });

    // 清除筛选缓存
    dynamicFilterCache.clear();

    // 更新全局AI的上下文（只包含显示的列，并使用经过筛选和搜索后的最终结果）
    tableAiContext.value = JSON.stringify(getDisplayData(filteredData.value), null, 2);

    MessagePlugin.success(responseData.message || '数据加载成功');
    emit('data-loaded', data.value);
  } catch (error) {
    console.error('数据读取过程中出错:', error);
    MessagePlugin.error(error.message || '数据加载失败');
  } finally {
    loading.value = false;
  }
};

// 获取只包含显示字段的数据
const getDisplayData = (sourceData) => {
  // 获取所有显示列的字段名（排除序号列、AI列和操作列）
  const displayFields = props.formFields
    // 只显示选中的列（如果selectedColumns为空，则显示所有列）
    // 但始终显示key列（根据isTitle属性判断）
    .filter(
      (field) =>
        field.isTitle === true || selectedColumns.value.length === 0 || selectedColumns.value.includes(field.key),
    )
    // 过滤掉设置了aiTableFilter=true的字段
    .filter((field) => !field.aiTableFilter)
    .map((field) => field.key);

  // 过滤数据，只保留显示的字段
  return sourceData.map((item) => {
    const filteredItem = { id: item.id }; // 始终保留id字段
    displayFields.forEach((field) => {
      if (item.hasOwnProperty(field)) {
        filteredItem[field] = item[field];
      }
    });
    return filteredItem;
  });
};

// 批量导入相关方法
const onBatchImport = () => {
  // 重置状态
  fileList.value = [];
  uploadError.value = '';
  importDialogVisible.value = true;
};

// 处理文件选择变化
const handleFileChange = (files) => {
  uploadError.value = '';
  fileList.value = files;

  // 验证文件格式
  if (files.length > 0) {
    const file = files[0];
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.xlsx')) {
      uploadError.value = '文件格式错误，请选择.xlsx格式的文件';
      fileList.value = []; // 清空错误文件
    }
  }
};

const handleImportSubmit = async () => {
  if (fileList.value.length === 0) {
    uploadError.value = '请先选择文件';
    return;
  }

  if (uploadError.value) {
    return;
  }

  importLoading.value = true;
  uploadError.value = '';

  try {
    const file = fileList.value[0];

    // 读取Excel文件
    const reader = new FileReader();
    const data = await new Promise((resolve, reject) => {
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsArrayBuffer(file.raw);
    });

    // 解析Excel文件
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheetName];

    // 转换为JSON
    const jsonData = XLSX.utils.sheet_to_json(worksheet);

    if (!jsonData || jsonData.length === 0) {
      throw new Error('Excel文件中没有数据');
    }

    // 验证数据结构是否与表单字段匹配
    const expectedHeaders = props.formFields.map((field) => field.label);
    const actualHeaders = Object.keys(jsonData[0]);

    // 检查是否所有Excel列都在表单字段中存在
    const missingHeaders = expectedHeaders.filter((header) => !actualHeaders.includes(header));
    if (missingHeaders.length > 0) {
      throw new Error(`Excel文件缺少以下列: ${missingHeaders.join(', ')}`);
    }

    // 逐行处理数据并保存到后端
    let successCount = 0;
    let failCount = 0;

    for (const row of jsonData) {
      try {
        // 将Excel列名转换为字段键名
        const rowData = {};
        props.formFields.forEach((field) => {
          // 查找Excel中匹配的列名
          const excelColumn = Object.keys(row).find((key) => key === field.label);
          if (excelColumn) {
            // 如果是选择类型字段，尝试将标签转换为值
            if (field.type === 'select' && field.options) {
              const option = field.options.find((opt) => opt.label === row[excelColumn]);
              rowData[field.key] = option ? option.value : row[excelColumn];
            } else {
              rowData[field.key] = row[excelColumn];
            }
          }
        });

        // 从Pinia store中获取当前用户信息
        const currentUser = userStore.userInfo.name || 'guest';

        const requestData = {
          user: currentUser,
          table_name: props.defaultParams.table_name,
          conditions: rowData,
        };

        // 添加默认参数到conditions
        Object.keys(props.defaultParams).forEach((key) => {
          if (key !== 'table_name' && requestData.conditions[key] === undefined) {
            requestData.conditions[key] = props.defaultParams[key];
          }
        });

        // 调用后端API保存数据
        const response = await fetch(`${SERVER_API_URL}${props.saveApiPath}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData),
        });

        if (!response.ok) {
          throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }

        const responseData = await response.json();

        if (responseData.status !== 'success') {
          throw new Error(responseData.message || '保存数据失败');
        }

        successCount++;
      } catch (error) {
        console.error('保存单行数据失败:', error);
        failCount++;
      }
    }

    MessagePlugin.success(`批量导入完成: 成功 ${successCount} 条, 失败 ${failCount} 条`);

    await onTableRead(); // 重新加载数据

    importDialogVisible.value = false;
  } catch (error) {
    console.error('批量导入失败', error);
    uploadError.value = error.message || '批量导入失败';
  }

  importLoading.value = false;
};

// 批量导出功能
const onBatchExport = async () => {
  // 判断是否有数据可导出
  if (data.value.length === 0) {
    MessagePlugin.warning('当前没有数据可导出');
    return;
  }

  try {
    // 根据表单字段配置生成导出数据
    const exportData = data.value.map((row) => {
      const exportRow = {};
      props.formFields.forEach((field) => {
        // 根据字段类型和配置处理数据
        if (field.type === 'select' && field.options) {
          // 如果是选择框类型，获取对应的标签而不是值
          const option = field.options.find((opt) => opt.value === row[field.key]);
          // 限制单元格内容长度以防止Excel超出限制
          exportRow[field.label] = option ? option.label : row[field.key] || '';
        } else if (field.type === 'html' || field.type === 'textarea') {
          // 对于HTML和文本域类型，限制内容长度以防止超出Excel限制
          const content = row[field.key] || '';
          // Excel单元格最大字符数为32767，我们限制为更安全的长度
          exportRow[field.label] = content.length > 30000 ? content.substring(0, 30000) + '...' : content;
        } else {
          // 对于其他类型，限制内容长度并直接使用值
          const content = row[field.key] || '';
          exportRow[field.label] = content.length > 30000 ? content.substring(0, 30000) + '...' : content;
        }
      });
      return exportRow;
    });

    // 创建工作簿和工作表
    const worksheet = XLSX.utils.json_to_sheet(exportData);

    // 动态调整列宽（根据内容长度估算）
    const columnWidths = [];
    const firstRow = exportData[0];
    if (firstRow) {
      Object.keys(firstRow).forEach((key) => {
        // 计算列标题的长度
        const headerWidth = key.length;
        // 计算数据中最长值的长度
        const maxWidth = Math.max(headerWidth, ...exportData.map((row) => (row[key] ? String(row[key]).length : 0)));
        // 设置适当的最大宽度，避免过宽
        columnWidths.push({ wch: Math.min(maxWidth + 2, 50) });
      });
    }
    worksheet['!cols'] = columnWidths;

    // 创建工作簿并添加工作表
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, props.tableTitle || '数据导出');

    // 生成文件名（使用表格标题和日期时间）
    const date = new Date();
    const formattedDate =
      `${date.getFullYear().toString().slice(2)}` +
      `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
      `${date.getDate().toString().padStart(2, '0')}` +
      `${date.getHours().toString().padStart(2, '0')}` +
      `${date.getMinutes().toString().padStart(2, '0')}`;
    const fileName = `${props.tableTitle || '数据'}批量导出_${formattedDate}.xlsx`;

    // 导出文件
    XLSX.writeFile(workbook, fileName);

    // 显示成功信息
    MessagePlugin.success('数据导出成功, 请查看下载文件');
  } catch (error) {
    console.error('数据导出失败:', error);
    MessagePlugin.error('数据导出失败，请重试');
  }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 下载示例文件
const downloadExampleFile = () => {
  try {
    // 创建一个示例数据，使用当前表单字段作为列
    const exampleData = [{}];
    props.formFields.forEach((field) => {
      exampleData[0][field.label] = `[${field.label}示例值]`;
    });

    // 创建工作簿和工作表
    const worksheet = XLSX.utils.json_to_sheet(exampleData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '示例');

    // 导出示例文件
    const fileName = `${props.tableTitle || '数据'}导入示例.xlsx`;
    XLSX.writeFile(workbook, fileName);

    MessagePlugin.success('示例文件下载成功');
  } catch (error) {
    console.error('示例文件生成失败:', error);
    MessagePlugin.error('示例文件生成失败');
  }
};

// 监听窗口大小变化的处理函数
const handleResize = () => {
  tableHeight.value = pubCalculateTableHeight(270);
};

// 生命周期
onMounted(async () => {
  // 如果提供了场景配置，默认选择第一个场景
  if (props.sceneConfig && props.sceneConfig.length > 0) {
    currentSceneKey.value = props.sceneConfig[0].key;
    const defaultScene = props.sceneConfig[0];
    if (defaultScene.columns) {
      selectedColumns.value = [...defaultScene.columns];
    }
    // 应用默认场景的筛选条件
    if (defaultScene.filters) {
      filterValue.value = { ...defaultScene.filters };
    }
  } else {
    // 如果没有场景配置，初始化选中的列（默认全选，但确保key列始终选中）
    const keyField = props.formFields.find((field) => field.isTitle === true);
    selectedColumns.value = keyField
      ? [keyField.key, ...props.formFields.filter((field) => !field.isTitle).map((field) => field.key)]
      : props.formFields.map((field) => field.key);
  }

  tableHeight.value = pubCalculateTableHeight(270);
  window.addEventListener('resize', handleResize);
  onTableRead();
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// 监听配置变化
watch(
  () => props.tableConfig,
  () => {
    // 配置变化时可以重新加载数据
  },
  { deep: true },
);

// 确保key列始终被选中
watch(selectedColumns, (newVal) => {
  // 查找key字段
  const keyField = props.formFields.find((field) => field.isTitle === true);
  // 检查key字段是否在选中列表中
  if (keyField && !newVal.includes(keyField.key)) {
    // 如果没有，则添加到列表中
    selectedColumns.value = [keyField.key, ...newVal];
  }
});
</script>

<style scoped>
.m-table :deep(.table-operations .t-link) {
  margin-right: 8px;
}

.m-table :deep(*) {
  th {
    background-color: #e7e7e7;
    color: #333;
    white-space: nowrap;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
    border-left: none;
    border-right: none;
    line-height: 1.4;
  }

  td {
    background-color: #fefefe;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4;
    border-left: none;
    border-right: none;
  }

  tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
  }

  @media (max-width: 600px) {
    th,
    td {
      padding: 10px 8px;
      font-size: 14px;
    }
  }
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  ::-webkit-scrollbar-track {
    background: transparent;
  }

  ::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 3px;
    opacity: 0.3;
  }

  ::-webkit-scrollbar-thumb:hover {
    background-color: rgba(0, 0, 0, 0.5);
  }

  ::-webkit-scrollbar-button {
    display: none;
  }

  .html {
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 0, 0, 0.3) transparent;
  }

  /* 编辑表单和导入导出样式 */
  .m-table :deep(*) {
    .edit-form .t-form__item {
      margin-bottom: 20px;
    }

    .import-container {
      padding: 16px 0;
    }

    .upload-component {
      margin-bottom: 20px;
    }

    .file-info {
      padding: 12px;
      background-color: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 16px;
    }

    .error-message {
      color: #ff4d4f;
      padding: 8px 0;
      min-height: 24px;
    }

    /* 导入相关样式补充 */
    /* 示例文件说明与下载按钮的容器样式 */
    .example-download {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px dashed #e5e6eb;
    }

    .example-space {
      display: flex; /* 水平布局 */
      align-items: center; /* 垂直居中对齐 */
      gap: 12px; /* 元素间间距，可根据需要调整 */
    }

    .example-space p {
      margin: 0; /* 清除默认外边距 */
      color: #666; /* 可选：调整文字颜色 */
      font-size: 14px; /* 与按钮文字大小保持一致 */
    }

    .example-btn {
      font-size: 14px; /* 与说明文字大小统一 */
      padding-left: 0;
      display: inline-flex;
      align-items: center;
    }

    .mr-1 {
      margin-right: 4px;
    }

    .file-size {
      color: #666;
      font-size: 12px;
      margin-top: 4px;
    }
  }
}
</style>
