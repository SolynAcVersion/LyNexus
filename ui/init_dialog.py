# [file name]: ui/init_dialog.py
import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGridLayout, QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal

from config.i18n import i18n

class InitDialog(QWidget):
    sig_done = Signal(str, str, str)  # api_key, api_base, model

    def __init__(self):
        super().__init__()

        self.api_key = ""
        self.api_base = ""
        self.model = ""

        self.setWindowTitle(i18n.tr("initial_setup"))
        self.resize(600, 300)

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel(i18n.tr("setup_title"))
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4a9cff;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(i18n.tr("setup_desc"))
        desc_label.setStyleSheet("color: #a0a0a0;")
        desc_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc_label)

        main_layout.addSpacing(20)

        # Configuration container
        config_container = QWidget()
        config_layout = QGridLayout(config_container)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(12)

        # API source selection
        config_layout.addWidget(QLabel("API Provider:"), 0, 0, Qt.AlignRight)
        self.api_source_combo = QComboBox()
        self.api_source_combo.addItems([
            "DeepSeek", "OpenAI", "Anthropic", "GLM", "Local", "Custom"
        ])
        self.api_source_combo.currentTextChanged.connect(self.on_api_source_changed)
        config_layout.addWidget(self.api_source_combo, 0, 1)

        # API base URL
        config_layout.addWidget(QLabel("API Base URL:"), 1, 0, Qt.AlignRight)
        self.api_base_edit = QLineEdit()
        self.api_base_edit.setPlaceholderText("https://api.deepseek.com")
        self.api_base_edit.setText("https://api.deepseek.com")
        config_layout.addWidget(self.api_base_edit, 1, 1)

        # Model selection with combo box and custom input
        model_layout = QHBoxLayout()
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(5)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "deepseek-chat",
            "gpt-4-turbo",
            "gpt-4o",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "glm-4-plus",
            "glm-4.7",
            "llama2",
            "custom"
        ])
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        # Custom model input (hidden by default)
        self.custom_model_edit = QLineEdit()
        self.custom_model_edit.setPlaceholderText("Enter custom model name")
        self.custom_model_edit.setVisible(False)
        model_layout.addWidget(self.custom_model_edit)

        config_layout.addWidget(QLabel("Model:"), 2, 0, Qt.AlignRight)
        config_layout.addLayout(model_layout, 2, 1)

        # API key
        config_layout.addWidget(QLabel("API Key:"), 3, 0, Qt.AlignRight)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter API key (sk-xxx...)")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        config_layout.addWidget(self.api_key_edit, 3, 1)

        main_layout.addWidget(config_container)

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        done_button = QPushButton(i18n.tr("start_lynexus"))
        done_button.clicked.connect(self.close_dialog)
        done_button.setStyleSheet("background-color: #4a9cff; color: white; font-weight: bold;")

        button_layout.addStretch()
        button_layout.addWidget(done_button)

        main_layout.addWidget(button_container)
        main_layout.addStretch()

        # Set shortcut
        done_button.setShortcut('return')

    def on_api_source_changed(self, source):
        """根据选择的API提供商更新默认值"""
        defaults = {
            "DeepSeek": ("https://api.deepseek.com", "deepseek-chat"),
            "OpenAI": ("https://api.openai.com/v1", "gpt-4o"),
            "Anthropic": ("https://api.anthropic.com", "claude-3-5-sonnet-20241022"),
            "GLM": ("https://open.bigmodel.cn/api/paas/v4", "glm-4-plus"),
            "Local": ("http://localhost:11434", "llama2"),
            "Custom": ("", "custom")
        }

        if source in defaults:
            api_base, model = defaults[source]
            self.api_base_edit.setText(api_base)
            if model in [self.model_combo.itemText(i) for i in range(self.model_combo.count())]:
                self.model_combo.setCurrentText(model)

    def on_model_changed(self, model):
        """Show/hide custom model input based on selection"""
        self.custom_model_edit.setVisible(model == "custom")

    def close_dialog(self):
        """关闭对话框并发出信号"""
        self.api_key = self.api_key_edit.text()
        self.api_base = self.api_base_edit.text()

        # Get model name
        if self.model_combo.currentText() == "custom":
            self.model = self.custom_model_edit.text().strip()
            if not self.model:
                QMessageBox.warning(self, "Validation Error", "Please enter a custom model name")
                return
        else:
            self.model = self.model_combo.currentText()

        # 保存非敏感配置到 data 目录（不包含API key）
        if self.api_base or self.model:
            config_data = {
                "api_base": self.api_base,
                "model": self.model
            }
            config_path = "data/last_config.json"
            os.makedirs("data", exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)

        self.sig_done.emit(self.api_key, self.api_base, self.model)
        self.close()
