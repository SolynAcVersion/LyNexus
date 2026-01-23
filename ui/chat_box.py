# [file name]: ui/chat_box.py

import sys
import os
import json
import time
import traceback
import shutil
import zipfile
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QScrollArea, QListWidget, QListWidgetItem, QFrame,
    QInputDialog, QMessageBox, QStatusBar, QFileDialog,
    QSizePolicy, QSpacerItem, QApplication, QProgressBar
)
from PySide6.QtGui import QIcon, QTextCursor, QTextDocument
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QSize, QPoint, QRect, QEvent,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, Property, QTime, QAbstractAnimation,
    QMetaObject, Slot, Q_ARG
)

from config.i18n import i18n
from utils.config_manager import ConfigManager
from utils.ai_history_manager import AIHistoryManager
from utils.chat_data_manager import ChatDataManager
from utils.markdown_renderer import MarkdownRenderer, RenderMode, get_renderer
from ui.init_dialog import InitDialog
from ui.settings_dialog import SettingsDialog
from ui.mcp_tools_widget import MCPToolsWidget
from aiclass import AI


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class DragDropTextEdit(QTextEdit):
    """Custom QTextEdit with proper drag and drop handling for file paths"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.parent_chat_box = None  # Reference to parent chat box

    def setParentChatBox(self, chat_box):
        """Set reference to parent chat box"""
        self.parent_chat_box = chat_box

    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Handle drop event - insert file paths at cursor position"""
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]

            # Build file paths string
            file_paths = ' '.join(f'"{f}"' for f in files if os.path.exists(f))

            if file_paths:
                print(f"[DragDropTextEdit] Inserting file paths: {file_paths}")

                # Get current state
                cursor = self.textCursor()
                position = cursor.position()
                text = self.toPlainText()

                print(f"[DragDropTextEdit] Before - Text length: {len(text)}, Cursor at: {position}")

                # Insert at cursor position
                new_text = text[:position] + file_paths + ' ' + text[position:]
                new_cursor_pos = position + len(file_paths) + 1

                # Set new text
                self.setPlainText(new_text)

                # Position cursor
                new_cursor = QTextCursor(self.document())
                new_cursor.setPosition(min(new_cursor_pos, len(new_text)), QTextCursor.MoveMode.MoveAnchor)
                new_cursor.clearSelection()
                self.setTextCursor(new_cursor)

                print(f"[DragDropTextEdit] After - Text length: {len(new_text)}, Cursor at: {new_cursor_pos}")

                # Ensure cursor is visible
                self.ensureCursorVisible()

            event.acceptProposedAction()
        else:
            # Let parent handle non-URL drops
            super().dropEvent(event)

class DraggableListWidget(QListWidget):
    """
    Custom QListWidget that accepts ZIP file drops for importing chat configurations.
    When a ZIP file is dropped, it calls the parent chat box's import function.
    """

    def __init__(self, parent_chat_box=None):
        super().__init__()
        self.parent_chat_box = parent_chat_box
        self.setAcceptDrops(True)

    def setParentChatBox(self, chat_box):
        """Set reference to parent chat box"""
        self.parent_chat_box = chat_box

    def dragEnterEvent(self, event):
        """Handle drag enter event - accept URLs"""
        if event.mimeData().hasUrls():
            # Check if any URL is a ZIP file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.zip'):
                    event.acceptProposedAction()
                    return
        # Otherwise use default behavior
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.zip'):
                    event.acceptProposedAction()
                    return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Handle drop event - process ZIP files"""
        if event.mimeData().hasUrls():
            zip_files = []

            # Collect all ZIP files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.zip') and os.path.exists(file_path):
                    zip_files.append(file_path)

            # Process ZIP files
            if zip_files and self.parent_chat_box:
                for zip_path in zip_files:
                    self.parent_chat_box._import_config_from_zip_path(zip_path)
                event.acceptProposedAction()
                return

        # Default behavior for non-ZIP files
        super().dropEvent(event)

def _load_default_prompts() -> Dict:
    """Load default prompts from configuration file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'default_prompts.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Config] Failed to load default_prompts.json: {e}")

    # Return minimal fallback if file doesn't exist
    return {
        "command_execution_prompt": "The command has been executed. Result:\n\n{result}\n\n",
        "command_retry_prompt": "【COMMAND EXECUTION FAILED】\nError: {error}\n\n",
        "final_summary_prompt": "You have reached the maximum number of iterations.\n",
        "system_prompts": {
            "default": "You are a helpful AI assistant."
        },
        "history_usage_guidance": ""
    }


def _load_default_config() -> Dict:
    """Load default configuration values from configuration file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'default_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Config] Failed to load default_config.json: {e}")

    # Return minimal fallback if file doesn't exist
    return {
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
            "stream": True,
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


# Load once at module level
_DEFAULT_PROMPTS = _load_default_prompts()
_DEFAULT_CONFIG = _load_default_config()


def _get_config_value(path: str, fallback=None):
    """
    Get configuration value from default_config.json using dot notation
    Example: _get_config_value('api.api_base', 'https://fallback.com')
    """
    keys = path.split('.')
    value = _DEFAULT_CONFIG
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return fallback
    return value if value is not None else fallback

@dataclass
class ConversationConfig:
    """Configuration for a conversation session"""
    api_key: str = ""
    api_base: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    stream: bool = True
    command_start: str = "YLDEXECUTE:"
    command_separator: str = "￥|"
    max_iterations: int = 15
    mcp_paths: List[str] = None
    enabled_mcp_tools: List[str] = None  # List of enabled MCP tool names
    system_prompt: str = ""

    def __post_init__(self):
        """Initialize default values for mutable fields and prompts from config"""
        if self.mcp_paths is None:
            self.mcp_paths = []
        if self.enabled_mcp_tools is None:
            self.enabled_mcp_tools = []

        # Load prompts from default_prompts.json if not explicitly provided
        # Check if prompts have their default values (empty strings would mean "use config file defaults")
        # We use hasattr to detect if these were set at all
        if not hasattr(self, '_prompts_initialized'):
            self.command_execution_prompt = _DEFAULT_PROMPTS.get('command_execution_prompt', '')
            self.command_retry_prompt = _DEFAULT_PROMPTS.get('command_retry_prompt', '')
            self.final_summary_prompt = _DEFAULT_PROMPTS.get('final_summary_prompt', '')
            self._prompts_initialized = True

    # Customizable prompts for command execution flow
    # These will be initialized in __post_init__ from default_prompts.json
    command_execution_prompt: str = ""  # Will be set from default_prompts.json
    command_retry_prompt: str = ""      # Will be set from default_prompts.json
    final_summary_prompt: str = ""      # Will be set from default_prompts.json


@dataclass
class ProcessingContext:
    """Context for AI processing operations"""
    conversation_name: str
    user_message: str
    ai_instance: Optional[AI] = None
    history_manager: Optional[AIHistoryManager] = None
    stream_callback: Optional[Callable] = None


# ============================================================================
# ENUM DEFINITIONS
# ============================================================================

class ProcessingState(Enum):
    """Processing state enumeration"""
    IDLE = auto()
    STREAMING = auto()
    EXECUTING_COMMAND = auto()
    AWAITING_SUMMARY = auto()
    ERROR = auto()
    LOADING = auto()  # Loading conversation


class BubbleType(Enum):
    """Message bubble type enumeration"""
    USER_MESSAGE = auto()
    AI_RESPONSE = auto()
    COMMAND_REQUEST = auto()
    COMMAND_RESULT = auto()
    FINAL_SUMMARY = auto()
    ERROR = auto()
    INFO = auto()


class MessageSource(Enum):
    """Message source for tracking"""
    USER = auto()
    AI = auto()
    SYSTEM = auto()


# ============================================================================
# ANIMATION MANAGER
# ============================================================================

class AnimationManager:
    """Manages UI animations"""
    
    @staticmethod
    def create_typing_animation(target, text: str) -> QPropertyAnimation:
        """Create typing animation"""
        animation = QPropertyAnimation(target, b"text")
        animation.setDuration(min(1000, len(text) * 30))
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        animation.setStartValue("")
        animation.setEndValue(text)
        return animation
    
    @staticmethod
    def create_fade_animation(target, fade_in: bool = True) -> QPropertyAnimation:
        """Create fade animation"""
        animation = QPropertyAnimation(target, b"windowOpacity")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        if fade_in:
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
        else:
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
        return animation


# ============================================================================
# CONTEXT MANAGER
# ============================================================================

class ConversationContextManager:
    """Manages conversation contexts and AI instances"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.conversation_ais: Dict[str, AI] = {}
        self.conversation_configs: Dict[str, ConversationConfig] = {}
        
    def get_ai_for_conversation(self, conversation_name: str) -> Optional[AI]:
        """Get or create AI instance for conversation"""
        if conversation_name in self.conversation_ais:
            return self.conversation_ais[conversation_name]

        try:
            config = self.load_conversation_config(conversation_name)
            if not config.api_key:
                return None

            # Show loading progress bar before creating AI
            if hasattr(self, 'loading_progress') and self.loading_progress:
                self.loading_progress.setVisible(True)
                # Force UI update
                QApplication.processEvents()

            # Pass conversation_name to create_ai_instance
            ai_instance = self.create_ai_instance(config, conversation_name)
            self.conversation_ais[conversation_name] = ai_instance

            # Hide loading progress bar after AI is ready
            if hasattr(self, 'loading_progress') and self.loading_progress:
                self.loading_progress.setVisible(False)

            return ai_instance

        except Exception as e:
            print(f"[ContextManager] Failed to create AI instance: {e}")
            # Hide loading progress on error
            if hasattr(self, 'loading_progress') and self.loading_progress:
                self.loading_progress.setVisible(False)
            return None
    
    def load_conversation_config(self, conversation_name: str) -> ConversationConfig:
        """Load configuration for conversation"""
        if conversation_name in self.conversation_configs:
            return self.conversation_configs[conversation_name]
        
        # Load from config manager
        config_data = self.config_manager.load_conversation_config(conversation_name)
        
        # Get API key from conversation-specific .confignore or environment
        api_key = (self.config_manager.load_api_key(conversation_name) or
                  os.environ.get("DEEPSEEK_API_KEY") or
                  os.environ.get("OPENAI_API_KEY") or
                  "")
        
        if config_data:
            config = ConversationConfig(
                api_key=api_key,
                api_base=config_data.get('api_base', _get_config_value('api.api_base')),
                model=config_data.get('model', _get_config_value('api.model')),
                temperature=config_data.get('temperature', _get_config_value('model_parameters.temperature')),
                max_tokens=config_data.get('max_tokens'),
                top_p=config_data.get('top_p', _get_config_value('model_parameters.top_p')),
                stream=config_data.get('stream', _get_config_value('model_parameters.stream')),
                command_start=config_data.get('command_start', _get_config_value('command_format.command_start')),
                command_separator=config_data.get('command_separator', _get_config_value('command_format.command_separator')),
                max_iterations=config_data.get('max_iterations', _get_config_value('execution.max_iterations')),
                mcp_paths=config_data.get('mcp_paths', _get_config_value('mcp.mcp_paths', [])),
                enabled_mcp_tools=config_data.get('enabled_mcp_tools', _get_config_value('mcp.enabled_mcp_tools', [])),
                system_prompt=config_data.get('system_prompt', ''),
                command_execution_prompt=config_data.get(
                    'command_execution_prompt',
                    ConversationConfig.command_execution_prompt
                ),
                command_retry_prompt=config_data.get(
                    'command_retry_prompt',
                    ConversationConfig.command_retry_prompt
                ),
                final_summary_prompt=config_data.get(
                    'final_summary_prompt',
                    ConversationConfig.final_summary_prompt
                )
            )
        else:
            config = ConversationConfig(
                api_key=api_key,
                system_prompt=_DEFAULT_PROMPTS.get('system_prompts', {}).get('default', "You are a helpful AI assistant.")
            )

        self.conversation_configs[conversation_name] = config
        return config
    
    def create_ai_instance(self, config: ConversationConfig, conversation_name: str = None) -> AI:
        """Create AI instance from configuration"""
        ai_kwargs = {
            'api_key': config.api_key,
            'api_base': config.api_base,
            'model': config.model,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'top_p': config.top_p,
            'stream': config.stream,
            'command_start': config.command_start,
            'command_separator': config.command_separator,
            'max_iterations': config.max_iterations,
            'mcp_paths': config.mcp_paths if config.mcp_paths is not None else [],
            'system_prompt': config.system_prompt,
            # Pass custom prompts
            'command_execution_prompt': config.command_execution_prompt,
            'command_retry_prompt': config.command_retry_prompt,
            'final_summary_prompt': config.final_summary_prompt,
            # CRITICAL: Pass chat_name
            'chat_name': conversation_name or 'default'
        }

        # Remove None values (but keep empty lists)
        ai_kwargs = {k: v for k, v in ai_kwargs.items() if v is not None and v != ''}

        ai_instance = AI(**ai_kwargs)

        # Load enabled_mcp_tools from config
        if config.enabled_mcp_tools:
            ai_instance.enabled_mcp_tools = set(config.enabled_mcp_tools)
            print(f"[ContextManager] Loaded {len(config.enabled_mcp_tools)} enabled tools from config")

        return ai_instance
    
    def clear_conversation(self, conversation_name: str):
        """Clear conversation data"""
        if conversation_name in self.conversation_ais:
            # Clean up MCP servers BEFORE deleting AI instance to avoid thread errors
            ai_instance = self.conversation_ais[conversation_name]
            try:
                if hasattr(ai_instance, 'cleanup_mcp_servers'):
                    ai_instance.cleanup_mcp_servers()
                    print(f"[ContextManager] Cleaned up MCP servers for {conversation_name}")
            except Exception as e:
                print(f"[ContextManager] Error cleaning up MCP servers: {e}")

            # Now delete the AI instance
            del self.conversation_ais[conversation_name]
        if conversation_name in self.conversation_configs:
            del self.conversation_configs[conversation_name]


