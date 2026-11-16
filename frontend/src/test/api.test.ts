import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../lib/api";

const fetchMock = vi.fn<typeof fetch>();

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1)!;
  return { url: String(url), init: init!, headers: new Headers(init!.headers) };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe("lib/api request handling", () => {
  it("posts JSON to /auth/register and returns the body", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ user_id: 1, message: "User registered" }, 201));

    const result = await api.register({ username: "u1", email: "u@x.io", password: "Strong123pw" });

    expect(result).toEqual({ user_id: 1, message: "User registered" });
    const { url, init, headers } = lastCall();
    expect(url).toMatch(/\/auth\/register$/);
    expect(init.method).toBe("POST");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.has("Authorization")).toBe(false);
    expect(JSON.parse(init.body as string)).toEqual({
      username: "u1",
      email: "u@x.io",
      password: "Strong123pw",
    });
  });

  it("sends the bearer token for authenticated calls", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ user_id: 1, username: "u1", email: "u@x.io" }));

    await api.me("tok-123");

    const { url, init, headers } = lastCall();
    expect(url).toMatch(/\/auth\/me$/);
    expect(init.method).toBe("GET");
    expect(headers.get("Authorization")).toBe("Bearer tok-123");
    expect(headers.has("Content-Type")).toBe(false);
  });

  it("URL-encodes run ids for history lookups", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ run_id: "a/b" }));
    await api.historyEntry("a/b c", "tok");
    expect(lastCall().url).toMatch(/\/history\/a%2Fb%20c$/);
  });

  it("logs out with POST and the token", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ message: "Logged out" }));
    await expect(api.logout("tok")).resolves.toEqual({ message: "Logged out" });
    expect(lastCall().init.method).toBe("POST");
  });

  it("prefers a string `detail` from the backend as the error message", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Invalid credentials" }, 401));
    await expect(api.login({ identifier: "u", password: "p" })).rejects.toThrow("Invalid credentials");
  });

  it("formats the first field-level validation error", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: "INVALID_REQUEST",
            message: "Invalid or missing fields",
            fields: [{ field: "email", message: "value is not a valid email address" }],
          },
        },
        400,
      ),
    );
    await expect(api.register({ username: "u1", email: "bad", password: "x" })).rejects.toThrow(
      "email: value is not a valid email address",
    );
  });

  it("labels unnamed field errors as Input", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ error: { fields: [{ message: "bad" }] } }, 400));
    await expect(api.me("t")).rejects.toThrow("Input: bad");
  });

  it("falls back to the generic error envelope message", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ error: { message: "Something failed" } }, 500));
    await expect(api.me("t")).rejects.toThrow("Something failed");
  });

  it("uses a default message for non-JSON error bodies", async () => {
    fetchMock.mockResolvedValue(new Response("<html>502</html>", { status: 502 }));
    await expect(api.me("t")).rejects.toThrow("The request could not be completed.");
  });

  it("ignores non-string detail values", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: [{ msg: "x" }] }, 422));
    await expect(api.me("t")).rejects.toThrow("The request could not be completed.");
  });

  it("reports an unreachable server", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api.me("t")).rejects.toThrow(/Cannot reach the server/);
  });
});

describe("lib/api downloadReport", () => {
  it("returns a blob and sends the token when present", async () => {
    fetchMock.mockResolvedValue(new Response("a,b\n1,2", { status: 200 }));

    const blob = await api.downloadReport("run_1", "csv", "tok");

    expect(await blob.text()).toBe("a,b\n1,2");
    const { url, headers } = lastCall();
    expect(url).toMatch(/\/reports\/run_1\/csv$/);
    expect(headers.get("Authorization")).toBe("Bearer tok");
  });

  it("omits Authorization for guests", async () => {
    fetchMock.mockResolvedValue(new Response("%PDF", { status: 200 }));
    await api.downloadReport("run_1", "pdf", null);
    expect(lastCall().headers.has("Authorization")).toBe(false);
    expect(lastCall().url).toMatch(/\/reports\/run_1\/pdf$/);
  });

  it("surfaces backend errors", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: "Reports are available after the evaluation is completed" }, 409),
    );
    await expect(api.downloadReport("run_1", "csv")).rejects.toThrow(/after the evaluation is completed/);
  });

  it("uses envelope or default messages when detail is missing", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ error: { message: "Envelope error" } }, 500));
    await expect(api.downloadReport("r", "csv")).rejects.toThrow("Envelope error");

    fetchMock.mockResolvedValueOnce(new Response("oops", { status: 500 }));
    await expect(api.downloadReport("r", "csv")).rejects.toThrow("The report could not be downloaded.");
  });

  it("reports an unreachable server", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api.downloadReport("r", "pdf")).rejects.toThrow(/Cannot reach the server/);
  });
});
