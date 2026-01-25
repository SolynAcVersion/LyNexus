/**
 * MessageBubble Component
 * Telegram-style message bubble with Markdown support
 */

import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import { formatTime } from '../../utils';
import { cn } from '../../utils/classnames';
import type { Message, MessageType } from '../../types';
import {
  Copy,
  CheckCheck,
  Terminal,
  AlertCircle,
  Info,
} from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

interface MessageIconProps {
  type: MessageType;
}

// ============================================================================
// Message Type Icon Component
// ============================================================================

/**
 * Get icon for message type
 */
function MessageIcon({ type }: MessageIconProps) {
  const iconProps = { size: 16, className: 'flex-shrink-0' };

  switch (type) {
    case 'COMMAND_REQUEST':
      return <Terminal {...iconProps} />;
    case 'COMMAND_RESULT':
      return <Terminal {...iconProps} />;
    case 'ERROR':
      return <AlertCircle {...iconProps} />;
    case 'INFO':
      return <Info {...iconProps} />;
    default:
      return null;
  }
}

// ============================================================================
// Message Bubble Styles
// ============================================================================

/**
 * Get bubble styles based on message type
 */
function getBubbleStyles(type: MessageType) {
  const userStyles = 'bg-primary text-white rounded-2xl rounded-tr-md';
  const aiStyles = 'bg-dark-bgTertiary text-dark-text rounded-2xl rounded-tl-md';
  const commandStyles = 'bg-message-command text-green-100 rounded-2xl rounded-tl-md border border-green-900';
  const commandResultStyles = 'bg-message-commandResult text-blue-100 rounded-2xl rounded-tl-md border border-blue-900';
  const summaryStyles = 'bg-message-summary text-purple-100 rounded-2xl rounded-tl-md border border-purple-900';
  const errorStyles = 'bg-message-error text-red-100 rounded-2xl rounded-tl-md border border-red-900';
  const infoStyles = 'bg-message-info text-teal-100 rounded-2xl rounded-tl-md border border-teal-900';

  switch (type) {
    case 'USER':
      return userStyles;
    case 'AI':
      return aiStyles;
    case 'COMMAND_REQUEST':
      return commandStyles;
    case 'COMMAND_RESULT':
      return commandResultStyles;
    case 'FINAL_SUMMARY':
      return summaryStyles;
    case 'ERROR':
      return errorStyles;
    case 'INFO':
      return infoStyles;
    default:
      return aiStyles;
  }
}

/**
 * Get alignment based on message type
 */
function getAlignment(type: MessageType) {
  return type === 'USER' ? 'justify-end' : 'justify-start';
}

// ============================================================================
// Markdown Renderer Component
// ============================================================================

/**
 * Custom Markdown renderer with styled elements
 */
function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkRehype]}
      rehypePlugins={[rehypeRaw]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        code: ({ node, className, children, ...props }: any) =>
          className ? (
            <code
              className="px-1.5 py-0.5 rounded bg-black/20 text-sm font-mono"
              {...props}
            >
              {children}
            </code>
          ) : (
            <code
              className="block p-3 rounded-lg bg-black/30 text-sm font-mono overflow-x-auto"
              {...props}
            >
              {children}
            </code>
          ),
        pre: ({ children }) => (
          <pre className="bg-black/30 rounded-lg p-3 overflow-x-auto my-2">
            {children}
          </pre>
        ),
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-light underline hover:text-white transition-colors"
          >
            {children}
          </a>
        ),
        ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
        li: ({ children }) => <li className="ml-2">{children}</li>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-black/20 pl-4 italic my-2">
            {children}
          </blockquote>
        ),
        h1: ({ children }) => (
          <h1 className="text-xl font-bold mb-2 mt-4">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-base font-bold mb-2 mt-2">{children}</h3>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2">
            <table className="min-w-full border-collapse">{children}</table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-black/20">{children}</thead>
        ),
        tbody: ({ children }) => <tbody>{children}</tbody>,
        tr: ({ children }) => (
          <tr className="border-b border-black/10">{children}</tr>
        ),
        th: ({ children }) => (
          <th className="px-3 py-2 text-left font-semibold">{children}</th>
        ),
        td: ({ children }) => (
          <td className="px-3 py-2">{children}</td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Telegram-style message bubble component
 */
export const MessageBubble = memo(({ message, isStreaming = false }: MessageBubbleProps) => {
  const isUser = message.type === 'USER';
  const bubbleStyles = getBubbleStyles(message.type);
  const alignment = getAlignment(message.type);

  console.log('[MessageBubble] Rendered:', { id: message.id, content: message.content, isStreaming });

  return (
    <div className={cn('flex w-full mb-4 animate-fade-in', alignment)}>
      <div
        className={cn(
          'flex flex-col max-w-[75%] px-4 py-2.5 shadow-sm',
          bubbleStyles
        )}
      >
        {/* Message Header (Icon for non-user messages) */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <MessageIcon type={message.type} />
            <span className="text-xs font-medium uppercase">
              {message.type.replace(/_/g, ' ').toLowerCase()}
            </span>
          </div>
        )}

        {/* Message Content */}
        <div className="prose prose-invert prose-sm max-w-none">
          {isStreaming ? (
            <p>{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        {/* Message Footer */}
        <div
          className={cn(
            'flex items-center gap-2 mt-1 text-xs opacity-70',
            isUser ? 'justify-end' : 'justify-start'
          )}
        >
          {/* Timestamp */}
          <span className="text-[11px]">{formatTime(message.timestamp)}</span>

          {/* Read receipts for user messages */}
          {isUser && (
            <>
              <CheckCheck size={14} strokeWidth={2.5} />
            </>
          )}

          {/* Copy button (visible on hover) */}
          <button
            className="opacity-0 group-hover:opacity-100 transition-opacity hover:opacity-80"
            onClick={() => {
              navigator.clipboard.writeText(message.content);
            }}
            aria-label="Copy message"
          >
            <Copy size={14} />
          </button>
        </div>

        {/* Streaming indicator */}
        {isStreaming && (
          <div className="flex items-center gap-1 mt-2">
            <span className="w-1.5 h-1.5 bg-current rounded-full animate-pulse" />
            <span className="w-1.5 h-1.5 bg-current rounded-full animate-pulse delay-75" />
            <span className="w-1.5 h-1.5 bg-current rounded-full animate-pulse delay-150" />
          </div>
        )}
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble;
