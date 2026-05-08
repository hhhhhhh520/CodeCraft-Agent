"""代码生成交互页面 - CodeCraft Agent 深色科技主题"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.styles.theme import apply_global_styles, THEME_COLORS
from frontend.components.ui_components import (
    render_hero_section,
    render_agent_pipeline,
    render_code_block,
    render_score_gauge,
    render_issue_list,
    render_token_usage,
    render_empty_state,
)
from frontend.utils.session import (
    SessionManager,
    ConfigManager,
    AgentState,
    GenerationResult,
)

# 页面配置
st.set_page_config(
    page_title="代码生成 - CodeCraft Agent",
    page_icon="💬",
    layout="wide",
)

# 应用全局样式
apply_global_styles()

# 初始化会话状态
SessionManager.init_session()

# 页面标题
render_hero_section(
    title="代码生成",
    subtitle="输入需求，多Agent协作生成高质量代码",
    description=""
)

# ===== 需求输入区域 =====
st.markdown("### 需求描述")

requirement = st.text_area(
    "需求描述",
    placeholder="例如：实现一个快速排序算法\n或者：写一个函数计算斐波那契数列\n\n支持中英文输入，详细描述效果更好",
    height=120,
    key="requirement_input",
    max_chars=10000,
    label_visibility="collapsed",
)

# 生成按钮
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate_btn = st.button("🚀 生成代码", type="primary", use_container_width=True)

# ===== Agent状态展示 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Agent 协作状态")

status_placeholder = st.empty()
with status_placeholder.container():
    render_agent_pipeline()

# ===== 处理生成请求 =====
if generate_btn and requirement:
    # 输入验证
    from backend.utils.input_validator import validate_requirement
    is_valid, cleaned_requirement, error_msg = validate_requirement(requirement)
    if not is_valid:
        st.error(f"❌ 输入验证失败: {error_msg}")
        st.stop()

    requirement = cleaned_requirement

    # 检查配置
    config = st.session_state.config
    if not config.get("api_key"):
        st.error("❌ 请先在设置页面配置 API Key")
        st.stop()

    # 导入后端模块
    try:
        from backend.core import Orchestrator, SharedContext, Memory
        from backend.llm import LLMFactory, TokenManager
        from backend.tools import ASTParser, CodeExecutor
        from backend.agents import (
            CodeGeneratorAgent,
            CodeReviewerAgent,
            DebuggerAgent,
            TestGeneratorAgent,
        )
    except ImportError as e:
        st.error(f"❌ 导入后端模块失败: {e}")
        st.stop()

    # 创建LLM
    api_key = config["api_key"]
    api_type = config.get("api_type", "deepseek")

    if api_type == "deepseek":
        base_url = "https://api.deepseek.com/v1"
        model = "deepseek-chat"
    else:
        base_url = None
        model = config.get("model", "gpt-4o-mini")

    try:
        token_manager = TokenManager(max_tokens=128000)
        llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url, token_manager=token_manager)
    except Exception as e:
        st.error(f"❌ 创建LLM失败: {e}")
        st.stop()

    # 创建工具
    tools = [ASTParser(), CodeExecutor(timeout=30)]

    # 创建记忆系统
    memory = Memory(enable_vector=True)

    # 创建Agents
    generator = CodeGeneratorAgent(llm=llm, tools=tools, memory=memory)
    agents = {"generator": generator}

    if not config.get("fast_mode", False):
        reviewer = CodeReviewerAgent(llm=llm, tools=tools, memory=memory)
        debugger = DebuggerAgent(llm=llm, tools=tools, memory=memory)
        test_generator = TestGeneratorAgent(llm=llm, tools=tools, memory=memory)
        agents["reviewer"] = reviewer
        agents["debugger"] = debugger
        agents["test_generator"] = test_generator

    context = SharedContext()
    orchestrator = Orchestrator(agents=agents, context=context)

    completed_agents = []

    try:
        # Step 1: 代码生成
        SessionManager.set_agent_state(AgentState.GENERATING)
        with status_placeholder.container():
            render_agent_pipeline(current_agent="Generator", completed_agents=completed_agents)

        # 流式生成代码
        generator = agents["generator"]
        messages = [
            {"role": "system", "content": generator.SYSTEM_PROMPT},
            {"role": "user", "content": f"请实现：{requirement}"},
        ]

        # 流式显示区域
        code_placeholder = st.empty()
        full_code = ""

        for chunk in llm.stream(messages):
            full_code += chunk
            # 简化显示，避免频繁更新
            code_placeholder.markdown(f"""
            <div style="
                background: {THEME_COLORS['bg_tertiary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 12px;
                padding: 1rem;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                color: {THEME_COLORS['text_primary']};
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            ">{full_code}</div>
            """, unsafe_allow_html=True)

        # 提取代码块
        import re
        pattern = r"```python\s*\n(.*?)\n```"
        matches = re.findall(pattern, full_code, re.DOTALL)
        code = matches[0] if matches else full_code

        completed_agents.append("Generator")

        # Step 2: 代码审查
        issues = []
        review_score = 100
        test_code = ""

        if not config.get("fast_mode", False) and "reviewer" in agents:
            SessionManager.set_agent_state(AgentState.REVIEWING)
            with status_placeholder.container():
                render_agent_pipeline(current_agent="Reviewer", completed_agents=completed_agents)

            reviewer = agents["reviewer"]
            review_result = reviewer.process({"code": code}, context.data)
            issues = review_result.get("issues", [])
            review_score = review_result.get("score", 100)

            completed_agents.append("Reviewer")

            # Step 3: 修复问题
            if not review_result.get("passed", True) and "debugger" in agents:
                SessionManager.set_agent_state(AgentState.FIXING)
                with status_placeholder.container():
                    render_agent_pipeline(current_agent="Debugger", completed_agents=completed_agents)

                debugger = agents["debugger"]
                fix_result = debugger.process({"code": code, "issues": issues}, context.data)
                code = fix_result.get("fixed_code", code)

                completed_agents.append("Debugger")

            # Step 4: 生成测试
            if "test_generator" in agents:
                SessionManager.set_agent_state(AgentState.TESTING)
                with status_placeholder.container():
                    render_agent_pipeline(current_agent="TestGenerator", completed_agents=completed_agents)

                test_generator = agents["test_generator"]
                test_result = test_generator.process({"code": code}, context.data)
                test_code = test_result.get("test_code", "")

                completed_agents.append("TestGenerator")

        # 完成
        SessionManager.set_agent_state(AgentState.DONE)
        with status_placeholder.container():
            render_agent_pipeline(current_agent=None, completed_agents=completed_agents)

        st.success("✅ 代码生成完成！")

        # 保存结果
        generation_result = GenerationResult(
            requirement=requirement,
            code=code,
            review_score=review_score,
            issues=issues,
            agent_state=AgentState.DONE,
        )
        SessionManager.set_generation_result(generation_result)
        SessionManager.set_agent_state(AgentState.DONE)
        SessionManager.add_to_history(generation_result)

    except Exception as e:
        SessionManager.set_agent_state(AgentState.IDLE)
        st.error(f"❌ 生成失败: {e}")

# ===== 生成结果展示 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 生成结果")

result = st.session_state.generation_result

if result:
    col1, col2 = st.columns([3, 1])

    with col1:
        # 代码展示
        render_code_block(result.code, title="generated_code.py")

    with col2:
        # 评分展示
        if result.review_score and not st.session_state.config.get("fast_mode", False):
            render_score_gauge(result.review_score)

            # Token使用量
            render_token_usage(used=5000, total=128000)

    # 问题列表
    if result.issues:
        st.markdown("<br>", unsafe_allow_html=True)
        render_issue_list(result.issues)

    # 测试代码
    if result.test_code:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 测试代码")
        render_code_block(result.test_code, title="test_generated.py")

    # 复制按钮
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("📋 复制代码", use_container_width=True):
            try:
                import pyperclip
                pyperclip.copy(result.code)
                st.toast("代码已复制到剪贴板!", icon="✅")
            except Exception:
                st.session_state.show_copy_text = True

    if st.session_state.get("show_copy_text", False):
        st.text_area("复制以下文本:", result.code, height=100, key="copy_text_area")
        if st.button("关闭", key="close_copy_btn"):
            st.session_state.show_copy_text = False
            st.rerun()

else:
    render_empty_state(
        icon="💻",
        title="等待输入",
        description="输入你的代码需求，点击生成按钮开始"
    )
