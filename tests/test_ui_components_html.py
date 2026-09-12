# tests/test_ui_components_html.py
"""ISSUE-010 回归：ui_components 输出的 HTML 必须渲染成 HTML，不能降级成代码块

根因（CommonMark 规则，不是某个模板写错）：
1. HTML 块**遇空行即终止**；终止之后，4 空格缩进的行会被解析成「缩进代码块」
2. HTML 块**起始行缩进超过 3 空格**根本不会开启块，整段直接进代码块

本文件用 Streamlit 前端同款的 CommonMark 渲染器（markdown_it）对**真实组件函数**
的输出做断言，而不是只测手写的样例字符串。
"""

import pytest
from markdown_it import MarkdownIt

import frontend.components.ui_components as ui

MD = MarkdownIt("commonmark", {"html": True})


@pytest.fixture
def captured(monkeypatch):
    """拦下组件里的 st.markdown，取出它实际要渲染的字符串"""
    box = []

    def _fake(markdown_str, **kwargs):
        box.append((markdown_str, kwargs))

    monkeypatch.setattr(ui.st, "markdown", _fake)
    return box


def _render(captured):
    assert len(captured) == 1, f"期望组件只调用一次 st.markdown，实际 {len(captured)} 次"
    text, kwargs = captured[0]
    assert kwargs.get("unsafe_allow_html") is True, "HTML 渲染必须带 unsafe_allow_html=True"
    # 必须 lstrip：Streamlit 会 lstrip 整个 markdown body，这是实测确认的行为。
    # 不 lstrip 的话本测试会比真实渲染器严格（把「4 空格缩进 + 无空行」误判成代码块），
    # 产生假失败。四种「缩进×空行」组合已实测逐一比对，lstrip 模型 4/4 吻合。
    return MD.render(text.lstrip())


# 每个组件一条：调用方式 + 渲染结果里必须真实出现的标签 + 不能出现的转义标记
CASES = [
    pytest.param(
        lambda: ui.render_hero_section("CodeCraft Agent", "多 Agent 协作", "描述"),
        ("<h1", "<p"), id="hero_section",
    ),
    pytest.param(
        lambda: ui.render_feature_card("🚀", "功能标题", "功能描述"),
        ("<h3", "<p"), id="feature_card",
    ),
    pytest.param(
        lambda: ui.render_stat_card("118", "测试数"),
        ("<div",), id="stat_card",
    ),
    pytest.param(
        lambda: ui.render_agent_pipeline(current_agent="Generator", completed_agents=["Generator"]),
        ("代码生成", "→"), id="agent_pipeline",
    ),
    pytest.param(
        # 故意不传含 < > 的代码，避免正常的 HTML 转义干扰断言
        lambda: ui.render_code_block("def f():\n    return 1", title="a.py"),
        ("<pre", "<code"), id="code_block",
    ),
    pytest.param(
        lambda: ui.render_score_gauge(88),
        ("88",), id="score_gauge",
    ),
    pytest.param(
        lambda: ui.render_issue_list(["未加类型标注", "变量命名不规范"]),
        ("<div", "未加类型标注"), id="issue_list_with_issues",
    ),
    pytest.param(
        lambda: ui.render_issue_list([]),
        ("<div",), id="issue_list_empty",
    ),
    pytest.param(
        lambda: ui.render_token_usage(5000, 128000),
        ("<div",), id="token_usage",
    ),
    pytest.param(
        lambda: ui.render_history_card("实现一个回文函数", "2026-09-12 10:00", 90, 0),
        ("<div", "实现一个回文函数"), id="history_card",
    ),
    pytest.param(
        lambda: ui.render_empty_state("💻", "等待输入", "输入需求后开始"),
        ("<h3", "<p"), id="empty_state",
    ),
    pytest.param(
        lambda: ui.render_config_status(True, "deepseek"),
        ("<div", "API 已配置"), id="config_status_ok",
    ),
    pytest.param(
        lambda: ui.render_config_status(False),
        ("<div", "API 未配置"), id="config_status_missing",
    ),
]


@pytest.mark.parametrize("make,markers", CASES)
def test_component_renders_as_html_not_code_block(captured, make, markers):
    make()
    out = _render(captured)

    # 核心断言：任何被转义的标签都说明这段 HTML 掉进了代码块
    assert "&lt;" not in out, (
        "组件 HTML 被渲染成了代码块（CommonMark 规则：空行终止 HTML 块 / 首行缩进 >3 空格不开启块）。\n"
        f"渲染结果片段：\n{out[:400]}"
    )
    assert "<pre><code>" not in out, f"出现了缩进代码块：\n{out[:400]}"

    # 反向断言：确认目标标签真的渲染出来了（防止"什么都没输出"也算通过）
    for marker in markers:
        assert marker in out, f"渲染结果里缺少 {marker!r}，断言会变成空转：\n{out[:400]}"


def test_code_block_preserves_blank_lines_in_user_code(captured):
    """边界：用户代码里的空行不能被 _render_html 的「去空行」误伤

    _render_html 会剥掉纯空白行。若用户代码里的空行也变成纯空白行，代码显示就会丢行。
    实际不会——numbered_code 每行都带一个行号 <span>，空代码行渲染出来是
    `<span ...>  3  </span>` 而非空白，因此不会被剥掉。本测试把这个前提钉住。
    """
    code = "def f():\n\n    return 1\n\n"
    ui.render_code_block(code, title="a.py")
    text, _ = captured[0]
    out = MD.render(text)

    assert "&lt;" not in out, f"代码块自身被降级成代码块了：\n{out[:400]}"

    # 只数【行号 span】——它带 user-select: none；不能用全部 </span>，
    # 因为 render_code_block 自己的窗口按钮(3)和标题(1)也是 span，
    # 用 ">=" 比总数会让断言恒真，变成假测试。
    line_count = len(code.strip().split("\n"))
    rendered_lines = out.count("user-select: none")
    assert rendered_lines == line_count, (
        f"行号 span 数({rendered_lines}) 与代码行数({line_count}) 不符，"
        f"空行可能被 _render_html 剥掉了：\n{out[:400]}"
    )

    # 空行那一行虽然没有内容，但行号仍在，说明整行没被删掉
    assert str(line_count).rjust(3) in out, "最后一行行号缺失，代码尾部被截断"
