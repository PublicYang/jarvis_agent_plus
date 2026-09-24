# Jarvis Agent Plus（LangChain Edition）

> **Jarvis Agent 的 LangChain Reference Migration 工程**  
> 目标：深入理解 LangChain 如何将自研 Agent Runtime 的核心能力抽象为工业级框架能力。

---

## 1. 项目定位

**Jarvis Agent Plus** 是自研 Agent 系统 **Jarvis Agent** 的官方对照迁移项目（Reference Migration）。

本项目**不是**使用 LangChain 简单重写 Jarvis Agent 的业务功能，而是建立起一套严格的认知演进路径：

```text
Jarvis Agent（自研底层 Runtime）
        │
        ▼
Jarvis Agent Plus（LangChain 框架抽象）
        │
        ▼
Jarvis Agent Pro（未来的复杂图调度 / Multi-Agent，待后续阶段）
```

通过重构与映射，彻底解构 LangChain 的设计哲学，明晰框架在工程化层面为开发者封装了什么、省掉了什么，以及哪些 Runtime 底层能力依旧需要架构师自主设计与掌控。

---

## 2. 学习目标

完成本项目后，能够从架构师与高级工程师的视角精准回答以下核心问题：

1. **为什么 Runnable 是 LangChain 的核心抽象？**
   - 理解 LCEL（LangChain Expression Language）与 Unix 管道思想的共通点；
   - 掌握 `invoke`、`batch`、`stream`、`ainvoke` 等统一协议的底层机制与组合优势。

2. **为什么 Tool 不需要自己维护 ToolRegistry？**
   - 理解 LangChain 如何统一 Schema 声明（Pydantic）、执行入口与绑定协议；
   - 探究 `@tool` 装饰器与 `BaseTool` 抽象对动态绑定（`bind_tools`）的支持。

3. **为什么 PromptTemplate 比纯字符串 Prompt 更适合工程化？**
   - 变量类型强约束、部分格式化（Partial Formatting）、多模态支持与 MessageRole 抽象对生产环境稳定性的意义。

4. **LangChain 帮我们省掉了哪些样板代码？**
   - 自动序列化/反序列化、统一流式推导、规范化异常包装、跨模型 API 适配器等。

5. **哪些 Runtime 能力依然需要自己实现？**
   - 复杂的 Agent 状态控制流、循环熔断防死循环、细粒度 Token 计费、跨会话恢复、业务级重试策略等。

---

## 3. 与 Jarvis Agent 的关系

| 维度 | Jarvis Agent（自研版） | Jarvis Agent Plus（本项目 / LangChain 版） |
| :--- | :--- | :--- |
| **设计核心** | 自研 Runtime 循环与原生调度 | LCEL (Runnable) 管道化组合与标准接口 |
| **代码量** | 包含大量底层协议通信与调度胶水代码 | 借助框架抽象消解样板代码，聚焦能力编排 |
| **Tool 管理** | 自定义 `ToolRegistry` 字典维护与分发 | 标准化 `BaseTool` 体系与模型原生 `bind_tools` |
| **Prompt** | 字符串模板与原生字典拼接 | `ChatPromptTemplate` 强类型消息化模板 |
| **状态/记忆** | 手动维护上下文截断与字典列表 | 标准 `BaseChatMessageHistory` 与链式挂载 |
| **角色** | 机制原理解构者 | 工业级框架对照者与能力验证者 |

---

## 4. 未来与 Jarvis Agent Pro 的关系

- **Jarvis Agent Plus**（本项目）：聚焦于 **Single-Agent & LCEL Core**。彻底吃透 Runnable 体系、Prompt、Tool Calling、Streaming、Memory 以及 Mini-Agent 基础闭环。明确坚守 **“本项目不引入 LangGraph”** 的架构红线。
- **Jarvis Agent Pro**（后续阶段）：在彻底掌握 LangChain 核心抽象的基础上，进一步引入 **LangGraph**，探索有向有环图（DAG / StateGraph）、多智能体协作（Multi-Agent Collaboration）、人机协同（Human-in-the-loop）、断点恢复与持久化 State 机制。

---

## 5. 项目路线图概览（9 阶段）

本项目遵循严格的软件工程规范，拆解为三个大版本、九个渐进式阶段：

- **V0 Foundation**
  - **Phase0 Design Gate**（当前）：完成架构蓝图、全量映射表与 ADR 决策文档。
  - **Phase1 Project Skeleton**：构建符合现代规范的空工程骨架与模块结构。
  - **Phase2 Development Infrastructure**：搭建工具链（uv, Ruff, Black, pytest, Typer, httpx）。
- **V1 LangChain Core**
  - **Phase3 Runnable Foundation**：实现基于 LCEL 的核心调用链（invoke / stream / batch）。
  - **Phase4 Prompt Engineering**：结构化消息模板与多参数动态渲染。
  - **Phase5 Tool Calling**：结构化工具绑定与模型 Tool Call 闭环。
- **V2 Agent Capability**
  - **Phase6 Streaming**：端到端 Token 级流式响应。
  - **Phase7 Memory**：基于会话 ID 的滑动窗口与持久化历史。
  - **Phase8 Mini Agent**：整合全流程的具备 ReAct 决策能力的紧凑 Agent。

---

## 6. 开发纪律与规则

- **一个 Phase 一个能力，一个 Phase 一个 Git Commit**。
- 每次实现代码量严格控制在 **200 ~ 500 行** 左右。
- 每个 Phase 必须同步更新文档、编写自动化测试并生成 Git Diff 总结。
- 严禁一次性生成整个项目，严禁提前引入 LangGraph，严禁使用 Legacy Chain API 或废弃接口。
