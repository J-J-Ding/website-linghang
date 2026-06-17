<template>
    <div class="scene-main">
        <t-space direction="vertical">
            <t-space>
                <t-select
                v-model="selectedBoardOptionList"
                multiple
                filterable
                :clearable="false"
                :min-collapsed-num="1"
                :max="5"
                style="width: 250px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择单板模型"
                label="单板模型: ">
                    <t-option v-for="option in boardOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-cascader
                v-model="selectedFeatureList"
                :options="featureList"
                :filter="pubFilterTreeOptionFun"
                multiple
                filterable
                clearable
                :min-collapsed-num="1"
                value-type="full"
                style="width: 400px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择特性"
                label="特性: "/>
                <t-select
                v-model="selectedSupportOption"
                filterable
                clearable
                style="width: 200px;"
                placeholder="请选择子特性支持情况"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                label="子特性支持情况: "
                @change="handleSupportOptionChange">
                    <t-option v-for="option in supportOptionList" :key="option.id" :value="option.value" :label="option.label" />
                </t-select>
                <t-select
                v-model="selectedStatusOptionList"
                filterable
                clearable
                style="width: 180px;"
                :input-props="{ style: 'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' }"
                placeholder="请选择数据状态"
                label="数据状态: ">
                    <t-option v-for="option in statusOptionList" :key="option" :value="option" :label="option" />
                </t-select>
                <t-button @click="filterData">筛选</t-button>
                <t-button @click="resetFilters">重置</t-button>
                <t-button @click="onExpandAllToggle">{{
                    expandAll ? '收起全部' : '展开全部'
                }}</t-button>
                <t-button @click="onBatchImport">批量导入</t-button>
                <t-button @click="onBatchOutput">批量导出</t-button>
            </t-space>
            <p> </p>
        </t-space>
        <t-enhanced-table
        ref="tableRef"
        row-key="id"
        :columns="tableColumnList"
        :data="tableDataList"
        :tree="{childrenKey: 'childrenList', checkStrictly: false, treeNodeColumnIndex: 3, expandedRowKeys: expandedKeys }"
        :max-height="tableHeight" 
        :bordered="true"
        active-row-type="multiple"
        :hover="true"
        resizable
        @expanded-tree-nodes-change="onExpandedTreeNodesChange"
        >
            <template #index="{ rowIndex }">
                <span>{{ rowIndex + 1 }}</span>
            </template>

            <!-- 使用 footer-summary 插槽来实现交互式且对齐的表尾 -->
             <!-- footer-summary 插槽 -->
            <template #footer-summary>
                <div :key="footerKey">
                    <table style="width: 100%; table-layout: fixed; margin: 0; border: none;">
                        <colgroup>
                            <col 
                            v-for="col in tableColumnList" 
                            :key="col.colKey" 
                            :style="{ width: formatWidth(col.width) }" 
                            />
                        </colgroup>
                        <tbody>
                            <tr 
                            v-for="(row, rowIndex) in footerRows" 
                            :key="`footer-row-${rowIndex}`" 
                            style="background-color: #fafafa;">
                                <td 
                                    v-for="col in tableColumnList" 
                                    :key="`footer-cell-${col.colKey}-${rowIndex}`" 
                                    :style="{
                                    padding: '5px 10px',
                                    textAlign: col.align || 'left',
                                    border: 'none',
                                    boxSizing: 'border-box'
                                    }">
                                    <component :is="row[col.colKey]" v-if="row[col.colKey]"/>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </template>
        </t-enhanced-table>

        <t-dialog
        v-model:visible="importDialogVisible"
        :width="600"
        theme="warning"
        header="批量导入数据">
            <div class="import-container">
                <t-upload
                ref="uploadRef"
                :key="uploadKey"
                :auto-upload="false"
                :on-change="handleFileChange"
                :file-list="fileList"
                :max-size="10 * 1024 * 1024"
                :allow-multiple="false"
                accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                class="upload-component">
                    <t-button variant="outline">选择XLSX文件</t-button>
                </t-upload>

                <div v-if="fileList.length > 0" class="file-info">
                    <p>已选择文件: {{ fileList[0].name }}</p>
                    <p class="file-size">文件大小: {{ formatFileSize(fileList[0].size) }}</p>
                </div>
                <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
                <div class="example-download">
                <!-- 添加 wrap="false" 禁止换行，确保在一行显示 -->
                    <t-space wrap="false" class="example-space">
                        <p>请按照示例文件格式填写数据</p>
                        <t-button
                        variant="text"
                        theme="primary"
                        @click="downloadExampleFile"
                        class="example-btn">
                        <t-icon name="download" size="16" class="mr-1" />
                        下载导入示例文件
                        </t-button>
                    </t-space>
                </div>
            </div>
            <template #footer>
                <t-button @click="cancelImportSubmit">取消</t-button>
                <t-button :loading="importLoading" @click="handleImportSubmit">确认导入</t-button>
            </template>
        </t-dialog>
    </div>
