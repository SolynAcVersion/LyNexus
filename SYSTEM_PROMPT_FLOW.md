# System Prompt 数据流分析

## 用户按下"发送"键后的完整流程

### 1. UI 层 (chat_box.py)

```
_send_message()
  └─> _start_message_processing()
       └─> MessageProcessor.process_message()
            ├─> 获取 AI 实例
            ├─> 加载对话历史 (带 system_prompt)
            └─> 调用 AI 处理
```

### 2. System Prompt 获取流程

```
[chat_box.py:512]
system_prompt = getattr(ai_instance, 'system_prompt', None)
    ↓
[chat_box.py:513-516]
history = self.history_manager.load_history(
    conversation_name,
    system_prompt
)
    ↓
[ai_history_manager.py:60-71]
load_history(conversation_name, system_prompt)
    ↓
[ai_history_manager.py:73-98]
_ensure_system_prompt(loaded_history, system_prompt)
    ↓ 返回完整历史（第一条是 system prompt）
[
    {"role": "system", "content": system_prompt + history_usage_guidance},
    ...历史消息...
]
```

### 3. System Prompt 来源追踪

#### 3.1 AI 初始化时 (aiclass.py:232-237)

```python
if system_prompt:  # 从配置传入
    self.user_system_prompt = system_prompt
else:
    self.user_system_prompt = self.get_complete_system_prompt()

self.system_prompt = self.user_system_prompt
```

#### 3.2 配置加载链

```
[chat_data_manager.py:282]
load_chat_settings("prefab_file_operator")
    ↓ 读取 data/prefab_file_operator/settings.json
    ↓ 返回 {'system_prompt': "...", ...}

[config_manager.py:81]
load_conversation_config("prefab_file_operator")
    ↓ 返回配置字典

[chat_box.py:379-428]
load_conversation_config("prefab_file_operator")
    ↓ 创建 ConversationConfig
    ↓ config.system_prompt = config_data.get('system_prompt', '')

[chat_box.py:430-456]
create_ai_instance(config, conversation_name)
    ↓ AI(system_prompt=config.system_prompt, ...)
```

### 4. 配置文件优先级

对于 `prefab_file_operator` 会话：

1. **用户配置** (优先级高):
   - `data/prefab_file_operator/settings.json`
   - 如果存在 `system_prompt` 字段，使用该值

2. **主配置** (fallback):
   - `prefab_file_operator.json` (根目录)
   - 包含预定义的 `system_prompt` 字段
   - 已包含文件操作工作流程

3. **默认配置** (最后fallback):
   - `ConversationConfig.command_execution_prompt` (ui/chat_box.py:205)

### 5. System Prompt 最终组成

当发送给 API 时，system prompt 包含：

```
final_system_prompt =
    user_system_prompt (来自 settings.json 或 prefab_file_operator.json)
    + 工具描述 (自动添加)
    + Markdown 格式规范 (自动添加)
    + history_usage_guidance (自动添加)
```

### 6. 关键代码位置

| 组件 | 文件 | 行号 | 说明 |
|------|------|------|------|
| AI 初始化 | aiclass.py | 232-237 | system_prompt 赋值 |
| 配置加载 | chat_data_manager.py | 282-321 | load_chat_settings |
| 配置管理 | config_manager.py | 81-105 | load_conversation_config |
| UI 创建 AI | chat_box.py | 430-456 | create_ai_instance |
| 历史加载 | ai_history_manager.py | 60-71 | load_history |
| 添加 system prompt | ai_history_manager.py | 73-98 | _ensure_system_prompt |
| 消息处理 | chat_box.py | 495-537 | MessageProcessor.process_message |

### 7. 示例：prefab_file_operator 的 system_prompt

**来源**: `prefab_file_operator.json:12`

**包含内容**:
1. 工具描述 (ls, cat, mkdir, etc.)
2. 核心原则
3. 调用格式
4. 错误示例
5. 多步操作规则
6. **文件操作工作流程** (已添加):
   ```
   【CRITICAL: File Operations Workflow】
   **MUST READ**: Before ANY file operation (ls, cat, mkdir, etc.), you MUST:

   1. FIRST call: YLDEXECUTE: get_system_info
   2. READ the result to get actual paths (desktop_dir, home_dir, etc.)
   3. THEN call the file operation with correct paths
   ```

### 8. 运行时修改

如果需要运行时修改 system_prompt：

```python
# 方法1: 通过配置更新
ai_instance.update_config({
    'system_prompt': 'new system prompt'
})

# 方法2: 直接更新
ai_instance.update_system_prompt('new system prompt')
```

修改后会自动更新到 `conv_his[0]["content"]`
