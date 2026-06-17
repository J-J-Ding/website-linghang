<template>
  <div class="kanban-main">

    <t-tooltip content="返回诊断会话" placement="top">
      <t-button class="back-to-chat" size="large" theme="primary" shape="circle" variant="base" @click="jumpToChatPage">
        <icon name="arrow-left" />
      </t-button>
    </t-tooltip>

    <t-space direction="vertical">
      <t-space>
        <t-card title="场景活跃度" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button @click="exportSceneActiveData" class="export-btn">
                <icon name="download" />
                导出Excel
              </t-button>
            </t-space>
          </template>

          <div class="filter-controls">
            <div class="filter-group">
              <t-space>
                <div class="filter-item">
                  <label class="filter-label">时间范围</label>
                  <t-select v-model="timeRangeSceneActive" class="filter-select" @change="handleSceneActiveFilterChange">
                    <t-option value="week" label="周"></t-option>
                    <t-option value="month" label="月"></t-option>
                    <t-option value="quarter" label="季度"></t-option>
                    <t-option value="half" label="半年"></t-option>
                  </t-select>
                </div>

              <div class="filter-item">
                <label class="filter-label">部门</label>
                <t-select v-model="selectedDepartmentSceneActive" class="filter-select" @change="handleSceneActiveDepartmentChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="dept in departmentsSceneActive" :key="dept" :value="dept" :label="dept"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">领域</label>
                <t-select v-model="selectedFieldSceneActive" class="filter-select" @change="handleSceneActiveFieldChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="field in fieldsSceneActive" :key="field" :value="field" :label="field"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">团队</label>
                <t-select v-model="selectedTeamSceneActive" class="filter-select" @change="handleSceneActiveTeamChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="team in teamsSceneActive" :key="team" :value="team" :label="team"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">成员</label>
                <t-select v-model="selectedMemberSceneActive" class="filter-select" @change="handleSceneActiveFilterChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="member in membersSceneActive" :key="member.account" :value="member.account" :label="member.name"></t-option>
                </t-select>
              </div>
            </t-space>
          </div>

            <div class="filter-group main-scene-group">
              <t-space>
                <div class="filter-item main-scene-item">
                  <label class="filter-label">主场景</label>
                  <t-select
                    v-model="selectedMainScene"
                    class="filter-select main-scene-select"
                    @change="handleMainSceneChange"
                    clearable
                    placeholder="选择主场景"
                  >
                    <t-option value="" label="全部"></t-option>
                    <t-option v-for="scene in mainScenes" :key="scene" :value="scene" :label="scene"></t-option>
                  </t-select>
                </div>

                <div class="filter-item main-scene-item">
                  <label class="filter-label">子场景</label>
                  <t-select
                    v-model="selectedSubScene"
                    class="filter-select main-scene-select"
                    @change="handleSubSceneChange"
                    clearable
                    placeholder="选择子场景"
                    :disabled="!selectedMainScene"
                  >
                    <t-option value="" label="全部"></t-option>
                    <t-option v-for="scene in subScenes" :key="scene" :value="scene" :label="scene"></t-option>
                  </t-select>
                </div>
              </t-space>
            </div>
          </div>

          <div id="sceneActive" style="width: 100%; height: 500px"></div>
        </t-card>

        <t-card title="故障覆盖率" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button @click="exportFaultCoverageData" class="export-btn">
                <icon name="download" />
                导出Excel
              </t-button>
            </t-space>
          </template>

          <div class="filter-controls">
            <t-space>
              <div class="filter-item">
                <label class="filter-label">时间范围</label>
                <t-select v-model="timeRangeSceneCover" class="filter-select" @change="handleSceneCoverFilterChange">
                  <t-option value="week" label="周"></t-option>
                  <t-option value="month" label="月"></t-option>
                  <t-option value="quarter" label="季度"></t-option>
                  <t-option value="half" label="半年"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">部门</label>
                <t-select v-model="selectedDepartmentSceneCover" class="filter-select" @change="handleSceneCoverDepartmentChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="dept in departmentsSceneCover" :key="dept" :value="dept" :label="dept"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">领域</label>
                <t-select v-model="selectedFieldSceneCover" class="filter-select" @change="handleSceneCoverFieldChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="field in fieldsSceneCover" :key="field" :value="field" :label="field"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">团队</label>
                <t-select v-model="selectedTeamSceneCover" class="filter-select" @change="handleSceneCoverTeamChange">
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="team in teamsSceneCover" :key="team" :value="team" :label="team"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">标签</label>
                <t-select v-model="selectedTagSceneCover" class="filter-select" @change="handleSceneCoverFilterTagChange">
                  <t-option value="智诊" label="全部"></t-option>
                  <t-option value="智诊创建" label="智诊创建"></t-option>
                  <t-option value="智诊检查" label="智诊检查"></t-option>
                </t-select>
              </div>
            </t-space>
          </div>

          <div id="sceneCover" style="width: 100%; height: 500px"></div>
        </t-card>
      </t-space>


      <t-space>
        <t-card title="上线语料统计" class="kanban-card unified-height-card up-knowledge-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button @click="exportUpKnowledgeData" class="export-btn">
                <icon name="download" />
                导出Excel
              </t-button>
            </t-space>
          </template>

          <!-- 筛选控件区域 -->
          <div class="filter-controls">
            <t-space>
              <div class="filter-item">
                <label class="filter-label">时间范围</label>
                <t-select v-model="timeRangeUpKnowledge" class="filter-select" @change="handleUpKnowledgeFilterChange">
                  <t-option value="week" label="周"></t-option>
                  <t-option value="month" label="月"></t-option>
                  <t-option value="quarter" label="季度"></t-option>
                  <t-option value="half" label="半年"></t-option>
                </t-select>
              </div>

            <div class="filter-item">
              <label class="filter-label">领域</label>
              <t-select v-model="selectedFieldUpKnowledge" class="filter-select" @change="handleUpKnowledgeFieldChange">
                <t-option value="" label="全部"></t-option>
                <t-option v-for="field in fieldsUpKnowledge" :key="field" :value="field" :label="field"></t-option>
              </t-select>
            </div>

            <div class="filter-item">
              <label class="filter-label">团队</label>
              <t-select v-model="selectedTeamUpKnowledge" class="filter-select" @change="handleUpKnowledgeTeamChange">
                <t-option value="" label="全部"></t-option>
                <t-option v-for="team in teamsUpKnowledge" :key="team" :value="team" :label="team"></t-option>
              </t-select>
            </div>

            </t-space>
          </div>

          <div id="upKnowledge" style="width: 100%; height: 400px"></div>
        </t-card>

      <t-card title="语料录入记录" class="kanban-card unified-height-card knowledge-record-card" hover-shadow>
        <template #actions>
          <t-space>
            <t-button @click="exportKnowledgeRecords" class="export-btn">
              <icon name="download" />
              导出Excel
            </t-button>
          </t-space>
        </template>
        <t-table
          :data="knowledgeRecord"
          :columns="knowledgeRecordColumns"
          :hover="true"
          :max-height="480"
          rowKey="index"
          :pagination="knowledgeRecordPagination"
          @page-change="handleKnowledgeRecordPageChange"
        />
      </t-card>
      </t-space>

      <t-space>
      <t-card title="使用效果（场景）" class="kanban-card" hover-shadow>
        <template #actions>
          <t-space>
            <t-button @click="exportUseEffectData" class="export-btn">
              <icon name="download" />
              导出Excel
            </t-button>
          </t-space>
        </template>

        <div class="filter-controls">
          <div class="filter-group">
            <t-space>
              <div class="filter-item">
                <label class="filter-label">部门</label>
                <t-select
                  v-model="selectedDepartmentUseEffect"
                  class="filter-select"
                  @change="handleUseEffectDepartmentChange"
                  clearable
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="dept in departmentsUseEffect" :key="dept" :value="dept" :label="dept"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">领域</label>
                <t-select
                  v-model="selectedFieldUseEffect"
                  class="filter-select"
                  @change="handleUseEffectFieldChange"
                  clearable
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="field in fieldsUseEffect" :key="field" :value="field" :label="field"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">团队</label>
                <t-select
                  v-model="selectedTeamUseEffect"
                  class="filter-select"
                  @change="handleUseEffectTeamChange"
                  clearable
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="team in teamsUseEffect" :key="team" :value="team" :label="team"></t-option>
                </t-select>
              </div>

              <div class="filter-item">
                <label class="filter-label">成员</label>
                <t-select
                  v-model="selectedMemberUseEffect"
                  class="filter-select"
                  @change="handleUseEffectMemberChange"
                  clearable
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="member in membersUseEffect" :key="member.account" :value="member.account" :label="member.name"></t-option>
                </t-select>
              </div>
            </t-space>
          </div>

          <div class="filter-group main-scene-group">
            <t-space>
              <div class="filter-item main-scene-item">
                <label class="filter-label">主场景</label>
                <t-select
                  v-model="selectedMainSceneUseEffect"
                  class="filter-select main-scene-select"
                  @change="handleUseEffectMainSceneChange"
                  clearable
                  placeholder="选择主场景"
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="scene in mainScenesUseEffect" :key="scene" :value="scene" :label="scene"></t-option>
                </t-select>
              </div>

              <div class="filter-item main-scene-item">
                <label class="filter-label">子场景</label>
                <t-select
                  v-model="selectedSubSceneUseEffect"
                  class="filter-select main-scene-select"
                  @change="handleUseEffectSubSceneChange"
                  clearable
                  placeholder="选择子场景"
                  :disabled="!selectedMainSceneUseEffect"
                >
                  <t-option value="" label="全部"></t-option>
                  <t-option v-for="scene in subScenesUseEffect" :key="scene" :value="scene" :label="scene"></t-option>
                </t-select>
              </div>
            </t-space>
          </div>
        </div>

        <div id="useEffectScene" style="width: 100%; height: 500px"></div>
      </t-card>

        <t-card title="调用量统计" class="kanban-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button @click="exportStatistics" class="export-btn">
                <icon name="download" />
                导出Excel
              </t-button>
            </t-space>
          </template>
          <!-- 筛选控件区域-->
          <div class="filter-controls">
              <div class="filter-group first-row">
                <t-space>
                  <div class="filter-item">
                    <label class="filter-label">时间范围</label>
                    <t-select v-model="timeRange" class="filter-select" @change="handleFilterChange">
                      <t-option value="week" label="周"></t-option>
                      <t-option value="month" label="月"></t-option>
                      <t-option value="quarter" label="季度"></t-option>
                      <t-option value="half" label="半年"></t-option>
                    </t-select>
                  </div>

                  <div class="filter-item">
                    <label class="filter-label">部门</label>
                    <t-select v-model="selectedDepartment" class="filter-select" @change="handleDepartmentChange">
                      <t-option value="" label="全部"></t-option>
                      <t-option v-for="dept in departments" :key="dept" :value="dept" :label="dept"></t-option>
                    </t-select>
                  </div>

                  <div class="filter-item">
                    <label class="filter-label">领域</label>
                    <t-select v-model="selectedField" class="filter-select" @change="handleFieldChange">
                      <t-option value="" label="全部"></t-option>
                      <t-option v-for="field in fields" :key="field" :value="field" :label="field"></t-option>
                    </t-select>
                  </div>

                  <div class="filter-item">
                    <label class="filter-label">团队</label>
                    <t-select v-model="selectedTeam" class="filter-select" @change="handleTeamChange">
                      <t-option value="" label="全部"></t-option>
                      <t-option v-for="team in teams" :key="team" :value="team" :label="team"></t-option>
                    </t-select>
                  </div>

                  <div class="filter-item">
                    <label class="filter-label">成员</label>
                    <t-select v-model="selectedMember" class="filter-select" @change="handleFilterChange">
                      <t-option value="" label="全部"></t-option>
                      <t-option v-for="member in members" :key="member.account" :value="member.account" :label="member.name"></t-option>
                    </t-select>
                  </div>
                </t-space>
              </div>

              <div class="filter-group second-row">
                <t-space>
                  <div class="filter-item">
                    <label class="filter-label">功能</label>
                    <t-select
                      v-model="selectedFunction"
                      class="filter-select"
                      @change="handleFunctionChange"
                      clearable
                      placeholder="选择功能（默认显示全部功能总次数）"
                    >
                      <t-option value="" label="全部功能"></t-option>
                      <t-option value="故障问答" label="故障确认"></t-option>
                      <t-option value="日志分析" label="日志分析-通用分析"></t-option>
                      <t-option value="数据一致性比较分析" label="日志分析-数据一致性比较分析"></t-option>
                      <t-option value="内存分析" label="日志分析-内存分析"></t-option>
                      <t-option value="直接定位" label="直接定位"></t-option>
                      <t-option value="上站定位" label="上站定位"></t-option>
                      <t-option value="工程故障横推" label="工程故障横推"></t-option>
                      <t-option value="irunner调用" label="irunner调用"></t-option>
                    </t-select>
                  </div>

                  <!-- 可以在这里添加更多第二行的筛选项 -->
                </t-space>
              </div>
            </div>
          <!-- 图表区域 -->
          <div id="visits" style="width: 100%; height: 400px"></div>
        </t-card>
      </t-space>

     <!-- <t-space>
        <t-card title="RDC检查记录" class="kanban-card unified-height-card knowledge-record-card" hover-shadow>
          <template #actions>
            <t-space>
              <t-button @click="exportRdcCheckRecords" class="export-btn">
                <icon name="download" />
                导出Excel
              </t-button>
            </t-space>
          </template>
          <t-table
            :data="rdcCheckRecord"
            :columns="rdcCheckRecordColumns"
            :hover="true"
            :max-height="480"
            rowKey="index"
            :pagination="rdcCheckRecordPagination"
            @page-change="handleRdcCheckRecordPageChange"
          />
        </t-card>
      </t-space>-->
    </t-space>
  </div>
