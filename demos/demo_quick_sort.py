"""
Demo 1: 排序算法生成演示

演示场景: 生成快速排序算法
展示能力: 代码生成、PEP8规范、类型注解
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.context import SharedContext
from backend.core.memory import ShortTermMemory
from backend.llm.openai_llm import OpenAILLM


def demo_quick_sort():
    """快速排序算法生成演示"""
    print("=" * 60)
    print("Demo 1: 排序算法生成演示")
    print("=" * 60)

    # 初始化组件
    llm = OpenAILLM(model="deepseek-chat")
    memory = ShortTermMemory()
    context = SharedContext()

    # 模拟Generator Agent
    from backend.agents.code_generator import CodeGeneratorAgent

    generator = CodeGeneratorAgent(llm=llm, tools=[], memory=memory)

    # 用户需求
    requirement = "实现一个快速排序算法，支持自定义比较函数"

    print(f"\n📝 用户需求: {requirement}")
    print("\n⏳ 正在生成代码...\n")

    # 生成代码
    result = generator.process({"requirement": requirement}, context.data)

    print("✅ 生成的代码:")
    print("-" * 40)
    print(result.get("code", "生成失败"))
    print("-" * 40)

    # 保存到记忆
    memory.add({
        "type": "code_generation",
        "requirement": requirement,
        "code": result.get("code", ""),
    })

    print("\n📊 统计:")
    print(f"  - 代码行数: {len(result.get('code', '').splitlines())}")
    print(f"  - 记忆条目: {len(memory.items)}")

    return result


if __name__ == "__main__":
    demo_quick_sort()
