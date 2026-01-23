/**
 * ToolsList Component
 * Dialog showing available MCP tools with enable/disable toggles
 */

import { useEffect, useState } from 'react';
import { Modal } from '@components/common/Modal';
import { useAppStore } from '../../stores/useAppStore';
import { api } from '../../services/api';
import { Check, X } from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

interface MCPTool {
  name: string;
  description: string;
  enabled: boolean;
  server?: string;
}

interface ToolsListProps {
  isOpen: boolean;
  onClose: () => void;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * MCP Tools list dialog
 */
export function ToolsList({ isOpen, onClose }: ToolsListProps) {
  const { currentConversation } = useAppStore();
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load tools when dialog opens
  useEffect(() => {
    if (isOpen && currentConversation) {
      loadTools();
    }
  }, [isOpen, currentConversation]);

  /**
   * Load MCP tools from backend
   */
  async function loadTools() {
    if (!currentConversation) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.mcp.getTools(currentConversation.id);
      if (response.success && response.data) {
        setTools(response.data);
      } else {
        setError(response.error || 'Failed to load tools');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tools');
    } finally {
      setLoading(false);
    }
  }

  /**
   * Toggle tool enabled state
   */
  async function toggleTool(toolName: string, enabled: boolean) {
    if (!currentConversation) return;

    try {
      const response = await api.mcp.toggleTool(currentConversation.id, toolName, enabled);
      if (response.success) {
        // Update local state
        setTools(tools.map(t =>
          t.name === toolName ? { ...t, enabled } : t
        ));
      } else {
        setError(response.error || 'Failed to update tool');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update tool');
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="MCP Tools">
      <div className="p-4">
        {loading && (
          <div className="text-center text-dark-textSecondary py-8">
            Loading tools...
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {!loading && tools.length === 0 && (
          <div className="text-center text-dark-textSecondary py-8">
            No MCP tools loaded. Add tools via Settings.
          </div>
        )}

        {!loading && tools.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm text-dark-textSecondary mb-4">
              Select which MCP tools should be available to the AI.
            </p>

            {tools.map((tool) => (
              <div
                key={tool.name}
                className="flex items-start gap-3 p-3 rounded-lg border border-dark-border hover:border-dark-textTertiary transition-colors"
              >
                <button
                  onClick={() => toggleTool(tool.name, !tool.enabled)}
                  className={`mt-1 flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                    tool.enabled
                      ? 'bg-primary border-primary text-white'
                      : 'border-dark-border hover:border-dark-textTertiary'
                  }`}
                >
                  {tool.enabled && <Check size={14} />}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="font-medium text-dark-text text-sm">
                    {tool.name}
                  </div>
                  <div className="text-xs text-dark-textSecondary mt-1 break-words">
                    {tool.description}
                  </div>
                  {tool.server && (
                    <div className="text-xs text-dark-textTertiary mt-1">
                      Server: {tool.server}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-dark-border">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-dark-text hover:bg-dark-bgTertiary transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default ToolsList;
