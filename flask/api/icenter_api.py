#!/usr/bin/python
# -*- coding: UTF-8 -*- 

import requests
import json
import time
import lxml.html
import re
import hashlib
import os
import matplotlib.pyplot as plt
from time import sleep
from requests_toolbelt.multipart.encoder import MultipartEncoder
from pathlib import Path
from matplotlib.font_manager import FontProperties
from jinja2 import Template
from utils import icenter_api_template as at

#公司代理服务器会阻止put和delete方法，需要强制置代理服务器为空
proxies = {
    "http": "",
    "https": ""
}

###########################################################################
def get_header(employno, authval):
    return {'Content-type': 'application/json','X-Emp-No':employno,'X-Auth-Value':authval, 'X-Lang-Id':'zh_CN'} 

###--------------------------------------------------------------------------------------
def requests_post(url, text, headers):
    return requests.post(url, data = json.dumps(text), headers = headers, proxies = proxies)
###--------------------------------------------------------------------------------------
def requests_put(url, text, headers):
    return requests.put(url, data = json.dumps(text), headers = headers, proxies = proxies)

###--------------------------------------------------------------------------------------
def requests_get(url, auth, headers):
    return requests.get(url, auth = auth, headers = headers, proxies = proxies)

###--------------------------------------------------------------------------------------
def requests_auth_get(employno, authval, url):
    auth = requests.auth.HTTPDigestAuth(employno, authval)
    headers = get_header(employno, authval)
    content = requests_get(url, auth, headers)
    while content.status_code != 200:
        sleep(3)
        content = requests_get(url, auth, headers)
    return content.json()

###--------------------------------------------------------------------------------------
def requests_auth_post(employno, authval, url, post):
    auth = requests.auth.HTTPDigestAuth(employno, authval)
    headers = get_header(employno, authval)
    content = requests_post(url, post, headers)
    while content.status_code != 200:
        sleep(3)
        content = requests_post(url, post, headers)
    return content.json()

###--------------------------------------------------------------------------------------
def requests_auth_put(employno, authval, url, post):
    auth = requests.auth.HTTPDigestAuth(employno, authval)
    headers = get_header(employno, authval)
    content = requests_put(url, post, headers)
    while content.status_code != 200:
        sleep(3)
        content = requests_put(url, post, headers)
    return content.json()

###--------------------------------------------------------------------------------------
def get_groups(employno, authval, spaceid):
    url = at.icapi_get_user_group(spaceid, employno)
    # print('get_groups:' + url)
    return requests_auth_get(employno, authval, url)

###--------------------------------------------------------------------------------------
def get_page_content(employno, authval, spaceid, pageid):
    url = at.icapi_get_page_content(spaceid, pageid)
    # print('get_page_content:' + url)
    return requests_auth_get(employno, authval, url)
    
###--------------------------------------------------------------------------------------
def get_space_nodes(employno, authval, spaceid):
    url = at.icapi_get_space_tree(spaceid)
    # print('get_space_nodes:' + url)
    return requests_auth_get(employno, authval, url)
    
###--------------------------------------------------------------------------------------
def get_page_tree(employno, authval, spaceid, pageid):
    url = at.icapi_get_page_tree(spaceid, pageid)
    # print('get_page_tree:' + url)
    return requests_auth_get(employno, authval, url)

###--------------------------------------------------------------------------------------
def get_page_tree_1children(employno, authval, spaceid, pageid):
    url = at.icapi_get_page_tree_1children(spaceid, pageid)
    # print('get_page_tree_1children:' + url)
    return requests_auth_get(employno, authval, url)  

###--------------------------------------------------------------------------------------
def get_space_templates(employno, authval, spaceid):
    url = at.icapi_get_space_template(spaceid)
    print('get_space_templates:' + url)
    return requests_auth_get(employno, authval, url)
    
###--------------------------------------------------------------------------------------
def get_template_content(employno, authval, spaceid, templateId):
    url = at.icapi_get_template_content(spaceid, templateId)
    print('get_template_content:' + url)
    return requests_auth_get(employno, authval, url)
    
###--------------------------------------------------------------------------------------
def get_page_history(employno, authval, spaceid, pageid):
    url = at.icapi_get_page_history(spaceid, pageid)
    # print('get_page_history:' + url)
    return requests_auth_get(employno, authval, url)
    
