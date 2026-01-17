# [file name]: utils/config_manager.py
"""
Configuration Manager
Handles saving and loading of configuration files with relative paths.
Now integrates with ChatDataManager for individual chat folders
"""
import os
import json
import pickle
from utils.chat_data_manager import ChatDataManager

class ConfigManager:
    """Manages configuration files with relative path handling."""

    def __init__(self):
        self.configs_dir = "configs"
        self.ignore_file = ".confignore"
        self.conversations_dir = "conversations"
        self.history_dir = "chathistory"
        self.app_config_file = "app_config.json"
        self.chat_data_manager = ChatDataManager()

        # Create directories if they don't exist (for backward compatibility)
        os.makedirs(self.configs_dir, exist_ok=True)
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Initialize app config if it doesn't exist
        self._init_app_config()
    
    def _init_app_config(self):
        """Initialize application configuration file if it doesn't exist."""
        config_path = self.app_config_file
        if not os.path.exists(config_path):
            default_config = {
                "chat_list": ["general_chat"],
                "app_settings": {
                    "window_width": 1400,
                    "window_height": 900,
                    "last_active_chat": "general_chat"
                }
            }
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                print(f"Created default app config at {config_path}")
            except Exception as e:
                print(f"Error creating app config: {e}")
    
    def load_config_file(self):
        """Load main application configuration file."""
        config_path = self.app_config_file
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        # Return default config if file doesn't exist or error
        return {
            "chat_list": [],
            "app_settings": {}
        }
    
    def save_config_file(self, config_data):
        """Save main application configuration file."""
        config_path = self.app_config_file
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get_conversation_config_path(self, conversation_name):
        """Get config file path for a conversation (sanitized name)."""
        # Sanitize conversation name for filename
        safe_name = "".join(c for c in conversation_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return os.path.join(self.conversations_dir, f"{safe_name}.json")
    
    def load_conversation_config(self, conversation_name):
        """Load configuration for a conversation with path conversion."""
        # Try new ChatDataManager first
        config = self.chat_data_manager.load_chat_settings(conversation_name)
        if config:
            return config

        # Fall back to old method for backward compatibility
        config_path = self.get_conversation_config_path(conversation_name)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                    # Convert relative MCP paths to absolute paths
                    if 'mcp_paths' in config:
                        config['mcp_paths'] = [
                            os.path.abspath(path) if not os.path.isabs(path) else path
                            for path in config['mcp_paths']
                        ]

                    return config
            except Exception as e:
                print(f"Error loading config for {conversation_name}: {e}")
        return None
    
    def save_conversation_config(self, conversation_name, config):
        """Save conversation configuration with relative paths."""
        # Save using new ChatDataManager
        success = self.chat_data_manager.save_chat_settings(conversation_name, config)

        # Also save to old location for backward compatibility
        config_path = self.get_conversation_config_path(conversation_name)
        safe_config = config.copy()

        # Remove sensitive information
        if 'api_key' in safe_config:
            del safe_config['api_key']
        if 'ai_config' in safe_config and 'api_key' in safe_config['ai_config']:
            del safe_config['ai_config']['api_key']

        # Convert absolute MCP paths to relative paths if they are in the current directory tree
        if 'mcp_paths' in safe_config:
            safe_config['mcp_paths'] = [
                self._make_path_relative(path) for path in safe_config['mcp_paths']
            ]

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config for {conversation_name}: {e}")
            return success
    
    def _make_path_relative(self, path):
        """Convert absolute path to relative if possible."""
        if not os.path.isabs(path):
            return path

        # Try to make path relative to current directory
        try:
            rel_path = os.path.relpath(path)
            # Use relative path as long as it's reasonable (not going up more than 3 levels)
            # Count how many ".." are in the path
            up_levels = rel_path.count('..' + os.sep)
            if up_levels <= 3:
                return rel_path
        except ValueError:
            pass

        # Return absolute path if relative conversion fails or goes too far up
        return path
    
    def load_api_key(self):
        """Load API key from .confignore file or environment variables."""
        # Try .confignore file first
        ignore_path = self.ignore_file
        if os.path.exists(ignore_path):
            try:
                with open(ignore_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    lines = content.split('\n')
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'api_key':
                                return value.strip()
            except:
                pass
        
        # Check environment variables
        env_keys = ['DEEPSEEK_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        for key in env_keys:
            value = os.environ.get(key)
            if value:
                return value
        
        return None
    
    def save_api_key(self, api_key):
        """Save API key to .confignore file."""
        try:
            with open(self.ignore_file, 'w', encoding='utf-8') as f:
                f.write(f"api_key={api_key}")
            return True
        except:
            return False
    
    def save_chat_history(self, chat_records):
        """Save chat history to pickle files."""
        for chat, messages in chat_records.items():
            file_path = os.path.join(self.history_dir, f"{chat}.his")
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(messages, f)
            except Exception as e:
                print(f"Error saving chat history: {e}")
    
    def load_chat_history(self):
        """Load chat history from pickle files."""
        chat_records = {}
        for file_name in os.listdir(self.history_dir):
            if file_name.endswith('.his'):
                chat_name = file_name[:-4]
                file_path = os.path.join(self.history_dir, file_name)
                try:
                    with open(file_path, 'rb') as f:
                        chat_records[chat_name] = pickle.load(f)
                except Exception as e:
                    print(f"Error loading chat history: {e}")
        return chat_records
    
    def save_chat_list(self, chat_list):
        """保存聊天列表 - 自动与data目录同步"""
        try:
            # 获取data目录中的实际聊天文件夹
            actual_chats = set(self.chat_data_manager.list_all_chats())

            # 合并传入的列表和实际的文件夹列表
            merged_list = []
            seen = set()

            # 首先添加传入的聊天(保持用户指定的顺序)
            for chat in chat_list:
                if chat in actual_chats and chat not in seen:
                    merged_list.append(chat)
                    seen.add(chat)

            # 然后添加data目录中存在的其他聊天
            for chat in sorted(actual_chats):
                if chat not in seen:
                    merged_list.append(chat)
                    seen.add(chat)

            # 保存合并后的列表
            data = self.load_config_file()
            data['chat_list'] = merged_list
            self.save_config_file(data)

            # 如果合并后的列表与传入的不同,打印日志
            if merged_list != chat_list:
                print(f"[ConfigManager] Chat list synced with data directory: {chat_list} -> {merged_list}")

            return True
        except Exception as e:
            print(f"Error saving chat list: {e}")
            return False
    
    def load_chat_list(self):
        """加载聊天列表 - 自动同步data目录中的实际聊天文件夹"""
        try:
            # 从data目录获取实际的聊天文件夹列表
            actual_chats = set(self.chat_data_manager.list_all_chats())

            # 从配置文件加载聊天列表
            data = self.load_config_file()
            config_chats = data.get('chat_list', [])

            # 合并两个列表: 保留配置文件中的顺序,并添加data中新发现的聊天
            merged_list = []
            seen = set()

            # 首先添加配置文件中的聊天(保持顺序)
            for chat in config_chats:
                if chat in actual_chats and chat not in seen:
                    merged_list.append(chat)
                    seen.add(chat)

            # 然后添加data目录中新发现的聊天
            for chat in sorted(actual_chats):  # 排序以确保一致性
                if chat not in seen:
                    merged_list.append(chat)
                    seen.add(chat)

            # 如果列表有变化,自动保存
            if merged_list != config_chats:
                print(f"[ConfigManager] Auto-syncing chat list: {config_chats} -> {merged_list}")
                data['chat_list'] = merged_list
                self.save_config_file(data)

            return merged_list
        except Exception as e:
            print(f"Error loading chat list: {e}")
            return None
    
    def save_last_active_chat(self, chat_name):
        """保存最后活动的聊天"""
        try:
            data = self.load_config_file()
            if 'app_settings' not in data:
                data['app_settings'] = {}
            data['app_settings']['last_active_chat'] = chat_name
            self.save_config_file(data)
            return True
        except Exception as e:
            print(f"Error saving last active chat: {e}")
            return False
    
    def load_last_active_chat(self):
        """加载最后活动的聊天"""
        try:
            data = self.load_config_file()
            return data.get('app_settings', {}).get('last_active_chat')
        except Exception as e:
            print(f"Error loading last active chat: {e}")
            return None