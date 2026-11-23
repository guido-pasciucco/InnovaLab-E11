import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, searchAddresses, suggestActivities } from "./client";
import { describeError } from "./errors";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
  throw new Error("expected the request to fail");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("API errors", () => {
  it("reads code and request id from the error body and shows the mapped message, not the raw detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(503, {
      code: "PROCEDURES_LOADING", request_id: "abc123", detail: "texto técnico",
    })));

    const error = await caught(suggestActivities("peluquería"));

    expect(error.kind).toBe("http");
    expect(error.status).toBe(503);
    expect(error.code).toBe("PROCEDURES_LOADING");
    expect(error.requestId).toBe("abc123");
    expect(describeError(error)).toBe("Estamos cargando los trámites, volvé a intentar.");
  });

  it("falls back to the X-Request-ID header and never shows a 422 body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(422,
      { detail: [{ type: "string_pattern_mismatch", loc: ["query", "query"] }] }, { "X-Request-ID": "hdr-1" })));

    const error = await caught(suggestActivities("peluquería"));

    expect(error.code).toBeNull();
    expect(error.requestId).toBe("hdr-1");
    expect(describeError(error)).toBe("Revisá los datos ingresados: hay un valor que no es válido.");
  });

  it("tells a network failure apart", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = await caught(searchAddresses("Corrientes 2500"));

    expect(error.kind).toBe("network");
    expect(describeError(error)).toBe("Sin conexión. Revisá tu internet e intentá de nuevo.");
  });

  it("treats a cancelled request as nothing to show", async () => {
    vi.stubGlobal("fetch", vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    })));
    const controller = new AbortController();

    const pending = caught(searchAddresses("Corrientes 2500", { signal: controller.signal }));
    controller.abort();
    const error = await pending;

    expect(error.kind).toBe("aborted");
    expect(describeError(error)).toBeNull();
  });

  it("turns a request that never answers into a timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    })));

    const pending = caught(searchAddresses("Corrientes 2500"));
    await vi.advanceTimersByTimeAsync(90_000);
    const error = await pending;

    expect(error.kind).toBe("timeout");
    expect(describeError(error)).toBe("El servicio está tardando demasiado en responder. Intentá de nuevo en unos segundos.");
  });
});

describe("requests below the thresholds are not sent", () => {
  it.each([
    ["empty activity", () => suggestActivities(""), "Escribí la actividad que querés realizar."],
    ["one-character activity", () => suggestActivities("a"), "Escribí al menos 2 caracteres."],
    ["blank activity", () => suggestActivities("   "), "Escribí algo más que espacios."],
    ["activity over 100", () => suggestActivities("x".repeat(101)), "Usá como máximo 100 caracteres."],
    ["activities limit 0", () => suggestActivities("peluquería", { limit: 0 }), "La cantidad de resultados tiene que estar entre 1 y 10."],
    ["activities limit 11", () => suggestActivities("peluquería", { limit: 11 }), "La cantidad de resultados tiene que estar entre 1 y 10."],
    ["two-character address", () => searchAddresses("ab"), "Escribí al menos 3 caracteres."],
    ["blank address", () => searchAddresses("   "), "Escribí algo más que espacios."],
    ["addresses limit 11", () => searchAddresses("Corrientes 2500", { limit: 11 }), "La cantidad de resultados tiene que estar entre 1 y 10."],
  ])("%s", async (_name, call, message) => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const error = await caught(call());

    expect(error.kind).toBe("validation");
    expect(describeError(error)).toBe(message);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("trims the text before sending it", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { activities: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await suggestActivities("  pe  ", { limit: 10 });

    const url = new URL(fetchMock.mock.calls[0][0] as string, "http://localhost");
    expect(url.searchParams.get("query")).toBe("pe");
    expect(url.searchParams.get("limit")).toBe("10");
  });
});
