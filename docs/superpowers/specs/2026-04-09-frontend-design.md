---
name: CodeCraft Agent 前端界面设计
date: 2026-04-09
status: approved
---

# CodeCraft Agent 前端界面设计

## 概述

为 CodeCraft Agent 多Agent代码生成助手构建 Streamlit 前端界面，支持代码生成交互、Agent协作状态展示、历史记录管理和设置配置。

## 技术选型

- **框架**: Streamlit
- **部署场景**: 本地个人使用
- **后端集成**: 直接调用现有 backend 模块

## 项目结构

```
frontend/
├── app.py              # Streamlit 主入口
├── pages/
│   ├── chat.py         # 代码生成交互页
│   ├── history.py      # 历史记录页
│   └── settings.py     # 设置页
├── components/
│   ├── agent_status.py # Agent状态展示组件
│   └── code_display.py # 代码高亮显示组件
└── utils/
    └── session.py      # 会话状态管理
```

## 页面设计

### 1. 主页面 (app.py)

- 侧边栏导航菜单
- 默认显示对话页
- 底部显示版本信息

### 2. 对话页 (pages/chat.py)

**布局**:
- 顶部：需求输入框（多行文本区域）
- 中部：生成按钮 + Agent状态流程展示
- 底部：代码结果展示区

**功能**:
- 输入需求描述
- 点击生成按钮触发代码生成
- 实时显示 Agent 协作状态
- 展示生成的代码（语法高亮）
- 一键复制代码

### 3. 历史记录页 (pages/history.py)

**功能**:
- 列表展示历史生成记录
- 每条记录显示：时间、需求摘要、评分
- 点击展开查看完整代码
- 支持删除单条记录
- 支持清空全部历史

**存储**: 本地 JSON 文件 (`~/.codecraft/history.json`)

### 4. 设置页 (pages/settings.py)

**配置项**:
- API Key 输入（支持 DeepSeek / OpenAI）
- 模型选择下拉框
- 快速模式开关（跳过代码审查）
- 保存配置按钮

**存储**: 本地配置文件 (`~/.codecraft/config.json`)

## Agent 状态展示

**状态流转**:
```
IDLE → ANALYZING → GENERATING → REVIEWING → FIXING → DONE
```

**可视化设计**:
- 水平流程图
- 当前阶段高亮显示
- 每个阶段显示执行时间
- 失败时显示错误信息

**状态映射**:
| 状态 | 显示文本 | 颜色 |
|------|----------|------|
| IDLE | 等待输入 | 灰色 |
| ANALYZING | 分析需求 | 蓝色 |
| GENERATING | 生成代码 | 蓝色 |
| REVIEWING | 代码审查 | 黄色 |
| FIXING | 修复优化 | 橙色 |
| DONE | 完成 | 绿色 |

## 数据流

```
用户输入
    ↓
Streamlit Session State
    ↓
调用 backend.Orchestrator.process_request()
    ↓
返回结果 {code, review_score, issues}
    ↓
更新 UI + 保存历史记录
```

## 依赖

```
streamlit>=1.28.0
```

## 实现优先级

1. **P0 - 核心功能**
   - 对话页基础交互
   - 后端集成调用
   - 代码展示

2. **P1 - 状态展示**
   - Agent状态流转可视化
   - 审查评分显示

3. **P2 - 配置管理**
   - 设置页
   - API Key 配置

4. **P3 - 历史记录**
   - 历史记录存储
   - 历史记录展示
