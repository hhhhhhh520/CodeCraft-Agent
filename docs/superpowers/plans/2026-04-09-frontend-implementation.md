# CodeCraft Agent 前端界面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 CodeCraft Agent 构建 Streamlit 前端界面，支持代码生成、Agent状态展示、历史记录和设置配置。

**Architecture:** Streamlit 多页面应用，通过 Session State 管理状态，直接调用后端 Orchestrator 进行代码生成。

**Tech Stack:** Streamlit, Python, 本地 JSON 存储

---

## Task 1: 项目初始化

**Files:**
- Create: `frontend/__init__.py`
- Create: `frontend/pages/__init__.py`
- Create: `frontend/components/__init__.py`
- Create: `frontend/utils/__init__.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p frontend/pages frontend/components frontend/utils
touch frontend/__init__.py frontend/pages/__init__.py frontend/components/__init__.py frontend/utils/__init__.py
```

- [ ] **Step 2: 添加 Streamlit 依赖**

在 `requirements.txt` 末尾添加：

```
streamlit>=1.28.0
```

- [ ] **Step 3: 提交**

```bash
git add frontend/ requirements.txt
git commit -m "chore: 初始化前端项目结构"
```

---

## Task 2: 会话状态管理

**Files:**
- Create: `frontend/utils/session.py`

- [ ] **Step 1: 创建会话状态管理模块**

创建 `frontend/utils/session.py`:

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add frontend/utils/session.py
git commit -m "feat: 添加会话状态管理模块"
```

---

## Task 3: Agent状态展示组件

**Files:**
- Create: `frontend/components/agent_status.py`

- [ ] **Step 1: 创建Agent状态展示组件**

创建 `frontend/components/agent_status.py`:

```python
"""Agent状态展示组件"""

import streamlit as st
from frontend.utils.session import AgentState


# 状态配置
STATUS_CONFIG = {
    AgentState.IDLE: {"label": "等待输入", "color": "gray", "icon": "⏸️"},
    AgentState.ANALYZING: {"label": "分析需求", "color": "blue", "icon": "🔍"},
    AgentState.GENERATING: {"label": "生成代码", "color": "blue", "icon": "✨"},
    AgentState.REVIEWING: {"label": "代码审查", "color": "orange", "icon": "📋"},
    AgentState.FIXING: {"label": "修复优化", "color": "orange", "icon": "🔧"},
    AgentState.DONE: {"label": "完成", "color": "green", "icon": "✅"},
}

# 状态流转顺序
STATUS_ORDER = [
    AgentState.IDLE,
    AgentState.ANALYZING,
    AgentState.GENERATING,
    AgentState.REVIEWING,
    AgentState.FIXING,
    AgentState.DONE,
]


