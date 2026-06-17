// utils/storage.js
export const storage = {
  // 设置缓存
  set(key, value) {
    try {
      const serializedValue = JSON.stringify(value);
      localStorage.setItem(key, serializedValue);
    } catch (error) {
      console.error('缓存设置失败:', error);
    }
  },
  
  // 获取缓存
  get(key, defaultValue = null) {
    try {
      const serializedValue = localStorage.getItem(key);
      if (serializedValue === null) return defaultValue;
      return JSON.parse(serializedValue);
    } catch (error) {
      console.error('缓存读取失败:', error);
      return defaultValue;
    }
  },
  
  // 删除缓存
  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('缓存删除失败:', error);
    }
  },
  
  // 清空所有缓存
  clear() {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('清空缓存失败:', error);
    }
  }
};