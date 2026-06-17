from langgraph.graph import StateGraph, END, START
from typing import Any, Dict, List, Callable, Generator, TypedDict
import sys
import threading
import time
import requests
from pydantic import BaseModel, Field
import logging
import io
from agent_base import MessageDict, ConfigDict

def create_logger(name, stream=None):
    logger = logging.getLogger(name)
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)

    # 创建handler
    if stream is None:
        stream = sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    handler.terminator = ""

    # 设置自定义formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def create_progress_logger(name='progress_logger', stream=None):
    """创建专门用于不换行输出的logger"""
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    if stream is None:
        stream = sys.stdout
    handler = logging.StreamHandler(stream)
    handler.terminator = ""  # 关键设置
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False  # 防止传播到root logger
    
    return logger

# 打印点的函数
def print_dots():
    global stop_printing
    progress_logger = create_progress_logger(stream=stream_redirector)
    stop_printing = False
    while not stop_printing:
        progress_logger.info(".")
        time.sleep(0.5)
    else:
        progress_logger.info("\n\n")

# 全局变量控制打印点的线程
stop_printing = False

def stop_print_dot(dot_thread):
    global stop_printing
    stop_printing = True
    dot_thread.join()

class StreamRedirector:
    def __init__(self):
        self.buffer = io.StringIO()
        self.lock = threading.Lock()
        self.task_done = threading.Event()  # 新增任务完成事件

    def write(self, text):
        with self.lock:
            self.buffer.write(text)
            self.buffer.flush()

    def get_value(self):
        with self.lock:
            return self.buffer.getvalue()
    
    def reset(self):
        with self.lock:
            self.buffer.truncate(0)
            self.buffer.seek(0)


# 初始化流重定向器
stream_redirector = StreamRedirector()

logger = create_logger("icenter页面内容识别", stream_redirector)

cloud_desktop_addr = "http://10.90.149.145:8001"
irunner_agent_addr = "http://10.156.129.89:8000"

# 定义状态类型
class FtState(BaseModel):
    url: str
    html_content: str = ""
    json_data: str = ""
    content_type: str = ""
    test_data: str = ""
    test_case: str = ""
    result_content: str = ""
    body_content: str = ""
    response: Any = None
    curr_time: float = time.time()

def common_node_proc(state: FtState, service_url: str, payload_dict: Dict, result_dict: Dict, timeout=30) -> FtState:
    """通用节点处理"""
    service_name = service_url.split("/")[-1].replace("-", " ").title()
    logger.info(f"🔄 开始{service_name}处理...")
    dot_thread = threading.Thread(target=print_dots)
    dot_thread.start()
    payload = {}
    for payload_key, payload_value in payload_dict.items():
        if payload_value.startswith("state."):
            attr_name = payload_value.replace("state.", "")
            payload[payload_key] = getattr(state, attr_name)
        else:
            payload[payload_key] = payload_value
    try:
        logger.debug(f"👉 发送请求到: {service_url}\n\n")
        if timeout > 0:
            response = requests.post(service_url, json=payload, timeout=timeout)
        else:
            response = requests.post(service_url, json=payload)
        response.raise_for_status()
        response_json = response.json()
        for result_key, result_value in result_dict.items():
            setattr(state, result_key, response_json[result_value])
        execution_time = time.time() - state.curr_time
        # 停止打印点
        stop_print_dot(dot_thread)
        logger.info(f"✅ {service_name}处理完成，耗时{execution_time:.6f}秒\n\n")
        for result_key, result_value in result_dict.items():
            logger.debug(f"state.{result_key}: {response_json[result_value]}\n\n")
        state.curr_time = time.time()
        state.response = {"status": "success", "message": f"{service_name} success"}

        return state
    except requests.exceptions.RequestException as e:
        # 停止打印点
        stop_print_dot(dot_thread)
        logger.error(f"❌ {service_name}处理失败: {str(e)}\n\n")

        return {
            "curr_time": time.time(),
            "response": {"status": "error", "message": str(e)}
        }

def icenter2html_node(state: FtState) -> FtState:
    """ICENTER转HTML服务节点"""
    payload = {
        "url": "state.url"
    }
    result = {
        "html_content": "html"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/icenter-to-html",
        payload,
        result
    )

def html2json_node(state: FtState) -> FtState:
    """HTML转JSON服务节点"""
    payload = {
        "html_content": "state.html_content"
    }
    result = {
        "json_data": "json_data"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/html2json",
        payload,
        result
    )

def detect_content_node(state: FtState) -> FtState:
    """icenter页面内容识别服务节点"""
    payload = {
        "content": "state.json_data"
    }
    result = {
        "content_type": "content_type"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/detect-content",
        payload,
        result
    )

def gen_testdata_node(state: FtState) -> FtState:
    """测试数据生成服务节点"""
    payload = {
        "content": "state.json_data"
    }
    result = {
        "test_data": "test_data"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/gen-testdata",
        payload,
        result
    )

