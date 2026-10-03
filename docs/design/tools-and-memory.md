# 工具体系与状态记忆设计（Tools & Memory Design）

> **设计定位**：标准化工具契约、安全求值沙箱、多层级会话隔离与持久化记忆架构。  
> **代码依据**：[`tools/calculator.py`](file:///d:/myProject/AgentFlow/tools/calculator.py), [`tools/system.py`](file:///d:/myProject/AgentFlow/tools/system.py), [`runtime/tool_caller.py`](file:///d:/myProject/AgentFlow/runtime/tool_caller.py), [`memory/history.py`](file:///d:/myProject/AgentFlow/memory/history.py)

---

## 1. 工具体系（Tool System Architecture）

AgentFlow 遵循“强类型参数契约 + 隔离安全执行 + 结构化错误回传”的设计原则。

```mermaid
flowchart LR
    LLM[ChatModel with bind_tools] -->|ToolCall JSON| Dispatcher[runtime.tool_caller.execute_tool_calls]
    
    subgraph ToolRegistry [Registered Tools]
        Calc[calculator: 安全 AST 解析]
        Sys[get_system_info: 平台探针]
    end

    Dispatcher -->|name 匹配| Calc
    Dispatcher -->|name 匹配| Sys
    Calc -->|返回值| Packager[包装为 ToolMessage]
    Sys -->|返回值| Packager
    Dispatcher -->|找不到工具 / 执行异常| ErrorPackager[包装为 status='error' ToolMessage]
    
    Packager --> ResultList[list[ToolMessage]]
    ErrorPackager --> ResultList
    ResultList -->|追加回上下文| AgentContext[Agent 上下文继续循环]
```

### 1.1 工具规范契约（Tool Contract）
所有工具必须使用 `@tool` 装饰器，并通过 Pydantic `BaseModel` 显式定义入参 Schema：
- **自描述能力**：字段必须带有明确的 `description`，框架将自动将其提取为符合 OpenAI Function Calling 标准的 JSON Schema；
- **确定性校验**：非法入参会在执行前被 Pydantic 直接拦截，不会传递给工具内部。

### 1.2 内置工具实现

#### 1. 安全数学计算器（`tools/calculator.py`）
- **安全沙箱**：严禁使用 Python 原生内置的 `eval()` 函数执行任意代码。
- **实现原理**：使用 Python 原生抽象语法树模块（`ast.parse`）将表达式解析为 AST 树，并通过白名单操作符字典（`SAFE_OPERATORS`）递归求值：
  ```python
  SAFE_OPERATORS = {
      ast.Add: operator.add, ast.Sub: operator.sub,
      ast.Mult: operator.mul, ast.Div: operator.truediv,
      ast.Mod: operator.mod, ast.Pow: operator.pow,
      ast.FloorDiv: operator.floordiv,
  }
  ```
- **异常拦截**：非法语法或除零异常被安全捕获，以错误字符串返回模型。

#### 2. 系统环境探针（`tools/system.py`）
- **功能**：基于 `platform` 标准库获取当前宿主机操作系统名称、版本号与 Python 运行时版本；
- **入参约束**：支持指定 `query_type` 为 `os`、`python` 或 `all`。

### 1.3 调度执行与异常隔离（`runtime/tool_caller.py`）
- **分发机制**：`execute_tool_calls(tool_calls, tool_map)` 根据模型返回的 `tool_name` 在 `tool_map` 中索引对应的 `BaseTool` 实例并调用 `tool.invoke(args)`；
- **错误降级**：
  - 若模型请求了未注册的工具名，生成 `status="error"` 的 `ToolMessage`；
  - 若工具运行时抛出未捕获异常，生成附带详细堆栈信息的 `ToolMessage`；
  - 核心 Runtime 进程永不崩溃，错误信息作为观察结果原样输入给模型进行重试。

---

## 2. 状态记忆体系（Memory & Session Architecture）

AgentFlow 严格遵守函数式无状态原则：**计算逻辑（LCEL Chain / Agent）与会话状态（Chat History）完全剥离**。

```mermaid
flowchart TD
    subgraph Stores [History Stores]
        MemStore[InMemoryHistoryStore\n内存多会话隔离]
        FileStore[FileHistoryStore\n.sessions/{session_id}.json 持久化]
    end

    subgraph Histories [History Implementations]
        WinHistory[WindowedChatMessageHistory\n滑动窗口消息队列]
        FileHistory[FileChatMessageHistory\nJSON 序列化读写]
    end

    MemStore -->|get_history(session_id)| WinHistory
    FileStore -->|get_history(session_id)| FileHistory

    subgraph WindowStrategy [Window & Truncation]
        TrimFunc[trim_chat_history / 截取最新 N 条消息]
    end

    WinHistory --> WindowStrategy
    FileHistory --> WindowStrategy
```

### 2.1 存储分层与抽象契约
所有记忆组件均实现 LangChain 标准的 `BaseChatMessageHistory` 抽象：
1. **`WindowedChatMessageHistory`**：
   - 纯内存消息队列，线程隔离；
   - 每次追加消息时自动触发 `_apply_window()`，保留最近 `max_messages` 条消息。
2. **`FileChatMessageHistory`**：
   - 本地 JSON 文件持久化，文件存储在 `.sessions/{session_id}.json`；
   - 使用 LangChain 官方标准的 `message_to_dict` 与 `messages_from_dict` 进行无损序列化，确保 `tool_calls`、`additional_kwargs` 与角色类型（Human, AI, System, Tool）完整复原；
   - 写入时执行窗口截断，杜绝磁盘存储与上下文无序膨胀。

### 2.2 会话隔离管理器（History Store）
- **`FileHistoryStore`**：管理文件级多会话。提供 `get_history(session_id)`、`clear_session(session_id)`、`list_sessions()` 与 `reset_all()` 方法；
- **`InMemoryHistoryStore`**：管理内存字典多会话，适用于测试或无盘容器环境。

### 2.3 会话与 Runtime 的组合方式
1. **在 MiniAgent 中使用**：
   `MiniAgent` 初始化时传入 `history_store=FileHistoryStore()`。每次调用 `stream_run(query, session_id="user_123")` 时动态加载前序历史，回答完毕后将提问与回答原子化追加至存储。
2. **在标准 LCEL 链中使用**：
   `runtime/stateful_chain.py` 封装了 `create_stateful_chain()`，通过 `RunnableWithMessageHistory` 为任意纯函数式 LCEL 管道赋能带状态的多轮会话能力。
