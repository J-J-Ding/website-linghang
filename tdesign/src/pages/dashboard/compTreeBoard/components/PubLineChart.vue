<!-- src/pages/dashboard/compTreeBoard/PubLineChart.vue -->
<template>
    <div class="chart-container" :style="{ height }">
        <div ref="chartRef" class="chart" :style="{ height }"></div>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
    chartData: {
        type: Array,
        required: true,
        default: () => []
    },
    title: {
        type: String,
        default: '数据趋势图'
    },
    yAxisName: {
        type: String,
        default: '数值'
    },
    height: {
        type: String,
        default: '400px'
    }
})

// 定义事件
const emit = defineEmits(['chart-click'])

const chartRef = ref(null)
let myChart = null

// 获取图表配置
const getChartOption = () => {
    // 按领域分组
    const fieldGroups = {}
    props.chartData.forEach(item => {
        if (!fieldGroups[item.field_name]) {
            fieldGroups[item.field_name] = []
        }
        fieldGroups[item.field_name].push({
            name: item.date,
            value: item.value
        })
    })

    // 提取所有日期（去重、排序）
    const allDates = [...new Set(props.chartData.map(item => item.date))].sort()

    // 构造 series
    const seriesList = Object.keys(fieldGroups).map(fieldName => {
        const dataMap = {}
        fieldGroups[fieldName].forEach(d => {
            dataMap[d.name] = d.value
        })

        return {
            name: fieldName,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            areaStyle: { opacity: 0.2 },
            emphasis: { 
                focus: 'series',
                itemStyle: {
                    borderWidth: 2,
                    borderColor: '#fff'
                }
            },
            data: allDates.map(date => dataMap[date] || 0)
        }
    })

    return {
        title: {
            text: props.title,
            left: 'center',
            top: '5%',
            textStyle: { fontSize: 17 }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { 
                type: 'cross',
                crossStyle: {
                    color: '#999'
                }
            },
            formatter: (params) => {
                let result = `<div style="padding: 4px 8px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">${params[0].axisValue}</div>`
                params.forEach(param => {
                    result += `<div style="display: flex; align-items: center; margin: 2px 0;">
                        <span style="display: inline-block; width: 10px; height: 10px; 
                            background: ${param.color}; border-radius: 50%; margin-right: 6px;"></span>
                        <span>${param.seriesName}: <strong>${param.value}</strong></span>
                    </div>`
                })
                return result
            }
        },
        legend: {
            data: Object.keys(fieldGroups),
            bottom: '5%',
            type: 'scroll'
        },
        grid: {
            left: '9%',
            right: '4%',
            bottom: '15%',
            top: '20%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: allDates,
            axisLabel: {
                rotate: 0,
                fontSize: 10,
                interval: 'auto',
                hideOverlap: true,
                margin: 8
            },
            axisTick: {
                alignWithLabel: true
            },
            triggerEvent: true
        },
        yAxis: {
            type: 'value',
            name: props.yAxisName,
            nameLocation: 'middle',
            nameGap: 40,
            nameTextStyle: { fontSize: 12 },
            axisLabel: {
                formatter: '{value}',
                fontSize: 12,
                color: '#666'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    color: '#e0e0e0',
                    width: 1,
                    type: 'dashed'
                }
            },
            axisLine: {
                show: true,
                lineStyle: {
                    color: '#333'
                }
            },
            axisTick: {
                show: true,
                alignWithLabel: true
            }
        },
        series: seriesList
    }
}

// 绑定图表点击事件
const bindChartEvents = () => {
    if (!myChart) return
    
    myChart.off('click')
    
    myChart.on('click', (params) => {
        if (params.componentType === 'series') {
            const clickInfo = {
                fieldName: params.seriesName,
                xValue: params.name,
                yValue: params.value,
                chartTitle: props.title,
                color: params.color,
                dataIndex: params.dataIndex,
                seriesIndex: params.seriesIndex
            }
            
            emit('chart-click', clickInfo)
            showClickFeedback(params)
        }
    })
    
    myChart.on('mouseover', (params) => {
        if (params.componentType === 'series') {
            myChart.getZr().setCursorStyle('pointer')
        }
    })
    
    myChart.on('mouseout', () => {
        myChart.getZr().setCursorStyle('default')
    })
}

// 点击反馈效果
const showClickFeedback = (params) => {
    if (!myChart) return
    
    myChart.dispatchAction({
        type: 'highlight',
        seriesIndex: params.seriesIndex,
        dataIndex: params.dataIndex
    })
    
    setTimeout(() => {
        if (myChart) {
            myChart.dispatchAction({
                type: 'downplay',
                seriesIndex: params.seriesIndex,
                dataIndex: params.dataIndex
            })
        }
    }, 2000)
}

// 更新图表
const updateChart = () => {
    if (!myChart) return
    const option = getChartOption()
    myChart.setOption(option, true)
    bindChartEvents()
}

// 初始化图表
const initChart = () => {
    if (!chartRef.value) return
    
    if (myChart) {
        myChart.dispose()
        myChart = null
    }
    
    myChart = echarts.init(chartRef.value)
    updateChart()
    bindChartEvents()
}

// 窗口大小变化处理
const handleResize = () => {
    if (myChart) {
        myChart.resize()
    }
}

// 监听数据变化
watch(() => props.chartData, () => {
    updateChart()
}, { deep: true })

// 监听标题变化
watch(() => props.title, () => {
    if (myChart) {
        myChart.setOption({
            title: {
                text: props.title
            }
        })
    }
})

onMounted(() => {
    initChart()
    window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    if (myChart) {
        myChart.off('click')
        myChart.off('mouseover')
        myChart.off('mouseout')
        myChart.dispose()
        myChart = null
    }
})

// 暴露方法给父组件
defineExpose({
    resize: handleResize,
    getChart: () => myChart,
    refresh: updateChart
})
</script>

<style scoped>
.chart-container {
    width: 100%;
    background: #fff;
    padding: 10px;
    border-radius: 4px;
    overflow: hidden;
    cursor: default;
}

.chart {
    width: 100%;
}
</style>