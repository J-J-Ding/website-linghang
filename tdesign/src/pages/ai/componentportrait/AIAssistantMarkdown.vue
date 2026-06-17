<!-- src/components/MarkdownRenderer.vue -->
<template>
    <div class="markdown-content">
        <div v-html="renderedHtml"></div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import plantumlEncoder from 'plantuml-encoder'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps({
    content: {
        type: String,
        required: true
    },
    messageId: {
        type: [Number, String],
        default: null
    }
})

const emit = defineEmits(['copy', 'like', 'dislike'])

// 配置 marked
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: true,
    mangle: false
})

// 处理 PlantUML 代码块
const processPlantUML = (content) => {
    if (!content) return ''
    
    let processed = content
    
    // 匹配 ```plantuml 代码块
    const plantumlRegex = /```plantuml\s*\n([\s\S]*?)```/g
    processed = processed.replace(plantumlRegex, (match, code) => {
        const trimmedCode = code.trim()
        if (trimmedCode) {
            try {
                // 确保 PlantUML 代码包含必要的标签
                let plantUmlCode = trimmedCode
                if (!plantUmlCode.startsWith('@startuml')) {
                    plantUmlCode = '@startuml\n' + plantUmlCode + '\n@enduml'
                }
                const encoded = plantumlEncoder.encode(plantUmlCode)
                const imageUrl = `https://www.plantuml.com/plantuml/svg/${encoded}`
                const uniqueId = `plantuml-${Math.random().toString(36).substr(2, 9)}`
                
                return `<div class="plantuml-container" data-plantuml-id="${uniqueId}">
                    <div class="plantuml-wrapper">
                        <img 
                            src="${imageUrl}" 
                            alt="PlantUML Diagram" 
                            class="plantuml-image" 
                            loading="lazy"
                            onerror="this.parentElement.innerHTML='<div class=\\'plantuml-error\\'><span class=\\'error-icon\\'>⚠️</span><p>PlantUML图表加载失败</p><pre><code>${escapeHtml(trimmedCode)}</code></pre></div>'"
                            onclick="if(this.src) window.open(this.src, '_blank')"
                        />
                        <div class="plantuml-toolbar">
                            <button class="toolbar-btn" onclick="window.open('${imageUrl}', '_blank')" title="在新窗口打开">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                                    <path d="M14 2h-3.5L12 3.5l-2 2L11 6.5l2-2L14.5 6 14 2zM2 2h5v1H3v10h10V9h1v5H2V2z"/>
                                </svg>
                            </button>
                            <button class="toolbar-btn" onclick="navigator.clipboard.writeText('${escapeHtml(trimmedCode)}')" title="复制源码">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                                    <path d="M4 2a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V3a1 1 0 00-1-1H4zm0-1h8a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V3a2 2 0 012-2z"/>
                                    <path d="M8 5a.5.5 0 01.5.5v3h3a.5.5 0 010 1h-3v3a.5.5 0 01-1 0v-3h-3a.5.5 0 010-1h3v-3A.5.5 0 018 5z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>`
            } catch (error) {
                console.error('PlantUML编码失败:', error)
                return `<pre><code class="language-text">${escapeHtml(trimmedCode)}</code></pre>`
            }
        }
        return match
    })
    
    return processed
}

