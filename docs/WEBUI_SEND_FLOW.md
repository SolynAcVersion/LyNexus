# WebUI 发送消息流程文档

## 概述

本文档详细说明了用户在 webui 中点击"发送按钮"后，从前端到后端的完整 API 调用和函数执行流程。

---

## 完整流程图

```
用户点击发送按钮
    ↓
MessageInput 组件
    ↓
ChatArea.handleSend
    ↓
useAppStore.sendMessage
    ↓
API Service (api.message.stream)
    ↓
后端 API (api_server.py)
    ↓
AI 处理 (aiclass.py)
    ↓
SSE 流式响应
    ↓
前端更新状态
    ↓
渲染消息气泡
```

---

## 详细步骤

### 1. 用户点击发送按钮

**文件**: `webui/src/components/chat/MessageInput.tsx:212-231`

```typescript
// 发送按钮点击处理
onClick={showStop ? onStop : () => {
  const trimmed = value.trim();
  if (trimmed) {
    onSend(trimmed);  // 调用传入的 onSend 回调
    clearInput();      // 清空输入框
    setAttachedFiles([]); // 清空附件
  }
}}
```

**触发条件**:
- 输入框有内容
- 当前没有正在进行的流式响应（`showStop` 为 false）

---

### 2. 事件传播到 ChatArea 组件

**文件**: `webui/src/components/sidebar/ChatArea.tsx:63-65`

```typescript
function handleSend(content: string) {
  sendMessage(content);  // 调用 store 的 sendMessage 方法
}
```

`MessageInput` 组件通过 prop 接收 `onSend` 回调，该回调实际上是 `ChatArea` 的 `handleSend` 函数。

---

### 3. Store 处理发送请求

**文件**: `webui/src/stores/useAppStore.ts:372-468`

#### 3.1 添加用户消息

```typescript
// 添加用户消息
const userMessage: Message = {
  id: `msg-${Date.now()}`,
  content,
  type: 'USER' as any,
  source: 'USER' as any,
  timestamp: new Date().toISOString(),
  conversationId: currentConversation.id,
};
addMessage(currentConversation.id, userMessage);
```

**作用**: 将用户消息立即添加到消息列表，用户可以在 UI 上看到自己发送的消息。

#### 3.2 设置处理状态

```typescript
setProcessingState(currentConversation.id, ProcessingState.STREAMING);
```

**作用**: 将当前对话状态设置为 `STREAMING`，这会触发 UI 显示停止按钮和加载动画。

#### 3.3 初始化流式消息

```typescript
const aiMessageId = `msg-${Date.now() + 1}`;
set((state) => ({
  streamingMessages: {
    ...state.streamingMessages,
    [currentConversation.id]: {
      id: aiMessageId,
      content: '',
      type: 'AI' as any,
      source: 'AI' as any,
      timestamp: new Date().toISOString(),
      conversationId: currentConversation.id,
      isStreaming: true,
    },
  },
}));
```

**作用**: 创建一个空的 AI 消息占位符，准备接收流式响应内容。

---

### 4. API 服务发起流式请求

**文件**: `webui/src/services/api.ts:254-334`

#### 4.1 函数签名

```typescript
async stream(
  conversationId: string,
  content: string,
  onChunk: (chunk: string) => void,          // 接收文本块
  onComplete: (message: Message) => void,    // 完成回调
  onError: (error: string) => void,          // 错误回调
  onCommandRequest?: (message: Message) => void,  // 命令请求回调
  onCommandResult?: (message: Message) => void    // 命令结果回调
): Promise<void>
```

#### 4.2 发起 SSE 请求

```typescript
const response = await fetch(
  `${API_BASE_URL}/conversations/${conversationId}/messages/stream`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }
);
```

**端点**: `POST /api/conversations/{conversationId}/messages/stream`

#### 4.3 处理 SSE 事件流

```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader!.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));

      // 根据事件类型分发
      if (event.type === 'chunk') {
        onChunk(event.content || '');
      } else if (event.type === 'complete') {
        onComplete(event.message);
      } else if (event.type === 'error') {
        onError(event.error || 'Unknown error');
      } else if (event.type === 'command_request') {
        onCommandRequest?.(event.message);
      } else if (event.type === 'command_result') {
        onCommandResult?.(event.message);
      }
    }
  }
}
```

