"""Add file operations workflow to prefab_file_operator.json"""
import json

with open('prefab_file_operator.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 检查是否已有文件操作工作流程
if '【CRITICAL: File Operations Workflow】' not in data['system_prompt']:
    # 在 system_prompt 末尾添加文件操作工作流程
    workflow = '\n\n【CRITICAL: File Operations Workflow】\n'
    workflow += '**MUST READ**: Before ANY file operation (ls, cat, mkdir, etc.), you MUST:\n\n'
    workflow += '1. FIRST call: YLDEXECUTE: get_system_info\n'
    workflow += '2. READ the result to get actual paths (desktop_dir, home_dir, etc.)\n'
    workflow += '3. THEN call the file operation with correct paths\n\n'
    workflow += 'Examples:\n'
    workflow += '- User: "List my desktop"\n'
    workflow += '  WRONG: YLDEXECUTE: ls ￥| ~/Desktop\n'
    workflow += '  CORRECT:\n'
    workflow += '    Step 1: YLDEXECUTE: get_system_info\n'
    workflow += '    Step 2: YLDEXECUTE: ls ￥| C:\\Users\\YOUR_USER\\Desktop (using actual path from step 1)\n\n'
    workflow += 'NEVER use ~, /home/user, /Users/username in paths!\n'

    data['system_prompt'] += workflow

    with open('prefab_file_operator.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('Updated prefab_file_operator.json with file operations workflow')
else:
    print('File operations workflow already exists in prefab_file_operator.json')
