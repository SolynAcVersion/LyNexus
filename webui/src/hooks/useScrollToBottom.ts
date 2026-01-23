/**
 * Custom hook for auto-scrolling to bottom
 * Useful for chat interfaces
 */

import { useEffect, useRef, useCallback } from 'react';
import { scrollToBottom, isScrolledToBottom } from '../utils';

interface UseScrollToBottomOptions {
  /**
   * Additional dependencies that should trigger scroll
   */
  deps?: React.DependencyList;
  /**
   * Whether auto-scroll is enabled
   */
  enabled?: boolean;
  /**
   * Threshold for considering "at bottom"
   */
  threshold?: number;
  /**
   * Smooth scrolling
   */
  smooth?: boolean;
}

interface UseScrollToBottomReturn {
  scrollRef: React.RefObject<HTMLDivElement>;
  scrollToBottom: () => void;
  scrollToBottomIfNeeded: () => void;
  isAtBottom: boolean;
}

/**
 * Hook for managing scroll-to-bottom behavior
 */
export function useScrollToBottom(
  options: UseScrollToBottomOptions = {}
): UseScrollToBottomReturn {
  const { deps = [], enabled = true, threshold = 50, smooth = true } = options;

  const scrollRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  /**
   * Scroll to bottom
   */
  const scrollToBottomFn = useCallback(() => {
    if (scrollRef.current && enabled) {
      scrollToBottom(scrollRef.current, smooth);
    }
  }, [enabled, smooth]);

  /**
   * Scroll to bottom only if already near bottom
   */
  const scrollToBottomIfNeeded = useCallback(() => {
    if (scrollRef.current && enabled && isAtBottomRef.current) {
      scrollToBottom(scrollRef.current, smooth);
    }
  }, [enabled, smooth]);

  /**
   * Track scroll position to determine if user is at bottom
   */
  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;

    const handleScroll = () => {
      isAtBottomRef.current = isScrolledToBottom(element, threshold);
    };

    element.addEventListener('scroll', handleScroll);
    return () => element.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  /**
   * Auto-scroll when dependencies change
   */
  useEffect(() => {
    scrollToBottomIfNeeded();
  }, [...deps, scrollToBottomIfNeeded]);

  return {
    scrollRef,
    scrollToBottom: scrollToBottomFn,
    scrollToBottomIfNeeded,
    isAtBottom: isAtBottomRef.current,
  };
}

export default useScrollToBottom;