</template>
<script setup lang="jsx">
import { ref, onMounted, computed, nextTick, onBeforeUnmount } from 'vue'; // 引入 computed
import * as XLSX from 'xlsx';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';
import { queryFeatureBoardByParams, queryFeatureBoardBoardList, queryFeatureBoardTree, queryFeatureBoardStatusList, updateFeatureBoardData, importExcelFeatureBoardData, queryFeatureTreeTree, queryFeatureTreeByParams, queryFeatureTreeStatusList, queryFeatureTreeFeatureFirstTypeList} from '@/api/electric.js';
import { debounce } from 'lodash-es';
import { deepClone } from '@/utils/public_function.js';
import { pubBuildTreeWithText, pubFilterTreeOptionFun } from '@/utils/pub';

const router = useRouter();
const user = useUserStore();
// 表格配置
const tableRef = ref();
const expandedKeys = ref([]);
const tableColumnList = ref([]);
const expandAll = ref(false);
const uploadKey = ref(0);
const importLoading = ref(false);
// 固定列配置
const fixedColumns = [
    { colKey: 'index', title: '编号', width: '70', align: 'center' },
    { colKey: 'featureFirstType', title: () => (<div style={{ textAlign: 'center' }}>特性一级分类</div>), width: '100', align: 'left', ellipsis: { theme: 'light', placement: 'bottom',} },
    { colKey: 'featureSecondType', title: () => (<div style={{ textAlign: 'center' }}>特性二级分类</div>), width: '100', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
    { 
      colKey: 'feature', 
      title: () => (<div style={{ textAlign: 'center' }}>特性</div>), 
      width: '300', align: 'left', 
      cell: (_, { row }) => (
          <div style={{ whiteSpace: 'normal' }}>  {/* 允许换行 */}
              {row.feature}
          </div>
        )
      },
    { colKey: 'subFeature', title: () => (<div style={{ textAlign: 'center' }}>子特性</div>), width: '300', align: 'left', ellipsis: { theme: 'light', placement: 'bottom' } },
];
// 数据与状态管理
const tableDataList = ref([]);
const editBoardList = ref([]);
const selectedFeatureList = ref([]);
const featureList = ref([]);
const selectedStatusOptionList = ref([]);
const statusOptionList = ref([]);
const selectedSupportOption = ref([]);
const supportOptionList = ref([{id: 1, label: "支持", value: "2"}, {id: 2, label: "不支持", value: "0"}]);
const selectedBoardOptionList = ref([]);
const boardOptionList = ref([]);
// const footData = ref([]); // 移除 footData
const editingColumns = ref([]); // 存储当前可编辑的列
// const originalDataMap = {}; // 存储编辑前的原始数据 (改为普通对象，因为 reactive 可能导致 footData 更新问题)
const editStateMap = ref(new Map());
const tableHeight = ref('900px');
const importDialogVisible = ref(false);
const uploadRef = ref(null);
const fileList = ref([]);
const uploadError = ref('');
const originData = ref([]);

const footerKey = ref(0);
const forceFooterUpdate = () => footerKey.value++;

const calculateTableHeight = () => {
  // 减去顶部筛选区域、页脚和其他元素的预估高度
  const offset = 230; // 根据实际情况调整这个值
  tableHeight.value = `${window.innerHeight - offset}px`;
};


// 计算属性：用于 footer-summary 插槽获取当前动态字段
const dynamicFieldsForFooter = computed(() => {
    return extractDynamicFields(editBoardList.value);
});

const formatWidth = (width) => {
  if (!width) return '100px';
  if (typeof width === 'number') return `${width}px`;
  return width.endsWith('px') ? width : `${width}px`;
};

const onExpandAllToggle = () => {
  expandAll.value = !expandAll.value;
  expandAll.value ? tableRef.value.expandAll() : tableRef.value.foldAll();
};

// 计算属性：生成页脚行 (依赖于 dynamicFieldsForFooter)
const footerRows = computed(() => {
  return generateFooterRows(dynamicFieldsForFooter.value);
});

// const onRowToggle = (rowIds) => {
//   rowIds.forEach((id) => {
//     // getData 参数为行唯一标识，lodash.get(row, rowKey)
//     const rowData = tableRef.value.getData(id);
//     tableRef.value.toggleExpandData(rowData);
//     // 或者
//     // tableRef.value.toggleExpandData({ rowIndex: rowData.rowIndex, row: rowData.row });
//   });
// };

const onExpandedTreeNodesChange = (expandedTreeNodes) => {
    const uniqueNumbers = Array.from(new Set(expandedTreeNodes)); 
    if(uniqueNumbers.length > 0) {
        expandAll.value = true;
    } else {
        expandAll.value = false;
    }
    expandedKeys.value = uniqueNumbers;
};

// 生成页脚行数据的方法
const generateFooterRows = (dynamicFields) => {
  // 每个动态字段对应一个状态标签和一组按钮
  const statusRow = {}; // 第一行：状态标签
  const actionRow = {}; // 第二行：操作按钮

  dynamicFields.forEach((field) => {
    const fieldKey = field.colKey;
    const isInEdit = editStateMap.value.get(fieldKey);
    const isChecked = field.status.includes("审核中") ? true : false;//false : false;
    const isSupport = selectedSupportOption.value === undefined? false : true;

    // 状态标签
    statusRow[fieldKey] = isChecked ? (
      <t-tag theme={isChecked? "danger" : "success"} style={{ display: 'inline-flex', justifyContent: 'center', width: '100%' }}>
        { field.status }
      </t-tag>
    ):(
      <t-tag theme={isInEdit? "warning" : "success"} style={{ display: 'inline-flex', justifyContent: 'center', width: '100%' }}>
        { isInEdit? "修改中":"正常" }
      </t-tag>
    );

    // 操作按钮
    actionRow[fieldKey] = isChecked || isSupport? null:isInEdit ? (
      <t-space size="small" style={{ display: 'inline-flex', justifyContent: 'center', width: '100%' }}>
        <t-button size="medium" theme="primary" variant="text" onClick={() => handleSaveClick(fieldKey)}>
          保存
        </t-button>
        <t-button size="medium" theme="primary" variant="text" onClick={() => handleCancelEdit(fieldKey)}>
          取消
        </t-button>
      </t-space>
    ) : (
      <t-button
        size="medium"
        theme="primary"
        variant="text"
        style={{ display: 'block', margin: '0 auto' }} // 居中单个按钮
        onClick={() => handleEditClick(fieldKey)}
      >
        修改
      </t-button>
    );
  });

  return [statusRow, actionRow]; // 返回包含两行数据的数组
};

// 从数据中提取动态字段
const extractDynamicFields = (data) => {
    if (!data || data.length === 0) return [];
    
    // 使用 Set 自动去重
    const dynamicFields = new Set();
    
    // 递归处理每个元素及其子元素
    const processItem = (item) => {
        if (item.boardBusiness) {
          dynamicFields.add({
            colKey: item.boardBusiness,
            status: item.status,
          });
        }
    };
    
    // 遍历原始数据
    data.forEach(processItem);
    // 转换为目标格式
    return Array.from(dynamicFields).map(key => ({
        colKey: key.colKey,
        title: key.colKey,
        width: 120,
        align: 'center',
        status: key.status
    }));
};

// 修改原有批量导入方法
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

// 格式化文件大小显示
const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const downloadExampleFile = () => {
    try {
        const exampleFilePath = '/templates/characteristic_single_board.xlsx';
        // 创建下载链接
        const link = document.createElement('a');
        link.href = exampleFilePath;
        link.download = '特性&单板批量导入示例.xlsx'; // 指定下载文件名
        document.body.appendChild(link);
        link.click();
        // 清理
        document.body.removeChild(link);
        MessagePlugin.success('特性&单板批量导入示例文件下载成功，请查看下载文件');
    } catch (error) {
        console.error('特性&单板批量导入示例文件下载失败', error);
        MessagePlugin.error('特性&单板批量导入示例文件失败，请联系管理员');
    }
};

const resetUploadData = () => {
    // 1. 清空文件列表
    fileList.value = []
    // 2. 重置上传组件（如果已挂载）
    uploadKey.value++
};

const cancelImportSubmit = () => {
    resetUploadData()
    importDialogVisible.value = false
};

const handleImportSubmit = async () => {
    if (fileList.value.length === 0) {
        uploadError.value = '请先选择文件';
        return;
    }

    if (uploadError.value) {
        return;
    }

    uploadError.value = '';
    importLoading.value = true;
    try {
        const file = fileList.value[0];
        const formData = new FormData();

        // 构造表单数据
        formData.append('file', file.raw);

        // 调用后端批量导入接口
        const response = await importExcelFeatureBoardData(formData);

        MessagePlugin.success(`${response.message || ''}`);

        resetFilters();
        importDialogVisible.value = false;
    } catch (error) {
        console.error('批量导入失败', error);
        uploadError.value = '批量导入失败';
    } finally {
      importLoading.value = false;
    }
    uploadKey.value++
};


// 批量导出实现
const onBatchOutput = async () => {
    if (tableDataList.value.length === 0) {
        MessagePlugin.warning('当前没有数据可导出');
        return;
    }
    const dynamicFields = getKeydata(editBoardList.value);
    try {
        const flattenData = (data) => {
            let result = [];
            data.forEach(item => {
              const baseItem = {
              '编号': item.index,
              '特性一级分类': item.featureFirstType || '',
              '特性二级分类': item.featureSecondType || '',
              '特性': item.feature || '',
              '子特性': item.subFeature || '',
              // 动态添加 dynamicFields 的键值
              ...dynamicFields.reduce((acc, key) => {
                  acc[key] = item[key] || false; // 如果 item[key] 不存在，默认为空字符串
                  return acc;
              }, {})
            };

                // const dynamicKeys = Object.keys(item).filter(
                //     key => !['index', 'featureFirstType', 'featureSecondType', 'feature', 'subFeature', 'childrenList', ...dynamicFields].includes(key)
                // );

                // console.log("dynamicKeys:", dynamicKeys);

                
                // dynamicKeys.forEach(key => {
                //     baseItem[key] = item[key];
                // });

                result.push(baseItem);

                if (item.childrenList?.length) {
                    result = result.concat(flattenData(item.childrenList));
                }
            });

            return result;
        };

        const exportData = flattenData(tableDataList.value).map((item, index) => ({
            ...item,
            '编号': index + 1
        }));
        // 创建工作簿和工作表
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        
        // 动态生成列宽配置
        const fixedColumns = [
            { wch: 8 },   // 编号
            { wch: 30 },  // 特性一级分类
            { wch: 30 },  // 特性二级分类
            { wch: 30 },  // 特性
            { wch: 30 }  // 子特性
        ];
        
        // 获取动态列的数量（总列数 - 固定列数）
        const dynamicKeyCount = exportData.length > 0 
            ? Object.keys(exportData[0]).length - fixedColumns.length 
            : 0;
        
        // 为每个动态列添加默认宽度20
        const dynamicColumns = Array(dynamicKeyCount).fill({ wch: 20 });
        
        // 合并固定列和动态列配置
        const wscols = [...fixedColumns, ...dynamicColumns];
        worksheet['!cols'] = wscols;

        // 创建工作簿并添加工作表
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, '单板特性批量导出');
        
        // 生成文件名
        const date = new Date();
        const formattedDate = 
          `${date.getFullYear().toString().slice(2)}` +
          `${(date.getMonth() + 1).toString().padStart(2, '0')}` +
          `${date.getDate().toString().padStart(2, '0')}` +
          `${date.getHours().toString().padStart(2, '0')}` +
          `${date.getMinutes().toString().padStart(2, '0')}`;
        const fileName = `单板特性批量导出_${formattedDate}.xlsx`;
        
        // 导出文件
        XLSX.writeFile(workbook, fileName);
        MessagePlugin.success('数据导出成功, 请查看下载文件');
    } catch (error) {
        console.error('数据导出失败:', error);
        MessagePlugin.error('数据导出失败，请重试');
    }
};
// 自动生成动态列配置
/* Started by AICoder, pid:r19baz4ad2642dc14ce10a3860d61f4bf3649abb */
const generateDynamicColumns = (fields) => {
  return fields.map((field) => {
    const colKey = field.colKey;
    
    return {
      colKey,
      title: field.title,
      width: formatWidth(field.width),
      align: 'center',
      cell: (_, { row }) => {
        if (!row) return null;
        
        const isEditable = editStateMap.value.get(colKey);
        const checked = Boolean(row[colKey]);

        const { allChecked, noneChecked, hasChildren } = calculateChildrenStatus(row, colKey);
        const indeterminate = hasChildren && !allChecked && !noneChecked;

        const handleChange = debounce((checked) => {
          // 保存当前展开状态
          // const currentExpandedKeys = [...expandedKeys.value];

          // 更新数据
          updateCheckboxState(
            tableDataList.value,
            row.id,
            colKey,
            checked
          );
          // tableDataList.value = [...tableDataList.value];
          // 恢复展开状态
          // nextTick(() => {
          //   expandedKeys.value = currentExpandedKeys;
          //   onRowToggle(expandedKeys.value);
          // });
          forceFooterUpdate();
        }, 100);

        return hasChildren ? (
          <t-checkbox
            checked={checked}
            indeterminate={indeterminate}
            onChange={handleChange}
            disabled={!isEditable}
          />
        ) : (
          <t-checkbox
            checked={checked}
            onChange={handleChange}
            disabled={!isEditable}
          />
        );
      }
    };
  });
};
/* Ended by AICoder, pid:r19baz4ad2642dc14ce10a3860d61f4bf3649abb */

