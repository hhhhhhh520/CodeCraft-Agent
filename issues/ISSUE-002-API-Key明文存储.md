# API Key明文存储风险

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`frontend/utils/session.py:86-107` API Key以明文形式存储在 `~/.codecraft/config.json` 文件中：

- 无加密保护
- 文件权限未设置（可能被其他用户读取）
- 历史记录文件 `history.json` 同样无保护

### 风险
- 其他用户可能读取配置文件获取API Key
- 备份时可能泄露敏感信息
- 日志或错误信息可能暴露配置内容

## 出现原因

原实现直接使用 `json.dump()` 保存配置，未对敏感字段进行特殊处理。

## 解决方案

### 1. 支持系统密钥环存储

优先使用 `keyring` 库将API Key存储到系统密钥环：
- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service API

### 2. 备选方案：混淆存储

如果密钥环不可用，使用base64混淆存储（非真正加密，仅防止明文显示）：
```python
config_to_save["api_key"] = f"enc:{base64.b64encode(key.encode()).decode()}"
```

### 3. 设置安全文件权限

```python
# POSIX系统设置仅所有者可读写
os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
```

### 4. 配置文件内容示例

```json
{
  "api_key": "***STORED_IN_KEYRING***",
  "api_type": "deepseek",
  "model": "deepseek-chat"
}
```

## 相关文件

- `frontend/utils/session.py` - 主要修改

## 使用说明

推荐安装keyring库以获得最佳安全性：
```bash
pip install keyring
```
