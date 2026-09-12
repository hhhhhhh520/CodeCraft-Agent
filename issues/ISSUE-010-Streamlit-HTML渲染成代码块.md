# Streamlit 页面大量 HTML 被渲染成源码文本

> 创建时间: 2026-09-12 | 状态: 🔴未解决

## 问题描述

首页与生成页的**主内容区大面积以裸 HTML 源码形式显示**。实测首页 `<pre>` 代码块共 10 个，**其中 9 个装的是原始 HTML 源码**——包括主标题 hero、4 张核心特性卡、4 张项目指标卡、生成页的 4-Agent 协作流水线。

用户看到的是 `<!-- 主标题 --> <h1 style="...">CodeCraft Agent</h1>` 这样的文本，而不是渲染后的样式。

侧栏的同类 HTML 却渲染正常。

## 出现原因

**根因：HTML 字符串中间夹了空行。**

CommonMark 的 HTML 块规则：以块级标签开头的 HTML 块**遇到空行即终止**；终止之后，那些 **4 空格缩进**的内容行会被解析为「缩进代码块」，于是变成 `<pre><code>` 输出。

实测对比（用 Streamlit 底层 `markdown_it` 跑真实字符串）：

| 字符串 | 空行位置 | 渲染结果 |
|---|---|---|
| 侧栏 HTML（295 字符） | 只在**首尾**（7 行里 2 个空行都在边界） | ✅ 正常 HTML |
| 主区 hero HTML（2173 字符） | **夹在中间**（66 行里 7 个空行） | ❌ `<pre><code>` |

已排除的两个错误方向（勿再往这两处找）：

- **不是** `unsafe_allow_html=True` 缺失——`ui_components.py` 里 13 处 `st.markdown` **全部带**该参数（AST 逐个核过）
- **不是** HTML 注释——只删注释不删空行，主区**仍然是** `<pre>`；去掉空行后两段都正常

## 解决方案

去掉 HTML 字符串内部的空行（或改用 `st.html()` / 单行拼接 / 先 `textwrap.dedent` 再消除空行）。改动集中在 `ui_components.py` 的 `render_hero_section` / `render_feature_card` / `render_stat_card` / `render_agent_pipeline`。

## 验证方式

重新加载页面，统计 `<pre>` 中内容含 `<` 或 `<!--` 的块数应为 **0**；hero 的 `<h1>` 应是真实 DOM 节点而非代码块内容。

## 相关文件

- `frontend/components/ui_components.py`
- `frontend/app.py:88`（调用 render_hero_section 起始行；L90 是调用内的 `subtitle=` 参数行）
- `frontend/pages/chat.py`（调用 render_agent_pipeline）

## 修复时需一并留意的既有隐患

`render_hero_section`（`ui_components.py:47 / :57 / :60`）把 `{title}` / `{subtitle}` / `{description}` **原样插进 HTML，未走 `html_lib.escape()`**；同文件 `render_history_card:546` 对用户输入 `requirement` 则是转义后才插入。

**当前不可利用**：已逐个核对全部调用点（`frontend/app.py:88`、`frontend/pages/chat.py:42`、`frontend/pages/history.py:40`、`frontend/pages/settings.py:45`），传入的都是硬编码字符串字面量，无用户可控数据到达插值点。

但有个机制性事实值得记：这些 HTML 块**眼下正因为空行 bug 而渲染失败**，被降级成惰性的转义文本；本 ISSUE 修复后它们会作为真实 HTML 渲染。也就是说，修复会移走一个「因 bug 而意外存在」的屏障。当前无危害，但若将来这些参数接入动态内容，未转义的插值就会变成存活的内联注入点——届时须先 `html_lib.escape()` 或改用 `st.html()` 受控渲染。
