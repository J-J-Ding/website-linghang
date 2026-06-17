#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块验证正则表达式
"""

import re

def is_valid_module_page_title_format(module_str):
    """简化版本"""
    if not isinstance(module_str, str) or not module_str.strip():
        return ""
    pattern = r'^M[\d.]+-(.*)$'
    match = re.match(pattern, module_str)
    if match:
        return match.group(1)
    else:
        return ""

# 测试用例
test_cases = [
    "M001-PRTC_MODE 模块",
    "M002-PRTC_AOSD 模块",
    "M001-数据备份处理",
    "M007.3-CRYPT_DOMAIN_FSM_DECRYPT 模块",
    "C-F023-PRTC 组件",
    "SC001-数据处理",
    "临时数据",
    "消息处理模块",
]

print("=" * 80)
print("测试 is_valid_module_page_title_format 函数")
print("=" * 80)

for title in test_cases:
    result = is_valid_module_page_title_format(title)
    status = "✅ VALID" if result else "❌ INVALID"
    print(f"{status}: '{title}' → '{result}'")
