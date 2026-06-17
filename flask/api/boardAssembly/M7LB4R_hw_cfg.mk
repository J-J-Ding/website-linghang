# 单板名，实际单板填写
export _BRD_NAME=M3LB4R

# 单板模型 sl:分离线路板; sc：分离客户板; mn:合一无frm; mf:合一有frm
export _MDL_TYPE=sl
 
# 重要数据是否需要扩展 need/no
export _PRTC_NEED_EXTEND=no

# 是否是osu fg单板, hxl中会增加宏定义，支持osu业务填写osu, 支持fg业务填写fg, 不支持osu，fg填none
export _BOARD_SUPPORT_FG_OSU_=none

# 光模块驱动库种类：otc_10g 或者 otc_100g 或者 otc_10g otc_100g
export _OTC_TYPE_= otc_100g

# 光模块种类：c04m4 c08m1 cd1x
export _OTC_100G_LIST_ = c04m4 c08m1 cd1x

# 下背板芯片种类：支线路合一单板填写 bp_none
export _BP_NAME_=zx242300

# 业务芯片种类： 编译ut写 def; 300分离单板: 线路侧填 zx300_line, 客户侧填 zx300_client; 合一无frm单板:otc_v1
export _FRM_NAME_=zx300_line

# 单板支持的时钟芯片种类，这里面可以写多个，用空格隔开
export _CLK_TYPE_= ncs23347

# 单板支持的 cdr 类型，没有的填写 cdr_none 
export _GEARBOX_TYPE_=cdr_none

# 单板dl层芯片名 注意加双引号, 300frm 写"zx242300", 支线路合一无frm写"otc"
export _DL_FRM_NAME_="zx242300"
export _DL_BP_NAME_="zx242300"

# nvr功能 不支持填 nvr_none, 支持填 nvr_support
export _NVR_SUPPORT_=nvr_none

# 该单板发货版本，代码自动生成模块选择 如omp5线路侧板子(oam_res_zx300 irq_zx300_line prtc_zx300 ct_zx300 gcc_zx300)
# 模块规则：模块_spec文件路径关键字 oam_res_zx300--表示oam模块，ubf中sepc路径关键字 res_zx300
export _ATUO_GEN_WK_MODE_=oam_res_zx300 irq_res_zx300_line prtc_res_zx300 ct_res_zx300 esc_res_zx300 dm_res_zx300

# OAM模块包含OAM和BP_OAM，对于两者第一级模块关键字是相同的都是res_zx300，
# 但是，对于BP_OAM来说，同一个芯片可能存在两种背板连接，例如zx300，分 300和double300 表示单芯片和双芯片
# 因此 对于bp-oam来说，除了提供 _ATUO_GEN_WK_MODE_外，还要提供子模块名称
export _AUTO_GEN_WK_OAM_BP_SUB_MODE_=300

# CPU类型
export BD_CPU_TYPE=_CPU_ARM64_FT

