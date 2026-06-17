<template>
  <div class="health-monitor-container">
    <!-- 返回按钮 -->
    <t-tooltip content="返回诊断会话" placement="top">
      <t-button class="back-to-chat" size="large" theme="primary" shape="circle" variant="base" @click="jumpToChatPage">
        <icon name="arrow-left" />
      </t-button>
    </t-tooltip>

    <!-- 主内容区域 -->
    <div class="main-content-area">
      <!-- 三卡片功能区域 -->
      <div class="triple-cards-section">
        <t-card class="triple-cards-container full-width-card" :body-style="{ padding: '20px' }">
          <t-row :gutter="[20, 20]" style="width: 100%">
            <!-- 网元在线健康诊断 -->
            <t-col :xs="12" :sm="12" :md="4" :lg="4" :xl="4">
              <t-card class="online-diagnosis-trigger-card" :body-style="{ padding: '20px' }">
                <div class="card-content-wrapper">
                  <div class="icon-container">
                    <icon name="monitor" size="48px" style="color: var(--td-success-color)" />
                  </div>
                  <div class="description-container">
                    <h3>网元在线健康诊断</h3>
                    <p>实时检测网元设备运行状态，进行在线健康评估</p>
                  </div>
                  <div class="button-container">
                    <t-button theme="success" size="large" class="diagnosis-button" @click="startOnlineDiagnosis">
                      <template #icon><icon name="play-circle" /></template>
                      开始诊断
                    </t-button>
                  </div>
                </div>
              </t-card>
            </t-col>

            <!-- 网元离线健康日志分析 -->
            <t-col :xs="12" :sm="12" :md="4" :lg="4" :xl="4">
              <t-card class="upload-trigger-card" :body-style="{ padding: '20px' }">
                <div class="card-content-wrapper">
                  <div class="icon-container">
                    <icon name="file-upload" size="48px" style="color: var(--td-brand-color)" />
                  </div>
                  <div class="description-container">
                    <h3>网元离线健康日志分析</h3>
                    <p>上传网元日志文件，系统将自动解析各项健康指标数据</p>
                  </div>
                  <div class="button-container upload-button-wrapper">
                    <t-upload
                      :key="uploadKey"
                      ref="uploadRef"
                      v-model="files"
                      :request-method="uploadFile"
                      :disabled="uploading"
                      accept=".log"
                      :multiple="false"
                      :show-upload-progress="true"
                      theme="file"
                      :auto-upload="true"
                      :show-file-list="false"
                      @success="handleUploadSuccess"
                      @fail="handleUploadFail"
                    >
                      <t-button theme="primary" size="large">
                        <template #icon><icon name="upload" /></template>
                        上传日志文件
                      </t-button>
                    </t-upload>

                    <div v-if="uploadStatus" class="upload-status" :class="uploadStatus.type">
                      <t-alert :theme="uploadStatus.type === 'success' ? 'success' : 'error'" :message="uploadStatus.message" />
                    </div>

                    <div v-if="uploading" class="uploading-indicator">
                      <t-loading size="small" text="文件上传中..." />
                    </div>
                  </div>
                </div>
              </t-card>
            </t-col>

            <!-- 批量离线健康日志分析 -->
            <t-col :xs="12" :sm="12" :md="4" :lg="4" :xl="4">
              <t-card class="batch-analysis-trigger-card" :body-style="{ padding: '20px' }">
                <div class="card-content-wrapper">
                  <div class="icon-container">
                    <icon name="" size="48px" style="color: var(--td-warning-color)" />
                  </div>
                  <div class="description-container">
                    <h3>批量离线健康日志分析</h3>
                    <p>自动获取多网元离线KPI日志，批量分析并生成健康评分总表</p>
                  </div>
                  <div class="button-container">
                    <t-button theme="warning" size="large" class="batch-analysis-button" @click="openBatchAnalysisDialog">
                      <template #icon><icon name="cloud-download" /></template>
                      批量分析
                    </t-button>
                  </div>
                </div>
              </t-card>
            </t-col>
          </t-row>
        </t-card>
      </div>

        <!-- 批量分析结果表格（主界面展示） -->
        <div v-if="batchAnalysisResults.length > 0" class="batch-results-section">
          <t-card title="批量离线健康日志分析结果" class="batch-results-card full-width-card">
            <div class="batch-results-header">
              <div class="results-stats">
              <t-space>
                <t-tooltip content="总的tar文件数量">
                  <t-tag theme="primary" variant="light" style="font-weight: bold;">
                    总网元数量：{{ batchAnalysisStatistics.totalTarFiles || 0 }}
                  </t-tag>
                </t-tooltip>

                <t-tooltip content="包含KPI日志的tar文件数量">
                  <t-tag theme="success" variant="light">
                    支持网元: {{ batchAnalysisStatistics.filesWithKpi || 0 }}
                  </t-tag>
                </t-tooltip>

                <t-tooltip content="不包含KPI日志的tar文件数量">
                  <t-tag theme="warning" variant="light">
                    不支持网元: {{ (batchAnalysisStatistics.totalTarFiles || 0) - (batchAnalysisStatistics.filesWithKpi || 0) }}
                  </t-tag>
                </t-tooltip>

                <t-tooltip content="健康评分低于60分的网元数量">
                  <t-tag theme="danger" variant="light">
                    不健康网元: {{ unhealthyCount }}
                  </t-tag>
                </t-tooltip>

                <t-tooltip content="所有支持网元的平均健康评分">
                  <t-tag theme="primary" variant="light">
                    平均分: {{ averageScore }}
                  </t-tag>
                </t-tooltip>
              </t-space>
            </div>
              <div class="results-actions">
                <t-space>
                   <t-button
                    theme="warning"
                    size="small"
                    @click="exportSsdLifeData"
                    :loading="exportingSsdLife"
                  >
                    <template #icon><icon name="cloud-download" /></template>
                    SSD寿命导出
                  </t-button>
                  <t-button
                    theme="default"
                    size="small"
                    @click="showScoreRules"
                  >
                    <template #icon><icon name="info-circle" /></template>
                    得分规则
                  </t-button>
                  <t-button
                    theme="default"
                    size="small"
                    @click="clearBatchResults"
                  >
                    <template #icon><icon name="delete" /></template>
                    清空结果
                  </t-button>
                  <t-button
                    theme="primary"
                    size="small"
                    @click="batchAnalysisDialogVisible = true"
                  >
                    <template #icon><icon name="settings" /></template>
                    配置分析
                  </t-button>
                </t-space>
              </div>
            </div>

          <div style="max-height: 500px; overflow-y: auto; margin-top: 16px;">
            <t-table
              :data="batchAnalysisResults"
              :columns="batchAnalysisColumns"
              row-key="log_filename"
              :hover="true"
              :bordered="true"
              :stripe="true"
              :loading="batchAnalysisStatus.isRunning"
              size="medium"
            >
              <template #empty>
                <div class="empty-data" style="padding: 40px 0; text-align: center;">
                  <icon name="file" size="48px" style="color: var(--td-text-color-placeholder); margin-bottom: 16px;" />
                  <div style="color: var(--td-text-color-placeholder);">暂无分析结果</div>
                </div>
              </template>
            </t-table>
          </div>
        </t-card>
      </div>

      <!-- 在线健康诊断卡片 -->
      <t-card v-if="diagnosisStatusInfo.ip" title="在线健康诊断" class="online-diagnosis-card full-width-card">
        <t-space direction="vertical" style="width: 100%" size="large">
          <!-- 诊断状态 -->
          <div class="diagnosis-status">
            <t-alert
              :theme="diagnosisStatusInfo.connected ? 'success' : 'error'"
              :message="getDiagnosisStatusMessage()"
              :closable="false"
            />
          </div>

          <!-- 只在连接正常且有数据时才显示详细信息和总体评估 -->
          <template v-if="diagnosisStatusInfo.connected && combinedDiagnosisData.length > 0">
            <t-card title="网元健康详细信息" class="combined-info-card">
              <template #extra>
                <t-space size="small">
                  <t-tag v-if="diagnosisStatusInfo.ip" theme="primary" variant="light">
                    IP: {{ diagnosisStatusInfo.ip }}
                  </t-tag>
                  <t-tag v-if="diagnosisStatusInfo.shelf" theme="primary" variant="light">
                    子架: {{ diagnosisStatusInfo.shelf }}
                  </t-tag>
                  <t-tag v-if="diagnosisStatusInfo.slot" theme="primary" variant="light">
                    槽位: {{ diagnosisStatusInfo.slot }}
                  </t-tag>
                </t-space>
              </template>

              <t-space direction="vertical" style="width: 100%" size="large">
                <!-- NE 组件表格 -->
                <t-card v-if="neComponentsData.length > 0" title="NE 信息" class="sub-table-card">
                  <t-table
                    :data="neComponentsData"
                    :columns="diagnosisColumns"
                    row-key="no"
                    bordered
                    stripe
                    size="small"
                    max-height="300"
                  >
                    <template #empty>
                      <div class="empty-data">
                        <icon name="file" size="32px" />
                        <div>暂无NE组件数据</div>
                      </div>
                    </template>
                  </t-table>
                </t-card>

                <!-- 其它组件表格 -->
                <t-card v-if="otherComponentsData.length > 0" title="board 信息" class="sub-table-card">
                  <t-table
                    :data="otherComponentsData"
                    :columns="diagnosisColumns"
                    row-key="no"
                    bordered
                    stripe
                    size="small"
                    max-height="300"
                  >
                    <template #empty>
                      <div class="empty-data">
                        <icon name="file" size="32px" />
                        <div>暂无其它组件数据</div>
                      </div>
                    </template>
                  </t-table>
                </t-card>

                <div v-if="neComponentsData.length === 0 && otherComponentsData.length === 0">
                  <div class="empty-data">
                    <icon name="file" size="32px" />
                    <div>暂无数据，请先执行在线诊断</div>
                  </div>
                </div>
              </t-space>
            </t-card>

            <!-- 在线健康诊断报告 -->
            <div class="online-diagnosis-report-container">
              <t-card title="网元在线健康诊断报告" class="online-diagnosis-report-card full-width-card">
                  <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <span>网元在线健康诊断报告</span>
                    <t-button
                      theme="default"
                      size="small"
                      @click="showScoreRules"
                      style="margin-left: auto;"
                    >
                      <template #icon><icon name="info-circle" /></template>
                      得分规则
                    </t-button>
                  </div>
                </template>
                <t-space direction="vertical" size="large" style="width: 100%">
                  <!-- 在线诊断报告生成状态 -->
                  <div v-if="generatingOnlineReport" class="report-generating">
                    <t-loading size="small" text="正在生成网元在线健康诊断报告..." />
                  </div>

                  <!-- 在线诊断报告内容 -->
                  <div v-else-if="onlineDiagnosisReport" class="report-content">
                    <!-- 总体评估 -->
                    <t-card class="overall-assessment-card">
                      <template #header>
                        <div class="assessment-header">
                          <h3>总体健康评估</h3>
                          <t-tag :theme="getHealthStatusTag(onlineDiagnosisReport.overallAssessment.healthStatus)" size="large" class="health-status-tag">
                            {{ onlineDiagnosisReport.overallAssessment.healthStatus }}
                          </t-tag>
                        </div>
                      </template>

                      <t-space direction="vertical" style="width: 100%">
                        <div class="score-section">
                          <t-progress
                            theme="circle"
                            :percentage="onlineDiagnosisReport.overallAssessment.score"
                            :stroke-width="8"
                            size="large"
                            :color="getProgressColor(onlineDiagnosisReport.overallAssessment.score)"
                          />
                          <div class="score-info">
                            <h4>健康评分: {{ onlineDiagnosisReport.overallAssessment.score }}%</h4>
                            <p>{{ onlineDiagnosisReport.overallAssessment.summary }}</p>
                          </div>
                        </div>
                      </t-space>
                    </t-card>

                    <!-- 详细指标分析 -->
                    <t-card v-if="Object.keys(onlineDiagnosisReport.metricAnalysis).length > 0" title="详细指标分析" class="metric-analysis-card">
                      <t-space direction="vertical" style="width: 100%" size="large">
                        <div v-for="(analysis, metricName) in onlineDiagnosisReport.metricAnalysis" :key="metricName" class="metric-item">
                          <div class="metric-header">
                            <div class="metric-title-section">
                              <h4>{{ metricName.replace('分析', '') }}</h4>
                              <t-tag :theme="getHealthStatusTag(analysis.status)" size="small" class="status-tag">
                                {{ analysis.status }}
                              </t-tag>
                            </div>
                          </div>

                          <div class="metric-details">
                            <div class="metric-info-grid">
                              <!-- 分析内容 -->
                              <div v-if="analysis.analysis" class="info-item analysis-content">
                                <div class="info-label">
                                  <icon name="bulb" size="16px" />
                                  <span>分析</span>
                                </div>
                                <div class="info-content" v-html="formatAnalysisText(analysis.analysis)"></div>
                              </div>

                              <!-- 建议内容 -->
                              <div v-if="analysis.suggestion" class="info-item suggestion-content">
                                <div class="info-label">
                                  <icon name="lightning" size="16px" />
                                  <span>建议</span>
                                </div>
                                <div class="info-content" v-html="formatAnalysisText(analysis.suggestion)"></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </t-space>
                    </t-card>

                    <!-- 趋势分析 -->
                    <t-card v-if="onlineDiagnosisReport.trendAnalysis" title="网元健康趋势分析与预测" class="trend-analysis-card">
                      <div class="trend-content">
                        {{ onlineDiagnosisReport.trendAnalysis }}
                      </div>
                    </t-card>

                    <!-- 综合优化建议 -->
                    <t-card v-if="onlineDiagnosisReport.comprehensiveSuggestions.length > 0" title="综合优化建议" class="suggestions-card">
                      <t-space direction="vertical" style="width: 100%">
                        <div v-for="(suggestion, index) in onlineDiagnosisReport.comprehensiveSuggestions" :key="index" class="suggestion-item">
                          <t-alert theme="info" :message="suggestion" :closable="false" />
                        </div>
                      </t-space>
                    </t-card>

                    <!-- 紧急处理事项 -->
                    <t-card v-if="onlineDiagnosisReport.urgentActions.length > 0" title="紧急处理事项" class="urgent-actions-card">
                      <t-space direction="vertical" style="width: 100%" size="small">
                        <div v-for="(action, index) in onlineDiagnosisReport.urgentActions" :key="index" class="urgent-action-item">
                          <div class="urgent-marker">
                            <icon name="error-circle-filled" size="16px" />
                          </div>
                          <div class="urgent-content">{{ action }}</div>
                        </div>
                      </t-space>
                    </t-card>
                  </div>

                  <!-- 生成报告提示 -->
                  <div v-else-if="combinedDiagnosisData.length > 0 && !onlineDiagnosisReport && !generatingOnlineReport" class="auto-generate-hint">
                    <t-alert theme="info" message="系统正在生成网元在线健康诊断报告，请稍候..." />
                  </div>
                </t-space>
              </t-card>
            </div>
          </template>

          <!-- 连接异常时的提示 -->
          <template v-else-if="diagnosisStatusInfo.ip && !diagnosisStatusInfo.connected">
            <t-card class="error-card">
              <t-space direction="vertical" align="center" size="large">
                <icon name="error-circle-filled" size="48px" style="color: var(--td-error-color)" />
                <h4>连接异常</h4>
                <p>无法连接到网元设备，请检查：</p>
                <ul>
                  <li>IP地址是否正确</li>
                  <li>网络连接是否正常</li>
                  <li>设备是否在线</li>
                  <li>防火墙设置</li>
                </ul>
                <t-button theme="primary" @click="startOnlineDiagnosis">
                  重新诊断
                </t-button>
              </t-space>
            </t-card>
          </template>

          <!-- 未执行诊断时的提示 -->
          <template v-else-if="!diagnosisStatusInfo.ip">
            <t-card class="empty-card">
              <t-space direction="vertical" align="center" size="large">
                <icon name="play-circle" size="48px" style="color: var(--td-text-color-placeholder)" />
                <h4>未执行在线诊断</h4>
                <p>请点击左侧"开始网元在线健康诊断"按钮进行诊断</p>
              </t-space>
            </t-card>
          </template>
        </t-space>
      </t-card>

      <!-- 离线健康图表 -->
      <div v-if="chartData.length > 0" class="charts-container">
        <t-card title="网元离线健康指标" class="charts-card full-width-card">
          <t-space direction="vertical" size="large" style="width: 100%">
            <t-row :gutter="[16, 16]">
              <!-- CPU 使用率 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="CPU 使用率" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="cpuChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>

              <!-- 内存使用率 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="系统内存使用率" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="memChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>

              <!-- 磁盘使用率 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="SSD 磁盘使用率" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="diskChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>

              <!-- 队列使用率 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="队列使用率" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="queueChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>

              <!-- SSD 剩余寿命 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="SSD 剩余寿命" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="ssdChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>

              <!-- 有效备用块 -->
              <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                <t-card title="SSD 有效备用块" class="metric-card full-width-card">
                  <div class="chart-wrapper">
                    <div ref="spareChart" style="width: 100%; height: 300px;"></div>
                  </div>
                </t-card>
              </t-col>
            </t-row>

            <!-- 进程内存使用率图表-->
            <t-card title="进程内存使用率监控" class="process-mem-card full-width-card">
              <div class="chart-wrapper">
                <div ref="procMemChart" style="width: 100%; height: 400px;"></div>
              </div>
            </t-card>
          </t-space>
        </t-card>
      </div>

      <!-- 数据表格展示 -->
      <div v-if="chartData.length > 0" class="data-table-container">
        <t-card title="原始数据" class="full-width-card">
          <t-table
            :data="chartData"
            :columns="columns"
            row-key="timestamp"
            max-height="400"
            bordered
            stripe
          >
            <template #empty>
              <div class="empty-data">
                <icon name="file" size="48px" />
                <div>暂无数据</div>
              </div>
            </template>
          </t-table>
        </t-card>
      </div>

      <!-- 诊断报告卡片 -->
      <div class="diagnosis-report-container">
        <t-card title="网元健康诊断报告" class="diagnosis-report-card full-width-card">
            <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
              <span>网元健康诊断报告</span>
              <t-button
                theme="default"
                size="small"
                @click="showScoreRules"
                style="margin-left: auto;"
              >
                <template #icon><icon name="info-circle" /></template>
                得分规则
              </t-button>
            </div>
          </template>
          <t-space direction="vertical" size="large" style="width: 100%">
            <!-- 诊断报告生成状态 -->
            <div v-if="generatingReport" class="report-generating">
              <t-loading size="small" text="正在生成网元健康诊断报告..." />
            </div>

            <!-- 诊断报告内容 -->
            <div v-else-if="diagnosisReport" class="report-content">
              <!-- 总体评估 -->
              <t-card class="overall-assessment-card">
                <template #header>
                  <div class="assessment-header">
                    <h3>总体健康评估</h3>
                    <t-tag :theme="getHealthStatusTag(diagnosisReport.overallAssessment.healthStatus)" size="large" class="health-status-tag">
                      {{ diagnosisReport.overallAssessment.healthStatus }}
                    </t-tag>
                  </div>
                </template>

                <t-space direction="vertical" style="width: 100%">
                  <div class="score-section">
                    <t-progress
                      theme="circle"
                      :percentage="diagnosisReport.overallAssessment.score"
                      :stroke-width="8"
                      size="large"
                      :color="getProgressColor(diagnosisReport.overallAssessment.score)"
                    />
                    <div class="score-info">
                      <h4>健康评分: {{ diagnosisReport.overallAssessment.score }}%</h4>
                      <p>{{ diagnosisReport.overallAssessment.summary }}</p>
                    </div>
                  </div>
                </t-space>
              </t-card>

              <!-- 详细指标分析 -->
              <t-card v-if="Object.keys(diagnosisReport.metricAnalysis).length > 0" title="详细指标分析" class="metric-analysis-card">
                <t-space direction="vertical" style="width: 100%" size="large">
                  <div v-for="(analysis, metricName) in diagnosisReport.metricAnalysis" :key="metricName" class="metric-item">
                    <div class="metric-header">
                      <div class="metric-title-section">
                        <h4>{{ metricName.replace('分析', '') }}</h4>
                        <t-tag :theme="getHealthStatusTag(analysis.status)" size="small" class="status-tag">
                          {{ analysis.status }}
                        </t-tag>
                      </div>
                    </div>

                    <div class="metric-details">
                      <div class="metric-info-grid">
                        <!-- 当前值 -->
                        <div v-if="analysis.currentValue" class="info-item current-value">
                          <div class="info-label">
                            <icon name="chart-line" size="16px" />
                            <span>当前值</span>
                          </div>
                          <div class="info-content">{{ analysis.currentValue }}</div>
                        </div>

                        <!-- 分析内容 -->
                        <div v-if="analysis.analysis" class="info-item analysis-content">
                          <div class="info-label">
                            <icon name="bulb" size="16px" />
                            <span>分析</span>
                          </div>
                          <div class="info-content" v-html="formatAnalysisText(analysis.analysis)"></div>
                        </div>

                        <!-- 建议内容 -->
                        <div v-if="analysis.suggestion" class="info-item suggestion-content">
                          <div class="info-label">
                            <icon name="lightning" size="16px" />
                            <span>建议</span>
                          </div>
                          <div class="info-content" v-html="formatAnalysisText(analysis.suggestion)"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </t-space>
              </t-card>

              <!-- 趋势分析 -->
              <t-card v-if="diagnosisReport.trendAnalysis" title="网元健康趋势分析与预测" class="trend-analysis-card">
                <div class="trend-content">
                  {{ diagnosisReport.trendAnalysis }}
                </div>
              </t-card>

              <!-- 综合优化建议 -->
              <t-card v-if="diagnosisReport.comprehensiveSuggestions.length > 0" title="综合优化建议" class="suggestions-card">
                <t-space direction="vertical" style="width: 100%">
                  <div v-for="(suggestion, index) in diagnosisReport.comprehensiveSuggestions" :key="index" class="suggestion-item">
                    <t-alert theme="info" :message="suggestion" :closable="false" />
                  </div>
                </t-space>
              </t-card>

              <!-- 紧急处理事项 -->
              <t-card v-if="diagnosisReport.urgentActions.length > 0" title="紧急处理事项" class="urgent-actions-card">
                <t-space direction="vertical" style="width: 100%" size="small">
                  <div v-for="(action, index) in diagnosisReport.urgentActions" :key="index" class="urgent-action-item">
                    <div class="urgent-marker">
                      <icon name="error-circle-filled" size="16px" />
                    </div>
                    <div class="urgent-content">{{ action }}</div>
                  </div>
                </t-space>
              </t-card>
            </div>

            <!-- 生成报告提示 -->
            <div v-else-if="chartData.length > 0 && !diagnosisReport && !generatingReport" class="auto-generate-hint">
              <t-alert theme="info" message="系统正在生成网元健康诊断报告，请稍候..." />
            </div>

            <!-- 没有数据时提示 -->
            <div v-else-if="!chartData.length" class="no-data-prompt">
              <t-alert theme="info" message="请先上传日志文件并解析数据，然后生成网元健康诊断报告" />
            </div>
          </t-space>
        </t-card>
      </div>
    </div>

      <t-dialog
      v-model:visible="scoreRulesVisible"
      header="网元健康诊断得分规则"
      width="750px"
      :close-btn="true"
      :footer="false"
    >
      <div class="score-rules-content">
        <t-tabs :default-value="'overall'">
          <!-- 总体评分规则 -->
          <t-tab-panel value="overall" label="总体评分规则">
            <div style="padding: 16px 0;">
              <t-card title="总体健康评分标准" :bordered="true" class="rule-card">
                <t-table
                  :data="overallScoreRules"
                  :columns="ruleColumns"
                  row-key="range"
                  :bordered="true"
                  size="small"
                  style="margin-bottom: 16px;"
                />
                <t-alert
                  theme="info"
                  message="总分由各指标加权计算得出，再根据整体状态进行±10-20分的调整。"
                  :closable="false"
                  style="margin-top: 8px;"
                />
              </t-card>
            </div>
          </t-tab-panel>

          <!-- 详细指标规则 -->
          <t-tab-panel value="metrics" label="详细指标规则">
            <div style="padding: 16px 0; max-height: 500px; overflow-y: auto;">
              <t-space direction="vertical" size="large" style="width: 100%">
                <!-- CPU使用率规则 -->
                <t-card title="📊 CPU使用率" :bordered="true" class="rule-card">
                  <t-table
                    :data="cpuScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- 内存使用率规则 -->
                <t-card title="📊 内存使用率" :bordered="true" class="rule-card">
                  <t-table
                    :data="memScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- 磁盘使用率规则 -->
                <t-card title="📊 磁盘使用率" :bordered="true" class="rule-card">
                  <t-table
                    :data="diskScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- 队列使用率规则 -->
                <t-card title="📊 队列使用率" :bordered="true" class="rule-card">
                  <t-table
                    :data="queueScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- SSD剩余寿命规则 -->
                <t-card title="💾 SSD剩余寿命" :bordered="true" class="rule-card">
                  <t-table
                    :data="ssdLifeScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- SSD有效备用块规则 -->
                <t-card title="💾 SSD有效备用块" :bordered="true" class="rule-card">
                  <t-table
                    :data="ssdSpareScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>

                <!-- 进程内存使用率规则 -->
                <t-card title="⚙️ 进程内存使用率" :bordered="true" class="rule-card">
                  <t-table
                    :data="processScoreRules"
                    :columns="metricRuleColumns"
                    row-key="range"
                    :bordered="true"
                    size="small"
                  />
                </t-card>
              </t-space>
            </div>
          </t-tab-panel>
        </t-tabs>
      </div>
    </t-dialog>



    <!-- AI 聊天对话框 -->
    <t-drawer
      v-model:visible="aiDrawerVisible"
      size="600px"
      :footer="false"
      :close-btn="true"
      :size-draggable="true"
    >
      <template #header>
        <span class="title">
          Hi，我是
          <span style="color: #1a16fc; font-weight: 600">网元健康助手</span>
          AI智能体
        </span>
      </template>

      <div class="ai-chat-box">
        <t-tooltip content="新建对话" placement="top">
          <t-button
            class="ai-chat-new"
            size="large"
            theme="primary"
            shape="circle"
            variant="base"
            @click="handleNewAIChat"
          >
            <icon name="plus" />
          </t-button>
        </t-tooltip>

        <t-chat ref="aiChatRef" layout="both" :clear-history="false">
          <template v-for="(item, index) in aiChatList" :key="index">
            <t-chat-item
              :variant="item.role === 'user' ? 'base' : 'base'"
              :avatar="item.avatar"
              :name="item.name"
              :role="item.role"
              :datetime="item.datetime"
              :text-loading="item.textLoading || false"
            >
              <template #content>
                <div class="message-content" v-html="formatMessageForDisplay(item.content)"></div>
              </template>

              <template #actions v-if="item.showActions !== false">
                <t-chat-action
                  :content="item.content"
                  :operation-btn="['copy']"
                  @operation="(type, options) => handleAIOperation(type, options, index)"
                />
              </template>
            </t-chat-item>
          </template>

          <template #footer>
            <t-chat-sender
              ref="aiChatSenderRef"
              v-model="aiInputText"
              :stop-disabled="aiStreamLoading"
              :textarea-props="{ placeholder: '请输入关于健康诊断的问题...', autosize: { minRows: 2, maxRows: 12 } }"
              @stop="handleOnAIStop"
              @send="handleOnAISend"
            >
              <template #prefix>
                <div class="ai-chat-select">
                  <t-select v-model="aiSelectModelValue" :options="aiSelectModel" value-type="object"></t-select>
                </div>
              </template>
            </t-chat-sender>
          </template>
        </t-chat>
      </div>
    </t-drawer>

    <!-- 在线诊断配置弹窗 -->
    <t-drawer
      v-model:visible="onlineDiagnosisDrawerVisible"
      size="500px"
      :footer="false"
      :close-btn="true"
      placement="right"
    >
      <template #header>
        <span class="title">
          <span style="color: var(--td-success-color); font-weight: 600">网元在线健康诊断</span>
        </span>
      </template>

      <div class="online-diagnosis-config">
        <t-space direction="vertical" style="width: 100%" size="large">
          <!-- 跳板机选择 -->
          <div class="config-item">
            <t-form label-align="left" :label-width="100">
              <t-form-item label="跳板机">
                <t-select
                  v-model="onlineDiagnosisConfig.jumpName"
                  :options="jumpNameOptions"
                  placeholder="请选择跳板机"
                  clearable
                  style="width: 100%"
                />
              </t-form-item>

              <!-- 网元IP -->
              <t-form-item label="网元IP">
                <t-input
                  v-model="onlineDiagnosisConfig.targetIp"
                  placeholder="请输入网元IP地址"
                  clearable
                />
              </t-form-item>

              <!-- 子架 -->
              <t-form-item label="子架">
                <t-input
                  v-model="onlineDiagnosisConfig.shelf"
                  placeholder="请输入子架号"
                  clearable
                />
              </t-form-item>

              <!-- 槽位 -->
              <t-form-item label="槽位">
                <t-input
                  v-model="onlineDiagnosisConfig.slot"
                  placeholder="请输入槽位号"
                  clearable
                />
              </t-form-item>
            </t-form>
          </div>

          <!-- 诊断状态显示 -->
          <div v-if="onlineDiagnosisStatus.message" class="diagnosis-status-message" :class="onlineDiagnosisStatus.type">
            <t-alert
              :theme="onlineDiagnosisStatus.type"
              :message="onlineDiagnosisStatus.message"
              :closable="false"
            />
          </div>

          <!-- 诊断按钮 -->
          <div class="diagnosis-actions">
            <t-button
              theme="primary"
              size="large"
              :loading="onlineDiagnosisLoading"
              :disabled="!isFormValid"
              @click="executeOnlineDiagnosis"
              style="width: 100%"
            >
              <template #icon><icon name="play-circle" /></template>
              {{ onlineDiagnosisLoading ? '诊断中...' : '开始诊断' }}
            </t-button>
          </div>
        </t-space>
      </div>
    </t-drawer>

    <!-- 批量KPI日志分析对话框 -->
    <t-drawer
      v-model:visible="batchAnalysisDialogVisible"
      size="800px"
      :footer="false"
      :close-btn="true"
      placement="right"
    >
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <span class="title">
            <span style="color: var(--td-warning-color); font-weight: 600">批量KPI日志分析配置</span>
          </span>
          <div v-if="batchAnalysisStatus.isRunning" style="display: flex; align-items: center;">
            <t-loading size="small" style="margin-right: 8px;" />
            <span style="color: var(--td-warning-color); font-size: 12px;">分析中...</span>
          </div>
        </div>
      </template>

      <div class="batch-analysis-config">
        <t-space direction="vertical" style="width: 100%" size="large">
          <!-- 配置表单卡片 -->
          <t-card title="分析配置" :bordered="true" class="config-card">
            <t-form label-align="left" :label-width="120" :disabled="batchAnalysisStatus.isRunning">
              <t-row :gutter="[16, 16]">
                <t-col :span="24">
                  <t-form-item label="跳板机" required>
                    <t-select
                      v-model="batchAnalysisConfig.jumpServerName"
                      :options="[
                         { label: '燕郊_1B4-1实验室', value: '燕郊_1B4-1实验室' },
                      ]"
                      placeholder="请选择跳板机"
                      clearable
                      style="width: 100%"
                    />
                    <template #help>
                      选择跳板机来自动获取最新的KPI日志文件
                    </template>
                  </t-form-item>
                </t-col>
              </t-row>
            </t-form>
          </t-card>

          <!-- 分析状态卡片 -->
          <t-card title="分析状态" :bordered="true" class="status-card">
            <t-space direction="vertical" style="width: 100%">
              <t-alert
                :theme="batchAnalysisStatus.isRunning ? 'info' : batchAnalysisStatus.progress === 100 ? 'success' : 'warning'"
                :message="batchAnalysisStatus.message"
                :closable="false"
              />

              <!-- 日期信息显示 -->
              <div v-if="batchAnalysisStatus.dateInfo" class="date-info">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                  <icon name="calendar" size="16px" style="margin-right: 8px; color: var(--td-brand-color);" />
                  <span style="font-weight: 500;">文件日期分布:</span>
                </div>
                <div v-for="(count, date) in batchAnalysisStatus.dateInfo" :key="date"
                     class="date-item" :class="{'today': date === batchAnalysisStatus.today}">
                  <span>{{ date }}:</span>
                  <span style="margin-left: 8px; font-weight: 600;">{{ count }} 个文件</span>
                  <t-tag v-if="date === batchAnalysisStatus.today" theme="success" size="small" variant="light" style="margin-left: 8px;">
                    当天
                  </t-tag>
                </div>
              </div>

              <!-- 进度条 -->
              <div v-if="batchAnalysisStatus.isRunning || batchAnalysisStatus.progress > 0" class="progress-section">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                  <span>分析进度</span>
                  <span style="color: var(--td-brand-color); font-weight: 500;">
                    {{ batchAnalysisStatus.current }} / {{ batchAnalysisStatus.total }}
                  </span>
                </div>
                <t-progress
                  :percentage="batchAnalysisStatus.progress"
                  :label="false"
                  theme="line"
                  :color="batchAnalysisStatus.progress === 100 ? 'var(--td-success-color)' : 'var(--td-brand-color)'"
                  style="margin-bottom: 8px;"
                />
                <div class="progress-text">
                  <span v-if="batchAnalysisStatus.isRunning" style="color: var(--td-brand-color);">
                    <icon name="loading" style="margin-right: 4px;" />
                    正在分析中...
                  </span>
                  <span v-else style="color: var(--td-success-color);">
                    <icon name="check-circle" style="margin-right: 4px;" />
                    分析完成
                  </span>
                </div>
              </div>
            </t-space>
          </t-card>

          <!-- 操作按钮区域 -->
          <div class="batch-analysis-actions">
            <t-space style="width: 100%; justify-content: space-between;">
              <div>
                <t-button
                  theme="primary"
                  size="large"
                  :loading="batchAnalysisStatus.isRunning"
                  :disabled="!batchAnalysisConfig.jumpServerName || batchAnalysisStatus.isRunning"
                  @click="startBatchKpiAnalysis"
                >
                  <template #icon>
                    <icon :name="batchAnalysisStatus.isRunning ? 'loading' : 'play-circle'" />
                  </template>
                  {{ batchAnalysisStatus.isRunning ? '分析中...' : '开始批量分析' }}
                </t-button>

                <t-button
                  v-if="batchAnalysisStatus.isRunning"
                  theme="default"
                  size="large"
                  @click="stopBatchAnalysis"
                  style="margin-left: 12px;"
                >
                  <template #icon><icon name="stop-circle" /></template>
                  停止
                </t-button>
              </div>

              <div>
                <t-button
                  theme="default"
                  size="large"
                  @click="clearBatchResults"
                  :disabled="batchAnalysisResults.length === 0 || batchAnalysisStatus.isRunning"
                  style="margin-right: 12px;"
                >
                  <template #icon><icon name="delete" /></template>
                  清空结果
                </t-button>

                <t-button
                  theme="default"
                  size="large"
                  @click="batchAnalysisDialogVisible = false"
                >
                  <template #icon><icon name="close" /></template>
                  关闭
                </t-button>
              </div>
            </t-space>
          </div>
        </t-space>
      </div>
    </t-drawer>

    <!-- 详细分析报告弹窗 -->
    <t-drawer
      v-model:visible="detailedReportVisible"
      size="90%"
      :footer="false"
      :close-btn="true"
      placement="right"
      :destroy-on-close="false"
    >
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
          <span class="title">
            <span style="color: var(--td-brand-color); font-weight: 600">
              详细分析报告: {{ selectedReportData?.log_filename }}
            </span>
          </span>
          <div v-if="selectedReportData?.health_score" style="display: flex; align-items: center; gap: 12px;">
            <t-tag :theme="selectedReportData.health_score >= 80 ? 'success' : selectedReportData.health_score >= 60 ? 'warning' : 'danger'"
                   size="medium">
              {{ selectedReportData.health_score }}分
            </t-tag>
            <t-button size="small" theme="default" @click="detailedReportVisible = false">
              关闭
            </t-button>
          </div>
        </div>
      </template>

      <div class="detailed-report-container" v-if="selectedReportData">
        <!-- 网元信息 -->
        <t-card class="ne-info-card" :bordered="true">
          <t-space>
            <t-tag theme="primary" variant="light">
              网元名称: {{ selectedReportData.tar_filename.replace('.tar', '') }}
            </t-tag>
            <t-tag theme="primary" variant="light">
              日志文件: {{ selectedReportData.log_filename }}
            </t-tag>
            <t-tag theme="primary" variant="light">
              KPI路径: {{ selectedReportData.kpi_path }}
            </t-tag>
          </t-space>
        </t-card>

        <!-- 如果有图表数据，显示图表 -->
        <div v-if="selectedReportMetrics.length > 0" class="detailed-charts-container">
          <t-card title="健康指标趋势" class="detailed-charts-card full-width-card">
            <t-space direction="vertical" size="large" style="width: 100%">
              <t-row :gutter="[16, 16]">
                <!-- CPU 使用率 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="CPU 使用率" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedCpuChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>

                <!-- 内存使用率 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="系统内存使用率" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedMemChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>

                <!-- 磁盘使用率 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="SSD 磁盘使用率" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedDiskChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>

                <!-- 队列使用率 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="队列使用率" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedQueueChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>

                <!-- SSD 剩余寿命 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="SSD 剩余寿命" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedSsdChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>

                <!-- 有效备用块 -->
                <t-col :xs="24" :sm="12" :lg="8" :xl="6">
                  <t-card title="SSD 有效备用块" class="metric-card full-width-card">
                    <div class="chart-wrapper">
                      <div ref="detailedSpareChart" style="width: 100%; height: 300px;"></div>
                    </div>
                  </t-card>
                </t-col>
              </t-row>

              <!-- 进程内存使用率图表-->
              <t-card title="进程内存使用率监控" class="process-mem-card full-width-card">
                <div class="chart-wrapper">
                  <div ref="detailedProcMemChart" style="width: 100%; height: 400px;"></div>
                </div>
              </t-card>
            </t-space>
          </t-card>
        </div>

        <!-- 原始数据表格 -->
        <div v-if="selectedReportMetrics.length > 0" class="detailed-data-table">
          <t-card title="原始数据" class="full-width-card">
            <t-table
              :data="selectedReportMetrics"
              :columns="columns"
              row-key="timestamp"
              max-height="400"
              bordered
              stripe
            >
              <template #empty>
                <div class="empty-data">
                  <icon name="file" size="48px" />
                  <div>暂无数据</div>
                </div>
              </template>
            </t-table>
          </t-card>
        </div>

        <!-- 批量诊断报告 -->
        <div class="detailed-diagnosis-report-container" v-if="detailedDiagnosisReport">
          <t-card title="网元健康诊断报告" class="detailed-diagnosis-report-card full-width-card">
            <t-space direction="vertical" size="large" style="width: 100%">
              <!-- 总体评估 -->
              <t-card class="overall-assessment-card">
                <template #header>
                  <div class="assessment-header">
                    <h3>总体健康评估</h3>
                    <t-tag :theme="getHealthStatusTag(detailedDiagnosisReport.overallAssessment.healthStatus)"
                           size="large" class="health-status-tag">
                      {{ detailedDiagnosisReport.overallAssessment.healthStatus }}
                    </t-tag>
                  </div>
                </template>

                <t-space direction="vertical" style="width: 100%">
                  <div class="score-section">
                    <t-progress
                      theme="circle"
                      :percentage="detailedDiagnosisReport.overallAssessment.score"
                      :stroke-width="8"
                      size="large"
                      :color="getProgressColor(detailedDiagnosisReport.overallAssessment.score)"
                    />
                    <div class="score-info">
                      <h4>健康评分: {{ detailedDiagnosisReport.overallAssessment.score }}%</h4>
                      <p>{{ detailedDiagnosisReport.overallAssessment.summary }}</p>
                    </div>
                  </div>
                </t-space>
              </t-card>

              <!-- 详细指标分析 -->
              <t-card v-if="Object.keys(detailedDiagnosisReport.metricAnalysis || {}).length > 0"
                      title="详细指标分析" class="metric-analysis-card">
                <t-space direction="vertical" style="width: 100%" size="large">
                  <div v-for="(analysis, metricName) in detailedDiagnosisReport.metricAnalysis" :key="metricName" class="metric-item">
                    <div class="metric-header">
                      <div class="metric-title-section">
                        <h4>{{ metricName.replace('分析', '') }}</h4>
                        <t-tag :theme="getHealthStatusTag(analysis.status)" size="small" class="status-tag">
                          {{ analysis.status }}
                        </t-tag>
                      </div>
                    </div>

                    <div class="metric-details">
                      <div class="metric-info-grid">
                        <!-- 当前值 -->
                        <div v-if="analysis.currentValue" class="info-item current-value">
                          <div class="info-label">
                            <icon name="chart-line" size="16px" />
                            <span>当前值</span>
                          </div>
                          <div class="info-content">{{ analysis.currentValue }}</div>
                        </div>

                        <!-- 分析内容 -->
                        <div v-if="analysis.analysis" class="info-item analysis-content">
                          <div class="info-label">
                            <icon name="bulb" size="16px" />
                            <span>分析</span>
                          </div>
                          <div class="info-content" v-html="formatAnalysisText(analysis.analysis)"></div>
                        </div>

                        <!-- 建议内容 -->
                        <div v-if="analysis.suggestion" class="info-item suggestion-content">
                          <div class="info-label">
                            <icon name="lightning" size="16px" />
                            <span>建议</span>
                          </div>
                          <div class="info-content" v-html="formatAnalysisText(analysis.suggestion)"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </t-space>
              </t-card>

              <!-- 趋势分析 -->
              <t-card v-if="detailedDiagnosisReport.trendAnalysis"
                      title="网元健康趋势分析与预测" class="trend-analysis-card">
                <div class="trend-content">
                  {{ detailedDiagnosisReport.trendAnalysis }}
                </div>
              </t-card>

              <!-- 综合优化建议 -->
              <t-card v-if="detailedDiagnosisReport.comprehensiveSuggestions?.length > 0"
                      title="综合优化建议" class="suggestions-card">
                <t-space direction="vertical" style="width: 100%">
                  <div v-for="(suggestion, index) in detailedDiagnosisReport.comprehensiveSuggestions"
                       :key="index" class="suggestion-item">
                    <t-alert theme="info" :message="suggestion" :closable="false" />
                  </div>
                </t-space>
              </t-card>

              <!-- 紧急处理事项 -->
              <t-card v-if="detailedDiagnosisReport.urgentActions?.length > 0"
                      title="紧急处理事项" class="urgent-actions-card">
                <t-space direction="vertical" style="width: 100%" size="small">
                  <div v-for="(action, index) in detailedDiagnosisReport.urgentActions"
                       :key="index" class="urgent-action-item">
                    <div class="urgent-marker">
                      <icon name="error-circle-filled" size="16px" />
                    </div>
                    <div class="urgent-content">{{ action }}</div>
                  </div>
                </t-space>
              </t-card>
            </t-space>
          </t-card>
        </div>

        <!-- 加载状态 -->
        <div v-else-if="generatingDetailedReport" class="report-generating">
          <t-loading size="small" text="正在生成详细诊断报告..." />
        </div>

        <!-- 如果没有报告数据，显示原始分析结果 -->
        <div v-else-if="selectedReportData.analysis_result" class="raw-analysis-result">
          <t-card title="原始分析结果" class="full-width-card">
            <div class="raw-content" style="max-height: 500px; overflow-y: auto; padding: 16px; background: #f5f5f5; border-radius: 8px;">
              <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-family: inherit;">{{ selectedReportData.analysis_result }}</pre>
            </div>
          </t-card>
        </div>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="jsx">
