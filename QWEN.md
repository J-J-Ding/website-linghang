## Qwen Added Memories

- 数据库表新增字段的完整开发流程包括：1) 在数据库操作函数（如 test_sql_control）中添加表创建逻辑；2) 更新 TABLE_CONFIG_MAP 以包含新表配置；3) 在前端创建对应的页面组件（如 cpu.vue）以支持表的交互操作。本次完成了 CPU 表的开发，包含字段：子卡型号（主键）、子卡 ID、CPU 架构、DRAM 容量、支持主控。
