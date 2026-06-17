import logging
import re
from bs4 import BeautifulSoup
from api_data import Icenter_content_html_get
from task_common import write_task_database, clear_table_data
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def Icenter_table_get_two(url):
    """从iCenter页面提取表格数据并返回Python原生JSON格式（list of dict）

    Args:
        url (str): 要抓取的iCenter页面URL

    Returns:
        list: 表格数据的Python列表，每个元素是字典（key为列名，value为单元格内容）
              如果无数据或出错，返回空列表 []

    Raises:
        ValueError: 当输入URL无效时
    """
    # 输入验证
    if not url or not isinstance(url, str):
        raise ValueError("无效的URL参数")

    try:
        logger.info(f"开始获取iCenter表格数据，URL: {url}")

        # 1、获取iCenter页面内容
        page_html = Icenter_content_html_get(url)
        if not page_html:
            logger.warning("获取页面内容失败或返回空内容")
            return []  # 改为返回空列表，而不是 None

        # 2、解析页面内容
        soup = BeautifulSoup(page_html, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            logger.warning("页面中没有找到任何表格")
            return []

        data_list = []
        for item in tables:
            first_table = item
            data = []
            # 提取表头
            header_row = first_table.find('tr')
            if not header_row:
                logger.warning("表格中没有找到表头行")
                return []

            headers = []
            for th in header_row.find_all(['th', 'td']):
                # link = th.find('a')
                # if link and link.get('href'):
                #     content = link['href']
                # else:
                    # 使用 prettify() 保留原始HTML结构，再提取文本
                content = th.prettify()
                # 移除标签但保留换行符
                content = BeautifulSoup(content, 'html.parser').get_text(strip=False)
                content = re.sub(r'\n\s*\n', '\n', content.strip())
                headers.append(content.strip())

            # 提取表格数据
            for row in first_table.find_all('tr')[1:]:  # 跳过表头行
                row_data = {}
                for idx, cell in enumerate(row.find_all(['th', 'td'])):
                    try:
                        # link = cell.find('a')
                        # if link and link.get('href'):
                        #     content = link['href']
                        # else:
                        # 关键修改：保留原始换行
                        content = cell.prettify()
                        content = BeautifulSoup(content, 'html.parser').get_text(strip=False)
                        content = re.sub(r'\n\s*\n', '\n', content.strip())

                        # 用列名作为 key，内容作为 value
                        col_name = headers[idx] if idx < len(headers) else f"column_{idx}"
                        row_data[col_name] = content.strip() if isinstance(content, str) else str(content)
                    except Exception as cell_error:
                        logger.warning(f"处理单元格时出错: {str(cell_error)}")
                        col_name = headers[idx] if idx < len(headers) else f"column_{idx}"
                        row_data[col_name] = ""

                # 确保行数据与表头一致
                if len(row_data) == len(headers):
                    data.append(row_data)
                else:
                    logger.warning(f"跳过不匹配的行数据，表头长度: {len(headers)}, 行数据长度: {len(row_data)}")

            # if not data:
            #     logger.warning("没有提取到有效的表格数据")
            #     return []

            # ✅ 返回真正的 Python list，不是字符串！
            logger.info(f"成功提取表格数据，共 {len(data)} 条记录")
            data_list.append(data)
            print(data)
        return data_list
    except Exception as e:
        logger.error(f"处理表格数据时发生未预期错误: {str(e)}", exc_info=True)
        return []  # 出错时返回空列表，安全

def get_branch_leakage_data():
    url = "https://i.zte.com.cn/#/shared/c5dbe928c3f54634922abbf7012bc8c4/wiki/page/a5cde8f79aad11f0b38c630c81c5eac5/view"
    add_data, all_data = Icenter_table_get_two(url)
    add_ids = {item["故障/需求编号"] for item in add_data} 
    for item in all_data:
        item["首次合入时间"] = datetime.strptime(item["首次合入时间"], '%Y-%m-%d')
        if item["故障/需求编号"] in add_ids:
            item["是否增量"] = "是"
        else:
            item["是否增量"] = "否"
        item["标识"] = item["故障/需求编号"]  
        del item["故障/需求编号"] 
    clear_table_data('leakage_branch', '../data/sql_config.db') 
    write_task_database(all_data, 'leakage_branch', "标识", '../data/sql_config.db')

if __name__ == "__main__":
    get_branch_leakage_data()