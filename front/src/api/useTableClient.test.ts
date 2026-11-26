import { afterEach, describe, expect, it, vi } from "vitest";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

/** The committed .env enables mock mode, so every case loads the client with an explicit env. */
async function api(mock: "true" | "false") {
  vi.stubEnv("VITE_USE_MOCK_API", mock);
  vi.resetModules();
  return import("./client");
}

async function caught(promise: Promise<unknown>): Promise<{ kind: string; code: string | null }> {
  try {
    await promise;
  } catch (error) {
    const candidate = error as Error & { kind?: string; code?: string | null };
    if (candidate instanceof Error && typeof candidate.kind === "string") return candidate as never;
    throw error;
  }
  throw new Error("expected the request to fail");
}

const point = { lat: -34.604, lng: -58.4055 };
const source = { id: "usig-ciudad-3d", title: "Ciudad 3D — Cuadro de usos", publisher: "USIG, Gobierno de la Ciudad de Buenos Aires", url: "https://ciudad3d.buenosaires.gob.ar" };
const useTable = {
  smp: "013-099-018", official_address: "CORRIENTES AV. 2801", mix_area: 4,
  categories: [{ id: 1, name: "Comercial", rubros: [{ id: 102, name: "1.5. Alimentación en general y gastronomía" }] }],
  source, limitations: [],
};
const referencias = {
  permitido_mixtura_de_usos: ["Permitido"], bicicletas: ["1 bicicleta"], estacionamientos: [],
  cargaydescarga: ["20 a 6 h"], observaciones: null, source, limitations: [],
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.useRealTimers();
  vi.resetModules();
});

describe("territory API clients", () => {
  it("getUseTable sends lat/lng through the shared request helper and returns the wire shape", async () => {
    const { getUseTable } = await api("false");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, useTable));
    vi.stubGlobal("fetch", fetchMock);

    expect(await getUseTable(point)).toEqual(useTable);

    const url = new URL(fetchMock.mock.calls[0][0] as string, "http://localhost");
    expect(url.pathname).toBe("/api/territory/use-table");
    expect(url.searchParams.get("lat")).toBe("-34.604");
    expect(url.searchParams.get("lng")).toBe("-58.4055");
    expect(fetchMock.mock.calls[0][1].headers["Content-Type"]).toBe("application/json");
  });

  it("getUseTable forwards AbortSignal and surfaces cancellation as an ApiError", async () => {
    const { getUseTable } = await api("false");
    vi.stubGlobal("fetch", vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    })));
    const controller = new AbortController();

    const pending = caught(getUseTable(point, { signal: controller.signal }));
    controller.abort();
    const error = await pending;

    expect(error.kind).toBe("aborted");
  });

  it("getRubroReferencias sends all four parameters and maps upstream errors to ApiError", async () => {
    const { getRubroReferencias } = await api("false");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, referencias));
    vi.stubGlobal("fetch", fetchMock);

    expect(await getRubroReferencias({ smp: "013-099-018", categoria: 1, mixtura: 4, rubro: 102 })).toEqual(referencias);
    const url = new URL(fetchMock.mock.calls[0][0] as string, "http://localhost");
    expect(url.pathname).toBe("/api/territory/rubro-referencias");
    expect(url.searchParams.get("smp")).toBe("013-099-018");
    expect(url.searchParams.get("categoria")).toBe("1");
    expect(url.searchParams.get("mixtura")).toBe("4");
    expect(url.searchParams.get("rubro")).toBe("102");

    fetchMock.mockResolvedValue(jsonResponse(503, { code: "TERRITORY_UNAVAILABLE" }));
    const error = await caught(getRubroReferencias({ smp: "013-099-018", categoria: 1, mixtura: 4, rubro: 102 }));
    expect(error.kind).toBe("http");
    expect(error.code).toBe("TERRITORY_UNAVAILABLE");
  });

  it("mock mode returns an honest empty use table with a limitation and no fake rubros", async () => {
    const { getUseTable } = await api("true");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const data = await getUseTable(point);

    expect(data.smp).toBeNull();
    expect(data.official_address).toBeNull();
    expect(data.mix_area).toBeNull();
    expect(data.categories).toEqual([]);
    expect(data.limitations.join(" ")).toMatch(/demostración/i);
    expect(data.source.url).toBe(source.url);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("mock mode returns empty referencias with a limitation, never invented conditions", async () => {
    const { getRubroReferencias } = await api("true");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const data = await getRubroReferencias({ smp: "013-099-018", categoria: 1, mixtura: 4, rubro: 102 });

    expect(data.permitido_mixtura_de_usos).toEqual([]);
    expect(data.bicicletas).toEqual([]);
    expect(data.estacionamientos).toEqual([]);
    expect(data.cargaydescarga).toEqual([]);
    expect(data.observaciones).toBeNull();
    expect(data.limitations.join(" ")).toMatch(/demostración/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("preserves the existing address search: validation, URL and response parsing", async () => {
    const { searchAddresses } = await api("false");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { addresses: [] }));
    vi.stubGlobal("fetch", fetchMock);

    expect(await searchAddresses("Corrientes 2500")).toEqual({ addresses: [] });
    const url = new URL(fetchMock.mock.calls[0][0] as string, "http://localhost");
    expect(url.pathname).toBe("/api/geolocation/addresses");
    expect(url.searchParams.get("address")).toBe("Corrientes 2500");
    expect(url.searchParams.get("limit")).toBe("5");
    expect((await caught(searchAddresses("ab"))).kind).toBe("validation");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
