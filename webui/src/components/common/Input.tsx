/**
 * Input Component
 * Reusable text input component
 */

import { forwardRef } from 'react';
import { cn } from '../../utils/classnames';

// ============================================================================
// Type Definitions
// ============================================================================

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Input label
   */
  label?: string;
  /**
   * Error message
   */
  error?: string;
  /**
   * Left icon
   */
  leftIcon?: React.ReactNode;
  /**
   * Right icon
   */
  rightIcon?: React.ReactNode;
  /**
   * Full width input
   */
  fullWidth?: boolean;
}

// ============================================================================
// Component
// ============================================================================

/**
 * Reusable Input component
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label className="text-sm font-medium text-dark-textSecondary">
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-textTertiary">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            className={cn(
              'px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border',
              'text-dark-text placeholder:text-dark-textTertiary',
              'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors duration-200',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
              fullWidth && 'w-full',
              className
            )}
            disabled={disabled}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-textTertiary">
              {rightIcon}
            </div>
          )}
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
