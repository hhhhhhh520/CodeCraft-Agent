"""历史记录页面"""

import streamlit as st
from datetime import datetime
from frontend.utils.session import SessionManager, HistoryManager

# 页面配置
st.set_page_config(
    page_title="历史记录 - CodeCraft Agent",
    page_icon=":scroll:",
)

# 初始化会话状态
SessionManager.init_session()

# 加载历史记录
if not st.session_state.history:
    st.session_state.history = HistoryManager.load()

# 页面标题
st.title(":scroll: 历史记录")
st.markdown("查看和管理你的代码生成历史")

# 工具栏
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input(":mag: 搜索", placeholder="搜索需求或代码...")
with col2:
    sort_order = st.selectbox("排序", ["最新优先", "最早优先"])
with col3:
    if st.button(":wastebasket: 清空历史", type="secondary"):
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
                st.caption(f":calendar: {time_str}")
            with col2:
                if score >= 90:
                    st.success(f"评分: {score}")
                elif score >= 70:
                    st.warning(f"评分: {score}")
                else:
                    st.error(f"评分: {score}")
            with col3:
                if st.button(":wastebasket:", key=f"delete_{i}"):
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
