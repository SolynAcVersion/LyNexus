/**
 * Main Application Store
 * Manages global application state using Zustand
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  ProcessingState,
} from '../types';
import type {
  Conversation,
  Message,
  ConversationSettings,
  UIState,
} from '../types';
import { api } from '../services/api';

// ============================================================================
// Store State Interface
// ============================================================================

interface AppState extends UIState {
  // Data
  conversations: Conversation[];
  messages: Record<string, Message[]>;
  currentConversation: Conversation | null;

  // UI State (Per-conversation)
  processingStates: Record<string, ProcessingState>;
  streamingMessages: Record<string, Message>;
  showSettings: boolean;
  showInitDialog: boolean;
  showToolsList: boolean;

  // Actions
  setCurrentConversation: (conversation: Conversation | null) => void;
  getProcessingState: (conversationId: string) => ProcessingState;
  setProcessingState: (conversationId: string, state: ProcessingState) => void;
  addConversation: (conversation: Conversation) => void;
  removeConversation: (id: string) => void;
  updateConversation: (id: string, data: Partial<Conversation>) => void;

  // Message actions
  setMessages: (conversationId: string, messages: Message[]) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateStreamingMessage: (content: string) => void;
  finalizeStreamingMessage: (message: Message) => void;
  clearMessages: (conversationId: string) => void;

  // UI actions
  toggleSidebar: () => void;
  openSettings: () => void;
  closeSettings: () => void;
  openInitDialog: () => void;
  closeInitDialog: () => void;
  openToolsList: () => void;
  closeToolsList: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  setLanguage: (language: string) => void;

  // Async actions
  loadConversations: () => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
  createConversation: (name: string) => Promise<Conversation | null>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  stopStreaming: () => Promise<void>;
}

// ============================================================================
// Create Store
// ============================================================================

/**
 * Main application store
 */
