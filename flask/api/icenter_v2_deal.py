# -*- coding: utf-8 -*-
import icenter_base
import re
from bs4 import BeautifulSoup
from collections import OrderedDict

NORMAL_TYPE_LIST = ['p', 'img', 'figure', 'ul', 'ol', 'table']
MACRO_TYPE_NAME_LIST = ['div', 'details', 'inline-macro',]  ## p 有很多特殊的
MACRO_TYPE_LIST = ['div', 'details', 'inline-macro','inlineMacro','blockMacro' ,'block',]  ## tag-start
## 宏tag 属性中排除的部分 所有id均排除 内置在函数中 其他局的不重要的字段自己添加在这里
EXCLUDE_ATTRS_LIST = ['style','open', ]


#blockMacro 往往内部嵌套一个tag-start 为block 的div
class Keyword:
    def __init__(self, keyword):
        self.keyword = keyword
        self.attributes = {}

    def add_attribute(self, attribute_name, attribute_value):
        self.attributes[attribute_name] = attribute_value

    def get_attribute(self, attribute_name):
        return self.attributes.get(attribute_name)

    def get_attributes(self,):
        return self.attributes

    def remove_attribute(self, attribute_name):
        if attribute_name in self.attributes:
            del self.attributes[attribute_name]

    def __str__(self):
        return f"Keyword: {self.keyword}, Attributes: {self.attributes}"


# 创建一个包含多个关键词对象的字典
def add_keywords(keywords_list):
    keywords_dict = {}
    for keyword_info in keywords_list:
        keyword = Keyword(keyword_info['keyword'])
        for attr_name, attr_value in keyword_info['attributes'].items():
            keyword.add_attribute(attr_name, attr_value)
        keywords_dict[keyword_info['keyword']] = keyword
    return keywords_dict


