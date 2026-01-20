# [file name]: aiclass.py
"""
Lynexus AI Assistant - Complete version with proper history management
保持所有原始功能，包括：
1. 系统提示集成
2. 完整的对话历史上下文
3. 流式和非流式处理
4. 命令执行迭代
5. MCP工具加载
"""

from datetime import datetime
import os
import sys
import importlib.util
import json
from typing import List, Dict, Generator, Optional
from openai import OpenAI
from mcp_utils import MCPServerManager, load_mcp_conf


def _load_default_prompts() -> Dict:
    """Load default prompts from configuration file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'default_prompts.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[AI] Failed to load default_prompts.json: {e}")

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
        config_path = os.path.join(os.path.dirname(__file__), 'default_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[AI] Failed to load default_config.json: {e}")

    # Return minimal fallback if file doesn't exist
    return {
        "api": {
            "api_base": "https://api.deepseek.com",
            "model": "deepseek-chat"
        }
    }

# Load once at module level
_DEFAULT_PROMPTS = _load_default_prompts()
_DEFAULT_CONFIG = _load_default_config()


class AI:
    """
    完整的AI助手类，支持流式、命令执行和完整历史管理
    """
    
    def __init__(self,
                # 基本配置
                mcp_paths=None,
                api_key=None,
                api_base=None,
                model=None,

                # 会话名称 (用于加载独立配置)
                chat_name=None,

                # 系统提示
                system_prompt=None,

                # 模型参数
                temperature=1.0,
                max_tokens=2048,
                top_p=1.0,
                stop=None,
                stream=True,  # 默认流式
                presence_penalty=0.0,
                frequency_penalty=0.0,

                # 命令解析
                command_start="YLDEXECUTE:",
                command_separator="￥|",

                # 命令执行
                max_iterations=15,

                # 自定义提示词（可从设置对话框配置）
                command_execution_prompt=None,
                command_retry_prompt=None,
                final_summary_prompt=None):  # Removed redundant max_execution_iterations

        # 工具配置
        self.mcp_paths = mcp_paths if mcp_paths is not None else []
        self.funcs = {}
        self.mcp_managers = {}  # 存储每个 server 的 MCPServerManager 实例

        # MCP 工具描述字典 - 独立于 system_prompt
        self.mcp_tools_desc = {}  # {tool_name: description}
        self.enabled_mcp_tools = set()  # 已启用的 MCP 工具集合

        # 会话配置管理
        self.chat_name = chat_name or "default"
        self.conversation_config = None

        # 如果提供了会话名称,从配置文件加载 API key
        if chat_name:
            try:
                from utils.conversation_config import get_global_config_manager
                config_manager = get_global_config_manager()
                self.conversation_config = config_manager.get_config(chat_name)

                # 从配置文件加载 API key (如果未提供)
                if not api_key:
                    api_key = self.conversation_config.get_api_key()
                    if api_key:
                        print(f"[AI] Loaded API key from conversation config: {chat_name}")

                # 从配置文件加载其他配置
                if not api_base:
                    api_base = self.conversation_config.get_api_base()
                if not model:
                    model = self.conversation_config.get_model()
            except Exception as e:
                print(f"[AI] Failed to load conversation config: {e}")

        # API配置
        self.api_key = api_key
        self.api_base = api_base or _DEFAULT_CONFIG.get('api', {}).get('api_base', 'https://api.deepseek.com')
        self.model = model or _DEFAULT_CONFIG.get('api', {}).get('model', 'deepseek-chat')
        self.client = None

        # 命令配置
        self.command_start = command_start
        self.command_separator = command_separator
        self.max_iterations = max_iterations

        # 自定义提示词（从配置或使用默认值）
        self.command_execution_prompt = command_execution_prompt or _DEFAULT_PROMPTS.get('command_execution_prompt', '')

        self.command_retry_prompt = command_retry_prompt or _DEFAULT_PROMPTS.get('command_retry_prompt', '')

        self.final_summary_prompt = final_summary_prompt or _DEFAULT_PROMPTS.get('final_summary_prompt', '')

        # 模型参数
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stop = stop
        self.stream = stream  # 存储流式参数
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty

        # 内部对话历史 - 由外部管理，但这里保留用于处理
        self.conv_his = []

        # 执行状态跟踪
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }

        # 环境信息检测
        self.env_info = self._detect_environment()

        # 停止标志
        self._stop_flag = False

        # 初始化AI客户端
        self.init_ai_client()

        # 加载MCP工具 - 必须在生成系统提示之前
        self.load_mcp_tools()

        # 系统提示 - 保存用户的原始 system_prompt（不包含 Markdown 规范）
        if system_prompt:
            self.user_system_prompt = system_prompt
        else:
            self.user_system_prompt = self.get_complete_system_prompt()

        # system_prompt 将在需要时动态组合（用户提示 + 工具描述 + Markdown 规范）
        self.system_prompt = self.user_system_prompt

        # 重置对话历史（添加系统提示）
        self.reset_conversation()
        
        print(f"[AI] 初始化完成，加载了 {len(self.funcs)} 个工具，stream={self.stream}")

    def _sanitize_name(self, name: str) -> str:
        """清理会话名称，用作文件夹名"""
        import re
        # 移除非法字符
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        # 替换空格为下划线
        safe_name = safe_name.replace(' ', '_')
        return safe_name or "default_chat"

    def _detect_environment(self) -> Dict[str, str]:
        """检测当前环境信息"""
        import platform
        env_info = {}

        # 操作系统
        env_info['os'] = platform.system()
        env_info['os_release'] = platform.release()

        # 用户名
        env_info['username'] = os.path.expanduser('~').split(os.sep)[-1]

        # 关键路径
        home_dir = os.path.expanduser('~')
        env_info['home_dir'] = home_dir

        # 桌面路径
        if env_info['os'] == 'Windows':
            desktop_dir = os.path.join(os.path.expandvars('%USERPROFILE%'), 'Desktop')
            if not os.path.exists(desktop_dir):
                # 备选方案
                desktop_dir = os.path.join(home_dir, 'Desktop')
        else:
            # Linux/Mac
            desktop_dir = os.path.join(home_dir, 'Desktop')

        env_info['desktop_dir'] = desktop_dir if os.path.exists(desktop_dir) else home_dir

        # 当前工作目录
        env_info['cwd'] = os.getcwd()

        return env_info

    def get_complete_system_prompt(self):
        """返回完整的系统提示"""
        # 生成工具描述
        tools_desc = self.gen_tools_desc()

        # 基础系统提示
        base_prompt = f"""
You are an AI assistant that can directly execute commands and call available tools.

【CRITICAL: File Operations Workflow】
When user asks about "my desktop", "my home directory", "my files", or any path-related question:
1. FIRST call: YLDEXECUTE: get_system_info
2. Parse the JSON result to get actual paths (desktop_dir, home_dir, etc.)
3. THEN call the appropriate file operation function with the correct path
4. Provide the final answer to the user

DO NOT guess or assume paths. Always use get_system_info() first.

【Core Principles】
1. **Strict Response Mode**:
- When the user explicitly requests an operation (query, search, file operations, etc.), **only output one line {self.command_start} instruction**, without any other text
- When the user requests content creation, answers questions, or normal conversation, **directly output the content itself**, without any additional explanations
- When the user says "continue", only output the next {self.command_start} instruction, without any explanation

2. **Accurate Understanding of Intent**:
- User states facts (e.g., "I'm from Jinan") → Respond directly to the fact, do not call tools
- User explicitly requests operations (e.g., "save file to desktop") → Call the corresponding tool

3. **Use Correct Tools and Syntax**:
- Only use actually available tools
- Ensure command syntax is correct, especially for file operations

