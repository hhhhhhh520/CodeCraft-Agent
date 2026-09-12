"""流式显示组件模块

提供代码生成的实时流式显示功能。
"""

import html as html_lib
import streamlit as st
from typing import Iterator
import time

from frontend.styles.theme import THEME_COLORS


def render_streaming_code(
    stream: Iterator[str],
    placeholder: st.delta_generator.DeltaGenerator,
    language: str = "python",
    show_progress: bool = True,
) -> str:
    """流式渲染代码生成

    Args:
        stream: 代码片段迭代器
        placeholder: Streamlit占位符
        language: 代码语言
        show_progress: 是否显示进度指示

    Returns:
        完整的代码文本
    """
    full_code = ""
    char_count = 0
    start_time = time.time()

    for chunk in stream:
        full_code += chunk
        char_count += len(chunk)

        # 更新显示
        if show_progress:
            elapsed = time.time() - start_time
            speed = char_count / elapsed if elapsed > 0 else 0
            # 用户代码必须先把换行编码成 &#10; 再塞进模板。
            # 原因：<div> 是 CommonMark 的 **type-6** HTML 块，**遇空行即终止**；
            # 代码里的空行一旦把块截断，其后 4 空格缩进的代码行就会被渲染成
            # **嵌套的缩进代码块**（视觉上在方框里又套一个小代码框）。
            # 编码后代码区变成单行，markdown 里再无空行，块不会断开；
            # 浏览器会把实体解码回换行，white-space: pre-wrap 照常显示。
            # 实测对比（真实 Streamlit + Playwright）：
            #   div + 原始转义          -> ❌ 嵌套代码块
            #   div + &#10; 编码        -> ✅ 正常，空行完整保留
            #   <pre> 承载              -> ❌ 标签被 Streamlit 净化剥掉，进不了 DOM
            escaped = (
                html_lib.escape(full_code)
                .replace("\r\n", "\n")
                .replace("\r", "\n")
                .replace("\n", "&#10;")
            )
            # 整段模板不能有游离空行（否则同理会截断块，见 ISSUE-010）
            placeholder.markdown(
                f"""<div style="
    background: {THEME_COLORS['bg_tertiary']};
    border: 1px solid {THEME_COLORS['border']};
    border-radius: 12px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: {THEME_COLORS['text_primary']};
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
">{escaped}</div>
<div style="font-size: 12px; color: #888; margin-top: 0.5rem;">
    📝 生成中... {char_count} 字符 | {speed:.0f} 字符/秒
</div>""",
                unsafe_allow_html=True,
            )
        else:
            placeholder.code(full_code, language=language)

    return full_code

