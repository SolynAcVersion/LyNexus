import os
import sys
import importlib.util
import re
import inspect
from openai import OpenAI
import json
from mcp_utils import MCPServerManager, load_mcp_conf, exec_mcp_tools


class AI:
    def __init__(self, mcp_paths=None, api_key=None,
                 system_prompt=None, temperature=1.0, api_base=None,
                 model=None, max_tokens=None, top_p=None, stream=None,
                 max_iterations=None, chat_name=None):

        self.mcp_paths = mcp_paths or []
        self.api_key = api_key
        self.system_prompt = system_prompt or self.get_default_system_prompt()
        self.temperature = temperature
        self.api_base = api_base or 'https://api.deepseek.com'
        self.model = model or 'deepseek-chat'
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream if stream is not None else True
        self.max_iterations = max_iterations or 15
        self.chat_name = chat_name or 'default'

        self.funcs = {}
        self.tool_registry = {}
        self.conv_his = []
        self.stop_flag = False

        self.client = None

        self.load_mcp_tools()
        self.init_ai_client()
        self.reset_conversation()

    def get_default_system_prompt(self):
        return """
You are an AI assistant using the ReAct (Reasoning + Acting) paradigm.

【CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY】
1. NEVER make up tool names. ONLY use tools from the list below.
2. NEVER guess information. ALWAYS call tools to get real data.
3. EVERY response must start with "Thought:" followed by reasoning
4. Then output "Action:" with a tool name from the available list
5. Wait for "Observation:" before continuing
6. Only use "final_answer" when you have actual results from tools

【Response Format - EVERY TIME】
Thought: [what you're thinking and why]
Action: [exact tool name from the list below]

【Tool Usage Process】
Step 1: Output just the tool name (e.g., "Action: ls") to get its parameters
Step 2: After seeing the parameters, execute with values (e.g., "Action: ls(directory="/home/user")")

【Example】
User: List files in my home directory

Thought: I need to list directory contents. The available tool is "ls".
Action: ls

Observation: [Tool: ls]
Description: List directory contents
Parameters: directory (string, default=".")

Thought: I'll execute ls to list the home directory.
Action: ls(directory="/home/user")

Observation: file1.txt, file2.py, documents/

Thought: Successfully got the directory listing. I can now answer.
Action: final_answer: Your home directory contains: file1.txt, file2.py, and a documents folder.

【Available Tools - USE ONLY THESE】
{TOOLS_LIST}

【IMPORTANT WARNINGS】
- If you use a tool NOT in this list, you will get an error
- Check the tool list carefully before outputting Action:
- Common file tools: ls, cat, mv, cp, mkdir, rm
- Common OCR tools: ocr_process_pdf, ocr_process_pictures
"""

    def get_effective_system_prompt(self):
        return self.system_prompt

    def load_mcp_mod(self, mcp_path):
        """Load a single MCP module file (supports .json and .py)"""
        try:
            # JSON file: MCP server configuration
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
                            funcs[func_name] = make_tool_func(ser_name, tool_name, tool.get('description', 'no description'))

                class MCPModule:
                    def __init__(self):
                        self.manager = mcp_manager
                return MCPModule(), funcs

            else:
                # Python file: as module
                module_name = os.path.basename(mcp_path).replace('.py', '')
                spec = importlib.util.spec_from_file_location(module_name, mcp_path)
                if spec is None:
                    raise ImportError(f"Failed to load module from {mcp_path}")

                mcp_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mcp_module
                spec.loader.exec_module(mcp_module)
                print(f"Successfully loaded {module_name}")

                funcs = {}
                for attr_name in dir(mcp_module):
                    attr = getattr(mcp_module, attr_name)
                    if callable(attr) and not attr_name.startswith('_'):
                        funcs[attr_name] = attr

                return mcp_module, funcs

        except Exception as e:
            print(f"Loading failed: {e}")
            return None, {}

    def load_mult_mcp_mod(self, mcp_paths):
        """Load mult MCP module files"""
        all_funcs = {}
        all_mods = []

        for path in mcp_paths:
            mod, funcs = self.load_mcp_mod(path)
            if mod:
                all_mods.append(mod)
            if funcs:
                for func_name, func in funcs.items():
                    all_funcs[func_name] = func
        return all_mods, all_funcs

    def build_tool_registry(self):
        """Build two-tier storage: summary (1-line) + detail (full metadata)"""
        self.tool_registry = {}

        for func_name, func in self.funcs.items():
            doc = func.__doc__ or "No description available"
            lines = doc.strip().split('\n')
            summary = lines[0].strip() if lines else "No description"

            detail = {
                "description": doc,
                "parameters": {}
            }

            try:
                if hasattr(func, '__signature__'):
                    sig = inspect.signature(func)
                    for param_name, param in sig.parameters.items():
                        param_info = {
                            "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                            "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                            "required": param.default == inspect.Parameter.empty
                        }
                        detail["parameters"][param_name] = param_info
            except Exception:
                pass

            self.tool_registry[func_name] = {
                "summary": summary,
                "detail": detail
            }

        print(f"Built tool registry for {len(self.tool_registry)} tools")

    def gen_tools_desc(self):
        if not self.tool_registry:
            return ""

        desc = ""
        for func_name, info in self.tool_registry.items():
            desc += f"- {func_name}: {info['summary']}\n"

        return desc

    def get_tool_detail(self, tool_name):
        if tool_name not in self.tool_registry:
            return f"Error: Tool '{tool_name}' not found"

        detail = self.tool_registry[tool_name]["detail"]

        result = f"[Tool: {tool_name}]\n"
        result += f"Description: {detail['description']}\n"

        if detail["parameters"]:
            result += "Parameters:\n"
            for param_name, param_info in detail["parameters"].items():
                result += f"  - {param_name}"
                if param_info.get("type"):
                    result += f" (type: {param_info['type']})"
                if param_info.get("required"):
                    result += " [required]"
                elif param_info.get("default"):
                    result += f" (default: {param_info['default']})"
                result += "\n"
        else:
            result += "Parameters: None\n"

        return result

    def load_mcp_tools(self):
        """Load MCP tools from paths and auto-load default tools"""
        # default tools， hardcoded
        if(self.mcp_paths.count('./tools/ocr.py') == 0):
            self.mcp_paths.append('./tools/ocr.py')
        if(self.mcp_paths.count('./tools/mcp_config.json') == 0):
            self.mcp_paths.append('./tools/mcp_config.json')

        if not self.mcp_paths:
            print("No file paths entered")

        valid_paths = []
        for path in self.mcp_paths:
            if not os.path.exists(path):
                print(f"File does not exist: {path}")
            elif os.path.isdir(path):
                # 如果是目录，扫描所有 .py 和 .json 文件
                print(f"Scanning directory: {path}")
                for file in os.listdir(path):
                    if file.endswith('.py') or file.endswith('.json'):
                        full_path = os.path.join(path, file)
                        valid_paths.append(full_path)
                        print(f"  Found: {file}")
            else:
                valid_paths.append(path)
        print(f"Will load {len(valid_paths)} MCP files")

        _, self.funcs = self.load_mult_mcp_mod(valid_paths)

        if self.funcs:
            self.build_tool_registry()
            tools_desc = self.gen_tools_desc()
            self.system_prompt = self.system_prompt.replace("{TOOLS_LIST}", tools_desc)
            print("System prompt updated with tools description (ReAct mode)")

    def add_mcp_mods(self, valid_paths):
        _, funcs = self.load_mult_mcp_mod(valid_paths)
        self.funcs.update(funcs)

        if self.funcs:
            self.build_tool_registry()
            tools_desc = self.gen_tools_desc()

            if "{TOOLS_LIST}" in self.system_prompt:
                self.system_prompt = self.system_prompt.replace("{TOOLS_LIST}", tools_desc)
            else:
                self.system_prompt = self.system_prompt + "\n\n" + tools_desc

        self.update_system_prompt(self.system_prompt)

    def init_ai_client(self):
        if not self.api_key:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError("API KEY not provided")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        print("Successfully obtained API KEY")

    def reset_conversation(self):
        self.conv_his = [{"role": "system", "content": self.system_prompt}]

    def exec_func(self, func_name, *args, **kwargs):
        if func_name not in self.funcs:
            return f"Error: Function '{func_name}' does not exist"
        try:
            if func_name.startswith('mcp_'):
                if kwargs:
                    res = self.funcs[func_name](**kwargs)
                elif args:
                    kwargs_converted = {}
                    for arg in args:
                        if '=' in arg:
                            key, value = arg.split('=', 1)
                            kwargs_converted[key.strip()] = value.strip()
                        elif arg.strip():
                            kwargs_converted['value'] = arg.strip()
                    res = self.funcs[func_name](**kwargs_converted)
                else:
                    res = self.funcs[func_name]()
            else:
                res = self.funcs[func_name](*args, **kwargs)

            # 直接返回结果，不添加额外文本
            return str(res)
        except Exception as e:
            return f"Execution failed: {e}"

    def parse_action(self, text):
        match = re.search(r'Action:\s*(\w+)', text)
        if not match:
            return None, None

        action = match.group(1)

        if action == "final_answer":
            return "final_answer", text.split("Action: final_answer:", 1)[1].strip()

        # 检查是否有括号（表示意图执行）
        has_parens = re.search(rf'{action}\s*\(', text)

        params = {}
        params_match = re.search(rf'{action}\s*\((.*?)\)', text)
        if params_match:
            params_str = params_match.group(1)
            # 如果括号内有内容，解析参数
            if params_str.strip():
                try:
                    for pair in params_str.split(','):
                        pair = pair.strip()
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            params[key.strip()] = value.strip()
                        elif pair:
                            params['value'] = pair.strip()
                except:
                    pass

        # 返回 (action, params, has_parens)
        # has_parens=True 表示意图执行，False 表示只是查询
        return action, params, has_parens if has_parens else False

    def react_loop(self, user_inp, max_iter=15):
        self.conv_his.append({"role": "user", "content": user_inp})

        for step in range(max_iter):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=self.conv_his,
                    stream=False
                )
                reply = response.choices[0].message.content.strip()

                if "Thought:" in reply:
                    parts = reply.split("Thought:", 1)
                    if len(parts) > 1:
                        thought_part = parts[1].split("Action:", 1)[0].strip()
                        if thought_part:
                            print(f"\n[Thought] {thought_part}")

                self.conv_his.append({"role": "assistant", "content": reply})

                if "Action: final_answer:" in reply:
                    return reply.split("Action: final_answer:", 1)[1].strip()

                action, params, has_parens = self.parse_action(reply)

                if action is None:
                    return reply

                if action in self.tool_registry:
                    if has_parens:  # 有括号，意图执行
                        print(f"[Action] Executing: {action}")
                        res = self.exec_func(action, **params)
                        observation = f"Execution result: {res}"
                    else:  # 无括号，查询工具详情
                        observation = self.get_tool_detail(action)
                else:
                    available_tools = list(self.tool_registry.keys())
                    observation = f"Error: Tool '{action}' not found. Available tools: {', '.join(available_tools[:10])}"
                    if len(available_tools) > 10:
                        observation += f" ... and {len(available_tools) - 10} more"
                    print(f"Warning: {observation}")

                self.conv_his.append({"role": "user", "content": f"Observation: {observation}"})

            except Exception as e:
                return f"Error during ReAct loop: {e}"

        return f"Maximum iterations ({max_iter}) reached"

    def process_user_inp(self, user_inp, max_iter = 15):
        if not user_inp:
            return "", False

        result = self.react_loop(user_inp, max_iter)
        return result, True

    def get_available_tools(self):
        tools = []
        for func_name, info in self.tool_registry.items():
            summary = info['summary']
            tools.append({"name": func_name, "description": summary})
        return tools

    def print_tools_list(self):
        print("\nAvailable tools:")
        tools = self.get_available_tools()
        for i, tool in enumerate(tools, 1):
            print(f"{i:2}. {tool['name']}: {tool['description'][:60]}...")

    def update_system_prompt(self, new_prompt):
        self.system_prompt = new_prompt
        self.conv_his.append({"role": "system", "content": self.system_prompt})

    def update_temperature(self, new_temp):
        self.temperature= new_temp

    def process_user_input_stream(self, user_message, conversation_history=None):
        if conversation_history:
            self.conv_his = conversation_history

        if not user_message:
            return

        self.conv_his.append({"role": "user", "content": user_message})

        for step in range(self.max_iterations):
            if self.stop_flag:
                self.stop_flag = False
                break

            try:
                if self.stream:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        temperature=self.temperature,
                        messages=self.conv_his,
                        stream=True
                    )
                    reply = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            reply += content
                            yield content
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        temperature=self.temperature,
                        messages=self.conv_his,
                        stream=False
                    )
                    reply = response.choices[0].message.content
                    yield reply

                if "Action: final_answer:" in reply:
                    answer = reply.split("Action: final_answer:", 1)[1].strip()
                    self.conv_his.append({"role": "assistant", "content": reply})
                    yield f"\n[Final Answer] {answer}"
                    break

                action, params, has_parens = self.parse_action(reply)

                if action is None:
                    self.conv_his.append({"role": "assistant", "content": reply})
                    break

                self.conv_his.append({"role": "assistant", "content": reply})

                if action in self.tool_registry:
                    if has_parens:
                        res = self.exec_func(action, **params)
                        observation = f"Execution result: {res}"
                        yield f"\n[Observation - Result]\n{observation}"
                    else:
                        observation = self.get_tool_detail(action)
                        yield f"\n[Observation - Tool Detail]\n{observation}"
                else:
                    observation = f"Error: Tool '{action}' not found"
                    yield f"\n[Observation - Error]\n{observation}"

                self.conv_his.append({"role": "user", "content": f"Observation: {observation}"})

            except Exception as e:
                yield f"\n[Error] {str(e)}"
                break

    def process_user_input_with_history(self, user_message, conversation_history):
        if not user_message:
            return ""

        self.conv_his = conversation_history
        response, success = self.process_user_inp(user_message, self.max_iterations)
        return response

    def set_stop_flag(self, value):
        self.stop_flag = value

    def get_mcp_tools_info(self):
        tools = []
        for func_name, info in self.tool_registry.items():
            summary = info['summary']
            is_mcp = func_name.startswith('mcp_')
            server_name = func_name.split('_')[1] if is_mcp and '_' in func_name else "local"

            tools.append({
                'name': func_name,
                'description': summary,
                'enabled': True,
                'server': server_name
            })
        return tools


def main():
    MCP_PATH = input("Directory of MCP files (supports .py or .json) (separate multiple files with spaces):").strip()
    mcp_paths = [p.strip() for p in MCP_PATH.split() if p.strip()]

    ai = AI(mcp_paths=mcp_paths)
    print("Running in ReAct mode")

    while True:
        try:
            user_inp = input("\n>>").strip()
            if user_inp.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            if not user_inp:
                continue

            if user_inp.lower() in ['clear']:
                ai.reset_conversation()
                print("Conversation history cleared")
                continue

            response, completed = ai.process_user_inp(user_inp)
            if response:
                print(f"\n[AI] {response}")

        except KeyboardInterrupt:
            print("\nOperation interrupted, goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

if __name__ == "__main__":
    main()
