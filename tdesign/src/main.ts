/* eslint-disable simple-import-sort/imports */
import { createApp } from 'vue';
import TDesign from 'tdesign-vue-next';
import TDesignChat from '@tdesign-vue-next/chat'; // 引入chat组件
import dayjs from 'dayjs'

import App from './App.vue';
import router from './router';
import { store } from './store';
import i18n from './locales';
// import tokenPlugin from './plugins/token';
import 'tdesign-vue-next/es/style/index.css';
import '@/style/index.less';
import './permission';
import tokenManager from '@/utils/tokenManager';
// 引入用户 store
import { useUserStore } from '@/store';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

// 构建 API URL 的辅助函数，确保 URL 格式正确
const getApiUrl = (path: string): string => {
  let baseUrl = SERVER_API_URL?.endsWith('/api') 
    ? SERVER_API_URL.replace(/\/api$/, '') 
    : (SERVER_API_URL || 'http://10.239.69.183:3030');
  
  // 确保 baseUrl 是有效的 URL（以 http:// 或 https:// 开头）
  if (!baseUrl || (!baseUrl.startsWith('http://') && !baseUrl.startsWith('https://'))) {
    console.warn('Invalid SERVER_API_URL, using default:', baseUrl);
    baseUrl = 'http://10.239.69.183:3030';
  }
  
  // 移除末尾的斜杠
  baseUrl = baseUrl.replace(/\/$/, '');
  
  // 如果 path 已经以 /api 开头，直接拼接；否则添加 /api
  const apiPath = path.startsWith('/api') ? path : `/api${path}`;
  
  return `${baseUrl}${apiPath}`;
};

const app = createApp(App);
app.config.globalProperties.$dayjs = dayjs
app.use(TDesign).use(TDesignChat);
app.use(store);
app.use(router);
app.use(i18n);
// app.use(tokenPlugin);
// ========== 修改点：在路由 afterEach 中获取用户信息并上报 ==========
router.afterEach(async (to, from) => {
  // 获取 Pinia 中的 user store
  const userStore = useUserStore();

  // 安全获取用户标识（优先使用 username 或 userId）
  // 假设你的 store 中有 username 或 id 字段
  const user_id = userStore.userInfo.name || 'guest';

  // 构造上报数据
  const payload = {
    page_now: to.fullPath,
    page_before: from.fullPath,
    user_id,
    user_agent: navigator.userAgent,
    timestamp: new Date().toLocaleString('sv-SE', { timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone }),
  };

  // 发送访问统计（使用环境变量拼接 URL）
  fetch(`${SERVER_API_URL}/api_login/API_Visit_set`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  }).catch((err) => {
    console.warn('访问统计上报失败:', err);
  });

  // 刷新token
  // await tokenManager.getTokenAutoRefresh();
});

app.mount('#app');
