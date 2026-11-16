import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "../api/client";

const fetchMock = vi.fn<typeof fetch>();

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1)!;
  return { url: String(url), init: init!, headers: new Headers(init!.headers) };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  fetchMock.mockReset();
  localStorage.clear();
});

describe("api/client apiRequest", () => {
  it("normalizes leading slashes and parses JSON", async () => {
    fetchMock.mockResolvedValue(Response.json({ ok: true }));

    await expect(apiRequest<{ ok: boolean }>("///algorithms")).resolves.toEqual({ ok: true });
    expect(lastCall().url).toMatch(/[^/]\/algorithms$/);
  });

  it("sets JSON content type for string bodies but not for FormData", async () => {
    fetchMock.mockImplementation(async () => Response.json({}));

    await apiRequest("evaluations", { method: "POST", body: JSON.stringify({ a: 1 }) });
    expect(lastCall().headers.get("Content-Type")).toBe("application/json");

    await apiRequest("upload", { method: "POST", body: new FormData() });
    expect(lastCall().headers.has("Content-Type")).toBe(false);
  });

  it("keeps an explicit Content-Type header", async () => {
    fetchMock.mockImplementation(async () => Response.json({}));
    await apiRequest("x", { method: "POST", body: "a,b", headers: { "Content-Type": "text/csv" } });
    expect(lastCall().headers.get("Content-Type")).toBe("text/csv");
  });

  it("uses the stored token, and an explicit token overrides it", async () => {
    fetchMock.mockImplementation(async () => Response.json({}));
    localStorage.setItem("authToken", "stored-token");

    await apiRequest("history");
    expect(lastCall().headers.get("Authorization")).toBe("Bearer stored-token");

    await apiRequest("history", { token: "explicit-token" });
    expect(lastCall().headers.get("Authorization")).toBe("Bearer explicit-token");
  });

  it("sends no Authorization header for guests", async () => {
    fetchMock.mockImplementation(async () => Response.json({}));
    await apiRequest("algorithms");
    expect(lastCall().headers.has("Authorization")).toBe(false);
  });

  it("still works when localStorage is unavailable", async () => {
    fetchMock.mockResolvedValue(Response.json({ ok: 1 }));
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });
    await expect(apiRequest("algorithms")).resolves.toEqual({ ok: 1 });
    expect(lastCall().headers.has("Authorization")).toBe(false);
  });

  it("returns undefined for 204 No Content", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    await expect(apiRequest("history/run_1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("throws ApiError with backend detail and status", async () => {
    fetchMock.mockResolvedValue(Response.json({ detail: "Run not found" }, { status: 404 }));

    const error = await apiRequest("evaluations/x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ name: "ApiError", message: "Run not found", status: 404 });
  });

  it("uses a status-based message when the error body has no string detail", async () => {
    fetchMock.mockResolvedValueOnce(Response.json({ detail: [{ msg: "x" }] }, { status: 422 }));
    await expect(apiRequest("x")).rejects.toMatchObject({ message: "Request failed (422)", status: 422 });

    fetchMock.mockResolvedValueOnce(new Response("not json", { status: 500 }));
    await expect(apiRequest("x")).rejects.toMatchObject({ message: "Request failed (500)", status: 500 });

    fetchMock.mockResolvedValueOnce(Response.json(null, { status: 503 }));
    await expect(apiRequest("x")).rejects.toMatchObject({ message: "Request failed (503)" });
  });

  it("wraps network failures in a friendly ApiError without status", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const error = await apiRequest("x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBeUndefined();
    expect((error as ApiError).message).toMatch(/Unable to reach the backend/);
  });

  it("rethrows AbortError untouched and forwards the signal", async () => {
    const controller = new AbortController();
    const abort = new DOMException("The operation was aborted.", "AbortError");
    fetchMock.mockRejectedValue(abort);

    await expect(apiRequest("x", { signal: controller.signal })).rejects.toBe(abort);
    expect(lastCall().init.signal).toBe(controller.signal);
  });
});
