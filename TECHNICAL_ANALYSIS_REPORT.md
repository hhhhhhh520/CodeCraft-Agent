# CodeCraft Agent 项目完整技术分析报告

**时点快照声明（2026-09-06 初版 / 2026-09-10 复核补全）**: 本文是 **2026-04-15 的分析快照**。文中的数据（"80个测试用例"、"81%覆盖率"）、目录结构、代码片段**全部是当时状态，不代表当前代码**。

此后项目发生过以下删除 —— 本文相应段落保留，仅作历史记录，**不要按文中代码执行**：

| 已移除 | 时间 | 说明 |
|---|---|---|
| `backend/core/protocol.py`（AgentMessage / MessageType） | 2026-06-28 | 死代码、零调用方；`tests/test_protocol.py` 同步删除 |
| `BaseAgent.observe() / think() / act()` | Phase 7 | 未被使用的 ReAct 骨架方法 |
| `CodeExecutor.safe_exec()` 及其 `safe_getattr` 白名单 | Phase 8 | exec 沙箱整体移除，统一改走 subprocess `execute()` |
| `backend/core/memory.py`、`backend/core/vector_memory.py` | 2026-09-10 | 实现后从未被主流程调用；`tests/test_memory.py`、`tests/test_vector_memory.py` 同步删除 |
| `Orchestrator.send_message()` | 2026-06-28 | 依赖 protocol.py，随其一起删除 |
| `BaseAgent.receive_message()` | 2026-09-10 | 依赖已删的 protocol.py，零调用 |
| `demos/`（4 个演示脚本 + 运行脚本 + 演示指南） | 2026-09-10 | 引用已删的记忆模块 |
| 依赖 `langchain` / `langchain-openai` / `langchain-anthropic` / `chromadb` / `numpy` | 2026-09-10 | 代码中从未 import |

**当前状态**（118 个测试全部通过、backend 覆盖率约 74%）请以 [PROGRESS.md](PROGRESS.md)、[README.md](README.md) 为准。

> 分析日期: 2026-04-15
> 项目版本: v0.2.0
> 分析范围: 全部源代码、测试、文档

---

## 目录

