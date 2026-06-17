<!-- src/components/AIAssistant.vue -->
<template>
    <div class="ai-chat-container">
        <div class="ai-header">
            <span class="ai-title">组件智能体</span>
            <t-button variant="text" shape="circle" @click="close">
                <template #icon>
                    <close-icon />
                </template>
            </t-button>
        </div>
        <div class="ai-messages" ref="messagesContainer">
            <div 
                v-for="(message, index) in messages" 
                :key="index"
                :class="['ai-message', `ai-${message.type}`]"
            >
                <div class="message-content">
                    <MarkdownRenderer 
                        :content="message.content" 
                        :message-id="index"
                        @copy="handleCopy"
                        @like="handleLike"
                        @dislike="handleDislike"
                    />
                </div>
                <div class="message-actions" v-if="message.type === 'bot'">
                    <t-button 
                        variant="text" 
                        size="small" 
                        @click="handleCopy(message.content)"
                        title="复制"
                    >
                        <template #icon>
                            <file-copy-icon />
                        </template>
                    </t-button>
                    <t-button 
                        variant="text" 
                        size="small" 
                        :theme="message.feedback === 'like' ? 'primary' : 'default'"
                        @click="handleLike(index)"
                        title="有用"
                    >
                        <template #icon>
                            <thumb-up-icon />
                        </template>
                    </t-button>
                    <t-button 
                        variant="text" 
                        size="small" 
                        :theme="message.feedback === 'dislike' ? 'danger' : 'default'"
                        @click="handleDislike(index)"
                        title="无用"
                    >
                        <template #icon>
                            <thumb-down-icon />
                        </template>
                    </t-button>
                </div>
            </div>
        </div>
        <div class="ai-input-area">
            <t-input
                v-model="inputValue"
                placeholder="请输入消息..."
                @enter="sendMessage"
                :disabled="isSending"
                clearable
            />
            <t-button 
                theme="primary" 
                shape="circle" 
                @click="sendMessage" 
                :disabled="isSending || !inputValue.trim()"
            >
                <template #icon>
                    <send-icon v-if="!isSending" />
                    <loading-icon v-else />
                </template>
            </t-button>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { CloseIcon, FileCopyIcon, ThumbUpIcon, ThumbDownIcon, SendIcon, LoadingIcon } from 'tdesign-icons-vue-next'
import MarkdownRenderer from '@/pages/ai/componentportrait/AIAssistantMarkdown.vue'

const props = defineProps({
    initialMessages: {
        type: Array,
        default: () => []
    }
})

const emit = defineEmits(['user-message', 'close', 'feedback'])

const messages = ref([
    {
        type: 'bot',
        content: '您好！我是您的智能助手，有什么可以帮助您？',
        feedback: null
    }
])

const inputValue = ref('')
const isSending = ref(false)
const messagesContainer = ref(null)

// 初始化消息
watch(() => props.initialMessages, (newVal) => {
    messages.value = [
        {
            type: 'bot',
            content: '您好！我是您的智能助手，有什么可以帮助您？',
            feedback: null
        },
        ...newVal.map(msg => ({
            ...msg,
            feedback: msg.feedback || null
        }))
    ]
}, { immediate: true })

// 监听消息变化，滚动到底部
watch(messages, () => {
    nextTick(() => {
        scrollToBottom()
    })
}, { deep: true })

const sendMessage = () => {
    if (!inputValue.value.trim() || isSending.value) return

    const userMessage = {
        type: 'user',
        content: inputValue.value.trim(),
        feedback: null
    }

    messages.value.push(userMessage)
    emit('user-message', inputValue.value.trim())
    inputValue.value = ''
}

const addAIMessage = (content) => {
    messages.value.push({
        type: 'bot',
        content: content,
        feedback: null
    })
}

const close = () => {
    emit('close')
}

const scrollToBottom = () => {
    const container = messagesContainer.value
    if (container) {
        container.scrollTop = container.scrollHeight
    }
}

const handleCopy = (content) => {
    navigator.clipboard.writeText(content).then(() => {
        MessagePlugin.success('已复制到剪贴板')
    }).catch(() => {
        MessagePlugin.error('复制失败')
    })
}

const handleLike = (index) => {
    const message = messages.value[index]
    if (message && message.type === 'bot') {
        message.feedback = message.feedback === 'like' ? null : 'like'
        emit('feedback', { index, type: 'like', messageId: index })
    }
}

const handleDislike = (index) => {
    const message = messages.value[index]
    if (message && message.type === 'bot') {
        message.feedback = message.feedback === 'dislike' ? null : 'dislike'
        emit('feedback', { index, type: 'dislike', messageId: index })
    }
}

onMounted(() => {
    scrollToBottom()
})

// 暴露方法给父组件
defineExpose({
    addAIMessage
})
</script>

<style scoped>
.ai-chat-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
}

.ai-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #ebeef5;
    font-size: 14px;
    color: #333;
    flex-shrink: 0;
}

.ai-title {
    font-weight: 500;
}

.ai-messages {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.ai-message {
    max-width: 90%;
    border-radius: 12px;
    line-height: 1.5;
    animation: fadeIn 0.3s ease;
    position: relative;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.ai-user {
    background-color: #e6f7ff;
    align-self: flex-start;
    border-top-right-radius: 4px;
}

.ai-bot {
    background-color: #f0f0f0;
    align-self: flex-end;
    border-top-left-radius: 4px;
}

.message-content {
    padding: 12px 14px;
}

.message-actions {
    display: flex;
    gap: 8px;
    padding: 8px 14px;
    border-top: 1px solid rgba(0,0,0,0.05);
}

.ai-input-area {
    padding: 16px;
    display: flex;
    gap: 10px;
    background-color: #f5f5f5;
    border-top: 1px solid #ebeef5;
    flex-shrink: 0;
}

.ai-input-area :deep(.t-input) {
    flex: 1;
}
</style>