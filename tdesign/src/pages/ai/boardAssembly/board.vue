<template>
    <div class="board-assembly-main">
        <div class="assembly-container">
            <!-- 顶部步骤按钮区域 -->
            <div class="steps-header">
                <div class="mcp-service-label">
                    <span class="mcp-text">MCP服务</span>
                </div>
                <div class="step-item">
                    <div class="step-label">第一步</div>
                    <t-button 
                        theme="primary" 
                        class="step-button"
                        :disabled="loading"
                        @click="handleStep1">
                        组装要素生成
                    </t-button>
                </div>
                <div class="step-item">
                    <div class="step-label">第二步</div>
                    <t-button 
                        theme="primary" 
                        class="step-button"
                        :disabled="loading || !canStep2"
                        @click="handleStep2">
                        框架代码生成
                    </t-button>
                </div>
                <div class="step-item">
                    <div class="step-label">第三步</div>
                    <t-button 
                        theme="primary" 
                        class="step-button"
                        :disabled="loading || !canStep3"
                        @click="handleStep3">
                        配置参数生成
                    </t-button>
                </div>
            </div>

            <!-- 主内容区域 -->
            <div class="content-area">
                <!-- 左侧输入区域 -->
                <div class="left-panel">
                    <div class="input-group">
                        <t-form :data="formData" layout="vertical" label-width="100px">
                            <t-form-item label="IP" name="ip">
                                <t-select
                                    v-model="formData.ip"
                                    :options="ipHistoryOptions"
                                    placeholder="请输入或选择IP地址"
                                    clearable
                                    filterable
                                    creatable
                                    allow-input
                                />
                            </t-form-item>
                            <t-form-item label="代码路径" name="codePath">
                                <t-select
                                    v-model="formData.codePath"
                                    :options="codePathHistoryOptions"
                                    placeholder="请输入或选择代码路径"
                                    clearable
                                    filterable
                                    creatable
                                    allow-input
                                />
                            </t-form-item>
                            <t-form-item label="单板名称" name="boardName">
                                <t-select
                                    v-model="formData.boardName"
                                    :options="boardNameOptions"
                                    placeholder="请选择单板名称"
                                    clearable
                                    filterable
                                    creatable
                                />
                            </t-form-item>
                            <t-form-item label="业务模型" name="businessModel">
                                <t-select
                                    v-model="formData.businessModel"
                                    :options="businessModelOptions"
                                    placeholder="请选择业务模型"
                                    clearable
                                    filterable
                                    creatable
                                />
                            </t-form-item>
                        </t-form>
                    </div>
                </div>

                <!-- 右侧输出区域 -->
                <div class="right-panel">
                    <div class="output-header">
                        <span class="output-title">内容输出</span>
                    </div>
                    <div class="output-content" ref="outputContentRef">
                        <div v-if="outputContent" class="output-text" v-html="formatOutput(outputContent)"></div>
                        <div v-else class="output-placeholder">
                            <p>请先填写左侧输入信息，然后点击上方步骤按钮生成内容</p>
                        </div>
                        <div v-if="loading" class="loading-indicator">
                            <t-loading :loading="loading" text="生成中..." />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="jsx">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';
import { getBoardNamestFactorRelationByParams, getBusinessModels, generateElements, generateFramework, generateConfig } from '@/api/assistant.js'

const SERVER_API_URL = import.meta.env.VITE_SERVER_API_URL;
const router = useRouter();
const user = useUserStore();

// 表单数据
const formData = ref({
    ip: '',
    codePath: '',
    boardName: '',
    businessModel: ''
});

// IP历史记录选项列表
const ipHistoryOptions = ref([]);

// 代码路径历史记录选项列表
const codePathHistoryOptions = ref([]);

// 单板名称选项列表
const boardNameOptions = ref([]);

// 业务模型选项列表
const businessModelOptions = ref([]);

// 输出内容
const outputContent = ref('');
const loading = ref(false);
const outputContentRef = ref(null);

// 步骤状态
const step1Completed = ref(false);
const step2Completed = ref(false);

// 计算属性：是否可以执行步骤2和3
const canStep2 = computed(() => step1Completed.value);
const canStep3 = computed(() => step2Completed.value);

