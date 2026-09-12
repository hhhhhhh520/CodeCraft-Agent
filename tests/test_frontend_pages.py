# tests/test_frontend_pages.py
"""Streamlit 页面路径测试

背景：ISSUE-009 —— `frontend/pages/chat.py:141` 把 `generator.llm.stream` 写成裸 `llm`，
同一段代码里 `context` 也被用了 3 次却从未定义。118 个后端测试全绿却拦不住，
原因是 `tests/` 对 `frontend/pages/**` **零覆盖**（`.coverage` 里 25 个文件全在 backend/）。

本文件补上这条路径，两层防护：
1. 静态：frontend/ 下不得出现未定义名（F821），直接命中本类笔误
2. 运行时：用 Streamlit 官方 AppTest 真跑一次生成流程，把两个 NameError 都走到
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CHAT_PAGE = FRONTEND_DIR / "pages" / "chat.py"


class TestFrontendUndefinedNames:
    """静态守卫：frontend/ 下不允许存在未定义名（F821）

    修复前实测命中 4 处：`llm`(chat.py:141) + `context`(chat.py:176/189/201)。
    """

    def test_no_undefined_names_in_frontend(self):
        ruff = shutil.which("ruff") or shutil.which("ruff.exe")
        if ruff is None:
            # 回退到 `python -m ruff`，仍不可用则跳过（ruff 在 dev 依赖里）
            probe = subprocess.run(
                [sys.executable, "-m", "ruff", "--version"],
                capture_output=True,
                text=True,
            )
            if probe.returncode != 0:
                pytest.skip("ruff 不可用，跳过静态未定义名检查")
            ruff_cmd = [sys.executable, "-m", "ruff"]
        else:
            ruff_cmd = [ruff]

        result = subprocess.run(
            ruff_cmd
            + ["check", "--select", "F821", "--no-cache", "--output-format", "concise",
               str(FRONTEND_DIR)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0, (
            "frontend/ 下存在未定义名，这类笔误只会在页面真正执行时才炸：\n"
            f"{result.stdout}\n{result.stderr}"
        )


# ===== 运行时防护：用 AppTest 真跑生成流程 =====


class _FakeStreamingLLM:
    """替身 LLM：只实现页面用到的 stream()"""

    def stream(self, messages, **kwargs):
        # 断言页面确实把 messages 传下来了，而不是对着空气调用
        assert isinstance(messages, list) and messages, "messages 必须是非空列表"
        yield "```python\n"
        yield "def is_palindrome(s: str) -> bool:\n"
        yield "    return s == s[::-1]\n"
        yield "```"


class _FakeGenerator:
    """替身 generator：模拟 CodeGeneratorAgent 的对外形状（SYSTEM_PROMPT + llm）"""

    SYSTEM_PROMPT = "you are a code generator"

    def __init__(self, calls=None):
        self.llm = _FakeStreamingLLM()
        self.calls = calls if calls is not None else []

    def process(self, input_data, context):
        self.calls.append("generator")
        return {}


class _FakeReviewer:
    """故意返回 passed=False，逼页面走进 debugger 分支（那里有 context.data 的使用）"""

    def __init__(self, calls=None):
        self.calls = calls if calls is not None else []

    def process(self, input_data, context):
        self.calls.append("reviewer")
        return {
            "passed": False,
            "issues": [{"severity": "low", "type": "style", "line": 1, "message": "加类型标注"}],
            "score": 60,
        }


class _FakeDebugger:
    def __init__(self, calls=None):
        self.calls = calls if calls is not None else []

    def process(self, input_data, context):
        self.calls.append("debugger")
        return {"fixed_code": input_data.get("code", "")}


class _FakeTestGenerator:
    def __init__(self, calls=None):
        self.calls = calls if calls is not None else []

    def process(self, input_data, context):
        self.calls.append("test_generator")
        return {"test_code": "def test_is_palindrome():\n    assert is_palindrome('ab')\n"}


class _FakeContext:
    data = {"task_id": "fake"}


class _FakeOrchestrator:
    def __init__(self):
        # 记录每个 agent 是否真被调用——用来证明流程真的走到了那一行，
        # 而不是"没走到所以没报错"（后者是假测试）
        self.calls = []
        self.agents = {
            "generator": _FakeGenerator(self.calls),
            "reviewer": _FakeReviewer(self.calls),
            "debugger": _FakeDebugger(self.calls),
            "test_generator": _FakeTestGenerator(self.calls),
        }
        self.context = _FakeContext()


@pytest.fixture
def stub_orchestrator(monkeypatch, tmp_path):
    """把 create_orchestrator 换成替身，避免测试真的打网络

    chat.py 在点击生成时才 `from backend.core.factory import create_orchestrator`，
    属延迟导入，因此 patch 模块属性即可生效。

    ⚠️ 同时必须隔离历史记录落盘：页面成功后会走
    `SessionManager.add_to_history` → `HistoryManager.save`，而它写的是
    `Path.home()/.codecraft/history.json`。AppTest 里 `st.session_state.history`
    初始为空 `[]`，于是 save 是**覆盖**而非追加——不隔离就会把用户真实历史文件冲掉。
    （本测试第一版没隔离，实际覆盖过一次，见 ISSUE-009。）
    """
    import backend.core.factory as factory_module
    from frontend.utils.session import HistoryManager

    monkeypatch.setattr(HistoryManager, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(HistoryManager, "HISTORY_FILE", tmp_path / "history.json")

    created = []

    def _fake_create(**kwargs):
        orch = _FakeOrchestrator()
        created.append(orch)
        return orch

    monkeypatch.setattr(factory_module, "create_orchestrator", _fake_create)
    return created


@pytest.fixture
def real_history_file():
    """哨兵：记录真实 history.json 的状态，测试结束时断言它没被动过"""
    real = Path.home() / ".codecraft" / "history.json"
    before = real.read_bytes() if real.exists() else None
    yield real
    after = real.read_bytes() if real.exists() else None
    assert after == before, (
        f"测试污染了用户真实文件 {real}！"
        "HistoryManager 未被隔离到 tmp_path。"
    )


def _run_generation(api_type="openai", fast_mode=False):
    """跑一次真实页面 + 真实点击生成，返回 AppTest"""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(CHAT_PAGE), default_timeout=60)
    at.session_state["config"] = {
        "api_key": "test-key-not-a-real-secret",
        "api_type": api_type,
        "model": "test-model",
        "fast_mode": fast_mode,
    }
    at.run()

    at.text_area[0].set_value("实现一个判断字符串是否为回文的函数")
    at.button[0].click().run()
    return at


class TestChatPageGenerationFlow:
    """ISSUE-009 回归：生成功能必须真的跑通，而不是抛 NameError"""

    def test_generation_flow_completes_without_nameerror(self, stub_orchestrator, real_history_file):
        at = _run_generation()

        # 页面不得抛出任何未捕获异常
        assert not at.exception, f"页面抛异常了: {[str(e.value) for e in at.exception]}"

        # 不得出现 NameError 提示
        errors = [e.value for e in at.error]
        assert not any("NameError" in str(e) for e in errors), f"仍有 NameError: {errors}"
        assert not any("is not defined" in str(e) for e in errors), f"仍有未定义名: {errors}"

        # 生成结果必须落进会话状态
        result = at.session_state["generation_result"]
        assert result is not None, f"生成结果为空，页面错误信息: {errors}"
        assert "is_palindrome" in result.code, f"代码未正确提取: {result.code!r}"

        # test_code 必须真的接出去（修复前 GenerationResult 没这个字段，
        # 页面 L256 的 result.test_code 会 AttributeError，且 TestGenerator 白跑）
        assert result.test_code, "test_code 未接进 GenerationResult"
        assert "test_is_palindrome" in result.test_code

        # 历史条目也必须带上 test_code（history.py:177 靠它显示「测试代码」区块）
        history = at.session_state["history"]
        assert history, "历史记录为空"
        assert "test_code" in history[0], f"历史条目缺 test_code: {history[0].keys()}"
        assert history[0]["test_code"], "历史里的 test_code 为空"

        # 确认真实 save 路径跑过、且落在 tmp_path 而非用户目录
        from frontend.utils.session import HistoryManager

        assert HistoryManager.HISTORY_FILE.exists(), "HistoryManager.save 未被执行"
        saved = json.loads(HistoryManager.HISTORY_FILE.read_text(encoding="utf-8"))
        assert saved and saved[0]["test_code"] == history[0]["test_code"]

    def test_debugger_branch_runs_with_context(self, stub_orchestrator, real_history_file):
        """reviewer 返回 passed=False 时页面会走 debugger，那里用了 orchestrator.context.data

        关键：这里断言的是「debugger / test_generator 真被调用了」。
        只断言 errors 里没有 'context' 是假测试——流程若在前一步就崩，
        这一行根本不会被执行，断言会恒真。
        """
        at = _run_generation()

        assert not at.exception, f"页面抛异常了: {[str(e.value) for e in at.exception]}"

        orch = stub_orchestrator[-1]
        assert orch.calls == ["reviewer", "debugger", "test_generator"], (
            f"流程未按预期走到 debugger/test_generator，实际调用顺序: {orch.calls}"
        )
        assert "fix_result" not in [
            str(e.value) for e in at.error
        ], f"错误信息: {[str(e.value) for e in at.error]}"

    def test_fast_mode_still_works(self, stub_orchestrator, real_history_file):
        """fast_mode 只跑 generator，走的是不同分支，单独覆盖"""
        at = _run_generation(fast_mode=True)

        assert not at.exception, f"页面抛异常了: {[str(e.value) for e in at.exception]}"
        errors = [e.value for e in at.error]
        assert not any("is not defined" in str(e) for e in errors), f"仍有未定义名: {errors}"
