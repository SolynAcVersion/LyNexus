/**
 * Electron API Hook
 * Provides access to Electron APIs from the renderer process
 */

import { useEffect, useState } from 'react';
import type { ElectronAPI } from '../types';

/**
 * Check if running in Electron environment
 */
export function isElectron(): boolean {
  return typeof window !== 'undefined' && !!window.electronAPI;
}

/**
 * Hook to access Electron APIs
 * Returns null if not running in Electron
 */
export function useElectron(): ElectronAPI | null {
  const [electronAPI, setElectronAPI] = useState<ElectronAPI | null>(null);

  useEffect(() => {
    if (isElectron()) {
      setElectronAPI(window.electronAPI);
    }
  }, []);

  return electronAPI;
}

/**
 * Hook to get window information
 */
export function useWindowInfo() {
  const electronAPI = useElectron();
  const [windowInfo, setWindowInfo] = useState({
    isMaximized: false,
    isFullscreen: false,
    bounds: { width: 0, height: 0, x: 0, y: 0 },
  });

  useEffect(() => {
    if (!electronAPI) return;

    const fetchWindowInfo = async () => {
      const info = await electronAPI.window.getInfo();
      setWindowInfo(info);
    };

    fetchWindowInfo();

    // TODO: Set up event listeners for window state changes
    // when IPC events are implemented in the main process
  }, [electronAPI]);

  return windowInfo;
}

/**
 * Hook to get system information
 */
export function useSystemInfo() {
  const electronAPI = useElectron();
  const [systemInfo, setSystemInfo] = useState({
    platform: '',
    version: '',
  });

  useEffect(() => {
    if (!electronAPI) return;

    const fetchSystemInfo = async () => {
      const [platform, version] = await Promise.all([
        electronAPI.system.getPlatform(),
        electronAPI.system.getVersion(),
      ]);

      setSystemInfo({ platform, version });
    };

    fetchSystemInfo();
  }, [electronAPI]);

  return systemInfo;
}

export default useElectron;