###--------------------------------------------------------------------------------------
def get_page_table(employno, authval, spaceid, pageid, tableheader=False, tableindex=1):
    url = at.icapi_get_page_table()
    page_url = 'https://i.zte.com.cn/#/space/%s/wiki/page/%s/view' %(spaceid, pageid)
    # print('get_page_table:' + page_url)
    jsondata = {
        # 请求消息ID，用于表示与服务器端的一次交互；由请求方自己生成，服务器端在响应消息中回填；可选参数。 */
        "msg_id": "1123",  
        # “表格是否存在表头”标记，如果设置为 true，则服务器端采用以下第一种格式（带表头的表格）返回响应结果；
        # 如果设置为 false，则服务器端采用以下第二种格式（不带表头的表格）返回响应结果；默认为 false。
        "table_header": tableheader, 
        # 表格所在的页面地址 
        "page_url": page_url, 
        # 要读取的表格在页面中的序号，默认为 1 
        "table_index": tableindex  
    }
    return requests_auth_post(employno, authval, url, jsondata)

###--------------------------------------------------------------------------------------
def new_page_content(employno, authval, spaceid, parentId, title, body, summary, templateId = '', employee = '10088659'):
    url = at.icapi_new_page_content(spaceid, parentId)
    jsondata = {
        "atEmpNos": [],
        "description": "",
        "employees": [],
        "groupKeyList": [],
        "parentId": parentId,
        "spaceId": spaceid,
        "title": title,
        "contentBody": body,
        "summary": summary,
        # "templateId":templateId
    }
    if templateId:
        jsondata["templateId"] = templateId
    return requests_auth_post(employno, authval, url, jsondata)

###--------------------------------------------------------------------------------------
def update_page_content(employno, authval, spaceid, pageid, title, body, summary, verNo = ''):
    url = at.icapi_update_page_content(spaceid, pageid)
    if verNo == '':
        verNo = time.strftime('%Y%m%d%H:%M:%S',time.localtime(time.time()))
    jsondata = {
        "employees": [],
        "groups": [],
        "groupKeyList": [],
        "urlTemplate": "",
        "contentBody": body,
        "spaceId": spaceid,
        "spaceName": "",
        "title": title,
        "currentVersion": verNo,
        "summary": summary
    }
    return requests_auth_put(employno, authval, url, jsondata)


def get_page_power(employno, authval, page_url):
    page_url_search = re.search("(space|shared|wiki)/([0-9a-z]+)/wiki/page/([0-9a-z]+)", page_url)
    if not page_url_search:
        return False, "page_url不合法, 获取space和page失败"
    spaceid, businessId = page_url_search.group(2), page_url_search.group(3)
    url = at.icapi_page_power(spaceid, businessId)
    data = requests_auth_get(employno, authval, url)
    code = data.get("code", {}).get("code", "")
    if code == "0002":
        return False, "token失效, 请重新登录系统获取新token"
    if code != "0000":
        return False, data.get("code", {}).get("msg", "")
    return True, data.get("bo", {})


def pie_generate(data_dict, image_save_path):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
    plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

    sizes = data_dict.get("sizes", [])
    labels = data_dict.get("labels", [])
    colors = data_dict.get("colors", [])
    explode = data_dict.get("explode", ())
    title = data_dict.get("title", "")

    # 创建饼图
    fig, ax = plt.subplots()
    patches, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                                       shadow=False, startangle=180, labeldistance=5)

    # 绘制一个圆圈，使其看起来像一个饼图
    plt.axis('equal')

    # 添加图例
    plt.legend(patches, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3)

    # 添加标题
    plt.title(title)

    # 保存图片
    plt.savefig(image_save_path)
    plt.close(fig)  # 关闭图形，避免重复显示
    return image_save_path


