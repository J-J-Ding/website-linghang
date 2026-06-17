#!/bin/bash

# gen_one_board.sh - 生成单板目录结构
# 用法: ./gen_one_board.sh <单板名称>
# 示例: ./gen_one_board.sh M1C2R

set -e  # 遇到错误立即退出

# ================================
# 颜色和输出函数
# ================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# ================================
# 配置和常量
# ================================
## 用于生成通用框架
readonly SOURCE_PRIVATE_RELATIVE_PATH="01_universal_framework/private"
readonly SCRIPT_NAME=$(basename "$0")

## 用于将私有硬件配置复制到私有代码 如 芯片类型 CPU类型 等
readonly HW_CONFIG_RELATIVE_PATH="05_assembly_config/"$1"_hw_cfg.mk"
readonly TARGET_HW_CONFIG_NAME="hw_cfg.mk"

## 用于将不同单板类型及芯片类型的私有单板spec的格式不一样，基于不同模式拷贝不同spec到私有代码
readonly CUSTOM_SPEC_TEMPLATE_RELATIVE_PATH="04_specialed_template/01_custom_spec_template"
readonly TARGET_BOARD_CONFIG_DIR="private/usr_hxl/hxl_code/custom_spec"
# 支持的模板模式
declare -A SUPPORTED_MODES=(
    ["stub_mode"]="stub_mode_custom_spec"
    ["zx300_mode"]="zx300_mode_custom_spec"
)

## 用于将编译路径从单板组装工厂拷贝的目标单板的私有代码中
readonly COMPILE_SCRIPT_RELATIVE_PATH="04_specialed_template/02_gen_compile_dir_script"
readonly TARGET_DL_COMPILE_DIR="private/usr_hxl/manul/dl_compile_cfg"
readonly TARGET_UBF_COMPILE_DIR="private/usr_hxl/manul/ubf_compile_cfg"

# ================================
# 核心功能函数
# ================================

# 显示用法信息
show_usage() {
    echo ""
    echo "用法01: $SCRIPT_NAME <单板名称>"
    echo "示例01: $SCRIPT_NAME M1C2R"
    echo "功能01: 在 assemble_factory 同级目录创建单板文件夹，并拷贝 private 目录"
    echo ""
    echo "用法02: $SCRIPT_NAME <单板名称> clean"
    echo "示例02: $SCRIPT_NAME M1C2R clean"
    echo "功能02: 在 assemble_factory 同级目录<单板名称>文件夹中删除 private 目录"
    echo ""
    exit 1
}
show_clean_usage() {
    echo ""
    echo "用法02: $SCRIPT_NAME <单板名称> clean"
    echo "示例02: $SCRIPT_NAME M1C2R clean"
    echo "功能02: 在 assemble_factory 同级目录<单板名称>文件夹中删除 private 目录"
    echo ""
    exit 1
}

