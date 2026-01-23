/**
 * Spinner Component
 * Loading spinner with various sizes
 */

import { cn } from '../../utils/classnames';

// ============================================================================
// Type Definitions
// ============================================================================

export interface SpinnerProps {
  /**
   * Spinner size
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /**
   * Spinner color
   */
  color?: 'primary' | 'white' | 'current';
  /**
   * Additional className
   */
  className?: string;
}

// ============================================================================
// Size Styles
// ============================================================================

const sizeStyles: Record<string, string> = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

const colorStyles: Record<string, string> = {
  primary: 'text-primary',
  white: 'text-white',
  current: 'text-current',
};

// ============================================================================
// Component
// ============================================================================

/**
 * Loading spinner component
 */
export function Spinner({
  size = 'md',
  color = 'primary',
  className,
}: SpinnerProps) {
  return (
    <svg
      className={cn(
        'animate-spin',
        sizeStyles[size],
        colorStyles[color],
        className
      )}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      role="status"
      aria-label="Loading"
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
  );
}

export default Spinner;
