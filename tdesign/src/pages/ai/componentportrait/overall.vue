<template>
    <div>
        <div class="filter-container">
            <div class="filter-background">
                <t-form layout="inline" label-width="70px">
                    <t-row :gutter="16">
                        <t-col :span="6">
                            <t-form-item label="组件名称">
                                <t-select 
                                    v-model="filterObj.comp_name" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择组件"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in compNameOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="6">
                            <t-form-item label="领域">
                                <t-select 
                                    v-model="filterObj.field_name" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择领域"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in fieldNameOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="6">
                            <t-form-item label="是否核心">
                                <t-select 
                                    v-model="filterObj.classification" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择是否核心"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in classificationOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="6">
                            <t-form-item label="上云等级">
                                <t-select 
                                    v-model="filterObj.actual_up_level" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择上云等级"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in upLevelOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                    </t-row>
                    <t-row :gutter="16">
                        <t-col :span="6">
                            <t-form-item label="是否下云">
                                <t-select 
                                    v-model="filterObj.down_flag" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择是否下云"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in downFlagOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="6">
                            <t-form-item label="成熟度">
                                <t-select 
                                    v-model="filterObj.mature_status" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择成熟度等级"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in matureStatusOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="6">
                            <t-form-item label="优质组件">
                                <t-select 
                                    v-model="filterObj.high_quality_status" 
                                    multiple 
                                    filterable 
                                    clearable
                                    placeholder="请选择优质组件状态"
                                    :min-collapsed-num="2"
                                >
                                    <t-option 
                                        v-for="item in highQualityStatusOptionList" 
                                        :key="item" 
                                        :label="item" 
                                        :value="item" 
                                    />
                                </t-select>
                            </t-form-item>
                        </t-col>
                        <t-col :span="4">
                            <t-space>
                                <t-button theme="primary" @click="applyFilters">筛选</t-button>
                                <t-button theme="default" @click="resetFilters">重置</t-button>
                                <t-button theme="success" @click="exportTableData">
                                    <template #icon>
                                        <download-icon />
                                    </template>
                                    导出数据
                                </t-button>
                            </t-space>
                        </t-col>
                    </t-row>
                </t-form>
            </div>
        </div>

        <!-- 表格区域 -->
        <t-table 
            :data="filteredProfileList" 
            :columns="tableColumns"
            row-key="comp_name"
            bordered
            stripe
            hover
            :max-height="tableMaxHeight"
            :header-cell-style="{ textAlign: 'center' }"
        >
            <!-- <template #comp_name="{ row }">
                <t-link theme="primary" hover="color" @click="goToProfileDetail(row)">
                    {{ row.comp_name }}
                </t-link>
            </template>
            <template #total_score="{ row }">
                <t-link theme="primary" hover="color" @click="goToMeasureDetail(row)">
                    {{ row.total_score }}
                </t-link>
            </template> -->
        </t-table>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { DownloadIcon } from 'tdesign-icons-vue-next'
import { compQueryCompProfileList, mainAddUserActInfo } from "@/api/comp.js"
import { Utils } from "@/utils/utils";

const store = Utils.getHeader();
const tableMaxHeight = ref(window.innerHeight * 0.75)
const profileList = ref([])
const compNameOptionList = ref([])
const fieldNameOptionList = ref([])
const classificationOptionList = ref([])
const upLevelOptionList = ref([])
const downFlagOptionList = ref([])
const matureStatusOptionList = ref([])
const highQualityStatusOptionList = ref([])
const filteredProfileList = ref([])

const filterObj = reactive({
    comp_name: [],
    field_name: [],
    classification: [],
    actual_up_level: [],
    down_flag: [],
    mature_status: [],
    high_quality_status: []
})

