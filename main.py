# [file name]: main.py
"""
Main entry point for Lynexus AI Assistant application.
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLocale

# 导入 ModernChatBox 替代 ChatBox
from ui.chat_box import ModernChatBox
from config.i18n import i18n

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
        # 使用 ModernChatBox 替代 ChatBox
        chat_box = ModernChatBox()
        chat_box.show()
        
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