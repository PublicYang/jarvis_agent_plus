# ADR-001: 为什么选择 LangChain LCEL 作为参考迁移标杆

## 状态
已接受（Accepted）

## 日期
2026-09-24（更新于 2026-10-03，项目更名为 AgentFlow）

---

## 背景 (Context)

在自研开发完成基础 Agent 后，我们掌握了 LLM 通信、手动 ToolRegistry 注册分发、自定义 Prompt 格式化以及手写 ReAct 调度循环等核心机制。然而，在面对工业级工程需求时，自研底层 Runtime 面临以下挑战：

1. **协议碎片化**：不同模型厂商（OpenAI、Anthropic、DeepSeek、本地 Ollama）的接口协议、流式格式（SSE）、工具调用参数格式各异，自研适配层维护成本居高不下；
2. **缺乏统一组合范式**：自研代码大多采用命令式、面向过程的函数嵌套，难以统一支持批处理（Batch）、流式输出（Streaming）与异步（Async）模式；
3. **行业标准对齐诉求**：在当前 AI 基础设施与 Agent 领域，LangChain 的 LCEL、Message 体系与 Tool Schema 定义已成为事实上的工业标准与开源通用语言。

为了从更高维度审视 Agent 架构，必须引入一个成熟、工业级的开源框架作为参考系（Reference Architecture），对比分析自研体系与成熟框架的得失。

---

## 决策 (Decision)

我们决定选择 **LangChain（以 LCEL Core 为核心）** 作为第一对照迁移与机制解构目标，启动 **AgentFlow** 项目。

重点学习并实践以下核心模块：
- **Runnable 抽象体系**：理解通用组件契约与管道化声明式组合；
- **ChatPromptTemplate & Messages**：学习工业级结构化消息模型；
- **BaseTool & bind_tools**：基于 Pydantic 的工业级 Schema 抽取与模型绑定；
- **OutputParser 生态**：掌握类型安全的数据反序列化；
- **RunnableWithMessageHistory**：体验无状态函数式链与状态外置隔离的最佳实践。

---

## 影响 (Consequences)

### 正向影响 (Positive)
1. **统一认知底座**：借助 LangChain 的抽象体系，建立现代 Agent 系统从 Prompt、LLM、Tool 到 Memory 的全局通用认知；
2. **大幅缩减样板代码**：省去手写 HTTP/SSE 解析、JSON Schema 反射、多模态协议适配等机械化劳动；
3. **强化工程设计素养**：深刻领会“为什么这样抽象”背后的设计权衡，为自主掌控核心 Runtime 提供坚实经验。

### 负向影响与代价 (Negative / Trade-offs)
1. **学习曲线存在一定陡峭度**：LCEL 采用了大量重载操作符（如 `|`）与元编程技术，初学者容易迷失在深层调用栈中；
2. **抽象泄露风险**：框架层的高度封装有时会隐藏底层模型请求的原生细节，排查复杂异常时需要深入源码理解。

---

## 后续演进 (Future Evolution)

在 AgentFlow 完成对 LangChain 核心原语的对照掌握后，我们将进一步针对复杂多智能体协作、循环状态图场景向 LangGraph 阶段演进。
