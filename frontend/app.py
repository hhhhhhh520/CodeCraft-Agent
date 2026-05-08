"""Streamlit 主入口 - CodeCraft Agent 深色科技主题"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.styles.theme import apply_global_styles
from frontend.components.ui_components import (
    render_hero_section,
    render_feature_card,
    render_stat_card,
    render_config_status,
)
from frontend.utils.session import SessionManager

# 页面配置
st.set_page_config(
    page_title="CodeCraft Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 应用全局样式
apply_global_styles()

# 初始化会话状态
SessionManager.init_session()

# ===== 侧边栏 =====
with st.sidebar:
    # Logo区域
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚡</div>
        <h1 style="font-size: 1.25rem; margin: 0;">CodeCraft</h1>
        <p style="font-size: 0.8rem; color: #64748b; margin: 0.25rem 0 0 0;">Agent</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 导航
    st.markdown("### 导航")
    st.page_link("pages/chat.py", label="代码生成", icon="💬")
    st.page_link("pages/history.py", label="历史记录", icon="📜")
    st.page_link("pages/settings.py", label="设置", icon="⚙️")

    st.markdown("---")

    # 快速模式
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

    # 配置状态
    render_config_status(
        is_configured=bool(st.session_state.config.get("api_key")),
        api_type=st.session_state.config.get("api_type", "deepseek")
    )

    st.markdown("---")

    # 版本信息
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <p style="font-size: 0.75rem; color: #64748b; margin: 0;">v0.2.0</p>
        <p style="font-size: 0.7rem; color: #475569; margin: 0.25rem 0 0 0;">多Agent协作代码生成</p>
    </div>
    """, unsafe_allow_html=True)

# ===== 主页内容 =====

# Hero区域
render_hero_section(
    title="CodeCraft Agent",
    subtitle="多Agent协作的智能代码生成助手",
    description="生成 → 审查 → 修复 → 测试，完整闭环"
)

# 功能特性
st.markdown("## 核心特性")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_feature_card(
        icon="🤖",
        title="智能生成",
        description="根据自然语言需求生成符合PEP 8规范的Python代码",
        color="#00f5d4"
    )

with col2:
    render_feature_card(
        icon="🔍",
        title="代码审查",
        description="多维度审查：规范、Bug、性能、安全、可维护性",
        color="#f72585"
    )

with col3:
    render_feature_card(
        icon="🔧",
        title="自动修复",
        description="分析审查结果，智能修复代码问题，最多3次迭代",
        color="#ffd60a"
    )

with col4:
    render_feature_card(
        icon="🧪",
        title="测试生成",
        description="自动生成pytest测试用例，确保代码质量",
        color="#4361ee"
    )

st.markdown("<br>", unsafe_allow_html=True)

# 统计数据
st.markdown("## 项目指标")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_stat_card(value="67", label="测试用例", color="#00f5d4")

with col2:
    render_stat_card(value="81%", label="覆盖率", color="#f72585")

with col3:
    render_stat_card(value="4", label="专业Agent", color="#ffd60a")

with col4:
    render_stat_card(value="∞", label="可能", color="#4361ee")

st.markdown("<br>", unsafe_allow_html=True)

# 使用指南
st.markdown("## 快速开始")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background: #1a2234;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    ">
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            color: #00f5d4;
            margin-bottom: 1rem;
        ">01</div>
        <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">配置 API</h4>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
            在设置页面配置你的 API Key，支持 DeepSeek、OpenAI 等多种模型
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background: #1a2234;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    ">
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            color: #f72585;
            margin-bottom: 1rem;
        ">02</div>
        <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">输入需求</h4>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
            用自然语言描述你的代码需求，例如"实现一个快速排序算法"
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background: #1a2234;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    ">
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            color: #ffd60a;
            margin-bottom: 1rem;
        ">03</div>
        <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">获取代码</h4>
        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
            等待多Agent协作完成，获取经过审查、修复、测试的高质量代码
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# 架构说明
with st.expander("📊 查看系统架构"):
    st.markdown("""
    ### 多Agent协作架构

    ```
    ┌─────────────────────────────────────────────────────────┐
    │                      用户请求                            │
    └─────────────────────────┬───────────────────────────────┘
                              ▼
    ┌─────────────────────────────────────────────────────────┐
    │                   Orchestrator                          │
    │              (任务分析、分发、协调)                       │
    └─────────────────────────┬───────────────────────────────┘
                              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Generator│───▶│Reviewer │───▶│Debugger │───▶│  Test   │
    │ 代码生成 │    │ 代码审查 │    │ 问题修复 │    │ 测试生成 │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   SharedContext │
                    │   (共享上下文)   │
                    └─────────────────┘
    ```

    **核心特性：**
    - **状态机管理**: 8状态有限状态机，确保任务流转可控
    - **反馈闭环**: 审查不通过自动修复，最多3次迭代
    - **多模型支持**: OpenAI / Claude / DeepSeek 可切换
    - **向量记忆**: ChromaDB语义检索历史代码
    """)
