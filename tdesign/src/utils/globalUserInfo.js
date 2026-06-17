// src/utils/globalUserInfo.js
import * as CryptoJS from 'crypto-js';

const secretKey = 'secret-key-bofenruanjiankaifayibu-linghang-ai';

class GlobalUserInfo {
  constructor() {
    this._userInfo = this._loadFromStorage();
  }

  // 从localStorage加载用户信息
  _loadFromStorage() {
    try {
      const stored = localStorage.getItem('global_user_info');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('加载用户信息失败:', error);
    }
    return null;
  }

  // 保存到localStorage
  _saveToStorage() {
    try {
      if (this._userInfo) {
        localStorage.setItem('global_user_info', JSON.stringify(this._userInfo));
      } else {
        localStorage.removeItem('global_user_info');
      }
    } catch (error) {
      console.error('保存用户信息失败:', error);
    }
  }

  setTimeInfo(timestamp) {
    this._timestamp = timestamp;
    this._userInfo = this._loadFromStorage();
    if (!this._userInfo) return;
    this.setUserInfo(this._userInfo);
  }

  // 设置用户信息
  setUserInfo(userInfo) {
    this._userInfo = {
      account: userInfo.account,
      password: userInfo.password, // 存储明文密码（考虑安全性）
      timestamp:  this._timestamp, // 添加时间戳用于验证
    };
    this._saveToStorage();
  }

  // 获取用户信息
  getUserInfo() {
    return this._userInfo ? { ...this._userInfo } : null;
  }

  // 获取账号
  getAccount() {
    return this._userInfo?.account || '';
  }

  // 获取密码（返回明文）
  getPassword() {
    return this._userInfo?.password || '';
  }

  // 获取加密后的密码
  getEncryptedPassword() {
    if (!this._userInfo?.password) return '';
    return CryptoJS.AES.encrypt(this._userInfo.password, secretKey).toString();
  }

  // 清除用户信息
  clearUserInfo() {
    this._userInfo = null;
    this._saveToStorage();
  }

  // 检查是否有用户信息
  hasUserInfo() {
    return !!this._userInfo;
  }

  // 验证用户信息是否有效（例如：不超过8小时）
  isValid() {
    if (!this._userInfo || !this._userInfo.timestamp) return false;
    
    // 设置有效期（6小时）
    const expirationTime = 6 * 60 * 60 * 1000;
    const hasNotExpired = Date.now() - this._userInfo.timestamp;
    return hasNotExpired < expirationTime;
  }
}

// 创建全局单例
const globalUserInfo = new GlobalUserInfo();

export default globalUserInfo;