"""流式显示组件模块

提供代码生成的实时流式显示功能。
"""

import streamlit as st
from typing import Iterator, Optional
import time


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
            placeholder.markdown(
                f"""
                ```{language}
{full_code}
                ```
                <div style="font-size: 12px; color: #888;">
                    📝 生成中... {char_count} 字符 | {speed:.0f} 字符/秒
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            placeholder.code(full_code, language=language)

    return full_code


def render_streaming_text(
    stream: Iterator[str],
    placeholder: st.delta_generator.DeltaGenerator,
    show_progress: bool = True,
) -> str:
    """流式渲染文本

    Args:
        stream: 文本片段迭代器
        placeholder: Streamlit占位符
        show_progress: 是否显示进度指示

    Returns:
        完整的文本
    """
    full_text = ""
    char_count = 0

    for chunk in stream:
        full_text += chunk
        char_count += len(chunk)

        if show_progress:
            placeholder.markdown(
                f"""
                {full_text}

                <div style="font-size: 12px; color: #888;">
                    📝 生成中... {char_count} 字符
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            placeholder.markdown(full_text)

    return full_text


class StreamingDisplay:
    """流式显示管理器"""

    def __init__(self, container: st.delta_generator.DeltaGenerator):
        """初始化流式显示管理器

        Args:
            container: Streamlit容器
        """
        self.container = container
        self.code_placeholder = None
        self.status_placeholder = None
        self.progress_bar = None

    def start(self, message: str = "正在生成..."):
        """开始流式显示

        Args:
            message: 状态消息
        """
        self.status_placeholder = self.container.empty()
        self.code_placeholder = self.container.empty()
        self.progress_bar = self.container.progress(0)

        self.status_placeholder.info(f"⏳ {message}")

    def update_code(self, code: str, language: str = "python"):
        """更新代码显示

        Args:
            code: 当前代码
            language: 代码语言
        """
        self.code_placeholder.code(code, language=language)

    def update_status(self, message: str, progress: Optional[float] = None):
        """更新状态

        Args:
            message: 状态消息
            progress: 进度 (0.0 - 1.0)
        """
        self.status_placeholder.info(f"⏳ {message}")

        if progress is not None and self.progress_bar:
            self.progress_bar.progress(min(progress, 1.0))

    def complete(self, code: str, language: str = "python"):
        """完成流式显示

        Args:
            code: 最终代码
            language: 代码语言
        """
        self.status_placeholder.success("✅ 生成完成!")
        self.code_placeholder.code(code, language=language)

        if self.progress_bar:
            self.progress_bar.progress(1.0)
            self.progress_bar.empty()

    def error(self, message: str):
        """显示错误

        Args:
            message: 错误消息
        """
        self.status_placeholder.error(f"❌ {message}")

        if self.progress_bar:
            self.progress_bar.empty()


def render_agent_streaming_status(
    current_agent: str,
    agents: list[str],
    completed: list[str],
    placeholder: st.delta_generator.DeltaGenerator,
):
    """渲染Agent流式状态

    Args:
        current_agent: 当前执行的Agent
        agents: 所有Agent列表
        completed: 已完成的Agent列表
        placeholder: Streamlit占位符
    """
    status_html = "<div style='display: flex; gap: 10px; flex-wrap: wrap;'>"

    for agent in agents:
        if agent in completed:
            # 已完成
            status_html += f"""
            <div style='
                padding: 8px 16px;
                border-radius: 20px;
                background: #d4edda;
                color: #155724;
                font-weight: bold;
            '>
                ✅ {agent}
            </div>
            """
        elif agent == current_agent:
            # 执行中
            status_html += f"""
            <div style='
                padding: 8px 16px;
                border-radius: 20px;
                background: #fff3cd;
                color: #856404;
                font-weight: bold;
                animation: pulse 1s infinite;
            '>
                ⏳ {agent}
            </div>
            """
        else:
            # 等待中
            status_html += f"""
            <div style='
                padding: 8px 16px;
                border-radius: 20px;
                background: #e9ecef;
                color: #6c757d;
            '>
                ⏸️ {agent}
            </div>
            """

    status_html += "</div>"

    placeholder.markdown(status_html, unsafe_allow_html=True)
