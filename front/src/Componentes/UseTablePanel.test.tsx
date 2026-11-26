import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ApiError, getParcelGeometry } from "../api/client";
import type { RubroReferencias, SourceReference, UseTableResponse } from "../types";
import UseTablePanel, {
  OFFICIAL_USE_TABLE_SOURCE,
  RubroReferenciasView,
  UseTableEmptyState,
  UseTableError,
  UseTableResult,
  UseTableResults,
  categoryRows,
  publishParcelGeometry,
  referenciaSections,
  useTableErrorMessage,
  useTableIsEmpty,
} from "./UseTablePanel";

// Only the geometry client is stubbed; the real ApiError stays in place for the error-message tests.
vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, getParcelGeometry: vi.fn() };
});

const source: SourceReference = {
  id: "usig-ciudad-3d", title: "Ciudad 3D — Cuadro de usos",
  publisher: "USIG, Gobierno de la Ciudad de Buenos Aires", url: "https://ciudad3d.buenosaires.gob.ar",
};
const data: UseTableResponse = {
  smp: "013-099-018",
  official_address: "CORRIENTES AV. 2801",
  mix_area: 4,
  categories: [
    { id: 1, name: "Comercial", rubros: [
      { id: 101, name: "1.4. Comercio minorista" },
      { id: 102, name: "1.5. Alimentación en general y gastronomía" },
    ] },
    { id: 2, name: "Servicios", rubros: [{ id: 201, name: "2.1. Servicios" }] },
  ],
  source, limitations: ["Dato de referencia."],
};
const referencias: RubroReferencias = {
  permitido_mixtura_de_usos: ["Comercial permitido"],
  bicicletas: ["Se permite bicicleta"],
  estacionamientos: [],
  cargaydescarga: ["Carga y descarga de 20 a 6 h"],
  observaciones: "Consultar el Cuadro de Usos vigente.",
  source, limitations: ["Sin validación catastral."],
};

describe("cuadro de usos transforms", () => {
  it("categoryRows keeps the official category order, every rubro and its count", () => {
    const rows = categoryRows(data.categories);

    expect(rows.map(row => [row.id, row.name, row.rubroCount])).toEqual([
      [1, "Comercial", 2], [2, "Servicios", 1],
    ]);
    expect(rows[0].rubros.map(rubro => rubro.id)).toEqual([101, 102]);
    expect(categoryRows([])).toEqual([]);
  });

  it("referenciaSections exposes the five official keys in a fixed order, including empty ones", () => {
    const sections = referenciaSections(referencias);

    expect(sections.map(section => section.key)).toEqual([
      "permitido_mixtura_de_usos", "bicicletas", "estacionamientos", "cargaydescarga", "observaciones",
    ]);
    expect(sections.find(section => section.key === "estacionamientos")?.items).toEqual([]);
    expect(sections.find(section => section.key === "cargaydescarga")?.items).toEqual(["Carga y descarga de 20 a 6 h"]);
  });

  it("useTableIsEmpty recognises the outside-CABA result", () => {
    expect(useTableIsEmpty({ ...data, smp: null, official_address: null, mix_area: null, categories: [] })).toBe(true);
    expect(useTableIsEmpty(data)).toBe(false);
  });

  it("shows a clear empty state and lists the backend limitations", () => {
    const html = renderToStaticMarkup(<UseTableEmptyState limitations={["La parcela está fuera de CABA."]} />);

    expect(html).toMatch(/No encontramos la parcela/i);
    expect(html).toContain("La parcela está fuera de CABA.");
    expect(html).toContain("role=\"status\"");
  });

  it("surfaces an ApiError message instead of swallowing the failure", () => {
    const message = useTableErrorMessage(new ApiError("validation", "Revisá el punto consultado."));
    const html = renderToStaticMarkup(<UseTableError message={message} />);

    expect(html).toContain("Revisá el punto consultado.");
    expect(html).toContain("role=\"alert\"");
  });
});

describe("cuadro de usos panel", () => {
  it("without a point it states there is no consultation point instead of inventing parcel data", () => {
    const html = renderToStaticMarkup(<UseTablePanel point={null} />);

    expect(html).toContain("Cuadro de usos");
    expect(html).toMatch(/sin un punto|Sin un punto/i);
    expect(html).not.toContain("013-099-018");
  });

  it("with a point it starts by announcing the official consultation is loading", () => {
    const html = renderToStaticMarkup(<UseTablePanel point={{ lat: -34.604, lng: -58.4055 }} />);

    expect(html).toMatch(/Consultando el cuadro de usos/i);
    expect(html).toContain("role=\"status\"");
  });

  it("shows SMP, official address and mix area from the parcel", () => {
    const html = renderToStaticMarkup(<UseTableResult data={data} />);

    expect(html).toContain("013-099-018");
    expect(html).toContain("CORRIENTES AV. 2801");
    expect(html).toContain("4");
    expect(html).toMatch(/Área de mixtura/i);
  });

  it("renders categories as an accessible accordion with a button per rubro", () => {
    const html = renderToStaticMarkup(<UseTableResult data={data} />);

    expect(html).toContain("aria-expanded=\"false\"");
    expect(html).toContain("aria-controls=\"use-table-rubros-1\"");
    expect(html).toContain("Comercial");
    expect(html).toContain("2 rubros");
    expect(html).toContain("1.5. Alimentación en general y gastronomía");
  });

  it("groups the selected rubro conditions under the five official keys", () => {
    const html = renderToStaticMarkup(<RubroReferenciasView referencias={referencias} />);

    expect(html).toContain("Permitido por mixtura de usos");
    expect(html).toContain("Bicicletas");
    expect(html).toContain("Estacionamientos");
    expect(html).toContain("Carga y descarga");
    expect(html).toContain("Observaciones");
    expect(html).toContain("Carga y descarga de 20 a 6 h");
    expect(html).toContain("Sin validación catastral.");
  });

  it("cites the official source with a link in every panel state", () => {
    const withoutPoint = renderToStaticMarkup(<UseTablePanel point={null} />);
    const loading = renderToStaticMarkup(<UseTablePanel point={{ lat: -34.604, lng: -58.4055 }} />);

    for (const html of [withoutPoint, loading]) {
      expect(html).toContain(source.url);
      expect(html).toContain("USIG");
    }
    expect(OFFICIAL_USE_TABLE_SOURCE).toEqual(source);
  });

  it("states in Spanish that this is reference information, not a cadastral confirmation nor a ruling on the activity", () => {
    const html = renderToStaticMarkup(<UseTablePanel point={null} />) +
      renderToStaticMarkup(<UseTableResult data={data} />);

    expect(html).toMatch(/información de referencia/i);
    expect(html).toMatch(/no (es|constituye) una confirmación catastral/i);
    expect(html).toMatch(/dictamen|juicio/i);
    expect(html).toMatch(/actividad (del|de la persona|que querés hacer)/i);
  });
});

