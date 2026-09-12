# 历史页搜索框 HTML 注入（原判「反射型 XSS」过重）

> 创建时间: 2026-09-12 | 状态: 🟢已解决（2026-09-12）
>
> **重要更正**：本工单原判「反射型 XSS，`<img onerror=alert()>` 会执行」——**实测未达成脚本执行**。
> 发现于 ISSUE-010 的提交前审查（攻击者视角 subagent），当时是**静态推断**。
> 按"先复现再修"的要求在浏览器实测后，影响面比原判窄：**HTML 注入成立，脚本执行不成立**。
> 下面「实测结论」一节是逐向量跑出来的原始数据。

## 问题描述

历史记录页的搜索框内容**未做 HTML 转义**就被插进交给 `st.markdown(..., unsafe_allow_html=True)` 的 f-string，用户可以往页面里注入任意 HTML 标签。

## 出现原因

`frontend/pages/history.py:123`（修复前）

```python
if not history and search_query:
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 2rem;
        color: {THEME_COLORS['text_muted']};
    ">
        未找到匹配 "{search_query}" 的记录      # ← 未转义
    </div>
    """, unsafe_allow_html=True)
```

`search_query` 来自 `history.py:52` 的 `st.text_input`，用户可控。

**同文件内已有正确写法可对照**：`history.py:172` 渲染 `issues` 用 `html_lib.escape(str(issue))`；`render_history_card` 对 `requirement` 也做了转义——不是"不知道要转义"，是**漏了一处**。

**还有一个前置条件（原判漏写）**：这段代码在 `else` 分支里，而 `history.py:97` 有 `if not history: render_empty_state(...)` **提前返回**。所以：

- 历史为空 → 根本走不到这段代码（**这也是它长期没被发现的原因之一**）
- 必须"先有一条历史记录 + 搜索一个匹配不到的词"才触发

## 实测结论（Streamlit 1.55 + Playwright，逐向量）

| 向量 | 实测结果 |
|---|---|
| `<img src=x onerror="...">` | 标签存活，但 **`onerror` 被前端净化剥掉** → `<img src="x">`，不执行 |
| `<svg onload="...">` | 不执行 |
| `<script>...</script>` | 不执行（innerHTML 插入的 script 本就不执行） |
| `<details open ontoggle="...">` | 不执行 |
| `<a href="javascript:...">` | **href 属性存活**，但 Streamlit 自动加 `target="_blank" rel="noopener noreferrer"` → 开新标签页，未命中当前页 |
| `<iframe src="https://example.com">` | **存活并加载**（`contentDocument` 跨源不可读 = 确实导航过去了）|

**结论**：

1. **HTML 注入成立** —— 任意标签/属性/样式可注入，`<iframe>` 可加载任意外站（钓鱼、UI 伪造面）
2. **脚本执行未达成** —— 事件处理器被净化，`javascript:` 因 `noopener` 无法命中当前页
3. **不可外部投递** —— `search_query` 不经 URL 传递（grep 确认 app/history 均不读 `query_params`），payload 只能由受害者自己输入 → **自注入**，不是可交付的 XSS

故严重度**低于**原判。真修复点仍是"转义"——净化器行为不属本项目的契约，不该依赖它兜底。

## 解决方案

一处改动：

```python
未找到匹配 "{html_lib.escape(search_query)}" 的记录
```

`html_lib` 在 `history.py:3` 已导入。

**同时核过该文件其余插值**：`unsafe_allow_html` 的三处块（`:77` / `:117` / `:160`）里，除本处外其余插值全是 `THEME_COLORS` 常量、`count`（int）或已转义的 `issues`——**仅此一处漏点**。

## 验证方式

新增 `tests/test_history_page_xss.py`（3 用例，用 AppTest 跑真实历史页）：

1. `test_search_payload_is_escaped_not_injected` —— 注入 payload 后断言渲染串含 `&lt;img` 且**不含** `<img`
2. `test_normal_search_term_still_shown` —— 反向：普通搜索词原样显示，防止转义写过头
3. `test_empty_history_short_circuits` —— 钉住"历史为空时提前返回"这个前置条件

> 测试须先喂一条记录才测得到（因为上述 `if not history:` 提前返回），fixture 里 monkeypatch 掉了 `HistoryManager.load` 并隔离到 `tmp_path`。

**单测红绿证**：修复前 `1 failed, 2 passed` → 修复后 `3 passed`。
（另两条两版都过——它们不依赖本修复，属正常。）

**浏览器端到端实测**（真启动应用 + 真实输入）：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `<img onerror>` 注入后页面 `img` 元素数 | **1** | **0** |
| 「未找到匹配」文案 | `未找到匹配 "" 的记录`（标签被当 HTML 吃掉）| `未找到匹配 "<img src=x onerror=...>" 的记录`（原样可见）|
| `<iframe src=外站>` 页面 `iframe` 元素数 | **1**（且加载） | **0** |

## 复现时的一次事故（记录备查）

复现需要一条历史记录，而 `~/.codecraft/history.json` 当时是空的（生成功能自 2026-04-12 起就崩，从没产生过记录）。为复现**临时写入了一条测试记录**，验证完成后已还原为 `[]`。教训：验证"需要前置数据"的缺陷时，要事先想好数据来源与还原方式。

## 相关文件

- `frontend/pages/history.py:123`（修复点）、`:52`（来源）、`:97`（前置条件）、`:172`（正确写法对照）
- `frontend/pages/history.py:77`、`:117`、`:160`（三处 `unsafe_allow_html` 块，已逐个核过）
- `tests/test_history_page_xss.py`（新增）
