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
