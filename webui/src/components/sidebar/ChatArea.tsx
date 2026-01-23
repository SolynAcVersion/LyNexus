/**
 * ChatArea Component
 * Main chat area with header, message list, and input
 */

import { useEffect } from 'react';
import { MoreVertical, Phone, Video, Search, Info } from 'lucide-react';
import { MessageList } from '../chat/MessageList';
import { MessageInput } from '../chat/MessageInput';
import { useAppStore } from '../../stores/useAppStore';
import { cn } from '../../utils/classnames';
import { Button } from '../common/Button';

// ============================================================================
// Type Definitions
// ============================================================================

interface ChatAreaProps {
  /**
   * Additional className
   */
  className?: string;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Main chat area component
 */
export function ChatArea({ className }: ChatAreaProps) {
  const {
    currentConversation,
    messages,
    streamingMessages,
    processingStates,
    loadMessages,
    sendMessage,
    stopStreaming,
    showToolsList,
    openToolsList,
  } = useAppStore();

  // Load messages when conversation changes
  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation.id);
    }
  }, [currentConversation, loadMessages]);

  const conversationId = currentConversation?.id;
  const conversationMessages = conversationId
    ? messages[conversationId] || []
    : [];
  const streamingMessage = conversationId ? streamingMessages[conversationId] : undefined;
  const processingState = conversationId ? (processingStates[conversationId] || 'IDLE') : 'IDLE';
  const isProcessing = processingState !== 'IDLE';

  /**
   * Handle send message
   */
  function handleSend(content: string) {
    sendMessage(content);
  }

  /**
   * Handle stop streaming
   */
  function handleStop() {
    stopStreaming();
  }

  return (
    <div className={cn('flex flex-col h-full bg-dark-bg', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border bg-dark-bg/95 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          {/* Avatar */}
          {currentConversation && (
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white font-bold">
              {currentConversation.name.charAt(0).toUpperCase()}
            </div>
          )}

          {/* Title */}
          <div>
            <h2 className="font-semibold text-dark-text">
              {currentConversation?.name || 'Select a conversation'}
            </h2>
            {currentConversation && (
              <p className="text-xs text-dark-textSecondary">
                {conversationMessages.length} messages
              </p>
            )}
          </div>
        </div>

        {/* Action buttons */}
        {currentConversation && (
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" icon={<Search size={18} />} />
            <Button variant="ghost" size="sm" icon={<Phone size={18} />} />
            <Button variant="ghost" size="sm" icon={<Video size={18} />} />
            <Button variant="ghost" size="sm" icon={<Info size={18} />} onClick={openToolsList} />
            <Button variant="ghost" size="sm" icon={<MoreVertical size={18} />} />
          </div>
        )}
      </div>

      {/* Messages */}
      <MessageList
        messages={conversationMessages}
        streamingMessage={streamingMessage}
        isProcessing={isProcessing}
        emptyMessage={
          currentConversation
            ? 'Start a conversation by sending a message!'
            : 'Select a conversation from the sidebar or create a new one.'
        }
      />

      {/* Input */}
      {currentConversation && (
        <MessageInput
          onSend={handleSend}
          onStop={handleStop}
          showStop={isProcessing}
          disabled={processingState === 'LOADING'}
        />
      )}
    </div>
  );
}

export default ChatArea;
