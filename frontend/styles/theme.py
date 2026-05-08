"""全局样式配置 - CodeCraft Agent 深色科技主题"""

import streamlit as st
from pathlib import Path

# 主题色彩配置
THEME_COLORS = {
    "bg_primary": "#0a0e17",      # 深蓝黑
    "bg_secondary": "#111827",    # 次级背景
    "bg_tertiary": "#1a2234",     # 卡片背景
    "accent_cyan": "#00f5d4",     # 青色强调
    "accent_magenta": "#f72585",  # 品红强调
    "accent_gold": "#ffd60a",     # 金色强调
    "accent_blue": "#4361ee",     # 蓝色
    "text_primary": "#e2e8f0",    # 主文字
    "text_secondary": "#94a3b8",  # 次级文字
    "text_muted": "#64748b",      # 弱化文字
    "border": "#2d3748",          # 边框
    "success": "#10b981",         # 成功
    "warning": "#f59e0b",         # 警告
    "error": "#ef4444",           # 错误
}

# Agent 配色
AGENT_COLORS = {
    "Generator": {"color": "#00f5d4", "icon": "✨", "label": "代码生成"},
    "Reviewer": {"color": "#f72585", "icon": "🔍", "label": "代码审查"},
    "Debugger": {"color": "#ffd60a", "icon": "🔧", "label": "问题修复"},
    "TestGenerator": {"color": "#4361ee", "icon": "🧪", "label": "测试生成"},
}


def apply_global_styles():
    """应用全局CSS样式"""

    st.markdown(f"""
    <style>
    /* ===== 导入字体 ===== */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    /* ===== CSS变量 ===== */
    :root {{
        --bg-primary: {THEME_COLORS['bg_primary']};
        --bg-secondary: {THEME_COLORS['bg_secondary']};
        --bg-tertiary: {THEME_COLORS['bg_tertiary']};
        --accent-cyan: {THEME_COLORS['accent_cyan']};
        --accent-magenta: {THEME_COLORS['accent_magenta']};
        --accent-gold: {THEME_COLORS['accent_gold']};
        --accent-blue: {THEME_COLORS['accent_blue']};
        --text-primary: {THEME_COLORS['text_primary']};
        --text-secondary: {THEME_COLORS['text_secondary']};
        --text-muted: {THEME_COLORS['text_muted']};
        --border: {THEME_COLORS['border']};
        --font-display: 'Space Grotesk', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }}

    /* ===== 全局背景 ===== */
    .stApp {{
        background: var(--bg-primary);
        background-image:
            linear-gradient(rgba(0, 245, 212, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 245, 212, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
    }}

    /* 扫描线效果 */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 245, 212, 0.01) 2px,
            rgba(0, 245, 212, 0.01) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }}

    /* ===== 标题样式 ===== */
    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font-display) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    h1 {{
        font-size: 2.5rem !important;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-magenta));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    /* ===== 文字样式 ===== */
    p, span, div, label {{
        font-family: var(--font-display) !important;
        color: var(--text-secondary) !important;
    }}

    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }}

    [data-testid="stSidebar"] .element-container {{
        margin: 0.5rem 0;
    }}

    /* 侧边栏标题 */
    [data-testid="stSidebar"] h1 {{
        font-size: 1.5rem !important;
        -webkit-text-fill-color: var(--accent-cyan) !important;
        text-align: center;
        padding: 1rem 0;
    }}

    /* ===== 按钮样式 ===== */
    .stButton > button {{
        font-family: var(--font-display) !important;
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: var(--bg-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 245, 212, 0.3) !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 245, 212, 0.4) !important;
    }}

    .stButton > button:active {{
        transform: translateY(0) !important;
    }}

    /* 次要按钮 */
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        box-shadow: none !important;
    }}

    .stButton > button[kind="secondary"]:hover {{
        border-color: var(--accent-cyan) !important;
        color: var(--accent-cyan) !important;
    }}

    /* ===== 输入框 ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        font-family: var(--font-mono) !important;
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 3px rgba(0, 245, 212, 0.1) !important;
    }}

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {{
        color: var(--text-muted) !important;
    }}

    /* ===== 选择框 ===== */
    .stSelectbox > div > div {{
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }}

    .stSelectbox > div > div > div {{
        color: var(--text-primary) !important;
        font-family: var(--font-display) !important;
    }}

    /* ===== 代码块 ===== */
    .stCodeBlock {{
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}

    .stCodeBlock pre {{
        font-family: var(--font-mono) !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
    }}

    code {{
        font-family: var(--font-mono) !important;
        background: rgba(0, 245, 212, 0.1) !important;
        color: var(--accent-cyan) !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 4px !important;
    }}

    pre code {{
        background: transparent !important;
        color: var(--text-primary) !important;
        padding: 0 !important;
    }}

    /* ===== 消息提示 ===== */
    .stSuccess {{
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 8px !important;
        color: #10b981 !important;
    }}

    .stWarning {{
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 8px !important;
        color: #f59e0b !important;
    }}

    .stError {{
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 8px !important;
        color: #ef4444 !important;
    }}

    .stInfo {{
        background: rgba(67, 97, 238, 0.1) !important;
        border: 1px solid rgba(67, 97, 238, 0.3) !important;
        border-radius: 8px !important;
        color: #4361ee !important;
    }}

    /* ===== 展开/折叠 ===== */
    .streamlit-expanderHeader {{
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: var(--font-display) !important;
    }}

    /* ===== 进度条 ===== */
    .stProgress > div > div {{
        background: var(--bg-tertiary) !important;
        border-radius: 10px !important;
    }}

    .stProgress > div > div > div {{
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-magenta)) !important;
        border-radius: 10px !important;
    }}

    /* ===== Toggle 开关 ===== */
    .stToggle > div {{
        background: var(--bg-tertiary) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }}

    /* ===== 分隔线 ===== */
    hr {{
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border), transparent) !important;
        margin: 2rem 0 !important;
    }}

    /* ===== 页面链接 ===== */
    .stPageLink {{
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem 0 !important;
        transition: all 0.3s ease !important;
    }}

    .stPageLink:hover {{
        border-color: var(--accent-cyan) !important;
        background: rgba(0, 245, 212, 0.05) !important;
    }}

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--bg-secondary);
    }}

    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-muted);
    }}

    /* ===== 动画 ===== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}

    @keyframes glow {{
        0%, 100% {{ box-shadow: 0 0 5px var(--accent-cyan); }}
        50% {{ box-shadow: 0 0 20px var(--accent-cyan), 0 0 30px var(--accent-cyan); }}
    }}

    @keyframes slideIn {{
        from {{ transform: translateX(-20px); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}

    @keyframes typing {{
        from {{ width: 0; }}
        to {{ width: 100%; }}
    }}

    .fade-in {{
        animation: fadeIn 0.5s ease forwards;
    }}

    .pulse {{
        animation: pulse 2s ease-in-out infinite;
    }}

    .glow {{
        animation: glow 2s ease-in-out infinite;
    }}

    /* ===== 响应式 ===== */
    @media (max-width: 768px) {{
        h1 {{
            font-size: 1.8rem !important;
        }}

        .stButton > button {{
            width: 100% !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


def get_agent_color(agent_name: str) -> dict:
    """获取Agent配色"""
    return AGENT_COLORS.get(agent_name, {"color": "#64748b", "icon": "⬡", "label": agent_name})