# ============================================================================
# MESSAGE PROCESSING ENGINE
# ============================================================================

class MessageProcessor:
    """Handles message processing logic"""
    
    def __init__(self, context_manager: ConversationContextManager, 
                 history_manager: AIHistoryManager):
        self.context_manager = context_manager
        self.history_manager = history_manager
        
    def process_message(self, context: ProcessingContext) -> Dict[str, Any]:
        """Process a message and return results"""
        try:
            # Load AI instance
            ai_instance = self.context_manager.get_ai_for_conversation(
                context.conversation_name
            )
            
            if not ai_instance:
                return {
                    'success': False,
                    'error': "AI not initialized. Please check API key."
                }
            
            context.ai_instance = ai_instance
            
            # Load conversation history
            system_prompt = getattr(ai_instance, 'system_prompt', None)
            history = self.history_manager.load_history(
                context.conversation_name, 
                system_prompt
            )
            
            # Add user message to history
            history.append({
                "role": "user",
                "content": context.user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process based on streaming mode
            if ai_instance.stream:
                return self._process_streaming(context, history)
            else:
                return self._process_non_streaming(context, history)
                
        except Exception as e:
            print(f"[MessageProcessor] Error: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Processing error: {str(e)}"
            }
    
    def _process_streaming(self, context: ProcessingContext, 
                          history: List[Dict]) -> Dict[str, Any]:
        """Process message with streaming"""
        result = {
            'success': False,
            'streaming': True,
            'chunks': [],
            'full_response': "",
            'contains_command': False
        }
        
        def stream_callback(chunk: str):
            """Callback for streaming chunks"""
            if chunk and chunk.strip():
                result['chunks'].append(chunk)
                result['full_response'] += chunk
                if context.stream_callback:
                    context.stream_callback(chunk)
        
        try:
            # Process with streaming
            if hasattr(context.ai_instance, 'process_user_input_stream'):
                response = context.ai_instance.process_user_input_stream(
                    context.user_message,
                    history,
                    callback=stream_callback
                )

                # CRITICAL: Consume generator completely to ensure it finishes
                # This is necessary because the generator performs cleanup after yielding ""
                if hasattr(response, '__iter__') and not isinstance(response, (str, list, dict)):
                    print("[MessageProcessor] Consuming generator to completion...")
                    chunk_count = 0
                    for chunk in response:
                        chunk_count += 1
                        # The callback has already been invoked with the content
                        # We just need to consume the generator
                        if chunk_count % 10 == 0:
                            print(f"[MessageProcessor] Consumed {chunk_count} chunks...")

                    print(f"[MessageProcessor] Generator fully consumed after {chunk_count} chunks")
                else:
                    print("[MessageProcessor] Response is not a generator or is already consumed")

                # Check if there were any errors in the response
                full_response_lower = result['full_response'].lower()
                # Check for common error patterns
                error_patterns = [
                    'function does not exist',
                    'execution failed',
                    'error:',
                    'failed to',
                    'command execution error'
                ]

                has_error = any(pattern in full_response_lower for pattern in error_patterns)

                # Success if no errors found
                result['success'] = not has_error
                result['contains_command'] = self._check_for_command(
                    result['full_response'],
                    context.ai_instance
                )

                # If there was an error, add it to the result
                if has_error:
                    # Extract error message if possible
                    error_lines = [line for line in result['full_response'].split('\n')
                                 if any(pattern in line.lower() for pattern in error_patterns)]
                    if error_lines:
                        result['error'] = error_lines[0].strip()
                
            else:
                # Fallback to non-streaming
                return self._process_non_streaming(context, history)
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def _process_non_streaming(self, context: ProcessingContext,
                              history: List[Dict]) -> Dict[str, Any]:
        """Process message without streaming"""
        try:
            response = context.ai_instance.process_user_input_with_history(
                context.user_message,
                history
            )
            
            contains_command = self._check_for_command(
                response, 
                context.ai_instance
            )
            
            # Save to history
            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            self.history_manager.save_history(
                context.conversation_name,
                history
            )
            
            return {
                'success': True,
                'streaming': False,
                'full_response': response,
                'contains_command': contains_command
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_for_command(self, response: str, ai_instance: AI) -> bool:
        """Check if response contains a command"""
        if not hasattr(ai_instance, 'command_start'):
            return False
        return ai_instance.command_start in response
    
    def execute_command(self, context: ProcessingContext, 
                       response: str) -> Dict[str, Any]:
        """Execute command found in AI response"""
        try:
            # Extract command
            command_text = self._extract_command(response, context.ai_instance)
            if not command_text:
                return {
                    'success': False,
                    'error': "No valid command found"
                }
            
            # Parse command
            func_name, args = self._parse_command(
                command_text, 
                context.ai_instance
            )
            
            # Validate command exists
            if not hasattr(context.ai_instance, 'funcs') or func_name not in context.ai_instance.funcs:
                return {
                    'success': False,
                    'error': f"Tool '{func_name}' does not exist. Please use only available tools."
                }
            
            # Execute command
            command_result = context.ai_instance.exec_func(func_name, *args)
            
            # Save to history
            history = self.history_manager.load_history(
                context.conversation_name,
                getattr(context.ai_instance, 'system_prompt', None)
            )
            
            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            history.append({
                "role": "user",
                "content": f"Execution result: {command_result}",
                "timestamp": datetime.now().isoformat()
            })
            
            self.history_manager.save_history(
                context.conversation_name,
                history
            )
            
            return {
                'success': True,
                'command_text': command_text,
                'command_result': command_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Command execution error: {str(e)}"
            }
    
    def _extract_command(self, response: str, ai_instance: AI) -> Optional[str]:
        """Extract command from response"""
        if not hasattr(ai_instance, 'command_start'):
            return None
        
        start_idx = response.find(ai_instance.command_start)
        if start_idx == -1:
            return None
        
        end_idx = response.find('\n', start_idx)
        if end_idx == -1:
            end_idx = len(response)
        
        return response[start_idx:end_idx].strip()
    
    def _parse_command(self, command_text: str, ai_instance: AI) -> tuple:
        """Parse command text into function name and arguments"""
        command_text = command_text.replace(ai_instance.command_start, "").strip()
        tokens = command_text.split(ai_instance.command_separator)
        tokens = [t.strip() for t in tokens if t.strip()]
        
        if not tokens:
            return "", []
        
        func_name = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []
        
        return func_name, args


# ============================================================================
# PROCESSING WORKER (FOR NON-STREAMING)
# ============================================================================

class ProcessingWorker(QThread):
    """Worker thread for non-streaming processing"""
    
    # Signals
    processing_started = Signal()
    processing_completed = Signal(dict)  # {'response': str, 'contains_command': bool}
    processing_error = Signal(str)
    
    def __init__(self, processor: MessageProcessor, context: ProcessingContext):
        super().__init__()
        self.processor = processor
        self.context = context
        self._should_stop = False
        
    def run(self):
        """Main processing loop"""
        self.processing_started.emit()
        
        try:
            # Process message
            result = self.processor.process_message(self.context)
            
            if not result['success']:
                self.processing_error.emit(result.get('error', 'Unknown error'))
                return
            
            if not result['streaming']:
                # Non-streaming result is ready
                self.processing_completed.emit({
                    'response': result['full_response'],
                    'contains_command': result['contains_command']
                })
                
        except Exception as e:
            self.processing_error.emit(f"Worker error: {str(e)}")
    
    def stop(self):
        """Stop the worker"""
        self._should_stop = True
        if self.isRunning():
            self.wait(1000)


# ============================================================================
# STREAMING PROCESSOR
# ============================================================================

class StreamingProcessor:
    """Handles streaming processing with real-time updates"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.is_processing = False
        self.current_chunks = []
        
    def process_with_streaming(self, processor: MessageProcessor,
                              context: ProcessingContext):
        """Process with streaming and handle callbacks

        IMPORTANT: In streaming mode, the AI class handles command execution internally.
        We should NOT interfere with that process here. Just collect the stream chunks.
        """
        self.is_processing = True
        self.current_chunks = []

        def stream_callback(chunk: str):
            """Handle streaming chunks"""
            if not self.is_processing:
                return

            self.current_chunks.append(chunk)
            if self.parent:
                # Use signal instead of QMetaObject.invokeMethod for reliability
                self.parent.stream_chunk_signal.emit(chunk)

        context.stream_callback = stream_callback

        try:
            result = processor.process_message(context)

            # In streaming mode, the AI class handles everything internally
            # Just return the result without interfering
            if not result['success']:
                return result
            else:
                # Return the full response from streaming
                # The AI class has already handled commands and provided final output
                return {
                    'success': result.get('success', True),
                    'response': result.get('full_response', ''),
                    'command_executed': result.get('contains_command', False),  # Reflect actual command execution
                    'error': result.get('error')  # Include error if any
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.is_processing = False
    
    def _request_summary(self, processor: MessageProcessor, context: ProcessingContext,
                        original_response: str, command_result: str) -> tuple:
        """Request summary after command execution

        Returns:
            tuple: (summary, full_response_with_command)
        """
        try:
            # Load history
            history = processor.history_manager.load_history(
                context.conversation_name,
                getattr(context.ai_instance, 'system_prompt', None)
            )

            # Add summary request (without saving to history permanently)
            summary_request = "Based on the execution results, please provide a final summary in Chinese of what was found or accomplished. Be concise and clear. IMPORTANT: Do NOT repeat any previous responses or summaries. Only provide NEW, original summary content. Do NOT include phrases like 'as mentioned before' or repeat the same content multiple times.\n\nFORMAT REQUIREMENT: Use proper line breaks and structure. Separate different points with blank lines. Do NOT cram everything into one single paragraph."
            temp_history = history.copy()
            temp_history.append({
                "role": "user",
                "content": summary_request,
                "timestamp": datetime.now().isoformat()
            })

            # Get summary (without saving the summary request/response to history)
            summary = context.ai_instance.process_user_input_with_history(
                summary_request,
                temp_history
            )

            # Detect and remove repetitive content from summary
            # Split into sentences for better deduplication
            sentences = []
            for line in summary.split('\n'):
                # Split by common sentence delimiters
                parts = line.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                sentences.extend([p.strip() for p in parts if p.strip()])

            # Remove duplicate sentences
            seen_sentences = set()
            unique_sentences = []
            for sentence in sentences:
                if sentence not in seen_sentences:
                    seen_sentences.add(sentence)
                    unique_sentences.append(sentence)

            # Reconstruct summary
            deduplicated_summary = '。'.join(unique_sentences)
            if deduplicated_summary and not deduplicated_summary.endswith('。'):
                deduplicated_summary += '。'

            # If deduplication removed too much, use original with line-based dedup
            if len(deduplicated_summary) < len(summary) * 0.3:
                lines = summary.split('\n')
                seen_lines = set()
                unique_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line and stripped_line not in seen_lines:
                        seen_lines.add(stripped_line)
                        unique_lines.append(line)
                    elif stripped_line and stripped_line in seen_lines:
                        continue
                    else:
                        unique_lines.append(line)
                deduplicated_summary = '\n'.join(unique_lines)

            # Combine original response (with command) and summary for display
            # Extract clean response without command for display
            clean_response = original_response
            if context.ai_instance and hasattr(context.ai_instance, 'command_start'):
                cmd_start = context.ai_instance.command_start
                if cmd_start in clean_response:
                    # Remove command line from response
                    lines = clean_response.split('\n')
                    clean_response = '\n'.join([
                        line for line in lines
                        if cmd_start not in line
                    ]).strip()

            full_response = f"{clean_response}\n\n{deduplicated_summary}" if clean_response else deduplicated_summary

            # Only save the combined response, not the summary exchange
            history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            })

            processor.history_manager.save_history(
                context.conversation_name,
                history
            )

            return summary, full_response

        except Exception as e:
            return f"Summary error: {str(e)}", original_response
    
    def stop(self):
        """Stop streaming processing"""
        self.is_processing = False


# ============================================================================
# MESSAGE BUBBLE (OPTIMIZED VERSION)
# ============================================================================

class ModernMessageBubble(QWidget):
    """Modern message bubble with improved performance"""
    
    def __init__(self, message: str = "", bubble_type: BubbleType = BubbleType.AI_RESPONSE,
                 timestamp: str = None, parent=None):
        super().__init__(parent)

        self.message = message
        self.bubble_type = bubble_type
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.current_text = message
        self.is_streaming = False

        # Markdown renderer
        self.renderer = get_renderer()
        self.enable_markdown = True  # Enable markdown rendering for AI responses

        self._init_ui()
        self._apply_styling()

        # Initialize text with markdown rendering
        if message:
            self.update_text(message)

        self._update_size_hint()
    
    def _init_ui(self):
        """Initialize UI components"""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Bubble container
        self.bubble_container = QFrame()
        self.bubble_container.setObjectName("bubbleContainer")
        self.bubble_container.setFrameStyle(QFrame.NoFrame)
        # Set fixed minimum width for AI bubbles to prevent jitter
        if self.bubble_type != BubbleType.USER_MESSAGE:
            self.bubble_container.setMinimumWidth(450)
            self.bubble_container.setMaximumWidth(800)

        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(16, 12, 16, 6)
        bubble_layout.setSpacing(0)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML rendering
        self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.message_label.setOpenExternalLinks(True)  # Allow opening links
        
        # Timestamp
        timestamp_layout = QHBoxLayout()
        timestamp_layout.setContentsMargins(0, 0, 0, 0)

        self.timestamp_label = QLabel(self.timestamp)
        self.timestamp_label.setObjectName("timestamp")
        self.timestamp_label.setAlignment(Qt.AlignRight)
        self.timestamp_label.setAlignment(Qt.AlignRight)
        # Remove any extra margins from timestamp
        self.timestamp_label.setContentsMargins(0, 0, 0, 0)
        
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(self.timestamp_label)
        
        # Assemble
        bubble_layout.addWidget(self.message_label)
        bubble_layout.addLayout(timestamp_layout)
        
        # Add to main layout with alignment
        container_layout = QHBoxLayout()
        if self.bubble_type == BubbleType.USER_MESSAGE:
            container_layout.addStretch()
            container_layout.addWidget(self.bubble_container)
        else:
            container_layout.addWidget(self.bubble_container)
            container_layout.addStretch()
        
        main_layout.addLayout(container_layout)
    
    def _apply_styling(self):
        """Apply styling based on bubble type"""
        styles = {
            BubbleType.USER_MESSAGE: """
                #bubbleContainer {
                    background-color: #0084FF;
                    border-radius: 18px 4px 18px 18px;
                }
                QLabel { color: white; }
                QLabel#timestamp { color: rgba(255, 255, 255, 0.7); }
            """,
            
            BubbleType.COMMAND_REQUEST: """
                #bubbleContainer {
                    background-color: #1A5F1A;
                    border-radius: 4px 18px 18px 18px;
                    border: 1px solid #0F4F0F;
                }
                QLabel { color: #E0FFE0; }
                QLabel#timestamp { color: rgba(224, 255, 224, 0.7); }
            """,
            
            BubbleType.COMMAND_RESULT: """
                #bubbleContainer {
                    background-color: #2A4A6A;
                    border-radius: 4px 18px 18px 18px;
                    border: 1px solid #1A3A5A;
                }
                QLabel { color: #E0E0FF; }
                QLabel#timestamp { color: rgba(224, 224, 255, 0.7); }
            """,
            
            BubbleType.FINAL_SUMMARY: """
                #bubbleContainer {
                    background-color: #4A2A6A;
                    border-radius: 4px 18px 18px 18px;
                    border: 1px solid #3A1A5A;
                }
                QLabel { color: #F0E0FF; }
                QLabel#timestamp { color: rgba(240, 224, 255, 0.7); }
            """,
            
            BubbleType.ERROR: """
                #bubbleContainer {
                    background-color: #6A2A2A;
                    border-radius: 4px 18px 18px 18px;
                    border: 1px solid #5A1A1A;
                }
                QLabel { color: #FFE0E0; }
                QLabel#timestamp { color: rgba(255, 224, 224, 0.7); }
            """,
            
            BubbleType.INFO: """
                #bubbleContainer {
                    background-color: #2A4A4A;
                    border-radius: 4px 18px 18px 18px;
                    border: 1px solid #1A3A3A;
                }
                QLabel { color: #E0FFFF; }
                QLabel#timestamp { color: rgba(224, 255, 255, 0.7); }
            """
        }
        
        base_style = """
            QLabel {
                background-color: transparent;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.4;
            }
            QLabel#timestamp {
                font-size: 11px;
                font-weight: 300;
            }
        """
        
        style_sheet = styles.get(self.bubble_type, """
            #bubbleContainer {
                background-color: #2D2D2D;
                border-radius: 4px 18px 18px 18px;
                border: 1px solid #333333;
            }
            QLabel { color: #E0E0E0; }
            QLabel#timestamp { color: rgba(224, 224, 224, 0.6); }
        """)
        
        self.bubble_container.setStyleSheet(style_sheet + base_style)
    
    def update_text(self, new_text: str, force_plain: bool = False):
        """
        Update bubble text with optional markdown rendering

        Args:
            new_text: New text to display
            force_plain: Force plain text (no markdown rendering)
        """
        text_length = len(new_text)

        # Smart rendering strategy based on text length
        if text_length > 100000:  # Very long text (>100k)
            print(f"[MessageBubble] Very long text ({text_length} chars), using plain text")
            # Use plain text for very long content to prevent crashes
            display_text = self.renderer._escape_text(new_text)
        elif text_length > 50000:  # Long text (50k-100k)
            print(f"[MessageBubble] Long text ({text_length} chars), truncating")
            # Truncate to prevent rendering issues
            truncated = new_text[:50000]
            display_text = self._render_with_fallback(truncated + "\n\n... (Text truncated at 50,000 characters to prevent crash)")
        else:
            # Normal rendering for manageable texts
            display_text = self._render_with_fallback(new_text, force_plain)

        self.message_label.setText(display_text)
        self.timestamp_label.setText(datetime.now().strftime("%H:%M"))
        self._update_size_hint()

    def _render_with_fallback(self, text: str, force_plain: bool = False) -> str:
        """
        Render markdown with automatic fallback to plain text on error
        """
        # Determine if we should render markdown
        should_render = (
            self.enable_markdown and
            not force_plain and
            self.bubble_type != BubbleType.USER_MESSAGE and
            self.bubble_type not in [BubbleType.COMMAND_REQUEST, BubbleType.ERROR]
        )

        if not should_render:
            return self.renderer._escape_text(text)

        try:
            return self.renderer.render(text, mode=RenderMode.FINAL)
        except Exception as e:
            print(f"[MessageBubble] Markdown render failed, using plain text: {e}")
            return self.renderer._escape_text(text)

    def append_text(self, additional_text: str, render_html: bool = False):
        """
        Append text (for streaming) with optional incremental rendering

        Args:
            additional_text: Text to append
            render_html: Whether to render as HTML (ignored, markdown only rendered on finalize)
        """
        self.current_text += additional_text

        # Always use plain text during streaming to avoid flickering
        # Markdown will only be rendered when finalize_rendering() is called
        display_text = self.renderer._escape_text(self.current_text)

        self.message_label.setText(display_text)
        self.timestamp_label.setText(datetime.now().strftime("%H:%M"))

        # Don't call _update_size_hint during streaming to prevent jitter
        # Size will be updated in finalize_rendering()

    def finalize_rendering(self):
        """Finalize markdown rendering after streaming completes"""
        # Stop streaming mode to allow size updates
        self.is_streaming = False

        # Enable markdown for all AI-related messages (not user messages)
        should_render = (
            self.enable_markdown and
            self.bubble_type != BubbleType.USER_MESSAGE and
            self.bubble_type not in [BubbleType.COMMAND_REQUEST, BubbleType.ERROR, BubbleType.INFO]
        )

        if should_render:
            final_html = self.renderer.finalize_rendering(self.current_text)
            self.message_label.setText(final_html)
            self._update_size_hint()
    
    def _update_size_hint(self):
        """Update size based on content"""
        # Only update if not streaming to avoid jitter
        if self.is_streaming:
            return

        # Let QLabel calculate its own size based on rendered content
        self.message_label.adjustSize()

        # Get the height from the label's size hint
        label_height = self.message_label.sizeHint().height()

        # Calculate total height with padding and timestamp
        total_height = label_height + 20 + 8  # Label height + timestamp + margin

        # Set minimum height but allow it to expand if needed
        self.setMinimumHeight(max(70, total_height))

    def sizeHint(self):
        # Use the message label's size hint as base
        base_height = self.message_label.sizeHint().height()
        total_height = base_height + 20 + 8  # + timestamp + margins
        return QSize(450, max(70, total_height))


# ============================================================================
# MAIN CHAT BOX (REFACTORED)
# ============================================================================

class ModernChatBox(QWidget):
    """Refactored main chat interface"""

    # Signals for thread-safe UI updates
    finalize_response = Signal(str)
    stream_chunk_signal = Signal(str)

    def __init__(self):
        super().__init__()
        
        # Core managers
        self.config_manager = ConfigManager()
        self.history_manager = AIHistoryManager()
        self.chat_data_manager = ChatDataManager()
        self.context_manager = ConversationContextManager(self.config_manager)
        self.message_processor = MessageProcessor(self.context_manager, self.history_manager)
        self.streaming_processor = StreamingProcessor(self)
        
        # State
        self.current_state = ProcessingState.IDLE
        self.current_conversation = None  # Will be set when loading chats
        
        # UI references
        self.current_stream_bubble = None
        self.last_command_bubble = None
        self.command_bubbles = []  # Track all command bubbles for cleanup
        
        # Threading
        self.processing_worker = None
        self.processing_thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Data
        self.chat_list_names = self.config_manager.load_chat_list() or []
        self.chat_records = self.config_manager.load_chat_history()
        
        # Dialogs
        self.init_dialog = None
        self.settings_dialog = None
        
        # Initialize
        self._initialize_ui()

        # Load chat list (will show empty state if no chats)
        self._load_chat_list_to_ui()

        # Load first chat if available
        if self.chat_list_names:
            # Get last active chat from config or first chat
            last_active = self.config_manager.load_last_active_chat()
            if last_active and last_active in self.chat_list_names:
                items = self.chat_list.findItems(last_active, Qt.MatchFlag.MatchExactly)
                if items:
                    self.switch_chat_target(items[0])
            elif self.chat_list_names:
                # Load first chat
                items = self.chat_list.findItems(self.chat_list_names[0], Qt.MatchFlag.MatchExactly)
                if items:
                    self.switch_chat_target(items[0])

        self._initialize_ai()

        # Connect signals
        # Use QueuedConnection to ensure slots execute in the main thread
        self.finalize_response.connect(self._finalize_streaming_response, Qt.QueuedConnection)
        self.stream_chunk_signal.connect(self.handle_stream_chunk, Qt.QueuedConnection)

        print("[ModernChatBox] Initialization complete")
    
    # ============================================================================
    # UI INITIALIZATION
    # ============================================================================
    
    def _initialize_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(f'{i18n.tr("app_name")} - AI Assistant')
        self.setGeometry(100, 100, 1400, 900)
        
        # Set icon
        icon_path = "assets/logo.ico"
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Apply theme
        self._apply_dark_theme()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add components
        self.title_bar = self._create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar = self._create_sidebar()
        content_layout.addWidget(self.sidebar)
        
        self.chat_area = self._create_chat_area()
        content_layout.addWidget(self.chat_area, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        self.status_bar = self._create_status_bar()
        main_layout.addWidget(self.status_bar)
        
        # Load initial data
        self._load_chat_list_to_ui()
        
        # Select first chat
        if self.chat_list.count() > 0:
            self.switch_chat_target(self.chat_list.item(0))
    
    def _apply_dark_theme(self):
        """Apply dark theme"""
        # Get base markdown CSS
        markdown_css = MarkdownRenderer.get_base_css()

        self.setStyleSheet(f"""
            QWidget {{
                background-color: #1E1E1E;
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }}
            QScrollBar:vertical {{
                background-color: #2A2A2A;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #404040;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #4A4A4A;
            }}

            /* Markdown Content Styles */
            {markdown_css}
        """)
    
    def _create_title_bar(self):
        """Create title bar"""
        title_bar = QWidget()
        title_bar.setFixedHeight(52)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                border-bottom: 1px solid #333333;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # App icon
        icon_label = QLabel("⚡")
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #4A9CFF;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        
        # App title
        title_label = QLabel(i18n.tr("app_name"))
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                background-color: transparent;
                letter-spacing: 0.5px;
            }
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()
        
        return title_bar
    
    def _create_sidebar(self):
        """Create sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-right: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # New chat button
        new_chat_btn = QPushButton(i18n.tr("new_chat"))
        new_chat_btn.setFixedHeight(56)
        new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9CFF;
                color: white;
                border: none;
                font-size: 14px;
                font-weight: 500;
                margin: 16px;
                border-radius: 12px;
                padding: 0px 20px;
            }
            QPushButton:hover { background-color: #5AACFF; }
            QPushButton:pressed { background-color: #3A8CEE; }
        """)
        new_chat_btn.clicked.connect(self._add_new_chat)
        layout.addWidget(new_chat_btn)
        
        # Conversations label
        chats_label = QLabel(i18n.tr("conversations"))
        chats_label.setFixedHeight(48)
        chats_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                font-weight: 600;
                padding-left: 20px;
                background-color: transparent;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(chats_label)

        # Chat list - use custom DraggableListWidget for ZIP file drag-drop support
        self.chat_list = DraggableListWidget(parent_chat_box=self)
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 14px;
                padding: 4px 8px;
            }
            QListWidget::item {
                color: #CCCCCC;
                padding: 12px 16px;
                border-radius: 8px;
                margin: 2px 8px;
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: rgba(45, 45, 45, 0.8);
                color: #FFFFFF;
                padding-left: 20px;
            }
            QListWidget::item:selected {
                background-color: #4A9CFF;
                color: white;
                font-weight: 500;
                padding-left: 24px;
            }
        """)
        self.chat_list.itemClicked.connect(self.switch_chat_target)
        layout.addWidget(self.chat_list, 1)
        
        # Bottom actions
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(280)
        bottom_widget.setStyleSheet("background-color: transparent;")
        
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(16, 16, 16, 16)
        bottom_layout.setSpacing(8)
        
        # Action buttons
        actions = [
            (i18n.tr("settings"), self._open_settings, "#4A4A4A"),
            (i18n.tr("initialize"), self._show_init_dialog, "#2A7CDD"),
            (i18n.tr("tools"), self._show_tools_list, "#3A3A3A"),
            (i18n.tr("export_chat"), self._export_chat_history, "#3A3A3A"),
            (i18n.tr("import_config"), self._import_config_from_zip, "#2E7D32"),
            (i18n.tr("delete_chat"), self._delete_current_chat, "#D32F2F"),
            (i18n.tr("clear_chat"), self._clear_current_chat, "#666666")
        ]
        
        for text, callback, color in actions:
            btn = self._create_sidebar_button(text, callback, color)
            bottom_layout.addWidget(btn)
        
        bottom_layout.addStretch()
        layout.addWidget(bottom_widget)
        
        return sidebar
    
    def _create_sidebar_button(self, text: str, callback, color: str):
        """Create sidebar button"""
        button = QPushButton(text)
        button.setFixedHeight(44)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #E0E0E0;
                border: none;
                text-align: left;
                padding-left: 16px;
                font-size: 14px;
                font-weight: 400;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #3D3D3D;
                color: white;
                padding-left: 20px;
            }}
        """)
        button.clicked.connect(callback)
        return button
    
    def _create_chat_area(self):
        """Create main chat area"""
        chat_widget = QWidget()
        chat_widget.setStyleSheet("background-color: #1E1E1E;")
        
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat title
        self.chat_title = QLabel(i18n.tr("general_chat"))
        self.chat_title.setFixedHeight(68)
        self.chat_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 600;
                padding-left: 28px;
                background-color: transparent;
                border-bottom: 1px solid #333333;
            }
        """)
        layout.addWidget(self.chat_title)
        
        # Message area
        self.message_scroll = QScrollArea()
        self.message_scroll.setWidgetResizable(True)
        self.message_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1E1E1E;
                border: none;
            }
        """)
        
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background-color: #1E1E1E;")
        
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(20, 20, 20, 20)
        self.message_layout.setSpacing(12)
        self.message_layout.addStretch()
        
        self.message_scroll.setWidget(self.message_container)
        layout.addWidget(self.message_scroll, 1)
        
        # Input area
        input_widget = QWidget()
        input_widget.setFixedHeight(160)
        input_widget.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-top: 1px solid #333333;
            }
        """)
        
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(20, 16, 20, 16)
        input_layout.setSpacing(12)
        
        # Input text box
        self.input_text = DragDropTextEdit()
        self.input_text.setParentChatBox(self)
        self.input_text.setPlaceholderText(i18n.tr("type_message"))
        self.input_text.setAcceptRichText(False)
        self.input_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction |
            Qt.TextInteractionFlag.TextSelectableByKeyboard |
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D2D;
                border: 2px solid #333333;
                border-radius: 12px;
                color: #FFFFFF;
                padding: 16px;
                font-size: 14px;
                selection-background-color: #4A9CFF;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #4A9CFF;
                background-color: #2A2A2A;
            }
            QTextEdit::placeholder {
                color: #777777;
                font-style: italic;
            }
        """)
        self.input_text.setMaximumHeight(80)
        input_layout.addWidget(self.input_text, 1)
        
        # Button layout
        button_layout = QHBoxLayout()

        button_layout.addStretch()

        # Stop button
        self.stop_button = QPushButton(i18n.tr("stop"))
        self.stop_button.setFixedHeight(40)
        self.stop_button.setVisible(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4757;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #FF5E6D; }
            QPushButton:pressed { background-color: #E63E4D; }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """)
        self.stop_button.clicked.connect(self._stop_processing)
        button_layout.addWidget(self.stop_button)
        
        # Send button
        self.send_button = QPushButton(i18n.tr("send"))
        self.send_button.setFixedHeight(40)
        self.send_button.setShortcut('Ctrl+Return')
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4A9CFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #5AACFF; }
            QPushButton:pressed { background-color: #3A8CEE; }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """)
        self.send_button.clicked.connect(self._send_message)
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        layout.addWidget(input_widget)
        
        return chat_widget
    
    def _create_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #252525;
                color: #AAAAAA;
                font-size: 11px;
                font-weight: 400;
                border-top: 1px solid #333333;
                padding: 8px 16px;
            }
        """)

        # Create loading progress bar (indeterminate)
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # Indeterminate mode
        self.loading_progress.setMaximumWidth(200)
        self.loading_progress.setMaximumHeight(16)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
                border-radius: 8px;
            }
            QProgressBar::chunk {
                background-color: #4A9CFF;
                border-radius: 8px;
            }
        """)
        self.loading_progress.setVisible(False)

        # Add progress bar to status bar
        status_bar.addPermanentWidget(self.loading_progress)

        status_bar.showMessage("Lynexus AI | Not connected")
        return status_bar
    
    def _load_chat_list_to_ui(self):
        """Load chat list to UI"""
        self.chat_list.clear()

        # Show empty state if no chats
        if not self.chat_list_names:
            self._show_empty_state()
            return

        for name in self.chat_list_names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)

            if name not in self.chat_records:
                self.chat_records[name] = []

            self.chat_list.addItem(item)

    def _show_empty_state(self):
        """Show empty state when no conversations exist"""
        self.chat_list.clear()
        self.current_conversation = None
        self.chat_title.setText("")

        # Clear message display
        self._clear_message_display()

        # Show empty state message in message area
        empty_message = QLabel(
            "📝 No conversations yet\n\n"
            "Click 'New Chat' to create your first conversation"
        )
        empty_message.setAlignment(Qt.AlignCenter)
        empty_message.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                padding: 40px;
                background-color: transparent;
            }
        """)

        # Add empty message to display
        self.message_layout.insertWidget(0, empty_message)
        self.message_container.adjustSize()
    
    # ============================================================================
    # MESSAGE PROCESSING
    # ============================================================================
    
    def _send_message(self):
        """Send message to AI"""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        if self.current_state != ProcessingState.IDLE:
            return
        
        # Check AI initialization
        ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
        if not ai_instance:
            QMessageBox.warning(self, "Error", "AI not initialized. Please check API key.")
            return
        
        try:
            # Update state
            self.current_state = ProcessingState.STREAMING
            self.send_button.setEnabled(False)
            self.stop_button.setVisible(True)
            self.input_text.clear()

            # Initialize chat records for new conversation if needed
            if self.current_conversation not in self.chat_records:
                self.chat_records[self.current_conversation] = []

            # Save user message
            current_time = datetime.now().isoformat()
            self.chat_records[self.current_conversation].append({
                "text": message,
                "is_sender": True,
                "timestamp": current_time
            })
            
            # Display user message
            self._add_message_to_display(
                message=message,
                bubble_type=BubbleType.USER_MESSAGE,
                timestamp=current_time
            )
            
            QApplication.processEvents()
            
            # Start processing
            self._start_message_processing(message, ai_instance)
            
        except Exception as e:
            print(f"[ModernChatBox] Send message error: {e}")
            traceback.print_exc()
            self._reset_state()
    
    def _start_message_processing(self, message: str, ai_instance: AI):
        """Start message processing based on mode"""
        context = ProcessingContext(
            conversation_name=self.current_conversation,
            user_message=message,
            ai_instance=ai_instance,
            history_manager=self.history_manager
        )
        
        if ai_instance.stream:
            # Streaming mode
            self._process_streaming(context)
        else:
            # Non-streaming mode (use thread)
            self._process_non_streaming(context)
    
    def _process_streaming(self, context: ProcessingContext):
        """Process message with streaming"""
        # Run in thread pool to avoid blocking
        future = self.processing_thread_pool.submit(
            self._execute_streaming_processing,
            context
        )
        future.add_done_callback(self._handle_streaming_result)
    
    def _execute_streaming_processing(self, context: ProcessingContext):
        """Execute streaming processing in background"""
        return self.streaming_processor.process_with_streaming(
            self.message_processor,
            context
        )
    
    def _handle_streaming_result(self, future):
        """Handle streaming result from thread pool"""
        try:
            result = future.result()
            # Removed verbose debug print to reduce terminal clutter

            if not result['success']:
                self._handle_processing_error(result.get('error', 'Unknown error'))
                return

            # In streaming mode, AI handles everything internally
            # Just finalize the current bubble if it exists
            response_text = result.get('response', '')
            print(f"[ChatBox] Finalizing streaming response, text length: {len(response_text)}")

            # Save AI conversation history (this is critical for context memory)
            if self.current_conversation:
                ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
                if ai_instance and hasattr(ai_instance, 'conv_his') and ai_instance.conv_his:
                    print(f"[ChatBox] Saving AI history with {len(ai_instance.conv_his)} messages")
                    self.history_manager.save_history(
                        self.current_conversation,
                        ai_instance.conv_his
                    )

            # Use Signal to ensure UI operations happen on main thread
            # This is the most reliable way for cross-thread communication in Qt
            print("[ChatBox] Emitting finalize_response signal")
            self.finalize_response.emit(response_text)

        except Exception as e:
            print(f"[ChatBox] Error in _handle_streaming_result: {e}")
            traceback.print_exc()
            self._handle_processing_error(f"Streaming error: {str(e)}")

    @Slot(str)
    def _finalize_streaming_response(self, response_text: str):
        """Finalize streaming response in main thread"""
        try:
            print(f"[ChatBox] _finalize_streaming_response called, current_stream_bubble: {self.current_stream_bubble}")

            # Clean and process response text
            display_text = self._clean_response_text(response_text)

            if self.current_stream_bubble:
                self.current_stream_bubble.is_streaming = False
                # 注意：streaming过程中所有内容已经通过handle_stream_chunk添加到气泡了
                # 这里只需要finalize渲染,不需要再更新文本(除非气泡为空)
                if not self.current_stream_bubble.current_text.strip():
                    # 气泡为空时才使用display_text更新
                    if display_text:
                        self.current_stream_bubble.update_text(display_text)

                # 总是finalize markdown渲染
                self.current_stream_bubble.finalize_rendering()

                # 保存聊天记录
                bubble_text = self.current_stream_bubble.current_text
                if bubble_text and bubble_text.strip():
                    bubble_type = self.current_stream_bubble.bubble_type
                    self._save_chat_record(bubble_text, False, bubble_type)
                else:
                    # No display text but have bubble, save its current content
                    if hasattr(self.current_stream_bubble, 'message_label'):
                        bubble_text = self.current_stream_bubble.message_label.text()
                        if bubble_text and bubble_text.strip():
                            from PySide6.QtGui import QTextDocument
                            doc = QTextDocument()
                            doc.setHtml(bubble_text)
                            plain_text = doc.toPlainText()
                            bubble_type = self.current_stream_bubble.bubble_type
                            self._save_chat_record(plain_text, False, bubble_type)
            else:
                # Should have been created via streaming chunks
                print("[ChatBox] No stream bubble found, showing final response")
                self._show_final_response(display_text)

            print("[ChatBox] Calling _reset_state()")
            self._reset_state()
            print("[ChatBox] _reset_state() completed")
        except Exception as e:
            print(f"[ChatBox] Error finalizing response: {e}")
            traceback.print_exc()

    def _clean_response_text(self, response_text: str) -> str:
        """Clean response text by removing commands and duplicates"""
        # Get command_start and command_separator from current AI instance (use config defaults as fallback)
        cmd_start = ConversationConfig.command_start  # Use config default
        cmd_sep = ConversationConfig.command_separator  # Use config default
        if self.current_conversation:
            ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
            if ai_instance:
                if hasattr(ai_instance, 'command_start'):
                    cmd_start = ai_instance.command_start
                if hasattr(ai_instance, 'command_separator'):
                    cmd_sep = ai_instance.command_separator

        # Step 1: Remove all command lines
        lines = response_text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip command lines using configured command_start and command_separator
            if cmd_start in line or line.strip().startswith(cmd_sep):
                continue
            cleaned_lines.append(line)

        # Step 2: Join and split by "最终总结" to find the last one
        text = '\n'.join(cleaned_lines)

        # Find all "最终总结" occurrences
        if '**最终总结**' in text:
            parts = text.split('**最终总结**')
            # Take only the last "最终总结" section
            text = '**最终总结**' + parts[-1]

        # Step 3: Clean up extra whitespace while preserving newlines
        lines = text.split('\n')
        final_lines = []
        prev_empty = False

        for line in lines:
            stripped = line.rstrip()  # Only strip trailing whitespace, preserve leading
            if stripped:
                final_lines.append(stripped)
                prev_empty = False
            elif not prev_empty:
                # Keep single empty lines between paragraphs
                final_lines.append('')
                prev_empty = True

        # Step 4: Rejoin with proper line breaks
        display_text = '\n'.join(final_lines)

        # Remove any trailing whitespace
        display_text = display_text.rstrip()

        return display_text
    
    def _process_non_streaming(self, context: ProcessingContext):
        """Process message without streaming"""
        # Clear any existing worker
        if self.processing_worker:
            self.processing_worker.stop()
        
        # Create and start worker
        self.processing_worker = ProcessingWorker(self.message_processor, context)
        
        self.processing_worker.processing_started.connect(
            self._on_non_streaming_started
        )
        self.processing_worker.processing_completed.connect(
            self._on_non_streaming_completed
        )
        self.processing_worker.processing_error.connect(
            self._handle_processing_error
        )
        
        self.processing_worker.start()
    
    def _on_non_streaming_started(self):
        """Handle non-streaming processing started"""
        # Show progress indicator
        self._add_message_to_display(
            message="Processing...",
            bubble_type=BubbleType.INFO
        )
    
    def _on_non_streaming_completed(self, result: dict):
        """Handle non-streaming processing completed"""
        # Remove progress indicator
        self._remove_last_bubble()
        
        response = result.get('response', '')
        contains_command = result.get('contains_command', False)
        
        if contains_command:
            # Handle command execution
            self._handle_non_streaming_command(response)
        else:
            # Show regular response
            self._show_final_response(response)
        
        self._reset_state()
    
    def _handle_non_streaming_command(self, response: str):
        """Handle command in non-streaming mode"""
        # Show command bubble and save reference
        command_bubble = self._add_message_to_display(
            message=f"🔧 Executing command...",
            bubble_type=BubbleType.COMMAND_REQUEST
        )
        self.last_command_bubble = command_bubble
        self.command_bubbles.append(command_bubble)  # Track for cleanup

        # Execute command
        context = ProcessingContext(
            conversation_name=self.current_conversation,
            user_message="",
            ai_instance=self.context_manager.get_ai_for_conversation(self.current_conversation)
        )

        command_result = self.message_processor.execute_command(context, response)

        # Update command bubble with result
        if command_result['success']:
            result_text = command_result['command_result']
            display_result = result_text[:100] + "..." if len(result_text) > 100 else result_text
            command_bubble.update_text(
                f"✅ Command executed successfully\n{display_result}"
            )

            # Request and show summary
            summary, full_response = self._request_summary_after_command(
                response,
                command_result['command_result']
            )

            self._show_final_summary(summary, full_response)

        else:
            command_bubble.update_text(
                f"❌ Command failed\n{command_result['error']}"
            )
            command_bubble.bubble_type = BubbleType.ERROR
            command_bubble._apply_styling()
            self.last_command_bubble = None  # Clear reference on error
    
    def _request_summary_after_command(self, original_response: str,
                                      command_result: str) -> tuple:
        """Request summary after command execution

        Returns:
            tuple: (summary, full_response_with_command)
        """
        try:
            ai_instance = self.context_manager.get_ai_for_conversation(
                self.current_conversation
            )

            # Load history
            history = self.history_manager.load_history(
                self.current_conversation,
                getattr(ai_instance, 'system_prompt', None)
            )

            # Add summary request (without saving to history permanently)
            summary_request = "Based on the execution results, please provide a final summary in Chinese of what was found or accomplished. Be concise and clear. IMPORTANT: Do NOT repeat any previous responses or summaries. Only provide NEW, original summary content. Do NOT include phrases like 'as mentioned before' or repeat the same content multiple times.\n\nFORMAT REQUIREMENT: Use proper line breaks and structure. Separate different points with blank lines. Do NOT cram everything into one single paragraph."
            temp_history = history.copy()
            temp_history.append({
                "role": "user",
                "content": summary_request,
                "timestamp": datetime.now().isoformat()
            })

            # Get summary (without saving the summary request/response to history)
            summary = ai_instance.process_user_input_with_history(
                summary_request,
                temp_history
            )

            # Detect and remove repetitive content from summary
            # Split into sentences for better deduplication
            sentences = []
            for line in summary.split('\n'):
                # Split by common sentence delimiters
                parts = line.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                sentences.extend([p.strip() for p in parts if p.strip()])

            # Remove duplicate sentences
            seen_sentences = set()
            unique_sentences = []
            for sentence in sentences:
                if sentence not in seen_sentences:
                    seen_sentences.add(sentence)
                    unique_sentences.append(sentence)

            # Reconstruct summary
            deduplicated_summary = '。'.join(unique_sentences)
            if deduplicated_summary and not deduplicated_summary.endswith('。'):
                deduplicated_summary += '。'

            # If deduplication removed too much, use original with line-based dedup
            if len(deduplicated_summary) < len(summary) * 0.3:
                lines = summary.split('\n')
                seen_lines = set()
                unique_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line and stripped_line not in seen_lines:
                        seen_lines.add(stripped_line)
                        unique_lines.append(line)
                    elif stripped_line and stripped_line in seen_lines:
                        continue
                    else:
                        unique_lines.append(line)
                deduplicated_summary = '\n'.join(unique_lines)

            # Combine original response (with command) and summary for display
            # Extract clean response without command for display
            clean_response = original_response
            if ai_instance and hasattr(ai_instance, 'command_start'):
                cmd_start = ai_instance.command_start
                if cmd_start in clean_response:
                    # Remove command line from response
                    lines = clean_response.split('\n')
                    clean_response = '\n'.join([
                        line for line in lines
                        if cmd_start not in line
                    ]).strip()

            full_response = f"{clean_response}\n\n{deduplicated_summary}" if clean_response else deduplicated_summary

            # Only save the combined response, not the summary exchange
            history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            })

            self.history_manager.save_history(
                self.current_conversation,
                history
            )

            return summary, full_response

        except Exception as e:
            return f"Error generating summary: {str(e)}", original_response
    
    @Slot(str)
    def handle_stream_chunk(self, chunk: str):
        """Handle streaming chunk (called from streaming processor)

        IMPORTANT: Filter out ALL command-related content before display.
        Only show clean final results to the user.

        CRITICAL: This method is called from a Qt signal connected to a worker thread.
        All UI operations must be thread-safe.
        """
        if not chunk:
            return

        # Initialize command filtering state
        if not hasattr(self, '_in_command_mode'):
            self._in_command_mode = False
        if not hasattr(self, '_accumulated_before_command'):
            self._accumulated_before_command = ""

        # Check for command markers in the chunk
        if self.current_conversation:
            ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
            if ai_instance and hasattr(ai_instance, 'command_start'):
                cmd_start = ai_instance.command_start
                cmd_sep = ai_instance.command_separator if hasattr(ai_instance, 'command_separator') else ConversationConfig.command_separator

                # If this chunk contains a command marker
                if cmd_start in chunk:
                    print(f"[ChatBox] Command detected in stream chunk: {chunk[:50]}...")

                    # Save any content that was shown before the command
                    if self.current_stream_bubble:
                        print("[ChatBox] Saving bubble content before removing it")
                        # Get the current text from the bubble before removing
                        if hasattr(self.current_stream_bubble, 'message_label'):
                            bubble_text = self.current_stream_bubble.message_label.text()
                            if bubble_text and bubble_text.strip():
                                # Convert HTML back to plain text for storage
                                from PySide6.QtGui import QTextDocument
                                doc = QTextDocument()
                                doc.setHtml(bubble_text)
                                plain_text = doc.toPlainText()
                                bubble_type = self.current_stream_bubble.bubble_type
                                self._save_chat_record(plain_text, False, bubble_type)
                                print(f"[ChatBox] Saved pre-command content: {plain_text[:50]}...")

                        print("[ChatBox] Removing bubble that had content before command")
                        self._remove_bubble(self.current_stream_bubble)
                        self.current_stream_bubble = None
                        self._accumulated_before_command = ""

                    # Enter command mode - stop displaying
                    self._in_command_mode = True

                    # 创建命令气泡显示命令本身
                    # 提取命令文本 - 可能包含多个命令行
                    command_lines = chunk.split('\n')
                    command_text = command_lines[0] if command_lines else chunk

                    # 创建命令气泡
                    command_bubble = self._add_message_to_display(
                        message=command_text,
                        bubble_type=BubbleType.COMMAND_REQUEST
                    )
                    self.last_command_bubble = command_bubble
                    self.command_bubbles.append(command_bubble)  # Track for cleanup
                    print(f"[ChatBox] Created command bubble for: {command_text}")

                    # If there are more lines with commands, create additional bubbles
                    for i, line in enumerate(command_lines[1:], 1):
                        line = line.strip()
                        if line and (cmd_start in line or line.startswith(cmd_sep)):
                            # This is another command
                            additional_bubble = self._add_message_to_display(
                                message=line,
                                bubble_type=BubbleType.COMMAND_REQUEST
                            )
                            self.command_bubbles.append(additional_bubble)  # Track for cleanup
                            print(f"[ChatBox] Created additional command bubble {i}: {line}")

                    # Don't display command content beyond the bubble
                    return

                # If we're in command mode, check if this is the start of real content
                if self._in_command_mode:
                    # CRITICAL: Check if this is ANOTHER command (multi-command scenario)
                    if cmd_start in chunk:
                        print(f"[ChatBox] ANOTHER command detected while in command mode: {chunk[:50]}...")
                        # Exit command mode temporarily to handle new command
                        self._in_command_mode = False
                        # Let the code above handle this new command
                        # Continue to the command detection logic below
                    else:
                        # Look for indicators that we're now getting real content (not command output)
                        # Real content typically starts with text after newlines, not command syntax
                        chunk_clean = chunk.strip()

                        # Skip empty chunks or chunks that look like continuation of command
                        if not chunk_clean:
                            return

                    # Check if this is a command result (terminal output, file listing, etc.)
                    # Command results are typically:
                    # 1. Starting with "Execution successful" or similar
                    # 2. Multi-line text without markdown formatting
                    # 3. File listings, directory contents
                    # 4. Raw terminal output
                    is_command_result = (
                        chunk_clean.startswith('Execution successful') or
                        chunk_clean.startswith('Execution failed') or
                        chunk_clean.startswith('【执行结果')
                    )

                    if is_command_result:
                        print(f"[ChatBox] ✓✓✓ COMMAND RESULT DETECTED ✓✓✓")
                        print(f"[ChatBox] Result preview: {chunk_clean[:150]}...")
                        # 限制命令结果显示为前100字
                        display_result = chunk_clean[:100] + "..." if len(chunk_clean) > 100 else chunk_clean
                        # 创建命令结果气泡
                        result_bubble = self._add_message_to_display(
                            message=display_result,
                            bubble_type=BubbleType.COMMAND_RESULT
                        )
                        self.command_bubbles.append(result_bubble)  # Track for cleanup
                        # Still in command mode, wait for real content
                        QApplication.processEvents()
                        self._scroll_to_bottom()
                        return

                    # Check if this is an error message
                    is_error = (
                        '错误' in chunk_clean or
                        'error' in chunk_clean.lower() or
                        'Error' in chunk_clean or
                        'failed' in chunk_clean.lower() or
                        'Failed' in chunk_clean or
                        chunk_clean.startswith('**错误**')
                    )

                    if is_error:
                        print(f"[ChatBox] Error detected in command execution: {chunk_clean[:50]}...")
                        # 创建错误气泡
                        error_bubble = self._add_message_to_display(
                            message=chunk_clean,
                            bubble_type=BubbleType.ERROR
                        )
                        self._in_command_mode = False
                        self.current_stream_bubble = None
                        QApplication.processEvents()
                        self._scroll_to_bottom()
                        return

                    # If we see actual content (not just special characters or command artifacts),
                    # exit command mode and start displaying
                    # Check if this looks like real content (has substantial text, not just symbols)
                    has_real_content = (
                        len(chunk_clean) >= 1 and  # Even 1 char is OK for streaming
                        not chunk_clean.startswith(cmd_sep) and
                        not chunk_clean.startswith('》') and
                        not cmd_start in chunk_clean
                    )

                    if has_real_content:
                        print(f"[ChatBox] Exiting command mode, showing real content: {chunk_clean[:50]}...")
                        self._in_command_mode = False

                        # Create new bubble for the final conclusion
                        if self.current_stream_bubble is None:
                            self.current_stream_bubble = self._add_message_to_display(
                                message=chunk,
                                bubble_type=BubbleType.AI_RESPONSE
                            )
                            self.current_stream_bubble.is_streaming = True
                        else:
                            # Pass the original chunk with newlines preserved
                            # render_html=False to prevent flickering, markdown will be rendered on finalize
                            self.current_stream_bubble.append_text(chunk, render_html=False)

                        QApplication.processEvents()
                        self._scroll_to_bottom()
                        return
                    else:
                        # Still in command mode, skip this chunk
                        return

        # CRITICAL FIX: Don't strip the chunk! Preserve newlines and formatting
        # Only skip completely empty chunks
        if not chunk or chunk.isspace():
            return

        # Create or update streaming bubble (only for clean content)
        if self.current_stream_bubble is None:
            self.current_stream_bubble = self._add_message_to_display(
                message=chunk,
                bubble_type=BubbleType.AI_RESPONSE
            )
            self.current_stream_bubble.is_streaming = True
        else:
            # Always use plain text during streaming to prevent flickering
            # Markdown will be rendered when finalize_rendering() is called
            self.current_stream_bubble.append_text(chunk, render_html=False)

        QApplication.processEvents()
        self._scroll_to_bottom()
    
    def _show_final_response(self, response: str):
        """Show final response bubble with markdown rendering"""
        bubble = self._add_message_to_display(
            message=response,
            bubble_type=BubbleType.AI_RESPONSE
        )

        # Apply final markdown rendering
        bubble.finalize_rendering()

        self._save_chat_record(response, False, BubbleType.AI_RESPONSE)
    
    def _show_final_summary(self, summary: str, full_response: str = ""):
        """Show final summary bubble with markdown rendering

        Args:
            summary: The summary text from AI
            full_response: The full response including cleaned original response
        """
        # Remove ALL intermediate bubbles (all command execution bubbles)
        # This ensures only the final answer is visible, not the command history
        print(f"[ChatBox] Removing {len(self.command_bubbles)} command bubbles before final summary")

        for bubble in self.command_bubbles:
            if bubble:
                self._remove_bubble(bubble)
                print(f"[ChatBox] Removed command bubble")

        # Clear all bubble references
        self.command_bubbles.clear()
        self.last_command_bubble = None

        # Save and remove current streaming bubble if it exists
        if self.current_stream_bubble:
            print("[ChatBox] Saving streaming bubble content before final summary")
            # Get the current text from the bubble before removing
            if hasattr(self.current_stream_bubble, 'message_label'):
                bubble_text = self.current_stream_bubble.message_label.text()
                if bubble_text and bubble_text.strip():
                    # Convert HTML back to plain text for storage
                    from PySide6.QtGui import QTextDocument
                    doc = QTextDocument()
                    doc.setHtml(bubble_text)
                    plain_text = doc.toPlainText()
                    bubble_type = self.current_stream_bubble.bubble_type
                    self._save_chat_record(plain_text, False, bubble_type)
                    print(f"[ChatBox] Saved streaming content before summary: {plain_text[:50]}...")

            self._remove_bubble(self.current_stream_bubble)
            self.current_stream_bubble = None

        # Use full_response if provided, otherwise use summary
        display_text = full_response if full_response else summary

        bubble = self._add_message_to_display(
            message=f"✅ Task completed:\n{display_text}",
            bubble_type=BubbleType.FINAL_SUMMARY
        )

        # Apply final markdown rendering
        bubble.finalize_rendering()

        self._save_chat_record(f"Task completed:\n{display_text}", False, BubbleType.FINAL_SUMMARY)

    def _handle_processing_error(self, error_text: str):
        """Handle processing error"""
        self._add_message_to_display(
            message=f"❌ Error:\n{error_text}",
            bubble_type=BubbleType.ERROR
        )

        self._save_chat_record(f"Error:\n{error_text}", False, BubbleType.ERROR)
        self._reset_state()
    
    def _reset_state(self):
        """Reset processing state"""
        self.current_state = ProcessingState.IDLE
        self.send_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.current_stream_bubble = None
        self.processing_worker = None

        # CRITICAL: Reset AI stop flag to allow future processing
        if self.current_conversation:
            ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
            if ai_instance and hasattr(ai_instance, 'set_stop_flag'):
                ai_instance.set_stop_flag(False)

        # Reset command filtering state
        if hasattr(self, '_in_command_mode'):
            self._in_command_mode = False
        if hasattr(self, '_accumulated_before_command'):
            self._accumulated_before_command = ""

        self._update_status_bar()
        QApplication.processEvents()
    
    def _stop_processing(self):
        """Stop ongoing processing"""
        # Stop streaming processor
        self.streaming_processor.stop()

        # Stop worker if running
        if self.processing_worker and self.processing_worker.isRunning():
            self.processing_worker.stop()

        # Stop AI instance
        ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
        if ai_instance and hasattr(ai_instance, 'set_stop_flag'):
            ai_instance.set_stop_flag(True)

        # Show stopped message
        self._add_message_to_display(
            message="⏹️ Processing stopped",
            bubble_type=BubbleType.INFO
        )

        self._reset_state()

    def _delete_current_chat(self):
        """Delete current chat conversation"""
        if not self.current_conversation:
            return

        # Confirm deletion
        confirm_title = i18n.tr("confirm_delete") or "Confirm Delete"
        confirm_msg = i18n.tr("confirm_delete_message")

        if confirm_msg and "{0}" in confirm_msg:
            message = confirm_msg.replace("{0}", self.current_conversation)
        else:
            message = f'Are you sure you want to delete chat "{self.current_conversation}"?'

        reply = QMessageBox.question(
            self,
            confirm_title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop any ongoing processing
            self._stop_processing()

            # Store the name being deleted
            deleted_conversation = self.current_conversation

            # Clear conversation data from context manager
            self.context_manager.clear_conversation(deleted_conversation)

            # Remove from chat records
            if deleted_conversation in self.chat_records:
                del self.chat_records[deleted_conversation]

            # Remove from chat list
            if deleted_conversation in self.chat_list_names:
                self.chat_list_names.remove(deleted_conversation)

            # Clear AI history
            self.history_manager.delete_history(deleted_conversation)

            # Delete chat folder and all its contents
            self.chat_data_manager.delete_chat_folder(deleted_conversation)

            # Clear current conversation
            self.current_conversation = None
            self.chat_title.setText("")

            # Clear message display
            self._clear_message_display()

            # Save updated config
            self.config_manager.save_chat_history(self.chat_records)
            self.config_manager.save_chat_list(self.chat_list_names)

            # Reload chat list UI
            self._load_chat_list_to_ui()

            # Show empty state if no chats left
            if not self.chat_list_names:
                self._show_empty_state()
            else:
                # Switch to first available chat
                first_chat = self.chat_list_names[0]
                if first_chat:
                    items = self.chat_list.findItems(first_chat, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.switch_chat_target(items[0])

            print(f"[ModernChatBox] Deleted conversation: {deleted_conversation}")
    
    # ============================================================================
    # UI HELPERS
    # ============================================================================
    
    def _add_message_to_display(self, message: str, bubble_type: BubbleType,
                               timestamp: str = None) -> ModernMessageBubble:
        """Add message to display area

        CRITICAL: Must be called from main thread only.
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")

        # Create bubble with explicit parent (message_container) to avoid threading issues
        # This prevents "QObject::setParent: Cannot set parent, new parent is in a different thread" errors
        bubble = ModernMessageBubble(message, bubble_type, timestamp, parent=self.message_container)
        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)
        
        self.message_container.adjustSize()
        QTimer.singleShot(100, self._scroll_to_bottom)
        
        return bubble
    
    def _remove_bubble(self, bubble: ModernMessageBubble):
        """Remove bubble from display"""
        index = self.message_layout.indexOf(bubble)
        if index != -1:
            item = self.message_layout.takeAt(index)
            if item and item.widget():
                item.widget().deleteLater()
    
    def _remove_last_bubble(self):
        """Remove last bubble (for progress indicators)"""
        count = self.message_layout.count()
        if count > 1:  # Don't remove the stretch item
            item = self.message_layout.takeAt(count - 2)
            if item and item.widget():
                item.widget().deleteLater()
    
    def _clear_message_display(self):
        """Clear all messages from display"""
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear bubble references
        self.current_stream_bubble = None
        self.last_command_bubble = None
        self.command_bubbles.clear()  # Clear all tracked command bubbles
    
    def _scroll_to_bottom(self):
        """Scroll to bottom of message area"""
        scrollbar = self.message_scroll.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def _save_chat_record(self, text: str, is_sender: bool, bubble_type: BubbleType = BubbleType.AI_RESPONSE):
        """Save chat record with bubble type

        Args:
            text: Message text
            is_sender: Whether this is a user message
            bubble_type: Type of bubble for correct color restoration
        """
        self.chat_records[self.current_conversation].append({
            "text": text,
            "is_sender": is_sender,
            "timestamp": datetime.now().isoformat(),
            "bubble_type": bubble_type.value  # Save as integer
        })

        self.config_manager.save_chat_history(self.chat_records)

    def _detect_bubble_type(self, text: str, is_sender: bool) -> BubbleType:
        """Detect bubble type from text content (fallback for old records)

        Args:
            text: Message text
            is_sender: Whether this is a user message

        Returns:
            Detected bubble type
        """
        if is_sender:
            return BubbleType.USER_MESSAGE
        elif "执行命令" in text or "Executing command" in text:
            return BubbleType.COMMAND_REQUEST
        elif "执行结果" in text or "Command executed" in text:
            return BubbleType.COMMAND_RESULT
        elif "任务完成" in text or "Task completed" in text:
            return BubbleType.FINAL_SUMMARY
        elif "错误" in text or "Error" in text:
            return BubbleType.ERROR
        elif "Processing" in text:
            return BubbleType.INFO
        else:
            return BubbleType.AI_RESPONSE
    
    def _update_status_bar(self):
        """Update status bar"""
        ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
        
        if ai_instance:
            tools_count = len(ai_instance.funcs) if hasattr(ai_instance, 'funcs') else 0
            streaming_status = "Streaming" if ai_instance.stream else "Standard"
            model_name = getattr(ai_instance, 'model', 'Unknown')
            
            state_text = {
                ProcessingState.STREAMING: " | Streaming",
                ProcessingState.EXECUTING_COMMAND: " | Executing Command",
                ProcessingState.AWAITING_SUMMARY: " | Awaiting Summary",
                ProcessingState.ERROR: " | Error",
                ProcessingState.LOADING: " | Loading..."
            }.get(self.current_state, "")
            
            status_text = f"Lynexus AI | {model_name} | {tools_count} tools | {streaming_status}{state_text}"
            self.status_bar.showMessage(status_text)
        else:
            self.status_bar.showMessage("Lynexus AI | Not connected")
    
    # ============================================================================
    # CONVERSATION MANAGEMENT
    # ============================================================================
    
    def switch_chat_target(self, item):
        """Switch to different chat conversation"""
        if not item:
            return

        conversation_name = item.data(Qt.UserRole)

        if conversation_name == self.current_conversation:
            return

        # If currently processing, warn user and don't switch
        if self.current_state != ProcessingState.IDLE:
            QMessageBox.warning(
                self,
                i18n.tr("warning") or "Warning",
                i18n.tr("cannot_switch_during_process") or "Please wait for the current response to complete before switching conversations.",
                QMessageBox.StandardButton.Ok
            )
            return

        print(f"[ModernChatBox] Switching to: {conversation_name}")

        try:
            # Set loading state
            self.current_state = ProcessingState.LOADING
            self._update_status_bar()

            # Set as current item in QListWidget for visual selection
            self.chat_list.setCurrentItem(item)

            self.current_conversation = conversation_name
            self.chat_title.setText(conversation_name)

            # Save as last active
            self.config_manager.save_last_active_chat(conversation_name)

            # Clear UI
            self._clear_message_display()
            self.current_stream_bubble = None
            self.last_command_bubble = None
            self.command_bubbles.clear()  # Clear all tracked command bubbles

            # Load AI for conversation
            self.context_manager.get_ai_for_conversation(conversation_name)

            # Load messages
            self._load_conversation_messages(conversation_name)

            # Update status
            self.current_state = ProcessingState.IDLE
            self._update_status_bar()

            # Scroll to bottom
            QTimer.singleShot(100, self._scroll_to_bottom)

        except Exception as e:
            print(f"[ModernChatBox] Switch error: {e}")
            self.current_state = ProcessingState.IDLE
            self._update_status_bar()
            QMessageBox.warning(self, "Switch Error", f"Error: {e}")
    
    def _load_conversation_messages(self, conversation_name: str):
        """Load and display conversation messages"""
        if conversation_name in self.chat_records:
            messages = self.chat_records[conversation_name]

            # Ensure messages is a list
            if not isinstance(messages, list):
                print(f"[ModernChatBox] Warning: chat_records[{conversation_name}] is not a list: {type(messages)}")
                messages = []
                self.chat_records[conversation_name] = messages

            self.message_container.setUpdatesEnabled(False)

            for msg in messages:
                # Ensure msg is a dict
                if not isinstance(msg, dict):
                    print(f"[ModernChatBox] Warning: message is not a dict: {type(msg)}")
                    continue

                # Get timestamp
                timestamp = msg.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%H:%M")
                    except:
                        time_str = datetime.now().strftime("%H:%M")
                else:
                    time_str = datetime.now().strftime("%H:%M")

                # Get message properties
                is_sender = msg.get("is_sender", False)
                text = msg.get("text", "")

                # Try to get bubble_type from saved data first
                saved_bubble_type = msg.get("bubble_type")

                if saved_bubble_type is not None:
                    # Use saved bubble type
                    try:
                        bubble_type = BubbleType(saved_bubble_type)
                    except:
                        # Invalid bubble type value, fall back to detection
                        bubble_type = self._detect_bubble_type(text, is_sender)
                else:
                    # No saved bubble type, detect from text (for old records)
                    bubble_type = self._detect_bubble_type(text, is_sender)

                # Create bubble with explicit parent
                bubble = ModernMessageBubble(text, bubble_type, time_str, parent=self.message_container)
                self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)

                # Apply markdown rendering for AI responses and summaries
                if not is_sender and bubble_type in [BubbleType.AI_RESPONSE, BubbleType.FINAL_SUMMARY]:
                    bubble.finalize_rendering()

            self.message_container.setUpdatesEnabled(True)
            self.message_container.adjustSize()
            QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _create_new_chat_programmatically(self) -> str:
        """
        Create a new default chat programmatically (without user dialog)
        Returns the name of the created chat, or empty string if failed
        """
        # Generate a default name
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"new_chat_{timestamp}"

        try:
            # Add to chat list
            self.chat_list_names.append(default_name)
            self.config_manager.save_chat_list(self.chat_list_names)

            # Create chat folder structure
            chat_dir = self.chat_data_manager.get_chat_dir(default_name)
            chat_dir.mkdir(parents=True, exist_ok=True)

            # Initialize chat record as empty list (not dict!)
            self.chat_records[default_name] = []
            self.config_manager.save_chat_history(self.chat_records)

            # Add to UI
            item = QListWidgetItem(default_name)
            item.setData(Qt.UserRole, default_name)
            self.chat_list.addItem(item)

            print(f"[ModernChatBox] Created new default chat: {default_name}")
            return default_name

        except Exception as e:
            print(f"[ModernChatBox] Failed to create new chat: {e}")
            return ""

    def _add_new_chat(self):
        """Add new chat"""
        name, ok = QInputDialog.getText(self, "New Chat", "Enter chat name:")

        if ok and name:
            # Add to UI
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            self.chat_list.addItem(item)

            if name not in self.chat_list_names:
                self.chat_list_names.append(name)
                self.config_manager.save_chat_list(self.chat_list_names)

            # Select new chat
            items = self.chat_list.findItems(name, Qt.MatchExactly)
            if items:
                self.chat_list.setCurrentItem(items[0])
                self.switch_chat_target(items[0])
    
    # ============================================================================
    # AI INITIALIZATION
    # ============================================================================
    
    def _initialize_ai(self):
        """Initialize AI"""
        # Try to load API key for current conversation
        api_key = self.config_manager.load_api_key(self.current_conversation) if self.current_conversation else None

        if not api_key and not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")):
            # Show init dialog
            QTimer.singleShot(500, self._show_init_dialog)
        else:
            # Load AI for current conversation (if exists)
            if self.current_conversation:
                self.context_manager.get_ai_for_conversation(self.current_conversation)

            has_api_key = bool(api_key)
            self.send_button.setEnabled(has_api_key)
            self._update_status_bar()
    
    # ============================================================================
    # DIALOGS AND ACTIONS
    # ============================================================================
    
    def _open_settings(self):
        """Open settings dialog"""
        if not self.current_conversation:
            return
        
        # Get current AI instance
        ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
        
        if ai_instance:
            self.settings_dialog = SettingsDialog(
                ai_instance=ai_instance,
                conversation_name=self.current_conversation
            )
        else:
            # Default config
            default_config = ConversationConfig()
            self.settings_dialog = SettingsDialog(
                current_config=default_config.__dict__,
                conversation_name=self.current_conversation
            )
        
        self.settings_dialog.sig_save_settings.connect(self._handle_settings_save)
        self.settings_dialog.show()
    
    def _handle_settings_save(self, settings: dict):
        """Handle settings save"""
        if self.current_conversation:
            # Show loading status
            self.current_state = ProcessingState.LOADING
            self._update_status_bar()

            # Save configuration
            self.config_manager.save_conversation_config(self.current_conversation, settings)

            # Update AI configuration asynchronously
            from PySide6.QtCore import QThreadPool, QRunnable

            class ReloadAITask(QRunnable):
                def __init__(self, chat_box, conversation_name, settings):
                    super().__init__()  # 调用父类初始化
                    self.chat_box = chat_box
                    self.conversation_name = conversation_name
                    self.settings = settings

                def run(self):
                    try:
                        # Clear and reload AI
                        self.chat_box.context_manager.clear_conversation(self.conversation_name)
                        ai_instance = self.chat_box.context_manager.get_ai_for_conversation(self.conversation_name)

                        if ai_instance:
                            # 更新基本配置
                            print(f"[AsyncReload] Updating AI config...")
                            ai_instance.update_config(self.settings)

                            # 清除缓存并重新创建 AI 实例
                            print("[AsyncReload] Clearing conversation cache and recreating AI instance...")
                            self.chat_box.context_manager.clear_conversation(self.conversation_name)
                            ai_instance = self.chat_box.context_manager.get_ai_for_conversation(self.conversation_name)

                            print(f"[AsyncReload] New AI instance created with {len(ai_instance.enabled_mcp_tools)} tools")

                            # 在主线程中执行 UI 更新
                            QMetaObject.invokeMethod(
                                self.chat_box,
                                "_on_mcp_load_complete",
                                Qt.QueuedConnection,
                                Q_ARG(str, self.conversation_name)
                            )

                    except Exception as e:
                        print(f"[Error] Failed to reload AI: {e}")
                        import traceback
                        traceback.print_exc()

                        # 即使失败也要通知完成
                        QMetaObject.invokeMethod(
                            self.chat_box,
                            "_on_mcp_load_complete",
                            Qt.QueuedConnection,
                            Q_ARG(str, self.conversation_name)
                        )

            # Run in background
            QThreadPool.globalInstance().start(ReloadAITask(self, self.current_conversation, settings))

    @Slot(str)
    def _on_mcp_load_complete(self, conversation_name: str):
        """MCP tools load complete callback"""
        self.current_state = ProcessingState.IDLE
        self._update_status_bar()
        QMessageBox.information(self, "Success", f"Settings updated for {conversation_name}")
    
    def _clear_current_chat(self):
        """Clear current chat"""
        if self.current_conversation:
            reply = QMessageBox.question(
                self, "Clear Chat",
                f"Clear all messages in '{self.current_conversation}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Clear UI history
                self.chat_records[self.current_conversation] = []
                self._clear_message_display()
                
                # Clear AI history
                ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)
                system_prompt = ai_instance.system_prompt if ai_instance else None
                self.history_manager.clear_history(self.current_conversation, system_prompt)
                
                QMessageBox.information(self, "Chat Cleared",
                    f"Chat history cleared for '{self.current_conversation}'.\n"
                    f"AI conversation history has also been reset.")
    
    def _export_chat_history(self):
        """Export chat history"""
        if not self.current_conversation or not self.chat_records.get(self.current_conversation):
            QMessageBox.warning(self, "Export Error", "No chat history to export")
            return
        
        desktop_path = str(Path.home() / "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = f"{self.current_conversation}_{timestamp}.txt"
        default_path = os.path.join(desktop_path, default_file)
        
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Export Chat History")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDirectory(desktop_path)
        file_dialog.selectFile(default_file)
        file_dialog.setNameFilter("Text Files (*.txt);;JSON Files (*.json);;Markdown Files (*.md)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                try:
                    messages = self.chat_records[self.current_conversation]
                    
                    if file_path.endswith('.json'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(messages, f, indent=2, ensure_ascii=False)
                    
                    elif file_path.endswith('.md'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"# Chat: {self.current_conversation}\n\n")
                            f.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                            f.write("---\n\n")
                            for msg in messages:
                                sender = "**You**" if msg.get("is_sender", False) else "**AI**"
                                timestamp = msg.get("timestamp", "")
                                if timestamp:
                                    try:
                                        dt = datetime.fromisoformat(timestamp)
                                        time_str = dt.strftime("%H:%M")
                                    except:
                                        time_str = timestamp
                                else:
                                    time_str = ""
                                
                                f.write(f"{sender} ({time_str}):\n\n")
                                f.write(f"{msg.get('text', '')}\n\n")
                                f.write("---\n\n")
                    
                    else:
                        if not file_path.endswith('.txt'):
                            file_path += '.txt'
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"Chat: {self.current_conversation}\n")
                            f.write("=" * 50 + "\n\n")
                            for msg in messages:
                                sender = "You" if msg.get("is_sender", False) else "AI"
                                timestamp = msg.get("timestamp", "")
                                if timestamp:
                                    try:
                                        dt = datetime.fromisoformat(timestamp)
                                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                                    except:
                                        time_str = timestamp
                                else:
                                    time_str = ""
                                
                                f.write(f"[{time_str}] {sender}:\n")
                                f.write(f"{msg.get('text', '')}\n\n")
                    
                    QMessageBox.information(self, "Export Success", f"Chat exported to:\n{file_path}")

                except Exception as e:
                    QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")

    def _import_config_from_zip(self):
        """
        Import chat configuration from a zip archive (via file dialog).
        The archive should contain a {chat_name}/ folder with:
        - settings.json
        - tools/ directory
        Extracts to data/ and adds to chat list, then switches to it.
        """
        try:
            # Open file dialog to select zip file
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle(i18n.tr("import_config"))
            file_dialog.setFileMode(QFileDialog.ExistingFile)
            file_dialog.setNameFilter("ZIP Archives (*.zip)")

            selected_files, _ = file_dialog.getOpenFileNames(
                self, "Select Configuration Archive", "", "ZIP Archives (*.zip)"
            )

            if not selected_files:
                return

            zip_path = selected_files[0]
            self._import_config_from_zip_path(zip_path)

        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import configuration:\n{e}")

    def _import_config_from_zip_path(self, zip_path: str):
        """
        Import chat configuration from a specific zip file path.
        This method can be called from drag-drop or file dialog.

        Args:
            zip_path: Path to the ZIP archive file
        """
        try:
            # Read zip archive
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Get list of files in zip
                file_list = zipf.namelist()

                # Validate ZIP structure
                # Must contain: {chat_name}/settings.json and {chat_name}/tools/
                chat_folder_name = None
                has_settings = False
                has_tools = False

                for name in file_list:
                    parts = name.split('/')
                    if len(parts) > 1:
                        if not chat_folder_name:
                            chat_folder_name = parts[0]

                        # Check for settings.json
                        if len(parts) == 2 and parts[1] == 'settings.json':
                            has_settings = True

                        # Check for tools directory
                        if len(parts) >= 2 and parts[1] == 'tools':
                            has_tools = True

                # Validate structure
                if not chat_folder_name or not has_settings or not has_tools:
                    QMessageBox.warning(
                        self,
                        i18n.tr("invalid_zip_format"),
                        i18n.tr("invalid_zip_message")
                    )
                    return

                # Generate unique chat name
                original_name = chat_folder_name
                new_chat_name = original_name
                counter = 1

                # Check if name already exists and generate unique name
                existing_chats = set(self.chat_list_names)
                while new_chat_name in existing_chats:
                    new_chat_name = f"{original_name}_{counter}"
                    counter += 1

                # Extract to data directory
                temp_extract_dir = Path("data") / "__temp_import__"
                temp_extract_dir.mkdir(exist_ok=True, parents=True)

                try:
                    # Extract all files
                    zipf.extractall(temp_extract_dir)

                    # Source and destination paths
                    source_chat_dir = temp_extract_dir / chat_folder_name
                    dest_chat_dir = Path("data") / new_chat_name

                    # Move extracted folder to final location
                    if dest_chat_dir.exists():
                        shutil.rmtree(dest_chat_dir)
                    shutil.move(str(source_chat_dir), str(dest_chat_dir))

                    # Update settings.json if name was changed
                    if new_chat_name != original_name:
                        settings_path = dest_chat_dir / "settings.json"
                        if settings_path.exists():
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                            # Update any chat-specific settings if needed
                            with open(settings_path, 'w', encoding='utf-8') as f:
                                json.dump(settings, f, indent=2, ensure_ascii=False)

                    # Add to app_config.json chat list
                    if new_chat_name not in self.chat_list_names:
                        self.chat_list_names.append(new_chat_name)
                        self.config_manager.save_chat_list(self.chat_list_names)

                    # Add to UI
                    self._load_chat_list_to_ui()

                    # Switch to the newly imported chat
                    # Find the item in the list
                    for i in range(self.chat_list.count()):
                        item = self.chat_list.item(i)
                        if item.data(Qt.UserRole) == new_chat_name:
                            self.switch_chat_target(item)
                            break

                    QMessageBox.information(self, "Import Success",
                        f"Configuration imported successfully!\n\n"
                        f"Chat name: {new_chat_name}\n"
                        f"Location: data/{new_chat_name}/")

                finally:
                    # Clean up temp directory
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir)

        except zipfile.BadZipFile:
            QMessageBox.warning(self, i18n.tr("invalid_zip_format"),
                i18n.tr("invalid_zip_message"))
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import configuration:\n{e}")

    def _show_init_dialog(self):
        """Show initialization dialog"""
        if self.init_dialog is None:
            self.init_dialog = InitDialog()
            self.init_dialog.sig_done.connect(self._handle_init_done)
        
        self.init_dialog.show()
    
    def _handle_init_done(self, api_key: str, mcp_files: list, config_file: str):
        """Handle initialization completion"""
        if api_key:
            # Save API key to current conversation's .confignore
            self.config_manager.save_api_key(api_key, self.current_conversation)

        # Reload AI
        self.context_manager.get_ai_for_conversation(self.current_conversation)

        self.send_button.setEnabled(True)
        self._update_status_bar()
    
    def _show_tools_list(self):
        """Show MCP tools selection dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton

        ai_instance = self.context_manager.get_ai_for_conversation(self.current_conversation)

        if not ai_instance:
            QMessageBox.information(self, "Tools", "No AI instance available.")
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("MCP Tools")
        dialog.setMinimumSize(500, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
        """)

        # Create layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)

        # Create MCP tools widget
        tools_widget = MCPToolsWidget(ai_instance)
        layout.addWidget(tools_widget)

        # Add close button
        close_button = QPushButton("Close")
        close_button.setFixedHeight(40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4A9CFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #5AACFF; }
            QPushButton:pressed { background-color: #3A8CEE; }
        """)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        # Show dialog
        dialog.exec()
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def closeEvent(self, event):
        """Handle window close"""
        print("[ModernChatBox] Closing application...")
        
        # Stop processing
        if self.current_state != ProcessingState.IDLE:
            self._stop_processing()
        
        # Stop worker
        if self.processing_worker and self.processing_worker.isRunning():
            self.processing_worker.stop()
            self.processing_worker.wait(2000)
        
        # Save data
        try:
            self.config_manager.save_chat_history(self.chat_records)
            self.config_manager.save_chat_list(self.chat_list_names)
            print("[ModernChatBox] Chat data saved")
        except Exception as e:
            print(f"[ModernChatBox] Save error: {e}")
        
        # Shutdown thread pool
        self.processing_thread_pool.shutdown(wait=True)
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key_Escape:
            event.ignore()
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
            self._add_new_chat()
        elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self._open_settings()
        elif event.key() == Qt.Key_T and event.modifiers() & Qt.ControlModifier:
            self._show_tools_list()
        else:
            super().keyPressEvent(event)



# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

class ChatBox(ModernChatBox):
    """Legacy compatibility alias"""
    pass


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """Main entry point for testing"""
    print("Starting Lynexus AI Chat Box...")
    
    app = QApplication(sys.argv)
    chat_box = ModernChatBox()
    chat_box.show()
    
    sys.exit(app.exec())