const updateCheckboxState = (data, targetIndex, field, checked) => {

  const updateNode = (nodes) => {
    for (const node of nodes) {
      if (node.id === targetIndex) {
        node[field] = checked;
        if (node.childrenList) {
          node.childrenList.forEach((child) => {
            child[field] = checked;
          });
        }
        return true;
      }
      
      if (node.childrenList) {
        if (updateNode(node.childrenList)) {
          updateParentState(node, field);
          return true;
        }
      }
    }
    return false;
  };
  
  updateNode(data);
  return data;
};

// 新增：更新父节点状态
const updateParentState = (parent, field) => {
  if (!parent.childrenList) return;
  const allChecked = parent.childrenList.every((child) => child[field]);
  const incompleteChecked = parent.childrenList.some((child) => child[field]);// 不完全勾选也算true
  parent[field] = allChecked || incompleteChecked;
};

const handleEditClick = async (colKey) => {
  //const currentExpandedKeys = [...expandedKeys.value];
  
  // 先将所有编辑状态设置为false
  editStateMap.value.forEach((value, key) => {
    editStateMap.value.set(key, false);
  });
  // 然后设置当前colKey为true
  editStateMap.value.set(colKey, true);

  originData.value = deepClone(tableDataList.value);

  //tableDataList.value = [...tableDataList.value]; //触发表格刷新，达到组件渲染效果，目前仅这种方法刷新表格生效
  forceFooterUpdate();
  MessagePlugin.info(`开始修改 ${colKey} 单板模型`);

  // await nextTick();
  // expandedKeys.value = currentExpandedKeys;
  // onRowToggle(expandedKeys.value);
};