</template>

<script setup lang="jsx">
import axios from 'axios';
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { Icon } from 'tdesign-icons-vue-next';
import { useRouter } from 'vue-router';

const INTELDIGA_API_URL = import.meta.env.VITE_INTELDIGA_API_URL;
const router = useRouter();


// 图表实例
let dayVisitsChart = null;
let visitsChart = null;
let upKnowledgeChart = null;
let sceneActiveChart = null;
let sceneCoverChart = null;
let useEffectSceneChart = null;
let useEffectDayChart = null;

// 图表数据
const dayVisitsData = ref([]);

const visitsData = ref([
  {label:"2025-09-20", data:32},
  {label:"2025-09-21", data:33},
  {label:"2025-09-22", data:55},
  {label:"2025-09-23", data:75},
  {label:"2025-09-24", data:79},
  {label:"2025-09-25", data:75},
  {label:"2025-09-26", data:64},
  {label:"2025-09-27", data:68},
  {label:"2025-09-28", data:73},
  {label:"2025-09-29", data:80}
]);

const upKnowledgeData = ref([]);

const knowledgeRecord = ref([]);
const knowledgeRecordPagination = ref({
  current: 1,
  pageSize: 6,
  total: 0
});

const rdcCheckRecord = ref([]);
const rdcCheckRecordPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
});

const sceneActiveData = ref([]);

const sceneCoverData = ref([
  {label:"主备倒换失败", cover:35, uncover:15},
  {label:"光模块异常", cover:28, uncover:12},
  {label:"光监控ETH模式", cover:22, uncover:18},
  {label:"VLAN电监控对接不通", cover:30, uncover:10},
  {label:"OP板组合倒换倒换超时", cover:25, uncover:15},
  {label:"OTDR模块周期测量", cover:18, uncover:22},
  {label:"端口配置失效", cover:32, uncover:8},
  {label:"端口属性配置下发失败", cover:20, uncover:20}
]);


const useEffectDayData = ref([
  {
    label: "主备倒换失败",
    data: [
      { time: "2025-09-20", value: 3 },
      { time: "2025-09-21", value: 3 },
      { time: "2025-09-22", value: 3.6 },
      { time: "2025-09-23", value: 3.7 },
      { time: "2025-09-24", value: 4.2 },
      { time: "2025-09-25", value: 4.6 },
      { time: "2025-09-26", value: 3.7 },
      { time: "2025-09-27", value: 2.8 },
      { time: "2025-09-28", value: 4.9 },
      { time: "2025-09-29", value: 3.5 }
    ]
  },
  {
    label: "光模块异常",
    data: [
      { time: "2025-09-20", value: 4 },
      { time: "2025-09-21", value: 4 },
      { time: "2025-09-22", value: 5 },
      { time: "2025-09-23", value: 3 },
      { time: "2025-09-24", value: 3.8 },
      { time: "2025-09-25", value: 4.6 },
      { time: "2025-09-26", value: 3.9 },
      { time: "2025-09-27", value: 4.6 },
      { time: "2025-09-28", value: 4.8 },
      { time: "2025-09-29", value: 4.2 }
    ]
  },
  {
    label: "光监控ETH模式",
    data: [
      { time: "2025-09-20", value: 5 },
      { time: "2025-09-21", value: 5 },
      { time: "2025-09-22", value: 5 },
      { time: "2025-09-23", value: 4 },
      { time: "2025-09-24", value: 3 },
      { time: "2025-09-25", value: 2.5 },
      { time: "2025-09-26", value: 3.9 },
      { time: "2025-09-27", value: 4.6 },
      { time: "2025-09-28", value: 4.7 },
      { time: "2025-09-29", value: 3.8 }
    ]
  },
  {
    label: "VLAN电监控对接不通",
    data: [
      { time: "2025-09-20", value: 5 },
      { time: "2025-09-21", value: 3 },
      { time: "2025-09-22", value: 4 },
      { time: "2025-09-23", value: 3.8 },
      { time: "2025-09-24", value: 4.9 },
      { time: "2025-09-25", value: 3.9 },
      { time: "2025-09-26", value: 4.2 },
      { time: "2025-09-27", value: 4.6 },
      { time: "2025-09-28", value: 4.3 },
      { time: "2025-09-29", value: 4.7 }
    ]
  }
]);

// 获取数据示例
// const getAiAccessData = async () => {
//   try {
//     const res = await axios.post(`${INTELDIGA_API_URL}/api/daily-visits`, {
//       period: parseInt(selectedRange.value.days),
//     });
//     if (res.data.status === 'success') {
//       return res.data.data;
//     }
//     return [];
//   } catch (err) {
//     console.error('AI访问量数据请求失败:', err);
//     return [];
//   }
// };

// 使用效果（场景）筛选相关数据
const timeRangeUseEffect = ref('week');
const selectedDepartmentUseEffect = ref('');
const selectedFieldUseEffect = ref('');
const selectedTeamUseEffect = ref('');
const selectedMemberUseEffect = ref('');
const selectedMainSceneUseEffect = ref('');
const selectedSubSceneUseEffect = ref('');
const departmentsUseEffect = ref([]);
const fieldsUseEffect = ref([]);
const teamsUseEffect = ref([]);
const membersUseEffect = ref([]);
const mainScenesUseEffect = ref([]);
const subScenesUseEffect = ref([]);

// 使用效果筛选变化处理函数
const handleUseEffectDepartmentChange = (dept) => {
  selectedDepartmentUseEffect.value = dept;
  updateUseEffectFieldOptions();
  getUseEffectSceneData();
};

const handleUseEffectFieldChange = (field) => {
  selectedFieldUseEffect.value = field;
  updateUseEffectTeamOptions();
  getUseEffectSceneData();
};

const handleUseEffectTeamChange = (team) => {
  selectedTeamUseEffect.value = team;
  updateUseEffectMemberOptions();
  getUseEffectSceneData();
};

const handleUseEffectMemberChange = () => {
  getUseEffectSceneData();
};

const handleUseEffectMainSceneChange = () => {
  selectedSubSceneUseEffect.value = '';
  getUseEffectSubScenes();
  getUseEffectSceneData();
};

const handleUseEffectSubSceneChange = () => {
  getUseEffectSceneData();
};

