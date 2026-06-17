<template>
  <div class="developing-page">
    <div class="content">
      <!-- 使用一个醒目的图标 -->
      <t-icon name="building" size="80px" class="construction-icon pulse" />

      <!-- 主要提示信息 -->
      <h2 class="title">功能开发中</h2>
      <p class="description">我们正在努力开发此功能，敬请期待！</p>
    </div>
  </div>
</template>

<script setup>
import { Icon as TIcon } from 'tdesign-vue-next';
</script>

<style scoped>
.developing-page {
  height: 80vh; /* 全屏高度 */
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 渐变背景 */
  font-family: 'Arial', sans-serif;
}

.content {
  text-align: center;
  color: white;
  padding: 40px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px); /* 毛玻璃效果 */
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 100%;
  animation: fadeIn 0.6s ease-out; /* 淡入动画 */
}

.construction-icon {
  color: #ffd700; /* 金色 */
  margin-bottom: 24px;
  display: inline-block;
}

/* 脉冲动画 */
.pulse {
  animation: pulse 2s infinite;
}

.title {
  font-size: 2.2rem;
  margin: 0 0 16px 0;
  font-weight: 600;
}

.description {
  font-size: 1.1rem;
  margin: 0;
  opacity: 0.9;
  line-height: 1.6;
}

/* 动画关键帧 */
@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
