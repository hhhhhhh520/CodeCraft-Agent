"""自定义UI组件库 - CodeCraft Agent"""

import streamlit as st
from frontend.styles.theme import THEME_COLORS, AGENT_COLORS, get_agent_color
from typing import Optional
import time


def render_hero_section(title: str, subtitle: str, description: str = ""):
    """渲染Hero区域 - 带动画的主标题区"""

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem 1rem;
        margin-bottom: 2rem;
        background: linear-gradient(180deg, rgba(0, 245, 212, 0.05) 0%, transparent 100%);
        border-radius: 20px;
        position: relative;
        overflow: hidden;
    ">
        <!-- 装饰性背景元素 -->
        <div style="
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 30%, rgba(0, 245, 212, 0.03) 0%, transparent 50%),
                        radial-gradient(circle at 70% 70%, rgba(247, 37, 133, 0.03) 0%, transparent 50%);
            animation: rotate 30s linear infinite;
        "></div>

        <!-- 主标题 -->
        <h1 style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, {THEME_COLORS['accent_cyan']}, {THEME_COLORS['accent_magenta']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
        ">{title}</h1>

        <!-- 副标题 -->
        <p style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.25rem;
            color: {THEME_COLORS['text_secondary']};
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        ">{subtitle}</p>

        <!-- 描述文字 -->
        {f'<p style="font-size: 0.95rem; color: {THEME_COLORS["text_muted"]}; position: relative; z-index: 1;">{description}</p>' if description else ''}

        <!-- 装饰线 -->
        <div style="
            width: 100px;
            height: 3px;
            background: linear-gradient(90deg, {THEME_COLORS['accent_cyan']}, {THEME_COLORS['accent_magenta']});
            margin: 1.5rem auto 0;
            border-radius: 2px;
        "></div>
    </div>

    <style>
    @keyframes rotate {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_feature_card(icon: str, title: str, description: str, color: str = None):
    """渲染功能卡片"""

    if color is None:
        color = THEME_COLORS['accent_cyan']

    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    " onmouseover="this.style.borderColor='{color}'; this.style.transform='translateY(-4px)';"
       onmouseout="this.style.borderColor='{THEME_COLORS['border']}'; this.style.transform='translateY(0)';">

        <!-- 顶部装饰线 -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, {color}, transparent);
        "></div>

        <!-- 图标 -->
        <div style="
            font-size: 2.5rem;
            margin-bottom: 1rem;
        ">{icon}</div>

        <!-- 标题 -->
        <h3 style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: {THEME_COLORS['text_primary']};
            margin-bottom: 0.5rem;
        ">{title}</h3>

        <!-- 描述 -->
        <p style="
            font-size: 0.9rem;
            color: {THEME_COLORS['text_secondary']};
            line-height: 1.5;
            margin: 0;
        ">{description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_stat_card(value: str, label: str, color: str = None):
    """渲染统计卡片"""

    if color is None:
        color = THEME_COLORS['accent_cyan']

    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    " onmouseover="this.style.borderColor='{color}';"
       onmouseout="this.style.borderColor='{THEME_COLORS['border']}';">

        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 2rem;
            font-weight: 700;
            color: {color};
            margin-bottom: 0.25rem;
        ">{value}</div>

        <div style="
            font-size: 0.85rem;
            color: {THEME_COLORS['text_muted']};
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_agent_pipeline(current_agent: str = None, completed_agents: list = None):
    """渲染Agent协作流水线"""

    if completed_agents is None:
        completed_agents = []

    agents = ["Generator", "Reviewer", "Debugger", "TestGenerator"]

    html = """
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 1.5rem;
        background: {bg_tertiary};
        border-radius: 16px;
        border: 1px solid {border};
        margin: 1rem 0;
        flex-wrap: wrap;
    ">
    """.format(
        bg_tertiary=THEME_COLORS['bg_tertiary'],
        border=THEME_COLORS['border']
    )

    for i, agent in enumerate(agents):
        config = get_agent_color(agent)
        is_completed = agent in completed_agents
        is_current = agent == current_agent

        # 状态样式
        if is_completed:
            bg_color = f"rgba(16, 185, 129, 0.15)"
            border_color = THEME_COLORS['success']
            icon = "✓"
            opacity = "1"
        elif is_current:
            bg_color = f"rgba({int(config['color'][1:3], 16)}, {int(config['color'][3:5], 16)}, {int(config['color'][5:7], 16)}, 0.15)"
            border_color = config['color']
            icon = config['icon']
            opacity = "1"
        else:
            bg_color = "transparent"
            border_color = THEME_COLORS['border']
            icon = config['icon']
            opacity = "0.4"

        html += f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0.75rem 1rem;
            background: {bg_color};
            border: 2px solid {border_color};
            border-radius: 12px;
            min-width: 100px;
            opacity: {opacity};
            transition: all 0.3s ease;
        ">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.8rem;
                font-weight: 500;
                color: {THEME_COLORS['text_primary']};
                margin-top: 0.25rem;
            ">{config['label']}</span>
        </div>
        """

        # 添加连接箭头（除了最后一个）
        if i < len(agents) - 1:
            arrow_color = THEME_COLORS['accent_cyan'] if (is_completed or is_current) else THEME_COLORS['border']
            html += f"""
            <div style="
                color: {arrow_color};
                font-size: 1.25rem;
                opacity: 0.6;
            ">→</div>
            """

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def render_code_block(code: str, language: str = "python", title: str = None, show_copy: bool = True):
    """渲染代码块 - IDE风格"""

    # 代码行数
    lines = code.strip().split('\n')
    line_count = len(lines)

    # 生成带行号的代码
    numbered_code = '\n'.join(
        f'<span style="color: {THEME_COLORS["text_muted"]}; user-select: none;">{str(i+1).rjust(3)}  </span>{line}'
        for i, line in enumerate(lines)
    )

    html = f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        overflow: hidden;
        margin: 1rem 0;
    ">
        <!-- 标题栏 -->
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid {THEME_COLORS['border']};
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <!-- 窗口按钮 -->
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #ff5f57;"></span>
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #febc2e;"></span>
                <span style="width: 12px; height: 12px; border-radius: 50%; background: #28c840;"></span>
            </div>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
                color: {THEME_COLORS['text_muted']};
            ">{title or f'{language.upper()} · {line_count} lines'}</span>
        </div>

        <!-- 代码区域 -->
        <pre style="
            margin: 0;
            padding: 1rem;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            color: {THEME_COLORS['text_primary']};
        "><code>{numbered_code}</code></pre>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_score_gauge(score: int, label: str = "代码评分"):
    """渲染评分仪表盘"""

    # 根据分数确定颜色
    if score >= 90:
        color = THEME_COLORS['success']
        status = "优秀"
    elif score >= 70:
        color = THEME_COLORS['warning']
        status = "良好"
    else:
        color = THEME_COLORS['error']
        status = "需改进"

    # 计算角度 (0-100 -> 0-180度)
    angle = (score / 100) * 180

    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 1.5rem;
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 16px;
    ">
        <!-- 仪表盘 -->
        <div style="
            position: relative;
            width: 120px;
            height: 60px;
            overflow: hidden;
        ">
            <!-- 背景弧 -->
            <div style="
                position: absolute;
                width: 120px;
                height: 120px;
                border-radius: 50%;
                border: 10px solid {THEME_COLORS['border']};
                border-bottom: none;
                border-left: none;
                transform: rotate(-45deg);
            "></div>

            <!-- 进度弧 -->
            <div style="
                position: absolute;
                width: 120px;
                height: 120px;
                border-radius: 50%;
                border: 10px solid {color};
                border-bottom: none;
                border-left: none;
                transform: rotate(-45deg);
                clip-path: polygon(0 0, {score}% 0, {score}% 100%, 0 100%);
            "></div>

            <!-- 分数 -->
            <div style="
                position: absolute;
                bottom: 0;
                left: 50%;
                transform: translateX(-50%);
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.75rem;
                font-weight: 700;
                color: {color};
            ">{score}</div>
        </div>

        <!-- 标签 -->
        <div style="
            margin-top: 0.5rem;
            font-size: 0.9rem;
            color: {THEME_COLORS['text_secondary']};
        ">{label}</div>

        <!-- 状态 -->
        <div style="
            margin-top: 0.25rem;
            font-size: 0.85rem;
            font-weight: 600;
            color: {color};
        ">{status}</div>
    </div>
    """, unsafe_allow_html=True)


