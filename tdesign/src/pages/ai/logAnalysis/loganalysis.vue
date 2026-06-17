<template>
  <t-watermark
    :watermark-content="{
      text: `${headerParams['X-Emp-No']}`,
    }"
    :width="120"
    :height="60"
    :y="120"
    :x="80"
  >
    <div class="log-analysis-tool">
      <!-- 主页面 -->
      <div class="main-container">
        <div class="header">
          <h1>日志分析工具</h1>
          <p class="subtitle">欢迎使用日志分析工具，请选择一个操作。</p>
        </div>
        
        <div class="actions-container">
          <t-card class="action-card" hover-shadow>
            <div class="action-content">
              <div class="icon-container">
                <t-icon name="add" size="40px" />
              </div>
              <h3>创建新的日志分析项目</h3>
              <p>开始一个新的日志分析项目</p>
              <t-button 
                theme="primary" 
                size="large" 
                @click="showNewProjectDialog"
                block
              >
                创建新项目
              </t-button>
            </div>
          </t-card>
          
          <t-card class="action-card" hover-shadow>
            <div class="action-content">
              <div class="icon-container">
                <t-icon name="folder" size="40px" />
              </div>
              <h3>打开现有的分析项目</h3>
              <p>继续处理已有的日志分析项目</p>
              <t-button 
                variant="outline" 
                size="large" 
                @click="showSelectProjectDialog"
                block
              >
                打开项目
              </t-button>
            </div>
          </t-card>
        </div>
        
        <div class="footer">
          <p>版本 1.0.0 | 技术支持</p>
        </div>
      </div>
      
      <!-- 选择项目弹窗 -->
      <t-dialog
        v-model:visible="selectProjectDialogVisible"
        header="选择项目"
        :footer="false"
        :close-on-overlay-click="false"
        width="500px"
        :on-close="closeSelectProjectDialog"
      >
        <div class="select-project-dialog">
          <!-- 搜索框和创建按钮 -->
          <div class="dialog-header">
            <div class="search-container">
              <t-input
                v-model="searchQuery"
                placeholder="搜索项目"
                clearable
                @change="handleSearch"
              >
                <template #prefix-icon>
                  <t-icon name="search" />
                </template>
              </t-input>
            </div>
            <t-button
              v-if="isCreate"
              theme="primary"
              variant="outline"
              @click="showCreateProjectDialog"
              class="create-project-btn"
            >
              <template #icon><t-icon name="add" /></template>
              新建项目
            </t-button>
          </div>
          
          <!-- 项目列表 -->
          <div class="project-list-container">
            <div class="project-list-header">
              <span class="selected-count">
                已选择 {{ selectedProjects.length }} 个项目
              </span>
              <t-button
                variant="text"
                size="small"
                @click="clearSelection"
                v-if="selectedProjects.length > 0"
              >
                清空选择
              </t-button>
            </div>
            
            <div class="project-list">
              <!-- 空状态 -->
              <div v-if="filteredProjects.length === 0 && !searchQuery" class="empty-state">
                <t-icon name="folder-off" size="60px" style="color: var(--td-brand-color-light); margin-bottom: 16px;" />
                <p class="empty-title">暂无项目</p>
                <p class="empty-description">您还没有创建任何项目</p>
                <t-button
                  v-if="isCreate"
                  theme="primary"
                  variant="outline"
                  @click="showCreateProjectDialog"
                  class="create-first-project-btn"
                >
                  <template #icon><t-icon name="add" /></template>
                  创建第一个项目
                </t-button>
              </div>
              
              <!-- 搜索无结果状态 -->
              <div v-else-if="filteredProjects.length === 0 && searchQuery" class="empty-state">
                <t-icon name="search" size="60px" style="color: var(--td-text-color-secondary); margin-bottom: 16px;" />
                <p class="empty-title">未找到匹配的项目</p>
                <p class="empty-description">尝试使用其他关键词搜索或创建新项目</p>
                <t-button
                  theme="primary"
                  variant="outline"
                  @click="showCreateProjectDialog">
                  <template #icon><t-icon name="add" /></template>
                  创建新项目
                </t-button>
              </div>
              
              <!-- 项目列表 -->
              <t-checkbox-group v-else v-model="selectedProjects" class="checkbox-group" @change="handleSingleSelect">
                <div 
                  v-for="project in filteredProjects" 
                  :key="project.project_name"
                  class="project-item"
                >
                  <t-checkbox :value="project.project_name" class="project-checkbox">
                    <div class="project-info">
                      <div class="project-name">{{ project.project_name }}</div>
                      <!-- <div class="project-meta">
                        <span class="project-type">{{ project.type }}</span>
                        <span class="project-date">{{ project.createDate }}</span>
                      </div> -->
                    </div>
                  </t-checkbox>
                  <div class="project-actions">
                    <!-- <t-button
                      variant="text"
                      size="small"
                      @click.stop="editProject(project)"
                    >
                      <template #icon><t-icon name="edit" /></template>
                    </t-button> -->
                    <t-popconfirm
                      theme="danger"
                      content="是否要删除该项目"
                      @confirm="deleteProject(project.project_name)"
                    >
                      <t-button
                        variant="text"
                        size="small"
                        @click.stop
                      >
                        <template #icon>
                          <t-icon name="delete" />
                        </template>
                      </t-button>
                    </t-popconfirm>
                  </div>
                </div>
              </t-checkbox-group>
            </div>
          </div>
          
          <!-- 底部操作按钮 -->
          <div class="dialog-footer">
            <t-button
              variant="outline"
              @click="closeSelectProjectDialog"
            >
              取消
            </t-button>
            <t-button
              theme="primary"
              @click="handleProjectSelection(selectedProjects)"
              :disabled="selectedProjects.length === 0"
            >
              确定
            </t-button>
          </div>
        </div>
      </t-dialog>
      
      <!-- 创建/编辑项目弹窗 -->
      <t-dialog
        v-model:visible="projectFormDialogVisible"
        :header="isEditingProject ? '编辑项目' : '创建新项目'"
        :footer="false"
        :close-on-overlay-click="false"
        width="400px"
      >
        <div class="project-form-dialog">
          <t-form
            ref="projectFormRef"
            :data="projectForm"
            :rules="projectFormRules"
            @submit="handleProjectFormSubmit"
            class="project-form"
          >
            <t-form-item label="项目名称" name="name">
              <t-input
                v-model="projectForm.name"
                placeholder="请输入项目名称"
                clearable
              />
            </t-form-item>
            
            <!-- <t-form-item label="项目类型" name="type">
              <t-select
                v-model="projectForm.type"
                placeholder="请选择项目类型"
                clearable
                :options="projectTypeOptions"
              />
            </t-form-item>
            
            <t-form-item label="项目描述" name="description">
              <t-textarea
                v-model="projectForm.description"
                placeholder="请输入项目描述（可选）"
                :autosize="{ minRows: 3, maxRows: 5 }"
              />
            </t-form-item> -->
            
            <div class="form-footer">
              <t-button
                variant="outline"
                @click="projectFormDialogVisible = false"
              >
                取消
              </t-button>
              <t-button
                theme="primary"
                type="submit"
              >
                {{ isEditingProject ? '保存修改' : '创建项目' }}
              </t-button>
            </div>
          </t-form>
        </div>
      </t-dialog>
      
      <!-- 文件上传弹窗 -->
      <t-dialog
        v-model:visible="uploadDialogVisible"
        :header="`日志上传 (${projectInfo.project_name})`"
        :footer="false"
        :close-on-overlay-click="false"
        placement="center"
        width="900px"
        :on-close="handleCancel"
      >
        <div class="upload-dialog-content-new">
          <!-- 上传区域 -->
          <div class="upload-area-new">
            <!-- 自定义文件选择区域 -->
            <div class="upload-drag-area" @click="triggerFileInput">
              <t-icon name="cloud-upload" size="48px" />
              <p class="upload-drag-text">拖拽文件到此处或 <span class="upload-select-text">选择文件</span></p>
              <input
                type="file"
                ref="fileInputRef"
                multiple
                @change="handleFileSelect"
                style="display: none"
                accept=".log,.txt,.json,.csv,.zip,.xlsx,.xls"
              />
            </div>
            
            <div class="upload-section">
              <div class="section-header">
                <h4>待上传文件列表 ({{ pendingFiles.length }}个)</h4>
                <div class="section-actions">
                  <t-button variant="text" size="small" @click="clearPendingFiles" :disabled="pendingFiles.length === 0 || isUploading">
                    清空
                  </t-button>
                  <t-button
                    theme="primary"
                    size="small"
                    @click="uploadSelectedFiles"
                    :disabled="pendingFiles.length === 0 || isUploading"
                  >
                    上传
                  </t-button>
                </div>
              </div>
              
              <div class="file-list-section" v-if="pendingFiles.length > 0">
                <div class="file-item-new" v-for="(file, index) in pendingFiles" :key="file.id">
                  <div class="file-info-new">
                    <t-icon name="file" class="file-icon-new" />
                    <div>
                      <span class="file-name-new">{{ file.name }}</span>
                      <div class="file-size">
                        {{ formatFileSize(file.size) }}
                      </div>
                      <div class="file-status" v-if="file.status === 'uploading'">
                        <t-icon name="loading" size="14px" style="margin-right: 4px;" />
                        <span class="uploading-text">上传中 {{ file.progress || 0 }}%</span>
                      </div>
                      <div class="file-status" v-if="file.status === 'success'">
                        <t-icon name="check-circle-filled" size="14px" style="color: var(--td-success-color); margin-right: 4px;" />
                        <span class="success-text">上传成功</span>
                      </div>
                      <div class="file-status" v-if="file.status === 'fail'">
                        <t-icon name="error-circle-filled" size="14px" style="color: var(--td-error-color); margin-right: 4px;" />
                        <span class="error-text">上传失败</span>
                      </div>
                    </div>
                  </div>
                  <t-button variant="text" size="small" @click="removePendingFile(index)" :disabled="file.status === 'uploading'">
                    <template #icon><t-icon name="close" /></template>
                  </t-button>
                </div>
              </div>
              
              <div v-else class="empty-state-new">
                <p>暂无待上传文件</p>
              </div>
            </div>
            
            <div class="upload-section">
              <div class="section-header">
                <h4>已上传成功的文件 ({{ uploadedFiles.length }}个)</h4>
                <div class="section-actions">
                  <t-popconfirm
                    theme="danger"
                    content="是否要清空所有上传文件？"
                    @confirm="clearuploadedFiles"
                  >
                    <t-button variant="text" size="small" :disabled="uploadedFiles.length === 0 || isUploading">
                      清空
                    </t-button>
                  </t-popconfirm>
                </div>
              </div>
              
              <div v-if="uploadedFiles.length > 0" class="file-list-section">
                <div v-for="(file, index) in uploadedFiles" :key="file.id" class="file-item-new">
                  <div class="file-info-new">
                    <t-icon name="file" class="file-icon-new uploaded-icon" />
                    <div>
                      <span class="file-name-new">{{ file.name }}</span>
                      <div class="file-size">
                        {{ formatFileSize(file.size) }}
                      </div>
                      <div class="file-status">
                        <t-icon name="check-circle-filled" size="14px" style="color: var(--td-success-color); margin-right: 4px;" />
                        <span class="success-text">上传成功</span>
                        <span class="upload-time">{{ file.uploadTime }}</span>
                      </div>
                    </div>
                  </div>
                  <t-popconfirm
                    theme="danger"
                    content="是否要删除该上传文件？"
                    @confirm="removeUploadedFile(index)"
                  >
                    <t-button variant="text" size="small">
                      <template #icon><t-icon name="delete" /></template>
                    </t-button>
                  </t-popconfirm>
                </div>
              </div>
              
              <div v-else class="empty-state-new">
                <p>暂无已上传文件</p>
              </div>
            </div>
          </div>
          
          <!-- 上传进度 -->
          <div v-if="isUploading" class="upload-progress-new">
            <div class="progress-header">
              <span>正在上传文件 ({{ currentUploadIndex + 1 }}/{{ totalUploadCount }})</span>
              <!-- <span>{{ overallProgress }}%</span> -->
            </div>
            <t-progress :percentage="overallProgress" />
            <p class="upload-status">上传中，请勿关闭窗口...</p>
          </div>
          
          <!-- 底部操作按钮 -->
          <div class="dialog-footer-new">
            <t-button
              theme="primary"
              size="large"
              :loading="isParsing"
              @click="startDataParsing"
              :disabled="uploadedFiles.length === 0 || isUploading"
              block
            >
              开始解析数据
            </t-button>
          </div>
          <div class="dialog-footer-old">
            <t-button
              variant="outline"
              size="large"
              @click="jumpChannelAlarmURL(projectInfo)"
              block
            >
              直接跳转
            </t-button>
          </div>
        </div>
      </t-dialog>

      <!-- 项目创建成功提示 -->
      <t-dialog
        v-model:visible="successDialogVisible"
        header="解析成功"
        :footer="false"
        :close-on-overlay-click="true"
        width="400px"
      >
        <div class="success-content">
          <div class="success-icon">
            <t-icon name="check-circle" size="60px" style="color: var(--td-success-color)" />
          </div>
          <h3>数据已解析</h3>
          <p>您已完成解析项目数据，请点击完成结束流程。</p>
          <div class="success-actions">
            <t-button theme="primary" @click="finishProject(projectInfo)">完成</t-button>
          </div>
        </div>
      </t-dialog>
    </div>
  </t-watermark>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue';
