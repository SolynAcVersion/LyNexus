/**
 * Textarea Component
 * Reusable textarea component with auto-resize
 */

import { forwardRef, useEffect, useRef } from 'react';
import { cn } from '../../utils/classnames';

// ============================================================================
// Type Definitions
// ============================================================================

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Textarea label
   */
  label?: string;
  /**
   * Error message
   */
  error?: string;
  /**
   * Maximum height for auto-resize
   */
  maxHeight?: number;
  /**
   * Enable auto-resize
   */
  autoResize?: boolean;
  /**
   * Full width textarea
   */
  fullWidth?: boolean;
}

// ============================================================================
// Component
// ============================================================================

/**
 * Reusable Textarea component
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      maxHeight = 200,
      autoResize = true,
      fullWidth = false,
      className,
      value,
      disabled,
      ...props
    },
    ref
  ) => {
    const internalRef = useRef<HTMLTextAreaElement>(null);
    const textareaRef = (ref as React.RefObject<HTMLTextAreaElement>) || internalRef;

    /**
     * Auto-resize textarea based on content
     */
    useEffect(() => {
      if (!autoResize) return;

      const textarea = textareaRef.current;
      if (!textarea) return;

      // Reset height to auto to calculate the correct scrollHeight
      textarea.style.height = 'auto';

      // Calculate new height
      const newHeight = Math.min(textarea.scrollHeight, maxHeight);
      textarea.style.height = `${newHeight}px`;
    }, [value, autoResize, maxHeight, textareaRef]);

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label className="text-sm font-medium text-dark-textSecondary">
            {label}
          </label>
        )}

        <textarea
          ref={textareaRef}
          value={value}
          className={cn(
            'px-4 py-3 rounded-lg bg-dark-bgTertiary border border-dark-border',
            'text-dark-text placeholder:text-dark-textTertiary',
            'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors duration-200 resize-none',
            error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
            fullWidth && 'w-full',
            autoResize && 'overflow-hidden',
            className
          )}
          disabled={disabled}
          {...props}
        />

        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;