【Output Format Requirements】
- **IMPORTANT**: Always format your responses using **Markdown** for better readability
- Use proper headings (##, ###), bullet points, code blocks, and bold text where appropriate
- For code examples, use triple backticks (```) to create code blocks
- For structured information, use tables or lists
- Keep responses well-organized and easy to scan

Before executing MCP tools, please check:
1. Are all required parameters provided in the correct format?
2. Are parameter value types correct (numbers/strings/booleans)?
3. Are there additional optional parameters that can be provided?
4. If there's an error, try multiple parameter formats, such as 2, peoplecount=2, etc.

If unsure, ask the user what parameters are needed.

【Call Format】
- `{self.command_start} tool_name {self.command_separator} param1 {self.command_separator} param2 {self.command_separator} ...`
- Or direct system command: `{self.command_start} command {self.command_separator} param1 {self.command_separator} param2 {self.command_separator} ...`

【Strictly Prohibited】
1. Do not add explanatory text before or after any {self.command_start} instruction
2. Do not actively plan multi-step operations when not explicitly requested by user
3. Do not use incorrect command syntax (especially for file operations)
4. Do not output words like "I'll", "let me", "try", "now", "then", etc.
5. Do not provide alternative suggestions or explain reasons when operations fail
6. Do not combine multiple operations into one instruction without explicit user request

【Error Examples】
User: I'm from Jinan
Wrong: {self.command_start} weather {self.command_separator} Jinan # (User is just stating, not requesting query)

User: continue
Wrong: [AI] Now getting current date... # (Should only output {self.command_start} instruction, no explanation)

User: save file
Wrong: {self.command_start} echo {self.command_separator} content {self.command_separator} 2 {self.command_separator} file_path # (Incorrect redirection syntax)

【Multi-step Operation Rules】
1. Only execute multiple steps when user explicitly requests multiple operations
2. Execute only one step at a time, wait for user to say "continue" before next step
3. Output only one {self.command_start} instruction per step, without any other text
4. Do not decompose tasks on your own if user doesn't explicitly request multiple steps

【Error Handling】
- If execution fails, directly reply "Operation failed" (non-{self.command_start} situation) or wait for further user instructions
- Do not explain reasons, do not provide alternatives

Please strictly follow these rules to ensure responses are concise, accurate, and meet actual user needs.
"""

        # 组合完整的系统提示：工具描述 + 基础提示
        full_prompt = base_prompt.strip()

        if tools_desc:
            full_prompt = tools_desc + "\n\n" + base_prompt.strip()

        return full_prompt
    
    # === MCP工具加载 ===
    
    def load_mcp_mod(self, mcp_path):
        """加载一个MCP文件(*.json或*.py)"""
        try:
            if mcp_path.endswith('.json'):
                mcp_manager = MCPServerManager()
                tool_names = load_mcp_conf(mcp_path, mcp_manager)
                
                if not tool_names:
                    return None, {}
                
                funcs = {}
                
                for ser_name in mcp_manager.servers.keys():
                    for tool in mcp_manager.tools.get(ser_name, []):
                        tool_name = tool.get('name', '')
                        if tool_name:
                            func_name = f"mcp_{ser_name}_{tool_name}"
                            def make_tool_func(name_ser, name_tool, desc):
                                def tool_func(**kwargs):
                                    res = mcp_manager.call_tool(name_ser, name_tool, kwargs)
                                    return json.dumps(res, ensure_ascii=False, indent=2)
                                tool_func.__name__ = name_tool
                                tool_func.__doc__ = tool.get('description', desc)
                                return tool_func
                            funcs[func_name] = make_tool_func(ser_name, tool_name, tool.get('description', 'No description'))
                
                class MCPModule:
                    def __init__(self):
                        self.manager = mcp_manager
                return MCPModule(), funcs
                        
            else:
                # Python文件
                module_name = os.path.basename(mcp_path).replace('.py', '')
                spec = importlib.util.spec_from_file_location(module_name, mcp_path)
                if spec is None:
                    raise ImportError(f"Cannot load module from {mcp_path}")
                
                mcp_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mcp_module
                spec.loader.exec_module(mcp_module)
                
                funcs = {}
                for attr_name in dir(mcp_module):
                    attr = getattr(mcp_module, attr_name)
                    if callable(attr) and not attr_name.startswith('_'):
                        funcs[attr_name] = attr
                        
                return mcp_module, funcs
            
        except Exception as e:
            print(f"[Warning] Load failed: {e}")
            return None, {}
    
    def load_mcp_tools(self):
        """从路径加载MCP工具"""
        if not self.mcp_paths:
            print("[Info] No MCP paths to load")
            self.enabled_mcp_tools = set()
            return

        print(f"[Info] Loading {len(self.mcp_paths)} MCP tools during initialization...")

        # 直接加载工具
        self._load_mcp_from_paths()

        # 如果 enabled_mcp_tools 为空，默认启用所有加载的工具
        # 用户可以通过设置对话框禁用不需要的工具
        if not self.enabled_mcp_tools and self.mcp_tools_desc:
            self.enabled_mcp_tools = set(self.mcp_tools_desc.keys())
            print(f"[Info] Auto-enabled all {len(self.enabled_mcp_tools)} loaded tools")
        elif self.enabled_mcp_tools:
            # 只保留仍然存在的工具
            self.enabled_mcp_tools = self.enabled_mcp_tools.intersection(set(self.mcp_tools_desc.keys()))
            print(f"[Info] Kept {len(self.enabled_mcp_tools)} previously enabled tools")

        print(f"[Info] Loaded {len(self.funcs)} tools, {len(self.enabled_mcp_tools)} tools enabled")

    def reload_mcp_tools(self, mcp_paths=None):
        """按需重新加载 MCP 工具（从 settings 或会话配置）"""
        if mcp_paths is None:
            mcp_paths = self.mcp_paths

        if not mcp_paths:
            print("[Info] No MCP paths to load")
            return

        print(f"[Info] Loading {len(mcp_paths)} MCP tools on demand...")

        # 使用加载逻辑
        self._load_mcp_from_paths()

        # 保留现有的 enabled_mcp_tools 设置，或者启用所有新工具
        if self.enabled_mcp_tools:
            # 只保留仍然存在的工具
            self.enabled_mcp_tools = self.enabled_mcp_tools.intersection(set(self.mcp_tools_desc.keys()))
        elif self.mcp_tools_desc:
            # 如果没有启用任何工具，默认启用所有
            self.enabled_mcp_tools = set(self.mcp_tools_desc.keys())
        print(f"[Info] Reloaded {len(self.funcs)} tools, {len(self.enabled_mcp_tools)} tools enabled")

    def _load_mcp_from_paths(self):
        """从指定路径加载 MCP 工具"""
        # 不再自动添加默认工具
        # 用户必须明确添加工具

        # 验证路径并转换为绝对路径
        valid_paths = []
        for path in self.mcp_paths:
            # 如果是绝对路径且存在，直接使用
            if os.path.isabs(path) and os.path.exists(path):
                valid_paths.append(path)
                continue

            # 如果是相对路径，只从 data/chat_name/tools/ 查找
            if not os.path.isabs(path):
                # 处理相对路径（移除 ./ 前缀）
                if path.startswith("./"):
                    relative_filename = path[2:]  # 移除 ./
                elif path.startswith(".\\"):
                    relative_filename = path[3:]  # 移除 .\
                else:
                    relative_filename = path

                # 如果路径以 tools/ 开头，移除它（因为我们已经在 tools_dir 中）
                if relative_filename.startswith("tools/"):
                    relative_filename = relative_filename[6:]  # 移除 "tools/"
                elif relative_filename.startswith("tools\\"):
                    relative_filename = relative_filename[6:]  # 移除 "tools\"

                # 只从 data/chat_name/tools/ 目录查找
                if self.chat_name:
                    chat_dir = os.path.join("data", self._sanitize_name(self.chat_name))
                    tools_dir = os.path.join(chat_dir, "tools")
                    chat_path = os.path.join(tools_dir, relative_filename)

                    if os.path.exists(chat_path):
                        abs_path = os.path.abspath(chat_path)
                        valid_paths.append(abs_path)
                    else:
                        print(f"[Warning] MCP tool not found: {path}")
                else:
                    print(f"[Warning] No chat_name set, cannot resolve relative path: {path}")
            elif os.path.exists(path):
                valid_paths.append(path)
                print(f"[Debug]   Path exists, using: {path}")
            else:
                print(f"[Warning] File does not exist: {path}")

        if not valid_paths:
            print("[Warning] No valid MCP file paths found")
            return

        print(f"[Info] Will load {len(valid_paths)} MCP files")

        # 加载有效的MCP文件
        _, self.funcs = self.load_mult_mcp_mod(valid_paths)

        # 存储工具描述到字典(不直接加入 system_prompt)
        if self.funcs:
            for func_name, func in self.funcs.items():
                doc = func.__doc__ or "No description"
                self.mcp_tools_desc[func_name] = doc
                # Tool loaded successfully (silent)
            print(f"[Info] Loaded {len(self.mcp_tools_desc)} tools from {len(valid_paths)} files")

    def _load_mcp_from_config(self, config_path: str = None):
        """从 MCP 配置文件加载工具 - 为每个 server 创建独立的 MCPServerManager 实例

        Args:
            config_path: 配置文件路径,默认为 ./tools/mcp_config.json
        """
        import json

        config_path = config_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "mcp_config.json")

        if not os.path.exists(config_path):
            print(f"[Warning] MCP config file not found at: {config_path}")
            return

        try:
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            servers_config = config_data.get("servers", {})

            if not servers_config:
                print("[Warning] No servers defined in MCP config")
                return

            print(f"[Info] Found {len(servers_config)} MCP servers in config")

            # 存储所有 MCP server 管理器实例
            self.mcp_managers = {}
            self.funcs = {}

            # 为每个 server 创建独立的 MCPServerManager 实例
            for server_name, server_config in servers_config.items():
                print(f"[Info] Initializing MCP server: {server_name}")

                try:
                    # 创建独立的 MCPServerManager 实例
                    mcp_manager = MCPServerManager()

                    # 构建配置字符串 (mcp_utils.py 需要的格式)
                    server_json = json.dumps({
                        "mcpServers": {
                            server_name: server_config
                        }
                    })

                    # 解析配置
                    if not mcp_manager.parse_config(server_json):
                        print(f"[Warning] Failed to parse config for {server_name}")
                        continue

                    # 启动 server 进程
                    if not mcp_manager.start_ser(server_name):
                        print(f"[Warning] Failed to start server {server_name}")
                        continue

                    # 初始化 server 并获取工具列表
                    if not mcp_manager.init_ser(server_name):
                        print(f"[Warning] Failed to initialize server {server_name}")
                        continue

                    # 保存 manager 实例
                    self.mcp_managers[server_name] = mcp_manager

                    # 为该 server 的所有工具创建函数
                    server_tools = mcp_manager.tools.get(server_name, [])
                    print(f"[Info] Server {server_name} provides {len(server_tools)} tools")

                    for tool in server_tools:
                        tool_name = tool.get('name', '')
                        if not tool_name:
                            continue

                        # 创建函数名: mcp_servername_toolname
                        func_name = f"mcp_{server_name}_{tool_name}"
                        tool_desc = tool.get('description', 'No description')

                        # 创建工具函数 (使用闭包捕获 manager 和 server_name)
                        def make_tool_func(manager, ser_name, t_name, t_desc):
                            def tool_func(**kwargs):
                                try:
                                    result = manager.call_tool(ser_name, t_name, kwargs)
                                    return json.dumps(result, ensure_ascii=False, indent=2)
                                except Exception as e:
                                    error_result = {"error": str(e)}
                                    return json.dumps(error_result, ensure_ascii=False, indent=2)

                            tool_func.__name__ = t_name
                            tool_func.__doc__ = t_desc
                            tool_func.__server_name__ = ser_name  # 标记属于哪个 server
                            return tool_func

                        self.funcs[func_name] = make_tool_func(
                            mcp_manager, server_name, tool_name, tool_desc
                        )

                        print(f"[Info]   - Loaded tool: {func_name}")

                except Exception as e:
                    print(f"[Error] Failed to load server {server_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # 打印汇总信息
            print(f"[Info] Successfully loaded {len(self.funcs)} MCP tools from {len(self.mcp_managers)} servers")

            # 存储工具描述到字典(不直接加入 system_prompt)
            if self.funcs:
                for func_name, func in self.funcs.items():
                    doc = func.__doc__ or "No description"
                    self.mcp_tools_desc[func_name] = doc
                print(f"[Info] Loaded {len(self.mcp_tools_desc)} tools from MCP config")
            else:
                print("[Warning] No MCP tools loaded")

        except Exception as e:
            print(f"[Error] Failed to load MCP config: {e}")
            import traceback
            traceback.print_exc()
            # 降级到旧方法
            print("[Info] Falling back to old MCP loading method")
            self._load_mcp_from_paths()
    
    def load_mult_mcp_mod(self, mcp_paths):
        """加载多个MCP文件"""
        all_funcs = {}
        all_mods = []
        
        for path in mcp_paths:
            mod, funcs = self.load_mcp_mod(path)
            if mod:
                all_mods.append(mod)
            if funcs:
                for func_name, func in funcs.items():
                    if func_name in all_funcs:
                        print(f"[Warning] Function '{func_name}' exists in multiple MCP files, will use the last loaded version")
                    all_funcs[func_name] = func
        return all_mods, all_funcs
    
    def gen_tools_desc(self):
        """生成工具描述 - 不截断任何描述"""
        print(f"[Debug] mcp_tools_desc keys: {list(self.mcp_tools_desc.keys())}")
        print(f"[Debug] funcs keys: {list(self.funcs.keys())}")

        if not self.mcp_tools_desc:
            print("[Debug] mcp_tools_desc is empty, returning empty string")
            return ""

        desc = "【Available Tools】\nYou can use the following tools:\n\n"

        # 按服务器分组工具
        server_tools = {}
        for func_name in self.mcp_tools_desc.keys():
            if func_name in self.funcs:
                func = self.funcs[func_name]
                server_name = getattr(func, '__server_name__', 'Other')

                if server_name not in server_tools:
                    server_tools[server_name] = []

                doc = self.mcp_tools_desc[func_name]
                server_tools[server_name].append({
                    'name': func_name,
                    'desc': doc
                })

        # 为每个 server 生成工具描述(不截断)
        for server_name, tools in server_tools.items():
            desc += f"─── {server_name.upper()} SERVER ───\n"

            for tool in tools:
                tool_name = tool['name']
                tool_desc = tool['desc']

                desc += f"  • {tool_name}\n"
                desc += f"    {tool_desc}\n\n"

        # 添加使用示例
        desc += f"\n【Tool Usage】\n"
        desc += f"Format: {self.command_start} tool_name {self.command_separator} key1=value1 {self.command_separator} key2=value2\n"
        desc += f"Example: {self.command_start} mcp_filesystem_read_file {self.command_separator} path=/path/to/file.txt\n\n"

        desc += "【Important Notes】\n"
        desc += "1. Use key=value format for parameters\n"
        desc += "2. Parameter values should be properly escaped/quoted if needed\n"
        desc += "3. Only use tools from the list above\n"

        return desc

    def _get_tool_description_reading_prompt(self) -> str:
        """
        获取硬编码的工具描述阅读要求提示词
        这个提示词始终会被添加到系统提示中（当有工具启用时），确保 AI 仔细阅读工具描述
        这是框架级逻辑，不涉及用户自定义内容
        """
        return """【CRITICAL: Tool Description Reading Requirements - MANDATORY】

**MUST READ COMPLETE DESCRIPTIONS:**
You MUST carefully read the ENTIRE description for EACH tool before using it.

**PAY SPECIAL ATTENTION TO:**
Sections marked with:
- 'CRITICAL' or '**CRITICAL**'
- 'MUST' or '**MUST**'
- 'REQUIREMENT' or '**REQUIREMENT**'
- 'WORKFLOW' or '**WORKFLOW**'
- 'PREREQUISITE' or '**PREREQUISITE**'

**WHY THIS MATTERS:**
These highlighted sections contain CRITICAL information about:
- Required setup steps BEFORE using the tool
- Dependencies on OTHER tools that must be called FIRST
- Correct usage patterns and parameter order
- Common mistakes to AVOID
- Multi-step workflows that MUST be followed

**EXAMPLES OF CRITICAL WORKFLOWS:**
- Some file operations REQUIRE calling get_system_info() FIRST
- Some operations have specific prerequisite steps
- Some tools depend on results from other tools

**MANDATORY PRACTICE:**
1. BEFORE calling any tool: Read its COMPLETE description
2. Look for 'CRITICAL', 'MUST', 'REQUIREMENT' markers
3. Follow documented workflows EXACTLY
4. NEVER skip steps marked as 'REQUIRED' or 'MUST'
5. If a description says "Call X first", ALWAYS call X first

**CONSEQUENCES OF NOT READING:**
Skipping these sections will cause operations to FAIL because you won't have:
- Required information from prerequisite tools
- Correct parameter values
- Proper setup completed

FAILURE TO FOLLOW TOOL DESCRIPTION WORKFLOWS WILL RESULT IN ERRORS."""

    def _get_markdown_format_prompt(self) -> str:
        """
        获取硬编码的 Markdown 格式规范提示词
        这个提示词始终会被添加到系统提示中，确保 AI 正确使用 Markdown 格式
        """
        return """【CRITICAL: Markdown Formatting Requirements - MANDATORY】

**MANDATORY LINE BREAK RULES:**
You MUST use actual newline characters (\\n) between different points, items, or sections.
- NEVER cram multiple items into one paragraph
- ALWAYS use \\n before each bullet point
- ALWAYS use \\n before each numbered list item
- ALWAYS use \\n between different sections

**Correct Format:**
```
Here are the items:\\n
- Item 1\\n
- Item 2\\n
- Item 3
```

**Wrong Format:**
```
Here are the items: - Item 1 - Item 2 - Item 3
```

**MANDATORY STRUCTURE:**
1. Start with a brief summary (2-3 sentences max)
2. Use ## for main sections
3. Use - or * for bullet points (with \\n before each)
4. Use numbered lists (1. 2. 3.) for steps (with \\n before each)
5. Use ```language for code blocks
6. End with a brief conclusion

**LANGUAGE RULE:**
Respond in the SAME language as the user's message (Chinese→Chinese, English→English).

**Line Break Examples:**
GOOD: "Found 5 files:\\n\\n1. file1.txt\\n2. file2.txt\\n3. file3.txt"
BAD: "Found 5 files: 1. file1.txt 2. file2.txt 3. file3.txt"

GOOD: "Categories:\\n\\n- Programming\\n- Tools\\n- Documents"
BAD: "Categories: - Programming - Tools - Documents"

**Code Format:**
Always use triple backticks with language:
```python
print('hello')
```

VIOLATION OF THESE FORMATTING RULES WILL RESULT IN POOR USER EXPERIENCE.
STRICTLY ENFORCE PROPER LINE BREAKS AND STRUCTURE IN EVERY RESPONSE."""

    def get_effective_system_prompt(self):
        """
        获取有效的系统提示
        将选中的 MCP 工具描述与用户 system_prompt 组合
        注意：返回的提示词已经包含了硬编码的 Markdown 格式规范
        """
        base_prompt = self.user_system_prompt  # 使用用户的原始提示，不包含 Markdown 规范

        # No debug output for system prompt generation (reduced verbosity)

        # 获取已启用工具的描述
        if self.enabled_mcp_tools and self.mcp_tools_desc:
            enabled_desc = {}
            for tool_name in self.enabled_mcp_tools:
                if tool_name in self.mcp_tools_desc:
                    enabled_desc[tool_name] = self.mcp_tools_desc[tool_name]

            if enabled_desc:
                # 生成已启用工具的描述
                desc = "【Available Tools】\nYou can use the following tools:\n\n"

                # 按服务器分组
                server_tools = {}
                for tool_name in enabled_desc.keys():
                    if tool_name in self.funcs:
                        func = self.funcs[tool_name]
                        server_name = getattr(func, '__server_name__', 'Other')

                        if server_name not in server_tools:
                            server_tools[server_name] = []

                        server_tools[server_name].append({
                            'name': tool_name,
                            'desc': enabled_desc[tool_name]
                        })

                # 生成完整描述 - 显示工具描述，但不列出工具名列表
                for server_name, tools in server_tools.items():
                    desc += f"─── {server_name.upper()} SERVER ───\n"
                    desc += f"   Available tools: {len(tools)}\n\n"

                    # 显示每个工具的描述（不包含工具名）
                    for tool in tools:
                        tool_desc = tool['desc']
                        # 确保描述强调位置参数
                        if "CORRECT:" not in tool_desc and "WRONG:" not in tool_desc:
                            # 如果描述中没有使用示例，添加一个通用的使用说明
                            tool_desc += "\n\nIMPORTANT: Call with positional arguments only, do NOT use parameter names."
                        desc += f"{tool_desc}\n\n"

                # 添加使用说明 - 强调位置参数，不要用 key=value 格式
                desc += f"\n【Tool Usage】\n"
                desc += f"IMPORTANT: Call tools with POSITIONAL arguments only, NOT named parameters.\n\n"
                desc += f"CORRECT format: {self.command_start} tool_name {self.command_separator} value1 {self.command_separator} value2\n"
                desc += f"WRONG format: {self.command_start} tool_name {self.command_separator} param1=value1 {self.command_separator} param2=value2\n\n"
                desc += f"Example: {self.command_start} ls {self.command_separator} /home/user/documents\n"
                desc += f"NOT: {self.command_start} ls {self.command_separator} directory=/home/user/documents\n\n"

                desc += "【Important Notes】\n"
                desc += "1. Pass ONLY values, do NOT include parameter names\n"
                desc += "2. Pass parameters in the correct order as shown in tool descriptions\n"
                desc += "3. String values should NOT be quoted (unless they contain spaces)\n"
                desc += "4. Use tools based on their descriptions and parameter requirements\n"

                # 组合:工具描述 + \n\n + 框架级工具描述阅读要求 + 用户 system_prompt + 硬编码 Markdown 规范
                final_prompt = desc + "\n\n" + self._get_tool_description_reading_prompt() + "\n\n" + base_prompt + "\n\n" + self._get_markdown_format_prompt()

                return final_prompt

        # No tools enabled, return 用户 system_prompt + 硬编码 Markdown 规范
        return base_prompt + "\n\n" + self._get_markdown_format_prompt()

    def set_tool_enabled(self, tool_name: str, enabled: bool):
        """设置工具是否启用"""
        if enabled:
            self.enabled_mcp_tools.add(tool_name)
        else:
            self.enabled_mcp_tools.discard(tool_name)
        # Silent operation - no output needed

    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用"""
        return tool_name in self.enabled_mcp_tools

    def get_mcp_tools_info(self) -> List[Dict]:
        """获取所有 MCP 工具的信息(用于设置界面)"""
        tools_info = []
        for tool_name, desc in self.mcp_tools_desc.items():
            tools_info.append({
                'name': tool_name,
                'description': desc,  # 完整描述,不截断
                'enabled': self.is_tool_enabled(tool_name),
                'server': getattr(self.funcs.get(tool_name), '__server_name__', 'Unknown') if tool_name in self.funcs else 'Unknown'
            })
        return tools_info
    
    # === 核心方法 ===
    
    def init_ai_client(self):
        """初始化AI客户端"""
        if not self.api_key:
            # 尝试各种环境变量
            self.api_key = os.environ.get("DEEPSEEK_API_KEY") or \
                          os.environ.get("OPENAI_API_KEY") or \
                          os.environ.get("ANTHROPIC_API_KEY")

            if not self.api_key:
                raise ValueError("No API key provided and no API key found in environment variables")

        # Disable proxy to avoid SSL/TLS issues
        # This fixes the "[SSL: WRONG_VERSION_NUMBER]" error when using HTTP proxies
        import httpx

        # Create a mount that bypasses proxy for all URLs
        no_proxy_mount = httpx.HTTPTransport(verify=True)

        # Create client with custom mount
        http_client = httpx.Client(
            mounts={
                "http://": no_proxy_mount,
                "https://": no_proxy_mount,
            },
            timeout=60.0
        )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            http_client=http_client
        )
        print(f"[Info] API client initialized with model: {self.model} (proxy disabled)")
    
    def set_stop_flag(self, value: bool):
        """设置停止标志"""
        self._stop_flag = value
        if value:
            self.execution_status = {
                "status": "idle",
                "tool_name": None,
                "tool_args": None,
                "start_time": None
            }
            print(f"[Info] Stop flag set to True, execution interrupted")
    
    def get_stop_flag(self):
        """获取当前停止标志值"""
        return self._stop_flag
    
    def exec_func(self, func_name, *args):
        """执行函数，带状态跟踪和停止标志支持"""
        if self.get_stop_flag():
            return "Execution interrupted by user"
        
        if func_name not in self.funcs:
            return f"Error: Function '{func_name}' does not exist"
        
        try:
            # 更新执行状态
            self.execution_status = {
                "status": "executing_tool",
                "tool_name": func_name,
                "tool_args": args,
                "start_time": datetime.now().isoformat()
            }
            
            print(f"[Debug] Executing function: {func_name} with args: {args}")
            
            # 检查停止标志
            if self.get_stop_flag():
                self.execution_status = {
                    "status": "stopped",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                return "Execution interrupted by user before execution"
            
            # 处理MCP函数
            if func_name.startswith('mcp_'):
                kwargs = {}
                for arg in args:
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        kwargs[key.strip()] = value.strip()
                    elif arg.strip():
                        kwargs['value'] = arg.strip()
                
                print(f"[Debug] Calling MCP function with kwargs: {kwargs}")
                
                # 检查停止标志
                if self.get_stop_flag():
                    self.execution_status = {
                        "status": "stopped",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    return "Execution interrupted by user before MCP execution"
                
                res = self.funcs[func_name](**kwargs)
            else:
                print(f"[Debug] Calling regular function with args: {args}")
                
                # 检查停止标志
                if self.get_stop_flag():
                    self.execution_status = {
                        "status": "stopped",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    return "Execution interrupted by user before function execution"
                
                # 尝试执行函数，如果参数错误，提供更多信息
                try:
                    res = self.funcs[func_name](*args)
                except TypeError as e:
                    # 获取函数签名
                    import inspect
                    func = self.funcs[func_name]
                    sig = inspect.signature(func)
                    expected_args = list(sig.parameters.keys())
                    
                    error_msg = f"Parameter error: {e}\nExpected parameters: {expected_args}"
                    print(f"[Error] {error_msg}")
                    return f"Execution failed: {error_msg}"
            
            print(f"[Debug] Function execution result: {res[:100]}..." if len(str(res)) > 100 else f"[Debug] Function execution result: {res}")
            
            # 重置执行状态
            self.execution_status = {
                "status": "idle",
                "tool_name": None,
                "tool_args": None,
                "start_time": None
            }
            
            return f"Execution successful: {res}"
        
        except Exception as e:
            print(f"[Error] Function execution failed: {e}")
            
            # 重置执行状态
            self.execution_status = {
                "status": "idle",
                "tool_name": None,
                "tool_args": None,
                "start_time": None
            }
            
            return f"Execution failed: {e}"
            
    def process_user_input_with_history(self, user_input: str, external_history: List[Dict] = None) -> str:
        """
        Process user input with external history
        Returns AI's complete response with proper command execution handling
        
        Args:
            user_input: The user's input message
            external_history: External conversation history (optional)
        
        Returns:
            str: AI's complete response
        """
        # Use external history if provided, otherwise use internal history
        if external_history:
            current_history = external_history.copy()
        else:
            current_history = self.conv_his.copy()

        # Ensure system prompt is at the beginning
        if not current_history or current_history[0].get("role") != "system":
            # 使用有效的系统提示(包含已启用的 MCP 工具)
            effective_prompt = self.get_effective_system_prompt()
            current_history.insert(0, {"role": "system", "content": effective_prompt})
        
        # Add user input to history
        current_history.append({"role": "user", "content": user_input})
        
        iteration = 0
        full_response = ""
        
        print(f"[AI] Processing with history (length: {len(current_history)}), iteration limit: {self.max_iterations}")
        
        while iteration < self.max_iterations:
            if self.get_stop_flag():
                self.set_stop_flag(False)
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                return "**Execution stopped**\nProcessing was interrupted by user."
            
            try:
                # Prepare API parameters
                api_params = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": current_history,
                    "stream": False  # Non-streaming for internal processing
                }
                
                # Add optional parameters
                optional_params = {
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "stop": self.stop,
                    "presence_penalty": self.presence_penalty,
                    "frequency_penalty": self.frequency_penalty
                }
                
                for param, value in optional_params.items():
                    if value is not None:
                        api_params[param] = value
                
                print(f"[AI] Sending request to API with {len(current_history)} messages (iteration {iteration + 1})")
                
                # Execute API call
                response = self.client.chat.completions.create(**api_params)
                get_reply = response.choices[0].message.content
                full_response += get_reply
                
                print(f"[AI] Received reply: {get_reply[:100]}..." if len(get_reply) > 100 else f"[AI] Received reply: {get_reply}")
                
                # Check if AI wants to execute a command
                if get_reply.startswith(self.command_start):
                    print(f"\n[AI][Iteration {iteration + 1}] Command detected: {get_reply}")
                    
                    # Add AI reply to history
                    current_history.append({"role": "assistant", "content": get_reply})
                    
                    # Parse command - extract ONLY the first command
                    # Sometimes AI outputs multiple commands in one response
                    command_line = get_reply
                    
                    # If there are multiple commands, take only the first one
                    if '\n' in get_reply:
                        lines = get_reply.split('\n')
                        for line in lines:
                            if line.startswith(self.command_start):
                                command_line = line
                                break
                    
                    # Parse the command
                    tokens = command_line.replace(self.command_start, "").strip().split(self.command_separator)
                    tokens = [t.strip() for t in tokens if t.strip()]
                    
                    if len(tokens) < 1:
                        res = "Error: Command format is incorrect. Please use: {command_start} tool_name {command_separator} param1 {command_separator} param2"
                    else:
                        func_name = tokens[0]
                        args = tokens[1:] if len(tokens) > 1 else []
                        
                        print(f"[AI] Executing command: {func_name} with args: {args}")
                        
                        # Execute function
                        res = self.exec_func(func_name, *args)
                    
                    print(f"[AI] Command execution result: {res[:200]}...")
                    
                    # Check if command exists
                    if "does not exist" in res or "Error: Function" in res:
                        # Command doesn't exist - add feedback and let AI try again
                        error_feedback = f"Tool '{func_name}' is not available. Please use only available tools from the list provided in the system prompt."
                        current_history.append({
                            "role": "user",
                            "content": error_feedback
                        })
                        
                        # Add a small delay to prevent rapid retries
                        import time
                        time.sleep(0.5)
                        
                        iteration += 1
                        continue
                    
                    # Add execution result to history with guidance
                    current_history.append({
                        "role": "user",
                        "content": f"Execution result: {res}\n\nBased on this result, please decide the next step. If the task is complete or the command failed, provide a final summary in Chinese of what was accomplished or found.\n\nIMPORTANT: Format your summary with proper line breaks and structure. Use separate lines for different points. Do not cram everything into one paragraph."
                    })
                    
                    iteration += 1
                    
                else:
                    # No command, processing is complete
                    current_history.append({"role": "assistant", "content": get_reply})
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    
                    return full_response
                    
            except Exception as e:
                print(f"[AI] Error processing user input: {e}")
                
                # Reset execution status
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                
                return f"Error occurred during processing: {e}"
        
        # Reached maximum iterations
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }
        
        return f"{full_response}\n\n[Note: Reached maximum execution steps ({self.max_iterations}), task may not be fully completed]"


    def _process_with_history(self, user_input: str, history: List[Dict]) -> str:
        """使用指定历史处理用户输入"""
        if self.get_stop_flag():
            self.set_stop_flag(False)
            return "**Execution stopped**\nProcessing was interrupted by user."
        
        # 设置处理状态
        self.execution_status = {
            "status": "processing",
            "tool_name": None,
            "tool_args": None,
            "start_time": datetime.now().isoformat()
        }
        
        # 添加用户输入到历史
        history.append({"role": "user", "content": user_input})
        
        iteration = 0
        full_response = ""
        
        while iteration < self.max_iterations:
            if self.get_stop_flag():
                print(f"[Info] Stop flag detected, stopping execution at iteration {iteration}")
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                self.set_stop_flag(False)
                return "**Execution stopped**\nProcessing was interrupted by user."
            
            try:
                # 准备API参数
                api_params = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": history,
                    "stream": False  # 非流式用于内部处理
                }
                
                # 添加可选参数
                optional_params = {
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "stop": self.stop,
                    "presence_penalty": self.presence_penalty,
                    "frequency_penalty": self.frequency_penalty
                }
                
                for param, value in optional_params.items():
                    if value is not None:
                        api_params[param] = value
                
                print(f"[Debug] Sending request to API with {len(history)} messages (iteration {iteration + 1})")
                
                # 执行API调用
                response = self.client.chat.completions.create(**api_params)
                get_reply = response.choices[0].message.content
                full_response += get_reply
                
                print(f"[Debug] Received reply: {get_reply[:100]}..." if len(get_reply) > 100 else f"[Debug] Received reply: {get_reply}")
                
                if self.get_stop_flag():
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    self.set_stop_flag(False)
                    return "**Execution stopped**\nProcessing was interrupted by user."
                
                if get_reply.startswith(self.command_start):
                    print(f"\n[Iteration {iteration + 1}][AI requested execution] {get_reply}")
                    
                    # 添加AI回复到历史
                    history.append({"role": "assistant", "content": get_reply})
                    
                    # 解析命令
                    tokens = get_reply.replace(self.command_start, "").strip().split(self.command_separator)
                    tokens = [t.strip() for t in tokens]
                    
                    if len(tokens) < 1:
                        res = "Error! Your command format is incorrect"
                    else:
                        func_name = tokens[0]
                        args = tokens[1:] if len(tokens) > 1 else []
                        
                        if self.get_stop_flag():
                            self.execution_status = {
                                "status": "idle",
                                "tool_name": None,
                                "tool_args": None,
                                "start_time": None
                            }
                            self.set_stop_flag(False)
                            return "**Execution stopped**\nProcessing was interrupted by user."
                        
                        # 执行函数
                        res = self.exec_func(func_name, *args)
                    
                    print(f"[Info] AI execution result: {res}")
                    
                    if self.get_stop_flag():
                        self.execution_status = {
                            "status": "idle",
                            "tool_name": None,
                            "tool_args": None,
                            "start_time": None
                        }
                        self.set_stop_flag(False)
                        return "**Execution stopped**\nProcessing was interrupted by user."
                    
                    # 添加执行结果到历史
                    history.append({
                        "role": "user", 
                        "content": f"Execution result: {res}\nPlease decide the next operation based on this result. If the task is complete, please summarize and tell me the result."
                    })
                    
                    iteration += 1
                    
                else:
                    # 没有命令，完成处理
                    history.append({"role": "assistant", "content": get_reply})
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    
                    return full_response
                    
            except Exception as e:
                print(f"[Error] Error processing user input: {e}")
                
                if self.get_stop_flag():
                    self.set_stop_flag(False)
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    return "**Execution stopped**\nProcessing was interrupted by user."
                
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                
                return f"Error occurred during processing: {e}"
        
        # 达到最大迭代次数
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }
        
        return f"{full_response}\n\n[Note: Reached maximum execution steps ({self.max_iterations}), task may not be fully completed]"
    
    # === 流式处理 ===
    def process_user_input_stream(self, user_input: str, conversation_history: List[Dict], callback=None):
        """流式处理用户输入 - 修复版本，支持命令执行"""
        print(f"[AI] Starting stream processing for: {user_input[:50]}...")
        
        if self.get_stop_flag():
            self.set_stop_flag(False)
            if callback:
                callback("**Execution stopped**\nProcessing was interrupted by user.")
            else:
                yield "**Execution stopped**\nProcessing was interrupted by user."
            return
        
        # 设置处理状态
        self.execution_status = {
            "status": "processing",
            "tool_name": None,
            "tool_args": None,
            "start_time": datetime.now().isoformat()
        }
        
        # 创建历史副本
        history = conversation_history.copy()

        # 确保系统提示
        if not history or history[0].get("role") != "system":
            # 使用有效的系统提示(包含已启用的 MCP 工具)
            effective_prompt = self.get_effective_system_prompt()
            history.insert(0, {"role": "system", "content": effective_prompt})

        # 注意：用户消息已经在 MessageProcessor 中添加，这里不需要再添加
        # 如果 history 中最后一条已经是用户消息，说明已经被添加过了
        if history and history[-1].get("role") == "user" and history[-1].get("content") == user_input:
            # 用户消息已存在，不需要重复添加
            pass
        else:
            # 用户消息不存在，添加用户输入
            history.append({"role": "user", "content": user_input})

        # 打印简洁的prompt信息（不显示完整内容）
        print("\n" + "="*80)
        print("[AI] SENDING REQUEST TO API:")
        print("="*80)
        print(f"Messages: {len(history)} total")
        print(f"Model: {self.model}")
        print(f"Temperature: {self.temperature}")
        print(f"System prompt length: {len(history[0]['content']) if history and history[0]['role'] == 'system' else 'N/A'}")
        print(f"User messages: {sum(1 for msg in history if msg['role'] == 'user')}")
        print(f"Assistant messages: {sum(1 for msg in history if msg['role'] == 'assistant')}")
        print("="*80 + "\n")

        iteration = 0
        full_response = ""
        summary_requested = False  # Flag to track if we've already requested a summary

        while iteration < self.max_iterations:
            if self.get_stop_flag():
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                self.set_stop_flag(False)
                if callback:
                    callback("**Execution stopped**\nProcessing was interrupted by user.")
                else:
                    yield "**Execution stopped**\nProcessing was interrupted by user."
                return
            
            try:
                # 准备API参数
                api_params = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": history,
                    "stream": True,  # 关键：启用流式
                    "max_tokens": self.max_tokens or 2048
                }
                
                print(f"[AI] Sending stream request with {len(history)} messages (iteration {iteration + 1})")
                
                # 调用流式API
                response = self.client.chat.completions.create(**api_params)
                
                # 处理流式响应
                current_response = ""
                for chunk in response:
                    if self.get_stop_flag():
                        break
                    
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        current_response += content
                        full_response += content
                        
                        # 发送内容
                        if callback:
                            callback(content)
                        else:
                            yield content
                
                print(f"[AI] Stream iteration {iteration + 1} complete: {current_response[:100]}...")
                
                # 检查是否AI想要执行命令
                if current_response.startswith(self.command_start):
                    print(f"[AI] Command detected in response: {current_response}")

                    # 发送命令本身到UI（通过callback）
                    if callback:
                        command_message = current_response.strip()
                        print(f"[AI] >>>>> SENDING COMMAND VIA CALLBACK: {command_message}")
                        callback(command_message)

                    # 添加AI回复到历史
                    history.append({"role": "assistant", "content": current_response})

                    # 解析命令
                    tokens = current_response.replace(self.command_start, "").strip().split(self.command_separator)
                    tokens = [t.strip() for t in tokens]
                    
                    if len(tokens) < 1:
                        res = "Error! Your command format is incorrect"
                    else:
                        func_name = tokens[0]
                        args = tokens[1:] if len(tokens) > 1 else []
                        
                        # 执行函数
                        res = self.exec_func(func_name, *args)

                    print(f"[AI] Command execution result: {res}")

                    # 发送命令执行结果到UI（通过callback）
                    if callback:
                        result_message = f"{res}"
                        print(f"[AI] >>>>> SENDING COMMAND RESULT VIA CALLBACK: {result_message[:100]}...")
                        callback(result_message)

                    # 添加执行结果到历史（使用自定义提示词）
                    history.append({
                        "role": "user",
                        "content": self.command_execution_prompt.format(result=res)
                    })

                    iteration += 1

                    # 如果执行失败，显示错误信息并让 AI 重新尝试
                    # 移除 iteration < 2 的限制，允许持续重试
                    if ("Execution failed" in res or "Error" in res or "error:" in res.lower()):
                        print("[AI] Command execution failed, showing error to user")
                        # Remove the failed command and execution prompt from history
                        if len(history) >= 2:
                            history.pop()  # Remove execution prompt
                            history.pop()  # Remove command response
                            print(f"[AI] Removed failed command, history size now: {len(history)}")

                        # 显示错误信息给用户
                        error_prompt = f"**错误**: {res}\n\n" + self.command_retry_prompt.format(error=res)
                        history.append({
                            "role": "user",
                            "content": error_prompt
                        })
                        continue

                    # 如果执行成功，让AI决定是否需要继续
                    if "Execution successful" in res:
                        # 继续下一个迭代，但AI应该主动停止
                        print("[AI] Command executed successfully, AI will decide next step")
                        # 给AI一次机会决定是否继续，但限制总迭代次数
                        if iteration >= self.max_iterations:  # 使用配置的迭代次数
                            print(f"[AI] Reached safety limit ({self.max_iterations}), requesting final summary")
                            history.append({
                                "role": "user",
                                "content": self.final_summary_prompt
                            })
                            summary_requested = True  # Mark that we've requested summary
                            continue
                        else:
                            continue
                    else:
                        # 不是明确成功，直接请求总结（不要再继续了）
                        print("[AI] Command execution did not succeed, requesting summary")
                        history.append({
                            "role": "user",
                            "content": self.final_summary_prompt
                        })
                        summary_requested = True
                        iteration += 1
                        continue
                        
                else:
                    # 没有命令执行，完成处理
                    history.append({"role": "assistant", "content": current_response})

                    # 检查是否需要总结（只在第一次请求）
                    if iteration > 0 and not summary_requested:
                        # 如果已经执行过命令，检查AI的响应是否已经是完整的总结
                        # 判断标准：响应长度足够（>100字符）且包含常见的总结性词汇
                        is_complete_answer = (
                            len(current_response) > 100 and
                            any(keyword in current_response for keyword in [
                                '您的', '包含', '总结', '综上', '因此', '文件', '文件夹',
                                'your', 'contains', 'summary', 'conclusion', 'files', 'folders'
                            ])
                        )

                        if is_complete_answer:
                            # AI已经给出了完整的答案，不需要再请求总结
                            print("[AI] AI provided complete answer, no need to request summary")
                            print(f"[AI] Answer length: {len(current_response)}, preview: {current_response[:100]}...")
                            break
                        else:
                            # AI的响应不够完整，请求总结
                            print("[AI] Requesting final summary...")
                            history.append({
                                "role": "user",
                                "content": self.final_summary_prompt
                            })

                            summary_requested = True  # Mark that we've requested summary
                            iteration += 1
                            continue  # 最后一次迭代获取总结
                    else:
                        # 已经请求过总结，或没有执行过命令，直接结束
                        if summary_requested:
                            print("[AI] Summary provided, completing task")
                        break
                        
            except Exception as e:
                import traceback
                print(f"[AI] Stream API error: {e}")
                print(f"[AI] Error type: {type(e).__name__}")
                print(f"[AI] Traceback:\n{traceback.format_exc()}")

                # Provide more helpful error message
                error_msg = f"❌ **Connection Error**\n\n"
                error_msg += f"**Error Details:**\n"
                error_msg += f"- Type: {type(e).__name__}\n"
                error_msg += f"- Message: {str(e)}\n\n"

                # Check for common issues
                error_str = str(e).lower()
                if 'connection' in error_str or 'network' in error_str:
                    error_msg += f"**Possible Causes:**\n"
                    error_msg += f"- Network connection issue\n"
                    error_msg += f"- API server is down or unreachable\n"
                    error_msg += f"- Firewall or proxy blocking the connection\n"
                    error_msg += f"- Incorrect API base URL\n\n"
                    error_msg += f"**Suggestions:**\n"
                    error_msg += f"- Check your internet connection\n"
                    error_msg += f"- Verify API base URL: `{self.api_base}`\n"
                    error_msg += f"- Try again later\n"
                elif 'timeout' in error_str:
                    error_msg += f"**Request timed out.**\n\n"
                    error_msg += f"**Suggestions:**\n"
                    error_msg += f"- Check your network speed\n"
                    error_msg += f"- The API server might be overloaded\n"
                    error_msg += f"- Try again later\n"
                elif 'authentication' in error_str or '401' in error_str:
                    error_msg += f"**Authentication failed.**\n\n"
                    error_msg += f"**Suggestions:**\n"
                    error_msg += f"- Check your API key\n"
                    error_msg += f"- Verify your API key is valid\n"
                elif 'rate' in error_str or '429' in error_str:
                    error_msg += f"**Rate limit exceeded.**\n\n"
                    error_msg += f"**Suggestions:**\n"
                    error_msg += f"- Wait a moment and try again\n"
                    error_msg += f"- Check your API usage limits\n"

                if callback:
                    callback(error_msg)
                else:
                    yield error_msg
                break
        
        # 重置状态
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }

        # CRITICAL: 将处理后的历史保存回 self.conv_his
        # 这样下次对话时才能记住上下文
        self.conv_his = history.copy()
        print(f"[AI] Updated conv_his with {len(self.conv_his)} messages")

        # CRITICAL: 确保生成器正确结束
        # 发送结束标记并明确完成生成器
        print("[AI] Stream processing completing, sending final empty chunk")

        # 生成器结束前的日志（在yield之前执行，避免线程问题）
        print("[AI] Generator completing, sending final empty chunk")

        # 最后一次yield，确保生成器结束
        yield ""


    def _process_user_inp_stream_internal(self, user_input: str, history: List[Dict], callback=None):
        """内部流式处理方法 - 保持原始逻辑"""
        if not user_input:
            yield ""
            return

        max_iter = self.max_iterations
        
        # 检查停止标志
        if self.get_stop_flag():
            self.set_stop_flag(False)
            self.execution_status = {
                "status": "idle",
                "tool_name": None,
                "tool_args": None,
                "start_time": None
            }
            yield "**Execution stopped**\nProcessing was interrupted by user."
            return
        
        # 设置执行状态
        self.execution_status = {
            "status": "processing",
            "tool_name": None,
            "tool_args": None,
            "start_time": datetime.now().isoformat()
        }
        
        iteration = 0
        while iteration < max_iter:
            # 检查停止标志
            if self.get_stop_flag():
                print(f"[Info] Stop flag detected, stopping execution at iteration {iteration}")
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                self.set_stop_flag(False)
                yield "**Execution stopped**\nProcessing was interrupted by user."
                return
            
            try:
                # 准备API参数
                api_params = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": history,
                    "stream": True
                }
                
                # 添加可选参数
                optional_params = {
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "stop": self.stop,
                    "presence_penalty": self.presence_penalty,
                    "frequency_penalty": self.frequency_penalty
                }
                
                for param, value in optional_params.items():
                    if value is not None:
                        api_params[param] = value
                
                print(f"[Debug] Sending stream request to API with {len(history)} messages (iteration {iteration + 1})")
                
                # 执行流式API调用
                response = self.client.chat.completions.create(**api_params)
                
                # 收集响应
                collected_chunks = []
                collected_messages = []
                
                # 处理流式响应
                for chunk in response:
                    # 检查停止标志
                    if self.get_stop_flag():
                        self.execution_status = {
                            "status": "idle",
                            "tool_name": None,
                            "tool_args": None,
                            "start_time": None
                        }
                        self.set_stop_flag(False)
                        yield "**Execution stopped**\nProcessing was interrupted by user."
                        return
                    
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        collected_chunks.append(chunk)
                        collected_messages.append(content)
                        
                        # 发送实时内容
                        if callback:
                            callback(content)
                        else:
                            yield content
                
                # 合并收集的消息
                full_reply = ''.join(collected_messages)
                print(f"[Debug] Full reply received (iteration {iteration + 1}): {full_reply[:100]}..." if len(full_reply) > 100 else f"[Debug] Full reply received: {full_reply}")
                
                # 检查是否AI想要执行命令
                if self.command_start in full_reply:
                    print(f"\n[Iteration {iteration + 1}][AI requested execution] {full_reply}")
                    
                    # 提取命令部分
                    if full_reply.startswith(self.command_start):
                        command_line = full_reply
                    else:
                        # 从回复中提取命令
                        start_idx = full_reply.find(self.command_start)
                        command_line = full_reply[start_idx:].split('\n')[0].strip()
                    
                    # 解析命令
                    command_text = command_line.replace(self.command_start, "").strip()
                    tokens = command_text.split(self.command_separator)
                    tokens = [t.strip() for t in tokens]
                    
                    if len(tokens) < 1:
                        res = "Error! Your command format is incorrect"
                    else:
                        func_name = tokens[0]
                        args = tokens[1:] if len(tokens) > 1 else []
                        
                        # 检查停止标志
                        if self.get_stop_flag():
                            self.execution_status = {
                                "status": "idle",
                                "tool_name": None,
                                "tool_args": None,
                                "start_time": None
                            }
                            self.set_stop_flag(False)
                            yield "**Execution stopped**\nProcessing was interrupted by user."
                            return
                        
                        # 执行函数
                        res = self.exec_func(func_name, *args)
                    
                    print(f"[Info] AI execution result: {res}")
                    
                    # 检查停止标志
                    if self.get_stop_flag():
                        self.execution_status = {
                            "status": "idle",
                            "tool_name": None,
                            "tool_args": None,
                            "start_time": None
                        }
                        self.set_stop_flag(False)
                        yield "**Execution stopped**\nProcessing was interrupted by user."
                        return
                    
                    # 添加回复和结果到对话历史
                    history.append({"role": "assistant", "content": full_reply})
                    history.append({
                        "role": "user", 
                        "content": f"Execution result: {res}\nPlease decide the next operation based on this result. If the task is complete, please summarize and tell me the result."
                    })
                    
                    # 流式命令执行结果
                    result_message = f"\n\n**Command Execution Result**\n```\n{res}\n```"
                    
                    # 发送结果
                    if callback:
                        callback(result_message)
                    else:
                        yield result_message
                    
                    iteration += 1
                    
                    # 如果执行成功，继续下一个迭代
                    if "Execution successful" in res:
                        print(f"[Info] Command executed successfully, continuing to next iteration")
                        continue
                    else:
                        # 如果执行失败，AI应该重新尝试
                        print(f"[Info] Command execution failed, AI should retry")
                        continue
                    
                else:
                    # 没有命令执行，完成处理
                    history.append({"role": "assistant", "content": full_reply})
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    return
                    
            except Exception as e:
                print(f"[Error] Error processing user input: {e}")
                
                # 检查是否是stop导致的错误
                if self.get_stop_flag():
                    self.set_stop_flag(False)
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    yield "**Execution stopped**\nProcessing was interrupted by user."
                    return
                
                # 重置执行状态
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                
                yield f"Error occurred during processing: {e}"
                return
        
        # 达到最大迭代次数
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }
        
        yield f"Reached maximum execution steps ({max_iter}), task may not be fully completed"
    
    # === 兼容性方法 ===
    
    def process_user_inp(self, user_inp, max_iter=None):
        """兼容性方法 - 处理用户输入"""
        if self.stream:
            # 流式处理 - 返回生成器
            return self._process_user_inp_stream_internal(user_inp, self.conv_his)
        else:
            # 非流式处理 - 返回元组
            return self._process_user_inp_non_stream(user_inp, max_iter)
    
    def _process_user_inp_non_stream(self, user_inp, max_iter=None):
        """非流式处理用户输入 - 保持原始逻辑"""
        if not user_inp:
            return "", False

        max_iter = max_iter or self.max_iterations
        
        # 检查停止标志
        if self.get_stop_flag():
            self.set_stop_flag(False)
            self.execution_status = {
                "status": "idle",
                "tool_name": None,
                "tool_args": None,
                "start_time": None
            }
            return "**Execution stopped**\nProcessing was interrupted by user.", True
        
        self.execution_status = {
            "status": "processing",
            "tool_name": None,
            "tool_args": None,
            "start_time": datetime.now().isoformat()
        }
        
        self.conv_his.append({"role": "user", "content": user_inp})
        
        for step in range(max_iter):
            if self.get_stop_flag():
                print(f"[Info] Stop flag detected, stopping execution at step {step+1}")
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                self.set_stop_flag(False)
                return "**Execution stopped**\nProcessing was interrupted by user.", True
            
            try:
                api_params = {
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": self.conv_his,
                    "stream": False  # 非流式
                }
                
                optional_params = {
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "stop": self.stop,
                    "presence_penalty": self.presence_penalty,
                    "frequency_penalty": self.frequency_penalty
                }
                
                for param, value in optional_params.items():
                    if value is not None:
                        api_params[param] = value
                
                print(f"[Debug] Sending non-stream request to API with {len(self.conv_his)} messages")
                
                response = self.client.chat.completions.create(**api_params)
                get_reply = response.choices[0].message.content
                print(f"[Debug] Received reply: {get_reply[:100]}..." if len(get_reply) > 100 else f"[Debug] Received reply: {get_reply}")
                
                if self.get_stop_flag():
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    self.set_stop_flag(False)
                    return "**Execution stopped**\nProcessing was interrupted by user.", True
                
                if get_reply.startswith(self.command_start):
                    print(f"\n[Step {step + 1}][AI requested execution] {get_reply}")
                    
                    tokens = get_reply.replace(self.command_start, "").strip().split(self.command_separator)
                    tokens = [t.strip() for t in tokens]
                    
                    if len(tokens) < 1:
                        res = "Error! Your command format is incorrect"
                    else:
                        func_name = tokens[0]
                        args = tokens[1:] if len(tokens) > 1 else []
                        
                        if self.get_stop_flag():
                            self.execution_status = {
                                "status": "idle",
                                "tool_name": None,
                                "tool_args": None,
                                "start_time": None
                            }
                            self.set_stop_flag(False)
                            return "**Execution stopped**\nProcessing was interrupted by user.", True
                        
                        res = self.exec_func(func_name, *args)
                    
                    print(f"[Info] AI execution result: {res}")
                    
                    if self.get_stop_flag():
                        self.execution_status = {
                            "status": "idle",
                            "tool_name": None,
                            "tool_args": None,
                            "start_time": None
                        }
                        self.set_stop_flag(False)
                        return "**Execution stopped**\nProcessing was interrupted by user.", True
                    
                    self.conv_his.append({"role": "assistant", "content": get_reply})
                    self.conv_his.append({
                        "role": "user", 
                        "content": f"Execution result: {res}\nPlease decide the next operation based on this result. If the task is complete, please summarize and tell me the result."
                    })
                    
                else:
                    self.conv_his.append({"role": "assistant", "content": get_reply})
                    
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    
                    return get_reply, True
                    
            except Exception as e:
                print(f"[Error] Error processing user input: {e}")
                
                if self.get_stop_flag():
                    self.set_stop_flag(False)
                    self.execution_status = {
                        "status": "idle",
                        "tool_name": None,
                        "tool_args": None,
                        "start_time": None
                    }
                    return "**Execution stopped**\nProcessing was interrupted by user.", True
                
                self.execution_status = {
                    "status": "idle",
                    "tool_name": None,
                    "tool_args": None,
                    "start_time": None
                }
                
                return f"Error occurred during processing: {e}", True
        
        self.execution_status = {
            "status": "idle",
            "tool_name": None,
            "tool_args": None,
            "start_time": None
        }
        
        return f"Reached maximum execution steps ({max_iter}), task may not be fully completed", False
    
    # === 历史管理 ===
    
    def reset_conversation(self):
        """重置对话历史"""
        # 使用有效的系统提示(包含已启用的 MCP 工具)
        effective_prompt = self.get_effective_system_prompt()
        self.conv_his = [{"role": "system", "content": effective_prompt}]
        print("[AI] Conversation history reset")
    
    def load_conversation_history(self, history_messages: List[Dict]):
        """加载对话历史到AI上下文"""
        print(f"[AI] Loading {len(history_messages)} conversation history messages")
        
        # 重置对话
        self.reset_conversation()
        
        # 添加历史消息到对话
        for msg in history_messages:
            role = "user" if msg.get("is_sender", False) else "assistant"
            content = msg.get("text", "")
            
            # 跳过空消息
            if content and content.strip():
                self.conv_his.append({"role": role, "content": content})
        
        print(f"[AI] Conversation history loaded. Total messages: {len(self.conv_his)}")
    
    def get_current_history(self) -> List[Dict]:
        """获取当前对话历史"""
        return self.conv_his.copy()
    
    def set_current_history(self, history: List[Dict]):
        """设置当前对话历史"""
        self.conv_his = history.copy()
        print(f"[AI] History set with {len(self.conv_his)} messages")
    
    # === 配置方法 ===
    
    def update_system_prompt(self, new_prompt: str):
        """更新系统提示（只更新用户的原始提示词）"""
        self.user_system_prompt = new_prompt
        # 生成完整的有效提示词（包含工具描述和 Markdown 规范）
        effective_prompt = self.get_effective_system_prompt()
        # 更新对话历史中的系统提示
        for i, msg in enumerate(self.conv_his):
            if msg.get("role") == "system":
                self.conv_his[i]["content"] = effective_prompt
                break
        else:
            self.conv_his.insert(0, {"role": "system", "content": effective_prompt})
    
    def update_config(self, config_dict: Dict):
        """从字典更新配置，不创建新实例"""
        print(f"[AI] Updating AI configuration for existing instance")

        # 更新API配置
        if 'api_key' in config_dict and config_dict['api_key']:
            self.api_key = config_dict['api_key']
            # 保存到会话配置（.confignore）
            if self.conversation_config:
                self.conversation_config.set_api_key(self.api_key)

        if 'api_base' in config_dict and config_dict['api_base']:
            self.api_base = config_dict['api_base']
            # 不再保存到 ConversationConfig（只存 API key）

        if 'model' in config_dict and config_dict['model']:
            self.model = config_dict['model']
            # 不再保存到 ConversationConfig

        # 重新初始化客户端
        if any(key in config_dict for key in ['api_key', 'api_base', 'model']):
            self.init_ai_client()

        # 更新模型参数
        if 'temperature' in config_dict:
            self.temperature = config_dict['temperature']

        if 'max_tokens' in config_dict:
            self.max_tokens = config_dict['max_tokens']

        if 'top_p' in config_dict:
            self.top_p = config_dict['top_p']

        if 'stop' in config_dict:
            self.stop = config_dict['stop']
        
        if 'stream' in config_dict:
            self.stream = config_dict['stream']
            print(f"[AI] Stream mode updated to: {self.stream}")
        
        if 'presence_penalty' in config_dict:
            self.presence_penalty = config_dict['presence_penalty']
        
        if 'frequency_penalty' in config_dict:
            self.frequency_penalty = config_dict['frequency_penalty']
        
        # 更新命令配置
        if 'command_start' in config_dict:
            self.command_start = config_dict['command_start']
        
        if 'command_separator' in config_dict:
            self.command_separator = config_dict['command_separator']
        
        if 'max_iterations' in config_dict:
            self.max_iterations = config_dict['max_iterations']
        
        # 更新系统提示（只更新用户的原始提示词，不包含硬编码的 Markdown 规范）
        if 'system_prompt' in config_dict and config_dict['system_prompt']:
            self.user_system_prompt = config_dict['system_prompt']
            self.update_system_prompt(self.user_system_prompt)
        
        # 更新MCP路径并重新加载工具
        if 'mcp_paths' in config_dict:
            new_paths = config_dict['mcp_paths']
            print(f"[AI] MCP paths changed, reloading tools")
            print(f"[Debug] New paths: {new_paths}")
            print(f"[Debug] Old paths: {self.mcp_paths}")

            if set(new_paths) != set(self.mcp_paths):
                self.mcp_paths = new_paths
                # 实际加载 MCP 工具（不再跳过）
                print("[AI] Calling _load_mcp_from_paths...")
                self._load_mcp_from_paths()
                print(f"[Debug] Loaded {len(self.mcp_tools_desc)} tool descriptions")
                # 保留现有的 enabled_mcp_tools 设置，或者启用所有新工具
                if self.enabled_mcp_tools:
                    self.enabled_mcp_tools = self.enabled_mcp_tools.intersection(set(self.mcp_tools_desc.keys()))
                elif self.mcp_tools_desc:
                    # 如果没有启用任何工具，默认启用所有
                    self.enabled_mcp_tools = set(self.mcp_tools_desc.keys())
                print(f"[Info] MCP tools reloaded, {len(self.enabled_mcp_tools)} tools enabled")
            else:
                print("[AI] MCP paths unchanged, skipping reload")

        # 更新自定义提示词
        if 'command_execution_prompt' in config_dict and config_dict['command_execution_prompt']:
            self.command_execution_prompt = config_dict['command_execution_prompt']

        if 'command_retry_prompt' in config_dict and config_dict['command_retry_prompt']:
            self.command_retry_prompt = config_dict['command_retry_prompt']

        if 'final_summary_prompt' in config_dict and config_dict['final_summary_prompt']:
            self.final_summary_prompt = config_dict['final_summary_prompt']

        # 更新已启用的 MCP 工具
        if 'enabled_mcp_tools' in config_dict:
            enabled_tools = config_dict['enabled_mcp_tools']
            self.enabled_mcp_tools = set(enabled_tools)
            print(f"[AI] Enabled {len(self.enabled_mcp_tools)} MCP tools")

        print(f"[AI] Configuration updated successfully, stream={self.stream}")
    
    def get_config(self) -> Dict:
        """获取当前配置字典（返回用户的原始 system_prompt，不包含硬编码的 Markdown 规范）"""
        return {
            # API配置
            "api_base": self.api_base,
            "model": self.model,

            # 提示配置（只返回用户的原始提示，不包含 Markdown 规范）
            "system_prompt": self.user_system_prompt,

            # 模型参数
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": self.stop,
            "stream": self.stream,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,

            # 命令执行配置
            "command_start": self.command_start,
            "command_separator": self.command_separator,
            "max_iterations": self.max_iterations,

            # 工具配置
            "mcp_paths": self._convert_paths_to_relative(self.mcp_paths.copy()),
            "available_tools": list(self.funcs.keys()),
            "enabled_mcp_tools": list(self.enabled_mcp_tools)  # 保存已启用的工具
        }

    def _convert_paths_to_relative(self, paths: List[str]) -> List[str]:
        """将路径转换为相对路径格式(使用正斜杠)"""
        relative_paths = []
        for path in paths:
            # 转换为相对路径
            if os.path.isabs(path):
                try:
                    rel_path = os.path.relpath(path, os.getcwd())
                except ValueError:
                    # 如果无法计算相对路径,使用原始路径
                    rel_path = path
            else:
                rel_path = path

            # 统一使用正斜杠
            rel_path = rel_path.replace('\\', '/')

            # 如果不是以 ./ 开头的相对路径,添加 ./
            if not rel_path.startswith('./') and not rel_path.startswith('../'):
                rel_path = './' + rel_path

            relative_paths.append(rel_path)

        return relative_paths
    
    def get_execution_status(self) -> Dict:
        """获取当前执行状态用于状态栏显示"""
        return self.execution_status.copy()
    
    def get_available_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        tools = []
        for func_name, func in self.funcs.items():
            doc = func.__doc__ or "No description"
            tools.append({"name": func_name, "description": doc})
        return tools
    
    def print_tools_list(self):
        """打印可用工具列表"""
        print("\nAvailable tools:")
        tools = self.get_available_tools()
        for i, tool in enumerate(tools, 1):
            # 打印完整描述,不截断
            desc = tool['description']
            print(f"{i:2}. {tool['name']}: {desc}")

    def cleanup_mcp_servers(self):
        """清理所有 MCP server 进程"""
        if hasattr(self, 'mcp_managers') and self.mcp_managers:
            print(f"[Info] Cleaning up {len(self.mcp_managers)} MCP servers...")
            for server_name, manager in self.mcp_managers.items():
                try:
                    manager.stop()
                    print(f"[Info] Stopped MCP server: {server_name}")
                except Exception as e:
                    print(f"[Warning] Failed to stop server {server_name}: {e}")
            self.mcp_managers.clear()
            print("[Info] MCP servers cleanup complete")

    def __del__(self):
        """析构函数 - 确保 MCP servers 被正确关闭"""
        try:
            self.cleanup_mcp_servers()
        except:
            pass


