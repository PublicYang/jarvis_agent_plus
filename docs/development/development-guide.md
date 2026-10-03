# AgentFlow 开发者指南（Development Guide）

> **文档性质**：面向贡献者与开发者的完整工程操作手册、环境搭建指南与质量门禁规范。  
> **核心原则**：环境可再现、命令真实可执行、测试门禁全覆盖。

---

## 1. 环境准备（Prerequisites）

- **Python 运行时**：CPython `>=3.12`
- **包管理器推荐**：[`uv`](https://github.com/astral-sh/uv)（极速依赖解析与虚拟环境管理，推荐 `>=0.4.0`）

---

## 2. 快速安装与配置（Setup）

### 2.1 克隆代码与同步依赖

```bash
# 1. 克隆代码仓库
git clone <repository_url>
cd AgentFlow

# 2. 使用 uv 创建虚拟环境并同步全量依赖（含 dev 依赖）
uv sync
```

### 2.2 配置环境变量（Environment Configuration）

项目根目录提供了 `.env.example` 模板。复制并创建本地 `.env` 文件：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

编辑 `.env` 文件填入必要参数：

```dotenv
# 1. 大模型 API 密钥（必须）
# 支持官方 OpenAI 或兼容接口（如 DeepSeek、Moonshot、SiliconFlow 等）
OPENAI_API_KEY=your_actual_api_key_here

# 2. 自定义 Base URL（可选，默认 https://api.openai.com/v1）
# 示例：
# - DeepSeek: https://api.deepseek.com/v1
# - 本地 Ollama: http://localhost:11434/v1
# - OneAPI 代理: https://your-proxy-domain/v1
OPENAI_BASE_URL=https://api.openai.com/v1

# 3. 默认模型名称（可选，默认 gpt-4o-mini）
OPENAI_MODEL_NAME=gpt-4o-mini
```

> [!NOTE]
> 如果未配置 `OPENAI_API_KEY`，本地单元测试依然能完整通过（测试通过 Mock 与 Scripted 模型隔离外部网络请求），但运行真实 CLI 命令时需要有效的 API Key。

---

## 3. CLI 运行方式（CLI Usage）

项目注册了控制台命令 `jarvis`，同时支持 `python -m app` 标准模块入口。

### 3.1 单次问答（`ask` 命令）

```bash
# 基础调用
uv run python -m app ask "请帮我计算 (23 * 45) + 1024 并查看当前操作系统"

# 指定会话 ID（持久化记忆隔离）
uv run python -m app ask "我的名字是 Alice" --session-id user_01
uv run python -m app ask "你还记得我是谁吗？" --session-id user_01

# 指定模型与采样温度
uv run python -m app ask "介绍一下 Python 3.12 的新特性" --model deepseek-chat --temperature 0.2
```

### 3.2 交互式多轮对话（`chat` 命令）

启动终端 REPL 对话会话，具备实时打字机流式渲染与工具调用观察：

```bash
uv run python -m app chat --session-id my_session
```

**交互内置控制指令**：
- `exit` 或 `quit`：退出当前对话；
- `clear`：清空当前会话的历史记忆。

### 3.3 查看已注册工具（`tools` 命令）

在终端打印当前环境中已注册的全部工具契约与参数 Schema：

```bash
uv run python -m app tools
```

输出示例：
```text
                     Registered Tools in Jarvis Agent Plus                     
+-----------------------------------------------------------------------------+
| Tool Name       | Description                          | Parameters Schema  |
|-----------------+--------------------------------------+--------------------|
| calculator      | Calculate the result of a            | expression: string |
|                 | mathematical expression safely.      |                    |
| get_system_info | Query current host system and        | query_type: string |
|                 | runtime environment information.     |                    |
+-----------------------------------------------------------------------------+
```

---

## 4. 自动化测试（Testing）

项目使用 `pytest` 进行严格的质量门禁验证。测试套件利用标准 Mock 与脚本模型隔离外部大模型 API 调用，可在完全离线状态下运行。

```bash
# 运行全量测试套件（当前共 43 项测试）
uv run pytest

# 运行特定模块测试
uv run pytest tests/test_mini_agent.py
uv run pytest tests/test_tools.py
uv run pytest tests/test_memory.py

# 显示详细输出
uv run pytest -v
```

当前测试矩阵概览：
- `tests/test_infra.py`：基础设施与环境加载验证（2 项）
- `tests/test_memory.py`：滑动窗口与文件会话存储隔离验证（6 项）
- `tests/test_mini_agent.py`：MiniAgent ReAct 循环、多步推理、熔断保护验证（9 项）
- `tests/test_prompts.py`：提示词模版与输出解析器验证（7 项）
- `tests/test_renderer.py`：打字机流式渲染与事件输出验证（1 项）
- `tests/test_runnable.py`：LCEL 原语、管道组合与批处理验证（7 项）
- `tests/test_streaming.py`：流式 Chunk 聚合与事件序列验证（4 项）
- `tests/test_tools.py`：AST 计算器与平台探针 Schema 及执行验证（7 项）

---

## 5. 代码质量与格式规范（Code Quality）

### 5.1 代码静态检查（Ruff）

```bash
# 运行 Ruff Linter 检查
uv run ruff check
```

### 5.2 格式化规范（Black）

```bash
# 检查格式是否符合规范
uv run black --check .

# 执行格式化自动修复
uv run black .
```

> [!NOTE]
> 在执行工程文档标准化期间，按规则不修改业务代码。代码库中存在少数历史文件待格式化对齐，开发者在提交业务 PR 时可统一运行 `uv run black .`。

---

## 6. 开发纪律与架构红线（Engineering Rules）

1. **单向依赖红线**：
   - `tools/` 与 `llm/` 位于底层能力层，严禁向上导入 `runtime/` 或 `app/`；
   - `app/` 仅能通过 `MiniAgent` 或公开接口操作能力，不得直接耦合具体工具内部逻辑。
2. **纯函数式 LCEL 契约**：
   - 所有的自定义 Runnable 逻辑必须满足可流式化、可异步调用的纯函数式要求；
   - 状态必须外置，严禁在 Chain 内部维持不可重置的类全局变量。
3. **安全第一的工具准则**：
   - 严禁引入动态 `eval()`、未经验证的系统命令执行等高危操作；
   - 所有工具必须有精确的 Pydantic `Field(description=...)` 描述。
4. **范围控制**：
   - 当前单智能体版本**严禁引入 `langgraph` 依赖**；图状态机与多智能体调度将在后续阶段独立演进。
