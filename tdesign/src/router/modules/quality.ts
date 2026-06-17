import Layout from '@/layouts/index.vue';

export default [
  {
    path: '/quality',
    name: 'quality',
    component: Layout,
    redirect: '/quality/team',
    meta: {
      title: {
        zh_CN: '质量改进',
        en_US: 'Quality Improvement',
      },
      icon: 'secured',
    },
    children: [
      {
        path: 'redline',
        name: 'RedLine',
        component: () => import('@/pages/quality/redline/index.vue'),
        meta: { title: { zh_CN: '质量红线', en_US: 'Red Line' } },
      },
      {
        path: 'demand',
        name: 'demandManagement',
        meta: { title: { zh_CN: '需求度量', en_US: 'logAnalysis' } },
        children: [
          {
            path: 'demandBoard',
            name: 'demandManagement',
            component: () => import('@/pages/ai/demandManagement/demandmanagement.vue'),
            meta: { title: { zh_CN: '需求管理看板', en_US: 'demandManagement' } },
          },
          {
            path: 'requirementForm',
            name: 'requirementDetailTable',
            component: () => import('@/pages/ai/demandManagement/requirementDetailTable.vue'),
            meta: { title: { zh_CN: '需求预检看板', en_US: 'requirementDetailTable' } },
          },
        ]
      },
      {
        path: 'logAnalysis',
        name: 'logAnalysis',
        meta: { title: { zh_CN: '日志分析工具', en_US: 'logAnalysis' } },
        children: [
          {
            path: 'logUpload',
            name: 'logUpload',
            component: () => import('@/pages/ai/logAnalysis/loganalysis.vue'),
            meta: { title: { zh_CN: '日志上传分析', en_US: 'logUpload' } },
          },
          {
            path: 'channelAlarm',
            name: 'channelAlarm',
            component: () => import('@/pages/ai/function/channelalarm.vue'),
            meta: { title: { zh_CN: '通道告警业务查询', en_US: 'channelAlarm' } },
          },
          {
            path: 'businessAnalysis',
            name: 'businessAnalysis',
            component: () => import('@/pages/ai/function/businessanalysis.vue'),
            meta: { title: { zh_CN: '路径上业务历史动作分析', en_US: 'businessAnalysis' } },
          },
          {
            path: 'alarmAnalysis',
            name: 'alarmAnalysis',
            component: () => import('@/pages/ai/function/alarmanalysis.vue'),
            meta: { title: { zh_CN: '通道告警业务分析', en_US: 'alarmAnalysis' } },
          },
          {
            path: 'fiberBreakageAnalysis',
            name: 'fiberBreakageAnalysis',
            component: () => import('@/pages/ai/function/fiberbreakageanalysis.vue'),
            meta: { title: { zh_CN: '断纤告警业务分析', en_US: 'fiberBreakageAnalysis' } },
          },
          {
            path: 'businessRecoveryAnalysis',
            name: 'businessRecoveryAnalysis',
            component: () => import('@/pages/ai/function/businessrecovery.vue'),
            meta: { title: { zh_CN: '业务恢复分析', en_US: 'businessRecoveryAnalysis' } },
          },
          {
            path: 'businessRecoveryDetails',
            name: 'businessRecoveryDetails',
            component: () => import('@/pages/ai/function/businessrecoverydetails.vue'),
            meta: { title: { zh_CN: '业务恢复详情', en_US: 'businessRecoveryDetails' } },
          },
          {
            path: 'businessActionFlow',
            name: 'businessActionFlow',
            component: () => import('@/pages/ai/function/businessactionflow.vue'),
            meta: { title: { zh_CN: '日志分析业务动作流', en_US: 'businessActionFlow' } },
          },
        ],
      },
      // {
      //   path: 'review',
      //   name: 'QualityReview',
      //   component: () => import('@/pages/quality/review/index.vue'),
      //   meta: { title: { zh_CN: '故障复盘', en_US: 'Quality Review' } },
      // },
      // {
      //   path: 'version',
      //   name: 'QualityVersion',
      //   component: () => import('@/pages/quality/version/index.vue'),
      //   meta: { title: { zh_CN: '在研版本', en_US: 'Quality Version' } },
      // },
      {
        path: 'case',
        name: 'CaseLibrary',
        component: () => import('@/pages/quality/case/index.vue'),
        meta: { title: { zh_CN: '案例库', en_US: 'Case Library' } },
      },
    ],
  },
];
