"""
一键运行所有Demo

运行方式: python demos/run_all_demos.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demos.demo_quick_sort import demo_quick_sort
from demos.demo_security_fix import demo_security_fix
from demos.demo_performance import demo_performance
from demos.demo_full_workflow import demo_full_workflow, print_workflow_diagram


def run_all_demos():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("🚀 CodeCraft Agent 演示套件")
    print("=" * 60)

    demos = [
        ("Demo 1: 排序算法生成", demo_quick_sort),
        ("Demo 2: 安全漏洞修复", demo_security_fix),
        ("Demo 3: 性能优化", demo_performance),
        ("Demo 4: 完整工作流", lambda: (print_workflow_diagram(), demo_full_workflow())[1]),
    ]

    results = []

    for name, demo_func in demos:
        print(f"\n{'=' * 60}")
        print(f"▶️ 运行 {name}")
        print("=" * 60)

        try:
            result = demo_func()
            results.append((name, "✅ 成功", result))
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            results.append((name, "❌ 失败", str(e)))

    # 汇总报告
    print("\n" + "=" * 60)
    print("📊 演示汇总报告")
    print("=" * 60)

    for name, status, _ in results:
        print(f"  {status} {name}")

    success_count = sum(1 for _, status, _ in results if "成功" in status)
    print(f"\n总计: {success_count}/{len(results)} 个演示成功")

    return results


if __name__ == "__main__":
    run_all_demos()
