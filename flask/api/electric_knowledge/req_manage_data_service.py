import os

from uuid import uuid4
from typing import Optional
from datetime import datetime
from urllib.parse import quote_plus
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer

from electric_knowledge.data_model import db, REQ_MANAGE_AGENT_CHAT_RECORD, REQ_MANAGE_AGENT_PROMPT, REQ_MANAGE_AGENT_MCP_CFG
from electric_knowledge.db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE, DB_PORT
from sqlalchemy import or_, and_, insert, update, delete, column, table, text, label, desc, case, func


class ReqManageAgentChatRecord(BaseModel):
    id: Optional[int] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    model: Optional[str] = None
    tool_name_str: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


def get_chat_record_list_by_session_id(session_id: str):
    """返回指定session的完整聊天历史, 按时间排序"""
    try:
        model_list = db.session.query(REQ_MANAGE_AGENT_CHAT_RECORD).filter(REQ_MANAGE_AGENT_CHAT_RECORD.session_id == session_id).order_by(REQ_MANAGE_AGENT_CHAT_RECORD.timestamp).all()
        return [ReqManageAgentChatRecord.model_validate(model_item).model_dump() for model_item in model_list]
    except Exception as e:
        print(f"An error occurred in get_chat_record_list_by_session_id: {e}")
        db.session.rollback()
        return []


def add_single_chat_record(chat_record_dict: dict):
    """保存一条聊天记录"""
    try:
        model = REQ_MANAGE_AGENT_CHAT_RECORD(
            session_id=chat_record_dict.get("session_id"),
            request_id=str(uuid4()),
            role=chat_record_dict["role"],
            user_id=chat_record_dict.get("user_id"),
            user_name=chat_record_dict.get("user_name"),
            model=chat_record_dict.get("model"),
            tool_name_str=chat_record_dict.get("tool_name_str"),
            content=chat_record_dict["content"],
        )
        db.session.add(model)
        db.session.commit()
    except Exception as e:
        print(f"An error occurred in add_single_chat_record: {e}")
        db.session.rollback()


def get_chat_record_list_by_user_id(user_id: str):
    """获取用户最近聊天记录"""
    try:
        query = db.session.query(
            REQ_MANAGE_AGENT_CHAT_RECORD.session_id,
            REQ_MANAGE_AGENT_CHAT_RECORD.request_id,
            REQ_MANAGE_AGENT_CHAT_RECORD.role,
            REQ_MANAGE_AGENT_CHAT_RECORD.user_id,
            REQ_MANAGE_AGENT_CHAT_RECORD.user_name,
            REQ_MANAGE_AGENT_CHAT_RECORD.tool_name_str,
            REQ_MANAGE_AGENT_CHAT_RECORD.content,
            REQ_MANAGE_AGENT_CHAT_RECORD.timestamp,
        )
        if user_id:
            query = query.filter(REQ_MANAGE_AGENT_CHAT_RECORD.user_id == user_id)
        model_list = query.order_by(REQ_MANAGE_AGENT_CHAT_RECORD.timestamp.desc()).limit(200).all()
        data_list = [
            {
                "session_id": model_item.session_id,
                "request_id": model_item.request_id,
                "role": model_item.role,
                "user_id": model_item.user_id,
                "user_name": model_item.user_name,
                "tool_name_str": model_item.tool_name_str,
                "content": model_item.content,
                "timestamp": model_item.timestamp.isoformat() if model_item.timestamp else None,
            }
            for model_item in model_list
        ]
        return data_list
    except Exception as e:
        print(f"An error occurred in get_chat_record_list_by_user_id: {e}")
        return []


