# 流式生成进度显示被渲染成 HTML 源码

> 创建时间: 2026-09-12 | 状态: 🔴未解决

## 问题描述

代码生成过程中，流式进度区域显示的是**裸 HTML 源码**而不是渲染后的文本：

```
{生成中的代码文本}

<div style="font-size: 12px; color: #888;">
    📝 生成中... 1234 字符
</div>
```

用户看到的是 `📝 生成中...` 那段的标签源码，而不是灰色小字。

## 出现原因

与 ISSUE-010 **同一根因**——HTML 字符串中间夹空行：

`frontend/components/streaming_display.py:82`

```python
placeholder.markdown(
    f"""
    {html_lib.escape(full_text)}

    <div style="font-size: 12px; color: #888;">
        📝 生成中... {char_count} 字符
    </div>
    """,
    unsafe_allow_html=True,
)
```

`{full_text}` 后紧跟一个空行 → CommonMark 在空行处终止 HTML 块 → 其后**带 4 空格缩进**的 `<div …>` 行被解析成缩进代码块。

已用真实渲染器判定：`MarkdownIt("commonmark", {"html": True}).render(text.lstrip())` 输出含 `&lt;` → **确认命中代码块**。

## 解决方案

两种，任选：

1. **推荐**：把 `ui_components._render_html` 提为公共工具（如 `frontend/utils/html_render.py`），本处一并改走它——这样同类问题只在一处收口
2. 就地去掉模板里的空行（`{full_text}` 与 `<div …>` 之间那行）

注意**不要**用 `textwrap.dedent`：`full_text` 是用户代码，内嵌行零缩进，会让公共前缀算成空串、dedent 失效（详见 ISSUE-010）。

## 验证方式

1. 单测：用 `markdown_it(text.lstrip())` 渲染本组件的输出，断言不含 `&lt;`
2. 端到端：真启动应用 → 生成页发起一次生成 → 检查进度区域 DOM 中 `<pre><code>` 数量为 0，且「📝 生成中…」是真实元素文本

## 相关文件

- `frontend/components/streaming_display.py:82`（另 `:51`、`:90`、`:231` 也有 `unsafe_allow_html`，本次未判定，修复时一并核）
- `frontend/components/ui_components.py`（`_render_html` 参考实现）
- `issues/ISSUE-010-Streamlit-HTML渲染成代码块.md`（同一根因）
