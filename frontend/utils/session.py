"""会话状态管理模块"""

import streamlit as st
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    FIXING = "fixing"
    DONE = "done"


@dataclass
class GenerationResult:
    """生成结果"""
    requirement: str
    code: str
    review_score: int
    issues: list[str]
    agent_state: AgentState
    error: Optional[str] = None


class SessionManager:
    """会话状态管理器"""

    @staticmethod
    def init_session() -> None:
        """初始化会话状态"""
        if "agent_state" not in st.session_state:
            st.session_state.agent_state = AgentState.IDLE
        if "generation_result" not in st.session_state:
            st.session_state.generation_result = None
        if "history" not in st.session_state:
            st.session_state.history = []
        if "config" not in st.session_state:
            st.session_state.config = ConfigManager.load()

    @staticmethod
    def set_agent_state(state: AgentState) -> None:
        """设置Agent状态"""
        st.session_state.agent_state = state

    @staticmethod
    def get_agent_state() -> AgentState:
        """获取Agent状态"""
        return st.session_state.agent_state

    @staticmethod
    def set_generation_result(result: GenerationResult) -> None:
        """设置生成结果"""
        st.session_state.generation_result = result

    @staticmethod
    def get_generation_result() -> Optional[GenerationResult]:
        """获取生成结果"""
        return st.session_state.generation_result

    @staticmethod
    def add_to_history(result: GenerationResult) -> None:
        """添加到历史记录"""
        from datetime import datetime
        history_item = {
            "timestamp": datetime.now().isoformat(),
            "requirement": result.requirement,
            "code": result.code,
            "review_score": result.review_score,
            "issues": result.issues,
        }
        st.session_state.history.insert(0, history_item)
        HistoryManager.save(st.session_state.history)


class ConfigManager:
    """配置管理器"""

    CONFIG_DIR = Path.home() / ".codecraft"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    @classmethod
    def load(cls) -> dict:
        """加载配置"""
        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "api_key": "",
            "api_type": "deepseek",
            "model": "deepseek-chat",
            "fast_mode": False,
        }

    @classmethod
    def save(cls, config: dict) -> None:
        """保存配置"""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


class HistoryManager:
    """历史记录管理器"""

    HISTORY_DIR = Path.home() / ".codecraft"
    HISTORY_FILE = HISTORY_DIR / "history.json"

    @classmethod
    def load(cls) -> list:
        """加载历史记录"""
        if cls.HISTORY_FILE.exists():
            with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    @classmethod
    def save(cls, history: list) -> None:
        """保存历史记录"""
        cls.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    @classmethod
    def clear(cls) -> None:
        """清空历史记录"""
        if cls.HISTORY_FILE.exists():
            cls.HISTORY_FILE.unlink()
