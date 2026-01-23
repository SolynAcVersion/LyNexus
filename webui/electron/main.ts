/**
 * Electron Main Process
 * Handles window creation and IPC communication
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

// ============================================================================
// Type Definitions
// ============================================================================

interface WindowConfig {
  width: number;
  height: number;
  minWidth: number;
  minHeight: number;
  resizable: boolean;
}

// ============================================================================
// Global References
// ============================================================================

let mainWindow: BrowserWindow | null = null;

// ============================================================================
// Window Creation
// ============================================================================

/**
 * Create and configure the main application window
 */
function createMainWindow(): void {
  const windowConfig: WindowConfig = {
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    resizable: true,
  };

  mainWindow = new BrowserWindow({
    width: windowConfig.width,
    height: windowConfig.height,
    minWidth: windowConfig.minWidth,
    minHeight: windowConfig.minHeight,
    resizable: windowConfig.resizable,
    frame: true,
    titleBarStyle: 'default',
    backgroundColor: '#1E1E1E',
    show: false, // Don't show until ready
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Set app title
  mainWindow.setTitle('LyNexus AI - Assistant');

  // Set app icon (platform-specific)
  if (process.platform === 'win32') {
    const iconPath = path.join(__dirname, '../assets/logo.ico');
    if (fs.existsSync(iconPath)) {
      mainWindow.setIcon(iconPath);
    }
  } else if (process.platform === 'darwin') {
    const iconPath = path.join(__dirname, '../assets/logo.icns');
    if (fs.existsSync(iconPath)) {
      mainWindow.setIcon(iconPath);
    }
  } else {
    const iconPath = path.join(__dirname, '../assets/logo.png');
    if (fs.existsSync(iconPath)) {
      mainWindow.setIcon(iconPath);
    }
  }
}

// ============================================================================
// App Lifecycle
// ============================================================================

/**
 * Handle app ready event
 */
app.on('ready', () => {
  createMainWindow();
  setupIpcHandlers();
});

/**
 * Handle all windows closed
 * Quit on Windows/Linux, keep running on macOS
 */
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * Handle app activation (macOS)
 */
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

/**
 * Handle any uncaught errors
 */
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// ============================================================================
// IPC Handlers
// ============================================================================

/**
 * Setup all IPC communication handlers
 */
function setupIpcHandlers(): void {
  // Window control handlers
  ipcMain.handle('window:minimize', handleWindowMinimize);
  ipcMain.handle('window:maximize', handleWindowMaximize);
  ipcMain.handle('window:close', handleWindowClose);
  ipcMain.handle('window:getInfo', handleWindowGetInfo);

  // System info handlers
  ipcMain.handle('system:getPlatform', handleGetPlatform);
  ipcMain.handle('system:getVersion', handleGetVersion);
}

/**
 * Handle window minimize request
 */
async function handleWindowMinimize(): Promise<void> {
  if (mainWindow) {
    mainWindow.minimize();
  }
}

/**
 * Handle window maximize request
 */
async function handleWindowMaximize(): Promise<void> {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
}

/**
 * Handle window close request
 */
async function handleWindowClose(): Promise<void> {
  if (mainWindow) {
    mainWindow.close();
  }
}

/**
 * Get window information
 */
async function handleWindowGetInfo(): Promise<{
  isMaximized: boolean;
  isFullscreen: boolean;
  bounds: { width: number; height: number; x: number; y: number };
}> {
  if (!mainWindow) {
    return {
      isMaximized: false,
      isFullscreen: false,
      bounds: { width: 0, height: 0, x: 0, y: 0 },
    };
  }

  return {
    isMaximized: mainWindow.isMaximized(),
    isFullscreen: mainWindow.isFullScreen(),
    bounds: mainWindow.getBounds(),
  };
}

/**
 * Get the current platform
 */
async function handleGetPlatform(): Promise<string> {
  return process.platform;
}

/**
 * Get the app version
 */
async function handleGetVersion(): Promise<string> {
  return app.getVersion();
}

// ============================================================================
// Export for testing
// ============================================================================

export { createMainWindow, setupIpcHandlers };
