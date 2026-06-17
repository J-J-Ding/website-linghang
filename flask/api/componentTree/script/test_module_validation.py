#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块验证函数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from componentTree.component_know_daily_data import is_valid_module_page_title_format

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