1. [项目概述](#一项目概述)
2. [系统架构分析](#二系统架构分析)
3. [核心模块详解](#三核心模块详解)
4. [专业Agent实现](#四专业agent实现)
5. [LLM抽象层](#五llm抽象层)
6. [工具层设计](#六工具层设计)
7. ~~[记忆系统](#七记忆系统)~~ ⚠️ 已移除
8. [错误处理与日志](#八错误处理与日志)
9. [前端实现](#九前端实现)
10. [CLI实现](#十cli实现)
11. [测试体系](#十一测试体系)
12. [技术栈分析](#十二技术栈分析)
13. [设计模式应用](#十三设计模式应用)
14. [项目亮点](#十四项目亮点)
15. [面试展示价值](#十五面试展示价值)
16. [改进建议](#十六改进建议)

---

## 一、项目概述

### 1.1 项目定位

**CodeCraft Agent** 是一个基于多Agent协作的Python代码生成与优化助手。核心价值在于实现 **代码生成 → 审查 → 修复 → 测试** 的完整自动化闭环。

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| **多Agent协作** | Generator、Reviewer、Debugger、TestGenerator 四个专业Agent分工协作 |
| **反馈闭环** | 审查不通过自动修复，最多3次迭代 |
| **状态机管理** | 8状态有限状态机，确保任务流转可控 |
| **多模型支持** | OpenAI、Claude、DeepSeek 可切换（DeepSeek 经 base_url 复用 OpenAI 兼容接口） |
| ~~**向量记忆**~~ | ⚠️ ~~ChromaDB语义检索历史代码~~（2026-09-10 已移除） |
| **双入口** | CLI (Typer) + Web (Streamlit) |
| **高测试覆盖** | 80个测试用例（快照口径；当前 118 个） |

### 1.3 项目规模

| 指标 | 数值 |
|------|------|
| 代码行数 | ~3000行 |
| 模块数量 | 17个核心模块 |
| 测试文件 | 16个 |
| Agent数量 | 4个 |
| 状态数量 | 8个 |
| 错误码数量 | 14种 |

---

## 二、系统架构分析

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│           CLI (Typer/Rich)  │  Web (Streamlit)              │
├─────────────────────────────────────────────────────────────┤
│                       协调层                                 │
│    Orchestrator  │  StateMachine  │  SharedContext          │
├─────────────────────────────────────────────────────────────┤
│                       Agent层                                │
│  Generator  │  Reviewer  │  Debugger  │  TestGenerator      │
├─────────────────────────────────────────────────────────────┤
│                       工具层                                 │
│           AST Parser  │  Code Executor                      │
├─────────────────────────────────────────────────────────────┤
│                     基础设施层                               │
│   LLM Adapter  │  Token Manager  │  Logger     │  (Memory 已移除) │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
D:\my project\CodeCraft Agent/
├── backend/                          # 后端核心模块
│   ├── __init__.py                   # 包初始化，版本号 v0.2.0
│   ├── core/                         # 核心框架层
│   │   ├── agent.py                  # Agent基类（⚠️ ReAct骨架observe/think/act已移除）
│   │   ├── orchestrator.py           # 多Agent协调器
│   │   ├── state.py                  # 8状态有限状态机
│   │   ├── context.py                # 共享上下文（线程安全）
│   │   ├── factory.py                # Orchestrator装配工厂（2026-09-10 新增）
│   │   ├── protocol.py               # ⚠️ 已于 2026-06-28 移除
│   │   ├── memory.py                 # ⚠️ 已于 2026-09-10 移除
│   │   ├── vector_memory.py          # ⚠️ 已于 2026-09-10 移除
│   │   ├── logger.py                 # 日志系统（敏感信息脱敏）
│   │   └── errors.py                 # 统一错误处理
│   ├── agents/                       # 专业Agent实现
│   │   ├── code_generator.py         # 代码生成Agent
│   │   ├── code_reviewer.py          # 代码审查Agent
│   │   ├── debugger.py               # 调试/修复Agent
│   │   └── test_generator.py         # 测试生成Agent
│   ├── llm/                          # LLM抽象层
│   │   ├── base.py                   # LLM抽象基类 + 工厂模式
│   │   ├── openai_llm.py             # OpenAI实现（支持DeepSeek）
│   │   ├── claude_llm.py             # Claude实现
│   │   └── token_manager.py          # Token管理器
│   ├── tools/                        # 工具层
│   │   ├── ast_parser.py             # AST语法解析器
│   │   └── executor.py               # 沙箱代码执行器
│   └── utils/                        # 工具函数
│       └── code_utils.py             # 代码处理工具
├── frontend/                         # Streamlit Web界面
│   ├── app.py                        # 主入口
│   ├── components/                   # UI组件
│   │   ├── agent_status.py           # Agent状态可视化
│   │   ├── code_display.py           # 代码展示组件
│   │   └── streaming_display.py      # 流式输出组件
│   ├── pages/                        # 页面
│   │   ├── chat.py                   # 代码生成页面
│   │   ├── history.py                # 历史记录页面
│   │   └── settings.py               # 设置页面
│   └── utils/                        # 前端工具
│       └── session.py                # 会话状态管理
├── cli/                              # 命令行界面
│   └── main.py                       # CLI入口
├── tests/                            # 测试文件（17个）
├── docs/                             # 文档
│   └── assets/architecture.md        # 架构图文档
├── demos/                            # 演示脚本
├── pyproject.toml                    # 项目配置
├── requirements.txt                  # 依赖清单
├── HIGHLIGHTS.md                     # 技术亮点文档
└── INTERVIEW_GUIDE.md                # 面试指南
```

### 2.3 数据流图

```
用户输入
    │
    ▼
┌─────────────┐
│ CLI / Web   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ Orchestrator│────▶│ StateMachine │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│ 任务分析    │ ─── 关键词匹配: 生成/审查/调试/测试
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Agent路由   │
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Generator  │───▶│  Reviewer   │───▶│  Debugger   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       │                  ▼                  │
       │           ┌─────────────┐           │
       │           │ 审查通过？  │           │
       │           └──────┬──────┘           │
       │                  │                  │
       │         ┌────────┴────────┐         │
       │         ▼                 ▼         │
       │    [通过] Done        [不通过]──────┘
       │                                    │
       └────────────────────────────────────┘
                        反馈闭环 (最多3次)
```

---

## 三、核心模块详解

### 3.1 Agent基类 (`backend/core/agent.py`)

> ⚠️ **下方为 2026-04 快照**：`memory` 参数与 `observe()/think()/act()` 方法均已移除；当前 `BaseAgent` 只有 `__init__()`（name/llm/tools）与抽象方法 `process()`。

#### 设计理念: ReAct推理模式（已不适用）

```python
class BaseAgent(ABC):
    """Agent基类 - 支持ReAct模式"""

    def __init__(
        self,
        name: str,
        llm: Any,
        tools: list[Any],
        memory: Optional[Any] = None,
    ) -> None:
        self.name = name
        self.llm = llm
        self.tools = tools
        self.memory = memory

    @abstractmethod
    def process(self, input_data: dict, context: dict) -> dict:
        """处理任务 - 子类必须实现"""
        pass

    def observe(self, state: dict) -> dict:
        """观察当前状态"""
        return {"observation": state}

    def think(self, observation: dict) -> str:
        """推理下一步行动"""
        return f"Agent {self.name} thinking about {observation}"

    def act(self, thought: str) -> dict:
        """执行行动"""
        return {"action": "default", "thought": thought}

    def receive_message(self, message: Any) -> Optional[dict]:
        """接收消息"""
        return self.process(message.payload, {})
```

#### ReAct循环

```
┌─────────────────────────────────────────────────┐
│                   ReAct Loop                     │
│                                                  │
│    ┌─────────┐      ┌─────────┐      ┌────────┐ │
│    │ Observe │ ───▶ │  Think  │ ───▶ │  Act   │ │
│    └─────────┘      └─────────┘      └────────┘ │
│         ▲                                   │    │
│         └───────────────────────────────────┘    │
│                    反馈循环                       │
└─────────────────────────────────────────────────┘
```

### 3.2 状态机 (`backend/core/state.py`)

#### 8状态定义

```python
class TaskState(Enum):
    PENDING = "pending"       # 等待处理
    ANALYZING = "analyzing"   # 分析中
    GENERATING = "generating" # 生成代码中
    REVIEWING = "reviewing"   # 审查代码中
    FIXING = "fixing"         # 修复问题中
    TESTING = "testing"       # 测试中
    DONE = "done"             # 完成
    FAILED = "failed"         # 失败
```

#### 状态转换矩阵

```python
TRANSITIONS: dict[TaskState, list[TaskState]] = {
    TaskState.PENDING: [TaskState.ANALYZING],
    TaskState.ANALYZING: [TaskState.GENERATING, TaskState.REVIEWING],
    TaskState.GENERATING: [TaskState.REVIEWING, TaskState.FAILED],
    TaskState.REVIEWING: [TaskState.TESTING, TaskState.FIXING, TaskState.DONE],
    TaskState.FIXING: [TaskState.REVIEWING, TaskState.GENERATING],
    TaskState.TESTING: [TaskState.DONE, TaskState.FIXING],
    TaskState.DONE: [],
    TaskState.FAILED: [TaskState.PENDING],
}
```

#### 状态转换图

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
              ┌──────────┐                                    │
              │ PENDING  │                                    │
              └────┬─────┘                                    │
                   │                                          │
                   ▼                                          │
              ┌──────────┐                                    │
              │ ANALYZING│                                    │
              └────┬─────┘                                    │
                   │                                          │
         ┌────────┴────────┐                                  │
         ▼                 ▼                                  │
   ┌──────────┐      ┌──────────┐                             │
   │GENERATING│      │REVIEWING │◀─────────────────┐          │
   └────┬─────┘      └────┬─────┘                  │          │
        │                 │                        │          │
        │         ┌───────┼───────┐                │          │
        │         ▼       ▼       ▼                │          │
        │    ┌────────┐ ┌──────┐ ┌──────┐          │          │
        │    │TESTING │ │FIXING│ │ DONE │          │          │
        │    └───┬────┘ └──┬───┘ └──────┘          │          │
        │        │         │                      │          │
        │        ▼         └──────────────────────┘          │
        │   ┌──────┐                                       │
        │   │ DONE │                                       │
        │   └──────┘                                       │
        │                                                  │
        ▼                                                  │
   ┌──────────┐                                            │
   │  FAILED  │────────────────────────────────────────────┘
   └──────────┘                    重试
```

#### 核心方法

```python
def transition(self, next_state: TaskState) -> bool:
    """执行状态转换"""
    if self.can_transition_to(next_state):
        self.history.append(self.current_state)  # 记录历史
        self.current_state = next_state
        return True
    return False

def can_transition_to(self, state: TaskState) -> bool:
    """检查是否可以转换"""
    return state in self.TRANSITIONS[self.current_state]
```

### 3.3 Orchestrator协调器 (`backend/core/orchestrator.py`)

#### 核心职责

| 职责 | 描述 |
|------|------|
| 任务分析 | 根据关键词识别任务类型 |
| 任务路由 | 将任务分发给对应Agent |
| Agent协调 | 管理Agent间的协作流程 |
| 状态管理 | 驱动状态机转换 |
| 反馈闭环 | 处理审查-修复循环 |

#### 主流程实现

```python
def process_request(self, user_request: str) -> dict:
    """处理用户请求 - 主流程"""
    # 1. 保存请求到上下文
    self.context.set("user_request", user_request)

    # 2. 任务分析 (PENDING → ANALYZING)
    self.state_machine.transition(TaskState.ANALYZING)
    task_type = self._analyze_task(user_request)

    # 3. 任务路由 (ANALYZING → GENERATING)
    result = self._route_task(task_type, user_request)

    # 4. 反馈闭环处理
    if "reviewer" in self.agents and "debugger" in self.agents:
        result = self._handle_feedback_loop(result)

    # 5. 标记完成
    self.state_machine.transition(TaskState.DONE)
    return result
```

#### 任务类型分析

```python
def _analyze_task(self, request: str) -> str:
    """分析任务类型"""
    request_lower = request.lower()

    if any(kw in request_lower for kw in ["生成", "实现", "写", "generate", "create"]):
        return "generate"
    elif any(kw in request_lower for kw in ["审查", "检查", "review", "check"]):
        return "review"
    elif any(kw in request_lower for kw in ["调试", "修复", "debug", "fix"]):
        return "debug"
    elif any(kw in request_lower for kw in ["测试", "test"]):
        return "test"
    else:
        return "generate"  # 默认
```

#### 反馈闭环机制

```python
def _handle_feedback_loop(self, result: dict, max_iterations: int = 3) -> dict:
    """处理反馈闭环 - 最多3次迭代"""
    iteration = 0

    while iteration < max_iterations:
        # 审查阶段
        review_result = self.agents["reviewer"].process(
            {"code": result.get("code", "")},
            self.context.data,
        )

        if review_result.get("passed", True):
            # 审查通过，进入测试阶段
            result["review_score"] = review_result.get("score", 100)

            # 如果有 test_generator，执行测试生成
            if "test_generator" in self.agents:
                self.state_machine.transition(TaskState.TESTING)
                test_result = self.agents["test_generator"].process(
                    {"code": result.get("code", "")},
                    self.context.data,
                )
                result["test_code"] = test_result.get("test_code", "")
                result["test_passed"] = test_result.get("passed", True)

            # 测试完成，标记完成
            self.state_machine.transition(TaskState.DONE)
            return result
        else:
            # 审查不通过，进入修复
            self.state_machine.transition(TaskState.FIXING)
            fix_result = self.agents["debugger"].process(
                {"code": result.get("code", ""), "issues": review_result.get("issues", [])},
                self.context.data,
            )
            result["code"] = fix_result.get("fixed_code", result.get("code", ""))
            iteration += 1
            # 重新审查
            self.state_machine.transition(TaskState.REVIEWING)

    return result
```

**新增特性**：
- 审查通过后自动进入 TESTING 状态
- 调用 TestGeneratorAgent 生成测试用例
- 返回结果包含 `test_code` 和 `test_passed`

### 3.4 Agent通信协议 (`backend/core/protocol.py`) ⚠️ 已移除（2026-06-28）

> 死代码、零调用方，已于 2026-06-28 连同 `tests/test_protocol.py` 一起删除。以下仅作历史记录。

#### 消息类型

```python
class MessageType(Enum):
    TASK_ASSIGN = "task_assign"      # 任务分配
    RESULT_RETURN = "result_return"  # 结果返回
    QUERY_REQUEST = "query_request"  # 查询请求
    FEEDBACK = "feedback"            # 反馈消息
    ERROR = "error"                  # 错误消息
```

#### 消息结构

```python
@dataclass
class AgentMessage:
    sender: str                        # 发送者名称
    receiver: str                      # 接收者名称
    msg_type: MessageType              # 消息类型
    payload: dict[str, Any]            # 消息内容
    correlation_id: str = field(...)   # 关联ID（追踪任务链）
    timestamp: float = field(...)      # 时间戳
```

**设计要点**：
- `correlation_id`: 用于追踪完整的任务链路
- `timestamp`: 支持时序分析和性能监控
- `payload`: 灵活的字典结构，适应不同消息类型

### 3.5 共享上下文 (`backend/core/context.py`)

#### 线程安全设计

```python
class SharedContext:
    """共享上下文 - 使用RLock确保线程安全"""

    def __init__(self) -> None:
        self.task_id: str = str(uuid.uuid4())
        self.data: dict[str, Any] = {}
        self._lock = threading.RLock()  # 可重入锁

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.data[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        with self._lock:
            return self.data.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.data.update(data)

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {"task_id": self.task_id, "data": self.data.copy()}
```

**为什么用 RLock 而不是 Lock**：
- 支持同一线程多次获取锁（可重入）
- 避免嵌套调用时的死锁风险
- 适合复杂调用链场景

---

## 四、专业Agent实现

### 4.1 CodeGeneratorAgent (`backend/agents/code_generator.py`)

#### Prompt设计

```python
SYSTEM_PROMPT = """你是一个专业的Python代码生成专家。

请根据用户需求生成高质量的Python代码，要求：
1. 遵循PEP 8规范
2. 添加类型注解
3. 包含docstring
4. 考虑异常处理

直接输出代码，使用```python代码块包裹。"""
```

**设计要点**：
- 明确角色定位（Python代码生成专家）
- 4个具体质量要求
- 输出格式约束（代码块包裹）

#### 处理流程

```python
def process(self, input_data: dict, context: dict) -> dict:
    requirement = input_data.get("requirement", "")

    messages = [
        {"role": "system", "content": self.SYSTEM_PROMPT},
        {"role": "user", "content": f"请实现：{requirement}"},
    ]

    response = self.llm.invoke(messages)
    code = self._extract_code(response)

    return {
        "code": code,
        "raw_response": response,
        "requirement": requirement,
    }
```

#### 代码提取容错机制

```python
def _extract_code(self, response: str) -> str:
    # 优先匹配 ```python ... ```
    pattern = r"```python\s*\n(.*?)\n```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0]

    # 兜底匹配 ``` ... ```
    pattern = r"```\s*\n(.*?)\n```"
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return matches[0]

    # 最后返回原始响应
    return response.strip()
```

### 4.2 CodeReviewerAgent (`backend/agents/code_reviewer.py`)

#### 多维度审查框架

```python
SYSTEM_PROMPT = """你是一个专业的Python代码审查专家。

请审查给定的代码，从以下维度评估：
1. 代码规范（PEP 8）
2. 潜在Bug
3. 性能问题
4. 安全隐患
5. 可维护性

以JSON格式返回审查结果：
{
    "passed": true/false,
    "issues": [
        {
            "severity": "high/medium/low",
            "type": "security/performance/style/bug",
            "line": 行号,
            "message": "问题描述",
            "suggestion": "改进建议"
        }
    ],
    "score": 0-100,
    "summary": "总体评价"
}

只返回JSON，不要其他内容。"""
```

**审查维度**：

| 维度 | 关注点 | 示例问题 |
|------|--------|----------|
| 代码规范 | PEP 8、命名、格式 | 变量命名不规范 |
| 潜在Bug | 逻辑错误、边界条件 | 除零未处理 |
| 性能问题 | 算法复杂度、资源使用 | O(n²)可优化为O(n) |
| 安全隐患 | 注入、敏感信息暴露 | SQL注入风险 |
| 可维护性 | 代码结构、注释 | 缺少docstring |

#### JSON解析容错

```python
def _parse_response(self, response: str) -> dict:
    # 尝试直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # 尝试从代码块中提取
    json_pattern = r"```json\s*\n(.*?)\n```"
    matches = re.findall(json_pattern, response, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass

    # 返回默认结果
    return {
        "passed": True,
        "issues": [],
        "score": 70,
        "summary": "无法解析审查结果",
        "raw_response": response,
    }
```

### 4.3 DebuggerAgent (`backend/agents/debugger.py`)

#### Prompt设计

```python
SYSTEM_PROMPT = """你是一个专业的Python调试专家。

根据提供的代码和问题列表，修复代码中的问题。

要求：
1. 保持原有功能不变
2. 修复所有列出的问题
3. 添加必要的错误处理
4. 保持代码风格一致

直接输出修复后的代码，使用```python代码块包裹。"""
```

#### 问题格式化

```python
def process(self, input_data: dict, context: dict) -> dict:
    code = input_data.get("code", "")
    issues = input_data.get("issues", [])
    error_message = input_data.get("error_message", "")

    # 构建问题描述
    issues_text = "\n".join(
        [f"- [{i['severity']}] 行{i.get('line', '?')}: {i['message']}" for i in issues]
    )

    prompt = f"""请修复以下代码：

```python
{code}
```

问题列表：
{issues_text}

{f'错误信息：{error_message}' if error_message else ''}

请输出修复后的完整代码。"""
```

### 4.4 TestGeneratorAgent (`backend/agents/test_generator.py`)

#### 测试用例生成

```python
SYSTEM_PROMPT = """你是一个专业的Python测试工程师。

请为给定的代码生成全面的测试用例，包括：
1. 正常情况测试
2. 边界情况测试
3. 异常情况测试

使用pytest框架，直接输出测试代码，使用```python代码块包裹。"""
```

**测试覆盖类型**：

| 类型 | 描述 | 示例 |
|------|------|------|
| 正常情况 | 验证核心功能 | `test_add_normal()` |
| 边界情况 | 极端输入值 | `test_add_empty_list()` |
| 异常情况 | 错误处理 | `test_add_invalid_input()` |

---

## 五、LLM抽象层

### 5.1 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                     LLMFactory                          │
│                    (工厂模式)                            │
├─────────────────────────────────────────────────────────┤
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐        │
│   │ BaseLLM   │   │ BaseLLM   │   │ BaseLLM   │        │
│   │ (OpenAI)  │   │ (Claude)  │   │ (Others)  │        │
│   └───────────┘   └───────────┘   └───────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 5.2 抽象基类 (`backend/llm/base.py`)

```python
class BaseLLM(ABC):
    """LLM抽象基类"""

    def __init__(self, model: str, token_manager: Optional[Any] = None, **kwargs: Any) -> None:
        self.model = model
        self.config = kwargs
        self.token_manager = token_manager

    @abstractmethod
    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """调用模型"""
        pass

    @abstractmethod
    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """流式调用"""
        pass

    def _track_tokens(self, text: str) -> None:
        """追踪Token使用量"""
        if self.token_manager is not None:
            estimated_tokens = self.token_manager.estimate_tokens(text)
            self.token_manager.track_usage(estimated_tokens)


class LLMFactory:
    """LLM工厂类"""

    @staticmethod
    def create(provider: str, model: str, token_manager: Optional[Any] = None, **kwargs: Any) -> BaseLLM:
        if provider == "openai":
            from .openai_llm import OpenAILLM
            return OpenAILLM(model, token_manager=token_manager, **kwargs)
        elif provider == "claude":
            from .claude_llm import ClaudeLLM
            return ClaudeLLM(model, token_manager=token_manager, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

### 5.3 OpenAI实现 (`backend/llm/openai_llm.py`)

```python
class OpenAILLM(BaseLLM):
    """OpenAI LLM实现 - 支持OpenAI兼容API（如DeepSeek）"""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        token_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(model, token_manager=token_manager, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        content = response.choices[0].message.content or ""

        # 追踪Token使用量
        self._track_tokens(content)

        # 如果API返回了token使用量，使用实际值
        if hasattr(response, 'usage') and response.usage and self.token_manager:
            actual_tokens = response.usage.total_tokens
            self.token_manager.current_usage -= self.token_manager.estimate_tokens(content)
            self.token_manager.track_usage(actual_tokens)

        return content

    def stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        full_content = ""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield content

        # 流式结束后追踪总Token
        self._track_tokens(full_content)
```

**支持的API**：
- OpenAI (gpt-4, gpt-4o-mini)
- DeepSeek (deepseek-chat)
- 其他OpenAI兼容API

**Token追踪特性**：
- 自动追踪每次调用的token使用量
- 优先使用API返回的实际token数
- 流式调用结束后统计总token

### 5.4 Claude实现 (`backend/llm/claude_llm.py`)

```python
class ClaudeLLM(BaseLLM):
    """Claude LLM实现"""

    def invoke(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        # 转换消息格式
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_message if system_message else None,
            messages=claude_messages,
        )

        return response.content[0].text
```

**消息格式转换**：
- OpenAI格式: `{"role": "system", "content": "..."}`
- Claude格式: `system` 参数 + `messages` 列表

### 5.5 Token管理器 (`backend/llm/token_manager.py`)

```python
class TokenManager:
    """Token管理器 - 管理和追踪Token使用量"""

    def __init__(self, max_tokens: int = 128000) -> None:
        self.max_tokens = max_tokens
        self.current_usage = 0

    def estimate_tokens(self, text: str) -> int:
        """估算Token数（简单估算：约3字符/token）"""
        return max(1, len(text) // 3)

    def should_compress(self, context: str) -> bool:
        """判断是否需要压缩上下文（超过80%阈值）"""
        return self.estimate_tokens(context) > self.max_tokens * 0.8

    def track_usage(self, usage: int) -> None:
        """追踪Token使用量"""
        self.current_usage += usage

    def get_remaining(self) -> int:
        """获取剩余可用Token数"""
        return max(0, self.max_tokens - self.current_usage)
```

---

## 六、工具层设计

### 6.1 AST解析器 (`backend/tools/ast_parser.py`)

```python
class ASTParser:
    """Python AST解析器"""

    def parse(self, code: str) -> ast.Module:
        """解析代码为AST"""
        return ast.parse(code)

    def extract_functions(self, tree: ast.Module) -> list[ast.FunctionDef]:
        """提取所有函数定义"""
        return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def extract_classes(self, tree: ast.Module) -> list[ast.ClassDef]:
        """提取所有类定义"""
        return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def extract_imports(self, tree: ast.Module) -> list[ast.stmt]:
        """提取所有导入"""
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

    def get_function_signature(self, func: ast.FunctionDef) -> dict[str, Any]:
        """获取函数签名"""
        return {
            "name": func.name,
            "args": [arg.arg for arg in func.args.args],
            "defaults": [ast.unparse(d) if d else None for d in func.args.defaults],
            "returns": ast.unparse(func.returns) if func.returns else None,
            "docstring": ast.get_docstring(func),
        }

    def get_class_info(self, cls: ast.ClassDef) -> dict[str, Any]:
        """获取类信息"""
        methods = [node.name for node in cls.body if isinstance(node, ast.FunctionDef)]
        return {
            "name": cls.name,
            "bases": [ast.unparse(base) for base in cls.bases],
            "methods": methods,
            "docstring": ast.get_docstring(cls),
        }
```

**应用场景**：
- 代码结构分析
- 函数签名提取
- 依赖关系分析
- 代码重构建议

### 6.2 沙箱执行器 (`backend/tools/executor.py`)

> ⚠️ **代码已过期，以现行实现为准（2026-09-10 标注）**。下方是 2026-04 的版本，现行实现有三处收紧：
> 1. `execute()` 签名变为 `execute(code, validate=True, test_safe=False)`，默认先过 `CodeValidator` 静态校验，不通过直接返回 `{"success": False, "error": "代码未通过安全验证", "security_issues": [...]}`；
> 2. 临时文件改用 `tempfile.TemporaryDirectory()` + 固定名 `sandbox.py`，并传 `cwd=tmpdir` 限制工作目录（旧版用 `NamedTemporaryFile` 且不限定 cwd，脚本可读到进程当前目录）；
> 3. `_get_safe_env()` **不再传 `HOME`**；Windows 下额外传 `TEMP`/`TMP`/`SystemRoot`，且用固定路径 `C:\Windows\Temp` 以避免泄露宿主用户名。
>
> 另：`__init__` 现为 `__init__(timeout: int = 30, max_memory_mb: int = 256)`。

```python
class CodeExecutor:
    """代码执行器 - 在沙箱环境中安全执行Python代码"""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def execute(self, code: str) -> dict[str, Any]:
        """执行代码"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._get_safe_env(),
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Execution timeout after {self.timeout} seconds",
            }

        finally:
            os.unlink(temp_path)

    def _get_safe_env(self) -> dict[str, str]:
        """获取安全的环境变量"""
        safe_path = "/usr/bin:/bin" if sys.platform != "win32" else os.path.dirname(sys.executable)

        return {
            "PATH": safe_path,
            "PYTHONPATH": "",  # 禁止导入用户自定义模块
            "PYTHONIOENCODING": "utf-8",
            "HOME": os.environ.get("HOME", ""),
            "TEMP": os.environ.get("TEMP", "/tmp"),
        }
```

**安全措施**：

| 措施 | 实现 | 目的 |
|------|------|------|
| 超时控制 | `subprocess.run(timeout=30)` | 防止无限循环 |
| 临时文件 | `NamedTemporaryFile` + `finally: os.unlink()` | 清理痕迹 |
| 输出捕获 | `capture_output=True` | 隔离输出 |
| 环境隔离 | 最小权限环境变量 | 限制访问 |
| 路径限制 | 仅系统路径 | 禁止危险操作 |

---

## 七、记忆系统 ⚠️ 已移除（2026-09-10）

> 本章描述的 `core/memory.py`、`core/vector_memory.py` 实现后**从未被主流程调用**（全仓零调用点），已于 2026-09-10 连同其对应用例一并删除，依赖 `chromadb` 也已从 requirements 移除。以下仅作历史记录。
>
> 教训：如果今后重做记忆能力，必须把**写入路径**先接到主流程上再谈检索，否则会重演「接了但永远查空库」。

### 7.1 多层记忆架构

```
┌─────────────────────────────────────────────────────────┐
│                      Memory System                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐       │
│  │   ShortTermMemory   │  │   LongTermMemory    │       │
│  │   ───────────────   │  │   ───────────────   │       │
│  │   - max_items: 100  │  │   - dict结构        │       │
│  │   - FIFO淘汰策略    │  │   - 持久化存储      │       │
│  │   - 时间戳追踪      │  │   - 时间戳追踪      │       │
│  └─────────────────────┘  └─────────────────────┘       │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              VectorMemory (ChromaDB)             │    │
│  │              ─────────────────────               │    │
│  │              - 语义相似度检索                     │    │
│  │              - 持久化到磁盘                       │    │
│  │              - 元数据过滤                         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.2 短期记忆 (`backend/core/memory.py`) ⚠️ 文件已删除，以下代码不可运行

```python
class ShortTermMemory:
    """短期记忆 - 会话级别，有容量限制"""

    def __init__(self, max_items: int = 100) -> None:
        self.items: list[dict[str, Any]] = []
        self.max_items = max_items

    def add(self, key: str, value: Any) -> None:
        """添加记忆"""
        self.items.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })

        # 超过容量时移除最早的
        if len(self.items) > self.max_items:
            self.items.pop(0)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """搜索记忆 - 简单实现：返回最近的k条"""
        return self.items[-k:]
```

### 7.3 向量记忆 (`backend/core/vector_memory.py`) ⚠️ 文件已删除，以下代码不可运行

```python
class VectorMemory:
    """基于ChromaDB的向量记忆系统"""

    def __init__(
        self,
        persist_dir: str = "./memory/chroma",
        collection_name: str = "code_memory",
    ) -> None:
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=persist_dir)

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Code generation history"},
        )

    def add(
        self,
        requirement: str,
        code: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """添加代码记忆"""
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._doc_counter}"
        document = f"需求: {requirement}\n\n代码:\n{code}"

        self.collection.add(
            documents=[document],
            metadatas=[{
                "requirement": requirement,
                "code_length": len(code),
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }],
            ids=[doc_id],
        )
        return doc_id

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """相似代码检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
        return self._format_results(results)
```

### 7.4 混合记忆 ⚠️ `HybridMemory` 随记忆系统一并删除，以下代码不可运行

```python
class HybridMemory:
    """混合记忆系统 - 整合短期记忆和向量记忆"""

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """搜索记忆"""
        results = []

        # 从短期记忆搜索
        results.extend(self.short_term.search(query, k))

        # 从向量记忆搜索
        if self.vector_memory:
            results.extend(self.vector_memory.search(query, n_results=k))

        return results[:k]
```

---

## 八、错误处理与日志

### 8.1 错误码体系 (`backend/core/errors.py`)

```python
class ErrorCode(Enum):
    """错误码枚举 - 14种错误码"""

    # LLM相关错误 (4种)
    LLM_ERROR = "LLM_ERROR"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_CONNECTION_ERROR = "LLM_CONNECTION_ERROR"
    LLM_AUTH_ERROR = "LLM_AUTH_ERROR"

    # 验证相关错误 (3种)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"

    # 执行相关错误 (3种)
    EXECUTION_ERROR = "EXECUTION_ERROR"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_SECURITY = "EXECUTION_SECURITY"

    # 状态相关错误 (2种)
    STATE_ERROR = "STATE_ERROR"
    STATE_TRANSITION_FAILED = "STATE_TRANSITION_FAILED"

    # Agent相关错误 (2种)
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_ERROR = "AGENT_ERROR"

    # 通用错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
```

### 8.2 统一错误结果

```python
@dataclass
class ErrorResult:
    """统一错误结果格式"""
    success: bool = False
    error_code: str = ""
    error_message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Optional[dict[str, Any]] = None) -> "ErrorResult":
        """创建成功结果"""
        return cls(success=True, details=data or {})

    @classmethod
    def error(
        cls,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> "ErrorResult":
        """创建错误结果"""
        return cls(
            success=False,
            error_code=code.value,
            error_message=message,
            details=details or {},
        )
```

### 8.3 异常类层次

```
CodeCraftError (基类)
    ├── LLMError (LLM相关异常)
    ├── ValidationError (验证相关异常)
    ├── ExecutionError (执行相关异常)
    └── StateError (状态相关异常)
```

### 8.4 错误处理装饰器

```python
def handle_errors(default_return: Optional[dict[str, Any]] = None) -> Callable[[F], F]:
    """错误处理装饰器"""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_result = ErrorResult.error(
                    code=ErrorCode.UNKNOWN_ERROR,
                    message=str(e),
                    details={"exception_type": type(e).__name__},
                )
                if default_return is not None:
                    return {**default_return, **error_result.to_dict()}
                return error_result.to_dict()

        return wrapper

    return decorator
```

### 8.5 敏感信息脱敏 (`backend/core/logger.py`)

```python
# 敏感信息脱敏模式
SENSITIVE_PATTERNS = [
    (r"(api[_-]?key\s*[=:]\s*['\"]?)[^'\"\s]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(token\s*[=:]\s*['\"]?)[^'\"\s]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(password\s*[=:]\s*['\"]?)[^'\"\s]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(secret\s*[=:]\s*['\"]?)[^'\"\s]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(sk-[a-zA-Z0-9]{20,})", r"sk-***REDACTED***"),  # OpenAI Key
]


def sanitize_message(message: str) -> str:
    """脱敏敏感信息"""
    sanitized = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized


class SensitiveInfoFilter(logging.Filter):
    """敏感信息过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg:
            record.msg = sanitize_message(str(record.msg))
        if record.args:
            record.args = tuple(
                sanitize_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True
```

**覆盖场景**：
- API Key（各种命名风格：api_key, apiKey, API-KEY）
- Token
- Password
- Secret
- OpenAI Key 特征码（sk-xxx）

---

## 九、前端实现

### 9.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Streamlit | >=1.28.0 | Web框架 |
| pyperclip | >=1.8.0 | 剪贴板操作 |

### 9.2 页面结构

```
frontend/
├── app.py                 # 主页
├── components/
│   ├── agent_status.py    # Agent状态可视化
│   ├── code_display.py    # 代码展示组件
│   └── streaming_display.py # 流式输出组件
├── pages/
│   ├── chat.py            # 代码生成页面
│   ├── history.py         # 历史记录页面
│   └── settings.py        # 设置页面
└── utils/
    └── session.py         # 会话状态管理
```

### 9.3 会话状态管理 (`frontend/utils/session.py`)

```python
class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    FIXING = "fixing"
    TESTING = "testing"  # 新增：测试生成阶段
    DONE = "done"


@dataclass
class GenerationResult:
    """生成结果"""
    requirement: str
    code: str
    review_score: int
    issues: list[str]
    agent_state: AgentState
    error: Optional[str] = None


class SessionManager:
    """会话状态管理器"""

    @staticmethod
    def init_session() -> None:
        """初始化会话状态"""
        if "agent_state" not in st.session_state:
            st.session_state.agent_state = AgentState.IDLE
        if "generation_result" not in st.session_state:
            st.session_state.generation_result = None
        if "history" not in st.session_state:
            st.session_state.history = []
        if "config" not in st.session_state:
            st.session_state.config = ConfigManager.load()


class ConfigManager:
    """配置管理器"""
    CONFIG_DIR = Path.home() / ".codecraft"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    @classmethod
    def load(cls) -> dict:
        """加载配置"""
        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "api_key": "",
            "api_type": "deepseek",
            "model": "deepseek-chat",
            "fast_mode": False,
        }
```

### 9.4 Agent状态可视化 (`frontend/components/agent_status.py`)

```python
# 状态配置
STATUS_CONFIG = {
    AgentState.IDLE: {"label": "等待输入", "color": "gray", "icon": "⏸️"},
    AgentState.ANALYZING: {"label": "分析需求", "color": "blue", "icon": "🔍"},
    AgentState.GENERATING: {"label": "生成代码", "color": "blue", "icon": "✨"},
    AgentState.REVIEWING: {"label": "代码审查", "color": "orange", "icon": "📋"},
    AgentState.FIXING: {"label": "修复优化", "color": "orange", "icon": "🔧"},
    AgentState.TESTING: {"label": "生成测试", "color": "purple", "icon": "🧪"},
    AgentState.DONE: {"label": "完成", "color": "green", "icon": "✅"},
}

def render_agent_status(current_state: AgentState) -> None:
    """渲染Agent状态流程图"""
    current_index = STATUS_ORDER.index(current_state)
    cols = st.columns(len(STATUS_ORDER))

    for i, state in enumerate(STATUS_ORDER):
        config = STATUS_CONFIG[state]
        is_current = state == current_state
        is_passed = i < current_index

        with cols[i]:
            if is_current:
                # 当前状态：高亮显示
                st.markdown(f"""
                    <div style="text-align: center; padding: 10px;
                                background-color: {config['color']}20;
                                border: 2px solid {config['color']};
                                border-radius: 8px;">
                        <div style="font-size: 24px;">{config['icon']}</div>
                        <div style="font-size: 12px; font-weight: bold; color: {config['color']};">
                            {config['label']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
```

### 9.5 流式生成实现 (`frontend/pages/chat.py`)

```python
# 流式显示代码
code_placeholder = st.empty()
full_code = ""

for chunk in llm.stream(messages):
    full_code += chunk
    code_placeholder.code(full_code, language="python")

# 提取代码块
pattern = r"```python\s*\n(.*?)\n```"
matches = re.findall(pattern, full_code, re.DOTALL)
code = matches[0] if matches else full_code
```

---

## 十、CLI实现

### 10.1 入口设计 (`cli/main.py`)

```python
app = typer.Typer(
    name="codecraft",
    help="CodeCraft Agent - Multi-Agent Python code generation assistant",
)
console = Console()

# 全局 TokenManager 实例
_token_manager: TokenManager | None = None


def get_token_manager() -> TokenManager:
    """获取全局 TokenManager 实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(max_tokens=128000)
    return _token_manager


def get_orchestrator(fast: bool = False) -> Orchestrator:
    """获取Orchestrator实例"""
    # 支持 DeepSeek 或 OpenAI
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

    # 判断使用哪个API
    if os.getenv("DEEPSEEK_API_KEY"):
        base_url = "https://api.deepseek.com/v1"
        model = "deepseek-chat"
    else:
        base_url = None
        model = "gpt-4o-mini"

    # 创建LLM（集成 TokenManager）
    token_manager = get_token_manager()
    llm = LLMFactory.create("openai", model, api_key=api_key, base_url=base_url, token_manager=token_manager)

    # 创建工具
    tools: list[Any] = [ASTParser(), CodeExecutor(timeout=30)]

    # ⚠️ 2026-04 快照。当前该装配逻辑已收敛到 backend/core/factory.py 的
    #    create_orchestrator(api_key, model, base_url, fast, token_manager)，
    #    CLI 与 Streamlit 两处入口共用，不再各自重复组装；
    #    记忆系统与 memory= 注入已随 2026-09-10 清理移除。
    generator = CodeGeneratorAgent(llm=llm, tools=tools)
    agents: dict[str, Any] = {"generator": generator}

    if not fast:
        reviewer = CodeReviewerAgent(llm=llm, tools=tools)
        debugger = DebuggerAgent(llm=llm, tools=tools)
        test_generator = TestGeneratorAgent(llm=llm, tools=tools)
        agents["reviewer"] = reviewer
        agents["debugger"] = debugger
        agents["test_generator"] = test_generator

    return Orchestrator(agents=agents, context=SharedContext())


@app.command()
def generate(requirement: str, fast: bool = False) -> None:
    """生成代码"""
    console.print(Panel(f"[bold blue]正在生成代码...[/bold blue]\n{requirement}"))

    orchestrator = get_orchestrator(fast=fast)

    if fast:
        console.print("[dim]快速模式：跳过代码审查[/dim]")

    result = orchestrator.process_request(requirement)

    if "code" in result:
        # 显示审查结果
        if not fast and "review_score" in result:
            score = result["review_score"]
            if score >= 90:
                console.print(f"\n[bold green]✓ 代码审查通过[/bold green] (评分: {score})")
            else:
                console.print(f"\n[bold yellow]⚠ 代码已自动修复优化[/bold yellow] (评分: {score} → 优化后)")

        console.print("\n[bold green]生成的代码:[/bold green]\n")
        console.print(Markdown(f"```python\n{result['code']}\n```"))


@app.command()
def chat(fast: bool = False) -> None:
    """交互模式"""
    console.print(Panel("[bold green]CodeCraft Agent 交互模式[/bold green]"))
    if fast:
        console.print("[dim]快速模式：跳过代码审查[/dim]")
    else:
        console.print("多Agent协作: 生成 → 审查 → 修复优化 → 测试")
    console.print("输入需求生成代码，输入 'exit' 退出\n")

    orchestrator = get_orchestrator(fast=fast)
    token_manager = get_token_manager()

    while True:
        user_input = console.input("[bold blue]You:[/bold blue] ")
        if user_input.lower() == "exit":
            break

        result = orchestrator.process_request(user_input)
        # ... 显示结果


@app.command()
def version() -> None:
    """显示版本信息"""
    from backend import __version__
    console.print(f"CodeCraft Agent v{__version__}")
```

### 10.2 集成特性

**CLI 已集成的组件**：

| 组件 | 集成方式 |
|------|----------|
| TokenManager | 全局单例，传入 LLM |
| ASTParser | 注入 Agent tools |
| CodeExecutor | 注入 Agent tools |
| ~~Memory~~ | ⚠️ 已移除（2026-09-10）；装配统一走 `create_orchestrator()` |
| TestGeneratorAgent | 非快速模式下创建 |

**完整工作流**：
```
用户输入 → Generator → Reviewer → [通过] → TestGenerator → Done
                              ↓
                         [不通过] → Debugger → 重新审查
```

---

## 十一、测试体系

### 11.1 测试文件清单

| 测试文件 | 测试目标 | 测试数量 |
|----------|----------|----------|
| test_state.py | 状态机 | 9个 |
| ~~test_protocol.py~~ | ⚠️ 已随 protocol.py 删除 | - |
| test_agent.py | Agent基类 | 4个 |
| test_context.py | 共享上下文 | 6个 |
| test_llm.py | LLM抽象层 | 5个 |
| test_code_generator.py | 代码生成Agent | 4个 |
| test_code_reviewer.py | 代码审查Agent | 4个 |
| test_debugger.py | 调试Agent | 4个 |
| ~~test_memory.py~~ | ⚠️ 2026-09-10 删除 | - |
| test_orchestrator.py | 协调器 | 4个 |
| test_ast_parser.py | AST解析器 | 4个 |
| test_executor.py | 执行器 | 4个 |
| test_test_generator.py | 测试生成器 | 3个 |
| test_token_manager.py | Token管理器 | 6个 |
| ~~test_vector_memory.py~~ | ⚠️ 2026-09-10 删除 | - |
| test_integration.py | 集成测试 | 4个 |

**总计（2026-04 快照）**: 80个测试用例。

**当前**: 116 个测试全部通过（`pytest -q`，约 4 秒）。相对快照的 80 个，中间经历了两轮变动：2026-06-28 删 5 个协议用例、2026-09-10 删 17 个记忆用例（`test_memory.py` 4 个 + `test_vector_memory.py` 13 个），期间 Phase 7/8 新增了 `test_errors.py`、`test_code_utils.py`、安全攻击向量用例，2026-09-10 又新增 `test_factory.py`（3 个），2026-09-11 新增 2 个沙箱编码回归测试（116 → 118）。

### 11.2 测试示例

#### 状态机测试

```python
class TestStateMachine:
    def test_valid_transition(self):
        """测试有效状态转换"""
        sm = StateMachine()
        assert sm.transition(TaskState.ANALYZING) is True
        assert sm.current_state == TaskState.ANALYZING

    def test_invalid_transition(self):
        """测试无效状态转换"""
        sm = StateMachine()
        assert sm.transition(TaskState.DONE) is False
        assert sm.current_state == TaskState.PENDING

    def test_full_workflow(self):
        """测试完整工作流"""
        sm = StateMachine()
        sm.transition(TaskState.ANALYZING)
        sm.transition(TaskState.GENERATING)
        sm.transition(TaskState.REVIEWING)
        sm.transition(TaskState.TESTING)
        sm.transition(TaskState.DONE)
        assert sm.current_state == TaskState.DONE
```

#### 反馈闭环测试

```python
def test_feedback_loop(self):
    """测试反馈闭环"""
    generator = Mock()
    generator.process.return_value = {"code": "def test(): pass"}

    reviewer = Mock()
    # 第一次审查不通过，第二次通过
    reviewer.process.side_effect = [
        {"passed": False, "issues": [{"severity": "high", "message": "test"}], "score": 60},
        {"passed": True, "issues": [], "score": 90},
    ]

    debugger = Mock()
    debugger.process.return_value = {"fixed_code": "def test():\n    return 1"}

    agents = {"generator": generator, "reviewer": reviewer, "debugger": debugger}
    orch = Orchestrator(agents=agents, context=SharedContext())

    result = orch.process_request("实现一个测试函数")

    # 验证审查被调用了两次
    assert reviewer.process.call_count == 2
    # 验证调试器被调用了一次
    assert debugger.process.call_count == 1
```

#### 集成测试

```python
@patch("backend.llm.openai_llm.OpenAI")
def test_full_multi_agent_workflow(self, mock_openai_class):
    """测试完整多Agent工作流"""
    mock_client = Mock()

    # 模拟多次调用返回不同结果
    mock_client.chat.completions.create.side_effect = [
        generate_response,    # 第一次：生成代码
        review_response_1,    # 第二次：审查（不通过）
        fix_response,         # 第三次：修复代码
        review_response_2,    # 第四次：审查（通过）
    ]

    # 创建完整的Agent系统
    llm = LLMFactory.create("openai", "gpt-4o-mini", api_key="test-key")
    generator = CodeGeneratorAgent(llm=llm, tools=[])
    reviewer = CodeReviewerAgent(llm=llm, tools=[])
    debugger = DebuggerAgent(llm=llm, tools=[])

    orchestrator = Orchestrator(
        agents={"generator": generator, "reviewer": reviewer, "debugger": debugger},
        context=SharedContext(),
    )

    result = orchestrator.process_request("实现一个除法函数")

    assert "code" in result
    assert orchestrator.state_machine.current_state == TaskState.DONE
```

---

## 十二、技术栈分析

### 12.1 核心依赖

| 类别 | 技术 | 版本要求 | 用途 |
|------|------|----------|------|
| **编程语言** | Python | >=3.10 | 类型注解、模式匹配等新特性 |
| ~~LLM框架~~ | ⚠️ ~~LangChain~~ | - | 已移除：代码中从未 import，编排/状态机/重试均自研 |
| ~~LLM适配~~ | ⚠️ ~~langchain-openai / langchain-anthropic~~ | - | 已移除：直接使用官方 SDK |
| **LLM API** | OpenAI | >=1.0.0 | OpenAI官方SDK |
| **LLM API** | Anthropic | >=0.25.0 | Claude官方SDK |
| **CLI框架** | Typer | >=0.12.0 | 命令行界面 |
| **终端美化** | Rich | >=13.0.0 | 富文本终端输出 |
| ~~向量存储~~ | ⚠️ ~~ChromaDB~~ | - | 已移除：随记忆系统一并删除 |
| **数据验证** | Pydantic | >=2.0.0 | 数据模型验证 |
| **Web框架** | Streamlit | >=1.28.0 | Web UI界面 |
| **剪贴板** | pyperclip | >=1.8.0 | 代码复制功能 |

### 12.2 开发工具

| 类别 | 技术 | 版本要求 | 用途 |
|------|------|----------|------|
| **测试框架** | pytest | >=8.0.0 | 单元测试 |
| **异步测试** | pytest-asyncio | >=0.23.0 | 异步测试支持 |
| **覆盖率** | pytest-cov | >=4.0.0 | 测试覆盖率报告 |
| **代码检查** | ruff | >=0.3.0 | Linting |
| **类型检查** | mypy | >=1.8.0 | 静态类型检查 |
| **构建工具** | hatchling | - | 包构建 |

### 12.3 项目配置 (`pyproject.toml`)

```toml
[project]
name = "codecraft-agent"
version = "0.2.0"
requires-python = ">=3.10"

[project.scripts]
codecraft = "cli.main:app"  # pip install后可直接运行

[tool.mypy]
strict = true  # 严格类型检查

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py310"
```

---

## 十三、设计模式应用

### 13.1 工厂模式

**应用场景**: LLM Provider创建

```python
class LLMFactory:
    @staticmethod
    def create(provider: str, model: str, **kwargs: Any) -> BaseLLM:
        if provider == "openai":
            return OpenAILLM(model, **kwargs)
        elif provider == "claude":
            return ClaudeLLM(model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

**好处**:
- 开闭原则：新增Provider只需添加elif分支
- 解耦：调用方无需知道具体实现类
- 统一接口：所有LLM实现相同接口

### 13.2 状态机模式

**应用场景**: 任务状态管理

```python
class StateMachine:
    TRANSITIONS = {
        TaskState.PENDING: [TaskState.ANALYZING],
        TaskState.ANALYZING: [TaskState.GENERATING, TaskState.REVIEWING],
        # ...
    }

    def transition(self, next_state: TaskState) -> bool:
        if self.can_transition_to(next_state):
            self.history.append(self.current_state)
            self.current_state = next_state
            return True
        return False
```

**好处**:
- 状态可追踪
- 防止非法转换
- 便于调试和监控
- 支持断点恢复

### 13.3 策略模式

**应用场景**: Agent行为定义

```python
class BaseAgent(ABC):
    @abstractmethod
    def process(self, input_data: dict, context: dict) -> dict:
        pass

class CodeGeneratorAgent(BaseAgent):
    def process(self, input_data: dict, context: dict) -> dict:
        # 生成策略

class CodeReviewerAgent(BaseAgent):
    def process(self, input_data: dict, context: dict) -> dict:
        # 审查策略
```

**好处**:
- 每个Agent专注一个任务
- 可独立测试和优化
- 易于扩展新Agent

### 13.4 观察者模式 ⚠️ 已移除

> 该模式依赖的 `protocol.py`（AgentMessage/MessageType）已于 2026-06-28 删除，Agent 间现在通过 Orchestrator 直接调用传递结果。以下仅作历史记录。

**应用场景**: Agent间消息通信

```python
@dataclass
class AgentMessage:
    sender: str
    receiver: str
    msg_type: MessageType
    payload: dict[str, Any]
    correlation_id: str
    timestamp: float
```

**好处**:
- 解耦Agent间通信
- 支持消息追踪
- 便于日志和调试

### 13.5 模板方法模式

**应用场景**: Agent处理流程

```python
class BaseAgent(ABC):
    def process(self, input_data: dict, context: dict) -> dict:
        # 模板方法：定义处理骨架
        observation = self.observe(context)
        thought = self.think(observation)
        return self.act(thought)

    @abstractmethod
    def act(self, thought: str) -> dict:
        pass
```

---

## 十四、项目亮点

### 14.1 架构亮点

| 亮点 | 描述 | 技术实现 |
|------|------|----------|
| **多Agent协作** | Generator → Reviewer → Debugger → TestGenerator | Orchestrator模式 |
| **反馈闭环** | 审查不通过自动修复，最多3次迭代 | `_handle_feedback_loop()` |
| **状态机管理** | 8状态有限状态机，确保任务流转可控 | `StateMachine`类 |
| **多模型支持** | OpenAI / Claude / DeepSeek 可切换 | `LLMFactory`工厂模式 |
| ~~向量记忆~~ | ⚠️ 已移除（2026-09-10） | - |
| **高测试覆盖** | 118个测试用例，全部通过 | pytest + pytest-cov |
| **完整集成** | CLI 与 Web 共用同一装配入口 | `create_orchestrator()`（tools/token_manager 注入） |

### 14.2 技术创新点

1. ~~**ReAct推理模式**~~: ⚠️ 该骨架方法（observe/think/act）已移除，当前是「基类定义抽象 process() + 各 Agent 实现」的策略模式
2. **线程安全上下文**: 使用RLock保护共享数据
3. **敏感信息脱敏**: 日志系统自动过滤API Key等敏感信息
4. **沙箱执行**: 代码执行器隔离用户代码，限制权限
5. **流式输出**: Web界面支持代码逐步生成显示
6. **多维度代码审查**: 规范/Bug/性能/安全/可维护性五维评估
7. **Token追踪**: LLM层集成TokenManager，实时追踪使用量
8. **自动测试生成**: 审查通过后自动生成pytest测试用例

### 14.3 与同类项目对比

| 特性 | CodeCraft Agent | AutoGPT | BabyAGI |
|------|-----------------|---------|---------|
| 架构模式 | Orchestrator | Agent驱动 | 任务队列 |
| 状态管理 | 8状态FSM | 无 | 简单状态 |
| 反馈闭环 | ✅ 多轮审查修复 | ❌ | ❌ |
| 多模型支持 | OpenAI/Claude/DeepSeek | 仅OpenAI | 仅OpenAI |
| 测试覆盖 | 118个测试全部通过 | 低 | 低 |
| Web UI | Streamlit | 无 | 无 |
| 向量记忆 | 无（曾实现后移除） | Pinecone | ChromaDB |
| Token追踪 | ✅ 集成 | ❌ | ❌ |
| 自动测试生成 | ✅ TestGeneratorAgent | ❌ | ❌ |

---

## 十五、面试展示价值

### 15.1 可展示的技术能力

#### Python高级编程
- 类型注解（Type Hints）
- 装饰器模式
- 数据类（dataclass）
- 枚举类（Enum）
- 上下文管理器

#### 设计模式应用
- 工厂模式：LLM Provider创建
- 状态机模式：任务状态管理
- 策略模式：Agent行为定义
- 模板方法：`BaseAgent` 定义抽象 `process()`，各 Agent 实现

#### LLM应用开发
- Prompt Engineering
- 官方 SDK 直用（不引编排框架，自己实现编排与重试）
- 多模型适配
- Token管理优化

#### Web开发
- Streamlit快速原型
- 响应式UI设计
- 会话状态管理

#### 测试驱动开发
- Pytest单元测试
- 集成测试
- Mock/Fixture应用
- 覆盖率报告

### 15.2 面试问答要点

#### Q: 为什么用多Agent而不是单Agent？

**回答要点**:
1. **职责分离**：每个Agent专注一个任务，Prompt更精准
2. **便于测试**：可以单独测试每个Agent的行为
3. **可维护性**：修改一个Agent不影响其他Agent
4. **可扩展性**：新增功能只需添加新Agent

#### Q: 状态机有什么好处？

**回答要点**:
1. **状态可追踪**：任何时候都知道任务处于什么阶段
2. **防止非法转换**：比如不能从PENDING直接跳到DONE
3. **便于调试**：状态历史记录可以帮助定位问题
4. **支持断点恢复**

#### Q: 如何处理LLM的不稳定性？

**回答要点**:
1. **多轮审查机制**：Reviewer检查Generator的输出
2. **结构化输出要求**：要求LLM返回JSON格式
3. **错误重试策略**：失败后自动重试，最多3次
4. **人工反馈闭环**：用户可以干预修复过程

### 15.3 简历写法建议

**简洁版**:
> 设计并实现多Agent协作的Python代码生成系统，采用Orchestrator模式协调4个专业Agent（生成、审查、调试、测试），通过8状态有限状态机管理任务流转，实现了代码生成-审查-修复-测试的自动化闭环。支持OpenAI/Claude多模型切换，118个测试全部通过。

**详细版**:
> **CodeCraft Agent** - 多Agent协作代码生成系统
> - 设计Orchestrator模式协调Generator、Reviewer、Debugger、TestGenerator四个Agent
> - 实现8状态有限状态机管理任务流转，确保状态转换可控
> - 构建反馈闭环机制，审查不通过自动修复，最多3次迭代
> - 设计LLM抽象层，支持OpenAI/Claude多模型切换
> - 实现AST解析器、沙箱执行器、Token管理器等工具链
> - 编写118个测试用例，backend 覆盖率约74%

---

## 十六、改进建议

### 16.1 短期改进（1-2周）

| 改进点 | 描述 | 优先级 |
|--------|------|--------|
| 流式输出优化 | CLI支持流式显示 | 高 |
| 错误重试策略 | LLM调用失败自动重试 | 高 |
| 配置文件支持 | 支持配置文件管理API Key | 中 |
| 日志级别配置 | 支持动态调整日志级别 | 低 |

### 16.2 中期改进（1-2月）

| 改进点 | 描述 | 优先级 |
|--------|------|--------|
| 更多LLM支持 | Gemini、Qwen等模型 | 高 |
| 代码补全功能 | 支持IDE插件 | 中 |
| 历史记录优化 | 支持搜索和导出 | 中 |
| 性能优化 | 缓存、并发处理 | 中 |

### 16.3 长期改进（3-6月）

| 改进点 | 描述 | 优先级 |
|--------|------|--------|
| 多语言支持 | 支持Java、JavaScript等 | 高 |
| 企业级部署 | Docker、K8s部署方案 | 中 |
| Agent市场 | 支持自定义Agent | 中 |
| 在线Demo | 公开演示环境 | 低 |

---

## 附录

### A. 快速使用指南

#### 安装
```bash
git clone <repository-url>
cd "CodeCraft Agent"
pip install -r requirements.txt
pip install -e ".[dev]"
```

#### 配置API Key
```bash
export DEEPSEEK_API_KEY="your-api-key"  # 推荐
# 或
export OPENAI_API_KEY="your-api-key"
```

#### 使用CLI
```bash
python -m cli.main generate "实现一个快速排序算法"
python -m cli.main generate "实现一个快速排序算法" --fast  # 快速模式
python -m cli.main chat  # 交互模式
```

#### 使用Web UI
```bash
streamlit run frontend/app.py --server.port 8501
# 访问 http://localhost:8501
```

### B. 项目文件统计

| 类型 | 数量 |
|------|------|
| Python文件 | ~~35个~~ → 当前 42 个（backend+cli+frontend） |
| 测试文件 | ~~16个~~ → 当前 18 个 |
| 文档文件 | 5个（快照口径） |
| 配置文件 | 3个（快照口径） |
| 总代码行数 | ~~~3000行~~ → 当前约 6500 行（含 tests） |

---

*报告生成时间: 2026-04-14*
*报告版本: 1.0*
