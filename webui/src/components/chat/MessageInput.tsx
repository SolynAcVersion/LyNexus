/**
 * MessageInput Component
 * Telegram-style message input with file drag-drop support
 */

import { useState } from 'react';
import { Send, Paperclip, FileUp } from 'lucide-react';
import { useMessageInput } from '@hooks/useMessageInput';
import { Button } from '@components/common/Button';
import { cn } from '../../utils/classnames';
import type { DroppedFile } from '../../types';

// ============================================================================
// Type Definitions
// ============================================================================

interface MessageInputProps {
  /**
   * Callback when message is sent
   */
  onSend: (content: string) => void;
  /**
   * Callback when files are dropped
   */
  onFileDrop?: (files: File[]) => void;
  /**
   * Whether input is disabled
   */
  disabled?: boolean;
  /**
   * Placeholder text
   */
  placeholder?: string;
  /**
   * Show stop button instead of send
   */
  showStop?: boolean;
  /**
   * Callback when stop is clicked
   */
  onStop?: () => void;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Telegram-style message input component
 */
export function MessageInput({
  onSend,
  onFileDrop,
  disabled = false,
  placeholder = 'Type your message...',
  showStop = false,
  onStop,
}: MessageInputProps) {
  const [attachedFiles, setAttachedFiles] = useState<DroppedFile[]>([]);

  const {
    value,
    setValue,
    handleChange,
    handleKeyDown,
    handlePaste,
    handleDrop,
    handleDragOver,
    handleDragLeave,
    textareaRef,
    isDragging,
    clearInput,
    focusInput,
  } = useMessageInput({
    onSend: (content) => {
      onSend(content);
      clearInput();
      setAttachedFiles([]);
    },
    onDrop: handleFileDrop,
    disabled,
    placeholder,
  });

  /**
   * Handle file drop
   */
  function handleFileDrop(files: File[]) {
    if (!onFileDrop) return;

    const droppedFiles: DroppedFile[] = files.map((file) => ({
      name: file.name,
      path: (file as any).path || file.name,
      size: file.size,
      type: file.type,
    }));

    setAttachedFiles([...attachedFiles, ...droppedFiles]);
    onFileDrop(files);
  }

  /**
   * Remove attached file
   */
  function removeFile(index: number) {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  }

  /**
   * Get file icon based on type
   */
  function getFileIcon(type: string) {
    if (type.startsWith('image/')) {
      return '🖼️';
    }
    if (type.startsWith('video/')) {
      return '🎬';
    }
    if (type.startsWith('audio/')) {
      return '🎵';
    }
    return '📎';
  }

  return (
    <div className="border-t border-dark-border bg-dark-bgSecondary">
      {/* Attached files preview */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pt-4">
          {attachedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-1.5 bg-dark-bgTertiary rounded-full text-sm"
            >
              <span>{getFileIcon(file.type)}</span>
              <span className="max-w-[200px] truncate">{file.name}</span>
              <button
                onClick={() => removeFile(index)}
                className="text-dark-textTertiary hover:text-dark-text transition-colors"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input area */}
      <div
        className={cn(
          'flex items-end gap-3 px-4 py-3 transition-all duration-200',
          isDragging && 'bg-primary/5 scale-[1.02]'
        )}
      >
        {/* Attachment button */}
        {!showStop && (
          <button
            className="p-2 text-dark-textSecondary hover:text-dark-text hover:bg-dark-bgTertiary rounded-lg transition-colors"
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.multiple = true;
              input.onchange = (e) => {
                const files = Array.from((e.target as HTMLInputElement).files || []);
                if (files.length > 0) {
                  handleFileDrop(files);
                }
              };
              input.click();
            }}
            disabled={disabled}
            aria-label="Attach file"
          >
            <Paperclip size={20} />
          </button>
        )}

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'w-full min-h-[44px] max-h-[200px] px-4 py-3',
              'bg-dark-bgTertiary border border-dark-border rounded-2xl',
              'text-dark-text placeholder:text-dark-textTertiary',
              'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'resize-none overflow-hidden',
              'transition-colors duration-200'
            )}
            rows={1}
          />

          {/* Drag overlay */}
          {isDragging && (
            <div className="absolute inset-0 border-2 border-dashed border-primary rounded-2xl flex flex-col items-center justify-center bg-primary/10 backdrop-blur-sm animate-in fade-in duration-200">
              <FileUp size={32} className="text-primary mb-2" />
              <p className="text-primary font-medium">Drop files here</p>
              <p className="text-xs text-primary/70 mt-1">Files will be attached with full paths</p>
            </div>
          )}
        </div>

        {/* Send/Stop button */}
        <Button
          size="md"
          variant={showStop ? 'danger' : 'primary'}
          icon={showStop ? undefined : <Send size={18} />}
          onClick={showStop ? onStop : () => {
            const trimmed = value.trim();
            if (trimmed) {
              onSend(trimmed);
              clearInput();
              setAttachedFiles([]);
            }
          }}
          disabled={disabled || (!showStop && !value.trim())}
          className={cn(
            'h-11 min-w-[44px] px-4 rounded-full',
            !showStop && !value.trim() && 'opacity-50'
          )}
        >
          {showStop ? 'Stop' : null}
        </Button>
      </div>

      {/* Helper text */}
      <div className="px-4 pb-2">
        <p className="text-xs text-dark-textTertiary">
          Press <kbd className="px-1.5 py-0.5 bg-dark-bgTertiary rounded text-[10px]">Enter</kbd> to send,
          <kbd className="px-1.5 py-0.5 bg-dark-bgTertiary rounded text-[10px]">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}

export default MessageInput;
