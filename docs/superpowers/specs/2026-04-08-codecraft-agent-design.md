# CodeCraft Agent 设计文档

> 创建时间: 2026-04-08

---

## 一、项目概述

### 1.1 项目定位

**CodeCraft Agent** 是一个基于多Agent协作的Python代码生成与优化助手，主要用于简历和面试展示，重点体现AI Agent架构设计能力。

### 1.2 核心能力展示

- **多Agent协作** - 多个专业Agent（代码生成、审查、测试、调试）协同工作
- **ReAct推理模式** - 展示"观察-思考-行动"的循环决策能力
- **工具调用系统** - 丰富的工具集（AST解析、Git操作、代码检查、沙箱执行）
- **记忆系统** - 会话记忆 + 长期记忆（项目知识、用户偏好）
- **多模型支持** - OpenAI/Claude可切换，展示架构设计能力

### 1.3 技术栈

- **语言**: Python 3.10+
- **框架**: LangChain / LangGraph
- **LLM**: OpenAI API / Claude API
- **CLI**: Typer + Rich
- **存储**: ChromaDB（向量存储）、SQLite（会话存储）

---

## 二、系统架构

### 2.1 目录结构

```
codecraft-agent/
├── backend/
│   ├── core/
│   │   ├── agent.py          # Agent基类
│   │   ├── orchestrator.py   # 多Agent协调器
│   │   ├── memory.py         # 记忆系统
│   │   ├── state.py          # 任务状态机
│   │   ├── context.py        # 共享上下文管理
│   │   └── protocol.py       # Agent间通信协议
│   ├── agents/
│   │   ├── code_generator.py # 代码生成Agent
│   │   ├── code_reviewer.py  # 代码审查Agent
│   │   ├── test_generator.py # 测试生成Agent
│   │   └── debugger.py       # 调试Agent
│   ├── tools/
│   │   ├── ast_parser.py     # AST解析
│   │   ├── git_tools.py      # Git操作
│   │   ├── linter.py         # 代码检查
│   │   ├── executor.py       # 代码执行
│   │   └── sandbox/          # 沙箱隔离
│   │       ├── docker_sandbox.py
│   │       └── subprocess_sandbox.py
│   ├── llm/
│   │   ├── base.py           # LLM抽象基类
│   │   ├── openai.py         # OpenAI实现
│   │   ├── claude.py         # Claude实现
│   │   └── token_manager.py  # Token管理
│   └── knowledge/
│       ├── patterns/         # 设计模式
│       ├── templates/        # 代码模板
│       └── best_practices/   # 最佳实践
├── cli/
│   └── main.py               # CLI入口
├── web/                      # Web界面（可选扩展）
└── tests/
```

### 2.2 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层 (CLI/Web)                   │
├─────────────────────────────────────────────────────────┤
│                    Orchestrator (协调层)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 状态机      │  │ 上下文管理   │  │ 消息路由    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                    Agent层 (业务逻辑)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Generator   │  │ Reviewer    │  │ Debugger    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐                                        │
│  │ Test Gen    │                                        │
│  └─────────────┘                                        │
├─────────────────────────────────────────────────────────┤
│                    工具层 (能力扩展)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ AST Parser  │  │ Linter      │  │ Executor    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                    基础设施层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ LLM适配     │  │ 记忆系统    │  │ 知识库      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 三、核心模块设计

### 3.1 Agent基类 (core/agent.py)

```python
from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain.agents import AgentExecutor

class BaseAgent(ABC):
    """Agent基类，定义统一接口"""

    def __init__(self, name: str, llm: Any, tools: list):
        self.name = name
        self.llm = llm
        self.tools = tools
        self.memory = None

    @abstractmethod
    def process(self, input_data: dict, context: dict) -> dict:
        """处理任务，返回结果"""
        pass

    def observe(self, state: dict) -> dict:
        """观察当前状态"""
        return {"observation": state}

    def think(self, observation: dict) -> str:
        """推理下一步行动"""
        pass

    def act(self, thought: str) -> dict:
        """执行行动"""
        pass
```

### 3.2 任务状态机 (core/state.py)

