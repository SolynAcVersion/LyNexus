# utils/conversation_config.py
"""
会话配置管理器
每个对话都有独立的文件夹和配置,包括 API key 等敏感信息
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List


class ConversationConfig:
    """会话配置类"""

    def __init__(self, chat_name: str, config_dir: Optional[Path] = None):
        """
        初始化会话配置

        Args:
            chat_name: 会话名称
            config_dir: 配置目录,默认为 data/{chat_name}/
        """
        self.chat_name = chat_name
        self.config_dir = config_dir or Path("data") / self._sanitize_name(chat_name)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 配置文件路径(使用 .confignore 避免被 git 追踪)
        self.config_file = self.config_dir / ".confignore"

        # 加载配置
        self.config_data = self._load_config()

    def _sanitize_name(self, name: str) -> str:
        """清理会话名称,用作文件夹名"""
        # 移除非法字符
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        # 替换空格为下划线
        safe_name = safe_name.replace(' ', '_')
        return safe_name or "default_chat"

    def _load_config(self) -> Dict:
        """加载配置文件（只存储 api_key）"""
        if not self.config_file.exists():
            # 创建默认配置（只包含 api_key）
            default_config = {
                "api_key": ""
            }
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ConversationConfig] Failed to load config: {e}")
            return {}

    def _save_config(self, config: Dict) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ConversationConfig] Failed to save config: {e}")
            return False

    # === 配置访问方法 ===

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config_data.get(key, default)

    def set(self, key: str, value) -> bool:
        """设置配置项并保存"""
        self.config_data[key] = value
        return self._save_config(self.config_data)

    def get_api_key(self) -> str:
        """获取 API key"""
        return self.get("api_key", "")

    def set_api_key(self, api_key: str) -> bool:
        """设置 API key"""
        return self.set("api_key", api_key)

    def delete_config(self) -> bool:
        """删除配置文件"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except Exception as e:
            print(f"[ConversationConfig] Failed to delete config: {e}")
            return False


class ConversationConfigManager:
    """会话配置管理器 - 管理多个会话的配置"""

    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self._configs: Dict[str, ConversationConfig] = {}

    def get_config(self, chat_name: str) -> ConversationConfig:
        """
        获取或创建会话配置

        Args:
            chat_name: 会话名称

        Returns:
            ConversationConfig 实例
        """
        if chat_name not in self._configs:
            self._configs[chat_name] = ConversationConfig(chat_name)
        return self._configs[chat_name]

    def list_all_conversations(self) -> List[str]:
        """列出所有已存在的会话"""
        conversations = []
        for item in self.data_dir.iterdir():
            if item.is_dir() and (item / ".confignore").exists():
                conversations.append(item.name)
        return conversations

    def delete_conversation(self, chat_name: str) -> bool:
        """
        删除会话配置和文件夹

        Args:
            chat_name: 会话名称

        Returns:
            是否删除成功
        """
        if chat_name in self._configs:
            del self._configs[chat_name]

        chat_dir = self.data_dir / ConversationConfig(chat_name)._sanitize_name(chat_name)

        if not chat_dir.exists():
            return False

        try:
            import shutil
            shutil.rmtree(chat_dir)
            return True
        except Exception as e:
            print(f"[ConversationConfigManager] Failed to delete conversation: {e}")
            return False

    def conversation_exists(self, chat_name: str) -> bool:
        """检查会话是否存在"""
        chat_dir = self.data_dir / ConversationConfig(chat_name)._sanitize_name(chat_name)
        return chat_dir.exists() and (chat_dir / ".confignore").exists()


# 全局单例
_global_config_manager: Optional[ConversationConfigManager] = None


def get_global_config_manager() -> ConversationConfigManager:
    """获取全局配置管理器单例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConversationConfigManager()
    return _global_config_manager
