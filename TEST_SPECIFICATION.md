# CodeCraft Agent 功能测试规格书

> 创建时间: 2026-06-27
> 用途: 逐项验证项目所有设计功能的实际运行结果
> 测试方式: CLI / Web UI / Python 直接调用
> 复核: 2026-09-10 —— 已清理指向已删除代码的条目（通信协议/记忆系统/safe_exec/send_message），其余条目本次未逐项重跑

---

## 使用说明

每个测试项包含：
- **ID**: 唯一标识
- **前置条件**: 测试前需要什么
- **操作步骤**: 具体执行什么命令/操作
- **预期结果**: 必须看到什么才能证明功能正常
- **判定标准**: ✅ 通过 / ❌ 失败的明确界限

---

## 一、状态机（StateMachine）

### SM-01: 初始状态
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine
  sm = StateMachine()
  print(sm.current_state)
  ```
- **预期结果**: 输出 `TaskState.PENDING`
- **判定标准**: 输出值等于 `TaskState.PENDING` 即通过

### SM-02: 合法转换链
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  steps = [
      (TaskState.ANALYZING, True),
      (TaskState.GENERATING, True),
      (TaskState.REVIEWING, True),
      (TaskState.DONE, True),
  ]
  for target, expected in steps:
      result = sm.transition(target)
      print(f"→ {target.value}: {result} (期望: {expected})")
  print(f"最终状态: {sm.current_state}")
  ```
- **预期结果**:
  ```
  → analyzing: True (期望: True)
  → generating: True (期望: True)
  → reviewing: True (期望: True)
  → done: True (期望: True)
  最终状态: TaskState.DONE
  ```
- **判定标准**: 每步返回值与期望一致，最终状态为 DONE

### SM-03: 非法转换拒绝
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  result = sm.transition(TaskState.DONE)  # PENDING 直接跳 DONE
  print(f"转换结果: {result}")
  print(f"状态未变: {sm.current_state}")
  ```
- **预期结果**:
  ```
  转换结果: False
  状态未变: TaskState.PENDING
  ```
- **判定标准**: 返回 False 且状态保持 PENDING

### SM-04: 转换历史记录
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  sm.transition(TaskState.GENERATING)
  sm.transition(TaskState.REVIEWING)
  print(f"历史记录: {[s.value for s in sm.history]}")
  print(f"历史长度: {len(sm.history)}")
  ```
- **预期结果**:
  ```
  历史记录: ['pending', 'analyzing', 'generating']
  历史长度: 3
  ```
- **判定标准**: history 包含所有经过的状态（不含当前状态）

### SM-05: 修复循环
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  sm.transition(TaskState.GENERATING)
  sm.transition(TaskState.REVIEWING)
  sm.transition(TaskState.FIXING)
  sm.transition(TaskState.REVIEWING)  # 第二轮审查
  sm.transition(TaskState.FIXING)
  sm.transition(TaskState.REVIEWING)  # 第三轮审查
  sm.transition(TaskState.DONE)
  print(f"最终状态: {sm.current_state}")
  print(f"历史: {[s.value for s in sm.history]}")
  ```
- **预期结果**:
  ```
  最终状态: TaskState.DONE
  历史: ['pending', 'analyzing', 'generating', 'reviewing', 'fixing', 'reviewing', 'fixing', 'reviewing']
  ```
- **判定标准**: 可以多次 REVIEWING↔FIXING 循环，最终到 DONE

### SM-06: 中间状态→FAILED
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  states_to_test = [TaskState.REVIEWING, TaskState.FIXING, TaskState.TESTING]
  for state in states_to_test:
      sm = StateMachine()
      sm.transition(TaskState.ANALYZING)
      sm.transition(TaskState.GENERATING)
      if state == TaskState.TESTING:
          sm.transition(TaskState.REVIEWING)
      sm.transition(state)
      result = sm.transition(TaskState.FAILED)
      print(f"{state.value}→FAILED: {result}")
  ```
- **预期结果**:
  ```
  reviewing→FAILED: True
  fixing→FAILED: True
  testing→FAILED: True
  ```
- **判定标准**: 三个中间状态都可以转到 FAILED

### SM-07: FAILED→PENDING 重试
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  sm.transition(TaskState.GENERATING)
  sm.transition(TaskState.FAILED)
  print(f"当前状态: {sm.current_state}")
  result = sm.transition(TaskState.PENDING)
  print(f"FAILED→PENDING: {result}")
  print(f"重试后状态: {sm.current_state}")
  ```
- **预期结果**:
  ```
  当前状态: TaskState.FAILED
  FAILED→PENDING: True
  重试后状态: TaskState.PENDING
  ```
- **判定标准**: FAILED 可以回到 PENDING 重新开始

### SM-08: DONE 终态保护
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  sm.transition(TaskState.GENERATING)
  sm.transition(TaskState.REVIEWING)
  sm.transition(TaskState.DONE)
  targets = [TaskState.PENDING, TaskState.ANALYZING, TaskState.FAILED]
  for t in targets:
      result = sm.transition(t)
      print(f"DONE→{t.value}: {result}")
  print(f"状态仍为: {sm.current_state}")
  ```
- **预期结果**:
  ```
  DONE→pending: False
  DONE→analyzing: False
  DONE→failed: False
  状态仍为: TaskState.DONE
  ```
- **判定标准**: DONE 状态下所有转换都返回 False

### SM-09: reset()
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  sm.transition(TaskState.GENERATING)
  sm.reset()
  print(f"重置后状态: {sm.current_state}")
  print(f"历史长度: {len(sm.history)}")
  ```
- **预期结果**:
  ```
  重置后状态: TaskState.PENDING
  历史长度: 0
  ```
- **判定标准**: 状态回到 PENDING，history 清空

### SM-10: 非法转换不记录历史
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.state import StateMachine, TaskState
  sm = StateMachine()
  sm.transition(TaskState.ANALYZING)
  history_before = len(sm.history)
  sm.transition(TaskState.DONE)  # 非法转换
  history_after = len(sm.history)
  print(f"转换前历史长度: {history_before}")
  print(f"转换后历史长度: {history_after}")
  print(f"历史未增长: {history_before == history_after}")
  ```
- **预期结果**:
  ```
  转换前历史长度: 1
  转换后历史长度: 1
  历史未增长: True
  ```
- **判定标准**: 非法转换不写入 history

---

