# [file name]: utils/ai_history_manager.py
"""
AI Conversation History Manager - Independent from chat display history
Manages AI's conversation context, saves only valid conversations and command execution results
Now integrates with ChatDataManager for individual chat folders
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from config.i18n import i18n
from utils.chat_data_manager import ChatDataManager


class AIHistoryManager:
    """
    AI Conversation History Manager
    Manages AI's conv_his, completely separate from chat display history
    """

    # 隐藏的历史记录使用指导（代码内控制，用户不可见）
    HISTORY_USAGE_GUIDANCE = """

【Conversation History Usage Guidelines】
1. **Reference Only**: Use conversation history only as a knowledge base for reference
2. **Focus on Current Question**: Only answer what the user is currently asking, unless explicitly requested to review or summarize previous conversations
3. **Avoid Unnecessary Association**: Do not make assumptions or establish connections between unrelated conversations
4. **No Retroactive Summarization**: When answering simple questions, do not summarize or evaluate the entire conversation session
5. **Independent Responses**: Each response should focus on the current question, do not continuously reference or expand based on previous topics
6. **Exception**: If the user explicitly requests a summary, review, or correlation analysis, follow the user's specific requirements
"""

    def get_history_usage_guidance(self):
        """Get history usage guidance (in English for AI understanding)"""
        return self.HISTORY_USAGE_GUIDANCE

    def __init__(self, ai_conv_dir: str = "ai_conv"):
        self.ai_conv_dir = Path(ai_conv_dir)
        self.ai_conv_dir.mkdir(exist_ok=True, parents=True)
        self.chat_data_manager = ChatDataManager()
    
    def get_history_file(self, conversation_name: str) -> Path:
        """Get conversation history file path"""
        # Clean invalid characters from filename
        safe_name = "".join(c for c in conversation_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.strip() or "default"
        return self.ai_conv_dir / f"{safe_name}_ai.json"
    
    def _user_has_history_instructions(self, system_prompt: str) -> bool:
        """检查用户的 system_prompt 是否已经包含明确的历史记录使用指示"""
        if not system_prompt:
            return False

        # 检查是否包含明确的历史记录使用相关关键词
        history_keywords = [
            '历史记录', 'history', 'conversation history',
            '上下文', 'context', 'previous conversation',
            '总结历史', 'summarize history', 'recap'
        ]

        system_lower = system_prompt.lower()
        for keyword in history_keywords:
            if keyword.lower() in system_lower:
                return True

        return False

    def load_history(self, conversation_name: str, system_prompt: str = None) -> List[Dict]:
        """Load AI conversation history"""
        # Try new ChatDataManager first
        loaded_history = self.chat_data_manager.load_ai_history(conversation_name)
        if loaded_history is not None:
            print(f"[AIHistory] Loaded {len(loaded_history)} messages from ChatDataManager")

            # Ensure system prompt is at the beginning
            return self._ensure_system_prompt(loaded_history, system_prompt)

        # Fall back to old method for backward compatibility
        history_file = self.get_history_file(conversation_name)
        loaded_history = []

        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    loaded_history = json.load(f)
                print(f"[AIHistory] Loaded {len(loaded_history)} messages from {history_file}")
            except Exception as e:
                print(f"[AIHistory] Failed to load history: {e}")

        # Ensure system prompt is at the beginning
        return self._ensure_system_prompt(loaded_history, system_prompt)

    def _ensure_system_prompt(self, loaded_history: List[Dict], system_prompt: str = None) -> List[Dict]:
        """Ensure system prompt is at the beginning of history"""
        if system_prompt:
            # 移除所有现有的 system 消息
            filtered_history = [msg for msg in loaded_history if msg.get("role") != "system"]

            # 构建完整的 system prompt
            final_system_prompt = system_prompt

            # 检查用户是否已经提供了明确的历史记录使用指示
            if not self._user_has_history_instructions(system_prompt):
                # 自动注入隐藏的历史记录使用指导（使用 i18n）
                final_system_prompt = system_prompt + self.get_history_usage_guidance()
                print(f"[AIHistory] Injected history usage guidance (user had no specific instructions)")

            # 添加完整的 system prompt 到开头
            filtered_history.insert(0, {"role": "system", "content": final_system_prompt})
            return filtered_history
        elif loaded_history and loaded_history[0].get("role") == "system":
            return loaded_history
        else:
            # Return default system prompt with history guidance (使用 i18n)
            default_prompt = "You are an AI assistant that can execute commands when requested."
            return [
                {"role": "system", "content": default_prompt + self.get_history_usage_guidance()}
            ]
    
    def save_history(self, conversation_name: str, history: List[Dict]):
        """Save AI conversation history"""
        # Save using new ChatDataManager
        success = self.chat_data_manager.save_ai_history(conversation_name, history)
        if success:
            print(f"[AIHistory] Saved {len(history)} messages to ChatDataManager")

        # Also save to old location for backward compatibility
        history_file = self.get_history_file(conversation_name)

        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"[AIHistory] Saved {len(history)} messages to {history_file}")
        except Exception as e:
            print(f"[AIHistory] Failed to save history: {e}")
    
    def add_message_pair(self, conversation_name: str, user_input: str, assistant_response: str) -> List[Dict]:
        """Add user-assistant message pair to history"""
        history = self.load_history(conversation_name)
        
        # Add user message
        history.append({"role": "user", "content": user_input})
        
        # Add assistant message
        history.append({"role": "assistant", "content": assistant_response})
        
        self.save_history(conversation_name, history)
        return history
    
    def clear_history(self, conversation_name: str, system_prompt: str = None):
        """Clear conversation history, keep only system prompt"""
        if system_prompt:
            history = [{"role": "system", "content": system_prompt}]
        else:
            history = [
                {"role": "system", "content": "You are an AI assistant that can execute commands when requested."}
            ]

        self.save_history(conversation_name, history)
        print(f"[AIHistory] Cleared history for {conversation_name}")

    def delete_history(self, conversation_name: str):
        """Delete conversation history file"""
        # Delete from ChatDataManager (this deletes entire chat folder)
        # Note: We don't do this here as it should be called from a higher level
        # Just delete the old location for now
        history_file = self.get_history_file(conversation_name)

        if history_file.exists():
            try:
                history_file.unlink()
                print(f"[AIHistory] Deleted history file: {history_file}")
            except Exception as e:
                print(f"[AIHistory] Failed to delete history: {e}")
        else:
            print(f"[AIHistory] History file does not exist: {history_file}")