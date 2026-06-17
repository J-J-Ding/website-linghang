<template>
  <div class="test">
    <t-layout>
      <t-aside width="400px">任务列表</t-aside>
      <t-content>Content</t-content>
      <t-aside width="600px"><AiChat :ai-chat-title="tableAiTitle" :ai-chat-context="tableAiContext" /></t-aside>
    </t-layout>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import AiChat from '@/pages/ai/chat/chatpro.vue';

// AI对话相关
const tableAiTitle = ref('这是我要传给子组件的标题');
const tableAiContext = ref('{"主题":"这是我要传给子组件的上下文"}');
</script>