## 二、通信协议（Protocol）—— 已废弃

> ⚠️ **整章失效（2026-09-10 标注）**：`backend/core/protocol.py`（`AgentMessage` / `MessageType`）自始至终没有被主流程调用，已于 2026-06-28 作为死代码删除，`tests/test_protocol.py`（5 个用例）同步移除。原 PT-01 / PT-02 已删除，**不要再去执行**——`from backend.core.protocol import ...` 现在会直接抛 `ModuleNotFoundError`。

---

## 三、共享上下文（SharedContext）

### CT-01: 基本 set/get
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.context import SharedContext
  ctx = SharedContext()
  ctx.set("key1", "value1")
  ctx.set("key2", {"nested": True})
  print(f"key1: {ctx.get('key1')}")
  print(f"key2: {ctx.get('key2')}")
  print(f"不存在的key: {ctx.get('missing', '默认值')}")
  ```
- **预期结果**:
  ```
  key1: value1
  key2: {'nested': True}
  不存在的key: 默认值
  ```
- **判定标准**: get 返回 set 的值，不存在时返回默认值

### CT-02: update 批量更新
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.context import SharedContext
  ctx = SharedContext()
  ctx.update({"a": 1, "b": 2, "c": 3})
  print(f"keys: {sorted(ctx.keys())}")
  print(f"len: {len(ctx)}")
  ```
- **预期结果**:
  ```
  keys: ['a', 'b', 'c']
  len: 3
  ```
- **判定标准**: update 后 keys() 和 len() 正确

### CT-03: __contains__ 和 __len__
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.context import SharedContext
  ctx = SharedContext()
  ctx.set("exists", 1)
  print(f"'exists' in ctx: {'exists' in ctx}")
  print(f"'nope' in ctx: {'nope' in ctx}")
  print(f"len: {len(ctx)}")
  ```
- **预期结果**:
  ```
  'exists' in ctx: True
  'nope' in ctx: False
  len: 1
  ```
- **判定标准**: in 操作符和 len() 正确工作

### CT-04: to_dict 返回副本
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.context import SharedContext
  ctx = SharedContext()
  ctx.set("key", "original")
  d = ctx.to_dict()
  d["data"]["key"] = "modified"
  print(f"原值未变: {ctx.get('key')}")
  print(f"包含task_id: {'task_id' in d}")
  ```
- **预期结果**:
  ```
  原值未变: original
  包含task_id: True
  ```
- **判定标准**: 修改 to_dict 返回值不影响原数据

### CT-05: clear 清空
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.context import SharedContext
  ctx = SharedContext()
  ctx.set("a", 1)
  ctx.set("b", 2)
  ctx.clear()
  print(f"清空后len: {len(ctx)}")
  print(f"清空后keys: {ctx.keys()}")
  ```
- **预期结果**:
  ```
  清空后len: 0
  清空后keys: []
  ```
- **判定标准**: clear 后 len 为 0，keys 为空列表

---

## 四、代码生成 Agent（CodeGeneratorAgent）

### CG-01: 正常生成代码
- **前置条件**: 设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY 环境变量
- **操作步骤**:
  ```python
  from backend.agents.code_generator import CodeGeneratorAgent
  from backend.llm import LLMFactory
  import os
  llm = LLMFactory.create("openai", "deepseek-chat",
      api_key=os.getenv("DEEPSEEK_API_KEY"),
      base_url="https://api.deepseek.com/v1")
  agent = CodeGeneratorAgent(llm=llm, tools=[])
  result = agent.process({"requirement": "实现一个计算阶乘的函数"}, {})
  print(f"包含code字段: {'code' in result}")
  print(f"代码包含factorial: {'factorial' in result.get('code', '')}")
  print(f"代码包含def: {'def' in result.get('code', '')}")
  ```
- **预期结果**:
  ```
  包含code字段: True
  代码包含factorial: True
  代码包含def: True
  ```
- **判定标准**: 返回 dict 含 code 字段，代码包含 def 关键字和需求相关函数名

### CG-02: system prompt 包含安全约束
- **前置条件**: 无（不需要 LLM 调用）
- **操作步骤**:
  ```python
  from backend.agents.code_generator import CodeGeneratorAgent
  prompt = CodeGeneratorAgent.SYSTEM_PROMPT
  checks = ["importlib", "eval()", "exec()", "__class__", "__subclasses__"]
  for keyword in checks:
      print(f"包含'{keyword}': {keyword in prompt}")
  ```
- **预期结果**:
  ```
  包含'importlib': True
  包含'eval()': True
  包含'exec()': True
  包含'__class__': True
  包含'__subclasses__': True
  ```
- **判定标准**: system prompt 包含所有安全约束关键词

### CG-03: 安全验证拦截危险代码
- **前置条件**: Mock LLM 返回含 `import os` 的代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_generator import CodeGeneratorAgent
  llm = Mock()
  llm.invoke.return_value = "```python\nimport os\nos.system('whoami')\n```"
  agent = CodeGeneratorAgent(llm=llm, tools=[], strict_security=True)
  result = agent.process({"requirement": "test"}, {})
  print(f"返回security_error: {'security_error' in result}")
  print(f"code为空: {result.get('code') == ''}")
  print(f"有security_issues: {len(result.get('security_issues', [])) > 0}")
  ```
- **预期结果**:
  ```
  返回security_error: True
  code为空: True
  有security_issues: True
  ```
- **判定标准**: strict_security=True 时，危险代码被拦截，code 为空

### CG-04: 非严格模式记录但不拦截
- **前置条件**: Mock LLM 返回含 `import os` 的代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_generator import CodeGeneratorAgent
  llm = Mock()
  llm.invoke.return_value = "```python\nimport os\nprint(os.name)\n```"
  agent = CodeGeneratorAgent(llm=llm, tools=[], strict_security=False)
  result = agent.process({"requirement": "test"}, {})
  print(f"code非空: {len(result.get('code', '')) > 0}")
  print(f"security_issues非空: {len(result.get('security_issues', [])) > 0}")
  print(f"无security_error: {'security_error' not in result}")
  ```
- **预期结果**:
  ```
  code非空: True
  security_issues非空: True
  无security_error: True
  ```
- **判定标准**: strict_security=False 时，代码保留，issues 记录但不拦截

---

## 五、代码审查 Agent（CodeReviewerAgent）

### CR-01: 审查通过
- **前置条件**: Mock LLM 返回 passed=true 的 JSON
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_reviewer import CodeReviewerAgent
  llm = Mock()
  llm.invoke.return_value = '{"passed": true, "issues": [], "score": 95, "summary": "代码质量优秀"}'
  agent = CodeReviewerAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): pass"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"score: {result.get('score')}")
  print(f"issues数量: {len(result.get('issues', []))}")
  ```
