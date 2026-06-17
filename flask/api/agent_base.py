from typing import TypedDict

# 定义消息类型的结构
class MessageDict(TypedDict):
    role: str # "user", "assistant", "system"
    content: str

# 定义配置字典的结构
class ConfigDict(TypedDict, total=False):
    user_id: str
    user_token: str
    model: str
    context: str
    knowledge: str
    session_id: str
    request_id: str
    temperature: float
