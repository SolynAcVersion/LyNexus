/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Telegram-inspired dark theme colors
        primary: {
          DEFAULT: '#4A9CFF',
          hover: '#5AACFF',
          active: '#3A8CEE',
          light: '#7EB8FF',
        },
        dark: {
          bg: '#1E1E1E',
          bgSecondary: '#252525',
          bgTertiary: '#2D2D2D',
          border: '#333333',
          text: '#E0E0E0',
          textSecondary: '#AAAAAA',
          textTertiary: '#888888',
        },
        message: {
          user: '#0084FF',
          ai: '#2D2D2D',
          command: '#1A5F1A',
          commandResult: '#2A4A6A',
          summary: '#4A2A6A',
          error: '#6A2A2A',
          info: '#2A4A4A',
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'Microsoft YaHei', 'sans-serif'],
      },
      borderRadius: {
        'message': '18px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
