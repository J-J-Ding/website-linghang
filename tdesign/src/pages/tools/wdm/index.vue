<template>
  <div class="iframe-container" :class="{ 'is-collapsed': isSidebarCollapsed, 'no-sidebar': !showSidebar }">
    <iframe
      src="https://wsit.zx.zte.com.cn/bf_generate_aide/"
      frameborder="0"
      scrolling="auto"
      sandbox="allow-same-origin allow-scripts allow-forms allow-downloads allow-uploads"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useSettingStore } from '@/store';

const settingStore = useSettingStore();
const isSidebarCollapsed = computed(() => settingStore.isSidebarCompact);
const showSidebar = computed(() => settingStore.showSidebar);
</script>

<style scoped>
.iframe-container {
  position: absolute; /* 改为absolute定位 */
  top: 56px; /* 头部高度 */
  left: 232px; /* 侧边栏展开时的宽度 */
  right: 0;
  bottom: 0;
  width: calc(100vw - 232px); /* 减去侧边栏宽度 */
  height: calc(100vh - 56px); /* 减去头部高度 */
  overflow: hidden;
  margin: 0;
  padding: 0;
  border: none;
  z-index: 1; /* 确保在合适的层级 */
}

/* 侧边栏收起（紧凑）时，左偏移和宽度调整 */
.iframe-container.is-collapsed {
  left: 64px;
  width: calc(100vw - 64px);
}

/* 侧边栏隐藏时，全屏显示 */
.iframe-container.no-sidebar {
  left: 0;
  width: 100vw;
}

iframe {
  width: 100%;
  height: 100%;
  display: block;
  margin: 0;
  padding: 0;
  border: none;
}
</style>