import {
  MessagePlugin,
} from 'tdesign-vue-next';
import { Utils } from "@/utils/utils";
import { getProjectList, uploadFileList, addProjectList, deleteProjectList, editProjectList, queryDataParse, getProjectFileList, deleteUploadFile } from "@/api/analysis";
import { v4 as uuidv4 } from 'uuid';
const headerParams = Utils.getRDCHeader();

// 状态管理
const selectProjectDialogVisible = ref(false);
const projectFormDialogVisible = ref(false);
const uploadDialogVisible = ref(false);
const successDialogVisible = ref(false);
const isProjectCreated = ref(false);
const isUploading = ref(false);
const isParsing = ref(false);
const overallProgress = ref(0);
const currentUploadIndex = ref(0);
const totalUploadCount = ref(0);
const fileInputRef = ref(null);
const projectFormRef = ref(null);
const pendingFiles = ref([]);
const uploadedFiles = ref([]);
const isCreate = ref(true);
const projectNum = ref(0);
// 搜索和选择相关
const searchQuery = ref('');
const selectedProjects = ref([]); // 存储选中的项目ID
const projectInfo = ref({});
// 项目类型选项
const projectTypeOptions = [
  { label: 'Web应用日志', value: 'Web应用日志' },
  { label: '服务器日志', value: '服务器日志' },
  { label: '数据库日志', value: '数据库日志' },
  { label: '安全日志', value: '安全日志' },
  { label: '网络日志', value: '网络日志' },
  { label: '应用监控日志', value: '应用监控日志' },
  { label: '系统日志', value: '系统日志' },
  { label: '业务日志', value: '业务日志' },
];

