# Prompt Vault CLI

[English](README.md) | **简体中文**

Prompt Vault CLI 是一个轻量级的本地命令行应用，用于在 JSON 文件中存储和管理可复用的 Prompt 模板。

## 功能特点

- 添加包含必填名称和内容的 Prompt
- 按插入顺序列出 Prompt
- 使用大小写不敏感的部分匹配搜索 Prompt 名称
- 使用大小写不敏感的精确匹配删除 Prompt
- 存储可选的 Prompt 描述
- 使用人类可读的 JSON 在本地持久化数据
- 防止重复名称，包括仅大小写不同的重复名称
- 通过原子文件替换降低数据丢失风险
- 提供清晰的应用错误和可预测的退出码
- 使用 pytest 自动化测试验证行为

## 环境要求

- Python 3.12 或更高版本
- pytest，仅在运行测试时需要

应用本身仅使用 Python 标准库。

## 安装

克隆仓库，或进入已有的项目目录：

```shell
git clone <repository-url>
cd prompt-vault-cli
```

创建虚拟环境：

```shell
python -m venv .venv
```

在 macOS 或 Linux 上激活虚拟环境：

```shell
source .venv/bin/activate
```

在 Windows PowerShell 上激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装用于开发和测试的 pytest：

```shell
python -m pip install pytest
```

## 使用方法

请在仓库根目录中运行命令。

```text
python -m src.main add --name NAME --content CONTENT [--description DESCRIPTION]
python -m src.main list
python -m src.main search QUERY
python -m src.main delete NAME
```

添加一个 Prompt：

```shell
python -m src.main add --name "code-review" --content "Review the following code."
```

添加带描述的 Prompt：

```shell
python -m src.main add --name "email summary" --content "Summarize this email." --description "Creates a concise email summary."
```

列出所有 Prompt：

```shell
python -m src.main list
```

按完整名称或部分名称搜索：

```shell
python -m src.main search "review"
```

按名称删除 Prompt：

```shell
python -m src.main delete "code-review"
```

## 输出示例

添加成功：

```text
Added prompt: code-review
```

列出 Prompt，其中一个 Prompt 没有描述：

```text
Name: code-review
Description: (none)
Content: Review the following code.

Name: email summary
Description: Creates a concise email summary.
Content: Summarize this email.
```

重复名称错误：

```text
Error: A prompt named "code-review" already exists.
```

搜索无结果：

```text
Error: no prompts found matching "translate".
```

删除成功：

```text
Deleted prompt: code-review
```

应用错误会写入标准错误（`stderr`），成功输出会写入标准输出（`stdout`）。

## 数据存储

默认数据文件是当前工作目录中的 `data.json`。文件缺失表示一个空 vault，第一次添加 Prompt 时会创建该文件。运行时的 `data.json` 文件会被 Git 忽略。

数据以人类可读的 UTF-8 JSON 格式存储，Prompt 按插入顺序保存。Prompt 名称保留原始大小写，而重复检查、搜索和删除使用大小写不敏感的比较。

写入时会先在同一目录中创建临时文件，再执行原子替换，以降低数据丢失风险。空文件、格式错误、无法读取或结构无效的文件会产生清晰的 `StorageError`，而不会被静默丢弃或替换。

## 退出码

- `0`：命令执行成功
- `1`：发生预期的应用错误或存储错误
- `2`：`argparse` 检测到命令行参数错误

## 测试

运行完整测试套件：

```shell
python -m pytest -v
```

分别运行各测试套件：

```shell
python -m pytest tests/test_models.py -v
python -m pytest tests/test_storage.py -v
python -m pytest tests/test_cli.py -v
```

编译源代码和测试以检查 Python 语法：

```shell
python -m compileall src tests
```

## 项目结构

```text
prompt-vault-cli/
├── REQUIREMENTS.md
├── IMPLEMENTATION_PLAN.md
├── README.md
├── README.zh-CN.md
├── LEARNING_LOG.md
├── src/
│   ├── __init__.py
│   ├── errors.py
│   ├── models.py
│   ├── storage.py
│   └── main.py
└── tests/
    ├── test_models.py
    ├── test_storage.py
    └── test_cli.py
```

生产模块：

- `src/__init__.py` 将 `src` 标记为 Python 包。
- `src/errors.py` 定义应用异常层次结构。
- `src/models.py` 定义并验证 `Prompt` 数据模型。
- `src/storage.py` 管理 JSON 持久化和 Prompt 集合操作。
- `src/main.py` 定义 CLI 参数解析、输出格式和退出码处理。

## 设计说明

- `Prompt` 是不可变 dataclass。
- 模型负责验证和规范化。
- `PromptStorage` 负责 JSON 持久化和集合操作。
- `main.py` 负责 CLI 命令解析、输出格式和退出码转换。
- Prompt 名称使用 `casefold()` 比较，同时保留存储时的原始大小写。
- 测试注入临时存储路径，避免修改真实用户数据。

## 项目范围

当前版本有意不包含：

- Web 界面
- 数据库
- 云同步
- 身份认证
- 外部 AI API 集成
- Prompt 编辑
- 标签或分类
- 导入或导出命令

## 学习流程

本仓库通过需求定义、批准后的实现计划、Agent 分阶段开发、自动化测试、手动 CLI 集成测试、只读代码审查、审查驱动的修复、聚焦的 Git 提交和文档完善逐步完成。

`LEARNING_LOG.md` 保留给开发者进行个人复盘。
