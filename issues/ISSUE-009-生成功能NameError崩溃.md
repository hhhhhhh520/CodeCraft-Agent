# 代码生成功能 100% 崩溃：同一路径上连续四层缺陷

> 创建时间: 2026-09-12 | 状态: 🟢已解决（2026-09-12）
>
> **修复过程的重要更正**：初次诊断只找到第 1 层。实际修复时补写的 AppTest 测试当场抓到第 3 层，
> 扩散面 grep 又带出第 4 层——**只修第 1 层等于没修**。教训：诊断"崩溃类"问题必须把整条路径走到头，
> 而不是停在第一个异常上。

## 问题描述

Streamlit 界面输入需求（如"实现一个判断字符串是否为回文的函数"）并点击「🚀 生成代码」，页面立即显示：

```
❌ 生成失败: name 'llm' is not defined
```

**核心功能开箱即崩**，不是环境或 key 问题。

## 出现原因

`frontend/pages/chat.py` 中变量名写错：

```python
generator = agents["generator"]        # L129 取出 generator
messages = [...]
for chunk in llm.stream(messages):     # L141  llm 从未定义 → NameError
```

`llm` 在整个文件中**仅此一处出现**；`generator` 赋值后在 L131 被用于取 `generator.SYSTEM_PROMPT`，**并非死变量**——真正的错因只是 L141 把 `generator.llm` 漏写成了裸 `llm`。

正确的对象结构（已核实）：

- `backend/core/factory.py:47` — `CodeGeneratorAgent(llm=llm, tools=tools)`，LLM 挂在 agent 上
- `backend/core/agent.py:27` — `self.llm = llm`
- `backend/agents/code_generator.py:60` — 同文件其它位置用的是 `self.llm.invoke(messages)`
- `backend/llm/base.py:39` — `def stream(self, messages, **kwargs)` 定义在 `BaseLLM`

即应改为 `generator.llm.stream(messages)`。

**为何 118 个测试全绿却没拦住**：`tests/` 下有 test_agent / test_llm / test_code_generator 等一整套**后端**测试，但**没有任何测试覆盖 `frontend/pages/` 这条 Streamlit 页面路径**。

已用三重证据坐实：① `grep frontend tests/` 零命中；② `grep "import frontend"` 全仓命中只在 `frontend/` 与 `docs/`；③ `.coverage`（SQLite）里 25 个文件**全部在 `backend/` 下**，`frontend` 零命中。`tests/` 下也没有 `conftest.py`。

### 同一段代码里的另外两颗地雷（一并修，否则第一个修完立刻撞第二个）

**地雷 2：`context` 未定义**（`frontend/pages/chat.py:176`、`:189`、`:201`）

```python
review_result = reviewer.process({"code": code}, context.data)   # L176 context 从未定义
fix_result = debugger.process({...}, context.data)               # L189
test_result = test_generator.process({...}, context.data)        # L201
```

`context` 在整文件里只有这 3 次使用、零次赋值。正确对象是 `orchestrator.context`（`backend/core/factory.py:53` 构造 `Orchestrator(agents=agents, context=SharedContext())`），`SharedContext.data` 是 `dict`（`backend/core/context.py:18`），与四个 agent 的 `def process(self, input_data: dict, context: dict)` 签名匹配。

**触发条件**：非 fast_mode 且 reviewer 存在 —— 即**默认路径**。修完地雷 1 后必然撞上。

**地雷 3：`GenerationResult` 缺 `test_code` 字段 → 必现 `AttributeError`**（`frontend/pages/chat.py:257`、`:260`）

```python
test_code = ""                                    # L168 初始化
test_code = test_result.get("test_code", "")      # L202 拿到测试代码
generation_result = GenerationResult(             # L214-221 构造时【没有传 test_code】
    requirement=..., code=..., review_score=..., issues=..., agent_state=...,
)
...
if result.test_code:                              # L257 → AttributeError！
```

