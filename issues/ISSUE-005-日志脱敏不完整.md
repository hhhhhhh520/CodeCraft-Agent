# 日志脱敏不完整

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`backend/core/logger.py:12-18` 日志脱敏模式不完整：

- 未覆盖DeepSeek API Key格式
- 未覆盖Anthropic API Key格式
- 未处理JSON格式的敏感数据
- 未处理JWT token
- 未处理AWS Access Key

### 风险
敏感信息可能被记录到日志文件中，导致信息泄露。

## 出现原因

原实现仅覆盖了基本的API key格式：
```python
SENSITIVE_PATTERNS = [
    (r"(api[_-]?key\s*[=:]\s*['\"]?)[^'\"\s]+(['\"]?)", ...),
    (r"(sk-[a-zA-Z0-9]{20,})", ...),  # 仅OpenAI格式
]
```

## 解决方案

扩展脱敏模式覆盖更多格式：

### 1. API Key格式
- OpenAI: `sk-...`
- DeepSeek: `sk-...` (32位hex)
- Anthropic: `sk-ant-...`

### 2. Token格式
- Bearer token
- JWT token (`eyJ...`)

### 3. 云服务密钥
- AWS Access Key (`AKIA...`)

### 4. JSON格式
```python
# 处理JSON中的敏感字段
(r"(\"api[_-]?key\"\s*:\s*\")[^\"]+(\")", r"\1***REDACTED***\2"),
```

## 相关文件

- `backend/core/logger.py` - 主要修改

## 测试验证

```python
from backend.core.logger import sanitize_message

# 测试DeepSeek Key
msg = 'api_key="sk-1234567890abcdef1234567890abcdef"'
assert "sk-1234567890abcdef1234567890abcdef" not in sanitize_message(msg)

# 测试JWT
msg = 'token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy"'
assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitize_message(msg)
```
