<template>
  <div class="f-design_review_agent">
    <AiChat :ai-chat-agent="DesignReviewAgent" />
  </div>
</template>

<script setup lang="js">
import { ref, onMounted, onUnmounted } from 'vue';
import AiChat from '@/pages/ai/agent/design.vue';

const DesignReviewAgent = ref('DocReviewAgent');

// 计算容器高度
const calculateContainerHeight = () => {
  const offset = 150;
  return window.innerHeight - offset;
};

// 监听窗口大小变化
const handleResize = () => {
  document.documentElement.style.setProperty('--container-height', calculateContainerHeight() + 'px');
};

onMounted(() => {
  // 初始化高度
  handleResize();

  // 添加窗口大小变化监听器
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // 移除窗口大小变化监听器
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.f-design_review_agent {
  width: 100%;
  height: var(--container-height, 100vh); /* 使用CSS变量，回退值为100vh */
}
</style>
