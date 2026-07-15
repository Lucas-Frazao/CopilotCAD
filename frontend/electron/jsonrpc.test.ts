/**
 * ============================================================================
 * FILE: jsonrpc.test.ts — Unit tests for JsonRpcClient routing and edge cases
 * ============================================================================
 *
 * Tests run in Vitest without a real Python process. A fake `send` captures
 * outgoing requests; tests call `receive` with synthetic stdout lines to simulate
 * the backend. Covers concurrent ids, chunked lines, errors, close, and timeout.
 * ============================================================================
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import { JsonRpcClient } from "./jsonrpc";

/** Shape of a parsed outbound JSON-RPC request line. */
interface SentRequest {
  id: number;
  method: string;
  params: unknown;
}

/** Build a client whose send pushes parsed requests into `sent` for assertions. */
function makeClient() {
  const sent: SentRequest[] = [];
  const client = new JsonRpcClient({
    send: (line: string) => sent.push(JSON.parse(line) as SentRequest),
    defaultTimeoutMs: 1000,
  });
  return { client, sent };
}

/** Simulate one line of backend stdout with a successful result. */
function respond(client: JsonRpcClient, id: number, result: unknown): void {
  client.receive(JSON.stringify({ jsonrpc: "2.0", id, result }) + "\n");
}

describe("JsonRpcClient", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("routes concurrent responses to the correct request by id", async () => {
    const { client, sent } = makeClient();
    const first = client.request("a");
    const second = client.request("b");

    expect(sent.map((r) => r.id)).toEqual([1, 2]);

    // Respond out of order: second request resolves first.
    respond(client, 2, "result-b");
    respond(client, 1, "result-a");

    await expect(first).resolves.toBe("result-a");
    await expect(second).resolves.toBe("result-b");
  });

  it("reassembles a response split across multiple data chunks", async () => {
    const { client } = makeClient();
    const pending = client.request("ping");

    const full = JSON.stringify({ jsonrpc: "2.0", id: 1, result: "pong" }) + "\n";
    client.receive(full.slice(0, 10));
    client.receive(full.slice(10));

    await expect(pending).resolves.toBe("pong");
  });

  it("ignores non-JSON and unknown-id lines without disrupting pending requests", async () => {
    const { client } = makeClient();
    const pending = client.request("ping");

    client.receive("not json at all\n");
    client.receive(JSON.stringify({ jsonrpc: "2.0", id: 999, result: "stray" }) + "\n");
    respond(client, 1, "pong");

    await expect(pending).resolves.toBe("pong");
  });

  it("rejects with an Error carrying code and data on a JSON-RPC error", async () => {
    const { client } = makeClient();
    const pending = client.request("boom");

    client.receive(
      JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        error: { code: -32603, message: "kaboom", data: { error_type: "validation" } },
      }) + "\n",
    );

    await expect(pending).rejects.toMatchObject({
      message: "kaboom",
      code: -32603,
      data: { error_type: "validation" },
    });
  });

  it("rejects pending requests when the backend closes", async () => {
    const { client } = makeClient();
    const pending = client.request("ping");

    client.handleClose(new Error("backend exited"));

    await expect(pending).rejects.toThrow(/backend exited/);
  });

  it("rejects immediately once closed", async () => {
    const { client } = makeClient();
    client.handleClose();
    await expect(client.request("ping")).rejects.toThrow();
  });

  it("times out a request that never receives a response", async () => {
    vi.useFakeTimers();
    const { client } = makeClient();
    const pending = client.request("slow", {}, 50);
    const assertion = expect(pending).rejects.toThrow(/timed out/);
    await vi.advanceTimersByTimeAsync(60);
    await assertion;
  });
});
