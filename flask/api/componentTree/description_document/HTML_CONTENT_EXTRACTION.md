# HTML 格式章节内容提取指南

## 📋 修改概述

将章节内容从**纯文本格式**改为**HTML 格式**传递给前端，保留原始的排版、表格、代码块等结构化信息。

---

## 🎯 修改内容

### 1. 新增 `_clean_html_content()` 方法

**位置**: `graph_service.py` 第 653-690 行

**功能**: 清理并保留 HTML 标签

```python
def _clean_html_content(self, content_elements: list) -> str:
    """
    清理和保留 HTML 格式的内容
    
    Args:
        content_elements: 内容元素列表（BeautifulSoup 标签）
    
    Returns:
        清理后的 HTML 字符串
    """
    if not content_elements:
        return ""
    
    try:
        html_parts = []
        for elem in content_elements:
            if hasattr(elem, 'decode'):
                # 保留 HTML 标签
                html = elem.decode()
                # 清理不需要的标签（script, style 等）
                if elem.name not in ['script', 'style', 'noscript']:
                    html_parts.append(html)
            else:
                # 文本节点
                text = str(elem).strip()
                if text:
                    html_parts.append(f'<p>{text}</p>')
        
        # 合并 HTML
        full_html = ''.join(html_parts)
        
        # 清理多余的空白字符（但保留 HTML 结构）
        full_html = re.sub(r'>\s+<', '><', full_html)
        
        return full_html
    
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {str(e)}")
        return ""
```

### 2. 修改 `_extract_section_content()` 方法

**位置**: `graph_service.py` 第 565-617 行

**修改**: 增加 `return_html` 参数（默认 `True`）

```python
def _extract_section_content(self, title_tag, soup: BeautifulSoup, return_html: bool = True) -> str:
    """
    从章节标题节点开始提取章节内容
    
    Args:
        title_tag: 章节标题的 BeautifulSoup 标签节点
        soup: BeautifulSoup 对象
        return_html: 是否返回 HTML 格式（默认 True）
    
    Returns:
        章节内容（HTML 格式或纯文本）
    """
    # ... 省略中间逻辑 ...
    
    if return_html:
        return self._clean_html_content(content_parts)
    else:
        return self._clean_content(content_parts)
```

### 3. 保留原有的 `_clean_content()` 方法

**位置**: `graph_service.py` 第 691-728 行

**功能**: 纯文本清理（向后兼容）

---

## 📊 修改前后对比

| 项目 | 修改前 | 修改后 |
|------|--------|--------|
| **返回格式** | 纯文本 | HTML |
| **表格** | 文本（丢失结构） | `<table>` 标签保留 |
| **代码块** | 纯文本（丢失格式） | `<pre><code>` 保留 |
| **列表** | 文本（丢失结构） | `<ul><li>` 保留 |
| **图片** | 丢失 | `<img>` 保留 |
| **PlantUML** | JSON 字符串 | 可渲染为 SVG |
| **数据量** | 较小 | 较大（但可接受） |

---

## 🔍 HTML 内容示例

### 修改前（纯文本）

```
接口说明函数包括但不限于：功能描述、函数名称、输入参数、返回参数、使用示例等
消息包括但不限于：功能描述、消息类型、消息 ID、消息体、使用示例等
共享变量包括但不限于：名称、操作权限等

组件方案设计
功能描述
otc 组件是一个光传输控制组件...
```

### 修改后（HTML）

```html
<p>接口说明函数包括但不限于：功能描述、函数名称、输入参数、返回参数、使用示例等</p>
<p>消息包括但不限于：功能描述、消息类型、消息 ID、消息体、使用示例等</p>
<p>共享变量包括但不限于：名称、操作权限等</p>

<h3>组件方案设计</h3>
<h4>功能描述</h4>
<p>otc 组件是一个光传输控制组件...</p>

<table>
  <tr>
    <th>模块</th>
    <th>功能描述</th>
    <th>代码文件路径</th>
  </tr>
  <tr>
    <td>激光器控制</td>
    <td>实现激光器的开关控制</td>
    <td>usm_board/otc/sdk/laser/...</td>
  </tr>
</table>

<pre><code>usm_board/otc/
├── makefile
├── sdk/
│   ├── include/
│   └── src/
</code></pre>
```

---

## 🚀 前端使用方法

### Vue 组件中渲染 HTML