```python
from enum import Enum
from typing import Optional

class TaskState(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待处理
    ANALYZING = "analyzing"       # 分析中
    GENERATING = "generating"     # 生成代码中
    REVIEWING = "reviewing"       # 审查代码中
    FIXING = "fixing"             # 修复问题中
    TESTING = "testing"           # 测试中
    DONE = "done"                 # 完成
    FAILED = "failed"             # 失败

class StateMachine:
    """任务状态机"""

    TRANSITIONS = {
        TaskState.PENDING: [TaskState.ANALYZING],
        TaskState.ANALYZING: [TaskState.GENERATING, TaskState.REVIEWING],
        TaskState.GENERATING: [TaskState.REVIEWING, TaskState.FAILED],
        TaskState.REVIEWING: [TaskState.TESTING, TaskState.FIXING, TaskState.DONE],
        TaskState.FIXING: [TaskState.REVIEWING, TaskState.GENERATING],
        TaskState.TESTING: [TaskState.DONE, TaskState.FIXING],
        TaskState.DONE: [],
        TaskState.FAILED: [TaskState.PENDING],
    }

    def __init__(self):
        self.current_state = TaskState.PENDING
        self.history = []

    def transition(self, next_state: TaskState) -> bool:
        """状态转换"""
        if next_state in self.TRANSITIONS[self.current_state]:
            self.history.append(self.current_state)
            self.current_state = next_state
            return True
        return False

    def can_transition_to(self, state: TaskState) -> bool:
        """检查是否可以转换到目标状态"""
        return state in self.TRANSITIONS[self.current_state]
```

### 3.3 Agent间通信协议 (core/protocol.py)

```python
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
import time
import uuid

class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGN = "task_assign"       # 任务分配
    RESULT_RETURN = "result_return"   # 结果返回
    QUERY_REQUEST = "query_request"   # 查询请求
    FEEDBACK = "feedback"             # 反馈消息
    ERROR = "error"                   # 错误消息

@dataclass
class AgentMessage:
    """Agent间通信消息"""
    sender: str
    receiver: str
    msg_type: MessageType
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "msg_type": self.msg_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }
```

### 3.4 Orchestrator (core/orchestrator.py)

```python
from typing import Any, Optional
from .state import TaskState, StateMachine
from .protocol import AgentMessage, MessageType
from .context import SharedContext

class Orchestrator:
    """多Agent协调器"""

    def __init__(self, agents: dict, context: SharedContext):
        self.agents = agents  # {name: agent_instance}
        self.context = context
        self.state_machine = StateMachine()
        self.message_queue = []

    def process_request(self, user_request: str) -> dict:
        """处理用户请求的主入口"""
        # 1. 任务分析和拆解
        self.state_machine.transition(TaskState.ANALYZING)
        task_type = self._analyze_task(user_request)

        # 2. 根据任务类型路由到对应Agent
        result = self._route_task(task_type, user_request)

        # 3. 处理反馈闭环
        while not self._is_terminal_state():
            result = self._handle_feedback(result)

        return result

    def _analyze_task(self, request: str) -> str:
        """分析任务类型"""
        # 使用LLM分析任务类型
        pass

    def _route_task(self, task_type: str, request: str) -> dict:
        """路由任务到对应Agent"""
        pass

    def _handle_feedback(self, result: dict) -> dict:
        """处理Agent间的反馈闭环"""
        # Reviewer发现问题 → Debugger修复 → 重新Review
        # 测试失败 → Debugger修复 → 重新测试
        pass

    def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """发送消息给指定Agent"""
        if message.receiver in self.agents:
            agent = self.agents[message.receiver]
            return agent.receive_message(message)
        return None
```

### 3.5 记忆系统 (core/memory.py)

