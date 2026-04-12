"""
Demo 2: 安全漏洞修复演示

演示场景: SQL注入漏洞修复
展示能力: 代码审查发现问题、自动修复安全漏洞
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.context import SharedContext
from backend.core.memory import ShortTermMemory
from backend.llm.openai_llm import OpenAILLM
from backend.agents.code_reviewer import CodeReviewerAgent
from backend.agents.debugger import DebuggerAgent


# 存在SQL注入漏洞的代码
VULNERABLE_CODE = '''
def get_user(cursor, user_id):
    """获取用户信息"""
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
'''


def demo_security_fix():
    """安全漏洞修复演示"""
    print("=" * 60)
    print("Demo 2: 安全漏洞修复演示")
    print("=" * 60)

    # 初始化组件
    llm = OpenAILLM(model="deepseek-chat")
    memory = ShortTermMemory()
    context = SharedContext()

    reviewer = CodeReviewerAgent(llm=llm, tools=[], memory=memory)
    debugger = DebuggerAgent(llm=llm, tools=[], memory=memory)

    print("\n🔍 原始代码（存在SQL注入漏洞）:")
    print("-" * 40)
    print(VULNERABLE_CODE)
    print("-" * 40)

    # Step 1: 代码审查
    print("\n⏳ 正在审查代码...")
    review_result = reviewer.process({"code": VULNERABLE_CODE}, context.data)

    print("\n📋 审查结果:")
    print(f"  - 通过: {'✅' if review_result.get('passed') else '❌'}")
    print(f"  - 评分: {review_result.get('score', 0)}/100")
    print(f"  - 问题数: {len(review_result.get('issues', []))}")

    if review_result.get("issues"):
        print("\n⚠️ 发现的问题:")
        for i, issue in enumerate(review_result.get("issues", []), 1):
            print(f"  {i}. [{issue.get('severity', 'unknown')}] {issue.get('message', '')}")
            print(f"     建议: {issue.get('suggestion', '')}")

    # Step 2: 修复问题
    if not review_result.get("passed", True):
        print("\n⏳ 正在修复问题...")
        fix_result = debugger.process(
            {"code": VULNERABLE_CODE, "issues": review_result.get("issues", [])},
            context.data,
        )

        print("\n✅ 修复后的代码:")
        print("-" * 40)
        print(fix_result.get("fixed_code", "修复失败"))
        print("-" * 40)

        # Step 3: 重新审查
        print("\n⏳ 重新审查修复后的代码...")
        re_review = reviewer.process({"code": fix_result.get("fixed_code", "")}, context.data)
        print(f"\n📋 重新审查结果:")
        print(f"  - 通过: {'✅' if re_review.get('passed') else '❌'}")
        print(f"  - 评分: {re_review.get('score', 0)}/100")

    return review_result


if __name__ == "__main__":
    demo_security_fix()