// 获取单板名称选项列表
const fetchBoardNameOptions = async () => {
    try {
        const responseData = {
            status: "error",
        };//await getBoardNamestFactorRelationByParams();

        // if (!response.ok) {
        //     throw new Error(`HTTP错误! 状态码: ${response.status}`);
        // }

        // const responseData = await response.json();
        if (responseData.status === 'success' && responseData.data) {
            // 将数据转换为 t-select 需要的格式
            boardNameOptions.value = responseData.data.map(item => ({
                label: item.name || item.value || item,
                value: item.value || item.name || item
            }));
        } else {
            // 如果 API 失败，使用默认选项
            boardNameOptions.value = [
                { label: 'M1CB8R', value: 'M1CB8R' },
                { label: 'M1LB8TF', value: 'M1LB8TF' },
                { label: 'M3CB4R', value: 'M3CB4R' },
                { label: 'M3LB4R', value: 'M3LB4R' },
                { label: 'M8C4R', value: 'M8C4R' },
                { label: 'M1MQ4HB', value: 'M1MQ4HB' },
                { label: 'M1MHM4G', value: 'M1MHM4G' }
            ];
            console.warn('获取单板名称选项失败，使用默认选项');
        }
    } catch (error) {
        console.error('获取单板名称选项失败:', error);
        // 使用默认选项作为后备
        boardNameOptions.value = [
            { label: 'M1CB8R', value: 'M1CB8R' },
            { label: 'M1LB8TF', value: 'M1LB8TF' },
            { label: 'M3CB4R', value: 'M3CB4R' },
            { label: 'M3LB4R', value: 'M3LB4R' },
            { label: 'M8C4R', value: 'M8C4R' },
            { label: 'M1MQ4HB', value: 'M1MQ4HB' },
            { label: 'M1MHM4G', value: 'M1MHM4G' }
        ];
    }
};

// 获取业务模型选项列表
const fetchBusinessModelOptions = async () => {
    try {
        const responseData = await getBusinessModels();

        // if (!response.ok) {
        //     throw new Error(`HTTP错误! 状态码: ${response.status}`);
        // }

        // const responseData = await response.json();
        if (responseData.status === 'success' && responseData.data) {
            // 将数据转换为 t-select 需要的格式
            businessModelOptions.value = responseData.data.map(item => ({
                label: item.label || item.name || `${item.value}(${item.description || ''})`,
                value: item.value || item.name || item
            }));
        } else {
            // 如果 API 失败，使用默认选项
            // businessModelOptions.value = [
            //     { label: 'sc(客户版)', value: 'sc' },
            //     { label: 'sl(线路板)', value: 'sl' },
            //     { label: 'mf(支线路有framer板)', value: 'mf' },
            //     { label: 'mn(支线路无framer板)', value: 'mn' }
            // ];
            console.warn('获取业务模型选项失败，使用默认选项');
        }
    } catch (error) {
        console.error('获取业务模型选项失败:', error);
        // 使用默认选项作为后备
        businessModelOptions.value = [
            { label: 'sc(客户版)', value: 'sc' },
            { label: 'sl(线路板)', value: 'sl' },
            { label: 'mf(支线路有framer板)', value: 'mf' },
            { label: 'mn(支线路无framer板)', value: 'mn' }
        ];
    }
};

// localStorage key
const IP_HISTORY_KEY = 'board_assembly_ip_history';
const CODE_PATH_HISTORY_KEY = 'board_assembly_code_path_history';
const MAX_HISTORY_COUNT = 20; // 最多保存20条历史记录

// 从localStorage加载IP历史记录
const loadIpHistory = () => {
    try {
        const defaultIp = '10.239.69.183';
        const historyStr = localStorage.getItem(IP_HISTORY_KEY);
        let history = [];
        
        if (historyStr) {
            history = JSON.parse(historyStr);
        }
        
        // 确保默认IP在选项中（如果不存在则添加）
        if (!history.includes(defaultIp)) {
            history.unshift(defaultIp);
        }
        
        // 转换为t-select需要的格式，去重并限制数量
        const uniqueHistory = Array.from(new Set(history)).slice(0, MAX_HISTORY_COUNT);
        ipHistoryOptions.value = uniqueHistory.map(ip => ({
            label: ip,
            value: ip
        }));
    } catch (error) {
        console.error('加载IP历史记录失败:', error);
        // 即使出错也确保默认IP在选项中
        ipHistoryOptions.value = [
            { label: '10.239.69.183', value: '10.239.69.183' }
        ];
    }
};

