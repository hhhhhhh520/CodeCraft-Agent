# 流式显示组件：死代码 + 渲染缺陷（原判"渲染成源码"不成立）

> 创建时间: 2026-09-12 | 状态: 🟢已解决（2026-09-12）
>
> **两处更正**：
> ① 原判「用户看到裸 HTML 源码」**不成立**——该模块当时零调用点，渲染成什么样都没人看。
> ② 处置方式经讨论定为**接入 + 全删**：`render_streaming_code` 修好并接进 `chat.py`
> 消除重复；其余无处可"接入"的死代码（3 个函数/类 + 2 个整模块）**全部删除**。

## 问题描述（原始）

`frontend/components/streaming_display.py`（231 行）**没有任何调用点**：

- `render_streaming_code` / `StreamingDisplay` 只在 `frontend/components/__init__.py` 被 import 与列入 `__all__`
- `render_streaming_text`、`render_agent_streaming_status` 连 `__init__.py` 都没导出
- `tests/` 下零引用

**同类问题不止这一个模块**——`frontend/components/` 下 4 个模块原本有 3 个是死代码：

| 模块 | 行数 | 原始状态 | 当前状态 |
|---|---|---|---|
| `ui_components.py` | 686 | ✅ 在用 | ✅ 在用 |
| `streaming_display.py` | 231 | ❌ 死代码 | 🟡 `render_streaming_code` 已接入，其余仍死 |
| `agent_status.py` | 107 | ❌ 死代码 | ❌ 仍死 |
| `code_display.py` | 53 | ❌ 死代码 | ❌ 仍死 |

**为何会这样**：`PLAN_简历展示完善.md:217-233` 明确计划「**在 chat.py 中使用** `render_streaming_code`」，但该步从未落地——`chat.py` 自己内联实现了一套流式显示。两套并存，页面用的是内联那套。

**代价已经发生过**：`PROGRESS.md:151/195/196/209` 记录了对 `streaming_display` 的多轮 XSS 加固（最后改动 2026-06-28）——**这些工作量全花在了没人执行的代码上**。

## 出现原因

计划与实现脱节：计划文档写明了接入点，实现时改成了内联写法，但组件模块被保留下来，且 `__init__.py` 把它导出，制造了「这是个在用的模块」的假象。

## 已做（2026-09-12）

### 1. 修复 `render_streaming_code` 的渲染缺陷

原实现把流式输出包进 **markdown 代码围栏**：

````python
placeholder.markdown(
    f"""
    ```{language}
{escaped_code}
    ```
    ...
````

**两个问题**：① 闭合围栏缩进 16 空格 → CommonMark 只认 ≤3 空格的闭合围栏 → **围栏永不闭合，整段变成代码块**；② 即使围栏修好，用户代码里若出现一行单独的三反引号会提前闭合围栏（用户内容直接参与语法解析）。

改为**用 HTML div 承载**（与 chat.py 原内联实现同款样式），彻底避开围栏语义。

### 2. 接入 `chat.py`，消除重复

`frontend/pages/chat.py` 删除内联的流式循环（24 行），改为：

```python
code_placeholder = st.empty()
full_code = render_streaming_code(
    generator.llm.stream(messages), code_placeholder, language="python"
)
```

连带清理：`THEME_COLORS` 与 `import html as html_lib` 在本文件已成孤儿，一并移除。

**样式刻意保持一致**（没有换成组件原来的围栏样式），目的是让"接入"这件事**可被验证**——若改了外观，就没有基线可比，无法证明没改坏。

> 接入后新增信息：进度行多出速度显示（组件原本就有，内联版没有）。

## 验证方式

**单测** `tests/test_streaming_display_html.py`（6 用例，`placeholder` 是入参所以直接塞替身，无需 monkeypatch）：

- 渲染成 HTML 而非代码块（`markdown_it` 判定，须 `.lstrip()`，见 ISSUE-010）
- **用户代码空行不被吃掉**——断言的是**交给 markdown 的字符串**里的代码行数，不是返回值（只断言返回值的话，空行被剥掉也照样通过，是假测试）
- 用户代码里的标签被转义
- 进度行存在 / `show_progress=False` 走 `placeholder.code` 分支

**红绿证**：修复前 `3 failed, 3 passed` → 修复后 `6 passed`。

**视觉无回归验证**（浏览器实测，真启动 Streamlit 并排渲染旧内联模板与新组件）：

两个块的 `outerHTML` 与全部 computed style **逐项相同**——背景 `rgb(26,34,52)`、边框 `1px rgb(45,55,72)`、圆角 `12px`、内边距 `16px`、字号 `13.6px`、`white-space: pre-wrap`、`max-height: 400px`、`overflow-y: auto`。**确认无视觉回归。**

顺带发现一个**既有**现象（两版完全相同，非本次引入）：流式代码里以 4 空格开头的行会被 CommonMark 当成缩进代码块，在深色方框内再嵌一层 Streamlit 代码块。已列为未处理项。

**全量回归**：144 passed（原 139 + 新增 5）。

## 已删除（2026-09-12）

`render_streaming_code` 已接入后，剩下的死代码**无处可"接入"**，按删除路线收敛：

| 删除项 | 位置 | 为什么无处可并 |
|---|---|---|
| `StreamingDisplay` 类 | `streaming_display.py` | chat.py 没有对应的生命周期管理器，属**独有功能** |
| `render_streaming_text` | `streaming_display.py` | chat.py 只流式渲染代码，无文本流场景 |
| `render_agent_streaming_status` | `streaming_display.py` | chat.py 用的是 `ui_components.render_agent_pipeline`，**粒度不同** |
| `agent_status.py` | 整模块 107 行 | 渲染 7 个*状态*，比在用的 `render_agent_pipeline`（4 个 *Agent*）更贴合状态机——属**替代实现**而非重复。且用的是 `gray`/`#e8f5e9` 等浅色，写于主题系统上线（`1f0e8df`，2026-05-08）**之前**，直接用会错色 |
| `code_display.py` | 整模块 53 行 | `render_code_display` 与 `chat.py` 的复制按钮块近乎逐字重复，但 chat.py 用的是带样式的 `render_code_block`，组件用的是朴素 `st.code`——接入等于**降级外观** |

顺带把 `frontend/components/__init__.py` 里导出这些无人用名字的语句一并清掉——正是它制造了「这是个在用的模块」的假象。

**这不损失能力**：git 历史里全都在；先例是 2026-09-10 以同样理由删除 Memory/VectorMemory 子系统（见 `PROGRESS.md` 修改历史）。

**注意**：`render_streaming_text` 与 `render_agent_streaming_status` 被删时**其渲染缺陷未修**——删除取代了修复。若将来要从 git 捞回来复用，先补上这两处。

## 相关文件

- `frontend/components/streaming_display.py`（`render_streaming_code` 已修并接入）
- `frontend/pages/chat.py`（删除内联实现，改用组件）
- `tests/test_streaming_display_html.py`（新增）
- `frontend/components/agent_status.py`、`frontend/components/code_display.py`（仍为死代码）
- `frontend/components/__init__.py`（导出了无人用的名字）
- `PLAN_简历展示完善.md:217-233`（未执行的原计划）
- `PROGRESS.md:151/195/196/209`（对死代码做过的 XSS 加固记录）
