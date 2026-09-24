# Jarvis Agent → LangChain 全量迁移映射手册（Migration Map）

> **文档性质**：Jarvis Agent Plus 的核心认知与工程基石。  
> **核心使命**：逐项对比自研 Agent Runtime 底层实现与 LangChain 框架抽象，揭示“框架如何提炼通用设计”、“省去了哪些冗余代码”，以及“保留了哪些关键控制权”。

---

## 迁移概览大地图

```text
┌─────────────────────────┐                     ┌─────────────────────────┐
│       Jarvis Agent      │                     │    Jarvis Agent Plus    │
│      (自研机制实现)       │                     │    (LangChain 框架抽象)   │
├─────────────────────────┤                     ├─────────────────────────┤
│ 1. 自定义 Message 结构   ├────────────────────►│ BaseMessage 强类型体系   │
│ 2. 原生 f-string 模板    ├────────────────────►│ ChatPromptTemplate 抽象 │
│ 3. 命令模式 Planner     ├────────────────────►│ Runnable 协议与 LCEL 管道 │
│ 4. 自研 ToolRegistry    ├────────────────────►│ BaseTool 与 bind_tools   │
│ 5. 正则手写 Parser      ├────────────────────►│ OutputParser 验证生态    │
│ 6. 实例私有 history 数组 ├────────────────────►│ RunnableWithMessageHistory│
│ 7. 底层 SSE 流式生成器   ├────────────────────►│ 原生 stream / astream 契约│
│ 8. 原生 While 调度循环   ├────────────────────►│ Agent Runtime 控制环      │
│ 9. 全局上下文/字典传递   ├────────────────────►│ RunnableConfig 统一元数据 │
└─────────────────────────┘                     └─────────────────────────┘
```

---

## 1. 消息契约：Jarvis Message → LangChain Message

### Jarvis 如何实现
- **实现方式**：自定义字典 `{"role": "user", "content": "..."}` 或原生 Dataclass。
- **痛点与局限**：
  - 各大模型 API（OpenAI, Anthropic, Gemini）对 Role 字段的定义并不统一（例如 Function call 与 Tool call 协议差异、tool_call_id 的存放位置不同）。
  - 需要在每次发起 HTTP 请求前，手写映射函数将内部 Message 格式序列化为目标模型的特定 Payload。
  - 多模态数据（图片、音频）或工具调用元数据（`tool_calls`）缺乏统一结构，极易在传递中被篡改或丢失类型支持。

### LangChain 如何实现
- **实现方式**：继承自 `BaseMessage` 的强类型对象：
  - `HumanMessage`：用户输入；
  - `AIMessage`：模型响应（内含 `tool_calls: list[ToolCall]` 结构化字段）；
  - `SystemMessage`：系统行为约束；
  - `ToolMessage`：工具执行返回结果（绑定必须的 `tool_call_id`）；
  - `ChatMessage`：支持任意自定义 Role 的兜底类型。
- **调用范式**：
  ```python
  from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
  messages = [
      SystemMessage(content="You are a senior engineer."),
      HumanMessage(content="Calculate 2 + 2"),
  ]
  ```

### 框架帮我们解决了什么
1. **多模型协议归一化**：不同厂商的消息协议在框架层被平滑抹平，上层业务无需关心具体厂商的底层 JSON 字段命名。
2. **工具调用链标准追踪**：`ToolMessage` 与 `AIMessage.tool_calls` 的关联由框架严格保障，防止漏传 `tool_call_id` 导致的 API 400 校验错误。
3. **内置多模态与元数据**：原生支持 `additional_kwargs`、`response_metadata` 以及结构化 Content（如文本+图片 URL 混合列表）。

---

## 2. 提示词工程：Jarvis Prompt → ChatPromptTemplate

### Jarvis 如何实现
- **实现方式**：原生 Python f-string 或轻量级 `jinja2` 模板渲染。
- **痛点与局限**：
  - 纯字符串在拼接多轮消息时极易产生空行、格式污染以及 Role 注入漏洞（Prompt Injection）。
  - 无法天然处理“多轮对话历史列表”这一变量类型——通常需要开发者自己手写循环把历史数组拼接成纯文本，或者写专有解析器转换。
  - 缺乏“部分变量预填充（Partial）”与入参强类型防御。

### LangChain 如何实现
- **实现方式**：`ChatPromptTemplate` 及其配合的 `MessagesPlaceholder`。
- **调用范式**：
  ```python
  from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

  prompt = ChatPromptTemplate.from_messages([
      ("system", "You are an assistant. Current date: {current_date}."),
      MessagesPlaceholder(variable_name="chat_history"),
      ("human", "{input}"),
  ])
  # 支持部分填充
  partial_prompt = prompt.partial(current_date="2026-09-24")
  ```

