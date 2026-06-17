import requests
import json
import time
import threading
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# -------------------------- 核心配置（可根据实际情况调整） --------------------------
API_URL = "https://wsit.zx.zte.com.cn/api/api_data/API_Knowledge_requirement_tree_refresh"
# API_URL = "http://10.239.69.183:9001/api/api_data/API_Knowledge_requirement_tree_refresh"
SCOPES = ["智能OTN", "M721", "NTON"]

# 超时配置（关键：覆盖最长20分钟响应）
CONNECT_TIMEOUT = 30    # TCP连接建立超时（秒）
READ_TIMEOUT = 1500     # 数据读取超时（秒）= 25分钟 > 最长20分钟
TOTAL_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

# 重试配置（网络波动自动恢复）
MAX_RETRIES = 3         # 单请求最多重试3次
RETRY_DELAY = 60        # 失败后等待1分钟再重试

# 心跳配置（解决"脚本是否卡住"的感知问题）
HEARTBEAT_INTERVAL = 60 # 每分钟打印一次等待状态

# 请求头配置
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Python-Requests/2.31.0"
}
# -----------------------------------------------------------------------------------

class HeartbeatThread(threading.Thread):
    """守护线程：长请求期间定期打印状态，防止用户误以为脚本卡死"""
    def __init__(self, scope: str, interval: int = 60):
        super().__init__(daemon=True)
        self.scope = scope
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self):
        start_time = time.time()
        while not self._stop_event.is_set():
            elapsed = int(time.time() - start_time)
            print(f"⏳ 等待 {self.scope} 响应中... 已耗时 {elapsed//60}分{elapsed%60}秒")
            self._stop_event.wait(self.interval)

    def stop(self):
        self._stop_event.set()

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_fixed(RETRY_DELAY),
    retry=retry_if_exception_type((
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
        requests.exceptions.SSLError,
        requests.exceptions.ChunkedEncodingError
    )),
    before_sleep=lambda state: print(
        f"⚠️  第 {state.attempt_number} 次请求失败，{RETRY_DELAY}秒后进行第 {state.attempt_number+1} 次重试..."
    )
)
def send_refresh_request(scope: str) -> Dict[str, Any]:
    """发送单个刷新请求（带自动重试）"""
    payload = {"scope": scope}
    
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json=payload,
        timeout=TOTAL_TIMEOUT,
        verify=False  # 生产环境建议开启或指定证书路径
    )
    response.raise_for_status()  # 捕获4xx/5xx HTTP错误
    return response.json()

def main():
    print(f"=== API知识树刷新任务启动 ===")
    print(f"API地址: {API_URL}")
    print(f"待刷新范围: {', '.join(SCOPES)}")
    print(f"最大响应等待: {READ_TIMEOUT//60}分钟")
    print(f"自动重试: 最多{MAX_RETRIES}次，间隔{RETRY_DELAY}秒")
    print("=" * 70)
    
    total_start = time.time()
    success_count = 0
    failed_scopes = []
    
    for idx, scope in enumerate(SCOPES, 1):
        print(f"\n[{idx}/{len(SCOPES)}] 开始处理: {scope}")
        req_start = time.time()
        
        # 启动心跳线程
        heartbeat = HeartbeatThread(scope, HEARTBEAT_INTERVAL)
        heartbeat.start()
        
        try:
            result = send_refresh_request(scope)
            req_elapsed = time.time() - req_start
            
            # 停止心跳
            heartbeat.stop()
            heartbeat.join()
            
            # 解析响应
            code = result.get("code", "N/A")
            data = result.get("data", {})
            
            if code == 200:
                print(f"✅ {scope} 同步成功！耗时: {int(req_elapsed//60)}分{int(req_elapsed%60)}秒")
                print(f"   节点数: {data.get('nodeCount', 'N/A')}")
                print(f"   刷新时间: {data.get('refreshedAt', 'N/A')}")
                print(f"   结果: {data.get('result', {}).get('message', 'N/A')}")
                success_count += 1
            else:
                print(f"⚠️  {scope} 同步异常！耗时: {int(req_elapsed//60)}分{int(req_elapsed%60)}秒")
                print(f"   状态码: {code}, 信息: {result.get('message', 'N/A')}")
                failed_scopes.append(scope)
                
        except Exception as e:
            heartbeat.stop()
            heartbeat.join()
            req_elapsed = time.time() - req_start
            print(f"❌ {scope} 同步失败！耗时: {int(req_elapsed//60)}分{int(req_elapsed%60)}秒")
            print(f"   错误: {str(e)}")
            failed_scopes.append(scope)
            continue
    
    # 任务总结
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print(f"=== 任务执行完成 ===")
    print(f"总耗时: {int(total_elapsed//60)}分{int(total_elapsed%60)}秒")
    print(f"成功: {success_count}/{len(SCOPES)}")
    
    if failed_scopes:
        print(f"失败范围: {', '.join(failed_scopes)}")
        print("建议: 检查网络后手动重试失败项")
    else:
        print("🎉 所有范围刷新成功！")

if __name__ == "__main__":
    main()