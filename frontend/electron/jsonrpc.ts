/**
 * ============================================================================
 * FILE: jsonrpc.ts — JSON-RPC 2.0 client for the Python backend (stdio)
 * ============================================================================
 *
 * The Python backend speaks JSON-RPC over stdin/stdout: one JSON object per line
 * (NDJSON). This class:
 *   - Sends requests with incrementing numeric ids
 *   - Buffers partial stdout chunks until full lines arrive
 *   - Routes each response to the correct in-flight Promise by id
 *   - Handles timeouts and backend process death
 *
 * One JsonRpcClient instance owns the entire stdout stream (main.ts wires it).
 * ============================================================================
 */

/** Internal bookkeeping for a request waiting for a matching response line. */
interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout> | null;
}

/**
 * RpcError — normal JavaScript Error plus optional JSON-RPC code and data payload.
 * The renderer uses data for user-friendly error messages.
 */
export type RpcError = Error & { code?: number; data?: unknown };

/** Constructor options for JsonRpcClient. */
export interface JsonRpcClientOptions {
  /** Called to write one newline-terminated request line to backend stdin. */
  send: (line: string) => void;
  /** Per-request timeout in milliseconds; 0 disables timeouts. Default 60000. */
  defaultTimeoutMs?: number;
}

/**
 * JsonRpcClient — transport-agnostic JSON-RPC client (stdio in production).
 */
export class JsonRpcClient {
  // Incomplete line left over from the last stdout chunk.
  private buffer = "";
  // Monotonically increasing request id (JSON-RPC requires matching id in response).
  private nextId = 0;
  // Map from request id → Promise settle functions.
  private readonly pending = new Map<number, PendingRequest>();
  // After handleClose(), no new requests succeed.
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
   * request — send a JSON-RPC call and return a Promise for its result.
   *
   * Rejects on JSON-RPC error object, timeout, send failure, or if backend closed.
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

  /**
   * receive — feed raw stdout bytes/text from the backend child process.
   * Complete NDJSON lines are parsed and dispatched to pending requests.
   */
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

      let message: {
        id?: unknown;
        result?: unknown;
        error?: { code?: number; message?: string; data?: unknown };
      };
      try {
        message = JSON.parse(trimmed);
      } catch {
        // Ignore non-JSON noise (e.g. stray prints) until a full message arrives.
        continue;
      }

      if (typeof message.id !== "number") {
        // Notifications / responses without a numeric id we issued.
        continue;
      }

      const pending = this.pending.get(message.id);
      if (!pending) {
        // Late response to a timed-out or unknown request.
        continue;
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

  /** handleClose — backend process exited; reject every in-flight request. */
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

  /** reset — clear closed state when main process spawns a fresh backend child. */
  reset(): void {
    this.closed = false;
    this.closedError = null;
    this.buffer = "";
  }

  /** clearPending — remove one id from the pending map and clear its timeout. */
  private clearPending(id: number): void {
    const pending = this.pending.get(id);
    if (pending?.timer) {
      clearTimeout(pending.timer);
    }
    this.pending.delete(id);
  }
}