def render_issue_list(issues: list):
    """渲染问题列表"""

    if not issues:
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            color: {THEME_COLORS['success']};
        ">
            <span>✓</span>
            <span>代码审查通过，未发现问题</span>
        </div>
        """, unsafe_allow_html=True)
        return

    html = f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        overflow: hidden;
        margin: 1rem 0;
    ">
        <div style="
            padding: 0.75rem 1rem;
            background: rgba(239, 68, 68, 0.1);
            border-bottom: 1px solid {THEME_COLORS['border']};
            color: {THEME_COLORS['error']};
            font-weight: 600;
        ">
            ⚠ 发现 {len(issues)} 个问题
        </div>
        <div style="padding: 0.5rem 0;">
    """

    for i, issue in enumerate(issues, 1):
        html += f"""
        <div style="
            padding: 0.75rem 1rem;
            border-bottom: 1px solid {THEME_COLORS['border']};
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
        ">
            <span style="
                background: rgba(247, 37, 133, 0.2);
                color: {THEME_COLORS['accent_magenta']};
                padding: 0.1rem 0.5rem;
                border-radius: 4px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
            ">{i}</span>
            <span style="
                color: {THEME_COLORS['text_secondary']};
                font-size: 0.9rem;
                line-height: 1.5;
            ">{issue}</span>
        </div>
        """

    html += "</div></div>"

    st.markdown(html, unsafe_allow_html=True)