// 项目表单
const projectForm = reactive({
  id: '',
  name: '',
  type: '',
  description: '',
  createDate: '',
});

// 表单验证规则
const projectFormRules = {
  name: [
    { required: true, message: '请输入项目名称', type: 'error' },
    { max: 50, message: '项目名称不能超过50个字符', type: 'warning' },
  ],
  // type: [
  //   { required: true, message: '请选择项目类型', type: 'error' },
  // ],
};

// 是否正在编辑项目
const isEditingProject = ref(false);

// 模拟项目数据 - 初始为空
const projects = ref([]);
const visible = ref(false);
// 从本地存储加载项目数据
onMounted(() => {
  uploadedFiles.value = [];
});

// 过滤后的项目列表
const filteredProjects = computed(() => {
  if (!searchQuery.value) {
    return projects.value;
  }
  const query = searchQuery.value.toLowerCase();
  return projects.value.filter((project) =>
    project.project_name.toLowerCase().includes(query)
  );
});

const showNewProjectDialog = async () => {
  isCreate.value = true;
  projects.value = await getProjectData();
  selectProjectDialogVisible.value = true;
};

const getProjectData = async () => {
  try {
    const params = {
      get_total: 0,
      enable_limit: 0,
      order: 'desc',
    };
    const response = await getProjectList(params);
    const projectInfo = response.data;
    // const projectInfo = transformProjects(response.data);
    return projectInfo;
  } catch (error) {
    MessagePlugin.error('获取项目列表失败，请重试');
    return [];
  }
};

