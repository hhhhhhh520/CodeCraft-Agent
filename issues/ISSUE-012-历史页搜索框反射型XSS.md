# 历史页搜索框反射型 XSS：搜索词未转义直接插入 HTML

> 创建时间: 2026-09-12 | 状态: 🔴未解决
>
> **安全类问题**。发现于 ISSUE-010 的提交前审查（攻击者视角 subagent），与本轮改动无关，属**既有缺陷**。

## 问题描述

历史记录页（`frontend/pages/history.py`）的搜索框内容**未做 HTML 转义**就被插进交给 `st.markdown(..., unsafe_allow_html=True)` 的 f-string，构成反射型 XSS。

在搜索框输入：

```html
<img src=x onerror=alert(document.cookie)>
```

由于该词匹配不到任何记录，会走进「未找到匹配」分支（`history.py:116` 的 `if not history and search_query:`），上面那段 HTML 被作为**真实 HTML 渲染**，`onerror` 立即执行。

## 出现原因

`frontend/pages/history.py:117-125`

```python
if not history and search_query:
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 2rem;
        color: {THEME_COLORS['text_muted']};
    ">
        未找到匹配 "{search_query}" 的记录      # ← L123 未转义
    </div>
    """, unsafe_allow_html=True)
```

`search_query` 来自 `history.py:52` 的 `st.text_input`，是**用户可控输入**。

**同文件内已有正确写法可对照**：`history.py:172` 渲染 `issues` 时用的是
`html_lib.escape(str(issue))`；`render_history_card` 对 `requirement` 也做了转义。
即这不是"不知道该转义"，而是**漏了一处**。

**为何长期未被发现**：这段代码块内**不含空行**，因此一直是正常渲染的——ISSUE-010 那个 bug 反而"意外保护"了含空行的块（把它们变成惰性文本）。本处不在此列，从始至终都是活的。

## 解决方案

最小修法（一行）：

```python
未找到匹配 "{html_lib.escape(search_query)}" 的记录
```

并确认文件顶部已 `import html as html_lib`。

**建议一并做**：这个文件还有 5 处直接 `st.markdown(..., unsafe_allow_html=True)`，修复时应**逐个核对每个插值是否来自用户输入**，而不是只补这一处——同类漏点往往成串出现。

## 验证方式

1. 单测：构造 `search_query = '<img src=x onerror=1>'`，渲染后断言输出中**不含**该原始标签（应含 `&lt;img`）
2. 端到端：真启动应用 → 历史页搜索框输入 `<img src=x onerror=alert(1)>` → 页面不应弹出 alert，DOM 中应显示为文本
3. 反向验证：修复前先跑一次，确认 alert 真的弹出（否则证明不了这是真漏洞）

## 相关文件

- `frontend/pages/history.py:117-125`（`search_query` 插值在 `:123`）
- `frontend/pages/history.py:52`（`search_query` 来源）
- `frontend/pages/history.py:172`（同文件正确转义写法，可对照）
- `frontend/utils/session.py`（`html_lib` 导入惯例参考）
