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
