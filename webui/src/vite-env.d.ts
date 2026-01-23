/**
 * Vite environment variable type definitions
 */

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  // Add more env variables here
}

interface ImportMeta {
  readonly env: ImportMetaEnv
  hot?: any
}
