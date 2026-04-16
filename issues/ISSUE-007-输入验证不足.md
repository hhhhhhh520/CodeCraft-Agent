# 输入验证不足

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

多处用户输入未经充分验证：

- `frontend/pages/chat.py:34-39` - 需求输入
- `frontend/pages/settings.py:48-53` - API Key输入

### 风险
- 资源耗尽（超长输入）
- Prompt injection攻击
- 存储型XSS（如果日志被渲染为HTML）

## 出现原因

原实现未限制输入长度，未过滤特殊字符：
```python
requirement = st.text_area("需求描述", ...)  # 无长度限制
api_key = st.text_input("API Key", ...)  # 无格式验证
```

## 解决方案

### 1. 创建输入验证模块

`backend/utils/input_validator.py` 提供验证功能：

```python
class UserRequirement(BaseModel):
    requirement: str = Field(..., min_length=1, max_length=10000)

    @field_validator("requirement")
    def sanitize(cls, v: str) -> str:
        # 移除控制字符
        v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)
        # 检测prompt injection
        ...
```

### 2. Prompt注入检测

检测常见注入模式：
- `ignore previous`
- `system prompt`
- `<|im_start|>`
- `jailbreak`

### 3. 前端限制

```python
st.text_area("需求描述", max_chars=10000)  # 限制最大字符数
st.text_input("API Key", max_chars=200)
```

### 4. 后端验证

```python
is_valid, cleaned, error = validate_requirement(requirement)
if not is_valid:
    st.error(f"输入验证失败: {error}")
    st.stop()
```

## 相关文件

- `backend/utils/input_validator.py` - 验证模块（新增）
- `frontend/pages/chat.py` - 需求输入验证
- `frontend/pages/settings.py` - API Key验证
