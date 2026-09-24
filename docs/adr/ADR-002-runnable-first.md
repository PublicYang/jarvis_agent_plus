# ADR-002: 为什么将 Runnable 确立为第一学习目标

## 状态
已接受（Accepted）

## 日期
2026-09-24

---

## 背景 (Context)

在早期的 LangChain（0.1 之前版本）中，系统充斥着大量黑盒式的 Legacy Chains（如 `LLMChain`、`ConversationalRetrievalChain`、`SimpleSequentialChain` 等）。这些旧版 Chain 存在显著缺陷：
1. **黑盒化严重**：难以定制中间提示词逻辑或插入自定义校验；
2. **接口不统一**：有的用 `run()`，有的用 `call()`，有的用 `apply()`，流式与异步支持碎片化；
3. **难以组合与观测**：无法像 Unix 管道一样直观地串联与调试。

为了解决这一问题，LangChain 团队重构推出了 **LCEL（LangChain Expression Language）**，并将 **Runnable** 确立为整个框架唯一的一等公民（First-class Citizen）。

在 Jarvis Agent 自研代码中，各种组件（Prompt 拼接器、LLM 客户端、正则解析器）本质上也是一个个“输入 A 输出 B”的计算步骤，但在自研版中这些步骤是通过分散的命令式逻辑粘合的，缺乏通用契约。

---

## 决策 (Decision)

我们决策：**在进入 Tool、Memory 与 Agent 业务逻辑之前，必须将 `Runnable` 协议与 LCEL 基础作为最核心的攻坚目标（Phase 3 重点学习）**。

必须彻底掌握 Runnable 的五大统一调用标准：
- `invoke`（同步单次执行）
- `ainvoke`（异步单次执行）
- `stream`（同步流式执行）
- `astream`（异步流式执行）
- `batch`（批量并发执行）

并掌握核心组合原语：
- 管道操作符 `|`（`RunnableSequence`）
- `RunnableLambda`（自定义纯函数包装）
- `RunnableParallel`（并行多分支合并）
- `RunnablePassthrough`（输入直通与动态注入）

---

## 影响 (Consequences)

### 正向影响 (Positive)
1. **降维打击传统面向对象胶水代码**：一旦掌握 Runnable，无论是 Prompt 渲染、模型调用还是输出解析，都可以像组合乐高积木一样优雅组装。
2. **天然获得多维运行能力**：开发者只需编写一套逻辑，自动免去了单独编写异步（Async）、批量（Batch）与流式（Stream）接口的巨大工作量。
3. **解耦业务与生命周期**：所有 Runnable 节点天然支持 `config` 透传与生命周期回调，大幅降低后续集成监控日志的侵入性。

### 负向影响与代价 (Negative / Trade-offs)
1. **思维模式转换门槛**：需要从面向对象命令式编程（Imperative Programming）转向声明式函数式组合（Declarative Composition）。
2. **调试方式改变**：管道组合在报错时，调用栈较深，需要掌握针对 Runnable 的专用调试策略（如调试回调、中间节点断点打印）。

---

## 未来可能变化 (Future Evolution)

随着未来进入多智能体或状态图时代（如 LangGraph），节点与边仍然建立在 Runnable 协议之上。彻底吃透 Runnable 将成为后续所有高级 AI 架构演进的最坚实底座。
