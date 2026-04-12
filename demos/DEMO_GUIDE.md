# CodeCraft Agent 演示指南

> 快速演示项目核心能力的完整指南

---

## 快速开始

### 环境准备

```bash
# 1. 进入项目目录
cd "D:/my project/CodeCraft Agent"

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API Key
export DEEPSEEK_API_KEY="your-api-key"
# 或
export OPENAI_API_KEY="your-api-key"
```

### 运行所有演示

```bash
python demos/run_all_demos.py
```

---

## 演示列表

### Demo 1: 排序算法生成

**文件**: `demos/demo_quick_sort.py`

**演示内容**:
- 根据自然语言需求生成快速排序算法
- 展示代码生成能力
- 展示PEP8规范、类型注解

**运行方式**:
```bash
python demos/demo_quick_sort.py
```

**预期输出**:
- 生成的快速排序代码
- 代码行数统计
- 记忆系统状态

---

### Demo 2: 安全漏洞修复

**文件**: `demos/demo_security_fix.py`

**演示内容**:
- 检测SQL注入漏洞
- 自动修复安全问题
- 展示审查-修复闭环

**运行方式**:
```bash
python demos/demo_security_fix.py
```

**预期输出**:
- 原始代码（存在漏洞）
- 审查结果（发现安全问题）
- 修复后代码（参数化查询）
- 重新审查结果

---

### Demo 3: 性能优化

**文件**: `demos/demo_performance.py`

**演示内容**:
- 检测O(n²)复杂度问题
- 优化为O(n)复杂度
- 性能对比测试

**运行方式**:
```bash
python demos/demo_performance.py
```

**预期输出**:
- 原始代码（O(n²)）
- 性能测试结果
- 优化后代码（O(n)）
- 性能提升倍数

---

### Demo 4: 完整工作流

**文件**: `demos/demo_full_workflow.py`

**演示内容**:
- 完整的代码生成→审查→修复→测试流程
- 多Agent协作演示
- 状态机状态转换追踪

**运行方式**:
```bash
python demos/demo_full_workflow.py
```

**预期输出**:
- 工作流图示
- 状态转换历史
- 最终生成的代码
- 审查评分

---

## 演示场景设计

### 场景1: 面试演示（5分钟）

```bash
# 1. 快速展示CLI
python -m cli.main generate "实现一个二分查找算法"

# 2. 运行完整工作流Demo
python demos/demo_full_workflow.py

# 3. 展示架构图
# 打开 README.md 或 docs/assets/architecture.md
```

### 场景2: 技术分享（15分钟）

```bash
# 1. 运行所有Demo
python demos/run_all_demos.py

# 2. 深入讲解架构
# 打开 HIGHLIGHTS.md

# 3. Q&A环节
# 参考 INTERVIEW_GUIDE.md
```

### 场景3: 功能验证（10分钟）

```bash
# 1. 安全漏洞修复
python demos/demo_security_fix.py

# 2. 性能优化
python demos/demo_performance.py

# 3. 查看测试覆盖率
pytest tests/ --cov=backend --cov-report=html
```

---

## 常见问题

### Q: Demo运行报错 "API Key not found"

**解决方案**:
```bash
# 设置环境变量
export DEEPSEEK_API_KEY="your-key"
# 或
export OPENAI_API_KEY="your-key"
```

### Q: Demo运行报错 "Module not found"

**解决方案**:
```bash
# 确保在项目根目录运行
cd "D:/my project/CodeCraft Agent"

# 安装依赖
pip install -r requirements.txt
```

### Q: 生成的代码质量不高

**原因**: LLM模型能力限制

**解决方案**:
- 使用更强大的模型（如GPT-4、Claude-3）
- 调整Agent的SYSTEM_PROMPT
- 增加审查迭代次数

---

## 演示技巧

### 技巧1: 准备备用方案

- 录制演示视频作为备份
- 准备截图作为备用展示材料
- 熟悉代码结构，可以手动讲解

### 技巧2: 控制演示节奏

- 先展示简单Demo建立信心
- 再展示复杂Demo体现深度
- 最后展示架构设计

### 技巧3: 互动环节

- 让观众提出需求，现场演示
- 展示代码审查发现的问题
- 讨论可能的改进方向

---

## 文件结构

```
demos/
├── demo_quick_sort.py      # 排序算法生成演示
├── demo_security_fix.py    # 安全漏洞修复演示
├── demo_performance.py     # 性能优化演示
├── demo_full_workflow.py   # 完整工作流演示
├── run_all_demos.py        # 一键运行所有Demo
└── DEMO_GUIDE.md           # 本文件
```

---

*文档版本: 1.0 | 更新时间: 2026-04-12*
