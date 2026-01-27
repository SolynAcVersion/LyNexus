/**
 * Custom hook for message input handling
 * Manages text input, file drag-drop, and keyboard shortcuts
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { isEnterKey } from '../utils';

interface UseMessageInputOptions {
  onSend: (content: string) => void;
  onDrop?: (files: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

interface UseMessageInputReturn {
  value: string;
  setValue: (value: string) => void;
  handleChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handlePaste: (e: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  handleDrop: (e: React.DragEvent<HTMLTextAreaElement>) => void;
  handleDragOver: (e: React.DragEvent<HTMLTextAreaElement>) => void;
  handleDragLeave: () => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  isDragging: boolean;
  clearInput: () => void;
  focusInput: () => void;
}

/**
 * Hook for managing message input
 */
export function useMessageInput(options: UseMessageInputOptions): UseMessageInputReturn {
  const {
    onSend,
    onDrop,
    disabled = false,
    placeholder = 'Type your message...',
    maxLength = 50000,
  } = options;

  const [value, setValue] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Handle input change
   */
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;

    if (newValue.length <= maxLength) {
      setValue(newValue);
    }
  };

  /**
   * Handle keyboard shortcuts
   * - Enter: Send message
   * - Shift + Enter: New line
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (disabled) return;

    if (isEnterKey(e)) {
      e.preventDefault();
      const trimmed = value.trim();
      if (trimmed) {
        onSend(trimmed);
        setValue('');
      }
    }
  };

  /**
   * Handle paste event
   * Insert file paths if files are pasted
   */
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    if (!onDrop) return;

    const items = e.clipboardData?.items;
    if (!items) return;

    const files: File[] = [];

    for (let i = 0; i < items.length; i++) {
      const item = items[i];

      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          files.push(file);
        }
      }
    }

    if (files.length > 0) {
      e.preventDefault();
      onDrop(files);
    }
  };

  /**
   * Handle drag over event
   */
  const handleDragOver = (e: React.DragEvent<HTMLTextAreaElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  /**
   * Handle drag leave event
   * Only hide overlay if we're actually leaving the textarea
   */
  const handleDragLeave = (e: React.DragEvent<HTMLTextAreaElement>) => {
    e.preventDefault();
    e.stopPropagation();

    // Check if we're really leaving the element (not just entering a child)
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
      setIsDragging(false);
    }
  };

  /**
   * Handle drop event
   * Insert file absolute paths when files are dropped
   */
  const handleDrop = (e: React.DragEvent<HTMLTextAreaElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (!onDrop) return;

    const files = Array.from(e.dataTransfer.files);

    if (files.length > 0) {
      onDrop(files);

      // Insert file absolute paths at the beginning of input
      // In Electron, File objects have a 'path' property
      // In browser, we fall back to just the filename
      const paths = files.map((f) => {
        // Electron provides full path via 'path' property
        const fullPath = (f as File & { path?: string }).path || f.name;
        console.log('File dropped:', {
          name: f.name,
          path: (f as File & { path?: string }).path,
          fullPath: fullPath
        });
        return `"${fullPath}"`;
      }).join(' ');

      // Prepend the paths to the current content
      const newValue = value ? `${paths} ${value}` : paths;
      setValue(newValue);

      // Focus back to textarea
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
  };

  /**
   * Clear input
   */
  const clearInput = useCallback(() => {
    setValue('');
  }, []);

  /**
   * Focus input textarea
   */
  const focusInput = useCallback(() => {
    textareaRef.current?.focus();
  }, []);

  /**
   * Auto-resize textarea based on content
   */
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [value]);

  return {
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
  };
}

export default useMessageInput;
