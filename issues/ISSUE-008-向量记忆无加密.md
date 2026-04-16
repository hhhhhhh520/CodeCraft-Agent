# 向量记忆无加密风险

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`backend/core/vector_memory.py:40-44` ChromaDB数据无加密存储：

```python
os.makedirs(persist_dir, exist_ok=True)
self.client = chromadb.PersistentClient(path=persist_dir)
```

### 风险
- 向量数据库存储在 `./memory/chroma` 目录
- 包含用户需求描述和生成的代码
- 可能包含敏感业务逻辑
- 其他用户可能读取数据

## 出现原因

原实现未考虑：
- 目录权限设置
- 敏感内容检测
- 数据加密存储

## 解决方案

### 1. 设置安全目录权限

```python
def _set_secure_permissions(path: str) -> None:
    """设置安全目录权限（仅所有者可访问）"""
    if os.name == 'posix':
        os.chmod(path, stat.S_IRWXU)  # 700
```

### 2. 敏感内容检测

添加敏感关键词检测，拒绝存储包含敏感信息的内容：

```python
SENSITIVE_KEYWORDS = [
    "api_key", "apikey", "password", "secret", "token",
    "credential", "private_key", "access_key",
]

def _check_sensitive_content(self, text: str) -> bool:
    """检查文本是否包含敏感信息"""
    for keyword in self.SENSITIVE_KEYWORDS:
        if keyword in text.lower():
            return True
    return False
```

### 3. 存储时验证

```python
def add(self, requirement: str, code: str, ...):
    if self._check_sensitive_content(requirement):
        raise ValueError("需求描述包含敏感信息，不应存储到向量记忆")
```

## 相关文件

- `backend/core/vector_memory.py` - 主要修改

## 安全建议

对于生产环境：
1. 考虑使用加密文件系统
2. 实施数据保留策略，定期清理旧数据
3. 审计日志记录所有访问
