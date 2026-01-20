# 硬编码 Prompt 移除总结

## 修改目标
将所有用户可配置的 prompt 硬编码移至配置文件 `default_prompts.json`，保留框架核心逻辑的硬编码。

## 已移除的硬编码（用户可配置）

### 1. Command Execution Prompt
**原位置**:
- `ui/chat_box.py:205-216` (ConversationConfig)
- `aiclass.py:107-183` (AI.__init__)

**新位置**: `default_prompts.json` → `command_execution_prompt`

**用途**: 命令执行后指导 AI 下一步操作的提示

### 2. Command Retry Prompt
**原位置**:
- `ui/chat_box.py:218-232` (ConversationConfig)
- `aiclass.py:160-172` (AI.__init__)

**新位置**: `default_prompts.json` → `command_retry_prompt`

**用途**: 命令执行失败时指导 AI 重试的提示

### 3. Final Summary Prompt
**原位置**:
- `ui/chat_box.py:234-257` (ConversationConfig)
- `aiclass.py:176-199` (AI.__init__)

**新位置**: `default_prompts.json` → `final_summary_prompt`

**用途**: 达到最大迭代次数时指导 AI 给出最终答案的提示

### 4. Default System Prompts
**原位置**:
- `ui/chat_box.py:408` (fallback)
- `utils/ai_history_manager.py:95` (fallback)

**新位置**: `default_prompts.json` → `system_prompts.default` / `system_prompts.fallback`

**用途**: 当没有配置时的默认系统提示

### 5. History Usage Guidance
**原位置**:
- `utils/ai_history_manager.py:23-32` (HISTORY_USAGE_GUIDANCE 常量)

**新位置**: `default_prompts.json` → `history_usage_guidance`

**用途**: 指导 AI 如何使用对话历史的提示

## 保留的硬编码（框架核心逻辑）

### 1. Markdown Format Prompt
**位置**: `aiclass.py:_get_markdown_format_prompt()` (第734-787行)

**原因**: 这是框架的输出格式规范，属于核心功能逻辑，不应该由用户配置

**内容**:
```python
def _get_markdown_format_prompt(self) -> str:
    """
    获取硬编码的 Markdown 格式规范提示词
    这个提示词始终会被添加到系统提示中，确保 AI 正确使用 Markdown 格式
    """
    return """【CRITICAL: Markdown Formatting Requirements - MANDATORY】
...
```

## 实现方式

### 加载机制
每个模块在加载时调用 `_load_default_prompts()` 函数：

```python
def _load_default_prompts() -> Dict:
    """Load default prompts from configuration file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'default_prompts.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Module] Failed to load default_prompts.json: {e}")

    # Return minimal fallback if file doesn't exist
    return {...}

# Load once at module level
_DEFAULT_PROMPTS = _load_default_prompts()
```

### 使用方式
```python
# 使用配置文件的值
self.command_execution_prompt = command_execution_prompt or _DEFAULT_PROMPTS.get('command_execution_prompt', '')
```

## 修改的文件

1. **新增**: `default_prompts.json` - 集中管理所有用户可配置的默认 prompt
2. **ui/chat_box.py**:
   - 添加 `_load_default_prompts()` 函数
   - 修改 `ConversationConfig` 使用配置文件
   - 修改 fallback system_prompt 使用配置文件
3. **aiclass.py**:
   - 添加 `_load_default_prompts()` 函数
   - 修改 `AI.__init__` 使用配置文件
4. **utils/ai_history_manager.py**:
   - 添加 `_load_default_prompts()` 函数
   - 移除 `HISTORY_USAGE_GUIDANCE` 常量
   - 修改 `get_history_usage_guidance()` 方法
   - 修改 fallback system_prompt 使用配置文件

## 配置优先级

```
用户配置 (data/{chat}/settings.json)
    ↓ (如果不存在)
主配置 (prefab_file_operator.json)
    ↓ (如果不存在)
默认配置 (default_prompts.json)
    ↓ (如果文件不存在)
代码 fallback (最小化硬编码)
```

## 验证

所有用户可配置的 prompt 都已从代码中移除，保留的硬编码仅限框架核心逻辑：

✅ command_execution_prompt → default_prompts.json
✅ command_retry_prompt → default_prompts.json
✅ final_summary_prompt → default_prompts.json
✅ system_prompts → default_prompts.json
✅ history_usage_guidance → default_prompts.json
✅ markdown_format_prompt → 保留硬编码（框架核心逻辑）