describe("estimated location and visible limitations (S9)", () => {
  it("labels the SMP as estimated and lists the backend limitations next to the parcel facts", () => {
    const limitation = "La ubicación es aproximada; puede corresponder a la parcela vecina.";
    const html = renderToStaticMarkup(<UseTableResult data={{ ...data, limitations: [limitation] }} />);

    expect(html).toMatch(/SMP estimado/i);
    expect(html).toContain(limitation);
    expect(html.indexOf(limitation)).toBeLessThan(html.indexOf("Categorías del cuadro de usos"));
    // RN-04 still lives in the enclosing panel, unchanged and unsoftened.
    expect(renderToStaticMarkup(<UseTablePanel point={null} />)).toContain("No es una confirmación catastral");
  });
});

describe("rubro name filter (S10)", () => {
  function filtered(query: string): string {
    return renderToStaticMarkup(
      <UseTableResults categories={data.categories} query={query} selected={null} onSelect={() => {}} />,
    );
  }

  it("exposes an accessible type=search input in the result", () => {
    const html = renderToStaticMarkup(<UseTableResult data={data} />);

    expect(html).toMatch(/<input[^>]*type="search"/);
    expect(html).toContain('id="use-table-rubro-filter"');
    expect(html).toContain('for="use-table-rubro-filter"');
    expect(html).toMatch(/Filtrar rubros/i);
  });

  it("filters rubros per category, accent- and case-insensitively, keeping order and filtered counts", () => {
    const html = filtered("ALIMENTACION");

    expect(html).toContain("1.5. Alimentación en general y gastronomía");
    expect(html).not.toContain("1.4. Comercio minorista");
    expect(html).not.toContain("2.1. Servicios");
    expect(html).toContain("1 rubro");
    expect(html.indexOf("Comercial")).toBeLessThan(html.indexOf("Servicios"));
  });

  it("shows a per-category empty state and a global one when nothing matches anywhere", () => {
    const partial = filtered("alimentacion");
    expect(partial).toMatch(/Ningún rubro de esta categoría coincide/i);
    expect(partial).not.toMatch(/No hay rubros que coincidan/i);

    const none = filtered("zzz");
    expect(none).toMatch(/No hay rubros que coincidan/i);
    expect(none).toContain('role="status"');
    expect(none).not.toContain("Comercial");
  });
});

describe("real parcel geometry wiring (S12)", () => {
  const geometry: GeoJSON.Geometry = {
    type: "Polygon",
    coordinates: [[[-58.406, -34.605], [-58.405, -34.605], [-58.405, -34.604], [-58.406, -34.605]]],
  };

  it("publishes null geometry and skips the client when the use-table has no SMP", async () => {
    const onGeometry = vi.fn();
    vi.mocked(getParcelGeometry).mockReset();

    await publishParcelGeometry({ ...data, smp: null }, new AbortController().signal, onGeometry);

    expect(onGeometry).toHaveBeenCalledWith(null);
    expect(getParcelGeometry).not.toHaveBeenCalled();
  });

  it("publishes the geometry returned for the resolved SMP", async () => {
    const onGeometry = vi.fn();
    vi.mocked(getParcelGeometry).mockResolvedValueOnce({ geometry, source, limitations: [] });

    await publishParcelGeometry(data, new AbortController().signal, onGeometry);

    expect(getParcelGeometry).toHaveBeenCalledWith("013-099-018", expect.objectContaining({ signal: expect.any(AbortSignal) }));
    expect(onGeometry).toHaveBeenCalledWith(geometry);
  });

  it("skips geometry silently on failure and never fetches after an abort", async () => {
    const onGeometry = vi.fn();
    vi.mocked(getParcelGeometry).mockRejectedValueOnce(new Error("geometry service down"));
    await publishParcelGeometry(data, new AbortController().signal, onGeometry);

    const controller = new AbortController();
    controller.abort();
    vi.mocked(getParcelGeometry).mockClear();
    await publishParcelGeometry(data, controller.signal, onGeometry);

    expect(getParcelGeometry).not.toHaveBeenCalled();
    expect(onGeometry).not.toHaveBeenCalled();
  });
});
