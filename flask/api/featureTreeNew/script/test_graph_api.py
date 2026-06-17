"""
组件知识图谱 API 接口测试脚本
使用方法：
    python test_graph_api.py

前提条件：
    1. Flask 后端已启动（端口 3001）
    2. 数据库表已创建（执行 graph_schema.sql）
    3. 数据库中有测试数据（knowledge_component_tree 表）
"""

import requests
import json
import sys

# API 基础 URL
BASE_URL = "http://localhost:3001/api/api_data"

# 测试用的种子组件 ID（需要根据实际数据库数据修改）
TEST_SEED_COMPONENT_ID = "SC001-xxx"  # 请替换为实际的组件 ID
TEST_SCOPE = "L0"


def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def test_api_graph_get():
    """测试获取图谱接口"""
    print_separator("测试 1: API_Knowledge_component_graph_get - 获取图谱")
    
    url = f"{BASE_URL}/API_Knowledge_component_graph_get"
    payload = {
        "seedComponentId": TEST_SEED_COMPONENT_ID,
        "scope": TEST_SCOPE,
        "maxDepth": 2
    }
    
    print(f"请求 URL: {url}")
    print(f"请求参数：{json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 测试通过！")
                data = result.get("data", {})
                print(f"   - 种子组件：{data.get('seedComponentName', 'N/A')}")
                print(f"   - 节点总数：{data.get('totalNodes', 0)}")
                print(f"   - 边总数：{data.get('totalEdges', 0)}")
                print(f"   - 图谱状态：{data.get('status', 'N/A')}")
                return True
            else:
                print(f"\n❌ 测试失败：{result.get('message', 'Unknown error')}")
        else:
            print(f"\n❌ HTTP 错误：{response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败：无法连接到 Flask 服务器（端口 3001）")
        print("   请确保 Flask 后端已启动：cd flask/api && gunicorn -w 4 -b 0.0.0.0:3001 app:app")
    except Exception as e:
        print(f"\n❌ 发生错误：{str(e)}")
    
    return False


def test_api_graph_stats():
    """测试获取统计信息接口"""
    print_separator("测试 2: API_Knowledge_component_graph_stats - 获取统计信息")
    
    # 首先需要有一个图谱 ID
    # 这里假设我们已经通过 test_api_graph_get 获取了图谱
    # 实际测试时需要先调用获取图谱接口
    
    print("⚠️  此测试需要先获取图谱 ID")
    print("   建议先运行 test_api_graph_get() 获取图谱数据")
    return False


def test_api_graph_layout_save():
    """测试保存布局接口"""
    print_separator("测试 3: API_Knowledge_component_graph_layout_save - 保存布局")
    
    url = f"{BASE_URL}/API_Knowledge_component_graph_layout_save"
    payload = {
        "graphId": 1,  # 需要替换为实际的图谱 ID
        "layoutName": "测试布局",
        "layoutType": "custom",
        "isDefault": False,
        "isPublic": False,
        "nodePositions": {
            "node1": {"x": 100, "y": 200},
            "node2": {"x": 300, "y": 400}
        },
        "operatorPerson": "test_user"
    }
    
    print(f"请求 URL: {url}")
    print(f"请求参数：{json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 测试通过！")
                return True
            else:
                print(f"\n❌ 测试失败：{result.get('message', 'Unknown error')}")
        else:
            print(f"\n❌ HTTP 错误：{response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 发生错误：{str(e)}")
    
    return False


def test_api_graph_layout_list():
    """测试获取布局列表接口"""
    print_separator("测试 4: API_Knowledge_component_graph_layout_list - 获取布局列表")
    
    url = f"{BASE_URL}/API_Knowledge_component_graph_layout_list"
    payload = {
        "graphId": 1,  # 需要替换为实际的图谱 ID
        "operatorPerson": "test_user"
    }
    
    print(f"请求 URL: {url}")
    print(f"请求参数：{json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 测试通过！")
                layouts = result.get("data", [])
                print(f"   - 布局数量：{len(layouts)}")
                for layout in layouts:
                    print(f"     * {layout.get('layoutName')} (默认：{layout.get('isDefault')})")
                return True
            else:
                print(f"\n❌ 测试失败：{result.get('message', 'Unknown error')}")
        else:
            print(f"\n❌ HTTP 错误：{response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 发生错误：{str(e)}")
    
    return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("  组件知识图谱 API 接口测试")
    print("=" * 80)
    print(f"\n测试环境：{BASE_URL}")
    print(f"测试组件：{TEST_SEED_COMPONENT_ID}")
    print(f"测试范围：{TEST_SCOPE}")
    
    results = []
    
    # 运行测试
    results.append(("获取图谱", test_api_graph_get()))
    # results.append(("获取统计信息", test_api_graph_stats()))
    # results.append(("保存布局", test_api_graph_layout_save()))
    # results.append(("获取布局列表", test_api_graph_layout_list()))
    
    # 打印测试报告
    print_separator("测试报告")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    # 检查测试配置
    if TEST_SEED_COMPONENT_ID == "SC001-xxx":
        print("⚠️  警告：测试组件 ID 未配置！")
        print("   请编辑 test_graph_api.py 文件，修改 TEST_SEED_COMPONENT_ID 和 TEST_SCOPE")
        print("   例如：")
        print("     TEST_SEED_COMPONENT_ID = 'SC001-SC_MP_IF 网管接口子组件设计'")
        print("     TEST_SCOPE = 'L0'")
        print()
        
        response = input("是否继续测试？(y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
        print()
    
    # 运行测试
    exit_code = run_all_tests()
    sys.exit(exit_code)
