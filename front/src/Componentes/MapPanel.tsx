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
  point: GeoPoint;
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
        <MapContainer center={[point.lat, point.lng]} zoom={15} scrollWheelZoom className="map">
          <Recenter point={point} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[point.lat, point.lng]}>
            <Popup>{address}</Popup>
          </Marker>
          {features.filter((feature) => visibleLayers.includes(feature.id)).map((feature) => (
            <GeoJSON key={feature.id} data={feature.geometry} />
          ))}
        </MapContainer>
        <p className="hint">
          La precisión del punto y las capas dependen de la información que entregue el backend.
          En la versión de demostración, la coordenada puede ser ilustrativa.
        </p>
      </section>
    </div>
  );
}
