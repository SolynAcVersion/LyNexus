/**
 * Core type definitions for the application
 */

// ============================================================================
// Message Types
// ============================================================================

/**
 * Message bubble type enumeration
 */
export enum MessageType {
  USER = 'USER',
  AI = 'AI',
  COMMAND_REQUEST = 'COMMAND_REQUEST',
  COMMAND_RESULT = 'COMMAND_RESULT',
  FINAL_SUMMARY = 'FINAL_SUMMARY',
  ERROR = 'ERROR',
  INFO = 'INFO',
}

/**
 * Message source enumeration
 */
export enum MessageSource {
  USER = 'USER',
  AI = 'AI',
  SYSTEM = 'SYSTEM',
}

/**
 * Base message interface
 */
export interface Message {
  id: string;
  content: string;
  type: MessageType;
  source: MessageSource;
  timestamp: string;
  conversationId: string;
  isStreaming?: boolean;
}

/**
 * User message
 */
export interface UserMessage extends Message {
  type: MessageType.USER;
  source: MessageSource.USER;
}

/**
 * AI response message
 */
export interface AIMessage extends Message {
  type: MessageType.AI;
  source: MessageSource.AI;
}

/**
 * Command request message
 */
export interface CommandRequestMessage extends Message {
  type: MessageType.COMMAND_REQUEST;
  command?: string;
}

/**
 * Command result message
 */
export interface CommandResultMessage extends Message {
  type: MessageType.COMMAND_RESULT;
  exitCode?: number;
}

// ============================================================================
// Conversation Types
// ============================================================================

/**
 * Conversation metadata
 */
export interface Conversation {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessage?: string;
  settings?: ConversationSettings;
}

/**
 * Conversation settings
 */
export interface ConversationSettings {
  apiKey?: string;
  apiBase: string;
  model: string;
  temperature: number;
  maxTokens?: number;
  topP: number;
  presencePenalty: number;
  frequencyPenalty: number;
  stream: boolean;
  commandStart: string;
  commandSeparator: string;
  maxIterations: number;
  mcpPaths: string[];
  enabledMcpTools: string[];
  systemPrompt: string;
}

// ============================================================================
// API Configuration Types
// ============================================================================

/**
 * API provider configuration
 */
export interface APIProvider {
  name: string;
  apiBase: string;
  models: string[];
}

/**
 * Available API providers
 */
export const API_PROVIDERS: Record<string, APIProvider> = {
  deepseek: {
    name: 'DeepSeek',
    apiBase: 'https://api.deepseek.com',
    models: ['deepseek-chat', 'deepseek-reasoner'],
  },
  openai: {
    name: 'OpenAI',
    apiBase: 'https://api.openai.com/v1',
    models: ['gpt-4-turbo', 'gpt-4o', 'gpt-3.5-turbo'],
  },
  anthropic: {
    name: 'Anthropic',
    apiBase: 'https://api.anthropic.com',
    models: ['claude-opus-4.5', 'claude-sonnet-4.5', 'claude-haiku-4.5'],
  },
  glm: {
    name: 'GLM',
    apiBase: 'https://open.bigmodel.cn/api/paas/v4',
    models: ['glm-4.7'],
  },
  local: {
    name: 'Local',
    apiBase: 'http://localhost:11434',
    models: ['llama2', 'mistral'],
  },
  custom: {
    name: 'Custom',
    apiBase: '',
    models: [],
  },
};

// ============================================================================
// Processing State Types
// ============================================================================

/**
 * Processing state enumeration
 */
export enum ProcessingState {
  IDLE = 'IDLE',
  STREAMING = 'STREAMING',
  EXECUTING_COMMAND = 'EXECUTING_COMMAND',
  AWAITING_SUMMARY = 'AWAITING_SUMMARY',
  ERROR = 'ERROR',
  LOADING = 'LOADING',
}

// ============================================================================
// MCP Tools Types
// ============================================================================

/**
 * MCP tool information
 */
export interface MCPTool {
  name: string;
  description: string;
  enabled: boolean;
  server: string;
}

/**
 * MCP tools list response
 */
export interface MCPToolsResponse {
  tools: MCPTool[];
  total: number;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Standard API response wrapper
 */
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// ============================================================================
// Export/Import Types
// ============================================================================

/**
 * Export configuration format
 */
export interface ExportConfig {
  conversationId: string;
  settings: ConversationSettings;
  tools?: string[];
  exportedAt: string;
}

/**
 * Import configuration format
 */
export interface ImportConfig {
  settings: ConversationSettings;
  tools?: { name: string; content: string }[];
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Application UI state
 */
export interface UIState {
  currentConversationId: string | null;
  processingState: ProcessingState;
  isSidebarOpen: boolean;
  theme: 'dark' | 'light';
  language: string;
}

// ============================================================================
// Electron Window API Types
// ============================================================================

/**
 * Window information
 */
export interface WindowInfo {
  isMaximized: boolean;
  isFullscreen: boolean;
  bounds: {
    width: number;
    height: number;
    x: number;
    y: number;
  };
}

/**
 * Electron API exposed via context bridge
 */
export interface ElectronAPI {
  window: {
    minimize: () => Promise<void>;
    maximize: () => Promise<void>;
    close: () => Promise<void>;
    getInfo: () => Promise<WindowInfo>;
  };
  system: {
    getPlatform: () => Promise<string>;
    getVersion: () => Promise<string>;
  };
}

// ============================================================================
// File Types
// ============================================================================

/**
 * File drag-drop item
 */
export interface DroppedFile {
  name: string;
  path: string;
  size: number;
  type: string;
}

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Form validation error
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Form validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}
