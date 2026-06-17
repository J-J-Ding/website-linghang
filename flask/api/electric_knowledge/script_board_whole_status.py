import requests
import logging
from typing import List

# 配置
BASE_URL = "http://10.239.69.183:3001"
EMP_NO = "10305454"


HEADERS = {
    "X-Emp-No": EMP_NO,
    "Content-Type": "application/json"
}


def update_board_global_status():
    """更新所有单板的全局状态数据"""
    try:
        print("正在查询单板列表...")
        response = requests.get(f"{BASE_URL}/api/electric_knowledge/front_board_tree_data_service/queryBoardTreeByParams", headers=HEADERS)
        response.raise_for_status()
        data = response.json().get("data")

        if not isinstance(data, list):
            print("返回数据格式错误：期望为列表")
            return

        board_list = [item["board"] for item in data if item.get("board")]
        print(f"共获取到 {len(board_list)} 个单板")

        for board in board_list:
            payload = {"board": board}
            print(f"正在更新单板状态: {board}")
            resp = requests.post(f"{BASE_URL}/api/electric_knowledge/front_board_whole_status_data_service/update_board_whole_st_data", headers=HEADERS, json=payload)
            resp.raise_for_status()
            print(f"单板 {board} 状态更新成功")

        print("所有单板全局状态更新完成！")
    except requests.RequestException as e:
        print(f"HTTP 请求失败: {e}")
    except Exception as e:
        print(f"更新单板状态时发生错误: {e}")


def update_feature_link():
    """更新特性&子特性的特性树链接"""
    try:
        print("正在同步特性树链接（feature）...")
        payload = {"data_type": "feature"}
        response = requests.post(f"{BASE_URL}/api/electric_knowledge/front_feature_relation_data_service/syncFeatureIcenterPage", headers=HEADERS, json=payload)
        response.raise_for_status()
        print("特性树链接同步成功！")
    except requests.RequestException as e:
        print(f"同步特性树链接时 HTTP 请求失败: {e}")
    except Exception as e:
        print(f"同步特性树链接时发生未知错误: {e}")


def update_board_plan_link():
    """更新单板的单板方案链接"""
    try:
        print("正在同步单板方案链接（board）...")
        payload = {"data_type": "board"}
        response = requests.post(f"{BASE_URL}/api/electric_knowledge/front_board_tree_data_service/syncBoardIcenterPage", headers=HEADERS, json=payload)
        response.raise_for_status()
        print("单板方案链接同步成功！")
    except requests.RequestException as e:
        print(f"同步单板方案链接时 HTTP 请求失败: {e}")
    except Exception as e:
        print(f"同步单板方案链接时发生未知错误: {e}")


def run_all_updates():
    """执行所有需要运行的更新操作（目前只有单板状态更新）"""
    update_board_global_status()
    update_feature_link()
    update_board_plan_link()


def main():
    run_all_updates()


if __name__ == "__main__":
    main()