```python
from typing import Any, Optional
from datetime import datetime
import json

class Memory:
    """记忆系统基类"""

    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def add(self, key: str, value: Any, memory_type: str = "short"):
        """添加记忆"""
        if memory_type == "short":
            self.short_term.add(key, value)
        else:
            self.long_term.add(key, value)

    def recall(self, query: str, k: int = 5) -> list:
        """回忆相关信息"""
        # 先查短期记忆
        short_results = self.short_term.search(query, k)
        # 再查长期记忆（向量检索）
        long_results = self.long_term.search(query, k)
        return short_results + long_results

class ShortTermMemory:
    """短期记忆（会话级别）"""

    def __init__(self, max_items: int = 100):
        self.items = []
        self.max_items = max_items

    def add(self, key: str, value: Any):
        self.items.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def search(self, query: str, k: int) -> list:
        return self.items[-k:]

class LongTermMemory:
    """长期记忆（持久化 + 向量检索）"""

    def __init__(self, storage_path: str = "./memory/storage"):
        self.storage_path = storage_path
        self.vectorstore = None  # ChromaDB

    def add(self, key: str, value: Any):
        # 存储到向量数据库
        pass

    def search(self, query: str, k: int) -> list:
        # 向量相似度检索
        pass
```

### 3.6 LLM抽象层 (llm/base.py)

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseLLM(ABC):
    """LLM抽象基类"""

    @abstractmethod
    def invoke(self, messages: list, **kwargs) -> str:
        """调用模型"""
        pass

    @abstractmethod
    def stream(self, messages: list, **kwargs):
        """流式调用"""
        pass

