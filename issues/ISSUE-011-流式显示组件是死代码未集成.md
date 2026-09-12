# 流式显示组件是死代码（原判"渲染成源码"不成立）

> 创建时间: 2026-09-12 | 状态: 🔴未解决（**性质已更正**）
>
> **重要更正**：本工单原判「用户看到裸 HTML 源码」——**不成立**。
> 该模块**从未被任何代码调用**，渲染成什么样用户都看不到。
> 真正的问题是它属于 CLAUDE.md 明令必须报告的「设计了但未集成」。
> 触发更正的经过：修复前核对调用点，发现零调用，遂推翻原判。

## 问题描述

`frontend/components/streaming_display.py`（231 行）**没有任何调用点**：

- `render_streaming_code` / `StreamingDisplay` 只在 `frontend/components/__init__.py:5,11,12` 被 import 与列入 `__all__`，**无实际调用者**
- `render_streaming_text`、`render_agent_streaming_status` **连 `__init__.py` 都没导出**
- `tests/` 下零引用

**同类问题不止这一个模块**——`frontend/components/` 下 4 个模块有 3 个是死代码：

| 模块 | 行数 | 状态 |
|---|---|---|
| `ui_components.py` | 686 | ✅ 被 `app.py` + 3 个页面引用 |
| `streaming_display.py` | 231 | ❌ 死代码 |
| `agent_status.py` | 107 | ❌ 死代码 |
| `code_display.py` | 53 | ❌ 死代码 |

**为何会这样**：`PLAN_简历展示完善.md:217-233` 明确计划「**在 chat.py 中使用** `render_streaming_code`」，但该步从未落地——`frontend/pages/chat.py:136-157` 自己内联实现了一套流式显示。两套并存，页面用的是内联那套。

**代价已经发生过**：`PROGRESS.md:151/195/196/209` 记录了对 `streaming_display` 的多轮 XSS 加固（最后改动 2026-06-28「彻底修复3个遗留安全问题」）——**这些工作量全花在了没人执行的代码上**。

## 出现原因

计划与实现脱节：计划文档写明了接入点，实现时改成了内联写法，但组件模块被保留下来，且 `__init__.py` 把它导出，制造了「这是个在用的模块」的假象。

## 解决方案（待决策）

三条路，需产品/维护者定夺：

1. **删除**（推荐）：连同 `__init__.py` 的导出一起删。chat.py 的内联实现已覆盖需求，保留无人用的副本只会持续误导（PROGRESS.md 已在声称它有 XSS 加固）。
2. **接入**：让 `chat.py` 改用 `render_streaming_code` 替换内联实现，消除重复。**注意**：接入前必须先修掉它的 3 处渲染缺陷（见下），否则等于把坏代码换上去。
3. **保留但修渲染缺陷**：不接入，只让代码本身正确。

### 无论选哪条，这几处渲染缺陷都是真的（已用真实渲染器判定）

| 位置 | 缺陷 | 判定 |
|---|---|---|
| `:42` `render_streaming_code` | 闭合代码围栏 ` ``` ` 被缩进 16 空格 → 围栏永不闭合，整段进代码块 | ❌ |
| `:82` `render_streaming_text` | `{full_text}` 后夹空行 → HTML 块被终止 | ❌ |
| `:231` `render_agent_streaming_status` | `+=` 拼接的每段 f-string 以纯空白行结尾 → 拼接后产生空行 | ❌ |

判定方法：`MarkdownIt("commonmark", {"html": True}).render(text.lstrip())`，输出含 `&lt;` 即命中。

**注意**：`render_streaming_text`（`:82`）不能简单套用 `ui_components._render_html` 的「去空行」变换——它会误伤流式文本里的空行（该处插值的是**用户内容**且嵌在块内，不像 `render_code_block` 有空号 `<span>` 保护）。正确做法是**修模板**（去掉那行空行），而不是在渲染时统一剥空行。

## 验证方式

- 若选「删除」：删后 `python -m pytest -q` 全绿，且 `grep -rn render_streaming_code` 除了 git 历史外零命中
- 若选「接入/保留」：对每个函数用真实渲染器断言输出不含 `&lt;`；E2E 走一次真实生成确认进度显示正常

## 相关文件

- `frontend/components/streaming_display.py`（`:42` / `:82` / `:231`）
- `frontend/components/agent_status.py`、`frontend/components/code_display.py`（同为死代码）
- `frontend/components/__init__.py`（导出了无人用的名字）
- `frontend/pages/chat.py:136-157`（内联的流式实现，实际在用）
- `PLAN_简历展示完善.md:217-233`（未执行的原计划）
- `PROGRESS.md:151/195/196/209`（对死代码做过的 XSS 加固记录）
