"""
LyNexus API Server
FastAPI backend for LyNexus WebUI

This server provides REST APIs for the WebUI to interact with
the AI assistant core logic, removing Qt UI dependencies.
"""

import os
import sys
import json
import io
import asyncio
import zipfile
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Import AI core
from aiclass import AI
from utils.config_manager import ConfigManager
from utils.ai_history_manager import AIHistoryManager
from utils.chat_data_manager import ChatDataManager

# ============================================================================
# Configuration
# ============================================================================

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories - Use ChatDataManager for consistency with Qt UI
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Initialize managers (consistent with chat_box.py)
config_manager = ConfigManager()
history_manager = AIHistoryManager()
chat_data_manager = ChatDataManager()

# ============================================================================
# Pydantic Models
# ============================================================================

class MessageModel(BaseModel):
    """Message model"""
    id: str
    content: str
    type: str  # USER, AI, COMMAND_REQUEST, COMMAND_RESULT, FINAL_SUMMARY, ERROR, INFO
    source: str  # USER, AI, SYSTEM
    timestamp: str
    conversationId: str
    isStreaming: Optional[bool] = False

class ConversationModel(BaseModel):
    """Conversation model"""
    id: str
    name: str
    createdAt: str
    updatedAt: str
    messageCount: int
    lastMessage: Optional[str] = None

class ConversationSettingsModel(BaseModel):
    """Conversation settings model"""
    apiKey: Optional[str] = None
    apiBase: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 1.0
    maxTokens: Optional[int] = None
    topP: float = 1.0
    presencePenalty: float = 0.0
    frequencyPenalty: float = 0.0
    stream: bool = True
    commandStart: str = "YLDEXECUTE:"
    commandSeparator: str = "￥|"
    maxIterations: int = 15
    mcpPaths: List[str] = []
    enabledMcpTools: List[str] = []
    systemPrompt: str = ""

class CreateConversationModel(BaseModel):
    """Create conversation model"""
    name: str

class SendMessageModel(BaseModel):
    """Send message model"""
    content: str

class UpdateSettingsModel(BaseModel):
    """Update settings model"""
    apiKey: Optional[str] = None
    apiBase: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None
    topP: Optional[float] = None
    presencePenalty: Optional[float] = None
    frequencyPenalty: Optional[float] = None
    stream: Optional[bool] = None
    commandStart: Optional[str] = None
    commandSeparator: Optional[str] = None
    maxIterations: Optional[int] = None
    mcpPaths: Optional[List[str]] = None
    enabledMcpTools: Optional[List[str]] = None
    systemPrompt: Optional[str] = None

class ValidateApiKeyModel(BaseModel):
    """Validate API key model"""
    apiKey: str
    apiBase: str

class MCPToolModel(BaseModel):
    """MCP tool model"""
    name: str
    description: str
    enabled: bool
    server: str

class SystemStatusModel(BaseModel):
    """System status model"""
    connected: bool
    version: str
    processingState: str

# ============================================================================
# Manager Instances
# ============================================================================

config_manager = ConfigManager()
history_manager = AIHistoryManager()
chat_data_manager = ChatDataManager()

# Store AI instances per conversation
conversation_ais: Dict[str, AI] = {}
conversation_configs: Dict[str, Dict] = {}

# ============================================================================
# Helper Functions
# ============================================================================

def get_conversation_dir(conversation_id: str) -> Path:
    """Get conversation directory - use ChatDataManager for consistency"""
    return chat_data_manager.get_chat_dir(conversation_id)

def load_conversation_config(conversation_id: str) -> Dict:
    """Load conversation configuration from disk"""
    config_file = get_conversation_dir(conversation_id) / "settings.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_conversation_config(conversation_id: str, config: Dict):
    """Save conversation configuration to disk"""
    config_file = get_conversation_dir(conversation_id) / "settings.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_api_key(conversation_id: str) -> str:
    """Load API key from .confignore file"""
    confignore_file = get_conversation_dir(conversation_id) / ".confignore"
    if confignore_file.exists():
        with open(confignore_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))

def save_api_key(conversation_id: str, api_key: str):
    """Save API key to .confignore file"""
    confignore_file = get_conversation_dir(conversation_id) / ".confignore"
    confignore_file.parent.mkdir(parents=True, exist_ok=True)
    with open(confignore_file, 'w', encoding='utf-8') as f:
        f.write(api_key)