def image_upload(employno, authval, image_path):
    url = at.icapi_image_upload()
    # url = f"https://icenterapi.zte.com.cn/zte-km-icenter-filetransfer/file/uploadImage?action=uploadimage&encode=utf-8"
    image_path = Path(image_path)
    image_data = MultipartEncoder(
        fields = {
            'upfile': (image_path.name, open(image_path, "rb"))
        }
    )
    headers = {'Content-type': f'{image_data.content_type}', 'X-Emp-No': employno, 'X-Auth-Value': authval, 'X-Lang-Id':'zh_CN'} 
    content = requests.post(url, data = image_data, headers = headers, proxies = proxies)
    data = content.json()
    code = data.get("code", {}).get("code", "")
    if code == "0002":
        return False, "token失效, 请重新登录系统获取新token"
    if code != "0000":
        return False, data.get("code", {}).get("msg", "")
    image_size = data.get('bo', [{}])[0].get("fileSize", 0)
    image_path = data.get('bo', [{}])[0].get("path", "")
    image_url = f"{at.iCenterapi_url}/{image_path}"
    return True, {
        "image_data_size": image_size,
        "image_path": image_path,
        "image_url": image_url,
        "image_html": f'<img data-img-size="{image_size}" src="{image_url}">'
    }

def attachment_upload(employno, authval, spaceid, file_path):
    udm_config_url = f"{at.iCenterapi_url}/zte-rd-icenter-advanced/udm/config?t=timestamp&spaceId={spaceid}&environmentType=browser"
    udm_config_data = requests_auth_get(employno, authval, udm_config_url)
    if udm_config_data.get("code", {}).get("code", "") != "0000":
        return False, udm_config_data.get("code", {}).get("msg", "")
    udm_config_data_bo = udm_config_data.get("bo", {})
    verify_code = udm_config_data_bo.get("verifyCode", "")
    access_key = udm_config_data_bo.get("accessKey", "")
    timestamp = udm_config_data_bo.get("timestamp", "")
    headers = {
        'X-Emp-No': employno, 
        'X-Auth-Value': authval, 
        'x-access-key': access_key, 
        'x-origin-servicename':'WIKI',
        'x-timestamp': timestamp,
        'x-verify-code': verify_code,
    }
    get_lib_info_url = f"{at.idriveapi_url}/zte-km-cloududm-core/docLib/getLibInfo?spaceId={spaceid}&empNo={employno}"
    get_lib_info_response = requests.get(get_lib_info_url, headers = headers, proxies = proxies)
    get_lib_info_data = get_lib_info_response.json()
    if get_lib_info_data.get("code", {}).get("code", "") != "0000":
        return False, get_lib_info_data.get("code", {}).get("msg", "")
    library_id = get_lib_info_data.get("bo", {}).get("libraryId", "")
    
    create_app_folder_url = f"{at.idriveapi_url}/zte-km-cloududm-core/docLib/createAppFolder"
    create_app_folder_response = requests.post(create_app_folder_url, data= {
        "libraryId": library_id
    }, headers = headers, proxies = proxies)
    create_app_folder_data = create_app_folder_response.json()
    if create_app_folder_data.get("code", {}).get("code", "") != "0000":
        return False, create_app_folder_data.get("code", {}).get("msg", "")
    folder_id = create_app_folder_data.get("bo", {}).get("folderId", "")

    hash_md5 = hashlib.md5()
    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    file_md5 = hash_md5.hexdigest()
    file_status_url = f"{at.idriveapi_url}/zte-km-cloududm-core/docUpload/fileStatus"
    file_status_response = requests.post(file_status_url, data= {
        "fileName": file_path.name,
        "fileMd5": file_md5,
        "libraryId": library_id,
        "folderId": folder_id,
        "fileSize": file_size,
        "md5DirectTransfer": True
    }, headers = headers, proxies = proxies)
    file_status_data = file_status_response.json()
    if file_status_data.get("code", {}).get("code", "") != "0000":
        return False, file_status_data.get("code", {}).get("msg", "")
    recommand_chunk_size = file_status_data.get("bo", {}).get("recommandChunkSize", "")
    md5_direct_transfer_enable = file_status_data.get("bo", {}).get("md5DirectTransferEnable", "")
    if not md5_direct_transfer_enable:
        file_data = MultipartEncoder(
            fields = {
                "fileMd5": file_md5,
                'file': (file_path.name, open(file_path, "rb"))
            }
        )
        send_data_headers = headers.copy()
        send_data_headers["Content-type"] = file_data.content_type
        send_data_response = requests.post(f"{at.idriveapi_url}/zte-km-cloududm-core/docUpload/sendData", data = file_data, headers = send_data_headers, proxies = proxies)
        send_data = send_data_response.json()
        if send_data.get("code", {}).get("code", "") != "0000":
            return False, send_data.get("code", {}).get("msg", "")
    save_files_url = f"{at.idriveapi_url}/zte-km-cloududm-core/docUpload/saveFiles"
    save_files_response = requests.post(save_files_url, data= {
        "libraryId": library_id,
        "folderId": folder_id,
        "searchRange": 1,
        "fileInfos": '[{"fileId":"WU_FILE_0","fileMd5":"%s","fileName":"%s","fileSize": %s}]' % (file_md5, file_path.name, file_size)

    }, headers = headers, proxies = proxies)
    save_files_data = save_files_response.json()
    if save_files_data.get("code", {}).get("code", "") != "0000":
        return False, save_files_data.get("code", {}).get("msg", "")
    group_key = save_files_data.get("bo", {}).get("groupKey", "")
    file_id = save_files_data.get("bo", {}).get("files", [{}])[0].get("id", "")
    file_ext_name = save_files_data.get("bo", {}).get("files", [{}])[0].get("fileExtName", "")
    if "xls" in file_ext_name:
        icon_type = "xls"
    elif "doc" in file_ext_name:
        icon_type = "doc"
    else:
        icon_type = file_ext_name
    return True, f'<img src="/zte-km-icenter-webeditor/static/publish/static/ueditor1_4_3_3/dialogs/attachment/fileTypeImages/icon_{icon_type}.svg" style="vertical-align:bottom;margin-right:2px;width:20px;height:20px;">\
    <a style="font-size:14px; color:#0066cc;" attachmentsource="udm-doc" filesize="{file_size}" groupkey="{group_key}" ext="{file_ext_name}" href="udm-doc-{file_id}" title="{file_path.name}" _href="udm-doc-{file_id}">{file_path.name}</a>'


