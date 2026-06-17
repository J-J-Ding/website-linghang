#!/bin/bash
# 脚本：run_template_generator.sh
# 功能：运行模板生成器，传递C数据模型和JSON数据文件作为参数
# 设置脚本在遇到错误时退出
set -e
readonly SCRIPT_NAME=$(basename "$0")
show_script_usage() {
    echo "=============================================================================="
    echo "功能: 在单板名称对应的private 目录下替换单板的配置参数"
    echo "用法: $SCRIPT_NAME < para1: 单板名称> <para2: 操作指令> <para3:template是否自动生成>"
    echo "para1(单板名称):     M1C2R"
    echo "para2(单板模型):     sc(客户版)/sl(线路板)/mf(支线路有framer板)/mn(支线路无framer板)"
    echo "para3(操作指令):     gen_json/gen_data/gen_all"
    echo "para4(template是否自动生成): tmp_true/NONE"
    echo "=================================================================================="
    exit 1
}

## 单板名称
BOARD_NAME="$1"
echo " "
echo " "
echo "---------- BOARD_NAME: $BOARD_NAME"

## 单板业务模型
SVC_TYPE="$2"
echo "---------- SVC_TYPE: $SVC_TYPE"

## 操作指令 json/data/all
COMMAND_TYPE="$3"
echo "---------- COMMAND_TYPE: $COMMAND_TYPE"

## 请输入 tmp_true 如果需要 加template
TEMPLATE_VISIBLE=$4
echo "---------- TEMPLATE_VISIBLE: $TEMPLATE_VISIBLE"

if [ $# -lt 2 ]; then
        echo "================请提供单板名称与单板的业务模型作为参数"
        show_script_usage    
else
   # 校验参数2是否为允许的值
    case "$SVC_TYPE" in
        "sc"|"sl"|"mf"|"mn")
            echo "---------- 参数2校验通过，继续执行脚本..."
            ;;
        *)
            echo "================错误：参数2必须为sc/sl/mf/mn中的一种"
            show_script_usage
            ;;
    esac

  if [ $# -eq 2 ]; then
          COMMAND_TYPE="gen_all"
          TEMPLATE_VISIBLE=""
  else
      echo "---------- 参数数量正确，继续执行脚本..."
  fi
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "---------- SCRIPT_DIR: $SCRIPT_DIR"
# 定义Python脚本路径
# 图谱到JSON文件脚本
PATTERN_TO_JSON_PYTHON_SCRIPT="$SCRIPT_DIR/code/03_gen_json_data_from_kg/dst_json_data_generator.py"
# JSON到cfg_data脚本
JSON_TO_CFGDATA_PYTHON_SCRIPT="$SCRIPT_DIR/code/main.py"
## 等价于 SOFT/boardassemble  这个路径的绝对路径
BOARDASSEMLBLE_DIR="$SCRIPT_DIR/../.."
echo "---------- BOARDASSEMLBLE_DIR: $BOARDASSEMLBLE_DIR"
# 打印执行信息
echo "----------------------------------------"
###########增加判断条件
case "$COMMAND_TYPE" in
    "gen_json")
        echo "[INFO] 执行知识图谱 -> JSON 转换..."
        echo " "
        python3  -B "$PATTERN_TO_JSON_PYTHON_SCRIPT" -b "$BOARD_NAME" -m "$SVC_TYPE"
        ;;
    "gen_data")
        echo "[INFO] 执行 JSON -> C代码 转换..."
        echo " "
        python3  -B "$JSON_TO_CFGDATA_PYTHON_SCRIPT" "$BOARDASSEMLBLE_DIR" "$BOARD_NAME" "$TEMPLATE_VISIBLE"
        ;;
    "gen_all")
        echo "[INFO] ============ 执行全部流程：知识图谱 -> JSON -> C代码... ========="
        echo " "
        # 先执行知识图谱转 JSON
        python3  -B "$PATTERN_TO_JSON_PYTHON_SCRIPT" -b "$BOARD_NAME" -m "$SVC_TYPE"
        python3 -B "$JSON_TO_CFGDATA_PYTHON_SCRIPT" "$BOARDASSEMLBLE_DIR" "$BOARD_NAME" "$TEMPLATE_VISIBLE"
        ;;
    *)
        echo "[ERROR] 未知模式: $MODE"
        show_script_usage
        ;;
esac
# 检查执行是否成功
if [ $? -eq 0 ]; then
    echo "----------------------------------------"
    echo " "
    echo " "
    # echo "模板生成器执行成功!"
else
    echo "----------------------------------------"
    echo "模板生成器执行失败!"
    exit 1
fi
