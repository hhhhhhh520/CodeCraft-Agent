# 代码生成功能 100% 崩溃：name 'llm' is not defined

> 创建时间: 2026-09-12 | 状态: 🔴未解决

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

`context` 在整文件里只有这 3 次使用、零次赋值。正确对象是 `orchestrator.context`（`backend/core/factory.py:50` 构造 `Orchestrator(agents=agents, context=SharedContext())`），`SharedContext.data` 是 `dict`（`backend/core/context.py:20`），与四个 agent 的 `def process(self, input_data: dict, context: dict)` 签名匹配。

**触发条件**：非 fast_mode 且 reviewer 存在 —— 即**默认路径**。修完地雷 1 后必然撞上。

**地雷 3：`test_code` 算了但没接出去**（`frontend/pages/chat.py:168`、`:202`）

```python
test_code = ""                                    # L168 初始化
test_code = test_result.get("test_code", "")      # L202 拿到测试代码
generation_result = GenerationResult(             # L214-220 构造时【没有传 test_code】
    requirement=..., code=..., review_score=..., issues=..., agent_state=...,
)
```

后果：L256 的 `if result.test_code:` 恒为假，「### 测试代码」区块**永远不显示**——TestGenerator agent 白跑。属 CLAUDE.md 定义的「设计了但未集成」。

## 解决方案

1. 把 `frontend/pages/chat.py:141` 的 `llm.stream(...)` 改为 `generator.llm.stream(...)`
2. 新增覆盖该页面生成路径的测试（否则同类 bug 会再次存活）

## 验证方式

启动 `streamlit run frontend/app.py`，输入需求点生成，应不再出现 NameError；有可用 key 时应输出代码。

## 相关文件

- `frontend/pages/chat.py:129`、`:141`
- `backend/core/agent.py:27`
- `backend/core/factory.py:47`
- `backend/agents/code_generator.py:60`
- `backend/llm/base.py:39`
