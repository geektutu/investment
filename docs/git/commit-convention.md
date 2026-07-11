# Git Commit 规范

本项目采用 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 规范，确保提交历史清晰、可读，并能够自动化生成 Changelog。

---

## 格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

---

## Type（类型）

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 仅文档变更 |
| `style` | 代码格式调整（不影响功能，如空格、分号等） |
| `refactor` | 代码重构（不新增功能、不修复 Bug） |
| `perf` | 性能优化 |
| `test` | 新增或修改测试 |
| `build` | 构建系统或外部依赖变更 |
| `ci` | CI/CD 配置变更 |
| `chore` | 其他杂项（如 .gitignore 修改） |

---

## Scope（范围，可选）

标明本次提交影响的范围，根据项目模块划分：

| Scope | 说明 |
|-------|------|
| `frontend` | Vue 前端（web/ 目录） |
| `data` | Python 数据脚本（data/ 目录） |
| `etf` | ETF 数据处理逻辑 |
| `docs` | 文档 |

---

## Description（描述，必填）

- 简短概括本次变更内容（**不超过 72 字符**）
- 使用**祈使句**，现在时，首字母小写
- 末尾不加句号

示例：
```
feat(frontend): add ETF ATR data table
fix(data): retry on TickFlow rate limit error
```

---

## Body（正文，可选）

- 与 description 之间空一行
- 补充说明变更的**原因**（Why）和**背景**，而不是如何实现（How）

---

## Footer（页脚，可选）

### Breaking Change

破坏性变更必须在 footer 中标注，同时 `type` 后加 `!`：

```
feat(etf)!: change ATR calculation window from 14 to 20 days

BREAKING CHANGE: ATR window parameter changed from 14 to 20 days.
```

### 引用 Issue

```
fix(data): correct drawdown calculation for empty dataframe

Closes #42
Refs #15
```

---

## 完整示例

### 简单提交

```
feat(frontend): add ETF ATR data table
```

### 带 body

```
fix(data): add rate limit retry for TickFlow API

TickFlow free tier limits to 60 requests/min. Added try-except
with 60s sleep and retry to handle RateLimitError gracefully.
```

### Bug 修复

```
fix(etf): correct current drawdown sign

Current drawdown was showing as positive value. Now correctly
displays as negative percentage.
```

### 构建/依赖变更

```
build(data): pin pandas to 3.0.3
```

### 杂项

```
chore: add .venv and __pycache__ to .gitignore
```

---

## 快速参考

```bash
# 新功能
git commit -m "feat(frontend): add xxx"

# Bug 修复
git commit -m "fix(data): correct xxx"

# 重构
git commit -m "refactor(etf): simplify xxx"

# 文档
git commit -m "docs: update README"

# 依赖
git commit -m "build(data): add tickflow dependency"
```
