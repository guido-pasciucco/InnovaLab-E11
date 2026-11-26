import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ApiError } from "../api/client";
import type { RubroReferencias, SourceReference, UseTableResponse } from "../types";
import UseTablePanel, {
  OFFICIAL_USE_TABLE_SOURCE,
  RubroReferenciasView,
  UseTableEmptyState,
  UseTableError,
  UseTableResult,
  categoryRows,
  referenciaSections,
  useTableErrorMessage,
  useTableIsEmpty,
} from "./UseTablePanel";

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
