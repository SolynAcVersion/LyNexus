# Data Storage Structure

All chat-related data is stored in the `data/` directory with the following structure:

```
data/
├── {chat_name}/
│   ├── settings.json          # Chat settings (API keys removed for security)
│   ├── chat_his.pickle        # Chat display history (UI messages)
│   ├── {chat_name}_ai.json    # AI conversation history (for context)
│   └── tools/                 # MCP tools specific to this chat
│       ├── *.py               # Python tool files
│       ├── *.json             # MCP configuration files
│       └── ...
└── ...
```

## Directory Structure Details

### `data/{chat_name}/`
Each conversation has its own folder with a sanitized name (invalid characters removed, spaces replaced with underscores).

#### Files in each chat folder:

1. **`settings.json`**
   - Chat-specific settings
   - Contains: model, temperature, max_tokens, mcp_paths, etc.
   - API keys are **NOT** stored here (stored separately in `.confignore`)

2. **`chat_his.pickle`**
   - Chat display history
   - Stores messages shown in the UI
   - Includes: user messages, AI responses, timestamps
   - Format: Python pickle file

3. **`{chat_name}_ai.json`**
   - AI conversation history
   - Used for AI context and continuity
   - Contains: system prompt, user messages, assistant responses
   - Format: JSON array of message objects
   - Example:
     ```json
     [
       {"role": "system", "content": "You are an AI assistant..."},
       {"role": "user", "content": "Hello"},
       {"role": "assistant", "content": "Hi! How can I help?"}
     ]
     ```

4. **`tools/` directory**
   - MCP (Model Context Protocol) tools for this specific chat
   - Can contain:
     - Python tool files (`*.py`)
     - MCP configuration files (`*.json`, `*.yaml`, `*.yml`)
   - Tools are loaded when the chat is initialized

## Old Directories (Deprecated)

The following directories are **NO LONGER USED** but may still exist for backward compatibility:

- `ai_conv/` - Old AI conversation history storage
- `chathistory/` - Old chat display history storage
- `conversations/` - Old conversation storage

These directories are ignored by git and will not be created for new chats.

## Data Management

### Creating a New Chat
```python
from utils.chat_data_manager import ChatDataManager

manager = ChatDataManager()
chat_dir = manager.create_chat_folder("My Chat")
# Creates: data/My_Chat/
#          data/My_Chat/tools/
```

### Saving Chat Data
```python
# Save AI history
manager.save_ai_history("My Chat", [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Hello"}
])

# Save chat display history
manager.save_chat_history("My Chat", [
    {"text": "Hello", "is_sender": True, "timestamp": "..."}
])

# Save settings
manager.save_chat_settings("My Chat", {
    "model": "claude-3-5-sonnet",
    "mcp_paths": ["./tools/file.py"]
})
```

### Loading Chat Data
```python
# Load AI history
ai_history = manager.load_ai_history("My Chat")

# Load chat display history
chat_history = manager.load_chat_history("My Chat")

# Load settings
settings = manager.load_chat_settings("My Chat")
```

### Deleting a Chat
```python
# Deletes the entire chat folder and all its contents
manager.delete_chat_folder("My Chat")
# Removes: data/My_Chat/ and everything inside it
```

## Security Notes

1. **API Keys**: Never stored in `settings.json` - stored in `.confignore` files which are git-ignored
2. **Sensitive Data**: All data in `data/` is local and not synced to git
3. **File Permissions**: Ensure `data/` directory has appropriate permissions

## Migration from Old Structure

If you have data in the old directories (`ai_conv/`, `chathistory/`), it will **NOT** be automatically migrated. Old data is still readable during the transition period, but new data will only be written to the `data/` directory structure.

To manually migrate old data:
1. Create new chat folders in `data/`
2. Copy `ai_conv/*.json` → `data/{chat_name}/{chat_name}_ai.json`
3. Copy `chathistory/*.pickle` → `data/{chat_name}/chat_his.pickle`
4. Verify data integrity
5. Delete old directories when confident

## Benefits of New Structure

1. **Isolation**: Each chat's data is completely self-contained
2. **Easy Backup**: Simply copy the `data/` directory
3. **Easy Sharing**: Share individual chat folders
4. **Easy Deletion**: Delete a chat by removing its folder
5. **Scalability**: Supports unlimited chats without clutter
6. **Tool Management**: Each chat can have its own set of MCP tools
