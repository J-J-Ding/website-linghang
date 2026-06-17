import json
import socket
import logging
import hashlib
import requests

logger = logging.getLogger("Logger")

class Icenter2API:
    def __init__(self, user_id, user_password, user_token):
        self.user_id = user_id
        self.user_password = user_password
        self.user_token = user_token
        self.loginsyscode = 'Portal'
        self.originsyscode = ''
        self.auth = requests.auth.HTTPDigestAuth(self.user_id, self.user_token) # pyright: ignore[reportAttributeAccessIssue]
        self.proxies = {"http": "", "https": ""}
        self.headers = {
                'Content-type': 'application/json', 
                'X-Emp-No': self.user_id, 
                'X-Auth-Value': self.user_token, 
                'X-Lang-Id': 'zh_CN',
                'appCode': '4811ee4055a74cb4b52e7295e1d1858d'}
    
        if user_password:
            self.user_token = self._get_user_token()

    def _get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    
    def _get_user_token(self):
        baseurl = "http://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
        hostip = self._get_host_ip()
        text = {
            "account": self.user_id,
            "passWord": self.user_password,
            "loginClientIp": hostip,
            "loginSystemCode": self.loginsyscode,
            "originSystemCode": self.originsyscode,
            "other": {
                "networkArea": '1',
                "networkAccessType": '1'
            },
            "verifyCode": hashlib.md5(
                str(self.user_id + self.user_password + hostip + self.loginsyscode + self.originsyscode).encode(
                    encoding='utf-8')).hexdigest()
        }
        headers = {'Content-type': 'application/json'}
        content = requests.post(baseurl, data=json.dumps(text), headers=headers).json()
        return content["other"]["token"]

    def get_space_page_id(self, url):
        parts = url.split('/')
        space_id_index = parts.index('wiki') - 1
        space_id = parts[space_id_index]
        page_id = parts[-2]
        return space_id, page_id

    def get_page_block_content(self, url, block_id=None, block_title=None, block_tags=None, content_type="HTML"):
        """
        获取指定页面中某个 block 的内容（支持通过 blockId/blockName/blockTag 查询）
        
        :param space_id: 空间ID
        :param page_id: 页面ID
        :param block_id: 区块ID (可选)
        :param block_title: 区块名称 (可选)
        :param block_tags: 区块标签 (可选)
        :param content_type: 返回内容格式，"HTML" 或 "MARKDOWN"，默认 HTML
        :return: (content: str, title: str) 如果失败返回 (None, None)
        """
        base_url = "https://icosg.dt.zte.com.cn/studio-ispace/doc/block/content/query"
        
        space_id, page_id = self.get_space_page_id(url)

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
            return None, None

        headers = self.headers.copy()

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
            logger.error(f"Request failed when fetching block content: {e}")
            return None, None

        try:
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return None, None

            resp_json = response.json()

            # 检查返回码
            code = resp_json.get("code", {})
            if code.get("msgId") != "RetCode.Success":
                err_msg = code.get("msg", "") or code.get("errMsg", "")
                logger.error(f"API call failed: {err_msg}")
                return None, None

            # bo 是一个列表
            bo_data = resp_json.get("bo", {})
            if not bo_data:
                logger.warning("No block content returned from API.")
                return None, None

            # 取第一个匹配的 block（通常只有一个）
            blocks_list = bo_data.get("blocks", [])
            if not blocks_list:
                logger.warning("No blocks found in response.")
                return None, None

            # 取第一个匹配的 block
            block_data = blocks_list[0]
            content = block_data.get("content", "")
            title = block_data.get("blockName", "")

            return content, title

        except Exception as e:
            logger.error(f"Parse response failed: {e}, response: {response.text}")
            return None, None

# 测试get_page_block_content方法
def test_get_page_block_content():
    # 需要配置有效的user_id和user_token才能测试
    # 这里使用占位符，实际使用时需要替换为真实值
    user_id = "10171727"  # 替换为真实的用户ID
    user_token = "8bdb08ca6cb31034bc7ddf6f2c426965"  # 替换为真实的用户令牌
    
    # 创建Icenter2API实例
    api = Icenter2API(user_id, "", user_token)
    
    # token = api.get_token()
    # print(token)

    # 测试URL
    test_url = "https://i.zte.com.cn/index/ispace/#/space/bbb6e1d7fd774053b4c5a1b2fc8cb5e8/wiki/page/f2e671ab74fa11f0afa32bcf221343e4/view"
    
    print("开始测试get_page_block_content方法...")
    print(f"测试URL: {test_url}")
    
    print("\n测试: 尝试获取特定block内容（使用示例block_id）")
    block_id = ""
    block_title = "标题1名称"
    block_tag = ""

    content, title = api.get_page_block_content(test_url, block_id, block_title, block_tag, content_type="HTML")
    if content:
        print(f"获取成功！标题: {title}")
        print(f"内容长度: {len(content)} 字符")
    else:
        print("获取特定block失败！可能是因为提供的block_id不存在或无效")
    

if __name__ == "__main__":
    test_get_page_block_content()
