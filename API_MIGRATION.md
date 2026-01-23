# LyNexus Backend API Migration Guide

## Overview

The backend has been migrated from a Qt-based desktop application to a FastAPI web service. This allows the WebUI to interact with the AI assistant core logic.

## Architecture

```
LyNexus/
├── api_server.py          # FastAPI backend (NEW)
├── aiclass.py              # AI core logic (preserved, Qt-independent)
├── utils/                   # Helper modules
│   ├── config_manager.py
│   ├── ai_history_manager.py
│   ├── chat_data_manager.py
│   └── ...
├── data/                    # User data directory
│   └── {chat_name}/         # Per-conversation storage
│       ├── settings.json
│       ├── .confignore (API key)
│       ├── {chat_name}_ai.json (AI conversation history)
│       ├── chat_his.pickle (UI display history)
│       └── tools/
└── webui/                   # React WebUI
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements-api.txt
```

### 2. Install WebUI Dependencies

```bash
cd webui
npm install
```

## Running the Application

### Quick Start (Both Servers)

```bash
python start_dev.py
```

This will start both:
- API Server at http://127.0.0.1:8000
- WebUI at http://localhost:5173

### Manual Start

**Terminal 1 - API Server:**
```bash
python -m uvicorn api_server:app --reload
```

**Terminal 2 - WebUI:**
```bash
cd webui
npm run dev
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# AI Provider (optional, will use defaults if not set)
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
```

### Conversation Settings

Each conversation stores its settings in:
- `data/{chat_name}/settings.json` - General settings
- `data/{chat_name}/.confignore` - API key (not exported)

## Data Migration

Existing conversations from the Qt application are automatically compatible. They're stored in:
- `data/{chat_name}/` - Already using this structure!

## Development

### Adding New API Endpoints

1. Define Pydantic model in `api_server.py`
2. Create route function with `@app.get/post/put/delete`
3. Implement business logic
4. Return response

Example:
```python
@app.get("/conversations")
async def get_conversations():
    conversations = load_all_conversations()
    return conversations
```

### Testing

```bash
# Test API
curl http://localhost:8000/conversations

# Stream test
curl -N http://localhost:8000/api/conversations/{id}/messages/stream \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello"}'
```

## Migration from Qt UI

The Qt UI code in `ui/chat_box.py` is NOT used by the WebUI. All UI logic has been rewritten in React (`webui/src/`).

### Key Changes

1. **Removed**: Qt widgets, signals/slots, event loops
2. **Preserved**: AI core logic (`aiclass.py`), data managers, utilities
3. **Added**: FastAPI routes, SSE streaming, REST endpoints

### Qt Code Removal

You can safely remove or archive:
- `ui/chat_box.py` - Replaced by webui/src/
- `ui/settings_dialog.py` - Replaced by webui/src/components/dialogs/
- `ui/init_dialog.py` - Replaced by webui/src/components/dialogs/
- `ui/splash_screen.py` - Replaced by webui/src/components/dialogs/

**DO NOT REMOVE**:
- `aiclass.py` - Core AI logic
- `utils/*.py` - Helper functions
- `config/` - Configuration files

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### CORS Errors

Ensure the API allows origins from `webui/.env`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### AI Not Initialized

1. Open WebUI
2. Select a conversation
3. Click "Initialize" or go to Settings
4. Enter API key and configuration
5. Save

## Production Deployment

### Build WebUI

```bash
cd webui
npm run build
```

### Run with Gunicorn

```bash
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (Optional)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt
COPY . .
CMD ["gunicorn", "api_server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

## API Reference

See [API Documentation](./API_DOCUMENTATION.md) for complete endpoint reference.
