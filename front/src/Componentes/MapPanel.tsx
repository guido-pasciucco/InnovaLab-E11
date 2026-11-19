import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, Rectangle, CircleMarker, useMap } from "react-leaflet";
import L from "leaflet";
import type { GeoPoint, TerritorialFeature } from "../types";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

// Used when the address has no coordinates: the map shows the city without a marker.
const CABA_CENTER: GeoPoint = { lat: -34.6037, lng: -58.4416 };

const TILE_URLS = {
  calles: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  satelite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
};

// --- helpers: meters -> coordinates, to draw the illustrative layers around the consultation point ---
const off = (center: GeoPoint, dx: number, dy: number): [number, number] => [
  center.lat + dy / 111320,
  center.lng + dx / (111320 * Math.cos((center.lat * Math.PI) / 180)),
];
const rect = (center: GeoPoint, x1: number, y1: number, x2: number, y2: number): [[number, number], [number, number]] =>
  [off(center, x1, y1), off(center, x2, y2)];

type DemoLayerId = "zonificacion" | "parcela" | "comercios" | "transporte" | "protegidas";

const DEMO_LAYERS: { id: DemoLayerId; label: string }[] = [
  { id: "zonificacion", label: "Zonificación y usos del suelo" },
  { id: "parcela", label: "Parcela y catastro" },
  { id: "comercios", label: "Comercios habilitados cercanos" },
  { id: "transporte", label: "Transporte público" },
  { id: "protegidas", label: "Áreas protegidas y patrimonio" },
];

const zoneStyle = { color: "#1D3343", weight: 1.5, fillColor: "#035C80", fillOpacity: 0.2 };
const parcelStyle = { color: "#1D3343", weight: 2, dashArray: "6 4", fillColor: "#fff", fillOpacity: 0.9 };
const protectedStyle = { color: "#035C80", weight: 2, dashArray: "6 4", fillColor: "#FFCD02", fillOpacity: 0.22 };
const poiStyle = { radius: 7, color: "#1D3343", weight: 2, fillColor: "#FFCD02", fillOpacity: 1 };

const zoneLabel = L.divIcon({ className: "map-demo-label", html: "<span>Distrito comercial</span>", iconSize: [150, 28], iconAnchor: [0, 0] });
const stopIcon = L.divIcon({ className: "map-demo-stop", html: "<i></i>", iconSize: [16, 16], iconAnchor: [8, 8] });

function Recenter({ point }: { point: GeoPoint }) {
  const map = useMap();
  useEffect(() => {
    map.setView([point.lat, point.lng], 15);
  }, [map, point.lat, point.lng]);
  return null;
}

function ZoomControls({ center }: { center: GeoPoint }) {
  const map = useMap();
  return (
    <div className="map-zoom">
      <button type="button" onClick={() => map.zoomIn()} aria-label="Acercar">+</button>
      <button type="button" onClick={() => map.zoomOut()} aria-label="Alejar">−</button>
      <button type="button" onClick={() => map.setView([center.lat, center.lng], 16)} aria-label="Centrar en la ubicación">Centro</button>
    </div>
  );
}

/** Illustrative demo layers drawn around the consultation point; not real GIS data. */
function DemoLayers({ point, visible }: { point: GeoPoint; visible: DemoLayerId[] }) {
  return (
    <>
      {visible.includes("zonificacion") && (
        <>
          <Rectangle bounds={rect(point, -180, 28, 180, 170)} pathOptions={zoneStyle} />
          <Rectangle bounds={rect(point, -180, -170, 180, -28)} pathOptions={zoneStyle} />
          <Marker position={off(point, -170, 164)} icon={zoneLabel} interactive={false} keyboard={false} />
        </>
      )}
      {visible.includes("parcela") && (
        <Rectangle bounds={rect(point, -11, -13, 11, 13)} pathOptions={parcelStyle} />
      )}
      {visible.includes("comercios") && (
        <>
          {[[-100, 40], [95, 48], [150, -60], [-60, -110], [40, -130]].map(([x, y], i) => (
            <CircleMarker key={i} center={off(point, x, y)} pathOptions={poiStyle} />
          ))}
        </>
      )}
      {visible.includes("transporte") && (
        <>
          {[[-175, -5], [170, 8], [10, -150]].map(([x, y], i) => (
            <Marker key={i} position={off(point, x, y)} icon={stopIcon} interactive={false} keyboard={false} />
          ))}
        </>
      )}
      {visible.includes("protegidas") && (
        <>
          <Rectangle bounds={rect(point, 220, 100, 330, 230)} pathOptions={protectedStyle} />
          <Rectangle bounds={rect(point, -340, -230, -230, -110)} pathOptions={protectedStyle} />
        </>
      )}
    </>
  );
}