keywords_list = [
    {
        'keyword': '块', ##  多种宏中最内层的div  自命名为块
        'attributes': {
            'class': ['ze-macro-body'],
            'tag-start': 'block',
        }
    },
    {
        'keyword': '高亮块',
        'attributes': {
            'type': 'highlight',
            'tag-start': 'div',
        }
    },
    {
        'keyword': '内容块',
        'attributes': {
            'block-type': 'custom',
            'tag-start': 'div',
        }
    },
    {
        'keyword': '折叠块',
        'attributes': {
            'tag-start': 'details',
        }
    },
    # {
    #     'keyword': '生成锚点链接',
    #     'attributes': {
    #         'tag-start': 'p',
    #     }
    # },
    # {
    #     'keyword': '特殊字符', ## 与普通段落没有区别
    #     'attributes': {
    #         'tag-start': 'p',
    #     }
    # },
    {
        'keyword': '缩略语', ##
        'attributes': {
            'm-dita-tag': 'gxref',
            'macro-key': 'AbbrMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '全局变量',
        'attributes': {
            'm-dita-tag': 'rpph',
            'macro-key': 'globalVariableMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '关键词',
        'attributes': {
            'm-dita-tag': 'cmdname',
            'macro-key': 'keyWordMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '文档间链接',
        'attributes': {
            'm-dita-tag': 'ph',
            'macro-key': 'keyWordMacro',##与关键词撞车
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '书名',
        'attributes': {
            'm-dita-tag': 'cite',
            'macro-key': 'bookNameMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '文件路径',
        'attributes': {
            'm-dita-tag': 'filepath',
            'macro-key': 'filePathMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '菜单',
        'attributes': {
            'm-dita-tag': 'menucascade',
            'macro-key': 'menuCascadeMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '子菜单',
        'attributes': {
            'm-dita-tag': 'uicontrol',
            'macro-key': 'menuItemMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '屏幕输出',
        'attributes': {
            'm-dita-tag': 'screen',
            'macro-key': 'screenMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '注释',
        'attributes': {
            'm-dita-tag': 'annotation',
            'macro-key': 'annotationMacro',
            'tag-start': 'blockMacro', ## div
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '观点引述',
        'attributes': {
            'm-dita-tag': 'q',
            'macro-key': 'opinionMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '长单词',
        'attributes': {
            'm-dita-tag': 'ph',  ## 与文档间链接 撞车
            'macro-key': 'longWordMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '用户输入',
        'attributes': {
            'm-dita-tag': 'userinput',
            'macro-key': 'UserInputMacro',
            'tag-start': 'inlineMacro',## inline-macro
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '系统输出',
        'attributes': {
            'm-dita-tag': 'systemoutput',
            'macro-key': 'SystemOutputMacro',
            'tag-start': 'inlineMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '表格汇聚宏',
        'attributes': {
            'macro-key': 'com.zte.rdcloud.TableConvergenceMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '显示子页面宏',
        'attributes': {
            'macro-key': 'ChildrenDisplayMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '从模板创建宏',
        'attributes': {
            'macro-key': 'CreateFromTemplateMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '包含页面宏',
        'attributes': {
            'macro-key': 'PageIncludeMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': 'plantuml宏',
        'attributes': {
            'macro-key': 'PlantUmlMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '时序图宏',
        'attributes': {
            'macro-key': 'PlantUMLSequenceDiagramMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '自动增加标签宏',
        'attributes': {
            'macro-key': 'AutoSetTagMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '页面属性报告宏',
        'attributes': {
            'macro-key': 'com.zte.rdcloud.PagePropertyReportMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '页面属性宏',
        'attributes': {
            'macro-key': 'com.zte.rdcloud.PagePropertyMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },
    {
        'keyword': '选择标签宏',
        'attributes': {
            'macro-key': 'ChooseLabelMacro',
            'tag-start': 'blockMacro',
            'class': ['ze-macro'],
        }
    },


]

MACRO_KEYWORDS_DICT = add_keywords(keywords_list)


def get_h_text(h_num_tag):
    h_num_tag = parse_html_input_format(h_num_tag)
    h_text = h_num_tag.get_text(strip=True)
    return h_text


def para_handle(content_tag):
    res = get_h_text(content_tag)
    res += '\n'
    return res


## 标题分割
def parse_html_input_format(html_content):
    if isinstance(html_content, str):
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        soup = html_content
    return soup


def get_outer_tags(html_content):## 对于一整块的章节 作用是获取最外层的所有tag ； 对于一个tag而言 获取的是向内一层的tag
    """
    获取HTML内容中最外层标签的类型和内容，但排除div标签。
    参数:
    html_content (str): HTML字符串
    返回:
    list: 包含每个最外层标签的类型和内容的列表
    """
    soup = parse_html_input_format(html_content)
    # 获取所有最外层标签，但排除div标签
    tags = [tag for tag in soup.find_all(recursive=False)] #if tag.name != 'div'
    # 返回每个标签的类型和内容
    result= [{'Type': tag.name, 'Content': tag} for tag in tags]
    return result


def get_inner_tags(html_content_one_tag): ## 输入一整个tag
    """
    获取HTML内容中次外层标签的类型和内容，但排除div标签。
    参数:
    html_content (str): HTML字符串
    返回:
    list: 包含每个次外层标签的类型和内容的列表
    """
    soup = parse_html_input_format(html_content_one_tag)
    result = get_outer_tags(soup)
    target_tag = result[0]['Type']
    soup = soup.find(target_tag)
    # 获取所有次外层标签，但排除div标签
    tags = [tag for tag in soup.find_all(recursive=False)] # if tag.name != 'div'
    # 返回每个标签的类型和内容
    result= [{'Type': tag.name, 'Content': tag} for tag in tags]
    return result


def parse_html_tables(html_content):
    """
    解析HTML中的所有表格，并返回一个包含多个二维数组的列表。
    每个二维数组记录一个表格的内容，其中每个元素是一个元组 (cell_text, cell_type)。
    参数:
    html_content (str): HTML内容字符串
    返回:
    list: 包含多个二维数组的列表，每个二维数组对应一个表格的数据
    """
    # 使用BeautifulSoup解析HTML内容
    soup = parse_html_input_format(html_content)
    # 找到所有表格元素
    tables = soup.find_all('table')
    # 初始化一个列表来存储所有表格的数据
    all_tables_data = []
    # 遍历每一个表格
    for table in tables:
        # 初始化一个列表来存储当前表格的数据
        table_data = []
        # 遍历表格中的每一行
        for row in table.find_all('tr'):
            row_data = []
            # 遍历每一行中的每一个单元格（包括th和td）
            for cell in row.find_all(['th', 'td']):  ##  td: table_data th: table_head
                cell_content=[]
                # 获取单元格的文本内容，并去除首尾空白字符
                sub_tag_list = get_outer_tags(cell)
                # if len(sub_tag_list) == 0:
                #     print('herr')
                for item in sub_tag_list:
                    res = parser_html_by_type(item['Type'],item['Content'])
                    cell_content.append(res)
                if len(cell_content) == 1:
                    cell_content = cell_content[0]
                # 确定单元格的类型（th或td）
                cell_type = cell.name
                # 将单元格的文本内容和类型作为一个元组添加到当前行的列表中
                row_data.append((cell_content, cell_type))
            # 将当前行的列表添加到当前表格的数据列表中
            table_data.append(row_data)
        # 将当前表格的数据列表添加到所有表格的数据列表中
        all_tables_data.append(table_data)
        if len(all_tables_data) == 1:
            all_tables_data = all_tables_data[0]  ## 一般就一个
    return all_tables_data


## 有序、无序列表解析
def parse_lists(html_content):
    soup = parse_html_input_format(html_content)
    lists_info = []
    # Find all ordered lists (ol) and unordered lists (ul)
    for list_tag in soup.find_all(['ol', 'ul']):
        is_ordered = list_tag.name == 'ol'
        items = [item.get_text(strip=True) for item in list_tag.find_all('p')]
        lists_info.append({'is_ordered': is_ordered, 'items': items})
    return lists_info


## 图片解析
def parse_images(html_content):
    soup = parse_html_input_format(html_content)
    images = []
    # Find all <img> tags
    img_tags = soup.find_all('img')
    for img in img_tags:
        img_info = {
            'img_src': img['src'],
            # 'title': '',
            # 'captions': []
        }
        images.append(img_info)
    return images


# 提取章节内容，level为章节层级（默认为一级标题）
def extract_content_between_h_level(html_content: str, level=1):
    soup = BeautifulSoup(html_content, 'html.parser')
    h1_tags = soup.find_all("h"+str(level))
    results = OrderedDict()
    if not h1_tags: ## 无具体分级  直接整体返回
        results["h" + str(level) + '_序'] = html_content
        return results
    # 获取首个h1之前的内容
    first_h1 = h1_tags[0]
    previous_element = first_h1.previous_sibling
    content = ""
    while previous_element:
        if previous_element.name is not None:
            content = str(previous_element) + '\n' + content
        previous_element = previous_element.previous_sibling
    results["h"+str(level)+'_序'] = content
    # 获取两个h1之间的内容
    for i in range(len(h1_tags) - 1):
        current_h1 = h1_tags[i]
        current_h1_title = get_h_text(current_h1)
        next_h1 = h1_tags[i + 1]
        content = ""
        element = current_h1.next_sibling
        while element and element != next_h1:
            if element.name is not None:
                content += str(element)
            element = element.next_sibling
        results[current_h1_title]=content
    # 获取最后一个h1之后的内容
    last_h1 = h1_tags[-1]
    last_h11_title = get_h_text(last_h1)
    next_element = last_h1.next_sibling
    content = ""
    while next_element:
        if next_element.name is not None:
            content += str(next_element)
        next_element = next_element.next_sibling
    results[last_h11_title] = content
    return results


def p_type_is_macro(tag):
    inner_value = get_outer_tags(tag)
    if len(inner_value) != 0 and inner_value[0]['Type'] in MACRO_TYPE_LIST:
        return True
    return False


def parser_html_by_type(type_in: str, content_tag) -> dict:## 需要最外层的属性  TYPE需要扩展一下
    res = None
    if type_in in ['figure']:
        res_list = get_inner_tags(str(content_tag))
        res_local=[]
        for tc_dict in res_list:
            result = parser_html_by_type(tc_dict['Type'], tc_dict['Content'])
            res_local.append(result)
        res = res_local
    elif type_in in ['img']:
        res = parse_images(str(content_tag))
    elif type_in in ['ul', 'ol']:
        res = parse_lists(str(content_tag))
    elif type_in in ['table']:
        res = parse_html_tables(str(content_tag))
    elif type_in in ['p', 'figcaption', 'span', 'summary']: ## 宏中的折叠块没有什么有效特殊信息 当普通文字处理即可
        if type_in in ['p']:
            inner_value = get_outer_tags(content_tag)
            if len(inner_value) != 0 and inner_value[0]['Type'] in MACRO_TYPE_LIST:  ##  宏定义的内容都在跑中的一层 有且只有一个inline 只检查首个即可
                type_tmp, res = get_macro_type_and_value(inner_value[0]['Content'])
                if type_tmp is not None:
                    type_in = type_tmp
            else:
                res = para_handle(content_tag)
        else: ## 普通段落 或表头
            res = para_handle(content_tag)
    elif type_in in MACRO_TYPE_LIST:
        type_tmp, res = get_macro_type_and_value(content_tag)
        if type_tmp is not None:
            type_in = type_tmp
    elif type_in in ['br']:
        res = ''
    return {'type': type_in, 'value': res}


# 解析icenter2.0的内容块
def get_macro_type_and_value(tag, keywords_dict=MACRO_KEYWORDS_DICT):
    attrs = tag.attrs
    # tag_attrs = set(tag.attrs)
    if tag.get('tag-start') in MACRO_TYPE_LIST:
        for type, macro in keywords_dict.items():
            macro_dict = macro.get_attributes()
            if tag.get('tag-start') == macro_dict.get('tag-start') and all(tag.attrs.get(k) == v for k, v in macro_dict.items()):
                value = get_macro_value(tag, EXCLUDE_ATTRS_LIST)
                return type ,value
    elif tag.get('tag-start') in ['p'] and p_type_is_macro(tag):  ## 特殊的 包括内联宏的段落 ## 外层控制
        return get_macro_type_and_value(tag, keywords_dict)
    return None,None


def get_macro_value(tag, exclude_attrs=None):
    ## 对于该函数 tag 类型已知
    value_dict = {}
    ## tag块首内容 删除垃圾信息
    attributes = tag.attrs
    if exclude_attrs is None:  ## 全部返回
        value_dict['tag_head'] = attributes
    else:
        filtered_attributes = {k: v for k, v in attributes.items() if k not in exclude_attrs and not k.endswith('-id')}
        value_dict['tag_head'] = filtered_attributes
    ## tag块内内容
    type_in = tag.name
    tag_block = parser_html_block(type_in, tag)
    value_dict['tag_block'] = tag_block
    return value_dict


def parser_html_block(type_in: str, content_tag) -> list:
    res_local = []
    if type_in in MACRO_TYPE_NAME_LIST:
        res_list = get_outer_tags(content_tag)
        last_tc_dict_type = ''
        ## 针对inline-macro 中无嵌套tag时 直接获取他的
        if len(res_list) == 0:
            result =get_h_text(content_tag)
            res_local.append(result)
        else:
            for tc_dict in res_list:
                result = parser_html_by_type(tc_dict['Type'], tc_dict['Content'])
                if tc_dict['Type'] != 'p':
                    res_local.append(result)
                else:  ## 块内仍可堆叠
                    if last_tc_dict_type != 'p':
                        res_local.append(result)
                    else:
                        res_local[-1]['value'] += result.get('value')
                last_tc_dict_type = tc_dict['Type']
    return res_local


# 将html转化为格式化输出
def html_get_format(soup_str: str, level=1) -> list:
    if soup_str is None:
        return None
    result_dict = []
    h1_dict = extract_content_between_h_level(soup_str, level)
    # 提取的页面无章节时 整体作为序
    for k, v in h1_dict.items():
        chapter_list = []
        if v == '':  ## 无序的情况
            tmp_dict2 = {
                'chapter_title': k,
                'chapter_content': v,
            }
            result_dict.append(tmp_dict2)
            continue
        h1_value_list = get_outer_tags(v)
        if any('h' in tc_dict['Type'] for tc_dict in h1_value_list):
            h_num_dict = {'chapter_title': k, 'chapter_content': html_get_format(str(v), level + 1)}
            result_dict.append(h_num_dict)
            continue
        last_tc_dict_type = ''
        for tc_dict in h1_value_list:
            is_special_para_flag = 'p'
            tmp_dict = {'chapter_title': k, 'chapter_content': ''}
            if tc_dict['Type'] in NORMAL_TYPE_LIST or tc_dict['Type'] in MACRO_TYPE_NAME_LIST:  ## 基本类型 ## 双类型混合
                type_value_res = parser_html_by_type(tc_dict['Type'], tc_dict['Content'])
                is_special_para_flag=type_value_res.get('type')
                if last_tc_dict_type != 'p' or is_special_para_flag != 'p':  ## 上个章节内容  段落内容合并 ## todo p 中有宏
                    ## 宏类型   暂不考虑 生成锚点链接 &  条件变量。  特殊字符 按照普通段落处理即可
                    chapter_list.append(type_value_res)
                else:
                    chapter_list[-1]['value'] += type_value_res.get('value') if type_value_res.get('value') is not None else ''

            else:
                ## 其他类型
                chapter_list.append(tc_dict['Content'])
            tmp_dict['chapter_content'] = chapter_list
            last_tc_dict_type = tc_dict['Type']  if is_special_para_flag == 'p' else is_special_para_flag  ##  宏特殊返回
        result_dict.append(tmp_dict)
    return result_dict


def get_chapter(format_list: list, chapter_num: list):
    # 入参检查
    if format_list is None or chapter_num is None:
        return None
    empty_dict = {}
    tmp_num = chapter_num[0]
    # 异常防护
    if type(format_list) == type(empty_dict) or len(format_list) <= tmp_num:
        return None
    # 章节数字列表只剩一位数字时结束递归
    if len(chapter_num) == 1:
        return format_list[tmp_num]
    # 进入递归
    chapter_num.pop(0)
    return get_chapter(format_list[tmp_num].get('chapter_content'), chapter_num)


def extract_table_values_and_tag(value_table_list):
    empty_dict = {}
    empty_tuple = ()
    empty_list = []
    value2 = []
    for row in value_table_list:
        tmp_list = []
        for item in row:
            tmp_str = ''
            if type(item) == type(empty_tuple):
                if type(item[0]) == type(empty_dict):
                    tmp_list.append(item[0]['value'])
                elif type(item[0]) == type(empty_list):
                    for tmp in item[0]:
                        tmp_str += tmp['value']
                    tmp_list.append(tmp_str)
                else:
                    tmp_list.append('')
        value2.append(tmp_list)
    tag_array = [[item[1] for item in row] for row in value_table_list]
    return value2, tag_array


def determine_table_type(tag_array):
    rows = len(tag_array)
    cols = len(tag_array[0]) if rows > 0 else 0
    both_has_th_in_first_row = all(tag == 'th' for tag in tag_array[0]) if rows > 0 else False
    both_has_th_in_first_col = all(tag_array[r][0] == 'th' for r in range(rows)) if cols > 0 else False
    has_th_in_first_row = any(tag == 'th' for tag in tag_array[0]) if rows > 0 else False
    has_th_in_first_col = any(tag_array[r][0] == 'th' for r in range(rows)) if cols > 0 else False
    if both_has_th_in_first_row and not both_has_th_in_first_col:
        return "纵表"
    elif both_has_th_in_first_col and not both_has_th_in_first_row:
        return "横表"
    elif both_has_th_in_first_row and both_has_th_in_first_col:
        return "综合"
    elif not has_th_in_first_col and not has_th_in_first_row :
        return "无表头表"
    else:
        return "非标准表"


def rebulid_table_value(table_dict: dict) -> dict:
    if table_dict is None:
        return None
    value_table_list = table_dict.get('value')
    value2, tag_array = extract_table_values_and_tag(value_table_list)
    table_type = determine_table_type(tag_array)
    result_dict = {
        "type": table_type,
        "name": '',
        "data_list": value2,
        "comment": ''
    }
    return result_dict

def rebulid_img_value(img_dict: dict) -> dict:
    if img_dict is None:
        return None
    img_src = img_dict.get('value')
    result_dict = {
        "type": "图片",
        "name": '',
        "data_list": img_src,
        "comment": ''
    }
    return result_dict


# figure类型解析
def rebulid_figure_value(figure_dict: dict) -> dict:
    if figure_dict is None:
        return None
    table_type = ''
    figure_name = ''
    data_list = []
    comment = []
    figure_list = figure_dict.get('value')
    for dict_item in figure_list:
        if dict_item.get('type') == 'figcaption':
            figure_name = dict_item.get('value')
            continue
        if dict_item.get('type') == 'table':
            table_dict = rebulid_table_value(dict_item)
            table_type = table_dict.get('type')
            data_list = table_dict.get('data_list')
            continue
        if dict_item.get('type') == 'img':
            table_type = 'img'
            data_list = dict_item.get('value')
            continue
        if dict_item.get('type') == 'ol':
            comment = dict_item.get('value')
            continue
    return {
        "type": table_type,
        "name": figure_name,
        "data_list": data_list,
        "comment": comment
    }






# 对外提供api
def get_spaceId_pageId_by_url(url: str) -> dict:
    """
    根据url解析spaceId和pageId  1.0/2.0
    :param url: 需要进行解析的页面完整链接
    :return: 一个字典{
        'spaceId': 空间ID,
        'pageId': 页面ID
    }
    """
    if url is None or url == '':
        return None
    else:
        pattern = r'/space/([^/]+)/wiki/page/([^/]+)/'
        match = re.search(pattern, url)
        if match:
            spaceId = match.group(1)
            pageId = match.group(2)
        else:
            return None
    # 构建输出字典
    return {
        'spaceId': spaceId,
        'pageId': pageId
    }


# 对外提供api
def icenter_get_format(url: str, X_Emp_No, X_Auth_Value, APP_Code):
    """
    获取icenter2.0页面的格式化输出
    :param url:  需要提取的2.0空间页面完整链接
    :param X_Emp_No:  工号
    :param X_Auth_Value:  uac token
    :param APP_Code:  InOne应用的APPCode
    :return:  一个列表，列表元素为字典，每一个列表元素对应一个章节字典
    """
    # 入参检查
    if url is None or url == '':
        return None
    # 从url中解析spaceId/pageId
    url_info = get_spaceId_pageId_by_url(url)
    if url_info is None:
        return None
    # 查询文档内容2.0
    resp = icenter_base.icenter_get(url_info.get('spaceId'), url_info.get('pageId'), 'HTML', X_Emp_No, X_Auth_Value, APP_Code)
    # 查询文档内容失败
    if resp['code']['msgId'] != 'RetCode.Success':
        return None
    soup = BeautifulSoup(resp['bo']['contentBody'], 'html.parser')
    # 文档内容进行格式化处理，输出为列表，列表元素为字典
    result = html_get_format(resp['bo']['contentBody'], 1)
    return result


# 对外提供api
def icenter_format_get_chapter(format_list: list, chapter_num: str):
    """
    章节内容获取，能够根据传入的页面格式化输出和想要获取对应的章节字符如 1.1  3.2  5
    :param format_list: 页面格式化输出
    :param chapter_num: 章节字符，如 1.1  3.2  5  2.0
    :return: 返回对应章节字典{'chapter_title': 章节名, 'chapter_content': 章节内容（是一个列表）
    }
    """
    # 入参检查
    if format_list is None or chapter_num is None or chapter_num == '':
        return None
    # 获取章节数字列表（将章节字符解析为数字列表）
    num_list_char = chapter_num.split('.')
    chapter_num_list = [int(char) for char in num_list_char]
    # 获取章节内容，输出为字典
    result_chapter = get_chapter(format_list, chapter_num_list)
    return result_chapter


# 对外提供api
def chapter_parse(chapter_dict: dict):
    """
    格式化章节解析api（必须是最小章节单位，不能再有子章节），暂时只能解析段落/图片/表格
    :param chapter_dict: 章节字典
    :return: 字典，格式同输入
    """
    if chapter_dict is None:
        return None
    empty_list = []
    result_list = []
    chapter_title = chapter_dict.get('chapter_title')
    chapter_content = chapter_dict.get('chapter_content')
    if type(chapter_content) != type(empty_list):
        return None
    last_dict_type = ''
    for tmp_dict in chapter_content:
        current_dict_type = tmp_dict.get('type')
        if current_dict_type == 'p': # 段落处理
            if bool(tmp_dict.get('value')) and (c == '\n' for c in tmp_dict.get('value')):
                continue
            result_list.append(tmp_dict)
        elif current_dict_type == 'img': # 图片处理
            result_list.append(rebulid_img_value(tmp_dict))
            continue
        elif current_dict_type == 'table': # 表格处理
            last_dict_type = 'table'
            result_list.append(rebulid_table_value(tmp_dict))
            continue
        elif current_dict_type == 'figure': # 图片/表格处理（带表名/图名/表注/图注）
            result_list.append(rebulid_figure_value(tmp_dict))
            continue
        else:
            continue
    return {
        'chapter_title': chapter_title,
        'chapter_content': result_list
    }
