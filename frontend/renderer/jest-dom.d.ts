// Registers @testing-library/jest-dom matchers (e.g. toBeInTheDocument) on
// vitest's Assertion type so `tsc` type-checks test files. The runtime import
// lives in vitest.setup.ts; this declaration makes the augmentation visible to
// the compiler, which only includes files under renderer/.
import "@testing-library/jest-dom/vitest";
