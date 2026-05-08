"""历史记录页面 - CodeCraft Agent 深色科技主题"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.styles.theme import apply_global_styles, THEME_COLORS
from frontend.components.ui_components import (
    render_hero_section,
    render_history_card,
    render_code_block,
    render_empty_state,
)
from frontend.utils.session import SessionManager, HistoryManager

# 页面配置
st.set_page_config(
    page_title="历史记录 - CodeCraft Agent",
    page_icon="📜",
    layout="wide",
)

# 应用全局样式
apply_global_styles()

# 初始化会话状态
SessionManager.init_session()

# 加载历史记录
if not st.session_state.history:
    st.session_state.history = HistoryManager.load()

# 页面标题
render_hero_section(
    title="历史记录",
    subtitle="查看和管理你的代码生成历史",
    description=""
)

# ===== 工具栏 =====
st.markdown("### 管理工具")

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    search_query = st.text_input(
        "搜索",
        placeholder="搜索需求或代码...",
        key="search_input",
        label_visibility="collapsed",
    )

with col2:
    sort_order = st.selectbox(
        "排序",
        ["最新优先", "最早优先"],
        key="sort_select",
        label_visibility="collapsed",
    )

with col3:
    if st.button("🗑️ 清空历史", use_container_width=True):
        st.session_state.history = []
        HistoryManager.clear()
        st.success("历史记录已清空")
        st.rerun()

with col4:
    # 统计数量
    count = len(st.session_state.history)
    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 8px;
        padding: 0.5rem 1rem;
        text-align: center;
    ">
        <span style="font-family: 'JetBrains Mono', monospace; color: {THEME_COLORS['accent_cyan']}; font-weight: 600;">
            {count}
        </span>
        <span style="color: {THEME_COLORS['text_muted']}; font-size: 0.85rem;">条记录</span>
    </div>
    """, unsafe_allow_html=True)

# ===== 显示历史记录 =====
st.markdown("<br>", unsafe_allow_html=True)

history = st.session_state.history

if not history:
    render_empty_state(
        icon="📜",
        title="暂无历史记录",
        description="去代码生成页面生成一些代码吧！"
    )
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

    if not history and search_query:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 2rem;
            color: {THEME_COLORS['text_muted']};
        ">
            未找到匹配 "{search_query}" 的记录
        </div>
        """, unsafe_allow_html=True)
    else:
        # 显示记录列表
        for i, item in enumerate(history):
            timestamp = item.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = timestamp

            requirement = item.get("requirement", "")
            score = item.get("review_score", 100)

            # 卡片容器
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    render_history_card(requirement, time_str, score, i)

                with col2:
                    if st.button("🗑️", key=f"delete_{i}", help="删除此记录"):
                        st.session_state.history.pop(i)
                        HistoryManager.save(st.session_state.history)
                        st.rerun()

                # 展开查看代码
                with st.expander("查看代码", expanded=False):
                    render_code_block(
                        item.get("code", ""),
                        title="generated_code.py"
                    )

                    if item.get("issues"):
                        st.markdown(f"""
                        <div style="
                            background: rgba(247, 37, 133, 0.1);
                            border: 1px solid rgba(247, 37, 133, 0.3);
                            border-radius: 8px;
                            padding: 1rem;
                            margin-top: 1rem;
                        ">
                            <div style="color: {THEME_COLORS['accent_magenta']}; font-weight: 600; margin-bottom: 0.5rem;">
                                ⚠ 发现的问题
                            </div>
                            <ul style="color: {THEME_COLORS['text_secondary']}; margin: 0; padding-left: 1.5rem;">
                                {"".join(f"<li>{issue}</li>" for issue in item.get("issues", []))}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)

                    if item.get("test_code"):
                        st.markdown("<br>", unsafe_allow_html=True)
                        render_code_block(item.get("test_code", ""), title="test_generated.py")

                st.markdown("---")