# tests/test_history_page_xss.py
"""ISSUE-012 回归：历史页搜索词必须转义后再插入 HTML

`frontend/pages/history.py:123` 原先把 `st.text_input` 的搜索词直接插进
交给 `st.markdown(..., unsafe_allow_html=True)` 的 f-string，构成 HTML 注入。

浏览器实测（Streamlit 1.55 + Playwright）确认影响面：
- `<img onerror=...>` 的 onerror 被前端净化剥掉，`<script>` 不执行 → **脚本执行未达成**
- 但 `<a href="javascript:...">` 的 href 存活、`<iframe src=任意URL>` 存活并加载
  → **HTML/内容注入成立**（钓鱼、UI 伪造面）
- 搜索词不经 URL 投递 → 属**自注入**，非可交付的 XSS

本测试钉住"转义"这个修复点：无论净化器未来怎么变，标签都不该以原始形态进入 HTML。
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PAGE = PROJECT_ROOT / "frontend" / "pages" / "history.py"

PAYLOAD = '<img src=x onerror="document.title=\'XSS\'">'

# 搜索词匹配不到这条记录，因此会走进「未找到匹配」分支（该分支才用到 search_query）
RECORD = {
    "timestamp": "2026-09-12T10:00:00",
    "requirement": "实现一个快速排序算法",
    "code": "def quicksort(a):\n    return a",
    "review_score": 95,
    "issues": [],
    "test_code": "",
}


@pytest.fixture
def seeded_history(monkeypatch, tmp_path):
    """让页面拿到一条记录，并把 HistoryManager 隔离到 tmp_path

    页面的搜索分支有前置条件 `if not history:`（history.py:97 提前返回）——
    历史为空时**根本走不到**那段代码，所以必须喂一条记录才能测到。
    """
    from frontend.utils.session import HistoryManager

    monkeypatch.setattr(HistoryManager, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(HistoryManager, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(HistoryManager, "load", classmethod(lambda cls: [dict(RECORD)]))
    return tmp_path


def _run_with_search(term: str):
    at = AppTest.from_file(str(HISTORY_PAGE), default_timeout=60)
    at.run()
    at.text_input[0].set_value(term).run()
    return at


class TestHistorySearchEscaping:
    """ISSUE-012 回归"""

    def test_search_payload_is_escaped_not_injected(self, seeded_history):
        at = _run_with_search(PAYLOAD)

        assert not at.exception, f"页面抛异常: {[str(e.value) for e in at.exception]}"

        hits = [m.value for m in at.markdown if "未找到匹配" in m.value]
        assert hits, "没走到「未找到匹配」分支，测试前提不成立（需先有历史记录）"

        rendered = hits[0]
        # 关键断言：标签必须以实体形式出现，不能是活的标签
        assert "&lt;img" in rendered, f"搜索词未被转义：\n{rendered}"
        assert "<img" not in rendered, f"搜索词以原始标签插入，构成 HTML 注入：\n{rendered}"
        assert "onerror" not in rendered.split("&lt;img")[0], "onerror 出现在未转义区段"

    def test_normal_search_term_still_shown(self, seeded_history):
        """反向：普通搜索词要原样显示，别把转义写过头"""
        at = _run_with_search("不存在的关键词")

        hits = [m.value for m in at.markdown if "未找到匹配" in m.value]
        assert hits, "没走到「未找到匹配」分支"
        assert "不存在的关键词" in hits[0], f"正常搜索词被杀掉了：\n{hits[0]}"

    def test_empty_history_short_circuits(self, monkeypatch, tmp_path):
        """历史为空时页面提前返回空状态，不会走到搜索分支——这是 ISSUE-012 不可达的原因"""
        from frontend.utils.session import HistoryManager

        monkeypatch.setattr(HistoryManager, "HISTORY_FILE", tmp_path / "history.json")
        monkeypatch.setattr(HistoryManager, "load", classmethod(lambda cls: []))

        at = AppTest.from_file(str(HISTORY_PAGE), default_timeout=60)
        at.run()
        at.text_input[0].set_value(PAYLOAD).run()

        texts = " ".join(m.value for m in at.markdown)
        assert "未找到匹配" not in texts, "历史为空时不该走到搜索分支"
