import axios from 'axios';
import * as CryptoJS from 'crypto-js';

import { defineStore } from 'pinia';
import { MessagePlugin } from 'tdesign-vue-next';

import { usePermissionStore } from '@/store';
import type { UserInfo } from '@/types/interface';
import globalUserInfo from '@/utils/globalUserInfo';
const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const secretKey = 'secret-key-bofenruanjiankaifayibu-linghang-ai'; // 后端必须使用相同的密钥

const InitUserInfo: UserInfo = {
  name: '', // 用户名，用于展示在页面右上角头像处
  roles: [], // 前端权限模型使用 如果使用请配置modules/permission-fe.ts使用
};

export const useUserStore = defineStore('user', {
  state: () => ({
    token: 'main_token', // 默认token不走权限
    uacToken: '', // UAC账号token
    userInfo: { ...InitUserInfo },
  }),
  getters: {
    roles: (state) => {
      return state.userInfo?.roles;
    },
  },
  actions: {
    async login(userInfo: Record<string, unknown>) {
      // 使用 AES 加密密码
      const encryptedPassword = CryptoJS.AES.encrypt(userInfo.password as string, secretKey).toString();

      const response = await fetch(`${SERVER_API_URL}/api_login/Login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: userInfo.account,
          password: encryptedPassword,
        }),
      });

      const res = await response.json();

      if (res.code === 200) {
        this.token = 'main_token';
        this.uacToken = res.uactoken;
        this.userInfo.name = res.username;

        globalUserInfo.setTimeInfo(Date.now());
        
        globalUserInfo.setUserInfo({
          account: userInfo.account,
          password: userInfo.password,
        });

        return res.code;
      } else {
        // 抛出错误以便调用处 catch
        const message = res.message || '登录失败，请检查账号或密码';
        throw new Error(message);
      }
    },
    async getUserInfo() {
      const mockRemoteUserInfo = async (token: string) => {
        if (token === 'main_token') {
          return {
            name: this.userInfo.name,
            roles: ['all'], // 前端权限模型使用 如果使用请配置modules/permission-fe.ts使用
          };
        }
        return {
          name: 'td_dev',
          roles: ['UserIndex', 'AiChat', 'login'], // 前端权限模型使用 如果使用请配置modules/permission-fe.ts使用
        };
      };
      const res = await mockRemoteUserInfo(this.token);

      this.userInfo = res;
    },
    async logout() {
      this.token = '';
      this.userInfo = { ...InitUserInfo };
    },
  },
  persist: {
    afterRestore: () => {
      const permissionStore = usePermissionStore();
      permissionStore.initRoutes();
    },
    key: 'user',
    paths: ['token', 'uacToken', 'userInfo'],
  },
});
