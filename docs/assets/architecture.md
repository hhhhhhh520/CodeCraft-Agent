# CodeCraft Agent 架构图

> 本文档包含项目的核心架构图，使用 Mermaid 格式，可在 GitHub 和支持 Mermaid 的 Markdown 编辑器中渲染。

---

## 1. 系统架构图

```mermaid
graph TB
    subgraph 用户交互层
        CLI[CLI - Typer/Rich]
        WEB[Web - Streamlit]
    end

    subgraph 协调层
        ORC[Orchestrator<br/>多Agent协调器]
        SM[StateMachine<br/>状态机]
        CTX[SharedContext<br/>共享上下文]
    end

    subgraph Agent层
        GEN[Generator<br/>代码生成]
        REV[Reviewer<br/>代码审查]
        DBG[Debugger<br/>问题修复]
        TST[TestGenerator<br/>测试生成]
    end

    subgraph 工具层
        AST[AST Parser<br/>语法解析]
        EXE[Executor<br/>代码执行]
    end

    subgraph 基础设施层
        LLM[LLM Adapter<br/>OpenAI/Claude/DeepSeek]
        MEM[Memory<br/>记忆系统]
        TOK[Token Manager<br/>Token管理]
    end

    CLI --> ORC
    WEB --> ORC
    ORC --> SM
    ORC --> CTX
    SM --> GEN
    SM --> REV
    SM --> DBG
    SM --> TST
    GEN --> AST
    DBG --> EXE
    GEN --> LLM
    REV --> LLM
    DBG --> LLM
    LLM --> TOK
    CTX --> MEM

    style CLI fill:#e1f5fe
    style WEB fill:#e1f5fe
    style ORC fill:#fff3e0
    style SM fill:#fff3e0
    style CTX fill:#fff3e0
    style GEN fill:#e8f5e9
    style REV fill:#e8f5e9
    style DBG fill:#e8f5e9
    style TST fill:#e8f5e9
    style AST fill:#fce4ec
    style EXE fill:#fce4ec
    style LLM fill:#f3e5f5
    style MEM fill:#f3e5f5
    style TOK fill:#f3e5f5
```

---

## 2. Agent协作流程图

```mermaid
flowchart LR
    subgraph 输入
        REQ[用户需求]
    end

    subgraph 生成阶段
        GEN[Generator<br/>代码生成]
    end

    subgraph 审查阶段
        REV{Reviewer<br/>代码审查}
    end

    subgraph 修复阶段
        DBG[Debugger<br/>问题修复]
    end

    subgraph 测试阶段
        TST[TestGenerator<br/>生成测试]
    end

    subgraph 输出
        DONE[完成输出]
    end

    REQ --> GEN
    GEN --> REV
    REV -->|通过| TST
    REV -->|不通过| DBG
    DBG --> REV
    TST --> DONE

    style REQ fill:#bbdefb
    style GEN fill:#c8e6c9
    style REV fill:#fff9c4
    style DBG fill:#ffccbc
    style TST fill:#d1c4e9
    style DONE fill:#b2dfdb
```

### 反馈闭环机制

```mermaid
sequenceDiagram
    participant U as 用户
    participant O as Orchestrator
    participant G as Generator
    participant R as Reviewer
    participant D as Debugger

    U->>O: 提交需求
    O->>G: 生成代码
    G-->>O: 返回代码

    loop 最多3次迭代
        O->>R: 审查代码
        R-->>O: 返回审查结果
        alt 审查通过
            O-->>U: 返回最终代码
        else 审查不通过
            O->>D: 修复问题
            D-->>O: 返回修复后代码
        end
    end
```

---

## 3. 状态机转换图

```mermaid
stateDiagram-v2
    [*] --> PENDING: 初始化

    PENDING --> ANALYZING: 开始处理

    ANALYZING --> GENERATING: 生成任务
    ANALYZING --> REVIEWING: 审查任务

    GENERATING --> REVIEWING: 生成完成
    GENERATING --> FAILED: 生成失败

    REVIEWING --> TESTING: 审查通过
    REVIEWING --> FIXING: 审查不通过
    REVIEWING --> DONE: 无需测试

    FIXING --> REVIEWING: 修复完成
    FIXING --> GENERATING: 需要重新生成

    TESTING --> DONE: 测试通过
    TESTING --> FIXING: 测试失败

    FAILED --> PENDING: 重试

    DONE --> [*]: 任务完成

    note right of PENDING
        等待处理
    end note

    note right of ANALYZING
        分析任务类型
        (generate/review/debug/test)
    end note

    note right of GENERATING
        Generator Agent
        生成代码
    end note

    note right of REVIEWING
        Reviewer Agent
        多维度审查
    end note

    note right of FIXING
        Debugger Agent
        修复问题
    end note

    note right of TESTING
        TestGenerator Agent
        生成测试用例
    end note
```

### 状态说明

| 状态 | 说明 | 可转换状态 |
|------|------|------------|
| PENDING | 等待处理 | ANALYZING |
| ANALYZING | 分析任务类型 | GENERATING, REVIEWING |
| GENERATING | 代码生成中 | REVIEWING, FAILED |
| REVIEWING | 代码审查中 | TESTING, FIXING, DONE |
| FIXING | 问题修复中 | REVIEWING, GENERATING |
| TESTING | 测试生成中 | DONE, FIXING |
| DONE | 任务完成 | - |
| FAILED | 任务失败 | PENDING |

---

## 4. 数据流图

```mermaid
flowchart TB
    subgraph 输入层
        INPUT[用户输入<br/>自然语言需求]
    end

    subgraph 处理层
        PARSE[需求解析]
        ROUTE[任务路由]
        EXEC[Agent执行]
    end

    subgraph 存储层
        CTX[SharedContext<br/>会话上下文]
        MEM[Memory<br/>历史记忆]
    end

    subgraph 输出层
        CODE[生成的代码]
        REVIEW[审查报告]
        TEST[测试用例]
    end

    INPUT --> PARSE
    PARSE --> ROUTE
    ROUTE --> EXEC
    EXEC --> CTX
    CTX --> MEM
    EXEC --> CODE
    EXEC --> REVIEW
    EXEC --> TEST

    style INPUT fill:#e3f2fd
    style PARSE fill:#fff8e1
    style ROUTE fill:#fff8e1
    style EXEC fill:#fff8e1
    style CTX fill:#f3e5f5
    style MEM fill:#f3e5f5
    style CODE fill:#e8f5e9
    style REVIEW fill:#e8f5e9
    style TEST fill:#e8f5e9
```

---

## 5. LLM抽象层架构

```mermaid
classDiagram
    class BaseLLM {
        <<abstract>>
        +generate(prompt: str) str
        +stream(prompt: str) Iterator
        +count_tokens(text: str) int
    }

    class OpenAILLM {
        -client: OpenAI
        -model: str
        +generate(prompt: str) str
        +stream(prompt: str) Iterator
    }

    class ClaudeLLM {
        -client: Anthropic
        -model: str
        +generate(prompt: str) str
        +stream(prompt: str) Iterator
    }

    class TokenManager {
        -max_tokens: int
        -encoding: Encoding
        +truncate(text: str, max_tokens: int) str
        +count(text: str) int
    }

    BaseLLM <|-- OpenAILLM
    BaseLLM <|-- ClaudeLLM
    BaseLLM --> TokenManager : uses
```

---

## 渲染说明

- 以上图表使用 **Mermaid** 语法编写
- GitHub 原生支持 Mermaid 渲染
- VS Code 可安装 "Markdown Preview Mermaid Support" 插件预览
- 在线预览: [Mermaid Live Editor](https://mermaid.live/)