class ReqManageAgentPrompt(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tool_name_str: Optional[str] = None
    content: Optional[str] = None
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    reference_count: Optional[int] = None
    create_time: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


def get_prompt_list_by_search_str(search_str: str):
    """查询Prompt, 支持模糊搜索 title/content/creator_name/tool_name_str/description/"""
    try:
        query = db.session.query(REQ_MANAGE_AGENT_PROMPT)
        if search_str:
            safe_search_str = search_str.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like_search_str = f"%{safe_search_str}%"
            query = query.filter(
                or_(
                    REQ_MANAGE_AGENT_PROMPT.title.like(like_search_str, escape='\\'),
                    REQ_MANAGE_AGENT_PROMPT.description.like(like_search_str, escape='\\'),
                    REQ_MANAGE_AGENT_PROMPT.tool_name_str.like(like_search_str, escape='\\'),
                    REQ_MANAGE_AGENT_PROMPT.content.like(like_search_str, escape='\\'),
                    REQ_MANAGE_AGENT_PROMPT.creator_name.like(like_search_str, escape='\\'),
                    REQ_MANAGE_AGENT_PROMPT.creator_id.like(like_search_str, escape='\\')
                )
            )
        model_list = query.order_by(REQ_MANAGE_AGENT_PROMPT.create_time.desc()).all()
        return [ReqManageAgentPrompt.model_validate(model_item).model_dump(mode='json') for model_item in model_list]
    except Exception as e:
        print(f"An error occurred in get_prompt_list_by_search_str: {e}")
        return []


def update_single_prompt_content(prompt_dict: dict):
    """更新 Prompt（根据 title 判断是否存在），若不存在则创建新记录"""
    title = prompt_dict.get("title")
    tool_name_str = prompt_dict.get("tool_name_str")
    description = prompt_dict.get("description")
    creator_id = prompt_dict.get("creator_id")
    creator_name = prompt_dict.get("creator_name")
    content = prompt_dict.get("content", "")
    if not title or not creator_id:
        return f"缺少标题({title})或创建人({creator_id})"
    try:
        old_model = db.session.query(REQ_MANAGE_AGENT_PROMPT).filter_by(title=title).first()
        if not old_model:
            # 不存在则创建新记录
            new_prompt = REQ_MANAGE_AGENT_PROMPT(
                title=title,
                description=description,
                tool_name_str=tool_name_str,
                content=content,
                creator_id=creator_id,
                creator_name=creator_name,
                reference_count=0,
                create_time=datetime.utcnow()
            )
            db.session.add(new_prompt)
        else:
            # 存在则检查权限并更新
            if creator_id != old_model.creator_id:
                return "当前用户非创建人，无更新权限！"
            old_model.description = description
            old_model.tool_name_str = tool_name_str
            old_model.content = content
        db.session.commit()
        return ""
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred in update_single_prompt_content: {e}")
        return f"An error occurred in update_single_prompt_content: {e}"


def update_single_prompt_reference_count(prompt_dict: dict):
    """更新 Prompt(根据 title 判断是否存在）"""
    title = prompt_dict.get("title")
    if not title:
        return f"缺少标题({title})"
    try:
        old_model = db.session.query(REQ_MANAGE_AGENT_PROMPT).filter_by(title=title).first()
        if not old_model:
            return f"未找到对应的标题({title})"
        old_model.reference_count += 1
        db.session.commit()
        return ""
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred in update_single_prompt_reference_count: {e}")
        return f"An error occurred in update_single_prompt_reference_count: {e}"


def del_single_prompt(prompt_dict: dict):
    """删除 Prompt, 需验证 creator_id == creator_id"""
    title = prompt_dict.get("title")
    creator_id = prompt_dict.get("creator_id")
    if not title or not creator_id:
        return f"缺少标题({title})或创建人({creator_id})"
    try:
        old_model = db.session.query(REQ_MANAGE_AGENT_PROMPT).filter_by(title=title).first()
        if not old_model:
            return f"未找到对应的标题({title})"
        if creator_id != old_model.creator_id:
            return "当前用户非创建人，无删除权限！"
        db.session.delete(old_model)
        db.session.commit()
        return ""
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred in del_single_prompt: {e}")
        return f"An error occurred in del_single_prompt: {e}"


class ReqManageAgentMcpCfg(BaseModel):
    id: Optional[int] = None
    mcp_name: Optional[str] = None
    mcp_url: Optional[str] = None
    need_tool: Optional[str] = None
    not_need_tool: Optional[str] = None
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    create_time: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


def get_all_mcp_cfg_dict():
    try:
        model_list = db.session.query(REQ_MANAGE_AGENT_MCP_CFG).all()
        mcp_cfg_list = [ReqManageAgentMcpCfg.model_validate(model_item).model_dump() for model_item in model_list]
        return {item.get("mcp_url"):item for item in mcp_cfg_list}
    except Exception as e:
        print(f"An error occurred in get_chat_record_list_by_session_id: {e}")
        return {}
