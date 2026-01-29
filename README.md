# LyNexus - Community-Driven AI Agent Platform

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.46-blue" alt="Version">
  <img src="https://img.shields.io/badge/License-MPL%202.0-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/WebUI-React%202024-blue" alt="WebUI">
</p>

<div align="center">
  <strong>Empower your AI development with community-driven intelligence</strong>
</div>

<div align="center">
  <a href="README_zh_cn.md">简体中文</a>
</div>

## 🌟 What is LyNexus?

LyNexus is a **community-driven AI agent platform** that empowers developers to create, customize, and share intelligent agents with configurable prompts, tools, and behavior parameters. Built with flexibility and collaboration in mind, it transforms AI development into a shared experience.

🎯 **Key Philosophy**: Create once, share everywhere. Learn from others, build faster.

## ✨ Features

### 🤖 **Flexible AI Configuration**
- **Model Agnostic**: Connect to various AI models (DeepSeek, OpenAI, Anthropic, etc.)
- **Parameter Freedom**: Fine-tune temperature, tokens, penalties, and more
- **Custom System Prompts**: Tailor AI behavior to your exact needs
- **MCP Integration**: Seamlessly integrate Model Context Protocol tools

### 🌐 **Dual Interface Architecture**
- **Modern WebUI**: Built with React + Vite + Tailwind CSS
  - Telegram-style chat interface
  - Real-time streaming responses
  - Dark theme optimized for long sessions
  - File drag-and-drop support
- **Desktop Application**: PySide6/Qt-based native experience
  - Windows 11 inspired UI design
  - Multi-conversation management
  - Export chats as TXT, JSON, or Markdown

### 🔄 **Community-Driven Ecosystem**
- **One-Click Export**: Package your entire configuration for sharing
- **One-Click Import**: Use others' optimized setups instantly
- **Configuration Sharing**: Share & discover configurations
- **Stand on Giants' Shoulders**: Build upon community-tested configurations

### ⚡ **Advanced Tooling**
- **Command Execution**: AI can execute shell commands (configurable)
- **Tool Integration**: Connect to various APIs and services via MCP
- **Execution Control**: Stop long-running operations anytime
- **History Management**: Preserve and load conversation history

## 🚀 Quick Start

### Option 1: Modern WebUI (Recommended)

#### Windows
1. Double-click `start.bat`
2. Wait for both servers to start
3. Browser opens automatically at http://localhost:5173

#### Linux/Mac
```bash
# Install dependencies
pip install -r requirements-api.txt
cd webui && npm install

# Start the application
cd ..
python start_dev.py
```

### Option 2: Desktop Application

#### Windows
```bash
python main.py
```

#### Linux/Mac
```bash
python3 main.py
```

## 📦 Project Structure

```
LyNexus/
├── main.py                 # Desktop application entry point (PySide6)
├── api_server.py           # FastAPI backend for WebUI
├── start_dev.py            # Quick start script for WebUI
├── start.bat               # Windows quick start script
├── aiclass.py              # Core AI functionality
├── mcp_utils.py            # MCP protocol utilities
│
├── webui/                  # Modern WebUI (React + Vite)
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client & services
│   │   └── stores/         # State management (Zustand)
│   ├── electron/           # Electron desktop wrapper
│   ├── package.json
│   └── vite.config.ts
│
├── ui/                     # PySide6 Desktop UI
│   ├── chat_box.py         # Main chat interface
│   ├── init_dialog.py      # Initialization dialog
│   ├── settings_dialog.py  # Settings interface
│   └── mcp_tools_widget.py # MCP tools display
│
├── tools/                  # MCP Tools Implementation
│   ├── files.py            # File operations
│   ├── network.py          # Network requests
│   ├── ocr.py              # OCR functionality
│   └── osmanager.py        # OS operations
│
├── utils/                  # Utility Functions
│   ├── config_manager.py   # Configuration management
│   ├── chat_data_manager.py # Chat data handling
│   ├── stream_processor.py # Stream processing
│   └── markdown_renderer.py # Markdown rendering
│
├── config/                 # Configuration files
├── data/                   # User data directory
│   └── conversations/      # Conversation storage
├── conversations/          # Legacy conversation storage
├── docs/                   # Documentation
│   ├── README.md           # English documentation
│   └── zh-cn/README.md     # Chinese documentation
│
├── requirements.txt        # Python dependencies
├── requirements-api.txt    # API server dependencies
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

## 🔧 First Time Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements-api.txt
```

