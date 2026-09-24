# Jarvis Agent Plus 研发路线图（Roadmap）

> **版本定位**：从自研 Runtime 到工业级 LangChain LCEL 核心抽象的 9 阶段演进方案。  
> **核心原则**：单一阶段单一能力、严格代码量控制（200~500行）、完备质量门禁、强对比分析。

---

## 阶段概览

```text
V0 Foundation (工程与设计地基)
├── Phase 0: Design Gate (架构设计与映射门禁) ◄ [当前阶段]
├── Phase 1: Project Skeleton (工程目录骨架)
└── Phase 2: Development Infrastructure (现代化开发基础设施)

V1 LangChain Core (核心抽象迁移)
├── Phase 3: Runnable Foundation (LCEL 核心原语与统一协议)
├── Phase 4: Prompt Engineering (结构化与强类型提示词工程)
└── Phase 5: Tool Calling (标准化工具绑定与调用闭环)

V2 Agent Capability (运行时高阶能力)
├── Phase 6: Streaming (端到端双工与流式生成)
├── Phase 7: Memory (状态外置与会话历史注入)
└── Phase 8: Mini Agent (LCEL 驱动的 ReAct 闭环智能体)
```

---

## V0 Foundation

### Phase 0: Design Gate（架构设计与映射门禁）

- **Goal**：完成项目顶层设计，建立自研 Jarvis Agent 与 LangChain 的完整认知映射，确立工程规范与 ADR。
- **Deliverables**：
  - `README.md`：项目定位、学习目标与演进关系。
  - `docs/roadmap.md`：完整九阶段实施规划与质量门禁。
  - `docs/architecture.md`：分层架构、数据流与组件对照。
  - `docs/migration-map.md`：自研系统与 LangChain 核心机制全量映射。
  - `docs/engineering-plan.md`：工程选型与现代化工具链技术论证。
  - `docs/adr/ADR-001-why-langchain.md`：技术选型决策记录。
  - `docs/adr/ADR-002-runnable-first.md`：核心抽象优先级决策。
  - `docs/adr/ADR-003-no-langgraph-yet.md`：架构边界与范围控制决策。
- **Learning Focus**：
  - 理清框架抽象背后的设计动机。
  - 明确“框架为我解决了什么”与“哪些底层能力仍需自主掌控”。
- **Jarvis 对照**：
  - 对标 Jarvis 系统的设计规范和概念词汇表，建立一一对应的翻译词典。
- **Expected Git Diff**：
  - 全量文档生成，纯 Markdown 文件，代码变更量为 0。
- **Quality Gate**：
  - 架构设计文档经架构师（Architect）审核通过；
  - 严禁产生任何 Runnable、Tool 或业务代码。

---

### Phase 1: Project Skeleton（工程目录骨架）

- **Goal**：建立符合现代 Python 规范的模块化分层目录结构，定义各模块职责边界。
- **Deliverables**：
  - 目录树结构：`app/`, `llm/`, `prompts/`, `tools/`, `runtime/`, `memory/`, `tests/`。
  - 核心模块的 `__init__.py` 占位与顶层暴露声明。
  - 基础 `.gitignore` 与类型导出检查。
- **Learning Focus**：
  - LangChain 项目的标准工程分层结构。
  - 模块间高内聚低耦合的单向依赖规则（如 runtime 依赖 runnable/llm，反之不依赖）。
- **Jarvis 对照**：
  - 对标 Jarvis 自研目录结构（`core/`, `planner/`, `tools/`, `agent/`），转化为 LangChain 模块化分层。
- **Expected Git Diff**：
  - 约 50~100 行（仅包含 `__init__.py` 与 `.gitignore`）。
- **Quality Gate**：
  - 目录层次清晰；模块间无循环导入隐患；无任何多余伪代码。

---

### Phase 2: Development Infrastructure（现代化开发基础设施）

