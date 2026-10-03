# ADR-002: 为什么将 Runnable 确立为第一攻坚目标

## 状态
已接受（Accepted）

## 日期
2026-09-24（更新于 2026-10-03，项目更名为 AgentFlow）

---

## 背景 (Context)

在早期的 LangChain（0.1 之前版本）中，系统充斥着大量黑盒式的 Legacy Chains（如 `LLMChain`、`ConversationalRetrievalChain` 等）。这些旧版 Chain 存在显著缺陷：
1. **黑盒化严重**：难以定制中间提示词逻辑或插入自定义校验；
2. **接口不统一**：有的用 `run()`，有的用 `call()`，流式与异步支持碎片化；
3. **难以组合与观测**：无法像 Unix 管道一样直观地串联与调试。

为了解决这一问题，LangChain 推出了 **LCEL（LangChain Expression Language）**，并将 **Runnable** 确立为整个框架唯一的一等公民（First-class Citizen）。

在 AgentFlow 的底层设计中，必须确立清晰的核心计算契约，而不是依靠命令式胶水代码把各模块拼凑在一起。

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
1. **消除胶水代码**：无论是 Prompt 渲染、模型调用还是输出解析，均以统一管道契约组合；
2. **天然获得多维运行能力**：开发者只需编写一套逻辑，免去了单独编写异步（Async）、批量（Batch）与流式（Stream）接口的工作量；
3. **解耦业务与生命周期**：所有 Runnable 节点天然支持 `config` 透传与生命周期回调，方便集成可观测性。

### 负向影响与代价 (Negative / Trade-offs)
1. **思维模式转换门槛**：需要从面向对象命令式编程转向声明式函数式组合；
2. **异常调用栈较深**：LCEL 管道报错时调用栈相对较长，需要掌握针对 Runnable 的专用调试策略。

---

## 后续演进 (Future Evolution)

即使未来进入多智能体或状态图时代（如 LangGraph），节点与边仍然建立在 Runnable 协议之上。吃透 Runnable 协议是后续所有高级 AI 架构演进的最坚实底座。