**支持的事件类型**:
- `user_message`: 用户消息已确认
- `chunk`: 流式文本内容
- `command_request`: MCP 工具命令请求
- `command_result`: MCP 工具命令结果
- `complete`: 流式响应完成
- `error`: 错误发生

---

### 5. 后端处理请求

**文件**: `api_server.py:664-596`

#### 5.1 路由处理

```python
@app.post("/api/conversations/{conversation_id}/messages/stream")
async def stream_message(conversation_id: str, data: SendMessageModel):
    try:
        ai = get_ai_instance(conversation_id)
        if not ai:
            raise HTTPException(status_code=400, detail="AI not initialized")

        return EventSourceResponse(
            message_generator(ai, data.content, conversation_id),
            media_type="text/event-stream"
        )
```

**作用**: 创建 SSE 响应，使用 `message_generator` 生成器产生事件流。

---

### 6. 消息生成器

**文件**: `api_server.py:504-662`

#### 6.1 生成用户消息事件

```python
user_msg = {
    "id": f"msg-{int(datetime.now().timestamp() * 1000)}",
    "content": user_message,
    "type": "USER",
    "source": "USER",
    "timestamp": current_time,
    "conversationId": conversation_id,
    "isStreaming": False
}
yield {'data': json.dumps({'type': 'user_message', 'message': user_msg})}
```

#### 6.2 流式处理 AI 响应

```python
for chunk in ai.process_user_input_stream(user_message, conversation_history):
    if chunk:
        full_response += chunk
        yield {'data': json.dumps({'type': 'chunk', 'content': chunk, 'messageId': message_id})}
```

**作用**: 将 AI 返回的每个文本块作为 `chunk` 事件发送给前端。

#### 6.3 处理多个命令

```python
# 解析所有命令
lines = full_response.split('\n')
commands = []
for line in lines:
    line = line.strip()
    if line.startswith(command_start):
        commands.append(line)

# 如果有多个命令，每个命令作为单独的消息气泡
if len(commands) > 1:
    for i, command in enumerate(commands):
        # 发送 COMMAND_REQUEST 消息
        cmd_msg = {
            "id": f"msg-{...}",
            "content": command,
            "type": "COMMAND_REQUEST",
            "source": "AI",
            ...
        }
        yield {'data': json.dumps({'type': 'command_request', 'message': cmd_msg})}

        # 执行命令
        tokens = command.replace(command_start, "").strip().split(command_separator)
        func_name = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []
        result = ai.exec_func(func_name, *args)

        # 发送 COMMAND_RESULT 消息
        result_msg = {
            "id": f"msg-{...}",
            "content": result,
            "type": "COMMAND_RESULT",
            "source": "SYSTEM",
            ...
        }
        yield {'data': json.dumps({'type': 'command_result', 'message': result_msg})}
```

**作用**: 当 AI 返回多个命令时，每个命令都会作为单独的消息气泡显示。

#### 6.4 发送完成事件

```python
ai_msg = {
    "id": message_id,
    "content": full_response,
    "type": "AI",
    "source": "AI",
    "timestamp": datetime.now().isoformat(),
    "conversationId": conversation_id,
    "isStreaming": False
}
yield {'data': json.dumps({'type': 'complete', 'message': ai_msg})}
```

---

### 7. AI 处理核心

**文件**: `aiclass.py:1403-1701`

#### 7.1 流式处理入口

```python
def process_user_input_stream(self, user_input: str, conversation_history: List[Dict], callback=None):
    """流式处理用户输入"""
    history = conversation_history.copy()

    # 确保系统提示
    if not history or history[0].get("role") != "system":
        effective_prompt = self.get_effective_system_prompt()
        history.insert(0, {"role": "system", "content": effective_prompt})

    iteration = 0
    full_response = ""
```

#### 7.2 API 调用与流式响应

