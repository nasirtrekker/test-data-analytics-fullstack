/**
 * Application entry point - React 18 DOM bootstrap.
 * 
 * This file:
 * 1. Initializes React DOM root
 * 2. Mounts App component into #app element
 * 3. Enables StrictMode for development warnings
 * 4. Loads main CSS styles
 * 
 * Vite Configuration:
 * - Entry: frontend/src/main.tsx
 * - Output: Optimized ES module bundle
 * - HMR: Fast refresh on file changes
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
