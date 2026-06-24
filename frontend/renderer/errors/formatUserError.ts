/** Central user-facing error formatter (F-026). */

interface StructuredErrorData {
  error_type?: string;
  message?: string;
  suggested_next_steps?: string[];
  details?: Record<string, unknown>;
}

interface ErrorLike {
  message?: string;
  data?: StructuredErrorData;
}

export function formatUserError(err: unknown): string {
  if (!err || typeof err !== "object") {
    return String(err);
  }

  const e = err as ErrorLike;
  const data = e.data;
  const steps = data?.suggested_next_steps ?? [];

  if (data?.error_type === "validation") {
    return (
      "I couldn't turn that into a modeling plan. Try describing a part with dimensions — " +
      "for example: \"Create a 100×50×6 mm plate with 6 mm corner holes.\""
    );
  }
  if (data?.error_type === "configuration") {
    return "LLM is not configured. Set ANTHROPIC_API_KEY in your environment and restart the app.";
  }
  if (data?.error_type === "export") {
    return "This part has no geometry yet. Model the part in chat first, then export again.";
  }
  if (data?.error_type === "slash") {
    return data.message ?? "Invalid slash command. Check usage and try again.";
  }
  if (data?.error_type === "execution" || data?.error_type === "geometry") {
    const base = data.message ?? "Geometry generation failed.";
    if (steps.length === 0) {
      return base;
    }
    return `${base}\n${steps.map((s) => `• ${s}`).join("\n")}`;
  }

  const raw = e.message ?? String(err);
  if (raw.includes("Error invoking remote method")) {
    return "Something went wrong talking to the backend. Try restarting the app.";
  }

  return data?.message ?? raw;
}
