# Lynexus - Community-Driven AI Agent Platform 

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.46-blue" alt="Version">
  <img src="https://img.shields.io/badge/License-MPL 2.0-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey" alt="Platform">
</p>

<div align="center">
  <strong>Empower your AI development with community-driven intelligence</strong>
</div>

<div align="center">
  <a href = "https://github.com/SolynAcVersion/LyNexus/blob/main/README_zh_cn.md">简体中文</a>
</div>

## 🌟 What is Lynexus?

Lynexus is a **community-driven AI agent platform** that empowers developers to create, customize, and share intelligent agents with configurable prompts, tools, and behavior parameters. Built with flexibility and collaboration in mind, it transforms AI development into a shared experience.

🎯 **Key Philosophy**: Create once, share everywhere. Learn from others, build faster.

## ✨ Features

### 🤖 **Flexible AI Configuration**
- **Model Agnostic**: Connect to various AI models (DeepSeek, OpenAI, etc.)
- **Parameter Freedom**: Fine-tune temperature, tokens, penalties, and more
- **Custom System Prompts**: Tailor AI behavior to your exact needs
- **MCP Integration**: Seamlessly integrate Model Context Protocol tools

### 🔄 **Community-Driven Ecosystem**
- **One-Click Export**: Package your entire configuration for sharing
- **One-Click Import**: Use others' optimized setups instantly
- **Forum Integration**: Share & discover configurations on our community forum
- **Stand on Giants' Shoulders**: Build upon community-tested configurations

### 🎨 **Modern Interface**
- **Windows 11 Inspired UI**: Clean, dark-themed interface
- **Conversation Management**: Multiple chat sessions with independent AI instances
- **Real-time Execution**: Watch AI execute commands with live status updates
- **Export Formats**: Save chats as TXT, JSON, or Markdown

### ⚡ **Advanced Tooling**
- **Command Execution**: AI can execute shell commands (configurable)
- **Tool Integration**: Connect to various APIs and services via MCP
- **Execution Control**: Stop long-running operations anytime
- **History Management**: Preserve and load conversation history

## 🚀 Quick Start

#### Prerequisites
- Python 3.8 or higher
- AI API key (DeepSeek, OpenAI, etc.)

#### Installation

```bash
# Clone the repository
git clone https://github.com/SolynAcVersion/LyNexus.git
cd lynexus

# Install dependencies
uv pip install -r requirements.txt
```

#### Launch Options
**Option 1: Run from source**
```bash
uv run python ./main.py
```
**Option 2: Download release (coming soon)**
- Download the latest release from [Releases page](https://github.com/SolynAcVersion/LyNexus/releases/new)

- Extract and run Lynexus.exe

## 🛠️ Configuration
Lynexus gives you complete control over your AI agents:

**Model Configuration**
```python
# Full parameter customization
mcp_paths=None, 
api_key=None,
api_base=None,
model=None,
system_prompt=None,
temperature=1.0,
max_tokens=None,
top_p=1.0,
stop=None,
stream=False,
presence_penalty=0.0,
frequency_penalty=0.0,
command_start="YLDEXECUTE:",
command_separator="￥|",
max_iterations=15
```

#### Conversation Management
- **Multiple Chat Sessions**: Each with independent AI instances

- **Persistent History**: Chats are saved and can be exported

- **Context Preservation**: AI remembers conversation history

- **Export/Import**: Share your complete chat configurations

## 📦 One-Click Sharing Workflow

#### Export Your Setup
1. Configure your AI agent perfectly

2. Click "Export Configuration"

3. Share the `.json` file on our forum

4. Help others benefit from your work

5. **REMEMBER DONT LEAK YOUR `.confignore` file**

#### Import Others' Setups
1. Browse the community forum

2. Download a configuration that interests you

3. Click "Import Configuration"

4. Instantly use optimized settings

## 🤝 Community & Contribution

#### Join Our Community
- **Forum**: Share configurations and get help

- **Discord**: Real-time discussions

- **GitHub Issues**: Report bugs and request features

- **Showcase**: Share your amazing AI agents

#### Contributing

We welcome contributions! Here's how you can help:

1. **Share Configurations**: Upload your best setups to the forum

2. **Report Bugs**: Help us improve stability

3. **Suggest Features**: What would make Lynexus better?

4. **Improve Documentation**: Help others get started

5. **Code Contributions**: Submit pull requests

Check out our [Contributing Guidelines]() for details.

## 📁 Project Structure
```text
lynexus/
├── main.py              # Application entry point
├── aiclass.py           # Core AI functionality
├── ui/                  # User interface components
│   ├── chat_box.py      # Main chat interface
│   ├── init_dialog.py   # Initialization dialog
│   └── settings_dialog.py # Settings interface
├── config/              # Configuration management
└── utils/               # Utility functions

```

## 🔧 Advanced Usage

#### Custom MCP Servers / Files

1. Place MCP server in `.json` files 

2. Prepare MCP `.py` files  

3. Configure paths in settings

4. AI will automatically discover and use available tools

#### System Integration

- **API Key Management**: Store keys securely

- **Environment Variables**: Use DEEPSEEK_API_KEY or OPENAI_API_KEY

- **Desktop Integration**: Save exports to desktop for easy access




## 📄 License
This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](https://github.com/SolynAcVersion/LyNexus/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments
- **AI Community**: For sharing knowledge and configurations

- **Open Source Projects**: That made this platform possible

- **Contributors**: Everyone who helps improve Lynexus

- **Users**: For trusting us with your AI development needs

<div align="center"> <p> <strong>Built with ❤️ by the AI community, for the AI community</strong> </p> <p> <a href="https://forum.lynexus.ai">Forum</a> • <a href="https://github.com/SolynAcVersion/LyNexus/issues">Issues</a> • <a href="https://github.com/SolynAcVersion/LyNexus/discussions">Discussions</a> </p> </div><p align="center"> <sub>Star ⭐ this repository if you find it useful!</sub> </p>