def write_testdata_node(state: FtState) -> FtState:
    """测试数据写入服务节点"""
    payload = {
        "filename": "d:\\qxcfg_new.json",
        "content":"state.test_data",
        "append": "{\"column\": 1}"
    }
    result = {}
    
    return common_node_proc(
        state,
        f"{irunner_agent_addr}/write-file",
        payload,
        result
    )

def irunner_node(state: FtState) -> FtState:
    """iRunner测试执行服务节点"""
    payload = {
        "userid": "10010430",
        "taskid": "693508"
    }
    result = {}
    
    return common_node_proc(
        state,
        f"{irunner_agent_addr}/irunner",
        payload,
        result,
        0
    )

def read_testcase_node(state: FtState) -> FtState:
    """测试用例读取服务节点"""
    payload = {
        "filename": "d:\\json_qx\\test_case.json"
    }
    result = {
        "test_case": "content"
    }
    
    return common_node_proc(
        state,
        f"{irunner_agent_addr}/read-file",
        payload,
        result
    )

def convert_testcase_node(state: FtState) -> FtState:
    """测试用例数据转换服务节点"""
    payload = {
        "content": "state.test_case"
    }
    result = {
        "body_content": "body_content"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/convert",
        payload,
        result
    )

def testcase2icenter_node(state: FtState) -> FtState:
    """测试用例写入icenter服务节点"""
    payload = {
        "url": "state.url",
        "content": "state.body_content",
        "op_type": "create",
        "title": "测试用例"
    }
    result = {}
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/json-to-icenter",
        payload,
        result
    )

def write_testcase_node(state: FtState) -> FtState:
    """测试用例写入服务节点"""
    payload = {
        "filename": "d:\\qxcfg_new.json",
        "content":"state.json_data",
        "append": "{\"column\": 2}"
    }
    result = {}
    
    return common_node_proc(
        state,
        f"{irunner_agent_addr}/write-file",
        payload,
        result
    )

def analyze_testresult_node(state: FtState) -> FtState:
    """测试执行结果分析服务节点"""
    payload = {
        "content": "state.test_case"
    }
    result = {
        "result_content": "result"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/analyze-test-case",
        payload,
        result
    )

def convert_testresult_node(state: FtState) -> FtState:
    """测试执行结果转换服务节点"""
    payload = {
        "content": "state.result_content"
    }
    result = {
        "body_content": "body_content"
    }
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/convert",
        payload,
        result
    )

def testresult2icenter_node(state: FtState) -> FtState:
    """测试结果写入icenter服务节点"""
    payload = {
        "url": "state.url",
        "content": "state.body_content",
        "op_type": "create",
        "title": "测试执行"
    }
    result = {}
    
    return common_node_proc(
        state,
        f"{cloud_desktop_addr}/json-to-icenter",
        payload,
        result
    )

# 调用子图的节点函数
def call_gen_ft_node(state: FtState) -> FtState:
    global logger
    logger = create_logger("FT用例生成", stream_redirector)
    app = build_gen_ft_graph()
    return app.invoke(state)

def call_run_ft_node(state: FtState) -> FtState:
    global logger
    logger = create_logger("FT用例执行", stream_redirector)
    app = build_run_ft_graph()
    return app.invoke(state)

def no_need_process_node(state: FtState) -> FtState:
    logger.info(f"✅ 当前页面已经是测试执行结果页面，不需要处理\n\n")
    return state

def ft_router_node(state: FtState) -> FtState:
    return state

def should_end(state: FtState) -> bool:
    if isinstance(state.response, dict) and state.response.get("status") == "success":
        return False
    else:
        return True

def build_state_graph(workflow: StateGraph, nodes: Dict[str, Callable], graph_str: str):
    """根据字符串描述构建状态图"""
    # 解析节点和边
    steps = graph_str.split("->")
    current_node = None
    node_name = None
    
    for i, step in enumerate(steps):
        # 处理条件边标记
        if step.startswith(">"):
            node_name = step[1:]
            is_conditional = True
        else:
            node_name = step
            is_conditional = False

        if node_name.startswith("^"):
            node_name = node_name[1:]
            is_start = True
        else:
            is_start = False
        if node_name.endswith("$"):
            node_name = node_name[:-1]
            is_end = True
        else:
            is_end = False
        
        # 添加节点（如果尚未添加）
        if node_name not in workflow.nodes:
            workflow.add_node(node_name, nodes[node_name])
        
        # 添加边
        if current_node is not None:
            if is_conditional:
                workflow.add_conditional_edges(
                    current_node,
                    should_end,
                    {True: END, False: node_name}
                )
            else:
                workflow.add_edge(current_node, node_name)
        if is_start:
            workflow.add_edge(START, node_name)
        if is_end:
            workflow.add_edge(node_name, END)
        current_node = node_name

def build_gen_ft_graph():
    nodes = {
        "gen-testdata": gen_testdata_node,
        "write-testdata": write_testdata_node,
        "irunner": irunner_node,
        "read-testcase": read_testcase_node,
        "convert": convert_testcase_node,
        "write-icenter": testcase2icenter_node
    }

    graph_str = "^gen-testdata->>write-testdata->>irunner->>read-testcase->>convert->>write-icenter$"
    # graph_str = "^read-testcase->>convert$"
    
    # 构建状态机图
    workflow = StateGraph(FtState)

    build_state_graph(workflow, nodes, graph_str)

    return workflow.compile()