class LLMFactory:
    """LLM工厂"""

    @staticmethod
    def create(provider: str, model: str, **kwargs) -> BaseLLM:
        if provider == "openai":
            from .openai import OpenAILLM
            return OpenAILLM(model, **kwargs)
        elif provider == "claude":
            from .claude import ClaudeLLM
            return ClaudeLLM(model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

### 3.7 Token管理器 (llm/token_manager.py)

```python
from typing import Any

class TokenManager:
    """Token管理器"""

    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self.current_usage = 0

    def estimate_tokens(self, text: str) -> int:
        """估算文本Token数"""
        # 简单估算：中文约1.5字符/token，英文约4字符/token
        return len(text) // 3

    def should_compress(self, context: str) -> bool:
        """判断是否需要压缩上下文"""
        return self.estimate_tokens(context) > self.max_tokens * 0.8

    def summarize_history(self, messages: list) -> str:
        """压缩历史对话"""
        # 使用LLM总结历史
        pass

    def track_usage(self, usage: int):
        """追踪Token使用量"""
        self.current_usage += usage
```

---

## 四、Agent详细设计

### 4.1 代码生成Agent (agents/code_generator.py)

**职责**: 根据需求生成Python代码

**工具**:
- `ast_parser`: 解析现有代码结构
- `template_loader`: 加载代码模板
- `knowledge_search`: 搜索设计模式和最佳实践

**Prompt模板**:
```
你是一个专业的Python代码生成专家。

用户需求: {requirement}
项目上下文: {context}
相关设计模式: {patterns}

请生成符合以下要求的代码:
1. 遵循PEP 8规范
2. 添加类型注解
3. 包含docstring
4. 考虑异常处理

输出格式:
```python
# 代码实现
```

解释: [设计思路说明]
```

### 4.2 代码审查Agent (agents/code_reviewer.py)

**职责**: 审查代码质量，发现问题

**工具**:
- `linter`: 代码静态检查
- `ast_parser`: 代码结构分析
- `security_checker`: 安全漏洞检查

**审查维度**:
1. 代码规范（PEP 8）
2. 潜在Bug
3. 性能问题
4. 安全隐患
5. 可维护性

**输出格式**:
```json
{
  "passed": false,
  "issues": [
    {
      "severity": "high",
      "type": "security",
      "line": 42,
      "message": "SQL注入风险",
      "suggestion": "使用参数化查询"
    }
  ],
  "score": 75
}
```

### 4.3 调试Agent (agents/debugger.py)

**职责**: 分析错误并修复代码

**工具**:
- `executor`: 执行代码
- `error_analyzer`: 分析错误信息
- `search_similar`: 搜索相似问题的解决方案

**工作流程**:
1. 执行代码，捕获错误
2. 分析错误类型和原因
3. 定位问题代码位置
4. 生成修复方案
5. 验证修复效果

### 4.4 测试生成Agent (agents/test_generator.py)

**职责**: 为代码生成测试用例

**工具**:
- `ast_parser`: 分析代码结构
- `coverage_analyzer`: 分析覆盖率

**测试类型**:
1. 单元测试
2. 边界测试
3. 异常测试
4. 集成测试（可选）

---

## 五、工具层设计

### 5.1 AST解析器 (tools/ast_parser.py)

```python
import ast
from typing import Any

class ASTParser:
    """Python AST解析器"""

    def parse(self, code: str) -> ast.Module:
        """解析代码为AST"""
        return ast.parse(code)

    def extract_functions(self, tree: ast.Module) -> list:
        """提取所有函数定义"""
        return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def extract_classes(self, tree: ast.Module) -> list:
        """提取所有类定义"""
        return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def extract_imports(self, tree: ast.Module) -> list:
        """提取所有导入"""
        return [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

    def get_function_signature(self, func: ast.FunctionDef) -> dict:
        """获取函数签名"""
        return {
            "name": func.name,
            "args": [arg.arg for arg in func.args.args],
            "returns": ast.unparse(func.returns) if func.returns else None,
            "docstring": ast.get_docstring(func),
        }
```

### 5.2 沙箱执行器 (tools/sandbox/subprocess_sandbox.py)

```python
import subprocess
import tempfile
import os
from typing import Any

class SubprocessSandbox:
    """子进程沙箱执行器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def execute(self, code: str) -> dict:
        """在沙箱中执行代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._get_safe_env()
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "执行超时"}
        finally:
            os.unlink(temp_path)

    def _get_safe_env(self) -> dict:
        """获取安全的环境变量"""
        return {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "",
        }
```

---

## 六、协作流程

### 6.1 完整协作流程图

```
用户请求
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1. 任务分析 → [ANALYZING]                         │   │
│  │    - 解析用户意图                                 │   │
│  │    - 确定任务类型                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                        │                                │
│                        ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 2. 任务分发 → [GENERATING]                        │   │
│  │    - 路由到Generator                              │   │
│  │    - 生成初始代码                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                        │                                │
│                        ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 3. 代码审查 → [REVIEWING]                         │   │
│  │    - Reviewer检查代码                             │   │
│  │    - 通过 → 进入测试                              │   │
│  │    - 不通过 → 进入修复                            │   │
│  └─────────────────────────────────────────────────┘   │
│                        │                                │
│            ┌───────────┴───────────┐                   │
│            ▼                       ▼                   │
│     [TESTING]                  [FIXING]                │
│        │                          │                    │
│        ▼                          ▼                    │
│   Test Generator              Debugger                 │
│        │                          │                    │
│        │         ┌────────────────┘                    │
│        │         │                                     │
│        ▼         ▼                                     │
│     测试通过?  ──否──→  返回Reviewing                   │
│        │                                                │
│       是                                                │
│        │                                                │
│        ▼                                                │
│     [DONE]                                              │
│        │                                                │
│        ▼                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 4. 结果聚合                                       │   │
│  │    - 整合所有Agent输出                            │   │
│  │    - 存储到记忆系统                               │   │
│  │    - 返回用户                                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
返回用户
```

### 6.2 反馈闭环机制

```python
# Orchestrator中的反馈处理逻辑
def _handle_feedback(self, result: dict) -> dict:
    """处理Agent间的反馈闭环"""

    while True:
        # 审查阶段
        if self.state_machine.current_state == TaskState.REVIEWING:
            review_result = self.agents["reviewer"].process(result)

            if review_result["passed"]:
                self.state_machine.transition(TaskState.TESTING)
            else:
                self.state_machine.transition(TaskState.FIXING)
                result["issues"] = review_result["issues"]

        # 修复阶段
        elif self.state_machine.current_state == TaskState.FIXING:
            fix_result = self.agents["debugger"].process(result)
            result["code"] = fix_result["fixed_code"]
            self.state_machine.transition(TaskState.REVIEWING)

        # 测试阶段
        elif self.state_machine.current_state == TaskState.TESTING:
            test_result = self.agents["test_generator"].process(result)

            if test_result["passed"]:
                self.state_machine.transition(TaskState.DONE)
                return result
            else:
                self.state_machine.transition(TaskState.FIXING)
                result["test_failures"] = test_result["failures"]

        # 完成状态
        elif self.state_machine.current_state == TaskState.DONE:
            return result
```

---

## 七、CLI设计

### 7.1 命令结构

```bash
# 生成代码
codecraft generate "实现一个快速排序算法"

# 审查代码
codecraft review ./my_module.py

# 调试代码
codecraft debug ./broken_code.py --error "IndexError"

# 生成测试
codecraft test ./my_module.py

# 交互模式
codecraft chat
```

### 7.2 CLI实现 (cli/main.py)

```python
import typer
from rich.console import Console
from rich.markdown import Markdown

app = typer.Typer()
console = Console()

@app.command()
def generate(requirement: str):
    """生成代码"""
    console.print(f"[bold blue]正在生成代码...[/bold blue]")

    orchestrator = get_orchestrator()
    result = orchestrator.process_request(requirement)

    console.print(Markdown(f"```python\n{result['code']}\n```"))

@app.command()
def review(file_path: str):
    """审查代码"""
    with open(file_path, 'r') as f:
        code = f.read()

    orchestrator = get_orchestrator()
    result = orchestrator.agents["reviewer"].process({"code": code})

    if result["passed"]:
        console.print("[bold green]代码审查通过![/bold green]")
    else:
        console.print("[bold red]发现问题:[/bold red]")
        for issue in result["issues"]:
            console.print(f"  - [{issue['severity']}] {issue['message']}")

@app.command()
def chat():
    """交互模式"""
    console.print("[bold green]CodeCraft Agent 交互模式[/bold green]")
    console.print("输入 'exit' 退出\n")

    orchestrator = get_orchestrator()

    while True:
        user_input = console.input("[bold blue]You:[/bold blue] ")
        if user_input.lower() == 'exit':
            break

        result = orchestrator.process_request(user_input)
        console.print(Markdown(result["response"]))

if __name__ == "__main__":
    app()
```

---

## 八、实现优先级

### Phase 1: 核心链路 (预计3-5天)

- [ ] 项目初始化和依赖配置
- [ ] Agent基类实现
- [ ] Orchestrator基础框架
- [ ] OpenAI LLM适配
- [ ] Generator Agent实现
- [ ] 简单CLI交互

**里程碑**: 能够通过CLI生成简单Python代码

### Phase 2: 多Agent协作 (预计5-7天)

- [ ] 任务状态机实现
- [ ] Agent通信协议
- [ ] Reviewer Agent实现
- [ ] Debugger Agent实现
- [ ] 反馈闭环机制
- [ ] 基础记忆系统

**里程碑**: 多Agent协作完成代码生成→审查→修复闭环

### Phase 3: 工具能力 (预计3-5天)

- [ ] AST解析器
- [ ] Linter集成
- [ ] 沙箱执行器
- [ ] Test Generator Agent

**里程碑**: 完整的工具链支持

### Phase 4: 增强特性 (预计5-7天)

- [ ] Claude LLM适配
- [ ] Token管理器
- [ ] 长期记忆（向量存储）
- [ ] 知识库构建
- [ ] Web界面（可选）

**里程碑**: 生产级功能完善

---

## 九、测试策略

### 9.1 单元测试

- 每个Agent独立测试
- 工具函数测试
- 状态机转换测试

### 9.2 集成测试

- 多Agent协作流程测试
- 端到端CLI测试

### 9.3 评估基准

- 代码生成质量评估
- 代码审查准确率
- Bug修复成功率

---

## 十、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM API成本高 | 高 | Token管理器 + 本地缓存 |
| 代码执行安全 | 高 | 沙箱隔离 + 超时限制 |
| 多Agent协调复杂 | 中 | 状态机 + 清晰的消息协议 |
| 生成代码质量不稳定 | 中 | Reviewer多轮审查 + 人工反馈 |

---

*文档版本: 1.0*
*最后更新: 2026-04-08*
