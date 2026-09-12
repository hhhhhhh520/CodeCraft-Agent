# tests/test_streaming_display_html.py
"""ISSUE-011 回归：流式组件的 HTML 必须渲染成 HTML

修复前 3 处缺陷（均用真实渲染器实测确认）：
- `render_streaming_code`：闭合代码围栏缩进 16 空格 → 围栏永不闭合，整段进代码块
- `render_streaming_text`：`{full_text}` 后夹空行 → HTML 块被终止
- `render_agent_streaming_status`：`+=` 拼接每段以纯空白行结尾 → 产生空行

本文件覆盖前者的**已修复**状态；后两者仍为死代码，未修（见 ISSUE-011）。
`placeholder` 是函数入参，所以直接塞替身即可，不需要 monkeypatch。
"""

import pytest
from markdown_it import MarkdownIt

from frontend.components.streaming_display import render_streaming_code

MD = MarkdownIt("commonmark", {"html": True})


class _FakePlaceholder:
    """替代 st.empty() 占位符，记录每次渲染"""

    def __init__(self):
        self.calls = []

    def markdown(self, text, **kwargs):
        self.calls.append((text, kwargs))

    def code(self, text, **kwargs):
        self.calls.append((f"__CODE__{text}", kwargs))


def _assert_all_html(calls):
    assert calls, "组件一次都没渲染"
    for text, kwargs in calls:
        assert kwargs.get("unsafe_allow_html") is True, "HTML 渲染必须带 unsafe_allow_html=True"
        # Streamlit 会 lstrip body —— 不 lstrip 比真实渲染器严格（详见 ISSUE-010）
        out = MD.render(text.lstrip())
        assert "&lt;" not in out, f"HTML 被渲染成代码块：\n{out[:400]}"
        assert "<pre><code>" not in out, f"出现了缩进代码块：\n{out[:400]}"


class TestStreamingCodeRendering:
    def test_renders_as_html_not_code_block(self):
        ph = _FakePlaceholder()
        result = render_streaming_code(iter(["def f():\n", "    return 1\n"]), ph, "python")

        assert result == "def f():\n    return 1\n", "返回值必须拼出完整代码"
        _assert_all_html(ph.calls)

    def test_user_code_blank_lines_survive(self):
        """用户代码里的空行不能被渲染逻辑吃掉

        关键：断言的是**交给 markdown 的那段字符串**，不是返回值。
        只断言返回值的话，即使渲染串里空行被剥掉了测试也照样通过（假测试）。
        """
        ph = _FakePlaceholder()
        code = "def f():\n\n    return 1\n"
        result = render_streaming_code(iter([code]), ph, "python")

        assert result == code

        last = ph.calls[-1][0]
        # 代码区被包在 <div ...>{escaped_code}</div> 里，取出中间那段
        start = last.index(">", last.index("overflow-y: auto")) + 1
        end = last.index("</div>", start)
        rendered_code = last[start:end]
        assert len(rendered_code.split("\n")) == len(code.split("\n")), (
            f"渲染串里的代码行数({len(rendered_code.split(chr(10)))}) 与输入"
            f"({len(code.split(chr(10)))}) 不符，空行被吃掉了：\n{rendered_code!r}"
        )
        assert rendered_code.startswith("def f():\n\n"), f"空行没保住：\n{rendered_code!r}"

    def test_escapes_html_in_user_code(self):
        """用户代码里的标签必须转义，不能作为 HTML 注入"""
        ph = _FakePlaceholder()
        render_streaming_code(iter(["x = '<script>alert(1)</script>'\n"]), ph, "python")

        last = ph.calls[-1][0]
        assert "&lt;script&gt;" in last, f"用户代码未转义：\n{last}"
        assert "<script>" not in last, "用户代码里的标签成了活 HTML"

    def test_progress_indicator_present(self):
        """进度行是接入组件后的新增信息，必须在最后一个渲染帧里"""
        ph = _FakePlaceholder()
        render_streaming_code(iter(["abc"]), ph, "python")

        last = ph.calls[-1][0]
        assert "生成中" in last and "字符" in last

    def test_no_progress_mode_uses_plain_code(self):
        """show_progress=False 走 placeholder.code 分支"""
        ph = _FakePlaceholder()
        render_streaming_code(iter(["abc"]), ph, "python", show_progress=False)

        assert len(ph.calls) == 1
        assert ph.calls[0][0].startswith("__CODE__"), "应走 placeholder.code 分支"