export default function MapPanel({
  point,
  address,
  features,
}: {
  point: GeoPoint | null;
  address: string;
  features: TerritorialFeature[];
}) {
  const [visibleLayers, setVisibleLayers] = useState<string[]>(features.map((feature) => feature.id));
  const [visibleDemo, setVisibleDemo] = useState<DemoLayerId[]>(["zonificacion", "parcela"]);
  const [satellite, setSatellite] = useState(false);

  function toggleLayer(id: string) {
    setVisibleLayers((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  }

  function toggleDemo(id: DemoLayerId) {
    setVisibleDemo((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  }

  const center = point ?? CABA_CENTER;

  return (
    <div className="map-workspace">
      <aside className="map-controls" aria-label="Controles del mapa">
        <h2>Capas de información</h2>
        {features.length ? (
          features.map((feature) => (
            <label className="map-layer" key={feature.id}>
              <input
                type="checkbox"
                checked={visibleLayers.includes(feature.id)}
                onChange={() => toggleLayer(feature.id)}
              />
              <span>{feature.label}</span>
            </label>
          ))
        ) : (
          <p className="small-note">
            Todavía no hay capas territoriales disponibles para esta consulta.
          </p>
        )}
        {point && (
          <>
            <h3 className="map-controls__subtitle">Capas de ejemplo (ilustrativas)</h3>
            {DEMO_LAYERS.map((layer) => (
              <label className="map-layer" key={layer.id}>
                <input
                  type="checkbox"
                  checked={visibleDemo.includes(layer.id)}
                  onChange={() => toggleDemo(layer.id)}
                />
                <span>{layer.label}</span>
              </label>
            ))}
          </>
        )}
        <h3 className="map-controls__subtitle">Mapa base</h3>
        <div className="map-base" role="group" aria-label="Tipo de mapa">
          <button type="button" aria-pressed={!satellite} className={satellite ? "" : "is-active"} onClick={() => setSatellite(false)}>Calles</button>
          <button type="button" aria-pressed={satellite} className={satellite ? "is-active" : ""} onClick={() => setSatellite(true)}>Satélite</button>
        </div>
        <div className="map-legend">
          <h3 className="map-controls__subtitle">Leyenda</h3>
          <div className="map-legend__item"><i className="map-legend__swatch map-legend__swatch--zone" /><span>Distrito comercial</span></div>
          <div className="map-legend__item"><i className="map-legend__swatch map-legend__swatch--parcel" /><span>Parcela consultada</span></div>
          <div className="map-legend__item"><i className="map-legend__swatch map-legend__swatch--dot" /><span>Ubicación de la consulta</span></div>
        </div>
        <div className="map-location">
          <span>UBICACIÓN CONSULTADA</span>
          <strong>{address}</strong>
        </div>
      </aside>

      <section className="panel map-panel">
        <div className="section-heading">
          <div>
            <h2>Mapa territorial</h2>
            <p>Visualización de referencia de la ubicación ingresada.</p>
          </div>
          <span className="badge">{satellite ? "Esri" : "OpenStreetMap"}</span>
        </div>
        {!point && (
          <p className="small-note" role="status">No pudimos ubicar esta dirección en el mapa. Mostramos la Ciudad como referencia.</p>
        )}
        <MapContainer center={[center.lat, center.lng]} zoom={point ? 15 : 12} scrollWheelZoom className="map">
          {point && <Recenter point={point} />}
          {satellite ? (
            <TileLayer
              attribution='Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics'
              url={TILE_URLS.satelite}
              maxZoom={19}
            />
          ) : (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url={TILE_URLS.calles}
              maxZoom={19}
            />
          )}
          {point && (
            <Marker position={[point.lat, point.lng]}>
              <Popup>{address}</Popup>
            </Marker>
          )}
          {features.filter((feature) => visibleLayers.includes(feature.id)).map((feature) => (
            <GeoJSON key={feature.id} data={feature.geometry} />
          ))}
          {point && <DemoLayers point={point} visible={visibleDemo} />}
          <ZoomControls center={center} />
        </MapContainer>
        <p className="map-credit">
          Fuente del mapa: {satellite ? "Imágenes © Esri" : "© colaboradores de OpenStreetMap"}
        </p>
        <p className="hint">
          La ubicación del punto es aproximada: la informa el servicio nacional de direcciones Georef.
          Las capas dependen de la información que entregue el backend; las capas de ejemplo son ilustrativas.
        </p>
      </section>
    </div>
  );
}