def get_ai_instance(conversation_id: str) -> Optional[AI]:
    """Get or create AI instance for conversation"""
    if conversation_id in conversation_ais:
        return conversation_ais[conversation_id]

    # Load configuration
    config = load_conversation_config(conversation_id)
    api_key = load_api_key(conversation_id)

    if not api_key:
        return None

    # Create AI instance
    try:
        ai_kwargs = {
            'api_key': api_key,
            'api_base': config.get('api_base', 'https://api.deepseek.com'),
            'model': config.get('model', 'deepseek-chat'),
            'temperature': config.get('temperature', 1.0),
            'max_tokens': config.get('max_tokens'),
            'top_p': config.get('top_p', 1.0),
            'stream': config.get('stream', True),
            'command_start': config.get('command_start', 'YLDEXECUTE:'),
            'command_separator': config.get('command_separator', '￥|'),
            'max_iterations': config.get('max_iterations', 15),
            'mcp_paths': config.get('mcp_paths', []),
            'system_prompt': config.get('system_prompt', ''),
            'chat_name': conversation_id
        }

        # Remove None values
        ai_kwargs = {k: v for k, v in ai_kwargs.items() if v is not None and v != ''}

        ai_instance = AI(**ai_kwargs)
        conversation_ais[conversation_id] = ai_instance
        conversation_configs[conversation_id] = config

        return ai_instance
    except Exception as e:
        logger.error(f"Failed to create AI instance: {e}")
        return None

def get_message_file(conversation_id: str) -> Path:
    """Get message file path for conversation"""
    return get_conversation_dir(conversation_id) / f"{conversation_id}_ai.json"

def load_messages(conversation_id: str) -> List[Dict]:
    """Load messages from disk and convert to frontend format"""
    # Load AI history format: [{"role": "user/assistant", "content": "...", "timestamp": "..."}]
    ai_history = history_manager.load_history(conversation_id)

    # Convert to frontend message format
    messages = []
    for idx, msg in enumerate(ai_history):
        role = msg.get("role", "")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp")  # Get timestamp from AI history if available

        # Map role to type and source
        if role == "user":
            msg_type = "USER"
            source = "USER"
        elif role == "assistant":
            msg_type = "AI"
            source = "AI"
        else:
            msg_type = "INFO"
            source = "SYSTEM"

        messages.append({
            "id": f"msg-{idx}",
            "content": content,
            "type": msg_type,
            "source": source,
            "timestamp": timestamp if timestamp else datetime.now().isoformat(),
            "conversationId": conversation_id,
            "isStreaming": False
        })

    return messages

def save_messages(conversation_id: str, messages: List[Dict]):
    """Save messages to disk - use AIHistoryManager for consistency"""
    history_manager.save_history(conversation_id, messages)

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="LyNexus API",
    description="AI Assistant API with MCP tools support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API Routes: Conversations
# ============================================================================

