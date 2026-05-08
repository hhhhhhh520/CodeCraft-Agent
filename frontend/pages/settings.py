"""设置页面 - CodeCraft Agent 深色科技主题"""

import streamlit as st
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.styles.theme import apply_global_styles, THEME_COLORS
from frontend.components.ui_components import (
    render_hero_section,
    render_config_status,
)
from frontend.utils.session import SessionManager, ConfigManager

# 页面配置
st.set_page_config(
    page_title="设置 - CodeCraft Agent",
    page_icon="⚙️",
    layout="wide",
)

# 应用全局样式
apply_global_styles()

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
render_hero_section(
    title="设置",
    subtitle="配置你的 API 和偏好设置",
    description=""
)

# 检查secrets配置
secrets_config = get_secrets_config()
if secrets_config and secrets_config.get("api_key"):
    st.markdown(f"""
    <div style="
        background: rgba(67, 97, 238, 0.1);
        border: 1px solid rgba(67, 97, 238, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <span style="color: {THEME_COLORS['accent_blue']};">🔐</span>
        <span style="color: {THEME_COLORS['text_secondary']};">检测到云端配置，API Key 已通过 Secrets 配置</span>
    </div>
    """, unsafe_allow_html=True)
    if not st.session_state.config.get("api_key"):
        st.session_state.config.update(secrets_config)

# ===== API 配置 =====
st.markdown("### API 配置")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    api_type = st.selectbox(
        "API 类型",
        ["deepseek", "openai"],
        index=0 if st.session_state.config.get("api_type", "deepseek") == "deepseek" else 1,
    )

with col2:
    api_key = st.text_input(
        "API Key",
        value=st.session_state.config.get("api_key", ""),
        type="password",
        placeholder="输入你的 API Key",
        max_chars=200,
    )

# 模型选择
st.markdown("<br>", unsafe_allow_html=True)

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

# ===== 生成设置 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 生成设置")
st.markdown("<br>", unsafe_allow_html=True)

fast_mode = st.toggle(
    "快速模式（跳过代码审查）",
    value=st.session_state.config.get("fast_mode", False),
)

# 快速模式说明
st.markdown(f"""
<div style="
    background: {THEME_COLORS['bg_tertiary']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 8px;
    padding: 1rem;
    margin-top: 0.5rem;
">
    <p style="color: {THEME_COLORS['text_muted']}; font-size: 0.85rem; margin: 0;">
        💡 启用快速模式后，代码将直接生成，跳过审查、修复和测试环节。<br>
        适合快速原型开发，但不建议用于生产环境代码。
    </p>
</div>
""", unsafe_allow_html=True)

# ===== 保存按钮 =====
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("💾 保存配置", type="primary", use_container_width=True):
        # 输入验证
        if api_key:
            from backend.utils.input_validator import validate_api_key
            is_valid, cleaned_key, error_msg = validate_api_key(api_key)
            if not is_valid:
                st.error(f"❌ API Key验证失败: {error_msg}")
                st.stop()
            api_key_to_save = cleaned_key
        else:
            api_key_to_save = ""

        st.session_state.config = {
            "api_key": api_key_to_save,
            "api_type": api_type,
            "model": model,
            "fast_mode": fast_mode,
        }
        ConfigManager.save(st.session_state.config)
        st.success("✅ 配置已保存")

# ===== 当前配置状态 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 当前配置状态")
st.markdown("<br>", unsafe_allow_html=True)

render_config_status(
    is_configured=bool(st.session_state.config.get("api_key")),
    api_type=st.session_state.config.get("api_type", "deepseek")
)

if st.session_state.config.get("api_key"):
    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    ">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
            <span style="color: {THEME_COLORS['text_muted']};">API 类型</span>
            <span style="font-family: 'JetBrains Mono', monospace; color: {THEME_COLORS['text_primary']};">
                {st.session_state.config.get('api_type', 'deepseek').upper()}
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
            <span style="color: {THEME_COLORS['text_muted']};">模型</span>
            <span style="font-family: 'JetBrains Mono', monospace; color: {THEME_COLORS['text_primary']};">
                {st.session_state.config.get('model', 'deepseek-chat')}
            </span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: {THEME_COLORS['text_muted']};">快速模式</span>
            <span style="color: {THEME_COLORS['success'] if st.session_state.config.get('fast_mode') else THEME_COLORS['text_muted']};">
                {'已启用' if st.session_state.config.get('fast_mode') else '已禁用'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== 帮助信息 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 帮助信息")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    ">
        <h4 style="color: {THEME_COLORS['accent_cyan']}; margin-bottom: 1rem;">获取 API Key</h4>
        <div style="margin-bottom: 0.75rem;">
            <span style="color: {THEME_COLORS['text_muted']};">DeepSeek</span><br>
            <a href="https://platform.deepseek.com/" target="_blank" style="color: {THEME_COLORS['accent_cyan']};">
                platform.deepseek.com
            </a>
        </div>
        <div>
            <span style="color: {THEME_COLORS['text_muted']};">OpenAI</span><br>
            <a href="https://platform.openai.com/" target="_blank" style="color: {THEME_COLORS['accent_cyan']};">
                platform.openai.com
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    ">
        <h4 style="color: {THEME_COLORS['accent_magenta']}; margin-bottom: 1rem;">配置文件位置</h4>
        <div style="margin-bottom: 0.75rem;">
            <span style="color: {THEME_COLORS['text_muted']};">配置文件</span><br>
            <code style="color: {THEME_COLORS['text_primary']}; background: rgba(0,0,0,0.3); padding: 0.2rem 0.5rem; border-radius: 4px;">
                ~/.codecraft/config.json
            </code>
        </div>
        <div>
            <span style="color: {THEME_COLORS['text_muted']};">历史记录</span><br>
            <code style="color: {THEME_COLORS['text_primary']}; background: rgba(0,0,0,0.3); padding: 0.2rem 0.5rem; border-radius: 4px;">
                ~/.codecraft/history.json
            </code>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== 安全提示 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="
    background: rgba(247, 37, 133, 0.1);
    border: 1px solid rgba(247, 37, 133, 0.3);
    border-radius: 8px;
    padding: 1rem;
">
    <span style="color: {THEME_COLORS['accent_magenta']};">🔒</span>
    <span style="color: {THEME_COLORS['text_secondary']};">
        API Key 将安全存储在系统密钥环中（如果可用），或加密存储在本地配置文件中。
    </span>
</div>
""", unsafe_allow_html=True)