import { ref, onMounted, onUnmounted, nextTick, watch, computed} from 'vue';
import { MessagePlugin} from 'tdesign-vue-next';
import { Icon } from 'tdesign-icons-vue-next';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';
import { v4 as uuidv4 } from 'uuid';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();


const aiDrawerVisible = ref(false);
const aiChatList = ref([]);
const aiInputText = ref('');
const aiStreamLoading = ref(false);
const aiChatRef = ref(null);
const aiChatSenderRef = ref(null);

const onlineDiagnosisDrawerVisible = ref(false);
const onlineDiagnosisLoading = ref(false);
const jumpNameOptions = ref([]);
const jumpServerSelected = ref('');
const targetIp = ref('');
const shelfNumber = ref('');
const slotNumber = ref('');

const detailedReportVisible = ref(false);
const selectedReportData = ref(null);
const selectedReportMetrics = ref([]);

//批量kpi 添加响应式数据
const batchAnalysisStatistics = ref({
  totalTarFiles: 0,
  processedTarFiles: 0,
  filesWithKpi: 0,
  totalKpiFiles: 0,
  tarFilesByDate: {}
});
const detailedCpuChart = ref(null);
const detailedMemChart = ref(null);
const detailedDiskChart = ref(null);
const detailedQueueChart = ref(null);
const detailedSsdChart = ref(null);
const detailedSpareChart = ref(null);
const detailedProcMemChart = ref(null);

