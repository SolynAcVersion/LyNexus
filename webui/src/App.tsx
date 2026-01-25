/**
 * Main App Component
 * Root component that orchestrates all UI elements
 */

import { useEffect, useState } from 'react';
import { ConversationList } from '@components/sidebar/ConversationList';
import { ChatArea } from '@components/sidebar/ChatArea';
import { SettingsDialog } from '@components/dialogs/SettingsDialog';
import { InitDialog } from '@components/dialogs/InitDialog';
import { ToolsList } from '@components/dialogs/ToolsList';
import { SplashScreen } from '@components/dialogs/SplashScreen';
import { useAppStore } from '@stores/useAppStore';
import { api } from '@services/api';
import { cn } from '@utils/classnames';

// ============================================================================
// Main Component
// ============================================================================

/**
 * Root application component
 */
export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [splashProgress, setSplashProgress] = useState(0);

  const {
    conversations,
    currentConversation,
    showSettings,
    showToolsList,
    showInitDialog,
    loadConversations,
    closeSettings,
    closeInitDialog,
    createConversation,
    setCurrentConversation,
  } = useAppStore();

  /**
   * Initialize app on mount
   */
  useEffect(() => {
    async function initialize() {
      // Simulate loading progress
      for (let i = 0; i <= 100; i += 10) {
        setSplashProgress(i);
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      // Load conversations
      await loadConversations();

      // Hide splash screen
      setTimeout(() => {
        setShowSplash(false);
      }, 500);
    }

    initialize();
  }, []);

  /**
   * Set current conversation after conversations load
   */
  useEffect(() => {
    if (conversations.length > 0 && !currentConversation) {
      setCurrentConversation(conversations[0]);
    }
  }, [conversations, currentConversation]);

  /**
   * Handle init dialog complete
   */
  async function handleInitComplete(config: {
    apiKey: string;
    apiBase: string;
    model: string;
  }) {
    // Save configuration to current conversation
    if (currentConversation) {
      const settings = {
        apiKey: config.apiKey,
        apiBase: config.apiBase,
        model: config.model,
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
      };

      const response = await api.settings.update(currentConversation.id, settings);
      if (response.success && response.data) {
        // Update current conversation settings
        const updatedConversation = {
          ...currentConversation,
          settings: response.data,
        };
        setCurrentConversation(updatedConversation);
        useAppStore.getState().updateConversation(currentConversation.id, {
          settings: response.data,
        });
      }
    }

    closeInitDialog();
  }

  /**
   * Handle settings save
   */
  async function handleSettingsSave(settings: any) {
    if (!currentConversation) {
      console.error('No active conversation to save settings');
      return;
    }

    // Save settings to backend
    const response = await api.settings.update(currentConversation.id, settings);
    if (response.success && response.data) {
      // Reload conversations to ensure sync with backend
      await loadConversations();

      // Update current conversation with reloaded data
      const { conversations } = useAppStore.getState();
      const updatedConversation = conversations.find(c => c.id === currentConversation.id);
      if (updatedConversation) {
        setCurrentConversation(updatedConversation);
      }
    } else {
      console.error('Failed to save settings:', response.error);
      alert('Failed to save settings: ' + (response.error || 'Unknown error'));
    }
  }

  return (
    <>
      {/* Splash Screen */}
      <SplashScreen
        isVisible={showSplash}
        progress={splashProgress}
        onComplete={() => setShowSplash(false)}
      />

      {/* Init Dialog */}
      <InitDialog
        isOpen={showInitDialog}
        onClose={() => useAppStore.getState().closeInitDialog()}
        onComplete={handleInitComplete}
      />

      {/* Main App */}
      <div
        className={cn(
          'flex h-screen overflow-hidden bg-dark-bg text-dark-text',
          'transition-opacity duration-500',
          showSplash && 'opacity-0'
        )}
      >
        {/* Sidebar */}
        <ConversationList
          className={cn(
            'transition-all duration-300',
            useAppStore.getState().isSidebarOpen ? 'w-80' : 'w-0'
          )}
        />

        {/* Chat Area */}
        <ChatArea className="flex-1" />
      </div>

      {/* Settings Dialog */}
      <SettingsDialog
        isOpen={showSettings}
        onClose={closeSettings}
        onSave={handleSettingsSave}
      />

      {/* Tools List Dialog */}
      <ToolsList
        isOpen={showToolsList}
        onClose={() => useAppStore.getState().closeToolsList()}
      />
    </>
  );
}
