# AgentFlow 研发路线图（Roadmap）

> **项目定位**：从底层自研 Runtime 到工业级 LangChain LCEL 核心抽象的系统化演进工程。  
> **演进原则**：阶段目标明确、代码量受控、质量门禁严苛、代码与文档真实一致。

---

## 阶段执行状态概览

```text
V0 Foundation (工程与设计地基) ────────────────────────── [已完成 / Completed]
├── Phase 0: Design Gate (架构设计与映射门禁)           [✓]
├── Phase 1: Project Skeleton (工程目录骨架)             [✓]
└── Phase 2: Development Infrastructure (现代工具链)    [✓]

V1 LangChain Core (核心抽象迁移) ─────────────────────── [已完成 / Completed]
├── Phase 3: Runnable Foundation (LCEL 统一协议原语)     [✓]
├── Phase 4: Prompt Engineering (结构化与解析生态)       [✓]
└── Phase 5: Tool Calling (标准化工具绑定与调用闭环)     [✓]

V2 Agent Capability (运行时高阶能力) ─────────────────── [已完成 / Completed]
├── Phase 6: Streaming (端到端 Token 流与事件派发)       [✓]
├── Phase 7: Memory (状态外置与文件持久化会话隔离)       [✓]
└── Phase 8: Mini Agent (LCEL 驱动的 ReAct 闭环智能体)   [✓]

V3 StateGraph & Scaling (高阶图调度与多智能体) ───────── [规划中 / Planned]
├── Phase 9: LangGraph StateGraph (有向有环图状态机)     [ ]
├── Phase 10: Multi-Agent Collaboration (多智能体协作)  [ ]
├── Phase 11: RAG & Knowledge Retrieval (向量检索增强)   [ ]
├── Phase 12: MCP Ecosystem (Model Context Protocol 接入)[ ]
└── Phase 13: Service Gateway (FastAPI 服务化暴露)      [ ]
```

---

## 已交付阶段详情（Completed Deliverables）

### V0 Foundation（基础地基）

#### Phase 0: Design Gate（架构设计与映射门禁）[✓ 完成]
- **交付内容**：完成全套顶层架构设计、自研机制与框架机制映射分析表（Migration Map）与核心 ADR。
- **产出文档**：`docs/architecture/`、`docs/design/`、`docs/adr/`。

#### Phase 1: Project Skeleton（工程目录骨架）[✓ 完成]
- **交付内容**：构建符合现代化 Python 规范的模块化分层目录：`app/`, `llm/`, `prompts/`, `tools/`, `runtime/`, `memory/`, `tests/`。
- **核心约束**：建立严格的单向依赖拓扑，杜绝循环导入。

#### Phase 2: Development Infrastructure（现代化工具链）[✓ 完成]
- **交付内容**：配置以 `uv` 为核心的现代 Python 工具链，集成 `Ruff`、`Black`、`pytest`、`Typer`、`httpx` 与 `python-dotenv`。
- **验证结果**：建立基线冒烟测试 `tests/test_infra.py` 并通过。

---

### V1 LangChain Core（核心抽象）

#### Phase 3: Runnable Foundation（LCEL 核心原语）[✓ 完成]
- **交付模块**：`llm/client.py`, `runtime/runnables.py`, `tests/test_runnable.py`。
- **交付能力**：实现 ChatOpenAI 统一适配器；提供 `compose_sequence`、`compose_parallel`、`make_lambda`、`assign_context`；验证 LCEL 的 `invoke` 与 `batch` 标准协议。

#### Phase 4: Prompt Engineering（结构化提示词工程）[✓ 完成]
- **交付模块**：`prompts/templates.py`, `prompts/parser.py`, `tests/test_prompts.py`。
- **交付能力**：基于 `ChatPromptTemplate` 与 `MessagesPlaceholder` 封装提示词工厂；集成 `StrOutputParser`、`JsonOutputParser` 与 `PydanticOutputParser` 强类型反序列化校验。