@app.get("/api/conversations", response_model=List[ConversationModel])
async def get_all_conversations():
    """Get all conversations - using config_manager like chat_box.py"""
    try:
        # Use config_manager to load chat list (syncs with data directory automatically)
        chat_list_names = config_manager.load_chat_list()
        chat_records = config_manager.load_chat_history()

        conversations = []
        for chat_name in chat_list_names:
            # Get conversation config
            config = config_manager.load_conversation_config(chat_name) or {}

            # Get messages
            messages = chat_records.get(chat_name, [])

            # Get last message
            last_message = None
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    last_message = last_msg.get("text", "")
                elif isinstance(last_msg, str):
                    last_message = last_msg

            conversations.append({
                "id": chat_name,
                "name": config.get("name", chat_name),
                "createdAt": config.get("createdAt", datetime.now().isoformat()),
                "updatedAt": config.get("updatedAt", datetime.now().isoformat()),
                "messageCount": len(messages),
                "lastMessage": last_message
            })

        return conversations
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}", response_model=ConversationModel)
async def get_conversation(conversation_id: str):
    """Get conversation by ID"""
    try:
        conv_dir = get_conversation_dir(conversation_id)
        if not conv_dir.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")

        config = load_conversation_config(conversation_id)
        messages = load_messages(conversation_id)

        return {
            "id": conversation_id,
            "name": config.get("name", conversation_id),
            "createdAt": config.get("createdAt", datetime.now().isoformat()),
            "updatedAt": config.get("updatedAt", datetime.now().isoformat()),
            "messageCount": len(messages),
            "lastMessage": messages[-1].get("content", "") if messages else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations", response_model=ConversationModel)
async def create_conversation(data: CreateConversationModel):
    """Create new conversation - following chat_box.py _add_new_chat logic"""
    try:
        chat_name = data.name

        # Step 1: Create data folder using chat_data_manager
        chat_dir = chat_data_manager.create_chat_folder(chat_name)
        logger.info(f"Created chat data folder: {chat_dir}")

        # Step 2: Initialize chat records (empty list)
        chat_records = config_manager.load_chat_history()
        chat_records[chat_name] = []

        # Step 3: Save chat records
        config_manager.save_chat_history(chat_records)

        # Step 4: Save chat list
        chat_list = config_manager.load_chat_list() or []
        if chat_name not in chat_list:
            chat_list.append(chat_name)
        config_manager.save_chat_list(chat_list)

        # Step 5: Create settings with timestamps
        now = datetime.now().isoformat()
        settings = {
            "name": chat_name,
            "createdAt": now,
            "updatedAt": now
        }
        config_manager.save_conversation_config(chat_name, settings)

        logger.info(f"Created new chat: {chat_name}")

        return {
            "id": chat_name,
            "name": chat_name,
            "createdAt": now,
            "updatedAt": now,
            "messageCount": 0,
            "lastMessage": None
        }
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/conversations/{conversation_id}", response_model=ConversationModel)
async def update_conversation(conversation_id: str, data: Dict):
    """Update conversation"""
    try:
        conv_dir = get_conversation_dir(conversation_id)
        if not conv_dir.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")

        config = load_conversation_config(conversation_id)

        if "name" in data:
            config["name"] = data["name"]
        config["updatedAt"] = datetime.now().isoformat()

        save_conversation_config(conversation_id, config)

        messages = load_messages(conversation_id)

        return {
            "id": conversation_id,
            "name": config["name"],
            "createdAt": config["createdAt"],
            "updatedAt": config["updatedAt"],
            "messageCount": len(messages),
            "lastMessage": messages[-1].get("content", "") if messages else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation - following chat_box.py logic"""
    try:
        # Check if conversation exists
        conv_dir = get_conversation_dir(conversation_id)
        if not conv_dir.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Remove AI instance from cache
        if conversation_id in conversation_ais:
            del conversation_ais[conversation_id]
        if conversation_id in conversation_configs:
            del conversation_configs[conversation_id]

        # Delete chat folder using chat_data_manager (this removes all data)
        success = chat_data_manager.delete_chat_folder(conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chat folder")

        # Remove from chat list
        chat_list = config_manager.load_chat_list() or []
        if conversation_id in chat_list:
            chat_list.remove(conversation_id)
            config_manager.save_chat_list(chat_list)

        logger.info(f"Deleted conversation: {conversation_id}")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}/messages")
async def clear_conversation_messages(conversation_id: str):
    """Clear all messages in a conversation"""
    try:
        # Get AI instance to obtain system prompt
        ai = get_ai_instance(conversation_id)
        system_prompt = ai.system_prompt if ai else None

        # Use history_manager.clear_history() to preserve system prompt
        # clear_history handles None system_prompt by using default
        history_manager.clear_history(conversation_id, system_prompt or "")

        # Update config
        config = load_conversation_config(conversation_id)
        config["updatedAt"] = datetime.now().isoformat()
        save_conversation_config(conversation_id, config)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error clearing messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Routes: Messages
# ============================================================================

@app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageModel])
async def get_messages(conversation_id: str):
    """Get messages for a conversation"""
    try:
        messages = load_messages(conversation_id)
        return messages
    except Exception as e:
        logger.error(f"Error loading messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def message_generator(ai: AI, user_message: str, conversation_id: str):
    """Generate streaming response"""
    try:
        current_time = datetime.now().isoformat()

        # Create user message
        user_msg = {
            "id": f"msg-{int(datetime.now().timestamp() * 1000)}",
            "content": user_message,
            "type": "USER",
            "source": "USER",
            "timestamp": current_time,
            "conversationId": conversation_id,
            "isStreaming": False
        }

        # Load conversation history with system prompt
        # This is CRITICAL: history_manager.load_history() will:
        # 1. Load history from data/{chat_name}/{chat_name}_ai.json
        # 2. Inject system prompt with tools description + markdown rules + history guidance
        # Get effective system prompt (includes tools description + markdown rules)
        system_prompt = ai.get_effective_system_prompt() if ai else None
        conversation_history = history_manager.load_history(conversation_id, system_prompt or "")

        # Add user message to history WITH timestamp
        conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": current_time
        })

        # Yield user message - EventSourceResponse requires JSON-encoded string for 'data'
        yield {'data': json.dumps({'type': 'user_message', 'message': user_msg})}

        # Stream AI response
        full_response = ""
        message_id = f"msg-{int(datetime.now().timestamp() * 1000) + 1}"

        # Process with streaming - CRITICAL: pass conversation_history
        # This ensures AI has proper context with system prompt
        # aiclass.py will handle command detection and execution internally
        for chunk in ai.process_user_input_stream(user_message, conversation_history):
            if chunk:
                full_response += chunk
                # Send chunk - EventSourceResponse requires JSON-encoded string for 'data'
                yield {'data': json.dumps({'type': 'chunk', 'content': chunk, 'messageId': message_id})}

        # CRITICAL: Use the updated history from aiclass (includes all commands and results)
        # aiclass.process_user_input_stream updates ai.conv_his internally
        updated_history = ai.conv_his.copy() if hasattr(ai, 'conv_his') and ai.conv_his else conversation_history

        # Create AI message
        ai_msg = {
            "id": message_id,
            "content": full_response,
            "type": "AI",
            "source": "AI",
            "timestamp": datetime.now().isoformat(),
            "conversationId": conversation_id,
            "isStreaming": False
        }

        # Save updated history (includes all commands, results, and final AI response)
        # The updated_history from aiclass contains:
        # - User messages
        # - All command executions (assistant role)
        # - All command results (user role with command_execution_prompt)
        # - Final AI response
        history_manager.save_history(conversation_id, updated_history)

        # Update conversation timestamp
        config = load_conversation_config(conversation_id)
        config["updatedAt"] = datetime.now().isoformat()
        save_conversation_config(conversation_id, config)

        # Send complete event - EventSourceResponse requires JSON-encoded string for 'data'
        yield {'data': json.dumps({'type': 'complete', 'message': ai_msg})}

    except Exception as e:
        logger.error(f"Error in streaming: {e}")
        yield {'data': json.dumps({'type': 'error', 'error': str(e)})}

@app.post("/api/conversations/{conversation_id}/messages/stream")
async def stream_message(conversation_id: str, data: SendMessageModel):
    """Send message with streaming response (SSE)"""
    try:
        ai = get_ai_instance(conversation_id)
        if not ai:
            raise HTTPException(status_code=400, detail="AI not initialized. Please configure API key first.")

        return EventSourceResponse(
            message_generator(ai, data.content, conversation_id),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stream_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, data: SendMessageModel):
    """Send message (non-streaming)"""
    try:
        ai = get_ai_instance(conversation_id)
        if not ai:
            raise HTTPException(status_code=400, detail="AI not initialized")

        current_time = datetime.now().isoformat()

        # Load AI history
        # Get effective system prompt (includes tools description + markdown rules)
        system_prompt = ai.get_effective_system_prompt() if ai else None
        conversation_history = history_manager.load_history(conversation_id, system_prompt or "")

        # Add user message to history WITH timestamp
        user_msg_timestamp = current_time
        conversation_history.append({
            "role": "user",
            "content": data.content,
            "timestamp": user_msg_timestamp
        })

        # Get AI response
        response = ai.process_user_input_with_history(data.content, conversation_history)

        # CRITICAL: Use the updated history from aiclass (includes all commands and results)
        # aiclass.process_user_input_with_history updates ai.conv_his internally
        updated_history = ai.conv_his.copy() if hasattr(ai, 'conv_his') and ai.conv_his else conversation_history

        # Save to AI history (includes all commands and results)
        history_manager.save_history(conversation_id, updated_history)

        # Return in frontend format
        ai_msg = {
            "id": f"msg-{int(datetime.now().timestamp() * 1000) + 1}",
            "content": response,
            "type": "AI",
            "source": "AI",
            "timestamp": datetime.now().isoformat(),
            "conversationId": conversation_id,
            "isStreaming": False
        }

        return ai_msg
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/messages/stop")
async def stop_streaming(conversation_id: str):
    """Stop streaming response and kill any running command processes"""
    try:
        # Get AI instance for this conversation
        ai = get_ai_instance(conversation_id)
        if ai:
            # Set stop flag to stop streaming
            ai.set_stop_flag(True)

            # Kill any running subprocess if exists
            if hasattr(ai, 'current_process') and ai.current_process:
                try:
                    ai.current_process.kill()
                    logger.info(f"Killed running process for conversation {conversation_id}")
                except Exception as proc_error:
                    logger.warning(f"Failed to kill process: {proc_error}")

            # Stop MCP server processes if they exist
            if hasattr(ai, 'mcp_managers') and ai.mcp_managers:
                for server_name, manager in ai.mcp_managers.items():
                    try:
                        if hasattr(manager, 'stop_all'):
                            manager.stop_all()
                            logger.info(f"Stopped MCP server: {server_name}")
                    except Exception as mcp_error:
                        logger.warning(f"Failed to stop MCP server {server_name}: {mcp_error}")

            logger.info(f"Stop flag set for conversation {conversation_id}")
        else:
            logger.warning(f"No AI instance found for conversation {conversation_id}")

        return {"success": True}
    except Exception as e:
        logger.error(f"Error stopping streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Routes: Settings
# ============================================================================

@app.get("/api/conversations/{conversation_id}/settings", response_model=ConversationSettingsModel)
async def get_settings(conversation_id: str):
    """Get conversation settings"""
    try:
        config = load_conversation_config(conversation_id)
        api_key = load_api_key(conversation_id)  # Load from .confignore

        # Convert snake_case to camelCase for frontend
        converted_config = {
            "apiKey": api_key,  # Load API key from .confignore file
            "apiBase": config.get("api_base", config.get("apiBase", "https://api.deepseek.com")),
            "model": config.get("model", "deepseek-chat"),
            "temperature": config.get("temperature", 1.0),
            "maxTokens": config.get("max_tokens", config.get("maxTokens", 4096)),
            "topP": config.get("top_p", config.get("topP", 1.0)),
            "presencePenalty": config.get("presence_penalty", config.get("presencePenalty", 0.0)),
            "frequencyPenalty": config.get("frequency_penalty", config.get("frequencyPenalty", 0.0)),
            "stream": config.get("stream", True),
            "commandStart": config.get("command_start", config.get("commandStart", "YLDEXECUTE:")),
            "commandSeparator": config.get("command_separator", config.get("commandSeparator", "￥|")),
            "maxIterations": config.get("max_iterations", config.get("maxIterations", 15)),
            "mcpPaths": config.get("mcp_paths", config.get("mcpPaths", [])),
            "enabledMcpTools": config.get("enabled_mcp_tools", config.get("enabledMcpTools", [])),
            "systemPrompt": config.get("system_prompt", config.get("systemPrompt", "")),
        }

        return converted_config
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/conversations/{conversation_id}/settings", response_model=ConversationSettingsModel)
async def update_settings(conversation_id: str, data: UpdateSettingsModel):
    """Update conversation settings"""
    try:
        config = load_conversation_config(conversation_id)

        # Convert camelCase to snake_case for saving to settings.json
        camel_to_snake = {
            "apiKey": "apiKey",
            "apiBase": "api_base",
            "model": "model",
            "temperature": "temperature",
            "maxTokens": "max_tokens",
            "topP": "top_p",
            "presencePenalty": "presence_penalty",
            "frequencyPenalty": "frequency_penalty",
            "stream": "stream",
            "commandStart": "command_start",
            "commandSeparator": "command_separator",
            "maxIterations": "max_iterations",
            "mcpPaths": "mcp_paths",
            "enabledMcpTools": "enabled_mcp_tools",
            "systemPrompt": "system_prompt",
        }

        # Update only provided fields
        update_dict = data.dict(exclude_unset=True)

        for key, value in update_dict.items():
            if value is not None:
                # Convert to snake_case for storage
                snake_key = camel_to_snake.get(key, key)
                config[snake_key] = value

        # Save API key if provided
        if data.apiKey:
            save_api_key(conversation_id, data.apiKey)
            if "apiKey" in config:
                del config["apiKey"]

        config["updatedAt"] = datetime.now().isoformat()
        save_conversation_config(conversation_id, config)

        # Recreate AI instance with new settings
        if conversation_id in conversation_ais:
            del conversation_ais[conversation_id]

        # Return converted config for frontend (must await!)
        return await get_settings(conversation_id)
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/validate-key")
async def validate_api_key(data: ValidateApiKeyModel):
    """Validate API key"""
    try:
        # Simple validation - try to create AI instance
        test_kwargs = {
            'api_key': data.apiKey,
            'api_base': data.apiBase,
            'model': 'gpt-3.5-turbo',  # Use small model for validation
            'chat_name': 'validation_test'
        }

        test_ai = AI(**test_kwargs)

        # Try a simple request
        # TODO: Implement actual validation call
        return {"valid": True}
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return {"valid": False, "error": str(e)}

# ============================================================================
# API Routes: MCP Tools
# ============================================================================

@app.get("/api/mcp/tools", response_model=List[MCPToolModel])
async def get_mcp_tools(conversation: Optional[str] = None):
    """Get available MCP tools"""
    try:
        if not conversation:
            return []

        ai = get_ai_instance(conversation)
        if not ai:
            return []

        # Get tools from AI instance using get_mcp_tools_info()
        tools_info = ai.get_mcp_tools_info()

        # Convert to MCPToolModel format
        tools = [
            MCPToolModel(
                name=tool['name'],
                description=tool['description'],
                enabled=tool['enabled'],
                server=tool['server']
            )
            for tool in tools_info
        ]

        return tools
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/mcp-tools")
async def add_mcp_tool(conversation_id: str, filePath: str = Form(...)):
    """Add MCP tool to conversation (deprecated - use upload_mcp_tools instead)"""
    try:
        config = load_conversation_config(conversation_id)
        mcp_paths = config.get("mcp_paths", [])

        if filePath not in mcp_paths:
            mcp_paths.append(filePath)
            config["mcp_paths"] = mcp_paths
            save_conversation_config(conversation_id, config)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error adding MCP tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{conversation_id}/mcp-tools/upload")
async def upload_mcp_tools(conversation_id: str, files: List[UploadFile] = File(...)):
    """
    Upload MCP tool files to the conversation's tools directory (data/{conversation_id}/tools/)
    Automatically saves files and returns the relative paths
    """
    try:
        # Get or create conversation directory
        conv_dir = get_conversation_dir(conversation_id)
        if not conv_dir.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get tools directory
        tools_dir = chat_data_manager.get_tools_dir(conversation_id)
        tools_dir.mkdir(parents=True, exist_ok=True)

        uploaded_paths = []

        for file in files:
            # Check file extension
            if not file.filename.endswith(('.py', '.json', '.yaml', '.yml')):
                logger.warning(f"Skipping invalid file type: {file.filename}")
                continue

            # Save file to tools directory
            file_path = tools_dir / file.filename

            try:
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)

                # Return relative path with forward slashes
                relative_path = f"./tools/{file.filename}"
                uploaded_paths.append(relative_path)

                logger.info(f"Uploaded MCP tool: {file.filename} -> {file_path}")

            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {e}")
                continue

        # Update conversation config with new paths
        if uploaded_paths:
            config = load_conversation_config(conversation_id)
            mcp_paths = config.get("mcp_paths", [])

            for path in uploaded_paths:
                if path not in mcp_paths:
                    mcp_paths.append(path)

            config["mcp_paths"] = mcp_paths
            config["updatedAt"] = datetime.now().isoformat()
            save_conversation_config(conversation_id, config)

            # Recreate AI instance to reload tools
            if conversation_id in conversation_ais:
                del conversation_ais[conversation_id]

        return {
            "success": True,
            "uploadedCount": len(uploaded_paths),
            "paths": uploaded_paths
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/mcp/tools/{tool_name}/toggle")
async def toggle_mcp_tool(tool_name: str, conversationId: str, enabled: bool):
    """Toggle MCP tool enabled state"""
    try:
        config = load_conversation_config(conversationId)
        enabled_tools = config.get("enabledMcpTools", [])

        if enabled:
            if tool_name not in enabled_tools:
                enabled_tools.append(tool_name)
        else:
            if tool_name in enabled_tools:
                enabled_tools.remove(tool_name)

        config["enabledMcpTools"] = enabled_tools
        save_conversation_config(conversationId, config)

        return {"success": True}
    except Exception as e:
        logger.error(f"Error toggling MCP tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Routes: Export/Import
# ============================================================================

@app.post("/api/conversations/{conversation_id}/export")
async def export_config(conversation_id: str):
    """Export conversation configuration as ZIP"""
    try:
        logger.info(f"[Export] Export config request for conversation_id: {conversation_id}")
        logger.info(f"[Export] conversation_id type: {type(conversation_id)}")

        import io

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add settings.json
            config_file = get_conversation_dir(conversation_id) / "settings.json"
            logger.info(f"[Export] Config file path: {config_file}")
            logger.info(f"[Export] Config file exists: {config_file.exists()}")

            if config_file.exists():
                zipf.write(config_file, f"{conversation_id}/settings.json")
                logger.info(f"[Export] Added settings.json to ZIP")
            else:
                logger.warning(f"[Export] Config file does not exist: {config_file}")

            # Add tools directory
            tools_dir = get_conversation_dir(conversation_id) / "tools"
            logger.info(f"[Export] Tools directory path: {tools_dir}")
            logger.info(f"[Export] Tools directory exists: {tools_dir.exists()}")

            if tools_dir.exists():
                for root, dirs, files in os.walk(tools_dir):
                    for file in files:
                        if "__pycache__" in root:
                            continue
                        file_path = Path(root) / file
                        arcname = f"{conversation_id}/tools/{file_path.relative_to(tools_dir)}"
                        zipf.write(file_path, arcname)
                logger.info(f"[Export] Added tools directory to ZIP")

        zip_buffer.seek(0)

        # Return ZIP file
        filename = f"{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        logger.info(f"[Export] Successfully created ZIP file: {filename}")

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        import traceback
        logger.error(f"[Export] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}/export/history")
async def export_history(conversation_id: str):
    """Export chat history"""
    try:
        messages = load_messages(conversation_id)

        # Return as JSON
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "conversationId": conversation_id,
                "exportedAt": datetime.now().isoformat(),
                "messages": messages
            },
            headers={
                "Content-Disposition": f"attachment; filename={conversation_id}_history.json"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/import")
async def import_config(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """Import conversation configuration from ZIP"""
    try:
        # Read ZIP file
        zip_data = await file.read()

        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zipf:
            # Find the root folder
            files = zipf.namelist()

            if not files:
                raise HTTPException(status_code=400, detail="Empty ZIP file")

            # Get root folder name
            root_folder = files[0].split('/')[0]

            # Extract settings.json
            settings_data = None
            if f"{root_folder}/settings.json" in files:
                settings_data = json.loads(zipf.read(f"{root_folder}/settings.json"))

            # Create new conversation
            conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            conv_dir = get_conversation_dir(conv_id)
            conv_dir.mkdir(parents=True, exist_ok=True)

            now = datetime.now().isoformat()

            # Save settings
            if settings_data:
                settings_data["createdAt"] = now
                settings_data["updatedAt"] = now
                # Use provided name or fallback to settings name
                if name:
                    settings_data["name"] = name
                save_conversation_config(conv_id, settings_data)
            else:
                save_conversation_config(conv_id, {
                    "name": name or conv_id,
                    "createdAt": now,
                    "updatedAt": now
                })

            # Extract tools
            for file in files:
                if file.startswith(f"{root_folder}/tools/"):
                    # Extract tool files
                    file_data = zipf.read(file)
                    rel_path = Path(file).relative_to(Path(root_folder))
                    dest_path = conv_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest_path, 'wb') as f:
                        f.write(file_data)

        # Return created conversation
        config = load_conversation_config(conv_id)
        return {
            "id": conv_id,
            "name": config.get("name", conv_id),
            "createdAt": config.get("createdAt", now),
            "updatedAt": config.get("updatedAt", now),
            "messageCount": 0,
            "lastMessage": None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Routes: System
# ============================================================================

@app.get("/api/system/status", response_model=SystemStatusModel)
async def get_system_status():
    """Get system status"""
    return {
        "connected": True,
        "version": "1.0.0",
        "processingState": "IDLE"
    }

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*50)
    print("🚀 LyNexus API Server")
    print("="*50)
    print(f"📂 Data directory: {DATA_DIR.absolute()}")
    print(f"🔗 API URL: http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    print("="*50 + "\n")

    # Check for --no-reload flag (useful for production/packaged builds)
    reload_flag = "--no-reload" not in sys.argv

    print(f"Auto-reload: {'Enabled' if reload_flag else 'Disabled (production mode)'}")

    # Import app directly for PyInstaller/uvicorn compatibility
    # This avoids the "Could not import module" error in packaged builds
    if reload_flag:
        # Development mode: use string reference for auto-reload
        uvicorn.run(
            "api_server:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        # Production mode: use direct app reference
        from api_server import app as asgi_app
        uvicorn.run(
            asgi_app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