### 框架帮我们解决了什么
1. **消息序列结构化渲染**：变量直接映射为标准 Message 对象，不再有字符串到消息对象的二次脆弱解析。
2. **历史记录无缝占位符**：`MessagesPlaceholder` 能够将 `list[BaseMessage]` 原生嵌入在任意指定位置，无需开发者手写展平逻辑。
3. **工程化变量校验**：自动校验模板中所声明的入参变量（`input_variables`），缺失变量时直接在客户端抛出明确异常，防止将未解析的 `{var}` 裸发给模型造成浪费与幻觉。

---

## 3. 核心计算与流程编排：Jarvis Planner → Runnable (LCEL)

### Jarvis 如何实现
- **实现方式**：自定义 `Planner` 类，内部显式编写串行命令：
  ```python
  class Planner:
      def plan_and_execute(self, user_query):
          prompt = self.build_prompt(user_query)
          raw_resp = self.llm.call(prompt)
          action = self.parser.parse(raw_resp)
          return action
  ```
- **痛点与局限**：
  - 无法无痛支持流式（Streaming）：如果要支持流式，必须自顶向下重构每一个方法的签名，将其全部改造为 Generator。
  - 无法天然支持批量化（Batching）与并发（Async）：每一个步骤都需要手动写 `asyncio.gather` 或线程池。
  - 缺乏标准管道操作符，逻辑复用性差，中间状态难以无侵入观测与拦截。

### LangChain 如何实现
- **实现方式**：LCEL 表达式（通过重载管道符 `|` 实现的 `RunnableSequence`），所有组件必须实现统一的 `Runnable` 协议接口：
  - 同步调用：`invoke(input, config=None)`
  - 异步调用：`ainvoke(input, config=None)`
  - 流式响应：`stream(input, config=None)`
  - 异步流式：`astream(input, config=None)`
  - 批量执行：`batch(inputs, config=None)`
- **调用范式**：
  ```python
  chain = prompt | llm | parser
  result = chain.invoke({"input": "Hello"})
  # 无需重写一行代码，天然支持流式：
  for chunk in chain.stream({"input": "Hello"}):
      print(chunk, end="")
  ```

### 框架帮我们解决了什么
1. **Unix 管道式标准化契约**：只要满足输入/输出类型契约，任何组件皆可随意自由串联（`RunnableLambda`, `RunnableParallel`, `RunnablePassthrough`）。
2. **能力升维完全免费**：编写一个同步管道，自动无缝获得异步、流式、批量与重试支持，彻底终结样板胶水代码。
3. **内置生命周期钩子（Callbacks）**：无需在每个函数内部打日志，框架在 Runnable 边界统一派发 start、end、error 事件，与观测工具天然集成。

---

## 4. 工具生态与注册调度：Jarvis ToolRegistry → BaseTool & bind_tools

### Jarvis 如何实现
- **实现方式**：单例 `ToolRegistry` 字典类，使用装饰器注册函数，通过 Python `inspect` 提取函数签名并手动组装成 OpenAI JSON Schema。
- **痛点与局限**：
  - 类型检查脆弱：原生 `inspect` 难以精准处理复杂的嵌套对象、Optional 字段与默认值校验。
  - 执行与分发需手动实现：模型返回 `tool_calls` 后，自研代码必须写一个大的 `switch/case` 或 `registry.get(name).call(**args)`，并且需要手动捕获每个工具的各种异常，包装错误并喂回模型。

### LangChain 如何实现
- **实现方式**：`@tool` 装饰器或继承 `BaseTool`，底层基于 Pydantic BaseModel 进行自动参数校验；模型层提供标准的 `bind_tools()` 方法。
- **调用范式**：
  ```python
  from langchain_core.tools import tool
  from pydantic import BaseModel, Field

  class CalcInput(BaseModel):
      expr: str = Field(description="Mathematical expression to evaluate")

  @tool("calculator", args_schema=CalcInput)
  def calculator(expr: str) -> str:
      """Evaluate a math expression."""
      return str(eval(expr))

  model_with_tools = llm.bind_tools([calculator])
  ```

### 框架帮我们解决了什么
1. **自动且工业级的 Schema 生成**：完全依赖 Pydantic 生态，对字段文档、可选值、默认值进行零成本标准化抽取，格式百分之百符合各大模型厂商要求。
2. **模型直接动态绑定**：模型与工具之间通过 `bind_tools` 一行绑定，无需通过提示词注入冗长的工具说明文本。
3. **原生错误拦截与容错**：`BaseTool` 内置 `handle_tool_error` 机制，工具异常不会导致整个 Agent 崩溃，而是作为观察结果安全返回给模型进行自我修复。

---

