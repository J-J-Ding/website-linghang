<template>
    <div class="doc-renderer">
        <template v-for="(part, index) in partList" :key="`part-${index}`">
            <!-- 普通文本 -->
            <p v-if="part.type === 'text'" class="text">{{ part.content }}</p>

            <!-- 标题 -->
            <component
                :id="part.id"
                v-else-if="part.type === 'heading'"
                :is="`h${part.level || 2}`"
                class="heading"
            >
                {{ part.content }}
            </component>

            <!-- PlantUML 图 -->
            <div v-else-if="part.type === 'plantuml'" class="uml-container">
                <img
                    :src="getPlantUmlUrl(part.content)"
                    class="uml-image"
                    alt="PlantUML Diagram"
                    loading="lazy"
                    @click="openModal(getPlantUmlUrl(part.content))"
                    style="cursor: pointer;"
                />

                <!-- 模态框 -->
                <teleport to="body">
                    <div v-if="currentImage" class="modal-overlay" @click="closeModal">
                        <div class="modal-content" @click.stop>
                            <img :src="currentImage" alt="Zoomed PlantUML" class="modal-image" />
                        </div>
                    </div>
                </teleport>
            </div>

            <!-- ECharts 图 -->
            <div v-else-if="part.type === 'echart'" :ref="el => setChartRef(el, index)" class="chart-container"></div>

            <!-- Markdown -->
            <div v-else-if="part.type === 'markdown'" class="markdown-content" v-html="renderMarkdown(part.content)"></div>

            <!-- 表格 -->
            <t-table
                v-else-if="part.type === 'table'"
                :data="part.data"
                :columns="getTableColumns(part.columns)"
                bordered
                stripe
                hover
                style="width: 100%; margin: 10px 0;"
            />

            <!-- 兜底 -->
            <div v-else class="unknown">
                [不支持的内容类型: {{ part.type }}]
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import plantumlEncoder from 'plantuml-encoder'
import { marked } from 'marked'

const props = defineProps({
    partList: { type: Array, required: true }
})

const currentImage = ref(null)
const chartRefs = ref({})
const charts = ref([])

// 设置图表引用
const setChartRef = (el, index) => {
    if (el) {
        chartRefs.value[`chart-${index}`] = el
    }
}

const getPlantUmlUrl = (code) => {
    if (!code) return ''
    let plantUmlCode = code.trim()
    if (!plantUmlCode.startsWith('@startuml')) {
        plantUmlCode = '@startuml\n' + plantUmlCode + '\n@enduml'
    }
    const encoded = plantumlEncoder.encode(plantUmlCode)
    return `https://www.plantuml.com/plantuml/png/${encoded}`
}

const openModal = (src) => {
    currentImage.value = src
    document.addEventListener('keydown', handleKeydown)
}

const closeModal = () => {
    currentImage.value = null
    document.removeEventListener('keydown', handleKeydown)
}

const handleKeydown = (e) => {
    if (e.key === 'Escape') closeModal()
}

const renderMarkdown = (content) => {
    return marked(content || '')
}

const getTableColumns = (columns) => {
    return columns.map(col => ({
        colKey: col.prop,
        title: col.label
    }))
}

