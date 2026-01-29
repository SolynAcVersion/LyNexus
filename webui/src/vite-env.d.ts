/// <reference types="vite/client" />

/**
 * Vite environment variable type definitions
 */

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  // Add more env variables here as needed
}

/**
 * Electron-specific extensions
 */
declare global {
  interface File {
    /**
     * Full file path (available in Electron environment)
     * This property is added by Chromium when running in Electron
     */
    path?: string;
  }
}

export {};