const handleSupportOptionChange = (option) => {
  forceFooterUpdate();
};

const handleSaveClick = async (colKey) => {
  // const currentExpandedKeys = [...expandedKeys.value];
  editStateMap.value.set(colKey, false);
  forceFooterUpdate();
  const diffData = findDiff(originData.value, tableDataList.value, colKey);
  // tableDataList.value = [...tableDataList.value]; //触发表格刷新，达到组件渲染效果，目前仅这种方法刷新表格生效

  try {
        // 保存当前展开状态
        //const currentExpandedKeys = [...expandedKeys.value];
        const response = await updateFeatureBoardData(diffData);

        MessagePlugin.success(`${response.message}`);
        MessagePlugin.success(`${colKey} 单板模型保存成功`);

        filterData();
    } catch (error) {
        console.error(error);
        MessagePlugin.error(`${colKey} 单板模型保存失败，请重试`);
    }

  // await nextTick();
  // expandedKeys.value = currentExpandedKeys;
  // onRowToggle(expandedKeys.value);
};

const convertData = (convertData, colKey) => {
  const data = deepClone(convertData);
  // 遍历每个主项
    return data.map(item => {
        // 如果有 childrenList，则计算主项的 colKey 值
        if (item.childrenList && item.childrenList.length > 0) {
            // 统计子项的 colKey 值情况
            let allTrue = true;
            let allFalse = true;

            for (const child of item.childrenList) {
                const value = child[colKey];
                
                // 检查是否为 true 或 "2"
                if (value !== true && value !== "2") {
                    allTrue = false;
                }
                
                // 检查是否为 false 或 "0"
                if (value !== false && value !== "0") {
                    allFalse = false;
                }

                // 如果已经确定既不全真也不全假，可以提前终止循环
                if (!allTrue && !allFalse) {
                    break;
                }
            }

            // 根据子项情况设置主项的 colKey 值
            if (allTrue) {
                item[colKey] = "2";
            } else if (allFalse) {
                item[colKey] = "0";
            } else {
                item[colKey] = "1";
            }
        }

        // 返回修改后的项
        return item;
    });
};