#### Phase 5: Tool Calling（标准化工具绑定与闭环）[✓ 完成]
- **交付模块**：`tools/calculator.py`, `tools/system.py`, `runtime/tool_caller.py`, `tests/test_tools.py`。
- **交付能力**：基于 `@tool` 与 Pydantic Schema 定义安全 AST 计算器与系统信息探针；实现 `bind_model_tools()` 与 `execute_tool_calls()` 批量执行与 `ToolMessage` 容错包装。

---

### V2 Agent Capability（运行时高阶能力）

#### Phase 6: Streaming（端到端流式响应）[✓ 完成]
- **交付模块**：`runtime/streaming.py`, `app/renderer.py`, `tests/test_streaming.py`, `tests/test_renderer.py`。
- **交付能力**：实现 `stream_text` 文本块流与 `astream_pipeline_events`（`astream_events` v2）；实现基于 Rich 的 `StepRenderer` 低延迟打字机流式渲染。

#### Phase 7: Memory（状态外置与持久化历史）[✓ 完成]
- **交付模块**：`memory/history.py`, `runtime/stateful_chain.py`, `tests/test_memory.py`。
- **交付能力**：实现 `WindowedChatMessageHistory`（内存滑动窗口）与 `FileChatMessageHistory` / `FileHistoryStore`（本地 `.sessions/{session_id}.json` JSON 持久化）；实现 `create_stateful_chain` 赋能任意 LCEL 管道带状态会话能力。

#### Phase 8: Mini Agent（ReAct 闭环智能体）[✓ 完成]
- **交付模块**：`runtime/mini_agent.py`, `app/cli.py`, `app/main.py`, `tests/test_mini_agent.py`。
- **交付能力**：以纯 LCEL 方式组装完整的 Reasoning + Action 决策循环；支持 DeepSeek `reasoning_content` 及前置 Thought 思考提取；实现动态自适应流式缓冲算法；实现最大迭代步数防死锁熔断；交付完整 CLI 入口（`ask`, `chat`, `tools`）。
- **质量门禁**：全量 43 项自动化单元/集成测试 100% 通过。

---

## 未来演进路线（Future Roadmap / Planned）

### V3 StateGraph & Advanced Orchestration（图状态机与高级编排）

#### Phase 9: LangGraph StateGraph 集成
- **目标**：在彻底吃透 LCEL 原语的基础上，正式引入 `langgraph` 状态机。
- **核心特性**：
  - 基于有向有环图（DAG）实现更灵活的分支回溯与条件跳转；
  - 引入持久化 Checkpointers 实现跨节点断点恢复；
  - 引入人机交互中断机制（Human-in-the-loop / Tool Approval）。

#### Phase 10: Multi-Agent Collaboration（多智能体协作网络）
- **目标**：从单智能体升级为专业分工的多智能体协作系统。
- **核心特性**：
  - Supervisor 路由模式与网络对等协作模式（Swarm）；
  - 智能体间结构化消息传递与共享状态管理。

#### Phase 11: RAG & Knowledge Retrieval（知识检索增强）
- **目标**：为 Agent 注入外部领域知识库能力。
- **核心特性**：
  - 基于 LangChain 标准 Document Loaders 与 Text Splitters 进行文档解析与分块；
  - 接入向量数据库（如 Chroma / Qdrant）与 Embedding 适配器；
  - 实现基于 Retriever 的上下文检索与语义重排（Rerank）。

#### Phase 12: Model Context Protocol (MCP) 集成
- **目标**：支持业界通用的 MCP 开放标准。
- **核心特性**：
  - 编写 MCP Client 动态连接外部 MCP Server；
  - 自动化发现远程工具并动态绑定至 Agent 运行时。

#### Phase 13: Service Gateway（API 服务化）
- **目标**：提供生产级网络服务接口。
- **核心特性**：
  - 基于 FastAPI 构建标准化 RESTful API 与 SSE（Server-Sent Events）流式推送端点；
  - 统一认证、Rate Limiting 与分布式日志追踪。
