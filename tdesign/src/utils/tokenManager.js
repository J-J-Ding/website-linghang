// src/utils/tokenManager.js
import axios from 'axios';
import * as CryptoJS from 'crypto-js';
import globalUserInfo from './globalUserInfo';
import { MessagePlugin } from 'tdesign-vue-next';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;

class TokenManager {
  constructor() {
    this._token = null;
    this._refreshPromise = null;
    this._requestQueue = [];
  }

  // 设置用户信息（调用全局存储）
  setUserInfo(userInfo) {
    globalUserInfo.setUserInfo(userInfo);
  }

  // 获取当前token
  getToken() {
    return this._token;
  }

  // 设置token
  setToken(token) {
    console.log('设置用户的token: ', token);
    this._token = token;
  }

  // 清除token和用户信息
  clearToken() {
    this._token = null;
    globalUserInfo.clearUserInfo();
  }

  // 刷新token的方法
  async refreshToken() {
    if (this._refreshPromise) {
      return this._refreshPromise;
    }

    this._refreshPromise = new Promise(async (resolve, reject) => {
      try {
        // 检查全局用户信息
        if (!globalUserInfo.hasUserInfo()) {
          MessagePlugin.error('用户信息缺失，请退出重新登陆!');
          return null;
        }

        // 使用全局存储的账号和加密密码
        const account = globalUserInfo.getAccount();
        const encryptedPassword = globalUserInfo.getEncryptedPassword();

        const refreshResponse = await fetch(`${SERVER_API_URL}/api_login/Login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: account,
            password: encryptedPassword,
          }),
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          
          if (data.code === 200) {
            const newToken = data.uactoken;
            globalUserInfo.setTimeInfo(Date.now());
            this.setToken(newToken);
            this._processQueue(null, newToken);
            resolve(newToken);
          } else {
            throw new Error(data.message || 'Token刷新失败');
          }
        } else {
          throw new Error(`Token refresh failed with status: ${refreshResponse.status}`);
        }
      } catch (error) {
        this.clearToken();
        this._processQueue(error, null);
        reject(error);
      } finally {
        this._refreshPromise = null;
      }
    });

    return this._refreshPromise;
  }

  // 添加请求到队列
  addToQueue(resolve, reject) {
    this._requestQueue.push({ resolve, reject });
  }

  // 处理队列中的请求
  _processQueue(error, token = null) {
    this._requestQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });
    this._requestQueue = [];
  }

  // 获取token，如果token不存在则自动刷新
  async getTokenAutoRefresh() {
    // const currentToken = this.getToken();
    // const hasNotExpired = globalUserInfo.isValid();
    // if (currentToken && hasNotExpired) {
    //   return currentToken;
    // }
    
    try {
      const newToken = await this.refreshToken();
      return newToken;
    } catch (error) {
      throw error;
    }
  }

  // 初始化方法
  async init() {
    try {
      if (globalUserInfo.hasUserInfo() && globalUserInfo.isValid()) {
        return await this.getTokenAutoRefresh();
      }
      throw new Error('需要重新登录');
    } catch (error) {
      console.error('Token初始化失败:', error);
      throw error;
    }
  }
}

// 创建全局单例
const tokenManager = new TokenManager();

export default tokenManager;