const findDiff = (oriData, modiData, colKey) => {

  const originalData = deepClone(oriData);
  const modifiedData = deepClone(modiData);
    const diffResults = [];

    // 比较主数组中的项
    for (let i = 0; i < originalData.length; i++) {
        const originalItem = originalData[i];
        const modifiedItem = modifiedData.find(item => item.id === originalItem.id);
        
        if (modifiedItem) {
            // 比较主项的colKey
            if (originalItem[colKey] !== modifiedItem[colKey]) {
                diffResults.push({
                    id: modifiedItem.id,
                    [colKey]: (() => {
                      const children = modifiedItem.childrenList;
                      if (!children.length) return 0;
                      
                      const hasTrue = children.some(child => child[colKey]);
                      const hasFalse = children.some(child => !child[colKey]);
                      
                      return hasTrue && hasFalse ? "1" : hasTrue ? "2" : "0";
                    })()
                });
            }

            // 比较子项的colKey
            if (originalItem.childrenList && modifiedItem.childrenList) {
                for (let j = 0; j < originalItem.childrenList.length; j++) {
                    const originalChild = originalItem.childrenList[j];
                    const modifiedChild = modifiedItem.childrenList.find(child => child.id === originalChild.id);

                    if (modifiedChild && originalChild[colKey] !== modifiedChild[colKey]) {
                        diffResults.push({
                            id: modifiedChild.id,
                            [colKey]: modifiedChild[colKey] ? "2":"0"
                        });
                    }
                }
            }
        }
    }

    return diffResults;
};

