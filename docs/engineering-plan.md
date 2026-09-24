# Jarvis Agent Plus 工程化与工具链选型规划（Engineering Plan）

> **工程定位**：为 Jarvis Agent Plus 提供现代化、高性能、高确定性与高可维护性的 Python 工程基础设施。  
> **规划标准**：严格遵循现代 Python 软件工程规范，杜绝过时工具链与松散配置。

---

## 1. 核心工具链选型矩阵

| 工具 | 角色 / 定位 | 版本 / 范围 | 选型核心理由 |
| :--- | :--- | :--- | :--- |
| **Python** | 核心运行环境 | `3.12+` | 原生性能大幅提升、强大的泛型语法（PEP 695 类型参数语法）、增强的异步与类型检查支持。 |
| **uv** | 包管理与虚拟环境 | `>=0.4.0` | 极速依赖解析与安装（比 pip 快 10~100 倍）、内置虚拟环境管理、严格的跨平台锁文件锁定。 |
| **Ruff** | 极致快速 Linter | `>=0.6.0` | 基于 Rust 构建，秒级检查全项目代码，整合 flake8、isort 等数十种规则，极大提升本地开发反馈速度。 |
| **Black** | 确定性代码格式化器 | `>=24.0.0` | 团队风格一致性基准，无配置哲学，消除关于代码风格的无谓争论，与 Ruff Formatter 协同保障格式整洁。 |
| **pytest** | 自动化测试框架 | `>=8.0.0` | Python 工业界首选测试框架，丰富的 fixture 机制、优异的断言重写能力、无缝支持异步测试（`pytest-asyncio`）。 |
| **Typer** | 现代命令行（CLI）框架 | `>=0.12.0` | 基于 Python 类型注解自动生成帮助文档与参数解析，代码优雅，易于打造直观流利的终端交互体验。 |
| **httpx** | 现代化 HTTP/网络客户端 | `>=0.27.0` | 原生异步（async/await）与同步双持、全面支持 HTTP/2、标准连接池管理、出色的 Mock 扩展性，非常适于编写 LLM 模拟测试。 |

---

## 2. 深入技术论证：为什么选择这些工具？

### 2.1 为什么选择 Python 3.12？
- **运行时性能大幅优化**：Python 3.12 引入了更强大的专门化自适应解释器（Specializing Adaptive Interpreter），函数调用开销更低，在 Agent 高频的字典与对象处理中性能显著优于 3.10/3.11。
- **现代化类型系统（Type Parameter Syntax）**：PEP 695 引入了原生的 `type Alias = ...` 与 `def func[T](val: T) -> T:` 泛型语法，显著提升了在构建复杂 Runnable 链与 Schema 契约时的静态类型可读性与 IDE 补全体验。
- **更优的错误回溯信息**：更精准的高亮报错行定位，极大降低调试深层 LCEL 管道时的心理压力。

### 2.2 为什么选择 uv 作为包与环境管理器？
- **极速构建反馈**：传统 `pip` 和 `poetry` 在解析深度嵌套的依赖树（特别是 `langchain`、`pydantic`、`numpy` 等生态依赖）时经常耗时数分钟甚至超时死锁。`uv` 利用 Rust 实现高并发并行依赖解析，可在数秒内完成依赖安装与锁定。
- **单一工具收敛（All-in-One）**：兼顾 Python 版本管理（`uv python`）、虚拟环境创建（`uv venv`）、依赖安装（`uv pip / uv sync`）与脚本独立运行（`uv run`），极大简化后续 CI/CD 与多环境同步流程。

### 2.3 为什么同时规划 Ruff 与 Black？
- **Ruff 负责严苛的静态规则审计**：利用 Ruff 高速扫描未使用的导入、变量遮蔽、不安全异常捕获、已废弃 API 使用以及类型提示不规范。
- **Black 负责确定性的美学排版**：Black 拥有极强的行业共识与严格的代码折叠规范。通过配置确保代码在格式化上达到毫无歧义的统一标准。

### 2.4 为什么选择 pytest 作为质量门禁？
- **单 Phase 强契约验证**：每个 Phase 都必须编写独立的测试套件。pytest 的参数化测试（`@pytest.mark.parametrize`）与强大的 Mock 体系（配合 `pytest-mock`）能够轻松模拟 LLM 返回、网络故障与流式 Chunk 截断。
- **异步测试原生支持**：结合 `pytest-asyncio`，无缝覆盖 `ainvoke`、`astream` 等异步原语的端到端调用验证。

### 2.5 为什么选择 Typer 构建 CLI？
- **强类型与代码自解释**：在 Phase 6（Streaming）与 Phase 8（Mini Agent）中，我们需要一个友好的终端人机对话交互界面。Typer 完美契合本项目“强类型第一”的工程哲学，无需编写冗长易错的 `argparse` 代码即可自动生成参数类型校验与终端配色输出。

### 2.6 为什么选择 httpx？
- **双模态支持**：自研系统和框架适配层需要同时支持同步与异步 HTTP 通信。`httpx` 提供了与 `requests` 几乎一致的 API，同时支持原生的 `AsyncClient`。
- **网络测试与 Mock 能力**：在不需要实际消耗 OpenAI API Key 的单元测试中，`httpx.MockTransport` 可以以极高的效率拦截 HTTP 请求并返回固定的 Mock SSE 响应，确保 CI 环境能够在离线状态下稳定运行。

---

## 3. 工程目录落地方案

在 Phase 1 正式构建代码骨架时，将遵循以下标准分层结构：

```text
jarvis-agent-plus/
├── docs/                      # 架构设计、路线图、ADR 决策与工程规划
│   ├── roadmap.md
│   ├── architecture.md
│   ├── migration-map.md
│   ├── engineering-plan.md
│   └── adr/
│       ├── ADR-001-why-langchain.md
│       ├── ADR-002-runnable-first.md
│       └── ADR-003-no-langgraph-yet.md
├── app/                       # 终端交互与应用程序入口 (Typer CLI)
├── llm/                       # 模型适配器与通用模型封装
├── prompts/                   # 结构化提示词模板与输出解析器
├── tools/                     # 标准化工具定义 (BaseTool / @tool)
├── runtime/                   # LCEL 核心执行链与 Mini-Agent 控制调度
├── memory/                    # 会话历史与外置状态持久化
├── tests/                     # 单元测试与端到端集成测试套件
├── pyproject.toml             # 项目元数据与依赖配置
├── README.md                  # 项目总览
└── .gitignore                 # Git 忽略配置
```

---

## 4. 实施阶段与管控纪律

1. **Phase 0（当前）**：完成全部工程选型规划与文档定义，不产生任何 Python 代码。
2. **Phase 1**：创建上述目录结构骨架与必要的包标识文件（`__init__.py`），不写具体逻辑。
3. **Phase 2**：落地 `pyproject.toml` 依赖配置，打通 `uv`、`ruff`、`pytest` 工具链，建立基线环境。
4. **禁止提前偷跑**：在未通过 Phase 0 评审前，绝对不创建任何 Python 实现文件。