- **预期结果**:
  ```
  passed: True
  score: 95
  issues数量: 0
  ```
- **判定标准**: passed=True, score=95, issues 为空列表

### CR-02: 审查不通过
- **前置条件**: Mock LLM 返回 passed=false 的 JSON
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_reviewer import CodeReviewerAgent
  llm = Mock()
  llm.invoke.return_value = '{"passed": false, "issues": [{"severity": "high", "message": "未处理除零"}], "score": 60}'
  agent = CodeReviewerAgent(llm=llm, tools=[])
  result = agent.process({"code": "def div(a,b): return a/b"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"score: {result.get('score')}")
  print(f"issues数量: {len(result.get('issues', []))}")
  print(f"issue内容: {result['issues'][0]['message']}")
  ```
- **预期结果**:
  ```
  passed: False
  score: 60
  issues数量: 1
  issue内容: 未处理除零
  ```
- **判定标准**: passed=False, issues 非空

### CR-03: JSON 解析失败返回不通过
- **前置条件**: Mock LLM 返回非 JSON 文本
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_reviewer import CodeReviewerAgent
  llm = Mock()
  llm.invoke.return_value = "这段代码看起来不错，没有明显问题。"
  agent = CodeReviewerAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): pass"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"score: {result.get('score')}")
  print(f"有parse_error issue: {any('parse_error' in str(i) for i in result.get('issues', []))}")
  ```
- **预期结果**:
  ```
  passed: False
  score: 0
  有parse_error issue: True
  ```
- **判定标准**: 解析失败时 passed=False, score=0

### CR-04: 从 json 代码块提取
- **前置条件**: Mock LLM 返回 ```json 代码块
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_reviewer import CodeReviewerAgent
  llm = Mock()
  llm.invoke.return_value = '审查结果如下：\n```json\n{"passed": true, "issues": [], "score": 88}\n```'
  agent = CodeReviewerAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): pass"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"score: {result.get('score')}")
  ```
- **预期结果**:
  ```
  passed: True
  score: 88
  ```
- **判定标准**: 从 json 代码块中正确提取 JSON

### CR-05: 宽松提取（尾逗号）
- **前置条件**: Mock LLM 返回带尾逗号的 JSON
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.code_reviewer import CodeReviewerAgent
  llm = Mock()
  llm.invoke.return_value = '{"passed": true, "issues": [], "score": 90,}'
  agent = CodeReviewerAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): pass"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"score: {result.get('score')}")
  ```
- **预期结果**:
  ```
  passed: True
  score: 90
  ```
- **判定标准**: 去掉尾逗号后能正确解析

---

## 六、调试 Agent（DebuggerAgent）

### DB-01: 修复代码
- **前置条件**: Mock LLM 返回修复后的代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.debugger import DebuggerAgent
  llm = Mock()
  llm.invoke.return_value = "```python\ndef div(a, b):\n    if b == 0:\n        raise ValueError('除数不能为0')\n    return a / b\n```"
  agent = DebuggerAgent(llm=llm, tools=[], strict_security=False)
  result = agent.process({
      "code": "def div(a,b): return a/b",
      "issues": [{"severity": "high", "message": "未处理除零"}]
  }, {})
  print(f"有fixed_code: {'fixed_code' in result}")
  print(f"代码含ValueError: {'ValueError' in result.get('fixed_code', '')}")
  print(f"issues_fixed: {result.get('issues_fixed')}")
  ```
- **预期结果**:
  ```
  有fixed_code: True
  代码含ValueError: True
  issues_fixed: 1
  ```
- **判定标准**: 返回修复后的代码，issues_fixed 等于输入 issues 数量

### DB-02: 修复后代码不安全时回退
- **前置条件**: Mock LLM 返回含危险代码的"修复"
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.debugger import DebuggerAgent
  llm = Mock()
  llm.invoke.return_value = "```python\nimport os\nos.system('rm -rf /')\n```"
  agent = DebuggerAgent(llm=llm, tools=[], strict_security=True)
  result = agent.process({
      "code": "def div(a,b): return a/b",
      "issues": [{"severity": "high", "message": "test"}]
  }, {})
  print(f"返回原始代码: {result.get('fixed_code') == 'def div(a,b): return a/b'}")
  print(f"有security_error: {'security_error' in result}")
  ```
- **预期结果**:
  ```
  返回原始代码: True
  有security_error: True
  ```
- **判定标准**: strict_security=True 时，不安全的修复被拒绝，返回原始代码

### DB-03: system prompt 包含安全约束
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.agents.debugger import DebuggerAgent
  prompt = DebuggerAgent.SYSTEM_PROMPT
  checks = ["importlib", "eval()", "exec()", "__class__"]
  for keyword in checks:
      print(f"包含'{keyword}': {keyword in prompt}")
  ```
- **预期结果**:
  ```
  包含'importlib': True
  包含'eval()': True
  包含'exec()': True
  包含'__class__': True
  ```
- **判定标准**: system prompt 包含所有安全约束关键词

---

## 七、测试生成 Agent（TestGeneratorAgent）

### TG-01: 生成测试代码
- **前置条件**: Mock LLM 返回测试代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.test_generator import TestGeneratorAgent
  llm = Mock()
  llm.invoke.return_value = "```python\ndef test_factorial():\n    assert factorial(5) == 120\n```"
  agent = TestGeneratorAgent(llm=llm, tools=[])
  result = agent.process({"code": "def factorial(n): return 1 if n<=1 else n*factorial(n-1)"}, {})
  print(f"有test_code: {'test_code' in result}")
  print(f"test_code含assert: {'assert' in result.get('test_code', '')}")
  print(f"passed是bool: {isinstance(result.get('passed'), bool)}")
  ```
- **预期结果**:
  ```
  有test_code: True
  test_code含assert: True
  passed是bool: True
  ```
- **判定标准**: 返回 test_code 字段，passed 是 bool 类型

### TG-02: 实际执行测试
- **前置条件**: Mock LLM 返回正确的测试代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.test_generator import TestGeneratorAgent
  llm = Mock()
  llm.invoke.return_value = "```python\ndef test_hello():\n    assert hello() == 'world'\n```"
  agent = TestGeneratorAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): return 'world'"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"无test_error: {result.get('test_error', '') == ''}")
  ```