def render_token_usage(used: int, total: int):
    """渲染Token使用量"""

    percentage = (used / total) * 100 if total > 0 else 0

    # 根据使用量确定颜色
    if percentage < 50:
        color = THEME_COLORS['accent_cyan']
    elif percentage < 80:
        color = THEME_COLORS['warning']
    else:
        color = THEME_COLORS['error']

    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        ">
            <span style="color: {THEME_COLORS['text_secondary']}; font-size: 0.9rem;">Token 使用量</span>
            <span style="font-family: 'JetBrains Mono', monospace; color: {color}; font-size: 0.9rem;">
                {used:,} / {total:,}
            </span>
        </div>
        <div style="
            background: {THEME_COLORS['border']};
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {THEME_COLORS['accent_cyan']}, {color});
                border-radius: 10px;
                transition: width 0.5s ease;
            "></div>
        </div>
        <div style="
            text-align: right;
            margin-top: 0.25rem;
            font-size: 0.8rem;
            color: {THEME_COLORS['text_muted']};
        ">{percentage:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)


def render_history_card(requirement: str, timestamp: str, score: int, index: int):
    """渲染历史记录卡片"""

    # 根据分数确定颜色
    if score >= 90:
        score_color = THEME_COLORS['success']
        score_bg = f"rgba(16, 185, 129, 0.15)"
    elif score >= 70:
        score_color = THEME_COLORS['warning']
        score_bg = f"rgba(245, 158, 11, 0.15)"
    else:
        score_color = THEME_COLORS['error']
        score_bg = f"rgba(239, 68, 68, 0.15)"

    # 截断需求文本
    display_requirement = requirement[:60] + "..." if len(requirement) > 60 else requirement

    st.markdown(f"""
    <div style="
        background: {THEME_COLORS['bg_tertiary']};
        border: 1px solid {THEME_COLORS['border']};
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
    " onmouseover="this.style.borderColor='{THEME_COLORS['accent_cyan']}';"
       onmouseout="this.style.borderColor='{THEME_COLORS['border']}';">

        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div style="
                    color: {THEME_COLORS['text_primary']};
                    font-weight: 500;
                    margin-bottom: 0.25rem;
                ">{display_requirement}</div>
                <div style="
                    font-size: 0.8rem;
                    color: {THEME_COLORS['text_muted']};
                    font-family: 'JetBrains Mono', monospace;
                ">📅 {timestamp}</div>
            </div>
            <div style="
                background: {score_bg};
                color: {score_color};
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 600;
            ">{score}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, description: str, action_text: str = None):
    """渲染空状态"""

    html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        text-align: center;
    ">
        <div style="
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        ">{icon}</div>
        <h3 style="
            color: {THEME_COLORS['text_secondary']};
            font-weight: 500;
            margin-bottom: 0.5rem;
        ">{title}</h3>
        <p style="
            color: {THEME_COLORS['text_muted']};
            font-size: 0.9rem;
            max-width: 300px;
        ">{description}</p>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_config_status(is_configured: bool, api_type: str = ""):
    """渲染配置状态"""

    if is_configured:
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
        ">
            <span style="color: {THEME_COLORS['success']}; font-size: 1.25rem;">✓</span>
            <div>
                <div style="color: {THEME_COLORS['success']}; font-weight: 500;">API 已配置</div>
                <div style="color: {THEME_COLORS['text_muted']}; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;">
                    {api_type.upper()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
        ">
            <span style="color: {THEME_COLORS['error']}; font-size: 1.25rem;">⚠</span>
            <div>
                <div style="color: {THEME_COLORS['error']}; font-weight: 500;">API 未配置</div>
                <div style="color: {THEME_COLORS['text_muted']}; font-size: 0.85rem;">
                    请在设置页面配置 API Key
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