const transformProjects = (projects) => {
  return projects.map((project) => {
    // 使用项目ID作为基础生成更稳定的ID
    // const baseId = project.id.toString().padStart(4, '0');

    return {
      id: project.id,
      name: project.project_name,
      type: project.project_type,
      description: project.project_depict || '',
      createDate: project.create_time ? project.create_time.split(' ')[0] : '',
    };
  });
};

// 显示选择项目弹窗
const showSelectProjectDialog = async () => {
  isCreate.value = false;
  projects.value = await getProjectData();
  selectProjectDialogVisible.value = true;
};

// 关闭选择项目弹窗
const closeSelectProjectDialog = () => {
  selectedProjects.value = [];
  selectProjectDialogVisible.value = false;
  clearSelection();
  searchQuery.value = '';
};

// 显示创建项目弹窗
const showCreateProjectDialog = () => {
  resetProjectForm();
  isEditingProject.value = false;
  projectFormDialogVisible.value = true;

  // 重置表单验证状态
  nextTick(() => {
    if (projectFormRef.value) {
      projectFormRef.value.reset();
    }
  });
};

const handleSingleSelect = (value) => {
  // 如果选中多个，只保留最后一个
  if (Array.isArray(value) && value.length > 1) {
    selectedProjects.value = [value[value.length - 1]];
  }
};

// 重置项目表单
const resetProjectForm = () => {
  projectForm.id = '';
  projectForm.project_name = '';
  projectForm.type = '';
  projectForm.description = '';
  projectForm.createDate = '';
};

// 编辑项目
const editProject = (project) => {
  isEditingProject.value = true;
  Object.assign(projectForm, {
    id: project.id,
    name: project.name,
    type: project.type,
    description: project.description || '',
    createDate: project.createDate,
  });
  projectFormDialogVisible.value = true;
};

// 删除项目
const deleteProject = async (projectId) => {
  const project = projects.value.find(p => p.project_name === projectId);
  if (!project) return;
  
  await deleteProjectData(projectId);
};

const addProjectData = async (projectForm) => {
  try {
        const params = {
          project_name: projectForm.name,
          // project_type: projectForm.type,
          // project_depict: projectForm.description,

        }
        await addProjectList(params);
        MessagePlugin.success(`项目 "${projectForm.name}" 创建成功`);
    } catch (error) {
        MessagePlugin.error('获取项目列表失败，请重试');
    }
}; 

const generateId = () => {
  const timestamp = Date.now(); // 1740642345678
  const random = Math.random().toString(36).substring(2, 8); // 'x5myw6'
  return `${timestamp}_${random}`;
};

const editProjectData = async (projectForm) => {
  try {
    const params = {
      // id: projectForm.id,
      project_name: projectForm.name,
      // project_type: projectForm.type,
      // project_depict: projectForm.description,
    };
    const response = await editProjectList(params);
    if (response.code > -1) {
      const index = projects.value.findIndex((p) => p.project_name === projectForm.name);
      if (index > -1) {
        projects.value[index] = { ...projectForm };
      }
      MessagePlugin.success(`${response.data}`);
    } else {
      MessagePlugin.warning(`${response.data}`);
    }
  } catch (error) {
    MessagePlugin.error('编辑项目失败，请重试');
  }
};