const handleCancelEdit = async (colKey) => {
  // const currentExpandedKeys = [...expandedKeys.value];
  editStateMap.value.set(colKey, false);
  forceFooterUpdate();
  // tableDataList.value = [...tableDataList.value]; //触发表格刷新，达到组件渲染效果，目前仅这种方法刷新表格生效
  
  filterData();
  MessagePlugin.info(`已取消 ${colKey} 单板模型修改`);

  // await nextTick();
  // expandedKeys.value = currentExpandedKeys;
  // onRowToggle(expandedKeys.value);
};

// 计算子节点状态
const calculateChildrenStatus = (row, field) => {
    if (!row.childrenList || row.childrenList.length === 0) {
        return { allChecked: row[field], noneChecked: !row[field], hasChildren: false };
    }
    const allChecked = row.childrenList.every(child => child[field]);
    const noneChecked = row.childrenList.every(child => !child[field]);
    return { allChecked, noneChecked, hasChildren: true };
};
// 处理复选框变更
const handleCheckboxChange = (row, checked, field) => {
    // 保存当前展开状态
    const currentExpandedKeys = [...expandedKeys.value];
    
    // 创建数据副本
    const newData = JSON.parse(JSON.stringify(tableDataList.value));
    
    const updateNode = (rows) => {
        for (let i = 0; i < rows.length; i++) {
            if (rows[i].index === row.index) {
                // 更新当前节点
                rows[i][field] = checked;
                
                // 更新所有子节点
                if (rows[i].childrenList && rows[i].childrenList.length > 0) {
                    rows[i].childrenList.forEach(child => {
                        child[field] = checked;
                    });
                }
                
                // 更新父节点状态
                updateParentStatus(newData, rows[i], field);
                return true;
            }
            
            // 递归处理子节点
            if (rows[i].childrenList && rows[i].childrenList.length > 0) {
                if (updateNode(rows[i].childrenList)) {
                    return true;
                }
            }
        }
        return false;
    };
    
    if (updateNode(newData)) {
        tableDataList.value = newData;

        // 使用 nextTick 延迟操作以确保数据更新完成
        nextTick();

        // 恢复展开状态
        expandedKeys.value = currentExpandedKeys;
    }
};
// 更新父节点状态
const updateParentStatus = (rows, childRow, field) => {
    const findParent = (rows, childId) => {
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            if (row.childrenList && row.childrenList.some(child => child.id === childId)) {
                return row;
            }
            if (row.childrenList && row.childrenList.length > 0) {
                const parent = findParent(row.childrenList, childId);
                if (parent) return parent;
            }
        }
        return null;
    };
    const parent = findParent(rows, childRow.id);
    if (!parent) return;
    const { allChecked } = calculateChildrenStatus(parent, field);
    parent[field] = allChecked;
    updateParentStatus(rows, parent, field);
};