- **预期结果**:
  ```
  passed: True
  无test_error: True
  ```
- **判定标准**: 测试代码与原始代码组合执行成功，passed=True

### TG-03: 测试执行失败
- **前置条件**: Mock LLM 返回错误的测试代码
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.agents.test_generator import TestGeneratorAgent
  llm = Mock()
  llm.invoke.return_value = "```python\ndef test_hello():\n    assert hello() == 'wrong'\n```"
  agent = TestGeneratorAgent(llm=llm, tools=[])
  result = agent.process({"code": "def hello(): return 'world'"}, {})
  print(f"passed: {result.get('passed')}")
  print(f"有test_error: {len(result.get('test_error', '')) > 0}")
  ```
- **预期结果**:
  ```
  passed: False
  有test_error: True
  ```
- **判定标准**: 断言失败时 passed=False，test_error 包含错误信息

---

## 八、协调器（Orchestrator）

### OR-01: 生成请求路由
- **前置条件**: Mock Generator Agent
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock()
  gen.process.return_value = {"code": "def hello(): pass"}
  orch = Orchestrator(agents={"generator": gen}, context=SharedContext())
  result = orch.process_request("实现一个hello函数")
  print(f"generator被调用: {gen.process.called}")
  print(f"结果含code: {'code' in result}")
  print(f"最终状态: {orch.state_machine.current_state}")
  ```
- **预期结果**:
  ```
  generator被调用: True
  结果含code: True
  最终状态: TaskState.DONE
  ```
- **判定标准**: generator 被调用，结果含 code，状态为 DONE

### OR-02: 任务类型分析
- **前置条件**: Mock Generator Agent
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.return_value = {"code": "pass"}
  rev = Mock(); rev.process.return_value = {"passed": True, "score": 90}
  orch = Orchestrator(agents={"generator": gen, "reviewer": rev}, context=SharedContext())
  # 测试 "审查" 关键词
  result = orch.process_request("审查这段代码")
  print(f"'审查'路由到reviewer: {rev.process.called}")
  ```
- **预期结果**:
  ```
  '审查'路由到reviewer: True
  ```
- **判定标准**: 包含"审查"关键词的请求路由到 reviewer

### OR-03: 反馈闭环
- **前置条件**: Mock Generator/Reviewer/Debugger
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.return_value = {"code": "v1"}
  rev = Mock(); rev.process.side_effect = [
      {"passed": False, "issues": [{"severity": "high", "message": "bug"}], "score": 50},
      {"passed": True, "issues": [], "score": 90}
  ]
  dbg = Mock(); dbg.process.return_value = {"fixed_code": "v2"}
  orch = Orchestrator(agents={"generator": gen, "reviewer": rev, "debugger": dbg}, context=SharedContext())
  result = orch.process_request("实现一个函数")
  print(f"reviewer调用次数: {rev.process.call_count}")
  print(f"debugger调用次数: {dbg.process.call_count}")
  print(f"最终code: {result.get('code')}")
  print(f"最终状态: {orch.state_machine.current_state}")
  ```
- **预期结果**:
  ```
  reviewer调用次数: 2
  debugger调用次数: 1
  最终code: v2
  最终状态: TaskState.DONE
  ```
- **判定标准**: reviewer 被调用 2 次（失败→修复→通过），debugger 调用 1 次

### OR-04: Agent 返回 None
- **前置条件**: Mock Generator 返回 None
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.return_value = None
  orch = Orchestrator(agents={"generator": gen}, context=SharedContext())
  result = orch.process_request("test")
  print(f"有error: {'error' in result}")
  print(f"error含AGENT_ERROR: {'AGENT_ERROR' in str(result)}")
  ```
- **预期结果**:
  ```
  有error: True
  error含AGENT_ERROR: True
  ```
- **判定标准**: Agent 返回 None 时返回 AGENT_ERROR

### OR-05: Agent 抛异常
- **前置条件**: Mock Generator 抛异常
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.side_effect = RuntimeError("LLM超时")
  orch = Orchestrator(agents={"generator": gen}, context=SharedContext())
  result = orch.process_request("test")
  print(f"有error: {'error' in result}")
  print(f"含LLM超时: {'LLM超时' in str(result)}")
  print(f"最终状态: {orch.state_machine.current_state}")
  ```
- **预期结果**:
  ```
  有error: True
  含LLM超时: True
  最终状态: TaskState.DONE（因为没有反馈闭环时直接完成）
  ```
- **判定标准**: 异常被捕获，返回错误信息