const handleUseEffectFilterChange = () => {
  getUseEffectSceneData();
};

// 更新使用效果筛选选项
const updateUseEffectFieldOptions = () => {
  if (selectedDepartmentUseEffect.value && departmentStructure.value[selectedDepartmentUseEffect.value]) {
    fieldsUseEffect.value = Object.keys(departmentStructure.value[selectedDepartmentUseEffect.value]);
  } else {
    fieldsUseEffect.value = [];
  }
  selectedFieldUseEffect.value = '';
  selectedTeamUseEffect.value = '';
  selectedMemberUseEffect.value = '';
  updateUseEffectTeamOptions();
};

const updateUseEffectTeamOptions = () => {
  if (selectedDepartmentUseEffect.value && selectedFieldUseEffect.value &&
      departmentStructure.value[selectedDepartmentUseEffect.value]?.[selectedFieldUseEffect.value]) {
    teamsUseEffect.value = Object.keys(departmentStructure.value[selectedDepartmentUseEffect.value][selectedFieldUseEffect.value]);
  } else {
    teamsUseEffect.value = [];
  }
  selectedTeamUseEffect.value = '';
  selectedMemberUseEffect.value = '';
  updateUseEffectMemberOptions();
};

const updateUseEffectMemberOptions = () => {
  if (selectedDepartmentUseEffect.value && selectedFieldUseEffect.value && selectedTeamUseEffect.value &&
      departmentStructure.value[selectedDepartmentUseEffect.value]?.[selectedFieldUseEffect.value]?.[selectedTeamUseEffect.value]) {
    const teamMembers = departmentStructure.value[selectedDepartmentUseEffect.value][selectedFieldUseEffect.value][selectedTeamUseEffect.value];
    membersUseEffect.value = Object.keys(teamMembers).map(account => ({
      account,
      name: teamMembers[account]
    }));
  } else {
    membersUseEffect.value = [];
  }
  selectedMemberUseEffect.value = '';
};

// 获取使用效果主场景列表
const getUseEffectMainScenes = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/use-effect-mainscenes`, {
      department: selectedDepartmentUseEffect.value,
      field: selectedFieldUseEffect.value,
      team: selectedTeamUseEffect.value,
      member: selectedMemberUseEffect.value,
    });

    if (res.data.status === 'success') {
      mainScenesUseEffect.value = res.data.data;
    } else {
      console.error('获取使用效果主场景列表失败:', res.data.message);
      mainScenesUseEffect.value = [];
    }
  } catch (err) {
    console.error('获取使用效果主场景列表请求失败:', err);
    mainScenesUseEffect.value = [];
  }
};

// 获取使用效果子场景列表
const getUseEffectSubScenes = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/use-effect-subscenes`, {
      department: selectedDepartmentUseEffect.value,
      field: selectedFieldUseEffect.value,
      team: selectedTeamUseEffect.value,
      member: selectedMemberUseEffect.value,
      mainscene: selectedMainSceneUseEffect.value,
    });

    if (res.data.status === 'success') {
      subScenesUseEffect.value = res.data.data;
    } else {
      console.error('获取使用效果子场景列表失败:', res.data.message);
      subScenesUseEffect.value = [];
    }
  } catch (err) {
    console.error('获取使用效果子场景列表请求失败:', err);
    subScenesUseEffect.value = [];
  }
};

// 故障覆盖率筛选相关数据
const timeRangeSceneCover = ref('week');
const selectedTagSceneCover = ref('智诊');
const selectedDepartmentSceneCover = ref('');
const selectedFieldSceneCover = ref('');
const selectedTeamSceneCover = ref('');
const departmentsSceneCover = ref([]);
const fieldsSceneCover = ref([]);
const teamsSceneCover = ref([]);

// 故障覆盖率筛选变化处理函数
const handleSceneCoverDepartmentChange = (dept) => {
  selectedDepartmentSceneCover.value = dept;
  updateSceneCoverFieldOptions();
  getFaultCoverageData();
};

const handleSceneCoverFieldChange = (field) => {
  selectedFieldSceneCover.value = field;
  updateSceneCoverTeamOptions();
  getFaultCoverageData();
};

const handleSceneCoverTeamChange = (team) => {
  selectedTeamSceneCover.value = team;
  getFaultCoverageData();
};

const handleSceneCoverFilterChange = () => {
  getFaultCoverageData();
};

const handleSceneCoverFilterTagChange = () => {
  getFaultCoverageData();
};

// 更新故障覆盖率筛选选项
const updateSceneCoverFieldOptions = () => {
  if (selectedDepartmentSceneCover.value && rdcDepartmentStructure.value[selectedDepartmentSceneCover.value]) {
    fieldsSceneCover.value = Object.keys(rdcDepartmentStructure.value[selectedDepartmentSceneCover.value]);
  } else {
    fieldsSceneCover.value = [];
  }
  selectedFieldSceneCover.value = '';
  selectedTeamSceneCover.value = '';
  updateSceneCoverTeamOptions();
};

const updateSceneCoverTeamOptions = () => {
  if (selectedDepartmentSceneCover.value && selectedFieldSceneCover.value &&
  rdcDepartmentStructure.value[selectedDepartmentSceneCover.value]?.[selectedFieldSceneCover.value]) {
    teamsSceneCover.value = Object.keys(rdcDepartmentStructure.value[selectedDepartmentSceneCover.value][selectedFieldSceneCover.value]);
  } else {
    teamsSceneCover.value = [];
  }
  selectedTeamSceneCover.value = '';
};

// 获取故障覆盖率数据
const getFaultCoverageData = async () => {
  try {
    console.log('发送故障覆盖率请求参数:', {
      time_range: timeRangeSceneCover.value,
      department: selectedDepartmentSceneCover.value,
      field: selectedFieldSceneCover.value,
      team: selectedTeamSceneCover.value,
      tag: selectedTagSceneCover.value,
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/fault-coverage-statistics`, {
      time_range: timeRangeSceneCover.value,
      department: selectedDepartmentSceneCover.value,
      field: selectedFieldSceneCover.value,
      team: selectedTeamSceneCover.value,
      tag: selectedTagSceneCover.value,
    });

    if (res.data.status === 'success') {
      sceneCoverData.value = res.data.data;
      updateSceneCoverChartData();

    } else {
      console.error('故障覆盖率接口返回错误:', res.data.message);
      sceneCoverData.value = [];
    }
  } catch (err) {
    console.error('故障覆盖率数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    sceneCoverData.value = [];
  }
};


// 使用效果（场景）相关数据
const useEffectSceneData = ref([]);
const availableMainScenes = ref([]);
const currentScenePage = ref(1);
const pageSize = ref(8);

// 获取使用效果（场景）数据
const getUseEffectSceneData = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/use-effect-scene-statistics`, {
      department: selectedDepartmentUseEffect.value,
      field: selectedFieldUseEffect.value,
      team: selectedTeamUseEffect.value,
      member: selectedMemberUseEffect.value,
      mainscene: selectedMainSceneUseEffect.value,
      subscene: selectedSubSceneUseEffect.value,
    });

    if (res.data.status === 'success') {
      useEffectSceneData.value = res.data.data;
      updateUseEffectSceneChartData();
    } else {
      console.error('使用效果（场景）接口返回错误:', res.data.message);
      useEffectSceneData.value = [];
    }
  } catch (err) {
    console.error('使用效果（场景）数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    useEffectSceneData.value = [];
  }
};

// 获取可用主场景列表
const getAvailableMainScenes = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/available-mainscenes`);
    if (res.data.status === 'success') {
      availableMainScenes.value = res.data.data;
    } else {
      console.error('获取主场景列表失败:', res.data.message);
      availableMainScenes.value = [];
    }
  } catch (err) {
    console.error('获取主场景列表请求失败:', err);
    availableMainScenes.value = [];
  }
};


// 分页变化处理
const handleScenePageChange = (pageInfo) => {
  currentScenePage.value = pageInfo.current;
  pageSize.value = pageInfo.pageSize;
};

// 页面大小变化处理
const handlePageSizeChange = (size) => {
  pageSize.value = size;
  currentScenePage.value = 1;
};


const handleKnowledgeRecordPageChange = (pageInfo) => {
  knowledgeRecordPagination.value.current = pageInfo.current;
  knowledgeRecordPagination.value.pageSize = pageInfo.pageSize;
  getKnowledgeRecords();
};

// 获取语料录入记录
const getKnowledgeRecords = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/knowledge-records`, {
      page: knowledgeRecordPagination.value.current,
      pageSize: knowledgeRecordPagination.value.pageSize
    });

    if (res.data.status === 'success') {
      knowledgeRecord.value = res.data.data;
      knowledgeRecordPagination.value.total = res.data.total;
    } else {
      console.error('语料录入记录接口返回错误:', res.data.message);
      knowledgeRecord.value = [];
      knowledgeRecordPagination.value.total = 0;
    }
  } catch (err) {
    console.error('语料录入记录数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    knowledgeRecord.value = [];
    knowledgeRecordPagination.value.total = 0;
  }
};

const handleRdcCheckRecordPageChange = (pageInfo) => {
  rdcCheckRecordPagination.value.current = pageInfo.current;
  rdcCheckRecordPagination.value.pageSize = pageInfo.pageSize;
  getRdcCheckRecords();
};

// 获取RDC检查记录
const getRdcCheckRecords = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/rdc-check-records`, {
      page: rdcCheckRecordPagination.value.current,
      pageSize: rdcCheckRecordPagination.value.pageSize
    });

    if (res.data.status === 'success') {
      rdcCheckRecord.value = res.data.data;
      rdcCheckRecordPagination.value.total = res.data.total;
    } else {
      console.error('语料录入记录接口返回错误:', res.data.message);
      rdcCheckRecord.value = [];
      rdcCheckRecordPagination.value.total = 0;
    }
  } catch (err) {
    console.error('语料录入记录数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    rdcCheckRecord.value = [];
    rdcCheckRecordPagination.value.total = 0;
  }
};

// 上线语料获取领域选项的方法
const fetchAvailableFields = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/available-fields`);
    if (res.data.status === 'success') {
      fieldsUpKnowledge.value = res.data.data;

    }
  } catch (err) {
    console.error('获取领域列表失败:', err);
    fieldsUpKnowledge.value = [];
  }
};