const renderCharts = () => {
    disposeCharts()

    props.partList.forEach((part, index) => {
        if (part.type !== 'echart') return

        const el = chartRefs.value[`chart-${index}`]
        if (!el) return

        const chart = echarts.init(el)
        let option

        if (part.chartType === 'radar') {
            let indicatorList = ["发现能力", "设计能力", "编码能力", "质量能力", "组装能力", "工程能力"]
            let baseScoreList = [60, 60, 60, 60, 60, 60]
            let tooltipText = ""
            for (let i = 0; i < part.data.value.length; i++) {
                const score = part.data.value[i]
                const baseScore = baseScoreList[i]
                const status = score >= baseScore ? "<span style='color:green'>【达  标】</span>" : "<span style='color:red'>【未达标】</span>"
                tooltipText += `${status} ${indicatorList[i]}：${score} (达标分：${baseScore})<br>`
            }

            option = {
                tooltip: {
                    trigger: 'item',
                    backgroundColor: "#000000",
                    formatter: () => tooltipText
                },
                radar: {
                    center: ['20%', '50%'],
                    indicator: part.data.indicator.map(name => ({ name, max: 100 })),
                    name: {
                        formatter: "【{value}】",
                        textStyle: {
                            color: '#428BD4',
                            fontSize: 16,
                            fontWeight: 'bold',
                            padding: [0, 0, 15, 0]
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#eee',
                            width: 1,
                            type: 'solid'
                        }
                    },
                },
                series: [
                    {
                        name: "得分",
                        type: "radar",
                        data: [
                            {
                                value: part.data.value,
                                name: "得分",
                                label: {
                                    show: true,
                                    fontSize: 18,
                                    fontWeight: 'bold',
                                    formatter: (params) => params.value,
                                    color: '#4CAF50',
                                },
                                lineStyle: {
                                    width: 3,
                                    color: '#4CAF50'
                                },
                            },
                            {
                                value: baseScoreList,
                                name: "达标线",
                                lineStyle: {
                                    width: 2,
                                    type: 'dashed',
                                    color: '#FF5252'
                                },
                            },
                        ],
                    },
                ],
            }
        } else if (part.chartType === 'tree') {
            option = {
                series: [{
                    type: 'tree',
                    data: [part.data],
                    left: '10%',
                    right: '30%',
                    bottom: '10%',
                    symbolSize: 7,
                    initialTreeDepth: 2,
                    edgeShape: 'polyline',
                    edgeForkPosition: '63%',
                    label: {
                        position: 'left',
                        verticalAlign: 'middle',
                        align: 'right',
                    },
                    leaves: {
                        label: {
                            position: 'right',
                            verticalAlign: 'middle',
                            align: 'left',
                        },
                    },
                    expandAndCollapse: true,
                    animationDuration: 550,
                    animationDurationUpdate: 750,
                }]
            }
        } else if (part.chartType === 'bar') {
            const xAxisData = part.data.map(item => item.date)
            const addData = part.data.map(item => item.add)
            const delData = part.data.map(item => item.del)
            option = {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    }
                },
                legend: {
                    data: ['新增', '删除'],
                    bottom: '1%',
                },
                xAxis: {
                    type: 'category',
                    data: xAxisData
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        name: '新增',
                        type: 'bar',
                        stack: '总量',
                        data: addData,
                        itemStyle: {
                            color: '#299B48'
                        },
                    },
                    {
                        name: '删除',
                        type: 'bar',
                        stack: '总量',
                        data: delData,
                        itemStyle: {
                            color: '#E53D30'
                        },
                    }
                ]
            }
        }
        
        if (option) {
            chart.setOption(option)
            charts.value.push(chart)
        }
    })

    bindResizeEvent()
}

const bindResizeEvent = () => {
    window.addEventListener('resize', handleResize)
}

const handleResize = () => {
    charts.value.forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize()
        }
    })
}

const disposeCharts = () => {
    window.removeEventListener('resize', handleResize)
    charts.value.forEach(chart => {
        if (chart && typeof chart.dispose === 'function') {
            chart.dispose()
        }
    })
    charts.value = []
}

onMounted(() => {
    nextTick(() => {
        renderCharts()
    })
})

// 监听 partList 变化
watch(() => props.partList, () => {
    nextTick(() => {
        renderCharts()
    })
}, { deep: true })

onBeforeUnmount(() => {
    disposeCharts()
    document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.doc-renderer {
    line-height: 1.8;
}

.text {
    font-size: 15px;
    color: #333;
    margin: 1em 0;
}

.heading {
    margin: 1.5em 0 0.8em;
    color: #000;
    font-weight: 600;
}

/* PlantUML 图片样式 */
.uml-image {
    max-width: 100%;
    height: auto;
    margin: 20px 0;
    border: 1px solid #ddd;
    border-radius: 4px;
    transition: transform 0.2s ease;
}

.uml-image:hover {
    transform: scale(1.02);
}

/* 模态框样式 */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.85);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2000;
    animation: fadeIn 0.3s ease-out;
}

.modal-content {
    position: relative;
    max-width: 95vw;
    max-height: 95vh;
    padding: 10px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    animation: zoomIn 0.3s ease-out;
}

.modal-image {
    max-width: 100%;
    max-height: 90vh;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

/* 动画效果 */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes zoomIn {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

.chart-container {
    height: 400px;
    margin: 20px 0;
}

.markdown-content {
    background: #fdfdfd;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #eee;
}

.unknown {
    color: red;
    font-style: italic;
    padding: 10px;
    background: #fff0f0;
    border: 1px dashed #f66;
}
</style>