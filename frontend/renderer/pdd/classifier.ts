/** Client-side PDD complexity heuristics (F-013) — mirrors backend classifier for UI tests. */

export interface ComplexityResult {
  classification: "simple" | "suggest_pdd";
  reason: string;
}

const ASSEMBLY_KEYWORDS = ["assembly", "frame", "drone", "robot", "multi-part", "motor mount"];
const SIMPLE_DIMENSION_PATTERN = /\d+\s*(mm|cm|m|×|x)\s*\d+/i;

export function classifyRequestComplexity(message: string): ComplexityResult {
  const lower = message.toLowerCase();
  const wordCount = lower.split(/\s+/).length;

  const hasAssemblyCue = ASSEMBLY_KEYWORDS.some((k) => lower.includes(k));
  const hasDimensions = SIMPLE_DIMENSION_PATTERN.test(message);

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

export function buildPddSuggestionActions(): Array<{ label: string; command: string }> {
  return [
    { label: "Start with /vision", command: "/vision" },
    { label: "Continue without PDD", command: "Continue without PDD" },
  ];
}
