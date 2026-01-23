/**
 * MessageList Component
 * Container for displaying messages with auto-scroll
 */

import { useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { useScrollToBottom } from '@hooks/useScrollToBottom';
import { Spinner } from '@components/common/Spinner';
import { cn } from '../../utils/classnames';
import type { Message } from '../../types';

// ============================================================================
// Type Definitions
// ============================================================================

interface MessageListProps {
  /**
   * Array of messages to display
   */
  messages: Message[];
  /**
   * Currently streaming message
   */
  streamingMessage?: Message | null;
  /**
   * Whether new messages are being loaded
   */
  isLoading?: boolean;
  /**
   * Whether AI is processing
   */
  isProcessing?: boolean;
  /**
   * Empty state message
   */
  emptyMessage?: string;
  /**
   * Additional className
   */
  className?: string;
}

// ============================================================================
// Empty State Component
// ============================================================================

/**
 * Empty state when no messages exist
 */
function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 mb-4 rounded-full bg-dark-bgTertiary flex items-center justify-center">
        <svg
          className="w-8 h-8 text-dark-textTertiary"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <p className="text-dark-textSecondary">{message}</p>
    </div>
  );
}

// ============================================================================
// Typing Indicator Component
// ============================================================================

/**
 * Typing indicator for AI processing
 */
function TypingIndicator() {
  return (
    <div className="flex w-full mb-4 justify-start">
      <div className="flex items-center gap-2 px-4 py-3 bg-dark-bgTertiary rounded-2xl rounded-tl-md">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce" />
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100" />
          <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200" />
        </div>
        <span className="text-sm text-dark-textTertiary">AI is typing...</span>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Message list container with auto-scroll
 */
export function MessageList({
  messages,
  streamingMessage = null,
  isLoading = false,
  isProcessing = false,
  emptyMessage = 'No messages yet. Start a conversation!',
  className,
}: MessageListProps) {
  const { scrollRef, scrollToBottomIfNeeded } = useScrollToBottom({
    deps: [messages, streamingMessage],
    enabled: true,
  });

  // Scroll to bottom when processing state changes
  useEffect(() => {
    if (!isProcessing) {
      scrollToBottomIfNeeded();
    }
  }, [isProcessing, scrollToBottomIfNeeded]);

  return (
    <div
      ref={scrollRef}
      className={cn(
        'flex-1 overflow-y-auto px-6 py-4',
        'scrollbar-thin scrollbar-thumb-dark-border scrollbar-track-transparent',
        className
      )}
    >
      {/* Loading indicator */}
      {isLoading && (
        <div className="flex items-center justify-center h-full">
          <Spinner size="lg" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && messages.length === 0 && !streamingMessage && (
        <EmptyState message={emptyMessage} />
      )}

      {/* Messages */}
      {!isLoading && (
        <div className="flex flex-col">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Streaming message */}
          {streamingMessage && (
            <MessageBubble message={streamingMessage} isStreaming={true} />
          )}

          {/* Typing indicator */}
          {isProcessing && !streamingMessage && <TypingIndicator />}
        </div>
      )}

      {/* Bottom padding for scroll */}
      <div className="h-4" />
    </div>
  );
}

export default MessageList;
