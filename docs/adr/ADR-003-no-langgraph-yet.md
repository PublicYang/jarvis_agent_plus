# ADR-003: 为什么暂不引入 LangGraph，将其延后至后续项目

## 状态
已接受（Accepted）

## 日期
2026-09-24

---

## 背景 (Context)

在现代 LangChain 生态中，**LangGraph** 已经成为构建具备复杂循环、多分支路由、持久化状态机和多智能体协同（Multi-Agent）的官方首选方案。许多开发者在学习 LangChain 时，往往急于直接上手 LangGraph，或者试图在一个项目中将 LangChain Core、LCEL 与 LangGraph 混为一谈。

然而，在软件工程学习与架构重构中，这种做法存在显著的认知风险与陷阱：
1. **抽象层次混淆**：LangGraph 是建立在 LangChain Core（Runnable, Messages, Tools）基础之上的高阶图调度引擎。在未彻底吃透底层 Runnable 数据契约、Tool 绑定机制与流式协议之前直接进入 LangGraph，会导致“只知图节点连线，不知底层数据如何流动流转”。
2. **学习目标不聚焦**：本项目（Jarvis Agent Plus）的核心目标是对标自研 Jarvis Agent 的基础 Runtime，搞清楚框架在单智能体（Single-Agent）维度上是如何进行原子抽象的。若同时引入状态图（StateGraph）、检查点持久化（Checkpointers）以及多 Agent 通信协议，会导致项目范围失控。

---

## 决策 (Decision)

我们明确决策：**在 Jarvis Agent Plus 项目中，严禁引入 LangGraph 库及任何图状态机代码。LangGraph 将被严格限定在后续的演进项目（Jarvis Agent Pro）中展开**。

本项目的技术边界与范围约束如下：
- **本项目包含**：
  - 基于 LCEL 原语的链式编排；
  - 标准 Prompt、Tool Calling、Streaming、Memory；
  - 纯 LCEL + 轻量控制环实现的 Mini ReAct Agent。
- **本项目禁止**：
  - 导入 `langgraph` 依赖包；
  - 使用 StateGraph、End、START、CompiledGraph 等图原语；
  - 复杂多智能体协作与分支路由状态机。

---

## 影响 (Consequences)

### 正向影响 (Positive)
1. **认知负荷解耦**：团队和学习者能够心无旁骛地聚焦于 LCEL、Runnable 与标准 Tool 绑定的底层机制。
2. **阶段边界清晰**：每一个 Phase 代码量稳定受控（200~500行），交付节奏平稳可靠。
3. **架构演进路线平滑**：当未来在 Jarvis Agent Pro 中学习 LangGraph 时，能够清晰看出“为什么纯 LCEL 做复杂循环会捉襟见肘，从而必须引入状态图”，形成深度的技术洞察。

### 负向影响与代价 (Negative / Trade-offs)
1. **单智能体循环需轻度自持**：在 Phase 8（Mini Agent）中，我们需要自己维持一个极简的 ReAct 循环调度结构，而不能直接调用 LangGraph 现成的预制 Agent 图。
2. **多分支复杂状态受限**：本项目无法直接展示复杂的分支回溯、人机交互中断（Human-in-the-loop）等图特性。

---

## 未来可能变化 (Future Evolution)

在顺利通过 Phase 8 验收并彻底吃透 LangChain 单智能体核心抽象后，我们将启动 **Jarvis Agent Pro**，全面基于 LangGraph 探索图状态机、持久化断点恢复与多智能体协同架构。