// 保存IP到历史记录
const saveIpToHistory = (ip) => {
    if (!ip || !ip.trim()) return;
    
    try {
        const defaultIp = '10.239.69.183';
        const historyStr = localStorage.getItem(IP_HISTORY_KEY);
        let history = historyStr ? JSON.parse(historyStr) : [];
        
        // 移除已存在的相同IP
        history = history.filter(item => item !== ip);
        // 将新IP添加到最前面
        history.unshift(ip);
        // 限制历史记录数量
        history = history.slice(0, MAX_HISTORY_COUNT);
        
        // 保存到localStorage
        localStorage.setItem(IP_HISTORY_KEY, JSON.stringify(history));
        
        // 确保默认IP在选项中（如果不存在则添加）
        if (!history.includes(defaultIp)) {
            history.unshift(defaultIp);
        }
        
        // 更新选项列表
        const uniqueHistory = Array.from(new Set(history));
        ipHistoryOptions.value = uniqueHistory.map(ip => ({
            label: ip,
            value: ip
        }));
    } catch (error) {
        console.error('保存IP历史记录失败:', error);
    }
};

// 从localStorage加载代码路径历史记录
const loadCodePathHistory = () => {
    try {
        const defaultCodePath = '/otn_ai/test/wanghao';
        const historyStr = localStorage.getItem(CODE_PATH_HISTORY_KEY);
        let history = [];
        
        if (historyStr) {
            history = JSON.parse(historyStr);
        }
        
        // 确保默认代码路径在选项中（如果不存在则添加）
        if (!history.includes(defaultCodePath)) {
            history.unshift(defaultCodePath);
        }
        
        // 转换为t-select需要的格式，去重并限制数量
        const uniqueHistory = Array.from(new Set(history)).slice(0, MAX_HISTORY_COUNT);
        codePathHistoryOptions.value = uniqueHistory.map(path => ({
            label: path,
            value: path
        }));
    } catch (error) {
        console.error('加载代码路径历史记录失败:', error);
        // 即使出错也确保默认代码路径在选项中
        codePathHistoryOptions.value = [
            { label: '/otn_ai/test/wanghao', value: '/otn_ai/test/wanghao' }
        ];
    }
};

// 保存代码路径到历史记录
const saveCodePathToHistory = (codePath) => {
    if (!codePath || !codePath.trim()) return;
    
    try {
        const defaultCodePath = '/otn_ai/test/wanghao';
        const historyStr = localStorage.getItem(CODE_PATH_HISTORY_KEY);
        let history = historyStr ? JSON.parse(historyStr) : [];
        
        // 移除已存在的相同代码路径
        history = history.filter(item => item !== codePath);
        // 将新代码路径添加到最前面
        history.unshift(codePath);
        // 限制历史记录数量
        history = history.slice(0, MAX_HISTORY_COUNT);
        
        // 保存到localStorage
        localStorage.setItem(CODE_PATH_HISTORY_KEY, JSON.stringify(history));
        
        // 确保默认代码路径在选项中（如果不存在则添加）
        if (!history.includes(defaultCodePath)) {
            history.unshift(defaultCodePath);
        }
        
        // 更新选项列表
        const uniqueHistory = Array.from(new Set(history));
        codePathHistoryOptions.value = uniqueHistory.map(path => ({
            label: path,
            value: path
        }));
    } catch (error) {
        console.error('保存代码路径历史记录失败:', error);
    }
};

// 组件挂载时获取选项列表
onMounted(() => {
    loadIpHistory();
    loadCodePathHistory();
    fetchBoardNameOptions();
    fetchBusinessModelOptions();
});