## 5. 结果结构化与解析：Jarvis Parser → OutputParser

### Jarvis 如何实现
- **实现方式**：开发者手写正则表达式提取 ````json ... ```` 代码块，然后调用 `json.loads`；或者写字符串切割逻辑提取特定的 Action 标签。
- **痛点与局限**：
  - 极其脆弱：大模型如果带有多余的思考解释、Markdown 反引号缺失、或者包含未转义字符时，自研解析代码直接抛异常。
  - 缺乏输出格式自我修复指示：当解析失败时，无法标准地生成“纠错提示词”让模型重试。

### LangChain 如何实现
- **实现方式**：标准 `BaseOutputParser` 体系：
  - `StrOutputParser`：无损提取文本字符串；
  - `JsonOutputParser`：流式友好的 JSON 提取器；
  - `PydanticOutputParser`：强制反序列化为 Pydantic 强类型模型；
  - 提供 `get_format_instructions()` 自动将目标结构转变为 System/Human Prompt 指令。
- **调用范式**：
  ```python
  from langchain_core.output_parsers import PydanticOutputParser
  from pydantic import BaseModel, Field

  class UserProfile(BaseModel):
      name: str
      age: int

  parser = PydanticOutputParser(pydantic_object=UserProfile)
  chain = prompt | llm | parser
  profile: UserProfile = chain.invoke({"query": "..."})
  ```

### 框架帮我们解决了什么
1. **类型安全端到端保障**：LLM 的无序非结构化文本输出，在管道终点被保证转化为类型安全的高级业务对象。
2. **流式 JSON 解析支持**：`JsonOutputParser` 能够在模型流式返回 JSON 片段时，动态构建并逐步产出 partial dict，实现真正的实时流式结构化输出。
3. **提示词指令自动生成**：自动根据 Pydantic 类结构生成完美的格式遵循 Prompt 指令。

---

## 6. 状态管理与会话记忆：Jarvis Memory → RunnableWithMessageHistory

### Jarvis 如何实现
- **实现方式**：在 `Agent` 类实例中声明私有变量 `self.history = []`，每轮对话结束时调用 `self.history.append(...)`。
- **痛点与局限**：
  - 严重的并发与多会话灾难：类实例变为有状态对象，无法在多线程、异步微服务或高并发 Web 环境中直接共享。
  - 存储硬编码：内存存储与外部数据库（Redis, Postgres）存储逻辑深度耦合在 Agent 类中，替换成本极高。

### LangChain 如何实现
- **实现方式**：将核心 LCEL Chain 保持为纯净的无状态函数，使用外置装饰器 `RunnableWithMessageHistory`，通过外部 `session_id` 动态挂载对应的 `BaseChatMessageHistory` 实现。
- **调用范式**：
  ```python
  from langchain_core.runnables.history import RunnableWithMessageHistory
  from langchain_community.chat_message_histories import ChatMessageHistory

  session_store = {}

  def get_history(session_id: str):
      if session_id not in session_store:
          session_store[session_id] = ChatMessageHistory()
      return session_store[session_id]

  with_history = RunnableWithMessageHistory(
      runnable=chain,
      get_session_history=get_history,
      input_messages_key="input",
      history_messages_key="chat_history",
  )

  # 会话间完全隔离
  res1 = with_history.invoke({"input": "I am Alice"}, config={"configurable": {"session_id": "user_1"}})
  res2 = with_history.invoke({"input": "What is my name?"}, config={"configurable": {"session_id": "user_2"}})
  ```

### 框架帮我们解决了什么
1. **函数式无状态解耦**：计算管道与状态存储完全剥离，Chain 成为线程安全的只读对象。
2. **多会话原生支持**：通过 `session_id` 配置驱动，天然支持多租户高并发场景。
3. **存储介质自由插拔**：上层逻辑完全面向 `BaseChatMessageHistory` 抽象编程，未来从内存一键切换到 Redis / SQL 无需改动核心 Agent 链代码。

---

## 7. 实时流式传输：Jarvis Stream → Runnable.stream / astream_events

### Jarvis 如何实现
- **实现方式**：底层手写基于 `requests.post(..., stream=True)` 或 `httpx.stream()` 的解析逻辑，手动判断 SSE 的 `data: ` 前缀并 `yield chunk`。
- **痛点与局限**：
  - 管道链路流式断裂：如果中间经过了解析器或格式化器，开发者必须为每个环节编写专用的生成器适配器，极易引起缓冲阻塞。
  - 中间状态无法观测：无法方便地区分输出到底是来自 Prompt 模板、LLM 思考、还是工具执行日志。