// 上线语料获取团队选项的方法
const fetchAvailableTeams = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/available-teams`, {
      field: selectedFieldUpKnowledge.value
    });
    if (res.data.status === 'success') {
      teamsUpKnowledge.value = res.data.data;

    }
  } catch (err) {
    console.error('获取团队列表失败:', err);
    teamsUpKnowledge.value = [];
  }
};

// 上线语料筛选相关数据
const timeRangeUpKnowledge = ref('week');
const selectedDepartmentUpKnowledge = ref('');
const selectedFieldUpKnowledge = ref('');
const selectedTeamUpKnowledge = ref('');
const departmentsUpKnowledge = ref([]);
const fieldsUpKnowledge = ref([]);
const teamsUpKnowledge = ref([]);

// 上线语料筛选变化处理函数
const handleUpKnowledgeDepartmentChange = (dept) => {
  selectedDepartmentUpKnowledge.value = dept;
  selectedFieldUpKnowledge.value = '';
  selectedTeamUpKnowledge.value = '';
  updateUpKnowledgeFieldOptions();
  getUpKnowledgeData();
};

const handleUpKnowledgeFieldChange = (field) => {
  selectedFieldUpKnowledge.value = field;
  selectedTeamUpKnowledge.value = '';
  updateUpKnowledgeTeamOptions();
  getUpKnowledgeData();
};

const handleUpKnowledgeTeamChange = (team) => {
  selectedTeamUpKnowledge.value = team;
  getUpKnowledgeData();
};

const handleUpKnowledgeFilterChange = () => {
  getUpKnowledgeData();
};


// 上线语料筛选选项更新方法
const updateUpKnowledgeFieldOptions = () => {
  fetchAvailableFields();
};

const updateUpKnowledgeTeamOptions = () => {
  if (selectedFieldUpKnowledge.value) {
    fetchAvailableTeams();
  } else {
    teamsUpKnowledge.value = [];
  }
};

const updateUpKnowledgeMemberOptions = () => {
  if (selectedDepartmentUpKnowledge.value && selectedFieldUpKnowledge.value && selectedTeamUpKnowledge.value &&
      departmentStructure.value[selectedDepartmentUpKnowledge.value]?.[selectedFieldUpKnowledge.value]?.[selectedTeamUpKnowledge.value]) {
    const teamMembers = departmentStructure.value[selectedDepartmentUpKnowledge.value][selectedFieldUpKnowledge.value][selectedTeamUpKnowledge.value];
    members.value = Object.keys(teamMembers).map(account => ({
      account,
      name: teamMembers[account]
    }));
  } else {
    members.value = [];
  }
};

const selectedMainScene = ref('');
const mainScenes = ref([]);


const selectedSubScene = ref('');
const subScenes = ref([]);

//获取子场景列表
const getSubScenes = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/active-scene-subscenes`, {
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
      mainscene: selectedMainScene.value,
    });

    if (res.data.status === 'success') {
      subScenes.value = res.data.data;
    } else {
      console.error('获取子场景列表失败:', res.data.message);
      subScenes.value = [];
    }
  } catch (err) {
    console.error('获取子场景列表请求失败:', err);
    subScenes.value = [];
  }
};

// 子场景变化处理
const handleSubSceneChange = () => {
  getFilteredSceneActiveData();
};

//获取主场景列表
const getMainScenes = async () => {
  try {
    const res = await axios.post(`${INTELDIGA_API_URL}/api/active-scene-mainscenes`, {
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
    });

    if (res.data.status === 'success') {
      mainScenes.value = res.data.data;
    } else {
      console.error('获取主场景列表失败:', res.data.message);
      mainScenes.value = [];
    }
  } catch (err) {
    console.error('获取主场景列表请求失败:', err);
    mainScenes.value = [];
  }
};

// 主场景变化处理
const handleMainSceneChange = () => {
  selectedSubScene.value = '';
  getSubScenes();
  getFilteredSceneActiveData();
};

