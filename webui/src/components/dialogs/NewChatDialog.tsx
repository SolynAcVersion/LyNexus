/**
 * NewChatDialog Component
 * Modal for creating a new conversation with custom name
 */

import { useState, useRef, useEffect } from 'react';
import { Modal } from '@components/common/Modal';
import { Input } from '@components/common/Input';
import { Button } from '@components/common/Button';
import { Plus } from 'lucide-react';
import I18n from '@i18n';

// ============================================================================
// Type Definitions
// ============================================================================

interface NewChatDialogProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  /**
   * Callback when modal is closed
   */
  onClose: () => void;
  /**
   * Callback when chat is created
   */
  onCreate: (name: string) => void;
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * New chat dialog for entering conversation name
 */
export function NewChatDialog({ isOpen, onClose, onCreate }: NewChatDialogProps) {
  const [chatName, setChatName] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when dialog opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Reset form when dialog closes
  useEffect(() => {
    if (!isOpen) {
      setChatName('');
    }
  }, [isOpen]);

  /**
   * Handle create chat
   */
  function handleCreate() {
    const trimmedName = chatName.trim();
    if (!trimmedName) {
      alert('Please enter a conversation name');
      return;
    }
    onCreate(trimmedName);
    setChatName('');
    onClose();
  }

  /**
   * Handle key press (Enter to create)
   */
  function handleKeyPress(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      handleCreate();
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" title="New Conversation">
      <div className="space-y-6">
        {/* Name Input */}
        <div>
          <label className="block text-sm font-medium text-dark-textSecondary mb-2">
            Conversation Name
          </label>
          <Input
            ref={inputRef}
            value={chatName}
            onChange={(e) => setChatName(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter conversation name..."
            autoFocus
          />
          <p className="text-xs text-dark-textTertiary mt-2">
            Give your conversation a meaningful name to help you identify it later.
          </p>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-end gap-2 pt-4 mt-6 border-t border-dark-border">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="primary"
          icon={<Plus size={16} />}
          onClick={handleCreate}
          disabled={!chatName.trim()}
        >
          Create Conversation
        </Button>
      </div>
    </Modal>
  );
}

export default NewChatDialog;
