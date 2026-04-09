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
)

# 生成按钮
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    generate_btn = st.button("🚀 生成代码", type="primary", use_container_width=True)

# Agent状态展示
st.markdown("---")
st.markdown("### Agent 协作状态")
render_agent_status(st.session_state.agent_state)

# 处理生成请求
if generate_btn and requirement:
    # 检查配置
    config = st.session_state.config
    if not config.get("api_key"):
        st.error("❌ 请先在设置页面配置 API Key")
        st.stop()

    # 导入后端模块
    try:
        from backend.core import Orchestrator, SharedContext
        from backend.llm import LLMFactory
        from backend.agents import CodeGeneratorAgent, CodeReviewerAgent, DebuggerAgent
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
        llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url)
    except Exception as e:
        st.error(f"❌ 创建LLM失败: {e}")
        st.stop()

    # 创建Agents
    generator = CodeGeneratorAgent(llm=llm, tools=[])
    agents = {"generator": generator}

    if not config.get("fast_mode", False):
        reviewer = CodeReviewerAgent(llm=llm, tools=[])
        debugger = DebuggerAgent(llm=llm, tools=[])
        agents["reviewer"] = reviewer
        agents["debugger"] = debugger

    context = SharedContext()
    orchestrator = Orchestrator(agents=agents, context=context)

    # 执行生成
    with st.spinner("正在生成代码..."):
        try:
            # 调用后端
            result = orchestrator.process_request(requirement)

            # 保存结果
            generation_result = GenerationResult(
                requirement=requirement,
                code=result.get("code", ""),
                review_score=result.get("review_score", 100),
                issues=result.get("issues", []),
                agent_state=AgentState.DONE,
            )
            SessionManager.set_generation_result(generation_result)
            SessionManager.set_agent_state(AgentState.DONE)

            # 添加到历史
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