```python
while iteration < self.max_iterations:
    api_params = {
        "model": self.model,
        "temperature": self.temperature,
        "messages": history,
        "stream": True,  # 启用流式
        "max_tokens": self.max_tokens or 2048
    }

    response = self.client.chat.completions.create(**api_params)

    # 处理流式响应
    current_response = ""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            current_response += content
            full_response += content

            # 发送内容
            if callback:
                callback(content)
            else:
                yield content
```

**作用**: 调用 OpenAI API 的流式接口，将返回的每个文本块 yield 出去。

#### 7.3 命令检测与执行

```python
# 检查是否 AI 想要执行命令
if current_response.startswith(self.command_start):
    # 解析命令
    tokens = current_response.replace(self.command_start, "").strip().split(self.command_separator)
    tokens = [t.strip() for t in tokens]

    if len(tokens) >= 1:
        func_name = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []

        # 执行函数
        res = self.exec_func(func_name, *args)

    # 添加执行结果到历史
    history.append({
        "role": "user",
        "content": self.command_execution_prompt.format(result=res)
    })

    iteration += 1
    continue  # 继续下一个迭代
```

**作用**: 检测 AI 返回的命令，执行命令后将结果添加到对话历史，让 AI 继续处理。

---

### 8. 前端处理流式响应

#### 8.1 onChunk 回调

**文件**: `webui/src/stores/useAppStore.ts:429-431`

```typescript
(chunk) => {
  console.log('[Store] onChunk callback called with chunk:', chunk);
  updateStreamingMessage(chunk);
}
```

#### 8.2 更新流式消息

**文件**: `webui/src/stores/useAppStore.ts:201-220`

```typescript
updateStreamingMessage: (chunk: string) => {
  const { currentConversation, streamingMessages } = get();

  if (!currentConversation) return;

  const currentStreaming = streamingMessages[currentConversation.id];
  if (!currentStreaming) return;

  set((state) => ({
    streamingMessages: {
      ...state.streamingMessages,
      [currentConversation.id]: {
        ...currentStreaming,
        content: currentStreaming.content + chunk,
      },
    },
  }));
},
```

**作用**: 将新接收到的文本块追加到当前流式消息的内容中。

#### 8.3 onComplete 回调

**文件**: `webui/src/stores/useAppStore.ts:434-442`

```typescript
(message) => {
  finalizeStreamingMessage({
    ...message,
    id: aiMessageId,
    conversationId: currentConversation.id,
  });
  setProcessingState(currentConversation.id, ProcessingState.IDLE);
}
```

#### 8.4 完成流式消息

**文件**: `webui/src/stores/useAppStore.ts:225-239`

```typescript
finalizeStreamingMessage: (message: Message) => {
  const { currentConversation, addMessage } = get();

  if (!currentConversation) return;

  // 添加到正式消息列表
  addMessage(currentConversation.id, message);

  // 清除流式消息状态
  set((state) => {
    const { [currentConversation.id]: removed, ...remainingMessages } = state.streamingMessages;
    return {
      streamingMessages: remainingMessages,
    };
  });
},
```

**作用**: 将流式消息转移到正式消息列表，并清除流式状态。

---

### 9. UI 渲染更新

#### 9.1 消息列表渲染

**文件**: `webui/src/components/chat/MessageList.tsx:147-154`

```typescript
{messages.map((message) => (
  <MessageBubble key={message.id} message={message} />
))}

{/* 流式消息 */}
{streamingMessage && (
  <MessageBubble message={streamingMessage} isStreaming={true} />
)}
```

**作用**: 渲染所有历史消息和当前正在流式传输的消息。

#### 9.2 消息气泡组件

**文件**: `webui/src/components/chat/MessageBubble.tsx:220-225`

```typescript
{isStreaming ? (
  <p>{message.content}</p>  // 流式时直接显示纯文本
) : (
  <MarkdownRenderer content={message.content} />  // 完成后渲染 Markdown
)}

{/* 流式动画 */}
{isStreaming && (
  <span className="flex gap-1 ml-2">
    <span className="w-2 h-2 bg-current rounded-full animate-pulse" />
    <span className="w-2 h-2 bg-current rounded-full animate-pulse delay-75" />
    <span className="w-2 h-2 bg-current rounded-full animate-pulse delay-150" />
  </span>
)}
```

**作用**: 流式时显示纯文本和三个跳动的圆点动画，完成后渲染完整的 Markdown 格式。

