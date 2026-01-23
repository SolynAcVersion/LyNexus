/**
 * Button Component
 * A reusable button component with various styles and states
 */

import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '../../utils/classnames';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Button variant/style
   */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  /**
   * Button size
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Loading state
   */
  isLoading?: boolean;
  /**
   * Full width button
   */
  fullWidth?: boolean;
  /**
   * Icon element to display
   */
  icon?: React.ReactNode;
  /**
   * Icon position
   */
  iconPosition?: 'left' | 'right';
}

// ============================================================================
// Styles
// ============================================================================

const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-bg disabled:opacity-50 disabled:cursor-not-allowed';

const variantStyles: Record<string, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover active:bg-primary-active focus:ring-primary',
  secondary: 'bg-dark-bgTertiary text-dark-text hover:bg-dark-border',
  ghost: 'bg-transparent text-dark-text hover:bg-dark-bgTertiary',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  success: 'bg-green-600 text-white hover:bg-green-700',
};

const sizeStyles: Record<string, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

// ============================================================================
// Component
// ============================================================================

/**
 * Reusable Button component
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      fullWidth = false,
      icon,
      iconPosition = 'left',
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}

        {icon && iconPosition === 'left' && !isLoading && <span>{icon}</span>}

        {children}

        {icon && iconPosition === 'right' && !isLoading && <span>{icon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
