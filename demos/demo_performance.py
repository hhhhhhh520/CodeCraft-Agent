"""
Demo 3: 性能优化演示

演示场景: O(n^2) → O(n) 复杂度优化
展示能力: 性能问题检测、优化建议生成
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.context import SharedContext
from backend.core.memory import ShortTermMemory
from backend.llm.openai_llm import OpenAILLM
from backend.agents.code_reviewer import CodeReviewerAgent
from backend.agents.debugger import DebuggerAgent
from backend.tools.executor import CodeExecutor


# O(n^2) 复杂度的低效代码
SLOW_CODE = '''
def find_duplicates(arr):
    """查找数组中的重复元素"""
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates
'''


def safe_exec_code(code: str, func_name: str, *args, **kwargs):
    """安全执行代码并调用指定函数

    Args:
        code: Python代码字符串
        func_name: 要调用的函数名
        *args, **kwargs: 函数参数

    Returns:
        函数执行结果或错误信息
    """
    executor = CodeExecutor(timeout=30)

    # 使用安全执行方法
    result = executor.safe_exec(code)

    if not result["success"]:
        print(f"  ⚠️ 安全执行失败: {result.get('error', 'Unknown error')}")
        return None

    # 获取函数并执行
    if func_name in result["globals"]:
        return result["globals"][func_name](*args, **kwargs)
    else:
        print(f"  ⚠️ 函数 {func_name} 未找到")
        return None


def demo_performance():
    """性能优化演示"""
    print("=" * 60)
    print("Demo 3: 性能优化演示")
    print("=" * 60)

    # 初始化组件
    llm = OpenAILLM(model="deepseek-chat")
    memory = ShortTermMemory()
    context = SharedContext()

    reviewer = CodeReviewerAgent(llm=llm, tools=[], memory=memory)
    debugger = DebuggerAgent(llm=llm, tools=[], memory=memory)

    print("\n🔍 原始代码（O(n^2)复杂度）:")
    print("-" * 40)
    print(SLOW_CODE)
    print("-" * 40)

    # 性能测试数据
    test_data = list(range(1000)) + list(range(500))

    # 测试原始代码（使用安全执行）
    print("\n⏱️ 性能测试（1500个元素）:")
    start = time.time()
    result_slow = safe_exec_code(SLOW_CODE, "find_duplicates", test_data)
    time_slow = time.time() - start

    if result_slow is not None:
        print(f"  - 原始代码耗时: {time_slow:.4f}秒")
    else:
        print("  - 原始代码执行失败，使用默认值")
        time_slow = 1.0
        result_slow = []

    # Step 1: 代码审查
    print("\n⏳ 正在审查代码...")
    review_result = reviewer.process({"code": SLOW_CODE}, context.data)

    print("\n📋 审查结果:")
    print(f"  - 通过: {'✅' if review_result.get('passed') else '❌'}")
    print(f"  - 评分: {review_result.get('score', 0)}/100")

    # 查找性能问题
    perf_issues = [
        i for i in review_result.get("issues", [])
        if i.get("type") == "performance"
    ]
    if perf_issues:
        print("\n⚠️ 性能问题:")
        for issue in perf_issues:
            print(f"  - {issue.get('message', '')}")
            print(f"    建议: {issue.get('suggestion', '')}")

    # Step 2: 优化代码
    print("\n⏳ 正在优化代码...")
    fix_result = debugger.process(
        {"code": SLOW_CODE, "issues": review_result.get("issues", [])},
        context.data,
    )

    optimized_code = fix_result.get("fixed_code", SLOW_CODE)
    print("\n✅ 优化后的代码:")
    print("-" * 40)
    print(optimized_code)
    print("-" * 40)

    # 测试优化后代码（使用安全执行）
    print("\n⏱️ 优化后性能测试:")
    start = time.time()
    result_fast = safe_exec_code(optimized_code, "find_duplicates", test_data)
    time_fast = time.time() - start

    if result_fast is not None:
        print(f"  - 优化后耗时: {time_fast:.4f}秒")
        if time_fast > 0:
            print(f"  - 性能提升: {time_slow / time_fast:.1f}x")
    else:
        print("  - 优化后代码执行失败")

    # 验证结果一致性
    if result_slow is not None and result_fast is not None:
        print(f"\n✅ 结果验证: {'通过' if set(result_slow) == set(result_fast) else '失败'}")

    return fix_result


if __name__ == "__main__":
    demo_performance()
