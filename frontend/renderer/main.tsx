/**
 * ============================================================================
 * FILE: main.tsx — Application entry point (where the UI first starts)
 * ============================================================================
 *
 * This file is the very first TypeScript/React code that runs when you open
 * CopilotCAD's main window. Think of it as "pressing the power button" on the
 * user interface: it finds an empty HTML container on the page and mounts
 * (attaches) the full React application inside it.
 *
 * CopilotCAD is an Electron desktop app. Electron shows a web page; this file
 * runs inside that page and turns it into an interactive React UI.
 * ============================================================================
 */

// Import the React library. React is a tool for building user interfaces out of
// reusable pieces called "components". We need the React namespace for
// <React.StrictMode> below.
import React from "react";

// Import createRoot from react-dom/client. "DOM" means the live HTML page in
// the browser (or Electron window). createRoot is the modern API that connects
// a React component tree to a real HTML element on the page.
import { createRoot } from "react-dom/client";

// Import our top-level App component from ./app (the file app.tsx in this
// folder). App contains the full layout: panels, chat, viewport, etc.
import App from "./app";

// document is the browser's representation of the HTML page. getElementById
// searches for an element whose id attribute is "root". That element is defined
// in frontend/index.html — an empty div where React will render everything.
const root = document.getElementById("root");

// Only run the startup code if we actually found the #root element. If index.html
// were misconfigured and had no #root, root would be null and we skip rendering
// instead of crashing.
if (root) {
  // createRoot(root) creates a React "root" tied to that DOM node. .render(...)
  // draws our component tree into the page. Everything visible in the UI flows
  // from this single call.
  createRoot(root).render(
    // StrictMode is a React development helper. It intentionally runs some code
    // twice in development to surface bugs. It does not change production behavior.
    <React.StrictMode>
      {/* App is our entire application UI — sidebars, 3D viewport, chat, etc. */}
      <App />
    </React.StrictMode>,
  );
}
