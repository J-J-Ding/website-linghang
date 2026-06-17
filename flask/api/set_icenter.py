import os
from threading import Thread
import logging
import requests
import json
import time
import hashlib
import socket
import base64
import datetime as dt
logger = logging.getLogger("Logger")

username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

class icenter_measure(object):
    def __init__(self, *args, **kwargs):
        # self.user = '10213378' # user
        # self.password = 'DingTao582194' # password
        self.user = username
        self.password = password
        spaceId = kwargs.get('spaceId')
        if spaceId == None:
            self.ICENTER_api = ICENTER_API(self.user, self.password)
        else:
            self.ICENTER_api = ICENTER_API(self.user, self.password, spaceId=spaceId)
        self.fetch_project_flag = args

    # 获取页面内容信息
    def get_icenter_content(self,pageID):
        responseJson = self.ICENTER_api.icenter_content_get(pageID)
        return responseJson

    # 获取修改记录
    def get_icenter_operateLog(self,pageID):
        try:
            responseJson = self.ICENTER_api.icenter_contents_icenter_operateLog(pageID)
            operateLog = responseJson.json()
            return operateLog
        except Exception as e:
            print (u'Json获取操作记录失败->', pageID, str(e))
    # 获取访问记录
    def get_icenter_macro(self,pageID):
        try:
            responseJson = self.ICENTER_api.icenter_contents_icenter_macro(pageID)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageID, str(e))
    # 获取贡献者报告
    def get_icenter_macro_gongxian(self,pageID):
        try:
            responseJson = self.ICENTER_api.icenter_contents_icenter_macro_gongxian(pageID)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageID, str(e))
    # 获取页面标签信息
    def get_icenter_macro_tags(self, pageID):
        try:
            responseJson = self.ICENTER_api.icenter_content_tags_get(pageID)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageID, str(e))
    # 获取所有子节点信息
    def get_icenter_all_childs(self, pageID, tages=None):
        childs_list = list()
        try:
            self.ICENTER_api.icenter_childs_get(0, pageID, childs_list)
        except Exception as e:
            print (u'获取子节点失败->', pageID, str(e))
        return childs_list
    # 获取节点的当前子节点 20230830 dingtao
    def get_icenter_cur_childs(self, pageID):
        childs_list = list()
        try:
            self.ICENTER_api.icenter_cur_node_childs(pageID, childs_list)
        except Exception as e:
            print(u'获取当前子节点失败->', pageID, str(e))
        return childs_list
    # 解析页面表格信息 20221109 dingtao
    def get_icenter_table_info(self, pageID, table_index=1):
        try:
            responseJson = self.ICENTER_api.icenter_table_get(pageID, table_index)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageID, str(e))
    # 页面增加标签 20221116 dingtao
    def add_icenter_tag(self, pageId, tag_name):
        try:
            responseJson = self.ICENTER_api.icenter_tag_add(pageId, tag_name)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageId, str(e))
    # 创建新的页面 20221124 dingtao
    def create_icenter(self, contentBody, title, summary, parentId='e90d31e9ed40444ebee9453aa8706537'):
        try:
            responseJson = self.ICENTER_api.icenter_content_create(contentBody, title, summary, parentId)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', str(e))
     # 页面删除标签 20230710 dingtao
    def del_icenter_tag(self, pageID, tagRelationId):
        try:
            responseJson = self.ICENTER_api.icenter_tag_del(pageID, tagRelationId)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', pageID, str(e))
    # 更新页面内容 20230129 dingtao
    def update_icenter_content(self, contentid, BodyupdateHandler = None, TitleupdateHandler = None, content_body = None):
        try:
            responseJson, edit_flag = self.ICENTER_api.icenter_content_put(contentid, BodyupdateHandler, TitleupdateHandler, content_body = content_body)
            response = responseJson.json()
            return response, edit_flag
        except Exception as e:
            print (u'Json获取访问记录失败->', contentid, str(e))
    # 页面转发至消息 20230911 dingtao
    def send_msg_to_moa(self, spaceId, contentId, page_url, employees, groups):
        try:
            responseJson = self.ICENTER_api.icenter_send_msg_to_moa(spaceId, contentId, page_url, employees, groups)
            response = responseJson.json()
            return response
        except Exception as e:
            print (u'Json获取访问记录失败->', contentId, str(e))

    # 解析HTML
    def parse_html_str(self, html_str):
        ret_list = list()
        title_dict = dict()
        html_str = html_str.split('<tbody>')[1]
        tr_info_list = html_str.split('</tr>')
        for tr_index, tr_info in enumerate(tr_info_list):
            if tr_index == 0:
                th_info_list = tr_info.split('</th>')[:-1]
                for th_index, th_info in enumerate(th_info_list):
                    title = th_info.split('>')[-1]
                    title_dict.update({th_index: title})
            else:
                td_info_list = tr_info.split('</td>')[:-1]
                tmp_dict = dict()
                for td_index, th_info in enumerate(td_info_list):
                    td_value = th_info.split('</a>')[0].split('>')[-1]
                    tmp_dict.update({title_dict.get(td_index): td_value})
                ret_list.append(tmp_dict)
        return ret_list

    def start_tree(self):
        start = time.time()
        print(u'主程序运行开始--', dt.datetime.now())
        for k,v in requirementPageIDMap.items():
            # if k not in self.fetch_project_flag:continue
            LIST = self.ICENTER_api.thread_childs_get(0,v, [])
            print(u'长度-->', len(LIST))
        end = time.time()
        print(u"主程序运行结束,总共耗时: %.02f 分钟" %((end-start)/60))
        return ""

