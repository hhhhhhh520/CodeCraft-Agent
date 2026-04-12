"""
Demo 4: 完整工作流演示

演示场景: 完整的代码生成 → 审查 → 修复 → 测试流程
展示能力: 多Agent协作、反馈闭环、状态机管理
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.context import SharedContext
from backend.core.memory import ShortTermMemory
from backend.core.orchestrator import Orchestrator
from backend.core.state import TaskState
from backend.llm.openai_llm import OpenAILLM
from backend.agents.code_generator import CodeGeneratorAgent
from backend.agents.code_reviewer import CodeReviewerAgent
from backend.agents.debugger import DebuggerAgent
from backend.agents.test_generator import TestGeneratorAgent


def demo_full_workflow():
    """完整工作流演示"""
    print("=" * 60)
    print("Demo 4: 完整工作流演示")
    print("=" * 60)

    # 初始化组件
    llm = OpenAILLM(model="deepseek-chat")
    memory = ShortTermMemory()
    context = SharedContext()

    # 创建Agent实例
    agents = {
        "generator": CodeGeneratorAgent(llm=llm, tools=[], memory=memory),
        "reviewer": CodeReviewerAgent(llm=llm, tools=[], memory=memory),
        "debugger": DebuggerAgent(llm=llm, tools=[], memory=memory),
        "test_generator": TestGeneratorAgent(llm=llm, tools=[], memory=memory),
    }

    # 创建Orchestrator
    orchestrator = Orchestrator(agents=agents, context=context)

    # 用户需求
    requirement = "实现一个二分查找算法，支持查找任意可比较类型"

    print(f"\n📝 用户需求: {requirement}")
    print("\n" + "=" * 60)

    # Step 1: 任务分析
    print("\n🔍 Step 1: 任务分析")
    print(f"  当前状态: {orchestrator.state_machine.current_state.value}")

    # Step 2: 处理请求（完整流程）
    print("\n⏳ Step 2: 开始处理请求...")
    result = orchestrator.process_request(requirement)

    # 显示状态变化
    print(f"\n📊 状态历史:")
    for i, state in enumerate(orchestrator.state_machine.history):
        print(f"  {i + 1}. {state.value}")
    print(f"  最终状态: {orchestrator.state_machine.current_state.value}")

    # 显示结果
    print("\n" + "=" * 60)
    print("✅ 最终生成的代码:")
    print("-" * 40)
    print(result.get("code", "生成失败"))
    print("-" * 40)

    # 显示审查结果
    if "issues" in result:
        print(f"\n📋 审查发现的问题: {len(result.get('issues', []))}个")
        for issue in result.get("issues", []):
            print(f"  - [{issue.get('severity')}] {issue.get('message')}")

    if "review_score" in result:
        print(f"\n📊 审查评分: {result.get('review_score', 0)}/100")

    # 显示统计
    print("\n📈 统计信息:")
    print(f"  - 状态转换次数: {len(orchestrator.state_machine.history)}")
    print(f"  - 记忆条目数: {len(memory.items)}")
    print(f"  - 代码行数: {len(result.get('code', '').splitlines())}")

    return result


def print_workflow_diagram():
    """打印工作流图示"""
    print("\n" + "=" * 60)
    print("📊 工作流图示")
    print("=" * 60)
    print("""
    ┌─────────────┐
    │ 用户需求    │
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │ Orchestrator│
    └──────┬──────┘
           ▼
    ┌─────────────┐     ┌─────────────┐
    │  Generator  │────▶│  Reviewer   │
    └─────────────┘     └──────┬──────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌─────────────┐       ┌─────────────┐
            │   通过 ✅   │       │  不通过 ❌  │
            └──────┬──────┘       └──────┬──────┘
                   │                     │
                   ▼                     ▼
            ┌─────────────┐       ┌─────────────┐
            │TestGenerator│       │  Debugger   │
            └──────┬──────┘       └──────┬──────┘
                   │                     │
                   ▼                     │
            ┌─────────────┐              │
            │    Done     │◀─────────────┘
            └─────────────┘
    """)


if __name__ == "__main__":
    print_workflow_diagram()
    demo_full_workflow()
