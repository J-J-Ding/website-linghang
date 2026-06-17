import Layout from '@/layouts/index.vue';

export default [
  {
    path: '/ai',
    name: 'ai',
    component: Layout,
    redirect: '/ai/chat',
    meta: {
      title: {
        zh_CN: '智能助手',
        en_US: 'AI',
      },
      icon: 'logo-adobe-illustrate',
    },
    children: [
      {
        path: 'chat',
        name: 'AiChat',
        component: () => import('@/pages/ai/chat/index.vue'),
        meta: { title: { zh_CN: 'AI助手', en_US: 'Chat' } },
      },
      // {
      //   path: 'spuerchat',
      //   name: 'spuerchat',
      //   component: () => import('@/pages/ai/chat/superchat.vue'),
      //   meta: { title: { zh_CN: '超级AI助手', en_US: 'spuerchat' } },
      // },
      {
        path: 'boardChat',
        name: 'AiBoardChat',
        component: () => import('@/pages/ai/boardChat/index.vue'),
        meta: { title: { zh_CN: '单板助手', en_US: 'boardChat' } },
      },
      {
        path: 'boardChat/BoardChatTable',
        name: 'AIBoardChatTable',
        component: () => import('@/pages/ai/boardChat/BoardChatTable.vue'),
        meta: { title: { zh_CN: '单板助手手看板', en_US: 'BoardChatTable' }, hidden: true },
      },
      {
        path: 'diag',
        name: 'AiDiag',
        component: () => import('@/pages/ai/diag/index.vue'),
        meta: { title: { zh_CN: '智能诊断助手', en_US: 'diag' } },
      },
      {
        path: 'diag/diagSceneBoard',
        name: 'AiDiagSceneBoard',
        component: () => import('@/pages/ai/diag/scene.vue'),
        meta: { title: { zh_CN: '语料新增', en_US: 'diagSceneBoard' }, hidden: true },
      },
      {
        path: 'diag/diagTable',
        name: 'AiDiagTable',
        component: () => import('@/pages/ai/diag/diagtable.vue'),
        meta: { title: { zh_CN: '故障度量衡', en_US: 'diagTable' }, hidden: true },
      },
      {
        path: 'code/genCode',
        name: 'AiGenCode',
        component: () => import('@/pages/ai/genCode/index.vue'),
        meta: { title: { zh_CN: '代码生成助手', en_US: 'genCode' } },
      },
      {
        path: 'testAssistant',
        name: 'testAssistant',
        component: () => import('@/pages/ai/knowledgeRepo/testcase.vue'),
        meta: { title: { zh_CN: '功能测试助手', en_US: 'testAssistant' } },
      },
      {
        path: 'code/genCodeTable',
        name: 'AiGenCodeTable',
        component: () => import('@/pages/ai/genCode/board.vue'),
        meta: { title: { zh_CN: '代码生成度量衡', en_US: 'GenCodeTable' }, hidden: true },
      },
      {
        path: 'issueProcess',
        name: 'issueProcess',
        component: () => import('@/pages/ai/knowledgeRepo/issue.vue'),
        meta: { title: { zh_CN: '故障处理助手', en_US: 'issueProcess' } },
      },
      {
        path: 'issueImpacte',
        name: 'issueImpacte',
        component: () => import('@/layouts/blank.vue'),
        redirect: '/ai/issueImpacte/caseList',
        meta: { title: { zh_CN: '故障波及助手', en_US: 'issueImpacte' } },
        children: [
          {
            path: 'caseList',
            name: 'issueImpacteCaseList',
            component: () => import('@/pages/ai/issueImpacte/caseList.vue'),
            meta: { title: { zh_CN: '案例库', en_US: 'Case List' } },
          },
          {
            path: 'version',
            name: 'issueImpacteVersion',
            component: () => import('@/pages/ai/issueImpacte/version.vue'),
            meta: { title: { zh_CN: '版本库', en_US: 'Version List' } },
          },
          {
            path: 'version/:versionId/cases',
            name: 'issueImpacteVersionCases',
            component: () => import('@/pages/ai/issueImpacte/versionCases.vue'),
            meta: { title: { zh_CN: '版本案例清单', en_US: 'Version Cases' }, hidden: true },
          },
        ],
      },
      {
        path: 'requirementScheduleAssistant',
        name: 'requirementScheduleAssistant',
        component: () => import('@/layouts/blank.vue'),
        redirect: '/ai/requirementScheduleAssistant/requirementView/requirementList',
        meta: { title: { zh_CN: '需求排期助手', en_US: 'RequirementScheduleAssistant' } },
        children: [
          {
            path: 'requirementView',
            name: 'requirementView',
            meta: { title: { zh_CN: '需求视图', en_US: 'RequirementView' } },
            children: [
              {
                path: 'requirementList',
                name: 'requirementList',
                meta: { title: { zh_CN: '需求清单', en_US: 'RequirementList' } },
                component: () => import('@/pages/ai/requireSchedule/requirementList.vue'),
              },
            ],
          },
          {
            path: 'humanResourceView',
            name: 'humanResourceView',
            meta: { title: { zh_CN: '人力视图', en_US: 'HumanResourceView' } },
            children: [
              {
                path: 'personSkillMap',
                name: 'personSkillMap',
                meta: { title: { zh_CN: '01 人员技能地图', en_US: 'PersonSkillMap' } },
                component: () => import('@/pages/ai/personSkillMap/personSkillMap.vue'),
              },
              {
                path: 'humanResourceSetting',
                name: 'humanResourceSetting',
                meta: { title: { zh_CN: '02 需求交付人力投入', en_US: 'HumanResourceSetting' } },
                component: () => import('@/pages/ai/humanResourceSetting/humanResourceSetting.vue'),
              },
              {
                path: 'humanResourcePivot',
                name: 'humanResourcePivot',
                meta: { title: { zh_CN: '03 人力透视表', en_US: 'HumanResourcePivot' } },
                component: () => import('@/pages/ai/humanResourcePivot/humanResourcePivot.vue'),
              },
              {
                path: 'availableHumanResource',
                name: 'availableHumanResource',
                meta: { title: { zh_CN: '04 需求交付可用人力', en_US: 'AvailableHumanResource' } },
                component: () => import('@/pages/ai/availableHumanResource/availableHumanResource.vue'),
              },
            ],
          },
          {
            path: 'versionView',
            name: 'versionView',
            meta: { title: { zh_CN: '版本视图', en_US: 'VersionView' } },
            children: [
              {
                path: 'versionList',
                name: 'versionList',
                meta: { title: { zh_CN: '版本清单', en_US: 'VersionList' } },
                component: () => import('@/pages/ai/versionTable/versionList.vue'),
              },
            ],
          },
          {
            path: 'featureView',
            name: 'featureView',
            meta: { title: { zh_CN: '特性视图', en_US: 'FeatureView' } },
            children: [
              {
                path: 'featureList',
                name: 'featureList',
                meta: { title: { zh_CN: '特性清单', en_US: 'FeatureList' } },
                component: () => import('@/pages/ai/featureView/featureView.vue'),
              },
            ],
          },
        ],
      },
      {
        path: 'boardAssembly',
        name: 'boardAssembly',
        component: () => import('@/pages/ai/boardAssembly/board.vue'),
        meta: { title: { zh_CN: '单板组装助手', en_US: 'boardAssembly' } },
      },
      {
        path: 'componentDesignAgent',
        name: 'componentDesignAgent',
        component: () => import('@/pages/ai/agent/componentDesignAgent.vue'),
        meta: { title: { zh_CN: '组件功能设计助手', en_US: 'componentDesignAgent' } },
      },
      {
        path: 'design-knowledge',
        name: 'DesignKnowledgeBase',
        component: () => import('@/pages/ai/agent/DesignKnowledgeBase.vue'),
        meta: { title: { zh_CN: '组件设计知识库', en_US: 'Design Knowledge Base' }, hidden: true },
      },
      {
        path: 'metrics-system',
        name: 'MetricsSystem',
        component: () => import('@/pages/ai/agent/MetricsSystem.vue'),
        meta: { title: { zh_CN: '度量系统', en_US: 'Metrics System' }, hidden: true },
      },
      {
        path: 'design-tracking',
        name: 'DesignTracking',
        component: () => import('@/pages/ai/agent/DesignTracking.vue'),
        meta: { title: { zh_CN: '详细设计跟踪', en_US: 'Design Tracking' }, hidden: true },
      },
      {
        path: 'healthAssistant',
        name: 'healthAssistant',
        component: () => import('@/pages/ai/healthAssistant/health.vue'),
        meta: { title: { zh_CN: '网元健康助手', en_US: 'healthAssistant' } },
      },
      {
        path: 'apoInspectionAssistant',
        name: 'apoInspectionAssistant',
        component: () => import('@/pages/ai/apoInspection/index.vue'),
        meta: { title: { zh_CN: 'APO巡检助手', en_US: 'apoInspectionAssistant' } },
      },
      // {
      //   path: 'layout',
      //   name: 'AiLayout',
      //   component: () => import('@/pages/ai/layout/index.vue'),
      //   meta: { title: { zh_CN: '界面测试', en_US: 'Layout' } },
      // },
    ],
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: Layout,
    redirect: '/knowledge/develop',
    meta: {
      title: {
        zh_CN: '知识体系',
        en_US: 'Knowledge',
      },
      icon: 'book-open',
    },
    children: [
      // {
      //   path: 'knowledge',
      //   name: 'AiKnowledge',
      //   component: () => import('@/pages/ai/knowledge/index.vue'),
      //   meta: { title: { zh_CN: '知识全景', en_US: 'Knowledge' } },
      // },
      {
        path: 'scene',
        name: 'scene',
        component: () => import('@/pages/ai/knowledgeTree/scene.vue'),
        meta: { title: { zh_CN: '场景树', en_US: 'scene' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'feature',
        name: 'feature',
        component: () => import('@/pages/ai/knowledgeTree/feature.vue'),
        meta: { title: { zh_CN: '特性树', en_US: 'feature' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'component',
        name: 'component',
        component: () => import('@/pages/ai/knowledgeTree/component.vue'),
        meta: { title: { zh_CN: '组件树', en_US: 'component' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'boardmax',
        name: 'boardmax',
        component: () => import('@/pages/ai/knowledgeTree/board.vue'),
        meta: { title: { zh_CN: '单板树', en_US: 'board' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'device',
        name: 'device',
        meta: { title: { zh_CN: '硬件树', en_US: 'device' }, icon: 'tree-round-dot-vertical-filled' },
        children: [
          // {
          //   path: 'boardpro',
          //   name: 'boardpro',
          //   component: () => import('@/pages/ai/device/boardpro.vue'),
          //   meta: { title: { zh_CN: '单板库', en_US: 'boardpro' } },
          // },
          {
            path: 'sd',
            name: 'sd',
            component: () => import('@/pages/ai/device/sd.vue'),
            meta: { title: { zh_CN: 'SD库', en_US: 'sd' } },
          },
          {
            path: 'phy',
            name: 'phy',
            component: () => import('@/pages/ai/device/phy.vue'),
            meta: { title: { zh_CN: 'PHY库', en_US: 'phy' } },
          },
          {
            path: 'cpu',
            name: 'cpu',
            component: () => import('@/pages/ai/device/cpu.vue'),
            meta: { title: { zh_CN: 'CPU库', en_US: 'cpu' } },
          },

          {
            path: 'switch',
            name: 'switch',
            component: () => import('@/pages/ai/device/switch.vue'),
            meta: { title: { zh_CN: '交换芯片库', en_US: 'switch' } },
          },
          {
            path: 'clock',
            name: 'clock',
            component: () => import('@/pages/ai/device/clock.vue'),
            meta: { title: { zh_CN: '时钟芯片库', en_US: 'clock' } },
          },
          {
            path: 'module',
            name: 'module',
            component: () => import('@/pages/ai/device/module.vue'),
            meta: { title: { zh_CN: '光模块库', en_US: 'module' } },
          },
          {
            path: 'fpgaaddr',
            name: 'fpgaaddr',
            component: () => import('@/pages/ai/device/fpgaaddr.vue'),
            meta: { title: { zh_CN: 'FPGA地址库', en_US: 'fpgaaddr' } },
          },
          {
            path: 'eeprom',
            name: 'eeprom',
            component: () => import('@/pages/ai/device/eeprom.vue'),
            meta: { title: { zh_CN: 'EEPROM库', en_US: 'eeprom' } },
          },
        ],
      },
      {
        path: 'generalKnowledge',
        name: 'generalKnowledge',
        meta: { title: { zh_CN: '通用知识管理', en_US: 'GeneralKnowledge' }, icon: 'sitemap-filled' },
        children: [
          {
            path: 'requirement',
            name: 'requirement',
            component: () => import('@/pages/ai/knowledgeRepo/requirement.vue'),
            meta: { title: { zh_CN: '需求库', en_US: 'requirement' } },
          },
          {
            path: 'issue',
            name: 'issue',
            component: () => import('@/pages/ai/knowledgeRepo/issue.vue'),
            meta: { title: { zh_CN: '故障库', en_US: 'issue' } },
          },
          {
            path: 'testcase',
            name: 'testcase',
            component: () => import('@/pages/ai/knowledgeRepo/testcase.vue'),
            meta: { title: { zh_CN: '用例库', en_US: 'testcase' } },
          },
          {
            path: 'ft_testcase',
            name: 'ft_testcase',
            component: () => import('@/pages/ai/knowledgeRepo/ft_testcase.vue'),
            meta: { title: { zh_CN: 'FT用例库', en_US: 'ft_testcase' } },
          },
          {
            path: 'repo',
            name: 'repo',
            component: () => import('@/pages/ai/knowledgeRepo/repo.vue'),
            meta: { title: { zh_CN: '代码库', en_US: 'repo' } },
          },
          {
            path: 'api',
            name: 'api',
            component: () => import('@/pages/ai/knowledgeRepo/api.vue'),
            meta: { title: { zh_CN: '命令库', en_US: 'api' } },
          },
          {
            path: 'branch',
            name: 'branch',
            component: () => import('@/pages/ai/knowledgeRepo/branch.vue'),
            meta: { title: { zh_CN: '分支库', en_US: 'branch' } },
          },
          {
            path: 'version',
            name: 'version',
            component: () => import('@/pages/ai/knowledgeRepo/version.vue'),
            meta: { title: { zh_CN: '版本库', en_US: 'version' } },
          },
          {
            path: 'general_ai_application',
            name: 'general_ai_application',
            component: () => import('@/pages/ai/generalApplication/general_ai_application.vue'),
            meta: { title: { zh_CN: 'AI应用库', en_US: 'general ai application' } },
          },
          {
            path: 'pe',
            name: 'pe',
            component: () => import('@/pages/ai/knowledgeRepo/pe.vue'),
            meta: { title: { zh_CN: 'PE模版库', en_US: 'pe' } },
          },
          {
            path: 'upgrade_before',
            name: 'upgrade_before',
            component: () => import('@/pages/ai/knowledgeRepo/upgrade_before.vue'),
            meta: { title: { zh_CN: '升级前巡检库', en_US: 'upgrade_before' } },
          },
          {
            path: 'leakage_branch',
            name: 'leakage_branch',
            component: () => import('@/pages/ai/knowledgeRepo/leakage_branch.vue'),
            meta: { title: { zh_CN: '分支漏合库', en_US: 'leakage_branch' } },
          },
          {
            path: 'device_check',
            name: 'device_check',
            component: () => import('@/pages/ai/knowledgeRepo/device_check.vue'),
            meta: { title: { zh_CN: '硬件通用库', en_US: 'device_check' } },
          },
          {
            path: 'board_temperature_check',
            name: 'board_temperature_check',
            component: () => import('@/pages/ai/knowledgeRepo/board_temperature_check.vue'),
            meta: { title: { zh_CN: '单板温度检测库', en_US: 'board_temperature_check' } },
          },
        ],
      },
      {
        path: 'electricKnowledgeManage',
        name: 'electricKnowledgeManage',
        meta: { title: { zh_CN: '电层知识管理', en_US: 'ElectricKnowledgeManage' }, icon: 'sitemap-filled' },
        children: [
          {
            path: 'electricBusiness',
            name: 'electricBusiness',
            meta: { title: { zh_CN: '业务模型', en_US: 'ElectricBusiness' } },
            children: [
              {
                path: 'businessType',
                name: 'businessType',
                meta: { title: { zh_CN: '光口业务速率&业务类型', en_US: 'BusinessType' } },
                component: () => import('@/pages/ai/electricBusiness/businessType.vue'),
              },
              {
                path: 'boardBusiness',
                name: 'boardBusiness',
                meta: { title: { zh_CN: '单板业务模型', en_US: 'BoardBusiness' } },
                component: () => import('@/pages/ai/electricBusiness/boardBusiness.vue'),
              },
              {
                path: 'netBusiness',
                name: 'netBusiness',
                meta: { title: { zh_CN: '网元业务模型', en_US: 'NetBusiness' } },
                component: () => import('@/pages/ai/electricBusiness/netBusiness.vue'),
              },
            ],
          },
          {
            path: 'electricElement',
            name: 'electricElement',
            meta: { title: { zh_CN: '要素因子', en_US: 'ElectricElement' } },
            children: [
              {
                path: 'business',
                name: 'business',
                meta: { title: { zh_CN: '业务要素因子', en_US: 'Business' } },
                component: () => import('@/pages/ai/electricElement/business.vue'),
              },
              {
                path: 'board',
                name: 'board',
                meta: { title: { zh_CN: '单板要素因子', en_US: 'Board' } },
                component: () => import('@/pages/ai/electricElement/board.vue'),
              },
              {
                path: 'shelf',
                name: 'shelf',
                meta: { title: { zh_CN: '子架要素因子', en_US: 'Shelf' } },
                component: () => import('@/pages/ai/electricElement/shelf.vue'),
              },
            ],
          },
          {
            path: 'electricFeature',
            name: 'electricFeature',
            meta: { title: { zh_CN: '特性树', en_US: 'ElectricFeature' } },
            children: [
              {
                path: 'featureTree',
                name: 'featureTree',
                meta: { title: { zh_CN: '特性&子特性', en_US: 'FeatureTree' } },
                component: () => import('@/pages/ai/electricFeature/featureTree.vue'),
              },
              {
                path: 'featureBoard',
                name: 'featureBoard',
                meta: { title: { zh_CN: '特性&单板', en_US: 'FeatureBoard' } },
                component: () => import('@/pages/ai/electricFeature/featureBoard.vue'),
              },
            ],
          },
          {
            path: 'electricHardware',
            name: 'electricHardware',
            meta: { title: { zh_CN: '硬件树', en_US: 'ElectricHardware' } },
            children: [
              {
                path: 'boardTree',
                name: 'boardTree',
                meta: { title: { zh_CN: '单板树', en_US: 'BoardTree' } },
                component: () => import('@/pages/ai/electricHardware/boardTree.vue'),
              },
              {
                path: 'boardPartTree',
                name: 'boardPartTree',
                meta: { title: { zh_CN: '单板部件树', en_US: 'BoardPartTree' } },
                component: () => import('@/pages/ai/electricHardware/boardPartTree.vue'),
              },
              {
                path: 'shelfTree',
                name: 'shelfTree',
                meta: { title: { zh_CN: '子架树', en_US: 'ShelfTree' } },
                component: () => import('@/pages/ai/electricHardware/shelfTree.vue'),
              },
              {
                path: 'shelfPartTree',
                name: 'shelfPartTree',
                meta: { title: { zh_CN: '子架部件树', en_US: 'ShelfPartTree' } },
                component: () => import('@/pages/ai/electricHardware/shelfPartTree.vue'),
              },
            ],
          },
          {
            path: 'boardGlobalStatus',
            name: 'boardGlobalStatus',
            meta: { title: { zh_CN: '单板全局状态', en_US: 'BoardGlobalStatus' } },
            component: () => import('@/pages/ai/electricHardware/boardGlobalStatus.vue'),
          },
          {
            path: 'manualReview',
            name: 'manualReview',
            meta: { title: { zh_CN: '人工审核', en_US: 'ManualReview' } },
            component: () => import('@/pages/ai/manualReview/manualreview.vue'),
          },
        ],
      },

      // {
      //   path: 'summary',
      //   name: 'AiSummary',
      //   component: () => import('@/pages/ai/summary/index.vue'),
      //   meta: { title: { zh_CN: '汇总表', en_US: 'summary' } },
      // },
    ],
  },
  {
    path: '/engineering',
    name: 'engineering',
    component: Layout,
    redirect: '/engineering/tree',
    meta: {
      title: {
        zh_CN: '知识工程',
        en_US: 'Engineering',
      },
      icon: 'book-open',
    },
    children: [
      {
        path: 'scene',
        name: 'scene',
        component: () => import('@/pages/ai/knowledgeTree/scene.vue'),
        meta: { title: { zh_CN: '场景树', en_US: 'scene' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'feature',
        name: 'feature',
        component: () => import('@/pages/ai/knowledgeTree/feature.vue'),
        meta: { title: { zh_CN: '特性树', en_US: 'feature' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'component',
        name: 'component',
        component: () => import('@/pages/ai/knowledgeTree/component.vue'),
        meta: { title: { zh_CN: '组件树', en_US: 'component' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'requirements',
        name: 'requirements',
        component: () => import('@/pages/ai/knowledgeTree/requirements.vue'),
        meta: { title: { zh_CN: '需求树', en_US: 'requirements' }, icon: 'tree-round-dot-vertical-filled' },
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/pages/dashboard/compTreeBoard/index.vue'),
        meta: { title: { zh_CN: '知识看板', en_US: 'dashboard' }, icon: 'tree-round-dot-vertical-filled' },
        // children: [
        //   {
        //     path: 'comp',
        //     name: 'Comp',
        //     meta: { title: { zh_CN: '组件树建设', en_US: 'Component Tree Construction' } },
        //     component: () => import('@/pages/dashboard/compTreeBoard/index.vue'),
        //   },
        // ],
      },
      {
        path: 'feature_new',
        name: 'feature_new',
        component: () => import('@/pages/ai/knowledgeTree/feature_new.vue'),
        meta: { title: { zh_CN: '特性树', en_US: 'feature_new' }, icon: 'tree-round-dot-vertical-filled' },
      },
    ],
  },
];
