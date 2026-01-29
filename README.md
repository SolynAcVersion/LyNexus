# LyNexus - Community-Driven AI Agent Platform

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.6-blue" alt="Version">
  <img src="https://img.shields.io/badge/License-MPL%202.0-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/WebUI-React%202026-blue" alt="WebUI">
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

### 🌐 **Modern Interface**
- Built with React + Vite + Tailwind CSS
- Telegram-style chat interface
- Real-time streaming responses
- Dark theme optimized for long sessions
- File drag-and-drop support
- Multi-conversation management
- Export chats as TXT, JSON, or Markdown

### 🔄 **Community-Driven Ecosystem**
- **One-Click Export**: Package your entire configuration for sharing
- **One-Click Import**: Use others' optimized setups instantly
- **Configuration Sharing**: Share & discover configurations
- **Stand on Giants' Shoulders**: Build upon community-tested configurations

### ⚡ **Advanced Tooling**
- **Dynamic Tool Discovery**: AI automatically understands and uses MCP tools through their descriptions - no hardcoded tool names
- **Command Execution**: AI can execute shell commands (configurable)
- **Tool Integration**: Connect to various APIs and services via MCP protocol
- **Execution Control**: Stop long-running operations anytime
- **History Management**: Preserve and load conversation history

## 🚀 Quick Start

### Development Mode

```bash
# Terminal 1: Start API server
uv run uvicorn api_server:app --reload

# Terminal 2: Start WebUI
cd webui
npm run dev
```

Open http://localhost:5173 in your browser.

### Release Version

🚧 **Coming soon** - Pre-built release packages will be available for download.

## 📦 Project Structure

```
LyNexus/
├── api_server.py           # FastAPI backend server
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
├── docs/                   # Documentation
│   ├── README.md           # English documentation
│   └── zh-cn/README.md     # Chinese documentation
│
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

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
uv run uvicorn api_server:app --reload
```

### Start Frontend Only
```bash
cd webui
npm run dev
```

### Build WebUI
```bash
cd webui
npm run build
```

### Build Electron App
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