const detailedDiagnosisReport = ref(null);
const generatingDetailedReport = ref(false);

// 详细图表实例
let detailedCpuChartInstance = null;
let detailedMemChartInstance = null;
let detailedDiskChartInstance = null;
let detailedQueueChartInstance = null;
let detailedSsdChartInstance = null;
let detailedSpareChartInstance = null;
let detailedProcMemChartInstance = null;


// 得分规则相关响应式数据
const scoreRulesVisible = ref(false);

// 总体评分规则表格列
const ruleColumns = [
  {
    title: '评分范围',
    colKey: 'range',
    width: 120,
    align: 'center',
  },
  {
    title: '健康状态',
    colKey: 'status',
    width: 100,
    align: 'center',
    cell: (h, { row }) => {
      let theme = 'default';
      let color = '#666';
      if (row.status === '优秀') {
        theme = 'success';
        color = '#52c41a';
      } else if (row.status === '良好') {
        theme = 'success';
        color = '#52c41a';
      } else if (row.status === '一般') {
        theme = 'warning';
        color = '#faad14';
      } else if (row.status === '警告') {
        theme = 'warning';
        color = '#faad14';
      } else if (row.status === '危险') {
        theme = 'danger';
        color = '#ff4d4f';
      }
      return h('span', { style: { color: color, fontWeight: 'bold' } }, row.status);
    }
  },
  {
    title: '描述',
    colKey: 'description',
    align: 'left',
  }
];

// 指标评分规则表格列
const metricRuleColumns = [
  {
    title: '范围',
    colKey: 'range',
    width: 100,
    align: 'center',
  },
  {
    title: '状态',
    colKey: 'status',
    width: 80,
    align: 'center',
    cell: (h, { row }) => {
      let emoji = '';
      let color = '#666';
      if (row.status === '正常') {
        emoji = '🟢 ';
        color = '#52c41a';
      } else if (row.status === '警告') {
        emoji = '🟡 ';
        color = '#faad14';
      } else if (row.status === '危险') {
        emoji = '🔴 ';
        color = '#ff4d4f';
      }
      return h('span', { style: { color: color, fontWeight: 'bold' } }, emoji + row.status);
    }
  },
  {
    title: '基础分',
    colKey: 'baseScore',
    width: 80,
    align: 'center',
  },
  {
    title: '调整',
    colKey: 'adjustment',
    width: 150,
    align: 'left',
  }
];

// 总体评分规则数据
const overallScoreRules = ref([
  { range: '90-100分', status: '优秀', description: '所有指标均正常，系统运行状态极佳' },
  { range: '80-89分', status: '良好', description: '主要指标正常，少数指标需关注' },
  { range: '70-79分', status: '一般', description: '部分指标异常但无严重问题' },
  { range: '60-69分', status: '警告', description: '多个指标异常需要关注和处理' },
  { range: '0-59分', status: '危险', description: '存在严重问题需要立即处理' },
]);

// CPU使用率评分规则
const cpuScoreRules = ref([
  { range: '0-50%', status: '正常', baseScore: '25', adjustment: '状态Normal:+0' },
  { range: '50-70%', status: '正常', baseScore: '20', adjustment: '状态Warning:-5' },
  { range: '70-85%', status: '警告', baseScore: '15', adjustment: '状态Error:-10' },
  { range: '85-100%', status: '危险', baseScore: '5', adjustment: '峰值>80%额外-10' },
]);

// 内存使用率评分规则
const memScoreRules = ref([
  { range: '0-60%', status: '正常', baseScore: '25', adjustment: '状态Normal:+0' },
  { range: '60-75%', status: '正常', baseScore: '20', adjustment: '状态Warning:-5' },
  { range: '75-85%', status: '警告', baseScore: '15', adjustment: '状态Error:-10' },
  { range: '85-100%', status: '危险', baseScore: '5', adjustment: '内存泄漏额外-15' },
]);

// 磁盘使用率评分规则
const diskScoreRules = ref([
  { range: '0-70%', status: '正常', baseScore: '20', adjustment: '状态Normal:+0' },
  { range: '70-85%', status: '正常', baseScore: '15', adjustment: '状态Warning:-5' },
  { range: '85-95%', status: '警告', baseScore: '10', adjustment: '状态Error:-10' },
  { range: '95-100%', status: '危险', baseScore: '5', adjustment: '接近满盘额外-15' },
]);

// 队列使用率评分规则
const queueScoreRules = ref([
  { range: '0-50%', status: '正常', baseScore: '15', adjustment: '状态Normal:+0' },
  { range: '50-70%', status: '正常', baseScore: '12', adjustment: '状态Warning:-3' },
  { range: '70-85%', status: '警告', baseScore: '8', adjustment: '状态Error:-7' },
  { range: '85-100%', status: '危险', baseScore: '3', adjustment: '拥塞额外-10' },
]);

// SSD剩余寿命评分规则
const ssdLifeScoreRules = ref([
  { range: '70-100%', status: '正常', baseScore: '30', adjustment: '状态Normal:+5' },
  { range: '50-70%', status: '正常', baseScore: '25', adjustment: '状态Warning:-5' },
  { range: '30-50%', status: '警告', baseScore: '15', adjustment: '状态Error:-15' },
  { range: '0-30%', status: '危险', baseScore: '5', adjustment: '建议立即更换' },
]);

// SSD有效备用块评分规则
const ssdSpareScoreRules = ref([
  { range: '>1000', status: '正常', baseScore: '20', adjustment: '状态Normal:+5' },
  { range: '500-1000', status: '正常', baseScore: '15', adjustment: '状态Warning:-5' },
  { range: '100-500', status: '警告', baseScore: '10', adjustment: '状态Error:-10' },
  { range: '<100', status: '危险', baseScore: '5', adjustment: '备用块即将耗尽' },
]);

// 进程内存使用率评分规则
const processScoreRules = ref([
  { range: '0-60%', status: '正常', baseScore: '15', adjustment: '所有进程正常:+0' },
  { range: '60-75%', status: '正常', baseScore: '12', adjustment: '单个进程偏高:-3' },
  { range: '75-85%', status: '警告', baseScore: '8', adjustment: '多个进程偏高:-7' },
  { range: '85-100%', status: '危险', baseScore: '3', adjustment: '存在异常进程:-15' },
]);

// 显示得分规则弹窗
const showScoreRules = () => {
  scoreRulesVisible.value = true;
};

// 初始化详细图表
const initDetailedCharts = () => {
  if (selectedReportMetrics.value.length === 0) {
    console.log('详细图表：无数据可用');
    return;
  }

  console.log('初始化详细图表，数据量:', selectedReportMetrics.value.length);

  // 销毁旧图表实例
  [detailedCpuChartInstance, detailedMemChartInstance, detailedDiskChartInstance,
   detailedQueueChartInstance, detailedSsdChartInstance, detailedSpareChartInstance,
   detailedProcMemChartInstance].forEach(instance => {
    if (instance) {
      instance.dispose();
      instance = null;
    }
  });

  // 等待DOM渲染完成
  nextTick(() => {
    try {
      // 判断是否需要添加缩放功能（超过15个数据点）
      const useDataZoom = selectedReportMetrics.value.length > 15;

      // 初始化详细CPU图表
      if (detailedCpuChart.value) {
        detailedCpuChartInstance = echarts.init(detailedCpuChart.value);
        const cpuOptions = createChartOptions(
          selectedReportMetrics.value,
          'CPU使用率',
          'cpuUsage',
          '#5470c6',
          useDataZoom  // 添加缩放参数
        );
        detailedCpuChartInstance.setOption(cpuOptions);
      }

      // 初始化详细内存图表
      if (detailedMemChart.value) {
        detailedMemChartInstance = echarts.init(detailedMemChart.value);
        const memOptions = createChartOptions(
          selectedReportMetrics.value,
          '系统内存使用率',
          'memUsage',
          '#91cc75',
          useDataZoom
        );
        detailedMemChartInstance.setOption(memOptions);
      }

      // 初始化详细磁盘图表
      if (detailedDiskChart.value) {
        detailedDiskChartInstance = echarts.init(detailedDiskChart.value);
        const diskOptions = createChartOptions(
          selectedReportMetrics.value,
          'SSD磁盘使用率',
          'diskSpace',
          '#fac858',
          useDataZoom
        );
        detailedDiskChartInstance.setOption(diskOptions);
      }

      // 初始化详细队列图表
      if (detailedQueueChart.value) {
        detailedQueueChartInstance = echarts.init(detailedQueueChart.value);
        const queueOptions = createChartOptions(
          selectedReportMetrics.value,
          '队列使用率',
          'queueUsage',
          '#ee6666',
          useDataZoom
        );
        detailedQueueChartInstance.setOption(queueOptions);
      }

      // 初始化详细SSD寿命图表
      if (detailedSsdChart.value) {
        detailedSsdChartInstance = echarts.init(detailedSsdChart.value);
        const ssdOptions = createChartOptions(
          selectedReportMetrics.value,
          'SSD剩余寿命',
          'ssdRemainLife',
          '#73c0de',
          useDataZoom
        );
        detailedSsdChartInstance.setOption(ssdOptions);
      }

      // 初始化详细备用块图表
      if (detailedSpareChart.value) {
        detailedSpareChartInstance = echarts.init(detailedSpareChart.value);
        const spareOptions = createChartOptions(
          selectedReportMetrics.value,
          'SSD有效备用块',
          'validSpareBlocks',
          '#3ba272',
          useDataZoom
        );
        detailedSpareChartInstance.setOption(spareOptions);
      }

      // 初始化详细进程内存图表
      if (detailedProcMemChart.value) {
        detailedProcMemChartInstance = echarts.init(detailedProcMemChart.value);
        const procMemOptions = createProcessChartOptions(
          selectedReportMetrics.value,
          useDataZoom
        );
        detailedProcMemChartInstance.setOption(procMemOptions);
      }

      console.log('详细图表初始化完成');
    } catch (error) {
      console.error('初始化详细图表失败:', error);
    }
  });
};

// 创建通用图表选项
const createChartOptions = (data, title, dataKey, color, useDataZoom = false) => {
  const timeData = data.map(item => item.timestamp);
  const valueData = data.map(item => item[dataKey] || 0);

  // 基础配置
  const options = {
    title: {
      text: title + '趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach(item => {
          result += `${item.marker} ${item.seriesName}: ${item.value}${dataKey.includes('Usage') || dataKey === 'diskSpace' || dataKey === 'queueUsage' || dataKey === 'ssdRemainLife' ? '%' : ''}<br/>`;
        });
        return result;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: useDataZoom ? '15%' : '3%',  // 有缩放时留出底部空间
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        color: '#666',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#666',
        formatter: dataKey.includes('Usage') || dataKey === 'diskSpace' || dataKey === 'queueUsage' || dataKey === 'ssdRemainLife' ? '{value}%' : '{value}'
      },
      min: 0,
      max: dataKey === 'validSpareBlocks' ? Math.max(...valueData) * 1.1 : 100
    },
    series: [{
      name: title,
      type: 'line',
      data: valueData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: color
      },
      itemStyle: {
        color: color
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color.replace(')', ', 0.5)').replace('rgb', 'rgba') },
          { offset: 1, color: color.replace(')', ', 0.1)').replace('rgb', 'rgba') }
        ])
      }
    }]
  };

  // 添加数据缩放配置
  if (useDataZoom) {
    options.dataZoom = [
      {
        type: 'inside',  // 内置型数据区域缩放组件
        xAxisIndex: 0,   // 控制第一个x轴
        start: 0,        // 默认起始位置
        end: 100,        // 默认结束位置
        zoomLock: false, // 是否锁定选择区域大小
        zoomOnMouseWheel: true, // 允许滚轮缩放
        moveOnMouseWheel: true, // 允许滚轮移动
        preventDefaultMouseMove: true
      },
      {
        type: 'slider',  // 滑动条型数据区域缩放组件
        xAxisIndex: 0,
        show: true,
        start: 0,
        end: 100,
        height: 20,
        bottom: 0,
        fillerColor: 'rgba(84, 112, 198, 0.2)',
        borderColor: '#5470c6',
        handleStyle: {
          color: '#5470c6',
          borderColor: '#5470c6'
        },
        moveHandleStyle: {
          color: '#5470c6'
        }
      }
    ];
  }

  return options;
};

// 创建进程内存图表选项
const createProcessChartOptions = (data, useDataZoom = false) => {
  const timeData = data.map(item => item.timestamp);
  const processNames = ['WASON', 'QXOAGENT', 'MIM', 'UEM', 'TOPUEM', 'USM', 'UPP2OTNAGENT'];
  const processColors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666',
    '#73c0de', '#3ba272', '#fc8452'
  ];

  const series = processNames.map((name, index) => ({
    name: name,
    type: 'line',
    data: data.map(item => item.procMemUsage?.[name] || 0),
    smooth: true,
    symbol: 'circle',
    symbolSize: 4,
    lineStyle: {
      width: 2,
      color: processColors[index]
    },
    itemStyle: {
      color: processColors[index]
    }
  }));

  const options = {
    title: {
      text: '进程内存使用率监控',
      left: 'center',
      top: 20,  // 将标题向上移动，给图例留出空间
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: processNames,
      top: 50,  // 将图例向下移动，避免与标题重叠
      textStyle: {
        color: '#666'
      },
      type: 'scroll',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      borderColor: '#ccc',
      borderWidth: 1,
      padding: [5, 10]
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: useDataZoom ? '15%' : '3%',
      top: 100,  // 增加顶部边距，为标题和图例留出空间
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        color: '#666',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '内存使用率(%)',
      axisLabel: {
        color: '#666',
        formatter: '{value}%'
      },
      min: 0,
      max: 100
    },
    series: series
  };

  // 添加数据缩放配置
  if (useDataZoom) {
    options.dataZoom = [
      {
        type: 'inside',
        xAxisIndex: 0,
        start: 0,
        end: 100,
        zoomLock: false,
        zoomOnMouseWheel: true,
        moveOnMouseWheel: true,
        preventDefaultMouseMove: true
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        show: true,
        start: 0,
        end: 100,
        height: 20,
        bottom: 0,
        fillerColor: 'rgba(84, 112, 198, 0.2)',
        borderColor: '#5470c6',
        handleStyle: {
          color: '#5470c6',
          borderColor: '#5470c6'
        },
        moveHandleStyle: {
          color: '#5470c6'
        }
      }
    ];
  }

  return options;
};

// 计算属性
const completedCount = computed(() => {
  return batchAnalysisResults.value.filter(r => r.status === 'completed').length;
});
const unhealthyCount = computed(() => {
  return batchAnalysisResults.value.filter(r =>
    r.status === 'completed' && r.health_score < 60
  ).length;
});
const failedCount = computed(() => {
  return batchAnalysisResults.value.filter(r => r.status === 'failed').length;
});

const averageScore = computed(() => {
  const completedResults = batchAnalysisResults.value.filter(r => r.status === 'completed' && r.health_score > 0);
  if (completedResults.length === 0) return 0.0;

  const sum = completedResults.reduce((sum, r) => sum + r.health_score, 0);
  return (sum / completedResults.length).toFixed(1);
});

// 批量分析相关状态
const batchAnalysisDialogVisible = ref(false);
const batchAnalysisConfig = ref({
  jumpServerName: '燕郊_1B4-1实验室',
});
const batchAnalysisStatus = ref({
  isRunning: false,
  progress: 0,
  current: 0,
  total: 0,
  message: '请配置参数并开始分析'
});
const batchAnalysisResults = ref([]);
const batchAnalysisTimer = ref(null);

// 打开批量分析对话框
const openBatchAnalysisDialog = () => {
  batchAnalysisDialogVisible.value = true;
  batchAnalysisStatus.value.message = '请配置参数并开始分析';
};

