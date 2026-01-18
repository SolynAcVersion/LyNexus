"""
MCP Config Loader and Tool Manager
识别并加载 MCP 配置文件中的多 server 配置
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


class MCPServer:
    """单个 MCP 服务器配置"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.command = config.get("command", "npx")
        self.args = config.get("args", [])
        self.env = config.get("env", {})

    def get_launch_command(self) -> str:
        """获取完整的启动命令"""
        cmd = self.command + " " + " ".join(self.args)
        return cmd

    def get_environment_vars(self) -> Dict[str, str]:
        """获取环境变量"""
        return self.env.copy()


class MCPConfigLoader:
    """MCP 配置加载器"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__),
            "mcp_config.json"
        )
        self.servers: Dict[str, MCPServer] = {}
        self.load_config()

    def load_config(self) -> bool:
        """加载 MCP 配置文件"""
        if not os.path.exists(self.config_path):
            print(f"[MCPConfigLoader] Config file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            servers = config_data.get("servers", {})

            for name, server_config in servers.items():
                self.servers[name] = MCPServer(name, server_config)
                print(f"[MCPConfigLoader] Loaded server: {name} - Command: {self.servers[name].get_launch_command()}")

            print(f"[MCPConfigLoader] Loaded {len(self.servers)} MCP servers")
            return True

        except Exception as e:
            print(f"[MCPConfigLoader] Error loading config: {e}")
            return False

    def get_servers(self) -> Dict[str, MCPServer]:
        """获取所有服务器配置"""
        return self.servers

    def get_server(self, name: str) -> Optional[MCPServer]:
        """获取特定服务器配置"""
        return self.servers.get(name)

    def get_available_server_names(self) -> List[str]:
        """获取可用服务器名称列表"""
        return list(self.servers.keys())


class MCPToolManager:
    """MCP 工具管理器"""

    def __init__(self, mcp_loader: MCPConfigLoader):
        self.mcp_loader = mcp_loader
        self.active_tools: Dict[str, Any] = {}

    def load_tools_from_config(self, server_name: str = None) -> Dict[str, Any]:
        """
        从配置加载工具

        Args:
            server_name: 指定加载哪个 server，None 表示加载所有

        Returns:
            工具字典 {tool_name: tool_description}
        """
        tools = {}

        servers_to_load = [server_name] if server_name else self.mcp_loader.get_available_server_names()]

        for name in servers_to_load:
            server = self.mcp_server.get_server(name)
            if server:
                tool_desc = f"MCP Server: {name}\nCommand: {server.get_launch_command()}"

                # 使用 server 名称作为工具名称
                tools[name] = {
                    "description": tool_desc,
                    "server": server
                }

        print(f"[MCPToolManager] Loaded {len(tools)} tools from {len(servers_to_load)} servers")
        return tools

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """获取特定工具配置"""
        tools = self.load_tools_from_config()
        return tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, Any]:
        """获取所有可用工具"""
        return self.load_tools_from_config()

    def execute_tool(self, tool_name: str, args: List[str] = None) -> str:
        """
        执行 MCP 工具（模拟）

        在实际使用中，这里会调用 Python subprocess 启动 npx 进程
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"

        server = tool["server"]
        cmd = server.get_launch_command()

        # 在实际实现中，这里会使用 subprocess.Popen()
        # 现在只返回命令字符串
        return f"Executing: {cmd}"

    def get_server_for_tool(self, tool_name: str) -> Optional[MCPServer]:
        """获取工具对应的服务器"""
        tools = self.load_tools_from_config()
        if tool_name in tools and "server" in tools[tool_name]:
            return tools[tool_name]["server"]
        return None


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    """测试 MCP 配置加载"""

    print("=" * 60)
    print("MCP Config Loader Test")
    print("=" * 60)

    # 创建加载器
    loader = MCPConfigLoader()

    # 获取所有服务器
    servers = loader.get_available_server_names()
    print(f"\nAvailable servers: {servers}")

    # 创建工具管理器
    tool_manager = MCPToolManager(loader)

    # 加载工具
    tools = tool_manager.get_all_tools()

    print("\n" + "=" * 60)
    print("Available Tools:")
    print("=" * 60)

    for name, info in tools.items():
        print(f"\n{name}:")
        print(f"  Description: {info['description']}")
        if "server" in info:
            server = info["server"]
            print(f"  Server: {server.name}")
            print(f"  Command: {server.get_launch_command()}")
