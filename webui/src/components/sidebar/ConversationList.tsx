/**
 * ConversationList Component
 * Telegram-style sidebar with conversation list
 */

import { useState, useCallback } from 'react';
import {
  Plus,
  Settings,
  Database,
  Trash2,
  MessageSquare,
  Import,
  Download,
  Wrench,
  Eraser,
  FileArchive,
} from 'lucide-react';
import { api } from '@services/api';
import I18n from '@i18n';
import { cn } from '../../utils/classnames';
import { useAppStore } from '../../stores/useAppStore';
import { getRelativeTime, stripMarkdown, truncate } from '../../utils';
import type { Conversation } from '../../types';
import { NewChatDialog } from '@components/dialogs/NewChatDialog';

// ============================================================================
// Type Definitions
// ============================================================================

interface ConversationListProps {
  /**
   * Additional className
   */
  className?: string;
}

// ============================================================================
// Action Button Component
// ============================================================================

/**
 * Sidebar action button
 */
interface ActionButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: 'default' | 'danger';
}

function ActionButton({ icon, label, onClick, variant = 'default' }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
        'hover:translate-x-1',
        variant === 'danger'
          ? 'text-red-400 hover:bg-red-500/10'
          : 'text-dark-text hover:bg-dark-bgTertiary'
      )}
      title={label}
    >
      <span className="flex-shrink-0">{icon}</span>
      <span className="flex-1 text-left text-sm font-medium">{label}</span>
    </button>
  );
}

// ============================================================================
// Conversation Item Component
// ============================================================================

/**
 * Single conversation item
 */
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
}

