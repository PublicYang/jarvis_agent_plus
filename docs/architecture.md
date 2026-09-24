# Jarvis Agent Plus 架构设计说明书（Architecture）

> **系统定位**：基于 LangChain LCEL 核心原语构建的解耦型单智能体（Single-Agent）架构。  
> **核心原则**：纯函数式管道编排、分层解耦、统一协议抽象、无全局有状态对象。

---

## 1. 系统分层架构（Layered Architecture）

Jarvis Agent Plus 采用严格的单向依赖分层架构，自顶向下分为六层：

```text
┌────────────────────────────────────────────────────────┐
│                   Application Layer                    │
│   (CLI 终端交互 / Typer 入口 / 交互流式渲染 / 参数解析)   │
└───────────────────────────┬────────────────────────────┘
                            │ 调用
┌───────────────────────────▼────────────────────────────┐
│                LangChain Runtime Layer                 │
│ (Mini-Agent 循环控制 / 记忆挂载 / 流式事件调度 / 会话隔离)│
└───────────────────────────┬────────────────────────────┘
                            │ 编排
┌───────────────────────────▼────────────────────────────┐
│                    Runnable Layer                      │
│ (LCEL 管道组合 / RunnableParallel / Lambda / Parser)   │
└─────────────┬────────────────────────────┬─────────────┘
              │ 绑定                       │ 驱动
┌─────────────▼──────────────┐ ┌───────────▼─────────────┐
│        Tools Layer         │ │    LLM Adapter Layer    │
│ (BaseTool / @tool / Schema)│ │ (ChatOpenAI / 模型抽象) │
└─────────────┬──────────────┘ └───────────┬─────────────┘
              │ 依赖                       │ 依赖
┌─────────────▼────────────────────────────▼─────────────┐
│                 Infrastructure Layer                   │
│   (Python 3.12 / uv / httpx / 配置中心 / 日志观测)      │
└────────────────────────────────────────────────────────┘
```

### 各层职责规范

1. **Application Layer（应用接入层）**
   - **核心职责**：负责与最终用户或外部客户端对接。提供基于 Typer 的 CLI 交互界面、标准打字机流式字符渲染、用户输入预处理与异常提示。
   - **依赖约束**：仅依赖 Runtime Layer 暴露的标准化执行接口，严禁直接越级操作底层 LLM 或 Tools。

2. **LangChain Runtime Layer（智能体运行时层）**
   - **核心职责**：管理 Agent 的宏观执行循环（ReAct 循环）、最大迭代步数熔断控制（Max Iteration Protection）、跨轮会话 Memory 挂载（通过 `RunnableWithMessageHistory`）、流式事件分发。
   - **依赖约束**：依赖 Runnable 链式组合与外部工具集合。

3. **Runnable Layer（核心原语编排层）**
   - **核心职责**：基于 LCEL 构建纯函数式调用链。负责提示词渲染、参数动态穿透（`RunnablePassthrough`）、并行数据准备（`RunnableParallel`）、结果结构化解析（OutputParser）。
   - **依赖约束**：连接 LLM Adapter、Prompt 模板与解析器。

4. **Tools Layer（工具集成层）**
   - **核心职责**：定义 Agent 可调用的外部能力（如数学计算、外部 API 请求、知识检索）。统一使用 Pydantic 声明入参 Schema，利用 `@tool` 封装执行体。
   - **依赖约束**：独立无副作用（除工具本身功能外），向上提供标准化 Schema 和 `BaseTool` 实例。

5. **LLM Adapter Layer（大模型适配层）**
   - **核心职责**：屏蔽底层具体大模型厂商（OpenAI、DeepSeek、Claude 等）的通信协议差异。统一输出 LangChain 标准的 `BaseChatModel` 接口，暴露 `bind_tools` 能力。
   - **依赖约束**：依赖 Infrastructure 层的网络通信与环境变量配置。

6. **Infrastructure Layer（基础设施层）**
   - **核心职责**：提供运行环境与底层支撑。包含 Python 3.12 运行时、uv 依赖管理、httpx 异步网络客户端、环境变量加载、以及统一日志与错误处理。

---

## 2. 单次请求端到端数据流（Data Flow）

在最典型的非多轮工具调用场景下，从用户输入到获取最终回答的端到端数据流动如下：

