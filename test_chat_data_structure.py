# [file name]: test_chat_data_structure.py
"""
Test script for the new chat data structure
Verifies that ChatDataManager works correctly
"""

import os
import json
from pathlib import Path
from utils.chat_data_manager import ChatDataManager

def test_chat_data_manager():
    """Test the ChatDataManager functionality"""
    print("=" * 60)
    print("Testing ChatDataManager")
    print("=" * 60)

    manager = ChatDataManager()
    test_chat_name = "test_chat_1"

    # Test 1: Create chat folder
    print("\n[Test 1] Creating chat folder...")
    chat_dir = manager.create_chat_folder(test_chat_name)
    print(f"Created: {chat_dir}")
    print(f"Exists: {chat_dir.exists()}")
    print(f"Has tools dir: {(chat_dir / 'tools').exists()}")

    # Test 2: Save and load settings
    print("\n[Test 2] Testing settings save/load...")
    test_settings = {
        "api_base": "https://api.test.com",
        "model": "test-model",
        "mcp_paths": [],
        "temperature": 0.7
    }
    manager.save_chat_settings(test_chat_name, test_settings)
    loaded_settings = manager.load_chat_settings(test_chat_name)
    print(f"Saved settings: {test_settings}")
    print(f"Loaded settings: {loaded_settings}")
    print(f"Match: {loaded_settings['api_base'] == test_settings['api_base']}")

    # Test 3: Copy MCP tool
    print("\n[Test 3] Testing MCP tool copying...")
    # Create a dummy MCP file first
    dummy_mcp_path = Path("test_dummy_mcp.py")
    dummy_mcp_path.write_text("# Dummy MCP tool\ndef test_func():\n    pass\n")

    copied_path = manager.copy_mcp_tool_to_chat(test_chat_name, str(dummy_mcp_path))
    print(f"Original path: {dummy_mcp_path}")
    print(f"Copied path: {copied_path}")
    print(f"Copy exists: {Path(copied_path).exists() if copied_path else False}")

    # Update settings with MCP path
    if copied_path:
        test_settings["mcp_paths"] = [copied_path]
        manager.save_chat_settings(test_chat_name, test_settings)
        loaded_with_mcp = manager.load_chat_settings(test_chat_name)
        print(f"Settings with MCP: {loaded_with_mcp['mcp_paths']}")

    # Test 4: List all chats
    print("\n[Test 4] Listing all chats...")
    all_chats = manager.list_all_chats()
    print(f"All chats: {all_chats}")
    print(f"Test chat in list: {test_chat_name in all_chats}")

    # Test 5: Save and load AI history
    print("\n[Test 5] Testing AI history save/load...")
    test_ai_history = [
        {"role": "system", "content": "You are a test assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    manager.save_ai_history(test_chat_name, test_ai_history)
    loaded_ai_history = manager.load_ai_history(test_chat_name)
    print(f"Saved {len(test_ai_history)} messages")
    print(f"Loaded {len(loaded_ai_history)} messages")
    print(f"Match: {len(loaded_ai_history) == len(test_ai_history)}")

    # Test 6: Save and load chat history
    print("\n[Test 6] Testing chat history save/load...")
    test_chat_history = [
        {"is_sender": True, "text": "User message"},
        {"is_sender": False, "text": "AI response"}
    ]
    manager.save_chat_history(test_chat_name, test_chat_history)
    loaded_chat_history = manager.load_chat_history(test_chat_name)
    print(f"Saved {len(test_chat_history)} messages")
    print(f"Loaded {len(loaded_chat_history)} messages")

    # Test 7: Delete chat folder
    print("\n[Test 7] Deleting chat folder...")
    print(f"Chat exists before delete: {manager.chat_exists(test_chat_name)}")
    success = manager.delete_chat_folder(test_chat_name)
    print(f"Delete success: {success}")
    print(f"Chat exists after delete: {manager.chat_exists(test_chat_name)}")

    # Cleanup dummy file
    if dummy_mcp_path.exists():
        dummy_mcp_path.unlink()
        print(f"Cleaned up dummy file: {dummy_mcp_path}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

    # Show final structure
    print("\n[Final Structure] Data directory contents:")
    data_dir = Path("data")
    if data_dir.exists():
        for item in data_dir.iterdir():
            print(f"  - {item.name}")
    else:
        print("  (data directory not created)")

if __name__ == "__main__":
    test_chat_data_manager()
