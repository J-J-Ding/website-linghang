import requests
import hashlib
import json
import socket
import time
import logging
import re
import markdownify
import sys
import os
import markdown
import html
import markdown.extensions.tables
from bs4 import BeautifulSoup

logger = logging.getLogger("Logger")

# 用于 AI 统计接口的 appcode。
# 该常量在文件内此前被引用但未定义；补齐后可避免采集时触发 NameError。
APP_CODE = "e63a3a4d62f24441a14c5c1b7fa92212"

class IcenterAPI:
    def __init__(self, account, password="", token=""):
        self.content_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s?spaceId=%s&environmentType=browser"
        self.table_url = "http://icenterapi.zte.com.cn/zte-rd-icenter-advanced/content/get_table?limit=500&offset=0"
        self.history_detail_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/histories/%s?t=timestamp&spaceId=%s&environmentType=browser&id=%s"
        self.X_Emp_No = account
        self.password = password
        self.X_Auth_Value = ''
        self.loginsyscode = 'Portal'
        self.originsyscode = ''
        self.token_status = 0
        if not token:
            token_dic = self.get_token()
            self.account = token_dic['other']['account']
            self.token = token_dic['other']['token']
        else:
            self.account = account
            self.token = token
        self.headers = {'Content-type': 'application/json', 'X-Emp-No': self.account, 'X-Auth-Value': self.token, 'X-Lang-Id': 'zh_CN'}
        self.headers2 = {
                'Content-type': 'application/json', 
                'X-Emp-No': self.account, 
                'X-Auth-Value': self.token, 
                'X-Lang-Id': 'zh_CN',
                'appCode': '4811ee4055a74cb4b52e7295e1d1858d'}

        self.auth = requests.auth.HTTPDigestAuth(self.account, self.token)
        self.proxies = {"http": "", "https": ""}
        self.history_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/histories/?spaceId=%s&environmentType=browser&limit=%s&offset=%s"
        self.tag_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/tags"
        self.page_update_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s?spaceId=%s"
        self.page_edit_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s/edit"
        # self.page_create_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content?spaceId=%s&parentId=%s"
        self.page_create_url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/content?spaceId=%s"
        self.page_exist_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/title/multiDuplicate"
        self.page_delete_url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/content/%s?spaceId=%s&multi=%s"
        # self.template_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/templates/?spaceId=%s"
        self.template_url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/templates/?spaceId=%s"
        # self.template_content_url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/templates/%s/edit?spaceId=%s&dataType=%s"
        self.template_content_url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/templates/%s/edit?spaceId=%s&dataType=HTML"
        self.operate_log_url = "https://icosg.dt.zte.com.cn/studio-ispace/content/operateLog/space/%s/content/%s"
        self.flower_detail_url = "https://icosg.dt.zte.com.cn/studio-ispace/content/page/%s/flower/detail?offset=%s&limit=%s&spaceId=%s"
        self.page_tags_url = "https://icosg.dt.zte.com.cn/studio-ispace/content/page/%s/tags?spaceId=%s"
        self.page_detail_url = "https://icosg.dt.zte.com.cn/studio-ispace/content/page/%s?spaceId=%s"
        
        

    def get_token(self):
        url = "http://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
        client_ip = self.get_host_ip()
        text = {
            "account": self.X_Emp_No,
            "passWord": self.password,
            "loginClientIp": client_ip,
            "loginSystemCode": self.loginsyscode,
            "originSystemCode": self.originsyscode,
            "other": {
                "networkArea": '1',
                "networkAccessType": '1'
            },
            "verifyCode": hashlib.md5(
                str(self.X_Emp_No + self.password + client_ip + self.loginsyscode + self.originsyscode).encode(
                    encoding='utf-8')).hexdigest()
        }
        headers = {'Content-type': 'application/json'}
        content = requests.post(url, data=json.dumps(text), headers=headers)
        return content.json()

    def get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip


    def get_page_block_content(self, space_id, page_id, block_id=None, block_title=None, block_tags=None, content_type="HTML"):
        """
        获取指定页面中某个 block 的内容（支持通过 blockId/blockName/blockTag 查询）
        
        :param space_id: 空间ID
        :param page_id: 页面ID
        :param block_id: 区块ID (可选)
        :param block_title: 区块名称 (可选)
        :param block_tags: 区块标签 (可选)
        :param content_type: 返回内容格式，"HTML" 或 "MARKDOWN"，默认 HTML
        :return: (content: str, title: str) 如果失败返回 ("", "")
        """
        url = "https://icosg.dt.zte.com.cn/studio-ispace/doc/block/content/query"

        # 构建请求体
        body = {
            "spaceId": space_id,
            "pageId": page_id,
            "contentType": content_type  # 返回格式
        }

        # 至少提供 blockId、blockName、blockTag 中的一个
        if block_id:
            body["blockId"] = block_id
        if block_title:
            body["blockName"] = block_title
        if block_tags:
            body["blockTag"] = block_tags

        # 如果都没有提供，无法查询
        if 'blockId' not in body and 'blockName' not in body and 'blockTag' not in body:
            logger.error("At least one of block_id, block_title, block_tags must be provided.")
            return "", ""

        headers = self.headers2.copy()
        headers['Content-Type'] = 'application/json'  # 显式设置

        try:
            response = requests.post(
                url,
                data=json.dumps(body),
                headers=headers,
                auth=self.auth,
                proxies=self.proxies,
                timeout=10
            )
        except Exception as e:
            logger.error(f"Request failed when fetching block content: {e}")
            return "", ""

        try:
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return "", ""

            resp_json = response.json()

            # 检查返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "")
                logger.error(f"API call failed: {err_msg}")
                return "", ""

            # bo 是一个列表
            bo_data = resp_json.get("bo", {})
            if not bo_data:
                logger.warning("No block content returned from API.")
                return "", ""

            # 取第一个匹配的 block（通常只有一个）
            blocks_list = bo_data.get("blocks", [])
            if not blocks_list:
                logger.warning("No blocks found in response.")
                return "", ""

            # 取第一个匹配的 block
            block_data = blocks_list[0]
            content = block_data.get("content", "")
            title = block_data.get("blockName", "")

            return content, title

        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return "", ""
        
    def insert_block_content(self, space_id, page_id, block_id=None, block_title=None, block_tags=None, block_content="", position='before'):
        """
        在指定页面中某个block前后插入某个 block 的内容，支持通过 blockId、blockTitle 或 blockTags 定位

        :param space_id: 空间ID
        :param page_id: 页面ID（即 URL 路径中的 contentId）
        :param block_id: 要更新的 block 的 ID（可选）
        :param block_title: 要更新的 block 的标题（可选）
        :param block_tags: 要更新的 block 的标签列表（可选），如 ["验收", "用例"]
        :param block_content: 要写入的内容，HTML 字符串（如 "<p>新的内容</p>"）
        :param content_type: 内容类型，仅用于语义，实际传 body 即可
        :return: bool - 是否成功
        """
        # 参数校验：至少提供 block_id、block_title、block_tags 中的一个
        if not block_id and not block_title and not block_tags:
            logger.error("At least one of block_id, block_title, or block_tags must be provided to locate the block.")
            return False

        # 构造 URL
        url = f"https://icosg.dt.zte.com.cn/studio-ispace/doc/block/content/{page_id}?spaceId={space_id}"

        # 构建请求体
        body = {
            "position": position,
            "block": {
                "body": block_content  # 写入内容
            }
        }

        # 只添加非空字段到 body 中
        if block_id:
            body["targetBlockId"] = block_id
        if block_title:
            body["targetBlockTitle"] = block_title
        if block_tags is not None:  # 允许传空列表 []
            body["targetBlockTags"] = block_tags

        # 设置请求头
        headers = self.headers2.copy()
        # headers['Content-Type'] = 'application/json'
        logger.info(f"----------headers:{headers}")
        logger.info(f"----------body:{body}")
        try:
            response = requests.post(
                url,
                data=json.dumps(body, ensure_ascii=False),  # ensure_ascii=False 防止中文被转义
                headers=headers,
                proxies=self.proxies,
                timeout=10
            )
        except Exception as e:
            logger.error(f"Request failed when updating block content: {e}")
            return False

        try:
            # 检查状态码
            if response.status_code not in [200, 201]:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return False

            resp_json = response.json()

            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Update failed: {err_msg}")
                return False

            # 成功日志（可输出定位方式）
            locator = []
            if block_id: locator.append(f"ID='{block_id}'")
            if block_title: locator.append(f"Title='{block_title}'")
            if block_tags: locator.append(f"Tags={block_tags}")
            logger.info(f"Block updated successfully by {' | '.join(locator)}")

            return True

        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return False

    def set_block_content(self, space_id, page_id, block_id=None, block_title=None, block_tags=None, block_content="", content_type="HTML"):
       """
       更新指定页面中某个 block 的内容，支持通过 blockId、blockTitle 或 blockTags 定位

       :param space_id: 空间ID
       :param page_id: 页面ID（即 URL 路径中的 contentId）
       :param block_id: 要更新的 block 的 ID（可选）
       :param block_title: 要更新的 block 的标题（可选）
       :param block_tags: 要更新的 block 的标签列表（可选），如 ["验收", "用例"]
       :param block_content: 要写入的内容，HTML 字符串（如 "<p>新的内容</p>"）
       :param content_type: 内容类型，仅用于语义，实际传 body 即可
       :return: bool - 是否成功
       """
       # 参数校验：至少提供 block_id、block_title、block_tags 中的一个
       if not block_id and not block_title and not block_tags:
           logger.error("At least one of block_id, block_title, or block_tags must be provided to locate the block.")
           return False

       # 构造 URL
       url = f"https://icosg.dt.zte.com.cn/studio-ispace/doc/block/content/{page_id}?spaceId={space_id}"

       # 构建请求体
       body = {
           "block": {
               "body": block_content  # 写入内容
           }
       }

       # 只添加非空字段到 body 中
       if block_id:
           body["targetBlockId"] = block_id
       if block_title:
           body["targetBlockTitle"] = block_title
       if block_tags is not None:  # 允许传空列表 []
           body["targetBlockTags"] = block_tags

       # 设置请求头
       headers = self.headers2.copy()
       # headers['Content-Type'] = 'application/json'
       try:
           response = requests.put(
               url,
               data=json.dumps(body, ensure_ascii=False),  # ensure_ascii=False 防止中文被转义
               headers=headers,
               auth=self.auth,
               proxies=self.proxies,
               timeout=10
           )
       except Exception as e:
           logger.error(f"Request failed when updating block content: {e}")
           return False

       try:
           # 检查状态码
           if response.status_code not in [200, 201]:
               logger.error(f"HTTP {response.status_code}: {response.text}")
               return False

           resp_json = response.json()

           # 检查业务返回码
           code = resp_json.get("code", {})
           if code.get("msgId") != "RetCode.Success":
               err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
               logger.error(f"Update failed: {err_msg}")
               return False

           # 成功日志（可输出定位方式）
           locator = []
           if block_id: locator.append(f"ID='{block_id}'")
           if block_title: locator.append(f"Title='{block_title}'")
           if block_tags: locator.append(f"Tags={block_tags}")
           logger.info(f"Block updated successfully by {' | '.join(locator)}")

           return True

       except Exception as e:
           logger.error(f"Parse response failed: {e}, response: {response.text}")
           return False

    def set_page_content(self, content_id, space_id, title, content):
       """
       更新文档内容，仅允许更新title、内容
       
       :param content_id: 内容ID (对应URL中的pageId)
       :param space_id: 空间ID
       :param title: 文档标题
       :param content: 文档内容，HTML格式字符串
       :param doc_type: 文档类型，默认为HTML
       :return: bool - 是否成功
       """
       # 构造 URL，参考set_block_content函数的格式
       url = f"https://icenterapi.zte.com.cn/zte-rdcloud-space-content/content/{content_id}/updateContent?spaceId={space_id}"

       # 构建请求体，根据接口说明
       body = {
           "docType": "HTML",
           "title": title,
           "text": content
       }

       # 设置请求头，参考set_block_content函数的格式
       headers = self.headers2.copy()
       headers['Content-Type'] = 'application/json'

       try:
           response = requests.post(
               url,
               data=json.dumps(body, ensure_ascii=False),  # ensure_ascii=False 防止中文被转义
               headers=headers,
               auth=self.auth,
               proxies=self.proxies,
               timeout=10
           )
       except Exception as e:
           logger.error(f"Request failed when updating page content: {e}")
           return False

       try:
           # 检查状态码
           if response.status_code not in [200, 201]:
               logger.error(f"HTTP {response.status_code}: {response.text}")
               return False

           resp_json = response.json()

           # 检查业务返回码
           code = resp_json.get("code", {})
           if code.get("msgId") != "RetCode.Success":
               err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
               logger.error(f"Update failed: {err_msg}")
               return False

           logger.info(f"Page content updated successfully for content {content_id} in space {space_id}")

           return True

       except Exception as e:
           logger.error(f"Parse response failed: {e}, response: {response.text}")
           return False

    def new_page(self, space_id, parent_id, title, content="", template_id=""):
       """
       新建页面（基于2.0版本API）
       
       :param space_id: 空间ID
       :param title: 页面标题
       :param parent_id: 父页面ID，默认为空（创建在根目录）
       :param content: 页面内容，HTML格式字符串，默认为空
       :param template_id: 模板ID，默认为空（不使用模板）
       :return: 成功时返回完整的API响应，失败时返回None
       """
       # 使用2.0版本API创建页面
       url = "https://icosg.dt.zte.com.cn/studio-ispace/doc/page?spaceId=%s" % space_id
       
       # 构建请求体
       body = {
           "parentId": parent_id,
           "spaceId": space_id,
           "title": title
       }
       
       # 如果提供了模板ID，则添加到请求体中
       if template_id.strip():
           body["templateId"] = template_id
       
       # 如果提供了内容，则添加到请求体中
       if content.strip():
           body["text"] = content
           body["dataType"] = "HTML"
       
       # 设置请求头
       headers = self.headers2.copy()
       headers['Content-Type'] = 'application/json'
       
       try:
           response = requests.post(
               url,
               data=json.dumps(body, ensure_ascii=False),
               headers=headers,
               auth=self.auth,
               proxies=self.proxies,
               timeout=10
           )
       except Exception as e:
           logger.error(f"Request failed when creating new page: {e}")
           return None
       
       try:
           # 检查状态码
           if response.status_code not in [200, 201]:
               logger.error(f"HTTP {response.status_code}: {response.text}")
               return None
           
           resp_json = response.json()
           
           # 检查业务返回码
           code = resp_json.get("code", {})
           if code.get("msgId") != "RetCode.Success":
               err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
               logger.error(f"Create page failed: {err_msg}")
               return None
           
           logger.info(f"Page created successfully in space {space_id}")
           return resp_json
           
       except Exception as e:
           logger.error(f"Parse response failed: {e}, response: {response.text}")
           return None

    def add_comment(self, content_id, space_id, comment):
        """
        添加评论内容到指定页面

        :param content_id: 内容ID
        :param space_id: 空间ID
        :param comment: 评论详细内容，HTML格式
        :param parent_id: 父节点ID，第一层评论不传
        :param jump_url: 跳转地址，可选
        :param group_key_list: UDM授权ID列表，附件用，可选
        :return: bool - 是否成功
        """
        # 构造URL
        url = f"https://icenterapi.zte.com.cn/zte-rd-icenter-extend/comments/businessTypes/content/businesses/{content_id}?spaceId={space_id}"

        # 构建请求体
        body = {
            "commentDetail": comment
        }

        # 设置请求头
        headers = self.headers2.copy()
        headers['Content-Type'] = 'application/json'

        try:
            response = requests.post(
                url,
                data=json.dumps(body, ensure_ascii=False),  # ensure_ascii=False 防止中文被转义
                headers=headers,
                auth=self.auth,
                proxies=self.proxies,
                timeout=10
            )
        except Exception as e:
            logger.error(f"Request failed when adding comment: {e}")
            return False

        try:
            # 检查状态码
            if response.status_code not in [200, 201]:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return False

            resp_json = response.json()

            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Add comment failed: {err_msg}")
                return False

            logger.info(f"Comment added successfully to content {content_id} in space {space_id}")
            return True

        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return False
    

    def get_pageid_spaceid(self, url):
        """
        从iCenter页面URL中解析出页面ID和空间ID
        该方法通过分析iCenter页面URL的结构，提取出页面ID（pageid）和空间ID（spaceId）。
        
        :param url: iCenter页面URL，必须包含'wiki'和'page'路径段
        :return: 元组 (pageid, spaceId)，包含解析出的页面ID和空间ID
        :raises ValueError: 如果URL中不包含'wiki'路径段
        :raises IndexError: 如果URL格式不正确，无法找到对应的路径段
        """
        if not url.strip():
            return "", ""
        parts = url.split('/')
        spaceId_index = parts.index('wiki') - 1
        spaceId = parts[spaceId_index]
        pageid = parts[-2]
        return pageid, spaceId

    def set_pageid_spaceid(self, url, pageid, spaceid):
        """
        用入参的pageid和spaceid替换url中对应的值，返回新的url值
        如果pageid或spaceid为空字符串，则不替换对应位置的值，保持原样
        
        :param url: 原始iCenter页面URL
        :param pageid: 新的页面ID，如果为空字符串则不替换
        :param spaceid: 新的空间ID，如果为空字符串则不替换
        :return: 替换后的新URL
        """
        # 将URL按'/'分割成列表
        parts = url.split('/')
        
        # 找到spaceId的位置（wiki的前一个位置）
        try:
            wiki_index = parts.index('wiki')
            space_index = wiki_index - 1
            # 只有当spaceid不为空字符串时才替换
            if spaceid != "":
                parts[space_index] = spaceid
        except ValueError:
            # 如果找不到'wiki'，则无法替换spaceId
            logger.warning(f"Cannot find 'wiki' in URL: {url}")
        
        # 只有当pageid不为空字符串时才替换pageId（倒数第二个位置）
        if len(parts) >= 2 and pageid != "":
            parts[-2] = pageid
        
        # 重新组合成新的URL
        new_url = '/'.join(parts)
        return new_url


    # 获取icenter整体页面内容与标题
    def get_page_info(self, spaceid, contendid, type:str='part'):
        url = self.content_url % (contendid, spaceid)
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
        except Exception as e:
            # logger.error("Fail to get page:space_id:{}, page_id:{}".format(self.space_id, content_id))
            return None, None
        reps_json_data = json.loads(resp.content)
        try:
            if resp.status_code != 200 or reps_json_data["code"]["msgId"] != 'RetCode.Success':
                time.sleep(1)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
                print(resp.status_code)
                reps_json_data = json.loads(resp.content)
        except Exception as e:
            logger.error(e)
            return None, None
        if "bo" not in reps_json_data.keys() or reps_json_data['bo'] is None:
            return None, None
        content = reps_json_data['bo'].get('contentBody')
        title = reps_json_data['bo'].get('title')
        if type != 'part':
            return reps_json_data['bo']
        return content, title

    def icenter_table_get(self, spaceid, contendid, table_index=1):
        page_url = 'https://i.zte.com.cn/#/space/%s/wiki/page/%s/view' % (spaceid, contendid)
        json_data = {
            "msg_id": "1123",
            "table_header": False,
            # 表格所在的页面地址
            "page_url": page_url,
            "table_index": table_index
        }
        resp = requests.post(self.table_url, json=json_data, headers=self.headers, proxies=self.proxies)
        reps_json_data = json.loads(resp.content)
        if resp.status_code != 200:
            if resp.status_code != 200 or reps_json_data["code"]["msgId"] != 'RetCode.Success':
                time.sleep(1)
                resp = requests.get(self.table_url, auth=self.auth, headers=self.headers, proxies=self.proxies)
                reps_json_data = json.loads(resp.content)
        if "bo" not in reps_json_data:
            return None
        else:
            resp = reps_json_data["bo"]
        return resp

    # 获取icenter整体页面标题
    def get_catalog(self, html_text):
        catalog = []
        if html_text:
            content = BeautifulSoup(html_text, 'html.parser')
            title_tags = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            for tag in title_tags:
                if tag.text.strip():
                    catalog.append(tag.text.strip())
        return catalog

    def get_first_children(self, spaceId, contentId):
        url = f"https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/subtree?contentId={contentId}&spaceId={spaceId}&environmentType=browser&&hasDepth=false"
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
        except Exception as e:
            # logger.error("Fail to get page:space_id:{}, page_id:{}".format(self.space_id, content_id))
            return None
        reps_json_data = json.loads(resp.content)
        try:
            if resp.status_code != 200 or reps_json_data["code"]["msgId"] != 'RetCode.Success':
                time.sleep(1)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
                print(resp.status_code)
                reps_json_data = json.loads(resp.content)
        except Exception as e:
            logger.error(e)
            return None
        if "bo" not in reps_json_data.keys():
            return None
        children_list = reps_json_data.get('bo', [])
        # children_list = [item["id"] for item in children_list]
        # return children_list
        result = dict()
        if not children_list:
            children_list = []
        for child in children_list:
            result[child["title"]] = "https://i.zte.com.cn/index/ispace/#/space/" + spaceId + "/wiki/page/" + child["id"] + "/view" 

        return result

    # 获取页面最新更新时间，无关的函数需要删除
    def get_latest_page_info(self, space_id, content_id):
        try:
            url = self.content_url % (content_id, space_id)
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            res = json.loads(resp.content)['bo']
            latest_page_info = {"updateDate": res["updateDate"], "updateBy": res["updateBy"]}
            return latest_page_info
        except Exception as e:
            return {}
        
    # 获取页面标签
    def get_page_tags(self, content_id):
        url = self.tag_url % (content_id)
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            res = json.loads(resp.content)['bo']
            # 使用列表推导式提取所有name值
            tags = [item['name'] for item in res]
            return tags
        except Exception as e:
            return []

    # 获取页面编辑内容
    def get_page_edit(self, content_id):
        url = self.page_edit_url % (content_id)
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            
            res = json.loads(resp.content)['bo']
            # print(json.dumps(res, indent=4, ensure_ascii=False))
            
            title = res.get('title')
            current_version = res.get('currentVersion')
            content_body = res.get('contentBody')
            if content_body is not None:
                return title, content_body, current_version
            else:
                return None, None, None
            
        except Exception as e:
            return None, None, None
        
    # 更新页面内容
    def set_page_edit(self, content_id, spaceId, title, content_body, current_version):
        url = self.page_update_url % (content_id, spaceId)
        json_data = {
            "employees": [],
            "groups": [],
            "groupKeyList": [],
            "urlTemplate": "",
            "contentBody": json.loads(json.dumps(content_body)),
            "spaceId": spaceId,
            "spaceName": "",
            "isLatestVersion": 'true',
            "title": title,
            "currentVersion": current_version,
            "summary": ""
        }
        
        # print(f"url:{url}")
        # print(f"json:{json.dumps(json_data, indent=4, ensure_ascii=False)}")
        # print(f"headers:{json.dumps(self.headers, indent=4, ensure_ascii=False)}")

        try:
            resp = requests.post(url, json=json_data, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON

            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                return True  # 成功返回 True 或 resp_json_data
            else:
                print(f"Failed to update page tag: {resp_json_data}")
                time.sleep(1)
                return False

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while adding tag: {e}")
            return False
        # 更新页面内容
    
    def page_set(self, content_id, spaceId, title, content_body, current_version, request_type='old'):
        url = self.page_update_url % (content_id, spaceId)
        json_data = {
            "employees": [],
            "groups": [],
            "groupKeyList": [],
            "urlTemplate": "",
            "contentBody": content_body,
            "spaceId": spaceId,
            "spaceName": "",
            "isLatestVersion": 'true',
            "title": title,
            "currentVersion": current_version if current_version else "",
            "summary": ""
        }
        if request_type == "new":
            url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/content/%s/updateContent?spaceId=%s" % (content_id, spaceId)
            json_data = {
                "docType": "HTML",
                "title": title,
                "text": content_body
            }
        
        try:
            resp = requests.post(url, json=json_data, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON

            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                return True  # 成功返回 True 或 resp_json_data
            else:
                print(f"Failed to update page tag: {resp_json_data}")
                time.sleep(1)
                return False

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while adding tag: {e}")
            return False

    # 更新页面内容 20230129 dingtao
    def update_icenter_content(self, contentid, BodyupdateHandler = None, TitleupdateHandler = None, content_body = None):
        try:
            responseJson, edit_flag = self.ICENTER_api.icenter_content_put(contentid, BodyupdateHandler, TitleupdateHandler, content_body = content_body)
            response = responseJson.json()
            return response, edit_flag
        except Exception as e:
            print (u'Json获取访问记录失败->', contentid, str(e))

    def get_page_view_count(self, url):
        """
        获取指定页面的浏览量和访客数据

        :param url: iCenter Wiki 页面 URL
        :return: dict 包含 totalViewCount（总浏览量）、totalVisitorCount（总访客数）、
                 datas（访客明细列表），失败返回 None
        """
        page_id, space_id = self.get_pageid_spaceid(url)

        # print(f"[get_page_view_count] url: {url}")
        # print(f"[get_page_view_count] page_id: {page_id}, space_id: {space_id}")

        base_url = "https://icosg.dt.zte.com.cn/studio-ispace/plugin/macro/execute"

        # 构建请求体
        body = {
            "macroKey": "PageViewMacro",
            "macroData": {
                "contentId": page_id,
                "contentName": "",
                "currentContentId": page_id,
                "level": "descendants",
                "limit": 10,
                "macroId": "01k3x1qrhdbssemf703vbsw2x859q4w2",
                "offset": 0,
                "spaceId": space_id,
            }
        }

        # print(f"[get_page_view_count] base_url: {base_url}")
        # print(f"[get_page_view_count] body: {json.dumps(body, ensure_ascii=False)}")

        # 此接口 appCode 与默认不同，需要覆盖
        headers = self.headers2.copy()
        headers['appCode'] = '500a0dc294334562b0e62b6d73abafff'

        try:
            response = requests.post(
                base_url,
                data=json.dumps(body),
                headers=headers,
                auth=self.auth,
                proxies=self.proxies,
                timeout=10
            )
        except Exception as e:
            logger.error(f"Request failed when fetching page view count: {e}")
            return None

        try:
            # print(f"[get_page_view_count] status_code: {response.status_code}")
            # print(f"[get_page_view_count] response.text: {response.text}")

            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return None

            resp_json = response.json()

            # print(f"[get_page_view_count] resp_json: {json.dumps(resp_json, ensure_ascii=False)}")

            # 检查返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "")
                logger.error(f"API call failed: {err_msg}")
                return None

            bo_data = resp_json.get("bo", {})
            if not bo_data:
                logger.warning("No page view data returned from API.")
                return None

            # 解析访客明细列表
            visitor_list = []
            for item in bo_data.get("datas", []):
                visitor_list.append({
                    "userId": item.get("userId", ""),
                    "user": item.get("user", ""),
                    "accountId": item.get("accountId", ""),
                    "latestViewTime": item.get("latestViewTime", ""),
                    "viewCount": item.get("viewCount", 0),
                })

            result = {
                "totalViewCount": bo_data.get("totalViewCount", 0),
                "totalVisitorCount": bo_data.get("totalVisitorCount", 0),
                "datas": visitor_list,
            }

            # print(f"[get_page_view_count] totalViewCount: {result['totalViewCount']}, totalVisitorCount: {result['totalVisitorCount']}, datas_count: {len(visitor_list)}")

            return result

        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return None


    def get_page_statistics(self, spaceId, contentId):
        url = f"https://icenterapi.zte.com.cn/zte-rd-icenter-advanced/statistics/content/{contentId}/pageShareCount"

        params = {
            "spaceId": spaceId,
            "level": "current",
            "system": "space-1921402263",
            "environmentType": "browser",
        }
        headers = {
            "X-Auth-Value": self.token,
            "X-Cookie-From-Cros": "Y",
            "X-Emp-No": self.account,
            "X-Lang-Id": "zh_CN",
            "X-Tenant-Id": "ZTE",
            "Cookie": "JSESSIONID=6C22DCBDAB493B467A539A50EF233A17",
        }

        def _to_int(v):
            if v is None:
                return None
            if isinstance(v, bool):
                return None
            if isinstance(v, int):
                return v
            if isinstance(v, float):
                return int(round(v))
            if isinstance(v, str):
                vv = v.strip()
                if not vv:
                    return None
                try:
                    return int(float(vv))
                except Exception:
                    return None
            return None

        def _extract_edit_count(item: dict):
            if not isinstance(item, dict):
                return None
            # 常见字段名
            for key in ("editCount", "edit_count", "editNum", "edit_num", "editCnt", "editCountNum"):
                if key in item:
                    cnt = _to_int(item.get(key))
                    if cnt is not None:
                        return cnt
            # 扫描键名：同时包含 edit 和 count
            try:
                for k, v in item.items():
                    if not isinstance(k, str):
                        continue
                    kl = k.lower()
                    if "edit" in kl and "count" in kl:
                        cnt = _to_int(v)
                        if cnt is not None:
                            return cnt
            except Exception:
                pass
            # 一层嵌套
            for nest_key in ("value", "data", "stat"):
                nest = item.get(nest_key)
                if isinstance(nest, dict):
                    cnt = _to_int(nest.get("editCount"))
                    if cnt is not None:
                        return cnt
            return None

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[ICENTER_DEBUG] get_page_statistics status={response.status_code}")
                return None, 0, 0

            json_data = response.json()
            bo_value = json_data.get("bo")
            if bo_value is None:
                return None, 0, 0

            # bo 可能是 list，也可能是 dict 包了 rows/data
            if isinstance(bo_value, list):
                items = bo_value
            elif isinstance(bo_value, dict):
                items = bo_value.get("rows") or bo_value.get("data") or bo_value.get("list") or []
            else:
                items = []

            filtered = []
            edit_sum = 0
            for item in items:
                cnt = _extract_edit_count(item)
                if cnt is None:
                    continue
                if cnt > 0:
                    filtered.append(item)
                edit_sum += cnt

            # Debug：前 3 次打印 bo 结构/字段名，帮你确认实际字段
            try:
                dbg_cnt = getattr(self.get_page_statistics, "_dbg_cnt", 0)
                if dbg_cnt < 3:
                    dbg_cnt = dbg_cnt + 1
                    self.get_page_statistics._dbg_cnt = dbg_cnt
                    print("[ICENTER_DEBUG] get_page_statistics bo_type:", type(bo_value))
                    if isinstance(bo_value, dict):
                        print("[ICENTER_DEBUG] bo_keys:", list(bo_value.keys())[:40])
                    if isinstance(items, list):
                        print("[ICENTER_DEBUG] items_len:", len(items))
                        if items and isinstance(items[0], dict):
                            print("[ICENTER_DEBUG] first_item_keys:", list(items[0].keys())[:40])
                    print("[ICENTER_DEBUG] computed:", {"editor_num": len(filtered), "edit_sum": edit_sum})
            except Exception:
                pass

            return filtered, len(filtered), edit_sum
        except requests.exceptions.RequestException as e:
            print(f"[ICENTER_DEBUG] get_page_statistics request failed: {e}")
            return None, 0, 0
        except Exception as e:
            print(f"[ICENTER_DEBUG] get_page_statistics parse failed: {e}")
            return None, 0, 0

    # AI采纳率
    def get_ai_adapt(self, spaceId, contentId):
        url_ado = "https://icosg.dt.zte.com.cn/studio-ispace/ai/adoption/stats/query"
        payload_ado = {
            "spaceId": spaceId,
            "pageId": contentId,
            "statisticsLevel": "PAGE_LEVEL"
        }
        headers = {
            "x-emp-no": self.account,
            "X-Auth-Value": self.token,
            "appcode": APP_CODE,
            "Content-Type": "application/json"
        }
        try:
            response_ado = requests.post(url_ado, data=json.dumps(payload_ado), headers=headers, timeout=10)
            if response_ado.status_code != 200:
                time.sleep(1)
                response_ado = requests.post(url_ado, data=json.dumps(payload_ado), headers=headers, timeout=10)
            json_response_ado = response_ado.json()
            bo = json_response_ado.get("bo", {}) or {}
            adoption_rate = bo.get("adoptionRate", "0")
            # Debug：前 3 次打印 response 里 bo 的字段（排查字段名/返回值为何为 0）
            try:
                dbg_cnt = getattr(self.get_ai_adapt, "_dbg_cnt", 0)
                if dbg_cnt < 3:
                    dbg_cnt = dbg_cnt + 1
                    self.get_ai_adapt._dbg_cnt = dbg_cnt
                    print("[ICENTER_DEBUG] get_ai_adapt bo_keys:", list(bo.keys())[:40])
                    print("[ICENTER_DEBUG] get_ai_adapt adoptionRate(raw):", adoption_rate)
            except Exception:
                pass

            if adoption_rate in ("0", 0, 0.0, None, "", "0.0"):
                return 0.0
            rounded = round(float(adoption_rate), 4)
            percent = round(rounded * 100, 2)
            return float(f"{percent:.2f}")
        except Exception:
            return 0.0

    # AI生成率
    def get_ai_gene(self, spaceId, contentId):
        try:
            url_gene = "https://icosg.dt.zte.com.cn/studio-ispace/ai/generation/stats/query"
            payload_gene = {
                "spaceId": spaceId,
                "pageId": contentId,
                "spaceFrom": "DOC_FROM",
            }
            headers = {
                "x-emp-no": self.account,
                "X-Auth-Value": self.token,
                "appcode": APP_CODE,
                "Content-Type": "application/json",
            }
            response_gene = requests.post(url_gene, data=json.dumps(payload_gene), headers=headers, timeout=10)
            if response_gene.status_code != 200:
                time.sleep(1)
                response_gene = requests.post(url_gene, data=json.dumps(payload_gene), headers=headers, timeout=10)
            json_response_gene = response_gene.json()
            bo = json_response_gene.get("bo", {}) or {}
            generation_rate = bo.get("generationRate", "0")
            # Debug：前 3 次打印 response 里 bo 的字段（排查字段名/返回值为何为 0）
            try:
                dbg_cnt = getattr(self.get_ai_gene, "_dbg_cnt", 0)
                if dbg_cnt < 3:
                    dbg_cnt = dbg_cnt + 1
                    self.get_ai_gene._dbg_cnt = dbg_cnt
                    print("[ICENTER_DEBUG] get_ai_gene bo_keys:", list(bo.keys())[:40])
                    print("[ICENTER_DEBUG] get_ai_gene generationRate(raw):", generation_rate)
            except Exception:
                pass

            if generation_rate in ("0", 0, 0.0, None, "", "0.0"):
                return 0.0
            rounded = round(float(generation_rate), 4)
            percent = round(rounded * 100, 2)
            return float(f"{percent:.2f}")
        except Exception:
            return 0.0

    #添加标签
    def add_page_tags(self, content_id:str, tag_name:str='大模型'):
        url = self.tag_url % (content_id)
        json_data = {
            "name": tag_name
        }

        try:
            resp = requests.post(url, json=json_data, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON

            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                return True  # 成功返回 True 或 resp_json_data
            else:
                print(f"Failed to add tag: {resp_json_data}")
                time.sleep(1)
                return False

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while adding tag: {e}")
            return False




    # 获取icenter最近100条变更
    def get_history_time(self, contentid, spaceid):
        url = self.history_url % (contentid, spaceid, 200, 0)
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
        except Exception as e:
            # logger.error("Fail to get page:space_id:{}, page_id:{}".format(self.space_id, content_id))
            return None
        reps_json_data = json.loads(resp.content)
        try:
            if resp.status_code != 200 or reps_json_data["code"]["msgId"] != 'RetCode.Success':
                time.sleep(1)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
                print(resp.status_code)
                reps_json_data = json.loads(resp.content)
        except Exception as e:
            logger.error(e)
            return None
        historyid_list = reps_json_data['bo']['rows']
        return historyid_list

    def get_history_content(self, content_id, space_id, history_id):
        try:
            time.sleep(0.8)
            url = self.history_detail_url % (content_id, history_id, space_id, history_id)
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if 'bo' in json.loads(resp.content):
                rawContent = json.loads(resp.content)['bo']
                return rawContent["contentBody"]
            else:
                return ''
        except Exception as e:
            return ''

    # 获取页面的第一个表格
    def get_person_info(self, html_text):
        person_info_dict = {}
        if html_text:
            content = BeautifulSoup(html_text, 'html.parser')
            target_table = content.find('table')
            if target_table:
                try:
                    trs = target_table.find_all('tr')
                    for tr in trs:
                        th = tr.find('th')
                        if th and th.get_text().strip() == "页面设计状态":
                            person_info_dict["页面设计状态"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["页面设计状态"])
                            if matches:
                                person_info_dict["页面设计状态"] = ', '.join(matches)
                        if th and th.get_text().strip() == "BA":
                            person_info_dict["BA"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["BA"])
                            if matches:
                                person_info_dict["BA"] = ', '.join(matches)
                        if th and th.get_text().strip() == "领域名称":
                            person_info_dict["领域名称"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["领域名称"])
                            if matches:
                                person_info_dict["领域名称"] = ', '.join(matches)
                        if th and th.get_text().strip() == "SE":
                            person_info_dict["SE"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["SE"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["SE"])
                                if matches:
                                    person_info_dict["SE"] = ', '.join(matches)
                        if th and th.get_text().strip() == "TL":
                            person_info_dict["TL"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["TL"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["TL"])
                                if matches:
                                    person_info_dict["TL"] = ', '.join(matches)
                        if th and th.get_text().strip() == "TSE":
                            person_info_dict["TSE"] = th.find_next_sibling('td').get_text().strip().replace("\ufeff", "")
                            if ',' not in person_info_dict["TSE"]:
                                matches = re.findall(r'([\u4e00-\u9fa5]+[\d]+)', person_info_dict["TSE"])
                                if matches:
                                    person_info_dict["TSE"] = ', '.join(matches)
                        if th and th.get_text().strip() == "页面设计状态":
                            td = th.find_next_sibling('td')
                            select_tag = td.find('select')
                            if select_tag:
                                selected_option = select_tag.find('option', selected=True)
                                if selected_option:
                                    person_info_dict["page_status"] = selected_option.get_text().strip().replace("\ufeff", "")
                                else:
                                    person_info_dict["page_status"] = ''
                            else:
                                person_info_dict["page_status"] = td.get_text().strip().replace("\ufeff", "")
                except Exception as e:
                    # global_logger.info(f"获取表格信息失败，{e}")
                    print(1111111)
        return person_info_dict
    
    def create_page(self, spaceId, parentId, title, contentBody:str="", templateId:str="", request_type:str="old"):
        # url = self.page_create_url % (spaceId, parentId)
        url = self.page_create_url % spaceId
        json_data = {
            "parentId": parentId,
            "spaceId": spaceId,
            "title": title,
            "text": contentBody,
            "dataType": "HTML"
        }
        if request_type == "new":
            url = "https://icenterapi.zte.com.cn/zte-rdcloud-space-content/content?spaceId=%s" % spaceId
            json_data = {
                "parentId": parentId,
                "spaceId": spaceId,
                "title": title
            }
            if templateId.strip():
                json_data["templateId"] = templateId
        
        try:
            resp = requests.post(url, json=json_data, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON
            resp_flag = False
            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                # return True  # 成功返回 True 或 resp_json_data
                resp_flag = True
            else:
                print(f"Failed to create page: {resp_json_data}")
                time.sleep(1)
            return resp_json_data, resp_flag

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while create page: {e}")
            return {}, False
    # 批量检查内容的标题在指定父节点下是否存在。
    def is_exist(self, spaceId, parentId, title):
        url = self.page_exist_url 
        json_data = [{
            "title":title,
            "spaceId":spaceId,
            "parentId":parentId
        }]
        
        try:
            resp = requests.post(url, json=json_data, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON
            resp_flag = False
            page_id = ""
            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                # return True  # 成功返回 True 或 resp_json_data
                bo = resp_json_data.get("bo", [])
                if bo and bo[0].get("id", ""):
                    resp_flag = True
                    page_id = bo[0].get("id", "")
            else:
                print(f"Failed to judge page is_exist: {resp_json_data}")
                time.sleep(1)
            return resp_flag, page_id

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while judge page is_exist: {e}")
            return False, ""
        
    def delete_page(self, spaceId, parentId, multi):
        url = self.page_delete_url % (parentId, spaceId, multi)
        
        try:
            resp = requests.delete(url, headers=self.headers, proxies=self.proxies)
            
            # 解析响应数据
            resp_json_data = resp.json()  # 更简洁的方式解析 JSON
            resp_flag = False
            if resp.status_code == 200 and resp_json_data.get("code", {}).get("msgId") == 'RetCode.Success':
                # return True  # 成功返回 True 或 resp_json_data
                resp_flag = True
            else:
                print(f"Failed to delete page: {resp_json_data}")
                time.sleep(1)
            return resp_flag

        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"Error occurred while delete page: {e}")
            return False
    
    def get_template_list(self, space_id):
        result = dict()
        try:
            time.sleep(0.8)
            url = self.template_url % space_id
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if 'bo' in json.loads(resp.content):
                rawContents = json.loads(resp.content)['bo']
                for rawContent in rawContents:
                    result[rawContent["title"]] = (rawContent["id"], rawContent['updateDate'])
                return result
            else:
                return result
        except Exception as e:
            return result
        
    def get_template_contents(self, template_id, space_id):
        result = ''
        try:
            time.sleep(0.8)
            url = self.template_content_url % (template_id, space_id)
            resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if resp.status_code != 200:
                time.sleep(2)
                resp = requests.get(url, auth=self.auth, headers=self.headers, proxies=self.proxies)
            if 'bo' in json.loads(resp.content):
                rawContents = json.loads(resp.content)['bo']
                return  rawContents['contentBody']
            else:
                return result
        except Exception as e:
            return result
    
    def get_page_operate_log(self, space_id, content_id, start=0, count=10):
        """
        获取页面操作日志（空间 2.0 API）
        
        :param space_id: 空间 ID
        :param content_id: 内容 ID（页面 ID）
        :param start: 起始偏移量，默认 0
        :param count: 每页数量，默认 10
        :return: 操作日志列表，失败返回空列表
        """
        
        try:
            url = self.operate_log_url % (space_id, content_id)
            headers = {
                "x-emp-no": "10210415",  # 工号
                "X-Auth-Value": "00da230806a936d53f79a6daca44b783",  # token
                "appcode": "500a0dc294334562b0e62b6d73abafff",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            body = {
                "start": start,
                "count": count
            }
            
            response = requests.post(url, headers=headers, json=body)
        except Exception as e:
            logger.error(f"Request failed when fetching operate log: {e}")
            return []
        
        try:
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return []
            
            resp_json = response.json()
            
            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Get operate log failed: {err_msg}")
                return []
            
            # 提取操作日志数据
            bo_data = resp_json.get("bo", [])
            if not bo_data:
                logger.warning("No operate log found.")
                return []
            
            return bo_data
            
        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return []
    
    def get_page_flower_detail(self, space_id, content_id, offset=0, limit=100):
        """
        获取页面点赞详情信息（空间 2.0 API）
        
        :param space_id: 空间 ID
        :param content_id: 内容 ID（页面 ID）
        :param offset: 分页偏移量，默认 0
        :param limit: 每页数量，默认 100
        :return: 点赞详情列表，失败返回空列表
        """
        
        try:
            url = self.flower_detail_url % (content_id, offset, limit, space_id)
            headers = {
                "x-emp-no": "10210415",  # 工号
                "X-Auth-Value": "00da230806a936d53f79a6daca44b783",  # token
                "appcode": "500a0dc294334562b0e62b6d73abafff",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
        except Exception as e:
            logger.error(f"Request failed when fetching flower detail: {e}")
            return []
        
        try:
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return []
            
            resp_json = response.json()
            
            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Get flower detail failed: {err_msg}")
                return []
            
            # 提取点赞详情数据
            bo_data = resp_json.get("bo", [])
            if not bo_data:
                logger.info("No flower detail found.")
                return []
            
            return bo_data
            
        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return []
    
    def get_page_tags_v2(self, space_id, content_id):
        """
        获取页面标签信息（空间 2.0 API）
        
        :param space_id: 空间 ID
        :param content_id: 内容 ID（页面 ID）
        :return: 标签列表，失败返回空列表
        """

        try:
            url_ado = self.page_tags_url % (content_id, space_id)
            headers = {
                "x-emp-no": "10210415",  # 工号
                "X-Auth-Value": "00da230806a936d53f79a6daca44b783",  # token
                "appcode": "500a0dc294334562b0e62b6d73abafff",
                "Content-Type": "application/json"
            }
            response = requests.get(url_ado, headers=headers)
        except Exception as e:
            logger.error(f"Request failed when fetching page tags: {e}")
            return []
        
        try:
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return []
            
            resp_json = response.json()
            
            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Get page tags failed: {err_msg}")
                return []
            
            # 提取标签数据
            bo_data = resp_json.get("bo", [])
            if not bo_data:
                logger.info("No tags found.")
                return []
            
            return bo_data
            
        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return []
    
    def get_page_detail(self, space_id, content_id):
        """
        获取页面详情信息（空间 2.0 API）
        
        :param space_id: 空间 ID
        :param content_id: 内容 ID（页面 ID）
        :return: 页面详情字典，包含标题、内容等信息，失败返回 None
        """
        
        try:
            url = self.page_detail_url % (content_id, space_id)
            headers = {
                "x-emp-no": "10210415",  # 工号
                "X-Auth-Value": "00da230806a936d53f79a6daca44b783",  # token
                "appcode": "500a0dc294334562b0e62b6d73abafff",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
        except Exception as e:
            logger.error(f"Request failed when fetching page detail: {e}")
            return None
        
        try:
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return None
            
            resp_json = response.json()
            
            # 检查业务返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "") or "Unknown error"
                logger.error(f"Get page detail failed: {err_msg}")
                return None
            
            # 提取页面详情数据
            bo_data = resp_json.get("bo", {})
            if not bo_data:
                logger.warning("No page detail found.")
                return None
            
            return bo_data
            
        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return None


def overwrite_file(file_path, title, content):
    """
    将内容覆盖写入指定文件
    
    :param file_path: 要写入的文件路径
    :param content: 要写入的文本内容
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(title+'\n\n'+content)
        print(f"内容已成功写入文件: {file_path}")
    except IOError as e:
        print(f"写入文件时出错: {e}")

def Get_icenter(url):
    """从iCenter平台获取指定页面的内容及相关信息
    
    通过给定的iCenter页面URL，获取页面标题、原始内容、Markdown格式内容，
    以及页面的人员信息、目录结构和子页面信息。

    Args:
        url (str): iCenter页面的完整URL，例如：
                  'https://icenter.tsinghua.edu.cn/{spaceId}/wiki/{pageId}/'

    Returns:
        tuple: 包含以下元素的元组：
            - title (str): 页面标题
            - content (str): 页面的原始HTML内容
            - content_markdown (str): 转换为Markdown格式的内容

    示例:
        >>> title, content, md = Get_icenter('https://icenter.tsinghua.edu.cn/123/wiki/456/')
        >>> print(title)
    """
    icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]

    historyid_list = icentapi.get_history_time(pageId, spaceId)
    content, title = icentapi.get_page_info(spaceId, pageId)
    latest_page_info = icentapi.get_latest_page_info(spaceId, pageId)
    tag = icentapi.get_page_tags(pageId)

    finalize = icentapi.get_person_info(content)
    catalog = icentapi.get_catalog(content)
    # childrenIds = icentapi.get_first_children(spaceId, pageId)

    content_markdown = markdownify.markdownify(content)  # 直接传入 response.text

    # 获取编辑、AI生成率、浏览量等信息
    # view 接口在不同分支可能不存在：这里做兜底，避免采集直接崩溃
    # view_data = {}
    # try:
    #     view_data = icentapi.icenter_contents_ic_macro(spaceId, pageId) or {}
    # except AttributeError:
    #     view_data = {}
    # except Exception:
    #     view_data = {}
    # 初始化默认值都为 0，即使异常也保持 0 更合理
    view_data = {"totalVisitorCount": 0, "totalViewCount": 0}
    try:
        view_ret = icentapi.get_page_view_count(url)
        # 取不到数据 或 数据为None 时，自动赋值 0
        view_data["totalVisitorCount"] = view_ret.get("totalVisitorCount", 0) or 0
        view_data["totalViewCount"] = view_ret.get("totalViewCount", 0) or 0
    except Exception as e:
        print(f"接口报错: {e}")
    latest_page_info["view"] = view_data

    edit_info_list, editor_num, edit_num = icentapi.get_page_statistics(spaceId, pageId)
    latest_page_info["edit"] = {
        "edit_info_list": edit_info_list,
        "editor_num": editor_num,
        "edit_num": edit_num,
    }

    latest_page_info["ai"] = {
        "ai_adapt_num": icentapi.get_ai_adapt(spaceId, pageId),
        "ai_gene_num": icentapi.get_ai_gene(spaceId, pageId),
    }

    return title, content, content_markdown, latest_page_info

def Set_icenter(url, title=None, content=None):
   """
   通用接口，用于更新 iCenter 页面内容
   
   :param url: iCenter 页面 URL
   :param title: 新的页面标题（可选，如果不提供则保持原标题）
   :param content: 新的页面内容，HTML 格式（可选，如果不提供则保持原内容）
   :return: bool - 更新是否成功
   """
   # 创建 IcenterAPI 实例
   icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
   
   # 解析 URL 获取 spaceId 和 contentId
   content_id, space_id = icenterapi.get_pageid_spaceid(url)
   
   # 如果没有提供新的标题或内容，则获取当前页面的标题和内容
   if title is None or content is None:
       current_title, _, _, _ = Get_icenter(url)
       if title is None:
           title = current_title
   
   # 使用新的 set_page_content 方法更新页面
   result = icenterapi.set_page_content(
       content_id=content_id,
       space_id=space_id,
       title=title,
       content=content,
   )
   
   return result

def Icenter_title_get(url):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    contentid, spaceid = icenterapi.get_pageid_spaceid(url)
    content, title = icenterapi.get_page_info(spaceid, contentid)
    return title

def Icenter_content_html_get(url):
    title, content, content_markdown, latest_page_info = Get_icenter(url)
    return content

def Icenter_content_html_set(url, html):
    icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]

    # 获取页面内容与当前版本
    title, content_body, current_version = icentapi.get_page_edit(pageId)
    if not current_version:
        # 没有查询到版本号，尝试空间2.0的接口
        bo_data = icentapi.get_page_info(spaceId, pageId, type='whole')
        if not bo_data.get('currentVersion', ''):
            # 空间2.0如果返回标题为空，说明1.0和2.0都失败
            print("无法获取当前版本号，终止更新")
            return False
        else:
            current_version = bo_data['currentVersion']

    # 更新页面
    result = icentapi.page_set(pageId, spaceId, title, html, current_version)

    return result    

def Icenter_children_get(url):
    """
    获取指定iCenter页面的所有子页面链接和对应标题

    Args:
        url (str): 父页面URL，格式如：
            https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view

    Returns:
        tuple: 包含三个元素的元组：
            - 第一个元素是子页面完整URL列表 (list of str)
            - 第二个元素是子页面标题列表 (list of str)
            - 第三个元素是标题到URL的映射字典 (dict: { title: url })
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))    
    contentid, spaceid = icenterapi.get_pageid_spaceid(url)    
    result = icenterapi.get_first_children(spaceid, contentid)

    # 关键修复：处理 None 的情况
    if not result:  # None 或 空列表 都视为无子页面
        return [], [], {}

    # children_url = []
    # children_title = []
    # children_map = {}

    # for child_id in children_id:
    #     child_url = url.replace(contentid, child_id)
    #     children_url.append(child_url)
    #     title = Icenter_title_get(child_url)
    #     children_title.append(title)
    #     children_map[title] = child_url

    return list(result.values()), list(result.keys()), result


def Icenter_block_get(url, block_id, block_title, block_tag):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))    
    contentid, spaceid = icenterapi.get_pageid_spaceid(url)
    block_content,title = icenterapi.get_page_block_content(spaceid, contentid, block_id, block_title, block_tag, "MARKDOWN")
    return block_content

def Icenter_block_set(url, block_id, block_title, block_tag, block_content):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    contentid, spaceid = icenterapi.get_pageid_spaceid(url)
    
    # 将markdown内容转换为HTML，启用表格扩展
    block_content_html = markdown.markdown(block_content, extensions=['tables'])

    res = icenterapi.set_block_content(spaceid, contentid, block_id, block_title, block_tag, block_content_html)
    return res

def Icenter_comment_add(url, comment):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    content_id, space_id = icenterapi.get_pageid_spaceid(url)
    result = icenterapi.add_comment(content_id, space_id, comment)
    return result


def Icenter_add_page(spaceId, parentId, title, content='', templateId=""):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    result = icenterapi.create_page(spaceId, parentId, title, content, templateId)
    return result


def Icenter_new_page(url, title, content=""):
    """
    新建页面（基于2.0版本API）
    
    :param url: iCenter页面URL，用于解析空间ID和父页面ID
    :param title: 页面标题
    :param content: 页面内容，Markdown格式字符串，默认为空（将自动转换为HTML格式）
    :return: 成功时返回新创建页面的URL，失败时返回None
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    pageId, spaceId = icenterapi.get_pageid_spaceid(url)
    
    # 将Markdown格式的内容转换为HTML格式，启用表格扩展
    html_content = ""
    if content.strip():
        html_content = markdown.markdown(content, extensions=['tables'])
    
    result = icenterapi.new_page(spaceId, pageId, title, html_content)
    
    # 如果创建成功，从响应中提取新的页面ID并构建新的URL
    if result is not None:
        # 检查响应格式，bo字段可能是字符串或字典
        bo_data = result.get('bo')
        if bo_data is not None:
            # 如果bo是字符串，直接作为新的页面ID
            if isinstance(bo_data, str):
                new_page_id = bo_data
            # 如果bo是字典，尝试从中提取页面ID
            elif isinstance(bo_data, dict):
                new_page_id = bo_data.get('id', '')
            else:
                # 其他格式，尝试转换为字符串
                new_page_id = str(bo_data)
            
            # 如果成功获取到新的页面ID，构建新的URL
            if new_page_id:
                # 使用set_pageid_spaceid方法替换URL中的页面ID
                new_url = icenterapi.set_pageid_spaceid(url, new_page_id, "")
                return new_url
    
    # 如果创建失败或无法提取页面ID，返回None
    return None


def Icenter_page_isexist(spaceId, parentId, title):
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    result = icenterapi.is_exist(spaceId, parentId, title)
    return result


def Get_icenter_markdown(url):
    title, content, content_markdown, latest_page_info = Get_icenter(url)
    icenter_markdown = f"# {title}\n{content_markdown}\n最后更新时间： {latest_page_info['updateDate']}"
    return icenter_markdown

def Set_icenter_markdown(url, content_markdown):
    """
    用于更新 iCenter 页面内容，接收markdown格式的内容
    
    :param url: iCenter 页面 URL
    :param content_markdown: 新的页面内容，Markdown 格式
    :return: bool - 更新是否成功
    """
    # 获取当前页面信息
    title, _, _, _ = Get_icenter(url)
    
    # 将markdown内容转换为HTML，启用表格扩展
    content_html = markdown.markdown(content_markdown, extensions=['tables'])
    
    # 调用Set_icenter函数更新页面
    result = Set_icenter(
        url=url,
        title=title,  # 保持原有标题
        content=content_html  # 传递转换后的HTML内容
    )
    
    return result

def Get_icenter_title_markdown(url):
    title, content, content_markdown, latest_page_info = Get_icenter(url)
    icenter_markdown = f"# {title}\n{content_markdown}\n最后更新时间： {latest_page_info['updateDate']}"
    return title, icenter_markdown


def Get_icenter_content_markdown(url):
    title, content, content_markdown, latest_page_info = Get_icenter(url)
    return content_markdown

def Get_icenter_html(url):
    title, content, content_markdown, latest_page_info = Get_icenter(url)
    icenter_content = f"# {title}\n{content}\n最后更新时间： {latest_page_info['updateDate']}"
    return icenter_content


def Get_icenter_table(url, tableIndex = 1):
    icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]

    table_content = icentapi.icenter_table_get(spaceId, pageId, tableIndex)
    # print(table_content)
    return table_content


def Get_icenter_parentpath(url):
    icentapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    parts = url.split('/')
    spaceId_index = parts.index('wiki') - 1
    spaceId = parts[spaceId_index]
    pageId = parts[-2]

    bo = icentapi.get_page_info(spaceId, pageId, 'all')
    # print(bo['parentPath'])
    return bo['parentPath']


def Get_icenter_operate_log(url, start=0, count=10):
    """
    获取 iCenter 页面的操作日志
    
    :param url: iCenter 页面 URL，格式如：
               https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view
    :param start: 起始偏移量，默认 0
    :param count: 每页数量，默认 10
    :return: 操作日志列表，每个日志项包含操作人、操作时间、操作类型等信息
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    content_id, space_id = icenterapi.get_pageid_spaceid(url)
    
    if not content_id or not space_id:
        logger.error("Invalid URL format, cannot extract space_id and content_id")
        return []
    
    operate_logs = icenterapi.get_page_operate_log(space_id, content_id, start=start, count=count)
    return operate_logs


def Get_icenter_flower_detail(url, offset=0, limit=100):
    """
    获取 iCenter 页面的点赞详情信息
    
    :param url: iCenter 页面 URL，格式如：
               https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view
    :param offset: 分页偏移量，默认 0
    :param limit: 每页数量，默认 100
    :return: 点赞详情列表，包含点赞人、点赞时间等信息
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    content_id, space_id = icenterapi.get_pageid_spaceid(url)
    
    if not content_id or not space_id:
        logger.error("Invalid URL format, cannot extract space_id and content_id")
        return []
    
    flower_details = icenterapi.get_page_flower_detail(space_id, content_id, offset, limit)
    return flower_details


def Get_icenter_tags_v2(url):
    """
    获取 iCenter 页面的标签信息（空间 2.0 API）
    
    :param url: iCenter 页面 URL，格式如：
               https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view
    :return: 标签列表，包含标签名称、ID 等信息
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    content_id, space_id = icenterapi.get_pageid_spaceid(url)
    
    if not content_id or not space_id:
        logger.error("Invalid URL format, cannot extract space_id and content_id")
        return []
    
    tags = icenterapi.get_page_tags_v2(space_id, content_id)
    return tags


def Get_icenter_page_detail(url):
    """
    获取 iCenter 页面的详情信息（空间 2.0 API）
    
    :param url: iCenter 页面 URL，格式如：
               https://i.zte.com.cn/index/ispace/#/space/{spaceid}/wiki/page/{contentid}/view
    :return: 页面详情字典，包含以下信息：
             - title: 页面标题
             - contentBody: 页面内容（HTML 格式）
             - createBy: 创建人
             - updateDate: 更新时间
             - 等其他页面元数据
             失败返回 None
    """
    icenterapi = IcenterAPI(os.getenv('USERNAME'), os.getenv('PASSWORD'))
    content_id, space_id = icenterapi.get_pageid_spaceid(url)
    
    if not content_id or not space_id:
        logger.error("Invalid URL format, cannot extract space_id and content_id")
        return None
    
    page_detail = icenterapi.get_page_detail(space_id, content_id)
    return page_detail


def Content_body_update(content_body, data_json):
    # 如果 data_json 是字符串，则将其转换为字典
    if isinstance(data_json, str):
        data_json = json.loads(data_json)

    # print(json.dumps(data_json, indent=4, ensure_ascii=False))

    # 解析 HTML 内容
    content_body_update = BeautifulSoup(content_body, 'html.parser')
    # print(f"content_body_update:\n{content_body_update}")

    # 查找表格主体
    table = content_body_update.find('table')
    # tbody = table.find('tbody')
    # print(f"tbody:\n{tbody}")
    # print("----------------------------------------")

    # 遍历 tbody 中的所有 <tr>
    for row in table.find_all('tr'):
        # 判断是否是标题行：检查第一个子元素是否是 <th>
        first_cell = row.find(['th', 'td'])
        if first_cell and first_cell.name == 'th':
            continue  # 跳过标题行

        # 确保是数据行：查找所有 <td>
        cells = row.find_all('td')
        num_cell = cells[0]   # “序号”列
        output_cell = cells[4] # “输出”列

        # print(f"num_cell:{num_cell}")
        # print(f"output_cell:{output_cell}")

        num_name = num_cell.get_text(strip=True)
        if not num_name:
            continue  # 跳过没有任务名的行

        # print(f"num_name:{num_name}")
    
        # 查找第一个匹配的项
        matching_item = next((item for item in data_json if item.get("#") == num_name), None)

        if matching_item is not None:
            output_content = matching_item.get("输出", "")
            # print(f"output_content: {output_content}")

            # 将 Markdown 转换为 HTML，启用表格扩展
            output_content_html = markdown.markdown(output_content, extensions=['tables'])
            # print(output_content_html)

            # 更新 HTML 单元格
            output_cell.clear()
            new_paragraph = content_body_update.new_tag('p')
            new_paragraph.string = output_content_html
            output_cell.append(new_paragraph)
            # print(f"output_cell: {output_cell}")
        else:
            print(f"未找到 '#' 为 {num_name} 的条目")

    # print(content_body_update)

    # 返回更新后的 HTML 字符串
    return content_body_update.prettify(formatter=None)


def Icenter_table_update(url, table_json):
    # 获取页面
    content_body = Icenter_content_html_get(url)

    # 更新表格
    content_body_update = Content_body_update(content_body, table_json)

    # 更新页面
    rep = Icenter_content_html_set(url, content_body_update)

    return rep

def test_Icenter_titel_get():
    print(Icenter_title_get("https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/845d16f934a140b8a7aa97b819f6d6c6/view"))

def test_Icenter_children_get():
    print(Icenter_children_get("https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/845d16f934a140b8a7aa97b819f6d6c6/view"))

def test_Icenter_block_get_set():
    url = "https://i.zte.com.cn/index/ispace/#/space/bbb6e1d7fd774053b4c5a1b2fc8cb5e8/wiki/page/f2e671ab74fa11f0afa32bcf221343e4/view"
    block_id = ""
    block_title = "标题1名称"
    block_tag = ""

    print("读block")
    print(Icenter_block_get(url, block_id, block_title, block_tag))

    print("写block")
    print(Icenter_block_set(url, block_id, block_title, block_tag, "| 用例标题 | G（预置条件） | W（测试步骤） | T（预期结果） | 实际结果 |\n|---------|------------|------------|------------|----------|\n| LAG聚合组创建测试 | 1. 设备正常运行<br>2. 具备管理员权限 | 1. 登录设备管理界面<br>2. 进入LAG配置页面<br>3. 创建新的LAG聚合组<br>4. 配置聚合组参数 | 成功创建LAG聚合组，显示聚合组状态为未激活 | 待填写 |\n| LAG聚合组成员端口添加测试 | 1. LAG聚合组已存在<br>2. 至少有2个可用物理端口 | 1. 选择已存在的LAG聚合组<br>2. 添加物理端口到聚合组<br>3. 验证端口添加结果 | 物理端口成功加入LAG聚合组，聚合组成员列表更新 | 待填写 |"))


def test_Icenter_get_set():
    url = "https://i.zte.com.cn/index/ispace/#/space/bbb6e1d7fd774053b4c5a1b2fc8cb5e8/wiki/page/f2e671ab74fa11f0afa32bcf221343e4/view"
    content_html = Icenter_content_html_get(url)

    Icenter_content_html_set(url, content_html)


def test_Icenter_comment_add():
    url = "https://i.zte.com.cn/index/ispace/#/space/bbb6e1d7fd774053b4c5a1b2fc8cb5e8/wiki/page/f2e671ab74fa11f0afa32bcf221343e4/view"
    # HTML content example with proper formatting
    comment = "<p>这是一条带有HTML格式的评论内容。<br/>这里包含换行和<strong>加粗文本</strong>。</p><ul><li>列表项1</li><li>列表项2</li></ul>"
    result = Icenter_comment_add(url, comment)
    print(f"Comment addition result: {result}")
    return result

def test_Icenter_content_set():
   """测试Set_icenter_markdown方法"""
   url = "https://i.zte.com.cn/index/ispace/#/space/f0fec92cefba4aa18cb7876cd6078c23/wiki/page/50484426f3a211f0b3a7594ea3c9898c/view"
   
   # 测试更新页面内容，使用markdown格式
   markdown_content = "# 这是通过Set_icenter_markdown方法更新的新内容\n\n- 这里是列表项1\n- 这里是列表项2\n\n**这里是粗体文本**"
   
   result = Set_icenter_markdown(
       url=url,
       content_markdown=markdown_content
   )
   
   print(f"页面内容更新结果: {result}")
   return result


def test_Icenter_new_page():
    result = Icenter_new_page("https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/f8e50ab3f5d311f09ab957b11d3e710d/view", "这是一个测试页新建", "## 测试内容")
    return result


def test_Get_icenter_operate_log():
    """测试获取页面操作日志功能"""
    url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/f9b7092aeca011f09d6fa9a20935cc4c/view"
    
    print("获取页面操作日志...")
    
    # 示例 1：使用默认参数（start=0, count=10）
    logs = Get_icenter_operate_log(url)
    
    # 示例 2：使用自定义参数（取消注释以测试）
    # logs = Get_icenter_operate_log(url, start=0, count=20)  # 获取前 20 条
    
    if logs:
        # 确保 logs 是列表类型
        if isinstance(logs, list):
            print(f"共找到 {len(logs)} 条操作日志")
            print("\n最近 5 条操作日志:")
            for i, log in enumerate(logs[:5], 1):
                print(f"\n{i}. 操作日志详情:")
                # 根据实际返回的字段打印，这里假设常见字段
                if isinstance(log, dict):
                    for key, value in log.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   {log}")
        elif isinstance(logs, dict):
            # 如果返回的是字典，可能是 bo 字段在字典中
            bo_data = logs.get('bo', [])
            if isinstance(bo_data, list):
                print(f"共找到 {len(bo_data)} 条操作日志")
                print("\n最近 5 条操作日志:")
                for i, log in enumerate(bo_data[:5], 1):
                    print(f"\n{i}. 操作日志详情:")
                    if isinstance(log, dict):
                        for key, value in log.items():
                            print(f"   {key}: {value}")
                    else:
                        print(f"   {log}")
            else:
                print(f"操作日志数据格式异常：{type(bo_data)}")
                print(f"完整响应：{logs}")
        else:
            print(f"操作日志数据格式异常：{type(logs)}")
            print(f"完整响应：{logs}")
    else:
        print("未找到操作日志或获取失败")
    
    return logs


def test_Get_icenter_flower_detail():
    """测试获取页面点赞详情功能"""
    url = "https://i.zte.com.cn/index/ispace/#/space/bbb6e1d7fd774053b4c5a1b2fc8cb5e8/wiki/page/f2e671ab74fa11f0afa32bcf221343e4/view"
    
    print("获取页面点赞详情...")
    flowers = Get_icenter_flower_detail(url, offset=0, limit=100)
    
    if flowers:
        print(f"共找到 {len(flowers)} 个点赞")
        print("\n点赞详情:")
        for i, flower in enumerate(flowers[:10], 1):  # 只显示前 10 个
            print(f"\n{i}. 点赞详情:")
            if isinstance(flower, dict):
                for key, value in flower.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {flower}")
        
        if len(flowers) > 10:
            print(f"\n... 还有 {len(flowers) - 10} 个点赞")
    else:
        print("未找到点赞信息或获取失败")
    
    return flowers


def test_Get_icenter_tags_v2():
    """测试获取页面标签信息功能（空间 2.0 API）"""
    url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/f9b7092aeca011f09d6fa9a20935cc4c/view"
    
    print("获取页面标签信息...")
    tags = Get_icenter_tags_v2(url)
    
    if tags:
        print(f"共找到 {len(tags)} 个标签")
        print("\n标签详情:")
        for i, tag in enumerate(tags, 1):
            print(f"\n{i}. 标签详情:")
            if isinstance(tag, dict):
                for key, value in tag.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {tag}")
    else:
        print("未找到标签信息或获取失败")
    
    return tags


def test_Get_icenter_page_detail():
    """测试获取页面详情功能（空间 2.0 API）"""
    url = "https://i.zte.com.cn/index/ispace/#/space/fbff14a6a14c4985874248df3ac610c1/wiki/page/c08feaa01e6611f09cd5f179f8a94ed1/view"
    
    print("获取页面详情...")
    page_detail = Get_icenter_page_detail(url)
    
    if page_detail:
        print("\n页面详情:")
        print("=" * 50)
        
        # 打印常见字段
        common_fields = [
            'title',           # 标题
            'contentBody',     # 内容体
            'createBy',        # 创建人
            'updateDate',      # 更新时间
            'createDate',      # 创建时间
            'status',          # 状态
            'type',            # 类型
            'spaceId',         # 空间 ID
            'id'               # 页面 ID
        ]
        
        for field in common_fields:
            if field in page_detail:
                value = page_detail[field]
                # 如果内容太长，只显示前 100 字符
                if isinstance(value, str) and len(value) > 100:
                    print(f"{field}: {value[:100]}...")
                else:
                    print(f"{field}: {value}")
        
        # 打印所有其他字段
        print("\n其他字段:")
        for key, value in page_detail.items():
            if key not in common_fields:
                print(f"  {key}: {value}")
    else:
        print("未找到页面详情或获取失败")
    
    return page_detail


if __name__ == '__main__':
    # url = 'https://i.zte.com.cn/index/ispace/#/space/f0fec92cefba4aa18cb7876cd6078c23/wiki/page/ee35c580ae86427f8b7e08c36b8e91d4/view'
    # title, content, content_markdown,updatetime = Get_icenter(url)
    # print(updatetime['updateDate'])
    # print(type(updatetime))
    # print("\nHTML页面内容------------------------------------------------------------")
    # # print(title)
    # # print(content)

    # print("\nMarkdown页面内容------------------------------------------------------------")
    # print(title)
    # print(content_markdown)

    # overwrite_file("text.html", page_title, page_content)
    # overwrite_file("text.md", page_title_markdown, page_content_markdown)

    # 更新页面
    # url = 'https://i.zte.com.cn/index/ispace/#/space/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/a037cb677577469e979f5da1a7a77659/view'
    # table_json = [
    #     {'#': '2', 
    #      '任务': '陈雷的周报', 
    #      '输入': '[陈雷的周报](\n\n# 陈雷的周报\n5月目标：完成100分试卷打印。\n\n5月进展：已完成80份，还剩20份，进度正常。\n\n5月风险：无风险。\n\n "陈雷的周报")', 
    #      '提示词': '', 
    #      '输出': '### 陈雷的周报整理与要点提炼\n\n**目标：**\n- 完成100分试卷打印。\n\n**当前进展：**\n- 已完成80份试卷打印。\n- 剩余20份试卷待完成。\n- 整体进度正常，符合预期。\n\n**风险评估：**\n- 当前无任何风险。\n\n**总结：**\n项目进展顺利，已完成大部分工作，剩余任务量较小，暂未发现影响进度的风险。建议继续保持当前节奏，确保按时完成目标。'
    #      }, 
    #      {'#': '3', 
    #       '任务': '陈韬的周报', 
    #       '输入': '[陈韬的周报](\n\n# 陈韬的周报\n5月目标：完成100份眼镜制作。\n\n5月进展：已完成30份，还剩70份，进度缓慢。\n\n5月风险：风险1：原材料供应延误，导致进度延误2周左右。\n\n "陈韬的周报")', 
    #       '提示词': '', 
    #       '输出': '**周报整理与要点提炼：**\n\n**姓名：** 陈韬  \n**月份：** 5月  \n\n---\n\n### **目标：**\n- 完成100份眼镜制作。\n\n---\n\n### **当前进展：**\n- 已完成：30份  \n- 剩余任务：70份  \n- 进度评估：整体进度偏慢，需加快执行以达成目标。\n\n---\n\n### **风险与问题：**\n1. **原材料供应延误**  \n   - 影响：导致项目进度延迟约2周  \n   - 建议措施：尽快联系供应商确认交货时间，考虑备选方案或调整生产计划。\n\n---\n\n### **总结建议：**\n- 当前进度滞后，存在原材料延迟的风险。\n- 建议采取应对措施，确保后续工作顺利推进，并尽量减少延误影响。'
    #       }
    # ]
    # print(Icenter_table_update(url, table_json))

    # print(Get_icenter_markdown("https://i.zte.com.cn/index/ispace/#/space/c58964e8abbc45dbbe30d39d0308c7e9/wiki/page/845d16f934a140b8a7aa97b819f6d6c6/view"))

    # test_Icenter_titel_get()
    # test_Icenter_children_get()
    # test_Icenter_block_get_set()
    # test_Get_icenter_operate_log()
    test_Get_icenter_flower_detail()
    # test_Icenter_get_set()
    # test_Icenter_comment_add()  # Uncomment to test the new function
    # test_Icenter_comment_add()

    # test_Icenter_content_set()
    # test_Get_icenter_tags_v2()
    # print(test_Icenter_new_page())
    test_Get_icenter_page_detail()