def render_agent_status(current_state: AgentState) -> None:
    """渲染Agent状态流程图

    Args:
        current_state: 当前状态
    """
    # 获取当前状态在流程中的位置
    current_index = STATUS_ORDER.index(current_state)

    # 构建状态流程HTML
    cols = st.columns(len(STATUS_ORDER))

    for i, state in enumerate(STATUS_ORDER):
        config = STATUS_CONFIG[state]
        is_current = state == current_state
        is_passed = i < current_index

        with cols[i]:
            if is_current:
                # 当前状态：高亮显示
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px;
                                background-color: {config['color']}20;
                                border: 2px solid {config['color']};
                                border-radius: 8px;">
                        <div style="font-size: 24px;">{config['icon']}</div>
                        <div style="font-size: 12px; font-weight: bold; color: {config['color']};">
                            {config['label']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif is_passed:
                # 已完成状态
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px;
                                background-color: #e8f5e9;
                                border-radius: 8px; opacity: 0.7;">
                        <div style="font-size: 24px;">✓</div>
                        <div style="font-size: 12px; color: gray;">
                            {config['label']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # 未到达状态
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 10px;
                                background-color: #f5f5f5;
                                border-radius: 8px; opacity: 0.5;">
                        <div style="font-size: 24px;">○</div>
                        <div style="font-size: 12px; color: gray;">
                            {config['label']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_review_score(score: int) -> None:
    """渲染审查评分

    Args:
        score: 审查评分 (0-100)
    """
    if score >= 90:
        st.success(f"✓ 代码审查通过 (评分: {score})")
    elif score >= 70:
        st.warning(f"⚠ 代码已优化 (评分: {score})")
    else:
        st.error(f"✗ 代码需要改进 (评分: {score})")
```

- [ ] **Step 2: 提交**

```bash
git add frontend/components/agent_status.py
git commit -m "feat: 添加Agent状态展示组件"
```

---

## Task 4: 代码展示组件

**Files:**
- Create: `frontend/components/code_display.py`

- [ ] **Step 1: 创建代码展示组件**

创建 `frontend/components/code_display.py`:

```python
"""代码展示组件"""

import streamlit as st
import pyperclip


def render_code_display(code: str, language: str = "python") -> None:
    """渲染代码展示区

    Args:
        code: 代码内容
        language: 代码语言
    """
    if not code:
        st.info("暂无生成的代码")
        return

    # 代码展示
    st.code(code, language=language)

    # 复制按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("📋 复制代码", key="copy_code_btn"):
            try:
                pyperclip.copy(code)
                st.toast("代码已复制到剪贴板!", icon="✅")
            except Exception:
                # 如果pyperclip不可用，使用备用方案
                st.session_state.show_copy_text = True
                st.toast("请手动复制下方文本", icon="📋")

    # 备用复制方案
    if st.session_state.get("show_copy_text", False):
        st.text_area("复制以下文本:", code, height=100, key="copy_text_area")
        if st.button("关闭", key="close_copy_btn"):
            st.session_state.show_copy_text = False
            st.rerun()


def render_code_with_issues(code: str, issues: list[str]) -> None:
    """渲染带问题列表的代码展示

    Args:
        code: 代码内容
        issues: 问题列表
    """
    if issues:
        with st.expander(f"⚠ 发现 {len(issues)} 个问题", expanded=True):
            for i, issue in enumerate(issues, 1):
                st.markdown(f"{i}. {issue}")

    render_code_display(code)
```

- [ ] **Step 2: 添加 pyperclip 依赖**

在 `requirements.txt` 末尾添加：

```
pyperclip>=1.8.0
```

- [ ] **Step 3: 提交**

```bash
git add frontend/components/code_display.py requirements.txt
git commit -m "feat: 添加代码展示组件"
```

---

## Task 5: 主入口页面

**Files:**
- Create: `frontend/app.py`

- [ ] **Step 1: 创建主入口页面**

创建 `frontend/app.py`:

```python
"""Streamlit 主入口"""

import streamlit as st
from frontend.utils.session import SessionManager

# 页面配置
st.set_page_config(
    page_title="CodeCraft Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态
SessionManager.init_session()

# 侧边栏
with st.sidebar:
    st.title("🚀 CodeCraft Agent")
    st.markdown("---")
    st.markdown("### 导航")
    st.page_link("pages/chat.py", label="💬 代码生成", icon="💬")
    st.page_link("pages/history.py", label="📜 历史记录", icon="📜")
    st.page_link("pages/settings.py", label="⚙️ 设置", icon="⚙️")
    st.markdown("---")
    st.markdown("### 快速模式")
    fast_mode = st.toggle(
        "跳过代码审查",
        value=st.session_state.config.get("fast_mode", False),
        key="fast_mode_toggle",
    )
    if fast_mode != st.session_state.config.get("fast_mode", False):
        st.session_state.config["fast_mode"] = fast_mode
        from frontend.utils.session import ConfigManager
        ConfigManager.save(st.session_state.config)

    st.markdown("---")
    st.caption("CodeCraft Agent v0.1.0")
    st.caption("多Agent协作代码生成助手")

# 主页内容
st.title("🚀 CodeCraft Agent")
st.markdown("### 多Agent协作代码生成助手")

st.markdown("""
欢迎使用 CodeCraft Agent！

**功能特点：**
- 🤖 智能代码生成
- 🔍 自动代码审查
- 🔧 问题自动修复
- 📝 历史记录管理

**开始使用：**
1. 点击左侧 **💬 代码生成** 进入对话页面
2. 输入你的代码需求
3. 等待多Agent协作完成
4. 复制生成的代码

**提示：** 在 **⚙️ 设置** 页面配置你的 API Key。
""")

# 显示当前配置状态
st.markdown("---")
if st.session_state.config.get("api_key"):
    api_type = st.session_state.config.get("api_type", "deepseek")
    st.success(f"✅ 已配置 {api_type.upper()} API")
else:
    st.warning("⚠️ 请先在设置页面配置 API Key")
```

- [ ] **Step 2: 提交**

```bash
git add frontend/app.py
git commit -m "feat: 添加主入口页面"
```

---

## Task 6: 对话页面

**Files:**
- Create: `frontend/pages/chat.py`

- [ ] **Step 1: 创建对话页面**

创建 `frontend/pages/chat.py`:

```python
"""代码生成交互页面"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.utils.session import (
    SessionManager,
    ConfigManager,
    AgentState,
    GenerationResult,
)
from frontend.components.agent_status import render_agent_status, render_review_score
from frontend.components.code_display import render_code_with_issues

# 页面配置
st.set_page_config(
    page_title="代码生成 - CodeCraft Agent",
    page_icon="💬",
)

# 初始化会话状态
SessionManager.init_session()

# 页面标题
st.title("💬 代码生成")
st.markdown("输入你的代码需求，多Agent协作生成高质量代码")

# 需求输入
requirement = st.text_area(
    "需求描述",
    placeholder="例如：实现一个快速排序算法\n或者：写一个函数计算斐波那契数列",
    height=150,
    key="requirement_input",
)

# 生成按钮
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate_btn = st.button("🚀 生成代码", type="primary", use_container_width=True)

# Agent状态展示
st.markdown("---")
st.markdown("### Agent 协作状态")
render_agent_status(st.session_state.agent_state)

# 处理生成请求
if generate_btn and requirement:
    # 检查配置
    config = st.session_state.config
    if not config.get("api_key"):
        st.error("❌ 请先在设置页面配置 API Key")
        st.stop()

    # 导入后端模块
    try:
        from backend.core import Orchestrator, SharedContext
        from backend.llm import LLMFactory
        from backend.agents import CodeGeneratorAgent, CodeReviewerAgent, DebuggerAgent
    except ImportError as e:
        st.error(f"❌ 导入后端模块失败: {e}")
        st.stop()

    # 创建LLM
    api_key = config["api_key"]
    api_type = config.get("api_type", "deepseek")

    if api_type == "deepseek":
        base_url = "https://api.deepseek.com/v1"
        model = "deepseek-chat"
    else:
        base_url = None
        model = config.get("model", "gpt-4o-mini")

    try:
        llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url)
    except Exception as e:
        st.error(f"❌ 创建LLM失败: {e}")
        st.stop()

    # 创建Agents
    generator = CodeGeneratorAgent(llm=llm, tools=[])
    agents = {"generator": generator}

    if not config.get("fast_mode", False):
        reviewer = CodeReviewerAgent(llm=llm, tools=[])
        debugger = DebuggerAgent(llm=llm, tools=[])
        agents["reviewer"] = reviewer
        agents["debugger"] = debugger

    context = SharedContext()
    orchestrator = Orchestrator(agents=agents, context=context)

    # 执行生成
    with st.spinner("正在生成代码..."):
        try:
            # 更新状态
            SessionManager.set_agent_state(AgentState.ANALYZING)
            st.rerun()

            # 调用后端
            result = orchestrator.process_request(requirement)

            # 更新状态为完成
            SessionManager.set_agent_state(AgentState.DONE)

            # 保存结果
            generation_result = GenerationResult(
                requirement=requirement,
                code=result.get("code", ""),
                review_score=result.get("review_score", 100),
                issues=result.get("issues", []),
                agent_state=AgentState.DONE,
            )
            SessionManager.set_generation_result(generation_result)

            # 添加到历史
            SessionManager.add_to_history(generation_result)

            st.rerun()

        except Exception as e:
            SessionManager.set_agent_state(AgentState.IDLE)
            st.error(f"❌ 生成失败: {e}")

# 显示生成结果
st.markdown("---")
st.markdown("### 生成结果")

result = st.session_state.generation_result
if result:
    # 显示审查评分
    if result.review_score and not st.session_state.config.get("fast_mode", False):
        render_review_score(result.review_score)

    # 显示代码
    render_code_with_issues(result.code, result.issues)
else:
    st.info("👆 输入需求并点击生成按钮开始")
```

- [ ] **Step 2: 提交**

```bash
git add frontend/pages/chat.py
git commit -m "feat: 添加代码生成对话页面"
```

---

## Task 7: 历史记录页面

**Files:**
- Create: `frontend/pages/history.py`

- [ ] **Step 1: 创建历史记录页面**

创建 `frontend/pages/history.py`:

```python
"""历史记录页面"""

import streamlit as st
from datetime import datetime
from frontend.utils.session import SessionManager, HistoryManager

# 页面配置
st.set_page_config(
    page_title="历史记录 - CodeCraft Agent",
    page_icon="📜",
)

# 初始化会话状态
SessionManager.init_session()

# 加载历史记录
if not st.session_state.history:
    st.session_state.history = HistoryManager.load()

# 页面标题
st.title("📜 历史记录")
st.markdown("查看和管理你的代码生成历史")

# 工具栏
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("🔍 搜索", placeholder="搜索需求或代码...")
with col2:
    sort_order = st.selectbox("排序", ["最新优先", "最早优先"])
with col3:
    if st.button("🗑️ 清空历史", type="secondary"):
        st.session_state.history = []
        HistoryManager.clear()
        st.success("历史记录已清空")
        st.rerun()

# 显示历史记录
st.markdown("---")

history = st.session_state.history

if not history:
    st.info("暂无历史记录，去代码生成页面生成一些代码吧！")
else:
    # 过滤和排序
    if search_query:
        history = [
            item
            for item in history
            if search_query.lower() in item.get("requirement", "").lower()
            or search_query.lower() in item.get("code", "").lower()
        ]

    if sort_order == "最早优先":
        history = list(reversed(history))

    # 显示记录
    for i, item in enumerate(history):
        timestamp = item.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = timestamp

        requirement = item.get("requirement", "")[:50]
        if len(item.get("requirement", "")) > 50:
            requirement += "..."

        score = item.get("review_score", 100)

        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{requirement}**")
                st.caption(f"📅 {time_str}")
            with col2:
                if score >= 90:
                    st.success(f"评分: {score}")
                elif score >= 70:
                    st.warning(f"评分: {score}")
                else:
                    st.error(f"评分: {score}")
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.history.pop(i)
                    HistoryManager.save(st.session_state.history)
                    st.rerun()

            # 展开查看代码
            with st.expander("查看代码"):
                st.code(item.get("code", ""), language="python")
                if item.get("issues"):
                    st.markdown("**问题列表:**")
                    for issue in item.get("issues", []):
                        st.markdown(f"- {issue}")

            st.markdown("---")
```

- [ ] **Step 2: 提交**

```bash
git add frontend/pages/history.py
git commit -m "feat: 添加历史记录页面"
```

---

## Task 8: 设置页面

**Files:**
- Create: `frontend/pages/settings.py`

- [ ] **Step 1: 创建设置页面**

创建 `frontend/pages/settings.py`:

```python
"""设置页面"""

import streamlit as st
from frontend.utils.session import SessionManager, ConfigManager

# 页面配置
st.set_page_config(
    page_title="设置 - CodeCraft Agent",
    page_icon="⚙️",
)

# 初始化会话状态
SessionManager.init_session()

# 页面标题
st.title("⚙️ 设置")
st.markdown("配置你的 API 和偏好设置")

# API 配置
st.markdown("### API 配置")

api_type = st.selectbox(
    "API 类型",
    ["deepseek", "openai"],
    index=0 if st.session_state.config.get("api_type", "deepseek") == "deepseek" else 1,
)

api_key = st.text_input(
    "API Key",
    value=st.session_state.config.get("api_key", ""),
    type="password",
    placeholder="输入你的 API Key",
)

# 模型选择
if api_type == "deepseek":
    model = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-coder"],
        index=0 if st.session_state.config.get("model", "deepseek-chat") == "deepseek-chat" else 1,
    )
else:
    model = st.selectbox(
        "模型",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0,
    )

# 快速模式
st.markdown("### 生成设置")
fast_mode = st.toggle(
    "快速模式（跳过代码审查）",
    value=st.session_state.config.get("fast_mode", False),
)

# 保存按钮
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("💾 保存配置", type="primary"):
        st.session_state.config = {
            "api_key": api_key,
            "api_type": api_type,
            "model": model,
            "fast_mode": fast_mode,
        }
        ConfigManager.save(st.session_state.config)
        st.success("✅ 配置已保存")

# 显示当前配置状态
st.markdown("---")
st.markdown("### 当前配置状态")

if st.session_state.config.get("api_key"):
    st.success(f"✅ 已配置 {st.session_state.config.get('api_type', 'deepseek').upper()} API")
    st.info(f"模型: {st.session_state.config.get('model', 'deepseek-chat')}")
else:
    st.warning("⚠️ 尚未配置 API Key")

# 帮助信息
st.markdown("---")
st.markdown("### 帮助信息")
st.markdown("""
**获取 API Key:**
- DeepSeek: https://platform.deepseek.com/
- OpenAI: https://platform.openai.com/

**配置文件位置:**
- `~/.codecraft/config.json`
- `~/.codecraft/history.json`
""")
```

- [ ] **Step 2: 提交**

```bash
git add frontend/pages/settings.py
git commit -m "feat: 添加设置页面"
```

---

## Task 9: 验证与启动脚本

**Files:**
- Create: `run_web.bat`
- Create: `run_web.sh`

- [ ] **Step 1: 创建 Windows 启动脚本**

创建 `run_web.bat`:

```batch
@echo off
chcp 65001 >nul
echo Starting CodeCraft Agent Web UI...
streamlit run frontend/app.py --server.port 8501
```

- [ ] **Step 2: 创建 Linux/Mac 启动脚本**

创建 `run_web.sh`:

```bash
#!/bin/bash
echo "Starting CodeCraft Agent Web UI..."
streamlit run frontend/app.py --server.port 8501
```

- [ ] **Step 3: 安装依赖并验证**

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

预期：浏览器自动打开 http://localhost:8501，显示 CodeCraft Agent 主页

- [ ] **Step 4: 提交**

```bash
git add run_web.bat run_web.sh
git commit -m "feat: 添加Web界面启动脚本"
```

---

## 实现完成检查清单

- [ ] 所有文件创建完成
- [ ] 依赖安装成功
- [ ] 启动脚本可运行
- [ ] 主页显示正常
- [ ] 代码生成功能正常
- [ ] 历史记录功能正常
- [ ] 设置保存功能正常