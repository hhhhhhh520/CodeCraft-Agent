# exec()代码注入风险

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`demos/demo_performance.py:60,101` 直接使用 `exec()` 执行代码：

```python
exec_globals = {}
exec(SLOW_CODE, exec_globals)  # 第60行
exec(optimized_code, exec_globals)  # 第101行
```

### 风险
- 如果LLM生成的优化代码包含恶意内容，可执行任意操作
- demo代码可能被误复制到生产环境
- 无安全验证，无命名空间限制

## 出现原因

demo文件为简化演示直接使用 `exec()`，未考虑安全风险。

## 解决方案

### 1. 使用安全执行方法

引入 `CodeExecutor.safe_exec()` 方法：
- 使用 `CodeValidator` 进行AST安全验证
- 使用受限全局命名空间
- 仅允许安全的内置函数

### 2. 添加安全执行包装函数

```python
def safe_exec_code(code: str, func_name: str, *args, **kwargs):
    """安全执行代码并调用指定函数"""
    executor = CodeExecutor(timeout=30)
    result = executor.safe_exec(code)

    if not result["success"]:
        print(f"  ⚠️ 安全执行失败: {result.get('error')}")
        return None

    if func_name in result["globals"]:
        return result["globals"][func_name](*args, **kwargs)
    return None
```

### 3. 受限命名空间

仅允许安全的内置函数：
```python
safe_builtins = {
    "print", "range", "len", "str", "int", "float", "bool",
    "list", "dict", "set", "tuple", "enumerate", "zip",
    "map", "filter", "sorted", "reversed", "sum", "min", "max",
}
```

## 相关文件

- `demos/demo_performance.py` - 主要修改
- `backend/tools/executor.py` - 提供安全执行方法

## 参考资料

- [Python exec安全最佳实践](https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html)