const getFilteredSceneActiveData = async () => {
  try {
    console.log('发送筛选后场景活跃度请求参数:', {
      time_range: timeRangeSceneActive.value,
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
      mainscene: selectedMainScene.value,
      subscene: selectedSubScene.value,
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/filtered-scene-activity`, {
      time_range: timeRangeSceneActive.value,
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
      mainscene: selectedMainScene.value,
      subscene: selectedSubScene.value,
    });

    if (res.data.status === 'success') {
      sceneActiveData.value = res.data.data;
      updateSceneActiveChartData();
    } else {
      console.error('筛选场景活跃度接口返回错误:', res.data.message);
      sceneActiveData.value = [];
    }
  } catch (err) {
    console.error('筛选场景活跃度数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    sceneActiveData.value = [];
  }
};


// 场景活跃度筛选相关数据
const timeRangeSceneActive = ref('week');
const selectedDepartmentSceneActive = ref('');
const selectedFieldSceneActive = ref('');
const selectedTeamSceneActive = ref('');
const selectedMemberSceneActive = ref('');
const departmentsSceneActive = ref([]);
const fieldsSceneActive = ref([]);
const teamsSceneActive = ref([]);
const membersSceneActive = ref([]);

// 场景活跃度筛选变化处理函数
const handleSceneActiveDepartmentChange = (dept) => {
  selectedDepartmentSceneActive.value = dept;
  updateSceneActiveFieldOptions();
  getMainScenes(); //更新主场景列表
  getFilteredSceneActiveData();
};

const handleSceneActiveFieldChange = (field) => {
  selectedFieldSceneActive.value = field;
  updateSceneActiveTeamOptions();
  getMainScenes();
  getFilteredSceneActiveData();
};

const handleSceneActiveTeamChange = (team) => {
  selectedTeamSceneActive.value = team;
  updateSceneActiveMemberOptions();
  getMainScenes();
  getFilteredSceneActiveData();
};

const handleSceneActiveFilterChange = () => {
  getMainScenes();
  getFilteredSceneActiveData();
};

// 更新场景活跃度筛选选项
const updateSceneActiveFieldOptions = () => {
  if (selectedDepartmentSceneActive.value && departmentStructure.value[selectedDepartmentSceneActive.value]) {
    fieldsSceneActive.value = Object.keys(departmentStructure.value[selectedDepartmentSceneActive.value]);
  } else {
    fieldsSceneActive.value = [];
  }
  selectedFieldSceneActive.value = '';
  selectedTeamSceneActive.value = '';
  selectedMemberSceneActive.value = '';
  updateSceneActiveTeamOptions();
};

const updateSceneActiveTeamOptions = () => {
  if (selectedDepartmentSceneActive.value && selectedFieldSceneActive.value &&
      departmentStructure.value[selectedDepartmentSceneActive.value]?.[selectedFieldSceneActive.value]) {
    teamsSceneActive.value = Object.keys(departmentStructure.value[selectedDepartmentSceneActive.value][selectedFieldSceneActive.value]);
  } else {
    teamsSceneActive.value = [];
  }
  selectedTeamSceneActive.value = '';
  selectedMemberSceneActive.value = '';
  updateSceneActiveMemberOptions();
};

const updateSceneActiveMemberOptions = () => {
  if (selectedDepartmentSceneActive.value && selectedFieldSceneActive.value && selectedTeamSceneActive.value &&
      departmentStructure.value[selectedDepartmentSceneActive.value]?.[selectedFieldSceneActive.value]?.[selectedTeamSceneActive.value]) {
    const teamMembers = departmentStructure.value[selectedDepartmentSceneActive.value][selectedFieldSceneActive.value][selectedTeamSceneActive.value];
    membersSceneActive.value = Object.keys(teamMembers).map(account => ({
      account,
      name: teamMembers[account]
    }));
  } else {
    membersSceneActive.value = [];
  }
  selectedMemberSceneActive.value = '';
};

// 获取场景活跃度数据
const getSceneActiveData = async () => {
  try {
    console.log('发送场景活跃度请求参数:', {
      time_range: timeRangeSceneActive.value,
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/scene-activity-statistics`, {
      time_range: timeRangeSceneActive.value,
      department: selectedDepartmentSceneActive.value,
      field: selectedFieldSceneActive.value,
      team: selectedTeamSceneActive.value,
      member: selectedMemberSceneActive.value,
    });

    if (res.data.status === 'success') {
      sceneActiveData.value = res.data.data;
      updateSceneActiveChartData();
    } else {
      console.error('场景活跃度接口返回错误:', res.data.message);
      sceneActiveData.value = [];
    }
  } catch (err) {
    console.error('场景活跃度数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    sceneActiveData.value = [];
  }
};

// 获取上线语料数据
const getUpKnowledgeData = async () => {
  try {
    console.log('发送上线语料请求参数:', {
      time_range: timeRangeUpKnowledge.value,
      field: selectedFieldUpKnowledge.value,
      team: selectedTeamUpKnowledge.value,
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/up-knowledge-statistics`, {
      time_range: timeRangeUpKnowledge.value,
      field: selectedFieldUpKnowledge.value,
      team: selectedTeamUpKnowledge.value,
    });


    console.log('上线语料响应数据:', res.data);

    if (res.data.status === 'success') {
      upKnowledgeData.value = res.data.data.map(item => ({
        label: item.label,
        data: item.count || 0
      }));
      console.log('处理后的上线语料数据:', upKnowledgeData.value);
      updateUpKnowledgeChartData();
    } else {
      console.error('上线语料接口返回错误:', res.data.message);
      upKnowledgeData.value = [];
    }
  } catch (err) {
    console.error('上线语料数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    upKnowledgeData.value = [];
  }
};

// 日活量时间范围选项
const timeRanges_DailyVisitsData = [
  { label: '全部', value: '0', days: '0' },
  { label: '最近7天', value: '7', days: '7' },
  { label: '最近20天', value: '20', days: '20' },
  { label: '最近30天', value: '30', days: '30' },
  { label: '最近90天', value: '90', days: '90' },
];
const selectedRange_DailyVisitsData = ref(timeRanges_DailyVisitsData[2]);

// 获取日活量
const getDailyVisitsData = async () => {
  try {
    // 检查 selectedRange_DailyVisitsData 是否存在
    if (!selectedRange_DailyVisitsData.value) {
      console.error('日活量时间范围未定义');
      dayVisitsData.value = [];
      return;
    }

    console.log('日活量请求参数:', {
      period: parseInt(selectedRange_DailyVisitsData.value.days),
      selectedRange: selectedRange_DailyVisitsData.value
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/daily-visits-statistics`, {
      period: parseInt(selectedRange_DailyVisitsData.value.days),
    });

    if (res.data.status === 'success') {
      dayVisitsData.value = res.data.data.map(item => ({
        label: item.date,
        data: item.count
      }));
      console.log(`日活量数据（${selectedRange_DailyVisitsData.value.label}）:`, dayVisitsData.value);
    } else {
      console.error('日活量接口返回错误:', res.data.message);
      dayVisitsData.value = [];
    }
  } catch (err) {
    console.error('日活量数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    dayVisitsData.value = [];
  }
};

const selectedFunction = ref('');
const functionOptions = ref([
  { value: '', label: '全部' },
  { value: '日志分析', label: '日志分析' },
  { value: '故障问答', label: '故障问答' },
  { value: '测试诊断', label: '测试诊断' },
  { value: '规范检查', label: '规范检查' }
]);

const handleFunctionChange = () => {
  updateVisitsDataOnly();
};

// 获取访问量数据
const getVisitsData = async () => {
  try {
    console.log('发送访问量请求参数:', {
      time_range: timeRange.value,
      department: selectedDepartment.value,
      field: selectedField.value,
      team: selectedTeam.value,
      member: selectedMember.value,
      function_name: selectedFunction.value,
    });

    const res = await axios.post(`${INTELDIGA_API_URL}/api/visits-statistics`, {
      time_range: timeRange.value,
      department: selectedDepartment.value,
      field: selectedField.value,
      team: selectedTeam.value,
      member: selectedMember.value,
      function_name: selectedFunction.value,
    });

    console.log('访问量响应数据:', res.data);

    if (res.data.status === 'success') {
      // 转换数据格式以适应图表
      visitsData.value = res.data.data.map(item => ({
        label: item.label,
        data: item.count || 0
      }));
      console.log('处理后的访问量数据:', visitsData.value);

      // 更新图表
      updateVisitsChartData();
    } else {
      console.error('访问量接口返回错误:', res.data.message);
      visitsData.value = [];
    }
  } catch (err) {
    console.error('访问量数据请求失败:', err);
    console.error('错误详情:', err.response?.data);
    visitsData.value = [];
  }
};

// 筛选相关数据
const timeRange = ref('week');
const selectedDepartment = ref('');
const selectedField = ref('');
const selectedTeam = ref('');
const selectedMember = ref('');
const departments = ref([]);
const fields = ref([]);
const teams = ref([]);
const members = ref([]);

// 在 onMounted 中初始化筛选数据
onMounted(async () => {
  // 初始化图表...
  const visitsChartDom = document.getElementById('visits');
  visitsChart = echarts.init(visitsChartDom);

  // 初始化使用效果数据
  await getAvailableMainScenes();

  // 获取用户信息部门结构
  await getDepartmentStructure();

  // 获取故障单信息部门结构
  await getRdcDepartmentStructure();

  departmentsUseEffect.value = [...departments.value];
  updateUseEffectFieldOptions();
  await getUseEffectMainScenes();
  await getUseEffectSceneData();

  // 初始化故障覆盖率筛选选项和数据
  departmentsSceneCover.value = [...Object.keys(rdcDepartmentStructure.value)];
  updateSceneCoverFieldOptions();
  await getFaultCoverageData();

  // 初始化上线语料数据
  await updateUpKnowledgeFieldOptions();
  await getUpKnowledgeData();
  updateUpKnowledgeChartData();

  // 初始化场景活跃度筛选选项
  departmentsSceneActive.value = [...departments.value];
  updateSceneActiveFieldOptions();
  await getSceneActiveData();

    // 初始化主场景列表
  await getMainScenes();
  await getFilteredSceneActiveData();

  await handleUpdate();
});

// 根据故障单信息获取部门结构的方法
const getRdcDepartmentStructure = async () => {
  try {
    const res = await axios.get(`${INTELDIGA_API_URL}/api/rdc-department-field-team`);
    if (res.data) {
      // 保存完整的部门结构数据
      rdcDepartmentStructure.value = res.data;
    }
  } catch (err) {
    console.error('获取组织结构失败:', err);
  }
};

// 部门结构数据引用
const rdcDepartmentStructure = ref({});

// 根据用户信息获取部门结构的方法
const getDepartmentStructure = async () => {
  try {
    const res = await axios.get(`${INTELDIGA_API_URL}/api/department-field-team`);
    if (res.data) {
      // 保存完整的部门结构数据
      departmentStructure.value = res.data;
      departments.value = Object.keys(res.data);

      // 初始化其他选项
      updateFieldOptions();
      updateTeamOptions();
      updateMemberOptions();

      updateUpKnowledgeFieldOptions();

      // 使用效果筛选也初始化
      departmentsUseEffect.value = [...departments.value];
      updateUseEffectFieldOptions();
    }
  } catch (err) {
    console.error('获取组织结构失败:', err);
  }
};

// 部门结构数据引用
const departmentStructure = ref({});

// 更新领域选项的方法
const updateFieldOptions = () => {
  if (selectedDepartment.value && departmentStructure.value[selectedDepartment.value]) {
    fields.value = Object.keys(departmentStructure.value[selectedDepartment.value]);
  } else {
    fields.value = [];
  }
  selectedField.value = '';
  // 清空后续选项
  selectedTeam.value = '';
  selectedMember.value = '';
  updateTeamOptions();
};

// 修改更新团队选项的方法
const updateTeamOptions = () => {
  if (selectedDepartment.value && selectedField.value &&
      departmentStructure.value[selectedDepartment.value]?.[selectedField.value]) {
    teams.value = Object.keys(departmentStructure.value[selectedDepartment.value][selectedField.value]);
  } else {
    teams.value = [];
  }
  selectedTeam.value = '';
  // 清空成员选项
  selectedMember.value = '';
  updateMemberOptions();
};

// 修改更新成员选项的方法
const updateMemberOptions = () => {
  if (selectedDepartment.value && selectedField.value && selectedTeam.value &&
      departmentStructure.value[selectedDepartment.value]?.[selectedField.value]?.[selectedTeam.value]) {
    const teamMembers = departmentStructure.value[selectedDepartment.value][selectedField.value][selectedTeam.value];
    members.value = Object.keys(teamMembers).map(account => ({
      account,
      name: teamMembers[account]
    }));
  } else {
    members.value = [];
  }
  selectedMember.value = '';
};

// 修改筛选变化处理函数
const handleDepartmentChange = (dept) => {
  selectedDepartment.value = dept;
  updateFieldOptions();
  updateVisitsDataOnly();
};

const handleFieldChange = (field) => {
  selectedField.value = field;
  updateTeamOptions();
  updateVisitsDataOnly();
};

const handleTeamChange = (team) => {
  selectedTeam.value = team;
  updateMemberOptions();
  updateVisitsDataOnly();
};

const handleFilterChange = () => {
  updateVisitsDataOnly();
};

const updateVisitsDataOnly = async () => {
  try {
    await getVisitsData();
    updateVisitsChartData();
  } catch (error) {
    console.error('调用量数据更新失败:', error);
  }
};

// 日活量时间范围变更处理
const handleDailyVisitsTimeRangeChange = async (value) => {
  selectedRange_DailyVisitsData.value = timeRanges_DailyVisitsData.find(
    item => item.value === value
  );
  await getDailyVisitsData();
  updateDayVisitsChartData();
};

// 使用效果数据导出
const exportUseEffectData = async () => {
  try {
    MessagePlugin.loading('正在生成使用效果导出文件...');

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-use-effect-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({

        department: selectedDepartmentUseEffect.value,
        field: selectedFieldUseEffect.value,
        team: selectedTeamUseEffect.value,
        member: selectedMemberUseEffect.value,
        mainscene: selectedMainSceneUseEffect.value,
        subscene: selectedSubSceneUseEffect.value,
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('使用效果导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();
    console.log('使用效果Blob大小:', blob.size);

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `使用效果统计_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`使用效果数据导出开始: ${filename}`);

  } catch (err) {
    console.error('使用效果数据导出失败:', err);
    let errorMessage = '使用效果数据导出失败';
    if (err.message) {
      errorMessage = err.message;
    }
    MessagePlugin.error(errorMessage);
  }
};

// 故障覆盖率导出功能
const exportFaultCoverageData = async () => {
  try {
    MessagePlugin.loading('正在生成故障覆盖率导出文件...');

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-fault-coverage-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        time_range: timeRangeSceneCover.value,
        department: selectedDepartmentSceneCover.value,
        field: selectedFieldSceneCover.value,
        team: selectedTeamSceneCover.value,
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('故障覆盖率导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();
    console.log('故障覆盖率Blob大小:', blob.size);

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `故障覆盖率统计_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`故障覆盖率数据导出开始: ${filename}`);

  } catch (err) {
    console.error('故障覆盖率数据导出失败:', err);
    let errorMessage = '故障覆盖率数据导出失败';
    if (err.message) {
      errorMessage = err.message;
    }
    MessagePlugin.error(errorMessage);
  }
};

// 场景活跃度导出功能
const exportSceneActiveData = async () => {
  try {
    MessagePlugin.loading('正在生成场景活跃度导出文件...');

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-scene-active-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        time_range: timeRangeSceneActive.value,
        department: selectedDepartmentSceneActive.value,
        field: selectedFieldSceneActive.value,
        team: selectedTeamSceneActive.value,
        member: selectedMemberSceneActive.value,
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('场景活跃度导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();
    console.log('场景活跃度Blob大小:', blob.size);

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `场景活跃度统计_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`场景活跃度数据导出开始: ${filename}`);

  } catch (err) {
    console.error('场景活跃度数据导出失败:', err);
    let errorMessage = '场景活跃度数据导出失败';
    if (err.message) {
      errorMessage = err.message;
    }
    MessagePlugin.error(errorMessage);
  }
};

// 语料录入记录导出功能
const exportKnowledgeRecords = async () => {
  try {
    MessagePlugin.loading('正在生成语料录入记录导出文件...');
    const response = await fetch(`${INTELDIGA_API_URL}/api/export-knowledge-records`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      // 尝试读取错误信息
      const errorText = await response.text();
      console.error('语料录入记录导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `语料录入记录_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`语料录入记录导出开始: ${filename}`);

  } catch (err) {
    console.error('语料录入记录导出失败:', err);

    let errorMessage = '语料录入记录导出失败';
    if (err.message) {
      errorMessage = err.message;
    }

    MessagePlugin.error(errorMessage);
  }
};

// 上线语料导出功能
const exportUpKnowledgeData = async () => {
  try {
    console.log('开始导出上线语料数据...');
    MessagePlugin.loading('正在生成上线语料导出文件...');

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-up-knowledge-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        time_range: timeRangeUpKnowledge.value,
        field: selectedFieldUpKnowledge.value,
        team: selectedTeamUpKnowledge.value,
      })
    });

    console.log('上线语料导出响应状态:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('上线语料导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();
    console.log('上线语料Blob大小:', blob.size);

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `上线语料统计_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`上线语料数据导出开始: ${filename}`);

  } catch (err) {
    console.error('上线语料数据导出失败:', err);
    let errorMessage = '上线语料数据导出失败';
    if (err.message) {
      errorMessage = err.message;
    }
    MessagePlugin.error(errorMessage);
  }
};

// 导出访问量
const exportStatistics = async () => {
  try {
    console.log('开始正式导出...');

    const response = await fetch(`${INTELDIGA_API_URL}/api/export-time-range-visits`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        time_range: timeRange.value,
        department: selectedDepartment.value,
        field: selectedField.value,
        team: selectedTeam.value,
        member: selectedMember.value,
        function_name: selectedFunction.value,
      })
    });

    console.log('Fetch响应状态:', response.status);
    console.log('Fetch响应ok:', response.ok);

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`);
    }

    const blob = await response.blob();
    console.log('Blob大小:', blob.size);

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // 获取文件名
    let filename = `访问统计_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    MessagePlugin.success(`文件下载开始: ${filename}`);

  } catch (err) {
    console.error('正式导出失败:', err);
    MessagePlugin.error('导出失败: ' + err.message);
  }
};

// 语料录入记录导出功能
const exportRdcCheckRecords = async () => {
  try {
    MessagePlugin.loading('正在生成RDC检查记录导出文件...');
    const response = await fetch(`${INTELDIGA_API_URL}/api/export-rdc-check-records`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    if (!response.ok) {
      // 尝试读取错误信息
      const errorText = await response.text();
      console.error('RDC检查记录导出服务器错误:', errorText);
      throw new Error(`HTTP错误: ${response.status} - ${errorText}`);
    }

    const blob = await response.blob();

    if (blob.size === 0) {
      throw new Error('服务器返回空文件');
    }

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    let filename = `RDC检查记录_${new Date().toISOString().split('T')[0]}.csv`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const matches = contentDisposition.match(/filename="?([^"]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);

    MessagePlugin.success(`RDC检查记录导出开始: ${filename}`);

  } catch (err) {
    console.error('RDC检查记录导出失败:', err);

    let errorMessage = 'RDC检查记录导出失败';
    if (err.message) {
      errorMessage = err.message;
    }

    MessagePlugin.error(errorMessage);
  }
};

// 更新日访问量图表
function updateDayVisitsChartData() {
  if (!dayVisitsData.value || dayVisitsData.value.length === 0) {
    console.log('没有日活量数据可显示');
    return;
  }

  const labels = dayVisitsData.value.map((item) => item.label);
  const values = dayVisitsData.value.map((item) => item.data);

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}<br/>${params[0].marker} 日活量: ${params[0].value} 人次`;
      },
    },
    legend: {
      data: ['日活量'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45,
        interval: 0, // 显示所有标签
        formatter: function(value) {
          // 对于20天数据，可以完整显示日期
          return value;
        }
      },
    },
    yAxis: {
      type: 'value',
      name: '日活量（人次）',
      nameLocation: 'middle',
      nameGap: 35,
    },
    series: [
      {
        name: '日活量',
        type: 'bar',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2378f7' },
              { offset: 0.7, color: '#2378f7' },
              { offset: 1, color: '#83bff6' }
            ])
          }
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
  dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',  // 明确指定为滑动条类型
          start: 0,        // 起始位置设为0%
          end: 100,        // 结束位置设为100%，但根据数据量动态调整
          handleSize: 8,
          bottom: 10,
          height: 20,
          borderColor: '#e8eaec',
          fillerColor: 'rgba(135,206,250,0.2)',
          backgroundColor: '#f5f7fa',
          showDetail: false
        }
      ]
  };

  if (dayVisitsChart) {
    dayVisitsChart.setOption(option, true);
  }
}

