# Streamlit 页面大量 HTML 被渲染成源码文本

> 创建时间: 2026-09-12 | 状态: 🟢已解决（2026-09-12）
>
> **修复过程更正了一条初判**：原文说受影响的是 hero / 特性卡 / 指标卡 / 流水线 4 个组件——
> 实际受影响的是**所有块内夹了空行的模板**（单测 9/14 红）。无空行的组件（token 用量、
> 空状态、配置状态）**本来就是正常的**，不受影响。
>
> 另有一条**我修到一半写错又改回来**的结论，值得记下：我一度据 Python `markdown_it` 判断
> "4 空格缩进本身也会导致代码块"，并据此写了更正。**那是错的**——`markdown_it` 不比
> Streamlit 多做一步 `lstrip`，所以比真实渲染器严格。做了受控实验才纠正过来，详见下节。

## 问题描述

首页与生成页的**主内容区大面积以裸 HTML 源码形式显示**。实测首页 `<pre>` 代码块共 10 个，**其中 9 个装的是原始 HTML 源码**——包括主标题 hero、4 张核心特性卡、4 张项目指标卡、生成页的 4-Agent 协作流水线。

用户看到的是 `<!-- 主标题 --> <h1 style="...">CodeCraft Agent</h1>` 这样的文本，而不是渲染后的样式。

侧栏的同类 HTML 却渲染正常——因为侧栏那个块**没有夹空行**。

## 出现原因

**根因：HTML 字符串中间夹了空行。**

CommonMark 的 HTML 块规则：以块级标签开头的 HTML 块**遇到空行即终止**；终止之后，那些**仍带 4 空格缩进**的内容行会被解析为「缩进代码块」，于是整段变成 `<pre><code>` 输出。

**「缩进 + 空行」两个条件同时成立才致命**——这是受控实验（真启动 Streamlit，Playwright 读真实 DOM）测出来的：

| 用例 | 缩进 | 中间空行 | Streamlit 实测 |
|---|---|---|---|
| A | 4 空格 | 无 | ✅ 正常 HTML |
| B | 4 空格 | **有** | ❌ 缩进代码块 |
| C | 无 | 无 | ✅ 正常 HTML |
| D | 无 | **有** | ✅ 正常 HTML（空行后的行顶格，各自成新的 HTML 块）|

即：**缩进单独无害**（Streamlit 会 `lstrip` 整个 body，A 因此正常）、**空行单独也无害**（D 因此正常），只有二者叠加才把内容推进缩进代码块。

已排除的两个错误方向（勿再往这两处找）：

- **不是** `unsafe_allow_html=True` 缺失——13 处调用**全部带**该参数（AST 逐个核过）
- **不是** HTML 注释——注释本身无害

### 建模这个行为时的坑（重要）

用 Python `markdown_it` 复现时**必须 `.lstrip()`**，否则它会比 Streamlit 严格：把「4 空格缩进 + 无空行」（真实情况是 ✅）也判成代码块，产生假失败。

验证方式：把四种组合分别喂给 `markdown_it`（不 lstrip / lstrip）与真实 Streamlit，四组对照后确认 **`markdown_it(text.lstrip())` 4/4 吻合真实 Streamlit**。本 ISSUE 的测试就建立在这个模型上。

## 解决方案

在渲染入口统一处理，`frontend/components/ui_components.py` 新增 `_render_html()`：

```python
def _render_html(html: str) -> None:
    lines = [line for line in html.split("\n") if line.strip()]
    if lines:
        lines[0] = lines[0].lstrip()
    st.markdown("\n".join(lines), unsafe_allow_html=True)
```

13 处 `st.markdown(<html>, unsafe_allow_html=True)` 全部改走它。**模板字符串一字未动**——不 dedent、不动内部缩进，避免破坏 `<pre>` 里嵌的代码。

> `textwrap.dedent` 不可用：`render_code_block` 会把用户代码（`\n` 拼接的 `<span>` 行，**本身零缩进**）嵌进模板，导致各行公共缩进前缀被算成空串，`dedent` 变成 no-op。

