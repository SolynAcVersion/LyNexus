/**
 * Core API Service
 * Handles all HTTP communication with the backend
 *
 * All APIs are now connected to the real backend
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Message,
  Conversation,
  ConversationSettings,
  APIResponse,
  MCPTool,
} from '../types';
import { ProcessingState } from '../types';

// ============================================================================
// Configuration
// ============================================================================

/**
 * Base URL for the backend API
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Request timeout in milliseconds
 */
const REQUEST_TIMEOUT = 30000;

// ============================================================================
// API Client
// ============================================================================

/**
 * Create and configure axios instance
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor
 */
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized access');
    } else if (error.response?.status === 500) {
      console.error('Server error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Conversation API
// ============================================================================

/**
 * Conversation API endpoints
 */
export const conversationAPI = {
  /**
   * Get all conversations
   *
   * GET /conversations
   */
  async getAll(): Promise<APIResponse<Conversation[]>> {
    try {
      const response = await apiClient.get<Conversation[]>('/conversations');
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch conversations',
      };
    }
  },

  /**
   * Get a single conversation by ID
   *
   * GET /conversations/:id
   */
  async getById(id: string): Promise<APIResponse<Conversation>> {
    try {
      const response = await apiClient.get<Conversation>(`/conversations/${id}`);
      return { success: true, data: response.data };
    } catch (error) {
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Conversation not found',
        };
      }
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch conversation',
      };
    }
  },

  /**
   * Create a new conversation
   *
   * POST /conversations
   */
  async create(name: string): Promise<APIResponse<Conversation>> {
    try {
      const response = await apiClient.post<Conversation>('/conversations', { name });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create conversation',
      };
    }
  },

  /**
   * Update a conversation
   *
   * PUT /conversations/:id
   */
  async update(id: string, data: Partial<Conversation>): Promise<APIResponse<Conversation>> {
    try {
      const response = await apiClient.put<Conversation>(`/conversations/${id}`, data);
      return { success: true, data: response.data };
    } catch (error) {
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Conversation not found',
        };
      }
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update conversation',
      };
    }
  },

  /**
   * Delete a conversation
   *
   * DELETE /conversations/:id
   */
  async delete(id: string): Promise<APIResponse<void>> {
    try {
      await apiClient.delete(`/conversations/${id}`);
      return { success: true };
    } catch (error) {
      if (error.response?.status === 404) {
        return {
          success: false,
          error: 'Conversation not found',
        };
      }
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete conversation',
      };
    }
  },

  /**
   * Clear all messages in a conversation
   *
   * DELETE /conversations/:id/messages
   */
  async clearMessages(id: string): Promise<APIResponse<void>> {
    try {
      await apiClient.delete(`/conversations/${id}/messages`);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to clear messages',
      };
    }
  },
};

// ============================================================================
// Message API
// ============================================================================

/**
 * Message API endpoints
 */
export const messageAPI = {
  /**
   * Get messages for a conversation
   *
   * GET /conversations/:id/messages
   */
  async getByConversation(conversationId: string): Promise<APIResponse<Message[]>> {
    try {
      const response = await apiClient.get<Message[]>(`/conversations/${conversationId}/messages`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch messages',
      };
    }
  },

  /**
   * Send a message to AI
   *
   * POST /conversations/:id/messages
   */
  async send(conversationId: string, content: string): Promise<APIResponse<Message>> {
    try {
      const response = await apiClient.post<Message>(
        `/conversations/${conversationId}/messages`,
        { content }
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send message',
      };
    }
  },

  /**
   * Stream a message response
   *
   * POST /conversations/:id/messages/stream
   * Returns Server-Sent Events (SSE)
   */
  async stream(
    conversationId: string,
    content: string,
    onChunk: (chunk: string) => void,
    onComplete: (message: Message) => void,
    onError: (error: string) => void
  ): Promise<void> {
    try {
      console.log('[API Stream] Starting stream for conversation:', conversationId);
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let fullResponse = '';

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        console.log('[API Stream] Received chunk:', chunk);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix
            console.log('[API Stream] SSE data:', data);
            try {
              const event = JSON.parse(data);
              console.log('[API Stream] Parsed event:', event);
              if (event.type === 'user_message') {
                // User message received
                console.log('[API Stream] User message received');
              } else if (event.type === 'chunk') {
                // Streaming chunk
                console.log('[API Stream] Chunk received:', event.content);
                onChunk(event.content || '');
                fullResponse += event.content || '';
              } else if (event.type === 'complete') {
                // Streaming complete
                console.log('[API Stream] Stream complete, message:', event.message);
                onComplete(event.message);
              } else if (event.type === 'error') {
                // Error occurred
                console.error('[API Stream] Error:', event.error);
                onError(event.error || 'Unknown error');
              }
            } catch (e) {
              console.error('[API Stream] Failed to parse SSE data:', e, 'data:', data);
            }
          }
        }
      }
    } catch (error) {
      console.error('[API Stream] Streaming error:', error);
      onError(error instanceof Error ? error.message : 'Streaming failed');
    }
  },

  /**
   * Stop current streaming response
   *
   * POST /conversations/:id/messages/stop
   */
  async stop(conversationId: string): Promise<APIResponse<void>> {
    try {
      await apiClient.post(`/conversations/${conversationId}/messages/stop`);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to stop streaming',
      };
    }
  },
};

// ============================================================================
// Settings API
// ============================================================================

/**
 * Settings API endpoints
 */
