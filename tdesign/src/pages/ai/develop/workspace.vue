<template>
  <div class="workspace-main">hello world!</div>
</template>

<script setup lang="jsx">
import { ref } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useUserStore } from '@/store';

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const userStore = useUserStore();
</script>

<style lang="less">
.workspace-main :deep(*) {
}
</style>