# 验证参数
validate_arguments() {
    local board_name="$1"
    local mode="$2"
    
    if [ $# -ne 2 ]; then
        print_error "请提供单板名称作为参数"
        show_usage
    fi

    # 验证单板名称格式
    # if ! echo "$board_name" | grep -qE '^[A-Z0-9]+$'; then
    #     print_error "单板名称格式错误: $board_name"
    #     print_error "单板名称应只包含大写字母和数字"
    #     exit 1
    # fi

    # 验证模式参数
    if [[ -z "${SUPPORTED_MODES[$mode]}" ]]; then
        print_error "不支持的模板模式: $mode"
        print_error "支持的模板模式: ${!SUPPORTED_MODES[@]}"
        exit 1
    fi
}

# 计算目录路径
calculate_paths() {
    local board_name="$1"
    local mode="$2"
    
    # 获取脚本所在目录的绝对路径
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # print_debug "脚本目录: $script_dir"

    # 计算 assemble_factory 目录的绝对路径
    local assemble_factory_dir="$(dirname "$script_dir")"
    # print_debug "assemble_factory 目录: $assemble_factory_dir"

    # 计算项目根目录（assemble_factory 的父目录）
    local project_root="$(dirname "$assemble_factory_dir")"
    # print_debug "项目根目录: $project_root"

    # 定义源目录和目标目录
    local source_private_dir="$assemble_factory_dir/$SOURCE_PRIVATE_RELATIVE_PATH"
    local source_hw_config="$assemble_factory_dir/$HW_CONFIG_RELATIVE_PATH"
    local source_spec_template_dir="$assemble_factory_dir/$CUSTOM_SPEC_TEMPLATE_RELATIVE_PATH/${SUPPORTED_MODES[$mode]}"
    local source_dl_temp_dir="$assemble_factory_dir/$COMPILE_SCRIPT_RELATIVE_PATH/dl_compile_cfg/dl_temp_mk"
    local source_ubf_temp_dir="$assemble_factory_dir/$COMPILE_SCRIPT_RELATIVE_PATH/ubf_compile_cfg/ubf_temp_mk"

    local target_board_dir="$project_root/$board_name"
    local target_private_dir="$target_board_dir/private"
    local target_hw_config="$target_private_dir/$TARGET_HW_CONFIG_NAME"
    local target_board_config_spec_dir="$target_board_dir/$TARGET_BOARD_CONFIG_DIR"    
    local target_dl_compile_dir="$target_board_dir/$TARGET_DL_COMPILE_DIR"
    local target_ubf_compile_dir="$target_board_dir/$TARGET_UBF_COMPILE_DIR"

    # 返回路径信息
    echo "$source_private_dir:$target_board_dir:$target_private_dir:$project_root:$source_hw_config:$target_hw_config:$source_spec_template_dir:$target_board_config_spec_dir:$source_dl_temp_dir:$target_dl_compile_dir:$source_ubf_temp_dir:$target_ubf_compile_dir:$assemble_factory_dir"
}

# 检查源目录是否存在
check_source_directory() {
    local source_dir="$1"
    
    if [ ! -d "$source_dir" ]; then
        print_error "源目录不存在: $source_dir"
        print_error "请检查目录结构是否正确"
        exit 1
    fi
    print_info "  - 源 private 目录: $source_dir"
}

# 检查硬件配置文件是否存在
check_hardware_config() {
    local source_hw_config="$1"
    
    if [ ! -f "$source_hw_config" ]; then
        print_error "硬件配置文件不存在: $source_hw_config"
        print_error "请检查文件是否存在或路径是否正确"
        exit 1
    fi
    print_info "  - 源硬件配置文件: $source_hw_config"
}

# 检查模板目录是否存在
check_spec_template_directory() {
    local source_spec_template_dir="$1"
    local mode="$2"
    
    if [ ! -d "$source_spec_template_dir" ]; then
        print_error "模板目录不存在: $source_spec_template_dir"
        print_error "请检查 $mode 模式对应的模板目录是否正确配置"
        exit 1
    fi
    print_info "  - 源模板目录: $source_spec_template_dir"
    
    # 检查模板目录是否为空
    if [ -z "$(ls -A "$source_spec_template_dir")" ]; then
        print_warn "模板目录为空: $source_spec_template_dir"
    else
        local template_files_count=$(find "$source_spec_template_dir" -type f | wc -l)
        print_info "  - 模板文件数量: $template_files_count"
    fi
}

check_compile_template_directories() {
    local source_dl_temp_dir="$1"
    local source_ubf_temp_dir="$2"
    
    # 检查 DL 编译模板目录
    if [ ! -d "$source_dl_temp_dir" ]; then
        print_error "DL编译模板目录不存在: $source_dl_temp_dir"
        print_error "请检查目录结构是否正确"
        exit 1
    fi
    print_info "  - 源DL编译模板目录: $source_dl_temp_dir"
    
    # 检查 UBF 编译模板目录
    if [ ! -d "$source_ubf_temp_dir" ]; then
        print_error "UBF编译模板目录不存在: $source_ubf_temp_dir"
        print_error "请检查目录结构是否正确"
        exit 1
    fi
    print_info "  - 源UBF编译模板目录: $source_ubf_temp_dir"
    
    # 检查目录内容
    local dl_files_count=$(find "$source_dl_temp_dir" -name "*.mk" -type f | wc -l)
    local ubf_files_count=$(find "$source_ubf_temp_dir" -name "*.mk" -type f | wc -l)
    
    print_info "  - DL编译模板文件数量: $dl_files_count"
    print_info "  - UBF编译模板文件数量: $ubf_files_count"
}

# 处理目标目录存在的情况
handle_existing_target() {
    local target_dir="$1"
    
    if [ -d "$target_dir" ]; then
        print_warn "  - 目标目录已存在: $target_dir"
        read -p "是否覆盖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "  - 操作已取消"
            exit 0
        fi
        print_warn "  - 覆盖现有目录..."
    fi
}

# 创建目录结构
create_directory_structure() {
    local target_board_dir="$1"
    local source_private_dir="$2"
    local target_private_dir="$3"
    
    print_info "创建单板目录: $target_board_dir"
    mkdir -p "$target_board_dir"

    print_info "拷贝 private 目录到目标位置..."
    if cp -r "$source_private_dir" "$target_board_dir/"; then
        print_info "拷贝成功"
    else
        print_error "拷贝失败"
        exit 1
    fi
}

# 拷贝并重命名硬件配置文件
copy_and_rename_hardware_config() {
    local source_hw_config="$1"
    local target_hw_config="$2"
    
    print_info "拷贝硬件配置文件..."
    
    if [ ! -f "$source_hw_config" ]; then
        print_error "源硬件配置文件不存在: $source_hw_config"
        return 1
    fi
    
    # 拷贝并重命名文件
    if cp "$source_hw_config" "$target_hw_config"; then
        print_info "硬件配置文件拷贝成功: $target_hw_config"
        
        # 显示文件信息
        local file_size=$(stat -c%s "$target_hw_config" 2>/dev/null || stat -f%z "$target_hw_config")
        print_info "文件大小: ${file_size} 字节"
        
        return 0
    else
        print_error "硬件配置文件拷贝失败"
        return 1
    fi
}

# 根据硬件的配置xxx_hw_cfg.mk 将spec中的 frm_name, bp_type, pcc_type 进行修改
update_spec_mode_template()
{
    local mode="$1"
    local source_board_des_spec="$2/board_config/board_des.spec"
    local source_hw_config="$3"
    local update_spec_by_hw_cfg="$(pwd)/update_spec_by_hw_cfg.sh"

    # print_info "mode: $mode"
    # print_info "source_board_des_spec: $source_board_des_spec"
    # print_info "source_hw_config: $source_hw_config"
    # print_info "update_spec_by_hw_cfg: $update_spec_by_hw_cfg"

    print_info "==0301==chmod +x update_spec_by_hw_cfg"
    chmod +x $update_spec_by_hw_cfg
    
    print_info "==0302==update_spec_by_hw_cfg"
    if [[ $mode == "zx300_mode" ]]; then
        $update_spec_by_hw_cfg "$source_board_des_spec" "$source_hw_config"
    fi

}

# 拷贝模式模板文件
copy_spec_mode_template() {
    local source_spec_template_dir="$1"
    local target_board_config_dir="$2"
    local mode="$3"
    
    print_info "==0401==开始拷贝 $mode 模式模板文件..."
    
    # # 创建目标目录
    # mkdir -p "$target_board_config_dir"
    
    # # 检查源目录是否有内容
    # if [ -z "$(ls -A "$source_spec_template_dir")" ]; then
    #     print_warn "模板源目录为空，跳过模板拷贝"
    #     return 0
    # fi
    
    print_info "  - 从 $source_spec_template_dir"
    print_info "  - 拷贝到 $target_board_config_dir"
    
    # 拷贝所有模板文件
    if cp -r "$source_spec_template_dir"/* "$target_board_config_dir"/ 2>/dev/null; then
        local copied_files=$(find "$target_board_config_dir" -type f | wc -l)
        print_info "==0402==模式模板拷贝成功: 拷贝了 $copied_files 个文件"
        
        # 显示拷贝的文件列表
        print_info "==0403==拷贝的模板文件:"
        find "$target_board_config_dir" -type f -exec basename {} \; | while read -r file; do
            print_info "  - $file"
        done
        
        return 0
    else
        print_error "模式模板拷贝失败"
        return 1
    fi
}

## 脚本生成temp的mk文件
generate_compile_mk_temp_file() {
    local dl_script_dir="$1"
    local ubf_script_dir="$2"

    # print_info "dl目录: $dl_script_dir"
    # print_info "dl目录: $ubf_script_dir"

    # 输入参数验证
    if [[ -z "$dl_script_dir" ]]; then
        print_info "错误: dl_script_dir 绝对路径不能为空"
        return 1
    fi
    
    if [[ ! -d "$dl_script_dir" ]]; then
        print_info "错误: 目录不存在: $dl_script_dir"
        return 1
    fi
    
     if [[ -z "$ubf_script_dir" ]]; then
        print_info "错误: ubf_script_dir 绝对路径不能为空"
        return 1
    fi
    
    if [[ ! -d "$ubf_script_dir" ]]; then
        print_info "错误: 目录不存在: $ubf_script_dir"
        return 1
    fi

    # 构建 auto_gen_dl_h_dir_top.sh/auto_gen_dl_so_dir_top 的路径
    local auto_gen_dl_h_dir_top="$dl_script_dir/auto_gen_dl_h_dir_top.sh"
    local auto_gen_dl_so_dir_top="$dl_script_dir/auto_gen_dl_so_dir_top.sh"
    chmod +x "$dl_script_dir"/*.sh

    # 构建 auto_gen_ubf_h_dir_top.sh/auto_gen_ubf_so_dir_top 的路径
    local auto_gen_ubf_h_dir_top="$ubf_script_dir/auto_gen_ubf_h_dir_top.sh"
    local auto_gen_ubf_so_dir_top="$ubf_script_dir/auto_gen_ubf_so_dir_top.sh"
    chmod +x "$ubf_script_dir"/*.sh
       
    # 调用脚本
    print_info "正在调用auto_gen_dl_h_dir_top: 脚本生成.mk"
    "$auto_gen_dl_h_dir_top" "$dl_script_dir"
    print_info "正在调用auto_gen_dl_so_dir_top: 脚本生成.mk"
    "$auto_gen_dl_so_dir_top" "$dl_script_dir"
    print_info "正在调用auto_gen_ubf_h_dir_top: 脚本生成.mk"
    "$auto_gen_ubf_h_dir_top" "$ubf_script_dir"
    print_info "正在调用auto_gen_ubf_so_dir_top: 脚本生成.mk"
    "$auto_gen_ubf_so_dir_top" "$ubf_script_dir"
    
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        print_info "错误: auto_gen_ubf_h_dir_top.sh 执行失败，退出码: $exit_code"
        return $exit_code
    fi
    
    print_info "auto_gen_ubf_h_dir_top.sh 执行成功"
    return 0
}

## 拷贝编译路径的mk文件到目标单板
copy_compile_config_files() {
    local source_dl_temp_dir="$1"
    local target_dl_compile_dir="$2"
    local source_ubf_temp_dir="$3"
    local target_ubf_compile_dir="$4"
    
    print_info "开始拷贝编译配置文件..."
    
    # 创建目标目录
    # mkdir -p "$target_dl_compile_dir"
    # mkdir -p "$target_ubf_compile_dir"
    
    local dl_copied_count=0
    local ubf_copied_count=0
    
    # 拷贝 DL 编译配置文件 (*.mk)
    if [ -d "$source_dl_temp_dir" ] && [ -n "$(ls -A "$source_dl_temp_dir"/*.mk 2>/dev/null)" ]; then
        print_info "拷贝 DL 编译配置文件..."
        for mk_file in "$source_dl_temp_dir"/*.mk; do
            if [ -f "$mk_file" ]; then
                local filename=$(basename "$mk_file")
                if cp "$mk_file" "$target_dl_compile_dir/"; then
                    print_info "  - DL: $filename"
                    ((++dl_copied_count))
                else
                    print_error "  - DL: $filename 拷贝失败"
                fi
            fi
        done
    else
        print_warn "未找到 DL 编译模板文件 (*.mk)"
    fi

    # 拷贝 UBF 编译配置文件 (*.mk)
    if [ -d "$source_ubf_temp_dir" ] && [ -n "$(ls -A "$source_ubf_temp_dir"/*.mk 2>/dev/null)" ]; then
        print_info "拷贝 UBF 编译配置文件..."
        for mk_file in "$source_ubf_temp_dir"/*.mk; do
            if [ -f "$mk_file" ]; then
                local filename=$(basename "$mk_file")
                if cp "$mk_file" "$target_ubf_compile_dir/"; then
                    print_info "  - UBF: $filename"
                    ((++ubf_copied_count))
                else
                    print_error "  - UBF: $filename 拷贝失败"
                fi
            fi
        done
    else
        print_warn "未找到 UBF 编译模板文件 (*.mk)"
    fi
    
    print_info "编译配置文件拷贝完成: DL($dl_copied_count 个文件) UBF($ubf_copied_count 个文件)"
    
    if [ $dl_copied_count -eq 0 ] && [ $ubf_copied_count -eq 0 ]; then
        print_warn "未拷贝任何编译配置文件"
        return 1
    fi
    
    return 0
}

## 拷贝重要数据模版文件到 ubf
copy_imdt_mode_template() {
    local board_name="$1"
    local auto_gen_imdt="$(pwd)/auto_gen_imdt.sh"

    print_info "==0501==chmod +x auto_gen_imdt.sh"
    chmod +x $auto_gen_imdt
    
    print_info "==0502==拷贝 $1 单板重要数据到UBF"
    $auto_gen_imdt  "$1"   

}

## 组装模型相关框架代码到目标单板路径
assemble_model_framework() {
    local hw_cfg_mk="$1"
    local src_brd_assemble_dir="$2"
    local dst_private_dir="$3"
    local assemble_model_framework="$(pwd)/assemble_modle_framework.sh"

    print_info "==0601==chmod +x assemble_modle_framework.sh"
    chmod +x $assemble_model_framework

    # print_info "==0602==组装模型相关框架代码到目标单板路径: "
    $assemble_model_framework "$hw_cfg_mk" "$src_brd_assemble_dir" "$dst_private_dir"
}

## 组装硬件及模型相关框架代码到目标单板路径
assemble_hardware_and_model_framework() {
    local hw_cfg_mk="$1"
    local src_brd_assemble_dir="$2"
    local dst_private_dir="$3"
    local assemble_hw_framework="$(pwd)/assemble_hw_framework.sh"

    print_info "==0701==chmod +x assemble_hw_framework.sh"   
    chmod +x $assemble_hw_framework

    # print_info "==0702==组装硬件及模型相关框架代码到目标单板路径: " 
    $assemble_hw_framework "$hw_cfg_mk" "$src_brd_assemble_dir" "$dst_private_dir"
}

# 验证操作结果
verify_operation() {
    local target_private_dir="$1"
    local project_root="$2"
    local board_name="$3"
    local target_hw_config="$4"
    
    if [ -d "$target_private_dir" ]; then
        print_info "验证成功: private 目录已正确拷贝到 $target_private_dir"
        
        # 显示拷贝的文件数量
        local file_count=$(find "$target_private_dir" -type f | wc -l)
        print_info "拷贝的文件数量: $file_count"
        
        # 检查硬件配置文件
        if [ -f "$target_hw_config" ]; then
            print_info "硬件配置文件验证成功: $(basename "$target_hw_config")"
        else
            print_warn "硬件配置文件未找到: $(basename "$target_hw_config")"
        fi
        
        # # 显示目录结构
        # print_info "生成的目录结构:"
        # echo "$project_root/"
        # echo "├── assemble_factory/"
        # echo "└── $board_name/"
        # echo "    └── private/"
        # echo "        ├── ... (其他文件)"
        # echo "        └── $TARGET_HW_CONFIG_NAME"
        
    else
        print_error "验证失败: private 目录未正确创建"
        exit 1
    fi
}

# 创建生成记录
create_generation_record() {
    local target_board_dir="$1"
    local board_name="$2"
    local source_private_dir="$3"
    local source_hw_config="$4"
    local mode="$5"
    local source_spec_template_dir="$6"
    local source_dl_temp_dir="$7"
    local source_ubf_temp_dir="$8"
    
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    cat > "$target_board_dir/generation_info.txt" << EOF
生成时间: $timestamp
单板名称: $board_name
源目录: $source_private_dir
硬件配置文件: $source_hw_config -> $TARGET_HW_CONFIG_NAME
SPEC模板目录: $source_spec_template_dir -> $TARGET_BOARD_CONFIG_DIR
DL模板: $source_dl_temp_dir ($dl_mk_files 个文件) -> $TARGET_DL_COMPILE_DIR
UBF模板: $source_ubf_temp_dir ($ubf_mk_files 个文件) -> $TARGET_UBF_COMPILE_DIR
生成脚本: $SCRIPT_NAME
EOF
    
    print_info "生成信息已保存到: $target_board_dir/generation_info.txt"
}

# 显示完成信息
show_completion_message() {
    local board_name="$1"
    local target_board_dir="$2"
    
    print_info "单板 $board_name 目录生成完成!"
    print_info "目标位置: $target_board_dir"
}

# ================================
# 主函数
# ================================

main() {
    local board_name="$1"
    local mode="zx300_mode"

    if [[ "$2" == "stub" ]]; then
        mode="stub_mode"
    fi
    print_info "====00==准备工作: $board_name (模式: $mode)"
    
    # 验证参数
    validate_arguments "$board_name" "$mode"
    
    # 计算路径
    local path_info=$(calculate_paths "$board_name" "$mode")    
    local source_private_dir=$(echo "$path_info" | cut -d: -f1)
    local target_board_dir=$(echo "$path_info" | cut -d: -f2)
    local target_private_dir=$(echo "$path_info" | cut -d: -f3)
    local project_root=$(echo "$path_info" | cut -d: -f4)
    local source_hw_config=$(echo "$path_info" | cut -d: -f5)
    local target_hw_config=$(echo "$path_info" | cut -d: -f6)
    local source_spec_template_dir=$(echo "$path_info" | cut -d: -f7)
    local target_board_config_dir=$(echo "$path_info" | cut -d: -f8)
    local source_dl_temp_dir=$(echo "$path_info" | cut -d: -f9)
    local target_dl_compile_dir=$(echo "$path_info" | cut -d: -f10)
    local source_ubf_temp_dir=$(echo "$path_info" | cut -d: -f11)
    local target_ubf_compile_dir=$(echo "$path_info" | cut -d: -f12)
    local source_boardassemble_dir=$(echo "$path_info" | cut -d: -f13)

    # 

    # 如果是clean则删除单板文件夹的内容并退出
    if [ "$2" == "clean" ]; then
        print_info "删除单板目录: $board_name"
        rm -rf $target_board_dir
        exit 0
    esle 
        show_clean_usage
        exit 1
    fi
    
    print_info "==0001==目标单板目录: $target_board_dir"
    print_info "==0002==单板组装框架源目录: "
    
    # 检查源目录
    check_source_directory "$source_private_dir"

     # 检查硬件配置文件
    check_hardware_config "$source_hw_config"

    # 检查模板目录
    check_spec_template_directory "$source_spec_template_dir" "$mode"
    
    # 处理目标目录存在的情况
    handle_existing_target "$target_board_dir"
    
    # 01-创建目标单板的通用框架：主要实现将组装框架中的通用private目录拷贝到目标单板目录
    print_info "====01====将单板框架中的通用private目录拷贝到目标单板目录: "
    create_directory_structure "$target_board_dir" "$source_private_dir" "$target_private_dir"

    # 02-目标单板的配置文件需要再单板组装框架里面描述，由组装框架自动拷贝到目标单板目录
    print_info "====02====将单板组装框架中的硬件配置文件拷贝到目标单板目录: "
    copy_and_rename_hardware_config "$source_hw_config" "$target_hw_config"
    
    #03-根据硬件的配置xxx_hw_cfg.mk 将spec中的 frm_name, bp_type, pcc_type 进行修改
    print_info "====03====根据硬件配置文件更新spec模板文件: "
    update_spec_mode_template "$mode" "$source_spec_template_dir" "$source_hw_config"

    # 04-自动将公共框架里面的custom里面的单板sepc的集中模式私有配置，拷贝/custom_spec/board_config目录下
    print_info "====04====自动将公共框架里面的更新后的sepc拷贝到目标单板目录: "
    copy_spec_mode_template "$source_spec_template_dir" "$target_board_config_dir" "$mode"

    # 05 -自动扫描xxx_hw_cfg.mk配置文件，根据配置文件中的_BRD_TYPE和 _PRTC_NEED_EXTEND变量，选择04_specialed_template 下面 03_gen_imdt_template下面的重要数据参数模版
    print_info "====05====根据硬件配置文件生成单板重要数据参数文件: "
    # 生成单板的重要数据参数，并写入ubf的单板重要数据参数文件 board_imdata_parameter.sh 
    # 注意生成的重要数据参数，是同类型单板的交集，是基础数据，每个单板重要数据需要根据单板实际情况再进行自行添加。
    copy_imdt_mode_template "$board_name"

    # 06-组装模型相关代码到目标单板目录
    print_info "====06====组装模型相关代码到目标单板目录: "
    assemble_model_framework "$source_hw_config" "$source_boardassemble_dir" "$target_private_dir"

    # 07-组装硬件及模型相关代码到目标单板目录
    print_info "====07====组装硬件及模型相关代码到目标单板目录: "
    assemble_hardware_and_model_framework "$source_hw_config" "$source_boardassemble_dir" "$target_private_dir"

    # 08-自动扫描UBF及驱动库的代码库，基于最新的代码库，更新源码编译所需要的源码路径和头文件路径
    print_info "====08====生成并拷贝源码编译路径配置文件到目标单板目录: "
    # 0801 调用 02_gen_compile_dir_script脚本生成源码编译所需要的源码路径和头文件路径的mk文件
    generate_compile_mk_temp_file "$source_dl_temp_dir/.." "$source_ubf_temp_dir/.."
    # 0802 拷贝编译配置文件
    copy_compile_config_files "$source_dl_temp_dir" "$target_dl_compile_dir" "$source_ubf_temp_dir" "$target_ubf_compile_dir"
    # 0803 删除临时目录中的mk文件
    rm -rf "$source_dl_temp_dir"/*.mk "$source_ubf_temp_dir"/*.mk

    # 验证操作结果
    print_info "====09====验证操作结果: "
    verify_operation "$target_private_dir" "$project_root" "$board_name" "$target_hw_config"
    
    # 创建生成记录
    print_info "====10====创建生成记录: "
    create_generation_record "$target_board_dir" "$board_name" "$source_private_dir" "$source_hw_config" "$mode" "$source_spec_template_dir" "$source_dl_temp_dir" "$source_ubf_temp_dir"
    
    # 显示完成信息
    print_info "====11====显示完成信息: "
    show_completion_message "$board_name" "$target_board_dir"
     
    return 0
}

# ================================
# 脚本入口点
# ================================

# 检查是否直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 如果没有提供参数，显示用法
    if [ $# -eq 0 ]; then
        show_usage
    fi
    main "$1" "$2"
fi
