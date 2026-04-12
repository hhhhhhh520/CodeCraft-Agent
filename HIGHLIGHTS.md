# CodeCraft Agent 项目亮点

> 面试展示专用文档，汇总技术亮点和可展示的技术能力

---

## 技术亮点

### 1. 多Agent协作架构

**设计模式**: Orchestrator模式，集中式协调

```
用户请求 → Orchestrator → 状态机 → Agent调度 → 结果汇总
```

**核心组件**:
- **Orchestrator**: 任务分析、分发、协调
- **StateMachine**: 8状态有限状态机，确保任务流转可控
- **SharedContext**: Agent间共享上下文，支持状态传递

**Agent通信协议**:
```python
class AgentMessage:
    sender: str          # 发送者
    receiver: str        # 接收者
    message_type: MessageType  # TASK_ASSIGN / RESULT_RETURN / FEEDBACK
    content: dict        # 消息内容
    timestamp: datetime  # 时间戳
```

**为什么这样设计**:
- 职责分离，每个Agent专注一个任务
- 便于测试和维护
- 可独立优化每个Agent的Prompt
- 体现模块化设计思想

---

### 2. 反馈闭环机制

**流程设计**:
```
Generator → Reviewer → [通过] → Done
                ↓ [不通过]
            Debugger → Reviewer (重审)
```

**核心实现** (`orchestrator.py:188-264`):
```python
def _handle_feedback_loop(self, result: dict, max_iterations: int = 3) -> dict:
    iteration = 0
    while iteration < max_iterations:
        review_result = self.agents["reviewer"].process(...)
        if review_result.get("passed", True):
            return result  # 审查通过
        else:
            # 审查不通过，进入修复
            fix_result = self.agents["debugger"].process(...)
            result["code"] = fix_result.get("fixed_code")
            iteration += 1
    return result
```

**设计考量**:
- 最大迭代次数控制，避免无限循环
- 问题分级处理（规范/Bug/性能/安全）
- 修复后重新审查，确保质量

---

### 3. 状态机管理

**状态定义** (`state.py`):
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

**转换规则**:
```python
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
```

**好处**:
- 任务状态可追踪
- 防止非法状态转换
- 便于调试和监控
- 支持断点续传

---

### 4. LLM抽象层

**工厂模式创建Provider** (`llm/base.py`):
```python
class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    def stream(self, prompt: str) -> Iterator[str]: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

**实现类**:
- `OpenAILLM` - OpenAI GPT系列
- `ClaudeLLM` - Anthropic Claude系列

**统一接口，易于扩展**:
```python
def create_llm(provider: str, model: str) -> BaseLLM:
    if provider == "openai":
        return OpenAILLM(model)
    elif provider == "claude":
        return ClaudeLLM(model)
    # 新增Provider只需添加elif分支
```

---

### 5. 工具链设计

**AST解析器** (`tools/ast_parser.py`):
- 解析Python代码结构
- 提取函数、类、导入信息
- 支持代码重构建议

**沙箱执行器** (`tools/executor.py`):
- 安全执行用户代码
- 超时控制
- 输出捕获

**Token管理器** (`llm/token_manager.py`):
- 上下文窗口优化
- 自动截断超长文本
- Token计数

---

### 6. 记忆系统

**短期记忆** (`core/memory.py`):
```python
class ShortTermMemory:
    def __init__(self, max_items: int = 100):
        self.items: list[dict] = []
        self.max_items = max_items

    def add(self, item: dict) -> None: ...
    def get_recent(self, n: int = 10) -> list[dict]: ...
    def search(self, query: str) -> list[dict]: ...
```

**向量记忆** (计划中):
- ChromaDB语义检索
- 历史代码相似度匹配
- 上下文增强生成

---

## 代码质量指标

| 指标 | 数值 |
|------|------|
| 测试覆盖率 | 81% |
| 测试数量 | 67个 |
| 代码行数 | ~3000行 |
| 模块化程度 | 高 |
| 类型注解覆盖 | 100% |

---

## 可展示的技术能力

### Python高级编程
- 类型注解（Type Hints）
- 装饰器模式
- 异步编程（async/await）
- 上下文管理器
- 数据类（dataclass）

### 设计模式应用
- **工厂模式**: LLM Provider创建
- **状态机模式**: 任务状态管理
- **策略模式**: Agent行为定义
- **观察者模式**: 消息通知机制

### LLM应用开发
- Prompt Engineering
- LangChain框架应用
- 多模型适配
- Token管理优化

### Web开发
- Streamlit快速原型
- 响应式UI设计
- 会话状态管理

### 测试驱动开发
- Pytest单元测试
- 集成测试
- Mock/Fixture应用
- 覆盖率报告

---

## 项目难点与解决方案

### 难点1: Agent间协调的复杂性

**问题**: 多个Agent如何高效协作，避免状态混乱？

**解决方案**:
- 引入Orchestrator集中协调
- 状态机管理任务流转
- SharedContext共享上下文
- 消息队列解耦通信

### 难点2: 状态转换的边界条件

**问题**: 什么情况下可以转换状态？如何防止非法转换？

**解决方案**:
- 定义TRANSITIONS字典，明确合法转换
- `can_transition_to()` 方法检查合法性
- 状态历史记录，支持回溯

### 难点3: Token管理优化

**问题**: LLM上下文窗口有限，如何处理长对话？

**解决方案**:
- TokenManager自动计数
- 超过阈值自动截断
- 保留关键上下文
- 历史记录压缩

### 难点4: 代码执行的安全性

**问题**: 用户代码可能包含恶意操作，如何安全执行？

**解决方案**:
- 沙箱隔离执行
- 超时控制（默认30秒）
- 禁止危险操作（文件IO、网络请求）
- 资源限制

---

## 与同类项目对比

| 特性 | CodeCraft Agent | AutoGPT | BabyAGI |
|------|-----------------|---------|---------|
| 架构模式 | Orchestrator | Agent驱动 | 任务队列 |
| 状态管理 | 状态机 | 无 | 简单状态 |
| 反馈闭环 | ✅ 多轮审查修复 | ❌ | ❌ |
| 多模型支持 | ✅ OpenAI/Claude | 仅OpenAI | 仅OpenAI |
| 测试覆盖 | 81% | 低 | 低 |
| 学习曲线 | 低 | 中 | 中 |

---

## 未来规划

### 短期（1-2周）
- [ ] ChromaDB向量记忆
- [ ] 流式输出UI
- [ ] 在线Demo部署

### 中期（1-2月）
- [ ] 更多LLM支持（Gemini、Qwen）
- [ ] 代码补全功能
- [ ] VS Code插件

### 长期（3-6月）
- [ ] 多语言支持
- [ ] 企业级部署方案
- [ ] Agent市场

---

*文档版本: 1.0 | 更新时间: 2026-04-12*