- **Goal**：配置以 `uv` 为核心的现代 Python 工具链，集成格式化、代码检查与测试框架。
- **Deliverables**：
  - `pyproject.toml`：依赖声明（Python 3.12, langchain-core, langchain-openai, typer, httpx, pytest, ruff, black）。
  - 代码格式与 Linter 配置（Ruff / Black 规则）。
  - 基础测试入口与环境验证测试 `tests/test_infra.py`。
- **Learning Focus**：
  - 现代 Python 打包体系与依赖解析机制。
  - 严格类型检查与代码风格在 Agent 系统中的必要性。
- **Jarvis 对照**：
  - 替代原 Jarvis 中传统的 `requirements.txt` / setup.py 与松散校验脚本。
- **Expected Git Diff**：
  - 约 100~200 行（配置文件与环境冒烟测试）。
- **Quality Gate**：
  - `uv sync` 一键解析成功；`ruff check`、`black --check`、`pytest` 全绿通过。

---

## V1 LangChain Core

### Phase 3: Runnable Foundation（LCEL 核心原语与统一协议）

- **Goal**：实现基于 LCEL（LangChain Expression Language）的最小调用链路，掌握 Runnable 核心原语与操作符。
- **Deliverables**：
  - `llm/client.py`：标准 ChatModel 适配器封装（基于 `langchain_openai` 或通用兼容层）。
  - `runtime/runnable_demo.py`：管道符（`|`）、`RunnableLambda`、`RunnableParallel` 与 `RunnablePassthrough` 组合范式。
  - `tests/test_runnable.py`：验证 `invoke()`、`batch()` 与异步调用的单元测试。
- **Learning Focus**：
  - 深入剖析 `Runnable` 协议：为什么一切皆可流式化与批处理？
  - LCEL 管道操作符重载背后的数据契约。
- **Jarvis 对照**：
  - 对标 Jarvis 中的 `Planner.plan()`、`Executor.execute()` 原生函数串联调用。
- **Expected Git Diff**：
  - 约 200~300 行核心代码及单测。
- **Quality Gate**：
  - 链路无阻塞打通；支持 invoke 与 batch 行为；单元测试覆盖率 100%。

---

### Phase 4: Prompt Engineering（结构化与强类型提示词工程）

- **Goal**：将原 Jarvis 中的字符串模板升级为 LangChain 的结构化强类型 `ChatPromptTemplate` 体系。
- **Deliverables**：
  - `prompts/templates.py`：系统提示词、多轮对话角色模板、部分格式化（Partial Formatter）。
  - `prompts/parser.py`：基于 `StrOutputParser` 与 `PydanticOutputParser` 的输出解析管道。
  - `tests/test_prompts.py`：Prompt 变量校验、类型容错与解析测试。
- **Learning Focus**：
  - 为什么 PromptTemplate 比字符串拼接更具工程防御性？
  - LangChain 如何在 Prompt 阶段处理角色定义（System, Human, AI）及多模态占位符。
- **Jarvis 对照**：
  - 对标 Jarvis 中基于 `jinja2` 或 f-string 的原生 Prompt 格式化与手写正则 JSON 抽取器。
- **Expected Git Diff**：
  - 约 200~350 行。
- **Quality Gate**：
  - 强校验必填参数；输出结果被 Pydantic 模型精确验证反序列化；测试覆盖异常边界。

---

### Phase 5: Tool Calling（标准化工具绑定与调用闭环）

- **Goal**：利用 LangChain 标准 Tool 抽象（`@tool` / `BaseTool`）取代自研 ToolRegistry，实现模型层原生工具绑定与执行。
- **Deliverables**：
  - `tools/calculator.py`、`tools/search.py`：标准化 Tool 定义及参数 Schema 声明。
  - `runtime/tool_caller.py`：模型 `bind_tools` 管道与 ToolNode / 工具执行器对接。
  - `tests/test_tools.py`：工具 Schema 提取、模型 ToolCall 生成与执行回传测试。
- **Learning Focus**：
  - 为什么 Tool 不需要自己写 Registry？Pydantic 是如何被自动转换为 OpenAI Function Calling JSON Schema 的？
  - `ToolMessage` 在多轮调用协议中的生命周期。
