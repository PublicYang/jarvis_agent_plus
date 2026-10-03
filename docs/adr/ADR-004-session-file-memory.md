# ADR-004: 为什么单智能体阶段采用本地 JSON 文件与滑动窗口会话记忆

## 状态
已接受（Accepted）

## 日期
2026-10-03

---

## 背景 (Context)

在构建 Agent 会话记忆体系时，常见的技术方案有：
1. **纯内存字典**：进程内 `dict[str, list[BaseMessage]]`，重启即丢；
2. **外部数据库存储**：集成 Redis、PostgreSQL 或 DynamoDB；
3. **本地文件持久化**：基于本地目录（如 `.sessions/{session_id}.json`）存储结构化消息。

在 AgentFlow 的单智能体与 CLI 终端交互场景中：
- 纯内存无法支持用户在两次运行 `uv run python -m app ask --session-id user1` 之间保持上下文连贯；
- 外部数据库（如 Redis/Postgres）会为本地开发和单测引入过重的基础设施依赖（需配置 Docker、端口、连接串），极大降低项目的易用性与新手上手速度；
- 无节制的消息累积会导致上下文迅速超出大模型上下文窗口，产生高昂 Token 成本或直接调用报错。

---

## 决策 (Decision)

我们决策：**在 AgentFlow 当前阶段，采用“本地 JSON 文件持久化（`FileHistoryStore`）+ 消息滑动窗口截断（`WindowedChatMessageHistory`）”作为默认会话记忆方案**。

核心规范：
1. **标准序列化契约**：使用 LangChain 官方 `message_to_dict` 与 `messages_from_dict` 进行持久化，完整保留 `tool_calls` 与消息 Role；
2. **基于 `session_id` 物理隔离**：每个会话独立存储于 `.sessions/{session_id}.json`，支持多会话独立读写与清理（`clear_session`）；
3. **强制滑动窗口截断**：默认限制每个会话保留最近 10 条消息（可通过 `--max-history` 配置），写入与读取时自动裁剪；
4. **面向标准接口编程**：统一继承自 LangChain `BaseChatMessageHistory`，业务代码完全面向抽象编程，保持向未来 Redis / 数据库后端无缝替换的能力。

---

## 影响 (Consequences)

### 正向影响 (Positive)
1. **零外部基础设施依赖**：克隆代码即可运行，无需依赖任何本地 Docker 或外部数据库服务；
2. **跨命令行运行持久性**：CLI 连续多次执行 `ask` 或进入 `chat` 时能够准确记住历史上下文；
3. **上下文安全性**：滑动窗口裁剪机制有效防止大模型上下文超限与 Token 浪费；
4. **易于调试**：存储文件为人类可读的标准 JSON 格式，方便开发者随时打开检查消息与工具调用链路。

### 负向影响与代价 (Negative / Trade-offs)
1. **多进程高并发文件锁限制**：本地文件 I/O 未实现复杂的分布式文件锁，不适于高并发生产集群部署；
2. **无全文或语义检索**：当前仅支持按时间序的滑动窗口，不支持跨会话历史的语义向量检索（待后续 RAG 阶段扩展）。

---

## 后续演进 (Future Evolution)

在后续服务化（FastAPI）或生产部署阶段，可在不修改 `MiniAgent` 或核心链代码的前提下，直接通过实现基于 Redis / SQL 的 `BaseChatMessageHistory` 插件完成后端存储平滑替换。
