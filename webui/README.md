# LyNexus WebUI

A modern, Telegram-style web interface for the LyNexus AI Assistant. Built with React, TypeScript, Vite, and Tailwind CSS. Connects to the Python FastAPI backend.

## Features

- 🚀 **Modern UI**: Telegram-inspired design with smooth animations
- 💬 **Rich Chat**: Support for multiple message types with Markdown rendering
- 🎨 **Dark Theme**: Beautiful dark theme optimized for long usage sessions
- 🔧 **Settings**: Comprehensive configuration dialogs
- 📁 **File Drag-Drop**: Drag and drop files directly into chat
- ⌨️ **Keyboard Shortcuts**: Full keyboard navigation support
- 🌐 **Multi-language**: i18n support for English and Chinese
- 🔌 **FastAPI Backend**: RESTful API with SSE streaming support

## Project Structure

```
webui/
├── electron/              # Electron main process files
│   ├── main.ts           # Main process entry point
│   └── preload.ts        # Preload script for context bridge
├── src/
│   ├── components/       # React components
│   │   ├── common/       # Reusable UI components
│   │   ├── chat/         # Chat-related components
│   │   ├── sidebar/      # Sidebar components
│   │   └── dialogs/      # Modal dialogs
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API service layer
│   ├── stores/           # State management (Zustand)
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Root component
│   ├── main.tsx          # React entry point
│   └── index.css         # Global styles
├── package.json
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── electron-builder.toml # Electron builder configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Python 3.8+ (for backend)

### Installation

```bash
# Install dependencies
npm install
```

### Development

**Option 1: Quick Start (Recommended)**

From the project root:
```bash
# Windows
start.bat

# Linux/Mac
python start_dev.py
```

This will start both:
- API Server at http://127.0.0.1:8000
- WebUI at http://localhost:5173

**Option 2: Manual Start**

Terminal 1 - API Server:
```bash
pip install -r requirements-api.txt
python -m uvicorn api_server:app --reload
```

Terminal 2 - WebUI:
```bash
cd webui
npm install
npm run dev
```

### Connecting to Backend

The WebUI is configured to connect to the backend API at `http://localhost:8000/api` by default.

To verify the connection:
1. Check API status: http://localhost:8000/api/system/status
2. View API docs: http://localhost:8000/docs

### First Time Setup

1. Start the application (see above)
2. Open http://localhost:5173 in your browser
3. Click "Initialize" or go to Settings
4. Enter your API key:
   - DeepSeek: Get from https://platform.deepseek.com
   - OpenAI: Get from https://platform.openai.com
   - Or select from preset providers
5. Click "Save Settings"
6. Start chatting!

### Build

```bash
# Build for web
npm run build

# Build Electron app (optional, for desktop app)
npm run electron:build
```

## Backend API

The WebUI connects to a FastAPI backend (`api_server.py`) that provides:

- **Conversation Management**: CRUD operations for conversations
- **Messaging**: Send/receive messages with SSE streaming
- **Settings**: Configure API keys, model parameters, MCP tools
- **Export/Import**: Save and load conversation configurations

See [API Documentation](../API_DOCUMENTATION.md) for complete API reference.

## Component Documentation

### Common Components

#### Button
Reusable button component with multiple variants.

```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click me
</Button>
```

#### Modal
Dialog component with backdrop and animations.

```tsx
<Modal isOpen={isOpen} onClose={handleClose} title="Title">
  Content
</Modal>
```

### Chat Components

#### MessageBubble
Telegram-style message bubble with Markdown support.

```tsx
<MessageBubble message={message} isStreaming={false} />
```

#### MessageList
Scrollable message container with auto-scroll.

```tsx
<MessageList
  messages={messages}
  streamingMessage={streaming}
  isProcessing={isProcessing}
/>
```

#### MessageInput
Input field with file drag-drop support.

```tsx
<MessageInput
  onSend={handleSend}
  onFileDrop={handleFileDrop}
  showStop={isProcessing}
/>
```

### Sidebar Components

#### ConversationList
Sidebar with conversation list and action buttons.

```tsx
<ConversationList className="w-80" />
```

#### ChatArea
Main chat area with header and messages.

```tsx
<ChatArea className="flex-1" />
```

## State Management

The app uses Zustand for state management. Main store is located in `src/stores/useAppStore.ts`.

```tsx
import { useAppStore } from '@stores/useAppStore';

function MyComponent() {
  const { conversations, currentConversation, sendMessage } = useAppStore();

  // ...
}
```

## API Service Layer

All backend communication is handled through the API service layer in `src/services/api.ts`.

```tsx
import { api } from '@services/api';

// Get all conversations
const response = await api.conversation.getAll();

// Send a message
await api.message.send(conversationId, content);
```

## Styling

The app uses Tailwind CSS with a custom dark theme. Colors and styles are defined in `tailwind.config.js`.

```tsx
<div className="bg-dark-bg text-dark-text">
  Content
</div>
```

## Backend Integration

All API endpoints are defined in `src/services/api.ts`. Replace mock implementations with actual API calls.

Example:
```tsx
// TODO: Replace with actual API call
// const response = await apiClient.get('/conversations');
// return { success: true, data: response.data };

// Mock implementation
return { success: true, data: [] };
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
