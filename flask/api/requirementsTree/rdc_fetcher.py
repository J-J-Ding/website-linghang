"""
RDC 需求数据在线拉取模块
从 RDC API 分页获取 MR ID 列表 → 并发拉取详情 → 提取目标字段 → 返回扁平节点列表
"""

import json
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from requirementsTree.uac_token import get_uac_token

logger = logging.getLogger(__name__)

# rdc_query_config.json 与本模块同目录
_CONFIG_PATH = Path(__file__).parent / "rdc_query_config.json"


# ==================== RDC 提取类 ====================
class RdcExtractor:
    """
    基于 RDC API 的需求数据提取器

    封装认证、API 调用、数据解析的公共逻辑，
    各提取方法只需关注具体的业务规则。
    """

    def __init__(self):
        user_num, token = get_uac_token()
        if not token:
            raise RuntimeError("获取 UAC token 失败")
        self._user_num = user_num
        self._token = token

    def _refresh_token(self):
        """刷新认证信息，token 失效时调用"""
        user_num, token = get_uac_token()
        if token:
            self._user_num = user_num
            self._token = token

    # ---- 静态方法 ----

    @staticmethod
    def _load_query_config(scope):
        """
        读取 rdc_query_config.json，返回指定 scope 的配置 dict
        返回: {"scope": "智能OTN", "queries": [...]} 或 None
        """
        try:
            with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)
            for cfg in all_configs:
                if cfg.get("scope") == scope:
                    return cfg
            return None
        except Exception as e:
            logger.error(f"读取 rdc_query_config.json 失败: {e}")
            return None

    @staticmethod
    def _parse_query_url(url):
        """
        从 RDC 查询页面 URL 中解析 workspaceKey 和 teamId
        支持两种格式:
          - .../queries?wicViewId=xxx&teamId=yyy
          - .../queries/5222006?type=root3&teamId=yyy
        返回: {"workspaceKey": str, "teamId": str}
        解析失败则抛出 ValueError
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # workspaceKey: 从路径 .../workspaces/{workspaceKey}/apps/... 提取
        workspace_key = None
        for i, part in enumerate(path_parts):
            if part == "workspaces" and i + 1 < len(path_parts):
                workspace_key = path_parts[i + 1]
                break
        if not workspace_key:
            raise ValueError(f"无法从 URL 解析 workspaceKey: {url}")

        # teamId: 从 query string 取
        qs = parse_qs(parsed.query)
        team_id_list = qs.get("tenantId")
        if not team_id_list:
            raise ValueError(f"无法从 URL 解析 teamId: {url}")
        team_id = team_id_list[0]

        # queryId: 优先从路径中提取（如 /queries/5469063），否则从 wicViewId 参数取
        query_id = None
        # 尝试从路径：找到 'queries' 后的下一个数字段
        for i, part in enumerate(path_parts):
            if part == "queries" and i + 1 < len(path_parts):
                # 可能是查询ID
                candidate = path_parts[i + 1]
                if candidate.isdigit():
                    query_id = candidate
                    break
        # 如果没找到，从参数取
        if not query_id:
            wic_view_id_list = qs.get("wicViewId")
            if wic_view_id_list:
                query_id = wic_view_id_list[0]

        result = {
            "workspaceKey": workspace_key,
            "teamId": team_id,
        }
        if query_id:
            result["queryId"] = query_id
        return result

    @staticmethod
    def _build_headers(user_num, token, tenant_id="ZTE"):
        """构建 RDC API 请求头"""
        headers = {
            "Content-Type": "application/json",
            "X-Emp-No": user_num,
            "X-Auth-Value": token,
            "X-Lang-Id": "zh_CN",
            "X-Tenant-Id": tenant_id,
            "X-Api-Key": "rdc_99f1b87ce5e84d8b87f03111cb0a0416"
        }
        headers["Cookie"] = f"iuacToken_prod={token}"
        return headers

    @staticmethod
    def _parse_query_items(data):
        """从 query_work_items 响应中解析 items 列表"""
        items = []
        bo = data.get("bo")
        if bo is None:
            if isinstance(data.get("result"), dict):
                items = data["result"].get("items", [])
            elif isinstance(data.get("items"), list):
                items = data["items"]
        else:
            if isinstance(bo, dict):
                result = bo.get("result")
                if result is None:
                    if isinstance(bo, list):
                        items = bo
                else:
                    items = result.get("items", [])
            elif isinstance(bo, list):
                items = bo
        return items

    def _get_headers(self, tenant_id=None):
        """获取当前认证信息的请求头"""
        if tenant_id is None:
            # 尝试从之前解析的 URL 参数里获取 tenant_id（如果有）
            tenant_id = getattr(self, '_tenant_id', 'ZTE')
        return self._build_headers(self._user_num, self._token, tenant_id)

    def fetch_single_mr_detail(self, mr_id, workspace_key="OTNSW"):
        """获取单条 MR 的完整详情"""
        try:
            url = f"https://rdcloud.zte.com.cn/zte-rdcloud-rdc-rdcserver/rdc/workspaces/{workspace_key}/work_items/{mr_id}?workItemTypeKey=MR"
            headers = self._get_headers()
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"获取 {mr_id} 详情失败: {resp.status_code}")
                return None
            data = resp.json()
            return data.get('bo') or data
        except Exception as e:
            logger.warning(f"获取 {mr_id} 异常: {e}")
            return None

    def fetch_all_mr_details(self, mr_ids, workspace_key="OTNSW"):
        """并发获取所有 MR 的完整详情"""
        logger.info(f"并发获取 {len(mr_ids)} 条 MR 详情...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.fetch_single_mr_detail, mr_id, workspace_key): mr_id for mr_id in mr_ids}
            bo_list = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    bo_list.append(result)
        logger.info(f"成功获取 {len(bo_list)} 条 MR 详情")
        return bo_list

    @staticmethod
    def extract_from_detail_items(items, workspace_key="OTNSW", project_name_override="", milestone_name_override=""):
        """从详情 items 中提取目标字段

        project_name_override / milestone_name_override:
            优先使用配置文件中的值，不再依赖 RDC 详情字段（RDC 详情字段值不稳定）
        """
        result = []
        for item in items:
            fields_list = item.get('fields', [])
            field_map = {f.get('key', ''): f for f in fields_list}

            def get_field_value(key, subpath=None):
                f = field_map.get(key)
                if not f:
                    return ''
                val = f.get('value', '')
                if subpath and isinstance(val, dict):
                    for p in subpath.split('.'):
                        if isinstance(val, dict):
                            val = val.get(p, '')
                        else:
                            return ''
                    return val if val is not None else ''
                return val if not isinstance(val, str) else val.strip()

            project_name = project_name_override
            milestone_name = milestone_name_override

            # rdc_id
            rdc_id = ''
            id_field = field_map.get('System_Id')
            if id_field:
                val = id_field.get('value', '')
                if isinstance(val, dict):
                    rdc_id = val.get('fullNo', '')
                elif isinstance(val, str):
                    rdc_id = val

            # title
            title = get_field_value('System_Title')

            # status
            status = ''
            state_field = field_map.get('System_State')
            if state_field:
                state_val = state_field.get('value', {})
                if isinstance(state_val, dict):
                    status = state_val.get('stateGroup', {}).get('groupName', '')

            # main_domain
            main_domain = ''
            ma_field = field_map.get('MasterArea')
            if ma_field:
                val = ma_field.get('value', '')
                if val:
                    main_domain = val.get('label', '') if isinstance(val, dict) else val
            if not main_domain:
                area_field = field_map.get('System_AreaPath')
                if area_field:
                    val = area_field.get('value', '')
                    if isinstance(val, dict):
                        main_domain = val.get('label', '')
                        if not main_domain:
                            bd = val.get('baseDataValue', {})
                            if isinstance(bd, dict):
                                main_domain = bd.get('label', '')
                    elif isinstance(val, str) and val.strip():
                        main_domain = val
                    if not main_domain:
                        persistent = area_field.get('persistentValue', {})
                        if isinstance(persistent, dict):
                            bd = persistent.get('baseDataValue', {})
                            if isinstance(bd, dict):
                                main_domain = bd.get('label', '')

            # instance_url
            instance_url = get_field_value('SpecificationByExampleUrl')

            # solution_status
            solution_status = get_field_value('DesignState')

            # solution_doc_url
            solution_doc_url = get_field_value('DesignSpecificationUrl')

            # access_check: AI准入检查
            access_check = get_field_value('AccessCheck')

            # instance_status: 需求实例化状态
            instance_status = get_field_value('SpecificationByExampleState')

            # operator_person
            operator_person = ''
            cb_field = field_map.get('System_CreatedBy')
            if cb_field:
                val = cb_field.get('value', {})
                if isinstance(val, dict):
                    operator_person = val.get('nameDisplayLong', '')
                elif isinstance(val, str):
                    operator_person = val

            # market_req_url：市场需求自身页面链接
            market_req_url = f"https://rdcloud.zte.com.cn/uportal/rd-uportal/workspaces/{workspace_key}/apps/wim/allWorkItems/{rdc_id}" if rdc_id else ""

            result.append({
                'project_name': project_name,
                'milestone_name': milestone_name,
                'rdc_id': rdc_id,
                'title': title,
                'status': status,
                'main_domain': main_domain,
                'market_req_url': market_req_url,
                'instance_url': instance_url,
                'instance_status': instance_status,
                'solution_status': solution_status,
                'solution_doc_url': solution_doc_url,
                'access_check': access_check,
                'operator_person': operator_person,
            })
        return result

    # ---- 对外提取方法 ----
    def fetch_requirement_data(self, scope):
        """
        在线拉取指定 scope 的需求数据
        返回: list[dict] 扁平节点列表，每个 dict 包含 project_name, milestone_name, rdc_id, title 等
        """
        # 1. 读取配置
        config = self._load_query_config(scope)
        if not config:
            raise ValueError(f"未找到 scope={scope} 的 RDC 查询配置")

        # 2. 遍历每个查询配置，拉取数据
        all_flat_nodes = []
        for query_cfg in config["queries"]:
            url = query_cfg.get("url", "")
            logger.info(f"开始拉取 scope={scope}, url={url}, milestone_filter={query_cfg.get('milestone_filter')}")

            # 从查询 URL 中解析 workspaceKey，供后续拼接链接使用
            try:
                url_params = self._parse_query_url(url)
                workspace_key = url_params["workspaceKey"]
            except ValueError as e:
                logger.error(f"url={url} workspaceKey 解析失败: {e}，跳过")
                continue

            try:
                mr_ids = self.fetch_mr_ids_by_query_url(url)
            except ValueError as e:
                logger.error(f"url={url} 配置解析失败: {e}，跳过")
                continue

            if not mr_ids:
                # 可能是 token 失效，尝试刷新重试一次
                logger.warning(f"url={url} 未获取到 MR ID，尝试刷新 token 重试")
                self._refresh_token()
                try:
                    mr_ids = self.fetch_mr_ids_by_query_url(url)
                except ValueError as e:
                    logger.error(f"url={url} 重试后配置解析失败: {e}，跳过")
                    continue

            if not mr_ids:
                logger.warning(f"url={url} 未获取到 MR ID，跳过")
                continue

            detail_list = self.fetch_all_mr_details(mr_ids, workspace_key)
            if not detail_list:
                logger.warning(f"url={url} 未获取到 MR 详情，跳过")
                continue

            flat_nodes = self.extract_from_detail_items(
                detail_list, workspace_key,
                project_name_override=query_cfg.get("project_name", ""),
                milestone_name_override=query_cfg.get("milestone_filter", ""),
            )
            all_flat_nodes.extend(flat_nodes)

        logger.info(f"scope={scope} 在线拉取完成，共 {len(all_flat_nodes)} 条需求")
        return all_flat_nodes

    def fetch_mr_ids_by_query_url(self, query_url: str):
        """
        从RDC查询URL直接拉取需求数据（不依赖配置文件）

        参数:
          query_url: RDC查询页面的完整URL
            示例: https://rdcloud.zte.com.cn/.../queries/5469063?type=root3&teamId=bdv_105441&tenantId=10001
        """
        try:
            # 1. 解析URL，获取 workspaceKey、teamId 和 queryId，以及 tenantId
            url_params = self._parse_query_url(query_url)
            workspace_key = url_params["workspaceKey"]
            team_id = url_params["teamId"]
            query_id = url_params.get("queryId")
            tenant_id = parse_qs(urlparse(query_url).query).get("tenantId", [""])[0] or "ZTE"
            logger.debug(f"URL解析成功: workspace={workspace_key}, team={team_id}, query={query_id}, tenant={tenant_id}")
        except ValueError as e:
            logger.error(f"URL解析失败: {e}")
            return []

        # 2. 获取 MR ID 列表（不限制数量，直到全部返回）
        mr_ids = self._fetch_mr_ids_by_params(workspace_key, team_id, query_id=query_id, tenant_id=tenant_id)
        logger.info(f"从查询URL共获取 {len(mr_ids)} 个MR ID")
        return mr_ids

    def _fetch_mr_ids_by_params(self, workspace_key: str, team_id: str, query_id: str = None, limit: int = None, tenant_id: str = None):
        """
        根据 workspaceKey、teamId 和可选的 query_id 获取 MR ID 列表。
        如果提供了 query_id，则先通过 WIC API 获取视图定义中的真实过滤条件（sourceClauses），
        并将其用于 query_work_items 请求。这确保与 RDC 页面显示完全一致。

        参数:
            workspace_key: 工作空间键
            team_id: 团队ID
            query_id: 视图查询ID（可选）
            limit: 最大返回数量限制（可选）
            tenant_id: 租户ID（可选，默认ZTE）

        返回:
            list[str]: MR ID列表
        """
        api_url = f"https://rdcloud.zte.com.cn/zte-rdcloud-rdc-rdcserver/rdc/workspaces/{workspace_key}/queries/query_work_items"
        if tenant_id is None:
            tenant_id = getattr(self, '_tenant_id', 'ZTE')
        headers = self._get_headers(tenant_id)
        page_size = 200
        page_no = 1
        all_mr_ids = []
        query_condition = None

        # ------------- 如果提供了 query_id，获取视图定义以提取精确过滤条件 -------------
        if query_id:
            view_def_url = f"https://rdcloud.zte.com.cn/zte-plm-wic-api/api/workspaces/{workspace_key}/view_queries/{query_id}"
            try:
                logger.debug(f"获取视图定义: {view_def_url}")
                view_resp = requests.get(view_def_url, headers=headers, timeout=30)
                if view_resp.status_code == 200:
                    view_data = view_resp.json()
                    bo = view_data.get("bo")
                    qc = bo.get("queryCondition") or bo.get("sourceClauses")
                    if qc:
                        if isinstance(qc, dict):
                            if "sourceClauses" in qc:
                                query_condition = qc
                            else:
                                # 可能是单个条件对象，转为列表
                                query_condition = {"sourceClauses": [qc]}
                        src = query_condition.get("sourceClauses", [])
                        logger.info(f"从视图定义提取到 {len(src)} 条查询条件")
                        if src and logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"查询条件示例: {json.dumps(src[:2], ensure_ascii=False)}")
                    else:
                        logger.warning("未从视图定义提取到查询条件，将仅使用wicViewId（效果可能不全）")
                else:
                    logger.warning(f"视图定义API返回状态码 {view_resp.status_code}，将仅使用wicViewId")
            except Exception as e:
                logger.warning(f"获取视图定义异常: {e}，将仅使用wicViewId")
        # ------------- 分页获取MR ID列表 -------------
        while True:
            payload = {
                "workItemTypeKeys": [],
                "workspaceKey": workspace_key,
                "pageNo": page_no,
                "pageSize": page_size,
                "queryType": "filter",
                "resultType": "flat",
                "selectItems": [
                    {"key": "System_Id", "name": "标识", "type": "workItemNo"}
                ],
                "sortItems": [{"isAscending": True, "key": "RequirementSortOrder"}],
                "teamId": team_id,
                "tenantKey": "ZTE",
                "userId": self._user_num,
            }

            # 决定使用哪种过滤条件
            if query_condition:
                # 合并条件：外部条件 + MR类型限制（如果sourceClauses中未包含）
                final_qc = query_condition.copy() if isinstance(query_condition, dict) else {"sourceClauses": query_condition}
                src = final_qc.get("sourceClauses", [])
                # 检查是否已有WorkItemType过滤
                has_mr_filter = any(
                    clause.get("field") == "System_WorkItemType" and
                    ((isinstance(clause.get("value"), str) and clause.get("value", "").startswith("MR")) or
                     (isinstance(clause.get("value"), list) and any(v.startswith("MR") for v in clause.get("value", []))))
                    for clause in src
                )
                payload["queryCondition"] = final_qc
                logger.debug(f"第{page_no}页使用从视图定义提取的queryCondition（{len(src)}条条件）")
            elif query_id:
                payload["wicViewId"] = query_id
                logger.debug(f"第{page_no}页使用wicViewId={query_id}")

            try:
                logger.debug(f"请求第{page_no}页数据...")
                resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
            except Exception as e:
                logger.error(f"第{page_no}页请求异常: {e}")
                break

            if resp.status_code != 200:
                logger.error(f"第{page_no}页API返回状态码 {resp.status_code}")
                break

            data = resp.json()
            items = self._parse_query_items(data)
            logger.debug(f"第{page_no}页返回 {len(items)} 条items")

            if not items:
                logger.debug(f"第{page_no}页无items，终止分页")
                break

            # 调试模式下打印前几条数据的结构
            if logger.isEnabledFor(logging.DEBUG) and items:
                for idx, item in enumerate(items[:3]):
                    logger.debug(f"item[{idx}] 字段: {list(item.keys())}")
                    mr_id = item.get("id") or item.get("System_Id")
                    work_item_type = item.get("System_WorkItemTypeKey") or item.get("workItemTypeKey") or ""
                    logger.debug(f"item[{idx}] id={mr_id}, type={work_item_type}")

            # 遍历所有items，收集MR ID
            collected_count = 0
            for item in items:
                mr_id = item.get("id") or item.get("System_Id")
                work_item_type = item.get("System_WorkItemTypeKey") or item.get("workItemTypeKey") or ""
                if mr_id and work_item_type.startswith("MR"):
                    all_mr_ids.append(mr_id)
                    collected_count += 1
                    if limit and len(all_mr_ids) >= limit:
                        logger.info(f"达到数量限制{limit}，共收集{collected_count}个MR ID")
                        return all_mr_ids

            logger.debug(f"第{page_no}页收集到 {collected_count}/{len(items)} 个MR ID")

            if collected_count == 0:
                logger.warning(f"第{page_no}页未收集到任何MR ID，终止分页")
                break

            if len(items) < page_size:
                break
            page_no += 1
        logger.info(f"共获取 {len(all_mr_ids)} 个MR ID (query_id={query_id})")
        return all_mr_ids


# ==================== 模块级便捷函数 ====================

_cached_extractor = None


def _get_extractor():
    """获取缓存的 RdcExtractor 实例，同一进程内复用，token 失效时由 _refresh_token 自动刷新"""
    global _cached_extractor
    if _cached_extractor is None:
        _cached_extractor = RdcExtractor()
    return _cached_extractor


def fetch_requirement_data_online(scope):
    """在线拉取指定 scope 的需求数据"""
    return _get_extractor().fetch_requirement_data(scope)