def page_table_additional_data(table_index, table_data, content_body):
    tree = lxml.html.fromstring(content_body)
    table_tree_list = tree.xpath(f'//table[not(@data-macro-props)]')
    if len(table_tree_list) < table_index:
        return content_body
    data_list = table_data.get("data_list", [])
    data_len = len(data_list)
    table_tree = tree.xpath(f'//table[not(@data-macro-props)]')[table_index]
    for serial, row_data in enumerate(data_list, 1):
        last_tr = table_tree.xpath(f'.//tr[last()]')
        if not last_tr:
            break
        last_tr = last_tr[0]
        for row_index, tr_element in enumerate(last_tr.xpath(".//*[text()]")):
            tr_element.text = "" if row_index >= len(row_data) else str(row_data[row_index])
        if serial == data_len:
            continue
        last_tr_html = lxml.html.tostring(last_tr, pretty_print=False, encoding='unicode')
        new_tr = lxml.html.fromstring(last_tr_html)
        last_tr.addnext(new_tr)
    table_merge_cells(table_tree, table_data, is_additional=True)    
    content_body = lxml.html.tostring(tree, pretty_print=False, encoding='unicode')
    return content_body


def table_html_generate(table_data):
    data_list = table_data.get("data_list", [])
    template_str = """
    <table data-sort="sortEnabled" class="sortEnabled setSortAttribute" style="position: relative;">
        <tbody>
            <tr class="firstRow">
                {% for item in data[0] %}
                <th class="" data-sort-type="reversebyasc"><em>{{ item }}</em></th>
                {% endfor %}
            </tr>
            {% for row in data[1:] %}
            <tr class="firstRow">
                {% for cell in row %}
                    {% if cell == '×' %}
                        <td style="background-color: rgb(255, 73, 73);"><em>{{ cell }}</em></td>
                    {% elif cell == '√' %}
                        <td style="background-color: rgb(19, 206, 102);"><em>{{ cell }}</em></td>
                    {% else %}
                        <td class=""><em>{{ cell }}</em></td>
                    {% endif %}
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    """
    template = Template(template_str)
    table_html = template.render(data=data_list)
    table_html = table_html.replace("\n", "").replace("    ", "")
    table_tree = lxml.html.fromstring(table_html)
    table_merge_cells(table_tree, table_data)  
    table_html = lxml.html.tostring(table_tree, pretty_print=True, encoding='unicode')
    return table_html