// 表格列配置
const tableColumns = computed(() => {
    const columns = [
        { colKey: 'serial-number', title: '序号', width: 60, align: 'center', fixed: 'left', cell: (h, { rowIndex }) => rowIndex + 1 },
        { colKey: 'comp_name', title: '组件名称', width: 160, fixed: 'left', ellipsis: true },
        { colKey: 'total_score', title: '精细化运营分数', width: 160, fixed: 'left', ellipsis: true, sorter: true },
        { colKey: 'field_name', title: '领域', width: 80, ellipsis: true },
        { colKey: 'team_name', title: '团队', width: 100, ellipsis: true },
        { colKey: 'defender_name', title: '守护人', width: 80, ellipsis: true },
        { colKey: 'project', title: '服务项目', width: 120, ellipsis: true },
        { colKey: 'classification', title: '是否核心', width: 100, ellipsis: true },
        { colKey: 'actual_up_level', title: '上云等级', width: 85, ellipsis: true },
        { colKey: 'down_flag', title: '是否下云', width: 85, ellipsis: true },
        { colKey: 'subscribe_time', title: '星云Market订阅量', width: 170, ellipsis: true, sorter: true },
        { colKey: 'mature_status', title: '成熟度等级', width: 100, ellipsis: true },
        { colKey: 'high_quality_status', title: '优质组件', width: 100, ellipsis: true },
        { colKey: 'code_aei_score', title: '代码级AEI分数', width: 140, ellipsis: true, sorter: true },
        { colKey: 'comp_aei_score', title: '组件级AEI分数', width: 140, ellipsis: true, sorter: true },
        { colKey: 'ut_func_rate', title: 'UT/FT函数覆盖率', width: 160, ellipsis: true, sorter: true },
        { colKey: 'ut_line_rate', title: 'UT/FT行覆盖率', width: 160, ellipsis: true, sorter: true },
        { colKey: 'ut_branch_rate', title: 'UT/FT分支覆盖率', width: 160, ellipsis: true, sorter: true },
        { colKey: 'fault_per_kilo_line_change_code', title: '千行修改代码故障数', width: 180, ellipsis: true, sorter: true },
        { colKey: 'fault_per_kilo_line_exist_code', title: '万行存量代码故障数', width: 180, ellipsis: true, sorter: true },
        { colKey: 'code_lines', title: 'AEI度量代码行数', width: 160, ellipsis: true, sorter: true },
        { colKey: 'code_all_line_num_with_cloc', title: '代码总行数(不含空行/注释)', width: 220, ellipsis: true, sorter: true },
        { colKey: 'code_all_line_aei_rate', title: '代码AEI度量覆盖率', width: 170, ellipsis: true, sorter: true },
        { colKey: 'jinos_dir_flag', title: 'JINOS目录规范', width: 160, ellipsis: true, sorter: true },
        { colKey: 'comp_tree_status', title: '组件树状态', width: 140, ellipsis: true, sorter: true },
        { colKey: 'code_all_aei_name', title: '代码级AEI任务名称', width: 160, ellipsis: true },
        { colKey: 'comp_all_aei_name', title: '组件级AEI任务名称', width: 160, ellipsis: true },
        { colKey: 'code_repo', title: '代码库名称', width: 140, ellipsis: true, sorter: true },
        { colKey: 'code_branch', title: '代码分支', width: 140, ellipsis: true },
        { colKey: 'code_path', title: '全部代码路径', width: 140, ellipsis: true },
        { colKey: 'code_simple_test_directory', title: '测试代码路径', width: 140, ellipsis: true },
        { colKey: 'change_num', title: '近半年变更行数', width: 160, ellipsis: true, sorter: true },
        { colKey: 'cn_name', title: '中文名称', width: 160, ellipsis: true },
        { colKey: 'en_name', title: '英文名称', width: 160, ellipsis: true },
        { colKey: 'en_code', title: '英文代号', width: 160, ellipsis: true },
        { colKey: 'pdm', title: 'PDM编号', width: 160, ellipsis: true }
    ]
    return columns
})

const fetchData = async () => {
    try {
        const response = await compQueryCompProfileList()
        profileList.value = response.body.data
        
        compNameOptionList.value = [...new Set(profileList.value.map(item => item.comp_name))].sort()
        fieldNameOptionList.value = [...new Set(profileList.value.map(item => item.field_name))].sort()
        classificationOptionList.value = [...new Set(profileList.value.map(item => item.classification))].sort()
        upLevelOptionList.value = [...new Set(profileList.value.map(item => item.actual_up_level))].sort()
        downFlagOptionList.value = [...new Set(profileList.value.map(item => item.down_flag))].sort()
        matureStatusOptionList.value = [...new Set(profileList.value.map(item => item.mature_status))].sort()
        highQualityStatusOptionList.value = [...new Set(profileList.value.map(item => item.high_quality_status))].sort()
        
        filteredProfileList.value = profileList.value
    } catch (error) {
        console.error(error)
        MessagePlugin.error('数据加载失败')
    }
}

