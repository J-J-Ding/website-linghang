#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 iSpace URL 解析
"""

def get_pageid_spaceid(url):
    """
    从 iCenter/iSpace 页面 URL 中解析出页面 ID 和空间 ID
    """
    if not url.strip():
        return "", ""
    
    parts = url.split('/')
    print(f"URL: {url}")
    print(f"Parts: {parts}")
    print(f"Length: {len(parts)}")
    
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageid = parts[-2]
    
    print(f"spaceId_index: {spaceId_index}")
    print(f"spaceId: {spaceId}")
    print(f"pageid: {pageid}")
    print("-" * 80)
    
    return pageid, spaceId


if __name__ == '__main__':
    # 测试 iSpace URL
    test_urls = [
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/f9b7092aeca011f09d6fa9a20935cc4c/view",
        "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/5cb15320eca111f0b1d72140a229b5db/view",
    ]
    
    for url in test_urls:
        pageid, spaceId = get_pageid_spaceid(url)
        print(f"✅ 解析结果：spaceId={spaceId}, pageId={pageid}\n")
