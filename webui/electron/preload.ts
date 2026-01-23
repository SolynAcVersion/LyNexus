/**
 * Electron Preload Script
 * Exposes safe APIs to the renderer process via context bridge
 */

import { contextBridge, ipcRenderer } from 'electron';

// ============================================================================
// Type Definitions
// ============================================================================

interface WindowAPI {
  window: {
    minimize: () => Promise<void>;
    maximize: () => Promise<void>;
    close: () => Promise<void>;
    getInfo: () => Promise<WindowInfo>;
  };
  system: {
    getPlatform: () => Promise<string>;
    getVersion: () => Promise<string>;
  };
}

interface WindowInfo {
  isMaximized: boolean;
  isFullscreen: boolean;
  bounds: {
    width: number;
    height: number;
    x: number;
    y: number;
  };
}

// ============================================================================
// Expose Safe APIs to Renderer
// ============================================================================

/**
 * Expose protected methods that allow the renderer process to use
 * the ipcRenderer without exposing the entire object
 */
const windowAPI: WindowAPI = {
  window: {
    minimize: () => ipcRenderer.invoke('window:minimize'),
    maximize: () => ipcRenderer.invoke('window:maximize'),
    close: () => ipcRenderer.invoke('window:close'),
    getInfo: () => ipcRenderer.invoke('window:getInfo'),
  },
  system: {
    getPlatform: () => ipcRenderer.invoke('system:getPlatform'),
    getVersion: () => ipcRenderer.invoke('system:getVersion'),
  },
};

/**
 * Expose the API to the window object
 */
contextBridge.exposeInMainWorld('electronAPI', windowAPI);

// ============================================================================
// Type Declaration for TypeScript
// ============================================================================

declare global {
  interface Window {
    electronAPI: WindowAPI;
  }
}

export {};