export const settingsAPI = {
  /**
   * Get conversation settings
   *
   * GET /conversations/:id/settings
   */
  async get(conversationId: string): Promise<APIResponse<ConversationSettings>> {
    try {
      const response = await apiClient.get<ConversationSettings>(
        `/conversations/${conversationId}/settings`
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch settings',
      };
    }
  },

  /**
   * Update conversation settings
   *
   * PUT /conversations/:id/settings
   */
  async update(
    conversationId: string,
    settings: Partial<ConversationSettings>
  ): Promise<APIResponse<ConversationSettings>> {
    try {
      const response = await apiClient.put<ConversationSettings>(
        `/conversations/${conversationId}/settings`,
        settings
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update settings',
      };
    }
  },

  /**
   * Validate API key
   *
   * POST /settings/validate-key
   */
  async validateApiKey(apiKey: string, apiBase: string): Promise<APIResponse<boolean>> {
    try {
      const response = await apiClient.post<{ valid: boolean }>('/settings/validate-key', {
        apiKey,
        apiBase,
      });
      return { success: true, data: response.data.valid };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to validate API key',
      };
    }
  },
};

// ============================================================================
// MCP Tools API
// ============================================================================

/**
 * MCP Tools API endpoints
 */
export const mcpAPI = {
  /**
   * Get available MCP tools
   *
   * GET /mcp/tools?conversation=:id
   */
  async getTools(conversationId: string): Promise<APIResponse<MCPTool[]>> {
    try {
      const response = await apiClient.get<MCPTool[]>(`/mcp/tools?conversation=${conversationId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch MCP tools',
      };
    }
  },

  /**
   * Add MCP tool to conversation
   *
   * POST /conversations/:id/mcp-tools
   */
  async addTool(conversationId: string, filePath: string): Promise<APIResponse<void>> {
    try {
      const formData = new FormData();
      formData.append('filePath', filePath);

      await apiClient.post(`/conversations/${conversationId}/mcp-tools`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to add MCP tool',
      };
    }
  },

  /**
   * Upload MCP tool files to conversation's tools directory
   *
   * POST /conversations/:id/mcp-tools/upload
   */
  async uploadTools(
    conversationId: string,
    files: File[]
  ): Promise<APIResponse<{ uploadedCount: number; paths: string[] }>> {
    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await apiClient.post<{ uploadedCount: number; paths: string[] }>(
        `/conversations/${conversationId}/mcp-tools/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to upload MCP tools',
      };
    }
  },

  /**
   * Toggle MCP tool enabled state
   *
   * PUT /mcp/tools/:toolName/toggle
   */
  async toggleTool(
    conversationId: string,
    toolName: string,
    enabled: boolean
  ): Promise<APIResponse<void>> {
    try {
      await apiClient.put(`/mcp/tools/${toolName}/toggle`, {
        conversationId,
        enabled,
      });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to toggle tool',
      };
    }
  },
};

// ============================================================================
// Export/Import API
// ============================================================================

/**
 * Export/Import API endpoints
 */
export const transferAPI = {
  /**
   * Export conversation configuration
   *
   * POST /conversations/:id/export
   */
  async exportConfig(conversationId: string): Promise<APIResponse<Blob>> {
    try {
      const response = await apiClient.post<Blob>(
        `/conversations/${conversationId}/export`,
        {},
        { responseType: 'blob' }
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to export configuration',
      };
    }
  },

  /**
   * Export chat history
   *
   * GET /conversations/:id/export/history
   */
  async exportHistory(conversationId: string): Promise<APIResponse<Blob>> {
    try {
      const response = await apiClient.get<Blob>(
        `/conversations/${conversationId}/export/history`,
        { responseType: 'blob' }
      );
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to export history',
      };
    }
  },

  /**
   * Import conversation configuration
   *
   * POST /conversations/import
   */
  async importConfig(file: File): Promise<APIResponse<Conversation>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/conversations/import`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        return {
          success: false,
          error: errorText || 'Failed to import configuration',
        };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to import configuration',
      };
    }
  },
};

// ============================================================================
// System API
// ============================================================================

/**
 * System information and status endpoints
 */
export const systemAPI = {
  /**
   * Get system status
   *
   * GET /system/status
   */
  async getStatus(): Promise<APIResponse<{
    connected: boolean;
    version: string;
  }>> {
    try {
      const response = await apiClient.get('/system/status');
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch system status',
      };
    }
  },
};

// ============================================================================
// MCP Tools API
// ============================================================================

/**
 * MCP Tools endpoints
 */
export const mcp = {
  /**
   * Get MCP tools for a conversation
   *
   * GET /api/mcp/tools?conversation={conversationId}
   */
  async getTools(conversationId: string): Promise<APIResponse<Array<{
    name: string;
    description: string;
    enabled: boolean;
    server?: string;
  }>>> {
    try {
      const response = await apiClient.get(`/mcp/tools?conversation=${conversationId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to fetch MCP tools',
      };
    }
  },

  /**
   * Toggle MCP tool enabled state
   *
   * PUT /api/mcp/tools/{toolName}/toggle?conversationId={conversationId}&enabled={true/false}
   */
  async toggleTool(conversationId: string, toolName: string, enabled: boolean): Promise<APIResponse<{ success: boolean }>> {
    try {
      const params = new URLSearchParams({
        conversationId,
        enabled: enabled.toString(),
      });
      const response = await apiClient.put(`/mcp/tools/${toolName}/toggle?${params}`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to toggle MCP tool',
      };
    }
  },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Handle API error consistently
 */
export function handleAPIError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}

/**
 * Export all APIs as a single object
 */
export const api = {
  conversation: conversationAPI,
  message: messageAPI,
  settings: settingsAPI,
  mcp: mcpAPI,
  transfer: transferAPI,
  system: systemAPI,
};

export default api;
