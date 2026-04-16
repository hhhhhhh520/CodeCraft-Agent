# 依赖版本未锁定

> 创建时间: 2026-04-16
> 状态: 🟢 已解决

## 问题描述

`requirements.txt` 依赖版本使用 `>=` 未锁定：

```
langchain>=0.2.0
langchain-openai>=0.1.0
...
```

### 风险
- 自动安装有漏洞的新版本
- 依赖冲突
- 不可复现的构建

## 出现原因

原实现使用 `>=` 允许自动升级，但未考虑：
- 新版本可能引入安全漏洞
- 不同环境可能安装不同版本
- CI/CD构建可能不一致

## 解决方案

### 1. 锁定依赖版本

`requirements.txt` 使用精确版本：
```
langchain==0.2.14
langchain-openai==0.1.21
```

### 2. 创建开发依赖文件

`requirements.in` 用于开发，允许版本范围：
```
langchain>=0.2.0
pytest>=8.0.0
```

### 3. 添加安全依赖

新增 `keyring>=25.0.0` 用于安全存储API Key。

### 4. 版本更新流程

```bash
# 更新依赖时
pip-compile requirements.in --output-file requirements.txt

# 或手动更新特定依赖
pip install langchain==0.2.15 --upgrade
pip freeze > requirements.txt
```

## 相关文件

- `requirements.txt` - 锁定版本（生产）
- `requirements.in` - 开发依赖

## 安全检查

建议添加依赖安全扫描：
```bash
pip install pip-audit
pip-audit -r requirements.txt
```
