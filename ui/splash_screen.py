"""
Splash Screen - Loading screen with progress indicator
Displays during async loading of MCP tools and conversations
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPainter, QPen, QColor


class SplashScreen(QWidget):
    """Splash screen with loading indicator"""

    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui()
        self._position_center()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main container with rounded corners
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 500, 300)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-radius: 15px;
                border: 2px solid #4a9cff;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)

        # Logo/Title
        title_label = QLabel("LyNexus AI")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #4a9cff; font-size: 32px; font-weight: bold;")
        container_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("AI Assistant with MCP Tools")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #a0a0a0; font-size: 14px;")
        container_layout.addWidget(subtitle_label)

        container_layout.addSpacing(30)

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        container_layout.addWidget(self.status_label)

        container_layout.addSpacing(20)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)  # Indeterminate progress
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2A2A;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4a9cff;
                border-radius: 2px;
            }
        """)
        container_layout.addWidget(self.progress_bar)

        container_layout.addStretch()

        # Loading text
        self.loading_label = QLabel("Loading, please wait...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #808080; font-size: 12px;")
        container_layout.addWidget(self.loading_label)

    def _position_center(self):
        """Center the splash screen on screen"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def set_status(self, text: str):
        """Update status text"""
        self.status_label.setText(text)

    def set_progress(self, value: int):
        """Update progress value (0-100)"""
        self.progress_bar.setValue(value)

    def pulse_progress(self):
        """Animate progress bar for indeterminate loading"""
        current = self.progress_bar.value()
        next_val = (current + 10) % 100
        self.progress_bar.setValue(next_val)
