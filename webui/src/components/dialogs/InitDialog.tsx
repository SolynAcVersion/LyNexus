/**
 * InitDialog Component
 * Initial setup dialog for first-time users
 */

import { useState } from 'react';
import { Modal } from '@components/common/Modal';
import { Input } from '@components/common/Input';
import { Button } from '@components/common/Button';
import { api } from '@services/api';
import { cn } from '../../utils/classnames';
import { Zap } from 'lucide-react';
import { API_PROVIDERS } from '../../types';

// ============================================================================
// Type Definitions
// ============================================================================

interface InitDialogProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  /**
   * Callback when modal is closed
   */
  onClose: () => void;
  /**
   * Callback when setup is complete
   */
  onComplete: (config: {
    apiKey: string;
    apiBase: string;
    model: string;
  }) => void;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * Initial setup dialog
 */
export function InitDialog({ isOpen, onClose, onComplete }: InitDialogProps) {
  const [selectedProvider, setSelectedProvider] = useState<string>('deepseek');
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState('https://api.deepseek.com');
  const [model, setModel] = useState('deepseek-chat');
  const [showApiKey, setShowApiKey] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handle provider change
   */
  function handleProviderChange(providerName: string) {
    setSelectedProvider(providerName);
    const provider = API_PROVIDERS[providerName];
    if (provider) {
      setApiBase(provider.apiBase);
      if (provider.models.length > 0) {
        setModel(provider.models[0]);
      }
    }
  }

  /**
   * Handle complete setup
   */
  async function handleComplete() {
    if (!apiKey.trim()) {
      alert('Please enter an API key');
      return;
    }

    setIsLoading(true);

    // Validate API key
    const response = await api.settings.validateApiKey(apiKey.trim(), apiBase);
    if (!response.success || !response.data) {
      alert('Invalid API key. Please check and try again.');
      setIsLoading(false);
      return;
    }

    setIsLoading(false);
    onComplete({
      apiKey: apiKey.trim(),
      apiBase,
      model,
    });
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" showCloseButton={false}>
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/20 mb-4">
          <Zap className="text-primary" size={32} />
        </div>
        <h2 className="text-2xl font-bold text-dark-text mb-2">
          Welcome to LyNexus AI
        </h2>
        <p className="text-dark-textSecondary">
          Configure your AI assistant to get started
        </p>
      </div>

      <div className="space-y-4">
        {/* Provider selection */}
        <div>
          <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
            API Provider
          </label>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(API_PROVIDERS).map(([key, provider]) => (
              <button
                key={key}
                onClick={() => handleProviderChange(key)}
                className={cn(
                  'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                  selectedProvider === key
                    ? 'bg-primary border-primary text-white'
                    : 'bg-dark-bgTertiary border-dark-border text-dark-text hover:border-dark-textTertiary'
                )}
              >
                {provider.name}
              </button>
            ))}
          </div>
        </div>

        {/* API Base */}
        <Input
          label="API Base URL"
          value={apiBase}
          onChange={(e) => setApiBase(e.target.value)}
          disabled={selectedProvider !== 'custom'}
        />

        {/* Model */}
        <div>
          <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
            Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border text-dark-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          >
            {API_PROVIDERS[selectedProvider]?.models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
            <option value="custom">Custom</option>
          </select>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-dark-textSecondary mb-1.5">
            API Key
          </label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              className="w-full px-4 py-2.5 rounded-lg bg-dark-bgTertiary border border-dark-border text-dark-text placeholder:text-dark-textTertiary focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary pr-20"
            />
            <button
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-primary hover:text-primary-light"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        {/* Start button */}
        <Button
          variant="primary"
          size="lg"
          fullWidth
          isLoading={isLoading}
          onClick={handleComplete}
          className="mt-6"
        >
          Start LyNexus
        </Button>

        <p className="text-xs text-center text-dark-textTertiary">
          Your API key is stored locally and never sent to our servers
        </p>
      </div>
    </Modal>
  );
}

export default InitDialog;
