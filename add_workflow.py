"""Add file operations workflow to prefab_file_operator.json"""
import json

with open('prefab_file_operator.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 检查是否已有文件操作工作流程
if '【CRITICAL: File Operations Workflow】' not in data['system_prompt']:
    # 在 system_prompt 末尾添加文件操作工作流程
    workflow = '\n\n【CRITICAL: File Operations Workflow】\n'
    workflow += '**MUST READ**: Before ANY file operation, you MUST:\n\n'
    workflow += '1. READ the complete tool description\n'
    workflow += '2. CHECK if the description mentions required prerequisites\n'
    workflow += '3. FOLLOW any documented workflows EXACTLY\n\n'
    workflow += 'Examples:\n'
    workflow += '- User: "List my desktop"\n'
    workflow += '  Steps:\n'
    workflow += '    1. Read the file operation tool description\n'
    workflow += '    2. If it says "Call system info tool first", DO IT\n'
    workflow += '    3. Use the actual paths from the system info\n'
    workflow += '    4. Call the file operation with correct paths\n\n'
    workflow += 'NEVER guess or assume paths like ~, /home/user, /Users/username!\n'
    workflow += 'ALWAYS read tool descriptions to understand the correct workflow.\n'

    data['system_prompt'] += workflow

    with open('prefab_file_operator.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('Updated prefab_file_operator.json with file operations workflow')
else:
    print('File operations workflow already exists in prefab_file_operator.json')
