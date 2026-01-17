# [file name]: test_auto_sync.py
"""
Test script for automatic chat_list synchronization with data directory
"""

import os
import json
from pathlib import Path
from utils.config_manager import ConfigManager
from utils.chat_data_manager import ChatDataManager

def test_auto_sync():
    """Test automatic chat_list synchronization"""
    print("=" * 70)
    print("Testing Automatic chat_list Synchronization")
    print("=" * 70)

    config_manager = ConfigManager()
    chat_data_manager = ChatDataManager()

    # Test 1: Create some chat folders
    print("\n[Test 1] Creating test chat folders...")
    test_chats = ["chat_alpha", "chat_beta", "chat_gamma"]
    for chat_name in test_chats:
        chat_data_manager.create_chat_folder(chat_name)
        # Create a settings file to make it valid
        settings_path = chat_data_manager.get_settings_path(chat_name)
        with open(settings_path, 'w') as f:
            json.dump({"test": f"data for {chat_name}"}, f)
    print(f"Created {len(test_chats)} test chat folders")

    # Test 2: Load chat list (should auto-sync)
    print("\n[Test 2] Loading chat list (should auto-sync with data directory)...")
    chat_list = config_manager.load_chat_list()
    print(f"Loaded chat list: {chat_list}")
    print(f"Contains all test chats: {all(chat in chat_list for chat in test_chats)}")

    # Test 3: Check app_config.json was updated
    print("\n[Test 3] Checking app_config.json was updated...")
    with open("app_config.json", 'r') as f:
        app_config = json.load(f)
    print(f"app_config.json chat_list: {app_config['chat_list']}")
    print(f"In sync with data directory: {set(app_config['chat_list']) == set(chat_list)}")

    # Test 4: Add a new chat folder externally
    print("\n[Test 4] Adding new chat folder externally...")
    new_chat = "chat_delta"
    chat_data_manager.create_chat_folder(new_chat)
    settings_path = chat_data_manager.get_settings_path(new_chat)
    with open(settings_path, 'w') as f:
        json.dump({"test": f"data for {new_chat}"}, f)
    print(f"Created new chat: {new_chat}")

    # Test 5: Load chat list again (should detect new chat)
    print("\n[Test 5] Loading chat list again (should detect new chat)...")
    updated_list = config_manager.load_chat_list()
    print(f"Updated chat list: {updated_list}")
    print(f"New chat detected: {new_chat in updated_list}")

    # Test 6: Delete a chat folder
    print("\n[Test 6] Deleting a chat folder...")
    chat_to_delete = "chat_beta"
    chat_data_manager.delete_chat_folder(chat_to_delete)
    print(f"Deleted chat: {chat_to_delete}")

    # Test 7: Load chat list (should remove deleted chat)
    print("\n[Test 7] Loading chat list (should reflect deletion)...")
    final_list = config_manager.load_chat_list()
    print(f"Final chat list: {final_list}")
    print(f"Deleted chat removed: {chat_to_delete not in final_list}")

    # Test 8: Save chat list with custom order
    print("\n[Test 8] Saving chat list with custom order...")
    custom_order = ["chat_gamma", "chat_alpha", "chat_delta"]
    config_manager.save_chat_list(custom_order)
    print(f"Tried to save custom order: {custom_order}")

    # Test 9: Verify saved order
    print("\n[Test 9] Verifying saved order...")
    with open("app_config.json", 'r') as f:
        app_config = json.load(f)
    saved_order = app_config['chat_list']
    print(f"Saved order: {saved_order}")
    print(f"Custom order preserved: {saved_order == custom_order}")

    # Test 10: Cleanup
    print("\n[Test 10] Cleaning up test data...")
    for chat_name in test_chats + [new_chat]:
        chat_data_manager.delete_chat_folder(chat_name)
    print("Cleanup complete")

    print("\n" + "=" * 70)
    print("All auto-sync tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_auto_sync()