def table_merge_cells(table_tree, table_data, is_additional=False):
    data_len = len(table_data.get("data_list", []))
    clear_element_list = []
    tr_tree = table_tree.xpath(f'.//tr')
    # 合并列单元格
    if table_data.get("merge_col_cell"):
        for tr_index, tr_element in enumerate(tr_tree, 1):
            for td_index, td_element in enumerate(tr_element.xpath('td'), 1):
                rowspan = 1
                if is_additional:
                    back_td_xpath = table_tree.xpath(f'.//tr[position() > {tr_index}]/td[{td_index}]')
                else:
                    back_td_xpath = table_tree.xpath(f'.//tr[position() > last() - {data_len - tr_index}]/td[{td_index}]')
                for back_td_element in back_td_xpath:
                    if not td_element.text_content().strip() or td_element.text_content().strip() != back_td_element.text_content().strip():
                        break
                    rowspan += 1
                    td_element.set('rowspan', str(rowspan)) 
                    clear_element_list.append(back_td_element)  
    # 合并行单元格
    if table_data.get("merge_row_cell"):
        for tr_index, tr_element in enumerate(tr_tree, 1):
            for td_index, td_element in enumerate(tr_element.xpath('td'), 1):
                colspan = 1
                if is_additional:
                    back_td_xpath = table_tree.xpath(f'.//tr[position() = {tr_index}]/td[position() > {td_index}]')
                else:
                    back_td_xpath = table_tree.xpath(f'.//tr[position() = last() - {data_len - tr_index}]/td[position() > {td_index}]')
                for back_td_element in back_td_xpath:
                    if not td_element.text_content().strip() or td_element.text_content().strip() != back_td_element.text_content().strip():
                        break
                    colspan += 1
                    td_element.set('colspan', str(colspan)) 
                    clear_element_list.append(back_td_element)   
    # 清除无用单元格
    for clear_element in clear_element_list:
        clear_element_parent = clear_element.getparent()
        if clear_element_parent:
            clear_element_parent.remove(clear_element)


def template_html_replace(variable_replace, template_html):
    for variable, val in variable_replace.items():
        if isinstance(val, dict):
            table_html = table_html_generate(val)
            template_html = template_html.replace(f"###{variable}###", table_html)
        elif isinstance(val, list):
            logo_match = re.search(f"(<p>###start{variable}###</p>(.*?)<p>###{variable}end###</p>)", template_html)
            if not logo_match:
                continue
            replace_source = logo_match.group(1)
            subtemplate = logo_match.group(2)
            replace_html = ""
            for loop_dict in val:
                add_html = subtemplate
                add_html = template_html_replace(loop_dict, add_html)
                replace_html += add_html
            template_html = template_html.replace(replace_source, replace_html)
        else:
            template_html = template_html.replace(f"###{variable}###", str(val))
    return template_html


def by_template_generate_page_content(employno, authval, template_url, data_dict, new_page={}):
    template_search = re.search("(space|shared|wiki)/([0-9a-z]+)/wiki/page/([0-9a-z]+)", template_url)
    if not template_search:
        return False, "template_url不合法, 获取space和page失败"
    template_space_id, template_page_id = template_search.group(2), template_search.group(3)
    template_data = get_page_content(employno, authval, template_space_id, template_page_id)
    if template_data.get("code", {}).get("code", "") != "0000":
        return False, template_data.get("code", {}).get("msg", "")
    template_content_body = template_data.get("bo", {}).get("contentBody", "")
    template_title = template_data.get("bo", {}).get("title", "")
    template_current_version = template_data.get("bo", {}).get("currentVersion", "")

    for table_index, table_data in data_dict.get("table_additional", {}).items():
        template_content_body = page_table_additional_data(table_index, table_data, template_content_body)
    template_content_body = template_html_replace(data_dict.get("variable_replace", {}), template_content_body)
    
    if new_page:
        new_page_parent_url = new_page.get("new_page_parent_url", "")
        parent_url_search = re.search("(space|shared|wiki)/([0-9a-z]+)/wiki/page/([0-9a-z]+)", new_page_parent_url)
        if not parent_url_search:
            return False, "new_page_parent_url不合法, 获取space和page失败"
        parent_space_id, parent_page_id = parent_url_search.group(2), parent_url_search.group(3)
        new_page_title = new_page.get("new_page_title", "")
        if not new_page_title:
            new_page_title = template_title
        page_content_data = new_page_content(employno, authval, parent_space_id, parent_page_id, new_page_title, template_content_body, "")
    else:
        page_content_data = update_page_content(employno, authval, template_space_id, template_page_id, template_title, template_content_body, "", verNo = template_current_version)
    if page_content_data.get("code", {}).get("code", "") != "0000":
        return False, page_content_data.get("code", {}).get("msg", "")
    return True, page_content_data.get("bo", {})


