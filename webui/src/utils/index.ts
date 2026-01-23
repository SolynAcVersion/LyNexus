/**
 * Utility Functions
 */

import { format, formatDistanceToNow } from 'date-fns';
import type { MessageType } from '../types';

// ============================================================================
// Date Utilities
// ============================================================================

/**
 * Format a timestamp to a readable time
 */
export function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return format(date, 'HH:mm');
  } catch {
    return '';
  }
}

/**
 * Format a timestamp to a readable date and time
 */
export function formatDateTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return format(date, 'yyyy-MM-dd HH:mm:ss');
  } catch {
    return '';
  }
}

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export function getRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return '';
  }
}

/**
 * Check if a date is today
 */
export function isToday(timestamp: string): boolean {
  try {
    const date = new Date(timestamp);
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  } catch {
    return false;
  }
}

// ============================================================================
// String Utilities
// ============================================================================

/**
 * Truncate a string to a maximum length
 */
export function truncate(str: string, maxLength: number, suffix = '...'): string {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Generate a unique ID
 */
export function generateId(prefix = 'id'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Escape HTML special characters
 */
export function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * Strip markdown formatting for preview
 */
export function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/`/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();
}

// ============================================================================
// Message Type Utilities
// ============================================================================

/**
 * Get message bubble type for styling
 */
export function getMessageBubbleColor(type: MessageType): string {
  const colors: Record<MessageType, string> = {
    USER: 'bg-primary',
    AI: 'bg-dark-bgTertiary',
    COMMAND_REQUEST: 'bg-green-900',
    COMMAND_RESULT: 'bg-blue-900',
    FINAL_SUMMARY: 'bg-purple-900',
    ERROR: 'bg-red-900',
    INFO: 'bg-teal-900',
  };

  return colors[type] || colors.AI;
}

/**
 * Get message alignment class
 */
export function getMessageAlignment(type: MessageType): string {
  return type === 'USER' ? 'justify-end' : 'justify-start';
}

// ============================================================================
// File Utilities
// ============================================================================

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get file extension
 */
export function getFileExtension(filename: string): string {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2);
}

/**
 * Check if a file is an image
 */
export function isImageFile(filename: string): boolean {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'];
  const ext = getFileExtension(filename).toLowerCase();
  return imageExtensions.includes(ext);
}

// ============================================================================
// Validation Utilities
// ============================================================================

/**
 * Validate email address
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate API key format (basic check)
 */
export function isValidApiKey(key: string): boolean {
  // Basic check: at least 20 characters
  return key.length >= 20;
}

// ============================================================================
// Color Utilities
// ============================================================================

/**
 * Generate a consistent color from a string
 */
export function stringToColor(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788',
  ];

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Adjust color brightness
 */
export function adjustBrightness(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) + amt;
  const G = (num >> 8 & 0x00FF) + amt;
  const B = (num & 0x0000FF) + amt;

  return '#' + (
    0x1000000 +
    (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
    (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
    (B < 255 ? (B < 1 ? 0 : B) : 255)
  ).toString(16).slice(1);
}

// ============================================================================
// DOM Utilities
// ============================================================================

/**
 * Scroll to bottom of an element
 */
export function scrollToBottom(element: HTMLElement | null, smooth = true): void {
  if (!element) return;

  element.scrollTo({
    top: element.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  });
}

/**
 * Check if element is scrolled to bottom
 */
export function isScrolledToBottom(element: HTMLElement | null, threshold = 50): boolean {
  if (!element) return true;

  return element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;
}

// ============================================================================
// Keyboard Utilities
// ============================================================================

/**
 * Check if key press is Enter (without modifiers)
 */
export function isEnterKey(event: React.KeyboardEvent): boolean {
  return event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.metaKey;
}

/**
 * Check if key press is Enter with Shift modifier
 */
export function isShiftEnter(event: React.KeyboardEvent): boolean {
  return event.key === 'Enter' && event.shiftKey;
}

// ============================================================================
// Debounce/Throttle Utilities
// ============================================================================

/**
 * Debounce a function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle a function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// ============================================================================
// Local Storage Utilities
// ============================================================================

/**
 * Safely get item from local storage
 */
export function getStorageItem<T>(key: string, defaultValue: T): T {
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

/**
 * Safely set item in local storage
 */
export function setStorageItem<T>(key: string, value: T): boolean {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

/**
 * Safely remove item from local storage
 */
export function removeStorageItem(key: string): boolean {
  try {
    window.localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

// ============================================================================
// Clipboard Utilities
// ============================================================================

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Application constants
 */
export const CONSTANTS = {
  MAX_MESSAGE_LENGTH: 50000,
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 100,
  SCROLL_THRESHOLD: 50,
  LOCAL_STORAGE_KEYS: {
    THEME: 'lynexus-theme',
    LANGUAGE: 'lynexus-language',
    SIDEBAR_STATE: 'lynexus-sidebar',
  },
} as const;

export default {
  formatTime,
  formatDateTime,
  getRelativeTime,
  truncate,
  generateId,
  escapeHtml,
  stripMarkdown,
  getMessageBubbleColor,
  getMessageAlignment,
  formatFileSize,
  getFileExtension,
  isImageFile,
  isValidEmail,
  isValidUrl,
  isValidApiKey,
  stringToColor,
  adjustBrightness,
  scrollToBottom,
  isScrolledToBottom,
  isEnterKey,
  isShiftEnter,
  debounce,
  throttle,
  getStorageItem,
  setStorageItem,
  removeStorageItem,
  copyToClipboard,
  CONSTANTS,
};
