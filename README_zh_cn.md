# LyNexus - 社区驱动的AI智能体平台

<p align="center">
  <img src="https://img.shields.io/badge/版本-0.46-blue" alt="版本">
  <img src="https://img.shields.io/badge/许可证-MPL%202.0-green" alt="许可证">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
  <img src="https://img.shields.io/badge/平台-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="平台">
  <img src="https://img.shields.io/badge/WebUI-React%202024-blue" alt="WebUI">
</p>

<div align="center">
  <strong>用社区驱动的智能，赋能您的AI开发</strong>
</div>

<div align="center">
  <a href="README.md">English</a>
</div>

## 🌟 LyNexus是什么？

LyNexus是一个**社区驱动的AI智能体平台**，使开发者能够创建、定制和分享具有可配置提示词、工具和行为参数的智能体。该平台以灵活性和协作为核心理念打造，将AI开发转变为共享的体验。

🎯 **核心理念**：一次创造，处处分享。向他人学习，加速构建。

## ✨ 功能特性

### 🤖 **灵活的AI配置**
- **模型无关**：连接多种AI模型（DeepSeek、OpenAI、Anthropic等）
- **参数自定义**：精确调节温度、tokens数、惩罚项等参数
- **自定义系统提示**：根据需要量身定制AI行为
- **MCP集成**：无缝集成模型上下文协议工具

### 🌐 **双界面架构**
- **现代化WebUI**：基于 React + Vite + Tailwind CSS 构建
  - Telegram风格的聊天界面
  - 实时流式响应
  - 暗色调主题，适合长时间会话
  - 文件拖拽支持
- **桌面应用**：基于 PySide6/Qt 的原生体验
  - Windows 11风格UI设计
  - 多对话管理
  - 导出聊天为TXT、JSON或Markdown格式

### 🔄 **社区驱动的生态系统**
- **一键导出**：打包整个配置用于分享
- **一键导入**：立即使用他人优化的配置
- **配置分享**：分享和发现配置
- **站在巨人肩膀上**：基于经过社区测试的配置构建

### ⚡ **高级工具**
- **命令执行**：AI可以执行shell命令（可配置）
- **工具集成**：通过MCP连接各种API和服务
- **执行控制**：随时停止长时间运行的操作
- **历史管理**：保留和加载对话历史

## 🚀 快速开始

### 方式一：现代化WebUI（推荐）

#### Windows
1. 双击 `start.bat`
2. 等待两个服务器启动
3. 浏览器会自动打开 http://localhost:5173

#### Linux/Mac
```bash
# 安装依赖
pip install -r requirements-api.txt
cd webui && npm install

# 启动应用
cd ..
python start_dev.py
```

### 方式二：桌面应用

#### Windows
```bash
python main.py
```

#### Linux/Mac
```bash
python3 main.py
```

## 📦 项目结构

```
LyNexus/
├── main.py                 # 桌面应用入口点 (PySide6)
├── api_server.py           # WebUI 的 FastAPI 后端
├── start_dev.py            # WebUI 快速启动脚本
├── start.bat               # Windows 快速启动脚本
├── aiclass.py              # 核心AI功能
├── mcp_utils.py            # MCP 协议工具
│
├── webui/                  # 现代化 WebUI (React + Vite)
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── services/       # API 客户端和服务
│   │   └── stores/         # 状态管理 (Zustand)
│   ├── electron/           # Electron 桌面包装器
│   ├── package.json
│   └── vite.config.ts
│
├── ui/                     # PySide6 桌面UI
│   ├── chat_box.py         # 主聊天界面
│   ├── init_dialog.py      # 初始化对话框
│   ├── settings_dialog.py  # 设置界面
│   └── mcp_tools_widget.py # MCP 工具显示
│
├── tools/                  # MCP 工具实现
│   ├── files.py            # 文件操作
│   ├── network.py          # 网络请求
│   ├── ocr.py              # OCR 功能
│   └── osmanager.py        # 操作系统操作
│
├── utils/                  # 工具函数
│   ├── config_manager.py   # 配置管理
│   ├── chat_data_manager.py # 聊天数据处理
│   ├── stream_processor.py # 流处理
│   └── markdown_renderer.py # Markdown 渲染
│
├── config/                 # 配置文件
├── data/                   # 用户数据目录
│   └── conversations/      # 对话存储
├── conversations/          # 旧版对话存储
├── docs/                   # 文档
│   ├── README.md           # 英文文档
│   └── zh-cn/README.md     # 中文文档
│
├── requirements.txt        # Python 依赖
├── requirements-api.txt    # API 服务器依赖
├── pyproject.toml          # 项目配置
└── uv.lock                 # 依赖锁定文件
```