```text
  User Input
      │
      ▼
┌──────────────────┐
│  PromptTemplate  │ ◄── 注入 System Prompt、历史上下文或变量
└─────────┬────────┘
          │ 生成标准 Messages 列表 (HumanMessage / SystemMessage)
          ▼
┌──────────────────┐
│     Runnable     │ ◄── 管道化前置处理 (参数映射、动态截断、日志追踪)
└─────────┬────────┘
          │ 格式化后的标准消息数据
          ▼
┌──────────────────┐
│   LLM Adapter    │ ◄── 统一调用 ChatModel，下发标准 API 请求
└─────────┬────────┘
          │ 接收模型原生响应 (AIMessage / ToolCalls)
          ▼
┌──────────────────┐
│   OutputParser   │ ◄── 提取文本内容 (StrOutputParser) 或强转结构化对象
└─────────┬────────┘
          │ 纯净的目标对象 / 字符串
          ▼
    Final Answer
```

### 多轮工具调用（ReAct 循环）的扩展数据流

当引入 Tool Calling 时，数据流在 LLM 返回后发生动态分支：

```text
User ──► PromptTemplate ──► LLM (bind_tools) ──► AIMessage
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             │                                               │
                      [有 Tool Calls]                                [无 Tool Calls: 最终回答]
                             │                                               │
                             ▼                                               ▼
                      Tool Executor                                    OutputParser
                      (执行指定 Tool)                                         │
                             │                                               ▼
                             ▼                                             Answer
                        ToolMessage
                             │
                             ▼
                   追加至上下文并重新进入循环 ──► LLM
```

---

## 3. Jarvis 对照表（Jarvis vs LangChain）

本表清晰阐明了自研系统组件在迁移到 LangChain 体系时的对应关系与抽象升级：

| 自研组件（Jarvis Agent） | 迁移对应（Jarvis Agent Plus） | 架构升级价值与本质变化 |
| :--- | :--- | :--- |
| **Jarvis Planner** | **Runnable / LCEL Chain** | 从手写命令模式/函数嵌套，转变为符合统一协议的 Unix 管道式声明式编排，天然获得批处理与流式能力。 |
| **Jarvis Message** | **LangChain BaseMessage** | 从自定义 Dict/Dataclass，升级为工业标准的 `HumanMessage`、`AIMessage`、`SystemMessage`、`ToolMessage` 强类型体系。 |
| **Jarvis ToolRegistry** | **`BaseTool` & `bind_tools`** | 废弃单例注册中心与字符串字典分发，直接基于 Pydantic 自动生成 Function Calling JSON Schema 并由模型原生绑定。 |
| **Jarvis Loop** | **Agent Runtime / Mini-Agent** | 明确循环调度边界。自研手写的 while 循环被解耦为外层轻量状态驱动与内部 LCEL 链式决策。 |
| **Jarvis Prompt** | **ChatPromptTemplate** | 从易碎的 f-string / 字符串拼接，升级为支持角色槽位、部分变量预填（Partial）的结构化消息模版。 |
| **Jarvis Parser** | **OutputParser (Str/Json/Pydantic)** | 从手写正则表达式抽取 markdown/json，升级为强类型验证器，支持自动重试与格式修复指令。 |
| **Jarvis Memory** | **RunnableWithMessageHistory** | 从 Agent 实例内部强绑定的私有列表 `self.history`，升级为无状态函数式外置持久化历史协议。 |
| **Jarvis Stream** | **Runnable.stream / astream_events** | 从底层手写迭代器/SSE 协议适配，升级为整条链路所有节点自动感知的端到端流式传递。 |

---

## 4. 架构设计原则与约束

1. **不可变与函数式组合**：LCEL Chain 应当是无状态的、纯净的转换函数，任何外部状态均应通过上下文变量显式传入。
2. **禁止循环依赖**：下游模块绝对不可反向引用上游模块（如 Tool 绝对不可导入 Runtime 或 Application）。
3. **强类型第一**：所有数据流动必须有 Pydantic 或标准 LangChain 消息对象做类型契约支撑，杜绝非受控任意字典传递。
4. **渐进式演化**：单智能体状态在本项目内通过精简的控制闭环实现，严禁提前引入 LangGraph 等重型状态机。