// 格式化输出内容（支持markdown和代码高亮）
const formatOutput = (content) => {
    if (!content) return '';
    // 简单的格式化处理，将换行符转换为<br>
    // return content;
    return content.replace(/\n/g, '<br>');
};

// 第一步：组装要素生成
const handleStep1 = async () => {
    // 验证输入
    if (!formData.value.ip || !formData.value.codePath || !formData.value.boardName || !formData.value.businessModel) {
        MessagePlugin.warning('请填写完整的输入信息（IP、代码路径、单板名称、业务模型）');
        return;
    }

    loading.value = true;
    outputContent.value = '';

    try {
        const requestData = {
            user: user.userInfo.name || 'guest',
            ip: formData.value.ip,
            codePath: formData.value.codePath,
            boardName: formData.value.boardName,
            businessModel: formData.value.businessModel,
            step: 1
        };

        const responseData = await generateElements(requestData);

        // if (!response.ok) {
        //     throw new Error(`HTTP错误! 状态码: ${response.status}`);
        // }

        // const responseData = await response.json();
        if (responseData.status === 'success') {
            // 优先显示文件内容，如果没有则显示文件路径或消息
            if (responseData.data && responseData.data.file_content) {
                // 显示文件内容，添加文件路径信息作为标题
                const filePath = responseData.data.target_file || '';
                outputContent.value = `文件路径: ${filePath}\n\n文件内容:\n${'='.repeat(80)}\n${responseData.data.file_content}`;
            } else {
                // 如果没有文件内容，显示文件路径或消息
                outputContent.value = responseData.data.target_file || responseData.message || '组装要素生成完成';
            }
            step1Completed.value = true;
            // 保存IP和代码路径到历史记录
            saveIpToHistory(formData.value.ip);
            saveCodePathToHistory(formData.value.codePath);
            MessagePlugin.success('组装要素生成成功');
            
            // 滚动到底部
            setTimeout(() => {
                if (outputContentRef.value) {
                    outputContentRef.value.scrollTop = outputContentRef.value.scrollHeight;
                }
            }, 100);
        } else {
            throw new Error(responseData.message || '组装要素生成失败');
        }
    } catch (error) {
        console.error('组装要素生成失败:', error);
        outputContent.value = `错误: ${error.message || '生成失败，请重试'}`;
        MessagePlugin.error(error.message || '组装要素生成失败');
    } finally {
        loading.value = false;
    }
};

// 第二步：框架代码生成
const handleStep2 = async () => {
    // if (!step1Completed.value) {
    //     MessagePlugin.warning('请先完成第一步：组装要素生成');
    //     return;
    // }

    loading.value = true;

    try {
        const requestData = {
            user: user.userInfo.name || 'guest',
            ip: formData.value.ip,
            codePath: formData.value.codePath,
            boardName: formData.value.boardName,
            businessModel: formData.value.businessModel,
            step: 2,
            previousStepData: '/otn_ai/test/wanghao/boardassemble/05_assembly_config/M3LB4R_hw_cfg.mk',//outputContent.value
        };

    // const response = await fetch(`http://10.239.69.183:3035/api/boardAssembly/generateFramework`, {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify(requestData),
    // });
    
    // console.log('response', response);
    // const responseData = response.data;

    // console.log('responseData', responseData);

        const responseData = await generateFramework(requestData);

        // if (!response.ok) {
        //     throw new Error(`HTTP错误! 状态码: ${response.status}`);
        // }

        // const responseData = await response.json();
        if (responseData.status === 'success') {
            const newContent = responseData.data.output || responseData.message || '框架代码生成完成';
            outputContent.value += '\n\n=== 框架代码生成结果 ===\n\n' + newContent;
            step2Completed.value = true;
            MessagePlugin.success('框架代码生成成功');
            
            // 滚动到底部
            setTimeout(() => {
                if (outputContentRef.value) {
                    outputContentRef.value.scrollTop = outputContentRef.value.scrollHeight;
                }
            }, 100);
        } else {
            throw new Error(responseData.message || '框架代码生成失败');
        }
    } catch (error) {
        console.error('框架代码生成失败:', error);
        outputContent.value += `\n\n错误: ${error.message || '生成失败，请重试'}`;
        MessagePlugin.error(error.message || '框架代码生成失败');
    } finally {
        loading.value = false;
    }
};

