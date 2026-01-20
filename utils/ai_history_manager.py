# [file name]: utils/ai_history_manager.py
"""
AI Conversation History Manager - Independent from chat display history
Manages AI's conversation context, saves only valid conversations and command execution results
All data is stored in data/{chat_name}/ directory structure
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional

from utils.chat_data_manager import ChatDataManager


def _load_default_prompts() -> Dict:
    """Load default prompts from configuration file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'default_prompts.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[AIHistory] Failed to load default_prompts.json: {e}")

    # Return minimal fallback if file doesn't exist
    return {
        "system_prompts": {
            "fallback": "You are an AI assistant that can execute commands when requested."
        },
        "history_usage_guidance": "\n\n【Conversation History Usage Guidelines】\n1. **Reference Only**: Use conversation history only as a knowledge base for reference\n2. **Focus on Current Question**: Only answer what the user is currently asking\n"
    }

# Load once at module level
_DEFAULT_PROMPTS = _load_default_prompts()


class AIHistoryManager:
    """
    AI Conversation History Manager
    Manages AI's conversation history, completely separate from chat display history
    All data is stored in data/{chat_name}/ directory
    """

    def get_history_usage_guidance(self):
        """Get history usage guidance (in English for AI understanding)"""
        return _DEFAULT_PROMPTS.get('history_usage_guidance', '')

    def __init__(self):
        self.chat_data_manager = ChatDataManager()

    def _user_has_history_instructions(self, system_prompt: str) -> bool:
        """Check if user's system_prompt already contains explicit history usage instructions"""
        if not system_prompt:
            return False

        # Check for explicit history usage related keywords
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
        """Load AI conversation history from data/{chat_name}/{chat_name}_ai.json"""
        loaded_history = self.chat_data_manager.load_ai_history(conversation_name)

        if loaded_history is None:
            loaded_history = []
            print(f"[AIHistory] No existing history found for {conversation_name}")
        else:
            print(f"[AIHistory] Loaded {len(loaded_history)} messages from data/{conversation_name}/")

        # Ensure system prompt is at the beginning
        return self._ensure_system_prompt(loaded_history, system_prompt)

    def _ensure_system_prompt(self, loaded_history: List[Dict], system_prompt: str = None) -> List[Dict]:
        """Ensure system prompt is at the beginning of history"""
        if system_prompt:
            # Remove all existing system messages
            filtered_history = [msg for msg in loaded_history if msg.get("role") != "system"]

            # Build complete system prompt
            final_system_prompt = system_prompt

            # Check if user already provided explicit history usage instructions
            if not self._user_has_history_instructions(system_prompt):
                # Auto-inject hidden history usage guidance
                final_system_prompt = system_prompt + self.get_history_usage_guidance()
                print(f"[AIHistory] Injected history usage guidance (user had no specific instructions)")

            # Add complete system prompt at the beginning
            filtered_history.insert(0, {"role": "system", "content": final_system_prompt})
            return filtered_history
        elif loaded_history and loaded_history[0].get("role") == "system":
            return loaded_history
        else:
            # Return default system prompt with history guidance
            default_prompt = _DEFAULT_PROMPTS.get('system_prompts', {}).get('fallback', "You are an AI assistant that can execute commands when requested.")
            return [
                {"role": "system", "content": default_prompt + self.get_history_usage_guidance()}
            ]

    def save_history(self, conversation_name: str, history: List[Dict]):
        """Save AI conversation history to data/{chat_name}/{chat_name}_ai.json"""
        success = self.chat_data_manager.save_ai_history(conversation_name, history)

        if success:
            print(f"[AIHistory] Saved {len(history)} messages to data/{conversation_name}/")
        else:
            print(f"[AIHistory] Failed to save history for {conversation_name}")

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
        """
        Delete conversation history file.
        Note: This is handled by ChatDataManager.delete_chat_folder() which deletes the entire chat folder.
        This method is kept for API compatibility but doesn't need to do anything.
        """
        print(f"[AIHistory] History deletion for {conversation_name} will be handled by chat folder deletion")
