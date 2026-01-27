/**
 * SettingsDialog Component
 * Modal for configuring conversation settings
 */

import { useEffect, useState, useRef } from 'react';
import { Modal } from '@components/common/Modal';
import { Input } from '@components/common/Input';
import { Textarea } from '@components/common/Textarea';
import { Button } from '@components/common/Button';
import { api } from '@services/api';
import { useAppStore } from '../../stores/useAppStore';
import { Save, Download, X, Upload } from 'lucide-react';
import type { ConversationSettings, APIProvider } from '../../types';
import { API_PROVIDERS } from '../../types';

// ============================================================================
// Type Definitions
// ============================================================================

interface SettingsDialogProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  /**
   * Callback when modal is closed
   */
  onClose: () => void;
  /**
   * Callback when settings are saved
   */
  onSave?: (settings: ConversationSettings) => void;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Settings dialog for conversation configuration
 */
export function SettingsDialog({ isOpen, onClose, onSave }: SettingsDialogProps) {
  const { currentConversation } = useAppStore();
  const [settings, setSettings] = useState<ConversationSettings>({
    apiBase: 'https://api.deepseek.com',
    model: 'deepseek-chat',
    temperature: 1.0,
    topP: 1.0,
    presencePenalty: 0.0,
    frequencyPenalty: 0.0,
    stream: true,
    commandStart: 'YLDEXECUTE:',
    commandSeparator: '￥|',
    maxIterations: 15,
    mcpPaths: [],
    enabledMcpTools: [],
    systemPrompt: '',
  });

  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('deepseek');
  const mcpFileInputRef = useRef<HTMLInputElement>(null);

  // Load settings from file when dialog opens - always fetch fresh from backend
  useEffect(() => {
    async function loadSettingsFromFile() {
      if (isOpen && currentConversation) {
        const response = await api.settings.get(currentConversation.id);
        if (response.success && response.data) {
          setSettings(response.data);

          // Load API key if present
          if (response.data.apiKey) {
            setApiKey(response.data.apiKey);
          }

          // Set provider based on apiBase
          const provider = Object.entries(API_PROVIDERS).find(
            ([_, p]) => p.apiBase === response.data.apiBase
          );
          if (provider) {
            setSelectedProvider(provider[0]);
          }
        }
      }
    }

    loadSettingsFromFile();
  }, [isOpen, currentConversation]);

  /**
   * Update settings field
   */
  function updateSetting<K extends keyof ConversationSettings>(
    key: K,
    value: ConversationSettings[K]
  ) {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }

  /**
   * Handle provider change
   */
  function handleProviderChange(providerName: string) {
    setSelectedProvider(providerName);
    const provider = API_PROVIDERS[providerName];
    if (provider) {
      updateSetting('apiBase', provider.apiBase);
      if (provider.models.length > 0) {
        updateSetting('model', provider.models[0]);
      }
    }
  }

  /**
   * Handle save
   */
  function handleSave() {
    // Validate settings
    if (!settings.apiBase.trim()) {
      alert('API Base URL is required');
      return;
    }
    if (!settings.model.trim()) {
      alert('Model is required');
      return;
    }
    if (settings.temperature < 0 || settings.temperature > 2) {
      alert('Temperature must be between 0 and 2');
      return;
    }
    if (settings.topP < 0 || settings.topP > 1) {
      alert('Top P must be between 0 and 1');
      return;
    }
    if (settings.maxIterations < 1 || settings.maxIterations > 100) {
      alert('Max iterations must be between 1 and 100');
      return;
    }

    onSave?.({ ...settings, apiKey: apiKey || undefined });
    onClose();
  }

  /**
   * Handle export config
   */
  async function handleExport() {
    if (!currentConversation) {
      alert('No active conversation to export');
      return;
    }

    try {
      console.log('[Export] Current conversation:', currentConversation);
      console.log('[Export] Conversation ID:', currentConversation.id);
      console.log('[Export] Conversation ID type:', typeof currentConversation.id);

      const response = await api.transfer.exportConfig(currentConversation.id);
      if (response.success && response.data) {
        // Create download link for ZIP file
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = url;
        // Use .zip extension since backend returns a ZIP file
        a.download = `${currentConversation.name}_config.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to export: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export configuration');
    }
  }

  /**
   * Handle add MCP files
   */
  function handleAddMcpFiles() {
    mcpFileInputRef.current?.click();
  }

  /**
   * Handle MCP file selection
   */
  async function handleMcpFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || !currentConversation) return;

    const fileArray = Array.from(files);

    // Filter valid file types
    const validFiles = fileArray.filter(file =>
      file.name.endsWith('.py') || file.name.endsWith('.json') || file.name.endsWith('.yaml') || file.name.endsWith('.yml')
    );

    if (validFiles.length === 0) {
      alert('No valid files selected. Please select .py, .json, .yaml, or .yml files.');
      return;
    }

    if (validFiles.length < fileArray.length) {
      alert(`Some files were skipped. Only .py, .json, .yaml, and .yml files are supported.`);
    }

    try {
      // Upload files to server
      const response = await api.mcp.uploadTools(currentConversation.id, validFiles);

      if (response.success && response.data) {
        // Add the new paths to settings
        const newPaths = [...settings.mcpPaths];
        for (const path of response.data.paths) {
          if (path && !newPaths.includes(path)) {
            newPaths.push(path);
          }
        }

        updateSetting('mcpPaths', newPaths);

        // Show success message
        alert(`Successfully uploaded ${response.data.uploadedCount} MCP tool(s) to data/${currentConversation.id}/tools/`);
      } else {
        alert(`Failed to upload MCP tools: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Failed to upload MCP tools: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    // Reset the input
    if (mcpFileInputRef.current) {
      mcpFileInputRef.current.value = '';
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" title="Settings">
      <div className="space-y-6 max-h-[60vh] overflow-y-auto">
        {/* API Configuration */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-textTertiary">
            API Configuration
          </h3>

          {/* Provider selection */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
                Provider
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border text-dark-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              >
                {Object.entries(API_PROVIDERS).map(([key, provider]) => (
                  <option key={key} value={key}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
                Model
              </label>
              <select
                value={settings.model}
                onChange={(e) => updateSetting('model', e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border text-dark-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              >
                {API_PROVIDERS[selectedProvider]?.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>

          {/* API Base */}
          <Input
            label="API Base URL"
            value={settings.apiBase}
            onChange={(e) => updateSetting('apiBase', e.target.value)}
            placeholder="https://api.example.com"
          />

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
              API Key
            </label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border text-dark-text placeholder:text-dark-textTertiary focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary pr-20"
                />
                <button
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-dark-textTertiary hover:text-dark-text"
                >
                  {showApiKey ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Model Parameters */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-textTertiary">
            Model Parameters
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Temperature"
              type="number"
              step="0.1"
              min="0"
              max="2"
              value={settings.temperature}
              onChange={(e) => updateSetting('temperature', parseFloat(e.target.value))}
            />

            <Input
              label="Max Tokens"
              type="number"
              min="0"
              value={settings.maxTokens || ''}
              onChange={(e) =>
                updateSetting('maxTokens', e.target.value ? parseInt(e.target.value) : undefined)
              }
            />

            <Input
              label="Top P"
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={settings.topP}
              onChange={(e) => updateSetting('topP', parseFloat(e.target.value))}
            />

            <Input
              label="Presence Penalty"
              type="number"
              step="0.1"
              min="-2"
              max="2"
              value={settings.presencePenalty}
              onChange={(e) => updateSetting('presencePenalty', parseFloat(e.target.value))}
            />
          </div>

          <Input
            label="Frequency Penalty"
            type="number"
            step="0.1"
            min="-2"
            max="2"
            value={settings.frequencyPenalty}
            onChange={(e) => updateSetting('frequencyPenalty', parseFloat(e.target.value))}
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="stream"
              checked={settings.stream}
              onChange={(e) => updateSetting('stream', e.target.checked)}
              className="w-4 h-4 rounded border-dark-border bg-dark-bgTertiary text-primary focus:ring-primary"
            />
            <label htmlFor="stream" className="text-sm font-medium text-dark-text">
              Enable Streaming
            </label>
          </div>
        </section>

        {/* Command Configuration */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-textTertiary">
            Command Configuration
          </h3>

          <Input
            label="Command Start Marker"
            value={settings.commandStart}
            onChange={(e) => updateSetting('commandStart', e.target.value)}
            placeholder="YLDEXECUTE:"
          />

          <Input
            label="Command Separator"
            value={settings.commandSeparator}
            onChange={(e) => updateSetting('commandSeparator', e.target.value)}
            placeholder="￥|"
          />

          <Input
            label="Max Iterations"
            type="number"
            min="1"
            max="100"
            value={settings.maxIterations}
            onChange={(e) => updateSetting('maxIterations', parseInt(e.target.value))}
          />
        </section>

        {/* System Prompt */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-textTertiary">
            System Prompt
          </h3>

          <Textarea
            label="System Prompt"
            value={settings.systemPrompt}
            onChange={(e) => updateSetting('systemPrompt', e.target.value)}
            placeholder="You are a helpful AI assistant..."
            rows={6}
            autoResize={false}
          />
        </section>

        {/* MCP Tools */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-dark-textTertiary">
            MCP Tools
          </h3>

          {/* Display loaded MCP tools */}
          {settings.mcpPaths.length > 0 && (
            <div className="p-3 rounded-lg bg-dark-bgTertiary border border-dark-border space-y-1">
              <p className="text-xs text-dark-textTertiary mb-2">Loaded Tools:</p>
              {settings.mcpPaths.map((path, index) => (
                <div key={index} className="text-xs text-dark-textSecondary font-mono bg-dark-bg px-2 py-1 rounded">
                  {path}
                </div>
              ))}
            </div>
          )}

          {settings.mcpPaths.length === 0 && (
            <div className="p-4 rounded-lg bg-dark-bgTertiary border border-dark-border">
              <p className="text-sm text-dark-textSecondary">
                No MCP tools loaded
              </p>
            </div>
          )}

          {/* Hidden file input */}
          <input
            ref={mcpFileInputRef}
            type="file"
            accept=".py"
            multiple
            className="hidden"
            onChange={handleMcpFileChange}
          />

          <Button
            variant="secondary"
            size="sm"
            fullWidth
            icon={<Upload size={14} />}
            onClick={handleAddMcpFiles}
          >
            Add MCP Files
          </Button>
        </section>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between pt-4 mt-6 border-t border-dark-border">
        <Button
          variant="ghost"
          size="sm"
          icon={<Download size={16} />}
          onClick={handleExport}
        >
          Export Config
        </Button>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            icon={<Save size={16} />}
            onClick={handleSave}
          >
            Save Settings
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default SettingsDialog;
