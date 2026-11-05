import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from "react-leaflet";
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

function Recenter({ point }: { point: GeoPoint }) {
  const map = useMap();
  useEffect(() => {
    map.setView([point.lat, point.lng], 15);
  }, [map, point.lat, point.lng]);
  return null;
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

  function toggleLayer(id: string) {
    setVisibleLayers((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  }

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
          <span className="badge">OpenStreetMap</span>
        </div>
        {!point && (
          <p className="small-note" role="status">No pudimos ubicar esta dirección en el mapa. Mostramos la Ciudad como referencia.</p>
        )}
        <MapContainer center={[(point ?? CABA_CENTER).lat, (point ?? CABA_CENTER).lng]} zoom={point ? 15 : 12} scrollWheelZoom className="map">
          {point && <Recenter point={point} />}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {point && (
            <Marker position={[point.lat, point.lng]}>
              <Popup>{address}</Popup>
            </Marker>
          )}
          {features.filter((feature) => visibleLayers.includes(feature.id)).map((feature) => (
            <GeoJSON key={feature.id} data={feature.geometry} />
          ))}
        </MapContainer>
        <p className="hint">
          La ubicación del punto es aproximada: la informa el servicio nacional de direcciones Georef.
          Las capas dependen de la información que entregue el backend.
        </p>
      </section>
    </div>
  );
}