export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // ====================================================================
        // Initial State
        // ====================================================================

        conversations: [],
        messages: {},
        currentConversation: null,
        currentConversationId: null,
        processingStates: {},
        streamingMessages: {},
        processingState: ProcessingState.IDLE,
        isSidebarOpen: true,
        showSettings: false,
        showInitDialog: false,
        showToolsList: false,
        theme: 'dark',
        language: 'en',

        // ====================================================================
        // Conversation Actions
        // ====================================================================

        /**
         * Set the current active conversation
         */
        setCurrentConversation: (conversation) => {
          set({
            currentConversation: conversation,
            currentConversationId: conversation?.id || null,
          });
        },

        /**
         * Get processing state for a conversation
         */
        getProcessingState: (conversationId) => {
          const state = get();
          return state.processingStates[conversationId] || ProcessingState.IDLE;
        },

        /**
         * Update processing state for a conversation
         */
        setProcessingState: (conversationId, newState) => {
          set((state) => ({
            processingStates: {
              ...state.processingStates,
              [conversationId]: newState,
            },
          }));
        },

        /**
         * Add a new conversation to the list
         */
        addConversation: (conversation) => {
          set((state) => ({
            conversations: [...state.conversations, conversation],
          }));
        },

        /**
         * Remove a conversation from the list
         */
        removeConversation: (id) => {
          set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== id),
            messages: { ...state.messages, [id]: [] },
            currentConversation:
              state.currentConversation?.id === id ? null : state.currentConversation,
          }));
        },

        /**
         * Update conversation data
         */
        updateConversation: (id, data) => {
          set((state) => ({
            conversations: state.conversations.map((c) =>
              c.id === id ? { ...c, ...data } : c
            ),
            currentConversation:
              state.currentConversation?.id === id
                ? { ...state.currentConversation, ...data }
                : state.currentConversation,
          }));
        },

        // ====================================================================
        // Message Actions
        // ====================================================================

        /**
         * Set messages for a conversation
         */
        setMessages: (conversationId, messages) => {
          set((state) => ({
            messages: { ...state.messages, [conversationId]: messages },
          }));
        },

        /**
         * Add a message to a conversation
         */
        addMessage: (conversationId, message) => {
          set((state) => {
            const currentMessages = state.messages[conversationId] || [];
            return {
              messages: {
                ...state.messages,
                [conversationId]: [...currentMessages, message],
              },
            };
          });
        },

        /**
         * Update streaming message content
         */
        updateStreamingMessage: (content) => {
          console.log('[Store] updateStreamingMessage called with content:', content);
          set((state) => {
            const conversationId = state.currentConversation?.id;
            if (!conversationId || !state.streamingMessages[conversationId]) {
              console.warn('[Store] No streamingMessage to update!');
              return state;
            }
            const currentContent = state.streamingMessages[conversationId].content || '';
            console.log('[Store] Current streamingMessage before update:', state.streamingMessages[conversationId]);
            const updated = { ...state.streamingMessages[conversationId], content: currentContent + content };
            console.log('[Store] Updated streamingMessage:', updated);
            return {
              streamingMessages: {
                ...state.streamingMessages,
                [conversationId]: updated,
              },
            };
          });
        },

        /**
         * Finalize streaming message
         */
        finalizeStreamingMessage: (message) => {
          set((state) => {
            const conversationId = message.conversationId;
            const currentMessages = state.messages[conversationId] || [];
            // Remove the streaming message key for this conversation
            const { [conversationId]: removed, ...remainingMessages } = state.streamingMessages;
            return {
              messages: {
                ...state.messages,
                [conversationId]: [...currentMessages, message],
              },
              streamingMessages: remainingMessages,
            };
          });
        },

        /**
         * Clear all messages for a conversation
         */
        clearMessages: (conversationId) => {
          set((state) => ({
            messages: { ...state.messages, [conversationId]: [] },
          }));
        },

        // ====================================================================
        // UI Actions
        // ====================================================================

        /**
         * Toggle sidebar visibility
         */
        toggleSidebar: () => {
          set((state) => ({ isSidebarOpen: !state.isSidebarOpen }));
        },

        /**
         * Open settings dialog
         */
        openSettings: () => {
          set({ showSettings: true });
        },

        /**
         * Close settings dialog
         */
        closeSettings: () => {
          set({ showSettings: false });
        },

        /**
         * Open init dialog
         */
        openInitDialog: () => {
          set({ showInitDialog: true });
        },

        /**
         * Close init dialog
         */
        closeInitDialog: () => {
          set({ showInitDialog: false });
        },

        /**
         * Open tools list
         */
        openToolsList: () => {
          set({ showToolsList: true });
        },

        /**
         * Close tools list
         */
        closeToolsList: () => {
          set({ showToolsList: false });
        },

        /**
         * Set application theme
         */
        setTheme: (theme) => {
          set({ theme });
        },

        /**
         * Set application language
         */
        setLanguage: (language) => {
          set({ language });
        },

        // ====================================================================
        // Async Actions
        // ====================================================================

        /**
         * Load all conversations from backend
         */
        loadConversations: async () => {
          const response = await api.conversation.getAll();
          if (response.success && response.data) {
            set({ conversations: response.data });
          }
        },

        /**
         * Load messages for a conversation
         * Always uses backend timestamps directly without caching
         */
        loadMessages: async (conversationId) => {
          const response = await api.message.getByConversation(conversationId);
          if (response.success && response.data) {
            set((state) => ({
              messages: {
                ...state.messages,
                [conversationId]: response.data,
              },
            }));
          }
        },

        /**
         * Create a new conversation
         */
        createConversation: async (name) => {
          const response = await api.conversation.create(name);
          if (response.success && response.data) {
            get().addConversation(response.data);
            return response.data;
          }
          return null;
        },

        /**
         * Delete a conversation
         */
        deleteConversation: async (id) => {
          const response = await api.conversation.delete(id);
          if (response.success) {
            get().removeConversation(id);
          }
        },

        /**
         * Send a message to AI
         */
        sendMessage: async (content) => {
          console.log('[Store] sendMessage called with content:', content);
          const {
            currentConversation,
            addMessage,
            updateStreamingMessage,
            finalizeStreamingMessage,
            setProcessingState,
          } = get();

          if (!currentConversation) {
            console.error('No active conversation');
            return;
          }

          console.log('[Store] Current conversation:', currentConversation.id);

          // Add user message
          const userMessage: Message = {
            id: `msg-${Date.now()}`,
            content,
            type: 'USER' as any,
            source: 'USER' as any,
            timestamp: new Date().toISOString(),
            conversationId: currentConversation.id,
          };
          addMessage(currentConversation.id, userMessage);
          console.log('[Store] User message added:', userMessage);

          // Update processing state for this conversation
          setProcessingState(currentConversation.id, ProcessingState.STREAMING);
          console.log('[Store] Processing state set to STREAMING for', currentConversation.id);

          // Initialize streaming message for this conversation
          const aiMessageId = `msg-${Date.now() + 1}`;
          set((state) => ({
            streamingMessages: {
              ...state.streamingMessages,
              [currentConversation.id]: {
                id: aiMessageId,
                content: '',
                type: 'AI' as any,
                source: 'AI' as any,
                timestamp: new Date().toISOString(),
                conversationId: currentConversation.id,
                isStreaming: true,
              },
            },
          }));
          console.log('[Store] Streaming message initialized:', aiMessageId);

          // Stream response via API
          console.log('[Store] Calling api.message.stream...');
          await api.message.stream(
            currentConversation.id,
            content,
            // onChunk
            (chunk) => {
              console.log('[Store] onChunk callback called with chunk:', chunk);
              updateStreamingMessage(chunk);
            },
            // onComplete
            (message) => {
              console.log('[Store] onComplete callback called with message:', message);
              finalizeStreamingMessage({
                ...message,
                id: aiMessageId,
                conversationId: currentConversation.id,
              });
              setProcessingState(currentConversation.id, ProcessingState.IDLE);
              console.log('[Store] Stream completed and state set to IDLE');
            },
            // onError
            (error) => {
              console.error('[Store] onError callback called:', error);
              set((state) => {
                // Remove the streaming message key for this conversation
                const { [currentConversation.id]: removed, ...remainingMessages } = state.streamingMessages;
                return {
                  streamingMessages: remainingMessages,
                };
              });
              setProcessingState(currentConversation.id, ProcessingState.ERROR);
            }
          );
          console.log('[Store] api.message.stream call completed');
        },

        /**
         * Stop current streaming response
         */
        stopStreaming: async () => {
          const { currentConversation, setProcessingState } = get();

          if (!currentConversation) return;

          await api.message.stop(currentConversation.id);
          setProcessingState(currentConversation.id, ProcessingState.IDLE);
        },
      }),
      {
        name: 'lynexus-app-store',
        // Only persist specific fields
        partialize: (state) => ({
          theme: state.theme,
          language: state.language,
          isSidebarOpen: state.isSidebarOpen,
        }),
      }
    ),
    { name: 'LynexusAppStore' }
  )
);

// ============================================================================
// Selectors
// ============================================================================

/**
 * Get current conversation messages
 */
export const useCurrentMessages = () => {
  const { currentConversation, messages, streamingMessages } = useAppStore();
  const conversationId = currentConversation?.id;
  const conversationMessages =
    conversationId && messages[conversationId]
      ? messages[conversationId]
      : [];

  return {
    messages: conversationMessages,
    streamingMessage: conversationId ? streamingMessages[conversationId] : null,
  };
};

/**
 * Get processing state for current conversation
 */
export const useProcessingState = () => {
  const { currentConversation, processingStates, streamingMessages } = useAppStore();
  const conversationId = currentConversation?.id;

  return {
    isProcessing: conversationId ? (processingStates[conversationId] !== ProcessingState.IDLE) : false,
    processingState: conversationId ? (processingStates[conversationId] || ProcessingState.IDLE) : ProcessingState.IDLE,
    streamingMessage: conversationId ? streamingMessages[conversationId] : null,
  };
};

export default useAppStore;