// 更新访问量图表
function updateVisitsChartData() {
  const labels = visitsData.value.map((item) => item.label);
  const values = visitsData.value.map((item) => item.data);

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}<br/>${params[0].marker} 访问量: ${params[0].value} 人次`;
      },
    },
    legend: {
      data: ['总访问量'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45,
        interval: 0 // 显示所有标签
      },
    },
    yAxis: {
      type: 'value',
      name: '总访问量（人次）',
      nameLocation: 'middle',
      nameGap: 35,
    },
    series: [
      {
        name: '总访问量',
        type: 'line',
        data: values,
        itemStyle: {
          color: '#52c41a'
        },
        lineStyle: {
          width: 3,
          shadowColor: 'rgba(82,196,26,0.3)',
          shadowBlur: 10,
          shadowOffsetY: 8
        },
        smooth: true,
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(82,196,26,0.6)' },
            { offset: 1, color: 'rgba(82,196,26,0.1)' }
          ])
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ]
  };

  if (visitsChart) {
    visitsChart.setOption(option, true);
  }
}

// 更新上线语料量图表
function updateUpKnowledgeChartData() {
  if (!upKnowledgeData.value || upKnowledgeData.value.length === 0) {
    console.log('没有上线语料数据可显示');
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 16
        }
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    };
    if (upKnowledgeChart) {
      upKnowledgeChart.setOption(option, true);
    }
    return;
  }

  const labels = upKnowledgeData.value.map((item) => item.label);
  const values = upKnowledgeData.value.map((item) => item.data);

  // 计算Y轴的最大值，确保显示整数
  const maxValue = Math.max(...values);
  const yMax = maxValue <= 0 ? 5 : Math.ceil(maxValue * 1.2); // 留20%的余量

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}<br/>${params[0].marker} 上线语料: ${params[0].value} 篇`;
      },
    },
    legend: {
      data: ['上线语料数量'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45,
        interval: 0 // 显示所有标签
      },
    },
    yAxis: {
      type: 'value',
      name: '上线语料（篇）',
      nameLocation: 'middle',
      nameGap: 35,
      min: 0, // 从0开始
      max: yMax, // 设置最大值
      interval: Math.ceil(yMax / 5), // 设置合适的间隔
      axisLabel: {
        formatter: function(value) {
          return Math.round(value); // 确保显示整数
        }
      }
    },
    series: [
      {
        name: '上线语料数量',
        type: 'bar',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ff9f7f' },
            { offset: 0.5, color: '#ff6b6b' },
            { offset: 1, color: '#c44569' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff7979' },
              { offset: 0.7, color: '#ff7979' },
              { offset: 1, color: '#ff9f7f' }
            ])
          }
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ]
  };

  if (upKnowledgeChart) {
    upKnowledgeChart.setOption(option, true);
  }
}