const goToProfileDetail = (row) => {
    window.open(`http://local.zte.com.cn:3002/tools/componentportraitdetails?comp_name=${row.comp_name}`, "_blank")
}

const goToMeasureDetail = (row) => {
    window.open(`http://local.zte.com.cn:3002/tools/compmeasuredetail?comp_name=${row.comp_name}`, "_blank")
}

const applyFilters = () => {
    filteredProfileList.value = profileList.value.filter(item => {
        return (
            (!filterObj.comp_name.length || filterObj.comp_name.includes(item.comp_name)) &&
            (!filterObj.field_name.length || filterObj.field_name.includes(item.field_name)) &&
            (!filterObj.classification.length || filterObj.classification.includes(item.classification)) &&
            (!filterObj.actual_up_level.length || filterObj.actual_up_level.includes(item.actual_up_level)) &&
            (!filterObj.down_flag.length || filterObj.down_flag.includes(item.down_flag)) &&
            (!filterObj.mature_status.length || filterObj.mature_status.includes(item.mature_status)) &&
            (!filterObj.high_quality_status.length || filterObj.high_quality_status.includes(item.high_quality_status))
        )
    })
}

const resetFilters = () => {
    Object.keys(filterObj).forEach(key => {
        filterObj[key] = []
    })
    filteredProfileList.value = profileList.value
}

// 导出表格数据
const exportTableData = () => {
    if (filteredProfileList.value.length === 0) {
        MessagePlugin.warning('没有数据可以导出')
        return
    }

    const headers = {
        comp_name: '组件名称',
        total_score: '精细化运营分数',
        field_name: '领域',
        team_name: '团队',
        project: '服务项目',
        defender_name: '守护人',
        classification: '是否核心',
        actual_up_level: '上云等级',
        down_flag: '是否下云',
        subscribe_time: '星云Market订阅量',
        mature_status: '成熟度等级',
        high_quality_status: '优质组件',
        code_aei_score: '代码级AEI分数',
        comp_aei_score: '组件级AEI分数',
        ut_func_rate: 'UT/FT函数覆盖率',
        ut_line_rate: 'UT/FT行覆盖率',
        ut_branch_rate: 'UT/FT分支覆盖率',
        fault_per_kilo_line_change_code: '千行修改代码故障数',
        fault_per_kilo_line_exist_code: '万行存量代码故障数',
        code_lines: 'AEI度量代码行数',
        code_all_line_num_with_cloc: '代码总行数(不含空行/注释)',
        code_all_line_aei_rate: '代码AEI度量覆盖率',
        jinos_dir_flag: 'JINOS目录规范',
        comp_tree_status: '组件树状态',
        code_repo: '代码库名称',
        code_branch: '代码分支',
        code_path: '全部代码路径',
        code_simple_test_directory: "测试代码路径",
        change_num: '近半年变更行数',
        code_all_aei_name: '代码级AEI任务名称',
        cn_name: '中文名称',
        en_name: '英文名称',
        en_code: '英文代号',
        pdm: 'PDM编号',
    }

    const exportData = filteredProfileList.value.map(item => {
        const rowData = {}
        Object.keys(headers).forEach(key => {
            rowData[headers[key]] = item[key]
        })
        return rowData
    })

    let csvContent = convertToCSV(exportData)
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `组件画像全景_${new Date().toLocaleDateString()}.csv`
    link.click()
    URL.revokeObjectURL(url)

    mainAddUserActInfo({
        "user_id": '',
        "user_name": '',
        "act": "exportProfileTableData",
        "remark": filterObj,
    })

    MessagePlugin.success('导出成功')
}

const convertToCSV = (data) => {
    const headers = Object.keys(data[0])
    let csv = headers.join(',') + '\n'

    data.forEach(row => {
        const values = headers.map(header => {
            const rawValue = row[header]
            const value = rawValue == null ? '' : String(rawValue).trim()
            if (value.includes(',') || value.includes('"') || value.includes('\n')) {
                return `"${value.replace(/"/g, '""')}"`
            }
            return value
        })
        csv += values.join(',') + '\n'
    })

    return csv
}

onMounted(() => {
    fetchData()
})
</script>

<style scoped>
.filter-container {
    margin-top: 10px;
    margin-bottom: 0px;
    margin-left: 5px;
    text-align: left;
    width: 100%;
}

.filter-background {
    background-color: white;
    padding: 15px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

:deep(.t-form__item) {
    margin-top: 8px;
    margin-bottom: 8px;
}
</style>