这样即使以后有人在模板里加空行，也不会再退化。

## 验证方式

新增 `tests/test_ui_components_html.py`：13 个组件各一条参数化用例 + 1 条边界用例，用 `markdown_it(text.lstrip())` 渲染**真实组件函数的输出**（而非手写样例），断言渲染结果里不出现 `&lt;`（出现即说明掉进了代码块），并反向断言目标标签真实存在（防止"什么都没输出"也算通过）。

边界用例专测「用户代码里的空行不能被去空行误伤」——`render_code_block` 每行都带行号 `<span>`，空代码行渲染出来是 `<span ...>  3  </span>` 而非纯空白，因此安全。

**单测红绿证**：

| 版本 | 结果 |
|---|---|
| HEAD（修复前） | **9 failed, 5 passed** |
| 修复后 | **14 passed** |

那 5 个修复前就通过的，正是无空行的组件（`issue_list_empty` / `token_usage` / `empty_state` / `config_status_ok` / `config_status_missing`）——**与真实产品表现一致**，说明测试模型可信、没有假失败。

**浏览器端到端实测**（真启动 `streamlit run frontend/app.py`，Playwright 读真实 DOM）：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `<pre>` 总数 | 10 | 1 |
| HTML 泄漏进代码块的块数 | **9** | **0** |
| `<h1>` 数量 | 1（仅侧栏） | **2**（hero 成为真实 DOM 节点） |
| `<h3>` 数量 | 3 | 7 |
| 页面出现裸 HTML 注释文本 | **true** | **false** |
| 应用级控制台错误 | — | **0** |

修复后剩下的那 1 个 `<pre>` 是首页合法的 ASCII 架构图，非泄漏。

**全量回归**：136 passed（原 122 + 新增 14），零失败。

### 本次只修了 `ui_components.py`——同一 bug 在别处还有实例

修复后对 `frontend/` 做了 AST 全扫（找「HTML 块内夹空行」的调用点），并用真实渲染器逐个判定：

| 文件 | 判定 |
|---|---|
| `frontend/components/streaming_display.py:82` | ❌ **仍会渲染成代码块**（流式生成时的进度显示），已另立工单 |
| `frontend/styles/theme.py:36` | ✅ 正常——以 `<style>` 开头属 CommonMark **type-1 HTML 块**，由闭合标签结束，空行不终止 |
| `app.py` / `pages/history.py` / `pages/settings.py` 等 | 块内无空行，正常 |

**结论：判别这类问题时，不能只看"有没有空行"，还要看首标签是不是 `<style>/<script>/<pre>/<textarea>`——那四类不受空行影响。**

## 修复时需一并留意的既有隐患

`render_hero_section`（`ui_components.py:47 / :57 / :60`）把 `{title}` / `{subtitle}` / `{description}` **原样插进 HTML，未走 `html_lib.escape()`**；同文件 `render_history_card` 对用户输入 `requirement` 则是转义后才插入。

**当前不可利用**：已逐个核对全部调用点（`frontend/app.py:88`、`frontend/pages/chat.py:42`、`frontend/pages/history.py:40`、`frontend/pages/settings.py:45`），传入的都是硬编码字符串字面量，无用户可控数据到达插值点。

但有个机制性事实值得记：这些 HTML 块**在修复前正因为渲染失败**而显示为惰性的转义文本；本 ISSUE 修好后它们才真正作为 HTML 渲染。也就是说，修复移走了一个「因 bug 而意外存在」的屏障。当前无危害，但若将来这些参数接入动态内容，未转义的插值就会变成存活的内联注入点——届时须先 `html_lib.escape()`。

## 相关文件

- `frontend/components/ui_components.py`（新增 `_render_html`，13 处调用点）
- `frontend/app.py:88`（调用 render_hero_section 起始行；L90 是调用内的 `subtitle=` 参数行）
- `frontend/pages/chat.py`（调用 render_agent_pipeline）
- `tests/test_ui_components_html.py`（新增）