### LangChain 如何实现
- **实现方式**：Runnable 协议内置流式契约。提供高阶 `astream_events(version="v2")` API，发射细粒度的事件流（如 `on_chat_model_start`, `on_chat_model_stream`, `on_tool_start`, `on_tool_end`）。
- **调用范式**：
  ```python
  async for event in chain.astream_events({"input": "query"}, version="v2"):
      kind = event["event"]
      if kind == "on_chat_model_stream":
          content = event["data"]["chunk"].content
          print(content, end="", flush=True)
      elif kind == "on_tool_start":
          print(f"\n[Tool Executing: {event['name']}]")
  ```

### 框架帮我们解决了什么
1. **管道全链路流式穿透**：链上的所有标准节点自动保持流式传递，彻底告别单点缓冲卡死。
2. **结构化事件统一分发**：直接输出统一的事件信道，前端 UI 可以轻松实现思考过程折叠、工具执行指示器与打字机文本的解耦渲染。

---

## 8. 智能体主循环：Jarvis Loop → Agent Runtime (Mini-Agent)

### Jarvis 如何实现
- **实现方式**：手写 `while step < max_steps:` 循环，在循环体中手动判断 LLM 返回是否包含动作、调用工具、将结果拼接到列表、再发给 LLM。
- **痛点与局限**：
  - 业务逻辑与循环调度严重糅合：错误处理、Token 监控、超时熔断与核心推理逻辑全部挤在一个巨大而混乱的函数中。
  - 无法标准化复用不同的决策策略（如 ReAct、Plan-and-Solve）。

### LangChain 如何实现
- **实现方式**：在本项目（Jarvis Agent Plus）中，解耦为：
  - 决策单元：封装为纯粹的 LCEL Chain（Prompt + Tool-bound LLM + ToolCall Parser）；
  - 调度 Runtime：实现精简且健壮的控制环，专注于状态驱动、工具调用转发、异常隔离与最大迭代深度保护。
- **调用范式**：
  - 决策单步全走 LCEL 标准管道；
  - 外层循环维护执行边界与生命周期回调，为后续迁移至状态图（LangGraph）保留明确的切面。

### 框架帮我们解决了什么
1. **职责严格分离**：“如何思考并选定工具”（LCEL 决策链路）与“如何执行工具并维持循环”（Runtime 循环调度）完全解耦。
2. **模型绑定一致性**：模型无论换成哪家，工具调用的触发与回传协议完全统一。

---

## 9. 上下文与元数据传递：Jarvis Context → RunnableConfig

### Jarvis 如何实现
- **实现方式**：在函数传参中层层穿透显式传递 `context: dict`，或者借助全局变量（Global State）/ 线程局部变量（ThreadLocal）。
- **痛点与局限**：
  - 接口污染严重：底层任何一个深层函数想拿一个追踪 ID（trace_id）或用户身份（user_id），上层每一个调用者都必须在签名里增加参数。
  - 异步并发环境下容易产生上下文错乱与脏读。

### LangChain 如何实现
- **实现方式**：所有 `invoke` / `stream` / `batch` 方法自带的统一参数 `config: RunnableConfig`，支持：
  - `tags: list[str]`：追踪标记；
  - `metadata: dict[str, Any]`：业务元数据；
  - `callbacks: Callbacks`：回调处理器；
  - `configurable: dict[str, Any]`：运行时动态配置（如动态替换模型温度、动态切换 session_id 等）。
- **调用范式**：
  ```python
  config = {
      "configurable": {"session_id": "user_42", "model": "gpt-4o"},
      "tags": ["production", "vip-user"],
      "metadata": {"trace_id": "req-98765"},
  }
  chain.invoke({"input": "Hello"}, config=config)
  ```

### 框架帮我们解决了什么
1. **隐式且安全的上下文字段透传**：Runnable 内部自动沿着调用栈向下传递 Config，无需逐层污染业务函数签名。
2. **运行时动态行为重写**：能够无需重新构建 Chain 即可动态切换提示词策略或底层模型参数。

---

## 总结：框架为我们减负与我们的自主掌控边界

| 框架帮我们彻底消解的（Don't Re-invent） | 我们依然需要自主把控的（Architect Ownership） |
| :--- | :--- |
| 跨厂商 LLM API 协议与 HTTP 通信细节 | 业务领域工具（Domain Tools）的语义划分与边界定义 |
| 统一流式（Stream）与批处理（Batch）底层协议转换 | 业务级循环熔断策略、防死循环逻辑与兜底策略 |
| Tool 的 JSON Schema 自动推导与绑定逻辑 | 核心业务提示词（System Prompt）的精准调优与工程防护 |
| 结构化输出解析与格式容错 | 会话持久化存储后端的容量规划与安全隔离 |
| 生命周期回调追踪（Callbacks）标准接口 | 业务层交互体验与最终客户端（CLI/Web）架构设计 |
