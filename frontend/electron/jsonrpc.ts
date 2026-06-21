/**
 * Transport-agnostic JSON-RPC 2.0 client for the backend stdio bridge.
 *
 * A single instance owns the backend's stdout stream: callers feed it raw chunks
 * via {@link JsonRpcClient.receive} and it routes each NDJSON response to the
 * matching in-flight request by id. This replaces the previous design where each
 * request attached its own stdout listener with its own buffer — which duplicated
 * partial-line state and could mis-route responses once two requests overlapped.
 */

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout> | null;
}

/** An Error augmented with the JSON-RPC error `code`/`data` for the renderer. */
export type RpcError = Error & { code?: number; data?: unknown };

export interface JsonRpcClientOptions {
  /** Write a single framed request line (already newline-terminated) to the backend. */
  send: (line: string) => void;
  /** Per-request timeout in ms; 0 disables timeouts. Defaults to 60000. */
  defaultTimeoutMs?: number;
}

export class JsonRpcClient {
  private buffer = "";
  private nextId = 0;
  private readonly pending = new Map<number, PendingRequest>();
  private closed = false;
  private closedError: Error | null = null;
  private readonly send: (line: string) => void;
  private readonly defaultTimeoutMs: number;

  constructor(options: JsonRpcClientOptions) {
    this.send = options.send;
    this.defaultTimeoutMs = options.defaultTimeoutMs ?? 60000;
  }

  /** True once the backend stream has closed; no further requests can succeed. */
  get isClosed(): boolean {
    return this.closed;
  }

  /**
   * Send a request and resolve with its `result`, or reject with an {@link RpcError}
   * (on a JSON-RPC error), a timeout error, or the close error if the backend is gone.
   */
  request(method: string, params: unknown = {}, timeoutMs?: number): Promise<unknown> {
    if (this.closed) {
      return Promise.reject(this.closedError ?? new Error("Backend process is not running"));
    }

    const id = ++this.nextId;
    const line = JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n";

    return new Promise<unknown>((resolve, reject) => {
      const ms = timeoutMs ?? this.defaultTimeoutMs;
      const timer =
        ms > 0
          ? setTimeout(() => {
              this.pending.delete(id);
              reject(new Error(`JSON-RPC request '${method}' timed out after ${ms}ms`));
            }, ms)
          : null;

      this.pending.set(id, { resolve, reject, timer });

      try {
        this.send(line);
      } catch (err) {
        this.clearPending(id);
        reject(err instanceof Error ? err : new Error(String(err)));
      }
    });
  }

  /** Feed raw stdout bytes/text; complete NDJSON lines are parsed and dispatched. */
  receive(chunk: string | Buffer): void {
    this.buffer += typeof chunk === "string" ? chunk : chunk.toString();
    const lines = this.buffer.split("\n");
    // Keep the trailing partial line (if any) for the next chunk.
    this.buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        continue;
      }

      let message: { id?: unknown; result?: unknown; error?: { code?: number; message?: string; data?: unknown } };
      try {
        message = JSON.parse(trimmed);
      } catch {
        continue; // Ignore non-JSON noise (e.g. stray prints) until a full message arrives.
      }

      if (typeof message.id !== "number") {
        continue; // Notifications / responses without a numeric id we issued.
      }

      const pending = this.pending.get(message.id);
      if (!pending) {
        continue; // Late response to a timed-out/unknown request.
      }
      this.clearPending(message.id);

      if (message.error) {
        const error: RpcError = new Error(message.error.message ?? "JSON-RPC error");
        error.code = message.error.code;
        error.data = message.error.data;
        pending.reject(error);
      } else {
        pending.resolve(message.result);
      }
    }
  }

  /** Mark the backend gone and reject every in-flight request. */
  handleClose(error?: Error): void {
    this.closed = true;
    this.closedError = error ?? new Error("Backend process exited");
    for (const pending of this.pending.values()) {
      if (pending.timer) {
        clearTimeout(pending.timer);
      }
      pending.reject(this.closedError);
    }
    this.pending.clear();
  }

  /** Re-arm the client to serve a freshly respawned backend process. */
  reset(): void {
    this.closed = false;
    this.closedError = null;
    this.buffer = "";
  }

  private clearPending(id: number): void {
    const pending = this.pending.get(id);
    if (pending?.timer) {
      clearTimeout(pending.timer);
    }
    this.pending.delete(id);
  }
}
