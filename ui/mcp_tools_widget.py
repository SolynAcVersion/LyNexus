# ui/mcp_tools_widget.py
"""
MCP 工具选择组件
在设置对话框中显示所有可用的 MCP 工具,并允许用户通过复选框启用/禁用它们
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QScrollArea, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal


class MCPToolCheckBox(QWidget):
    """单个 MCP 工具的复选框组件"""

    # 状态变更信号
    stateChanged = Signal(str, bool)  # tool_name, is_enabled

    def __init__(self, tool_name: str, description: str, enabled: bool = False, server: str = "", parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.setup_ui(description, enabled, server)

    def setup_ui(self, description: str, enabled: bool, server: str):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)

        # 复选框
        self.checkbox = QCheckBox(self.tool_name)
        self.checkbox.setChecked(enabled)
        self.checkbox.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.checkbox)

        # 工具描述(完整显示,不截断)
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px; padding-left: 20px;")
        layout.addWidget(desc_label)

        # 服务器信息(如果有的话)
        if server:
            server_label = QLabel(f"Server: {server}")
            server_label.setStyleSheet("color: #999; font-size: 10px; padding-left: 20px;")
            layout.addWidget(server_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

    def _on_state_changed(self, state):
        """处理状态变更"""
        is_enabled = state == Qt.Checked.value
        self.stateChanged.emit(self.tool_name, is_enabled)

    def is_checked(self) -> bool:
        """返回复选框状态"""
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool):
        """设置复选框状态"""
        self.checkbox.setChecked(checked)


class MCPToolsWidget(QWidget):
    """MCP 工具选择组件"""

    # 工具状态变更信号
    toolStateChanged = Signal(str, bool)  # tool_name, is_enabled

    def __init__(self, ai_instance, parent=None):
        super().__init__(parent)
        self.ai_instance = ai_instance
        self.tool_checkboxes = {}  # {tool_name: MCPToolCheckBox}
        self.setup_ui()
        self.load_tools()

    def setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("MCP Tools")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 说明文本
        info_label = QLabel(
            "Select which MCP tools should be available to the AI.\n"
            "Only enabled tools will be included in the system prompt."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px 0;")
        layout.addWidget(info_label)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 工具列表容器
        self.tools_container = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_container)
        self.tools_layout.setContentsMargins(5, 5, 5, 5)
        self.tools_layout.setSpacing(10)

        scroll_area.setWidget(self.tools_container)
        layout.addWidget(scroll_area)

    def load_tools(self):
        """从 AI 实例加载工具列表"""
        # 清空现有工具
        for i in reversed(range(self.tools_layout.count())):
            self.tools_layout.itemAt(i).widget().setParent(None)

        self.tool_checkboxes.clear()

        # 获取工具信息
        tools_info = self.ai_instance.get_mcp_tools_info()

        if not tools_info:
            no_tools_label = QLabel("No MCP tools loaded")
            no_tools_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            self.tools_layout.addWidget(no_tools_label)
            return

        # 为每个工具创建复选框
        for tool in tools_info:
            tool_widget = MCPToolCheckBox(
                tool_name=tool['name'],
                description=tool['description'],
                enabled=tool['enabled'],
                server=tool['server']
            )

            # 连接状态变更信号
            tool_widget.stateChanged.connect(self._on_tool_state_changed)

            self.tools_layout.addWidget(tool_widget)
            self.tool_checkboxes[tool['name']] = tool_widget

        # 添加弹性空间
        self.tools_layout.addStretch()

    def _on_tool_state_changed(self, tool_name: str, is_enabled: bool):
        """处理工具状态变更"""
        # 更新 AI 实例
        self.ai_instance.set_tool_enabled(tool_name, is_enabled)

        # 转发信号
        self.toolStateChanged.emit(tool_name, is_enabled)

    def get_enabled_tools(self) -> list:
        """获取所有已启用的工具名称"""
        return [
            tool_name
            for tool_name, checkbox in self.tool_checkboxes.items()
            if checkbox.is_checked()
        ]

    def set_tool_enabled(self, tool_name: str, enabled: bool):
        """设置工具启用状态"""
        if tool_name in self.tool_checkboxes:
            self.tool_checkboxes[tool_name].set_checked(enabled)

    def refresh_tools(self):
        """刷新工具列表"""
        self.load_tools()


# 使用示例(在设置对话框中)
"""
from ui.mcp_tools_widget import MCPToolsWidget
from aiclass import AI

class SettingsDialog(QDialog):
    def __init__(self, ai_instance, parent=None):
        super().__init__(parent)
        self.ai_instance = ai_instance
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建 MCP 工具选择组件
        self.mcp_tools_widget = MCPToolsWidget(self.ai_instance)

        # 添加到布局
        layout.addWidget(self.mcp_tools_widget)

        # 连接信号(可选)
        self.mcp_tools_widget.toolStateChanged.connect(self.on_tool_changed)

    def on_tool_changed(self, tool_name: str, is_enabled: bool):
        print(f"Tool {tool_name} {'enabled' if is_enabled else 'disabled'}")
        # 可以在这里保存配置等操作
"""
