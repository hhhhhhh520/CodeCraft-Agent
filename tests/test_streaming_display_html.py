# tests/test_streaming_display_html.py
"""ISSUE-011 回归：流式组件的 HTML 必须渲染成 HTML

被测函数 `render_streaming_code` 修复过 3 个问题中的 2 个（第 3 个是同文件里
已删除的死代码，见下）：

1. 闭合代码围栏缩进 16 空格 → 围栏永不闭合，整段变代码块
   修法：改用 HTML div 承载，不再用 markdown 围栏
2. 用户代码里的空行截断 type-6 HTML 块 → 后续缩进行变成嵌套代码块
   修法：把换行编码成 `&#10;`（详见 `test_no_nested_code_block_from_user_blank_lines`）

同文件原有的 `render_streaming_text` / `StreamingDisplay` /
`render_agent_streaming_status` 从未被调用，连同 `agent_status.py` /
`code_display.py` 已于 2026-09-12 删除（见 issues/ISSUE-011）。

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
        # 代码区在承载容器内部；容器是 <div …>…</div>
        # （不要按 </pre> 提取——换用 pre 承载在真实 Streamlit 里会被净化剥掉）
        start = last.index(">", last.index("overflow-y: auto")) + 1
        end = last.index("</div>", start)
        rendered_code = last[start:end]

        # 换行在渲染串里被编码成 &#10;（防止空行截断 HTML 块），行数要按实体数
        assert rendered_code.count("&#10;") == code.count("\n"), (
            f"渲染串里编码后的换行数({rendered_code.count('&#10;')}) 与输入"
            f"({code.count(chr(10))}) 不符，空行被吃掉了：\n{rendered_code!r}"
        )
        assert rendered_code.startswith("def f():&#10;&#10;"), f"空行没保住：\n{rendered_code!r}"
        assert "\n" not in rendered_code, (
            "代码区里出现了真实换行——会重新触发空行截断 HTML 块的问题：\n"
            f"{rendered_code!r}"
        )

    def test_escapes_html_in_user_code(self):
        """用户代码里的标签必须转义，不能作为 HTML 注入"""
        ph = _FakePlaceholder()
        render_streaming_code(iter(["x = '<script>alert(1)</script>'\n"]), ph, "python")

        last = ph.calls[-1][0]
        assert "&lt;script&gt;" in last, f"用户代码未转义：\n{last}"
        assert "<script>" not in last, "用户代码里的标签成了活 HTML"

    def test_no_nested_code_block_from_user_blank_lines(self):
        """用户代码里的空行不能把后续缩进行变成嵌套代码块

        真因：`<div>` 是 CommonMark 的 **type-6** HTML 块，**遇空行即终止**；
        块一断，其后 4 空格缩进的代码行就被渲染成缩进代码块（视觉上在深色方框里
        再套一个小代码框）。修法：把代码里的换行编码成 `&#10;`，代码区变成单行，
        markdown 里再无空行，块不会断开。

        ⚠️ 本测试用 markdown_it，能覆盖"空行截断"这条规则；但**覆盖不到
        Streamlit 的 HTML 净化**——曾经试过用 `<pre>` 承载，markdown_it 判定通过，
        真实 Streamlit 却把 `<pre>` 标签整个剥掉了。这类差异只能靠浏览器实测发现。
        """
        ph = _FakePlaceholder()
        render_streaming_code(iter(["def f():\n\n    return 1\n"]), ph, "python")

        out = MD.render(ph.calls[-1][0].lstrip())
        assert out.count("<pre><code>") == 0, f"出现了嵌套的缩进代码块：\n{out[:400]}"
        assert out.count("<pre") == 0, f"不应有任何 pre（承载靠 div）：\n{out[:400]}"
        # markdown_it 不解码 HTML 实体（解码发生在浏览器），
        # 所以这里断言实体**存在**；"浏览器会把它解码回换行"由浏览器实测覆盖。
        assert "&#10;" in out, f"换行未被编码成实体：\n{out[:400]}"

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