// 用于更新表格列和数据的辅助函数
const updateTableColumnsAndData = (newData) => {
    // 保存当前展开状态
    const currentExpandedKeys = [...expandedKeys.value];
    
    // tableDataList.value = newData;
    const dynamicFields = extractDynamicFields(newData);
    tableColumnList.value = [...fixedColumns, ...generateDynamicColumns(dynamicFields)];
    
    // 恢复展开状态
    expandedKeys.value = currentExpandedKeys;
};

// 生命周期钩子
onMounted(async () => {
    if (!user.userInfo.name) {
        MessagePlugin.error('请先登录...');
        router.push('/login');
    }
    try {
        const queryFeatureBoardBoardListResponse = await queryFeatureBoardBoardList();

        boardOptionList.value = queryFeatureBoardBoardListResponse.data || [];
        if(boardOptionList.value.length > 0) {
          selectedBoardOptionList.value[0] = boardOptionList.value[0];
        }

        const relatedBoardModel = selectedBoardOptionList.value.join(',');

        // 构建参数对象，过滤掉空值
        const requestParams = {
          relatedBoardModel: relatedBoardModel,
        };
        const [
            queryFeatureBoardTreeResponse,
            queryFeatureBoardByParamsResponse,
            queryFeatureBoardStatusListResponse,
            //queryFeatureBoardBoardListResponse,
        ] = await Promise.all([
            queryFeatureBoardTree(),
            queryFeatureBoardByParams(requestParams),
            queryFeatureBoardStatusList(),
            //queryFeatureBoardBoardList(),
        ]);
        featureList.value = pubBuildTreeWithText(queryFeatureBoardTreeResponse.data || []);
        const initialData = queryFeatureBoardByParamsResponse.data || [];
        editBoardList.value = queryFeatureBoardByParamsResponse.board || [];
        statusOptionList.value = queryFeatureBoardStatusListResponse.data || [];

        updateTableColumnsAndData(editBoardList.value); // 使用辅助函数初始化

        tableDataList.value = updateParentDynamicKeys(initialData, editBoardList.value);

        calculateTableHeight();
        window.addEventListener('resize', calculateTableHeight);

        // await nextTick();
        // onRowToggle(expandedKeys.value);
        forceFooterUpdate();
    } catch (error) {
        console.error(error); // 打印错误堆栈
        MessagePlugin.error('数据加载失败，请重试');
    }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', calculateTableHeight);
});

const getKeydata = (keys) => {
  const dynamicFields = new Set();
    // 递归处理每个元素及其子元素
    const processItem = (item) => {
      if (item.boardBusiness) {
        dynamicFields.add(item.boardBusiness);
      }
    };
  keys.forEach(processItem);
  return Array.from(dynamicFields);
};

/**
 * 处理数据函数
 * @param {Array} data - 原始数据数组
 * @param {Array} keys - 需要处理的键名数组
 * @returns {Array} - 处理后的数据
 */
const updateParentDynamicKeys = (data, keys) => {
  // 使用 reactive 让返回的数据具有响应性（Vue 3 特性）
  const processedData = deepClone(data);

  const dynamicFields = getKeydata(keys);

  // 遍历 data 数组
  processedData.forEach(item => {
    // 处理当前元素的 keys
    dynamicFields.forEach(key => {
      if (item.hasOwnProperty(key)) {
        if (selectedSupportOption.value === "0") item[key] = 0;
        if (selectedSupportOption.value === undefined) item[key] = Number(item[key]);
        if (selectedSupportOption.value === "2") item[key] = 2;
      }
    });

    // 处理 childrenList
    if (item.childrenList && item.childrenList.length > 0) {
      item.childrenList.forEach(child => {
        dynamicFields.forEach(key => {
          if (child.hasOwnProperty(key)) {
            if (child[key] === "0") child[key] = false;
            if (child[key] === "2") child[key] = true;
          }
        });
      });
    }
  });
  return processedData;
};

const processString = (str) => {
    // 将字符串按逗号分割成数组
    const items = str.split(',');
    // 对每个元素进行处理，去掉最后一个 - 及其后面的字符
    const processedItems = items.map(item => {
        // 使用正则表达式去掉最后一个 - 及其后面的字符
        return item.replace(/-[^-]*$/, '');
    });
    // 将处理后的数组重新拼接成字符串
    return processedItems.join(',');
};

