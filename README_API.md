# LyNexus - AI Assistant with MCP Tools

## Quick Start

### Windows
1. Double-click `start.bat`
2. Wait for both servers to start
3. Browser opens automatically at http://localhost:5173

### Linux/Mac
```bash
python start_dev.py
```

## What's New

### ✨ Modern Web Interface
- Telegram-style chat interface
- Real-time streaming responses
- Dark theme optimized for long sessions
- Markdown support with syntax highlighting
- File drag-and-drop support

### 🔌 Backend API Server
- FastAPI-based REST API
- Server-Sent Events (SSE) for streaming
- CORS-enabled for development
- Auto-reload on code changes

### 📦 Project Structure
```
LyNexus/
├── api_server.py          # Backend API (NEW)
├── start_dev.py          # Quick start script
├── start.bat             # Windows quick start
├── webui/                 # React WebUI (NEW)
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   └── stores/       # State management
│   └── package.json
├── aiclass.py            # AI core (preserved)
├── utils/                # Utilities (preserved)
├── data/                 # User data
└── ui/                   # Qt UI (legacy, can be archived)
```

## First Time Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements-api.txt
   ```

2. **Install WebUI dependencies**
   ```bash
   cd webui
   npm install
   ```

3. **Start the application**
   ```bash
   python start_dev.py
   ```

4. **Configure API Key**
   - Open http://localhost:5173
   - Click "Initialize" or go to Settings
   - Enter your API key:
     - DeepSeek: https://platform.deepseek.com
     - OpenAI: https://platform.openai.com
     - Anthropic: https://console.anthropic.com
   - Save and start chatting!

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Start Backend Only
```bash
python -m uvicorn api_server:app --reload
```

### Start Frontend Only
```bash
cd webui
npm run dev
```

### View API Docs
- Open http://localhost:8000/docs in your browser

## Data Location

All conversations and settings are stored in:
- `data/conversations/{id}/` - Per-conversation data
  - `settings.json` - Conversation settings
  - `.confignore` - API key (not exported)
  - `{id}_ai.json` - Message history
  - `tools/` - MCP tool files

## Migration from Qt UI

Your existing conversations are automatically compatible!

The new WebUI uses the same data structure as the Qt application, so all your existing conversations will appear automatically.

### What Changed

| Component | Qt UI | WebUI |
|-----------|--------|-------|
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

### What Can Be Archived

You can safely remove or archive:
- `ui/chat_box.py` - Replaced by webui/
- `ui/settings_dialog.py` - Replaced by webui/src/components/dialogs/
- `ui/init_dialog.py` - Replaced by webui/src/components/dialogs/
- `ui/splash_screen.py` - Replaced by webui/src/components/dialogs/

**Keep these:**
- `aiclass.py` - AI logic
- `utils/*.py` - Helper functions
- `config/` - Configuration

## Troubleshooting

### Port 8000 Already in Use
```bash
# Windows
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### Port 5173 Already in Use
```bash
# Find and kill the process using port 5173
netstat -ano | findstr :5173
```

### Backend Not Connecting
1. Check if API server is running: http://localhost:8000/docs
2. Check WebUI console (F12) for errors
3. Verify `webui/.env` has correct `VITE_API_BASE_URL`

### "AI Not Initialized" Error
1. Go to Settings (gear icon in sidebar)
2. Enter your API key
3. Click "Save Settings"

## Production Deployment

### Build WebUI for Production
```bash
cd webui
npm run build
```
This creates an optimized `dist/` folder.

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

## Support

For issues or questions:
- Check the console logs (F12) for errors
- Verify API server is running at http://localhost:8000
- Review API docs at http://localhost:8000/docs

## License

MIT
