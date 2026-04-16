"""会话状态管理模块"""

import os
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
    TESTING = "testing"
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
    # API Key存储标识（实际key存储在系统密钥环）
    KEYRING_SERVICE = "codecraft-agent"
    KEYRING_KEY = "api_key"

    @classmethod
    def _set_secure_permissions(cls, path: Path) -> None:
        """设置安全文件权限（仅所有者可读写）"""
        if os.name == 'posix':
            import stat
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    @classmethod
    def _get_keyring(cls) -> Optional[Any]:
        """获取密钥环（如果可用）"""
        try:
            import keyring
            return keyring
        except ImportError:
            return None

    @classmethod
    def load(cls) -> dict:
        """加载配置

        API Key从系统密钥环加载（如果可用），否则从配置文件读取。
        """
        config = {
            "api_key": "",
            "api_type": "deepseek",
            "model": "deepseek-chat",
            "fast_mode": False,
        }

        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)

        # 处理加密存储的key
        file_api_key = config.get("api_key", "")
        if file_api_key.startswith("enc:"):
            config["api_key"] = cls._decrypt_key(file_api_key)
        elif file_api_key == "***STORED_IN_KEYRING***":
            config["api_key"] = ""

        # 尝试从密钥环获取API Key
        keyring = cls._get_keyring()
        if keyring:
            try:
                stored_key = keyring.get_password(cls.KEYRING_SERVICE, cls.KEYRING_KEY)
                if stored_key:
                    config["api_key"] = stored_key
            except Exception:
                pass  # 密钥环不可用，使用文件中的key

        return config

    @classmethod
    def save(cls, config: dict) -> None:
        """保存配置

        API Key存储到系统密钥环（如果可用），配置文件中存储占位符。
        """
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 设置目录权限
        if os.name == 'posix':
            import stat
            os.chmod(cls.CONFIG_DIR, stat.S_IRWXU)

        # 分离敏感信息
        config_to_save = config.copy()
        api_key = config_to_save.pop("api_key", "")

        # 尝试存储到密钥环
        keyring = cls._get_keyring()
        keyring_available = False
        if keyring and api_key:
            try:
                keyring.set_password(cls.KEYRING_SERVICE, cls.KEYRING_KEY, api_key)
                config_to_save["api_key"] = "***STORED_IN_KEYRING***"
                keyring_available = True
            except Exception:
                keyring_available = False

        # 如果密钥环不可用，加密存储到文件
        if not keyring_available and api_key:
            config_to_save["api_key"] = cls._encrypt_key(api_key)

        with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_to_save, f, ensure_ascii=False, indent=2)

        cls._set_secure_permissions(cls.CONFIG_FILE)

    @classmethod
    def _encrypt_key(cls, key: str) -> str:
        """简单混淆API Key（非加密，仅防止明文显示）

        注意：这不是真正的加密，建议安装keyring库使用系统密钥环。
        """
        import base64
        # 简单base64编码，仅防止明文显示
        return f"enc:{base64.b64encode(key.encode()).decode()}"

    @classmethod
    def _decrypt_key(cls, encrypted: str) -> str:
        """解密API Key"""
        if encrypted.startswith("enc:"):
            import base64
            try:
                return base64.b64decode(encrypted[4:].encode()).decode()
            except Exception:
                return ""
        return encrypted


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