- **Jarvis 对照**：
  - 对标 Jarvis 自研的 `ToolRegistry.register()`、参数反射提取与手动解析模型 JSON 工具参数。
- **Expected Git Diff**：
  - 约 250~400 行。
- **Quality Gate**：
  - 工具 Schema 准确注入；模型能够触发 ToolCalls；工具执行返回值规范包装为 `ToolMessage`。

---

## V2 Agent Capability

### Phase 6: Streaming（端到端双工与流式生成）

- **Goal**：掌握 LangChain 的 `stream`、`astream` 与 `astream_events` 体系，实现低延迟流式输出。
- **Deliverables**：
  - `runtime/streaming.py`：流式适配管道，支持中间 Thought、Tool 调用事件与最终 Answer 的分流处理。
  - `app/cli.py`：基于 Typer 的终端打字机流式交互命令。
  - `tests/test_streaming.py`：流式 Chunk 聚合与事件序列测试。
- **Learning Focus**：
  - LCEL 如何在整个管道中天然保持流式透明传递？
  - Token 级流与结构化事件流（Event Stream）的差异与场景。
- **Jarvis 对照**：
  - 对标 Jarvis 原生基于 `requests(stream=True)` 或 SSE 解析实现的自定义回调发生器。
- **Expected Git Diff**：
  - 约 250~450 行。
- **Quality Gate**：
  - 首字延迟（TTFT）处于最佳水平；Tool 调用与文本输出事件无错乱丢包。

---

### Phase 7: Memory（状态外置与会话历史注入）

- **Goal**：摒弃有状态的全局对象，采用 LangChain 推荐的 `RunnableWithMessageHistory` 实现外置化多会话管理。
- **Deliverables**：
  - `memory/history.py`：基于内存及轻量存储（如 SQLite/文件）的 `BaseChatMessageHistory` 实现。
  - `runtime/stateful_chain.py`：挂载会话历史的带状态 Runnable 链。
  - `tests/test_memory.py`：验证不同 `session_id` 状态隔离、历史滑动窗口与会话截断。
- **Learning Focus**：
  - LangChain 新旧 Memory 机制更迭：为什么废弃旧版 `ConversationChain`，全面转向 `RunnableWithMessageHistory`？
  - 纯函数式状态管理与上下文注入哲学。
- **Jarvis 对照**：
  - 对标 Jarvis 中在 Agent 实例中维护私有列表 `self.chat_history` 的状态管理模式。
- **Expected Git Diff**：
  - 约 250~400 行。
- **Quality Gate**：
  - 严格按 `session_id` 实现数据完全隔离；历史消息长度超限时具备安全的截断机制。

---

### Phase 8: Mini Agent（LCEL 驱动的 ReAct 闭环智能体）

- **Goal**：融汇前序所有模块，以纯 LCEL 方式组装一个具备 Reasoning + Action 循环能力的最小闭环 Agent。
- **Deliverables**：
  - `runtime/mini_agent.py`：Agent 决策主循环、终止条件判断与工具执行回传总装。
  - `app/main.py`：完整 CLI 入口，支持交互式多轮对话、流式展示与工具观测。
  - `tests/test_mini_agent.py`：端到端集成测试，覆盖单工具调用、多步推理及循环防死锁（Max Iterations）。
- **Learning Focus**：
  - 在不依赖 LangGraph 复杂状态机的前提下，使用标准 LangChain 原语实现 Agent 核心循环。
  - 明确 LCEL 单智能体的能力边界与引入 LangGraph 的真正拐点。
- **Jarvis 对照**：
  - 完整对标 Jarvis Agent 自研主调度循环（`JarvisRuntime.run_loop()`）。
- **Expected Git Diff**：
  - 约 350~500 行。
- **Quality Gate**：
  - 完整走通“提问 → 思考 → 调工具 → 接收结果 → 总结回答”闭环；具备最大迭代深度熔断保护；端到端测试 100% 通过。
