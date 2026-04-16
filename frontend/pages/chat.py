"""代码生成交互页面"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.utils.session import (
    SessionManager,
    ConfigManager,
    AgentState,
    GenerationResult,
)
from frontend.components.agent_status import render_agent_status, render_review_score
from frontend.components.code_display import render_code_with_issues

# 页面配置
st.set_page_config(
    page_title="代码生成 - CodeCraft Agent",
    page_icon="💬",
)

# 初始化会话状态
SessionManager.init_session()

# 页面标题
st.title("💬 代码生成")
st.markdown("输入你的代码需求，多Agent协作生成高质量代码")

# 需求输入
requirement = st.text_area(
    "需求描述",
    placeholder="例如：实现一个快速排序算法\n或者：写一个函数计算斐波那契数列",
    height=150,
    key="requirement_input",
    max_chars=10000,  # 限制最大字符数
)

# 生成按钮
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate_btn = st.button("🚀 生成代码", type="primary", use_container_width=True)

# Agent状态展示（动态更新）
st.markdown("---")
st.markdown("### Agent 协作状态")
status_placeholder = st.empty()
with status_placeholder.container():
    render_agent_status(st.session_state.agent_state)

# 处理生成请求
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
        # 创建 TokenManager
        token_manager = TokenManager(max_tokens=128000)
        llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url, token_manager=token_manager)
    except Exception as e:
        st.error(f"❌ 创建LLM失败: {e}")
        st.stop()

    # 创建工具
    tools = [ASTParser(), CodeExecutor(timeout=30)]

    # 创建记忆系统
    memory = Memory(enable_vector=True)

    # 创建Agents（注入 tools 和 memory）
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

    # Agent列表
    all_agents = ["Generator", "Reviewer", "Debugger", "TestGenerator"]
    completed_agents = []

    try:
        # Step 1: 代码生成
        SessionManager.set_agent_state(AgentState.GENERATING)
        with status_placeholder.container():
            render_agent_status(AgentState.GENERATING)

        # 使用流式生成
        from backend.agents.code_generator import CodeGeneratorAgent

        generator = agents["generator"]
        messages = [
            {"role": "system", "content": generator.SYSTEM_PROMPT},
            {"role": "user", "content": f"请实现：{requirement}"},
        ]

        # 流式显示代码
        code_placeholder = st.empty()
        full_code = ""

        for chunk in llm.stream(messages):
            full_code += chunk
            code_placeholder.code(full_code, language="python")

        # 提取代码块
        import re
        pattern = r"```python\s*\n(.*?)\n```"
        matches = re.findall(pattern, full_code, re.DOTALL)
        code = matches[0] if matches else full_code

        completed_agents.append("Generator")

        # Step 2: 代码审查（如果未启用快速模式）
        issues = []
        review_score = 100
        test_code = ""

        if not config.get("fast_mode", False) and "reviewer" in agents:
            # 更新状态为审查中
            SessionManager.set_agent_state(AgentState.REVIEWING)
            with status_placeholder.container():
                render_agent_status(AgentState.REVIEWING)

            reviewer = agents["reviewer"]
            review_result = reviewer.process({"code": code}, context.data)
            issues = review_result.get("issues", [])
            review_score = review_result.get("score", 100)

            completed_agents.append("Reviewer")

            # Step 3: 修复问题（如果有）
            if not review_result.get("passed", True) and "debugger" in agents:
                # 更新状态为修复中
                SessionManager.set_agent_state(AgentState.FIXING)
                with status_placeholder.container():
                    render_agent_status(AgentState.FIXING)

                debugger = agents["debugger"]
                fix_result = debugger.process({"code": code, "issues": issues}, context.data)
                code = fix_result.get("fixed_code", code)

                completed_agents.append("Debugger")

            # Step 4: 生成测试（如果有 test_generator）
            if "test_generator" in agents:
                test_generator = agents["test_generator"]
                test_result = test_generator.process({"code": code}, context.data)
                test_code = test_result.get("test_code", "")
                completed_agents.append("TestGenerator")

        # 完成
        SessionManager.set_agent_state(AgentState.DONE)
        with status_placeholder.container():
            render_agent_status(AgentState.DONE)

        st.success("✅ 代码生成完成！")

        # 显示 Token 使用情况
        remaining = token_manager.get_remaining()
        st.info(f"📊 Token 使用量: {token_manager.current_usage:,} / {token_manager.max_tokens:,} (剩余: {remaining:,})")

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

# 显示生成结果
st.markdown("---")
st.markdown("### 生成结果")

result = st.session_state.generation_result
if result:
    # 显示审查评分
    if result.review_score and not st.session_state.config.get("fast_mode", False):
        render_review_score(result.review_score)

    # 显示代码
    render_code_with_issues(result.code, result.issues)
else:
    st.info("👆 输入需求并点击生成按钮开始")