function ConversationItem({
  conversation,
  isActive,
  onClick,
  onDelete,
}: ConversationItemProps) {
  const [showDelete, setShowDelete] = useState(false);

  return (
    <div
      className={cn(
        'group relative flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-all duration-200',
        isActive
          ? 'bg-primary text-white'
          : 'hover:bg-dark-bgTertiary text-dark-text'
      )}
      onClick={onClick}
      onMouseEnter={() => setShowDelete(true)}
      onMouseLeave={() => setShowDelete(false)}
    >
      {/* Avatar with first letter */}
      <div
        className={cn(
          'flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold',
          isActive ? 'bg-white/20' : 'bg-primary'
        )}
      >
        {conversation.name.charAt(0).toUpperCase()}
      </div>

      {/* Conversation info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-semibold truncate">{conversation.name}</h3>
          {conversation.updatedAt && (
            <span
              className={cn(
                'text-xs flex-shrink-0',
                isActive ? 'text-white/70' : 'text-dark-textTertiary'
              )}
            >
              {getRelativeTime(conversation.updatedAt)}
            </span>
          )}
        </div>

        {conversation.lastMessage && (
          <p
            className={cn(
              'text-sm truncate mt-0.5',
              isActive ? 'text-white/70' : 'text-dark-textSecondary'
            )}
          >
            {truncate(stripMarkdown(conversation.lastMessage), 50)}
          </p>
        )}

        {/* Message count badge */}
        {conversation.messageCount > 0 && (
          <span className="text-xs mt-1">{conversation.messageCount} messages</span>
        )}
      </div>

      {/* Delete button */}
      {showDelete && !isActive && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="flex-shrink-0 p-1.5 rounded-md text-red-400 hover:bg-red-500/10 transition-colors"
          aria-label="Delete conversation"
        >
          <Trash2 size={16} />
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Telegram-style conversation list sidebar
 */
export function ConversationList({ className }: ConversationListProps) {
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    createConversation,
    deleteConversation,
    openSettings,
    openInitDialog,
    openToolsList,
    loadConversations,
  } = useAppStore();

  const [isCreating, setIsCreating] = useState(false);
  const [showNewChatDialog, setShowNewChatDialog] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  /**
   * Handle new chat button click - show dialog
   */
  function handleNewChat() {
    if (isCreating) return;
    setShowNewChatDialog(true);
  }

  /**
   * Handle creating chat with custom name
   */
  async function handleCreateChat(name: string) {
    if (isCreating) return;

    setIsCreating(true);
    const newConversation = await createConversation(name);

    if (newConversation) {
      setCurrentConversation(newConversation);
    }

    setIsCreating(false);
  }

  /**
   * Handle conversation select
   */
  function handleSelectConversation(conversation: Conversation) {
    setCurrentConversation(conversation);
  }

  /**
   * Handle conversation delete
   */
  async function handleDeleteConversation(id: string) {
    const conversation = conversations.find(c => c.id === id);
    const message = conversation
      ? I18n.trp('confirm_delete_message', { 0: conversation.name })
      : 'Are you sure you want to delete this conversation?';

    if (window.confirm(message)) {
      await deleteConversation(id);
    }
  }

  /**
   * Handle export chat history
   */
  async function handleExportChat() {
    if (!currentConversation) {
      alert('No active conversation to export');
      return;
    }

    try {
      const response = await api.transfer.exportHistory(currentConversation.id);
      if (response.success && response.data) {
        // Create download link
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentConversation.name}_history.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to export: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export chat history');
    }
  }

  /**
   * Handle import config
   */
  async function handleImportConfig() {
    // Create file input for ZIP files
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.zip';

    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const response = await api.transfer.importConfig(file);
        if (response.success && response.data) {
          // Add the imported conversation to the store
          const { setCurrentConversation, loadConversations } = useAppStore.getState();
          // Reload conversations to get the latest list
          await loadConversations();
          setCurrentConversation(response.data);
          alert('Configuration imported successfully!');
        } else {
          alert('Failed to import: ' + (response.error || 'Unknown error'));
        }
      } catch (error) {
        console.error('Import error:', error);
        alert('Failed to import configuration');
      }
    };

    input.click();
  }

  /**
   * Handle clear chat messages
   */
  async function handleClearChat() {
    if (!currentConversation) {
      alert(I18n.tr('warning'));
      return;
    }

    const clearMessage = `Clear all messages in '${currentConversation.name}'?`;
    if (!confirm(clearMessage)) {
      return;
    }

    try {
      const response = await api.conversation.clearMessages(currentConversation.id);
      if (response.success) {
        // Clear messages in store
        useAppStore.getState().setMessages(currentConversation.id, []);
        const successMessage = `Chat history cleared for '${currentConversation.name}'.\nAI conversation history has also been reset.`;
        alert(successMessage);
      } else {
        alert('Failed to clear: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Clear error:', error);
      alert('Failed to clear chat history');
    }
  }

  /**
   * Extract conversation name from zip filename
   * Removes "_config" suffix and generates unique name if needed
   */
  function getConversationNameFromZip(fileName: string): string {
    // Remove .zip extension
    let name = fileName.replace(/\.zip$/i, '');

    // Remove "_config" suffix if present
    name = name.replace(/_config$/, '');

    // Check for existing names with the same base
    const existingNames = new Set(conversations.map(c => c.name.toLowerCase()));

    // If name doesn't exist, use it directly
    if (!existingNames.has(name.toLowerCase())) {
      return name;
    }

    // Find a unique name by appending _1, _2, etc.
    let counter = 1;
    let uniqueName = name;
    while (existingNames.has(uniqueName.toLowerCase())) {
      uniqueName = `${name}_${counter}`;
      counter++;
    }

    return uniqueName;
  }

  /**
   * Handle drag over event - only allow zip files
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Check if dragging files
    const hasFiles = e.dataTransfer.types.includes('Files');
    if (hasFiles) {
      setIsDragging(true);
    }
  }, []);

  /**
   * Handle drag leave event
   */
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Only hide drag overlay if we're leaving the container
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
      setIsDragging(false);
    }
  }, []);

  /**
   * Handle drop event - process zip files
   */
  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);

    // Filter for zip files only
    const zipFiles = files.filter(file =>
      file.name.toLowerCase().endsWith('.zip')
    );

    if (zipFiles.length === 0) {
      return;
    }

    // Process first zip file
    const zipFile = zipFiles[0];
    const conversationName = getConversationNameFromZip(zipFile.name);

    try {
      const response = await api.transfer.importConfig(zipFile, conversationName);
      if (response.success && response.data) {
        // Reload conversations to get the latest list
        await loadConversations();
        setCurrentConversation(response.data);
        alert(`Configuration imported successfully!\nCreated conversation: ${response.data.name}`);
      } else {
        alert('Failed to import: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Import error:', error);
      alert('Failed to import configuration');
    }
  }, [conversations, loadConversations, setCurrentConversation]);

  return (
    <div
      className={cn(
        'flex flex-col h-full bg-dark-bgSecondary border-r border-dark-border relative',
        className
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <MessageSquare className="text-primary" size={24} />
          <h1 className="text-lg font-semibold">LyNexus</h1>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          disabled={isCreating}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-4 py-3',
            'bg-primary text-white font-medium rounded-lg',
            'hover:bg-primary-hover active:bg-primary-active',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors duration-200'
          )}
        >
          <Plus size={18} />
          <span>{I18n.tr('new_chat')}</span>
        </button>
      </div>

      {/* Conversations Label */}
      <div className="px-4 pb-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-dark-textTertiary">
          {I18n.tr('conversations')}
        </h2>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2 scrollbar-thin scrollbar-thumb-dark-border scrollbar-track-transparent">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="w-16 h-16 mb-4 rounded-full bg-dark-bgTertiary flex items-center justify-center">
              <MessageSquare className="text-dark-textTertiary" size={32} />
            </div>
            <p className="text-dark-textSecondary text-sm">
              No conversations yet.<br />Click "{I18n.tr('new_chat')}" to create one.
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={currentConversation?.id === conversation.id}
                onClick={() => handleSelectConversation(conversation)}
                onDelete={() => handleDeleteConversation(conversation.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="border-t border-dark-border p-2">
        <div className="space-y-1">
          <ActionButton
            icon={<Settings size={18} />}
            label={I18n.tr('settings')}
            onClick={openSettings}
          />
          <ActionButton
            icon={<Database size={18} />}
            label={I18n.tr('initialize')}
            onClick={openInitDialog}
          />
          <ActionButton
            icon={<Wrench size={18} />}
            label={I18n.tr('tools')}
            onClick={openToolsList}
          />
          <ActionButton
            icon={<Download size={18} />}
            label={I18n.tr('export_chat')}
            onClick={handleExportChat}
          />
          <ActionButton
            icon={<Import size={18} />}
            label={I18n.tr('import_config')}
            onClick={handleImportConfig}
          />
          {currentConversation && (
            <ActionButton
              icon={<Eraser size={18} />}
              label={I18n.tr('clear_chat')}
              onClick={handleClearChat}
            />
          )}
          {currentConversation && (
            <ActionButton
              icon={<Trash2 size={18} />}
              label={I18n.tr('delete_chat')}
              onClick={() => handleDeleteConversation(currentConversation.id)}
              variant="danger"
            />
          )}
        </div>
      </div>

      {/* New Chat Dialog */}
      <NewChatDialog
        isOpen={showNewChatDialog}
        onClose={() => setShowNewChatDialog(false)}
        onCreate={handleCreateChat}
      />

      {/* Drag and Drop Overlay */}
      {isDragging && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-primary/90 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="flex flex-col items-center gap-4 p-8 rounded-2xl bg-dark-bgSecondary border-2 border-dashed border-primary">
            <FileArchive size={64} className="text-primary" />
            <p className="text-xl font-semibold text-dark-text">
              Drop configuration file here
            </p>
            <p className="text-sm text-dark-textSecondary">
              Import conversation configuration from .zip file
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ConversationList;
