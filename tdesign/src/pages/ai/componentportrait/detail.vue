<!-- src/views/DocDetail.vue -->
<template>
    <div class="doc-container">
        <!-- 主标题 -->
        <h1 class="main-title">{{ doc.title }}</h1>
        <!-- 左侧内容区 -->
        <div class="content-wrapper">
            <!-- 主内容 -->
            <div class="main-content">
                <template v-for="part in doc.partList" :key="part.id">
                    <div :id="part.id" class="part">
                        <h2>{{ part.title }}</h2>
                        <DocRenderer :part-list="part.content" />
                    </div>
                </template>
            </div>
            <!-- 右侧悬浮导航 -->
            <div class="sidebar-nav">
                <div class="nav-box">
                    <h3>📌 快速导航</h3>
                    <ul class="nav-list">
                        <li v-for="item in toc" :key="item.id">
                            <a 
                                href="#" 
                                :class="['nav-link', `level-${item.level}`, { 'is-active': activeSection === item.id }]" 
                                @click.prevent="scrollTo(item.id)"
                            >
                                {{ item.text }}
                            </a>
                            <!-- 二级标题嵌套 -->
                            <ul v-if="item.children && item.children.length" class="nav-sublist">
                                <li v-for="child in item.children" :key="child.id">
                                    <a 
                                        href="#" 
                                        :class="['nav-link', `level-${child.level}`, { 'is-active': activeSection === child.id }]" 
                                        @click.prevent="scrollTo(child.id)"
                                    >
                                        {{ child.text }}
                                    </a>
                                </li>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- AI 助手抽屉面板 -->
        <transition name="slide">
            <div v-if="isAIChatOpen" class="ai-chat-drawer">
                <AIAssistant 
                    ref="aiAssistantRef"
                    @user-message="handleUserMessage"
                    @close="closeAIChat"
                />
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import DocRenderer from '@/pages/ai/componentportrait/DocRenderer.vue'
import AIAssistant from '@/pages/ai/componentportrait/AIAssistant.vue'
// import { compQuerySingleCompProfileDetailList } from "@/api/comp.js"

const route = useRoute()
const doc = reactive({
    title: `${route.query.comp_name}组件画像详情`,
    partList: []
})
const toc = ref([])
const activeSection = ref('')
const isAIChatOpen = ref(false)
const aiAssistantRef = ref(null)
const observer = ref(null)

// 生成目录
const generateToc = () => {
    const tocData = []
    doc.partList.forEach(part => {
        // 一级标题
        tocData.push({
            id: part.id,
            text: part.title,
            level: 2,
            children: []
        })

        // 查找 content 中的 heading 类型作为二级标题
        part.content.forEach(block => {
            if (block.type === 'heading' && block.id) {
                const lastItem = tocData[tocData.length - 1]
                lastItem.children = lastItem.children || []
                lastItem.children.push({
                    id: block.id,
                    text: block.content,
                    level: block.level
                })
            }
        })
    })
    toc.value = tocData
}

// 平滑滚动到指定 ID
const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        activeSection.value = id
    }
}

// 监听当前可视章节
const observeSections = () => {
    observer.value = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    activeSection.value = entry.target.id
                }
            })
        },
        { threshold: 0.2, rootMargin: '-100px 0px 0px 0px' }
    )

    doc.partList.forEach(part => {
        const el = document.getElementById(part.id)
        if (el) observer.value.observe(el)
    })
}

// 控制 AI 抽屉开关
const toggleAIChat = () => {
    isAIChatOpen.value = !isAIChatOpen.value
}

const closeAIChat = () => {
    isAIChatOpen.value = false
}

// 处理用户消息
const handleUserMessage = async (message) => {
    try {
        // 模拟AI回复延迟
        setTimeout(() => {
            if (aiAssistantRef.value) {
                aiAssistantRef.value.addAIMessage(`收到您的消息："${message}"。这是AI助手的回复内容。`)
            }
        }, 1000)
    } catch (error) {
        console.error('AI助手调用失败:', error)
        if (aiAssistantRef.value) {
            aiAssistantRef.value.addAIMessage('抱歉，AI助手暂时无法响应，请稍后再试。')
        }
    }
}

onMounted(async () => {
    // try {
    //     const response = await compQuerySingleCompProfileDetailList(route.query.comp_name)
    //     doc.partList = response.body.data
    //     generateToc()
    //     observeSections()
    // } catch (err) {
    //     console.error('请求数据失败:', err)
    // }
})

onBeforeUnmount(() => {
    if (observer.value) {
        observer.value.disconnect()
    }
})
</script>

<style scoped>
.doc-container {
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    position: relative;
    min-height: 100vh;
}

.main-title {
    text-align: center;
    border-bottom: 4px solid #0052d9;
    padding-bottom: 10px;
    margin-bottom: 30px;
    color: #1a1a1a;
}

.content-wrapper {
    display: flex;
    gap: 30px;
    min-height: calc(100vh - 120px);
}

.main-content {
    flex: 1;
}

.part {
    margin-bottom: 60px;
    padding: 20px 0;
}

.part h2 {
    border-left: 4px solid #0052d9;
    padding-left: 12px;
    color: #000;
    font-size: 22px;
    margin-bottom: 20px;
}

/* 右侧悬浮导航 */
.sidebar-nav {
    width: 240px;
    position: sticky;
    top: 20px;
    height: fit-content;
}

.nav-box {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    max-height: 80vh;
    overflow-y: auto;
}

.nav-box h3 {
    margin: 0 0 15px 0;
    font-size: 16px;
    color: #333;
    text-align: center;
}

.nav-list {
    list-style: none;
    padding: 0;
    margin: 0;
    font-size: 14px;
}

.nav-sublist {
    list-style: none;
    padding-left: 18px;
    margin-top: 6px;
}

.nav-link {
    display: block;
    padding: 6px 8px;
    color: #555;
    text-decoration: none;
    border-radius: 4px;
    transition: all 0.2s;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.nav-link:hover {
    background-color: #f0f5ff;
    color: #0052d9;
}

.nav-link.is-active {
    background-color: #e6f7ff;
    color: #0052d9;
    font-weight: 500;
}

.nav-link.level-2 {
    font-weight: 600;
    color: #000;
}

.nav-link.level-3 {
    font-size: 13px;
}

/* AI 抽屉面板 */
.ai-chat-drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: 800px;
    height: 100vh;
    z-index: 1000;
    box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
    border-left: 1px solid #ebeef5;
}

/* 滑动动画 */
.slide-enter-active,
.slide-leave-active {
    transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
    transform: translateX(100%);
}
</style>