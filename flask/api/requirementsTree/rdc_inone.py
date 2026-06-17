#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import requests
import json
import logging
from typing import List, Dict, Any

from requirementsTree.uac_token import get_uac_token


logger = logging.getLogger(__name__)


class RdcRepository:
    """RDC InOne API 仓库类"""

    # 基础 URL
    APP_CODE = "d09fddc101a14bb3bfa0fbd02ed1932a"
    BASE_URL = "https://inone.zte.com.cn/ZXRDCloud/RDCloud/zte-plm-wic-rest/api/rest/v1"

    def __init__(self, timeout: int = 20):
        """
        初始化 RDC 仓库

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        user_num, _ = get_uac_token()
        if not user_num:
            raise RuntimeError("获取 UAC token 失败，无法初始化 RdcRepository")
        self._user_num = user_num

    # ---- 实例方法（私有） ----

    def _get_headers(self, user_id: str) -> Dict[str, str]:
        """获取请求头"""
        return {
            "X-Tenant-Id": "ZTE",
            "X-Emp-No": user_id,
            "appcode": self.APP_CODE,
            "X-Lang-Id": "zh_CN",
            "Content-Type": "application/json",
        }

    def _get_relations(self, rdc_id: str, user_id: str) -> Dict[str, Any]:
        """
        查询 RDC 关联项

        Args:
            rdc_id: RDC 工作项 ID
            user_id: 用户工号 ID

        Returns:
            RDC 关联数据字典
        """
        url = f"{self.BASE_URL}/work_items/relations/query?workItemId={rdc_id}"
        headers = self._get_headers(user_id)

        logger.info(f"RDC InOne API 请求 | workItemId={rdc_id}")

        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"RDC InOne API 响应 | status={response.status_code}, 耗时={elapsed_ms:.2f}ms")

            result = response.json()
            logger.debug(f"响应体：{json.dumps(result, ensure_ascii=False)[:500]}...")
            return result

        except requests.exceptions.ConnectionError as e:
            logger.error(f"RDC InOne API 请求失败：{e}", exc_info=True)
            return {"status": f"请求异常：{e}"}
        except requests.exceptions.Timeout as e:
            logger.error(f"RDC InOne API 请求超时：{e}", exc_info=True)
            return {"status": f"请求超时：{e}"}
        except json.JSONDecodeError as e:
            logger.error(f"RDC InOne API 响应解析失败：{e}, body={response.text}", exc_info=True)
            return {"status": f"JSON 解析失败：{e}", "body": response.text}

    def _get_workitems_detail(self, rdc_id_list: List[str], user_id: str) -> Dict[str, Any]:
        """
        查询 RDC 工作项详情

        Args:
            rdc_id_list: RDC 工作项 ID 列表
            user_id: 用户工号 ID

        Returns:
            RDC 工作项详情字典
        """
        url = f"{self.BASE_URL}/work_items/query_workitems"
        headers = self._get_headers(user_id)

        logger.info(f"RDC InOne API 请求 | 工作项数量={len(rdc_id_list)}")

        try:
            start_time = time.time()
            response = requests.post(
                url,
                headers=headers,
                json=rdc_id_list,
                timeout=self.timeout
            )
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"RDC InOne API 响应 | status={response.status_code}, 耗时={elapsed_ms:.2f}ms")

            result = response.json()
            logger.debug(f"响应体：{json.dumps(result, ensure_ascii=False)[:500]}...")
            return result

        except requests.exceptions.ConnectionError as e:
            logger.error(f"RDC InOne API 请求失败：{e}", exc_info=True)
            return {"status": f"请求异常：{e}"}
        except requests.exceptions.Timeout as e:
            logger.error(f"RDC InOne API 请求超时：{e}", exc_info=True)
            return {"status": f"请求超时：{e}"}
        except json.JSONDecodeError as e:
            logger.error(f"RDC InOne API 响应解析失败：{e}, body={response.text}", exc_info=True)
            return {"status": f"JSON 解析失败：{e}", "body": response.text}

    # ---- 实例方法（对外） ----

    def get_child_prs(self, rdc_id: str) -> List[Dict[str, str]]:
        """
        获取 MR 关联的子级 PR 列表

        Args:
            rdc_id: RDC 工作项 ID（MR）

        Returns:
            [{"id": "OTNSW-794196", "title": "F010705-C-..."}, ...]
        """
        data = self._get_relations(rdc_id, self._user_num)

        # 请求异常时返回空列表
        if "status" in data and "bo" not in data:
            logger.error(f"获取 {rdc_id} 关联项失败: {data.get('status')}")
            return []

        children = data.get("bo", {}).get("子级", [])
        result = []
        for item in children:
            if item.get("System_WorkItemTypeKey") != "PR":
                continue
            pr_id = item.get("System_Id", "")
            pr_title = item.get("System_Title", "")
            if pr_id:
                result.append({"id": pr_id, "title": pr_title})

        logger.info(f"{rdc_id} 关联子级 PR 数量={len(result)}")
        return result

    def get_pr_details(self, pr_id_list: List[str]) -> List[Dict[str, str]]:
        """
        获取 PR 详情列表，提取领域、详设文档链接、复用程度、开发类型、细分类别

        Args:
            pr_id_list: PR 工作项 ID 列表

        Returns:
            [{"id": "OTNSW-794196", "system_areapath": "...", "detail_design_url": "...", "reuse_degree": "...",
              "development_type": "...", "detail_category": "..."}]
        """
        if not pr_id_list:
            return []

        data = self._get_workitems_detail(pr_id_list, self._user_num)

        if "status" in data and "bo" not in data:
            logger.error(f"获取 PR 详情失败：{data.get('status')}")
            return []

        items = data.get("bo", {}).get("items", [])
        field_keys = {
            "DetailedDesignUrl": "detail_design_url",
            "ReuseDegree": "reuse_degree",
            "DevelopmentType": "development_type",
            "DetailCategory": "detail_category",
        }

        result = []
        for item in items:
            fields_list = item.get("fields", [])
            field_map = {f.get("key"): f.get("value", "") for f in fields_list}

            row = {"id": item.get("id", "")}
            # 提取 system_areapath 的 label（只返回一个字符串值）
            system_areapath_value = field_map.get("System_AreaPath", "")
            system_areapath = ""
            if isinstance(system_areapath_value, dict):
                # 从嵌套结构中获取 label，优先从 baseDataValue 中获取
                base_data_value = system_areapath_value.get("baseDataValue", {})
                if isinstance(base_data_value, dict):
                    system_areapath = base_data_value.get("label", "")
                # 如果 baseDataValue 中没有，尝试直接从 system_areapath 获取
                if not system_areapath:
                    system_areapath = system_areapath_value.get("label", "")
            elif isinstance(system_areapath_value, str):
                system_areapath = system_areapath_value
            row["system_areapath"] = system_areapath
            # 提取其他字段（处理可能是 dict 类型的情况，如 ReuseDegree、DevelopmentType、DetailCategory）
            for src_key, dst_key in field_keys.items():
                value = field_map.get(src_key, "")
                if isinstance(value, dict):
                    # 尝试从嵌套结构中获取 label，优先从 baseDataValue 中获取
                    base_data_value = value.get("baseDataValue", {})
                    if isinstance(base_data_value, dict):
                        value = base_data_value.get("label", "")
                    else:
                        value = value.get("label", str(value))
                elif not isinstance(value, str):
                    value = str(value) if value is not None else ""
                row[dst_key] = value

            result.append(row)

        logger.info(f"获取 PR 详情数量={len(result)}")
        return result


# ==================== 模块级便捷函数 ====================

_cached_repository = None


def _get_repository():
    """获取缓存的 RdcRepository 实例，同一进程内复用"""
    global _cached_repository
    if _cached_repository is None:
        _cached_repository = RdcRepository()
    return _cached_repository