const deleteProjectData = async (projectId) => {
  try {
    const params = {
      project_name: projectId,
    };
    const response = await deleteProjectList(params);
    if (response.code > -1) {
      // 从选中列表中移除
      const index = selectedProjects.value.indexOf(projectId);
      if (index > -1) {
        selectedProjects.value.splice(index, 1);
      }
      // 从项目列表中移除
      projects.value = projects.value.filter((p) => p.project_name !== projectId);
      MessagePlugin.success(`${response.data}`);
    } else {
      MessagePlugin.warning(`${response.data}`);
    }
  } catch (error) {
    MessagePlugin.error('删除项目失败，请重试');
  }
};

// 处理项目表单提交
const handleProjectFormSubmit = async ({ validateResult, firstError }) => {
  if (validateResult === true) {
    if (isEditingProject.value) {
      // 更新现有项目
      await editProjectData(projectForm);
    } else {
      await addProjectData(projectForm);
      projects.value = await getProjectData();
    }

    projectFormDialogVisible.value = false;
    resetProjectForm();
  } else {
    console.log('Validate Errors: ', firstError, validateResult);
    MessagePlugin.warning(firstError);
  }
};

// 清空选择
const clearSelection = () => {
  selectedProjects.value = [];
};

// 处理项目选择
const handleProjectSelection = async (data) => {
  if (data.length === 0) {
    MessagePlugin.error('请至少选择一个项目');
    return;
  }

  // 获取选中的项目信息
  const selectedProjectNames = data.map((id) => {
    const project = projects.value.find((p) => p.project_name === id);
    projectInfo.value = project;
    return project?.name || id;
  });
  const file = selectedProjectNames.join(', ');
  uploadedFiles.value = await getUploadFile(file);

  MessagePlugin.success(`已选择项目: ${file}`);
  // 关闭选择项目弹窗
  closeSelectProjectDialog();
  selectedProjects.value = [];
  // 显示上传弹窗
  uploadDialogVisible.value = true;
};

const getUploadFile = async (name) => {
  try {
    const params = {
      project_name: name,
    };
    const response = await getProjectFileList(params);
    return response.data;
  } catch (error) {
    MessagePlugin.error('查询文件失败，请重试');
  }
};

const deleteUploadFiles = async (name, file, type, index) => {
  try {
    const params = {
      project_name: name,
      file_name: file,
      type: type
    };
    const response = await deleteUploadFile(params);
    if (response.code >= 0 && type === 0) {
      MessagePlugin.success('删除成功');
      uploadedFiles.value = [];
    } else if (response.code >= 0 && type === 1) {
      MessagePlugin.success('删除成功');
      uploadedFiles.value.splice(index, 1);
    } else {
      MessagePlugin.error(`删除失败，${ response.data }`);
    }
  } catch (error) {
    MessagePlugin.error('删除文件失败，请重试');
  }
};

// 处理搜索
const handleSearch = () => {
  console.log('搜索项目:', searchQuery.value);
};

// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value.click();
};

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files);

  if (files.length === 0) return;

  // 添加文件到待上传列表
  files.forEach((file) => {
    // 检查是否已存在同名文件
    const exists = pendingFiles.value.some((f) => f.name === file.name && f.size === file.size);
    if (!exists) {
      pendingFiles.value.push({
        id: `pending_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: file.size,
        rawFile: file, // 保存原始File对象
        status: 'pending', // pending, uploading, success, fail
        progress: 0,
      });
    }
  });

  // 清空input以便再次选择相同文件
  event.target.value = '';

  MessagePlugin.success(`已添加 ${files.length} 个文件到待上传列表`);
};

// 模拟上传单个文件
const uploadMultipleFiles = async (files) => {
  return new Promise(async (resolve, reject) => {
    try {
      // 创建 FormData 对象
      const formData = new FormData();
      
      // 添加项目名称
      formData.append('project_name', projectInfo.value.project_name);
      
      // 添加所有文件到 FormData（使用相同的字段名）
      files.forEach((file, index) => {
        if (file.status === 'uploading') {
          // 使用相同的字段名，后端可以通过数组方式接收
          formData.append('files', file.rawFile);
          // 或者使用不同的字段名
          // formData.append(`file_${index}`, file.rawFile);
        }
      });
      
      // 如果需要添加其他参数，可以在这里添加
      // formData.append('project_id', selectedProjectId);
      
      // 模拟整体进度更新（因为原生 fetch/xhr 不支持进度监听，这里用模拟进度）
      const simulateProgress = () => {
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 8; // 缓慢增加
          if (progress >= 95) {
            progress = 95;
            clearInterval(interval);
          }
          
          // 更新所有文件进度
          files.forEach(file => {
            if (file.status === 'uploading') {
              const pendingFile = pendingFiles.value.find(f => f.id === file.id);
              if (pendingFile) {
                pendingFile.progress = Math.floor(progress);
              }
            }
          });
          
          // 更新整体进度
          overallProgress.value = Math.floor(progress);
        }, 300);
        
        return interval;
      };
      
      const progressInterval = simulateProgress();
      
      // 调用批量上传接口
      const response = await uploadFileList(formData);
      
      // 清除进度模拟
      clearInterval(progressInterval);
      
      // 检查响应结果
      if (response.data && Array.isArray(response.data)) {
        // 假设后端返回每个文件的上传结果数组
        response.data.forEach((result, index) => {
          const file = files[index];
          if (file) {
            const pendingFile = pendingFiles.value.find(f => f.id === file.id);
            if (pendingFile) {
              if (result.success) {
                // 上传成功
                pendingFile.status = 'success';
                pendingFile.progress = 100;
                
                // 添加到已上传文件列表
                const uploadedFile = {
                  id: `uploaded_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                  name: file.name,
                  size: file.size,
                  uploadTime: new Date().toLocaleTimeString(),
                  status: 'success',
                  response: result.data,
                };
                uploadedFiles.value.unshift(uploadedFile);
              } else {
                // 上传失败
                pendingFile.status = 'fail';
                pendingFile.progress = 0;
                MessagePlugin.error(`文件 ${file.name} 上传失败: ${result.message || '未知错误'}`);
              }
            }
          }
        });
      } else {
        // 如果后端返回统一成功，将所有文件标记为成功
        files.forEach(file => {
          const pendingFile = pendingFiles.value.find(f => f.id === file.id);
          if (pendingFile && pendingFile.status === 'uploading') {
            pendingFile.status = 'success';
            pendingFile.progress = 100;
            
            // 添加到已上传文件列表
            const uploadedFile = {
              id: `uploaded_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              name: file.name,
              size: file.size,
              uploadTime: new Date().toLocaleTimeString(),
              status: 'success',
              response: response.data,
            };
            uploadedFiles.value.unshift(uploadedFile);
          }
        });
      }
      
      // 更新整体进度为100%
      overallProgress.value = 100;
      
      // MessagePlugin.success(`批量上传完成，共 ${files.length} 个文件`);
      resolve(response);
      
    } catch (error) {
      console.error('批量上传失败:', error);
      
      // 将所有上传中的文件标记为失败
      files.forEach(file => {
        const pendingFile = pendingFiles.value.find(f => f.id === file.id);
        if (pendingFile && pendingFile.status === 'uploading') {
          pendingFile.status = 'fail';
          pendingFile.progress = 0;
        }
      });
      
      // 更新整体进度
      overallProgress.value = 0;
      
      MessagePlugin.error(`批量上传失败: ${error.message || '未知错误'}`);
      reject(error);
    }
  });
};

const uploadSingleFileWithProgress = async (file) => {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file.rawFile);
    
    // 使用 axios 配置，需要修改 request.js 支持进度监听
    // 或者在当前文件直接使用 axios
    import('axios').then(axios => {
      axios.default({
        method: 'post',
        url: '/project_manage/upload_and_parse',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total > 0) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            
            // 更新文件进度
            const pendingFile = pendingFiles.value.find((f) => f.id === file.id);
            if (pendingFile) {
              pendingFile.progress = percentCompleted;
            }
            
            // 更新整体进度
            updateOverallProgress();
          }
        },
      })
      .then(response => {
        // 更新文件状态为成功
        const pendingFile = pendingFiles.value.find(f => f.id === file.id);
        if (pendingFile) {
          pendingFile.status = 'success';
          pendingFile.progress = 100;
        }
        
        // 添加到已上传文件列表
        const uploadedFile = {
          id: `uploaded_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name: file.name,
          size: file.size,
          uploadTime: new Date().toLocaleTimeString(),
          status: 'success',
          response: response.data,
        };
        
        uploadedFiles.value.unshift(uploadedFile);
        
        MessagePlugin.success(`文件 ${file.name} 上传成功`);
        resolve({
          success: true,
          file: uploadedFile,
          response: response.data,
        });
      })
      .catch(error => {
        // 更新文件状态为失败
        const pendingFile = pendingFiles.value.find(f => f.id === file.id);
        if (pendingFile) {
          pendingFile.status = 'fail';
        }
        
        MessagePlugin.error(`文件 ${file.name} 上传失败: ${error.message || '未知错误'}`);
        reject(error);
      })
      .finally(() => {
        // 更新整体进度
        updateOverallProgress();
      });
    });
  });
};

// 更新整体上传进度
const updateOverallProgress = () => {
  if (pendingFiles.value.length === 0) {
    overallProgress.value = 0;
    return;
  }

  const totalFiles = pendingFiles.value.length;
  const completedFiles = pendingFiles.value.filter((f) => f.status === 'success').length;
  const uploadingFiles = pendingFiles.value.filter((f) => f.status === 'uploading');

  let totalProgress = completedFiles * 100;

  if (uploadingFiles.length > 0) {
    const uploadingProgress = uploadingFiles.reduce((sum, file) => sum + (file.progress || 0), 0);
    totalProgress += uploadingProgress;
  }

  overallProgress.value = Math.floor(totalProgress / totalFiles);
};

