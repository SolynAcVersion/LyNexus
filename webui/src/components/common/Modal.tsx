/**
 * Modal Component
 * A reusable modal/dialog component
 */

import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/classnames';
import { X } from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  /**
   * Callback when modal is closed
   */
  onClose: () => void;
  /**
   * Modal title
   */
  title?: string;
  /**
   * Modal size
   */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /**
   * Show close button
   */
  showCloseButton?: boolean;
  /**
   * Close on backdrop click
   */
  closeOnBackdropClick?: boolean;
  /**
   * Close on Escape key press
   */
  closeOnEscape?: boolean;
  /**
   * Modal content
   */
  children: React.ReactNode;
  /**
   * Additional className for modal content
   */
  className?: string;
}

// ============================================================================
// Size Styles
// ============================================================================

const sizeStyles: Record<string, string> = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-full mx-4',
};

// ============================================================================
// Component
// ============================================================================

/**
 * Modal component with backdrop and animations
 */
export function Modal({
  isOpen,
  onClose,
  title,
  size = 'md',
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
  children,
  className,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  /**
   * Handle Escape key press
   */
  useEffect(() => {
    if (!closeOnEscape || !isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [closeOnEscape, isOpen, onClose]);

  /**
   * Focus trap inside modal
   */
  useEffect(() => {
    if (!isOpen) return;

    const modal = modalRef.current;
    if (!modal) return;

    // Focus first focusable element
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    firstElement?.focus();

    // Focus trap
    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleTab);
    return () => document.removeEventListener('keydown', handleTab);
  }, [isOpen]);

  /**
   * Prevent body scroll when modal is open
   */
  useEffect(() => {
    if (!isOpen) return;

    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  /**
   * Handle backdrop click
   */
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnBackdropClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  const content = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in" />

      {/* Modal */}
      <div
        ref={modalRef}
        className={cn(
          'relative bg-dark-bg border border-dark-border rounded-xl shadow-2xl',
          'w-full animate-slide-in',
          sizeStyles[size],
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border">
            {title && (
              <h2 className="text-lg font-semibold text-dark-text">{title}</h2>
            )}

            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-1 rounded-lg text-dark-textSecondary hover:text-dark-text hover:bg-dark-bgTertiary transition-colors"
                aria-label="Close modal"
              >
                <X size={20} />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );

  return createPortal(content, document.body);
}

export default Modal;