# 配置文件加载函数
def load_config_from_file(config_path: str) -> Optional[Dict]:
    """从文件加载配置(JSON或YAML)"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                config = json.load(f)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                try:
                    import yaml
                    config = yaml.safe_load(f)
                except ImportError:
                    print("[Warning] PyYAML not installed. Install with: pip install pyyaml")
                    return None
            else:
                raise ValueError("Unsupported config file format, supports JSON or YAML")
        return config
    except Exception as e:
        print(f"[Error] Failed to load config file: {e}")
        return None


def create_ai_from_config(config_path: str) -> Optional[AI]:
    """从配置文件创建AI实例"""
    config = load_config_from_file(config_path)
    if not config:
        return None
    
    # 提取配置参数
    mcp_paths = config.get("mcp_paths", [])
    api_key = config.get("api_key")
    
    # 创建AI实例
    ai = AI(
        mcp_paths=mcp_paths,
        api_key=api_key,
        api_base=config.get("api_base"),
        model=config.get("model"),
        system_prompt=config.get("system_prompt"),
        temperature=config.get("temperature", 1.0),
        max_tokens=config.get("max_tokens"),
        top_p=config.get("top_p", 1.0),
        stop=config.get("stop"),
        stream=config.get("stream", True),
        presence_penalty=config.get("presence_penalty", 0.0),
        frequency_penalty=config.get("frequency_penalty", 0.0),
        command_start=config.get("command_start", "YLDEXECUTE:"),
        command_separator=config.get("command_separator", "￥|"),
        max_iterations=config.get("max_iterations", 15)
    )
    
    return ai


def save_config_to_file(ai_instance: AI, config_path: str) -> bool:
    """将AI实例配置保存到文件"""
    config = ai_instance.get_config()
    config["api_key"] = ai_instance.api_key  # 警告：保存API密钥需谨慎
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"[Info] Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"[Error] Failed to save configuration: {e}")
        return False


if __name__ == "__main__":
    """主控制台界面"""
    print("Lynexus AI Assistant - Console Interface")
    
    # 简单测试
    ai = AI(stream=True)
    
    print(f"\nAI initialized with {len(ai.funcs)} tools")
    print("Type 'exit' to quit, 'tools' to list tools, 'clear' to clear history")
    
    while True:
        try:
            user_input = input("\n>> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', '退出', '再见']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['clear', '清空']:
                ai.reset_conversation()
                print("Conversation history cleared")
                continue
            
            if user_input.lower() == 'tools':
                ai.print_tools_list()
                continue
            
            if user_input.lower() == 'config':
                config = ai.get_config()
                print("\nCurrent configuration:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
                continue
            
            if ai.stream:
                # 流式模式
                print("\n[AI] ", end="", flush=True)
                for chunk in ai.process_user_inp(user_input):
                    if chunk:
                        print(chunk, end="", flush=True)
                print()
            else:
                # 非流式模式
                response, completed = ai.process_user_inp(user_input)
                if response:
                    print(f"\n[AI] {response}")
            
        except KeyboardInterrupt:
            print("\n[Info] Operation interrupted")
            break
        except Exception as e:
            print(f"\n[Error] Error: {e}")
            continue