// 筛选数据
const filterData = async () => {
    try {
        if(selectedBoardOptionList.value.length === 0) return MessagePlugin.warning('单板模型不能为空！');

        const featureFirstTypeList = selectedFeatureList.value.map(item => item[0]);
        const featureSecondTypeList = selectedFeatureList.value.map(item => item[1]);
        const featureList = selectedFeatureList.value.map(item => item[2]);
        const subFeatureList = selectedFeatureList.value.map(item => item[3]);

        const relatedBoardModel = selectedBoardOptionList.value.join(',');
        const featureFirstType = [...new Set(featureFirstTypeList)].join(',');
        const featureSecondType = [...new Set(featureSecondTypeList)].join(',');
        const feature = [...new Set(featureList)].join(',');
        const subFeature = [...new Set(subFeatureList)].join(',');
        const status = selectedStatusOptionList.value;
        const relatedFlag = selectedSupportOption.value;

        // 构建参数对象，过滤掉空值
        const requestParams = {};
        if (relatedBoardModel) requestParams.relatedBoardModel = relatedBoardModel;
        if (featureFirstType) requestParams.featureFirstType = processString(featureFirstType);
        if (featureSecondType) requestParams.featureSecondType = processString(featureSecondType);
        if (feature) requestParams.feature = processString(feature);
        if (subFeature) requestParams.subFeature = processString(subFeature);
        if (status) requestParams.status = status;
        if (relatedFlag !== undefined) requestParams.relatedFlag = relatedFlag;
        

        // 保存当前展开状态
        //const currentExpandedKeys = [...expandedKeys.value];
        const response = await queryFeatureBoardByParams(requestParams);
        const filteredData = response.data || [];
        editBoardList.value = response.board || [];

        updateTableColumnsAndData(editBoardList.value);

        tableDataList.value = updateParentDynamicKeys(filteredData, editBoardList.value);

        editStateMap.value.forEach((value, key) => {
          editStateMap.value.set(key, false);
        });
        
        editingColumns.value = [];

        expandAll.value = false;

        
        // 恢复展开状态
        // 强制恢复展开状态
        // await nextTick();
        // expandedKeys.value = currentExpandedKeys;
        // onRowToggle(expandedKeys.value);
        MessagePlugin.success(`共找到 ${filteredData.length} 条数据`);
    } catch (error) {
        console.error(error);
        MessagePlugin.error('筛选失败，请重试');
    }
};
// 重置筛选
const resetFilters = async () => {
    
    selectedBoardOptionList.value = [];
    selectedFeatureList.value = [];
    selectedSupportOption.value = [];
    selectedStatusOptionList.value = [];
    expandedKeys.value = [];
    expandAll.value = false;
    selectedBoardOptionList.value[0] = boardOptionList.value[0];

    await nextTick();
        
    // 如果有表格实例，强制关闭所有展开行
    if (tableRef.value) {
        tableRef.value.foldAll();
    }

    filterData();
    MessagePlugin.info('已重置筛选条件');

    // router.go(0);
};
</script>
<style scoped>
.scene-main {
    padding: 16px;
}
.t-enhanced-table {
    margin-top: 16px;
}

/* 调整标签和按钮的显示样式 - 移除之前的 margin: 0 auto，因为已在 JSX 中处理 */
/*
.t-tag {
    margin: 0 auto;
    display: inline-flex;
}
.t-button {
    margin: 0 auto;
}
*/
/* 表格样式保持不变 */
.scene-main table {
    border-collapse: collapse;
    white-space: pre-line;
    width: 100%;
}

.scene-main /deep/ .t-table__row-full-element {
  padding: 0 !important;
}

.scene-main th {
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
.scene-main td {
    background-color: #fefefe;
    border-bottom: 1px solid #d6d6d6;
    color: #555;
    line-height: 1.4;
    border-left: none;
    border-right: none;
}
.scene-main tr:nth-child(even) td {
    background-color: #f8f8f8;
}
.scene-main tr:hover td {
    background-color: #dbeafe;
    transition: background-color 0.3s ease;
}
@media (max-width: 600px) {
    .scene-main th,
    .scene-main td {
        padding: 10px 8px;
        font-size: 14px;
    }
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
}

.example-btn {
    padding-left: 0;
    display: inline-flex;
    align-items: center;
}


/* 确保表格页脚的表格继承父级样式 */
.scene-main :deep(.t-table__footer) table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin: 0;
  border: none;
}
.scene-main :deep(.t-table__footer) td {
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  /* padding: 5px 10px; */
  background-color: #fafafa;
  vertical-align: middle;
  border-left: none;
  border-right: none;
  box-sizing: border-box;
  text-align: center; /* 将表格单元格内容居中显示 */
}
</style>
