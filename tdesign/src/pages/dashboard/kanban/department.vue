<template>
  <div class="dashboard-container">
    <!-- 顶部仪表板 -->
    <div class="top-section">
      <div class="dashboard-panel">
        <!-- 左侧圆形仪表 - 交付健康度 -->
        <div class="gauge-panel left-gauge">
          <div class="gauge-title">交付健康度</div>
          <div class="gauge-container">
            <t-progress :percentage="85" theme="circle" :stroke-width="10" />
          </div>
        </div>

        <!-- 中间关键信息 -->
        <div class="info-panel">
          <div class="info-row main-title">波分软件开发一部</div>
          <div class="info-row">研发人数147人，3个领域，16个团队</div>
          <div class="info-row">智能OTN，M721，7000</div>
          <div class="info-row slogan">用代码书写尊严</div>
        </div>

        <!-- 右侧圆形仪表 - 质量健康度 -->
        <div class="gauge-panel right-gauge">
          <div class="gauge-title">质量健康度</div>
          <div class="gauge-container">
            <t-progress :percentage="92" theme="circle" :stroke-width="10" color="#00a870" />
          </div>
        </div>
      </div>
    </div>

    <!-- 中间看板 -->
    <div class="middle-section">
      <div class="board-container">
        <!-- 交付情况 -->
        <div class="board-panel delivery-board">
          <div class="board-header">
            <h3>交付情况</h3>
          </div>
          <div class="board-content">
            <div class="stats-panel">
              <div class="stat-item">
                <div class="stat-label">项目数：</div>
                <div class="stat-value">42</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">正常数：</div>
                <div class="stat-value">36</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">异常数：</div>
                <div class="stat-value">6</div>
              </div>
            </div>
            <div class="issues-panel">
              <t-table
                :data="deliveryIssues"
                :columns="issueColumns"
                size="small"
                row-key="index"
                :header-affixed-top="true"
                vertical-align="top"
              />
            </div>
          </div>
        </div>

        <!-- 质量情况 -->
        <div class="board-panel quality-board">
          <div class="board-header">
            <h3>质量情况</h3>
          </div>
          <div class="board-content">
            <div class="stats-panel">
              <div class="stat-item">
                <div class="stat-label">外场故障数：</div>
                <div class="stat-value">3</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">内场故障数：</div>
                <div class="stat-value">12</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">待解决故障数：</div>
                <div class="stat-value">5</div>
              </div>
            </div>
            <div class="issues-panel">
              <t-table
                :data="qualityIssues"
                :columns="issueColumns"
                size="small"
                row-key="index"
                :header-affixed-top="true"
                vertical-align="top"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部选项卡 -->
    <div class="bottom-section">
      <t-tabs v-model="activeTab" class="tab-container">
        <t-tab-panel value="delivery" label="交付">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">交付模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
        <t-tab-panel value="quality" label="质量">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">质量模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
        <t-tab-panel value="improvement" label="改进">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">改进模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
        <t-tab-panel value="team" label="团队">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">团队模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
        <t-tab-panel value="personnel" label="人员">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">人员模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
        <t-tab-panel value="compliance" label="合规">
          <div class="tab-content">
            <div class="construction-placeholder">
              <div class="construction-icon">🚧</div>
              <div class="construction-text">合规模块建设中...</div>
            </div>
          </div>
        </t-tab-panel>
      </t-tabs>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DepartmentDashboard',
  data() {
    return {
      activeTab: 'delivery',
      // 交付问题数据
      deliveryIssues: [
        { index: 1, subject: '项目A延期风险', responsible: '张三' },
        { index: 2, subject: '资源分配紧张', responsible: '李四' },
        { index: 3, subject: '需求变更频繁', responsible: '王五' },
        { index: 4, subject: '开发环境不稳定', responsible: '赵六' },
        { index: 5, subject: '开发环境不稳定', responsible: '赵六' },
      ],
      // 质量问题数据
      qualityIssues: [
        { index: 1, subject: '模块X性能问题', responsible: '陈七' },
        { index: 2, subject: '测试覆盖率不足', responsible: '孙八' },
        { index: 3, subject: '代码审查不充分', responsible: '周九' },
        { index: 4, subject: '自动化测试缺失', responsible: '吴十' },
      ],
      // 表格列配置
      issueColumns: [
        {
          title: '序号',
          colKey: 'index',
          width: 60,
          align: 'center',
        },
        {
          title: '关键问题',
          colKey: 'subject',
          width: 200,
        },
        {
          title: '责任人',
          colKey: 'responsible',
          width: 80,
          align: 'center',
        },
      ],
    };
  },
};
</script>

<style scoped>
.dashboard-container {
  height: 160vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 顶部区域 */
.top-section {
  height: 25vh;
  padding: 16px;
}

.dashboard-panel {
  display: flex;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.gauge-panel {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.gauge-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #333;
}

.gauge-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.info-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 20px;
}

.info-row {
  margin: 8px 0;
  font-size: 16px;
  color: #333;
}

.main-title {
  font-size: 24px;
  font-weight: bold;
  color: #0052d9;
}

.slogan {
  font-size: 18px;
  font-weight: 600;
  color: #00a870;
  margin-top: 15px;
}

/* 中间区域 */
.middle-section {
  height: 35vh; /* 增加高度 */
  padding: 0 16px 16px; /* 添加底部间距 */
  min-height: 250px; /* 设置最小高度以确保内容可显示 */
}

.board-container {
  display: flex;
  height: 100%;
  gap: 16px;
}

.board-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.board-header {
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.board-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.board-content {
  flex: 1;
  display: flex;
  padding: 15px;
  min-height: 0; /* 允许flex子项缩小到内容以下 */
}

.stats-panel {
  width: 33.33%;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding-right: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-right: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #0052d9;
}

.issues-panel {
  width: 66.67%;
  padding-left: 15px;
  border-left: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.issues-panel .t-table {
  flex: 1;
  overflow: auto;
  max-height: 100%; /* 移除标题后，表格可使用全部高度 */
}

.issues-panel .t-table__content {
  max-height: 100%;
  overflow: auto;
}

/* 移除了 .issues-title 样式，因为元素已被删除 */

/* 底部区域 */
.bottom-section {
  flex: 1;
  padding: 0 16px 16px;
  min-height: 200px;
}

.tab-container {
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.tab-content {
  height: 100%;
  padding: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.construction-placeholder {
  text-align: center;
  color: #999;
}

.construction-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.construction-text {
  font-size: 18px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .dashboard-panel {
    flex-direction: column;
    height: auto;
  }

  .gauge-panel {
    width: 100%;
    flex-direction: row;
    justify-content: space-around;
    margin: 10px 0;
  }

  .board-container {
    flex-direction: column;
    height: auto;
  }

  .info-panel {
    order: -1;
    padding: 10px 0;
  }

  .info-row {
    margin: 4px 0;
  }

  .board-content {
    flex-direction: column;
  }

  .stats-panel,
  .issues-panel {
    width: 100%;
    padding: 0;
    border-left: none;
  }

  .issues-panel {
    margin-top: 15px;
  }
}
</style>
