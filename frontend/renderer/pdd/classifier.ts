/**
 * ============================================================================
 * FILE: classifier.ts — Client-side PDD complexity heuristics (F-013)
 * ============================================================================
 *
 * PDD = Part-Driven Design: a structured workflow for multi-part projects.
 * Before sending every message to the LLM, the UI can guess if the user is
 * asking for something simple (one part with dimensions) vs complex (assembly,
 * robot, frame). This mirrors backend logic so frontend tests stay consistent.
 * ============================================================================
 */

/**
 * ComplexityResult — outcome of classifyRequestComplexity().
 */
export interface ComplexityResult {
  // simple: model directly; suggest_pdd: offer /vision workflow.
  classification: "simple" | "suggest_pdd";
  // Human-readable explanation shown in the chat hint.
  reason: string;
}

/** Keywords that suggest multi-part / assembly work. */
const ASSEMBLY_KEYWORDS = ["assembly", "frame", "drone", "robot", "multi-part", "motor mount"];

/** Regex: looks for two numbers with units or × between them (e.g. "100×50 mm"). */
const SIMPLE_DIMENSION_PATTERN = /\d+\s*(mm|cm|m|×|x)\s*\d+/i;

/**
 * classifyRequestComplexity — cheap text heuristics on the user's chat message.
 */
export function classifyRequestComplexity(message: string): ComplexityResult {
  const lower = message.toLowerCase();
  const wordCount = lower.split(/\s+/).length;

  const hasAssemblyCue = ASSEMBLY_KEYWORDS.some((k) => lower.includes(k));
  const hasDimensions = SIMPLE_DIMENSION_PATTERN.test(message);

  // Long vague prompts without dimensions → suggest PDD; assembly words → suggest PDD.
  if (hasAssemblyCue || (wordCount > 12 && !hasDimensions)) {
    return {
      classification: "suggest_pdd",
      reason: "This request spans multiple parts or systems — Part-Driven Design can help structure it.",
    };
  }

  return {
    classification: "simple",
    reason: "Single-part request with enough structure to model directly.",
  };
}

/**
 * buildPddSuggestionActions — buttons the UI can show when PDD is suggested.
 */
export function buildPddSuggestionActions(): Array<{ label: string; command: string }> {
  return [
    { label: "Start with /vision", command: "/vision" },
    { label: "Continue without PDD", command: "Continue without PDD" },
  ];
}