// 清空批量分析结果
const clearBatchResults = () => {
  // 清空结果列表
  batchAnalysisResults.value = [];

  // 重置统计信息
  batchAnalysisStatistics.value = {
    totalTarFiles: 0,
    processedTarFiles: 0,
    filesWithKpi: 0,
    totalKpiFiles: 0
  };

  // 重置分析状态到初始状态
  batchAnalysisStatus.value = {
    isRunning: false,
    progress: 0,
    current: 0,
    total: 0,
    message: '请配置参数并开始分析'
  };

  // 停止状态轮询
  if (batchAnalysisTimer.value) {
    clearInterval(batchAnalysisTimer.value);
    batchAnalysisTimer.value = null;
  }

  MessagePlugin.success('已清空所有分析结果和状态');
};

//并行分析
const startBatchKpiAnalysis = async () => {
  try {
    // 验证配置 - 只需要验证跳板机
    if (!batchAnalysisConfig.value.jumpServerName) {
      MessagePlugin.warning('请选择跳板机');
      return;
    }

    batchAnalysisStatus.value.isRunning = true;
    batchAnalysisStatus.value.message = '正在获取KPI日志文件...';
    batchAnalysisStatus.value.progress = 0;
    batchAnalysisStatus.value.current = 0;
    batchAnalysisResults.value = [];

    // 重置统计信息
    batchAnalysisStatistics.value = {
      totalTarFiles: 0,
      processedTarFiles: 0,
      filesWithKpi: 0,
      totalKpiFiles: 0
    };

    MessagePlugin.info('开始获取KPI日志文件...');

    // 根据跳板机名称确定 basePath
    let basePath = '';
    if (batchAnalysisConfig.value.jumpServerName === '武汉_302A实验室') {
      basePath = 'D:\\123\\111\\backbrd\\test_20';
    } else if (batchAnalysisConfig.value.jumpServerName === '燕郊_1B4-1实验室') {
      basePath = 'F:\\';
    } else {
      // 默认路径
      basePath = 'F:\\';
    }

    console.log(`使用跳板机: ${batchAnalysisConfig.value.jumpServerName}, 路径: ${basePath}`);

    // 1. 获取KPI日志文件列表
    const getLogsResponse = await fetch(`${SERVER_API_URL}/getBatchKpiLogs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jump_server_name: batchAnalysisConfig.value.jumpServerName,
        base_path: basePath,
      })
    });

    const logsResult = await getLogsResponse.json();
    console.log('获取KPI日志结果:', logsResult);

    if (logsResult.status !== 'success') {
      MessagePlugin.error(`获取日志失败: ${logsResult.message}`);
      batchAnalysisStatus.value.isRunning = false;
      batchAnalysisStatus.value.message = `获取失败: ${logsResult.message}`;
      return;
    }

    const kpiFiles = logsResult.data.kpi_files || [];

    // 更新统计信息
    if (logsResult.data && logsResult.data.statistics) {
      console.log('获取到统计信息:', logsResult.data.statistics);
      batchAnalysisStatistics.value = {
        totalTarFiles: logsResult.data.statistics.total_tar_files || 0,
        processedTarFiles: logsResult.data.statistics.processed_tar_files || 0,
        filesWithKpi: logsResult.data.statistics.files_with_kpi || 0,
        totalKpiFiles: logsResult.data.statistics.total_kpi_files || kpiFiles.length
      };
    } else {
      // 如果没有返回statistics，使用默认值
      batchAnalysisStatistics.value.totalKpiFiles = kpiFiles.length;
      batchAnalysisStatistics.value.totalTarFiles = Math.ceil(kpiFiles.length / 2); // 估计值
    }

    if (kpiFiles.length === 0) {
      MessagePlugin.warning('未找到KPI日志文件');
      batchAnalysisStatus.value.isRunning = false;
      batchAnalysisStatus.value.message = '未找到KPI日志文件';
      return;
    }

    // 显示统计信息
    MessagePlugin.success(
      `📊 统计信息：找到 ${batchAnalysisStatistics.value.totalTarFiles} 个tar文件，` +
      `其中 ${batchAnalysisStatistics.value.filesWithKpi} 个包含KPI日志`
    );

    batchAnalysisStatus.value.message = `找到 ${batchAnalysisStatistics.value.totalKpiFiles} 个KPI日志，开始分析...`;
    batchAnalysisStatus.value.total = kpiFiles.length;

    // 使用所有文件，不限制数量
    const filesToAnalyze = kpiFiles;

    // 2. 开始批量分析
    const analyzeResponse = await fetch(`${SERVER_API_URL}/analyzeBatchKpiLogs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        kpi_files: filesToAnalyze
      })
    });

    const analyzeResult = await analyzeResponse.json();

    if (analyzeResult.status !== 'success') {
      MessagePlugin.error(`启动分析失败: ${analyzeResult.message}`);
      batchAnalysisStatus.value.isRunning = false;
      batchAnalysisStatus.value.message = `启动失败: ${analyzeResult.message}`;
      return;
    }

    // 3. 启动状态轮询
    startBatchStatusPolling();

  } catch (error) {
    console.error('批量分析失败:', error);
    MessagePlugin.error(`批量分析失败: ${error.message}`);
    batchAnalysisStatus.value.isRunning = false;
    batchAnalysisStatus.value.message = `分析失败: ${error.message}`;
  }
};

// 启动状态轮询
const startBatchStatusPolling = () => {
  if (batchAnalysisTimer.value) {
    clearInterval(batchAnalysisTimer.value);
  }

  // 添加防抖，避免过于频繁的更新
  let isChecking = false;

  batchAnalysisTimer.value = setInterval(async () => {
    if (isChecking) {
      return;
    }

    isChecking = true;
    try {
      await checkBatchAnalysisStatus();
    } catch (error) {
      console.error('轮询检查失败:', error);
    } finally {
      isChecking = false;
    }
  }, 3000); // 改为3秒一次，避免太频繁
};


// 批量分析的表格列定义
const batchAnalysisColumns = [
  {
    title: '排名',
    colKey: 'index',
    width: 80,
    align: 'center',
    cell: (h, { rowIndex }) => {
      return h('div', {
        style: {
          width: '32px',
          height: '32px',
          lineHeight: '32px',
          borderRadius: '50%',
          backgroundColor: '#f0f2f5',
          margin: '0 auto',
          fontWeight: 'bold',
          color: '#333'
        }
      }, rowIndex + 1);
    }
  },
  {
    title: '网元名称',
    colKey: 'tar_filename',
    ellipsis: true,
    width: 180,
    cell: (h, { row }) => {
      let displayName = row.tar_filename || '';
      if (displayName.toLowerCase().endsWith('.tar')) {
        displayName = displayName.slice(0, -4);
      }
      return h('span', {
        style: {
          color: '#333'
        }
      }, displayName);
    }
  },
  {
    title: 'KPI日志',
    colKey: 'log_filename',
    ellipsis: true,
    width: 120,
    cell: (h, { row }) => {
      return h('span', {
        style: {
          color: '#666'
        }
      }, row.log_filename || '');
    }
  },
  {
    title: '问题项/总项',
    colKey: 'problem_items',
    width: 120,
    align: 'center',
    cell: (h, { row }) => {
      const problemItems = row.problem_items || 0;
      const totalItems = row.total_items || 7;

      // 根据问题数量设置颜色
      let color = '#52c41a'; // 绿色 - 没有问题
      if (problemItems >= 5) {
        color = '#ff4d4f'; // 红色 - 严重
      } else if (problemItems >= 3) {
        color = '#faad14'; // 黄色 - 警告
      } else if (problemItems >= 1) {
        color = '#fa8c16'; // 橙色 - 轻微
      }

      // 计算问题比例
      const ratio = (problemItems / totalItems * 100).toFixed(0);

      return h('div', {
        style: {
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }
      }, [
        h('div', {
          style: {
            color: color,
            fontWeight: 'bold',
            fontSize: '16px'
          }
        }, `${problemItems}/${totalItems}`),
        h('div', {
          style: {
            width: '60px',
            height: '4px',
            backgroundColor: '#f0f0f0',
            borderRadius: '2px',
            marginTop: '4px',
            overflow: 'hidden'
          }
        }, [
          h('div', {
            style: {
              width: `${ratio}%`,
              height: '100%',
              backgroundColor: color,
              borderRadius: '2px'
            }
          })
        ])
      ]);
    }
  },
  {
    title: '健康评分',
    colKey: 'health_score',
    width: 120,
    align: 'center',
    cell: (h, { row }) => {
      const score = row.health_score || 0;
      const validScore = isNaN(score) ? 0 : Math.max(0, Math.min(100, score));

      // 根据分数设置颜色
      let color = '#ff6b6b'; // 红色 - 默认
      if (validScore >= 80) {
        color = '#52c41a'; // 绿色 - 健康
      } else if (validScore >= 60) {
        color = '#faad14'; // 黄色 - 警告
      }
      // 小于60分显示红色

      // 添加分数旁边的健康状态标签
      let healthStatus = '';
      if (validScore >= 80) {
        healthStatus = '健康';
      } else if (validScore >= 60) {
        healthStatus = '警告';
      } else {
        healthStatus = '不健康';
      }

      return h('div', {
        style: {
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }
      }, [
        h('div', {
          style: {
            color: color,
            fontWeight: 'bold',
            fontSize: '14px'
          }
        }, `${validScore}分`),
        h('div', {
          style: {
            color: color,
            fontSize: '12px',
            marginTop: '2px'
          }
        }, healthStatus)
      ]);
    }
  },
  {
    title: '状态',
    colKey: 'status',
    width: 100,
    align: 'center',
    cell: (h, { row }) => {
      const status = row.status || 'failed';
      let color = '#ff6b6b'; // 红色 - 失败
      let label = '失败';

      if (status === 'completed') {
        color = '#52c41a'; // 绿色
        label = '完成';
      } else if (status === 'timeout') {
        color = '#faad14'; // 黄色
        label = '超时';
      } else if (status === 'processing') {
        color = '#1890ff'; // 蓝色
        label = '处理中';
      }

      return h('div', {
        style: {
          color: color,
          fontWeight: '500',
          fontSize: '12px'
        }
      }, label);
    }
  },
  {
    title: '操作',
    colKey: 'operations',
    width: 100,
    align: 'center',
    cell: (h, { row }) => {
      const isDisabled = row.status !== 'completed';

      return h('button', {
        style: {
          padding: '4px 8px',
          fontSize: '12px',
          color: isDisabled ? '#999' : '#1890ff',
          backgroundColor: 'transparent',
          border: '1px solid',
          borderColor: isDisabled ? '#d9d9d9' : '#1890ff',
          borderRadius: '4px',
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          opacity: isDisabled ? 0.6 : 1
        },
        onClick: () => {
          if (!isDisabled) {
            viewSingleAnalysis(row);
          }
        },
        disabled: isDisabled
      }, '查看详情');
    }
  }
];

// 计算有问题的网元数量（至少有一项问题）
const hasProblemCount = computed(() => {
  return batchAnalysisResults.value.filter(r =>
    r.status === 'completed' && r.problem_items > 0
  ).length;
});

// 计算总问题项数
const totalProblemItems = computed(() => {
  return batchAnalysisResults.value
    .filter(r => r.status === 'completed')
    .reduce((sum, r) => sum + (r.problem_items || 0), 0);
});

// 检查批量分析状态
const checkBatchAnalysisStatus = async () => {
  try {
    const response = await fetch(`${SERVER_API_URL}/getBatchAnalysisStatus`);
    const result = await response.json();

    if (result.status === 'success') {
      const statusData = result.data;

      // 只在状态变化时更新
      const newStatus = {
        isRunning: statusData.is_running || false,
        progress: statusData.progress || 0,
        current: statusData.current || 0,
        total: statusData.total || 0,
        message: statusData.message || ''
      };

      // 使用深比较，避免不必要的更新
      if (JSON.stringify(batchAnalysisStatus.value) !== JSON.stringify(newStatus)) {
        batchAnalysisStatus.value = newStatus;
      }

      // 如果有日期分布信息，也更新
      if (statusData.date_distribution) {
        const today = new Date().toISOString().split('T')[0];
        batchAnalysisStatus.value = {
          ...batchAnalysisStatus.value,
          dateInfo: statusData.date_distribution,
          today: today
        };
      }

      // 如果有结果，更新结果列表
      if (statusData.results && Array.isArray(statusData.results)) {
        // 确保结果有必要的字段
        const processedResults = statusData.results.map(result => {
          // 确保 health_score 是有效数字
          let healthScore = result.health_score || result.score || result.healthScore || 0;

          if (typeof healthScore === 'string') {
            healthScore = parseFloat(healthScore);
          }

          if (isNaN(healthScore)) {
            healthScore = 0;
          }

          // 确保在 0-100 范围内
          healthScore = Math.max(0, Math.min(100, healthScore));

          // 确保有状态字段
          let status = result.status || 'failed';
          if (status === 'completed' && healthScore > 0) {
            status = 'completed';
          } else if (status === 'completed' && healthScore === 0) {
            status = 'failed';
          } else if (!status) {
            status = healthScore > 0 ? 'completed' : 'failed';
          }

          // 确保问题项字段存在
          let problemItems = result.problem_items;

          if (problemItems === undefined || problemItems === null) {
            problemItems = 0;
          } else if (typeof problemItems === 'string') {
            problemItems = parseInt(problemItems, 10);
            if (isNaN(problemItems)) {
              problemItems = 0;
            }
          } else if (typeof problemItems === 'number') {
            // 已经是数字，保持原样
          } else {
            problemItems = 0;
          }

          let totalItems = result.total_items;
          if (totalItems === undefined || totalItems === null) {
            totalItems = 7;
          } else if (typeof totalItems === 'string') {
            totalItems = parseInt(totalItems, 10);
            if (isNaN(totalItems) || totalItems < 1) {
              totalItems = 7;
            }
          } else if (typeof totalItems === 'number') {
            // 已经是数字，保持原样
          } else {
            totalItems = 7;
          }


          return {
            tar_filename: result.tar_filename || '',
            log_filename: result.log_filename || '',
            kpi_path: result.kpi_path || '',
            health_score: healthScore,
            problem_items: problemItems,
            total_items: totalItems,
            analysis_result: result.analysis_result || result.analysis_result || '',
            status: status,
            timestamp: result.timestamp || new Date().toISOString()
          };
        });

        // 按评分从低到高排序
        const sortedResults = [...processedResults].sort((a, b) => a.health_score - b.health_score);

        // 只在结果不同时更新
        if (JSON.stringify(batchAnalysisResults.value) !== JSON.stringify(sortedResults)) {
          batchAnalysisResults.value = sortedResults;
        }

        // 如果分析完成，停止轮询
        if (!statusData.is_running && sortedResults.length > 0) {
          if (batchAnalysisTimer.value) {
            clearInterval(batchAnalysisTimer.value);
            batchAnalysisTimer.value = null;
          }

          const successCount = sortedResults.filter(r => r.status === 'completed').length;
          const totalCount = sortedResults.length;

          if (successCount > 0) {
            MessagePlugin.success(`批量分析完成，成功 ${successCount}/${totalCount} 个文件`);
          }
        }
      }

      // 如果没有结果但分析已停止，也停止轮询
      if (!statusData.is_running && (!statusData.results || statusData.results.length === 0)) {
        if (batchAnalysisTimer.value) {
          clearInterval(batchAnalysisTimer.value);
          batchAnalysisTimer.value = null;
        }
      }
    }
  } catch (error) {
    console.error('检查分析状态失败:', error);
    // 发生错误时也要尝试停止轮询
    if (batchAnalysisTimer.value) {
      clearInterval(batchAnalysisTimer.value);
      batchAnalysisTimer.value = null;
    }
  }
};


const viewSingleAnalysis = async (kpiInfo) => {
  console.log('查看详细分析:', kpiInfo);

  if (kpiInfo.status !== 'completed') {
    MessagePlugin.warning('该文件分析失败，无法查看详情');
    return;
  }

  MessagePlugin.info(`正在加载 ${kpiInfo.log_filename} 的详细分析...`);

  try {
    // 重置详细报告数据
    selectedReportData.value = null;
    selectedReportMetrics.value = [];
    detailedDiagnosisReport.value = null;  // 重置详细报告
    generatingDetailedReport.value = true;  // 设置为生成中

    // 1. 获取真实的KPI数据
    const detailResponse = await fetch(`${SERVER_API_URL}/getKpiDetailData`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        log_filename: kpiInfo.log_filename,
        kpi_path: kpiInfo.kpi_path,
        tar_filename: kpiInfo.tar_filename,
        jump_server_name: batchAnalysisConfig.value.jumpServerName
      })
    });

    const detailResult = await detailResponse.json();

    if (detailResult.status === 'success') {
      // 2. 设置选中报告数据
      selectedReportData.value = {
        ...kpiInfo,
        detailedData: detailResult.data,
        analysisResult: kpiInfo.analysis_result
      };

      // 3. 获取真实的指标数据
      if (detailResult.data && detailResult.data.metrics) {
        selectedReportMetrics.value = detailResult.data.metrics;

        // 初始化详细图表
        await nextTick();
        initDetailedCharts();

        // 4. 如果有完整的分析结果，直接使用
        if (kpiInfo.analysis_result && kpiInfo.analysis_result.includes('## 一、总体健康评估')) {
          const reportData = parseHealthDiagnosisReport(kpiInfo.analysis_result);
          if (reportData) {
            selectedReportData.value.report = reportData;
            detailedDiagnosisReport.value = reportData;  // 设置详细报告
            MessagePlugin.success('详细分析报告已加载');
            detailedReportVisible.value = true;
            generatingDetailedReport.value = false;
            return;
          }
        }

        // 5. 否则生成新的诊断报告
        MessagePlugin.info('正在生成详细诊断报告...');
        await generateRealKpiDiagnosisReport(kpiInfo, detailResult.data.metrics);

      } else {
        MessagePlugin.warning('未获取到指标数据');
        generatingDetailedReport.value = false;

        // 使用已有的分析结果
        if (kpiInfo.analysis_result) {
          selectedReportData.value.report = {
            overallAssessment: {
              healthStatus: "信息",
              score: kpiInfo.health_score,
              summary: "KPI日志分析报告"
            },
            rawContent: kpiInfo.analysis_result
          };
          detailedDiagnosisReport.value = selectedReportData.value.report;
        }
      }

      // 6. 显示详细报告界面
      detailedReportVisible.value = true;

    } else {
      MessagePlugin.error('加载详细数据失败: ' + detailResult.message);
      generatingDetailedReport.value = false;
    }

  } catch (error) {
    console.error('显示详细分析失败:', error);
    MessagePlugin.error('加载详细分析失败: ' + error.message);
    generatingDetailedReport.value = false;
  }
};


