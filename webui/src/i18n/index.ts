/**
 * i18n Internationalization
 * Provides multi-language support for the application
 */

export const translations = {
  en: {
    // General
    app_name: "Lynexus",
    status_connected: "Connected",
    status_not_connected: "Not connected",
    tools_available: "tools available",

    // Buttons
    send: "Send",
    settings: "Settings",
    save_settings: "Save Settings",
    save_as_config: "Export Config",
    import_config: "Import Config",
    import_config_file: "Import Settings",
    cancel: "Cancel",
    initialize: "Initialize",
    load_config: "Load Config",
    tools: "Tools",
    new_chat: "New Chat",
    clear_chat: "Clear Chat",
    export_chat: "Export Chat",
    delete_chat: "Delete Chat",
    stop: "Stop",

    // Dialogs
    initial_setup: "Initial Setup",
    setup_title: "Lynexus AI Assistant Setup",
    setup_desc: "Configure your AI assistant to get started",
    select_mcp_files: "Select MCP Files",
    start_lynexus: "Start Lynexus",
    load_config_file: "Load Config",
    confirm_delete: "Confirm Delete",
    confirm_delete_message: 'Are you sure you want to delete chat "{0}"?',
    warning: "Warning",
    cannot_switch_during_process: "Please wait for the current response to complete before switching conversations.",
    invalid_zip_format: "Invalid Archive Format",
    invalid_zip_message: "The ZIP file must contain a single folder with settings.json and tools/ directory inside.",

    // Messages
    type_message: "Type your message here...",
    conversations: "Conversations",
    quick_actions: "Quick Actions",

    // Chat names
    chat: "Chat",
    general_chat: "Chat 1",
  },
  zh: {
    // General
    app_name: "Lynexus",
    status_connected: "已连接",
    status_not_connected: "未连接",
    tools_available: "个工具可用",

    // Buttons
    send: "发送",
    settings: "设置",
    save_settings: "保存设置",
    save_as_config: "导出配置",
    import_config: "导入配置",
    cancel: "取消",
    initialize: "初始化",
    load_config: "加载配置",
    tools: "工具",
    new_chat: "新建对话",
    clear_chat: "清空对话",
    export_chat: "导出对话",
    delete_chat: "删除聊天",
    stop: "停止",

    // Dialogs
    initial_setup: "初始设置",
    setup_title: "Lynexus AI 助手设置",
    setup_desc: "配置你的AI助手以开始使用",
    select_mcp_files: "选择MCP文件",
    start_lynexus: "启动 Lynexus",
    load_config_file: "加载配置",
    confirm_delete: "确认删除",
    confirm_delete_message: '确定要删除聊天 "{0}" 吗？',
    warning: "警告",
    cannot_switch_during_process: "请等待当前响应完成后再切换对话。",
    invalid_zip_format: "无效的压缩包格式",
    invalid_zip_message: "ZIP 文件必须包含一个文件夹，其中包含 settings.json 和 tools/ 目录。",

    // Messages
    type_message: "在此输入消息...",
    conversations: "对话列表",
    quick_actions: "快速操作",

    // Chat names
    chat: "对话",
    general_chat: "对话 1",
  },
} as const;

type Language = keyof typeof translations;
type TranslationKey = keyof typeof translations.en;

let currentLanguage: Language = 'en';

/**
 * i18n class for managing translations
 */
export class I18n {
  /**
   * Set the current language
   */
  static setLanguage(lang: Language) {
    if (lang in translations) {
      currentLanguage = lang;
      // Save to localStorage
      localStorage.setItem('lynexus-language', lang);
    }
  }

  /**
   * Get the current language
   */
  static getLanguage(): Language {
    return currentLanguage;
  }

  /**
   * Get translation for a key
   */
  static tr(key: TranslationKey): string {
    return translations[currentLanguage][key] || translations.en[key] || key;
  }

  /**
   * Get translation with parameters
   */
  static trp(key: TranslationKey, params: Record<string, string>): string {
    let text = this.tr(key);
    // Replace {0}, {1}, etc. with params
    Object.keys(params).forEach((paramKey) => {
      text = text.replace(`{${paramKey}}`, params[paramKey]);
    });
    return text;
  }

  /**
   * Initialize i18n from localStorage or browser language
   */
  static init() {
    const savedLang = localStorage.getItem('lynexus-language') as Language;
    if (savedLang && savedLang in translations) {
      currentLanguage = savedLang;
    } else {
      // Detect browser language
      const browserLang = navigator.language.split('-')[0] as Language;
      currentLanguage = browserLang in translations ? browserLang : 'en';
    }
  }

  /**
   * Get supported languages
   */
  static getSupportedLanguages(): Language[] {
    return Object.keys(translations) as Language[];
  }
}

// Initialize on load
if (typeof window !== 'undefined') {
  I18n.init();
}

export default I18n;
