import { createElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import MapPanel, {
  MapLegend,
  ParcelGeometryLayer,
  REAL_PARCEL_STYLE,
  demoLayerOptions,
  visibleDemoLayerIds,
} from "./MapPanel";

// jsdom/RTL are not installed: render on the server with the Leaflet boundary replaced.
// The assertions cover the pre-existing controls, legend and hint that must not change.
vi.mock("leaflet", () => {
  function Marker() {}
  (Marker as unknown as { prototype: { options: Record<string, unknown> } }).prototype.options = {};
  return {
    default: { icon: () => ({}), divIcon: () => ({}), Marker },
  };
});
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: unknown }) => children,
  TileLayer: () => null,
  Marker: () => null,
  Popup: () => null,
  GeoJSON: ({ data, style }: { data: unknown; style?: unknown }) =>
    createElement("div", { "data-geojson": JSON.stringify(data), "data-style": JSON.stringify(style ?? null) }),
  Rectangle: () => null,
  CircleMarker: () => null,
  useMap: () => ({ setView() {}, zoomIn() {}, zoomOut() {} }),
}));

describe("MapPanel existing render is preserved", () => {
  it("renders without a point: layer controls, legend, map hint and the additive use-table panel", () => {
    const html = renderToStaticMarkup(
      <MapPanel point={null} address="Corrientes 2500, CABA" features={[]} />,
    );

    expect(html).toContain("Capas de información");
    expect(html).toContain("Todavía no hay capas territoriales disponibles para esta consulta.");
    expect(html).toContain("Mapa base");
    expect(html).toContain("Leyenda");
    expect(html).toContain("No pudimos ubicar esta dirección en el mapa.");
    expect(html).toContain("La ubicación del punto es aproximada");
    expect(html).toContain("Corrientes 2500, CABA");
    expect(html).toContain("Cuadro de usos");
    expect(html).not.toContain("Capas de ejemplo");
  });

  it("renders with a point: demo layer toggles, base map toggle and legend stay available", () => {
    const html = renderToStaticMarkup(
      <MapPanel point={{ lat: -34.604, lng: -58.4055 }} address="Corrientes 2500, CABA" features={[]} />,
    );

    expect(html).toContain("Capas de ejemplo (ilustrativas)");
    expect(html).toContain("Zonificación y usos del suelo");
    expect(html).toContain("Parcela y catastro");
    expect(html).toContain("Comercios habilitados cercanos");
    expect(html).toContain("Calles");
    expect(html).toContain("Satélite");
    expect(html).toContain("Leyenda");
    expect(html).toContain("Consultando el cuadro de usos");
  });
});

describe("real parcel geometry on the map (S12)", () => {
  const geometry: GeoJSON.Geometry = {
    type: "Polygon",
    coordinates: [[[-58.406, -34.605], [-58.405, -34.605], [-58.405, -34.604], [-58.406, -34.605]]],
  };

  it("renders the real geometry with a distinct style and nothing when no geometry is available", () => {
    const withGeometry = renderToStaticMarkup(<ParcelGeometryLayer geometry={geometry} />);

    expect(withGeometry).toContain("data-geojson=");
    expect(withGeometry).toContain("Polygon");
    expect(withGeometry).toContain(REAL_PARCEL_STYLE.color);
    expect(renderToStaticMarkup(<ParcelGeometryLayer geometry={null} />)).toBe("");
  });

  it("hides the illustrative parcel layer and relabels zoning only with real geometry", () => {
    expect(visibleDemoLayerIds(["zonificacion", "parcela"], true)).toEqual(["zonificacion"]);
    expect(visibleDemoLayerIds(["zonificacion", "parcela"], false)).toEqual(["zonificacion", "parcela"]);

    const realOptions = demoLayerOptions(true);
    expect(realOptions.map(layer => layer.id)).not.toContain("parcela");
    expect(realOptions.find(layer => layer.id === "zonificacion")?.label).toMatch(/ilustrativ/i);

    const demoOptions = demoLayerOptions(false);
    expect(demoOptions.map(layer => layer.id)).toContain("parcela");
    expect(demoOptions.find(layer => layer.id === "zonificacion")?.label).toBe("Zonificación y usos del suelo");
  });

  it("swaps the demo parcel legend entry for a real-parcel entry only with real geometry", () => {
    const real = renderToStaticMarkup(<MapLegend hasRealGeometry={true} />);
    expect(real).toContain("Parcela real");
    expect(real).not.toContain("Parcela consultada");

    const demo = renderToStaticMarkup(<MapLegend hasRealGeometry={false} />);
    expect(demo).toContain("Parcela consultada");
    expect(demo).not.toContain("Parcela real");
  });
});