// 生成真实的KPI诊断报告
const generateRealKpiDiagnosisReport = async (kpiInfo, metrics) => {
  generatingDetailedReport.value = true;

  try {
    const healthData = {
      metrics: metrics,
      summary: generateHealthSummary(metrics)
    };

    const response = await fetch(`${SERVER_API_URL}/api_chat/Agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: 'health_monitor_system',
        session_id: `kpi_detail_${Date.now()}`,
        request_id: `kpi_detail_${uuidv4()}`,
        model: 'nebula',
        agent: 'HealthDiagnosisAgent',
        icenter: false,
        rdc: false,
        think: true,
        content: JSON.stringify(healthData),
        context: '单网元KPI日志详细健康诊断',
        component: 'HealthMonitor',
        knowledge: 'HealthDiagnosisKnowledge',
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.trim() === '') continue;

        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6);
          if (dataStr === '[DONE]') break;

          try {
            const data = JSON.parse(dataStr);
            if (data.text) {
              fullResponse += data.text;
            }
          } catch (e) {
            console.error('解析JSON出错:', e);
          }
        }
      }
    }

    // 解析诊断报告
    const reportData = parseHealthDiagnosisReport(fullResponse);
    if (reportData) {
      selectedReportData.value.report = reportData;
      detailedDiagnosisReport.value = reportData;
      MessagePlugin.success('详细诊断报告生成完成');
    } else {
      // 如果解析失败，设置为原始内容
      selectedReportData.value.report = {
        overallAssessment: {
          healthStatus: "信息",
          score: kpiInfo.health_score,
          summary: "详细KPI日志分析报告"
        },
        rawContent: fullResponse
      };
    }

  } catch (error) {
    console.error('生成详细KPI报告错误:', error);
    MessagePlugin.error(`生成详细报告失败: ${error.message}`);

    // 使用已有的分析结果
    if (kpiInfo.analysis_result) {
      selectedReportData.value.report = {
        overallAssessment: {
          healthStatus: "信息",
          score: kpiInfo.health_score,
          summary: "KPI日志分析报告"
        },
        rawContent: kpiInfo.analysis_result
      };
    }
  } finally {
    generatingDetailedReport.value = false;
  }
};


// 停止批量分析
const stopBatchAnalysis = () => {
  if (batchAnalysisTimer.value) {
    clearInterval(batchAnalysisTimer.value);
    batchAnalysisTimer.value = null;
  }

  batchAnalysisStatus.value.isRunning = false;
  batchAnalysisStatus.value.message = '分析已停止';

  MessagePlugin.info('批量分析已停止');
};

// 组件卸载时清理
onUnmounted(() => {
  if (batchAnalysisTimer.value) {
    clearInterval(batchAnalysisTimer.value);
  }
});

// 计算NE组件数据
const neComponentsData = computed(() => {
  return combinedDiagnosisData.value.filter(item =>
    item.component && item.component.toUpperCase() === 'NE'
  );
});

// 计算其它组件数据
const otherComponentsData = computed(() => {
  return combinedDiagnosisData.value.filter(item =>
    item.component && item.component.toUpperCase() !== 'NE'
  );
});

// 添加跳板机配置对象
const onlineDiagnosisConfig = ref({
  jumpName: '',
  targetIp: '',
  shelf: '',
  slot: ''
});

// 添加诊断状态
const onlineDiagnosisStatus = ref({
  type: '',
  message: ''
});

// 添加诊断状态信息
const diagnosisStatusInfo = ref({
  ip: '',
  shelf: '',
  slot: '',
  connected: true,
  message: '连接正常，诊断数据已就绪'
});

const aiSelectModel = [
  {
    label: '星云大模型',
    value: 'nebula',
  },
  {
    label: '通义千问-中兴',
    value: 'qwen3-zte',
  },
  {
    label: '通义千问-阿里',
    value: 'qwen',
  },
  {
    label: 'Qwen3-coder',
    value: 'qwen3-coder',
  },
  {
    label: 'Deepseek-V3',
    value: 'deepseek-V3',
  },
  {
    label: 'Kimi-K2',
    value: 'kimi-K2',
  },
];

const aiSelectModelValue = ref({
  label: '星云大模型',
  value: 'nebula',
});

// 在线诊断状态网元IP消息
const getDiagnosisStatusMessage = () => {
  const { ip, shelf, slot, connected, message } = diagnosisStatusInfo.value;

  if (!ip) {
    return '请先执行在线诊断获取设备状态';
  }

  let statusMessage = `网元IP:${ip} `;

  if (shelf && slot) {
    statusMessage += `${shelf}子架 ${slot}槽位 `;
  }

  if (connected) {
    statusMessage += '连接正常，诊断数据已就绪';
  } else {
    statusMessage += '连接异常，请检查设备状态';
  }

  return statusMessage;
};

// 获取跳板机列表
const fetchJumpServers = async () => {
  try {
    const response = await fetch(`${SERVER_API_URL}/get-jump-servers`, {
      method: 'POST',  // 改为 POST 方法
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})  // 发送空请求体或必要的参数
    });

    console.log('响应状态:', response.status, response.statusText);

    if (response.ok) {
      const result = await response.json();
      if (result.status === 'success') {
        jumpNameOptions.value = result.data;
      } else {
        MessagePlugin.error('获取跳板机列表失败: ' + (result.message || '未知错误'));
      }
    } else {
      console.error('HTTP错误:', response.status);
      MessagePlugin.error(`获取跳板机列表失败: HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('获取跳板机列表失败:', error);
    MessagePlugin.error(`获取跳板机列表失败: ${error.message}`);
  }
};

const isFormValid = computed(() => {
  return (
    onlineDiagnosisConfig.value.jumpName &&
    onlineDiagnosisConfig.value.targetIp &&
    onlineDiagnosisConfig.value.shelf &&
    onlineDiagnosisConfig.value.slot
  );
});

// 开始在线诊断
const startOnlineDiagnosis = () => {
  onlineDiagnosisDrawerVisible.value = true;
  // 加载跳板机列表
  fetchJumpServers();
  // 重置状态
  onlineDiagnosisStatus.value = { type: '', message: '' };
  onlineDiagnosisConfig.value = {
    jumpName: '',
    targetIp: '',
    shelf: '',
    slot: ''
  };
};

// 执行在线诊断
const executeOnlineDiagnosis = async () => {
  if (!isFormValid.value) {
    MessagePlugin.warning('请填写完整的诊断参数');
    return;
  }

  onlineDiagnosisLoading.value = true;
  onlineDiagnosisStatus.value = {
    type: 'info',
    message: '正在连接设备执行诊断...'
  };

  try {
    const response = await fetch(`${SERVER_API_URL}/executeOnlineDiagnosis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jump_name: onlineDiagnosisConfig.value.jumpName,
        target_ip: onlineDiagnosisConfig.value.targetIp,
        shelf_number: parseInt(onlineDiagnosisConfig.value.shelf),
        slot_number: parseInt(onlineDiagnosisConfig.value.slot),
        session_id: `online_diagnosis_${Date.now()}`
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === 'success') {
      onlineDiagnosisStatus.value = {
        type: 'success',
        message: '在线诊断执行成功'
      };

      // 更新诊断状态信息
      diagnosisStatusInfo.value = {
        ip: onlineDiagnosisConfig.value.targetIp,
        shelf: onlineDiagnosisConfig.value.shelf,
        slot: onlineDiagnosisConfig.value.slot,
        connected: true,
        message: `连接正常，${onlineDiagnosisConfig.value.shelf}子架 ${onlineDiagnosisConfig.value.slot}槽位诊断数据已就绪`
      };

      // 更新combinedDiagnosisData数据
      if (result.data && result.data.length > 0) {
        combinedDiagnosisData.value = result.data;

       // 自动生成在线诊断报告
      setTimeout(() => {
      generateOnlineDiagnosisReport();
    }, 1000);
      }else {
        combinedDiagnosisData.value = [];
      }
      // 2秒后关闭弹窗
      setTimeout(() => {
        onlineDiagnosisDrawerVisible.value = false;
      }, 2000);

    } else {
      throw new Error(result.message || '诊断执行失败');
    }

    //调用示例数据接口加载离线的图表
    await loadSampleDataForOnlineDiagnosis();

  } catch (error) {
    console.error('在线诊断错误:', error);
    onlineDiagnosisStatus.value = {
      type: 'error',
      message: `诊断失败: ${error.message}`
    };
     // 失败也更新状态信息（显示失败状态）
    diagnosisStatusInfo.value = {
      ip: onlineDiagnosisConfig.value.targetIp,
      shelf: onlineDiagnosisConfig.value.shelf,
      slot: onlineDiagnosisConfig.value.slot,
      connected: false,
      message: `连接失败，请检查网络连接和设备状态`
    };
    combinedDiagnosisData.value = [];

    //调用示例数据接口加载离线的图表
    await loadSampleDataForOnlineDiagnosis();

    MessagePlugin.error(`在线诊断失败: ${error.message}`);
  } finally {
    onlineDiagnosisLoading.value = false;
  }
};

// 在线诊断报告相关数据
const onlineDiagnosisReport = ref(null);
const generatingOnlineReport = ref(false);

// 在线诊断报告生成方法
const generateOnlineDiagnosisReport = async () => {
  if (combinedDiagnosisData.value.length === 0) {
    MessagePlugin.warning('请先执行在线诊断获取数据');
    return;
  }

  generatingOnlineReport.value = true;
  onlineDiagnosisReport.value = null;

  try {
    const onlineHealthData = {
      metrics: combinedDiagnosisData.value,
      summary: generateOnlineHealthSummary(combinedDiagnosisData.value)
    };

    const response = await fetch(`${SERVER_API_URL}/api_chat/Agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: 'health_monitor_system',
        session_id: `online_diagnosis_${Date.now()}`,
        request_id: `online_${uuidv4()}`,
        model: 'nebula',
        agent: 'HealthDiagnosisAgent',
        icenter: false,
        rdc: false,
        think: true,
        content: JSON.stringify(onlineHealthData),
        context: '网元在线健康诊断分析',
        component: 'HealthMonitor',
        knowledge: 'OnlineDiagnosisKnowledge',
      }),
    });

    console.log('在线诊断API响应状态:', response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.trim() === '') continue;

        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6);

          if (dataStr === '[DONE]') {
            console.log('收到结束标记 [DONE]');
            break;
          }

          try {
            const data = JSON.parse(dataStr);
            if (data.text) {
              fullResponse += data.text;
            }
          } catch (e) {
            console.error('解析JSON出错:', e);
          }
        }
      }
    }

    // 解析在线诊断报告
    try {
      const reportData = parseOnlineDiagnosisReport(fullResponse);
      onlineDiagnosisReport.value = reportData;
      console.log('在线诊断报告数据:', reportData);
      MessagePlugin.success('在线诊断报告生成完成');
    } catch (parseError) {
      console.error('解析在线报告错误:', parseError);
      onlineDiagnosisReport.value = {
        overallAssessment: {
          healthStatus: "信息",
          score: 0,
          summary: "在线健康诊断报告"
        },
        rawContent: fullResponse
      };
      MessagePlugin.success('在线诊断报告生成完成');
    }

  } catch (error) {
    console.error('生成在线诊断报告错误:', error);
    MessagePlugin.error(`生成在线诊断报告失败: ${error.message}`);
  } finally {
    generatingOnlineReport.value = false;
  }
};

const generateOnlineHealthSummary = (data) => {
  if (!data || data.length === 0) {
    console.log('generateOnlineHealthSummary: 数据为空');
    return {};
  }
  const cpuData = data.filter(item => item.item === 'CPU Utilization');
  const memoryData = data.filter(item => item.item === 'Memory Usage');
  const diskData = data.filter(item => item.item === 'Disk Usage Rate');
  const queueData = data.filter(item => item.item === 'TIPC Queue Usage');
  const ssdLifeData = data.filter(item => item.item === 'SSD Remain Life');
  const spareBlocksData = data.filter(item => item.item === 'Valid Spare Blocks');

  //数值提取函数
  const extractOnlineValue = (item) => {
    if (!item || !item.result) {
      console.log('extractOnlineValue: item 或 result 为空', item);
      return 0;
    }

    const result = item.result.toString();

    //格式提取数字
    if (/^\d+$/.test(result.trim())) {
      const value = parseFloat(result.trim());
      return value;
    }

    // 格式2: 带百分号 "75%"
    const percentMatch = result.match(/(\d+(\.\d+)?)%/);
    if (percentMatch) {
      const value = parseFloat(percentMatch[1]);
      return value;
    }

    // 格式3: 带单位 "75 %"
    const unitMatch = result.match(/(\d+(\.\d+)?)\s*%/);
    if (unitMatch) {
      const value = parseFloat(unitMatch[1]);
      return value;
    }

    // 格式4: 包含数字的字符串
    const anyNumberMatch = result.match(/(\d+(\.\d+)?)/);
    if (anyNumberMatch) {
      const value = parseFloat(anyNumberMatch[1]);
      return value;
    }

    return 0;
  };

  const summary = {
    latestMetrics: {
      cpuUsage: cpuData.length > 0 ? extractOnlineValue(cpuData[0]) : 0,
      memUsage: memoryData.length > 0 ? extractOnlineValue(memoryData[0]) : 0,
      diskSpace: diskData.length > 0 ? extractOnlineValue(diskData[0]) : 0,
      queueUsage: queueData.length > 0 ? extractOnlineValue(queueData[0]) : 0,
      ssdRemainLife: ssdLifeData.length > 0 ? extractOnlineValue(ssdLifeData[0]) : 100,
      validSpareBlocks: spareBlocksData.length > 0 ? extractOnlineValue(spareBlocksData[0]) : 100
    },
    dataPoints: data.length,
    components: {
      cpu: cpuData,
      memory: memoryData,
      disk: diskData,
      queue: queueData,
      ssdLife: ssdLifeData,
      spareBlocks: spareBlocksData
    }
  };

  return summary;
};

// 从结果字符串中提取数值
const extractValue = (resultString) => {
  if (!resultString) return 0;
  const match = resultString.match(/(\d+(\.\d+)?)/);
  return match ? parseFloat(match[1]) : 0;
};

