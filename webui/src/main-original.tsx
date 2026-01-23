/**
 * Application Entry Point
 * Main React component initialization
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// ============================================================================
// Render App
// ============================================================================

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

/**
 * Enable hot module replacement in development
 */
if (import.meta.hot) {
  import.meta.hot.accept();
}