// 上传选中的文件
const uploadSelectedFiles = async () => {
  if (pendingFiles.value.length === 0) {
    MessagePlugin.error('没有待上传的文件');
    return;
  }

  isUploading.value = true;
  overallProgress.value = 0;
  totalUploadCount.value = pendingFiles.value.length;

  // 标记所有文件为上传中状态
  pendingFiles.value.forEach((file) => {
    if (file.status === 'pending') {
      file.status = 'uploading';
      file.progress = 0;
    }
  });

  try {
    // 批量上传文件
    await uploadMultipleFiles(pendingFiles.value);
  } catch (error) {
    console.error('批量上传失败:', error);
    MessagePlugin.error('批量上传失败');
  } finally {
    // 上传完成
    isUploading.value = false;
  }

  // 统计上传结果
  const successCount = pendingFiles.value.filter((f) => f.status === 'success').length;
  const failCount = pendingFiles.value.filter((f) => f.status === 'fail').length;

  // 移除已成功的文件
  pendingFiles.value = pendingFiles.value.filter((f) => f.status !== 'success');

  if (successCount > 0) {
    MessagePlugin.success(`成功上传 ${successCount} 个文件`);
  }

  if (failCount > 0) {
    MessagePlugin.warning(`${failCount} 个文件上传失败`);
  }

};

// 清空待上传文件
const clearPendingFiles = async () => {
  if (pendingFiles.value.length === 0) {
    MessagePlugin.info('待上传文件列表已为空');
    return;
  }

  // 如果正在上传，不能清空
  if (isUploading.value) {
    MessagePlugin.warning('上传进行中，请等待上传完成后再清空');
    return;
  }
  pendingFiles.value = [];
  MessagePlugin.success('已清空待上传文件列表');
};

const handleCancel = () => {
  clearPendingFiles();
  uploadedFiles.value = [];
  uploadDialogVisible.value = false;
};

const clearuploadedFiles = async () => {
  if (uploadedFiles.value.length === 0) {
    MessagePlugin.info('已上传成功文件列表已为空');
    return;
  }

  // 如果正在上传，不能清空
  if (isUploading.value) {
    MessagePlugin.warning('上传进行中，请等待上传完成后再清空');
    return;
  }
  await deleteUploadFiles(projectInfo.value.project_name, null, 0, null);
  MessagePlugin.success('已清空上传成功文件列表');
};

// 移除单个待上传文件
const removePendingFile = (index) => {
  const file = pendingFiles.value[index];

  // 如果正在上传，不能移除
  if (file.status === 'uploading') {
    MessagePlugin.warning('文件上传中，无法移除');
    return;
  }

  pendingFiles.value.splice(index, 1);
  MessagePlugin.info(`已移除文件: ${file.name}`);
};

// 移除已上传文件
const removeUploadedFile = async (index) => {
  await deleteUploadFiles(projectInfo.value.project_name, uploadedFiles.value[index].name, 1, index);
  MessagePlugin.info(`已删除已上传文件: ${file.name}`);
};

const jumpChannelAlarmURL = (data) => {
  // 构建URL参数
  const params = new URLSearchParams({
    // id: data.id,
    name: data.project_name,
    // type: data.type,
    // description: data.description,
    // createDate: data.createDate,
  }).toString();
  const baseUrl = Utils.getBaseUrl();
  // 打开新页面并传递数据
  window.open(`${baseUrl}/quality/logAnalysis/channelAlarm?${params}`, '_blank');
};

// 开始解析数据
const startDataParsing = async () => {
  if (uploadedFiles.value.length === 0) {
    MessagePlugin.error('请先上传文件');
    return;
  }
  if (isUploading.value) {
    MessagePlugin.warning('文件上传中，请等待上传完成后再解析');
    return;
  }
  isParsing.value = true;

  try {
    const params = {
      project_name: projectInfo.value.project_name,
    };
    const response = await queryDataParse(params);
    if (response.code === 0) {
      // 关闭上传弹窗
      uploadDialogVisible.value = false;
      // 显示成功提示
      setTimeout(() => {
        successDialogVisible.value = true;
        // isProjectCreated.value = true;
      }, 300);
    } else {
      MessagePlugin.error(`${response.data}`);
    }
  } catch (error) {
    console.error('解析失败:', error);
    // MessagePlugin.error('解析失败');
  } finally {
    isParsing.value = false;
  }
};

const finishProject = (project) => {
  successDialogVisible.value = false;
  jumpChannelAlarmURL(project);
};
// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '未知大小';
  if (size < 1024) return size + ' B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB';
  return (size / (1024 * 1024)).toFixed(2) + ' MB';
};
</script>

