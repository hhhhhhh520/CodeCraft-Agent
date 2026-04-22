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
    AgentState.TESTING: {"label": "生成测试", "color": "purple", "icon": "🧪"},
    AgentState.DONE: {"label": "完成", "color": "green", "icon": "✅"},
}

# 状态流转顺序（包含测试阶段）
STATUS_ORDER = [
    AgentState.IDLE,
    AgentState.ANALYZING,
    AgentState.GENERATING,
    AgentState.REVIEWING,
    AgentState.FIXING,
    AgentState.TESTING,
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
