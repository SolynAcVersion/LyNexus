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

【Format】
Thought: [your reasoning]
Action: [tool_name]

Wait for Observation before your next Thought.

【Rules】
1. Start with "Thought:" before any "Action:"
2. Each Action should be ONE single step
3. Use "Action: final_answer: [answer]" when task is complete

【Example】
User: What's the current date?

Thought: User wants current date. Use get_current_date tool.
Action: get_current_date

Observation: [Tool: get_current_date]
Description: Get current system date
Parameters: None

Thought: Got tool details. Execute it.
Action: get_current_date()

Observation: 

Thought: Successfully obtained date. Provide final answer.
Action: final_answer: Today's date is 2026-03-22.

【Available Tools】
{TOOLS_LIST}

【Tool Usage】
- First Action: Output tool name to get detailed information
- Second Action: Use tool_name(param1=value1, param2=value2) to execute
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
        """Load multiple MCP module files"""
        all_funcs = {}
        all_mods = []

        for path in mcp_paths:
            mod, funcs = self.load_mcp_mod(path)
            if mod:
                all_mods.append(mod)
            if funcs:
                for func_name, func in funcs.items():
                    if func_name in all_funcs:
                        print(f"Function '{func_name}' exists in multiple files, using last loaded version")
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

        desc = "【Available Tools】\n"
        for func_name, info in self.tool_registry.items():
            desc += f"- {func_name}: {info['summary']}\n"

        desc += "\nTo use a tool, output: Action: tool_name\n"
        desc += "You will receive detailed parameter information before execution.\n"

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

            return f"Execution successful: {res}"
        except Exception as e:
            return f"Execution failed: {e}"

    def parse_action(self, text):
        match = re.search(r'Action:\s*(\w+)', text)
        if not match:
            return None, None

        action = match.group(1)

        if action == "final_answer":
            answer_match = re.search(r'Action:\s*final_answer:\s*(.+)', text, re.DOTALL)
            if answer_match:
                return "final_answer", answer_match.group(1).strip()
            return "final_answer", ""

        params = {}
        params_match = re.search(rf'{action}\s*\((.*?)\)', text)
        if params_match:
            params_str = params_match.group(1)
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

        return action, params

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
                reply = response.choices[0].message.content

                self.conv_his.append({"role": "assistant", "content": reply})

                if "Action: final_answer:" in reply:
                    answer_match = re.search(r'Action:\s*final_answer:\s*(.+)', reply, re.DOTALL)
                    if answer_match:
                        return answer_match.group(1).strip()
                    return "Task completed"

                action, params = self.parse_action(reply)

                if action is None:
                    return reply

                if action in self.tool_registry:
                    if params:
                        print(f"\n[Step {step + 1}] Executing: {action}")
                        res = self.exec_func(action, **params)
                        observation = f"Execution result: {res}"
                        print(f"Result: {res}")
                    else:
                        print(f"\n[Step {step + 1}] Tool query: {action}")
                        observation = self.get_tool_detail(action)
                else:
                    observation = f"Error: Tool '{action}' not found"
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
                    answer_match = re.search(r'Action:\s*final_answer:\s*(.+)', reply, re.DOTALL)
                    if answer_match:
                        self.conv_his.append({"role": "assistant", "content": reply})
                        yield f"\n[Final Answer] {answer_match.group(1).strip()}"
                    break

                action, params = self.parse_action(reply)

                if action is None:
                    self.conv_his.append({"role": "assistant", "content": reply})
                    break

                self.conv_his.append({"role": "assistant", "content": reply})

                if action in self.tool_registry:
                    if params:
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