## 🔧 首次设置

### 1. 安装 Python 依赖
```bash
pip install -r requirements-api.txt
```

### 2. 安装 WebUI 依赖
```bash
cd webui
npm install
cd ..
```

### 3. 配置 API 密钥
- 打开应用
- 点击"初始化"或进入设置
- 输入您的 API 密钥：
  - **DeepSeek**: https://platform.deepseek.com
  - **OpenAI**: https://platform.openai.com
  - **Anthropic**: https://console.anthropic.com
- 保存并开始聊天！

## 📖 文档

详细的安装、配置和使用说明：

- **[文档网站](https://solynacversion.github.io/LyNexus)**
- **[API 文档](README_API.md)** - 后端API参考
- **[WebUI 指南](docs/zh-cn/README.md)** - WebUI 专项文档

文档包含：
- 安装和设置
- 配置选项
- 使用指南
- 分享工作流
- 高级功能
- API 参考
- 等等！

## 🔌 API 文档

API 服务器运行后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ 开发

### 仅启动后端
```bash
python -m uvicorn api_server:app --reload
```

### 仅启动前端
```bash
cd webui
npm run dev
```

### 构建生产版 WebUI
```bash
cd webui
npm run build
```

### 构建 Electron 桌面应用
```bash
cd webui
npm run electron:build
```

## 📁 数据位置

所有对话和设置存储在：
- `data/conversations/{id}/` - 每个对话的数据
  - `settings.json` - 对话设置
  - `.confignore` - API密钥（不导出）
  - `{id}_ai.json` - 消息历史
  - `tools/` - MCP 工具文件

## 🔄 从 Qt UI 迁移

您现有的对话自动兼容！

新的 WebUI 使用与 Qt 应用相同的数据结构，因此所有现有对话都会自动显示。

### 变化对比

| 组件 | Qt UI | WebUI |
|------|-------|-------|
| **界面** | PySide6/Qt | React + Vite |
| **后端** | 嵌入在 Qt 中 | FastAPI |
| **样式** | QSS | Tailwind CSS |
| **状态** | Qt 信号 | Zustand |
| **通信** | 直接调用 | REST API |

### 保持不变

- ✅ AI 核心逻辑 (`aiclass.py`)
- ✅ 数据管理器 (`utils/`)
- ✅ 对话存储结构
- ✅ MCP 工具集成

## 🤝 社区与贡献

#### 加入社区
- **GitHub Issues**: 报告错误和请求功能
- **GitHub Discussions**: 分享您的优秀AI智能体
- **文档**: [https://solynacversion.github.io/LyNexus](https://solynacversion.github.io/LyNexus)

#### 贡献方式

欢迎贡献！您可以通过以下方式帮助我们：

1. **分享配置**：上传您的最佳配置
2. **报告错误**：帮助我们提高稳定性
3. **建议功能**：什么能让 LyNexus 变得更好？
4. **改进文档**：帮助他人快速上手
5. **代码贡献**：提交 Pull Request

查看[贡献指南](CONTRIBUTING.md)了解详情。

## 🐛 故障排除

### 端口 8000 已被占用
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### 端口 5173 已被占用
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5173 | xargs kill -9
```

### 后端无法连接
1. 检查 API 服务器是否运行：http://localhost:8000/docs
2. 检查 WebUI 控制台（F12）是否有错误
3. 验证 `webui/.env` 中有正确的 `VITE_API_BASE_URL`

### "AI 未初始化" 错误
1. 进入设置（侧边栏中的齿轮图标）
2. 输入您的 API 密钥
3. 点击"保存设置"

## 🚀 生产部署

### 使用生产服务器运行
```bash
# 安装 gunicorn
pip install gunicorn

# 使用4个worker运行
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 使用 Nginx 服务 WebUI
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # API 服务器
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebUI 静态文件
    location / {
        root /path/to/LyNexus/webui/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 📄 许可证

本项目采用 Mozilla Public License 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- **AI社区**：感谢分享知识和配置的社区
- **开源项目**：使本平台成为可能
- **贡献者**：每位帮助改进 LyNexus 的人
- **用户**：感谢信任我们的AI开发需求

---

<div align="center">
  <p><strong>由AI社区🫶为AI社区打造</strong></p>
  <p>
    <a href="https://solynacversion.github.io/LyNexus">文档</a> •
    <a href="https://github.com/SolynAcVersion/LyNexus/issues">问题反馈</a> •
    <a href="https://github.com/SolynAcVersion/LyNexus/discussions">讨论区</a>
  </p>
  <p><i>如果觉得这个项目有用，请给它一个⭐吧！</i></p>
</div>