---

## 关键数据结构

### Message 消息结构

```typescript
interface Message {
  id: string;                    // 消息唯一标识
  content: string;               // 消息内容
  type: MessageType;             // 消息类型：USER, AI, COMMAND_REQUEST, COMMAND_RESULT
  source: MessageSource;         // 消息来源：USER, AI, SYSTEM
  timestamp: string;             // ISO 8601 时间戳
  conversationId: string;        // 所属对话 ID
  isStreaming?: boolean;         // 是否正在流式传输
}
```

### SSE 事件格式

```typescript
// 文本块事件
{
  "type": "chunk",
  "content": "文本内容",
  "messageId": "msg-xxx"
}

// 完成事件
{
  "type": "complete",
  "message": { /* Message 对象 */ }
}

// 命令请求事件
{
  "type": "command_request",
  "message": { /* Message 对象 */ }
}

// 命令结果事件
{
  "type": "command_result",
  "message": { /* Message 对象 */ }
}
```

---

## 状态管理

### ProcessingState 状态流转

```
IDLE (初始状态)
    ↓
STREAMING (开始流式响应)
    ↓
IDLE (完成)
    ↓
EXECUTING_COMMAND (执行 MCP 工具)
    ↓
STREAMING (继续流式)
```

### streamingMessages 状态

```typescript
{
  [conversationId: string]: {
    id: string;
    content: string;
    type: MessageType;
    source: MessageSource;
    timestamp: string;
    conversationId: string;
    isStreaming: true;
  }
}
```

**作用**: 存储每个对话当前正在流式传输的消息。

---

## 错误处理

### 前端错误处理

**文件**: `webui/src/stores/useAppStore.ts:444-455`

```typescript
(error) => {
  console.error('[Store] onError callback called:', error);
  set((state) => {
    // 移除流式消息
    const { [currentConversation.id]: removed, ...remainingMessages } = state.streamingMessages;
    return {
      streamingMessages: remainingMessages,
    };
  });
  setProcessingState(currentConversation.id, ProcessingState.ERROR);
}
```

### 后端错误处理

**文件**: `api_server.py:660-662`

```python
except Exception as e:
    logger.error(f"Error in streaming: {e}")
    yield {'data': json.dumps({'type': 'error', 'error': str(e)})}
```

---

## 性能优化

1. **流式传输**: 使用 SSE 实现实时流式响应，用户无需等待完整响应
2. **状态缓存**: 使用 Zustand 进行轻量级状态管理
3. **虚拟滚动**: MessageList 支持长对话列表的虚拟滚动
4. **增量更新**: 只更新变化的消息内容，避免全量重渲染

---

## 相关文件清单

### 前端文件

| 文件路径 | 说明 |
|---------|------|
| `webui/src/components/chat/MessageInput.tsx` | 输入框和发送按钮组件 |
| `webui/src/components/sidebar/ChatArea.tsx` | 聊天区域容器 |
| `webui/src/components/chat/MessageList.tsx` | 消息列表 |
| `webui/src/components/chat/MessageBubble.tsx` | 消息气泡组件 |
| `webui/src/stores/useAppStore.ts` | 全局状态管理 |
| `webui/src/services/api.ts` | API 服务封装 |
| `webui/src/types/index.ts` | TypeScript 类型定义 |

### 后端文件

| 文件路径 | 说明 |
|---------|------|
| `api_server.py` | FastAPI 服务器和 SSE 端点 |
| `aiclass.py` | AI 处理核心逻辑 |
| `utils/config_manager.py` | 配置管理 |
| `utils/ai_history_manager.py` | 对话历史管理 |
| `utils/chat_data_manager.py` | 聊天数据管理 |

---

## 总结

整个流程的核心是使用 **Server-Sent Events (SSE)** 实现流式响应：

1. 用户点击发送后，前端立即显示用户消息
2. 同时创建一个空的 AI 消息占位符
3. 后端通过 SSE 不断推送文本块
4. 前端接收并追加到流式消息中
5. 完成后将流式消息转为正式消息

这种设计提供了流畅的用户体验，用户可以实时看到 AI 的回复过程，而不需要等待整个响应完成。
