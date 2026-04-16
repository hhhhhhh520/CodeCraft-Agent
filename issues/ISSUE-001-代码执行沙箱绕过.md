# 代码执行沙箱绕过风险

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`backend/tools/executor.py:38-50` 代码执行器沙箱不完整，存在以下问题：

1. **环境变量泄露**: `HOME` 和 `TEMP` 环境变量被传递，恶意代码可访问用户目录
2. **无安全验证**: 用户/LLM生成的代码直接执行，未检查危险操作
3. **工作目录未限制**: 在系统临时目录执行，可能访问其他文件

### 攻击场景
```python
# 恶意代码可访问用户HOME目录
import os
home = os.environ.get("HOME", "")
with open(os.path.join(home, ".ssh/id_rsa")) as f:
    print(f.read())
```

## 出现原因

原实现仅设置了受限PATH，但：
- 传递了HOME、TEMP等敏感环境变量
- 未对代码进行AST安全分析
- 工作目录未隔离

## 解决方案

### 1. 添加代码安全验证器 `CodeValidator`

使用AST解析检测危险操作：
- 危险导入: `os`, `subprocess`, `socket`, `shutil`, `pickle`, `ctypes`等
- 危险函数: `eval`, `exec`, `compile`, `__import__`, `open`等
- 危险模式: 动态导入、反射访问私有属性、访问全局命名空间

### 2. 强化沙箱环境

- 移除HOME、TEMP、USER等敏感环境变量
- 使用 `TemporaryDirectory` 作为工作目录
- 添加内存限制参数

### 3. 添加安全执行方法 `safe_exec()`

用于demo等场景，使用受限命名空间执行：
- 仅允许安全的内置函数
- 可自定义允许的全局变量

## 相关文件

- `backend/tools/executor.py` - 主要修改

## 参考资料

- [Python AST安全分析](https://docs.python.org/3/library/ast.html)
- [沙箱执行最佳实践](https://cheatsheetseries.owasp.org/cheatsheets/Python_Sandbox_Cheatsheet.html)
