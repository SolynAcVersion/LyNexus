# [file name]: ui/chat_box.py
"""
Modern Chat Interface with Fluent Design and Windows 11 style
"""
import sys
import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QScrollArea, QListWidget, QListWidgetItem, QSplitter, QFrame,
    QInputDialog, QMessageBox, QStatusBar, QFileDialog,
    QSizePolicy, QSpacerItem, QApplication, QToolTip, QProgressDialog, QProgressBar
)
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QPixmap, QPainter, QColor, QCursor
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QPoint, QRect, QEvent

from config.i18n import i18n
from utils.config_manager import ConfigManager
from ui.init_dialog import InitDialog
from ui.settings_dialog import SettingsDialog
from aiclass import AI

class AIThread(QThread):
    """AI Processing Thread with real-time status updates."""
    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    
    def __init__(self, ai_instance, message):
        super().__init__()
        self.ai_instance = ai_instance
        self.message = message
        self._should_stop = False
        
    def run(self):
        try:
            # 重置停止标志
            if self.ai_instance:
                self.ai_instance.set_stop_flag(False)
            
            # 执行AI处理
            response, _ = self.ai_instance.process_user_inp(self.message)
            
            if response and not self._should_stop:
                self.finished.emit(response)
                
        except Exception as e:
            if not self._should_stop:
                self.error.emit(str(e))
                self.status_update.emit(f"Error: {str(e)}")
                
    def stop(self):
        """停止线程"""
        self._should_stop = True
        if self.ai_instance:
            self.ai_instance.set_stop_flag(True)

class ModernMessageBubble(QWidget):
    """现代风格的消息气泡 - 类似Telegram/WhatsApp"""
    
    def __init__(self, message: str, is_sender: bool, timestamp: str, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_sender = is_sender
        self.timestamp = timestamp
        
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """设置UI布局"""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 气泡容器
        self.bubble_container = QWidget()
        self.bubble_container.setObjectName("bubbleContainer")
        
        # 气泡布局
        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)
        
        # 消息内容
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setTextFormat(Qt.MarkdownText)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 时间戳和状态
        timestamp_layout = QHBoxLayout()
        timestamp_layout.setContentsMargins(0, 0, 0, 0)
        timestamp_layout.setSpacing(6)
        
        self.timestamp_label = QLabel(self.timestamp)
        self.timestamp_label.setAlignment(Qt.AlignRight)
        
        timestamp_layout.addStretch()
        timestamp_layout.addWidget(self.timestamp_label)
        
        if self.is_sender:
            self.status_label = QLabel("✓")
            timestamp_layout.addWidget(self.status_label)
        
        # 添加到气泡
        bubble_layout.addWidget(self.message_label)
        bubble_layout.addLayout(timestamp_layout)
        
        # 主布局添加气泡容器
        if self.is_sender:
            # 发送者消息右对齐
            container_layout = QHBoxLayout()
            container_layout.setContentsMargins(8, 4, 8, 4)
            container_layout.addStretch()
            container_layout.addWidget(self.bubble_container)
            main_layout.addLayout(container_layout)
        else:
            # 接收者消息左对齐
            container_layout = QHBoxLayout()
            container_layout.setContentsMargins(8, 4, 8, 4)
            container_layout.addWidget(self.bubble_container)
            container_layout.addStretch()
            main_layout.addLayout(container_layout)
    
    def setup_style(self):
        """设置样式"""
        if self.is_sender:
            # 发送者消息 - 蓝色
            bubble_style = """
                #bubbleContainer {
                    background-color: #0084ff;
                    border-radius: 18px 18px 4px 18px;
                    padding: 0px;
                }
                QLabel {
                    color: white;
                    background-color: transparent;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    font-size: 14px;
                }
                QLabel#timestamp {
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 11px;
                }
                QLabel#status {
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 11px;
                }
            """
        else:
            # 接收者消息 - 灰色
            bubble_style = """
                #bubbleContainer {
                    background-color: #2a2a2a;
                    border-radius: 18px 18px 18px 4px;
                    padding: 0px;
                }
                QLabel {
                    color: white;
                    background-color: transparent;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    font-size: 14px;
                }
                QLabel#timestamp {
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 11px;
                }
            """
        
        # 特殊消息类型
        if "**AI Error**" in self.message:
            bubble_style = bubble_style.replace("#2a2a2a", "#d32f2f").replace("#0084ff", "#d32f2f")
        elif "**Execution stopped**" in self.message:
            bubble_style = bubble_style.replace("#2a2a2a", "#f57c00").replace("#0084ff", "#f57c00")
        elif "**Command Execution Requested**" in self.message:
            bubble_style = bubble_style.replace("#2a2a2a", "#388e3c").replace("#0084ff", "#388e3c")
        
        # 设置对象名称以便样式应用
        self.timestamp_label.setObjectName("timestamp")
        if self.is_sender and hasattr(self, 'status_label'):
            self.status_label.setObjectName("status")
        
        self.bubble_container.setStyleSheet(bubble_style)
    
    def sizeHint(self):
        """返回建议大小"""
        # 计算文本高度
        font_metrics = QFontMetrics(self.message_label.font())
        
        # 根据可用宽度计算文本高度（减去内边距）
        available_width = self.message_label.width() if self.message_label.width() > 0 else 400
        available_width = min(available_width, 500)  # 限制最大宽度
        
        text_rect = font_metrics.boundingRect(
            0, 0, available_width, 0,
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            self.message
        )
        
        # 气泡高度 = 文本高度 + 内边距 + 时间戳高度 + 外边距
        text_height = text_rect.height()
        padding = 8 + 8  # 上下内边距
        timestamp_height = 16  # 时间戳行高度
        margin = 8  # 上下外边距
        
        total_height = text_height + padding + timestamp_height + margin
        
        # 返回宽度和高度
        return QSize(available_width + 50, min(800, max(60, total_height)))
    
    def resizeEvent(self, event):
        """处理窗口大小变化"""
        super().resizeEvent(event)
        # 当大小变化时更新大小提示
        self.updateGeometry()