```vue
<template>
  <div class="section-content">
    <!-- 使用 v-html 渲染 HTML 内容 -->
    <div v-html="sectionContent"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{
  sectionId: string
}>()

const sectionContent = ref('')

onMounted(async () => {
  // 从 API 获取章节内容
  const response = await fetch(`/api/component-tree/section/${props.sectionId}`)
  const data = await response.json()
  sectionContent.value = data.section_content // HTML 字符串
})
</script>

<style scoped>
.section-content {
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
  }
  
  :deep(th), :deep(td) {
    border: 1px solid #ddd;
    padding: 8px;
  }
  
  :deep(pre) {
    background-color: #f4f4f4;
    padding: 10px;
    overflow-x: auto;
  }
  
  :deep(code) {
    font-family: 'Courier New', monospace;
  }
}
</style>
```

---

## ⚠️ 注意事项

### 1. XSS 安全

前端渲染 HTML 时需要注意 XSS 攻击：

```vue
<!-- ❌ 危险：直接渲染 -->
<div v-html="userInput"></div>

<!-- ✅ 安全：使用 DOMPurify 清理 -->
<script src="dompurify"></script>
<script>
const cleanHTML = DOMPurify.sanitize(dirtyHTML)
</script>
```

**推荐安装**:
```bash
npm install dompurify
```

**使用示例**:
```typescript
import DOMPurify from 'dompurify'

const safeHTML = DOMPurify.sanitize(sectionContent.value)
```

### 2. 样式处理

后端返回的 HTML 不包含样式，需要前端提供：

```css
/* 全局样式或组件样式 */
.section-content {
  /* 表格样式 */
  table {
    border-collapse: collapse;
    width: 100%;
  }
  
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  
  th {
    background-color: #f2f2f2;
    font-weight: bold;
  }
  
  /* 代码块样式 */
  pre {
    background-color: #f4f4f4;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
  }
  
  code {
    font-family: 'Courier New', monospace;
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 2px;
  }
  
  /* 列表样式 */
  ul, ol {
    padding-left: 20px;
  }
  
  li {
    margin: 5px 0;
  }
  
  /* 图片样式 */
  img {
    max-width: 100%;
    height: auto;
  }
  
  /* 引用样式 */
  blockquote {
    border-left: 4px solid #ddd;
    padding-left: 10px;
    color: #666;
    margin: 10px 0;
  }
}
```

### 3. PlantUML 处理

如果 HTML 中包含 PlantUML 代码，需要前端渲染：

```vue
<template>
  <div class="section-content">
    <div v-for="(block, index) in contentBlocks" :key="index">
      <!-- PlantUML 代码块 -->
      <div v-if="block.type === 'plantuml'" :id="`plantuml-${index}`"></div>
      
      <!-- 普通 HTML -->
      <div v-else v-html="block.html"></div>
    </div>
  </div>
</template>

<script setup>
import plantumlEncoder from 'plantuml-encoder'

// 渲染 PlantUML
const renderPlantUML = (encoded, elementId) => {
  const url = `https://www.plantuml.com/plantuml/svg/${encoded}`
  const img = document.createElement('img')
  img.src = url
  document.getElementById(elementId).appendChild(img)
}
</script>
```

---

## 📝 数据库字段说明

### knowledge_component_section 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `section_content` | TEXT | **HTML 格式**的章节内容 |
| `raw_html` | TEXT | 原始 HTML（可选，用于调试） |

---

## ✅ 验证方法

### 1. 后端日志

查看控制台输出，确认提取的是 HTML：

```
📝 提取章节内容：'5.3.1 流程设计'
   ✅ HTML 内容长度：12500
   ✅ 包含标签：table, pre, code, ul, li
```

### 2. API 响应

```bash
curl http://localhost:3001/api/component-tree/section/xxx
```

响应中 `section_content` 字段应包含 HTML 标签。

### 3. 前端渲染

在浏览器开发者工具中查看渲染后的 HTML：

```html
<div class="section-content">
  <p>接口说明函数包括但不限于...</p>
  <table>...</table>
  <pre><code>...</code></pre>
</div>
```

---

## 🔄 回滚方案

如果需要回滚到纯文本格式：

```python
# 修改调用处
section_content = self._extract_section_content(
    title_tag, 
    soup, 
    return_html=False  # ← 改为 False
)
```

---

## 📚 相关文档

- [SECTION_PRINT_EXAMPLE.md](SECTION_PRINT_EXAMPLE.md) - 打印信息示例
- [CHANGE_NODE_NAME_TO_TEXT.md](script/CHANGE_NODE_NAME_TO_TEXT.md) - 字段类型变更说明

---

**修改时间**: 2026-05-21  
**影响范围**: 章节内容提取逻辑  
**向后兼容**: ✅ 是（支持 return_html=False）  
**前端要求**: 需要支持 HTML 渲染和样式
