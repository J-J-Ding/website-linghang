<template>
  <div class="test_ai" :style="{ height: containerHeight + 'px' }">
    <AiChat :ai-chat-title="tableAiTitle" :ai-chat-context="tableAiContext" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import AiChat from '@/pages/ai/chat/chatpro.vue';

// AI对话相关
const tableAiTitle = ref('这是我要传给子组件的标题');
const tableAiContext = ref('{"主题":"这是我要传给子组件的上下文"}');

// 容器高度
const containerHeight = ref(window.innerHeight);

// 计算容器高度
const calculateContainerHeight = () => {
  // 可以根据需要在这里加入其他需要扣除的高度（如header、footer等）
  const offset = 150; // 设置偏移量
  return window.innerHeight - offset;
};

// 监听窗口大小变化
const handleResize = () => {
  containerHeight.value = calculateContainerHeight();
};

onMounted(() => {
  // 初始化高度
  containerHeight.value = calculateContainerHeight();
  // 添加窗口大小变化监听器
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // 移除窗口大小变化监听器
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.test_ai {
  width: 100%;
}
</style>
