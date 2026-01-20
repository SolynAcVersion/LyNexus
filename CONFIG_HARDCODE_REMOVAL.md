# 配置硬编码移除总结

## 目标
将所有用户可配置的默认值从代码硬编码移至配置文件，确保所有 settings 中可配置的内容都可以通过配置文件统一管理。

## 配置文件结构

### 1. `default_config.json` - 默认配置值
包含所有可配置参数的默认值：
```json
{
  "api": {
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-chat"
  },
  "command_format": {
    "command_start": "YLDEXECUTE:",
    "command_separator": "￥|"
  },
  "model_parameters": {
    "temperature": 1.0,
    "max_tokens": 4096,
    "top_p": 1.0,
    "stream": true,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
  },
  "execution": {
    "max_iterations": 15
  },
  "mcp": {
    "mcp_paths": [],
    "enabled_mcp_tools": []
  }
}
```

### 2. `default_prompts.json` - 默认提示词
包含所有用户可配置的 prompt：
```json
{
  "system_prompts": {
    "default": "You are a helpful AI assistant...",
    "fallback": "You are an AI assistant that can execute commands..."
  },
  "command_execution_prompt": "...",
  "command_retry_prompt": "...",
  "final_summary_prompt": "...",
  "history_usage_guidance": "..."
}
```

## 修改的文件

### ui/chat_box.py
**添加函数**:
- `_load_default_config()` - 加载 default_config.json
- `_get_config_value(path, fallback)` - 使用点号路径获取配置值

**修改方法**:
- `load_conversation_config()` - 所有 `config_data.get()` 的 fallback 从 `_get_config_value()` 读取

### aiclass.py
**添加函数**:
- `_load_default_config()` - 加载 default_config.json

**修改方法**:
- `AI.__init__()` - API 配置的 fallback 从 `_DEFAULT_CONFIG` 读取

### default_config.json
**新增文件** - 集中管理所有默认配置值

## 配置优先级

```
用户配置 (data/{chat}/settings.json)
    ↓ (如果不存在或字段缺失)
主配置 (prefab_file_operator.json)
    ↓ (如果不存在或字段缺失)
默认配置 (default_config.json / default_prompts.json)
    ↓ (如果文件不存在)
代码 fallback (最小化，仅作为最后保障)
```

## 已移除的硬编码

### API 配置
- ❌ `'https://api.deepseek.com'` → ✅ `_get_config_value('api.api_base')`
- ❌ `'deepseek-chat'` → ✅ `_get_config_value('api.model')`

### 命令格式
- ❌ `'YLDEXECUTE:'` → ✅ `_get_config_value('command_format.command_start')`
- ❌ `'￥|'` → ✅ `_get_config_value('command_format.command_separator')`

### 模型参数
- ❌ `temperature=1.0` → ✅ `_get_config_value('model_parameters.temperature')`
- ❌ `max_iterations=15` → ✅ `_get_config_value('execution.max_iterations')`
- ❌ `stream=True` → ✅ `_get_config_value('model_parameters.stream')`

## 保留的硬编码

### 1. UI Placeholder 文本 (ui/init_dialog.py, ui/settings_dialog.py)
```python
api_base_edit.setPlaceholderText("https://api.deepseek.com")  # 保留
```
**原因**: 这是用户界面的示例文本，不是实际使用的配置值

### 2. Dataclass 默认值 (ui/chat_box.py - ConversationConfig)
```python
@api Class ConversationConfig:
    api_base: str = "https://api.deepseek.com"  # 保留
```
**原因**:
- 这些只是类型注解的默认值
- 实际使用时会从配置文件读取
- 作为最后的 fallback 保障

### 3. Markdown 格式 Prompt (aiclass.py - _get_markdown_format_prompt)
```python
def _get_markdown_format_prompt(self) -> str:
    return """【CRITICAL: Markdown Formatting Requirements..."""
```
**原因**: 这是框架的核心输出格式规范，不应由用户配置

## 加载机制

### 模块级加载（启动时一次）
```python
# ui/chat_box.py
_DEFAULT_CONFIG = _load_default_config()  # 启动时加载
_DEFAULT_PROMPTS = _load_default_prompts()

# aiclass.py
_DEFAULT_CONFIG = _load_default_config()
_DEFAULT_PROMPTS = _load_default_prompts()
```

### 使用时读取
```python
# 方式1: 直接获取
api_base = _get_config_value('api.api_base')

# 方式2: 作为 fallback
config_data.get('api_base', _get_config_value('api.api_base'))
```

## 验证

✅ 所有用户可配置的默认值都已移至配置文件
✅ 代码中仅保留必要的 fallback（当配置文件不存在时）
✅ UI placeholder 保留（因为是示例文本）
✅ 框架核心逻辑保留（Markdown 格式规范）

## 使用示例

### 修改默认 API
编辑 `default_config.json`:
```json
{
  "api": {
    "api_base": "https://api.openai.com",
    "model": "gpt-4"
  }
}
```

### 修改命令格式
编辑 `default_config.json`:
```json
{
  "command_format": {
    "command_start": "EXECUTE:",
    "command_separator": "|"
  }
}
```

### 修改默认提示词
编辑 `default_prompts.json`:
```json
{
  "system_prompts": {
    "default": "You are a coding assistant..."
  }
}
```
