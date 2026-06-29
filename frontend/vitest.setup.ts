/**
 * ============================================================================
 * FILE: vitest.setup.ts — Runs once before all frontend unit tests
 * ============================================================================
 *
 * Vitest is the test runner for the frontend (like pytest for Python). This
 * "setup" file runs automatically before any test file. We use it to register
 * extra matchers from @testing-library/jest-dom so tests can write things like
 * expect(element).toBeInTheDocument() instead of only basic equality checks.
 * ============================================================================
 */

// Side-effect import: we do not assign the result to a variable. Importing this
// module patches Vitest's expect() with DOM-focused assertions (visible, enabled,
// has text, etc.) used throughout frontend/renderer/**/*.test.tsx files.
import "@testing-library/jest-dom/vitest";
