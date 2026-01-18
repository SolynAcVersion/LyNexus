# [file name]: main.py
"""
Main entry point for Lynexus AI Assistant application.
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLocale, QThread, Signal, QTimer

# 导入 ModernChatBox 替代 ChatBox
from ui.chat_box import ModernChatBox
from ui.splash_screen import SplashScreen
from config.i18n import i18n


class InitializationThread(QThread):
    """Background thread for async initialization"""
    progress_updated = Signal(str, int)  # status, progress (0-100)
    finished = Signal()

    def run(self):
        """Run initialization tasks"""
        # Simulate loading steps
        import time

        self.progress_updated.emit("Loading configuration...", 10)
        time.sleep(0.3)

        self.progress_updated.emit("Loading chat history...", 30)
        time.sleep(0.3)

        self.progress_updated.emit("Initializing AI module...", 50)
        time.sleep(0.3)

        self.progress_updated.emit("Loading MCP tools...", 70)
        time.sleep(0.3)

        self.progress_updated.emit("Preparing user interface...", 90)
        time.sleep(0.3)

        self.progress_updated.emit("Ready!", 100)
        time.sleep(0.2)

        self.finished.emit()


def main():
    """Main application entry point."""
    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("Lynexus")
    app.setOrganizationName("Lynexus")

    # 设置应用程序字体
    from PySide6.QtGui import QFont
    font = QFont("Segoe UI", 9)  # 添加回退大小
    app.setFont(font)

    # 设置应用程序样式
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致

    # 设置语言基于系统区域设置
    system_language = QLocale.system().name()[:2]
    if system_language in i18n.get_supported_languages():
        i18n.set_language(system_language)
    else:
        i18n.set_language("en")  # 默认英文

    # 创建并显示主窗口
    try:
        # Show splash screen first
        splash = SplashScreen()
        splash.show()

        # Create main window (hidden initially)
        chat_box = ModernChatBox()

        # Create initialization thread
        init_thread = InitializationThread()

        # Connect signals
        def on_progress(status, progress):
            splash.set_status(status)
            splash.set_progress(progress)
            # Pulse effect for visual feedback
            if progress < 100:
                QTimer.singleShot(100, splash.pulse_progress)

        def on_init_finished():
            # Hide splash
            splash.close()
            # Show main window
            chat_box.show()
            # Clean up
            splash.deleteLater()

        init_thread.progress_updated.connect(on_progress)
        init_thread.finished.connect(on_init_finished)

        # Start async loading
        QTimer.singleShot(100, init_thread.start)

        # 运行应用程序事件循环
        return_code = app.exec()

        # 清理
        sys.exit(return_code)

    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()