<style scoped>
/* 原有样式保持不变 */
.log-analysis-tool {
  min-height: 85vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.main-container {
  max-width: 1200px;
  width: 100%;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 70px;
}

.header {
  text-align: center;
  margin-bottom: 60px;
}

.header h1 {
  font-size: 36px;
  color: #1f2d3d;
  margin-bottom: 10px;
  font-weight: 700;
}

.subtitle {
  font-size: 18px;
  color: #5e6d82;
  margin-top: 0;
}

.actions-container {
  display: flex;
  gap: 40px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 60px;
}

.action-card {
  width: 320px;
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.action-card:hover {
  transform: translateY(-5px);
}

.action-content {
  text-align: center;
  padding: 20px;
}

.icon-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  border-radius: 50%;
  color: white;
}

.action-content h3 {
  font-size: 20px;
  color: #1f2d3d;
  margin-bottom: 10px;
}

.action-content p {
  color: #5e6d82;
  margin-bottom: 25px;
}

.footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #eaeaea;
  color: #8492a6;
  font-size: 14px;
}

/* 选择项目弹窗样式 */
.select-project-dialog {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.dialog-header {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: flex-start;
}

.search-container {
  flex: 1;
}

.create-project-btn {
  white-space: nowrap;
}

.project-list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.project-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e0e0e0;
}

.selected-count {
  font-size: 14px;
  color: #0052d9;
  font-weight: 500;
}

.project-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.checkbox-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0px;
}

.project-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.project-item:last-child {
  border-bottom: none;
}

.project-item:hover {
  background-color: #f9f9f9;
}

.project-checkbox {
  flex: 1;
  display: flex;
  align-items: center;
}

.project-info {
  flex: 1;
  margin-left: 12px;
}

.project-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2d3d;
  margin-bottom: 4px;
}

.project-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #5e6d82;
}

.project-type {
  background-color: #ecf2fe;
  color: #0052d9;
  padding: 2px 6px;
  border-radius: 3px;
}

.project-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.project-item:hover .project-actions {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  padding: 20px;
  text-align: center;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: #1f2d3d;
  margin-bottom: 8px;
}

.empty-description {
  font-size: 14px;
  color: #8492a6;
  margin-bottom: 20px;
  max-width: 300px;
}

.create-first-project-btn {
  margin-top: 10px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

/* 项目表单弹窗样式 */
.project-form-dialog {
  padding: 0;
}

.project-form {
  padding: 10px 0;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

/* 新的上传弹窗样式 */
.upload-dialog-content-new {
  padding: 10px 0;
  /* max-height: 500px; */
  overflow-y: auto;
}

.upload-area-new {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-drag-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border: 2px dashed #d1d9e6;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
}

.upload-drag-area:hover {
  border-color: #0052d9;
  background-color: #ecf2fe;
}

.upload-drag-text {
  margin-top: 12px;
  font-size: 16px;
  color: #1f2d3d;
  text-align: center;
}

.upload-select-text {
  color: #0052d9;
  font-weight: 600;
}

.upload-section {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.section-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2d3d;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.file-list-section {
  max-height: 150px;
  overflow-y: auto;
  padding: 8px 0;
}

.file-item-new {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  transition: background-color 0.2s;
}

.file-item-new:hover {
  background-color: #f9f9f9;
}

.file-info-new {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex: 1;
}

.file-icon-new {
  color: #0052d9;
  font-size: 20px;
  margin-top: 2px;
}

.uploaded-icon {
  color: var(--td-success-color);
}

.file-name-new {
  font-size: 14px;
  color: #1f2d3d;
  word-break: break-all;
  display: block;
}

.file-size {
  font-size: 12px;
  color: #8492a6;
  margin-top: 2px;
}

.file-status {
  display: flex;
  align-items: center;
  margin-top: 2px;
  font-size: 12px;
}

.success-text {
  color: var(--td-success-color);
}

.uploading-text {
  color: #0052d9;
}

.error-text {
  color: var(--td-error-color);
}

.upload-time {
  color: #8492a6;
  margin-left: 8px;
  font-size: 11px;
}

.empty-state-new {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  color: #8492a6;
  font-size: 14px;
}

.dialog-footer-new {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.dialog-footer-old {
  margin-top: 10px;
  padding-top: 10px;
}

.upload-progress-new {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #1f2d3d;
}

.upload-status {
  text-align: center;
  margin: 10px 0 0 0;
  font-size: 14px;
  color: #5e6d82;
}

.success-content {
  text-align: center;
  padding: 10px 0 20px;
}

.success-icon {
  margin-bottom: 20px;
}

.success-content h3 {
  margin: 0 0 10px 0;
  color: #1f2d3d;
}

.success-content p {
  color: #5e6d82;
  margin-bottom: 25px;
}

.success-actions {
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .actions-container {
    flex-direction: column;
    align-items: center;
  }
  
  .action-card {
    width: 100%;
    max-width: 320px;
  }
  
  .main-container {
    padding: 20px;
  }
  
  .header h1 {
    font-size: 28px;
  }
  
  .select-project-dialog {
    height: 400px;
  }
  
  .dialog-header {
    flex-direction: column;
  }
  
  .create-project-btn {
    width: 100%;
    margin-top: 0;
  }
}
</style>