/**
 * Utility function for conditionally joining class names
 * Similar to clsx or classnames package
 */

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

export default cn;