// 第三步：配置参数生成
const handleStep3 = async () => {
    // if (!step2Completed.value) {
    //     MessagePlugin.warning('请先完成第二步：框架代码生成');
    //     return;
    // }

    loading.value = true;

    try {
        const requestData = {
            user: user.userInfo.name || 'guest',
            ip: formData.value.ip,
            codePath: formData.value.codePath,
            boardName: formData.value.boardName,
            businessModel: formData.value.businessModel,
            step: 3,
            previousStepData: outputContent.value
        };

        const responseData = await generateConfig(requestData);

        // if (!response.ok) {
        //     throw new Error(`HTTP错误! 状态码: ${response.status}`);
        // }

        // const responseData = await response.json();
        if (responseData.status === 'success') {
            const newContent = responseData.data.output || responseData.message || '配置参数生成完成';
            outputContent.value += '\n\n=== 配置参数生成结果 ===\n\n' + newContent;
            MessagePlugin.success('配置参数生成成功');
            
            // 滚动到底部
            setTimeout(() => {
                if (outputContentRef.value) {
                    outputContentRef.value.scrollTop = outputContentRef.value.scrollHeight;
                }
            }, 100);
        } else {
            throw new Error(responseData.message || '配置参数生成失败');
        }
    } catch (error) {
        console.error('配置参数生成失败:', error);
        outputContent.value += `\n\n错误: ${error.message || '生成失败，请重试'}`;
        MessagePlugin.error(error.message || '配置参数生成失败');
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
.board-assembly-main {
    width: 100%;
    height: 100%;
    padding: 20px;
    background: 
        linear-gradient(90deg, #e5e5e5 1px, transparent 1px),
        linear-gradient(#e5e5e5 1px, transparent 1px);
    background-size: 20px 20px;
    background-color: #f5f5f5;
}

.assembly-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

/* 步骤按钮区域 */
.steps-header {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    padding: 20px;
    background-color: #fafafa;
    border-bottom: 1px solid #e5e5e5;
    gap: 30px;
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.step-label {
    font-size: 14px;
    color: #666;
    font-weight: 500;
}

.step-button {
    min-width: 150px;
    height: 40px;
    font-size: 14px;
    font-weight: 500;
}

/* 主内容区域 */
.content-area {
    flex: 1;
    display: flex;
    min-height: 0;
    overflow: hidden;
}

/* 左侧输入面板 */
.left-panel {
    width: 350px;
    min-width: 350px;
    padding: 20px;
    background-color: #ffffff;
    border-right: 1px solid #e5e5e5;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.mcp-service-label {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 80px;
    padding-right: 20px;
    border-right: 1px solid #e5e5e5;
}

.mcp-text {
    font-size: 16px;
    font-weight: 600;
    color: #1a16fc;
    display: inline-block;
    line-height: 1;
}

.input-group {
    flex: 1;
}

/* 右侧输出面板 */
.right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    background-color: #ffffff;
}

.output-header {
    padding: 15px 20px;
    background-color: #fafafa;
    border-bottom: 1px solid #e5e5e5;
}

.output-title {
    font-size: 16px;
    font-weight: 600;
    color: #333;
}

.output-content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background-color: #ffffff;
    position: relative;
    max-height: 60vh;
}

.output-text {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
}

.output-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999;
    font-size: 14px;
}

.output-placeholder p {
    text-align: center;
    margin: 0;
}

.loading-indicator {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 10;
}

/* 响应式设计 */
@media (max-width: 1200px) {
    .left-panel {
        width: 300px;
        min-width: 300px;
    }
}

@media (max-width: 768px) {
    .content-area {
        flex-direction: column;
    }
    
    .left-panel {
        width: 100%;
        min-width: 100%;
        border-right: none;
        border-bottom: 1px solid #e5e5e5;
    }
    
    .steps-header {
        flex-direction: column;
        gap: 15px;
    }
    
    .step-item {
        width: 100%;
    }
    
    .step-button {
        width: 100%;
    }
}
</style>