const knowledgeRecordColumns = [
  { colKey: 'scene', title: '场景', width: 120 },
  { colKey: 'subScene', title: '子场景', width: 150 },
  { colKey: 'account', title: '触发人', width: 100 },
  {
    colKey: 'time',
    title: '触发时间',
    width: 160,
    cell: (h, { row }) => {
      // 格式化时间显示
      if (row.time) {
        const date = new Date(row.time);
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      return row.time || '';
    }
  },
  {
    colKey: 'status',
    title: '状态',
    width: 100,
    cell: (h, { row }) => {
      const statusConfig = {
        '已完成': { theme: 'success', content: '已完成' },
        '进行中': { theme: 'warning', content: '进行中' },
        '待审核': { theme: 'default', content: '待审核' }
      };
      const config = statusConfig[row.status] || { theme: 'default', content: row.status };
      return <t-tag theme={config.theme} variant="light">{config.content}</t-tag>;
    }
  },
];

//  Started by AICoder, pid:b93d63f7a8u5b78140e90a9ee0717558f738e3d1
const rdcCheckRecordColumns = [
  {
    colKey: 'department',
    title: '部门',
    width: 100,
  },
  {
    colKey: 'work_item_id',
    title: '标识',
    width: 100,
  },
  {
    colKey: 'work_item_name',
    title: '标题',
    width: 100,
  },
  {
    colKey: 'work_item_type',
    title: '工作项类型',
    width: 100,
  },
  {
    colKey: 'work_item_status',
    title: '状态',
    width: 100,
  },
  {
    colKey: 'check_item',
    title: '检查项',
    width: 100,
  },
  {
    colKey: 'check_result',
    title: '检查结果',
    width: 100,
    render: (value) => <span>{value == 1 ? '通过' : '未通过'}</span>,
    cell: (h, { row }) => {
      const statusConfig = [
        { theme: 'warning', content: '未通过' },
        { theme: 'success', content: '通过' }
      ];
      const config = statusConfig[row.check_result] || { theme: 'default', content: row.status };
      return <t-tag theme={config.theme} variant="light">{config.content}</t-tag>;
    }
  },
  {
    colKey: 'message',
    title: '详细信息',
    width: 200,
  },
  {
    colKey: 'updatetime',
    title: '时间',
    width: 100,
  },
];
//  Ended by AICoder, pid:b93d63f7a8u5b78140e90a9ee0717558f738e3d1

// 预定义一组美观的颜色
const colorPalette = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'];

function updateSceneActiveChartData() {
  if (!sceneActiveData.value || sceneActiveData.value.length === 0) {
    console.log('没有场景活跃度数据可显示');

    // 显示无数据状态
    const option = {
      title: {
        text: '暂无场景活跃度数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 16
        }
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    };

    if (sceneActiveChart) {
      sceneActiveChart.setOption(option, true);
    }
    return;
  }

  // 提取所有唯一的时间点作为 X 轴
  const timePointsSet = new Set();
  sceneActiveData.value.forEach(series => {
    series.data.forEach(point => {
      timePointsSet.add(point.time);
    });
  });
  const timePoints = Array.from(timePointsSet).sort(); // 按时间排序

  // 构建 ECharts series
  const series = sceneActiveData.value.map((item, index) => ({
    name: item.label,
    type: 'line',
    data: timePoints.map(time => {
      const point = item.data.find(d => d.time === time);
      return point ? point.value : 0; // 如果没有数据，显示0
    }),
    smooth: true,
    label: {
      show: true,
      position: 'top',
      formatter: (params) => {
        return params.value > 0 ? params.value : '';
      }
    },
    itemStyle: {
      color: colorPalette[index % colorPalette.length]
    },
    lineStyle: {
      width: 3,
      shadowColor: 'rgba(0,0,0,0.1)',
      shadowBlur: 5,
      shadowOffsetY: 3
    },
    emphasis: {
      focus: 'series',
      lineStyle: {
        width: 4
      }
    }
  }));

  const option = {
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'item',
        confine: true,
        position: function (point, params, dom, rect, size) {
          const x = point[0];
          const y = point[1];
          const viewWidth = size.viewSize[0];
          const viewHeight = size.viewSize[1];
          const tooltipWidth = dom.offsetWidth || 200;
          const tooltipHeight = dom.offsetHeight || 100;

          let posX = x;
          let posY = y;

          if (x + tooltipWidth > viewWidth) {
            posX = x - tooltipWidth - 10;
          } else {
            posX = x + 10;
          }

          if (y + tooltipHeight > viewHeight) {
            posY = y - tooltipHeight - 10;
          } else {
            posY = y + 10;
          }

          return [posX, posY];
        },
        formatter: (params) => {
          const time = timePoints[params.dataIndex];
          const sceneData = sceneActiveData.value.find(s => s.label === params.seriesName);
          const pointData = sceneData?.data.find(d => d.time === time);

          let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${time}</div>`;
          tooltip += `
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 4px 0;">
              <span>${params.marker} ${params.seriesName}</span>
              <span style="font-weight: bold; margin-left: 20px;">${params.value} 次</span>
            </div>
          `;

          if (pointData && pointData.user_count > 0) {
            tooltip += `
              <div style="font-size: 12px; color: #666; margin-left: 16px;">
                使用人数: ${pointData.user_count}人
              </div>
            `;
          }

          return tooltip;
        },
      },
      legend: {
      data: sceneActiveData.value.map(item => item.label),
      top: 0,
      type: 'scroll',
      pageIconColor: '#2c3e50',
      pageTextStyle: {
        color: '#2c3e50'
      }
    },
    xAxis: {
      type: 'category',
      data: timePoints,
      axisLabel: {
        rotate: 45,
        interval: 0 // 显示所有标签
      },
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '使用次数',
      nameLocation: 'middle',
      nameGap: 35,
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series: series,
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '20%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        bottom: 10,
        height: 20,
        handleSize: 8,
        borderColor: '#e8eaec',
        fillerColor: 'rgba(135,206,250,0.2)',
        backgroundColor: '#f5f7fa'
      }
    ]
  };

  if (sceneActiveChart) {
    sceneActiveChart.setOption(option, true);
  }
}

function updateSceneCoverChartData() {
  if (!sceneCoverData.value || sceneCoverData.value.length === 0) {
    console.log('没有故障覆盖率数据可显示');

    const option = {
      title: {
        text: '暂无故障覆盖率数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 16
        }
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    };

    if (sceneCoverChart) {
      sceneCoverChart.setOption(option, true);
    }
    return;
  }

  const validData = sceneCoverData.value.filter(item =>
    item.label && item.label !== 'null' && item.label !== ''
  );

  if (validData.length === 0) {
    console.log('过滤后没有有效的故障覆盖率数据');

    const option = {
      title: {
        text: '暂无有效的故障覆盖率数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 16
        }
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    };

    if (sceneCoverChart) {
      sceneCoverChart.setOption(option, true);
    }
    return;
  }

  const labels = validData.map((item) => item.label);
  const coverValues = validData.map((item) => item.cover || 0);
  const uncoverValues = validData.map((item) => item.uncover || 0);

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const coverParam = params[0];
        const uncoverParam = params[1];
        const total = (coverParam.value || 0) + (uncoverParam.value || 0);
        const coverageRate = total > 0 ? ((coverParam.value / total) * 100).toFixed(1) : 0;

        return `${coverParam.axisValue}<br/>
                ${coverParam.marker} ${coverParam.seriesName}: ${coverParam.value || 0} 个<br/>
                ${uncoverParam.marker} ${uncoverParam.seriesName}: ${uncoverParam.value || 0} 个<br/>
                总计: ${total} 个<br/>
                覆盖率: ${coverageRate}%`;
      },
    },
    legend: {
      data: ['已覆盖', '未覆盖'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45,
        interval: 0
      },
    },
    yAxis: {
      type: 'value',
      name: '故障数量（个）',
      nameLocation: 'middle',
      nameGap: 35,
    },
    series: [
      {
        name: '已覆盖',
        type: 'bar',
        stack: '总量',
        data: coverValues,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#5cdbd3' },
            { offset: 0.5, color: '#36cfc9' },
            { offset: 1, color: '#13c2c2' }
          ])
        },
        label: {
          show: true,
          position: 'inside',
          valueAnimation: true,
          formatter: '{c}',
          color: '#fff'
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#36cfc9' },
              { offset: 0.7, color: '#36cfc9' },
              { offset: 1, color: '#5cdbd3' }
            ])
          }
        },
      },
      {
        name: '未覆盖',
        type: 'bar',
        stack: '总量',
        data: uncoverValues,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ff9c6e' },
            { offset: 0.5, color: '#ff7a45' },
            { offset: 1, color: '#fa541c' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff7a45' },
              { offset: 0.7, color: '#ff7a45' },
              { offset: 1, color: '#ff9c6e' }
            ])
          }
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        bottom: 10,
        height: 20,
        handleSize: 8,
        borderColor: '#e8eaec',
        fillerColor: 'rgba(135,206,250,0.2)',
        backgroundColor: '#f5f7fa'
      }
    ]
  };

  if (sceneCoverChart) {
    sceneCoverChart.setOption(option, true);
  }
}

function updateUseEffectSceneChartData() {
  if (!useEffectSceneData.value || useEffectSceneData.value.length === 0) {
    console.log('没有使用效果数据可显示');

    // 显示无数据状态
    const option = {
      title: {
        text: '暂无使用效果数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 16
        }
      },
      xAxis: {
        show: false
      },
      yAxis: {
        show: false
      }
    };

    if (useEffectSceneChart) {
      useEffectSceneChart.setOption(option, true);
    }
    return;
  }

  const labels = useEffectSceneData.value.map((item) => {
    const label = item.label;
    if (label.length > 15) {
      return label.substring(0, 15) + '...';
    }
    return label;
  });

  const fullLabels = useEffectSceneData.value.map((item) => item.label);
  const values = useEffectSceneData.value.map((item) => item.value);

  const yMax = 5;
  const yMin = 0;

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter: (params) => {
        const index = params[0].dataIndex;
        const fullLabel = fullLabels[index];
        const value = params[0].value;

        let displayLabel = fullLabel;
        if (fullLabel.length > 20) {
          const middleIndex = Math.floor(fullLabel.length / 2);
          let breakIndex = fullLabel.lastIndexOf('-', middleIndex);
          if (breakIndex === -1) {
            breakIndex = middleIndex;
          }
          displayLabel = fullLabel.substring(0, breakIndex + 1) + '<br/>' + fullLabel.substring(breakIndex + 1);
        }

        return `<div style="max-width: 300px; word-wrap: break-word;">
                  <strong>${displayLabel}</strong><br/>
                  平均得分: <b>${value}</b> 分
                </div>`;
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {
        color: '#333',
        fontSize: 12
      },
      extraCssText: 'box-shadow: 0 2px 8px rgba(0,0,0,0.15); max-width: 350px;'
    },
    legend: {
      data: ['使用效果'],
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45,
        interval: 0,
        fontSize: 12,
        margin: 10,
        formatter: function(value) {
          if (value.length > 20) {
            return value.substring(0, 20) + '...';
          }
          return value;
        }
      },
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      name: '平均得分',
      nameLocation: 'middle',
      nameGap: 35,
      min: yMin,
      max: yMax,
      interval: 1,
      axisLabel: {
        formatter: '{value}'
      },
      splitLine: {
        lineStyle: {
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '使用效果',
        type: 'bar',
        data: values,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          valueAnimation: true,
          formatter: '{c}',
          fontSize: 12,
          fontWeight: 'bold'
        },
        barWidth: '60%',
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2378f7' },
              { offset: 0.7, color: '#2378f7' },
              { offset: 1, color: '#83bff6' }
            ])
          }
        },
      },
    ],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '20%',
      top: '10%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        show: true,
        start: 0,
        end: 100,
        bottom: 10,
        height: 20,
        handleSize: 8,
        borderColor: '#e8eaec',
        fillerColor: 'rgba(135,206,250,0.2)',
        backgroundColor: '#f5f7fa'
      }
    ]
  };

  if (useEffectSceneChart) {
    useEffectSceneChart.setOption(option, true);
  }
}

function updateUseEffectDayChartData() {
  if (!useEffectDayData.value || useEffectDayData.value.length === 0) {
    return;
  }

  // 提取所有唯一的时间点作为 X 轴
  const timePointsSet = new Set();
  useEffectDayData.value.forEach(series => {
    series.data.forEach(point => {
      timePointsSet.add(point.time);
    });
  });
  const timePoints = Array.from(timePointsSet).sort(); // 按时间排序

  // 构建 ECharts series
  const series = useEffectDayData.value.map((item, index) => ({
    name: item.label,
    type: 'line',
    data: timePoints.map(time => {
      const point = item.data.find(d => d.time === time);
      return point ? point.value : null; // 如果某时间点无数据，用 null
    }),
    smooth: true,
    label: {
      show: true,
      position: 'top',
      valueAnimation: true,
      formatter: '{c}',
    },
    itemStyle: {
      color: colorPalette[index % colorPalette.length]
    },
    lineStyle: {
      width: 3,
      shadowColor: 'rgba(0,0,0,0.1)',
      shadowBlur: 5,
      shadowOffsetY: 3
    },
    emphasis: {
      lineStyle: {
        width: 4
      }
    }
  }));

  const option = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const time = timePoints[params[0].dataIndex]; // 获取对应时间
        let tooltip = `${time}<br/>`;
        params.forEach(param => {
          tooltip += `${param.marker} ${param.seriesName}: ${param.value || 0} 次<br/>`;
        });
        return tooltip;
      },
    },
    legend: {
      data: useEffectDayData.value.map(item => item.label),
      top: 0,
      type: 'scroll',
      pageIconColor: '#2c3e50',
      pageTextStyle: {
        color: '#2c3e50'
      }
    },
    xAxis: {
      type: 'category',
      data: timePoints,
      axisLabel: {
        rotate: 45,
        interval: 0 // 显示所有标签
      },
    },
    yAxis: {
      type: 'value',
      name: '平均得分',
      nameLocation: 'middle',
      nameGap: 35,
    },
    series: series,
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '20%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ]
  };

  if (useEffectDayChart) {
    useEffectDayChart.setOption(option, true);
  }
}

// 初始化图表
onMounted(async () => {

  const visitsChartDom = document.getElementById('visits');
  visitsChart = echarts.init(visitsChartDom);

  const upKnowledgeChartDom = document.getElementById('upKnowledge');
  upKnowledgeChart = echarts.init(upKnowledgeChartDom);

  const sceneActiveChartDom = document.getElementById('sceneActive');
  sceneActiveChart = echarts.init(sceneActiveChartDom);

  const sceneCoverChartDom = document.getElementById('sceneCover');
  sceneCoverChart = echarts.init(sceneCoverChartDom);

  const useEffectSceneChartDom = document.getElementById('useEffectScene');
  useEffectSceneChart = echarts.init(useEffectSceneChartDom);

  // 添加 resize 事件监听器
  window.addEventListener('resize', () => {
    if (visitsChart) visitsChart.resize();
    if (upKnowledgeChart) upKnowledgeChart.resize();
    if (sceneActiveChart) sceneActiveChart.resize();
    if (sceneCoverChart) sceneCoverChart.resize();
    if (useEffectSceneChart) useEffectSceneChart.resize();
  });

  // 获取初始数据
  await handleUpdate();
});

// 监听数据变化
// watch(
//   [aiAccessChartData, selectedRange],
//   () => {
//     if (aiAccessChartData.value.length > 0) {
//       updateAiChartData();
//     }
//   },
//   { deep: true },
// );


// 切换时间范围
// async function handleTimeRangeChange(days) {
//   const numDays = parseInt(days, 10);
//   const range = timeRanges.find((r) => parseInt(r.days, 10) === numDays);

//   if (range) {
//     selectedRange.value = range;

//     // 获取新数据
//     const [aiAccessData, websiteAccessData, aiVisitorData, websiteVisitorData] = await Promise.all([
//       getAiAccessData(),
//       getWebsiteAccessData(),
//       getAiVisitorStats(),
//       getWebsiteVisitorStats(),
//     ]);

//     // 更新数据
//     aiAccessChartData.value = aiAccessData;
//     websiteAccessChartData.value = websiteAccessData;
//     aiVisitorStatsData.value = aiVisitorData;
//     websiteVisitorStatsData.value = websiteVisitorData;

//     // 更新视图
//     updateAiChartData();
//     updateAiVisitorStats();
//     updateWebsiteChartData();
//     updateWebsiteVisitorStats();
//   }
// }

// 更新所有数据
const handleUpdate = async () => {
  try {
    // 显示加载提示
    MessagePlugin.loading('数据更新中...');

    // 并行获取所有数据
    await Promise.all([
      getVisitsData(),
      getUpKnowledgeData(),
      getSceneActiveData() ,
      getKnowledgeRecords(),
      getUseEffectSceneData(),
      getRdcCheckRecords(),
      // 其他图表数据获取...
    ]);

    // // 更新数据
    // aiAccessChartData.value = aiAccessData;
    // websiteAccessChartData.value = websiteAccessData;
    // aiVisitorStatsData.value = aiVisitorData;
    // websiteVisitorStatsData.value = websiteVisitorData;

    // 更新视图
    updateVisitsChartData();
    updateUpKnowledgeChartData();
    updateSceneActiveChartData();
    updateSceneCoverChartData();
    updateUseEffectSceneChartData();
    // 隐藏加载提示
    MessagePlugin.success('数据更新成功');
  } catch (error) {
    console.error('数据更新失败:', error);
    MessagePlugin.error('数据更新失败');
  }
};

// 组件销毁前清理图表实例
onBeforeUnmount(() => {
  if (visitsChart) {
    visitsChart.dispose();
    visitsChart = null;
  }
  if (upKnowledgeChart) {
    upKnowledgeChart.dispose();
    upKnowledgeChart = null;
  }
  if (sceneActiveChart) {
    sceneActiveChart.dispose();
    sceneActiveChart = null;
  }
  if (sceneCoverChart) {
    sceneCoverChart.dispose();
    sceneCoverChart = null;
  }
  if (useEffectSceneChart) {
    useEffectSceneChart.dispose();
    useEffectSceneChart = null;
  }
});

const jumpToChatPage = () => {
  router.push('/ai/diag'); // 根据实际路由路径调整
};

</script>

<style scoped>
/* 场景分页选择器样式*/
.scene-pagination-selector {
  width: 100%;
  padding: 16px 0;
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.scene-pagination-controls {
  display: flex;
  justify-content: center;
}

/* 筛选控件样式 */
.filter-controls {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.filter-select {
  width: 120px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.kanban-main {
  padding-top: 50px;

  .kanban-card {
    flex: 1;
    min-width: 800px; /* 设置最小宽度 */
  }

  :deep(.t-card) {
    display: flex;
    padding: 10px;
    flex-direction: column;
    height: 600px; /* 固定高度 */
    overflow: hidden; /* 防止内部溢出 */
  }

  :deep(.t-card__title) {
    font-size: 20px;
    font-weight: 400;
    flex-shrink: 0;
  }

  :deep(.t-card__actions) {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
  }

  :deep(.t-card__body) {
    flex: 1;
    padding: 20px;
    display: flex;
    flex-direction: column;
    overflow: hidden; /* 关键：限制内容溢出 */
  }

  .back-to-chat {
    position: absolute; /* 或 absolute，视你的布局而定 */
    z-index: 4000; /* 确保浮在最上层 */
    top: 70px; /* 距离页面顶部的距离为0 */
    left: 250px; /* 距离页面左边的距离为0 */
    margin-left: 0px;
    box-shadow:
      0px 4px 12px rgba(0, 0, 0, 0.15),
      0px 16px 32px rgba(0, 0, 0, 0.2),
      0px 32px 48px rgba(0, 0, 0, 0.15);
  }

:deep(.unified-height-card) {
  min-height: 650px !important;
  max-height: 700px !important;
  height: auto !important;
}

:deep(.up-knowledge-card .t-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-bottom: 8px;
  min-height: 580px;
}

:deep(.up-knowledge-card #upKnowledge) {
  flex: 1;
  min-height: 320px;
  max-height: 400px;
}

:deep(.knowledge-record-card .t-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-bottom: 8px;
  min-height: 580px;
}

:deep(.knowledge-record-card .t-table) {
  flex: 1;
  max-height: none !important;
}

:deep(.knowledge-record-card .t-table__container) {
  height: 100%;
  overflow: auto;
  min-height: 450px;
  max-height: 500px;
}

:deep(.knowledge-record-card .t-pagination) {
  flex-shrink: 0;
  margin-top: auto;
  padding: 12px 0 4px;
  border-top: 1px solid #f0f0f0;
  background: white;
  position: sticky;
  bottom: 0;
  z-index: 5;
}

:deep(.t-pagination__btn) {
  margin: 0 4px;
}

:deep(.t-pagination__number) {
  margin: 0 2px;
}

:deep(.t-table__content) {
  width: 100%;
}

:deep(#upKnowledge) {
  width: 100%;
  position: relative;
}

@media (max-height: 800px) {
  :deep(.unified-height-card) {
    min-height: 600px !important;
    max-height: 650px !important;
  }

  :deep(.up-knowledge-card .t-card__body),
  :deep(.knowledge-record-card .t-card__body) {
    min-height: 520px;
  }

  :deep(.knowledge-record-card .t-table__container) {
    min-height: 380px;
    max-height: 430px;
  }

  :deep(.up-knowledge-card #upKnowledge) {
    min-height: 280px;
    max-height: 350px;
  }
}

@media (min-height: 1000px) {
  :deep(.unified-height-card) {
    min-height: 700px !important;
    max-height: 750px !important;
  }

  :deep(.up-knowledge-card .t-card__body),
  :deep(.knowledge-record-card .t-card__body) {
    min-height: 620px;
  }
}

:deep(.knowledge-record-card .t-table__body) {
  max-height: calc(100% - 40px) !important;
}

:deep(.knowledge-record-card .t-table__header) {
  position: sticky;
  top: 0;
  background: white;
  z-index: 2;
}
}
  </style>