### OR-06: 无 reviewer 时跳过反馈闭环
- **前置条件**: 只有 generator
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.return_value = {"code": "pass"}
  orch = Orchestrator(agents={"generator": gen}, context=SharedContext())
  result = orch.process_request("test")
  print(f"结果含code: {'code' in result}")
  print(f"最终状态: {orch.state_machine.current_state}")
  ```
- **预期结果**:
  ```
  结果含code: True
  最终状态: TaskState.DONE
  ```
- **判定标准**: 无 reviewer 时直接完成，不进入反馈循环

### OR-07: 最大迭代次数
- **前置条件**: Mock Reviewer 始终返回不通过
- **操作步骤**:
  ```python
  from unittest.mock import Mock
  from backend.core.orchestrator import Orchestrator
  from backend.core.context import SharedContext
  gen = Mock(); gen.process.return_value = {"code": "v1"}
  rev = Mock(); rev.process.return_value = {"passed": False, "issues": [{"message": "bug"}], "score": 30}
  dbg = Mock(); dbg.process.return_value = {"fixed_code": "v2"}
  orch = Orchestrator(agents={"generator": gen, "reviewer": rev, "debugger": dbg}, context=SharedContext())
  result = orch.process_request("test")
  print(f"reviewer调用次数: {rev.process.call_count}")
  print(f"debugger调用次数: {dbg.process.call_count}")
  print(f"最终状态: {orch.state_machine.current_state}")
  ```
- **预期结果**:
  ```
  reviewer调用次数: 3
  debugger调用次数: 3
  最终状态: TaskState.FAILED
  ```
- **判定标准**: 最多 3 轮迭代，之后状态为 FAILED

### OR-08: send_message —— 已废弃

> ⚠️ **本条目已失效（2026-09-10 标注）**：`Orchestrator.send_message()` 与 `BaseAgent.receive_message()` 依赖已删除的 `protocol.py`，且实现后无任何调用点，已随两轮清理移除。保留仅作历史记录，**不要执行**。

---

## 九、记忆系统 —— 已废弃

> ⚠️ **整章失效（2026-09-10 标注）**：`backend/core/memory.py`、`backend/core/vector_memory.py` 实现后从未被主流程调用（全仓零调用点），已于 2026-09-10 连同 `tests/test_memory.py`、`tests/test_vector_memory.py` 一起删除。原 MM-01 ~ MM-04 已删除，**不要再去执行**——对应导入均已失效。

---

## 十、LLM 抽象层

### LLM-01: LLMFactory 创建 OpenAI
- **前置条件**: 无（不需要真实 API Key，只测试创建）
- **操作步骤**:
  ```python
  from backend.llm import LLMFactory
  from unittest.mock import patch
  with patch("backend.llm.openai_llm.OpenAI"):
      llm = LLMFactory.create("openai", "gpt-4o-mini", api_key="test-key")
      print(f"类型: {type(llm).__name__}")
      print(f"model: {llm.model}")
  ```
- **预期结果**:
  ```
  类型: OpenAILLM
  model: gpt-4o-mini
  ```
- **判定标准**: 返回 OpenAILLM 实例，model 正确

### LLM-02: LLMFactory 创建 Claude
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.llm import LLMFactory
  from unittest.mock import patch
  with patch("backend.llm.claude_llm.Anthropic"):
      llm = LLMFactory.create("claude", "claude-3-5-sonnet", api_key="test-key")
      print(f"类型: {type(llm).__name__}")
      print(f"model: {llm.model}")
  ```
- **预期结果**:
  ```
  类型: ClaudeLLM
  model: claude-3-5-sonnet
  ```
- **判定标准**: 返回 ClaudeLLM 实例

### LLM-03: LLMFactory 未知 provider
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.llm import LLMFactory
  try:
      LLMFactory.create("unknown", "model")
      print("未抛异常")
  except ValueError as e:
      print(f"抛ValueError: True")
      print(f"错误信息: {e}")
  ```
- **预期结果**:
  ```
  抛ValueError: True
  错误信息: Unknown provider: unknown
  ```
- **判定标准**: 抛出 ValueError，信息包含 "Unknown provider"

### LLM-04: OpenAILLM 重试机制
- **前置条件**: Mock OpenAI 客户端
- **操作步骤**:
  ```python
  from unittest.mock import Mock, patch
  from openai import RateLimitError
  with patch("backend.llm.openai_llm.OpenAI") as mock_cls:
      mock_client = Mock()
      mock_cls.return_value = mock_client
      # 前两次失败，第三次成功
      success_response = Mock()
      success_response.choices = [Mock(message=Mock(content="ok"))]
      success_response.usage = Mock(total_tokens=10)
      mock_client.chat.completions.create.side_effect = [
          RateLimitError(message="rate limited", response=Mock(status_code=429), body=None),
          RateLimitError(message="rate limited", response=Mock(status_code=429), body=None),
          success_response,
      ]
      from backend.llm import LLMFactory
      llm = LLMFactory.create("openai", "gpt-4o-mini", api_key="test")
      result = llm.invoke([{"role": "user", "content": "hi"}])
      print(f"结果: {result}")
      print(f"调用次数: {mock_client.chat.completions.create.call_count}")
  ```
- **预期结果**:
  ```
  结果: ok
  调用次数: 3
  ```
- **判定标准**: 前两次失败后第三次成功，总共调用 3 次

---

## 十一、Token 管理器

### TM-01: 基本功能
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.llm.token_manager import TokenManager
  tm = TokenManager(max_tokens=1000)
  tm.track_usage(100)
  tm.track_usage(200)
  print(f"当前使用: {tm.current_usage}")
  print(f"剩余: {tm.get_remaining()}")
  print(f"需要压缩(短文本): {tm.should_compress('hello')}")
  print(f"需要压缩(长文本): {tm.should_compress('x' * 5000))}")
  tm.reset()
  print(f"重置后: {tm.current_usage}")
  ```
- **预期结果**:
  ```
  当前使用: 300
  剩余: 700
  需要压缩(短文本): False
  需要压缩(长文本): True
  重置后: 0
  ```
- **判定标准**: track_usage 累加，get_remaining 正确计算，should_compress 按 80% 阈值判断

---

## 十二、AST 解析器

### AST-01: 解析和提取
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.ast_parser import ASTParser
  parser = ASTParser()
  code = '''
import os
from pathlib import Path

class MyClass:
    def method(self, x: int) -> str:
        return str(x)

def standalone(y):
    return y + 1
'''
  tree = parser.parse(code)
  funcs = parser.extract_functions(tree)
  classes = parser.extract_classes(tree)
  imports = parser.extract_imports(tree)
  print(f"函数数量: {len(funcs)}")
  print(f"函数名: {[f.name for f in funcs]}")
  print(f"类数量: {len(classes)}")
  print(f"类名: {[c.name for c in classes]}")
  print(f"导入数量: {len(imports)}")
  sig = parser.get_function_signature(funcs[-1])
  print(f"standalone签名: {sig}")
  info = parser.get_class_info(classes[0])
  print(f"MyClass信息: {info}")
  ```
- **预期结果**:
  ```
  函数数量: 2
  函数名: ['method', 'standalone']
  类数量: 1
  类名: ['MyClass']
  导入数量: 2
  standalone签名: {'name': 'standalone', 'args': ['y'], 'defaults': [], 'returns': None, 'docstring': None}
  MyClass信息: {'name': 'MyClass', 'bases': [], 'methods': ['method'], 'docstring': None}
  ```
- **判定标准**: 函数/类/导入提取正确，签名和类信息完整

### AST-02: 语法错误
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.ast_parser import ASTParser
  parser = ASTParser()
  try:
      parser.parse("def hello(")
      print("未抛异常")
  except SyntaxError as e:
      print(f"抛SyntaxError: True")
      print(f"行号: {e.lineno}")
  ```
- **预期结果**:
  ```
  抛SyntaxError: True
  行号: 1
  ```
