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

# 尝试从Streamlit secrets读取配置
def get_secrets_config():
    """从Streamlit Cloud secrets读取配置"""
    try:
        if hasattr(st, 'secrets'):
            return {
                "api_key": st.secrets.get("DEEPSEEK_API_KEY", ""),
                "api_type": st.secrets.get("DEFAULT_API_TYPE", "deepseek"),
            }
    except Exception:
        pass
    return None

# 页面标题
st.title("⚙️ 设置")
st.markdown("配置你的 API 和偏好设置")

# 检查secrets配置
secrets_config = get_secrets_config()
if secrets_config and secrets_config.get("api_key"):
    st.info("🔐 检测到云端配置，API Key 已通过 Secrets 配置")
    if not st.session_state.config.get("api_key"):
        st.session_state.config.update(secrets_config)

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