proxies = {"http": "", "https": ""}

requirementPageIDMap = {
    # 场景节点：10 场景树
    'm1':'74f66d0db5db44c29f3eb0ec1c53d852',
    # 需求节点：20 需求树
    'm2':'f5d5a603a1a74b3b87add70db7d3b670',
    # 特性节点：30-02 领域特性
    'm3':'df8b5d39f5e248e2af2d8c9ce90b180d',
    # 组件节点：40 组件树
    'm4':'ab4aa12a760b4f01bb5cebf11e9e1c6e',
    # 功能节点：30-01 产品特性
    'm5':'94e5e649d8eb44e8b748c1dfd2ec1bee'
}

class ICENTER_API():

    def __init__(self, username, password, host='https://icenterapi.zte.com.cn/zte-rd-icenter-contents/', bodysample='',
                 spaceId='c58964e8abbc45dbbe30d39d0308c7e9'):
        self.host = host
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
        self.X_Emp_No = username  # 人事账号
        self.passowrd = password  # 密码
        self.X_Auth_Value = ''
        self.last_update_time = None
        self.loginsyscode = 'Portal'
        self.originsyscode = ''
        self.token_status = 0
        self.size = 0
        self.body_sample = bodysample
        self.spaceId = spaceId  # 波分需求
        self._get_token(self.passowrd)

    def get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.81.8.8', 80))
            ip = s.getsockname()[0]
        except Exception as ee:
            print("ee =", ee)
        finally:
            s.close()
        return ip

    def save_token(self, value):
        token_data = {'value': value, 'create_time': time.time()}
        token_file_path = os.path.join(os.path.dirname(__file__), 'uac_token.json')
        with open(token_file_path, 'wt') as wt:
            json.dump(token_data, wt)

    def read_token(self, ):
        cur_time = time.time()
        file_path = os.path.join(os.path.dirname(__file__), 'uac_token.json')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as ft:
                token_info = json.load(ft)
                create_time = token_info.get('create_time')
                if int((cur_time - create_time)) <= 28500:  # 7小时55分
                    return token_info.get('value')

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

    def get_icenter_token(self):
        url = "http://uac.zte.com.cn/uaccommauth/auth/comm/verify.serv"
        clientip = self.get_host_ip()
        text = \
            {
                "account": self.X_Emp_No,
                "passWord": self.passowrd,
                "loginClientIp": clientip,
                "loginSystemCode": self.loginsyscode,
                "originSystemCode": self.originsyscode,
                "other": {
                    "networkArea": '1',
                    "networkAccessType": '1'
                },
                "verifyCode": hashlib.md5(
                    str(self.X_Emp_No + self.passowrd + clientip + self.loginsyscode + self.originsyscode).encode(
                        encoding='utf-8')).hexdigest()
            }
        headers = {'Content-type': 'application/json'}
        content = requests.post(url, data=json.dumps(text), headers=headers)
        return content


    def _get_token(self, passwd=''):
        if self.last_update_time == None:
            pass
        elif self.last_update_time != None and (time.time() - self.last_update_time) > 129500:
            print("暂停3分钟，进行更新token")
            print('ICENTER_API', self.last_update_time)
            print('time.time()', time.time())
            time.sleep(2)
        else:
            return
        content = self.get_icenter_token()
        self.X_Auth_Value = content.json()['other']['token']
        self.last_update_time = time.mktime(time.strptime(content.json()['other']['startVaildTime'], "%Y-%m-%d %H:%M:%S"))
        return content.json()


    def icenter_content_get(self, contentid):
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s?spaceId=%s&tags=1" % (
        contentid, self.spaceId)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json',
                   'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value, 'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        return content.json()

    # 接口说明地址 https://i.zte.com.cn/#/shared/6838ce4a34644fb698e99215cc97f8c1/wiki/page/a307618b0d6d4a4e86865a5da45954fe/view 76条
    def icenter_table_get(self, pageId, table_index=1):
        url = 'https://icenterapi.zte.com.cn/zte-rd-icenter-advanced/content/get_table?limit=500&offset=0'
        page_url = 'https://i.zte.com.cn/#/space/%s/wiki/page/%s/view' % (self.spaceId, pageId)
        json_data = {
            # 请求消息ID，用于表示与服务器端的一次交互；由请求方自己生成，服务器端在响应消息中回填；可选参数。 */
            "msg_id": "1123",
            # “表格是否存在表头”标记，如果设置为 true，则服务器端采用以下第一种格式（带表头的表格）返回响应结果；
            # 如果设置为 false，则服务器端采用以下第二种格式（不带表头的表格）返回响应结果；默认为 false。
            "table_header": False,
            # 表格所在的页面地址
            "page_url": page_url,
            # 要读取的表格在页面中的序号，默认为 1
            "table_index": table_index
        }
        self._get_token()
        time.sleep(0.3)
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        response_post = requests.post(url, json=json_data, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # 20221116 dingtao 增加标签
    def icenter_tag_add(self, pageId, tag_name):
        url = 'https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/tags' % pageId
        json_data = {
            "name": tag_name,
        }
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        response_post = requests.post(url, json=json_data, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # 20230710 dingtao 删除标签
    def icenter_tag_del(self, pageId, tagRelationId):
        url = 'https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/tags/%s' % (pageId, tagRelationId)
        self._get_token()
        headers = {'Content-type': 'application/json',
                   'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value, 'X-Lang-Id': 'zh_CN'}
        content = requests.delete(url, headers=headers)
        return content

    # 20221019 dingtao 获取页面的标签信息
    def icenter_content_tags_get(self, contentid):
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-extend/content/%s/tags/?t=timestamp&spaceId=%s&environmentType=browser" % (
        contentid, self.spaceId)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json',
                   'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value, 'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        return content

    def thread_content_get(self, contentid, childIds):
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s?spaceId=%s" % (contentid, self.spaceId)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json',
                   'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value, 'X-Lang-Id': 'zh_CN'}
        # content = requests.get(url,auth=auth,headers=headers).json()
        content = requests.get(url, headers=headers).json()
        childIds.append(content)

    def icenter_content_get_history(self, contentid):
        pass

    def icenter_contents_get_tag(self, contentid):
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s/tags?spaceId=%s" % (
        contentid, self.spaceId)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json',
                   'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value, 'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        return content.json()

    def icenter_contents_icenter_operateLog(self, contentid):
        text = \
            {
                "start": 0,
                "count": 1000
            }
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-advanced/operateLog/space/%s/content/%s/?t=timestamp&spaceId=%s&environmentType=browser" % (
        self.spaceId, contentid, self.spaceId)
        # response_post = requests.post(url,json=text,auth=auth, headers=headers,proxies=proxies)
        response_post = requests.post(url, json=text, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    def icenter_contents_icenter_macro(self, ContentId):
        text = {
            "currentContentId": ContentId,
            "currentSpaceId": "c58964e8abbc45dbbe30d39d0308c7e9",
            "macroId": "INLINE163162243383260",
            "mappingObject": "pageViewMacro",
            "spaceId": "c58964e8abbc45dbbe30d39d0308c7e9",
            "macroKey": "com.zte.wiki.macro.PageViewsMacro",
            "html": "<span class='icenter-macro-backend-parsed-inline icenter-macro-wrapper icenter-macro-isomorphic-wrapper'> <span class='macro-container'> <img data-macro-props='{\"macroParameters\":{\"contentTitle\":\"\",\"contentId\":\"\",\"spaceId\":\"\",\"expandable\":true,\"level\":\"current\",\"scope\":\"Current\",\"pagination\":{\"limit\":300,\"offset\":0}},\"macroInfo\":{\"id\":\"0ca9ebaf373711e8b8f70242ac110002\",\"disabled\":null,\"createBy\":null,\"createDate\":null,\"updateBy\":null,\"updateDate\":null,\"createNo\":null,\"updateNo\":null,\"macroKey\":\"com.zte.wiki.macro.PageViewsMacro\",\"version\":\"v1\",\"isLatest\":null,\"title\":\"页面浏览\",\"iconFont\":null,\"categoryCode\":\"00003\",\"invokeType\":\"1\",\"description\":\"以表格的形式，展示页面被浏览情况。\",\"renderMode\":\"INLINE\",\"useCache\":null,\"expireTime\":null,\"mappingObject\":\"pageViewMacro\",\"customize\":false,\"environment\":null,\"onlineHelpLink\":\"https://i.zte.com.cn/#/space/69d0a155f72a41d6bf36740b011f33b7/wiki/page/6aa2d2dd663b45d1b953d4201a8efc09/view\",\"sortNo\":null},\"isUpdate\":false,\"employeeShortId\":\"10090211\",\"spaceId\":\"c58964e8abbc45dbbe30d39d0308c7e9\",\"hasContentBody\":false,\"parentContextNode\":\"\"}' id=\"INLINE163162243383260\" data-macro-key=\"com.zte.wiki.macro.PageViewsMacro\" data-icenter-macro-type=\"original\" class=\"editor-inline-macro icenter-macro icenter-macro-original icenter-macro-find\" /> </span> </span>",
            "contentId": ContentId
        }
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-macro/macroRender/?t=timestamp&spaceId=%s&environmentType=browser&mode=execute" % (
            self.spaceId)
        # response_post = requests.post(url,json=text,auth=auth, headers=headers,proxies=proxies)
        response_post = requests.post(url, json=text, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # 20221019 dingtao 获取页面贡献者报告信息
    def icenter_contents_icenter_macro_gongxian(self, ContentId):
        text = {
            "currentContentId": ContentId,
            "currentSpaceId": "c58964e8abbc45dbbe30d39d0308c7e9",
            "macroId": "INLINE163162243383260",
            "mappingObject": "pageViewMacro",
            "spaceId": "c58964e8abbc45dbbe30d39d0308c7e9",
            "macroKey": "com.zte.wiki.macro.PageViewsMacro",
            # "html":'''<span class='icenter-macro-backend-parsed-inline icenter-macro-wrapper icenter-macro-isomorphic-wrapper'> <span class='macro-container'> <img data-macro-props='{"macroParameters":{"contentTitle":"","contentId":"","columns":["user","edit","tag","comment","like"],"level":"descendants","scope":"后继所有页面","pagination":{"limit":300,"offset":0}},"macroInfo":{"categoryCode":"00006","customize":false,"description":"显示页面贡献者的概要信息，从创建时间起每24小时更新一次数据。","id":"a7f0aa51c99647b58cec38e40a7bd2db","invokeType":"1","macroKey":"com.zte.wiki.macro.ContributorsReportMacro","onlineHelpLink":"https://i.zte.com.cn/#/space/69d0a155f72a41d6bf36740b011f33b7/wiki/page/92c35a79b4674e528667d3b5f32bcf93/view","renderMode":"INLINE","title":"贡献者报告","version":"v1"},"isUpdate":false,"employeeShortId":"00108345","spaceId":"c58964e8abbc45dbbe30d39d0308c7e9","hasContentBody":false,"parentContextNode":""}' id="INLINE166590969984700" data-macro-key="com.zte.wiki.macro.ContributorsReportMacro" data-icenter-macro-type="original" class="editor-inline-macro icenter-macro icenter-macro-original icenter-macro-find" /> </span> </span>''',
            "contentId": ContentId,
            "html": '''<span class='icenter-macro-backend-parsed-inline icenter-macro-wrapper icenter-macro-isomorphic-wrapper'> <span class='macro-container'> <img data-macro-props='{"macroParameters":{"contentTitle":"","contentId":"","columns":["user","edit","tag","comment","like"],"level":"current","scope":"Current","pagination":{"limit":300,"offset":0}},"macroInfo":{"categoryCode":"00006","customize":false,"description":"显示页面贡献者的概要信息，从创建时间起每24小时更新一次数据","id":"a7f0aa51c99647b58cec38e40a7bd2db","invokeType":"1","macroKey":"com.zte.wiki.macro.ContributorsReportMacro","onlineHelpLink":"https://i.zte.com.cn/#/space/69d0a155f72a41d6bf36740b011f33b7/wiki/page/92c35a79b4674e528667d3b5f32bcf93/view","renderMode":"INLINE","title":"贡献者报告","version":"v1"},"isUpdate":false,"employeeShortId":"10331877","spaceId":"c58964e8abbc45dbbe30d39d0308c7e9","hasContentBody":false,"parentContextNode":""}' id="INLINE1666419033220" data-macro-key="com.zte.wiki.macro.ContributorsReportMacro" data-icenter-macro-type="original" class="editor-inline-macro icenter-macro icenter-macro-original icenter-macro-find" /> </span> </span>''',
        }
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/macros/preview/?t=timestamp&spaceId=%s&environmentType=browser&mode=execute" % (
            self.spaceId)
        # response_post = requests.post(url,json=text,auth=auth, headers=headers,proxies=proxies)
        response_post = requests.post(url, json=text, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    def icenter_get_table(self, pageUrl, tableIndex=1, header=False):
        text = \
            {
                "table_header": header,
                "page_url": pageUrl,
                "table_index": tableIndex
            }
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        time.sleep(0.3)
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-advanced/content/get_table?limit=2000&offset=0"
        # response_post = requests.post(url,json=text,auth=auth, headers=headers,proxies=proxies)
        response_post = requests.post(url, json=text, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # 20221124 dingtao 创建文章
    def icenter_content_create(self, contentBody, title, summary, parentId):
        data = {
            "atEmpNos": [],
            "description": "",
            "employees": [],
            "groupKeyList": [],
            "parentId": parentId,
            "spaceId": self.spaceId,
            "title": title,
            "contentBody": contentBody,
            "summary": summary,
            "templateId": ""
        }
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content?spaceId={spaceId}".format(
            spaceId=self.spaceId)
        response_post = requests.post(url, json=data, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # # 页面转发至消息 20230911 dingtao
    def icenter_send_msg_to_moa(self, spaceId, contentId, page_url, employees, groups):
        data = {
            "employees": employees,
            # "groups": groups,
            "spaceId": spaceId,
            "link": {
                "linkPC": page_url,
                "linkMobile": "https://i.zte.com.cn/zte-rd-icenter-ssr/wiki/page/{contentId}/comments/0?fromType=MOA&spaceId={spaceId}".format(
                    contentId=contentId, spaceId=spaceId)
            }
        }
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/{contentId}/msgForward/?spaceId={spaceId}".format(
            contentId=contentId, spaceId=spaceId)
        response_post = requests.post(url, json=data, headers=headers, proxies=proxies)
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post

    # 20221124 dingtao 更新文章
    def icenter_content_put(self, contentid, BodyupdateHandler=None, TitleupdateHandler=None, content_body=None):
        content = self.icenter_content_get(contentid)
        title = content['bo']['title']
        body_value = content['bo']['contentBody']
        edit_flag = False
        if BodyupdateHandler is not None:
            new_body_value, edit_flag = BodyupdateHandler(body_value)
        if content_body != None:
            new_body_value = content_body
        text = \
            {
                "employees": [],
                "groups": [],
                "groupKeyList": [],
                "urlTemplate": "",
                "contentBody": new_body_value,
                "spaceId": self.spaceId,
                "spaceName": content['bo']['spaceName'],
                "title": title,
                "currentVersion": content['bo']['currentVersion'],
                "summary": ""
            }
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/%s?spaceId=%s" % (contentid, self.spaceId)
        response_post = requests.post(url, json=text, headers=headers, proxies=proxies)
        print(f"url:{url}")
        print(f"json:{json.dumps(text, indent=4, ensure_ascii=False)}")
        print(f"headers:{json.dumps(headers, indent=4, ensure_ascii=False)}")
        if response_post.status_code != 200:
            print('api-exception', response_post.status_code)
        return response_post, edit_flag

    def icenter_cur_node_childs(self, contentid, childIds):
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/subtree?contentId=%s&spaceId=%s" \
              % (contentid, self.spaceId)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        for content in content.json()['bo']:
            childIds.append({
                'pageID': content["id"],
                'pageTitle': content["title"],
            })

    def icenter_childs_get(self, page, contentid, childIds):
        tags = 0
        # 20221022 dingtao  下边接口返回信息包括 contentid 信息
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/nodes?contentId=%s&page=%d&size=%d&spaceId=%s&tags=%d" \
              % (contentid, page, self.size, self.spaceId, tags)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        endRow = content.json()['bo']['endRow']
        hasNextPage = content.json()['bo']['hasNextPage']
        isFirstPage = content.json()['bo']['isFirstPage']
        isLastPage = content.json()['bo']['isLastPage']
        for child_dict in content.json()['bo']['list']:
            tmp_dict = {'id': child_dict['id'], 'title': child_dict['title'], 'parentId': child_dict['parentId']}
            childIds.append(tmp_dict)
        if isLastPage == False:
            self.icenter_childs_get(page + 1, contentid, childIds)
        return

    def thread_childs_get(self, page, contentid, childIds):
        tags = 0
        ths = []
        url = "https://icenterapi.zte.com.cn/zte-rd-icenter-contents/content/nodes?contentId=%s&page=%d&size=%d&spaceId=%s&tags=%d" \
              % (contentid, page, self.size, self.spaceId, tags)
        # auth = requests.auth.HTTPDigestAuth(self.X_Emp_No, self.X_Auth_Value)
        self._get_token()
        headers = {'Content-type': 'application/json', 'X-Emp-No': self.X_Emp_No, 'X-Auth-Value': self.X_Auth_Value,
                   'X-Lang-Id': 'zh_CN'}
        # content=requests.get(url,auth=auth,headers=headers)
        content = requests.get(url, headers=headers)
        thr = []
        for content in content.json()['bo']['list']:
            contentid = content['id']
            ts = Thread(target=self.thread_content_get(contentid, childIds), args=(contentid, childIds))
            thr.append(ts)
        for t in thr:
            t.start()
            ths.append(t)
        for t in ths:
            t.join()
        return childIds


if __name__ == '__main__':
    # 必须是已经存在的页面 且spaceid必须为：c58964e8abbc45dbbe30d39d0308c7e9

    contectid = '5c31b8d52c2643bf911900b528b1be35'
    title_name = "修改成功"
    query_set = "12345678987654312"
    contentBody_summary = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{title_name}</title>
                </head>
                <body>
                    <h1>{title_name}</h1>
                    <p>{query_set}</p>
                    <table border="1">
                        <tr>
                            <td>在研版本的需求实例化页面内容无变更，详见链接：aaaaaaaaaaaaaaaaaaaaaaaaaa</td>
                        </tr>
                    </table>
                </body>
                </html>
                """
    new_page_info = icenter_measure(spaceId='c58964e8abbc45dbbe30d39d0308c7e9').update_icenter_content(contectid, None, None, content_body=contentBody_summary)[0]