- **判定标准**: 语法错误时抛出 SyntaxError

---

## 十三、代码执行器

### EX-01: 正常执行
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeExecutor
  executor = CodeExecutor(timeout=5)
  result = executor.execute("print(1 + 1)")
  print(f"success: {result['success']}")
  print(f"stdout: {result['stdout'].strip()}")
  print(f"returncode: {result['returncode']}")
  ```
- **预期结果**:
  ```
  success: True
  stdout: 2
  returncode: 0
  ```
- **判定标准**: success=True, stdout 包含 "2"

### EX-02: 超时
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeExecutor
  executor = CodeExecutor(timeout=2)
  result = executor.execute("import time; time.sleep(10)")
  print(f"success: {result['success']}")
  print(f"error含超时: {'超时' in result.get('error', '')}")
  ```
- **预期结果**:
  ```
  success: False
  error含超时: True
  ```
- **判定标准**: 超时后 success=False，error 含"超时"

### EX-03: 安全环境变量
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeExecutor
  executor = CodeExecutor(timeout=5)
  env = executor._get_safe_env()
  print(f"有PATH: {'PATH' in env}")
  print(f"有PYTHONPATH: {'PYTHONPATH' in env}")
  print(f"无HOME: {'HOME' not in env}")
  print(f"无USER: {'USER' not in env}")
  print(f"无TEMP: {'TEMP' not in env}")
  ```
- **预期结果**:
  ```
  有PATH: True
  有PYTHONPATH: True
  无HOME: True
  无USER: True
  无TEMP: True
  ```
- **判定标准**: 只有 PATH/PYTHONPATH/PYTHONIOENCODING，不含敏感变量

### EX-04 / EX-05: safe_exec —— 已废弃

> ⚠️ **本条目已失效（2026-09-10 标注）**：`CodeExecutor.safe_exec()`（基于 `exec()` 的沙箱）已在 Phase 8 安全整改中**完全移除**，统一改用 `subprocess` 的 `execute()` 执行，以消除 exec 逃逸面。原 EX-04 / EX-05 已删除，**不要再去执行**。

---

## 十四、输入验证

### IV-01: Anthropic 格式 API Key
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.utils.input_validator import validate_api_key
  key = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"
  is_valid, cleaned, error = validate_api_key(key)
  print(f"valid: {is_valid}")
  print(f"error: {error}")
  ```
- **预期结果**:
  ```
  valid: True
  error: None
  ```
- **判定标准**: sk-ant- 格式且长度足够时通过

### IV-02: 控制字符清理
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.utils.input_validator import validate_requirement
  dirty = "hello\x00\x01\x1fworld"
  is_valid, cleaned, error = validate_requirement(dirty)
  print(f"valid: {is_valid}")
  print(f"清理后: {repr(cleaned)}")
  print(f"不含控制字符: {all(ord(c) >= 32 or c in '\\n\\r\\t' for c in cleaned)}")
  ```
- **预期结果**:
  ```
  valid: True
  清理后: 'helloworld'
  不含控制字符: True
  ```
- **判定标准**: 控制字符被移除

### IV-03: sanitize_for_display
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.utils.input_validator import sanitize_for_display
  long_text = "a" * 1000
  result = sanitize_for_display(long_text)
  print(f"长度: {len(result)}")
  print(f"以...结尾: {result.endswith('...')}")
  ```
- **预期结果**:
  ```
  长度: 503
  以...结尾: True
  ```
- **判定标准**: 超过 500 字符时截断并加 "..."

---

## 十五、日志系统

### LG-01: 敏感信息脱敏
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.core.logger import sanitize_message
  cases = [
      ('api_key="sk-1234567890abcdefghijklmnop"', "sk-1234567890abcdefghijklmnop"),
      ('password="my_secret"', "my_secret"),
      ('token="eyJhbGci.xxx.yyy"', "eyJhbGci"),
      ('AWS_KEY="AKIA1234567890ABCDEF"', "AKIA1234567890ABCDEF"),
  ]
  for msg, secret in cases:
      sanitized = sanitize_message(msg)
      print(f"'{secret}'被脱敏: {secret not in sanitized}")
      print(f"  结果: {sanitized}")
  ```
- **预期结果**:
  ```
  'sk-1234567890abcdefghijklmnop'被脱敏: True
    结果: api_key="sk-***REDACTED***"
  'my_secret'被脱敏: True
    结果: password="***REDACTED***"
  'eyJhbGci'被脱敏: True
    结果: token="***JWT_REDACTED***"
  'AKIA1234567890ABCDEF'被脱敏: True
    结果: AWS_KEY="***AWS_KEY_REDACTED***"
  ```
- **判定标准**: 所有敏感信息被替换为 ***REDACTED*** 或对应标记

### LG-02: setup_logger 创建
- **前置条件**: 无
- **操作步骤**:
  ```python
  import logging
  from backend.core.logger import setup_logger
  logger = setup_logger("test_logger", level=logging.DEBUG)
  print(f"名称: {logger.name}")
  print(f"level: {logger.level}")
  print(f"handlers数量: {len(logger.handlers)}")
  # 重复调用不应添加更多 handler
  logger2 = setup_logger("test_logger", level=logging.INFO)
  print(f"重复调用后handlers: {len(logger2.handlers)}")
  ```
- **预期结果**:
  ```
  名称: test_logger
  level: 10
  handlers数量: 1
  重复调用后handlers: 1
  ```
- **判定标准**: 创建 logger 有 1 个 handler，重复调用不增加

### LG-03: SensitiveInfoFilter
- **前置条件**: 无
- **操作步骤**:
  ```python
  import logging
  from backend.core.logger import SensitiveInfoFilter
  record = logging.LogRecord(
      name="test", level=logging.INFO, pathname="", lineno=0,
      msg='api_key="sk-1234567890abcdefghijklmnop"', args=(), exc_info=None
  )
  f = SensitiveInfoFilter()
  f.filter(record)
  print(f"脱敏后: {record.msg}")
  print(f"不含原始key: {'sk-1234567890abcdefghijklmnop' not in record.msg}")
  ```
- **预期结果**:
  ```
  脱敏后: api_key="sk-***REDACTED***"
  不含原始key: True
  ```
- **判定标准**: filter 方法对 LogRecord 的 msg 进行脱敏

---

## 十六、安全验证高级场景

### SEC-01: importlib 动态导入
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeValidator
  code = "import importlib\nos = importlib.import_module('os')\nos.system('whoami')"
  is_safe, issues = CodeValidator.validate(code)
  print(f"is_safe: {is_safe}")
  print(f"issues数量: {len(issues)}")
  ```