`GenerationResult`（`session.py:24-32`）**根本没有 `test_code` 字段**，所以 L257 不是"恒为假"，而是**每次生成成功都抛 `AttributeError`**。这一层是补写 AppTest 测试时才当场抓到的——静态 F821 抓不到它（属性访问不是未定义名）。

**地雷 4：`add_to_history` 不写 `test_code` → 历史页永不显示**（`session.py:74-81`）

`add_to_history` 构造的历史条目 dict（`:74-81`）不含 `test_code` 键，而 `frontend/pages/history.py:177` 靠 `item.get("test_code")` 判断是否渲染「测试代码」区块——于是历史页那块**永远不出现**。属全局 `~/.claude/CLAUDE.md:104` 定义的「设计了但未集成」。

## 解决方案

四层缺陷必须一起修，缺一层功能就仍然不可用：

| # | 位置 | 缺陷 | 修法 |
|---|---|---|---|
| 1 | `chat.py:141` | `llm` 未定义 | → `generator.llm.stream(messages)` |
| 2 | `chat.py:176/189/201` | `context` 未定义 | → `orchestrator.context.data` |
| 3 | `chat.py:257/260` 读 `result.test_code` | `GenerationResult` 没这个字段 → `AttributeError`（**每次生成成功必现**） | `session.py:31` 加 `test_code: Optional[str] = None`；`chat.py:219` 构造时传 `test_code=test_code` |
| 4 | `session.py:74-81` `add_to_history` | 历史条目 dict 不带 `test_code` → `history.py:177` 的「测试代码」区块永不显示 | `:80` 补 `"test_code": result.test_code` |

**注意 3、4 是"算了但没接出去"型的静默缺陷**，不报错、不崩溃，只让 TestGenerator 白跑——属全局 `~/.claude/CLAUDE.md:104` 定义的「设计了但未集成」。

## 验证方式

新增 `tests/test_frontend_pages.py`（4 个用例，两层防护）：

1. **静态**：`ruff --select F821 frontend/`，修复前实测命中 4 处（`llm` ×1 + `context` ×3）
2. **运行时**：Streamlit 官方 `AppTest` 真跑 `frontend/pages/chat.py` + 真点击生成，stub 掉 `create_orchestrator` 避免打网络

**红绿证**（把 `chat.py` + `session.py` 回退到 HEAD 后重跑）：

| 版本 | 结果 |
|---|---|
| HEAD（修复前） | **4 failed** |
| 修复后 | **4 passed** |

关键设计：`test_debugger_branch_runs_with_context` 断言的是「debugger / test_generator **真被调用了**」（`orch.calls == ["reviewer","debugger","test_generator"]`），不是「错误信息里没有 context」——后者在流程提前崩溃时恒真，是假测试。第一版就是那么写的，红证时被发现旧代码上竟然通过，遂改正。

**全量回归**：122 passed（原 118 + 新增 4），零失败。

### 写这个测试时踩的坑（务必记住）

**AppTest 会写用户真实文件。** 页面成功后走 `SessionManager.add_to_history` → `HistoryManager.save` → 写 `Path.home()/.codecraft/history.json`（`session.py:210-211`、`:224-226`）。而 AppTest 里 `st.session_state.history` 初始为空 `[]`，`save` 是**覆盖**不是追加——**测试第一版没做隔离，实际覆盖了一次用户的真实历史文件**。

现已修：fixture 里用 `monkeypatch` 把 `HistoryManager.HISTORY_DIR` / `HISTORY_FILE` 指到 `tmp_path`，并加 `real_history_file` 哨兵 fixture 断言测试前后真实文件字节不变。哨兵有效性已实测（临时关掉隔离 → 哨兵报错）。

**通用教训**：给 Streamlit 页面写 AppTest 时，凡页面路径上有 `Path.home()` 落盘，必须先隔离再跑。

## 相关文件

- `frontend/pages/chat.py:129`、`:141`
- `backend/core/agent.py:27`
- `backend/core/factory.py:47`
- `backend/agents/code_generator.py:60`
- `backend/llm/base.py:39`