// HTML 转义函数
const escapeHtml = (text) => {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }
    return text.replace(/[&<>"']/g, (m) => map[m])
}

// 添加代码块复制按钮
const addCopyButtons = (html) => {
    return html.replace(/<pre><code([\s\S]*?)<\/code><\/pre>/g, (match, attrs) => {
        const codeMatch = match.match(/<code[^>]*>([\s\S]*?)<\/code>/)
        if (!codeMatch) return match
        
        const code = codeMatch[1]
        const escapedCode = escapeHtml(code)
        
        return `<div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-language">${getLanguageFromClass(attrs)}</span>
                <t-button 
                    class="copy-button" 
                    variant="text" 
                    size="small"
                    data-code="${escapedCode}"
                    @click="copyCode"
                >
                    <t-icon name="file-copy" />
                    <span>复制代码</span>
                </t-button>
            </div>
            <pre><code${attrs}>${code}</code></pre>
        </div>`
    })
}

// 获取代码语言
const getLanguageFromClass = (classStr) => {
    const match = classStr.match(/class="language-(\w+)"/)
    return match ? match[1] : 'text'
}

// 处理后的内容
const processedContent = computed(() => {
    if (!props.content) return ''
    
    // 先处理 PlantUML
    let processed = processPlantUML(props.content)
    
    // 配置 marked 渲染器以支持代码高亮
    const renderer = new marked.Renderer()
    
    renderer.code = function(code, language) {
        const validLanguage = language && hljs.getLanguage(language) ? language : 'plaintext'
        const highlighted = hljs.highlight(code, { 
            language: validLanguage, 
            ignoreIllegals: true 
        }).value
        
        return `<div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-language">${validLanguage}</span>
                <t-button 
                    class="copy-button" 
                    variant="text" 
                    size="small"
                    onclick="handleCopyCode(this)"
                    data-code="${escapeHtml(code)}"
                >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M4 2a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V2z"/>
                        <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h1v7a1 1 0 001 1h5.73a2 2 0 01-1.73 1H4a2 2 0 01-2-2V6z"/>
                    </svg>
                    <span>复制</span>
                </t-button>
            </div>
            <pre><code class="hljs language-${validLanguage}">${highlighted}</code></pre>
        </div>`
    }
    
    // 渲染 Markdown
    marked.setOptions({ renderer })
    const html = marked(processed)
    
    return html
})

// 渲染后的 HTML
const renderedHtml = computed(() => {
    return processedContent.value
})

// 复制代码处理方法（供内联 onclick 使用）
const handleCopyCode = (button) => {
    const code = button.dataset.code
    if (code) {
        const decodedCode = decodeURIComponent(code)
        navigator.clipboard.writeText(decodedCode).then(() => {
            const originalHtml = button.innerHTML
            button.innerHTML = '<span>已复制!</span>'
            setTimeout(() => {
                button.innerHTML = originalHtml
            }, 2000)
        }).catch(err => {
            console.error('复制失败:', err)
        })
    }
}

// 暴露给全局使用
if (typeof window !== 'undefined') {
    window.handleCopyCode = handleCopyCode
}
</script>

<style scoped>
.markdown-content {
    line-height: 1.6;
    color: #333;
    font-size: 14px;
}

.markdown-content :deep(h1) {
    font-size: 1.5em;
    margin: 0.67em 0;
    font-weight: bold;
    color: #000;
}

.markdown-content :deep(h2) {
    font-size: 1.3em;
    margin: 0.83em 0;
    font-weight: bold;
    color: #000;
}

.markdown-content :deep(h3) {
    font-size: 1.1em;
    margin: 1em 0;
    font-weight: bold;
    color: #000;
}

.markdown-content :deep(h4) {
    font-size: 1em;
    margin: 1.2em 0;
    font-weight: bold;
}

.markdown-content :deep(p) {
    margin: 0.8em 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
    margin: 0.8em 0;
    padding-left: 1.5em;
}

.markdown-content :deep(li) {
    margin: 0.3em 0;
}

.markdown-content :deep(a) {
    color: #0052d9;
    text-decoration: none;
}

.markdown-content :deep(a:hover) {
    text-decoration: underline;
}

/* 代码块容器 */
.markdown-content :deep(.code-block-wrapper) {
    margin: 16px 0;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid #e7e7e7;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.markdown-content :deep(.code-block-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: #f5f7fa;
    border-bottom: 1px solid #e7e7e7;
}

.markdown-content :deep(.code-language) {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    font-weight: 500;
}

.markdown-content :deep(.copy-button) {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #666;
    cursor: pointer;
    transition: all 0.2s;
    padding: 4px 8px;
    border-radius: 4px;
}

.markdown-content :deep(.copy-button:hover) {
    background: #e8eaed;
    color: #0052d9;
}

.markdown-content :deep(.copy-button svg) {
    width: 14px;
    height: 14px;
}

.markdown-content :deep(pre) {
    position: relative;
    padding: 16px;
    margin: 0;
    overflow: auto;
    background-color: #f6f8fa;
}

.markdown-content :deep(code) {
    font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
    font-size: 0.9em;
    background-color: rgba(27, 31, 35, 0.05);
    padding: 0.2em 0.4em;
    border-radius: 3px;
}

.markdown-content :deep(pre code) {
    background: none;
    padding: 0;
    border-radius: 0;
    font-size: 13px;
    line-height: 1.5;
}

.markdown-content :deep(blockquote) {
    margin: 1em 0;
    padding: 12px 16px;
    border-left: 4px solid #0052d9;
    background-color: #f0f5ff;
    color: #666;
    border-radius: 0 4px 4px 0;
}

.markdown-content :deep(table) {
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
    display: block;
    overflow-x: auto;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
}

.markdown-content :deep(th) {
    background-color: #f5f5f5;
    font-weight: bold;
}

.markdown-content :deep(strong) {
    font-weight: bold;
}

.markdown-content :deep(em) {
    font-style: italic;
}

/* PlantUML 容器样式 */
.markdown-content :deep(.plantuml-container) {
    text-align: center;
    margin: 16px 0;
    padding: 16px;
    background-color: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e9ecef;
    position: relative;
}

.markdown-content :deep(.plantuml-wrapper) {
    position: relative;
    display: inline-block;
    max-width: 100%;
}

.markdown-content :deep(.plantuml-image) {
    max-width: 100%;
    height: auto;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-radius: 4px;
    cursor: pointer;
    transition: transform 0.2s;
}

.markdown-content :deep(.plantuml-image:hover) {
    transform: scale(1.02);
}

.markdown-content :deep(.plantuml-toolbar) {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
}

.markdown-content :deep(.plantuml-wrapper:hover .plantuml-toolbar) {
    opacity: 1;
}

.markdown-content :deep(.toolbar-btn) {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
    color: #666;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.markdown-content :deep(.toolbar-btn:hover) {
    background: #0052d9;
    color: white;
    border-color: #0052d9;
}

.markdown-content :deep(.plantuml-error) {
    padding: 16px;
    text-align: center;
    color: #d54941;
}

.markdown-content :deep(.error-icon) {
    font-size: 24px;
    margin-bottom: 8px;
}

.markdown-content :deep(hr) {
    border: none;
    border-top: 1px solid #e7e7e7;
    margin: 16px 0;
}

.markdown-content :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
}

/* 代码高亮主题调整 */
.markdown-content :deep(.hljs) {
    background: transparent;
    padding: 0;
}

/* 列表嵌套样式 */
.markdown-content :deep(ul ul),
.markdown-content :deep(ol ol) {
    margin: 0;
}

/* 任务列表样式 */
.markdown-content :deep(input[type="checkbox"]) {
    margin-right: 0.5em;
}
</style>