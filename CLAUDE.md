# CLAUDE.md — CodeCraft Agent

多 Agent 协作的 Python 代码生成助手（Generator → Reviewer → Debugger → TestGenerator）。
双入口：CLI（Typer）+ Web（Streamlit）。技术细节见 `TECHNICAL_ANALYSIS_REPORT.md`；
进度与结构见 `PROGRESS.md`。

## 命令

```bash
pytest -q                      # 全量（145 个）
ruff check --no-cache frontend/ backend/
streamlit run frontend/app.py --server.port 8501
```

## 红线

- **改 `frontend/pages/**` 后必须跑 `tests/test_frontend_pages.py`**。页面代码在 Streamlit 里才执行，
  纯后端测试永远拦不住页面里的 `NameError`/`AttributeError`——2026-09-12 实测：118 个后端测试全绿，
  而生成功能因一行变量名写错 100% 崩溃，存活了 5 个月。
- **给页面写 AppTest 测试时，先确认页面路径上有没有 `Path.home()` 落盘**（如 `HistoryManager`
  写 `~/.codecraft/history.json`），有就必须 `monkeypatch` 到 `tmp_path`。AppTest 里
  `st.session_state.history` 初始为空，`save` 是**覆盖**不是追加——不隔离会冲掉用户真实文件（已发生过一次）。

## Streamlit 渲染陷阱（踩过多次，改 UI 前必读）

`st.markdown(html, unsafe_allow_html=True)` 的字符串受 **CommonMark** 规则约束，违反不会报错，
只会静默把整段变成 `<pre><code>` 源码显示：

1. **HTML 块内不能有游离空行**——`<div>` 属 type-6 块，**遇空行即终止**，其后带缩进的行会被
   当成「缩进代码块」。整段模板要么无空行，要么把换行编码掉。
2. **例外**：`<style>` / `<script>` / `<pre>` / `<textarea>` 属 type-1 块，由**闭合标签**结束，
   **空行不终止**。`frontend/styles/theme.py` 的全局 CSS 就是靠这点才没坏。
3. **首行不能缩进超过 3 空格**——模板别写成 `f"""` 后换行再缩进 4 空格。
   `ui_components._render_html()` 就是为收口这条而存在，**新的 HTML 渲染一律走它**。
4. **用户内容里的换行要编码成 `&#10;`** 再塞进模板（`streaming_display.render_streaming_code` 的做法），
   否则用户内容里的空行会截断 HTML 块。
5. **Streamlit 会净化 HTML**：`<pre>` 标签会被整个剥掉、事件处理器（`onerror` 等）会被剥掉。
   所以**不能靠 `<pre>` 承载**，也不能把"能执行"当作防护假设。

### 验证渲染问题的正确方法

- **单元测试**：`MarkdownIt("commonmark", {"html": True}).render(text.lstrip())`。
  **必须 `.lstrip()`**——Streamlit 会 lstrip 整个 body，不 lstrip 的 markdown_it 更严格，
  会把「4 空格缩进 + 无空行」（实际正常）误判成代码块，产生**假失败**。
  四种「缩进 × 空行」组合已实测逐一比对，`markdown_it(text.lstrip())` 4/4 吻合真实 Streamlit。
- **但 markdown_it 覆盖不到 Streamlit 的净化行为**（它不净化）。凡是"某个标签/属性能不能用"这类问题，
  **只能靠浏览器实测**。已因此误判过一次（`<pre>` 方案单测通过、真实环境标签被剥掉）。

## 架构约定

- **`create_orchestrator()`（`backend/core/factory.py`）是唯一装配入口**，CLI 与 Streamlit 都走它。
- **Agent 的 LLM 挂在实例上**：`agent.llm`（`backend/core/agent.py:27`）。页面取流用
  `generator.llm.stream(messages)`。
- **共享上下文是 `orchestrator.context`**（`SharedContext`），传给 agent 时取 `.context.data`。
- **UI 组件只在 `frontend/components/ui_components.py` 与 `streaming_display.py`**。
  `__init__.py` 不导出名字，各页面直接按子模块导入。
- 领域问题（崩溃、静默失败、渲染异常）记录到 `issues/ISSUE-NNN-简述.md`。

## 深入文档

| 文档 | 内容 |
|---|---|
| `README.md` | 安装、使用、架构图、项目亮点 |
| `PROGRESS.md` | 各 Phase 完成情况、当前结构、修改历史 |
| `TECHNICAL_ANALYSIS_REPORT.md` | 2026-04-15 的分析快照（**已标注为历史，勿按其中代码执行**）|
| `docs/assets/architecture.md` | 5 张详细架构图 |
| `issues/` | 13 份工单，含根因与验证方式 |
