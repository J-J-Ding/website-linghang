import tokenManager from '@/utils/tokenManager';

export default {
  install: (app) => {
    // 初始化token
    const initToken = () => {
      const token = tokenManager.getToken();
      if (!token) {
        tokenManager.getTokenAutoRefresh().catch((error) => {
          console.log('自动获取token失败', error);
        });
      }
    };
    // 立即执行一次
    initToken();
    // 提供全局方法
    app.config.globalProperties.$tokenManager = tokenManager;
  },
};