### 2. Install WebUI Dependencies
```bash
cd webui
npm install
cd ..
```

### 3. Configure API Key
- Open the application
- Click "Initialize" or go to Settings
- Enter your API key:
  - **DeepSeek**: https://platform.deepseek.com
  - **OpenAI**: https://platform.openai.com
  - **Anthropic**: https://console.anthropic.com
- Save and start chatting!

## 📖 Documentation

For detailed installation, configuration, and usage instructions:

- **[Documentation Website](https://solynacversion.github.io/LyNexus)**
- **[API Documentation](README_API.md)** - Backend API reference
- **[WebUI Guide](docs/README.md)** - WebUI specific documentation

The documentation covers:
- Installation and setup
- Configuration options
- Usage guide
- Sharing workflows
- Advanced features
- API reference
- And much more!

## 🔌 API Documentation

Once the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Development

### Start Backend Only
```bash
python -m uvicorn api_server:app --reload
```

### Start Frontend Only
```bash
cd webui
npm run dev
```

### Build WebUI for Production
```bash
cd webui
npm run build
```

### Build Electron Desktop App
```bash
cd webui
npm run electron:build
```

## 📁 Data Location

All conversations and settings are stored in:
- `data/conversations/{id}/` - Per-conversation data
  - `settings.json` - Conversation settings
  - `.confignore` - API key (not exported)
  - `{id}_ai.json` - Message history
  - `tools/` - MCP tool files

## 🔄 Migration from Qt UI

Your existing conversations are automatically compatible!

The new WebUI uses the same data structure as the Qt application, so all your existing conversations will appear automatically.

### What Changed

| Component | Qt UI | WebUI |
|-----------|-------|-------|
| **Interface** | PySide6/Qt | React + Vite |
| **Backend** | Embedded in Qt | FastAPI |
| **Styling** | QSS | Tailwind CSS |
| **State** | Qt Signals | Zustand |
| **Communication** | Direct calls | REST API |

### What Stayed the Same

- ✅ AI core logic (`aiclass.py`)
- ✅ Data managers (`utils/`)
- ✅ Conversation storage structure
- ✅ MCP tool integration

## 🤝 Community & Contribution

#### Join Our Community
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Share your amazing AI agents
- **Documentation**: [https://solynacversion.github.io/LyNexus](https://solynacversion.github.io/LyNexus)

#### Contributing

We welcome contributions! Here's how you can help:

1. **Share Configurations**: Upload your best setups
2. **Report Bugs**: Help us improve stability
3. **Suggest Features**: What would make LyNexus better?
4. **Improve Documentation**: Help others get started
5. **Code Contributions**: Submit pull requests

Check out our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Port 5173 Already in Use
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5173 | xargs kill -9
```

### Backend Not Connecting
1. Check if API server is running: http://localhost:8000/docs
2. Check WebUI console (F12) for errors
3. Verify `webui/.env` has correct `VITE_API_BASE_URL`

### "AI Not Initialized" Error
1. Go to Settings (gear icon in sidebar)
2. Enter your API key
3. Click "Save Settings"

## 🚀 Production Deployment

### Run with Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Serve WebUI with Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # API server
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebUI static files
    location / {
        root /path/to/LyNexus/webui/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 📄 License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Community**: For sharing knowledge and configurations
- **Open Source Projects**: That made this platform possible
- **Contributors**: Everyone who helps improve LyNexus
- **Users**: For trusting us with your AI development needs

---

<div align="center">
  <p><strong>Built with ❤️ by the AI community, for the AI community</strong></p>
  <p>
    <a href="https://solynacversion.github.io/LyNexus">Documentation</a> •
    <a href="https://github.com/SolynAcVersion/LyNexus/issues">Issues</a> •
    <a href="https://github.com/SolynAcVersion/LyNexus/discussions">Discussions</a>
  </p>
  <p><sub>Star ⭐ this repository if you find it useful!</sub></p>
</div>