// 解析在线诊断报告
const parseOnlineDiagnosisReport = (markdownText) => {
  try {
    const report = {
      overallAssessment: {
        healthStatus: '',
        score: 0,
        summary: ''
      },
      metricAnalysis: {},
      trendAnalysis: '',
      comprehensiveSuggestions: [],
      urgentActions: []
    };

    // 解析总体健康评估
    const overallMatch = markdownText.match(/## 一、总体健康评估([\s\S]*?)(?=## 二、|$)/);
    if (overallMatch) {
      const overallSection = overallMatch[1];

      // 提取健康状态
      const statusMatch = overallSection.match(/\*\*健康状态\*\*:\s*([🟢🟡🔴\s]*)([^\n]*)/);
      if (statusMatch) {
        const emoji = statusMatch[1].trim();
        const text = statusMatch[2].trim();
        report.overallAssessment.healthStatus = `${emoji} ${text}`.trim();
      } else {
        report.overallAssessment.healthStatus = '🟢 健康';
      }

      // 提取总体评分
      const scoreMatch = overallSection.match(/\*\*总体评分\*\*:\s*\[?(\d{1,3})\]?\s*分/);
      if (scoreMatch) {
        report.overallAssessment.score = parseInt(scoreMatch[1]);
      } else {
        // 自动计算分数
        const calculatedScore = calculateOnlineAutoScore(combinedDiagnosisData.value);
        report.overallAssessment.score = calculatedScore;
      }

      // 提取评估摘要
      const summaryMatch = overallSection.match(/\*\*评估摘要\*\*:\s*([^\n]+)/);
      if (summaryMatch) {
        let summary = summaryMatch[1].trim();
        summary = summary.replace(/\s*---\s*$/, '');
        summary = summary.replace(/\s*-\s*-\s*-.*$/, '');
        report.overallAssessment.summary = summary;
      } else {
        report.overallAssessment.summary = '在线健康诊断评估完成';
      }
    }

    // 解析详细指标分析
    const metricsSectionMatch = markdownText.match(/## 二、详细指标分析([\s\S]*?)(?=## 三、|$)/);
    if (metricsSectionMatch) {
      const metricsSection = metricsSectionMatch[1];

      // 定义在线诊断的指标列表
      const onlineMetrics = ['CPU使用率分析', '内存使用率分析', '磁盘使用率分析', '队列使用率分析', 'SSD健康状态分析'];

      onlineMetrics.forEach(metric => {
        const metricRegex = new RegExp(`### ${metric}([\\s\\S]*?)(?=### |## |$)`);
        const metricMatch = metricsSection.match(metricRegex);

        if (metricMatch) {
          const metricText = metricMatch[1];

          // 提取状态
          let status = '';
          const statusMatch = metricText.match(/\*\*状态\*\*:\s*([🟢🟡🔴\s]*)([^\n]*)/);
          if (statusMatch) {
            const emoji = statusMatch[1].trim();
            const text = statusMatch[2].trim();
            status = `${emoji} ${text}`.trim();
          } else {
            status = '🟢 正常';
          }

          // 提取分析
          let analysis = '';
          const analysisMatch = metricText.match(/\*\*分析\*\*:\s*([\s\S]*?)(?=\*\*建议\*\*|\*\*当前值\*\*|\*\*状态\*\*|### |## |$)/);
          if (analysisMatch) {
            analysis = analysisMatch[1].trim();
            analysis = analysis.replace(/\s*---\s*$/, '');
            analysis = analysis.replace(/\s*-\s*-\s*-.*$/, '');
          } else {
            analysis = '在线指标分析完成';
          }

          // 提取建议
          let suggestion = '';
          const suggestionMatch = metricText.match(/\*\*建议\*\*:\s*([\s\S]*?)(?=\*\*当前值\*\*|\*\*状态\*\*|\*\*分析\*\*|### |## |$)/);
          if (suggestionMatch) {
            suggestion = suggestionMatch[1].trim();
            suggestion = suggestion.replace(/\s*---\s*$/, '');
            suggestion = suggestion.replace(/\s*-\s*-\s*-.*$/, '');
          }

          report.metricAnalysis[metric] = {
            status: status,
            analysis: analysis,
            suggestion: suggestion
          };
        }
      });
    }

    // 解析趋势分析
    const trendMatch = markdownText.match(/## 三、趋势分析与预测\s*\n([^#]+)(?=##|$)/);
    if (trendMatch) {
      let trendText = trendMatch[1].trim();
      trendText = trendText.replace(/\s*---\s*$/, '');
      report.trendAnalysis = trendText;
    }

    // 解析综合优化建议
    const suggestionsMatch = markdownText.match(/## 四、综合优化建议\s*\n([^#]+)(?=##|$)/);
    if (suggestionsMatch) {
      const suggestionsText = suggestionsMatch[1];
      const suggestions = suggestionsText.split('\n')
        .filter(line => {
          const trimmed = line.trim();
          return trimmed && /[•\-*]/.test(trimmed);
        })
        .map(line => line.replace(/[•\-*]\s*/, '').trim());
      report.comprehensiveSuggestions = suggestions;
    }

    // 解析紧急处理事项
    const urgentMatch = markdownText.match(/## 五、紧急处理事项\s*\n([\s\S]*?)(?=##|$)/);
    if (urgentMatch) {
      const urgentText = urgentMatch[1];
      const urgentItems = urgentText.split('\n')
        .filter(line => {
          const trimmed = line.trim();
          // 增强过滤条件，排除以 "--" 开头的分隔符
          return trimmed &&
                 trimmed !== '--' &&
                 !trimmed.startsWith('--') &&  // 排除以 "--" 开头的行
                 !trimmed.startsWith('---') && // 排除以 "---" 开头的行
                 (/[•\-*]/.test(trimmed) ||
                  trimmed.includes('紧急') ||
                  trimmed.includes('处理') ||
                  trimmed.includes('立即') ||
                  trimmed.includes('尽快') ||
                  trimmed.includes('重要')) &&
                 !trimmed.startsWith('---') &&
                 !/^-\s*-/.test(trimmed) &&
                 !trimmed.includes('报告人') &&
                 !trimmed.includes('网元健康诊断专家系统') &&
                 trimmed.length > 2;
        })
        .map(line => {
          let content = line.replace(/[•\-*]\s*/, '').trim();
          content = content.replace(/\s*---\s*$/, '');
          // 进一步清理可能包含的报告人信息
          content = content.replace(/\*报告人\*\s*:[^]*$/, '');
          content = content.replace(/报告人[：:][^]*$/, '');
          content = content.replace(/网元健康诊断专家系统[^]*$/, '');
          return content;
        })
        .filter(content => {
          return content &&
                 !content.includes('报告人') &&
                 !content.includes('网元健康诊断专家系统') &&
                 content.length > 0 &&
                 content !== '--'; // 再次过滤 "--"
        });
      report.urgentActions = urgentItems;
    }
    return report;
  } catch (error) {
    console.error('解析在线诊断报告错误:', error);
    return null;
  }
};

// 自动计算在线诊断分数
const calculateOnlineAutoScore = (data) => {
  let score = 85; // 基础分

  // 根据各个指标状态调整分数
  data.forEach(item => {
    const component = item.component;
    const status = item.status;
    const result = item.result;

    if (status === 'Normal') {
      score += 2;
    } else if (status === 'Warning') {
      score -= 5;
    } else if (status === 'Error') {
      score -= 15;
    }

    // 对于特定组件额外调整
    if (component === 'CPU Utilization') {
      const cpuValue = extractValue(result);
      if (cpuValue > 80) score -= 10;
      else if (cpuValue > 60) score -= 5;
    } else if (component === 'Memory Usage') {
      const memValue = extractValue(result);
      if (memValue > 80) score -= 10;
      else if (memValue > 60) score -= 5;
    } else if (component === 'SSD Remain Life') {
      const ssdValue = extractValue(result);
      if (ssdValue < 30) score -= 20;
      else if (ssdValue < 50) score -= 10;
    }
  });

  // 确保分数在合理范围内
  return Math.max(0, Math.min(100, score));
};

const welcomeMessage = `🎯 您好！我是专业的网元健康助手AI智能体

📊 我的专业能力包括：
• 深度分析网元健康体检报告
• 能够对硬件资源如微动开关状态、SSD状态、交换芯片状态、时钟芯片状态、PHY芯片状态、EEPROM状态、FPGA状态等硬件器件实时监控和预警
• 能够对软件资源如CPU利用率、内存利用率、SSD利用率、SSD寿命、信号量、消息队列、文件描述符等软件资源实时监控和预警
• 能够对数据资源进行网元内数据对账、配置残余等进行快速诊断
• 提供智能预测和优化建议

💡 您可以这样问我：
• "分析一下SSD剩余寿命情况"
• "CPU使用率正常吗？"
• "系统整体健康状态如何？"
• "有哪些优化建议？"

请告诉我您关心的健康指标或具体问题，我将为您提供专业的分析！`;

// 打开 AI 聊天对话框
const openAIChatDialog = () => {
  aiDrawerVisible.value = true;

  // 如果还没有初始化对话，添加欢迎消息
  if (aiChatList.value.length === 0) {
    aiChatList.value.unshift({
      avatar: '/src/assets/assets-ai2.png',
      datetime: new Date().toLocaleString(),
      content: welcomeMessage,
      role: 'assistant',
      showActions: true,
    });
  }
};

// 新建 AI 对话
const handleNewAIChat = () => {
  aiChatList.value = [];
  aiInputText.value = '';
  MessagePlugin.info('已开始新的对话');

  // 重新添加欢迎消息
  aiChatList.value.unshift({
    avatar: '/src/assets/assets-ai2.png',
    datetime: new Date().toLocaleString(),
    content: welcomeMessage,
    role: 'assistant',
    showActions: true,
  });
};

// AI 聊天操作处理
const handleAIOperation = (type, options, index) => {
  if (type === 'copy') {
    navigator.clipboard.writeText(options.content);
    MessagePlugin.success('已复制到剪贴板');
  }
};

// 停止 AI 流式响应
const handleOnAIStop = () => {
  aiStreamLoading.value = false;
  // 这里可以添加停止流式请求的逻辑
};

// 发送 AI 消息
const handleOnAISend = async (inputValue) => {
  if (aiStreamLoading.value || !inputValue) return;

  // 添加用户消息
  aiChatList.value.unshift({
    avatar: '/src/assets/assets-user3.png',
    datetime: new Date().toLocaleString(),
    content: inputValue,
    role: 'user',
    showActions: true,
  });

  // 添加AI回答占位项
  aiChatList.value.unshift({
    avatar: '/src/assets/assets-ai2.png',
    datetime: new Date().toLocaleString(),
    content: '',
    role: 'assistant',
    showActions: false,
    textLoading: true,
  });

  await handleAIData(inputValue);
  aiInputText.value = '';
};

// 格式化消息内容，统一处理换行符
const formatMessage = (content) => {
  if (!content) return '';

  // 将多个连续换行符替换为单个换行符
  return content.replace(/\n\s*\n\s*\n/g, '\n\n').replace(/\n{3,}/g, '\n\n');
};

const formatMessageForDisplay = (content) => {
  if (!content) return '';

  return content
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/\n/g, '<br>');
};

// 处理 AI 数据请求
const handleAIData = async (inputValue) => {
  aiStreamLoading.value = true;
  const currentResponse = aiChatList.value[0];

  try {
    // 构建对话上下文，包含诊断报告信息
    const chatContext = {
      diagnosisReport: diagnosisReport.value,
      healthMetrics: chartData.value,
      userQuestion: inputValue
    };

    const response = await fetch(`${SERVER_API_URL}/api_chat/Agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: 'health_monitor_user',
        session_id: `health_chat_${Date.now()}`,
        request_id: `health_chat_${uuidv4()}`,
        model: aiSelectModelValue.value.value,
        agent: 'HealthDiagnosisAgent',
        icenter: false,
        rdc: false,
        think: true,
        content: inputValue,
        context: JSON.stringify(chatContext),
        component: 'HealthMonitor',
        knowledge: 'HealthDiagnosisKnowledge',
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.trim() === '') continue;

        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6);

          if (dataStr === '[DONE]') {
            currentResponse.showActions = true;
            currentResponse.textLoading = false;
            aiStreamLoading.value = false;
            return;
          }

          try {
            const data = JSON.parse(dataStr);
            if (data.text) {
              fullResponse += data.text;
              // 初步规范化换行符
              let processedResponse = fullResponse.replace(/\n{3,}/g, '\n\n');
              currentResponse.content = processedResponse;
            }
          } catch (e) {
            console.error('解析JSON出错:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('AI对话请求出错:', error);
    currentResponse.content = `抱歉，处理您的请求时出现错误: ${error.message}`;
    currentResponse.showActions = true;
    currentResponse.textLoading = false;
    aiStreamLoading.value = false;
  }
};

// 在线健康诊断数据
const combinedDiagnosisData = ref([]);

// 诊断信息表格列定义
const diagnosisColumns = [
  {
    colKey: 'no',
    title: 'No',
    width: 60,
    align: 'center'
  },
  {
    colKey: 'component',
    title: 'Component',
    width: 120,
    align: 'center'
  },
  {
    colKey: 'item',
    title: 'Item',
    width: 200,
    align: 'center'
  },
  {
    colKey: 'result',
    title: 'Result',
    width: 120,
    align: 'center'
  },
  {
    colKey: 'referenceValue',
    title: 'Reference Value',
    width: 140,
    align: 'center'
  },
  {
    colKey: 'status',
    title: 'Status',
    width: 100,
    align: 'center',
    cell: (h, { row }) => {
      let theme = 'default';
      if (row.status === 'Normal') {
        theme = 'success';
      } else if (row.status === '--') {
        theme = 'default';
      }
      return <t-tag theme={theme} variant="light" size="small">{row.status}</t-tag>;
    }
  }
];


// 响应式数据
const files = ref([]);
const uploading = ref(false);
const uploadStatus = ref(null);
const chartData = ref([]);

// 最近上传记录
const recentUploads = ref([]);
//标记是否已加载示例数据
const hasLoadedSampleData = ref(false);

// 图表引用
const cpuChart = ref(null);
const memChart = ref(null);
const diskChart = ref(null);
const queueChart = ref(null);
const ssdChart = ref(null);
const spareChart = ref(null);
const procMemChart = ref(null);

// 图表实例
let cpuChartInstance = null;
let memChartInstance = null;
let diskChartInstance = null;
let queueChartInstance = null;
let ssdChartInstance = null;
let spareChartInstance = null;
let procMemChartInstance = null;

const processNames = ['WASON', 'QXOAGENT', 'MIM', 'UEM', 'TOPUEM', 'USM', 'UPP2OTNAGENT'];

// 表格列定义
const columns = [
  {
    colKey: 'timestamp',
    title: '时间戳',
    width: 180,
    ellipsis: true,
  },
  {
    colKey: 'cpuUsage',
    title: 'CPU使用率(%)',
    width: 120,
    align: 'center',
  },
  {
    colKey: 'memUsage',
    title: '内存使用率(%)',
    width: 120,
    align: 'center',
  },
  {
    colKey: 'diskSpace',
    title: '磁盘使用率(%)',
    width: 120,
    align: 'center',
  },
  {
    colKey: 'queueUsage',
    title: '队列使用率(%)',
    width: 120,
    align: 'center',
  },
  {
    colKey: 'ssdRemainLife',
    title: 'SSD剩余寿命(%)',
    width: 120,
    align: 'center',
  },
  {
    colKey: 'validSpareBlocks',
    title: 'SSD有效备用块',
    width: 120,
    align: 'center',
  },
];

const uploadKey = ref(0);

// 加载离线示例数据
const loadSampleData = async () => {
  if (hasLoadedSampleData.value) {
    console.log('示例数据已加载过，跳过重复加载');
    return;
  }
  console.log('开始加载示例数据...');

  try {
    generatingReport.value = true;

    const response = await fetch(`${SERVER_API_URL}/getSampleHealthData`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        request_type: 'sample_data',
        timestamp: new Date().getTime()
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === 'success') {
      resetDiagnosisData();
      chartData.value = result.data || [];

      if (chartData.value.length > 0) {
        await nextTick();
        initCharts();
        await generateDiagnosisReport();

        // 标记已加载示例数据
        hasLoadedSampleData.value = true;

      } else {
        MessagePlugin.warning('示例数据加载完成但未找到有效数据');
      }
    } else {
      throw new Error(result.message || '加载示例数据失败');
    }
  } catch (error) {
    console.error('加载示例数据错误:', error);
    MessagePlugin.error(`加载示例数据失败: ${error.message}`);
  } finally {
    generatingReport.value = false;
  }
};

// 在线诊断专用 加载离线示例图表数据
const loadSampleDataForOnlineDiagnosis = async () => {
  try {
    generatingReport.value = true;

    const response = await fetch(`${SERVER_API_URL}/getSampleHealthData`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        request_type: 'online_diagnosis',
        ip: onlineDiagnosisConfig.value.targetIp,
        shelf: onlineDiagnosisConfig.value.shelf,
        slot: onlineDiagnosisConfig.value.slot,
        timestamp: new Date().getTime()
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result = await response.json();

    if (result.status === 'success') {
      // 只重置图表相关数据，不清除诊断报告
      chartData.value = result.data || [];

      if (chartData.value.length > 0) {
        await nextTick();
        initCharts();
        // 生成诊断报告（如果已经有诊断报告，可以跳过或更新）
        if (!diagnosisReport.value) {
          await generateDiagnosisReport();
        }

      } else {
        MessagePlugin.warning('图表数据加载完成但未找到有效数据');
      }
    } else {
      throw new Error(result.message || '加载示例图表数据失败');
    }
  } catch (error) {
    console.error('加载示例图表数据错误:', error);
    MessagePlugin.error(`加载图表数据失败: ${error.message}`);
  } finally {
    generatingReport.value = false;
  }
};

// 文件上传
const uploadFile = async (file) => {
  uploading.value = true;
  uploadStatus.value = null;

  try {
    // 检查文件类型
    if (!file.raw?.name?.toLowerCase().endsWith('.log')) {
      throw new Error('仅支持 .log 格式的二进制日志文件');
    }

    const formData = new FormData();
    formData.append('file', file.raw);

    const response = await fetch(`${SERVER_API_URL}/parseHealthLog`, {
      method: 'POST',
      body: formData,
    });

    console.log('响应状态:', response.status, response.statusText);

    const contentType = response.headers.get('content-type');
    console.log('响应Content-Type:', contentType);

    let result;

    if (contentType && contentType.includes('application/json')) {
      result = await response.json();
    } else {
      const textResponse = await response.text();
      console.error('非JSON响应:', textResponse.substring(0, 500));

      if (response.status === 404) {
        throw new Error('API接口未找到 (404)，请检查后端服务');
      } else if (response.status === 500) {
        throw new Error('服务器内部错误 (500)');
      } else if (textResponse.includes('<!DOCTYPE html>') || textResponse.includes('<!doctype html>')) {
        throw new Error('后端返回了HTML页面而不是JSON数据，请检查API地址和服务状态');
      } else {
        throw new Error(`服务器返回了意外的响应格式: ${contentType}`);
      }
    }

    if (!response.ok) {
      throw new Error(result.message || `请求失败: ${response.status} ${response.statusText}`);
    }

    if (result.status === 'success') {
      uploadStatus.value = {
        type: 'success',
        message: result.message || '日志文件解析成功'
      };

      // 重置诊断报告
      resetDiagnosisData();

      // 处理返回的图表数据
      chartData.value = result.data || [];

      // 添加到最近上传记录
     // addToRecentUploads(file.raw.name, result.data);

      if (chartData.value.length > 0) {
        await nextTick();
        initCharts();

        MessagePlugin.success(result.message || '日志解析完成，正在生成诊断报告...');

        // 异步生成诊断报告，不阻塞上传完成状态
        generateDiagnosisReport();
      } else {
        MessagePlugin.warning('解析完成但未找到有效数据');
      }
    } else {
      throw new Error(result.message || '日志解析失败');
    }

    // 上传完成后强制重新渲染上传组件
    uploadKey.value += 1;

    return {
      status: 'success',
      response: { code: 0 }
    };
  } catch (error) {
    console.error('文件上传错误:', error);

    let errorMessage = error.message;

    // 处理网络错误
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      errorMessage = `网络连接失败，请检查: ${SERVER_API_URL} 是否可访问`;
    }

    uploadStatus.value = {
      type: 'error',
      message: errorMessage
    };

    MessagePlugin.error(`上传失败: ${errorMessage}`);

    uploadKey.value += 1;
    return {
      status: 'fail',
      error: errorMessage
    };
  } finally {
    // 文件上传完成，无论成功失败都重置上传状态
    uploading.value = false;
  }
};

// 上传成功和失败的处理函数
const handleUploadSuccess = () => {
  console.log('上传成功，重置上传组件');
  // 清空文件列表
  files.value = [];
};

const handleUploadFail = () => {
  console.log('上传失败，重置上传组件');
  // 清空文件列表
  files.value = [];
};

// 添加到最近上传记录
const addToRecentUploads = (fileName, data) => {
  const uploadRecord = {
    fileName,
    timestamp: new Date().getTime(),
    data: data.length > 100 ? null : data.slice(0, 100), // 只保存前100条数据或为空
    size: data.length,
    isLargeFile: data.length > 1000
  };

  recentUploads.value.unshift(uploadRecord);

  // 只保留最近5条记录
  if (recentUploads.value.length > 5) {
    recentUploads.value = recentUploads.value.slice(0, 5);
  }

  try {
    const simplifiedRecords = recentUploads.value.map(record => ({
      fileName: record.fileName,
      timestamp: record.timestamp,
      size: record.size,
      isLargeFile: record.isLargeFile
    }));

    localStorage.setItem('healthMonitorRecentUploads', JSON.stringify(simplifiedRecords));
  } catch (error) {
    console.warn('保存到localStorage失败，可能是存储空间不足:', error);
    // 清空localStorage中的大文件记录
    localStorage.removeItem('healthMonitorRecentUploads');
  }
};

// 加载上传数据
const loadUploadData = async (upload) => {
  if (!upload.data || upload.isLargeFile) {
    MessagePlugin.warning(`${upload.fileName} 是大文件，请重新上传进行分析`);
    return;
  }

  resetDiagnosisData();
  chartData.value = upload.data || [];
  if (chartData.value.length > 0) {
    await nextTick();
    initCharts();

    // 自动生成诊断报告
    await generateDiagnosisReport();

    MessagePlugin.success(`已加载文件: ${upload.fileName}`);
  }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 初始化图表
const initCharts = () => {
  if (chartData.value.length === 0) return;

  const timeData = chartData.value.map(item => item.timestamp);

  const useDataZoom = timeData.length > 15; // 超过15个数据点时启用缩放

  // 销毁旧图表实例
  [cpuChartInstance, memChartInstance, diskChartInstance, queueChartInstance,
   ssdChartInstance, spareChartInstance, procMemChartInstance]
    .forEach(instance => instance && instance.dispose());

  // 初始化新图表
  cpuChartInstance = echarts.init(cpuChart.value);
  memChartInstance = echarts.init(memChart.value);
  diskChartInstance = echarts.init(diskChart.value);
  queueChartInstance = echarts.init(queueChart.value);
  ssdChartInstance = echarts.init(ssdChart.value);
  spareChartInstance = echarts.init(spareChart.value);
  procMemChartInstance = echarts.init(procMemChart.value);

  // 通用图表配置
  const commonOptions = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50, 50, 50, 0.7)',
      borderColor: '#777',
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      },
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach(item => {
          result += `${item.marker} ${item.seriesName}: ${item.value}%<br/>`;
        });
        return result;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: useDataZoom ? '15%' : '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        color: '#666',
        rotate: 45,
        formatter: function(value) {
          if (timeData.length > 50) {
            const date = new Date(value);
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
          }
          return value;
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        color: '#666',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
          type: 'dashed'
        }
      },
      min: 0,
      max: 100
    }
  };

  // 添加数据缩放配置
  const dataZoomConfig = useDataZoom ? {
    dataZoom: [
      {
        type: 'inside', // 内置型数据区域缩放组件
        xAxisIndex: 0, // 控制第一个x轴
        start: 0,      // 默认起始位置
        end: 100,      // 默认结束位置
        zoomLock: false, // 是否锁定选择区域大小
        zoomOnMouseWheel: true, // 允许滚轮缩放
        moveOnMouseWheel: true, // 允许滚轮移动
        preventDefaultMouseMove: true
      },
      {
        type: 'slider', // 滑动条型数据区域缩放组件
        xAxisIndex: 0,
        show: true,
        start: 0,
        end: 100,
        height: 20,
        bottom: 0,
        fillerColor: 'rgba(84, 112, 198, 0.2)',
        borderColor: '#5470c6',
        handleStyle: {
          color: '#5470c6',
          borderColor: '#5470c6'
        },
        moveHandleStyle: {
          color: '#5470c6'
        }
      }
    ]
  } : {};

  // CPU 使用率图表
  cpuChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: 'CPU 使用率趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: 'CPU使用率',
      type: 'line',
      data: chartData.value.map(item => item.cpuUsage),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#5470c6'
      },
      itemStyle: {
        color: '#5470c6'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(84, 112, 198, 0.5)' },
          { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
        ])
      }
    }]
  });

  // 内存使用率图表
  memChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: '系统内存使用率趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: '内存使用率',
      type: 'line',
      data: chartData.value.map(item => item.memUsage),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#91cc75'
      },
      itemStyle: {
        color: '#91cc75'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(145, 204, 117, 0.5)' },
          { offset: 1, color: 'rgba(145, 204, 117, 0.1)' }
        ])
      }
    }]
  });

  // 磁盘使用率图表
  diskChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: 'SSD 磁盘使用率趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: '磁盘使用率',
      type: 'line',
      data: chartData.value.map(item => item.diskSpace),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#fac858'
      },
      itemStyle: {
        color: '#fac858'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(250, 200, 88, 0.5)' },
          { offset: 1, color: 'rgba(250, 200, 88, 0.1)' }
        ])
      }
    }]
  });

  // 队列使用率图表
  queueChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: '队列使用率趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: '队列使用率',
      type: 'line',
      data: chartData.value.map(item => item.queueUsage),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#ee6666'
      },
      itemStyle: {
        color: '#ee6666'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(238, 102, 102, 0.5)' },
          { offset: 1, color: 'rgba(238, 102, 102, 0.1)' }
        ])
      }
    }]
  });

  // SSD 剩余寿命图表
  ssdChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: 'SSD 剩余寿命趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: 'SSD剩余寿命',
      type: 'line',
      data: chartData.value.map(item => item.ssdRemainLife),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#73c0de'
      },
      itemStyle: {
        color: '#73c0de'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(115, 192, 222, 0.5)' },
          { offset: 1, color: 'rgba(115, 192, 222, 0.1)' }
        ])
      }
    }]
  });

  // 有效备用块图表
  spareChartInstance.setOption({
    ...commonOptions,
    ...dataZoomConfig,
    title: {
      text: 'SSD 有效备用块趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 14
      }
    },
    series: [{
      name: '有效备用块',
      type: 'line',
      data: chartData.value.map(item => item.validSpareBlocks),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 3,
        color: '#3ba272'
      },
      itemStyle: {
        color: '#3ba272'
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 162, 114, 0.5)' },
          { offset: 1, color: 'rgba(59, 162, 114, 0.1)' }
        ])
      }
    }]
  });

  // 进程内存使用率图表
  const processColors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666',
    '#73c0de', '#3ba272', '#fc8452'
  ];

  const processSeries = processNames.map((name, index) => ({
    name: name,
    type: 'line',
    data: chartData.value.map(item => item.procMemUsage[name]),
    smooth: true,
    symbol: 'circle',
    symbolSize: 4,
    lineStyle: {
      width: 2,
      color: processColors[index]
    },
    itemStyle: {
      color: processColors[index]
    }
  }));

  const processChartOptions = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50, 50, 50, 0.7)',
      borderColor: '#777',
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      }
    },
    legend: {
      data: processNames,
      top: 'top',
      textStyle: {
        color: '#666'
      },
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: useDataZoom ? '15%' : '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        color: '#666',
        rotate: 45,
        formatter: function(value) {
          if (timeData.length > 50) {
            const date = new Date(value);
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
          }
          return value;
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '内存使用率(%)',
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        color: '#666',
        formatter: '{value}%'
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
          type: 'dashed'
        }
      },
      min: 0,
      max: 100
    },
    series: processSeries
  };

  // 进程内存图表
  if (useDataZoom) {
    processChartOptions.dataZoom = [
      {
        type: 'inside',
        xAxisIndex: 0,
        start: 0,
        end: 100,
        zoomLock: false,
        zoomOnMouseWheel: true,
        moveOnMouseWheel: true,
        preventDefaultMouseMove: true
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        show: true,
        start: 0,
        end: 100,
        height: 20,
        bottom: 0,
        fillerColor: 'rgba(84, 112, 198, 0.2)',
        borderColor: '#5470c6',
        handleStyle: {
          color: '#5470c6',
          borderColor: '#5470c6'
        },
        moveHandleStyle: {
          color: '#5470c6'
        }
      }
    ];
  }

  procMemChartInstance.setOption(processChartOptions);

  // 响应式调整图表大小
  window.addEventListener('resize', handleResize);
};

// 重置诊断报告数据
const resetDiagnosisData = () => {
  diagnosisReport.value = null;
  generatingReport.value = false;
  console.log('诊断报告数据已重置');
};

// 处理窗口大小变化
const handleResize = () => {
  [cpuChartInstance, memChartInstance, diskChartInstance, queueChartInstance,
   ssdChartInstance, spareChartInstance, procMemChartInstance]
    .forEach(instance => {
      if (instance) {
        instance.resize();
        // 重新应用缩放
        const options = instance.getOption();
        if (options.dataZoom && options.dataZoom.length > 0) {
          instance.dispatchAction({
            type: 'dataZoom',
            start: 0,
            end: 100
          });
        }
      }
    });
};

// 跳转到聊天页面
const jumpToChatPage = () => {
  router.push('/ai/diag');
};

// 组件卸载时清理
onUnmounted(() => {
  [cpuChartInstance, memChartInstance, diskChartInstance, queueChartInstance,
   ssdChartInstance, spareChartInstance, procMemChartInstance]
    .forEach(instance => instance && instance.dispose());

  window.removeEventListener('resize', handleResize);

  // 清理批量分析定时器
  if (batchAnalysisTimer.value) {
    clearInterval(batchAnalysisTimer.value);
    batchAnalysisTimer.value = null;
  }
});

onMounted(() => {
  console.log('SERVER_API_URL:', SERVER_API_URL);
  console.log('健康监控页面已加载');
  resetDiagnosisData();

  // 从本地存储加载最近上传记录
  const savedUploads = localStorage.getItem('healthMonitorRecentUploads');
  if (savedUploads) {
    try {
      recentUploads.value = JSON.parse(savedUploads);
    } catch (e) {
      console.error('加载最近上传记录失败:', e);
    }
  }
  console.log('开始自动加载示例诊断报告...');
  setTimeout(() => {
    loadSampleData();
  }, 500);
});



// 检查是否有详细分析内容
const hasDetailedAnalysis = (report) => {
  return report.cpuAnalysis || report.memoryAnalysis || report.diskAnalysis ||
         report.queueAnalysis || report.ssdAnalysis || report.ssdSpareBlocksAnalysis ||
         report.processAnalysis;
};


// 添加响应式数据
const diagnosisReport = ref(null);
const generatingReport = ref(false);

// 严重程度主题映射
const getSeverityTheme = (severity) => {
  const themeMap = {
    'normal': 'success',
    'warning': 'warning',
    'critical': 'error',
    'danger': 'error'
  };
  return themeMap[severity] || 'default';
};

// 严重程度文本映射
const getSeverityText = (severity) => {
  const textMap = {
    'normal': '正常',
    'warning': '警告',
    'critical': '严重',
    'danger': '危险'
  };
  return textMap[severity] || '未知';
};

// 总体评价主题
const getAssessmentTheme = (severity) => {
  const themeMap = {
    'normal': 'success',
    'warning': 'warning',
    'critical': 'error'
  };
  return themeMap[severity] || 'info';
};

const generateDiagnosisReport = async () => {

  if (chartData.value.length === 0) {
    MessagePlugin.warning('请先上传并解析日志文件');
    return;
  }

  generatingReport.value = true;
  diagnosisReport.value = null;

  try {
    const healthData = {
      metrics: chartData.value,
      summary: generateHealthSummary(chartData.value)
    };

    const response = await fetch(`${SERVER_API_URL}/api_chat/Agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: 'health_monitor_system',
        session_id: `health_diagnosis_${Date.now()}`,
        request_id: `health_${uuidv4()}`,
        model: 'nebula',
        agent: 'HealthDiagnosisAgent',
        icenter: false,
        rdc: false,
        think: true,
        content: JSON.stringify(healthData),
        context: '网元健康诊断日志分析',
        component: 'HealthMonitor',
        knowledge: 'NoneKnowledge',
      }),
    });

    console.log('API响应状态:', response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.trim() === '') continue;

        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6);

          if (dataStr === '[DONE]') {
            console.log('收到结束标记 [DONE]');
            break;
          }

          try {
            const data = JSON.parse(dataStr);
            if (data.text) {
              fullResponse += data.text;
              //console.log('收到数据块:', data.text.substring(0, 50) + '...');
            }
          } catch (e) {
            console.error('解析JSON出错:', e);
          }
        }
      }
    }

    //console.log('完整响应:', fullResponse);

    // 解析大模型返回的健康诊断报告
    try {
      const reportData = parseHealthDiagnosisReport(fullResponse);
      diagnosisReport.value = reportData;
      console.log('诊断报告数据:', reportData);
    } catch (parseError) {
      console.error('解析错误:', parseError);
      // 如果解析失败，将原始文本作为报告内容
      diagnosisReport.value = {
        overallAssessment: {
          healthStatus: "信息",
          score: 0,
          summary: "健康诊断报告"
        },
        rawContent: fullResponse
      };
      MessagePlugin.success('诊断报告生成完成');
    }

  } catch (error) {
    console.error('生成诊断报告错误:', error);
    MessagePlugin.error(`生成诊断报告失败: ${error.message}`);
  } finally {
    generatingReport.value = false;
  }
};


// Markdown 报告解析函数
const parseMarkdownReport = (markdownText) => {
  const lines = markdownText.split('\n');
  const report = {
    overallAssessment: {
      severity: "normal",
      summary: "",
      details: ""
    },
    cpuAnalysis: null,
    memoryAnalysis: null,
    diskAnalysis: null,
    queueAnalysis: null,
    ssdAnalysis: null,
    ssdSpareBlocksAnalysis: null,
    processAnalysis: null,
    comprehensiveSuggestions: [],
    rawContent: markdownText
  };

  let currentSection = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.startsWith('### 总体评估')) {
      currentSection = 'overall';
      continue;
    } else if (line.startsWith('### 详细指标分析')) {
      currentSection = 'metrics';
      continue;
    } else if (line.startsWith('### 综合优化建议')) {
      currentSection = 'suggestions';
      continue;
    }

    // 解析总体评估
    if (currentSection === 'overall') {
      if (line.startsWith('**状态**:')) {
        const summary = line.replace('**状态**:', '').trim();
        report.overallAssessment.summary = summary;

        // 根据文本判断严重程度
        if (summary.includes('良好') || summary.includes('正常')) {
          report.overallAssessment.severity = 'normal';
        } else if (summary.includes('警告') || summary.includes('注意')) {
          report.overallAssessment.severity = 'warning';
        } else if (summary.includes('严重') || summary.includes('立即处理')) {
          report.overallAssessment.severity = 'critical';
        }
      } else if (line.startsWith('**详情**:')) {
        report.overallAssessment.details = line.replace('**详情**:', '').trim();
      }
    }

    // 解析详细指标分析
    if (currentSection === 'metrics') {
      // CPU 使用率
      if (line.includes('CPU使用率') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.cpuAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        // 读取后续的评估和建议
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.cpuAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.cpuAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // 内存使用率
      else if (line.includes('内存使用率') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.memoryAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.memoryAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.memoryAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // 磁盘使用率
      else if (line.includes('磁盘使用率') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.diskAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.diskAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.diskAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // 队列使用率
      else if (line.includes('队列使用率') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.queueAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.queueAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.queueAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // SSD寿命
      else if (line.includes('SSD寿命') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.ssdAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.ssdAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.ssdAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // SSD有效备用块
      else if ((line.includes('SSD有效备用块') || line.includes('有效备用块')) && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.ssdSpareBlocksAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.ssdSpareBlocksAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.ssdSpareBlocksAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
      // 进程内存
      else if (line.includes('进程内存') && (line.includes('🟢') || line.includes('🟡') || line.includes('🔴'))) {
        report.processAnalysis = {
          severity: getSeverityFromEmoji(line),
          assessment: '',
          suggestion: ''
        };
        let j = i + 1;
        while (j < lines.length && !lines[j].includes('**') && lines[j].trim() !== '') {
          const contentLine = lines[j].trim();
          if (contentLine.startsWith('- 评估:')) {
            report.processAnalysis.assessment = contentLine.replace('- 评估:', '').trim();
          } else if (contentLine.startsWith('- 建议:')) {
            report.processAnalysis.suggestion = contentLine.replace('- 建议:', '').trim();
          }
          j++;
        }
      }
    }

    // 解析综合建议
    if (currentSection === 'suggestions') {
      if (line.startsWith('🟡') || line.startsWith('🔴') || line.startsWith('🟢')) {
        const priority = line.startsWith('🔴') ? 'high' : line.startsWith('🟡') ? 'medium' : 'low';
        const content = line.substring(2).trim(); // 移除表情符号
        report.comprehensiveSuggestions.push({
          priority: priority,
          content: content
        });
      }
    }
  }

  return report;
};

// 从表情符号获取严重程度
const getSeverityFromEmoji = (line) => {
  if (line.includes('🔴')) return 'critical';
  if (line.includes('🟡')) return 'warning';
  if (line.includes('🟢')) return 'normal';
  return 'normal';
};

// 生成健康数据摘要
const generateHealthSummary = (data) => {
  if (!data || data.length === 0) return {};

  const latest = data[data.length - 1];
  const averages = calculateAverages(data);

  return {
    latestMetrics: {
      cpuUsage: latest.cpuUsage,
      memUsage: latest.memUsage,
      diskSpace: latest.diskSpace,
      queueUsage: latest.queueUsage,
      ssdRemainLife: latest.ssdRemainLife,
      validSpareBlocks: latest.validSpareBlocks
    },
    averageMetrics: averages,
    dataPoints: data.length,
    timeRange: {
      start: data[0].timestamp,
      end: data[data.length - 1].timestamp
    },
    trends: analyzeTrends(data)
  };
};

// 计算平均值
const calculateAverages = (data) => {
  const sums = data.reduce((acc, item) => {
    acc.cpuUsage += item.cpuUsage;
    acc.memUsage += item.memUsage;
    acc.diskSpace += item.diskSpace;
    acc.queueUsage += item.queueUsage;
    return acc;
  }, { cpuUsage: 0, memUsage: 0, diskSpace: 0, queueUsage: 0 });

  const count = data.length;
  return {
    cpuUsage: Math.round(sums.cpuUsage / count),
    memUsage: Math.round(sums.memUsage / count),
    diskSpace: Math.round(sums.diskSpace / count),
    queueUsage: Math.round(sums.queueUsage / count)
  };
};

// 分析趋势
const analyzeTrends = (data) => {
  if (data.length < 2) return {};

  const first = data[0];
  const last = data[data.length - 1];

  return {
    cpuTrend: last.cpuUsage - first.cpuUsage,
    memTrend: last.memUsage - first.memUsage,
    diskTrend: last.diskSpace - first.diskSpace,
    queueTrend: last.queueUsage - first.queueUsage
  };
};

// 在文件上传成功后自动生成报告
watch(() => chartData.value, (newData, oldData) => {
  // 只有当数据从空变为有数据时才自动生成报告
  if (newData && newData.length > 0 && (!oldData || oldData.length === 0)) {
    console.log('检测到新数据，准备自动生成报告...');

    setTimeout(() => {
      generateDiagnosisReport();
    }, 500);
  }
});

// 解析紧急处理事项
const parseHealthDiagnosisReport = (markdownText) => {
  try {
    const report = {
      overallAssessment: {
        healthStatus: '',
        score: 0,
        summary: ''
      },
      metricAnalysis: {},
      trendAnalysis: '',
      comprehensiveSuggestions: [],
      urgentActions: []
    };

    //console.log('开始解析Markdown内容:', markdownText);

    // 解析总体健康评估
    const overallMatch = markdownText.match(/## 一、总体健康评估([\s\S]*?)(?=## 二、|$)/);
    if (overallMatch) {
      const overallSection = overallMatch[1];
      //console.log('总体评估部分:', overallSection);

      // 提取健康状态
      const statusMatch = overallSection.match(/\*\*健康状态\*\*:\s*([🟢🟡🔴\s]*)([^\n]*)/);
      if (statusMatch) {
        const emoji = statusMatch[1].trim();
        const text = statusMatch[2].trim();
        report.overallAssessment.healthStatus = `${emoji} ${text}`.trim();
        console.log('健康状态:', report.overallAssessment.healthStatus);
      } else {
        const altStatusMatch = overallSection.match(/健康状态[：:\s]*([🟢🟡🔴\s]*)([^\n]*)/);
        if (altStatusMatch) {
          const emoji = altStatusMatch[1].trim();
          const text = altStatusMatch[2].trim();
          report.overallAssessment.healthStatus = `${emoji} ${text}`.trim();
        } else {
          report.overallAssessment.healthStatus = '🟢 健康';
        }
      }

      // 提取总体评分
      const scoreMatch = overallSection.match(/\*\*总体评分\*\*:\s*\[?(\d{1,3})\]?\s*分/);
      if (scoreMatch) {
        report.overallAssessment.score = parseInt(scoreMatch[1]);
        console.log('总体评分:', report.overallAssessment.score);
      } else {
        const altScoreMatch = overallSection.match(/总体评分[：:\s]*\[?(\d{1,3})\]?\s*分/);
        if (altScoreMatch) {
          report.overallAssessment.score = parseInt(altScoreMatch[1]);
        } else {
          if (report.overallAssessment.healthStatus.includes('🟢') || report.overallAssessment.healthStatus.includes('健康')) {
            report.overallAssessment.score = 85;
          } else if (report.overallAssessment.healthStatus.includes('🟡') || report.overallAssessment.healthStatus.includes('警告')) {
            report.overallAssessment.score = 60;
          } else if (report.overallAssessment.healthStatus.includes('🔴') || report.overallAssessment.healthStatus.includes('危险')) {
            report.overallAssessment.score = 30;
          } else {
            const calculatedScore = calculateAutoScore(markdownText);
            report.overallAssessment.score = calculatedScore;
          }
        }
      }

      // 提取评估摘要
      const summaryMatch = overallSection.match(/\*\*评估摘要\*\*:\s*([^\n]+)/);
      if (summaryMatch) {
        let summary = summaryMatch[1].trim();
        summary = summary.replace(/\s*---\s*$/, '');
        summary = summary.replace(/\s*-\s*-\s*-.*$/, '');
        report.overallAssessment.summary = summary;
      } else {
        const altSummaryMatch = overallSection.match(/评估摘要[：:\s]*([^\n]+)/);
        if (altSummaryMatch) {
          let summary = altSummaryMatch[1].trim();
          summary = summary.replace(/\s*---\s*$/, '');
          summary = summary.replace(/\s*-\s*-\s*-.*$/, '');
          report.overallAssessment.summary = summary;
        } else {
          report.overallAssessment.summary = '系统健康状态评估完成';
        }
      }
    }

    // 解析详细指标分析
    const metricsSectionMatch = markdownText.match(/## 二、详细指标分析([\s\S]*?)(?=## 三、|$)/);
    if (metricsSectionMatch) {
      const metricsSection = metricsSectionMatch[1];

      const metrics = ['CPU使用率分析', '内存使用率分析', '磁盘使用率分析', '队列使用率分析', 'SSD健康状态分析', '进程内存分析'];

      metrics.forEach(metric => {
        const metricRegex = new RegExp(`### ${metric}([\\s\\S]*?)(?=### |## |$)`);
        const metricMatch = metricsSection.match(metricRegex);

        if (metricMatch) {
          const metricText = metricMatch[1];
          console.log(`${metric} 内容:`, metricText);

          // 提取当前值
          let currentValue = '';
          const currentMatch = metricText.match(/\*\*当前值\*\*:\s*([^\n]+)/);
          if (currentMatch) {
            currentValue = currentMatch[1].trim();
          } else {
            if (metric === 'SSD健康状态分析') {
              currentValue = '剩余寿命: 良好';
            } else if (metric === '进程内存分析') {
              currentValue = '各进程使用正常';
            }
          }

          // 提取状态
          let status = '';
          const statusMatch = metricText.match(/\*\*状态\*\*:\s*([🟢🟡🔴\s]*)([^\n]*)/);
          if (statusMatch) {
            const emoji = statusMatch[1].trim();
            const text = statusMatch[2].trim();
            status = `${emoji} ${text}`.trim();
          } else {
            status = '🟢 正常';
          }

          // 提取分析
          let analysis = '';
          const analysisMatch = metricText.match(/\*\*分析\*\*:\s*([\s\S]*?)(?=\*\*建议\*\*|\*\*当前值\*\*|\*\*状态\*\*|### |## |$)/);
          if (analysisMatch) {
            analysis = analysisMatch[1].trim();
            analysis = analysis.replace(/\s*---\s*$/, '');
            analysis = analysis.replace(/\s*-\s*-\s*-.*$/, '');
          } else {
            analysis = '指标分析完成';
          }

          // 提取建议
          let suggestion = '';
          const suggestionMatch = metricText.match(/\*\*建议\*\*:\s*([\s\S]*?)(?=\*\*当前值\*\*|\*\*状态\*\*|\*\*分析\*\*|### |## |$)/);
          if (suggestionMatch) {
            suggestion = suggestionMatch[1].trim();
            suggestion = suggestion.replace(/\s*---\s*$/, '');
            suggestion = suggestion.replace(/\s*-\s*-\s*-.*$/, '');
            suggestion = suggestion.replace(/^---\s*/, '');
          }

          report.metricAnalysis[metric] = {
            currentValue: currentValue,
            status: status,
            analysis: analysis,
            suggestion: suggestion
          };

          console.log(`${metric} 解析结果:`, report.metricAnalysis[metric]);
        }
      });
    }

    // 解析趋势分析
    const trendMatch = markdownText.match(/## 三、趋势分析与预测\s*\n([^#]+)(?=##|$)/);
    if (trendMatch) {
      let trendText = trendMatch[1].trim();
      trendText = trendText.replace(/\s*---\s*$/, '');
      trendText = trendText.replace(/\s*-\s*-\s*-.*$/, '');
      report.trendAnalysis = trendText;
    } else {
      const altTrendMatch = markdownText.match(/## 三、趋势分析与预测([\s\S]*?)(?=## 四、|$)/);
      if (altTrendMatch) {
        let trendText = altTrendMatch[1].replace(/^[\s\n]*/, '').replace(/[\s\n]*$/, '');
        trendText = trendText.replace(/\s*---\s*$/, '');
        trendText = trendText.replace(/\s*-\s*-\s*-.*$/, '');
        report.trendAnalysis = trendText;
      }
    }

    // 解析综合优化建议
    const suggestionsMatch = markdownText.match(/## 四、综合优化建议\s*\n([^#]+)(?=##|$)/);
    if (suggestionsMatch) {
      const suggestionsText = suggestionsMatch[1];
      const suggestions = suggestionsText.split('\n')
        .filter(line => {
          const trimmed = line.trim();
          return trimmed &&
                 (/[•\-*]/.test(trimmed) ||
                  trimmed.includes('建议') ||
                  trimmed.includes('优化')) &&
                 !trimmed.startsWith('---') &&
                 !/^-\s*-/.test(trimmed) &&
                 !trimmed.includes('报告人') && // 过滤报告人信息
                 !trimmed.includes('网元健康诊断专家系统'); // 过滤系统名称
        })
        .map(line => {
          let content = line.replace(/[•\-*]\s*/, '').trim();
          content = content.replace(/\s*---\s*$/, '');
          return content;
        })
        .filter(content => content.length > 0); // 过滤空内容
      report.comprehensiveSuggestions = suggestions;
    }

    // 解析紧急处理事项
    const urgentMatch = markdownText.match(/## 五、紧急处理事项\s*\n([\s\S]*?)(?=##|$)/);
    if (urgentMatch) {
      const urgentText = urgentMatch[1];
      const urgentItems = urgentText.split('\n')
        .filter(line => {
          const trimmed = line.trim();
          return trimmed &&
                 (/[•\-*]/.test(trimmed) ||
                  trimmed.includes('紧急') ||
                  trimmed.includes('处理') ||
                  trimmed.includes('立即') ||
                  trimmed.includes('尽快') ||
                  trimmed.includes('重要')) &&
                 !trimmed.startsWith('---') &&
                 !/^-\s*-/.test(trimmed) &&
                 !trimmed.includes('报告人') &&
                 !trimmed.includes('网元健康诊断专家系统') &&
                 !trimmed.match(/\*报告人\*\s*:/) &&
                 !trimmed.match(/报告人[：:]/) &&
                 trimmed.length > 2;
        })
        .map(line => {
          let content = line.replace(/[•\-*]\s*/, '').trim();
          content = content.replace(/\s*---\s*$/, '');
          // 进一步清理可能包含的报告人信息
          content = content.replace(/\*报告人\*\s*:[^]*$/, '');
          content = content.replace(/报告人[：:][^]*$/, '');
          content = content.replace(/网元健康诊断专家系统[^]*$/, '');
          return content;
        })
        .filter(content => {
          return content &&
                 !content.includes('报告人') &&
                 !content.includes('网元健康诊断专家系统') &&
                 content.length > 0;
        });
      report.urgentActions = urgentItems;
    }

    // 如果紧急处理事项为空
    if (report.urgentActions.length === 0) {
      const urgentBackupMatch = markdownText.match(/紧急处理事项[^#]*([^#]+)/);
      if (urgentBackupMatch) {
        const backupText = urgentBackupMatch[1];
        const backupItems = backupText.split('\n')
          .filter(line => {
            const trimmed = line.trim();
            return trimmed &&
                   trimmed.length > 10 && // 确保是实际内容
                   !trimmed.includes('报告人') &&
                   !trimmed.includes('网元健康诊断专家系统');
          })
          .map(line => line.trim())
          .filter(line => line.length > 0);

        if (backupItems.length > 0) {
          report.urgentActions = backupItems;
        }
      }
    }

    console.log('最终解析结果:', report);
    return report;
  } catch (error) {
    console.error('解析健康诊断报告错误:', error);
    console.error('错误详情:', error.stack);
    return null;
  }
};

// 格式化分析文本，处理换行和列表
const formatAnalysisText = (text) => {
  if (!text) return '';

  // 清理分隔符
  let cleanedText = text.replace(/\s*---\s*/g, '');
  cleanedText = cleanedText.replace(/^---\s*/, '');
  cleanedText = cleanedText.replace(/\s*---$/, '');
  cleanedText = cleanedText.replace(/-\s*-\s*-/g, '');

  // 将换行符转换为HTML换行
  let formattedText = cleanedText.replace(/\n/g, '<br>');

  // 处理列表项
  formattedText = formattedText.replace(/^- /gm, '• ');
  formattedText = formattedText.replace(/^• /gm, '<span style="color: #0052d9; font-weight: 500;">• </span>');

  // 处理数字列表
  formattedText = formattedText.replace(/^(\d+)\./gm, '<span style="color: #0052d9; font-weight: 500;">$1.</span>');

  // 添加文字颜色
  formattedText = formattedText.replace(/(<br>|^)([^<]*)/g, '$1<span style="color: var(--td-text-color-secondary);">$2</span>');

  return formattedText;
};

// 获取状态对应的标签颜色
const getHealthStatusTag = (status) => {
  if (!status) return 'default';

  if (status.includes('🟢') || status.includes('健康') || status.includes('正常') || status.includes('良好')) {
    return 'success';
  } else if (status.includes('🟡') || status.includes('警告') || status.includes('注意')) {
    return 'warning';
  } else if (status.includes('🔴') || status.includes('危险') || status.includes('严重')) {
    return 'danger';
  }
  return 'default';
};

// 自动计算健康评分
const calculateAutoScore = (markdownText) => {
  let score = 70; // 基础分

  // 根据各个指标状态调整分数
  const metrics = [
    { pattern: /CPU使用率分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } },
    { pattern: /内存使用率分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } },
    { pattern: /磁盘使用率分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } },
    { pattern: /队列使用率分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } },
    { pattern: /SSD健康状态分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } },
    { pattern: /进程内存分析[\s\S]*?\*\*状态\*\*:\s*[🟢🔴🟡]/g, weights: { '🟢': 10, '🟡': -5, '🔴': -20 } }
  ];

  metrics.forEach(metric => {
    const match = markdownText.match(metric.pattern);
    if (match) {
      const statusLine = match[0];
      if (statusLine.includes('🟢')) {
        score += metric.weights['🟢'];
      } else if (statusLine.includes('🟡')) {
        score += metric.weights['🟡'];
      } else if (statusLine.includes('🔴')) {
        score += metric.weights['🔴'];
      }
    }
  });

  // 确保分数在合理范围内
  return Math.max(0, Math.min(100, score));
};

// 获取进度条颜色
const getProgressColor = (score) => {
  if (score >= 80) return 'var(--td-success-color)';
  if (score >= 60) return 'var(--td-warning-color)';
  return 'var(--td-error-color)';
};


// 导出SSD寿命数据
const exportingSsdLife = ref(false);
const exportSsdLifeData = async () => {
  if (!batchAnalysisConfig.value.jumpServerName) {
    MessagePlugin.warning('请先在批量分析配置中选择跳板机');
    batchAnalysisDialogVisible.value = true;
    return;
  }

  try {
    exportingSsdLife.value = true;
    MessagePlugin.info('正在导出SSD寿命数据，请稍候...');

    console.log('开始请求导出SSD寿命数据...');

    // 构建请求参数
    const params = new URLSearchParams({
      jump_server_name: batchAnalysisConfig.value.jumpServerName,
      base_path: 'F:\\'
    });

    // 使用 fetch 获取数据
    const response = await fetch(`${SERVER_API_URL}/exportSsdLifeData?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/gzip,application/octet-stream'
      }
    });

    console.log('响应状态:', response.status);
    console.log('响应头:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 检查响应类型
    const contentType = response.headers.get('content-type');
    console.log('Content-Type:', contentType);

    // 获取blob数据
    const blob = await response.blob();
    console.log('Blob 大小:', blob.size, 'bytes');
    console.log('Blob 类型:', blob.type);

    if (blob.size === 0) {
      throw new Error('下载文件为空');
    }

    // 从响应头获取文件名
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `ssd_life_data_${new Date().toISOString().slice(0,10)}.tar.gz`;

    if (contentDisposition) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
      if (matches && matches[1]) {
        filename = matches[1].replace(/['"]/g, '');
      }
    }

    console.log('下载文件名:', filename);

    // 使用 URL.createObjectURL
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    link.style.display = 'none';

    // 添加到文档并触发点击
    document.body.appendChild(link);

    // 使用 setTimeout
    setTimeout(() => {
      link.click();

      // 清理
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
    }, 0);

    MessagePlugin.success('SSD寿命数据导出成功');

  } catch (error) {
    console.error('导出SSD寿命数据失败:', error);
    MessagePlugin.error(`导出失败: ${error.message}`);
  } finally {
    // 延迟重置状态
    setTimeout(() => {
      exportingSsdLife.value = false;
    }, 2000);
  }
};

</script>



<style scoped>
/* ==================== 基础布局重置 ==================== */
.health-monitor-container {
  width: 100%;
  max-width: 100%;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  background-color: var(--td-bg-color-container);
}

.main-content-area {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

/* ==================== 返回按钮样式 ==================== */
.back-to-chat {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* ==================== 三卡片区域样式 ==================== */
.triple-cards-section {
  width: 100%;
  margin-bottom: 24px;
}

.triple-cards-container {
  width: 100% !important;
  margin: 0 !important;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.triple-cards-container :deep(.t-row) {
  width: 100% !important;
  margin: 0 !important;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.triple-cards-container :deep(.t-col) {
  flex: 1;
  min-width: 0;
  margin: 0 8px;
  margin-bottom: 0;
}

/* 卡片统一样式 */
.online-diagnosis-trigger-card,
.upload-trigger-card,
.batch-analysis-trigger-card {
  height: 100%;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  transition: all 0.3s ease;
  border: 1px solid var(--td-border-level-1-color);
}

.online-diagnosis-trigger-card:hover,
.upload-trigger-card:hover,
.batch-analysis-trigger-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  border-color: var(--td-brand-color-light);
}

/* 卡片内容区域 */
.card-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px 0;
}

.icon-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80px;
  margin-bottom: 16px;
}

.icon-container :deep(svg) {
  width: 48px;
  height: 48px;
}

.description-container {
  text-align: center;
  flex: 1;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-bottom: 20px;
}

.description-container h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--td-text-color-primary);
}

.description-container p {
  margin: 0;
  color: var(--td-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
  padding: 0 8px;
}

.button-container {
  display: flex;
  justify-content: center;
  margin-top: auto;
  padding-top: 16px;
}

.button-container .t-button {
  min-width: 180px;
  height: 44px;
  font-weight: 500;
}

/* 上传按钮特殊样式 */
.upload-button-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-status,
.uploading-indicator {
  width: 100%;
  text-align: center;
}

/* ==================== 批量分析结果区域 ==================== */
.batch-results-section {
  width: 100%;
  margin-top: 24px;
  margin-bottom: 24px;
}

.batch-results-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.batch-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--td-border-level-1-color);
}

.results-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.results-actions {
  display: flex;
  align-items: center;
}

.batch-results-actions {
  padding-top: 16px;
  border-top: 1px solid var(--td-border-level-1-color);
}

/* ==================== 详细报告弹窗样式 ==================== */
.detailed-report-container {
  padding: 20px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.ne-info-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.detailed-charts-container,
.detailed-data-table,
.detailed-diagnosis-report-container,
.raw-analysis-result {
  margin-bottom: 24px;
}

.detailed-charts-card,
.detailed-diagnosis-report-card {
  border-radius: 12px;
  overflow: hidden;
}

/* ==================== 通用卡片样式 ==================== */
.full-width-card {
  width: 100%;
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--td-border-level-1-color);
}

/* ==================== 在线诊断卡片样式 ==================== */
.online-diagnosis-card {
  margin-bottom: 24px;
}

.diagnosis-status {
  margin-bottom: 16px;
}

.combined-info-card {
  margin-bottom: 20px;
}

.sub-table-card {
  margin-bottom: 16px;
}

/* ==================== 图表区域样式 ==================== */
.charts-container {
  margin-bottom: 24px;
}

.charts-card {
  margin-bottom: 24px;
}

.chart-wrapper {
  width: 100%;
  min-height: 300px;
  position: relative;
}

.metric-card {
  height: 100%;
}

.process-mem-card {
  margin-top: 20px;
}

/* ==================== 表格区域样式 ==================== */
.data-table-container,
.diagnosis-report-container {
  margin-bottom: 24px;
}

/* ==================== 诊断报告样式 ==================== */
.report-generating {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.report-content {
  width: 100%;
}

.overall-assessment-card {
  margin-bottom: 24px;
}

.assessment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.health-status-tag {
  margin-left: 16px;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 24px;
  justify-content: center;
  padding: 16px 0;
}

.score-info {
  flex: 1;
  max-width: 400px;
}

.score-info h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--td-text-color-primary);
}

.score-info p {
  margin: 0;
  color: var(--td-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

/* 详细指标分析 */
.metric-analysis-card {
  margin-bottom: 24px;
}

.metric-item {
  padding: 20px;
  border: 1px solid var(--td-border-level-2-color);
  border-radius: 8px;
  background: var(--td-bg-color-container);
  margin-bottom: 16px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.metric-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-title-section h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.status-tag {
  font-size: 12px;
}

.metric-details {
  padding-left: 28px;
}

.metric-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.info-item {
  background: var(--td-bg-color-container-hover);
  border-radius: 6px;
  padding: 12px;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--td-text-color-secondary);
  font-size: 14px;
  font-weight: 500;
}

.info-label :deep(svg) {
  color: var(--td-brand-color);
}

.info-content {
  color: var(--td-text-color-primary);
  font-size: 14px;
  line-height: 1.5;
}

/* 趋势分析卡片 */
.trend-analysis-card {
  margin-bottom: 24px;
}

.trend-content {
  padding: 16px;
  color: var(--td-text-color-primary);
  font-size: 14px;
  line-height: 1.6;
}

/* 建议卡片 */
.suggestions-card {
  margin-bottom: 24px;
}

.suggestion-item {
  margin-bottom: 8px;
}

/* 紧急处理事项 */
.urgent-actions-card {
  border-color: var(--td-error-color-light);
  background: linear-gradient(135deg, var(--td-error-color-light) 0%, var(--td-bg-color-container) 50%);
}

.urgent-action-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-error-color-light);
  border-radius: 8px;
  margin-bottom: 8px;
}

.urgent-marker {
  color: var(--td-error-color);
  flex-shrink: 0;
  margin-top: 2px;
}

.urgent-content {
  color: var(--td-text-color-primary);
  font-size: 14px;
  line-height: 1.5;
  flex: 1;
}

/* ==================== 空状态样式 ==================== */
.empty-data {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
  text-align: center;
  color: var(--td-text-color-placeholder);
}

.empty-data :deep(svg) {
  margin-bottom: 16px;
  opacity: 0.6;
}

/* ==================== 错误和提示卡片 ==================== */
.error-card,
.empty-card {
  margin: 20px 0;
  text-align: center;
  padding: 40px 20px;
}

.error-card h4,
.empty-card h4 {
  margin: 0 0 12px 0;
  color: var(--td-text-color-primary);
}

.error-card p,
.empty-card p {
  margin: 0 0 16px 0;
  color: var(--td-text-color-secondary);
}

.error-card ul {
  text-align: left;
  display: inline-block;
  margin: 16px 0;
  color: var(--td-text-color-secondary);
}

/* ==================== 弹窗样式 ==================== */
/* AI聊天对话框 */
.ai-chat-box {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.ai-chat-select {
  display: flex;
  align-items: center;
  margin-right: 8px;
}

.ai-chat-select :deep(.t-select) {
  width: 140px;
}

.ai-chat-new {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
}

/* 在线诊断配置 */
.online-diagnosis-config {
  padding: 20px;
}

.config-item {
  margin-bottom: 24px;
}

.diagnosis-status-message {
  margin: 16px 0;
}

.diagnosis-actions {
  margin-top: 24px;
}

/* 批量分析配置弹窗 */
.batch-analysis-config {
  padding: 20px;
}

.config-card,
.status-card {
  margin-bottom: 20px;
}

.date-info {
  padding: 12px;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 8px;
  margin-bottom: 16px;
}

.date-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.date-item.today {
  color: var(--td-success-color);
  font-weight: 500;
}

.progress-section {
  padding: 16px;
  background: var(--td-bg-color-container);
  border-radius: 8px;
  border: 1px solid var(--td-border-level-1-color);
  margin-top: 16px;
}

.progress-text {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  margin-top: 8px;
  color: var(--td-brand-color);
}

.batch-analysis-actions {
  padding-top: 20px;
  border-top: 1px solid var(--td-border-level-1-color);
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .triple-cards-container :deep(.t-row) {
    flex-wrap: wrap;
  }

  .triple-cards-container :deep(.t-col) {
    flex: 0 0 calc(50% - 16px);
    margin-bottom: 16px;
  }

  .metric-info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 992px) {
  .health-monitor-container {
    padding: 16px;
  }

  .triple-cards-container :deep(.t-col) {
    margin: 0 0 16px 0;
    flex: 0 0 100%;
  }

  .score-section {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .score-info {
    max-width: 100%;
  }

  .batch-results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .results-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .health-monitor-container {
    padding: 12px;
  }

  .triple-cards-section {
    margin-bottom: 16px;
  }

  .batch-results-section {
    margin-top: 16px;
    margin-bottom: 16px;
  }

  .full-width-card {
    margin-bottom: 16px;
  }

  .card-content-wrapper {
    padding: 4px 0;
  }

  .description-container h3 {
    font-size: 16px;
  }

  .description-container p {
    font-size: 13px;
  }

  .button-container .t-button {
    min-width: 160px;
    height: 40px;
    font-size: 14px;
  }

  .metric-item {
    padding: 16px;
  }

  .metric-info-grid {
    gap: 12px;
  }

  .assessment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .health-status-tag {
    margin-left: 0;
  }

  .back-to-chat {
    top: 12px;
    left: 12px;
  }
}

@media (max-width: 576px) {
  .triple-cards-container :deep(.t-card__body) {
    padding: 16px !important;
  }

  .online-diagnosis-trigger-card,
  .upload-trigger-card,
  .batch-analysis-trigger-card {
    min-height: 240px;
  }

  .icon-container {
    height: 60px;
    margin-bottom: 12px;
  }

  .icon-container :deep(svg) {
    width: 40px;
    height: 40px;
  }

  .description-container {
    min-height: 70px;
    margin-bottom: 16px;
  }

  .button-container {
    padding-top: 12px;
  }

  .detailed-report-container {
    padding: 16px;
    height: calc(100vh - 100px);
  }
}

/* ==================== 动画效果 ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* ==================== 滚动条样式 ==================== */
.detailed-report-container::-webkit-scrollbar,
.batch-results-card :deep(.t-table__body)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.detailed-report-container::-webkit-scrollbar-track,
.batch-results-card :deep(.t-table__body)::-webkit-scrollbar-track {
  background: var(--td-bg-color-container-hover);
  border-radius: 3px;
}

.detailed-report-container::-webkit-scrollbar-thumb,
.batch-results-card :deep(.t-table__body)::-webkit-scrollbar-thumb {
  background: var(--td-border-level-2-color);
  border-radius: 3px;
}

.detailed-report-container::-webkit-scrollbar-thumb:hover,
.batch-results-card :deep(.t-table__body)::-webkit-scrollbar-thumb:hover {
  background: var(--td-brand-color);
}

/* ==================== 辅助类 ==================== */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-column {
  display: flex;
  flex-direction: column;
}

.mb-16 {
  margin-bottom: 16px;
}

.mb-24 {
  margin-bottom: 24px;
}

.mt-16 {
  margin-top: 16px;
}

.mt-24 {
  margin-top: 24px;
}

.p-16 {
  padding: 16px;
}

.p-24 {
  padding: 24px;
}

/* 文件统计样式 */
.file-statistics {
  padding: 12px;
  background: var(--td-bg-color-container);
  border-radius: 8px;
  border: 1px solid var(--td-border-level-1-color);
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--td-border-level-2-color);
}

.stat-item:last-child {
  border-bottom: none;
}

/* 日期分布样式 */
.date-distribution {
  padding: 12px;
  background: var(--td-bg-color-container-hover);
  border-radius: 8px;
  border: 1px solid var(--td-border-level-1-color);
  margin-top: 12px;
}

.date-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.date-item:first-child {
  padding-top: 0;
}

.date-item:last-child {
  padding-bottom: 0;
}

/* 得分规则弹窗样式 */
.score-rules-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 4px;
}

.score-rules-content :deep(.t-tabs) {
  height: 100%;
}

.score-rules-content :deep(.t-tabs__content) {
  padding: 0;
}

.rule-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.rule-card:last-child {
  margin-bottom: 0;
}

/* 滚动条样式 */
.score-rules-content::-webkit-scrollbar,
.score-rules-content :deep(.t-tabs__content)::-webkit-scrollbar {
  width: 6px;
}

.score-rules-content::-webkit-scrollbar-track,
.score-rules-content :deep(.t-tabs__content)::-webkit-scrollbar-track {
  background: var(--td-bg-color-container-hover);
  border-radius: 3px;
}

.score-rules-content::-webkit-scrollbar-thumb,
.score-rules-content :deep(.t-tabs__content)::-webkit-scrollbar-thumb {
  background: var(--td-border-level-2-color);
  border-radius: 3px;
}

.score-rules-content::-webkit-scrollbar-thumb:hover,
.score-rules-content :deep(.t-tabs__content)::-webkit-scrollbar-thumb:hover {
  background: var(--td-brand-color);
}
</style>
