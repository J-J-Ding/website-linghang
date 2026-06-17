import { DashboardIcon } from 'tdesign-icons-vue-next';
import { shallowRef } from 'vue';

import Layout from '@/layouts/index.vue';

export default [
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/kanban',
    name: 'dashboard',
    meta: {
      title: {
        zh_CN: '仪表盘',
        en_US: 'Dashboard',
      },
      icon: shallowRef(DashboardIcon),
      orderNo: 0,
    },
    children: [
      // {
      //   path: 'base',
      //   name: 'DashboardBase',
      //   component: () => import('@/pages/dashboard/base/index.vue'),
      //   meta: {
      //     title: {
      //       zh_CN: '概览仪表盘',
      //       en_US: 'Overview',
      //     },
      //   },
      // },
      // {
      //   path: 'detail',
      //   name: 'DashboardDetail',
      //   component: () => import('@/pages/dashboard/detail/index.vue'),
      //   meta: {
      //     title: {
      //       zh_CN: '统计报表',
      //       en_US: 'Dashboard Detail',
      //     },
      //   },
      // },
      {
        path: 'kanban',
        name: 'DashboardKanban',
        component: () => import('@/pages/dashboard/kanban/index.vue'),
        meta: {
          title: {
            zh_CN: '数据看板',
            en_US: 'Dashboard Kanban',
          },
        },
      },
      {
        path: 'prkanban',
        name: 'DashboardPrKanban',
        component: () => import('@/pages/dashboard/prkanban/index.vue'),
        meta: {
          title: {
            zh_CN: '需求看板',
            en_US: 'Dashboard PR Kanban',
          },
        },
      },
      {
        path: 'department',
        name: 'department',
        component: () => import('@/pages/dashboard/kanban/department.vue'),
        meta: {
          title: {
            zh_CN: '部门看板',
            en_US: 'Dashboard Department Kanban',
          },
        },
      },
    {
        path: 'cntevalkanban',
        name: 'DashboardCEKanban',
        component: () => import('@/pages/dashboard/cntevalkanban/index.vue'),
        meta: {
          title: {
            zh_CN: '测评看板',
            en_US: 'Dashboard CE Kanban',
          },
        },
      },
    ],
  },
];
