# [file name]: utils/chat_data_manager.py
"""
Chat Data Manager - Manages individual chat folders and their data
Each chat has its own folder containing settings, history, and MCP tools
"""

import os
import json
import pickle
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class ChatDataManager:
    """
    Manages data storage for individual chats
    Each chat gets its own folder in data/ directory
    """

    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True, parents=True)

    def _sanitize_chat_name(self, chat_name: str) -> str:
        """Sanitize chat name for use as folder name"""
        # Remove invalid characters
        safe_name = "".join(c for c in chat_name if c.isalnum() or c in (' ', '-', '_')).strip()
        # Replace spaces with underscores
        safe_name = safe_name.replace(' ', '_')
        return safe_name or "default_chat"

    def get_chat_dir(self, chat_name: str) -> Path:
        """Get the directory path for a specific chat"""
        safe_name = self._sanitize_chat_name(chat_name)
        return self.data_dir / safe_name

    def create_chat_folder(self, chat_name: str) -> Path:
        """
        Create a new chat folder with subdirectories
        Returns the path to the created folder
        """
        chat_dir = self.get_chat_dir(chat_name)
        chat_dir.mkdir(exist_ok=True, parents=True)

        # Create tools subdirectory
        tools_dir = chat_dir / "tools"
        tools_dir.mkdir(exist_ok=True)

        return chat_dir

    def delete_chat_folder(self, chat_name: str) -> bool:
        """
        Delete a chat folder and all its contents
        Returns True if successful, False otherwise
        """
        chat_dir = self.get_chat_dir(chat_name)

        if not chat_dir.exists():
            print(f"[ChatData] Chat folder does not exist: {chat_dir}")
            return False

        try:
            shutil.rmtree(chat_dir)
            print(f"[ChatData] Deleted chat folder: {chat_dir}")
            return True
        except Exception as e:
            print(f"[ChatData] Failed to delete chat folder: {e}")
            return False

    def chat_exists(self, chat_name: str) -> bool:
        """Check if a chat folder exists"""
        return self.get_chat_dir(chat_name).exists()

    def list_all_chats(self) -> List[str]:
        """List all existing chat folder names"""
        chats = []
        for item in self.data_dir.iterdir():
            if item.is_dir():
                chats.append(item.name)
        return chats

    # === File path getters ===

    def get_settings_path(self, chat_name: str) -> Path:
        """Get path to settings.json for a chat"""
        return self.get_chat_dir(chat_name) / "settings.json"

    def get_chat_history_path(self, chat_name: str) -> Path:
        """Get path to chat_his.pickle for a chat"""
        return self.get_chat_dir(chat_name) / "chat_his.pickle"

    def get_ai_history_path(self, chat_name: str) -> Path:
        """Get path to conversation_ai.json for a chat"""
        safe_name = self._sanitize_chat_name(chat_name)
        return self.get_chat_dir(chat_name) / f"{safe_name}_ai.json"

    def get_tools_dir(self, chat_name: str) -> Path:
        """Get path to tools directory for a chat"""
        return self.get_chat_dir(chat_name) / "tools"

    # === MCP Tool Management ===

    def copy_mcp_tool_to_chat(self, chat_name: str, original_path: str) -> Optional[str]:
        """
        Copy an MCP tool file to the chat's tools directory
        Returns the absolute path to the copied file, or None if failed
        """
        chat_dir = self.get_chat_dir(chat_name)
        if not chat_dir.exists():
            print(f"[ChatData] Chat folder does not exist: {chat_name}")
            return None

        tools_dir = self.get_tools_dir(chat_name)
        original_path_obj = Path(original_path)

        if not original_path_obj.exists():
            print(f"[ChatData] Original file does not exist: {original_path}")
            return None

        # Get the filename
        filename = original_path_obj.name
        dest_path = tools_dir / filename

        try:
            # Copy the file
            shutil.copy2(original_path, dest_path)
            # Return absolute path
            absolute_path = str(dest_path.resolve())
            print(f"[ChatData] Copied MCP tool to: {absolute_path}")
            return absolute_path
        except Exception as e:
            print(f"[ChatData] Failed to copy MCP tool: {e}")
            return None

    def get_chat_mcp_tools(self, chat_name: str) -> List[str]:
        """
        Get list of MCP tool files in the chat's tools directory
        Returns list of absolute paths
        """
        tools_dir = self.get_tools_dir(chat_name)
        if not tools_dir.exists():
            return []

        tool_files = []
        for file in tools_dir.iterdir():
            if file.is_file():
                # Include Python, JSON, YAML files
                if file.suffix in ['.py', '.json', '.yaml', '.yml']:
                    tool_files.append(str(file.resolve()))

        return tool_files

    # === Settings Management ===

    def load_chat_settings(self, chat_name: str) -> Optional[Dict]:
        """Load settings.json for a chat"""
        settings_path = self.get_settings_path(chat_name)

        if not settings_path.exists():
            return None

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Convert relative MCP paths to absolute paths
            if 'mcp_paths' in settings:
                settings['mcp_paths'] = [
                    os.path.abspath(path) if not os.path.isabs(path) else path
                    for path in settings['mcp_paths']
                ]

            return settings
        except Exception as e:
            print(f"[ChatData] Failed to load settings: {e}")
            return None

    def save_chat_settings(self, chat_name: str, settings: Dict) -> bool:
        """
        Save settings.json for a chat
        Removes sensitive info before saving
        """
        chat_dir = self.get_chat_dir(chat_name)
        if not chat_dir.exists():
            self.create_chat_folder(chat_name)

        settings_path = self.get_settings_path(chat_name)

        # Remove sensitive information
        safe_settings = settings.copy()
        if 'api_key' in safe_settings:
            del safe_settings['api_key']
        if 'ai_config' in safe_settings and 'api_key' in safe_settings['ai_config']:
            del safe_settings['ai_config']['api_key']

        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(safe_settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ChatData] Failed to save settings: {e}")
            return False

    # === Chat History Management ===

    def load_chat_history(self, chat_name: str) -> Optional[List]:
        """Load chat display history from pickle file"""
        history_path = self.get_chat_history_path(chat_name)

        if not history_path.exists():
            return None

        try:
            with open(history_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[ChatData] Failed to load chat history: {e}")
            return None

    def save_chat_history(self, chat_name: str, history: List) -> bool:
        """Save chat display history to pickle file"""
        chat_dir = self.get_chat_dir(chat_name)
        if not chat_dir.exists():
            self.create_chat_folder(chat_name)

        history_path = self.get_chat_history_path(chat_name)

        try:
            with open(history_path, 'wb') as f:
                pickle.dump(history, f)
            return True
        except Exception as e:
            print(f"[ChatData] Failed to save chat history: {e}")
            return False

    # === AI Conversation History Management ===

    def load_ai_history(self, chat_name: str) -> Optional[List[Dict]]:
        """Load AI conversation history from JSON file"""
        ai_history_path = self.get_ai_history_path(chat_name)

        if not ai_history_path.exists():
            return None

        try:
            with open(ai_history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ChatData] Failed to load AI history: {e}")
            return None

    def save_ai_history(self, chat_name: str, history: List[Dict]) -> bool:
        """Save AI conversation history to JSON file"""
        chat_dir = self.get_chat_dir(chat_name)
        if not chat_dir.exists():
            self.create_chat_folder(chat_name)

        ai_history_path = self.get_ai_history_path(chat_name)

        try:
            with open(ai_history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ChatData] Failed to save AI history: {e}")
            return False