if __name__ == "__main__":
    # 附件上传
    # flag, file_html = attachment_upload("6407002385", "fd2c2cb90bf4441329c944978cb9e57c", "ff77f6673281495b9b262761a35aca09", r"C:\Users\6407002385.WIN-1H7SSV6G87F\Desktop\www.xlsx")
    # print(file_html)

    # 判断界面权限
    # flag, power_dict = get_page_power("10002438", "f6a3a917f17670f368b7776617347c9c", "https://i.zte.com.cn/index/ispace/#/space/181d9eb900124b85b5c18134ff8228f6/wiki/page/98276af393a04e6cb724f2690832a837/view")
    # print(power_dict)
    # print(power_dict.get("spaceAllView"))  # 判断是否有查看权限
    # print(power_dict.get("spacePageAdd"))  # 判断是否有增加界面权限
    # print(power_dict.get("singlePageEdit"))  # 判断是否有修改界面权限

    # 生成Pie图
    # data_dict = {
    #     # "sizes": [60, 10, 0],
    #     # "labels": ['完全覆盖', '部分覆盖', '未覆盖'],
    #     # "colors": ['#4f81bd', '#9bbb59', '#c0504d'],
    #     # "explode": (0.01, 0.01, 0.01),
    #     # "title": "配置项覆盖情况",
    #     'sizes': [18, 2, 4], 'labels': ['完全覆盖', '部分覆盖', '未覆盖'], 'colors': ['#4f81bd', '#9bbb59', '#c0504d'], 'explode': (0.01, 0.01, 0.01), 'title': '配置项覆盖情况'
    # }
    # pie_generate(data_dict, r"D:\test\pie_chart1.jpeg")

    # 文件上传
    # flag, image_dict = image_upload("6407002385", "2167371c8dbd89f1faef86d16ee2ec23", r'D:\test\pie_chart1.jpeg')
    # print(image_dict.get("image_html"))

    # 模板替换
    template_url = "https://i.zte.com.cn/index/ispace/#/space/ff77f6673281495b9b262761a35aca09/wiki/page/1bfe844f262f4d5dabfef2901e9b55d4/view"
    new_page_parent_url = "https://i.zte.com.cn/index/ispace/#/space/0b4104b150cf498fb7382fdb57509a4f/wiki/page/041467a7525111f0a4de15692bc383dc/view"
    flag, page_content_data = by_template_generate_page_content("6407002385", "f476d8fb8df2b526f6bbf013cfe3642f", template_url, {}, {"new_page_parent_url": new_page_parent_url, "new_page_title": "运营商工程场景与实验室环境数据对比测试23"})
    # if not flag:
    #     return 
    new_page_parent_search = re.search("(space|shared|wiki)/([0-9a-z]+)/wiki/page/([0-9a-z]+)", new_page_parent_url)
    # if not new_page_parent_search:
        # return False, "new_page_parent_url不合法, 获取space和page失败"
    new_space_id = new_page_parent_search.group(2)
    new_page_id = page_content_data.get('id', "")
    new_page_url = f"https://i.zte.com.cn/index/ispace/#/space/{new_space_id}/wiki/page/{new_page_id}/view"
    flag, page_content_data = by_template_generate_page_content("6407002385", "f476d8fb8df2b526f6bbf013cfe3642f", new_page_url, {"variable_replace": {"配置项总数": 100}})
    print(flag, page_content_data)

    # template_url = "https://i.zte.com.cn/index/ispace/#/space/ff77f6673281495b9b262761a35aca09/wiki/page/aea5dbaaf48b43bfbb6346db82080601/view"
    # page_content_data = by_template_generate_page_content("6407002385", "fd2c2cb90bf4441329c944978cb9e57c", template_url, {
    #     # "table_additional": {3: {"data_list": [[1, 2, 3], [1, 5, 5], [1, 9, 8], [2, 8, 9], [1, 8, 9]], "merge_row_cell": True, "merge_col_cell": True}},
    #     "variable_replace": {
    #         "配置项总数": 100,
    #         # "饼图替换": image_dict.get("image_html"),
    #         # "附加替换": file_html,
    #         "表格插入": {
    #             "data_list": [['完全覆盖', '部分覆盖', '未覆盖'], [1, 2, 3], [1, 5, 5], [1, 9, 8], [2, 8, 9], [1, 8, 9]],
    #             "merge_row_cell": True,
    #             "merge_col_cell": True
    #         },
    #         "网络信息分析": [
    #             {"网络信息分析标题": "2.1.2 全网网元分类", "网络信息分析表格": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "×", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }, "全网网元": [{"网元名称": "NEA"}, {"网元名称": "NEB"}],
    #             "对比规则": "对比规则:123"},
    #             {"网络信息分析标题": "2.1.3 全网网元分类1", "网络信息分析表格": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "√", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }, "全网网元": [], "对比规则": "对比规则:456"},
    #         ],
    #         "折叠网络信息分析": [
    #             {"折叠标题": "2.1.2 全网网元分类", "折叠表格插入": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "×", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }},
    #             {"折叠标题": "2.1.3 全网网元分类1", "折叠表格插入": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "√", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }}
    #         ]
    #     }
    # }, {"new_page_parent_url": "https://i.zte.com.cn/index/ispace/#/space/ff77f6673281495b9b262761a35aca09/wiki/page/3a888cb03826421a8773d8c676460693/view", "new_page_title": "运营商工程场景与实验室环境数据对比测试6"}
    # )
    # print(page_content_data)


    # template_url = "https://i.zte.com.cn/index/ispace/#/space/ff77f6673281495b9b262761a35aca09/wiki/page/aea5dbaaf48b43bfbb6346db82080601/view"
    # page_content_data = by_template_generate_page_content("6407002385", "fd2c2cb90bf4441329c944978cb9e57c", template_url, {
    #     # "table_additional": {3: {"data_list": [[1, 2, 3], [1, 5, 5], [1, 9, 8], [2, 8, 9], [1, 8, 9]], "merge_row_cell": True, "merge_col_cell": True}},
    #     "variable_replace": {
    #         "配置项总数": 100,
    #         # "饼图替换": image_dict.get("image_html"),
    #         # "附加替换": file_html,
    #         "表格插入": {
    #             "data_list": [['完全覆盖', '部分覆盖', '未覆盖'], [1, 2, 3], [1, 5, 5], [1, 9, 8], [2, 8, 9], [1, 8, 9]],
    #             "merge_row_cell": True,
    #             "merge_col_cell": True
    #         },
    #         "网络信息分析": [
    #             {"网络信息分析标题": "2.1.2 全网网元分类", "网络信息分析表格": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "×", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }, "全网网元": [{"网元名称": "NEA"}, {"网元名称": "NEB"}],
    #             "对比规则": "对比规则:123"},
    #             {"网络信息分析标题": "2.1.3 全网网元分类1", "网络信息分析表格": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "√", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }, "全网网元": [], "对比规则": "对比规则:456"},
    #         ],
    #         "折叠网络信息分析": [
    #             {"折叠标题": "2.1.2 全网网元分类", "折叠表格插入": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "×", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }},
    #             {"折叠标题": "2.1.3 全网网元分类1", "折叠表格插入": {
    #                 "data_list": [
    #                     ["#", "网元类型-工程",	"软件版本-工程", "硬件版本-工程", "覆盖结果对比",
    #                         "网元类型-实验室",	"软件版本-实验室", "硬件版本-实验室"],
    #                     ["1", "ZXMP M721E", "9.10",	"3.00",
    #                         "√", "ZXMP M721E", "9.10", "3.00"],
    #                     ["2", "ZXONE 19700", "9.00",	"1.00",
    #                         "√", "ZXONE 19700",	"9.00",	"1.00"]
    #                 ],
    #                 "merge_row_cell": False,
    #                 "merge_col_cell": False
    #             }}
    #         ]
    #     }
    # }, {"new_page_parent_url": "https://i.zte.com.cn/index/ispace/#/space/ff77f6673281495b9b262761a35aca09/wiki/page/3a888cb03826421a8773d8c676460693/view", "new_page_title": "运营商工程场景与实验室环境数据对比测试6"}
    # )
    # print(page_content_data)
    a = ""