def build_run_ft_graph():
    nodes = {
        "write-testdata": write_testcase_node,
        "irunner": irunner_node,
        "read-testcase": read_testcase_node,
        "analyze-testresult": analyze_testresult_node,
        "convert": convert_testresult_node,
        "write-icenter": testresult2icenter_node
    }

    graph_str = "^write-testdata->>irunner->>read-testcase->>analyze-testresult->>convert->>write-icenter$"
    # graph_str = "^read-testcase->>analyze-testresult$"
    
    # 构建状态机图
    workflow = StateGraph(FtState)

    build_state_graph(workflow, nodes, graph_str)

    return workflow.compile()


def get_content_type(state: FtState) -> str:
    return state.content_type


def build_main_graph():
    nodes = {
        "icenter2html": icenter2html_node,
        "html2json": html2json_node,
        "detect-content": detect_content_node,
        "ft-router": ft_router_node
    }

    graph_str = "^icenter2html->>html2json->>detect-content->>ft-router"

    # 构建状态机图
    workflow = StateGraph(FtState)

    build_state_graph(workflow, nodes, graph_str)

    workflow.add_node("gen_ft", call_gen_ft_node)
    workflow.add_node("run_ft", call_run_ft_node)
    workflow.add_node("no_process", no_need_process_node)

    workflow.add_conditional_edges(
        "ft-router", 
        get_content_type, 
        {"G": "gen_ft", "R": "run_ft", "E": "no_process"}
    )
    return workflow.compile()


def state_machine_runner(state: FtState):
    app = build_main_graph()
    app.invoke(state)

def state_machine_thread_func(state_machine_func, state, redirector):
    """任务执行线程"""
    try:
        state_machine_func(state)
    finally:
        redirector.task_done.set()  # 标记任务完成

def Agent_ft_langgraph(messages: List[MessageDict] = [], config: ConfigDict = {}) -> Generator[str, None, None]:
    """
    LangGraph版FT用例生成应用（流式输出）
    
    Args:
        messages: 对话消息列表，格式 [{"role": "user"/"assistant", "content": "..."}]
        config: 配置字典，包含 model_name 和 temperature
    
    Yields:
        逐字符返回应用输出
    """
    if not messages:        
        yield ""
        return
    
    # 从消息中提取url
    url = messages[-1]["content"]
    if not url:
        yield "请输入有效的icenter页面地址"
        return

    state = FtState(url=url, curr_time=time.time())

    global logger
    logger = create_logger("icenter页面内容识别", stream_redirector)

    # 创建并启动任务线程
    task_thread = threading.Thread(
        target=state_machine_thread_func,
        args=(state_machine_runner, state, stream_redirector),
        name="TaskThread"
    )
    task_thread.start()

    while not stream_redirector.task_done.is_set():  # 非阻塞检查任务状态
        content = stream_redirector.get_value()
        if content:
            # print(content, end='', flush=True)  # 实时打印到控制台
            stream_redirector.reset()  # 清空已处理内容
            yield content
        else:
            # 使用非阻塞等待（最多等待0.1秒）
            stream_redirector.task_done.wait(timeout=0.1)

    # 最后一次检查确保所有日志都被处理
    remaining = stream_redirector.get_value()
    if remaining:
        # print(remaining, end='', flush=True)
        stream_redirector.reset()  # 清空已处理内容
        yield remaining

    # 等待任务线程完成
    task_thread.join()
    stream_redirector.task_done.clear()

def Agent_call_test(messages: List[MessageDict] = [], config: ConfigDict = {}) -> str:
    """
    测试函数：调用 Agent_ft_langchain 并逐字打印，返回完整回答
    
    Args:
        messages: 聊天消息列表
        config: 模型配置，如 {"model_name": "...", "temperature": 0.7}
    
    Returns:
        完整的应用字符串
    """
    answer = []
    
    try:
        for chunk in Agent_ft_langgraph(messages, config):
            # 逐字符打印，模拟打字机效果
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(0.01)  # 可调：控制打印速度
            answer.append(chunk)
        
        print()  # 换行
        return "".join(answer)
    
    except Exception as e:
        error_msg = f"[测试错误] {str(e)}"
        print(error_msg)
        return error_msg


def test_Agent_ft_langgraph():
    """测试ft用例生成功能"""

    while True:
        url = input("🚀 请输入有效的icenter页面地址，输入q退出：")
        
        # 如果用户输入 'q' 或 'Q'，则退出循环
        if url.lower() == 'q':
            print("退出程序。")
            break
        # 初始化对话历史
        messages: List[MessageDict] = []

        # 默认配置 - 使用config.json中的模型键
        config: ConfigDict = {}

        messages.append({"role": "user", "content": url})
        answer = Agent_call_test(messages, config)
        messages.append({"role": "assistant", "content": answer})


# 使用示例
if __name__ == "__main__":
    test_Agent_ft_langgraph()