- **预期结果**:
  ```
  is_safe: False
  issues数量: >=1
  ```
- **判定标准**: importlib 导入被检测为危险

### SEC-02: __subclasses__ 链攻击
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeValidator
  code = "().__class__.__bases__[0].__subclasses__()"
  is_safe, issues = CodeValidator.validate(code)
  print(f"is_safe: {is_safe}")
  print(f"issues: {issues}")
  ```
- **预期结果**:
  ```
  is_safe: False
  issues: 包含 __subclasses__ 或 __class__ 相关的检测
  ```
- **判定标准**: 链式属性访问被检测

### SEC-03: CodeValidator 拦截 dunder 属性访问
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeValidator
  code = 'cls = getattr(obj, "__class__")'
  is_safe, issues = CodeValidator.validate(code)
  print(f"is_safe: {is_safe}")
  print(f"issues数量: {len(issues)}")
  ```
- **预期结果**:
  ```
  is_safe: False
  issues数量: >0
  ```
- **判定标准**: getattr 访问 `__` 开头的属性被静态拦截

### SEC-04: 普通属性访问不误拦
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.tools.executor import CodeValidator
  code = 'name = getattr(obj, "name")'
  is_safe, issues = CodeValidator.validate(code)
  print(f"is_safe: {is_safe}")
  ```
- **预期结果**:
  ```
  is_safe: True
  ```
- **判定标准**: 只拦截 `__` 开头的属性名，普通属性访问放行

> 注（2026-09-10 修订）：本条早期描述的是 `CodeExecutor.safe_exec()` 运行时的 `safe_getattr` 白名单。exec 沙箱已在 Phase 8 移除，`safe_getattr` 随之不存在，现在改由 `CodeValidator` 在**静态检查阶段**拦截，对应 `tests/test_security.py::test_code_validator_blocks_dunder_getattr` 与 `test_code_validator_allows_normal_getattr`。

---

## 十七、代码工具

### CU-01: 提取代码块各种格式
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.utils.code_utils import extract_code_from_response
  cases = [
      ("```python\ndef a(): pass\n```", "def a(): pass"),
      ("```\ndef b(): pass\n```", "def b(): pass"),
      ("无代码块", "无代码块"),
      ("", ""),
      (None, ""),
  ]
  for input_text, expected in cases:
      result = extract_code_from_response(input_text)
      match = expected in result if expected else result == expected
      print(f"'{str(input_text)[:30]}...' → 匹配: {match}")
  ```
- **预期结果**:
  ```
  '```python\ndef a(): pass\n```...' → 匹配: True
  '```\ndef b(): pass\n```...' → 匹配: True
  '无代码块...' → 匹配: True
  '...' → 匹配: True
  'None...' → 匹配: True
  ```
- **判定标准**: 所有格式都正确提取

### CU-02: validate_python_code
- **前置条件**: 无
- **操作步骤**:
  ```python
  from backend.utils.code_utils import validate_python_code
  cases = [
      ("def hello(): pass", True),
      ("def hello(", False),
      ("", False),
      (None, False),
  ]
  for code, expected_valid in cases:
      is_valid, error = validate_python_code(code)
      print(f"'{str(code)[:20]}' → valid={is_valid}, 期望={expected_valid}, 匹配={is_valid == expected_valid}")
  ```
- **预期结果**:
  ```
  'def hello(): pass' → valid=True, 期望=True, 匹配=True
  'def hello(' → valid=False, 期望=False, 匹配=True
  '' → valid=False, 期望=False, 匹配=True
  'None' → valid=False, 期望=False, 匹配=True
  ```
- **判定标准**: 所有输入的验证结果与期望一致

---

## 十八、CLI 命令

### CLI-01: version 命令
- **前置条件**: 无
- **操作步骤**:
  ```bash
  cd "D:/my project/CodeCraft Agent"
  python -m cli.main version
  ```
- **预期结果**: 输出包含版本号，如 `CodeCraft Agent v0.2.0`
- **判定标准**: 输出非空且包含 "v" + 数字

### CLI-02: generate 命令（无 API Key）
- **前置条件**: 确保 DEEPSEEK_API_KEY 和 OPENAI_API_KEY 都未设置
- **操作步骤**:
  ```bash
  cd "D:/my project/CodeCraft Agent"
  unset DEEPSEEK_API_KEY OPENAI_API_KEY
  python -m cli.main generate "实现一个hello函数"
  ```
- **预期结果**: 输出红色错误信息 "请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"
- **判定标准**: 退出码非 0，输出包含 "API_KEY"

### CLI-03: generate --fast 命令
- **前置条件**: 设置 DEEPSEEK_API_KEY 环境变量
- **操作步骤**:
  ```bash
  cd "D:/my project/CodeCraft Agent"
  export DEEPSEEK_API_KEY="your-key"
  python -m cli.main generate "实现一个计算阶乘的函数" --fast
  ```
- **预期结果**:
  - 输出包含 "快速模式：跳过代码审查"
  - 输出包含生成的 Python 代码（含 def 关键字）
  - 不包含 "代码审查通过" 或 "代码已自动修复"
- **判定标准**: 有代码输出，无审查信息

### CLI-04: generate 命令（完整模式）
- **前置条件**: 设置 DEEPSEEK_API_KEY 环境变量
- **操作步骤**:
  ```bash
  cd "D:/my project/CodeCraft Agent"
  export DEEPSEEK_API_KEY="your-key"
  python -m cli.main generate "实现一个快速排序算法"
  ```
- **预期结果**:
  - 输出包含 "正在生成代码"
  - 输出包含生成的 Python 代码（含 def 和排序逻辑）
  - 输出包含 "代码审查通过" 或 "代码已自动修复优化"
  - 输出包含评分数字
- **判定标准**: 有代码输出，有审查评分

---

## 十九、前端 Web UI

### WEB-01: 主页加载
- **前置条件**: 启动 Streamlit
- **操作步骤**:
  ```bash
  cd "D:/my project/CodeCraft Agent"
  streamlit run frontend/app.py --server.port 8501
  ```
  浏览器访问 http://localhost:8501