class CommandToolTip(QWidget):
    """自定义命令执行提示工具"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        self.command_label = QLabel()
        self.command_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-family: 'Segoe UI', monospace;
                background-color: rgba(40, 40, 40, 0.9);
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid #555555;
            }
        """)
        layout.addWidget(self.command_label)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-family: 'Segoe UI';
                background-color: rgba(40, 40, 40, 0.9);
                padding: 4px 10px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.status_label)
    
    def show_command(self, command: str, status: str = "Executing..."):
        """显示命令提示"""
        self.command_label.setText(command)
        self.status_label.setText(status)
        
        # 调整大小
        self.adjustSize()
        
        # 显示在鼠标位置
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        
        self.show()
        QTimer.singleShot(3000, self.hide)  # 3秒后自动隐藏

class ModernChatBox(QWidget):
    """现代聊天界面"""
    
    def __init__(self):
        super().__init__()
        
        self.init_dialog = None
        self.settings_dialog = None
        self.ai = None
        self.current_chat_target = i18n.tr("general_chat")
        self.is_processing = False
        self.ai_thread = None
        self.command_tooltip = None
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 加载聊天列表和聊天记录
        self.chat_list_names = self.config_manager.load_chat_list() or [i18n.tr("general_chat")]
        self.chat_records = self.config_manager.load_chat_history()
        
        # 对话特定的AI实例
        self.conversation_ais = {}
        
        # 执行状态定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_execution_status)
        self.status_timer.start(500)  # 每500ms更新一次
        
        # 初始化UI
        self.init_ui()
        
        # 检查API密钥并初始化
        self.initialize_ai()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f'{i18n.tr("app_name")} - AI Assistant')
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置窗口图标
        icon_path = "assets/logo.ico"
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 主内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 左侧边栏
        self.sidebar = self.create_sidebar()
        content_layout.addWidget(self.sidebar)
        
        # 右侧聊天区域
        self.chat_area = self.create_chat_area()
        content_layout.addWidget(self.chat_area, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        # 状态栏
        self.status_bar = self.create_status_bar()
        main_layout.addWidget(self.status_bar)
        
        # 更新状态
        self.update_status_bar()
        
        # 加载聊天列表到UI
        self.load_chat_list_to_ui()
        
        # 切换到默认聊天
        if self.chat_list.count() > 0:
            self.switch_chat_target(self.chat_list.item(0))
    
    def create_title_bar(self):
        """创建标题栏"""
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-bottom: 1px solid #333333;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        
        # 应用图标和标题
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        icon_label.setText("⚡")
        
        title_label = QLabel(i18n.tr("app_name"))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 移除窗口控制按钮
        return title_bar
    
    def create_sidebar(self):
        """创建左侧边栏"""
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-right: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 新聊天按钮
        new_chat_button = QPushButton(i18n.tr("new_chat"))
        new_chat_button.setFixedHeight(48)
        new_chat_button.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                font-size: 14px;
                font-weight: 500;
                margin: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
        """)
        new_chat_button.clicked.connect(self.add_new_chat)
        
        layout.addWidget(new_chat_button)
        
        # 聊天列表标题
        chats_label = QLabel(i18n.tr("conversations"))
        chats_label.setFixedHeight(40)
        chats_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                font-weight: 500;
                padding-left: 16px;
                background-color: transparent;
            }
        """)
        layout.addWidget(chats_label)
        
        # 聊天列表
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 12px 16px;
                border-radius: 0px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #1a73e8;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #1a73e8;
            }
        """)
        
        # 连接点击信号 - 这是关键！
        self.chat_list.itemClicked.connect(self.switch_chat_target)
        
        layout.addWidget(self.chat_list, 1)
        
        # 底部按钮区域
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(240)
        bottom_widget.setStyleSheet("background-color: transparent;")
        
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(12, 12, 12, 12)
        bottom_layout.setSpacing(8)
        
        # 导入配置按钮
        import_button = self.create_sidebar_button(i18n.tr("import_config"), self.import_config_file)
        bottom_layout.addWidget(import_button)
        
        # 设置按钮
        settings_button = self.create_sidebar_button(i18n.tr("settings"), self.open_settings)
        bottom_layout.addWidget(settings_button)
        
        # 初始化按钮
        self.init_button = self.create_sidebar_button(i18n.tr("initialize"), self.show_init_dialog)
        bottom_layout.addWidget(self.init_button)
        
        # 工具按钮
        tools_button = self.create_sidebar_button(i18n.tr("tools"), self.show_tools_list)
        bottom_layout.addWidget(tools_button)
        
        # 导出聊天按钮
        export_button = self.create_sidebar_button(i18n.tr("export_chat"), self.export_chat_history)
        bottom_layout.addWidget(export_button)
        
        # 清空聊天按钮
        clear_button = self.create_sidebar_button(i18n.tr("clear_chat"), self.clear_current_chat)
        bottom_layout.addWidget(clear_button)
        
        bottom_layout.addStretch()
        
        layout.addWidget(bottom_widget)
        
        return sidebar
    
    def create_sidebar_button(self, text, callback):
        """创建侧边栏按钮"""
        button = QPushButton(text)
        button.setFixedHeight(40)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                text-align: left;
                padding-left: 12px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: white;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        button.clicked.connect(callback)
        return button
    
    def create_chat_area(self):
        """创建聊天区域"""
        chat_widget = QWidget()
        chat_widget.setStyleSheet("background-color: #1e1e1e;")
        
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 聊天标题
        self.chat_title = QLabel(i18n.tr("general_chat"))
        self.chat_title.setFixedHeight(60)
        self.chat_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
                padding-left: 24px;
                background-color: transparent;
                border-bottom: 1px solid #333333;
            }
        """)
        layout.addWidget(self.chat_title)
        
        # 消息显示区域
        self.message_scroll = QScrollArea()
        self.message_scroll.setWidgetResizable(True)
        self.message_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #444444;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
        """)
        
        # 消息容器
        self.message_container = QWidget()
        self.message_container.setStyleSheet("background-color: #1e1e1e;")
        
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(16, 16, 16, 16)
        self.message_layout.setSpacing(8)
        
        self.message_scroll.setWidget(self.message_container)
        layout.addWidget(self.message_scroll, 1)
        
        # 输入区域
        input_widget = QWidget()
        input_widget.setFixedHeight(140)
        input_widget.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-top: 1px solid #333333;
            }
        """)
        
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(i18n.tr("type_message"))
        self.input_text.setAcceptRichText(False)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #333333;
                border-radius: 8px;
                color: white;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #0084ff;
            }
            QTextEdit:focus {
                border-color: #0084ff;
                background-color: #2d2d2d;
            }
        """)
        
        input_layout.addWidget(self.input_text, 1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # 停止按钮
        self.stop_button = QPushButton(i18n.tr("stop"))
        self.stop_button.setFixedHeight(36)
        self.stop_button.setVisible(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
            QPushButton:pressed {
                background-color: #ff2222;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """)
        self.stop_button.clicked.connect(self.stop_execution)
        
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        
        # 发送按钮
        self.send_button = QPushButton(i18n.tr("send"))
        self.send_button.setFixedHeight(36)
        self.send_button.setShortcut('Ctrl+Return')
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        
        layout.addWidget(input_widget)
        
        return chat_widget
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #252525;
                color: #888888;
                font-size: 11px;
                border-top: 1px solid #333333;
                padding: 4px 12px;
            }
        """)
        return status_bar
    
    # ============ 新增方法：进度条相关 ============
    
    def show_loading_dialog(self, title="Loading", message="Please wait..."):
        """显示加载进度对话框"""
        self.progress_dialog = QProgressDialog(message, None, 0, 100, self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        
        # 自定义进度条样式
        progress_bar = QProgressBar(self.progress_dialog)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2a2a2a;
                border-radius: 5px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0084ff;
                border-radius: 3px;
            }
        """)
        self.progress_dialog.setBar(progress_bar)
        
        self.progress_dialog.show()
        
        # 启动定时器模拟进度更新
        self.current_progress = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_progress)
        self.loading_timer.start(30)  # 每30ms更新一次
    
    def update_progress(self):
        """更新进度条"""
        if self.progress_dialog:
            # 平滑增加进度，直到95%（留5%给实际完成）
            if self.current_progress < 95:
                self.current_progress = min(95, self.current_progress + 1)
                self.progress_dialog.setValue(self.current_progress)
    
    def complete_progress(self):
        """完成进度条并关闭对话框"""
        if self.progress_dialog:
            self.current_progress = 100
            self.progress_dialog.setValue(100)
            QTimer.singleShot(200, self.close_progress_dialog)  # 延迟200ms关闭
    
    def close_progress_dialog(self):
        """关闭进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if hasattr(self, 'loading_timer') and self.loading_timer:
            self.loading_timer.stop()
            self.loading_timer = None
    
    # ============ 聊天列表相关方法 ============
    
    def load_chat_list_to_ui(self):
        """加载聊天列表到UI"""
        self.chat_list.clear()
        for name in self.chat_list_names:
            self.add_chat_item(name)
        
        # 设置默认选中的项（如果有的话）
        if self.chat_list.count() > 0:
            # 尝试获取最后活动的聊天
            last_chat = self.config_manager.load_last_active_chat()
            if last_chat and last_chat in self.chat_list_names:
                items = self.chat_list.findItems(last_chat, Qt.MatchExactly)
                if items:
                    self.chat_list.setCurrentItem(items[0])
                    self.chat_title.setText(last_chat)
                    self.current_chat_target = last_chat
            else:
                # 否则选择第一个
                self.chat_list.setCurrentRow(0)    
    
    def add_chat_item(self, name: str):
        """添加聊天项到列表并保存到配置"""
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, name)
        
        # 初始化聊天记录
        if name not in self.chat_records:
            self.chat_records[name] = []
        
        # 添加到列表
        self.chat_list.addItem(item)
        
        # 保存聊天列表到配置
        if name not in self.chat_list_names:
            self.chat_list_names.append(name)
            self.config_manager.save_chat_list(self.chat_list_names)
    
    # ============ 修改后的switch_chat_target方法 ============
    
    def switch_chat_target(self, item):
        """切换到不同的聊天"""
        if not item:
            return
            
        conversation_name = item.data(Qt.UserRole)
        
        # 如果已经在当前对话，直接返回
        if conversation_name == self.current_chat_target:
            return
        
        print(f"正在切换到对话: {conversation_name}")  # 调试信息
        
        try:
            # 直接执行切换，不使用定时器
            self.current_chat_target = conversation_name
            self.chat_title.setText(conversation_name)
            
            # 保存最后活动的聊天
            self.config_manager.save_last_active_chat(conversation_name)
            
            # 清空消息显示
            self.clear_message_layout()
            
            # 为此对话加载AI
            if conversation_name in self.conversation_ais:
                self.ai = self.conversation_ais[conversation_name]
                print(f"使用已缓存的AI实例: {conversation_name}")
            else:
                # 加载AI实例
                print(f"创建新的AI实例: {conversation_name}")
                self.load_conversation_ai(conversation_name)
            
            # 加载并显示此聊天的消息
            if conversation_name in self.chat_records:
                messages = self.chat_records[conversation_name]
                print(f"加载 {len(messages)} 条消息")
                
                for msg in messages:
                    self.add_message_to_display(msg["text"], msg["is_sender"])
            
            # 更新状态栏
            self.update_status_bar()
            
            # 确保消息容器大小正确
            self.message_container.adjustSize()
            
            # 滚动到底部
            QTimer.singleShot(50, self.scroll_to_bottom)
            
            print(f"切换到对话 {conversation_name} 完成")
            
        except Exception as e:
            print(f"切换对话时出错: {e}")
            QMessageBox.warning(self, "切换错误", f"切换对话时出错: {e}")
    
    # ============ 消息显示相关方法 ============
    
    def clear_message_layout(self):
        """清空消息显示区域"""
        # 使用更安全的方式移除所有消息部件
        for i in reversed(range(self.message_layout.count())):
            item = self.message_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                # 移除拉伸项
                self.message_layout.removeItem(item)
        
        # 重新设置布局
        self.message_layout.setContentsMargins(16, 16, 16, 16)
        self.message_layout.setSpacing(8)
           
    def add_message_to_display(self, message: str, is_sender: bool):
        """添加消息到显示区域"""
        # 创建消息气泡
        timestamp = datetime.now().strftime("%H:%M")
        bubble = ModernMessageBubble(message, is_sender, timestamp)
        
        # 添加到布局
        self.message_layout.addWidget(bubble)
        
        # 更新布局并调整大小
        bubble.updateGeometry()
        self.message_container.updateGeometry()
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """内部方法滚动到底部"""
        # 确保布局已经更新
        self.message_container.updateGeometry()
        
        # 获取滚动条并滚动到底部
        scrollbar = self.message_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 强制重绘
        self.message_scroll.viewport().update()
    
    # ============ 消息发送和处理方法 ============
    
    def send_message(self):
        """发送消息给AI"""
        message = self.input_text.toPlainText().strip()
        if not message or not self.ai or self.is_processing:
            return
        
        # 设置为处理中
        self.is_processing = True
        
        # 禁用发送按钮，显示停止按钮
        self.send_button.setEnabled(False)
        self.stop_button.setVisible(True)
        self.input_text.clear()
        
        # 添加到聊天记录
        self.chat_records[self.current_chat_target].append({
            "text": message,
            "is_sender": True,
            "timestamp": datetime.now().isoformat()
        })
        
        # 显示消息
        self.add_message_to_display(message, is_sender=True)
        
        # 确保消息容器大小正确
        self.message_container.adjustSize()
        
        # 创建并启动AI线程
        self.ai_thread = AIThread(self.ai, message)
        self.ai_thread.finished.connect(self.handle_ai_response)
        self.ai_thread.error.connect(self.handle_ai_error)
        self.ai_thread.status_update.connect(self.handle_status_update)
        self.ai_thread.start()
    
    def handle_ai_response(self, response):
        """处理AI响应"""
        # 重置处理状态
        self.is_processing = False
        self.stop_button.setVisible(False)
        self.send_button.setEnabled(True)
        
        # 添加到聊天记录
        self.chat_records[self.current_chat_target].append({
            "text": response,
            "is_sender": False,
            "timestamp": datetime.now().isoformat()
        })
        
        # 显示响应
        self.add_message_to_display(response, is_sender=False)
        
        # 更新状态栏
        self.update_status_bar()
        
        # 滚动到底部
        self.scroll_to_bottom()
        
        # 清理线程
        self.ai_thread = None
    
    def handle_ai_error(self, error_msg):
        """处理AI错误"""
        # 重置处理状态
        self.is_processing = False
        self.stop_button.setVisible(False)
        self.send_button.setEnabled(True)
        
        error_display = f"**AI Error**\n```\n{error_msg}\n```"
        
        # 添加到聊天记录
        self.chat_records[self.current_chat_target].append({
            "text": error_display,
            "is_sender": False,
            "timestamp": datetime.now().isoformat()
        })
        
        # 显示错误
        self.add_message_to_display(error_display, is_sender=False)
        
        # 更新状态
        self.update_status_bar()
        
        # 清理线程
        self.ai_thread = None
    
    def handle_status_update(self, status_msg):
        """处理状态更新"""
        if self.ai:
            tools_count = len(self.ai.funcs) if hasattr(self.ai, 'funcs') else 0
            status_text = f"Lynexus AI | Connected to {self.ai.model} | {tools_count} tools available | {status_msg}"
            self.status_bar.showMessage(status_text)
        else:
            self.status_bar.showMessage(f"Lynexus AI | {status_msg}")
    
    def stop_execution(self):
        """停止当前AI执行"""
        if self.ai_thread and self.ai_thread.isRunning():
            print("Stopping AI execution...")
            
            # 禁用停止按钮
            self.stop_button.setEnabled(False)
            
            # 停止线程
            self.ai_thread.stop()
            
            # 设置AI停止标志
            if self.ai:
                self.ai.set_stop_flag(True)
            
            # 等待线程结束
            if self.ai_thread.wait(1000):
                print("AI thread stopped successfully")
            else:
                print("AI thread did not stop in time, terminating...")
                self.ai_thread.terminate()
                self.ai_thread.wait()
            
            # 重置UI状态
            self.is_processing = False
            self.stop_button.setVisible(False)
            self.stop_button.setEnabled(True)
            self.send_button.setEnabled(True)
            
            # 添加停止消息
            stopped_message = "**Execution stopped**\nProcessing was interrupted by user."
            
            self.chat_records[self.current_chat_target].append({
                "text": stopped_message,
                "is_sender": False,
                "timestamp": datetime.now().isoformat()
            })
            
            self.add_message_to_display(stopped_message, is_sender=False)
            
            # 更新状态栏
            self.update_status_bar()
            
            # 清理线程
            self.ai_thread = None
    
    # ============ AI初始化和配置方法 ============
    
    def update_execution_status(self):
        """定时更新执行状态，显示当前执行的命令"""
        if self.ai:
            status_info = self.ai.get_execution_status()
            
            if status_info["status"] == "executing_tool":
                tool_name = status_info.get("tool_name", "Unknown")
                tool_args = status_info.get("tool_args", [])
                
                # 格式化命令显示
                if tool_args:
                    args_str = f" {self.ai.command_separator} ".join([str(arg) for arg in tool_args])
                    command_display = f"{self.ai.command_start}{tool_name} {self.ai.command_separator} {args_str}"
                else:
                    command_display = f"{self.ai.command_start}{tool_name}"
                
                # 计算执行时间
                elapsed_time = ""
                if status_info.get("start_time"):
                    try:
                        start_time = datetime.fromisoformat(status_info["start_time"])
                        elapsed = datetime.now() - start_time
                        elapsed_time = f" | {elapsed.seconds}s elapsed"
                    except:
                        pass
                
                # 在状态栏显示
                tools_count = len(self.ai.funcs) if hasattr(self.ai, 'funcs') else 0
                status_text = f"Lynexus AI | Connected to {self.ai.model} | {tools_count} tools | Executing: {command_display}{elapsed_time}"
                self.status_bar.showMessage(status_text)
                
                # 显示工具提示
                if not self.command_tooltip:
                    self.command_tooltip = CommandToolTip(self)
                self.command_tooltip.show_command(command_display, f"Executing...{elapsed_time}")
    
    def initialize_ai(self):
        """基于保存的配置初始化AI"""
        api_key = self.config_manager.load_api_key()
        if not api_key and not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")):
            QTimer.singleShot(500, self.show_init_dialog)
        else:
            # 加载当前对话AI
            self.load_conversation_ai(self.current_chat_target)
            
            # 更新按钮可见性
            has_api_key = bool(api_key)
            self.init_button.setVisible(not has_api_key)
            self.send_button.setEnabled(has_api_key)
    
    def show_init_dialog(self):
        """显示初始化对话框"""
        if self.init_dialog is None:
            self.init_dialog = InitDialog()
            self.init_dialog.sig_done.connect(self.handle_init_done)
        self.init_dialog.show()
    
    def handle_init_done(self, api_key: str, mcp_files: list, config_file: str):
        """处理初始化完成"""
        if api_key:
            self.config_manager.save_api_key(api_key)
        
        # 加载当前对话AI
        self.load_conversation_ai(self.current_chat_target)
        
        # 更新UI
        self.init_button.setVisible(False)
        self.send_button.setEnabled(True)
        self.update_status_bar()
    
    def load_conversation_ai(self, conversation_name):
        """加载或创建对话的AI实例"""
        try:
            # 如果已经在对话AI字典中，直接返回
            if conversation_name in self.conversation_ais:
                self.ai = self.conversation_ais[conversation_name]
                return
            
            # 加载对话配置
            config = self.config_manager.load_conversation_config(conversation_name)
            
            # 加载API密钥
            api_key = self.config_manager.load_api_key()
            if not api_key:
                api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
            
            if not api_key:
                print(f"No API key found for {conversation_name}")
                return
            
            # 创建AI实例
            if config:
                ai_config = config.copy()
                ai_config['api_key'] = api_key
                
                self.ai = AI(
                    mcp_paths=ai_config.get('mcp_paths', []),
                    api_key=ai_config.get('api_key', ''),
                    api_base=ai_config.get('api_base', 'https://api.deepseek.com'),
                    model=ai_config.get('model', 'deepseek-chat'),
                    system_prompt=ai_config.get('system_prompt', ''),
                    temperature=ai_config.get('temperature', 1.0),
                    max_tokens=ai_config.get('max_tokens'),
                    top_p=ai_config.get('top_p', 1.0),
                    presence_penalty=ai_config.get('presence_penalty', 0.0),
                    frequency_penalty=ai_config.get('frequency_penalty', 0.0),
                    command_start=ai_config.get('command_start', 'YLDEXECUTE:'),
                    command_separator=ai_config.get('command_separator', '￥|'),
                    max_iterations=ai_config.get('max_iterations', 15)
                )
            else:
                # 创建默认AI实例
                self.ai = AI(api_key=api_key, temperature=1.0)
            
            # 存储AI实例
            self.conversation_ais[conversation_name] = self.ai
            
            # 将对话历史加载到AI上下文（异步进行）
            if conversation_name in self.chat_records:
                history_messages = self.chat_records[conversation_name]
                if history_messages:
                    # 在后台线程中加载历史
                    QTimer.singleShot(0, lambda: self._load_history_async(conversation_name, history_messages))
            
            # 更新UI
            self.update_status_bar()
            
        except Exception as e:
            print(f"Failed to create/load AI instance for {conversation_name}: {e}")
        
    def _load_history_async(self, conversation_name, history_messages):
        """异步加载对话历史"""
        try:
            if conversation_name in self.conversation_ais:
                ai = self.conversation_ais[conversation_name]
                # 先清除现有历史
                if hasattr(ai, 'reset_conversation'):
                    ai.reset_conversation()
                # 加载新历史
                ai.load_conversation_history(history_messages)
                print(f"加载了 {len(history_messages)} 条消息到AI上下文: {conversation_name}")
        except Exception as e:
            print(f"加载对话历史时出错: {e}")    
    
    # ============ 状态栏更新方法 ============
    
    def update_status_bar(self):
        """更新状态栏"""
        if self.ai:
            tools_count = len(self.ai.funcs) if hasattr(self.ai, 'funcs') else 0
            status_text = f"Lynexus AI | Connected to {self.ai.model} | {tools_count} tools available | Ready"
            self.status_bar.showMessage(status_text)
        else:
            self.status_bar.showMessage("Lynexus AI | Not connected")
    
    # ============ 设置和配置相关方法 ============
    
    def open_settings(self):
        """打开设置对话框"""
        if not self.current_chat_target:
            return
        
        if self.ai:
            # 使用当前AI实例打开设置
            self.settings_dialog = SettingsDialog(
                ai_instance=self.ai,
                conversation_name=self.current_chat_target
            )
        else:
            # 使用默认配置创建
            default_config = {
                'api_base': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
                'temperature': 1.0,
                'command_start': 'YLDEXECUTE:',
                'command_separator': '￥|',
                'max_iterations': 15,
                'mcp_paths': []
            }
            self.settings_dialog = SettingsDialog(
                current_config=default_config,
                conversation_name=self.current_chat_target
            )
        
        # 连接信号
        self.settings_dialog.sig_save_settings.connect(self.handle_settings_save)
        self.settings_dialog.show()
    
    def handle_settings_save(self, settings: dict):
        """处理设置保存"""
        if self.current_chat_target and self.ai:
            # 保存对话配置
            self.config_manager.save_conversation_config(self.current_chat_target, settings)
            
            # 更新现有AI实例
            self.ai.update_config(settings)
            
            # 更新UI
            self.update_status_bar()
            
            QMessageBox.information(self, "Success", f"Settings updated for {self.current_chat_target}")
    
    def import_config_file(self):
        """导入配置文件并应用到当前对话"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Import Configuration File")
        file_dialog.setNameFilter("Config Files (*.json);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                config_path = selected_files[0]
                try:
                    # 加载配置文件
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 验证配置文件
                    if not isinstance(config, dict):
                        raise ValueError("Invalid configuration format")
                    
                    # 应用配置到当前AI实例
                    if self.ai:
                        self.ai.update_config(config)
                        self.config_manager.save_conversation_config(self.current_chat_target, config)
                        
                        # 重新加载MCP工具
                        if 'mcp_paths' in config:
                            self.ai.load_mcp_tools()
                        
                        QMessageBox.information(self, "Success", f"Configuration imported and applied to '{self.current_chat_target}'")
                        self.update_status_bar()
                    else:
                        QMessageBox.warning(self, "Error", "No AI instance available. Please initialize AI first.")
                        
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Error", "Invalid JSON file")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to import configuration: {str(e)}")
    
    # ============ 其他功能方法 ============
    
    def add_new_chat(self):
        """添加新聊天"""
        name, ok = QInputDialog.getText(self, "New Chat", "Enter chat name:")
        if ok and name:
            self.add_chat_item(name)
            
            # 自动切换到新聊天
            items = self.chat_list.findItems(name, Qt.MatchExactly)
            if items:
                self.chat_list.setCurrentItem(items[0])
                self.switch_chat_target(items[0])
    
    def clear_current_chat(self):
        """清空当前聊天"""
        if self.current_chat_target:
            reply = QMessageBox.question(
                self, "Clear Chat", 
                f"Clear all messages in '{self.current_chat_target}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.chat_records[self.current_chat_target] = []
                self.clear_message_layout()
                
                # 重置AI对话历史
                if self.ai:
                    self.ai.reset_conversation()
    
    def export_chat_history(self):
        """导出聊天历史到桌面文件"""
        if not self.current_chat_target or not self.chat_records.get(self.current_chat_target):
            QMessageBox.warning(self, "Export Error", "No chat history to export")
            return
        
        # 获取桌面路径
        desktop_path = str(Path.home() / "Desktop")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = f"{self.current_chat_target}_{timestamp}.txt"
        default_path = os.path.join(desktop_path, default_file)
        
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Export Chat History")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDirectory(desktop_path)
        file_dialog.selectFile(default_file)
        file_dialog.setNameFilter("Text Files (*.txt);;JSON Files (*.json);;Markdown Files (*.md)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                try:
                    messages = self.chat_records[self.current_chat_target]
                    
                    if file_path.endswith('.json'):
                        import json
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(messages, f, indent=2, ensure_ascii=False)
                    elif file_path.endswith('.md'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"# Chat: {self.current_chat_target}\n\n")
                            f.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                            f.write("---\n\n")
                            for msg in messages:
                                sender = "**You**" if msg.get("is_sender", False) else "**AI**"
                                timestamp = msg.get("timestamp", "")
                                if timestamp:
                                    try:
                                        dt = datetime.fromisoformat(timestamp)
                                        time_str = dt.strftime("%H:%M")
                                    except:
                                        time_str = timestamp
                                else:
                                    time_str = ""
                                
                                f.write(f"{sender} ({time_str}):\n\n")
                                f.write(f"{msg.get('text', '')}\n\n")
                                f.write("---\n\n")
                    else:
                        # 默认保存为txt
                        if not file_path.endswith('.txt'):
                            file_path += '.txt'
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"Chat: {self.current_chat_target}\n")
                            f.write("=" * 50 + "\n\n")
                            for msg in messages:
                                sender = "You" if msg.get("is_sender", False) else "AI"
                                timestamp = msg.get("timestamp", "")
                                if timestamp:
                                    try:
                                        dt = datetime.fromisoformat(timestamp)
                                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                                    except:
                                        time_str = timestamp
                                else:
                                    time_str = ""
                                
                                f.write(f"[{time_str}] {sender}:\n")
                                f.write(f"{msg.get('text', '')}\n\n")
                    
                    QMessageBox.information(self, "Export Success", f"Chat exported to:\n{file_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Export Error", f"Failed to export chat: {e}")
    
    def show_tools_list(self):
        """显示可用工具列表"""
        if self.ai:
            tools = self.ai.get_available_tools()
            if tools:
                tools_text = "**Available Tools**\n\n"
                for i, tool in enumerate(tools, 1):
                    desc = tool.get('description', 'No description')
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    tools_text += f"**{i}. {tool.get('name', 'Unnamed')}**\n   {desc}\n\n"
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Available Tools")
                msg_box.setText(tools_text)
                msg_box.setStyleSheet("QLabel { color: white; min-width: 400px; font-size: 12px; }")
                msg_box.exec()
            else:
                QMessageBox.information(self, "Tools", "No tools available. Add MCP files in Settings.")
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 停止状态更新定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # 如果AI线程在运行则停止
        if hasattr(self, 'ai_thread') and self.ai_thread and self.ai_thread.isRunning():
            print("Stopping AI thread on close...")
            self.ai_thread.stop()
            self.ai_thread.wait(1000)
        
        # 保存聊天历史和聊天列表
        self.config_manager.save_chat_history(self.chat_records)
        self.config_manager.save_chat_list(self.chat_list_names)
        
        # 清理AI实例
        for ai in self.conversation_ais.values():
            if hasattr(ai, 'close'):
                ai.close()
        
        super().closeEvent(event)

# 保留旧版 ChatBox 类，如果需要兼容
class ChatBox(ModernChatBox):
    """兼容旧版 ChatBox 名称"""
    pass