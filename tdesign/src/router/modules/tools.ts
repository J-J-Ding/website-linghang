import Layout from '@/layouts/index.vue';

export default [
  {
    path: '/tools',
    name: 'tools',
    component: Layout,
    redirect: '/tools/loganalyze',
    meta: {
      title: {
        zh_CN: '常用工具',
        en_US: 'Common Tools',
      },
      icon: 'tools-circle',
    },
    children: [
      {
        path: 'loganalyze',
        name: 'LogAnalyze',
        component: () => import('@/pages/tools/loganalyze/index.vue'),
        meta: { title: { zh_CN: '硫化日志分析', en_US: 'Log Analyze' } },
      },
      {
        path: 'l0',
        name: 'L0',
        component: () => import('@/pages/tools/l0/index.vue'),
        meta: { title: { zh_CN: '新增光板', en_US: 'New Board' } },
      },
      {
        path: 'wdm',
        name: 'WDM',
        component: () => import('@/pages/tools/wdm/index.vue'),
        meta: { title: { zh_CN: '波分代码生成', en_US: 'WDM Code Generation' } },
      },
      // {
      //   path: 'xingxiaomi',
      //   name: 'Xingxiaomi',
      //   component: () => import('@/pages/tools/xingxiaomi/index.vue'),
      //   meta: { title: { zh_CN: '兴小秘', en_US: 'Xing xiaomi' } },
      // },
      {
        path: 'componentportrait',
        name: 'componentPortrait',
        component: () => import('@/pages/ai/componentportrait/index.vue'),
        meta: { title: { zh_CN: '组件画像', en_US: 'ComponentPortrait' } },
      },
      {
        path: 'superagent',
        name: 'AI超级助手',
        component: () => import('@/pages/ai/chat/superagent.vue'),
        meta: { title: { zh_CN: '超级AI助手', en_US: 'superagent' } },
      },
      {
        path: 'test',
        name: 'AiTest',
        component: () => import('@/pages/ai/test/index2.vue'),
        meta: { title: { zh_CN: '测试页', en_US: 'Test' } },
      },
    ],
  },
];