- **预期结果**:
  - 页面标题包含 "CodeCraft Agent"
  - 显示 "多Agent协作的智能代码生成助手"
  - 侧边栏有 "代码生成"、"历史记录"、"设置" 导航
  - 显示 4 个功能卡片（智能生成/代码审查/自动修复/测试生成）
  - 显示 4 个统计卡片（4 专业Agent / 8 状态节点 / 3轮自动修复 / ∞ 可能）
- **判定标准**: 所有元素可见，统计数字为实际值（非 67/81%）

### WEB-02: 设置页面配置 API Key
- **前置条件**: Web UI 已启动
- **操作步骤**:
  1. 点击侧边栏 "设置"
  2. 选择 API 类型（DeepSeek/OpenAI）
  3. 输入 API Key
  4. 点击保存
- **预期结果**:
  - 显示 "配置已保存" 提示
  - 配置状态显示 "已配置"
  - ~/.codecraft/config.json 文件被创建
- **判定标准**: 保存成功，配置文件存在

### WEB-03: 代码生成页面
- **前置条件**: API Key 已配置
- **操作步骤**:
  1. 点击侧边栏 "代码生成"
  2. 输入 "实现一个计算阶乘的函数"
  3. 点击 "生成代码"
- **预期结果**:
  - Agent 流水线显示各 Agent 状态变化（Generator→Reviewer→Debugger→TestGenerator）
  - 代码区域显示生成的 Python 代码
  - 评分仪表盘显示审查分数
  - 如有问题，问题列表显示具体 issue
  - 如有测试，测试代码区域显示生成的测试
- **判定标准**: 代码生成完成，有评分显示

### WEB-04: 快速模式
- **前置条件**: API Key 已配置
- **操作步骤**:
  1. 侧边栏开启 "跳过代码审查"
  2. 输入需求并生成
- **预期结果**:
  - Agent 流水线只显示 Generator
  - 不显示评分仪表盘
  - 生成速度更快
- **判定标准**: 无 Reviewer/Debugger 状态显示

### WEB-05: 历史记录页面
- **前置条件**: 已生成过至少一个代码
- **操作步骤**:
  1. 点击侧边栏 "历史记录"
- **预期结果**:
  - 显示之前生成的需求和代码
  - 每条记录显示时间戳和评分
  - 可以点击查看详细内容
- **判定标准**: 历史列表非空，信息完整

### WEB-06: XSS 防护验证
- **前置条件**: API Key 已配置
- **操作步骤**:
  1. 输入包含 HTML 标签的需求：`实现一个函数，返回 "<script>alert(1)</script>"`
  2. 生成代码
- **预期结果**:
  - 页面不弹出 alert 对话框
  - 代码区域显示转义后的文本：`<script>` 被显示为文本而非执行
- **判定标准**: 无 JavaScript 执行，HTML 标签被转义显示

---

## 二十、装配工厂（Factory）

> 2026-09-10 新增：`create_orchestrator()` 统一了 CLI 与 Streamlit 两处装配，对应 `tests/test_factory.py`（3 个用例）。

### FC-01: 完整模式注册四个Agent
- **前置条件**: 无（mock 掉 LLMFactory，不发起真实调用）
- **操作步骤**:
  ```python
  from unittest.mock import Mock, patch
  from backend.core.factory import create_orchestrator

  with patch("backend.core.factory.LLMFactory") as f:
      f.create.return_value = Mock()
      orch = create_orchestrator(api_key="test-key", model="test-model")
      print(f"注册的Agent: {sorted(orch.agents)}")
  ```
- **预期结果**:
  ```
  注册的Agent: ['debugger', 'generator', 'reviewer', 'test_generator']
  ```
- **判定标准**: 四个Agent全部注册，且共享同一个 LLM 实例

### FC-02: 快速模式只注册 generator
- **前置条件**: 无
- **操作步骤**:
  ```python
  from unittest.mock import Mock, patch
  from backend.core.factory import create_orchestrator

  with patch("backend.core.factory.LLMFactory") as f:
      f.create.return_value = Mock()
      orch = create_orchestrator(api_key="k", model="m", fast=True)
      print(f"注册的Agent: {sorted(orch.agents)}")
  ```
- **预期结果**:
  ```
  注册的Agent: ['generator']
  ```
- **判定标准**: 快速模式不装配 reviewer / debugger / test_generator

### FC-03: LLM 按调用方传入的参数创建
- **前置条件**: 无
- **操作步骤**:
  ```python
  from unittest.mock import Mock, patch
  from backend.core.factory import create_orchestrator

  with patch("backend.core.factory.LLMFactory") as f:
      f.create.return_value = Mock()
      create_orchestrator(api_key="key-1", model="model-1", base_url="https://example.com/v1")
      print(f"位置参数: {f.create.call_args.args}")
      print(f"api_key: {f.create.call_args.kwargs['api_key']}")
      print(f"base_url: {f.create.call_args.kwargs['base_url']}")
  ```
- **预期结果**:
  ```
  位置参数: ('openai', 'model-1')
  api_key: key-1
  base_url: https://example.com/v1
  ```
- **判定标准**: api_key / model / base_url 原样透传给 LLMFactory

---

## 测试执行记录模板

```
| 测试ID | 测试时间 | 执行结果 | 实际输出（关键部分） | 备注 |
|--------|----------|----------|---------------------|------|
| SM-01  |          | ✅/❌    |                     |      |
| SM-02  |          | ✅/❌    |                     |      |
| ...    |          |          |                     |      |
```

---

## 统计

| 类别 | 测试项数 |
|------|----------|
| 状态机 | 10 |
| 通信协议 | 0（整章废弃）|
| 共享上下文 | 5 |
| 代码生成 Agent | 4 |
| 代码审查 Agent | 5 |
| 调试 Agent | 3 |
| 测试生成 Agent | 3 |
| 协调器 | 7（OR-08 废弃）|
| 记忆系统 | 0（整章废弃）|
| LLM 抽象层 | 4 |
| Token 管理器 | 1 |
| AST 解析器 | 2 |
| 代码执行器 | 3（EX-04/05 废弃）|
| 输入验证 | 3 |
| 日志系统 | 3 |
| 安全验证 | 4 |
| 代码工具 | 2 |
| CLI 命令 | 4 |
| 前端 Web UI | 6 |
| 装配工厂 | 3 |
| **合计** | **72** |
