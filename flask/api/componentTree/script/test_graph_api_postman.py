#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件知识图谱 API 命令行测试工具
使用方式：python test_graph_api_postman.py
"""

import requests
import json
from datetime import datetime

# API 配置
BASE_URL = "http://10.239.69.183:3030"
API_PATH = "/api/api_data"

# 测试参数
TEST_PARAMS = {
    "seedComponentId": "C-F023-PRTC 组件",
    "scope": "L1",
    "maxDepth": 2,
    "forceRefresh": False,
    "operatorPerson": "测试用户"
}


def print_separator(char="=", length=80):
    """打印分隔线"""
    print(char * length)


def print_json(title, data, indent=2):
    """格式化打印 JSON"""
    print(f"\n{title}:")
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def test_get_graph(params=None):
    """测试获取图谱 API"""
    if params is None:
        params = TEST_PARAMS
    
    print_separator()
    print(f"[测试] 获取组件知识图谱")
    print_separator()
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {BASE_URL}{API_PATH}/API_Knowledge_component_graph_get")
    print(f"方法：POST")
    print_json("请求参数", params)
    print()
    
    try:
        start_time = datetime.now()
        
        # 发送 POST 请求
        response = requests.post(
            f"{BASE_URL}{API_PATH}/API_Knowledge_component_graph_get",
            json=params,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        
        print(f"响应状态码：{response.status_code}")
        print(f"请求耗时：{duration:.2f}ms")
        
        # 解析响应
        try:
            result = response.json()
            
            if response.status_code == 200 and result.get("code") == 200:
                print_separator("=", 80)
                print("✅ 请求成功!")
                print_separator("=", 80)
                
                data = result.get("data", {})
                print(f"\n📊 图谱统计:")
                print(f"  - 种子组件：{data.get('seedComponentName', 'N/A')}")
                print(f"  - 节点总数：{data.get('totalNodes', 0)}")
                print(f"  - 边总数：{data.get('totalEdges', 0)}")
                print(f"  - 图谱状态：{data.get('status', 'N/A')}")
                print(f"  - 生成时间：{data.get('generatedAt', 'N/A')}")
                print(f"  - 过期时间：{data.get('expiresAt', 'N/A')}")
                
                # 显示前 5 个节点
                nodes = data.get("nodes", [])
                if nodes:
                    print(f"\n📍 节点列表 (前 5 个):")
                    for i, node in enumerate(nodes[:5], 1):
                        print(f"  {i}. [{node.get('type', 'N/A')}] {node.get('name', 'N/A')}")
                
                # 显示前 5 个边
                edges = data.get("edges", [])
                if edges:
                    print(f"\n🔗 边列表 (前 5 个):")
                    for i, edge in enumerate(edges[:5], 1):
                        print(f"  {i}. {edge.get('source', 'N/A')} --[{edge.get('relationLabel', 'N/A')}]--> {edge.get('target', 'N/A')}")
                
                # 保存完整响应到文件
                output_file = f"graph_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 完整响应已保存到：{output_file}")
                
                return True
            else:
                print_separator("!", 80)
                print("❌ 请求失败!")
                print_separator("!", 80)
                print(f"错误码：{result.get('code', 'N/A')}")
                print(f"错误信息：{result.get('message', 'N/A')}")
                print_json("完整响应", result)
                return False
                
        except json.JSONDecodeError as e:
            print(f"\n❌ 响应解析失败：{e}")
            print(f"原始响应：{response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 连接错误：{e}")
        print(f"请检查后端服务是否启动在 {BASE_URL}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"\n❌ 请求超时：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试用例"""
    print("\n" + "=" * 80)
    print("🚀 开始批量测试组件知识图谱 API")
    print("=" * 80 + "\n")
    
    test_cases = [
        {
            "name": "测试用例 1: 使用 title 查询",
            "params": {
                "seedComponentId": "C-F023-PRTC 组件",
                "scope": "L1",
                "maxDepth": 2
            }
        },
        {
            "name": "测试用例 2: 使用 node_id 查询",
            "params": {
                "seedComponentId": "a6fa84ef6e7511f080eaf9504434accd",
                "scope": "L1",
                "maxDepth": 2
            }
        },
        {
            "name": "测试用例 3: 强制刷新",
            "params": {
                "seedComponentId": "C-F023-PRTC 组件",
                "scope": "L1",
                "maxDepth": 2,
                "forceRefresh": True
            }
        },
        {
            "name": "测试用例 4: 深度为 1",
            "params": {
                "seedComponentId": "C-F023-PRTC 组件",
                "scope": "L1",
                "maxDepth": 1
            }
        },
        {
            "name": "测试用例 5: 深度为 3",
            "params": {
                "seedComponentId": "C-F023-PRTC 组件",
                "scope": "L1",
                "maxDepth": 3
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"📋 {test_case['name']}")
        print(f"{'=' * 80}")
        
        success = test_get_graph(test_case["params"])
        results.append({
            "name": test_case["name"],
            "success": success,
            "params": test_case["params"]
        })
        
        # 等待 1 秒
        import time
        time.sleep(1)
    
    # 打印测试总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"总测试数：{len(results)}")
    print(f"成功数：{sum(1 for r in results if r['success'])}")
    print(f"失败数：{sum(1 for r in results if not r['success'])}")
    print(f"成功率：{sum(1 for r in results if r['success']) / len(results) * 100:.2f}%")
    
    print("\n详细结果:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['name']}")


def check_connectivity():
    """检查 API 连通性"""
    print("\n🔍 检查 API 连通性...")
    print(f"API 地址：{BASE_URL}{API_PATH}/API_Knowledge_component_graph_get")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PATH}/API_Knowledge_component_graph_get",
            json={"seedComponentId": "test", "scope": "L1"},
            timeout=5
        )
        
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 405:
            print("❌ 错误：405 Method Not Allowed")
            print("   请检查请求方法是否为 POST")
        elif response.status_code == 400:
            print("✅ API 可访问，但参数不正确（这是预期的）")
        elif response.status_code == 200:
            print("✅ API 正常工作")
        else:
            print(f"⚠️  未知状态码：{response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 API 服务器：{BASE_URL}")
        print("   请检查后端服务是否启动")
    except Exception as e:
        print(f"❌ 检查失败：{e}")


def show_help():
    """显示帮助信息"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           组件知识图谱 API 命令行测试工具                        ║
╠════════════════════════════════════════════════════════════════╣
║  使用方法:                                                      ║
║  python test_graph_api_postman.py [选项]                        ║
╠════════════════════════════════════════════════════════════════╣
║  选项:                                                          ║
║  (无参数)              运行默认测试                             ║
║  --all                运行所有测试用例                          ║
║  --check              检查 API 连通性                             ║
║  --help               显示帮助信息                              ║
╠════════════════════════════════════════════════════════════════╣
║  示例:                                                          ║
║  python test_graph_api_postman.py                               ║
║  python test_graph_api_postman.py --all                         ║
║  python test_graph_api_postman.py --check                       ║
╚════════════════════════════════════════════════════════════════╝
    """)


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--all":
            run_all_tests()
        elif arg == "--check":
            check_connectivity()
        elif arg == "--help":
            show_help()
        else:
            print(f"未知参数：{arg}")
            show_help()
    else:
        # 默认运行单个测试
        test_get_graph()


if __name__ == "__main__":
    main()
